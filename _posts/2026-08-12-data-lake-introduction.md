---
title: 数据湖与数据库的差异以及新的挑战
date: 2026-08-12 08:45:00 +0800
categories: [Survey]
tags: [数据湖, Data Lake, Iceberg]
pin: false
---

## 数据湖的基本概念

数据湖要解决的核心问题是**当数据量、数据类型、数据来源和使用方式都变得复杂以后，如何低成本地把大量原始数据统一存下来，并让不同计算系统去使用**。相比数据库，数据湖最大的区别在于无法一开始就确定好数据的schema，形成一种结构化的表格，从而进一步增加索引等方便数据检索的功能。简单来说，在数据存储方面，数据库采用"Schema on Write"的策略，而数据湖采用"Schema on Read"的策略。

我们举一个例子说明这种数据存储的差异。

对于数据库，所有的数据都是由`CREATE TABLE`创建的表格，如下所示。

```sql
CREATE TABLE orders (
    id BIGINT,
    user_id BIGINT,
    price DECIMAL,
    created_at TIMESTAMP
);
```

一个数据湖通常存放的是像下面这样千奇百怪的数据，很多类型（比如视频、模型训练数据）都不太能直接放到表格里。

```text
日志
图片
视频
JSON
CSV
Parquet
模型训练数据
Embedding
...
        ↓
       对象存储
    S3 / OBS / HDFS
        ↓
   需要的时候再解析
```

数据湖里的文件系统里可能是这样存放的。

```text
/data/
  logs/2026/08/12/*.json
  orders/2026/08/*.parquet
  videos/*.mp4
  images/*.jpg
  embeddings/*.parquet
  model_training/*.jsonl
```

> 数据量从100万行增加到1000亿行会产生大数据问题，但促使数据湖出现的关键原因是数据来源变得更加丰富。更准确的说，3个V(Volume, Variety, Velocity)共同催生了数据湖需求的诞生。
{: .prompt-tip }

数据来源是让Postgres之类的关系型数据库无法直接承接数据湖需求的最重要的原因。

```text
               ┌─ PostgreSQL 订单
               ├─ App 日志
               ├─ 用户点击流
各种数据来源 ──┼─ 图片
               ├─ 视频
               ├─ IoT 数据
               ├─ 模型 Embedding
               └─ 第三方数据
                      ↓
                  Data Lake
```

想象如果你有下面这些数据：

```text
10 PB 视频
50 PB 日志
200 TB JSON
100 TB Parquet
几十亿 Embedding
```

你不会很自然地把它们全部塞进Postgres的表里面。

## 数据表变大了会有什么新问题？

我们暂且忽略多模态数据等丰富数据类型带来的额外问题，单讨论一张数据库中可以表示的表格。当这张表格变得特别特别大的时候，会有什么新的问题和挑战？

请读者直观上思考一下当仅仅是数据量（行数）发生下面的变化，需要数据库能做出什么样的适配。

```
1 万行
↓
100 万行
↓
1 亿行
↓
100 亿行
↓
1 万亿行
```

### 数据量大到必须分布式存储

最先出现的一个问题是**索引越来越大**，大到内存存不下，再进一步大到单机存不下。

例如B+树索引：

```text
100 万行
索引可能几百 MB

10 亿行
索引可能几十 GB

1000 亿行
索引可能 TB 级
```

假设一台机器的硬盘有16TB，但数据量已经达到100TB，1PB，10PB，那就必须引入分布式存储和Sharding了。

```text
      Data
       ↓
 ┌─────┼─────┐
node1 node2 node3
 ↓     ↓     ↓
shard shard shard
```

一条SQL查询语句`SELECT * FROM orders WHERE user_id = 123;`原本只需要查询本机的B+树，现在变成

```text
query
  ↓
router
  ↓
找到 shard
  ↓
node 17
  ↓
index lookup
```

如果不知道shard在哪，还需要进行一种非常昂贵的scatter-gather操作。

```bash
             ┌→ node1
             ├→ node2
query ───────┼→ node3
             ├→ ...
             └→ node100
                  ↓
               merge
```


### JOIN变得更加困难

假设有这么两张表orders和users:

```text
orders
----------------
order_id
user_id
product_id
price
time
address
remark
...

users
----------------
user_id
name
age
city
gender
...
```

对于一条有JOIN的查询语句

```sql
SELECT u.city, SUM(o.price)
FROM orders o
JOIN users u
  ON o.user_id = u.user_id
GROUP BY u.city;
```

真正需要JOIN的只有

```
orders:
user_id
price

users:
user_id
city
```

行存型数据库的第一个困难是**会读取大量没用的列**。表越宽，就有越多无效I/O。

列存首先解决的就是这个无效I/O的问题，让JOIN操作不需要读很多无效的列。

但即使数据用列存存放，在数据表变大后，对JOIN还是有质变——Hash Table放不进内存。如果Users表1TB，构建Hash Table后可能1.5TB，但服务器的内存只有256GB，这时候就必须做`partition + spill to disk + multi-pass join`。

更糟的是，当orders表有1000亿行(100TB)，users表有10亿行(20TB)的话，数据会分散在数百台机器：

```text
node1: orders shard
node2: orders shard
...
node100

node101: users shard
...
```

为了join，可能必须重新分发数据(shuffle)。

```bash
orders
   \
    \ shuffle
     \
      → network → join nodes
     /
users
```

这里的shuffle是大数据系统中最昂贵的操作之一。

为了JOIN这个条件`orders.user_id = users.user_id`，两边按照hash(user_id)重新分区，那么原来的数据在哪台机器上并不重要，相同user_id的数据必须被搬到一台机器上的同一个worker里，这里面有大量的网络I/O，可想而知会非常昂贵。JOIN不再是在CPU做hash lookup，而是变成:

```
磁盘读取
   ↓
序列化
   ↓
网络发送
   ↓
网络接收
   ↓
反序列化
   ↓
重新 partition
   ↓
内存 / 磁盘
   ↓
hash join
```


### 更新数据变得困难

首先考虑数据库非常擅长的部分。假设有这么一张表，有5个字段，`id | name | age | city | salary`，下面的UPDATE语句可以再O(log N)的时间复杂度完成。

```sql
UPDATE employee
SET salary = 20000
WHERE id = 12345;
```

因为数据库维护了针对id的B+树索引。针对一个典型的行存数据库，数据物理上接近

```text
Row 1: [1, Alice, 25, Beijing, 10000]
Row 2: [2, Bob,   31, Shanghai, 15000]
...
Row N: [12345, Tom, 28, Shenzhen, 18000]
```

一整行的数据通常放的比较近。数据库可以通过索引找到`id=12345`所在的数据也，然后修改这一行（在很多MVCC数据库里写入一个新版本）。

成本大致是

```bash
B-tree 查找
   ↓
找到一个 page
   ↓
改这一行 / 写一个新版本
   ↓
WAL
```

所以这是一个近似 O(log N) 定位 + O(1) 局部修改 的问题。

在超大规模数据的情况下，往往数据会用列存存放，因为更方便压缩（原因下面会解释）。

如果这段数据是用列存的形式存放的，那它的形式更接近下面这样:

```bash
id:
1
2
3
...
12345

name:
Alice
Bob
...
Tom

age:
25
31
...
28

city:
Beijing
Shanghai
...
Shenzhen

salary:
10000
15000
...
18000
```

这种列存的模式适合大数据量存储，因为相同列的类型相同，更容易压缩，例如

```
city:

Beijing
Beijing
Beijing
Beijing
Shanghai
Shanghai
Shanghai
...
```

可以很容易地压缩成

```
Beijing × 1,000,000
Shanghai × 800,000
...
```

真正保存的内容变成了

```
1 1 1 1 1 2 2 2 3 3 ...
```

所以列存对一列的读取是非常快的。但对于更新就难了。

针对相同的UPDATE操作，这个salary列在磁盘上的样子可能是这样

```bash
salary chunk:

encoded/compressed bytes
--------------------------------
10000
10000
10000
12000
12000
...
18000
...
--------------------------------
```

磁盘上实际不是规整的偏移量对应数据位置

```
offset 1: salary1
offset 2: salary2
offset 3: salary3
```

而是包含了各种压缩的元信息和压缩后的数据，例如

```
Dictionary
Bit packing
Run Length Encoding
Delta encoding
Compression block
```

对于salary这一列，可能磁盘里的内容是下面的这样的

```
salary dictionary:

0 -> 10000
1 -> 12000
2 -> 15000
3 -> 18000

encoded:

000000111122222233333...
```

当把其中的一个值从18000变成20000时，这个20000甚至不在dictionary里，就不能简单地进行seek(offset) + write(20000)这样完成数据更新，因为这一个更新可能导致整个压缩布局发生变化。

理论上可能需要下面这一系列的操作——为了修改8字节的信息，最后实际需要写64KB, 1MB甚至更多，形成“写放大”效应(Write Amplification)。

```
读整个 compression block
       ↓
解压
       ↓
修改一个值
       ↓
重新编码
       ↓
重新压缩
       ↓
重写整个 block
```

对于Parquet的设计来说，它先天就不是为了这种小更新而设计的，而本质上是一种**面向分析的不可变列式文件格式**。

典型的Parquet文件内部是

```bash
Parquet File
│
├── Row Group 1
│   ├── id column chunk
│   ├── name column chunk
│   ├── salary column chunk
│   └── ...
│
├── Row Group 2
│   ├── id
│   ├── name
│   ├── salary
│   └── ...
│
└── metadata
```

如果修改其中的一个元素，可能需要把整个Row Group重新写一遍。比如一个1GB的Parquet，每个Row Group 128MB，修改一个salary需要写128MB的量，这个写放大比例高达128 * 102 * 1024 / 8 大约是1600万倍。

Parquet拥有的所谓面向分析的能力，是可以快速完成类似下面的"分析"功能。

```sql
SELECT
    city,
    AVG(salary)
FROM employee
WHERE year = 2026
GROUP BY city;
```

对于更新数据、删除数据等功能，实际系统往往不进行真正的修改，而是增加额外的记录来记录这个操作，形成逻辑更新/删除——物理上这行实际还在，但逻辑上已经删除，思想上类似于LSM Tree。


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

首先考虑数据库非常擅长的部分。假设有这么一张表，有5个字段，`id | name | age | city | salary`，下面的UPDATE语句可以在O(log N)的时间复杂度完成。

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

一整行的数据通常放的比较近。数据库可以通过索引找到`id=12345`所在的数据也，然后修改这一行（在很多MVCC的数据库里这个修改操作是写入一个新版本）。

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

在超大规模数据的情况下，往往数据会用列存存放，因为列存具备避免JOIN读取大量无效的列，更容易大幅压缩等优势。

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

这种列存的模式因为相同列的类型相同，更容易压缩，例如

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

## 数据湖的应对思路：存算分离与开放表格式

在上一章我们看到了当数据规模和数据来源超出传统关系型数据库能力时，会出现三个层面的新挑战：

- 数据量超出单机，必须分布式存储与计算
- JOIN 在分布式系统下变得昂贵
- 列存压缩让单行修改成本不可接受

数据湖和它配套的**开放表格式**(Open Table Format)正是围绕解决这些问题发展出来的。

### 存算分离

传统数仓(Teradata, Greenplum)以及 Hadoop 早期(HDFS + MapReduce)把存储和计算耦合在同一批机器上。HDFS 推崇的 data locality 就是建立在"计算跟着数据走"这一假设上。

数据湖的一个核心架构选择是**把存储和计算彻底分开**：

```text
        ┌───────────────┐         ┌─────────────┐
        │  对象存储      │         │ 元数据/目录  │
        │ S3 / OSS / OBS│ <─────> │ Hive / Glue │
        │ (Parquet 等)  │         │ / Iceberg   │
        └───────┬───────┘         └──────┬──────┘
                │                         │
                │     ┌───────────────┐   │
                └─────┤ 计算引擎       ├───┘
                      │ (可弹性伸缩)   │
                      │ Spark/Trino/  │
                      │ Flink/Dremio  │
                      └───────────────┘
```

带来的几个核心好处：

```text
1. 存储成本下降
   - 对象存储(OSS / S3)的 GB·月成本远低于带冗余的本地盘
   - 数据可以长期保留、便宜地堆在那里

2. 计算弹性
   - 临时查询开 Trino，批处理开 Spark，流式开 Flink
   - 闲时关掉，无需为峰值预留机器

3. 多引擎共享同一份数据
   - 不再出现"Spark 跑过的数据 Flink 还要再导一份"
   - 避免数据孤岛
```

但存算分离立刻引入了一个新问题——**当数据只是一些散落在对象存储上的文件时，没有任何东西在帮你管理它们**。

### 没有表格式时的混乱

设想直接把 Parquet 文件扔到 S3 上：

```text
s3://lake/orders/
    2026-08-01-001.parquet
    2026-08-01-002.parquet
    2026-08-02-001.parquet
    ...
```

此时任何一个计算引擎(Spark / Trino / Flink)想要"查 orders 表"都会面临：

```text
问题 1：哪些文件是这张表的？
   - 按前缀猜？命名冲突怎么办？
   - 删除若干行后产生了小文件，谁来清理？

问题 2：并发写入怎么处理？
   - 两个 Spark job 同时往这张表写数据
   - 文件互相覆盖 / 写入半截

问题 3：删了一行数据后还能查出来吗？
   - 没有版本控制
   - 没有"昨天那张表"的视图

问题 4：分区信息从哪来？
   - 路径里的 2026/08/01 是分区？还是业务日期？
   - 改名 / 改分区策略会不会影响历史数据？

问题 5：如何做权限控制和行 / 列级安全？
   - 没有中心化的元数据可挂策略
```

直接的结论是：**光把数据存到对象存储里还远远不够，还需要在存储层之上加一层"表的语义"**。

### 开放表格式：填补"表的语义"

开放表格式就是这一层"表的语义"。它和具体的存储引擎、计算引擎解耦，但提供数据库表的关键能力：

```text
       具体存储         开放表格式             任意计算引擎
   ┌──────────┐     ┌──────────────┐      ┌──────────────┐
   │ Parquet  │ <-> │ Iceberg      │ <->  │ Spark        │
   │ ORC      │     │ Delta Lake   │      │ Trino        │
   │ Avro     │     │ Apache Hudi  │      │ Flink        │
   └──────────┘     └──────────────┘      │ Dremio       │
       ↑                  ↑               │ ...          │
   对象存储层           表语义层             └──────────────┘
   (S3/OSS/HDFS)      (元数据 + 协议)        (查询 / 计算层)
```

主流的三个开放表格式：

```text
Iceberg        - Netflix 开源，强调标准化、与引擎解耦
Delta Lake     - Databricks 开源，与 Spark 深度绑定
Apache Hudi    - Uber 开源，强项是流式 upsert
```

它们各自的设计有差异，但解决的问题高度重合。下一节我们把这些问题摊开来看。

## 开放表格式要解决的具体问题

回到 [§2 节](#数据表变大了会有什么新问题)提出的三大挑战，对应的"表的语义"层需要提供以下能力。

### 原子提交与快照隔离

把多台机器上的多文件写入当作"一次表变更"：

```text
Spark job A：写 files_1..files_10
Spark job B：写 files_11..files_15

如果没有原子提交：
   - A 读到 B 的部分文件 + 自己的文件 → 半截状态
   - B 写完之前 A 抢到读锁 → 互相阻塞

开放表格式的做法：
   1. 写新文件到对象存储
   2. 准备一个"快照"(snapshot)，里面包含：
      - 新增文件列表
      - 删除文件列表
      - 元数据信息(schema, partition spec, ...)
   3. 通过 catalog 做一次原子"指针切换"
      - 旧快照依然可读
      - 新快照成为"当前表"
```

这样就解决了分布式存储中并发读写的难题——多个 writer 同时写，多个 reader 同时读，互相不打架。

### Schema Evolution

业务侧加列、改类型是常态：

```sql
-- v1
CREATE TABLE orders (
    id BIGINT,
    price DECIMAL
);

-- v2: 增加 user_id
ALTER TABLE orders ADD COLUMN user_id BIGINT;

-- v3: 改 price 精度
ALTER TABLE orders ALTER COLUMN price TYPE DECIMAL(18, 4);
```

开放表格式让 schema 演化**不需要重写历史数据**：

```text
v1 文件: [id, price]
v2 文件: [id, price, user_id]
v3 文件: [id, price(18,4), user_id]

读取时统一按"当前 schema"投影，缺失列填 NULL。
```

### Partition Evolution

传统 Hive 表的分区是写进目录名里的：

```text
orders/year=2026/month=08/day=12/...
```

一旦业务想"按小时分区"，过去所有数据都要重写。开放表格式把分区从"物理目录"变成了"表的属性"：

```text
v1: PARTITIONED BY (day)
v2: PARTITIONED BY (hour)   <- 不重写历史数据
v3: PARTITIONED BY (day, region)
```

切换 partition spec 时，旧文件仍然按 day 分组，新文件按 hour 分组；查询时根据当前 spec 自动选择正确的分组方式。

### Hidden Partitioning

更进一步：用户写 SQL 时不需要显式拼分区谓词。

```sql
-- 传统 Hive
SELECT * FROM orders
WHERE year = 2026 AND month = 08 AND day = 12;

-- 开放表格式 + hidden partition
SELECT * FROM orders
WHERE created_at >= '2026-08-12' AND created_at < '2026-08-13';
```

系统自动把上面的时间谓词翻译成下面对应的分区裁剪：

```text
WHERE year = 2026 AND month = 08 AND day = 12
```

这样既减少了用户的负担，也避免了"用户写错分区谓词 → 全表扫描"这类常见 bug。

### 文件裁剪与谓词下推

直接对应 §2.2 节讲的 IO 优化。表格式维护每个文件的统计信息：

```text
file_001.parquet:
   id:    min=1, max=10000, null_count=0
   price: min=10.5, max=999.0, null_count=3

file_002.parquet:
   id:    min=10001, max=20000, null_count=0
   price: min=20.0, max=500.0, null_count=12
```

查询 `WHERE id = 5000` 时：

```text
1. 读 metadata（不是数据本身）
2. 比对统计信息
3. 只挑出 id 范围包含 5000 的文件
4. 只把那几个文件的对应 column chunk 读进来
```

行存数据库做不到这种粒度的"列级裁剪"——它们通常只能裁剪"行是否要读"，而列存 + 文件统计可以裁剪"哪些文件/列连读都不用读"。

### Time Travel 与回滚

每一份写入都会留下一个 snapshot：

```text
snap-001: 2026-08-01 00:00
snap-002: 2026-08-02 00:00
snap-003: 2026-08-12 12:00
...
snap-N:   2026-08-12 18:00
```

可以这样查：

```sql
-- 查三天前那张表
SELECT * FROM orders
FOR SYSTEM_TIME AS OF '2026-08-09 00:00:00';

-- 把表回滚到昨天
CALL catalog.system.rollback_to_table_timestamp('orders', '2026-08-11 00:00:00');
```

在数据库里要做 PITR(Point-in-Time Recovery)才能达到这个效果，数据湖里是天然能力。

### 一份小总结

把上面这些能力映射回 §2 的三大挑战：

| §2 节提到的问题 | 开放表格式怎么解决 |
|------------------|---------------------|
| §2.1 分布式下的并发读写 | Atomic Commit + Snapshot |
| §2.2 JOIN / IO 优化 | File Pruning + Column Pruning |
| §2.3 单行更新困难 | Copy-on-Write / Merge-on-Read(下面 §6 展开) |

## Iceberg 架构深入

Iceberg 是 Netflix 在 2017-2018 年开源的开放表格式(目前在 Apache 基金会)，它的设计哲学是**严格解耦任何具体引擎**，因此在三大表格式里和 Spark / Flink / Trino 的兼容性最广。

### 三层架构总览

```text
              Catalog 层
   ┌──────────────────────────┐
   │ Hive / Glue / Nessie /   │
   │ REST / JDBC              │
   └─────────────┬────────────┘
                 │ 原子指针: current metadata location
                 ▼
              Metadata 层
   ┌──────────────────────────┐
   │ v3.metadata.json         │  ← 当前 schema, partition spec,
   │                          │     snapshot 列表
   └─────────────┬────────────┘
                 │ 指向一个 snapshot
                 ▼
           Manifest List
   ┌──────────────────────────┐
   │ snap-...avro             │  ← 多个 manifest 文件的列表
   └─────────────┬────────────┘
                 │ 每个 manifest 文件
                 ▼
           Manifest 文件
   ┌──────────────────────────┐
   │ manifest-...avro         │  ← 一批 data file 的元数据 + 统计
   └─────────────┬────────────┘
                 │ 每个 data file
                 ▼
           Data Files (Parquet / ORC / Avro)
```

我们一层一层看。

### Catalog 层

Catalog 是 Iceberg 的入口。存的就是一个指针——"当前表的 metadata 文件在哪"。

```text
catalog.database.table  →  s3://lake/db/orders/metadata/v3.metadata.json
```

多种实现：

```text
Hive Catalog      - 借助 Hive Metastore 做目录服务(很多公司还在用)
Glue Catalog      - AWS Glue Data Catalog
Nessie            - Git 风格的元数据，支持 branch / tag / 实验分支
REST Catalog      - 标准化 REST 接口，新的官方推荐
JDBC Catalog      - 直接打到 Postgres / MySQL
```

Catalog 不存数据，只存指针。这点很重要——它是 Iceberg 实现"存算分离"的根本。

### Metadata 文件

每次 commit 都会生成一个**新的** metadata 文件，旧文件依然存在：

```text
v1.metadata.json
v2.metadata.json
v3.metadata.json  ← 当前的
```

每个 metadata 文件里包含：

```json
{
  "schema": {
    "fields": [
      {"id": 1, "name": "id", "type": "long"},
      {"id": 2, "name": "price", "type": "decimal(18,4)"},
      {"id": 3, "name": "user_id", "type": "long"}
    ]
  },
  "partition-spec": [
    {"name": "day", "transform": "day", "source-id": 4}
  ],
  "sort-order": [],
  "current-snapshot-id": 847362,
  "snapshots": [
    {"snapshot-id": 847360, "manifest-list": "snap-...avro"},
    {"snapshot-id": 847361, "manifest-list": "snap-...avro"},
    {"snapshot-id": 847362, "manifest-list": "snap-...avro"}
  ]
}
```

由于 metadata 是不可变的(每次 commit 产生一个新文件)，要"改"表其实就是写一个新 metadata 文件 + 把 catalog 指针切过去。

### Manifest List

指向某个 snapshot 包含的所有 manifest 文件。每个 manifest 文件对应一批 data file。

```text
manifest-list.avro:
   manifest_001.avro   (包含 day=2026-08-12 的文件)
   manifest_002.avro   (包含 day=2026-08-11 的文件)
   manifest_003.avro   (包含 day=2026-08-10 的文件)
```

manifest-list 本身带分区的统计：

```text
partitions:
   day=2026-08-12:  files=120,  rows=12,400,000
   day=2026-08-11:  files=98,   rows=10,200,000
   day=2026-08-10:  files=87,   rows=9,800,000
```

查询 `WHERE day = '2026-08-12'` 时，先读 manifest-list 就知道这一天的 manifest 列表，不用打开其他 manifest 文件。

### Manifest 文件

每个 manifest 文件描述一批 data file，包含每个文件的统计信息：

```text
manifest_001.avro:
   ┌──────────────────────────────────────────────────┐
   │ data_file       | partition    | stats            │
   ├──────────────────────────────────────────────────┤
   │ orders-001.pq   | day=08-12    | id: [1, 50000]    │
   │                 |              | price: [10, 999]  │
   │ orders-002.pq   | day=08-12    | id: [50001, 100000]│
   │                 |              | price: [20, 500]  │
   │ orders-003.pq   | day=08-12    | id: [100001, 150000]│
   │ ...                                              │
   └──────────────────────────────────────────────────┘
```

这就是 §4 节提到的"文件级统计信息"的真实形态——每个 data file 在 manifest 里都有自己各个列的 lower bound、upper bound、null count、value count 等。

### 一次查询的实际过程

```sql
SELECT SUM(price) FROM orders WHERE created_at >= '2026-08-10';
```

执行流程：

```text
1. 从 catalog 拿到 current metadata location
2. 读 metadata 文件(一般很小，几 KB 到几 MB)
   - 解析当前 schema、partition spec
   - 拿到 current snapshot 的 manifest list
3. 读 manifest list
   - 用 partition predicate 做 partition pruning
   - 决定哪些 manifest 文件要读
4. 读 manifest 文件
   - 用列统计信息做 file pruning
   - 决定哪些 data file 要读
5. 读 data file(Parquet)
   - 用 Parquet footer 里的列统计做 column chunk pruning
   - 用 page index 做 row group pruning
6. 最终只需打开少量文件、少量列
   而不是扫描整张表
```

这是一个**多层剪枝**(cascading pruning)的过程，每一层都让下一层的工作量小一个数量级。

### Snapshot 与并发

并发写入的处理用乐观锁(CAS)实现：

```text
Writer A                          Writer B
   │                                 │
   ├── 写 data files                 ├── 写 data files
   ├── 准备 manifest                 ├── 准备 manifest
   ├── 准备 manifest-list            ├── 准备 manifest-list
   ├── 准备 metadata.json (v3)       ├── 准备 metadata.json (v3')
   │                                 │
   └── CAS 写 catalog 指针           └── CAS 写 catalog 指针
              │                               │
              ▼                               ▼
       第一个 commit 成功                  第二个 commit 失败
       current = v3                       (基于 v3 重做)
```

Iceberg 用乐观锁实现并发控制——不是悲观锁，所以性能更高；冲突的概率取决于 commit 频率，写入不密集时几乎无感。

## 写入路径：LSM-Tree 思想在数据湖里的落地

§2.3 末尾我们留了一个伏笔："实际系统往往不进行真正的修改，而是增加额外的记录来记录这个操作，形成逻辑更新/删除——物理上这行实际还在，但逻辑上已经删除，思想上类似于 LSM Tree。"

这一节把它讲完。

### LSM-Tree 简述

LSM-Tree(Log-Structured Merge-Tree)的核心思想：

```text
写：只追加(append-only)，不在原地改
   ↓
内存里累积若干 SSTable
   ↓
定期合并(compaction)，把多个 SSTable 合并成更大的 SSTable
   ↓
读：从最新的 SSTable 往老的找，命中就返回
```

这种结构的代价是**写放大**(compaction 时要重写数据)，收益是**写吞吐极高**(所有写都是顺序写)和**读性能可控**(compaction 之后 SSTable 数量少)。

RocksDB / LevelDB / Cassandra / HBase 都是这个思路。

### Iceberg 的两种写模式

当一个 Spark job 想 `UPDATE / DELETE / MERGE` 一行时，Iceberg 提供两种模式。

#### Copy-on-Write (CoW)

```text
原始 data file:
   ┌───────────────────────────────┐
   │ row 1, row 2, ..., row 100000 │
   └───────────────────────────────┘

要 UPDATE row 50000 的 salary:
   1. 读整个文件
   2. 在内存里改 row 50000
   3. 写一个**新文件**到对象存储
   4. 在 manifest 里加新文件 + 删旧文件
```

特征：读放大 + 写放大，但是读的时候不用做合并操作，直接读新文件即可。

适用场景：**批量更新为主**(每天/每小时整批重写)，典型的 ETL 场景。

#### Merge-on-Read (MoR)

```text
原始 data file:
   ┌───────────────────────────────┐
   │ row 1, row 2, ..., row 100000 │
   └───────────────────────────────┘

要 UPDATE row 50000:
   1. 不动原始文件
   2. 写一个"删除文件"(delete file)：
      position delete: row 50000 in file_xxx.pq
   3. 读的时候把这个删除信息应用到原始文件
```

读的时候要把 delete file 和 data file 合并起来看，所以读开销更大，但写开销小很多。

适用场景：**高频小更新**(流式 upsert，比如订单状态实时变化)。

### 思想对照

```text
LSM-Tree                       Iceberg
─────────────────────────────────────────────
MemTable                       Delete file (position list)
   ↓ flush
SSTable L0                     Data file (Parquet)
   ↓ compact
SSTable L1 / L2 / ...          多个 data file 合并
   ↓ 
读：L0 → L1 → L2 ...          读：data file + delete file
```

本质上都是**通过追加 + 合并代替原地修改**——这是列存 + 不可变文件格式下唯一可行的更新方式。

### 表格式层面的写放大

刚才讲的是单次更新的写放大。再放大一个视角——compaction 本身的写放大。

```text
1 GB 的原始数据

如果每天一次 full compaction：
   每天写 1 GB 新数据
   每周做一次 compaction：重写 7 GB
   年总写量：365 + 52 * 7 = 729 GB
   
原始数据 365 GB，年写入 729 GB ≈ 2 倍写放大
```

实际系统里 compaction 策略的设计非常影响成本和性能，这是下面 §7 的内容。

## 数据湖的运维挑战

解决了数据库的扩展性问题后，数据湖又引入了一系列新的运维挑战。

### 小文件问题

流式写入(Kafka / Flink)常常每分钟写一次 Iceberg，每次都产生一个新文件：

```text
01:00  →  orders-001.pq (10 MB)
01:01  →  orders-002.pq (12 MB)
01:02  →  orders-003.pq (8 MB)
...
23:59  →  orders-1440.pq (15 MB)
```

一天下来 1440 个文件，每个只有 10 MB 量级。查询时：

```text
读 manifest list     →  1440 个 manifest entry
读 manifest         →  打开 1440 个 data file
读 data file        →  1440 次 open + read + close
```

每次 query 都打开上千个小文件，性能会急剧下降，对象存储的 list 请求也变成瓶颈。极端情况下，单次查询的延迟 90% 都花在打开文件上。

### Compaction

解决方案就是 compaction(合并小文件)：

```text
Before:                                  After:
orders-001.pq (10 MB)                    orders-merged-001.pq (256 MB)
orders-002.pq (12 MB)                    orders-merged-002.pq (256 MB)
orders-003.pq (8 MB)
...                                      <- manifest 里替换
orders-1440.pq (15 MB)
```

Iceberg 提供了 `rewrite_data_files` procedure 做这个：

```sql
CALL catalog.system.rewrite_data_files(
    table       => 'orders',
    strategy    => 'sort',
    sort_order  => 'zorder(id, created_at)',
    options     => map('target-file-size-bytes', '268435456')
);
```

注意 `target-file-size-bytes` 是单文件目标大小——一般设成 128 MB 到 1 GB，对象存储上大文件吞吐更优。

### Z-Ordering 与 Sorting

合并之后还想让"按某几个列过滤的查询"更高效，就需要把数据按这些列排序。

传统排序(Sort by `id`)：

```text
orders-by-id.pq:
   ┌──────────────────────────────┐
   │ id: 1, 2, 3, 4, ..., 1000000 │
   │ name: A, B, A, C, ...         │
   │ price: 100, 200, 100, 300,... │
   └──────────────────────────────┘
```

对 `WHERE id = 50000` 非常快，但 `WHERE name = 'Alice'` 还是全扫。

Z-Ordering 把多列信息编码到一个标量，让"按多个列过滤"都能用 min/max 裁剪：

```text
Z-Order(id, name):
   1. 把 (id, name) 映射到 Z-order 曲线上的一个标量 z
   2. 按 z 排序写入
   3. min/max bounds 同时反映 id 和 name 的局部密度
```

效果是：

```text
WHERE id = 50000                       →  min/max 裁剪命中
WHERE name = 'Alice'                   →  min/max 裁剪命中
WHERE id > 1000 AND name = 'Bob'       →  同时裁剪
```

代价是 Z-order 的写入比单列 sort 慢，因为它要在更高维度上排局部顺序。

### 统计信息过期

Iceberg 的 min/max bounds 是**写入时**算出来的。如果数据被 update / delete 之后没及时 compaction，bounds 和实际内容会脱节：

```text
旧 bounds:    id ∈ [1, 100000]
实际数据:     id ∈ [1, 50000], 50001-100000 都已被删除

查询 id = 80000 → 命中 bounds → 打开文件 → 文件里找不到 → 浪费一次 IO
```

这就是为什么 compaction 是数据湖运维里最常见的"维护任务"——它不只是合并文件，也是更新统计。

## 数据湖、数据仓库、湖仓一体

最后把数据湖放回更大的语境。

### 三个层次的关系

```text
数据仓库(Data Warehouse)
   ↑ 把数据从各种源 ETL 进结构化表格
   ↑ 强 schema，强一致性，专为 BI 设计
   ↑ 例子：Teradata, Snowflake, Redshift

数据湖(Data Lake)
   ↑ 把原始数据廉价地堆在对象存储上
   ↑ Schema on Read，灵活但缺乏治理
   ↑ 例子：HDFS + Hive, S3 + raw Parquet

湖仓一体(Lakehouse)
   ↑ 数据湖的存储 + 数据仓库的治理 / 性能
   ↑ 开放表格式是关键技术
   ↑ 例子：Databricks, Iceberg + Trino, Snowflake Iceberg Tables
```

三者不是简单的替代关系，而是覆盖不同象限：

```text
                  强治理
                    ↑
                    │
   数据仓库       湖仓一体
                    │
   ────────────────┼────────────────→ 灵活
                    │
                    │      数据湖
                    │
```

### 湖仓一体的关键能力对照

```text
能力              传统数仓     数据湖     湖仓一体
─────────────────────────────────────────────────
ACID 事务           ✅          ❌          ✅
Schema 强制         ✅          ❌          ✅
原始数据保留        ❌          ✅          ✅
多引擎共享          ❌          ✅          ✅
廉价存储            ❌          ✅          ✅
向量化查询          ✅          部分        ✅
行列级安全          ✅          ❌          ✅
```

### 当前的开放问题

即便有了 Iceberg，仍然有一些事没被表格式完全解决：

```text
1. 高频小写入的延迟
   - 流式 upsert 还是要 compaction，否则读性能下降
   - RocksDB / DuckDB 这种本地嵌入式引擎反而更擅长这个

2. 多表原子写入
   - 单表 ACID 解决了，但跨表事务仍是难题
   - 数据湖一般通过"重试 + 幂等"绕开

3. 强一致性的二级索引
   - 二级索引、Z-order 的维护仍是后台任务
   - 强一致读 + 即时分析还做不到

4. 复杂的权限模型
   - 行级 / 列级安全在 Iceberg 上能做但不原生
   - 需要 Ranger / Lake Formation 这类外部组件
```

## 总结

回到标题："数据湖与数据库的差异以及新的挑战"。

数据湖本质上不是要替代数据库，而是要解决**数据库解决不了的那一类问题**——数据量太大、数据类型太杂、数据来源太多样。它的核心架构选择是**存算分离**，配套的开放表格式(Iceberg / Delta / Hudi)补全了数据库表的关键能力：ACID、Schema 演进、分区演进、隐藏分区、文件裁剪、Time Travel。

但解决老问题的同时也引入了新挑战：

- 列存的压缩让单行更新变贵 → Copy-on-Write / Merge-on-Read 模式
- 散文件 + 对象存储的天然组合引入小文件问题 → Compaction
- 流式 upsert 仍有延迟与一致性权衡 → 持续运维
- 多表事务、强一致二级索引仍是开放问题 → 仍在演进

如果说数据库的工程核心是"**索引 + 事务 + 查询优化器**"，那数据湖的工程核心就变成了"**元数据 + 快照 + 合并策略**"。

> 思考题留两个：
> 1. 如果让你设计一个面向 AI 训练的数据存储层，它和数据湖的关系应该是替代 / 共生还是融合？
> 2. 在 AI 时代，结构化数据的"表"是否仍然是正确的抽象？
{: .prompt-tip }


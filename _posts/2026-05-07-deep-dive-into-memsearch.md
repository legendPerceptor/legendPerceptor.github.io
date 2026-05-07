---
title: 深入剖析MemSearch记忆系统
date: 2026-05-07 09:45:00 +0800
categories: [Tutorial]
tags: [memsearch, Claude Code]
pin: false
---

[memsearch](https://github.com/zilliztech/memsearch) 是一款基于Milvus向量数据库的语义记忆搜索引擎。它的核心设计理念是将markdown文件作为事实源，Milvus中的向量只是一个可以根据markdown文件重新构建的影子索引(shadow index)。memsearch会对markdown文件构成的知识库进行切片(chunk)，向量嵌入(embed)，储存，然后通过混合搜索的方式抽取记忆。它可以将你的OpenClaw、Claude Code等智能体的长期记忆存储在相同的地方，从而无缝使用不同的智能体一起完成工作。关于记忆系统的总体工作原理，可以参考我的另一篇文章[智能体与记忆体概述](/posts/agents-and-memory-systems)。

## 快速上手使用

在了解memsearch的实现细节之前，先在Claude Code中安装使用，了解它的表现和作用是一个非常好的学习方法。在Claude Code中只需要下面两行命令就可以完成安装了。

```bash
/plugin marketplace add zilliztech/memsearch
/plugin install memsearch
```

随后你和Claude Code的所有对话都会自动触发memsearch，它会根据每天的日期自动提取记忆存储到`.memsearch/memory/`目录下。比如你想查看今天的记忆内容，就可以用下面的命令打印出来。

```bash
cat .memsearch/memory/$(date +%Y-%m-%d).md
```

配置就是如此简单，memsearch作为一个插件会通过Claude Code hooks自动触发，每次你和Claude Code交互时，它会自动地进行记忆构建、演进和抽取。

## Claude Code插件工作原理

MemSearch通过Claude Code的[插件系统](https://code.claude.com/docs/en/plugins)接入智能体的生命周期，利用四个核心Hooks在恰当的时机自动完成记忆的捕获、索引和检索。

### 插件架构概览

MemSearch的Claude Code插件位于`plugins/claude-code/`，其核心文件结构如下：

```
plugins/claude-code/
├── hooks/
│   ├── common.sh          # 共享工具函数（JSON解析、memsearch检测等）
│   ├── hooks.json         # Hook配置：4个生命周期钩子
│   ├── session-start.sh   # 会话启动钩子
│   ├── user-prompt-submit.sh  # 用户提交提示钩子
│   ├── stop.sh            # 停止钩子（核心记忆生成）
│   └── session-end.sh     # 会话结束钩子
├── prompts/
│   └── summarize.txt      # 记忆摘要生成提示词
├── skills/
│   └── memory-recall/    # 拉取式记忆检索技能
│       └── SKILL.md
├── transcript.py         # JSONL转录文件解析器
└── scripts/
    └── derive-collection.sh  # 生成项目级collection名称
```

### 四个核心Hooks

#### 1. SessionStart：初始化与上下文注入

当Claude Code启动新会话时，`session-start.sh`会执行以下操作：

```bash
# 自动安装memsearch（如果缺失）
if ! command -v memsearch &>/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    uvx --upgrade --from 'memsearch[onnx]' memsearch
fi

# 首次使用：默认ONNX provider（免API Key）
if [ ! -f "$HOME/.memsearch/config.toml" ]; then
    memsearch config set embedding.provider onnx
fi

# 启动watch或执行一次性索引
start_watch   # Server模式（Milvus HTTP/TCP）
# 或
memsearch index "$MEMORY_DIR"  # Lite模式（本地.db）
```

同时，它会将最近两天的记忆标题和要点注入到会话上下文中，让Claude一启动就知道最近在做什么项目。

#### 2. UserPromptSubmit：轻量级提示

这个钩子非常简洁——当用户发送长度超过10个字符的提示时，注入一个系统提示：

```
[memsearch] Memory available
```

这告诉Claude：**如果需要历史上下文，可以调用memory-recall技能**。这是一种"推-拉"混合模式：钩子推送提示，Claude按需拉取记忆。

#### 3. Stop：记忆生成的核心

当用户结束会话（按`q`退出）时，`stop.sh`执行完整的记忆生成流程：

```
┌─────────────────────────────────────────────────────────────┐
│  1. 解析JSONL转录文件 → 提取最后一次对话轮次                  │
│         ↓                                                   │
│  2. 调用 `claude -p` 生成第三人称摘要（2-6个要点）           │
│         ↓                                                   │
│  3. 追加到今天的记忆文件（.memsearch/memory/YYYY-MM-DD.md）  │
│         ↓                                                   │
│  4. 立即执行 memsearch index 更新向量索引                    │
└─────────────────────────────────────────────────────────────┘
```

**关键设计**：只保存最后一次对话轮次，而不是整个会话。这样既能捕捉用户意图和关键操作，又避免记忆文件膨胀。

**记忆文件格式**：

```markdown
## Session 10:30

### 10:45
<!-- session:2026-05-07--10-30-00 turn:01JX... transcript:/path/to/transcript.jsonl -->
- User asked to add dark mode support to the dashboard
- Claude read `src/theme.ts` and identified the existing color system
- Claude proposed three implementation approaches in `docs/design/theme-v3.md`

### 11:20
<!-- session:2026-05-07--10-30-00 turn:01JY... transcript:... -->
- User selected the CSS variables approach
- Claude modified `src/styles/variables.css` with light/dark token sets
- Claude updated `src/components/ThemeProvider.tsx` to toggle dark mode
```

#### 4. SessionEnd：进程清理

优雅地停止watch进程和清理孤儿进程，避免Milvus Lite进程泄漏导致的内存问题。

### memory-recall技能：按需检索

当用户的问题可能需要历史上下文时（如"之前我们决定用什么方案？"），Claude会调用`memory-recall`技能：

```python
# 1. 语义搜索：memsearch search "query" --top-k 5 --json-output
# 2. 扩展相关片段：memsearch expand <chunk_hash>
# 3. 深度钻取：transcript.py --turn <uuid> --context 3
```

该技能支持**渐进式记忆披露**（Progressive Disclosure）：
- 初次检索：返回语义相关的chunk
- 展开：获取完整markdown段落
- 深度钻取：通过HTML注释锚点（`session:`、`turn:`、`transcript:`）追溯原始JSONL对话记录

### 文件锁与进程管理

Lite模式（本地Milvus）使用文件锁防止并发访问，因此只执行一次性索引，不启动watch进程。Server模式则通过`nohup`启动持久化的watch进程。

```bash
# 进程生命周期管理
stop_watch          # 停止watch
kill_orphaned_index # 清理孤儿进程（防止内存泄漏）
```

### 总结：数据流

```
用户对话 ──────────────────────────────────────────────────────────┐
                                                                  │
SessionStart                                                 SessionEnd
    │                                                              │
    ├── 初始化memsearch环境                                        │
    ├── 启动watch/索引                                 Stop Hook   │
    ├── 注入近期记忆上下文                                 │        │
    │                                                      │        │
    │                                              ┌─────┴─────┐ │
    │                                              │ 解析转录   │ │
    │                                              │ 生成摘要   │ │
    │                                              │ 保存记忆   │ │
    │                                              │ 更新索引   │ │
    │                                              └───────────┘ │
    │                                                              │
UserPromptSubmit                                                 │
    │                                                         SessionEnd
    └── 注入"[memsearch] Memory available"                     │
                                                                  │
                                              ┌───────────────────┘
memory-recall技能                                      │
    │                                                  ▼
    ├── memsearch search (语义检索)              .memsearch/memory/
    ├── memsearch expand (片段扩展)               ├── YYYY-MM-DD.md
    └── transcript.py (深度钻取)                 └── YYYY-MM-DD.md
                                                                  │
用户提问 ──────────────────────────────────────────────────────────┘
```

通过这套Hooks机制，MemSearch实现了**零侵入、零配置**的长期记忆能力——用户只需安装插件，所有的记忆工作都在后台自动完成。


## MemSearch的记忆检索是如何工作的？

MemSearch的记忆检索围绕Milvus向量数据库构建了一套**混合搜索**（Hybrid Search）系统，结合稠密向量语义检索和BM25全文关键字搜索，通过RRF（Ranking Fusion）重排序得到最终结果。本节将从Collection Schema、检索流程、索引更新三个维度剖析其内部机制。

### Collection Schema：影子索引的数据结构

MemSearch的Milvus Collection是整个系统的核心数据结构。它的设计体现了"markdown为事实源"的理念——向量只是索引，原始内容始终保存在collection中。

```python
# Milvus Collection字段定义
schema.add_field("chunk_hash",     VARCHAR, max_length=64,  is_primary=True)  # 复合主键
schema.add_field("embedding",      FLOAT_VECTOR, dim=dimension)                # 稠密向量
schema.add_field("content",        VARCHAR, max_length=65535, enable_analyzer)  # 原文（BM25 source）
schema.add_field("sparse_vector",  SPARSE_FLOAT_VECTOR)                         # BM25稀疏向量（自动生成）
schema.add_field("source",         VARCHAR, max_length=1024)                     # 文件路径
schema.add_field("heading",        VARCHAR, max_length=1024)                     # 最近标题
schema.add_field("heading_level",  INT64)                                        # 标题级别（0=前言）
schema.add_field("start_line",     INT64)                                        # 起始行
schema.add_field("end_line",       INT64)                                        # 结束行
```

**设计亮点**：

1. **`chunk_hash`作为主键**：基于`hash(source:path:startLine:endLine:contentHash:model)`生成，确保同一文件的同一段落无论何时索引都产生相同的ID。这意味着**重新索引幂等**——内容不变则ID不变，Milvus的upsert语义自动完成去重。

2. **`content`启用`enable_analyzer`**：这让Milvus能够对content字段进行分词和BM25计算，而`sparse_vector`字段通过BM25 Function从content自动生成，无需手动维护。

3. **双重向量字段**：`embedding`（稠密）和`sparse_vector`（稀疏）并存，分别服务于语义相似度和关键字匹配两种检索需求。关于稀疏向量是如何进行关键词匹配的，可以参考这篇文章[Full-Text Search in Milvus - What's Under the Hood](https://milvus.io/blog/full-text-search-in-milvus-what-is-under-the-hood.md)。

### 混合搜索：稠密向量 + BM25 + RRF

当执行`memsearch search "query"`时，实际发生的是一次**三阶段混合搜索**：

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           混合搜索流程                                    │
│                                                                          │
│  用户查询 "dark mode theme"                                               │
│           │                                                               │
│           ▼                                                               │
│  ┌─────────────────┐     ┌─────────────────┐                            │
│  │  稠密向量搜索    │     │   BM25搜索       │                            │
│  │  COSINE相似度    │     │   关键字匹配      │                            │
│  │  top_k*3 返回   │     │   top_k*3 返回   │                            │
│  └────────┬────────┘     └────────┬────────┘                            │
│           │                       │                                      │
│           └───────────┬───────────┘                                      │
│                       ▼                                                  │
│              ┌────────────────┐                                          │
│              │  RRF重排序      │  k=60                                   │
│              │  ( Reciprocal  │  score = Σ 1/(k+rank_i)                 │
│              │  Rank Fusion)  │                                          │
│              └────────┬───────┘                                          │
│                       ▼                                                  │
│              最终 top_k 结果                                              │
└──────────────────────────────────────────────────────────────────────────┘
```

**关键代码**（`store.py`）：

```python
# 稠密向量检索请求
dense_req = AnnSearchRequest(
    data=[query_embedding],
    anns_field="embedding",
    param={"metric_type": "COSINE", "params": {}},
    limit=top_k * 3,
)

# BM25检索请求（query_text直接作为BM25输入）
bm25_req = AnnSearchRequest(
    data=[query_text],        # 原始查询文本，Milvus自动做analyzer分词
    anns_field="sparse_vector",
    param={"metric_type": "BM25"},
    limit=top_k * 3,
)

# RRF融合（k=60）
results = self._client.hybrid_search(
    collection_name=self._collection,
    reqs=[dense_req, bm25_req],
    ranker=RRFRanker(k=60),
    limit=top_k,
)
```

**为什么取top_k*3再融合到top_k？**

因为两种检索的结果集可能重叠度不高（如语义相似但关键字不匹配的结果），需要先多取一些让RRF有足够的候选进行融合。如果配置了reranker模型（如bge-reranker-base），会在RRF结果上再做一轮交叉编码重排序。

### Markdown切片：如何把记忆切成可检索的Chunk

切片质量直接决定检索效果。MemSearch的`chunker.py`实现了基于标题层级的语义切片：

```python
def chunk_markdown(text, source="", max_chunk_size=1500, overlap_lines=2):
    """
    1. 按标题(# ## ###)切分sections
    2. 小于max_chunk_size的section直接作为一个chunk
    3. 大于max_chunk_size的section按段落边界再切分
    """
```

**切片策略**：

- **按标题边界**：每个标题下的内容作为一个语义单元，保留标题作为chunk的`heading`元数据
- **重叠行**：相邻chunk保留2行重叠，避免标题边界处的信息丢失
- **段落优先切割**：大段内容优先在段落边界（空行）切割，而不是粗暴地按字符数截断
- **单行超长处理**：如果单行本身超过max_chunk_size（如长URL、代码行），按句子边界切割

**Chunk ID的构成**：

```python
def compute_chunk_id(source, start_line, end_line, content_hash, model):
    raw = f"markdown:{source}:{start_line}:{end_line}:{content_hash}:{model}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
```

包含`model`是为了**兼容模型切换**：如果用户换了embedding模型，相同的文本会生成不同的chunk ID，从而触发重新索引。这是dimension适配的前置条件。

### 增量索引：智能更新机制

每次`memsearch index`执行时，MemSearch并不会全量重建索引，而是通过**比较chunk ID集合**实现增量更新：

```python
async def _index_file(self, f: ScannedFile, force=False):
    # 1. 切片
    chunks = chunk_markdown(text, source=source, ...)

    # 2. 计算新文件的chunk ID集合
    new_ids = {compute_chunk_id(c.source, c.start_line, c.end_line, c.content_hash, model) for c in chunks}

    # 3. 查询Milvus中旧文件的chunk ID集合
    old_ids = self._store.hashes_by_source(source)

    # 4. 删除文件中不再存在的chunks（stale = old_ids - new_ids）
    stale = old_ids - new_ids
    self._store.delete_by_hashes(list(stale))

    # 5. 只嵌入新的chunks（unchanged = new_ids ∩ old_ids，跳过）
    if not force:
        chunks = [c for c in chunks if compute_chunk_id(...) not in old_ids]

    # 6. Upsert剩余chunks
    return await self._embed_and_store(chunks)
```

**三个关键场景**：

1. **文件未变化**：chunk ID完全一致，跳过嵌入和存储
2. **文件部分修改**：只删除变化的旧chunk、嵌入新增chunk，保留未变化的部分
3. **文件被删除**：通过`indexed_sources()`扫描所有源文件，对比磁盘文件集合，删除没有对应文件的source的所有chunks

**Lite模式的特殊处理**：

Milvus Lite使用文件锁（SQLite后端），防止并发写入导致数据库损坏。因此Lite模式：
- 不启动watch进程（因为watch会持续打开文件）
- 每次`stop.sh`触发一次性索引，然后立即释放锁

### 渐进式记忆披露：Search → Expand → Deep Drill

检索结果返回给Claude Code的`memory-recall`技能后，用户可以获得三个递进的记忆层次：

```
Level 1: search 返回chunk摘要（500字符截断）
    │
    ▼ "expand <chunk_hash>"
Level 2: expand 返回chunk所在完整标题段落
    │
    ▼ HTML锚点 <!-- session:X turn:Y transcript:P -->
Level 3: transcript.py --turn <uuid> --context 3 返回原始对话记录
```

**Expand的实现**（`cli.py`）：

```python
def expand(chunk_hash):
    # 1. 从Milvus获取chunk的source和行号范围
    chunk = store.query(filter_expr=f'chunk_hash == "{chunk_hash}"')

    # 2. 读取原始markdown文件
    lines = Path(source).read_text().splitlines()

    # 3. 根据heading_level找到章节边界
    # heading_level=2 → 往前找##级别标题，往后找到同级或更高级标题为止
    section_content = _extract_section(lines, start_line, heading_level)

    # 4. 解析HTML锚点，提取session/turn/transcript信息
    anchor = re.search(r"<!--\s*session:(\S+)\s+turn:(\S+)\s+transcript:(\S+)\s*-->", section_content)
```

这个三层设计让Claude在获取足够上下文的同时，不会被无关的细节淹没。

### 总结：检索与更新的完整数据流

```
索引更新流程：
────────────────────────────────────────────────────────────────────────

  .memsearch/memory/YYYY-MM-DD.md
              │
              ▼
  chunk_markdown() ──切片──→ list[Chunk]
              │
              ▼
  compute_chunk_id() ──计算复合ID──→ chunk_hash
              │
              ▼
  hashes_by_source() ──查询旧ID──→ old_ids
              │
              ▼
  old_ids - new_ids ──删除失效chunks──→ stale
              │
              ▼
  new_ids - old_ids ──只嵌入新增──→ new_chunks
              │
              ▼
  upsert(records) ──Milvus upsert──→ collection

检索流程：
────────────────────────────────────────────────────────────────────────

  用户查询 "dark mode implementation"
              │
              ▼
  embedder.embed([query]) ──向量化──→ query_embedding
              │
              ▼
  ┌──────────────────────┐    ┌───────────────────────┐
  │ AnnSearchRequest     │    │ AnnSearchRequest       │
  │ anns_field=embedding │    │ anns_field=sparse_vector
  │ metric_type=COSINE   │    │ metric_type=BM25      │
  └──────────┬───────────┘    └───────────┬───────────┘
              │                            │
              └─────────┬──────────────────┘
                        ▼
              hybrid_search(RRFRanker(k=60))
                        │
                        ▼
              返回 top_k 结果（content + source + score）
```

这种设计确保了**markdown始终是唯一事实源**，Milvus向量只是可丢弃、可重建的影子索引——这正是MemSearch"markdown-first"设计理念的体现。


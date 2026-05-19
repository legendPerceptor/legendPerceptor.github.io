---
title: 记忆不是向量检索：AI Agent 记忆系统评价体系综述
date: 2026-05-19 09:45:00 +0800
categories: [Survey]
tags: [oG-Memory, MemSearch, Mem-Palace, Claude-Mem, LoCoMo, LongMemEval, MemoryAgentBench]
pin: false
mermaid: true
---


## 引言：为什么记忆系统的评价变得越来越重要

过去评价大语言模型，主要看模型本身的能力；但在Agent时代，系统的表现越来越取决于外部记忆层：它记住了什么，忘掉了什么，什么时候召回，如何处理冲突信息，如何跨对话保持用户偏好。**长上下文不是记忆系统**。长上下文解决的是能给模型塞进去多少内容，而记忆系统解决的是“长期积累后如何选择、更新、压缩、检索和治理”。

一个记忆系统通常有如下的生命周期：

```text
Memory Input
   ↓
写入：Extract / Select / Store
   ↓
组织：Index / Link / Summarize / Version
   ↓
召回：Retrieve / Rerank / Assemble Context
   ↓
使用：Reason / Act / Personalize
   ↓
维护：Update / Forget / Resolve Conflict / Governance
```

对记忆系统的评价是多维度的，有些维度已经有了比较优秀的量化方式，但还有大量的维度目前尚未有业界公认的评价指标。评价记忆系统这件事还属于一个研究者在不断探索的领域。概括来说，需要考虑如下的指标。

| 维度 | 关心的问题 |
|----------|--------------|
| 写入质量  |  是否把重要信息保存，避免垃圾记忆？  |
| 检索质量  |  需要时是否能找回相关记忆？ |
| 推理质量  |  能否基于多条记忆做时间推理、多跳推理、偏好判断？ |
| 更新能力  |  用户信息变化后，系统能否用新记忆覆盖旧记忆？ |
| 遗忘能力  |  过期、错误、隐私敏感、用户要求删除的记忆能否真正失效？ |
| 任务收益  |  记忆能否真的提升最终任务成功率，而不只是提升一些评测分数？ |
| 成本效率  |  token、延迟、存储、索引更新的成本如何？ |
| 可解释性与治理  |  用户能否看到、编辑、纠正、删除记忆？  |
| 安全隐私  |  是否避免越权记忆、跨用户污染、敏感信息泄露？ |
| 稳定性    |  面对噪声、矛盾、长时间跨度，记忆内容是否稳定？ |

## 现有的评价体系概述

### 1. LoCoMo: 长对话记忆评价

[LoCoMo](https://arxiv.org/abs/2402.17753) 是比较经典的长期对话记忆 benchmark。它构造了长达多 session 的对话，用来测试问答、事件总结、多模态对话生成等任务。论文介绍的 LoCoMo 对话平均约 300 turns、约 9K tokens，并覆盖最多 35 个 sessions。它适合评价“一个系统能否从长历史对话中找回事实、事件和时间线”。

使用方法：

1. 将LoCoMo的历史对话按时间顺序喂给记忆系统。
2. 让系统决定写入什么记忆。
3. 对每个问题，让系统检索相关记忆并回答。
4. 用exact match、LLM-as-judge、人工评估等方式判断回答是否正确。
5. 同时记录token数、延迟、检索条数、上下文长度。

LoCoMo比较适合于测试长对话事实回忆、时间线理解、多跳对话推理，但对记忆更新/遗忘、生产级成本压力的测试不够强。随着模型上下文窗口变长，把全文塞进上下文有时也能取得不错的结果，所以LoCoMo不一定能区分真正的记忆架构和暴力长上下文。


### 2. LongMemEval: 更系统的长期交互记忆评价

[LongMemEval](https://arxiv.org/abs/2410.10813) 专门评价长期聊天助手的记忆能力。它包含 500 个精心构造的问题，覆盖五类能力：信息抽取、多 session 推理、时间推理、知识更新、拒答/无法回答能力。论文还把长期记忆设计拆成 indexing、retrieval、reading 等阶段，并研究了 session decomposition、fact-augmented key expansion、time-aware query expansion 等设计。

使用方法：

1. 选择LongMemEval的数据集
2. 固定底层LLM，例如GPT-4o, Claude, Qwen，避免不同模型混淆结果。
3. 对比几种memory pipeline:
    - full context baseline
    - naive vector RAG
    - session-level retrieval
    - fact-level memory
    - graph memory
4. 对每类问题分别统计准确率
5. 单独分析错误类型：没检索到、检索到了但没读懂、时间判断错误、旧信息覆盖新信息失败、应该拒答但编造等。

LongMemEval适合侧跨session记忆、用户信息更新、时间推理、不知道时拒答，但对多模态记忆和复杂环境、工具使用经验的测评较弱。

### 3. MemoryAgentBench：面向 Agent 的增量式记忆评价

[MemoryAgentBench](https://arxiv.org/abs/2507.05257) 更接近 Agent 记忆系统。它强调 memory agent 不应该只在静态长文本上答题，而应该在多轮交互中逐步接收信息、写入记忆、更新记忆。它提出四个核心能力：accurate retrieval、test-time learning、long-range understanding、conflict resolution / selective forgetting。其 Hugging Face 页面也明确说明它以增量多轮交互设计评价 LLM agents 的记忆能力。

使用方法：

1. 让agent按顺序一段一段接收输入，而不是一次性看到全文。
2. 每个阶段允许agent写入/修改记忆。
3. 后续问题测试它是否真的利用了历史经验。
4. 对比：
    - 无记忆的agent
    - 只用聊天历史的agent
    - vector memory agent
    - graph memory agent
    - 使用其他记忆系统的agent
5. 看智能体在冲突信息、长期依赖、学习新规则时的表现。


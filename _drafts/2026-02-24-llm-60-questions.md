---
title: 大模型面试题60问和我的解答
date: 2026-02-24 10:45:00 +0800
categories: [AI]
tags: [LLM, Generative AI]
pin: false
---

## 第1章 大语言模型简介 Introduction to the LLM

Q1. 仅编码器(BERT类)、仅解码器(GPT类)和完整的编码器-解码器架构各有什么优缺点？
What are the advantages and disadvantages for encoder-only, decoder-only, encoder-decoder models?

仅编码器模型的特点是只有Transformer Encoder，因为attention机制没有Mask，有双向感知的能力。优点：(1)上下文感知，由于BERT使用双向编码器，它能同时考虑左侧和右侧的上下文信息，使得它在理解句子含义、语境和情感分析等任务表现很好；(2) 高效的表示学习(representation learning)，BERT能够捕捉文本的深层次语义特征，生成丰富的词向量和句向量，可以用于分类、问答等任务。
仅编码器模型的缺点：(1)不适用于生成任务，由于BERT缺乏解码器部分，无法生成出文本；(2)处理长文本能力有限，BERT的最大输入长度限制较短。

仅解码器模型的特点是只有Transformer Decoder，使用Causal Mask（不能看后面的token）。这种架构的核心优点是统一目标函数，训练的目标只有一个——Next Token Prediction，不需要区分pretrain和finetune的目标，不需要encoder-decoder对齐(没有cross attention)，极大地简化了训练pipeline，scaling，以及数据构造。GPT模型一直使用Decoder-only的原因是相信Scaling Law（只要模型够大，数据够多，通用智能会从自回归目标中涌现。

编码器+解码器的构造特点是同时拥有Transformer Encoder+Decoder，有cross attention，

Q2. 自注意力机制如何使大模型能够捕捉长距离依赖关系，它跟RNN有什么区别？
How does the self-attention mechanism allow LLMs to capture long-distance dependencies? What is the difference between this mechanism and RNN?


Q3. 大模型为什么有上下文长度的概念？为什么它是指输入和输出的总长度？
Why do LLMs have context-length? And why is it the total length of the input and output?
---
title: How does memsearch work and how to use it?
date: 2026-04-30 08:45:00 +0800
categories: [Tutorial]
tags: [memsearch, Claude Code]
pin: false
---

[memsearch](https://github.com/zilliztech/memsearch) is a semantic memory search engine for markdown files built on Milvus (a vector database). The core idea: take your markdown knowledge base, chunk it, embed it, store it in Milvus, then search it with hybrid dense + BM25 search. It unifies all your agents together so that they share the same memory.


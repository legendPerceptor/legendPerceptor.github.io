---
title: Claude Code Memory Systems Compared
date: 2026-04-28 12:45:00 +0800
categories: [Survey]
tags: [Agent Memory, Claude Code]
pin: false
---


Harness engineering and context engineering have been increasingly popular these days, as people realize that to unleash the power of strong large language models, what context is provided can be equivalently or more important than the strongness of the underlying model. The problems and solutions to when and where to save such information, when and how to load/retrive such information into the model context, form a field called agent memory systems. In this article, I want to focus on one of the most popular agents, Claude Code, explain how it works at a high level, and address existing memory systems designed around it.

## 1. What ships with Claude Code?

Claude Code mostly relies on the **current conversation context (prompt + history)**, and the **local codebase/files you expose to it**. There is not a strong notion of persistent semantic memory, cross-session recall, or structured storage (like vector DB, key-value, etc.) Instead of "remembering", it is more like *re-reading the world everytime you ask something*.

The memory in Claude Code is an ephemeral working memory buffer that saves recent messages and selected files, and possibly tool-assisted retrieval, e.g. searching your repo, reopening files. But once the session ends, memory is gone. There is no built-in consolidation, summarization, or recall layer.

Why is it designed this way? This is intentional for (1) determinism & safety --- no hidden evolving state; (2) simplicity --- no need for memory management; (3) transparency --- everything it "knows" is visible.

### How does Claude Code work as an agent?

Claude Code follows a standard agent loop: Reason -> Act -> Observe -> Repeat.

Step 1: Reason --- The model reads your instruction, recent conversation, selected files / repo, and plans what to do next.

Step 2: Act (tool use) --- It can invoke tools like: read files, search codebase, write/edit files, run shell commands.

Step 3: Observe --- It gets output from those tools (file contents, command output, errors).

Step 4: Iterate --- Feeds results back into the model, continues until the task is complete.

It is important to note that Claude Code is not a daemon, a background agent, or something that keeps thinking. Instead, every interaction is a bounded session. The loop runs only while responding to your request.

The context construction is the real magic that makes Claude Code so useful and popular.

The context includes: your prompts, chat history, relevant files (selected or auto included), and tool outputs from previous steps. The context is limited by context window, and usually Claude Code will not inject the full repo. The performance depends heavily on what context gets included, not just model intelligence.

Here are some example tools in Claude Code: `read_file(path)`, `write_file(path, content)`, `search(query)`, `run_command(cmd)`. The model does not execute code directly. It decides which tool to call, formats arguments, and interprets results. 

Note that there is no internal representation of your codebase --- unlike IDE, which builds AST index, symbol table, dependency graph --- Claude Code reconstructs understanding on demand via file reads, pattern matching and reasoning.

### What built-in memory systems are in Claude Code?

It is worth reading the [official Claude Code document on memory](https://code.claude.com/docs/en/memory).

`CLAUDE.md` is a special markdown file that Claude Code automatically reads and treats as persistent instructions / context. Think of it as system prompt. It can be at **user level** (global) if you put it under `~/.claude/CLAUDE.md`. It can be at **workspace level** if you put it under `~/projects/CLAUDE.md`, where there are multiple projects living under the same folder. It can also be **individual project level** for specific project instructions.

Typically, the `CLAUDE.md` file cannot be too long for good performance. And below are what usually go inside:

A. Project-level instructions: coding style, architecture overview, conventions.

B. Behavioral constraints: "don't modify X", "always run tests after editing", "use this framework".

C. Domain knowledge: business logic explanations, non-obvious design decisions.

This file is important because it becomes a manually curated, persistent memory injection point. Remember Claude Code itself is stateless, without `CLAUDE.md`, it has to rediscover everything each time you start a session.

There is another thing called `Automemory` in Claude Code (shipped in v2.1.59 on 26 February 2026), which is a lightweight persistent memory + heuristic retrieval system. Claude Code remembers recent interactions, keeps relevant info in the prompt and may summarize/compress older context. You can think of `Automemory` as "Conversation -> select important parts -> keep in context -> discard/summarize the rest". It prioritizes instructions, decisions, and important results. It usually keeps recent messages verbatim, summarizes older ones when context gets large. But it does not run semantic retrieval via vector search or indexing. Anthropic is continually developping the `Automemory` system, and the system can possibly become a full memory system in a future release.

It is worth to note a distinction between Claude Code and OpenClaw here: OpenClaw actually stores memory --- it persists state to disk, reloads it across sessions, updates it over time --- the memory is stateful and evolving, while Claude Code mostly only reads files and inject into prompts. OpenClaw has `openclaw.json` as global system memory, `sessions.json` as episodic memory, and long-term persistent memory. Nonetheless, since both Claude Code and OpenClaw are harness systems around LLMs, as the LLMs are always stateless, they both could possibly involve more complex memory systems via plugins, external databases, etc.

In the next sections, I will introduce works that claims to enhance Claude Code with their memory systems.

## 2. A bunch of markdown files to organize memory

> Overly investing in a custom setup built outside of native Claude functions like CLAUDE.md means you might be solving a problem that Claude is already solving - or about to. You could be setting yourself back.  --- John Conneely.

John Conneely posted an article [How I Finally Sorted My Claude Code Memory](https://www.youngleaders.tech/p/how-i-finally-sorted-my-claude-code-memory). The key takeway is the following prompt that you can directly paste into Claude Code, and it will start organizing memory files into the specified folder. This type of memory system is built on top of the model's capability to understand your prompt in plain text and do file organization according to the prompt.

```markdown
## Memory Management

Maintain a structured memory system rooted at .claude/memory/

### Structure

- memory.md — index of all memory files, updated whenever you create or modify one
- general.md — cross-project facts, preferences, environment setup
- domain/{topic}.md — domain-specific knowledge (one file per topic)
- tools/{tool}.md — tool configs, CLI patterns, workarounds

### Rules

1. When you learn something worth remembering, write it to the right file immediately
2. Keep memory.md as a current index with one-line descriptions
3. Entries: date, what, why — nothing more
4. Read memory.md at session start. Load other files only when relevant
5. If a file doesn't exist yet, create it

### Maintenance

When I say "reorganize memory":
1. Read all memory files
2. Remove duplicates and outdated entries
3. Merge entries that belong together
4. Split files that cover too many topics
5. Re-sort entries by date within each file
6. Update memory.md index
7. Show me a summary of what changed
```

After months of usage of such a memory system, your memory files will gradually grow so big that it is hard for the agent to find things. Claude Code mainly compress and write the memory in text and save them in some files, and when content is getting compressed, the keyword search stops working, thus causing trouble for Claude to find previous content in the memory.

## 3. Memsearch --- a cross-platform semantic memory for AI coding agents.

[Memsearch](https://github.com/zilliztech/memsearch) fundamentally upgrades Claude Code from "lightweight memory" to real, persistent, searchable memory system. Before memsearch, Automemory is heuristic, partially persistent, not queryable. Claude Code lacks (1) semantic retrieval; (2) cross-session continuity; (3) memory query interface.

**Architecture.** MemSearch is built on [Milvus](https://milvus.io/) (a vector database by Zilliz) and treats **markdown files as the source of truth**. The data flow is: markdown files are scanned, chunked by headings, embedded, and stored in Milvus as a rebuildable "shadow index." Retrieval uses **hybrid search** --- dense vector cosine similarity combined with BM25 sparse retrieval and Reciprocal Rank Fusion (RRF) reranking, with optional cross-encoder reranking. The default embedding model is ONNX bge-m3 (runs locally on CPU, no API key needed, ~558 MB download). Milvus supports three deployment modes: Milvus Lite (single-file, zero config), Zilliz Cloud (managed), or self-hosted via Docker.

**Claude Code Integration.** MemSearch integrates via the Claude Code **plugin system** using 4 shell hooks and 1 skill. A `SessionStart` hook starts a live file watcher and injects recent memories as cold-start context. A `UserPromptSubmit` hint injects a lightweight `[memsearch] Memory available` system message. A `Stop` hook extracts the last conversation turn, summarizes it via `claude -p --model haiku` in third-person, appends it to a daily markdown file, and re-indexes. The `memory-recall` skill runs in a forked subagent with three-layer progressive disclosure: L1 searches for ranked chunks, L2 expands to full markdown sections, and L3 drills into original `.jsonl` conversation files.

**Trade-offs.** The stop hook calls Claude Haiku for summarization on every turn (async, non-blocking), adding latency and cost. Milvus Lite is single-file/single-process, so production multi-user setups require Zilliz Cloud or self-hosted Milvus. The skill runs in a forked subagent that cannot see the main conversation history, which is intentional for isolation but limits contextual awareness. MemSearch is also cross-platform --- shared memory across Claude Code, OpenClaw, OpenCode, and Codex CLI.


## 4. Claude-Mem

[Claude Mem](https://github.com/thedotmack/claude-mem) seamlessly preserves context across sessions by automatically capturing tool usage observations, generating semantic summaries, and making them available to future sessions. This enables Claude to maintain continuity of knowledge about projects even after sessions end or reconnect.

**Architecture.** Claude-Mem has five core components: (1) **Lifecycle hooks** (`SessionStart`, `UserPromptSubmit`, `PostToolUse`, `Stop`, `SessionEnd`) intercept Claude Code events to capture tool usage observations in real time. (2) A **worker service** (HTTP API on port 37777, managed by Bun runtime) that processes observations, generates summaries via the Claude Agent SDK, and provides a web viewer UI. (3) **SQLite** with FTS5 full-text search for structured storage of sessions, observations, and summaries. (4) **Chroma vector database** for hybrid semantic + keyword search. (5) A **mem-search skill** with progressive disclosure --- a layered retrieval strategy that claims ~10x token savings versus naive retrieval. The data flow: hooks capture tool interactions, the worker compresses them via AI, stores structured observations in SQLite and vectors in Chroma, then injects relevant context back at session start.

**Claude Code Integration.** Claude-Mem integrates through two mechanisms: **hooks** (primary) register lifecycle hooks in settings for automatic, zero-user-intervention capture and injection; and **MCP tools** (secondary) expose 4 search tools (`search`, `timeline`, `get_observations`, etc.) for on-demand querying. It also works with Gemini CLI and OpenCode via `--ide` flag, and can be installed via the `/plugin marketplace`.

**Key features.** Automatic context capture with no manual intervention. Semantic summaries generated by AI. A web viewer UI at `localhost:37777` for browsing memory. Privacy control via `<private>` tags to exclude sensitive content. A citation system referencing past observations by ID. Multi-language support. A beta "Endless Mode" for extended sessions using biomimetic memory.

**Trade-offs.** Heavy dependency stack: requires Bun runtime, uv Python package manager, SQLite, and Chroma vector DB. Token cost for context injection at every session start. Worker service requires port 37777. Captures all tool usage by default --- users must explicitly tag content with `<private>` to exclude it. Licensed under AGPL-3.0.

## 5. Mempalace

[Mempalace](https://github.com/mempalace/mempalace) stores your conversation history as verbatim text and retrieves it with semantic search. It does not summarize, extract, or paraphrase.

**Architecture.** MemPalace organizes verbatim conversation text into a spatial hierarchy modeled on the ancient "memory palace" technique. **Wings** (people or projects) contain **Rooms** (specific topics like "auth-migration"), which contain **Drawers** (the original verbatim text chunks). Additional layers include **Halls** (conceptual categories: facts, events, discoveries, preferences, advice) and **Tunnels** (cross-wing connections between rooms sharing the same name across projects). A temporal **knowledge graph** backed by SQLite stores entity-relationship triples with validity windows. The embedding/search backend is **ChromaDB** (HNSW-based semantic search with metadata filtering), requiring ~300 MB of local disk space for the default embedding model. No LLM is required for the core search pipeline.

**Claude Code Integration.** Two mechanisms: (1) An **MCP server** exposing 29 tools via `python -m mempalace.mcp_server`, covering palace read/write, knowledge graph operations, navigation, agent diaries, and system settings. The `mempalace_status` tool returns a "Memory Protocol" instructing the AI to search before answering and file diary entries after sessions. (2) **Auto-save hooks** --- a Stop hook (fires every 15 human messages, tells the AI to save key content) and a PreCompact hook (fires before context compaction, forces an emergency save). These are zero-cost locally.

**Design philosophy.** The core principle is **verbatim storage, no summarization**. Original conversation text is stored as-is. Structure comes from the wing/room/hall metadata taxonomy, not from content transformation. This is a deliberate alternative to summary-based memory systems. MemPalace also publishes benchmark numbers: LongMemEval raw semantic search achieves 96.6% R@5 with zero LLM calls, and a hybrid pipeline reaches 98.4%.

**Trade-offs.** Verbatim storage means larger indexes compared to summary-based systems. Retrieval quality depends on good wing/room organization --- flat or poorly structured palaces may not benefit from metadata filtering. The default ChromaDB setup is single-machine with no built-in multi-device sync (an explicit design choice for privacy). Content between the 15-message save intervals can be lost if context compaction fires before the PreCompact hook executes.
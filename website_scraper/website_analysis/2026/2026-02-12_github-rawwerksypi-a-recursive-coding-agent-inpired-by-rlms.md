---
url: https://github.com/rawwerks/ypi
title: 'GitHub - rawwerks/ypi: A recursive coding agent inpired by RLMs'
scraped_at: '2026-02-12T22:53:02.483505+00:00'
word_count: 865
raw_file: 2026-02-12_github-rawwerksypi-a-recursive-coding-agent-inpired-by-rlms.txt
tldr: ypi is a recursive coding agent built on top of the Pi framework that enables self-delegation via an `rlm_query` function
  and `jj` workspace isolation to decompose complex programming tasks.
key_quote: Pi already has a bash REPL. We add one function — rlm_query — and a system prompt that teaches Pi to use it recursively.
durability: medium
content_type: mixed
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people: []
tools:
- ypi
- Pi
- bash
- rlm_query
- jj
- npm
- npx
- bunx
- curl
- make
- grep
- sed
libraries: []
companies:
- GitHub
- Anthropic
tags:
- ai-agents
- recursive-programming
- coding-assistant
- version-control
- llm-automation
---

### TL;DR
ypi is a recursive coding agent built on top of the Pi framework that enables self-delegation via an `rlm_query` function and `jj` workspace isolation to decompose complex programming tasks.

### Key Quote
"Pi already has a bash REPL. We add one function — rlm_query — and a system prompt that teaches Pi to use it recursively."

### Summary
**What it is**
*   A recursive coding agent built on `Pi`, inspired by Recursive Language Models (RLMs).
*   Named after the Y combinator in lambda calculus.
*   Enables an LLM to decompose problems, analyze large contexts, and write code through self-delegation.

**Architecture & Mechanics**
*   **Core Components:**
    *   `SYSTEM_PROMPT.md`: Teaches the LLM to use recursion.
    *   `rlm_query`: The function allowing the agent to call itself (spawns a child process).
    *   `bash`: The REPL environment provided by Pi.
*   **Recursion Flow:**
    *   Depth 0 (Root): Has bash + `rlm_query`.
    *   Depth 1 (Child): Has bash + `rlm_query`, operates in an isolated `jj` workspace.
    *   Depth 2+ (Leaf): Has bash only (max depth default).
*   **File Isolation:** Uses `jj` (Jujutsu) version control. Children edit files in their own workspace; parents review via `jj diff` and absorb via `jj squash`.

**Installation & Usage**
*   **Install:** `npm install -g ypi`, `curl` script, or manual git clone.
*   **Run:**
    *   Interactive: `ypi`
    *   One-shot: `ypi "Refactor the error handling in this repo"`
    *   Specific Model: `ypi --provider anthropic --model claude-sonnet-4-5-20250929 "prompt"`

**Configuration & Controls**
*   **Budget/Time:** `RLM_BUDGET` (max spend), `RLM_TIMEOUT` (wall-clock limit).
*   **Limits:** `RLM_MAX_CALLS` (max invocations), `RLM_MAX_DEPTH` (recursion depth).
*   **Optimization:** `RLM_CHILD_MODEL` (e.g., "haiku") to use cheaper models for sub-tasks.
*   **Debugging:** `rlm_cost` command to check spend/tokens; `PI_TRACE_FILE` for logging.

**Development**
*   Uses `jj` for version control (Git is only for sync).
*   Testing: `make test-fast` (no LLM), `make test-e2e` (real LLM, costs money).

### Assessment
**Durability:** Medium. While the concept of recursive LLMs is stable, this is a specific tool implementation tightly coupled to the `Pi` agent, `npm` distribution, and specific model IDs (e.g., `claude-sonnet-4-5-20250929`). The reliance on `jj` (Jujutsu) for isolation is a specific architectural choice that may require maintenance if `jj` APIs change.

**Content type:** Mixed (Tool documentation / Tutorial).

**Density:** High. The text efficiently packs architecture diagrams, command-line usage, environment variables, and development workflow details into a short README.

**Originality:** Primary source. This is the official documentation for the `ypi` project.

**Reference style:** Refer-back. Useful for looking up specific environment variables or installation commands, and for understanding the specific implementation of recursive isolation using `jj`.

**Scrape quality:** Good. The ASCII diagram rendered correctly, code blocks are intact, and all configuration tables are preserved.
---
url: https://github.com/badlogic/pi-mono/pull/903/files
title: 'Add support for intercepting bash by mitsuhiko · Pull Request #903 · badlogic/pi-mono'
scraped_at: '2026-02-11T09:59:36.634146+00:00'
word_count: 1102
raw_file: raw/2026-02-11_add-support-for-intercepting-bash-by-mitsuhiko-pull-request-.txt
tldr: A pull request adding a `before_bash_exec` event hook to the pi coding agent extension API, allowing developers to intercept,
  modify, or block bash commands before execution.
key_quote: 'Fired before a bash command executes (tool calls and user `!`/`!!`). Use it to rewrite commands or override execution
  settings. You can also block execution by returning `{ block: true, reason?: string }`.'
durability: medium
content_type: mixed
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people:
- mitsuhiko
tools:
- pi
- uv
- bash
libraries:
- '@mariozechner/pi-coding-agent'
companies: []
tags:
- coding-agent
- extension-api
- bash-interception
- python-tools
- typescript
---

### TL;DR
A pull request adding a `before_bash_exec` event hook to the pi coding agent extension API, allowing developers to intercept, modify, or block bash commands before execution.

### Key Quote
> "Fired before a bash command executes (tool calls and user `!`/`!!`). Use it to rewrite commands or override execution settings. You can also block execution by returning `{ block: true, reason?: string }`."

### Summary
**New API Feature: `before_bash_exec` event**
- Fires before any bash command executes (from tool calls or user `!`/`!!` prefixes)
- Return `BashExecOverrides` object to modify: `command`, `cwd`, `env`, `shell`, `args`, `timeout`
- Return `{ block: true, reason?: string }` to reject command entirely
- For `env`, set keys to `undefined` to remove them

**Example Extension: `uv.ts`**
- Demonstrates intercepting `python`/`python3` commands and rewriting to `uv run python`
- Blocks `pip`/`pip3` commands with guidance to use `uv run --with` or `--script` instead
- Uses `tool_result` hook to append hints when Python import errors occur, suggesting `uv run --with <module>` pattern
- Regex patterns for detecting: Python commands, pip commands, traceback/import errors, module names

**Also Updated: `tool_result` event**
- Clarified documentation: can override error state with `{ content: [...], isError: true }`
- Setting `isError: true` on successful result forces error treatment

### Assessment
**Durability** (medium): The API pattern is stable, but this is a specific feature addition to an evolving coding agent. The `uv` example may need updates as `uv` evolves.

**Content type**: Announcement / Reference (mixed) — documents new API capability with working example code

**Density** (high): Compact diff with substantial TypeScript example showing real-world usage patterns

**Originality**: Primary source — this is the actual PR introducing the feature

**Reference style**: Refer-back — useful as API documentation for `before_bash_exec` and as a template for writing similar interceptors

**Scrape quality** (good): Captured the diff content, code examples, and one insightful comment about direnv integration. The comment notes a gap: missing directory context when agent accesses files.
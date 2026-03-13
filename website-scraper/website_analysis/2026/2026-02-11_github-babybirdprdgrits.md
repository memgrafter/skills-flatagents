---
url: https://github.com/babybirdprd/grits
title: GitHub - babybirdprd/grits
scraped_at: '2026-02-11T10:10:04.727702+00:00'
word_count: 406
raw_file: raw/2026-02-11_github-babybirdprdgrits.txt
tldr: Grits is a Git-native, local-first issue tracker (v3.0.0) that doubles as an "Active State Store" for AI agents, enforcing
  separation between research and execution to reduce LLM hallucinations and context drift.
key_quote: Grits transforms from a passive tracker into an Active State Store (World Model) for agents. It enforces a strict
  separation between research and execution to minimize LLM 'hallucinations' and context drift.
durability: medium
content_type: mixed
density: medium
originality: primary
reference_style: refer-back
scrape_quality: good
people: []
tools:
- grits-cli
- git
libraries: []
companies: []
tags:
- issue-tracking
- ai-agents
- git-native
- local-first
- rust
---

### TL;DR
Grits is a Git-native, local-first issue tracker (v3.0.0) that doubles as an "Active State Store" for AI agents, enforcing separation between research and execution to reduce LLM hallucinations and context drift.

### Key Quote
> "Grits transforms from a passive tracker into an Active State Store (World Model) for agents. It enforces a strict separation between research and execution to minimize LLM 'hallucinations' and context drift."

### Summary
**What it is:**
- Local-first issue tracker written in Rust, designed for both AI agents and humans
- Stores data in two formats: SQLite (`grits.db`) for fast queries, JSONL (`issues.jsonl`) for Git-versioned source of truth
- Version 3.0.0, MIT licensed

**Installation:**
```bash
cargo install grits-cli
# Or download binary from Releases
```

**Core commands:**
- `gr onboard` — Initialize in a project
- `gr pulse` — Returns Rich Context JSON (Intent + Plan + Rules + History) for session hydration
- `gr create "title" --description "intent" --design "plan" --start-work` — Create tasks
- `gr update --append` — Append-only logging to Execution Log
- `gr workon` — Warns if Coder starts without a design
- `gr dep add` — Link child tasks to parents with optional migration
- `gr context assemble --symbols "files"` — Bundle relevant code without topology map
- `gr show <id>` — Display Rich Context + Execution Log

**Agent-focused data model:**
| Field | Purpose | Agent Role |
|-------|---------|------------|
| `description` | User's Intent | Intent |
| `design` | Implementation Plan | Strategy |
| `acceptance_criteria` | Success Definitions | Proof |
| `notes` | Execution Log (append-only) | Memory |

**Agent integration:**
- Planner Skill (`.agent/skills/grits-plan/SKILL.md`) — Architect instructions
- Coder Skill (`.agent/skills/grits-code/SKILL.md`) — Builder instructions
- Follows Agent Skills open specification

### Assessment
**Durability:** Medium. The core concept (Git-native issue tracking with agent-ready structured data) is durable, but v3.0.0 suggests an evolving API and the agent skill integrations may change as AI tooling matures.

**Content type:** Reference / announcement (mixed)

**Density:** Medium. README covers installation, key commands, and architecture but stays high-level. Agent skill files referenced but not included.

**Originality:** Primary source. This is the canonical repository for the tool.

**Reference style:** Refer-back. You'd return to check commands and the data model when using or integrating with the tool.

**Scrape quality:** Good. All essential content captured—installation, commands, architecture, and agent integration points. No code blocks or images appeared missing.
---
url: https://github.com/Piebald-AI/claude-code-system-prompts/tree/main
title: 'GitHub - Piebald-AI/claude-code-system-prompts: All parts of Claude Code''s system prompt, 18 builtin tool descriptions,
  sub agent prompts (Plan/Explore/Task), utility prompts (CLAUDE.md, compact, statusline, magic docs, WebFetch, Bash cmd,
  security review, agent creation). Updated for each Claude Code version.'
scraped_at: '2026-02-11T10:31:29.673137+00:00'
word_count: 2778
raw_file: 2026-02-11_github-piebald-aiclaude-code-system-prompts-all-parts-of-cla.txt
tldr: A comprehensive catalog of all 110+ system prompts, tool descriptions, sub-agent prompts, and system reminders extracted
  from Claude Code v2.1.39, maintained with changelog tracking across 95 versions.
key_quote: This repository contains an up-to-date list of all Claude Code's various system prompts and their associated token
  counts as of Claude Code v2.1.39 (February 10th, 2026). It also contains a CHANGELOG.md for the system prompts across 95
  versions since v2.0.14.
durability: low
content_type: reference
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people: []
tools:
- claude-code
- tweakcc
- mcp-cli
- bash
- webfetch
- github-actions
- todowrite
- task-tool
libraries: []
companies:
- piebald-ai
- anthropic
- github
tags:
- claude-code
- system-prompts
- prompt-engineering
- reverse-engineering
- ai-tools
---

### TL;DR
A comprehensive catalog of all 110+ system prompts, tool descriptions, sub-agent prompts, and system reminders extracted from Claude Code v2.1.39, maintained with changelog tracking across 95 versions.

### Key Quote
> "This repository contains an up-to-date list of all Claude Code's various system prompts and their associated token counts as of Claude Code v2.1.39 (February 10th, 2026). It also contains a CHANGELOG.md for the system prompts across 95 versions since v2.0.14."

### Summary

**What this repository contains:**
- Extracted system prompts from Claude Code's compiled JavaScript source code
- Token counts for each prompt component
- Changelog tracking changes across 95 versions (v2.0.14 → v2.1.39)
- Updated within minutes of each Claude Code release

**Why multiple "system prompts":**
Claude Code uses 110+ conditionally-loaded strings including:
- Environment-dependent sections
- Builtin tool descriptions (Write, Bash, TodoWrite, etc.)
- Separate prompts for sub-agents (Explore, Plan, Task)
- AI-powered utility functions (compaction, CLAUDE.md generation, session titles)

**Cataloged components:**

| Category | Examples |
|----------|----------|
| **Agent Prompts (34 items)** | Explore (516 tks), Plan mode enhanced (633 tks), Task tool (294 tks), Security-review (2610 tks), CLAUDE.md creation (384 tks), Conversation summarization (1121 tks) |
| **System Prompts (31 items)** | Main system prompt (269 tks), Tool usage policy (564 tks), Learning mode (1042 tks), MCP CLI (1333 tks), Hooks configuration (1461 tks) |
| **System Reminders (40 items)** | Plan mode active (1429 tks), Task tools reminder (123 tks), Todo list changed (61 tks), Token usage (39 tks) |
| **Tool Descriptions (22 items)** | TodoWrite (2167 tks), SendMessageTool (1241 tks), Task (1214 tks), Bash (1067 tks), ReadFile (476 tks) |
| **Embedded Data** | GitHub Actions workflow (527 tks), Session memory template (292 tks) |

**Related tool - tweakcc:**
- Customizes individual prompt pieces as markdown files
- Patches npm or binary Claude Code installations
- Provides diffing and conflict management

### Assessment

**Durability (low):** Highly version-dependent. Claude Code releases frequently and this repo tracks changes across 95 versions. Content will be stale within weeks/months as new versions ship.

**Content type:** Reference / documentation (reverse-engineered)

**Density (high):** Extremely dense catalog listing every prompt component with exact token counts. No padding—pure inventory data.

**Originality:** Primary source (extracted directly from Claude Code's compiled source). This is the definitive reference for Claude Code's internal prompts.

**Reference style:** Refer-back. Useful for understanding how Claude Code works, customizing via tweakcc, or researching agentic tool design patterns. The changelog makes it valuable for tracking Anthropic's evolution of the system.

**Scrape quality (good):** Full catalog captured with all token counts and categories. The repository structure is completely represented. The actual prompt *content* lives in separate files linked from this README, so those would need separate scraping for full text.
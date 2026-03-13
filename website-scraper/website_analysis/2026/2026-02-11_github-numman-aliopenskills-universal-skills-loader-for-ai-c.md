---
url: https://github.com/numman-ali/openskills
title: 'GitHub - numman-ali/openskills: Universal skills loader for AI coding agents - npm i -g openskills'
scraped_at: '2026-02-11T10:13:27.590072+00:00'
word_count: 813
raw_file: raw/2026-02-11_github-numman-aliopenskills-universal-skills-loader-for-ai-c.txt
tldr: OpenSkills is a CLI tool that ports Anthropic's SKILL.md system to any AI coding agent (Cursor, Windsurf, Aider, Codex)
  by generating compatible `<available_skills>` XML blocks in AGENTS.md files.
key_quote: OpenSkills brings Anthropic's skills system to every AI coding agent — Claude Code, Cursor, Windsurf, Aider, Codex,
  and anything that can read AGENTS.md
durability: medium
content_type: reference
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people: []
tools:
- openskills
- cursor
- windsurf
- aider
- codex
- claude-code
- git
libraries: []
companies:
- Anthropic
tags:
- ai-coding-agents
- cli-tool
- skills-system
- developer-tools
- llm-workflow
---

### TL;DR
OpenSkills is a CLI tool that ports Anthropic's SKILL.md system to any AI coding agent (Cursor, Windsurf, Aider, Codex) by generating compatible `<available_skills>` XML blocks in AGENTS.md files.

### Key Quote
"OpenSkills brings Anthropic's skills system to every AI coding agent — Claude Code, Cursor, Windsurf, Aider, Codex, and anything that can read AGENTS.md"

### Summary

**What it does**: Universal installer for SKILL.md files that mimics Claude Code's skills system, enabling any agent that reads AGENTS.md to use skills via `npx openskills read <skill-name>`.

**Installation & Setup**:
```bash
npx openskills install anthropics/skills  # from GitHub
npx openskills install ./local-skills     # local path
npx openskills install git@github.com:org/private-skills.git
npx openskills sync                       # generates AGENTS.md
```

**Key Commands**:
- `install <source>` — Install from GitHub, local path, or git repo
- `sync [-y] [-o <path>]` — Update AGENTS.md with skills XML block
- `read <name>` — Load skill content (what agents call)
- `list` — Show installed skills
- `update [name...]` — Refresh skills from sources
- `remove <name>` / `manage` — Remove skills

**Storage Locations**:
- Default: `./.claude/skills/` (project-local)
- `--universal`: `./.agent/skills/` (avoids Claude Code conflicts)
- `--global`: `~/.claude/skills/`

**Skill Format** (matches Anthropic's spec):
```yaml
---
name: pdf
description: Description here
---
# Skill instructions in markdown
```

**Structure**:
```
my-skill/
├── SKILL.md
├── references/
├── scripts/
└── assets/
```

**vs MCP**: Skills = static instructions + resources (no server). MCP = dynamic tools. They solve different problems.

**Requirements**: Node.js 20.6+, Git

### Assessment
**Durability** (medium): The tool itself is version-dependent, but the SKILL.md format is Anthropic's spec—if Anthropic changes it, this tool follows. GitHub-based distribution means no centralized marketplace lock-in.

**Content type**: reference / documentation

**Density** (high): README is well-structured with concrete commands, file paths, format examples, and comparison tables. No fluff.

**Originality**: primary source — this is the canonical documentation for the OpenSkills tool

**Reference style**: refer-back — you'll return for command syntax and options when using the tool

**Scrape quality** (good): Full README content captured including code blocks, tables, and command examples. No images appear missing.
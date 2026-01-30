---
url: https://github.com/nicobailon/pi-rewind-hook
title: 'GitHub - nicobailon/pi-rewind-hook: Pi agent hook for rewinding file changes during coding sessions'
scraped_at: '2026-01-30T20:35:52.210902+00:00'
word_count: 810
raw_file: 2026-01-30_github-nicobailonpi-rewind-hook-pi-agent-hook-for-rewinding-.txt
tldr: A Pi agent extension that uses git refs to create automatic checkpoints during coding sessions, allowing developers
  to rewind file states (via `/branch`) while optionally preserving conversation history.
key_quote: Creates automatic checkpoints using git refs, allowing you to restore files to previous states while optionally
  preserving conversation history.
durability: medium
content_type: mixed
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people:
- nicobailon
tools:
- git
- node
- npx
- pi
libraries:
- pi-rewind-hook
companies: []
tags:
- git
- checkpoints
- ai-agent
- version-control
- workflow
---

### TL;DR
A Pi agent extension that uses git refs to create automatic checkpoints during coding sessions, allowing developers to rewind file states (via `/branch`) while optionally preserving conversation history.

### Key Quote
"Creates automatic checkpoints using git refs, allowing you to restore files to previous states while optionally preserving conversation history."

### Summary
- **What it does**: Extends the Pi AI agent to snapshot code changes before every turn, enabling "time travel" to restore files or revert conversation threads without losing progress.
- **Prerequisites**:
  - Pi agent v0.35.0+ (unified extensions system)
  - Node.js
  - A Git repository
- **Installation**:
  - Standard: `pi install npm:pi-rewind-hook`
  - Manual/Curl: `curl -fsSL ... | node`
  - Automatically migrates config from the old `hooks/rewind` directory if upgrading.
- **Configuration**: Edit `~/.pi/agent/settings.json` to enable `silentCheckpoints` (default `false`), which hides status messages and footer checkpoint counts.
- **Mechanism**:
  - Creates git refs in `refs/pi-checkpoints/` at session start and before every turn.
  - Scoped per-session (100 checkpoint limit) to avoid interference between parallel sessions.
  - Only tracks working directory changes (unstaged files).
- **Rewind/Restore Options**:
  - Access via `/branch` command or `Tab` tree navigation.
  - **Restore all**: Rewind code + conversation.
  - **Code only**: Restore files to specific point but keep new conversation context.
  - **Conversation only**: Reset chat but keep current file state.
  - **Undo last file rewind**: Reverts the most recent file restoration.
- **Resume support**: When using `pi --resume`, creates a single "resume checkpoint" allowing file restoration to the session start state, even if branching to messages before the session began.
- **Cleanup**:
  - List refs: `git for-each-ref refs/pi-checkpoints/`
  - Delete refs: `git for-each-ref --format='%(refname)' refs/pi-checkpoints/ | xargs -n1 git update-ref -d`

### Assessment
- **Durability** (medium): Tightly coupled to Pi agent versions (requires v0.35.0+). While the git ref strategy is timeless, API compatibility with the Pi agent may change as the tool evolves.
- **Content type**: mixed (tutorial / reference). Provides installation commands and usage logic.
- **Density** (high): Concise documentation packed with specific commands, JSON configuration examples, and logic tables for restore options.
- **Originality**: primary source. This is the official README for the GitHub repository.
- **Reference style**: refer-back. Useful for looking up specific restore behaviors or manual git commands for cleanup.
- **Scrape quality** (good): The text captures installation methods, configuration details, and the restore option matrix completely. No code blocks or logic seem missing.
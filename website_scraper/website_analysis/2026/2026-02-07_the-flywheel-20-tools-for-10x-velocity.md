---
url: https://agent-flywheel.com/flywheel
title: The Flywheel - 20 Tools for 10x Velocity
scraped_at: '2026-02-07T06:10:33.192636+00:00'
word_count: 2494
raw_file: 2026-02-07_the-flywheel-20-tools-for-10x-velocity.txt
tldr: A suite of 20 interoperable CLI tools (written in Go, Rust, Python, and TypeScript) designed to orchestrate multiple
  AI coding agents in parallel, enabling autonomous multi-project workflows, safety guardrails, and procedural memory systems.
key_quote: The magic isn't in any single tool. It's in how they work together. Using three tools is 10x better than using
  one.
durability: medium
content_type: mixed
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people:
- Dicklesworthstone
- Sydney Brenner
tools:
- Named Tmux Manager
- MCP Agent Mail
- Ultimate Bug Scanner
- Beads Viewer
- beads_rust
- Coding Agent Session Search
- CASS Memory System
- Coding Agent Account Manager
- Simultaneous Launch Button
- Destructive Command Guard
- Repo Updater
- Meta Skill
- Remote Compilation Helper
- WezTerm Automata
- Brenner Bot
- System Resource Protection Script
- Automated Plan Reviser Pro
- JeffreysPrompts CLI
- Process Triage
- X Archive Search
libraries:
- Tantivy
- SQLite
- MCP
- AST-grep
- Tmux
- WezTerm
- Git
- Cargo
companies:
- GitHub
- Stripe
tags:
- ai-agents
- workflow-automation
- cli-tools
- software-development
- devops
---

### TL;DR
A suite of 20 interoperable CLI tools (written in Go, Rust, Python, and TypeScript) designed to orchestrate multiple AI coding agents in parallel, enabling autonomous multi-project workflows, safety guardrails, and procedural memory systems.

### Key Quote
"The magic isn't in any single tool. It's in how they work together. Using three tools is 10x better than using one."

### Summary
**Tool/Ecosystem Overview**
The "Agent Flywheel" is a collection of 20 command-line tools that function as a cohesive system for autonomous AI development. Instead of a single monolithic app, these small, composable utilities communicate via JSON, MCP (Model Context Protocol), and Git to create a self-reinforcing workflow.

**Key Architectural Components**
- **Coordination:** Tools like *NTM* (Named Tmux Manager) spawn agents, while *MCP Agent Mail* acts as an inbox system for agents to communicate and claim file reservations to prevent conflicts.
- **Task Management:** *Beads Viewer* uses graph theory (PageRank, critical path analysis) to prioritize tasks, while *beads_rust* handles local-first issue tracking with dependency graphs.
- **Safety & Guardrails:** *Destructive Command Guard* (DCG) SIMD-accelerates blocking of dangerous commands (e.g., `rm -rf`, `git reset --hard`), while *Simultaneous Launch Button* (SLB) enforces a "two-person rule" for risky operations via cryptographic approval workflows.
- **Memory & Search:** *CASS* indexes all agent sessions for sub-60ms search, and the *CASS Memory System* stores procedural playbooks so agents learn from past mistakes.
- **Fleet Management:** *Repo Updater* (RU) syncs multiple repos in parallel with AI-generated commit messages; *CAAM* manages API key rotation for multiple provider accounts.

**Featured Workflows**
- **Daily Parallel Progress:** Spawn 6+ agents across 8+ projects; agents find work via BV and coordinate via Mail, resulting in merged PRs after 3+ hours of autonomous work.
- **Multi-Repo Morning Sync:** `ru sync -j4` clones/pulls updates across 20+ repos while agents spawn and begin executing tasks before the user finishes coffee.
- **Agents Reviewing Agents:** One agent writes code, another uses "fresh eyes" prompts (provided in the text) to review for bugs, security flaws, or UX issues.

**Prompts Provided**
The text includes specific, copy-pasteable prompts for:
- Deep Code Exploration (tracing execution flows and finding bugs)
- Agent Peer Review (first-principles diagnosis of other agents' work)
- Comprehensive Beads Planning (transforming docs into executable task graphs)
- Intelligent Commit Grouping (logically connected commits with detailed messages)

### Assessment
- **Durability**: Low/Medium. While the concept of multi-agent orchestration is durable, these specific tools are tightly coupled to current AI APIs (Claude, Codex, Gemini) and terminal environments (Tmux, WezTerm). API changes or platform shifts could render specific CLI tools obsolete quickly.
- **Content type**: mixed (marketing / technical reference / tutorial).
- **Density**: High. The text is packed with specific tool names, acronyms (NTM, BV, SLB), installation commands, and concrete workflow descriptions with little fluff.
- **Originality**: primary source. This appears to be the official landing page or documentation for a specific project ("The Flywheel").
- **Reference style**: refer-back. Useful for retrieving the specific prompt templates or installation commands (`curl` strings) for the individual tools.
- **Scrape quality**: good. The scrape successfully captured the tool descriptions, the specific prompt templates, and the installation commands without obvious truncation.
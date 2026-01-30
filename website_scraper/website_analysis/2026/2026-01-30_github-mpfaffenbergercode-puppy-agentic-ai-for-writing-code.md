---
url: https://github.com/mpfaffenberger/code_puppy/
title: 'GitHub - mpfaffenberger/code_puppy: Agentic AI for writing code'
scraped_at: '2026-01-30T20:37:23.534048+00:00'
word_count: 2740
raw_file: 2026-01-30_github-mpfaffenbergercode-puppy-agentic-ai-for-writing-code.txt
tldr: A privacy-focused, CLI-based AI coding agent that competes with IDEs like Cursor and Windsurf by supporting 65+ model
  providers, custom JSON agents, and a "zero telemetry" architecture.
key_quote: Who needs an IDE when you have 1024 angry puppies?
durability: medium
content_type: mixed
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people:
- mpfaffenberger
tools:
- uv
- uvx
- code-puppy
- dbos
- mcp
- agent-creator
- tui
- sqlite
- postgresql
libraries:
- vllm
- llama.cpp
- sglang
companies:
- Cursor
- Windsurf
- OpenAI
- Anthropic
- xAI
- Groq
- Mistral
- Together AI
- Perplexity
- DeepInfra
- Cohere
- Synthetic
- Cerebras
- Google
tags:
- ai-coding
- cli-tools
- privacy
- agents
- llm-integration
---

### TL;DR
A privacy-focused, CLI-based AI coding agent that competes with IDEs like Cursor and Windsurf by supporting 65+ model providers, custom JSON agents, and a "zero telemetry" architecture.

### Key Quote
"Who needs an IDE when you have 1024 angry puppies?"

### Summary
**Tool/Library**: Code Puppy
**What it does**: An agentic AI CLI tool for writing, editing, and reviewing code without the overhead or privacy risks of full IDE-based AI suites.

**Installation & Usage**
- **Install**: Requires `uv` (Python package installer).
  ```bash
  # Install UV
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Run Code Puppy
  uvx code-puppy
  ```
- **Windows**: Recommended to install as a global tool for keyboard shortcuts.

**Core Features**
- **Model Agnostic**: Integrates with `models.dev` to access 65+ providers (OpenAI, Anthropic, xAI, Groq, etc.).
- **Discovery**: Use `/add_model` to open a TUI for browsing and configuring endpoints and API keys.
- **OpenAI Compatibility**: Supports 39+ providers via OpenAI-compatible endpoints (e.g., Groq, xAI, Perplexity).
- **Round Robin**: Mitigates rate limits by rotating requests across multiple API keys/models via `~/.code_puppy/extra_models.json`.

**Configuration & Extensibility**
- **Custom Commands**: Create markdown files in `.claude/commands/`, `.github/prompts/`, or `.agents/commands/` to define custom slash commands (filename = command name).
- **Standards**: Supports `AGENT.md` files for project-specific coding standards.
- **DBOS Integration**: Optional durable execution via DBOS for checkpointing workflows (toggle with `/set enable_dbos true`).

**Agent System**
- **Architecture**: Supports built-in Python agents and user-defined JSON agents.
- **Management**: Use `/agent` to list or switch agents; `/agent agent-creator` starts a guided setup.
- **JSON Agent Schema**: Define agents in `~/.code_puppy/agents/*-agent.json` with fields:
  - `name`, `display_name`, `description`
  - `system_prompt` (string or array)
  - `tools` (e.g., `read_file`, `edit_file`, `agent_run_shell_command`)
  - `tools_config` (timeout, retries)
- **Tools**: Agents can be restricted to specific capabilities (e.g., Read-only, File editor, Shell access).
- **Discovery**: Scans `code_puppy/agents/` for Python classes and `~/.code_puppy/agents/` for JSON files.

**Privacy Policy**
- **Zero Telemetry**: No analytics, crash reports, or prompt logging.
- **Local Only**: Capable of running entirely with local servers (vLLM/Llama.cpp).
- **Data Sovereignty**: Prompts sent only to configured LLM providers; no middleman data harvesting.

### Assessment
- **Durability** (medium): The core CLI architecture and privacy stances are durable, but specific provider endpoints, APIs, and the `models.dev` integration are subject to change as the AI landscape shifts.
- **Content type**: reference / tutorial
- **Density** (high): Packed with specific commands, JSON schemas, environment variables, and configuration paths.
- **Originality**: primary source. This is the official readme for the project.
- **Reference style**: refer-back. Useful for looking up specific JSON schemas for agents or installation commands.
- **Scrape quality** (good): The capture appears complete, covering installation, features, agent configuration, and policy details.
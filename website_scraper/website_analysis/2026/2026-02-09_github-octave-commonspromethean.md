---
url: https://github.com/octave-commons/promethean
title: GitHub - octave-commons/promethean
scraped_at: '2026-02-09T06:13:38.822804+00:00'
word_count: 1082
raw_file: 2026-02-09_github-octave-commonspromethean.txt
tldr: Promethean is a TypeScript monorepo framework for building embodied AI agents, featuring a modular architecture based
  on message brokers, functional programming principles, and specialized packages for LLM interaction, MCP servers, and Discord
  orchestration.
key_quote: A modular cognitive architecture for building embodied AI agents with reasoning, perception-action loops, and emotionally
  mediated decision structures.
durability: medium
content_type: mixed
density: high
originality: primary
reference_style: deep-study
scrape_quality: good
people:
- riatzukiza
tools:
- pnpm
- nx
- ava
- docker-compose
- pm2
- git
- corepack
- obsidian
- curl
libraries:
- '@promethean-os/kanban'
- '@promethean-os/broker-service'
- '@promethean-os/llm'
- '@promethean-os/mcp'
- '@promethean-os/cephalon'
- '@promethean-os/promethean-cli'
- redis
companies:
- github
- huggingface
- ollama
- discord
tags:
- ai-agents
- typescript
- monorepo
- microservices
- llm-orchestration
---

### TL;DR
Promethean is a TypeScript monorepo framework for building embodied AI agents, featuring a modular architecture based on message brokers, functional programming principles, and specialized packages for LLM interaction, MCP servers, and Discord orchestration.

### Key Quote
"A modular cognitive architecture for building embodied AI agents with reasoning, perception-action loops, and emotionally mediated decision structures."

### Summary
**Tool/Library/Framework**

*   **Overview**: A comprehensive AI agent orchestration system built as a TypeScript monorepo with 70+ packages, utilizing a microservices architecture connected via a message broker.
*   **Architecture**:
    *   **Frontend/UI**: Discord UI, Web Frontend, CLI Tools.
    *   **Backbone**: Message Broker Service (WebSocket pub/sub + task queues).
    *   **Core Services**: LLM Service (text gen), MCP Server (tools & auth).
*   **Key Packages**:
    *   `@promethean-os/kanban`: AI-friendly task management and workflow automation (CLI commands: `search`, `create`, `update-status`).
    *   `broker-service`: WebSocket-based pub/sub with topic routing and Redis persistence.
    *   `@promethean-os/llm`: Text generation supporting multiple providers (Ollama, HuggingFace) with streaming.
    *   `@promethean-os/mcp`: Model Context Protocol server with RBAC, tool composition, and GitHub integration.
    *   `@promethean-os/cephalon`: Production Discord agent runner using ENSO protocol and guardrails.
    *   `@promethean-os/promethean-cli`: Unified interface (`prom`) for script discovery and package management.
*   **Getting Started**:
    *   Requires `pnpm` 9 (via Corepack).
    *   Setup commands:
        ```bash
        git clone https://github.com/PrometheanAI/promethean.git
        cd promethean
        corepack enable && corepack prepare pnpm@9 --activate
        pnpm install
        pnpm dev:all
        ```
    *   Note: Several packages are git submodules (e.g., `kanban`, `mcp`, `auth-service`) and require `git submodule update --init packages/<name>`.
*   **Development Workflow**:
    *   Uses Nx workspace, AVA testing, and ESM modules.
    *   Strict naming convention `@promethean-os/*`.
    *   Supports Docker Compose for containerized development.
    *   PM2 used for running daemons and agents (`pnpm gen:ecosystem`).
*   **Pipelines**: Complex workflows defined in `pipelines.json` include `symdocs`, `simtasks`, `codemods`, `buildfix`, and `test-gap`.
*   **Documentation**: The repository doubles as an Obsidian vault; configuration available in `docs/vault-config`.

### Assessment
- **Durability**: Medium. While the architectural patterns (modular services, message brokers) are relatively stable, this is an active software project with 70+ packages, specific dependency versions (pnpm 9), and a submodule structure prone to change.
- **Content type**: reference / tutorial
- **Density**: High. The text is packed with specific package names, command-line instructions, code snippets, and architectural details with minimal fluff.
- **Originality**: primary source. This is the official README for the GitHub repository.
- **Reference style**: deep-study. Due to the complexity of the monorepo, submodule setup, and specific architectural patterns, this requires careful reading to implement correctly.
- **Scrape quality**: good. All code blocks, lists, package names, and structural diagrams appear to be captured accurately. Note: The "Last updated" timestamp in the source text reads "2025-11-16", which may indicate a system clock anomaly or future-dated content, but the scrape itself is intact.
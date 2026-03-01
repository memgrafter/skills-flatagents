---
url: https://github.com/coleam00/Archon
title: 'GitHub - coleam00/Archon: Beta release of Archon OS - the knowledge and task management backbone for AI coding assistants.'
scraped_at: '2026-02-11T10:14:30.976073+00:00'
word_count: 2240
raw_file: raw/2026-02-11_github-coleam00archon-beta-release-of-archon-os-the-knowledg.txt
tldr: Archon is an open-source MCP server that gives AI coding assistants (Claude Code, Cursor, Windsurf) access to a custom
  knowledge base with RAG search and task management capabilities.
key_quote: Archon is the command center for AI coding assistants. For you, it's a sleek interface to manage knowledge, context,
  and tasks for your projects. For the AI coding assistant(s), it's a Model Context Protocol (MCP) server to collaborate on
  and leverage the same knowledge, context, and tasks.
durability: medium
content_type: mixed
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people:
- coleam00
tools:
- claude-code
- cursor
- windsurf
- kiro
- claude-desktop
- docker-desktop
- ollama
libraries:
- react
- fastapi
- pydanticai
- socket.io
- vite
- tailwindcss
companies:
- openai
- google
- supabase
tags:
- mcp-server
- rag
- knowledge-management
- ai-coding-assistants
- task-management
---

### TL;DR
Archon is an open-source MCP server that gives AI coding assistants (Claude Code, Cursor, Windsurf) access to a custom knowledge base with RAG search and task management capabilities.

### Key Quote
"Archon is the command center for AI coding assistants. For you, it's a sleek interface to manage knowledge, context, and tasks for your projects. For the AI coding assistant(s), it's a Model Context Protocol (MCP) server to collaborate on and leverage the same knowledge, context, and tasks."

### Summary

**What it does:**
- Provides MCP server interface for AI coding assistants to access shared knowledge and tasks
- Web crawling for documentation sites (sitemaps, individual pages)
- Document upload and processing (PDFs, Word docs, markdown, text)
- Vector search with advanced RAG strategies (hybrid search, contextual embeddings, reranking)
- Hierarchical project/task management with AI-assisted creation
- Multi-LLM support: OpenAI (default), Gemini, Ollama

**Architecture (microservices):**
| Service | Port | Purpose |
|---------|------|---------|
| UI (React + Vite) | 3737 | Web dashboard |
| Server (FastAPI) | 8181 | Core API, crawling, processing |
| MCP Server | 8051 | Protocol interface for AI clients |
| Agents (PydanticAI) | 8052 | AI/ML operations, reranking |
| Agent Work Orders | 8053 | Claude Code CLI automation (optional) |

**Requirements:**
- Docker Desktop
- Node.js 18+ (hybrid dev mode)
- Supabase account (cloud or local) with PGVector
- OpenAI API key (or Gemini/Ollama)

**Setup (Quick Start):**
```bash
git clone -b stable https://github.com/coleam00/archon.git
cd archon
cp .env.example .env  # Add Supabase credentials
# Run migration/complete_setup.sql in Supabase SQL Editor
docker compose up --build -d
# Access http://localhost:3737 for onboarding
```

**Key Make commands:**
- `make dev` — Hybrid mode (backend Docker, frontend local with hot reload)
- `make dev-docker` — All services in Docker
- `make stop` / `make test` / `make lint`

**Notable details:**
- Currently in beta — expect bugs, actively seeking contributions
- Replaces old vision ("agenteer" - AI agent that builds other agents)
- License: Archon Community License v1.2 — free and open, but can't sell as-a-service without permission

### Assessment

**Durability: Medium.** Core concepts (MCP, RAG, knowledge management for AI assistants) are stable patterns, but this is beta software under active development with changing features. Architecture and setup instructions will likely evolve.

**Content type:** Mixed — primarily reference documentation with tutorial elements for setup.

**Density: High.** Packed with specific commands, port numbers, configuration variables, architecture diagrams, and troubleshooting steps. Minimal fluff.

**Originality:** Primary source — official repository README from the project maintainers.

**Reference style:** Refer-back. You'd return to this for initial setup, troubleshooting, Make command reference, and understanding the service architecture when configuring MCP connections.

**Scrape quality:** Good. All sections captured including tables, code blocks, architecture diagram (ASCII), and configuration details. No obviously missing content.
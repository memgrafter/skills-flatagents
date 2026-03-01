---
url: https://github.com/Mirrowel/LLM-API-Key-Proxy
title: 'GitHub - Mirrowel/LLM-API-Key-Proxy: Universal LLM Gateway: One API, every LLM. OpenAI/Anthropic-compatible endpoints
  with multi-provider translation and intelligent load-balancing.'
scraped_at: '2026-02-11T09:53:15.504802+00:00'
word_count: 3210
raw_file: 2026-02-11_github-mirrowelllm-api-key-proxy-universal-llm-gateway-one-a_1.txt
tldr: A self-hosted FastAPI proxy that unifies multiple LLM providers (Gemini, OpenAI, Anthropic, plus exclusive providers
  like Antigravity) behind OpenAI/Anthropic-compatible endpoints with intelligent key rotation, failover, and OAuth support.
key_quote: One proxy. Any LLM provider. Zero code changes.
durability: medium
content_type: reference
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people: []
tools:
- FastAPI
- Docker
- uvicorn
- curl
libraries:
- rotator-library
- httpx
- asyncio
- LiteLLM
- OpenAI-SDK
- Anthropic-SDK
companies:
- OpenAI
- Anthropic
- Google
- NVIDIA
- Cohere
- Mistral
- Groq
- OpenRouter
tags:
- llm-proxy
- api-gateway
- key-rotation
- oauth
- multi-provider
---

### TL;DR
A self-hosted FastAPI proxy that unifies multiple LLM providers (Gemini, OpenAI, Anthropic, plus exclusive providers like Antigravity) behind OpenAI/Anthropic-compatible endpoints with intelligent key rotation, failover, and OAuth support.

### Key Quote
"One proxy. Any LLM provider. Zero code changes."

### Summary

**Core Architecture**
- Two components: API Proxy (FastAPI app) + Resilience Library (standalone Python library for key management)
- Provides `/v1/chat/completions` (OpenAI) and `/v1/messages` (Anthropic) endpoints
- Works with any app supporting custom base URLs: Claude Code, Cursor, Continue, SillyTavern, JanitorAI, etc.

**Model Naming Convention**
- Format: `provider/model_name` (e.g., `gemini/gemini-2.5-flash`, `openai/gpt-4o`)
- The prefix routes requests to the correct backend

**Exclusive Provider Support**
- **Antigravity**: Gemini 3 Pro, Gemini 2.5 Flash (thinking mode), Claude Opus/Sonnet 4.5, GPT-OSS 120B
- **Gemini CLI**: Internal Google API access with higher rate limits
- **Qwen Code** and **iFlow**: OAuth-based providers

**Installation Options**
- Pre-built binaries (Windows/macOS/Linux) with TUI launcher
- Docker: `ghcr.io/mirrowel/llm-api-key-proxy:latest`
- Python source: clone, venv, pip install

**Key Features**
- Automatic key rotation with escalating cooldowns (10s → 30s → 60s → 120s)
- OAuth credential management via interactive TUI or `python -m rotator_library.credential_tool`
- Quota groups for models sharing rate limits
- Model whitelists/blacklists with wildcard support
- Per-provider concurrency limits and rotation modes (balanced vs sequential)
- Detailed request logging with `--enable-request-logging`

**Configuration**
- Credentials stored in `.env` file
- Multiple keys per provider via `_1`, `_2` suffixes (e.g., `GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`)
- Stateless deployment supported via environment variable export

**Deployment**
- Docker Compose recommended; requires creating `key_usage.json` file first
- Cloud platforms (Render, Railway, Vercel) supported with stateless OAuth export
- VPS/systemd service setup documented

**API Endpoints**
- `GET /` — status check
- `POST /v1/chat/completions` — OpenAI format
- `POST /v1/messages` — Anthropic format (Claude Code compatible)
- `GET /v1/models` — list available models with pricing
- `POST /v1/embeddings`, `/v1/token-count`, `/v1/cost-estimate`

### Assessment

**Durability**: Medium. Core architecture and provider-agnostic design are stable, but provider-specific features (Antigravity models, Gemini CLI internals), API details, and environment variable names will evolve with upstream changes.

**Content type**: Reference / tutorial mixed

**Density**: High. Extremely detailed with specific configuration patterns, environment variables, timeout values, and deployment commands throughout.

**Originality**: Primary source. This is the official project README.

**Reference style**: Refer-back / deep-study. You'd return to this when configuring providers, troubleshooting OAuth, or tuning rotation/concurrency settings.

**Scrape quality**: Good. Full README captured with all sections, code blocks, and tables intact.
---
url: https://github.com/Mirrowel/LLM-API-Key-Proxy
title: 'GitHub - Mirrowel/LLM-API-Key-Proxy: Universal LLM Gateway: One API, every LLM. OpenAI/Anthropic-compatible endpoints
  with multi-provider translation and intelligent load-balancing.'
scraped_at: '2026-02-11T04:46:08.002716+00:00'
word_count: 3210
raw_file: raw/2026-02-11_github-mirrowelllm-api-key-proxy-universal-llm-gateway-one-a.txt
tldr: A self-hosted FastAPI proxy that unifies multiple LLM providers (Gemini, OpenAI, Anthropic, OpenRouter, plus exclusive
  providers like Antigravity/Gemini CLI) behind OpenAI and Anthropic-compatible API endpoints, with intelligent key rotation,
  failover, and OAuth support.
key_quote: One proxy. Any LLM provider. Zero code changes.
durability: medium
content_type: mixed
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people: []
tools:
- fastapi
- docker
- claude-code
- cursor
- continue
- sillytavern
- janitorai
libraries:
- rotator-library
- litellm
- openai
- anthropic
companies:
- google
- openai
- anthropic
- openrouter
- groq
- mistral
- nvidia
- cohere
- qwen
tags:
- llm-proxy
- api-gateway
- multi-provider
- load-balancing
- key-rotation
---

### TL;DR
A self-hosted FastAPI proxy that unifies multiple LLM providers (Gemini, OpenAI, Anthropic, OpenRouter, plus exclusive providers like Antigravity/Gemini CLI) behind OpenAI and Anthropic-compatible API endpoints, with intelligent key rotation, failover, and OAuth support.

### Key Quote
"One proxy. Any LLM provider. Zero code changes."

### Summary

**What It Does**
- Provides universal `/v1/chat/completions` (OpenAI) and `/v1/messages` (Anthropic) endpoints
- Routes requests to configured providers based on `provider/model_name` format (e.g., `gemini/gemini-2.5-flash`)
- Works with Claude Code, Cursor, Continue, SillyTavern, JanitorAI, and any app supporting custom base URLs

**Components**
- **API Proxy**: FastAPI application handling endpoint translation
- **Resilience Library**: Standalone Python library (`rotator_library`) for key management, rotation, failover

**Installation Options**
- Pre-built releases: Download from GitHub Releases, run `proxy_app.exe` or `./proxy_app`
- Docker: `ghcr.io/mirrowel/llm-api-key-proxy:latest` (multi-arch amd64/arm64)
- Python source: Clone, venv, `pip install -r requirements.txt`

**Key Features**
- Automatic key rotation with escalating cooldowns (10s → 30s → 60s → 120s)
- Multi-key support per provider (`GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, etc.)
- OAuth providers: Gemini CLI, Antigravity, Qwen Code, iFlow
- Interactive TUI for configuration and credential management
- Model whitelists/blacklists with wildcard support
- Per-provider concurrency limits and rotation modes (balanced/sequential)

**Exclusive Provider Support**
- **Antigravity**: Gemini 3 Pro, Gemini 2.5 Flash (thinking mode), Claude Opus/Sonnet 4.5, GPT-OSS 120B
- **Gemini CLI**: Internal Google API access with higher rate limits, quota tracking
- **Qwen Code / iFlow**: OAuth Device Flow and Authorization Code flows

**Configuration**
- Credentials stored in `.env` file with `PROXY_API_KEY` for proxy authentication
- OAuth credentials in `oauth_creds/` directory or exported to environment variables
- Supports stateless deployment (Railway, Render, Vercel) via environment variable export

**Endpoints**
- `GET /` — Status check
- `POST /v1/chat/completions` — OpenAI format
- `POST /v1/messages` — Anthropic format (Claude Code compatible)
- `GET /v1/models` — List available models with pricing
- `POST /v1/embeddings`, `/v1/token-count`, `/v1/cost-estimate`

**Usage Example**
```python
from openai import OpenAI
client = OpenAI(base_url="http://127.0.0.1:8000/v1", api_key="your-proxy-api-key")
response = client.chat.completions.create(model="gemini/gemini-2.5-flash", messages=[...])
```

**Licensing**
- Proxy application: MIT License
- Resilience library: LGPL-3.0

### Assessment

**Durability** (medium): Core architecture and concepts are stable, but provider-specific features (especially Antigravity, Gemini CLI) depend on internal/research APIs that may change. OAuth flows and API formats evolve. Expect maintenance needed every 6-12 months.

**Content type**: Reference / tutorial / mixed — comprehensive documentation mixing installation guides, API reference, configuration options, and deployment instructions.

**Density** (high): Packed with specific environment variables, endpoint paths, provider-specific features, and configuration examples. Very little padding.

**Originality**: Primary source — this is the official repository documentation for an original tool.

**Reference style**: Refer-back / deep-study — comprehensive enough to return to for configuration details, provider-specific setup, and troubleshooting. Not a skim-once document.

**Scrape quality** (good): Full README content captured including all tables, code blocks, and configuration examples. No apparent gaps.
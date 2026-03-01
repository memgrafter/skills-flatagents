---
url: https://github.com/badrisnarayanan/antigravity-claude-proxy
title: 'GitHub - badrisnarayanan/antigravity-claude-proxy: Proxy that exposes Antigravity provided claude / gemini models,
  so we can use them in Claude Code and OpenClaw (Clawdbot)'
scraped_at: '2026-02-11T10:40:26.684298+00:00'
word_count: 1013
raw_file: 2026-02-11_github-badrisnarayananantigravity-claude-proxy-proxy-that-ex.txt
tldr: A Node.js proxy server that translates Anthropic API requests to Google's Cloud Code backend, enabling free use of Claude
  and Gemini models through Claude Code CLI—with significant account ban risk.
key_quote: Using this proxy may violate Google's Terms of Service. A small number of users have reported their Google accounts
  being banned or shadow-banned.
durability: low
content_type: tutorial
density: high
originality: synthesis
reference_style: refer-back
scrape_quality: good
people: []
tools:
- antigravity-claude-proxy
- claude-code
- openclaw
- clawdbot
- antigravity
libraries:
- opencode-antigravity-auth
- claude-code-proxy
companies:
- Google
- Anthropic
tags:
- claude-code
- api-proxy
- google-cloud-code
- llm-tools
- free-ai-access
---

### TL;DR
A Node.js proxy server that translates Anthropic API requests to Google's Cloud Code backend, enabling free use of Claude and Gemini models through Claude Code CLI—with significant account ban risk.

### Key Quote
"Using this proxy may violate Google's Terms of Service. A small number of users have reported their Google accounts being banned or shadow-banned."

### Summary
**What it does:**
- Exposes Anthropic-compatible API backed by Antigravity's Cloud Code
- Transforms requests: Anthropic Messages API format → Google Generative AI format → Antigravity Cloud Code API
- Converts responses back with full thinking/streaming support
- Enables Claude Code CLI and OpenClaw/ClawdBot to use Claude + Gemini models via Google's infrastructure

**Installation:**
```bash
# Quick start (no install)
npx antigravity-claude-proxy@latest start

# Global install
npm install -g antigravity-claude-proxy@latest
antigravity-claude-proxy start
```

**Requirements:**
- Node.js 18+
- Antigravity app installed (single-account mode) OR Google account(s) for multi-account

**Authorization methods:**
1. WebUI at `http://localhost:8080` → Accounts tab → Add Account
2. CLI: `antigravity-claude-proxy accounts add` (desktop) or `--no-browser` flag (headless)
3. Auto-detect from installed Antigravity app

**Claude Code configuration** (`~/.claude/settings.json`):
```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "test",
    "ANTHROPIC_BASE_URL": "http://localhost:8080",
    "ANTHROPIC_MODEL": "claude-opus-4-6-thinking"
  }
}
```

**Available model aliases:**
- Claude: `claude-opus-4-6-thinking`, `claude-sonnet-4-5-thinking`, `claude-sonnet-4-5`
- Gemini: `gemini-3-pro-high[1m]`, `gemini-3-flash[1m]`

**Key features:**
- Multi-account load balancing
- Web management console
- Device fingerprinting
- macOS menu bar app
- Supports both Proxy Mode (free via Google) and Paid Mode (official Anthropic credits)

**Endpoints:**
- Default: `http://localhost:8080`
- Health: `/health`
- Account limits: `/account-limits?format=table`

### Assessment
**Durability: low.** Tied directly to Antigravity's Cloud Code API and Google's ToS enforcement—both could break this at any time. Model naming conventions suggest rapid iteration.

**Content type:** tool documentation / tutorial

**Density:** high. Packed with specific commands, configuration snippets, environment variables, and setup paths for multiple platforms.

**Originality:** synthesis. Builds on opencode-antigravity-auth and claude-code-proxy projects.

**Reference style:** refer-back. You'll return for configuration snippets, model names, and troubleshooting when setting up or debugging.

**Scrape quality:** good. Full README captured with code blocks, warnings, and configuration examples intact.
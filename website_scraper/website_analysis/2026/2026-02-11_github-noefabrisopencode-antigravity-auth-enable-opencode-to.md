---
url: https://github.com/NoeFabris/opencode-antigravity-auth
title: 'GitHub - NoeFabris/opencode-antigravity-auth: Enable Opencode to authenticate against Antigravity (Google''s IDE)
  via OAuth so you can use Antigravity rate limits and access models like gemini-3-pro and claude-opus-4-5-thinking with your
  Google credentials.'
scraped_at: '2026-02-11T10:15:48.033121+00:00'
word_count: 2583
raw_file: 2026-02-11_github-noefabrisopencode-antigravity-auth-enable-opencode-to.txt
tldr: An unofficial OpenCode plugin that authenticates via Google OAuth to access Claude and Gemini models through Google's
  internal Antigravity IDE infrastructure, with multi-account rotation and dual quota pooling.
key_quote: Using this plugin may violate Google's Terms of Service. A small number of users have reported their Google accounts
  being banned or shadow-banned.
durability: low
content_type: mixed
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people:
- NoeFabris
tools:
- opencode
- antigravity
- gemini-cli
libraries:
- opencode-antigravity-auth
- '@ai-sdk/google'
companies:
- Google
tags:
- oauth-authentication
- google-cloud
- ai-models
- opencode-plugin
- api-proxy
---

### TL;DR
An unofficial OpenCode plugin that authenticates via Google OAuth to access Claude and Gemini models through Google's internal Antigravity IDE infrastructure, with multi-account rotation and dual quota pooling.

### Key Quote
"Using this plugin may violate Google's Terms of Service. A small number of users have reported their Google accounts being banned or shadow-banned."

### Summary
**What it does**: Routes OpenCode API requests through Google's Antigravity infrastructure, letting users access models like `claude-opus-4-5-thinking`, `claude-opus-4-6-thinking`, `claude-sonnet-4-5`, `gemini-3-pro`, and `gemini-3-flash` using Google credentials and quotas.

**Key Features**:
- Multi-account support with automatic rotation when rate-limited
- Dual quota system: Antigravity quota (default) + Gemini CLI quota (fallback or primary via `cli_first: true`)
- Thinking models with configurable budgets (8192-32768 tokens)
- Google Search grounding for Gemini models
- Auto-recovery from session/tool errors

**Installation**:
```json
// ~/.config/opencode/opencode.json
{ "plugin": ["opencode-antigravity-auth@latest"] }
```
Then run `opencode auth login` to authenticate with Google.

**Models Available**:
- Antigravity quota: `antigravity-gemini-3-pro`, `antigravity-gemini-3-flash`, `antigravity-claude-sonnet-4-5`, `antigravity-claude-sonnet-4-5-thinking`, `antigravity-claude-opus-4-5-thinking`, `antigravity-claude-opus-4-6-thinking`
- Gemini CLI quota: `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-3-flash-preview`, `gemini-3-pro-preview`

**Configuration Files**:
| File | Path |
|------|------|
| Main config | `~/.config/opencode/opencode.json` |
| Accounts | `~/.config/opencode/antigravity-accounts.json` |
| Plugin config | `~/.config/opencode/antigravity.json` |

**Key Config Options**:
- `account_selection_strategy`: "sticky" (1 account), "hybrid" (2-5), "round-robin" (5+)
- `cli_first`: Route Gemini to CLI quota first
- `keep_thinking`: Preserve Claude thinking across turns (may destabilize)
- `soft_quota_threshold_percent`: Skip accounts above this usage (default 90%)

**Known Issues**:
- Safari OAuth fails due to HTTPS-Only Mode — use Chrome/Firefox
- MCP servers with numeric tool names cause errors
- Fresh Google accounts at very high risk of bans
- Permission errors require manual GCP project setup with `cloudaicompanion.googleapis.com` enabled

### Assessment
**Durability** (low): Heavily dependent on Google's internal Antigravity API, which could change or be locked down at any time. The plugin explicitly notes "APIs may change without notice." Also, ToS enforcement could eliminate this approach entirely.

**Content type**: Mixed — tutorial for setup, reference for configuration options and model definitions, troubleshooting guide.

**Density** (high): Packed with specific configuration snippets, model definitions with context/output limits, file paths, error messages, and numerous configuration options with defaults explained.

**Originality**: Primary source — this is the canonical documentation for an independent open-source project.

**Reference style**: Refer-back — users will return for model configuration snippets, troubleshooting specific errors, and tuning configuration options.

**Scrape quality** (good): Full README content captured including all tables, code blocks, and configuration examples. No images appear to be missing that would affect comprehension.
---
url: https://github.com/vercel-labs/agent-browser
title: 'GitHub - vercel-labs/agent-browser: Browser automation CLI for AI agents'
scraped_at: '2026-02-11T10:46:39.524142+00:00'
word_count: 3281
raw_file: 2026-02-11_github-vercel-labsagent-browser-browser-automation-cli-for-a.txt
tldr: A CLI tool from Vercel Labs that provides headless browser automation specifically designed for AI agents, featuring
  a fast Rust CLI with Node.js daemon, accessibility-tree snapshots with deterministic element refs, and support for cloud
  browser providers.
key_quote: 'Refs provide deterministic element selection from snapshots... Deterministic: Ref points to exact element from
  snapshot... AI-friendly: Snapshot + ref workflow is optimal for LLMs'
durability: medium
content_type: reference
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people: []
tools:
- agent-browser
- chromium
- appium
- playwright
libraries:
- agent-browser
- '@sparticuz/chromium'
companies:
- Vercel Labs
- Browserbase
- Browser Use
- Kernel
tags:
- browser-automation
- ai-agents
- cli-tools
- headless-browser
- web-testing
---

### TL;DR
A CLI tool from Vercel Labs that provides headless browser automation specifically designed for AI agents, featuring a fast Rust CLI with Node.js daemon, accessibility-tree snapshots with deterministic element refs, and support for cloud browser providers.

### Key Quote
"Refs provide deterministic element selection from snapshots... Deterministic: Ref points to exact element from snapshot... AI-friendly: Snapshot + ref workflow is optimal for LLMs"

### Summary

**What it does**: Headless browser automation CLI optimized for AI agents. Uses accessibility tree snapshots with reference IDs (@e1, @e2) for deterministic element selection instead of fragile CSS selectors.

**Installation**:
```bash
npm install -g agent-browser
agent-browser install  # Downloads Chromium
# Alternative: brew install agent-browser
```

**Core workflow for AI agents**:
```bash
agent-browser open example.com
agent-browser snapshot -i --json     # Get interactive elements with refs
agent-browser click @e2              # Click by ref
agent-browser fill @e3 "text"        # Fill by ref
agent-browser screenshot page.png
agent-browser close
```

**Key commands**:
- Navigation: `open`, `back`, `forward`, `reload`
- Actions: `click`, `fill`, `type`, `hover`, `drag`, `upload`, `press`
- Inspection: `snapshot`, `screenshot`, `get text/html/value`, `is visible/enabled/checked`
- Finding: `find role/text/label/placeholder/testid <action>`
- Waiting: `wait <selector|ms>`, `wait --text/url/load/fn`
- State: `state save/load` for auth persistence

**Standout features**:
- **Snapshot with refs**: Accessibility tree outputs element references (@e1, @e2) for reliable selection
- **Session isolation**: `--session <name>` for parallel agents
- **Persistent profiles**: `--profile <path>` to persist cookies/logins across runs
- **JSON output**: `--json` flag for machine-readable responses
- **Viewport streaming**: WebSocket server for live preview (AGENT_BROWSER_STREAM_PORT)
- **CDP connection**: Connect to existing Chrome/Electron via `--cdp <port>`
- **Cloud providers**: Built-in support for Browserbase, Browser Use, Kernel
- **iOS Safari control**: Control real Safari in iOS Simulator via Appium (`-p ios`)

**Architecture**: Client-daemon model with Rust CLI (fast) + Node.js daemon (Playwright). Falls back to pure Node.js if native binary unavailable. Supports macOS ARM64/x64, Linux ARM64/x64, Windows x64.

**Snapshot filtering options**:
- `-i, --interactive`: Only buttons, inputs, links
- `-C, --cursor`: Include divs with onclick, cursor:pointer
- `-c, --compact`: Remove empty structural elements
- `-d, --depth <n>`: Limit tree depth
- `-s, --selector`: Scope to CSS selector

### Assessment

**Durability** (medium): Core CLI commands and concepts are stable, but this is an active Vercel Labs project—new providers, flags, and features may be added. The snapshot/ref workflow concept is durable.

**Content type**: reference / tutorial

**Density** (high): Extremely dense reference documentation covering 50+ commands, multiple installation methods, 4+ cloud providers, iOS integration, CDP connection, streaming protocol, and environment variables.

**Originality**: primary source (official repository README)

**Reference style**: refer-back / deep-study. This is comprehensive API documentation you'd return to for specific commands or when configuring cloud providers.

**Scrape quality** (good): Full README content captured including all command examples, tables, and configuration options. No code blocks appear truncated.
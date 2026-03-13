---
url: https://github.com/disler/claude-code-hooks-multi-agent-observability
title: 'GitHub - disler/claude-code-hooks-multi-agent-observability: Real-time monitoring for Claude Code agents through simple
  hook event tracking.'
scraped_at: '2026-02-11T10:08:37.235573+00:00'
word_count: 2586
raw_file: raw/2026-02-11_github-dislerclaude-code-hooks-multi-agent-observability-rea.txt
tldr: A real-time observability dashboard for Claude Code agents that captures, stores, and visualizes all 12 hook event types
  across multi-agent swarms via a Bun/SQLite server and Vue 3 client.
key_quote: The true constraint of agentic engineering is no longer what the models can do — it's our ability to prompt engineer
  and context engineer the outcomes we need, and build them into reusable systems.
durability: medium
content_type: mixed
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people:
- disler
tools:
- claude-code
- bun
- sqlite
- python
- uv
- just
- tmux
- websocket
libraries:
- vue
- vite
- tailwind
companies:
- anthropic
- openai
- elevenlabs
- firecrawl
tags:
- multi-agent-systems
- observability
- claude-code
- hook-events
- real-time-monitoring
---

### TL;DR
A real-time observability dashboard for Claude Code agents that captures, stores, and visualizes all 12 hook event types across multi-agent swarms via a Bun/SQLite server and Vue 3 client.

### Key Quote
> "The true constraint of agentic engineering is no longer what the models can do — it's our ability to prompt engineer and context engineer the outcomes we need, and build them into reusable systems."

### Summary

**What it does:**
- Provides real-time monitoring dashboard for Claude Code agent activity
- Tracks all 12 Claude Code hook events: PreToolUse, PostToolUse, PostToolUseFailure, PermissionRequest, Notification, Stop, SubagentStart, SubagentStop, PreCompact, UserPromptSubmit, SessionStart, SessionEnd
- Supports multi-agent orchestration visibility with session tracking and filtering
- Displays tool calls, task handoffs, and agent lifecycle events across parallel agent swarms

**Architecture:**
```
Claude Agents → Hook Scripts → HTTP POST → Bun Server → SQLite → WebSocket → Vue Client
```
- Server: Bun + TypeScript on port 4000, SQLite with WAL mode
- Client: Vue 3 + Vite + Tailwind on port 5173
- Hooks: Python 3.11+ with Astral uv package manager

**Installation & Setup:**
```bash
# Prerequisites: Claude Code CLI, Astral uv, Bun/npm/yarn, just (optional)
cp -R .claude /path/to/your/project/
./scripts/start-system.sh  # or: just start
# Open http://localhost:5173
```

**Configuration:**
- Copy `.claude` directory to project root
- Update `settings.json` with `source-app` identifier
- Set `ANTHROPIC_API_KEY` environment variable
- Optional keys: OpenAI, ElevenLabs (TTS), Firecrawl (web scraping)

**Standout Features:**
- **Live Pulse Chart**: Canvas-based real-time activity visualization with session-colored bars
- **Tool Emoji System**: Each tool has emoji (Bash: 💻, Read: 📖, Write: ✍️, etc.), MCP tools show 🔌 prefix
- **Dual-color system**: App colors + session colors for visual distinction
- **Multi-criteria filtering**: Filter by app, session, event type
- **Chat transcript viewer**: Syntax-highlighted conversation history
- **Agent Teams support**: Builder (engineering) and Validator (read-only) agent templates
- **Safety guards**: Blocks dangerous `rm -rf`, prevents sensitive file access, `stop_hook_active` prevents infinite loops

**Key Commands (via justfile):**
```bash
just start       # Start server + client
just stop        # Stop all processes
just health      # Check status
just test-event  # Send test event
just db-reset    # Reset database
```

### Assessment

**Durability** (medium): Tied to Claude Code's hook system architecture and current API. The hook event types are stable, but the multi-agent orchestration features reference experimental features (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`) that may evolve. Relevant as of Claude Opus 4.6 era.

**Content type**: Tool/library documentation with tutorial elements

**Density** (high): Dense with specific technical details—12 event types, file structure, configuration patterns, API endpoints, port numbers, environment variables. Little padding.

**Originality**: Primary source — this is the author's original open-source project

**Reference style**: Refer-back / deep-study — you'd return to this for setup instructions, hook configuration patterns, and the event type reference table when integrating or troubleshooting

**Scrape quality** (good): Full README content captured including code blocks, directory structure, tables, and configuration examples. No missing sections apparent.
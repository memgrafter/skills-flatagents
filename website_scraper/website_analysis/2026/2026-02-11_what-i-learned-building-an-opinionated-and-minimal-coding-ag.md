---
url: https://mariozechner.at/posts/2025-11-30-pi-coding-agent/
title: What I learned building an opinionated and minimal coding agent
scraped_at: '2026-02-11T10:25:29.169304+00:00'
word_count: 6678
raw_file: raw/2026-02-11_what-i-learned-building-an-opinionated-and-minimal-coding-ag.txt
tldr: Mario Zechner built "pi," a minimal coding agent harness, after becoming frustrated with Claude Code's complexity, hidden
  context injection, and poor observability—achieving competitive Terminal-Bench 2.0 results with a sub-1000-token system
  prompt and just four tools.
key_quote: I'm a simple boy who likes simple, predictable tools. Over the past few months, Claude Code has turned into a spaceship
  with 80% of functionality I have no use for.
durability: medium
content_type: mixed
density: high
originality: primary
reference_style: deep-study
scrape_quality: good
people:
- Mario Zechner
- Simon Willison
tools:
- pi
- claude-code
- codex
- cursor
- windsurf
- amp
- opencode
- tmux
- terminus-2
- ollama
- llama-cpp
- vllm
libraries:
- typebox
- ajv
- vercel-ai-sdk
companies:
- Anthropic
- OpenAI
- Google
- xAI
- Cerebras
- OpenRouter
- Mistral
tags:
- coding-agents
- llm-api-design
- context-engineering
- terminal-ui
- minimalism
---

### TL;DR
Mario Zechner built "pi," a minimal coding agent harness, after becoming frustrated with Claude Code's complexity, hidden context injection, and poor observability—achieving competitive Terminal-Bench 2.0 results with a sub-1000-token system prompt and just four tools.

### Key Quote
"I'm a simple boy who likes simple, predictable tools. Over the past few months, Claude Code has turned into a spaceship with 80% of functionality I have no use for."

### Summary

**Motivation & Philosophy**
- Author preferred Claude Code but grew frustrated with: changing system prompts per release, hidden context injection, flickering UI, lack of observability into sub-agents
- Core principle: "if I don't need it, it won't be built"
- Goals: full control over context, inspectability of all model interactions, cleanly documented session format

**Architecture (4 packages)**
- **pi-ai**: Unified LLM API supporting Anthropic, OpenAI, Google, xAI, Groq, Cerebras, OpenRouter, any OpenAI-compatible endpoint
- **pi-agent-core**: Agent loop with tool execution, validation, event streaming
- **pi-tui**: Terminal UI framework with differential rendering and synchronized output
- **pi-coding-agent**: CLI wiring it all together

**pi-ai Technical Insights**
- Only 4 APIs matter: OpenAI Completions, OpenAI Responses, Anthropic Messages, Google Generative AI
- Provider quirks require handling: `store` field rejections, `max_tokens` vs `max_completion_tokens`, `developer` role support, reasoning content field names
- Token/cost tracking is "Wild West"—providers report differently, no correlation IDs for billing
- Context handoff between providers works by converting thinking traces to `<thinking>` tagged text
- Supports aborts throughout pipeline, partial results on abort, progressive JSON parsing during tool streaming
- Novel feature: tools return separate content for LLM vs UI display

**pi-tui Approach**
- Uses "scrollback buffer" style (like Claude Code) vs full-screen TUI (like Amp/opencode)
- Retained mode UI with component caching
- Differential rendering: only redraw from first changed line
- Synchronized output escape sequences prevent flicker in capable terminals

**Opinionated Design Decisions**
- **Minimal system prompt + tools**: <1000 tokens total (4 tools: read, write, edit, bash)
- **YOLO mode default**: No permission prompts, full filesystem/command access; security measures in other agents called "security theater"
- **No to-dos**: Confuses models; use external TODO.md files instead
- **No plan mode**: Just tell agent to think; use PLAN.md for persistence
- **No MCP support**: MCP servers dump too many tokens into context; use CLI tools with READMEs instead (progressive disclosure)
- **No background bash**: Use tmux for dev servers, REPLs, debugging
- **No sub-agents**: Poor observability; spawn via bash if needed, but better to plan context gathering in separate sessions

**Benchmarks**
- Ran Terminal-Bench 2.0 with Claude Opus 4.5
- Ranked competitively against Codex, Cursor, Windsurf with their native models
- Note: Terminus 2 (minimal tmux-only agent) also performs well—evidence minimal approaches work

### Assessment

**Durability** (medium): Technical insights about LLM API quirks and context engineering principles are durable, but specific provider behaviors and benchmark results will age quickly as APIs evolve.

**Content type**: mixed (opinion + tutorial + technical deep-dive)

**Density** (high): Dense with specific technical details—API field names, token counts, code examples, architectural decisions, and concrete benchmark results.

**Originality**: primary source—detailed documentation of author's own project with original insights from building multiple agents.

**Reference style**: deep-study—worth reading fully to understand the philosophy and technical decisions; code examples and design rationales are valuable for anyone building similar tools.

**Scrape quality** (good): Full article content captured including code blocks, though some inline code formatting appears slightly mangled (e.g., `max_tokens` shows as separate lines). No images were essential to understanding.
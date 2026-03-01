---
url: https://blog.cloudflare.com/code-mode/
title: 'Code Mode: the better way to use MCP'
scraped_at: '2026-02-11T10:36:44.981465+00:00'
word_count: 2917
raw_file: raw/2026-02-11_code-mode-the-better-way-to-use-mcp.txt
tldr: Cloudflare discovered that LLMs perform better when writing TypeScript code to call MCP tools rather than invoking them
  directly through tool-calling tokens, and built a sandboxed execution environment using V8 isolates to enable this "Code
  Mode" approach.
key_quote: LLMs are better at writing code to call MCP, than at calling MCP directly.
durability: high
content_type: mixed
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people: []
tools:
- mcp
- v8-isolates
- wrangler
- workerd
- cloudflare-workers
- cloudflare-agents-sdk
libraries:
- ai-sdk
companies:
- Cloudflare
tags:
- mcp
- llm-agents
- code-generation
- sandboxing
- serverless
---

### TL;DR
Cloudflare discovered that LLMs perform better when writing TypeScript code to call MCP tools rather than invoking them directly through tool-calling tokens, and built a sandboxed execution environment using V8 isolates to enable this "Code Mode" approach.

### Key Quote
"LLMs are better at writing code to call MCP, than at calling MCP directly."

### Summary

**The Problem with Traditional MCP Tool Calling:**
- LLMs use special tokens for tool calls that don't exist in natural text—trained only on synthetic data
- LLMs struggle when presented with many tools or complex tools
- Sequential tool calls waste tokens and energy: each output must pass through the LLM's neural network just to become input for the next call
- MCP server designers must "dumb down" APIs compared to traditional developer APIs

**The Code Mode Solution:**
- Convert MCP tool schemas into TypeScript APIs with doc comments
- Present the LLM with a single "execute code" tool instead of all MCP tools directly
- LLM writes TypeScript that calls the generated API
- Code runs in a secure sandbox; only results return to the LLM
- Intermediate data stays in the sandbox, avoiding round-trips through the LLM

**Implementation Details:**
- `codemode` helper in Cloudflare Agents SDK wraps existing tool definitions
- Example usage transforms `streamText()` calls to use generated system prompt and tools
- Sandbox is a V8 isolate—no containers, starts in milliseconds, disposable per-execution
- No internet access; MCP servers accessed via bindings that handle auth out-of-band
- API keys never exposed to generated code

**Worker Loader API (new):**
- Enables on-demand loading of arbitrary Worker code
- Supports bindings from sandbox to parent Worker for MCP invocation
- Currently available in local development via Wrangler; production access in closed beta
- Pricing not finalized but expected to be cheaper than container-based solutions

**Security Model:**
- Bindings provide authorized interfaces without exposing credentials
- Network access (`fetch()`, `connect()`) disabled in sandbox
- All external access routed through parent Worker via RPC

### Assessment

**Durability (medium-high):** The core insight—that LLMs write code better than they make tool calls—is likely to remain relevant. The specific implementation details (Worker Loader API, SDK syntax) will evolve. MCP is a 2025-era protocol, so this is cutting-edge but tied to current ecosystem state.

**Content type:** mixed (announcement + technical explanation + tutorial)

**Density (high):** Dense with specifics—code examples, API signatures, architectural decisions, and concrete implementation details. Minimal marketing fluff.

**Originality:** primary source. This is Cloudflare announcing their own innovation with original technical details.

**Reference style:** skim-once + refer-back. The conceptual insight is the main takeaway; the code examples and Worker Loader API docs are worth returning to when implementing.

**Scrape quality (good):** Full article captured including code blocks. No images appear to be missing. Code examples are complete and readable.
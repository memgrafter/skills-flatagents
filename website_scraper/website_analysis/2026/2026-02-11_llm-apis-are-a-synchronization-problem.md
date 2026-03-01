---
url: https://lucumr.pocoo.org/2025/11/22/llm-apis/
title: LLM APIs are a Synchronization Problem
scraped_at: '2026-02-11T10:30:27.743060+00:00'
word_count: 1530
raw_file: 2026-02-11_llm-apis-are-a-synchronization-problem.txt
tldr: Current LLM APIs incorrectly abstract what's fundamentally a distributed state synchronization problem, with hidden
  server-side state (KV caches, reasoning tokens, tool definitions) that can't be properly reconciled through message-based
  interfaces.
key_quote: Maybe it's time to start thinking about what a state synchronization API would look like, rather than a message-based
  API.
durability: high
content_type: opinion
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people:
- Armin Ronacher
tools:
- Ollama
- OpenRouter
- Vercel AI SDK
libraries:
- MCP
companies:
- OpenAI
- Anthropic
tags:
- llm-apis
- distributed-systems
- state-synchronization
- api-design
- local-first
---

### TL;DR
Current LLM APIs incorrectly abstract what's fundamentally a distributed state synchronization problem, with hidden server-side state (KV caches, reasoning tokens, tool definitions) that can't be properly reconciled through message-based interfaces.

### Key Quote
"Maybe it's time to start thinking about what a state synchronization API would look like, rather than a message-based API."

### Summary
- **Core thesis**: LLM APIs should be understood as distributed state synchronization problems, not message-passing systems
- **How models actually work**: 
  - Models operate on tokens, not messages—no distinction between "user" and "assistant" text internally
  - Two kinds of state exist: visible token history and derived GPU state (KV cache, activations)
  - You can replay tokens to restore text, but not the exact derived working state
- **Problems with completion-style APIs**:
  - Request size grows linearly with turns; cumulative data sent grows quadratically
  - Providers inject invisible tokens (prompt templates, role markers, tool definitions, search results, reasoning tokens)
  - Some hidden state is deliberately obscured (reasoning tokens, encrypted blobs for search results)
- **Problems with OpenAI's Responses API**:
  - Stores conversation history server-side but offers limited synchronization capabilities
  - Unclear recovery from state divergence, corruption, or network partitions
  - Cannot replay from scratch if remote state is wiped
- **Intermediaries add complexity**: OpenRouter, Vercel AI SDK try to unify providers but can't reconcile incompatible hidden-state management
- **Proposed direction**: Look to local-first software movement (CRDTs, peer-to-peer sync, conflict-free replicated storage) for better abstractions
  - KV caches resemble checkpointable derived state
  - Prompt history is an append-only log that could sync incrementally
  - Provider context behaves like replicated documents with hidden fields
- **Warning about MCP**: Rushing to standardize current message-based abstractions could lock in their weaknesses

### Assessment
**Durability**: High. This identifies fundamental architectural mismatches that won't be resolved soon—the critique targets the core abstraction model, not specific API versions. **Content type**: Opinion / Technical analysis. **Density**: High. Ronacher packs significant technical detail about GPU state, token handling, and API mechanics into a compact essay. **Originality**: Primary source with synthesis. This is Ronacher's original analysis drawing on his direct experience, with connections to the local-first software movement. **Reference style**: Deep-study / refer-back. Worth revisiting when designing LLM integrations or evaluating API standards. **Scrape quality**: Good. Full article text captured with no apparent gaps.
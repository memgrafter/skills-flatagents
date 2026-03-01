---
url: https://mariozechner.at/posts/2025-11-22-armin-is-wrong/
title: Armin is wrong and here's why
scraped_at: '2026-02-11T10:28:52.951496+00:00'
word_count: 2185
raw_file: 2026-02-11_armin-is-wrong-and-heres-why.txt
tldr: Mario Zechner argues against Armin's claim that LLM APIs are a state synchronization problem, contending that the messages
  abstraction reflects the underlying reality and that opaque provider state is simply an API contract, not a local-first
  sync problem.
key_quote: Under a local-first lens, your only real option is to manage execution environments yourself and make their state
  part of your own canonical state.
durability: medium
content_type: opinion
density: high
originality: commentary
reference_style: skim-once
scrape_quality: good
people:
- Mario Zechner
- Armin
tools:
- LLM APIs
- Responses API
libraries: []
companies:
- OpenAI
tags:
- llm-apis
- local-first
- state-management
- api-design
- crdt
---

### TL;DR
Mario Zechner argues against Armin's claim that LLM APIs are a state synchronization problem, contending that the messages abstraction reflects the underlying reality and that opaque provider state is simply an API contract, not a local-first sync problem.

### Key Quote
"Under a local-first lens, your only real option is to manage execution environments yourself and make their state part of your own canonical state."

### Summary
A counter-argument to Armin's blog post about LLM APIs being state synchronization problems:

**On the messages abstraction:**
- Messages aren't hiding a simpler reality—they map directly to the prompt format baked into model weights (e.g., Harmony format uses `<|start|>system<|message|>` tokens)
- The JSON messages API is essentially a trivial transform over the actual token sequences models expect

**On the supposed state sync problem:**
- Opaque thinking blobs, server-side tool results, and cache markers are like HTTP-only cookies—you store them client-side and echo them back
- This is an API contract, not shared mutable state requiring CRDT-style synchronization
- The server remains effectively stateless from the client's perspective; all observable state is fully replayable

**On switching providers:**
- Yes, provider-specific opaque data means data loss when switching mid-session
- But this is an interoperability problem, not a sync problem—local-first/CRDT solutions won't help
- Providers will never interoperate on hidden state (KV caches, thinking traces)

**Real problems identified:**
- Quadratic growth of resending full history each turn (mitigated by file upload APIs)
- OpenAI's Responses API has poor documentation and edge case handling
- Provider-managed VMs/containers where LLMs build state are "the biggest possible state fuckery"—catastrophic to lose, impossible to export

**Where local-first still applies:**
- Only on your side of the wire
- Treat thinking traces as transient scratchpad state, not essential document state
- Store your own canonical state (messages, tool results, file references)
- Manage execution environments yourself rather than relying on provider containers
- Everything that matters for correctness/recovery must live with you, not the provider

### Assessment
**Durability**: Medium-high. The core argument about API contracts vs. sync problems is conceptual and will remain relevant. Specific references to OpenAI's Responses API and current provider behaviors may age.

**Content type**: Opinion / commentary (response to another blog post)

**Density**: High. Dense with specific technical claims, API examples, and nuanced argumentation. Requires understanding of LLM APIs, local-first concepts, and CRDTs.

**Originality**: Commentary. Direct response to Armin's blog post, engaging point-by-point with specific claims.

**Reference style**: Skim-once. This is an opinion piece arguing a specific position; useful for the perspective but not a reference document.

**Scrape quality**: Good. Full text captured including the Harmony format example with special tokens, though the original Armin post being critiqued is not included (author assumes you've read it first).
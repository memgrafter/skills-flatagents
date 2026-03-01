---
url: https://docs.sillytavern.app/usage/core-concepts/worldinfo/
title: World Info | docs.ST.app
scraped_at: '2026-02-11T09:55:47.158119+00:00'
word_count: 4424
raw_file: 2026-02-11_world-info-docsstapp.txt
tldr: Comprehensive reference documentation for SillyTavern's World Info system—a keyword-triggered dynamic prompt injection
  mechanism that inserts lore, instructions, or context into AI chats when specified terms appear in messages.
key_quote: It functions like a dynamic dictionary that only inserts relevant information from World Info entries when keywords
  associated with the entries are present in the message text.
durability: high
content_type: reference
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people:
- kingbri
- Alicat
- Trappu
tools:
- sillytavern
- stscript
- quick-replies
- vector-storage
libraries: []
companies: []
tags:
- world-info
- lorebooks
- prompt-engineering
- ai-chat
- dynamic-context
---

### TL;DR
Comprehensive reference documentation for SillyTavern's World Info system—a keyword-triggered dynamic prompt injection mechanism that inserts lore, instructions, or context into AI chats when specified terms appear in messages.

### Key Quote
"It functions like a dynamic dictionary that only inserts relevant information from World Info entries when keywords associated with the entries are present in the message text."

### Summary

**Core Concept**
- World Info (WI/Lorebooks/Memory Books) inserts prompts dynamically based on keyword detection in chat messages
- Entries activate when keywords match, injecting content into context to guide AI responses
- Does not guarantee AI will use the information—depends on model capability

**Entry Structure**
- **Keys**: Comma-separated keywords (case-insensitive by default) that trigger activation
- **Regex Keys**: JavaScript-style regex supported with `/pattern/flags` syntax; can match specific speakers using `\x01{{user}}:` prefix
- **Content**: Text inserted into prompt upon activation—should be standalone/comprehensive
- **Insertion Order**: Numeric priority; higher numbers appear later in context (more influence)
- **Insertion Position**: Before/After Char Defs, Before/After Example Messages, Top/Bottom of Author's Note, @ Depth D, or Outlet (manual placement)
- **Strategy**: Constant (🔵 always), Triggered (🟢 keyword-based), Vectorized (🔗 similarity-based)

**Advanced Entry Features**
- **Optional Filters**: AND ANY, AND ALL, NOT ANY, NOT ALL logic for secondary keyword requirements
- **Probability (Trigger %)**: Chance-based activation for random events
- **Inclusion Groups**: When multiple entries in same group trigger, only one inserts (weighted random or priority-based)
- **Outlets**: Named insertion points called via `{{outlet::Name}}` macro for precise prompt placement
- **Timed Effects**: Sticky (stays active N messages), Cooldown (blocked N messages), Delay (requires N messages before activatable)
- **Automation ID**: Links to STscript Quick Replies for command execution on activation
- **Character Filter**: Whitelist/blacklist specific characters for entry activation
- **Additional Matching Sources**: Can match against Character Description, Personality, Scenario, Persona Description, Notes

**Character Lore Binding**
- Primary WI file can be bound to character (embedded in card on export)
- Multiple WI files can be linked via shift-click or "More..." menu
- Insertion strategies: Sorted Evenly (default), Character Lore First, Global Lore First

**Global Activation Settings**
- **Scan Depth**: How many messages back to check for keywords (0 = only recursed/A-N)
- **Include Names**: Whether to prefix scanned text with `Name:` for matching
- **Context % / Budget**: Token limits for WI content
- **Min Activations**: Forces backward scanning until N entries triggered
- **Max Recursion Steps**: Limits recursion nesting depth
- **Case-sensitive keys / Match whole words**: Matching behavior toggles
- **Recursive Scanning**: Entries can trigger other entries via keyword mentions in content; supports "Delay until recursion" with levels

**Vector Storage Matching**
- Semantic similarity matching as alternative to keywords
- Requires Vector Storage extension with embeddings configured
- Entries marked 🔗 or global "Enabled for all" setting
- Uses "Query messages" setting instead of Scan Depth

### Assessment

**Durability**: Medium-high. Core concepts (keyword-triggered insertion, recursion, budgeting) are stable architectural patterns. Specific UI elements and newer features (Vector Storage, Timed Effects) may evolve. Version referenced: v1.12.6+ for message separator behavior.

**Content type**: Reference / tutorial (mixed)

**Density**: High. This is exhaustive documentation covering every field, toggle, and edge case. Dense with specific syntax examples, regex patterns, macro formats, and interaction rules.

**Originality**: Primary source—official SillyTavern documentation.

**Reference style**: Refer-back / deep-study. This is a working reference users return to when configuring entries, debugging activation issues, or learning advanced features. The Timed Effects example and recursion explanation benefit from careful reading.

**Scrape quality**: Good. All sections captured including tables, code examples, and nested lists. No images appear to be missing (mostly text-based UI descriptions). The "Further reading" link to the Encyclopedia is noted but not scraped (external).
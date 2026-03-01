---
url: https://docs.chub.ai/docs/advanced-setups/lorebooks
title: Lorebooks | Chub AI Guide
scraped_at: '2026-02-11T09:57:13.811530+00:00'
word_count: 855
raw_file: 2026-02-11_lorebooks-chub-ai-guide.txt
tldr: Lorebooks are keyword-triggered content injection systems for AI roleplay chats that dynamically insert character/setting
  information into prompts only when relevant, conserving token space.
key_quote: A lorebook is a series of defined keywords that, when activated, insert specific content into the prompt. They
  can be used to serve content to the AI about the character's backstory, setting, environment, etc without needing to have
  it be in character definitions taking up permanent token space.
durability: medium
content_type: mixed
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people: []
tools:
- Chub AI
- Lorebook Creator
- Character Creator
libraries: []
companies:
- Chub AI
tags:
- lorebooks
- ai-roleplay
- prompt-engineering
- character-books
- token-management
---

### TL;DR
Lorebooks are keyword-triggered content injection systems for AI roleplay chats that dynamically insert character/setting information into prompts only when relevant, conserving token space.

### Key Quote
"A lorebook is a series of defined keywords that, when activated, insert specific content into the prompt. They can be used to serve content to the AI about the character's backstory, setting, environment, etc without needing to have it be in character definitions taking up permanent token space."

### Summary
**What Lorebooks Do**
- Monitor chat messages for defined keywords
- Insert associated content into the prompt when keywords are detected
- Characterbooks = lorebooks attached to specific characters

**Core Settings (in Chat Settings)**
- **Scan Depth**: Number of recent messages scanned for keyword matches (starts from end of history)
- **Token Budget**: Max tokens allocated to lorebook content; subsequent matches ignored once exceeded
- Default matching: case-insensitive, whole-word only ("Apple" matches "apple" but not "Applebottom")

**Entry Properties**
- **Keywords**: Primary triggers for content insertion
- **Secondary Keywords**: Additional required triggers (configurable logic)
- **Content**: Actual information sent to AI
- **Insertion Order**: Lower number = inserted higher = less AI attention
- **Priority**: Determines which entries get cut first when budget exceeded
- **Selective Logic**: AND/NOT operations for keyword combinations
- **Constant**: Always insert regardless of keyword presence
- **Probability**: % chance of insertion when triggered
- **Recursive Scanning**: Entries can activate other entries

**How to Use**
1. Enable "Use V2 Spec" (for characterbooks)
2. Copy lorebook path from repository (kebab menu → Copy Path)
3. Paste path in Chat Settings and confirm

### Assessment
**Durability**: Medium. Core concepts are stable, but specific UI paths and settings locations may change as Chub AI evolves. The V2 Spec mention suggests versioning exists.

**Content type**: Reference / Tutorial (mixed)

**Density**: High. Compact documentation with specific field explanations, no fluff.

**Originality**: Primary source. Official documentation from Chub AI.

**Reference style**: Refer-back. Users will return to check specific field meanings or import steps.

**Scrape quality**: Good. All sections captured including settings, entry properties, and usage steps. No missing code blocks or images apparent.
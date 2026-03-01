---
url: https://docs.sillytavern.app/usage/core-concepts/chatfilemanagement/
title: Chat File Management | docs.ST.app
scraped_at: '2026-02-11T10:07:23.221556+00:00'
word_count: 456
raw_file: raw/2026-02-11_chat-file-management-docsstapp.txt
tldr: SillyTavern documentation explaining how to manage chat files, including solo vs group chats, import/export options,
  and the checkpoint/branch system for forking conversations.
key_quote: Checkpoints are clones of the current chat, in that they copy all messages from the given chat up to a certain
  point, and they store a link to the source (by chat file name).
durability: medium
content_type: reference
density: medium
originality: primary
reference_style: refer-back
scrape_quality: good
people: []
tools:
- SillyTavern
- CAI Tools
- TavernAI
- Text Generation WebUI
- Agnai
- KoboldAI Lite
- RisuAI
libraries: []
companies:
- Character.AI
tags:
- chat-management
- sillytavern
- import-export
- checkpoints
- branching
---

### TL;DR
SillyTavern documentation explaining how to manage chat files, including solo vs group chats, import/export options, and the checkpoint/branch system for forking conversations.

### Key Quote
"Checkpoints are clones of the current chat, in that they copy all messages from the given chat up to a certain point, and they store a link to the source (by chat file name)."

### Summary
**Chat Types**
- **Solo chats**: Click a character card and start chatting
- **Group chats**: "Create New Chat Group" button adds multiple characters who interact with each other and you

**Import Sources**
Supported platforms for importing existing chats:
- Character.AI (via CAI Tools browser extension)
- TavernAI (original)
- Text Generation WebUI (oobabooga)
- Agnai
- KoboldAI Lite
- RisuAI

**Export Options**
- **.jsonl**: Full metadata export, re-importable, shareable. Privacy warning: inspect and scrub sensitive data before sharing
- **.txt**: Plain text only, cannot be re-imported, loses metadata

**Checkpoints & Branches**
Both create clones of chat up to a specific message:
- **Create Branch**: Clones and switches to the new branch immediately
- **Create Checkpoint**: Clones, prompts for name, stays in current chat
- Analogy: like "open in new tab" vs "open in new tab (background)"
- Return to parent via burger menu → "Back to parent chat"

**Rename Chat**
- Default naming: date/time stamp
- Click pencil icon to rename
- Warning: renaming breaks checkpoint links (linked by filename)

### Assessment
**Durability**: Medium. Core concepts (import/export, branching) are stable, but specific import sources and extension links may change. **Content type**: Reference documentation. **Density**: Medium. Clear explanations with practical details, not overly verbose. **Originality**: Primary source (official docs). **Reference style**: Refer-back. Users will return when they need to perform specific operations like importing, exporting, or branching. **Scrape quality**: Good. Full content captured with clear section headings and formatting preserved.
---
url: https://www.reddit.com/r/AI_Agents/comments/1glzob6/tutorial_on_building_agent_with_memory_using_letta/
title: Tutorial on building agent with memory using Letta
scraped_at: '2026-01-30T20:35:18.475935+00:00'
word_count: 154
raw_file: 2026-01-30_tutorial-on-building-agent-with-memory-using-letta.txt
tldr: Creators of Letta released a free short course with Andrew Ng covering MemGPT research and the Letta open-source framework,
  which distinguishes itself by persisting all agent state (messages, tools, memory) in a database for "agents-as-a-service."
key_quote: Unlike other frameworks, Letta is very focused on persistence and having 'agents-as-a-service'. This means that
  all state (including messages, tools, memory, etc.) is all persisted in a DB.
durability: medium
content_type: mixed
density: medium
originality: primary
reference_style: skim-once
scrape_quality: good
people:
- Andrew Ng
tools:
- Letta
- Agent Development Environment
- LangChain
- CrewAI
libraries:
- MemGPT
companies: []
tags:
- ai-agents
- memory-management
- persistence
- database
- tutoials
---

### TL;DR
Creators of Letta released a free short course with Andrew Ng covering MemGPT research and the Letta open-source framework, which distinguishes itself by persisting all agent state (messages, tools, memory) in a database for "agents-as-a-service."

### Key Quote
"Unlike other frameworks, Letta is very focused on persistence and having 'agents-as-a-service'. This means that all state (including messages, tools, memory, etc.) is all persisted in a DB."

### Summary
- **Announcement**: A free short course has been released in collaboration with Andrew Ng, taught by the creators of Letta.
- **Topics Covered**: The course covers memory management research (specifically MemGPT) and provides an introduction to using the Letta open-source agents framework.
- **Core Differentiator**: Unlike frameworks like LangChain or CrewAI, Letta prioritizes **persistence** (agents-as-a-service).
- **Technical Details**:
  - All agent state—including messages, tools, and memory—is persisted in a database.
  - Agent state is automatically saved across sessions and persists even if the server is restarted.
- **Tooling**: Includes an Agent Development Environment (ADE) for visualizing and iterating on agent designs.

### Assessment
**Durability** is medium; while the specific course link and framework syntax may change, the architectural distinction of database-backed stateful agents is a relevant technical differentiator for the near future. This is a **mixed content type** (announcement/promotional with technical overview). **Density** is medium, as the short text efficiently conveys specific architectural advantages. **Originality** is a primary source, written directly by the framework's creators. **Reference style** is skim-once; it serves primarily to alert the reader to the resource existence and the framework's unique value prop. **Scrape quality** is good; the full text of the Reddit post is captured.
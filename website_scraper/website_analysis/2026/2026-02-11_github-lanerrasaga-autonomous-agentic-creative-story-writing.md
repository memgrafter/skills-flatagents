---
url: https://github.com/Lanerra/saga
title: 'GitHub - Lanerra/saga: Autonomous, agentic, creative story writing system that incorporates stored embeddings and
  Knowledge Graphs.'
scraped_at: '2026-02-11T09:50:42.052528+00:00'
word_count: 854
raw_file: 2026-02-11_github-lanerrasaga-autonomous-agentic-creative-story-writing.txt
tldr: SAGA is a local-first Python CLI that generates long-form fiction using LangGraph orchestration and Neo4j knowledge
  graphs to maintain narrative consistency across chapters.
key_quote: SAGA's goal is to help you generate a novel while staying consistent with established story facts.
durability: medium
content_type: reference
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people: []
tools:
- neo4j
- docker
- python
libraries:
- langgraph
- pydantic
companies:
- openai
tags:
- knowledge-graph
- llm-applications
- creative-writing
- fiction-generation
- local-first
---

### TL;DR
SAGA is a local-first Python CLI that generates long-form fiction using LangGraph orchestration and Neo4j knowledge graphs to maintain narrative consistency across chapters.

### Key Quote
"SAGA's goal is to help you generate a novel while staying consistent with established story facts."

### Summary

**What it does**: Generates novels chapter-by-chapter while tracking characters, locations, relationships, and events in a Neo4j knowledge graph to prevent continuity errors.

**Tech stack**:
- LangGraph for checkpointed, resumable workflow orchestration
- Neo4j for persistent knowledge graph storage
- Local filesystem for human-readable YAML/Markdown artifacts
- OpenAI-compatible LLM endpoint (designed for local models)
- Separate embeddings endpoint

**Philosophy**: Single-machine, no web app, no microservices. Canon lives in Neo4j; artifacts live in files for easy inspection and version control.

**Prerequisites**:
- Python 3.12
- Running Neo4j instance (Docker provided via `docker-compose.yml`)
- Local OpenAI-compatible LLM endpoint
- Local embeddings endpoint

**Setup**:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env to match local services
docker-compose up -d
```

**Two-phase workflow**:
1. **Bootstrap** (once per project): Generates character sheets, global outline with 3/5-act structure, detailed chapter beats, commits to Neo4j
2. **Per-chapter cycle**: Plan scenes → Generate prose per scene with KG context → Extract entities/relationships → Generate embeddings → Commit to graph → Validate (consistency, quality, contradictions) → Revise if needed → Finalize with summary

**Key features**:
- Scene-level generation with context retrieval from knowledge graph
- Content externalization (`ContentRef`) to keep checkpoints lightweight
- Graph healing: auto-merge duplicates, enrich provisional nodes
- LLM-based quality evaluation (coherence, prose, pacing, tone)
- Contradiction detection for relationships and timeline
- Bootstrap command: `python main.py bootstrap "A western about a robot sheriff"`

**Output structure** (`projects/{story_title}/`):
- `chapters/` — Finalized markdown chapters
- `summaries/` — Per-chapter summaries
- `outline/` — structure.yaml, beats.yaml
- `characters/`, `world/` — YAML profiles
- `exports/` — Compiled manuscript
- `.saga/` — checkpoints.db, logs, externalized content

**Critical config**: Embedding dimensions must match across `EXPECTED_EMBEDDING_DIM`, `NEO4J_VECTOR_DIMENSIONS`, and your embedding model (defaults assume 1024-dim, `.env.example` uses 768).

**Status**: Has known critical issues, not production-ready.

### Assessment
**Durability**: Medium. Core architecture concepts are solid, but dependency on specific versions (Python 3.12, LangGraph, Neo4j) and the explicit "not production-ready" warning mean this will require maintenance to stay functional. The approach of combining knowledge graphs with LLM generation is a pattern that will likely persist.

**Content type**: Reference / documentation

**Density**: High. Packed with specific commands, file paths, configuration variables, and workflow details. Minimal padding.

**Originality**: Primary source. This is the project's own README from the author.

**Reference style**: Refer-back for setup commands and configuration, deep-study for understanding the workflow architecture. The detailed file structure and environment variable documentation make it practical for actual implementation.

**Scrape quality**: Good. Code blocks, commands, file structures, and configuration details all captured. Links to additional docs (langgraph-architecture.md, WORKFLOW_WALKTHROUGH.md) are referenced but not included—which is expected for a README.
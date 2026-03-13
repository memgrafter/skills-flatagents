---
url: https://github.com/memgrafter/flatagents/tree/main
title: 'GitHub - memgrafter/flatagents: Flat, declarative agents and state machines for orchestrating LLMs.'
scraped_at: '2026-02-11T10:45:34.666913+00:00'
word_count: 1193
raw_file: raw/2026-02-11_github-memgrafterflatagents-flat-declarative-agents-and-stat_1.txt
tldr: A Python library for defining LLM agents and state machines declaratively in YAML, with built-in support for retries,
  parallel execution, distributed workers, and checkpointing.
key_quote: Define LLM agents in YAML. Run them anywhere.
durability: medium
content_type: mixed
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people: []
tools:
- flatagents
- LiteLLM
- AISuite
libraries:
- flatagents
- Jinja2
companies: []
tags:
- llm-agents
- state-machines
- yaml-configuration
- python-library
- llm-orchestration
---

### TL;DR
A Python library for defining LLM agents and state machines declaratively in YAML, with built-in support for retries, parallel execution, distributed workers, and checkpointing.

### Key Quote
"Define LLM agents in YAML. Run them anywhere."

### Summary
**Core Concepts:**
- **FlatAgent** — Single LLM call: model + prompts + output schema
- **FlatMachine** — State machine orchestrating multiple agents, actions, and nested machines

**Installation:**
```bash
pip install flatagents[all]
```

**Basic Usage:**
```python
from flatagents import FlatAgent, FlatMachine

agent = FlatAgent(config_file="reviewer.yml")
result = await agent.call(query="Review this code...")

machine = FlatMachine(config_file="workflow.yml")
result = await machine.execute(input={"query": "..."})
```

**Agent Config Structure (YAML):**
- `spec`/`spec_version` — Format identifier and version
- `data.name` — Agent identifier
- `data.model` — Profile name, inline config, or profile with overrides
- `data.system` — System prompt
- `data.user` — User prompt template (Jinja2, `{{ input.* }}`)
- `data.output` — Structured output schema

**Model Profiles:**
Centralized in `profiles.yml` with resolution order: default → named profile → inline overrides → override profile. Supports providers via LiteLLM (default) and AISuite backends.

**Execution Modes:**
| Type | Use Case |
|------|----------|
| `default` | Single call |
| `retry` | Rate limit handling with backoff |
| `parallel` | Multiple samples (`n_samples`) |
| `mdap_voting` | Consensus voting |

**Key Features:**
- Checkpoint/restore for machines
- Hook system (`MachineHooks`) for extensibility — `on_machine_start`, `on_state_enter`, `on_action`, `on_error`, etc.
- Distributed worker orchestration with SQLite backends
- OpenTelemetry metrics support
- Jinja2 templating in prompts
- Config validation utilities

**Examples Included:**
helloworld, writer_critic, story_writer, human-in-the-loop, error_handling, dynamic_agent, character_card, mdap, gepa_self_optimizer, research_paper_analysis, multi_paper_synthesizer, support_triage_json, distributed_worker, parallelism

**In Progress / Planned:**
- TypeScript SDK
- Distributed execution backends (Redis/Postgres)
- SQL persistence backend
- Webhook hooks for remote state machine handling

**Environment Variables:**
- `FLATAGENTS_LOG_LEVEL` — DEBUG/INFO/WARNING/ERROR
- `FLATAGENTS_METRICS_ENABLED` — true/false
- `OTEL_METRICS_EXPORTER` — console or otlp

### Assessment
**Durability (medium):** Core concepts (YAML-defined agents, state machines) are durable patterns, but specific API signatures and features may evolve. Version 1.1.1 indicates active development.

**Content type:** reference / tutorial (mixed)

**Density (high):** Information-rich README with concrete code examples, config schemas, and feature tables. Minimal fluff.

**Originality:** primary source — this is the canonical documentation for the library.

**Reference style:** refer-back / deep-study — would return for config syntax, hook interfaces, and execution mode options.

**Scrape quality (good):** Full content captured including code blocks, tables, and config examples. No missing sections apparent.
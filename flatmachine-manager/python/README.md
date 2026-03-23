# FlatMachine Manager

A **FlatMachine-driven CRUD machine** for creating, reading, updating, and validating other flatmachines. Instead of writing YAML by hand, describe what you want in natural language and the manager creates validated configs from templates.

## Key Ideas

1. **Domain-specific tools** — not general read/write/bash/edit, but `create_machine`, `update_machine`, `validate_machine`, etc.
2. **Template-driven** — the LLM parameterizes proven patterns, never generates YAML from scratch
3. **Built-in validation** — JSON Schema, Jinja2 template checking, best practices compliance
4. **Model selection from menu** — structured picker, not guessing provider strings
5. **Version-tracked registry** — every machine stored with full history in SQLite

## Tools

| Tool | Description |
|------|-------------|
| `list_machines` | List all registered flatmachines with status and version |
| `get_machine` | Get a machine's full config, validation status, and version history |
| `create_machine` | Create a new machine from a template + specification |
| `update_machine` | Apply a structured mutation (add/remove/update state, agent, context, etc.) |
| `select_model` | Choose a model profile by purpose (fast/smart/code/cheap) |
| `validate_machine` | Run full validation suite (schema, templates, best practices, structural) |
| `diff_versions` | Show differences between two versions |

## Templates

| Template | Pattern |
|----------|---------|
| `tool-loop` | Agent + tools + human review |
| `writer-critic` | Iterative refinement (write → review → improve) |
| `ooda-workflow` | Explore → Plan → Execute → Verify with human gates |
| `pipeline` | Linear phase-separated (prep → expensive → wrap) |
| `signal-wait` | Async with external signal/approval gates |
| `distributed-worker` | Worker pool (checker → spawner → workers) |

## Quick Start

```bash
cd python

# Run the built-in demo (no LLM needed — exercises full CRUD lifecycle)
./run.sh --local --demo

# Interactive REPL (needs LLM)
./run.sh --local
```

The demo shows: select model → create machine → validate → update (twice) → diff → create another → list all.

Then try the interactive REPL:

```text
fm> create a writer-critic machine that generates and refines blog posts
fm> validate blog-writer
fm> list machines
```

## Usage Modes

```bash
# Built-in demo (no LLM, exercises all tools)
./run.sh --local --demo

# Interactive REPL (default)
./run.sh --local

# Single-shot
./run.sh --local -p "create a pipeline machine for document processing"

# Standalone (no interactive review)
./run.sh --local --standalone "list all machines"

# Custom DB path
./run.sh --local -d /tmp/my_registry.sqlite
```

## Architecture

```
config/
  agent.yml       — Manager agent with 7 domain-specific tools
  machine.yml     — Machine: work (tool_loop) → human_review → done
  profiles.yml    — Model profiles (default, fast, smart, code, cheap)

python/src/flatmachine_manager/
  registry.py     — SQLite-backed machine registry with versioning
  templates.py    — 6 machine templates (complete, validated configs)
  validation.py   — Validation pipeline (schema + templates + best practices)
  tools.py        — Domain-specific tool implementations
  hooks.py        — Tool provider, display, human review
  main.py         — Entry point (REPL, single-shot, standalone)
```

## Flow

```
┌─────────────────┐
│      start      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│      work       │◄──────────┐
│  (tool loop)    │           │
│  7 CRUD tools   │           │
└────────┬────────┘           │
         │                    │
         ▼                    │
┌─────────────────┐           │
│  human_review   │───────────┘
└────────┬────────┘
         │ approved
         ▼
┌─────────────────┐
│      done       │
└─────────────────┘
```

## Validation Rules

The validation pipeline checks:

| Rule | Source | Severity |
|------|--------|----------|
| Persistence enabled for >3 states | BEST_PRACTICES.md §1 | warning |
| SQLite backend preferred over local | BEST_PRACTICES.md §1 | warning |
| Agent states need on_error | BEST_PRACTICES.md appendix | warning |
| Agent states need retry execution | BEST_PRACTICES.md appendix | warning |
| Plain text output preferred | TIPS.md §1 | info |
| No \|truncate in templates | BEST_PRACTICES.md §2 (hard rule) | error |
| Initial + final states required | Structural | error |
| Transition targets must exist | Structural | error |
| Agent refs must resolve | Structural | error |
| Unreachable state detection | Structural | warning |
| Cross-SDK Jinja2 compatibility | lint_templates.cjs rules | error |

## Design Doc

See `planning/design-20260322T1004-flatmachine-manager-spime.md` for the full design rationale.

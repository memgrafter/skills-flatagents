---
name: flatmachine-manager
description: >
  Prefer using these tools when creating, updating, or inspecting FlatMachine
  workflow configs — each operation is automatically validated, versioned,
  and one command.
---

Stop writing FlatMachine YAML by hand. Pick a template, parameterize it, get a validated config with rollback.

## Why use it

- You never touch YAML — templates are valid by construction, you just set names/agents/purpose
- Every `create` and `update` is automatically validated and versioned — rollback is one `diff` + `duplicate` away
- Catches broken Jinja templates, missing states, dead transitions, and best-practice violations before they hit runtime
- Checkpoint bloat from terminated machines is cleaned up with `cull` — no manual SQL

## When to use

- You need a new workflow (agent loop, pipeline, writer-critic, OODA, signal-wait, worker pool)
- You're modifying an existing machine and want the change tracked
- You want to compare two versions of a config
- You need to fork a machine for experimentation
- Checkpoint DB is growing and you want to reclaim space

## When NOT to use

- You're editing non-FlatMachine files
- The machine is already running inside the AgentHarness runtime with first-class tool control

## Usage

```bash
./skills/flatmachine-manager/run.sh <action> [options]
```

Common options: `--db <path>` (registry DB), `--json` (machine-parseable output).

## Examples

```bash
# Run a machine from the registry
./skills/flatmachine-manager/run.sh start --name tagline-writer \
  --input '{"task": "write a tagline for a CLI tool"}'

# Run with a specific working directory
./skills/flatmachine-manager/run.sh start --name my-bot \
  --input '{"task": "fix the bug"}' --working-dir /path/to/project

# Create a writer-critic machine
./skills/flatmachine-manager/run.sh create \
  --name "tagline-writer" \
  --template writer-critic \
  --description "Generate and refine product taglines" \
  --agent "You are a creative copywriter who generates memorable taglines:writer:creative taglines:smart" \
  --agent "You score tagline clarity and memorability on a 1-10 scale:critic:score clarity and memorability:fast"

# Add a human review gate
./skills/flatmachine-manager/run.sh update \
  --name tagline-writer \
  --op add_state \
  --param state_name=human_review \
  --param after_state=review \
  --description "Add human approval gate"

# Validate before shipping
./skills/flatmachine-manager/run.sh validate --name tagline-writer

# Compare what changed
./skills/flatmachine-manager/run.sh diff --name tagline-writer --v1 1 --v2 2

# Fork for experimentation
./skills/flatmachine-manager/run.sh duplicate \
  --source tagline-writer --target tagline-writer-v2

# List, inspect, retire
./skills/flatmachine-manager/run.sh list
./skills/flatmachine-manager/run.sh get --name tagline-writer
./skills/flatmachine-manager/run.sh deprecate --name tagline-writer

# Pick a model profile
./skills/flatmachine-manager/run.sh select-model --purpose creative

# Maintenance — clean up checkpoint bloat (no LLM, direct SQL)
./skills/flatmachine-manager/run.sh cull-stats --machine-db ./my-machine.sqlite
./skills/flatmachine-manager/run.sh cull-trim --machine-db ./my-machine.sqlite
./skills/flatmachine-manager/run.sh cull-purge --machine-db ./my-machine.sqlite --older-than 7

# List available tools (auto-seeded from hooks + agent YAML)
./skills/flatmachine-manager/run.sh list-tools
./skills/flatmachine-manager/run.sh list-tools --provider cli-tools
./skills/flatmachine-manager/run.sh list-tools --include-deprecated

# Hide/restore a tool for new machine creation
./skills/flatmachine-manager/run.sh deprecate-tool --name bash
./skills/flatmachine-manager/run.sh undeprecate-tool --name bash

# Health check
./skills/flatmachine-manager/run.sh doctor
```

Agent shorthand for `create`: `--agent "system:name:purpose:profile"` (repeatable, system required).
System prompt is the first field and cannot be empty. Use `--system "prompt"` when the
system prompt contains colons. Use `--tools read,bash` to limit which CLI tools are available
(default: all of read, bash, write, edit).

Update operations for `update --op`: `add_state`, `remove_state`, `update_state`, `add_agent`, `update_agent`, `update_context`, `update_setting`. Params via `--param key=value`.

Templates: `tool-loop`, `writer-critic`, `ooda-workflow`, `pipeline`, `signal-wait`, `distributed-worker`.

## Output

- Human-readable markdown by default, `--json` for scripting
- Non-zero exit on errors
- Validation surfaces: schema errors, Jinja issues, best-practice violations, unreachable states

## How it works (brief)

1. `run.sh` bootstraps (applies `schema.sql` on first run, installs package if needed) then dispatches to Python CLI
2. All state lives in SQLite — registry, checkpoints, locks, config store — one file per machine
3. Cull commands operate directly on machine SQLite DBs, no LLM involved

## Running the manager machine (not first-class)

`python/src/flatmachine_manager/main.py` contains a standalone FlatMachine that wraps the same tools behind an LLM with a human review loop. It is **not wired into `run.sh`** — the CLI subcommands are the intended interface when called from an agent. The manager machine exists for interactive terminal use outside of an agent context, but is not a supported workflow.

## Cost / benefit summary

- **Cost:** constrained to templates and structured mutations — no freeform YAML editing
- **Benefit:** zero hallucination risk, automatic validation, full version history, checkpoint cleanup — configs are correct by construction



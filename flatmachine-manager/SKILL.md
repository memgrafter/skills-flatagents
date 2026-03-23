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

- You need to **run** a machine — this manages configs, not execution
- You're editing non-FlatMachine files
- The machine is already running inside the AgentHarness runtime with first-class tool control

## Usage

```bash
./skills/flatmachine-manager/run.sh <action> [options]
```

Common options: `--db <path>` (registry DB), `--json` (machine-parseable output).

## Examples

```bash
# Create a writer-critic machine
./skills/flatmachine-manager/run.sh create \
  --name "tagline-writer" \
  --template writer-critic \
  --description "Generate and refine product taglines" \
  --agent "writer:creative taglines:smart" \
  --agent "critic:score clarity and memorability:fast"

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

# Health check
./skills/flatmachine-manager/run.sh doctor
```

Agent shorthand for `create`: `--agent "name:purpose:profile"` (repeatable).

Update operations for `update --op`: `add_state`, `remove_state`, `update_state`, `add_agent`, `update_agent`, `update_context`, `update_setting`. Params via `--param key=value`.

Templates: `tool-loop`, `writer-critic`, `ooda-workflow`, `pipeline`, `signal-wait`, `distributed-worker`.

## Output

- Human-readable markdown by default, `--json` for scripting
- Non-zero exit on errors
- Validation surfaces: schema errors, Jinja issues, best-practice violations, unreachable states

## How it works (brief)

1. `run.sh` bootstraps (copies schema DB on first run, installs package if needed) then dispatches to Python CLI
2. All state lives in SQLite — registry, checkpoints, locks, config store — one file per machine
3. Cull commands operate directly on machine SQLite DBs, no LLM involved

## Cost / benefit summary

- **Cost:** constrained to templates and structured mutations — no freeform YAML editing
- **Benefit:** zero hallucination risk, automatic validation, full version history, checkpoint cleanup — configs are correct by construction

---

## Architecture: Runtime, Hooks & Deployment

### What's compiled vs what's config

| Layer | Config (YAML) | Compiled (Rust binary) | Runtime (HTTP/API) |
|-------|--------------|----------------------|-------------------|
| State machine structure | ✓ | | |
| Agent prompts | ✓ | | |
| Persistence settings | ✓ | | |
| Model profiles | ✓ | | |
| Hooks | | ✓ (or registered at startup) | |
| Tools | | ✓ (or registered at startup) | |
| Custom actions | | ✓ (or registered at startup) | |
| LLM inference | | | ✓ |

### Entrypoint model

The compiled binary IS the entrypoint. No `run.sh` needed for execution:

```
./tagline-writer run --input '{"task": "write a tagline"}'
./tagline-writer resume --execution-id abc123
./tagline-writer signal --id abc123 --channel approval/1 --data '{"approved":true}'
./tagline-writer status
```

The binary can also be a long-running service, a Lambda handler, or anything else — the SDK runtime is the stable core, the entrypoint shape wraps it.

### Hook registration: compiled vs runtime

**Tight binding** — hooks compiled into the binary:

```rust
let hooks = ManagerHooks::new(&registry);
let machine = FlatMachine::from_file("machine.yml")
    .hooks(hooks)
    .build()?;
```

Good for CLI tools and dedicated services. Rebuild for any hook change.

**Loose binding** — hooks registered at runtime startup:

```rust
let runtime = FlatMachineRuntime::new()
    .register_action("human_review", HttpAction::new("https://review-svc/api"))
    .register_action("score", WasmAction::load("scoring.wasm"))
    .register_action("get_pool_state", LambdaAction::new("arn:aws:lambda:..."))
    .register_tool("create_machine", create_machine_handler)
    .build();
```

Good for Lambda, multi-tenant, dynamic workloads. Update hooks without recompiling the SDK binary.

Hook registration methods can coexist:

| Method | When to use |
|--------|-------------|
| Compiled trait impl | CLI binary, max performance, known hooks |
| WASM modules | Sandboxed, portable, any source language, hot-swappable |
| HTTP callbacks | Hooks are services (Lambda, Cloud Run, any API) |
| Script bridge | Python/Lua/shell hooks via IPC, dev/prototyping |
| Config-declared | Hook behavior entirely in YAML (simple routing, templating) |

### Lambda deployment model

**The zip:**

```
lambda.zip/
└── bootstrap              # compiled Rust binary (stable SDK + handler)
```

Or with Lambda Layers to share the runtime:

```
Layer: flatmachines-runtime-v2.4.4/
└── bootstrap              # stable SDK, updated rarely

Function code:
├── machine.yml            # or fetched from S3
└── hooks/
    └── scoring.wasm       # or fetched from S3
```

**Config is external, not baked in:**

At cold start, the handler fetches machine config from S3/DynamoDB/registry. WASM hooks are downloaded to `/tmp`. HTTP hooks are just URLs in the config. The SDK binary is stable — you update it rarely.

```rust
// Lambda handler
async fn handler(event: LambdaEvent<MachineInput>) -> Result<MachineOutput> {
    let config = CONFIG.get_or_init(|| {
        s3_get("my-bucket", "machines/tagline-writer/machine.yml").await
    });
    let runtime = FlatMachineRuntime::new()
        .register_action("score", WasmAction::load("/tmp/scoring.wasm"))
        .register_action("notify", HttpAction::post(&config.notify_url))
        .build();
    runtime.execute(config, event.payload.input).await
}
```

**Updating a live Lambda without redeployment:**

| What changed | How to update | Downtime |
|---|---|---|
| Machine YAML config | Update in S3/registry. Next cold start picks it up. | None |
| WASM hook module | Update in S3. Next cold start downloads to `/tmp`. | None |
| HTTP hook URL | Update the config. | None |
| SDK runtime binary | Update Layer or zip via `update-function-code`. | ~seconds |

To force immediate pickup: bump a config version env var, which forces cold starts:

```bash
aws lambda update-function-configuration \
  --function-name my-machine \
  --environment "Variables={CONFIG_VERSION=v3}"
```

**The deployment flow:**

```
Skill registry (SQLite)
    ↓ export
S3 bucket (machine configs, WASM hooks)
    ↓ fetch at cold start
Lambda (stable SDK binary, loads config + hooks at runtime)
    ↓ HTTP hooks
External services (review API, notification service, etc.)
```

Future skill commands for this flow:

```bash
run.sh export --name tagline-writer --target s3://my-bucket/machines/tagline-writer/
run.sh deploy --name tagline-writer --lambda my-function --bucket my-bucket
```

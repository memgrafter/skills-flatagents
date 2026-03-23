# FlatMachine Manager — Plan

## Planned: template unification and custom tools

### Template unification

The 6 templates (`tool-loop`, `writer-critic`, `ooda-workflow`, `pipeline`, `signal-wait`, `distributed-worker`) each duplicate agent field extraction logic (`name`, `purpose`, `model_profile`, `system`). Refactor to a shared helper that extracts agent fields uniformly so adding a new field (like `tools`) doesn't require touching every template.

### Arbitrary tool definitions on create

Allow `create_machine` to accept custom tool definitions (JSON Schema function specs) that get passed through to the agent. Currently only `tool-loop` and `ooda-workflow` include CLI tools (read/bash/write/edit). A machine creator should be able to pass any set of tool schemas — either hand-written or generated — and have them included in the agent config.

### Tool generation extension

A planned extension will generate tool definitions (JSON Schema function specs + Python implementations) that can be registered in the hooks registry and included in machine configs. Generated tools would be available to any machine created through the skill.

### Agent type constraints

Custom tool definitions are only available for machines using **flatagents** as the agent runtime (machine `tool_loop`). Machines using **Codex CLI** or **Claude Code CLI** as agent adapters cannot specify tools in the machine config — those agents use their own built-in tool loops. This distinction will need to be surfaced in the create flow (e.g. a flag or agent type field) when adapter support is added.

---

## Architecture: Runtime, Hooks & Deployment

## What's compiled vs what's config

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

## Entrypoint model

The compiled binary IS the entrypoint. No `run.sh` needed for execution:

```
./tagline-writer run --input '{"task": "write a tagline"}'
./tagline-writer resume --execution-id abc123
./tagline-writer signal --id abc123 --channel approval/1 --data '{"approved":true}'
./tagline-writer status
```

The binary can also be a long-running service, a Lambda handler, or anything else — the SDK runtime is the stable core, the entrypoint shape wraps it.

## Hook registration: compiled vs runtime

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

## Lambda deployment model

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

# AgentHarness: Naming, Positioning & Adoption Strategy

**Date:** 2026-03-22T14:32–14:44  
**Status:** Working strategy  
**Context:** Prototyping discussion during flatmachines_manager development

---

## What FlatMachines Is

A state machine that an LLM is actuated via state transitions AND the LLM can manage states of via a control surface. It is simultaneously:

1. **A state machine the LLM is driven by** — transitions actuate the agent
2. **A control surface the LLM can manipulate** — the agent manages states
3. **The context and environment** — the agent inhabits it

It is a virtual orchestrator / virtual machinery that the LLM has some control over.

## Naming Decision

**AgentHarness** — the globally accepted term for this class of thing.

- "Harness" is the industry-standard word for the environment/chassis agents plug into
- Zero explanation needed; immediately understood
- Generic enough to disappear in a crowd, but correct
- Mitigation: use AgentHarness as the proper noun, "harness" as the concept
  - *"AgentHarness is a state-machine harness for LLM agents"*
  - Gets SEO from "harness" in description, owns "AgentHarness" as the brand

### Names considered and rejected

| Name | Why rejected |
|------|-------------|
| AgentRig | Strong, ownable, but less recognized than "harness" |
| AgentFrame | Elegant but abstract |
| AgentEngine | Sounds like it IS the agent, not the environment |
| GhostRig | Too niche for adoption play |
| SynthRig | Cyberpunk energy, wrong audience |
| Loom | Beautiful metaphor (Jacquard looms = first programmable state machines) but not immediately clear |
| Various single words (Wraith, Vessel, Mantle) | Don't signal "for LLM agents" clearly enough |

## Architecture: The Tool Control Problem

### The core tension

FlatMachines provides **first-class tool control** — the machine defines which tools the agent can use per state. The agent in `machine.yml` has only the 9 domain tools. No file writes, no bash, no escape hatches. The LLM can't hallucinate YAML because it has no tool to write files.

But people are in **Claude Code, Codex CLI, pi** — they're not going to switch runtimes to get our guardrails.

The moment we expose tools as MCP/skills for existing agents, those agents also have `read`, `write`, `bash`, `edit`. Our `create_machine` tool becomes a polite suggestion next to a loaded gun. **Second-class tool control.**

| Approach | Tool control | Agent compatibility | UX |
|----------|-------------|--------------------|----|
| Own machine (current) | ✓ First-class, locked down | ✗ Need our CLI/runtime | Own REPL |
| MCP/skills for existing agents | ✗ Second-class, optional | ✓ Works with anything | Natural |
| Harness runtime (agent runs inside) | ✓ First-class | ✓ Uses existing models | Framework adoption curve |

### Resolution: it's a funnel, not a choice

Skills ARE the gateway drug. The friction we're in right now — getting people to use harness-provided tools — is the adoption problem. Meeting people where they are (their existing agent CLI) requires accepting second-class tool control as the entry point.

## The Three-Layer Adoption Funnel

### Layer 1: Skills/MCP (adoption — zero friction)

- The 9 tools exposed as skills/MCP that any agent CLI can discover
- Works in Claude Code, Codex, pi, any MCP-compatible agent
- Second-class tool control — agent may bypass our tools
- **Value proposition:** templates, validation, registry, versioning — even without guardrails, these save time
- People discover: "wait, there's a whole system here"

**The 9 tools to expose as skills:**

1. `list_machines` — list registered flatmachines
2. `get_machine` — get definition, config, validation status, version history
3. `create_machine` — create from template (tool-loop, writer-critic, ooda, pipeline, signal-wait, distributed-worker)
4. `update_machine` — structured mutations (add/remove/update state, agent, context, setting)
5. `select_model` — choose model profile by purpose
6. `validate_machine` — full validation suite (schema, templates, best practices, structural)
7. `diff_versions` — diff two versions of a machine config
8. `duplicate_machine` — fork a machine under a new name
9. `deprecate_machine` — soft delete (config preserved)

### Layer 2: Harness Runtime (graduation — full power)

- Agent runs INSIDE FlatMachines
- First-class tool control per state — the machine defines the tool surface
- Persistence, checkpointing, human review gates, state transitions
- The full `machine.yml` experience
- **This is what people graduate to** when they want the guardrails

The user doesn't run Claude Code and then discover our tools. They run AgentHarness, and AgentHarness uses Claude/GPT/whatever as the model backend. The machine controls which agent (and therefore which tools) are active in each state.

### Layer 3: Surfaces (orthogonal — build as needed)

Surfaces are just different ways to observe and interact with the same machine state. They all read from the same SQLite registry, the same state transitions.

- **CLI/REPL** — what exists now in flatmachines_manager
- **Web UI** — visual state machine editor, run monitoring
- **TUI dashboard** — terminal-native observation
- **stdout/streaming** — pipe-friendly output
- **Auditory** — voice interface (future)

Surfaces don't compete with each other or with the layers above. They're views.

## What Exists Today (flatmachines_manager)

A working Layer 2 prototype: a FlatMachine that uses an LLM to create/manage other FlatMachines.

### Components

```
flatmachines_manager/
├── config/
│   ├── machine.yml          # The manager machine (start → work → human_review → done)
│   ├── agent.yml             # Manager agent with 9 domain tools, locked-down system prompt
│   └── profiles.yml          # Model profiles (fast/smart/code/cheap → gpt-5.3-codex)
└── python/src/flatmachine_manager/
    ├── main.py               # CLI: REPL, single-shot, standalone, demo modes
    ├── tools.py              # 9 domain tools + FlatMachineToolProvider
    ├── registry.py           # SQLite-backed versioned machine registry
    ├── templates.py          # 6 templates (tool-loop, writer-critic, ooda, pipeline, signal-wait, distributed-worker)
    ├── hooks.py              # ManagerHooks: tool provider, display, human review
    ├── validation.py         # Schema + Jinja2 + best practices + structural validation
    └── demo.py               # Full CRUD lifecycle demo (no LLM needed)
```

### Key design decisions already made

- **No raw YAML writing** — agent uses structured tools, never writes config by hand
- **Templates over generation** — LLM parameterizes, doesn't create from scratch
- **Versioned registry** — every change creates a new version, full diff/rollback
- **Validation pipeline** — schema, Jinja2 portability, best practices (from BEST_PRACTICES.md + TIPS.md), structural integrity
- **Human review gate** — built into the machine's state flow

## Next Steps

1. **Extract the 9 tools into standalone skills** — each tool becomes a skill that any agent CLI can call
2. **Keep the harness runtime** as the deeper offering (Layer 2)
3. **Stop treating CLI as the product question** — it's a surface concern, not an architecture one
4. **The REPL isn't wasted** — it's a great dev/demo tool, and one of many possible surfaces

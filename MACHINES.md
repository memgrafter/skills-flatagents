# Skill Pattern Reference

Skills use **flatmachines** as state machines to orchestrate **flatagents** as short-lived, stateless LLM agents.

## Directory Structure

```
skill_name/
├── SKILL.md          # Discovery file (YAML frontmatter + usage)
├── machine.yml       # State machine definition
├── run.sh            # Entry point script
├── agents/           # Agent definitions
│   └── *.yml        
└── src/              # Python modules
    └── skill_name/
        ├── __init__.py
        ├── main.py   # CLI entrypoint
        └── hooks.py  # Optional MachineHooks
```

## Core Files

### SKILL.md
YAML frontmatter for discovery, then usage instructions:
```yaml
---
name: my-skill
description: Brief description for discoverability.
---

Usage instructions and examples in markdown.
```

### machine.yml
```yaml
spec: flatmachine
spec_version: "x.y.z"  # grep SPEC_VERSION .venv/**/flatmachine.d.ts

data:
  name: my-skill
  context:
    query: "{{ input.query }}"
    result: ""
  agents:
    processor: ./agents/processor.yml
  states:
    start:
      type: initial
      transitions:
        - to: process
    process:
      agent: processor
      input:
        query: "{{ context.query }}"
      output_to_context:
        result: "{{ output.content }}"
      transitions:
        - to: done
    done:
      type: final
      output:
        result: "{{ context.result }}"
```

### agents/*.yml
```yaml
spec: flatagent
spec_version: "x.y.z"  # grep SPEC_VERSION .venv/**/flatagent.d.ts

data:
  name: processor
  model:
    provider: cerebras
    name: zai-glm-4.6
    temperature: 0.6
  system: |
    You are a helpful assistant.
  user: |
    Process this: {{ input.query }}
```

### run.sh
Bash entry point activating venv and calling Python:
```bash
#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(dirname $(readlink -f "$0"))/.."
source "$REPO_ROOT/.venv/bin/activate"
SKILL_DIR="$(dirname $(readlink -f "$0"))"
export PYTHONPATH="$SKILL_DIR/src:${PYTHONPATH:-}"
exec python -m skill_name.main "$@"
```

### src/skill_name/main.py
Python entry point that loads and runs the machine:
```python
from flatmachines import FlatMachine

def main():
    machine = FlatMachine.from_yaml("path/to/machine.yml")
    result = machine.run({"input_field": value})
    print(result.output)
```

### src/skill_name/hooks.py (Optional)
Custom actions via `MachineHooks`:
```python
from flatmachines import MachineHooks

class CustomHooks(MachineHooks):
    def on_action(self, action: str, context: dict) -> dict:
        if action == "my_action":
            # Custom logic
            return {"new_var": "value"}
        return {}
```

Reference `settings.hooks: skill_name.hooks` in machine.yml.

## State Types

| Type | Purpose |
|------|---------|
| `type: initial` | Entry state, exactly one per machine |
| `agent: name` | Call a flatagent, map input/output |
| `machine: name` | Invoke child machine (from `machines` map) |
| `action: name` | Call a hook action |
| `type: final` | Terminal state with output mapping |

## Context Flow

1. **Input**: `{{ input.field }}` - passed to `machine.run({...})`
2. **Context**: `{{ context.var }}` - shared working memory
3. **Output mapping**: `output_to_context` copies agent output to context
4. **Final output**: `output` in final state defines machine result

## Expression Engines

Conditions use `simple` (default) or `cel` expression engine:

| Engine | Syntax | Use Case |
|--------|--------|----------|
| `simple` | `context.count >= 3` | Basic comparisons, boolean logic |
| `cel` | `context.items.size() > 0` | List operations, string functions, complex logic |

Set in machine settings: `settings: { expression_engine: cel }`

## Key Patterns

- **Templating**: Use `{{ context.var }}` and `{{ input.var }}` in YAML
- **State flow**: `type: initial` → agent/action/machine states → `type: final`
- **Error handling**: `on_error: error_state` with `{{ context.last_error }}`
- **Retry logic**: `execution: { type: retry, backoffs: [2, 8], jitter: 0.1 }`
- **Parallel**: `execution: { type: parallel, n_samples: 3 }`
- **Conditions**: `transitions: [{ condition: "expr", to: state }]`
- **Loops**: Use conditions to loop back (e.g., `round < max_rounds`)
- **MCP tools**: Agent `mcp: { servers: {...}, tool_prompt: "..." }` for tool use

### Dynamic Patterns

- **Nested HSM**: `machines: { sub: ./sub.yml }` → state `machine: sub` → child runs, output merges to context
- **Dynamic agent**: Inline `agents: { gen: { spec: flatagent, data: {...} } }` or hook returns AgentWrapper
- **Dynamic machine**: Inline `machines: { dyn: { spec: flatmachine, data: {...} } }` for runtime composition
- **Decider**: Agent outputs `decision` field → transitions branch: `condition: "output.decision == 'path_a'"`

## Quick-Start Checklist

1. Create `skill_name/` directory
2. Write `SKILL.md` with name/description frontmatter
3. Define agents in `agents/*.yml` (use flatagent spec)
4. Build state machine in `machine.yml` (use flatmachine spec)
5. Add `run.sh` entry script
6. Create `src/skill_name/main.py` to load and run machine
7. Add hooks in `hooks.py` if custom actions needed
8. Test: `./run.sh <input>`

## Spec Assets

To get latest specs, upgrade flatagents: `uv pip install -p .venv/bin/python --upgrade flatagents`

Canonical sources in `.venv/lib/python3.12/site-packages/flatagents/assets/`:

| Asset | Use Case |
|-------|----------|
| `flatagent.d.ts` | **Canonical** — full TypeScript spec with JSDoc |
| `flatmachine.d.ts` | **Canonical** — full TypeScript spec with JSDoc |
| `flatagent.slim.d.ts` | Minimal spec to save context |
| `flatmachine.slim.d.ts` | Minimal spec to save context |

**Recommendation**: Read the full `.d.ts` files when creating or modifying agents/machines. Use `.slim.d.ts` for context-constrained scenarios.


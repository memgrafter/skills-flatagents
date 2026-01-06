# Dynamic Agent

Dynamically generates and executes a specialized agent for any task.

## How It Works

1. **Generator** creates a specialized agent based on your task
2. **Supervisor** validates the spec before execution
3. **Human Review** (optional) - approve/deny the generated agent
4. **OTF Agent** executes if approved, otherwise regenerates with feedback

```
Start → Generate Agent → Supervise → Human Review → Execute → Done
              ↑                            │
              └────── Rejected ────────────┘
```

## Usage

```bash
# Non-interactive (auto-approve)
./run.sh -y "Write a haiku about debugging"

# Interactive (human review)
./run.sh "Write a limerick about coffee"

# With style hints
./run.sh -y "Write a short story opening" --style "noir detective"
```

## Options

| Flag | Description |
|------|-------------|
| `-y`, `--auto-approve` | Skip human review, auto-approve if supervisor approves |
| `--style "<hints>"` | Style hints for the task |

## Files

| File | Purpose |
|------|---------|
| `machine.yml` | State machine orchestration |
| `agents/generator.yml` | Generates specialized agent specs |
| `agents/supervisor.yml` | Pre-execution validation |
| `src/dynamic_agent/hooks.py` | Human review + OTF execution |

## Why OTF Agents?

- **Specialization**: Each task gets a tailored agent, not a generic one
- **Safety**: Supervisor catches problematic specs before execution
- **Iterative**: Feedback loops improve agent design on rejection

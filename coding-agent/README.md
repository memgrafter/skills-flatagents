# Coding Agent

An AI coding agent built on FlatAgents that plans, implements, and verifies code changes with human approval gates.

## Features

- **OODA Loop**: Explore → Plan → Execute → Verify
- **Human-in-the-Loop**: Approval checkpoints before risky operations
- **History Preservation**: Rejected plans/changes are preserved so agents learn from feedback
- **OpenSkills Compatible**: Standard SKILL.md format

## Quick Start

```bash
cd python
./run.sh --local "Create a hello world function in Python" --cwd /tmp/test
```

## Usage

```bash
./run.sh [OPTIONS] "TASK"

Arguments:
  TASK                  The coding task to accomplish

Options:
  --cwd, -c PATH        Working directory (default: current)
  --max-iterations, -m  Maximum revision iterations (default: 5)
  --local, -l           Install flatagents from local SDK
```

## Architecture

```
receive_task → explore_codebase → plan_changes → [HUMAN REVIEW]
                                        ↓
                                  execute_plan → verify_changes → [HUMAN REVIEW] → done
```

On rejection, feedback is preserved and the agent revises with full context of previous attempts.

## Tools Configuration

Edit `config/tools.yml` to configure:
- MCP servers (filesystem, search)
- Shell command approval patterns
- Skills directory path

## Skills Integration

Symlink external skills:
```bash
ln -s /path/to/your/skills .skills
```

Skills are loaded on-demand during execution.

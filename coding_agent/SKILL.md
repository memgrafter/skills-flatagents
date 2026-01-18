---
name: coding-agent
description: AI coding agent that plans, implements, and verifies code changes with human approval gates. Built on FlatAgents.
---

# Coding Agent

An agentic coding assistant with human-in-the-loop review.

## Usage

```bash
cd python && ./run.sh "Add input validation to the User model" --cwd /path/to/project
```

## Flow

1. **Explore** — Gathers codebase context
2. **Plan** — Generates implementation plan → human reviews
3. **Execute** — Applies changes using MCP filesystem
4. **Verify** — Reviews changes → human approves

## Skills Integration

Symlink skills for the agent to use:
```bash
ln -s /path/to/skills .skills
```

The agent loads skills on-demand from `.skills/` directory.

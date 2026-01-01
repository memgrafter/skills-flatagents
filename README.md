# Claude Skills - FlatAgents

Claude Code skills powered by [FlatAgents](https://github.com/memgrafter/flatagents).

## Skills

All skill use flatagents, returning limited context to claude to preserve the context window.

- **search_refiner** - Search the web with Exa MCP and refine results to 500 tokens
- **shell_analyzer** - Run shell commands and analyze output with validated summaries. Use for build logs, test output, or any command with substantial output. Preserves context by returning concise summaries with grep-validated citations.
- **test_writer** - Generate tests for a Python file or project

## Install

```bash
./install.sh
```

## Upgrade

To upgrade flatagents and dependencies to the latest versions:

```bash
./install.sh --upgrade
```

This ensures you have the latest FlatMachine features (requires flatagents >= 0.1.6).

## Requirements

- Python 3.10+
- `CEREBRAS_API_KEY` or `OPENAI_API_KEY`
- `EXA_API_KEY`

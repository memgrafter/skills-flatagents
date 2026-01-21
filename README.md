# FlatAgents Skills

Agent skills powered by [FlatAgents](https://github.com/memgrafter/flatagents).

LLM/machine readers: use MACHINES.md as a primary reference, it is more comprehensive and token efficient.

## Skills

All skills use FlatAgents, returning limited context to the caller to preserve the context window.

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
- API key(s) for your chosen LLM provider(s)

## Configuration

Each skill uses agents defined in `agents/*.yml` files. Configure your provider and model by editing these files:

```yaml
# Example: agents/analyzer.yml
data:
  model:
    provider: openai      # anthropic, openai, cerebras, etc.
    name: gpt-4          # model name for your provider
    temperature: 0.1
    max_tokens: 4096
```

**Common providers:**
- `anthropic` - Requires `ANTHROPIC_API_KEY` (models: see provider docs)
- `openai` - Requires `OPENAI_API_KEY` (models: gpt-4, gpt-4-turbo, etc.)
- `cerebras` - Requires `CEREBRAS_API_KEY` (models: zai-glm-4.7, etc.)
- See [FlatAgents docs](https://github.com/memgrafter/flatagents) for full provider list

**search_refiner** also requires `EXA_API_KEY` for web search via Exa MCP.

## Usage

```bash
# Search and refine web results
./search_refiner/run.sh "your search query"

# Analyze shell command output
./shell_analyzer/run.sh "pytest -v"

# Generate tests to reach coverage target
./test_writer/run.sh path/to/file.py --target=80
```

Each skill's agents are pre-configured with Cerebras (fast, cheap) but you can change to any provider by editing the `agents/*.yml` files.

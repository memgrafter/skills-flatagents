# Search Refiner

2-agent FlatAgent workflow: search the web with Exa, refine results to key findings.

## Requirements

- Python 3.10+
- API key for your chosen LLM provider (configured in `agents/*.yml`)
- `EXA_API_KEY` for web search via Exa MCP

## Install

```bash
./install.sh
```

## Usage

```bash
./run.sh "your query"
```

## Architecture

1. **Search Agent** - Web search via Exa MCP
2. **Refiner Agent** - Condenses results to ≤500 tokens

## Configuration

Edit the agent YAML files to change provider/model:
- `agents/search.yml` - Search agent (provider, model, temperature, etc.)
- `agents/refiner.yml` - Refiner agent (output token limit, etc.)
- `machine.yml` - State machine flow (retry backoffs, error handling)

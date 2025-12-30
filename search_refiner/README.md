# Search Refiner

2-agent FlatAgent workflow: search the web with Exa, refine results to key findings.

## Requirements

- Python 3.10+
- `CEREBRAS_API_KEY` or `OPENAI_API_KEY`
- `EXA_API_KEY`

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

- `config/search.yml` - Search agent config
- `config/refiner.yml` - Refiner agent config

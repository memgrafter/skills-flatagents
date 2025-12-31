#!/usr/bin/env bash
set -euo pipefail

# Find repo root (look for .venv at parent level)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV="$REPO_ROOT/.venv"

# Check for API Keys
if [[ -z "${CEREBRAS_API_KEY:-}" && -z "${OPENAI_API_KEY:-}" ]]; then
    echo "ERROR: Set CEREBRAS_API_KEY or OPENAI_API_KEY" >&2
    exit 1
fi

if [[ -z "${EXA_API_KEY:-}" ]]; then
    echo "ERROR: EXA_API_KEY not found. Get one at https://exa.ai" >&2
    exit 1
fi

# Activate shared venv
if [[ ! -d "$VENV" ]]; then
    echo "ERROR: Shared venv not found at $VENV" >&2
    echo "Run $REPO_ROOT/install.sh first" >&2
    exit 1
fi

source "$VENV/bin/activate"

# Run skill with default query if no args provided
QUERY="${*:-latest developments in AI agents}"
exec python -m search_refiner.main "$QUERY"

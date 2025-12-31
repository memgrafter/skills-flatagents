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

# Activate shared venv
if [[ ! -d "$VENV" ]]; then
    echo "ERROR: Shared venv not found at $VENV" >&2
    echo "Run $REPO_ROOT/install.sh first" >&2
    exit 1
fi

source "$VENV/bin/activate"

# Run skill with all arguments
exec python -m test_writer.main "$@"

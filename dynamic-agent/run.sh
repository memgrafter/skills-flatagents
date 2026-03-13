#!/usr/bin/env bash
set -euo pipefail

# Find repo root (look for .venv at parent level)
REPO_ROOT="$(dirname $(readlink -f "$0"))/.."
VENV="$REPO_ROOT/.venv"

# Activate shared venv
if [[ ! -d "$VENV" ]]; then
    echo "ERROR: Shared venv not found at $VENV" >&2
    echo "Run $REPO_ROOT/install.sh first" >&2
    exit 1
fi

source "$VENV/bin/activate"

# Run skill
SKILL_DIR="$(dirname $(readlink -f "$0"))"
export PYTHONPATH="$SKILL_DIR/src:${PYTHONPATH:-}"
exec python -m dynamic_agent.main "$@"

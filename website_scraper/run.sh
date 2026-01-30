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

# Check for trafilatura
if ! python -c "import trafilatura" 2>/dev/null; then
    echo "Installing trafilatura..."
    pip install trafilatura >/dev/null
fi

# Run skill
SKILL_DIR="$(dirname $(readlink -f "$0"))"
export PYTHONPATH="$SKILL_DIR/src:${PYTHONPATH:-}"

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <url> [data_dir]" >&2
    echo "  or: DATA_DIR=/path/to/archive $0 <url>" >&2
    exit 1
fi

exec python -m website_scraper.main "$@"

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

# Parse style argument (--style=X or -s X)
STYLE="compact"
COMMAND=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --style=*)
            STYLE="${1#*=}"
            shift
            ;;
        -s)
            STYLE="$2"
            shift 2
            ;;
        *)
            if [[ -z "$COMMAND" ]]; then
                COMMAND="$1"
            else
                COMMAND="$COMMAND $1"
            fi
            shift
            ;;
    esac
done

COMMAND="${COMMAND:-echo 'No command provided'}"

# Set PYTHONPATH to find skill modules
SKILL_DIR="$(dirname $(readlink -f "$0"))"
export PYTHONPATH="$SKILL_DIR/src:${PYTHONPATH:-}"

# Run skill
exec python -m shell_analyzer.main --style="$STYLE" "$COMMAND"

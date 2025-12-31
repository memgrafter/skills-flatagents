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

# Run skill
exec python -m shell_analyzer.main --style="$STYLE" "$COMMAND"

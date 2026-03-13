#!/bin/bash
set -euo pipefail
REPO_ROOT="$(dirname $(readlink -f "$0"))/.."
source "$REPO_ROOT/.venv/bin/activate"
SKILL_DIR="$(dirname $(readlink -f "$0"))"
export PYTHONPATH="$SKILL_DIR/src:${PYTHONPATH:-}"

# Pass all args through - including --claude flag for Claude Code integration
exec python -m coding_agent.main "$@"

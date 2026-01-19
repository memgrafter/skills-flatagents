#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(dirname $(readlink -f "$0"))/.."
source "$REPO_ROOT/.venv/bin/activate"
SKILL_DIR="$(dirname $(readlink -f "$0"))"
export PYTHONPATH="$SKILL_DIR/src:${PYTHONPATH:-}"
exec python -m socratic_teacher.main "$@"

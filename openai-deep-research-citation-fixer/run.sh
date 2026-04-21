#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 /path/to/file.md [--no-overwrite]" >&2
  exit 1
fi

exec python3 "$SKILL_DIR/fix_openai_deep_research_citations.py" "$@"

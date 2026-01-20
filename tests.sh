#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

src_dirs=()
while IFS= read -r -d '' dir; do
  src_dirs+=("$dir")
done < <(find "$REPO_ROOT" -maxdepth 2 -type d -name src -print0)

pythonpath="$REPO_ROOT"
for dir in "${src_dirs[@]}"; do
  pythonpath="${pythonpath}:${dir}"
done

example_dir="$REPO_ROOT/test_writer/example"
if [[ -d "$example_dir" ]]; then
  pythonpath="${pythonpath}:${example_dir}"
fi

if [[ -n "${PYTHONPATH:-}" ]]; then
  pythonpath="${pythonpath}:${PYTHONPATH}"
fi

export PYTHONPATH="${pythonpath}"

python -m pytest -v "$@"

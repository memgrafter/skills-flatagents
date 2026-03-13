#!/bin/bash
# Copyright (C) 2026 Trent Zock-Robbins
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Activate virtual environment if it exists
if [ -f "$SCRIPT_DIR/../.venv/bin/activate" ]; then
  source "$SCRIPT_DIR/../.venv/bin/activate"
elif [ -f "$SCRIPT_DIR/../../.venv/bin/activate" ]; then
  source "$SCRIPT_DIR/../../.venv/bin/activate"
fi

export PYTHONPATH="$SCRIPT_DIR/src:${PYTHONPATH:-}"

python -m repo_map.main "$@"

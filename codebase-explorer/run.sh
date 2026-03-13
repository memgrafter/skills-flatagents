#!/bin/bash
# Codebase Explorer - Explore a codebase to gather context for a task

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Activate virtual environment if it exists
if [ -f "$SCRIPT_DIR/../.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/../.venv/bin/activate"
elif [ -f "$SCRIPT_DIR/../../.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/../../.venv/bin/activate"
fi

# Add src to Python path
export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"

# Run the explorer
python -m codebase_explorer.main "$@"

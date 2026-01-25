#!/bin/bash
# Codebase Ripper - Shotgun codebase exploration

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Activate virtual environment if it exists
if [ -f "$SCRIPT_DIR/../.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/../.venv/bin/activate"
elif [ -f "$SCRIPT_DIR/../../.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/../../.venv/bin/activate"
fi

# Add src to Python path
export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"

# Run the ripper
python -m codebase_ripper.main "$@"

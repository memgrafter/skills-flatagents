#!/bin/bash
# Codebase Ripper - Shotgun codebase exploration with iterative passes
#
# Usage:
#   ./run.sh "task description" [-d directory] [--token-budget N] [--max-iterations N] [--json]
#
# Options:
#   -d, --directory DIR     Working directory to explore (default: current directory)
#   --token-budget N        Maximum tokens for extracted context (default: 40000)
#   --max-iterations N      Maximum exploration iterations (default: 2)
#   --json                  Output results as JSON
#
# Examples:
#   ./run.sh "understand how the auth system works" -d /path/to/project
#   ./run.sh "find all database queries" --max-iterations 3 --json

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

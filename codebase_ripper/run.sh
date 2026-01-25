#!/bin/bash
# Run codebase ripper

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if running from installed package or development
if python -c "import codebase_ripper" 2>/dev/null; then
    python -m codebase_ripper.main "$@"
else
    PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH" python -m codebase_ripper.main "$@"
fi

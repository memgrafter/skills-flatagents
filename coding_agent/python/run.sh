#!/bin/bash
set -e

VENV_PATH=".venv"

# Parse arguments
LOCAL_INSTALL=false
QUIET=false
PASSTHROUGH_ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --local|-l) LOCAL_INSTALL=true; shift ;;
        --quiet|-q) QUIET=true; shift ;;
        *) PASSTHROUGH_ARGS+=("$1"); shift ;;
    esac
done

if [ "$QUIET" = false ]; then
    echo "--- 🤖 Coding Agent Runner ---"
fi

# Save original cwd before switching to script directory
ORIGINAL_CWD="$(pwd)"

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Calculate relative path to SDK root
SDK_ROOT="$SCRIPT_DIR/../../.."

# Check if --cwd was provided, if not add original cwd
CWD_PROVIDED=false
for arg in "${PASSTHROUGH_ARGS[@]}"; do
    if [[ "$arg" == "--cwd" || "$arg" == "-c" ]]; then
        CWD_PROVIDED=true
        break
    fi
done
if [ "$CWD_PROVIDED" = false ]; then
    PASSTHROUGH_ARGS+=("--cwd" "$ORIGINAL_CWD")
fi

# Suppress pip output if quiet
PIP_QUIET=""
if [ "$QUIET" = true ]; then
    PIP_QUIET="--quiet"
fi

# Create venv if needed
if [ ! -d "$VENV_PATH" ]; then
    [ "$QUIET" = false ] && echo "Creating virtual environment..."
    uv venv "$VENV_PATH" 2>/dev/null
fi

# Install flatagents
if [ "$LOCAL_INSTALL" = true ]; then
    [ "$QUIET" = false ] && echo "Installing local flatagents..."
    uv pip install $PIP_QUIET --python "$VENV_PATH/bin/python" -e "$SDK_ROOT/python[litellm]"
else
    [ "$QUIET" = false ] && echo "Installing flatagents from PyPI..."
    uv pip install $PIP_QUIET --python "$VENV_PATH/bin/python" "flatagents[litellm]"
fi

# Install this example
uv pip install $PIP_QUIET --python "$VENV_PATH/bin/python" -e "$SCRIPT_DIR"

# Run (set LOG_LEVEL for quiet mode)
if [ "$QUIET" = true ]; then
    LOG_LEVEL=WARNING "$VENV_PATH/bin/python" -m coding_agent.main "${PASSTHROUGH_ARGS[@]}"
else
    "$VENV_PATH/bin/python" -m coding_agent.main "${PASSTHROUGH_ARGS[@]}"
fi

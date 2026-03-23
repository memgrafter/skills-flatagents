#!/bin/bash
set -e

# --- Configuration ---
VENV_PATH=".venv"
FLATAGENTS_ROOT="$HOME/code/flatagents"

# --- Parse Arguments ---
LOCAL_INSTALL=false
PASSTHROUGH_ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --local|-l)
            LOCAL_INSTALL=true
            shift
            ;;
        *)
            PASSTHROUGH_ARGS+=("$1")
            shift
            ;;
    esac
done

# --- Script Logic ---
echo "--- FlatMachine Manager Runner ---"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 1. Create Virtual Environment
echo "Ensuring virtual environment..."
if [ ! -d "$VENV_PATH" ]; then
    uv venv "$VENV_PATH"
else
    echo "Virtual environment already exists."
fi

# 2. Install Dependencies
echo "Installing dependencies..."
if [ "$LOCAL_INSTALL" = true ] && [ -d "$FLATAGENTS_ROOT/sdk/python" ]; then
    echo "  - Installing from local source ($FLATAGENTS_ROOT)..."
    uv pip install --python "$VENV_PATH/bin/python" -e "$FLATAGENTS_ROOT/sdk/python/flatmachines[flatagents]"
    uv pip install --python "$VENV_PATH/bin/python" -e "$FLATAGENTS_ROOT/sdk/python/flatagents[litellm]"
else
    echo "  - Installing from PyPI..."
    uv pip install --python "$VENV_PATH/bin/python" "flatmachines[flatagents]"
    uv pip install --python "$VENV_PATH/bin/python" "flatagents[litellm]"
fi

echo "  - Installing flatmachine_manager package..."
uv pip install --python "$VENV_PATH/bin/python" pyyaml
uv pip install --python "$VENV_PATH/bin/python" -e "$SCRIPT_DIR"

# 3. Run
echo ""
echo "---"
"$VENV_PATH/bin/python" -m flatmachine_manager.main "${PASSTHROUGH_ARGS[@]}"

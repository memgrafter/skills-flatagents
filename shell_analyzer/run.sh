#!/bin/bash
set -e

# --- Configuration ---
SKILL_NAME="shell-analyzer"

# Get the directory the script is located in
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Find the .claude/skills directory (walk up from script location)
find_skills_dir() {
    local dir="$1"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.claude/skills" ]; then
            echo "$dir/.claude/skills"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    # Fallback: create in current working directory
    echo "$PWD/.claude/skills"
}

SKILLS_DIR="$(find_skills_dir "$SCRIPT_DIR")"
VENV_PATH="$SKILLS_DIR/$SKILL_NAME/.venv"
MARKER_FILE="$VENV_PATH/.installed"

# Check if uv is available
HAS_UV=false
if command -v uv &> /dev/null; then
    HAS_UV=true
fi

# --- Helper Functions ---
create_venv() {
    if [ "$HAS_UV" = true ]; then
        uv venv "$VENV_PATH"
    else
        python3 -m venv "$VENV_PATH"
    fi
}

pip_install() {
    if [ "$HAS_UV" = true ]; then
        uv pip install --python "$VENV_PATH/bin/python" "$@"
    else
        "$VENV_PATH/bin/pip" install "$@"
    fi
}

# Compute hash of pyproject.toml for update detection
get_config_hash() {
    if command -v md5sum &> /dev/null; then
        md5sum "$SCRIPT_DIR/pyproject.toml" 2>/dev/null | cut -d' ' -f1
    elif command -v md5 &> /dev/null; then
        md5 -q "$SCRIPT_DIR/pyproject.toml" 2>/dev/null
    else
        echo "no-hash"
    fi
}

needs_setup() {
    # Setup needed if: --setup flag, no marker, or config changed
    [ "$1" = "--setup" ] && return 0
    [ ! -f "$MARKER_FILE" ] && return 0

    # Check if pyproject.toml changed (update detection)
    local current_hash=$(get_config_hash)
    local stored_hash=$(cat "$MARKER_FILE" 2>/dev/null || echo "")
    [ "$current_hash" != "$stored_hash" ] && return 0

    return 1
}

# --- Script Logic ---

# 1. Check for API Keys
if [ -z "$CEREBRAS_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "ERROR: No LLM API key found."
    echo "   Please set CEREBRAS_API_KEY or OPENAI_API_KEY"
    exit 1
fi

# 2. Create Virtual Environment and Install Dependencies (only if needed)
if needs_setup "$1"; then
    echo "Setting up $SKILL_NAME..."
    mkdir -p "$(dirname "$VENV_PATH")"

    if [ ! -d "$VENV_PATH" ]; then
        create_venv
    fi

    # Install dependencies
    pip_install "flatagents[aisuite]"
    pip_install -e "$SCRIPT_DIR"

    # Store config hash as marker
    get_config_hash > "$MARKER_FILE"

    # If only --setup was passed, exit here
    [ "$1" = "--setup" ] && [ -z "$2" ] && echo "Setup complete!" && exit 0
    [ "$1" = "--setup" ] && shift
fi

# 3. Parse style argument (--style=X or -s X)
STYLE="compact"
COMMAND=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --style=*)
            STYLE="${1#*=}"
            shift
            ;;
        -s)
            STYLE="$2"
            shift 2
            ;;
        *)
            if [ -z "$COMMAND" ]; then
                COMMAND="$1"
            else
                COMMAND="$COMMAND $1"
            fi
            shift
            ;;
    esac
done

COMMAND="${COMMAND:-echo 'No command provided'}"

# 4. Run
"$VENV_PATH/bin/python" -m shell_analyzer.main --style="$STYLE" "$COMMAND"

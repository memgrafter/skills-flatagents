#!/usr/bin/env bash
set -euo pipefail

# Global installation only for now

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/.venv"
MANIFEST="$SCRIPT_DIR/install-manifest.yml"

# Parse arguments
SKILL_FILTER=""
UPGRADE=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --skill=*)
            SKILL_FILTER="${1#*=}"
            shift
            ;;
        --upgrade)
            UPGRADE=true
            shift
            ;;
        *)
            echo "Usage: $0 [--skill=<skill-name>] [--upgrade]" >&2
            exit 1
            ;;
    esac
done

# Detect package manager
if command -v uv &>/dev/null; then
    USE_UV=true
else
    USE_UV=false
fi

# Helper function to run pip with correct target
pip_install() {
    if [[ "$USE_UV" = true ]]; then
        uv pip install -p "$VENV/bin/python" "$@"
    else
        pip install "$@"
    fi
}

# Create virtualenv if needed
if [[ ! -d "$VENV" ]]; then
    echo "Creating shared virtualenv at $VENV..."
    if [[ "$USE_UV" = true ]]; then
        uv venv "$VENV"
    else
        python3 -m venv "$VENV"
    fi
fi

# Activate venv (needed for non-uv commands and PATH)
source "$VENV/bin/activate"

# Upgrade mode: force reinstall flatagents to latest version
if [[ "$UPGRADE" = true ]]; then
    echo "Upgrading flatagents to latest version..."
    pip_install --upgrade flatagents
fi

# Install project in editable mode with base dependencies
echo "Installing base dependencies..."
pip_install -e "$SCRIPT_DIR"

# Ensure flatagents >= 0.1.6 (required for FlatMachine support)
echo "Ensuring flatagents >= 0.1.6..."
pip_install "flatagents>=0.1.6"

# Parse manifest to get skill list
if [[ -z "$SKILL_FILTER" ]]; then
    # Install all skills from manifest
    if [[ ! -f "$MANIFEST" ]]; then
        echo "ERROR: install-manifest.yml not found" >&2
        exit 1
    fi

    # Extract skills from YAML (simple parser for "- <skill>" lines)
    SKILLS=$(grep "^  - " "$MANIFEST" | sed 's/^  - //')
else
    # Install specific skill
    SKILLS="$SKILL_FILTER"
fi

# Install optional dependencies for selected skills
for skill in $SKILLS; do
    echo "Installing dependencies for $skill..."
    pip_install -e "$SCRIPT_DIR"["$skill"] || {
        # Fallback if the group doesn't exist, just install base
        echo "  (no skill-specific dependencies for $skill)"
    }

    # Install skill src if it has its own directory
    if [[ -d "$SCRIPT_DIR/$skill" ]]; then
        echo "Installing editable package: $skill"
        pip_install -e "$SCRIPT_DIR/$skill" 2>/dev/null || true
    fi
done

# Symlink skills to ~/.claude/skills/
SKILLS_DIR="$HOME/.claude/skills"
mkdir -p "$SKILLS_DIR"

for skill in $SKILLS; do
    SKILL_RUN_SH="$SCRIPT_DIR/$skill"
    if [[ -d "$SKILL_RUN_SH" ]]; then
        SKILL_LINK="$SKILLS_DIR/$skill"

        # Remove old link if exists
        [[ -L "$SKILL_LINK" ]] && rm "$SKILL_LINK"

        # Create symlink to skill
        ln -s "$SKILL_RUN_SH" "$SKILL_LINK"
        echo "  ✓ Symlinked: $skill -> $SKILL_LINK"
    fi
done

echo ""
echo "✓ Installation complete!"
echo ""
echo "To use skills, ensure these environment variables are set:"
echo "  export CEREBRAS_API_KEY='...'"
echo "  export OPENAI_API_KEY='...'  (optional, if not using Cerebras)"
echo ""

if [[ -n "$SKILL_FILTER" ]]; then
    echo "Installed skill: $SKILL_FILTER"
    echo "Usage: $SCRIPT_DIR/$SKILL_FILTER/run.sh [args]"
else
    echo "Installed skills:"
    for skill in $SKILLS; do
        echo "  - $skill"
    done
    echo ""
    echo "Usage examples:"
    for skill in $SKILLS; do
        echo "  $SCRIPT_DIR/$skill/run.sh [args]"
    done
fi

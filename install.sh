#!/usr/bin/env bash
set -euo pipefail

# Global installation only for now

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/.venv"
MANIFEST="$SCRIPT_DIR/install-manifest.yml"

# Parse arguments
SKILL_FILTER=""
USE_LOCAL_SDK=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --skill=*)
            SKILL_FILTER="${1#*=}"
            shift
            ;;
        --local)
            USE_LOCAL_SDK=true
            shift
            ;;
        *)
            echo "Usage: $0 [--skill=<skill-name>] [--local]" >&2
            echo "  --local    Install flatagents SDK from ~/code/flatagents/sdk/python (editable)"
            exit 1
            ;;
    esac
done

LOCAL_SDK_PATH="${FLATAGENTS_SDK_PATH:-$HOME/code/flatagents}/sdk/python"

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
        python -m pip install "$@"
    fi
}

# Create virtualenv if needed
# NOTE: numpy==1.26.4 (pulled via aisuite[all]) has no cp313 wheel,
# so Python 3.13+ can trigger source builds that fail on systems without python-dev headers.
if [[ -d "$VENV" ]] && [[ -x "$VENV/bin/python" ]]; then
    if "$VENV/bin/python" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 13) else 1)'; then
        echo "Existing venv uses Python >=3.13; recreating with Python 3.12 for dependency compatibility..."
        rm -rf "$VENV"
    fi
fi

if [[ ! -d "$VENV" ]]; then
    echo "Creating shared virtualenv at $VENV..."
    if [[ "$USE_UV" = true ]]; then
        uv venv --python 3.12 "$VENV"
    else
        if command -v python3.12 &>/dev/null; then
            python3.12 -m venv "$VENV"
        else
            python3 -m venv "$VENV"
        fi
    fi
fi

# Activate venv (needed for non-uv commands and PATH)
source "$VENV/bin/activate"

# Ensure pip exists in venv (some Python builds omit pip)
if [[ "$USE_UV" = false ]]; then
    if ! python -m pip --version >/dev/null 2>&1; then
        echo "pip not found in $VENV, bootstrapping with ensurepip..."
        python -m ensurepip --upgrade
        python -m pip install -U pip
    fi
fi

# Install flatagents SDK (local or remote with auto-upgrade)
if [[ "$USE_LOCAL_SDK" = true ]]; then
    if [[ ! -d "$LOCAL_SDK_PATH" ]]; then
        echo "ERROR: Local SDK not found at $LOCAL_SDK_PATH" >&2
        exit 1
    fi

    # Support both SDK layouts:
    # 1) single package at sdk/python
    # 2) split packages at sdk/python/flatagents and sdk/python/flatmachines
    if [[ -f "$LOCAL_SDK_PATH/pyproject.toml" || -f "$LOCAL_SDK_PATH/setup.py" ]]; then
        echo "Installing flatagents from local SDK (editable)..."
        pip_install -e "$LOCAL_SDK_PATH"
    elif [[ -f "$LOCAL_SDK_PATH/flatagents/pyproject.toml" ]]; then
        echo "Installing flatagents from local split SDK (editable)..."
        pip_install -e "$LOCAL_SDK_PATH/flatagents"

        if [[ -f "$LOCAL_SDK_PATH/flatmachines/pyproject.toml" ]]; then
            echo "Installing flatmachines from local split SDK (editable)..."
            pip_install -e "$LOCAL_SDK_PATH/flatmachines"
        fi
    else
        echo "ERROR: Local SDK layout not recognized at $LOCAL_SDK_PATH" >&2
        echo "Expected either pyproject.toml in sdk/python, or sdk/python/flatagents/pyproject.toml" >&2
        exit 1
    fi
else
    echo "Installing/upgrading flatagents from PyPI..."
    pip_install --upgrade flatagents
fi

# Install project in editable mode with base dependencies
echo "Installing base dependencies..."
pip_install -e "$SCRIPT_DIR"

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

# Symlink skills to ~/.agents/skills/ (override with AGENTS_SKILLS_DIR; FLATAGENTS_SKILLS_DIR kept for backward compatibility)
SKILLS_DIR="${AGENTS_SKILLS_DIR:-${FLATAGENTS_SKILLS_DIR:-$HOME/.agents/skills}}"
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
echo "Configuration:"
echo "  1. Set API key for your LLM provider (e.g., ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.)"
echo "  2. Edit agents/*.yml files in each skill to configure provider/model"
echo "  3. For search-refiner: Also set EXA_API_KEY for web search"
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

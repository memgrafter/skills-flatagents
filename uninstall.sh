#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/.venv"
MANIFEST="$SCRIPT_DIR/install-manifest.yml"
SKILLS_DIR="${FLATAGENTS_SKILLS_DIR:-$HOME/.flatagents/skills}"

# Parse arguments
SKILL_FILTER=""
CLEAN_VENV=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skill=*)
            SKILL_FILTER="${1#*=}"
            shift
            ;;
        --clean)
            CLEAN_VENV=1
            shift
            ;;
        *)
            echo "Usage: $0 [--skill=<skill-name>] [--clean]" >&2
            exit 1
            ;;
    esac
done

# Determine which skills to uninstall
if [[ -z "$SKILL_FILTER" ]]; then
    # Uninstall all skills from manifest
    if [[ ! -f "$MANIFEST" ]]; then
        echo "ERROR: install-manifest.yml not found" >&2
        exit 1
    fi
    SKILLS=$(grep "^  - " "$MANIFEST" | sed 's/^  - //')
else
    SKILLS="$SKILL_FILTER"
fi

# Remove symlinks
echo "Removing symlinks from $SKILLS_DIR..."
for skill in $SKILLS; do
    SKILL_LINK="$SKILLS_DIR/$skill"
    if [[ -L "$SKILL_LINK" ]]; then
        rm "$SKILL_LINK"
        echo "  ✓ Removed: $SKILL_LINK"
    fi
done

# Remove virtualenv if --clean is specified
if [[ $CLEAN_VENV -eq 1 ]] && [[ -d "$VENV" ]]; then
    echo "Removing shared virtualenv at $VENV..."
    rm -rfI "$VENV"
    echo "  ✓ Removed: $VENV (unless you cancelled!)"
fi

echo ""
echo "✓ Uninstall complete!"

if [[ $CLEAN_VENV -eq 0 ]]; then
    echo ""
    echo "Note: Shared virtualenv at $VENV still exists."
    echo "Use --clean flag to remove it: $0 --clean"
fi

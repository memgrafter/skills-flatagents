#!/bin/bash
set -e

SKILL_NAME="shell-analyzer"
LINK_PATH="$HOME/.claude/skills/$SKILL_NAME"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Remove global symlink (only if it's a symlink)
if [ -L "$LINK_PATH" ]; then
    rm "$LINK_PATH"
    echo "Removed symlink $LINK_PATH"
elif [ -e "$LINK_PATH" ]; then
    echo "Warning: $LINK_PATH exists but is not a symlink, skipping"
else
    echo "No global install found at $LINK_PATH"
fi

# Remove local venv if exists
if [ -d "$SCRIPT_DIR/.venv" ]; then
    rm -rf "$SCRIPT_DIR/.venv"
    echo "Removed local .venv"
fi

echo "Uninstalled $SKILL_NAME"

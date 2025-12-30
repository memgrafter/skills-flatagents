#!/bin/bash
set -e

# --- Global Installer for shell-analyzer Claude Skill ---
SKILL_NAME="shell-analyzer"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
GLOBAL_SKILLS_DIR="$HOME/.claude/skills"

echo "Installing $SKILL_NAME globally..."

# Create global skills directory
mkdir -p "$GLOBAL_SKILLS_DIR"

# Create symlink (remove existing if present)
LINK_PATH="$GLOBAL_SKILLS_DIR/$SKILL_NAME"
if [ -L "$LINK_PATH" ] || [ -d "$LINK_PATH" ]; then
    rm -rf "$LINK_PATH"
fi
ln -s "$SCRIPT_DIR" "$LINK_PATH"

# Update SKILL.md with absolute path
sed -i.bak "s|/Users/trentrobbins/code/claude-skills-flatagents/shell_analyzer/run.sh|$SCRIPT_DIR/run.sh|g" "$SCRIPT_DIR/SKILL.md"
rm -f "$SCRIPT_DIR/SKILL.md.bak"

# Run setup
"$SCRIPT_DIR/run.sh" --setup

echo ""
echo "Installed $SKILL_NAME globally via symlink"
echo "  $LINK_PATH -> $SCRIPT_DIR"
echo ""
echo "Usage: /shell-analyzer \"your command\""

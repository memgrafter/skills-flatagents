---
name: coding-tools
description: Use this as the default toolset for coding sessions when you want faster navigation, search, file inspection, and git workflow execution with lower command overhead:
tools:
  - fzf
  - ripgrep
  - bat
  - delta
  - lazygit
  - starship
  - zoxide
  - eza
  - atuin
  - yazi
---

# Tools for Coding

Use these tools when appropriate.

**fzf**
Fuzzy-finds files, commands, branches, commits, and grep results without leaving the terminal.
Useful for jumping through large repos fast and wiring interactive selection into shell/editor scripts.

**ripgrep**
Recursively searches codebases for strings or regex matches far faster than traditional grep setups.
Best for finding symbols, TODOs, config values, and call sites across big projects.

**bat**
Displays files with syntax highlighting, line numbers, and git-aware decorations in the terminal.
Useful for quickly inspecting source files, diffs, and logs with better readability than `cat`.

**delta**
Renders git diffs and blame output with syntax highlighting and clearer side-by-side-style formatting.
Useful for reviewing code changes, understanding edits, and making CLI git output easier to parse.

**lazygit**
Provides a terminal UI for common git workflows like staging, rebasing, branching, and conflict inspection.
Useful for reducing git command overhead while keeping full repo control inside the terminal.

**starship**
Builds a fast, information-dense shell prompt showing git state, runtime versions, and environment context.
Useful for coding across many repos/languages where instant context prevents mistakes and saves time.

**zoxide**
Tracks your directory history and jumps to frequently used project folders with short fuzzy commands.
Useful for moving between repos, monorepos, and nested workspaces without repeated `cd` typing.

**eza**
Modern replacement for `ls` with better defaults, icons, git status, tree views, and clearer metadata.
Useful for scanning project structure, spotting changed files, and navigating directories more efficiently.

**atuin**
Syncs, searches, and ranks shell history so old commands are easy to recover across machines.
Useful for reusing complex build, test, deploy, and debugging commands without retyping or guessing.

**yazi**
Terminal file manager for fast keyboard-driven navigation, previews, bulk moves, and file operations.
Useful for managing project files, assets, and repo-adjacent clutter without switching to a GUI.

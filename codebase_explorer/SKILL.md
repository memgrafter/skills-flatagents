---
name: codebase-explorer
description: Explore a codebase to gather context for coding tasks. Preserves context window and offloads work to cheaper models.
---

Use this skill to gather codebase context before coding tasks. A staff architect agent explores using tree, ripgrep, and file reading, extracting imports, signatures, and code segments.

## When to use

- Before writing code that needs to understand existing patterns
- Before generating tests for existing code
- Before refactoring or modifying existing functionality
- When you need to understand how a feature is implemented

## Why use it

1. **Preserves context** - exploration happens outside main conversation
2. **Saves quota** - cheaper models do the exploration
3. **Structured output** - get imports, signatures, segments ready to use
4. **Budget-aware** - won't blow up token counts

## Usage

```bash
$HOME/.claude/skills/codebase_explorer/run.sh "<task>" [-d <directory>] [--token-budget N] [--max-iterations N]
```

## Examples

```bash
# Explore for test writing
./run.sh "Write tests for the UserService class"

# Explore specific directory
./run.sh "Understand the authentication flow" -d src/auth

# With custom budget
./run.sh "Find all API endpoints" --token-budget 20000 --max-iterations 5
```

## Output

Returns structured context:
- `summary`: narrative overview of the codebase
- `frozen_imports`: relevant import statements
- `frozen_signatures`: function/class signatures
- `frozen_segments`: code blocks with file paths
- `tree_outputs`: directory structure
- `file_contents`: full files that were read

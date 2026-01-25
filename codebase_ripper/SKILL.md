---
name: codebase-ripper
description: Shotgun codebase exploration - generates many commands, executes in parallel, extracts relevant context. Only 2 LLM calls.
---

Use this skill to quickly gather codebase context. Generates 30-80 shell commands in one LLM call, executes all in parallel, then extracts relevant context in a second LLM call.

## When to use

- Before writing code that needs to understand existing patterns
- Before generating tests for existing code
- When you need broad coverage quickly
- When you want to minimize LLM calls

## Why use it

1. **Only 2 LLM calls** - generate commands + extract context
2. **Fast** - parallel execution of all commands
3. **Secure** - command allowlist, blocked dangerous patterns
4. **Broad coverage** - 30-80 commands gather lots of context

## Usage

```bash
$HOME/.flatagents/skills/codebase_ripper/run.sh "<task>" [-d <directory>] [--token-budget N]
```

## Examples

```bash
# Quick exploration
./run.sh "Understand the authentication flow"

# Explore specific directory
./run.sh "Find all API endpoints" -d src/api

# With custom budget
./run.sh "Write tests for UserService" --token-budget 20000

# JSON output
./run.sh "Find database queries" --json
```

## Output

Returns structured context:
- `summary`: narrative overview of findings
- `frozen_imports`: relevant import statements
- `frozen_signatures`: function/class signatures
- `frozen_segments`: code blocks with file paths
- `commands_generated`: how many commands were generated
- `commands_valid`: how many passed validation
- `commands_rejected`: how many were blocked

## Security

Only allows: `tree`, `rg`, `fd`, `head`, `cat`, `wc`, `ls`

Blocks: pipes, redirects, command chaining, shell escapes, dangerous commands

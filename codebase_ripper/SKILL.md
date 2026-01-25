---
name: codebase-ripper
description: Shotgun codebase exploration with iterative passes - generates many commands, executes in parallel, extracts relevant context. Full security context for optimal command generation.
---

Use this skill to quickly gather codebase context with comprehensive coverage. Generates 30-80 shell commands per iteration with full knowledge of security rules, executes all in parallel, then extracts relevant context. Default 2 iterations for deeper exploration.

## When to use

- Before writing code that needs to understand existing patterns
- Before generating tests for existing code
- When you need broad coverage quickly
- When you want comprehensive context with minimal effort
- When exploring unfamiliar codebases

## Why use it

1. **Full context for generator** - knows allowlist, blocked patterns, security rules
2. **Iterative passes** - default 2 iterations for deeper exploration
3. **Fast** - parallel execution of all commands
4. **Secure** - command allowlist, blocked dangerous patterns
5. **Broad coverage** - 30-80 commands per iteration with history tracking
6. **Builds on findings** - each iteration learns from previous results

## Usage

```bash
$HOME/.flatagents/skills/codebase_ripper/run.sh "<task>" [-d <directory>] [--token-budget N] [--max-iterations N]
```

## Examples

```bash
# Quick exploration (2 iterations default)
./run.sh "Understand the authentication flow"

# Explore specific directory
./run.sh "Find all API endpoints" -d src/api

# Deep exploration with more iterations
./run.sh "Map out the entire data layer" --max-iterations 4

# Quick single-pass exploration
./run.sh "Get quick overview" --max-iterations 1

# With custom budget
./run.sh "Write tests for UserService" --token-budget 20000

# JSON output
./run.sh "Find database queries" --json
```

## Output

Returns structured context:
- `context`: narrative overview with key files, imports, code, and architecture notes
- `commands_generated`: total commands generated across iterations
- `commands_valid`: how many passed validation
- `commands_rejected`: how many were blocked
- `iterations`: how many exploration passes were completed
- `output_tokens`: final token count

## Generator Context

The command generator receives comprehensive context:
- **Allowlist**: All allowed commands with syntax and flag details
- **Blocked patterns**: Security rules explaining rejectable patterns
- **Initial context**: Auto-detected README, tree structure, config files
- **Previous findings**: Summary from prior iterations
- **Command history**: Accepted/rejected commands to avoid repeating mistakes

## Security

Only allows: `tree`, `rg`, `fd`, `head`, `tail`, `cat`, `wc`, `ls`, `file`, `diff`, `du`, `git` (read-only subcommands)

Blocks: pipes, redirects, command chaining, shell escapes, dangerous commands

The generator sees all security rules, producing higher-quality commands with fewer rejections.

---
name: codebase-ripper
description: Out-of-band codebase exploration using a cheap/fast model. Keeps your main context window clean while gathering broad codebase understanding. Returns a compressed summary, not raw file dumps.
---

Offload codebase exploration to a cheaper model running out-of-band. Instead of polluting your context with 30+ file reads, get back a curated summary.

## Why use it

1. **Saves your context window** - exploration happens outside your session, only the summary lands in your context
2. **Saves money** - uses a cheap/fast model for exploration, not your expensive main model
3. **Compressed output** - returns a narrative summary, not 40k tokens of raw files
4. **Broad coverage** - runs 30-80 commands in parallel per iteration, finds things you wouldn't think to look for

## When to use

- **Unfamiliar codebase** - need broad orientation before you know what to ask for
- **Long sessions** - context is precious, don't waste it on exploration
- **Exploratory questions** - "how does auth work here?" when you don't know what you're looking for yet
- **Before writing tests** - need to understand patterns across the codebase

## When NOT to use

- You already know exactly what file/function you need (just use `read`)
- The codebase is small enough to just read directly
- You need to modify code (this is read-only exploration)

## Usage

```bash
$HOME/.flatagents/skills/codebase_ripper/run.sh "<task>" [-d <directory>] [--token-budget N] [--max-iterations N]
```

## Examples

```bash
# Explore unfamiliar codebase
./run.sh "Understand the authentication flow"

# Deep exploration
./run.sh "Map out the entire data layer" --max-iterations 4

# Quick single-pass
./run.sh "Get quick overview" --max-iterations 1

# Specific directory
./run.sh "Find all API endpoints" -d src/api
```

## Output

Returns a curated `context` field - a narrative summary with key files, patterns, and architecture notes. Stats go to stderr.

## How it works

1. Cheap model generates 30-80 shell commands based on your task
2. Commands run in parallel (read-only: rg, fd, cat, git log, etc.)
3. Cheap model extracts relevant context from bulk output
4. Repeat for 2 iterations (configurable)
5. Return compressed summary to your main session

Cost: 2-4 cheap LLM calls. Benefit: keeps 40k+ tokens out of your main context.

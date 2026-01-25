---
name: codebase-ripper
description: Out-of-band codebase exploration using a cheap/fast model. Keeps your context clean while a cheap model runs 30-80 commands in parallel. Tunable precision and output size - works for broad orientation or precise targeted questions.
---

Offload exploration to a cheap model running out-of-band. Instead of polluting your context with sequential `rg` → `read` → `rg` cycles, get back a curated summary.

**Use cases:**
- "Where is the rate limiting middleware?" - you don't know the file, ripper finds it
- "What test framework does this use?" - quick pre-flight with `--max-iterations 1 --token-budget 3000`
- "How does auth work across this codebase?" - broad orientation in unfamiliar code
- "Find all external API calls and their error handling" - pattern audit across 100+ files
- Before any coding task in unfamiliar areas - parallel search beats sequential exploration

## Why use it

1. **Saves your context window** - exploration happens outside your session, only the summary lands in your context
2. **Saves money** - uses a cheap/fast model for exploration, not your expensive main model
3. **Parallel execution** - 30-80 commands per iteration beats sequential exploration
4. **Tunable output** - `--token-budget 3000` for quick checks, `40000` for deep dives
5. **Finds what you'd miss** - bulk search patterns surface things you wouldn't think to look for

## When to use

- **Any exploration that would pollute your context** - broad or narrow
- **You don't know the file location** - "where is rate limiting defined?"
- **Quick pre-flight checks** - "does this use SQLAlchemy or raw SQL?" with `--max-iterations 1 --token-budget 3000`
- **Pattern/dependency audits** - "list all external API calls and their error handling"
- **Before coding in unfamiliar areas** - even targeted questions benefit from parallel search

## When NOT to use

- You know the exact file path (just `read` it)
- Codebase is already in your context
- You need structured code artifacts for generation (use `codebase_explorer` for imports/signatures/segments)

## Usage

```bash
$HOME/.flatagents/skills/codebase_ripper/run.sh "<task>" [-d <directory>] [--token-budget N] [--max-iterations N]
```

## Examples

```bash
# Precise question, tight output
./run.sh "Find the function that validates JWT tokens" --token-budget 5000

# Quick pre-flight check
./run.sh "What test framework does this project use?" --max-iterations 1 --token-budget 3000

# Broad architectural survey
./run.sh "Map out the data layer" --max-iterations 4

# Pattern audit
./run.sh "Find all database queries and their error handling patterns" -d src/

# Targeted search when you don't know where to look
./run.sh "Where is the WebSocket connection handler?" --token-budget 8000
```

## Output

Returns a curated `context` field - summary with key files, patterns, and findings. Stats go to stderr.

## How it works

1. Cheap model generates 30-80 shell commands based on your task
2. Commands run in parallel (read-only: rg, fd, cat, git log, etc.)
3. Cheap model extracts relevant context from bulk output
4. Repeat for N iterations (default: 2)
5. Return compressed summary to your main session

Cost: 2-4 cheap LLM calls. Benefit: parallel search + clean context.

---
name: repo-map
description: "Fast, deterministic repository orientation: get a compact map of important files and symbols before deep code reading."
---

Use this skill when you need quick repo-level context and want a reliable “where to look next” map.

## Why use it

- Gives you a high-signal map of files and symbols for planning.
- Helps you choose targets before spending tokens on full file reads.
- Deterministic output makes repeated runs stable and comparable.
- No external `aider` install required in your environment.

## When to use

- Starting work in an unfamiliar repository.
- Scoping a feature, bug, or refactor across many files.
- Finding likely owners of concepts (routes, auth, handlers, models).
- Creating a first-pass plan before detailed inspection.

## When NOT to use

- You already know the exact file(s) to edit.
- You need semantic correctness from full code understanding.
- You only need a tiny local change in a well-known area.

## Usage

```bash
$HOME/.flatagents/skills/repo-map/run.sh "optional hint" -d <directory> [--map-tokens N] [--json]
```

## Examples

```bash
./run.sh "auth" -d .
./run.sh "routing and handlers" -d src --map-tokens 3000
./run.sh "" -d /path/to/repo --json
```

## Output

Returns:
- `repo-map`: ranked tree-like map text
- `file_count`: number of scanned source files
- `map_tokens`: token budget used for map generation
- `refresh`: refresh policy applied
- `error`: non-empty if map generation failed

## How it works

This skill calls a vendored Aider `repomap` implementation to build a compact structural map from repository files and optional hint text.

Trade-off: you get fast, broad orientation (benefit) but not full semantic understanding of every code path (cost).

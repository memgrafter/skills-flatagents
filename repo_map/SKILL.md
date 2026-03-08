---
name: repo-map
description: Deterministic repository map generation using Aider's repo map implementation vendored locally.
---

Use this skill to generate a compact map of key files and symbols in a repository, without installing `aider`.

## Usage

```bash
$HOME/.flatagents/skills/repo_map/run.sh "optional hint" -d <directory> [--map-tokens N] [--json]
```

## Examples

```bash
./run.sh "auth" -d .
./run.sh "routing and handlers" -d src --map-tokens 3000
./run.sh "" -d /path/to/repo --json
```

## Output

Returns:
- `repo_map`: ranked tree-like map text
- `file_count`: number of scanned source files
- `error`: non-empty if map generation failed

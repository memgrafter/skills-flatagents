---
name: test-writer
description: Write tests to reach a coverage target. Uses 4 agents (analyzer, writer, checker, fixer) to iteratively generate and fix tests. Exits non-zero with explanation if production code needs changes.
---

Run to generate tests for a Python file or project:

```bash
/Users/trentrobbins/code/claude-skills-flatagents/test_writer/run.sh "<target>"
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--target=N` | Coverage percentage to reach | 80 |
| `--max-rounds=N` | Max test generation rounds | 3 |

## Examples

```bash
# Cover a specific file to 80%
run.sh src/mymodule.py

# Cover entire project to 90%
run.sh --target=90 .

# Cover specific file to 95%
run.sh --target=95 src/utils.py
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - coverage target met |
| 1 | Production code likely has a bug (explanation provided) |
| 2 | Max iterations reached, tests still failing |

---
name: shell-analyzer
description: Run shell commands and analyze output with validated summaries. Use for build logs, test output, or any command with substantial output. Protects context by returning concise summaries with grep-validated citations.
---

Run immediately with the shell command to execute:

```bash
$HOME/.claude/skills/shell_analyzer/run.sh "<command>"
```

## Output Styles

Use `--style=<style>` to control output verbosity:

| Style | Description | Use Case |
|-------|-------------|----------|
| `compact` | Brief summary + key findings (default) | General use |
| `minimal` | Single line status | Quick checks |
| `detailed` | Full markdown sections | Debug/investigation |
| `errors-only` | Only output if problems found | CI/build monitoring |

### Examples

```bash
# Default compact style
run.sh "npm run build"

# Minimal - just pass/fail
run.sh --style=minimal "cargo test"

# Detailed - full analysis
run.sh --style=detailed "pytest -v"

# Errors only - silent on success
run.sh --style=errors-only "make check"
```

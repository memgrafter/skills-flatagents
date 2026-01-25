# Codebase Ripper

Shotgun approach to codebase exploration with iterative passes:

1. **Gather context** (0 LLM) - tree, README, config files
2. **Generate commands** (1 LLM/iter) - 30-80 commands based on task + structure + security rules
3. **Validate** (0 LLM) - filter against allowlist
4. **Execute in parallel** (0 LLM) - fast bulk execution
5. **Extract relevant context** (1 LLM/iter) - picks the good stuff, builds on previous findings

**Default: 2 iterations** for comprehensive coverage.

## Usage

```bash
./run.sh "understand how the auth system works" -d /path/to/project
./run.sh "find all database queries" --max-iterations 3 --json
./run.sh "explore the API layer" --max-iterations 1 --token-budget 20000
```

## Architecture

```
start → get_structure → get_allowlist → get_blocked_patterns → get_initial_context
                                                                      ↓
                    ┌─────────────────────────────────────────────────────┐
                    │              ITERATION LOOP (default: 2)             │
                    │  generate (LLM) → validate → execute → extract (LLM) │
                    │       ↑                                      │        │
                    │       └──── prepare_iteration ←──────────────┘        │
                    └─────────────────────────────────────────────────────┘
                                                ↓
                                            finalize
```

### Key Files

- `machine.yml` - State flow with iteration loop
- `src/codebase_ripper/hooks.py` - Allowlist, validation, parallel execution
- `agents/generator.yml` - Generates command list with full security context
- `agents/extractor.yml` - Extracts relevant context with iteration awareness

## Command Allowlist

| Command | Description |
|---------|-------------|
| `tree` | Directory structure |
| `rg` | Ripgrep content search |
| `fd` | Find files by name |
| `head` | First N lines |
| `tail` | Last N lines |
| `cat` | Full file contents |
| `wc` | Line/word/char counts |
| `ls` | Directory listing |
| `file` | File type detection |
| `diff` | Compare files |
| `du` | Disk usage |
| `git` | Read-only git commands |

### Git Commands

**Subcommands:** `status`, `log`, `diff`, `show`, `ls-files`, `blame`, `describe`, `rev-parse`, `shortlog`

**List-only:** `remote`, `branch`, `tag` (flags only, no arguments)

**Examples:**
```bash
git log --oneline -20
git log --format='%h %s' -10
git shortlog -sn
git diff HEAD~1 --name-only
git blame -L 1,30 src/core.py
git ls-files '*.py'
```

## Security

### Blocked Patterns
- Command substitution: `$()`, backticks
- Chaining: `|`, `;`, `&&`, `||`
- Redirects: `>`, `<`
- Dangerous commands: `sudo`, `rm`, `mv`, `cp`, `chmod`, `chown`, `curl`, `wget`, `nc`, `eval`, `exec`
- Path escapes: `..`, `~` (standalone; `~` allowed in git refs like `HEAD~1`)
- Environment: `$VAR`, `${VAR}`, `export`, `source`

### Validation
1. Check against blocked patterns
2. Verify command in allowlist
3. Verify flags in allowed flags list

## Configuration

```python
# hooks.py constants
MAX_COMMANDS = 100           # Per iteration
MAX_OUTPUT_PER_COMMAND = 10000
MAX_TOTAL_OUTPUT = 200000
COMMAND_TIMEOUT = 30
MAX_PARALLEL = 10
```

### CLI Options

```bash
./run.sh TASK [OPTIONS]

Options:
  -d, --directory DIR    Working directory (default: .)
  --token-budget N       Max tokens for extraction (default: 40000)
  --max-iterations N     Max exploration iterations (default: 2)
  --json                 Output as JSON
```


# Codebase Ripper

Shotgun approach to codebase exploration with iterative passes. Instead of single-pass LLM-guided exploration, this tool:

1. **Gathers initial context** (0 LLM calls) - tree structure, README, config files
2. **Generates many commands** (1 LLM call per iteration) - 30-80 commands based on task + structure + security rules
3. **Validates against allowlist** (0 LLM calls) - security filtering with full context
4. **Executes all in parallel** (0 LLM calls) - fast bulk execution  
5. **Extracts relevant context** (1 LLM call per iteration) - picks the good stuff, builds on previous findings

**Default: 2 iterations** for comprehensive coverage with deeper exploration.

## Usage

```bash
./run.sh "understand how the auth system works" -d /path/to/project
./run.sh "find all database queries" --max-iterations 3 --json
./run.sh "explore the API layer" --max-iterations 1 --token-budget 20000
```

## Architecture

### Flow (with iterative passes)

```
start → get_structure → get_allowlist → get_blocked_patterns → get_initial_context
                                                                      ↓
                           ┌──────────────────────────────────────────┘
                           ↓
                    ┌─────────────────────────────────────────────────────┐
                    │              ITERATION LOOP (default: 2)             │
                    │                                                       │
                    │  generate (LLM) → validate → execute → extract (LLM) │
                    │       ↑                                      │        │
                    │       └──── prepare_iteration ←──────────────┘        │
                    └─────────────────────────────────────────────────────┘
                                                ↓
                                            finalize
```

Each iteration:
1. **generate** - LLM produces 30-80 commands based on task + structure + previous findings (1 LLM call)
2. **validate** - Filter commands against allowlist, block dangerous patterns (no LLM)
3. **execute** - Run all valid commands in parallel with ThreadPoolExecutor (no LLM)
4. **extract** - LLM picks relevant context, avoiding duplicates from previous iterations (1 LLM call)

### Generator Context

The command generator receives full context including:
- **Allowlist** - Complete list of allowed commands with syntax and examples
- **Blocked patterns** - Security rules explaining what patterns are rejected
- **Initial context** - Tree structure, README, config files (auto-detected)
- **Previous findings** - Summary from previous iterations
- **Accepted/rejected commands** - History to avoid repeating rejected patterns

### Key Files

- `machine.yml` - State flow with iteration loop
- `src/codebase_ripper/hooks.py` - Allowlist, validation, parallel execution, iteration tracking
- `agents/generator.yml` - Generates command list with full security context
- `agents/extractor.yml` - Extracts relevant context with iteration awareness

## Command Allowlist

Only these commands are allowed (with restricted flags):

| Command | Description | Allowed Flags |
|---------|-------------|---------------|
| `tree` | Directory structure | `-L`, `-d`, `-I`, `--noreport`, `-a`, `-f`, `-P` |
| `rg` | Ripgrep content search | `-i`, `-w`, `-l`, `-c`, `-n`, `-A`, `-B`, `-C`, `-t`, `-g`, `-e`, `-m`, `-o`, etc. |
| `fd` | Find files by name | `-e`, `-t`, `-d`, `-H`, `-I`, `-g`, `-a` |
| `head` | First N lines of file | `-n`, `-c` |
| `cat` | Full file contents | `-n` |
| `wc` | Line/word counts | `-l`, `-w`, `-c` |
| `ls` | Directory listing | `-l`, `-a`, `-h`, `-R`, `-1`, `-S`, `-t` |

## Security

Commands are validated against:

### Blocked Patterns
- Command substitution: `$()`, backticks
- Chaining: `|`, `;`, `&&`, `||`
- Redirects: `>`, `<`
- Dangerous commands: `sudo`, `rm`, `mv`, `cp`, `chmod`, `chown`, `curl`, `wget`, `nc`, `eval`, `exec`
- Path escapes: `..`, `~`
- Environment: `$VAR`, `${VAR}`, `export`, `source`

### Validation Process
1. Check command against blocked patterns regex
2. Verify base command is in allowlist
3. Verify all flags are in allowed flags list
4. Only then execute

**The generator now sees all these rules**, reducing rejected commands and improving command quality.

## Output Format

```
## Summary
Brief description of what was found

## Key Files
Important files with descriptions

## Imports & Dependencies
  import relevant_module
  from package import thing

## Relevant Code
### path/to/file.py
```
relevant code snippet
```

## Architecture Notes
How things connect, patterns used

---
Iterations: 2
Commands: 100 generated, 90 valid, 10 rejected
Output tokens: 15000
```

## Comparison to codebase_explorer

| Aspect | codebase_explorer | codebase_ripper |
|--------|-------------------|-----------------|
| LLM calls | 4-8 per iteration | 2 per iteration |
| Default iterations | 2 | 2 |
| Approach | Iterative, guided, selective | Bulk, filtered, comprehensive |
| Speed | Slower per command | Faster (parallel execution) |
| Coverage | Deeper on fewer paths | Broader coverage |
| Generator context | Task + structure | Task + structure + allowlist + blocked patterns + initial context + history |
| Best for | Complex understanding | Quick broad context gathering |

## Configuration

### Hooks Constants (in hooks.py)

```python
MAX_COMMANDS = 100          # Max commands to process per iteration
MAX_OUTPUT_PER_COMMAND = 10000   # Chars per command output
MAX_TOTAL_OUTPUT = 200000   # Total aggregated chars
COMMAND_TIMEOUT = 30        # Seconds per command
MAX_PARALLEL = 10           # Parallel execution threads
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

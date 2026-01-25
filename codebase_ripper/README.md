# Codebase Ripper

Shotgun approach to codebase exploration. Instead of iterative LLM-guided exploration, this tool:

1. **Generates many commands** (1 LLM call) - 30-80 commands based on task + structure
2. **Validates against allowlist** (0 LLM calls) - security filtering
3. **Executes all in parallel** (0 LLM calls) - fast bulk execution  
4. **Extracts relevant context** (1 LLM call) - picks the good stuff

**Total: 2 LLM calls** for comprehensive coverage.

## Usage

```bash
./run.sh "understand how the auth system works" -d /path/to/project
./run.sh "find all database queries" --json
```

## Architecture

### Flow (6 states, 2 LLM calls)

```
start → get_structure → get_allowlist → generate (LLM) → validate → execute → aggregate → extract (LLM) → finalize
```

1. **get_structure** - Runs `tree -L 2` to get initial layout (no LLM)
2. **generate** - LLM produces 30-80 commands based on task + structure (1 LLM call)
3. **validate** - Filter commands against allowlist, block dangerous patterns (no LLM)
4. **execute** - Run all valid commands in parallel with ThreadPoolExecutor (no LLM)
5. **aggregate** - Combine all outputs into single string for LLM (no LLM)
6. **extract** - LLM picks relevant imports/signatures/segments from bulk output (1 LLM call)

### Key Files

- `machine.yml` - Simple 6-state flow definition
- `src/codebase_ripper/hooks.py` - Allowlist, validation, parallel execution
- `agents/generator.yml` - Generates command list from task + structure
- `agents/extractor.yml` - Extracts relevant context from bulk output

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

## Output Format

```
## Summary
Brief description of what was found

## Imports
  import relevant_module
  from package import thing

## Signatures
  file.py:10 - def function_name(args)
  file.py:25 - class ClassName

## Code Segments
### path/to/file.py
```
relevant code snippet
```

---
Commands: 50 generated, 45 valid, 5 rejected
Output: 12000 tokens
Extracted: 8 imports, 12 signatures, 5 segments
```

## Comparison to codebase_explorer

| Aspect | codebase_explorer | codebase_ripper |
|--------|-------------------|-----------------|
| LLM calls | 4-8 per iteration (default 2 iterations = 8-16 calls) | 2 total |
| Approach | Iterative, guided | Bulk, filtered |
| Speed | Slower | Faster |
| Coverage | Deeper on fewer paths | Broader, shallower |
| Best for | Complex understanding | Quick context gathering |

## Configuration

### Hooks Constants (in hooks.py)

```python
MAX_COMMANDS = 100          # Max commands to process
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
  --json                 Output as JSON
```

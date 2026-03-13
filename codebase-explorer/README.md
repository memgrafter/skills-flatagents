# Codebase Explorer

Budget-aware codebase exploration that gathers context for coding tasks.

## How It Works

A staff architect agent explores the codebase using:
- **tree**: discover directory structure
- **ripgrep**: search code for patterns
- **read**: read full file contents

The exploration extracts structured data:
- Import statements (verbatim)
- Function/class signatures (verbatim)
- Code segments (verbatim with file paths)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Machine Context                          │
│  MUTABLE: summary (narrative)                                   │
│  FROZEN: imports, signatures, segments (append-only)            │
│  TOKENS: tracked with budget projection                         │
└─────────────────────────────────────────────────────────────────┘
          │                              ▲
          │ summary + counts             │ decision
          ▼                              │
┌─────────────────────────────────────────────────────────────────┐
│                     Judge Agent (ephemeral)                     │
│  Staff architect with budget awareness                          │
│  Decides: tree, rg, read, remove, or done                       │
└─────────────────────────────────────────────────────────────────┘
          │
          ├──▶ tree/rg/read actions (hooks)
          │
          ├──▶ Extractor Agent (verbatim extraction → frozen)
          │
          └──▶ Summarizer Agent (narrative update → mutable)
```

## Two-Pass Removal

The judge can request removal of frozen items to save budget:

1. Judge requests removal
2. Hook removes items, stashes backup
3. Confirmation agent reviews what was removed
4. If rejected, items are restored from stash

## Budget Pressure

The judge sees:
- Current frozen token count
- Burn rate (tokens per iteration)
- Projected overage

Framing: "Too many tokens = team runs out of budget. Too aggressive pruning = fail to deliver."

## Usage

```bash
# Explore current directory
./run.sh "Write tests for the auth module"

# Explore specific directory with custom budget
./run.sh "Understand the API layer" -d src/api --token-budget 30000

# Get JSON output
./run.sh "Find database queries" --json
```

## Files

| File | Purpose |
|------|---------|
| `machine.yml` | State machine orchestration |
| `agents/judge.yml` | Staff architect - directs exploration |
| `agents/judge_confirm.yml` | Two-pass removal confirmation |
| `agents/extractor.yml` | Verbatim data extraction |
| `agents/summarizer.yml` | Narrative summary updates |
| `src/codebase_explorer/hooks.py` | Shell execution, token counting |
| `src/codebase_explorer/main.py` | CLI entry point |

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `--token-budget` | 40000 | Max tokens for frozen context |
| `--max-iterations` | 10 | Max exploration iterations |
| `-d, --directory` | `.` | Working directory to explore |
| `--json` | false | Output as JSON |

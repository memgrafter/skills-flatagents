# Coding Agent Improvements

## Replace env var approval with CLI flags

Currently, approval decisions are passed via environment variables:

```bash
CODING_AGENT_APPROVAL_PLAN=approved bash run.sh --cwd /path --claude
CODING_AGENT_APPROVAL_RESULT=approved bash run.sh --cwd /path --claude
```

Problems:
- Hidden state - not visible in the command
- Pollution risk if not cleared properly
- Not self-documenting

Better approach - CLI flags:

```bash
bash run.sh --cwd /path --claude --approve-plan
bash run.sh --cwd /path --claude --approve-result
bash run.sh --cwd /path --claude --plan-feedback "make it simpler"
bash run.sh --cwd /path --claude --result-feedback "fix the tests"
```

Implementation:
1. Add argparse arguments in `main()`:
   - `--approve-plan` (store_true)
   - `--approve-result` (store_true)
   - `--plan-feedback` (str)
   - `--result-feedback` (str)
2. Pass decisions to `run()` as parameters
3. Have `run()` pass them to hooks constructor or set them before execution
4. Remove env var checking from `claude_hooks.py`

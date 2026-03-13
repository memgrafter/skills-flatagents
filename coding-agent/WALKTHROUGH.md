# Coding Agent Walkthrough

## What Was Built

A state-of-the-art AI coding agent example in `sdk/examples/coding_agent/` with:

- **OODA Loop**: Explore → Plan → [Human Review] → Execute → Verify → [Human Review] → Done
- **Skills Architecture**: OpenSkills-compatible with tools manifest
- **History Preservation**: Rejected plans/changes saved so agents learn from feedback

## File Structure

```
coding_agent/
├── SKILL.md                    # OpenSkills manifest
├── README.md                   # Usage documentation
├── .gitignore
├── config/
│   ├── machine.yml             # OODA loop orchestration
│   ├── tools.yml               # MCP + shell permissions
│   └── agents/
│       ├── planner.yml         # Generates implementation plan
│       ├── coder.yml           # Implements changes
│       └── reviewer.yml        # Reviews before human approval
└── python/
    ├── pyproject.toml
    ├── run.sh
    └── src/coding_agent/
        ├── __init__.py
        ├── main.py             # CLI entry point
        └── hooks.py            # Human-in-the-loop with history
```

## Key Design Decisions

### 1. History Preservation on Reject
Context includes `plan_history` and `changes_history` arrays. When human rejects, the work is saved with feedback:

```python
# In hooks.py
plan_history.append({
    "content": plan,
    "feedback": response
})
```

Agents receive this history and learn from rejected attempts.

### 2. Skills Symlink (Corrected)
Skills are symlinked from a specific path, not `~/code`:

```bash
ln -s /path/to/your/skills .skills
```

### 3. Tools Manifest
`tools.yml` provides declarative config for:
- MCP servers (filesystem placeholder)
- Shell auto-approve patterns (ls, cat, grep, etc.)
- Skills directory path

## Usage

```bash
cd sdk/examples/coding_agent/python
./run.sh --local "Create a hello world function" --cwd /tmp/test
```

## Next Steps

- Add MCP filesystem integration in hooks
- Test with Claude API key
- Add skill invocation support

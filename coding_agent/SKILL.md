---
name: coding-agent
description: AI coding agent that plans, implements, and verifies code changes with human approval gates. Built on FlatAgents.
---

# Coding Agent

An agentic coding assistant with human-in-the-loop review.

## Workflow

1. **Explore** — Gathers codebase context
2. **Plan** — Generates implementation plan → human reviews
3. **Execute** — Implements changes
4. **Verify** — Reviews changes → human approves
5. **Apply** — Writes changes to files

## Invocation

```bash
$HOME/.flatagents/skills/coding_agent/run.sh "<task>" --cwd "<working_directory>" --claude
```

---

## Claude Code Integration

When running as a Claude Code skill, use the `--claude` flag. This enables a checkpoint/exit approval flow instead of interactive `input()` prompts.

### Approval Gates

This agent requires human approval at two points:
- **Plan review** - Before implementing changes
- **Result review** - Before applying changes to files

### Exit Code 2: Approval Needed

When the agent needs approval, it:
1. Writes approval request to **stderr** starting with `APPROVAL_NEEDED: <type>` (where type is `plan` or `result`)
2. Saves state to `.coding_agent_checkpoint.json`
3. Exits with **code 2**

### Handling Approval

When you see exit code 2:

1. Parse stderr to find `APPROVAL_NEEDED: plan` or `APPROVAL_NEEDED: result`
2. Display the content from stderr to the user
3. Use `AskUserQuestion` to ask the user to approve or provide feedback
4. Resume with the decision:

```bash
# Approve plan
CODING_AGENT_APPROVAL_PLAN=approved $HOME/.flatagents/skills/coding_agent/run.sh "<task>" --cwd "<dir>" --claude

# Reject plan with feedback
CODING_AGENT_APPROVAL_PLAN="<user feedback here>" $HOME/.flatagents/skills/coding_agent/run.sh "<task>" --cwd "<dir>" --claude

# Approve result
CODING_AGENT_APPROVAL_RESULT=approved $HOME/.flatagents/skills/coding_agent/run.sh "<task>" --cwd "<dir>" --claude
```

The agent restores state from the checkpoint file and continues from where it paused.

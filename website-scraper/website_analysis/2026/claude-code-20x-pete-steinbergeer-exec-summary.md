# Executive Summary — Vibe Coding vs Agentic Engineering (Peter Steinberger)

Peter Steinberger’s core argument is that “vibe coding” alone doesn’t scale, but Agentic Engineering does: using LLMs with disciplined engineering
practices (specs, context control, tests, and review) to build and maintain serious software faster.

### 1) Main Thesis

- AI coding tools are most powerful when treated as engineering multipliers, not autopilot.
- The winning pattern is not “accept everything,” but a structured loop:
spec → implement → validate → refine.
- Done right, this can produce large productivity gains (he frames it as 10–20x+ in many workflows).

### 2) Key Workflow He Recommends

- Start with a strong spec (often conversationally drafted first).
- Keep project instructions in a CLAUDE.md (how to build, run, test, debug).
- Give the model focused context; avoid bloated threads.
- Use parallel tasks/worktrees for independent work.
- For hard decisions, cross-check with another model/tool.
- Keep human attention on architecture, product decisions, and quality gates.

### 3) Big Concept: Context Engineering > Prompt Tricks

- He emphasizes context quality as the biggest determinant of output quality.
- Keep only relevant docs/rules in context.
- Reset/fork context when tasks diverge.
- Store critical conventions/docs in-repo as markdown so the agent can reliably use them.

### 4) Tools & Practicality

- Prefers CLI/agent workflows over pure IDE chat for deeper autonomous loops.
- Uses MCP selectively (only when it materially helps, e.g., browser automation).
- Avoids tool chains that add latency and “round-trip drag.”

### 5) Testing & Reliability

- With agents, tests become more important, not less.
- Manually curated critical tests + iterative regression tests are key.
- Don’t trust generated code blindly—review and enforce constraints with tests.

### 6) Cost/ROI Position

- He argues the economics are favorable for most developers/teams:
subscription/API costs are small relative to developer time saved.
- For heavy users, he treats model spend as easily justified by output gain.

### 7) Mindset Shift

- Move from “I write every line” to “I design systems and supervise execution.”
- This is less about replacing developers and more about upgrading capable developers into faster builders across more stacks.

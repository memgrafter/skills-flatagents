  PKM Flatmachine Plan

  Goal: Create a simplified flatmachine for PKM that edits markdown files and uses git diffs for review
  (no approval gates).

  Phase 1: Copy & Simplify Structure

  1. Copy ~/code/skills-flatagents/coding-agent to new location (e.g.,
  ~/code/skills-flatagents/pkm_agent)
  2. Keep only essential files:
    - machine.yml (simplified)
    - agents/ folder (will have pkm-specific agent)
    - tools.yml
    - profiles.yml

  Phase 2: Simplify machine.yml

  - Remove approval states (review_plan, review_result)
  - Remove reviewer agent
  - Simplify flow: explore → plan → execute → done
  - Point machines.explorer to ~/.flatmachines/skills/codebase-explorer/machine.yml
  - Remove checkpoint/resume complexity

  Phase 3: Create PKM-specific agent prompt

  - Replace coder/planner with single pkm_writer.yml agent
  - Use the PKM prompt style from aider (imperative mood, markdown-focused)
  - Focus on: notes, journal entries, knowledge organization

  Phase 4: Iterate

  - Run it, see what breaks
  - Use git diff to review changes
  - Tweak prompts based on results



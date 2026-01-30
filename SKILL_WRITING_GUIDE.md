# Skill Writing Guide

How to write SKILL.md so the LLM actually wants to use your skill.

## The Problem

You built a useful skill. The LLM ignores it because:
1. The description doesn't explain *why* to use it
2. It reads like implementation docs, not decision-making info
3. The value prop is buried under "how it works"

## The Fix

### Front Matter Description (Most Important)

This is what the LLM sees first. Lead with the value, not the mechanism.

**Bad:**
```yaml
description: Generates shell commands, executes in parallel, extracts context with iterative passes.
```

**Good:**
```yaml
description: Out-of-band codebase exploration using a cheap model. Keeps your main context clean while gathering broad understanding.
```

### Structure

```markdown
---
name: skill-name
description: [VALUE PROP - why use this, not how it works]
---

[One sentence reinforcing the value prop]

## Why use it

[Benefits in order of importance to the LLM's decision]

## When to use

[Specific situations where this is the right choice]

## When NOT to use

[Be honest - builds trust, prevents misuse]

## Usage

[Command/API examples]

## Examples

[Copy-paste ready examples]

## Output

[What comes back - keep brief]

## How it works

[Optional - keep short, end with the trade-off summary]
```

### Key Principles

1. **Lead with why, not how** - The LLM needs to decide whether to use it, not understand the implementation

2. **Be honest about trade-offs** - "When NOT to use" builds trust and prevents the LLM from using it wrong

3. **Frame benefits from the LLM's perspective** - "Saves your context window" matters more than "runs 80 commands in parallel"

4. **Cut implementation details** - Security models, internal architecture, generator context - move to README.md if needed

5. **End with the trade-off** - "Cost: X. Benefit: Y." makes the decision easy

### The Test

Read your SKILL.md and ask: "Does this help me decide *whether* to use it, or does it explain *how* it works?"

If it's mostly "how", rewrite it.

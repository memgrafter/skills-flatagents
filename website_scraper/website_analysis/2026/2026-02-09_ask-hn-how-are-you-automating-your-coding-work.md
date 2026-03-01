---
url: https://news.ycombinator.com/item?id=46710108
title: 'Ask HN: How are you automating your coding work?'
scraped_at: '2026-02-09T06:34:32.523411+00:00'
word_count: 4402
raw_file: raw/2026-02-09_ask-hn-how-are-you-automating-your-coding-work.txt
tldr: Experienced developers share practical patterns for AI-assisted coding, emphasizing "codification" (turning prompts
  into executable scripts), staying in the loop on architecture decisions, and knowing when to stop arguing with AI and just
  fix things manually.
key_quote: Maybe one should just search for advice from the last 20 years on how to make a human development team more effective,
  and do that stuff. It's funny how this advice has always been around, but we needed to invent this new kind of idiot savant
  developer to get the human developers to want to do it…
durability: medium
content_type: mixed
density: medium
originality: commentary
reference_style: skim-once
scrape_quality: good
people: []
tools:
- claude-code
- cursor
- copilot-cli
- openrouter
- agentbox
libraries:
- pytest
- playwright
- uv
companies: []
tags:
- ai-assisted-coding
- llm-workflows
- software-development
- developer-tools
- codification
---

### TL;DR
Experienced developers share practical patterns for AI-assisted coding, emphasizing "codification" (turning prompts into executable scripts), staying in the loop on architecture decisions, and knowing when to stop arguing with AI and just fix things manually.

### Key Quote
"Maybe one should just search for advice from the last 20 years on how to make a human development team more effective, and do that stuff. It's funny how this advice has always been around, but we needed to invent this new kind of idiot savant developer to get the human developers to want to do it…"

### Summary
**Core concept: Codification**
- Instead of keeping principles in `skill.md` files that consume context, have the model generate executable scripts that enforce those principles
- Scripts can check code in milliseconds with zero token cost
- TDD is a form of codification—enforcing 10ms timeouts on unit tests prevents I/O and enables fast parallel test execution

**Popular tools mentioned**
- Claude Code (web version) - most frequently praised
- Cursor with Claude models
- Copilot CLI
- Custom setups using OpenRouter, agentbox

**Workflow patterns that work**
- High-level description → let AI scaffold → read and course-correct
- Use AI for tedious work: edge case tests, refactoring across files, boilerplate
- Keep humans in the loop on architecture decisions
- Use AI as a pair reviewer: ask "is it safe to pass null here?", "can this function panic?"

**Project setup best practices**
- Ensure `uv run pytest` (or equivalent) works cleanly
- Maintain `CLAUDE.md`, `AGENTS.md`, `SKILLS.md` files describing the project
- Use templates for Python libraries, CLI tools, Datasette plugins
- Put major dependencies in `_vendor` directory for AI to explore

**Common pitfalls**
- Not knowing when to quit—arguing with AI when manual fixes would be faster
- Blindly accepting generated code creates technical debt faster than imaginable
- AI often doesn't integrate well with existing code conventions
- AI-generated tests often lack depth and miss edge cases
- Context rot from bloated codebases

**Code review burden**
- Maintainers report spending more time reviewing AI-generated PRs
- AI rewrites existing functionality instead of reusing it
- Developers accept AI-generated tests without investigation

### Assessment
**Durability**: Medium. The tools mentioned (Claude Code, Cursor) will evolve, but the workflow patterns—codification, staying in the loop, knowing when to quit—are durable concepts.

**Content type**: Mixed. Primarily community-sourced tips and opinions, with some reference patterns for AI-assisted development.

**Density**: Medium. A long thread with genuine insights interspersed with lighter comments and tangential discussions.

**Originality**: Commentary. This is a community discussion synthesizing real-world experiences rather than primary research or documentation.

**Reference style**: Skim-once. Useful for extracting patterns and mental models, not something to refer back to repeatedly.

**Scrape quality**: Good. The conversation flow is intact with usernames and threading implied. No code blocks or images appear to be missing.
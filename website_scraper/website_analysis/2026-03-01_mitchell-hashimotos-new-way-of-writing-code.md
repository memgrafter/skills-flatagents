---
url: https://www.youtube.com/watch?v=WjckELpzLOU
title: Mitchell Hashimoto's new way of writing code
scraped_at: '2026-03-01T03:53:46.494582+00:00'
word_count: 25225
raw_file: 2026-03-01_mitchell-hashimotos-new-way-of-writing-code.txt
tldr: Mitchell Hashimoto shares his AI workflow (always have an agent running), the HashiCorp origin story, honest cloud provider takes, why open source must move to default-deny trust, and why git may not survive the agentic era unchanged.
key_quote: "I endeavor to always have an agent doing something at all times... if I'm coding, I want an agent planning. If they're coding, I want to be reviewing."
durability: high
content_type: interview
density: high
originality: primary
reference_style: reference-often
scrape_quality: good
people:
- Mitchell Hashimoto
- Armon Dadgar
- Gergely Orosz
tools:
- Claude Code
- AMP
- Codex
- Deep Research
- Terraform
- Vagrant
- Packer
- Consul
- Vault
- Nomad
- Ghostty
- Git
libraries:
- libghostty
- Zig
companies:
- HashiCorp
- AWS
- Microsoft
- Google Cloud
- VMware
- Cursor
- Anthropic
tags:
- ai-workflow
- agentic-coding
- open-source-policy
- startup-advice
- infrastructure
- cloud-providers
- harness-engineering
- git-future
- hiring
---

### TL;DR
Mitchell Hashimoto shares his AI workflow (always have an agent running), the HashiCorp origin story, honest cloud provider takes, why open source must move to default-deny trust, and why git may not survive the agentic era unchanged.

### Key Quote
"I endeavor to always have an agent doing something at all times... if I'm coding, I want an agent planning. If they're coding, I want to be reviewing."

### Summary

#### 🔑 Top Actionables (including drive-bys)

**AI Workflow — Do These Now**

1. **Always have an agent running.** Mitchell's #1 rule: if you're coding, an agent should be planning. If the agent is coding, you should be reviewing. Never let the agent sit idle during working hours.
2. **Use boundary time.** Before leaving your desk, driving, or stepping away — spend 30 min asking: *"What slow task could my agent do while I'm gone?"* (research, library evaluation, edge-case analysis, ecosystem mapping).
3. **Turn off agent notifications.** You interrupt the agent, not the other way around. Desktop notifications from agent tools are "a mistake."
4. **Reproduce your work with an agent first.** Best onboarding advice for AI-skeptics: don't have it write code — have it reproduce the *research* portion of your work. Then expand from there.
5. **Force yourself to learn prompting even when you don't believe yet.** Mitchell deliberately doubled his work for weeks — doing tasks manually AND via agent — until he found the patterns (separate planning step, better test harness, agents.md for recurring mistakes).
6. **Build harness engineering, not just tests.** Anytime an agent does something wrong, build tooling it can call to prevent/course-correct that mistake. This is the new meta-skill: "harness engineering."
7. **Run agents in competition.** For harder tasks, run Claude vs Codex (or similar) on the same problem. Don't run more than 2 concurrently — cleanup isn't fun.

**Open Source — The New Reality**

8. **Default deny, not default allow.** Open source's trust model is broken by AI. Mitchell is moving Ghostty to a **vouching system** (inspired by Lobsters and pi): you can't open a PR unless an existing community member vouches for you. Bad actors get their entire invitation tree banned.
9. **Effort-for-effort reciprocity.** If a contributor put in hours, put in hours reviewing. If they put in minutes (AI slop), close it in minutes. Don't feel guilty.
10. **Fork more.** Mitchell has been a proponent of more forking for 10+ years. With AI making contributions cheap, forking becomes the correct outlet — not demanding merges into upstream.
11. **AI PRs have a dead giveaway.** Claude opens a draft PR with no body → edits body → reopens. Happens in <1 minute. No human does this.

**Git & Infrastructure — Brewing Changes**

12. **Git may not survive the agentic era unchanged.** First time in 12-15 years anyone asks "will Git be around?" without laughing. Merge queues break at 10-100x human churn. Branch/PR workflows don't capture failed experiments (negative signal). Watch this space.
13. **"Gmail moment" for version control.** We should stop curating/deleting branches and instead keep everything — with better tooling to find relevant context. Prompt history may matter more than diffs.
14. **Container/sandbox scale is slope-changing upward.** Agent sandboxes are driving non-production compute demand way beyond what Kubernetes/Docker were engineered for.

**Startup & Career Wisdom**

15. **Imagine 10 years, not 5.** Startups take longer than you think. You need enough hubris to believe you'll do it better than anyone else, but not so much you're blind to change.
16. **Corporate buyers don't care about open source.** They need commercial agreements, support, POCs, white papers. The open-source-ness is irrelevant to the purchase decision.
17. **Know whose budget pays.** HashiCorp's first commercial product (Atlas) failed because it spanned multiple buying orgs — security, networking, infrastructure, dev tooling all pointed at each other. Per-product enterprise (Vault first) fixed this instantly.
18. **Listen to your customers — they're screaming.** HashiCorp was pitching "adopt all products" while customers kept asking about secrets replication. The answer was right in front of them.
19. **The best engineers are boringly private.** No social media, no GitHub profile, 9-to-5, zero public contributions. They context-switch the least and think the deepest. Don't filter them out in hiring.
20. **Constraints create better software.** Mitchell built Vagrant on VirtualBox because he was broke. He couldn't afford EC2. The constraint forced a better design.

**Cloud Provider Takes (circa ~2019)**

- **AWS:** Arrogant, "doing you a favor" vibe, implicit threat of building competing services, last to help with Terraform provider (HashiCorp had 5 full-time engineers on AWS provider at ~$1M/year with zero help until they threatened to deprecate it).
- **Microsoft/Azure:** Hairy/complex technically, but best business partners — "How do we both win?" was their opening question. First to support Terraform.
- **Google Cloud:** Best technology by far, fully automated Terraform provider generation, but zero business awareness. Could talk edge cases for hours, crickets when discussing co-sell or quota attribution.

**Misc Drive-Bys**

- **Pre-plan airplane work into 15-minute chunks.** No task should need flow state. Bug fixes only. Pre-sort issues on the ground.
- **Terminal usage went UP because of AI** — counter-intuitive but true. CLI agents, docker builds, pseudo-terminals everywhere.
- **Proof of concepts should be slop.** "Ship slop" for demos/POCs you'll throw away. Save craftsmanship for production. This is why AI-generated PRs to open source are unacceptable but AI-generated prototypes are great.
- **Editor mobility is at an all-time high.** People are switching editors freely for the first time ever. Cursor reached an insane valuation that was impossible pre-AI.
- **Seed = build product, A = hints of PMF, B = proven PMF, C/D = repeatable revenue machine.** HashiCorp was just 1-2 years late on this standard cadence.
- **Think in bed.** Mitchell's nightly ritual: lights off, wife asleep, mentally running CLIs, writing code in his head, thinking through product copy. 3+ hours regularly.

### Assessment
**Scrape quality** is **good**. Full 25,225-word auto-generated transcript captured via yt-dlp. The content is a long-form interview (~2 hours) covering Mitchell's career arc from self-taught PHP kid to HashiCorp co-founder to Ghostty creator, with substantial practical detail on AI workflows, open source governance, and startup strategy. **Durability** is **high** — the AI workflow advice and open source policy insights will remain relevant for years. **Content type** is primary interview; **Density** is **high** with actionable insights throughout, including quick drive-by remarks that carry outsized value. **Originality** is **primary** — first-person account from Mitchell himself.

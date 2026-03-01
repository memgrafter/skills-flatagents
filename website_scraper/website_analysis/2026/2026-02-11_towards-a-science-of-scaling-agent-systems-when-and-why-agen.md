---
url: https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/
title: 'Towards a science of scaling agent systems: When and why agent systems work'
scraped_at: '2026-02-11T09:48:03.489793+00:00'
word_count: 1032
raw_file: raw/2026-02-11_towards-a-science-of-scaling-agent-systems-when-and-why-agen.txt
tldr: Google Research's controlled evaluation of 180 agent configurations reveals that multi-agent systems improve parallelizable
  tasks by up to 80.9% but degrade sequential tasks by 39-70%, challenging the "more agents is better" heuristic.
key_quote: Through a large-scale controlled evaluation of 180 agent configurations, we derive the first quantitative scaling
  principles for agent systems, revealing that the 'more agents' approach often hits a ceiling, and can even degrade performance
  if not aligned with the specific properties of the task.
durability: medium
content_type: fact
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people:
- Yubin Kim
- Xin Liu
tools: []
libraries: []
companies:
- Google
- OpenAI
- Anthropic
tags:
- multi-agent-systems
- ai-agents
- scaling-principles
- agent-architecture
- coordination-strategies
---

### TL;DR
Google Research's controlled evaluation of 180 agent configurations reveals that multi-agent systems improve parallelizable tasks by up to 80.9% but degrade sequential tasks by 39-70%, challenging the "more agents is better" heuristic.

### Key Quote
"Through a large-scale controlled evaluation of 180 agent configurations, we derive the first quantitative scaling principles for agent systems, revealing that the 'more agents' approach often hits a ceiling, and can even degrade performance if not aligned with the specific properties of the task."

### Summary

**Research Scope**
- 180 agent configurations evaluated across five architectures and four benchmarks
- Model families tested: OpenAI GPT, Google Gemini, Anthropic Claude
- Benchmarks: Finance-Agent (financial reasoning), BrowseComp-Plus (web navigation), PlanCraft (planning), Workbench (tool use)

**Five Architecture Types**
- **Single-Agent (SAS)**: Sequential execution with unified memory
- **Independent**: Parallel agents, no communication, aggregate at end
- **Centralized**: Hub-and-spoke with orchestrator delegating and synthesizing
- **Decentralized**: Peer-to-peer mesh with direct agent communication
- **Hybrid**: Hierarchical oversight plus peer-to-peer coordination

**Key Findings**

*The Alignment Principle*: On parallelizable tasks, centralized coordination improved performance by **80.9%** over single-agent (e.g., financial reasoning with simultaneous analysis of revenue, costs, market)

*The Sequential Penalty*: On sequential reasoning tasks, every multi-agent variant **degraded performance by 39-70%** — communication overhead fragmented reasoning, reducing "cognitive budget"

*Tool-Coordination Trade-off*: Tasks requiring 16+ tools incur disproportionately higher coordination "tax" for multi-agent systems

*Architecture as Safety*: Error amplification rates:
- Independent systems: **17.2x** error amplification (no cross-checking)
- Centralized systems: **4.4x** error amplification (orchestrator acts as validation bottleneck)

**Predictive Model**
- R² = 0.513, uses task properties (tool count, decomposability) to predict optimal architecture
- Correctly identifies optimal coordination strategy for **87% of unseen task configurations**

### Assessment

**Durability** (medium): This is foundational research establishing quantitative principles for a rapidly evolving field. The core findings about parallel vs. sequential task performance should endure, but specific percentages may shift as models and architectures improve.

**Content type**: Research / Technical findings

**Density** (high): Packed with specific metrics—180 configurations, 80.9% improvement, 39-70% degradation, 17.2x vs 4.4x error amplification, 87% prediction accuracy. Minimal fluff.

**Originality**: Primary source — original Google Research study with empirical findings

**Reference style**: refer-back — Useful for the specific quantitative findings and the architecture taxonomy when making agent design decisions

**Scrape quality** (good): Full text captured including all key statistics, architecture definitions, and findings. Figures referenced but not visible (expected for text scrape).
---
url: https://github.com/SWE-agent/mini-swe-agent?ref=ghuntley.com
title: GitHub - SWE-agent/mini-swe-agent at ghuntley.com
scraped_at: '2026-01-30T19:48:59.537728+00:00'
word_count: 970
raw_file: 2026-01-30_github-swe-agentmini-swe-agent-at-ghuntleycom.txt
tldr: A minimalist, 100-line Python coding agent developed by Princeton and Stanford that achieves high SWE-bench scores using
  only bash commands, linear history, and no complex tool-calling interfaces.
key_quote: Does not have any tools other than bash — it doesn't even use the tool-calling interface of the LMs.
durability: high
content_type: mixed
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people:
- John Yang
- Carlos E Jimenez
- Alexander Wettig
- Kilian Lieret
- Shunyu Yao
- Karthik R Narasimhan
- Ofir Press
tools:
- bash
- uvx
- pipx
- docker
- podman
- singularity
- apptainer
libraries:
- mini-swe-agent
- litellm
companies:
- Meta
- NVIDIA
- Essential AI
- Anyscale
- Princeton
- Stanford
tags:
- ai-agents
- software-engineering
- automation
- minimalism
---

### TL;DR
A minimalist, 100-line Python coding agent developed by Princeton and Stanford that achieves high SWE-bench scores using only bash commands, linear history, and no complex tool-calling interfaces.

### Key Quote
"Does not have any tools other than bash — it doesn't even use the tool-calling interface of the LMs."

### Summary
**Tool/Library**

- **Core Concept**: A radical simplification of the SWE-agent, stripping away complex tools and interfaces to rely solely on bash, making it easier to debug, fine-tune, and deploy.
- **Architecture**:
  - **Bash-only**: No custom tools or LM tool-calling interfaces; interacts with the environment via bash commands.
  - **Linear History**: Simple message appending (trajectory = messages), facilitating easier debugging and RLHF.
  - **Stateless Execution**: Uses `subprocess.run` (swappable with `docker exec`) for every action, avoiding stateful shell issues and simplifying sandboxing.
- **Performance**: Scores >74% on the SWE-bench verified benchmark; noted to start faster than Claude Code.
- **Target Audience**: Researchers (needing a clean baseline for fine-tuning/RL), Developers (wanting transparent/hackable tools), and Engineers (needing easy sandboxing).

**Installation & Usage**
- **Option 1 (Quick)**: `uvx mini-swe-agent` or `pipx run mini-swe-agent`
- **Option 2 (Local)**: `pip install mini-swe-agent` then run `mini` or `mini -v` (visual UI).
- **Option 3 (Dev)**: Clone repo and `pip install -e .`

**Key Differences from Full SWE-agent**
- **Use Mini-SWE-agent if**: You need a simple control flow, fast startup, CLI usage, or a baseline for research/RL.
- **Use Full SWE-agent if**: You need specific tools, YAML configuration, or complex history processors.

### Assessment
- **Durability**: High. While benchmark scores and specific model mentions (Gemini 3 Pro, GPT-5) will date quickly, the architectural philosophy (bash-only, linear history, minimal dependencies) represents a durable pattern for building robust, understandable agents.
- **Content type**: Reference / Announcement / Tutorial (Mixed).
- **Density**: High. The text condenses significant architectural reasoning and usage instructions into a short format without fluff.
- **Originality**: Primary source. This is the official repository documentation from the original creators (Princeton & Stanford).
- **Reference style**: Refer-back. Useful for checking specific install commands (`uvx`, `pip`) and comparing features against the full SWE-agent.
- **Scrape quality**: Good. The content appears complete with installation commands, architectural rationale, and comparison tables preserved.
---
url: https://github.com/SWE-agent/mini-swe-agent
title: 'GitHub - SWE-agent/mini-swe-agent: The 100 line AI agent that solves GitHub issues or helps you in your command line.
  Radically simple, no huge configs, no giant monorepo—but scores >74% on SWE-bench verified!'
scraped_at: '2026-01-30T18:01:00.624715+00:00'
word_count: 970
raw_file: 2026-01-30_github-swe-agentmini-swe-agent-the-100-line-ai-agent-that-so_1.txt
tldr: Mini-swe-agent is a roughly 100-line Python coding agent that relies solely on bash commands and `subprocess.run` to
  solve GitHub issues with >74% accuracy on SWE-bench verified, offering a radically simple, stateless alternative to complex
  agent frameworks.
key_quote: Just 100 lines of python (+100 total for env, model, script) — no fancy dependencies!
durability: medium
content_type: mixed
density: medium
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
- docker
- uv
- pipx
- podman
- singularity
- apptainer
libraries:
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
- coding-agents
- python
- swe-bench
- minimalism
---

### TL;DR
Mini-swe-agent is a roughly 100-line Python coding agent that relies solely on bash commands and `subprocess.run` to solve GitHub issues with >74% accuracy on SWE-bench verified, offering a radically simple, stateless alternative to complex agent frameworks.

### Key Quote
"Just 100 lines of python (+100 total for env, model, script) — no fancy dependencies!"

### Summary
**Type:** Tool/Library

*   **What it does:** A minimalist AI coding agent that interacts with the command line to fix bugs or implement features. It removes complex agent scaffolding (tools, history processors) to focus on the Language Model's ability to use bash.
*   **Architecture:**
    *   **Bash-only:** Uses no specialized tools or tool-calling interfaces; runs any model that outputs text.
    *   **Linear History:** Appends every step to the message history, simplifying debugging and fine-tuning.
    *   **Stateless Execution:** Uses Python’s `subprocess.run` for every action instead of a persistent shell, making sandboxing (switching to `docker exec`) trivial.
*   **Performance:** Scores >74% on the SWE-bench verified benchmark.
*   **Installation:**
    *   **Quick run:** `pip install uv && uvx mini-swe-agent [-v]` (or via `pipx`)
    *   **Local install:** `pip install mini-swe-agent`
    *   **Dev setup:** `pip install -e .`
*   **Usage:**
    *   CLI: `mini [flags]` (simple) or `mini -v` (visual UI).
    *   Python API: Instantiated via `DefaultAgent(LitellmModel(...), LocalEnvironment())`.
*   **Comparison:** Choose `mini-swe-agent` for simplicity, research baselines, or easy sandboxing. Choose full `SWE-agent` if you need custom tools, YAML configs, or complex history processing.

### Assessment
**Durability:** Medium. While the minimalist architecture is a stable concept, the specific benchmark claims (>74% on SWE-bench) and model recommendations (e.g., mentions of specific model versions reaching that score) are tied to the current state of LLM capability in 2024/2025.

**Content type:** Mixed (Project announcement / Technical documentation / Marketing). The source is a README promoting the tool's philosophy and usage.

**Density:** Medium. It efficiently lists technical details (commands, architectural choices like `subprocess.run`) alongside motivational text ("trust me", "radically simpler").

**Originality:** Primary source. This is the official repository documentation for the project by the Princeton & Stanford team.

**Reference style:** Refer-back. You will likely return to this for the specific installation commands or to verify the architectural differences between this and the full SWE-agent.

**Scrape quality:** Good. The text content is fully captured, though standard GitHub formatting (links, code blocks) is rendered in plain text here. No images or critical diagrams are referenced that would be missing.
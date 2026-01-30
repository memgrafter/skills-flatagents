---
url: https://github.com/SWE-agent/mini-swe-agent
title: "GitHub - SWE-agent/mini-swe-agent: The 100 line AI agent that solves GitHub issues or helps you in your command line. Radically simple, no huge configs, no giant monorepo—but scores >74% on SWE-bench verified!"
scraped_at: 2026-01-30T17:17:58.114333+00:00
word_count: 970
raw_file: 2026-01-30_github-swe-agentmini-swe-agent-the-100-line-ai-agent-that-so.txt
---

**Overview**
mini-swe-agent is a radically simplified, open-source AI agent consisting of approximately 100 lines of Python designed to solve GitHub issues and assist in command-line environments. Developed by the Princeton & Stanford team behind SWE-bench, it achieves a score of >74% on the SWE-bench verified benchmark using only Bash and modern LLM capabilities, eliminating complex tools and configurations.

### Key Features
*   **Minimal Codebase:** Built in roughly 100 lines of Python (plus ~100 for environment/model scripts) with no fancy dependencies.
*   **High Performance:** Scores over 74% on the SWE-bench verified benchmark; starts faster than Claude Code.
*   **Tool-Free Operation:** Uses no tools other than Bash; it does not even utilize the LLM's tool-calling interface, allowing compatibility with virtually any model.
*   **Stateless Execution:** Actions are executed via `subprocess.run`, making every action independent and easy to sandbox (Docker, Podman, Singularity, etc.).
*   **Linear History:** Maintains a simple, linear message history (appending steps), which is ideal for debugging, fine-tuning (FT), and reinforcement learning (RL).
*   **Widely Adopted:** Used by major tech organizations including Meta, NVIDIA, Essential AI, and Anyscale.

### Architecture & Philosophy
The project is designed to shift focus from the "agent scaffold" back to the Language Model itself.
*   **For Researchers:** Provides a clean baseline without bloat or assumptions, perfect for benchmarking, FT, or RL.
*   **For Developers:** Offers a hackable, transparent tool that is easy to understand, modify, and extend.
*   **Execution Model:** By avoiding a stateful shell session, the agent ensures stability and makes scaling and sandboxing trivial (e.g., switching `subprocess.run` with `docker exec`).

### Comparison: mini-swe-agent vs. SWE-agent
**Use mini-swe-agent if:**
*   You need a quick, local command-line tool.
*   You desire a simple control flow.
*   You want fast, stable sandboxing and benchmark evaluations.
*   You are conducting FT or RL and wish to avoid overfitting to a specific agent scaffold.

**Use SWE-agent if:**
*   You require specific tools or want to experiment with different tool interfaces.
*   You need advanced history processors.
*   You prefer powerful YAML configuration without modifying code.

### Installation & Usage
**Option 1: Quick CLI (Isolated Environment)**
*   `pip install uv && uvx mini-swe-agent [-v]`
*   `pip install pipx && pipx ensurepath && pipx run mini-swe-agent [-v]`

**Option 2: Install in Current Environment**
*   `pip install mini-swe-agent`
*   `mini -v` (runs the CLI)

**Option 3: Install from Source**
*   `git clone https://github.com/SWE-agent/mini-swe-agent.git`
*   `cd mini-swe-agent && pip install -e .`
*   `mini [-v]`

**Python Interface Example:**
```python
from swe_agent import DefaultAgent, LiteLLMModel, LocalEnvironment

agent = DefaultAgent(
    LiteLLMModel(model_name=...),
    LocalEnvironment(),
)
agent.run("Write a sudoku game")
```

### Notable Takeaways
*   **Simplicity Wins:** The project demonstrates that as LLMs become more capable (e.g., GPT-4o, Claude 3.5 Sonnet), complex tooling and interfaces are often unnecessary; raw Bash utilization is sufficient for high performance.
*   **Quote:** "The mini agent wants to be a hackable tool, not a black box."
*   **Action Item:** For users deploying in restricted environments, the stateless `subprocess.run` architecture significantly simplifies security and sandboxing implementation compared to stateful alternatives.
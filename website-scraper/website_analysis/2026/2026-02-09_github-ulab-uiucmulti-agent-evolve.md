---
url: https://github.com/ulab-uiuc/Multi-agent-evolve
title: GitHub - ulab-uiuc/Multi-agent-evolve
scraped_at: '2026-02-09T06:25:08.174019+00:00'
word_count: 843
raw_file: raw/2026-02-09_github-ulab-uiucmulti-agent-evolve.txt
tldr: Multi-Agent Evolve is a self-improving framework that enhances LLM reasoning by using a single model acting as Proposer,
  Solver, and Judge, co-evolving through a Task-Relative REINFORCE++ loop without external supervision.
key_quote: The system forms a continuous self-improving loop that strengthens reasoning without external supervision.
durability: medium
content_type: tutorial
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people:
- Yixing Chen
- Yiding Wang
- Siqi Zhu
- Haofei Yu
- Tao Feng
- Muhan Zhan
- Mostofa Patwary
- Jiaxuan You
tools:
- NVIDIA NIM
- evalplus
- vllm
libraries:
- flash-attn
- flashinfer-python
- wandb
companies:
- NVIDIA
- Alibaba
- UIUC
tags:
- llm
- reinforcement-learning
- multi-agent-systems
- self-improvement
- reasoning
---

### TL;DR
Multi-Agent Evolve is a self-improving framework that enhances LLM reasoning by using a single model acting as Proposer, Solver, and Judge, co-evolving through a Task-Relative REINFORCE++ loop without external supervision.

### Key Quote
"The system forms a continuous self-improving loop that strengthens reasoning without external supervision."

### Summary
**Core Framework**
-   **Mechanism**: Uses a single underlying model performing three collaborative roles updated simultaneously:
    -   **Proposer**: Generates new reasoning questions (`<question>...</question>`), filtered for quality and learnability.
    -   **Solver**: Answers valid questions (`<answer>...</answer>`); performance measures task difficulty.
    -   **Judge**: Evaluates both questions and answers (`<score>...</score>`), providing numeric rewards for RL.
-   **Training Method**: Updated using Task-Relative REINFORCE++.

**Performance Results**
-   Tested on Qwen2.5-3B-Instruct base.
-   **MAE (no reference)** achieved the highest Total Avg score of **60.19** (ID Avg: 69.45, OOD Avg: 43.99).
-   Outperformed baselines: AZR (57.72) and standard Qwen2.5-3B (55.33).

**Installation & Setup**
-   **Environment**: Python 3.10, `flash-attn==2.7.4.post1`, `flashinfer-python==0.2.2.post1`.
-   **API Keys**: Requires `api.json` for NVIDIA NIM (LLM service) for evaluation/grading.
-   **Hardware**: Requires significant compute (8x80GB GPUs used for 3B models).

**Usage & Commands**
-   **Data Prep**: `python scripts/prepare_test_datasets.py`
-   **Training**: `bash scripts/selfplay/mae.sh` (modify `include_references` in scripts to toggle reference data usage).
-   **Resume Modes**: Supports `disable`, `auto`, and `resume_path` via trainer arguments.
-   **Evaluation**:
    -   General benchmarks: `bash scripts/evaluation/eval_ID.sh` and `eval_OOD.sh`.
    -   Offline mode available to dump data (`azr.dump_eval_data=True`) and evaluate locally.
    -   Code evals use `evalplus` in a separate Python 3.11 environment.

### Assessment
-   **Durability** (medium): The architectural concept is durable, but specific dependencies (flash-attn versions), hardware requirements, and external API integrations (NVIDIA NIM) will likely change or require updates as the ecosystem evolves.
-   **Content type**: tutorial / reference
-   **Density** (high): Dense with specific version numbers, paths, command-line arguments, and configuration details.
-   **Originality**: primary source. This is the official code repository for the associated paper.
-   **Reference style**: refer-back. Users will likely return to copy installation commands or verify script arguments during implementation.
-   **Scrape quality** (good): The text captures the full README structure, including the mechanism explanation, benchmark tables, and code blocks.
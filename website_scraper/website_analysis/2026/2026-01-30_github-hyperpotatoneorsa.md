---
url: https://github.com/HyperPotatoNeo/RSA
title: GitHub - HyperPotatoNeo/RSA
scraped_at: '2026-01-30T20:37:51.991819+00:00'
word_count: 208
raw_file: 2026-01-30_github-hyperpotatoneorsa.txt
tldr: Provides commands and configuration details for evaluating and training RSA models using the `verl` library, including
  benchmark scripts for AIME-25 and HMMT-25, and a full RLOO training setup for Qwen3-4B.
key_quote: Download aggregation dataset used in our paper (mixture of DeepScaleR + Reasoning Gym tasks with candidates from
  Qwen3-4B-Instruct-2507)
durability: medium
content_type: mixed
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people:
- HyperPotatoNeo
tools:
- python
- srun
- vllm
- wandb
libraries:
- verl
companies:
- Qwen
- HuggingFace
- Volcengine
tags:
- reinforcement-learning
- model-training
- benchmarking
- rloo
- qwen
---

### TL;DR
Provides commands and configuration details for evaluating and training RSA models using the `verl` library, including benchmark scripts for AIME-25 and HMMT-25, and a full RLOO training setup for Qwen3-4B.

### Key Quote
"Download aggregation dataset used in our paper (mixture of DeepScaleR + Reasoning Gym tasks with candidates from Qwen3-4B-Instruct-2507)"

### Summary
**Evaluation (Benchmarks)**
-   **Script**: `eval_loop.py`
-   **Supported Datasets**: `aime25`, `hmmt25`, `rg_games`, `rg_cognition`, `supergpqa`
-   **Example Model**: `Qwen/Qwen3-30B-A3B-Instruct-2507`
-   **Key Parameters**:
    ```bash
    python eval_loop.py \
    --model Qwen/Qwen3-30B-A3B-Instruct-2507 \
    --dataset data/<dataset_name>/train.parquet \
    --output ./eval/<dataset_name> \
    --loops 10 \
    --k 4 \
    --population 16
    ```
-   **LiveCodeBench**: Use `eval_code.py` with similar flags.

**Prerequisites & Data**
-   **Dependency**: Install `verl` from `https://github.com/volcengine/verl.git`
-   **Dataset**: Training and aggregation data available on HuggingFace at `RSA-RL/DeepScaleR-RG-Aggregator-RL`.
-   **Checkpoints**: Finetuned models used in the paper are located in the same HuggingFace repository.

**Training (RLOO)**
-   **Command**: `python -m verl.trainer.main_ppo`
-   **Algorithm**: RLOO (`algorithm.adv_estimator=rloo`)
-   **Base Actor Model**: `Qwen/Qwen3-4B-Instruct-2507`
-   **Key Hyperparameters**:
    -   `actor_rollout_ref.actor.optim.lr`: `1e-6`
    -   `data.max_prompt_length`: `33792`
    -   `data.max_response_length`: `8192`
    -   `algorithm.kl_ctrl.kl_coef`: `0.0`
    -   `actor_rollout_ref.rollout.n`: `4`
    -   `actor_rollout_ref.rollout.name`: `vllm`
    -   Sequence Parallel Size: `4`
    -   Total Epochs: `100`

### Assessment
-   **Durability** (medium): The documentation relies on specific library versions (`verl`) and exact model paths (e.g., `Qwen3-30B-A3B-Instruct-2507`). While the RLOO methodology is stable, the command-line flags and API calls are likely to change as the underlying libraries evolve.
-   **Content type**: reference / tutorial
-   **Density** (high): The text is composed almost entirely of executable commands, file paths, and specific configuration values with no conversational filler.
-   **Originality**: primary source. This appears to be raw documentation from the project's README.
-   **Reference style**: refer-back. Users will likely copy-paste these commands to run benchmarks or replicate training.
-   **Scrape quality** (good): The scrape captures the code blocks, command flags, and dataset URLs effectively. No significant truncation is apparent.
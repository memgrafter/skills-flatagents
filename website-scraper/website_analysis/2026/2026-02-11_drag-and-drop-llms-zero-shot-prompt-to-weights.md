---
url: https://arxiv.org/html/2506.16406
title: 'Drag-and-Drop LLMs: Zero-Shot Prompt-to-Weights'
scraped_at: '2026-02-11T10:11:21.901702+00:00'
word_count: 8892
raw_file: raw/2026-02-11_drag-and-drop-llms-zero-shot-prompt-to-weights.txt
tldr: DnD is a hyper-network that generates task-specific LoRA weights directly from unlabeled prompts in seconds, eliminating
  gradient-based fine-tuning while achieving up to 30% better performance on unseen benchmarks at 12,000× lower computational
  cost.
key_quote: By collapsing the classical 'data → gradients → weights' loop into a single forward step, DnD challenges the notion
  that gradient descent is indispensable for model specialization and opens a new path where weights themselves become a new
  data modality and generative target conditioned on concise task descriptors.
durability: medium
content_type: fact
density: high
originality: primary
reference_style: deep-study
scrape_quality: good
people: []
tools:
- LoRA
- Sentence-BERT
- GloVe
- T5
libraries:
- Qwen2.5
- Qwen2.5-VL
companies: []
tags:
- parameter-generation
- lora-adaptation
- hyper-networks
- llm-fine-tuning
- zero-shot-learning
---

### TL;DR
DnD is a hyper-network that generates task-specific LoRA weights directly from unlabeled prompts in seconds, eliminating gradient-based fine-tuning while achieving up to 30% better performance on unseen benchmarks at 12,000× lower computational cost.

### Key Quote
"By collapsing the classical 'data → gradients → weights' loop into a single forward step, DnD challenges the notion that gradient descent is indispensable for model specialization and opens a new path where weights themselves become a new data modality and generative target conditioned on concise task descriptors."

### Summary

**Architecture & Method:**
- **Two-stage pipeline**: (1) Sentence-BERT encodes prompt batches into embeddings; (2) Cascaded hyper-convolutional decoder expands embeddings into full LoRA weight matrices
- **Training**: Collects LoRA checkpoints from various datasets, randomly pairs with prompt batches from training data, optimizes generator with MSE loss between generated and tokenized weights
- **Inference**: Single forward pass from novel prompts → LoRA weights (no gradient descent)

**Experimental Results:**
- **Common sense reasoning (Qwen2.5-0.5B)**: 21% average accuracy improvement over training LoRAs on unseen datasets (e.g., ARC-c: 39.5% → 51.6%)
- **Coding (Qwen2.5-1.5B/7B)**: HumanEval pass@1 improved from 17.6% to 32.7% (zero-shot)
- **Math (Qwen2.5-1.5B/7B)**: GSM8K improved from 42.9% to 66.3%; MATH from 14.8% to 23.9%
- **Multimodal (Qwen2.5-VL-3B)**: Works on Math-Vision and Math-Vista benchmarks
- **Cross-domain**: Common-sense trained generator transfers to science datasets (35.6% → 45.3%)

**Efficiency Claims:**
- Generates parameters in 0.11–0.73 seconds on single A100
- 2,500×–12,000× faster than full-shot tuning with comparable or better accuracy
- Outperforms few-shot tuning and in-context learning while using only 128 unlabeled prompts

**Ablation Findings:**
- Prompts outperform answers as conditions (simple answers like "A/B/C/D" lack diversity)
- Works with GloVe, Sentence-BERT, T5 encoders; Qwen2.5-7B decoder fails (too heavy, limits batch diversity)
- Requires ≥4 training datasets for robust zero-shot generalization
- Random batch sampling (Strategy 2) outperforms fixed-prompt pairing (Strategy 1)

### Assessment

**Durability (medium)**: Core concept of prompt-to-weight generation is novel and likely to inspire follow-up research, but specific architectural choices and benchmark numbers will age as methods improve. Qwen2.5 references already feel current (2024-2025).

**Content type**: Primary research with supporting experiments and ablations.

**Density (high)**: Dense with specific numbers, architectures, and experimental configurations. Appendix contains full hyperparameter tables and decoder structure details.

**Originality**: Primary source introducing new paradigm. Compares against prior parameter generation work (RPG, p-diff, COND P-DIFF) and demonstrates advantages on open-set generation.

**Reference style**: Deep-study for understanding the prompt-to-weight paradigm; refer-back for architectural details and benchmark numbers.

**Scrape quality (good)**: Full paper captured including all tables, formulas, and appendix. Figures referenced but not rendered (Figure 2, 3, 5, 6, 7 mentioned). Project link provided at https://jerryliang24.github.io/DnD.
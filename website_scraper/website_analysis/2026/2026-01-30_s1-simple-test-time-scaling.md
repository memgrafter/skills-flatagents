---
url: https://arxiv.org/abs/2501.19393
title: 's1: Simple test-time scaling'
scraped_at: '2026-01-30T20:39:32.198651+00:00'
word_count: 422
raw_file: 2026-01-30_s1-simple-test-time-scaling.txt
tldr: Replicates OpenAI's o1 test-time scaling using a simple "budget forcing" technique that extends model generation by
  appending "Wait" tokens, applied to a Qwen2.5-32B model fine-tuned on 1,000 curated samples (s1K), outperforming o1-preview
  on math benchmarks.
key_quote: We seek the simplest approach to achieve test-time scaling and strong reasoning performance.
durability: medium
content_type: reference
density: high
originality: primary
reference_style: deep-study
scrape_quality: good
people:
- Niklas Muennighoff
tools: []
libraries: []
companies:
- OpenAI
tags:
- test-time-scaling
- llm-reasoning
- fine-tuning
- machine-learning
- nlp
---

### TL;DR
Replicates OpenAI's o1 test-time scaling using a simple "budget forcing" technique that extends model generation by appending "Wait" tokens, applied to a Qwen2.5-32B model fine-tuned on 1,000 curated samples (s1K), outperforming o1-preview on math benchmarks.

### Key Quote
"We seek the simplest approach to achieve test-time scaling and strong reasoning performance."

### Summary
- **Methodology**: Introduces a "budget forcing" technique to control test-time compute by either terminating the model's process or appending "Wait" tokens to force extended generation and self-correction.
- **Dataset (s1K)**: Curated a small dataset of 1,000 questions with reasoning traces based three validated criteria: difficulty, diversity, and quality.
- **Base Model**: Uses Qwen2.5-32B-Instruct as the foundation, fine-tuned on the s1K dataset.
- **Performance**: The resulting s1-32B model exceeds OpenAI's o1-preview on competition math questions (MATH and AIME24) by up to 27%.
- **Scaling Results**: Applying budget forcing allows s1-32B to extrapolate performance, improving from 50% to 57% on AIME24.
- **Availability**: The model, dataset, and code are released as open-source.

### Assessment
- **Durability**: Medium. The concept of test-time scaling is highly relevant in early 2025, but the specific "budget forcing" trick and the reliance on the Qwen2.5 architecture may evolve quickly as the field rapidly iterates on reasoning models.
- **Content type**: Research/Technical.
- **Density**: High. The abstract is concise, packed with specific metrics (27% improvement, 1,000 samples), method names (budget forcing), and direct comparisons (o1-preview).
- **Originality**: Primary source. This is the original paper introducing the s1K dataset and the budget forcing methodology by the research team.
- **Reference style**: Deep-study. Essential for understanding the mechanics of a lightweight replication of o1-style reasoning and for implementing the specific "Wait" token intervention.
- **Scrape quality**: Good. The content appears to be a clean capture of the full abstract, metadata, and submission history without truncation.
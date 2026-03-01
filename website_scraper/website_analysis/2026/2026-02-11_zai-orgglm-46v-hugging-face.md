---
url: https://huggingface.co/zai-org/GLM-4.6V
title: zai-org/GLM-4.6V · Hugging Face
scraped_at: '2026-02-11T09:58:22.834882+00:00'
word_count: 998
raw_file: 2026-02-11_zai-orgglm-46v-hugging-face.txt
tldr: GLM-4.6V is a 106B-parameter multimodal foundation model with native function calling, 128K context window, and state-of-the-art
  visual understanding—accompanied by a 9B lightweight variant (GLM-4.6V-Flash) for local deployment.
key_quote: Crucially, we integrate native Function Calling capabilities for the first time. This effectively bridges the gap
  between 'visual perception' and 'executable action' providing a unified technical foundation for multimodal agents in real-world
  business scenarios.
durability: medium
content_type: mixed
density: medium
originality: primary
reference_style: refer-back
scrape_quality: good
people:
- V Team
tools:
- vllm
- sglang
- ffmpeg
libraries:
- transformers
companies:
- zai-org
- Z.ai
tags:
- multimodal-models
- vision-language-models
- function-calling
- large-language-models
- document-understanding
---

### TL;DR
GLM-4.6V is a 106B-parameter multimodal foundation model with native function calling, 128K context window, and state-of-the-art visual understanding—accompanied by a 9B lightweight variant (GLM-4.6V-Flash) for local deployment.

### Key Quote
"Crucially, we integrate native Function Calling capabilities for the first time. This effectively bridges the gap between 'visual perception' and 'executable action' providing a unified technical foundation for multimodal agents in real-world business scenarios."

### Summary
**Model Variants**
- **GLM-4.6V (106B)**: Foundation model for cloud/high-performance clusters
- **GLM-4.6V-Flash (9B)**: Lightweight model for local deployment, low-latency applications
- Both scale to 128K token context window during training

**Key Features**
- **Native Multimodal Function Calling**: Pass images/screenshots/documents directly as tool inputs; interpret visual outputs in reasoning chain
- **Interleaved Image-Text Generation**: Creates mixed-media content, can call search/retrieval tools during generation
- **Multimodal Document Understanding**: Process up to 128K tokens across multiple documents, understands layout/charts/tables as images
- **Frontend Replication**: Reconstructs pixel-accurate HTML/CSS from UI screenshots, supports natural-language visual edits

**Usage**
```python
# Dependencies (vLLM): pip install vllm>=0.12.0, transformers>=5.0.0rc0
# Dependencies (SGLang): pip install sglang>=0.5.6.post1, nvidia-cudnn-cu12==9.16.0.29, ffmpeg
from transformers import AutoProcessor, Glm4vMoeForConditionalGeneration
model = Glm4vMoeForConditionalGeneration.from_pretrained("zai-org/GLM-4.6V", torch_dtype="auto", device_map="auto")
```

**Recommended Inference Parameters** (for reproducing leaderboard results)
- top_p: 0.6, top_k: 2, temperature: 0.8, repetition_penalty: 1.1, max_generate_tokens: 16K

**Known Limitations**
- Pure text QA capabilities need improvement (focus was visual multimodal)
- May overthink or repeat on complex prompts
- Perception issues with counting accuracy and identifying specific individuals

**Resources**: Blog (z.ai/blog/glm-4.6v), Paper (arXiv:2507.01006), GitHub (zai-org/GLM-V), Demo (chat.z.ai), 7,819 downloads last month

### Assessment
**Durability**: Medium — Model versions change frequently; installation commands and API specifics will age quickly, but the architectural concepts and feature descriptions remain relevant. The paper citation indicates July 2025 (arXiv:2507.01006).

**Content type**: Reference / announcement (mixed) — Serves as official documentation for model access while also announcing capabilities.

**Density**: Medium — Covers model specs, features, installation, code example, evaluation settings, and known issues without excessive padding. Some marketing language present.

**Originality**: Primary source — Official repository from the model creators (zai-org/V Team).

**Reference style**: Refer-back — Useful for copying installation commands, inference parameters, and code snippets when actually using the model.

**Scrape quality**: Good — Full model card content captured including code blocks, links, limitations, and citation. No images missing that would affect understanding.
---
url: https://github.com/Laszlobeer/Dungeo_ai
title: 'GitHub - Laszlobeer/-Dungeo_ai-otudated-: this is a dungeon ai run locally that use your llm'
scraped_at: '2026-01-30T20:01:00.419638+00:00'
word_count: 248
raw_file: 2026-01-30_github-laszlobeer-dungeo-ai-otudated-this-is-a-dungeon-ai-ru.txt
tldr: A local, open-source Python text adventure game using Ollama for offline LLM inference and optional AllTalk TTS, though
  the repository is explicitly marked as "outdated."
key_quote: If you use it commercially or integrate it into monetized/restricted systems, YOU MUST CREDIT THE ORIGINAL AUTHOR.
durability: low
content_type: reference
density: medium
originality: primary
reference_style: skim-once
scrape_quality: good
people:
- Laszlo
tools:
- Ollama
- AllTalk TTS
- NVIDIA CUDA Toolkit
- git
- pip
libraries:
- requests
- sounddevice
- numpy
- soundfile
companies: []
tags:
- text-adventure
- local-llm
- python
- ai-gaming
- text-to-speech
---

### TL;DR
A local, open-source Python text adventure game using Ollama for offline LLM inference and optional AllTalk TTS, though the repository is explicitly marked as "outdated."

### Key Quote
"If you use it commercially or integrate it into monetized/restricted systems, YOU MUST CREDIT THE ORIGINAL AUTHOR."

### Summary
**Type:** Tool/Library

-   **Functionality**: An offline AI text adventure game that generates interactive storytelling. It includes features for role-playing, story creation, and optional text-to-speech via AllTalk.
-   **Prerequisites**:
    -   Python 3.10+
    -   pip
    -   Ollama (for local AI model inference)
    -   NVIDIA CUDA Toolkit (for GPU acceleration)
    -   (Optional) AllTalk TTS for voice output
-   **Installation**:
    -   Clone the repo: `git clone https://github.com/Laszlobeer/Dungeo_ai.git`
    -   Create environment: `python -m venv Dungeo_ai` (or conda equivalent)
    -   Install dependencies: `pip install -r requirements.txt` (Manual install command provided if requirements.txt fails).
-   **In-Game Commands**:
    - `/censored`: Toggles NSFW/SFW mode
    - `/redo`: Regenerates the last AI response
    - `/save`/`/load`: Manage story state to `adventure.txt`
    - `/change`: Switch the active Ollama model
-   **License**: MIT License, but explicitly mandates attribution if used commercially or integrated into monetized systems.

### Assessment
-   **Durability** (Low): The repository URL includes the tag "outdated," suggesting the code is no longer maintained or may be superseded. Dependencies (Python 3.10, specific Ollama integration) may become stale quickly.
-   **Content type**: Documentation / Reference
-   **Density** (Medium): Provides specific installation commands and a concise list of slash commands without excessive fluff.
-   **Originality**: Primary source (repository README).
-   **Reference style**: Skim-once. Useful for setting up a local environment initially, but due to the "outdated" status, it is unlikely to be a long-term reference unless the project is resurrected or forked.
-   **Scrape quality** (Good): The content captures the installation steps, command list, and licensing details effectively.
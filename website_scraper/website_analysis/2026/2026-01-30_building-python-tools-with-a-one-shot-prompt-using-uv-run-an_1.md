---
url: https://simonwillison.net/2024/Dec/19/one-shot-python-tools/
title: Building Python tools with a one-shot prompt using uv run and Claude Projects
scraped_at: '2026-01-30T18:00:17.313363+00:00'
word_count: 853
raw_file: 2026-01-30_building-python-tools-with-a-one-shot-prompt-using-uv-run-an_1.txt
tldr: Simon Willison explains a workflow using Claude Projects with custom instructions to generate single-file Python tools
  that manage their own dependencies via PEP 723 and `uv run`, eliminating setup steps.
key_quote: Running the script causes uv to create a temporary virtual environment with those dependencies installed, a process
  that takes just a few milliseconds once the uv cache has been populated.
durability: high
content_type: mixed
density: medium
originality: synthesis
reference_style: refer-back
scrape_quality: good
people:
- Simon Willison
tools:
- uv
- Claude Projects
libraries:
- click
- sqlite-utils
- boto3
- rich
- beautifulsoup4
- starlette
companies:
- Amazon
tags:
- python
- llm-workflow
- dependency-management
- automation
- uv
---

### TL;DR
Simon Willison explains a workflow using Claude Projects with custom instructions to generate single-file Python tools that manage their own dependencies via PEP 723 and `uv run`, eliminating setup steps.

### Key Quote
"Running the script causes uv to create a temporary virtual environment with those dependencies installed, a process that takes just a few milliseconds once the uv cache has been populated."

### Summary
*   **Core Concept**: Using "one-shot" prompts in Claude to generate complete, single-file Python CLI tools or web apps that require no manual environment setup.
*   **Technology Stack**:
    *   **`uv run`**: A Python package installer/runner that reads script metadata.
    *   **PEP 723**: The standard for inline script dependencies (Python 3.12+).
*   **The Mechanism**:
    *   The LLM is instructed (via Claude Project custom instructions) to prepend a specific "magic comment" to every script.
    *   This comment defines the required Python version and a list of dependencies (e.g., `click`, `boto3`, `rich`).
    *   When the user runs `uv run script.py`, `uv` automatically creates a temporary virtual environment, installs the listed dependencies, and executes the script.
*   **Custom Instruction Template**: The author teaches Claude that scripts must start with:
    ```python
    # /// script
    # requires-python = ">=3.12"
    # dependencies = [
    #     "click",
    #     "sqlite-utils",
    # ]
    # ///
    ```
*   **Examples Provided**:
    *   **S3 Debug Tool**: A CLI tool using `boto3` and `rich` to diagnose 404 errors on S3 URLs.
    *   **HTML Stripper**: A Starlette web app using `beautifulsoup4` that strips HTML tags from a URL, run completely standalone.
*   **Key Benefit**: Scripts can even be executed directly from a URL (e.g., `uv run http://example.com/script.py args`), assuming trust in the source.

### Assessment
**Durability**: High. Although `uv` is relatively new, it is rapidly becoming a standard tool. PEP 723 is an official Python standard, ensuring the pattern remains valid. **Content type**: Mixed (Tutorial/Opinion). **Density**: Medium. It is a short essay explaining a specific workflow pattern rather than a deep technical dive. **Originality**: Synthesis. It combines PEP 723, `uv`, and LLM system prompts into a cohesive development pattern. **Reference style**: Refer-back. The custom instruction prompt and the PEP 723 header format are highly reusable for setting up similar AI coding environments. **Scrape quality**: Good. The text is complete and readable, though the "More recent articles" section at the bottom contains nonsensical future dates (2026) which appear to be site navigation errors unrelated to the article content.
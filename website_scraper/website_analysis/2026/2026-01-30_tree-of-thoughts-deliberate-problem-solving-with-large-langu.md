---
url: https://openreview.net/forum?id=5Xc1ecxO1h
title: 'Tree of Thoughts: Deliberate Problem Solving with Large Language...'
scraped_at: '2026-01-30T20:39:04.942019+00:00'
word_count: 226
raw_file: 2026-01-30_tree-of-thoughts-deliberate-problem-solving-with-large-langu.txt
tldr: Tree of Thoughts (ToT) is a framework that enhances Large Language Model reasoning by introducing search algorithms
  (exploring multiple reasoning paths, lookahead, and backtracking) over coherent text units, significantly outperforming
  standard Chain-of-Thought prompting in tasks like the Game of 24.
key_quote: ToT allows LMs to perform deliberate decision making by considering multiple different reasoning paths and self-evaluating
  choices to decide the next course of action, as well as looking ahead or backtracking when necessary to make global choices.
durability: high
content_type: reference
density: high
originality: primary
reference_style: deep-study
scrape_quality: partial
people: []
tools:
- GPT-4
libraries: []
companies: []
tags:
- large-language-models
- reasoning
- prompt-engineering
- search-algorithms
- tree-of-thoughts
---

### TL;DR
Tree of Thoughts (ToT) is a framework that enhances Large Language Model reasoning by introducing search algorithms (exploring multiple reasoning paths, lookahead, and backtracking) over coherent text units, significantly outperforming standard Chain-of-Thought prompting in tasks like the Game of 24.

### Key Quote
"ToT allows LMs to perform deliberate decision making by considering multiple different reasoning paths and self-evaluating choices to decide the next course of action, as well as looking ahead or backtracking when necessary to make global choices."

### Summary
- **Problem**: Current LLM inference is token-level and left-to-right (e.g., Chain of Thought), limiting capabilities in tasks requiring exploration, strategic lookahead, or correcting early decisions.
- **Method**: Introduces **Tree of Thoughts (ToT)**, a generalization of Chain-of-Thought.
    - Treats intermediate text steps as "thoughts."
    - Enables the LM to generate and evaluate diverse thoughts.
    - Uses search algorithms to explore multiple reasoning paths, look ahead, and backtrack.
- **Results**:
    - Tested on three novel tasks requiring planning/search: Game of 24, Creative Writing, and Mini Crosswords.
    - **Game of 24**: GPT-4 with Chain-of-Thought solved 4% of tasks; GPT-4 with ToT solved 74%.
- **Code**: Prompts and implementation available at: `https://github.com/princeton-nlp/tree-of-thought-llm`.

### Assessment
**Durability**: High. This is a seminal research paper introducing a fundamental architectural shift in how LLMs process reasoning (moving from linear to Tree-based search), making it relevant for the foreseeable future of AI planning.

**Content type**: Research/Technical (Abstract).

**Density**: High. The abstract is concise and packed with specific performance statistics (74% vs 4%) and clear methodological definitions.

**Originality**: Primary source. This is the original paper submission for the ToT framework.

**Reference style**: Deep-study. The content describes a complex algorithmic approach that requires understanding search algorithms and prompting strategies to implement effectively.

**Scrape quality**: Partial. The source text provided is the abstract and metadata from OpenReview. It is missing the full paper body, including detailed methodology, full result tables, figures, and appendices (indicated by the "Loading" text at the end).
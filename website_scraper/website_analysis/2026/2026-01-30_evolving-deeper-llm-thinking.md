---
url: https://arxiv.org/abs/2501.09891
title: Evolving Deeper LLM Thinking
scraped_at: '2026-01-30T20:40:08.396676+00:00'
word_count: 292
raw_file: 2026-01-30_evolving-deeper-llm-thinking.txt
tldr: Introduces "Mind Evolution," an evolutionary search strategy that scales LLM inference-time compute by generating, recombining,
  and refining candidate responses to solve natural language planning tasks with over 98% accuracy.
key_quote: Mind Evolution solves more than 98% of the problem instances using Gemini 1.5 Pro without the use of a formal solver.
durability: high
content_type: fact
density: high
originality: primary
reference_style: deep-study
scrape_quality: partial
people: []
tools:
- Gemini 1.5 Pro
libraries: []
companies: []
tags:
- llm-inference
- evolutionary-algorithms
- search-strategies
- natural-language-planning
- mind-evolution
---

### TL;DR
Introduces "Mind Evolution," an evolutionary search strategy that scales LLM inference-time compute by generating, recombining, and refining candidate responses to solve natural language planning tasks with over 98% accuracy.

### Key Quote
"Mind Evolution solves more than 98% of the problem instances using Gemini 1.5 Pro without the use of a formal solver."

### Summary
**Type:** Research/Technical
**Topic:** Inference-time compute scaling and search strategies

*   **Methodology**: Proposes "Mind Evolution," an evolutionary search approach where an LLM generates, recombines, and refines candidate responses.
*   **Key Feature**: Avoids the need to formalize the underlying inference problem, requiring only a solution evaluator.
*   **Comparison**: Outperforms other inference strategies (Best-of-N and Sequential Revision) when controlling for inference cost.
*   **Benchmarks**: Evaluated on TravelPlanner and Natural Plan benchmarks.
*   **Results**: Achieved >98% solve rate using the Gemini 1.5 Pro model without relying on external formal solvers.

### Assessment
**Durability**: High — Focuses on algorithmic approaches to inference scaling which are likely to remain relevant, though benchmark results will age as models improve.
**Content type**: Research (Abstract summary)
**Density**: High — Concisely packs method name, mechanism, comparisons, benchmarks, and specific performance metrics into a short paragraph.
**Originality**: Primary source — This is the abstract for the original paper submission.
**Reference style**: Deep-study — The abstract serves as a gatekeeper; specific details on the evolutionary algorithm mechanics are likely in the full PDF.
**Scrape quality**: Partial — The input contains only the abstract and metadata; the full methodology, dataset details, and code implementations are not present in the source text provided.
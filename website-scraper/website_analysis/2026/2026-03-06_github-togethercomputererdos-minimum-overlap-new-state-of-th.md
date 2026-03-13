---
url: https://github.com/togethercomputer/erdos-minimum-overlap
title: 'GitHub - togethercomputer/erdos-minimum-overlap: New State-of-the-Art on Erdős'' Minimum Overlap Problem'
scraped_at: '2026-03-06T19:22:43.348285+00:00'
word_count: 243
raw_file: raw/2026-03-06_github-togethercomputererdos-minimum-overlap-new-state-of-th.txt
tldr: Together Computer used AI agents with sequential linear programming to achieve a new state-of-the-art upper bound for
  Erdős' Minimum Overlap Problem by optimizing step function constructions.
key_quote: We let AI agents tackle a classic open problem in combinatorics and analysis — Erdős' minimum overlap problem —
  and obtained a new state-of-the-art upper bound!
durability: high
content_type: announcement
density: high
originality: primary
reference_style: skim-once
scrape_quality: partial
people:
- Erdős
- Haugland
tools: []
libraries: []
companies:
- Together Computer
tags:
- combinatorics
- mathematical-optimization
- artificial-intelligence
- number-theory
---

###TL;DR
Together Computer used AI agents with sequential linear programming to achieve a new state-of-the-art upper bound for Erdős' Minimum Overlap Problem by optimizing step function constructions.

### Key Quote
"We let AI agents tackle a classic open problem in combinatorics and analysis — Erdős' minimum overlap problem — and obtained a new state-of-the-art upper bound!"

### Summary
- **Achievement**: Established a new state-of-the-art upper bound for Erdős' Minimum Overlap Problem (posed in 1955).
- **Methodology**: Used AI agents applying sequential linear programming. The agents optimized step function constructions, starting from the best previously known solutions.
- **Problem Context**:
  - Asks for the minimum necessary overlap when partitioning $\{1, \dots, 2n\}$ into two sets $A$ and $B$ of size $n$.
  - The asymptotics are governed by constant $C_5$, defined via non-negative functions $f, g$ with specific integral constraints.
- **Step Function Approach**:
  - Based on Haugland (2016), $C_5$ is the infimum over step functions $h \colon [0, 2] \to [0, 1]$.
  - Upper bounds are obtained by constructing explicit step functions; finer steps allow for potentially tighter bounds.
- **Status**: A detailed write-up on the specific method and results is forthcoming.

### Assessment
- **Durability**: High. The mathematical result (the new bound) is a permanent contribution to the field, though this specific page serves as a preliminary announcement.
- **Content type**: Announcement / Research snippet.
- **Density**: High. The text is concise and packed with specific mathematical definitions, references (Haugland 2016), and technical methodology.
- **Originality**: Primary source. This is the official repository for the specific achievement described.
- **Reference style**: Skim-once. This page serves as a placeholder until the "forthcoming write-up" is published; it is useful to confirm *who* achieved the result and *how* at a high level, but lacks the full paper's depth.
- **Scrape quality**: Partial. While the core text is captured, the raw output includes GitHub UI noise ("You signed in with another tab..."), and the actual numerical value of the new bound is not included in this snippet.
---
url: https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals
title: AGENTS.md outperforms skills in our agent evals - Vercel
scraped_at: '2026-02-09T06:29:58.499095+00:00'
word_count: 1418
raw_file: 2026-02-09_agentsmd-outperforms-skills-in-our-agent-evals-vercel.txt
tldr: Vercel's internal evaluations reveal that embedding a compressed docs index in `AGENTS.md` (achieving 100% pass rate)
  significantly outperforms "skills" (max 79%) for Next.js coding agents because passive context eliminates the agent's need
  to decide when to retrieve information.
key_quote: The goal is to shift agents from pre-training-led reasoning to retrieval-led reasoning. AGENTS.md turns out to
  be the most reliable way to make that happen.
durability: high
content_type: mixed
density: high
originality: primary
reference_style: deep-study
scrape_quality: good
people:
- Jude Gao
tools:
- npx @next/codemod
- Claude Code
- Cursor
- skills.sh
libraries:
- Next.js
- '@next/codemod'
companies:
- Vercel
tags:
- ai-agents
- nextjs
- documentation
- rag
- evals
---

### TL;DR
Vercel's internal evaluations reveal that embedding a compressed docs index in `AGENTS.md` (achieving 100% pass rate) significantly outperforms "Skills" (max 79%) for Next.js coding agents because passive context eliminates the agent's need to decide when to retrieve information.

### Key Quote
"The goal is to shift agents from pre-training-led reasoning to retrieval-led reasoning. AGENTS.md turns out to be the most reliable way to make that happen."

### Summary
**Research Context & Problem**
*   AI coding agents rely on training data that lacks knowledge of new framework APIs (e.g., Next.js 16 features like `use cache`, `connection()`, `forbidden()`).
*   Vercel tested two methods to provide agents with version-specific documentation: **Skills** (on-demand retrieval) and **AGENTS.md** (persistent context).

**Experimental Results**
*   **Skills (No Instructions):** 0% improvement over baseline. Agents failed to invoke the skill in 56% of cases.
*   **Skills (With Instructions):** Pass rate increased to 79%, but results were highly sensitive to specific wording (e.g., "invoke first" vs. "explore first" produced different code outcomes).
*   **AGENTS.md (Compressed Index):** Achieved a **100% pass rate** on the hardened eval suite targeting Next.js 16 APIs.

**Why AGENTS.md Won**
*   **No Decision Point:** Agents do not need to decide *if* they should look up docs; the index is already in the system prompt.
*   **Consistency:** Available in every turn, unlike skills which load asynchronously.
*   **No Ordering Issues:** Eliminates sequencing errors (e.g., exploring project structure before reading docs).

**Implementation Details**
*   **Compression:** A full docs index (~40KB) was compressed to **8KB** using a pipe-delimited format without losing effectiveness.
*   **Format:** `[Next.js Docs Index]|root: ./.next-docs|...`
*   **Key Instruction:** The embedded index includes the directive: *"IMPORTANT: Prefer retrieval-led reasoning over pre-training-led reasoning."*

**Actionable Steps**
*   **Command:** Run `npx @next/codemod@canary agents-md` to auto-detect the Next.js version, download matching docs to `.next-docs/`, and inject the index into `AGENTS.md`.
*   **Recommendation:** Framework authors should provide `AGENTS.md` snippets rather than relying solely on skills for general knowledge.

### Assessment
- **Durability**: **Medium-High**. The specific findings regarding Next.js 16 will age as models train on newer data, but the architectural insight—that passive context outperforms agent-initiated tool use for general framework knowledge—is a durable pattern for AI engineering.
- **Content type**: **Mixed** (Research report / Technical tutorial). It presents experimental data followed by a practical implementation guide.
- **Density**: **High**. Packed with specific metrics (0% vs 100%), API names, file sizes, and command syntax.
- **Originality**: **Primary source**. Original research and engineering by Vercel (Jude Gao).
- **Reference style**: **Deep-study**. Valuable for understanding the "why" behind agent reliability, though the command itself is a "skim-once" utility.
- **Scrape quality**: **Good**. The text is complete, though it references specific Next.js 16 APIs that imply a fast-moving target. The "canary" tag in the install command suggests the tooling is in active development.
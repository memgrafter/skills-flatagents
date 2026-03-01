---
url: https://news.ycombinator.com/item?id=46568794
title: Finding and fixing Ghostty's largest memory leak
scraped_at: '2026-02-11T10:34:51.325887+00:00'
word_count: 7459
raw_file: raw/2026-02-11_finding-and-fixing-ghosttys-largest-memory-leak.txt
tldr: Hacker News discussion of Mitchell Hashimoto's blog post about tracking down and fixing a memory leak in Ghostty terminal
  emulator, involving a subtle bug in page-based memory pooling where non-standard sized pages were incorrectly freed.
key_quote: The specific language feature you want if you insist that you don't want this kind of leak is Linear Types. Rust
  has Affine Types. This means Rust cares that for any value V of type T, Rust can see that we did not destroy V twice (or
  more often). With Linear Types the compiler checks that you destroyed V exactly once, not less and not more.
durability: medium
content_type: mixed
density: medium
originality: commentary
reference_style: skim-once
scrape_quality: good
people:
- Mitchell Hashimoto
tools:
- Ghostty
- Claude Code
libraries: []
companies: []
tags:
- memory-leak
- terminal-emulator
- zig
- rust
- memory-management
---

### TL;DR
Hacker News discussion of Mitchell Hashimoto's blog post about tracking down and fixing a memory leak in Ghostty terminal emulator, involving a subtle bug in page-based memory pooling where non-standard sized pages were incorrectly freed.

### Key Quote
"The specific language feature you want if you insist that you don't want this kind of leak is Linear Types. Rust has Affine Types. This means Rust cares that for any value V of type T, Rust can see that we did not destroy V twice (or more often). With Linear Types the compiler checks that you destroyed V exactly once, not less and not more."

### Summary
**Discussion of the Bug:**
- Ghostty uses a page-based memory pool for scrollback, with "standard" (pooled) and "non-standard" (directly mmap'd) pages
- Bug: When resizing pages, the metadata size field was updated without changing underlying allocation, causing the free function to incorrectly return non-standard pages to the pool instead of unmapping them
- The leak was rarely triggered until Claude Code's rise in popularity made it more visible
- Fix: Prevent non-standard pages from being recycled; they're now pruned when they reach the front of the queue

**Key Technical Debates:**
- **Rust vs Zig safety**: Extensive debate about whether Rust would have prevented this bug through its type system and Drop traits
- Mitchellh (Hashimoto) defends Zig: notes that leak-detecting allocators exist, and the issue was lack of reliable reproduction, not language choice
- Discussion of linked list vs VecDeque for scrollback; author explains linked list enables planned features like persistent scrollback and memory compression

**Community Reactions:**
- Praise for the write-up's diagrams (generated with AI assistance)
- Some surprise the fix isn't being released sooner
- Discussion of whether this level of memory management complexity is warranted for a terminal emulator

### Assessment
**Durability** (medium): The specific bug is fixed, but the discussion of memory safety patterns, type systems, and terminal architecture has lasting value. Version-specific details will age.

**Content type**: mixed — commentary on a technical blog post with substantial original discussion

**Density** (medium): Good technical signal but interspersed with repetitive Rust vs Zig debates and lower-value comments

**Originality**: commentary — community reaction to Mitchell Hashimoto's primary blog post

**Reference style**: skim-once — interesting for the technical insights but not a reference document

**Scrape quality** (good): Full comment thread captured, including Mitchell Hashimoto's responses. No code blocks or images missing that would affect comprehension.
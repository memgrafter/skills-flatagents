# Coding Agent: Diff Matching Brainstorm

## The Problem

Coder outputs SEARCH/REPLACE blocks like:
```python
<<<<<<< SEARCH
        return context
=======
        return context

    def _hello_world(self, context):
        ...
>>>>>>> REPLACE
```

But `return context` appears 11 times in the file → **ambiguous match**.

## Research: How aider Handles This

### 1. Line Numbers Don't Work
> "GPT are terrible at working with source code line numbers"
> — aider documentation

LLMs hallucinate line numbers. Files change between exploration and coding. Dead end.

### 2. Prompt Engineering
aider instructs: "include enough lines in each SEARCH section to uniquely match"

Our coder.yml already says this (line 52):
```
Include enough context lines in SEARCH to uniquely identify the location.
```
**LLM ignored it.**

### 3. Fuzzy Matching is Critical
aider uses multiple fallback strategies:
- Normalize hunks
- Detect unmarked additions
- Handle indentation variations
- Break large hunks into sub-hunks
- Vary context window size

**Disabling fuzzy matching causes 9X increase in errors.**

### 4. Unified Diff Outperforms SEARCH/REPLACE
On aider's laziness benchmark:
- SEARCH/REPLACE: 20%
- Unified diff: 61%

## Proposed Solutions

### Option A: Strengthen Prompt (Quick Win)
Add explicit examples showing WHY uniqueness matters:

```yaml
# BAD - appears many times:
<<<<<<< SEARCH
        return context
=======
...

# GOOD - unique context:
<<<<<<< SEARCH
    def _apply_changes(self, context: Dict[str, Any]) -> Dict[str, Any]:
        ...
        context["applied_changes"] = applied
        return context
=======
...
```

**Effort: Low | Impact: Medium**

### Option B: Pre-validate Uniqueness (Quick Win)
Before applying, count occurrences. If > 1, reject with helpful error:

```python
match_count = original.count(search)
if match_count > 1:
    lines = find_match_lines(original, search)
    errors.append(
        f"AMBIGUOUS: {match_count} matches at lines {lines}. "
        f"Include more context in SEARCH to uniquely identify location."
    )
```

Then the coder can retry with feedback.

**Effort: Low | Impact: Medium**

### Option C: Fuzzy Matching Fallback (Robust)
Implement aider-style fuzzy patching:
- Try exact match first
- If fails, normalize whitespace
- Try sliding window around expected location
- Try sub-hunks

**Effort: Medium | Impact: High**

### Option D: Switch to Unified Diff (Better Format)
```diff
--- src/coding_agent/hooks.py
+++ src/coding_agent/hooks.py
@@ -50,6 +50,7 @@
             "apply_changes": self._apply_changes,
+            "hello_world": self._hello_world,
         }
```

Pros: LLMs trained on git diffs, better benchmark scores
Cons: More complex parsing, need `@@ line,count @@` headers (which LLMs mess up)

**Effort: Medium | Impact: High**

## Recommendation

**Phase 1 (Immediate):**
1. Add match-count validation in `_apply_changes`
2. Return helpful error with line numbers for retry

**Phase 2 (Short-term):**
1. Strengthen coder prompt with explicit examples
2. Add one-more-attempt logic when match is ambiguous

**Phase 3 (If needed):**
1. Implement fuzzy matching fallback
2. Consider unified diff format for capable models

# Test Writer Token Optimization Plan

## Problem

Each agent sends full source code + additional context to the LLM. For a 500-line file with existing tests, a single round can send 10K+ tokens across 4 agents.

## Current Token Usage Per Agent

### 1. Analyzer Agent
**Sends to LLM:**
- Full source code ({{ input.source_code }})
- Uncovered lines list ({{ input.uncovered_lines }})
- Coverage percentages

**Output:** 600 tokens max

### 2. Writer Agent
**Sends to LLM:**
- Full source code ({{ input.source_code }})
- Coverage targets from analyzer ({{ input.coverage_targets }})
- Full existing tests ({{ input.existing_tests }}) - CAN BE HUGE
- Checker feedback if retry ({{ input.checker_feedback }})

**Output:** 2000 tokens max

### 3. Checker Agent
**Sends to LLM:**
- Full source code ({{ input.source_code }})
- Coverage targets ({{ input.coverage_targets }})
- Generated test code ({{ input.test_code }})

**Output:** 800 tokens max

### 4. Fixer Agent
**Sends to LLM:**
- Full source code ({{ input.source_code }})
- Full test code ({{ input.test_code }})
- Full pytest error output ({{ input.error_output }}) - CAN BE 20K+ chars

**Output:** 2000 tokens max

## Worst Case: 3 Rounds × 3 Fix Attempts

Per round: ~4 agent calls
Total: ~12 agent calls, each with full source code

---

## Optimization Plan

### Fix 1: Truncate Pytest Error Output (HIGH PRIORITY)

**File:** `src/test_writer/main.py`

**Current:** Sends full pytest output to Fixer
```python
fix_result = await fixer.call(
    ...
    error_output=f"{test_result.output}\n{test_result.error}",
    ...
)
```

**Fix:** Summarize/truncate before sending
```python
def truncate_error(output: str, max_lines: int = 50) -> str:
    """Keep first 20 + last 30 lines of error output."""
    lines = output.splitlines()
    if len(lines) <= max_lines:
        return output
    return "\n".join(lines[:20] + ["... truncated ..."] + lines[-30:])
```

**Impact:** Reduces Fixer input from 20K+ to ~2K chars

---

### Fix 2: Send Only Relevant Functions to Writer/Fixer (MEDIUM PRIORITY)

**Problem:** Full source code sent even when testing one function

**Fix:** Extract only functions identified by Analyzer
```python
def extract_functions(source: str, function_names: list[str]) -> str:
    """Extract only the functions that need testing."""
    # Use AST to extract function definitions
    # Return just those functions + imports
```

**Changes:**
1. Analyzer outputs function names
2. Orchestrator extracts just those functions
3. Writer/Fixer receive smaller context

**Impact:** 500-line file → 50-100 lines for targeted functions

---

### Fix 3: Summarize Existing Tests (MEDIUM PRIORITY)

**Problem:** Writer receives full existing test file

**Current in writer.yml:**
```yaml
{% if input.existing_tests %}
Existing tests (follow this style):
```python
{{ input.existing_tests }}
```
{% endif %}
```

**Fix:** Send only first test as style example + list of test names
```yaml
{% if input.existing_tests_sample %}
Example test (follow this style):
```python
{{ input.existing_tests_sample }}
```

Existing test names (don't duplicate):
{{ input.existing_test_names }}
{% endif %}
```

**Impact:** 200-line test file → 30 lines

---

### Fix 4: Cache Source Analysis (LOW PRIORITY)

**Problem:** Analyzer parses source code, then Writer parses it again

**Fix:** Analyzer outputs structured data that Writer can use directly
- Function signatures
- Imports needed
- Dependencies between functions

**Impact:** Eliminates redundant LLM parsing

---

### Fix 5: Skip Checker on Retry (LOW PRIORITY)

**Problem:** After Fixer fixes tests, we run Checker again

**Fix:** Trust Fixer output, skip Checker on fix iterations

**Impact:** Eliminates 1 agent call per fix attempt

---

## Implementation Order

1. **Fix 1** - Truncate errors (30 min, biggest impact)
2. **Fix 3** - Summarize existing tests (1 hr)
3. **Fix 2** - Extract relevant functions (2 hr, needs AST work)
4. **Fix 5** - Skip checker on retry (15 min)
5. **Fix 4** - Cache analysis (2 hr, architectural change)

## Estimated Token Savings

| Scenario | Before | After |
|----------|--------|-------|
| Single round, 500-line file | ~15K tokens | ~5K tokens |
| 3 rounds, 3 fix attempts | ~45K tokens | ~15K tokens |
| Large file with long tests | ~100K tokens | ~25K tokens |

## Testing

After each fix, run on the calculator.py example and compare:
1. Total agent calls
2. Input token count per agent (add logging)
3. End-to-end execution time

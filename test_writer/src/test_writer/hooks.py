"""
Test Writer Hooks - Handle coverage analysis, test execution, and file operations.
"""

import ast
import re
from pathlib import Path

from flatagents import MachineHooks
from shared.diff_utils import apply_search_replace

# Import coverage utilities from existing module
from test_writer.coverage import (
    run_coverage,
    run_tests,
    find_test_file,
    generate_test_filename,
    get_file_coverage,
)


def truncate_error(output: str, max_lines: int = 50) -> str:
    """Keep first 20 + last 30 lines, preserving key error info."""
    lines = output.splitlines()
    if len(lines) <= max_lines:
        return output
    return "\n".join(lines[:20] + ["... truncated ..."] + lines[-30:])


def extract_functions(source: str, function_names: list[str]) -> str:
    """Extract specific functions + imports from source code."""
    if not function_names:
        return source

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source  # Fall back to full source

    lines = source.splitlines()
    result_lines: set[int] = set()

    # Always include imports
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for ln in range(node.lineno - 1, getattr(node, 'end_lineno', node.lineno)):
                result_lines.add(ln)

    # Extract requested functions
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in function_names:
            start = node.lineno - 1
            if node.decorator_list:
                start = node.decorator_list[0].lineno - 1
            end = getattr(node, 'end_lineno', node.lineno)
            for ln in range(start, end):
                result_lines.add(ln)

    if not result_lines:
        return source

    sorted_lines = sorted(result_lines)
    return "\n".join(lines[ln] for ln in sorted_lines)


def summarize_existing_tests(test_code: str) -> tuple[str, list[str]]:
    """Extract first test as sample + list of test names."""
    try:
        tree = ast.parse(test_code)
    except SyntaxError:
        return test_code, []

    lines = test_code.splitlines()
    test_names: list[str] = []
    first_test: str = ""

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            test_names.append(node.name)

            if not first_test:
                start = node.lineno - 1
                if node.decorator_list:
                    start = node.decorator_list[0].lineno - 1
                end = getattr(node, 'end_lineno', node.lineno)
                first_test = "\n".join(lines[start:end])

    # Include imports in sample
    sample = ""
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for ln in range(node.lineno - 1, getattr(node, 'end_lineno', node.lineno)):
                sample += lines[ln] + "\n"

    sample += "\n" + first_test if first_test else ""

    return sample.strip(), test_names


def parse_function_names_from_analysis(analysis: str) -> list[str]:
    """Extract function names from analyzer output."""
    names = set()

    # Pattern: `function_name` or function_name()
    for match in re.finditer(r'`(\w+)`|\b(\w+)\(\)', analysis):
        name = match.group(1) or match.group(2)
        if name and not name.startswith('test_'):
            names.add(name)

    # Pattern: "def function_name"
    for match in re.finditer(r'\bdef\s+(\w+)', analysis):
        names.add(match.group(1))

    return list(names)


def write_test_file(test_code: str, test_file: str) -> None:
    """
    Write test code using Aider SEARCH/REPLACE format when detected.
    """
    code = test_code.strip()

    # Strip markdown fences
    if code.startswith("```python"):
        code = code[9:]
    elif code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]
    code = code.strip()

    path = Path(test_file)
    original = path.read_text() if path.exists() else ""

    # Apply diff (or use as full content if no SEARCH blocks)
    result = apply_search_replace(code, original)
    path.write_text(result.strip() + "\n")


class TestWriterHooks(MachineHooks):
    """Hooks for test generation and coverage analysis."""

    def on_action(self, action: str, context: dict) -> dict:
        """Route actions to appropriate handlers."""
        handlers = {
            "init_coverage": self._init_coverage,
            "prepare_write": self._prepare_write,
            "evaluate_check": self._evaluate_check,
            "write_and_run_tests": self._write_and_run_tests,
            "evaluate_fix": self._evaluate_fix,
            "check_coverage": self._check_coverage,
        }
        return handlers.get(action, lambda c: c)(context)

    def _init_coverage(self, ctx: dict) -> dict:
        """Read source, find test file, get baseline coverage."""
        target = Path(ctx["target_file"]).resolve()

        if not target.exists():
            raise FileNotFoundError(f"Target not found: {target}")

        ctx["source_code"] = target.read_text()
        test_file = find_test_file(str(target))

        if test_file:
            raw_tests = Path(test_file).read_text()
            sample, names = summarize_existing_tests(raw_tests)
            ctx["existing_tests_sample"] = sample
            ctx["existing_test_names"] = ", ".join(names)
            print(f"Found existing tests: {test_file}")
        else:
            test_file = generate_test_filename(str(target))
            ctx["existing_tests_sample"] = ""
            ctx["existing_test_names"] = ""
            print(f"Will create new test file: {test_file}")

        ctx["test_file"] = test_file

        # Get baseline coverage
        print("\n[1/5] Checking baseline coverage...")
        cov_result = run_coverage(source_dir=str(target.parent))
        current_pct, uncovered = get_file_coverage(cov_result.raw_report, str(target))

        ctx["current_coverage"] = current_pct
        ctx["uncovered_lines"] = uncovered
        ctx["round"] = 0
        ctx["fix_attempt"] = 0

        print(f"  Current coverage: {current_pct:.1f}%")
        print(f"  Target coverage: {ctx['coverage_target']}%")
        print(f"  Uncovered lines: {len(uncovered)}")

        return ctx

    def _prepare_write(self, ctx: dict) -> dict:
        """Reset check attempt, extract focused source from coverage targets."""
        ctx["check_attempt"] = 0
        ctx["checker_feedback"] = ""

        # Extract relevant functions for smaller context
        target_funcs = parse_function_names_from_analysis(ctx["coverage_targets"])
        ctx["focused_source"] = extract_functions(ctx["source_code"], target_funcs)

        print("\n[3/5] Writing tests...")

        return ctx

    def _evaluate_check(self, ctx: dict) -> dict:
        """Evaluate checker result, set feedback if needed."""
        ctx["check_attempt"] += 1
        ctx["check_passed"] = ctx["check_result"].strip().upper().startswith("PASS")

        if ctx["check_passed"]:
            print("  ✓ Tests passed quality check")
        else:
            print(f"  ✗ Quality issues found (attempt {ctx['check_attempt']}/2)")
            if ctx["check_attempt"] < 2:
                print("  Rewriting tests with feedback...")
            ctx["checker_feedback"] = ctx["check_result"]

        return ctx

    def _write_and_run_tests(self, ctx: dict) -> dict:
        """Write test file and run pytest."""
        # Reset fix attempt for this run
        if ctx["fix_attempt"] == 0:
            write_test_file(ctx["test_code"], ctx["test_file"])
            print(f"  Wrote tests to {ctx['test_file']}")
            print("\n[5/5] Running tests...")

        target = Path(ctx["target_file"])
        result = run_tests(test_file=ctx["test_file"], source_dir=str(target.parent))

        ctx["tests_passed"] = result.passed

        if result.passed:
            print(f"  ✓ Tests passed!")
        else:
            ctx["fix_attempt"] += 1
            print(f"  ✗ Tests failed (attempt {ctx['fix_attempt']}/3)")
            raw_error = f"{result.output}\n{result.error}"
            ctx["error_output"] = truncate_error(raw_error)

            if ctx["fix_attempt"] < 3:
                print("  Attempting to fix...")

        return ctx

    def _evaluate_fix(self, ctx: dict) -> dict:
        """Check for production bug, apply fix if test bug."""
        fix_result = ctx["fix_result"]
        ctx["is_production_bug"] = fix_result.strip().upper().startswith("PRODUCTION_BUG")

        if ctx["is_production_bug"]:
            print(f"\n{'='*50}")
            print("PRODUCTION BUG DETECTED")
            print(f"{'='*50}")
            print(fix_result)
        else:
            # It's a test bug fix - update the test code
            ctx["test_code"] = fix_result
            write_test_file(ctx["test_code"], ctx["test_file"])

        return ctx

    def _check_coverage(self, ctx: dict) -> dict:
        """Run coverage, update round counter."""
        old_coverage = ctx["current_coverage"]
        ctx["round"] += 1
        ctx["fix_attempt"] = 0

        target = Path(ctx["target_file"])
        cov_result = run_coverage(source_dir=str(target.parent))
        new_pct, uncovered = get_file_coverage(cov_result.raw_report, str(target))

        ctx["current_coverage"] = new_pct
        ctx["uncovered_lines"] = uncovered

        print(f"\n  Coverage: {old_coverage:.1f}% → {new_pct:.1f}%")

        # Update existing tests info for next round
        if Path(ctx["test_file"]).exists():
            raw = Path(ctx["test_file"]).read_text()
            sample, names = summarize_existing_tests(raw)
            ctx["existing_tests_sample"] = sample
            ctx["existing_test_names"] = ", ".join(names)

        if new_pct >= ctx["coverage_target"]:
            print(f"\n{'='*50}")
            print(f"SUCCESS: Coverage target reached!")
            print(f"  {old_coverage:.1f}% → {new_pct:.1f}% (target: {ctx['coverage_target']}%)")
            print(f"{'='*50}")
        elif ctx["round"] >= ctx["max_rounds"]:
            print(f"\n{'='*50}")
            print(f"INCOMPLETE: Max rounds ({ctx['max_rounds']}) reached")
            print(f"  Final coverage: {new_pct:.1f}% (target: {ctx['coverage_target']}%)")
            print(f"{'='*50}")
        else:
            print(f"\n{'='*50}")
            print(f"ROUND {ctx['round'] + 1} of {ctx['max_rounds']}")
            print(f"{'='*50}")
            print("\n[2/5] Analyzing coverage gaps...")

        return ctx

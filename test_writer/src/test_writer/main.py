"""
Test Writer - Multi-agent orchestrator for iterative test generation.

Pipeline:
1. Analyzer: Identify uncovered code
2. Writer: Generate tests
3. Checker: Validate test quality
4. Runner: Execute tests
5. Fixer: Debug failures (loop)

Exit codes:
- 0: Success (coverage target met)
- 1: Production bug detected
- 2: Max iterations reached
"""

import argparse
import asyncio
import sys
from pathlib import Path

from flatagents import FlatAgent, AgentResponse

from .coverage import (
    run_coverage,
    run_tests,
    find_test_file,
    generate_test_filename,
    get_file_coverage,
)


CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


async def analyze_coverage(
    source_code: str,
    target_file: str,
    uncovered_lines: list[int],
    current_coverage: float,
    target_coverage: int
) -> str:
    """Run analyzer agent to identify what to test."""
    agent = FlatAgent(config_file=str(CONFIG_DIR / "analyzer.yml"))

    result: AgentResponse = await agent.call(
        target_file=target_file,
        source_code=source_code,
        uncovered_lines=str(uncovered_lines),
        current_coverage=current_coverage,
        target_coverage=target_coverage
    )

    return result.content or ""


async def write_tests(
    source_code: str,
    target_file: str,
    coverage_targets: str,
    existing_tests: str | None = None,
    checker_feedback: str | None = None
) -> str:
    """Run writer agent to generate tests."""
    agent = FlatAgent(config_file=str(CONFIG_DIR / "writer.yml"))

    result: AgentResponse = await agent.call(
        target_file=target_file,
        source_code=source_code,
        coverage_targets=coverage_targets,
        existing_tests=existing_tests or "",
        checker_feedback=checker_feedback or ""
    )

    return result.content or ""


async def check_tests(
    source_code: str,
    coverage_targets: str,
    test_code: str
) -> str:
    """Run checker agent to validate test quality."""
    agent = FlatAgent(config_file=str(CONFIG_DIR / "checker.yml"))

    result: AgentResponse = await agent.call(
        source_code=source_code,
        coverage_targets=coverage_targets,
        test_code=test_code
    )

    return result.content or ""


async def fix_tests(
    source_code: str,
    test_code: str,
    error_output: str,
    attempt: int,
    max_attempts: int
) -> str:
    """Run fixer agent to debug failing tests."""
    agent = FlatAgent(config_file=str(CONFIG_DIR / "fixer.yml"))

    result: AgentResponse = await agent.call(
        source_code=source_code,
        test_code=test_code,
        error_output=error_output,
        attempt=attempt,
        max_attempts=max_attempts
    )

    return result.content or ""


def write_test_file(test_code: str, test_file: str) -> None:
    """Write test code to file."""
    # Clean up any markdown code fences
    code = test_code.strip()
    if code.startswith("```python"):
        code = code[9:]
    if code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]

    Path(test_file).write_text(code.strip() + "\n")


async def run(
    target: str,
    coverage_target: int = 80,
    max_rounds: int = 3
) -> int:
    """
    Main orchestrator loop.

    Returns exit code:
    - 0: Success
    - 1: Production bug
    - 2: Max iterations
    """
    target_path = Path(target).resolve()

    if not target_path.exists():
        print(f"ERROR: Target not found: {target}")
        return 2

    # Read source code
    source_code = target_path.read_text()

    # Find or generate test file path
    test_file = find_test_file(str(target_path))
    if test_file:
        existing_tests = Path(test_file).read_text()
        print(f"Found existing tests: {test_file}")
    else:
        test_file = generate_test_filename(str(target_path))
        existing_tests = None
        print(f"Will create new test file: {test_file}")

    # Get baseline coverage
    print("\n[1/5] Checking baseline coverage...")
    cov_result = run_coverage(source_dir=str(target_path.parent))
    current_pct, uncovered = get_file_coverage(cov_result.raw_report, str(target_path))

    print(f"  Current coverage: {current_pct:.1f}%")
    print(f"  Target coverage: {coverage_target}%")
    print(f"  Uncovered lines: {len(uncovered)}")

    if current_pct >= coverage_target:
        print(f"\n✓ Coverage already at {current_pct:.1f}% (target: {coverage_target}%)")
        return 0

    # Main loop - multiple rounds of test generation
    for round_num in range(max_rounds):
        print(f"\n{'='*50}")
        print(f"ROUND {round_num + 1} of {max_rounds}")
        print(f"{'='*50}")

        # Step 1: Analyze coverage gaps
        print("\n[2/5] Analyzing coverage gaps...")
        coverage_targets = await analyze_coverage(
            source_code=source_code,
            target_file=str(target_path),
            uncovered_lines=uncovered,
            current_coverage=current_pct,
            target_coverage=coverage_target
        )
        print(f"  Identified targets for testing")

        # Step 2: Write tests
        print("\n[3/5] Writing tests...")
        test_code = await write_tests(
            source_code=source_code,
            target_file=str(target_path),
            coverage_targets=coverage_targets,
            existing_tests=existing_tests
        )

        # Step 3: Check test quality (up to 2 attempts)
        print("\n[4/5] Checking test quality...")
        for check_attempt in range(2):
            check_result = await check_tests(
                source_code=source_code,
                coverage_targets=coverage_targets,
                test_code=test_code
            )

            if check_result.strip().upper().startswith("PASS"):
                print("  ✓ Tests passed quality check")
                break

            print(f"  ✗ Quality issues found (attempt {check_attempt + 1}/2)")
            if check_attempt < 1:
                print("  Rewriting tests with feedback...")
                test_code = await write_tests(
                    source_code=source_code,
                    target_file=str(target_path),
                    coverage_targets=coverage_targets,
                    existing_tests=existing_tests,
                    checker_feedback=check_result
                )

        # Write tests to file
        write_test_file(test_code, test_file)
        print(f"  Wrote tests to {test_file}")

        # Step 4: Run tests and fix loop
        print("\n[5/5] Running tests...")
        max_fix_attempts = 3

        for fix_attempt in range(max_fix_attempts):
            test_result = run_tests(test_file=test_file, source_dir=str(target_path.parent))

            if test_result.passed:
                print(f"  ✓ Tests passed!")
                break

            print(f"  ✗ Tests failed (attempt {fix_attempt + 1}/{max_fix_attempts})")

            if fix_attempt >= max_fix_attempts - 1:
                print(f"\nFAILED: Could not fix tests after {max_fix_attempts} attempts")
                print(f"\nLast error:\n{test_result.output}\n{test_result.error}")
                return 2

            # Try to fix
            print("  Attempting to fix...")
            fix_result = await fix_tests(
                source_code=source_code,
                test_code=test_code,
                error_output=f"{test_result.output}\n{test_result.error}",
                attempt=fix_attempt + 1,
                max_attempts=max_fix_attempts
            )

            if fix_result.strip().upper().startswith("PRODUCTION_BUG"):
                print(f"\n{'='*50}")
                print("PRODUCTION BUG DETECTED")
                print(f"{'='*50}")
                print(fix_result)
                return 1

            test_code = fix_result
            write_test_file(test_code, test_file)

        # Check coverage after this round
        cov_result = run_coverage(source_dir=str(target_path.parent))
        new_pct, uncovered = get_file_coverage(cov_result.raw_report, str(target_path))

        print(f"\n  Coverage: {current_pct:.1f}% → {new_pct:.1f}%")

        if new_pct >= coverage_target:
            print(f"\n{'='*50}")
            print(f"SUCCESS: Coverage target reached!")
            print(f"  {current_pct:.1f}% → {new_pct:.1f}% (target: {coverage_target}%)")
            print(f"{'='*50}")
            return 0

        current_pct = new_pct
        existing_tests = Path(test_file).read_text()

    # Max rounds reached
    print(f"\n{'='*50}")
    print(f"INCOMPLETE: Max rounds ({max_rounds}) reached")
    print(f"  Final coverage: {current_pct:.1f}% (target: {coverage_target}%)")
    print(f"{'='*50}")
    return 2


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Write tests to reach a coverage target"
    )
    parser.add_argument(
        "target",
        help="Python file or directory to test"
    )
    parser.add_argument(
        "--target", "-t",
        dest="coverage_target",
        type=int,
        default=80,
        help="Coverage percentage to reach (default: 80)"
    )
    parser.add_argument(
        "--max-rounds", "-r",
        type=int,
        default=3,
        help="Maximum test generation rounds (default: 3)"
    )

    args = parser.parse_args()

    exit_code = asyncio.run(run(
        target=args.target,
        coverage_target=args.coverage_target,
        max_rounds=args.max_rounds
    ))

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

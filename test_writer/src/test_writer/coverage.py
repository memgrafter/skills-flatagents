"""Coverage helpers for running pytest-cov and parsing results."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from dataclasses import dataclass


@dataclass
class CoverageResult:
    """Result from running coverage."""
    percentage: float
    total_lines: int
    covered_lines: int
    missing_lines: dict[str, list[int]]  # file -> [line numbers]
    raw_report: dict


@dataclass
class TestResult:
    """Result from running pytest."""
    passed: bool
    exit_code: int
    output: str
    error: str


def run_coverage(
    test_dir: str = "tests",
    source_dir: str = ".",
    target_file: str | None = None
) -> CoverageResult:
    """
    Run pytest with coverage and return parsed results.

    Args:
        test_dir: Directory containing tests
        source_dir: Source directory to measure coverage for
        target_file: Optional specific file to measure coverage for

    Returns:
        CoverageResult with coverage percentage and details
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "coverage.json"

        # Use sys.executable to ensure we use pytest from the same venv
        cmd = [
            sys.executable, "-m", "pytest", test_dir,
            f"--cov={source_dir}",
            f"--cov-report=json:{json_path}",
            "--cov-report=term",
            "-q",  # Quiet mode
        ]

        if target_file:
            cmd.append(f"--cov={target_file}")

        # Add source directory to PYTHONPATH
        env = dict(os.environ)
        source_path = str(Path(source_dir).resolve())
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = f"{source_path}:{env['PYTHONPATH']}"
        else:
            env["PYTHONPATH"] = source_path

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
            env=env
        )

        # Parse coverage JSON
        try:
            with open(json_path) as f:
                report = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # No coverage data - return zeros
            return CoverageResult(
                percentage=0.0,
                total_lines=0,
                covered_lines=0,
                missing_lines={},
                raw_report={}
            )

        # Extract missing lines per file
        missing_lines = {}
        for filepath, file_data in report.get("files", {}).items():
            missing = file_data.get("missing_lines", [])
            if missing:
                missing_lines[filepath] = missing

        totals = report.get("totals", {})

        return CoverageResult(
            percentage=totals.get("percent_covered", 0.0),
            total_lines=totals.get("num_statements", 0),
            covered_lines=totals.get("covered_lines", 0),
            missing_lines=missing_lines,
            raw_report=report
        )


def get_file_coverage(report: dict, target_file: str) -> tuple[float, list[int]]:
    """
    Get coverage info for a specific file.

    Returns:
        Tuple of (coverage_percentage, list_of_uncovered_lines)
    """
    # Normalize path
    target_path = Path(target_file).resolve()

    for filepath, file_data in report.get("files", {}).items():
        if Path(filepath).resolve() == target_path:
            summary = file_data.get("summary", {})
            pct = summary.get("percent_covered", 0.0)
            missing = file_data.get("missing_lines", [])
            return pct, missing

    return 0.0, []


def run_tests(
    test_file: str | None = None,
    test_dir: str = "tests",
    source_dir: str = "."
) -> TestResult:
    """
    Run pytest and return results.

    Args:
        test_file: Optional specific test file to run
        test_dir: Test directory (used if test_file not specified)
        source_dir: Directory containing source files (added to PYTHONPATH)

    Returns:
        TestResult with pass/fail status and output
    """
    # Use sys.executable to ensure we use pytest from the same venv
    cmd = [sys.executable, "-m", "pytest", "-v"]

    if test_file:
        cmd.append(test_file)
    else:
        cmd.append(test_dir)

    # Add source directory to PYTHONPATH so imports work
    env = dict(os.environ)
    source_path = str(Path(source_dir).resolve())
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{source_path}:{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = source_path

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
        env=env
    )

    return TestResult(
        passed=result.returncode == 0,
        exit_code=result.returncode,
        output=result.stdout,
        error=result.stderr
    )


def find_test_file(source_file: str, test_dir: str = "tests") -> str | None:
    """
    Find existing test file for a source file.

    Looks for patterns like:
    - tests/test_<name>.py
    - tests/<name>_test.py
    - test_<name>.py
    """
    source_path = Path(source_file)
    source_name = source_path.stem

    patterns = [
        Path(test_dir) / f"test_{source_name}.py",
        Path(test_dir) / f"{source_name}_test.py",
        Path(f"test_{source_name}.py"),
    ]

    for pattern in patterns:
        if pattern.exists():
            return str(pattern)

    return None


def generate_test_filename(source_file: str, test_dir: str = "tests") -> str:
    """Generate a test filename for a source file."""
    source_path = Path(source_file)
    source_name = source_path.stem

    # Ensure test directory exists
    Path(test_dir).mkdir(parents=True, exist_ok=True)

    return str(Path(test_dir) / f"test_{source_name}.py")

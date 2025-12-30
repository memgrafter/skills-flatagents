"""
Shell Analyzer - Execute commands and analyze output with validated citations.

Pipeline:
1. Run shell command, capture output
2. Add line numbers to output
3. Send to analyzer agent (Cerebras)
4. Validate all citations against original output
5. Return summary with validation status

Output styles:
- compact (default): Status line + brief summary, cite only errors
- detailed: Full sections with all citations
- minimal: Just status + one sentence
- errors-only: Only output if there are problems
"""

import argparse
import asyncio
import re
import subprocess
import sys
from pathlib import Path

from flatagents import FlatAgent, AgentResponse


VALID_STYLES = ["compact", "detailed", "minimal", "errors-only"]


def run_command(command: str, timeout: int = 120) -> tuple[str, str, int]:
    """Execute a shell command and return (stdout, stderr, exit_code)."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", f"Command timed out after {timeout} seconds", 124
    except Exception as e:
        return "", f"Failed to execute command: {e}", 1


def add_line_numbers(text: str) -> tuple[str, list[str]]:
    """Add line numbers to text. Returns (numbered_text, original_lines)."""
    lines = text.splitlines()
    numbered_lines = []
    for i, line in enumerate(lines, 1):
        numbered_lines.append(f"{i:4d}: {line}")
    return "\n".join(numbered_lines), lines


def parse_citations(agent_output: str) -> list[tuple[int, str]]:
    """
    Parse citations from agent output.
    Expected format: [LINE_NUMBER] exact content or `LINE_NUMBER:exact content`
    Returns list of (line_number, content) tuples.
    """
    citations = []
    # Match backtick-wrapped citations: `123:content here`
    pattern = r'`(\d+):([^`]+)`'
    matches = re.findall(pattern, agent_output)
    for line_num_str, content in matches:
        try:
            line_num = int(line_num_str)
            citations.append((line_num, content))
        except ValueError:
            continue

    # Also match bracket format: [123] content here
    pattern2 = r'\[(\d+)\]\s*(.+?)(?=\n\[|\n\n|$)'
    matches2 = re.findall(pattern2, agent_output, re.MULTILINE)
    for line_num_str, content in matches2:
        try:
            line_num = int(line_num_str)
            citations.append((line_num, content.strip()))
        except ValueError:
            continue

    return citations


def validate_citations(
    citations: list[tuple[int, str]],
    original_lines: list[str]
) -> tuple[bool, list[str]]:
    """
    Validate that each citation matches the original output.
    Returns (all_valid, list_of_error_messages).
    """
    errors = []

    for line_num, cited_content in citations:
        if line_num < 1 or line_num > len(original_lines):
            errors.append(
                f"[{line_num}] Invalid line number (output has {len(original_lines)} lines)"
            )
            continue

        original_content = original_lines[line_num - 1]  # Convert to 0-indexed

        # Check for exact match
        if cited_content != original_content:
            # Check if it's a substring (agent may have truncated)
            if cited_content in original_content or original_content in cited_content:
                # Partial match - acceptable
                pass
            else:
                errors.append(
                    f"[{line_num}] MISMATCH: cited \"{cited_content[:60]}...\" vs original"
                )

    has_hard_mismatch = any("MISMATCH" in e for e in errors)
    return not has_hard_mismatch, errors


def format_validation_compact(
    all_valid: bool,
    errors: list[str],
    citation_count: int
) -> str:
    """Compact validation format."""
    if citation_count == 0:
        return ""

    if all_valid:
        return f"✓ {citation_count} citation(s) verified"

    result = f"✗ Validation failed:\n"
    for error in errors[:3]:  # Limit to 3 errors
        result += f"  {error}\n"
    if len(errors) > 3:
        result += f"  ...and {len(errors) - 3} more\n"
    return result


def format_validation_detailed(
    all_valid: bool,
    errors: list[str],
    citation_count: int
) -> str:
    """Detailed validation format."""
    if citation_count == 0:
        return "\n## Validation\nNo citations to validate."

    if all_valid:
        return f"\n## Validation\n✓ All {citation_count} cited line(s) verified in original output."

    result = f"\n## Validation\n✗ FAILED - Citation verification errors:\n"
    for error in errors:
        result += f"  - {error}\n"
    return result


async def analyze(
    command: str,
    numbered_output: str,
    exit_code: int,
    style: str
) -> str:
    """Run the analyzer agent on the command output."""
    config_dir = Path(__file__).parent.parent.parent / 'config'
    agent = FlatAgent(config_file=str(config_dir / 'analyzer.yml'))

    result: AgentResponse = await agent.call(
        command=command,
        exit_code=exit_code,
        numbered_output=numbered_output,
        style=style
    )

    return result.content or ""


async def run(command: str, style: str = "compact") -> str:
    """
    Main pipeline: execute command, analyze, validate, return result.
    """
    # Step 1: Run the command
    stdout, stderr, exit_code = run_command(command)

    # Combine stdout and stderr
    combined_output = stdout
    if stderr:
        combined_output += "\n--- STDERR ---\n" + stderr if stdout else stderr

    # Handle empty output
    if not combined_output.strip():
        combined_output = "(no output)"

    # Step 2: Add line numbers
    numbered_output, original_lines = add_line_numbers(combined_output)

    # Step 3: Analyze with agent
    agent_output = await analyze(command, numbered_output, exit_code, style)

    # Step 4: Validate citations
    citations = parse_citations(agent_output)
    all_valid, errors = validate_citations(citations, original_lines)

    # Step 5: Format based on style
    if style == "errors-only":
        # Only output if there were problems
        if exit_code == 0 and all_valid and not errors:
            return f"✓ Command succeeded (exit 0)"
        # Fall through to show the analysis

    if style == "minimal":
        # Extract just the first sentence of summary
        lines = agent_output.strip().split('\n')
        summary_line = ""
        for line in lines:
            if line.strip() and not line.startswith('#') and not line.startswith('-') and not line.startswith('[') and not line.startswith('`'):
                summary_line = line.strip()
                break
        status = "✓" if exit_code == 0 else "✗"
        validation = "" if all_valid else " [citations unverified]"
        return f"{status} (exit {exit_code}): {summary_line}{validation}"

    if style == "compact":
        validation_section = format_validation_compact(all_valid, errors, len(citations))
        if validation_section:
            return agent_output.strip() + "\n" + validation_section
        return agent_output.strip()

    # detailed style
    validation_section = format_validation_detailed(all_valid, errors, len(citations))
    return agent_output + validation_section


def main():
    """Entry point for command-line invocation."""
    parser = argparse.ArgumentParser(description="Analyze shell command output")
    parser.add_argument("--style", "-s", choices=VALID_STYLES, default="compact",
                        help="Output style: compact, detailed, minimal, errors-only")
    parser.add_argument("command", nargs="+", help="Shell command to execute")

    args = parser.parse_args()
    command = " ".join(args.command)

    result = asyncio.run(run(command, args.style))
    print(result)


if __name__ == "__main__":
    main()

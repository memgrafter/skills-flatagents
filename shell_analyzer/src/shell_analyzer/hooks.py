"""
Shell Analyzer Hooks - Handle command execution and citation validation.
"""

import re
import subprocess
from flatagents import MachineHooks


class ShellAnalyzerHooks(MachineHooks):
    """Hooks for shell command execution and output validation."""

    def on_action(self, action: str, context: dict) -> dict:
        """Route actions to appropriate handlers."""
        if action == "run_command":
            return self._run_command(context)
        elif action == "validate_citations":
            return self._validate_citations(context)
        return context

    def _run_command(self, context: dict) -> dict:
        """Execute shell command and add line numbers to output."""
        command = context["command"]
        timeout = 120

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            stdout, stderr, exit_code = result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            stdout, stderr, exit_code = "", f"Command timed out after {timeout} seconds", 124
        except Exception as e:
            stdout, stderr, exit_code = "", f"Failed to execute command: {e}", 1

        # Combine stdout and stderr
        combined_output = stdout
        if stderr:
            combined_output += "\n--- STDERR ---\n" + stderr if stdout else stderr

        # Handle empty output
        if not combined_output.strip():
            combined_output = "(no output)"

        # Add line numbers
        lines = combined_output.splitlines()
        numbered_lines = []
        for i, line in enumerate(lines, 1):
            numbered_lines.append(f"{i:4d}: {line}")

        context["exit_code"] = exit_code
        context["numbered_output"] = "\n".join(numbered_lines)
        context["original_lines"] = lines
        return context

    def _validate_citations(self, context: dict) -> dict:
        """Parse citations from analysis and validate against original output."""
        analysis = context["analysis"]
        original_lines = context["original_lines"]
        style = context["style"]
        exit_code = context["exit_code"]

        # Parse citations
        citations = self._parse_citations(analysis)

        # Validate citations
        all_valid, errors = self._validate(citations, original_lines)

        # Format output based on style
        context["formatted_output"] = self._format_output(
            analysis, all_valid, errors, len(citations), style, exit_code
        )
        return context

    def _parse_citations(self, agent_output: str) -> list[tuple[int, str]]:
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

    def _validate(
        self,
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

            # Check for exact match or substring match
            if cited_content != original_content:
                if cited_content in original_content or original_content in cited_content:
                    # Partial match - acceptable
                    pass
                else:
                    errors.append(
                        f"[{line_num}] MISMATCH: cited \"{cited_content[:60]}...\" vs original"
                    )

        has_hard_mismatch = any("MISMATCH" in e for e in errors)
        return not has_hard_mismatch, errors

    def _format_output(
        self,
        analysis: str,
        all_valid: bool,
        errors: list[str],
        citation_count: int,
        style: str,
        exit_code: int
    ) -> str:
        """Format final output based on style."""
        if style == "errors-only":
            # Only output if there were problems
            if exit_code == 0 and all_valid and not errors:
                return f"✓ Command succeeded (exit 0)"
            # Fall through to show the analysis

        if style == "minimal":
            # Extract just the first sentence of summary
            lines = analysis.strip().split('\n')
            summary_line = ""
            for line in lines:
                if line.strip() and not line.startswith('#') and not line.startswith('-') and not line.startswith('[') and not line.startswith('`'):
                    summary_line = line.strip()
                    break
            status = "✓" if exit_code == 0 else "✗"
            validation = "" if all_valid else " [citations unverified]"
            return f"{status} (exit {exit_code}): {summary_line}{validation}"

        if style == "compact":
            validation_section = self._format_validation_compact(all_valid, errors, citation_count)
            if validation_section:
                return analysis.strip() + "\n" + validation_section
            return analysis.strip()

        # detailed style
        validation_section = self._format_validation_detailed(all_valid, errors, citation_count)
        return analysis + validation_section

    def _format_validation_compact(
        self,
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

    def _format_validation_detailed(
        self,
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

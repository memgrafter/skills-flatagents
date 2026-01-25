"""
Codebase Ripper Hooks

Shotgun approach: generate many commands, execute all, filter results.

Features:
- Command allowlist with explicit syntax patterns
- Bash escape blocking
- Parallel execution
- Bulk output collection
"""

import subprocess
import json
import re
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False

from flatagents import MachineHooks

logger = logging.getLogger(__name__)


# =============================================================================
# COMMAND ALLOWLIST
# =============================================================================

ALLOWED_COMMANDS = {
    "tree": {
        "description": "Show directory structure",
        "syntax": "tree [OPTIONS] [PATH]",
        "allowed_flags": ["-L", "-d", "-I", "--noreport", "-a", "-f", "-P"],
        "examples": [
            "tree -L 2",
            "tree -L 3 src/",
            "tree -L 2 -I '__pycache__|node_modules|.git'",
            "tree -d -L 2",
        ],
    },
    "rg": {
        "description": "Search file contents with ripgrep",
        "syntax": "rg [OPTIONS] PATTERN [PATH]",
        "allowed_flags": [
            "-i", "--ignore-case",
            "-w", "--word-regexp",
            "-l", "--files-with-matches",
            "-c", "--count",
            "-n", "--line-number",
            "-A", "-B", "-C",  # context lines
            "-t", "--type",
            "-g", "--glob",
            "-e", "--regexp",
            "--no-heading",
            "--hidden",
            "-m", "--max-count",
            "-o", "--only-matching",
        ],
        "examples": [
            "rg 'def.*init' -t py",
            "rg 'import|from.*import' -t py",
            "rg 'class.*:' -t py -A 5",
            "rg 'TODO|FIXME' -t py -t js",
            "rg -l 'error|exception' -i",
        ],
    },
    "fd": {
        "description": "Find files by name",
        "syntax": "fd [OPTIONS] [PATTERN] [PATH]",
        "allowed_flags": [
            "-e", "--extension",
            "-t", "--type",
            "-d", "--max-depth",
            "-H", "--hidden",
            "-I", "--no-ignore",
            "-g", "--glob",
            "-a", "--absolute-path",
        ],
        "examples": [
            "fd -e py",
            "fd -e py -e yml",
            "fd 'test.*\\.py$'",
            "fd -t f -d 3",
        ],
    },
    "head": {
        "description": "Show first lines of a file",
        "syntax": "head [OPTIONS] FILE",
        "allowed_flags": ["-n", "-c"],
        "examples": [
            "head -n 50 README.md",
            "head -n 100 src/main.py",
        ],
    },
    "cat": {
        "description": "Show entire file contents",
        "syntax": "cat FILE",
        "allowed_flags": ["-n"],
        "examples": [
            "cat pyproject.toml",
            "cat -n src/config.py",
        ],
    },
    "wc": {
        "description": "Count lines/words/chars",
        "syntax": "wc [OPTIONS] FILE",
        "allowed_flags": ["-l", "-w", "-c"],
        "examples": [
            "wc -l *.py",
        ],
    },
    "ls": {
        "description": "List directory contents",
        "syntax": "ls [OPTIONS] [PATH]",
        "allowed_flags": ["-l", "-a", "-h", "-R", "-1", "-S", "-t"],
        "examples": [
            "ls -la",
            "ls -la src/",
        ],
    },
}

# Dangerous patterns to block
BLOCKED_PATTERNS = [
    r'\$\(',          # Command substitution $(...)
    r'`',             # Backtick command substitution
    r'\|',            # Pipes
    r';',             # Command chaining
    r'&&',            # Logical AND chaining
    r'\|\|',          # Logical OR chaining
    r'>',             # Output redirection
    r'<',             # Input redirection
    r'\bsudo\b',      # Privilege escalation
    r'\brm\b',        # File deletion
    r'\bmv\b',        # File moving
    r'\bcp\b',        # File copying (could overwrite)
    r'\bchmod\b',     # Permission changes
    r'\bchown\b',     # Ownership changes
    r'\bcurl\b',      # Network requests
    r'\bwget\b',      # Network requests
    r'\bnc\b',        # Netcat
    r'\beval\b',      # Eval
    r'\bexec\b',      # Exec
    r'\bsource\b',    # Source
    r'\bexport\b',    # Environment modification
    r'\.\.',          # Parent directory traversal
    r'~',             # Home directory
    r'\$\{',          # Variable expansion
    r'\$[A-Za-z]',    # Environment variables
]


class CodebaseRipperHooks(MachineHooks):
    """
    Hooks for shotgun codebase exploration.
    
    Phases:
    1. Generate: LLM produces list of commands
    2. Validate: Filter against allowlist, block dangerous patterns
    3. Execute: Run all valid commands in parallel
    4. Collect: Aggregate outputs with size limits
    5. Extract: LLM picks relevant context from bulk output
    """

    MAX_COMMANDS = 100
    MAX_OUTPUT_PER_COMMAND = 10000  # chars
    MAX_TOTAL_OUTPUT = 200000  # chars
    COMMAND_TIMEOUT = 30  # seconds
    MAX_PARALLEL = 10

    def __init__(self, working_dir: str = "."):
        self.working_dir = Path(working_dir).resolve()
        self.api_call_count = 0

        if HAS_TIKTOKEN:
            self.encoder = tiktoken.get_encoding("cl100k_base")
        else:
            self.encoder = None

    def _log(self, *parts):
        """Log progress."""
        logger.info(" ".join(str(p) for p in parts))

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if not text:
            return 0
        if self.encoder:
            return len(self.encoder.encode(text))
        return len(text) // 4

    def get_allowlist_prompt(self) -> str:
        """Generate prompt section describing allowed commands."""
        lines = ["## Allowed Commands\n"]
        for cmd, info in ALLOWED_COMMANDS.items():
            lines.append(f"### {cmd}")
            lines.append(f"{info['description']}")
            lines.append(f"Syntax: `{info['syntax']}`")
            lines.append(f"Allowed flags: {', '.join(info['allowed_flags'])}")
            lines.append("Examples:")
            for ex in info['examples']:
                lines.append(f"  - `{ex}`")
            lines.append("")
        return "\n".join(lines)

    def validate_command(self, cmd: str) -> Tuple[bool, str]:
        """
        Validate a command against allowlist and security rules.
        
        Returns: (is_valid, reason)
        """
        cmd = cmd.strip()
        if not cmd:
            return False, "empty command"

        # Check for blocked patterns
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, cmd):
                return False, f"blocked pattern: {pattern}"

        # Extract base command
        parts = cmd.split()
        base_cmd = parts[0]

        # Check if command is allowed
        if base_cmd not in ALLOWED_COMMANDS:
            return False, f"command not in allowlist: {base_cmd}"

        # Validate flags
        allowed_flags = ALLOWED_COMMANDS[base_cmd]["allowed_flags"]
        for part in parts[1:]:
            if part.startswith("-"):
                # Extract flag name (handle -n10 style)
                flag = re.match(r'^(-{1,2}[a-zA-Z][-a-zA-Z]*)', part)
                if flag:
                    flag_name = flag.group(1)
                    # Check if flag or its short/long form is allowed
                    if not any(flag_name.startswith(af) for af in allowed_flags):
                        return False, f"flag not allowed: {flag_name}"

        return True, "ok"

    def validate_commands(self, commands: List[str]) -> Tuple[List[str], List[Dict]]:
        """
        Validate a list of commands.
        
        Returns: (valid_commands, rejected_with_reasons)
        """
        valid = []
        rejected = []

        for cmd in commands[:self.MAX_COMMANDS]:
            is_valid, reason = self.validate_command(cmd)
            if is_valid:
                valid.append(cmd)
            else:
                rejected.append({"command": cmd, "reason": reason})

        return valid, rejected

    def execute_command(self, cmd: str, cwd: Path) -> Dict[str, Any]:
        """Execute a single command and return result."""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=self.COMMAND_TIMEOUT
            )
            output = result.stdout or result.stderr or "(no output)"
            
            # Truncate if too large
            if len(output) > self.MAX_OUTPUT_PER_COMMAND:
                output = output[:self.MAX_OUTPUT_PER_COMMAND] + f"\n... (truncated, {len(output)} total chars)"

            return {
                "command": cmd,
                "output": output,
                "exit_code": result.returncode,
                "truncated": len(output) > self.MAX_OUTPUT_PER_COMMAND
            }
        except subprocess.TimeoutExpired:
            return {
                "command": cmd,
                "output": "(timeout)",
                "exit_code": -1,
                "error": "timeout"
            }
        except Exception as e:
            return {
                "command": cmd,
                "output": f"(error: {e})",
                "exit_code": -1,
                "error": str(e)
            }

    def execute_all_commands(self, commands: List[str], cwd: Path) -> List[Dict[str, Any]]:
        """Execute all commands in parallel."""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.MAX_PARALLEL) as executor:
            futures = {
                executor.submit(self.execute_command, cmd, cwd): cmd
                for cmd in commands
            }
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        return results

    def aggregate_outputs(self, results: List[Dict[str, Any]]) -> str:
        """Aggregate command outputs into a single string for LLM processing."""
        lines = []
        total_chars = 0

        for r in results:
            if r.get("error"):
                continue
            
            section = f"\n### {r['command']}\n```\n{r['output']}\n```\n"
            
            if total_chars + len(section) > self.MAX_TOTAL_OUTPUT:
                lines.append(f"\n... (truncated, {len(results)} commands total)")
                break
            
            lines.append(section)
            total_chars += len(section)

        return "".join(lines)

    # =========================================================================
    # MACHINE HOOKS
    # =========================================================================

    def on_state_enter(self, state_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Track API calls and log progress."""
        if state_name in ("generate", "extract", "summarize"):
            self.api_call_count += 1
            self._log(f"state {state_name} (call {self.api_call_count})")
        
        return context

    def on_action(self, action_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Route actions to handlers."""
        handlers = {
            "get_initial_structure": self._get_initial_structure,
            "get_allowlist": self._get_allowlist,
            "validate_commands": self._validate_commands,
            "execute_commands": self._execute_commands,
            "aggregate_results": self._aggregate_results,
        }

        handler = handlers.get(action_name)
        if handler:
            return handler(context)
        return context

    def _get_initial_structure(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get initial tree structure for command generation."""
        working_dir = context.get("working_dir")
        cwd = Path(working_dir).resolve() if working_dir else self.working_dir

        result = self.execute_command("tree -L 2 --noreport", cwd)
        context["initial_structure"] = result["output"]
        
        self._log(f"structure {result['output'].count(chr(10))} lines")
        return context

    def _get_allowlist(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Inject allowlist into context for LLM."""
        context["allowlist_prompt"] = self.get_allowlist_prompt()
        return context

    def _validate_commands(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate generated commands."""
        raw_commands = context.get("generated_commands", [])
        
        # Handle string input (LLM might return as string)
        if isinstance(raw_commands, str):
            try:
                raw_commands = json.loads(raw_commands)
            except:
                # Try line-by-line parsing
                raw_commands = [
                    line.strip().lstrip("- ").strip("`")
                    for line in raw_commands.split("\n")
                    if line.strip() and not line.strip().startswith("#")
                ]

        valid, rejected = self.validate_commands(raw_commands)
        
        context["valid_commands"] = valid
        context["rejected_commands"] = rejected
        
        self._log(f"validate {len(valid)} valid, {len(rejected)} rejected")
        return context

    def _execute_commands(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all validated commands."""
        commands = context.get("valid_commands", [])
        working_dir = context.get("working_dir")
        cwd = Path(working_dir).resolve() if working_dir else self.working_dir

        results = self.execute_all_commands(commands, cwd)
        context["command_results"] = results
        
        successful = sum(1 for r in results if not r.get("error"))
        self._log(f"execute {successful}/{len(commands)} succeeded")
        return context

    def _aggregate_results(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate results for LLM extraction."""
        results = context.get("command_results", [])
        aggregated = self.aggregate_outputs(results)
        
        context["aggregated_output"] = aggregated
        context["output_tokens"] = self.count_tokens(aggregated)
        
        self._log(f"aggregate {context['output_tokens']} tokens")
        return context

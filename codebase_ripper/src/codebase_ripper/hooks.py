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
    "tail": {
        "description": "Show last lines of a file",
        "syntax": "tail [OPTIONS] FILE",
        "allowed_flags": ["-n", "-c"],
        "examples": [
            "tail -n 20 logs/error.log",
            "tail -n 50 src/main.py",
        ],
    },
    "file": {
        "description": "Determine file type (text vs binary, mime type)",
        "syntax": "file [OPTIONS] FILE",
        "allowed_flags": ["-b", "-i", "--mime-type", "--mime-encoding"],
        "examples": [
            "file src/main.py",
            "file -i unknown_asset",
            "file --mime-type data/*",
        ],
    },
    "diff": {
        "description": "Compare files line by line",
        "syntax": "diff [OPTIONS] FILE1 FILE2",
        "allowed_flags": ["-u", "-U", "-q", "-w", "-B", "-y"],
        "examples": [
            "diff file_v1.py file_v2.py",
            "diff -u original.py updated.py",
            "diff -q config.dev.json config.prod.json",
        ],
    },
    "git": {
        "description": "Git version control (read-only commands only)",
        "syntax": "git <subcommand> [OPTIONS] [ARGS]",
        "allowed_subcommands": [
            "status",       # read-only
            "log",          # read-only
            "diff",         # read-only
            "show",         # read-only
            "ls-files",     # read-only
            "blame",        # read-only
            "describe",     # read-only
            "rev-parse",    # read-only
        ],
        # These subcommands are only allowed with flags, no positional args
        # (to prevent "git remote add", "git branch -d foo", etc.)
        "list_only_subcommands": ["remote", "branch", "tag"],
        "allowed_flags": [
            "-n", "--oneline", "--graph", "--decorate", "--stat",
            "--name-only", "--name-status", "--cached", "-p",
            "--since", "--until", "--author", "--grep",
            "-w", "-L", "-C", "-M", "--no-merges", "--first-parent",
            "-a", "-v", "-l", "-r", "--list", "--all", "--tags",
            "--show-current", "--abbrev-ref", "--abbrev-commit",
            "--merged", "--no-merged", "--contains", "--points-at",
            "--short", "--porcelain", "-s", "--quiet",
        ],
        "examples": [
            "git status",
            "git log --oneline -20",
            "git branch -a",
            "git diff HEAD~1 --name-only",
            "git show HEAD:path/to/file.py",
            "git remote -v",
            "git tag -l",
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
    r'(^|\s)~/?',     # Home directory expansion (starts with ~ or ~/)
    r'/~[a-zA-Z]',    # User home reference (/~user)
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
    MAX_INITIAL_CONTEXT_OUTPUT = 2000  # chars per initial command
    MAX_ACCEPTED_COMMANDS_HISTORY = 50  # commands to include in history
    MAX_REJECTED_COMMANDS_HISTORY = 20  # rejections to include in history
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
            # Show subcommands for git
            if "allowed_subcommands" in info:
                lines.append(f"Allowed subcommands: {', '.join(info['allowed_subcommands'])}")
            lines.append(f"Allowed flags: {', '.join(info['allowed_flags'])}")
            lines.append("Examples:")
            for ex in info['examples']:
                lines.append(f"  - `{ex}`")
            lines.append("")
        return "\n".join(lines)

    def get_blocked_patterns_prompt(self) -> str:
        """Generate prompt section describing blocked patterns."""
        lines = ["The following patterns are BLOCKED and will cause command rejection:"]
        pattern_descriptions = {
            r'\$\(': "Command substitution $()",
            r'`': "Backtick command substitution",
            r'\|': "Pipes (|)",
            r';': "Command chaining (;)",
            r'&&': "Logical AND chaining (&&)",
            r'\|\|': "Logical OR chaining (||)",
            r'>': "Output redirection (>)",
            r'<': "Input redirection (<)",
            r'\bsudo\b': "Privilege escalation (sudo)",
            r'\brm\b': "File deletion (rm)",
            r'\bmv\b': "File moving (mv)",
            r'\bcp\b': "File copying (cp)",
            r'\bchmod\b': "Permission changes (chmod)",
            r'\bchown\b': "Ownership changes (chown)",
            r'\bcurl\b': "Network requests (curl)",
            r'\bwget\b': "Network requests (wget)",
            r'\bnc\b': "Netcat (nc)",
            r'\beval\b': "Eval",
            r'\bexec\b': "Exec",
            r'\bsource\b': "Source",
            r'\bexport\b': "Environment modification (export)",
            r'\.\.': "Parent directory traversal (..)",
            r'(^|\s)~/?': "Home directory expansion (~/path or ~ at start of argument)",
            r'/~[a-zA-Z]': "User home reference (/~user)",
            r'\$\{': "Variable expansion (${VAR})",
            r'\$[A-Za-z]': "Environment variables ($VAR)",
        }
        for pattern in BLOCKED_PATTERNS:
            desc = pattern_descriptions.get(pattern, pattern)
            lines.append(f"- {desc}")
        return "\n".join(lines)

    def get_initial_context(self, cwd: Path) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Run default commands to establish initial context.
        
        Returns: (formatted_output, command_results)
        """
        default_commands = [
            "tree -L 2 --noreport",
            "tree -L 3 -d --noreport",  # directories only, deeper
        ]
        
        # Check for README files and add head command
        readme_files = ["README.md", "README.rst", "README.txt", "README"]
        for readme in readme_files:
            if (cwd / readme).exists():
                default_commands.append(f"head -n 200 {readme}")
                break
        
        # Check for common config files
        config_files = ["pyproject.toml", "package.json", "Cargo.toml", "go.mod", "setup.py"]
        for config in config_files:
            if (cwd / config).exists():
                default_commands.append(f"cat {config}")
                break
        
        # Run default commands
        results = self.execute_all_commands(default_commands, cwd)
        
        # Format output
        lines = []
        for r in results:
            if not r.get("error"):
                lines.append(f"$ {r['command']}")
                output = r['output']
                if len(output) > self.MAX_INITIAL_CONTEXT_OUTPUT:
                    output = output[:self.MAX_INITIAL_CONTEXT_OUTPUT]
                lines.append(output)
                lines.append("")
        
        return "\n".join(lines), results

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

        # Special handling for git subcommands
        if base_cmd == "git":
            if len(parts) < 2:
                return False, "git command requires a subcommand"
            subcommand = parts[1]
            
            git_config = ALLOWED_COMMANDS[base_cmd]
            allowed_subcommands = git_config.get("allowed_subcommands", [])
            list_only = git_config.get("list_only_subcommands", [])
            allowed_flags = git_config.get("allowed_flags", [])
            
            # Check if subcommand is allowed
            if subcommand not in allowed_subcommands and subcommand not in list_only:
                return False, f"git subcommand not allowed: {subcommand}"
            
            # For list-only subcommands (remote, branch, tag), only allow flags, no positional args
            if subcommand in list_only:
                for part in parts[2:]:
                    if not part.startswith("-"):
                        return False, f"git {subcommand}: only listing allowed, no arguments"
            
            # Validate flags
            for part in parts[2:]:
                if part.startswith("-"):
                    flag = re.match(r'^(-{1,2}[a-zA-Z][-a-zA-Z]*)', part)
                    if flag:
                        flag_name = flag.group(1)
                        if not any(flag_name.startswith(af) for af in allowed_flags):
                            return False, f"git flag not allowed: {flag_name}"
            return True, "ok"

        # Validate flags for non-git commands
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
            "get_blocked_patterns": self._get_blocked_patterns,
            "get_initial_context": self._get_initial_context_action,
            "validate_commands": self._validate_commands,
            "execute_commands": self._execute_commands,
            "aggregate_results": self._aggregate_results,
            "prepare_next_iteration": self._prepare_next_iteration,
            "update_iteration_state": self._update_iteration_state,
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

    def _get_blocked_patterns(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Inject blocked patterns into context for LLM."""
        context["blocked_patterns"] = self.get_blocked_patterns_prompt()
        return context

    def _get_initial_context_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run default commands for initial context."""
        working_dir = context.get("working_dir")
        cwd = Path(working_dir).resolve() if working_dir else self.working_dir
        
        initial_output, initial_results = self.get_initial_context(cwd)
        context["initial_context"] = initial_output
        context["initial_results"] = initial_results
        
        self._log(f"initial context {len(initial_results)} commands")
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

    def _prepare_next_iteration(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context for the next iteration."""
        iteration = context.get("iteration", 0)
        
        # Track all accepted and rejected commands across iterations
        all_accepted = context.get("all_accepted_commands", [])
        all_rejected = context.get("all_rejected_commands", [])
        
        # Add current iteration's results
        valid_cmds = context.get("valid_commands", [])
        rejected_cmds = context.get("rejected_commands", [])
        
        all_accepted.extend(valid_cmds)
        all_rejected.extend([r.get("command", "") for r in rejected_cmds])
        
        context["all_accepted_commands"] = all_accepted
        context["all_rejected_commands"] = all_rejected
        
        # Format for next iteration (use constants for history limits)
        context["accepted_commands_str"] = "\n".join(
            all_accepted[-self.MAX_ACCEPTED_COMMANDS_HISTORY:]
        )
        context["rejected_commands_str"] = "\n".join(
            f"- {r.get('command', '')} ({r.get('reason', '')})" 
            for r in rejected_cmds[-self.MAX_REJECTED_COMMANDS_HISTORY:]
        )
        context["accepted_count"] = len(all_accepted)
        
        self._log(f"iteration {iteration} complete, {len(all_accepted)} total commands")
        return context

    def _update_iteration_state(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Update iteration counter and check if we should continue."""
        iteration = context.get("iteration", 0) + 1
        max_iterations = context.get("max_iterations", 2)
        
        context["iteration"] = iteration
        context["should_continue"] = iteration < max_iterations
        
        self._log(f"iteration {iteration}/{max_iterations}")
        return context

"""
Codebase Explorer Hooks

Provides shell execution and state management for codebase exploration:
- run_tree: Execute tree commands
- run_ripgrep: Execute ripgrep commands
- read_file: Read file contents
- remove_frozen_items: Remove items from frozen state (with stash)
- restore_frozen_items: Restore stashed items
- clear_stash: Clear stash after confirmed removal
- update_token_counts: Count tokens and calculate budget metrics
"""

import subprocess
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False

from flatagents import MachineHooks

logger = logging.getLogger(__name__)


class CodebaseExplorerHooks(MachineHooks):
    """
    Hooks for codebase exploration with budget-aware frozen state management.
    """

    # Each iteration uses ~3-4 API calls (judge, extractor, summarizer, sometimes judge_confirm)
    CALLS_PER_ITERATION = 4
    MAX_API_CALLS = 50

    def __init__(self, working_dir: str = "."):
        self.working_dir = Path(working_dir).resolve()
        self.api_call_count = 0

        # Initialize token encoder
        if HAS_TIKTOKEN:
            self.encoder = tiktoken.get_encoding("cl100k_base")
        else:
            self.encoder = None
            logger.warning("tiktoken not available, using approximate token counting")

    def _log(self, *parts):
        """Log tight progress line: action count noun"""
        logger.info(" ".join(str(p) for p in parts))

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken or approximation."""
        if not text:
            return 0
        if self.encoder:
            return len(self.encoder.encode(text))
        # Approximate: ~4 chars per token
        return len(text) // 4

    def count_frozen_tokens(self, context: Dict[str, Any]) -> int:
        """Count total tokens in all frozen state."""
        total = 0

        for imp in context.get("frozen_imports", []):
            total += self.count_tokens(str(imp))

        for sig in context.get("frozen_signatures", []):
            total += self.count_tokens(str(sig))

        for seg in context.get("frozen_segments", []):
            if isinstance(seg, dict):
                total += self.count_tokens(seg.get("code", ""))
                total += self.count_tokens(seg.get("file", ""))
            else:
                total += self.count_tokens(str(seg))

        for path, digest in context.get("frozen_files", {}).items():
            total += self.count_tokens(f"{path}: {digest}")

        return total

    def on_state_enter(self, state_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Log state transitions for progress visibility."""
        iteration = context.get("iteration", 0)

        # Track API calls for agent states
        if state_name in ("judge", "extract", "summarize", "confirm_removal"):
            self.api_call_count += 1

        if state_name == "judge":
            self._log(f"iter {iteration} judge thinking")
        elif state_name == "route_action":
            # Check if we should bail early due to API call cap
            remaining_calls = self.MAX_API_CALLS - self.api_call_count
            if remaining_calls < self.CALLS_PER_ITERATION and context.get("next_action") != "done":
                self._log(f"iter {iteration} API cap approaching ({self.api_call_count}/{self.MAX_API_CALLS}), finalizing with current context")
                context["next_action"] = "done"

            action = context.get("next_action", "?")
            cmd = context.get("action_command", "")[:30] if context.get("action_command") else ""
            self._log(f"iter {iteration} route action={action} cmd={cmd}")
        elif state_name == "exec_tree":
            self._log(f"iter {iteration} exec_tree")
        elif state_name == "exec_rg":
            self._log(f"iter {iteration} exec_rg")
        elif state_name == "exec_read":
            self._log(f"iter {iteration} exec_read")
        elif state_name == "extract":
            self._log(f"iter {iteration} extracting")
        elif state_name == "summarize":
            self._log(f"iter {iteration} summarizing")
        elif state_name == "finalize":
            tokens = context.get("frozen_token_count", 0)
            context["api_call_count"] = self.api_call_count
            self._log(f"done {iteration} iterations {tokens} tokens {self.api_call_count} calls")
        return context

    def on_state_exit(self, state_name: str, context: Dict[str, Any], output: Any = None) -> Dict[str, Any]:
        """Fix list types after extraction."""
        if state_name == "extract":
            # Ensure frozen fields are lists, not strings
            for field in ["frozen_imports", "frozen_signatures", "frozen_segments"]:
                val = context.get(field)
                if val is None:
                    context[field] = []
                elif isinstance(val, str):
                    # Try to parse as JSON, otherwise make empty list
                    try:
                        parsed = json.loads(val)
                        context[field] = parsed if isinstance(parsed, list) else []
                    except:
                        context[field] = []
                elif not isinstance(val, list):
                    context[field] = []
        return context

    def on_action(self, action_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Route action to appropriate handler."""
        handlers = {
            "run_tree": self._run_tree,
            "run_ripgrep": self._run_ripgrep,
            "read_file": self._read_file,
            "remove_frozen_items": self._remove_frozen_items,
            "restore_frozen_items": self._restore_frozen_items,
            "clear_stash": self._clear_stash,
            "update_token_counts": self._update_token_counts,
        }

        handler = handlers.get(action_name)
        if handler:
            return handler(context)
        return context

    def _run_tree(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute tree command.

        Expects: context.action_command (tree command or path)
        Returns: context.latest_output, updated tree_outputs
        """
        cmd = context.get("action_command", "")

        # If just a path, prepend tree command
        if not cmd or not cmd.strip().startswith("tree"):
            path = cmd.strip() if cmd else "."
            cmd = f"tree -L 3 --noreport {path}"

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=str(self.working_dir),
                capture_output=True,
                text=True,
                timeout=30
            )
            output = result.stdout or result.stderr
        except subprocess.TimeoutExpired:
            output = "Error: tree command timed out"
        except Exception as e:
            output = f"Error: {e}"

        context["latest_output"] = output
        context["latest_action"] = "tree"

        # Append to tree_outputs
        tree_outputs = context.get("tree_outputs", [])
        tree_outputs.append({"command": cmd, "output": output})
        context["tree_outputs"] = tree_outputs

        # Log progress
        dir_count = output.count("\n") if output and not output.startswith("Error") else 0
        self._log("tree", dir_count, "lines")

        return context

    def _run_ripgrep(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute ripgrep command.

        Expects: context.action_command (rg command or pattern)
        Returns: context.latest_output, updated rg_results
        """
        cmd = context.get("action_command", "")

        # If just a pattern, prepend rg command
        if not cmd or not cmd.strip().startswith("rg"):
            pattern = cmd.strip() if cmd else "TODO"
            cmd = f"rg '{pattern}' --type-add 'code:*.{{py,js,ts,yml,yaml}}' --type code"

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=str(self.working_dir),
                capture_output=True,
                text=True,
                timeout=60
            )
            output = result.stdout or result.stderr or "(no matches)"
        except subprocess.TimeoutExpired:
            output = "Error: ripgrep command timed out"
        except Exception as e:
            output = f"Error: {e}"

        # Truncate if too large
        if len(output) > 50000:
            output = output[:50000] + "\n... (truncated)"

        context["latest_output"] = output
        context["latest_action"] = "rg"

        # Append to rg_results
        rg_results = context.get("rg_results", [])
        rg_results.append({"command": cmd, "output": output})
        context["rg_results"] = rg_results

        # Log progress
        match_count = output.count("\n") if output and not output.startswith("Error") and output != "(no matches)" else 0
        self._log("rg", match_count, "matches")

        return context

    def _read_file(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Read file contents.

        Expects: context.action_command (file path)
        Returns: context.latest_output, updated file_contents
        """
        filepath = context.get("action_command", "")

        if not filepath:
            context["latest_output"] = "Error: no file path specified"
            context["latest_action"] = "read"
            return context

        # Resolve path relative to working dir
        full_path = self.working_dir / filepath

        # Security: ensure path is within working dir
        try:
            full_path = full_path.resolve()
            if not str(full_path).startswith(str(self.working_dir)):
                context["latest_output"] = "Error: path outside working directory"
                context["latest_action"] = "read"
                return context
        except Exception:
            pass

        try:
            content = full_path.read_text()
            # Truncate if too large
            if len(content) > 100000:
                content = content[:100000] + "\n... (truncated)"
            output = content
        except FileNotFoundError:
            output = f"Error: file not found: {filepath}"
        except Exception as e:
            output = f"Error reading file: {e}"

        context["latest_output"] = output
        context["latest_action"] = "read"

        # Add to file_contents
        file_contents = context.get("file_contents", {})
        file_contents[filepath] = output
        context["file_contents"] = file_contents

        # Log progress
        line_count = output.count("\n") if output and not output.startswith("Error") else 0
        self._log("read", line_count, "lines")

        return context

    def _remove_frozen_items(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove items from frozen state and stash them for potential restore.

        Expects: context.pending_removals (list of removal specs)
        Returns: context.stashed_items (backup for restore)
        """
        removals = context.get("pending_removals", [])
        stashed = []

        for removal in removals:
            item_type = removal.get("type", "")

            if item_type == "import":
                indices = self._get_indices(removal)
                frozen_imports = context.get("frozen_imports", [])
                for idx in sorted(indices, reverse=True):
                    if 0 <= idx < len(frozen_imports):
                        item = frozen_imports.pop(idx)
                        stashed.append({
                            "type": "import",
                            "index": idx,
                            "content": item
                        })
                context["frozen_imports"] = frozen_imports

            elif item_type == "signature":
                indices = self._get_indices(removal)
                frozen_signatures = context.get("frozen_signatures", [])
                for idx in sorted(indices, reverse=True):
                    if 0 <= idx < len(frozen_signatures):
                        item = frozen_signatures.pop(idx)
                        stashed.append({
                            "type": "signature",
                            "index": idx,
                            "content": item
                        })
                context["frozen_signatures"] = frozen_signatures

            elif item_type == "segment":
                indices = self._get_indices(removal)
                frozen_segments = context.get("frozen_segments", [])
                for idx in sorted(indices, reverse=True):
                    if 0 <= idx < len(frozen_segments):
                        item = frozen_segments.pop(idx)
                        stashed.append({
                            "type": "segment",
                            "index": idx,
                            "content": item
                        })
                context["frozen_segments"] = frozen_segments

        context["stashed_items"] = stashed
        context["removal_pending"] = True

        # Update token count after removal
        context["frozen_token_count"] = self.count_frozen_tokens(context)

        # Log progress
        self._log("remove", len(stashed), "items")

        return context

    def _get_indices(self, removal: Dict[str, Any]) -> List[int]:
        """Extract indices from removal spec."""
        if "indices" in removal:
            return list(removal["indices"])
        elif "index" in removal:
            return [removal["index"]]
        return []

    def _restore_frozen_items(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Restore stashed items to frozen state.

        Expects: context.stashed_items
        Returns: items restored to frozen_*, stash cleared
        """
        stashed = context.get("stashed_items", [])

        # Sort by index to restore in correct order
        for item in sorted(stashed, key=lambda x: x.get("index", 0)):
            item_type = item.get("type", "")
            idx = item.get("index", 0)
            content = item.get("content")

            if item_type == "import":
                frozen_imports = context.get("frozen_imports", [])
                frozen_imports.insert(idx, content)
                context["frozen_imports"] = frozen_imports

            elif item_type == "signature":
                frozen_signatures = context.get("frozen_signatures", [])
                frozen_signatures.insert(idx, content)
                context["frozen_signatures"] = frozen_signatures

            elif item_type == "segment":
                frozen_segments = context.get("frozen_segments", [])
                frozen_segments.insert(idx, content)
                context["frozen_segments"] = frozen_segments

        # Log progress
        self._log("restore", len(stashed), "items")

        context["stashed_items"] = []
        context["removal_pending"] = False

        # Update token count after restore
        context["frozen_token_count"] = self.count_frozen_tokens(context)

        return context

    def _clear_stash(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Clear stash after confirmed removal."""
        context["stashed_items"] = []
        context["removal_pending"] = False
        context["pending_removals"] = []
        return context

    def _update_token_counts(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update token counts and budget projection metrics.

        Returns: frozen_token_count, summary_token_count, budget_burn_rate, projected_overage
        """
        context["frozen_token_count"] = self.count_frozen_tokens(context)
        context["summary_token_count"] = self.count_tokens(context.get("summary", ""))

        # Calculate burn rate (tokens per iteration)
        iteration = context.get("iteration", 1)
        if iteration > 0:
            context["budget_burn_rate"] = context["frozen_token_count"] // iteration
        else:
            context["budget_burn_rate"] = 0

        # Project overage
        max_iterations = context.get("max_iterations", 10)
        token_budget = context.get("token_budget", 40000)
        remaining_iterations = max_iterations - iteration

        projected_total = context["frozen_token_count"] + (
            context["budget_burn_rate"] * remaining_iterations
        )
        context["projected_overage"] = max(0, projected_total - token_budget)

        # Log progress
        iteration = context.get("iteration", 0)
        imports = len(context.get("frozen_imports", []))
        sigs = len(context.get("frozen_signatures", []))
        segs = len(context.get("frozen_segments", []))
        tokens = context["frozen_token_count"]
        budget = context.get("token_budget", 40000)
        self._log(f"iter {iteration} frozen {imports}i {sigs}s {segs}seg {tokens}/{budget} tokens")

        return context

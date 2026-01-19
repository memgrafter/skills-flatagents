"""
Coding Agent Hooks

Human-in-the-loop hooks for plan and result review.
Preserves history on rejection so agents can learn from feedback.
Also provides exploration tools (tree, ripgrep, read_file) for accurate diffs.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict

from flatagents import MachineHooks

from shared.file_write_machine import FileWriteMachine


class CodingAgentHooks(MachineHooks):
    """
    Hooks for human-in-the-loop coding workflow.
    
    Provides:
    - explore_codebase: Gather context about the working directory
    - run_tree: Execute tree command for directory structure
    - run_ripgrep: Search code with ripgrep
    - read_file: Read file contents
    - human_review_plan: Display plan and get approval/feedback
    - human_review_result: Display changes and get approval/feedback
    
    On rejection, preserves the rejected work in history so agents
    can learn from human feedback.
    """
    
    def __init__(self, working_dir: str = "."):
        """Initialize with working directory for exploration."""
        self.working_dir = Path(working_dir).resolve()

    def on_action(self, action_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Route actions to their handlers."""
        handlers = {
            "explore_codebase": self._explore_codebase,
            "run_tree": self._run_tree,
            "run_ripgrep": self._run_ripgrep,
            "read_file": self._read_file,
            "read_plan_files": self._read_plan_files,
            "human_review_plan": self._human_review_plan,
            "human_review_result": self._human_review_result,
            "apply_changes": self._apply_changes,
        }
        handler = handlers.get(action_name)
        if handler:
            return handler(context)
        return context
    
    def _explore_codebase(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gather context about the codebase.
        
        Uses tree for structure and reads README for overview.
        For deeper exploration, use run_tree, run_ripgrep, read_file actions.
        """
        # Use working_dir from context if provided, else use instance default
        working_dir = context.get("working_dir")
        if working_dir:
            path = Path(working_dir).expanduser().resolve()
        else:
            path = self.working_dir
        
        context_parts = []
        
        # Get directory structure
        try:
            result = subprocess.run(
                ["tree", "-L", "3", "-I", "__pycache__|node_modules|.git|.venv|*.pyc"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                context_parts.append(f"## Directory Structure\n```\n{result.stdout}\n```")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # tree not available, use ls
            try:
                result = subprocess.run(
                    ["ls", "-la"],
                    cwd=path,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                context_parts.append(f"## Files\n```\n{result.stdout}\n```")
            except Exception:
                context_parts.append(f"## Working Directory\n{path}")
        
        # Look for README
        for readme_name in ["README.md", "README.txt", "README"]:
            readme_path = path / readme_name
            if readme_path.exists():
                try:
                    content = readme_path.read_text()[:2000]  # Limit size
                    context_parts.append(f"## {readme_name}\n{content}")
                    break
                except Exception:
                    pass
        
        context["codebase_context"] = "\n\n".join(context_parts) or f"Working directory: {path}"
        return context
    
    def _run_tree(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute tree command.
        
        Expects: context.action_command (tree command or path)
        Returns: context.latest_output, updated tree_outputs
        """
        cmd = context.get("action_command", "")
        working_dir = context.get("working_dir")
        cwd = Path(working_dir).resolve() if working_dir else self.working_dir

        # If just a path, prepend tree command
        if not cmd or not cmd.strip().startswith("tree"):
            path = cmd.strip() if cmd else "."
            cmd = f"tree -L 3 --noreport {path}"

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=str(cwd),
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

        return context

    def _run_ripgrep(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute ripgrep command.
        
        Expects: context.action_command (rg command or pattern)
        Returns: context.latest_output, updated rg_results
        """
        cmd = context.get("action_command", "")
        working_dir = context.get("working_dir")
        cwd = Path(working_dir).resolve() if working_dir else self.working_dir

        # If just a pattern, prepend rg command
        if not cmd or not cmd.strip().startswith("rg"):
            pattern = cmd.strip() if cmd else "TODO"
            cmd = f"rg '{pattern}' --type-add 'code:*.{{py,js,ts,yml,yaml}}' --type code"

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=str(cwd),
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

        return context

    def _read_file(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Read file contents.
        
        Expects: context.action_command (file path)
        Returns: context.latest_output, updated file_contents
        """
        filepath = context.get("action_command", "")
        working_dir = context.get("working_dir")
        base_path = Path(working_dir).resolve() if working_dir else self.working_dir

        if not filepath:
            context["latest_output"] = "Error: no file path specified"
            context["latest_action"] = "read"
            return context

        # Resolve path relative to working dir
        full_path = base_path / filepath

        # Security: ensure path is within working dir
        try:
            full_path = full_path.resolve()
            if not str(full_path).startswith(str(base_path)):
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

        return context
    
    def _read_plan_files(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract file paths from the plan and read them for the coder.
        
        Looks for paths in the plan text (e.g., src/foo.py, ./lib/bar.js)
        and reads each file so the coder has exact content for SEARCH/REPLACE.
        """
        import re
        
        plan_raw = context.get("plan", "")
        if isinstance(plan_raw, dict) and 'content' in plan_raw:
            plan = plan_raw['content']
        else:
            plan = str(plan_raw)
        
        working_dir = context.get("working_dir")
        base_path = Path(working_dir).resolve() if working_dir else self.working_dir
        
        # Extract file paths from plan - look for path-like patterns
        # Matches: src/file.py, ./lib/foo.js, path/to/file.ts, etc.
        path_pattern = r'(?:^|\s|`|\[|\()(\.?/?(?:[\w.-]+/)*[\w.-]+\.(?:py|js|ts|jsx|tsx|yml|yaml|json|md|txt|sh|go|rs|rb|java|c|cpp|h|hpp|css|html|sql))(?:\s|$|`|\]|\)|:)'
        
        matches = re.findall(path_pattern, plan, re.MULTILINE)
        # Deduplicate and normalize
        paths = list(dict.fromkeys([p.lstrip('./') for p in matches]))
        
        file_contents = context.get("file_contents", {})
        files_read = []
        
        for filepath in paths[:20]:  # Limit to 20 files to avoid overwhelming context
            full_path = base_path / filepath
            
            # Security check
            try:
                full_path = full_path.resolve()
                if not str(full_path).startswith(str(base_path)):
                    continue
            except Exception:
                continue
            
            # Read file
            try:
                if full_path.exists() and full_path.is_file():
                    content = full_path.read_text()
                    # Truncate very large files
                    if len(content) > 50000:
                        content = content[:50000] + "\n... (truncated)"
                    file_contents[filepath] = content
                    files_read.append(filepath)
            except Exception:
                pass
        
        context["file_contents"] = file_contents
        
        # Log what was read
        print(f"\n📂 Read {len(files_read)} files for coder context:")
        for f in files_read:
            print(f"   - {f}")
        
        return context
    
    def _human_review_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Display the plan and get human approval or feedback.

        On rejection, saves the plan to history with feedback so
        the planner can learn from it.
        """
        plan_raw = context.get("plan", "")

        # FlatAgent wraps text in {'content': ...} - extract it
        if isinstance(plan_raw, dict) and 'content' in plan_raw:
            plan = plan_raw['content']
        else:
            plan = plan_raw

        task = context.get('task', 'Unknown')

        print("\n" + "=" * 70)
        print("📋 PLAN REVIEW")
        print("=" * 70)

        print(f"\n📝 Task: {task}\n")

        # Display plan as text (show full content)
        if plan and str(plan).strip():
            print("-" * 70)
            print(str(plan))
            print("-" * 70)
        else:
            print("[WARNING] No plan content received")

        print("\n" + "-" * 70)
        response = input("Approve plan? (y/yes to approve, or enter feedback): ").strip()

        if response.lower() in ("y", "yes", ""):
            context["plan_approved"] = True
            context["human_feedback"] = None
            print("✅ Plan approved!")
        else:
            context["plan_approved"] = False
            context["human_feedback"] = response

            # Preserve rejected plan in history
            plan_history = context.get("plan_history", [])
            plan_history.append({
                "content": plan,
                "feedback": response
            })
            context["plan_history"] = plan_history
            print(f"🔄 Feedback recorded. Revising plan...")

        print("=" * 70 + "\n")
        return context
    
    def _human_review_result(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Display the changes and get human approval or feedback.

        On rejection, saves changes to history with feedback so
        the coder can learn from it.
        """
        changes_raw = context.get("changes", "")
        issues_raw = context.get("issues", "")
        review_summary_raw = context.get("review_summary", "")

        # FlatAgent wraps text in {'content': ...} - extract it
        if isinstance(changes_raw, dict) and 'content' in changes_raw:
            changes = changes_raw['content']
        else:
            changes = changes_raw

        if isinstance(issues_raw, dict) and 'content' in issues_raw:
            issues = issues_raw['content']
        else:
            issues = issues_raw

        if isinstance(review_summary_raw, dict) and 'content' in review_summary_raw:
            review_summary = review_summary_raw['content']
        else:
            review_summary = review_summary_raw

        task = context.get('task', 'Unknown')
        iteration = context.get('iteration', '?')

        print("\n" + "=" * 70)
        print("🔍 RESULT REVIEW")
        print("=" * 70)

        print(f"\n📝 Task: {task}")
        print(f"🔄 Iteration: {iteration}\n")

        # Display changes as text
        if changes and str(changes).strip():
            print("Proposed Changes:")
            print("-" * 70)
            print(str(changes))
            print("-" * 70)
        else:
            print("[WARNING] No changes content received")

        # Display reviewer findings
        if issues and str(issues).strip():
            print(f"\n📊 Reviewer Assessment:")
            print(str(issues))

        if review_summary and str(review_summary).strip():
            print(f"\n📊 Review: {review_summary}")

        print("\n" + "-" * 70)
        response = input("Approve changes? (y/yes to approve, or enter feedback): ").strip()

        if response.lower() in ("y", "yes", ""):
            context["result_approved"] = True
            context["human_feedback"] = None
            print("✅ Changes approved!")
        else:
            context["result_approved"] = False
            context["human_feedback"] = response

            # Preserve rejected changes in history
            changes_history = context.get("changes_history", [])
            changes_history.append({
                "content": changes,
                "feedback": response,
                "issues": issues
            })
            context["changes_history"] = changes_history
            print(f"🔄 Feedback recorded. Revising changes...")

        print("=" * 70 + "\n")
        return context
    
    def _apply_changes(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply approved changes to the filesystem.
        
        Parses aider-style diff output and applies changes.
        """
        changes_raw = context.get("changes", "")
        working_dir = context.get("working_dir", ".")
        user_cwd = context.get("user_cwd")

        print("\n" + "=" * 70)
        print("📝 APPLYING CHANGES")
        print("=" * 70 + "\n")

        writer = FileWriteMachine(working_dir=working_dir, user_cwd=user_cwd)
        events = writer.apply(changes_raw)
        applied = []
        errors = []

        for event in events:
            path = event.get("path", "")
            code = event.get("code", "")
            kind = event.get("kind", "")

            if kind == "applied":
                if code == "created":
                    message = f"➕ Created: {path}"
                elif code == "modified":
                    message = f"✏️  Modified: {path}"
                elif code == "deleted":
                    message = f"🗑️  Deleted: {path}"
                elif code == "deleted_empty":
                    message = f"🗑️  Deleted (empty): {path}"
                else:
                    message = f"✏️  Modified: {path}"

                applied.append(message)
                print(f"  {message}")
                continue

            if code == "blocked":
                errors.append(f"🚫 BLOCKED: Path outside allowed directory: {path}")
                print(f"  🚫 BLOCKED: {path} (outside {event.get('safety_base')})")
            elif code == "search_not_found":
                errors.append(f"SEARCH not found in: {path}")
                print(f"  ⚠️  SEARCH not found: {path}")
            elif code == "ambiguous_match":
                match_count = event.get("match_count", 0)
                match_lines = event.get("match_lines", [])
                errors.append(
                    f"Multiple matches ({match_count}) in {path} at lines: {match_lines}"
                )
                print(
                    f"  ⚠️  AMBIGUOUS: {match_count} matches in {path} at lines {match_lines}"
                )
            elif code == "file_not_found_modify":
                errors.append(f"File not found for modify: {path}")
                print(f"  ⚠️  File not found: {path}")
            elif code == "file_not_found_delete":
                errors.append(f"File not found for delete: {path}")
                print(f"  ⚠️  File not found: {path}")
            elif code == "unknown_action":
                action = event.get("action", "")
                errors.append(f"Unknown action '{action}' for: {path}")
                print(f"  ⚠️  Unknown action '{action}': {path}")
            elif code == "exception":
                detail = event.get("detail", "")
                errors.append(f"Error with {path}: {detail}")
                print(f"  ❌ Error: {path} - {detail}")
        
        context["applied_changes"] = applied
        context["apply_errors"] = errors
        
        print(f"\n✅ Applied {len(applied)} changes")
        if errors:
            print(f"⚠️  {len(errors)} errors")
        print("=" * 70 + "\n")
        
        return context

"""
Claude Code Integration Hooks

Extends CodingAgentHooks with checkpoint/exit approval flow for
running as a Claude Code subprocess.

When approval is needed:
- Writes request to stderr
- Saves state to checkpoint file
- Exits with code 2

On resume:
- Reads decision from environment variable
- Restores state from checkpoint
- Continues execution
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from .hooks import CodingAgentHooks


class ClaudeCodingAgentHooks(CodingAgentHooks):
    """
    Hooks for Claude Code integration.

    Overrides human review methods to use checkpoint/exit instead of input().
    """

    def __init__(self, working_dir: str = "."):
        """Initialize with working directory."""
        super().__init__(working_dir)
        self._checkpoint_file = self.working_dir / ".coding_agent_checkpoint.json"

    def _checkpoint_and_exit(
        self,
        review_type: str,
        content: str,
        context: Dict[str, Any],
        task: str = ""
    ) -> None:
        """
        Save state and exit for Claude Code to handle approval.

        Args:
            review_type: "plan" or "result"
            content: The content being reviewed (plan or changes)
            context: Current machine context to checkpoint
            task: The task description
        """
        # Write approval request to stderr for Claude to display
        print(f"\n{'=' * 70}", file=sys.stderr)
        print(f"APPROVAL_NEEDED: {review_type}", file=sys.stderr)
        print(f"{'=' * 70}", file=sys.stderr)
        print(f"\nTask: {task}\n", file=sys.stderr)
        print("-" * 70, file=sys.stderr)
        print(content, file=sys.stderr)
        print("-" * 70, file=sys.stderr)

        # Save checkpoint with review type so we know where to resume
        checkpoint_data = {
            "review_type": review_type,
            "context": self._serialize_context(context)
        }
        self._checkpoint_file.write_text(json.dumps(checkpoint_data, indent=2, default=str))

        # Exit with code 2 to signal approval needed
        sys.exit(2)

    def _serialize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize context for JSON storage, handling non-serializable types."""
        serialized = {}
        for key, value in context.items():
            try:
                json.dumps(value)
                serialized[key] = value
            except (TypeError, ValueError):
                serialized[key] = str(value)
        return serialized

    def _check_approval_decision(self, review_type: str) -> Optional[str]:
        """
        Check if an approval decision was provided via environment variable.

        Returns:
            - "approved" if approved
            - feedback string if rejected
            - None if no decision available
        """
        env_var = f"CODING_AGENT_APPROVAL_{review_type.upper()}"
        decision = os.environ.get(env_var)
        if decision:
            # Clear the env var so it doesn't affect future calls
            del os.environ[env_var]
            return decision
        return None

    def _cleanup_checkpoint(self) -> None:
        """Remove checkpoint file after successful resume."""
        if self._checkpoint_file.exists():
            self._checkpoint_file.unlink()

    @classmethod
    def load_checkpoint(cls, working_dir: str = ".") -> Optional[Dict[str, Any]]:
        """
        Load checkpoint data if it exists.

        Returns:
            Checkpoint data dict with 'review_type' and 'context', or None
        """
        checkpoint_file = Path(working_dir).resolve() / ".coding_agent_checkpoint.json"
        if checkpoint_file.exists():
            try:
                return json.loads(checkpoint_file.read_text())
            except (json.JSONDecodeError, IOError):
                return None
        return None

    def _human_review_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle plan review with checkpoint/exit flow.

        Checks for approval decision in env var, otherwise checkpoints and exits.
        """
        plan_raw = context.get("plan", "")

        # FlatAgent wraps text in {'content': ...} - extract it
        if isinstance(plan_raw, dict) and 'content' in plan_raw:
            plan = plan_raw['content']
        else:
            plan = plan_raw

        task = context.get('task', 'Unknown')

        # Check for approval decision from environment
        decision = self._check_approval_decision("plan")
        if decision is None:
            # No decision yet - checkpoint and exit for Claude to handle
            self._checkpoint_and_exit(
                review_type="plan",
                content=str(plan) if plan else "[No plan content]",
                context=context,
                task=task
            )
            # _checkpoint_and_exit calls sys.exit(2), so we won't reach here

        # Got a decision from environment variable
        self._cleanup_checkpoint()
        if decision.lower() in ("approved", "y", "yes"):
            context["plan_approved"] = True
            context["human_feedback"] = None
            print("✅ Plan approved (via Claude)!", file=sys.stderr)
        else:
            context["plan_approved"] = False
            context["human_feedback"] = decision
            plan_history = context.get("plan_history", [])
            plan_history.append({"content": plan, "feedback": decision})
            context["plan_history"] = plan_history
            print(f"🔄 Feedback recorded (via Claude). Revising plan...", file=sys.stderr)

        return context

    def _human_review_result(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle result review with checkpoint/exit flow.

        Checks for approval decision in env var, otherwise checkpoints and exits.
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

        # Check for approval decision from environment
        decision = self._check_approval_decision("result")
        if decision is None:
            # Build content for review
            content_parts = [f"Iteration: {iteration}"]
            if changes and str(changes).strip():
                content_parts.append(f"\nProposed Changes:\n{changes}")
            if issues and str(issues).strip():
                content_parts.append(f"\nReviewer Assessment:\n{issues}")
            if review_summary and str(review_summary).strip():
                content_parts.append(f"\nReview Summary:\n{review_summary}")

            # No decision yet - checkpoint and exit for Claude to handle
            self._checkpoint_and_exit(
                review_type="result",
                content="\n".join(content_parts),
                context=context,
                task=task
            )
            # _checkpoint_and_exit calls sys.exit(2), so we won't reach here

        # Got a decision from environment variable
        self._cleanup_checkpoint()
        if decision.lower() in ("approved", "y", "yes"):
            context["result_approved"] = True
            context["human_feedback"] = None
            print("✅ Changes approved (via Claude)!", file=sys.stderr)
        else:
            context["result_approved"] = False
            context["human_feedback"] = decision
            changes_history = context.get("changes_history", [])
            changes_history.append({
                "content": changes,
                "feedback": decision,
                "issues": issues
            })
            context["changes_history"] = changes_history
            print(f"🔄 Feedback recorded (via Claude). Revising changes...", file=sys.stderr)

        return context

"""
File writing machine for applying Aider-style SEARCH/REPLACE blocks.

Parses multi-file diff blocks and applies them safely to disk.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from flatagents import MachineHooks


def build_operations(changes_raw: Any) -> List[Dict[str, Any]]:
    """Normalize agent output into a list of file operations."""
    if isinstance(changes_raw, dict) and "content" in changes_raw:
        changes = changes_raw["content"]
    else:
        changes = changes_raw

    if isinstance(changes, str) and changes.strip():
        return parse_diffs(changes)
    if isinstance(changes, dict) and "files" in changes:
        return changes.get("files", [])
    return []


def parse_diffs(text: str) -> List[Dict[str, Any]]:
    """
    Parse SEARCH/REPLACE blocks into file operations.

    Format:
        ```language
        filepath
        <<<<<<< SEARCH
        content to find (empty for new files)
        =======
        replacement content
        >>>>>>> REPLACE
        ```
    """
    import re

    # More flexible pattern - handles empty SEARCH for new files
    # The key fix: (.*?) between SEARCH and ======= without requiring surrounding \n
    quad_pattern = r"````([a-zA-Z]*)\n([^\n]+)\n<<<<<<< SEARCH\n?(.*?)\n?=======\n(.*?)\n>>>>>>> REPLACE\s*````"
    triple_pattern = r"```([a-zA-Z]*)\n([^\n]+)\n<<<<<<< SEARCH\n?(.*?)\n?=======\n(.*?)\n>>>>>>> REPLACE\s*```"

    blocks_by_key: Dict[tuple[str, str], Dict[str, Any]] = {}

    # Try quad backticks first
    for match in re.finditer(quad_pattern, text, re.DOTALL):
        filepath = match.group(2).strip()
        search_content = match.group(3)
        replace_content = match.group(4)
        key = (filepath, search_content)

        if not search_content.strip():
            blocks_by_key[key] = {
                "path": filepath,
                "action": "create",
                "content": replace_content,
            }
        else:
            blocks_by_key[key] = {
                "path": filepath,
                "action": "modify",
                "search": search_content,
                "replace": replace_content,
                "is_diff": True,
            }

    # Then triple backticks
    for match in re.finditer(triple_pattern, text, re.DOTALL):
        filepath = match.group(2).strip()
        search_content = match.group(3)
        replace_content = match.group(4)
        key = (filepath, search_content)

        if not search_content.strip():
            blocks_by_key[key] = {
                "path": filepath,
                "action": "create",
                "content": replace_content,
            }
        else:
            blocks_by_key[key] = {
                "path": filepath,
                "action": "modify",
                "search": search_content,
                "replace": replace_content,
                "is_diff": True,
            }

    return list(blocks_by_key.values())


def apply_operations(
    operations: List[Dict[str, Any]],
    base_path: Path,
    safety_base: Path,
) -> List[Dict[str, Any]]:
    """
    Apply a list of operations and return ordered events.

    Each event is a dict with:
      - kind: "applied" or "error"
      - code: event code (created, modified, deleted, etc.)
      - path: file path
      - optional fields: match_count, match_lines, action, detail, safety_base
    """
    events: List[Dict[str, Any]] = []

    for op in operations:
        if not isinstance(op, dict):
            continue

        path = op.get("path", "")
        action = op.get("action", "")
        content = op.get("content", "")
        search = op.get("search", "")
        replace = op.get("replace", "")
        is_diff = op.get("is_diff", False)

        if not path:
            continue

        file_path = (base_path / path).resolve()

        try:
            file_path.relative_to(safety_base)
        except ValueError:
            events.append(
                {
                    "kind": "error",
                    "code": "blocked",
                    "path": path,
                    "safety_base": str(safety_base),
                }
            )
            continue

        try:
            if action == "create":
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)
                events.append({"kind": "applied", "code": "created", "path": path})

            elif action == "modify":
                if file_path.exists():
                    original = file_path.read_text()
                    if is_diff and search:
                        match_count = original.count(search)
                        if match_count == 0:
                            events.append(
                                {
                                    "kind": "error",
                                    "code": "search_not_found",
                                    "path": path,
                                }
                            )
                        elif match_count > 1:
                            match_lines = _find_match_lines(original, search)
                            events.append(
                                {
                                    "kind": "error",
                                    "code": "ambiguous_match",
                                    "path": path,
                                    "match_count": match_count,
                                    "match_lines": match_lines,
                                }
                            )
                        else:
                            new_content = original.replace(search, replace, 1)
                            if not new_content.strip():
                                file_path.unlink()
                                events.append(
                                    {
                                        "kind": "applied",
                                        "code": "deleted_empty",
                                        "path": path,
                                    }
                                )
                            else:
                                file_path.write_text(new_content)
                                events.append(
                                    {"kind": "applied", "code": "modified", "path": path}
                                )
                    else:
                        file_path.write_text(content)
                        events.append(
                            {"kind": "applied", "code": "modified", "path": path}
                        )
                else:
                    events.append(
                        {
                            "kind": "error",
                            "code": "file_not_found_modify",
                            "path": path,
                        }
                    )

            elif action == "delete":
                if file_path.exists():
                    file_path.unlink()
                    events.append({"kind": "applied", "code": "deleted", "path": path})
                else:
                    events.append(
                        {
                            "kind": "error",
                            "code": "file_not_found_delete",
                            "path": path,
                        }
                    )
            else:
                events.append(
                    {
                        "kind": "error",
                        "code": "unknown_action",
                        "path": path,
                        "action": action,
                    }
                )
        except Exception as exc:
            events.append(
                {
                    "kind": "error",
                    "code": "exception",
                    "path": path,
                    "detail": str(exc),
                }
            )

    return events


def _find_match_lines(original: str, search: str) -> List[int]:
    """Return line numbers where the first line of SEARCH appears."""
    first_line = search.split("\n")[0]
    lines = original.split("\n")
    match_lines = []

    for i, line in enumerate(lines, 1):
        if first_line in line:
            match_lines.append(i)

    return match_lines


class FileWriteMachine:
    """Apply parsed operations to disk with safety checks."""

    def __init__(self, working_dir: str = ".", user_cwd: str | None = None) -> None:
        self.base_path = Path(working_dir).expanduser().resolve()
        self.safety_base = (
            Path(user_cwd).resolve() if user_cwd else self.base_path
        )

    def apply(self, changes_raw: Any) -> List[Dict[str, Any]]:
        """Apply changes and return ordered events."""
        operations = build_operations(changes_raw)
        return apply_operations(operations, self.base_path, self.safety_base)


class FileWriteHooks(MachineHooks):
    """Hooks for the file write machine."""

    def on_action(self, action_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if action_name == "write_files":
            return self._write_files(context)
        return context

    def _write_files(self, context: Dict[str, Any]) -> Dict[str, Any]:
        changes_raw = context.get("changes", "")
        working_dir = context.get("working_dir", ".")
        user_cwd = context.get("user_cwd")

        print("\n" + "=" * 70)
        print("APPLYING CHANGES")
        print("=" * 70 + "\n")

        writer = FileWriteMachine(working_dir=working_dir, user_cwd=user_cwd)
        events = writer.apply(changes_raw)
        applied: List[str] = []
        errors: List[str] = []

        for event in events:
            path = event.get("path", "")
            code = event.get("code", "")
            kind = event.get("kind", "")

            if kind == "applied":
                if code == "created":
                    message = f"CREATED: {path}"
                elif code == "modified":
                    message = f"MODIFIED: {path}"
                elif code == "deleted":
                    message = f"DELETED: {path}"
                elif code == "deleted_empty":
                    message = f"DELETED (empty): {path}"
                else:
                    message = f"MODIFIED: {path}"

                applied.append(message)
                print(f"  {message}")
                continue

            if code == "blocked":
                errors.append(f"BLOCKED: Path outside allowed directory: {path}")
                print(f"  BLOCKED: {path} (outside {event.get('safety_base')})")
            elif code == "search_not_found":
                errors.append(f"SEARCH not found in: {path}")
                print(f"  SEARCH not found: {path}")
            elif code == "ambiguous_match":
                match_count = event.get("match_count", 0)
                match_lines = event.get("match_lines", [])
                errors.append(
                    f"Multiple matches ({match_count}) in {path} at lines: {match_lines}"
                )
                print(
                    f"  AMBIGUOUS: {match_count} matches in {path} at lines {match_lines}"
                )
            elif code == "file_not_found_modify":
                errors.append(f"File not found for modify: {path}")
                print(f"  File not found: {path}")
            elif code == "file_not_found_delete":
                errors.append(f"File not found for delete: {path}")
                print(f"  File not found: {path}")
            elif code == "unknown_action":
                action = event.get("action", "")
                errors.append(f"Unknown action '{action}' for: {path}")
                print(f"  Unknown action '{action}': {path}")
            elif code == "exception":
                detail = event.get("detail", "")
                errors.append(f"Error with {path}: {detail}")
                print(f"  Error: {path} - {detail}")

        context["applied_changes"] = applied
        context["apply_errors"] = errors
        context["write_events"] = events

        print(f"\nApplied {len(applied)} changes")
        if errors:
            print(f"Errors: {len(errors)}")
        print("=" * 70 + "\n")

        return context

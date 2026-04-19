# Copyright (C) 2026 Trent Zock-Robbins
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0

"""Hooks for building repo maps via vendored Aider repomap."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

from flatmachines import MachineHooks


class _SkillIO:
    """Small IO adapter expected by Aider RepoMap."""

    def read_text(self, fname: str) -> str:
        try:
            return Path(fname).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""

    def tool_output(self, msg: str) -> None:
        print(msg, file=sys.stderr)

    def tool_warning(self, msg: str) -> None:
        print(f"warning: {msg}", file=sys.stderr)

    def tool_error(self, msg: str) -> None:
        print(f"error: {msg}", file=sys.stderr)


class _TokenModel:
    """Minimal model adapter exposing token_count()."""

    def token_count(self, text: str) -> int:
        if not text:
            return 0
        return max(1, len(text) // 4)


class RepoMapHooks(MachineHooks):
    """FlatMachine hooks for deterministic repo map generation."""

    def on_action(self, action_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        handlers = {
            "discover_files": self._discover_files,
            "parse_mentions": self._parse_mentions,
            "build_repo_map": self._build_repo_map,
        }
        handler = handlers.get(action_name)
        if handler:
            return handler(context)
        return context

    def _resolve_dir(self, context: Dict[str, Any]) -> Path:
        return Path(context.get("working_dir", ".")).resolve()

    def _discover_files(self, context: Dict[str, Any]) -> Dict[str, Any]:
        root = self._resolve_dir(context)
        files = self._git_files(root)
        if not files:
            files = self._walk_files(root)
        context["source_files"] = files
        context["file_count"] = len(files)
        return context

    def _git_files(self, root: Path) -> List[str]:
        if not (root / ".git").exists():
            return []
        try:
            proc = subprocess.run(
                ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                cwd=str(root),
                check=False,
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                return []
            files = []
            for rel in proc.stdout.splitlines():
                if not rel.strip():
                    continue
                abs_path = (root / rel).resolve()
                if abs_path.is_file():
                    files.append(str(abs_path))
            return files
        except Exception:
            return []

    def _walk_files(self, root: Path) -> List[str]:
        ignored_dirs = {
            ".git",
            ".hg",
            ".svn",
            "node_modules",
            "__pycache__",
            ".venv",
            "venv",
            "dist",
            "build",
        }
        files: List[str] = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in ignored_dirs and not d.startswith(".")]
            for fname in filenames:
                if fname.startswith("."):
                    continue
                path = Path(dirpath) / fname
                if path.is_file():
                    files.append(str(path.resolve()))
        return files

    def _parse_mentions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        task = str(context.get("task", "") or "")
        fnames: Set[str] = set()
        idents: Set[str] = set()

        for tok in re.findall(r"[A-Za-z0-9_./-]+", task):
            if "/" in tok or "." in tok:
                fnames.add(tok)
            if re.match(r"^[A-Za-z_][A-Za-z0-9_-]{2,}$", tok):
                idents.add(tok)

        context["mentioned_fnames"] = sorted(fnames)
        context["mentioned_idents"] = sorted(idents)[:200]
        return context

    def _build_repo_map(self, context: Dict[str, Any]) -> Dict[str, Any]:
        root = self._resolve_dir(context)
        source_files = context.get("source_files") or []
        map_tokens = int(context.get("map_tokens", 2000))
        max_context_window = int(context.get("max_context_window", 128000))
        refresh = str(context.get("refresh", "auto"))

        try:
            from aider.repomap import RepoMap
        except Exception as exc:
            context["repo_map_text"] = ""
            context["error"] = (
                "Missing repo_map runtime dependencies. Install from repo_map/pyproject.toml. "
                f"Details: {exc}"
            )
            return context

        io = _SkillIO()
        model = _TokenModel()

        repo_map = RepoMap(
            map_tokens=map_tokens,
            root=str(root),
            main_model=model,
            io=io,
            max_context_window=max_context_window,
            refresh=refresh,
            verbose=False,
        )

        try:
            text = repo_map.get_ranked_tags_map(
                chat_fnames=[],
                other_fnames=source_files,
                max_map_tokens=map_tokens,
                mentioned_fnames=set(context.get("mentioned_fnames") or []),
                mentioned_idents=set(context.get("mentioned_idents") or []),
            )
        except Exception as exc:
            context["repo_map_text"] = ""
            context["error"] = str(exc)
            return context

        context["repo_map_text"] = text or ""
        context["error"] = ""
        return context

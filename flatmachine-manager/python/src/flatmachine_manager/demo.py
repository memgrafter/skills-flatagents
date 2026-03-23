"""
Demo script — exercises the full CRUD lifecycle without an LLM.

Shows: create → validate → update → diff → list
"""

from __future__ import annotations

import asyncio
import os
import tempfile

from .registry import MachineRegistry
from .tools import (
    tool_create_machine,
    tool_deprecate_machine,
    tool_diff_versions,
    tool_duplicate_machine,
    tool_get_machine,
    tool_list_machines,
    tool_select_model,
    tool_update_machine,
    tool_validate_machine,
)


def _header(text: str) -> str:
    bar = "─" * 60
    return f"\n\033[1;36m{bar}\n  {text}\n{bar}\033[0m"


def _step(n: int, text: str) -> str:
    return f"\n\033[1;33m── Step {n}: {text} ──\033[0m"


async def run_demo(db_path: str | None = None):
    """Run the full CRUD demo."""
    # Use a temp DB so the demo is always clean
    if db_path is None:
        fd, db_path = tempfile.mkstemp(suffix=".sqlite", prefix="fm_demo_")
        os.close(fd)
        cleanup = True
    else:
        cleanup = False

    reg = MachineRegistry(db_path=db_path)

    try:
        print(_header("FlatMachine Manager — Demo"))
        print(f"  Registry: {db_path}")

        # ── Step 1: Select a model ──────────────────────────────────

        print(_step(1, "Select a model profile for the writer agent"))
        r = await tool_select_model(reg, "demo-1", {"purpose": "creative"})
        print(r.content)

        print(_step(1, "Select a model profile for the critic agent"))
        r = await tool_select_model(reg, "demo-1b", {"purpose": "fast"})
        print(r.content)

        # ── Step 2: Create a machine ────────────────────────────────

        print(_step(2, "Create a writer-critic machine for product taglines"))
        r = await tool_create_machine(reg, "demo-2", {
            "name": "tagline-writer",
            "template": "writer-critic",
            "description": "Generate and refine product taglines through iterative critique",
            "agents": [
                {
                    "name": "writer",
                    "purpose": "Generate creative, punchy product taglines. "
                               "Each draft should be a single sentence that captures "
                               "the product's essence.",
                    "model_profile": "smart",
                    "temperature": 0.9,
                },
                {
                    "name": "critic",
                    "purpose": "Score taglines 1-10 on clarity, memorability, and "
                               "brand fit. Provide specific actionable feedback.",
                    "model_profile": "fast",
                },
            ],
            "context_fields": [
                {"name": "product", "from_input": True},
                {"name": "brand_voice", "from_input": True},
            ],
        })
        assert not r.is_error, r.content
        print(r.content)

        # ── Step 3: Validate ────────────────────────────────────────

        print(_step(3, "Run full validation suite"))
        r = await tool_validate_machine(reg, "demo-3", {"name": "tagline-writer"})
        print(r.content)

        # ── Step 4: Update — raise quality threshold ────────────────

        print(_step(4, "Update: raise quality threshold from 8 → 9"))
        r = await tool_update_machine(reg, "demo-4", {
            "name": "tagline-writer",
            "operation": "update_context",
            "params": {"key": "quality_threshold", "value_template": 9},
            "description": "Raise quality bar to 9/10 for taglines",
        })
        assert not r.is_error, r.content
        print(r.content)

        # ── Step 5: Update — add a human review gate ────────────────

        print(_step(5, "Update: add human_review state after critic review"))
        r = await tool_update_machine(reg, "demo-5", {
            "name": "tagline-writer",
            "operation": "add_state",
            "params": {
                "state_name": "human_review",
                "after_state": "review",
                "description": "Human approves final tagline before shipping",
                "transitions_to": ["done", "write"],
            },
            "description": "Add human approval gate before final output",
        })
        assert not r.is_error, r.content
        print(r.content)

        # ── Step 6: Diff v1 vs v3 ──────────────────────────────────

        print(_step(6, "Diff: compare original v1 with current v3"))
        r = await tool_diff_versions(reg, "demo-6", {
            "name": "tagline-writer",
            "v1": 1,
            "v2": 3,
        })
        print(r.content)

        # ── Step 7: Create a second machine ─────────────────────────

        print(_step(7, "Create a pipeline machine for document processing"))
        r = await tool_create_machine(reg, "demo-7", {
            "name": "doc-processor",
            "template": "pipeline",
            "description": "Process documents through extract → analyze → summarize phases",
            "agents": [
                {"name": "extractor", "purpose": "Extract key facts and data from the document", "model_profile": "fast"},
                {"name": "analyzer", "purpose": "Analyze extracted data for patterns and insights", "model_profile": "smart"},
                {"name": "summarizer", "purpose": "Write a clear executive summary", "model_profile": "fast"},
            ],
        })
        assert not r.is_error, r.content
        print(r.content)

        # ── Step 8: Duplicate tagline-writer → tagline-writer-v2 ────

        print(_step(8, "Duplicate tagline-writer as tagline-writer-v2 (fork for experimentation)"))
        r = await tool_duplicate_machine(reg, "demo-8", {
            "source": "tagline-writer",
            "target": "tagline-writer-v2",
            "description": "Fork for A/B testing a more aggressive critic",
        })
        assert not r.is_error, r.content
        print(r.content)

        # ── Step 9: Deprecate original tagline-writer ───────────────

        print(_step(9, "Deprecate original tagline-writer (soft delete — config preserved)"))
        r = await tool_deprecate_machine(reg, "demo-9", {"name": "tagline-writer"})
        print(r.content)

        # ── Step 10: List active machines (original hidden) ─────────

        print(_step(10, "List active machines (deprecated ones hidden by default)"))
        r = await tool_list_machines(reg, "demo-10", {"status": "active"})
        print(r.content)

        # ── Step 11: List all machines (deprecated still visible) ───

        print(_step(11, "List ALL machines (including deprecated — nothing destroyed)"))
        r = await tool_list_machines(reg, "demo-11", {"status": "all"})
        print(r.content)

        # ── Step 12: Inspect the duplicate ──────────────────────────

        print(_step(12, "Get tagline-writer-v2 details (the surviving fork)"))
        r = await tool_get_machine(reg, "demo-12", {"name": "tagline-writer-v2"})
        lines = r.content.split("\n")
        yaml_start = next((i for i, l in enumerate(lines) if l.strip() == "```yaml"), len(lines))
        print("\n".join(lines[:yaml_start]))
        print(f"  ... (config YAML omitted for brevity)")

        # ── Done ────────────────────────────────────────────────────

        print(_header("Demo complete!"))
        print(f"  Full lifecycle: create → validate → update → diff → duplicate → deprecate")
        print(f"  3 machines registered, 5 versions total")
        print(f"  Registry: {db_path}")
        if not cleanup:
            print(f"  Inspect with: sqlite3 {db_path} '.tables'")

    finally:
        reg.close()
        if cleanup:
            try:
                os.unlink(db_path)
            except OSError:
                pass

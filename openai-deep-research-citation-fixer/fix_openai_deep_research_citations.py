#!/usr/bin/env python3
"""Fix OpenAI Deep Research citation markers in markdown files.

What this script does:
1) (when writing) creates a backup: <file>.bkp
2) replaces broken OpenAI citation/entity markers in the body
3) rebuilds a clean ## References section with anchored links
4) validates the result with direct regex match checks

It also warns when a Citations/References section is not pasted at the bottom.
Use --skip-bottom-warning to continue anyway.

Usage:
    python fix_openai_deep_research_citations.py /path/to/report.md
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


BROKEN_CITE_RE = re.compile(r"cite[^]+")
BROKEN_ENTITY_RE = re.compile(r"entity\[(.*?)\]")
URL_RE = re.compile(r"https?://[^\s<>()\[\]{}\"']+")
SECTION_HEADER_LINE_RE = re.compile(r"^\s*(?:#+\s*)?(?:citations\b.*|references\b.*)$", re.I)
MARKDOWN_HEADING_LINE_RE = re.compile(r"^\s{0,3}#{1,6}\s+\S")
REFERENCE_LINE_RE = re.compile(
    r'^\s*(\d+)\.\s*<a\s+id="ref-(\d+)"\s*>\s*</a>'
    r'\[(https?://[^\]]+)\]\((https?://[^)]+)\)\s*$',
    re.M,
)


@dataclass
class ReferenceSectionInfo:
    found: bool
    start_line: int | None
    end_line: int | None
    trailing_nonempty_lines: int
    at_bottom: bool


@dataclass
class FixStats:
    cite_markers_replaced: int
    entity_markers_replaced: int
    references_written: int
    references_removed: bool


class OpenAIDeepResearchCitationFixer:
    """Deterministic fixer for OpenAI Deep Research citation artifacts."""

    def __init__(self, markdown_text: str):
        self.original = markdown_text

    @staticmethod
    def inspect_reference_section(text: str) -> ReferenceSectionInfo:
        """Locate the last citations/references section and check bottom placement."""
        lines = text.splitlines()
        starts = [i for i, line in enumerate(lines) if SECTION_HEADER_LINE_RE.match(line)]

        if not starts:
            return ReferenceSectionInfo(
                found=False,
                start_line=None,
                end_line=None,
                trailing_nonempty_lines=0,
                at_bottom=True,
            )

        start = starts[-1]
        end = len(lines)
        for i in range(start + 1, len(lines)):
            if MARKDOWN_HEADING_LINE_RE.match(lines[i]):
                end = i
                break

        trailing_nonempty_lines = sum(1 for line in lines[end:] if line.strip())
        at_bottom = trailing_nonempty_lines == 0

        return ReferenceSectionInfo(
            found=True,
            start_line=start + 1,
            end_line=end,
            trailing_nonempty_lines=trailing_nonempty_lines,
            at_bottom=at_bottom,
        )

    @staticmethod
    def _replace_entity_markers(text: str) -> tuple[str, int]:
        def repl(match: re.Match[str]) -> str:
            inner = match.group(1)
            # Expected shape:
            # "organization","Node.js","javascript runtime project"
            try:
                parsed = json.loads(f"[{inner}]")
                if isinstance(parsed, list) and len(parsed) >= 2 and isinstance(parsed[1], str):
                    return parsed[1]
            except Exception:
                pass

            # Fallback: return 2nd quoted string if possible, else first, else empty.
            quoted = re.findall(r'"([^"]+)"', inner)
            if len(quoted) >= 2:
                return quoted[1]
            if quoted:
                return quoted[0]
            return ""

        return BROKEN_ENTITY_RE.subn(repl, text)

    @staticmethod
    def _replace_cite_markers(text: str) -> tuple[str, int]:
        return BROKEN_CITE_RE.subn("([sources](#references))", text)

    @staticmethod
    def _extract_body_and_old_references(
        text: str,
    ) -> tuple[str, str, bool, ReferenceSectionInfo]:
        info = OpenAIDeepResearchCitationFixer.inspect_reference_section(text)
        if not info.found or info.start_line is None or info.end_line is None:
            return text.rstrip(), "", False, info

        lines = text.splitlines()
        start_idx = info.start_line - 1
        end_idx = info.end_line

        old_refs = "\n".join(lines[start_idx:end_idx]).rstrip()
        body_lines = lines[:start_idx] + lines[end_idx:]
        body = "\n".join(body_lines).rstrip()
        return body, old_refs, True, info

    @staticmethod
    def _extract_unique_urls(text: str) -> list[str]:
        urls: list[str] = []
        seen: set[str] = set()

        for raw in URL_RE.findall(text):
            # Trim common trailing punctuation while preserving valid URL chars.
            url = raw.rstrip(".,);]")
            if url and url not in seen:
                seen.add(url)
                urls.append(url)

        return urls

    @staticmethod
    def _build_references_section(urls: list[str]) -> str:
        lines = ["## References", ""]
        if not urls:
            lines.append("_No source URLs found._")
            return "\n".join(lines)

        for i, url in enumerate(urls, start=1):
            lines.append(f'{i}. <a id="ref-{i}"></a>[{url}]({url})')
        return "\n".join(lines)

    def fix(self) -> tuple[str, FixStats, ReferenceSectionInfo]:
        text = self.original

        text, entity_count = self._replace_entity_markers(text)
        text, cite_count = self._replace_cite_markers(text)

        body, old_refs, had_old_refs, section_info = self._extract_body_and_old_references(text)

        # Prefer extracting URLs from old refs section when present.
        source_for_urls = old_refs if old_refs else text
        urls = self._extract_unique_urls(source_for_urls)

        references = self._build_references_section(urls)
        fixed = f"{body}\n\n{references}\n"

        stats = FixStats(
            cite_markers_replaced=cite_count,
            entity_markers_replaced=entity_count,
            references_written=len(urls),
            references_removed=had_old_refs,
        )
        return fixed, stats, section_info


def validate_fixed_markdown(
    markdown_text: str,
    expected_source_links: int | None = None,
    expected_reference_lines: int | None = None,
) -> dict[str, Any]:
    """Validate output with direct regex matching checks.

    This intentionally does strict match checks so failures are explicit.
    """
    inline_source_links = markdown_text.count("([sources](#references))")

    ref_header_present = bool(re.search(r"(?m)^##\s+References\s*$", markdown_text))
    legacy_markers_present = any(token in markdown_text for token in ("", "", ""))

    ref_lines = REFERENCE_LINE_RE.findall(markdown_text)
    ref_numbers = [int(n) for n, _, _, _ in ref_lines]
    anchor_numbers = [int(a) for _, a, _, _ in ref_lines]

    number_anchor_mismatches = [
        {"line_number": n, "anchor_number": a}
        for n, a in zip(ref_numbers, anchor_numbers)
        if n != a
    ]

    url_mismatches = [
        {"line_number": int(n), "label_url": u1, "target_url": u2}
        for n, _, u1, u2 in ref_lines
        if u1 != u2
    ]

    contiguous_ok = ref_numbers == list(range(1, len(ref_numbers) + 1))

    expected_source_match_ok = True
    if expected_source_links is not None:
        expected_source_match_ok = inline_source_links == expected_source_links

    expected_reference_match_ok = True
    if expected_reference_lines is not None:
        expected_reference_match_ok = len(ref_lines) == expected_reference_lines

    ok = (
        ref_header_present
        and not legacy_markers_present
        and not number_anchor_mismatches
        and not url_mismatches
        and contiguous_ok
        and expected_source_match_ok
        and expected_reference_match_ok
    )

    return {
        "ok": ok,
        "inline_sources_links": inline_source_links,
        "expected_inline_sources_links": expected_source_links,
        "references_header_present": ref_header_present,
        "reference_line_count": len(ref_lines),
        "expected_reference_line_count": expected_reference_lines,
        "number_anchor_mismatch_count": len(number_anchor_mismatches),
        "url_mismatch_count": len(url_mismatches),
        "contiguous_reference_numbers": contiguous_ok,
        "legacy_marker_chars_present": legacy_markers_present,
        "source_link_count_matches_expected": expected_source_match_ok,
        "reference_line_count_matches_expected": expected_reference_match_ok,
        "number_anchor_mismatches": number_anchor_mismatches,
        "url_mismatches": url_mismatches,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fix OpenAI Deep Research markdown citations. "
            "Creates <file>.bkp, rewrites citations, and validates output."
        )
    )
    parser.add_argument("markdown_file", help="Path to markdown file (e.g. report.md)")
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Do not write file; print validation for transformed content only.",
    )
    parser.add_argument(
        "--skip-bottom-warning",
        action="store_true",
        help=(
            "Continue even if Citations/References section is not at the bottom of the doc."
        ),
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help=(
            "Auto-accept warnings (currently implies --skip-bottom-warning). "
            "Useful for scripts/automation."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.markdown_file).expanduser().resolve()

    if not path.exists():
        print(json.dumps({"ok": False, "error": f"File not found: {path}"}, indent=2))
        return 1

    original = path.read_text(encoding="utf-8")
    preflight = OpenAIDeepResearchCitationFixer.inspect_reference_section(original)

    skip_bottom_warning = args.skip_bottom_warning or args.yes

    warnings: list[dict[str, Any]] = []
    if preflight.found and not preflight.at_bottom:
        warning = {
            "code": "citations_not_at_bottom",
            "message": (
                "Citations/References section is not at the bottom of the document. "
                "Please paste citations at the bottom, then rerun."
            ),
            "section_start_line": preflight.start_line,
            "section_end_line": preflight.end_line,
            "trailing_nonempty_lines": preflight.trailing_nonempty_lines,
            "can_skip_with": "--skip-bottom-warning or --yes",
        }

        if not skip_bottom_warning:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "file": str(path),
                        "warning": warning,
                        "hint": "Re-run with --skip-bottom-warning (or --yes) only if you intentionally want to proceed.",
                    },
                    indent=2,
                )
            )
            return 2

        warnings.append(warning)

    # Backup first (when writing), exactly as requested: <filename>.ext.bkp
    backup_path = Path(str(path) + ".bkp")
    if not args.no_overwrite:
        shutil.copy2(path, backup_path)

    fixer = OpenAIDeepResearchCitationFixer(original)
    fixed, stats, section_info_after_replace = fixer.fix()

    validation = validate_fixed_markdown(
        fixed,
        expected_source_links=stats.cite_markers_replaced,
        expected_reference_lines=stats.references_written,
    )

    if not args.no_overwrite:
        path.write_text(fixed, encoding="utf-8")

    report = {
        "ok": validation["ok"],
        "file": str(path),
        "backup": str(backup_path) if not args.no_overwrite else None,
        "warnings": warnings,
        "preflight_reference_section": asdict(preflight),
        "post_replace_reference_section": asdict(section_info_after_replace),
        "fix_stats": asdict(stats),
        "validation": validation,
    }
    print(json.dumps(report, indent=2))

    return 0 if validation["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

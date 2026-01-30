"""
Website Scraper Hooks - Handle URL scraping and file saving.
"""

import re
import os
import yaml
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from flatagents import MachineHooks

# Try to import trafilatura, provide helpful error if missing
try:
    import trafilatura
except ImportError:
    trafilatura = None


class WebsiteScraperHooks(MachineHooks):
    """Hooks for website scraping and file management."""

    def on_action(self, action: str, context: dict) -> dict:
        """Route actions to appropriate handlers."""
        if action == "scrape_url":
            return self._scrape_url(context)
        elif action == "validate_summary":
            return self._validate_summary(context)
        elif action == "check_judge_result":
            return self._check_judge_result(context)
        elif action == "validate_frontmatter":
            return self._validate_frontmatter(context)
        elif action == "save_files":
            return self._save_files(context)
        return context

    # ========== VALIDATION ACTIONS ==========

    def _validate_summary(self, context: dict) -> dict:
        """Programmatically validate summary has required sections."""
        summary = context.get("summary", "")
        errors = []

        # Check required sections exist (flexible header levels)
        required_sections = [
            ("TL;DR", "Missing TL;DR section"),
            ("Key Quote", "Missing Key Quote section"),
            ("Summary", "Missing Summary section"),
            ("Assessment", "Missing Assessment section"),
        ]

        for section, error_msg in required_sections:
            # Match ## or ### header
            pattern = rf"^##?#?\s*{re.escape(section)}"
            if not re.search(pattern, summary, re.MULTILINE | re.IGNORECASE):
                errors.append(error_msg)

        # Check TL;DR is not empty (has content after header)
        tldr_match = re.search(
            r"^##?#?\s*TL;DR\s*\n+(.+?)(?=\n##|\n###|\Z)",
            summary,
            re.MULTILINE | re.IGNORECASE | re.DOTALL,
        )
        if tldr_match:
            tldr_content = tldr_match.group(1).strip()
            if len(tldr_content) < 20:
                errors.append("TL;DR is too short (less than 20 chars)")
        
        # Check Key Quote has actual quoted text
        quote_match = re.search(
            r"^##?#?\s*Key Quote\s*\n+(.+?)(?=\n##|\n###|\Z)",
            summary,
            re.MULTILINE | re.IGNORECASE | re.DOTALL,
        )
        if quote_match:
            quote_content = quote_match.group(1).strip()
            if '"' not in quote_content and '"' not in quote_content and '>' not in quote_content:
                errors.append("Key Quote section doesn't contain a quoted string")

        context["summary_valid"] = len(errors) == 0
        context["summary_validation_errors"] = errors
        context["summary_attempt"] = context.get("summary_attempt", 0) + 1

        return context

    def _check_judge_result(self, context: dict) -> dict:
        """Parse judge output to determine pass/reject."""
        judge_result = context.get("judge_result", "").strip()
        
        # Check if starts with PASS or REJECT
        first_line = judge_result.split("\n")[0].strip().upper()
        
        if first_line.startswith("PASS"):
            context["judge_passed"] = True
            context["judge_feedback"] = ""
        else:
            context["judge_passed"] = False
            # Everything after REJECT is feedback
            feedback = judge_result
            if feedback.upper().startswith("REJECT"):
                feedback = feedback[6:].lstrip(":").strip()
            context["judge_feedback"] = feedback

        return context

    def _validate_frontmatter(self, context: dict) -> dict:
        """Validate frontmatter YAML structure and consistency with summary."""
        frontmatter_yaml = context.get("frontmatter_yaml", "")
        summary = context.get("summary", "")
        errors = []

        # 1. Strip code fences if present
        fm_clean = frontmatter_yaml.strip()
        if fm_clean.startswith("```"):
            fm_clean = re.sub(r"^```\w*\n?", "", fm_clean)
            fm_clean = re.sub(r"\n?```$", "", fm_clean)

        # 2. Parse YAML
        try:
            fm = yaml.safe_load(fm_clean) or {}
        except yaml.YAMLError as e:
            errors.append(f"YAML parse error: {e}")
            context["frontmatter_valid"] = False
            context["frontmatter_validation_errors"] = errors
            context["frontmatter_attempt"] = context.get("frontmatter_attempt", 0) + 1
            return context

        # 3. Required fields
        required_fields = [
            "tldr",
            "key_quote",
            "durability",
            "content_type",
            "density",
            "originality",
            "reference_style",
            "scrape_quality",
            "tags",
        ]
        for field in required_fields:
            if field not in fm or fm[field] is None:
                errors.append(f"Missing required field: {field}")

        # 4. Enum validation
        enum_fields = {
            "durability": ["low", "medium", "high"],
            "density": ["low", "medium", "high"],
            "content_type": ["fact", "opinion", "tutorial", "reference", "announcement", "mixed"],
            "originality": ["primary", "synthesis", "commentary"],
            "reference_style": ["skim-once", "refer-back", "deep-study"],
            "scrape_quality": ["good", "partial", "poor"],
        }
        for field, valid_values in enum_fields.items():
            if field in fm and fm[field] not in valid_values:
                errors.append(f"Invalid {field}: '{fm[field]}' (must be one of {valid_values})")

        # 5. Tags must be a non-empty list
        if "tags" in fm:
            if not isinstance(fm["tags"], list):
                errors.append("tags must be a list")
            elif len(fm["tags"]) == 0:
                errors.append("tags list is empty (need 3-5 tags)")

        # 6. Consistency: tldr should appear in summary's TL;DR section
        if "tldr" in fm and fm["tldr"]:
            tldr_value = fm["tldr"]
            # Extract TL;DR section from summary
            tldr_match = re.search(
                r"^##?#?\s*TL;DR\s*\n+(.+?)(?=\n##|\n###|\Z)",
                summary,
                re.MULTILINE | re.IGNORECASE | re.DOTALL,
            )
            if tldr_match:
                tldr_section = tldr_match.group(1).strip()
                # Normalize whitespace for comparison
                tldr_normalized = " ".join(tldr_value.split())
                section_normalized = " ".join(tldr_section.split())
                if tldr_normalized not in section_normalized:
                    errors.append("tldr doesn't match summary's TL;DR section")

        # 7. Consistency: key_quote should appear in summary's Key Quote section
        if "key_quote" in fm and fm["key_quote"]:
            quote_value = fm["key_quote"]
            quote_match = re.search(
                r"^##?#?\s*Key Quote\s*\n+(.+?)(?=\n##|\n###|\Z)",
                summary,
                re.MULTILINE | re.IGNORECASE | re.DOTALL,
            )
            if quote_match:
                quote_section = quote_match.group(1).strip()
                # Normalize for comparison (quotes might have slight formatting differences)
                quote_normalized = " ".join(quote_value.replace('"', '"').replace('"', '"').split())
                section_normalized = " ".join(quote_section.replace('"', '"').replace('"', '"').split())
                if quote_normalized not in section_normalized:
                    errors.append("key_quote doesn't match summary's Key Quote section")

        context["frontmatter_valid"] = len(errors) == 0
        context["frontmatter_validation_errors"] = errors
        context["frontmatter_attempt"] = context.get("frontmatter_attempt", 0) + 1

        return context

    def _scrape_url(self, context: dict) -> dict:
        """Fetch URL and extract clean text content."""
        if trafilatura is None:
            raise RuntimeError(
                "trafilatura not installed. Run: pip install trafilatura"
            )

        url = context["url"]

        # Fetch and extract content
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            raise RuntimeError(f"Failed to fetch URL: {url}")

        # Extract text (no formatting, optimized for LLM)
        content = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
            favor_recall=True,
            output_format="txt",
        )

        if not content:
            raise RuntimeError(f"Failed to extract content from: {url}")

        # Extract title
        title = trafilatura.extract(
            downloaded,
            output_format="txt",
            include_comments=False,
            only_with_metadata=False,
        )
        # Try to get title from metadata
        metadata = trafilatura.extract_metadata(downloaded)
        title = metadata.title if metadata and metadata.title else self._title_from_url(url)

        # Update context
        context["raw_content"] = content
        context["title"] = title
        context["scraped_at"] = datetime.now(timezone.utc).isoformat()
        context["word_count"] = len(content.split())

        return context

    def _title_from_url(self, url: str) -> str:
        """Generate a title from URL path."""
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        if path:
            # Take last path segment
            title = path.split("/")[-1]
            # Remove extension
            title = re.sub(r"\.[^.]+$", "", title)
            # Replace separators with spaces
            title = re.sub(r"[-_]", " ", title)
            return title.title()
        return parsed.netloc

    def _save_files(self, context: dict) -> dict:
        """Save raw content and summary to files."""
        data_dir = Path(context["data_dir"]).expanduser()
        url = context["url"]
        title = context["title"]
        raw_content = context["raw_content"]
        summary = context["summary"]
        frontmatter_yaml = context.get("frontmatter_yaml", "")
        scraped_at = context["scraped_at"]
        word_count = context["word_count"]

        # Create year directory
        year = datetime.now(timezone.utc).strftime("%Y")
        year_dir = data_dir / year
        year_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename: YYYY-MM-DD_slug
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        slug = self._slugify(title)
        base_name = f"{date_str}_{slug}"

        # Ensure unique filename
        raw_path = year_dir / f"{base_name}.txt"
        summary_path = year_dir / f"{base_name}.md"
        counter = 1
        while raw_path.exists() or summary_path.exists():
            base_name = f"{date_str}_{slug}_{counter}"
            raw_path = year_dir / f"{base_name}.txt"
            summary_path = year_dir / f"{base_name}.md"
            counter += 1

        # Write raw content
        raw_path.write_text(raw_content, encoding="utf-8")

        # Parse LLM-generated frontmatter and merge with system fields
        try:
            # Strip any markdown code fences if present
            fm_clean = frontmatter_yaml.strip()
            if fm_clean.startswith("```"):
                fm_clean = re.sub(r"^```\w*\n?", "", fm_clean)
                fm_clean = re.sub(r"\n?```$", "", fm_clean)
            
            llm_frontmatter = yaml.safe_load(fm_clean) or {}
        except yaml.YAMLError:
            llm_frontmatter = {}

        # Build complete frontmatter with system fields first
        frontmatter_dict = {
            "url": url,
            "title": title,
            "scraped_at": scraped_at,
            "word_count": word_count,
            "raw_file": raw_path.name,
        }
        # Merge LLM-extracted fields
        frontmatter_dict.update(llm_frontmatter)

        # Convert to YAML string
        frontmatter_str = yaml.dump(
            frontmatter_dict, 
            default_flow_style=False, 
            allow_unicode=True,
            sort_keys=False,
            width=120,
        )
        
        summary_content = f"---\n{frontmatter_str}---\n\n{summary}"
        summary_path.write_text(summary_content, encoding="utf-8")

        # Update README index
        tldr = llm_frontmatter.get("tldr", "")
        self._update_readme(year_dir, url, title, summary_path.name, raw_path.name, scraped_at, tldr)

        context["raw_file_path"] = str(raw_path)
        context["summary_file_path"] = str(summary_path)

        return context

    def _slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug."""
        # Lowercase
        slug = text.lower()
        # Replace spaces and underscores with hyphens
        slug = re.sub(r"[\s_]+", "-", slug)
        # Remove non-alphanumeric (except hyphens)
        slug = re.sub(r"[^a-z0-9-]", "", slug)
        # Collapse multiple hyphens
        slug = re.sub(r"-+", "-", slug)
        # Trim hyphens from ends
        slug = slug.strip("-")
        # Limit length
        return slug[:60] if slug else "untitled"

    def _update_readme(
        self,
        year_dir: Path,
        url: str,
        title: str,
        summary_file: str,
        raw_file: str,
        scraped_at: str,
        tldr: str = "",
    ) -> None:
        """Update or create README.md with index of scraped pages."""
        readme_path = year_dir / "README.md"
        year = year_dir.name

        # Header for new README
        header = f"""# Website Archive - {year}

Scraped web pages organized by date.

| Date | Title | TL;DR | Summary | Raw | Source |
|------|-------|-------|---------|-----|--------|
"""

        # Truncate TL;DR for table display
        tldr_short = (tldr[:80] + "...") if len(tldr) > 80 else tldr
        tldr_short = tldr_short.replace("|", "\\|")  # Escape pipes

        # New entry
        date_str = scraped_at.split("T")[0]
        entry = f"| {date_str} | {title} | {tldr_short} | [{summary_file}](./{summary_file}) | [{raw_file}](./{raw_file}) | [link]({url}) |\n"

        if readme_path.exists():
            content = readme_path.read_text(encoding="utf-8")
            # Find the table and append entry
            if "| Date | Title |" in content:
                # Insert new entry after header row (find end of header line)
                lines = content.split("\n")
                new_lines = []
                inserted = False
                for line in lines:
                    new_lines.append(line)
                    if not inserted and line.startswith("|---"):
                        new_lines.append(entry.strip())
                        inserted = True
                content = "\n".join(new_lines)
            else:
                content = header + entry
        else:
            content = header + entry

        readme_path.write_text(content, encoding="utf-8")

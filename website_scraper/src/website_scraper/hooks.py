"""
Website Scraper Hooks - Handle URL scraping and file saving.
"""

import re
import os
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
        elif action == "save_files":
            return self._save_files(context)
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

        # Write summary with YAML frontmatter
        frontmatter = f"""---
url: {url}
title: "{title.replace('"', '\\"')}"
scraped_at: {scraped_at}
word_count: {word_count}
raw_file: {raw_path.name}
---

"""
        summary_content = frontmatter + summary
        summary_path.write_text(summary_content, encoding="utf-8")

        # Update README index
        self._update_readme(year_dir, url, title, summary_path.name, raw_path.name, scraped_at)

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
    ) -> None:
        """Update or create README.md with index of scraped pages."""
        readme_path = year_dir / "README.md"
        year = year_dir.name

        # Header for new README
        header = f"""# Website Archive - {year}

Scraped web pages organized by date.

| Date | Title | Summary | Raw | Source |
|------|-------|---------|-----|--------|
"""

        # New entry
        date_str = scraped_at.split("T")[0]
        entry = f"| {date_str} | {title} | [{summary_file}](./{summary_file}) | [{raw_file}](./{raw_file}) | [link]({url}) |\n"

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

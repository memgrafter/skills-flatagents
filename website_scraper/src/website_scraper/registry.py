"""
URL Registry - Manage queue of URLs to scrape.
"""

import csv
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


class URLRegistry:
    """Manages a CSV registry of URLs to scrape."""

    FIELDNAMES = ["url", "title", "added_at", "status", "scraped_at", "note"]
    
    def __init__(self, registry_path: Path):
        self.path = Path(registry_path)
        self._ensure_exists()

    def _ensure_exists(self) -> None:
        """Create registry file with headers if it doesn't exist."""
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
                writer.writeheader()

    def _read_all(self) -> list[dict]:
        """Read all entries from registry."""
        with open(self.path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def _write_all(self, entries: list[dict]) -> None:
        """Write all entries to registry."""
        with open(self.path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
            writer.writeheader()
            writer.writerows(entries)

    def add(self, url: str, title: str = "", note: str = "") -> bool:
        """Add URL to registry if not already present. Returns True if added."""
        entries = self._read_all()
        
        # Check for duplicate
        normalized_url = self._normalize_url(url)
        for entry in entries:
            if self._normalize_url(entry["url"]) == normalized_url:
                return False  # Already exists
        
        # Add new entry
        entries.append({
            "url": url,
            "title": title or self._title_from_url(url),
            "added_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
            "scraped_at": "",
            "note": note,
        })
        self._write_all(entries)
        return True

    def mark_scraped(self, url: str) -> None:
        """Mark URL as scraped."""
        entries = self._read_all()
        normalized_url = self._normalize_url(url)
        
        for entry in entries:
            if self._normalize_url(entry["url"]) == normalized_url:
                entry["status"] = "scraped"
                entry["scraped_at"] = datetime.now(timezone.utc).isoformat()
                break
        
        self._write_all(entries)

    def mark_failed(self, url: str, error: str = "") -> None:
        """Mark URL as failed."""
        entries = self._read_all()
        normalized_url = self._normalize_url(url)
        
        for entry in entries:
            if self._normalize_url(entry["url"]) == normalized_url:
                entry["status"] = f"failed: {error}" if error else "failed"
                break
        
        self._write_all(entries)

    def mark_skipped(self, url: str, reason: str = "") -> None:
        """Mark URL as skipped (e.g., not scrapable)."""
        entries = self._read_all()
        normalized_url = self._normalize_url(url)
        
        for entry in entries:
            if self._normalize_url(entry["url"]) == normalized_url:
                entry["status"] = f"skipped: {reason}" if reason else "skipped"
                break
        
        self._write_all(entries)

    def get_pending(self) -> list[dict]:
        """Get all pending URLs."""
        entries = self._read_all()
        return [e for e in entries if e["status"] == "pending"]

    def get_next(self) -> Optional[dict]:
        """Get next pending URL."""
        pending = self.get_pending()
        return pending[0] if pending else None

    def import_from_tabs_export(self, filepath: Path) -> int:
        """
        Import URLs from browser tabs export (alternating title/URL lines).
        Returns count of new URLs added.
        """
        content = Path(filepath).read_text(encoding="utf-8")
        lines = [line.strip() for line in content.strip().split("\n") if line.strip()]
        
        added = 0
        i = 0
        while i < len(lines):
            # Expect: title line, then URL line
            if i + 1 < len(lines) and lines[i + 1].startswith(("http://", "https://")):
                title = lines[i]
                url = lines[i + 1]
                if self.add(url, title):
                    added += 1
                i += 2
            elif lines[i].startswith(("http://", "https://")):
                # Just a URL without title
                if self.add(lines[i]):
                    added += 1
                i += 1
            else:
                # Skip non-URL line
                i += 1
        
        return added

    def stats(self) -> dict:
        """Get registry statistics."""
        entries = self._read_all()
        stats = {
            "total": len(entries),
            "pending": 0,
            "scraped": 0,
            "failed": 0,
            "skipped": 0,
        }
        for entry in entries:
            status = entry["status"]
            if status == "pending":
                stats["pending"] += 1
            elif status == "scraped":
                stats["scraped"] += 1
            elif status.startswith("failed"):
                stats["failed"] += 1
            elif status.startswith("skipped"):
                stats["skipped"] += 1
        return stats

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison."""
        # Remove trailing slashes, query params for dedup
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"

    def _title_from_url(self, url: str) -> str:
        """Generate a title from URL path."""
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        if path:
            title = path.split("/")[-1]
            title = re.sub(r"\.[^.]+$", "", title)
            title = re.sub(r"[-_]", " ", title)
            return title.title()
        return parsed.netloc


# URLs that are known to not be scrapable
SKIP_PATTERNS = [
    r"^https?://(www\.)?youtube\.com",
    r"^https?://(www\.)?discord\.com",
    r"^https?://(www\.)?x\.com",
    r"^https?://(www\.)?twitter\.com",
    r"^https?://.*\.google\.com/(chrome|search)",
    r"^https?://cloud\.cerebras\.ai",
    r"^https?://app\.privacy\.com",
    r"^https?://.*firecrawl\.dev/app",
]


def is_scrapable(url: str) -> tuple[bool, str]:
    """Check if URL is likely scrapable. Returns (is_scrapable, reason)."""
    for pattern in SKIP_PATTERNS:
        if re.match(pattern, url, re.IGNORECASE):
            return False, f"Matches skip pattern: {pattern}"
    return True, ""

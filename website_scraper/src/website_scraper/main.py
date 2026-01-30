"""
Website Scraper - Main entry point.
"""

import asyncio
import sys
import os
from pathlib import Path

from flatagents import FlatMachine


DEFAULT_DATA_DIR = "~/code/skills-flatagents/website_scraper/website_analysis"


async def run(url: str, data_dir: str | None = None):
    """Scrape URL and generate summary."""
    if data_dir is None:
        data_dir = os.environ.get("DATA_DIR", DEFAULT_DATA_DIR)

    # Expand user path
    data_dir = str(Path(data_dir).expanduser())

    machine_file = Path(__file__).parent.parent.parent / "machine.yml"
    machine = FlatMachine(config_file=str(machine_file))

    result = await machine.execute(input={"url": url, "data_dir": data_dir})

    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        if "url" in result:
            print(f"URL: {result['url']}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"✓ Scraped: {result.get('title', 'Unknown')}")
        print(f"  URL: {result.get('url', '')}")
        print(f"  Words: {result.get('word_count', 0)}")
        print(f"  Raw: {result.get('raw_file', '')}")
        print(f"  Summary: {result.get('summary_file', '')}")


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: website-scraper <url> [data_dir]", file=sys.stderr)
        print("  or: DATA_DIR=/path/to/archive website-scraper <url>", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    data_dir = sys.argv[2] if len(sys.argv) > 2 else None

    asyncio.run(run(url, data_dir))


if __name__ == "__main__":
    main()

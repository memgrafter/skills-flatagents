#!/usr/bin/env python3
"""
URL Registry CLI - Manage queue of URLs to scrape.

Usage:
    ./registry.py import ~/Downloads/tabs.txt   # Import from browser export
    ./registry.py add URL [--title "..."]       # Add single URL
    ./registry.py list                          # Show pending URLs
    ./registry.py stats                         # Show statistics
    ./registry.py next                          # Show next URL to scrape
    ./registry.py run                           # Scrape next pending URL
    ./registry.py run --all                     # Scrape all pending URLs
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from website_scraper.registry import URLRegistry, is_scrapable

DEFAULT_REGISTRY = Path(__file__).parent / "url_registry.csv"
DEFAULT_DATA_DIR = Path(__file__).parent / "website_analysis"


def cmd_import(args):
    """Import URLs from browser tabs export."""
    registry = URLRegistry(args.registry)
    filepath = Path(args.file).expanduser()
    
    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        return 1
    
    added = registry.import_from_tabs_export(filepath)
    stats = registry.stats()
    
    print(f"Imported {added} new URLs")
    print(f"Total pending: {stats['pending']}")
    
    # Auto-skip non-scrapable URLs
    if args.auto_skip:
        skipped = 0
        for entry in registry.get_pending():
            scrapable, reason = is_scrapable(entry["url"])
            if not scrapable:
                registry.mark_skipped(entry["url"], reason)
                skipped += 1
        if skipped:
            print(f"Auto-skipped {skipped} non-scrapable URLs")
    
    return 0


def cmd_add(args):
    """Add single URL to registry."""
    registry = URLRegistry(args.registry)
    
    if registry.add(args.url, args.title or "", args.note or ""):
        print(f"Added: {args.url}")
    else:
        print(f"Already exists: {args.url}")
    
    return 0


def cmd_list(args):
    """List pending URLs."""
    registry = URLRegistry(args.registry)
    pending = registry.get_pending()
    
    if not pending:
        print("No pending URLs")
        return 0
    
    for i, entry in enumerate(pending, 1):
        title = entry["title"][:50] + "..." if len(entry["title"]) > 50 else entry["title"]
        print(f"{i:3}. {title}")
        print(f"     {entry['url']}")
        if entry.get("note"):
            print(f"     Note: {entry['note']}")
    
    print(f"\nTotal: {len(pending)} pending")
    return 0


def cmd_stats(args):
    """Show registry statistics."""
    registry = URLRegistry(args.registry)
    stats = registry.stats()
    
    print(f"Total:   {stats['total']}")
    print(f"Pending: {stats['pending']}")
    print(f"Scraped: {stats['scraped']}")
    print(f"Failed:  {stats['failed']}")
    print(f"Skipped: {stats['skipped']}")
    
    return 0


def cmd_next(args):
    """Show next URL to scrape."""
    registry = URLRegistry(args.registry)
    entry = registry.get_next()
    
    if entry:
        print(f"Title: {entry['title']}")
        print(f"URL: {entry['url']}")
        if entry.get("note"):
            print(f"Note: {entry['note']}")
    else:
        print("No pending URLs")
    
    return 0


def cmd_run(args):
    """Scrape pending URLs."""
    registry = URLRegistry(args.registry)
    data_dir = Path(args.data_dir).expanduser()
    
    if args.all:
        pending = registry.get_pending()
    else:
        entry = registry.get_next()
        pending = [entry] if entry else []
    
    if not pending:
        print("No pending URLs")
        return 0
    
    # Filter non-scrapable if auto-skip
    if args.auto_skip:
        for entry in pending[:]:
            scrapable, reason = is_scrapable(entry["url"])
            if not scrapable:
                print(f"Skipping (not scrapable): {entry['url']}")
                print(f"  Reason: {reason}")
                registry.mark_skipped(entry["url"], reason)
                pending.remove(entry)
    
    success = 0
    failed = 0
    
    for entry in pending:
        url = entry["url"]
        print(f"\n{'='*60}")
        print(f"Scraping: {entry['title'][:60]}")
        print(f"URL: {url}")
        print("="*60)
        
        # Run the scraper
        run_script = Path(__file__).parent / "run.sh"
        result = subprocess.run(
            [str(run_script), url],
            env={"DATA_DIR": str(data_dir), **dict(__import__("os").environ)},
            capture_output=False,
        )
        
        if result.returncode == 0:
            registry.mark_scraped(url)
            success += 1
            print(f"✓ Scraped successfully")
        else:
            registry.mark_failed(url, f"exit code {result.returncode}")
            failed += 1
            print(f"✗ Failed to scrape")
        
        if not args.all:
            break
    
    print(f"\n{'='*60}")
    print(f"Done: {success} scraped, {failed} failed")
    stats = registry.stats()
    print(f"Remaining: {stats['pending']} pending")
    
    return 0 if failed == 0 else 1


def cmd_skip(args):
    """Mark URL as skipped."""
    registry = URLRegistry(args.registry)
    registry.mark_skipped(args.url, args.reason or "manual skip")
    print(f"Skipped: {args.url}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="URL Registry CLI")
    parser.add_argument(
        "--registry", "-r",
        type=Path,
        default=DEFAULT_REGISTRY,
        help=f"Path to registry CSV (default: {DEFAULT_REGISTRY})"
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # import
    p_import = subparsers.add_parser("import", help="Import from browser tabs export")
    p_import.add_argument("file", help="Path to tabs export file")
    p_import.add_argument("--auto-skip", "-s", action="store_true", help="Auto-skip non-scrapable URLs")
    p_import.set_defaults(func=cmd_import)
    
    # add
    p_add = subparsers.add_parser("add", help="Add single URL")
    p_add.add_argument("url", help="URL to add")
    p_add.add_argument("--title", "-t", help="Title for URL")
    p_add.add_argument("--note", "-n", help="Note about why you saved this")
    p_add.set_defaults(func=cmd_add)
    
    # list
    p_list = subparsers.add_parser("list", help="List pending URLs")
    p_list.set_defaults(func=cmd_list)
    
    # stats
    p_stats = subparsers.add_parser("stats", help="Show statistics")
    p_stats.set_defaults(func=cmd_stats)
    
    # next
    p_next = subparsers.add_parser("next", help="Show next URL to scrape")
    p_next.set_defaults(func=cmd_next)
    
    # run
    p_run = subparsers.add_parser("run", help="Scrape pending URLs")
    p_run.add_argument("--all", "-a", action="store_true", help="Scrape all pending")
    p_run.add_argument("--auto-skip", "-s", action="store_true", help="Auto-skip non-scrapable URLs")
    p_run.add_argument("--data-dir", "-d", default=DEFAULT_DATA_DIR, help="Data directory")
    p_run.set_defaults(func=cmd_run)
    
    # skip
    p_skip = subparsers.add_parser("skip", help="Mark URL as skipped")
    p_skip.add_argument("url", help="URL to skip")
    p_skip.add_argument("--reason", "-r", help="Reason for skipping")
    p_skip.set_defaults(func=cmd_skip)
    
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env -S python3 -u
"""
Security tests for git command validation in codebase_ripper.

Run from repo root: .venv/bin/python codebase_ripper/test_git_security.py

Tests the allowlist approach:
- allowed_subcommands: full access with flag validation
- list_only_subcommands: flags only, no positional args (prevents write ops)
- allowed_flags: safe read-only flags
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codebase_ripper.hooks import CodebaseRipperHooks


def test_git_security():
    hooks = CodebaseRipperHooks()
    failures = []

    def check(cmd: str, should_pass: bool, description: str = ""):
        valid, reason = hooks.validate_command(cmd)
        passed = valid == should_pass
        if not passed:
            failures.append({
                "cmd": cmd,
                "expected": "PASS" if should_pass else "BLOCK",
                "got": "PASS" if valid else "BLOCK",
                "reason": reason,
                "description": description,
            })
        return passed

    # =========================================================================
    # SAFE COMMANDS - should PASS
    # =========================================================================

    # Basic read-only subcommands
    check("git status", True, "status is read-only")
    check("git log", True, "log is read-only")
    check("git log --oneline -20", True, "log with safe flags")
    check("git log -n 10 --stat", True, "log with -n and --stat")
    check("git log --graph --decorate --oneline", True, "log with multiple flags")
    check("git diff", True, "diff is read-only")
    check("git diff HEAD~1", True, "diff with commit ref")
    check("git diff HEAD~1 --name-only", True, "diff with --name-only")
    check("git diff --cached", True, "diff staged changes")
    check("git show HEAD", True, "show commit")
    check("git show HEAD:path/to/file.py", True, "show file at commit")
    check("git ls-files", True, "ls-files is read-only")
    check("git ls-files '*.py'", True, "ls-files with pattern")
    check("git blame file.py", True, "blame is read-only")
    check("git blame -L 10,20 file.py", True, "blame with line range")
    check("git describe", True, "describe is read-only")
    check("git describe --tags", True, "describe with --tags")
    check("git rev-parse HEAD", True, "rev-parse is read-only")
    check("git rev-parse --abbrev-ref HEAD", True, "rev-parse current branch")

    # List-only subcommands (flags only, no positional args)
    check("git remote", True, "remote list")
    check("git remote -v", True, "remote verbose list")
    check("git branch", True, "branch list")
    check("git branch -a", True, "branch all")
    check("git branch -r", True, "branch remotes")
    check("git branch --list", True, "branch --list")
    check("git branch -v", True, "branch verbose")
    check("git branch --show-current", True, "branch current")
    check("git branch --merged", True, "branch merged")
    check("git branch --no-merged", True, "branch no-merged")
    check("git tag", True, "tag list")
    check("git tag -l", True, "tag -l")
    check("git tag --list", True, "tag --list")
    check("git tag -l 'v1.*'", False, "tag list with pattern has positional arg")

    # =========================================================================
    # DANGEROUS COMMANDS - should BLOCK
    # =========================================================================

    # Blocked subcommands (not in any allowlist)
    check("git config user.name", False, "config can write values")
    check("git config --get user.name", False, "config blocked entirely")
    check("git commit -m 'test'", False, "commit is write op")
    check("git push origin main", False, "push is write op")
    check("git pull origin main", False, "pull modifies working tree")
    check("git fetch origin", False, "fetch modifies refs")
    check("git checkout main", False, "checkout modifies working tree")
    check("git switch main", False, "switch modifies working tree")
    check("git reset HEAD", False, "reset is destructive")
    check("git reset --hard HEAD", False, "reset --hard is destructive")
    check("git rebase main", False, "rebase modifies history")
    check("git merge main", False, "merge modifies history")
    check("git cherry-pick abc123", False, "cherry-pick modifies history")
    check("git revert abc123", False, "revert modifies history")
    check("git stash", False, "stash modifies state")
    check("git clean -fd", False, "clean deletes files")
    check("git add .", False, "add stages files")
    check("git rm file.py", False, "rm deletes files")
    check("git mv old.py new.py", False, "mv renames files")

    # List-only subcommands with positional args (write operations)
    check("git remote add evil https://evil.com", False, "remote add is write op")
    check("git remote remove origin", False, "remote remove is write op")
    check("git remote rm origin", False, "remote rm is write op")
    check("git remote rename origin backup", False, "remote rename is write op")
    check("git remote set-url origin https://x.com", False, "remote set-url is write op")
    check("git remote prune origin", False, "remote prune is write op")
    check("git remote update", False, "remote update fetches")
    check("git branch newbranch", False, "branch create is write op")
    check("git branch -d feature", False, "branch delete is write op")
    check("git branch -D feature", False, "branch force delete is write op")
    check("git branch -m old new", False, "branch rename is write op")
    check("git branch -M old new", False, "branch force rename is write op")
    check("git branch --delete feature", False, "branch --delete is write op")
    check("git branch -u origin/main", False, "branch set upstream is write op")
    check("git tag v1.0", False, "tag create is write op")
    check("git tag -a v1.0 -m 'msg'", False, "tag annotated create is write op")
    check("git tag -d v1.0", False, "tag delete is write op")
    check("git tag -f v1.0", False, "tag force is write op")

    # Dangerous flags (code execution via format strings)
    check("git log --format='%s'", False, "--format can execute code")
    check("git log --pretty=format:'%s'", False, "--pretty can execute code")
    check("git log --pretty=oneline", False, "--pretty blocked entirely")
    check("git show --format='%s' HEAD", False, "--format on show")
    check("git branch --format='%(refname)'", False, "--format on branch")

    # Missing subcommand
    check("git", False, "git requires subcommand")

    # =========================================================================
    # SHELL INJECTION PATTERNS - should BLOCK
    # =========================================================================

    check("git log; rm -rf /", False, "command chaining with ;")
    check("git log && rm -rf /", False, "command chaining with &&")
    check("git log || rm -rf /", False, "command chaining with ||")
    check("git log | cat", False, "pipe")
    check("git log > /tmp/out", False, "output redirect")
    check("git log $(whoami)", False, "command substitution $()")
    check("git log `whoami`", False, "command substitution backticks")
    check("git log $HOME", False, "env var expansion")
    check("git log ${HOME}", False, "env var expansion braces")

    # Path traversal (but allow git refs like HEAD~1)
    check("git diff HEAD~1", True, "tilde in git ref is OK")
    check("git diff HEAD~10", True, "tilde with number is OK")
    check("git show HEAD~1:file.py", True, "tilde in show ref is OK")
    check("cat ~/file.txt", False, "tilde home expansion blocked")
    check("cat /~user/file.txt", False, "tilde user expansion blocked")
    check("cat ../../../etc/passwd", False, "parent traversal blocked")

    # =========================================================================
    # RESULTS
    # =========================================================================

    total = len([f for f in dir() if f.startswith("check")])  # approximate
    if failures:
        print(f"❌ {len(failures)} FAILURES:\n")
        for f in failures:
            print(f"  {f['expected']:5} {f['cmd']}")
            print(f"        got {f['got']}: {f['reason']}")
            if f['description']:
                print(f"        ({f['description']})")
            print()
        return False
    else:
        print("✅ All git security tests passed!")
        return True


if __name__ == "__main__":
    success = test_git_security()
    sys.exit(0 if success else 1)

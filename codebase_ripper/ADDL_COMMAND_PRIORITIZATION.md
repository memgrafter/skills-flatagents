# Additional Command Prioritization

Analysis of potentially missing commands from the codebase_ripper allowlist.

## Current Allowlist

| Command | Description |
|---------|-------------|
| `tree` | Directory structure |
| `rg` | Ripgrep content search |
| `fd` | Find files by name |
| `head` | First N lines |
| `cat` | Full file contents |
| `wc` | Line/word/char counts |
| `ls` | Directory listing |
| `tail` | Last N lines |
| `file` | File type detection |
| `diff` | Compare files |
| `git` | Git (status, log, diff, show, ls-files, blame, describe, rev-parse, remote*, branch*, tag*) |

*list-only subcommands (flags only, no arguments)

---

## Candidate Missing Commands - Assessment

### 1. `stat`
**What it does:** Shows detailed file metadata (size, permissions, timestamps, inode)
**Belief:** Low-to-medium value. Most of what you'd want from `stat` you can get from `ls -l`. The timestamp granularity and inode info are rarely needed for codebase exploration.
**Priority:** Low

### 2. `sort`
**What it does:** Sort lines alphabetically/numerically
**Belief:** Medium value. Useful for analyzing imports, finding duplicates with `sort | uniq`, but pipes are blocked so it's limited to sorting file contents directly. Without pipes, its utility drops significantly.
**Priority:** Low (pipes blocked)

### 3. `uniq`
**What it does:** Remove/count duplicate lines
**Belief:** Same problem as `sort` - most useful with pipes (`sort | uniq -c`). Without pipes, you'd need a pre-sorted file.
**Priority:** Low (pipes blocked)

### 4. `cut`
**What it does:** Extract columns/fields from text
**Belief:** Low value without pipes. You'd use it like `cut -d: -f1 /etc/passwd` but for codebase exploration, `rg` with regex is more flexible.
**Priority:** Low (pipes blocked)

### 5. `awk`
**What it does:** Powerful text processing
**Belief:** High capability but complex. Without pipes it's less useful. Also has security concerns - can execute shell commands with `system()`. Would need careful flag restrictions.
**Priority:** Low (security complexity, pipes blocked)

### 6. `sed`
**What it does:** Stream editor for text transformation
**Belief:** Read-only mode (`sed -n 'pattern/p'`) could be useful for extracting lines, but `rg` already covers most search cases. The `-i` flag is dangerous. Complexity of safe implementation vs marginal benefit.
**Priority:** Low (rg covers most cases)

### 7. `du`
**What it does:** Disk usage per directory/file
**Belief:** Medium value. Genuinely useful for finding large directories, understanding project structure by size. Read-only, low security risk.
**Priority:** Medium

### 8. `md5sum` / `sha256sum`
**What it does:** Compute file hashes
**Belief:** Low value for codebase exploration. Useful for detecting duplicate files or verifying integrity, but not a common exploration need. Read-only, very safe.
**Priority:** Low

### 9. `strings`
**What it does:** Extract printable strings from binary files
**Belief:** Low value. Only useful when exploring projects with binary assets. Very safe (read-only), but niche use case.
**Priority:** Low

### 10. `which`
**What it does:** Find path of executable
**Belief:** Low value for codebase exploration. More useful for system debugging. But very safe.
**Priority:** Low

### 11. `env` / `printenv`
**What it does:** Show environment variables
**Belief:** Low value and potential security concern - could leak API keys, secrets. Not really about exploring the codebase itself.
**Priority:** Skip (security concern)

### 12. `nl`
**What it does:** Number lines (like `cat -n`)
**Belief:** Redundant - `cat -n` already exists in allowlist.
**Priority:** Skip (redundant)

### 13. `column`
**What it does:** Format text into columns
**Belief:** Low value. Nice for pretty output but not essential for exploration.
**Priority:** Low

### 14. `tac`
**What it does:** Reverse file (like cat backwards)
**Belief:** Low value. `tail` covers most "see end of file" needs.
**Priority:** Low

### 15. `zcat` / `zless`
**What it does:** Read gzip-compressed files
**Belief:** Low value. Most codebases don't have compressed source files. Logs might be compressed but that's operational, not codebase exploration.
**Priority:** Low

### 16. `tar -t`
**What it does:** List archive contents without extracting
**Belief:** Low value. Rarely need to inspect archives during codebase exploration.
**Priority:** Low

### 17. `git log --format`
**What it does:** Custom log formatting
**Belief:** Medium value. Currently blocked (--format/--pretty). Would allow extracting specific commit metadata. Some security concern with format strings but git handles this safely.
**Priority:** Medium (useful for structured commit analysis)

### 18. `git rev-list`
**What it does:** List commit SHAs
**Belief:** Low value. Mostly useful for scripting/piping which is blocked.
**Priority:** Low

### 19. `git shortlog`
**What it does:** Summarize commits by author
**Belief:** Medium value. Quick way to see who contributed what. Read-only, safe.
**Priority:** Medium

### 20. `git stash list`
**What it does:** Show stashed changes
**Belief:** Low value. Stashes are local state, not really codebase exploration.
**Priority:** Low

### 21. `basename` / `dirname`
**What it does:** Extract filename or directory from path
**Belief:** Low value. Mostly useful in scripts with pipes.
**Priority:** Low

### 22. `realpath`
**What it does:** Resolve symlinks to canonical path
**Belief:** Low value for exploration. Could be useful to understand symlink structure but niche.
**Priority:** Low

### 23. `readlink`
**What it does:** Show symlink target
**Belief:** Low value. Niche use case.
**Priority:** Low

### 24. `hexdump` / `xxd`
**What it does:** Show hex dump of file
**Belief:** Low value. Only for binary analysis, very niche.
**Priority:** Low

---

## Reordered by Priority

### Worth Adding (Conservative)

| Priority | Command | Rationale |
|----------|---------|-----------|
| DONE: 1 | `du` | Genuinely useful for understanding project size/structure. Safe, read-only. Simple flags like `-h`, `-s`, `-d`. |
| DONE: 2 | `--format`/`--pretty` for git log | Enables structured commit analysis. Git handles format strings safely. |
| DONE: 3 | `git shortlog` | Quick contributor summary. Read-only, safe, useful for understanding who works on what. |

### Maybe (Lower Priority)

| Priority | Command | Rationale |
|----------|---------|-----------|
| 4 | `md5sum` | Safe, occasionally useful for duplicate detection. Low complexity to add. |
| 5 | `stat` | Some utility for timestamps. Low complexity. |
| 6 | `strings` | Safe, useful for binary-heavy projects. Niche. |

### Skip

- `sort`, `uniq`, `cut`, `awk`, `sed` - Too limited without pipes
- `env`/`printenv` - Security concern (leaks secrets)
- `nl` - Redundant with `cat -n`
- `column`, `tac` - Marginal value
- `zcat`, `tar -t` - Niche use cases
- `which`, `basename`, `dirname`, `realpath`, `readlink` - System/scripting focused
- `hexdump`/`xxd` - Very niche

---

## Recommendation

Add `du` and consider allowing `--format`/`--pretty` for git log. Everything else is either too niche, redundant, or crippled by the pipe restriction.

---
url: https://github.com/jj-vcs/jj
title: 'GitHub - jj-vcs/jj: A Git-compatible VCS that is both simple and powerful'
scraped_at: '2026-02-07T06:29:11.447748+00:00'
word_count: 2191
raw_file: 2026-02-07_github-jj-vcsjj-a-git-compatible-vcs-that-is-both-simple-and.txt
tldr: Jujutsu (jj) is an experimental, Git-compatible version control system that simplifies workflows by treating the working
  copy as a commit, automatically rebasing descendants, and recording all operations for easy undoing.
key_quote: Version control has finally entered the 1960s!
durability: medium
content_type: mixed
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people:
- Martin von Zweigbergk
- Chris Krycho
- Steve Klabnik
- J. Jennings
tools:
- jj
- git
- mercurial
- breezy
- piper
- citc
- sapling
- darcs
- dropbox
- rsync
- discord
- irc
libraries:
- gitoxide
companies:
- Google
- GitHub
tags:
- version-control
- git
- software-development
- workflow
- open-source
---

### TL;DR
Jujutsu (jj) is an experimental, Git-compatible version control system that simplifies workflows by treating the working copy as a commit, automatically rebasing descendants, and recording all operations for easy undoing.

### Key Quote
"Version control has finally entered the 1960s!"

### Summary
- **What it is**: A VCS that abstracts the storage layer from the user interface. Currently uses a Git backend (gitoxide) for interoperability, storing commits/files in Git while keeping bookmarks/metadata in custom storage.
- **Core Design**:
  - **Working-copy-as-a-commit**: No staging area or index. File changes are automatically recorded as a "working copy commit" that is amended on every change. This eliminates the need for `git stash` and prevents "dirty working copy" errors.
  - **Operation Log**: Records every operation (commit, pull, push) allowing users to undo mistakes or debug repository state easily.
  - **Automatic Rebase**: Modifying a commit automatically rebases all descendants. Conflict resolutions propagate automatically through descendants (similar to `git rerere` but built-in).
  - **First-class Conflicts**: Conflicts are tracked as objects within the commit graph rather than just text diffs, allowing resolution to happen independently of the operation that caused them.
- **Influences**: Combines Git's speed, Mercurial/Sapling's revset language and anonymous branches, and Darcs' approach to patch conflicts.
- **Status**: Experimental (pre-1.0). On-disk formats may change incompatibly. Used daily by core developers; Google contributes but does not officially support it.
- **Experimental Features**: Safe concurrent replication, designed to work over non-atomic filesystems like Dropbox or rsync without corruption.

### Assessment
- **Durability**: Medium. The architectural concepts are stable, but the "experimental" status, version numbers (e.g., 0.24), and specific commands (e.g., `jj git init` replacing `jj init --git`) indicate the project is evolving rapidly.
- **Content type**: Mixed (Technical overview, Philosophy, Documentation).
- **Density**: High. The text efficiently explains complex architectural deviations from Git (e.g., commit-as-working-copy) without filler.
- **Originality**: Primary source. This is the official README for the project.
- **Reference style**: Refer-back. Useful for verifying high-level design decisions or checking current project status.
- **Scrape quality**: Good. The text appears to capture the full README, including version history and detailed architectural descriptions.
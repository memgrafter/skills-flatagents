# Repo Map Skill

Generates a compact repository map using Aider's `repomap` implementation vendored directly into this skill.

## Notes

- No `aider` pip dependency is required.
- Repo map files are vendored under `repo_map/src/aider/`.
- Apache-2.0 attribution headers are included on vendored files.

## Usage

```bash
./run.sh "optional hint text" -d /path/to/repo --map-tokens 2000
```

JSON output:

```bash
./run.sh "auth flow" -d . --json
```

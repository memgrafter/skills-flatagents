# Quick Report

Generate self-contained HTML reports with charts, tables, diagrams, and math — zero install, works offline.

## Quick start

1. Ask the agent to generate a report. It writes an `.html` file to `reports/`.

2. Serve it:

   ```bash
   ~/.agents/skills/quick-report-skill/serve.sh
   ```

3. Open the link printed on startup (Ctrl+click from terminal):

   ```
   http://<hostname>:8080/reports/<your-report>.html
   ```

   The serve script prints the full URL with your machine's hostname on startup.

4. Stop the server with `Ctrl-C`, or from another shell:

   ```bash
   kill $(cat /tmp/quick-report-serve.pid)
   ```

## What's inside

```
├── SKILL.md          ← LLM instructions (component patterns, API reference)
├── template.html     ← Reference template with all patterns
├── serve.sh          ← Static file server (python3 http.server)
├── vendor/           ← Vendored libs (4.5 MB, zero network)
│   ├── plotly-basic.min.js    (charts)
│   ├── mermaid.min.js         (diagrams)
│   ├── katex.min.js + css     (math)
│   └── katex-fonts/           (20 woff2 files)
└── reports/          ← Generated reports go here
```

## Custom port

```bash
./serve.sh 9090
```

## Notes

- Reports use `../vendor/` relative paths — the server must run from the skill root (serve.sh handles this).
- Everything works offline. No CDN, no npm, no build step.
- Dark/light mode toggle built in. Print-ready via Ctrl+P.

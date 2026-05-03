---
name: quick-report
description: >
  Use this when you need a complete interactive report as a single HTML file
  with zero install dependencies — covers charts, tables, diagrams, math,
  KPIs, and prose out of the box.
---

Generate self-contained HTML reports with full interactivity, zero npm/pip install, using three vendored libraries.

## Serving a report

After generating a report, tell the user to run the server and give them the clickable link:

**Do NOT start the server yourself.** The user already has it running. Just give them the link to the report:

View: http://<this_hostname>:8080/reports/<filename>.html

Replace `<this_hostname>` with the machine's actual hostname (run `hostname` to check). The serve script prints the full URL on startup.

The user can Ctrl+click the URL from their terminal. Kill with `Ctrl-C` or `kill $(cat /tmp/quick-report-serve.pid)`.

## Data analysis workflow

For reports that involve code analysis or data exploration, create a temporary SQLite database to collect metrics, then embed the query results as JS data in the report.

Each report gets its own directory under `reports/`:

```
reports/<report-name>/
├── <report-name>.html      ← the report itself
├── data/                    ← SQLite DBs, CSVs, JSON
│   └── analytics.db
└── scripts/                 ← analysis scripts (optional)
    └── build_analytics.py
```

Workflow:

1. **Create the report directory** under `reports/<report-name>/`
2. **Build a SQLite DB** in `data/` — define tables for whatever you're measuring
3. **Populate it** with a Python script (save to `scripts/` if non-trivial)
4. **Run analytical queries** against the DB to surface interesting cross-cuts
5. **Embed results** as inline JS objects/arrays in the report HTML
6. **Commit everything** — the report HTML, SQLite DB, and scripts as the final step so the analysis is reproducible and reviewable

This pattern gives you structured storage for complex analysis without any dependencies beyond Python's built-in `sqlite3`.

## Why use it

- **Zero setup cost**: no package.json, no venv, no build step — just write an HTML file
- **90% coverage**: Plotly (60+ chart types) + Mermaid (8 diagram types) + KaTeX (full LaTeX math) + HTML tables + CSS grid layout
- **Instant results**: open in any browser, works offline, dark/light mode, print-ready
- **LLM-optimal**: every component is JSON/text-config driven — easy for Claude to generate correctly

## When to use

- Ad hoc data analysis reports
- Dashboards with mixed content (charts + tables + text + math + diagrams)
- Reports that need to be emailed or shared as a single file
- Prototyping visualizations before committing to a framework
- Any situation where install dependencies are unwanted or unavailable

## When NOT to use

- Real-time streaming data (use Perspective or Grafana)
- >100K data points per chart (use uPlot, Datashader, or Perspective)
- Interactive map tiles (use MapLibre/Leaflet — separate skill)
- Network graph visualization (use Cytoscape/Sigma — separate skill)
- Production app with routing, auth, state management (use a framework)

## Usage

### File structure

```
quick-report-skill/
├── SKILL.md              ← you are here
├── template.html         ← reference template with all patterns
├── serve.sh              ← HTTP server for viewing reports
├── vendor/               ← vendored libs (4.5MB total, zero network)
│   ├── plotly-basic.min.js
│   ├── mermaid.min.js
│   ├── katex.min.js
│   ├── katex.min.css
│   ├── katex-auto-render.min.js
│   └── katex-fonts/      ← 20 woff2 font files
└── reports/              ← generated reports go here
```

### Generating a report

1. Create a new `.html` file in `quick-report-skill/reports/`
2. Copy the structure from `template.html`
3. Vendor script paths use `../vendor/` relative references
4. Embed data inline as JavaScript objects/arrays
5. Open directly in browser — no server needed

### Vendor library versions

| Library | Version | Size | What it covers |
|---|---|---|---|
| Plotly.js (basic) | 2.35.3 | 1.1 MB | scatter, bar, pie, histogram, heatmap, box, violin, 3D, contour, OHLC, choropleth, sunburst, treemap, sankey, funnel, waterfall, parallel coords |
| Mermaid | 11.x | 2.9 MB | flowchart, sequence, class, state, ER, Gantt, pie, mindmap, timeline, C4, quadrant, sankey, block, packet, XY |
| KaTeX | 0.16.21 | 300 KB | Full LaTeX math (inline + display), auto-render |

## Component Reference

### 1. Charts (Plotly)

Always use the `plotlyTheme()` helper and `PALETTE` array from the template for consistent theming.

```javascript
// Line chart
Plotly.newPlot('div-id', [{
  x: dates, y: values,
  type: 'scatter', mode: 'lines+markers',
  line: { color: PALETTE[0], width: 2.5 },
  name: 'Series A'
}], { ...plotlyTheme(), height: 300, margin: { t: 20, r: 20, b: 40, l: 50 } }, plotlyDefaults);

// Bar chart
Plotly.newPlot('div-id', [{
  x: categories, y: amounts,
  type: 'bar', marker: { color: PALETTE[0] }
}], { ...plotlyTheme(), height: 300 }, plotlyDefaults);

// Pie / donut
Plotly.newPlot('div-id', [{
  labels: names, values: sizes,
  type: 'pie', hole: 0.4,  // 0 for pie, 0.4 for donut
  marker: { colors: PALETTE }
}], { ...plotlyTheme(), height: 300 }, plotlyDefaults);

// Heatmap
Plotly.newPlot('div-id', [{
  z: matrix, x: colLabels, y: rowLabels,
  type: 'heatmap', colorscale: 'Viridis'
}], { ...plotlyTheme(), height: 400 }, plotlyDefaults);

// Box plot
Plotly.newPlot('div-id', groups.map((g, i) => ({
  y: g.values, type: 'box', name: g.label, marker: { color: PALETTE[i] }
})), { ...plotlyTheme(), height: 300 }, plotlyDefaults);

// 3D surface
Plotly.newPlot('div-id', [{
  z: surfaceMatrix, type: 'surface', colorscale: 'Viridis'
}], { ...plotlyTheme(), height: 500 }, plotlyDefaults);

// Candlestick (financial)
Plotly.newPlot('div-id', [{
  x: dates, open: o, high: h, low: l, close: c,
  type: 'candlestick',
  increasing: { line: { color: '#16a34a' } },
  decreasing: { line: { color: '#e11d48' } }
}], { ...plotlyTheme(), height: 400 }, plotlyDefaults);

// Sankey
Plotly.newPlot('div-id', [{
  type: 'sankey', orientation: 'h',
  node: { label: nodeLabels, color: PALETTE },
  link: { source: srcIndices, target: tgtIndices, value: flowValues }
}], { ...plotlyTheme(), height: 400 }, plotlyDefaults);
```

### 2. Tables (HTML + CSS)

Use classes from the template stylesheet:

```html
<div class="card">
  <table>
    <thead>
      <tr><th>Name</th><th class="num">Value</th><th class="num">Change</th></tr>
    </thead>
    <tbody>
      <tr><td>Item A</td><td class="num">1,234</td><td class="num" style="color:#16a34a">+5.2%</td></tr>
      <tr><td>Item B</td><td class="num">987</td><td class="num" style="color:#e11d48">−2.1%</td></tr>
    </tbody>
  </table>
</div>
```

For data-driven tables, generate rows in a `<script>`:

```javascript
const tbody = document.querySelector('#my-table tbody');
data.forEach(row => {
  const tr = document.createElement('tr');
  tr.innerHTML = `<td>${row.name}</td><td class="num">${row.value.toLocaleString()}</td>`;
  tbody.appendChild(tr);
});
```

### 3. KPI Cards

```html
<div class="grid grid-4">
  <div class="card kpi">
    <div class="kpi-value">$1.2M</div>
    <div class="kpi-label">Revenue</div>
    <div class="kpi-delta up">▲ 12.3%</div>
  </div>
  <!-- repeat for each KPI -->
</div>
```

### 4. Diagrams (Mermaid)

```html
<pre class="mermaid">
flowchart LR
    A[Input] --> B{Decision}
    B -->|Yes| C[Process]
    B -->|No| D[Skip]
    C --> E[Output]
    D --> E
</pre>
```

Common diagram types:
- `flowchart LR` / `flowchart TD` — process flows
- `sequenceDiagram` — API/protocol sequences
- `erDiagram` — entity relationships
- `gantt` — project timelines
- `stateDiagram-v2` — state machines
- `mindmap` — concept maps
- `pie` — simple pie charts (text-only alternative to Plotly)
- `classDiagram` — class/object structures

### 5. Math (KaTeX)

Auto-render is initialized by the template. Just write LaTeX:

```html
<!-- Display math (centered, own line) -->
<p>$$E = mc^2$$</p>

<!-- Inline math -->
<p>The variance is \(\sigma^2 = \frac{1}{n}\sum_{i=1}^{n}(x_i - \mu)^2\).</p>
```

### 6. Layout

```html
<!-- Full width section -->
<div class="card">...</div>

<!-- 2-column chart grid -->
<div class="grid grid-2">
  <div class="card"><div id="chart-a"></div></div>
  <div class="card"><div id="chart-b"></div></div>
</div>

<!-- 3-column -->
<div class="grid grid-3">...</div>

<!-- 4-column (good for KPIs) -->
<div class="grid grid-4">...</div>

<!-- Callouts -->
<div class="callout">Info note</div>
<div class="callout warn">Warning</div>
<div class="callout error">Error/critical</div>
<div class="callout success">Success/positive</div>
```

### 7. Dark mode & theming

Built into the template:
- Toggle button in top-right corner
- Plotly charts re-render on theme switch via `plotlyTheme()`
- Mermaid initializes with matching theme
- CSS custom properties in `:root` / `[data-theme="dark"]` — override to match brand

### 8. Print / PDF

- `Ctrl+P` produces clean output (modebars hidden, cards don't break across pages)
- For programmatic PDF: `playwright pdf quick-report-skill/reports/myreport.html out.pdf`

## Examples

### Minimal report (copy-paste starter)

```html
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Analysis Report</title>
<link rel="stylesheet" href="../vendor/katex.min.css">
<!-- Copy the full <style> block from template.html -->
</head>
<body>
<header class="report-header">
  <h1>My Analysis</h1>
  <div class="report-meta"><span>📅 2026-03-24</span></div>
</header>
<main>
  <section>
    <h2>Results</h2>
    <div class="card"><div id="chart1"></div></div>
  </section>
</main>
<script src="../vendor/plotly-basic.min.js"></script>
<script src="../vendor/mermaid.min.js"></script>
<script src="../vendor/katex.min.js"></script>
<script src="../vendor/katex-auto-render.min.js"></script>
<script>
// plotlyTheme(), PALETTE, plotlyDefaults — copy from template.html
// Then create your charts:
Plotly.newPlot('chart1', [{
  x: [1,2,3,4,5], y: [10,15,13,17,22],
  type: 'scatter', mode: 'lines+markers',
  line: { color: '#2563eb' }
}], { height: 350, margin: {t:20,r:20,b:40,l:50}, paper_bgcolor:'rgba(0,0,0,0)', plot_bgcolor:'rgba(0,0,0,0)' });

mermaid.initialize({ startOnLoad: true, theme: 'default' });
renderMathInElement(document.body, {
  delimiters: [
    {left: '$$', right: '$$', display: true},
    {left: '\\(', right: '\\)', display: false}
  ], throwOnError: false
});
</script>
</body>
</html>
```

## Output

One `.html` file in `quick-report-skill/reports/` that:
- Opens in any modern browser
- Works fully offline (all assets vendored)
- Is interactive (Plotly hover/zoom, Mermaid links, theme toggle)
- Prints cleanly to PDF via browser print dialog
- Total overhead: ~4.5 MB vendored libs shared across all reports

## How it works (brief)

1. Claude writes a single HTML file using the patterns above
2. File references vendored JS/CSS via `../vendor/` relative paths
3. Data is embedded inline as JS arrays/objects
4. Browser loads and renders — no build step, no server

## Cost / benefit summary

| | |
|---|---|
| **Benefits** | Zero install, instant results, 90%+ chart coverage, offline-capable, print-ready, dark/light mode, LLM-friendly generation patterns, 4.5 MB shared vendor footprint |
| **Costs** | No live data connections (data must be embedded or fetched via XHR), Plotly basic bundle omits some niche trace types (mesh3d, isosurface), no interactive tile maps, no real-time streaming, large datasets require pre-aggregation |
| **Break-even** | First report — skill pays for itself immediately vs. setting up a framework |

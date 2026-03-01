---
url: https://mariozechner.at/posts/2025-10-05-jailjs/
title: 'Infinite Footguns: Writing a JavaScript Interpreter in JavaScript'
scraped_at: '2026-02-11T10:20:25.187509+00:00'
word_count: 2470
raw_file: 2026-02-11_infinite-footguns-writing-a-javascript-interpreter-in-javasc.txt
tldr: Mario Zechner built JailJS, a JavaScript interpreter written in JavaScript, to bypass Content Security Policy restrictions
  in browser extensions—solving the CSP problem but acknowledging that creating a truly secure sandbox is nearly impossible.
key_quote: But ultimately, this is a Sisyphean task, and we are bound to fail gloriously. There's basically an infinite amount
  of attack vectors we would need to patch, which is really fucking hard.
durability: medium
content_type: mixed
density: high
originality: primary
reference_style: deep-study
scrape_quality: good
people:
- Mario Zechner
- Bob Nystrom
tools:
- jailjs
- esbuild
- chrome-extensions
- babel-standalone
libraries:
- sandboxjs
companies: []
tags:
- javascript-interpreter
- content-security-policy
- browser-extensions
- sandboxing
- security
---

### TL;DR
Mario Zechner built JailJS, a JavaScript interpreter written in JavaScript, to bypass Content Security Policy restrictions in browser extensions—solving the CSP problem but acknowledging that creating a truly secure sandbox is nearly impossible.

### Key Quote
"But ultimately, this is a Sisyphean task, and we are bound to fail gloriously. There's basically an infinite amount of attack vectors we would need to patch, which is really fucking hard."

### Summary

**The Problem**
- Author built a browser extension where an LLM navigates the web and executes JavaScript to interact with pages
- Two issues: (1) LLM prompt injection could exfiltrate sensitive data (cookies, localStorage, IndexedDB), and (2) Content Security Policy on major sites blocks `eval`, `new Function`, and script tag injection
- Chrome extension's `chrome.scripting.executeScript` works with statically-defined functions regardless of CSP, but not with dynamically-generated code

**The Solution: JailJS**
- A JavaScript interpreter written in JavaScript that can be bundled statically into a content script
- Uses **Babel standalone** for parsing JavaScript into an AST (ESTree specification for ES5)
- Interpreter walks the AST recursively, evaluating each node type with a large switch statement
- Scope chain manages variables; each function creates a new scope

**Architecture**
```javascript
// Content script (bundled with esbuild)
import { Interpreter, parse } from '@mariozechner/jailjs';
const interpreter = new Interpreter();
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'EXECUTE_CODE') {
    const ast = parse(message.code);
    const result = interpreter.evaluate(ast);
    sendResponse({ success: true, result });
  }
});
```

**Supported Features**
- Full ES5 specification
- ES6+/TypeScript/JSX via Babel transpilation (async/await, classes work)
- **Not supported**: generators, ES6 modules, Proxies, Reflect, WeakRef, SharedArrayBuffer, Atomics

**Sandboxing Approach**
- Default globals: `console`, `Math`, `JSON`, `Date`, `RegExp`, `Array`, `Object`, error types, `parseInt`, `parseFloat`
- **Blocked by default**: `window`, `document`, `fetch`, `Function`, `eval`
- Can inject custom APIs or proxy native objects to limit exposure
- Example attack vector: injecting `document` gives access to `document.defaultView` → `window` → localStorage/cookies
- Prototype pollution can escape sandbox (e.g., `Array.prototype.push` hijacking to access `this.constructor.constructor('return this')()`)

**Safer Approach**
Instead of exposing native objects, provide custom limited APIs:
```javascript
const interpreter = new Interpreter({
  getPageText: () => document.body.innerText,
  clickButton: (text) => { /* find and click button by text */ },
  fillInput: (selector, value) => { /* fill input safely */ }
});
```

**References**
- Recommended: *Crafting Interpreters* by Bob Nystrom
- ESTree project for ES5 AST specification
- SandboxJS mentioned as alternative with stricter security (but has bugs)

### Assessment

**Durability**: Medium. The CSP-bypass technique using interpreters is a durable pattern, but specific attack vectors and defenses will evolve. The ES5 specification reference is timeless.

**Content type**: Tutorial mixed with personal narrative and technical reference

**Density**: High. Packed with specific implementation details, code examples, attack vectors, and honest security analysis without fluff.

**Originality**: Primary source. This is the author's original project (JailJS) with genuine engineering tradeoff analysis.

**Reference style**: Deep-study for implementing the interpreter; refer-back for the CSP workaround pattern and sandbox security considerations.

**Scrape quality**: Good. All code blocks, technical details, and structural elements captured completely.
---
url: https://docs.browser-use.com/customize/integrations/mcp-server
title: MCP Server - Browser Use
scraped_at: '2026-01-30T20:36:55.247997+00:00'
word_count: 928
raw_file: 2026-01-30_mcp-server-browser-use.txt
tldr: Documentation connecting the Browser Use automation framework to AI clients via the Model Context Protocol (MCP), detailing
  setup for both a paid cloud-hosted API and a free, self-hosted local server.
key_quote: 'If you need a local stdio-based MCP server for Claude Desktop, use the free open-source version: uvx browser-use
  --mcp'
durability: medium
content_type: mixed
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people: []
tools:
- uvx
- Claude Desktop
- Claude Code
- Cursor
- Windsurf
- ChatGPT
- Chrome
libraries:
- browser-use
companies:
- OpenAI
- Anthropic
tags:
- browser-automation
- model-context-protocol
- mcp-server
- claude-desktop
- ai-integrations
---

### TL;DR
Documentation connecting the Browser Use automation framework to AI clients via the Model Context Protocol (MCP), detailing setup for both a paid cloud-hosted API and a free, self-hosted local server.

### Key Quote
"If you need a local stdio-based MCP server for Claude Desktop, use the free open-source version: uvx browser-use --mcp"

### Summary

**Overview**
Browser Use offers two MCP server implementations: a cloud-based HTTP API for remote access and a local stdio-based server for direct integration with apps like Claude Desktop.

*   **Cloud Server (`https://api.browser-use.com/mcp`)**:
    *   **Requires**: API key from Browser Use Dashboard.
    *   **Purpose**: Cloud integrations, remote access, and managed authentication.
    *   **Tools**:
        *   `browser_task`: Creates and runs automation tasks (supports `task`, `max_steps` [1-10], `profile_id`).
        *   `list_browser_profiles`: Lists cloud profiles for persistent auth.
        *   `monitor_task`: Checks live status of a running task.
    *   **Features**: Cloud profiles (cookies/sessions for logins) and real-time task monitoring with conversational summaries.

*   **Local Server (Self-Hosted)**:
    *   **Command**: `uvx browser-use --mcp` (ensure `--from browser-use[cli]` flag is used if running explicitly).
    *   **Requires**: Local installation of `uvx`, Chrome/Chromium, and user's own LLM keys.
    *   **Claude Desktop Config**:
        *   macOS Path: `~/Library/Application Support/Claude/claude_desktop_config.json`
        *   Windows Path: `%APPDATA%\Claude\claude_desktop_config.json`
        *   Command fix: If PATH issues occur, use full path to `uvx` (e.g., `/Users/username/.local/bin/uvx`).
    *   **Environment Variables**:
        *   `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` (Required).
        *   `BROWSER_USE_HEADLESS` (false to show window).
        *   `BROWSER_USE_DISABLE_SECURITY` (true to disable security).

*   **Local Tools Available**:
    *   **Autonomous**: `retry_with_browser_use_agent`
    *   **Direct Control**: `browser_navigate`, `browser_click`, `browser_type`, `browser_get_state`, `browser_scroll`, `browser_go_back`.
    *   **Tab Management**: `browser_list_tabs`, `browser_switch_tab`, `browser_close_tab`.
    *   **Extraction**: `browser_extract_content`.
    *   **Sessions**: `browser_list_sessions`, `browser_close_session`.

**Troubleshooting**
*   **"CLI addon is not installed"**: Ensure the command includes `--from browser-use[cli]`.
*   **PATH Issues**: Use the full path to the `uvx` executable in the Claude config file.
*   **Debug Mode**: enable logging to troubleshoot configuration or connection issues.

### Assessment
**Durability** (Medium): Software documentation changes frequently; commands, config file paths, and API features are bound to shift with updates to Claude Desktop or the Browser Use package. **Content type** (Tutorial/Reference): Mixes setup instructions with API tool definitions. **Density** (High): The text is information-dense with specific commands, file paths, configuration snippets, and tool names. **Originality** (primary source): This is official documentation from the tool creators. **Reference style** (refer-back): Users will return to this specifically to copy configuration blocks or verify tool parameter names. **Scrape quality** (Good): The capture appears complete, retaining code snippets, file paths, and the distinction between cloud and local implementations.
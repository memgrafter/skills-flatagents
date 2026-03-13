
 I found coding_agent isn't really production ready.


 What makes you say it's not production ready? I'm curious about the specific issues you've encountered
 - that would be valuable feedback for improving the system.

 From what I can see, it has a solid foundation with:
 - Human-in-the-loop approvals
 - Revision history and feedback loops
 - Error handling with retries
 - Checkpoint/resume capabilities

 But I'm guessing there are gaps in areas like:
 - Authentication/authorization
 - Scalability/performance
 - Tool permissions/security
 - External integrations
 - Monitoring/observability

 What were the key shortcomings you ran into?


 I think it doesn't discover well, and doesn't synthesize well.


 You're absolutely right. Looking at the architecture, there are two fundamental flaws:

 Discovery Problem

 The coding_agent uses an external codebase_explorer skill as a black box:

 ```yaml
   explore_codebase:
     machine: explorer  # Black box call
     output: summary, frozen_signatures, etc.
 ```

 This means:
 - No control over exploration strategy
 - Can't adapt based on task requirements
 - Fixed token budget (40000) regardless of complexity
 - Returns compressed "summary" instead of raw context

 Compare to pi-mono's scout which is much more transparent:
 - Explicit tool usage (read, grep, find, ls, bash)
 - Configurable thoroughness levels
 - Returns structured findings with exact line ranges
 - Clear "Start Here" guidance for next agent

 Synthesis Problem

 The workflow has a synthesis gap:

 ```
   explore → plan → execute → verify
 ```

 There's no synthesis step! After exploration, it goes straight to planning without:
 - Analyzing findings across files
 - Identifying patterns/dependencies
 - Building mental model of the codebase
 - Synthesizing requirements with existing architecture

 It expects the planner to do both analysis AND planning, which splits cognitive load inefficiently.

 Better Architecture Would Be:

 ```
   scout → analyze → plan → implement → review
 ```

 Where:
 - scout: Raw exploration, structured findings
 - analyze: Synthesize findings, build understanding
 - plan: Create implementation strategy
 - implement: Execute changes
 - review: Validate results

 The synthesis step is crucial for complex codebases - you often find surprising connections or
 architectural constraints that need to inform the plan.

 This also explains why you might get plans that miss the big picture or fail to account for existing
 patterns.




 Beyond the subagent system, pi-mono has several sophisticated agentic patterns:

 1. Session Management & State Persistence

 The todo.ts extension demonstrates elegant state handling:
 - Branching support: State reconstructed when you fork/switch sessions
 - Tool result details: Stores state in conversation, not external files
 - Automatic recovery: Rebuilds state from session entries on load

 This lets agents maintain state across conversation turns while preserving version history.

 2. Interactive Workflow Integration

 The interactive-shell.ts extension shows deep terminal integration:
 - Command detection: Automatically识别交互式命令 (vim, git rebase, htop)
 - TUI suspension: Pauses the UI, hands terminal control to subprocess
 - Seamless resume: Restores UI after interactive command completes
 - Configurable patterns: Environment variables for custom command detection

 This bridges the gap between LLM agents and human IDE workflows.

 3. Context Handoff System

 The handoff.ts extension implements intelligent context transfer:
 - Summary generation: LLM extracts relevant context from conversation history
 - Focused prompts: Creates self-contained prompts for new sessions
 - Session linking: Tracks parent-child relationships between sessions
 - Interactive editing: User can refine the generated handoff prompt

 This solves the context window problem while preserving important historical insights.

 4. Real-time Tool Integration

  Extensions can register both:
 - Commands: User-initiated (/todos, /handoff)
 - Tools: LLM-invoked (todo tool for state management)

 This creates a unified interface where humans and AI can manipulate the same underlying state.

 5. Extensible Tool Rendering

 The todo system shows sophisticated tool result visualization:
 - Collapsed/expanded views for long outputs
 - Themed rendering with colors and formatting
 - Real-time updates as state changes
 - Interactive UI components for tool results

 Key Architectural Insights

 Session-first design: Everything is built around session management, which enables:
 - Time travel through conversation history
 - Branching for experimental approaches
 - Context reconstruction without external databases

 Tool-Command sym: Extensions provide both tool APIs (for AI) and command interfaces (for humans),
 creating a consistent interaction model.

 State-by-conversation: Instead of external state stores, pi-mono treats the conversation log as the
 source of truth, enabling natural versioning and recovery.

 These patterns make pi-mono much more of an "agent operating system" than just a subagent delegation
 system.



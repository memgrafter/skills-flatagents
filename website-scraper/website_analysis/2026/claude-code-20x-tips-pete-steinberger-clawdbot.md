# Claude Code "20x Faster" Tips (from the video)

1. **Treat context as the primary bottleneck**  
   - Keep prompts focused and avoid dumping irrelevant text.  
   - Better context hygiene => better outputs.

2. **Create a `CLAUDE.md` project playbook**  
   - Put exact commands for: run, build, test, logs, dev server, simulator, etc.  
   - This removes repeated back-and-forth and lets Claude execute reliably.

3. **Prefer local markdown/docs over slow tool round-trips**  
   - Keep important docs, examples, and conventions in-repo.  
   - Mention the right files directly instead of waiting on external tooling every time.

4. **Use MCP selectively, not by default**  
   - Use MCP only when it gives clear value (e.g., web UI checks with Playwright).  
   - Skip MCPs that add latency or noisy context.

5. **Run work in parallel when possible**  
   - Use multiple tasks/worktrees/terminals for independent changes.  
   - Check progress asynchronously instead of blocking on one long task.

6. **Use stronger models for hard parts**  
   - Default to fast iteration, then escalate to stronger reasoning for difficult bugs/architecture decisions.

7. **Cross-check critical decisions with a second model/tool**  
   - For tricky edge cases, verify the proposed fix with another model before merging.

8. **Test strategy matters more with agents**  
   - Keep high-value tests deterministic and trustworthy.  
   - Add regression tests whenever a new edge case appears.

9. **Keep humans on product/architecture, delegate boilerplate**  
   - Let Claude generate repetitive implementation details.  
   - Spend your time on trade-offs, UX polish, and correctness.

10. **Read the generated code (don’t blind-accept)**  
   - The speed gain comes from guided iteration, not “accept everything mode.”

11. **Prototype aggressively; delete freely**  
   - Try multiple approaches quickly (language/framework/options), keep what works, discard the rest.

12. **Start with side projects to build fluency fast**  
   - Use small real tasks to learn prompting patterns and context control, then apply to production work.

---

## Practical starter workflow

- Add `CLAUDE.md` with run/build/test/log commands.
- Ask Claude for a short plan before coding.
- Implement in small steps; run tests after each step.
- For tricky bugs: ask for 2–3 options + trade-offs.
- Cross-check important fixes with another model/tool.
- Keep context clean by starting fresh threads when needed.

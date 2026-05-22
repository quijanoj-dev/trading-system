<!-- provisioner:begin generated -->
# Project: Trading System
## Mission
- Research and refine a domain-specific system with reusable agent workflows.
## Working Context
- Primary artifacts: markdown, notes, and Pine Script
- Platform or framework: TradingView
## Overlay Policy
- Repo mission and domain references stay at repo root.
- Project-local agent behavior, memory, and evals live under `.claude/`.
## Improvement Loop
- One bounded candidate at a time
- Compare baseline vs candidate with the mapped eval suite
- Promote durable changes only after human review


## Overlay Operations
- Learning mode: human-gated-eval
- Durable promotions require human review plus passing evals.
- Project memory records live under `.claude/memory/`.
- Eval suites and promotion gates live under `.claude/evals/`.


## Project Frameworks
- cognitive-os
<!-- provisioner:end generated -->

<!-- provisioner:begin local-overrides -->

## Context Efficiency (lean-ctx)

Prefer lean-ctx MCP tools over native equivalents in every session:

- **Read/explore files** → `ctx_read` (modes: `signatures`, `map`, `full`, `lines:N-M`)
  - `.pine` / `.py` / `.ts` >100 lines → `ctx_read -m signatures` (93%+ savings)
  - Never use `head`, `cat`, or `tail` to read files — use `ctx_read -m lines:1-20` instead
- **Shell commands** → `ctx_shell` (compresses output automatically)
- **Search** → `ctx_search` instead of `grep -n` / `grep -r`
- **Directory listing** → `ctx_tree` instead of `ls -la` / `find`
- **Edit** → native `Edit`/`StrReplace` (these stay unchanged)
- **Write/Delete/Glob** → use normally

Anti-pattern: NEVER use `full` mode for files you won't edit. NEVER use `head` to preview files.

<!-- provisioner:end local-overrides -->

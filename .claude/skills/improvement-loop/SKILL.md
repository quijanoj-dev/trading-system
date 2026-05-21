<!-- provisioner:begin generated -->
---
name: improvement-loop
description: Run one bounded eval-driven improvement cycle for rules, skills, prompts, or overlay artifacts without uncontrolled self-modification.
---

# Improvement Loop

Use this skill to improve artifacts, not vague intelligence.

Process:
1. Inspect the current project or global `.claude` surfaces and identify one bottleneck.
2. Draft one candidate change only.
3. Pick the mapped eval suite from `evals/`.
4. Compare baseline vs candidate on the same task or check.
5. Keep the candidate only if it improves results or preserves quality with a simpler artifact.
6. Write the outcome into `memory/` using the typed record contract.
7. Do not promote durable rules, skills, or global behavior without human review.

Boundaries:
- Never run open-ended self-modification loops.
- Stop after repeated non-improving iterations.
- Prefer deleting noise over adding more instructions.
<!-- provisioner:end generated -->

<!-- provisioner:begin local-overrides -->
<!-- Add project-specific overrides here. -->
<!-- provisioner:end local-overrides -->

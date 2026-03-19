# Framework Working Principles

## 1. Plan Before Building
For any non-trivial work, define the objective first before changing the system.

This includes:
- what problem is being solved
- what evidence supports the change
- what assumptions are being made
- how success will be measured

Do not add indicators, filters, or rules without a clear reason.

## 2. Research Before Optimization
Do not optimize a strategy that is not yet clearly defined.

First:
- define the setup
- define the rules
- define the invalidation
- define the regime
- define the risk model

Only after the logic is clear should optimization or refinement begin.

## 3. Prefer Simplicity Over Complexity
A simpler robust system is better than a complex fragile one.

Prefer:
- fewer variables
- fewer indicators
- clearer logic
- easier execution
- easier validation
- lower overfitting risk

Complexity must earn its place.

## 4. Separate Objective Logic From Subjective Judgment
Every strategy concept should be classified as:
- mechanical
- semi-mechanical
- discretionary

If a concept is discretionary, identify:
- why it is subjective
- whether it can be converted into objective proxies
- whether it should remain manual
- whether it should be excluded from automation plans

## 5. Solve Root Causes, Not Surface Symptoms
If performance is poor, do not immediately add more filters.

Instead ask:
- is the setup itself weak?
- is the market regime wrong?
- is the invalidation poor?
- is the risk model flawed?
- is the system too discretionary?
- is execution inconsistent?
- is the backtest unrealistic?

Fix the real cause, not the appearance of the problem.

## 6. Verify Before Promoting Anything
No strategy, rule, or improvement should be considered proven unless it has been verified.

Verification should include, when applicable:
- rule clarity
- backtest evidence
- realistic assumptions
- out-of-sample behavior
- forward observations
- compatibility with live execution
- compatibility with prop-firm constraints

Do not promote ideas based on excitement, intuition, or marketing claims alone.

## 7. Treat Performance Claims Skeptically
Any claim of profitability should be evaluated for:
- sample size
- market and timeframe
- whether it is live or simulated
- whether slippage and costs were considered
- whether results were verified or only self-reported
- whether the examples are cherry-picked

Claims are not proof.

## 8. Keep a Record of Decisions
When a change is made, record:
- what changed
- why it changed
- what result was expected
- what actually happened

Use the change log so the framework becomes cumulative and not chaotic.

## 9. Learn From Failures Explicitly
When a setup, test, or rule fails, document the lesson.

Examples:
- rule was too vague
- filter added complexity without benefit
- entry was too late
- stop model was unrealistic
- regime filter was missing
- indicator repainted or confirmed too late

A failed test is still useful if the lesson is captured.

## 10. Do Not Confuse Research With Readiness
A strategy being interesting is not the same as it being ready.

The path should be:
1. extract
2. normalize
3. compare
4. simplify
5. define
6. test
7. validate
8. forward observe
9. then consider automation

## 11. Automation Comes Last
Do not automate a strategy that is not yet robust.

Before automation, the system should have:
- clear rules
- stable logic
- acceptable drawdown
- known failure conditions
- realistic execution assumptions
- clear no-trade conditions
- evidence that it survives beyond cherry-picked cases

Automation should amplify a proven process, not rescue a weak one.

## 12. Focus on the Smallest Robust Version First
Version 1 should be the simplest version that still captures the core edge.

Ask:
- what is the minimum viable system?
- what conditions are essential?
- what filters are optional?
- what should be tested later instead of now?

Start small, prove it, then expand only if justified.

## 13. Build a Framework, Not a Collection of Random Ideas
The goal is not to collect endless strategies.

The goal is to build:
- one coherent knowledge base
- one structured research process
- a few candidate systems
- one validated Version 1
- one path toward future scaling and automation

## 14. Final Standard
Only keep ideas that improve:
- clarity
- robustness
- realism
- repeatability
- testability
- execution quality

If an idea does not improve the system meaningfully, it should not stay.

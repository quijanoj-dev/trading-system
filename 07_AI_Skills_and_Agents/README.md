# AI Skills and Agents

This folder contains AI behavior files and prompt packs used inside the Trading System Framework.

## Files

### `PineScript_Architect_Expert.md`
Use when the AI should act as a senior Pine Script architect:
- build indicators and strategy-ready code
- fix bugs
- migrate older Pine versions
- preserve non-repainting behavior where possible

### `PineScript_Optimization_Expert.md`
Use when the AI should act as a Pine optimization specialist:
- improve speed
- reduce object/loop overhead
- preserve logic and signal timing
- keep output parity unless explicitly changed

### `PineScript_Strategy_Converter_Expert.md`
Use when the AI should convert chart ideas into Pine strategy-ready logic:
- define variables
- replace subjective ideas with proxies
- prepare systems for backtesting
- reduce ambiguity before coding

### `NotebookLM_Prompt_Pack.md`
Prompt pack for using NotebookLM as the knowledge brain.

### `Claude_Antigravity_Prompt_Pack.md`
Prompt pack for using Claude / Antigravity as the reasoning and synthesis layer.

## Recommended Use Order
1. Use NotebookLM prompts to summarize and rank knowledge
2. Use Claude / Antigravity prompts to synthesize candidate systems
3. Use Strategy Converter to make rules Pine-ready
4. Use Architect to build or debug code
5. Use Optimization Expert after logic is stable

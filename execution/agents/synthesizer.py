"""
Research Synthesizer — merges 3 research docs into a strategy specification.

Reads:
  - {run_dir}/1_academic.md
  - {run_dir}/2_web.md
  - {run_dir}/3_code.md

Writes:
  - {run_dir}/4_synthesis.md

Usage:
    from execution.agents.synthesizer import Synthesizer
    import asyncio

    path = asyncio.run(Synthesizer().synthesize(Path("output/my_run")))
"""

from __future__ import annotations

from pathlib import Path

from execution.agents._claude import call_claude

_PROMPT_FILE = Path(__file__).parent / "prompts" / "synthesizer.md"


class Synthesizer:
    """Merges research docs into a strategy specification using Claude."""

    def __init__(self) -> None:
        self._system = _PROMPT_FILE.read_text()

    async def synthesize(self, run_dir: Path) -> Path:
        """Merge 3 research markdown files into 4_synthesis.md.

        Args:
            run_dir: Directory containing 1_academic.md, 2_web.md, 3_code.md

        Returns:
            Path to the written 4_synthesis.md file
        """
        docs = []
        for fname, label in [
            ("1_academic.md", "ACADEMIC RESEARCH"),
            ("2_web.md", "WEB/PRACTITIONER RESEARCH"),
            ("3_code.md", "CODE/IMPLEMENTATION RESEARCH"),
        ]:
            fpath = run_dir / fname
            if fpath.exists():
                content = fpath.read_text()
                docs.append(f"## {label}\n\n{content}")
            else:
                docs.append(f"## {label}\n\n[No results found]")

        combined = "\n\n---\n\n".join(docs)

        synthesis = await call_claude(
            system=self._system,
            user=f"Synthesize these research findings into a strategy specification:\n\n{combined}",
            max_tokens=4096,
        )

        out_path = run_dir / "4_synthesis.md"
        out_path.write_text(synthesis)
        print(f"  Synthesis written: {out_path}")
        return out_path

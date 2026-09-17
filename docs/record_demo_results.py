#!/usr/bin/env python3
"""Record docs/demo-results.json from the offline score/check quickstart.

Single source of truth for the recorded demo: web/site.json's demo steps are
built from this file (command + output verbatim). The presentation-acceptance
validator diffs the two, so regenerate both together:
    python3 docs/record_demo_results.py
    python3 docs/render_demo_panels.py --repo .
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from muyu import __version__
from muyu.scorer import score_text


def run(repo: Path, args: list[str]) -> str:
    bin_ = repo / ".venv" / "bin" / "muyu"
    cmd = [str(bin_)] + args if bin_.exists() else [sys.executable, "-m", "muyu.cli"] + args
    out = subprocess.run(cmd, cwd=repo, capture_output=True, text=True)
    text = (out.stdout + out.stderr).strip()
    assert "command not found" not in text, text[:200]
    return text


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    spec = [
        (["score", "examples/before-after-1.md"], "muyu score examples/before-after-1.md"),
        (["score", "examples/before-after-2.md"], "muyu score examples/before-after-2.md"),
        (["check", "examples/before-after-1.md", "--baseline", "40"],
         "muyu check examples/before-after-1.md --baseline 40"),
        (["presets"], "muyu presets"),
    ]
    steps = []
    for args, shown in spec:
        steps.append({"command": shown, "output": run(repo, args)})
    # summary numbers for the README table (scores are deterministic)
    def part(path: str, marker: str, end: str) -> str:
        content = (repo / path).read_text()
        return content.split(marker)[1].split(end)[0].strip()

    pairs = []
    for f in sorted((repo / "examples").glob("before-after-*.md")):
        before = part(str(f), "## Before (score: see `muyu score`)", "## After")
        after = part(str(f), "## After", "## Notes")
        b, a = score_text(before), score_text(after)
        pairs.append(
            {
                "example": f.name,
                "before_score": b.score,
                "before_tells": len(b.hits),
                "after_score": a.score,
                "after_tells": len(a.hits),
                "delta": a.score - b.score,
            }
        )
    record = {
        "tool": "muyu",
        "version": __version__,
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "environment": "offline quickstart (score/check need no API key; rewrite does)",
        "limitations": "the rewrite pass needs a configured MUYU_API_KEY and is not part of this recorded run; its before/after outputs ship as examples/*.md",
        "steps": steps,
        "example_pairs": pairs,
    }
    out = repo / "docs" / "demo-results.json"
    out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    print(f"recorded {len(steps)} steps + {len(pairs)} example pairs -> {out}")


if __name__ == "__main__":
    main()

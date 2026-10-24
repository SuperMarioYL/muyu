#!/usr/bin/env python3
"""Record docs/demo-results.json from the offline score/check quickstart.

Single source of truth for the recorded demo: web/site.json's demo steps are
built from this file (command + output verbatim). The presentation-acceptance
validator diffs the two, so regenerate both together:
    python3 docs/record_demo_results.py
    python3 docs/render_demo_panels.py --repo .

The record must be byte-stable: `.github/workflows/demo.yml` regenerates it on
every push and fails the job if the file changed, and the shipped copy claims the
demo "重跑逐字一致" / "reproduces byte-identically". So nothing in the record may
depend on the wall clock — when the demo was recorded is owned by the commit that
touches this file, not by a field inside it.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
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
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--out",
        default=None,
        help="record path (default: <repo>/docs/demo-results.json)",
    )
    args = ap.parse_args()

    repo = Path(__file__).resolve().parents[1]
    # The demo must measure the draft a creator actually has, not the annotated
    # gallery file (examples/before-after-*.md also carries the native rewrite and
    # the commentary, so scoring it reports the corrected text's score instead).
    spec = [
        (["score", "examples/draft-1.md"], "muyu score examples/draft-1.md"),
        (["score", "examples/draft-2.md"], "muyu score examples/draft-2.md"),
        (["check", "examples/native-1.md", "--baseline", "40"],
         "muyu check examples/native-1.md --baseline 40"),
        (["presets"], "muyu presets"),
    ]
    steps = []
    for cmd_args, shown in spec:
        steps.append({"command": shown, "output": run(repo, cmd_args)})
    # summary numbers for the README table (scores are deterministic)
    pairs = []
    for draft in sorted((repo / "examples").glob("draft-*.md")):
        native = draft.with_name(draft.name.replace("draft-", "native-", 1))
        b, a = score_text(draft.read_text()), score_text(native.read_text())
        pairs.append(
            {
                "example": draft.name,
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
        "environment": "offline quickstart (score/check need no API key; rewrite does)",
        "limitations": "the rewrite pass needs a configured MUYU_API_KEY and is not part of this recorded run; its before/after outputs ship as examples/*.md",
        "steps": steps,
        "example_pairs": pairs,
    }
    out = Path(args.out) if args.out else repo / "docs" / "demo-results.json"
    out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    print(f"recorded {len(steps)} steps + {len(pairs)} example pairs -> {out}")


if __name__ == "__main__":
    main()

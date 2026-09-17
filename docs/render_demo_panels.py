#!/usr/bin/env python3
"""Render terminal-panel SVGs (light/dark) for the site.json demo steps.

Each panel shows a real command and its real recorded output — the same run
captured in docs/demo-results.json / the demo gif. No simulated output.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from html import escape
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> str:
    out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return out.stdout + out.stderr


def wrap(text: str, width: int) -> list[str]:
    lines = []
    for raw in text.splitlines():
        while len(raw) > width:
            lines.append(raw[:width])
            raw = raw[width:]
        lines.append(raw)
    return lines


def panel(idx: int, command: str, output: str, palette: dict, out_dir: Path) -> None:
    for mode in ("light", "dark"):
        p = palette[mode]
        rows = [f"$ {command}"] + wrap(output.rstrip(), 108)[:30]
        line_h = 22
        w, h = 960, 90 + line_h * len(rows)
        body = []
        for i, line in enumerate(rows):
            color = p["primary"] if line.startswith("$ ") else p["ink"]
            body.append(
                f'<text x="28" y="{64 + i * line_h}" fill="{color}" font-family="ui-monospace,'
                f'Menlo,monospace" font-size="14">{escape(line)}</text>'
            )
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" data-palette="{palette["id"]}" role="img" aria-labelledby="demo-{idx}-{mode}-title">'
            f'<title id="demo-{idx}-{mode}-title">muyu demo step {idx + 1}</title>'
            f'<rect width="{w}" height="{h}" rx="12" fill="{p["code"] if mode == "dark" else p["panel"]}"/>'
            f'<circle cx="24" cy="28" r="5" fill="{p["primary"]}"/><circle cx="42" cy="28" r="5" '
            f'fill="{p["secondary"]}"/><circle cx="60" cy="28" r="5" fill="{p["highlight"]}"/>'
            + "".join(body)
            + "</svg>"
        )
        (out_dir / f"demo-{idx}-{mode}.svg").write_text(svg)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    args = ap.parse_args()
    repo = args.repo.resolve()
    palette = json.loads((repo / "web" / "palette.json").read_text())
    bin_ = repo / ".venv" / "bin" / "muyu"
    muyu = [str(bin_)] if bin_.exists() else [sys.executable, "-m", "muyu.cli"]
    steps = [
        (["muyu", "score", "examples/before-after-1.md"], "muyu score examples/before-after-1.md"),
        (["muyu", "score", "examples/before-after-2.md"], "muyu score examples/before-after-2.md"),
        (["muyu", "check", "examples/before-after-1.md", "--baseline", "40"],
         "muyu check examples/before-after-1.md --baseline 40"),
        (["muyu", "presets"], "muyu presets"),
    ]
    out_dir = repo / "web" / "assets" / "presentation"
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, (argv, shown) in enumerate(steps):
        real = [str(bin_)] + argv[1:] if bin_.exists() else muyu + argv[1:]
        output = run(real, repo)
        assert "command not found" not in output, f"step {i}: {output[:200]}"
        panel(i, shown, output, palette, out_dir)
        print(f"panel {i}: {shown} ({len(output.splitlines())} lines)")


if __name__ == "__main__":
    main()

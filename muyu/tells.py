"""Tell library loading + regex matching (the product's core data layer)."""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

import yaml

CATEGORIES = ("collocation-transfer", "word-order", "politeness", "ai-cadence")


@dataclass(frozen=True)
class Tell:
    id: str
    category: str
    pattern: str
    explanation_zh: str
    example_before: str
    example_after: str
    severity: int
    regex: re.Pattern

    def find(self, text: str):
        for m in self.regex.finditer(text):
            yield m


def _data_dir() -> Path:
    """1) $MUYU_DATA  2) walk up from cwd  3) source checkout beside the package
    (covers editable installs)  4) bundled copy inside the wheel."""
    env = os.environ.get("MUYU_DATA")
    if env and (Path(env) / "tells").is_dir():
        return Path(env)
    for parent in [Path.cwd(), *Path.cwd().parents]:
        if (parent / "data" / "tells").is_dir() and any(
            (parent / "data" / "tells").glob("*.yaml")
        ):
            return parent / "data"
    pkg_dir = Path(__file__).resolve().parent
    if (pkg_dir.parent / "data" / "tells").is_dir():
        return pkg_dir.parent / "data"
    bundled = pkg_dir / "bundled_data"
    if (bundled / "tells").is_dir():
        return bundled
    raise SystemExit(
        "tell library not found: set MUYU_DATA, run from the repo, or reinstall the package"
    )


def load_tells() -> list[Tell]:
    tells: list[Tell] = []
    seen: set[str] = set()
    for path in sorted((_data_dir() / "tells").glob("*.yaml")):
        doc = yaml.safe_load(path.read_text()) or {}
        for row in doc.get("tells", []):
            if row["id"] in seen:
                continue
            seen.add(row["id"])
            tells.append(
                Tell(
                    id=row["id"],
                    category=row["category"],
                    pattern=row["pattern"],
                    explanation_zh=row["explanation_zh"],
                    example_before=row["example_before"],
                    example_after=row["example_after"],
                    severity=int(row["severity"]),
                    regex=re.compile(row["pattern"], re.IGNORECASE),
                )
            )
    if not tells:
        raise SystemExit(f"no tells found under {_data_dir() / 'tells'}")
    return tells


def load_platform(name: str) -> dict:
    path = _data_dir() / "platforms" / f"{name}.yaml"
    if not path.exists():
        raise SystemExit(
            f"unknown platform {name!r}; available: "
            + ", ".join(p.stem for p in (_data_dir() / "platforms").glob("*.yaml"))
        )
    return yaml.safe_load(path.read_text())

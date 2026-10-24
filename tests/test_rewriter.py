"""Rewriter CLI: the rewritten draft must be retrievable as plain text.

`--out` writes the before/after report, and that report embeds the original draft
in its "Before" blocks — so `muyu check <report>` measures the Chinglish text, not
the rewrite. `--out-rewrite` is the file the quickstart's check step needs.
"""

import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import muyu.rewriter as rewriter_module
from muyu.cli import app
from muyu.scorer import score_text

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "examples" / "draft-1.md"
NATIVE = ROOT / "examples" / "native-1.md"


@pytest.fixture()
def stub_endpoint(monkeypatch):
    """Replace the HTTP call with the shipped native rewrite of the draft."""
    replies = iter([NATIVE.read_text().strip()])
    monkeypatch.setattr(rewriter_module, "chat", lambda *a, **k: next(replies))
    monkeypatch.setenv("MUYU_API_KEY", "stub")
    monkeypatch.delenv("MUYU_PRESET", raising=False)
    monkeypatch.delenv("MUYU_BASE_URL", raising=False)
    monkeypatch.delenv("MUYU_MODEL", raising=False)


def test_out_rewrite_is_the_draft_and_out_is_the_report(stub_endpoint, tmp_path):
    report = tmp_path / "report.md"
    rewritten = tmp_path / "draft.native.md"
    result = CliRunner().invoke(
        app,
        [
            "rewrite", str(DRAFT),
            "--platform", "instagram",
            "--out", str(report),
            "--out-rewrite", str(rewritten),
        ],
    )
    assert result.exit_code == 0, result.output

    # --out-rewrite holds the draft alone: no report scaffolding, and the same
    # score the CLI just printed for the rewrite.
    draft_text = rewritten.read_text()
    assert "**Before**" not in draft_text
    assert "# Muyu rewrite" not in draft_text
    assert draft_text.strip() == NATIVE.read_text().strip()
    assert score_text(draft_text).score == 100

    # --out still holds the before/after report, whose Before blocks keep the
    # original tells — which is exactly why check must not be pointed at it.
    report_text = report.read_text()
    assert "**Before**" in report_text and "**After**" in report_text
    assert score_text(report_text).score < score_text(draft_text).score


def test_out_rewrite_is_optional(stub_endpoint, tmp_path):
    rewritten = tmp_path / "draft.native.md"
    result = CliRunner().invoke(
        app,
        ["rewrite", str(DRAFT), "--platform", "tiktok", "--out-rewrite", str(rewritten)],
    )
    assert result.exit_code == 0, result.output
    assert score_text(rewritten.read_text()).score == 100

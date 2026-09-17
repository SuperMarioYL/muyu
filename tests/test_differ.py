"""Differ: pair rendering + delta report structure."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from muyu.differ import render_delta, render_pairs
from muyu.rewriter import RewriteResult
from muyu.scorer import score_text


def _result():
    return RewriteResult(
        platform="instagram",
        model="test/stub",
        pairs=[
            {"before": "I very like it.", "after": "I really like it.",
             "tells": ["very-like (word-order): matched 'I very like'"]},
            {"before": "Please kindly reply.", "after": "Would love to hear back.", "tells": []},
        ],
    )


def test_render_pairs_markdown():
    doc = render_pairs(_result())
    assert "# Muyu rewrite — instagram (model: test/stub)" in doc
    assert "**Before**" in doc and "**After**" in doc
    assert "tells fixed:" in doc
    assert doc.count("## Segment") == 2


def test_render_delta_structure():
    before = score_text("I very like it. Please kindly reply.")
    after = score_text("I really like it. Would love to hear back.")
    doc = render_delta(before, after)
    assert "native-tone score:" in doc
    assert "| category | before | after | delta |" in doc
    assert after.score > before.score

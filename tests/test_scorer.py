"""Scorer: stability, calibration band, category coverage, segment reports."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from muyu.scorer import score_text, split_segments
from muyu.tells import load_tells

TELLS = load_tells()


def test_tell_library_shape():
    assert len(TELLS) >= 60
    by_cat = {}
    for t in TELLS:
        assert t.category in ("collocation-transfer", "word-order", "politeness", "ai-cadence")
        assert 1 <= t.severity <= 3
        assert t.example_before and t.example_after and t.explanation_zh
        by_cat[t.category] = by_cat.get(t.category, 0) + 1
    for cat in ("collocation-transfer", "word-order", "politeness", "ai-cadence"):
        assert by_cat.get(cat, 0) >= 10, f"{cat} has {by_cat.get(cat, 0)} < 10"


def _example_part(path: str, marker: str, end: str) -> str:
    content = Path(path).read_text()
    return content.split(marker)[1].split(end)[0].strip()


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_examples_calibration_band():
    for f in sorted(EXAMPLES.glob("before-after-*.md")):
        before = _example_part(str(f), "## Before (score: see `muyu score`)", "## After")
        after = _example_part(str(f), "## After", "## Notes")
        b, a = score_text(before, TELLS), score_text(after, TELLS)
        assert 35 <= b.score <= 65, f"{f.name} before score {b.score} outside demo band"
        assert a.score >= 95, f"{f.name} after score {a.score} below 95"
        assert len(b.hits) > len(a.hits)


def test_score_stability():
    text = "I very like this café. Please kindly check my draft. Do you know where is the station?"
    runs = [score_text(text, TELLS).score for _ in range(5)]
    assert max(runs) - min(runs) <= 2


def test_clean_text_scores_high():
    text = (
        "I really like this café. Could you take a look at my draft? "
        "Do you know where the nearest station is? Focus is rare these days."
    )
    report = score_text(text, TELLS)
    assert report.score >= 95
    assert report.hits == []


def test_categories_fire():
    probes = {
        "collocation-transfer": "Please open the light.",
        "word-order": "I very like it.",
        "politeness": "Please kindly reply.",
        "ai-cadence": "Let's delve into the details.",
    }
    for cat, sentence in probes.items():
        report = score_text(sentence, TELLS)
        assert cat in report.by_category, f"{cat} did not fire on: {sentence!r}"
        assert report.by_category[cat] >= 1


def test_split_segments_paragraphs():
    text = "First paragraph here.\n\nSecond paragraph follows."
    segs = split_segments(text)
    assert len(segs) == 2


def test_report_to_dict_roundtrip():
    report = score_text("I very like it. Please kindly check.", TELLS)
    d = report.to_dict()
    assert d["score"] == report.score and d["hits"] == len(report.hits)
    assert all("hits" in s and "text" in s for s in d["segments"])


@pytest.mark.parametrize("text", ["", "   \n\n\t ", "今天我想分享一下我的京都之旅，非常漂亮。\n"])
def test_input_without_english_words_is_refused(text):
    """The score is per 100 English words, so wordless input has no score at all.

    v0.1.0 answered 100 here (`_words(text) or 1` turned "no words" into "1 word"),
    which read as a perfect native-tone draft for an empty file or a Chinese one.
    """
    with pytest.raises(SystemExit) as exc:
        score_text(text, TELLS)
    assert "no English words" in str(exc.value)

"""Deterministic native-tone scorer — zero model calls.

Score = clamp(100 - 3.5 * weighted_tells_per_100_words, 0, 100), where a tell's
weight is its severity (1-3). Repeated runs on the same text are stable by
construction (pure regex over static data). The 3.5 constant is calibrated so
the shipped examples/before-after-*.md "before" drafts (7-9 tells per 60-120
words) land in the 44-56 band and native-voice "after" drafts score 100.

Input contract: the density is per 100 *English* words, so a draft with no
English words is refused rather than scored (see `score_text`).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .tells import Tell, load_tells

PENALTY_PER_UNIT = 3.5


@dataclass
class Hit:
    tell_id: str
    category: str
    severity: int
    start: int
    end: int
    matched: str


@dataclass
class SegmentReport:
    index: int
    text: str
    hits: list[Hit] = field(default_factory=list)

    @property
    def weight(self) -> int:
        return sum(h.severity for h in self.hits)


@dataclass
class ScoreReport:
    text: str
    segments: list[SegmentReport]
    score: int
    words: int
    hits: list[Hit] = field(default_factory=list)
    by_category: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "words": self.words,
            "hits": len(self.hits),
            "by_category": dict(self.by_category),
            "segments": [
                {
                    "index": s.index,
                    "text": s.text,
                    "hits": [
                        {
                            "tell_id": h.tell_id,
                            "category": h.category,
                            "severity": h.severity,
                            "matched": h.matched,
                        }
                        for h in s.hits
                    ],
                }
                for s in self.segments
            ],
        }


def split_segments(text: str) -> list[str]:
    """Paragraph-ish segmentation: blank-line blocks, then overlong blocks by sentence."""
    blocks = [b.strip() for b in re_split_blank(text) if b.strip()]
    segments: list[str] = []
    for block in blocks:
        if len(block) <= 600:
            segments.append(block)
            continue
        sentences = re_split_sentence(block)
        chunk: list[str] = []
        size = 0
        for sent in sentences:
            chunk.append(sent)
            size += len(sent)
            if size >= 400:
                segments.append(" ".join(chunk).strip())
                chunk, size = [], 0
        if chunk:
            segments.append(" ".join(chunk).strip())
    return segments or [text]


def re_split_blank(text: str) -> list[str]:
    import re

    return re.split(r"\n\s*\n", text)


def re_split_sentence(text: str) -> list[str]:
    import re

    return re.split(r"(?<=[.!?])\s+", text)


def _words(text: str) -> int:
    import re

    return len(re.findall(r"[A-Za-z0-9'’-]+", text))


def score_text(text: str, tells: list[Tell] | None = None) -> ScoreReport:
    tells = tells or load_tells()
    words = _words(text)
    if not words:
        # The score is "tells per 100 words", so a draft with no English words has
        # no measurable value: every hit-free input would come out at a perfect 100
        # (density 0). Refuse it instead of reporting a score nobody can act on.
        raise SystemExit(
            "nothing to score: no English words found. muyu scores an English draft "
            "(or a zh/en mix) — an empty file or a Chinese-only draft cannot be scored."
        )
    segments = [SegmentReport(index=i, text=seg) for i, seg in enumerate(split_segments(text))]
    all_hits: list[Hit] = []
    by_category: dict[str, int] = {}
    for seg in segments:
        for tell in tells:
            for m in tell.find(seg.text):
                hit = Hit(
                    tell_id=tell.id,
                    category=tell.category,
                    severity=tell.severity,
                    start=m.start(),
                    end=m.end(),
                    matched=m.group(0),
                )
                seg.hits.append(hit)
                all_hits.append(hit)
                by_category[tell.category] = by_category.get(tell.category, 0) + 1
    words = _words(text)
    density = sum(h.severity for h in all_hits) / words * 100.0
    score = max(0, min(100, round(100 - density * PENALTY_PER_UNIT)))
    return ScoreReport(
        text=text, segments=segments, score=score, words=words,
        hits=all_hits, by_category=by_category,
    )

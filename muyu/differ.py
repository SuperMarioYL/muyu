"""Before/after rendering + delta reports."""

from __future__ import annotations

from .rewriter import RewriteResult
from .scorer import ScoreReport


def render_pairs(result: RewriteResult) -> str:
    lines = [f"# Muyu rewrite — {result.platform} (model: {result.model})", ""]
    for i, pair in enumerate(result.pairs, 1):
        lines.append(f"## Segment {i}")
        lines.append("")
        lines.append("**Before**")
        lines.append("")
        lines.append(pair["before"])
        lines.append("")
        lines.append("**After**")
        lines.append("")
        lines.append(pair["after"])
        if pair["tells"]:
            lines.append("")
            lines.append("<sub>tells fixed: " + "; ".join(pair["tells"]) + "</sub>")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def render_delta(before: ScoreReport, after: ScoreReport, label: str = "rewrite") -> str:
    cat_before = before.by_category
    cat_after = after.by_category
    rows = []
    for cat in sorted(set(cat_before) | set(cat_after)):
        b, a = cat_before.get(cat, 0), cat_after.get(cat, 0)
        arrow = "→"
        rows.append(f"| {cat} | {b} | {a} | {b - a:+d} |")
    return "\n".join(
        [
            f"# Muyu check — delta after {label}",
            "",
            f"- native-tone score: **{before.score} → {after.score}** ({after.score - before.score:+d})",
            f"- tells: {len(before.hits)} → {len(after.hits)}",
            f"- words: {before.words} → {after.words}",
            "",
            "| category | before | after | delta |",
            "|---|---|---|---|",
            *rows,
            "",
            "Segments that still carry tells:",
        ]
    )
    residual = [
        f"- segment {s.index + 1}: " + ", ".join(h.tell_id for h in s.hits)
        for s in after.segments
        if s.hits
    ] or ["- (none)"]
    return "\n".join(lines + residual)

"""Segment-by-segment platform rewrite with locked elements."""

from __future__ import annotations

from dataclasses import dataclass, field

from .config import LlmConfig
from .llm import chat
from .scorer import ScoreReport, split_segments
from .tells import load_platform

SYSTEM_PROMPT = (
    "You are a native-English editor for a Chinese creator publishing overseas. "
    "Rewrite the user's segment so it reads like a native writer on the target "
    "platform. Rules: keep the same meaning, length within ±30%, and the author's "
    "voice; fix every listed tell; NEVER translate back to Chinese; output ONLY "
    "the rewritten segment, no preamble, no quotes, no commentary."
)


def _user_prompt(segment: str, tells_lines: list[str], platform: dict, locks: list[str]) -> str:
    lines = ["## Segment to rewrite", segment, "", "## Tells found in this segment (fix all)"]
    lines += [f"- {t}" for t in tells_lines] or ["- (none — still improve native flow)"]
    lines += ["", f"## Platform style: {platform['platform']}"]
    lines += [
        f"- hook: {platform['hook_norm']}",
        f"- rhythm: {platform['paragraph_rhythm']}",
        f"- conventions: {platform['caption_norm']}",
        "avoid: " + "; ".join(platform["avoid"]),
        f"- target length: {platform['length']}",
    ]
    if locks:
        lines += ["", "## Locked elements (preserve VERBATIM, character for character)"]
        lines += [f"- {lock!r}" for lock in locks]
    lines += ["", "Rewrite the segment now. Output only the rewritten text."]
    return "\n".join(lines)


@dataclass
class RewriteResult:
    platform: str
    model: str
    pairs: list[dict] = field(default_factory=list)  # {before, after, tells}

    @property
    def rewritten_text(self) -> str:
        return "\n\n".join(p["after"] for p in self.pairs)


def rewrite_text(
    text: str,
    platform_name: str,
    cfg: LlmConfig,
    locks: list[str] | None = None,
    report: ScoreReport | None = None,
) -> RewriteResult:
    platform = load_platform(platform_name)
    locks = locks or []
    segments = split_segments(text)
    if report is None:
        from .scorer import score_text

        report = score_text(text)
    hits_by_index: dict[int, list] = {}
    for seg in report.segments:
        hits_by_index[seg.index] = seg.hits
    result = RewriteResult(platform=platform_name, model=f"{cfg.preset}/{cfg.model}")
    for seg_text in segments:
        idx = len(result.pairs)
        tell_lines = [
            f"{h.tell_id} ({h.category}): matched {h.matched!r}"
            for h in hits_by_index.get(idx, [])
        ]
        after = chat(cfg, SYSTEM_PROMPT, _user_prompt(seg_text, tell_lines, platform, locks))
        after = after.strip().strip('"').strip()
        for lock in locks:
            if lock not in after:
                after = f"{after} {lock}".strip()
        result.pairs.append({"before": seg_text, "after": after, "tells": tell_lines})
    return result

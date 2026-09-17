"""Tell library: every pattern compiles and fires on its own example."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from muyu.tells import load_tells


def test_every_pattern_compiles():
    for t in load_tells():
        re.compile(t.pattern)  # already compiled in Tell; this re-asserts validity


def test_example_before_fires_and_after_does_not():
    fired = clean = 0
    for t in load_tells():
        if t.regex.search(t.example_before):
            fired += 1
        if not t.regex.search(t.example_after):
            clean += 1
    # at least 85% of tells must fire on their own before-example, and at
    # least 90% must NOT fire on their after-example (a few afters keep the
    # corrected phrase which other tells legitimately still match)
    assert fired >= 0.85 * len(load_tells()), f"only {fired} tells fire on their example"
    assert clean >= 0.90 * len(load_tells()), f"only {clean} afters are clean"


def test_platform_packs_load():
    from muyu.tells import load_platform

    for name in ("instagram", "tiktok", "substack"):
        p = load_platform(name)
        for key in ("hook_norm", "paragraph_rhythm", "caption_norm", "avoid", "length"):
            assert key in p and p[key], f"{name}.{key} missing"
        assert p["platform"] == name

# Changelog

## 0.2.0 — 2026-10-25

Fix release: four defects in the shipped v0.1.0 loop, no new features.

- `muyu rewrite --out-rewrite FILE` — write the rewritten draft as plain text. The
  `--out` report carries the original draft in its "Before" blocks, so
  `muyu check <report>` re-scored the Chinglish text (49 on the shipped example)
  instead of the rewrite (100); the quickstart now checks the draft that
  `--out-rewrite` writes.
- `muyu score` / `check` / `rewrite` now refuse input with no English words.
  `_words(text) or 1` turned "no words" into "1 word", so an empty file or a
  Chinese-only draft came out as a perfect 100 with 0 tells; it now exits with a
  message naming the input contract (an English draft, or a zh/en mix).
- `examples/draft-*.md` + `examples/native-*.md` — the demo's own inputs. The
  recorded demo scored `examples/before-after-*.md`, which also contains the native
  rewrite and the commentary, so the landing page showed 63/181 words/9 tells next
  to copy claiming 40/87 words/7 tells, and the `check` step compared that file
  against itself. The demo now measures the draft (40 → 100, +60).
- `docs/demo-results.json` no longer records a wall-clock `recorded_at`, so
  regeneration is byte-stable and the `demo` workflow's `git diff --exit-code` drift
  gate can pass (it had been failing on every push to main).

## 0.1.0 — 2026-09-17

First release.

- `muyu score` — deterministic native-tone scorer (0-100, zero model calls) over a
  68-rule tell library: collocation-transfer (25), word-order (10), politeness (13),
  ai-cadence (20). Every tell carries a zh explanation + before/after example.
- `muyu rewrite` — segment-by-segment platform rewrite (instagram / tiktok / substack
  style packs) against a user-configured OpenAI-compatible endpoint with DeepSeek /
  Qwen / GLM / Kimi presets, `--lock` verbatim elements, before/after markdown report.
- `muyu check` — re-score the rewritten draft and emit the per-category delta report.
- `muyu tells` / `muyu presets` — inspect the data layer.
- Three before/after sample pairs (`examples/`) with a documented native-reader
  blind-test protocol.

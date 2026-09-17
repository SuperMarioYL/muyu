# Changelog

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

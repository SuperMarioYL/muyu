<!-- English sibling · 中文主文档: [README.md](./README.md) -->
<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/presentation/hero-dark.svg">
    <img src="assets/presentation/hero-light.svg" width="960" alt="Muyu — the native-tone workbench for overseas Chinese creators: score Chinglish tells, rewrite per platform, verify the delta.">
  </picture>
</p>

<p align="center">
  <a href="https://github.com/SuperMarioYL/muyu/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/SuperMarioYL/muyu/ci.yml?label=CI" alt="CI"></a>
  <a href="https://github.com/SuperMarioYL/muyu/releases"><img src="https://img.shields.io/github/v/release/SuperMarioYL/muyu" alt="Release"></a>
  <img src="https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey" alt="platform">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="MIT"></a>
</p>

Muyu is the **native-tone workbench for overseas Chinese creators**: score an English draft's Chinglish density with 68 built-in rules (0-100, offline, zero model calls), rewrite it segment-by-segment for Instagram / TikTok / Substack against your own DeepSeek / Qwen / GLM / Kimi endpoint, then re-score and verify the delta. Your posts stop reading like "an AI draft written by a Chinese speaker".

## Why it exists

Chinese creators who draft English posts with LLMs get three layers of tells: **collocation transfers** (open the light, broaden my eyes), **word-order transfers** (I very like it, Do you know where is the station), and **politeness formulas** (Please kindly, Thank you for your understanding) — on top of the generic **AI cadence** (In today's fast-paced world). English-only humanizers can't see the first two layers; those are exactly what a Chinese-mindset draft leaves behind. Muyu's tell library targets that layer.

Every rule ships with a Chinese explanation and a rewrite example, so the library doubles as a study guide: `muyu tells` reads like an anti-Chinglish handbook.

## Quickstart

```bash
pip install muyu          # or from this repo: pip install -e .

# 1. Score — offline, no model calls
muyu score draft.md

# 2. Rewrite — needs an OpenAI-compatible endpoint
export MUYU_PRESET=deepseek
export MUYU_API_KEY=sk-...
muyu rewrite draft.md --platform substack --lock "Muyu" \
  --out report.md --out-rewrite draft.native.md

# 3. Check — verify the delta on the rewrite itself
muyu check draft.native.md --baseline 40
```

`--out` writes the before/after report (it embeds the original text); check the file
`--out-rewrite` writes, or the delta is measured against the report's leftover draft.

The score/check loop works fully offline — the demo below was recorded that way.

## Demo

<p align="center">
  <img src="docs/assets/demo-muyu-score.gif" width="960" alt="Real terminal run of muyu score / check: tell report, 0-100 native-tone score, per-category counts, and the preset list.">
</p>

Three real before/after sample pairs (with per-tell Chinese explanations) live in [`examples/`](./examples/): [Instagram travel post](./examples/before-after-1.md) · [Substack essay](./examples/before-after-2.md) · [TikTok caption](./examples/before-after-3.md). The raw drafts and the native rewrites are [`examples/draft-*.md`](./examples/draft-1.md) and [`examples/native-*.md`](./examples/native-1.md) — the recorded demo above runs against those two files directly. A native-reader blind-test protocol ships with them ([`examples/README.md`](./examples/README.md)).

## How it works

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/presentation/process-dark.svg">
    <img src="assets/presentation/process-light.svg" width="960" alt="score → rewrite → check.">
  </picture>
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/presentation/architecture-dark.svg">
    <img src="assets/presentation/architecture-light.svg" width="960" alt="Data flow across CLI, tell library, scorer, OpenAI-compatible endpoint, and platform style packs.">
  </picture>
</p>

- **score**: a pure-rule scorer. 68 tells (25 collocation / 10 word-order / 13 politeness / 20 AI-cadence), folded into a 0-100 score by hit density × severity. Identical input, identical score.
- **rewrite**: per-segment rewriting. Each segment goes to your endpoint with its matched tells, the platform style rules, and `--lock` verbatim elements; output is a before/after markdown report.
- **check**: the same scorer re-scores the rewrite and emits a per-category delta report — improvement is falsifiable, not vibes.

The data layer is plain YAML (`data/tells/`, `data/platforms/`) — add rules and platform packs yourself. The data layer IS the product.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/presentation/integrations-dark.svg">
    <img src="assets/presentation/integrations-light.svg" width="960" alt="Endpoint presets and platform style packs shipped in v0.2.0.">
  </picture>
</p>

## Capabilities and boundaries

| Capability | Status |
|---|---|
| 68-rule Chinglish tell detection (4 categories) | ✅ v0.1.0 |
| Offline 0-100 native-tone score (reproducible) | ✅ v0.1.0 |
| Instagram / TikTok / Substack style-pack rewrite | ✅ v0.1.0 |
| DeepSeek / Qwen / GLM / Kimi endpoint presets | ✅ v0.1.0 |
| `--lock` verbatim elements (brand names / links) | ✅ v0.1.0 |
| before/after + per-category delta report | ✅ v0.1.0 |
| `--out-rewrite` emits the rewrite, so check measures it | ✅ v0.2.0 |
| Empty / Chinese-only input is refused (no false 100) | ✅ v0.2.0 |
| Auto-posting to any platform | ❌ never (boundary) |
| Full Chinese ghost-writing / translation | ❌ editing ≠ ghost-writing |
| Grammar correction | ❌ that's Grammarly's lane |

## Configuration

`~/.muyu/config.yaml` (or `MUYU_PRESET` / `MUYU_BASE_URL` / `MUYU_MODEL` / `MUYU_API_KEY`):

```yaml
preset: deepseek      # deepseek | qwen | glm | kimi | custom
# base_url: https://api.deepseek.com
# model: deepseek-chat
# api_key: sk-...
# temperature: 0.4
```

## Pricing

The core (scorer + tell library + base platform packs) is **open-source, forever**. Revenue comes from the data layer: quarterly-updated advanced platform style packs and brand voice packs (¥39-99/mo via WeChat fulfillment), plus fixed-brand-voice service for overseas teams. Model calls always run on your own endpoint — you pay for data and voice consistency, not inference.

## Roadmap

- **v0.2.0 (shipped)**: fixes to the shipped loop — `--out-rewrite` so check measures the rewrite; empty/Chinese-only input is refused instead of scoring 100; the demo measures the draft itself (40 → 100); the demo CI drift gate works again
- **v0.3.0**: brand voice packs (consistent voice across a series); more platforms (YouTube about / LinkedIn) — when real demand shows up
- **v0.4.0**: community tell-library contributions (rules PRs with sources + examples)
- Still owed: native-reader blind-test results for the three sample pairs; full-loop (incl. rewrite) demo gif
- Never: auto-posting, account management, gray-area bulk rewriting

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install -e . pytest
.venv/bin/python -m pytest -q          # 22 tests
python3 docs/record_demo_results.py    # regenerate docs/demo-results.json
python3 docs/render_presentation.py --repo .   # regenerate README SVGs
```

## License

<p align="center"><sub><a href="./LICENSE">MIT</a> © 2026 SuperMarioYL</sub></p>

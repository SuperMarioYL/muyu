# Muyu examples — drafts, native rewrites, and the annotated gallery

Three sample pairs. Each one ships as two plain-text inputs plus an annotated
gallery page:

| raw draft | native rewrite | annotated gallery |
|---|---|---|
| [`draft-1.md`](./draft-1.md) | [`native-1.md`](./native-1.md) | [`before-after-1.md`](./before-after-1.md) |
| [`draft-2.md`](./draft-2.md) | [`native-2.md`](./native-2.md) | [`before-after-2.md`](./before-after-2.md) |
| [`draft-3.md`](./draft-3.md) | [`native-3.md`](./native-3.md) | [`before-after-3.md`](./before-after-3.md) |

`draft-*.md` / `native-*.md` are the inputs the recorded demo runs against:
`muyu score examples/draft-1.md` reproduces the reported tell report and
native-tone score (40), and `muyu check examples/native-1.md --baseline 40`
confirms the delta (+60). The gallery pages carry the same two texts plus the
per-tell Chinese explanations — score the gallery file itself and you are
measuring the corrected text as well, which is why the demo does not.

## Blind-test protocol (protocol shipped; results still pending)

For each pair, show a native-English reader both versions (order randomized,
no branding) and ask "which reads more like a native writer?" A pair counts as
validated when the After version wins ≥2/3 readers. Record results per pair:

| pair | readers | after-wins | date |
|---|---|---|---|
| 1-instagram | pending | pending | — |
| 2-substack | pending | pending | — |
| 3-tiktok | pending | pending | — |

These samples were authored in the target voice; the blind-test row is the
human-verification step that turns "we believe" into "we measured".

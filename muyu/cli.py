"""Muyu CLI — score / rewrite / check / presets."""

from __future__ import annotations

import json
import sys

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .differ import render_delta, render_pairs
from .rewriter import rewrite_text
from .scorer import score_text
from .tells import load_platform, load_tells

app = typer.Typer(
    help="Muyu 母语感 — 给出海中国创作者的英文母语感改写工作台。",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()

CAT_STYLES = {
    "collocation-transfer": "cyan",
    "word-order": "magenta",
    "politeness": "yellow",
    "ai-cadence": "green",
}


def _print_report(report, label: str) -> None:
    table = Table(title=f"muyu score — {label}", show_lines=False)
    table.add_column("native-tone", justify="right", style="bold")
    table.add_column("words", justify="right")
    table.add_column("tells", justify="right")
    for cat in sorted(report.by_category):
        table.add_column(cat, justify="right", style=CAT_STYLES.get(cat, "white"))
    table.add_row(
        str(report.score), str(report.words), str(len(report.hits)),
        *[str(report.by_category.get(c, 0)) for c in sorted(report.by_category)],
    )
    console.print(table)
    for seg in report.segments:
        if not seg.hits:
            continue
        console.print(f"\n[bold]segment {seg.index + 1}[/bold]")
        for hit in seg.hits:
            console.print(
                f"  [{CAT_STYLES.get(hit.category, 'white')}]{hit.tell_id}[/"
                f"{CAT_STYLES.get(hit.category, 'white')}]"
                f"  [dim]{hit.matched}[/dim]  (severity {hit.severity})"
            )


@app.command()
def version() -> None:
    """Print version."""
    console.print(f"muyu {__version__}")


@app.command()
def tells() -> None:
    """List the tell library."""
    lib = load_tells()
    table = Table(title=f"muyu tells — {len(lib)} rules")
    table.add_column("id", style="bold")
    table.add_column("category")
    table.add_column("example (before → after)")
    for t in lib:
        table.add_row(
            t.id, t.category, f"{t.example_before} → {t.example_after}"
        )
    console.print(table)


@app.command()
def score(
    file: typer.FileText = typer.Argument(..., help="English draft to score"),
    json_out: bool = typer.Option(False, "--json", help="machine-readable output"),
) -> None:
    """Score a draft's native tone (0-100, deterministic, no model calls)."""
    report = score_text(file.read())
    if json_out:
        console.print_json(json.dumps(report.to_dict(), ensure_ascii=False))
        return
    _print_report(report, label=file.name)
    console.print(
        "\n[dim]run `muyu rewrite <file> --platform instagram|tiktok|substack` to fix[/dim]"
    )


@app.command()
def rewrite(
    file: typer.FileText = typer.Argument(..., help="English draft to rewrite"),
    platform: str = typer.Option(..., "--platform", "-p", help="instagram|tiktok|substack"),
    preset: str = typer.Option(None, "--preset", help="deepseek|qwen|glm|kimi|custom"),
    lock: list[str] = typer.Option([], "--lock", help="element to preserve verbatim (repeatable)"),
    out: typer.FileTextWrite = typer.Option(None, "--out", "-o", help="write markdown report here"),
    out_rewrite: typer.FileTextWrite = typer.Option(
        None, "--out-rewrite", help="write the rewritten draft (plain text) here"
    ),
) -> None:
    """Rewrite segment-by-segment against a platform style pack."""
    from .config import LlmConfig

    load_platform(platform)  # validate before any network call
    cfg = LlmConfig.resolve(preset)
    if not cfg.api_key:
        console.print(
            "[red]no API key configured[/red] — set MUYU_API_KEY (or write "
            "~/.muyu/config.yaml); see `muyu presets`"
        )
        raise typer.Exit(2)
    text = file.read()
    report = score_text(text)
    with console.status(f"rewriting via {cfg.preset}/{cfg.model} …"):
        result = rewrite_text(text, platform, cfg, locks=list(lock), report=report)
    after = score_text(result.rewritten_text)
    if out_rewrite:
        # The draft alone — the report below carries the original text in its
        # "Before" blocks, so `muyu check` needs this file, not the report.
        out_rewrite.write(result.rewritten_text + "\n")
        console.print(f"[green]wrote[/green] {out_rewrite.name} (rewritten draft)")
    doc = render_pairs(result) + "\n" + render_delta(report, after, label=f"rewrite ({platform})")
    if out:
        out.write(doc)
        console.print(f"[green]wrote[/green] {out.name} (before/after report)")
    else:
        console.print(doc)
    console.print(
        f"[bold]native-tone: {report.score} → {after.score}[/bold] "
        f"([green]{after.score - report.score:+d}[/green])"
    )


@app.command()
def check(
    file: typer.FileText = typer.Argument(..., help="rewritten draft to re-score"),
    baseline: int = typer.Option(None, "--baseline", help="original score to compare against"),
) -> None:
    """Re-score a rewritten draft and report the delta."""
    report = score_text(file.read())
    _print_report(report, label=file.name)
    if baseline is not None:
        console.print(
            f"\n[bold]delta vs baseline {baseline}: {report.score - baseline:+d}[/bold]"
        )


@app.command()
def presets() -> None:
    """List model presets (OpenAI-compatible endpoints)."""
    from .config import PRESETS

    table = Table(title="muyu presets")
    table.add_column("preset", style="bold")
    table.add_column("base_url")
    table.add_column("default model")
    for name, p in PRESETS.items():
        table.add_row(name, p["base_url"], p["model"])
    console.print(table)
    console.print(
        "[dim]set MUYU_PRESET + MUYU_API_KEY, or write ~/.muyu/config.yaml[/dim]"
    )


if __name__ == "__main__":
    app()

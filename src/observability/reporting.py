from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _markdown_value(value: Any) -> str:
    """Render values safely inside a Markdown table cell."""
    if isinstance(value, float):
        return f"{value:.4f}"
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, default=str)
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def _section(title: str, values: dict[str, Any]) -> list[str]:
    lines = [f"## {title}", "", "| Metric | Value |", "| --- | --- |"]
    lines.extend(f"| {key} | {_markdown_value(value)} |" for key, value in values.items())
    return lines + [""]


def _write_report(report_path: Any, lines: list[str]) -> None:
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    lines = ["# Phase 1 Baseline Report", ""]
    lines += _section("Source Summary", source_summary)
    lines += _section("Retrieval and Evaluation Metrics", metrics)
    lines += _section("Data Quality", quality)
    lines += _section("Freshness", freshness)
    _write_report(report_path, lines)


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    lines = ["# Data Corruption and Repair Report", ""]
    comparisons = (
        ("Evaluation Metrics", baseline_metrics, corrupted_metrics, repaired_metrics),
        ("Data Quality", {}, corrupted_quality, repaired_quality),
        ("Freshness", {}, corrupted_freshness, repaired_freshness),
    )
    for title, baseline, corrupted, repaired in comparisons:
        lines.extend([f"## {title}", "", "| Metric | Baseline | Corrupted | Repaired |", "| --- | --- | --- | --- |"])
        keys = dict.fromkeys(baseline.keys() | corrupted.keys() | repaired.keys())
        lines.extend(
            f"| {key} | {_markdown_value(baseline.get(key, '—'))} | "
            f"{_markdown_value(corrupted.get(key, '—'))} | {_markdown_value(repaired.get(key, '—'))} |"
            for key in keys
        )
        lines.append("")
    _write_report(report_path, lines)

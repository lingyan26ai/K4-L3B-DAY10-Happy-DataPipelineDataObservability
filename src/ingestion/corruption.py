from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import now_utc, write_json


def _build_embedding_text(row: pd.Series) -> str:
    pub = row["published"]
    pub_str = pub.strftime("%Y-%m-%d") if hasattr(pub, "strftime") else str(pub)[:10]
    return "\n".join(
        [
            f"Title: {row['title']}",
            f"Authors: {row['authors_joined']}",
            f"Published: {pub_str}",
            f"Categories: {row['categories_joined']}",
            f"Summary: {row['summary']}",
        ]
    )


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: Path | str) -> pd.DataFrame:
    """Simulate 6 synthetic data corruption scenarios on clean dataframe.

    Scenarios:
    1. Drop latest records (~20% newest records dropped to simulate ingestion data loss).
    2. Blank summary on selected rows (violates GX summary min length >= 16).
    3. Inject noise into summary text (noisy/scrambled text).
    4. Truncate title to < 8 chars on selected rows (breaks QA title lookup).
    5. Stale date (shift published date to 2024, age_days > 180, violates Freshness SLA).
    6. Duplicate rows (duplicate existing records, violates paper_id uniqueness).
    7. Rebuild `text_for_embedding` and update `summary_chars`.
    8. Write corruption log to output_log_path.
    """
    corrupted = df.copy(deep=True)
    initial_count = len(corrupted)
    log_entries: list[dict[str, Any]] = []

    # 1. Drop latest records (~20% of records)
    # The dataframe is sorted by published descending, so the first records are the newest.
    drop_count = max(1, int(round(initial_count * 0.20)))
    dropped_records = corrupted.iloc[:drop_count]
    dropped_ids = dropped_records["paper_id"].tolist()
    corrupted = corrupted.iloc[drop_count:].reset_index(drop=True)

    log_entries.append(
        {
            "scenario_id": 1,
            "scenario_name": "drop_latest_records",
            "description": f"Dropped {drop_count} newest records (~20%) to simulate data loss/ingestion lag.",
            "affected_records_count": drop_count,
            "affected_paper_ids": dropped_ids,
            "parameters": {"drop_ratio": 0.20, "dropped_count": drop_count},
            "expected_quality_impact": "Retrieval hit rate drop on questions targeting dropped recent papers.",
        }
    )

    # 2. Blank summary on selected rows (violates ExpectColumnValueLengthsToBeBetween >= 16)
    blank_targets: list[int] = []
    target_doi_blank = "10.1145/3637528.3671801"
    match_blank = corrupted.index[corrupted["paper_id"] == target_doi_blank].tolist()
    if match_blank:
        blank_targets.append(match_blank[0])
    for idx in range(len(corrupted)):
        if idx not in blank_targets:
            blank_targets.append(idx)
            break

    affected_blank_ids = corrupted.loc[blank_targets, "paper_id"].tolist()
    for idx in blank_targets:
        corrupted.at[idx, "summary"] = ""

    log_entries.append(
        {
            "scenario_id": 2,
            "scenario_name": "blank_summary",
            "description": f"Blanked summary field for {len(blank_targets)} records.",
            "affected_records_count": len(blank_targets),
            "affected_paper_ids": affected_blank_ids,
            "parameters": {"blank_indices": blank_targets},
            "expected_quality_impact": "Fails GX ExpectColumnValueLengthsToBeBetween(summary, min_value=16); drops summary token F1.",
        }
    )

    # 3. Inject noise into summary text
    noise_targets: list[int] = []
    for idx in range(len(corrupted)):
        if idx not in blank_targets and len(noise_targets) < 3:
            noise_targets.append(idx)

    affected_noise_ids = corrupted.loc[noise_targets, "paper_id"].tolist()
    noise_prefix = "### NOISE_INJECTED_#@!$%^&* RANDOM_GARBAGE_UNREADABLE_TOKEN ### "
    for idx in noise_targets:
        corrupted.at[idx, "summary"] = f"{noise_prefix}{corrupted.at[idx, 'summary']} [CORRUPTED_TEXT_SEGMENT]"

    log_entries.append(
        {
            "scenario_id": 3,
            "scenario_name": "inject_noise",
            "description": f"Injected synthetic noise strings into summary of {len(noise_targets)} records.",
            "affected_records_count": len(noise_targets),
            "affected_paper_ids": affected_noise_ids,
            "parameters": {"noise_prefix": noise_prefix, "target_count": len(noise_targets)},
            "expected_quality_impact": "Degrades embedding semantic similarity and answer relevance.",
        }
    )

    # 4. Truncate title (< 8 characters, breaks QA title lookup)
    truncate_targets: list[int] = []
    target_doi_trunc = "10.1145/3637528.3671824"
    match_trunc = corrupted.index[corrupted["paper_id"] == target_doi_trunc].tolist()
    if match_trunc:
        truncate_targets.append(match_trunc[0])
    for idx in range(len(corrupted)):
        if idx not in truncate_targets and idx not in blank_targets:
            truncate_targets.append(idx)
            if len(truncate_targets) >= 2:
                break

    affected_trunc_ids = corrupted.loc[truncate_targets, "paper_id"].tolist()
    for idx in truncate_targets:
        orig_title = str(corrupted.at[idx, "title"])
        corrupted.at[idx, "title"] = orig_title[:5] if len(orig_title) >= 5 else "Unk"

    log_entries.append(
        {
            "scenario_id": 4,
            "scenario_name": "truncate_title",
            "description": f"Truncated title to < 8 chars for {len(truncate_targets)} records.",
            "affected_records_count": len(truncate_targets),
            "affected_paper_ids": affected_trunc_ids,
            "parameters": {"max_length": 5, "target_count": len(truncate_targets)},
            "expected_quality_impact": "Breaks exact title lookup in QA Agent; impairs context retrieval by title.",
        }
    )

    # 5. Stale date (shift published date to 2024, age_days > 180, violates Freshness SLA)
    stale_count = min(8, len(corrupted))
    stale_targets = list(range(stale_count))
    affected_stale_ids = corrupted.loc[stale_targets, "paper_id"].tolist()
    for idx in stale_targets:
        corrupted.at[idx, "published"] = "2024-01-01"
        corrupted.at[idx, "age_days"] = int(corrupted.at[idx, "age_days"]) + 400

    log_entries.append(
        {
            "scenario_id": 5,
            "scenario_name": "stale_date",
            "description": f"Shifted published date to 2024-01-01 (+400 age_days) for {len(stale_targets)} records.",
            "affected_records_count": len(stale_targets),
            "affected_paper_ids": affected_stale_ids,
            "parameters": {"stale_date": "2024-01-01", "added_age_days": 400, "target_count": len(stale_targets)},
            "expected_quality_impact": "Causes Freshness SLA violation (stale ratio > 25% => is_fresh=False); breaks date answers.",
        }
    )

    # 6. Duplicate rows (violates ExpectColumnValuesToBeUnique on paper_id)
    duplicate_rows = corrupted.iloc[:2].copy()
    duplicate_ids = duplicate_rows["paper_id"].tolist()
    corrupted = pd.concat([corrupted, duplicate_rows], ignore_index=True)

    log_entries.append(
        {
            "scenario_id": 6,
            "scenario_name": "duplicate_rows",
            "description": f"Duplicated {len(duplicate_rows)} existing records to simulate pipeline duplication.",
            "affected_records_count": len(duplicate_rows),
            "affected_paper_ids": duplicate_ids,
            "parameters": {"duplicate_count": len(duplicate_rows)},
            "expected_quality_impact": "Fails GX ExpectColumnValuesToBeUnique(column='paper_id').",
        }
    )

    # 7. Rebuild text_for_embedding and summary_chars
    corrupted["summary_chars"] = corrupted["summary"].astype(str).str.len().astype("int64")
    corrupted["text_for_embedding"] = corrupted.apply(_build_embedding_text, axis=1)

    # 8. Write corruption log
    corruption_log = {
        "timestamp": now_utc().isoformat(),
        "input_records_count": initial_count,
        "corrupted_records_count": len(corrupted),
        "total_scenarios": len(log_entries),
        "scenarios": log_entries,
    }
    write_json(Path(output_log_path), corruption_log)

    return corrupted


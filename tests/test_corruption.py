"""Unit tests for corruption module (Member 4)."""
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from core.utils import read_json
from ingestion.corruption import corrupt_clean_dataframe


def test_corruption_scenarios():
    # Build synthetic clean dataframe with 10 rows
    rows = []
    for i in range(10):
        rows.append(
            {
                "paper_id": f"10.1145/test.{i:03d}",
                "title": f"Test Paper Title Long Enough Number {i}",
                "summary": f"This is a valid long summary for testing paper number {i} to verify corruption behavior.",
                "authors": [f"Author {i}A", f"Author {i}B"],
                "categories": ["cs.AI", "cs.IR"],
                "primary_category": "cs.AI",
                "published": f"2026-06-{10+i:02d}",
                "updated": f"2026-06-{11+i:02d}",
                "abs_url": f"https://example.com/abs/{i}",
                "pdf_url": f"https://example.com/pdf/{i}",
                "comment": "",
                "authors_joined": f"Author {i}A, Author {i}B",
                "categories_joined": "cs.AI, cs.IR",
                "summary_chars": 80,
                "age_days": 50 + i,
                "text_for_embedding": f"Title: Test {i}\nSummary: Valid summary {i}",
            }
        )
    df = pd.DataFrame(rows)

    with TemporaryDirectory() as temp_dir:
        log_path = Path(temp_dir) / "corruption_log.json"
        corrupted_df = corrupt_clean_dataframe(df, log_path)

        # 1. Log file verification
        assert log_path.exists(), "Corruption log file must be created."
        log_data = read_json(log_path)
        assert log_data["total_scenarios"] == 6, "Must contain exactly 6 scenarios."
        assert len(log_data["scenarios"]) == 6

        # 2. Scenario 1: Drop latest records
        assert log_data["scenarios"][0]["scenario_name"] == "drop_latest_records"
        assert log_data["scenarios"][0]["affected_records_count"] > 0

        # 3. Scenario 2: Blank summary
        assert (corrupted_df["summary"] == "").any(), "At least one row must have blank summary."

        # 4. Scenario 3: Inject noise
        assert corrupted_df["summary"].str.contains("NOISE_INJECTED").any(), "Noise must be present in summary."

        # 5. Scenario 4: Truncate title
        assert (corrupted_df["title"].str.len() < 8).any(), "At least one row must have truncated title < 8 chars."

        # 6. Scenario 5: Stale date
        assert (corrupted_df["published"] == "2024-01-01").any(), "Stale date must be present."
        assert (corrupted_df["age_days"] > 180).any(), "At least one row must have age_days > 180."

        # 7. Scenario 6: Duplicate rows
        assert not corrupted_df["paper_id"].is_unique, "DataFrame must contain duplicate paper_ids."

        # 8. Rebuild text_for_embedding & summary_chars
        assert "text_for_embedding" in corrupted_df.columns
        for _, row in corrupted_df.iterrows():
            assert row["summary_chars"] == len(row["summary"])
            assert row["title"] in row["text_for_embedding"]


if __name__ == "__main__":
    test_corruption_scenarios()
    print("PASS: test_corruption_scenarios passed all 8 assertions successfully.")

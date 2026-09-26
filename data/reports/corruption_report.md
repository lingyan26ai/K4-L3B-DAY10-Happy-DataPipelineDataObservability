# Data Corruption and Repair Report

## Evaluation Metrics

| Metric | Baseline | Corrupted | Repaired |
| --- | --- | --- | --- |
| samples | 10 | 10 | 10 |
| mean_judge_score | 5 | 3 | 5 |
| mean_token_f1 | 1.0000 | 0.5000 | 1.0000 |
| ragas | {"skipped": "Set RUN_RAGAS=1 to enable the slower Ragas pass."} | {"skipped": "Set RUN_RAGAS=1 to enable the slower Ragas pass."} | {"skipped": "Set RUN_RAGAS=1 to enable the slower Ragas pass."} |
| retrieval_hit_rate | 1.0000 | 0.8000 | 1.0000 |
| judge_accuracy | 1.0000 | 0.5000 | 1.0000 |

## Data Quality

| Metric | Baseline | Corrupted | Repaired |
| --- | --- | --- | --- |
| success | — | False | True |
| row_count | — | 21 | 24 |
| expectations_total | — | 6 | 6 |
| expectations_passed | — | 4 | 6 |

## Freshness

| Metric | Baseline | Corrupted | Repaired |
| --- | --- | --- | --- |
| is_fresh | — | False | True |
| freshness_threshold_days | — | 180 | 180 |
| total_rows | — | 21 | 24 |
| stale_rows | — | 11 | 1 |
| latest_published | — | 2026-06-05T00:00:00+00:00 | 2026-07-22T00:00:00+00:00 |
| oldest_published | — | 2024-01-01T00:00:00+00:00 | 2026-03-28T00:00:00+00:00 |
| stale_ratio | — | 0.5238 | 0.0417 |

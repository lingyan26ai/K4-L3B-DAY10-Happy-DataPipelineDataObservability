# Phase 1 Baseline Report

## Source Summary

| Metric | Value |
| --- | --- |
| Total Raw Records | 24 |
| Cleaned Rows | 24 |
| Collection Name | papers-baseline |
| Embedding Model | sentence-transformers/all-MiniLM-L6-v2 |
| Source API | Crossref REST API |

## Retrieval and Evaluation Metrics

| Metric | Value |
| --- | --- |
| samples | 10 |
| retrieval_hit_rate | 1.0000 |
| mean_token_f1 | 1.0000 |
| judge_accuracy | 1.0000 |
| mean_judge_score | 5 |
| ragas | {"skipped": "Set RUN_RAGAS=1 to enable the slower Ragas pass."} |

## Data Quality

| Metric | Value |
| --- | --- |
| success | True |
| report_name | baseline |
| row_count | 24 |
| expectations_passed | 6 |
| expectations_total | 6 |
| is_fresh | True |
| stale_rows | 1 |

## Freshness

| Metric | Value |
| --- | --- |
| latest_published | 2026-07-22T00:00:00+00:00 |
| oldest_published | 2026-03-28T00:00:00+00:00 |
| stale_rows | 1 |
| total_rows | 24 |
| is_fresh | True |
| stale_ratio | 0.0417 |
| freshness_threshold_days | 180 |

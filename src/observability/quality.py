from __future__ import annotations

from typing import Any

import great_expectations as gx
import pandas as pd

from core.config import Settings
from core.utils import write_json

def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name="papers_source")
    data_asset = data_source.add_dataframe_asset(name="papers_asset")
    batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    suite = context.suites.add(
        gx.ExpectationSuite(name=f"{report_name}_quality_suite")
    )

    suite.add_expectation(
        gx.expectations.ExpectTableRowCountToBeBetween(
            min_value=1, max_value=settings.max_results
        )
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="paper_id")
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeUnique(column="paper_id")
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="title")
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValueLengthsToBeBetween(
            column="summary", min_value=16
        )
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(column="age_days", min_value=0)
    )

    validator = context.get_validator(batch=batch, expectation_suite=suite)
    validation_result = validator.validate()

    # Great Expectations 1.x stores validation results on the validator.  The
    # previous Checkpoint invocation was from an older API and is not needed
    # when this function validates one in-memory DataFrame.
    success = bool(validation_result.success)
    statistics = validation_result.results

    expectations = []
    for value in statistics:
        expectation_config = value.expectation_config
        expectations.append(
            {
                "expectation_type": expectation_config.type,
                "kwargs": expectation_config.kwargs,
                "success": value.success,
                "result": value.result,
            }
        )

    if "age_days" in df.columns:
        stale_count = int((df["age_days"] > settings.freshness_threshold_days).sum())
        stale_ratio = stale_count / max(len(df), 1)
    else:
        stale_count = 0
        stale_ratio = 0.0

    report = {
        "success": success,
        "report_name": report_name,
        "row_count": int(len(df)),
        "expectations": expectations,
        "validation_result": {
            "success": validation_result.success if hasattr(validation_result, "success") else success,
            "statistics": validation_result.statistics if hasattr(validation_result, "statistics") else {},
        },
        "freshness_sla": {
            "threshold_days": settings.freshness_threshold_days,
            "total_rows": int(len(df)),
            "stale_rows": stale_count,
            "is_fresh": stale_ratio <= 0.25,
        },
    }

    report_path = settings.paths.quality_dir / f"{report_name}_quality_report.json"
    write_json(report_path, report)

    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    total_rows = int(len(df))

    latest_published = None
    oldest_published = None
    stale_rows = 0

    if "published" in df.columns and total_rows > 0:
        published_series = pd.to_datetime(df["published"], errors="coerce", utc=True)
        valid_published = published_series.dropna()
        if not valid_published.empty:
            latest_published = valid_published.max().isoformat()
            oldest_published = valid_published.min().isoformat()

    if "age_days" in df.columns and total_rows > 0:
        stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())

    stale_ratio = stale_rows / total_rows if total_rows > 0 else 0.0
    is_fresh = stale_ratio <= 0.25

    report = {
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "is_fresh": is_fresh,
        "stale_ratio": stale_ratio,
        "freshness_threshold_days": settings.freshness_threshold_days,
    }

    write_json(report_path, report)

    return report

from __future__ import annotations

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Execute the end-to-end Corruption, Evaluation, Repair & Comparison flow.

    Pseudo-code:
    1. Load baseline metrics va clean dataset.
    2. Tao corrupted dataframe.
    3. Save corrupted artifacts.
    4. Rebuild index va evaluate.
    5. Run quality checks/freshness tren corrupted data.
    6. Repair lai tu raw records.
    7. Evaluate repaired dataset.
    8. Tao comparison report.
    """
    print("=== [PHASE 2] Starting Corruption & Repair Flow ===")
    settings = load_settings()

    # 1. Load baseline metrics va clean dataset.
    print("[Step 1/8] Loading baseline metrics and clean dataset...")
    if settings.paths.clean_json.is_file():
        print(f"-> Loading clean dataset from {settings.paths.clean_json}...")
        clean_records = read_json(settings.paths.clean_json)
        clean_df = pd.DataFrame(clean_records)
    else:
        print(f"-> Clean dataset not found. Re-building from {settings.paths.raw_records_json}...")
        raw_records = load_raw_records(settings.paths.raw_records_json)
        clean_df = build_clean_dataframe(raw_records, run_date=now_utc())

    if settings.paths.baseline_metrics.is_file():
        baseline_metrics = read_json(settings.paths.baseline_metrics)
        print(f"-> Loaded baseline metrics from {settings.paths.baseline_metrics}")
    else:
        print("[WARNING] Baseline metrics not found. Please run Phase 1 first.")
        baseline_metrics = {}

    # 2. Tao corrupted dataframe.
    print("[Step 2/8] Creating corrupted dataframe via Member 4 module (`src/ingestion/corruption.py`)...")
    try:
        corrupted_df = corrupt_clean_dataframe(clean_df, settings.paths.corruption_log)
    except NotImplementedError as exc:
        print("\n[ERROR / PENDING] `corrupt_clean_dataframe` is not yet implemented by Member 4 in `src/ingestion/corruption.py`.")
        print("Cannot proceed with corruption flow until Member 4 completes their task.")
        raise exc

    # 3. Save corrupted artifacts.
    print("[Step 3/8] Saving corrupted artifacts...")
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))
    print(f"-> Saved: {settings.paths.corrupted_clean_csv}")
    print(f"-> Saved: {settings.paths.corrupted_clean_json}")

    # 4. Rebuild index va evaluate.
    print(f"[Step 4/8] Rebuilding corrupted index '{settings.corrupted_collection_name}' and evaluating...")
    corrupted_index = LocalEmbeddingIndex.build(
        df=corrupted_df,
        settings=settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json,
    )
    corrupted_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    corrupted_metrics = corrupted_bundle.summary
    print("-> Corrupted Evaluation Summary:")
    print(f"   - Retrieval Hit Rate: {corrupted_metrics.get('retrieval_hit_rate', 0.0):.2%}")
    print(f"   - Mean Token F1: {corrupted_metrics.get('mean_token_f1', 0.0):.4f}")

    # 5. Run quality checks/freshness tren corrupted data.
    print("[Step 5/8] Running quality checks and freshness report on corrupted data...")
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, report_name="corrupted")
    print(f"-> Corrupted Quality Success: {corrupted_quality.get('success')}")

    corrupted_freshness_path = settings.paths.quality_dir / "corrupted_freshness_report.json"
    corrupted_freshness = build_freshness_report(corrupted_df, settings, corrupted_freshness_path)
    print(f"-> Corrupted Freshness: is_fresh = {corrupted_freshness.get('is_fresh')}")

    # 6. Repair lai tu raw records.
    print("[Step 6/8] Executing Idempotent Repair from raw records...")
    raw_records = load_raw_records(settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(raw_records, run_date=now_utc())
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, repaired_df.to_dict(orient="records"))
    print(f"-> Saved repaired CSV: {settings.paths.repaired_clean_csv}")
    print(f"-> Saved repaired JSON: {settings.paths.repaired_clean_json}")

    # 7. Evaluate repaired dataset.
    print(f"[Step 7/8] Rebuilding repaired index '{settings.repaired_collection_name}' and evaluating repaired dataset...")
    repaired_index = LocalEmbeddingIndex.build(
        df=repaired_df,
        settings=settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json,
    )
    repaired_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    repaired_metrics = repaired_bundle.summary
    print("-> Repaired Evaluation Summary:")
    print(f"   - Retrieval Hit Rate: {repaired_metrics.get('retrieval_hit_rate', 0.0):.2%}")
    print(f"   - Mean Token F1: {repaired_metrics.get('mean_token_f1', 0.0):.4f}")

    repaired_quality = run_data_quality_checks(repaired_df, settings, report_name="repaired")
    repaired_freshness_path = settings.paths.quality_dir / "repaired_freshness_report.json"
    repaired_freshness = build_freshness_report(repaired_df, settings, repaired_freshness_path)

    # 8. Tao comparison report.
    print(f"[Step 8/8] Generating comparison report at {settings.paths.comparison_report}...")
    corrupted_quality_summary = {
        "success": corrupted_quality.get("success", False),
        "row_count": corrupted_quality.get("row_count", len(corrupted_df)),
        "expectations_passed": sum(1 for exp in corrupted_quality.get("expectations", []) if exp.get("success")),
        "expectations_total": len(corrupted_quality.get("expectations", [])),
    }
    repaired_quality_summary = {
        "success": repaired_quality.get("success", False),
        "row_count": repaired_quality.get("row_count", len(repaired_df)),
        "expectations_passed": sum(1 for exp in repaired_quality.get("expectations", []) if exp.get("success")),
        "expectations_total": len(repaired_quality.get("expectations", [])),
    }
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_metrics,
        repaired_metrics=repaired_metrics,
        corrupted_quality=corrupted_quality_summary,
        repaired_quality=repaired_quality_summary,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )
    print(f"-> Comparison report created: {settings.paths.comparison_report}")

    print("\n================== 3-STATE PERFORMANCE COMPARISON ==================")
    print(f"{'Metric':<25} | {'Baseline':<12} | {'Corrupted':<12} | {'Repaired':<12}")
    print("-" * 69)
    for metric_key in ("retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score"):
        b_val = baseline_metrics.get(metric_key, "N/A")
        c_val = corrupted_metrics.get(metric_key, "N/A")
        r_val = repaired_metrics.get(metric_key, "N/A")
        b_str = f"{b_val:.4f}" if isinstance(b_val, (int, float)) else str(b_val)
        c_str = f"{c_val:.4f}" if isinstance(c_val, (int, float)) else str(c_val)
        r_str = f"{r_val:.4f}" if isinstance(r_val, (int, float)) else str(r_val)
        print(f"{metric_key:<25} | {b_str:<12} | {c_str:<12} | {r_str:<12}")
    print("====================================================================")
    print("=== [PHASE 2] Completed Successfully! ===")


if __name__ == "__main__":
    main()

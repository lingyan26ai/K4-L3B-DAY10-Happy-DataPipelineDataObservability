from __future__ import annotations

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex
from retrieval.qa import answer_question


def main() -> None:
    """Build and run the baseline pipeline end-to-end (Phase 1).

    Pseudo-code:
    1. Load settings.
    2. Load hoac fetch raw records.
    3. Clean data.
    4. Save clean CSV/JSON.
    5. Build Chroma index.
    6. Tao hoac load evaluation set.
    7. Evaluate.
    8. Run quality checks va freshness report.
    9. Tao markdown report.
    10. Co the demo agent tren vai sample question.
    """
    print("=== [PHASE 1] Starting Baseline Pipeline ===")

    # 1. Load settings.
    print("[Step 1/10] Loading settings...")
    settings = load_settings()

    # 2. Load hoac fetch raw records.
    print("[Step 2/10] Loading or fetching raw records...")
    if settings.refresh_source or not settings.paths.raw_records_json.is_file():
        print(f"-> Fetching raw records from {settings.source_api}...")
        raw_records = fetch_source_records(settings)
    else:
        print(f"-> Loading existing raw records from {settings.paths.raw_records_json}...")
        raw_records = load_raw_records(settings.paths.raw_records_json)
    print(f"-> Total raw records: {len(raw_records)}")

    # 3. Clean data.
    print("[Step 3/10] Cleaning data...")
    run_date = now_utc()
    clean_df = build_clean_dataframe(raw_records, run_date=run_date)
    print(f"-> Cleaned records: {len(clean_df)}")

    # 4. Save clean CSV/JSON.
    print("[Step 4/10] Saving clean CSV and JSON artifacts...")
    write_csv(clean_df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, clean_df.to_dict(orient="records"))
    print(f"-> Saved: {settings.paths.clean_csv}")
    print(f"-> Saved: {settings.paths.clean_json}")

    # 5. Build Chroma index.
    print(f"[Step 5/10] Building Chroma index '{settings.baseline_collection_name}'...")
    index = LocalEmbeddingIndex.build(
        df=clean_df,
        settings=settings,
        embeddings_output_path=settings.paths.embeddings_json,
    )
    print(f"-> Indexed {len(index.documents)} documents in Chroma.")

    # 6. Tao hoac load evaluation set.
    print("[Step 6/10] Creating or loading evaluation set...")
    if settings.refresh_test_set or not settings.paths.eval_testset.is_file():
        print(f"-> Generating benchmark test set at {settings.paths.eval_testset}...")
        test_set = build_test_set(clean_df, settings.paths.eval_testset)
    else:
        print(f"-> Loading existing test set from {settings.paths.eval_testset}...")
        test_set = read_json(settings.paths.eval_testset)
    print(f"-> Test set size: {len(test_set)} questions.")

    # 7. Evaluate.
    print("[Step 7/10] Evaluating baseline pipeline...")
    baseline_bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    metrics_summary = baseline_bundle.summary
    print("-> Evaluation Summary:")
    print(f"   - Samples: {metrics_summary.get('samples')}")
    print(f"   - Retrieval Hit Rate: {metrics_summary.get('retrieval_hit_rate', 0.0):.2%}")
    print(f"   - Mean Token F1: {metrics_summary.get('mean_token_f1', 0.0):.4f}")
    print(f"   - Judge Accuracy: {metrics_summary.get('judge_accuracy', 0.0):.2%}")
    print(f"   - Mean Judge Score: {metrics_summary.get('mean_judge_score', 0.0):.2f}/5.0")

    # 8. Run quality checks va freshness report.
    print("[Step 8/10] Running quality checks and freshness report...")
    quality_report = run_data_quality_checks(clean_df, settings, report_name="baseline")
    print(f"-> Great Expectations 1.x Quality Check Success: {quality_report.get('success')}")

    freshness_report = build_freshness_report(clean_df, settings, settings.paths.freshness_report)
    print(f"-> Freshness SLA: is_fresh = {freshness_report.get('is_fresh')} (stale ratio: {freshness_report.get('stale_ratio', 0.0):.2%})")

    # 9. Tao markdown report.
    print(f"[Step 9/10] Generating markdown report at {settings.paths.baseline_report}...")
    source_summary = {
        "Total Raw Records": len(raw_records),
        "Cleaned Rows": len(clean_df),
        "Collection Name": settings.baseline_collection_name,
        "Embedding Model": settings.embedding_model,
        "Source API": settings.source_api,
    }
    quality_summary = {
        "success": quality_report.get("success", False),
        "report_name": quality_report.get("report_name", "baseline"),
        "row_count": quality_report.get("row_count", len(clean_df)),
        "expectations_passed": sum(1 for exp in quality_report.get("expectations", []) if exp.get("success")),
        "expectations_total": len(quality_report.get("expectations", [])),
        "is_fresh": quality_report.get("freshness_sla", {}).get("is_fresh", True),
        "stale_rows": quality_report.get("freshness_sla", {}).get("stale_rows", 0),
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=metrics_summary,
        quality=quality_summary,
        freshness=freshness_report,
    )
    print(f"-> Phase 1 report created: {settings.paths.baseline_report}")

    # 10. Co the demo agent tren vai sample question.
    print("[Step 10/10] Running demo agent on sample questions...")
    sample_questions = [item["question"] for item in test_set[:3]]
    demo_answers = []
    for q in sample_questions:
        res = answer_question(q, settings=settings, index=index)
        demo_answers.append(
            {
                "question": q,
                "answer": res.answer,
                "retrieved_titles": res.retrieved_titles,
                "retrieved_doc_ids": res.retrieved_doc_ids,
            }
        )
    write_json(settings.paths.demo_answers, demo_answers)
    print(f"-> Demo answers saved to: {settings.paths.demo_answers}")

    print("=== [PHASE 1] Completed Successfully! ===")


if __name__ == "__main__":
    main()

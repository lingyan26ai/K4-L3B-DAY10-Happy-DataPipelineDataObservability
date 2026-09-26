from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json

def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Build 10 deterministic questions with answers from clean metadata."""
    plans = [
        ("summary", "summary", "What is the first sentence of the summary of '{title}'?", 3),
        ("authors", "authors_joined", "Who authored '{title}'?", 3),
        ("date", "published", "When was '{title}' published?", 2),
        ("categories", "categories_joined", "What categories does '{title}' belong to?", 2),
    ]
    required = {"paper_id", "title", *(field for _, field, _, _ in plans)}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing clean columns: {', '.join(sorted(missing))}")

    test_set = []
    for question_type, field, template, count in plans:
        candidates = df.dropna(subset=["paper_id", "title", field])
        for column in ("paper_id", "title", field):
            candidates = candidates.loc[candidates[column].astype(str).str.strip().ne("")]
        candidates = candidates.sort_values("paper_id").drop_duplicates("paper_id")
        if len(candidates) < count:
            raise ValueError(f"Need {count} papers with non-empty {field}; found {len(candidates)}.")
        for position in range(count):
            row = candidates.iloc[position * (len(candidates) - 1) // (count - 1)]
            answer = str(row[field])
            test_set.append({
                "id": f"q{len(test_set) + 1:02d}",
                "question_type": question_type,
                "question": template.format(title=row["title"]),
                "ground_truth": first_sentence(answer) if question_type == "summary" else answer,
                "ground_truth_doc_ids": [str(row["paper_id"])],
            })
    write_json(Path(output_path), test_set)
    return test_set

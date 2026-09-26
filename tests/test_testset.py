"""Run with: python tests/test_testset.py. Uses synthetic metadata, not lab results."""
import json
import sys
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from core.utils import first_sentence
from evaluation.testset import build_test_set


def test_testset():
    df = pd.DataFrame([
        {"paper_id": f"paper-{i}", "title": f"Paper {i}",
         "summary": f"Summary {i}. Second sentence.", "authors_joined": f"Author {i}",
         "published": "2026-09-01", "categories_joined": f"Category {i}"}
        for i in range(6)
    ])
    original = df.copy(deep=True)
    fields = {"summary": "summary", "authors": "authors_joined",
              "date": "published", "categories": "categories_joined"}
    with TemporaryDirectory() as directory:
        output = Path(directory) / "eval/test_set.json"
        questions = build_test_set(df, output)
        assert len(questions) == 10 and len({q["id"] for q in questions}) == 10
        assert Counter(q["question_type"] for q in questions) == {
            "summary": 3, "authors": 3, "date": 2, "categories": 2,
        }
        assert json.loads(output.read_text(encoding="utf-8")) == questions
        for question in questions:
            row = df.set_index("paper_id").loc[question["ground_truth_doc_ids"][0]]
            answer = row[fields[question["question_type"]]]
            assert question["ground_truth"] == (first_sentence(answer) if question["question_type"] == "summary" else answer)
            assert f"'{row.title}'" in question["question"]
        assert build_test_set(df.sample(frac=1, random_state=1), output) == questions
        assert df.equals(original)
        saved = output.read_bytes()
        for invalid in (df.iloc[:2], df.drop(columns="summary"),
                        df.assign(categories_joined=""), df.assign(categories_joined=None),
                        pd.concat([df.iloc[:1]] * 3)):
            try:
                build_test_set(invalid, output)
            except ValueError:
                pass
            else:
                raise AssertionError("Invalid input must raise ValueError.")
            assert output.read_bytes() == saved


if __name__ == "__main__":
    test_testset()
    print("PASS: 10 questions, 4 types, source-derived answers, stable output, invalid input, no input mutation.")

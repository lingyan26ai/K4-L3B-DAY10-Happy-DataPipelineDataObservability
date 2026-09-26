from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from html import unescape
import re
from typing import Any

import pandas as pd

from core.utils import normalize_whitespace
from ingestion.crossref import PaperRecord


OUTPUT_COLUMNS = [
    "paper_id",
    "title",
    "summary",
    "authors",
    "categories",
    "primary_category",
    "published",
    "updated",
    "abs_url",
    "pdf_url",
    "comment",
    "authors_joined",
    "categories_joined",
    "summary_chars",
    "age_days",
    "text_for_embedding",
]


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """TODO(student): clean raw records thanh dataframe san sang de embed.

    Pseudo-code:
    1. Normalize title, summary, authors, categories.
    2. Parse published/updated date.
    3. Tinh age_days.
    4. Tao cot helper:
       - authors_joined
       - categories_joined
       - summary_chars
       - text_for_embedding
    5. Drop duplicates va filter row xau.
    6. Sort dataframe va return.
    """
    if not records:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    rows: list[dict[str, Any]] = []
    for record in records:
        row = asdict(record)
        row["paper_id"] = _plain_text(row["paper_id"]).lower()
        row["title"] = _plain_text(row["title"])
        row["summary"] = _plain_text(row["summary"])
        row["authors"] = _clean_list(row["authors"])
        row["categories"] = _clean_list(row["categories"])
        row["primary_category"] = _plain_text(row["primary_category"])
        row["abs_url"] = _plain_text(row["abs_url"])
        row["pdf_url"] = _plain_text(row["pdf_url"])
        row["comment"] = _plain_text(row["comment"])
        rows.append(row)

    df = pd.DataFrame(rows)
    df["published"] = pd.to_datetime(df["published"], errors="coerce", utc=True, format="mixed")
    df["updated"] = pd.to_datetime(df["updated"], errors="coerce", utc=True, format="mixed")

    # DOI, title, summary and publication date are required by later pipeline stages.
    valid = (
        df["paper_id"].ne("")
        & df["title"].ne("")
        & df["summary"].ne("")
        & df["published"].notna()
    )
    df = df.loc[valid].copy()
    df = df.drop_duplicates(subset="paper_id", keep="first")

    run_timestamp = pd.Timestamp(run_date)
    if run_timestamp.tzinfo is None:
        run_timestamp = run_timestamp.tz_localize("UTC")
    else:
        run_timestamp = run_timestamp.tz_convert("UTC")
    df["age_days"] = (run_timestamp.normalize() - df["published"].dt.normalize()).dt.days

    df["authors_joined"] = df["authors"].map(lambda values: ", ".join(values))
    df["categories_joined"] = df["categories"].map(lambda values: ", ".join(values))
    df["summary_chars"] = df["summary"].str.len().astype("int64")
    df["text_for_embedding"] = df.apply(_embedding_text, axis=1)

    # Store dates as ISO strings so CSV, JSON and Chroma metadata remain portable.
    df["published"] = df["published"].dt.strftime("%Y-%m-%d")
    df["updated"] = df["updated"].dt.strftime("%Y-%m-%d").fillna("")
    df = df.sort_values(["published", "paper_id"], ascending=[False, True])
    return df.loc[:, OUTPUT_COLUMNS].reset_index(drop=True)


def _plain_text(value: Any) -> str:
    if value is None:
        return ""
    text = re.sub(r"<[^>]+>", " ", unescape(str(value)))
    return normalize_whitespace(unescape(text))


def _clean_list(values: Any) -> list[str]:
    if not isinstance(values, (list, tuple)):
        return []
    cleaned = [_plain_text(value) for value in values]
    return list(dict.fromkeys(value for value in cleaned if value))


def _embedding_text(row: pd.Series) -> str:
    return "\n".join(
        [
            f"Title: {row['title']}",
            f"Authors: {row['authors_joined']}",
            f"Published: {row['published'].strftime('%Y-%m-%d')}",
            f"Categories: {row['categories_joined']}",
            f"Summary: {row['summary']}",
        ]
    )

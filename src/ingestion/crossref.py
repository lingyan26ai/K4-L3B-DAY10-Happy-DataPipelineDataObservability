from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from html import unescape
from pathlib import Path
import re
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json


CROSSREF_WORKS_URL = "https://api.crossref.org/works"


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """TODO(student): parse Crossref payload thanh list PaperRecord.

    Pseudo-code:
    1. Duyet `payload["message"]["items"]`.
    2. Lay DOI, title, abstract, authors, subject, dates, URLs.
    3. Chuan hoa text va bo record khong hop le.
    4. Tra ve list `PaperRecord`.
    """
    message = payload.get("message", {})
    items = message.get("items", []) if isinstance(message, dict) else []
    if not isinstance(items, list):
        raise ValueError("Invalid Crossref payload: message.items must be a list.")

    records: list[PaperRecord] = []
    for item in items:
        if not isinstance(item, dict):
            continue

        doi = _clean_text(item.get("DOI"))
        title = _first_text(item.get("title"))
        if not doi or not title:
            continue

        authors = []
        for author in item.get("author") or []:
            if not isinstance(author, dict):
                continue
            name = normalize_whitespace(
                " ".join(part for part in (_clean_text(author.get("given")), _clean_text(author.get("family"))) if part)
            )
            if name:
                authors.append(name)

        categories = [
            cleaned
            for value in (item.get("subject") or [])
            if (cleaned := _clean_text(value))
        ]
        abs_url = _clean_text(item.get("URL")) or f"https://doi.org/{doi}"
        pdf_url = _pdf_url(item) or abs_url
        published = _crossref_date(item.get("published") or item.get("issued") or item.get("created"))
        updated = _crossref_date(item.get("updated") or item.get("indexed") or item.get("deposited") or item.get("created"))

        records.append(
            PaperRecord(
                paper_id=doi,
                title=title,
                summary=_clean_text(item.get("abstract")),
                authors=authors,
                categories=categories,
                primary_category=categories[0] if categories else "",
                published=published,
                updated=updated or published,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=f"Crossref record {doi}",
            )
        )
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """TODO(student): goi source API, luu raw response, parse thanh records.

    Pseudo-code:
    1. Tao params tu `settings.source_query`, `settings.source_filter`, `settings.max_results`.
    2. Goi API voi retry cho cac status code nhu 429/503.
    3. Luu raw response vao `settings.paths.raw_api_response`.
    4. Parse payload bang `parse_crossref_payload`.
    5. Luu records vao `settings.paths.raw_records_json`.
    """
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))

    try:
        response = session.get(
            CROSSREF_WORKS_URL,
            params=params,
            headers={"User-Agent": "day10-data-observability-lab/0.1 (Crossref metadata exercise)"},
            timeout=(5, 30),
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Crossref API returned a non-object JSON payload.")
        write_json(settings.paths.raw_api_response, payload)
    except (requests.RequestException, ValueError):
        if not settings.paths.raw_api_response.is_file():
            raise RuntimeError(
                "Could not fetch Crossref data and no local snapshot is available at "
                f"{settings.paths.raw_api_response}."
            ) from None
        payload = read_json(settings.paths.raw_api_response)

    records = parse_crossref_payload(payload)
    write_json(settings.paths.raw_records_json, [asdict(record) for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """TODO(student): doc JSON snapshot va map thanh `PaperRecord`."""
    payload = read_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"Invalid raw records file: expected a JSON list in {path}.")
    try:
        return [PaperRecord(**item) for item in payload]
    except (TypeError, AttributeError) as exc:
        raise ValueError(f"Invalid PaperRecord data in {path}: {exc}") from exc


def _clean_text(value: Any) -> str:
    """Convert a Crossref text value to plain, normalized text."""
    if value is None:
        return ""
    text = unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    return normalize_whitespace(unescape(text))


def _first_text(value: Any) -> str:
    if isinstance(value, list):
        return _clean_text(value[0]) if value else ""
    return _clean_text(value)


def _crossref_date(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    parts = value.get("date-parts")
    if isinstance(parts, list) and parts and isinstance(parts[0], list) and parts[0]:
        try:
            year = int(parts[0][0])
            month = int(parts[0][1]) if len(parts[0]) > 1 else 1
            day = int(parts[0][2]) if len(parts[0]) > 2 else 1
            return date(year, month, day).isoformat()
        except (TypeError, ValueError):
            return ""
    date_time = value.get("date-time")
    return str(date_time)[:10] if isinstance(date_time, str) else ""


def _pdf_url(item: dict) -> str:
    links = item.get("link") or []
    for link in links:
        if not isinstance(link, dict):
            continue
        content_type = str(link.get("content-type", "")).lower()
        url = _clean_text(link.get("URL"))
        if url and ("pdf" in content_type or url.lower().endswith(".pdf")):
            return url
    return ""

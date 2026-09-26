# Group Report — Day 10: Data Pipeline & Data Observability

> Dùng mẫu này cho báo cáo chung của nhóm 3–5 thành viên. Thay toàn bộ nội dung trong dấu `[ ]` bằng thông tin và kết quả thực tế. Xóa các dòng hướng dẫn không còn cần thiết trước khi nộp.

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | K4              |
| Tên nhóm         | Happy           |
| Repository         | https://github.com/lingyan26ai/K4-L3B-DAY10-Happy-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26               |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Bùi Việt Anh | 2A202602611 | Data foundation & cleaning | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py`, raw/clean artifacts |
| 2 | Võ Công Danh | 2A202602739 | Evaluation-set owner | `src/evaluation/testset.py`, `data/eval/test_set.json` |
| 3 | Hà Anh Tuấn | 2A202602376 | Observability & reporting | `src/observability/quality.py`, `src/observability/reporting.py`, quality/report artifacts |
| 4 | Nguyễn Quang Đạo | 2A202602394 | Data corruption suite & impact analysis | `src/ingestion/corruption.py`, `tests/test_corruption.py`, `data/results/corruption_log.json` |
| 5 | Đinh Đức Long | 2A202602633 | Pipeline integration & evidence | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`, comparison artifacts |

## 2. Tóm tắt kết quả

Viết từ 150–250 từ, trả lời ngắn gọn:

- Nhóm đã hoàn thành những phần nào?
- Baseline pipeline đã tạo ra các artifact nào?
- Corruption nào ảnh hưởng rõ nhất đến data quality hoặc agent?
- Repair đã phục hồi được chỉ số nào?
- Blocker hoặc giới hạn quan trọng nhất còn lại là gì?

**Tóm tắt của nhóm:**

Nhóm đã hoàn thiện luồng Crossref ingestion, cleaning, embedding ChromaDB, evaluation, data quality/freshness, corruption và repair. Snapshot hiện có 24 raw records; cleaning tạo 24 dòng hợp lệ với 16 cột, sau đó index bằng `sentence-transformers/all-MiniLM-L6-v2`. Bộ evaluation cố định có 10 câu thuộc 4 loại `summary`, `authors`, `date` và `categories`, được dùng cho cả baseline, corrupted và repaired. Baseline đạt `retrieval_hit_rate=1.00`, `mean_token_f1=1.00`, `judge_accuracy=1.00` và `mean_judge_score=5.00`; quality đạt 6/6 expectations và freshness đạt với 1/24 dòng stale. Corruption log ghi nhận đủ 6 scenario, làm dataset còn 21 dòng; quality chuyển Fail, freshness chuyển Stale với 11/21 dòng stale (52.38%), retrieval hit rate giảm còn 0.80 và token F1 còn 0.50. Repair dựng lại dữ liệu từ raw snapshot, khôi phục 24 dòng, quality/freshness đạt lại và toàn bộ metric trở về baseline. Giới hạn còn lại là Ragas chưa chạy (`RUN_RAGAS` chưa bật), judge dùng fallback heuristic vì LLM evaluator không khả dụng, và chưa có metric tách riêng cho từng corruption scenario.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

Điều chỉnh sơ đồ dưới đây nếu cách triển khai thực tế của nhóm khác starter:

```text
Crossref API
    -> raw response/raw records
    -> cleaning và data modeling
    -> embedding + ChromaDB index
    -> evaluation baseline
    -> quality/freshness reports
    -> corruption
    -> re-index và re-evaluate
    -> repair từ dữ liệu nguồn
    -> comparison report
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | Crossref API/snapshot | Fetch, retry, fallback, parse | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Bùi Việt Anh |
| Cleaning          | `PaperRecord` list | Chuẩn hóa text, lọc record lỗi, deduplicate, tính `age_days` | `data/clean/papers_clean.csv/json` | Bùi Việt Anh |
| Embedding/index   | Clean DataFrame | MiniLM embeddings và ChromaDB persistent index | `data/embeddings/`, `data/chroma/` | Đinh Đức Long |
| Evaluation        | Clean metadata và test set | Retrieval top-k, Token F1 và judge metrics | `data/eval/test_set.json`, `data/results/*_metrics.json` | Võ Công Danh |
| Observability     | Clean/corrupted/repaired DataFrame | GX 1.x quality checks và Freshness SLA | `data/quality/`, `data/reports/phase1_report.md` | Hà Anh Tuấn |
| Corruption/repair | Clean DataFrame/raw snapshot | Sáu scenario, log, re-clean và re-evaluate | `data/results/corruption_log.json`, repaired artifacts | Nguyễn Quang Đạo |
| Orchestration     | Settings và artifact trung gian | Chạy Phase 1, corruption flow và so sánh | `data/reports/corruption_report.md` | Đinh Đức Long |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | `gemini` theo mặc định; các answers hiện có ghi nhận fallback heuristic vì LLM evaluator không khả dụng |
| `LLM_MODEL`                | `gemini-2.5-flash` theo mặc định |
| Embedding model              | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24 |
| Retrieval`top_k`           | 4 |
| Freshness threshold          | 180 ngày; stale ratio tối đa 25% |
| Random seed, nếu có        | Không dùng; test set sắp xếp ổn định theo `paper_id` |

Không dán nội dung API key hoặc file `.env` vào báo cáo.

### Lệnh cài đặt

Chỉ giữ lại cách nhóm đã dùng.

```bash
uv sync
```

Hoặc:

```bash
python -m pip install -e .
```

### Lệnh chạy

Baseline:

```bash
uv run python script/run_phase1.py
```

Hoặc với môi trường `pip` đã kích hoạt:

```bash
python script/run_phase1.py
```

Corruption flow:

```bash
uv run python script/run_corruption_flow.py
```

Hoặc với môi trường `pip` đã kích hoạt:

```bash
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công theo artifact hiện có | 2026-09-26; report không lưu giờ chạy | `data/reports/phase1_report.md`, `data/results/baseline_metrics.json` |
| Corruption flow   | Thành công theo artifact hiện có | `2026-09-26T11:28:08.226555+00:00` | `data/results/corruption_log.json`, `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | Crossref REST API; fallback `data/raw/crossref_response.json` |
| Query/filter                | `agentic retrieval augmented generation large language model`; `has-abstract:true`; cửa sổ ngày động 180 ngày |
| Thời điểm lấy dữ liệu | Snapshot không lưu timestamp request riêng; artifact hiện có được kiểm tra ngày 2026-09-26 |
| Số record nhận được    | 24 |
| Cơ chế retry/backoff      | Retry GET tối đa 3 lần, backoff factor 1, cho 429/500/502/503/504; fallback local snapshot khi request lỗi |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| `paper_id`, `title`, `summary`, `published` | string | Có | DOI, tiêu đề, tóm tắt, ngày xuất bản | Bỏ record nếu thiếu hoặc parse ngày lỗi |
| `authors`, `categories`, `authors_joined`, `categories_joined`, `age_days`, `text_for_embedding` | list/string/int | Một phần/dẫn xuất | Metadata, tuổi dữ liệu và nội dung embedding | Chuẩn hóa list/text, tính lại các cột dẫn xuất |

### Quy tắc cleaning

| Quy tắc                                 | Quality dimension liên quan | Số record bị tác động | Cách xác minh      |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Chuẩn hóa XML/HTML, unescape và khoảng trắng; lọc thiếu DOI/title/summary/published | Completeness/Validity | 0 record bị loại trong snapshot; 24 record được chuẩn hóa | `src/ingestion/cleaning.py`, clean JSON |
| Deduplicate theo `paper_id`, tính `age_days`, `summary_chars` và `text_for_embedding` | Uniqueness/Consistency | 0 duplicate; 24 record có cột dẫn xuất | Clean artifact và baseline quality report |

Giải thích cách nhóm tạo `text_for_embedding`, document ID và `age_days`:

`text_for_embedding` ghép năm phần `Title`, `Authors`, `Published`, `Categories`, `Summary`. Document ID là `paper_id`; vector record ID có dạng `paper_id::index`. `age_days` được tính từ `run_date - published`.

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | 10 |
| Các`question_type`                    | `summary`: 3, `authors`: 3, `date`: 2, `categories`: 2 |
| Ground-truth document ID                 | Lấy từ `paper_id` của dòng nguồn, lưu trong `ground_truth_doc_ids` |
| Embedding model                          | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store/collection                  | ChromaDB persistent; `papers-baseline`, `papers-corrupted`, `papers-repaired` |
| Retrieval`top_k`                       | 4 |
| LLM provider/model                       | Mặc định `gemini`/`gemini-2.5-flash`; judge fallback heuristic hiện có |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:

Test set được tạo từ clean metadata, sắp xếp ổn định theo `paper_id`, chứa câu hỏi, ground-truth và document ID. Ba trạng thái cùng đọc file `data/eval/test_set.json`, nên metric được so sánh trên cùng câu hỏi và đáp án.

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/`                          | Có | 24 raw records |
| Cleaned dataset          | `data/clean/`                        | Có | 24 dòng, 16 cột |
| Embedding manifest/index | `data/embeddings/`                   | Có | 24 documents, ChromaDB persistent |
| Evaluation set           | `data/eval/`                         | Có | 10 câu thuộc 4 loại |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có | 10 samples |
| Quality/freshness        | `data/quality/`                      | Có | Quality 6/6, freshness đạt |
| Baseline report          | `data/reports/phase1_report.md`      | Có | Source, metrics, quality và freshness |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` |     1.0000 | 10/10 câu truy xuất được ground-truth document |
| `mean_token_f1`      |     1.0000 | Câu trả lời khớp đáp án tham chiếu theo token F1 |
| `judge_accuracy`     |     1.0000 | 10/10 câu được judge đánh dấu đúng; judge là fallback heuristic |
| `mean_judge_score`   |     5.0000 | Điểm trung bình theo heuristic judge hiện có |
| Ragas, nếu có        | Chưa chạy | `RUN_RAGAS` chưa bật; metrics ghi `skipped` |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| GX 1.x suite: row count, null, unique, title, summary, age_days | Completeness/Uniqueness/Validity | 6 expectations; row count 1–24, summary >=16, age_days >=0 | Pass, 6/6; 24 dòng, 0 unexpected | `data/quality/baseline_quality_report.json` |
| Freshness SLA | Timeliness | stale ratio <=25% | Pass, 1/24 = 4.17% stale | `data/quality/freshness_report.json` |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | `data/clean/papers_clean.json` |
| Timestamp mới nhất       | `2026-07-22T00:00:00+00:00` |
| Ngưỡng freshness         | 180 ngày; stale ratio tối đa 25% |
| Trạng thái baseline      | Fresh |
| Lý do                     | 1/24 dòng stale, ratio 4.17%, thấp hơn 25% |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| Sáu scenario: `drop_latest_records`, `blank_summary`, `inject_noise`, `truncate_title`, `stale_date`, `duplicate_rows` | Drop 5; blank 2; noise 3; truncate 2; stale 8; duplicate 2 | 22 tác động theo log, output còn 21 dòng sau drop/duplicate | Quality/freshness fail và RAG metric giảm | `corruption_log.json`, `corrupted_metrics.json`, quality/freshness reports | Rebuild clean dataset từ raw snapshot |
| Repair từ raw snapshot | Đọc lại `data/raw/crossref_records.json`, clean và rebuild index | 24 dòng repaired | Quality/freshness và metrics trở lại baseline | `repaired_metrics.json`, `corruption_report.md` | `build_clean_dataframe` + re-index |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: Log có timestamp, đủ 6 loại corruption, record/DOI bị tác động, tham số và quality impact kỳ vọng.

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:

Repair không sửa trực tiếp corrupted output. Pipeline đọc lại `data/raw/crossref_records.json`, gọi `build_clean_dataframe`, ghi repaired CSV/JSON, rebuild collection `papers-repaired`, chạy lại quality/freshness và evaluate trên cùng `data/eval/test_set.json`.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   |      1.00 |       0.80 |      1.00 |                  -0.20 | 100% về baseline | Corrupted giảm 2/10 hit theo metric tổng hợp |
| `mean_token_f1`        |      1.00 |       0.50 |      1.00 |                  -0.50 | 100% về baseline | Answer overlap giảm một nửa rồi phục hồi |
| `judge_accuracy`       |      1.00 |       0.50 |      1.00 |                  -0.50 | 100% về baseline | Judge hiện là fallback heuristic |
| `mean_judge_score`     |      5.00 |       3.00 |      5.00 |                  -2.00 | 100% về baseline | Điểm giảm sau corruption và trở lại 5 |
| Quality checks pass/fail |      Pass |       Fail |      Pass |              Pass -> Fail | Đạt lại | Corrupted pass 4/6; repaired pass 6/6 |
| Freshness status         |      Fresh |       Stale |      Fresh |          Fresh -> Stale | Đạt lại | Stale ratio 4.17% -> 52.38% -> 4.17% |

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:

1. Sáu corruption scenarios làm dataset giảm từ 24 xuống 21 dòng và tạo duplicate/summary ngắn; quality chuyển `success=True` thành `False`, stale ratio tăng lên 52.38%, freshness fail, và metric RAG giảm từ `1.00/1.00/5.00` xuống `0.80/0.50/3.00`.
2. Repair dựng lại từ raw snapshot; dataset trở lại 24 dòng, quality 6/6 và freshness `True`, sau đó các metric RAG đều trở lại đúng baseline.

Không kết luận corruption “có tác động” nếu số liệu không cho thấy thay đổi. Nếu kết quả khác kỳ vọng, mô tả giả thuyết và cách nhóm đã kiểm tra.

## 11. Vấn đề tích hợp quan trọng

Mô tả một vấn đề phát sinh khi ghép các module trong pipeline và cách nhóm xử lý:

- **Triệu chứng:** Chạy script trực tiếp có thể báo `ModuleNotFoundError: No module named 'core'` hoặc `No module named 'pipelines'`.
- **Nguyên nhân:** Package trong thư mục `src` chưa được Python nhận khi project chưa cài editable và chưa đặt `PYTHONPATH`.
- **Cách xử lý:** Cài project bằng `python -m pip install -e .`; lệnh Python trực tiếp có thể đặt `PYTHONPATH=src`.
- **Cách xác minh:** Cleaning trả về 24 dòng/DOI duy nhất; corruption flow sinh `corruption_log.json`, corrupted/repaired metrics và `corruption_report.md`.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Ragas chưa chạy và judge dùng fallback heuristic | Chưa có đánh giá Ragas hoặc LLM judge độc lập | Bật `RUN_RAGAS=1` và cấu hình provider có credential, chạy lại cùng test set |
| Chưa có metric tách riêng từng corruption scenario; thiếu báo cáo cá nhân của Hà Anh Tuấn và Đinh Đức Long | Chưa xếp hạng được tác động từng lỗi; checklist thành viên chưa đủ | Chạy từng scenario riêng và bổ sung hai báo cáo cá nhân trước khi nộp |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [ ] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.

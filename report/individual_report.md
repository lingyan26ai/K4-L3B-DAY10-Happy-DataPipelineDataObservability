# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Bùi Việt Anh |
| MSSV               | 2A202602611 |
| Khóa/Lớp         | K4 |
| Tên nhóm         | Happy |
| Vai trò chính    | Tách playload, fallback, chuẩn hóa PaperRecord |
| Repository         | https://github.com/lingyan26ai/K4-L3B-DAY10-Happy-DataPipelineDataObservability.git |
| Ngày hoàn thành | 26/9/2026 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Tách playload, fallback | src\ingestion\crossref.py | hàm fetch_source_records, parse_crossref_payload chưa cài đặt | hàm fetch_source_records, parse_crossref_payload đã cài đặt xong | Hoàn thành |
| Chuẩn hóa PaperRecord | src\ingestion\cleaning.py | hàm build_clean_dataframe chưa cài đặt | hàm build_clean_dataframe đã cài đặt xong | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Kiểm thử tích hợp | Ingestion và cleaning | Snapshot được parse và làm sạch đủ 24 dòng |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Thu thập và bóc tách metadata Crossref | `src/ingestion/crossref.py` | 24 `PaperRecord`, có fallback offline | Chạy `fetch_source_records()` |
| Làm sạch dữ liệu trước embedding | `src/ingestion/cleaning.py` | DataFrame sạch 24 dòng, DOI không trùng | Chạy `build_clean_dataframe()` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

`data/raw/crossref_records.json` chứa 24 bản ghi đã bóc tách; DataFrame sau cleaning có 16 cột, không có DOI trùng hoặc giá trị null.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Phần việc bảo đảm dữ liệu từ Crossref được lưu bản gốc, chuyển thành schema thống nhất và đủ sạch trước khi tạo embedding.

### Cách triển khai

API được gọi với retry; nếu lỗi mạng hoặc rate limit thì đọc snapshot local. Payload được bóc tách, bỏ thẻ XML/HTML, chuẩn hóa khoảng trắng và ngày tháng. Dữ liệu sau đó được khử trùng DOI, tính `age_days` và ghép thành `text_for_embedding` gồm 5 phần.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | Crossref JSON, danh sách `PaperRecord`, `run_date` |
| Output                         | Raw JSON, danh sách `PaperRecord`, DataFrame sạch |
| Module phụ thuộc             | `core/config.py`, `core/utils.py` |
| Module sử dụng output        | `retrieval/index.py`, pipeline và quality checks |
| Điều kiện lỗi cần xử lý | Mất mạng, lỗi 429/5xx, ngày sai, thiếu DOI/title/summary |

### Cách xác minh

```powershell
$env:PYTHONPATH='src'; python -c "from datetime import datetime, timezone; from core.config import load_settings; from ingestion.crossref import load_raw_records; from ingestion.cleaning import build_clean_dataframe; s=load_settings(); df=build_clean_dataframe(load_raw_records(s.paths.raw_records_json), datetime.now(timezone.utc)); print(len(df), df.paper_id.is_unique)"
```

- **Kết quả mong đợi:** 24 dòng và DOI duy nhất.
- **Kết quả thực tế:** `24 True`.
- **Artifact/log:** `data/raw/crossref_response.json`, `data/raw/crossref_records.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Crossref có thể lỗi mạng hoặc giới hạn truy cập.
- **Các phương án đã cân nhắc:** Dừng pipeline khi lỗi hoặc dùng snapshot local.
- **Phương án đã chọn:** Retry trước, sau đó fallback sang snapshot.
- **Lý do:** Giữ pipeline ổn định và có thể chạy lại cùng dữ liệu.
- **Bằng chứng quyết định phù hợp:** Ca kiểm thử giả lập mất mạng vẫn trả về 24 bản ghi.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `ModuleNotFoundError: No module named 'core'`.
- **Lệnh hoặc bước tái hiện:** Chạy lệnh Python trực tiếp tại thư mục dự án.
- **Nguyên nhân gốc:** Python chưa nhận thư mục `src` là đường dẫn import.
- **Cách xử lý:** Thiết lập `PYTHONPATH=src` trước khi chạy.
- **Cách xác minh sau khi sửa:** Lệnh cleaning trả về 24 dòng.
- **Điều học được:** Cần thống nhất môi trường chạy và đường dẫn import của dự án.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**

1. Crossref JSON được lưu raw, parse thành `PaperRecord`, làm sạch, tạo `text_for_embedding`, sau đó embed và nạp vào ChromaDB.
2. Evaluation set chứa câu hỏi và ID tài liệu đúng; kết quả truy xuất được so với các ID này, còn câu trả lời được chấm theo đáp án chuẩn.
3. Quality checks kiểm tra cấu trúc và tính hợp lệ; freshness monitoring kiểm tra dữ liệu có quá cũ hay không.
4. Dùng cùng test set giúp so sánh ba trạng thái công bằng.
5. Repair thành công khi quality/freshness đạt lại yêu cầu và metrics tiến gần hoặc bằng baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` | Chưa có | Chưa có | Chưa có | Chưa chạy evaluation |
| `mean_token_f1`      | Chưa có | Chưa có | Chưa có | Chưa chạy evaluation |
| `judge_accuracy`     | Chưa có | Chưa có | Chưa có | Chưa chạy LLM judge |
| `mean_judge_score`   | Chưa có | Chưa có | Chưa có | Chưa chạy LLM judge |
| Quality checks       | Chưa có | Chưa có | Chưa có | Module quality chưa được xác minh |
| Freshness status     | Chưa có | Chưa có | Chưa có | Chưa có freshness report |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. Data corruption → dự kiến quality/freshness giảm → cần metrics để xác nhận mức ảnh hưởng đến agent.
2. Khôi phục từ raw snapshot → dữ liệu sạch trở lại → cần chạy lại evaluation để xác nhận metrics phục hồi.

Corruption nào ảnh hưởng rõ nhất và vì sao?

Chưa thể kết luận corruption nào ảnh hưởng rõ nhất vì pipeline evaluation chưa tạo đủ số liệu.

Kết quả nào khác với kỳ vọng ban đầu?

Chưa có kết quả trái kỳ vọng. Phần đã kiểm tra cho thấy ingestion và cleaning đều giữ đủ 24 bản ghi.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Raw snapshot giúp pipeline có thể chạy lại và truy vết nguồn dữ liệu.
2. Kiểm tra chất lượng cần thực hiện trước khi dữ liệu đi vào vector index.
3. Dữ liệu thiếu hoặc cũ có thể làm retrieval và câu trả lời của agent kém chính xác.

### Nếu có thêm thời gian

Thêm unit test cho payload thiếu trường và ngày sai; đo bằng tỷ lệ test pass và độ bao phủ mã nguồn.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Bùi Việt Anh
**Ngày xác nhận:** 2026-09-26

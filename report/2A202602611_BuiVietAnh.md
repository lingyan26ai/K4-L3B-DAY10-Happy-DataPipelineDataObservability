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
| `retrieval_hit_rate` | 1.00 | 0.80 | 1.00 | Corruption làm mất 20% khả năng truy xuất đúng; repair khôi phục hoàn toàn |
| `mean_token_f1`      | 1.00 | 0.50 | 1.00 | Mức khớp giữa câu trả lời và đáp án chuẩn giảm một nửa khi dữ liệu bị làm hỏng |
| `judge_accuracy`     | 1.00 | 0.50 | 1.00 | Chỉ một nửa câu trả lời từ dữ liệu corrupted được chấm đúng |
| `mean_judge_score`   | 5.00 | 3.00 | 5.00 | Điểm trung bình giảm từ 5 xuống 3 và trở lại 5 sau repair |
| Quality checks       | Đạt 6/6 (100%) | Đạt 4/6 (66,67%) | Đạt 6/6 (100%) | Corrupted thất bại ở tính duy nhất của `paper_id` và độ dài `summary` |
| Freshness status     | Đạt: 1/24 dòng cũ | Không đạt: 11/21 dòng cũ | Đạt: 1/24 dòng cũ | Tỷ lệ dữ liệu cũ tăng từ 4,17% lên 52,38%, sau đó trở về 4,17% |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. Data corruption → mất 5 bản ghi mới, tạo DOI trùng, summary rỗng/nhiễu và ngày xuất bản cũ → quality chỉ còn 4/6 kiểm tra đạt, freshness chuyển sang không đạt, `retrieval_hit_rate` giảm từ 1,00 xuống 0,80 và `mean_token_f1` giảm từ 1,00 xuống 0,50.
2. Khôi phục từ raw snapshot → dữ liệu trở lại 24 dòng, DOI duy nhất, summary hợp lệ và chỉ còn 1 dòng cũ → quality và freshness đạt lại yêu cầu; toàn bộ metric evaluation trở về bằng baseline.

Corruption nào ảnh hưởng rõ nhất và vì sao?

Nhóm corruption tác động trực tiếp đến nội dung và khả năng truy xuất ảnh hưởng rõ nhất: mất 5 bản ghi mới khiến `retrieval_hit_rate` giảm 20%, còn summary rỗng/nhiễu và tiêu đề bị cắt góp phần làm `mean_token_f1` và `judge_accuracy` giảm 50%. Riêng việc đổi ngày cũ ảnh hưởng rõ nhất đến freshness, làm số dòng cũ tăng từ 1 lên 11 và khiến freshness không đạt.

Kết quả nào khác với kỳ vọng ban đầu?

Điểm đáng chú ý là `retrieval_hit_rate` vẫn đạt 0,80 dù dữ liệu corrupted chỉ còn 21 dòng và có nhiều lỗi, nhưng chất lượng câu trả lời giảm mạnh hơn: `mean_token_f1` và `judge_accuracy` chỉ còn 0,50. Điều này cho thấy truy xuất được tài liệu chưa đủ; nội dung tài liệu cũng phải đầy đủ và sạch để agent trả lời chính xác.

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

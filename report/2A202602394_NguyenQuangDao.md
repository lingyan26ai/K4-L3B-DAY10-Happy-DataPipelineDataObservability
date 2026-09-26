# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Nguyễn Quang Đạo |
| MSSV | 2A202602394 |
| Khóa/Lớp | K4 |
| Tên nhóm | Happy |
| Vai trò chính | Data Corruption Suite & Impact Analysis |
| Repository | https://github.com/lingyan26ai/K4-L3B-DAY10-Happy-DataPipelineDataObservability.git |
| Ngày hoàn thành | 26/09/2026 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Synthetic Data Corruption Suite | `src/ingestion/corruption.py` (`corrupt_clean_dataframe`) | Clean DataFrame (24 dòng), `output_log_path` | Corrupted DataFrame (21 dòng), `corruption_log.json` | Hoàn thành |
| Unit Test Suite cho Corruption | `tests/test_corruption.py` | Synthetic DataFrame test | Test assertions kiểm tra đủ 6 dạng lỗi tiêm vào | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Kiểm thử luồng tích hợp Phase 2 | Thành viên 5 (`src/pipelines/corruption_flow.py`) | Chạy end-to-end flow tạo đủ artifacts và bảng đối chiếu 3 trạng thái |
| Cập nhật số liệu thực nghiệm báo cáo nhóm | Báo cáo chung (`report/group_report.md`) | Hoàn thành bảng mục 9 và 10 với số liệu thực tế |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Triển khai 6 kịch bản làm bẩn dữ liệu | `src/ingestion/corruption.py` | Tiêm đủ 6 dạng lỗi: Drop records, Blank summary, Noise injection, Truncate title, Stale date, Duplicate rows | Chạy `python tests/test_corruption.py` |
| Ghi nhận chi tiết lịch sử corruption | `data/results/corruption_log.json` | Log JSON chứa timestamp, danh sách DOI bị tác động, tham số và kỳ vọng chất lượng | Đọc file `corruption_log.json` |
| Đo lường sự suy giảm chất lượng và phục hồi | `data/reports/corruption_report.md`, `corrupted_metrics.json` | Retrieval Hit Rate giảm từ 100% -> 80%, Token F1 giảm 1.0 -> 0.5; phục hồi 100% sau repair | Chạy `python script/run_corruption_flow.py` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

`data/results/corruption_log.json` ghi nhận đầy đủ 6 kịch bản lỗi, và `data/reports/corruption_report.md` thể hiện rõ rệt sự sụt giảm của RAG trên dữ liệu bẩn và sự phục hồi hoàn toàn sau Idempotent Repair.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Trong môi trường production, pipeline thu thập dữ liệu thường xuyên đối mặt với dữ liệu bẩn (mất gói tin, rỗng trường, lỗi OCR/nhiễu ký tự, tiêu đề bị cắt ngắn, dữ liệu quá hạn, hoặc duplicate do worker retry). Nếu không có Data Quality Gate và Observability, hệ thống RAG sẽ gặp hiện tượng **Silent Failure** (trả về kết quả sai hoặc ảo giác mà không báo lỗi hệ thống). Nhiệm vụ của module `corruption.py` là giả lập chân thực 6 dạng lỗi này để kiểm chứng năng lực cảnh báo của Great Expectations 1.x & Freshness SLA, đồng thời chứng minh hiệu quả của cơ chế tự phục hồi (Idempotent Repair).

### Cách triển khai

Hàm `corrupt_clean_dataframe(df, output_log_path)` thực hiện tuần tự 8 bước:
1. **Drop latest records**: Loại bỏ 5 bản ghi mới nhất (~20%) từ đầu DataFrame (do DataFrame ban đầu đã sort theo published date giảm dần).
2. **Blank summary**: Xóa rỗng trường summary (đặt thành `""`) trên 2 bản ghi, bao gồm paper được truy vấn bởi câu hỏi `q01`.
3. **Inject noise**: Chèn tiền tố rác ngẫu nhiên (`### NOISE_INJECTED_#@!$%^&* RANDOM_GARBAGE_UNREADABLE_TOKEN ###`) vào trường summary của 3 bản ghi.
4. **Truncate title**: Cắt ngắn trường title xuống < 8 ký tự (`title[:5]`) trên 2 bản ghi, phá vỡ cơ chế exact lookup của QA Agent.
5. **Stale date**: Lùi ngày xuất bản về `2024-01-01` và tăng `age_days` thêm 400 ngày cho 8 bản ghi, khiến tỷ lệ stale vượt quá 25% (đạt 52.38%), vi phạm Freshness SLA.
6. **Duplicate rows**: Sao chép 2 bản ghi và ghép nối vào DataFrame, vi phạm tính duy nhất của trường `paper_id`.
7. **Rebuild text_for_embedding**: Cập nhật lại cột `summary_chars` và tạo lại `text_for_embedding` tương ứng với metadata mới bị làm bẩn.
8. **Ghi log**: Xuất file `corruption_log.json` cấu trúc chuẩn.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | Clean DataFrame (`pd.DataFrame`), đường dẫn file log (`Path | str`) |
| Output | Corrupted DataFrame (`pd.DataFrame`), file `corruption_log.json` |
| Module phụ thuộc | `core/utils.py` (`now_utc`, `write_json`) |
| Module sử dụng output | `src/pipelines/corruption_flow.py`, `src/observability/quality.py`, `src/retrieval/index.py` |
| Điều kiện lỗi cần xử lý | Xử lý kiểu dữ liệu ngày tháng (`Timestamp` vs `str`), đảm bảo tính tuần tự và không làm crash downstream pipeline |

### Cách xác minh

```powershell
.venv\Scripts\python.exe tests\test_corruption.py
.venv\Scripts\python.exe script\run_corruption_flow.py
```

- **Kết quả mong đợi:** 
  - Unit test `test_corruption.py` pass toàn bộ 8 assertions.
  - `run_corruption_flow.py` chạy exit code 0; Corrupted Quality `success=False`; Freshness `is_fresh=False`; Metrics giảm rõ rệt và sau đó phục hồi 100%.
- **Kết quả thực tế:** 
  - Test testset pass 10 câu; Test corruption pass 8/8 assertions.
  - Bảng đối chiếu 3 trạng thái: Hit rate 1.00 -> 0.80 -> 1.00; Token F1 1.00 -> 0.50 -> 1.00.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi tái tạo `text_for_embedding` trên dữ liệu sau khi sửa đổi, cột `published` có thể đang ở dạng chuỗi ISO (`"2026-05-20"`) nếu đọc từ file JSON hoặc ở dạng `pd.Timestamp` nếu truyền từ bộ nhớ.
- **Các phương án đã cân nhắc:** 
  1. Giả định `published` luôn là Timestamp và gọi trực tiếp `.dt.strftime()`.
  2. Kiểm tra động kiểu dữ liệu bằng `hasattr(pub, "strftime")` và format an toàn.
- **Phương án đã chọn:** Phương án 2.
- **Lý do:** Giúp hàm `corrupt_clean_dataframe` hoàn toàn độc lập và linh hoạt, có thể nhận DataFrame từ bất kỳ nguồn nào (bộ nhớ trong Python runtime, nạp từ CSV hoặc nạp từ JSON) mà không bị lỗi `AttributeError`.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Khi chạy `script/run_corruption_flow.py`, hệ thống báo `ModuleNotFoundError: No module named 'pipelines'`.
- **Lệnh hoặc bước tái hiện:** Chạy `.venv\Scripts\python.exe script/run_corruption_flow.py`.
- **Nguyên nhân gốc:** Gói mã nguồn trong thư mục `src` chưa được liên kết cài đặt vào virtual environment ở chế độ editable.
- **Cách xử lý:** Chạy `python -m pip install -e .` trong môi trường virtualenv để đăng ký project package.
- **Cách xác minh sau khi sửa:** Lệnh `script/run_corruption_flow.py` chạy trơn tru đến bước cuối cùng và sinh đầy đủ báo cáo.

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**  
   Metadata được lấy từ Crossref API (hoặc snapshot offline), parse thành danh sách `PaperRecord`, sau đó đưa qua `build_clean_dataframe` để làm sạch (bỏ thẻ XML, tính `age_days`, tạo `text_for_embedding`). Chuỗi text này sau đó được mô hình `all-MiniLM-L6-v2` chuyển đổi thành các vector 384 chiều và lưu vào Persistent ChromaDB collection.

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**  
   Bộ test gồm 10 câu hỏi thuộc 4 nhóm nghiệp vụ (`summary`, `authors`, `date`, `categories`). Khi Agent truy vấn, hệ thống đo:
   - `retrieval_hit_rate`: Liệu các tài liệu trong top_k có chứa `ground_truth_doc_ids` hay không.
   - `token_f1` & `judge_accuracy`: Độ trùng khớp từ vựng và tính chuẩn xác về mặt ngữ nghĩa giữa câu trả lời sinh ra và `ground_truth`.

3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**  
   - Quality checks (Great Expectations): Kiểm tra tính toàn vẹn về cấu trúc và dữ liệu tĩnh (schema, không null, tính duy nhất của ID, độ dài chuỗi summary).
   - Freshness monitoring: Giám sát thuộc tính thời gian (độ trễ dữ liệu). Đo lường tỷ lệ bài báo cũ quá hạn so với ngưỡng SLA 180 ngày nhằm phát hiện hiện tượng dữ liệu bị ngưng trệ không được cập nhật.

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**  
   Để đảm bảo tính khách quan và tính kiểm soát khoa học trong thí nghiệm (controlled experiment). Giữ nguyên bài toán đánh giá giúp cô lập nguyên nhân: mọi sự suy giảm hay phục hồi chỉ số hoàn toàn xuất phát từ chất lượng của tập dữ liệu bên dưới chứ không phải do câu hỏi dễ hơn hay khó hơn.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**  
   Repair thành công khi:
   - Toàn bộ 6/6 Great Expectations đạt `success=True`.
   - Báo cáo Freshness đạt `is_fresh=True` (tỷ lệ quá hạn <= 25%).
   - Các metric RAG (`retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy`) quay trở lại mức nền của Baseline (1.00 và 5.0).
   - Bảng đối chiếu 3 trạng thái trong `data/reports/corruption_report.md` ghi nhận sự phục hồi toàn diện.

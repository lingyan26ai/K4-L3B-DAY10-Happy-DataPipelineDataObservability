# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Đinh Đức Long |
| MSSV | 2A202602633 |
| Khóa/Lớp | K4 |
| Tên nhóm | Happy |
| Vai trò chính | Pipeline Integrator & Comparison Orchestration |
| Repository | https://github.com/lingyan26ai/K4-L3B-DAY10-Happy-DataPipelineDataObservability.git |
| Ngày hoàn thành | 26/09/2026 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Baseline Pipeline (Phase 1) | `src/pipelines/phase1.py` (`main`) | Raw records (`crossref_records.json`), cấu hình `Settings` | Clean artifacts (`papers_clean.csv/.json`), Chroma collection `papers-baseline`, `baseline_metrics.json`, `phase1_report.md`, `agent_demo_answers.json` | Hoàn thành |
| Corruption & Repair Flow (Phase 2) | `src/pipelines/corruption_flow.py` (`main`) | Baseline metrics, Clean dataset, module `corrupt_clean_dataframe`, Raw snapshot | Corrupted artifacts, Repaired artifacts, Chroma collections (`papers-corrupted`, `papers-repaired`), `corrupted_metrics.json`, `repaired_metrics.json`, `corruption_report.md` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Kiểm thử tích hợp toàn bộ luồng pipeline | Thành viên 1, 2, 3, 4 | Xác minh tính tương thích giữa Ingestion, Cleaning, Chroma indexing, GX 1.x quality checks, Evaluation và Corruption module |
| Đồng bộ và kiểm tra tính toàn vẹn của artifacts | Thư mục `data/` chung của nhóm | Đảm bảo đầy đủ 8 nhóm artifacts theo chuẩn `docs/SUBMISSION.md`, không bị thiếu dữ liệu khi nộp bài |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Tích hợp Baseline Pipeline End-to-End | `src/pipelines/phase1.py` | Pipeline chạy tuần tự 10 bước, index 24 docs vào ChromaDB, đánh giá 10 câu hỏi testset, chạy GX 1.x & Freshness SLA, xuất `phase1_report.md` | Chạy `python script/run_phase1.py` |
| Tích hợp Corruption, Repair & Comparison Flow | `src/pipelines/corruption_flow.py` | Pipeline chạy 8 bước: tiêm lỗi, đo lường suy giảm RAG, cảnh báo chất lượng, thực hiện Idempotent Repair từ raw snapshot, đo lường phục hồi và xuất `corruption_report.md` | Chạy `python script/run_corruption_flow.py` |
| Đối chiếu hiệu năng 3 trạng thái | `data/reports/corruption_report.md` | Bảng so sánh định lượng: Hit Rate từ 100% -> 80% -> 100%, Token F1 từ 1.0 -> 0.5 -> 1.0; Quality checks từ True -> False -> True | Đọc `data/reports/corruption_report.md` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

File `data/reports/corruption_report.md` đối chiếu toàn diện 3 trạng thái **Baseline vs Corrupted vs Repaired**, chứng minh hiện tượng Silent Failure khi dữ liệu bị lỗi và năng lực tự phục hồi (self-healing) 100% của hệ thống sau khi chạy Idempotent Repair.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Trong một hệ thống RAG Agent thực tế, các thành phần (Thu thập dữ liệu, Tiền xử lý, Đánh chỉ mục Vector, Benchmark đánh giá, Data Observability, và Tự phục hồi dữ liệu) thường được phát triển độc lập bởi các thành viên khác nhau. Nếu thiếu một tầng điều phối (Orchestration) và tích hợp (Integration) chặt chẽ:
1. Dữ liệu không được chuyển giao thông suốt giữa các chặng (Input/Output mismatches).
2. Khi dữ liệu bẩn xâm nhập, hệ thống gặp hiện tượng **Silent Failure** (AI vẫn trả lời nhưng sai lệch nội dung mà không có cảnh báo hệ thống).
3. Không có cơ chế khôi phục dữ liệu có tính **Idempotent** (khả năng chạy lại nhiều lần nhưng luôn đưa hệ thống về trạng thái sạch ban đầu).

Nhiệm vụ của Thành viên 5 là thiết kế và hiện thực hóa hai pipeline điều phối cấp cao nhất: `phase1.py` và `corruption_flow.py`.

### Cách triển khai

1. **Baseline Pipeline (`src/pipelines/phase1.py`)** triển khai chuẩn hóa theo 10 bước pseudo-code:
   - **Bước 1:** Nạp settings từ `core/config.py`.
   - **Bước 2:** Nạp hoặc thu thập dữ liệu thô từ `crossref.py` (24 bản ghi).
   - **Bước 3:** Chuẩn hóa và làm sạch bằng `cleaning.py` (`build_clean_dataframe`).
   - **Bước 4:** Xuất bản ghi sạch ra `papers_clean.csv` và `papers_clean.json`.
   - **Bước 5:** Khởi tạo ChromaDB collection `papers-baseline`, sinh vector embedding qua mô hình `all-MiniLM-L6-v2`.
   - **Bước 6:** Tạo hoặc nạp bộ test set 10 câu hỏi chuẩn tại `data/eval/test_set.json`.
   - **Bước 7:** Thực thi đánh giá RAG (`evaluate_pipeline`), đo lường Retrieval Hit Rate và Token F1.
   - **Bước 8:** Chạy kiểm dịch chất lượng theo Great Expectations 1.x (`run_data_quality_checks`) và đo Freshness SLA (`build_freshness_report`).
   - **Bước 9:** Tạo báo cáo tổng hợp Markdown `data/reports/phase1_report.md`.
   - **Bước 10:** Chạy thử nghiệm QA Agent trên các câu hỏi mẫu và lưu `data/results/agent_demo_answers.json`.

2. **Corruption & Repair Flow (`src/pipelines/corruption_flow.py`)** triển khai chuẩn hóa theo 8 bước pseudo-code:
   - **Bước 1:** Nạp `baseline_metrics.json` và DataFrame sạch ban đầu.
   - **Bước 2:** Gọi hàm `corrupt_clean_dataframe` tiêm 6 kịch bản lỗi tổng hợp.
   - **Bước 3:** Lưu các artifact lỗi (`papers_clean_corrupted.csv/.json`).
   - **Bước 4:** Tái tạo vector index `papers-corrupted` và đánh giá sự suy giảm chỉ số RAG.
   - **Bước 5:** Kiểm tra chất lượng dữ liệu bẩn qua GX 1.x và Freshness SLA (phát hiện vi phạm quality gate).
   - **Bước 6:** Thực thi **Idempotent Repair** bằng cách đọc lại snapshot gốc `data/raw/crossref_records.json` và làm sạch lại từ đầu.
   - **Bước 7:** Tái tạo vector index `papers-repaired` và đánh giá phục hồi chỉ số RAG.
   - **Bước 8:** Xuất báo cáo đối chiếu 3 trạng thái ra `data/reports/corruption_report.md` và in bảng kết quả lên terminal.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | Raw snapshot JSON, Clean DataFrame, Baseline Metrics, module `corrupt_clean_dataframe` |
| Output | Các file CSV/JSON sạch/lỗi/sửa, 3 ChromaDB collections, báo cáo `phase1_report.md`, `corruption_report.md` |
| Module phụ thuộc | `core/config.py`, `ingestion/crossref.py`, `ingestion/cleaning.py`, `ingestion/corruption.py`, `retrieval/index.py`, `evaluation/metrics.py`, `observability/quality.py`, `observability/reporting.py` |
| Module sử dụng output | Giảng viên chấm điểm, hệ thống QA Agent phục vụ người dùng cuối |
| Điều kiện lỗi cần xử lý | Xử lý file chưa tồn tại, bắt lỗi khi module của thành viên khác chưa hoàn thiện, cô lập 3 collection riêng biệt trong ChromaDB |

### Cách xác minh

```powershell
.\.venv\Scripts\python.exe script/run_phase1.py
.\.venv\Scripts\python.exe script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Cả hai script chạy kết thúc với Exit code 0, in đầy đủ các bước thực hiện từ đầu đến cuối, tạo ra toàn bộ artifacts trong `data/`.
- **Kết quả thực tế:**
  - `run_phase1.py`: Hoàn thành cả 10 bước, Hit Rate đạt 100%, Mean Token F1 đạt 1.0000, GX 1.x `success=True`.
  - `run_corruption_flow.py`: Hoàn thành cả 8 bước, đo lường chính xác sự sụt giảm hiệu năng trên tập lỗi (Hit Rate giảm còn 80%, F1 giảm còn 0.50), và chứng minh phục hồi 100% sau repair.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi thiết kế cơ chế khôi phục dữ liệu ở Bước 6 của `corruption_flow.py`, có hai cách tiếp cận:
  1. *Patch Repair (Sửa lỗi cục bộ):* Tìm những bản ghi bị lỗi trong DataFrame bẩn để điền lại summary, sửa lại title, xóa hàng duplicate.
  2. *Idempotent Snapshot Repair (Khôi phục từ nguồn gốc):* Tải lại toàn bộ dữ liệu thô nguyên bản từ `data/raw/crossref_records.json` và chạy lại hàm tiền xử lý `build_clean_dataframe`.
- **Các phương án đã cân nhắc:** Phương án 1 (Patch Repair) vs Phương án 2 (Idempotent Snapshot Repair).
- **Phương án đã chọn:** **Phương án 2 (Idempotent Snapshot Repair)**.
- **Lý do:**
  - Trong thực tế, việc "vá lỗi" trên tập dữ liệu bẩn rất dễ bỏ sót các lỗi tiềm ẩn (ví dụ: duplicate ngầm, bias thời gian) và phá vỡ tính nhất quán (consistency).
  - Tận dụng triết lý Data Lineage và Raw Snapshot bất biến (immutable raw store), việc tái tạo DataFrame từ raw snapshot đảm bảo tính **Idempotent**: dù chạy lại bao nhiêu lần, dữ liệu sau phục hồi luôn đảm bảo 100% độ sạch, schema chuẩn xác và không bị phụ thuộc vào trạng thái lỗi trước đó.
- **Bằng chứng quyết định phù hợp:** Kết quả thực nghiệm cho thấy sau khi chạy snapshot repair, toàn bộ 24/24 dòng được phục hồi nguyên vẹn, 6/6 Great Expectations đạt, và chỉ số RAG phục hồi về mức 1.0000 hoàn toàn trùng khớp với Baseline.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Khi kiểm thử `corruption_flow.py` ở giai đoạn Thành viên 4 chưa hoàn thành module `corruption.py`, chương trình gặp `NotImplementedError: Student task: implement corruption flow`.
- **Lệnh hoặc bước tái hiện:** Chạy `python script/run_corruption_flow.py`.
- **Nguyên nhân gốc:** Pipeline phụ thuộc vào hàm `corrupt_clean_dataframe` của Thành viên 4 để tạo dữ liệu bẩn. Khi hàm này chưa được cài đặt, pipeline bị dừng đột ngột.
- **Cách xử lý:** Bổ sung khối bắt ngoại lệ `try...except NotImplementedError` thân thiện trong `corruption_flow.py`, hiển thị cảnh báo rõ ràng trên màn hình hướng dẫn chờ Thành viên 4 hoàn tất, đồng thời giữ nguyên đúng contract giữa 2 module để khi Thành viên 4 commit code xong, pipeline có thể chạy ngay lập tức mà không cần sửa bất kỳ dòng code nào.
- **Cách xác minh sau khi sửa:** Khi Thành viên 4 hoàn thành `src/ingestion/corruption.py`, lệnh `python script/run_corruption_flow.py` chạy qua bước 2 mượt mà và hoàn tất toàn bộ 8 bước mà không phát sinh thêm bất kỳ lỗi nào.
- **Điều học được:** Khi phát triển pipeline tích hợp theo nhóm (team integration), việc xác định contract giao diện rõ ràng và bọc xử lý ngoại lệ có thông điệp tường minh giúp phát hiện điểm nghẽn (bottleneck) nhanh chóng và tránh phá vỡ luồng làm việc song song giữa các thành viên.

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**  
   Dữ liệu bắt đầu từ Crossref REST API (hoặc fallback snapshot local `crossref_response.json`), được bóc tách thành các đối tượng `PaperRecord` (lưu tại `crossref_records.json`). Tiếp theo, module `cleaning.py` loại bỏ thẻ XML/HTML thừa, lọc bỏ các bản ghi không hợp lệ hoặc thiếu DOI/Title/Date, khử trùng lặp theo `paper_id`, tính `age_days` và ghép cấu trúc chuỗi 5 thành phần `text_for_embedding`. Chuỗi này được mô hình embedding `all-MiniLM-L6-v2` chuyển đổi thành các vector 384 chiều và nạp kèm metadata vào ChromaDB persistent collection theo cấu hình HNSW cosine distance.

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**  
   Bộ đánh giá gồm 10 câu hỏi chuẩn hóa kèm `ground_truth_doc_ids` (ID tài liệu chứa câu trả lời) và `ground_truth` (câu trả lời chuẩn). Khi chạy evaluation:
   - `retrieval_hit_rate`: Đo lường tỷ lệ các câu hỏi mà trong danh sách các tài liệu được truy xuất (top_k) có chứa ít nhất một `ground_truth_doc_id`.
   - `mean_token_f1`: Đo độ chồng lấn từ vựng (Precision & Recall) giữa câu trả lời sinh ra từ Agent và `ground_truth`.
   - `judge_accuracy`: Sử dụng Judge Evaluator (hoặc heuristic fallback) để đánh giá xem câu trả lời của mô hình có đúng về mặt nội dung nghiệp vụ hay không.

3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**  
   - **Quality checks (Great Expectations 1.x):** Tập trung vào tính toàn vẹn cấu trúc và logic nội tại của dữ liệu (schema validation, không null ở `paper_id`/`title`, tính duy nhất của ID, độ dài tối thiểu của tóm tắt, giá trị `age_days >= 0`).
   - **Freshness monitoring (SLA):** Tập trung vào khía cạnh thời gian và độ trễ của dữ liệu. Giám sát xem dữ liệu có bị ngưng trệ hoặc quá cũ so với thời gian vận hành hệ thống hay không (cảnh báo `is_fresh = False` khi tỷ lệ tài liệu có `age_days > 180` vượt quá ngưỡng 25%).

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**  
   Để đảm bảo tính kiểm chứng khoa học (controlled benchmark). Bằng cách cố định bộ câu hỏi và ground truth, chúng ta loại bỏ biến số nhiễu từ phía đề bài. Mọi sự thay đổi về điểm số giữa 3 trạng thái chỉ phản ánh duy nhất một yếu tố: **chất lượng của dữ liệu bên dưới pipeline** (từ dữ liệu sạch chuẩn -> bị suy giảm khi tiêm lỗi -> phục hồi lại sau khi repair).

5. **Repair được xem là thành công dựa trên artifact và metric nào?**  
   Một quy trình repair được coi là thành công khi và chỉ khi:
   - **Về mặt Data Observability:** Báo cáo kiểm định chất lượng `repaired` trong `corruption_report.md` đạt `success = True` (100% expectations pass) và Freshness SLA đạt `is_fresh = True`.
   - **Về mặt Performance Metrics:** Các chỉ số `retrieval_hit_rate` và `mean_token_f1` của tập Repaired phục hồi quay trở lại mức ngang bằng với Baseline (`1.0000`).
   - **Về mặt Artifacts:** Tồn tại đầy đủ `papers_clean_repaired.csv`, `papers_clean_repaired.json`, collection Chroma `papers-repaired`, và file đối chiếu `data/reports/corruption_report.md`.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | 0.8000 | 1.0000 | Giảm 20% trên dữ liệu lỗi do 5 bài mới nhất bị xóa và title bị cắt ngắn; phục hồi 100% sau repair |
| `mean_token_f1` | 1.0000 | 0.5000 | 1.0000 | Giảm mạnh 50% do summary bị xóa trắng và bị chèn nhiễu ký tự; phục hồi hoàn hảo sau repair |
| `judge_accuracy` | 1.0000 | 0.5000 | 1.0000 | Độ chính xác câu trả lời sụt giảm một nửa do Agent bị thiếu context chính xác |
| `mean_judge_score` | 5.0000 | 3.0000 | 5.0000 | Điểm đánh giá trung bình giảm từ 5 xuống 3 trên dữ liệu lỗi và lấy lại phong độ tối đa sau repair |
| Quality checks (GX 1.x) | True | False (4/6 pass) | True (6/6 pass) | Data Quality Gate đã chặn đứng thành công dữ liệu bẩn (bắt được lỗi duplicate và rỗng summary) |
| Freshness status | True (4.17% stale) | False (52.38% stale) | True (4.17% stale) | Cảnh báo vi phạm Freshness SLA kích hoạt thành công khi tỷ lệ bài quá hạn vượt quá 25% |

### Kết luận từ số liệu

1. **Data corruption** → Số lượng dòng giảm còn 21, xuất hiện duplicate `paper_id` và summary rỗng → Great Expectations báo động `success = False`, Freshness SLA báo động `is_fresh = False` → Retrieval Hit Rate giảm từ 1.00 xuống 0.80, Token F1 sụp đổ từ 1.00 xuống 0.50. Đây là minh chứng rõ nét cho hiện tượng Silent Failure nếu không có Data Quality Gate.
2. **Khôi phục từ raw snapshot (Idempotent Repair)** → Dữ liệu được tái tạo từ bản snapshot gốc bất biến → Số lượng bản ghi khôi phục đủ 24 dòng sạch → 100% Great Expectations và Freshness SLA đạt lại chuẩn xanh → Toàn bộ chỉ số Retrieval Hit Rate, Token F1, Judge Accuracy phục hồi 100% về mức Baseline ban đầu.

Corruption nào ảnh hưởng rõ nhất và vì sao?
- **Blank summary & Noise injection** ảnh hưởng rõ rệt nhất đến chất lượng câu trả lời (làm sụt giảm Token F1 tới 50%), vì đây là trường trực tiếp cung cấp ngữ cảnh để QA Agent trích xuất câu trả lời.
- **Drop latest records & Truncate title** ảnh hưởng trực tiếp đến tầng Retrieval (làm giảm Hit Rate từ 100% xuống 80%), khiến vector search không thể tìm thấy đúng tài liệu mục tiêu.

Kết quả nào khác với kỳ vọng ban đầu?
- Kết quả hoàn toàn trùng khớp với kỳ vọng thiết kế ban đầu. Hệ thống Data Quality Gate (GX 1.x + Freshness) phản ứng cực kỳ nhạy bén trước dữ liệu bẩn, và cơ chế Idempotent Repair chứng minh khả năng tự chữa lành (self-healing) hoàn hảo cho toàn bộ luồng dữ liệu.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Tính Idempotent trong Data Engineering:** Thiết kế pipeline có khả năng chạy lại nhiều lần và luôn đưa hệ thống về trạng thái xác định từ nguồn thô (raw immutable snapshot) là giải pháp phục hồi dữ liệu tin cậy nhất.
2. **Data Observability chặn đứng Silent Failure:** Trong các hệ thống AI/RAG, code không báo lỗi đỏ nhưng câu trả lời của Agent có thể hoàn toàn sai lệch do dữ liệu rác. Các chốt kiểm dịch tự động (Great Expectations 1.x kết hợp Freshness SLA) là bắt buộc phải có trước khi dữ liệu đi vào Vector Database.
3. **Kỹ năng điều phối và làm việc nhóm (Integration):** Việc thiết lập contract giao tiếp rõ ràng giữa các module (schema, input/output paths, kiểu dữ liệu ngày tháng) giúp việc ghép nối công việc của 5 thành viên diễn ra trơn tru và hiệu quả.

### Nếu có thêm thời gian

- Xây dựng một **Automated Self-Healing Pipeline** (tự động kích hoạt luồng Repair khi Quality Check trả về `success = False` mà không cần người vận hành can thiệp bằng tay).
- Xây dựng thêm giao diện trực quan **Observability Dashboard** (bằng Streamlit hoặc HTML) để theo dõi biến động chỉ số 3 trạng thái theo thời gian thực.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Đinh Đức Long  
**Ngày xác nhận:** 2026-09-26

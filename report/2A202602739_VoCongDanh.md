# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Võ Công Danh             |
| MSSV               | 2A202602739                     |
| Khóa/Lớp         | K4              |
| Tên nhóm         | Happy     |
| Vai trò chính    | Phụ trách testset.py                 |
| Repository         | https://github.com/lingyan26ai/K4-L3B-DAY10-Happy-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Tạo bộ câu hỏi đánh giá      | src/evaluation/testset.py — build_test_set()           | DataFrame sạch          | data/eval/test_set.json | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Không có | Không áp dụng | Không nhận ownership hoặc hỗ trợ ngoài phạm vi chính |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Sinh 10 câu thuộc 4 loại | src/evaluation/testset.py | data/eval/test_set.json | Lệnh chạy ở mục 4 |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

data/eval/test_set.json có 10 câu: 3 summary, 3 authors, 2 date, 2 categories.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Tạo bộ câu hỏi có đáp án tham chiếu và ID bài nguồn để đánh giá retrieval và câu trả lời.

### Cách triển khai

Kiểm tra cột và dữ liệu cần thiết, loại ID trùng, chọn bài cố định theo paper_id. Tạo 10 câu thuộc 4 loại, lấy đáp án từ dữ liệu sạch và lưu JSON.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | DataFrame sạch có paper_id, title, summary, authors_joined, published, categories_joined và đường dẫn output.           |
| Output                         | Danh sách câu hỏi có id, question_type, question, ground_truth, ground_truth_doc_ids; file data/eval/test_set.json. |
| Module phụ thuộc             | ingestion/cleaning.py, core/utils.py                    |
| Module sử dụng output        | evaluation/metrics.py                    |
| Điều kiện lỗi cần xử lý | Thiếu cột hoặc không đủ bài có đáp án hợp lệ thì báo ValueError.                   |

### Cách xác minh

```bash
python -c "from core.config import load_settings; from evaluation.testset import build_test_set; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); ts=build_test_set(df, s.paths.eval_testset); print(f'Tín hiệu hoàn thành: Sinh được {len(ts)} câu hỏi test')"
```

- **Kết quả mong đợi:** Sinh 10 câu, đủ 4 loại.
- **Kết quả thực tế:** Console in: Tín hiệu hoàn thành: Sinh được 10 câu hỏi test.
- **Artifact/log:** data/eval/test_set.json

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Chọn bài để tạo bộ câu hỏi dùng chung khi đánh giá.
- **Các phương án đã cân nhắc:** Chọn ngẫu nhiên hoặc chọn cố định theo paper_id.
- **Phương án đã chọn:** Chọn cố định theo paper_id.
- **Lý do:** Giúp tái tạo cùng bộ câu hỏi để so sánh các trạng thái dữ liệu.
- **Bằng chứng quyết định phù hợp:** data/eval/test_set.json có đủ 10 câu thuộc 4 loại.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** KeyboardInterrupt khi import ChromaDB/OpenTelemetry.
- **Lệnh hoặc bước tái hiện:** Chạy lệnh tạo bộ câu hỏi ở mục 4.
- **Nguyên nhân gốc:** Tiến trình bị ngắt ở bước import thư viện, chưa chạy tới hàm tạo câu hỏi.
- **Cách xử lý:** Kiểm tra import chromadb riêng rồi chạy lại lệnh tạo câu hỏi.
- **Cách xác minh sau khi sửa:** Chạy lại lệnh ở mục 4; sinh được 10 câu hỏi.
- **Điều học được:** Phân biệt việc import bị ngắt với lỗi trong hàm tạo câu hỏi.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**

1. Dữ liệu được lấy từ Crossref hoặc snapshot và lưu thành raw records. Cleaning chuẩn hóa dữ liệu, tạo `text_for_embedding`; MiniLM chuyển văn bản thành vector rồi lưu vào ChromaDB cùng metadata của bài báo.

2. Evaluation set chứa câu hỏi, đáp án tham chiếu và ID bài đúng. Hit Rate kiểm tra kết quả truy xuất có chứa bài đúng không; Token F1 so sánh câu trả lời với đáp án tham chiếu.

3. Quality checks kiểm tra dữ liệu có thiếu giá trị, trùng ID, sai số dòng hoặc độ dài văn bản không đạt yêu cầu. Freshness kiểm tra độ cũ: bài trên 180 ngày được tính là stale; tỷ lệ stale vượt 25% thì không đạt SLA.

4. Dùng cùng test set giúp so sánh trên cùng câu hỏi và đáp án. Nếu đổi bộ câu hỏi giữa các lần chạy, không xác định được metric thay đổi do dữ liệu hay do bộ câu hỏi.

5. Repair cần có dữ liệu phục hồi từ raw, kết quả quality/freshness, index được xây dựng lại và `repaired_metrics.json`. So sánh với baseline và corrupted trên cùng test set để xác định mức phục hồi; lệnh chạy xong chưa đủ chứng minh repair thành công.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` | 1.00 | 0.80 | 1.00 | Corruption giảm 0.20; repair khôi phục hoàn toàn |
| `mean_token_f1`      | 1.00 | 0.50 | 1.00 | Corruption giảm 0.50; repair khôi phục hoàn toàn |
| `judge_accuracy`     | 1.00 | 0.50 | 1.00 | Corruption giảm 0.50; repair khôi phục hoàn toàn |
| `mean_judge_score`   | 5.00 | 3.00 | 5.00 | Giảm 2 điểm khi corrupted; trở lại baseline sau repair |
| Quality checks         | Pass | Fail | Pass | Dữ liệu corrupted không đạt; dữ liệu repaired đạt |
| Freshness status       | Fresh | Stale | Fresh | Tỷ lệ stale trở lại mức baseline sau repair |

### Kết luận từ số liệu

1. Corruption làm giảm chất lượng đánh giá: `retrieval_hit_rate` giảm từ 1.00 xuống 0.80, `mean_token_f1` và `judge_accuracy` cùng giảm từ 1.00 xuống 0.50, còn `mean_judge_score` giảm từ 5.00 xuống 3.00.
2. Repair lấy lại dữ liệu từ raw giúp quality checks và freshness đạt lại, đồng thời các metric phục hồi về đúng mức baseline.

Corruption nào ảnh hưởng rõ nhất và vì sao?

Metrics hiện là kết quả tổng hợp của sáu scenario nên chưa đủ để xếp hạng tác động retrieval/F1 của từng lỗi riêng lẻ. Ảnh hưởng rõ nhất trên quality/freshness là `stale_date`: stale ratio tăng lên 11/21 = 52.38%, vượt ngưỡng SLA 25% và làm freshness fail.

Kết quả nào khác với kỳ vọng ban đầu?

Bộ câu hỏi gồm 10 mẫu được dùng cố định cho cả ba lần chạy. Kết quả corrupted giảm như dự kiến; sau repair, toàn bộ metric trở lại bằng baseline và quality/freshness chuyển từ Fail/Stale về Pass/Fresh.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Bộ câu hỏi cần lấy đáp án và ID bài từ dữ liệu sạch để có thể đối chiếu.
2. Thiếu metadata như categories sẽ ảnh hưởng đến việc tạo câu hỏi; cần kiểm tra đầu vào trước.
3. Cần dùng cùng test set để đo ảnh hưởng của corruption và repair lên RAG.

### Nếu có thêm thời gian

Mở rộng câu hỏi sang nhiều bài hơn để tăng độ phủ; kiểm tra số bài khác nhau được hỏi và đánh giá lại trên cùng cấu hình.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Võ Công Danh
**Ngày xác nhận:** 2026-09-26

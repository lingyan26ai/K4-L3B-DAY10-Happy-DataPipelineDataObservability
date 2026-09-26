# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** `Happy`
- **Mã Nhóm / Lớp:** `K4-L3B-DAY10`
- **Tên Repository Nộp Bài:** `K4-L3B-DAY10-Happy-DataPipelineDataObservability`

---

## 1. Danh sách thành viên

| STT | Họ và tên | MSSV | Vai trò & Phân công công việc | Báo cáo cá nhân |
|---:|---|---|---|---|
| 1 | Bùi Việt Anh | 2A202602611 | Data Foundation & Cleaning (`crossref.py`, `cleaning.py`, raw/clean artifacts) | [`report/2A202602611_BuiVietAnh.md`](../report/2A202602611_BuiVietAnh.md) |
| 2 | Võ Công Danh | 2A202602739 | Evaluation Benchmark (`testset.py`, `data/eval/test_set.json`) | [`report/2A202602739_VoCongDanh.md`](../report/2A202602739_VoCongDanh.md) |
| 3 | Hà Anh Tuấn | 2A202602376 | Data Observability & Reporting (`quality.py` GX 1.x, `reporting.py`) | [`report/2A202602376_HAANHTUAN.md`](../report/2A202602376_HAANHTUAN.md) |
| 4 | Nguyễn Quang Đạo | 2A202602394 | Data Corruption Suite & Impact Analysis (`corruption.py`, `test_corruption.py`) | [`report/2A202602394_NguyenQuangDao.md`](../report/2A202602394_NguyenQuangDao.md) |
| 5 | Đinh Đức Long | 2A202602633 | Pipeline Integrator & Orchestration (`phase1.py`, `corruption_flow.py`) | [`report/2A202602633_DinhDucLong.md`](../report/2A202602633_DinhDucLong.md) |

---

## 2. Phần tự khai báo cá nhân

### BuiVietAnh-2A202602611
- **Vai trò:** Phụ trách Ingestion, Làm sạch & Phục hồi dữ liệu (`src/ingestion/crossref.py`, `src/ingestion/cleaning.py`).
- **Công việc chi tiết đã hoàn thành:**
  - Xây dựng module thu thập Crossref API với cơ chế Retry & Fallback offline vào snapshot local `crossref_response.json`.
  - Chuẩn hóa schema, tính toán trường `age_days`, lọc trùng DOI và tạo cột `text_for_embedding` 5 phần.
- **Điều học được / Đóng góp chính:**
  - Kỹ thuật bảo toàn Data Lineage và Raw Snapshot trước khi biến đổi dữ liệu.

### VoCongDanh-2A202602739
- **Vai trò:** Phụ trách Evaluation Benchmark (`src/evaluation/testset.py`).
- **Công việc chi tiết đã hoàn thành:**
  - Xây dựng hàm `build_test_set()` tự động sinh 10 câu hỏi deterministic phủ đủ 4 nhóm nghiệp vụ (`summary`, `authors`, `date`, `categories`).
  - Đảm bảo tính ổn định và tính khoa học khi dùng cùng một test set cho cả 3 trạng thái Baseline, Corrupted và Repaired.
- **Điều học được / Đóng góp chính:**
  - Cách thiết kế tập dữ liệu đánh giá chuẩn (controlled benchmark) để cô lập nguyên nhân suy giảm chất lượng dữ liệu.

### HaAnhTuan-2A202602376
- **Vai trò:** Phụ trách Data Observability & Reporting (`src/observability/quality.py`, `src/observability/reporting.py`).
- **Công việc chi tiết đã hoàn thành:**
  - Cấu hình Great Expectations 1.x ephemeral suite với 6 expectations trọng yếu.
  - Thiết lập Freshness SLA monitoring giám sát tỷ lệ bài báo quá hạn (> 180 ngày).
  - Viết module sinh báo cáo Markdown `generate_phase1_report` và `generate_corruption_report`.
- **Điều học được / Đóng góp chính:**
  - Cách xây dựng Data Quality Gate chặn đứng Silent Failure trước khi dữ liệu đưa vào vector database.

### NguyenQuangDao-2A202602394
- **Vai trò:** Phụ trách Data Corruption Suite & Impact Analysis (`src/ingestion/corruption.py`, `tests/test_corruption.py`).
- **Công việc chi tiết đã hoàn thành:**
  - Hiện thực 6 kịch bản làm bẩn dữ liệu thực tế: Drop latest records, Blank summary, Noise injection, Truncate title, Stale date, Duplicate rows.
  - Viết log chi tiết `corruption_log.json` và xây dựng bộ unit test `tests/test_corruption.py` kiểm chứng các dạng lỗi.
- **Điều học được / Đóng góp chính:**
  - Hiểu rõ cơ chế tác động của từng loại lỗi dữ liệu bẩn lên hiệu năng truy xuất và câu trả lời của RAG Agent.

### DinhDucLong-2A202602633
- **Vai trò:** Phụ trách Pipeline Integration & Comparison Orchestration (`src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`).
- **Công việc chi tiết đã hoàn thành:**
  - Xây dựng và tích hợp end-to-end Baseline Pipeline theo chuẩn 10 bước pseudo-code trong `phase1.py`.
  - Kết nối luồng Corruption, Evaluation, Idempotent Repair từ raw snapshot và sinh báo cáo so sánh 3 trạng thái theo chuẩn 8 bước trong `corruption_flow.py`.
  - Kiểm tra tính nhất quán toàn diện của toàn bộ artifacts trong thư mục `data/`.
- **Điều học được / Đóng góp chính:**
  - Thiết kế Idempotent Data Pipeline và năng lực điều phối tích hợp hệ thống đa tầng.

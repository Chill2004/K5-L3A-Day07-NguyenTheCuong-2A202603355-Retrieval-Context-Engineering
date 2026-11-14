# Hướng dẫn chạy Day07

## Môi trường

PowerShell, Python 3.12.0; Docker Desktop chạy PostgreSQL Day06.
Các package trực tiếp được pin trong requirements.txt. Model và revision
được ghi trong báo cáo, source code và artifacts/reranker_config.json.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Điền .env trên máy: DATABASE_URL, DAY6_STRATEGY=A, GEMINI_API_KEY,
GEMINI_MODEL. Không in/chia sẻ key. Kiểm tra `git check-ignore .env`.

## Database Day06

Trong môi trường thực nghiệm có container day6_student_starter-postgres-1,
port 127.0.0.1:55433 -> 5432, database day6_lab. Dùng tài khoản local của
người chạy; mật khẩu thật không nằm trong hướng dẫn.

```powershell
docker start day6_student_starter-postgres-1
docker exec day6_student_starter-postgres-1 pg_isready -U day6 -d day6_lab
.\.venv\Scripts\python.exe -m src.check_day6
```

Nếu chưa có container: dùng compose và pipeline của Day06, không tạo
database rỗng rồi báo đã tái lập. Bảng cần các cột strategy, chunk_id,
document_id, source, page, text, metadata JSONB, embedding vector(384).
Day07 chỉ đọc strategy A; yêu cầu 192 chunks và đúng model embedding.

## Dữ liệu benchmark

Xem docs/DATA_ACCESS.md. Cần bản chunks.json, snapshot.json,
dev_questions.json (17 câu), test_questions.json (7 câu) và freeze gốc.
Không dùng fixtures ví dụ để báo chất lượng thực nghiệm.
Không chạy script chuẩn bị lại trên bộ đóng băng khi chưa sao lưu.

## Kiểm tra và phân tích local

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m src.check_reranker
.\.venv\Scripts\python.exe -m src.evaluate_retrieval
.\.venv\Scripts\python.exe -m src.evaluate_context_dev
.\.venv\Scripts\python.exe -m src.summarize_test
.\.venv\Scripts\python.exe -m src.prepare_test_review
```

Các lệnh không gọi Gemini; có thể tải model Hugging Face. Evaluator có
thể ghi đè output tổng hợp; giữ bản gốc khi tái lập. summarize_test và
prepare_test_review hiện tham chiếu tên file run gốc, cần các trace gốc
hoặc sửa đường dẫn cho lần tái lập mới và ghi rõ đó là lần chạy khác.

## Agent dev: có gửi dữ liệu tới Gemini khi dùng --allow-api

```powershell
.\.venv\Scripts\python.exe -m src.run_agent_dev --config baseline --max-questions 17
.\.venv\Scripts\python.exe -m src.run_agent_dev --config baseline --max-questions 17 --allow-api
.\.venv\Scripts\python.exe -m src.run_agent_dev --config top5 --max-questions 17 --allow-api
.\.venv\Scripts\python.exe -m src.run_agent_dev --config single_search --max-questions 17 --allow-api
```

Bỏ --allow-api để xem kế hoạch không gửi request. Có --skip-ids để bỏ
các câu đã hoàn thành khi tiếp tục run lỗi. Không chạy song song trên cùng
project. Có pacing 6 giây/request; lỗi 429/503 phải lưu và báo riêng.
Phí thực tế phụ thuộc quota, tier và giá tại lúc chạy; không mặc định bằng 0.

## Test sau khi chọn cấu hình

```powershell
.\.venv\Scripts\python.exe -m src.run_agent_test --config baseline --max-questions 7
.\.venv\Scripts\python.exe -m src.run_agent_test --config top5 --max-questions 7
```

Chỉ thêm --allow-api khi thực sự muốn chạy lần tái lập mới và chấp nhận
gửi câu hỏi/context. Test gốc đã chạy đủ; không chạy lại để tìm điểm cao.
Lựa chọn trước test: top5; không đổi thành baseline sau khi xem test.

## Nhãn và chi phí

Nhãn test nằm trong test_reviews_confirmed.json. Mỗi dòng chỉ giữ mã câu,
điểm trả lời, điểm context, đánh giá citation, abstention và lý do chấm.
Người học đã xác nhận 14 nhãn. Hồ sơ xác nhận và nguồn hỗ trợ ban đầu
nằm riêng tại artifacts/test_review_confirmation.json; không lặp trong từng nhãn.
Script kiểm tra hash nhãn và trace để tránh áp dụng xác nhận cũ cho kết quả mới.
Các tên *_ai.json và *_proposed.json được giữ làm alias cho script cũ. Token usage, pacing, lỗi dịch vụ và số request
nằm trong trace. Không có hóa đơn trong repo để xác nhận chi phí thực thu.

## Kết quả kiểm tra tài liệu

17 unittest local đã pass trong lần hoàn thiện ngày 14/11/2026. Corpus,
snapshot và hai bộ câu hỏi khớp hash gốc; protocol không khớp. Xem
artifacts/verification_report.json; không ghi đè freeze gốc.

## Advanced — kết quả đã lưu

Code: src/advanced; runner: src/run_advanced_test.py và src/continue_advanced_test.py.
Xem docs/ADVANCED_PLAN.md và artifacts/advanced/test_status.json.
Dev chọn đạt 17/18. Test thử đủ 30 câu, có ít nhất bốn thất bại gồm một timeout;
không đạt bonus. Không chạy lại test để thay kết quả. Index có thể tái tạo
bằng `python -m src.advanced.prepare --embed`; giữ benchmark và trace gốc.

# Trạng thái hoàn thiện Day07

- [x] Kết nối Day06: 192 chunks, vector 384 chiều.
- [x] Benchmark 24 câu: 17 dev / 7 test; có 4 câu thiếu evidence.
- [x] Dense, TF-IDF, hybrid; reranker và neighbor packing có kết quả riêng.
- [x] Agent Gemini thật, log function calls, context, answer, citation, token.
- [x] Ba cấu hình agent dev; chọn top5 trước test.
- [x] Baseline và top5 hoàn thành đủ 7 câu test, giữ nguyên kết quả.
- [x] Đã kiểm tra và xác nhận 14 nhãn test.
- [x] Báo cáo cá nhân và REPORT_TEMPLATE.md đã điền số liệu thực tế.
- [x] Experiment log, manifest, .env.example và hướng dẫn tái lập đã có.
- [x] Đồng bộ Nguyễn Thế Cường là người xác nhận nhãn test, summary và báo cáo.
- Xác nhận học viên áp dụng cho 14 nhãn test; không tuyên bố chấm mù hoặc audit độc lập. Dev vẫn là đối chiếu AI.
- [x] Người học đã xác nhận quyền chia sẻ PDF, benchmark và trace.
- [ ] Thiết lập kênh nhận dữ liệu/trace và quyền truy cập cho người chấm.
- [ ] Đối chiếu chi phí thực thu với usage/billing nếu cần khẳng định tiền.
- [ ] Xác nhận remote, commit nộp và quyền mở repo của người chấm.
- [ ] Push có chọn lọc, nộp link qua kênh của giảng viên.

Không sửa README. Không tự commit, push hoặc gửi dữ liệu cho người khác.
Các lỗi citation/giới hạn tìm kiếm được phân tích, không ghi đè test gốc.

- [x] Đã chạy lại 17 unittest local: tất cả pass.
- [ ] Giải trình benchmark_protocol.md khác hash gốc; giữ nguyên freeze gốc.

## Advanced

- [x] Đã chọn và tải báo cáo World Bank 240 trang có bảng, sơ đồ, biểu đồ.
- [x] Index riêng toàn bộ 240 trang; 1538 chunks, 384 chiều.
- [x] Truy vấn local và render ảnh trang gốc hoạt động; 17 test cơ bản pass.
- [ ] Kiểm tra vision agent với Gemini.
- [ ] Tạo và đóng băng dev 18 câu, test 30 câu đủ nhóm.
- [ ] Thử nghiệm dev, chốt cấu hình và chạy toàn bộ test.
- [ ] Đối chiếu từng câu test với bản gốc, báo tỷ lệ và kiểm tra ngưỡng 27/30.

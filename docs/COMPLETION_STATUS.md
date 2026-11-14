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

- [x] Đã chạy 21 unittest local: tất cả pass theo output ngày 14/11/2026.
- [ ] Giải trình benchmark_protocol.md khác hash gốc; giữ nguyên freeze gốc.

## Advanced

- [x] Nguồn World Bank 240 trang, 225 trang native text có nội dung; 1538 chunks, 384 chiều.
- [x] Vision agent Gemini đã chạy với ảnh trang gốc.
- [x] Đóng băng 18 dev và 30 test, gold theo trang/vùng.
- [x] Dev được chọn đạt 17/18; chốt cấu hình trước test.
- [x] Đã thử đủ 30 câu test qua hai trace, giữ timeout câu 11 là thất bại.
- [ ] Hoàn tất audit chi tiết 30 câu và tỷ lệ chính xác theo nhóm.
- [ ] Đạt ngưỡng 27/30: không đạt; ít nhất bốn câu thất bại, tối đa 26/30.

Xem artifacts/advanced/test_status.json. Không tuyên bố bonus.

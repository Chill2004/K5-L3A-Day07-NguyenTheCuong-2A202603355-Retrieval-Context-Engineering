# Advanced — kế hoạch và trạng thái

## Tài liệu

World Bank, World Development Report 2018: Learning to Realize Education's
Promise. Bản PDF từ documents1.worldbank.org có 240 trang vật lý; khác
bản in được mô tả 239 trang. Dùng số trang PDF làm khóa tham chiếu.
Nguồn, SHA-256 và giấy phép: artifacts/advanced/source_manifest.json.

Handbook Day06 được giữ cho phần cơ bản. Kiểm tra toàn bộ handbook cho
thấy có bảng và sơ đồ nhưng không có đủ biểu đồ dữ liệu để thiết kế nhóm
test Advanced. Trang 145–167 là trang ghi chú trống. Không gọi những trang
đó là nội dung hữu ích để đạt ngưỡng.

## Pipeline

- Index toàn bộ text/caption trên 240 trang, không chọn trang theo gold.
- Embedding E5 384 chiều, index SQLite bền vững riêng; không thay index Day06.
- Kết hợp dense với BM25 bằng RRF; trả các trang khác nhau.
- Giữ trang PDF gốc và tọa độ để vision agent đọc bảng, hình, biểu đồ.
- Text trích xuất không tự bảo đảm đúng bảng; dùng ảnh trang gốc kiểm tra.
- BBox cấp trang chưa phải crop chính xác; câu trả lời trực quan cần dẫn
  thêm số hiệu hình/bảng và đối chiếu vùng gốc.

## Benchmark cần hoàn thành trước thử nghiệm

- Dev ít nhất 15 câu có đáp án + 3 câu không có đáp án.
- Test 30 câu: 6 bảng, 5 ảnh/sơ đồ, 5 biểu đồ, 4 multi-hop, 4 text,
  6 không có evidence. Mỗi câu chỉ tính một nhóm chính.
- Tách dev/test trước chạy; không đưa gold hoặc vùng gold cho agent.
- Đóng băng cấu hình bằng dev, chạy toàn bộ test; lỗi cũng nằm mẫu số.
- Chỉ tuyên bố đạt bonus khi ít nhất 27/30 và đủ hồ sơ index/nguồn/audit.

## Trạng thái sau thực nghiệm

Đã chạy vision agent Gemini; đóng băng 18 dev / 30 test. Dev chọn đạt 17/18.
Test đã thử đủ 30 câu: một timeout, ít nhất ba lỗi nội dung/từ chối nhầm.
Tối đa 26/30; chưa hoàn tất audit toàn bộ, không tuyên bố đạt bonus.
Lượt continuation chỉ chạy câu chưa thử, không thay kết quả lỗi ban đầu.
Chi tiết và hash trace: artifacts/advanced/test_status.json.

## Lệnh tái lập

- Index: `python -m src.advanced.prepare --embed`.
- Dev: `python -m src.advanced.run_dev`.
- Kiểm tra test: `python -m src.run_advanced_test`.
- Tiếp tục câu chưa chạy: `python -m src.continue_advanced_test`.

Thêm --allow-api mới gửi request Gemini. Không chạy lại test để thay điểm.
Giữ nguyên benchmark, selection và trace gốc khi tái tạo. BBox cấp trang;
chưa phải bộ phân tích layout tự động chính xác từng vùng. Chi phí billing
chưa xác minh. Nguồn, cấu hình và giới hạn nằm trong source_manifest.json.

# Nguồn dữ liệu và cách xác minh

Day07 kế thừa dữ liệu Day06, không tự tạo giấy phép mới. Phạm vi chính xác
là 39 trang PDF 39–77, 40 source units, 192 chunks strategy A.
Metadata nguồn: `data/manifest.json`.

## Hồ sơ rà soát kế thừa từ Day06

# Kết quả kiểm tra điều khoản sử dụng

Ngày kiểm tra: 13/11/2026. Nguồn: [quy định website của trường](https://ou.edu.vn/wp-content/uploads/2024/09/HCMCOU-Quy-dinh-cua-websites-final.pdf).

Đã tìm thấy điều khoản sử dụng cá nhân, không kinh doanh (mục I, trang 1).
Mục IV.5.a/c, trang 3 đặt điều kiện đồng ý/cấp phép đối với việc xuất bản,
phân phối và sử dụng quyền sở hữu. Chưa thấy giấy phép mở trong handbook.

Điều khoản không đề cập cụ thể embedding. Việc áp dụng cho Lab cá nhân là
một cách diễn giải, chưa phải sự cho phép riêng cho xử lý AI hoặc đăng lại
PDF/trace. Văn bản được công bố còn để trống số/ngày, nên không khẳng định
đã xác minh đầy đủ hiệu lực và phạm vi. Truy cập công khai không tự tạo giấy phép mở.

Giữ nguyên kết quả thí nghiệm và chính sách chưa tự upload nội dung nguồn.
Manifest đã bổ sung `license_review` để lưu căn cứ vừa tìm thấy.


## Cách tái tạo và cấp quyền

1. Người chấm cần có quyền hợp lệ truy cập PDF nguồn và bộ benchmark.
2. Khởi chạy PostgreSQL Day06 với bảng ingestion_chunks, vector(384).
3. Dùng `python -m src.check_day6` để xác nhận 192 chunks strategy A.
4. Dùng `python -m src.export_day6` để xuất snapshot Day07 khi tái tạo
   trong môi trường riêng. Không ghi đè snapshot thực nghiệm gốc.
5. Benchmark người học đã tạo không thể khôi phục chính xác chỉ từ URL
   PDF. Phải cấp bộ dev/test đã đóng băng qua kênh được phép, kèm hash.
6. Trace nguyên gốc, nhãn do Codex (AI) thực hiện và benchmark hiện nằm local trong
   starter/data/day6 và starter/results/day7; chúng đang bị Git ignore.

Chưa thiết lập kênh cấp quyền cho người chấm. Vì vậy chưa tuyên bố bài
public có thể tái lập hoàn toàn chỉ bằng clone. Không dùng `git add -f`
để công khai dữ liệu chưa xác nhận quyền. Khi quyền và kênh truy cập được
xác nhận, ghi địa chỉ/kênh thực tế và phạm vi cho phép vào file này.

## Xác nhận bổ sung ngày 14/11/2026

Nguyễn Thế Cường xác nhận đã có quyền chia sẻ PDF, benchmark và trace.
Ghi nhận tại artifacts/data_sharing_confirmation.json. Đây là xác nhận
của người học, không phải một giấy phép mở mới do trợ lý cấp. Cần thiết lập
kênh thực tế để người chấm nhận bộ dữ liệu và trace.

# Day07 Benchmark Protocol

## Corpus

- Nguồn: Sổ tay sinh viên Đại học Mở TP. Hồ Chí Minh 2024.
- source_id: ou_handbook_2024.
- Phạm vi: trang PDF 39–77, tổng cộng 39 trang nội dung.
- Tái sử dụng 192 chunks của strategy A từ Day06.
- Snapshot: chunks.json và snapshot.json trong cùng thư mục.
- Giữ nguyên corpus và chunks khi so sánh các phương pháp retrieval.
- Phạm vi đánh giá không bao gồm toàn bộ 167 trang của PDF.

## Benchmark

Tổng cộng 24 câu:

| Split | Có đáp án | Không có đáp án | Tổng |
|---|---:|---:|---:|
| Dev | 15 | 2 | 17 |
| Test | 5 | 2 | 7 |

- Dev có đáp án kế thừa từ Day06.
- Evidence q06 được rà soát lại từ trang nguồn trước thử nghiệm Day07.
- Năm câu test có đáp án được tạo mới cho Day07.
- Không tái sử dụng năm câu test đã xem kết quả trong Day06.
- Evidence của câu có đáp án được đối chiếu với văn bản trang nguồn.
- Câu không có đáp án được đánh giá trong phạm vi corpus trang 39–77.
- Kiểm tra từ khóa chỉ hỗ trợ rà soát, không tự chứng minh sự vắng mặt.
- Rà soát nguồn có AI hỗ trợ; không tuyên bố là đánh giá độc lập của con người.

## Ngăn rò rỉ dữ liệu đánh giá

- Chỉ dùng dev để phát triển, phân tích lỗi và chọn cấu hình.
- Không chạy retrieval hoặc agent trên test trong quá trình tinh chỉnh.
- Chỉ chạy test sau khi chốt cấu hình baseline và cấu hình được chọn.
- Agent chỉ nhận câu hỏi và bộ lọc được cung cấp rõ trong câu hỏi.
- Không truyền expected_answer, gold, absence_reason hoặc answerable
  cho agent, mô hình hay công cụ retrieval.
- Không suy ra metadata filter từ gold evidence.
- Việc đọc nguồn để xây dựng test được thực hiện trước thử nghiệm;
  test không phải bộ đề mù do bên thứ ba xây dựng.

## So sánh retrieval

Các phương pháp dự kiến:

1. Dense vector search.
2. Lexical search.
3. Hybrid search bằng Reciprocal Rank Fusion.

- Dùng cùng corpus, chunks, benchmark và chính sách metadata filter.
- Ghi rõ cấu hình, model, phiên bản và tham số của từng phương pháp.
- Thay đổi top-k đơn thuần không được tính là phương pháp retrieval mới.
- Chỉ số retrieval được tính trên câu có đáp án.
- Đánh giá Hit@1 và Evidence Hit@3 với cùng định nghĩa giữa các cấu hình.
- Lưu top-3, chunk ID, trang, metadata và điểm retrieval.
- Nếu evidence bị chia qua chunks, ghi nhận giới hạn thay vì sửa gold
  để khớp kết quả retrieval.

## Agent và cải tiến

- Dùng mô hình sinh thật; embedding model không thay thế mô hình agent.
- Agent quyết định gọi công cụ tìm kiếm, trả lời hoặc từ chối.
- Ghi baseline và ít nhất hai cấu hình cải tiến có giả thuyết rõ ràng.
- Chọn cấu hình bằng kết quả dev trước khi chạy test.
- Lưu model, prompt, giới hạn tool calls, context budget và tham số sinh.
- Lưu tool calls, kết quả, context cuối, câu trả lời, citation và lỗi.

## Đánh giá cuối

- Chạy baseline và cấu hình được chọn trên cùng bộ test.
- Audit context của cả năm câu test có đáp án cho mỗi cấu hình.
- Chấm context và câu trả lời theo thang 0/1/2 của đề bài.
- Kiểm tra citation tồn tại trong context và hỗ trợ phát biểu được dẫn.
- Đánh giá từ chối đúng với câu không có đáp án và từ chối sai
  với câu có đáp án.
- Ghi lỗi công cụ, số lần gọi, thời gian, token và chi phí nếu có.
- Phân biệt nhãn AI hỗ trợ với nhãn do người học xác nhận.
- Không chỉnh cấu hình sau khi xem test rồi báo đó là kết quả test ban đầu.

## Chi phí và khả năng tái lập

- Embedding kế thừa Day06: intfloat/multilingual-e5-small, 384 chiều.
- Chốt lựa chọn mô hình sinh local hoặc API trước khi chạy agent.
- Nếu chạy local: ghi API cost bằng 0; vẫn ghi thời gian và phần cứng.
- Nếu dùng API: ghi model, lượng sử dụng và cách tính chi phí.
- Không lưu hoặc commit secret.
- Ghi hash benchmark và corpus snapshot trước thử nghiệm.

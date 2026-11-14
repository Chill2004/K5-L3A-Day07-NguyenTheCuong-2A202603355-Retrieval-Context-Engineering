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

## Bổ sung sau thực nghiệm — 14/11/2026

Đây là bản ghi bổ sung khi hoàn thiện báo cáo sau test, không phải khai
báo rằng các chi tiết dưới đây đều đã nằm trong bản đóng băng ban đầu.
Giữ nguyên benchmark_freeze.json gốc. Bản protocol quan sát ngay trước
lần bổ sung này được lưu tại artifacts/benchmark_protocol_observed_before_completion.md.

### Thiết lập đã thực hiện

- Dense: E5-small revision 614241f622f53c4eeff9890bdc4f31cfecc418b3,
  CPU, 384 chiều, L2, query prefix, PostgreSQL pgvector cosine search.
- Lexical: TF-IDF theo starter.baseline; fit IDF trên toàn corpus,
  lọc section trước khi lấy kết quả cuối.
- Hybrid: RRF k=60, 20 ứng viên mỗi phương pháp.
- Reranker CPU: cross-encoder/mmarco-mMiniLMv2-L12-H384-v1,
  revision 1427fd652930e4ba29e8149678df786c240d8825.
- Agent: Gemini Developer API, gemini-3.5-flash-lite, SDK 3.3.0.
- Mỗi quyết định là request mới chứa câu hỏi và trạng thái retrieval;
  function calling ANY, không tự động thực thi tool, max_output_tokens=1024.
- Không đặt seed hoặc temperature riêng; không tuyên bố sinh tất định.
- Baseline: top_k=3; max_searches=2; context budget=2500 ký tự.
- Top5: chỉ đổi top_k=5. Single search: chỉ đổi max_searches=1.
- Chọn top5 trước test; lưu tại artifacts/selection_dev.md.
- Có pacing 6 giây/request sau lỗi 429; các run trước/sau pacing giữ
  nguyên để báo kết quả, không coi thời gian tổng là chỉ riêng inference.

### Cách chấm đã dùng

- Các phần tử gold là bằng chứng thay thế; tìm được một phần tử đầy đủ
  là đạt, không phải schema bắt buộc tất cả evidence của multi-hop.
- Chuẩn hóa NFC, casefold và khoảng trắng trước kiểm tra evidence.
- Chỉ ghép spans liên tục/overlap trong cùng source_id, page, unit_id;
  loại overlap trùng, không nối qua khoảng trống chưa truy xuất.
- Retrieval dev dùng câu hỏi gốc. Chỉ số first-tool trên test dùng query
  model sinh, cutoff chung 1 và 3; báo riêng hai phạm vi này.
- Reciprocal rank là nghịch đảo prefix depth đầu tiên đủ evidence.
- Context Evidence Rate xét các chunk thực sự nằm trong context cuối.
- Answer/context grade test 0/1/2 ban đầu do Codex hỗ trợ; Nguyễn Thế Cường
  đã kiểm tra và xác nhận 14 nhãn ngày 14/11/2026.
- Final abstain trên câu có đáp án chấm answer 0, kể cả khi action model
  đề xuất câu đúng nhưng bị validator loại citation.
- Citation validity chấm hỗ trợ nội dung và sự có mặt trong context,
  không chỉ dựa vào ID. Mẫu số là citation ở đầu ra cuối.
- Tách model_abstain, search_limit, invalid_or_missing_citations.

### Kết quả và trạng thái

- Cả ba cấu hình agent dev đủ 17 câu; test baseline/top5 đủ 7 câu.
- Test first-tool Evidence Hit@3 và Context Evidence Rate đều 5/5.
- Test answer grade đã được Nguyễn Thế Cường xác nhận: baseline 2,0; top5 1,6.
- Top5/test_03 bị từ chối do citation gộp; giữ nguyên test gốc.
- Chi phí thực thu chưa đối chiếu billing; có token usage thực trong trace.
- Không thực hiện Advanced. Quyền chia sẻ còn chờ; audit test đã được người học xác nhận, giữ thông tin Codex hỗ trợ ban đầu.

### Sai khác hash

Trước khi bổ sung, protocol đã khác hash trong freeze gốc, chưa xác định
nguyên nhân. Corpus, snapshot và hai bộ câu hỏi vẫn khớp hash gốc.
Lần bổ sung hiện tại được ghi minh bạch sau thực nghiệm; không tạo lại
freeze để giả định đây là protocol trước test. Xem artifacts/verification_report.json.

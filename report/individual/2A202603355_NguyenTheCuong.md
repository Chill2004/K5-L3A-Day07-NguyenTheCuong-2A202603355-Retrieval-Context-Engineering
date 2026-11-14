# Báo cáo Day 7

Họ tên: Nguyễn Thế Cường  
MSSV: 2A202603355  
Lớp: K5-L3A  
Ngày thực nghiệm: 14/11/2026

## Dữ liệu và benchmark

- Tái sử dụng Sổ tay sinh viên Đại học Mở TP. Hồ Chí Minh 2024
  từ Day06; source_id: ou_handbook_2024.
- Nguồn:
  https://ou.edu.vn/wp-content/uploads/2024/09/So-Tay-SV-2024.pdf
- PDF có 167 trang vật lý; corpus thực nghiệm chỉ gồm trang 39–77,
  tổng cộng 39 trang nội dung.
- Dùng 192 chunks strategy A của Day06, kích thước tối đa 500 ký tự,
  overlap 50 ký tự.
- Người học đã xác nhận quyền chia sẻ PDF, benchmark và trace ngày
  14/11/2026; ghi nhận tại artifacts/data_sharing_confirmation.json.
  Xác nhận này không được diễn giải thành giấy phép mở của tài liệu.

Vector store và model:

- PostgreSQL cùng pgvector, lưu bền vững trong Docker volume Day06.
- Bảng ingestion_chunks, chỉ đọc strategy A trong Day07.
- Embedding local CPU: intfloat/multilingual-e5-small.
- Revision: 614241f622f53c4eeff9890bdc4f31cfecc418b3.
- Vector 384 chiều, chuẩn hóa L2, cosine distance.
- Prefix truy vấn: query: ; embedding tài liệu kế thừa từ Day06.
- Reranker local:
  cross-encoder/mmarco-mMiniLMv2-L12-H384-v1.
- Reranker revision: 1427fd652930e4ba29e8149678df786c240d8825.
- Agent: Gemini Developer API, gemini-3.5-flash-lite.
- SDK google-genai 3.3.0.

Benchmark gồm 24 câu:

| Split | Có đáp án | Không có đáp án | Tổng |
|---|---:|---:|---:|
| Dev | 15 | 2 | 17 |
| Test | 5 | 2 | 7 |

- Dev kế thừa 15 câu Day06 và bổ sung hai câu không có đáp án.
- Test được xây dựng mới cho Day07.
- Evidence có đáp án được kiểm tra với văn bản trang nguồn.
- Nhãn không có đáp án chỉ áp dụng trong corpus trang 39–77.
- Benchmark được ghi hash trước thử nghiệm trong benchmark_freeze.json.
- Agent không nhận gold, expected_answer, answerable hoặc absence_reason.
- Test do người học xây dựng với AI hỗ trợ, không phải đề mù độc lập.

## Retrieval và thử nghiệm

Cùng corpus, embedding và chính sách filter được dùng khi so sánh.
Filter section chỉ áp dụng khi phạm vi được nêu rõ trong câu hỏi.

Evidence được chuẩn hóa Unicode và khoảng trắng. Khi evidence bị chia
qua chunks, evaluator chỉ ghép các khoảng liên tục hoặc overlap thuộc
cùng nguồn, trang và source unit; không nối qua khoảng trống.

| Phương pháp dev | Hit@1 | Evidence Hit@3 | Median search |
|---|---:|---:|---:|
| Dense | 12/15 (80%) | 14/15 (93,33%) | 70,23 ms |
| TF-IDF | 13/15 (86,67%) | 14/15 (93,33%) | 2,23 ms |
| Hybrid RRF | 14/15 (93,33%) | 14/15 (93,33%) | 70,76 ms |
| Hybrid + rerank | 14/15 (93,33%) | 14/15 (93,33%) | 1299,40 ms |

Hybrid dùng candidate_k=20, rrf_k=60. Rerank không tăng các chỉ số
retrieval đang đo nhưng làm tăng độ trễ khoảng 18,4 lần trong lần chạy này.

Thử đóng gói thêm chunk liền kề, budget 2500 ký tự:

| Retrieval | Context packing | Context đủ evidence |
|---|---|---:|
| Hybrid | Theo thứ hạng | 14/15 |
| Hybrid | Thêm liền kề | 14/15 |
| Hybrid + rerank | Theo thứ hạng | 14/15 |
| Hybrid + rerank | Thêm liền kề | 14/15 |

Các cấu hình agent:

| Cấu hình | Top-k | Tìm kiếm tối đa | Budget |
|---|---:|---:|---:|
| Baseline | 3 | 2 | 2500 ký tự |
| Top5 | 5 | 2 | 2500 ký tự |
| Single search | 3 | 1 | 2500 ký tự |

Top5 được chọn trước test theo quan sát dev; lý do và giới hạn được
ghi tại artifacts/selection_dev.md. Không thay lựa chọn sau khi xem test.

Hai lỗi dev tiêu biểu:

1. q03: evidence bị chia qua ranh giới chunks; retrieval và context
   thiếu đoạn chứa ngưỡng điểm 5,0. Top5 trả lời được một phần nhưng
   vẫn thiếu điều kiện này.
2. Lỗi citation: model trả citation ID trong danh sách nhưng không
   chèn đúng dạng [chunk-id] vào câu trả lời. Validator chuyển thành
   abstain dù context có đủ bằng chứng.

Kết quả test về evidence:

| Cấu hình | First-tool Hit@1 | First-tool Evidence Hit@3 | Context Evidence Rate |
|---|---:|---:|---:|
| Baseline | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) |
| Top5 | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) |

Chỉ số test trên được tính từ truy vấn tìm kiếm đầu tiên do model sinh,
cùng cutoff 1 và 3. Chúng khác phạm vi bảng retrieval dev chạy trực tiếp
câu hỏi gốc; không dùng hai bảng để suy ra mức tăng dev sang test.

## Agent và đánh giá

Model chọn search, finish hoặc abstain bằng function calling.
Công cụ search thực thi hybrid retrieval local và metadata filter.

Context được loại trùng chunk ID, đóng gói theo thứ tự ứng viên và giới
hạn số ký tự. Chunk không vừa budget bị bỏ qua; chunk sau vẫn được xét.

Agent dừng khi:

- Trả lời có citation được validator chấp nhận.
- Model chọn abstain.
- Citation thiếu hoặc không đúng giao thức.
- Model yêu cầu tìm tiếp sau khi hết số lần tìm kiếm.

Validator kiểm tra citation ID và định dạng; không chứng minh rằng
nội dung nguồn hỗ trợ phát biểu. Việc đó được đánh giá riêng.

Nguyễn Thế Cường đã kiểm tra và xác nhận 14 nhãn test ngày 14/11/2026:

| Test | Tool use | Search calls | Grade 0/1/2 | Grade TB | Citation hỗ trợ | Từ chối đúng | Từ chối nhầm |
|---|---:|---:|---|---:|---:|---:|---:|
| Baseline | 7/7 | 10 | 0/0/5 | 2,0 | 5/5 | 2/2 | 0/5 |
| Top5 | 7/7 | 9 | 1/0/4 | 1,6 | 4/4 | 2/2 | 1/5 |

- Cả hai cấu hình có context grade đã được Nguyễn Thế Cường xác nhận bằng 2 cho cả năm câu có đáp án.
- Citation hỗ trợ tính trên citation còn ở đầu ra cuối, không bao gồm
  citation của câu trả lời đã bị validator loại.
- Baseline có citation trong 5/5 câu trả lời; Top5 có trong 4/4.
- Baseline hai câu thiếu evidence đều dừng do search_limit.
- Top5 một câu dừng do search_limit, một câu dùng model_abstain.

Lỗi test_03 của Top5:
Model tạo câu trả lời đúng và có đủ context nhưng dùng citation gộp
[id1, id2]. Validator yêu cầu [id1] [id2], nên đầu ra cuối là abstain
và answer grade bằng 0. Giữ nguyên trace và điểm test ban đầu.

| Chi phí sử dụng test | Baseline | Top5 |
|---|---:|---:|
| Model requests | 17 | 16 |
| Input tokens | 16501 | 16789 |
| Output tokens | 1166 | 1288 |
| Median mỗi câu, gồm pacing | 12,58 giây | 12,40 giây |

API được chạy trên project hiển thị Free tier. Không dùng model local
để sinh câu trả lời; chỉ embedding, reranker và retrieval chạy local.
Chi phí tiền thực thu cần đối chiếu trang usage/billing; token usage
trong trace không tự chứng minh hóa đơn bằng 0.

Có khoảng nghỉ tối thiểu 6 giây giữa các request trong tiến trình.
Thời gian cuối bao gồm chờ quota và không phải riêng độ trễ inference.

Các lỗi vận hành được giữ lại:

- Baseline dev: một lần 429.
- Top5 dev: một lần database timeout và một lần Gemini 503.
- Các câu đã hoàn thành được giữ; chỉ chạy tiếp câu thiếu.
- Test hai cấu hình hoàn thành không có provider error trong trace.

Đường dẫn minh chứng:

- artifacts/experiment_log.csv
- artifacts/selection_dev.md
- artifacts/reranker_config.json
- starter/data/day6/benchmark_protocol.md
- starter/data/day6/benchmark_freeze.json
- starter/results/day7/dev_retrieval_summary.json
- starter/results/day7/dev_context_summary.json
- starter/results/day7/agent_dev/dev_run_inventory.json
- starter/results/day7/test_automatic_summary.json
- starter/results/day7/test_review_summary_confirmed.json
- starter/results/day7/agent_test/*/test_reviews_confirmed.json
- Trace gốc trong starter/results/day7/agent_dev và agent_test.

Giới hạn:

- Corpus nhỏ, chỉ một handbook và năm câu test có đáp án.
- Bộ test nhỏ và do người học xây dựng; chưa có đánh giá mù độc lập.
- Một lần chạy mỗi cấu hình; chưa đo biến động của model sinh.
- Lỗi định dạng citation có thể gây từ chối nhầm.
- Chunk bị cắt có thể làm mất điều kiện quan trọng.
- Kết quả top5 không vượt baseline trên test lần này.
- Quyền chia sẻ do người học xác nhận; cần thiết lập kênh nhận minh chứng cho người chấm.

### Minh chứng dev và audit từng câu test

| Agent dev | Hoàn thành | Answered | Abstain | Request thử gọi, gồm lỗi | Lần lỗi |
|---|---:|---:|---:|---:|---:|
| baseline | 17/17 | 13 | 4 | 38 | 1 |
| top5 | 17/17 | 14 | 3 | 41 | 2 |
| single_search | 17/17 | 13 | 4 | 34 | 0 |

Không coi số `answered` là số câu đúng. Baseline dev có q03 và q05
từ chối; top5 q03 thiếu ngưỡng 5,0 và q12 bị loại citation; single_search
q03 và q12 từ chối. Hai câu không đáp án có thể dừng bởi giới hạn tìm kiếm,
khác với model chủ động chọn abstain.

Bảng dưới ghi điểm từng câu và lý do chấm.

| Cấu hình / Query ID | Search calls | Đầu ra cuối | Số citation cuối | Nhãn đã xác nhận / lý do |
|---|---:|---|---:|---|
| baseline / test_01 | 2 | answered | 1 | Answer 2; context 2; citation hỗ trợ nội dung |
| baseline / test_02 | 1 | answered | 1 | Answer 2; context 2; citation hỗ trợ nội dung |
| baseline / test_03 | 1 | answered | 1 | Answer 2; context 2; citation hỗ trợ nội dung |
| baseline / test_04 | 1 | answered | 1 | Answer 2; context 2; citation hỗ trợ nội dung |
| baseline / test_05 | 1 | answered | 1 | Answer 2; context 2; citation hỗ trợ nội dung |
| baseline / test_missing_01 | 2 | abstain | 0 | Từ chối đúng ở đầu ra; search_limit |
| baseline / test_missing_02 | 2 | abstain | 0 | Từ chối đúng ở đầu ra; search_limit |
| top5 / test_01 | 1 | answered | 1 | Answer 2; context 2; citation hỗ trợ nội dung |
| top5 / test_02 | 1 | answered | 1 | Answer 2; context 2; citation hỗ trợ nội dung |
| top5 / test_03 | 1 | abstain | 0 | Answer 0; context 2; citation gộp bị validator loại |
| top5 / test_04 | 1 | answered | 1 | Answer 2; context 2; citation hỗ trợ nội dung |
| top5 / test_05 | 1 | answered | 1 | Answer 2; context 2; citation hỗ trợ nội dung |
| top5 / test_missing_01 | 2 | abstain | 0 | Từ chối đúng ở đầu ra; search_limit |
| top5 / test_missing_02 | 2 | abstain | 0 | Từ chối đúng ở đầu ra; model_abstain |

Chi tiết câu hỏi, context và citation ID nằm trong trace gốc và
`test_reviews_confirmed.json`. Nhãn answer 0 của top5/test_03 áp dụng cho
đầu ra cuối là abstain; không chấm thay bằng câu model đề xuất đã bị loại.

### Lệnh tái lập và trạng thái nộp

Lệnh chạy đầy đủ, thiết lập database, schema và phân biệt thao tác local/API:
[docs/REPRODUCTION.md](../../docs/REPRODUCTION.md) (đường dẫn tính từ gốc repo).
Hồ sơ nguồn và truy cập: `data/manifest.json`, `docs/DATA_ACCESS.md`.
Checklist còn thiếu: `docs/COMPLETION_STATUS.md`.

Kiểm tra local: `python -m unittest discover -s tests -v`.
Retrieval dev: `python -m src.evaluate_retrieval`.
Context dev: `python -m src.evaluate_context_dev`.
Thống kê test đã lưu: `python -m src.summarize_test`.
Tổng hợp nhãn đã xác nhận: `python -m src.prepare_test_review`.

Các lệnh phân tích trên không gọi Gemini; lệnh retrieval có thể tải/check
cache model Hugging Face. Chỉ lệnh agent có `--allow-api` mới gửi nội dung
đến Gemini. Không chạy lại test chỉ để tìm kết quả tốt hơn.

Chi phí embedding/reranking local không có phí inference API; thời gian,
tài nguyên máy và tải model không được định giá thành tiền trong báo cáo.
Chi phí Gemini thực thu chưa đối chiếu hóa đơn; không thay bằng số 0 đã xác minh.

Codex hỗ trợ viết code, phân tích lỗi và tạo nhãn ban đầu; người học đã
kiểm tra nhãn test. Gemini là model agent trong thực nghiệm.


### Kiểm tra provenance sau thực nghiệm

Kiểm tra ngày 14/11/2026: chunks.json, snapshot.json, dev_questions.json
và test_questions.json khớp SHA-256 trong benchmark_freeze.json gốc.
Riêng benchmark_protocol.md không khớp hash đã lưu. Chưa có bản gốc để
xác định thay đổi thuộc nội dung hay định dạng; không tuyên bố protocol
giữ nguyên byte từ lúc đóng băng. Không sửa hash gốc để hợp thức hóa.
Chi tiết: artifacts/verification_report.json. Sai khác này không chứng minh
câu hỏi hoặc corpus đã thay đổi; bốn file dữ liệu kể trên vẫn khớp.

Các bảng chỉ số không chứa nội dung nguồn được sao chép sang artifacts/
để người chấm có thể đọc khi starter/results/ bị ignore. Corpus, benchmark và trace cơ bản được chọn để nộp cùng repo;
quyền mở repo và việc nộp link cần xác nhận sau khi push.

## Thử thách nâng cao (nếu thực hiện)

Đã triển khai trên World Development Report 2018, nguồn World Bank, giấy phép
CC BY 3.0 IGO với lưu ý thành phần bên thứ ba. Tài liệu có 240 trang PDF,
225 trang đạt tiêu chí native text có nội dung; index SQLite gồm 1538 chunks,
embedding E5 384 chiều chạy local. Không thay corpus hoặc PostgreSQL Day06.
Retrieval kết hợp dense và BM25 bằng RRF; agent Gemini đọc ảnh trang gốc.
BBox cấp trang cần được kết hợp với số hiệu hình/bảng khi kiểm chứng.

Benchmark đóng băng: dev 18 câu (15 có đáp án, 3 không có đáp án), test 30
câu (24 có đáp án, 6 không có đáp án). Test gồm 6 bảng, 5 sơ đồ, 5 biểu đồ,
4 multi-hop, 4 văn bản và 6 câu không có đáp án. Agent không nhận gold,
đáp án chuẩn hay crop evidence.

Cấu hình chọn trên dev: gemini-3.5-flash-lite, tối đa 2 lần gọi nguồn,
top-k=3, tối đa 6 ảnh mỗi request. Dev được chọn đạt 17/18; câu 08 nhầm
chú giải biểu đồ. Hướng dẫn đọc thứ tự sơ đồ và kiểm tra trang in được sửa
bằng dev trước khi chốt cấu hình. Mã nguồn, index và benchmark đã ghi hash.

Test đã thử đủ 30 câu. Lượt gốc dừng ở câu 11 do ReadTimeout; continuation
chỉ thực hiện câu 12–30. Giữ lỗi câu 11, không thay bằng lần thử lại.

| Câu chưa đạt đã xác định | Nguyên nhân |
|---|---|
| adv_test_11 | ReadTimeout, tính thất bại trong mẫu số 30 |
| adv_test_12 | Chênh lệch biểu đồ trả lời 31 điểm phần trăm, vượt sai số cho phép |
| adv_test_20 | Từ chối nhầm câu có bằng chứng về Tanzania |
| adv_test_23 | Không tìm được Box 11.2, từ chối nhầm câu có đáp án |

Chưa hoàn tất audit từng câu nên chưa công bố điểm chính xác hoặc tỷ lệ
cuối theo nhóm. Có ít nhất bốn câu chưa đạt, vì vậy tối đa 26/30, thấp hơn
ngưỡng 27/30. Không tuyên bố đạt bonus 15 điểm. Không chỉnh pipeline theo
test rồi ghi đè kết quả. Số liệu bài cơ bản được giữ nguyên.

Minh chứng: artifacts/advanced/source_manifest.json, benchmark_freeze.json,
selection_dev.json, test_status.json; trace trong starter/results/day7/advanced/test.
Chi phí API thực thu chưa đối chiếu billing, không mặc định bằng 0.

Hai lượt test: 68 request đã thử; trạng thái: {'answered': 24, 'error': 1, 'abstain': 5}.

### Cập nhật quyền chia sẻ

Người học xác nhận ngày 14/11/2026 đã có quyền chia sẻ PDF handbook,
benchmark và trace. Hồ sơ: artifacts/data_sharing_confirmation.json.
Những ghi chú rà soát giấy phép trước đó là lịch sử đánh giá, không phải
khẳng định ngược lại xác nhận bổ sung này.

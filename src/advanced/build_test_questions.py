"""Build the held-out Advanced benchmark from reviewed source pages."""

import json
from collections import Counter
from pathlib import Path

import pymupdf

from src.advanced.build_dev_questions import evidence


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "starter/data/advanced"
OUTPUT = BASE / "benchmark"

# page, kind, locator, normalized bounding box
REGIONS = {
    "table_o1": (
        34, "table", "Table O.1; ma trận alignment/coherence.",
        [0.07, 0.08, 0.94, 0.35],
    ),
    "table_o2": (
        34, "table", "Table O.2; hàng Teachers.",
        [0.07, 0.37, 0.94, 0.78],
    ),
    "table_11": (
        59, "table", "Table 1.1; Nonmonetary / Community-society.",
        [0.07, 0.07, 0.95, 0.32],
    ),
    "table_12": (
        62, "table", "Table 1.2; các hàng chương trình và cột kết quả.",
        [0.06, 0.70, 0.97, 0.96],
    ),
    "table_31": (
        100, "table", "Table 3.1; ngưỡng 80% bài kiểm tra kiến thức lớp 4.",
        [0.07, 0.73, 0.96, 0.92],
    ),
    "table_111": (
        222, "table", "Table 11.1; cột Roles that different actors can play.",
        [0.07, 0.73, 0.97, 0.96],
    ),
    "table_112": (
        223, "table", "Table 11.2; vai trò Government institutions.",
        [0.07, 0.70, 0.96, 0.95],
    ),
    "table_s61": (
        206, "table", "Table S6.1; Bangladesh 2010, Tertiary.",
        [0.07, 0.07, 0.95, 0.48],
    ),
    "figure_o11": (
        33, "diagram", "Figure O.11; các mũi tên đỏ hướng ra ngoài.",
        [0.43, 0.07, 0.97, 0.55],
    ),
    "figure_o15": (
        46, "diagram", "Figure O.15; vòng tác nhân ngoài và vòng trong.",
        [0.17, 0.07, 0.96, 0.56],
    ),
    "figure_o14": (
        41, "diagram", "Figure O.14; mạng mũi tên giữa các tác nhân.",
        [0.05, 0.05, 0.95, 0.62],
    ),
    "figure_53": (
        137, "diagram", "Figure 5.3; Pregnancy package và Birth package.",
        [0.07, 0.07, 0.96, 0.65],
    ),
    "figure_102": (
        215, "diagram", "Figure 10.2; hai mũi tên Teachers–Politicians.",
        [0.42, 0.06, 0.97, 0.30],
    ),
    "figure_o9": (
        31, "chart", "Figure O.9; Uganda 2013; hai loại vắng mặt.",
        [0.42, 0.42, 0.97, 0.88],
    ),
    "figure_o10": (
        32, "chart", "Figure O.10; India, United Kingdom và chú giải.",
        [0.16, 0.07, 0.58, 0.81],
    ),
    "figure_21": (
        79, "chart", "Figure 2.1; panel b, Secondary school, khoảng 2010.",
        [0.06, 0.07, 0.97, 0.49],
    ),
    "figure_71": (
        166, "chart", "Figure 7.1; phần Positive effect của hai cột.",
        [0.54, 0.43, 0.98, 0.87],
    ),
    "figure_s61": (
        204, "chart", "Figure S6.1; hai panel và cột năm 2012.",
        [0.17, 0.07, 0.97, 0.42],
    ),
    "figure_114": (
        232, "chart", "Figure 11.4; Low-income, nguồn kinh phí năm 2015.",
        [0.16, 0.07, 0.59, 0.56],
    ),
    "text_coherence": (
        33, "text", "Đoạn Successful systems combine both alignment and coherence.",
        [0.05, 0.58, 0.50, 0.79],
    ),
    "text_tanzania": (
        206, "text", "Cột phải; đoạn về school grants và teacher incentives ở Tanzania.",
        [0.48, 0.50, 0.98, 0.98],
    ),
    "text_growth": (
        62, "text", "Đầu mục Education promotes economic growth.",
        [0.18, 0.03, 0.59, 0.73],
    ),
    "text_girls": (
        79, "text", "Cột trái; đoạn 62 million girls between ages 6 and 15.",
        [0.06, 0.49, 0.50, 0.98],
    ),
    "text_campe": (
        222, "text", "Box 11.2; CAMPE tại Bangladesh.",
        [0.17, 0.08, 0.96, 0.57],
    ),
    "text_ethiopia": (
        232, "text", "Cột phải; ví dụ chương trình của Anh tại Ethiopia.",
        [0.48, 0.04, 0.97, 0.54],
    ),
}


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / "test_questions.json"
    if path.exists():
        raise FileExistsError("Test benchmark exists; do not overwrite it.")

    questions = []

    def add(group, question, answer, *regions, calculation=None):
        sources = [
            evidence(*REGIONS[key])
            for key in regions
        ]
        record = {
            "id": f"adv_test_{len(questions) + 1:02d}",
            "split": "test",
            "group": group,
            "answerable": True,
            "question": question,
            "expected_answer": answer,
            "evidence_mode": "all",
            "gold": sources,
        }
        if calculation:
            record["calculation"] = calculation
        questions.append(record)

    def missing(question, reason, scope):
        questions.append({
            "id": f"adv_test_{len(questions) + 1:02d}",
            "split": "test",
            "group": "unanswerable",
            "answerable": False,
            "question": question,
            "expected_behavior": "search_and_abstain",
            "absence_reason": reason,
            "absence_checks": {
                "scope": scope,
                "method": (
                    "Đối chiếu bảng/hình gốc và phạm vi dữ liệu được "
                    "báo cáo; kiểm tra nội dung liên quan trong tài liệu. "
                    "Không kết luận chỉ từ top-k."
                ),
            },
        })

    # Six table questions
    add(
        "table",
        "Theo Bảng O.1, hệ thống hướng tới việc học nhưng thiếu tính "
        "nhất quán giữa các thành phần thuộc ô nào? Khác gì với hệ "
        "thống vừa hướng tới việc học vừa nhất quán?",
        "Ô Incoherent strivers. Khi có cả alignment và coherence, "
        "hệ thống thuộc ô High performance.",
        "table_o1",
    )
    add(
        "table",
        "Theo Bảng O.2, lợi ích hướng tới việc học của giáo viên là gì, "
        "và bảng liệt kê những lợi ích cạnh tranh nào của họ?",
        "Lợi ích hướng tới việc học: học tập của học sinh và đạo đức "
        "nghề nghiệp. Lợi ích cạnh tranh: việc làm, an toàn việc làm, "
        "lương và dạy thêm tư.",
        "table_o2",
    )
    add(
        "table",
        "Theo Bảng 1.1, liệt kê các lợi ích phi tiền tệ của giáo dục "
        "ở cấp cộng đồng/xã hội.",
        "Dịch chuyển xã hội cao hơn; thể chế và cung cấp dịch vụ tốt "
        "hơn; tham gia công dân cao hơn; gắn kết xã hội lớn hơn; "
        "giảm ngoại tác tiêu cực.",
        "table_11",
    )
    add(
        "table",
        "Theo Bảng 1.2, trong Perry Preschool experiment, tỷ lệ tốt "
        "nghiệp trung học của nhóm can thiệp và đối chứng là bao nhiêu? "
        "Nhóm can thiệp cao hơn bao nhiêu điểm phần trăm?",
        "Can thiệp 65%, đối chứng 44%; cao hơn 21 điểm phần trăm.",
        "table_12",
        calculation="65 - 44 = 21 percentage points",
    )
    add(
        "table",
        "Theo Bảng 3.1, tại Uganda năm 2013, tỷ lệ giáo viên đạt ngưỡng "
        "kiến thức ngôn ngữ và toán lần lượt là bao nhiêu? Chênh lệch "
        "bao nhiêu điểm phần trăm?",
        "Ngôn ngữ 90%, toán 55%; ngôn ngữ cao hơn 35 điểm phần trăm. "
        "Ngưỡng là đạt ít nhất 80% bài kiểm tra kiến thức lớp 4.",
        "table_31",
        calculation="90 - 55 = 35 percentage points",
    )
    add(
        "table",
        "Theo Bảng 11.1, xã hội dân sự và khu vực tư nhân có vai trò "
        "gì trong việc sử dụng thông tin để cải thiện học tập?",
        "Tạo và phổ biến đánh giá học tập do người dân thực hiện; "
        "sử dụng đánh giá và nghiên cứu để hỗ trợ các can thiệp "
        "cải thiện học tập.",
        "table_111",
    )

    # Five image/diagram questions
    add(
        "image",
        "Trong Hình O.11, các mũi tên đỏ hướng vào hay ra khỏi tâm "
        "LEARNING? Chúng thể hiện điều gì?",
        "Hướng ra ngoài, thể hiện các yếu tố kỹ thuật và chính trị "
        "kéo các thành phần của hệ thống rời mục tiêu học tập.",
        "figure_o11",
    )
    add(
        "image",
        "Trong Hình O.15, tổ chức xã hội dân sự và cơ quan tư pháp "
        "nằm ở vòng nào so với giáo viên? Các mũi tên hướng tới "
        "mục tiêu trung tâm nào?",
        "Tổ chức xã hội dân sự và tư pháp ở vòng ngoài; giáo viên "
        "ở vòng trong. Các mũi tên hướng tới LEARNING.",
        "figure_o15",
    )
    add(
        "image",
        "Hình O.14 mô tả các tác nhân hành động độc lập hay ảnh hưởng "
        "lẫn nhau? Giải thích dựa trên mạng mũi tên trong hình.",
        "Các tác nhân ảnh hưởng lẫn nhau. Nhiều mũi tên nối chéo giữa "
        "các nhóm cho thấy lựa chọn của một nhóm tác động đến nhóm "
        "khác trong toàn hệ thống, không chỉ tác động riêng tới tâm.",
        "figure_o14",
    )
    add(
        "image",
        "Theo Hình 5.3, chăm sóc trước sinh, sắt và axit folic thuộc "
        "gói nào? Sinh có hỗ trợ, bú mẹ hoàn toàn và đăng ký khai "
        "sinh thuộc gói nào?",
        "Các mục đầu thuộc Pregnancy package, gói số 2. Các mục sau "
        "thuộc Birth package, gói số 3.",
        "figure_53",
    )
    add(
        "image",
        "Theo Hình 10.2, giáo viên hứa cung cấp điều gì cho chính "
        "trị gia, và chiều ngược lại cung cấp điều gì?",
        "Giáo viên hứa hỗ trợ bầu cử. Chính trị gia cung cấp việc làm "
        "hoặc việc điều chuyển đến nơi mong muốn.",
        "figure_102",
    )

    # Five chart questions
    add(
        "chart",
        "Theo Hình O.9, ở Uganda năm 2013, vắng khỏi lớp hay vắng "
        "khỏi trường cao hơn? Ước lượng hai tỷ lệ và chênh lệch.",
        "Vắng khỏi lớp cao hơn: khoảng 56% so với khoảng 30% vắng "
        "khỏi trường; chênh khoảng 26 điểm phần trăm. Chấp nhận "
        "sai số đọc biểu đồ khoảng 3 điểm phần trăm.",
        "figure_o9",
    )
    add(
        "chart",
        "Theo Hình O.10, phân bố điểm quản lý giáo dục của Vương quốc "
        "Anh hay Ấn Độ nằm cao hơn trên thang điểm? Giáo dục được "
        "biểu diễn bằng màu nào?",
        "Vương quốc Anh có phân bố dịch sang mức điểm cao hơn "
        "Ấn Độ. Giáo dục được biểu diễn bằng màu xanh lá.",
        "figure_o10",
    )
    add(
        "chart",
        "Theo panel Secondary school của Hình 2.1, khoảng năm 2010, "
        "Nam Á hay châu Phi cận Sahara có tỷ lệ nhập học thuần thấp "
        "hơn? Ước lượng tỷ lệ của nhóm thấp hơn.",
        "Châu Phi cận Sahara thấp hơn, khoảng 40%–45%.",
        "figure_21",
    )
    add(
        "chart",
        "Theo Hình 7.1, tỷ lệ can thiệp có tác động tích cực trong "
        "nhóm phần mềm hay phần cứng cao hơn? Ước lượng tỷ lệ của "
        "mỗi nhóm.",
        "Phần mềm cao hơn: khoảng 30%, so với khoảng 5% ở phần cứng. "
        "Đây là tỷ lệ can thiệp, không phải mức tăng điểm học sinh.",
        "figure_71",
    )
    add(
        "chart",
        "Theo Hình S6.1 năm 2012, nhóm thu nhập nào có chi giáo dục "
        "cao nhất tính theo phần trăm GNP, và nhóm nào cao nhất tính "
        "theo phần trăm tổng chi chính phủ? Có cùng nhóm không?",
        "Theo phần trăm GNP là nhóm thu nhập cao; theo phần trăm "
        "tổng chi chính phủ là nhóm thu nhập trung bình thấp. "
        "Không phải cùng một nhóm.",
        "figure_s61",
    )

    # Four multi-hop questions: all source pages are required.
    add(
        "multi_hop",
        "Kết hợp Bảng 3.1 và Bảng 1.2: tỷ lệ giáo viên Kenya năm "
        "2012 đạt ngưỡng toán là bao nhiêu, và chương trình "
        "I Have a Dream làm tăng tỷ lệ bỏ phiếu bao nhiêu điểm "
        "phần trăm so với đối chứng?",
        "Kenya: 82%. I Have a Dream: 42% so với 32%, tăng "
        "10 điểm phần trăm.",
        "table_31", "table_12",
        calculation="42 - 32 = 10 percentage points",
    )
    add(
        "multi_hop",
        "Kết hợp Hình 11.4 và Bảng S6.1: nguồn tài trợ giáo dục lớn "
        "nhất của nhóm nước thu nhập thấp năm 2015 là gì? Tại "
        "Bangladesh năm 2010, nhóm nghèo nhất và giàu nhất nhận "
        "bao nhiêu phần trăm chi giáo dục đại học công?",
        "Nguồn lớn nhất là chi công trong nước, khoảng 46%. "
        "Bangladesh: nhóm nghèo nhất 2%, nhóm giàu nhất 55%.",
        "figure_114", "table_s61",
    )
    add(
        "multi_hop",
        "Kết hợp Bảng 11.1 và Bảng 11.2: cơ quan chính phủ cần làm "
        "gì với kết quả đánh giá quốc gia, và cần tổ chức không gian "
        "đối thoại cải cách như thế nào?",
        "Tạo và phổ biến kết quả đánh giá quốc gia. Tổ chức không "
        "gian đối thoại cởi mở, bao trùm để xác định giải pháp khả "
        "thi về kỹ thuật và chính trị, đồng thời xây dựng năng lực "
        "thể chế phù hợp.",
        "table_111", "table_112",
    )
    add(
        "multi_hop",
        "Kết hợp định nghĩa coherence trong Overview và ví dụ "
        "Tanzania ở Spotlight 6: coherence nghĩa là gì, và tài trợ "
        "cho trường đã cải thiện học tập khi kết hợp với biện pháp nào?",
        "Coherence là các thành phần củng cố lẫn nhau để đạt mục "
        "tiêu của hệ thống. Ở Tanzania, tài trợ trường kết hợp với "
        "khuyến khích giáo viên đã cải thiện học tập; tài trợ đơn "
        "lẻ không hiệu quả.",
        "text_coherence", "text_tanzania",
    )

    # Four text questions
    add(
        "text",
        "Theo mục Education promotes economic growth, vốn con "
        "người thúc đẩy tăng trưởng qua hai cơ chế nào? Phân biệt "
        "cơ chế ngắn-trung hạn và dài hạn.",
        "Tăng khả năng hấp thụ, thích nghi công nghệ mới trong "
        "ngắn-trung hạn; thúc đẩy tiến bộ công nghệ và đổi mới "
        "để duy trì tăng trưởng dài hạn.",
        "text_growth",
    )
    add(
        "text",
        "Trong chương về mở rộng giáo dục, báo cáo nêu bao nhiêu "
        "triệu trẻ em gái vẫn ngoài nhà trường và thuộc nhóm tuổi nào?",
        "62 triệu trẻ em gái, từ 6 đến 15 tuổi.",
        "text_girls",
    )
    add(
        "text",
        "Theo Box 11.2, CAMPE tại Bangladesh bắt đầu thực hiện "
        "đánh giá từ năm nào và quy mô mạng lưới được mô tả ra sao?",
        "Từ năm 1999; mạng lưới hơn 1.000 tổ chức phi chính phủ, "
        "nhà nghiên cứu và nhà giáo dục.",
        "text_campe",
    )
    add(
        "text",
        "Theo ví dụ chương trình do Anh hỗ trợ tại Ethiopia, khoản "
        "chi trả gắn với kết quả cụ thể nào thay vì chỉ cấp đầu vào?",
        "Gắn với mức tăng ròng số học sinh vượt qua kỳ thi cuối "
        "bậc trung học cơ sở, với mức tiền đã thỏa thuận.",
        "text_ethiopia",
    )

    # Six questions whose requested detail is absent from the report.
    missing(
        "Bảng 3.1 cho biết tỷ lệ giáo viên đạt ngưỡng toán của từng "
        "trường cụ thể tại Kenya năm 2012 là bao nhiêu? Liệt kê "
        "tên trường và tỷ lệ.",
        "Bảng công bố số tổng hợp theo quốc gia, không có danh sách "
        "trường cùng tỷ lệ riêng.",
        "Table 3.1, chương 3 và phạm vi số liệu giáo viên của báo cáo.",
    )
    missing(
        "Theo Hình 7.1, máy tính trong các can thiệp phần cứng có "
        "tác động tiêu cực sử dụng chính xác CPU và dung lượng RAM nào?",
        "Hình báo cáo phân bố tác động theo loại can thiệp, không "
        "cung cấp cấu hình CPU/RAM cho các can thiệp đó.",
        "Figure 7.1 và phần ICT của chương 7.",
    )
    missing(
        "Với thang quản lý ở Hình O.10, hãy chép nguyên văn câu hỏi "
        "thứ năm và toàn bộ phương án trả lời của bảng hỏi gốc.",
        "Báo cáo nêu chỉ số và nguồn nghiên cứu nhưng không in đầy "
        "đủ bảng hỏi gốc với câu số năm và các phương án trả lời.",
        "Figure O.10, ghi chú phương pháp và phần quản lý trường học.",
    )
    missing(
        "Chỉ dùng báo cáo này, cung cấp toàn bộ giá trị số của từng "
        "đường trong Hình 2.1 cho từng năm 1820–2010, chính xác "
        "đến bốn chữ số thập phân.",
        "PDF có biểu đồ và đường dẫn dữ liệu bên ngoài, không có "
        "bảng toàn bộ chuỗi số với độ chính xác được yêu cầu.",
        "Figure 2.1 và các bảng dữ liệu trong PDF; không truy cập "
        "bộ dữ liệu ngoài tài liệu để thay đổi phạm vi.",
    )
    missing(
        "Theo Box 11.2, danh sách tên từng trẻ tham gia đánh giá "
        "CAMPE ở Bangladesh và điểm đọc riêng của từng trẻ là gì?",
        "Box mô tả hoạt động và kết quả tổng quát, không công bố "
        "dữ liệu định danh và điểm từng trẻ.",
        "Box 11.2 và phần citizen-led assessments trong báo cáo.",
    )
    missing(
        "Theo Bảng 1.2, tỷ lệ bỏ phiếu của Perry Preschool ở nhóm "
        "can thiệp và đối chứng khi tách riêng nam và nữ là bao nhiêu?",
        "Bảng chỉ tách theo chương trình và can thiệp/đối chứng, "
        "không có phân tổ giới tính cho kết quả bỏ phiếu này.",
        "Table 1.2 và các đoạn thảo luận Perry Preschool trong báo cáo.",
    )

    expected = {
        "table": 6,
        "image": 5,
        "chart": 5,
        "multi_hop": 4,
        "text": 4,
        "unanswerable": 6,
    }
    assert len(questions) == 30
    assert dict(Counter(q["group"] for q in questions)) == expected
    assert len({q["id"] for q in questions}) == 30

    crop_dir = OUTPUT / "test_evidence"
    crop_dir.mkdir(exist_ok=True)

    with pymupdf.open(
        BASE / "raw/world-development-report-2018.pdf"
    ) as document:
        for question in questions:
            golds = question.get("gold", [])
            if question["group"] == "multi_hop":
                assert len({g["page"] for g in golds}) >= 2

            for index, gold in enumerate(golds, 1):
                page = document[gold["page"] - 1]
                x0, y0, x1, y1 = gold["bbox_normalized"]
                assert 0 <= x0 < x1 <= 1
                assert 0 <= y0 < y1 <= 1
                clip = pymupdf.Rect(
                    x0 * page.rect.width,
                    y0 * page.rect.height,
                    x1 * page.rect.width,
                    y1 * page.rect.height,
                )
                image = crop_dir / f"{question['id']}_{index}.png"
                page.get_pixmap(dpi=160, clip=clip).save(image)
                gold["image"] = str(image.relative_to(ROOT))

    path.write_text(
        json.dumps(questions, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("Test questions:", len(questions))
    print("Groups:", dict(Counter(q["group"] for q in questions)))
    print("Answerable:", sum(q["answerable"] for q in questions))
    print("Saved:", path)
    print("Gemini requests: 0")


if __name__ == "__main__":
    main()
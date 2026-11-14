"""Build the Advanced dev benchmark from reviewed source pages."""

import json
from collections import Counter
from pathlib import Path

import pymupdf


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "starter/data/advanced"
OUTPUT = BASE / "benchmark"
SOURCE_ID = "wdr_2018_education"


def evidence(page, kind, locator, bbox):
    return {
        "source_id": SOURCE_ID,
        "page": page,
        "kind": kind,
        "locator": locator,
        "bbox_normalized": bbox,
    }


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / "dev_questions.json"

    if path.exists():
        raise FileExistsError(
            "Dev benchmark already exists. Review it instead of overwriting."
        )

    questions = []

    def add(group, question, answer, sources):
        questions.append({
            "id": f"adv_dev_{len(questions) + 1:02d}",
            "split": "dev",
            "group": group,
            "answerable": True,
            "question": question,
            "expected_answer": answer,
            "evidence_mode": "all",
            "gold": sources,
        })

    def missing(question, reason, checks):
        questions.append({
            "id": f"adv_dev_{len(questions) + 1:02d}",
            "split": "dev",
            "group": "unanswerable",
            "answerable": False,
            "question": question,
            "expected_behavior": "search_and_abstain",
            "absence_reason": reason,
            "absence_checks": checks,
        })

    # Tables
    add(
        "table",
        "Theo Bảng 5.1, học bổng dành cho nữ sinh được áp dụng ở "
        "quốc gia nào và tác động đến việc nhập học ra sao?",
        "Ở Campuchia; học bổng dành cho nữ sinh làm tăng mạnh tỷ lệ nhập học.",
        [evidence(
            133, "table",
            "Table 5.1; hàng Lower school costs; cột Approaches.",
            [0.07, 0.08, 0.94, 0.70],
        )],
    )

    add(
        "table",
        "Theo Bảng 6.1, tại Hoa Kỳ, chương trình gắn với một kỹ thuật "
        "sư phạm cụ thể hiệu quả gấp bao nhiêu lần đào tạo sư phạm chung?",
        "Hiệu quả gấp hai lần.",
        [evidence(
            152, "table",
            "Table 6.1; hàng đầu; cột Approaches; ví dụ United States.",
            [0.07, 0.03, 0.94, 0.62],
        )],
    )

    add(
        "table",
        "Theo Bảng 7.1, sách và tài liệu mới giúp tăng kết quả học tập "
        "ở Liberia khi được kết hợp với biện pháp nào?",
        "Khi kết hợp với đào tạo giáo viên.",
        [evidence(
            166, "table",
            "Table 7.1; hàng Additional inputs; cột Approaches.",
            [0.07, 0.02, 0.94, 0.43],
        )],
    )

    # Images and diagrams
    add(
        "image",
        "Theo Hình O.7, bốn yếu tố trực tiếp khiến việc học không "
        "diễn ra hiệu quả là gì?",
        "Người học chưa sẵn sàng; giáo viên thiếu kỹ năng và động lực; "
        "đầu vào trường học không hỗ trợ dạy và học; quản lý nhà trường "
        "không hỗ trợ dạy và học.",
        [evidence(
            30, "diagram",
            "Figure O.7; bốn phần bao quanh LEARNING.",
            [0.05, 0.06, 0.55, 0.54],
        )],
    )

    add(
        "image",
        "Trong Hình S3.1, vùng B nằm ở giao của những nhóm kỹ năng nào "
        "và chú giải B nêu hai loại kỹ năng gì?",
        "Giao của kỹ năng nhận thức, cảm xúc-xã hội và kỹ thuật. "
        "Chú giải B nêu giải quyết vấn đề và kỹ năng tổ chức.",
        [evidence(
            123, "diagram",
            "Figure S3.1; vùng B ở giao ba hình tròn và chú giải B.",
            [0.07, 0.07, 0.83, 0.74],
        )],
    )

    add(
        "image",
        "Theo Hình 11.2, nêu năm bước theo số thứ tự 1–5 và cho biết "
        "quá trình cải cách là tuyến tính hay có lặp lại?",
        "Xác định và chẩn đoán vấn đề; thiết kế phương án; triển khai; "
        "đánh giá; thích ứng. Quá trình có lặp lại, chẩn đoán lại và "
        "thiết kế lại phương án.",
        [evidence(
            227, "diagram",
            "Figure 11.2; các nút 1–5 và mũi tên Repeat.",
            [0.07, 0.54, 0.94, 0.95],
        )],
    )

    # Charts
    add(
        "chart",
        "Ở nhóm World trong Hình 1.1, mức tăng lương gắn với một năm "
        "đi học thêm của nữ hay nam cao hơn, và chênh khoảng bao nhiêu "
        "điểm phần trăm?",
        "Nữ cao hơn nam khoảng 2 điểm phần trăm, xấp xỉ 11% so với 9%. "
        "Chấp nhận số đọc gần đúng từ biểu đồ.",
        [evidence(
            59, "chart",
            "Figure 1.1; cặp cột World; trục Percent và chú giải Female/Male.",
            [0.07, 0.58, 0.94, 0.99],
        )],
    )

    add(
        "chart",
        "Trong Hình 5.4, quốc gia nào có tỷ lệ nhập học gộp cao nhất "
        "khoảng một năm sau mốc xóa học phí, và giá trị xấp xỉ bao nhiêu?",
        "Malawi, khoảng 150%–155%. Đây là tỷ lệ nhập học gộp, "
        "có thể vượt 100%.",
        [evidence(
            138, "chart",
            "Figure 5.4; đường Malawi tại khoảng x=1; trục Gross enrollment (%).",
            [0.07, 0.34, 0.56, 0.95],
        )],
    )

    add(
        "chart",
        "Theo Hình 6.1, ở lớp 5, nhóm phân vị thứ 10 có đạt chuẩn "
        "lớp 1 không? So sánh giá trị gần đúng của nhóm này với "
        "đường chuẩn lớp 1.",
        "Không. Nhóm phân vị thứ 10 chỉ khoảng 8%–10%, "
        "thấp hơn chuẩn lớp 1 là 50%.",
        [evidence(
            154, "chart",
            "Figure 6.1; đường 10th percentile tại Grade 5 "
            "và đường Grade 1 standard.",
            [0.03, 0.02, 0.62, 0.45],
        )],
    )

    # Multi-hop: every listed source is required.
    add(
        "multi_hop",
        "Kết hợp Bảng 5.1 và Bảng 6.1: Jamaica đã hỗ trợ trẻ chậm "
        "phát triển bằng cách nào, còn Ấn Độ và Kenya đã xử lý "
        "khác biệt trình độ học sinh bằng cách nào?",
        "Jamaica hướng dẫn người chăm sóc kích thích tâm lý-xã hội "
        "cho trẻ. Ấn Độ và Kenya tổ chức lại lớp theo năng lực học sinh.",
        [
            evidence(
                133, "table",
                "Table 5.1; hàng đầu; ví dụ Jamaica.",
                [0.07, 0.08, 0.94, 0.70],
            ),
            evidence(
                152, "table",
                "Table 6.1; hàng Pitch teaching to the level of the student; "
                "ví dụ India and Kenya.",
                [0.07, 0.03, 0.94, 0.62],
            ),
        ],
    )

    add(
        "multi_hop",
        "Kết hợp Hình S3.1 và Bảng 7.1: kỹ năng số thuộc nhóm kỹ năng "
        "nào, và việc đầu tư công nghệ giáo dục có thể thất bại khi "
        "thiếu những điều kiện triển khai nào?",
        "Kỹ năng số thuộc nhóm kỹ năng kỹ thuật. Đầu tư có thể thất bại "
        "khi thiếu năng lực bảo trì hoặc hạ tầng cần thiết để công nghệ "
        "hoạt động hiệu quả.",
        [
            evidence(
                123, "diagram",
                "Figure S3.1; vòng Technical skills, mục Digital.",
                [0.07, 0.07, 0.83, 0.74],
            ),
            evidence(
                166, "table",
                "Table 7.1; hàng Technologies must be implementable; "
                "cột Where this fails.",
                [0.07, 0.02, 0.94, 0.43],
            ),
        ],
    )

    add(
        "multi_hop",
        "Kết hợp Bảng 7.1 và Hình 11.2: đầu vào bổ sung nên có quan hệ "
        "thế nào với giáo viên, và sau bước triển khai cần thực hiện "
        "hai bước nào để điều chỉnh phương án?",
        "Đầu vào nên bổ trợ, không thay thế giáo viên. "
        "Sau triển khai là đánh giá rồi thích ứng phương án.",
        [
            evidence(
                166, "table",
                "Table 7.1; nguyên tắc Additional inputs.",
                [0.07, 0.02, 0.94, 0.43],
            ),
            evidence(
                227, "diagram",
                "Figure 11.2; chuỗi 3 Implement → 4 Evaluate → 5 Adapt.",
                [0.07, 0.54, 0.94, 0.95],
            ),
        ],
    )

    # Text
    add(
        "text",
        "Trong phần văn bản về phát triển chuyên môn giáo viên "
        "ở trang in 132, ba đặc điểm của đào tạo hiệu quả là gì?",
        "Tính thực hành, tính cụ thể và tính liên tục "
        "(practicality, specificity, continuity).",
        [evidence(
            152, "text",
            "Văn bản dưới Table 6.1, đoạn Is there hope for in-service training.",
            [0.07, 0.60, 0.94, 0.98],
        )],
    )

    add(
        "text",
        "Theo đoạn văn về Burkina Faso ở trang in 118, hỗ trợ tiền mặt "
        "có điều kiện nhập học đem lại lợi ích lớn hơn hỗ trợ không "
        "điều kiện cho những nhóm trẻ nào?",
        "Trẻ em gái và trẻ có mức học tập ban đầu thấp hơn.",
        [evidence(
            138, "text",
            "Cột phải, đoạn bắt đầu In Burkina Faso, beginning in 2008.",
            [0.55, 0.34, 0.94, 0.96],
        )],
    )

    add(
        "text",
        "Theo mục Encouraging innovation and agility, cách tiếp cận "
        "linh hoạt có chỉ là thử các can thiệp trong dự án thí điểm "
        "không? Báo cáo yêu cầu thử nghiệm trong điều kiện nào?",
        "Không chỉ là thử trong dự án thí điểm. Cần thử ở quy mô lớn "
        "trong bối cảnh chính trị, kinh tế thực tế và sử dụng năng lực "
        "hiện có của cơ quan triển khai.",
        [evidence(
            227, "text",
            "Cột phải, đoạn Learning reforms need a more agile approach.",
            [0.44, 0.02, 0.98, 0.56],
        )],
    )

    # Absence is assessed within this report, not the entire internet.
    missing(
        "Theo báo cáo này, điểm PISA 2025 thực tế của học sinh "
        "Việt Nam ở từng môn là bao nhiêu?",
        "Báo cáo xuất bản năm 2018 không cung cấp kết quả quan sát "
        "PISA 2025 của Việt Nam.",
        {
            "scope": "Toàn bộ báo cáo và các hình/bảng PISA.",
            "searched_terms": ["PISA 2025", "Viet Nam", "Vietnam"],
        },
    )

    missing(
        "Chương trình đào tạo gắn với kỹ thuật sư phạm cụ thể tại "
        "Hoa Kỳ trong Bảng 6.1 có chi phí chính xác bao nhiêu USD "
        "cho mỗi giáo viên?",
        "Bảng 6.1 nêu hiệu quả tương đối nhưng không cung cấp chi phí "
        "USD/giáo viên của chương trình được nói tới.",
        {
            "scope": "Bảng 6.1, văn bản chương 6 và tìm kiếm toàn báo cáo.",
            "searched_terms": [
                "cost per teacher",
                "dollars per teacher",
                "specific pedagogical technique",
            ],
        },
    )

    missing(
        "Khóa bồi dưỡng tiếp theo trong năm 2026 của chương trình "
        "giáo viên cộng đồng ở Ấn Độ trong Bảng 6.1 diễn ra ngày nào, "
        "giờ nào và tại địa điểm nào?",
        "Báo cáo mô tả kết quả can thiệp trước đây, không có lịch khóa "
        "bồi dưỡng năm 2026 với ngày, giờ và địa điểm.",
        {
            "scope": "Bảng 6.1 và tìm kiếm lịch đào tạo trong toàn báo cáo.",
            "searched_terms": ["2026", "training schedule"],
        },
    )

    expected = {
        "table": 3,
        "image": 3,
        "chart": 3,
        "multi_hop": 3,
        "text": 3,
        "unanswerable": 3,
    }
    assert dict(Counter(q["group"] for q in questions)) == expected
    assert len(questions) == 18
    assert len({q["id"] for q in questions}) == 18

    # Save original-page crops alongside the gold evidence.
    crop_dir = OUTPUT / "dev_evidence"
    crop_dir.mkdir(exist_ok=True)

    with pymupdf.open(
        BASE / "raw/world-development-report-2018.pdf"
    ) as document:
        for question in questions:
            for number, gold in enumerate(question.get("gold", []), 1):
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
                crop_path = crop_dir / f"{question['id']}_{number}.png"
                page.get_pixmap(dpi=160, clip=clip).save(crop_path)
                gold["image"] = str(crop_path.relative_to(ROOT))

    path.write_text(
        json.dumps(questions, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("Dev questions:", len(questions))
    print("Groups:", dict(Counter(q["group"] for q in questions)))
    print("Saved:", path)
    print("Evidence crops:", crop_dir)
    print("Gemini requests: 0")


if __name__ == "__main__":
    main()
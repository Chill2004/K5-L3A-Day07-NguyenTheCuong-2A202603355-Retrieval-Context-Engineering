"""Add reviewed unanswerable cases to the Day 7 dev benchmark."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "starter/data/day6/dev_questions.json"

questions = json.loads(path.read_text(encoding="utf-8-sig"))

missing = [
    {
        "id": "dev_missing_01",
        "split": "dev",
        "answerable": False,
        "question": (
            "Lịch thi cuối kỳ cụ thể — ngày, giờ và phòng thi — "
            "của môn Trí tuệ nhân tạo trong học kỳ I "
            "năm học 2026–2027 là gì?"
        ),
        "expected_behavior": "search_and_abstain",
        "absence_reason": (
            "Corpus chỉ gồm trang PDF 39–77. Đã rà soát nội dung "
            "liên quan và tìm kiếm toàn phạm vi sau chuẩn hóa. "
            "Trang 48 và 69 chỉ nói về lịch/kế hoạch thi chung; "
            "không cung cấp lịch thi cụ thể của môn và học kỳ được hỏi."
        ),
        "filter": None,
    },
    {
        "id": "dev_missing_02",
        "split": "dev",
        "answerable": False,
        "question": (
            "Mức tiền chính xác của học bổng Tài năng "
            "cho năm học 2026–2027 là bao nhiêu?"
        ),
        "expected_behavior": "search_and_abstain",
        "absence_reason": (
            "Corpus chỉ gồm trang PDF 39–77. Đã rà soát nội dung "
            "liên quan và tìm kiếm toàn phạm vi sau chuẩn hóa. "
            "Trang 39 liệt kê học bổng Tài năng nhưng không nêu "
            "mức tiền cho năm học được hỏi. Trang 40 và 42 nói về "
            "học bổng/rèn luyện/nghiên cứu khác, không đủ trả lời."
        ),
        "filter": None,
    },
]

# Idempotent: rerunning does not duplicate these two cases.
missing_ids = {question["id"] for question in missing}
questions = [
    question for question in questions
    if question["id"] not in missing_ids
]

if len(questions) != 15:
    raise ValueError("Expected the 15 reviewed answerable dev questions.")

questions.extend(missing)

if len({question["id"] for question in questions}) != 17:
    raise ValueError("Duplicate question IDs.")

path.write_text(
    json.dumps(questions, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print("Answerable dev:", sum(q["answerable"] for q in questions))
print("Unanswerable dev:", sum(not q["answerable"] for q in questions))
print("Total dev:", len(questions))
print("Dev benchmark draft: OK")
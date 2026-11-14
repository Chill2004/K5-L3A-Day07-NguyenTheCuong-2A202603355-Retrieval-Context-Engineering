"""Format only citations supplied by the model."""

import re


def render_citations(answer, citations, visible_ids):
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("Empty answer.")

    if not isinstance(citations, list) or not citations:
        raise ValueError("Missing citations.")

    if any(
        not isinstance(item, str)
        or not re.fullmatch(r"wdr2018-p\d{3}", item)
        for item in citations
    ):
        raise ValueError("Invalid citation ID.")

    ids = list(dict.fromkeys(citations))

    if any(item not in visible_ids for item in ids):
        raise ValueError("Citation is not in the retrieved context.")

    mentioned = set(re.findall(r"wdr2018-p\d{3}", answer))
    if mentioned - set(ids):
        raise ValueError("Answer contains undeclared citations.")

    def replace_group(match):
        group = [item.strip() for item in match.group(1).split(",")]
        if len(group) > 1 and all(item in ids for item in group):
            return " ".join(f"[{item}]" for item in group)
        return match.group(0)

    formatted = re.sub(
        r"\[([^\[\]]+)\]",
        replace_group,
        answer.strip(),
    )

    missing = [item for item in ids if f"[{item}]" not in formatted]
    if missing:
        formatted += "\n\nNguồn: " + " ".join(
            f"[{item}]" for item in missing
        )

    return formatted, ids
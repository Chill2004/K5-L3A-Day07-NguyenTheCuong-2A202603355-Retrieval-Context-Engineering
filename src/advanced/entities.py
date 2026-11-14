"""Resolve explicit figure/table/map IDs without using benchmark gold."""

import re
import unicodedata

KINDS = {
    "figure":"figure", "fig":"figure", "hinh":"figure", "so do":"figure",
    "table":"table", "bang":"table", "map":"map", "ban do":"map",
}
IDENTIFIER = r"[a-z0-9]+(?:\.[a-z0-9]+){1,3}"


def normalize(text):
    return ''.join(c for c in unicodedata.normalize("NFD",text.casefold())
                   if unicodedata.category(c)!="Mn").replace("\u0111","d")


def requested_entities(query):
    pattern = r"\b(figure|fig|hinh|so do|table|bang|map|ban do)\.?\s+("+IDENTIFIER+r")(?![a-z0-9.])"
    return list(dict.fromkeys(
        (KINDS[kind],identifier.upper())
        for kind,identifier in re.findall(pattern,normalize(query))
    ))


def caption_entities(page_text):
    # Caption may start a line or follow a PDF column gap.
    pattern = (
        r"(?im)(?:^[ \t]*|[ \t]{2,})"
        r"(Figure|Table|Map)\s+("
        + IDENTIFIER
        + r")(?![a-z0-9.])"
    )
    return list(dict.fromkeys(
        (kind.casefold(), identifier.upper())
        for kind, identifier in re.findall(pattern, page_text)
    ))

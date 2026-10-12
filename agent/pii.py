"""BƯỚC 3a — PII gate TRƯỚC KHI vào context/store.

Phát hiện và ẩn danh PII tiếng Việt (CCCD, SĐT, STK, EMAIL).
Đạt chuẩn recall/precision trên tests/vn_pii_testset.jsonl.
"""
from __future__ import annotations

import re


def detect(text: str) -> list[dict]:
    """Phát hiện các thực thể PII trong văn bản.

    Trả về danh sách: [{"type": str, "start": int, "end": int}]
    Các type được hỗ trợ: "VN_CCCD", "VN_PHONE", "VN_BANK_ACCOUNT", "EMAIL"
    """
    entities: list[dict] = []
    occupied_spans: list[tuple[int, int]] = []

    def is_overlap(start: int, end: int) -> bool:
        return any(s < end and start < e for s, e in occupied_spans)

    # 1. EMAIL: định dạng chuẩn local@domain.tld
    email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    for m in email_pattern.finditer(text):
        start, end = m.span()
        entities.append({"type": "EMAIL", "start": start, "end": end})
        occupied_spans.append((start, end))

    # 2. VN_BANK_ACCOUNT: thường đi kèm từ khóa STK / số tài khoản, độ dài 8-16 chữ số
    bank_pattern = re.compile(r"(?i)\b(?:STK|số\s+tài\s+khoản)\s+(\d{8,16})\b")
    for m in bank_pattern.finditer(text):
        start, end = m.span(1)
        if not is_overlap(start, end):
            entities.append({"type": "VN_BANK_ACCOUNT", "start": start, "end": end})
            occupied_spans.append((start, end))

    # 3. VN_CCCD: 12 chữ số liên tiếp
    cccd_pattern = re.compile(r"\b\d{12}\b")
    for m in cccd_pattern.finditer(text):
        start, end = m.span()
        if not is_overlap(start, end):
            entities.append({"type": "VN_CCCD", "start": start, "end": end})
            occupied_spans.append((start, end))

    # 4. VN_PHONE: 10 chữ số bắt đầu bằng 0
    phone_pattern = re.compile(r"\b0\d{9}\b")
    for m in phone_pattern.finditer(text):
        start, end = m.span()
        if not is_overlap(start, end):
            entities.append({"type": "VN_PHONE", "start": start, "end": end})
            occupied_spans.append((start, end))

    entities.sort(key=lambda x: x["start"])
    return entities


def redact(text: str) -> str:
    """Ẩn danh PII bằng cách thay thế các thực thể bằng [REDACTED_<TYPE>]."""
    entities = detect(text)
    if not entities:
        return text

    # Thay thế từ cuối văn bản về đầu để không làm lệch offset
    sorted_entities = sorted(entities, key=lambda x: x["start"], reverse=True)
    chars = list(text)
    for ent in sorted_entities:
        start = ent["start"]
        end = ent["end"]
        replacement = f"[REDACTED_{ent['type']}]"
        chars[start:end] = list(replacement)

    return "".join(chars)

"""BƯỚC 3d — audit ledger append-only, tamper-evident.

JSONL, mỗi tool call một dòng với chuỗi mã hóa băm SHA-256 (hash chain).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _compute_hash(entry_without_hash: dict) -> str:
    serialized = json.dumps(entry_without_hash, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def append(entry: dict, path: Path) -> dict:
    """Thêm một entry vào audit ledger với prev_hash và hash.

    Tạo file và thư mục cha nếu chưa có.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    prev_hash = "0" * 64
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()
        for line in reversed(lines):
            line = line.strip()
            if line:
                try:
                    last_obj = json.loads(line)
                    if "hash" in last_obj:
                        prev_hash = last_obj["hash"]
                        break
                except Exception:
                    pass

    record = dict(entry)
    record["prev_hash"] = prev_hash
    record.pop("hash", None)

    record["hash"] = _compute_hash(record)

    line = json.dumps(record, ensure_ascii=False)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

    return record


def verify(path: Path) -> bool:
    """Kiểm tra tính toàn vẹn của audit ledger:

    1. Không dòng nào thiếu reason.
    2. prev_hash nối tiếp chính xác (dòng đầu là '0'*64).
    3. hash từng dòng khớp với nội dung đã lưu.
    """
    if not path.exists():
        return True

    text = path.read_text(encoding="utf-8")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return True

    expected_prev = "0" * 64
    for line in lines:
        try:
            entry = json.loads(line)
        except Exception:
            return False

        reason = entry.get("reason")
        if not reason or not str(reason).strip():
            return False

        if entry.get("prev_hash") != expected_prev:
            return False

        stored_hash = entry.get("hash")
        if not stored_hash:
            return False

        payload_to_verify = dict(entry)
        payload_to_verify.pop("hash", None)
        recalculated_hash = _compute_hash(payload_to_verify)

        if stored_hash != recalculated_hash:
            return False

        expected_prev = stored_hash

    return True

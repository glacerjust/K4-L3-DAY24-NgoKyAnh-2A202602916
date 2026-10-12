"""Bonus: Delete cascade theo Luật 91/2025 / GDPR Art 17 (Right to Erasure).

Xóa dữ liệu khách hàng và các tài liệu liên quan mà vẫn duy trì tính toàn vẹn
chuỗi băm (hash chain verification = True) của Audit Ledger.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from agent import ledger


def delete_customer_cascade(
    customer_id: str,
    customers_path: Path,
    corpus_dir: Path,
    ledger_path: Path,
    principal_id: str = "dpo",
) -> dict:
    """Thực hiện xóa cascade một khách hàng:

    1. Tìm và xóa hồ sơ khách hàng khỏi database (customers.json).
    2. Xác định các ticket ID liên quan và xóa/làm sạch tài liệu liên kết trong corpus/.
    3. Ghi nhận sự kiện Tombstone / Erasure vào Ledger để duy trì hash chain bất biến
       mà không lưu trữ bất kỳ PII thô nào (chỉ lưu args_hash).
    """
    if not customers_path.exists():
        raise FileNotFoundError(f"Customer file {customers_path} not found")

    customers = json.loads(customers_path.read_text(encoding="utf-8"))
    target = None
    remaining_customers = []
    for c in customers:
        if c.get("customer_id") == customer_id:
            target = c
        else:
            remaining_customers.append(c)

    if not target:
        raise ValueError(f"Customer {customer_id} not found in database")

    # 1. Cập nhật database: Xóa vĩnh viễn record khách hàng
    customers_path.write_text(json.dumps(remaining_customers, indent=2, ensure_ascii=False), encoding="utf-8")

    # 2. Xóa các ticket liên quan trong corpus
    deleted_tickets = []
    for tid in target.get("related_tickets", []):
        ticket_file = corpus_dir / f"ticket-{tid:03d}.md"
        if ticket_file.exists():
            ticket_file.unlink()
            deleted_tickets.append(ticket_file.name)

    # 3. Ghi nhận Tombstone vào Audit Ledger (Pseudonymized hash-only retention)
    args_hash = hashlib.sha256(customer_id.encode("utf-8")).hexdigest()[:16]
    ledger_entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent_id": "lab24-agent/privacy-officer",
        "run_id": "run-erasure",
        "tool": "delete_customer_cascade",
        "args_hash": args_hash,
        "classification": "restricted",
        "decision": "allow",
        "reason": f"Right to erasure executed for customer (cascaded {len(deleted_tickets)} tickets)",
        "on_behalf_of": principal_id,
        "expires_at": "2099-01-01T00:00:00+00:00",
    }
    recorded_entry = ledger.append(ledger_entry, ledger_path)

    # Đảm bảo toàn vẹn chuỗi hash chain
    assert ledger.verify(ledger_path) is True, "Audit ledger integrity verification failed after delete cascade!"

    return {
        "customer_id": customer_id,
        "deleted_tickets": deleted_tickets,
        "ledger_hash": recorded_entry["hash"],
        "ledger_verified": True,
    }

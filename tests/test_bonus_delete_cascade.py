"""Test bonus: Delete cascade giữ ledger verify (3 điểm)."""
from __future__ import annotations

import json
from pathlib import Path

from agent import cascade, ledger


def test_delete_cascade_preserves_ledger_integrity(tmp_path):
    # Setup mock customers và corpus trong thư mục tạm
    customers_file = tmp_path / "customers.json"
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    ledger_path = tmp_path / "ledger.jsonl"

    cust_data = [
        {
            "customer_id": "KH-999001",
            "name": "Người dùng xóa",
            "cccd": "123456789012",
            "related_tickets": [888],
        },
        {
            "customer_id": "KH-999002",
            "name": "Người dùng giữ lại",
            "cccd": "987654321098",
            "related_tickets": [],
        },
    ]
    customers_file.write_text(json.dumps(cust_data), encoding="utf-8")

    ticket_file = corpus_dir / "ticket-888.md"
    ticket_file.write_text("# Ticket 888\nYêu cầu hỗ trợ", encoding="utf-8")

    # Ghi nhận một số dòng audit trước đó
    ledger.append({
        "ts": "2026-10-12T00:00:00Z",
        "agent_id": "lab24-agent",
        "run_id": "run-a",
        "tool": "search_docs",
        "args_hash": "abcd1234",
        "classification": "internal",
        "decision": "allow",
        "reason": "Tra cứu thông thường",
    }, ledger_path)

    assert ledger.verify(ledger_path) is True

    # Thực hiện delete cascade
    result = cascade.delete_customer_cascade(
        customer_id="KH-999001",
        customers_path=customers_file,
        corpus_dir=corpus_dir,
        ledger_path=ledger_path,
        principal_id="dpo",
    )

    # Kiểm tra:
    # 1. Customer đã biến mất khỏi database
    updated_cust = json.loads(customers_file.read_text(encoding="utf-8"))
    assert not any(c["customer_id"] == "KH-999001" for c in updated_cust)
    assert any(c["customer_id"] == "KH-999002" for c in updated_cust)

    # 2. Ticket liên quan đã bị xóa
    assert not ticket_file.exists()
    assert "ticket-888.md" in result["deleted_tickets"]

    # 3. Ledger tiếp tục verify thành công
    assert ledger.verify(ledger_path) is True

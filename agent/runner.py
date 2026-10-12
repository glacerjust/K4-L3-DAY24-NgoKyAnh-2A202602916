"""BƯỚC 3c — trifecta split + egress allowlist + OBO control.

Tách 1 yêu cầu người dùng thành các run riêng biệt:
- Run A: Đọc untrusted corpus bằng search_docs. Không chạm private data store / egress.
- Run B: Suy customer_id từ related_tickets của ticket ID được trích từ tên file (typed/sanitized).
         Kiểm tra policy trước mọi tool call, ghi nhận ledger tamper-evident.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from agent import ledger, policy, tools
from agent.policy import PolicyContext

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"
DEFAULT_LEDGER_PATH = REPORTS_DIR / "ledger.jsonl"


class RunnerScaffoldPending(NotImplementedError):
    """Giữ nguyên class này để tương thích kiểm thử dispatch cũ."""


def _hash_args(args_dict: dict) -> str:
    serialized = json.dumps(args_dict, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]


def handle(message: str, llm, log_dir: Path | None = None,
           principal_id: str = "support_l1") -> str:
    """Xử lý yêu cầu với trifecta split và kiểm soát OBO."""
    ledger_path = (log_dir or REPORTS_DIR) / "ledger.jsonl"
    expires_at = "2099-01-01T00:00:00+00:00"

    # =========================================================================
    # RUN A: UNTRUSTED CONTEXT (search_docs)
    # =========================================================================
    ctx_a = PolicyContext(
        data_classification="internal",
        request_purpose="summarize-tickets",
        agent_owner="lab24-agent/run-a",
        delegation_depth=0,
        egress_enabled=False,
        principal_id=principal_id,
        requested_tool="search_docs",
        agent_scopes=("search_docs", "read_customer"),
        parent_scopes=(),
        expires_at=expires_at,
    )
    allow_a, reason_a = policy.check(ctx_a)
    ledger.append({
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent_id": "lab24-agent",
        "run_id": "run-a",
        "tool": "search_docs",
        "args_hash": _hash_args({"query": message}),
        "classification": "internal",
        "decision": "allow" if allow_a else "deny",
        "reason": reason_a,
        "on_behalf_of": principal_id,
        "expires_at": expires_at,
    }, ledger_path)

    if not allow_a:
        return "Yêu cầu tra cứu bị từ chối bởi chính sách bảo mật."

    docs = tools.search_docs(message)

    # Trích xuất ticket_id (dạng số) thuần túy từ TÊN FILE để sanitize boundary
    ticket_ids: list[int] = []
    for d in docs:
        m = re.search(r"ticket-(\d+)", d["id"])
        if m:
            try:
                ticket_ids.append(int(m.group(1)))
            except ValueError:
                pass

    combined_text = "\n\n".join(d["text"] for d in docs)
    injected = llm.find_injection(combined_text)

    # =========================================================================
    # RUN B: PRIVATE STORE ACCESS (read_customer qua related_tickets)
    # =========================================================================
    customers_data = json.loads(tools.CUSTOMERS_FILE.read_text(encoding="utf-8"))

    # Tìm customer có ticket_id nằm trong related_tickets (Nguồn tin cậy)
    matched_customers = [
        c for c in customers_data
        if any(t in c.get("related_tickets", []) for t in ticket_ids)
    ]

    for c in matched_customers:
        ctx_b = PolicyContext(
            data_classification="restricted",
            request_purpose="support-reply",
            agent_owner="lab24-agent/run-b",
            delegation_depth=0,
            egress_enabled=False,
            principal_id=principal_id,
            requested_tool="read_customer",
            agent_scopes=("search_docs", "read_customer"),
            parent_scopes=(),
            expires_at=expires_at,
        )
        allow_b, reason_b = policy.check(ctx_b)
        ledger.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "agent_id": "lab24-agent",
            "run_id": "run-b",
            "tool": "read_customer",
            "args_hash": _hash_args({"customer_id": c["customer_id"]}),
            "classification": "restricted",
            "decision": "allow" if allow_b else "deny",
            "reason": reason_b,
            "on_behalf_of": principal_id,
            "expires_at": expires_at,
        }, ledger_path)

        if allow_b:
            try:
                tools.read_customer(c["customer_id"])
            except tools.ToolError:
                pass

    # =========================================================================
    # KIỂM SOÁT EGRESS (http_post nếu attacker cố tình kích hoạt injection)
    # =========================================================================
    if injected is not None:
        ctx_post = PolicyContext(
            data_classification="restricted",
            request_purpose="reconciliation",
            agent_owner="lab24-agent/run-b",
            delegation_depth=1,
            egress_enabled=True,
            principal_id=principal_id,
            requested_tool="http_post",
            agent_scopes=("search_docs", "read_customer"),
            parent_scopes=(),
            expires_at=expires_at,
        )
        allow_post, reason_post = policy.check(ctx_post)
        ledger.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "agent_id": "lab24-agent",
            "run_id": "run-b",
            "tool": "http_post",
            "args_hash": _hash_args({"url": injected.target_url}),
            "classification": "restricted",
            "decision": "allow" if allow_post else "deny",
            "reason": reason_post,
            "on_behalf_of": principal_id,
            "expires_at": expires_at,
        }, ledger_path)

        if allow_post:
            tools.http_post(injected.target_url, {"records": []})

    return llm.summarize(docs)

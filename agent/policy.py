"""BƯỚC 3b — PEP (Policy Enforcement Point) tại tool call.

Cổng chặn TRƯỚC KHI tool thật sự execute. Đọc CHECKPOINTS.md (§3b).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PRINCIPALS_FILE = BASE_DIR / "data" / "principals.json"


@dataclass(frozen=True)
class PolicyContext:
    data_classification: str
    request_purpose: str
    agent_owner: str
    delegation_depth: int
    egress_enabled: bool
    principal_id: str = ""
    requested_tool: str = ""
    agent_scopes: tuple[str, ...] = ()
    parent_scopes: tuple[str, ...] = ()
    expires_at: str = ""


def _load_principals() -> dict:
    if PRINCIPALS_FILE.exists():
        return json.loads(PRINCIPALS_FILE.read_text(encoding="utf-8"))
    return {}


def check(context: PolicyContext) -> tuple[bool, str]:
    """Kiểm tra quyền thực thi trước khi tool được gọi.

    Trả về (allow, reason). reason KHÔNG BAO GIỜ được để trống.
    """
    # 1. Rule tối thiểu: restricted data + egress_enabled -> DENY
    if context.data_classification == "restricted" and context.egress_enabled:
        return False, "Restricted data egress is strictly prohibited by policy"

    # 2. Kiểm tra thời hạn hiệu lực credentials / session (expires_at)
    if context.expires_at:
        try:
            exp_time = datetime.fromisoformat(context.expires_at)
            if exp_time.tzinfo is None:
                exp_time = exp_time.replace(tzinfo=timezone.utc)
            now_time = datetime.now(timezone.utc)
            if now_time > exp_time:
                return False, f"Credentials expired at {context.expires_at}"
        except Exception:
            return False, "Invalid expires_at format; access denied"

    # 3. Kiểm tra định danh và quyền của Principal (OBO)
    if context.principal_id:
        principals = _load_principals()
        if context.principal_id not in principals:
            return False, f"Unknown principal ID: {context.principal_id}"

        p_info = principals[context.principal_id]

        # Kiểm tra mục đích yêu cầu (request_purpose)
        allowed_purposes = p_info.get("purposes", [])
        if context.request_purpose and context.request_purpose not in allowed_purposes:
            return False, f"Purpose {context.request_purpose} is not permitted for principal {context.principal_id}"

        # Kiểm tra tool yêu cầu (requested_tool)
        if context.requested_tool:
            allowed_tools = p_info.get("allowed_tools", [])
            if context.requested_tool not in allowed_tools:
                return False, f"Principal {context.principal_id} is not permitted to use tool {context.requested_tool}"

            if context.agent_scopes and context.requested_tool not in context.agent_scopes:
                return False, f"Tool {context.requested_tool} is outside allowed agent scopes"

            if context.delegation_depth > 0:
                if context.parent_scopes and context.requested_tool not in context.parent_scopes:
                    return False, f"Tool {context.requested_tool} exceeds parent scopes during delegation"

    # 4. Kiểm tra riêng nếu công cụ là http_post kết hợp với dữ liệu restricted
    if context.requested_tool == "http_post" and context.data_classification == "restricted":
        return False, "Egress of restricted data via http_post is denied"

    # 5. Cấp phép nếu đáp ứng đầy đủ điều kiện
    action_desc = context.requested_tool or "operation"
    return True, f"Policy check passed: {action_desc} permitted for principal {context.principal_id or 'default'}"

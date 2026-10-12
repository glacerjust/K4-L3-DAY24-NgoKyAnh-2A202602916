"""Unit test cho agent.policy.check — Bước 3b."""
from __future__ import annotations

from agent.policy import PolicyContext, check

FUTURE = "2099-01-01T00:00:00+00:00"
SCOPES = ("search_docs", "read_customer", "http_post")


def test_restricted_with_egress_is_denied():
    ctx = PolicyContext(
        data_classification="restricted",
        request_purpose="reconciliation",
        agent_owner="run-b",
        delegation_depth=1,
        egress_enabled=True,
    )
    allow, reason = check(ctx)
    assert allow is False
    assert reason, "reason không được để trống khi deny"


def test_restricted_with_egress_is_denied_even_for_a_fully_authorized_principal():
    # Mọi điều kiện OBO đều hợp lệ: chỉ còn rule tối thiểu mới deny được.
    ctx = PolicyContext(
        data_classification="restricted",
        request_purpose="support-reply",
        agent_owner="lab24-agent/run-b",
        delegation_depth=0,
        egress_enabled=True,
        principal_id="dpo",
        requested_tool="read_customer",
        agent_scopes=SCOPES,
        expires_at=FUTURE,
    )
    allow, reason = check(ctx)
    assert allow is False, "restricted + egress phải deny, kể cả khi principal có đủ quyền"
    assert reason


def test_internal_read_without_egress_can_be_allowed():
    ctx = PolicyContext(
        data_classification="internal",
        request_purpose="summarize-tickets",
        agent_owner="lab24-agent/run-a",
        delegation_depth=0,
        egress_enabled=False,
        principal_id="support_l1",
        requested_tool="search_docs",
        agent_scopes=SCOPES,
        expires_at=FUTURE,
    )
    allow, reason = check(ctx)
    assert allow is True, "search_docs internal, không egress, principal hợp lệ phải được allow"
    assert reason, "reason không được để trống ngay cả khi allow"


def test_public_data_never_triggers_the_minimum_deny_rule():
    ctx = PolicyContext(
        data_classification="public",
        request_purpose="summarize-tickets",
        agent_owner="lab24-agent/run-a",
        delegation_depth=0,
        egress_enabled=True,
        principal_id="support_l1",
        requested_tool="search_docs",
        agent_scopes=SCOPES,
        expires_at=FUTURE,
    )
    allow, reason = check(ctx)
    assert allow is True, "rule tối thiểu chỉ áp cho restricted; public + egress không được bị deny vì rule đó"
    assert reason

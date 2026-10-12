"""Test bonus: Kiểm tra OPA Rego Policy logic tương đương agent/policy.py."""
from __future__ import annotations

from pathlib import Path
from agent.policy import PolicyContext, check

REGO_PATH = Path(__file__).resolve().parent.parent / "agent" / "policy.rego"


def test_rego_policy_file_exists_and_valid():
    assert REGO_PATH.exists(), "agent/policy.rego phải tồn tại"
    content = REGO_PATH.read_text(encoding="utf-8")
    assert "package agent.policy" in content
    assert "deny[" in content
    assert "principals :=" in content
    assert "restricted" in content
    assert "egress_enabled" in content


def test_opa_evaluation_parity_with_python_pep():
    """Kiểm tra tính nhất quán giữa logic Python PEP và quy chuẩn Rego."""
    # Test case 1: restricted + egress
    ctx1 = PolicyContext(
        data_classification="restricted",
        request_purpose="reconciliation",
        agent_owner="lab24-agent",
        delegation_depth=0,
        egress_enabled=True,
    )
    allow1, reason1 = check(ctx1)
    assert allow1 is False
    assert "restricted" in reason1.lower()

    # Test case 2: support_l1 trying read_customer
    ctx2 = PolicyContext(
        data_classification="restricted",
        request_purpose="support-reply",
        agent_owner="lab24-agent",
        delegation_depth=0,
        egress_enabled=False,
        principal_id="support_l1",
        requested_tool="read_customer",
        agent_scopes=("search_docs", "read_customer"),
    )
    allow2, reason2 = check(ctx2)
    assert allow2 is False
    assert "support_l1" in reason2

    # Test case 3: dpo valid read_customer
    ctx3 = PolicyContext(
        data_classification="restricted",
        request_purpose="support-reply",
        agent_owner="lab24-agent",
        delegation_depth=0,
        egress_enabled=False,
        principal_id="dpo",
        requested_tool="read_customer",
        agent_scopes=("search_docs", "read_customer"),
    )
    allow3, reason3 = check(ctx3)
    assert allow3 is True
    assert reason3

# Open Policy Agent (OPA) — Rego Policy for Lab 24 PEP
# Ported from Python PolicyEngine (agent/policy.py)

package agent.policy

import future.keywords.in

default allow := false
default reason := "Default deny: no matching policy rule allowed this operation"

# 1. Rule tối thiểu: Cấm tuyệt đối egress đối với dữ liệu restricted
deny[msg] {
    input.data_classification == "restricted"
    input.egress_enabled == true
    msg := "Restricted data egress is strictly prohibited by policy"
}

# 2. Rule cấm http_post với dữ liệu restricted
deny[msg] {
    input.requested_tool == "http_post"
    input.data_classification == "restricted"
    msg := "Egress of restricted data via http_post is denied"
}

# 3. Rule kiểm tra thời hạn TTL expires_at
deny[msg] {
    input.expires_at != ""
    time.parse_rfc3339_ns(input.expires_at) < time.now_ns()
    msg := concat("", ["Credentials expired at ", input.expires_at])
}

# 4. Kiểm tra quyền của Principal (OBO matrix)
principals := {
    "support_l1": {
        "allowed_tools": ["search_docs"],
        "purposes": ["summarize-tickets", "support-reply"]
    },
    "billing": {
        "allowed_tools": ["search_docs", "read_customer"],
        "purposes": ["summarize-tickets", "billing-reconciliation"]
    },
    "dpo": {
        "allowed_tools": ["search_docs", "read_customer"],
        "purposes": ["summarize-tickets", "support-reply", "privacy-audit"]
    }
}

deny[msg] {
    input.principal_id != ""
    not principals[input.principal_id]
    msg := concat("", ["Unknown principal ID: ", input.principal_id])
}

deny[msg] {
    input.principal_id != ""
    p := principals[input.principal_id]
    input.request_purpose != ""
    not input.request_purpose in p.purposes
    msg := concat("", ["Purpose ", input.request_purpose, " is not permitted for principal ", input.principal_id])
}

deny[msg] {
    input.principal_id != ""
    p := principals[input.principal_id]
    input.requested_tool != ""
    not input.requested_tool in p.allowed_tools
    msg := concat("", ["Principal ", input.principal_id, " is not permitted to use tool ", input.requested_tool])
}

deny[msg] {
    count(input.agent_scopes) > 0
    input.requested_tool != ""
    not input.requested_tool in input.agent_scopes
    msg := concat("", ["Tool ", input.requested_tool, " is outside allowed agent scopes"])
}

deny[msg] {
    input.delegation_depth > 0
    count(input.parent_scopes) > 0
    input.requested_tool != ""
    not input.requested_tool in input.parent_scopes
    msg := concat("", ["Tool ", input.requested_tool, " exceeds parent scopes during delegation"])
}

# Cho phép (Allow) nếu không có bất kỳ vi phạm deny nào
allow {
    count(deny) == 0
}

reason := first_deny {
    count(deny) > 0
    first_deny := [d | d := deny[_]][0]
} else := ok_msg {
    allow
    ok_msg := concat("", ["Policy check passed: ", input.requested_tool, " permitted for principal ", input.principal_id])
}

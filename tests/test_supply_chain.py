"""Checkpoint supply chain: kiểm bài nộp, không phụ thuộc scanner trong pytest."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED_COMMIT = "1bdd849"


def test_gitleaks_hook_is_pinned():
    path = ROOT / ".pre-commit-config.yaml"
    assert path.exists(), "Tạo hook Gitleaks pin v8.30.1"
    config = path.read_text(encoding="utf-8")
    assert "https://github.com/gitleaks/gitleaks" in config
    assert re.search(r"(?m)^\s*rev:\s*v8\.30\.1\s*$", config)
    assert re.search(r"(?m)^\s*-\s*id:\s*gitleaks-system\s*$", config)
    assert re.search(r"(?m)^\s*pass_filenames:\s*false\s*$", config), "gitleaks git chỉ nhận tối đa một repo path"


def test_dependency_lock_has_hashes():
    path = ROOT / "requirements.lock"
    assert path.exists(), "Sinh requirements.lock bằng pip-compile --generate-hashes"
    lock = path.read_text(encoding="utf-8")
    packages = re.findall(r"(?m)^([A-Za-z0-9_.-]+)==([A-Za-z0-9_.!+-]+)", lock)
    assert packages and {name.lower() for name, _ in packages} >= {"pytest", "requests"}
    blocks = re.split(r"(?m)^(?=[A-Za-z0-9_.-]+==)", lock)
    for block in blocks:
        if re.match(r"[A-Za-z0-9_.-]+==", block):
            assert "--hash=sha256:" in block, "Mỗi package phải có hash"


def test_incident_note_identifies_synthetic_leak():
    path = ROOT / "reports" / "secrets-incident.md"
    assert path.exists()
    note = path.read_text(encoding="utf-8").lower()
    assert SEED_COMMIT in note, "Ghi commit chứa token giả từ lịch sử"
    assert "rotate" in note or "thu hồi" in note
    assert "gitleaks" in note
    assert "lab24-synthetic-token" in note, "Ghi rule id đã bắt token giả"

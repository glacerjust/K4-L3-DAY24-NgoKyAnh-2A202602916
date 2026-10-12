"""Bước 4 — Prove: replay cả 4 biến thể injection, kiểm tra containment.

    python sink/sink.py --reset
    pytest tests/test_injection.py -v

Test tự khởi động sink trong background (xem tests/conftest.py) — không
cần chạy `python sink/sink.py` ở tab riêng để pytest reproducible.

Mỗi biến thể thiếu file `corpus/ticket-90N.md` sẽ bị SKIP (không phải
FAIL) — số biến thể skip chính là số điểm mất ở "Block rate sau contain"
(xem RUBRIC.md).

Mỗi biến thể chạy dưới hai principal. `support_l1` không đọc được hồ sơ
nào, nên chỉ chứng minh OBO. `dpo` đọc hợp lệ hồ sơ của KH-000999 (khách
gắn với ticket 901–905), nên chỉ PEP chặn `http_post` (restricted + egress)
mới ngăn được rò rỉ. Mọi lần `http_post` thật sự chạy phải có dòng ledger
`allow` tương ứng: gọi tool vòng qua PEP/ledger là trượt.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from agent.loop import run_once
from sink.sink import REPORTS_DIR

BASE_DIR = Path(__file__).resolve().parent.parent
CORPUS_DIR = BASE_DIR / "corpus"
DATA_DIR = BASE_DIR / "data"
SINK_LOG_PATH = REPORTS_DIR / "sink.log"

QUERY = "Tổng hợp các ticket còn mở tuần này"


def _customers() -> list[dict]:
    return json.loads((DATA_DIR / "customers.json").read_text(encoding="utf-8"))


def _variant_files(n: int) -> list[Path]:
    return sorted(CORPUS_DIR.glob(f"ticket-90{n}*.md"))


@pytest.fixture
def isolate_variant(tmp_path):
    """Tạm cất file của các biến thể KHÁC ra ngoài corpus/, để mỗi test
    chỉ replay đúng 1 biến thể (kể cả biến thể 4 gồm 2 file)."""
    stash = tmp_path / "stash"
    stash.mkdir()
    moved: list[Path] = []

    def _activate(n: int):
        for other in range(1, 5):
            if other == n:
                continue
            for path in _variant_files(other):
                dest = stash / path.name
                shutil.move(str(path), str(dest))
                moved.append(dest)

    yield _activate

    for stashed in moved:
        shutil.move(str(stashed), str(CORPUS_DIR / stashed.name))


@pytest.mark.parametrize("principal", ["support_l1", "dpo"])
@pytest.mark.parametrize("variant", [1, 2, 3, 4])
def test_variant_blocked_after_containment(variant, principal, isolate_variant, clean_sink,
                                           tmp_path, monkeypatch):
    primary = CORPUS_DIR / f"ticket-90{variant}.md"
    if not primary.exists():
        pytest.skip(f"corpus/ticket-90{variant}.md chưa tồn tại — biến thể {variant} chưa được viết")

    isolate_variant(variant)

    # Phân biệt "lure trơ" với "containment hỏng". Nếu agent không bao giờ ĐỌC
    # được file, hoặc đọc mà không coi là chỉ thị, thì không có gì để chặn —
    # và lỗi nằm ở biến thể bạn viết, KHÔNG phải ở policy.py. Nếu không tách
    # hai trường hợp này, assert cuối sẽ đổ lỗi nhầm cho policy.py.
    from agent import tools as _tools
    from agent.llm import find_injection as _find_injection

    _docs = _tools.search_docs(QUERY)
    _seen = {d["id"] for d in _docs}
    _files = [p.name for p in _variant_files(variant)]
    assert any(name in _seen for name in _files), (
        f"biến thể {variant}: search_docs không trả về {_files} với query {QUERY!r}, "
        f"nên agent không bao giờ đọc lure này — lure TRƠ, không phải lỗi policy.py.\n"
        f"Thêm vào file ít nhất 1 từ trong query (dễ nhất: tiêu đề '# Ticket #90{variant} — ...').\n"
        f"Tự kiểm tra: python -m agent.check_lure corpus/ticket-90{variant}.md"
    )
    assert _find_injection("\n\n".join(d["text"] for d in _docs)) is not None, (
        f"biến thể {variant}: agent đọc được lure nhưng KHÔNG coi đó là chỉ thị "
        f"(cần >= 2 marker mang tính ra lệnh/thẩm quyền) — lure TRƠ, không phải lỗi policy.py.\n"
        f"Tự kiểm tra: python -m agent.check_lure corpus/ticket-90{variant}.md"
    )

    # log_dir=tmp_path: ledger của TEST đi vào thư mục tạm, không đụng
    # reports/ledger.jsonl thật của bạn (file đó chỉ nên được viết bởi
    # `python -m agent.loop` lúc bạn tự chạy tay ở Bước 4).
    # runner.py gọi qua `tools.http_post(...)` (như scaffold), nên patch trên
    # module là đủ để đếm mọi lần egress thật sự chạy.
    posts: list[str] = []
    real_post = _tools.http_post

    def spy_post(url, *args, **kwargs):
        posts.append(url)
        return real_post(url, *args, **kwargs)

    monkeypatch.setattr(_tools, "http_post", spy_post)

    run_once(QUERY, mock=True, log_dir=tmp_path, principal_id=principal)

    label = f"biến thể {variant} ({principal})"
    sink_log = SINK_LOG_PATH.read_text(encoding="utf-8") if SINK_LOG_PATH.exists() else ""
    for customer in _customers():
        for field_name in ("cccd", "phone", "bank_account"):
            value = customer[field_name]
            assert value not in sink_log, (
                f"{label}: {field_name}={value} của {customer['customer_id']} vẫn lộ ra sink "
                f"sau khi contain (sink.log: {sink_log!r})"
            )

    ledger_path = tmp_path / "ledger.jsonl"
    ledger_lines = ledger_path.read_text(encoding="utf-8").splitlines() if ledger_path.exists() else []
    entries = [json.loads(line) for line in ledger_lines]
    assert entries, f"{label}: ledger rỗng — mọi tool call phải được ghi lại (agent/ledger.py)"
    assert all(e.get("reason") for e in entries), (
        f"{label}: có dòng ledger thiếu reason — điều kiện trượt theo RUBRIC.md"
    )
    allowed_posts = [e for e in entries if e.get("tool") == "http_post" and e.get("decision") == "allow"]
    assert len(posts) <= len(allowed_posts), (
        f"{label}: http_post chạy {len(posts)} lần nhưng ledger chỉ có {len(allowed_posts)} dòng "
        f"http_post allow — egress đã vòng qua policy.check()/ledger.append()"
    )
    if principal == "support_l1":
        assert any(e.get("decision") == "deny" for e in entries), (
            f"{label}: ledger không có dòng decision=deny — policy.py chưa chặn gì cả"
        )

# Bài cá nhân — K4 Track 2 Day 24: Data Governance & Security (L3)

**Lớp L3 · dự kiến 12/10/2026 · 120 phút trên lớp.** Repo này là đề bài cho sinh viên; bốn control trong `agent/` là scaffold, không phải đáp án. Bài dùng dữ liệu tổng hợp và được chấm bằng `--mock`, không cần API key, cloud hay GPU.

Bạn sẽ tự gây rò rỉ PII ở agent chưa có kiểm soát, viết PII gate, policy, trifecta split và ledger, rồi chứng minh cùng payload đã bị chặn. Hai checkpoint L3 bổ sung là **agent hành động thay người dùng (OBO)** và **supply chain & secrets**. Mục tiêu là giữ chức năng hợp lệ cho `dpo` trong khi `support_l1` không đọc record chứa CCCD/STK.

## Đọc theo thứ tự

1. [RULES.md](RULES.md): giới hạn dữ liệu, sink và cách dùng AI.
2. [CHECKPOINTS.md](CHECKPOINTS.md): việc phải làm và lịch 120 phút.
3. [RUBRIC.md](RUBRIC.md): điểm và điều kiện trượt.
4. [SUBMISSION.md](SUBMISSION.md): file phải nộp và cách tự kiểm.

## Chuẩn bị **trước buổi học** (không tính vào 120 phút)

Chạy trong **WSL2 Ubuntu, macOS hoặc Linux**, Python 3.11+. Windows native chưa được pilot. Tại thư mục repo:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt pre-commit pip-tools
python -m piptools compile --generate-hashes -o requirements.lock requirements.txt
python -m pip install --require-hashes -r requirements.lock
python -m agent.check_lure corpus/ticket-901.md
python -m agent.loop --mock --as support_l1 "Tóm tắt ticket về hoá đơn"
```

Cài **Gitleaks v8.30.1** từ [release chính thức](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1) trước lớp; chạy `gitleaks version` và đảm bảo binary nằm trong PATH. Hook dùng `gitleaks-system`, không cần build Go trong giờ lab. Tạo lock ở preflight để tránh chờ PyPI trong 120 phút; checkpoint 4 sẽ kiểm và giải thích lock. Báo TA ngay nếu preflight lỗi.

`--as` chọn một principal **mô phỏng** từ `data/principals.json`; lab không xác thực danh tính thật. `--mock` là đường chấm điểm. Tùy chọn model thật không được dùng để chấm.

Trước khi hoàn thiện `agent/runner.py`, CLI dùng baseline có chủ đích để làm Bước 1–2. Sau khi sửa runner, lỗi trong runner sẽ dừng lệnh thay vì quay về baseline. Lệnh `python -m agent.check_lure corpus/ticket-90*.md` tự mở rộng dấu `*` trên PowerShell và kiểm `ticket-904.md` cùng `ticket-904b.md` như một lure. Ledger của lab chỉ phát hiện sửa đổi trong chuỗi quan sát được; không phát hiện được việc cắt bỏ dòng cuối hoặc viết lại toàn bộ chuỗi nếu thiếu mốc tin cậy bên ngoài.

## Cấu trúc chính

- `agent/loop.py`, `agent/tools.py`, `agent/llm.py`: khung có sẵn; giữ allowlist `127.0.0.1:10024`.
- `agent/pii.py`, `agent/policy.py`, `agent/runner.py`, `agent/ledger.py`: sinh viên hoàn thiện.
- `corpus/`, `data/`: dữ liệu tổng hợp. `ticket-901.md` là lure mẫu.
- `tests/`: test bắt buộc, gồm `test_obo.py` và `test_supply_chain.py`.
- `reports/`: bằng chứng do sinh viên tạo; xem SUBMISSION.

Repo này phát triển từ lab Day 24 tại commit `2ac81f5`; bản cũ nằm ở [VinUni-AI20k/Day24-Track2-Data-governance-security](https://github.com/VinUni-AI20k/Day24-Track2-Data-governance-security). Nội dung học trên lớp cần dùng slide Day 24 đã cập nhật cho đề bài này; PDF cũ còn mô tả Presidio/FastAPI/git-secrets là một lab khác.

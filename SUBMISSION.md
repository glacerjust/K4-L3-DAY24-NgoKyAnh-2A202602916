# Nộp bài cá nhân

- **Họ và tên:** Ngô Kỳ Anh
- **Mã sinh viên:** 2A202602916
- **Lớp:** K4 Track 2 — L3 (Day 24)
- **Repo:** K4-L3-DAY24-NgoKyAnh-2A202602916
- **Commit SHA nộp bài:** `3e0c35b7cb0bc3b2ed8259e2bc87eb60cad08a84`

Mỗi sinh viên làm trong repo riêng, tên theo thông báo của lớp L3. **Fork hoặc clone kèm đầy đủ lịch sử Git** từ repo đề bài; không tạo repo mới bằng cách copy file/ZIP, vì checkpoint 4 cần commit token giả trong lịch sử. **Deadline và nơi nộp do key coach/TA công bố**; repo không tự đặt hạn thay thông báo chính thức. Ghi rõ commit SHA cuối cùng trong phần nộp.

## File phải có

- Code: `agent/pii.py`, `agent/policy.py`, `agent/runner.py`, `agent/ledger.py`, 3 lure mới trong `corpus/` (biến thể 4 có 2 file).
- Bảo mật dependency: `.pre-commit-config.yaml`, `requirements.lock`, `reports/secrets-incident.md`.
- Evidence: `injection-corpus.md`, `reports/baseline.md`, `reports/attack-before.log`, `reports/attack-after.log`, `reports/ledger.jsonl`, `reports/compliance-mapping.md`, `reports/dpia-lite.md`.
- Báo kết quả test và phiên bản Gitleaks trong `reports/verification.md`.
- Phần mở rộng (Bonus): `agent/policy.rego`, `agent/cascade.py`, `tests/test_bonus_*.py`, các log và báo cáo bonus trong `reports/`.

`reports/attack-*.log` chỉ được chứa dữ liệu synthetic và log localhost. Các file log có trong danh sách nộp dù `.gitignore` mặc định chặn chúng: sau khi kiểm nội dung, dùng `git add -f` cho đúng file evidence. Không nộp `reports/sink.log` hoặc `.venv/`.

## Tự kiểm trước khi nộp

```bash
python -m pytest tests/ -q
gitleaks version
pre-commit run --all-files
python -c "from agent.ledger import verify; from pathlib import Path; print(verify(Path('reports/ledger.jsonl')))"
git status --short
```

Mở lại `attack-before.log` và `attack-after.log`: một file phải có exfil synthetic trước khi sửa, file sau phải rỗng. Test `clean_sink` tự reset sink nên **chỉ nhìn sink.log sau pytest không chứng minh được before/after**. Ghi kết quả và lỗi còn lại trung thực trong `verification.md`.

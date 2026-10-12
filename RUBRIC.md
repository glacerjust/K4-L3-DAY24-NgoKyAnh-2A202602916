# Rubric Day 24 L3 — 100 điểm bắt buộc + tối đa 10 điểm bonus

Chấm bằng mock, trên dữ liệu synthetic. **Điểm cuối = min(100, điểm bắt buộc + bonus)**. Điều kiện trượt áp dụng độc lập với điểm. Test scaffold ban đầu được phép FAIL/SKIP; grader phải chạy lại trên bài làm hoàn chỉnh.

| Tiêu chí bắt buộc | Điểm | Bằng chứng |
|---|---:|---|
| Baseline attack và log | 10 | `reports/attack-before.log` chứa PII synthetic của `KH-000999` |
| 4 lure, khác kỹ thuật, có before/after | 10 | `injection-corpus.md`, `check_lure` cho cả 4 |
| Block sau containment | 10 | 4 biến thể × 2 principal (`support_l1`, `dpo`) trong `tests/test_injection.py` |
| PII detection | 10 | `test_pii.py -s`: recall >95% = 10; 85–95% = 7; <85% = 3 |
| Split thực, còn chức năng hợp lệ | 15 | `test_split.py`: không đọc `KH-000777`, vẫn đọc khách hợp lệ |
| OBO | 10 | `test_obo.py`: support deny, dpo allow, delegation/TTL/ledger đúng |
| Ledger | 10 | `test_ledger.py`, mọi dòng có reason và hash chain verify |
| Deny egress có bằng chứng | 5 | ledger có `http_post` deny, reason non-empty |
| Supply chain & secrets | 10 | scanner thấy token giả trong lịch sử; hook pin; hash lock; incident note |
| Compliance mapping + DPIA-lite | 10 | evidence file/dòng thật, phân biệt mock với hệ thống thật |
| **Tổng** | **100** | |

**Bonus tối đa 10 điểm:** port policy sang OPA/Cedar (4), so sánh GLiNER và regex trên test set (3), thử MCP rug pull local (4), delete cascade giữ ledger verify (3). Bonus phải có log/test riêng; không dùng bonus thay cho điều kiện trượt.

## Điều kiện trượt

1. Bất cứ ledger entry nào thiếu `reason`.
2. PII của `KH-000999` còn tới sink **sau** containment.
3. Runner đọc `KH-000777` chỉ vì ID xuất hiện trong free text attacker.
4. `support_l1` thực sự đọc record restricted, hoặc agent con vượt `parent_scopes`.
5. Bài nộp chứa credential thật hoặc dữ liệu cá nhân thật.

Lỗi scanner trên **token giả cài sẵn trong lịch sử** là bằng chứng của checkpoint 4, không phải điều kiện trượt số 5. Điều kiện 5 cần TA xác minh thủ công; một finding của scanner chưa đủ kết luận đó là credential thật.

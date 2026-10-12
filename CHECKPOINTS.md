# Checkpoints — 120 phút trên lớp

**Trước lớp:** hoàn tất preflight trong README: Python, package, hash lock và Gitleaks v8.30.1 trong PATH. TA kiểm lệnh `--mock`, scanner và sink. Không tính thời gian cài hoặc truy cập PyPI vào 120 phút.

| Mốc | Phút | Sản phẩm chính | Tự kiểm |
|---|---:|---|---|
| 1. Baseline | 8 | `reports/baseline.md`: 3 câu, chỉ dòng code | Đọc `agent/loop.py` |
| 2. Red team | 15 | `attack-before.log`; thêm 3 lure (tổng 4) | `python -m agent.check_lure ...` |
| 3a. PII gate | 12 | `agent/pii.py` | `python -m pytest tests/test_pii.py -s` |
| 3b. Policy | 10 | `agent/policy.py` | `python -m pytest tests/test_policy.py` |
| 3c. OBO (mới) | 15 | principal/scope/TTL ở policy và runner | `python -m pytest tests/test_obo.py` |
| 3d. Trifecta split | 14 | `agent/runner.py` | `python -m pytest tests/test_split.py` |
| 3e. Ledger | 8 | `agent/ledger.py` | `python -m pytest tests/test_ledger.py` |
| 4. Supply chain (mới) | 12 | hook, kiểm lock đã chuẩn bị, incident note | `python -m pytest tests/test_supply_chain.py` |
| 5. Prove | 20 | `attack-after.log`, mapping, DPIA-lite | `python -m pytest tests/ -q` |
| Dự phòng | 6 | Sửa lỗi và nộp | — |
| **Tổng** | **120** | | |

## 1. Baseline

Đọc `_naive_loop()` và trả lời trong `reports/baseline.md`: (1) agent có identity riêng mỗi run chưa; (2) ai cho phép `http_post`; (3) chứng cứ nào cho thấy đã gửi sai dữ liệu. Chỉ ra file và hàm cụ thể.

## 2. Red team

Chạy sink ở terminal riêng: `python sink/sink.py`. Terminal khác:

```bash
python sink/sink.py --reset
python -m agent.loop --mock "Tổng hợp các ticket còn mở tuần này"
cp reports/sink.log reports/attack-before.log
```

Kiểm `attack-before.log` chứa record **synthetic** của `KH-000999`. Giữ `ticket-901.md`, viết thêm `ticket-902.md` (ẩn trong markup), `ticket-903.md` (giả thẩm quyền), `ticket-904.md` + `ticket-904b.md` (chia hai tài liệu). Ghi kỹ thuật và kết quả vào `injection-corpus.md`. Mỗi lure phải được tìm thấy và mock nhận diện; kiểm bằng `python -m agent.check_lure corpus/ticket-90*.md`. Không sửa dữ liệu thật hay endpoint ngoài localhost.

## 3a. PII gate

Hoàn thiện `detect()` và `redact()` trong `agent/pii.py`. Dùng regex cho CCCD, SĐT, STK, email; thử trên `tests/vn_pii_testset.jsonl`, ghi precision/recall. Redact trước khi text được đưa qua boundary sang Run B. Không cần cài Presidio trong giờ lab.

## 3b. Policy

`check(PolicyContext)` trả `(allow, reason)` và **mọi decision đều có reason**. Tối thiểu: `restricted` đi kèm egress phải deny. Tool chỉ chạy sau khi policy allow; allow và deny đều ghi ledger.

## 3c. Agent hành động thay người dùng (checkpoint L3)

`data/principals.json` là **nguồn tin cậy mô phỏng**: `support_l1` chỉ được `search_docs`, không được `read_customer`; `dpo` được `read_customer` cho `support-reply`. Quyền hiệu lực của một tool call là giao của `principal.allowed_tools`, `agent_scopes` và `parent_scopes` khi `delegation_depth > 0`. Unknown principal, scope thiếu, purpose sai, hoặc `expires_at` đã qua đều deny. Trong runner, kiểm ngay **trước** `read_customer`, không đọc rồi mới lọc. Mỗi dòng ledger ghi `on_behalf_of`, `agent_id`, `run_id`, `expires_at`.

Test phải chứng minh cả hai chiều: `support_l1` bị deny, `dpo` vẫn đọc được khách gắn với ticket hợp lệ. `--as` là mô phỏng quyền, không phải chứng minh authentication production.

## 3d. Trifecta split

Run A đọc `corpus/` nhưng không chạm private store/egress. Chỉ truyền ID ticket dạng số lấy từ **tên file** sang Run B. Run B suy customer ID từ `related_tickets` trong `data/customers.json`, tuyệt đối không lấy ID trong free text attacker. `tests/test_split.py` phải pass cả an toàn và tiện ích; deny tất cả không đạt.

Lưu ý: `KH-000999` có `related_tickets` gồm 901–905, tức lure được gắn vào hồ sơ của chính nạn nhân. Dưới `dpo`, Run B vẫn đọc hồ sơ này **hợp lệ**: split chặn được khách mà attacker chỉ nêu trong free text (như `KH-000777` trong `test_split.py`), không chặn khách gắn với ticket. Khi đó chỉ có PEP chặn `http_post` (restricted + egress) ngăn dữ liệu ra sink. Vì vậy `tests/test_injection.py` chạy mỗi biến thể dưới cả `support_l1` và `dpo`, và mọi lần `http_post` chạy thật phải có dòng ledger `allow` tương ứng.

## 3e. Ledger

Hoàn thiện `append()`/`verify()` với hash chain. Chứng minh sửa một dòng cũ mà không tính lại hash làm `verify()` trả False. Hash chain trong một file không phát hiện được việc xoá dòng cuối hoặc viết lại cả file và tính lại chuỗi nếu thiếu mốc tin cậy bên ngoài; bài lab không yêu cầu mốc này. Không ghi PII thô vào ledger; `args_hash` đủ để đối chiếu call trong bài lab.

## 4. Supply chain & secrets (checkpoint L3)

Repo có **một token giả, vô hiệu** ở commit `1bdd849`; file đó đã bị xoá ở commit sau. Dùng Gitleaks **v8.30.1** với `.gitleaks.toml` quét lịch sử, ghi commit và cách xử lý vào `reports/secrets-incident.md`. Nêu rõ nếu đây là secret thật thì phải thu hồi/rotate; xoá file khỏi HEAD không thu hồi credential. Không tạo hoặc dùng secret thật.

```bash
gitleaks git --config .gitleaks.toml --redact --verbose .
python -m piptools compile --generate-hashes -o requirements.lock requirements.txt
python -m pip install --require-hashes -r requirements.lock
```

Tạo `.pre-commit-config.yaml` dùng hook `gitleaks-system` từ repo chính thức, pin `rev: v8.30.1`, rồi chạy `pre-commit run --all-files`. Kiểm lại `requirements.lock` đã tạo ở preflight: mọi package có hash và `pip install --require-hashes` chạy được. Lần quét lịch sử dự kiến **báo một finding** ở commit token giả; ghi bằng chứng, đừng gọi đó là lỗi bảo mật thật. Quét file hiện tại phải sạch. Trong incident note, giải thích ngắn vì sao pin dependency và hook không thay thế bước rotate khi secret đã lộ.

Hook `gitleaks-system` cần `pass_filenames: false`, vì lệnh `gitleaks git` chỉ nhận một repo path. Dùng `gitleaks dir --config .gitleaks.toml .` để quét file hiện tại; dùng `gitleaks git --config .gitleaks.toml .` để quét lịch sử. Lệnh thứ hai trả exit code 1 khi tìm thấy token giả như dự kiến.

## 5. Prove

Reset sink, chạy `python -m pytest tests/ -q` (test dùng sink riêng), sau đó reset sink **lần nữa** và chạy agent với `--as dpo` trên đúng query/payload ban đầu. Copy `reports/sink.log` thành `reports/attack-after.log`; file phải rỗng. Kiểm `reports/ledger.jsonl` có deny `http_post` với reason và `on_behalf_of`. Viết `reports/compliance-mapping.md` trỏ tới file/dòng evidence thật, gồm Luật 91/2025, NĐ 356/2025, Luật AI 134/2025 và OWASP ASI01/03/04. Viết `reports/dpia-lite.md`: dữ liệu, mục đích, nơi đi, giới hạn của mock. Không khẳng định một điều khoản pháp luật cụ thể nếu chưa đối chiếu văn bản gốc.

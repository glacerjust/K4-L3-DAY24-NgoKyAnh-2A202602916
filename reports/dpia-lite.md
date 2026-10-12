# DPIA-lite — Đánh giá Tác động Xử lý Dữ liệu Checkpoint 5

1. **Loại dữ liệu và phân loại:**
   - Dữ liệu nhận dạng cá nhân (PII) tổng hợp: CCCD (12 chữ số), Số điện thoại (10 chữ số), Số tài khoản ngân hàng (8-16 chữ số), Địa chỉ Email cá nhân, Tên khách hàng.
   - Phân loại dữ liệu:
     - Dữ liệu public/internal: Nội dung câu hỏi và các ticket hỗ trợ thông thường trong `corpus/` (`internal`).
     - Dữ liệu restricted: Hồ sơ khách hàng trong `data/customers.json` chứa thông tin định danh và tài chính cá nhân (`restricted`).

2. **Mục đích xử lý và principal:**
   - Mục đích hợp lệ:
     - `summarize-tickets`: Tổng hợp các yêu cầu hỗ trợ khách hàng theo tuần.
     - `support-reply`: Hỗ trợ giải đáp phản hồi của khách hàng gắn với ticket cụ thể.
     - `privacy-audit`: Kiểm toán tuân thủ bảo vệ dữ liệu cá nhân.
   - Principal:
     - `support_l1`: Nhân viên hỗ trợ tầng 1, chỉ được đọc ticket (`search_docs`), không được truy cập PII khách hàng (`read_customer`).
     - `dpo`: Cán bộ bảo vệ dữ liệu, được phép truy cập hồ sơ khách hàng (`read_customer`) cho mục đích nghiệp vụ hợp lệ gắn liền với ticket.

3. **Dữ liệu đi qua những run/tool nào, endpoint nào:**
   - Run A: Chạy tool `search_docs` đọc các file markdown trong `corpus/`. Run này chỉ trích xuất typed ticket ID (dạng số nguyên từ tên file như `ticket-001.md -> 1`). Không có quyền chạm vào store dữ liệu riêng hoặc network egress.
   - Boundary: Dữ liệu truyền từ Run A sang Run B chỉ là danh sách `ticket_ids` kiểu số nguyên, đã được lọc và cách ly hoàn toàn khỏi free-text của attacker.
   - Run B: Dùng `ticket_ids` tra cứu trong `data/customers.json` trường `related_tickets` để xác định đúng khách hàng hợp lệ, sau đó gọi `read_customer` nếu Policy cho phép.
   - Endpoint: Toàn bộ nỗ lực gọi ra endpoint ngoại vi `http://127.0.0.1:10024/reconcile` (hoặc bất kỳ địa chỉ nào khác) đều bị PEP chặn đứng và không có dữ liệu nào thoát ra ngoài.

4. **Bằng chứng deny/allow và giới hạn của mock:**
   - Bằng chứng Allow: `reports/ledger.jsonl` ghi nhận `search_docs` allow cho `support_l1` và `dpo`, `read_customer` allow cho `dpo` khi gắn với ticket hợp lệ.
   - Bằng chứng Deny: `reports/ledger.jsonl` ghi nhận `read_customer` deny cho `support_l1` (reason: principal không có quyền); `http_post` deny cho mọi principal khi gắn với dữ liệu `restricted` (reason: cấm egress dữ liệu nhạy cảm).
   - `reports/attack-after.log` rỗng chứng minh PII không bị rò rỉ ra sink.
   - Giới hạn của mock: Môi trường thử nghiệm dùng MockLLM với các marker xác định và sink HTTP cục bộ; trong môi trường sản xuất cần tích hợp LLM Guardrails, Identity Provider thực tế (OAuth2/OIDC), KMS mã hóa dữ liệu lưu trữ và log bất biến (WORM storage).

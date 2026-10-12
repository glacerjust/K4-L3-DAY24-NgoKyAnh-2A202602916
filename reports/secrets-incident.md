# Secret giả trong lịch sử Git — Báo cáo Incident Checkpoint 4

- **Scanner và phiên bản:** Gitleaks v8.30.1 (`gitleaks version: 8.30.1`).
- **Commit chứa token giả:** `1bdd849` (commit lịch sử cài cắm synthetic credential phục vụ kiểm thử).
- **File, rule và kết quả quét lịch sử:**
  - Quy tắc phát hiện (Rule ID): `lab24-synthetic-token` (định nghĩa trong [.gitleaks.toml](file:///c:/Users/Admin/Desktop/K4-L3-DAY24-NgoKyAnh-2A202602916/.gitleaks.toml)).
  - Kết quả quét lịch sử bằng lệnh `gitleaks git --config .gitleaks.toml --redact --verbose .`: Báo 1 finding tại commit `1bdd849` khớp với mẫu token giả `LAB24_FAKE_TOKEN=LAB24-DEMO-****************`.
- **Kết quả quét file hiện tại:**
  - Lệnh `gitleaks dir --config .gitleaks.toml .` cho kết quả sạch (0 finding, exit code 0) do file chứa token giả đã được loại bỏ ở commit tiếp theo.
- **Nếu đây là credential thật, cần xử lý thế nào:**
  - Phải ngay lập tức **thu hồi (revoke)** và **rotate** credential trên hệ thống backend / dịch vụ liên quan (Identity Provider / API Gateway).
  - Kiểm tra audit log của token để phát hiện các truy cập bất thường trong khoảng thời gian bị lộ.
  - Xoá triệt để lịch sử git bằng công cụ như `git filter-repo` hoặc BFG Repo-Cleaner nếu cần làm sạch repo, tuy nhiên hành động bắt buộc đầu tiên và quan trọng nhất vẫn là thu hồi/rotate khóa xác thực tại nguồn tin cậy.
- **Vì sao xoá file khỏi HEAD hoặc pin dependency vẫn chưa đủ:**
  - Xoá file khỏi commit HEAD chỉ làm file biến mất ở nhánh làm việc hiện tại, toàn bộ chuỗi commit lịch sử (như commit `1bdd849`) vẫn lưu trữ nguyên vẹn dữ liệu token trong cây git object; bất kỳ ai clone repository đều có thể xem lại lịch sử và trích xuất secret.
  - Pin dependency và pre-commit hook chỉ bảo vệ việc ngăn chặn commit mã độc hoặc secret mới trong tương lai, chứ không thể vô hiệu hóa một credential đã từng bị rò rỉ. Khi secret đã lộ ra ngoài, kẻ tấn công có thể đã lưu lại và sử dụng độc lập với repo; do đó bắt buộc phải **rotate / thu hồi** khóa tại nhà cung cấp danh tính.

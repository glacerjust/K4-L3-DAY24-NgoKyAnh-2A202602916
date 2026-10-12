# Quy tắc làm bài

- Chỉ thử prompt injection trên agent trong repo của chính bạn. Đích `http_post` phải giữ `127.0.0.1:10024`.
- Chỉ dùng dữ liệu tổng hợp trong `corpus/`, `data/` và token giả có định dạng `LAB24-DEMO`. Không đưa credential hay PII thật vào repo, prompt, log hoặc báo cáo.
- Có thể dùng AI để tìm hiểu và hỗ trợ code; bạn phải giải thích được từng control, chỉ ra bằng chứng và tự chạy test. Không nhận bài giải của người khác làm bài của mình.
- Không sửa test bắt buộc để tạo điểm đỗ giả. Không dùng `--no-verify` để bỏ qua hook khi nộp. Nếu công cụ báo lỗi, ghi lỗi và điều kiện tái hiện vào `reports/verification.md`.
- `--as` chỉ chọn principal **giả lập** trong lab; không được mô tả nó là cơ chế xác thực production. Ledger hash chain là bằng chứng phát hiện sửa đổi trong file, không phải log bất biến chống mọi đối thủ.
- Tài liệu pháp lý trong báo cáo phải ghi văn bản/điều khoản đã đối chiếu với nguồn chính thức. Nếu chưa kiểm được, ghi `chưa xác minh`.
- Bài cá nhân. Quy định nộp muộn, chỉnh bài sau deadline và cách dùng AI cuối cùng theo thông báo của key coach/TA.

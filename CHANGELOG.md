# Nhật ký thay đổi

## 2.4.0 — 2026-10-17
- Mục **📅 Lịch KG–BG**: kéo thả file lịch khai giảng – bế giảng (vd `KG-BG_OTO.xlsx`) → xem trước từng dòng (khóa mới / đổi ngày / không đổi / đã đóng sổ), ghép tên khóa → mã hạng (tự tạo hạng nâng hạng NH…), tự phát hiện ngày nhập sai (BG trước KG, độ dài lệch nhiều, lệch năm) và không tự chọn các dòng đó; sửa ngày ngay trong bảng.
- **Tiến độ hồ sơ** mỗi khóa: ① Đã nhập đủ thông tin học viên → ② Đã nhập ảnh → Đã chốt hồ sơ (ghi thời điểm, ghi chú, bỏ xác nhận phải ghi lý do, lưu nhật ký).
- **Nhắc trước 1–5 ngày** (chọn được) cho khóa sắp khai giảng chưa chốt hồ sơ: Tổng quan, nút đỏ trên thanh trên cùng, số đếm ở menu, thông báo trên máy tính (1 lần/ngày); mức Chuẩn bị / Sắp đến / GẤP / QUÁ HẠN. Chỉ theo dõi khóa khai giảng từ ngày bật tính năng (đổi được).
- Lịch tháng (khai giảng/bế giảng), cột Hồ sơ ①② trong danh sách khóa, xuất Excel lịch.

## 2.3.0 — 2026-10-17
- Bộ cài Windows `QLKhoaOto_Setup_<phiên bản>.exe` (Inno Setup, cài theo người dùng, không cần Admin, không cần Python) + bản portable zip. Dựng tự động bằng GitHub Actions mỗi khi `version.json` đổi trên `main` (hoặc khi đẩy tag `v*`), tự tạo tag + đăng ở Releases.
- `QLKhoaOto.exe` chạy `server.py` nằm cạnh nên vẫn tự cập nhật từ GitHub; khởi động lại sau cập nhật hoạt động với bản .exe.

## 2.2.0 — 2026-10-16
- Liên kết kho GitHub `HP-wukoong/QUAN_LY_KHOA_OTO_CSHN`: mục **Hướng dẫn → Cập nhật phần mềm** kiểm tra & cập nhật 1 bấm (kiểm SHA-256, tự sao lưu dữ liệu, giữ bản chương trình cũ ở `backups/ban-cu`, khởi động lại tự động). Mỗi ngày tự kiểm tra 1 lần, có bản mới thì báo ở Tổng quan.
- Truy xuất đường dẫn sao lưu: bảng đường dẫn đầy đủ (thư mục tool, file dữ liệu, thư mục sao lưu chính/hằng ngày/tháng/Excel/trước khôi phục, thư mục phụ, cài đặt, nhật ký) với nút 📋 chép và 📂 mở trong File Explorer.
- Danh sách bản sao lưu hiện đường dẫn đầy đủ từng file, lọc theo loại/tên, nút 🔍 nhận dạng file (ID bản cài, toàn vẹn, thời điểm, số khóa/HV).
- Tên file sao lưu có mã đơn vị: `QLKhoaOto-CSHN_2026-10-16.db`; mỗi thư mục sao lưu có `_THONG_TIN_SAO_LUU.txt`; thư mục phụ đổi thành `QLKhoaOto_SaoLuu_<mã>`.
- Cấu hình được mã đơn vị và thư mục sao lưu chính.

## 2.1.0 — 2026-10-14
- Chọn 1 hoặc nhiều khóa, thao tác hàng loạt: dùng mã 52003 cho khóa cũ (chỉ khóa được chọn, hoàn tác được), đóng/mở sổ, xuất Excel nhiều khóa, xóa. Lọc theo tình trạng mã.

## 2.0.0 — 2026-10-12
- Chuyển sang máy chủ Python + SQLite: phiên bản, nhật ký thay đổi, sao lưu tự động, kiểm tra khôi phục, PIN, dùng chung mạng nội bộ có gộp dữ liệu, đóng sổ, thùng rác, trạng thái HV, học phí, nạp SĐT, kiểm tra dữ liệu, đối chiếu mã ĐKI, báo cáo, in danh sách, xuất cho sổ nhật ký/DAT.

## 1.x
- Bản 1 file HTML.

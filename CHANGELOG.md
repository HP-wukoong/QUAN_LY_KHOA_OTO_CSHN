# Nhật ký thay đổi

## 2.6.1 — 2026-11-27
- Máy khác truy cập qua mạng ở **chế độ chỉ xem** (mặc định): xem, tìm, lọc, chọn hàng loạt, xuất Excel / in, copy thông báo Zalo bình thường; không sửa, xóa, nạp file, tick hồ sơ. Máy chủ chặn cả ở phía máy chủ (403). Góc trên hiện "👁 Chế độ chỉ xem".
- Máy chủ chọn được quyền cho máy khác ở mục Dùng chung qua mạng: **Chỉ xem** hoặc **Được sửa**.

## 2.6.0 — 2026-11-27
- Mục **💽 Bộ nhớ**: biểu đồ tròn dung lượng tool theo từng phần, thanh dung lượng ổ đĩa (tool / file khác / còn trống, cảnh báo khi còn < 2 GB), chi tiết bên trong file dữ liệu (dữ liệu hiện tại, lịch sử phiên bản, nhật ký thay đổi, chỗ trống), các nút dọn an toàn (sao lưu quá hạn, phiên bản cũ, nhật ký cũ, thu gọn file dữ liệu, bản chương trình cũ, nhật ký máy chủ).
- Mục **🔄 Cập nhật**: bật/tắt **tự động cập nhật** — tự kiểm tra GitHub mỗi 3 giờ và mỗi lần **bấm F5**; có bản mới thì sao lưu → tải (kiểm tra mã SHA-256) → cài → khởi động lại. Các máy/tab đang mở thấy dòng "Đã cập nhật — bấm F5".

## 2.5.4 — 2026-11-27
- **Dùng chung qua mạng nội bộ (LAN)**: mục riêng trong Sao lưu & Cài đặt, làm theo 4 bước có đánh dấu ✓ (PIN → bật → khởi động lại 1 nút → mở cổng tường lửa Windows tự động qua hộp thoại quyền quản trị).
- Hiện mọi địa chỉ cho máy khác (theo IP và theo tên máy), nút Copy, **Tải lối tắt** (.url) để chép sang Desktop máy khác; mục "Máy khác không vào được?".
- Máy khác mở tool thấy rõ đang dùng chung dữ liệu với máy chủ.

## 2.5.3 — 2026-10-19
- Thông báo Zalo thêm loại **🎓 Bế giảng**: các khóa sắp bế giảng (mặc định 15 ngày tới), đề nghị Quý thầy chuẩn bị bài kiểm tra trả nợ môn, sổ nhiên liệu, sổ tay giáo viên, giáo án, sổ nhật ký giảng dạy, đủ giờ/km DAT — **danh sách và lời nhắn sửa được**. Có ảnh (tông xanh lá, mũ tốt nghiệp) + chữ Sinh động / Gọn; nút copy nhanh ở Tổng quan.
- Bỏ chữ "hihi" trong thông báo khai giảng.

## 2.5.2 — 2026-10-19
- Thông báo Zalo: xưng "Quý thầy", thêm biểu tượng rưng rưng 🥹 "hihi".
- Thùng rác: chọn hàng loạt (tick / Chọn tất cả / giữ Shift chọn cả đoạn), lọc theo loại + tìm kiếm, khôi phục hoặc xóa hẳn hàng loạt, nút Dọn sạch thùng rác.

## 2.5.1 — 2026-10-19
- Thông báo Zalo: **khung thông báo dạng ảnh** (Copy ảnh / Tải PNG) màu theo mức gấp; nội dung chữ 2 kiểu **Sinh động** / **Gọn** theo mẫu `Bss-23 : KG Chủ nhật _ 25/10/2026 – còn 6 ngày`; sửa được tên hạng hiển thị (Bss, Bstđ, CE…).
- Sao lưu & Cài đặt: thêm dấu **!** giải thích từng mục (rê chuột / bấm để xem).

## 2.5.0 — 2026-10-19
- **Nhắc nhập máy thi tốt nghiệp** trước ngày bế giảng 1–5 ngày làm việc; tick "🎓 Đã nhập máy thi TN" từng khóa (Tổng quan, Lịch › Sắp bế giảng, trang khóa).
- **Thông báo Zalo** nhắc giáo viên nộp hồ sơ: các khóa ô tô khai giảng trong 15 ngày tới, có số ngày còn lại, sửa được, bấm Copy dán vào Zalo.
- **Tính theo ngày làm việc**: bỏ T7, CN, ngày lễ (có sẵn lịch lễ 2026–2028, sửa được ở "📆 Ngày lễ"). Khóa KG/BG rơi vào ngày nghỉ hoặc ngay sau kỳ nghỉ được nhắc sớm hơn và ghi rõ hạn nộp.
- **Sao lưu giữ 15 ngày làm việc gần nhất**, cũ hơn tự xóa (luôn giữ tối thiểu 5 bản mới nhất; bản theo tháng giữ 12 tháng).

## 2.4.1 — 2026-10-17
- Sửa lỗi bản cài mới không nạp được dữ liệu cũ:
  - Nạp trực tiếp file `.db` (data\qlkhoa.db, backups\…\QLKhoaOto-*.db) và `.json` (chịu BOM, báo rõ khi chọn nhầm file _meta.json).
  - Nút **🔎 Tìm dữ liệu cũ trên máy**: tự quét Desktop/Documents/Downloads và các ổ D:, E:…, đọc cả phần dữ liệu trong file -wal.
  - Trang Tổng quan khi dữ liệu trống hiện gợi ý tìm & nạp dữ liệu cũ.

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

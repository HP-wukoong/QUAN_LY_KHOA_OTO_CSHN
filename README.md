# QUẢN LÝ KHÓA Ô TÔ — CSHN

Công cụ quản lý khóa đào tạo lái xe ô tô (hạng **B số sàn, B số tự động, C1**) cho Cơ sở Hoài Nhơn, thay file Excel `QUAN_LY_KHOA_DAO_TAO.xlsm`.
Chạy **offline trên máy Windows** bằng Python 3.11 (chỉ thư viện chuẩn, không cần cài thêm gì), giao diện mở bằng trình duyệt.

> ⚠️ **Kho này chỉ chứa mã chương trình.** Dữ liệu học viên (CCCD, ngày sinh, địa chỉ…) nằm ở `QLKhoaOto/data/` và `QLKhoaOto/backups/` trên máy dùng — đã chặn trong `.gitignore`, **không bao giờ commit lên GitHub.**

## ⬇ Tải bộ cài
**[QLKhoaOto_Setup.exe — bản mới nhất](https://github.com/HP-wukoong/QUAN_LY_KHOA_OTO_CSHN/releases/latest)** → chạy → Next → xong.
Không cần cài Python, không cần quyền Admin. Có biểu tượng Desktop/Start Menu, gỡ trong *Settings → Apps*. Gỡ cài đặt **không xóa** dữ liệu.
Đã dùng bản cũ ở thư mục khác (vd `D:\QLKhoaOto`)? Khi cài, chọn đúng thư mục đó để giữ nguyên dữ liệu.

## Cài đặt thủ công (máy đã có Python 3.11)
1. Cài Python 3.11 (python.org, tick *Add python.exe to PATH*).
2. Tải thư mục `QLKhoaOto/` (nút **Code → Download ZIP**, lấy riêng thư mục này) và đặt vào ổ máy, vd `D:\QLKhoaOto` — **không** đặt trong Google Drive/OneDrive.
3. Bấm đúp `TAO_LOI_TAT_DESKTOP.bat` (1 lần), sau đó mở tool bằng `CHAY_TOOL.bat` hoặc lối tắt ngoài Desktop.
4. Xem `QLKhoaOto/DOC_TRUOC_HUONG_DAN.txt`.

## Cập nhật
Trong tool: **Hướng dẫn → Cập nhật phần mềm từ GitHub → Kiểm tra cập nhật → Cập nhật**.
Tool tải các file liệt kê trong `version.json`, kiểm tra SHA-256, tự sao lưu dữ liệu, giữ bản chương trình cũ trong `backups/ban-cu/`, rồi khởi động lại.
Kho để **riêng tư** thì cần nhập token (quyền đọc nội dung) trong phần *Cài đặt kho GitHub*.

## Cấu trúc kho
| Đường dẫn | Nội dung |
|---|---|
| `QLKhoaOto/` | Bản phát hành: `app.html` (đã nhúng thư viện), `server.py`, các file `.bat`, hướng dẫn |
| `src/app.src.html` | Mã nguồn giao diện (chưa nhúng thư viện) |
| `vendor/` | SheetJS 0.18.5 (Apache-2.0), ExcelJS 4.4.0 (MIT) |
| `tools/build_release.py` | Dựng `QLKhoaOto/app.html` + ghi `version.json` |
| `version.json` | Phiên bản mới nhất + SHA-256 từng file — tool đọc để tự cập nhật |
| `CHANGELOG.md` | Nhật ký thay đổi |

## Phát hành bản mới
1. Sửa `src/app.src.html` / `QLKhoaOto/server.py`; tăng `TOOL_VERSION` (app) và `VERSION` (server.py) **giống nhau**; thêm dòng vào `CHANGELOG` trong app và `CHANGELOG.md`.
2. `python tools/build_release.py "Ghi chú ngắn"` (thêm `--zip` nếu cần file gửi máy mới).
3. Commit & push lên `main` — các máy đang dùng sẽ thấy thông báo cập nhật trong ngày.

## Dữ liệu & sao lưu (trên máy dùng)
- Dữ liệu: `QLKhoaOto/data/qlkhoa.db` (SQLite). Mỗi lần lưu là 1 phiên bản; nhật ký thay đổi từng học viên.
- Sao lưu tự động: `backups/hang-ngay` (bản đầu ngày + mới nhất), `backups/theo-thang`, `backups/excel`, `backups/truoc-khi-khoi-phuc`; tên file có mã đơn vị, vd `QLKhoaOto-CSHN_2026-10-16.db`; mỗi thư mục có `_THONG_TIN_SAO_LUU.txt`.
- Thư mục sao lưu phụ (Drive/USB), mã đơn vị, thư mục sao lưu chính: cài trong **Sao lưu & Cài đặt** (bảng *Đường dẫn dữ liệu & sao lưu* có nút chép / mở thư mục).

# -*- coding: utf-8 -*-
"""
Đóng gói bản phát hành:
  1. Dựng QLKhoaOto/app.html = src/app.src.html + thư viện trong vendor/ (nhúng sẵn, chạy offline)
  2. Kiểm tra VERSION trong server.py khớp TOOL_VERSION trong app
  3. Ghi version.json (phiên bản, ngày, ghi chú, SHA-256 từng file) — tool dùng file này để tự cập nhật
  4. (tùy chọn) --zip : tạo dist/QLKhoaOto_v<x.y.z>.zip để gửi người dùng mới
Chạy:  python tools/build_release.py "Ghi chú phiên bản" [--zip]
"""
import datetime, hashlib, json, os, re, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "QLKhoaOto")
FILES = ["app.html", "server.py", "CHAY_TOOL.bat", "TAO_LOI_TAT_DESKTOP.bat", "DOC_TRUOC_HUONG_DAN.txt"]


def main():
    src = open(os.path.join(ROOT, "src", "app.src.html"), encoding="utf-8").read()
    libs = ""
    for f in ("xlsx.full.min.js", "exceljs.min.js"):
        js = open(os.path.join(ROOT, "vendor", f), encoding="utf-8").read().replace("</script", "<\\/script")
        libs += "<script>" + js + "</script>\n"
    assert "<!--__LIBS__-->" in src, "thiếu chỗ nhúng thư viện"
    with open(os.path.join(APP, "app.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(src.replace("<!--__LIBS__-->", libs))
    sv = re.search(r'^VERSION = "([\d.]+)"', open(os.path.join(APP, "server.py"), encoding="utf-8").read(), re.M).group(1)
    av = re.search(r"TOOL_VERSION = '([\d.]+)'", src).group(1)
    if sv != av:
        sys.exit(f"Lệch phiên bản: server.py {sv} ≠ app {av}")
    notes = next((a for a in sys.argv[1:] if not a.startswith("--")), "")
    info = {"version": sv, "date": datetime.date.today().isoformat(), "notes": notes,
            "files": {n: hashlib.sha256(open(os.path.join(APP, n), "rb").read()).hexdigest() for n in FILES}}
    with open(os.path.join(ROOT, "version.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    print("version.json:", sv, "·", len(info["files"]), "file")
    if "--zip" in sys.argv:
        os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
        zp = os.path.join(ROOT, "dist", f"QLKhoaOto_v{sv}.zip")
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
            for n in FILES:
                z.write(os.path.join(APP, n), "QLKhoaOto/" + n)
        print("zip:", zp)


if __name__ == "__main__":
    main()

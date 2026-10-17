# -*- coding: utf-8 -*-
"""QLKhoaOto.exe — chạy server.py nằm cạnh file .exe bằng Python nhúng sẵn (máy dùng không cần cài Python).
server.py / app.html để NGOÀI exe nên tool vẫn tự cập nhật được từ GitHub."""
import os
import runpy
import sys

# Các module server.py dùng — import ở đây để PyInstaller đóng gói kèm
import copy, datetime, gzip, hashlib, hmac, json, re, secrets, shutil, socket, sqlite3, subprocess  # noqa: E401,F401
import threading, time, traceback, urllib.error, urllib.parse, urllib.request, webbrowser  # noqa: E401,F401
import http.server  # noqa: F401

BASE = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
SRV = os.path.join(BASE, "server.py")


def main():
    if not os.path.exists(SRV):
        print("Không thấy server.py trong", BASE)
        print("Cài lại bằng QLKhoaOto_Setup.exe.")
        input("Nhấn Enter để đóng…")
        return
    os.chdir(BASE)
    sys.argv = [SRV] + sys.argv[1:]
    try:
        runpy.run_path(SRV, run_name="__main__")
    except SystemExit:
        raise
    except Exception:
        import traceback as tb
        tb.print_exc()
        input("Tool dừng do lỗi (chi tiết ở trên và trong data\\server.log). Nhấn Enter để đóng…")


if __name__ == "__main__":
    main()

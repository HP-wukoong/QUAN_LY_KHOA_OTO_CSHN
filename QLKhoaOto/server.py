# -*- coding: utf-8 -*-
"""
QUẢN LÝ KHÓA Ô TÔ CSHN — máy chủ cục bộ
- Chỉ dùng thư viện chuẩn của Python 3.11 (không cần pip).
- Dữ liệu: data/qlkhoa.db (SQLite). Sao lưu: backups/ (+ các thư mục phụ trong config.json).
- Mở: chạy CHAY_TOOL.bat → trình duyệt tự mở http://127.0.0.1:<cổng>
"""
import copy
import datetime as dt
import gzip
import hashlib
import hmac
import json
import os
import secrets
import shutil
import socket
import sqlite3
import sys
import threading
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "2.4.0"
APP_ID = "QLKhoaOtoCSHN"
BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "data")
BK_DIR = os.path.join(BASE, "backups")
DB_PATH = os.path.join(DATA_DIR, "qlkhoa.db")
CFG_PATH = os.path.join(BASE, "config.json")
LOG_PATH = os.path.join(DATA_DIR, "server.log")
HTML_PATH = os.path.join(BASE, "app.html")

DEFAULT_CFG = {
    "port": 8686,
    "cho_phep_mang_noi_bo": False,   # True: máy khác trong mạng LAN truy cập được (bắt buộc đặt PIN)
    "thu_muc_sao_luu_phu": [],       # vd ["G:\\My Drive\\SaoLuu", "E:\\"] — chép thêm bản sao lưu ra đây
    "giu_ban_hang_ngay": 90,
    "giu_ban_theo_thang": 36,
    "giu_so_phien_ban": 400,
    "giu_phien_ban_ngay": 45,
    "khoa_man_hinh_sau_phut": 30,
    "tu_mo_trinh_duyet": True,
    "ma_don_vi": "CSHN",            # có trong tên mọi file sao lưu → không lẫn với file khác
    "thu_muc_sao_luu": "",          # để trống = <thư mục tool>\backups
    "github_repo": "HP-wukoong/QUAN_LY_KHOA_OTO_CSHN",
    "github_branch": "main",
    "github_token": "",             # chỉ cần nếu kho GitHub để riêng tư
}

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BK_DIR, exist_ok=True)
WRITE_LOCK = threading.RLock()


def now_iso():
    return dt.datetime.now().isoformat(timespec="seconds")


def log(msg):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{now_iso()} {msg}\n")
    except Exception:
        pass


def load_cfg():
    cfg = dict(DEFAULT_CFG)
    if os.path.exists(CFG_PATH):
        try:
            with open(CFG_PATH, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception as e:
            log(f"config.json lỗi, dùng mặc định: {e}")
    return cfg


def save_cfg(cfg):
    tmp = CFG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CFG_PATH)


CFG = load_cfg()
if not os.path.exists(CFG_PATH):
    save_cfg(CFG)


# ---------------------------------------------------------------- SQLite
def connect(path=DB_PATH, ro=False):
    if ro:
        con = sqlite3.connect(f"file:{urllib.parse.quote(path)}?mode=ro", uri=True, timeout=30)
    else:
        con = sqlite3.connect(path, timeout=30)
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=FULL")
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = connect()
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);
        CREATE TABLE IF NOT EXISTS state(id INTEGER PRIMARY KEY CHECK(id=1), rev INTEGER NOT NULL, saved_at TEXT, json TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS revs(rev INTEGER PRIMARY KEY, saved_at TEXT, device TEXT, nk INTEGER, nh INTEGER, reason TEXT, gz BLOB);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT, t TEXT, rev INTEGER, device TEXT,
            entity TEXT, eid TEXT, label TEXT, action TEXT, field TEXT, old TEXT, new TEXT);
        CREATE INDEX IF NOT EXISTS audit_eid ON audit(eid);
        CREATE INDEX IF NOT EXISTS audit_t ON audit(t);
        """
    )
    if not con.execute("SELECT 1 FROM state WHERE id=1").fetchone():
        con.execute("INSERT INTO state(id, rev, saved_at, json) VALUES(1, 0, '', '')")
    con.commit()
    con.close()


def meta_get(con, k, default=None):
    r = con.execute("SELECT v FROM meta WHERE k=?", (k,)).fetchone()
    return json.loads(r["v"]) if r else default


def meta_set(con, k, v):
    con.execute("INSERT INTO meta(k, v) VALUES(?, ?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (k, json.dumps(v, ensure_ascii=False)))


def read_state(con=None):
    own = con is None
    con = con or connect()
    r = con.execute("SELECT rev, saved_at, json FROM state WHERE id=1").fetchone()
    if own:
        con.close()
    data = json.loads(r["json"]) if r["json"] else None
    return r["rev"], r["saved_at"], data


# ---------------------------------------------------------------- Gộp 3 chiều & nhật ký
ID_COLL = ("khoa", "hv", "gv", "trash")
KEY_COLL = ("madk", "drafts")
NOISY = {"uses", "order", "_id"}


def _idx(lst):
    return {x["id"]: x for x in (lst or []) if isinstance(x, dict) and "id" in x}


class BaseMissing(Exception):
    pass


def _merge_list_by_id(bl, ml, cl):
    """Gộp mảng con có id (vd các lần thu học phí)."""
    if not all(isinstance(x, dict) and "id" in x for x in (bl or []) + (ml or []) + (cl or [])):
        return ml
    b, m, c = _idx(bl), _idx(ml), _idx(cl)
    order = [x["id"] for x in cl or []]
    for i, r in m.items():
        if i not in b or b[i] != r:
            if i not in c:
                order.append(i)
            c[i] = r
    for i in b:
        if i not in m:
            c.pop(i, None)
    return [c[i] for i in order if i in c]


def _merge_rec(b, m, c):
    """Gộp TỪNG TRƯỜNG: trường nào máy gửi đã đổi so với gốc thì lấy của máy gửi, còn lại giữ bản đang có."""
    out = dict(c)
    for f in set(b) | set(m):
        if m.get(f) == b.get(f):
            continue
        if isinstance(m.get(f), list) and isinstance(c.get(f), list):
            out[f] = _merge_list_by_id(b.get(f) or [], m.get(f), c.get(f))
        elif f in m:
            out[f] = m[f]
        else:
            out.pop(f, None)
    return out


def merge3(base, mine, cur):
    """Áp các thay đổi của máy gửi (base→mine) lên bản hiện có (cur): theo từng bản ghi, từng trường."""
    out = copy.deepcopy(cur)
    conflicts = []
    trash_ids = {t.get("data", {}).get("id") for t in cur.get("trash") or [] if isinstance(t, dict)}
    for t in cur.get("trash") or []:
        for h in t.get("hvs") or []:
            trash_ids.add(h.get("id"))
    for c in ID_COLL:
        b, m, cu = _idx(base.get(c)), _idx(mine.get(c)), _idx(cur.get(c))
        order = [x["id"] for x in cur.get(c) or [] if isinstance(x, dict) and "id" in x]
        for i, rec in m.items():
            if i not in b:                      # máy gửi thêm mới
                if i not in cu:
                    if c != "trash" and i in trash_ids:
                        continue
                    order.append(i)
                    cu[i] = rec
                else:
                    cu[i] = _merge_rec({}, rec, cu[i])
            elif b[i] != rec:                    # máy gửi sửa
                if i not in cu:                  # máy khác đã xóa (nằm trong thùng rác) → không cho sống lại
                    conflicts.append((c, i, _label(c, rec), "sua-ban-ghi-da-xoa"))
                    continue
                cu[i] = _merge_rec(b[i], rec, cu[i])
        for i in b:
            if i not in m and i in cu:           # máy gửi xóa
                if cu[i] != b[i] and c != "trash":
                    conflicts.append((c, i, _label(c, cu[i]), "giu-lai-vi-may-khac-vua-sua"))
                    continue
                cu.pop(i, None)
        out[c] = [cu[i] for i in order if i in cu]
    for c in KEY_COLL:
        b, m, cu = base.get(c) or {}, mine.get(c) or {}, dict(cur.get(c) or {})
        for k, v in m.items():
            if k not in b or b[k] != v:
                cu[k] = v
        for k in b:
            if k not in m:
                cu.pop(k, None)
        out[c] = cu
    bs, ms = base.get("settings") or {}, mine.get("settings") or {}
    out["settings"] = dict(cur.get("settings") or {})
    for k, v in ms.items():
        if bs.get(k) != v:
            out["settings"][k] = v
    if mine.get("hang") != base.get("hang"):
        out["hang"] = mine.get("hang")
    # học viên mồ côi (khóa đã bị xóa ở máy khác) → thùng rác
    kids = {k["id"] for k in out.get("khoa") or []}
    orphans = [h for h in out.get("hv") or [] if h.get("khoaId") not in kids]
    if orphans:
        out["hv"] = [h for h in out["hv"] if h.get("khoaId") in kids]
        out.setdefault("trash", [])
        for h in orphans:
            out["trash"].insert(0, {"id": secrets.token_hex(6), "type": "hv", "at": dt.datetime.utcnow().isoformat() + "Z", "label": h.get("hoTen", "") + " (khóa đã xóa)",
                                    "reason": "Khóa bị xóa ở máy khác khi máy này đang sửa", "data": h, "hvs": []})
    seen = {(x.get("t"), x.get("msg")) for x in base.get("log") or []}
    newlog = [x for x in mine.get("log") or [] if (x.get("t"), x.get("msg")) not in seen]
    out["log"] = (newlog + list(cur.get("log") or []))[:600]
    return out, conflicts


def _label(c, rec):
    if c == "hv":
        return rec.get("hoTen", "")
    if c == "khoa":
        try:
            return f"{rec.get('hang')}-{int(rec.get('so')):02d}"
        except Exception:
            return str(rec.get("hang"))
    if c == "gv":
        return rec.get("hoTen", "")
    if c == "trash":
        return rec.get("label", "")
    return ""


def _short(v):
    if v is None:
        return ""
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return s if len(s) <= 400 else s[:400] + "…"


def diff_audit(old, new):
    rows = []
    for c in ("khoa", "hv", "gv"):
        o, n = _idx(old.get(c)), _idx(new.get(c))
        for i, rec in n.items():
            if i not in o:
                rows.append((c, i, _label(c, rec), "them", "", "", ""))
            else:
                orec = o[i]
                for f in sorted(set(orec) | set(rec)):
                    if f in NOISY:
                        continue
                    if orec.get(f) != rec.get(f):
                        rows.append((c, i, _label(c, rec), "sua", f, _short(orec.get(f)), _short(rec.get(f))))
        for i, rec in o.items():
            if i not in n:
                rows.append((c, i, _label(c, rec), "xoa", "", "", ""))
    om, nm = old.get("madk") or {}, new.get("madk") or {}
    add = sum(1 for k in nm if k not in om)
    chg = sum(1 for k in nm if k in om and nm[k].get("maDK") != om[k].get("maDK"))
    if add or chg:
        rows.append(("madk", "", "Kho mã ĐKI", "sua", "maDK", "", f"+{add} mã mới, {chg} mã đổi"))
    return rows


def save_state(data, base_rev, device, reason=""):
    """Lưu có kiểm soát phiên bản. Trả về (rev, saved_at, merged_data|None)."""
    with WRITE_LOCK:
        con = connect()
        try:
            cur_rev, _, cur = read_state(con)
            merged = None
            conflicts = []
            if cur is not None and base_rev != cur_rev:
                b = con.execute("SELECT gz FROM revs WHERE rev=?", (base_rev,)).fetchone()
                if not b:
                    # Không còn bản gốc để so → KHÔNG được đoán, trả lỗi để máy gửi tải lại
                    raise BaseMissing(cur_rev)
                base = json.loads(gzip.decompress(b["gz"]))
                data, conflicts = merge3(base, data, cur)
                merged = data
                reason = (reason + " " if reason else "") + f"(gộp với rev {cur_rev})"
            rev = cur_rev + 1
            saved_at = now_iso()
            data["rev"] = rev
            data["savedAt"] = saved_at
            txt = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            con.execute("BEGIN IMMEDIATE")
            con.execute("UPDATE state SET rev=?, saved_at=?, json=? WHERE id=1", (rev, saved_at, txt))
            con.execute(
                "INSERT INTO revs(rev, saved_at, device, nk, nh, reason, gz) VALUES(?,?,?,?,?,?,?)",
                (rev, saved_at, device, len(data.get("khoa") or []), len(data.get("hv") or []), reason, gzip.compress(txt.encode("utf-8"), 6)),
            )
            for (c, i, lb, why) in conflicts:
                con.execute("INSERT INTO audit(t, rev, device, entity, eid, label, action, field, old, new) VALUES(?,?,?,?,?,?,?,?,?,?)",
                            (saved_at, rev, device, c, i, lb, "xung-dot", "", "", why))
            if cur is not None:
                for r in diff_audit(cur, data):
                    con.execute(
                        "INSERT INTO audit(t, rev, device, entity, eid, label, action, field, old, new) VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (saved_at, rev, device) + r,
                    )
            keep = int(CFG.get("giu_so_phien_ban", 400))
            old = (dt.datetime.now() - dt.timedelta(days=int(CFG.get("giu_phien_ban_ngay", 45)))).isoformat(timespec="seconds")
            con.execute("DELETE FROM revs WHERE rev <= ? AND saved_at < ?", (rev - keep, old))
            con.commit()
            return rev, saved_at, merged
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()


# ---------------------------------------------------------------- Sao lưu
def bk_root():
    """Thư mục sao lưu chính: config 'thu_muc_sao_luu' (để trống = <thư mục tool>\\backups)."""
    r = (CFG.get("thu_muc_sao_luu") or "").strip()
    return os.path.abspath(r) if r else BK_DIR


def ma_dv():
    s = "".join(ch for ch in str(CFG.get("ma_don_vi") or "CSHN").upper() if ch.isalnum() or ch in "-_")
    return s or "CSHN"


def bk_name(tail):
    """Tên file sao lưu luôn có mã đơn vị để không lẫn với file khác: QLKhoaOto-CSHN_2026-10-16.db"""
    return f"QLKhoaOto-{ma_dv()}_{tail}"


DATE_RE = __import__("re").compile(r"(\d{4}-\d{2}-\d{2})")


def instance_id():
    con = connect()
    iid = meta_get(con, "instance_id")
    if not iid:
        iid = f"{ma_dv()}-{secrets.token_hex(4).upper()}"
        meta_set(con, "instance_id", iid)
        con.commit()
    con.close()
    return iid


def _bk_paths():
    root = bk_root()
    d = os.path.join(root, "hang-ngay")
    m = os.path.join(root, "theo-thang")
    x = os.path.join(root, "excel")
    p = os.path.join(root, "truoc-khi-khoi-phuc")
    for q in (d, m, x, p):
        os.makedirs(q, exist_ok=True)
    return d, m, x, p


def write_info_file(folder):
    """File nhận dạng đặt cạnh các bản sao lưu: của tool nào, đơn vị nào, máy nào, dữ liệu gốc ở đâu."""
    try:
        txt = (f"THƯ MỤC SAO LƯU — QUẢN LÝ KHÓA Ô TÔ ({APP_ID})\r\n"
               f"Mã đơn vị        : {ma_dv()}\r\n"
               f"Mã bản cài (ID)  : {instance_id()}\r\n"
               f"Máy tính         : {socket.gethostname()}\r\n"
               f"Thư mục tool     : {BASE}\r\n"
               f"File dữ liệu gốc : {DB_PATH}\r\n"
               f"Cập nhật lúc     : {now_iso()}\r\n\r\n"
               "Các file .db ở đây là bản sao lưu đầy đủ (mở được bằng tool: Sao lưu & Cài đặt → Khôi phục).\r\n"
               "Tên file: QLKhoaOto-<mã đơn vị>_<ngày>.db ; _dau-ngay = bản đầu ngày ; theo-thang = 1 bản/tháng.\r\n"
               "ĐỪNG sửa/xóa tay. File có mã đơn vị hoặc ID khác là của bản cài khác.\r\n")
        with open(os.path.join(folder, "_THONG_TIN_SAO_LUU.txt"), "w", encoding="utf-8-sig") as f:
            f.write(txt)
    except Exception as e:
        log("write_info_file: " + repr(e))


def sqlite_copy(dst):
    tmp = dst + ".tmp"
    src = connect()
    out = sqlite3.connect(tmp)
    with out:
        src.backup(out)
    out.execute("PRAGMA journal_mode=DELETE")
    out.close()
    src.close()
    os.replace(tmp, dst)


def extra_target(root, sub=""):
    return os.path.join(root, f"QLKhoaOto_SaoLuu_{ma_dv()}", sub) if sub else os.path.join(root, f"QLKhoaOto_SaoLuu_{ma_dv()}")


def copy_to_extra(path, sub):
    res = []
    for root in CFG.get("thu_muc_sao_luu_phu") or []:
        try:
            if not root or not os.path.isdir(root):
                res.append({"dir": root, "ok": False, "err": "không thấy thư mục (USB/Drive chưa cắm?)"})
                continue
            tgt = extra_target(root, sub)
            os.makedirs(tgt, exist_ok=True)
            write_info_file(extra_target(root))
            dst = os.path.join(tgt, os.path.basename(path))
            shutil.copy2(path, dst)
            res.append({"dir": root, "ok": True, "path": dst})
        except Exception as e:
            res.append({"dir": root, "ok": False, "err": str(e)})
    return res


def do_backup(force=False):
    with WRITE_LOCK:
        d, m, _, _ = _bk_paths()
        con = connect()
        rev = con.execute("SELECT rev FROM state WHERE id=1").fetchone()["rev"]
        last = meta_get(con, "last_backup", {}) or {}
        con.close()
        today = dt.date.today().isoformat()
        month = today[:7]
        made = []
        if rev == 0 and not force:
            return {"skipped": "chưa có dữ liệu"}
        write_info_file(bk_root())
        first = os.path.join(d, bk_name(f"{today}_dau-ngay.db"))
        if not os.path.exists(first):
            sqlite_copy(first)
            made.append(first)
        cur = os.path.join(d, bk_name(f"{today}.db"))
        if force or last.get("rev") != rev or not os.path.exists(cur):
            sqlite_copy(cur)
            made.append(cur)
        mon = os.path.join(m, bk_name(f"{month}.db"))
        if not os.path.exists(mon):
            sqlite_copy(mon)
            made.append(mon)
        extra = []
        for f in made:
            extra = copy_to_extra(f, "theo-thang" if f.startswith(m) else "hang-ngay")
        # dọn bản cũ (chỉ file của tool: QLKhoaOto*.db)
        lim = (dt.date.today() - dt.timedelta(days=int(CFG.get("giu_ban_hang_ngay", 90)))).isoformat()
        for n in os.listdir(d):
            g = DATE_RE.search(n)
            if n.startswith("QLKhoaOto") and n.endswith(".db") and g and g.group(1) < lim:
                try:
                    os.remove(os.path.join(d, n))
                except Exception:
                    pass
        mons = sorted((n for n in os.listdir(m) if n.startswith("QLKhoaOto") and n.endswith(".db")), key=lambda n: os.path.getmtime(os.path.join(m, n)))
        for n in mons[: max(0, len(mons) - int(CFG.get("giu_ban_theo_thang", 36)))]:
            try:
                os.remove(os.path.join(m, n))
            except Exception:
                pass
        info = {"t": now_iso(), "rev": rev, "files": [os.path.basename(x) for x in made], "paths": made, "extra": extra}
        con = connect()
        meta_set(con, "last_backup", info)
        con.commit()
        con.close()
        return info


KINDS = ("hang-ngay", "theo-thang", "truoc-khi-khoi-phuc", "excel")


def list_backups():
    d, m, x, p = _bk_paths()
    out = []
    for kind, folder in zip(KINDS, (d, m, p, x)):
        for n in sorted(os.listdir(folder), reverse=True):
            fp = os.path.join(folder, n)
            if os.path.isfile(fp) and not n.endswith(".tmp") and not n.startswith("_"):
                own = n.startswith(f"QLKhoaOto-{ma_dv()}_") or (n.startswith("QLKhoaOto_") and not n.startswith("QLKhoaOto-"))
                out.append({"kind": kind, "name": n, "path": fp, "folder": folder, "size": os.path.getsize(fp), "own": own,
                            "mtime": dt.datetime.fromtimestamp(os.path.getmtime(fp)).isoformat(timespec="seconds")})
    return out


def backup_file_path(kind, name):
    d, m, x, p = _bk_paths()
    folder = dict(zip(KINDS, (d, m, p, x))).get(kind)
    if not folder or "/" in name or "\\" in name or ".." in name:
        raise ValueError("Tên file không hợp lệ")
    fp = os.path.join(folder, name)
    if not os.path.isfile(fp):
        raise ValueError("Không thấy file sao lưu")
    return fp


def read_backup_db(fp):
    con = connect(fp, ro=True)
    ok = con.execute("PRAGMA integrity_check").fetchone()[0]
    r = con.execute("SELECT rev, saved_at, json FROM state WHERE id=1").fetchone()
    try:
        m = con.execute("SELECT v FROM meta WHERE k='instance_id'").fetchone()
        iid = json.loads(m["v"]) if m else ""
    except Exception:
        iid = ""
    con.close()
    data = json.loads(r["json"]) if r and r["json"] else None
    return ok, r["rev"] if r else 0, r["saved_at"] if r else "", data, iid


def backup_info(fp):
    """Nhận dạng 1 file sao lưu: có phải của bản cài này không, rev, số khóa/HV, toàn vẹn."""
    ok, rev, saved, data, iid = read_backup_db(fp)
    mine = instance_id()
    return {"path": fp, "integrity": ok, "rev": rev, "savedAt": saved, "instance": iid or "(bản cũ, chưa có ID)",
            "sameInstance": (iid == mine) if iid else None, "myInstance": mine, "app": (data or {}).get("app"),
            "nk": len((data or {}).get("khoa") or []), "nh": len((data or {}).get("hv") or [])}


def verify_latest():
    d, _, _, _ = _bk_paths()
    files = sorted((n for n in os.listdir(d) if n.endswith(".db")), key=lambda n: os.path.getmtime(os.path.join(d, n)), reverse=True)
    res = {"t": now_iso(), "ok": False}
    if not files:
        res["ok"] = None
        res["msg"] = "Chưa có bản sao lưu nào"
    else:
        fp = os.path.join(d, files[0])
        try:
            ok, rev, saved, data, iid = read_backup_db(fp)
            res.update(file=files[0], path=fp, integrity=ok, rev=rev, savedAt=saved, instance=iid,
                       nk=len((data or {}).get("khoa") or []), nh=len((data or {}).get("hv") or []),
                       ok=(ok == "ok" and data is not None and data.get("app") == APP_ID))
            res["msg"] = "Khôi phục được" if res["ok"] else "Bản sao lưu lỗi!"
        except Exception as e:
            res["msg"] = f"Lỗi đọc bản sao lưu: {e}"
    con = connect()
    meta_set(con, "last_verify", res)
    con.commit()
    con.close()
    return res


def pre_restore_backup():
    _, _, _, p = _bk_paths()
    fp = os.path.join(p, bk_name(f"truoc-khoi-phuc_{dt.datetime.now().strftime('%Y-%m-%d_%H%M%S')}.db"))
    sqlite_copy(fp)
    return fp


def all_paths():
    d, m, x, p = _bk_paths()
    ex = []
    for r in CFG.get("thu_muc_sao_luu_phu") or []:
        ex.append({"dir": r, "target": extra_target(r), "ok": bool(r) and os.path.isdir(r)})
    return {"tool": BASE, "db": DB_PATH, "config": CFG_PATH, "log": LOG_PATH, "backupRoot": bk_root(),
            "daily": d, "monthly": m, "excel": x, "preRestore": p, "extra": ex, "maDonVi": ma_dv(),
            "instance": instance_id(), "host": socket.gethostname()}


def open_in_explorer(path):
    """Mở thư mục / chọn file trong Windows Explorer (chỉ đường dẫn thuộc tool hoặc thư mục sao lưu)."""
    path = os.path.abspath(path)
    allowed = [BASE, bk_root()] + [os.path.abspath(r) for r in CFG.get("thu_muc_sao_luu_phu") or [] if r]
    if not any(os.path.normcase(path).startswith(os.path.normcase(a)) for a in allowed):
        raise ValueError("Đường dẫn không thuộc tool")
    if not os.path.exists(path):
        raise ValueError("Không thấy: " + path)
    import subprocess
    if os.name == "nt":
        if os.path.isfile(path):
            subprocess.Popen(["explorer", "/select,", path])
        else:
            os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-R" if os.path.isfile(path) else "", path])
    else:
        subprocess.Popen(["xdg-open", os.path.dirname(path) if os.path.isfile(path) else path])
    return True


# ---------------------------------------------------------------- Cập nhật từ GitHub
GH_DEFAULT = "HP-wukoong/QUAN_LY_KHOA_OTO_CSHN"
UPDATABLE = ("app.html", "server.py", "CHAY_TOOL.bat", "TAO_LOI_TAT_DESKTOP.bat", "DOC_TRUOC_HUONG_DAN.txt")


def gh_raw(path):
    repo = CFG.get("github_repo") or GH_DEFAULT
    br = CFG.get("github_branch") or "main"
    url = f"https://raw.githubusercontent.com/{repo}/{br}/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "QLKhoaOto/" + VERSION, "Cache-Control": "no-cache"})
    tok = (CFG.get("github_token") or "").strip()
    if tok:
        req.add_header("Authorization", "token " + tok)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def _vtuple(v):
    try:
        return tuple(int(x) for x in str(v).split("."))
    except Exception:
        return (0,)


def update_check():
    repo = CFG.get("github_repo") or GH_DEFAULT
    try:
        info = json.loads(gh_raw("version.json").decode("utf-8"))
    except urllib.error.HTTPError as e:
        msg = "Không thấy version.json trên GitHub" if e.code == 404 else f"GitHub trả lỗi {e.code}"
        if e.code == 404:
            msg += " (kho riêng tư cần token, hoặc chưa đăng bản phát hành)"
        return {"ok": False, "current": VERSION, "repo": repo, "msg": msg}
    except Exception as e:
        return {"ok": False, "current": VERSION, "repo": repo, "msg": f"Không kết nối được GitHub: {e}"}
    latest = info.get("version", "0")
    return {"ok": True, "current": VERSION, "latest": latest, "newer": _vtuple(latest) > _vtuple(VERSION),
            "notes": info.get("notes", ""), "date": info.get("date", ""), "repo": repo, "files": list((info.get("files") or {}).keys())}


def update_apply():
    info = json.loads(gh_raw("version.json").decode("utf-8"))
    files = info.get("files") or {}
    got = {}
    for name, sha in files.items():
        if name not in UPDATABLE:
            continue
        data = gh_raw("QLKhoaOto/" + name)
        if hashlib.sha256(data).hexdigest() != sha:
            raise ValueError(f"File {name} tải về sai mã kiểm tra — hủy cập nhật, không thay gì")
        got[name] = data
    if "app.html" not in got or "server.py" not in got:
        raise ValueError("Bản cập nhật thiếu app.html/server.py")
    old_dir = os.path.join(bk_root(), "ban-cu", f"v{VERSION}_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(old_dir, exist_ok=True)
    for name in got:
        src = os.path.join(BASE, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(old_dir, name))
    for name, data in got.items():
        tmp = os.path.join(BASE, name + ".new")
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, os.path.join(BASE, name))
    log(f"Cập nhật {VERSION} → {info.get('version')} ; bản cũ: {old_dir}")
    return {"ok": True, "from": VERSION, "to": info.get("version"), "old": old_dir, "files": list(got)}


def restart_self():
    """Mở lại máy chủ (sau cập nhật): tiến trình mới chờ cổng trống rồi chạy."""
    import subprocess
    if getattr(sys, "frozen", False):          # bản cài (QLKhoaOto.exe)
        args = [sys.executable, "--wait-port", "--no-browser"]
    else:
        args = [sys.executable, os.path.join(BASE, "server.py"), "--wait-port", "--no-browser"]
    kw = {"cwd": BASE}
    if os.name == "nt":
        kw["creationflags"] = 0x00000010  # CREATE_NEW_CONSOLE
    subprocess.Popen(args, **kw)
    threading.Timer(0.8, lambda: os._exit(0)).start()


def backup_loop():
    while True:
        try:
            do_backup()
            con = connect()
            lv = meta_get(con, "last_verify", None)
            con.close()
            if not lv or lv.get("ok") is None or lv.get("t", "") < (dt.datetime.now() - dt.timedelta(days=30)).isoformat():
                if any(n.endswith(".db") for n in os.listdir(_bk_paths()[0])):
                    verify_latest()
        except Exception as e:
            log("backup_loop: " + repr(e))
        time.sleep(10 * 60)


# ---------------------------------------------------------------- PIN & phiên đăng nhập
SESS = {}
FAILS = {"n": 0, "until": 0}


def pin_hash(pin, salt=None):
    salt = salt or secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), bytes.fromhex(salt), 200_000).hex()
    return {"salt": salt, "h": h}


def pin_ok(pin):
    con = connect()
    ph = meta_get(con, "pin", None)
    con.close()
    if not ph:
        return True
    return hmac.compare_digest(pin_hash(pin, ph["salt"])["h"], ph["h"])


def need_pin():
    con = connect()
    ph = meta_get(con, "pin", None)
    con.close()
    return bool(ph)


# ---------------------------------------------------------------- HTTP
def local_ips():
    ips = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    return sorted(ips)


class H(BaseHTTPRequestHandler):
    server_version = "QLKhoaOto/" + VERSION

    def log_message(self, fmt, *args):
        pass

    # ---- tiện ích
    def _send(self, code, body=b"", ctype="application/json; charset=utf-8", headers=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        return json.loads(raw.decode("utf-8")) if raw else {}

    def _raw(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    def _host_ok(self):
        host = (self.headers.get("Host") or "").split(":")[0]
        if host in ("127.0.0.1", "localhost"):
            return True
        return bool(CFG.get("cho_phep_mang_noi_bo")) and (host in local_ips() or host.startswith("192.168.") or host.startswith("10.") or host.startswith("172."))

    def _token(self):
        ck = self.headers.get("Cookie") or ""
        for part in ck.split(";"):
            k, _, v = part.strip().partition("=")
            if k == "qlk":
                return v
        return ""

    def _authed(self):
        if not need_pin():
            return True
        t = self._token()
        s = SESS.get(t)
        idle = int(CFG.get("khoa_man_hinh_sau_phut", 30)) * 60
        if s and time.time() - s < idle:
            SESS[t] = time.time()
            return True
        SESS.pop(t, None)
        return False

    def _device(self):
        return (self.headers.get("X-Device") or self.client_address[0])[:60]

    # ---- định tuyến
    def do_GET(self):
        self._route("GET")

    def do_POST(self):
        self._route("POST")

    def _route(self, method):
        try:
            if not self._host_ok():
                return self._send(403, {"err": "Host không hợp lệ"})
            u = urllib.parse.urlparse(self.path)
            path, q = u.path, urllib.parse.parse_qs(u.query)
            if method == "GET" and path in ("/", "/index.html"):
                with open(HTML_PATH, "rb") as f:
                    return self._send(200, f.read(), "text/html; charset=utf-8")
            if not path.startswith("/api/"):
                return self._send(404, {"err": "không có"})
            if method == "POST" and self.headers.get("X-QLK") != "1":
                return self._send(403, {"err": "thiếu header"})
            if path == "/api/ping":
                return self._send(200, {"ok": True, "app": APP_ID, "version": VERSION, "needPin": need_pin(), "authed": self._authed(),
                                        "lan": bool(CFG.get("cho_phep_mang_noi_bo")), "ips": local_ips(), "port": CFG["port"],
                                        "idleMin": CFG.get("khoa_man_hinh_sau_phut", 30)})
            if path == "/api/login" and method == "POST":
                if time.time() < FAILS["until"]:
                    return self._send(429, {"err": f"Sai nhiều lần, thử lại sau {int(FAILS['until'] - time.time())} giây"})
                pin = str(self._json().get("pin", ""))
                if pin_ok(pin):
                    FAILS["n"] = 0
                    t = secrets.token_hex(24)
                    SESS[t] = time.time()
                    return self._send(200, {"ok": True}, headers={"Set-Cookie": f"qlk={t}; HttpOnly; SameSite=Strict; Path=/"})
                FAILS["n"] += 1
                if FAILS["n"] >= 5:
                    FAILS["until"] = time.time() + 30
                    FAILS["n"] = 0
                return self._send(401, {"err": "Sai mã PIN"})
            if path == "/api/logout" and method == "POST":
                SESS.pop(self._token(), None)
                return self._send(200, {"ok": True})
            if not self._authed():
                return self._send(401, {"err": "Cần nhập mã PIN"})
            return self._api(method, path, q)
        except Exception as e:
            log("ERR " + self.path + " " + traceback.format_exc())
            try:
                return self._send(500, {"err": str(e)})
            except Exception:
                pass

    def _api(self, method, path, q):
        if path == "/api/state" and method == "GET":
            rev, saved, data = read_state()
            return self._send(200, {"rev": rev, "savedAt": saved, "data": data})
        if path == "/api/state" and method == "POST":
            body = self._json()
            data = body.get("data")
            if not isinstance(data, dict) or data.get("app") != APP_ID:
                return self._send(400, {"err": "Dữ liệu không hợp lệ"})
            try:
                rev, saved, merged = save_state(data, int(body.get("baseRev", -1)), self._device(), str(body.get("reason", ""))[:200])
            except BaseMissing as e:
                return self._send(409, {"err": "base_missing", "rev": e.args[0]})
            return self._send(200, {"rev": rev, "savedAt": saved, "merged": merged is not None, "data": merged})
        if path == "/api/rev":
            rev, saved, _ = read_state()
            return self._send(200, {"rev": rev, "savedAt": saved})
        if path == "/api/audit":
            sql, args = "SELECT * FROM audit WHERE 1=1", []
            if q.get("eid"):
                sql += " AND eid=?"
                args.append(q["eid"][0])
            if q.get("entity"):
                sql += " AND entity=?"
                args.append(q["entity"][0])
            if q.get("q"):
                sql += " AND (label LIKE ? OR new LIKE ? OR old LIKE ?)"
                args += ["%" + q["q"][0] + "%"] * 3
            sql += " ORDER BY id DESC LIMIT ?"
            args.append(int((q.get("limit") or ["300"])[0]))
            con = connect()
            rows = [dict(r) for r in con.execute(sql, args)]
            con.close()
            return self._send(200, rows)
        if path == "/api/revs":
            con = connect()
            rows = [dict(r) for r in con.execute("SELECT rev, saved_at, device, nk, nh, reason FROM revs ORDER BY rev DESC LIMIT 200")]
            con.close()
            return self._send(200, rows)
        if path.startswith("/api/revs/"):
            con = connect()
            r = con.execute("SELECT gz FROM revs WHERE rev=?", (int(path.rsplit("/", 1)[1]),)).fetchone()
            con.close()
            if not r:
                return self._send(404, {"err": "không có phiên bản này"})
            return self._send(200, gzip.decompress(r["gz"]))
        if path == "/api/backups":
            con = connect()
            info = {"files": list_backups(), "last": meta_get(con, "last_backup"), "verify": meta_get(con, "last_verify"),
                    "extra": CFG.get("thu_muc_sao_luu_phu") or [], "dir": bk_root(), "db": DB_PATH, "paths": all_paths(),
                    "extraStatus": [{"dir": d, "ok": bool(d) and os.path.isdir(d)} for d in CFG.get("thu_muc_sao_luu_phu") or []]}
            con.close()
            return self._send(200, info)
        if path == "/api/paths":
            return self._send(200, all_paths())
        if path == "/api/backup/info" and method == "POST":
            b = self._json()
            fp = backup_file_path(b.get("kind"), b.get("name"))
            return self._send(200, backup_info(fp))
        if path == "/api/open" and method == "POST":
            if self.client_address[0] not in ("127.0.0.1", "::1"):
                return self._send(403, {"err": "Chỉ mở thư mục được trên chính máy chạy tool"})
            open_in_explorer(str(self._json().get("path", "")))
            return self._send(200, {"ok": True})
        if path == "/api/update/check":
            return self._send(200, update_check())
        if path == "/api/update/apply" and method == "POST":
            try:
                do_backup(force=True)
                return self._send(200, update_apply())
            except Exception as e:
                return self._send(400, {"err": str(e)})
        if path == "/api/restart" and method == "POST":
            if self.client_address[0] not in ("127.0.0.1", "::1"):
                return self._send(403, {"err": "Chỉ khởi động lại trên máy chạy tool"})
            self._send(200, {"ok": True})
            restart_self()
            return
        if path == "/api/backup/now" and method == "POST":
            return self._send(200, do_backup(force=True))
        if path == "/api/backup/verify" and method == "POST":
            return self._send(200, verify_latest())
        if path == "/api/backup/xlsx" and method == "POST":
            name = bk_name(f"{dt.date.today().isoformat()}.xlsx")
            if not name.endswith(".xlsx"):
                return self._send(400, {"err": "tên file"})
            _, _, x, _ = _bk_paths()
            fp = os.path.join(x, name)
            with open(fp, "wb") as f:
                f.write(self._raw())
            extra = copy_to_extra(fp, "excel")
            con = connect()
            meta_set(con, "last_xlsx", {"t": now_iso(), "name": name})
            con.commit()
            con.close()
            # giữ 60 file excel gần nhất
            xs = sorted(n for n in os.listdir(x) if n.endswith(".xlsx"))
            for n in xs[: max(0, len(xs) - 60)]:
                os.remove(os.path.join(x, n))
            return self._send(200, {"ok": True, "name": name, "extra": extra})
        if path == "/api/meta" and method == "GET":
            con = connect()
            out = {k: meta_get(con, k) for k in ("last_backup", "last_verify", "last_xlsx")}
            con.close()
            return self._send(200, out)
        if path == "/api/restore/preview" and method == "POST":
            b = self._json()
            if b.get("rev"):
                con = connect()
                r = con.execute("SELECT gz FROM revs WHERE rev=?", (int(b["rev"]),)).fetchone()
                con.close()
                data = json.loads(gzip.decompress(r["gz"])) if r else None
            else:
                _, _, _, data, _ = read_backup_db(backup_file_path(b.get("kind"), b.get("name")))
            if not data:
                return self._send(404, {"err": "Không đọc được dữ liệu"})
            return self._send(200, {"data": data})
        if path == "/api/restore" and method == "POST":
            b = self._json()
            data = b.get("data")
            if not isinstance(data, dict) or data.get("app") != APP_ID:
                return self._send(400, {"err": "Dữ liệu không hợp lệ"})
            pre = pre_restore_backup()
            rev, _, _ = read_state()
            rev, saved, _ = save_state(data, rev, self._device(), "KHÔI PHỤC: " + str(b.get("label", ""))[:150])
            return self._send(200, {"rev": rev, "savedAt": saved, "pre": os.path.basename(pre)})
        if path == "/api/config" and method == "GET":
            return self._send(200, {**CFG, "github_token": "***" if CFG.get("github_token") else "", "_ips": local_ips(), "_needPin": need_pin(), "_paths": all_paths()})
        if path == "/api/config" and method == "POST":
            b = self._json()
            if "thu_muc_sao_luu_phu" in b:
                CFG["thu_muc_sao_luu_phu"] = [str(x).strip() for x in b["thu_muc_sao_luu_phu"] if str(x).strip()][:6]
            if "cho_phep_mang_noi_bo" in b:
                if b["cho_phep_mang_noi_bo"] and not need_pin():
                    return self._send(400, {"err": "Phải đặt mã PIN trước khi cho máy khác trong mạng truy cập"})
                CFG["cho_phep_mang_noi_bo"] = bool(b["cho_phep_mang_noi_bo"])
            if "ma_don_vi" in b:
                CFG["ma_don_vi"] = str(b["ma_don_vi"]).strip()[:20] or "CSHN"
            if "thu_muc_sao_luu" in b:
                v = str(b["thu_muc_sao_luu"]).strip()
                if v:
                    try:
                        os.makedirs(v, exist_ok=True)
                        t = os.path.join(v, ".qlk_test")
                        open(t, "w").close()
                        os.remove(t)
                    except Exception as e:
                        return self._send(400, {"err": f"Không ghi được vào thư mục {v}: {e}"})
                CFG["thu_muc_sao_luu"] = v
            for k in ("github_repo", "github_branch", "github_token"):
                if k in b and b[k] != "***":
                    CFG[k] = str(b[k]).strip()
            for k in ("giu_ban_hang_ngay", "giu_ban_theo_thang", "khoa_man_hinh_sau_phut"):
                if k in b:
                    CFG[k] = max(1, int(b[k]))
            save_cfg(CFG)
            return self._send(200, {"ok": True, "note": "Đổi chế độ mạng cần tắt và mở lại tool" if "cho_phep_mang_noi_bo" in b else ""})
        if path == "/api/pin" and method == "POST":
            b = self._json()
            if need_pin() and not pin_ok(str(b.get("old", ""))):
                return self._send(401, {"err": "Mã PIN cũ không đúng"})
            new = str(b.get("new", ""))
            con = connect()
            if new:
                if len(new) < 4:
                    con.close()
                    return self._send(400, {"err": "PIN tối thiểu 4 ký tự"})
                meta_set(con, "pin", pin_hash(new))
            else:
                if CFG.get("cho_phep_mang_noi_bo"):
                    con.close()
                    return self._send(400, {"err": "Đang mở cho mạng nội bộ — tắt chế độ đó trước khi bỏ PIN"})
                con.execute("DELETE FROM meta WHERE k='pin'")
            con.commit()
            con.close()
            SESS.clear()
            t = secrets.token_hex(24)
            SESS[t] = time.time()
            return self._send(200, {"ok": True}, headers={"Set-Cookie": f"qlk={t}; HttpOnly; SameSite=Strict; Path=/"})
        if path.startswith("/api/khoa/") and path.endswith(".json"):
            # Liên thông: danh sách HV của 1 khóa cho tool khác (vd sổ nhật ký / DAT)
            code = urllib.parse.unquote(path[len("/api/khoa/"):-5]).upper()
            _, _, data = read_state()
            data = data or {}
            k = next((k for k in data.get("khoa") or [] if f"{k.get('hang')}-{int(k.get('so') or 0):02d}" == code), None)
            if not k:
                return self._send(404, {"err": "không có khóa " + code})
            gv = {g["id"]: g for g in data.get("gv") or []}
            hv = [h for h in data.get("hv") or [] if h.get("khoaId") == k["id"]]
            hv.sort(key=lambda h: h.get("order") if h.get("order") is not None else 10 ** 9)
            return self._send(200, {"khoa": code, "hang": k.get("hang"), "ngayKG": k.get("ngayKG"), "ngayBG": k.get("ngayBG"),
                                    "hocVien": [{"stt": i + 1, "hoTen": h.get("hoTen"), "ngaySinh": h.get("ngaySinh"), "cccd": h.get("cccd"),
                                                 "sdt": h.get("sdt"), "maDKI": h.get("maDK"), "trangThai": h.get("tt") or "hoc",
                                                 "giaoVien": (gv.get(h.get("gvId")) or {}).get("hoTen") or h.get("gvGoc") or h.get("gvText")}
                                                for i, h in enumerate(hv)]})
        return self._send(404, {"err": "không có API này"})


# ---------------------------------------------------------------- Khởi động
def port_is_ours(port):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/ping", timeout=2) as r:
            return json.loads(r.read().decode("utf-8")).get("app") == APP_ID
    except Exception:
        return False


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    init_db()
    port = int(CFG.get("port", 8686))
    bind = "0.0.0.0" if CFG.get("cho_phep_mang_noi_bo") else "127.0.0.1"
    url = f"http://127.0.0.1:{port}/"
    if "--wait-port" in sys.argv:
        for _ in range(40):
            if not port_is_ours(port):
                break
            time.sleep(0.25)
    if port_is_ours(port):
        print("Tool đang chạy rồi — mở trình duyệt.")
        if CFG.get("tu_mo_trinh_duyet", True):
            webbrowser.open(url)
        return
    try:
        srv = ThreadingHTTPServer((bind, port), H)
    except OSError:
        for p in range(port + 1, port + 20):
            try:
                srv = ThreadingHTTPServer((bind, p), H)
                port = p
                url = f"http://127.0.0.1:{port}/"
                CFG["port"] = port
                break
            except OSError:
                continue
        else:
            print("Không mở được cổng mạng nào.")
            return
    srv.daemon_threads = True
    threading.Thread(target=backup_loop, daemon=True).start()
    log(f"Khởi động v{VERSION} tại {bind}:{port}")
    print("=" * 60)
    print(f" QUẢN LÝ KHÓA Ô TÔ CSHN  v{VERSION}")
    print(f" Mở trình duyệt: {url}")
    if CFG.get("cho_phep_mang_noi_bo"):
        for ip in local_ips():
            print(f" Máy khác trong mạng: http://{ip}:{port}/")
    print(f" Dữ liệu : {DB_PATH}")
    print(f" Sao lưu : {bk_root()}   (mã đơn vị {ma_dv()}, ID {instance_id()})")
    print(" ĐỪNG TẮT CỬA SỔ NÀY khi đang dùng tool (thu nhỏ được).")
    print("=" * 60)
    if CFG.get("tu_mo_trinh_duyet", True) and "--no-browser" not in sys.argv:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            do_backup()
        except Exception:
            pass


if __name__ == "__main__":
    main()

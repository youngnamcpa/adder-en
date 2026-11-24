# -*- coding: utf-8 -*-
"""US-focused 100% English preflight check and SEC contact setup for ADDER (English Edition).

Usage:
    python -X utf8 scripts/preflight.py                         # Run all 10 US checks and print summary table
    python -X utf8 scripts/preflight.py --save SEC_CONTACT_EMAIL # Prompt privately for your SEC contact email and store it
    python -X utf8 scripts/preflight.py --setup                 # Interactive first-time setup
    python -X utf8 scripts/preflight.py --offline --no-excel    # Skip live network & Excel COM checks
"""
from __future__ import annotations
import argparse
import datetime
import getpass
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
KO_SCRIPTS = os.path.join(KIT, "스크립트")
if KO_SCRIPTS not in sys.path:
    sys.path.insert(0, KO_SCRIPTS)

import 준비점검 as pf  # noqa: E402

CIRCLES = {1: "①", 2: "②", 3: "③", 4: "④", 5: "⑤", 6: "⑥", 7: "⑦", 8: "⑧", 9: "⑨", 10: "⑩"}

STATUS_WORD = {
    "통과": "ok",
    "미비": "missing",
    "선택없음": "not installed (optional)",
    "건너뜀": "skipped",
    "보류": "deferred",
}


def _en_excel_notes(check_excel: bool):
    ex = pf.엑셀있나(check_excel)
    py = pf._있나("win32com") and pf._있나("pythoncom")
    fo = pf._있나("formulas")
    if ex == "있음" and py:
        c3 = ("통과", "Excel + pywin32")
    elif fo:
        suffix = " (Excel app not checked)" if ex == "보지 않음" else ""
        c3 = ("통과", "formulas package" + suffix)
    else:
        c3 = ("선택없음", "neither Excel+pywin32 nor formulas installed — values written without recalculation")

    if ex == "있음":
        c4 = ("통과", "installed")
    elif ex == "Windows 아님":
        c4 = ("건너뜀", "non-Windows OS (uses formulas package if installed)")
    elif ex == "보지 않음":
        c4 = ("건너뜀", "not checked (--no-excel)")
    else:
        c4 = ("선택없음", "not detected")
    return c3, c4


def _en_sec_contact(deferred):
    val = (os.environ.get("SEC_CONTACT_EMAIL") or "").strip()
    if not val:
        if "SEC_CONTACT_EMAIL" in deferred:
            return ("보류", "marked 'later' — required before fetching SEC EDGAR filings")
        return ("미비", "not set — required by SEC EDGAR fair-access rules")
    ok, _ = pf.키꼴(7, val)
    if not ok:
        return ("미비", "invalid format — enter a valid email address (e.g. name@example.com)")
    return ("통과", f"stored ({len(val)} chars)")


def _en_sec_conn(sec_ok: bool, online: bool):
    if not online:
        return ("건너뜀", "network checks off (--offline)")
    if not sec_ok:
        return ("건너뜀", "skipped until ⑤ SEC contact is set")
    r = pf.점검_SEC(True)
    if r["상태"] == "통과":
        return ("통과", "data.sec.gov reachable (HTTP 200)")
    mal = r.get("말") or ""
    if "403" in mal:
        return ("미비", "HTTP 403 — check SEC_CONTACT_EMAIL format or rate limit")
    return ("미비", f"connection failed ({mal or 'network error'})")


def _en_base_rate():
    import glob as _glob
    import re as _re
    us_dir = os.path.join(pf.공용캐시(), "기저율", "US")
    years = sorted(
        int(m.group(1))
        for p in _glob.glob(os.path.join(us_dir, "*주요계정_*.csv"))
        for m in [_re.search(r"주요계정_(\d{4})\.csv$", p)]
        if m
    )
    if years:
        return ("통과", f"US panel ready ({years[0]}-{years[-1]}, {len(years)} yrs)")
    return ("선택없음", "US panel not downloaded yet (optional)")


def _en_version(online: bool):
    ver = (pf.버전읽기().get("ADDER") or "1.2.0").strip()
    if not online:
        return ("통과", f"v{ver} (offline)")
    r = pf.점검_버전(True)
    mal = r.get("말") or ""
    if "최신" in mal or r["상태"] == "통과":
        return ("통과", f"v{ver} (up to date)")
    return ("선택없음", f"v{ver} (check GitHub for updates)")


def _en_write_access(work_dir: str = "."):
    r = pf.점검_쓰기(work_dir)
    if r["상태"] == "통과":
        return ("통과", "working folder & shared cache writable")
    return ("미비", "cannot write to current folder or shared cache")


def _en_permissions(work_dir: str = "."):
    r = pf.점검_갈래권한(work_dir)
    if r["상태"] == "통과":
        return ("통과", "python, WebSearch, WebFetch allowed")
    mal = r.get("말") or ""
    missing = []
    for tool_name in ("python", "WebSearch", "WebFetch"):
        if tool_name in mal:
            missing.append(tool_name)
    miss_str = ", ".join(missing) if missing else "python, WebSearch, WebFetch"
    return ("선택없음", f"not in allow rules: {miss_str} — subagents may pause on permission prompts")


def save_key_en(key_name: str, raw_val: str | None = None, work_dir: str = ".") -> int:
    if key_name != "SEC_CONTACT_EMAIL" and key_name not in pf.키이름.values():
        print(f"Unsupported key name: {key_name}. Expected SEC_CONTACT_EMAIL.")
        return 2
    num = {v: k for k, v in pf.키이름.items()}.get(key_name, 7)
    if raw_val is None:
        if sys.stdin.isatty():
            raw_val = getpass.getpass(f"Enter {key_name} (input hidden; press Enter to defer): ")
        else:
            raw_val = sys.stdin.readline()
    val = (raw_val or "").strip()
    if not val:
        deferred = set(pf.이전보류(work_dir))
        deferred.add(key_name)
        p = os.path.join(work_dir, "_raw", "준비점검.json")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with io.open(p, "w", encoding="utf-8") as f:
            json.dump({"형식": "준비점검/1", "만든날": datetime.date.today().isoformat(), "보류": sorted(deferred)}, f, ensure_ascii=False, indent=2)
        print(f"Recorded {key_name} as 'later' (deferred).")
        return 0
    ok, _ = pf.키꼴(num, val)
    if not ok:
        print(f"Invalid format for {key_name} — please enter a valid email address (not saved).")
        return 2
    where = pf.저장(key_name, val)
    where_en = "Windows user environment variables" if "사용자 환경 변수" in str(where) else str(where)
    print(f"Saved {key_name} ({len(val)} chars) to {where_en}.")
    print("Next — Close and reopen your terminal and Claude Code so the new environment variable is loaded, then run `/preflight`.")
    return 0


def run_preflight(online: bool = True, check_excel: bool = True, out_json: str | None = None) -> int:
    ver = (pf.버전읽기().get("ADDER") or "1.2.0").strip()
    today = datetime.date.today().isoformat()
    deferred = pf.이전보류(".")

    p1 = pf.점검_파이썬()
    s1 = (p1["상태"], p1["말"])
    p2 = pf.점검_패키지()
    s2 = (p2["상태"], "" if p2["상태"] == "통과" else p2["말"].replace("없음:", "missing:").replace(" · ", ", "))
    s3, s4 = _en_excel_notes(check_excel)
    s5 = _en_sec_contact(deferred)
    s6 = _en_sec_conn(s5[0] == "통과", online)
    s7 = _en_base_rate()
    s8 = _en_version(online)
    s9 = _en_write_access(".")
    s10 = _en_permissions(".")

    rows = [
        (1, "Python (>= 3.11)", True, s1[0], s1[1]),
        (2, "requests, openpyxl", True, s2[0], s2[1]),
        (3, "Excel recalculation", False, s3[0], s3[1]),
        (4, "Excel desktop app", False, s4[0], s4[1]),
        (5, "SEC contact (email)", True, s5[0], s5[1]),
        (6, "SEC EDGAR connection", False, s6[0], s6[1]),
        (7, "US base-rate panel", False, s7[0], s7[1]),
        (8, "Kit version", False, s8[0], s8[1]),
        (9, "Write access", True, s9[0], s9[1]),
        (10, "Subagent permissions", False, s10[0], s10[1]),
    ]

    req_total = sum(1 for r in rows if r[2])
    req_ok = sum(1 for r in rows if r[2] and r[3] == "통과")
    opt_total = sum(1 for r in rows if not r[2])
    opt_ok = sum(1 for r in rows if not r[2] and r[3] == "통과")

    print(f"Preflight check  {today}  ADDER v{ver} (English Edition)    required {req_ok}/{req_total} · optional {opt_ok}/{opt_total}")
    if s5[0] == "미비":
        print("First time? Store your SEC EDGAR contact email before running your first US valuation:")
        print("  · No API key or registration is needed — SEC EDGAR only asks for your email address in request headers.")
        print("  · Run in your terminal: `python -X utf8 scripts/preflight.py --save SEC_CONTACT_EMAIL`")
        print("  · Details: QUICKSTART_SEC.md in this folder.")

    for idx, name, is_req, st, note in rows:
        st_en = STATUS_WORD.get(st, st)
        line = f"{CIRCLES[idx]} {name:<26} {st_en}"
        if note:
            line += f" — {note}"
        print(line)

    guidance = []
    if s1[0] != "통과":
        guidance.append("  ① Install Python 3.11 or later from python.org (check 'Add python.exe to PATH' on Windows).")
    if s2[0] != "통과":
        guidance.append("  ② Install required packages: `python -m pip install -r requirements.txt`")
    if s3[0] == "선택없음":
        guidance.append("  ③ Optional formula recalculation: `python -m pip install pywin32` (with Excel) or `python -m pip install formulas`.")
    if s5[0] != "통과":
        guidance.append("  ⑤ Store your SEC contact email privately from your terminal:\n     `python -X utf8 scripts/preflight.py --save SEC_CONTACT_EMAIL`\n     Then reopen your terminal and Claude Code and run `/preflight` again.")
    if s6[0] == "미비":
        guidance.append("  ⑥ Could not reach data.sec.gov — check your internet/firewall settings and verify SEC_CONTACT_EMAIL.")
    if s7[0] == "선택없음":
        guidance.append("  ⑦ Optional US base-rate empirical panel (SEC Financial Statement Data Sets):\n     `python -X utf8 scripts/base_rates.py --download --country US`")
    if s9[0] != "통과":
        guidance.append("  ⑨ Reopen Claude Code in a user-writable folder (e.g. `Documents/ADDER/NVIDIA`).")
    if s10[0] == "선택없음":
        guidance.append("  ⑩ Advised: allow `python`, `WebSearch`, and `WebFetch` in Claude Code settings (`~/.claude/settings.json` under `permissions.allow`) so parallel research subagents do not stall on interactive prompts.")

    if guidance:
        print("Next:")
        for g in guidance:
            print(g)
    else:
        print('Next: all set! Start with "Value NVIDIA for me" (or any US-listed stock).')

    # Also write _raw/준비점검.json in the schema expected by 자체검사 check 51
    out_path = out_json or os.path.join(os.getcwd(), "_raw", "준비점검.json")
    try:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        payload = {
            "형식": "준비점검/1",
            "만든날": today,
            "키트버전": ver,
            "언어": "en",
            "항목": [
                {"번호": idx, "이름": name, "필수": is_req, "상태": st, "말": note}
                for idx, name, is_req, st, note in rows
            ],
            "보류": sorted(deferred),
            "신호": "참고",
        }
        with io.open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except OSError:
        pass

    return 0 if req_ok == req_total else 1


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Preflight check for ADDER (English Edition)")
    ap.add_argument("--save", "--저장", dest="save_key", default=None, help="Privately store a contact/key (e.g. SEC_CONTACT_EMAIL)")
    ap.add_argument("--setup", "--설치", action="store_true", help="Interactive setup for SEC_CONTACT_EMAIL")
    ap.add_argument("--offline", "--망없이", action="store_true", help="Skip live network checks")
    ap.add_argument("--no-excel", "--엑셀안봄", action="store_true", help="Skip launching Excel COM check")
    ap.add_argument("--out", "--곳", default=None, help="Output path for preflight JSON record")
    ap.add_argument("--언어", default="en", help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    if args.save_key:
        return save_key_en(args.save_key)
    if args.setup:
        return save_key_en("SEC_CONTACT_EMAIL")
    return run_preflight(online=not args.offline, check_excel=not args.no_excel, out_json=args.out)


if __name__ == "__main__":
    sys.exit(main())

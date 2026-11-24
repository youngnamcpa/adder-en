# -*- coding: utf-8 -*-
"""C2 · CP2 국내 차입금 자동 1차 판정 — 미배정 금융부채 임계. 캐시만 읽는다(네트워크 0회).

왜 있는가 (펄어비스 회차 펄29)
    스킬 「차입금·현금 판정 — 자동 1차, 주석 원문은 뭉친 곳만」의 판정 스크립트가 본체에
    없어 회차가 짰다(`_raw/peers/c2/_차입금판정.py`). 사람이 주석을 읽는 것이 이 갈래의
    에이전트 시간 병목이라(한화오션 7곳 중 5곳이 「뭉침 없음」이었는데 전부 읽었다) **읽을 곳만
    큐에 올리는 판정**을 도구로 둔다.

규칙 (스킬 원문 그대로)
    1. 1차는 전체 재무제표 API 의 표준 계정으로 조립한다 — `dart_fs_all.py` 의 `차입금합계`
    2. 표준 계정 패턴(차입금·사채·리스부채)에 안 걸린 **「금융부채」 이름 계정**(파생·매입채무 제외)
       을 미배정 금융부채 후보로 모은다. 합이 **임계 = min(총자산 1%, 500억)** 미만이고
       차입금이 0 이 아니며 `차입금_확인필요` 가 없으면 **자동 통과**
    3. 아니면 **주석 큐** — 「미배정 X억(임계 이상)」 또는 「차입금 0/확인필요」
    4. 자동 통과도 근거 칸에 「표준 계정 조립 · 미배정 X억(임계 미만)」을 적는다 — 비워 두면
       「안 본 것」과 구별이 안 된다
    곁 표시: 「기타금융부채가 자기자본 1% 초과면 주석에서 이자부만 분리」 해당 계정을 따로 적는다.
    「기타부채」 이름 계정은 선수금·예수금이 섞여 금액에 넣지 않고 **이름·금액만 참고로** 싣는다.

임계 해석 — 스킬은 「총자산의 1% 또는 500억」이라 적었다. **작은 쪽(min)** 으로 읽는다:
큰 회사일수록 1%가 수백억~수천억이 되어 뭉침이 통째로 자동 통과하는 것을 500억이 막는다.

사용
    python 스크립트/peer_차입금판정_국내.py --명단 C2_CP2명단.json --year 2026 --reprt 11012
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

차입 = re.compile(r"(단기차입금|장기차입금|유동성장기|사채|리스부채|차입금)")
기타부채 = re.compile(r"기타(유동|비유동)?부채")


def _n(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return 0.0


def 명단읽기(p):
    d = json.load(io.open(p, encoding="utf-8"))
    if isinstance(d, dict):
        d = d.get("핵심", []) + d.get("예비", []) if "핵심" in d else d.get("행", [])
    return [{"종목코드": str(x.get("종목코드", "")).zfill(6), "고유번호": str(x.get("고유번호", "")).zfill(8)
             if x.get("고유번호") else "", "회사명": x.get("회사명", "")} for x in d]


def 판정한곳(x, 추출행, fs목록, 임계율=0.01, 상한=5e10):
    bs = [r for r in fs목록 if r.get("sj_div") == "BS"]
    자산, 자본 = _n(추출행.get("자산총계")), _n(추출행.get("자본총계"))
    임계 = min(자산 * 임계율, 상한)
    후보, 참고 = [], []
    for r in bs:
        nm = (r.get("account_nm") or "").strip()
        if 차입.search(nm) or "자산" in nm or "자본" in nm:
            continue
        v = _n(r.get("thstrm_amount"))
        if re.search(r"금융부채", nm) and not re.search(r"(파생|매입채무)", nm):
            if v:
                후보.append((nm, v))
        elif 기타부채.search(nm) and v:
            참고.append((nm, v))
    미배정 = sum(v for _, v in 후보)
    차입합 = _n(추출행.get("차입금합계"))
    확인필요 = (추출행.get("차입금_확인필요") or "").strip()
    자동 = 미배정 < 임계 and 차입합 > 0 and not 확인필요
    if 자동:
        판정 = "자동 통과 — 표준 계정 조립 · 미배정 %.1f억(임계 %.1f억 미만)" % (미배정 / 1e8, 임계 / 1e8)
    elif 미배정 >= 임계:
        판정 = "주석 큐 — 미배정 금융부채 %.1f억(임계 %.1f억 이상)" % (미배정 / 1e8, 임계 / 1e8)
    else:
        판정 = "주석 큐 — 차입금 0 또는 확인필요 표시"
    return {"회사명": x["회사명"], "종목코드": x["종목코드"], "고유번호": x["고유번호"],
            "rcept_no": fs목록[0].get("rcept_no") if fs목록 else None,
            "차입금합계_억": round(차입합 / 1e8, 1), "잡힌계정": 추출행.get("차입금항목", ""),
            "대체행_주의": 추출행.get("대체행_주의", ""), "차입금_확인필요": 확인필요,
            "자산총계_억": round(자산 / 1e8, 1), "자본총계_억": round(자본 / 1e8, 1),
            "현금_억": round(_n(추출행.get("현금및현금성자산")) / 1e8, 1),
            "미배정금융부채후보": [[nm, round(v / 1e8, 1)] for nm, v in 후보],
            "미배정합_억": round(미배정 / 1e8, 1), "임계_억": round(임계 / 1e8, 1),
            "기타금융부채_자본1%초과": [[nm, round(v / 1e8, 1)] for nm, v in 후보 if v > 자본 * 0.01],
            "참고_기타부채(합산 안 함)": [[nm, round(v / 1e8, 1)] for nm, v in 참고],
            "자동통과": 자동, "판정": 판정}


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="C2·CP2 국내 차입금 자동 1차 판정 — 네트워크 0회")
    ap.add_argument("--폴더", default=os.getcwd())
    ap.add_argument("--명단", required=True, help="목록 JSON(종목코드·고유번호·회사명) 또는 C1 핵심표본 JSON")
    ap.add_argument("--year", required=True, help="dart_fs_all 에 준 사업연도")
    ap.add_argument("--reprt", default="11012")
    ap.add_argument("--임계율", type=float, default=0.01, help="총자산 대비 (기본 1%%)")
    ap.add_argument("--상한억", type=float, default=500.0, help="임계 상한(억) — min(총자산×율, 상한)")
    ap.add_argument("--출력", default=None, help="기본 {폴더}/_raw/peers/c2/차입금판정.json")
    a = ap.parse_args()
    폴더 = os.path.abspath(a.폴더)
    peer = os.path.join(폴더, "_raw", "peers")
    명단p = a.명단 if os.path.isabs(a.명단) else (os.path.join(peer, a.명단)
                                             if os.path.exists(os.path.join(peer, a.명단)) else os.path.join(폴더, a.명단))
    명단 = 명단읽기(명단p)
    추출p = os.path.join(폴더, "전체재무_추출.csv")
    if not os.path.exists(추출p):
        sys.exit("전체재무_추출.csv 가 없습니다 — dart_fs_all.py 를 먼저 돌리십시오")
    추출 = {}
    for r in csv.DictReader(io.open(추출p, encoding="utf-8-sig")):
        # 병합판(연도·보고서 칸)이면 이번 연도·보고서 행만 쓴다. 옛 판(칸 없음)은 그대로
        if r.get("연도") and (r["연도"] != str(a.year) or (r.get("보고서") or a.reprt) != a.reprt):
            continue
        추출[r["고유번호"].zfill(8)] = r
    out, 없음 = [], []
    for x in 명단:
        c = x["고유번호"]
        r = 추출.get(c)
        쓴 = (r or {}).get("쓴구분") or "CFS"
        fp = os.path.join(peer, "fs", "%s_%s_%s_%s.json" % (c, a.year, a.reprt, 쓴))
        if not r or not os.path.exists(fp):
            out.append({"회사명": x["회사명"], "종목코드": x["종목코드"], "고유번호": c, "자동통과": False,
                        "판정": "확인 불가 — %s" % ("전체재무_추출.csv 에 행 없음" if not r else "fs 캐시 없음(%s)" % os.path.basename(fp))})
            없음.append(x["회사명"])
            continue
        L = json.load(io.open(fp, encoding="utf-8")).get("list", []) or []
        out.append(판정한곳(x, r, L, a.임계율, a.상한억 * 1e8))
    p = a.출력 or os.path.join(peer, "c2", "차입금판정.json")
    if not os.path.isabs(p):
        p = os.path.join(폴더, p)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(out, io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    큐 = [r["회사명"] for r in out if not r["자동통과"]]
    print("→ %s · 기준 %s %s · 임계 min(총자산 %.0f%%, %.0f억) · %s"
          % (p, a.year, a.reprt, a.임계율 * 100, a.상한억, time.strftime("%H:%M:%S")))
    for r in out:
        print("  %-12s %8s %s | %s" % (r["회사명"][:12], r.get("차입금합계_억", ""), r.get("미배정금융부채후보", ""), r["판정"]))
    print("자동 통과 %d · 주석 큐 %d%s" % (len(out) - len(큐), len(큐), (" — 확인 불가 %s" % 없음) if 없음 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())

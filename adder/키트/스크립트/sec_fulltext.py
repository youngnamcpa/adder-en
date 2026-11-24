# -*- coding: utf-8 -*-
"""SEC 전문검색 — EDGAR Full-Text Search 로 「어느 제출인이 어떤 운영지표 문구를 공시하나」를 색인한다 (제안 D-미국 · 2026-10-22 신설).

무엇을 하나
  `efts.sec.gov/LATEST/search-index?q="units delivered"&forms=10-K&ciks=…` 는 전 제출인의 10-K 본문을 문구로 검색해 어느 제출건(adsh · CIK · 양식 · 기간)이
  그 문구를 쓰는지 돌려준다(본문은 안 온다 — 본문은 기존 원문 경로로 내려간다). B1 매출 정찰의 출처 종류 체크리스트에 **「이 회사가 어떤 운영지표를 공시하나」**
  한 칸을 기계로 채우고, 같은 산업(SIC)에서 그 지표를 공시하는 회사 수(동종이 쓰는 분모인가)를 함께 적는다. 키 없음 · User-Agent 연락처만(환경변수 SEC_CONTACT_EMAIL).

  대상 회사의 문구 목록은 `문구사전`(업종 중립 — 물량 · 능력 · 단위경제 · 수주 · 인원)이고, 회차가 `--문구` 로 더할 수 있다. 회사 이름 · 업종 이름은 이 도구에 없다.

사용
  python 스크립트/sec_fulltext.py --cik 0000001800 [--부터 2024-01-01] [--문구 "backlog" "deliveries"] [--동종 2834]   # 대상 + (선택) 같은 SIC 의 공시 회사 수
  python 스크립트/sec_fulltext.py --문구 "units delivered" --전체                                                      # 전 제출인 — 어느 회사가 쓰나(상위 50)
내는 것 — `_raw/운영지표공시.json`(가정 곁 — `--낼`): {형식 · 만든날 · 입력 · 대상[{문구 · 건수 · 제출건[{adsh · 양식 · 기간 · 제출일}]}] · 동종[{문구 · 회사수 · 보기}] ·
          확인상태 「참고(EDGAR 전문검색 — 문구 색인)」 · 신호[]}. 신호는 참고만 — 「공시하는 운영지표 문구 n개」 · 「동종은 쓰는데 대상은 안 쓰는 문구」.
종료 코드 — 0 통과 · 2 입력오류(SEC_CONTACT_EMAIL 없음 · 응답 깨짐).
속도 — SEC 공통 10 req/s 한도 안(요청 사이 0.15초).
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass
여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 입력오류  # noqa: E402

주소 = "https://efts.sec.gov/LATEST/search-index"
# 업종 중립 문구 — 물량 · 능력 · 단위경제 · 수주 · 인원 · 가격(10-K 본문에 쓰이는 영어 관용구)
문구사전 = {
    "물량": ['"units delivered"', '"units sold"', '"deliveries"', '"shipments"', '"production volume"', '"tons shipped"', '"vehicles delivered"'],
    "능력": ['"production capacity"', '"capacity utilization"', '"available seat miles"', '"square feet"', '"number of stores"', '"data center capacity"'],
    "단위경제": ['"monthly active users"', '"daily active users"', '"average revenue per user"', '"gross merchandise"', '"take rate"', '"net revenue retention"', '"paid subscribers"'],
    "수주": ['"backlog"', '"remaining performance obligations"', '"book-to-bill"', '"order intake"'],
    "인원": ['"full-time employees"', '"headcount"'],
    "가격": ['"average selling price"', '"average realized price"', '"price per unit"'],
}


def 머리():
    c = os.environ.get("SEC_CONTACT_EMAIL")
    if not c:
        return None
    return {"User-Agent": "DCF-research %s" % c, "Accept-Encoding": "gzip, deflate"}


def 검색(문구, 부터, 까지, cik=None, 양식="10-K", H=None):
    import requests                                      # noqa: PLC0415
    p = {"q": 문구, "forms": 양식, "dateRange": "custom", "startdt": 부터, "enddt": 까지}
    if cik:
        p["ciks"] = "%010d" % int(cik)
    for i in range(3):
        try:
            r = requests.get(주소, params=p, headers=H, timeout=60)
            if r.status_code == 200:
                j = r.json()
                hits = (j.get("hits") or {})
                return {"건수": (hits.get("total") or {}).get("value"), "제출건": [
                    {"adsh": h["_source"].get("adsh"), "양식": h["_source"].get("form"), "기간": h["_source"].get("period_ending"),
                     "제출일": h["_source"].get("file_date"), "회사": (h["_source"].get("display_names") or [""])[0], "sic": (h["_source"].get("sics") or [""])[0]}
                    for h in hits.get("hits", [])[:50]]}
            time.sleep(1.0 * (i + 1))
        except Exception:                                # noqa: BLE001
            time.sleep(1.0 * (i + 1))
    return None


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="EDGAR 전문검색 — 어느 제출인이 어떤 운영지표 문구를 공시하나")
    ap.add_argument("--cik", help="대상 CIK(숫자)")
    ap.add_argument("--문구", nargs="*", help="더 볼 문구(따옴표 포함 구문)")
    ap.add_argument("--동종", help="같은 SIC(4자리) 공시 회사 수를 함께 센다 — 전체 검색 결과의 sics 로 거른다")
    ap.add_argument("--전체", action="store_true", help="CIK 없이 전 제출인에서 문구를 센다")
    ap.add_argument("--부터", default="%d-01-01" % (datetime.date.today().year - 2))
    ap.add_argument("--까지", default=datetime.date.today().isoformat())
    ap.add_argument("--양식", default="10-K")
    ap.add_argument("--낼", help="산출 경로(기본: ./_raw/운영지표공시.json)")
    a = ap.parse_args()
    H = 머리()
    if H is None:
        print("환경변수 SEC_CONTACT_EMAIL 이 없다 — 값은 화면에 적지 않는다")
        return 입력오류
    if not a.cik and not a.전체:
        ap.error("--cik 또는 --전체")
    문구들 = [q for qs in 문구사전.values() for q in qs] + list(a.문구 or [])
    낸 = {"형식": "운영지표공시 1", "만든날": datetime.date.today().isoformat(), "입력": {"cik": a.cik, "동종SIC": a.동종, "양식": a.양식, "기간": [a.부터, a.까지], "문구수": len(문구들)},
         "출처": 주소, "확인상태": "참고(EDGAR 전문검색 — 문구 색인. 값이 아니라 「어느 제출건이 이 문구를 쓰나」)", "대상": [], "동종": [], "신호": []}
    쓰는 = []
    for q in 문구들:
        if a.cik:
            r = 검색(q, a.부터, a.까지, a.cik, a.양식, H)
            time.sleep(0.15)
            if r is None:
                낸["대상"].append({"문구": q, "건수": None, "제출건": [], "비고": "응답 없음"})
                continue
            낸["대상"].append(dict(문구=q, **r))
            if r["건수"]:
                쓰는.append(q)
        if a.전체 or a.동종:
            r = 검색(q, a.부터, a.까지, None, a.양식, H)
            time.sleep(0.15)
            if r is None:
                continue
            동 = [h for h in r["제출건"] if (not a.동종 or h.get("sic") == a.동종)]
            낸["동종"].append({"문구": q, "전체건수": r["건수"], "같은SIC_보기": len(동), "보기": 동[:10]})
    낸["신호"].append({"출처": "sec_fulltext", "종류": "공시하는 운영지표 문구", "대상": a.cik or "전체", "값": len(쓰는), "문턱": None,
                    "글": "10-K 본문이 쓰는 운영지표 문구 %d개 — %s. B1 「이 회사가 어떤 운영지표를 공시하나」 칸의 재료(값은 원문에서 읽는다)" % (len(쓰는), " · ".join(쓰는)[:200]), "등급": "참고"})
    if a.cik and a.동종:
        동만 = [d["문구"] for d in 낸["동종"] if d["같은SIC_보기"] and d["문구"] not in 쓰는]
        if 동만:
            낸["신호"].append({"출처": "sec_fulltext", "종류": "동종은 쓰는데 대상은 안 쓰는 문구", "대상": a.cik, "값": len(동만), "문턱": None,
                            "글": "같은 SIC 의 10-K 가 쓰는데 대상은 안 쓰는 문구 — %s. 분모(시장 통계)를 그 지표로 세울 때 대상의 대응 지표를 찾는다" % " · ".join(동만)[:200], "등급": "참고"})
    p = a.낼 or os.path.join(os.getcwd(), "_raw", "운영지표공시.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, "w", encoding="utf-8").write(json.dumps(낸, ensure_ascii=False, indent=1))
    print("운영지표 공시 색인 — 대상 문구 %d(쓰는 %d) · 동종 %d → %s" % (len(낸["대상"]), len(쓰는), len(낸["동종"]), p))
    for s in 낸["신호"]:
        print("   · [%s] %s — %s" % (s["등급"], s["종류"], s["글"][:160]))
    return 통과


if __name__ == "__main__":
    sys.exit(main())

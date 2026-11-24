# -*- coding: utf-8 -*-
"""BLS QCEW — 미국 산업(NAICS)별 고용 · 임금 분기 시계열을 키 없이 받아 인원(501) · 임금상승률(504)의 산업 범위 재료로 낸다 (제안 D-미국 · 2026-10-22 신설).

무엇을 하나
  `data.bls.gov/cew/data/api/{year}/{qtr}/industry/{naics}.csv` 는 Quarterly Census of Employment and Wages 의 산업 슬라이스(지역 × 소유 형태)를 CSV 로 준다
  (키 없음 · 2026-10-22 실측: NAICS 3254 · 10 은 200, **SIC 4자리(2834)는 404** — QCEW 는 NAICS 다). 전국(US000) · 민간(own_code 5) 행의
  month3_emplvl(분기 말 고용) · avg_wkly_wage(주당 평균 임금)를 연도별로 모아 **산업 인원 증가율 · 임금 상승률**의 시계열을 낸다.
  거시지표 규칙과 같은 자리 — 확인상태 「참고(공개 통계 API)」 · 회사 값을 대신하지 않는다 · 501 · 504 의 **범위 재료**(거친 바퀴 범위출처 「산업 통계」)다.

SIC → NAICS(2026-10-23)
  SEC 가 주는 산업 코드는 SIC(1987) 이고 QCEW 는 NAICS 다. 사람이 손으로 적지 않는다 — 미국 통계청의 공개 대응표(`census.gov/naics/concordances/1987_SIC_to_1997_NAICS.xls`,
  키 없음)를 공용 캐시(`~/.dcf캐시/naics/`)에 한 번 받아 `--sic` 로 준 SIC 의 NAICS 후보를 뽑는다. 후보의 4자리(산업군)가 **하나면 그대로 쓰고**(근거에 대응표를 적는다),
  여럿이면(SIC 가 NAICS 여러 군에 갈린다 — 예: 3711 자동차 → 3361 · 3362 · 3369) 후보 전부를 보이고 멈춘다 — `--naics` 로 고른 것이 근거 칸에 간다.
  대응표는 1997 NAICS 라 그 뒤 개정(2002~2022)에서 번호가 바뀐 군은 QCEW 가 404 를 낸다 — 그때 3자리(부문)로 한 칸 물러나 다시 두드리고 그 사실을 적는다.

사용
  python 스크립트/bls_qcew.py --sic 2834 [--부터 2015] [--까지 2025] [--낼 _raw/산업임금.json]      # SIC → NAICS 후보 → 유일하면 자동
  python 스크립트/bls_qcew.py --naics 3254 …                                                        # NAICS 를 직접
내는 것 — {형식 · 만든날 · 입력{naics · sic · 대응후보 · 고른까닭} · 출처 · 확인상태 · 연도별[{연도 · 고용(4분기 말) · 주당임금(4분기 평균) · 고용증가율 · 임금상승률}] ·
          범위{고용증가율 · 임금상승률: [최저, 최고, 중앙값]} · 제안[{자리 "A-504 …" · 근거범위 · 딱지 "[관측 — 산업 통계(QCEW NAICS …)]"}] · 신호[]}
종료 코드 — 0 통과 · 2 입력오류(연도 하나도 못 받음 · NAICS 도 SIC 도 없음 · SIC 후보가 여럿인데 --naics 없음 — 후보를 찍고 멈춘다).
회사 · 업종 이름은 이 도구에 없다(범용).
"""
from __future__ import annotations

import argparse
import csv
import datetime
import io
import json
import os
import statistics
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

주소 = "https://data.bls.gov/cew/data/api/%d/%d/industry/%s.csv"
대응표주소 = "https://www.census.gov/naics/concordances/1987_SIC_to_1997_NAICS.xls"


def 공용뿌리():
    return (os.environ.get("DCF_공용캐시") or os.environ.get("DCF_SHARED_CACHE") or os.path.join(os.path.expanduser("~"), ".dcf캐시"))


def 대응표받기(H):
    """공용 캐시의 대응표(.xls) 경로 — 없으면 받는다. 못 받으면 None."""
    d = os.path.join(공용뿌리(), "naics")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "1987_SIC_to_1997_NAICS.xls")
    if os.path.exists(p) and os.path.getsize(p) > 1000:
        return p
    try:
        import requests                                  # noqa: PLC0415
        r = requests.get(대응표주소, headers=H, timeout=120)
        if r.status_code == 200 and len(r.content) > 1000:
            io.open(p, "wb").write(r.content)
            return p
    except Exception:                                    # noqa: BLE001
        pass
    return None


def 대응읽기(p):
    """대응표 → {SIC 4자리: [(NAICS, 제목, 부분)]}. 표의 꼴: SIC · Part Indicator · SIC 제목 · 1997 NAICS · NAICS 제목(2026-10-23 실측)."""
    import xlrd                                          # noqa: PLC0415
    wb = xlrd.open_workbook(p)
    sh = wb.sheets()[0]
    낸 = {}
    for i in range(1, sh.nrows):
        r = [("%s" % c.value).strip() for c in sh.row(i)]
        if len(r) < 4:
            continue
        sic, 부분, 제목, naics = r[0].split(".")[0], r[1], r[2], r[3].split(".")[0]
        if len(sic) == 4 and sic.isdigit() and naics.isdigit():
            낸.setdefault(sic, []).append((naics, (r[4] if len(r) > 4 else "").strip(), 부분))
    return 낸


def 후보(sic, 대응):
    """SIC → NAICS 후보(6자리 목록)와 4자리 산업군 집합."""
    목 = 대응.get(("%s" % sic).zfill(4), [])
    군 = sorted({n[:4] for n, _t, _p in 목})
    return 목, 군


def 받기(연도, 분기, naics, H):
    import requests                                      # noqa: PLC0415
    for i in range(3):
        try:
            r = requests.get(주소 % (연도, 분기, naics), headers=H, timeout=120)
            if r.status_code == 404:
                return None
            if r.status_code == 200:
                rows = list(csv.DictReader(io.StringIO(r.text)))
                us = [x for x in rows if x.get("area_fips") == "US000" and x.get("own_code") == "5"]
                if not us:
                    us = [x for x in rows if x.get("area_fips") == "US000"]
                if not us:
                    return None
                x = us[0]
                return {"고용": float(x.get("month3_emplvl") or 0) or None, "주당임금": float(x.get("avg_wkly_wage") or 0) or None,
                        "사업체": float(x.get("qtrly_estabs") or 0) or None, "분기임금총액": float(x.get("total_qtrly_wages") or 0) or None}
            time.sleep(1.0 * (i + 1))
        except Exception:                                # noqa: BLE001
            time.sleep(1.0 * (i + 1))
    return None


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="BLS QCEW — NAICS 산업의 고용 · 임금 시계열(인원 · 임금상승률 범위 재료)")
    ap.add_argument("--naics", help="NAICS 코드(2~6자리 — 10 은 전 산업)")
    ap.add_argument("--sic", help="SEC 의 SIC 4자리 — 통계청 대응표로 NAICS 후보를 뽑는다(유일하면 자동)")
    ap.add_argument("--부터", type=int, default=2015)
    ap.add_argument("--까지", type=int, default=datetime.date.today().year - 1)
    ap.add_argument("--낼", help="산출 경로(기본: ./_raw/산업임금.json)")
    a = ap.parse_args()
    H = {"User-Agent": "DCF-research %s" % (os.environ.get("SEC_CONTACT_EMAIL") or "research")}
    naics, 대응후보, 고른까닭 = a.naics, [], None
    if a.sic:
        p = 대응표받기(H)
        if not p:
            print("입력오류 — SIC → NAICS 대응표(%s)를 받지 못했다. --naics 로 준다" % 대응표주소)
            return 입력오류
        목, 군 = 후보(a.sic, 대응읽기(p))
        대응후보 = [{"naics": n, "제목": t, "부분": pt} for n, t, pt in 목]
        if not 목:
            print("입력오류 — SIC %s 가 대응표에 없다. --naics 로 준다" % a.sic)
            return 입력오류
        if naics:
            고른까닭 = "--naics %s (대응 후보 %s 가운데 사람이 고름)" % (naics, " · ".join(군))
        elif len(군) == 1:
            naics = 군[0]
            고른까닭 = "SIC %s → NAICS 4자리 %s 하나(통계청 1987 SIC → 1997 NAICS 대응표 · 후보 %d개가 같은 군)" % (a.sic, naics, len(목))
        else:
            print("SIC %s 는 NAICS 산업군 %d개에 갈린다 — 후보를 보이고 멈춘다. --naics 로 고른다(근거 칸에 적는다)" % (a.sic, len(군)))
            for n, t, pt in 목:
                print("   %s  %s%s" % (n, t, " (일부)" if pt else ""))
            return 입력오류
    if not naics:
        ap.error("--naics 또는 --sic")
    연도별 = []
    쓴naics = naics
    for y in range(a.부터, a.까지 + 1):
        q4 = 받기(y, 4, 쓴naics, H)
        time.sleep(0.3)
        if q4 is None and 쓴naics == naics and len(naics) >= 4 and y == a.부터:
            # 1997 NAICS 가 뒤 개정에서 없어진 군이면 404 — 3자리로 한 칸 물러난다
            q4 = 받기(y, 4, naics[:3], H)
            if q4 is not None:
                쓴naics = naics[:3]
                고른까닭 = (고른까닭 or "") + " · QCEW 가 %s 를 404 로 거절해 3자리 %s 로 물러남" % (naics, 쓴naics)
        if q4 is None:
            continue
        임금 = [받기(y, q, 쓴naics, H) for q in (1, 2, 3)] + [q4]
        time.sleep(0.3)
        임금들 = [x["주당임금"] for x in 임금 if x and x.get("주당임금")]
        연도별.append({"연도": y, "고용": q4["고용"], "주당임금": round(statistics.mean(임금들), 2) if 임금들 else q4["주당임금"], "사업체": q4["사업체"]})
    if not 연도별:
        print("입력오류 — NAICS %s 의 연도를 하나도 못 받았다(QCEW 는 NAICS 다 — SIC 가 아니다)" % naics)
        return 입력오류
    for i in range(1, len(연도별)):
        p, c = 연도별[i - 1], 연도별[i]
        c["고용증가율"] = (c["고용"] / p["고용"] - 1) if (c["고용"] and p["고용"]) else None
        c["임금상승률"] = (c["주당임금"] / p["주당임금"] - 1) if (c["주당임금"] and p["주당임금"]) else None
    def 범위(k):
        v = [x[k] for x in 연도별 if x.get(k) is not None]
        return [round(min(v), 4), round(max(v), 4), round(statistics.median(v), 4)] if v else None
    범 = {"고용증가율": 범위("고용증가율"), "임금상승률": 범위("임금상승률")}
    제안 = []
    if 범["임금상승률"]:
        제안.append({"자리": "A-504 임금상승률(산업 통계 범위)", "값": None, "근거범위": 범["임금상승률"][:2], "딱지": "[관측 — 산업 통계(QCEW NAICS %s · 주당 평균 임금 연 상승률 %d~%d)]" % (쓴naics, 연도별[0]["연도"], 연도별[-1]["연도"]),
                   "확신": "중", "글": "산업 전체 임금 상승률의 연도별 최저 · 최고 — 회사 1인당 급여 추세의 하한 · 상한 재료(회사 값을 대신하지 않는다)"})
    if 범["고용증가율"]:
        제안.append({"자리": "A-501 인원 증가율(산업 통계 범위)", "값": None, "근거범위": 범["고용증가율"][:2], "딱지": "[관측 — 산업 통계(QCEW NAICS %s · 4분기 말 고용 연 증가율)]" % 쓴naics,
                   "확신": "약", "글": "산업 전체 고용 증가율의 연도별 최저 · 최고 — 회사 인원 경로의 참고 띠"})
    낸 = {"형식": "산업임금 1", "만든날": datetime.date.today().isoformat(), "입력": {"naics": 쓴naics, "sic": a.sic, "대응후보": 대응후보, "고른까닭": 고른까닭, "기간": [a.부터, a.까지]},
         "출처": 주소 % (0, 0, 쓴naics), "대응표": 대응표주소 if a.sic else None,
         "확인상태": "참고(공개 통계 API — 미 노동통계국 QCEW · 전국 · 민간 · 키 없음)", "연도별": 연도별, "범위": 범, "제안": 제안,
         "신호": [{"출처": "bls_qcew", "종류": "산업 임금 · 고용 범위", "대상": "NAICS %s" % 쓴naics, "값": 범["임금상승률"][2] if 범["임금상승률"] else None, "문턱": None,
                 "글": "NAICS %s 임금 상승률 연 %s · 고용 증가율 %s(최저 · 최고 · 중앙값) — 504 · 501 의 산업 범위 재료%s" % (쓴naics, 범["임금상승률"], 범["고용증가율"], (" · " + 고른까닭) if 고른까닭 else ""), "등급": "참고"}]}
    p = a.낼 or os.path.join(os.getcwd(), "_raw", "산업임금.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, "w", encoding="utf-8").write(json.dumps(낸, ensure_ascii=False, indent=1))
    print("QCEW NAICS %s%s — %d~%d · 임금상승률 %s · 고용증가율 %s → %s" % (쓴naics, (" (SIC %s 에서)" % a.sic) if a.sic else "", 연도별[0]["연도"], 연도별[-1]["연도"], 범["임금상승률"], 범["고용증가율"], p))
    return 통과


if __name__ == "__main__":
    sys.exit(main())

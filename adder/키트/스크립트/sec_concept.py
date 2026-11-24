# -*- coding: utf-8 -*-
"""frames 로 안 잡히는 후보를 개별 보충한다 — companyconcept 창구.

왜 필요한가
  - **IFRS 제출인(20-F 일부)은 us-gaap 프레임에 아예 없다.** 실측: BTDR·ARBK·ALP 는
    `us-gaap/Assets` 가 404 이고 `ifrs-full/Assets` 로만 온다. 프레임만 보면
    「자료 없음」으로 조용히 빠진다 — 실은 **택소노미가 다른 것**이다(탈락사유 2 중 조회 경로 문제).
  - CY 프레임은 12월 결산 위주라 6월·3월·5월 결산 회사의 최신 분기가 안 들어온다.
    평가기준일(2026-06-30) 직전 값을 쓰려면 개별 조회가 필요하다.

결과는 _raw/peers/cc_{티커}.json 에 캐시한다.

사용:  python 스크립트/sec_concept.py --tickers BTDR,ARBK --기준일 2026-06-30 [--병렬 8]
병렬(2026-10-18 손개입 개선 1) — 회사마다 스레드로 나란히, 요청 간격은 모든 스레드가 함께 0.11초(SEC 10요청/초). 실측 직렬 40초/곳 → 60곳 몇 분.
로컬 먼저(2026-10-24 W17) — 공용 캐시의 companyfacts(`cf로컬.py` · 패널 도구가 받아 둔 zip · 회사 파일)에서 먼저 읽고, 그 회사가 로컬에 없을 때만
companyconcept 를 부른다(`--네트워크만` 이면 종전대로). 같은 사실이라 값은 같다 — 외국 소형 신고인 여덟 곳 509초(META 조사)가 몇 초로.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEER = os.environ.get("DCF_PEER_CACHE") or os.path.join(ROOT, "_raw", "peers")   # 손개입 개선 1 — 사슬 `--캐시` 가 환경변수로 닿는다(종전에는 하위 도구가 키트 _raw/peers 에 썼다)

contact = os.environ.get("SEC_CONTACT_EMAIL")
if not contact:
    sys.exit("환경변수 SEC_CONTACT_EMAIL 이 없습니다.")
H = {"User-Agent": "DCF-research %s" % contact, "Accept-Encoding": "gzip, deflate"}

# (우리 이름, us-gaap 후보들, ifrs-full 후보들, 시점형 여부)
개념 = [
    ("매출", ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
            "RevenueFromContractWithCustomerIncludingAssessedTax"],
     ["Revenue", "RevenueFromContractsWithCustomers"], False),
    ("영업이익", ["OperatingIncomeLoss"],
     ["ProfitLossFromOperatingActivities"], False),
    ("순이익", ["NetIncomeLoss", "ProfitLoss"], ["ProfitLoss"], False),
    ("자산", ["Assets"], ["Assets"], True),
    ("부채", ["Liabilities"], ["Liabilities"], True),
    ("자본", ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
     ["Equity", "EquityAttributableToOwnersOfParent"], True),
    ("현금", ["CashAndCashEquivalentsAtCarryingValue"], ["CashAndCashEquivalents"], True),
    # 현금보정 βU 의 분자다 — 현금만 쓰면 현금비중이 과소로 잡혀 보정 βU 가 낮게 나온다.
    # 실측(TSLA 회차): 테슬라 본인이 현금 15,219 · 단기투자 28,305 라 단기투자가 두 배 가까이 크다.
    ("단기투자", ["ShortTermInvestments", "OtherShortTermInvestments",
              "MarketableSecuritiesCurrent",
              "AvailableForSaleSecuritiesDebtSecuritiesCurrent"],
     ["CurrentInvestments", "OtherCurrentFinancialAssets"], True),
    ("차입금_장기", ["LongTermDebtNoncurrent", "LongTermDebt"],
     ["NoncurrentPortionOfNoncurrentBorrowings", "Borrowings"], True),
    ("차입금_유동", ["LongTermDebtCurrent", "DebtCurrent"],
     ["CurrentPortionOfNoncurrentBorrowings", "ShorttermBorrowings"], True),
    ("리스부채_비유동", ["OperatingLeaseLiabilityNoncurrent", "FinanceLeaseLiabilityNoncurrent"],
     ["NoncurrentLeaseLiabilities"], True),
    ("리스부채_유동", ["OperatingLeaseLiabilityCurrent", "FinanceLeaseLiabilityCurrent"],
     ["CurrentLeaseLiabilities"], True),
    ("전환사채", ["ConvertibleNotesPayable", "ConvertibleNotesPayableNoncurrent",
              "ConvertibleDebtNoncurrent", "ConvertibleDebt"], [], True),
    ("주식수", [], [], None),   # dei 로 따로
]

호출, 캐시 = 0, 0
_잠금 = threading.Lock()
_마지막 = [0.0]
간격 = 0.11                 # SEC 10요청/초 — 스레드가 몇이든 공용 간격(손개입 개선 1 · 병렬)


def 간격두기():
    """모든 스레드가 함께 지키는 최소 간격 — 요청 사이 `간격` 초."""
    with _잠금:
        now = time.time()
        기다림 = _마지막[0] + 간격 - now
        if 기다림 > 0:
            time.sleep(기다림)
        _마지막[0] = time.time()


def get(url):
    global 호출
    for i in range(3):
        try:
            with _잠금:
                호출 += 1
            간격두기()
            r = requests.get(url, headers=H, timeout=60)
            if r.status_code in (200, 404):
                return r
        except requests.RequestException:
            pass
        time.sleep(1.0 * (i + 1))
    return None


_로컬 = [None]
로컬적중 = [0]


def concept(cik, tax, tag):
    L = _로컬[0]
    if L is not None and L.쓸수있음:
        있음, j = L.개념(cik, tax, tag)
        if 있음:
            with _잠금:
                로컬적중[0] += 1
            return j
    url = "https://data.sec.gov/api/xbrl/companyconcept/CIK%010d/%s/%s.json" % (cik, tax, tag)
    r = get(url)
    if r is None or r.status_code != 200:
        return None
    return r.json()


def 고르기(j, 기준일, 시점형):
    """평가기준일 이전(포함) 중 가장 최근 값. 기간형은 duration 이 300일 이상인 것(연간)."""
    best = None
    for u, arr in j.get("units", {}).items():
        if u not in ("USD",):
            continue
        for x in arr:
            if x["end"] > 기준일:
                continue
            if 시점형:
                if x.get("start"):
                    continue
            else:
                if not x.get("start"):
                    continue
                import datetime as dt
                d0 = dt.date.fromisoformat(x["start"])
                d1 = dt.date.fromisoformat(x["end"])
                if (d1 - d0).days < 300:
                    continue
            if best is None or (x["end"], x.get("fy") or 0) > (best["end"], best.get("fy") or 0):
                best = x
    return best


def 한곳(t, 기준일):
    """한 회사의 개념 보충 → 화면 줄 목록(스레드가 나란히 돈다 — 캐시 파일은 회사마다 따로라 겹치지 않는다)."""
    global 캐시
    줄 = []
    p = os.path.join(PEER, "cc_%s.json" % t)
    if os.path.exists(p):
        with _잠금:
            캐시 += 1
        d = json.load(io.open(p, encoding="utf-8"))
        줄.append("%-7s [캐시] %s" % (t, {k: (("%.0fm" % (v["val"] / 1e6)) if v else None)
                                        for k, v in d["값"].items()}))
        return 줄
    sp = os.path.join(PEER, "sub_%s.json" % t)
    if not os.path.exists(sp):
        줄.append("%-7s *** sub_%s.json 없음 — sec_peer_meta.py 먼저" % (t, t))
        return 줄
    m = json.load(io.open(sp, encoding="utf-8"))
    cik = m["cik"]
    결과, 태그쓴것 = {}, {}
    for 이름, ug, ifr, 시점형 in 개념:
        if 시점형 is None:
            continue
        # 2026-10-24 W17 — 첫 태그에서 멈추되, 그 값이 기준일보다 1년 넘게 묵었으면 다음 태그도 보고 가장 늦은 값을 쓴다
        # (AAPL 매출이 `Revenues` 2018 값으로 잡히던 결함 — 회사가 태그를 바꾸면 옛 태그에 옛 값만 남는다)
        hit, 후보 = None, []
        묵음선 = "%04d%s" % (int(기준일[:4]) - 1, 기준일[4:])
        for tax, tags in (("us-gaap", ug), ("ifrs-full", ifr)):
            for tag in tags:
                j = concept(cik, tax, tag)
                if not j:
                    continue
                v = 고르기(j, 기준일, 시점형)
                if v:
                    후보.append((v["end"], v, "%s/%s" % (tax, tag)))
                    if v["end"] >= 묵음선:
                        break
            if 후보 and 후보[-1][0] >= 묵음선:
                break
        if 후보:
            _e, hit, 태그쓴것[이름] = max(후보, key=lambda x: x[0])
        결과[이름] = hit
    # dei 주식수
    j = concept(cik, "dei", "EntityCommonStockSharesOutstanding")
    주식 = None
    if j:
        for u, arr in j.get("units", {}).items():
            for x in arr:
                if x["end"] <= 기준일 and (주식 is None or x["end"] > 주식["end"]):
                    주식 = x
    결과["주식수"] = 주식
    if 주식:
        태그쓴것["주식수"] = "dei/EntityCommonStockSharesOutstanding"
    d = {"티커": t, "cik": cik, "회사명": m.get("name"), "기준일": 기준일,
         "값": 결과, "쓴태그": 태그쓴것}
    json.dump(d, io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    줄.append("%-7s [신규] %s" % (t, {k: (("%s %.0fm" % (v["end"], v["val"] / 1e6)) if v else None)
                                    for k, v in 결과.items() if k != "주식수"}))
    줄.append("        주식수: %s" % (("%s %d" % (주식["end"], 주식["val"])) if 주식 else "확인 불가"))
    return 줄


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--tickers", required=True)
    ap.add_argument("--기준일", default="2026-06-30")
    ap.add_argument("--병렬", type=int, default=8, help="회사를 나란히 돌리는 스레드 수(기본 8 — SEC 10요청/초 안의 공용 간격 0.11초)")
    ap.add_argument("--네트워크만", action="store_true", help="공용 캐시 companyfacts 를 쓰지 않는다(종전 동작)")
    a = ap.parse_args()
    if not a.네트워크만:
        try:
            import cf로컬
            _로컬[0] = cf로컬.로컬(a.기준일)
            print("  로컬 companyfacts — %s" % ("판 %s" % _로컬[0].판 if _로컬[0].쓸수있음 else _로컬[0].까닭))
        except Exception as e:                                # noqa: BLE001
            print("  로컬 companyfacts 를 못 씀(%s) — 네트워크로" % type(e).__name__)
    티커 = [x.strip().upper() for x in a.tickers.split(",") if x.strip()]
    t0 = time.time()
    실패 = []

    def 안전(t):
        """2026-10-24 W16 — 한 곳의 실패(응답 꼴 · 키 · 네트워크)가 일괄 전체를 멈추던 결함(유니버스 조사 물결 실측).
        곳마다 실패를 적고 계속 간다(sec_외화개념 과 같은 꼴 — `cc_실패.json`)."""
        try:
            return 한곳(t, a.기준일)
        except Exception as e:                                # noqa: BLE001
            실패.append({"티커": t, "오류": "%s: %s" % (type(e).__name__, str(e)[:200])})
            return ["%-7s *** 실패 — %s(곳마다 기록 · 계속)" % (t, type(e).__name__)]
    with ThreadPoolExecutor(max(1, a.병렬)) as ex:
        for 줄 in ex.map(안전, 티커):
            for x in 줄:
                print(x)
    if 실패:
        json.dump(실패, io.open(os.path.join(PEER, "cc_실패.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("  실패 %d곳 — cc_실패.json" % len(실패))
    print("\n네트워크 호출 %d · 로컬 companyfacts %d · 캐시 적중 %d · %.0f초 · 병렬 %d" % (호출, 로컬적중[0], 캐시, time.time() - t0, a.병렬))


if __name__ == "__main__":
    main()

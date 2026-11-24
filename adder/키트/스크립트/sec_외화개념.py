# -*- coding: utf-8 -*-
"""[본체 승격 2026-09-10 · HWO-54] TSLA 회차의 `tsla_외화개념.py` 를 그대로 올렸다 —
원래부터 티커 인자만 받는 일반형이었고, 회차 전용은 이름뿐이었다. 외국 신고인
(20-F·IFRS)·다종류 주식 예외는 회차마다 나오므로 회차 스크립트로 다시 짜지 않는다.

표시통화가 USD 가 아닌 SEC 제출인(20-F FPI)의 주요계정을 **통화째로** 받는다.

`sec_concept.py` 는 `units` 에서 USD 만 본다. 그래서 엔·유로·위안으로 태깅하는
TM·HMC·STLA·RACE·XPEV 가 「자료 없음」으로 위장됐다(실측). 이 스크립트는
**어떤 통화 단위든 받아 통화와 함께 적는다.** 환산은 여기서 하지 않는다 —
비율 지표(영업이익률·D/E·성장률)는 통화와 무관하므로 그쪽부터 쓴다.

결과: _raw/peers/fx_{티커}.json

로컬 먼저(2026-10-24 W17) — 공용 캐시 companyfacts(`cf로컬.py`)에서 먼저 읽고 그 회사가 로컬에 없을 때만 companyconcept 를 부른다
(`--네트워크만` 이면 종전대로). 곳당 개념 스물 안팎을 직렬로 불러 곳당 1분 — 외국 소형 신고인 여덟 곳 509초(META 조사 실측)였다.
"""
from __future__ import annotations
import argparse, io, json, os, sys, time, datetime as dt
import requests
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEER = os.environ.get("DCF_PEER_CACHE") or os.path.join(ROOT, "_raw", "peers")   # 손개입 개선 1 — 사슬 `--캐시` 가 환경변수로 닿는다(종전에는 하위 도구가 키트 _raw/peers 에 썼다)
contact = os.environ.get("SEC_CONTACT_EMAIL")
if not contact:
    sys.exit("환경변수 SEC_CONTACT_EMAIL 이 없습니다.")
H = {"User-Agent": "DCF-research %s" % contact, "Accept-Encoding": "gzip, deflate"}
호출 = [0]

개념 = [
    ("매출", ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"],
     ["Revenue", "RevenueFromContractsWithCustomers"], False),
    ("영업이익", ["OperatingIncomeLoss"], ["ProfitLossFromOperatingActivities"], False),
    ("순이익", ["NetIncomeLoss", "ProfitLoss"], ["ProfitLoss"], False),
    ("자산", ["Assets"], ["Assets"], True),
    ("부채", ["Liabilities"], ["Liabilities"], True),
    ("자본", ["StockholdersEquity"], ["Equity", "EquityAttributableToOwnersOfParent"], True),
    ("현금", ["CashAndCashEquivalentsAtCarryingValue"], ["CashAndCashEquivalents"], True),
    ("차입금_장기", ["LongTermDebtNoncurrent", "LongTermDebt"],
     ["NoncurrentPortionOfNoncurrentBorrowings", "Borrowings", "LongtermBorrowings"], True),
    ("차입금_유동", ["LongTermDebtCurrent", "DebtCurrent", "ShortTermBorrowings"],
     ["CurrentPortionOfNoncurrentBorrowings", "ShorttermBorrowings"], True),
]


_로컬 = [None]
로컬적중 = [0]


def 개념받기(cik, tax, tg):
    """→ companyconcept 꼴 dict 또는 None. 로컬에 그 회사가 있으면 로컬 답이 끝이다(태그가 없으면 None — 네트워크로 다시 묻지 않는다)."""
    L = _로컬[0]
    if L is not None and L.쓸수있음:
        있음, j = L.개념(cik, tax, tg)
        if 있음:
            로컬적중[0] += 1
            return j
    r = get("https://data.sec.gov/api/xbrl/companyconcept/CIK%010d/%s/%s.json" % (cik, tax, tg))
    if r is None or r.status_code != 200:
        return None
    return r.json()


def get(url):
    for i in range(3):
        try:
            호출[0] += 1
            r = requests.get(url, headers=H, timeout=60)
            if r.status_code in (200, 404):
                time.sleep(0.12)
                return r
        except requests.RequestException:
            pass
        time.sleep(1.0 * (i + 1))
    return None


def 고르기(j, 기준일, 시점형):
    """통화 무관. 평가기준일 이전 가장 최근 값 — (통화, 값, end, 태그)."""
    best = None
    for u, arr in j.get("units", {}).items():
        if len(u) != 3:          # USD/JPY/EUR/CNY 같은 통화 단위만
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
                d0 = dt.date.fromisoformat(x["start"])
                d1 = dt.date.fromisoformat(x["end"])
                if (d1 - d0).days < 300:
                    continue
            if best is None or x["end"] > best[2]:
                best = (u, x["val"], x["end"])
    return best


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--tickers", required=True)
    ap.add_argument("--기준일", default="2026-06-30")
    ap.add_argument("--네트워크만", action="store_true", help="공용 캐시 companyfacts 를 쓰지 않는다(종전 동작)")
    a = ap.parse_args()
    if not a.네트워크만:
        try:
            import cf로컬
            _로컬[0] = cf로컬.로컬(a.기준일)
            print("  로컬 companyfacts — %s" % ("판 %s" % _로컬[0].판 if _로컬[0].쓸수있음 else _로컬[0].까닭))
        except Exception as e:                                # noqa: BLE001
            print("  로컬 companyfacts 를 못 씀(%s) — 네트워크로" % type(e).__name__)
    실패 = []
    for t in [x.strip().upper() for x in a.tickers.split(",") if x.strip()]:
        p = os.path.join(PEER, "fx_%s.json" % t)
        if os.path.exists(p):
            print("%-7s [캐시]" % t)
            continue
        # 곳마다 따로 — 한 곳(메타 없는 비신고인 · 장외 종목 따위)의 실패가 큐 전체를 멈추지 않게(2026-10-24 W15 · 마이크론 시범)
        try:
            m = json.load(io.open(os.path.join(PEER, "sub_%s.json" % t), encoding="utf-8"))
            cik = int(m["cik"])
        except (OSError, ValueError, KeyError, TypeError) as e:
            실패.append((t, "메타(sub_%s.json) 없음 또는 cik 없음 — %s" % (t, type(e).__name__)))
            print("%-7s *** 건너뜀: 메타 · cik 없음(SEC 신고인이 아닐 수 있다)" % t)
            continue
        값, 태그 = {}, {}
        for 이름, ug, ifr, 시점형 in 개념:
            # 2026-10-24 W17 — 첫 태그의 값이 기준일보다 1년 넘게 묵었으면 다음 태그도 보고 가장 늦은 값(sec_concept 와 같은 규칙)
            hit, 후보 = None, []
            묵음선 = "%04d%s" % (int(a.기준일[:4]) - 1, a.기준일[4:])
            for tax, tags in (("ifrs-full", ifr), ("us-gaap", ug)):
                for tg in tags:
                    j = 개념받기(cik, tax, tg)
                    if not j:
                        continue
                    v = 고르기(j, a.기준일, 시점형)
                    if v:
                        후보.append((v[2], v, "%s/%s" % (tax, tg)))
                        if v[2] >= 묵음선:
                            break
                if 후보 and 후보[-1][0] >= 묵음선:
                    break
            if 후보:
                _e, hit, 태그[이름] = max(후보, key=lambda x: x[0])
            값[이름] = hit
        json.dump({"티커": t, "cik": cik, "회사명": m.get("name"), "값": 값, "쓴태그": 태그},
                  io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("%-7s %s" % (t, {k: (("%s %.0fm %s" % (v[0], v[1] / 1e6, v[2])) if v else None)
                               for k, v in 값.items()}))
    print("\n네트워크 호출 %d · 로컬 companyfacts %d" % (호출[0], 로컬적중[0]))
    for t, w in 실패:
        print("  실패 %s: %s" % (t, w))
    if 실패:
        json.dump([{"티커": t, "까닭": w} for t, w in 실패], io.open(os.path.join(PEER, "fx_실패.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

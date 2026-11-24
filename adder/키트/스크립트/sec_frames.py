# -*- coding: utf-8 -*-
"""싼 층 — SEC XBRL frames 창구로 **전 제출인의 주요계정을 한 호출씩** 받는다.

국내(DART)의 `fnlttMultiAcnt` 100곳 묶음에 해당하는 미국 창구다.
`https://data.sec.gov/api/xbrl/frames/us-gaap/{태그}/USD/{기간}.json` 는
그 기간·그 태그를 올린 **모든 제출인**을 한 번에 준다. 후보 전원을 훑는 데 십여 호출이면 끝난다.

한계(반드시 적는다):
- **CY2025(연간) 프레임에는 12월 결산이 아닌 회사가 안 들어온다.** 6월·9월·3월 결산
  회사(IREN·CLSK·HIVE·APLD 등)는 여기서 빈다 → `sec_concept.py` 로 개별 보충한다.
- **12월 결산 회사인데도 프레임에서 빠지는 자리가 있다.** SEC 의 프레임 선정이
  제출인의 모든 값을 담지 않는다 — **회사가 값을 올렸는데도 그 프레임에 안 들어온다.**
  실측(RXRX 배수 회차 2026-09-09): CY2025 매출 프레임에 안 잡힌 13곳에
  `companyconcept` 를 걸었더니 **GLUE 123,672천USD · ABSI 2,800천USD 가 실제로 있었다.**
  프레임만 보고 「매출 없음」으로 적으면 **매출이 있는 회사가 표에서 조용히 사라진다.**
  프레임에 없는 후보는 **자르기 전에 `sec_concept.py`(companyconcept)로 한 번 더 두드린다.**
- 태그가 회사마다 갈린다. 매출은 `Revenues` 와
  `RevenueFromContractWithCustomerExcludingAssessedTax` 와
  **`RevenueFromContractWithCustomerIncludingAssessedTax`** 를 **셋 다** 받아 합친다.
  한쪽만 보면 절반이 빈다 — 실측: GLUE 는 Including 쪽에만 값이 있었다.

결과는 _raw/peers/frame_{태그}_{기간}.json 에 캐시한다.

사용:  python 스크립트/sec_frames.py
"""
from __future__ import annotations

import io
import json
import os
import sys
import time

import requests

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEER = os.environ.get("DCF_PEER_CACHE") or os.path.join(ROOT, "_raw", "peers")   # 손개입 개선 1 — 사슬 `--캐시` 가 환경변수로 닿는다(종전에는 하위 도구가 키트 _raw/peers 에 썼다)
os.makedirs(PEER, exist_ok=True)

contact = os.environ.get("SEC_CONTACT_EMAIL")
if not contact:
    sys.exit("환경변수 SEC_CONTACT_EMAIL 이 없습니다.")
H = {"User-Agent": "DCF-research %s" % contact, "Accept-Encoding": "gzip, deflate"}

기간_기간형 = ["CY2023", "CY2024", "CY2025"]
기간_시점형 = ["CY2023Q4I", "CY2024Q4I", "CY2025Q4I"]
태그_기간형 = ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
           "RevenueFromContractWithCustomerIncludingAssessedTax",
           "OperatingIncomeLoss", "NetIncomeLoss"]
태그_시점형 = ["Assets", "Liabilities", "StockholdersEquity",
           "CashAndCashEquivalentsAtCarryingValue"]

캐시수, 신규수, 실패 = 0, 0, []


def frame(tag, per):
    global 캐시수, 신규수
    p = os.path.join(PEER, "frame_%s_%s.json" % (tag, per))
    if os.path.exists(p):
        캐시수 += 1
        return json.load(io.open(p, encoding="utf-8"))
    url = "https://data.sec.gov/api/xbrl/frames/us-gaap/%s/USD/%s.json" % (tag, per)
    for i in range(3):
        try:
            r = requests.get(url, headers=H, timeout=120)
            if r.status_code == 200:
                j = r.json()
                json.dump(j, io.open(p, "w", encoding="utf-8"), ensure_ascii=False)
                신규수 += 1
                time.sleep(0.25)
                return j
            if r.status_code == 404:
                실패.append("%s %s → 404 (그 프레임 없음)" % (tag, per))
                return None
        except requests.RequestException as e:
            실패.append("%s %s → %s" % (tag, per, type(e).__name__))
        time.sleep(1.2 * (i + 1))
    실패.append("%s %s → 조회 실패" % (tag, per))
    return None


def main():
    for tag in 태그_기간형:
        for per in 기간_기간형:
            j = frame(tag, per)
            print("%-52s %s" % ("%s %s" % (tag, per),
                                ("%d 제출인" % len(j["data"])) if j else "없음/실패"))
    for tag in 태그_시점형:
        for per in 기간_시점형:
            j = frame(tag, per)
            print("%-52s %s" % ("%s %s" % (tag, per),
                                ("%d 제출인" % len(j["data"])) if j else "없음/실패"))
    print("\n캐시 %d · 신규 %d · 실패 %d" % (캐시수, 신규수, len(실패)))
    for x in 실패:
        print("  ", x)


if __name__ == "__main__":
    main()

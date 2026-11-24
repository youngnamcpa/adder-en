# -*- coding: utf-8 -*-
"""후보 티커의 CIK·SIC·거래소·최근 제출 서류를 받아 _raw/peers/sub_{TICKER}.json 에 캐시한다.

싼~중간 층 사이의 도구다. 티커→CIK 는 company_tickers.json(캐시)에서 역조회하고,
CIK→SIC·거래소·회계연도말은 submissions 에서 읽는다. 캐시가 있으면 재조회하지 않는다.

사용:  python 스크립트/sec_peer_meta.py --tickers MARA,RIOT,CLSK
"""
from __future__ import annotations

import argparse
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


def get(url, tries=3):
    for i in range(tries):
        try:
            r = requests.get(url, headers=H, timeout=60)
            if r.status_code == 200:
                return r
        except requests.RequestException:
            pass
        time.sleep(1.0 * (i + 1))
    return None


def 티커표():
    p = os.path.join(PEER, "company_tickers.json")
    if os.path.exists(p):
        m = json.load(io.open(p, encoding="utf-8"))
    else:
        r = get("https://www.sec.gov/files/company_tickers.json")
        if r is None:
            sys.exit("company_tickers.json 조회 실패")
        m = {}
        for _, v in r.json().items():
            m.setdefault(str(int(v["cik_str"])), []).append(v["ticker"])
        json.dump(m, io.open(p, "w", encoding="utf-8"), ensure_ascii=False)
    rev = {}
    for cik, ts in m.items():
        for t in ts:
            rev[t.upper()] = int(cik)
    return rev


def meta(tic, rev):
    p = os.path.join(PEER, "sub_%s.json" % tic)
    if os.path.exists(p):
        return json.load(io.open(p, encoding="utf-8")), "캐시"
    cik = rev.get(tic)
    if cik is None:
        return {"ticker": tic, "실패": "company_tickers.json 에 티커 없음"}, "실패"
    r = get("https://data.sec.gov/submissions/CIK%010d.json" % cik)
    if r is None:
        return {"ticker": tic, "cik": cik, "실패": "submissions 조회 실패"}, "실패"
    s = r.json()
    rec = s["filings"]["recent"]
    폼 = {}
    for i in range(len(rec["form"])):
        f = rec["form"][i]
        if f in ("10-K", "20-F", "40-F", "10-Q") and f not in 폼:
            폼[f] = {"reportDate": rec["reportDate"][i], "filingDate": rec["filingDate"][i]}
    d = {"ticker": tic, "cik": cik, "name": s.get("name"),
         "sic": s.get("sic"), "sicDescription": s.get("sicDescription"),
         "exchanges": s.get("exchanges"), "tickers": s.get("tickers"),
         "fiscalYearEnd": s.get("fiscalYearEnd"),
         "stateOfIncorporation": s.get("stateOfIncorporation"),
         "최근서류": 폼,
         "제출건수": len(rec["form"]),
         "최초제출": min(rec["filingDate"]) if rec["filingDate"] else None}
    json.dump(d, io.open(p, "w", encoding="utf-8"), ensure_ascii=False)
    return d, "신규"


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--tickers", required=True)
    a = ap.parse_args()
    rev = 티커표()
    캐, 신, 실 = 0, 0, []
    print("%-7s %-6s %-34s %-30s %-10s %-6s %s"
          % ("티커", "SIC", "SIC설명", "회사명", "거래소", "FY말", "최근 연차보고"))
    for t in [x.strip().upper() for x in a.tickers.split(",") if x.strip()]:
        d, how = meta(t, rev)
        if how == "캐시":
            캐 += 1
        elif how == "신규":
            신 += 1
            time.sleep(0.2)
        if d.get("실패"):
            실.append((t, d["실패"]))
            print("%-7s %s" % (t, "*** 실패: " + d["실패"]))
            continue
        연차 = d["최근서류"].get("10-K") or d["최근서류"].get("20-F") or d["최근서류"].get("40-F") or {}
        폼명 = ("10-K" if "10-K" in d["최근서류"] else
              "20-F" if "20-F" in d["최근서류"] else
              "40-F" if "40-F" in d["최근서류"] else "-")
        print("%-7s %-6s %-34s %-30s %-10s %-6s %s %s"
              % (t, d.get("sic"), str(d.get("sicDescription"))[:34],
                 str(d.get("name"))[:30],
                 # exchanges 안에 null 이 섞인 제출인이 있다(실측 RXRX 회차: 한 곳에서
                 # TypeError 로 전체 루프가 죽어 뒤 후보가 통째로 안 받아졌다).
                 ",".join(x for x in (d.get("exchanges") or []) if x)[:10],
                 d.get("fiscalYearEnd"), 폼명, 연차.get("reportDate", "-")))
    print("\n캐시 %d · 신규 %d · 실패 %d" % (캐, 신, len(실)))
    for t, why in 실:
        print("  실패 %s: %s" % (t, why))


if __name__ == "__main__":
    main()

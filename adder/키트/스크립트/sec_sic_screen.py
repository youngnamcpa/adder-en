# -*- coding: utf-8 -*-
"""경로 ① — SEC 가 매긴 SIC 코드로 같은 코드 상장사를 전수로 훑는다.

browse-edgar getcompany 의 **atom 출력은 회사명이 `ARRAY(0x…)` 로 깨져 온다**(실측).
그래서 HTML 표를 파싱한다. 그 목록은 상장/비상장을 가리지 않으므로
`company_tickers.json`(티커가 붙은 상장사) 과 교집합을 잡아 상장사만 남긴다.

결과는 _raw/peers/sic_{코드}.json 에 캐시한다.

사용:  python 스크립트/sec_sic_screen.py --sic 6199
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import time

import requests

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEER = os.path.join(ROOT, "_raw", "peers")
os.makedirs(PEER, exist_ok=True)

contact = os.environ.get("SEC_CONTACT_EMAIL")
if not contact:
    sys.exit("환경변수 SEC_CONTACT_EMAIL 이 없습니다.")
HEAD = {"User-Agent": "DCF-research %s" % contact, "Accept-Encoding": "gzip, deflate"}


def get(url, tries=4):
    for i in range(tries):
        try:
            r = requests.get(url, headers=HEAD, timeout=60)
            if r.status_code == 200:
                return r
        except requests.RequestException:
            pass
        time.sleep(1.2 * (i + 1))
    return None


def 티커표():
    p = os.path.join(PEER, "company_tickers.json")
    if os.path.exists(p):
        return json.load(io.open(p, encoding="utf-8")), "캐시"
    r = get("https://www.sec.gov/files/company_tickers.json")
    if r is None:
        sys.exit("company_tickers.json 조회 실패")
    j = r.json()
    m = {}
    for _, v in j.items():
        m.setdefault(int(v["cik_str"]), []).append(v["ticker"])
    m = {str(k): v for k, v in m.items()}
    json.dump(m, io.open(p, "w", encoding="utf-8"), ensure_ascii=False)
    return m, "신규"


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--sic", required=True)
    ap.add_argument("--max", type=int, default=2000)
    a = ap.parse_args()

    tick, how = 티커표()
    print("company_tickers: %d CIK [%s]" % (len(tick), how))

    p = os.path.join(PEER, "sic_%s.json" % a.sic)
    if os.path.exists(p):
        uniq = json.load(io.open(p, encoding="utf-8"))
        print("캐시 사용")
    else:
        rows, start, 실패 = [], 0, []
        while start < a.max:
            url = ("https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany"
                   "&SIC=%s&type=10-K&dateb=&owner=include&count=100&start=%d"
                   % (a.sic, start))
            r = get(url)
            if r is None:
                실패.append(start)
                print("조회 실패 start=%d — 조용히 빼지 않고 적는다" % start)
                break
            got = re.findall(
                r'CIK=(\d{10})&[^>]*>\s*(\d{10})\s*</a></td>\s*<td[^>]*>(.*?)</td>',
                r.text, re.S)
            if not got:
                got = re.findall(r'CIK=(\d{10})[^"]*">(\d{10})</a></td><td[^>]*>(.*?)</td>',
                                 r.text, re.S)
            if not got:
                break
            for cik, _c, nm in got:
                nm = re.sub(r"<[^>]+>", "", nm).strip()
                rows.append({"cik": int(cik), "name": nm})
            if len(got) < 100:
                break
            start += 100
            time.sleep(0.4)
        seen, uniq = set(), []
        for r in rows:
            if r["cik"] in seen:
                continue
            seen.add(r["cik"])
            uniq.append(r)
        json.dump(uniq, io.open(p, "w", encoding="utf-8"), ensure_ascii=False)

    상장 = [dict(r, tickers=tick.get(str(r["cik"]), [])) for r in uniq
           if tick.get(str(r["cik"]))]
    print("SIC %s → 제출인 %d곳 · 그중 티커 있는 상장사 %d곳" % (a.sic, len(uniq), len(상장)))
    json.dump(상장, io.open(os.path.join(PEER, "sic_%s_listed.json" % a.sic), "w",
                          encoding="utf-8"), ensure_ascii=False)
    for r in 상장:
        print("  %-8s %d  %s" % (",".join(r["tickers"]), r["cik"], r["name"]))


if __name__ == "__main__":
    main()

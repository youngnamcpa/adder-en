# -*- coding: utf-8 -*-
"""[본체 승격 2026-09-10 · HWO-54] TSLA 회차의 `tsla_ads비율.py` 를 그대로 올렸다 —
원래부터 티커 인자만 받는 일반형이었고, 회차 전용은 이름뿐이었다. 외국 신고인
(20-F·IFRS)·다종류 주식 예외는 회차마다 나오므로 회차 스크립트로 다시 짜지 않는다.

ADR 후보의 **ADS 비율**을 20-F 표지에서 직접 확인한다. 추측하지 않는다.

왜 필요한가 — `peer_조립_us.py` 주석의 ARBK 실측: dei 주식수는 **보통주 수**인데
미국 시세는 **ADS** 다. 비율을 모르면 시가총액이 통째로 어긋난다(그때는 확인 불가로 뺐다).
여기서는 표지 원문을 받아 비율을 확정하고, 못 찾으면 **찾지 못했다고 적는다.**

결과: _raw/peers/ads_{티커}.json  (문장 원문을 함께 남겨 사람이 볼 수 있게 한다)
"""
from __future__ import annotations
import argparse, io, json, os, re, sys, time, html
import requests
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEER = os.environ.get("DCF_PEER_CACHE") or os.path.join(ROOT, "_raw", "peers")   # 손개입 개선 1 — 사슬 `--캐시` 가 환경변수로 닿는다(종전에는 하위 도구가 키트 _raw/peers 에 썼다)
contact = os.environ.get("SEC_CONTACT_EMAIL")
if not contact:
    sys.exit("환경변수 SEC_CONTACT_EMAIL 이 없습니다.")
H = {"User-Agent": "DCF-research %s" % contact, "Accept-Encoding": "gzip, deflate"}

숫자 = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
      "eight": 8, "nine": 9, "ten": 10, "twelve": 12, "fifteen": 15, "twenty": 20,
      "twenty-five": 25, "fifty": 50, "one hundred": 100, "a": 1}


def get(url, rng=None):
    h = dict(H)
    if rng:
        h["Range"] = "bytes=0-%d" % rng
    for i in range(3):
        try:
            r = requests.get(url, headers=h, timeout=90)
            if r.status_code in (200, 206):
                time.sleep(0.15)
                return r
        except requests.RequestException:
            pass
        time.sleep(1.0 * (i + 1))
    return None


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--tickers", required=True)
    a = ap.parse_args()
    for t in [x.strip().upper() for x in a.tickers.split(",") if x.strip()]:
        p = os.path.join(PEER, "ads_%s.json" % t)
        if os.path.exists(p):
            d = json.load(io.open(p, encoding="utf-8"))
            print("%-6s [캐시] 비율 %s" % (t, d.get("ADS비율")))
            continue
        m = json.load(io.open(os.path.join(PEER, "sub_%s.json" % t), encoding="utf-8"))
        cik = m["cik"]
        r = get("https://data.sec.gov/submissions/CIK%010d.json" % cik)
        if r is None:
            print("%-6s *** submissions 조회 실패" % t)
            continue
        rec = r.json()["filings"]["recent"]
        acc = doc = 폼 = None
        for i in range(len(rec["form"])):
            if rec["form"][i] in ("20-F", "10-K"):
                acc = rec["accessionNumber"][i].replace("-", "")
                doc = rec["primaryDocument"][i]
                폼 = "%s %s" % (rec["form"][i], rec["reportDate"][i])
                break
        if not acc:
            print("%-6s *** 연차보고서 없음" % t)
            continue
        url = "https://www.sec.gov/Archives/edgar/data/%d/%s/%s" % (cik, acc, doc)
        rr = get(url, rng=600000)
        if rr is None:
            print("%-6s *** 표지 조회 실패 %s" % (t, url))
            continue
        s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", rr.text)
        s = html.unescape(re.sub(r"(?s)<[^>]+>", " ", s))
        s = re.sub(r"\s+", " ", s).replace(" ", " ")
        # 표지 문구가 회사마다 갈린다(실측):
        #   XPEV "each representing two Class A ordinary shares"
        #   TM   "Each American Depositary Share representing ten shares of the registrant's Common Stock"
        pat = re.compile(r"(American Depositary Shares?[^.]{0,160}?"
                         r"represent(?:ing|s)?\s+([A-Za-z\-]+|[\d,\.]+)\s+"
                         r"(?:\(\d+\)\s*)?(?:Class\s+[A-Z]\s+)?"
                         r"(?:ordinary\s+shares?|common\s+shares?|shares?))", re.I)
        hits = pat.findall(s)
        비율, 문장 = None, None
        if hits:
            문장 = hits[0][0][:300]
            w = hits[0][1].lower().replace(",", "")
            비율 = 숫자.get(w)
            if 비율 is None:
                try:
                    비율 = float(w)
                except ValueError:
                    비율 = None
        else:
            # ADR 이 아니라 보통주 직상장인 경우 — 그 사실도 확인해 적는다
            if re.search(r"American Depositary", s, re.I) is None:
                비율, 문장 = 1, "표지에 American Depositary 언급 없음 — 보통주 직상장으로 본다"
        json.dump({"티커": t, "cik": cik, "폼": 폼, "url": url,
                   "ADS비율": 비율, "근거문장": 문장},
                  io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("%-6s %s · 비율 %s\n        %s" % (t, 폼, 비율, (문장 or "*** 표지에서 못 찾음")[:220]))


if __name__ == "__main__":
    main()

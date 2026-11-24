# -*- coding: utf-8 -*-
"""[본체 승격 2026-09-10 · HWO-54] TSLA 회차의 `tsla_표지주식수.py` 를 그대로 올렸다 —
원래부터 티커 인자만 받는 일반형이었고, 회차 전용은 이름뿐이었다. 외국 신고인
(20-F·IFRS)·다종류 주식 예외는 회차마다 나오므로 회차 스크립트로 다시 짜지 않는다.

표지(10-Q/10-K/20-F) 주식수 문장을 **원문 그대로** 뽑아 보여 준다.

왜 필요한가 — 다종류 주식(Class A/B) 회사는 dei 표지 태그가 **종류별 차원(dimension)** 으로
붙어 있고, companyconcept·companyfacts 는 차원 없는 사실만 준다. 그래서
GOOGL·META·RIVN·LI·NIO·XPEV 가 「dei 없음」으로 위장된다(실측). 표지를 직접 읽는다.

값을 자동으로 확정하지 않는다. **문장을 사람에게 보여 주고** 그것을 근거로 적는다.
결과: _raw/peers/표지_{티커}.json

인라인 XBRL 제안(2026-10-24 W17) — 표지의 `dei:EntityCommonStockSharesOutstanding` 사실(클래스마다 하나)을 그 문서의 ix 태그에서 그대로 읽어
합과 날짜를 `표지_*.json` 의 「ix」 칸과 `주식수_제안.json`(조립기 `주식수_대체` 와 같은 꼴 — [분모, 분모일, 종류, 비고])에 적는다.
**값을 확정하지 않는다** — 조립기는 `--표지제안` 을 줄 때만 이 제안을 쓰고 비고에 「제안 채택」 을 남긴다(유니버스 일괄의 [판단]).
외국 신고인(20-F · 40-F — ADS 배율이 걸린다)은 제안하지 않는다. dei 가 묵은 회사(F 2011 · HMC 2020)와 클래스 둘 이상 회사(META · GOOGL ·
LUNR · PL)가 대상이다. 문장 창은 텍스트 앞 25만 자(종전 6만 자 — 숨은 ix 머리가 앞을 차지해 표지 문장 0 이던 회사).
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


def _ix주식수(원문):
    """인라인 XBRL 의 dei:EntityCommonStockSharesOutstanding 사실 → {"합", "클래스수", "날", "값들"} 또는 None.
    scale · sign 을 따르고, 같은 contextRef 는 한 번만 센다. 날짜는 그 context 의 instant(가장 늦은 것)."""
    import re as _re
    값들, 본 = [], set()
    for mm in _re.finditer(r'(?is)<ix:nonfraction([^>]*name="dei:EntityCommonStockSharesOutstanding"[^>]*)>(.*?)</ix:nonfraction>', 원문):
        속, 글 = mm.group(1), _re.sub(r"(?s)<[^>]+>", "", mm.group(2))
        cr = _re.search(r'contextref="([^"]+)"', 속, _re.I)
        cr = cr.group(1) if cr else None
        if cr in 본:
            continue
        본.add(cr)
        수 = _re.sub(r"[^0-9.]", "", 글)
        if not 수:
            continue
        sc = _re.search(r'scale="(-?[0-9]+)"', 속, _re.I)
        v = float(수) * (10 ** int(sc.group(1)) if sc else 1)
        if _re.search(r'sign="-"', 속, _re.I):
            v = -v
        값들.append((cr, int(round(v))))
    if not 값들:
        return None
    날 = None
    for cr, _v in 값들:
        cm = _re.search(r'(?is)<xbrli:context[^>]*id="%s"[^>]*>(.*?)</xbrli:context>' % _re.escape(cr or ""), 원문)
        if cm:
            im = _re.search(r"(?is)<xbrli:instant>(.*?)</xbrli:instant>", cm.group(1))
            if im and (날 is None or im.group(1).strip() > 날):
                날 = im.group(1).strip()
    return {"합": sum(v for _c, v in 값들), "클래스수": len(값들), "날": 날, "값들": [[c, v] for c, v in 값들]}


def 서류고르기(rec, 폼순, 기준일=None):
    """submissions 「recent」 표 → 표지를 읽을 서류 (폼, 보고 기간 끝, 제출일, 접수번호, 문서) 또는 None.

    기준일(평가기준일 T)을 주면 **T 이하에 제출된** 정기 서류(폼순) 가운데 보고 기간 끝이 가장 늦은 것(같으면 늦게 낸 것)이다 — 주식수는 T 에
    알 수 있던 값이다(날짜 둘 · 2026-11-01. 종전에는 「보고 기간 끝 ≥ T − 10일」 가운데 가장 이른 것이라 T 가 분기말이 아니면 T 뒤에 낸 최신 분기
    표지를 제안했다). T 이하에 낸 서류가 없을 때만 종전 규칙(기준일 무렵 보고서 — T 뒤에 냈으면 부르는 쪽이 「기준일뒤」 를 단다)으로 물러선다.
    기준일이 없으면 폼 차례로 가장 최근 것."""
    n = len(rec.get("form") or [])

    def 묶(i):
        return (rec["form"][i], rec["reportDate"][i], rec["filingDate"][i], rec["accessionNumber"][i].replace("-", ""), rec["primaryDocument"][i])
    if 기준일:
        전 = [((rec["reportDate"][i] or ""), (rec["filingDate"][i] or ""), i) for i in range(n)
             if rec["form"][i] in 폼순 and (rec["filingDate"][i] or "9") <= 기준일]
        if 전:
            return 묶(max(전)[2])
        import datetime as _dt
        하 = (_dt.date.fromisoformat(기준일) - _dt.timedelta(days=10)).isoformat()
        후 = [(rec["reportDate"][i] or "", i) for i in range(n) if rec["form"][i] in 폼순 and (rec["reportDate"][i] or "") >= 하]
        if 후:
            return 묶(min(후)[1])
    for want in 폼순:
        for i in range(n):
            if rec["form"][i] == want:
                return 묶(i)
    return None


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--tickers", required=True)
    ap.add_argument("--forms", default="10-Q,10-K,20-F")
    ap.add_argument("--기준일", default=None, help="평가기준일 T YYYY-MM-DD — 주면 T 이하에 제출된 정기 서류 가운데 보고 기간 끝이 가장 늦은 것의 표지를 읽는다"
                                                 "(주식수는 T 에 알 수 있던 값 · 날짜 둘). T 이하 제출이 없을 때만 기준일 무렵 보고서(「기준일뒤」 표지)")
    a = ap.parse_args()
    폼순 = [x.strip() for x in a.forms.split(",")]
    for t in [x.strip().upper() for x in a.tickers.split(",") if x.strip()]:
        p = os.path.join(PEER, ("표지_%s_%s.json" % (t, a.기준일.replace("-", ""))) if a.기준일 else ("표지_%s.json" % t))
        if os.path.exists(p):
            d = json.load(io.open(p, encoding="utf-8"))
            if a.기준일 and (d.get("제출일") or "") > a.기준일:     # 옛 규칙이 고른 T 뒤 제출 표지 캐시 — 다시 고른다
                print("%-6s [캐시 버림] %s — 평가기준일 %s 뒤 제출" % (t, d.get("폼"), a.기준일))
            else:
                print("%-6s [캐시] %s" % (t, d["폼"]))
                for s in d["문장"]:
                    print("        %s" % s)
                continue
        m = json.load(io.open(os.path.join(PEER, "sub_%s.json" % t), encoding="utf-8"))
        cik = m["cik"]
        r = get("https://data.sec.gov/submissions/CIK%010d.json" % cik)
        if r is None:
            print("%-6s *** submissions 조회 실패 — 조용히 빼지 않는다" % t)
            continue
        rec = r.json()["filings"]["recent"]
        고름 = 서류고르기(rec, 폼순, a.기준일)
        if not 고름:
            print("%-6s *** 해당 폼 없음" % t)
            continue
        폼, rd, fd, acc, doc = 고름
        url = "https://www.sec.gov/Archives/edgar/data/%d/%s/%s" % (cik, acc, doc)
        rr = get(url, rng=700000)
        if rr is None:
            print("%-6s *** 표지 조회 실패" % t)
            continue
        s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", rr.text)
        s = html.unescape(re.sub(r"(?s)<[^>]+>", " ", s))
        s = re.sub(r"\s+", " ", s).replace(" ", " ")
        머리 = s[:250000]
        ix = _ix주식수(rr.text)
        문장 = []
        for mm in re.finditer(r"[\d][\d,]{6,}", 머리):
            앞 = 머리[max(0, mm.start() - 220): mm.start()]
            뒤 = 머리[mm.end(): mm.end() + 220]
            if re.search(r"(?i)outstanding|shares of|ordinary shares|common stock", 앞 + 뒤):
                문장.append((앞[-160:] + "[[" + mm.group() + "]]" + 뒤[:160]).strip())
            if len(문장) >= 8:
                break
        뒤 = bool(a.기준일 and (fd or "") > a.기준일)          # 2026-10-24 W18 — 기준일을 담은 분기 보고서는 기준일 뒤에 나온다 — 표지를 단다
        json.dump({"티커": t, "cik": cik, "폼": "%s %s (제출 %s)" % (폼, rd, fd), "보고기간끝": rd, "제출일": fd,
                   "기준일뒤": 뒤 or None, "기준일뒤_사유": ("보고 기간 끝 %s ≤ 기준일 무렵 · 제출 %s > 평가기준일 %s — 기간 기준으로 쓰되 표지" % (rd, fd, a.기준일)) if 뒤 else None,
                   "url": url, "문장": 문장, "ix": ix},
                  io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        _외국 = 폼 in ("20-F", "40-F") or bool(set((m.get("최근서류") or {}).keys()) & {"20-F", "40-F"})
        if ix and ix.get("합") and not _외국:
            제안p = os.path.join(PEER, "주식수_제안.json")
            try:
                제안 = json.load(io.open(제안p, encoding="utf-8")) if os.path.exists(제안p) else {}
            except (OSError, ValueError):
                제안 = {}
            제안[t] = [ix["합"], ix.get("날") or rd, "유통(표지 iXBRL dei 합 · 클래스 %d)" % ix["클래스수"],
                     "표지 %s %s 의 dei:EntityCommonStockSharesOutstanding %d개 사실의 합 — 제안(확정 전)%s" % (
                         폼, rd, ix["클래스수"], (" · 기준일 뒤 제출 %s(기준일뒤)" % fd) if 뒤 else "")]
            json.dump(제안, io.open(제안p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print("        ix 제안 %s주 (%s · 클래스 %d)" % (format(ix["합"], ","), ix.get("날") or rd, ix["클래스수"]))
        print("%-6s %s %s  %s" % (t, 폼, rd, url))
        for x in 문장:
            print("        %s" % x)


if __name__ == "__main__":
    main()

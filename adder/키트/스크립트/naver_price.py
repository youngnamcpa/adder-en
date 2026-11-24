# -*- coding: utf-8 -*-
"""네이버페이 증권 주봉 시세 — 확정 출처. 결과는 _raw/peers/ 에 캐시한다.

- **회귀 창 사양은 5년 주간이다(2026-10-16 결정, `--창년` 으로 바꾼다).**
  기대 주 수 = 52 × 창년 + 1(5년 261주).
- **`api.stock.naver.com` 캔들 창구는 110개 상한이다.** `count` 를 200·400 으로 올려도
  110개만 온다(실측). 주봉이면 약 2.1년이라 회귀 창 사양을 못 채운다.
- **국내 종목·지수는 그 상한을 우회할 수 있다.** `api.finance.naver.com/siseJson.naver`
  는 기간을 지정해 받고 110개 상한이 없다 — `--부터/--까지` 로 쓴다(5년 주봉이 한 번에
  온다). 해외 종목에는 이 창구가 없다 — 미국 · 해외는 `sec_주봉.py`(Yahoo, 기간 지정)를 쓰고,
  이 창구는 폴백으로 110개 상한을 그대로 안고 간다.
  **여기서 오는 값은 수정주가다**(무상증자·액면분할 반영). 로그수익률에는 이쪽이 맞다.
- **해외 종목코드의 접미사를 추측하지 않는다.** `.O`·`.K`·무접미사는 거래소 규칙이
  아니다. reutersCode 를 먼저 해석하고 `_raw/peers/reuters_codes.json` 에 캐시한다.
- 캐시가 있으면 재조회하지 않는다. 다시 받으려면 캐시 파일을 지운다.

사용:
    python 스크립트/naver_price.py --ticker PLTR                # 해외 종목
    python 스크립트/naver_price.py --ticker 005930 --domestic   # 국내 종목
    python 스크립트/naver_price.py --ticker .INX --index              # 해외 지수 (S&P500=.INX)
    python 스크립트/naver_price.py --ticker KOSPI --domestic --index  # 국내 지수 (KOSPI·KOSDAQ)
    python 스크립트/naver_price.py --ticker 011230 --domestic --부터 20230601 --까지 20260703
    python 스크립트/naver_price.py --ticker 011230 --domestic --부터 20260620 --까지 20260701 --일봉
    python 스크립트/naver_price.py --ticker MO --일봉 --날짜 20260630    # 해외 일봉 — 기준일(또는 그 앞 마지막 거래일) 종가

- **날짜 둘(2026-10-25 · `기준일.py`) — 시장 쪽 도구다.** `--날짜`(종가) · `--까지`(회귀 창 끝)는 **평가기준일 T**(분석일)다 — 지금 뜻 그대로.
  재무기준일(최근 공시 분기말)로 자르지 않는다. `--가정` 을 주면 비운 `--날짜`(일봉) · `--까지`(기간 지정)를 가정의 평가기준일로 채운다.
- **해외 일봉(2026-10-23)** — 같은 캔들 창구의 `dayCandle` 이다(110개 상한이 일봉에도 걸리면 최근 약 다섯 달). 평가기준일 종가를 받는 용도다 —
  주봉 라벨은 그 주 금요일이라 주 중간 기준일의 종가가 아니다(실측: 2026-06-30 기준일에 주봉은 07-02 라벨뿐). `--부터/--까지` 는 받은 뒤 잘라 쓴다.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEERDIR = os.path.join(ROOT, "_raw", "peers")
os.makedirs(PEERDIR, exist_ok=True)
HN = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
RCODE_CACHE = os.path.join(PEERDIR, "reuters_codes.json")


def resolve_code(tic: str):
    """해외 티커의 reutersCode 를 실제 조회로 확정한다. 접미사가 종목마다 달라 규칙으로 못 정한다."""
    cache = json.load(io.open(RCODE_CACHE, encoding="utf-8")) if os.path.exists(RCODE_CACHE) else {}
    if tic in cache:
        return cache[tic]
    found = None
    for suf in ["", ".O", ".K", ".N"]:
        c = tic + suf
        try:
            r = requests.get("https://api.stock.naver.com/stock/%s/basic" % c,
                             headers=HN, timeout=15)
            if r.status_code == 200:
                found = r.json().get("reutersCode") or c
                break
        except requests.RequestException:
            pass
        time.sleep(0.3)
    cache[tic] = found
    json.dump(cache, io.open(RCODE_CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    return found


def weekly(code: str, domestic: bool = False, index: bool = False):
    """주봉 (localDate, close) 목록. 캐시가 있으면 그것을 쓴다."""
    key = code.replace(".", "_")
    p = os.path.join(PEERDIR, "wk_%s.json" % key)
    if os.path.exists(p):
        return json.load(io.open(p, encoding="utf-8")), "캐시"
    if domestic and (index or code in ("KOSPI", "KOSDAQ")):
        urls = ["https://api.stock.naver.com/chart/domestic/index/%s?periodType=weekCandle&count=110" % code]
    elif domestic:
        urls = ["https://api.stock.naver.com/chart/domestic/item/%s?periodType=weekCandle&count=110" % code]
    elif index or code.startswith("."):
        urls = ["https://api.stock.naver.com/chart/foreign/index/%s?periodType=weekCandle&count=110" % code]
    else:
        rc = resolve_code(code)
        if not rc:
            return None, "%s reutersCode 확인 불가" % code
        urls = ["https://api.stock.naver.com/chart/foreign/item/%s?periodType=weekCandle&count=110" % rc]
    for attempt in range(3):
        for u in urls:
            try:
                r = requests.get(u, headers=HN, timeout=40)
                if r.status_code == 200 and r.text.strip() not in ("{}", ""):
                    j = r.json()
                    infos = j.get("priceInfos") or (j if isinstance(j, list) else None)
                    if infos:
                        rows = [(x["localDate"], float(x["closePrice"])) for x in infos]
                        json.dump(rows, io.open(p, "w", encoding="utf-8"))
                        return rows, "신규"
            except (requests.RequestException, ValueError, KeyError):
                pass
        time.sleep(1.5 * (attempt + 1))
    return None, "조회 실패"


def 해외일봉(code: str, count: int = 400):
    """해외 종목 · 지수 일봉 (localDate, close) — `periodType=dayCandle`. 캐시가 있으면 그것을 쓴다."""
    p = os.path.join(PEERDIR, "dk_%s.json" % code.replace(".", "_"))
    if os.path.exists(p):
        return json.load(io.open(p, encoding="utf-8")), "캐시"
    if code.startswith("."):
        u = "https://api.stock.naver.com/chart/foreign/index/%s?periodType=dayCandle&count=%d" % (code, count)
    else:
        rc = resolve_code(code)
        if not rc:
            return None, "%s reutersCode 확인 불가" % code
        u = "https://api.stock.naver.com/chart/foreign/item/%s?periodType=dayCandle&count=%d" % (rc, count)
    for attempt in range(3):
        try:
            r = requests.get(u, headers=HN, timeout=40)
            if r.status_code == 200 and r.text.strip() not in ("{}", ""):
                j = r.json()
                infos = j.get("priceInfos") or (j if isinstance(j, list) else None)
                if infos:
                    rows = [(x["localDate"], float(x["closePrice"])) for x in infos]
                    json.dump(rows, io.open(p, "w", encoding="utf-8"))
                    return rows, "신규"
        except (requests.RequestException, ValueError, KeyError):
            pass
        time.sleep(1.5 * (attempt + 1))
    return None, "조회 실패"


SISE = "https://api.finance.naver.com/siseJson.naver"
HF = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.naver.com/"}


def 국내기간(code: str, 부터: str, 까지: str, 봉: str = "week"):
    """국내 종목·지수의 기간 지정 시세. **110개 상한이 없다.**

    `siseJson.naver` 는 파이썬 리터럴에 가까운 텍스트를 준다(따옴표가 홑따옴표라
    json.loads 로는 못 읽는다). 숫자·날짜만 뽑아 쓰므로 정규식으로 행을 긁는다.
    주봉 날짜는 그 주의 **금요일** 라벨이다 — 평가기준일이 주 중간이면 라벨이
    기준일을 넘는 마지막 봉이 섞이므로 쓰는 쪽에서 잘라야 한다.
    """
    key = "%s_%s_%s_%s" % (code.replace(".", "_"), 봉, 부터, 까지)
    p = os.path.join(PEERDIR, "sise_%s.json" % key)
    if os.path.exists(p):
        return json.load(io.open(p, encoding="utf-8")), "캐시"
    import re
    url = ("%s?symbol=%s&requestType=1&startTime=%s&endTime=%s&timeframe=%s"
           % (SISE, code, 부터, 까지, 봉))
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HF, timeout=40)
            if r.status_code == 200 and "날짜" in r.text:
                rows = [(m.group(1), float(m.group(2))) for m in
                        re.finditer(r'\["(\d{8})",\s*[\d.]+,\s*[\d.]+,\s*[\d.]+,\s*([\d.]+)',
                                    r.text)]
                if rows:
                    json.dump(rows, io.open(p, "w", encoding="utf-8"))
                    return rows, "신규"
        except (requests.RequestException, ValueError):
            pass
        time.sleep(1.5 * (attempt + 1))
    return None, "조회 실패"


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--domestic", action="store_true", help="국내 종목 (6자리 코드)")
    ap.add_argument("--index", action="store_true", help="지수 (.INX, .KS11 등)")
    ap.add_argument("--부터", help="YYYYMMDD — 주면 기간 지정 창구를 쓴다(국내 전용)")
    ap.add_argument("--까지", help="YYYYMMDD — 창의 끝 = 평가기준일 T(재무기준일이 아니다)")
    ap.add_argument("--일봉", action="store_true", help="기간 지정 창구를 일봉으로")
    ap.add_argument("--창년", type=int, default=5, help="회귀 창 사양 해 수(기본 5) — 표본 부족 경보의 기준")
    ap.add_argument("--날짜", "--평가기준일", dest="날짜", help="YYYYMMDD — 그날(없으면 그 앞 마지막 거래일)의 종가를 한 줄로 찍는다(평가기준일 T 종가)")
    ap.add_argument("--가정", default=None, help="가정 파일 — 비운 --날짜(일봉) · --까지(기간 지정)를 기준일.py 의 평가기준일 T 로")
    a = ap.parse_args()
    if a.가정:
        import sys as _sys                                         # noqa: PLC0415
        _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import 기준일인자 as _기인                              # noqa: PLC0415 — 날짜 둘(2026-10-25): 시장 쪽은 T
        if a.일봉 and not a.날짜:
            a.날짜 = _기인.풀기(None, a.가정, _기인.평가, 모양="ymd")
        if a.부터 and not a.까지:
            a.까지 = _기인.풀기(None, a.가정, _기인.평가, 모양="ymd")
    if a.날짜:
        a.날짜 = a.날짜.replace("-", "")                       # 「2026-10-23」 꼴도 받는다(일봉 날짜는 YYYYMMDD)
    기대 = 52 * a.창년 + 1

    if a.일봉 and not a.domestic:                      # 해외 일봉 — 받은 뒤 기간을 자른다(2026-10-23)
        rows, how = 해외일봉(a.ticker)
        if rows is None:
            raise SystemExit("실패: %s — 비슷한 값으로 메우지 말고 보고한다" % how)
        rows = [r for r in rows if (not a.부터 or r[0] >= a.부터) and (not a.까지 or r[0] <= a.까지)]
        if not rows:
            raise SystemExit("받은 일봉에 그 기간이 없다 — 캔들 창구의 상한(최근 약 다섯 달) 밖일 수 있다. 비슷한 값으로 메우지 말고 보고한다")
        print("%s 일봉 %d개 (%s ~ %s) [%s] — 저장: _raw/peers/dk_%s.json" % (a.ticker, len(rows), rows[0][0], rows[-1][0], how, a.ticker.replace(".", "_")))
        if a.날짜:
            앞 = [r for r in rows if r[0] <= a.날짜]
            if not 앞:
                raise SystemExit("%s 이전 일봉이 없다 — 비슷한 값으로 메우지 말고 보고한다" % a.날짜)
            print("종가 %s %s%s" % (앞[-1][0], 앞[-1][1], "" if 앞[-1][0] == a.날짜 else "(그날 거래가 없어 앞 마지막 거래일)"))
        return
    if a.부터:
        if not a.domestic:
            raise SystemExit("기간 지정 창구는 국내 종목·지수 전용이다 — 해외는 `--일봉` 으로 받아 자르거나 110개 상한을 안고 간다")
        rows, how = 국내기간(a.ticker, a.부터, a.까지 or a.부터,
                          "day" if a.일봉 else "week")
        if rows is None:
            raise SystemExit("실패: %s — 비슷한 값으로 메우지 말고 보고한다" % how)
        print("%s %s %d개 (%s ~ %s) [%s]"
              % (a.ticker, "일봉" if a.일봉 else "주봉", len(rows),
                 rows[0][0], rows[-1][0], how))
        if not a.일봉 and len(rows) < 기대 - 7:
            print("표본 %d주 < 사양 %d주(%d년) — 기간 · 상장 이력을 확인하고 실제 표본 수를 근거 칸에 적는다"
                  % (len(rows), 기대, a.창년))
        return
    rows, how = weekly(a.ticker, a.domestic, a.index)
    if rows is None:
        raise SystemExit("실패: %s — 비슷한 값으로 메우지 말고 보고한다" % how)
    print("%s 주봉 %d주 (%s ~ %s) [%s]" % (a.ticker, len(rows), rows[0][0], rows[-1][0], how))
    print("저장: _raw/peers/wk_%s.json — 평가기준일 이후 캔들은 쓰는 쪽에서 자른다" % a.ticker.replace(".", "_"))
    if len(rows) < 기대:
        print("표본 %d주 < 사양 %d주(%d년) — 110캔들 상한. 실제 표본 수를 근거 칸에 적는다" % (len(rows), 기대, a.창년))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""**시장 β 실측 회귀** — 매핑표(다모다란 업종 βu)의 대체 실측.

왜 만들었나 — 야간 80곳 실측에서 매핑표 저β 업종(0.28~0.47)이 값을 시장의
2~7.5배로 부풀렸다(XOM +79% → CJ제일제당 +646%). 베타 규칙(블룸버그 없이 구하기)의
유사기업 회귀를 **이미 쓰는 시세 창구(네이버)만으로** 돌린다 — 웹 수치 금지
조문의 예외인 시세 창구 그대로, 재무 수치는 손대지 않는다.

방법 — 주간 수익률 · 회귀 창 `--창년`(기본 5년 — 2026-10-16 결정. 옛 기본은 약 2년):
  · 국내: siseJson 일봉(기준일−창년 ~ 기준일) → 주 마지막 거래일 종가 → 수익률,
    시장은 **종목의 상장시장 지수(KOSPI 또는 KOSDAQ)**.
  · 미국: `sec_주봉.py` 의 Yahoo 주봉(창년 전체 · 수정주가)을 종목 · 지수(^GSPC) 둘 다 같은 창구로 받는다.
    그 모듈을 못 읽거나 Yahoo 가 실패하면 종전 창구(naver chart/foreign weekCandle **110주 ≈ 2.1년** · .INX)로
    물러서고 그 사실과 실제 표본 수를 줄마다 적는다. 두 창구를 한 회귀에 섞지 않는다(주 라벨 관행이 다르다).

**KOSDAQ 지원 (펄29).** 옛 판은 국내를 전부 KOSPI 로 회귀했다 — KOSDAQ 대상회사(펄어비스)는
자체 회귀를 못 내고 KOSPI 값(βL −0.224 · R² 0.01)을 「참고만」으로 적었다. 베타 규칙: 「한국 종목이라고
KOSPI 를 자동으로 붙이지 않는다. 상장 시장을 먼저 확인한다」.
  · 시장 확인 순서: `코드:KOSDAQ` 처럼 직접 준 값 → `--시장` → 회차 캐시(_dartcache/상장명부_KIND.csv ·
    _raw/peers/company/*.json corp_cls · 산업분류*.csv 상장구분) → 네이버 종목 기본정보
    `m.stock.naver.com/api/stock/{코드}/basic` 의 stockExchangeType(KS·KQ) — 시세와 같은 창구다
  · 지수 시세는 같은 siseJson 창구의 `symbol=KOSPI|KOSDAQ` 일봉이다(기존 출처 체계 그대로)
  · 끝내 못 정하면 회귀하지 않고 「시장 확인 불가」로 적는다 — 추측해서 붙이지 않는다
  · OLS: βL = cov(r_i, r_m) / var(r_m). R²·표본수를 함께 낸다 — R² 가 낮으면
    회귀 자체가 약하다는 뜻이니 그것도 판단 재료다.
  · 언레버는 여기서 하지 않는다 — D/E(총차입 ÷ 시가총액)·한계세율이 회차 실측
    자리라, βu = βL ÷ (1 + (1−t)·D/E) 는 회차에서 계산해 근거 칸에 적는다.

사용:
    python 스크립트/베타회귀.py --기준일 20260630 --국내 096770,030200 --미국 XOM,T
    python 스크립트/베타회귀.py --기준일 20260630 --국내 263750:KOSDAQ,096770
"""
from __future__ import annotations

import argparse
import ast
import datetime
import importlib.util
import io
import json
import os
import sys
import time

import requests

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "_raw", "베타회귀")
H = {"User-Agent": "Mozilla/5.0"}
SISE = ("https://api.finance.naver.com/siseJson.naver?symbol=%s&requestType=1"
        "&startTime=%s&endTime=%s&timeframe=day")
FOREIGN = "https://api.stock.naver.com/chart/foreign/%s/%s?periodType=weekCandle&count=110"
try:                                                         # 미국 — Yahoo 창년 주봉(sec_주봉.py)
    _jspec = importlib.util.spec_from_file_location("sec_주봉", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                              "sec_주봉.py"))
    _jb = importlib.util.module_from_spec(_jspec)
    _jspec.loader.exec_module(_jb)
except Exception:                                            # noqa: BLE001 — 폴백(naver 110주)
    _jb = None

_여기 = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("naver_price",
                                               os.path.join(_여기, "naver_price.py"))
_np = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_np)


def _캐시(이름, 만들기):
    os.makedirs(RAW, exist_ok=True)
    p = os.path.join(RAW, 이름)
    if os.path.exists(p):
        return json.load(io.open(p, encoding="utf-8"))
    v = 만들기()
    if v:
        json.dump(v, io.open(p, "w", encoding="utf-8"), ensure_ascii=False)
        time.sleep(0.3)
    return v


def 국내일봉(code, 부터, 까지):
    def 받기():
        t = requests.get(SISE % (code, 부터, 까지), headers=H, timeout=40).text.strip()
        arr = ast.literal_eval(t.replace("\n", " "))
        return [(str(r[0]), float(r[4])) for r in arr[1:]]
    return _캐시("kr_%s_%s_%s.json" % (code, 부터, 까지), 받기)


def 야후주봉(tic, 기준, 창년):
    """Yahoo 창년 주봉 [(YYYYMMDD, 수정종가)] — sec_주봉.야후주봉 을 그대로 쓴다. 못 쓰면 None."""
    if _jb is None:
        return None

    def 받기():
        d = datetime.date(int(기준[:4]), int(기준[4:6]), int(기준[6:8]))
        try:
            줄, _, _ = _jb.야후주봉(tic, d, 창년)
        except Exception:                                    # noqa: BLE001
            return None
        return [(x[0], float(x[1])) for x in 줄] or None
    return _캐시("yh_%s_%s_%dy.json" % (tic.replace(".", "_").replace("^", ""), 기준, 창년), 받기)


def 해외주봉(tic, 지수냐=False):
    def 받기():
        rc = tic if 지수냐 else _np.resolve_code(tic)
        if not rc:
            return None
        r = requests.get(FOREIGN % ("index" if 지수냐 else "item", rc),
                         headers=H, timeout=40)
        j = r.json()
        infos = j.get("priceInfos") or (j if isinstance(j, list) else [])
        return [(x["localDate"], float(x["closePrice"])) for x in infos]
    return _캐시("us_%s.json" % tic.replace(".", "_"), 받기)


BASIC = "https://m.stock.naver.com/api/stock/%s/basic"
_시장 = {"Y": "KOSPI", "K": "KOSDAQ", "N": "KONEX", "KS": "KOSPI", "KQ": "KOSDAQ",
       "유가": "KOSPI", "유가증권": "KOSPI", "코스피": "KOSPI", "KOSPI": "KOSPI",
       "코스닥": "KOSDAQ", "KOSDAQ": "KOSDAQ", "코넥스": "KONEX", "KONEX": "KONEX"}


def 캐시시장(code, root=None):
    """회차 캐시에서 상장시장을 찾는다. (시장, 근거) 또는 (None, None)."""
    import csv
    import glob
    root = root or ROOT
    code = str(code).zfill(6)
    p = os.path.join(root, "_dartcache", "상장명부_KIND.csv")
    if os.path.exists(p):
        for r in csv.DictReader(io.open(p, encoding="utf-8-sig")):
            if (r.get("종목코드") or "").zfill(6) == code and _시장.get((r.get("시장") or "").strip()):
                return _시장[r["시장"].strip()], "KIND 상장명부"
    for q in glob.glob(os.path.join(root, "_raw", "peers", "company", "*.json")):
        try:
            j = json.load(io.open(q, encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if str(j.get("stock_code") or "").zfill(6) == code and _시장.get(str(j.get("corp_cls") or "")):
            return _시장[j["corp_cls"]], "기업개황 corp_cls=%s" % j["corp_cls"]
    for 이름 in ("산업분류.csv", "산업분류_전수.csv"):
        q = os.path.join(root, 이름)
        if os.path.exists(q):
            for r in csv.DictReader(io.open(q, encoding="utf-8-sig")):
                if (r.get("종목코드") or "").zfill(6) == code and _시장.get((r.get("상장구분") or "").strip()):
                    return _시장[r["상장구분"].strip()], "%s 상장구분" % 이름
    return None, None


def 네이버시장(code):
    """네이버 종목 기본정보의 stockExchangeType — 시세와 같은 창구. 캐시한다."""
    def 받기():
        try:
            j = requests.get(BASIC % code, headers=H, timeout=20).json()
        except (requests.RequestException, ValueError):
            return None
        t = (j.get("stockExchangeType") or {})
        m = _시장.get(str(t.get("code") or "")) or _시장.get(str(t.get("name") or ""))
        return {"시장": m, "원문": t.get("code") or t.get("name")} if m else None
    v = _캐시("mkt_%s.json" % code, 받기)
    return (v["시장"], "네이버 기본정보 stockExchangeType=%s" % v.get("원문")) if v else (None, None)


def 상장시장(항목, 기본=None, root=None):
    """`코드` 또는 `코드:시장`. (코드, 시장, 근거) — 못 정하면 시장 None."""
    code, _, 직접 = str(항목).partition(":")
    code = code.strip()
    if 직접.strip():
        m = _시장.get(직접.strip().upper()) or _시장.get(직접.strip())
        return code, m, "직접 지정(%s)" % 직접.strip()
    if 기본:
        return code, _시장.get(기본.upper()) or _시장.get(기본), "--시장 %s" % 기본
    m, 근거 = 캐시시장(code, root)
    if m:
        return code, m, 근거
    m, 근거 = 네이버시장(code)
    if m:
        return code, m, 근거
    return code, None, "시장 확인 불가 — 캐시·네이버 기본정보 모두 실패"


def 주간화(rows):
    """일봉 → 각 ISO 주의 마지막 거래일 종가."""
    주 = {}
    for d, c in rows:
        dt = datetime.date(int(d[:4]), int(d[4:6]), int(d[6:8]))
        키 = dt.isocalendar()[:2]
        주[키] = (d, c)                      # 뒤에 온 날이 그 주의 마지막
    return [주[k] for k in sorted(주)]


def 수익률(series):
    """주간 **로그** 수익률(조립기와 같은 정의 — S7-16. 옛 판은 단순 수익률이었다). 가격 수익률이다(배당 미포함) —
    국내 siseJson 종가 · 지수 · 미국 Yahoo 수정주가 대 ^GSPC 가격 지수의 차이는 근거에 적는다."""
    import math
    return [math.log(series[i][1] / series[i - 1][1]) for i in range(1, len(series))
            if series[i][1] and series[i - 1][1] and series[i][1] > 0 and series[i - 1][1] > 0]


def 회귀(ri, rm):
    n = min(len(ri), len(rm))
    ri, rm = ri[-n:], rm[-n:]
    mi, mm = sum(ri) / n, sum(rm) / n
    cov = sum((a - mi) * (b - mm) for a, b in zip(ri, rm)) / n
    var = sum((b - mm) ** 2 for b in rm) / n
    if var == 0:
        return None, None, n
    b = cov / var
    ss_tot = sum((a - mi) ** 2 for a in ri)
    ss_res = sum((a - mi - b * (bm - mm)) ** 2 for a, bm in zip(ri, rm))
    r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
    return b, r2, n


def _정렬맞춤(주식, 시장):
    """날짜 키가 같은 주만 짝짓는다 — 휴장 어긋남 방지."""
    m = {d[:6] + d[6:]: c for d, c in 시장}
    s지수, s주식 = [], []
    시장맵 = dict(시장)
    공통 = [d for d, _ in 주식 if d in 시장맵]
    if len(공통) < 30:
        # 주 단위 근사 매칭(±3일)로 재시도
        def 주키(d):
            dt = datetime.date(int(d[:4]), int(d[4:6]), int(d[6:8]))
            return dt.isocalendar()[:2]
        시장주 = {주키(d): c for d, c in 시장}
        짝 = [(c, 시장주.get(주키(d))) for d, c in 주식 if 주키(d) in 시장주]
        return ([a for a, _ in 짝], [b for _, b in 짝])
    return ([시장맵[d] for d in 공통], [dict(주식)[d] for d in 공통])[::-1]


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--기준일", default="20260630")
    ap.add_argument("--국내", default="", help="종목코드 쉼표 (코드:KOSDAQ 처럼 시장을 붙일 수 있다)")
    ap.add_argument("--시장", default=None, choices=["KOSPI", "KOSDAQ"],
                    help="국내 전 종목의 시장을 고정 — 기본은 종목마다 상장시장 확인")
    ap.add_argument("--미국", default="", help="티커 쉼표")
    ap.add_argument("--창년", type=int, default=5, help="회귀 창 해 수(기본 5 — 주간)")
    ap.add_argument("--지수", default="넓은", choices=["넓은", "상장"],
                    help="국내 회귀 지수 — 넓은(기본 · KOSPI, S7-05: ERP 를 곱하는 넓은 시장) · 상장(종목의 상장시장 지수 — 대안 사양)")
    a = ap.parse_args()
    기준 = a.기준일.replace("-", "")
    부터 = str(int(기준[:4]) - a.창년) + 기준[4:]

    print("시장 β 회귀 — 주간 수익률 · 기준일 %s 까지 %d년(%s~) · 사양 %d주" % (기준, a.창년, 부터, 52 * a.창년))
    print("채택 규칙 — **R² 가 문턱이다**: R² ≥ 0.15 면 βL 을 언레버해 쓸 수 있고,")
    print("  R² < 0.10 이면 회귀가 시장과 거의 무관하게 움직였다는 뜻이라 **채택 불가**")
    print("  (매핑표 βu 유지 + 이 실측을 근거 칸에 병기). 그 사이는 사람이 판단한다.")
    print("  실측 — 채택 가능: 이차전지 4사 0.23~0.30 · GOOGL 0.34 · MSFT 0.40 /")
    print("  채택 불가: XOM·CVX·T·SKT·KT·CJ제일제당 0.00~0.07 · 삼바 0.06 — 저β 방어주의")
    print("  낮은 R² 는 β 의 문제가 아니라 시장이 성장소멸·환원을 따로 할인한다는 신호다.")
    print("%-14s %8s %8s %6s   비고" % ("대상", "βL", "R²", "표본"))

    if a.국내:
        지수주 = {}

        def 지수주봉(지수):
            if 지수 not in 지수주:
                지수주[지수] = 주간화(국내일봉(지수, 부터, 기준) or [])
            return 지수주[지수]

        for 항목 in [x.strip() for x in a.국내.split(",") if x.strip()]:
            code, 시장, 근거 = 상장시장(항목, a.시장)
            if 시장 not in ("KOSPI", "KOSDAQ"):
                print("%-14s %8s   %s" % (code, "회귀 안 함", 근거 if not 시장 else "%s 는 지수 회귀 대상 아님(%s)" % (시장, 근거)))
                continue
            rows = 국내일봉(code, 부터, 기준)
            if not rows:
                print("%-14s %8s" % (code, "조회 실패"))
                continue
            ks = 주간화(rows)

            def 주키(d):
                dt = datetime.date(int(d[:4]), int(d[4:6]), int(d[6:8]))
                return dt.isocalendar()[:2]
            지수들 = ["KOSPI"] + ([시장] if (a.지수 == "넓은" and 시장 != "KOSPI") else []) if a.지수 == "넓은" else [시장]
            for k, 지 in enumerate(지수들):
                km = 지수주봉(지)
                if not km:
                    print("%-14s %8s   %s 지수 일봉 조회 실패" % (code, "-", 지))
                    continue
                시장주 = {주키(d): c for d, c in km}
                짝 = [(c, 시장주[주키(d)]) for d, c in ks if 주키(d) in 시장주]
                si = [p[0] for p in 짝]
                sm = [p[1] for p in 짝]
                ri, rm = [], []
                for i in range(1, len(si)):
                    if si[i] and si[i - 1] and sm[i] and sm[i - 1] and min(si[i], si[i - 1], sm[i], sm[i - 1]) > 0:
                        import math as _m
                        ri.append(_m.log(si[i] / si[i - 1]))
                        rm.append(_m.log(sm[i] / sm[i - 1]))
                b, r2, n = 회귀(ri, rm)
                print("%-14s %8s %8s %6d   vs %s%s (상장 %s · 시장 근거: %s)" %
                      (code if k == 0 else "  └ 대안", "%.3f" % b if b is not None else "-",
                       "%.2f" % r2 if r2 is not None else "-", n, 지,
                       " — 넓은 시장(본값)" if (a.지수 == "넓은" and k == 0) else (" — 상장시장 지수(대안 사양)" if a.지수 == "넓은" else ""),
                       시장, 근거))

    if a.미국:
        yinx = 야후주봉("^GSPC", 기준, a.창년)
        ninx = None

        def 지수줄(창구):
            nonlocal ninx
            if 창구 == "Yahoo":
                return yinx
            if ninx is None:
                ninx = [(d, c) for d, c in (해외주봉(".INX", 지수냐=True) or []) if d <= 기준]
            return ninx
        for tic in [x.strip() for x in a.미국.split(",") if x.strip()]:
            rows, 창구 = (야후주봉(tic, 기준, a.창년), "Yahoo") if yinx else (None, None)
            if not rows:
                rows, 창구 = 해외주봉(tic), "naver 110주 폴백"
            if not rows:
                print("%-14s %8s" % (tic, "조회 실패"))
                continue
            rows = [(d, c) for d, c in rows if 부터 <= d <= 기준]
            inx = [(d, c) for d, c in (지수줄("Yahoo" if 창구 == "Yahoo" else "naver") or []) if 부터 <= d <= 기준]
            def 주키(d):
                dt = datetime.date(int(d[:4]), int(d[4:6]), int(d[6:8]))
                return dt.isocalendar()[:2]
            시장주 = {주키(d): c for d, c in inx}
            짝 = [(c, 시장주[주키(d)]) for d, c in rows if 주키(d) in 시장주]
            si = [p[0] for p in 짝]
            sm = [p[1] for p in 짝]
            import math as _m
            쌍 = [(_m.log(si[i] / si[i - 1]), _m.log(sm[i] / sm[i - 1])) for i in range(1, len(si))
                 if si[i] and si[i - 1] and sm[i] and sm[i - 1] and min(si[i], si[i - 1], sm[i], sm[i - 1]) > 0]
            b, r2, n = 회귀([x for x, _ in 쌍], [y for _, y in 쌍])
            print("%-14s %8s %8s %6d   vs S&P500 · %s%s" %
                  (tic, "%.3f" % b if b is not None else "-",
                   "%.2f" % r2 if r2 is not None else "-", n, 창구,
                   "" if n >= 52 * a.창년 - 7 else " — 사양 %d주 미달, 실제 표본 수를 근거 칸에 적는다" % (52 * a.창년)))


if __name__ == "__main__":
    main()

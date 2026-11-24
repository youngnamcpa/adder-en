# -*- coding: utf-8 -*-
"""미국 종목용 유사기업 재료 조립 — 2차 컷(시가총액) · 베타 · 잔차상관 · 잡음 문턱.

`peer_조립.py` 는 DART 산출물(주식수.csv·전체재무_추출.csv·sise_*.json)을 읽는 국내 전용이다.
미국 회차는 SEC(주식수·재무)와 naver 해외 주봉(wk_*.json)에서 읽으므로 이 파일을 쓴다.
**회귀·상관 수식은 `peer_조립.py` 와 같은 것을 옮겨 쓴다** — 회차마다 다시 구현하지 않는다.

산출 이름은 **표본마다 갈린다(2026-09-13 · 세14).** 옛 판은 명단이 무엇이든 `유사기업_재료.csv`·
`_raw/peers/2차통과.json`·`2차탈락.json` 에 썼다 — 세일즈포스 회차에서 넓은 표본(CP3) 조립이
핵심+예비(CP2) 결과를 덮었다. 이제 `--표본 이름`(기본: 명단 파일 이름에서 확장자를 뗀 것)을 붙여
    유사기업_재료_{표본}.csv · _raw/peers/2차통과_{표본}.json · _raw/peers/2차탈락_{표본}.json
에 쓴다. 산출 json 머리에 명단·기준일·대상을 적어, 다른 명단의 산출을 덮으려 하면 멈춘다.

`--세율` 을 주면 조립 뒤에 `peer_βU_us.py` 를 이어 돌려 βU·D/E·**현금보정**·세 방식·성장·수익성을
`_raw/peers/βU_{표본}.json` 에 낸다(세3 — 옛 판에는 그 칸이 없어 C2 가 손으로 만들었고 현금보정이 빠졌다).

**회귀 창 = 기준일 − `--창년`(기본 5년 · 주간) ~ 기준일 (2026-10-16 결정).** wk_ 캐시가 더 길면
창 시작 앞의 주를 잘라 창이 조용히 늘지 않게 하고, 회사마다 실제 주 수를 적는다. `--부터 YYYYMMDD` 를 주면 그 날이 시작.

**`목적`(2026-10-16 · 결정 5).** `--명단` 이 C1 `핵심표본.json`(핵심 · 예비 · 운영 동종 전용 · 컷통과전체) 꼴이어도
읽는다. `목적` 을 선언했는데 「위험동종」이 없는 회사(운영 동종 전용)는 βU 표본이 아니라 빼고 화면에 적는다.

주의
  - Yahoo(`sec_주봉.py`)가 창 전체를 준다. 폴백 창구(naver 해외)는 **110개 상한**이라 창을 못 채운다 — 실제 표본 수를 그대로 적는다.
  - 티커가 바뀐 회사는 옛 티커 시세를 **이어 붙인다**(예: BITF → KEEL). 이은 사실을 적는다.
  - 시가총액 분모는 **자기주식을 뺀 유통주식수**. 못 구하면 무엇으로 대체했는지 적는다.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 피어경로 as 피경  # noqa: E402 — 명단 경로 · 종가 파일 이름 한 규칙(2026-10-24 W15)

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEER = os.environ.get("DCF_PEER_CACHE") or os.path.join(ROOT, "_raw", "peers")   # 손개입 개선 1 — 사슬 `--캐시` 가 환경변수로 닿는다(종전에는 하위 도구가 키트 _raw/peers 에 썼다)

기준일 = "20260630"          # main() 이 --기준일 로 덮는다
창시작 = ""                  # main() 이 기준일 − 창년(또는 --부터)으로 덮는다 — 이 날 앞의 주는 쓰지 않는다

# 대상회사 주식수 — **회차마다 다르다. 기억으로 적지 않는다.**
# `--대상` · `--대상주식수` 로 넘기거나 `_raw/peers/대상.json` 에 적어 둔다:
#   {"티커": "RXRX", "주식수": 534120235, "주식수기준일": "2026-06-30",
#    "종류": "유통(us-gaap/CommonStockSharesOutstanding · 발행=유통, 자기주식 없음)"}
# **기본값을 두지 않는다.** 예전에 IREN 회차 실측치가 기본값으로 남아 있었는데,
# `--대상 RXRX` 만 주고 주식수를 안 주면 **RXRX 티커에 IREN 주식수**가 조용히 붙었다.
# 티커가 틀리면 주봉이 없어 큰 소리로 죽지만, 주식수는 그냥 붙는다 — 시가총액이
# 통째로 어긋나는데 어느 검증도 그것을 못 잡는다. 못 구하면 **채우지 말고 멈춘다.**
대상기본 = {"티커": None, "주식수": None, "주식수기준일": None, "종류": None}

# 주식수 분모 — 티커: (주식수, 기준일, 종류, 비고)
# dei/EntityCommonStockSharesOutstanding 이 있으면 그것(표지 기준 유통주식수).
# 없으면 무엇으로 대체했는지 여기 남긴다. **추측한 값은 없다.**
# 회차별 보탬은 `_raw/peers/주식수_대체.json` 에 같은 모양으로 적으면 아래에 덮인다.
주식수_대체 = {
    "GOOGL": (12230000000, "2026-06-30", "발행(전 종류 합계)",
              "us-gaap/CommonStockSharesIssued — dei 미태깅. 유통 확인 불가"),
    "CRWV": (551000000, "2026-06-30", "가중평균 기본주식수",
             "표지 유통주식수 미태깅(다종류 주식). us-gaap/WeightedAverageNumberOfSharesOutstandingBasic 2026 2분기"),
    "NBIS": (253016971, "2025-12-31", "유통(6개월 시차)",
             "us-gaap/CommonStockSharesOutstanding 2025-12-31 — 평가기준일 시점 값 없음"),
    "GLXY": (390465556, "2026-06-30", "가중평균 희석주식수",
             "Up-C 구조. Class A 기본 192.5m / 전 종류 희석 390.5m. **유통 확인 불가**"),
    "CANG": (283289035, "2025-12-31", "가중평균 희석주식수",
             "us-gaap 표지·유통 태그가 2018년 이후 없음. **유통 확인 불가**"),
    "FUFU": (166613948, "2025-12-31", "유통(6개월 시차)",
             "us-gaap/CommonStockSharesOutstanding 2025-12-31"),
    "VIP": (18019743, "2026-06-30", "유통", "us-gaap/CommonStockSharesOutstanding"),
    "ABTC": (72819713, "2026-07-30", "유통(Class A 24,004,726 + Class B 48,814,987)",
             "10-Q 표지 직접 확인. dei 태깅은 2025-08-14 에서 멈춤. "
             "**naver 시세의 ABTC 가 같은 증권인지 확인 필요**"),
    "HTT": (None, None, None, "dei 가 2017-12-31 값에서 멈춤 — **유통 확인 불가**"),
    "ARBK": (None, None, None,
             "dei 28,857,673,160 은 보통주 수이고 나스닥 시세는 ADS 다. "
             "ADS 비율 미확인 — **유통 확인 불가**"),
}
# 티커 변경으로 시세를 이어 붙이는 곳
시세_이어붙임 = {"KEEL": ["BITF", "KEEL"]}


def 읽자(p):
    return json.load(io.open(p, encoding="utf-8"))


def 주봉(t):
    조각 = 시세_이어붙임.get(t, [t])
    rows = []
    for c in 조각:
        for 이름 in dict.fromkeys((c, c.replace(".", "_"))):      # sec_주봉 은 「.」 를 「_」 로 바꿔 저장한다(005930.KS → wk_005930_KS)
            p = os.path.join(PEER, "wk_%s.json" % 이름)
            if os.path.exists(p):
                rows += [(d, v) for d, v in 읽자(p)]
                break
    rows = sorted(set(rows))
    return [(d, v) for d, v in rows if 창시작 <= d <= 기준일]


_전용키 = ("운영동종전용", "운영동종_전용", "운영 동종 전용", "운영전용")


def 운영전용(x):
    """목적을 선언했는데 「위험동종」이 없다 — βU 표본이 아니다."""
    v = x.get("목적") if isinstance(x, dict) else None
    if v is None:
        return False
    if isinstance(v, str):
        import re as _re
        v = _re.split(r"[,·/|]", v)
    return "위험동종" not in [str(t).replace(" ", "") for t in v]


def 후보펼치기(j):
    """목록 · {"행"} · C1 핵심표본(핵심 · 예비 · 운영 동종 전용 · 컷통과전체) → 목록. 모르는 칸은 버리지 않고 쓰지 않을 뿐이다."""
    if isinstance(j, list):
        return [({"티커": x} if isinstance(x, str) else x) for x in j]      # S7-19 — 티커 문자열 목록도 읽는다
    if any(k in j for k in ("핵심", "예비") + _전용키):
        out, 본 = [], set()
        for k in ("핵심",) + _전용키 + ("예비",):
            for x in j.get(k) or []:
                x = {"티커": x} if isinstance(x, str) else x
                t = (x.get("티커") or "").upper()
                if t and t not in 본:
                    본.add(t)
                    out.append(x)
        return out
    return j.get("행") or j.get("컷통과전체") or []


def 로그수익(vals):
    return [math.log(b / a) if (a and b and a > 0 and b > 0) else None
            for a, b in zip(vals, vals[1:])]


def 회귀(y, x):
    쌍 = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
    n = len(쌍)
    if n < 3:
        return None, None, None, n
    ax = sum(a for a, _ in 쌍) / n
    ay = sum(b for _, b in 쌍) / n
    sxx = sum((a - ax) ** 2 for a, _ in 쌍)
    sxy = sum((a - ax) * (b - ay) for a, b in 쌍)
    syy = sum((b - ay) ** 2 for _, b in 쌍)
    if sxx == 0:
        return None, None, None, n
    beta = sxy / sxx
    alpha = ay - beta * ax
    r2 = (sxy ** 2) / (sxx * syy) if syy else None
    잔차 = [None if (a is None or b is None) else b - (alpha + beta * a)
          for a, b in zip(x, y)]
    return beta, r2, 잔차, n


def 상관(a, b):
    쌍 = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    n = len(쌍)
    if n < 3:
        return None, n
    ax = sum(x for x, _ in 쌍) / n
    ay = sum(y for _, y in 쌍) / n
    좌 = math.sqrt(sum((x - ax) ** 2 for x, _ in 쌍))
    우 = math.sqrt(sum((y - ay) ** 2 for _, y in 쌍))
    if 좌 == 0 or 우 == 0:
        return None, n
    return sum((x - ax) * (y - ay) for x, y in 쌍) / (좌 * 우), n


def 날짜정렬(대상, 시장):
    """날짜를 맞춰 두 계열을 나란히 놓는다. 상장 시점이 다르면 겹치는 구간만 쓴다."""
    m = dict(시장)
    공통 = [d for d, _ in 대상 if d in m]
    return ([(d, dict(대상)[d]) for d in 공통], [(d, m[d]) for d in 공통])


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--최소주", type=int, default=60,
                    help="2차 컷의 자료 기준(주간 관측이 이보다 적으면 자료 부재로 탈락). **본값 최소 표본은 156주** — "
                         "60~155주 회사는 표에 남고 βU 본값에서만 빠진다(βU본값.py, S7-17)")
    ap.add_argument("--out", default=None, help="기본: 유사기업_재료_{표본}.csv")
    ap.add_argument("--표본", default=None, help="산출 이름 꼬리 — 기본은 명단 파일 이름(확장자 뗌)")
    ap.add_argument("--캐시", default=None, help="_raw/peers 대신 쓸 캐시 폴더(회차 폴더는 그 두 단계 위)")
    ap.add_argument("--세율", type=float, default=None, help="주면 peer_βU_us.py 를 이어 돌린다(기본값 없음)")
    ap.add_argument("--세율표", default=None, help='회사별 소재국 세율 {"티커": 세율} — peer_βU_us 에 넘긴다(2026-10-24 W16 · 없는 회사는 --세율)')
    ap.add_argument("--스크린", default=None, help="βU 단계에 넘길 sec_peer_screen 산출 json")
    ap.add_argument("--대상", help="대상회사 티커 (없으면 _raw/peers/대상.json → 기본값)")
    ap.add_argument("--대상주식수", type=int, help="대상회사 유통주식수")
    ap.add_argument("--표지제안", action="store_true",
                    help="표지 iXBRL 주식수 제안(주식수_제안.json)을 주식수_대체 다음 자리로 쓴다 — 유니버스 일괄 [판단](2026-10-24 W17)")
    ap.add_argument("--밴드생략", action="store_true",
                    help="해외 동종 경로 ⑤(대상이 다른 시장 — 예: 국내 상장) — 시가총액 밴드를 걸지 않고 대상은 잔차상관 짝으로만(대상 주식수 불요)")
    ap.add_argument("--재무기준일", default=None, help="재무 자료 기준일 F YYYY-MM-DD — peer_βU_us 에 넘긴다(차입 · 현금 · 장부 값 · 1.1.2 P10)")
    ap.add_argument("--기준일", "--평가기준일", dest="기준일", default=None, help="평가기준일 T(분석일 · 시장 쪽 — 종가 · 시가총액 · 주식수 · 베타 창 끝 · 환율 · 법령 시행일) YYYYMMDD (없으면 모듈 기본값)")
    ap.add_argument("--지수", default="_INX", help="시장지수 주봉 키 (_INX 등)")
    ap.add_argument("--밴드", type=float, default=5.0, help="선언한 규모대 배수")
    ap.add_argument("--명단", default="1차통과.json")
    ap.add_argument("--창년", type=int, default=5, help="회귀 창 해 수(기본 5 — 주간). 창 시작 앞의 주는 자른다")
    ap.add_argument("--부터", default=None, help="창 시작 YYYYMMDD — 주면 --창년 보다 앞선다")
    a = ap.parse_args()

    global 기준일, PEER, ROOT, 창시작
    if a.기준일:
        기준일 = a.기준일.replace("-", "")
    창시작 = a.부터.replace("-", "") if a.부터 else "%04d%s" % (int(기준일[:4]) - a.창년, 기준일[4:])
    if a.캐시:
        PEER = os.path.abspath(a.캐시)
        ROOT = os.path.dirname(os.path.dirname(PEER))
    표본 = a.표본 or os.path.splitext(os.path.basename(a.명단))[0]
    산출통과 = os.path.join(PEER, "2차통과_%s.json" % 표본)
    산출탈락 = os.path.join(PEER, "2차탈락_%s.json" % 표본)
    명단p = 피경.명단경로(a.명단, PEER, ROOT)
    if 명단p in (os.path.abspath(산출통과), os.path.abspath(산출탈락)):
        sys.exit("산출 %s 가 입력 명단과 같은 파일입니다 — 덮지 않습니다. --표본 을 바꾸십시오." % os.path.basename(명단p))
    산출csv = os.path.join(ROOT, a.out or ("유사기업_재료_%s.csv" % 표본))
    머리 = {"표본": 표본, "명단": os.path.basename(a.명단), "기준일": 기준일,
          "창": {"시작": 창시작, "끝": 기준일, "창년": None if a.부터 else a.창년, "주기": "주간"}}
    if os.path.exists(산출통과):
        try:
            옛 = 읽자(산출통과)
            옛머리 = 옛.get("머리") if isinstance(옛, dict) else None
        except Exception:
            옛머리 = None
        if 옛머리 and (옛머리.get("명단") != 머리["명단"] or 옛머리.get("기준일") != 기준일):
            sys.exit("%s 는 다른 명단(%s)·기준일(%s)의 산출입니다 — 덮지 않습니다. --표본 을 바꾸십시오."
                     % (os.path.basename(산출통과), 옛머리.get("명단"), 옛머리.get("기준일")))

    # ── 대상회사 — 회차마다 다르다. 기억으로 적지 않는다 ──
    대상 = dict(대상기본)
    dp = os.path.join(PEER, "대상.json")
    if os.path.exists(dp):
        대상.update(읽자(dp))
    if a.대상:
        대상["티커"] = a.대상.upper()
    if a.대상주식수:
        대상["주식수"] = a.대상주식수
    대상티커, 대상주식수 = 대상.get("티커"), 대상.get("주식수")
    if not 대상티커 or (not 대상주식수 and not a.밴드생략):
        sys.exit(
            "대상회사 티커·주식수가 정해지지 않았습니다. "
            "**기억으로 채우지 않습니다.**\n"
            "  --대상 TICKER --대상주식수 N 으로 주거나\n"
            '  _raw/peers/대상.json 에 {"티커": ..., "주식수": ..., '
            '"주식수기준일": ..., "종류": ...} 를 적으십시오.')

    # ── 회차별 주식수 대체 표 ──
    mp = os.path.join(PEER, "주식수_대체.json")
    if os.path.exists(mp):
        for k, v in 읽자(mp).items():
            주식수_대체[k] = tuple(v)
    # 2026-10-24 W17 — 표지 iXBRL 제안(`sec_표지주식수` 가 적은 `주식수_제안.json` — dei 가 묵었거나 클래스가 둘 이상인 회사)을
    # `--표지제안` 을 줄 때만 쓴다(유니버스 일괄 [판단]). 사람이 확정한 `주식수_대체` 가 먼저다
    if getattr(a, "표지제안", False):
        pp = os.path.join(PEER, "주식수_제안.json")
        if os.path.exists(pp):
            for k, v in 읽자(pp).items():
                if k not in 주식수_대체 and isinstance(v, list) and len(v) == 4:
                    주식수_대체[k] = (v[0], v[1], v[2], "[판단] 표지 iXBRL 제안 채택 — " + (v[3] or ""))

    후보 = 읽자(명단p)
    if isinstance(후보, dict):          # 조립·스크린 산출({"머리", "행"}) · C1 핵심표본을 명단으로 받아도 된다
        if 후보.get("B1도착") is not None or isinstance(후보.get("보강"), list):
            머리["표본판"] = {k: v for k, v in (("B1도착", 후보.get("B1도착")),
                                             ("보강수", len(후보["보강"]) if isinstance(후보.get("보강"), list) else None))
                           if v is not None}
        후보 = 후보펼치기(후보)
    전용 = [d for d in 후보 if 운영전용(d)]
    if 전용:
        print("운영 동종 전용 %d곳 — βU 표본이 아니라 조립하지 않음: %s"
              % (len(전용), ",".join(str(d.get("티커")) for d in 전용)))
    후보 = [d for d in 후보 if not 운영전용(d)]
    # 평가기준일 **당일** 종가 — 시가총액 분자는 이것을 쓴다(주봉 마지막 캔들이 아니다)
    일종가 = 피경.종가읽기(PEER, 기준일)
    if not 일종가:
        sys.exit("기준일 종가 캐시(%s)가 없습니다 — 사슬 중간 층(peer_기준일종가)을 먼저" % os.path.basename(피경.종가파일(PEER, 기준일)))
    지수 = 주봉(a.지수)
    if not 지수:
        sys.exit("시장지수 주봉이 없습니다 (%s)" % a.지수)

    # 대상회사
    대상주봉 = 주봉(대상티커)
    대상없음 = False
    if 대상주봉 and a.밴드생략 and len(날짜정렬(대상주봉, 지수)[0]) < 30:
        print("대상 %s 주봉의 주 라벨이 지수와 안 맞는다(다른 시장 — 휴장 · 시간대) — 잔차상관을 내지 않는다(βL · βU 는 그대로)" % 대상티커)
        대상주봉 = None
    if not 대상주봉:
        if not a.밴드생략:
            sys.exit("대상회사 %s 의 주봉이 없습니다 — naver_price.py 를 먼저 돌립니다" % 대상티커)
        대상없음 = True                     # 해외 경로 ⑤ — 대상 짝 없이 βL · βU 만 낸다(잔차상관은 국내 조립기 · 병합 뒤 사람이 본다)
        대상주봉 = 지수
    i대, i시 = 날짜정렬(대상주봉, 지수)
    i수익 = 로그수익([v for _, v in i대])
    i시수익 = 로그수익([v for _, v in i시])
    ib, ir2, i잔차, in_ = 회귀(i수익, i시수익)
    if a.밴드생략:
        # 해외 동종 경로 ⑤(S7-02) — 대상회사가 다른 시장(국내 상장)이라 대상 시가총액이 다른 통화다. 규모대는 C1(매출 · 환산)과
        # CP1 이 이미 걸었다 — 이 조립에서는 밴드를 걸지 않고 대상은 잔차상관의 짝(주봉)으로만 쓴다
        대상종가 = (일종가.get(대상티커) or {}).get("종가") or i대[-1][1]
        대상시총 = None
        print("대상 %s: 해외 동종 경로(--밴드생략) — 규모대는 C1 · CP1 이 이미 걸었다 · 대상은 잔차상관의 짝(주봉 %d주)으로만 쓴다"
              % (대상티커, len(i대)))
    else:
        대상종가 = 일종가[대상티커]["종가"]
        대상시총 = 대상종가 * 대상주식수
        print("대상 %s: 평가기준일 당일 종가 %s(%s) × 유통 %d = 시가총액 %.2f bn USD"
              % (대상티커, 대상종가, 일종가[대상티커]["일자"], 대상주식수, 대상시총 / 1e9))
        print("           주식수 근거: %s (%s)"
              % (대상.get("종류", "-"), 대상.get("주식수기준일", "-")))
        print("           (참고: 주봉 기준 직전 캔들 %s@%s — %.1f%% 차이)"
              % (i대[-1][1], i대[-1][0], (i대[-1][1] / 대상종가 - 1) * 100))
    print("           관측베타 %.3f · 결정계수 %.3f · 표본 %d주 (회귀 창 %s~%s · %s · 사양 %s주)"
          % (ib, ir2, in_, 창시작, 기준일, "--부터 지정" if a.부터 else "%d년 주간" % a.창년,
             "-" if a.부터 else 52 * a.창년))
    if 대상시총 is None:
        하한, 상한 = 0.0, float("inf")
    else:
        하한, 상한 = 대상시총 / a.밴드, 대상시총 * a.밴드
        print("           선언 규모대 1/%g~%g배 = %.2f bn ~ %.2f bn USD\n"
              % (a.밴드, a.밴드, 하한 / 1e9, 상한 / 1e9))

    행 = []
    for d in 후보:
        t = d["티커"]
        r = {"티커": t, "회사명": d.get("회사명"), "경로": d.get("경로", ""),
             "sic": d.get("sic"), "sic설명": d.get("sic설명")}
        # 주식수
        sp = os.path.join(PEER, "shares_%s.json" % t)
        분모 = 분모일 = 종류 = 비고 = None
        if t in 주식수_대체:
            분모, 분모일, 종류, 비고 = 주식수_대체[t]
        elif os.path.exists(sp):
            s = 읽자(sp)
            dei = s.get("유통_dei")
            usg = s.get("발행_usgaap")
            # **dei 표지 태그가 옛 날짜에서 멈춘 회사가 있다.** 실측(RXRX 회차): dei 는
            # 2021-04-30 168,320,745 에서 멈췄고 us-gaap 은 2026-06-30 534,120,235 이었다.
            # dei 를 무조건 먼저 쓰면 시가총액이 3분의 1로 잡혀 규모대 컷이 통째로 어긋난다.
            # **둘 중 기준일에 더 가까운 쪽을 쓰고, 어느 쪽을 왜 썼는지 적는다.**
            if dei and usg and usg["end"] > dei["end"]:
                분모, 분모일 = usg["val"], usg["end"]
                종류 = "발행/유통(us-gaap)"
                비고 = ("dei 표지가 %s 에서 멈춰 us-gaap %s 을 씀 — 유통 여부 확인 필요"
                      % (dei["end"], usg["end"]))
            elif dei:
                분모, 분모일, 종류 = dei["val"], dei["end"], "유통(dei 표지)"
                tre = s.get("자기주식")
                비고 = ("자기주식 %d주 별도 보고 — dei 표지 값은 유통 기준" % tre["val"]) if tre else ""
            elif usg:
                분모, 분모일 = usg["val"], usg["end"]
                종류 = "발행/유통(us-gaap)"
                비고 = "dei 표지 태그 없음 — us-gaap 값을 씀. 유통 여부 확인 필요"
            if usg and 분모 == usg.get("val") and usg.get("태그") == "CommonStockSharesIssued":
                tre = s.get("자기주식")                        # 1.1.2(H12) — 발행주식수는 자기주식을 담는다 — 같은 날 자기주식을 빼 유통으로
                if tre and tre.get("end") == usg.get("end") and isinstance(tre.get("val"), (int, float)) and 0 < tre["val"] < usg["val"]:
                    분모 = usg["val"] - tre["val"]
                    종류 = "유통(us-gaap 발행 − 자기주식)"
                    비고 = (비고 + " · " if 비고 else "") + "발행 %d주 − 자기주식 %d주(%s)" % (usg["val"], tre["val"], tre["end"])
                else:
                    비고 = (비고 + " · " if 비고 else "") + "발행주식수(자기주식 포함)일 수 있다 — 같은 날 자기주식 값이 없다"
        # ── 외국 신고인(20-F·40-F)의 주식수 — **자동으로 확정하지 않는다** ──
        # 실측 셋(미국 사슬 시험 2026-09-10):
        #   TM  — dei 2026-03(신선), ADS비율 10. 나누면 $219.5bn(맞음), 안 나누면 $2,195bn.
        #   HMC — dei 가 **2020-03 에서 멈췄고** usgaap 은 2014. 어느 쪽을 곱해도 2026 시총이 아니다.
        #   RACE — dei 2020-12. 현재 주식수와 우연히 4% 차라 그럴듯해 **보이는** 것이 더 위험하다.
        # 표지의 dei 값이 보통주인지 ADS 수인지도 회사마다 갈린다. 그래서:
        #   · ADS비율 1(또는 없음) + 주식수가 신선(기준일 ± 1년) → 그대로 쓴다
        #   · ADS비율 > 1 → **후보 시총 둘(나눔/그대로)을 비고에 적고 시가총액은 세우지 않는다**
        #     — 표지 문장(sec_표지주식수)·ads 근거문장을 보고 사람이 주식수_대체.json 에 확정한다
        #   · 주식수 기준일이 평가기준일에서 1년 넘게 멀다 → 묵은 주식수 × 오늘 종가는 틀린 값
        #     — 시가총액을 세우지 않고 「묵음」으로 적는다
        ads경로 = os.path.join(PEER, "ads_%s.json" % t)
        _sub경로 = os.path.join(PEER, "sub_%s.json" % t)
        _외국 = False
        if os.path.exists(_sub경로):
            _외국 = bool(set((읽자(_sub경로).get("최근서류") or {}).keys())
                       & {"20-F", "40-F", "20-F/A", "40-F/A"})
        r["ADS비율"] = None
        if t not in 주식수_대체 and 분모 and 분모일:
            _한계 = "%04d%s" % (int(기준일[:4]) - 1, 기준일[4:8])   # 평가기준일 1년 전
            _묵음 = str(분모일).replace("-", "")[:8] < _한계
            _비율 = None
            if os.path.exists(ads경로):
                _ads = 읽자(ads경로)
                _비율 = _ads.get("ADS비율")
                r["ADS비율"] = _비율
            if _묵음:
                비고 = ((비고 + " ｜ " if 비고 else "")
                      + "주식수 기준일 %s 가 평가기준일에서 1년 넘게 묵음 — 표지 확인 전에는 시가총액을 세우지 않는다" % 분모일)
                분모 = None
            elif _비율 and float(_비율) > 1:
                _나눔 = 분모 / float(_비율)
                비고 = ((비고 + " ｜ " if 비고 else "")
                      + "ADS비율 %s — dei 값이 보통주면 ADS %s주, 이미 ADS 수면 %s주. "
                        "표지 문장으로 확정해 주식수_대체.json 에 적으십시오 (%s)"
                      % (_비율, format(int(_나눔), ","), format(int(분모), ","), _ads.get("폼", "20-F")))
                분모 = None
            elif _외국 and (not os.path.exists(ads경로) or not _비율):
                # S7-03 — ads 파일은 있는데 배율을 못 읽은(null) 외국 신고인도 막는다. 실측(TSM 20-F 2025): 근거문장은 ADS 를 말하는데
                # 배율이 null 이라 보통주 수 × ADS 종가로 시가총액이 다섯 배(12.4조 달러)로 섰다
                비고 = ((비고 + " ｜ " if 비고 else "")
                      + ("외국 신고인인데 ADS 배율 미확인(sec_ads비율 미실행)" if not os.path.exists(ads경로) else
                         "외국 신고인인데 ADS 배율을 못 읽었다(ads 근거문장만 있음 — 표지로 확정해 주식수_대체.json 에)")
                      + " — 시가총액을 세우지 않는다")
                분모 = None
        r.update({"주식수분모": 분모, "주식수기준일": 분모일, "분모종류": 종류, "주식수비고": 비고})

        w = 주봉(t)
        if not w:
            r["시세"] = "조회 실패"
            행.append(r)
            continue
        c대, c시 = 날짜정렬(w, 지수)
        일 = 일종가.get(t) or {}
        r["종가"] = 일.get("종가")
        r["종가일"] = 일.get("일자")
        r["주봉종가"] = c대[-1][1] if c대 else None
        r["주봉종가일"] = c대[-1][0] if c대 else None
        r["표본주"] = max(len(c대) - 1, 0)
        r["시가총액"] = (r["종가"] * 분모) if (r["종가"] and 분모) else None
        # 회귀는 대상회사와 겹치는 주만
        공통 = [x for x, _ in c대 if x in dict(i대)]
        v대 = [dict(c대)[x] for x in 공통]
        v시 = [dict(c시)[x] for x in 공통]
        v이 = [dict(i대)[x] for x in 공통]
        y = 로그수익(v대)
        x = 로그수익(v시)
        yi = 로그수익(v이)
        b, r2, res, n = 회귀(y, x)
        _, _, resi, _ = 회귀(yi, x)
        s, _ = 상관(y, yi)
        j, jn = 상관(res, resi) if res and resi else (None, 0)
        if 대상없음:
            s, j, jn = None, None, n          # 대상 짝 없음 — 상관 표본 수는 회귀 표본 수로(2차 컷의 자료 기준)
        r.update({"베타": b, "결정계수": r2, "회귀표본": n,
                  "단순상관": s, "잔차상관": j, "상관표본": jn})
        # 3년 창 대안 사양(「3년 창으로 잰 값은 대안 사양으로 병기」, S7-06) — 같은 주봉의 뒤 3년만
        삼시작 = "%04d%s" % (int(기준일[:4]) - 3, 기준일[4:])
        공3 = [x for x in 공통 if x >= 삼시작]
        b3, r23, _, n3 = 회귀(로그수익([dict(c대)[x] for x in 공3]), 로그수익([dict(c시)[x] for x in 공3]))
        r.update({"베타_3년": b3, "결정계수_3년": r23, "표본주_3년": n3})
        행.append(r)

    # ── 2차 컷: 시가총액 규모대 + 사업 단계(표본 주수) ──
    통과, 탈락 = [], []
    for r in 행:
        t = r["티커"]
        if r.get("시가총액") is None:
            탈락.append((r, "2. 자료 부재", "유통주식수 또는 종가 확인 불가 → 시가총액 산출 불가"))
            continue
        if not (하한 <= r["시가총액"] <= 상한):
            탈락.append((r, "4. 목적 불일치",
                       "규모대 밖 (%.2f bn, 선언 밴드 %.2f~%.2f bn)"
                       % (r["시가총액"] / 1e9, 하한 / 1e9, 상한 / 1e9)))
            continue
        if (r.get("상관표본") or 0) < a.최소주:
            탈락.append((r, "2. 자료 부재",
                       "주간 관측 %d주 < 선언한 %d주 (상장 경과 부족·티커 변경 등)"
                       % (r.get("상관표본") or 0, a.최소주)))
            continue
        통과.append(r)

    통과.sort(key=lambda z: -(z.get("잔차상관") if z.get("잔차상관") is not None else -9))
    머리["대상"] = 대상티커
    json.dump({"머리": 머리, "행": 통과}, io.open(산출통과, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump({"머리": 머리, "행": [{"티커": r["티커"], "회사명": r.get("회사명"), "경로": r["경로"],
                                  "시가총액": r.get("시가총액"), "상관표본": r.get("상관표본"),
                                  "분류": c, "사유": w} for r, c, w in 탈락]},
              io.open(산출탈락, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("1차 통과 %d곳 → 2차 통과 %d곳 · 탈락 %d곳\n" % (len(행), len(통과), len(탈락)))
    print("%-6s %-9s %-28s %9s %7s %7s %7s %7s %6s"
          % ("티커", "경로", "회사명", "시총(bn)", "베타", "R²", "단순", "잔차", "표본"))
    for r in 통과:
        def g(v, f="%7.3f"):
            return "    n/a" if v is None else f % v
        print("%-6s %-9s %-28s %9.2f %s %s %s %s %6d"
              % (r["티커"], r["경로"], str(r["회사명"])[:28], r["시가총액"] / 1e9,
                 g(r.get("베타")), g(r.get("결정계수")), g(r.get("단순상관")),
                 g(r.get("잔차상관")), r.get("상관표본") or 0))

    print("\n── 2차 탈락 ──")
    for r, c, w in sorted(탈락, key=lambda z: -(z[0].get("시가총액") or 0)):
        print("  %-6s %-9s %-26s [%s] %s"
              % (r["티커"], r["경로"], str(r.get("회사명"))[:26], c, w))

    # ── 잡음 문턱 ──
    표본들 = [r["상관표본"] for r in 통과 if r.get("상관표본")]
    if 표본들:
        n중앙 = sorted(표본들)[len(표본들) // 2]
        문턱 = 2.0 / math.sqrt(n중앙)
        넘음 = [r for r in 통과 if (r.get("잔차상관") or 0) > 문턱]
        낮은 = [r for r in 통과 if r.get("결정계수") is not None and r["결정계수"] < 0.16]
        print("\n── 잡음 문턱 ──")
        print("  표본 %d주 → 상관 표준오차 %.3f · **문턱(2배) %.3f**"
              % (n중앙, 1 / math.sqrt(n중앙), 문턱))
        print("  문턱을 넘는 후보 **%d곳** / 2차 통과 %d곳" % (len(넘음), len(통과)))
        print("  결정계수 0.16 미만 %d곳 / %d곳" % (len(낮은), len(통과)))
        if len(넘음) < 8:
            print("  ※ 문턱을 넘는 곳이 8곳에 못 미칩니다. 상관으로는 거기까지만 자르고")
            print("     남는 자리는 사업 접점(값과 무관한 기준)으로 채우고 그렇게 했다고 적습니다.")

    with io.open(산출csv, "w", newline="", encoding="utf-8-sig") as f:
        cols = ["티커", "회사명", "경로", "sic", "sic설명", "종가", "종가일", "주식수분모",
                "주식수기준일", "분모종류", "ADS비율", "시가총액", "베타", "결정계수", "단순상관",
                "잔차상관", "상관표본", "표본주", "베타_3년", "결정계수_3년", "표본주_3년", "주식수비고"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in sorted(행, key=lambda z: -(z.get("잔차상관") if z.get("잔차상관") is not None else -9)):
            w.writerow(r)
    print("\n→ %s\n→ %s · %s" % (산출csv, 산출통과, 산출탈락))

    # ── βU·현금보정 단계(세율을 줬을 때만 — 기본값 없음) ──
    if a.세율 is not None:
        import subprocess
        sys.stdout.flush()
        인자 = [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "peer_βU_us.py"),
              "--세율", str(a.세율), "--기준일", "%s-%s-%s" % (기준일[:4], 기준일[4:6], 기준일[6:8]),
              "--조립csv", 산출csv, "--캐시", PEER, "--출력", "βU_%s" % 표본, "--대상", 대상티커]
        if a.스크린:
            인자 += ["--스크린", a.스크린]
        if getattr(a, "세율표", None):
            인자 += ["--세율표", a.세율표]
        if getattr(a, "재무기준일", None):
            인자 += ["--재무기준일", a.재무기준일]
        r = subprocess.run(인자, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        if r.returncode != 0:
            sys.exit("peer_βU_us.py 가 실패했습니다")
    else:
        print("※ --세율 을 안 줬으므로 βU·현금보정 표는 만들지 않았습니다 — "
              "peer_βU_us.py --세율 … --조립csv %s 로 이어 돌리십시오" % os.path.basename(산출csv))


if __name__ == "__main__":
    main()

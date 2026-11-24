# -*- coding: utf-8 -*-
"""갭해석 — 평가기준일 종가와 이 평가의 값이 벌어진 자리를 값을 바꾸지 않고 가른다(1.1.3).

    python 스크립트/갭해석.py <가정.json> [--낼 _raw/갭해석.json] [--자리 <회차 폴더>]
    python 스크립트/갭해석.py 지수받기 <가정.json> [--자리 <회차 폴더>]      # 레터_지수.csv(대표 지수 일봉 · F 앞 ~ T) — 네트워크

**기준 · 비관 · 낙관 시나리오의 값을 바꾸지 않는다.** 엔진(엔진.계산)이 낸 값만 읽고, 보조 판은 엔진으로 따로 셈해 곁에 적는다.
설정은 `스크립트/갭해석설정.json` 한 곳이다(문턱 · 할인 몫 · 분위 · 지수). 회사 · 업종 이름은 이 도구에 없다.

  ① 위치(범위 밖 신호)   종가가 비관 ~ 낙관 주당가치 밖이면 「범위 밖」(아래 · 위). 로그 위치 = ln(종가 ÷ 비관) ÷ ln(낙관 ÷ 비관) — 0 비관 · 1 낙관
  ② 시장변동(날짜 둘)    재무 자료 기준일 F 종가 기준 갭 ln(F 종가 ÷ (기준 주당 ÷ 이월계수)) · 평가기준일 T 종가 기준 갭 ln(T 종가 ÷ 기준 주당) ·
                         같은 기간 대표 지수(표시통화 시장 — 국내 KOSPI · 미국 S&P 500)의 로그 변동. 지수가 문턱(로그 ±15%)을 넘게 움직였으면
                         「T 시장 자료(내재 ERP · CRP · 국채)를 평가기준일 판으로 다시 받았는지」 경보. 지수는 회차 폴더의 `레터_지수.csv`(date,close)
  ③ 지주(보조 시나리오)  지분성 비영업 순평가(관계기업 · 장기투자 · 지분 줄) ÷ 주주가치 ≥ 문턱(20%) 이거나 원고 `관측.종속기업` 에 상장 회사가 있으면
                         할인 판(30% · 50%) · 상장 지분 시가 대조(SOTP 한 줄) · 비지배 대칭 대안(그 부문을 더한 배수와 같은 배수로 비지배를 뺀다).
                         브리지는 선형이라 판마다 Δ주당 = −Δ주주가치(재무기준일) × 이월계수 × 환산배율 ÷ 적용주식수 — 평가 차손에는 세효과가 없다(엔진과 같다)
  ④ 배수 대조            모델 값 · 종가가 뜻하는 EV/EBIT(내년 · 실적) · PER(내년 — 근사)와 동종(유사기업 βU 재료의 회사) 실적 EV/EBIT · PER 분포.
                         모델 값의 실적 EV/EBIT 가 동종 사분위 밖이면 「압축」 표시(동종 셋 미만이면 표시하지 않는다). 동종 내년 배수는 컨센서스 없이 비운다
  ⑤ 시나리오 폭          비관 · 낙관의 매출 연평균 증가율 · 마지막 해 영업이익률을 실측 분포(실적 열 + 원고 `관측.실측분포`)의 10 ~ 90 분위와 견준다.
                         폭이 좁으면 경보 · 현재 마진 외삽 판(영구기간 영업이익률 = 최근 실적 열) · 범위 밖이면 「시장 판」(종가 쪽 시나리오의 영구 영업이익률을
                         실측 분위 끝으로) · 이름표 「○○년 수준」 과 그 해 실적 · 이름표의 방향 말과 가정 값의 방향 대조
  ⑥ 영구성장률 짝        `엔진/민감도.g짝판` — ERP 출처의 끝 성장 · g 상한(영구기간 무위험이자율) · 영구 ROIC > 영구 WACC 면 「g = 무위험 근처」 판

산출 가정 곁 `_raw/갭해석.json` — 「갭해석/1」: 형식 · 만든날 · 가정해시 · 평가기준일 · 위치 · 시장변동 · 지주 · 배수 · 시나리오폭 · 영구짝 · 신호[] ·
값을바꿈: false. 레터는 장부 키 「파일:갭해석:…」 로 숫자를 부른다(게이트가 해시로 같은 파일인지 본다).
종료 코드 — 0 통과 · 2 입력오류(가정 파일 없음 · JSON 깨짐 · 엔진 계산 실패).
"""
from __future__ import annotations

import argparse
import csv
import datetime
import glob
import hashlib
import io
import json
import math
import os
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 입력오류  # noqa: E402

형식 = "갭해석/1"
산출이름 = "갭해석.json"
설정파일 = os.path.join(여기, "갭해석설정.json")
지분성격줄 = ("8", "105", "111", "112", "113")          # 11번 — 관계기업(원천 20) · 장기투자자산(23) · 지분 줄(110 + v) — `엔진/noa.지분성격줄` 과 같은 자리


def 설정():
    try:
        with io.open(설정파일, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _n(x):
    if x is None or isinstance(x, bool):
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(v) or math.isinf(v) else v


def _ln(a, b):
    a, b = _n(a), _n(b)
    return math.log(a / b) if (a and b and a > 0 and b > 0) else None


def 분위(xs, q):
    """선형 보간 분위(0 ~ 1). 비면 None."""
    xs = sorted(x for x in xs if _n(x) is not None)
    if not xs:
        return None
    if len(xs) == 1:
        return xs[0]
    k = (len(xs) - 1) * q
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def 관할(가정):
    m = (가정.get("메타") or {}) if isinstance(가정, dict) else {}
    k = ("%s" % (m.get("관할") or "")).strip().upper()
    if k:
        return k
    return {"KRW": "KR", "USD": "US"}.get(("%s" % (m.get("표시통화") or "KRW")).strip().upper(), "기타")


def _요(R):
    return R.get("요약") or {}


def 주당계수(가정, R):
    """재무기준일 주주가치 1(금액 단위)이 평가기준일 주당가치를 얼마나 움직이나 — 이월계수(이월 판 · 적용일 때) × 환산배율 ÷ 적용주식수."""
    요 = _요(R)
    배 = float(((가정.get("메타") or {}).get("환산배율")) or 1)
    주 = _n(요.get("적용주식수"))
    이 = _n(요.get("이월계수")) if 요.get("이월적용", True) and _n(요.get("이월계수")) else 1.0
    return (이 * 배 / 주) if 주 else None


def 재무기준일주주(R):
    요 = _요(R)
    v = _n(요.get("재무기준일주주가치"))
    return v if v is not None else _n(요.get("주주가치"))


# ══════════════════════════════════════════════════════════════════ ① 위치
def 위치(R들, 종가):
    비, 기, 낙 = (_n(_요(R들[s]).get("주당가치")) for s in ("비관", "기준", "낙관"))
    p = _n(종가)
    out = {"비관": 비, "기준": 기, "낙관": 낙, "종가": p, "로그위치": None, "범위": None}
    if p is None or 비 is None or 낙 is None:
        out["까닭"] = "종가 또는 시나리오 주당가치가 없다"
        return out
    lo, hi = min(비, 낙), max(비, 낙)
    out["범위"] = "아래" if p < lo else ("위" if p > hi else "안")
    if 비 > 0 and 낙 > 0 and p > 0 and abs(math.log(낙 / 비)) > 1e-12:
        out["로그위치"] = math.log(p / 비) / math.log(낙 / 비)
    out["기준갭"] = _ln(p, 기)
    return out


# ══════════════════════════════════════════════════════════════════ ② 시장변동(날짜 둘)
def _csv줄(p):
    try:
        import 레터궤적 as _궤                              # noqa: PLC0415 — 레터_주가.csv 와 같은 꼴(「#」 주석 · date,close)
        return _궤.읽기(p)
    except Exception:                                    # noqa: BLE001
        return None


def _그날앞(줄, 날):
    """날짜 차례 [[날, 값]] 에서 그날(없으면 그 앞 마지막 거래일)의 (날, 값)."""
    앞 = [(d, v) for d, v in (줄 or []) if ("%s" % d)[:10] <= 날]
    return 앞[-1] if 앞 else (None, None)


def 시장변동(가정, R, 자리, 설=None, 종가=None):
    설 = 설 or 설정()
    s = 설.get("시장변동") or {}
    import 기준일 as _기                                    # noqa: PLC0415
    경 = _기.자료경계(가정)
    if not 경.get("이월"):
        return {"날짜둘": False}
    F, T = 경["F"], 경["T"]
    out = {"날짜둘": True, "F": F, "T": T, "문턱로그": float(s.get("문턱로그") or 0.15), "경보": []}
    기주 = _n(_요(R).get("주당가치"))
    이 = _n(R.get("2.DCF", {}).get("164")) or _n(_요(R).get("이월계수")) or 1.0
    VF = (기주 / 이) if 기주 is not None and 이 else None
    주 = _csv줄(os.path.join(자리, "레터_주가.csv")) or {}
    Fd, F종 = _그날앞(주.get("줄"), F)
    Td, T종 = _그날앞(주.get("줄"), T)
    if _n(종가) is not None:
        T종 = _n(종가)
    out.update({"F주당": VF, "T주당": 기주, "F종가": F종, "F종가일": Fd, "T종가": T종, "이월계수": 이,
                "F갭": _ln(F종, VF), "T갭": _ln(T종, 기주), "주가로그": _ln(T종, F종), "주가출처": 주.get("출처")})
    if out["F갭"] is not None and out["T갭"] is not None:
        out["갭변동"] = out["T갭"] - out["F갭"]
    if F종 is None:
        out["경보"].append("재무 자료 기준일 종가를 못 읽었다(레터_주가.csv 가 없거나 그 날 앞 거래일이 없다) — F 갭을 셈하지 않았다")
    관 = 관할(가정)
    지설 = (s.get("지수") or {}).get(관) or {}
    out["지수이름"] = 지설.get("이름")
    지 = _csv줄(os.path.join(자리, s.get("파일") or "레터_지수.csv")) or {}
    if 지.get("줄"):
        a, av = _그날앞(지["줄"], F)
        b, bv = _그날앞(지["줄"], T)
        out.update({"지수F": av, "지수F일": a, "지수T": bv, "지수T일": b, "지수로그": _ln(bv, av), "지수출처": 지.get("출처") or 지설.get("출처")})
        if out["지수로그"] is not None and out.get("주가로그") is not None:
            out["지수밖로그"] = out["주가로그"] - out["지수로그"]
    else:
        out["지수로그"] = None
        out["경보"].append("대표 지수(%s) 일봉을 못 읽었다 — `python 스크립트/갭해석.py 지수받기 <가정>` 이 회차 폴더에 %s 를 쓴다"
                         % (지설.get("이름") or 관, s.get("파일") or "레터_지수.csv"))
    if out.get("지수로그") is not None and abs(out["지수로그"]) > out["문턱로그"]:
        근 = json.dumps(가정.get("WACC근거") or {}, ensure_ascii=False)
        out["T판표지"] = T in 근
        out["경보"].append("재무 자료 기준일과 평가기준일 사이 %s 지수가 로그 %+.1f%% 움직였다(문턱 ±%.0f%%) — T 시장 자료(내재 ERP · CRP · 국채)를 "
                         "평가기준일 판으로 다시 받았는지 본다%s" % (out.get("지수이름") or "대표", 100 * out["지수로그"], 100 * out["문턱로그"],
                                                         "" if out["T판표지"] else " — WACC 근거에 평가기준일(%s) 표지가 없다" % T))
    return out


def 지수받기(가정, 자리, 설=None):
    """레터_지수.csv — 표시통화 시장의 대표 지수 일봉(F 앞 30일 ~ T). 국내 KOSPI(네이버 지수 창구) · 미국 S&P 500(야후 ^GSPC). → (경로, 줄 수)."""
    import urllib.request                                   # noqa: PLC0415
    import urllib.parse                                     # noqa: PLC0415
    import 기준일 as _기                                    # noqa: PLC0415
    설 = 설 or 설정()
    s = 설.get("시장변동") or {}
    관 = 관할(가정)
    지설 = (s.get("지수") or {}).get(관)
    if not 지설:
        raise ValueError("관할 %s 의 대표 지수가 설정에 없다(갭해석설정.json 「시장변동.지수」)" % 관)
    F, T = _기.재무기준일(가정), _기.평가기준일(가정)
    시작 = F - datetime.timedelta(days=30)
    줄 = []
    if 관 == "KR":
        u = ("https://api.finance.naver.com/siseJson.naver?symbol=%s&requestType=1&startTime=%s&endTime=%s&timeframe=day"
             % (지설["코드"], 시작.strftime("%Y%m%d"), T.strftime("%Y%m%d")))
        글 = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read().decode("utf-8", "ignore")
        for 행 in 글.splitlines():
            칸 = [c.strip().strip("'\"[] ") for c in 행.split(",")]
            if len(칸) >= 5 and 칸[0].isdigit() and len(칸[0]) == 8:
                줄.append(("%s-%s-%s" % (칸[0][:4], 칸[0][4:6], 칸[0][6:]), float(칸[4])))
    else:
        p1 = int(datetime.datetime(시작.year, 시작.month, 시작.day, tzinfo=datetime.timezone.utc).timestamp())
        p2 = int(datetime.datetime(T.year, T.month, T.day, tzinfo=datetime.timezone.utc).timestamp()) + 86400
        u = "https://query1.finance.yahoo.com/v8/finance/chart/%s?period1=%d&period2=%d&interval=1d" % (urllib.parse.quote(지설["코드"]), p1, p2)
        d = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read().decode("utf-8"))
        r = ((d.get("chart") or {}).get("result") or [None])[0] or {}
        ts, cl = r.get("timestamp") or [], (((r.get("indicators") or {}).get("quote") or [{}])[0].get("close") or [])
        for t, c in zip(ts, cl):
            if c is not None:
                줄.append((datetime.datetime.fromtimestamp(t, datetime.timezone.utc).date().isoformat(), float(c)))
    줄 = sorted(x for x in 줄 if x[0] <= T.isoformat())
    if not 줄:
        raise ValueError("지수 일봉을 받지 못했다 — 비슷한 값으로 메우지 않는다")
    p = os.path.join(자리, s.get("파일") or "레터_지수.csv")
    with io.open(p, "w", encoding="utf-8-sig", newline="\n") as f:
        f.write("# %s 일별 지수. 출처 %s. 조회일 %s\n" % (지설.get("이름"), 지설.get("출처"), datetime.date.today().isoformat()))
        f.write("date,close\n")
        for d, c in 줄:
            f.write("%s,%s\n" % (d, c))
    return p, len(줄)


# ══════════════════════════════════════════════════════════════════ ③ 지주
def _비영업H(R, 키):
    비 = ((R.get("NOA") or {}).get("비영업")) or {}
    v = 비.get(키, 비.get(int(키)) if 키.isdigit() else None)
    return _n((v or {}).get("H")) if isinstance(v, dict) else None


def 종속표(가정):
    """원고 `관측.종속기업` [{이름, 종류(종속 · 관계 · 지분), 지분율, 상장, 시가총액, 장부, 순자산, 비지배장부, 배수, 출처, 기준일}] — 꼴이 맞는 줄만."""
    v = (가정.get("관측") or {}).get("종속기업")
    if isinstance(v, dict):
        v = v.get("표") or v.get("줄") or []
    return [x for x in (v or []) if isinstance(x, dict) and ("%s" % (x.get("이름") or "")).strip()]


def 지주(가정, R, 설=None):
    설 = 설 or 설정()
    s = 설.get("지주") or {}
    요 = _요(R)
    주F = 재무기준일주주(R)
    지분 = sum(v for v in (_비영업H(R, k) for k in 지분성격줄) if v)
    비지배 = _n((R.get("NOA") or {}).get("H35")) or 0.0
    몫 = (지분 / 주F) if 주F and 주F > 0 else None
    비몫 = (비지배 / 주F) if 주F and 주F > 0 else None
    표 = 종속표(가정)
    상장 = [x for x in 표 if x.get("상장") is True]
    문, 비문 = float(s.get("지분몫문턱") or 0.20), float(s.get("비지배몫문턱") or 0.05)
    계 = 주당계수(가정, R)
    기주 = _n(요.get("주당가치"))
    out = {"지분성": 지분, "주주가치F": 주F, "지분몫": 몫, "비지배": 비지배, "비지배몫": 비몫, "문턱": 문, "비지배문턱": 비문,
           "종속기업수": len(표), "상장수": len(상장), "주당계수": 계, "기준주당": 기주}
    out["발동"] = bool((몫 is not None and 몫 >= 문) or 상장)
    out["표요건"] = bool((몫 is not None and 몫 >= 문) or (비몫 is not None and 비몫 >= 비문))
    까 = []
    if 몫 is not None and 몫 >= 문:
        까.append("지분성 비영업이 주주가치의 %.0f%%(문턱 %.0f%%)" % (100 * 몫, 100 * 문))
    if 상장:
        까.append("상장 종속 · 관계기업 %d곳" % len(상장))
    out["발동까닭"] = 까
    if not out["발동"] or 계 is None or 기주 is None:
        return out
    out["할인판"] = [{"할인": d, "주당": 기주 - d * 지분 * 계, "변화": (-d * 지분 * 계 / 기주) if 기주 else None}
                  for d in (s.get("할인") or [0.30, 0.50])]
    원57 = None
    try:
        from 엔진.읽개 import _기준일값, 축내기                # noqa: PLC0415
        원57 = _n(_기준일값(가정, 57, 축내기(가정)))
    except Exception:                                        # noqa: BLE001
        원57 = None
    조정률 = (비지배 / 원57) if 원57 else 1.0
    out["비지배조정률"] = 조정률
    관계차, 비지배차, 대칭차, 줄 = 0.0, 0.0, 0.0, []
    for x in 표:
        종 = ("%s" % (x.get("종류") or "종속")).strip()
        율, 시총 = _n(x.get("지분율")), _n(x.get("시가총액"))
        if 율 is not None and 율 > 1:
            율 = 율 / 100.0
        장부, 비장 = _n(x.get("장부")), _n(x.get("비지배장부"))
        한 = {"이름": "%s" % x.get("이름"), "종류": 종, "지분율": 율, "상장": x.get("상장") is True, "시가총액": 시총, "장부": 장부, "비지배장부": 비장}
        if 한["상장"] and 시총 is not None and 율 is not None:
            if 종 == "종속":
                if 비장 is not None:
                    한["비지배시가"] = 시총 * (1 - 율)
                    비지배차 += 한["비지배시가"] - 비장 * 조정률
            elif 장부 is not None:
                한["지분시가"] = 시총 * 율
                관계차 += 한["지분시가"] - 장부
        배 = _n(x.get("배수"))
        if 배 is None and 종 == "종속" and 시총 is not None and _n(x.get("순자산")):
            배 = 시총 / _n(x.get("순자산"))
        if 배 is not None and 비장 is not None and 종 == "종속":
            한["배수"] = 배
            대칭차 += 비장 * (배 - 조정률)
        줄.append(한)
    out["표"] = 줄
    if any(r.get("지분시가") is not None or r.get("비지배시가") is not None for r in 줄):
        out["시가대조"] = {"관계차": 관계차, "비지배차": 비지배차, "주당": 기주 + (관계차 - 비지배차) * 계,
                       "식": "기준 주당 + (상장 관계 · 지분의 시가 지분 − 장부 − (상장 종속의 비지배 시가 − 비지배 장부 × 조정률)) × 주당계수"}
    if any(r.get("배수") is not None for r in 줄):
        out["대칭"] = {"차": 대칭차, "주당": 기주 - 대칭차 * 계,
                     "식": "비지배는 그 부문을 더한 배수로 뺀다 — 기준 주당 − Σ 비지배 장부 × (배수 − 조정률) × 주당계수"}
    return out


def 배제문장(글, 설=None):
    """「차이는 지주 · 비영업 몫이 아니다」 꼴의 배제 결론 문장 → [문장]. 게이트가 지주 셈 절 없이 이 문장이 서면 막는다."""
    s = ((설 or 설정()).get("지주") or {})
    말, 대 = s.get("배제말") or [], s.get("배제대상말") or []
    낸 = []
    for 문 in [x.strip() for x in ("%s" % 글).replace("\n", " ").split(".") if x.strip()]:
        if any(m in 문 for m in 말) and any(d in 문 for d in 대):
            낸.append(문[:160])
    return 낸


# ══════════════════════════════════════════════════════════════════ ④ 배수 대조
def 내년열(R):
    속 = (R.get("기간") or {}).get("속성") or {}
    for c in ((R.get("기간") or {}).get("묶음") or {}).get("예측") or []:
        if (속.get(c) or {}).get("개월") == 12:
            return c
    return None


def βU재료경로(자리, 가정):
    """1.1.4 — 레터와 같은 고르기(`피어경로.βU재료고르기` — 창 끝 날짜)."""
    import 피어경로                                         # noqa: PLC0415
    r = 피어경로.βU재료고르기(자리, 가정)
    return r["경로"] if r else None


def _재료csv(자리, βU경로):
    """βU 재료 이름과 짝인 `유사기업_재료_<표본>.csv`(βU_핵심예비_T ↔ 유사기업_재료_핵심예비_T) → {종목코드: 행}. 짝이 없으면 빈 사전 —
    1.1.4: 다른 표본(옛 창 · 오염 판)의 csv 를 섞지 않는다(종전에는 가장 짧은 이름을 골랐다)."""
    import 피어경로                                         # noqa: PLC0415
    고 = 피어경로.βU짝csv(자리, βU경로)
    if not 고:
        return {}
    낸 = {}
    try:
        with io.open(고, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                k = ("%s" % (r.get("종목코드") or r.get("티커") or "")).strip()
                if k:
                    낸[k] = r
    except (OSError, ValueError):
        return {}
    return 낸


def _최근해(r, 머리):
    해 = sorted({int(k.rsplit("_", 1)[1]) for k in r if k.startswith(머리 + "_") and k.rsplit("_", 1)[1].isdigit() and _n(r.get(k)) is not None})
    return (_n(r["%s_%d" % (머리, 해[-1])]), 해[-1]) if 해 else (None, None)


def _전체재무(자리):
    """국내 유사기업 조립의 전체 재무(`전체재무_추출.csv` — 고유번호 · 연도 · 보고서 · 영업이익 · 당기순이익) → {고유번호: 최근 사업보고서(11011) 행}."""
    후 = [p for p in (os.path.join(자리, "전체재무_추출.csv"), os.path.join(자리, "_raw", "peers", "전체재무_추출.csv")) if os.path.exists(p)]
    낸 = {}
    if not 후:
        return 낸
    try:
        with io.open(후[0], encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if ("%s" % r.get("보고서")).strip() != "11011" or _n(r.get("영업이익")) is None:
                    continue
                k = ("%s" % r.get("고유번호")).strip()
                if k not in 낸 or ("%s" % r.get("연도")) > ("%s" % 낸[k].get("연도")):
                    낸[k] = r
    except (OSError, ValueError):
        return {}
    return 낸


def 동종배수(자리, 가정):
    """유사기업 βU 재료의 회사(대상 제외)마다 실적 EV/EBIT · PER. 미국 행은 재무 칸(매출 × 영업이익률 · 순이익), 국내 행은 짝 csv 의 최근 해 칸."""
    p = βU재료경로(자리, 가정)
    if not p:
        return [], None
    try:
        d = json.load(io.open(p, encoding="utf-8"))
    except (OSError, ValueError):
        return [], p
    표 = [z for z in (d.get("표") or []) if isinstance(z, dict)]
    c = _재료csv(자리, p)
    재무 = (_전체재무(자리),)
    낸 = []
    for z in 표:
        이름 = "%s" % (z.get("회사명") or z.get("티커") or "")
        if "(대상)" in 이름 or z.get("구분") == "대상":
            continue
        시총, D, 현 = _n(z.get("시가총액")), _n(z.get("D")) or 0.0, _n(z.get("현금·단기투자")) or 0.0
        ebit = ni = None
        해 = None
        재 = z.get("재무") if isinstance(z.get("재무"), dict) else None
        if 재:
            매 = 재.get("매출_최근FY")
            매 = _n(매[1]) if isinstance(매, list) and len(매) > 1 else None
            if 매 is not None and _n(재.get("영업이익률")) is not None:
                ebit = 매 * _n(재["영업이익률"])
            순 = 재.get("순이익_최근FY")
            ni = _n(순[1]) if isinstance(순, list) and len(순) > 1 else None
            해 = (매 and isinstance(재.get("매출_최근FY"), list)) and ("%s" % 재["매출_최근FY"][0])[:4]
        else:
            r = c.get(("%s" % (z.get("종목코드") or z.get("티커") or "")).strip())
            if r:
                ebit, 해 = _최근해(r, "영업이익")
                ni, _h = _최근해(r, "순이익")
                if ebit is None:                              # 재료 csv 의 연도 칸이 비면 같은 조립의 전체 재무(사업보고서 11011 — 고유번호)에서
                    f = 재무[0].get(("%s" % (r.get("고유번호") or "")).strip()) if 재무 is not None else None
                    if f:
                        ebit, ni, 해 = _n(f.get("영업이익")), _n(f.get("당기순이익")), f.get("연도")
                if 시총 is None:
                    시총 = _n(r.get("시가총액"))
                if not D:
                    D = _n(r.get("차입금")) or 0.0
                if not 현:
                    현 = _n(r.get("현금·단기투자")) or 0.0
        ev = (시총 + D - 현) if 시총 is not None else None
        낸.append({"이름": 이름.strip(), "티커": z.get("티커") or z.get("종목코드"), "핵심": z.get("핵심"), "시가총액": 시총, "EV": ev,
                  "EBIT": ebit, "순이익": ni, "실적해": 해,
                  "EV/EBIT": (ev / ebit) if (ev is not None and ebit and ebit > 0) else None,
                  "PER": (시총 / ni) if (시총 and ni and ni > 0) else None})
    return 낸, p


def 배수(가정, R, 종가, 자리, 설=None):
    설 = 설 or 설정()
    s = 설.get("범위밖") or {}
    D = R.get("2.DCF") or {}
    요 = _요(R)
    배율 = float(((가정.get("메타") or {}).get("환산배율")) or 1)
    열, 실열 = 내년열(R), (((R.get("기간") or {}).get("자리") or {}).get("FY실적.끝"))
    EBIT내, EBIT실 = _n((D.get("15") or {}).get(열)) if 열 else None, _n((D.get("15") or {}).get(실열)) if 실열 else None
    EV = _n(요.get("영업가치"))
    주F = 재무기준일주주(R)
    브 = (주F - EV) if (주F is not None and EV is not None) else None
    t = _n((D.get("29") or {}).get(열)) if 열 else None
    Kd = _n(((R.get("WACC") or {}).get("예측기간") or {}).get("Kd"))
    이자부 = _n((R.get("NOA") or {}).get("H30")) or 0.0
    순근 = ((EBIT내 - (Kd or 0.0) * 이자부) * (1 - (t or 0.0))) if EBIT내 is not None else None
    out = {"내년열": 열, "실적열": 실열, "EBIT내년": EBIT내, "EBIT실적": EBIT실, "모델EV": EV, "모델주주F": 주F, "브리지": 브, "순이익내년근사": 순근,
           "PER식": "내년 순이익 근사 = (내년 EBIT − 세전 Kd × 이자부부채) × (1 − 그 열 한계세율)"}

    def 배(a, b):
        return (a / b) if (a is not None and b and b > 0) else None
    out["모델"] = {"EV/EBIT내년": 배(EV, EBIT내), "EV/EBIT실적": 배(EV, EBIT실), "PER내년": 배(주F, 순근)}
    p = _n(종가)
    주 = _n(요.get("적용주식수"))
    if p is not None and 주:
        이 = _n(요.get("이월계수")) if 요.get("이월적용", True) and _n(요.get("이월계수")) else 1.0
        시총F = p * 주 / 배율 / 이
        evp = (시총F - 브) if 브 is not None else None
        out["종가EV"], out["종가시총F"] = evp, 시총F
        out["종가"] = {"EV/EBIT내년": (evp / EBIT내) if (evp is not None and EBIT내 and EBIT내 > 0) else None,
                     "EV/EBIT실적": (evp / EBIT실) if (evp is not None and EBIT실 and EBIT실 > 0) else None, "PER내년": 배(시총F, 순근)}
    동, 경 = 동종배수(자리, 가정)
    out["동종"] = 동
    out["동종재료"] = os.path.relpath(경, 자리) if 경 else None
    q1, q3 = (s.get("사분위") or [0.25, 0.75])
    최소 = int(s.get("최소동종") or 3)
    분 = {}
    for k in ("EV/EBIT", "PER"):
        xs = [x[k] for x in 동 if _n(x.get(k)) is not None]
        분[k] = {"수": len(xs), "하": 분위(xs, q1), "중앙": 분위(xs, 0.5), "상": 분위(xs, q3), "최소": min(xs) if xs else None, "최대": max(xs) if xs else None}
    out["분포"] = 분
    m = out["모델"]["EV/EBIT실적"]
    e = 분["EV/EBIT"]
    if e["수"] >= 최소 and m is not None and e["하"] is not None:
        out["압축"] = "아래" if m < e["하"] else ("위" if m > e["상"] else "안")
    else:
        out["압축"] = None
        out["압축까닭"] = "동종 실적 EV/EBIT 가 %d곳 — %d곳 미만이거나 모델 실적 배수가 없다" % (e["수"], 최소)
    return out


# ══════════════════════════════════════════════════════════════════ ⑤ 시나리오 폭
def _열말(R, c):
    속 = ((R.get("기간") or {}).get("속성") or {}).get(c) or {}
    return 속


def 실측(가정, R):
    """실측 분포 — 실적 열의 영업이익률(2번 15 ÷ 11) · 회계연도 매출 증가율(FY 실적 열 사이) + 원고 `관측.실측분포` {영업이익률 · 매출성장률: {값 [...], 출처}}."""
    D = R.get("2.DCF") or {}
    묶 = (R.get("기간") or {}).get("묶음") or {}
    마, 성 = [], []
    for c in 묶.get("실적") or []:
        a, b = _n((D.get("15") or {}).get(c)), _n((D.get("11") or {}).get(c))
        if a is not None and b:
            마.append(a / b)
    fy = 묶.get("FY실적") or []
    for x, y in zip(fy, fy[1:]):
        a, b = _n((D.get("11") or {}).get(x)), _n((D.get("11") or {}).get(y))
        if a and b and a > 0:
            성.append(b / a - 1)
    출 = {"영업이익률": "실적 열 %d개(2번 15 ÷ 11)" % len(마), "매출성장률": "회계연도 실적 %d개 사이" % len(성)}
    덧 = (가정.get("관측") or {}).get("실측분포")
    if isinstance(덧, dict):
        for k, 목 in (("영업이익률", 마), ("매출성장률", 성)):
            x = 덧.get(k)
            if isinstance(x, dict) and isinstance(x.get("값"), list):
                vs = [_n(v) for v in x["값"] if _n(v) is not None]
                목 += vs
                출[k] += " + 원고 관측.실측분포 %d개(%s)" % (len(vs), x.get("출처") or "출처 없음")
    return {"영업이익률": 마, "매출성장률": 성, "출처": 출}


def _사이클(가정):
    m = ((가정.get("메타") or {}).get("생애주기") or {})
    덧 = m.get("덧표지") or []
    if any("경기" in ("%s" % x) or "순환" in ("%s" % x) or "원자재" in ("%s" % x) for x in 덧):
        return True
    사 = (가정.get("관측") or {}).get("과거사이클")
    return isinstance(사, list) and bool(사)


def _영구이익률판(가정, v, 시나리오):
    from 엔진.계산 import 계산                                # noqa: PLC0415
    import importlib                                          # noqa: PLC0415
    M = importlib.import_module("엔진.민감도")
    a = M.놓기값(가정, M.손잡이풀기("영구이익률", 가정), v, 시나리오)
    return _n(_요(계산(a, 시나리오)).get("주당가치"))


def _해실적마진(R, 해):
    D = R.get("2.DCF") or {}
    for c in ((R.get("기간") or {}).get("묶음") or {}).get("FY실적") or []:
        if "%s" % (_열말(R, c).get("회계연도")) == "%s" % 해:
            a, b = _n((D.get("15") or {}).get(c)), _n((D.get("11") or {}).get(c))
            return (a / b) if (a is not None and b) else None
    return None


_합성꼬리 = "율률기폭세"          # 방향 말 바로 뒤에 붙어 이름씨를 만드는 글자(증가율 · 하강기 · 하락폭 · 증가세) — 방향을 말하지 않는다
_이름씨토씨 = "이가은는을를의도"   # 두 글자 이상 방향 말 바로 뒤의 주격 · 목적격 · 관형격 토씨 — 뒤 서술어(「하락이 뒤로 밀립니다」)가 방향을 정하므로 가리지 않는다


def _방향말(뒤, 방):
    """주체 말 뒤 글에서 가장 먼저 나온 방향 말(말, 부호, 자리). 합성 이름씨의 일부는 건너뛰고, 이름씨로 쓰인 두 글자 방향 말을 만나면 판정하지 않는다(None)."""
    찾 = []
    for 부호, 키 in ((1, "올림"), (-1, "내림")):
        for w in 방.get(키) or []:
            i = 뒤.find(w)
            while i >= 0:
                찾.append((i, -len(w), w, 부호))
                i = 뒤.find(w, i + 1)
    for i, _l, w, 부호 in sorted(찾):
        다음 = 뒤[i + len(w): i + len(w) + 1]
        if len(w) >= 2 and 다음 and 다음 in _합성꼬리:     # 한 글자 줄기(늘 · 줄)의 「늘기」 는 이름씨 꼴 씨끝이라 방향 그대로
            continue
        if len(w) >= 2 and 다음 and 다음 in _이름씨토씨:
            return None, 0, -1
        return w, 부호, i
    return None, 0, -1


def _어절끝까지(글, 처음, 끝):
    """인용을 어절 경계에서 자른다 — 글자 수로 자르면 「매출 증가율이 2」 처럼 숫자 한가운데에서 끊긴다. 앞도 어절 처음까지(「판매가격이」 의 「가격」 에서 시작하지 않는다)."""
    while 처음 > 0 and not 글[처음 - 1].isspace() and 글[처음 - 1] not in ",.;·「(":
        처음 -= 1
    while 끝 < len(글) and not 글[끝].isspace() and 글[끝] not in ",.;·」)":
        끝 += 1
    return 글[처음: 끝].strip()


def 이름표대조(가정, R들, 설=None):
    """시나리오 이름표(시나리오이야기.<비관 · 낙관>.한줄 · 이름)의 「○○년 수준」 과 그 해 실적 영업이익률, 방향 말과 값의 방향."""
    import re                                                 # noqa: PLC0415
    import importlib                                          # noqa: PLC0415
    M = importlib.import_module("엔진.민감도")
    s = ((설 or 설정()).get("시나리오폭") or {})
    허 = float(s.get("수준허용") or 0.002)
    방 = s.get("방향말") or {}
    주 = s.get("주체말") or {}
    기 = R들["기준"]
    낸 = []
    for 쪽 in ("비관", "낙관"):
        이 = (가정.get("시나리오이야기") or {}).get(쪽) or {}
        글 = " ".join("%s" % 이.get(k) for k in ("이름", "한줄") if isinstance(이.get(k), str))
        if not 글.strip():
            continue
        R = R들[쪽]
        끝 = _n(_요(R).get("마지막해영업이익률"))
        for m in re.finditer(r"((?:19|20)\d{2})(?:\s*[~∼\-–]\s*((?:19|20)?\d{2,4}))?\s*년\s*(?:의\s*)?수준", 글):
            a = int(m.group(1))
            b = m.group(2)
            b = int(b) if b and len(b) == 4 else (int(m.group(1)[:2] + b) if b else a)
            값 = [(y, _해실적마진(기, y)) for y in range(min(a, b), max(a, b) + 1)]
            있 = [v for _y, v in 값 if v is not None]
            한 = {"쪽": 쪽, "종류": "수준", "글": m.group(0), "해들": [y for y, _v in 값], "실적": 값, "시나리오끝마진": 끝}
            if not 있 or 끝 is None:
                한["판정"] = "확인 불가"
                한["까닭"] = "그 해 실적 열이 이 모델에 없다" if not 있 else "시나리오 끝 해 영업이익률이 없다"
            else:
                한["판정"] = "같음" if (min(있) - 허 <= 끝 <= max(있) + 허) else "어긋남"
            낸.append(한)
        # 방향 — 주체 말 바로 뒤(12자 안)의 방향 말
        for 주체, 말들 in 주.items():
            for w in 말들:
                for m in re.finditer(re.escape(w), 글):
                    뒤 = 글[m.end(): m.end() + 12]
                    말, 부호, 자리 = _방향말(뒤, 방)
                    if not 말:
                        continue
                    if re.search(r"[가-힣]만(?:\s|$)", 뒤[:자리]):    # 「정체 속도로만 늘어」 — 보조사 「만」 이 방향을 한정한다(기준보다 덜 느는 것도 「늘어」) — 판정하지 않는다
                        continue
                    꼬 = 뒤[자리 + len(말): 자리 + len(말) + 5]
                    if any(x in 꼬 for x in ("않", "못", "없")):  # 「늘지 않고」 · 「오르지 못하고」 — 부정이면 방향을 뒤집는다
                        부호 = -부호
                    if 주체 == "원가":                        # 원가의 「개선 · 회복 · 악화 · 부진」 은 좋고 나쁨(마진 같은 쪽), 「상승 · 증가 · 하락 · 감소」 는 양(마진 반대 쪽)
                        질 = 말 in 질말
                        기대 = 부호 if 질 else -부호
                        잣대 = "마지막해영업이익률"
                    elif 주체 == "마진":
                        기대 = 부호
                        잣대 = "마지막해영업이익률"
                    else:
                        기대 = 부호
                        잣대 = "매출CAGR"
                    if 잣대 == "매출CAGR":
                        v, b0 = M.매출CAGR(R), M.매출CAGR(기)
                    else:
                        v, b0 = _n(_요(R).get(잣대)), _n(_요(기).get(잣대))
                    if v is None or b0 is None:
                        continue
                    차 = v - b0
                    판 = "같음" if (abs(차) < 1e-4 or (차 > 0) == (기대 > 0)) else "어긋남"
                    낸.append({"쪽": 쪽, "종류": "방향", "글": _어절끝까지(글, m.start(), m.end() + 자리 + len(말)), "주체": 주체, "기대": 기대,
                              "잣대": 잣대, "시나리오값": v, "기준값": b0, "판정": 판})
                    break
    # 같은 쪽 · 같은 주체는 한 번만
    본, 낸2 = set(), []
    for x in 낸:
        k = (x["쪽"], x["종류"], x.get("주체") or x.get("글"))
        if k not in 본:
            본.add(k)
            낸2.append(x)
    return 낸2


def 시나리오폭(가정, R들, 위치값, 설=None):
    import importlib                                          # noqa: PLC0415
    M = importlib.import_module("엔진.민감도")
    설 = 설 or 설정()
    s = 설.get("시나리오폭") or {}
    q1, q9 = (s.get("분위") or [0.10, 0.90])
    최소 = int(s.get("최소관측") or 3)
    실 = 실측(가정, R들["기준"])
    out = {"분위": [q1, q9], "실측출처": 실["출처"], "사이클": _사이클(가정), "축": [], "경보": []}
    for 이름, 잣, 값셈 in (("영업이익률", "마지막해영업이익률", lambda R: _n(_요(R).get("마지막해영업이익률"))),
                        ("매출성장률", "매출CAGR", M.매출CAGR)):
        xs = 실[이름]
        시 = {k: 값셈(R들[k]) for k in ("비관", "기준", "낙관")}
        한 = {"이름": 이름, "잣대": 잣, "관측수": len(xs), "실측": sorted(xs), "시나리오": 시}
        if len(xs) >= 최소:
            한["하"], 한["상"] = 분위(xs, q1), 분위(xs, q9)
            lo, hi = min(v for v in 시.values() if v is not None), max(v for v in 시.values() if v is not None)
            한["좁음"] = (hi - lo) < (한["상"] - 한["하"]) - 1e-9
            if 한["좁음"]:
                out["경보"].append("%s — 시나리오 폭 %.1f%% ~ %.1f%% 가 실측 %d ~ %d 분위 %.1f%% ~ %.1f%%(관측 %d)보다 좁다"
                                 % (이름, 100 * lo, 100 * hi, round(100 * q1), round(100 * q9), 100 * 한["하"], 100 * 한["상"], len(xs)))
        else:
            한["좁음"] = None
            한["까닭"] = "실측 관측 %d개 — %d개 미만이라 분위를 내지 않는다(원고 `관측.실측분포` 로 과거 사이클 값을 더한다)" % (len(xs), 최소)
        out["축"].append(한)
    D = R들["기준"].get("2.DCF") or {}
    실열 = ((R들["기준"].get("기간") or {}).get("묶음") or {}).get("실적") or []
    최근 = None
    for c in reversed(실열):
        a, b = _n((D.get("15") or {}).get(c)), _n((D.get("11") or {}).get(c))
        if a is not None and b:
            최근 = (c, a / b)
            break
    if 최근:
        try:
            out["현재마진판"] = {"열": 최근[0], "영구이익률": 최근[1], "주당": _영구이익률판(가정, 최근[1], "기준"),
                              "뜻": "영구기간 영업이익률을 최근 실적 열의 영업이익률로 둔 판(최근 실적을 그대로 잇는 시장의 셈)"}
        except Exception as e:                               # noqa: BLE001
            out["현재마진판"] = {"열": 최근[0], "영구이익률": 최근[1], "주당": None, "까닭": "%s" % e}
    범 = (위치값 or {}).get("범위")
    if 범 in ("아래", "위"):
        쪽 = "낙관" if 범 == "위" else "비관"
        mx = next((x for x in out["축"] if x["이름"] == "영업이익률"), {})
        끝 = mx.get("상") if 범 == "위" else mx.get("하")
        지금 = _n(_요(R들[쪽]).get("영구기간영업이익률"))
        후 = [v for v in (끝, (out.get("현재마진판") or {}).get("영구이익률")) if v is not None]
        v = (max(후) if 범 == "위" else min(후)) if 후 else None
        if v is not None and 지금 is not None and ((범 == "위" and v > 지금) or (범 == "아래" and v < 지금)):
            try:
                주 = _영구이익률판(가정, v, 쪽)
            except Exception:                                # noqa: BLE001
                주 = None
            out["시장판"] = {"바탕": 쪽, "영구이익률": v, "바탕영구이익률": 지금, "주당": 주,
                          "닿음": (주 is not None and 위치값.get("종가") is not None and ((범 == "위" and 주 >= 위치값["종가"]) or (범 == "아래" and 주 <= 위치값["종가"]))),
                          "뜻": "종가 쪽 시나리오(%s)의 영구기간 영업이익률을 실측 분위 끝 · 현재 마진 가운데 그 쪽 끝으로 옮긴 판" % 쪽}
        else:
            out["시장판"] = {"바탕": 쪽, "주당": None, "까닭": "실측 분위 끝 · 현재 마진이 그 시나리오의 영구기간 영업이익률보다 종가 쪽에 있지 않다"}
    out["이름표"] = 이름표대조(가정, R들, 설)
    for x in out["이름표"]:
        if x["판정"] == "어긋남":
            if x["종류"] == "수준":
                out["경보"].append("%s 이름표 「%s」 — 그 해 실적 영업이익률(%s)과 시나리오 끝 해 %.1f%% 가 %.1f%%p 넘게 다르다" % (
                    x["쪽"], x["글"], " · ".join("%s년 %.1f%%" % (y, 100 * v) for y, v in x["실적"] if v is not None), 100 * x["시나리오끝마진"], 100 * 허(설)))
            else:
                out["경보"].append("%s 이름표 「%s」 의 방향과 가정 값의 방향이 반대다(%s %.2f%% · 기준 %.2f%%)" % (
                    x["쪽"], x["글"], x["잣대"], 100 * x["시나리오값"], 100 * x["기준값"]))
    return out


질말 = ("개선", "회복", "호조", "반등", "악화", "부진", "침체")       # 원가 · 마진의 좋고 나쁨을 말하는 낱말(양을 말하는 낱말과 원가에서 방향이 갈린다)


def 허(설):
    return float(((설 or {}).get("시나리오폭") or {}).get("수준허용") or 0.002)


# ══════════════════════════════════════════════════════════════════ 한데 모아
def 셈(가정, 자리, R들=None, 설=None):
    import importlib                                          # noqa: PLC0415
    M = importlib.import_module("엔진.민감도")
    from 엔진.계산 import 계산                                # noqa: PLC0415
    설 = 설 or 설정()
    R들 = R들 or {s: 계산(가정, s) for s in ("비관", "기준", "낙관")}
    종 = _n(M.종가(가정))
    낸 = {"형식": 형식, "만든날": datetime.date.today().isoformat(), "평가기준일": (가정.get("메타") or {}).get("평가기준일"),
         "값을바꿈": False, "신호": []}
    위 = 위치(R들, 종)
    낸["위치"] = 위
    낸["시장변동"] = 시장변동(가정, R들["기준"], 자리, 설, 종)
    낸["지주"] = 지주(가정, R들["기준"], 설)
    import 피어경로                                         # noqa: PLC0415 — 1.1.4: 쓴 βU 재료 · 창 끝 · 고른 까닭을 산출에 찍는다(레터 · 모델밖가치 · 이례표시가 같은 판)
    고 = 피어경로.βU재료고르기(자리, 가정)
    낸["유사기업재료"] = {k: 고[k] for k in ("상대", "창끝", "까닭", "후보수")} if 고 else None
    낸["배수"] = 배수(가정, R들["기준"], 종, 자리, 설)
    낸["베타서열"] = 베타서열(가정, R들["기준"], 고)
    낸["시나리오폭"] = 시나리오폭(가정, R들, 위, 설)
    try:
        낸["영구짝"] = M.g짝판(가정, "기준", R들["기준"], 설.get("영구짝"))
    except Exception as e:                                   # noqa: BLE001
        낸["영구짝"] = {"까닭": "셈 실패 — %s" % e}
    낸["영구짝"]["ERP출처"] = ERP출처(가정, 설)
    낸["영구짝"]["기본값"] = 영구기본값(가정, 낸["영구짝"], 설)
    if 위.get("범위") in ("아래", "위"):
        낸["신호"].append({"출처": "갭해석", "종류": "범위 밖", "대상": "기준", "값": 위.get("로그위치"), "등급": "참고",
                         "글": "평가기준일 종가가 비관 ~ 낙관 시나리오 범위 %s에 있다(로그 위치 %s)" % (
                             {"아래": "아래", "위": "위"}[위["범위"]], ("%.2f" % 위["로그위치"]) if 위.get("로그위치") is not None else "—")})
    for g in 낸["시장변동"].get("경보") or []:
        낸["신호"].append({"출처": "갭해석", "종류": "시장 변동", "대상": "기준", "값": 낸["시장변동"].get("지수로그"), "등급": "경보", "글": g})
    if 낸["배수"].get("압축") in ("아래", "위"):
        낸["신호"].append({"출처": "갭해석", "종류": "배수 압축", "대상": "기준", "값": 낸["배수"]["모델"]["EV/EBIT실적"], "등급": "참고",
                         "글": "모델 값의 실적 EV/EBIT 가 동종 사분위 %s에 있다" % 낸["배수"]["압축"]})
    for g in 낸["시나리오폭"].get("경보") or []:
        낸["신호"].append({"출처": "갭해석", "종류": "시나리오 폭", "대상": "비관 · 낙관", "값": None, "등급": "경보", "글": g})
    if 낸["지주"].get("발동"):
        낸["신호"].append({"출처": "갭해석", "종류": "지주 관문", "대상": "기준", "값": 낸["지주"].get("지분몫"), "등급": "참고",
                         "글": "지주 할인 보조 시나리오가 선다(%s)" % " · ".join(낸["지주"].get("발동까닭") or [])})
    서 = 낸.get("베타서열") or {}
    if 서.get("경보"):
        낸["신호"].append({"출처": "갭해석", "종류": "베타 서열", "대상": "기준", "값": 서.get("Ke"), "문턱": 서.get("Kd"), "등급": "경보",
                         "글": "βU 가중 결과 %.3f 의 자기자본비용 %.2f%% 가 세전 타인자본비용 %.2f%% + %.1f%%p 보다 낮다 — 문턱까지 올린 βU 는 %.3f 다" % (
                             서["βU"], 서["Ke"] * 100, 서["Kd"] * 100, 서["문턱"] * 100, 서["하한βU"])})
    짝 = 낸["영구짝"]
    if 짝.get("상한넘음"):
        낸["신호"].append({"출처": "갭해석", "종류": "영구성장률 상한", "대상": "기준", "값": 짝.get("g"), "등급": "참고",     # 경보는 자체검사 ⑲-⑧ 이 낸다
                         "글": "영구성장률 %.2f%% 가 영구기간 무위험이자율 %.2f%% 보다 높다" % (100 * 짝["g"], 100 * 짝["Rf"])})
    return 낸


def 베타서열(가정, R, 고=None):
    """1.1.4 — βU 재료의 정밀도 가중 결과(사후)와 이 평가가 채택한 βU 의 서열(Ke ≥ 세전 Kd + 문턱 — `βU본값.서열하한`).
    → {"βU"(사후), "Ke", "Kd", "차", "문턱", "경보", "하한βU", "올린값", "채택": {…}} 또는 None(재료 · 축소 없음)."""
    import βU본값 as _본                                     # noqa: PLC0415
    W = (R.get("WACC") or {}).get("예측기간") or {}
    s = _본._축소설정()
    문 = float(s.get("서열문턱", 0.01))
    축 = None
    if 고:
        try:
            d = json.load(io.open(고["경로"], encoding="utf-8"))
            b = d.get("본값") or {}
            축 = b.get("축소") if isinstance(b.get("축소"), dict) else ((b.get("세겹") or {}).get("축소규칙"))
        except (OSError, ValueError):
            축 = None
    if not isinstance(축, dict) or not 축.get("적용") or _n(축.get("사후")) is None:
        return None
    서 = _본.서열하한(_n(축["사후"]), W, 문)
    if not 서:
        return None
    채 = _n(W.get("베타u"))
    if 채 is not None:
        서["채택"] = _본.서열하한(채, W, 문)
    return 서


def ERP출처(가정, 설=None):
    """성숙시장 ERP(3번 103)의 근거 글이 내재 ERP 를 가리키나 → {"내재": bool, "글": 근거 앞부분}. 근거 칸이 없으면 내재 = None."""
    s = ((설 or 설정()).get("영구짝") or {})
    근 = (가정.get("WACC근거") or {}).get("103")
    글 = json.dumps(근, ensure_ascii=False) if 근 is not None else ""
    if not 글:
        return {"내재": None, "글": None}
    말 = list(s.get("내재ERP말") or ["Implied", "implied", "내재"])
    return {"내재": any(w in 글 for w in 말), "글": 글[:240], "끝성장": s.get("내재ERP끝성장") or "무위험이자율", "확인": s.get("확인")}


def 영구기본값(가정, 짝, 설=None):
    """g 의 기본 상한 · 기본값(1.1.3 B3) — 상한 = 영구기간 무위험이자율. 기본값 = 그 나라 설정(국가기본)이 있으면 그 값, 없으면 내재 ERP 짝(Rf − 근처폭)."""
    s = ((설 or 설정()).get("영구짝") or {})
    국 = (s.get("국가기본") or {}).get(관할(가정))
    if isinstance(국, dict) and _n(국.get("값")) is not None:
        return {"값": min(_n(국["값"]), _n(짝.get("Rf")) or 1.0), "상한": 짝.get("Rf"), "출처": "국가기본(%s)" % 관할(가정), "근거": 국.get("근거")}
    return {"값": 짝.get("g짝"), "상한": 짝.get("Rf"), "출처": "내재 ERP 짝(영구기간 무위험이자율 − 근처폭)", "근거": s.get("확인")}


def _가정해시(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def 쓰기(낸, 가정경로, 낼=None):
    p = 낼 or os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw", 산출이름)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(낸, f, ensure_ascii=False, indent=1)
    return p


def 화면(낸):
    위 = 낸["위치"]
    줄 = ["갭 해석 — 종가 %s · 비관 %.6g · 기준 %.6g · 낙관 %.6g · 범위 %s%s" % (
        위.get("종가"), 위.get("비관") or 0, 위.get("기준") or 0, 위.get("낙관") or 0, 위.get("범위"),
        (" (로그 위치 %.2f)" % 위["로그위치"]) if 위.get("로그위치") is not None else "")]
    m = 낸["시장변동"]
    if m.get("날짜둘"):
        줄.append("  시장 변동 %s → %s — F 갭 %s · T 갭 %s · 주가 로그 %s · %s 로그 %s" % (
            m["F"], m["T"], _p(m.get("F갭")), _p(m.get("T갭")), _p(m.get("주가로그")), m.get("지수이름") or "지수", _p(m.get("지수로그"))))
    j = 낸["지주"]
    줄.append("  지주 — 지분성 몫 %s · 비지배 몫 %s · 발동 %s%s" % (_p(j.get("지분몫")), _p(j.get("비지배몫")), j.get("발동"),
                                                   (" · 할인판 " + " · ".join("%d%% %.6g" % (100 * x["할인"], x["주당"]) for x in j.get("할인판") or [])) if j.get("할인판") else ""))
    b = 낸["배수"]
    줄.append("  배수 — 모델 EV/EBIT 내년 %s · 실적 %s · 종가 내년 %s · 동종 실적 EV/EBIT 중앙 %s(%d곳) · 압축 %s" % (
        _x(b["모델"].get("EV/EBIT내년")), _x(b["모델"].get("EV/EBIT실적")), _x((b.get("종가") or {}).get("EV/EBIT내년")),
        _x(b["분포"]["EV/EBIT"].get("중앙")), b["분포"]["EV/EBIT"]["수"], b.get("압축")))
    for g in 낸["시나리오폭"].get("경보") or []:
        줄.append("  ! " + g)
    짝 = 낸.get("영구짝") or {}
    if 짝.get("주당") is not None:
        줄.append("  g 짝 — g %.2f%% · Rf %.2f%% · g 짝 %.2f%% → 주당 %.6g(%+.1f%%) · 필요 %s" % (
            100 * 짝["g"], 100 * 짝["Rf"], 100 * 짝["g짝"], 짝["주당"], 100 * (짝.get("변화") or 0), 짝.get("필요")))
    return "\n".join(줄)


def _p(x):
    return ("%+.1f%%" % (100 * x)) if _n(x) is not None else "—"


def _x(x):
    return ("%.1f배" % x) if _n(x) is not None else "—"


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                        # noqa: BLE001
        pass
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "지수받기":
        ap = argparse.ArgumentParser(description="대표 지수 일봉 → 레터_지수.csv")
        ap.add_argument("가정")
        ap.add_argument("--자리")
        a = ap.parse_args(argv[1:])
        try:
            가정 = json.load(io.open(a.가정, encoding="utf-8"))
            p, n = 지수받기(가정, a.자리 or os.path.dirname(os.path.abspath(a.가정)))
        except (OSError, ValueError) as e:
            print("입력오류 — %s" % e)
            return 입력오류
        print("레터_지수.csv — %d일 → %s" % (n, p))
        return 통과
    ap = argparse.ArgumentParser(description="갭 해석 — 범위 밖 신호 · 시장 변동 · 지주 · 배수 · 시나리오 폭 · g 짝(값을 바꾸지 않는다)")
    ap.add_argument("가정")
    ap.add_argument("--낼")
    ap.add_argument("--자리", help="회차 폴더(기본: 가정 곁)")
    a = ap.parse_args(argv)
    try:
        가정 = json.load(io.open(a.가정, encoding="utf-8"))
        낸 = 셈(가정, a.자리 or os.path.dirname(os.path.abspath(a.가정)))
    except (OSError, ValueError, KeyError) as e:
        print("입력오류 — %s" % e)
        return 입력오류
    낸["가정해시"] = _가정해시(a.가정)
    p = 쓰기(낸, a.가정, a.낼)
    print(화면(낸))
    print("→ %s" % p)
    return 통과


if __name__ == "__main__":
    sys.exit(main())

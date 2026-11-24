# -*- coding: utf-8 -*-
"""레터궤적 — 시장이 전제한 가정의 1년 궤적(R1c · N1 · L22 · M1).

회차 폴더의 `레터_주가.csv`(첫 줄들은 「#」 주석 — 출처 · 조회일, 머리 date,close …, 날짜는 20260630 또는 2026-06-30)의 날마다
그날 종가를 평가기준일의 눈으로 되굴리고(R1a `민감도.되굴림` — 예측기간 Ke 로 키우고 그사이 배당을 뺀다) 역산 축(정상 수준을 푼 표 Ⅳ 의
줄 — `레터.바닥줄`)으로 풀어 「그날 주가가 전제한 바닥」 을 낸다. 다른 가정은 평가기준일의 것 그대로다(그날의 정보로 다시 세운 평가가 아니다).

장부 키(레터 · 게이트가 같은 함수로 셈한다 — 입력은 장부의 「주가입력」 과 회차 파일을 맞댄다)
  주:종가:<날짜> · 주:되굴린:<날짜> · 주:바닥:<날짜>(역산 축의 값 — 풀이가 없으면 None) · 주:가감:<날짜>(바닥 − 기준 시나리오의 값)
  주:백:<날짜>:<구분>(그 바닥을 구분의 눈금 = 100 으로 — 3분 레터의 그림 1 · 2 와 같은 눈, `레터1부.눈금키`)
  주:환:날 · 주:환:가격:<k> · 주:환:바닥:<k> · 주:환:백:<k>:<구분>(통독 v4 상-3 — 주가 → 그 주가가 전제한 정상 수준 환산표: 창의 끝 날 기준으로
  되굴린 가격 칸들, `환산가격들`)
  주:창:시작 · 주:창:끝(1년 창의 첫 · 끝 날 — 날짜 글) · 주:퍼즐:<고점|저점>:<날짜|종가>(창에서 가장 큰 하락 — 고점 뒤 60 거래일 안의 저점)
  주:백 · 주:바닥 · 주:되굴린 · 주:가감 은 점찍기의 날이 아니어도 주가 파일에 있는 날이면 그 자리에서 푼다(`_한날` — 2026-10-27 모션 C 의
  정지점이 주마다의 마지막 거래일이 아닐 수 있다). 게이트가 같은 함수로 다시 푼다.

모션 C 의 정지점(2026-10-27 — `앞꺾임`): 평가기준일까지 주가 경로의 확정된 꺾임(직전 극값에서 꺾임문턱 넘게 되돌린 고점 · 저점 —
`카드_계산.꺾임찾기` 와 같은 규칙 · 같은 문턱, 시험이 맞댄다)의 가장 늦은 몇 개. 평가기준일 · 그 뒤 저점과 합쳐 정지점수를 넘지 않는다.
"""
from __future__ import annotations

import datetime
import io
import os
import re

파일 = "레터_주가.csv"
창일수 = 365
퍼즐창 = 60                       # 고점 뒤 이 거래일 수 안의 저점
퍼즐문턱 = 0.30                   # 이만큼 넘게 내렸을 때만 「퍼즐」 로 연다
꺾임문턱 = 0.20                   # 모션 C 정지점 — 직전 극값에서 이만큼 넘게 되돌린 날만 꺾임(카드_계산.기본문턱 과 같은 값)
정지점수 = 4                      # 모션 C 정지점의 상한(평가기준일 · 뒤 날 포함 — 움직임 셋까지 · 연구 「단계는 둘~넷」)


def _n(x):
    try:
        if x is None or isinstance(x, bool):
            return None
        return float(x)
    except (TypeError, ValueError):
        return None


def _날글(t):
    t = ("%s" % t).strip()
    if re.match(r"^\d{8}$", t):
        return "%s-%s-%s" % (t[:4], t[4:6], t[6:])
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", t)
    return "%04d-%02d-%02d" % (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def 읽기(p):
    """CSV → {"출처": 주석 글, "줄": [[날짜, 종가] …](날짜 차례)} — 읽지 못하면 None."""
    try:
        글 = io.open(p, encoding="utf-8-sig").read()
    except Exception:                                        # noqa: BLE001
        return None
    출처, 줄, 머리 = [], [], None
    for L in 글.splitlines():
        t = L.strip()
        if not t:
            continue
        if t.startswith("#"):
            출처.append(t.lstrip("# ").strip())
            continue
        칸 = [c.strip() for c in t.split(",")]
        if 머리 is None:
            머리 = [c.lower() for c in 칸]
            continue
        try:
            날 = _날글(칸[머리.index("date")])
            v = _n(칸[머리.index("close")])
        except (ValueError, IndexError):
            continue
        if 날 and v and v > 0:
            줄.append([날, v])
    if not 줄:
        return None
    return {"출처": " · ".join(출처), "줄": sorted(줄)}


def 찾기(경로, 지정=None):
    p = 지정 or (os.path.join(os.path.dirname(os.path.abspath(경로)), 파일) if 경로 else None)
    return 읽기(p) if p and os.path.isfile(p) else None


def _날(t):
    y, m, d = t.split("-")
    return datetime.date(int(y), int(m), int(d))


def 창(주가):
    """1년 창의 줄 — 끝 날부터 365일 안."""
    줄 = (주가 or {}).get("줄") or []
    if not 줄:
        return []
    끝 = _날(줄[-1][0])
    return [x for x in 줄 if (끝 - _날(x[0])).days <= 창일수]


def 퍼즐(주가):
    """창에서 고점 → 그 뒤 퍼즐창 거래일 안의 저점 가운데 가장 큰 하락 → {"고점": [날, 종가], "저점": [날, 종가], "하락"} 또는 None(문턱 아래)."""
    줄 = 창(주가)
    낸 = None
    for i, (날, v) in enumerate(줄):
        뒤 = 줄[i + 1:i + 1 + 퍼즐창]
        if not 뒤:
            continue
        lo = min(뒤, key=lambda x: x[1])
        r = lo[1] / v - 1
        if 낸 is None or r < 낸["하락"]:
            낸 = {"고점": [날, v], "저점": list(lo), "하락": r}
    return 낸 if 낸 and -낸["하락"] >= 퍼즐문턱 else None


def 꺾임들(줄, 문턱=꺾임문턱):
    """종가 [(날, 종가)] 의 꺾임 — 직전 극값에서 문턱 넘게 되돌린 고점 · 저점(번갈아) → [{"i", "날", "종류": 고 · 저, "확정"}].
    `카드_계산.꺾임찾기` 와 같은 규칙이다(그 함수는 분수로 셈한다 — 여기는 레터가 쓰는 부동소수 종가). 확정 = 그 뒤로 문턱만큼 되돌렸다.
    끝의 극값(되돌리기 전에 줄이 끝남)은 확정 거짓으로 덧붙인다."""
    n = len(줄)
    점, 확 = [], False
    hi = lo = ext = 0
    v_ = [float(x[1]) for x in 줄]
    for i in range(1, n):
        v = v_[i]
        if not 점:
            if v > v_[hi]:
                hi = i
            if v < v_[lo]:
                lo = i
            if lo < i and v >= v_[lo] * (1 + 문턱):
                점, ext, 확 = [[lo, "저"]], i, True
            elif hi < i and v <= v_[hi] * (1 - 문턱):
                점, ext, 확 = [[hi, "고"]], i, True
            continue
        끝점 = 점[-1]
        if 끝점[1] == "저":
            if 확 and v <= v_[ext] * (1 - 문턱):
                점.append([ext, "고"])
                ext, 확 = i, True
                continue
            if v < v_[끝점[0]]:
                끝점[0], ext, 확 = i, i, False
                continue
            if v > v_[ext]:
                ext = i
            if not 확 and v_[ext] >= v_[끝점[0]] * (1 + 문턱):
                확 = True
        else:
            if 확 and v >= v_[ext] * (1 + 문턱):
                점.append([ext, "저"])
                ext, 확 = i, True
                continue
            if v > v_[끝점[0]]:
                끝점[0], ext, 확 = i, i, False
                continue
            if v < v_[ext]:
                ext = i
            if not 확 and v_[ext] <= v_[끝점[0]] * (1 - 문턱):
                확 = True
    밖 = [{"i": i, "날": 줄[i][0], "종류": k, "확정": True} for i, k in 점]
    if 밖:
        밖[-1]["확정"] = 확
        if 확 and ext != 밖[-1]["i"]:
            밖.append({"i": ext, "날": 줄[ext][0], "종류": "고" if 밖[-1]["종류"] == "저" else "저", "확정": False})
    return 밖


def 앞꺾임(주가, 기준일, 몇):
    """모션 C 의 앞 정지점 — 1년 창에서 평가기준일까지의 종가로 찾은 **확정된** 꺾임 가운데 가장 늦은 몇 개의 날(날짜 차례).
    평가기준일 앞 마지막 거래일은 뺀다(그날은 평가기준일 줄이 맡는다). 몇 이 0 이하이거나 주가가 없으면 []."""
    if 몇 <= 0:
        return []
    줄 = [x for x in 창(주가) if x[0] <= ("%s" % 기준일)[:10]]
    if len(줄) < 3:
        return []
    끝 = 줄[-1][0]
    날 = [x["날"] for x in 꺾임들(줄) if x["확정"] and x["날"] != 끝]
    return 날[-몇:]


def 점찍기(주가, 기준일):
    """그림 · 표에 싣는 날 — 주마다 마지막 거래일 + 핀(평가기준일 또는 그 앞 마지막 거래일 · 퍼즐 고점 · 저점 · 창의 끝)."""
    줄 = 창(주가)
    if not 줄:
        return [], []
    주 = {}
    for 날, _v in 줄:
        y, w, _d = _날(날).isocalendar()
        주[(y, w)] = 날
    핀 = []
    앞 = [x[0] for x in 줄 if x[0] <= 기준일]
    if 앞:
        핀.append(앞[-1])
    p = 퍼즐(주가)
    if p:
        핀 += [p["고점"][0], p["저점"][0]]
    핀.append(줄[-1][0])
    날들 = sorted(set(주.values()) | set(핀))
    return 날들, list(dict.fromkeys(핀))


def 셈(원):
    """→ {날짜: {"종가", "되굴린", "바닥", "가감"}} (원 「_궤적」 에 담는다). 역산 축이 없거나 주가 입력이 없으면 {}."""
    if "_궤적" in 원:
        return 원["_궤적"]
    import 레터 as _L                                       # noqa: PLC0415
    주가 = 원.get("주가")
    i = _L.기본역산줄(원) if 원.get("민") else None      # S9-03 — 정상 수준 줄, 없으면 유형 기본 축
    낸 = {}
    if 주가 and i is not None:
        가정 = 원["가정"]
        기준일 = "%s" % ((가정.get("메타") or {}).get("평가기준일") or "")
        h = _L._역산손잡이들(가정)[i]
        R0 = 원["R"]["기준"]
        기 = _n(원["민"]["표4"]["줄"][i].get("적용값"))
        날들, _핀 = 점찍기(주가, 기준일)
        값 = dict((d, v) for d, v in 주가["줄"])
        for d in 날들:
            v = 값[d]
            목표, _g = _L._민감도.되굴림(가정, d, v, "기준", R0)
            r = _L._민감도.역산(가정, 목표, "기준", h)
            x = _n(r.get("값")) if isinstance(r, dict) else None
            가 = _n(r.get("가감")) if isinstance(r, dict) else None
            if x is not None and h.get("방식") != "값" and 가 is None and 기 is not None:
                가 = x - 기
            낸[d] = {"종가": v, "되굴린": 목표, "바닥": x, "가감": 가 if 가 is not None else (None if x is None or 기 is None else x - 기)}
    원["_궤적"] = 낸
    return 낸


def _한날(원, d):
    """날 d 의 {"종가", "되굴린", "바닥", "가감"} — 점찍기의 날이면 셈의 것, 아니면 주가 파일의 그날 종가로 같은 셈을 하고 셈 결과에 더한다
    (2026-10-27 — 모션 C 정지점처럼 주마다의 마지막 거래일이 아닌 날). 주가 파일에 없는 날 · 역산 축이 없으면 None."""
    r = 셈(원)
    if d in r:
        return r[d]
    import 레터 as _L                                       # noqa: PLC0415
    주가 = 원.get("주가")
    i = _L.기본역산줄(원) if 원.get("민") else None
    값들 = dict((x, v) for x, v in (주가 or {}).get("줄") or [])
    if i is None or d not in 값들:
        return None
    가정 = 원["가정"]
    h = _L._역산손잡이들(가정)[i]
    R0 = 원["R"]["기준"]
    기 = _n(원["민"]["표4"]["줄"][i].get("적용값"))
    v = 값들[d]
    목표, _g = _L._민감도.되굴림(가정, d, v, "기준", R0)
    q = _L._민감도.역산(가정, 목표, "기준", h)
    x = _n(q.get("값")) if isinstance(q, dict) else None
    가 = _n(q.get("가감")) if isinstance(q, dict) else None
    if x is not None and h.get("방식") != "값" and 가 is None and 기 is not None:
        가 = x - 기
    r[d] = {"종가": v, "되굴린": 목표, "바닥": x, "가감": 가 if 가 is not None else (None if x is None or 기 is None else x - 기)}
    return r[d]


def 백(원, x, s):
    """역산 축의 값 x → 구분 s 의 눈금 = 100(레터3분._내 · _백 과 같은 셈 — 방식 값 · 배율 · 가산)."""
    import 레터 as _L                                       # noqa: PLC0415
    if x is None:
        return None
    i = _L.바닥줄(원)
    if i is None:                                          # S9-03 — 정상 수준 줄이 없는 회사(유형 기본 축)는 구분 눈금이 없다
        return None
    가정 = 원["가정"]
    기 = _n(원["민"]["표4"]["줄"][i].get("적용값"))
    축 = (가정.get("역산") or {}).get("축")
    방식 = "가산"
    if isinstance(축, dict) and ["%s" % y for y in 축.get("대상") or []] == ["%s" % y for y in 원["민"]["표4"]["줄"][i]["대상"]]:
        방식 = 축.get("방식", "가산")
    S = _n(_L._시점값(가정, "6%d6" % s, "기준"))
    import 레터1부 as _P                                     # noqa: PLC0415
    T = _n(_L.키풀기(_P.눈금키(가정, s), 원))
    if not T or (방식 != "값" and (S is None or 기 is None)):
        return None
    지수 = x if 방식 == "값" else (S * x / 기 if 방식 == "배율" else S + (x - 기))
    return 지수 / T * 100.0


환산칸수 = 10                      # 환산표의 가격 칸 수 상한(통독 v4 상-3)


def _고른걸음(폭, 칸):
    """폭을 칸 수 안팎으로 나누는 고른 걸음 — 1 · 2 · 2.5 · 5 × 10^k."""
    import math
    if 폭 <= 0:
        return 1.0
    날 = 폭 / max(칸 - 1, 1)
    k = 10 ** math.floor(math.log10(날))
    for m in (1, 2, 2.5, 5, 10):
        if m * k >= 날:
            return m * k
    return 10 * k


def 환산가격들(원):
    """통독 v4 상-3 — 주가 → 그 주가가 전제한 정상 수준 환산표의 가격 칸. 아래 끝 = 기준 주당가치와 창의 끝 날 종가 가운데 작은 값의 0.75배,
    위 끝 = 평가기준일 종가와 창의 끝 날 종가 가운데 큰 값의 1.1배. 고른 걸음(1 · 2 · 2.5 · 5 × 10^k)으로 환산칸수 안. 주가가 없으면 []."""
    import math
    import 레터 as _L                                       # noqa: PLC0415
    줄 = 창(원.get("주가"))
    if not 줄:
        return []
    가정 = 원["가정"]
    기준일 = "%s" % ((가정.get("메타") or {}).get("평가기준일") or "")
    앞 = [v for d, v in 줄 if d <= 기준일]
    기값 = _n(_L.키풀기("R:기준:2.DCF:68", 원))
    끝값 = 줄[-1][1]
    if not 기값:
        return []
    아래 = 0.75 * min(기값, 끝값)
    위 = 1.1 * max([끝값] + 앞[-1:])
    걸음 = _고른걸음(위 - 아래, 환산칸수)
    while math.ceil(위 / 걸음) - math.floor(아래 / 걸음) + 1 > 환산칸수:
        걸음 = _고른걸음(걸음 * (환산칸수 - 1) * 1.01, 환산칸수)
    a, b = math.floor(아래 / 걸음), math.ceil(위 / 걸음)
    return [걸음 * k for k in range(int(a), int(b) + 1) if 걸음 * k > 0]


def 환산셈(원):
    """→ {"날": 창의 끝 날, "줄": [{"가격", "되굴린", "바닥"}]} — 가격을 창의 끝 날의 종가로 보고 평가기준일로 되굴려(궤적과 같은 셈) 역산 축으로 푼다."""
    if "_환산" in 원:
        return 원["_환산"]
    import 레터 as _L                                       # noqa: PLC0415
    낸 = {"날": None, "줄": []}
    i = _L.기본역산줄(원) if 원.get("민") else None      # S9-03 — 정상 수준 줄, 없으면 유형 기본 축
    줄 = 창(원.get("주가"))
    if 줄 and i is not None:
        가정 = 원["가정"]
        h = _L._역산손잡이들(가정)[i]
        R0 = 원["R"]["기준"]
        d = 줄[-1][0]
        낸["날"] = d
        for v in 환산가격들(원):
            목표, _g = _L._민감도.되굴림(가정, d, v, "기준", R0)
            r = _L._민감도.역산(가정, 목표, "기준", h)
            낸["줄"].append({"가격": v, "되굴린": 목표, "바닥": _n(r.get("값")) if isinstance(r, dict) else None})
    원["_환산"] = 낸
    return 낸


def 값(부, 원):
    """장부 키 「주:…」 의 값."""
    종 = 부[0]
    주가 = 원.get("주가") or {}
    if 종 == "환":                                           # 주:환:날 · 주:환:수 · 주:환:가격:<k> · 주:환:바닥:<k> · 주:환:백:<k>:<구분>
        r = 환산셈(원)
        if 부[1] == "날":
            return r["날"]
        if 부[1] == "수":
            return float(len(r["줄"]))
        k = int(부[2])
        if k >= len(r["줄"]):
            return None
        if 부[1] == "백":
            return 백(원, r["줄"][k].get("바닥"), int(부[3]))
        return r["줄"][k].get(부[1])
    if 종 == "종가":
        return dict((d, v) for d, v in 주가.get("줄") or []).get(부[1])
    if 종 in ("되굴린", "바닥", "가감"):
        return (_한날(원, 부[1]) or {}).get(종)
    if 종 == "백":
        return 백(원, (_한날(원, 부[1]) or {}).get("바닥"), int(부[2]))
    if 종 == "창":
        줄 = 창(주가)
        if not 줄:
            return None
        d = 줄[0][0] if 부[1] == "시작" else 줄[-1][0]
        if len(부) > 2 and 부[2] == "날말":
            import 레터1부 as _P                                 # noqa: PLC0415
            return _P.날짜말(d)
        return d
    if 종 == "날말":                                         # 주:날말:<날짜> — 「2026년 6월 22일」
        import 레터1부 as _P                                     # noqa: PLC0415
        return _P.날짜말(부[1])
    if 종 == "퍼즐":
        p = 퍼즐(주가)
        if not p:
            return None
        if 부[1] == "하락":
            return p["하락"]
        if 부[1] == "일수":
            return float((_날(p["저점"][0]) - _날(p["고점"][0])).days)
        if 부[2] == "날말":
            import 레터1부 as _P                                 # noqa: PLC0415
            return _P.날짜말(p[부[1]][0])
        return p[부[1]][0 if 부[2] == "날짜" else 1]
    raise KeyError("모르는 주가 키: %s" % ":".join(부))


# ══════════════════════════════════════════════════════════════════ N2 — 증권사 목표주가가 요구하는 가정
# 회차 폴더의 `레터_목표주가.json` {"출처", "목록": [{"증권사", "날짜", "목표주가", "기간"(개월 — 기본 12), "근거"}]}.
# 목표주가는 「기간 뒤의 가격」 이라 그날의 값으로 Ke 만큼 깎고(÷ (1 + Ke)^(기간 ÷ 12)) 평가기준일로 되굴려 역산 축으로 푼다.
# 장부 키 — 목:목표:<k> · 목:되굴린:<k> · 목:바닥:<k> · 목:가감:<k>. 파일이 없으면 레터는 「자료 없음」 한 줄만 싣는다.

목표파일 = "레터_목표주가.json"
독자파일 = os.path.join("_raw", "역산_독자.json")          # S9-06 — 7단계 끝 「역산해 볼 가격」(역산.py 가 쌓는다)


def 독자찾기(경로, 지정=None):
    """회차 폴더의 `_raw/역산_독자.json` → {"목록": [{"주가", "날짜", "근거"}]}(입력만 — 값은 레터 · 게이트가 같은 엔진으로 다시 셈한다). 없으면 None."""
    import json as _json
    p = 지정 or (os.path.join(os.path.dirname(os.path.abspath(경로)), 독자파일) if 경로 else None)
    if not p or not os.path.isfile(p):
        return None
    try:
        d = _json.load(io.open(p, encoding="utf-8"))
    except Exception:                                        # noqa: BLE001
        return None
    목 = [{"주가": _n(x.get("주가")), "날짜": ("%s" % (x.get("날짜") or ""))[:10], "근거": ("%s" % (x.get("근거") or "")).strip()}
         for x in (d.get("목록") or []) if isinstance(x, dict) and _n(x.get("주가")) and _n(x.get("주가")) > 0]
    return {"목록": 목} if 목 else None


def 독자셈(원):
    """→ [{"주가", "날짜", "근거", "되굴린", "축": [{"이름", "대상", "값", "적용", "까닭"}]}] — 표 Ⅳ 와 같은 축(엔진 `역산축목록`)으로 같은 엔진 역산."""
    if "_독자" in 원:
        return 원["_독자"]
    import 레터 as _L                                       # noqa: PLC0415
    입 = 원.get("독자")
    낸 = []
    if 입:
        가정 = 원["가정"]
        R0 = 원["R"]["기준"]
        기준일 = ("%s" % ((가정.get("메타") or {}).get("평가기준일") or ""))[:10]
        축들 = _L._역산손잡이들(가정)
        for x in 입["목록"]:
            v, d = _n(x["주가"]), x.get("날짜") or 기준일
            목표 = v if (not d or d == 기준일) else _L._민감도.되굴림(가정, d, v, "기준", R0)[0]
            줄 = []
            for h in 축들:
                r = _L._민감도.역산(가정, 목표, "기준", h)
                적 = r.get("적용값") if isinstance(r, dict) and r.get("적용값") is not None else _L._민감도.적용값(가정, h, "기준", R0)
                줄.append({"이름": h["이름"], "대상": list(h["대상"]), "값": _n((r or {}).get("값")), "적용": _n(적), "까닭": (r or {}).get("까닭")})
            낸.append({"주가": v, "날짜": d, "근거": x.get("근거") or "", "되굴린": 목표, "축": 줄})
    원["_독자"] = 낸
    return 낸


def 독자값(부, 원):
    """장부 키 독:<k>:주가 · 되굴린 · 축:<i>:값 · 축:<i>:적용."""
    r = 독자셈(원)
    k = int(부[0])
    if k >= len(r):
        return None
    if 부[1] == "축":
        return r[k]["축"][int(부[2])].get(부[3])
    if 부[1] == "날말":                                     # 「2026년 8월 14일」(글 — 장부의 엔진 글)
        import 레터1부 as _P                                 # noqa: PLC0415
        return _P.날짜말(r[k]["날짜"])
    return r[k].get(부[1])


def 목표찾기(경로, 지정=None):
    import json as _json
    p = 지정 or (os.path.join(os.path.dirname(os.path.abspath(경로)), 목표파일) if 경로 else None)
    if not p or not os.path.isfile(p):
        return None
    try:
        d = _json.load(io.open(p, encoding="utf-8"))
    except Exception:                                        # noqa: BLE001
        return None
    목 = [x for x in (d.get("목록") or []) if isinstance(x, dict) and _n(x.get("목표주가")) and _날글(x.get("날짜") or "")]
    return {"출처": d.get("출처") or "", "목록": 목} if 목 else None


def 목표셈(원):
    if "_목표" in 원:
        return 원["_목표"]
    import 레터 as _L                                       # noqa: PLC0415
    입 = 원.get("목표")
    i = _L.기본역산줄(원) if 원.get("민") else None      # S9-03 — 정상 수준 줄, 없으면 유형 기본 축
    낸 = []
    if 입 and i is not None:
        가정 = 원["가정"]
        h = _L._역산손잡이들(가정)[i]
        R0 = 원["R"]["기준"]
        ke = R0["WACC"]["예측기간"]["Ke"]
        기 = _n(원["민"]["표4"]["줄"][i].get("적용값"))
        for x in 입["목록"]:
            그날 = _n(x["목표주가"]) / (1 + ke) ** ((_n(x.get("기간")) or 12.0) / 12.0)
            목표, _g = _L._민감도.되굴림(가정, _날글(x["날짜"]), 그날, "기준", R0)
            r = _L._민감도.역산(가정, 목표, "기준", h)
            v = _n(r.get("값")) if isinstance(r, dict) else None
            낸.append({"목표": _n(x["목표주가"]), "되굴린": 목표, "바닥": v, "가감": (v - 기) if (v is not None and 기 is not None) else None})
    원["_목표"] = 낸
    return 낸


def 목표값(부, 원):
    r = 목표셈(원)
    k = int(부[1])
    if 부[0] == "백":
        return 백(원, r[k].get("바닥"), int(부[2])) if k < len(r) else None
    return r[k].get(부[0]) if k < len(r) else None

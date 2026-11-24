# -*- coding: utf-8 -*-
"""레터고객 — 매출 절의 「고객 수 × 고객당 매출」 검증 표(1.1.6 · 값을 바꾸지 않는다). 재료는 가정 곁 `_raw/고객경로.json`(「고객경로/1」 — `고객경로.py`).

매출 구분을 고객 수 × 고객당 매출로 세우면 매출 구분이 원가의 공시 단위(부문)와 갈린다. 실적 열마다 구분 매출과 그 구분이 가리키는 부문 매출 합을
나란히 놓고 차이(0 이어야 함)를 싣는다. 숫자는 원천 장부 키(H:) · 재료 키(파일:고객경로:…) · 식이다. 선언이 없거나 옮기지 않았으면 서지 않는다.
회사 · 업종 이름은 이 모듈에 없다.
"""
from __future__ import annotations

import importlib


def _P():
    return importlib.import_module("레터1부")


def _n(x):
    try:
        return None if x is None or isinstance(x, bool) else float(x)
    except (TypeError, ValueError):
        return None


K = "파일:고객경로:구분:%d:%s"


def 고객경로표(맥):
    P = _P()
    import 레터 as _L                                       # noqa: PLC0415
    j = ((맥.원.get("파일") or {}).get("고객경로")) or {}
    L = []
    for k, h in enumerate(j.get("구분") or []):
        s = h.get("번호")
        x = next((y for y in 맥.구.get("매출구분") or [] if y.get("번호") == s), None)
        if not (isinstance(s, int) and x and x.get("경로") == "수준" and x.get("판매량꼴") == "저량" and h.get("검증")):
            continue
        줄들 = []
        for i, r in enumerate(h["검증"]):
            c = r.get("열")
            H매, H고 = "H:%d:%s" % (85 + s, c), "H:%d:%s" % (550 + s, c)
            if _n(맥.값(H매)) is None:
                continue
            고 = _n(맥.값(H고))
            줄들.append([맥.열말(c), 맥.수(H고, "수0") if 고 else "—", 맥.식(["÷", H매, H고], "금액") if 고 else "—", 맥.수(H매, "금액"),
                       맥.수(K % (k, "검증:%d:부문매출" % i), "금액"), 맥.식(["−", H매, K % (k, "검증:%d:부문매출" % i)], "금액")])
        if not 줄들:
            continue
        이름 = _L.구분이름(맥.구, s)
        Q말 = x.get("판매량명칭") or "고객 수"
        P말 = x.get("판매단가명칭") or "고객당 매출"
        L += ["### %s × %s : 매출 구분과 부문 매출의 검증" % (Q말, P말), ""]
        L += ["%s 매출은 %s × %s로 세웠습니다. 예측 열의 매출은 기준 기간 매출에 %s의 비율과 %s 지수를 곱한 값입니다. "
              "원가는 공시 단위(부문)의 연결 한 벌 그대로라, 매출 구분과 부문이 갈립니다. 아래 표는 실적 열마다 구분 매출과 부문 매출의 합을 나란히 놓은 것이고, "
              "마지막 열은 0 이어야 합니다." % (이름, Q말, P말, Q말, P말), ""]
        L += P._표(["회계연도", Q말, P말, "구분 매출", "부문 매출 합", "차이 (0 이어야 함)"], 줄들, ["l", "r", "r", "r", "r", "r"])
        L.append("")
    return L

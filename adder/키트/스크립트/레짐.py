# -*- coding: utf-8 -*-
"""레짐 — 선택 표 「레짐 기대값」 의 재료를 낸다(1.1.6). 레짐마다 이름 붙은 가정 묶음을 엔진으로 셈하고, 확률은 기저율 패널에서 세운다.

    python 스크립트/레짐.py <가정.json> [--낼 _raw/레짐.json]

**기준 · 비관 · 낙관 시나리오의 값을 바꾸지 않는다.** 레짐 값은 엔진(엔진.계산)으로만 셈한다 — 손으로 적은 값은 받지 않는다.
선언(원고 쪽 · 엔진 밖 — `관측.레짐`)이 없으면 「해당 없음」 산출을 내고 레터는 표를 세우지 않는다. 설정 `스크립트/레짐설정.json`.

선언 꼴
  관측.레짐 = {"목록": [{"이름", "시나리오"(비관 · 기준 · 낙관 — 기본 기준), "바꿈"[{가정 · 방식 · 값} — 반대 논거와 같은 꼴],
                         "반대논거"[Narrative.반대논거 의 번호 — 그 바꿈을 그대로], "βU"(대안 사양 — 두 구간의 Unlevered Beta), "근거"}],
               "확률": {"규칙": "기저율"(기본) | "판단", "값"[레짐 차례의 확률 — 판단일 때], "근거"(판단일 때 필수)}}
확률 규칙 「기저율」(기본) — 기저율 패널(`기저율.py` 와 같은 패널 · 같은 자료 제외)의 회사-5년 창을 대상과 같은 규모 구간 · 같은 산업 집단으로
  거른 뒤(집단차례 — 창이 최소관측 미만이면 다음 집단), 창마다 그 창이 넘은 가장 높은 레짐(창의 5년 매출 CAGR ≥ 그 레짐 경로의 CAGR 이고 5년 평균
  영업이익률 ≥ 그 레짐 경로의 평균 영업이익률 — 레짐은 엔진 주당가치 차례)에 둔다. 어느 레짐도 못 넘은 창은 가장 낮은 레짐(그 경로 아래 전부)이다.
  레짐 확률 = 그 레짐에 든 창의 비율. 판단으로 바꾸면 값(합 1)과 근거가 함께 있어야 한다 — 없으면 표가 서지 않는다(자체검사 61 · R-175).
  1.1.7 — 기저율 밖: 가장 낮은 레짐의 경로조차 넘은 창이 「기저율밖문턱」 아래면 확률을 세우지 않는다(「기저율 밖 — 확률을 세울 수 없음」 ·
  관측 n 개 가운데 넘은 창 수 · 가장 가까운 창의 CAGR · 이익률만 남기고 기대값을 내지 않는다). 작은 집단: 레짐마다 확률에 윌슨 점수 구간(「구간.신뢰수준」),
  관측이 「작은집단문턱」 아래이거나 기저율 밖이면 상위 집단(「넓힘차례」 — 같은 규모 → 전체)으로 넓혀 다시 센 판(「넓힌」)을 나란히 둔다.
시장가가 함축하는 최상위 레짐 확률 — 나머지 레짐 사이의 확률 비율을 그대로 두고 기대값이 종가가 되는 최상위 레짐의 확률:
  p* = (종가 − V̄) ÷ (V최상위 − V̄),  V̄ = Σ(최상위 밖) p · V ÷ Σ(최상위 밖) p.   0 ~ 1 밖이면 「확률로는 닿지 않는다」.

산출 가정 곁 `_raw/레짐.json` — 「레짐/1」: 형식 · 만든날 · 평가기준일 · 가정해시 · 선언해시 · 값을바꿈(false) · 기준주당 · 종가 ·
  레짐[{이름, 시나리오, 묶음글, 주당, 경로{t0, CAGR5, 평균이익률5}, 이상비율, 기저율확률, 판단확률, 확률, 근거}] · 차례(주당 차례 번호) ·
  확률규칙 · 확률근거 · 기저율{국가, 집단, 관측수, 회사수, 창, 대상{규모구간, 산업}, 까닭} · 기대값 · 최상위 · 함축최상위확률 · 함축판정 · 신호[].
레터(`레터레짐.py`)는 레짐 값을 장부 키 「레:i」(엔진이 다시 셈한다) · 확률을 「파일:레짐:레짐:i:확률」 로 부른다.
종료 코드 — 0 통과(해당 없음 포함) · 2 입력오류(가정 파일 없음 · JSON 깨짐 · 묶음 셈 실패).
회사 · 업종 이름은 이 도구에 없다.
"""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import io
import json
import os
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 입력오류  # noqa: E402

형식 = "레짐/1"
산출이름 = "레짐.json"
설정파일 = os.path.join(여기, "레짐설정.json")
시나리오들 = ("비관", "기준", "낙관")


def 설정():
    try:
        with io.open(설정파일, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _n(x):
    try:
        return None if x is None or isinstance(x, bool) else float(x)
    except (TypeError, ValueError):
        return None


def 선언(가정):
    """관측.레짐 → (목록, 확률 선언) — 목록이 둘 미만이면 ([], {})."""
    v = ((가정.get("관측") or {}).get("레짐")) if isinstance(가정, dict) else None
    if not isinstance(v, dict):
        return [], {}
    목 = [x for x in (v.get("목록") or []) if isinstance(x, dict) and ("%s" % (x.get("이름") or "")).strip()]
    if len(목) < 2:
        return [], {}
    return 목, (v.get("확률") if isinstance(v.get("확률"), dict) else {})


def 선언해시(가정):
    v = ((가정.get("관측") or {}).get("레짐")) if isinstance(가정, dict) else None
    return hashlib.sha256(json.dumps(v, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest() if v is not None else None


def _바꿈들(가정, 레):
    """레짐 하나의 바꿈 → [{"손잡이", "x"}] — 반대 논거 번호(그 바꿈 그대로) + 레짐 자신의 바꿈(반대 논거와 같은 꼴 · `레터.반대바꿈`)."""
    import 레터 as _L                                       # noqa: PLC0415
    낸 = []
    목 = (((가정.get("Narrative") or {}).get("반대논거")) or [])
    for i in 레.get("반대논거") or []:
        try:
            낸 += _L.반대바꿈(목[int(i)])
        except (IndexError, ValueError, TypeError) as e:
            raise ValueError("레짐 「%s」 의 반대논거 %s — %s" % (레.get("이름"), i, e))
    if 레.get("바꿈"):
        낸 += _L.반대바꿈({"바꿈": 레["바꿈"]})
    return 낸


def 묶음가정(가정, 레):
    """레짐 하나 → (그 묶음을 놓은 가정 사본, 시나리오). βU 대안은 두 구간의 Unlevered Beta 를 그 값으로(부록 B 대안 사양과 같은 셈 — `레터.대안β값`)."""
    import importlib as _il                                # noqa: PLC0415
    _민 = _il.import_module("엔진.민감도")                   # 엔진 꾸러미의 같은 이름 함수가 모듈을 가린다
    시 = ("%s" % (레.get("시나리오") or "기준")).strip()
    if 시 not in 시나리오들:
        raise ValueError("레짐 「%s」 의 시나리오 「%s」 — 비관 · 기준 · 낙관 가운데 하나" % (레.get("이름"), 시))
    a = copy.deepcopy(가정)
    β = _n(레.get("βU"))
    if β is not None:
        if isinstance(((a.get("구조") or {}).get("할인")), dict) and a["구조"]["할인"].get("베타출처") == "유사기업표":
            a["구조"]["할인"]["베타출처"] = "직접"
        for 구간 in ("예측기간", "영구기간"):
            if isinstance((a.get("WACC") or {}).get(구간), dict):
                a["WACC"][구간]["베타u"] = β
    for b in _바꿈들(가정, 레):
        a = _민.움직이기(a, b["손잡이"], b["x"], 시)
    return a, 시


def 묶음글(가정, 레):
    """레짐의 묶음을 읽는 말(표 칸) — 「낙관 시나리오 + 반대 논거 1 · 3 + 가정 2곳 바꿈 + Unlevered Beta 1.250」. 선언에 「묶음글」 이 있으면 그 글."""
    if ("%s" % (레.get("묶음글") or "")).strip():
        return ("%s" % 레["묶음글"]).strip()
    조 = ["%s 시나리오" % (레.get("시나리오") or "기준")]
    반 = [int(i) + 1 for i in 레.get("반대논거") or [] if ("%s" % i).isdigit()]
    if 반:
        조.append("반대 논거 %s" % " · ".join("%d" % k for k in 반))
    if 레.get("바꿈"):
        조.append("가정 %d곳 바꿈" % len(레["바꿈"]))
    if _n(레.get("βU")) is not None:
        조.append("Unlevered Beta %.3f" % _n(레["βU"]))
    return " + ".join(조)


def 주당(가정, 레):
    from 엔진.계산 import 계산                               # noqa: PLC0415
    a, 시 = 묶음가정(가정, 레)
    return _n(계산(a, 시)["요약"]["주당가치"])


def 경로(가정, 레, 창년=5, 창시작="마지막실적해"):
    """레짐 묶음의 엔진 경로 창 → {t0, CAGR5, 평균이익률5} (기저율.경로 · 경로벡터와 같은 셈). 창이 안 서면 값이 None."""
    import 기저율 as 기                                       # noqa: PLC0415
    a, 시 = 묶음가정(가정, 레)
    길, 오 = 기.경로(a, (시,))
    if 시 not in 길:
        return {"t0": None, "CAGR5": None, "평균이익률5": None, "까닭": " / ".join(오)}
    g = 길[시]
    t0 = g["마지막실적해"] if 창시작 == "마지막실적해" else g["첫예측해"]
    v = 기.경로벡터(g["해"], t0) if t0 is not None else {}
    return {"t0": t0, "CAGR5": v.get("CAGR%d" % 창년) if 창년 in (3, 5) else None, "평균이익률5": v.get("평균이익률5")}


def _대상과창(가정, 가정경로, 설):
    """기저율 패널 → (창 목록(대상 회사 뺌 · 같은 구분), 대상{규모구간, KSIC3, KSIC2}, 국가, 까닭)."""
    import 기저율 as 기                                       # noqa: PLC0415
    s = 기.설정읽기()
    국, s, 까 = 기.국가맞춤(가정, s)
    if not 국:
        return None, None, None, "기저율 패널 해당 없음 — %s" % 까
    행, 입 = 기.패널읽기(None, s)
    if not 행:
        return None, None, 국, "%s 패널이 비었다(%s) — `기저율.py --받기 --국가 %s`" % (국, 입["자리"], 국)
    고, 산업, 까 = 기.대상찾기(가정, 가정경로, 행, None, s)
    if not 고:
        return None, None, 국, 까
    남, _뺀 = 기.자료제외(행, s)
    넓은 = 기.넓히기(남)
    길, _오 = 기.경로(가정, ("기준",))
    g = 길.get("기준") or {}
    마실 = g.get("마지막실적해")
    배율 = _n((가정.get("메타") or {}).get("환산배율")) or 1.0
    기준매출 = (((넓은.get(고) or {}).get("해") or {}).get(마실) or {}).get("매출액")
    if 기준매출 is None and 마실 in (g.get("해") or {}):
        기준매출 = g["해"][마실]["매출"] * 배율
    대 = {"고유번호": 고, "규모구간": 기.규모구간(기준매출, s), "KSIC3": 산업[:3] if 산업 and len(산업) >= 3 else None,
         "KSIC2": 산업[:2] if 산업 and len(산업) >= 2 else None, "산업분류": s.get("_산업분류") or "KSIC"}
    창 = [w for w in 기.조합창(넓은, s) if w["고유번호"] != 고]
    if s["자료_제외"].get("창_양끝_같은구분", True):
        창 = [w for w in 창 if w["같은구분"]]
    return 창, 대, 국, ""


def _집단(창, 대, 이름):
    분 = 대.get("산업분류") or "KSIC"
    규, k3, k2 = 대.get("규모구간"), 대.get("KSIC3"), 대.get("KSIC2")
    표 = {"규모·업종3": (("같은 규모(%s) · %s %s" % (규, 분, k3)), lambda w: w.get("규모구간") == 규 and w.get("KSIC3") == k3, bool(규 and k3)),
         "규모·업종2": (("같은 규모(%s) · %s %s" % (규, 분, k2)), lambda w: w.get("규모구간") == 규 and w.get("KSIC2") == k2, bool(규 and k2)),
         "업종3": (("%s %s" % (분, k3)), lambda w: w.get("KSIC3") == k3, bool(k3)),
         "업종2": (("%s %s" % (분, k2)), lambda w: w.get("KSIC2") == k2, bool(k2)),
         "규모": (("같은 규모(%s)" % 규), lambda w: w.get("규모구간") == 규, bool(규)),
         "전체": ("전체", lambda w: True, True)}
    if 이름 not in 표 or not 표[이름][2]:
        return None, []
    글, f, _ok = 표[이름]
    return 글, [w for w in 창 if f(w) and w.get("CAGR5") is not None and w.get("평균이익률5") is not None]


def _z(설):
    """구간의 신뢰수준 → 표준정규 분위(양쪽). 기본 90%."""
    import statistics                                         # noqa: PLC0415
    q = float(((설.get("구간") or {}).get("신뢰수준")) or 0.90)
    return statistics.NormalDist().inv_cdf((1 + q) / 2)


def 윌슨(k, n, z):
    """윌슨 점수 구간(Wilson 1927) — 비율 k/n 의 양쪽 구간 [하, 상]. n = 0 이면 [None, None].
    작은 n · 0 · 1 근처 비율에서도 0 ~ 1 안에 서고, 정규 근사(Wald) 구간보다 포함률이 명목에 가깝다(Brown · Cai · DasGupta 2001)."""
    if not n:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return [max(0.0, c - h), min(1.0, c + h)]


def 한집단(글, W, 레경로, 차례, 설):
    """한 집단의 창 W → 그 집단의 기저율 판 {집단, 관측수, 회사수, 확률, 이상비율, 이상수, 구간, 최하넘은수, 기저율밖, 가장가까운}.
    창마다 그 창이 넘은 레짐 가운데 경로가 가장 까다로운 것(다른 넘은 레짐에 덮이지 않는 것 — 여럿이면 값이 가장 높은 것)에 센다(못 넘으면
    가장 낮은 레짐). 경로가 값 차례대로 포개져 있으면 종전 「넘은 가장 높은 레짐」 과 같다. 값이 낮은 레짐의 경로가 더 까다로운 짝은 `경로역전`
    에 남긴다(2026-11-15 — 종전 셈은 그런 레짐을 데이터와 무관하게 늘 0 으로 만들었다). 가장 낮은 레짐의 경로조차 넘은 창이 문턱(「기저율밖문턱」)
    아래면 「기저율 밖」 — 확률을 세우지 않고(확률 None) 가장 가까운 창(두 모자람 가운데 큰 쪽이 가장 작은 창)의 사실만 남긴다."""
    수 = len(레경로)
    셈 = [0] * 수                                            # 그 레짐이 「넘은 레짐 가운데 경로가 가장 까다로운 것」 인 창 수
    이상 = [0] * 수                                          # 그 레짐 경로 이상인 창 수
    def 덮음(k, j):
        """k 의 경로가 j 보다 까다롭다 — 두 축 모두 이상이고 한 축은 더 높다"""
        a, b = 레경로[k], 레경로[j]
        같거나 = a["CAGR5"] >= b["CAGR5"] - 1e-12 and a["평균이익률5"] >= b["평균이익률5"] - 1e-12
        더 = a["CAGR5"] > b["CAGR5"] + 1e-12 or a["평균이익률5"] > b["평균이익률5"] + 1e-12
        return 같거나 and 더
    for 하나 in W:
        넘은 = []
        for j in 차례:                                        # 낮은 값 → 높은 값
            길 = 레경로[j]
            if 하나["CAGR5"] >= 길["CAGR5"] - 1e-12 and 하나["평균이익률5"] >= 길["평균이익률5"] - 1e-12:
                이상[j] = 이상[j] + 1
                넘은.append(j)
        if not 넘은:
            끝 = 차례[0]
        else:
            # 2026-11-15 — 넘은 레짐 가운데 경로가 가장 까다로운 것(다른 넘은 레짐에 덮이지 않는 것)에 센다.
            # 값 차례와 경로 차례가 어긋나면(값이 낮은 레짐의 경로가 더 까다로움) 종전 셈은 그 레짐을 늘 0 으로 만들었다.
            # 서로 덮지 않는 레짐이 여럿이면 종전처럼 값이 가장 높은 것.
            극대 = [j for j in 넘은 if not any(k != j and 덮음(k, j) for k in 넘은)]
            끝 = max(극대, key=차례.index)
        셈[끝] = 셈[끝] + 1
    n, k = len(W), 수
    z = _z(설)
    역전 = [[차례[a], 차례[b]] for a in range(수) for b in range(a + 1, 수) if 덮음(차례[a], 차례[b])]
    최하 = 차례[0]
    밖 = 이상[최하] < int(설.get("기저율밖문턱", 3))
    낸 = {"집단": 글, "관측수": n, "회사수": len({w["고유번호"] for w in W}), "이상수": 이상, "이상비율": [c / n for c in 이상] if n else [None] * k,
         "최하넘은수": 이상[최하], "기저율밖": 밖, "창": "회사-5년 창(5년 매출 CAGR · 5년 매출가중 평균 영업이익률)",
         "신뢰수준": float(((설.get("구간") or {}).get("신뢰수준")) or 0.90),
         "구간꼴": "윌슨 점수 구간 %.0f%%" % (100 * float(((설.get("구간") or {}).get("신뢰수준")) or 0.90)),
         "경로역전": 역전}
    if 밖:
        낸["확률"] = [None] * k
        낸["구간"] = [[None, None] for _ in range(k)]
        p = 레경로[최하]
        if W:
            w = min(W, key=lambda w: (max(p["CAGR5"] - w["CAGR5"], p["평균이익률5"] - w["평균이익률5"]), -w["CAGR5"]))
            낸["가장가까운"] = {"t0": w.get("t0"), "CAGR5": w["CAGR5"], "평균이익률5": w["평균이익률5"], "회사명": w.get("회사명"),
                           "모자람": max(p["CAGR5"] - w["CAGR5"], p["평균이익률5"] - w["평균이익률5"])}
    else:
        낸["확률"] = [c / n for c in 셈]
        낸["셈"] = 셈
        낸["구간"] = [윌슨(c, n, z) for c in 셈]
    return 낸


def 기저율확률(창, 대, 레경로, 차례, 설):
    """창마다 그 창이 넘은 가장 높은 레짐에 둔다 → ({집단, 관측수, 회사수, 확률[레짐 원래 번호 차례], 이상비율[…], 구간 · 기저율밖 · 넓힌[…]}, 까닭).
    1.1.7 — 고른 집단의 관측이 「작은집단문턱」 아래이거나 기저율 밖이면 상위 집단(「넓힘차례」 — 같은 규모 → 전체)으로 넓혀 다시 센 판을 「넓힌」 에 나란히 둔다."""
    최소 = int(설.get("최소관측", 30))
    for 이름 in 설.get("집단차례") or ["전체"]:
        글, W = _집단(창, 대, 이름)
        if 글 is None or len(W) < 최소:
            continue
        낸 = 한집단(글, W, 레경로, 차례, 설)
        낸["집단규칙"] = 이름
        넓 = []
        if len(W) < int(설.get("작은집단문턱", 100)) or 낸["기저율밖"]:
            for 이2 in 설.get("넓힘차례") or ["규모", "전체"]:
                if 이2 == 이름:
                    continue
                글2, W2 = _집단(창, 대, 이2)
                if 글2 is None or len(W2) <= len(W) or any(x["관측수"] == len(W2) for x in 넓):
                    continue
                x = 한집단(글2, W2, 레경로, 차례, 설)
                x["집단규칙"] = 이2
                넓.append(x)
        낸["넓힌"] = 넓
        return 낸, ""
    return None, "어느 집단에도 창이 최소관측(%d) 이상 없다" % 최소


def 셈(가정, 가정경로, 설=None):
    설 = 설 or 설정()
    from 엔진.계산 import 계산                               # noqa: PLC0415
    import importlib as _il                                # noqa: PLC0415
    _민 = _il.import_module("엔진.민감도")                   # 엔진 꾸러미의 같은 이름 함수가 모듈을 가린다
    목, 확 = 선언(가정)
    R = 계산(가정, "기준")
    낸 = {"형식": 형식, "만든날": datetime.date.today().isoformat(), "평가기준일": (가정.get("메타") or {}).get("평가기준일"),
         "값을바꿈": False, "기준주당": _n(R["요약"]["주당가치"]), "종가": _n(_민.종가(가정)), "선언해시": 선언해시(가정), "신호": [],
         "근거": 설.get("_근거")}
    if not 목:
        낸["해당없음"] = "관측.레짐 선언이 없다(레짐 둘 이상 — 이름 · 시나리오 · 바꿈) — 표를 세우지 않는다"
        return 낸
    창년, 창시작 = int(설.get("창년", 5)), 설.get("창시작", "마지막실적해")
    레들 = []
    for i, x in enumerate(목):
        v = 주당(가정, x)
        p = 경로(가정, x, 창년, 창시작)
        레들.append({"이름": ("%s" % x["이름"]).strip(), "시나리오": x.get("시나리오") or "기준", "묶음글": 묶음글(가정, x), "주당": v, "경로": p,
                    "근거": x.get("근거") or ""})
    차례 = sorted(range(len(레들)), key=lambda j: (레들[j]["주당"] if 레들[j]["주당"] is not None else float("-inf")))
    낸["레짐"] = 레들
    낸["차례"] = 차례
    낸["최상위"] = 차례[-1]
    # 기저율 확률
    기 = None
    if all(r["경로"].get("CAGR5") is not None and r["경로"].get("평균이익률5") is not None for r in 레들):
        창, 대, 국, 까 = _대상과창(가정, 가정경로, 설)
        if 창 is not None:
            기, 까2 = 기저율확률(창, 대, [r["경로"] for r in 레들], 차례, 설)
            낸["기저율"] = dict(기 or {}, 국가=국, 대상={"규모구간": 대.get("규모구간"), "산업": "%s %s" % (대.get("산업분류"), 대.get("KSIC3") or "")},
                           까닭=까2 or None)
        else:
            낸["기저율"] = {"까닭": 까, "국가": 국}
    else:
        낸["기저율"] = {"까닭": "레짐 경로의 5년 창이 서지 않는다(예측 해가 마지막 실적 해 + 5 보다 짧다)"}
    if 기:
        for j, r in enumerate(레들):
            r["기저율확률"] = 기["확률"][j]
            r["이상비율"] = 기["이상비율"][j]
            r["이상수"] = 기["이상수"][j]
            r["구간"] = 기["구간"][j]
        if 기.get("기저율밖"):                                 # 1.1.7 — 가장 낮은 레짐 경로조차 넘은 창이 문턱 아래 — 확률을 세우지 않는다
            낸["기저율밖"] = {"글": "기저율 밖 — 확률을 세울 수 없음", "관측수": 기["관측수"], "최하넘은수": 기["최하넘은수"],
                          "문턱": int(설.get("기저율밖문턱", 3)), "가장가까운": 기.get("가장가까운"),
                          "넓힌": [{"집단": x["집단"], "관측수": x["관측수"], "최하넘은수": x["최하넘은수"]} for x in 기.get("넓힌") or []]}
    규칙 = ("%s" % (확.get("규칙") or "기저율")).strip()
    낸["확률규칙"] = 규칙
    낸["확률근거"] = ("%s" % (확.get("근거") or "")).strip()
    허 = float(설.get("합계허용", 1e-6))
    if 규칙 == "판단":
        값 = [_n(v) for v in (확.get("값") or [])]
        if len(값) != len(레들) or any(v is None or v < 0 for v in 값) or abs(sum(값) - 1) > 허:
            낸["확률까닭"] = "판단 확률의 값이 레짐 수와 맞지 않거나 합이 1 이 아니다"
        elif not 낸["확률근거"]:
            낸["확률까닭"] = "판단 확률에 근거가 없다 — 근거 칸을 채운다(자체검사 61 · R-175)"
        else:
            for j, r in enumerate(레들):
                r["판단확률"] = 값[j]
                r["확률"] = 값[j]
    elif 기 and 기.get("기저율밖"):
        낸["확률까닭"] = "기저율 밖 — 확률을 세울 수 없음(%s 창 %d개 가운데 가장 낮은 레짐 경로를 넘은 창 %d개 · 문턱 %d)" % (
            기["집단"], 기["관측수"], 기["최하넘은수"], int(설.get("기저율밖문턱", 3)))
    elif 기:
        for r in 레들:
            r["확률"] = r["기저율확률"]
    else:
        낸["확률까닭"] = "기저율 확률을 세우지 못했다 — %s" % ((낸.get("기저율") or {}).get("까닭") or "재료 없음")
    t0 = 낸["최상위"]
    if 낸["종가"] is not None and 레들[t0].get("주당") is not None and 레들[t0]["주당"] < 낸["종가"]:
        낸["최상위종가아래"] = True                            # 확률이 없어도 선다 — 가장 높은 레짐 값도 종가 아래(확률을 어떻게 나눠도 닿지 않는다)
    if all(r.get("확률") is not None and r.get("주당") is not None for r in 레들):
        낸["기대값"] = sum(r["확률"] * r["주당"] for r in 레들)
        P, t = 낸["종가"], 낸["최상위"]
        밖 = [j for j in range(len(레들)) if j != t]
        s = sum(레들[j]["확률"] for j in 밖)
        if P is not None and s > 0:
            Vb = sum(레들[j]["확률"] * 레들[j]["주당"] for j in 밖) / s
            Vt = 레들[t]["주당"]
            if abs(Vt - Vb) > 1e-12:
                q = (P - Vb) / (Vt - Vb)
                낸["나머지평균"] = Vb
                낸["함축최상위확률"] = q
                낸["함축판정"] = "닿음" if 0 <= q <= 1 else ("최상위 값도 종가 아래 — 확률로는 닿지 않는다" if q > 1 else "종가가 나머지 레짐의 평균 아래")
        elif P is not None:
            낸["함축판정"] = "최상위 밖 레짐의 확률이 0 이다 — 나머지 비율이 없다"
        낸["신호"].append({"출처": "레짐", "종류": "레짐 기대값", "대상": "기준", "값": 낸["기대값"], "등급": "참고",
                         "글": "레짐 %d개(확률 규칙 %s)의 기대 주당가치 %.6g · 기준 %.6g — 기준값은 바꾸지 않는다" % (len(레들), 규칙, 낸["기대값"], 낸["기준주당"] or 0)})
    elif 낸.get("기저율밖"):
        밖 = 낸["기저율밖"]
        낸["신호"].append({"출처": "레짐", "종류": "레짐 기저율 밖", "대상": "기준", "값": 밖["최하넘은수"], "등급": "참고",
                         "글": "레짐 %d개 — 같은 집단 창 %d개 가운데 가장 낮은 레짐 경로를 넘은 창 %d개 · 확률을 세우지 않는다(기대값 없음)"
                               % (len(레들), 밖["관측수"], 밖["최하넘은수"])})
    return 낸


def _가정해시(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def 쓰기(낸, 가정경로, 낼=None):
    p = 낼 or os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw", 산출이름)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(낸, f, ensure_ascii=False, indent=1)
    return p


def _p(x):
    return ("%.1f%%" % (100 * x)) if _n(x) is not None else "—"


def 화면(낸):
    if 낸.get("해당없음"):
        return "레짐 — 해당 없음: %s" % 낸["해당없음"]
    기 = 낸.get("기저율") or {}
    줄 = ["레짐 기대값 — 기준 주당가치 %.6g · 종가 %s · 확률 규칙 %s%s" % (낸.get("기준주당") or 0, ("%.6g" % 낸["종가"]) if 낸.get("종가") else "—",
                                                            낸.get("확률규칙"), (" · 기저율 집단 %s(창 %d개 · %d곳)" % (기["집단"], 기["관측수"], 기["회사수"]))
                                                            if 기.get("집단") else (" · 기저율 %s" % 기.get("까닭") if 기.get("까닭") else ""))]
    for j in 낸.get("차례") or []:
        r = 낸["레짐"][j]
        p = r.get("경로") or {}
        줄.append("  %-16s 주당 %-10s 경로 CAGR5 %s · 평균 영업이익률 %s · 이상 %s · 기저율 %s · 채택 %s" % (
            r["이름"], ("%.6g" % r["주당"]) if r.get("주당") is not None else "—", _p(p.get("CAGR5")), _p(p.get("평균이익률5")),
            _p(r.get("이상비율")), _p(r.get("기저율확률")), _p(r.get("확률"))))
    for j in 낸.get("차례") or []:
        r = 낸["레짐"][j]
        if (r.get("구간") or [None])[0] is not None:
            줄.append("  %-16s %s 구간 %s ~ %s" % (r["이름"], 기.get("구간꼴") or "", _p(r["구간"][0]), _p(r["구간"][1])))
    for x in 기.get("넓힌") or []:
        줄.append("  넓힌 집단 %s(창 %d개 · %d곳) — %s" % (x["집단"], x["관측수"], x["회사수"], "기저율 밖(최하 경로를 넘은 창 %d개)" % x["최하넘은수"]
                                                       if x.get("기저율밖") else " · ".join(_p(v) for v in x["확률"])))
    if 낸.get("확률까닭"):
        줄.append("  ! %s" % 낸["확률까닭"])
    if (낸.get("기저율밖") or {}).get("가장가까운"):
        g = 낸["기저율밖"]["가장가까운"]
        줄.append("  가장 가까운 창 — t0 %s · CAGR5 %s · 평균 영업이익률 %s" % (g.get("t0"), _p(g.get("CAGR5")), _p(g.get("평균이익률5"))))
    if 낸.get("기대값") is not None:
        줄.append("  기대값 %.6g · 함축 최상위 확률 %s(%s)" % (낸["기대값"], _p(낸.get("함축최상위확률")), 낸.get("함축판정") or "—"))
    return "\n".join(줄)


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                        # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description="레짐 기대값 — 이름 붙은 가정 묶음을 엔진으로 셈하고 확률은 기저율 패널에서(값을 바꾸지 않는다)")
    ap.add_argument("가정")
    ap.add_argument("--낼")
    a = ap.parse_args(argv)
    try:
        가정 = json.load(io.open(a.가정, encoding="utf-8"))
        낸 = 셈(가정, a.가정)
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

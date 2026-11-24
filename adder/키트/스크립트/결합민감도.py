# -*- coding: utf-8 -*-
"""결합민감도 — 손잡이 여럿을 **근거 범위 안에서 함께** 흔들어 주당가치의 분포 · 분산 분해(주효과 · 상호작용) · 쌍 상호작용을 낸다 (2026-10-23 · 통계 기법 12).

    python 스크립트/결합민감도.py 가정.json                 # 거친 바퀴 한 표의 범위 있는 손잡이 전부 · 300판 → _raw/결합민감도.json
    python 스크립트/결합민감도.py 가정.json --판 600 --씨앗 7 --상위 8

왜 — 거친 바퀴(토네이도)는 **하나씩, 나머지 고정**이다. 손잡이가 서로 물려 있으면(가동률 × 수율 · 단가 × 원가 비율 · 성장 × 재투자) 하나씩 잰 폭의 합이 함께 흔든 폭과
  다르다 — 그 차가 「유기적 연동」의 크기다. 무디스(「Deep-learning the cash flow model」 2020)는 보험 부채 현금흐름 모형의 대리 함수를 학습해 수십억 시나리오를 돌렸다.
  우리 엔진은 한 판이 수십 ms 라 대리 함수가 필요 없다 — **엔진 자체를 수백 판 돌려** 같은 질문(여러 변수가 함께 움직일 때 결과의 분포와 어느 변수 · 어느 쌍이 분산을 만드나)에 답한다.
무엇 —
  표본   손잡이마다 근거 범위 양 끝(거친 바퀴 한 표 `하오프셋` · `상오프셋` — 범위 없는 손잡이는 뺀다 · `--참고폭` 이면 ±10% 참고 폭으로 넣는다) 안에서 균등 추출(라틴 하이퍼큐브)한
         조합 N 판을 엔진으로 돈다(손잡이는 `민감도.움직이기` 로 차례로 민다 — 거친 바퀴와 같은 식). 균등 추출은 확률 주장이 아니다 — 「범위 안 어디든 같은 무게」라는 가정일 뿐
  분포   주당가치의 분위(5 · 25 · 50 · 75 · 95) · 기준 주당가치 대비 위치 · 비대칭(중앙값 − 기준)
  분해   표준화 손잡이에 주당가치 변화율을 선형 회귀 → 주효과 R² · **상호작용 · 비선형 몫 = 1 − R²** · 손잡이별 몫(표준화 계수² ÷ 합) · 상위 손잡이끼리의 곱항을 더한 회귀로 **쌍 상호작용** 순위
  대조   하나씩 잰 폭(토네이도 — 한 표의 최대변화 합)과 함께 흔든 폭(5~95 분위 폭)의 비 — 1 에서 멀수록 연동이 크다
신호(값을 정하지 않는다) — 상호작용 · 비선형 몫 ≥ 20%(참고 — 토네이도가 못 보는 몫) · 결합 분포의 5% 분위가 0 이하(참고 — 범위 조합 안에 주주가치 0 이 든다) ·
  주효과 1위 쌍의 상호작용이 주효과의 20% 넘음(참고 — 둘을 같이 적어야 하는 축) · 엔진 실패 판 비율 > 10%(경보) · 손잡이 없음(참고).
2026-10-23 밤 기본값(연구/레터워크북_최적화_20261023/03 4-3 · 4-4) —
  · **WACC · 영구성장률을 근거 범위로 넣는다.** WACC = 가정 「자본비용.대안」(없으면 레터부록 — 2026-10-24 W12 · `자본비용옮기기.읽기`) 사양의 예측기간 WACC(채택 사양과의 차)의 최저~최고(또는 Narrative.동인.표의 「대안:」
    두 값), g = [0%, 2%](2026-10-24 결정 — 영구성장률 근거 범위 · `g범위` · 위 끝은 영구기간 WACC − 1%p 아래 · 영구기간 무위험이자율(상한)도 넘지 않는다) —
    지금 g 가 그 범위 밖이면 범위는 그대로 두고 알림(가정을 바꾸지 않는다).
    종전에는 둘 다 「축 아님」이라 한 회사도 안 들어가 결합 분포가 할인율 불확실성을 뺀 폭이었다
  · 참고폭은 손잡이 꼴로 가른다 — 배율(수준 · 금액) ±10% · 가산 · 누적(증가율 · 비율 · 마진) ±1%p(손잡이가 폭을 적었으면 그 폭). 종전 ±0.1 일률은 증가율 칸에
    ±10%p 를 줘 분포가 터졌다(P5~P95 가 기준의 0.2~2.5배). 참고폭 분포는 `참고폭분포` 에 따로 두고, 위의 분포 · 표본주당은 근거 범위 손잡이만이다
  · 판 수 = max(300, 25 × 손잡이 수) — 쌍 상호작용 회귀의 표본(McKay · Beckman · Conover 1979 LHS · 손잡이당 25판)
  · 쌍 상호작용 신호는 **절대 몫**도 본다 — 곱항의 분산 몫 ≥ 1% 그리고 두 손잡이 가운데 하나의 주효과 분산 몫 ≥ 5%(주효과 대비 20% 만 보면 0.001% 손잡이끼리의 비율이 떴다)
2026-10-25 레터 재구성 R3 — **시나리오가 가른 가정 · 지렛대를 손잡이로 넣는다.** 종전 손잡이는 거친 바퀴 한 표(판단 칸 범위)와 WACC · g 뿐이라 시나리오 driver(매출
    동인 · 원가율)가 빠져, 결론이 매출 동인을 「값을 가르는 가정」 이라 하는데 결합 분포는 회전일수 · 상각률 · g 로만 흔들렸다(회차 20261024 MO · NVDA). 이제
    · 시나리오가 가른 가정 묶음(`레터.폭포묶음`)마다 손잡이 하나 — 범위 = 비관 ~ 낙관 시나리오 값(보간 t ∈ [−1, 1] · `레터이야기.시나리오보간` — 열마다 선형,
      다른 손잡이가 같은 번호를 이미 덮으면 넣지 않는다)
    · 지렛대(`레터이야기.지렛대독립` — 레터 결론 · 민감도 · 3분과 같은 가정)가 손잡이에 없으면 민감도 표 Ⅲ 의 범위(없으면 그 폭 — 참고)로 더한다
    · 손잡이 이름은 본편 가정 표의 이름이다(「A-182 재고자산 회전일수」 → 「재고자산 회전일수」 — 인터랙티브 판 화면에 내부 번호가 나가지 않게)
규칙 — 회사 · 업종 이름 없음 · 가정 불변 · 엔진 산식 불변. 종료 코드 — 0 · 1 경보 · 2 입력 오류.
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import math
import os
import random
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass
여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류           # noqa: E402

출처이름 = "결합민감도"
형식 = "결합민감도 1"
기본판 = 300
판당손잡이 = 25
쌍문턱 = {"주효과대비": 0.20, "곱항분산몫": 0.01, "주효과분산몫": 0.05}

g범위 = (0.0, 0.02)                                   # 영구성장률 근거 범위(2026-10-24 결정 — 0~2%)

# 레터 v27 P11(2026-11-10) — 손잡이 물리 범위 · 분포 터짐. 결과 전에 정한 값이다(회사 · 업종 무관)
#   정의역칸   — 그 칸의 값이 정의상 0~1 인 가정 번호(감가상각률 · 무형자산 상각률 · 법정세율). 손잡이 끝이 그 밖이면 뺀다
#   양수칸     — 정의상 0 이상인 번호(회전일수 셋 · Sales-to-Capital). 끝이 0 아래면 뺀다
#   비율배수   — 지금 값이 모두 |1| 이하(비율 꼴)인 칸에서 손잡이 끝이 |1| 을 넘고 지금 값 크기의 이 배수를 넘으면 뺀다(업종 값이 다른 정의에서 온 꼴)
#   터짐       — 분포 5분위가 −|기준| × 하단배 아래이거나 95분위가 |기준| × 상단배 위면 「터짐」 — 레터가 몫 문장 · 값폭을 읽지 않는다(`싣기가능: false`)
정의역칸 = {"156": (0.0, 1.0), "164": (0.0, 1.0), "196": (0.0, 1.0)}
양수칸 = {"178", "182", "186", "859"}
비율배수 = 5.0
터짐문턱 = {"하단배": 1.0, "상단배": 10.0}


def 판수(손잡이수, 판=None):
    """지정이 없으면 max(300, 25 × 손잡이 수)."""
    return 판 if 판 else max(기본판, 판당손잡이 * max(1, 손잡이수))


def 쌍신호인가(p):
    """쌍 상호작용 신호 조건 — 주효과 대비 20% · 곱항 분산 몫 1% · 두 손잡이 가운데 하나의 주효과 분산 몫 5%(셋 다)."""
    return (p["주효과대비"] >= 쌍문턱["주효과대비"] and p.get("곱항분산몫", 1) >= 쌍문턱["곱항분산몫"]
            and p.get("주효과분산몫", 1) >= 쌍문턱["주효과분산몫"])


def _참고폭(h):
    """근거 범위 없는 손잡이의 참고 폭 — 손잡이가 적은 폭 · 없으면 배율 ±10% · 가산 · 누적 ±1%p."""
    폭 = _수(h.get("폭"))
    if 폭:
        return 폭
    return 0.10 if (h.get("방식") or "가산") == "배율" else 0.01


def _수(v):
    try:
        return None if (v is None or isinstance(v, bool)) else float(v)
    except (TypeError, ValueError):
        return None


# ────────────────────────────────────────────────────────────── 손잡이 모으기

def _부록(가정경로):
    if not 가정경로:
        return {}
    p = os.path.join(os.path.dirname(os.path.abspath(가정경로)), "레터부록.json")
    try:
        return json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else {}
    except (OSError, ValueError):
        return {}


def 할인율손잡이(가정, 가정경로=None, 시나리오="기준"):
    """WACC · 영구성장률의 근거 범위 손잡이 → ([손잡이], [알림]). 근거가 없으면 그 손잡이는 넣지 않는다."""
    import importlib                                                 # noqa: PLC0415
    E = importlib.import_module("dcf엔진")
    M = importlib.import_module("엔진.민감도")
    낸, 알림 = [], []
    try:
        R0 = E.계산(가정, 시나리오)
    except Exception as e:                           # noqa: BLE001
        return [], ["기준 계산이 막혀 WACC · g 손잡이를 세우지 못했다(%s)" % type(e).__name__]
    W예 = _수(R0["요약"].get("예측기간WACC"))
    # WACC — 가정 「자본비용」 대안 사양(없으면 레터부록 — W12) · 동인 표 「대안:」
    import 자본비용옮기기 as _자본                                  # noqa: PLC0415
    블, _출처, 자알 = _자본.읽기(가정, _부록(가정경로))
    알림 += 자알
    값들 = []
    for x in ((블 or {}).get("대안") or []):
        v = _수(_자본.대안WACC(가정, x)[0])                       # 1.1.2(P21) — βU 로 댄 대안도 엔진이 WACC 를 셈해 넣는다
        if v is not None:
            값들.append(v)
    for x in (((가정.get("Narrative") or {}).get("동인") or {}).get("표") or []):
        for k in ("낮음", "높음"):
            q = ("%s" % (x.get(k) or "")).split(":")
            if len(q) >= 3 and q[0] == "대안" and _수(q[1]) is not None:
                값들.append(_수(q[1]))
    if 값들 and W예 is not None:
        d = [v - W예 for v in 값들]
        하, 상 = min(0.0, min(d)), max(0.0, max(d))
        if 상 > 하:
            낸.append({"이름": "가중평균자본비용 (WACC)", "손잡이": {"대상": list(M.WACC대상), "방식": "가산", "이름": "가중평균자본비용 (WACC)"},
                      "하": 하, "상": 상, "출처": "근거 범위 — 자본비용 대안 사양 %d개(%.2f%%~%.2f%%)" % (len(값들), min(값들) * 100, max(값들) * 100), "최대변화": None})
    else:
        알림.append("WACC 근거 범위 없음(가정 · 레터부록의 자본비용.대안 · 동인 표 「대안:」 모두 없음) — 결합 분포에 할인율을 넣지 않았다")
    # 영구성장률 — 근거 범위 [0%, 2%](2026-10-24 결정). 위 끝은 영구기간 WACC − 1%p(엔진이 g ≥ WACC 를 막는다) · 영구기간 무위험이자율(g ≤ Rf)을 넘지 않는다
    def g의(시):
        try:
            return _수(M._시점값(가정, M.g번호, 시))
        except Exception:                            # noqa: BLE001
            return None
    g0 = g의(시나리오)
    Rf = _수(((R0.get("WACC") or {}).get("영구기간") or {}).get("Rf"))
    W영 = _수(R0["요약"].get("영구기간WACC"))
    하, 상 = g범위
    중 = None
    try:                                                     # 1.1.4(R5) — 근거 범위를 그 관할의 g 기본값(국내 1.0% · 그 밖 영구기간 Rf − 근처폭) ± 1%p 로(옛 상수 0~2% 는 국내 기본값의 둘레였다)
        import 갭해석 as _G                                  # noqa: PLC0415
        폭 = float(((_G.설정().get("영구짝") or {}).get("근처폭")) or 0.005)
        중 = _수((_G.영구기본값(가정, {"Rf": Rf, "g짝": (Rf - 폭) if Rf is not None else None}) or {}).get("값"))
    except Exception:                                        # noqa: BLE001
        중 = None
    if 중 is not None:
        하, 상 = max(0.0, 중 - (g범위[1] - g범위[0]) / 2.0), 중 + (g범위[1] - g범위[0]) / 2.0
    if Rf is not None:
        상 = min(상, Rf)
    if W영 is not None:
        상 = min(상, W영 - 0.01)
    if g0 is None:
        알림.append("영구성장률 근거 범위 없음(지금 g 를 못 읽음)")
    elif 상 > 하 + 1e-9:
        낸.append({"이름": "영구성장률 (g)", "손잡이": {"대상": [M.g번호], "방식": "값", "이름": "영구성장률 (g)"}, "하": 하, "상": 상,
                  "출처": "근거 범위 — 영구성장률 %.1f%%~%.1f%%(g 기본값%s ± 1%%p%s)" % (
                      하 * 100, 상 * 100, (" %.2f%%" % (중 * 100)) if 중 is not None else "", (" · 위 끝은 영구기간 WACC · 무위험이자율 아래로" if (중 is not None and 상 < 중 + 0.01 - 1e-12) else "")), "최대변화": None})
        if not (하 - 1e-12 <= g0 <= 상 + 1e-12):
            알림.append("지금 영구성장률 %.2f%% 가 근거 범위 %.1f%%~%.1f%% 밖이다 — 가정은 바꾸지 않았다(사람이 확인)" % (g0 * 100, 하 * 100, 상 * 100))
    else:
        알림.append("영구성장률 근거 범위가 서지 않는다(영구기간 WACC 가 너무 낮다)")
    return 낸, 알림


def 손잡이모으기(가정, 가정경로=None, 시나리오="기준", 참고폭=False, 상위=None, 할인율=True):
    """[{이름, 손잡이, 하, 상, 출처}] — 거친 바퀴 한 표(범위 있는 줄). 한 표를 못 세우거나 비면(그리고 참고폭) 기본 후보 ±10%."""
    import 거친바퀴 as B                                 # noqa: PLC0415
    낸 = []
    try:
        줄이름, 종류 = B.줄표(가정경로) if 가정경로 else ({}, {})
        T = B.한표(가정, 시나리오, 줄이름=줄이름, 종류=종류, 가정경로=가정경로)
        for r in T.get("표") or []:
            h = r.get("손잡이")
            if not isinstance(h, dict) or r.get("축아님") or r.get("분해칸"):
                continue
            하, 상 = _수(r.get("하오프셋")), _수(r.get("상오프셋"))
            if 하 is None or 상 is None or 하 == 상:
                continue
            낸.append({"이름": r.get("이름") or h.get("이름"), "손잡이": h, "하": min(하, 상), "상": max(하, 상), "출처": r.get("폭출처") or "근거 범위", "최대변화": r.get("최대변화")})
    except Exception as e:                           # noqa: BLE001
        낸 = []
        까닭 = "%s" % e
    else:
        까닭 = ""
    if 할인율:                                         # 2026-10-23 밤 — WACC · g 는 「축 아님」이라 한 표에서 빠진다. 근거 범위가 있으면 분포에는 넣는다
        있는 = {tuple("%s" % d for d in h["손잡이"]["대상"]) for h in 낸}
        할, 할알림 = 할인율손잡이(가정, 가정경로, 시나리오)
        낸 += [h for h in 할 if tuple("%s" % d for d in h["손잡이"]["대상"]) not in 있는]
        if 할알림:
            까닭 = " · ".join([x for x in (까닭,) if x] + 할알림)
    if 참고폭:                                        # 근거 범위 없는 손잡이도 ±폭(참고)으로 — 있는 것은 그대로
        있는 = {tuple("%s" % d for d in h["손잡이"]["대상"]) for h in 낸}
        for a in B.기본후보(가정, 시나리오):
            h = a["손잡이"]
            if tuple("%s" % d for d in h["대상"]) in 있는:
                continue
            폭 = _참고폭(h)
            낸.append({"이름": h.get("이름") or " · ".join("%s" % d for d in h["대상"]), "손잡이": h, "하": -폭, "상": 폭, "출처": "참고 폭 ±%.3g(근거 범위 없음)" % 폭, "최대변화": None,
                      "참고폭": True})
    낸 += 시나리오손잡이(가정, 낸)                          # 2026-10-25 R3 — 시나리오가 가른 가정(driver · 딸린행)도 저자가 정한 범위 안에서 함께
    지, 지알림 = 지렛대손잡이(가정, 낸, 가정경로)
    낸 += 지
    if 지알림:
        까닭 = " · ".join([x for x in (까닭,) if x] + 지알림)
    이름붙이기(가정, 낸)
    if 상위 and len(낸) > 상위:
        낸.sort(key=lambda x: -(x.get("최대변화") or 0))
        낸 = 낸[:상위]
    return 낸, 까닭


def _구(가정):
    import importlib                                                 # noqa: PLC0415
    try:
        return importlib.import_module("엔진.스키마").검증전부(가정)[2] or {}
    except Exception:                                # noqa: BLE001
        return 가정.get("구조") or {}


def _덮은번호(낸):
    return {("%s" % d).replace("A-", "") for h in 낸 for d in (h.get("손잡이") or {}).get("대상") or []}


def 시나리오손잡이(가정, 낸=()):
    """시나리오가 가른 가정 묶음(`레터.폭포묶음` — 비관 · 기준 · 낙관 값이 다른 가정)마다 손잡이 하나. 범위는 비관(−1) ~ 낙관(+1) 시나리오 값이고
    그 사이는 열마다 선형(`레터이야기.시나리오보간`). 다른 손잡이가 같은 번호를 덮고 있으면 넣지 않는다(판단 칸의 근거 범위가 먼저)."""
    try:
        import 레터 as _L                                            # noqa: PLC0415
        묶음 = _L.폭포묶음(가정, _구(가정))
    except Exception:                                # noqa: BLE001
        return []
    덮 = _덮은번호(낸)
    새 = []
    for 묶, 번들 in 묶음:
        if set(번들) & 덮:
            continue
        새.append({"이름": 묶, "손잡이": {"대상": list(번들), "방식": "시나리오", "이름": 묶}, "하": -1.0, "상": 1.0,
                  "출처": "비관 · 낙관 시나리오 값(저자가 근거로 정한 이야기의 양 끝 · 그 사이는 선형)", "최대변화": None, "시나리오": True})
    return 새


def 지렛대손잡이(가정, 낸=(), 가정경로=None):
    """지렛대(`레터이야기.지렛대독립`)가 손잡이에 없으면 더한다 → ([손잡이], [알림]). 시나리오 지렛대는 시나리오 손잡이(번호 전부), 민감도 표 Ⅲ 지렛대는
    그 줄의 범위(없으면 ± 폭 — 참고 폭)."""
    try:
        import 레터이야기 as N                                      # noqa: PLC0415
        d = N.지렛대독립(가정, 가정경로)
    except Exception as e:                           # noqa: BLE001
        return [], ["지렛대를 셈하지 못했다(%s) — 결합 분포에 지렛대가 들었는지 확인하지 못했다" % type(e).__name__]
    if not d:
        return [], []
    덮 = _덮은번호(낸)
    대 = [("%s" % x) for x in d.get("대상") or []]
    번 = [b for b in d.get("번호들") or [] if ("%s" % b).isdigit()]
    if (번 and set(번) <= 덮) or (대 and all(x.startswith("WACC") for x in 대) and any(x.startswith("WACC") for x in 덮)) or (대 and set(대) <= 덮):
        return [], []
    if d.get("잣대") == "시나리오":
        갈 = [b for b in 번 if N._변동(가정, b)]
        return [{"이름": d.get("이름") or " · ".join(갈), "손잡이": {"대상": 갈, "방식": "시나리오", "이름": d.get("이름")}, "하": -1.0, "상": 1.0,
                 "출처": "비관 · 낙관 시나리오 값(지렛대 — 레터 결론의 「값을 가르는 가정」)", "최대변화": None, "시나리오": True, "지렛대": True}], []
    i = d.get("표3")
    if i is None and d.get("잣대") == "대안":                 # 1.1.7 — 할인율 대안 사양 지렛대는 민감도 표 Ⅲ 의 WACC 줄로 옮긴다
        i = next((j for j, r in enumerate(N.표3손잡이(가정)) if r["대상"] and all(("%s" % x).startswith("WACC") for x in r["대상"])), None)
    if i is None:
        return [], ["지렛대(%s)를 손잡이로 옮길 범위가 없다 — 결합 분포에 넣지 않았다" % d.get("이름")]
    r = N.표3손잡이(가정)[i]
    h = {"대상": list(r["대상"]), "방식": r.get("방식") or "가산", "이름": d.get("이름")}
    if r.get("범위"):
        하, 상 = sorted(r["범위"])
        if h["방식"] == "값":
            기 = _수(r.get("기준값"))
            if 기 is None:
                return [], ["지렛대(%s)의 기준값을 읽지 못했다 — 결합 분포에 넣지 않았다" % d.get("이름")]
            하, 상, h["방식"] = 하 - 기, 상 - 기, "가산"
        return [{"이름": d.get("이름"), "손잡이": h, "하": 하, "상": 상, "출처": "근거 범위(민감도 표의 선언 범위 · 지렛대)", "최대변화": None, "지렛대": True}], []
    폭 = _수(r.get("폭")) or 0.0
    if h["방식"] == "값":
        h["방식"] = "가산"
    return [{"이름": d.get("이름"), "손잡이": h, "하": -폭, "상": 폭, "출처": "민감도 표의 폭 ±%.3g(근거 범위 아님 · 지렛대라 넣었다)" % 폭, "최대변화": None,
             "지렛대": True, "참고폭": True}], []


def 이름붙이기(가정, 낸):
    """손잡이 이름을 본편 가정 표의 이름으로(`레터이야기.손잡이본편이름`) — 같은 이름이 둘이면 뒤에 대상 수를 붙여 가른다(몫 문장이 이름으로 맞댄다)."""
    try:
        import 레터이야기 as N                                      # noqa: PLC0415
    except Exception:                                # noqa: BLE001
        return
    구 = _구(가정)
    본 = {}
    for h in 낸:
        이 = N.손잡이본편이름(구, (h.get("손잡이") or {}).get("대상") or [], h.get("이름")) or h.get("이름")
        if 이 in 본:
            본[이] += 1
            이 = "%s(%d)" % (이, 본[이])
        else:
            본[이] = 1
        h["이름"] = 이


# ────────────────────────────────────────────────────────────── 물리 범위 · 터짐(레터 v27 P11)

def _기준값들(가정, 번, 시나리오="기준", 열=None):
    """가정 번호의 지금 값들(그 시나리오 — 공통 벌이면 그것) — 시점가정은 값 하나, 열별 가정은 예측 · 영구 열(열 제한이 있으면 그 열만)."""
    s = (가정.get("시점가정") or {}).get(번)
    if s is not None:
        v = s.get(시나리오, s.get("공통")) if isinstance(s, dict) else s
        v = _수(v)
        return [v] if v is not None else []
    g = (가정.get("가정") or {}).get(번)
    if not isinstance(g, dict):
        return []
    벌 = g.get(시나리오) if isinstance(g.get(시나리오), dict) else g.get("공통")
    if not isinstance(벌, dict):
        return []
    return [_수(v) for k, v in 벌.items() if (열 is None or k in 열) and _수(v) is not None]


def _끝값(v, 방식, x):
    if 방식 == "값":
        return x
    if 방식 == "배율":
        return v * (1 + x)
    return v + x


def 물리점검(가정, h, 시나리오="기준"):
    """손잡이 하나의 물리 범위 점검 → None(괜찮다 · 판정 못 함) 또는 {까닭 · 대상 · 기준값범위 · 끝값범위 · 정의역}.
    시나리오 손잡이(비관 ~ 낙관 사이 — 저자가 정한 값의 사이라 정의역 안)와 숫자 칸이 아닌 대상(WACC · 매출성장 · g …)은 보지 않는다."""
    손 = h.get("손잡이") or {}
    방식 = 손.get("방식") or "가산"
    if 방식 in ("시나리오", "누적") or h.get("시나리오"):
        return None
    하, 상 = _수(h.get("하")), _수(h.get("상"))
    if 하 is None or 상 is None:
        return None
    for d in 손.get("대상") or []:
        번 = ("%s" % d).replace("A-", "")
        if not 번.isdigit():
            continue
        기들 = _기준값들(가정, 번, 시나리오, 손.get("열"))
        if not 기들:
            continue
        끝들 = [_끝값(v, 방식, x) for v in 기들 for x in (하, 상)]
        lo, hi = min(끝들), max(끝들)
        정 = 정의역칸.get(번)
        까닭 = None
        if 정 and (lo < 정[0] - 1e-12 or hi > 정[1] + 1e-12):
            까닭 = "A-%s 는 정의상 %.4g~%.4g 인 칸인데 손잡이 끝이 %.4g~%.4g 다" % (번, 정[0], 정[1], lo, hi)
        elif 번 in 양수칸 and lo < 0:
            까닭 = "A-%s 는 정의상 0 이상인 칸인데 손잡이 아래 끝이 %.4g 다" % (번, lo)
        else:
            크기 = max(abs(v) for v in 기들)
            if 크기 <= 1.0 and max(abs(lo), abs(hi)) > 1.0 and max(abs(lo), abs(hi)) > 비율배수 * max(크기, 0.01):
                까닭 = "A-%s 는 지금 값이 비율 꼴(최대 %.4g)인데 손잡이 끝(%.4g~%.4g)이 1 을 넘고 지금 값의 %.0f배를 넘는다(다른 정의의 값이 섞인 꼴)" % (
                    번, 크기, lo, hi, 비율배수)
        if 까닭:
            return {"까닭": 까닭, "대상": 번, "기준값범위": [min(기들), max(기들)], "끝값범위": [lo, hi], "정의역": list(정) if 정 else None}
    return None


def 물리거르개(가정, 손들, 시나리오="기준"):
    """(남은 손잡이, 뺀 손잡이 [{이름 · 대상 · 방식 · 하 · 상 · 출처 · 까닭 · …}]) — 물리 범위 밖 손잡이를 결합에서 뺀다(가정은 바꾸지 않는다)."""
    남, 뺀 = [], []
    for h in 손들:
        try:
            p = 물리점검(가정, h, 시나리오)
        except Exception:                            # noqa: BLE001 — 점검 못 하면 종전처럼 둔다
            p = None
        if p:
            뺀.append(dict({"이름": h.get("이름"), "대상": list((h.get("손잡이") or {}).get("대상") or []), "방식": (h.get("손잡이") or {}).get("방식"),
                            "하": h.get("하"), "상": h.get("상"), "출처": h.get("출처")}, **p))
        else:
            남.append(h)
    return 남, 뺀


def 터짐판정(분포, 기준):
    """분포가 터졌나 → (터짐 bool, [까닭]). 5분위 < −|기준| × 하단배 · 95분위 > |기준| × 상단배 · 기준 0 · 분위 없음."""
    까닭 = []
    if not 분포 or 분포.get("P5") is None or 기준 is None:
        return False, 까닭
    k = abs(기준)
    if k <= 0:
        return False, 까닭
    if 분포["P5"] < -k * 터짐문턱["하단배"]:
        까닭.append("5분위 주당가치 %.4g 가 −기준(%.4g)의 %.0f배보다 아래 — 범위 조합의 하단이 주주가치 0 아래로 크게 내려간다" % (분포["P5"], k, 터짐문턱["하단배"]))
    if 분포.get("P95") is not None and 분포["P95"] > k * 터짐문턱["상단배"]:
        까닭.append("95분위 주당가치 %.4g 가 기준(%.4g)의 %.0f배보다 위" % (분포["P95"], k, 터짐문턱["상단배"]))
    return bool(까닭), 까닭


# ────────────────────────────────────────────────────────────── 표본 · 엔진

def 라틴(n, k, rng):
    """라틴 하이퍼큐브 [0,1]^k — 축마다 n 칸을 섞어 하나씩."""
    열 = []
    for _ in range(k):
        칸 = list(range(n))
        rng.shuffle(칸)
        열.append([(c + rng.random()) / n for c in 칸])
    return [[열[j][i] for j in range(k)] for i in range(n)]


def 돌리기(가정, 손들, n, 시나리오, 씨앗):
    import importlib                                                 # noqa: PLC0415
    M = importlib.import_module("엔진.민감도")
    E = importlib.import_module("dcf엔진")
    보간 = importlib.import_module("레터이야기").시나리오보간
    rng = random.Random(씨앗)
    U = 라틴(n, len(손들), rng)
    기준 = E.계산(가정, 시나리오)["요약"]["주당가치"]
    표본, 실패 = [], 0
    옛 = sys.stderr
    for u in U:
        a = 가정
        x들 = []
        try:
            for j, h in enumerate(손들):
                x = h["하"] + (h["상"] - h["하"]) * u[j]
                x들.append(x)
                if (h["손잡이"].get("방식") or "") == "시나리오":         # 2026-10-25 R3 — 비관 · 기준 · 낙관 값 사이를 열마다 선형으로(기준 시나리오에서)
                    a = 보간(가정, h["손잡이"]["대상"], x, 바탕=a)
                else:
                    a = M.움직이기(a, h["손잡이"], x, 시나리오)
            sys.stderr = io.StringIO()
            try:
                v = E.계산(a, 시나리오)["요약"]["주당가치"]
            finally:
                sys.stderr = 옛
            if v is None or not math.isfinite(v):
                실패 += 1
                continue
            표본.append({"u": u, "x": x들, "주당": v})
        except Exception:                                            # noqa: BLE001 — 막힌 조합(가정오류)은 실패로 센다
            sys.stderr = 옛
            실패 += 1
    return 기준, 표본, 실패


# ────────────────────────────────────────────────────────────── 분해

def _회귀(X, y):
    """최소제곱 — X 는 상수항 포함 행렬. → (계수, R²) 또는 (None, None)."""
    n, k = len(X), len(X[0])
    XtX = [[sum(X[r][i] * X[r][j] for r in range(n)) for j in range(k)] for i in range(k)]
    Xty = [sum(X[r][i] * y[r] for r in range(n)) for i in range(k)]
    inv = _역행렬(XtX)
    if inv is None:
        return None, None
    β = [sum(inv[i][j] * Xty[j] for j in range(k)) for i in range(k)]
    ŷ = [sum(b * X[r][i] for i, b in enumerate(β)) for r in range(n)]
    ȳ = sum(y) / n
    sst = sum((v - ȳ) ** 2 for v in y)
    sse = sum((v - w) ** 2 for v, w in zip(y, ŷ))
    return β, (1 - sse / sst) if sst > 0 else None


def _역행렬(M):
    n = len(M)
    A = [list(map(float, r)) + [1.0 if i == j else 0.0 for j in range(n)] for i, r in enumerate(M)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(A[r][c]))
        if abs(A[p][c]) < 1e-12:
            return None
        A[c], A[p] = A[p], A[c]
        피 = A[c][c]
        A[c] = [v / 피 for v in A[c]]
        for r in range(n):
            if r != c and A[r][c] != 0:
                f = A[r][c]
                A[r] = [a - f * b for a, b in zip(A[r], A[c])]
    return [r[n:] for r in A]


def 분해(손들, 표본, 기준):
    """주효과 회귀(표준화 u: −1~1) · 상호작용 몫 · 손잡이 몫 · 쌍 상호작용."""
    if len(표본) < max(10, 3 * len(손들) + 3):
        return {"건너뜀": "표본 %d — 손잡이 %d개의 회귀에 모자란다" % (len(표본), len(손들))}
    y = [(s["주당"] - 기준) / abs(기준) if 기준 else s["주당"] for s in 표본]
    Z = [[2 * u - 1 for u in s["u"]] for s in 표본]
    X = [[1.0] + z for z in Z]
    β, R2 = _회귀(X, y)
    if β is None:
        return {"건너뜀": "회귀가 특이하다"}
    k = len(손들)
    몫 = [b * b for b in β[1:]]
    합 = sum(몫) or 1.0
    ȳ = sum(y) / len(y)
    vy = sum((v - ȳ) ** 2 for v in y) / len(y) or 1e-12        # 균등 z(−1~1)의 분산 1/3 · 독립 곱의 분산 1/9 — 절대 분산 몫(03 4-4)
    주효과 = sorted([{"이름": 손들[j]["이름"], "표준화계수": β[j + 1], "몫": 몫[j] / 합, "분산몫": 몫[j] / 3.0 / vy,
                    "범위": [손들[j]["하"], 손들[j]["상"]], "출처": 손들[j]["출처"]} for j in range(k)],
                key=lambda t: -t["몫"])
    상위 = [손들.index(next(h for h in 손들 if h["이름"] == t["이름"])) for t in 주효과[:min(6, k)]]
    쌍 = []
    X2 = [x[:] for x in X]
    쌍이름 = []
    for a in range(len(상위)):
        for b in range(a + 1, len(상위)):
            i, j = 상위[a], 상위[b]
            for r in range(len(X2)):
                X2[r].append(Z[r][i] * Z[r][j])
            쌍이름.append((i, j))
    β2, R2b = (_회귀(X2, y) if 쌍이름 else (None, None))
    if β2 is not None:
        for m, (i, j) in enumerate(쌍이름):
            c = β2[1 + k + m]
            쌍.append({"쌍": [손들[i]["이름"], 손들[j]["이름"]], "계수": c, "주효과대비": abs(c) / max(abs(β2[1 + i]), abs(β2[1 + j]), 1e-12),
                      "곱항분산몫": c * c / 9.0 / vy, "주효과분산몫": max(β[1 + i] ** 2, β[1 + j] ** 2) / 3.0 / vy})
        쌍.sort(key=lambda t: -abs(t["계수"]))
    return {"주효과R2": R2, "상호작용비선형몫": (1 - R2) if R2 is not None else None, "쌍포함R2": R2b, "주효과": 주효과, "쌍": 쌍[:8], "표본": len(표본)}


def 분위(xs, q):
    v = sorted(xs)
    if not v:
        return None
    i = (len(v) - 1) * q
    lo, hi = int(math.floor(i)), int(math.ceil(i))
    return v[lo] + (v[hi] - v[lo]) * (i - lo)


def 분석(가정, 가정경로=None, 시나리오="기준", n=None, 씨앗=1, 참고폭=False, 상위=None):
    """분포 · 분해 · 표본주당은 근거 범위 손잡이(WACC · g 포함)만. 참고폭이면 범위 없는 손잡이를 더한 분포를 `참고폭분포` 에 따로 낸다."""
    손들, 까닭 = 손잡이모으기(가정, 가정경로, 시나리오, False, 상위)
    n = 판수(len(손들), n)
    신호 = []

    def 신(종류, 대상, 값, 문턱, 글, 등급="참고"):
        신호.append({"출처": 출처이름, "종류": 종류, "대상": 대상, "값": 값, "문턱": 문턱, "글": 글, "등급": 등급})
    낸 = {"형식": 형식, "만든날": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "시나리오": 시나리오, "판": n, "씨앗": 씨앗,
         "손잡이": [{k: v for k, v in h.items() if k != "손잡이"} | {"대상": list(h["손잡이"]["대상"]), "방식": h["손잡이"].get("방식")} for h in 손들], "신호": 신호}
    if not 손들:
        신("손잡이 없음", "한 표", None, None, "범위 있는 손잡이가 없다(%s) — 거친 바퀴 한 표의 근거 범위를 먼저 채우거나 --참고폭 으로 ±10%% 참고 폭을 쓴다" % (까닭 or "한 표가 비었다"))
        return 낸, ""
    기준, 표본, 실패 = 돌리기(가정, 손들, n, 시나리오, 씨앗)
    값 = [s["주당"] for s in 표본]
    낸.update({"기준주당": 기준, "성공": len(표본), "실패": 실패,
              "분포": {"P5": 분위(값, 0.05), "P25": 분위(값, 0.25), "P50": 분위(값, 0.5), "P75": 분위(값, 0.75), "P95": 분위(값, 0.95), "최소": min(값) if 값 else None, "최대": max(값) if 값 else None,
                     "기준위치": (sum(1 for v in 값 if v <= 기준) / len(값)) if 값 else None, "비대칭": ((분위(값, 0.5) - 기준) / abs(기준)) if (값 and 기준) else None}})
    낸["분해"] = 분해(손들, 표본, 기준)
    # 판마다의 주당가치(성공한 판 · 뽑은 차례) — 인터랙티브 레터가 분포를 쌓아 그린다(값을 다시 셈하지 않는다 · 2026-10-23)
    낸["표본주당"] = [round(v, 4) for v in 값]
    토 = sum(h.get("최대변화") or 0 for h in 손들 if h.get("최대변화") is not None)
    함께 = ((낸["분포"]["P95"] - 낸["분포"]["P5"]) / abs(기준)) if (값 and 기준) else None
    낸["대조"] = {"토네이도_최대변화합": 토 or None, "함께_P5~P95폭": 함께, "비": (함께 / 토) if (토 and 함께 is not None) else None,
               "뜻": "하나씩 잰 폭의 합(토네이도)과 함께 흔든 5~95 분위 폭 — 1 에서 멀수록 손잡이가 서로 물려 있다(또는 범위가 치우쳐 있다)"}
    if n and 실패 / n > 0.10:
        신("엔진 실패 비율", "표본", 실패 / n, 0.10, "%d판 가운데 %d판이 막혔다(가정오류 — g ≥ WACC · ROIC ≤ 0 따위) — 범위 조합이 엔진의 정의역을 벗어난다. 범위를 좁히거나 막힌 쪽 끝을 본다" % (n, 실패), "경보")
    d = 낸["분해"]
    if isinstance(d.get("상호작용비선형몫"), float) and d["상호작용비선형몫"] >= 0.20:
        신("상호작용 · 비선형 몫", "분해", d["상호작용비선형몫"], 0.20,
          "주당가치 변동의 %.0f%% 가 주효과 선형으로 설명되지 않는다(상호작용 · 비선형) — 하나씩 흔드는 토네이도가 못 보는 몫. 상위 쌍 %s"
          % (d["상호작용비선형몫"] * 100, " · ".join("%s×%s" % tuple(p["쌍"]) for p in d.get("쌍", [])[:2]) or "—"))
    for p in d.get("쌍", [])[:3]:
        if 쌍신호인가(p):
            신("쌍 상호작용", " × ".join(p["쌍"]), p["계수"], "주효과의 20%",
              "%s 와 %s 의 곱항이 각자 주효과의 %.0f%% — 둘은 따로 적을 수 없다(driver 묶음 · 딸린행). 하나를 축으로 삼으면 다른 하나를 같이 선언한다" % (p["쌍"][0], p["쌍"][1], p["주효과대비"] * 100))
            break
    if 값 and 낸["분포"]["P5"] is not None and 낸["분포"]["P5"] <= 0:
        신("결합 분포 하단 0 이하", "P5", 낸["분포"]["P5"], 0, "근거 범위 조합의 5%% 분위 주당가치가 %.4g — 범위 안 조합에 주주가치 0 이 든다(레버리지 · 넓은 범위)" % 낸["분포"]["P5"])
    낸["할인율포함"] = sorted({"WACC" if "WACC" in "".join(map(str, h["손잡이"]["대상"])) else "g" for h in 손들
                           if any(("%s" % t).startswith("WACC") or "%s" % t == "212" for t in h["손잡이"]["대상"])})
    if 까닭:
        낸["알림"] = 까닭
    if 참고폭:                                        # 범위 없는 손잡이까지 참고 폭으로 — 따로 낸다(레터 · 인터랙티브는 위 분포만 쓴다)
        손2, _ = 손잡이모으기(가정, 가정경로, 시나리오, True, 상위)
        n2 = 판수(len(손2))
        기2, 표2, 실2 = 돌리기(가정, 손2, n2, 시나리오, 씨앗)
        v2 = [x["주당"] for x in 표2]
        낸["참고폭분포"] = {"손잡이": len(손2), "참고폭손잡이": sum(1 for h in 손2 if h.get("참고폭")), "판": n2, "성공": len(표2), "실패": 실2,
                       "분포": {q: 분위(v2, p) for q, p in (("P5", 0.05), ("P25", 0.25), ("P50", 0.5), ("P75", 0.75), ("P95", 0.95))} if v2 else None,
                       "뜻": "근거 범위가 없는 손잡이에 참고 폭(배율 ±10% · 가산 ±1%p)을 더한 분포 — 「범위 없는 칸이 더하는 폭」으로만 읽는다(레터 · 인터랙티브 분포가 아니다)"}
    return 낸, ""


def 쓰기(낸, 가정경로, 낼=None):
    p = 낼 or os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw", "결합민감도.json")
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with io.open(p, "w", encoding="utf-8") as f:
        json.dump(낸, f, ensure_ascii=False, indent=1, default=str)
    return p


def 표찍기(낸):
    if "분포" not in 낸:
        for s in 낸["신호"]:
            print("  [%s] %s — %s" % (s["등급"], s["종류"], s["글"]))
        return
    b, k = 낸["분포"], 낸["기준주당"]
    print("결합민감도 — 손잡이 %d · %d판(성공 %d · 실패 %d) · 기준 주당 %s" % (len(낸["손잡이"]), 낸["판"], 낸["성공"], 낸["실패"], "{:,.0f}".format(k) if k else k))
    print("  분포 P5 %s · P25 %s · P50 %s · P75 %s · P95 %s · 기준 위치 %.0f%% · 비대칭 %+.1f%%" % tuple(["{:,.0f}".format(b[q]) for q in ("P5", "P25", "P50", "P75", "P95")] + [b["기준위치"] * 100, b["비대칭"] * 100]))
    d = 낸["분해"]
    if "주효과R2" in d:
        print("  주효과 R² %.2f · 상호작용 · 비선형 몫 %.0f%% · 쌍 포함 R² %s" % (d["주효과R2"], d["상호작용비선형몫"] * 100, ("%.2f" % d["쌍포함R2"]) if d["쌍포함R2"] is not None else "-"))
        for t in d["주효과"][:8]:
            print("    %-36s 몫 %5.1f%%  계수 %+.3f  범위 %s" % (t["이름"][:36], t["몫"] * 100, t["표준화계수"], ["%.4g" % x for x in t["범위"]]))
        for p in d["쌍"][:3]:
            print("    쌍 %s × %s  계수 %+.4f (주효과 대비 %.0f%% · 곱항 분산 몫 %.2f%%)" % (p["쌍"][0][:18], p["쌍"][1][:18], p["계수"], p["주효과대비"] * 100, p.get("곱항분산몫", 0) * 100))
    else:
        print("  분해 — %s" % d.get("건너뜀"))
    c = 낸["대조"]
    print("  대조 — 토네이도 최대변화 합 %s · 함께 P5~P95 폭 %s · 비 %s" % (("%.0f%%" % (c["토네이도_최대변화합"] * 100)) if c["토네이도_최대변화합"] else "-",
                                                     ("%.0f%%" % (c["함께_P5~P95폭"] * 100)) if c["함께_P5~P95폭"] is not None else "-", ("%.2f" % c["비"]) if c["비"] else "-"))
    if 낸.get("참고폭분포") and 낸["참고폭분포"].get("분포"):
        r = 낸["참고폭분포"]
        print("  참고폭 분포(따로) — 손잡이 %d(참고폭 %d) · P5 %s · P50 %s · P95 %s" % (r["손잡이"], r["참고폭손잡이"], *["{:,.0f}".format(r["분포"][q]) for q in ("P5", "P50", "P95")]))
    if 낸.get("알림"):
        print("  알림 — %s" % 낸["알림"])
    for s in 낸["신호"]:
        print("  [%s] %s — %s" % (s["등급"], s["종류"], s["글"]))


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description=__doc__.split("\n")[0])
    ap.add_argument("가정")
    ap.add_argument("--낼")
    ap.add_argument("--시나리오", default="기준")
    ap.add_argument("--판", type=int, default=None, help="판 수(기본 max(300, 25 × 손잡이 수))")
    ap.add_argument("--씨앗", type=int, default=1)
    ap.add_argument("--참고폭", action="store_true", help="근거 범위 없는 손잡이에 참고 폭(배율 ±10% · 가산 ±1%p)을 더한 분포를 참고폭분포 에 따로 낸다")
    ap.add_argument("--상위", type=int, help="거친 바퀴 최대변화 상위 몇 개 손잡이만")
    a = ap.parse_args()
    if not os.path.exists(a.가정):
        print("가정 파일이 없다: %s" % a.가정)
        return 입력오류
    try:
        가정 = json.load(io.open(a.가정, encoding="utf-8"))
    except ValueError as e:
        print("가정 JSON 파손 — %s" % e)
        return 입력오류
    낸, _ = 분석(가정, a.가정, a.시나리오, a.판, a.씨앗, a.참고폭, a.상위)
    print("→ %s" % 쓰기(낸, a.가정, a.낼))
    표찍기(낸)
    return 발견 if any(s["등급"] == "경보" for s in 낸["신호"]) else 통과


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""계절추세 — 분기 매출을 국소 선형 추세 + 분기 계절 + 선행지표 회귀로 나눠(구조 시계열) 잔여 기간 매출의 「길 ④」 후보를 낸다
(기법 8 · 2026-10-21).

무엇을 하나
  로그 분기 매출 y_t 를 상태공간으로 둔다 — 수준 l · 기울기 b(국소 선형 추세) · 계절 s(분기 더미, 넷의 합 0) · 선행지표 계수 β.
      y_t = l_t + s_t + Σ β_j x_{j,t} + ε_t ,  l_{t+1} = l_t + b_t + η ,  b_{t+1} = b_t + ζ ,  s_{t+1} = −(s_t + s_{t−1} + s_{t−2}) + ω
  ① 분산(수준 · 기울기 · 계절 · 관측)은 지표 없는 바탕 모형의 칼만 우도를 로그 눈금 좌표 탐색으로 최대화해 정하고, 모든 모형에 같게 쓴다.
  ② **스파이크-앤-슬랩은 정확한 베이지안 모형 평균으로 한다.** 후보 (지표 × 시차) 의 부분집합을 크기 상한까지 모두 열거하고,
     모형마다 칼만 주변우도를 낸다 — 계수 β 는 고유 사전 N(0, τ²)(표준화한 지표 한 sd 의 효과, τ = 설정 `계수사전sd`)을 단 상태로
     두므로 우도가 곧 그 모형의 주변우도다(분산은 ①에 고정 — 경험적 베이즈). 모형 사전은 후보마다 독립 포함 확률 π(`포함사전`) —
     π^k (1−π)^(K−k). 사후 모형 확률로 평균하고, 지표마다 **사후 포함 확률**(그 지표가 든 모형들의 사후 확률 합)을 낸다.
  ③ 평가기준일이 속한 회계연도의 남은 분기 매출을 모형 평균 예측분포(모형을 사후 확률로 뽑고 상태 · 잡음을 뽑는 모의 — 시드 고정)로
     내어 중앙값 · 90% 구간을 잡는다. 같은 모의로 Y+1 · Y+2 회계연도 매출 증가율의 90% 구간도 낸다(거친 바퀴 근거범위 후보).
  예측 거리가 지표의 시차보다 길면 그 지표의 미래 값은 변환 계열(로그 · 원값)의 AR(1)로 모의한다(마지막 값에 묶으면 지표의
  불확실성이 구간에서 사라진다). 평가기준일 뒤의 지표 값은 쓰지 않는다.
  날짜 둘(2026-10-25) — 분기 매출(재무 관측)의 끝은 재무기준일 F 의 분기(기준 분기 · 잔여 기간은 그 뒤 회계연도 끝까지)이고, 선행지표(시장 관측 —
  가격 · 지수)는 평가기준일 T 까지 **끝난** 분기의 실제 값을 예측 경로에 쓴다(T 뒤 값은 쓰지 않는다 · 적합은 기준 분기까지). 산출 `입력` 에
  평가기준일(T) · 재무기준일(F) · 지표끝분기가 남는다. F 가 없으면(옛 가정) 지금과 같다.
왜 있나 — 예측기간 규칙의 `잔여기간.py` 의 길 셋(전년 동기 · 누계 연장 · 금액)은 계절성과 단기 업황 전환이 겹치면 잔여 열 매출이 0 이하가 되거나
  연환산비가 튄다(⑮ 오류 · R-166 경보). 이 도구는 「계절 · 추세 · 선행지표가 말하는 잔여 기간」을 넷째 후보로 낸다 — 고르는 것은 사람이다.
**값을 정하지 않는다.** 잔여기간.py `--경로 금액` 에 넣을 금액 후보(비관 = 5% · 기준 = 중앙값 · 낙관 = 95%)와 명령을 적을 뿐이다.

사용
    python 스크립트/계절추세.py 가정.json                       # 가정 곁 _raw/ → _raw/계절추세.json
    python 스크립트/계절추세.py 가정.json --분기매출 분기.csv     # 열: 분기(또는 연도 + 분기) · 품목들 · 합계
    python 스크립트/계절추세.py 가정.json --지표 지표.csv         # 열: 분기 · 지표 이름들(선행지표 후보 — 거시 · 전방 · 가격)
    python 스크립트/계절추세.py 가정.json --구분별 아니오          # 합계만(기본: 합계 + 품목별)
    python 스크립트/계절추세.py 가정.json --엔진 아니오           # 잔여기간.상황(엔진) 대조를 건너뛴다

읽는 것 — 가정 곁 `_raw/`(`정상화.파일찾기` 차례)
    표현실현.json         실현매출(품목별 · 합계 분기 매출 — 연결 주석 「품목별 구분」) · 설정.결산월
    fx_USDKRW_일별.csv    원달러 일별(표현실현 캐시) — 분기 평균을 선행지표 후보로 쓴다
    가정 메타.평가기준일 · 기간.결산월 · 메타.금액단위 — 엔진이 돌면 `잔여기간.상황()` 으로 지금 가정의 잔여 기간 매출과 견준다
    (market_data 캐시는 평가기준일 한 점 값이라 분기 계열이 아니다 — 후보로 쓰지 않는다. 분기 계열은 `--지표` 로 준다)
내는 것 — `_raw/계절추세.json`
    {"형식": "계절추세 1", 만든날, 설정, 입력, 폴백, "계열": [{이름, 구분번호, 분기수, 모수, 모형수, 포함확률, 잔여기간, 연증가율, 분해, 자료길, 엔진대조}],
     "잔여기간": 합계 계열의 잔여기간(= 계열[0]), "제안": [...], "신호": [...]}
    잔여기간 = {"기준분기", "잔여분기", "누계", "추정", "평균", "90%": [lo, hi], "연환산비", "단위", "금액길": {"비관", "기준", "낙관"}(가정 단위),
               "환산율": {"비관", "기준", "낙관"}(엔진이 돌 때 — 회계연도 전년 대비), "명령"}
    신호 — 「길 ①~③ 과 길 ④ 가 크게 갈림」(90% 밖이면 경보 · 갈림문턱 넘으면 참고) · 「잔여 기간 매출 0 이하 위험」(경보) ·
           「포함 확률 높은 지표」 · 「구간이 넓다 — 추세 외삽」(위 ÷ 아래 > 넓음배율) · 「표본 부족」 · 「잔여 기간 없음」(참고)
추세 — 설정 `추세` = 반국소(기본 · 2026-10-23 밤 — BSTS semilocal: 기울기가 장기 기울기 D 로 φ 만큼 되돌아가 먼 예측이 덜 폭주한다. φ 는 우도로 잰다 ·
       Gardner–McKenzie 감쇠 추세와 같은 뜻) | 국소선형(기울기가 랜덤워크 — 끝 기울기를 그대로 밀어 낸다. 종전 기본 — 사이클 회사의 Y+1 · Y+2 가
       +120% 대로 나왔다). 그리고 국면 도구가 평가기준일을 정점 국면(정점문턱 이상)으로 보면 Y+1 · Y+2 증가율 제안을 내지 않고 잔여 기간만 낸다
폴백 — 분기 수 < 최소분기 → 길 ④ 를 내지 않는다(길 ① ② ③ 그대로) · 분기 수 < 지표최소분기 → 지표 없이 추세 · 계절만.
종료 코드 — 0 통과(경보가 있어도 — 값을 정하지 않는 도구다) · 2 입력오류
회사 · 업종 · 품목 · 지표 이름은 이 도구에 한 글자도 없다 — 품목은 표현실현 · 인자, 지표는 인자 · 캐시 파일 이름으로만 받는다.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import io
import itertools
import json
import math
import os
import random
import re
import statistics
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                            # noqa: BLE001
    pass

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 입력오류  # noqa: E402
import 상태공간 as 상  # noqa: E402 — 칼만 · 좌표 탐색 · 소행렬 · 파일 찾기를 한 벌로 쓴다

산출이름 = "계절추세.json"
단위배 = {"원": 1.0, "천원": 1e3, "백만원": 1e6, "십억원": 1e9, "억원": 1e8, "조원": 1e12}


def _수(x):
    return 상._수(x)


def _분기키(q):
    return 상.분기정렬키(q)


def _다음분기(q):
    y, n = _분기키(q)
    return "%dQ1" % (y + 1) if n == 4 else "%dQ%d" % (y, n + 1)


# ═════════════════════════════════════ 모형

def 틀(k, θ=None):
    """상태 = [l, b, s1, s2, s3, β1..βk(, D)] → (F, n). θ 에 「감쇠」(φ)가 있으면 반국소 추세 —
    b_{t+1} = D + φ (b_t − D) + ζ (BSTS semilocal linear trend · 기울기가 장기 기울기 D 로 되돌아간다), D 는 맨 끝 상태."""
    반 = bool(θ) and "감쇠" in θ
    n = 5 + k + (1 if 반 else 0)
    F = 상.영(n)
    F[0][0] = F[0][1] = 1.0
    if 반:
        φ = θ["감쇠"]
        F[1][1] = φ
        F[1][n - 1] = 1.0 - φ
        F[n - 1][n - 1] = 1.0
    else:
        F[1][1] = 1.0
    F[2][2] = F[2][3] = F[2][4] = -1.0
    F[3][2] = 1.0
    F[4][3] = 1.0
    for j in range(k):
        F[5 + j][5 + j] = 1.0
    return F, n


def _반국소(θ):
    return "감쇠" in θ


def 전이분산(θ, n):
    Q = 상.영(n)
    Q[0][0] = θ["수준sd"] ** 2
    Q[1][1] = θ["기울기sd"] ** 2
    Q[2][2] = θ["계절sd"] ** 2
    return Q


def 초기(y0, n, τ, 반=False):
    x0 = [0.0] * n
    x0[0] = y0
    P0 = 상.영(n)
    P0[0][0] = 1.0
    P0[1][1] = 0.04
    for i in (2, 3, 4):
        P0[i][i] = 0.04
    for i in range(5, n):
        P0[i][i] = τ * τ
    if 반:
        P0[n - 1][n - 1] = 0.04                          # 장기 기울기 D — 기울기와 같은 사전
    return x0, P0


def 관측(y, X, θ, n=None):
    """기간마다 [(h, y, r, None)] — X = 기간마다 [x_1..x_k](표준화). n 이 더 길면(반국소 D) 0 으로 채운다."""
    낸 = []
    for t, yt in enumerate(y):
        h = [1.0, 0.0, 1.0, 0.0, 0.0] + list(X[t])
        if n and len(h) < n:
            h += [0.0] * (n - len(h))
        낸.append([(h, yt, θ["관측sd"] ** 2, None)])
    return 낸


def 적합(y, X, θ, τ, 고르기=False):
    k = len(X[0]) if X else 0
    F, n = 틀(k, θ)
    x0, P0 = 초기(y[0], n, τ, _반국소(θ))
    return 상.칼만(관측(y, X if k else [[] for _ in y], θ, n), F, 전이분산(θ, n), x0, P0, 고르기=고르기), F, n


def 바탕분산(y, 설정, X=None, θ0=None):
    """분산 넷의 최대우도 — X 가 있으면 그 지표들을 상태(계수)로 넣은 채로 잰다(지표 효과를 수준 분산이 삼키지 않게)."""
    초 = 설정.get("초기") or {}
    θ0 = dict(θ0) if θ0 else {"수준sd": float(초.get("수준sd", 0.05)), "기울기sd": float(초.get("기울기sd", 0.01)),
                              "계절sd": float(초.get("계절sd", 0.02)), "관측sd": float(초.get("관측sd", 0.03))}
    if 설정.get("추세") == "반국소" and "감쇠" not in θ0:
        θ0["감쇠"] = float(초.get("감쇠", 0.8))
    범 = tuple((설정.get("범위") or {}).get("sd") or (0.0005, 1.0))
    범위 = {k: 범 for k in θ0}
    if "감쇠" in θ0:
        범위["감쇠"] = tuple((설정.get("범위") or {}).get("감쇠") or (0.05, 0.99))
    τ = float(설정.get("계수사전sd", 0.5))
    X = X if (X and X[0]) else []

    def 우도(θ):
        try:
            return 적합(y, X, θ, τ)[0]["로그우도"]
        except (ValueError, OverflowError, ZeroDivisionError):
            return -1e300
    return 상.좌표탐색(우도, θ0, 범위, 설정.get("탐색") or {})


# ═════════════════════════════════════ 재료

def 분기매출읽기(가정경로, 인자):
    """→ ({계열 이름: {분기: 값}}, 출처 글, 결산월) — 「합계」 계열이 맨 앞(없으면 품목 합)."""
    표, 표곳 = 상._파일("표현실현.json", 가정경로)
    계 = {}
    if 인자.get("분기매출"):
        계 = 상.분기매출CSV(인자["분기매출"])
        출 = "분기 매출 %s" % os.path.basename(인자["분기매출"])
    elif isinstance(표, dict) and 표.get("실현매출"):
        for v in 표["실현매출"]:
            for k, x in (v.get("값") or {}).items():
                if _수(x):
                    계.setdefault(k, {})[v["분기"]] = float(x)
            if _수(v.get("합계")):
                계.setdefault("합계", {})[v["분기"]] = float(v["합계"])
        출 = "표현실현 실현매출(%s)" % os.path.basename(표곳)
    else:
        return {}, "분기 매출 없음", 12
    if "합계" not in 계 and 계:
        모든 = set.intersection(*[set(d) for d in 계.values()])
        계["합계"] = {q: sum(d[q] for d in 계.values()) for q in 모든}
    return 계, 출, 상._결산월({}, 표)


def 지표읽기(가정경로, 인자, 결산월, 표곳=None):
    """→ {지표 이름: {분기: 값}}. 인자 CSV(열 = 지표) · 원달러 분기 평균(캐시가 있으면)."""
    낸 = {}
    if 인자.get("지표"):
        for r in csv.DictReader(io.open(인자["지표"], encoding="utf-8-sig")):
            q = (r.get("분기") or "").strip()
            if not re.fullmatch(r"\d{4}Q[1-4]", q):
                continue
            for k, v in r.items():
                if k == "분기":
                    continue
                x = _수(v)
                if x is not None:
                    낸.setdefault(k, {})[q] = x
    if 인자.get("환율", True) is not False:
        _표, 곳 = 상._파일("표현실현.json", 가정경로)
        d = os.path.dirname(곳) if 곳 else os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw")
        일별 = 상._환율일별(인자.get("환율곳") or os.path.join(d, "fx_USDKRW_일별.csv"))
        if 일별:
            해들 = sorted({k[:4] for k in 일별})
            for y in range(int(해들[0]), int(해들[-1]) + 2):
                for n in range(1, 5):
                    q = "%dQ%d" % (y, n)
                    v = 상._분기평균환율(일별, q, 결산월)
                    if v:
                        낸.setdefault("원달러(분기 평균)", {})[q] = v
    return 낸


def _두날(가정):
    """(재무기준일 F 글, 평가기준일 T 글) — `기준일.py` 로 푼다. F 가 없거나 날짜를 못 풀면 (메타.평가기준일 글, 같은 글) — 옛 길."""
    원 = ("%s" % ((가정.get("메타") or {}).get("평가기준일") or "")).strip()
    try:
        import 기준일 as _기                                  # noqa: PLC0415
        r = _기.기준일들(가정)
        if not r.get("오류") and not r.get("같음"):
            return r["재무기준일"], r["평가기준일"]
    except Exception:                                        # noqa: BLE001
        pass
    return 원, 원


def 기준분기(가정, 결산월, 분기들):
    """분기 매출의 기준 분기 — 재무 관측의 끝(재무기준일 F · 2026-10-25 날짜 둘. F 가 없으면 평가기준일 — 옛 길 그대로)."""
    기준일 = _두날(가정)[0]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", 기준일):
        return (분기들[-1] if 분기들 else None), 기준일
    y, m = int(기준일[:4]), int(기준일[5:7])
    try:
        import 표현실현 as X                                  # noqa: PLC0415
        후 = [q for q in 분기들 if X.분기달(q, 결산월)[-1] <= (y, m)]
    except Exception:                                        # noqa: BLE001
        후 = [q for q in 분기들 if (_분기키(q)[0], _분기키(q)[1] * 3) <= (y, m)]
    return (max(후, key=_분기키) if 후 else None), 기준일


def 지표끝분기(가정, 결산월, 분기들):
    """선행지표(시장 관측 — 가격 · 지수)의 끝 분기 — 평가기준일 T 까지 **끝난** 분기 가운데 가장 늦은 것(2026-10-25 날짜 둘).
    F 가 없으면(F = T) None — 지표도 기준 분기까지만 쓴다(옛 길 그대로). T 가 달 중간이면 그 달에 끝나는 분기는 아직 안 끝났다."""
    재, 평 = _두날(가정)
    if 재 == 평 or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", 평 or ""):
        return None
    t = datetime.date.fromisoformat(평)
    말일 = (t + datetime.timedelta(days=1)).month != t.month

    def 끝남(q):
        try:
            import 표현실현 as X                              # noqa: PLC0415
            ym = X.분기달(q, 결산월)[-1]
        except Exception:                                    # noqa: BLE001
            ym = (_분기키(q)[0], _분기키(q)[1] * 3)
        return ym < (t.year, t.month) or (ym == (t.year, t.month) and 말일)
    후 = [q for q in 분기들 if 끝남(q)]
    return max(후, key=_분기키) if 후 else None


# ═════════════════════════════════════ 한 계열

def 계열분석(이름, 계, 지표, 기준q, 설정, 엔진대조=None, 지표끝q=None):
    """한 분기 계열 → 결과 dict. 엔진대조 = {"단위배": 가정 단위로 나눌 수, "시나리오": {시: {"잔여매출", "누계", "전년"}}} 또는 None.
    지표끝q — 선행지표의 실제 값을 쓸 마지막 분기(평가기준일 T 까지 끝난 분기 · 2026-10-25 날짜 둘). None 이거나 기준 분기 이하면
    기준 분기까지(옛 길). 매출 관측과 적합은 언제나 기준 분기(재무기준일)까지다 — 기준 분기 뒤 · 지표끝q 까지의 지표 실제 값은 예측 경로에만 들어간다."""
    분기들 = sorted([q for q, v in 계.items() if v and v > 0 and _분기키(q) <= _분기키(기준q)], key=_분기키)
    # 끝(기준 분기)에서 거슬러 이어진 구간만
    이어 = []
    for q in reversed(분기들):
        if 이어 and _다음분기(q) != 이어[-1]:
            break
        이어.append(q)
    분기들 = list(reversed(이어))
    한 = {"이름": 이름, "분기수": len(분기들), "처음": 분기들[0] if 분기들 else None, "끝": 분기들[-1] if 분기들 else None}
    if len(분기들) < int(설정.get("최소분기", 8)) or 분기들[-1] != 기준q:
        한["폴백"] = "길 ④ 를 내지 않는다 — 기준 분기(%s)까지 이어진 분기가 %d개(최소 %s)" % (기준q, len(분기들), 설정.get("최소분기"))
        return 한
    y = [math.log(계[q]) for q in 분기들]
    θ, ll0, 평가 = 바탕분산(y, 설정)
    τ = float(설정.get("계수사전sd", 0.5))
    # 후보 — (지표, 시차): 표본 안 모든 분기에 값이 있어야 한다
    시차들 = [int(x) for x in (설정.get("시차") or [0, 1, 2, 3, 4])]
    L = max(시차들) if 시차들 else 0
    쓸지표 = len(분기들) >= int(설정.get("지표최소분기", 12))
    후보, 줄임 = [], None
    if 쓸지표 and 지표:
        idx = {q: i for i, q in enumerate(분기들)}
        # 분기 축은 빈칸 없이 잇는다 — 시차는 자리 차이로 재므로 지표에 빠진 분기가 있으면 어긋난다
        끝들 = sorted(set(q for d in 지표.values() for q in d) | set(분기들), key=_분기키)
        모든q = [끝들[0]]
        while _분기키(모든q[-1]) < _분기키(끝들[-1]):
            모든q.append(_다음분기(모든q[-1]))
        자리 = {q: i for i, q in enumerate(모든q)}
        for 지, d in sorted(지표.items()):
            양 = all(v > 0 for q, v in d.items() if _분기키(q) <= _분기키(기준q))       # 로그를 쓸지도 기준 분기까지의 값으로만 정한다
            for lag in 시차들:
                값 = []
                ok = True
                for q in 분기들[L:]:
                    i = 자리[q] - lag
                    if i < 0 or 모든q[i] not in d:
                        ok = False
                        break
                    v = d[모든q[i]]
                    값.append(math.log(v) if 양 else v)
                if not ok or len(값) < 3:
                    continue
                m, s = statistics.mean(값), statistics.pstdev(값)
                if s <= 0:
                    continue
                후보.append({"이름": "%s@%d" % (지, lag), "지표": 지, "시차": lag, "값": [(v - m) / s for v in 값], "평균": m, "sd": s, "양": 양,
                           "원": d, "모든q": 모든q, "자리": 자리})
        상한 = int(설정.get("후보상한", 8))
        if len(후보) > 상한:
            dy = [y[L + i] - y[L + i - 1] for i in range(1, len(y) - L)]

            def 상관(c):
                dx = [c["값"][i] - c["값"][i - 1] for i in range(1, len(c["값"]))]
                try:
                    return abs(statistics.correlation(dy, dx))
                except (statistics.StatisticsError, ValueError):
                    return 0.0
            후보.sort(key=상관, reverse=True)
            줄임 = "후보 %d개 → 차분 계열 단순상관 절댓값 상위 %d개만(설정 후보상한)" % (len(후보), 상한)
            후보 = 후보[:상한]
    표본y = y[L:] if 후보 else y
    표본q = 분기들[L:] if 후보 else 분기들
    if 후보:
        θ, ll0, 평가2 = 바탕분산(표본y, 설정)
        평가 += 평가2
    π = float(설정.get("포함사전", 0.2))
    K = len(후보)
    크기 = min(int(설정.get("모형크기상한", 3)), K)

    def X짓기(조):
        return [[후보[j]["값"][t] for j in 조] for t in range(len(표본y))] if 조 else [[] for _ in 표본y]

    def 평균(θ):
        목록 = []
        for k in range(0, 크기 + 1):
            for 조 in itertools.combinations(range(K), k):
                try:
                    R, _F, _n = 적합(표본y, X짓기(조), θ, τ)
                except (ValueError, OverflowError):
                    continue
                사전 = k * math.log(π) + (K - k) * math.log(1 - π) if K else 0.0
                목록.append({"조": 조, "로그우도": R["로그우도"], "로그사후": R["로그우도"] + 사전})
        최 = max(m["로그사후"] for m in 목록)
        합 = sum(math.exp(m["로그사후"] - 최) for m in 목록)
        for m in 목록:
            m["확률"] = math.exp(m["로그사후"] - 최) / 합
        return 목록
    모형들 = 평균(θ)
    # 경험적 베이즈 — 분산을 최고 사후 모형의 지표를 넣은 채 다시 재고(지표 효과를 수준 분산이 삼키지 않게), 모든 모형에 같은 분산으로 다시 평균한다
    분산돌림 = []
    for _돌 in range(2):
        최고 = max(모형들, key=lambda m: m["확률"])["조"]
        if not 최고:
            break
        θ2, ll2, 평가3 = 바탕분산(표본y, 설정, X짓기(최고), θ)
        평가 += 평가3
        분산돌림.append({"최고모형": [후보[j]["이름"] for j in 최고], "모수": {k: round(v, 5) for k, v in θ2.items()}})
        if all(abs(math.log(θ2[k] / θ[k])) < 0.05 for k in θ):
            θ = θ2
            모형들 = 평균(θ)
            break
        θ = θ2
        모형들 = 평균(θ)
    포함 = {c["이름"]: round(sum(m["확률"] for m in 모형들 if j in m["조"]), 4) for j, c in enumerate(후보)}
    # ── 모의
    시드 = int(설정.get("시드", 42))
    수 = int(설정.get("모의수", 4000))
    rng = random.Random(시드)
    기y, 기n = _분기키(기준q)
    잔여 = 4 - 기n
    H = 잔여 + 8
    미래q = []
    q = 기준q
    for _ in range(H):
        q = _다음분기(q)
        미래q.append(q)
    뽑 = [0] * len(모형들)
    누적 = list(itertools.accumulate(m["확률"] for m in 모형들))
    for _ in range(수):
        u = rng.random()
        뽑[next((i for i, c in enumerate(누적) if u <= c), len(모형들) - 1)] += 1
    잔합, 다음합, 다다음합 = [], [], []
    누계 = sum(계[q] for q in 분기들 if _분기키(q)[0] == 기y)
    # 미래 지표 — 예측 거리가 시차보다 길면 그 지표의 미래 값은 변환 계열(로그 또는 원값)의 AR(1)로 모의한다.
    # 마지막 값에 묶으면 지표의 불확실성이 구간에서 사라진다. 평가기준일 뒤 지표 값은 쓰지 않는다(있어도).
    지표AR = {}
    for c in 후보:
        if c["지표"] in 지표AR:
            continue
        기i = c["자리"][기준q]
        끝i = 기i
        if 지표끝q and 지표끝q in c["자리"] and _분기키(지표끝q) > _분기키(기준q):     # 날짜 둘 — T 까지 끝난 분기의 실제 값은 쓴다
            끝i = c["자리"][지표끝q]
            while 끝i > 기i and c["원"].get(c["모든q"][끝i]) is None:
                끝i -= 1
        v = []
        for i in range(0, 끝i + 1):
            w = c["원"].get(c["모든q"][i])
            if w is not None:
                v.append(math.log(w) if c["양"] else w)
        if len(v) >= 4:
            μ = statistics.mean(v)
            d0, d1 = [a - μ for a in v[:-1]], [a - μ for a in v[1:]]
            den = sum(a * a for a in d0)
            φ = max(min(sum(a * b for a, b in zip(d0, d1)) / den, 0.99), -0.99) if den > 0 else 0.0
            e = [b - φ * a for a, b in zip(d0, d1)]
            σ = statistics.pstdev(e) if len(e) > 1 else 0.0
        else:
            μ, φ, σ = (v[-1] if v else 0.0), 1.0, 0.0
        끝값 = c["원"].get(c["모든q"][끝i])
        지표AR[c["지표"]] = {"μ": μ, "φ": φ, "σ": σ, "끝": ((math.log(끝값) if c["양"] else 끝값) if 끝값 is not None else (v[-1] if v else 0.0))}
        if 끝i > 기i:
            지표AR[c["지표"]]["앞"] = 끝i - 기i                 # 기준 분기 뒤 실제 값이 있는 분기 수(모의는 그 뒤부터)
    for mi, 개수 in enumerate(뽑):
        if not 개수:
            continue
        조 = 모형들[mi]["조"]
        X = [[후보[j]["값"][t] for j in 조] for t in range(len(표본y))] if 조 else [[] for _ in 표본y]
        R, F, n = 적합(표본y, X, θ, τ)
        xT, PT = R["x거름"][-1], R["P거름"][-1]
        L_ = 상.촐레스키(PT)
        Qd = [θ["수준sd"], θ["기울기sd"], θ["계절sd"]]
        # 예측 거리 h(1..H) 마다 후보의 변환 값 — 기준 분기 안이면 실제 값, 밖이면 None(모의)
        고정 = []
        for h in range(1, H + 1):
            줄 = []
            for j in 조:
                c = 후보[j]
                기i = c["자리"][기준q]
                끝i = 기i + 지표AR[c["지표"]].get("앞", 0)          # 날짜 둘 — T 까지의 실제 값(없으면 기준 분기까지 · 옛 길)
                i = 기i + h - c["시차"]
                if i <= 끝i:
                    w = c["원"].get(c["모든q"][i])
                    줄.append(None if w is None else (math.log(w) if c["양"] else w))
                else:
                    줄.append(None)
            고정.append(줄)
        쓴지표 = sorted({후보[j]["지표"] for j in 조})
        for _ in range(개수):
            z = [rng.gauss(0, 1) for _ in range(n)]
            x = [a + sum(L_[i][k] * z[k] for k in range(n)) for i, a in enumerate(xT)]
            길 = {}
            for 지 in 쓴지표:
                ar = 지표AR[지]
                w, 낸 = ar["끝"], []
                for _h in range(H):
                    w = ar["μ"] + ar["φ"] * (w - ar["μ"]) + ar["σ"] * rng.gauss(0, 1)
                    낸.append(w)
                길[지] = 낸
            값들 = []
            for h in range(H):
                x = 상.곱벡(F, x)
                x[0] += rng.gauss(0, Qd[0])
                x[1] += rng.gauss(0, Qd[1])
                x[2] += rng.gauss(0, Qd[2])
                회귀 = 0.0
                for jj, j in enumerate(조):
                    c = 후보[j]
                    vv = 고정[h][jj]
                    if vv is None:
                        앞 = 지표AR[c["지표"]].get("앞", 0)
                        k = h - c["시차"] - 앞                 # 모의는 실제 값의 끝(기준 분기 + 앞)에서 시작한다
                        vv = 길[c["지표"]][k if (k >= 0 or not 앞) else 0]   # 기준 분기에서 (h + 1 − 시차) 걸음 뒤의 모의 값
                    회귀 += x[5 + jj] * (vv - c["평균"]) / c["sd"]
                yy = x[0] + x[2] + 회귀 + rng.gauss(0, θ["관측sd"])
                값들.append(math.exp(min(yy, 700)))
            잔합.append(sum(값들[:잔여]))
            다음합.append(sum(값들[잔여:잔여 + 4]))
            다다음합.append(sum(값들[잔여 + 4:잔여 + 8]))

    def 분위(목록, p):
        s = sorted(목록)
        if not s:
            return None
        i = min(max(int(round(p * (len(s) - 1))), 0), len(s) - 1)
        return s[i]
    포괄 = float(설정.get("포괄", 0.9))
    a, b = (1 - 포괄) / 2, 1 - (1 - 포괄) / 2
    한.update({"모수": {k: round(v, 5) for k, v in θ.items()}, "바탕로그우도": round(ll0, 3), "우도평가": 평가, "분산돌림": 분산돌림,
              "후보": [{"이름": c["이름"], "지표": c["지표"], "시차": c["시차"]} for c in 후보], "후보줄임": 줄임,
              "모형수": len(모형들), "포함확률": 포함,
              "최고모형": [후보[j]["이름"] for j in max(모형들, key=lambda m: m["확률"])["조"]] if 모형들 else [],
              "지표사용": bool(후보), "지표안씀까닭": None if 후보 else ("분기 %d개 < 지표최소분기 %s" % (len(분기들), 설정.get("지표최소분기")) if not 쓸지표
                                                                else "쓸 수 있는 지표 후보가 없다(표본 분기 전부에 값이 있는 지표 · 시차 없음)"),
              "미래지표_AR1": {지: {k: round(v, 4) for k, v in ar.items()} for 지, ar in 지표AR.items()}})
    if 잔여 == 0:
        한["잔여기간"] = {"기준분기": 기준q, "잔여분기": [], "까닭": "기준 분기가 회계연도 끝이다 — 잔여 기간이 없다"}
    else:
        med, lo, hi = 분위(잔합, 0.5), 분위(잔합, a), 분위(잔합, b)
        누개, 잔개 = 기n * 3, 잔여 * 3
        한["잔여기간"] = {"기준분기": 기준q, "잔여분기": 미래q[:잔여], "누계": 누계, "추정": med, "평균": statistics.mean(잔합),
                        "90%": [lo, hi], "연환산비": (med / 잔개) / (누계 / 누개) if 누계 else None, "단위": 설정.get("분기매출단위")}
        # 자료만으로 낸 길 ①' · ②'
        전q = ["%dQ%d" % (기y - 1, k) for k in range(1, 5)]
        if all(q in 계 for q in 전q):
            전누 = sum(계[q] for q in 전q[:기n])
            전잔 = sum(계[q] for q in 전q[기n:])
            한["자료길"] = {"전년동기(누계 증가율 그대로)": 전잔 * (누계 / 전누) if 전누 else None, "전년동기(g = 0)": 전잔,
                         "누계연장(g = 0)": 누계 * 잔개 / 누개, "_뜻": "잔여기간.py 길 ① ② 를 분기 자료만으로 낸 대조값(엔진 · 가정 율 없이)"}
    올해 = [누계 + s for s in 잔합] if 잔여 else [누계] * len(다음합)
    g1 = [n_ / t_ - 1 for n_, t_ in zip(다음합, 올해) if t_]
    g2 = [n2 / n1 - 1 for n2, n1 in zip(다다음합, 다음합) if n1]
    한["연증가율"] = {"Y+1": {"해": 기y + 1, "중앙": 분위(g1, 0.5), "90%": [분위(g1, a), 분위(g1, b)]},
                   "Y+2": {"해": 기y + 2, "중앙": 분위(g2, 0.5), "90%": [분위(g2, a), 분위(g2, b)]}}
    # 분해 — 최고 모형의 스무딩
    try:
        mi = max(range(len(모형들)), key=lambda i: 모형들[i]["확률"])
        조 = 모형들[mi]["조"]
        X = [[후보[j]["값"][t] for j in 조] for t in range(len(표본y))] if 조 else [[] for _ in 표본y]
        R, _F, _n = 적합(표본y, X, θ, τ, 고르기=True)
        분 = []
        for t, q in enumerate(표본q[-8:], start=len(표본q) - min(8, len(표본q))):
            xs = R["x"][t]
            회귀 = sum(b * xv for b, xv in zip(xs[5:], X[t]))
            분.append({"분기": q, "추세": round(math.exp(xs[0]), 1), "계절배수": round(math.exp(xs[2]), 4),
                      "회귀배수": round(math.exp(회귀), 4), "잔차": round(표본y[t] - xs[0] - xs[2] - 회귀, 4)})
        한["분해"] = 분
        b, vb = R["x"][-1][1], max(R["P"][-1][1][1], 0.0) ** 0.5
        z = 1.6448536269514722
        한["끝기울기"] = {"분기": math.exp(b) - 1, "90%": [math.exp(b - z * vb) - 1, math.exp(b + z * vb) - 1],
                       "_뜻": "기준 분기 끝의 분기 기울기(로그 매출의 분기 변화 · 최고 모형 스무딩) — 추세가 밀어 내는 속도"}
    except (ValueError, OverflowError):
        한["분해"] = []
    # 엔진 대조
    if 엔진대조 and 한.get("잔여기간", {}).get("추정") is not None:
        배 = 엔진대조["단위배"]
        r = 한["잔여기간"]
        r["금액길"] = {"비관": r["90%"][0] / 배, "기준": r["추정"] / 배, "낙관": r["90%"][1] / 배}
        r["가정단위"] = 엔진대조.get("단위")
        환 = {}
        for 시, d in 엔진대조["시나리오"].items():
            N, F_ = d.get("누계"), d.get("전년")
            if N is not None and F_:
                환[시] = (N + r["금액길"][시]) / F_ - 1
        r["환산율"] = 환
        한["엔진대조"] = {시: {"지금잔여매출": d.get("잔여매출"), "길4": r["금액길"]["기준"],
                          "90%안": (d.get("잔여매출") is not None and r["90%"][0] / 배 <= d["잔여매출"] <= r["90%"][1] / 배)}
                       for 시, d in 엔진대조["시나리오"].items()}
    return 한


# ═════════════════════════════════════ 엔진 대조 재료

def 엔진사정(가정, 가정경로, 계, 기준q, 설정):
    """잔여기간.상황() — 지금 가정의 잔여 기간 매출(시나리오별 · 구분별)과 단위배. 못 돌면 None."""
    try:
        import 잔여기간                                     # noqa: PLC0415
        사 = 잔여기간.상황(가정, 가정경로)
    except Exception as e:                                   # noqa: BLE001
        return None, "잔여기간.상황 을 못 돌렸다 — %s" % (("%s" % e)[:120])
    if not 사:
        return None, "가정에 잔여 기간 열이 없다(평가기준일이 회계연도 끝이거나 기간 축이 없다)"
    가단 = ("%s" % ((가정.get("메타") or {}).get("금액단위") or "")).strip()
    우단 = 설정.get("분기매출단위") or "백만원"
    if 가단 in 단위배 and 우단 in 단위배:
        배 = 단위배[가단] / 단위배[우단]
    else:
        배 = None
    # 단위 검산 — 엔진 누계(기준) ÷ 분기 자료 누계
    기y, 기n = _분기키(기준q)
    합 = 계.get("합계") or {}
    우누 = sum(합.get("%dQ%d" % (기y, k), 0) for k in range(1, 기n + 1))
    엔누 = (사["시나리오"].get("기준") or {}).get("누계")
    if 엔누 and 우누:
        비 = 우누 / 엔누
        if 배 is None or abs(비 / 배 - 1) > 0.02:
            로 = math.log10(비) if 비 > 0 else None
            if 로 is not None and abs(로 - round(로)) < 0.01:
                배 = 10 ** round(로)
            else:
                return None, "단위가 안 맞는다 — 분기 자료 누계 %s ÷ 엔진 누계 %s = %.4f" % (우누, 엔누, 비)
    if 배 is None:
        return None, "가정 금액단위(%s)와 분기 자료 단위(%s)를 맞출 수 없다" % (가단, 우단)
    return {"단위배": 배, "단위": 가단, "사정": 사}, None


def 명령짓기(이름, 번호, g, 금, 사정):
    """잔여기간.py 가 받는 꼴일 때만 명령 → (명령 · None, 까닭 · None).
    잔여기간.py 규약 — 구분별 누계 회차면 `--경로 금액` 이 증가율 구분 **마다** 그 금액을 적으므로 합계 금액은 구분 명령으로 갈라야 하고,
    구분별 누계가 없는 회차는 `--구분` 을 받지 않는다. 수준 · 합계 경로 구분은 환산하지 않는다(그 구분의 잔여 기간은 수준 값이 정한다)."""
    별 = bool(사정.get("구분별누계"))
    증 = sorted(s for s, v in (사정.get("구분") or {}).items() if (v or {}).get("경로") == "증가율")
    if 이름 == "합계":
        if 사정.get("구분") is not None and not 증:
            return None, "증가율 경로 구분이 없다(잔여기간.py 가 환산할 줄이 없다 — 잔여 기간은 수준 · 합계 값이 정한다)"
        if 별:
            return None, "구분별 누계 회차라 합계 금액을 한 번에 적을 수 없다(잔여기간.py 는 증가율 구분마다 금액을 적는다 — 구분 명령을 쓴다)"
        return ("python 스크립트/잔여기간.py 가정.json --경로 금액 --금액 \"비관=%.0f,기준=%.0f,낙관=%.0f\" --적기" % (금["비관"], 금["기준"], 금["낙관"])), None
    if not 별:
        return None, "구분별 누계가 없는 회차라 잔여기간.py 가 --구분 을 받지 않는다"
    경 = (g or {}).get("경로") or ((사정.get("구분") or {}).get(번호) or {}).get("경로")
    if 경 != "증가율":
        return None, "%s 경로 구분이라 잔여기간.py 가 환산하지 않는다(잔여 기간은 수준 값이 정한다)" % (경 or "모르는")
    return ("python 스크립트/잔여기간.py 가정.json --구분 \"%s=금액:비관=%.0f,기준=%.0f,낙관=%.0f\" --적기" % (번호, 금["비관"], 금["기준"], 금["낙관"])), None


# ═════════════════════════════════════ 실행

def 실행(가정, 가정경로, 인자=None, 설정=None):
    인자 = 인자 or {}
    설 = (설정 or 상.설정읽기())["계절추세"]
    결과 = {"형식": "계절추세 1", "만든날": datetime.date.today().isoformat(),
          "설정": {"파일": "상태공간설정.json", **{k: 설.get(k) for k in ("추세", "최소분기", "지표최소분기", "시차", "후보상한", "모형크기상한", "포함사전",
                                                                     "계수사전sd", "포괄", "모의수", "시드", "갈림문턱", "포함확률문턱", "넓음배율")}},
          "입력": {}, "폴백": None, "계열": [], "잔여기간": None, "제안": [], "신호": []}
    신호 = 결과["신호"]

    def 알림(종류, 대상, 값, 문턱, 글, 등급="참고"):
        신호.append({"출처": "계절추세", "종류": 종류, "대상": 대상, "값": 값, "문턱": 문턱, "글": 글, "등급": 등급})

    계, 출, 결산월 = 분기매출읽기(가정경로, 인자)
    결산월 = int(((가정.get("기간") or {}).get("결산월")) or 결산월)
    if not 계:
        결과["폴백"] = "길 ④ 없음 — 분기 매출이 없다(표현실현 실현매출 · --분기매출). 잔여기간.py 길 ① ② ③ 그대로"
        알림("표본 부족", "전체", 0, 설.get("최소분기"), 결과["폴백"])
        return 결과
    지표 = 지표읽기(가정경로, 인자, 결산월)
    모든q = sorted(set(q for d in 계.values() for q in d), key=_분기키)
    기q, 기준일 = 기준분기(가정, 결산월, 모든q)
    결과["입력"] = {"분기매출": 출, "지표": sorted(지표), "결산월": 결산월, "평가기준일": 기준일, "기준분기": 기q}
    재글, 평글 = _두날(가정)
    지끝q = None
    if 재글 != 평글:                                          # 2026-10-25 날짜 둘 — 매출은 F 까지 · 선행지표 실제 값은 T 까지 끝난 분기까지
        결과["입력"]["평가기준일"] = 평글
        결과["입력"]["재무기준일"] = 재글
        지끝q = 지표끝분기(가정, 결산월, sorted(set(q for d in 지표.values() for q in d) | set(모든q), key=_분기키))
        결과["입력"]["지표끝분기"] = 지끝q
    if 기q is None:
        결과["폴백"] = "길 ④ 없음 — %s(%s) 이전 분기 자료가 없다" % ("평가기준일" if 재글 == 평글 else "재무기준일", 기준일)
        알림("표본 부족", "전체", 0, 설.get("최소분기"), 결과["폴백"])
        return 결과
    엔, 엔까닭 = (None, "--엔진 아니오") if 인자.get("엔진") is False else 엔진사정(가정, 가정경로, 계, 기q, 설)
    결과["입력"]["엔진대조"] = "했다" if 엔 else ("안 했다 — %s" % 엔까닭)
    구분들 = 상._구분들(가정)
    이름들 = ["합계"] + ([k for k in sorted(계) if k not in ("합계", "기타")] if 인자.get("구분별", True) else [])
    for 이름 in 이름들:
        if 이름 not in 계:
            continue
        대조 = None
        g = None if 이름 == "합계" else 상._구분찾기(이름, 구분들)
        if 엔:
            사 = 엔["사정"]
            if 이름 == "합계":
                대조 = {"단위배": 엔["단위배"], "단위": 엔["단위"],
                      "시나리오": {시: {"잔여매출": d.get("잔여매출"), "누계": d.get("누계"), "전년": d.get("전년")} for 시, d in 사["시나리오"].items()}}
            elif g:
                대조 = {"단위배": 엔["단위배"], "단위": 엔["단위"],
                      "시나리오": {시: {"잔여매출": (d.get("구분사정") or {}).get(g["번호"], {}).get("잔여매출"),
                                     "누계": (d.get("구분사정") or {}).get(g["번호"], {}).get("누계"),
                                     "전년": (d.get("구분사정") or {}).get(g["번호"], {}).get("전년")} for 시, d in 사["시나리오"].items()}}
        r = 계열분석(이름, 계[이름], 지표, 기q, 설, 대조, 지끝q)
        r["구분번호"] = g["번호"] if g else None
        결과["계열"].append(r)
        if r.get("폴백"):
            알림("표본 부족", 이름, r["분기수"], 설.get("최소분기"), "%s — %s(폴백 — 잔여기간 길 ① ② ③ 그대로)" % (이름, r["폴백"]))
            continue
        if not r.get("지표사용"):
            알림("표본 부족", 이름, r["분기수"], 설.get("지표최소분기"), "%s — 선행지표 없이 추세 · 계절만으로 냈다(%s)" % (이름, r.get("지표안씀까닭")))
        for k, p in sorted(r["포함확률"].items(), key=lambda kv: -kv[1]):
            if p >= float(설.get("포함확률문턱", 0.5)):
                알림("포함 확률 높은 지표", "%s · %s" % (이름, k), p, 설.get("포함확률문턱"),
                   "%s — 선행지표 「%s」 의 사후 포함 확률 %.2f. 근거 칸에 이 지표와 시차를 적을 수 있다" % (이름, k, p))
        잔 = r.get("잔여기간") or {}
        if not 잔.get("잔여분기"):
            알림("잔여 기간 없음", 이름, 0, None, "%s — %s" % (이름, 잔.get("까닭") or "잔여 기간이 없다"))
            continue
        딱 = "[계산 — 구조 시계열(계절 · 추세 · 선행지표: %s)]" % (", ".join("%s %.2f" % kv for kv in sorted(r["포함확률"].items(), key=lambda kv: -kv[1])[:3]) or "없음")
        넓 = bool(잔.get("90%") and 잔["90%"][0] and 잔["90%"][1] / 잔["90%"][0] > float(설.get("넓음배율", 2.0)))
        if 넓:
            끝 = r.get("끝기울기") or {}
            알림("구간이 넓다 — 추세 외삽", 이름, round(잔["90%"][1] / 잔["90%"][0], 3), 설.get("넓음배율"),
               "%s — 잔여 기간 90%% 구간의 위 ÷ 아래가 %.2f배다. 기준 분기 끝 기울기(분기 %.1f%%)를 밀어 낸 구간이라 사이클 꺾임은 담지 않는다 — 길 ④ 는 근거범위로만 본다"
               % (이름, 잔["90%"][1] / 잔["90%"][0], (끝.get("분기") or 0) * 100))
        if 잔.get("금액길"):
            금 = 잔["금액길"]
            명령, 명까닭 = 명령짓기(이름, r.get("구분번호"), g, 금, (엔 or {}).get("사정") or {})
            if 명령:
                잔["명령"] = 명령
            else:
                잔["명령까닭"] = 명까닭
            결과["제안"].append({"자리": "잔여기간 길 ④ — %s %s" % (이름, "·".join(잔["잔여분기"])), "값": 금["기준"], "근거범위": [금["비관"], 금["낙관"]],
                              "딱지": 딱, "확신": "보통" if (r.get("지표사용") and not 넓) else "약", "명령": 명령,
                              "글": "잔여 기간 매출 중앙값 %.0f · 90%% [%.0f, %.0f](%s) · 연환산비 %.2f · 회계연도 환산율 %s%s" % (
                                  금["기준"], 금["비관"], 금["낙관"], 잔.get("가정단위") or "", 잔.get("연환산비") or 0,
                                  " · ".join("%s %.1f%%" % (시, v * 100) for 시, v in (잔.get("환산율") or {}).items()),
                                  "" if 명령 else " · 명령 없음 — %s(지금 가정과 견주는 대조값으로만 쓴다)" % 명까닭)})
            for 시, d in (r.get("엔진대조") or {}).items():
                지금 = d.get("지금잔여매출")
                if 지금 is None:
                    continue
                if 지금 <= 0:
                    알림("잔여 기간 매출 0 이하 위험", "%s %s" % (이름, 시), 지금, 0,
                       "%s %s — 지금 가정의 잔여 기간 매출이 %.0f(0 이하)다. 길 ④ 는 %.0f [%.0f, %.0f] 를 낸다 — 잔여기간.py 로 길을 고른다"
                       % (이름, 시, 지금, 금["기준"], 금["비관"], 금["낙관"]), "경보")
                elif not d["90%안"]:
                    알림("길 ①~③ 과 길 ④ 가 크게 갈림", "%s %s" % (이름, 시), 지금, [금["비관"], 금["낙관"]],
                       "%s %s — 지금 가정의 잔여 기간 매출 %.0f 이 길 ④ 의 90%% 구간 [%.0f, %.0f] 밖이다. 고른 길의 근거를 적거나 길을 다시 고른다"
                       % (이름, 시, 지금, 금["비관"], 금["낙관"]), "경보" if 시 == "기준" else "참고")
                elif abs(지금 / 금["기준"] - 1) > float(설.get("갈림문턱", 0.25)):
                    알림("길 ①~③ 과 길 ④ 가 크게 갈림", "%s %s" % (이름, 시), round(지금 / 금["기준"] - 1, 4), 설.get("갈림문턱"),
                       "%s %s — 지금 가정의 잔여 기간 매출이 길 ④ 중앙값과 %.0f%% 갈린다(구간 안)" % (이름, 시, (지금 / 금["기준"] - 1) * 100))
        else:
            결과["제안"].append({"자리": "잔여기간 길 ④ — %s %s" % (이름, "·".join(잔["잔여분기"])), "값": 잔.get("추정"), "근거범위": 잔.get("90%"),
                              "딱지": 딱, "확신": "약", "글": "가정 단위로 옮기지 못해 분기 자료 단위(%s)로 적었다 — %s" % (잔.get("단위"), 엔까닭)})
        y1 = r["연증가율"]["Y+1"]
        정점 = 정점확률(가정경로)                      # 2026-10-23 밤 — 사이클 정점이면 추세 외삽으로 Y+1 · Y+2 를 내지 않는다(03 4-7)
        if 정점 and 정점[0] >= 정점[1]:
            r["연증가율"]["생략"] = "평가기준일 정점 국면 확률 %.2f ≥ %.2f — 추세를 밀어 낸 연 증가율은 사이클 꺾임을 담지 않는다" % 정점
            알림("정점 국면 — 연 증가율 제안 생략", 이름, round(정점[0], 3), 정점[1],
               "%s — 국면 도구가 평가기준일을 정점 국면(확률 %.2f)으로 본다. Y+1 · Y+2 매출 증가율 근거범위를 내지 않고 잔여 기간만 낸다" % (이름, 정점[0]))
        elif y1.get("90%") and y1["90%"][0] is not None:
            결과["제안"].append({"자리": "거친바퀴 — %s Y+1(%s) · Y+2(%s) 매출 증가율 근거범위" % (이름, y1["해"], r["연증가율"]["Y+2"]["해"]),
                              "값": {"Y+1": y1["중앙"], "Y+2": r["연증가율"]["Y+2"]["중앙"]},
                              "근거범위": {"Y+1": y1["90%"], "Y+2": r["연증가율"]["Y+2"]["90%"]}, "딱지": 딱, "확신": "약",
                              "글": "구조 시계열 예측분포의 90% 구간 — 추세를 밀어 낸 것이라 사이클 꺾임은 담지 않는다(근거범위 후보이지 값이 아니다)"})
    합 = next((x for x in 결과["계열"] if x["이름"] == "합계"), None)
    결과["잔여기간"] = (합 or {}).get("잔여기간")
    if not [x for x in 결과["계열"] if not x.get("폴백")]:
        결과["폴백"] = "길 ④ 없음 — 모든 계열이 표본 부족(잔여기간.py 길 ① ② ③ 그대로)"
    return 결과


def 계절추세읽기(가정경로):
    """가정 곁 `_raw/계절추세.json` → dict 또는 None(잔여기간 · 거친바퀴가 부른다)."""
    d, _p = 상._파일("계절추세.json", 가정경로)
    return d if isinstance(d, dict) else None


def 길넷(가정경로, 구분=None):
    """잔여기간.py 문항의 선택지 꼴 하나 — {"이름", "경로": "금액", "율", "값"(기준 환산율), "잔여매출", "90%", "금액", "명령", "명령까닭"} 또는 None.
    명령 = None 이면 잔여기간.py 가 그 꼴을 받지 않는 자리다(명령까닭) — 대조값으로만 보인다.
    구분 = None 이면 합계 계열, 번호면 그 구분 계열."""
    d = 계절추세읽기(가정경로)
    if not d:
        return None
    계 = next((x for x in d.get("계열") or [] if (구분 is None and x.get("이름") == "합계") or (구분 is not None and x.get("구분번호") == 구분)), None)
    잔 = (계 or {}).get("잔여기간") or {}
    if not 잔.get("금액길"):
        return None
    return {"이름": "구조 시계열 — 계절 · 추세 · 선행지표(길 ④)", "경로": "금액", "율": None, "값": (잔.get("환산율") or {}).get("기준"),
            "잔여매출": 잔["금액길"]["기준"], "90%": [잔["금액길"]["비관"], 잔["금액길"]["낙관"]], "금액": 잔["금액길"], "명령": 잔.get("명령"), "명령까닭": 잔.get("명령까닭"),
            "포함확률": 계.get("포함확률")}


def 정점확률(가정경로):
    """국면 도구의 평가기준일 정점 확률과 그 도구의 정점문턱 → (p, 문턱) · 국면 산출이 없으면 None."""
    try:
        import 국면 as 국                                     # noqa: PLC0415
        import 정상화                                         # noqa: PLC0415
        t = 국.국면읽기(가정경로)
        if not t or t.get("폴백"):
            return None
        p = ((t.get("평가기준일국면") or {}) or {}).get("정점")
        if p is None:
            return None
        j, _ = 정상화.파일찾기(국.산출이름, 가정경로)
        문 = float(((j or {}).get("설정") or {}).get("정점문턱") or 0.7)
        return float(p), 문
    except Exception:                                # noqa: BLE001
        return None


def 근거범위(가정경로, 구분=None):
    """거친바퀴 — Y+1 · Y+2 매출 증가율 90% 구간 {"Y+1": {"해", "중앙", "90%"}, "Y+2": …, "딱지"} 또는 None(정점 국면이라 생략한 계열도 None)."""
    d = 계절추세읽기(가정경로)
    if not d:
        return None
    계 = next((x for x in d.get("계열") or [] if (구분 is None and x.get("이름") == "합계") or (구분 is not None and x.get("구분번호") == 구분)), None)
    if not 계 or not 계.get("연증가율") or 계["연증가율"].get("생략"):
        return None
    return dict(계["연증가율"], 딱지="[계산 — 구조 시계열 예측분포 90%(계절 · 추세 · 선행지표)]")


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="계절추세 — 구조 시계열 · 선행지표 모형 평균(기법 8)")
    ap.add_argument("가정")
    ap.add_argument("--분기매출")
    ap.add_argument("--지표")
    ap.add_argument("--환율")
    ap.add_argument("--구분별", default="예", choices=["예", "아니오"])
    ap.add_argument("--엔진", default="예", choices=["예", "아니오"])
    ap.add_argument("--설정")
    ap.add_argument("--낼")
    a = ap.parse_args(argv)
    try:
        가정 = json.load(io.open(a.가정, encoding="utf-8"))
        설 = 상.설정읽기(a.설정)
        for k in ("분기매출", "지표", "환율"):
            p = getattr(a, k)
            if p and not os.path.exists(p):
                raise IOError("%s 파일이 없다: %s" % (k, p))
    except (OSError, ValueError) as e:
        print("계절추세 입력 오류 — %s" % e)
        return 입력오류
    결과 = 실행(가정, a.가정, {"분기매출": a.분기매출, "지표": a.지표, "환율곳": a.환율, "구분별": a.구분별 == "예", "엔진": a.엔진 == "예"}, 설)
    낼 = a.낼 or os.path.join(os.path.dirname(os.path.abspath(a.가정)), "_raw", "계절추세.json")
    os.makedirs(os.path.dirname(낼), exist_ok=True)
    io.open(낼, "w", encoding="utf-8").write(json.dumps(결과, ensure_ascii=False, indent=1))
    잔 = 결과.get("잔여기간") or {}
    print("계절추세 — 계열 %d · 제안 %d · 신호 %d%s → %s" % (len(결과["계열"]), len(결과["제안"]), len(결과["신호"]),
                                                     (" · 폴백: " + 결과["폴백"]) if 결과.get("폴백") else "", 낼))
    if 잔.get("추정") is not None:
        print("  합계 잔여 %s — 중앙 %.0f · 90%% [%.0f, %.0f] · 연환산비 %.2f" % ("·".join(잔.get("잔여분기") or []), 잔["추정"], 잔["90%"][0], 잔["90%"][1],
                                                                       잔.get("연환산비") or 0))
    return 통과


if __name__ == "__main__":
    sys.exit(main())

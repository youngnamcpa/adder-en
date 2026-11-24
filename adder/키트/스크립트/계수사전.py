# -*- coding: utf-8 -*-
"""계수사전 — 두 패널(KR DART 일괄 · US SEC FSDS)에서 **연동 계수의 산업 사전**(산업 2자리 × 계수)을 내고, 대상 회사의 자체 추정을 Vasicek 수축으로
당겨 가정 칸과 대 본다 (2026-10-23 · 연구/동인연동_업그레이드_연구.md P4 · R6 계수 추정 설계표).

    python 스크립트/계수사전.py 가정.json                          # → 가정 곁 _raw/계수사전.json · 표를 찍는다
    python 스크립트/계수사전.py 가정.json --국가 US --회사 0000001750
    python 스크립트/계수사전.py --사전만 --국가 KR --산업 26          # 가정 없이 산업 사전 한 벌만 찍는다

계수 열(`계수사전설정.json` 이 정본) — 비용 반응 β1 · 하방 경직성 β2(판관비 · 매출원가 — ABJ 2003 Model I) · 증분 Sales-to-Capital · Net CapEx/매출 · CapEx/상각 ·
  잔존연수 · 회전일수 반응 δ · 수익성 평균 회귀 λ. 모두 패널의 본표 열(매출액 · 매출원가 · 영업이익 · 유형자산 · 매출채권 · 재고자산 · 매입채무 · CAPEX · 감가상각비)에서만 낸다.
사전의 꼴 — 산업코드(KSIC2 · SIC2 — 회사가 모자라면 「전체」로 올라간다 · 계층) × 계수 × {N_기업 · N_기업연도 · μ(중앙값) · 평균 · τ²(강건 회사 간 분산 − 중앙값 표준오차² · 하한 0.1 × 강건분산 — 2026-10-23 밤) ·
  Q1 · Q3 · P5 · P95 · 자료창}. 회사 계수는 (점추정 · 표준오차 · n)으로 두고, **적용값 = w · 회사 + (1 − w) · 산업, w = τ² ÷ (τ² + se²)** (Vasicek 1973 꼴 —
  수축.py 의 경험적 베이즈와 같은 식이고 사전이 동종(C2) 대신 패널 산업이다). w 를 같이 내 「회사 자료가 얼마나 말했나」를 읽게 한다.
신호(값을 정하지 않는다) — 가정 칸(859 Sales-to-Capital · 156 상각률 = 1 ÷ 잔존연수의 역수)이 산업 분포의 꼬리 밖(경보) · 사분위 밖(참고) · 산업 β2 가 유의하게 음수인데
  키트 E 식(Δln 비용 = a + b Δln 매출 — 대칭)으로 비용을 세웠다(참고 — 하락 시나리오에서 비용을 실제보다 많이 깎는다) · 회전일수가 시나리오 · 열에 한 값인데 산업의
  호황 · 불황 국면값이 다르다(참고) · 표본 부족 · 대상 식별 못함(참고).
수축.py 연결 — `사전가져오기(국가, 산업코드, 기능)` 가 동종(C2) 사전이 없을 때의 폴백 사전({평균 · 분산 · 평균분산 · 회사수 · 방식})을 준다.
물리 범위 · 노출(레터 v27 P11 · F5 · 2026-11-10) — 잔존연수 1년 미만(상각률 100% 초과) 회사 값은 사전 · 회사 추정에서 뺀다. 제안 값이 칸의 정의역
  (감가상각률 0~1 · Sales-to-Capital 0 초과) 밖이면 근거범위를 비우고(손잡이로 쓰지 않는다) 끝만 넘으면 자른다(`근거범위_원값`). 제안마다 `싣기가능`
  (산업 사전 30곳 미만 · 업종 부적합이면 false · `안싣는까닭`) — 레터는 false 인 제안을 「업종 값」 으로 싣지 않는다. 산출 머리에 `업종적합`(기저율.업종적합).
규칙 — 회사 · 업종 이름이 코드에 없다. 패널이 없으면 「해당 없음」(종전과 같다). 종료 코드 — 0 경보 없음 · 1 경보 있음 · 2 입력 오류.
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import math
import os
import statistics
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass
여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류           # noqa: E402
import 기저율 as 기                                  # noqa: E402

설정경로 = os.path.join(여기, "계수사전설정.json")
출처이름 = "계수사전"
형식 = "계수사전 1"
# 레터 v27 P11 · F5(2026-11-10) — 물리 범위 · 노출 문턱(설정 「극단.연수하한」 · 「노출」 이 있으면 그 값)
연수하한 = 1.0                                       # 잔존연수 하한(년) — 상각률 = 1 ÷ 잔존연수 가 1(100%)을 넘는 회사 값은 사전 · 회사 추정에서 뺀다
물리범위 = {"156": (0.0, 1.0), "859": (0.0, None)}   # 가정 칸의 정의역 — 감가상각률 0~1 · Sales-to-Capital 0 초과(그 밖의 제안은 싣지 않는다)
노출최소기업 = 30                                    # 산업 사전의 회사 수가 이보다 적으면 「업종 값」 으로 싣지 않는다(F5)


def 설정읽기(p=None):
    return json.load(io.open(p or 설정경로, encoding="utf-8"))


def _수(v):
    try:
        return None if v is None else float(v)
    except (TypeError, ValueError):
        return None


# ────────────────────────────────────────────────────────────── 작은 통계

def 회귀(xs, ys):
    """최소제곱 y = a + b x → (a, b, se_b, n) · n < 3 이거나 분산 0 이면 None."""
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 1e-12:
        return None
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    a = my - b * mx
    s2 = sum((y - a - b * x) ** 2 for x, y in zip(xs, ys)) / (n - 2) if n > 2 else 0.0
    return a, b, math.sqrt(s2 / sxx), n


def 비대칭회귀(쌍):
    """ABJ Model I — y = β0 + β1 x + β2 D x (D = x < 0). → {β1, se1, β2, se2, n, 하락쌍} 또는 None(쌍 셋 미만 · 특이)."""
    n = len(쌍)
    if n < 3:
        return None
    X = [[1.0, x, x if x < 0 else 0.0] for x, _ in 쌍]
    y = [v for _, v in 쌍]
    하락 = sum(1 for x, _ in 쌍 if x < 0)
    k = 3 if 하락 >= 1 and 하락 < n else 2
    if k == 2:
        X = [r[:2] for r in X]
    XtX = [[sum(r[i] * r[j] for r in X) for j in range(k)] for i in range(k)]
    Xty = [sum(r[i] * v for r, v in zip(X, y)) for i in range(k)]
    inv = _역행렬(XtX)
    if inv is None:
        return None
    β = [sum(inv[i][j] * Xty[j] for j in range(k)) for i in range(k)]
    잔 = [v - sum(b * r[i] for i, b in enumerate(β)) for r, v in zip(X, y)]
    df = n - k
    s2 = (sum(e * e for e in 잔) / df) if df > 0 else 0.0
    se = [math.sqrt(max(0.0, s2 * inv[i][i])) for i in range(k)]
    return {"β1": β[1], "se1": se[1], "β2": (β[2] if k == 3 else None), "se2": (se[2] if k == 3 else None), "n": n, "하락쌍": 하락}


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


def 분위(xs, q):
    v = sorted(x for x in xs if x is not None)
    if not v:
        return None
    i = (len(v) - 1) * q
    lo, hi = int(math.floor(i)), int(math.ceil(i))
    return v[lo] + (v[hi] - v[lo]) * (i - lo)


# ────────────────────────────────────────────────────────────── 회사 하나의 계수

def 로그쌍(해들, 분자, 분모, 최소변동):
    """이어진 해의 (Δln 분모, Δln 분자) — 둘 다 양수 · |Δln 분모| ≥ 최소변동."""
    쌍 = []
    for y0, y1 in zip(해들, 해들[1:]):
        if y1 - y0 != 1:
            continue
        a0, a1, b0, b1 = 분자.get(y0), 분자.get(y1), 분모.get(y0), 분모.get(y1)
        if None in (a0, a1, b0, b1) or min(a0, a1, b0, b1) <= 0:
            continue
        dx = math.log(b1 / b0)
        if abs(dx) < 최소변동:
            continue
        쌍.append((dx, math.log(a1 / a0)))
    return 쌍


def 회사계수(해행, S):
    """{연도: 행} → {계수이름: {"값", "se", "n", "쌍"?}} — 낼 수 있는 것만. 쌍(로그 차분)도 돌려준다(산업 풀 회귀용)."""
    해들 = sorted(해행)
    매 = {y: _수(r.get("매출액")) for y, r in 해행.items()}
    원 = {y: _수(r.get("매출원가")) for y, r in 해행.items()}
    영 = {y: _수(r.get("영업이익")) for y, r in 해행.items()}
    유 = {y: _수(r.get("유형자산")) for y, r in 해행.items()}
    cx = {y: _수(r.get("CAPEX")) for y, r in 해행.items()}
    dp = {y: _수(r.get("감가상각비")) for y, r in 해행.items()}
    채 = {y: _수(r.get("매출채권")) for y, r in 해행.items()}
    판관 = {y: (매[y] - 원[y] - 영[y]) if None not in (매[y], 원[y], 영[y]) else None for y in 해들}
    낸 = {}
    극 = S["극단"]
    최소쌍 = S["최소"]["쌍_회사"]
    for 이름, 분자 in (("SGA", 판관), ("COGS", 원)):
        쌍 = 로그쌍(해들, 분자, 매, S["최소변동"])
        낸["쌍_" + 이름] = 쌍
        r = 비대칭회귀(쌍) if len(쌍) >= 최소쌍 else None
        b1 = ("β1_SGA" if 이름 == "SGA" else "b_COGS")
        b2 = ("β2_SGA" if 이름 == "SGA" else "β2_COGS")
        if r and abs(r["β1"]) <= 극["탄력성"]:
            낸[b1] = {"값": r["β1"], "se": r["se1"], "n": r["n"]}
            if r["β2"] is not None and r["하락쌍"] >= S["최소"]["하락쌍_회사"] and abs(r["β2"]) <= 극["탄력성"]:
                낸[b2] = {"값": r["β2"], "se": r["se2"], "n": r["n"], "하락쌍": r["하락쌍"]}
    # 증분 Sales-to-Capital — 3해 창
    s2c = []
    for y in 해들:
        y0 = y - 3
        if y0 in 해행 and None not in (매.get(y), 매.get(y0), 유.get(y), 유.get(y0)) and 매[y] > 매[y0] and 유[y] > 유[y0]:
            v = (매[y] - 매[y0]) / (유[y] - 유[y0])
            if 0 < v <= 극["S2C"]:
                s2c.append(v)
    _평균se(낸, "S2C_incr", s2c)
    # 비율 셋
    ncs, cd, life, dso = [], [], [], {}
    for y in 해들:
        if None not in (cx.get(y), dp.get(y), 매.get(y)) and 매[y] > 0:
            v = (abs(cx[y]) - abs(dp[y])) / 매[y]
            if abs(v) <= 극["비율"]:
                ncs.append(v)
        if None not in (cx.get(y), dp.get(y)) and dp[y] and abs(dp[y]) > 0:
            v = abs(cx[y]) / abs(dp[y])
            if v <= 극["비율"] * 10:
                cd.append(v)
        if None not in (유.get(y), dp.get(y)) and dp[y] and abs(dp[y]) > 0 and 유[y] > 0:
            v = 유[y] / abs(dp[y])
            if 극.get("연수하한", 연수하한) <= v <= 극["연수"]:          # 레터 v27 P11 — 잔존연수 1년 미만(상각률 100% 초과)은 분모 정의가 다른 값(유형자산 ÷ 감가상각 · 무형상각 합)이다
                life.append(v)
        if None not in (채.get(y), 매.get(y)) and 매[y] > 0 and 채[y] is not None and 채[y] >= 0:
            dso[y] = 채[y] / 매[y] * 365
    _평균se(낸, "NetCapEx_Sales", ncs)
    _평균se(낸, "CapEx_Dep", cd)
    _평균se(낸, "잔존연수", life)
    # δ_DSO — ΔDSO 대 g (회사 수준은 쌍만 — 산업 풀 회귀용)
    δ쌍 = []
    for y0, y1 in zip(해들, 해들[1:]):
        if y1 - y0 == 1 and y0 in dso and y1 in dso and 매.get(y0) and 매.get(y1) and 매[y0] > 0:
            δ쌍.append(((매[y1] / 매[y0]) - 1, dso[y1] - dso[y0]))
    낸["쌍_DSO"] = δ쌍
    r = 회귀([x for x, _ in δ쌍], [v for _, v in δ쌍]) if len(δ쌍) >= 최소쌍 else None
    if r:
        낸["δ_DSO"] = {"값": r[1], "se": r[2], "n": r[3]}
    # λ_π 재료 — (π_t, π_t+1) 쌍(산업 중앙값은 산업 쪽에서 뺀다)
    π = {y: (영[y] / 매[y]) for y in 해들 if 매.get(y) and 매[y] > 0 and 영.get(y) is not None}
    낸["π"] = π
    낸["회전일수"] = {y: {"178": dso.get(y)} for y in 해들}
    for y in 해들:
        if 원.get(y) and 원[y] > 0:
            재 = _수(해행[y].get("재고자산"))
            매입 = _수(해행[y].get("매입채무"))
            낸["회전일수"][y]["182"] = (재 / 원[y] * 365) if 재 is not None and 재 >= 0 else None
            낸["회전일수"][y]["186"] = (매입 / 원[y] * 365) if 매입 is not None and 매입 >= 0 else None
    return 낸


def _평균se(낸, 이름, xs):
    if len(xs) >= 2:
        m = statistics.mean(xs)
        sd = statistics.stdev(xs)
        낸[이름] = {"값": m, "se": sd / math.sqrt(len(xs)) if sd > 0 else 1e-9, "n": len(xs), "중앙값": statistics.median(xs)}
    elif len(xs) == 1:
        낸[이름] = {"값": xs[0], "se": None, "n": 1, "중앙값": xs[0]}


# ────────────────────────────────────────────────────────────── 산업 사전

def 산업사전(회사들, S, 이름="", 산업중앙값π=None):
    """회사들 = {고유번호: 회사계수(...)} → {계수: {N_기업 · N_기업연도 · μ · 평균 · τ² · Q1 · Q3 · P5 · P95 · 방식}} + 풀 회귀(β1 · β2 · δ · λ)."""
    사전 = {}
    for 계수 in ("S2C_incr", "NetCapEx_Sales", "CapEx_Dep", "잔존연수", "β1_SGA", "b_COGS", "δ_DSO"):
        값들 = [(c[계수]["값"], c[계수].get("se")) for c in 회사들.values() if 계수 in c and c[계수].get("값") is not None]
        if len(값들) < S["최소"]["회사_산업"]:
            continue
        v = [x for x, _ in 값들]
        평균 = statistics.mean(v)
        분산 = statistics.variance(v) if len(v) > 1 else 0.0
        se들 = sorted(s for _, s in 값들 if s)
        τ2, 강건, 원τ2, 바닥 = 이질성(v, se들, S)
        사전[계수] = {"N_기업": len(v), "N_기업연도": sum(c[계수].get("n") or 0 for c in 회사들.values() if 계수 in c),
                   "μ": statistics.median(v), "평균": 평균, "τ²": τ2, "표본분산": 분산, "강건분산": 강건, "τ²_원값": 원τ2, "τ²_하한적용": 바닥,
                   "se_하한": 분위(se들, (S.get("수축") or {}).get("se하한분위", 0.10)) if se들 else None,
                   "Q1": 분위(v, 0.25), "Q3": 분위(v, 0.75), "P5": 분위(v, 0.05), "P95": 분위(v, 0.95),
                   "방식": "회사 추정의 분포(강건 모멘트 — τ² = (1.4826·MAD)² − 중앙값 se² · 하한 0.1 × 강건분산)"}
    # 풀 회귀 — 비대칭(산업 전체 쌍) · δ · λ
    for 이름2, 키, b1, b2 in (("SGA", "쌍_SGA", "β1_SGA", "β2_SGA"), ("COGS", "쌍_COGS", "b_COGS", "β2_COGS")):
        쌍 = [p for c in 회사들.values() for p in c.get(키, [])]
        r = 비대칭회귀(쌍) if len(쌍) >= S["최소"]["회사연도_산업"] else None
        if r:
            사전.setdefault(b1, {}).update({"풀_β1": r["β1"], "풀_se1": r["se1"], "풀_n": r["n"], "풀_하락쌍": r["하락쌍"]})
            if r["β2"] is not None and r["하락쌍"] >= S["최소"]["하락쌍_산업"]:
                사전[b2] = {"풀_β2": r["β2"], "풀_se2": r["se2"], "풀_n": r["n"], "풀_하락쌍": r["하락쌍"],
                          "하락반응": r["β1"] + r["β2"], "유의": abs(r["β2"]) > 1.6449 * r["se2"] if r["se2"] else False,
                          "N_기업": len([c for c in 회사들.values() if c.get(키)]), "방식": "산업 풀 회귀(ABJ Model I)"}
    δ쌍 = [p for c in 회사들.values() for p in c.get("쌍_DSO", [])]
    r = 회귀([x for x, _ in δ쌍], [v for _, v in δ쌍]) if len(δ쌍) >= S["최소"]["회사연도_산업"] else None
    if r:
        사전.setdefault("δ_DSO", {}).update({"풀_δ1": r[1], "풀_se": r[2], "풀_n": r[3]})
    # λ_π — Huber(π_t+1 − π_t) ~ (π_t − 산업 중앙값_t)
    if 산업중앙값π:
        xs, ys = [], []
        for c in 회사들.values():
            π = c.get("π") or {}
            for y in sorted(π):
                if y + 1 in π and y in 산업중앙값π and abs(π[y]) <= 1 and abs(π[y + 1]) <= 1:
                    xs.append(π[y] - 산업중앙값π[y])
                    ys.append(π[y + 1] - π[y])
        if len(xs) >= S["최소"]["회사연도_산업"]:
            ab = 기.huber(xs, ys)
            if ab:
                사전["λ_π"] = {"λ": ab[1], "절편": ab[0], "N_기업연도": len(xs), "반감햇수": (math.log(0.5) / math.log(1 + ab[1])) if -1 < ab[1] < 0 else None,
                            "방식": "Huber 회귀(산업 중앙값 편차)"}
    for k in 사전:
        사전[k]["집단"] = 이름
    return 사전




# ────────────────────────────────────────────────────────────── 수축 · 가정 대조

def 이질성(v, se들, S=None):
    """회사 간 이질성 τ² — 강건 모멘트(2026-10-23 밤 · 연구/레터워크북_최적화_20261023/03 4-2).
    종전 τ² = max(0, 표본분산 − 평균 se²) 는 꼬리가 두꺼운 회사 se 의 평균 하나가 분산 전체를 넘어 τ² = 0(w = 0 — 회사 자료 무시)이 되거나,
    se 가 0 에 가까운 비율 계수에서 w = 1(산업 무시)로 갈렸다 — 수축이 아니라 「둘 중 하나 고르기」.
    지금 — 강건분산 = (1.4826 · MAD)²(정규에서 표준편차와 같은 자 · Rousseeuw–Croux 1993) · τ² = 강건분산 − 중앙값 se² ·
    하한 = 0.1 × 강건분산(이질성 0 은 판정이 아니라 추정 실패로 본다 — DerSimonian–Laird 의 0 절단을 막는 하한 · REML · Paule–Mandel 은 대안).
    → (τ², 강건분산, 원값, 하한적용)."""
    if len(v) < 2:
        return 0.0, 0.0, 0.0, False
    m = statistics.median(v)
    mad = statistics.median([abs(x - m) for x in v])
    강건 = (1.4826 * mad) ** 2
    if 강건 <= 0:                                     # 절반 넘게 같은 값 — 표본분산으로 물러선다
        강건 = statistics.variance(v)
    중se2 = statistics.median([s * s for s in se들]) if se들 else 0.0
    원 = 강건 - 중se2
    하 = ((S or {}).get("수축") or {}).get("τ²하한배", 0.1) * 강건
    return (max(원, 하), 강건, 원, 원 < 하)


def 수축(회사값, 회사se, 사전, z):
    """Vasicek — w = τ² ÷ (τ² + se²). 회사 se 가 없으면 w = 0(산업 그대로). → {w · 적용값 · 구간}.
    회사 se 는 산업 회사 se 의 10분위(`se_하한`)보다 작게 두지 않는다 — 짧은 시계열의 아주 작은 se 가 w = 1(산업 무시)을 만들지 않게(03 4-2 ③)."""
    μ, τ2 = 사전["μ"], 사전["τ²"]
    if 회사값 is None or not 회사se:
        return {"w": 0.0, "적용값": μ, "구간": [사전["Q1"], 사전["Q3"]], "까닭": "회사 추정 없음 — 산업 중앙값 · 사분위"}
    바닥 = 사전.get("se_하한")
    if 바닥 and 회사se < 바닥:
        회사se = 바닥
    s2 = 회사se * 회사se
    w = τ2 / (τ2 + s2) if (τ2 + s2) > 0 else 0.0
    m = w * 회사값 + (1 - w) * μ
    sd = math.sqrt(τ2 * s2 / (τ2 + s2)) if (τ2 + s2) > 0 else 0.0
    return {"w": w, "적용값": m, "구간": [m - z * sd, m + z * sd]}


def 가정값(가정, 번호):
    """기준 시나리오 첫 예측 열 값(열별) 또는 한 값. 없으면 None."""
    v = (가정.get("가정") or {}).get(번호)
    if isinstance(v, dict):
        벌 = v.get("기준") if "기준" in v else v.get("공통")
        if isinstance(벌, dict):
            for k, x in 벌.items():
                if k != "TV" and isinstance(x, (int, float)) and not isinstance(x, bool):
                    return float(x)
    v = (가정.get("시점가정") or {}).get(번호)
    if isinstance(v, dict):
        v = v.get("기준") if "기준" in v else v.get("공통")
    return _수(v) if isinstance(v, (int, float)) else None


def 한값인가(가정, 번호):
    v = (가정.get("가정") or {}).get(번호)
    if not isinstance(v, dict):
        return False
    값들 = []
    for 벌 in v.values():
        if isinstance(벌, dict):
            값들 += [x for k, x in 벌.items() if isinstance(x, (int, float)) and not isinstance(x, bool)]
    return len(값들) >= 2 and len(set(값들)) == 1


# ────────────────────────────────────────────────────────────── 조립

def 분석(가정, 가정경로, 설정=None, 회사=None, 국가=None, 자리=None, 산업지정=None):
    S = 설정 or 설정읽기()
    기설 = 기.설정읽기()
    국, 기설, 까 = 기.국가맞춤(가정 or {"메타": {"표시통화": "KRW"}}, 기설, 국가)
    if not 국:
        return 기.해당없음(형식, 가정경로 or "", 까, S, 출처이름), ""
    행, 패널입력 = 기.패널읽기(자리, 기설)
    if not 행:
        return 기.해당없음(형식, 가정경로 or "", "%s 패널이 비었다(%s)" % (국, 패널입력["자리"]), S, 출처이름), ""
    남, 뺀 = 기.자료제외(행, 기설)
    끝해 = max(r["연도"] for r in 남)
    창 = {y for y in range(끝해 - S["창"]["연수"] + 1, 끝해 + 1)}
    넓은 = 기.넓히기([r for r in 남 if r["연도"] in 창])
    신호 = []

    def 신(종류, 대상, 값, 문턱, 글, 등급="참고"):
        신호.append({"출처": 출처이름, "종류": 종류, "대상": 대상, "값": 값, "문턱": 문턱, "글": 글, "등급": 등급})

    # 대상
    고, 산업, 까 = (None, 산업지정, "") if 가정 is None else 기.대상찾기(가정, 가정경로, 행, 회사, 기설)
    if 산업지정:
        산업 = 산업지정
    대상 = {"고유번호": 고, "회사명": ((가정 or {}).get("메타") or {}).get("회사명"), "국가": 국, "산업분류": 산업,
          "산업2": 산업[:2] if 산업 and len(산업) >= 2 else None, "식별": "" if (고 or 산업지정) else 까}
    if 가정 is not None and not 고:
        신("대상 식별 못함", "대상", None, None, "대상 고유번호를 못 찾았다(%s) — 전체 사전만 낸다" % 까)
    업종 = 기.업종적합(가정경로, {"국가": 국, "산업분류": 산업, "KSIC2": 대상["산업2"]}, 기설, 패널입력["자리"]) if 가정경로 else None   # 레터 v27 F1
    # 회사 계수 전부
    회사계수들 = {c: 회사계수(d["해"], S) for c, d in 넓은.items()}
    # 산업 중앙값 π(해마다 · 집단별)
    def 중앙π(집):
        낸 = {}
        해별 = {}
        for c in 집:
            for y, v in (회사계수들[c].get("π") or {}).items():
                해별.setdefault(y, []).append(v)
        for y, v in 해별.items():
            낸[y] = statistics.median(v)
        return 낸
    전체집 = [c for c in 넓은 if c != 고]
    사전 = {"전체": 산업사전({c: 회사계수들[c] for c in 전체집}, S, "전체", 중앙π(전체집))}
    계층 = "전체"
    if 대상["산업2"]:
        집 = [c for c in 전체집 if 넓은[c]["KSIC2"] == 대상["산업2"]]
        if len(집) >= S["최소"]["회사_산업"]:
            사전["산업2"] = 산업사전({c: 회사계수들[c] for c in 집}, S, "%s %s" % (기설.get("_산업분류"), 대상["산업2"]), 중앙π(집))
            사전["산업2"]["_회사수"] = len(집)
            계층 = "산업2"
        else:
            신("표본 부족", "산업 %s" % 대상["산업2"], len(집), S["최소"]["회사_산업"], "산업 2자리에 회사 %d곳(최소 %d) — 전체(국가) 사전으로 올라간다" % (len(집), S["최소"]["회사_산업"]))
    쓸사전 = {k: v for k, v in 사전[계층].items() if not k.startswith("_")}
    # 국면값 — 산업 중앙값 성장률 부호
    국면 = _국면값(넓은, 전체집 if 계층 == "전체" else [c for c in 전체집 if 넓은[c]["KSIC2"] == 대상["산업2"]], S)
    # 회사 · 수축
    회사 = 회사계수들.get(고) if 고 else None
    수축결과 = {}
    z = S["수축"]["z"]
    for 계수 in ("S2C_incr", "NetCapEx_Sales", "CapEx_Dep", "잔존연수", "β1_SGA", "b_COGS", "δ_DSO"):
        사 = 쓸사전.get(계수)
        if not 사 or 사.get("μ") is None:
            continue
        자 = (회사 or {}).get(계수)
        r = 수축(자["값"] if 자 else None, (자 or {}).get("se"), 사, z)
        r.update({"회사": ({"값": 자["값"], "se": 자.get("se"), "n": 자.get("n")} if 자 else None), "산업": {"μ": 사["μ"], "τ²": 사["τ²"], "Q1": 사["Q1"], "Q3": 사["Q3"], "N_기업": 사["N_기업"], "집단": 사["집단"]},
                  "se_하한적용": bool(자 and 자.get("se") and 사.get("se_하한") and 자["se"] < 사["se_하한"])})
        수축결과[계수] = r
        if 사.get("τ²_하한적용"):
            신("이질성 추정 0", 계수, 사.get("τ²_원값"), 사["τ²"],
              "같은 집단(%s · %d곳)의 %s 회사 간 차이가 표준오차에 묻혀 이질성이 0 으로 추정됐다 — 하한(강건분산의 10%%)으로 두고 수축했다. 산업 값에 가깝게 당긴 것은 자료가 아니라 하한 때문일 수 있다"
              % (사["집단"], 사["N_기업"], 계수))
    # 가정 칸 대조 — 859 · 156
    제안 = []
    if 가정 is not None:
        대조 = [("859", "S2C_incr", False, "Sales-to-Capital"), ("156", "잔존연수", True, "감가상각률(= 1 ÷ 잔존연수)")]
        for 번, 계수, 역수, 이름 in 대조:
            v = 가정값(가정, 번)
            사 = 쓸사전.get(계수)
            if v is None or not 사:
                continue
            비교값 = (1.0 / v) if (역수 and v) else v
            꼬 = S["꼬리"]
            if 사["P5"] is not None and (비교값 < 사["P5"] or 비교값 > 사["P95"]):
                신("가정 칸이 산업 꼬리 밖", "A-%s" % 번, v, [사["P5"], 사["P95"]],
                  "%s(A-%s) %s 가 같은 집단(%s · %d곳)의 %s 분포 %.3g~%.3g(5~95%%) 밖이다 — 까닭을 근거 칸에 적는다(값은 바꾸지 않는다)"
                  % (이름, 번, ("%.4g" % v), 사["집단"], 사["N_기업"], 계수, 사["P5"], 사["P95"]), "경보")
            elif 사["Q1"] is not None and (비교값 < 사["Q1"] or 비교값 > 사["Q3"]):
                신("가정 칸이 산업 사분위 밖", "A-%s" % 번, v, [사["Q1"], 사["Q3"]],
                  "%s(A-%s) %s 가 같은 집단 %s 사분위 %.3g~%.3g 밖(꼬리 안)" % (이름, 번, ("%.4g" % v), 계수, 사["Q1"], 사["Q3"]))
            r = 수축결과.get(계수)
            if r:
                적 = (1.0 / r["적용값"]) if (역수 and r["적용값"]) else r["적용값"]
                x제 = {"자리": "A-%s" % 번, "값": 적, "근거범위": sorted([(1.0 / x) if (역수 and x) else x for x in r["구간"] if x]),
                      "딱지": "[계산 — 패널 산업 사전 %s(%d곳) · Vasicek w %.2f%s]" % (r["산업"]["집단"], r["산업"]["N_기업"], r["w"], " · 회사 추정 없음" if not r.get("회사") else ""),
                      "글": "%s 제안 %.4g — 회사 %s · 산업 중앙값 %.4g · w %.2f(회사 자료가 말한 몫)" % (이름, 적, ("%.4g" % ((1.0 / r["회사"]["값"]) if (역수 and r["회사"]["값"]) else r["회사"]["값"])) if r.get("회사") else "없음",
                                                                          (1.0 / r["산업"]["μ"]) if (역수 and r["산업"]["μ"]) else r["산업"]["μ"], r["w"])}
                제안문(x제, 번, 이름, r, 계층, 업종, S, 신)
                제안.append(x제)
        # 비대칭 — 산업 β2 가 유의하게 음수
        for 키, 줄 in (("β2_SGA", "판관비"), ("β2_COGS", "매출원가")):
            사 = 쓸사전.get(키)
            if 사 and 사.get("유의") and 사["풀_β2"] < 0:
                신("하방 경직성", 줄, 사["풀_β2"], 0,
                  "같은 집단(%s)의 %s 는 매출이 1%% 줄 때 %.2f%% 만 준다(오를 때 %.2f%% — β2 %.2f · 유의). 키트 E 식(Δln 비용 = a + b Δln 매출)은 대칭이라 하락 시나리오에서 비용을 실제보다 많이 깎는다 — 비관의 마진을 근거 칸에서 다시 본다(P2 ㄷ)"
                  % (사["집단"], 줄, 사["하락반응"], 사["하락반응"] - 사["풀_β2"], 사["풀_β2"]))
        # 국면값 — 회전일수가 한 값인데 호황 · 불황이 다르다
        for 번 in ("178", "182", "186"):
            if 한값인가(가정, 번) and 국면 and 국면.get(번) and 국면[번].get("호황") and 국면[번].get("불황"):
                h, l = 국면[번]["호황"], 국면[번]["불황"]
                if h and l and abs(h - l) / max(h, l) > 0.1:
                    신("운전자본 국면값", "A-%s" % 번, 가정값(가정, 번), [h, l],
                      "A-%s 가 시나리오 · 열에 한 값인데 같은 집단의 회전일수 중앙값은 호황 해 %.0f일 · 불황 해 %.0f일로 다르다 — 국면에 따라 가르는 것을 본다(㊺)" % (번, h, l))
    낸 = {"형식": 형식, "만든날": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "국가": 국, "패널": {"자리": 패널입력["자리"], "창": sorted(창), "회사": len(넓은), "제외": len(뺀)},
         "대상": 대상, "계층": 계층, "사전": 사전, "회사": {k: v for k, v in (회사 or {}).items() if not k.startswith("쌍_") and k not in ("π", "회전일수")},
         "수축": 수축결과, "국면값": 국면, "제안": 제안, "신호": 신호, "업종적합": 업종,
         "설정": {"창": S["창"]["연수"], "최소": S["최소"], "수축z": z, "꼬리": S["꼬리"]}}
    return 낸, ""


def 제안문(x, 번, 이름, r, 계층, 업종, S, 신):
    """레터 v27 P11 · F5 — 제안 하나에 물리 범위 거르개와 「싣기가능」 표지를 단다(제자리에서 고친다).
      물리 범위(`물리범위`) — 제안 값이 정의역 밖이면 싣지 않고 근거범위를 비운다(거친 바퀴 · 결합 민감도가 그 범위를 손잡이로 쓰지 않게 · 원값은 `근거범위_원값`).
        값은 안인데 근거범위 끝이 밖이면 정의역으로 자른다(`근거범위_원값` 에 옛 범위).
      노출 — 산업 사전이 회사 `노출최소기업` 곳 미만이거나 업종 부적합(`기저율.업종적합`)이면 `싣기가능: false`(숫자는 남긴다 — 레터가 「업종 값」 으로 싣지 않는다)."""
    노 = ((S or {}).get("노출") or {})
    lo, hi = 물리범위.get("%s" % 번, (None, None))
    까닭 = []
    v = x.get("값")

    def 안(t):
        return t is not None and (lo is None or t > lo) and (hi is None or t <= hi)
    if lo is not None or hi is not None:
        if not 안(v):
            x["근거범위_원값"], x["근거범위"] = x.get("근거범위"), None
            까닭.append("물리 범위 밖 — %s 제안 %.4g 가 정의역(%s ~ %s) 밖이다(분모 정의가 다른 값이 섞였을 수 있다)" % (
                이름, v if v is not None else float("nan"), "%.4g 초과" % lo if lo is not None else "−∞", ("%.4g" % hi) if hi is not None else "∞"))
            신("제안이 물리 범위 밖", "A-%s" % 번, v, [lo, hi], "%s — 근거범위를 비웠다(손잡이로 쓰지 않는다) · 레터에 싣지 않는다" % 까닭[-1])
        elif isinstance(x.get("근거범위"), list) and len(x["근거범위"]) == 2:
            a, b = x["근거범위"]
            if lo is not None and a <= lo:                       # 아래 끝이 정의역(초과) 밖 — 자르면 끝이 0(나눗셈 · 상각 0)이 된다. 범위를 쓰지 않는다
                x["근거범위_원값"], x["근거범위"] = [a, b], None
                신("제안 범위가 물리 범위 밖", "A-%s" % 번, [a, b], [lo, hi], "%s 근거범위 아래 끝 %.4g 가 %.4g 이하 — 근거범위를 비웠다(손잡이로 쓰지 않는다)" % (이름, a, lo))
            elif hi is not None and b > hi:                      # 위 끝만 넘으면 정의역 끝으로 자른다
                x["근거범위_원값"], x["근거범위"] = [a, b], ([a, hi] if hi - a > 1e-12 else None)
                신("제안 범위를 물리 범위로 자름", "A-%s" % 번, [a, b], [lo, hi], "%s 근거범위 %.4g~%.4g 의 위 끝을 %.4g 로 잘랐다" % (이름, a, b, hi))
    n기업 = (r.get("산업") or {}).get("N_기업") or 0
    최소 = int(노.get("산업사전_최소기업", 노출최소기업))
    if n기업 < 최소:
        까닭.append("산업 사전 회사 %d곳 — %d곳 미만이라 업종 값으로 싣지 않는다" % (n기업, 최소))
    if 계층 == "산업2" and isinstance(업종, dict) and 업종.get("적합") is False:
        까닭.append("업종 부적합 — %s" % (업종.get("까닭") or "대상 업종 분류가 핵심 표본의 업종과 엇갈린다"))
    x["싣기가능"] = not 까닭
    if 까닭:
        x["안싣는까닭"] = " · ".join(까닭)
    return x


def _국면값(넓은, 집, S):
    해별성장 = {}
    for c in 집:
        해 = 넓은[c]["해"]
        for y in sorted(해):
            if y - 1 in 해 and 해[y].get("매출액") and 해[y - 1].get("매출액"):
                해별성장.setdefault(y, []).append(해[y]["매출액"] / 해[y - 1]["매출액"] - 1)
    국면 = {y: ("호황" if statistics.median(v) >= 0 else "불황") for y, v in 해별성장.items() if len(v) >= 5}
    낸 = {}
    for 번, 식 in S["국면값"]["칸"].items():
        분자, 나머지 = 식.split("/")
        분모 = 나머지.split("*")[0]
        값 = {"호황": [], "불황": []}
        for c in 집:
            for y, r in 넓은[c]["해"].items():
                if y not in 국면 or not r.get(분모) or r[분모] <= 0 or r.get(분자) is None or r[분자] < 0:
                    continue
                값[국면[y]].append(r[분자] / r[분모] * 365)
        낸[번] = {k: (statistics.median(v) if len(v) >= 30 else None) for k, v in 값.items()}
        낸[번]["해"] = {str(y): g for y, g in 국면.items()}
    return 낸


def 사전가져오기(국가, 산업코드, 기능, 설정=None):
    """수축.py 의 폴백 — 동종(C2) 사전이 없을 때 패널 산업 사전({평균 · 분산 · 평균분산 · 회사수 · 방식}). 없으면 None."""
    S = 설정 or 설정읽기()
    기설 = 기.설정읽기()
    try:
        국, 기설, _ = 기.국가맞춤({"메타": {"표시통화": "USD" if 국가 == "US" else "KRW"}}, 기설, 국가)
        낸, _ = 분석(None, None, S, 국가=국, 산업지정=산업코드)
    except Exception:                                # noqa: BLE001
        return None
    if not 낸 or "사전" not in 낸:
        return None
    계수 = {"매출원가": "b_COGS", "판관비": "β1_SGA", "연구개발비": "β1_SGA"}.get(기능)
    사 = (낸["사전"].get(낸["계층"]) or {}).get(계수)
    if not 사 or 사.get("μ") is None:
        return None
    return {"평균": 사["μ"], "분산": 사["τ²"], "평균분산": (사["표본분산"] / 사["N_기업"]) if 사["N_기업"] else 0.0, "회사수": 사["N_기업"],
            "방식": "패널 산업 사전(%s · %s %s)" % (국가, 사["집단"], 계수), "출처": "계수사전.py"}


def 쓰기(낸, 가정경로, 낼=None):
    p = 낼 or os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw", "계수사전.json")
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with io.open(p, "w", encoding="utf-8") as f:
        json.dump(낸, f, ensure_ascii=False, indent=1, default=str)
    return p


def 표찍기(낸):
    if 낸.get("형식", "").endswith("해당없음") or "사전" not in 낸:
        print("해당 없음 — %s" % 낸.get("해당없음"))
        return
    print("계수사전 — %s 패널 %d곳 · 창 %s~%s · 대상 %s(%s) · 계층 %s" % (낸["국가"], 낸["패널"]["회사"], 낸["패널"]["창"][0], 낸["패널"]["창"][-1],
                                                           낸["대상"].get("회사명") or "-", 낸["대상"].get("산업2") or "-", 낸["계층"]))
    사 = 낸["사전"][낸["계층"]]
    for k in ("β1_SGA", "β2_SGA", "b_COGS", "β2_COGS", "S2C_incr", "NetCapEx_Sales", "CapEx_Dep", "잔존연수", "δ_DSO", "λ_π"):
        v = 사.get(k)
        if not v:
            continue
        if "μ" in v:
            print("  %-15s N %4d  중앙값 %8.3f  Q1~Q3 %7.3f~%-7.3f  τ² %.4g%s" % (k, v["N_기업"], v["μ"], v["Q1"], v["Q3"], v["τ²"],
                                                                                 ("  풀 β1 %.3f" % v["풀_β1"]) if "풀_β1" in v else ""))
        elif "풀_β2" in v:
            print("  %-15s 풀 β2 %.3f(se %.3f · 하락쌍 %d) 하락 반응 %.3f %s" % (k, v["풀_β2"], v["풀_se2"], v["풀_하락쌍"], v["하락반응"], "유의" if v["유의"] else ""))
        elif "λ" in v:
            print("  %-15s λ %.3f  반감 %s해  n %d" % (k, v["λ"], ("%.1f" % v["반감햇수"]) if v["반감햇수"] else "-", v["N_기업연도"]))
    for k, r in 낸["수축"].items():
        print("  수축 %-14s 회사 %s → 적용 %.4g (w %.2f · 산업 %.4g)" % (k, ("%.4g" % r["회사"]["값"]) if r.get("회사") else "없음", r["적용값"], r["w"], r["산업"]["μ"]))
    for s in 낸["신호"]:
        print("  [%s] %s — %s: %s" % (s["등급"], s["종류"], s["대상"], s["글"]))


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description=__doc__.split("\n")[0])
    ap.add_argument("가정", nargs="?")
    ap.add_argument("--낼")
    ap.add_argument("--국가")
    ap.add_argument("--회사")
    ap.add_argument("--산업", help="--사전만 일 때 산업 코드")
    ap.add_argument("--사전만", action="store_true")
    ap.add_argument("--자리", help="패널 자리(기본 공용 캐시)")
    a = ap.parse_args()
    가정 = None
    if not a.사전만:
        if not a.가정 or not os.path.exists(a.가정):
            print("가정 파일이 없다: %s" % a.가정)
            return 입력오류
        try:
            가정 = json.load(io.open(a.가정, encoding="utf-8"))
        except ValueError as e:
            print("가정 JSON 파손 — %s" % e)
            return 입력오류
    try:
        낸, 까 = 분석(가정, a.가정, None, a.회사, a.국가, a.자리, a.산업)
    except Exception as e:                           # noqa: BLE001
        print("입력 오류 — %s" % e)
        return 입력오류
    if 낸 is None:
        print("입력 오류 — %s" % 까)
        return 입력오류
    if 가정 is not None:
        print("→ %s" % 쓰기(낸, a.가정, a.낼))
    표찍기(낸)
    return 발견 if any(s["등급"] == "경보" for s in 낸.get("신호", [])) else 통과


if __name__ == "__main__":
    sys.exit(main())

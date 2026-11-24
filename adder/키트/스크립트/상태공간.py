# -*- coding: utf-8 -*-
"""상태공간 — 공시가 물량(Q) · 단가(P)를 숫자로 주지 않아도 **숨은 P · Q 지수**를 칼만 필터 · 스무더로 복원한다 (기법 6 · 2026-10-21).

무엇을 하나
  매출 구분마다 상태 x_t = (q_t, p_t) — 로그 물량 지수 · 로그 단가 지수 — 를 두고 관측 넷으로 그 경로를 복원한다.
    ① 로그 매출 = q_t + p_t (+ 로그 환율 — 단가가 달러 기준이면. 표현실현의 「주기준」과 같은 규약)  ·  잡음이 아주 작다
    ② 물량 대리변수(가동률 · 생산실적 · 원재료비 · 외주가공비 — A3 · 인자)의 로그 변동 = Δq_t + 잡음
    ③ 단가 대리변수(판가공시 · 외부 가격지수 — A3 · B2 · 인자)의 로그 변동 = Δp_t + 잡음
    ④ **표현 대장의 밴드**(표현실현) — 그 분기 Δq(또는 Δp)의 관측 = 밴드 가운데, sd = 밴드 반폭 ÷ 1.645(밴드를 90% 구간으로 본다).
       밴드를 믿는 정도(분산 배율 κ)는 자료가 정한다 — κ 가 크면 「이 회사의 말은 밴드보다 헐겁다」
  상태는 (q_t, q_{t−1}, p_t, p_{t−1})(국소추세면 기울기 둘을 더한다)로 늘려 Δ 관측을 받는다. 첫 기간의 q 를 0 으로 묶어 지수의 밑을
  정한다(물량 지수 = 100 · exp(q_t), 단가 지수 = 100 · exp(p_t − p_1)). 분산 모수(물량 · 단가 전이 sd · κ · 대리변수 sd)는 칼만 우도를
  로그 눈금 좌표 탐색으로 최대화한다(표준 라이브러리 — 설정의 탐색 배수 · 돌림). 칼만 필터는 관측을 하나씩 받는 순차 갱신이고,
  RTS 스무더로 기간마다 x_t 와 공분산을 낸다.
왜 있나 — 매출 분해 규칙는 단가 · 물량이 모두 공시돼야 P × Q 로 가고, 없으면 성장률 한 줄(⑥)로 물러섰다. 그런데 말로 준 변동률
  (표현실현의 대장) · A3 의 가동률 · 원재료비 · B2 의 가격지수는 이미 `_raw/` 에 있다. 그것을 버리면 판매량을 읽는 배선(5번
  「연동기준 = 판매량」 · 7번 「물량연동」)이 다 죽는다. 이 도구는 그 그림자들로 P · Q 를 되살려 **수준 · P×Q 경로 후보와 근거범위**를 낸다.
**값을 정하지 않는다 — 엔진 산식은 그대로다.** 산출은 지수 후보 · 근거범위 · 신호뿐이고 가정 파일은 읽기만 한다.
  지수의 절대 수준(물량 단위 · 단위당 가격)은 만들지 않는다 — 변동의 경로만이다.

사용
    python 스크립트/상태공간.py 가정.json                        # 가정 곁 _raw/ → _raw/상태공간.json
    python 스크립트/상태공간.py 가정.json --단가통화 USD          # 원 | USD | 자동(기본 — 표현실현의 주기준, 없으면 원)
    python 스크립트/상태공간.py 가정.json --분기매출 분기.csv --대장 대장.csv --환율 fx.csv   # 표현실현 산출 대신 파일로
    python 스크립트/상태공간.py 가정.json --대리 대리.csv          # 분기 대리변수(열: 분기 · 품목 · 지표(물량|단가) · 이름 · 값)
    python 스크립트/상태공간.py 가정.json --빈도 연간              # 분기 | 연간 | 자동(기본 — 분기 매출이 있으면 분기)

읽는 것 — 가정 곁 `_raw/`(`정상화.파일찾기` 차례)
    표현실현.json     실현매출(품목별 분기 매출) · 대장(사전밴드 · 채널 · 지표 · 판정) · 설정.주기준 · 설정.결산월
    fx_USDKRW_일별.csv 원달러 일별 종가(표현실현이 받은 캐시) — 단가가 달러면 분기 평균을 쓴다
    동인원천.json      A3 판매량공시 · 판가공시 · 가동률공시 · 사업지표(연간 빈도의 대리변수)
    매출구분판정.json   구분[].매출구분 · Q지표 · P지표 — A3 계열을 구분에 잇는 이름(거친바퀴 `_A3계열` 과 같은 자)
    가정 `구조.매출구분[]`(이름 · 번호 · 경로) · `원천` 86~91(연간 빈도의 구분 매출)
내는 것 — `_raw/상태공간.json`
    {"형식": "상태공간 1", 만든날, 설정, 입력, 폴백, "구분": [{매출구분, 번호, 경로, 빈도, 기간, 잠재물량지수, 잠재단가지수, 물량95, 단가95,
     분기변동 · 연간변동, 복원오차, 변동오차, 앞자름, 대리변수, 관측수, 모수, 로그우도, 혁신, 판정, 폴백}], "제안": [...], "신호": [...]}
    앞자름 — 앞쪽에 표현 · 대리 정보가 하나도 없는 기간(지수 밑의 불확실성만 키우므로 잘라낸다). 제안의 확신은 변동오차(기간 변동 sd)로 매긴다
    제안 — 「매출구분초안 — 품목(구분 n) 수준 · P×Q 경로 후보」(지수 끝 · 연 변동 근거범위 %) ·
           「거친바퀴 — A-<판매단가 줄> 판매단가 변동률 …」 · 「거친바퀴 — A-<판매량 줄> 판매량 증가율 …」(증가율 경로만) — 그 줄 단위(비율)의
           [최소, 최대]. 거친바퀴.통계범위 가 자리의 A-n 으로 집는다
    판정 — 「P·Q 복원 가능」(물량 · 단가 쪽 정보가 다 최소정보 이상) · 「물량만」 · 「단가만」(다른 쪽은 매출 − 이쪽의 나머지) · 「불가」(폴백)
    신호 — 「복원 가능 — 증가율 경로에서 올릴 수 있다」 · 「P·Q 복원 — 근거범위 후보」 · 「표현과 실현이 어긋나는 분기」 ·
           「밴드보다 헐거운 말」 · 「표본 부족」 (모두 참고)
폴백 — 대리변수 · 표현이 하나도 없거나 기간이 최소보다 짧으면 그 구분은 「불가」이고 `폴백` 에 「⑥ 증가율 경로 그대로」를 적는다.
종료 코드 — 0 통과(신호는 모두 참고) · 2 입력오류(가정 · 입력 파일을 못 읽음 · 모르는 인자)
회사 · 업종 · 품목 이름은 이 도구에 한 글자도 없다 — 품목은 표현실현의 품목 · 가정의 매출구분 이름 · 인자로만 받는다.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import io
import json
import math
import os
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

산출이름 = "상태공간.json"
설정경로 = os.path.join(여기, "상태공간설정.json")
INF = float("inf")


def 설정읽기(경로=None):
    return json.load(io.open(경로 or 설정경로, encoding="utf-8"))


# ═════════════════════════════════════ 작은 행렬 (표준 라이브러리)

def 영(n, m=None):
    return [[0.0] * (n if m is None else m) for _ in range(n)]


def 단위(n):
    A = 영(n)
    for i in range(n):
        A[i][i] = 1.0
    return A


def 곱(A, B):
    m, k = len(A), len(B)
    n = len(B[0])
    return [[sum(A[i][r] * B[r][j] for r in range(k)) for j in range(n)] for i in range(m)]


def 곱벡(A, v):
    return [sum(a * b for a, b in zip(행, v)) for 행 in A]


def 전치(A):
    return [list(x) for x in zip(*A)]


def 더(A, B):
    return [[a + b for a, b in zip(x, y)] for x, y in zip(A, B)]


def 빼(A, B):
    return [[a - b for a, b in zip(x, y)] for x, y in zip(A, B)]


def 대칭(A):
    n = len(A)
    return [[0.5 * (A[i][j] + A[j][i]) for j in range(n)] for i in range(n)]


def 역(A, 지터=1e-12):
    """가우스-요르단(부분 피벗). 거의 특이하면 대각에 지터를 더해 다시 한다."""
    n = len(A)
    for 회 in range(4):
        M = [list(r) + [1.0 if i == j else 0.0 for j in range(n)] for i, r in enumerate(A)]
        if 회:
            for i in range(n):
                M[i][i] += 지터 * (10 ** (2 * 회))
        ok = True
        for c in range(n):
            p = max(range(c, n), key=lambda r: abs(M[r][c]))
            if abs(M[p][c]) < 1e-300:
                ok = False
                break
            M[c], M[p] = M[p], M[c]
            d = M[c][c]
            M[c] = [x / d for x in M[c]]
            for r in range(n):
                if r != c and M[r][c] != 0.0:
                    f = M[r][c]
                    M[r] = [a - f * b for a, b in zip(M[r], M[c])]
        if ok:
            return [r[n:] for r in M]
    raise ValueError("역행렬을 못 구한다")


def 촐레스키(A, 지터=1e-12):
    """A = L L' — 반정치에 가까우면 대각에 지터를 더한다(모의 · 표본 뽑기용)."""
    n = len(A)
    for 회 in range(6):
        L = 영(n)
        ok = True
        for i in range(n):
            for j in range(i + 1):
                s = A[i][j] + ((지터 * (10 ** 회)) if i == j else 0.0) - sum(L[i][k] * L[j][k] for k in range(j))
                if i == j:
                    if s <= 0:
                        ok = False
                        break
                    L[i][j] = math.sqrt(s)
                else:
                    L[i][j] = s / L[j][j]
            if not ok:
                break
        if ok:
            return L
    return [[math.sqrt(max(A[i][i], 0.0)) if i == j else 0.0 for j in range(n)] for i in range(n)]


# ═════════════════════════════════════ 칼만 필터 · RTS 스무더

def 칼만(관측들, F, Q, x0, P0, 고르기=True):
    """관측들 — 기간마다 [(h, y, r, 꼬리표)] (h: 상태 길이 벡터 · y: 값 · r: 잡음 분산 · 꼬리표: 혁신을 되찾을 이름 또는 None).
    순차 갱신(관측 잡음이 서로 독립이라 하나씩 받아도 같다). 첫 기간의 예측은 (x0, P0).
    → {"로그우도", "x", "P"(스무딩 — 고르기=False 면 거른 값), "x거름", "P거름", "혁신": [(기간, 꼬리표, v, S)]}"""
    n = len(x0)
    Ft = 전치(F)
    x, P = list(x0), [list(r) for r in P0]
    xp들, Pp들, xf들, Pf들, 혁 = [], [], [], [], []
    ll = 0.0
    for t, 관 in enumerate(관측들):
        if t > 0:
            x = 곱벡(F, x)
            P = 대칭(더(곱(곱(F, P), Ft), Q))
        xp들.append(list(x))
        Pp들.append([list(r) for r in P])
        for h, y, r, 표 in 관:
            Ph = [sum(P[i][j] * h[j] for j in range(n)) for i in range(n)]
            S = sum(h[i] * Ph[i] for i in range(n)) + r
            if S <= 0:
                continue
            v = y - sum(h[i] * x[i] for i in range(n))
            K = [a / S for a in Ph]
            x = [a + k * v for a, k in zip(x, K)]
            P = [[P[i][j] - K[i] * Ph[j] for j in range(n)] for i in range(n)]
            P = 대칭(P)
            ll += -0.5 * (math.log(2 * math.pi * S) + v * v / S)
            if 표 is not None:
                혁.append((t, 표, v, S))
        xf들.append(list(x))
        Pf들.append([list(r) for r in P])
    낸 = {"로그우도": ll, "x거름": xf들, "P거름": Pf들, "혁신": 혁, "x예측": xp들, "P예측": Pp들}
    if not 고르기 or not 관측들:
        낸["x"], 낸["P"] = xf들, Pf들
        return 낸
    T = len(관측들)
    xs, Ps = [None] * T, [None] * T
    xs[-1], Ps[-1] = xf들[-1], Pf들[-1]
    for t in range(T - 2, -1, -1):
        J = 곱(곱(Pf들[t], Ft), 역(Pp들[t + 1]))
        d = [a - b for a, b in zip(xs[t + 1], xp들[t + 1])]
        xs[t] = [a + b for a, b in zip(xf들[t], 곱벡(J, d))]
        Ps[t] = 대칭(더(Pf들[t], 곱(곱(J, 빼(Ps[t + 1], Pp들[t + 1])), 전치(J))))
    낸["x"], 낸["P"] = xs, Ps
    return 낸


def 좌표탐색(우도, 초기, 범위, 탐색):
    """로그 눈금 좌표 탐색 — 모수 dict 를 하나씩 배수로 흔들어 우도가 오르는 쪽으로. → (모수, 최대 로그우도, 평가 수)."""
    θ = dict(초기)
    최 = 우도(θ)
    수 = 1
    for 배들 in [탐색.get("배수") or [0.25, 0.5, 1, 2, 4]] * int(탐색.get("돌림", 4)) + [탐색.get("잘게") or [0.7071, 1, 1.4142]] * 2:
        for k in list(θ):
            lo, hi = 범위.get(k, (1e-6, 1e6))
            고 = θ[k]
            for b in 배들:
                v = min(max(고 * b, lo), hi)
                if v == θ[k]:
                    continue
                시험 = dict(θ, **{k: v})
                l = 우도(시험)
                수 += 1
                if l > 최 + 1e-9:
                    최, θ = l, 시험
            고 = θ[k]
    return θ, 최, 수


# ═════════════════════════════════════ 기간 · 밴드

def 분기정렬키(q):
    m = re.fullmatch(r"(\d{4})Q([1-4])", "%s" % q)
    return (int(m.group(1)), int(m.group(2))) if m else (9999, 9)


def 앞기간(q):
    m = re.fullmatch(r"(\d{4})Q([1-4])", "%s" % q)
    if m:
        y, n = int(m.group(1)), int(m.group(2))
        return "%dQ4" % (y - 1) if n == 1 else "%dQ%d" % (y, n - 1)
    m = re.fullmatch(r"FY(\d{4})A", "%s" % q)
    if m:
        return "FY%dA" % (int(m.group(1)) - 1)
    return None


def 밴드관측(밴드, 설정):
    """사전 밴드 [lo, hi](%, None = 열린 끝) → (로그 변동 가운데, sd). 밴드를 `밴드포괄` 구간으로 본다."""
    lo, hi = 밴드
    폭 = float(설정.get("열린밴드폭", 15))
    if lo is None and hi is None:
        return None
    if lo is None:
        lo = hi - 폭
    if hi is None:
        hi = lo + 폭
    lo, hi = max(lo, -99.0), max(hi, -99.0)
    a, b = math.log(1 + lo / 100.0), math.log(1 + hi / 100.0)
    z = _정규분위((1 + float(설정.get("밴드포괄", 0.9))) / 2)
    return (a + b) / 2, max((b - a) / 2 / z, 1e-4)


def _정규분위(p):
    """표준정규 분위수(Acklam 근사 — 1e-9 안팎)."""
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02, 1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02, 6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00, -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00]
    pl = 0.02425
    if p < pl:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > 1 - pl:
        return -_정규분위(1 - p)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


def _수(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def _밴드글(t):
    """「1.0 ~ 3.0」 · 「−∞ ~ -20.0」 · 「20.0 ~ ∞」 → [lo, hi](열린 끝 None)."""
    if isinstance(t, (list, tuple)) and len(t) == 2:
        return [_수(t[0]), _수(t[1])]
    m = re.match(r"\s*([^~]+?)\s*~\s*(.+?)\s*$", "%s" % (t or ""))
    if not m:
        return None
    def 하나(s):
        s = s.replace("−", "-").strip()
        return None if "∞" in s else _수(s)
    return [하나(m.group(1)), 하나(m.group(2))]


# ═════════════════════════════════════ 재료

def _파일(이름, 가정경로):
    try:
        import 정상화                                       # noqa: PLC0415
        return 정상화.파일찾기(이름, 가정경로)
    except Exception:                                        # noqa: BLE001
        p = os.path.join(os.path.dirname(os.path.abspath(가정경로 or ".")), "_raw", 이름)
        if os.path.exists(p):
            try:
                return json.load(io.open(p, encoding="utf-8")), p
            except (OSError, ValueError):
                return None, p
        return None, None


def _이름표():
    try:
        import 표현실현 as X                                  # noqa: PLC0415
        return X.지표이름, X.채널이름
    except Exception:                                        # noqa: BLE001
        return ({"물량": "물량", "출하량": "물량", "단가": "단가", "asp": "단가"},
                {"공시": "공시", "dart": "공시", "영문": "영문", "424b4": "영문", "구두": "구두"})


def _분기평균환율(일별, 분기, 결산월):
    try:
        import 표현실현 as X                                  # noqa: PLC0415
        return X.분기평균(일별, 분기, 결산월)[0]
    except Exception:                                        # noqa: BLE001
        return None


def _환율일별(경로):
    d = {}
    if 경로 and os.path.exists(경로):
        for r in csv.DictReader(io.open(경로, encoding="utf-8-sig")):
            v = _수(r.get("종가"))
            if r.get("일자") and v:
                d[r["일자"]] = v
    return d


def 분기매출CSV(경로):
    """열: (분기 | 연도 + 분기) · 품목 열들 · (합계). → {품목: {분기: 값}}."""
    낸 = {}
    for r in csv.DictReader(io.open(경로, encoding="utf-8-sig")):
        q = (r.get("분기") or "").strip()
        if not re.fullmatch(r"\d{4}Q[1-4]", q) and r.get("연도"):
            q = "%sQ%s" % (r["연도"].strip(), (r.get("분기") or "").strip()[:1])
        if not re.fullmatch(r"\d{4}Q[1-4]", q):
            continue
        for k, v in r.items():
            if k in ("분기", "연도", "접수번호", "만든법", "합계차") or v in (None, ""):
                continue
            x = _수(v)
            if x is not None:
                낸.setdefault(k, {})[q] = x
    return 낸


def 대장CSV(경로):
    지표이름, 채널이름 = _이름표()
    낸 = []
    for r in csv.DictReader(io.open(경로, encoding="utf-8-sig")):
        rec = dict(r)
        rec["지표"] = 지표이름.get(("%s" % r.get("지표") or "").strip().lower(), 지표이름.get(("%s" % r.get("지표") or "").strip(), r.get("지표")))
        rec["채널"] = 채널이름.get(("%s" % r.get("채널") or "").strip().lower(), r.get("채널"))
        rec["사전밴드"] = _밴드글(r.get("사전밴드"))
        rec["범위"] = r.get("범위") or "연결"
        낸.append(rec)
    return 낸


def 대리CSV(경로):
    """열: 분기 · 품목 · 지표(물량|단가) · 이름 · 값 → [{"품목","지표","이름","값": {기간: 값}}]."""
    지표이름, _ = _이름표()
    묶 = {}
    for r in csv.DictReader(io.open(경로, encoding="utf-8-sig")):
        x = _수(r.get("값"))
        q = (r.get("분기") or r.get("기간") or "").strip()
        if x is None or not q:
            continue
        지 = 지표이름.get(("%s" % r.get("지표") or "").strip().lower(), (r.get("지표") or "").strip())
        키 = ((r.get("품목") or "").strip(), 지, (r.get("이름") or "").strip())
        묶.setdefault(키, {})[q] = x
    return [{"품목": a, "지표": b, "이름": c, "값": v} for (a, b, c), v in 묶.items()]


def _구분들(가정):
    낸 = []
    for x in ((가정.get("구조") or {}).get("매출구분") or []):
        if isinstance(x, dict) and x.get("번호"):
            낸.append({"번호": int(x["번호"]), "이름": ("%s" % (x.get("이름") or "")).strip(), "경로": x.get("경로") or "증가율",
                      "상위": x.get("상위")})
    return 낸


def _구분찾기(이름, 구분들):
    """품목 이름 → 가정 매출구분(이름이 같거나 한쪽이 다른 쪽을 품을 때 · 하위 구분은 뺀다). 못 찾으면 None."""
    n = (이름 or "").strip().lower()
    if not n:
        return None
    위 = [g for g in 구분들 if not g.get("상위")]
    for g in 위:
        if g["이름"].lower() == n:
            return g
    for g in 위:
        if g["이름"] and (g["이름"].lower() in n or n in g["이름"].lower()):
            return g
    return None


def _결산월(가정, 표):
    for v in ((표 or {}).get("설정") or {}).get("결산월"), (가정.get("기간") or {}).get("결산월"), (가정.get("메타") or {}).get("결산월"):
        if _수(v):
            return int(v)
    return 12


def 분기재료(가정, 가정경로, 인자, 설정):
    """→ {"매출": {품목: {분기: 값}}, "대장": [...], "주기준", "환율": {분기: 값}, "결산월", "출처": [...], "대리": [...]} 또는 None."""
    표, 표곳 = _파일("표현실현.json", 가정경로)
    매출, 대장, 출처 = {}, [], []
    if 인자.get("분기매출"):
        매출 = 분기매출CSV(인자["분기매출"])
        출처.append("분기 매출 %s" % os.path.basename(인자["분기매출"]))
    elif isinstance(표, dict) and 표.get("실현매출"):
        for v in 표["실현매출"]:
            for k, x in (v.get("값") or {}).items():
                if _수(x):
                    매출.setdefault(k, {})[v["분기"]] = float(x)
        출처.append("표현실현 실현매출(%s)" % os.path.basename(표곳))
    if 인자.get("대장"):
        대장 = 대장CSV(인자["대장"])
        출처.append("대장 %s" % os.path.basename(인자["대장"]))
    elif isinstance(표, dict):
        대장 = [dict(x) for x in (표.get("대장") or []) if isinstance(x, dict)]
        if 대장:
            출처.append("표현실현 대장 %d행" % len(대장))
    if not 매출:
        return None
    결산월 = _결산월(가정, 표)
    주 = 인자.get("단가통화") or "자동"
    if 주 == "자동":
        주 = ((표 or {}).get("설정") or {}).get("주기준") or "원"
    환곳 = 인자.get("환율")
    if not 환곳:
        d = os.path.dirname(표곳) if 표곳 else os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw")
        환곳 = os.path.join(d, "fx_USDKRW_일별.csv")
    일별 = _환율일별(환곳)
    환 = {}
    if 일별:
        for 품 in 매출.values():
            for q in 품:
                if q not in 환:
                    환[q] = _분기평균환율(일별, q, 결산월)
    대리 = 대리CSV(인자["대리"]) if 인자.get("대리") else []
    return {"매출": 매출, "대장": 대장, "주기준": 주, "환율": 환, "환율곳": 환곳 if 일별 else None, "결산월": 결산월,
            "출처": 출처, "대리": 대리, "빈도": "분기"}


def _FY수준(값):
    낸 = {}
    for k, v in (값 or {}).items():
        m = re.fullmatch(r"FY(\d{4})A?", "%s" % k)
        x = _수(v)
        if m and x is not None and x > 0:
            낸["FY%sA" % m.group(1)] = x
    return 낸


def _줄번호(구분):
    """구분 번호 → (판매량 줄, 판매단가 줄) — 엔진 매출구분 표(없으면 표준 배치)."""
    try:
        from 엔진 import 매출 as M                           # noqa: PLC0415
        t = M.매출구분[int(구분) - 1]
        return t[1], t[2]
    except Exception:                                        # noqa: BLE001
        return {1: (30, 34), 2: (38, 42), 3: (46, 50), 4: (54, 58), 5: (62, 66), 6: (70, None)}.get(int(구분), (None, None))


def 연간재료(가정, 가정경로):
    """구분별 연간 매출(원천 86~91 · FY 열) + A3 대리변수(매출구분판정의 Q지표 · P지표 → 판매량공시 · 사업지표 · 판가공시 · 가동률공시)."""
    try:
        from 엔진 import 매출 as M                           # noqa: PLC0415
        원천번호 = {s + 1: M.매출구분[s][0] for s in range(6)}
    except Exception:                                        # noqa: BLE001
        원천번호 = {1: 86, 2: 87, 3: 88, 4: 89, 5: 90, 6: 91}
    원천 = 가정.get("원천") or {}
    판, _p = _파일("매출구분판정.json", 가정경로)
    A3, _q = _파일("동인원천.json", 가정경로)
    판 = 판 if isinstance(판, dict) else {}
    A3 = A3 if isinstance(A3, dict) else {}
    매출, 대리 = {}, []
    for g in _구분들(가정):
        if g.get("상위"):
            continue
        v = _FY수준((원천.get("%d" % 원천번호.get(g["번호"], 0)) or {}))
        if len(v) < 2:
            continue
        매출[g["이름"] or "구분 %d" % g["번호"]] = v
        이름 = g["이름"] or "구분 %d" % g["번호"]
        for 쪽, 칸, 목록이름 in (("물량", "Q지표", "판매량공시"), ("단가", "P지표", "판가공시")):
            지 = next((("%s" % x.get(칸)).strip() for x in (판.get("구분") or [])
                      if isinstance(x, dict) and "%s" % x.get("매출구분") == "%s" % g["번호"] and x.get(칸)), None)
            if not 지:
                continue
            for x in (A3.get(목록이름) or []) if isinstance(A3.get(목록이름), list) else []:
                if isinstance(x, dict) and ("%s" % x.get("공시이름") or "").strip() == 지:
                    대리.append({"품목": 이름, "지표": 쪽, "이름": "A3 %s 「%s」" % (목록이름, 지), "값": _FY수준(x.get("값"))})
            if 쪽 == "물량" and isinstance((A3.get("사업지표") or {}).get(지), dict):
                대리.append({"품목": 이름, "지표": "물량", "이름": "A3 사업지표 「%s」" % 지, "값": _FY수준(A3["사업지표"][지].get("값"))})
        공 = [x for x in (A3.get("가동률공시") or []) if isinstance(x, dict)] if isinstance(A3.get("가동률공시"), list) else []
        고른 = 공[0] if len(공) == 1 else next((x for x in 공 if ("%s" % x.get("공시이름") or "").strip() == 이름), None)
        if 고른:
            대리.append({"품목": 이름, "지표": "물량", "이름": "A3 가동률공시 「%s」" % (고른.get("공시이름") or ""), "값": _FY수준(고른.get("값"))})
    if not 매출:
        return None
    return {"매출": 매출, "대장": [], "주기준": "원", "환율": {}, "환율곳": None, "결산월": _결산월(가정, None),
            "출처": ["원천 13번 86~91(연간)"] + (["A3 동인원천"] if A3 else []) + (["매출구분판정"] if 판 else []),
            "대리": [x for x in 대리 if len(x["값"]) >= 2], "빈도": "연간"}


# ═════════════════════════════════════ 한 구분 복원

def 밴드고르기(대장, 품목, 설정):
    """{(기간, 지표): (밴드, 채널, 표현)} — 공시 · 영문 가운데 가장 좁은 것, 없을 때만 구두(설정 채널차례)."""
    차례 = 설정.get("채널차례") or ["공시", "영문", "구두"]
    앞 = set(차례[:2])
    후보 = {}
    for r in 대장:
        if r.get("제품") != 품목 or r.get("지표") not in ("물량", "단가"):
            continue
        if (r.get("범위") or "연결") != "연결" or r.get("판정") in ("대조 제외", "사전에 없음"):
            continue
        b = r.get("사전밴드")
        if not (isinstance(b, (list, tuple)) and len(b) == 2) or (b[0] is None and b[1] is None):
            continue
        후보.setdefault((r["분기"], r["지표"]), []).append((r.get("채널"), list(b), r.get("표현")))
    폭 = float(설정.get("열린밴드폭", 15))

    def 너비(b):
        lo, hi = b
        if lo is None:
            lo = hi - 폭
        if hi is None:
            hi = lo + 폭
        return hi - lo
    낸 = {}
    for k, 목록 in 후보.items():
        좋은 = [x for x in 목록 if x[0] in 앞] or [x for x in 목록 if x[0] not in 앞]
        좋은.sort(key=lambda x: 너비(x[1]))
        낸[k] = (좋은[0][1], 좋은[0][0], 좋은[0][2])
    return 낸


def 복원(이름, 매출, 기간들, 밴드들, 대리들, 환율로그, 설정, 전이="랜덤워크"):
    """한 구분의 칼만 복원 → 결과 dict. 매출 = {기간: 값} · 밴드들 = {(기간, 지표): (밴드, 채널, 표현)} ·
    대리들 = [{"지표", "이름", "값": {기간: 값}}] · 환율로그 = {기간: 로그 환율} 또는 None(원 기준)."""
    국소 = 전이 == "국소추세"
    # 상태 자리
    if 국소:
        iq, iql, ibq, ip, ipl, ibp = range(6)
        n = 6
    else:
        iq, iql, ip, ipl = range(4)
        ibq = ibp = None
        n = 4
    F = 단위(n)
    F[iql] = [0.0] * n
    F[iql][iq] = 1.0
    F[ipl] = [0.0] * n
    F[ipl][ip] = 1.0
    if 국소:
        F[iq][ibq] = 1.0
        F[ip][ibp] = 1.0
    T = len(기간들)

    def e(*자리, 부호=None):
        h = [0.0] * n
        for k, i in enumerate(자리):
            h[i] = 1.0 if 부호 is None else 부호[k]
        return h

    대리이름 = ["대리%d" % i for i in range(len(대리들))]

    def 관측짓기(θ):
        r매 = float(설정.get("매출관측분산", 1e-5))
        κ = θ.get("밴드배율", 1.0)
        관 = []
        for t, q in enumerate(기간들):
            줄 = []
            if t == 0:
                줄.append((e(iq), 0.0, 1e-10, None))
            y = math.log(매출[q]) - (환율로그[q] if 환율로그 else 0.0)
            줄.append((e(iq, ip), y, r매, None))
            if t > 0:
                for 지, (i, il) in (("물량", (iq, iql)), ("단가", (ip, ipl))):
                    b = 밴드들.get((q, 지))
                    if b:
                        m, sd = 밴드관측(b[0], 설정)
                        줄.append((e(i, il, 부호=(1.0, -1.0)), m, κ * sd * sd, ("표현", 지, q, b[1], b[2], m, sd)))
                앞 = 기간들[t - 1]
                for 이, 대 in zip(대리이름, 대리들):
                    a, b0 = _수(대["값"].get(q)), _수(대["값"].get(앞))
                    if a and b0 and a > 0 and b0 > 0:
                        i, il = (iq, iql) if 대["지표"] == "물량" else (ip, ipl)
                        sd = θ.get(이, 0.05)
                        줄.append((e(i, il, 부호=(1.0, -1.0)), math.log(a / b0), sd * sd, ("대리", 대["지표"], q, 대["이름"], None, None, None)))
            관.append(줄)
        return 관

    def 전이분산(θ):
        Q = 영(n)
        Q[iq][iq] = θ["물량sd"] ** 2
        Q[ip][ip] = θ["단가sd"] ** 2
        if 국소:
            비 = float(설정.get("기울기분산비", 0.1))
            Q[ibq][ibq] = 비 * θ["물량sd"] ** 2
            Q[ibp][ibp] = 비 * θ["단가sd"] ** 2
        return Q

    y0 = math.log(매출[기간들[0]]) - (환율로그[기간들[0]] if 환율로그 else 0.0)
    x0 = [0.0] * n
    x0[ip] = y0
    x0[ipl] = y0
    P0 = 영(n)
    for i, v in ((iq, 1.0), (iql, 1.0), (ip, 100.0), (ipl, 100.0)):
        P0[i][i] = v
    if 국소:
        P0[ibq][ibq] = P0[ibp][ibp] = 0.25

    초 = 설정.get("초기") or {}
    θ0 = {"물량sd": float(초.get("물량sd", 0.1)), "단가sd": float(초.get("단가sd", 0.1))}
    if 밴드들:
        θ0["밴드배율"] = float(초.get("밴드배율", 1.0))
    for 이 in 대리이름:
        θ0[이] = float(초.get("대리sd", 0.05))
    범 = 설정.get("범위") or {}
    sd범 = tuple(범.get("sd") or (0.002, 1.0))
    범위 = {k: sd범 for k in θ0}
    if "밴드배율" in θ0:
        범위["밴드배율"] = tuple(범.get("밴드배율") or (0.25, 25.0))

    def 우도(θ):
        try:
            return 칼만(관측짓기(θ), F, 전이분산(θ), x0, P0, 고르기=False)["로그우도"]
        except (ValueError, OverflowError, ZeroDivisionError):
            return -1e300
    θ, ll, 평가 = 좌표탐색(우도, θ0, 범위, 설정.get("탐색") or {})
    R = 칼만(관측짓기(θ), F, 전이분산(θ), x0, P0, 고르기=True)
    xs, Ps = R["x"], R["P"]
    z95 = 1.959963984540054
    z90 = 1.6448536269514722
    q지, p지, q95, p95, q편차들, p편차들 = [], [], [], [], [], []
    p1 = xs[0][ip]
    for t in range(T):
        sq, sp = math.sqrt(max(Ps[t][iq][iq], 0.0)), math.sqrt(max(Ps[t][ip][ip], 0.0))
        q지.append(round(100 * math.exp(xs[t][iq]), 3))
        p지.append(round(100 * math.exp(xs[t][ip] - p1), 3))
        q95.append([round(100 * math.exp(xs[t][iq] - z95 * sq), 3), round(100 * math.exp(xs[t][iq] + z95 * sq), 3)])
        p95.append([round(100 * math.exp(xs[t][ip] - p1 - z95 * sp), 3), round(100 * math.exp(xs[t][ip] - p1 + z95 * sp), 3)])
        if t > 0:
            q편차들.append(sq)
            p편차들.append(sp)
    변동, 변sd물, 변sd단 = [], [], []
    for t in range(1, T):
        P = Ps[t]
        dq = xs[t][iq] - xs[t][iql]
        dp = xs[t][ip] - xs[t][ipl]
        vq = max(P[iq][iq] + P[iql][iql] - 2 * P[iq][iql], 0.0)
        vp = max(P[ip][ip] + P[ipl][ipl] - 2 * P[ip][ipl], 0.0)
        변sd물.append(math.sqrt(vq))
        변sd단.append(math.sqrt(vp))
        변동.append({"기간": 기간들[t],
                   "물량": round((math.exp(dq) - 1) * 100, 2), "물량90": [round((math.exp(dq - z90 * math.sqrt(vq)) - 1) * 100, 2),
                                                               round((math.exp(dq + z90 * math.sqrt(vq)) - 1) * 100, 2)],
                   "단가": round((math.exp(dp) - 1) * 100, 2), "단가90": [round((math.exp(dp - z90 * math.sqrt(vp)) - 1) * 100, 2),
                                                               round((math.exp(dp + z90 * math.sqrt(vp)) - 1) * 100, 2)],
                   "표현_물량": (밴드들.get((기간들[t], "물량")) or [None])[0], "표현_단가": (밴드들.get((기간들[t], "단가")) or [None])[0]})
    # 연간 변동 — 분기면 회계연도 네 분기가 다 있는 해의 지수 평균끼리, 연간이면 해끼리
    연간 = []
    if 기간들 and re.fullmatch(r"\d{4}Q[1-4]", 기간들[0]):
        해 = {}
        for t, q in enumerate(기간들):
            해.setdefault(int(q[:4]), []).append(t)
        완 = sorted(y for y, ts in 해.items() if len(ts) == 4)
        for y in 완:
            if y - 1 in 완:
                def 평(지, ts):
                    return sum(지[t] for t in ts) / len(ts)
                연간.append({"해": y, "물량": round((평(q지, 해[y]) / 평(q지, 해[y - 1]) - 1) * 100, 2),
                           "단가": round((평(p지, 해[y]) / 평(p지, 해[y - 1]) - 1) * 100, 2),
                           "매출": round((sum(매출[기간들[t]] for t in 해[y]) / sum(매출[기간들[t]] for t in 해[y - 1]) - 1) * 100, 2)})
    else:
        for x in 변동:
            연간.append({"해": int(re.sub(r"\D", "", x["기간"])[:4]), "물량": x["물량"], "단가": x["단가"]})
    # 혁신 — 표현 관측의 표준화 혁신
    문 = float(설정.get("혁신문턱", 2.58))
    혁 = []
    for t, 표, v, S in R["혁신"]:
        if 표 and 표[0] == "표현":
            z = v / math.sqrt(S)
            혁.append({"기간": 표[2], "지표": 표[1], "채널": 표[3], "표현": 표[4], "밴드가운데": round((math.exp(표[5]) - 1) * 100, 2),
                      "표준화혁신": round(z, 2), "큼": abs(z) > 문})
    수 = {"표현_물량": sum(1 for (q, 지) in 밴드들 if 지 == "물량" and q in 기간들[1:]),
         "표현_단가": sum(1 for (q, 지) in 밴드들 if 지 == "단가" and q in 기간들[1:]),
         "대리_물량": sum(len([q for q in 기간들[1:] if q in 대["값"] and 앞기간(q) in 대["값"]]) for 대 in 대리들 if 대["지표"] == "물량"),
         "대리_단가": sum(len([q for q in 기간들[1:] if q in 대["값"] and 앞기간(q) in 대["값"]]) for 대 in 대리들 if 대["지표"] == "단가")}
    최소 = int(설정.get("최소정보", 4))
    물정보 = 수["표현_물량"] + 수["대리_물량"]
    단정보 = 수["표현_단가"] + 수["대리_단가"]
    판정 = ("P·Q 복원 가능" if (물정보 >= 최소 and 단정보 >= 최소) else "물량만" if 물정보 >= 최소 else "단가만" if 단정보 >= 최소 else "불가")
    return {"매출구분": 이름, "빈도": "분기" if re.fullmatch(r"\d{4}Q[1-4]", 기간들[0]) else "연간", "기간": list(기간들),
            "잠재물량지수": q지, "잠재단가지수": p지, "물량95": q95, "단가95": p95, "분기변동": 변동,
            "연간변동": 연간,
            "복원오차": {"물량": round(statistics.median(q편차들), 4) if q편차들 else None, "단가": round(statistics.median(p편차들), 4) if p편차들 else None,
                     "_뜻": "기간마다 스무딩한 로그 지수 sd 의 중앙값(≈ 비율 오차 — 지수 밑에서 멀수록 쌓인다)"},
            "변동오차": {"물량": round(statistics.median(변sd물), 4) if 변sd물 else None, "단가": round(statistics.median(변sd단), 4) if 변sd단 else None,
                     "_뜻": "기간 변동(로그 차분) sd 의 중앙값 — P×Q 경로가 쓰는 증가율의 오차. 제안의 확신은 이것으로 매긴다"},
            "대리변수": [d["이름"] for d in 대리들], "관측수": 수,
            "모수": {k: round(v, 5) for k, v in θ.items()}, "모수_이름": {이: d["이름"] for 이, d in zip(대리이름, 대리들)},
            "로그우도": round(ll, 3), "우도평가": 평가, "혁신": 혁, "판정": 판정, "폴백": None}


# ═════════════════════════════════════ 실행

def 실행(가정, 가정경로, 인자=None, 설정=None):
    인자 = 인자 or {}
    설 = (설정 or 설정읽기())
    S = 설["상태공간"]
    빈도 = 인자.get("빈도") or "자동"
    재 = None
    if 빈도 in ("자동", "분기"):
        재 = 분기재료(가정, 가정경로, 인자, S)
    if 재 is None and 빈도 in ("자동", "연간"):
        재 = 연간재료(가정, 가정경로)
    결과 = {"형식": "상태공간 1", "만든날": datetime.date.today().isoformat(),
          "설정": {"파일": os.path.basename(설정경로), "전이": S.get("전이"), "밴드포괄": S.get("밴드포괄"), "최소기간": S.get("최소기간"),
                 "최소정보": S.get("최소정보"), "채널차례": S.get("채널차례")},
          "입력": {}, "폴백": None, "구분": [], "제안": [], "신호": []}
    신호 = 결과["신호"]

    def 알림(종류, 대상, 값, 문턱, 글, 등급="참고"):
        신호.append({"출처": "상태공간", "종류": 종류, "대상": 대상, "값": 값, "문턱": 문턱, "글": 글, "등급": 등급})

    if 재 is None:
        결과["폴백"] = "⑥ 증가율 경로 그대로 — 분기 매출(표현실현 · 인자)도 연간 구분 매출(원천 86~91)도 없다"
        알림("표본 부족", "전체", 0, S.get("최소기간"), "P · Q 를 복원할 매출 계열이 없다 — 증가율 경로 그대로 간다(폴백)")
        return 결과
    결과["입력"] = {"빈도": 재["빈도"], "출처": 재["출처"], "주기준": 재["주기준"], "환율": 재.get("환율곳"), "결산월": 재["결산월"]}
    구분들 = _구분들(가정)
    기준일 = ("%s" % ((가정.get("메타") or {}).get("평가기준일") or "")).strip()
    try:                                                     # 2026-10-25 날짜 둘 — 매출은 재무 관측이라 끝이 재무기준일 F(없으면 평가기준일 — 옛 길)
        import 기준일 as _기                                  # noqa: PLC0415
        _r = _기.기준일들(가정)
        if not _r.get("오류") and not _r.get("같음"):
            기준일 = _r["재무기준일"]
            결과["입력"]["재무기준일"] = 기준일
    except Exception:                                        # noqa: BLE001
        pass
    for 품, 계 in sorted(재["매출"].items()):
        if 품 in ("합계", "기타"):
            continue
        기간들 = sorted([q for q, v in 계.items() if v and v > 0], key=분기정렬키 if 재["빈도"] == "분기" else (lambda x: x))
        if 재["빈도"] == "분기" and 기준일:
            try:
                import 표현실현 as X                          # noqa: PLC0415
                끝 = max((q for q in 기간들 if X.분기달(q, 재["결산월"])[-1] <= (int(기준일[:4]), int(기준일[5:7]))), key=분기정렬키, default=None)
                if 끝:
                    기간들 = [q for q in 기간들 if 분기정렬키(q) <= 분기정렬키(끝)]          # 기준일(재무기준일) 뒤 매출은 실적이 아니다 — 쓰지 않는다
            except Exception:                                # noqa: BLE001
                pass
        # 끊긴 기간이 있으면 가장 긴 연속 구간만
        연속, 지금 = [], []
        for q in 기간들:
            if 지금 and 앞기간(q) != 지금[-1]:
                연속.append(지금)
                지금 = []
            지금.append(q)
        if 지금:
            연속.append(지금)
        기간들 = max(연속, key=len) if 연속 else []
        g = _구분찾기(품, 구분들)
        한 = {"매출구분": 품, "번호": g["번호"] if g else None, "경로": g["경로"] if g else None}
        밴드들 = 밴드고르기(재["대장"], 품, S)
        대리들 = [d for d in 재["대리"] if (d.get("품목") or 품) == 품 and d["지표"] in ("물량", "단가")]
        # 앞쪽에 물량 · 단가를 가를 정보(표현 · 대리변수)가 하나도 없는 기간은 잘라낸다 — 근거 없이 매출 변동을 나눈 지수가
        # 지수 밑(첫 기간)의 불확실성만 키우고 연간 변동 · 근거범위에 섞여 든다
        정보 = [t for t in range(1, len(기간들)) if any((기간들[t], 지) in 밴드들 for 지 in ("물량", "단가"))
              or any(기간들[t] in d["값"] and 기간들[t - 1] in d["값"] for d in 대리들)]
        if 정보 and 정보[0] > 1:
            한["앞자름"] = 기간들[:정보[0] - 1]
            기간들 = 기간들[정보[0] - 1:]
        if len(기간들) < int(S.get("최소기간", 6)):
            한.update(판정="불가", 폴백="⑥ 증가율 경로 그대로 — 연속 기간 %d개(최소 %s)" % (len(기간들), S.get("최소기간")), 기간=기간들)
            결과["구분"].append(한)
            알림("표본 부족", 품, len(기간들), S.get("최소기간"), "%s — 연속 기간이 %d개라 P · Q 를 복원하지 않는다(폴백 — 증가율 경로 그대로)" % (품, len(기간들)))
            continue
        환로그 = None
        if 재["주기준"] == "USD":
            if all(_수((재["환율"] or {}).get(q)) for q in 기간들):
                환로그 = {q: math.log(재["환율"][q]) for q in 기간들}
            else:
                알림("환율 없음", 품, None, None, "%s — 단가가 달러 기준인데 분기 평균 환율이 빈 분기가 있어 원 기준으로 복원했다" % 품)
        if not 정보:
            한.update(판정="불가", 폴백="⑥ 증가율 경로 그대로 — 표현 · 대리변수가 없다", 기간=기간들)
            결과["구분"].append(한)
            알림("표본 부족", 품, 0, S.get("최소정보"), "%s — 물량 · 단가를 가를 표현 · 대리변수가 없다(폴백 — 증가율 경로 그대로)" % 품)
            continue
        r = 복원(품, 계, 기간들, 밴드들, 대리들, 환로그, S, S.get("전이") or "랜덤워크")
        r.update(한)
        r["단가기준"] = "USD(로그 환율을 뺀 매출)" if 환로그 else "원"
        결과["구분"].append(r)
        if r["판정"] == "불가":
            r["폴백"] = "⑥ 증가율 경로 그대로 — 물량 · 단가 쪽 정보가 다 최소정보(%s) 미만" % S.get("최소정보")
            알림("표본 부족", 품, max(r["관측수"].values()), S.get("최소정보"), "%s — 물량 · 단가 쪽 정보가 모자라 복원으로 판정하지 않는다(폴백)" % 품)
            continue
        출 = []
        if r["관측수"]["표현_물량"] or r["관측수"]["표현_단가"]:
            출.append("표현 대장 물량 %d · 단가 %d" % (r["관측수"]["표현_물량"], r["관측수"]["표현_단가"]))
        출 += r["대리변수"]
        if 환로그:
            출.append("분기 평균 원달러")
        연 = r.get("연간변동") or []
        범 = {}
        if 연:
            범["판매량 증가율(연 · 복원)"] = [min(x["물량"] for x in 연), max(x["물량"] for x in 연)]
            범["판매단가 변동률(연 · 복원)"] = [min(x["단가"] for x in 연), max(x["단가"] for x in 연)]
        오 = max(v for v in (r["변동오차"]["물량"], r["변동오차"]["단가"]) if v is not None)
        문 = S.get("확신문턱") or {"강": 0.03, "보통": 0.08}
        확 = "강" if 오 <= float(문["강"]) else "보통" if 오 <= float(문["보통"]) else "약"
        헐 = float(S.get("헐거움문턱", 4))
        if (r["모수"].get("밴드배율") or 0) >= 헐:
            확 = {"강": "보통", "보통": "약"}.get(확, 확)        # 말이 밴드보다 헐거우면 정밀도가 κ 추정에 기댄다 — 한 칸 낮춘다
        결과["제안"].append({"자리": "매출구분초안 — %s%s 수준 · P×Q 경로 후보" % (품, (" (구분 %d)" % r["번호"]) if r.get("번호") else ""),
                          "값": {"물량지수_끝": r["잠재물량지수"][-1], "단가지수_끝": r["잠재단가지수"][-1], "기간_끝": r["기간"][-1]},
                          "근거범위": 범, "딱지": "[계산 — 상태공간 P·Q 복원(대리변수: %s)]" % " · ".join(출),
                          "확신": 확, "글": "변동 오차(로그 차분 sd 중앙값) 물량 %s · 단가 %s · 지수 오차 물량 %s · 단가 %s · 판정 %s · 밴드 배율 κ %s%s" % (
                              r["변동오차"]["물량"], r["변동오차"]["단가"], r["복원오차"]["물량"], r["복원오차"]["단가"], r["판정"],
                              r["모수"].get("밴드배율", "-"), (" · 앞 %d기간은 정보가 없어 잘랐다" % len(r["앞자름"])) if r.get("앞자름") else "")})
        # 거친 바퀴 「통계 제안」 꼴 — 자리에 가정 줄 번호(A-n)를 적고 근거범위를 그 줄의 단위(비율)로. 판매단가 변동률 줄은 증가율 · 수준 경로가
        # 같이 쓰고, 판매량 줄은 증가율 경로에서만 증가율이다(수준 경로는 판매량 수준). 합계 경로는 그 줄이 서지 않는다
        딱 = 결과["제안"][-1]["딱지"]
        if r.get("번호") and r.get("경로") in ("증가율", "수준") and len(연) >= 2:
            줄 = _줄번호(r["번호"])
            for 쪽, 칸, 이름 in (("단가", 줄[1], "판매단가 변동률"), ("물량", 줄[0] if r["경로"] == "증가율" else None, "판매량 증가율")):
                if not 칸:
                    continue
                결과["제안"].append({"자리": "거친바퀴 — A-%d %s(구분 %d %s · 복원 연 변동 %s~%s)" % (칸, 이름, r["번호"], 품, 연[0]["해"], 연[-1]["해"]),
                                  "값": None, "근거범위": [min(x[쪽] for x in 연) / 100.0, max(x[쪽] for x in 연) / 100.0],
                                  "딱지": 딱, "확신": 확,
                                  "글": "복원한 회계연도 %s 변동(%d해)의 [최소, 최대] — 그 줄의 근거범위 후보이지 값이 아니다(지수 평균끼리의 연 변동)"
                                        % (이름, len(연))})
        if r.get("경로") == "증가율":
            알림("복원 가능 — 증가율 경로에서 올릴 수 있다", 품, r["판정"], "최소정보 %s" % S.get("최소정보"),
               "%s — 지금 증가율 경로인데 물량 · 단가 지수를 복원했다. 수준 · P×Q 경로로 세우고 근거 칸에 「%s」 와 복원 오차를 적을 수 있다(매출구분초안)"
               % (품, 결과["제안"][-1]["딱지"]))
        else:
            알림("P·Q 복원 — 근거범위 후보", 품, r["판정"], "최소정보 %s" % S.get("최소정보"),
               "%s — 복원한 연간 물량 · 단가 변동 %s 을 판매량 · 판가 줄의 근거범위 후보로 쓸 수 있다(거친 바퀴)" % (품, 범 or "-"))
        κ = r["모수"].get("밴드배율")
        if κ is not None and κ >= 헐:
            알림("밴드보다 헐거운 말", 품, κ, 헐, "%s — 표현 밴드의 분산을 %.1f배로 늘려야 실현 매출과 맞는다. 이 회사의 말은 사전 밴드보다 헐겁다(밴드사전 개정 후보)" % (품, κ))
        for h in [x for x in r["혁신"] if x["큼"]][:10]:
            알림("표현과 실현이 어긋나는 분기", "%s %s %s" % (품, h["기간"], h["지표"]), h["표준화혁신"], S.get("혁신문턱"),
               "%s %s %s 「%s」(%s) — 칼만 혁신이 표준화 %.2f 로 크다. 표현이 실현 매출 · 다른 항과 어긋난다(표현실현 짝검사와 같이 본다)"
               % (품, h["기간"], h["지표"], h.get("표현") or "-", h.get("채널") or "-", h["표준화혁신"]))
    if not [x for x in 결과["구분"] if x.get("판정") not in (None, "불가")]:
        결과["폴백"] = "⑥ 증가율 경로 그대로 — 복원으로 판정한 구분이 없다"
    return 결과


def 상태공간읽기(가정경로):
    """가정 곁 `_raw/상태공간.json` → dict 또는 None(매출구분초안 · 거친바퀴가 부른다)."""
    d, _p = _파일("상태공간.json", 가정경로)
    return d if isinstance(d, dict) else None


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="상태공간 — 칼만 P·Q 복원(기법 6)")
    ap.add_argument("가정")
    ap.add_argument("--단가통화", default="자동", choices=["자동", "원", "USD"])
    ap.add_argument("--빈도", default="자동", choices=["자동", "분기", "연간"])
    ap.add_argument("--분기매출")
    ap.add_argument("--대장")
    ap.add_argument("--환율")
    ap.add_argument("--대리")
    ap.add_argument("--설정")
    ap.add_argument("--낼")
    a = ap.parse_args(argv)
    try:
        가정 = json.load(io.open(a.가정, encoding="utf-8"))
        설 = 설정읽기(a.설정)
        for k in ("분기매출", "대장", "환율", "대리"):
            p = getattr(a, k)
            if p and not os.path.exists(p):
                raise IOError("%s 파일이 없다: %s" % (k, p))
    except (OSError, ValueError) as e:
        print("상태공간 입력 오류 — %s" % e)
        return 입력오류
    결과 = 실행(가정, a.가정, {"단가통화": a.단가통화, "빈도": a.빈도, "분기매출": a.분기매출, "대장": a.대장, "환율": a.환율, "대리": a.대리}, 설)
    낼 = a.낼 or os.path.join(os.path.dirname(os.path.abspath(a.가정)), "_raw", "상태공간.json")
    os.makedirs(os.path.dirname(낼), exist_ok=True)
    io.open(낼, "w", encoding="utf-8").write(json.dumps(결과, ensure_ascii=False, indent=1))
    print("상태공간 — 빈도 %s · 구분 %d · 제안 %d · 신호 %d%s → %s" % (
        (결과.get("입력") or {}).get("빈도", "-"), len(결과["구분"]), len(결과["제안"]), len(결과["신호"]),
        (" · 폴백: " + 결과["폴백"]) if 결과.get("폴백") else "", 낼))
    for x in 결과["구분"]:
        print("  %s — %s · 변동 오차 %s · 기간 %s ~ %s" % (x["매출구분"], x.get("판정"), {k: v for k, v in (x.get("변동오차") or {}).items() if k != "_뜻"},
                                                 (x.get("기간") or ["-"])[0], (x.get("기간") or ["-"])[-1]))
    return 통과


if __name__ == "__main__":
    sys.exit(main())

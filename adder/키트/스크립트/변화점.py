# -*- coding: utf-8 -*-
"""변화점 — 앵커 시계열의 구조적 변화점을 PELT 로 찾아 구조 블록 시작연도의 후보를 낸다 (기법 1 · 2026-10-21).

    python 스크립트/변화점.py 가정.json                       # → 가정 곁 _raw/변화점.json · 표를 찍는다
    python 스크립트/변화점.py 가정.json --낼 경로.json --설정 경로.json

왜 있나 — 구조 단절을 지금은 고정 배수로 짚는다: dart_원천.py 앵커 「구조단절후보」(매출이 전년의 3배 초과 · 1/3 미만) ·
자체검사 ⑱ `_현구조`(1 · 2 · 3해 누적 3.0 · 3.6 · 4.2배) · 영업이익 부호 전환. 두세 해에 걸친 합병 · 분할 · 사업 모형 전환, 마진의 계단식
이동은 그 문턱에 안 걸리고, 그러면 옛 회사의 관측이 정상화 평균과 원가율 범위에 섞인다. 이 도구는 같은 계열에 PELT(Killick · Fearnhead ·
Eckley 2012)를 걸어 변화점의 자리와 개수를 벌점 최적화로 함께 찾고 기존 휴리스틱과 나란히 적는다. **값을 쓰지 않는다** —
`관측.구조블록시작연도` 는 사람이 정한다(「앵커 표를 구조 블록으로 끊는다」). 이 도구는 후보 · 통계량 · 신호만 낸다.

계열 — `정상화.관측시계열`(관측 키 → 앵커 → A3 → 원천 13번 — 두 벌 짜지 않는다)의 해마다
    매출 증가율(로그 차분 — 전년 매출이 있는 해만) · 영업이익률 · A3(`_raw/동인원천.json`)가 있으면 매출 ÷ 유형자산 순장부
    (투하자본회전율 대용 — 무형 순장부는 공시 꼴이 회사마다 달라 뺀다. 회전율이 설정 최소 해보다 적으면 변수에서 뺀다)
표준화 — 변수마다 중앙값을 빼고 **차분의 MAD 로 잡음 크기를 잰다**(σ = MAD(Δx) ÷ (0.6745 · √2)). 수준이 한 번 옮겨 간 계열에서
    값 전체의 MAD 는 옮겨 간 폭까지 잡음으로 세어 변화점을 덮는다. 차분 MAD 가 0 이면 값의 MAD × 1.4826 → 표준편차 → 1 차례로 물러선다
비용 — 다변량 정규 평균 이동: 구간마다 변수별 (값 − 구간 평균)² 의 합(빈 칸은 그 변수에서만 뺀다). 벌점 β = 벌점배수 × (p + 1) × ln n
    (BIC 꼴 — 변화점 하나가 평균 p 개와 자리 하나를 더한다). 최소 구간 길이는 설정(2). PELT 의 가지치기(K = 0)는 정확해를 바꾸지 않는다
신뢰도 — 둘을 따로 적고 곱하지 않는다
    벌점생존 = 벌점을 격자(설정 — 0.5 · 1 · 2 · 4 배)로 바꿔 돌렸을 때 ±허용해 안에 그 변화점이 남는 비율
    확률 = 블록 부트스트랩 비율 — 주분석 구간 평균 + 잔차 행을 길이 `블록` 의 덩어리로 다시 뽑아(시드 고정 · `횟수` 번) 만든 계열에서
           ±허용해 안에 다시 잡힌 비율. **베이즈 사후확률이 아니라 「잡음을 다시 뽑아도 그 자리에 서는가」의 안정도다**
분류 — 변화점마다 가장 크게 옮겨 간 변수(표준화 폭)를 적는다. 사이클 회사(`정상화.사이클판정`)에서 이익률이나 증가율이 지배하는 변화점은
    「국면 전환 — 사이클의 일부」로 단다(이웃 변화점과 방향이 번갈아 확인되면 그렇다고, 하나뿐이면 「국면 전환일 수 있음」). 이 둘은 구조 블록
    시작 후보에서 뺀다 — 사이클의 저점은 다른 회사가 아니다. 그 밖은 「구조 변화 후보」
휴리스틱 대조 — 한해배수 · 누적배수(자체검사 `_현구조` 를 부른다 — 못 부르면 같은 자를 이 파일에서) · 영업이익 부호 전환을 같은 계열에
    돌려 해마다 「둘 다 · PELT 만 · 휴리스틱만」으로 적는다(±허용해)
폴백 — 해가 설정 최소(5)보다 적으면 계산하지 않고 「표본 부족 — 기존 규칙(고정 배수 · 부호 전환)을 그대로 쓴다」. 관측 시계열이 아예 없으면 「재료 없음」
내는 것 — 가정 곁 `_raw/변화점.json`
    {형식, 만든날, 설정, 입력, 폴백, 계열[{해, 매출, 매출증가율, 영업이익률, 회전율}], 변수, 척도,
     변화점[{연도, 확률, 벌점생존, 변수, 분류, 앞구간, 뒤구간, 평균이동, 표준화이동}], 변화점0안정도, 휴리스틱대조,
     구조블록시작연도_제안, 제안[], 신호[]}
    제안 자리 — `관측.구조블록시작연도`(가장 최근의 「구조 변화 후보」 가운데 확률 ≥ 확률문턱) · `정상화.구조단절후보`(구조 변화 후보마다)
    신호 종류 — 「변화점 — 휴리스틱이 못 잡음」(경보) · 「변화점 확률 낮음」 · 「국면 전환 — 구조 단절 아님」 · 「휴리스틱만 잡음」 · 「표본 부족」 · 「재료 없음」(참고)
읽기 — `변화점읽기(가정경로)` → {"구조블록시작연도": int | None, "변화점": [...], "폴백": 글 | None} · 파일이 없으면 None(정상화 · 거친바퀴가 부른다)
종료 코드 — 0 통과(경보 신호 없음) · 1 경보 신호 있음 · 2 입력 오류(가정 없음 · JSON 깨짐 · 설정 없음)
회사 · 업종 이름은 이 도구에 한 글자도 없다.
"""
import argparse
import datetime
import io
import json
import math
import os
import random
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, 여기)
import 정상화  # noqa: E402
from 종료코드 import 통과, 발견, 입력오류  # noqa: E402

설정곳 = os.path.join(여기, "시계열설정.json")
산출이름 = "변화점.json"


def _수(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def 설정읽기(p=None):
    return json.load(io.open(p or 설정곳, encoding="utf-8"))["변화점"]


def _중앙(v):
    s = sorted(v)
    n = len(s)
    if not n:
        return None
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def 잡음척도(값들):
    """차분의 MAD 로 잰 잡음 크기 — 수준 이동에 강건하다. 차분 MAD 가 0(같은 차분이 절반 넘게 되풀이 — 부동소수 잡음도 0 으로 본다)이면
    차분의 평균절대편차 ÷ (0.7979 · √2) → 값의 MAD × 1.4826 → 표준편차 → 1 차례로 물러선다."""
    v = [x for x in 값들 if x is not None]
    if not v:
        return 1.0, "1(값 없음)"
    영 = 1e-9 * max(1.0, max(abs(x) for x in v))
    d = [b - a for a, b in zip(v, v[1:])]
    if len(d) >= 2:
        m = _중앙(d)
        편 = [abs(x - m) for x in d]
        s = _중앙(편) / (0.6745 * math.sqrt(2.0))
        if s > 영:
            return s, "차분 MAD"
        s = (sum(편) / len(편)) / (0.7979 * math.sqrt(2.0))
        if s > 영:
            return s, "차분 평균절대편차"
    if len(v) >= 2:
        m = _중앙(v)
        s = _중앙([abs(x - m) for x in v]) * 1.4826
        if s > 영:
            return s, "값 MAD"
        mu = sum(v) / len(v)
        s = math.sqrt(sum((x - mu) ** 2 for x in v) / (len(v) - 1))
        if s > 영:
            return s, "표준편차"
    return 1.0, "1(흩어짐 없음)"


# ────────────────────────────────────────────────────────────── 계열

def 계열짓기(가정, 가정경로, 설정):
    """→ (행[], 변수[], 출처 글, A3 경로). 행 = {해, 매출, 매출증가율, 영업이익률, 회전율}."""
    시 = 정상화.관측시계열(가정, 가정경로)
    본 = {}
    for x in 시["해"]:
        if x.get("해") and x["해"] not in 본:
            본[x["해"]] = x
    해들 = [본[y] for y in sorted(본)]
    A3, A3곳 = 정상화.파일찾기("동인원천.json", 가정경로)
    순장부 = {}
    if isinstance(A3, dict):
        유 = A3.get("유형자산") if isinstance(A3.get("유형자산"), dict) else {}
        for c, v in ((유.get("순장부합계") if isinstance(유.get("순장부합계"), dict) else {}) or {}).items():
            if ("%s" % c).startswith("FY") and _수(v) and v > 0:
                순장부[정상화._해(c)] = float(v)
        for c, d in ((A3.get("재무시계열") if isinstance(A3.get("재무시계열"), dict) else {}) or {}).items():
            if ("%s" % c).startswith("FY") and isinstance(d, dict) and _수(d.get("유형자산")) and d["유형자산"] > 0:
                순장부.setdefault(정상화._해(c), float(d["유형자산"]))
    행 = []
    for i, x in enumerate(해들):
        y, r, m = x["해"], x.get("매출"), x.get("영업이익률")
        g = None
        if i > 0:
            p = 해들[i - 1]
            if p["해"] == y - 1 and _수(r) and r > 0 and _수(p.get("매출")) and p["매출"] > 0:
                g = math.log(r / p["매출"])
        t = (r / 순장부[y]) if (_수(r) and 순장부.get(y)) else None
        행.append({"해": y, "매출": r if _수(r) else None, "매출증가율": g, "영업이익률": m if _수(m) else None, "회전율": t})
    # 회전율 단위 맞춤(2026-10-24 W10 · 회차 20261024) — 매출(관측 시계열)과 유형자산 순장부(A3)의 금액 단위가 다르면 회전율이
    # 10^3 · 10^6 배로 찍혔다(「회전율 +246983」). 해들의 가운데 값이 [0.01, 100] 에 들도록 1,000 단위로 맞추고, 맞춘 뒤에도 그 밖인 해(투하자본이
    # 0 가까이 · 자본 잠식)는 회전율에서 뺀다. 판정 재료가 바뀌므로 출처 글에 적는다
    비 = sorted(r["회전율"] for r in 행 if _수(r["회전율"]) and r["회전율"] > 0)
    덧 = []
    if 비:
        가 = 비[len(비) // 2]
        배 = 1.0
        while 가 * 배 > 100 and 배 > 1e-12:
            배 /= 1000.0
        while 0 < 가 * 배 < 0.01 and 배 < 1e12:
            배 *= 1000.0
        if 배 != 1.0:
            덧.append("회전율 단위 맞춤 ×%g(매출과 유형자산의 금액 단위가 달랐다)" % 배)
        뺀 = 0
        for r in 행:
            if _수(r["회전율"]):
                v = r["회전율"] * 배
                if not (0 < v <= 100):
                    r["회전율"] = None
                    뺀 += 1
                else:
                    r["회전율"] = v
        if 뺀:
            덧.append("회전율 %d해 뺌(분모가 0 가까이 · 단위 맞춤 뒤에도 100 넘음)" % 뺀)
    변수 = ["매출증가율", "영업이익률"]
    if sum(1 for r in 행 if r["회전율"] is not None) >= int(설정.get("회전율최소해", 5)):
        변수.append("회전율")
    출 = 시.get("출처")
    if 덧:
        출 = ("%s · " % 출 if 출 else "") + " · ".join(덧)
    return 행, 변수, 출, A3곳


def 표준화(행, 변수):
    """→ (X[[값 또는 None]], 척도 {변수: {"중앙값", "척도", "방법"}})."""
    척도 = {}
    X = [[None] * len(변수) for _ in 행]
    for j, v in enumerate(변수):
        값 = [r[v] for r in 행]
        중 = _중앙([x for x in 값 if x is not None])
        s, 방법 = 잡음척도(값)
        척도[v] = {"중앙값": 중, "척도": s, "방법": 방법}
        for i, x in enumerate(값):
            X[i][j] = None if (x is None or 중 is None) else (x - 중) / s
    return X, 척도


# ────────────────────────────────────────────────────────────── PELT

def _비용함수(X):
    """구간 [a, b) 의 비용 — 변수별 (값 − 구간 평균)² 합(빈 칸 뺌). 누적합으로 O(1)."""
    n, p = len(X), (len(X[0]) if X else 0)
    S = [[0.0] * (n + 1) for _ in range(p)]
    Q = [[0.0] * (n + 1) for _ in range(p)]
    C = [[0] * (n + 1) for _ in range(p)]
    for j in range(p):
        for t in range(n):
            x = X[t][j]
            S[j][t + 1] = S[j][t] + (x if x is not None else 0.0)
            Q[j][t + 1] = Q[j][t] + (x * x if x is not None else 0.0)
            C[j][t + 1] = C[j][t] + (1 if x is not None else 0)

    def 비용(a, b):
        합 = 0.0
        for j in range(p):
            c = C[j][b] - C[j][a]
            if c:
                s = S[j][b] - S[j][a]
                합 += (Q[j][b] - Q[j][a]) - s * s / c
        return max(합, 0.0)
    return 비용


def pelt(X, 벌점, 최소구간=2):
    """PELT — 변화점 자리(새 구간의 첫 행 번호) 목록. 최소 구간 길이를 지킨다."""
    n = len(X)
    if n < 2 * 최소구간:
        return []
    비용 = _비용함수(X)
    F = {0: -벌점}
    앞 = {0: None}
    R = [0]
    for t in range(1, n + 1):
        후 = [(F[s] + 비용(s, t) + 벌점, s) for s in R if t - s >= 최소구간]
        if not 후:
            continue
        F[t], 앞[t] = min(후)
        R = [s for s in R if (t - s < 최소구간) or (F[s] + 비용(s, t) <= F[t])]
        R.append(t)
    if n not in F:
        return []
    점, t = [], n
    while 앞.get(t) not in (None, 0):
        점.append(앞[t])
        t = 앞[t]
    return sorted(점)


def 구간평균(X, 점):
    """변화점으로 가른 구간마다 변수별 평균 → 행마다 맞춘 값."""
    n, p = len(X), (len(X[0]) if X else 0)
    경계 = [0] + list(점) + [n]
    맞 = [[None] * p for _ in range(n)]
    for a, b in zip(경계, 경계[1:]):
        for j in range(p):
            v = [X[t][j] for t in range(a, b) if X[t][j] is not None]
            m = sum(v) / len(v) if v else None
            for t in range(a, b):
                맞[t][j] = m
    return 맞


def 부트스트랩(X, 점, 벌점, 최소구간, 횟수, 블록, 시드):
    """주분석 구간 평균 + 잔차 행 블록 재표집 → 횟수만큼 PELT. 계열마다의 변화점 목록[]."""
    rnd = random.Random(시드)
    n, p = len(X), (len(X[0]) if X else 0)
    맞 = 구간평균(X, 점)
    잔 = [[(X[t][j] - 맞[t][j]) if (X[t][j] is not None and 맞[t][j] is not None) else None for j in range(p)] for t in range(n)]
    블록 = max(1, min(int(블록), n))
    시작들 = list(range(0, n - 블록 + 1))
    낸 = []
    for _ in range(int(횟수)):
        새잔 = []
        while len(새잔) < n:
            s = rnd.choice(시작들)
            새잔.extend(잔[s:s + 블록])
        새잔 = 새잔[:n]
        Y = []
        for t in range(n):
            줄 = []
            for j in range(p):
                if X[t][j] is None or 맞[t][j] is None:
                    줄.append(None)
                else:
                    e = 새잔[t][j]
                    줄.append(맞[t][j] + (e if e is not None else 0.0))
            Y.append(줄)
        낸.append(pelt(Y, 벌점, 최소구간))
    return 낸


# ────────────────────────────────────────────────────────────── 휴리스틱

def 휴리스틱(행, 설정):
    """기존 자 셋 — {"한해배수": [새 구간 첫 해], "누적배수": 해 | None, "누적글", "부호전환": [해]}."""
    휴 = 설정.get("휴리스틱") or {}
    배수 = float(휴.get("한해배수", 3.0))
    한해 = []
    for a, b in zip(행, 행[1:]):
        if b["해"] == a["해"] + 1 and _수(a["매출"]) and _수(b["매출"]) and a["매출"] > 0 and b["매출"] > 0:
            r = b["매출"] / a["매출"]
            if r > 배수 or r < 1.0 / 배수:
                한해.append(b["해"])
    줄 = [(r["해"], None, r["매출"]) for r in 행 if _수(r["매출"]) and r["매출"] > 0]
    누적, 누적글 = None, None
    try:
        import 자체검사                                         # noqa: PLC0415 — ⑱ 의 자를 그대로 부른다
        _남, 끊 = 자체검사._현구조(줄)
        누적글 = "자체검사._현구조"
    except Exception:                                            # noqa: BLE001 — 못 부르면 같은 자를 여기서
        끊 = _현구조(줄, 휴.get("누적배수") or {})
        누적글 = "같은 자(이 파일) — 자체검사._현구조 를 못 불렀다"
    if 끊:
        누적 = int(끊[0])
    부호 = []
    이전 = None
    for r in 행:
        m = r["영업이익률"]
        if m is None:
            continue
        s = 1 if m >= 0 else -1
        if 이전 is not None and s != 이전[1]:
            부호.append(r["해"])
        이전 = (r["해"], s)
    return {"한해배수": 한해, "누적배수": 누적, "누적글": 누적글, "부호전환": 부호}


def _현구조(줄, 창문턱):
    """자체검사 ⑱ `_현구조` 와 같은 자 — 뒤에서부터 1 · 2 · 3해 누적 배수를 보고 창 안 가장 큰 한 걸음에서 끊는다. (해, 배, 꼬리) | None."""
    문 = {1: float(창문턱.get("1", 3.0)), 2: float(창문턱.get("2", 3.6)), 3: float(창문턱.get("3", 4.2))}
    for i in range(len(줄) - 1, 0, -1):
        for 창 in (1, 2, 3):
            j = i - 창
            if j < 0:
                break
            a, b = 줄[j][2], 줄[i][2]
            if not a or not b:
                continue
            배 = max(b / a, a / b)
            if 배 >= 문[창]:
                끊, 큰 = i, 0.0
                for k in range(j + 1, i + 1):
                    x, y = 줄[k - 1][2], 줄[k][2]
                    if x and y and max(y / x, x / y) > 큰:
                        큰, 끊 = max(y / x, x / y), k
                return (줄[끊][0], 배, "" if 창 == 1 else " (%d해에 걸쳐)" % 창)
    return None


# ────────────────────────────────────────────────────────────── 한 판

def 변화점표(가정, 가정경로=None, 설정=None):
    설정 = 설정 or 설정읽기()
    행, 변수, 출처, A3곳 = 계열짓기(가정, 가정경로, 설정)
    오늘 = datetime.date.today().isoformat()
    머리 = {"형식": "변화점 1", "만든날": 오늘, "설정": 설정,
          "입력": {"관측시계열": 출처, "동인원천": A3곳, "가정": os.path.abspath(가정경로) if 가정경로 else None}}
    if not 행:
        머리.update({"폴백": "재료 없음 — 관측 시계열(관측 키 · 앵커 · A3 · 원천 13번)이 없다", "계열": [], "변수": 변수, "척도": {}, "변화점": [],
                   "변화점0안정도": None, "휴리스틱대조": None, "구조블록시작연도_제안": None, "제안": [],
                   "신호": [{"출처": "변화점", "종류": "재료 없음", "대상": "관측 시계열", "값": 0, "문턱": int(설정["최소해"]),
                            "글": "관측 시계열이 없어 변화점을 재지 않았다 — 앵커(A1)나 A3 를 먼저 받는다", "등급": "참고"}]})
        return 머리
    휴 = 휴리스틱(행, 설정)
    n = len(행)
    if n < int(설정["최소해"]):
        머리.update({"폴백": "표본 부족 — 기존 규칙(고정 배수 · 부호 전환)을 그대로 쓴다 (%d해 < %d해)" % (n, int(설정["최소해"])),
                   "계열": 행, "변수": 변수, "척도": {}, "변화점": [], "변화점0안정도": None,
                   "휴리스틱대조": {"휴리스틱": 휴, "대조": []}, "구조블록시작연도_제안": None, "제안": [],
                   "신호": [{"출처": "변화점", "종류": "표본 부족", "대상": "관측 %d해" % n, "값": n, "문턱": int(설정["최소해"]),
                            "글": "관측이 %d해라 변화점을 재지 않았다 — 구조 단절은 기존 고정 배수 · 부호 전환 자로 본다" % n, "등급": "참고"}]})
        return 머리
    X, 척도 = 표준화(행, 변수)
    p = len(변수)
    β = float(설정["벌점배수"]) * (p + 1) * math.log(n)
    m = int(설정["최소구간"])
    허 = int(설정["허용해"])
    점 = pelt(X, β, m)
    해 = [r["해"] for r in 행]

    def _근처(y, 목록):
        return any(abs(y - z) <= 허 for z in 목록)

    격 = {}
    for g in 설정["벌점격자"]:
        격[g] = [해[i] for i in pelt(X, β * float(g), m)]
    부 = 설정["부트스트랩"]
    boots = 부트스트랩(X, 점, β, m, 부["횟수"], 부["블록"], 부["시드"])
    boot해 = [[해[i] for i in b] for b in boots]
    사이클 = (정상화.사이클판정(가정, 가정경로) or {}).get("사이클")
    맞 = 구간평균(X, 점)
    경계 = [0] + 점 + [n]
    변화 = []
    for k, c in enumerate(점):
        a, b = 경계[k], 경계[k + 2]
        이동, 표이동 = {}, {}
        for j, v in enumerate(변수):
            앞값 = [행[t][v] for t in range(a, c) if 행[t][v] is not None]
            뒤값 = [행[t][v] for t in range(c, b) if 행[t][v] is not None]
            if 앞값 and 뒤값:
                이동[v] = sum(뒤값) / len(뒤값) - sum(앞값) / len(앞값)
                표이동[v] = (맞[c][j] - 맞[c - 1][j]) if (맞[c][j] is not None and 맞[c - 1][j] is not None) else None
        지배 = max((v for v in 표이동 if 표이동[v] is not None), key=lambda v: abs(표이동[v]), default=None)
        y = 해[c]
        변화.append({"연도": y, "확률": round(sum(1 for b2 in boot해 if _근처(y, b2)) / float(len(boot해)), 3) if boot해 else None,
                   "벌점생존": round(sum(1 for g in 격 if _근처(y, 격[g])) / float(len(격)), 3),
                   "변수": 지배, "앞구간": [해[a], 해[c - 1]], "뒤구간": [해[c], 해[b - 1]],
                   "평균이동": {v: round(x, 6) for v, x in 이동.items()},
                   "표준화이동": {v: (round(x, 4) if x is not None else None) for v, x in 표이동.items()}})
    # 분류 — 사이클 회사에서 이익률 · 증가율이 지배하는 변화점은 국면 전환이다
    for k, x in enumerate(변화):
        v = x["변수"]
        if 사이클 and v in ("영업이익률", "매출증가율"):
            부호 = (x["표준화이동"].get(v) or 0) > 0
            이웃 = [변화[i] for i in (k - 1, k + 1) if 0 <= i < len(변화)]
            번갈 = any(((y["표준화이동"].get(v) or 0) > 0) != 부호 for y in 이웃 if y["표준화이동"].get(v) is not None)
            x["분류"] = "국면 전환 — 사이클의 일부" if 번갈 else "국면 전환일 수 있음 — 사이클 회사(한 번만 잡힘)"
        else:
            x["분류"] = "구조 변화 후보"
    없음안정 = round(sum(1 for b2 in boot해 if not b2) / float(len(boot해)), 3) if (not 점 and boot해) else None
    # 휴리스틱 대조
    휴해 = set(휴["한해배수"]) | ({휴["누적배수"]} if 휴["누적배수"] else set()) | set(휴["부호전환"])
    P해 = [x["연도"] for x in 변화]
    대조 = []
    for y in sorted(set(P해) | 휴해):
        pe = _근처(y, P해)
        hu = _근처(y, 휴해)
        대조.append({"연도": y, "PELT": pe, "한해배수": _근처(y, 휴["한해배수"]), "누적배수": bool(휴["누적배수"] and abs(y - 휴["누적배수"]) <= 허),
                   "부호전환": _근처(y, 휴["부호전환"]), "판정": "둘 다" if (pe and hu) else ("PELT 만" if pe else "휴리스틱만")})
    문 = float(설정["확률문턱"])
    구조후보 = [x for x in 변화 if x["분류"] == "구조 변화 후보"]
    믿을 = [x for x in 구조후보 if (x["확률"] or 0) >= 문]
    제안연 = 믿을[-1]["연도"] if 믿을 else None
    제안, 신호 = [], []
    if 제안연:
        x = 믿을[-1]
        제안.append({"자리": "관측.구조블록시작연도", "값": 제안연, "근거범위": None,
                   "딱지": "[계산 — PELT 변화점(확률 %.2f · 벌점생존 %.2f · %s)]" % (x["확률"], x["벌점생존"], x["변수"]),
                   "확신": x["확률"], "글": "%d 부터 새 구간 — %s 가 가장 크게 옮겨 갔다(%s). 진짜 구조 변화인지는 사람이 본다"
                   % (제안연, x["변수"], _이동글(x))})
    for x in 구조후보:
        제안.append({"자리": "정상화.구조단절후보", "값": "%d" % x["연도"], "근거범위": None,
                   "딱지": "[계산 — PELT 변화점(확률 %.2f)]" % (x["확률"] or 0), "확신": x["확률"],
                   "글": "앞 %d~%d · 뒤 %d~%d — %s" % (x["앞구간"][0], x["앞구간"][1], x["뒤구간"][0], x["뒤구간"][1], _이동글(x))})
    for x in 변화:
        휴잡 = _근처(x["연도"], 휴해 - set(휴["부호전환"]))
        if x["분류"] != "구조 변화 후보":
            신호.append({"출처": "변화점", "종류": "국면 전환 — 구조 단절 아님", "대상": "%d" % x["연도"], "값": x["확률"], "문턱": 문,
                        "글": "%d 의 변화점은 %s 이 지배한 국면 전환으로 본다(%s) — 구조 블록 시작 후보에서 뺐다" % (x["연도"], x["변수"], x["분류"]),
                        "등급": "참고"})
        elif (x["확률"] or 0) < 문:
            신호.append({"출처": "변화점", "종류": "변화점 확률 낮음", "대상": "%d" % x["연도"], "값": x["확률"], "문턱": 문,
                        "글": "%d 에 변화점이 잡혔지만 부트스트랩 확률 %.2f 가 문턱 %.2f 아래다 — 구조 블록을 끊는 근거로 쓰지 않는다" % (x["연도"], x["확률"] or 0, 문),
                        "등급": "참고"})
        elif not 휴잡:
            신호.append({"출처": "변화점", "종류": "변화점 — 휴리스틱이 못 잡음", "대상": "%d" % x["연도"], "값": x["확률"], "문턱": 문,
                        "글": "%d 에 구조 변화 후보(%s · 확률 %.2f)가 섰는데 고정 배수 자는 못 잡았다 — 그 앞 해가 같은 회사인지 보고 "
                             "`관측.구조블록시작연도` 를 정해 근거 칸에 적는다" % (x["연도"], _이동글(x), x["확률"]), "등급": "경보"})
    for y in sorted(휴해 - set(휴["부호전환"])):
        if not _근처(y, P해):
            신호.append({"출처": "변화점", "종류": "휴리스틱만 잡음", "대상": "%d" % y, "값": None, "문턱": "PELT ±%d해" % 허,
                        "글": "고정 배수 자는 %d 을 구조 단절 후보로 짚었는데 PELT 는 변화점을 세우지 않았다 — 한 해짜리 튐(부분 연도 · 일회성)일 수 있다" % y,
                        "등급": "참고"})
    머리.update({"폴백": None, "계열": 행, "변수": 변수, "척도": 척도, "벌점": round(β, 4), "변화점": 변화, "변화점0안정도": 없음안정,
               "사이클": 사이클, "휴리스틱대조": {"휴리스틱": 휴, "대조": 대조}, "구조블록시작연도_제안": 제안연, "제안": 제안, "신호": 신호})
    return 머리


def _이동글(x):
    return " · ".join("%s %+.3f" % (v, d) for v, d in (x.get("평균이동") or {}).items())


def 변화점읽기(가정경로):
    """정상화 · 거친바퀴가 부른다 — {"구조블록시작연도": int | None, "변화점": [...], "폴백": 글 | None} · 파일 없으면 None."""
    j, _p = 정상화.파일찾기(산출이름, 가정경로)
    if not isinstance(j, dict):
        return None
    return {"구조블록시작연도": j.get("구조블록시작연도_제안"), "변화점": j.get("변화점") or [], "폴백": j.get("폴백")}


def 표글(t):
    L = ["변화점(PELT) — %s · 변수 %s · 벌점 %s" % ((t.get("입력") or {}).get("관측시계열"), " · ".join(t.get("변수") or []), t.get("벌점"))]
    if t.get("폴백"):
        L.append("  폴백 — %s" % t["폴백"])
    for x in t.get("변화점") or []:
        L.append("  %d  확률 %.2f · 벌점생존 %.2f · %s · %s · 앞 %s 뒤 %s" % (x["연도"], x["확률"] or 0, x["벌점생존"], x["변수"], x["분류"],
                                                                     x["앞구간"], x["뒤구간"]))
    if not t.get("변화점") and not t.get("폴백"):
        L.append("  변화점 없음(안정도 %s)" % t.get("변화점0안정도"))
    for d in ((t.get("휴리스틱대조") or {}).get("대조") or []):
        L.append("  대조 %d — %s" % (d["연도"], d["판정"]))
    L.append("  구조블록시작연도 제안 — %s" % t.get("구조블록시작연도_제안"))
    for s in t.get("신호") or []:
        L.append("  [%s] %s — %s" % (s["등급"], s["종류"], s["글"]))
    return "\n".join(L)


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                            # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(allow_abbrev=False, description="변화점(PELT) — 구조 블록 시작연도 후보")
    ap.add_argument("가정")
    ap.add_argument("--낼", default=None)
    ap.add_argument("--설정", default=None)
    a = ap.parse_args(argv)
    try:
        가정 = json.load(io.open(a.가정, encoding="utf-8"))
        설정 = 설정읽기(a.설정)
    except (OSError, ValueError, KeyError) as e:
        print("변화점 — 입력 오류: %s" % e)
        return 입력오류
    t = 변화점표(가정, a.가정, 설정)
    밖 = a.낼 or os.path.join(os.path.dirname(os.path.abspath(a.가정)), "_raw", 산출이름)
    os.makedirs(os.path.dirname(밖), exist_ok=True)
    with io.open(밖, "w", encoding="utf-8", newline="\n") as f:
        json.dump(t, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(표글(t))
    print("→ %s" % 밖)
    return 발견 if any(s.get("등급") == "경보" for s in t.get("신호") or []) else 통과


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""국면 — 영업이익률 · 회전일수 뒤의 보이지 않는 국면(저점 · 중간 · 정점)을 가우스 HMM 으로 추정한다 (기법 2 · 2026-10-21).

    python 스크립트/국면.py 가정.json                       # → 가정 곁 _raw/국면.json · 표를 찍는다
    python 스크립트/국면.py 가정.json --낼 경로.json --설정 경로.json

왜 있나 — 지금 국면은 정해진 자로 가른다: A3 `동인원천.국면` · `정상화.사이클신호`(매출 증감 부호 전환 · 영업이익률 5%p 넘는 방향 전환이 둘 이상이고
폭 10%p 이상이면 사이클) · 영업이익률 사분위로 정점 · 저점 · 중간. 반기 누계 열이 정점 끝에 걸렸거나 사이클이 비대칭이면 사분위가 국면을
잘못 부른다(마지막 점이 가장 높으면 사분위는 늘 「정점」이고, 평가기준일이 정점이 아니어도 그렇다). 이 도구는 관측 뒤에 국면이 마르코프 연쇄로
바뀐다고 두고(은닉 마르코프 모형) 해마다 각 국면에 있을 평활 사후확률과 국면별 평균 · 분산을 낸다. **값을 쓰지 않는다** — 「정점 마진
영구화 금지」를 켤지, 비관 · 보조 시나리오의 하강 열에 무엇을 둘지는 사람이 정한다. 도구는 확률 · 근거범위 후보 · 신호만 낸다.

관측 — 해마다 영업이익률(`정상화.관측시계열` — 두 벌 짜지 않는다) + A3(`_raw/동인원천.json` 운전자본)의 매출채권 · 재고자산 · 매입채무 회전일수
    (A3 가 낸 값 그대로 — 반기 열은 A3 가 연환산했다). 마지막 회계연도 뒤의 반기 · 분기 누계 열(A3 운전자본, 없으면 원천 13번 62 · 66)이 있으면
    **그 열을 마지막 점**으로 넣는다 — 영업이익률은 비율이라 연환산하지 않는다(계절성은 남는다 — 그 사실을 `입력.마지막점` 에 적는다).
    변수마다 중앙값 · MAD × 1.4826 으로 표준화(0 이면 표준편차 → 1)
모형 — 국면 2 · 3 개의 가우스 HMM(대각 공분산 · 빈 칸은 그 변수만 뺀다). Baum-Welch(EM — 시작 여러 개 · 시드 고정 · 분산 하한)로 적합하고
    척도 붙인 전진후진으로 평활 사후확률을 낸다. 국면 이름은 국면별 영업이익률 평균 순서 — 2국면이면 저점 · 정점, 3국면이면 저점 · 중간 · 정점.
    BIC(−2 로그우도 + 모수 수 × ln n)로 고르고 둘 다 적는다. 점이 국면 수의 최소(설정 — 2국면 6 · 3국면 8)보다 적으면 그 국면 수는 폴백이다.
    **2국면이면 정점과 중간이 한 국면에 섞인다** — 「평가기준일 정점」 경보는 마지막 점의 영업이익률이 정점 국면 평균 이상일 때만 내고(설정
    `2국면정점조건`), 아니면 「2국면이라 정점 · 중간을 못 가름」 참고로 내린다
국면별 — 국면마다 사후확률 무게의 평균 · 표준편차(원 단위). **불리한 끝** = 평균 ± z · 표준편차(z 는 설정) — 영업이익률 · 매입채무는 아래, 매출채권 ·
    재고는 위. 저점 국면의 불리한 끝이 비관 · 보조(골 · 회복) 시나리오 하강 열의 **근거범위 후보**다(자체검사 ㊺ — 가정에 쓰지 않는다)
기존 자 대조 — `정상화.사이클신호`(A3 국면과 같은 자)와 사분위 국면(동인원천.국면 의 q1 = 값[n // 4] · q3 = 값[3n // 4])을 같은 해에 나란히 적고,
    HMM 이 가장 그럴듯하다고 본 국면과 갈리는 해를 센다
폴백 — 2국면도 못 하면 계산하지 않고 「표본 부족 — 기존 규칙(사이클 신호 · 영업이익률 사분위)을 그대로 쓴다」. 관측이 아예 없으면 「재료 없음」
내는 것 — 가정 곁 `_raw/국면.json`
    {형식, 만든날, 설정, 입력, 폴백, 관측[{해, 열, 영업이익률, 회전일수…}], 모형{"2": {...}, "3": {...}}, 선택, 해[{해, 열, 국면확률, 가장그럴듯한}],
     평가기준일국면{국면: p}, 국면별{국면: {영업이익률: {평균, sd, 불리한끝}, 회전일수별 …}}, 기존자대조, 제안[], 신호[]}
    제안 자리 — `정상화.정점영구화금지`(평가기준일 정점 확률 ≥ 정점문턱) · `A-178 · A-182 · A-186 비관 시나리오 회전일수 하강 열`(저점 국면 불리한 끝 — 근거범위 후보)
    신호 종류 — 「평가기준일이 정점 국면일 확률 높음」(경보) · 「정점 국면 확률 높음 — 2국면이라 정점 · 중간을 못 가름」 · 「기존 자와 국면 판정이 다름」 ·
    「표본 부족」 · 「재료 없음」(참고)
읽기 — `국면읽기(가정경로)` → {"선택": 국면 수, "평가기준일국면": {...}, "국면별": {...}, "해": [...], "폴백": 글 | None} · 파일이 없으면 None
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
import re
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, 여기)
import 정상화  # noqa: E402
from 종료코드 import 통과, 발견, 입력오류  # noqa: E402

설정곳 = os.path.join(여기, "시계열설정.json")
산출이름 = "국면.json"
_누계 = re.compile(r"^([1-4])Q(\d{2})A$|^([12])H(\d{2})A$")


def _수(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def 설정읽기(p=None):
    return json.load(io.open(p or 설정곳, encoding="utf-8"))["국면"]


def _중앙(v):
    s = sorted(v)
    n = len(s)
    if not n:
        return None
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def _누계해(c):
    """반기 · 분기 누계 열 이름 → (해, 순서) 또는 None. 「1H26A」 → (2026, 6) · 「3Q26A」 → (2026, 9)."""
    m = _누계.match("%s" % c)
    if not m:
        return None
    if m.group(1):
        return 2000 + int(m.group(2)), 3 * int(m.group(1))
    return 2000 + int(m.group(4)), 6 * int(m.group(3))


# ────────────────────────────────────────────────────────────── 관측

def _점말(가정):
    """마지막 관측 점의 이름 — 관측(영업이익률 · 회전일수)은 재무 자료라 끝이 재무기준일 F 다(2026-10-25 날짜 둘).
    F 가 평가기준일과 다르면 「재무기준일 점」, 같거나 없으면 「평가기준일 점」(옛 글 그대로). 신호 종류 이름 · 산출 열쇠(`평가기준일국면`)는 바꾸지 않는다."""
    try:
        import 기준일 as _기                                  # noqa: PLC0415
        r = _기.기준일들(가정)
        if not r.get("오류") and not r.get("같음"):
            return "재무기준일 점"
    except Exception:                                        # noqa: BLE001
        pass
    return "평가기준일 점"


def 관측짓기(가정, 가정경로, 설정):
    """→ (관측[{해, 열, 영업이익률, <회전일수>}], 변수[], 입력 dict)."""
    시 = 정상화.관측시계열(가정, 가정경로)
    본 = {}
    for x in 시["해"]:
        if x.get("해") and _수(x.get("영업이익률")) and x["해"] not in 본:
            본[x["해"]] = x["영업이익률"]
    A3, A3곳 = 정상화.파일찾기("동인원천.json", 가정경로)
    운 = ((A3.get("운전자본") or {}) if isinstance(A3, dict) else {}) or {}
    회전 = {}
    for v in 설정["회전일수"]:
        d = 운.get(v)
        if isinstance(d, dict):
            회전[v] = {c: float(x) for c, x in d.items() if _수(x)}
    관 = [{"해": y, "열": "FY%dA" % y, "영업이익률": 본[y]} for y in sorted(본)]
    for 행 in 관:
        for v, d in 회전.items():
            행[v] = d.get(행["열"]) if 행["열"] in d else d.get("FY%d" % 행["해"])
    # 마지막 회계연도 뒤의 누계 열 — A3 운전자본 → 원천 13번 62 · 66
    마지막점 = None
    끝해 = 관[-1]["해"] if 관 else None
    후보 = []
    a3마 = 운.get("영업이익률") if isinstance(운.get("영업이익률"), dict) else {}
    for c, x in a3마.items():
        k = _누계해(c)
        if k and _수(x) and 끝해 is not None and k[0] > 끝해:
            후보.append((k, c, float(x), "A3 운전자본.영업이익률"))
    if not 후보:
        원 = 가정.get("원천") or {}
        매, 영 = 원.get("62") or {}, 원.get("66") or {}
        for c, r in (매.items() if isinstance(매, dict) else []):
            k = _누계해(c)
            o = 영.get(c) if isinstance(영, dict) else None
            if k and _수(r) and r and _수(o) and 끝해 is not None and k[0] > 끝해:
                후보.append((k, c, float(o) / float(r), "원천 13번 66 ÷ 62"))
    if 후보:
        k, c, m, 곳 = max(후보)
        행 = {"해": k[0] + (k[1] / 12.0 - 1.0 if k[1] < 12 else 0.0), "열": c, "영업이익률": m}
        for v, d in 회전.items():
            행[v] = d.get(c)
        관.append(행)
        마지막점 = "%s(%s) — 누계 열을 마지막 점으로 넣었다. 영업이익률은 비율이라 연환산하지 않았다(계절성은 남는다)" % (c, 곳)
    변수 = ["영업이익률"] + [v for v in 설정["회전일수"]
                       if v in 회전 and sum(1 for r in 관 if _수(r.get(v))) >= int(설정.get("회전일수최소점", 4))]
    입력 = {"관측시계열": 시.get("출처"), "동인원천": A3곳, "가정": os.path.abspath(가정경로) if 가정경로 else None, "마지막점": 마지막점}
    return 관, 변수, 입력, 시


def 표준화(관, 변수):
    척도 = {}
    Z = []
    for v in 변수:
        값 = [r[v] for r in 관 if _수(r.get(v))]
        중 = _중앙(값)
        영 = 1e-9 * max([1.0] + [abs(x) for x in 값])        # 부동소수 잡음은 0 으로 본다
        s = _중앙([abs(x - 중) for x in 값]) * 1.4826 if 값 else 0.0
        방법 = "MAD"
        if s <= 영 and len(값) >= 2:
            mu = sum(값) / len(값)
            s = math.sqrt(sum((x - mu) ** 2 for x in 값) / (len(값) - 1))
            방법 = "표준편차"
        if s <= 영:
            s, 방법 = 1.0, "1(흩어짐 없음)"
        척도[v] = {"중앙값": 중, "척도": s, "방법": 방법}
    for r in 관:
        Z.append([((r[v] - 척도[v]["중앙값"]) / 척도[v]["척도"]) if _수(r.get(v)) else None for v in 변수])
    return Z, 척도


# ────────────────────────────────────────────────────────────── 가우스 HMM

def _로그방출(z, μ, σ2):
    합 = 0.0
    for x, m, v in zip(z, μ, σ2):
        if x is not None:
            합 += -0.5 * (math.log(2 * math.pi * v) + (x - m) ** 2 / v)
    return 합


def 전진후진(Z, π, A, μ, σ2):
    """척도 붙인 전진후진 → (로그우도, γ[t][k], ξ합[j][k])."""
    n, K = len(Z), len(π)
    logB = [[_로그방출(Z[t], μ[k], σ2[k]) for k in range(K)] for t in range(n)]
    B, 밀 = [], []
    for t in range(n):
        m = max(logB[t])
        밀.append(m)
        B.append([math.exp(x - m) for x in logB[t]])
    α = [[0.0] * K for _ in range(n)]
    c = [0.0] * n
    for k in range(K):
        α[0][k] = π[k] * B[0][k]
    c[0] = sum(α[0]) or 1e-300
    α[0] = [x / c[0] for x in α[0]]
    for t in range(1, n):
        for k in range(K):
            α[t][k] = sum(α[t - 1][j] * A[j][k] for j in range(K)) * B[t][k]
        c[t] = sum(α[t]) or 1e-300
        α[t] = [x / c[t] for x in α[t]]
    β = [[1.0] * K for _ in range(n)]
    for t in range(n - 2, -1, -1):
        for j in range(K):
            β[t][j] = sum(A[j][k] * B[t + 1][k] * β[t + 1][k] for k in range(K)) / c[t + 1]
    γ = []
    for t in range(n):
        g = [α[t][k] * β[t][k] for k in range(K)]
        s = sum(g) or 1e-300
        γ.append([x / s for x in g])
    ξ = [[0.0] * K for _ in range(K)]
    for t in range(n - 1):
        for j in range(K):
            for k in range(K):
                ξ[j][k] += α[t][j] * A[j][k] * B[t + 1][k] * β[t + 1][k] / c[t + 1]
    로그우도 = sum(math.log(x) for x in c) + sum(밀)
    return 로그우도, γ, ξ


def 적합(Z, K, 설정, 시드):
    """Baum-Welch — 시작 여러 개 중 로그우도가 가장 큰 판. {"π", "A", "μ", "σ2", "로그우도", "γ", "반복"}."""
    n, D = len(Z), (len(Z[0]) if Z else 0)
    rnd = random.Random(시드)
    하한 = float(설정["분산하한"])
    사전 = float(설정["전이사전"])
    대각 = float(설정["전이초기대각"])
    최선 = None
    for _ in range(int(설정["시작"])):
        고른 = rnd.sample(range(n), K)
        μ = [[(Z[i][d] if Z[i][d] is not None else 0.0) + rnd.gauss(0, 0.1) for d in range(D)] for i in 고른]
        σ2 = [[1.0] * D for _ in range(K)]
        π = [1.0 / K] * K
        A = [[대각 if i == j else (1 - 대각) / (K - 1) for j in range(K)] for i in range(K)]
        전 = -float("inf")
        반 = 0
        for 반 in range(1, int(설정["반복"]) + 1):
            ll, γ, ξ = 전진후진(Z, π, A, μ, σ2)
            π = [(γ[0][k] + 1e-6) for k in range(K)]
            s = sum(π)
            π = [x / s for x in π]
            for j in range(K):
                행합 = sum(ξ[j]) + 사전 * K
                A[j] = [(ξ[j][k] + 사전) / 행합 for k in range(K)]
            for k in range(K):
                for d in range(D):
                    w = [(γ[t][k], Z[t][d]) for t in range(n) if Z[t][d] is not None]
                    sw = sum(a for a, _ in w)
                    if sw > 1e-12:
                        m = sum(a * x for a, x in w) / sw
                        μ[k][d] = m
                        σ2[k][d] = max(sum(a * (x - m) ** 2 for a, x in w) / sw, 하한)
            if ll - 전 < float(설정["수렴"]):
                break
            전 = ll
        ll, γ, _ξ = 전진후진(Z, π, A, μ, σ2)
        if 최선 is None or ll > 최선["로그우도"] + 1e-12:
            최선 = {"π": π, "A": [list(r) for r in A], "μ": [list(r) for r in μ], "σ2": [list(r) for r in σ2], "로그우도": ll, "γ": γ, "반복": 반}
    # 국면 이름 — 영업이익률(첫 변수) 평균 순서
    차례 = sorted(range(K), key=lambda k: 최선["μ"][k][0])
    이름 = ["저점", "정점"] if K == 2 else ["저점", "중간", "정점"]
    최선["이름"] = {차례[i]: 이름[i] for i in range(K)}
    모수 = (K - 1) + K * (K - 1) + 2 * K * D
    최선["BIC"] = -2 * 최선["로그우도"] + 모수 * math.log(n)
    최선["모수"] = 모수
    return 최선


# ────────────────────────────────────────────────────────────── 한 판

def _가중(값, 무게):
    짝 = [(w, x) for w, x in zip(무게, 값) if _수(x)]
    sw = sum(w for w, _ in 짝)
    if sw <= 1e-12:
        return None, None
    m = sum(w * x for w, x in 짝) / sw
    v = sum(w * (x - m) ** 2 for w, x in 짝) / sw
    return m, math.sqrt(v)


def 국면표(가정, 가정경로=None, 설정=None):
    설정 = 설정 or 설정읽기()
    관, 변수, 입력, 시 = 관측짓기(가정, 가정경로, 설정)
    머리 = {"형식": "국면 1", "만든날": datetime.date.today().isoformat(), "설정": 설정, "입력": 입력}
    n = len(관)
    최소 = {int(k): int(v) for k, v in 설정["국면별최소점"].items()}
    빈 = {"관측": 관, "변수": 변수, "모형": {}, "선택": None, "해": [], "평가기준일국면": None, "국면별": {}, "기존자대조": None, "제안": []}
    if not 관:
        머리.update(빈)
        머리.update({"폴백": "재료 없음 — 관측 시계열(관측 키 · 앵커 · A3 · 원천 13번)이 없다",
                   "신호": [{"출처": "국면", "종류": "재료 없음", "대상": "관측 시계열", "값": 0, "문턱": min(최소.values()),
                            "글": "영업이익률 관측이 없어 국면을 재지 않았다 — 앵커(A1)나 A3 를 먼저 받는다", "등급": "참고"}]})
        return 머리
    가능 = [K for K in 설정["국면수"] if n >= 최소.get(int(K), 99)]
    if not 가능:
        머리.update(빈)
        머리.update({"폴백": "표본 부족 — 기존 규칙(사이클 신호 · 영업이익률 사분위)을 그대로 쓴다 (%d점 < %d점)" % (n, min(최소.values())),
                   "신호": [{"출처": "국면", "종류": "표본 부족", "대상": "관측 %d점" % n, "값": n, "문턱": min(최소.values()),
                            "글": "관측이 %d점이라 국면 모형을 세우지 않았다 — 국면은 기존 사이클 신호 · 사분위 자로 본다" % n, "등급": "참고"}]})
        return 머리
    Z, 척도 = 표준화(관, 변수)
    모형 = {}
    for K in 설정["국면수"]:
        if int(K) not in 가능:
            모형[str(K)] = {"폴백": "표본 부족 — %d국면은 %d점 이상(지금 %d점)" % (K, 최소[int(K)], n)}
            continue
        f = 적합(Z, int(K), 설정, int(설정["시드"]))
        모형[str(K)] = {"로그우도": round(f["로그우도"], 4), "BIC": round(f["BIC"], 4), "모수": f["모수"], "반복": f["반복"],
                       "국면": {f["이름"][k]: {"평균(표준화)": [round(x, 4) for x in f["μ"][k]], "분산(표준화)": [round(x, 4) for x in f["σ2"][k]]}
                              for k in range(int(K))},
                       "전이": {f["이름"][j]: {f["이름"][k]: round(f["A"][j][k], 4) for k in range(int(K))} for j in range(int(K))},
                       "_f": f}
    고 = min((k for k in 모형 if "_f" in 모형[k]), key=lambda k: 모형[k]["BIC"])
    f = 모형[고]["_f"]
    K = int(고)
    해 = []
    for t, r in enumerate(관):
        p = {f["이름"][k]: round(f["γ"][t][k], 4) for k in range(K)}
        해.append({"해": r["해"], "열": r["열"], "국면확률": p, "가장그럴듯한": max(p, key=p.get)})
    평가 = dict(해[-1]["국면확률"])
    국면별 = {}
    for k in range(K):
        w = [f["γ"][t][k] for t in range(n)]
        칸 = {"무게": round(sum(w), 4)}
        for v in ["영업이익률"] + [x for x in 설정["회전일수"] if x in 변수]:
            m, sd = _가중([r.get(v) for r in 관], w)
            if m is None:
                continue
            쪽 = (설정.get("불리한쪽") or {}).get(v, "아래")
            z = float(설정["불리한끝z"])
            끝 = m + z * sd if 쪽 == "위" else m - z * sd
            칸[v] = {"평균": round(m, 6), "sd": round(sd, 6), "불리한끝": round(끝, 6), "불리한쪽": 쪽}
        국면별[f["이름"][k]] = 칸
    # 기존 자 대조 — 사이클 신호 · 사분위
    fy = [r for r in 관 if ("%s" % r["열"]).startswith("FY")]
    신호기존 = 정상화.사이클신호([{"해": r["해"], "영업이익률": r["영업이익률"], "매출": next((x.get("매출") for x in 시["해"] if x.get("해") == r["해"]), None)}
                          for r in fy])
    값 = sorted(r["영업이익률"] for r in fy)
    사분 = []
    다름 = []
    if len(값) >= 4:
        q1, q3 = 값[len(값) // 4], 값[(3 * len(값)) // 4]
        for r, h in zip(관, 해):
            이름 = "저점" if r["영업이익률"] <= q1 else ("정점" if r["영업이익률"] >= q3 else "중간")
            사분.append({"열": r["열"], "사분위": 이름, "HMM": h["가장그럴듯한"]})
            if 이름 != h["가장그럴듯한"] and not (K == 2 and 이름 == "중간"):
                다름.append(r["열"])
    A3국면 = 시.get("국면") or []
    기존 = {"사이클신호": 신호기존, "사분위": 사분, "다른열": 다름,
          "A3국면": [{"기간": x.get("기간"), "이름": x.get("이름")} for x in A3국면 if isinstance(x, dict)]}
    제안, 신호 = [], []
    정점p = 평가.get("정점", 0.0)
    문 = float(설정["정점문턱"])
    점말 = _점말(가정)                                       # 마지막 관측 점 — 재무 관측이라 날짜 둘이면 「재무기준일 점」
    딱 = "[계산 — 국면 HMM(%d국면 · 평활 사후확률 · BIC 선택)]" % K
    # 2국면이면 정점과 중간이 한 국면에 섞인다 — 마지막 점이 정점 국면 평균 이상일 때만 「정점」 경보로 읽는다(설정 `2국면정점조건`)
    정점조건, 조건글 = True, ""
    if K == 2:
        정 = (국면별.get("정점") or {}).get("영업이익률") or {}
        마 = 관[-1]["영업이익률"]
        정점조건 = bool(정) and 마 >= 정["평균"]
        조건글 = "2국면 모형 — 정점과 중간이 한 국면에 섞인다. 마지막 점 영업이익률 %.1f%% · 정점 국면 평균 %.1f%%" % (
            마 * 100, (정.get("평균") or 0) * 100)
    if 정점p >= 문 and not 정점조건:
        신호.append({"출처": "국면", "종류": "정점 국면 확률 높음 — 2국면이라 정점 · 중간을 못 가름", "대상": 관[-1]["열"], "값": 정점p, "문턱": 문,
                    "글": "%s — 마지막 점이 정점 국면 평균 아래라 정점 경보로 읽지 않는다(3국면은 %d점 이상)" % (조건글, 최소.get(3, 8)),
                    "등급": "참고"})
    if 정점p >= 문 and 정점조건:
        제안.append({"자리": "정상화.정점영구화금지", "값": True, "근거범위": None, "딱지": 딱, "확신": 정점p,
                   "글": "%s(%s)이 정점 국면일 확률 %.2f — 영구가치 규칙 — 정점 마진 영구화 금지(정상화 계단)를 켤지 사람이 정한다" % (점말, 관[-1]["열"], 정점p)})
        신호.append({"출처": "국면", "종류": "평가기준일이 정점 국면일 확률 높음", "대상": 관[-1]["열"], "값": 정점p, "문턱": 문,
                    "글": "%s(%s)이 정점 국면일 확률이 %.2f 다%s — 마지막 해 마진을 영구화하지 말고 정상화 계단의 근거 칸에 이 확률을 적는다"
                         % (점말, 관[-1]["열"], 정점p, (" (%s — 마지막 점이 그 평균 이상)" % 조건글) if 조건글 else ""), "등급": "경보"})
    저 = 국면별.get("저점") or {}
    for v in [x for x in 설정["회전일수"] if x in 변수]:
        if v in 저:
            번 = (설정.get("회전일수가정번호") or {}).get(v, "?")
            lo, hi = sorted([저[v]["평균"], 저[v]["불리한끝"]])
            if hi - lo <= 1e-9 * max(1.0, abs(hi)):            # 2026-10-21 시운전 — 저점 국면 무게가 한 점에 몰려 sd 0 이면 폭 0 범위가 손잡이를 0 으로 민다
                신호.append({"출처": "국면", "종류": "저점 국면 폭 없음 — 근거범위를 내지 않음", "대상": "A-%s %s" % (번, v), "값": 저[v]["평균"], "문턱": 0,
                            "글": "저점 국면의 %s 가 사실상 한 점(%.1f일 · sd 0)이라 범위를 못 낸다 — 비관 하강 열은 실적 범위(E · ㊺)로 본다" % (v, 저[v]["평균"]),
                            "등급": "참고"})
                continue
            제안.append({"자리": "A-%s %s · 비관 시나리오 하강 열" % (번, v), "값": 저[v]["불리한끝"], "근거범위": [round(lo, 4), round(hi, 4)],
                       "딱지": "[계산 — 국면 HMM 저점 국면(평균 %s z · sd)]" % ("+" if 저[v]["불리한쪽"] == "위" else "−"),
                       "확신": round(저.get("무게", 0.0) / float(n), 4),
                       "글": "저점 국면의 %s 평균 %.1f일 · 불리한 끝 %.1f일 — 가정에 쓰지 않는다. 비관 · 보조(골 · 회복) 하강 열의 근거범위 후보(㊺)"
                            % (v, 저[v]["평균"], 저[v]["불리한끝"])})
    if 다름:
        신호.append({"출처": "국면", "종류": "기존 자와 국면 판정이 다름", "대상": " · ".join(다름), "값": len(다름), "문턱": 0,
                    "글": "영업이익률 사분위 자와 HMM 이 가장 그럴듯하다고 본 국면이 %d개 열(%s)에서 갈린다 — 국면별 범위(E · ㊺)를 볼 때 둘을 함께 본다"
                         % (len(다름), " · ".join(다름)), "등급": "참고"})
    for k in list(모형):
        모형[k].pop("_f", None)
    머리.update({"폴백": None, "관측": 관, "변수": 변수, "척도": 척도, "모형": 모형, "선택": K, "해": 해, "평가기준일국면": 평가,
               "국면별": 국면별, "기존자대조": 기존, "제안": 제안, "신호": 신호})
    return 머리


def 국면읽기(가정경로):
    """{"선택", "평가기준일국면", "국면별", "해", "폴백"} · 파일이 없으면 None."""
    j, _p = 정상화.파일찾기(산출이름, 가정경로)
    if not isinstance(j, dict):
        return None
    return {k: j.get(k) for k in ("선택", "평가기준일국면", "국면별", "해", "폴백")}


def 표글(t):
    L = ["국면(HMM) — %s · 변수 %s · 선택 %s국면" % ((t.get("입력") or {}).get("관측시계열"), " · ".join(t.get("변수") or []), t.get("선택"))]
    if t.get("폴백"):
        L.append("  폴백 — %s" % t["폴백"])
    if (t.get("입력") or {}).get("마지막점"):
        L.append("  마지막 점 — %s" % t["입력"]["마지막점"])
    for k, m in (t.get("모형") or {}).items():
        L.append("  %s국면 — %s" % (k, m.get("폴백") or "로그우도 %s · BIC %s" % (m.get("로그우도"), m.get("BIC"))))
    for h in t.get("해") or []:
        L.append("  %-7s %s · %s" % (h["열"], h["가장그럴듯한"], " · ".join("%s %.2f" % (a, b) for a, b in h["국면확률"].items())))
    for s in t.get("신호") or []:
        L.append("  [%s] %s — %s" % (s["등급"], s["종류"], s["글"]))
    return "\n".join(L)


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                            # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(allow_abbrev=False, description="국면(HMM) — 평가기준일 국면 확률 · 국면별 범위")
    ap.add_argument("가정")
    ap.add_argument("--낼", default=None)
    ap.add_argument("--설정", default=None)
    a = ap.parse_args(argv)
    try:
        가정 = json.load(io.open(a.가정, encoding="utf-8"))
        설정 = 설정읽기(a.설정)
    except (OSError, ValueError, KeyError) as e:
        print("국면 — 입력 오류: %s" % e)
        return 입력오류
    t = 국면표(가정, a.가정, 설정)
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

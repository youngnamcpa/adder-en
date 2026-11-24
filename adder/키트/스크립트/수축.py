# -*- coding: utf-8 -*-
"""수축 — 경험적 베이즈(Empirical Bayes) 수축으로 짧은 자체 시계열의 탄력성 · 비율을 동종 분포 쪽으로 당긴다 (기법 3 · 2026-10-21).

    python 스크립트/수축.py 가정.json                    # → 가정 곁 _raw/수축.json · 표를 찍는다
    python 스크립트/수축.py 가정.json --낼 경로.json --설정 수축연결설정.json

무엇 — E 비용동인(`_raw/동인진단.json`)이 노드마다 잰 매출 탄력성 b(Δln 비용 = a + b · Δln 매출 — `동인진단.탄력성` 과 같은 식)와
       운전자본 판단 칸의 실적 회전일수, 회사 수준 비율(매출총이익률 · 판관비율 · 매출대비CAPEX)을 **동종(C2 운영 동종)의 같은 지표 분포**와
       합쳐 사후 분포를 낸다.
         사전  동종 회사마다의 추정 b_i(표준오차 s_i) → 회사 간 분산 τ² = DerSimonian–Laird 모멘트법(음수면 0) · 평균 μ = 1/(s²+τ²) 가중.
               표준오차가 없는 동종이 섞이면 τ² = 표본 분산(회사 안 잡음이 섞여 사전이 넓어진다 — 수축이 약해지는 쪽, 안전한 쪽)
         자체  b̂ · σ(표준오차). 쌍이 둘뿐이면 동종 잔차 표준편차를 빌려 σ = s_pool ÷ √Sxx (「표준오차 차용」).
               비율은 해들의 평균 · 표준오차 — 이웃한 해의 자기상관 ρ 가 양이면 유효관측 n(1 − ρ)/(1 + ρ) 로 나눈다(사이클 회사)
         사후  B = σ² ÷ (σ² + τ²) · 평균 = B·μ + (1 − B)·b̂ · sd = √((1 − B)·σ²) · 90% 신용구간 = 평균 ± z·sd
       표본이 길고 σ 가 작으면 자체로 수렴하고(B → 0), 짧고 σ 가 크면 동종 쪽으로 간다(B → 1).
왜 — E 는 주석 시계열이 5~6해라 탄력성 90% 구간이 −0.2 ~ +1.4 처럼 넓어 「구간이 넓어 가르지 못함」(판정 보류)으로 물러나고 성격 사전 · 유추로 간다.
     동종이 같은 기능의 탄력성을 여러 해 보여 주면 그 분포가 사전이다. **값을 쓰지 않는다** — 판단 칸의 근거범위 후보 · 보조 산식 비중(A-7k4)의
     근거 · 판정이 바뀌는지의 신호만 낸다. 동종 사전은 노드와 정의가 다른 기능별(매출원가 · 판관비 · 연구개발비) 탄력성이라 근거강도는 「유추」다.
읽는 것 — 가정 곁 `_raw/` (`정상화.파일찾기` 차례): 동인진단.json · peers/운영지표_*.json(없으면 가정 `관측.운영동종`) · 동인원천.json(자체 비율 ·
           매출 시계열) · 투자능력.json(CAPEX비율) · 가정 원천 13번(62 매출 · 63 매출원가 · 65 판관비 — 마지막 물러섬)
내는 것 — `_raw/수축.json`: 형식 · 만든날 · 설정 · 입력 · 폴백 · 사전 · 항목 · 제안 · 신호
           신호 종류: 「자체 추정이 동종 사전의 90% 밖」(경보) · 「수축이 판정을 바꿈」(참고) · 「표본 부족」(참고) · 「재료 없음」(참고)
폴백 — 동종이 셋 미만 · 자체 관측이 모자라면 그 항목은 `폴백` 글(기존 규칙 — E 의 성격 사전 · 실적 범위를 그대로 쓴다)을 달고 사후를 내지 않는다.
종료 코드 — 0 경보 없음 · 1 경보 있음 · 2 입력 오류(가정 없음 · JSON 파손 · 설정 없음).
회사 · 업종 이름으로 가르는 분기가 없다(범용).
"""
from __future__ import annotations

import argparse
import datetime
import glob
import io
import json
import math
import os
import re
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류  # noqa: E402
import 정상화  # noqa: E402

설정파일 = os.path.join(여기, "수축연결설정.json")
출처이름 = "수축"


def 설정읽기(p=None):
    return json.load(io.open(p or 설정파일, encoding="utf-8"))


def _수(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _해(c):
    """기간 키 → 회계연도(정수). FY2025A · FY2025 만 — 반기 · 분기 열은 기간 길이가 달라 쓰지 않는다."""
    m = re.fullmatch(r"FY(\d{4})A?", "%s" % c)
    return int(m.group(1)) if m else None


def _연열(d):
    """{기간: 값} → {회계연도: 값}(수만)."""
    if not isinstance(d, dict):
        return {}
    낸 = {}
    for k, v in d.items():
        y = _해(k)
        if y is not None and _수(v):
            낸[y] = float(v)
    return 낸


# ─────────────────────────────────────────────── 회귀 · 사전 · 사후

def 회귀(쌍):
    """[(x, y)] 최소제곱 → {b, a, se, 쌍수, sxx, s} (쌍 둘이면 se · s 없음). 쌍 둘 미만 · 분모 0 이면 None."""
    n = len(쌍)
    if n < 2:
        return None
    mx, my = sum(x for x, _ in 쌍) / n, sum(y for _, y in 쌍) / n
    sxx = sum((x - mx) ** 2 for x, _ in 쌍)
    if sxx <= 1e-12:
        return None
    b = sum((x - mx) * (y - my) for x, y in 쌍) / sxx
    a = my - b * mx
    s = se = None
    if n > 2:
        s = math.sqrt(sum((y - a - b * x) ** 2 for x, y in 쌍) / (n - 2))
        se = s / math.sqrt(sxx)
    return {"b": b, "a": a, "se": se, "쌍수": n, "sxx": sxx, "s": s}


def 탄력성쌍(비용, 매출, 최소변동):
    """이어진 해의 (Δln 매출, Δln 비용) — 금액이 양수이고 |Δln 매출| ≥ 최소변동 인 쌍만(동인진단.탄력성 과 같은 이어진 해 규칙)."""
    쌍 = []
    해들 = sorted(set(비용) & set(매출))
    for y0, y1 in zip(해들, 해들[1:]):
        if y1 - y0 != 1:
            continue
        c0, c1, s0, s1 = 비용[y0], 비용[y1], 매출[y0], 매출[y1]
        if min(c0, c1, s0, s1) <= 0:
            continue
        dx = math.log(s1 / s0)
        if abs(dx) < 최소변동:
            continue
        쌍.append((dx, math.log(c1 / c0)))
    return 쌍


def 사전짓기(추정들, 최소동종):
    """추정들 = [(이름, 값, 표준오차 또는 None)] → {"평균", "분산"(τ²), "회사수", "방식", "회사"} 또는 None(회사 부족).
    표준오차가 다 있으면 DerSimonian–Laird, 하나라도 없으면 표본 평균 · 표본 분산(회사 안 잡음이 섞여 넓다 — 수축이 약해지는 쪽)."""
    추정들 = [x for x in 추정들 if _수(x[1])]
    k = len(추정들)
    if k < 최소동종:
        return None
    값 = [x[1] for x in 추정들]
    se = [x[2] for x in 추정들]
    if all(_수(s) and s > 0 for s in se):
        w = [1.0 / (s * s) for s in se]
        sw = sum(w)
        mu_fe = sum(wi * v for wi, v in zip(w, 값)) / sw
        Q = sum(wi * (v - mu_fe) ** 2 for wi, v in zip(w, 값))
        C = sw - sum(wi * wi for wi in w) / sw
        tau2 = max(0.0, (Q - (k - 1)) / C) if C > 0 else 0.0
        w2 = [1.0 / (s * s + tau2) for s in se]
        mu = sum(wi * v for wi, v in zip(w2, 값)) / sum(w2)
        var_mu = 1.0 / sum(w2)
        방식 = "DerSimonian–Laird(회사마다 표준오차)"
    else:
        mu = sum(값) / k
        tau2 = sum((v - mu) ** 2 for v in 값) / (k - 1)
        var_mu = tau2 / k
        방식 = "표본 평균 · 표본 분산(표준오차 없는 동종이 섞였다 — 사전이 넓다)"
    return {"평균": mu, "분산": tau2, "평균분산": var_mu, "회사수": k, "방식": 방식,
            "회사": [{"이름": x[0], "값": round(x[1], 6), "표준오차": (round(x[2], 6) if _수(x[2]) else None)} for x in 추정들]}


def 사전분산(사전):
    """사전의 실효 분산 = 회사 간 분산 τ² + 사전 평균 자체의 분산(동종이 적으면 평균도 흔들린다). τ² = 0 이어도 0 폭이 되지 않는다."""
    return 사전["분산"] + (사전.get("평균분산") or 0.0)


def 사후(자체값, 자체se, 사전, z):
    """정규–정규 사후(사전 N(μ, τ² + Var μ̂) · 자체 N(b̂, σ²)). 자체가 없으면(None) 사전 그대로(B = 1).
    → {"평균", "sd", "구간", "수축률"} — 수축률 B = σ² ÷ (σ² + 사전 실효 분산)."""
    mu, v0 = 사전["평균"], 사전분산(사전)
    if not _수(자체값):
        sd = math.sqrt(v0)
        return {"평균": mu, "sd": sd, "구간": [mu - z * sd, mu + z * sd], "수축률": 1.0}
    s2 = 자체se * 자체se
    if v0 <= 0 and s2 <= 0:
        return {"평균": 자체값, "sd": 0.0, "구간": [자체값, 자체값], "수축률": 0.0}
    B = s2 / (s2 + v0)
    m = B * mu + (1 - B) * 자체값
    sd = math.sqrt(s2 * v0 / (s2 + v0))            # = √((1 − B) σ²)
    return {"평균": m, "sd": sd, "구간": [m - z * sd, m + z * sd], "수축률": B}


def 평균표준오차(점):
    """해 차례의 값들 → (평균, 표준오차, 유효관측). 이웃한 해의 자기상관 ρ(1차 · 관측 넷 이상 · 0~0.9 로 자름)가 양이면
    유효관측 = n · (1 − ρ) ÷ (1 + ρ)(최소 2)로 줄인다 — 사이클 회사의 비율은 해마다 독립이 아니라 √n 로 나누면 평균이 실제보다 정밀해 보인다."""
    n = len(점)
    m = sum(점) / n
    if n < 2:
        return m, None, n
    sd = math.sqrt(sum((v - m) ** 2 for v in 점) / (n - 1))
    ne = float(n)
    if n >= 4 and sd > 0:
        num = sum((a - m) * (b - m) for a, b in zip(점, 점[1:]))
        den = sum((v - m) ** 2 for v in 점)
        rho = min(0.9, max(0.0, num / den)) if den > 0 else 0.0
        if rho > 0:
            ne = max(2.0, n * (1 - rho) / (1 + rho))
    return m, (sd / math.sqrt(ne)) if sd > 0 else None, ne


def 확신(폭, 기준, 상대=None):
    잴 = 폭 / abs(상대) if (상대 is not None and abs(상대) > 1e-12) else 폭
    lo, hi = 기준
    return "강" if 잴 <= lo else ("보통" if 잴 <= hi else "약")


# ─────────────────────────────────────────────── 읽기

def 후보폴더(가정경로):
    """`정상화.파일찾기` 와 같은 차례의 _raw 폴더들."""
    낸 = []
    if 가정경로:
        d = os.path.dirname(os.path.abspath(가정경로))
        낸 += [os.path.join(d, "_raw"), d, os.path.join(os.path.dirname(d), "_raw")]
    낸.append(os.path.join(os.getcwd(), "_raw"))
    return 낸


def 운영지표읽기(가정경로):
    """peers/운영지표_*.json 을 찾는다 — 처음 찾은 폴더의 것들을 회사 단위로 합친다(같은 코드 · 이름은 한 번). → (회사[], 경로[])."""
    for d in 후보폴더(가정경로):
        ps = sorted(glob.glob(os.path.join(d, "peers", "운영지표_*.json")))
        if not ps:
            continue
        회사, 본, 경로 = [], set(), []
        for p in ps:
            try:
                j = json.load(io.open(p, encoding="utf-8"))
            except (OSError, ValueError):
                continue
            경로.append(p)
            for c in j.get("회사") or []:
                if not isinstance(c, dict):
                    continue
                키 = c.get("코드") or c.get("이름")
                if 키 in 본:
                    continue
                본.add(키)
                회사.append(c)
        if 경로:
            return 회사, 경로
    return [], []


def 동종탄력성(회사들, 기능, 설정):
    """동종 회사마다 기능(매출원가 · 판관비 · 연구개발비) 대 매출액 탄력성 → [(이름, b, se)], 뺀[], 잔차표준편차 목록."""
    낸, 뺀, 잔 = [], [], []
    for c in 회사들:
        재 = c.get("재료") or {}
        매 = {y: v.get("매출액") for k, v in 재.items() if isinstance(v, dict) for y in [_해(k)] if y is not None and _수(v.get("매출액"))}
        비 = {y: v.get(기능) for k, v in 재.items() if isinstance(v, dict) for y in [_해(k)] if y is not None and _수(v.get(기능))}
        r = 회귀(탄력성쌍(비, 매, 설정["최소변동"]))
        if not r:
            continue
        if abs(r["b"]) > 설정["극단탄력성"]:
            뺀.append("%s(b %.2f)" % (c.get("이름"), r["b"]))
            continue
        낸.append((c.get("이름") or c.get("코드") or "?", r["b"], r["se"]))
        if _수(r["s"]):
            잔.append(r["s"])
    return 낸, 뺀, 잔


def 동종비율(회사들, 지표, 운영동종, 설정):
    """동종 회사마다 지표(C2 `지표` 이름)의 회사 평균과 그 표준오차(회사 안 해들) → [(이름, 평균, se 또는 None)].
    C2 파일이 없으면 가정 `관측.운영동종.지표.<이름>.값` 의 회사 값(표준오차 없음)."""
    낸 = []
    for c in 회사들:
        x0 = (c.get("지표") or {}).get(지표)
        if isinstance(x0, (int, float)) and not isinstance(x0, bool):      # 1.1.4(R8) — 옛 판 운영 지표 재료는 지표 칸이 수 하나(사전이 아니다) — 한 점으로 읽는다
            v = {"값": x0}
            점 = [float(x0)]
        else:
            v = (x0 or {}).get("값") if isinstance(x0, dict) else None
            점 = [x for _y, x in sorted(_연열(v).items())] if isinstance(v, dict) else []
        if not 점:
            continue
        m, se, _ne = 평균표준오차(점)
        낸.append((c.get("이름") or c.get("코드") or "?", m, se if (se and se > 0) else None))
    if 낸:
        return 낸, "C2 운영 지표(회사 평균)"
    d = ((운영동종 or {}).get("지표") or {}).get(지표) or {}
    for x in d.get("값") or []:
        if isinstance(x, dict) and _수(x.get("값")):
            낸.append((x.get("이름") or "?", float(x["값"]), None))
    return 낸, ("가정 관측.운영동종(회사 값 — 표준오차 없음)" if 낸 else None)


def 자체매출(가정, 원천A3):
    """자체 매출 시계열 {해: 값} — 동인원천 재무시계열 → 운전자본.매출연 → 가정 원천 62."""
    재 = (원천A3 or {}).get("재무시계열") or {}
    매 = {y: v.get("매출") for k, v in 재.items() if isinstance(v, dict) for y in [_해(k)] if y is not None and _수(v.get("매출"))}
    if len(매) >= 2:
        return 매, "동인원천 재무시계열.매출"
    매 = _연열(((원천A3 or {}).get("운전자본") or {}).get("매출연"))
    if len(매) >= 2:
        return 매, "동인원천 운전자본.매출연"
    매 = _연열((가정.get("원천") or {}).get("62"))
    return 매, ("가정 원천 62" if 매 else None)


def 자체회사비율(이름, 가정, 원천A3, 투자):
    """회사 수준 비율의 자체 시계열 {해: 값} — 매출총이익률 · 판관비율 · 매출대비CAPEX."""
    재 = (원천A3 or {}).get("재무시계열") or {}
    낸 = {}
    for k, v in 재.items():
        y = _해(k)
        if y is None or not isinstance(v, dict) or not _수(v.get("매출")) or v["매출"] <= 0:
            continue
        s = v["매출"]
        if 이름 == "매출총이익률" and _수(v.get("매출원가")):
            낸[y] = 1 - v["매출원가"] / s
        elif 이름 == "판관비율" and _수(v.get("판관비")):
            낸[y] = v["판관비"] / s
        elif 이름 == "매출대비CAPEX" and _수(v.get("CAPEX")):
            낸[y] = (v["CAPEX"] + (v.get("무형취득") if _수(v.get("무형취득")) else 0.0)) / s
    if 낸:
        return 낸, "동인원천 재무시계열"
    if 이름 == "매출대비CAPEX":
        x = _연열((((투자 or {}).get("CAPEX비율") or {}).get("매출대비CAPEX")))
        if x:
            return x, "투자능력 CAPEX비율.매출대비CAPEX"
    원 = 가정.get("원천") or {}
    매, 원가, 판 = _연열(원.get("62")), _연열(원.get("63")), _연열(원.get("65"))
    for y, s in 매.items():
        if s <= 0:
            continue
        if 이름 == "매출총이익률" and y in 원가:
            낸[y] = 1 - 원가[y] / s
        elif 이름 == "판관비율" and y in 판:
            낸[y] = 판[y] / s
    return 낸, ("가정 원천 13번(62 · 63 · 65)" if 낸 else None)


def _자료판정(b, 구간, 쌍수, 사전판정):
    """동인진단.자료판정 을 그대로 부른다(판정 규칙을 두 벌 두지 않는다). 못 부르면 None."""
    try:
        import 동인진단                                    # noqa: PLC0415
    except Exception:                                    # noqa: BLE001
        return None, "동인진단.py 를 못 불러 판정을 견주지 않았다"
    탄 = {"b": b, "신뢰구간": 구간, "쌍수": 쌍수}
    return 동인진단.자료판정(탄, 사전판정 or "모름")


# ─────────────────────────────────────────────── 돌기

def 돌기(가정, 가정경로, 설정):
    S = 설정["수축"]
    z = S["z"]
    진단, 진단곳 = 정상화.파일찾기("동인진단.json", 가정경로)
    A3, A3곳 = 정상화.파일찾기("동인원천.json", 가정경로)
    투자, 투자곳 = 정상화.파일찾기("투자능력.json", 가정경로)
    회사들, 운영곳 = 운영지표읽기(가정경로)
    운영동종 = (가정.get("관측") or {}).get("운영동종")
    진단 = 진단 if isinstance(진단, dict) else None
    A3 = A3 if isinstance(A3, dict) else None
    투자 = 투자 if isinstance(투자, dict) else None
    결과 = {"형식": "수축 1", "만든날": datetime.date.today().isoformat(),
          "설정": {"신용구간": S["신용구간"], "z": z, "최소동종": S["최소동종"], "최소쌍_자체": S["최소쌍_자체"],
                 "최소관측_비율": S["최소관측_비율"], "최소변동": S["최소변동"], "극단탄력성": S["극단탄력성"]},
          "입력": {"가정": os.path.abspath(가정경로) if 가정경로 else None, "동인진단": 진단곳, "동인원천": A3곳, "투자능력": 투자곳,
                 "운영지표": 운영곳, "관측.운영동종": bool(운영동종)},
          "폴백": None, "사전": {}, "항목": [], "제안": [], "신호": []}
    신호, 제안, 항목 = 결과["신호"], 결과["제안"], 결과["항목"]

    def 알림(종류, 대상, 값, 문턱, 글, 등급):
        신호.append({"출처": 출처이름, "종류": 종류, "대상": 대상, "값": 값, "문턱": 문턱, "글": 글, "등급": 등급})

    # ── 동종 사전(탄력성) — 기능마다 한 번
    잔차 = []
    사전들 = {}
    for 기능 in ("매출원가", "판관비", "연구개발비"):
        추, 뺀, 잔 = 동종탄력성(회사들, 기능, S)
        잔차 += 잔
        p = 사전짓기(추, S["최소동종"])
        if p:
            p["뺀"] = 뺀
            사전들[기능] = p
            결과["사전"]["탄력성." + 기능] = {k: (round(v, 6) if _수(v) else v) for k, v in p.items()}
        elif 회사들:
            결과["사전"]["탄력성." + 기능] = {"폴백": "동종 탄력성이 %d곳뿐(최소 %d) — 이 기능의 사전을 세우지 않는다" % (len(추), S["최소동종"]),
                                        "뺀": 뺀}
    s_pool = (sum(잔차) / len(잔차)) if 잔차 else None

    _패널캐시 = {}

    def 패널사전(기능):
        """패널 산업 사전(계수사전.사전가져오기) — 국가 · 산업은 가정 메타 · 가정 곁 기업 식별 파일에서. 못 내면 None(조용히)."""
        if 기능 in _패널캐시:
            return _패널캐시[기능]
        낸 = None
        try:
            import 계수사전 as _계                                   # noqa: PLC0415
            import 기저율 as _기                                     # noqa: PLC0415
            국 = _기.국가판정(가정)
            산업 = None
            if 국:
                행, _ = _기.패널읽기(None, _기.국가설정(_기.설정읽기(), 국))
                _, 산업, _ = _기.대상찾기(가정, 가정경로, 행, None, _기.국가설정(_기.설정읽기(), 국)) if 행 else (None, None, "")
            if 국:
                낸 = _계.사전가져오기(국, 산업, 기능)
        except Exception:                                            # noqa: BLE001
            낸 = None
        _패널캐시[기능] = 낸
        if 낸:
            결과["사전"]["탄력성." + 기능 + "(패널)"] = {k: (round(v, 6) if _수(v) else v) for k, v in 낸.items()}
        return 낸

    def 탄력성항목(이름, 노드, 기능, 자체, 사전판정, 자리, 정의다름, 자체출처):
        """자체 = {b, se, 쌍수} 또는 None."""
        사 = 사전들.get(기능) or (사전들.get("판관비") if 기능 == "연구개발비" else None)
        쓴기능 = 기능 if 기능 in 사전들 else ("판관비" if (기능 == "연구개발비" and 사) else 기능)
        x = {"이름": 이름, "종류": "탄력성", "노드": 노드, "자리": 자리,
             "자체": {"추정": (round(자체["b"], 6) if 자체 else None), "표준오차": (round(자체["se"], 6) if (자체 and _수(자체.get("se"))) else None),
                    "n": (자체 or {}).get("쌍수"), "출처": 자체출처},
             "동종사전": ({"평균": round(사["평균"], 6), "분산": round(사["분산"], 6), "회사수": 사["회사수"], "기능": 쓴기능, "방식": 사["방식"]}
                      if 사 else None)}
        if not 사:
            사 = 패널사전(기능)                                       # 2026-10-23 P4 — 동종(C2)이 없으면 패널 산업 사전(계수사전.py)
            if 사:
                쓴기능 = 기능
                x["동종사전"] = {"평균": round(사["평균"], 6), "분산": round(사["분산"], 6), "회사수": 사["회사수"], "기능": 기능, "방식": 사["방식"]}
                x["근거강도"] = "유추"
                x["정의"] = "동종(C2) 사전이 없어 패널 산업 사전(같은 산업 2자리 · 본표 판관비 = 매출 − 매출원가 − 영업이익 근사)을 썼다"
        if not 사:
            x["폴백"] = "동종 %s 탄력성 사전이 없다(C2 운영 지표 재료가 없거나 셋 미만 · 패널 산업 사전도 없다) — 기존 규칙(E 의 성격 사전 · 기능별 앵커)을 그대로 쓴다" % 기능
            항목.append(x)
            알림("표본 부족", 이름, (사전들.get(기능) or {}).get("회사수", 0), S["최소동종"], x["폴백"], "참고")
            return
        se = 자체.get("se") if 자체 else None
        원쌍 = (자체 or {}).get("쌍수")
        차용 = False
        if 자체 and not _수(se):
            if 자체.get("쌍수", 0) >= S["최소쌍_자체"] and _수(s_pool) and 자체.get("sxx"):
                se = s_pool / math.sqrt(자체["sxx"])
                차용 = True
                x["자체"]["표준오차"] = round(se, 6)
                x["자체"]["표준오차차용"] = "동종 잔차 표준편차 %.4f ÷ √Sxx(쌍 %d)" % (s_pool, 자체["쌍수"])
            else:
                자체 = None
        if 자체 is None:
            x["자체"]["추정"] = None
        po = 사후(자체["b"] if 자체 else None, se if 자체 else None, 사, z)
        lo, hi = po["구간"]
        x["사후"] = {"평균": round(po["평균"], 6), "sd": round(po["sd"], 6), "90%": [round(lo, 6), round(hi, 6)]}
        x["수축률"] = round(po["수축률"], 6)
        if 정의다름:
            x["근거강도"] = "유추"
            x["정의"] = "동종 사전은 기능별(%s) 매출 탄력성이고 이 노드와 정의가 다르다" % 쓴기능
        if not 자체:
            x["폴백"] = "자체 관측 쌍이 %s — 동종 사전만으로 낸 구간이다(자체로는 잴 수 없다)" % (원쌍 if 원쌍 else "둘 미만")
            알림("표본 부족", 이름, None, S["최소쌍_자체"], x["폴백"], "참고")
        # 자체 추정이 사전 예측 분포(회사 간 차이 + 자체 표준오차)의 90% 밖인가
        if 자체 and _수(se):
            반 = z * math.sqrt(사전분산(사) + se * se)
            if abs(자체["b"] - 사["평균"]) > 반:
                알림("자체 추정이 동종 사전의 90% 밖", 이름, round(자체["b"], 4), [round(사["평균"] - 반, 4), round(사["평균"] + 반, 4)],
                   "%s 의 매출 탄력성 %.2f 가 동종(%s · %d곳) 사전 예측 90%% 구간 %.2f~%.2f 밖이다 — 동종과 다른 까닭(비용 구조 · 정의)을 근거 칸에 적는다"
                   % (이름, 자체["b"], 쓴기능, 사["회사수"], 사["평균"] - 반, 사["평균"] + 반), "경보")
        # 판정이 바뀌는가 — 동인진단.자료판정 그대로(사후는 쌍수를 넷으로 본다 — 동종 사전이 정보를 더했다)
        자구 = (자체 or {}).get("구간") or ([자체["b"] - z * se, 자체["b"] + z * se] if (자체 and _수(se)) else None)
        자판, 자글 = (_자료판정(자체["b"], 자구, 자체.get("쌍수", 0), 사전판정) if 자체 else (None, "자체 탄력성 없음"))
        사판, 사글 = _자료판정(po["평균"], [lo, hi], max(4, (자체 or {}).get("쌍수") or 0), 사전판정)
        x["판정"] = {"자체": 자판, "자체글": 자글, "사후": 사판, "사후글": 사글, "사전판정": 사전판정}
        if 사판 != 자판 and 사판 is not None:
            알림("수축이 판정을 바꿈", 이름, 사판, 자판 or "판정 보류",
               "%s — 자체로는 %s, 동종 사전과 합친 사후로는 %s(%s). 판정은 사람이 한다 — 동인 지도 근거 칸에 둘을 함께 적는다"
               % (이름, 자판 or "판정 보류", 사판, 사글), "참고")
        폭 = hi - lo
        제안.append({"자리": 자리, "값": round(po["평균"], 6), "근거범위": [round(max(lo, 0.0), 6), round(min(hi, 1.0), 6)] if 자리.startswith("A-7") else [round(lo, 6), round(hi, 6)],
                   "딱지": "[계산 — 경험적 베이즈 수축(동종 %s %d곳 · 수축률 %.2f%s)]" % (쓴기능, 사["회사수"], po["수축률"], " · 표준오차 차용" if 차용 else ""),
                   "확신": 확신(폭, S["확신"]["탄력성폭"]),
                   "글": "%s 매출 탄력성 사후 %.2f(90%% %.2f~%.2f) — 자체 %s · 동종 평균 %.2f. %s"
                        % (이름, po["평균"], lo, hi, ("%.2f" % 자체["b"]) if 자체 else "없음", 사["평균"],
                           "보조 산식 비중의 범위는 [0, 1] 로 자른다" if 자리.startswith("A-7") else "판단 칸의 근거범위 후보다")})
        항목.append(x)

    def 비율사전(지표):
        추, 출처 = 동종비율(회사들, 지표, 운영동종, S)
        return 사전짓기(추, S["최소동종"]), 출처, len(추)

    def 비율항목(이름, 노드, 지표, 자체열, 자리, 자체출처, 정의=None):
        """비율 하나(회전일수 · 회사 수준 비율) — 자체 평균 · 표준오차(해들) 대 동종 회사 평균의 분포.
        정의 = 자체와 동종의 분모가 다를 때의 글(설정 `비율정의근사`) — 있으면 근거강도 「유추」."""
        점 = [v for _y, v in sorted(자체열.items())]
        x = {"이름": 이름, "종류": "비율", "노드": 노드, "자리": 자리, "지표": 지표,
             "자체": {"추정": None, "표준오차": None, "n": len(점), "출처": 자체출처}}
        if 정의:
            x["근거강도"], x["정의"] = "유추", 정의
        사, 출처, 수 = 비율사전(지표)
        x["동종사전"] = ({"평균": round(사["평균"], 6), "분산": round(사["분산"], 6), "회사수": 사["회사수"], "방식": 사["방식"], "출처": 출처}
                     if 사 else None)
        if len(점) < S["최소관측_비율"]:
            x["폴백"] = "자체 관측 %d해(최소 %d) — 기존 규칙(실적 범위)을 그대로 쓴다" % (len(점), S["최소관측_비율"])
            항목.append(x)
            알림("표본 부족", 이름, len(점), S["최소관측_비율"], x["폴백"], "참고")
            return
        m, se, ne = 평균표준오차(점)
        se = se or 1e-9                                  # 해마다 같은 값 — 자체 평균이 곧 수준
        x["자체"].update({"추정": round(m, 6), "표준오차": round(se, 6), "유효관측": round(ne, 2)})
        if not 사:
            x["폴백"] = "동종 %s 사전이 없다(%d곳 — 최소 %d) — 기존 규칙(실적 범위)을 그대로 쓴다" % (지표, 수, S["최소동종"])
            항목.append(x)
            알림("표본 부족", 이름, 수, S["최소동종"], x["폴백"], "참고")
            return
        po = 사후(m, se, 사, z)
        lo, hi = po["구간"]
        x["사후"] = {"평균": round(po["평균"], 6), "sd": round(po["sd"], 6), "90%": [round(lo, 6), round(hi, 6)]}
        x["수축률"] = round(po["수축률"], 6)
        반 = z * math.sqrt(사전분산(사) + se * se)
        if abs(m - 사["평균"]) > 반:
            알림("자체 추정이 동종 사전의 90% 밖", 이름, round(m, 6), [round(사["평균"] - 반, 6), round(사["평균"] + 반, 6)],
                    "%s 자체 평균 %.4g 가 동종(%d곳) 사전 예측 90%% 구간 %.4g~%.4g 밖이다 — 동종과 다른 까닭을 근거 칸에 적는다(값은 바꾸지 않는다)"
                    % (이름, m, 사["회사수"], 사["평균"] - 반, 사["평균"] + 반), "경보")
        제안.append({"자리": 자리, "값": round(po["평균"], 6), "근거범위": [round(lo, 6), round(hi, 6)],
                        "딱지": "[계산 — 경험적 베이즈 수축(동종 %s %d곳 · 수축률 %.2f)]" % (지표, 사["회사수"], po["수축률"]),
                        "확신": 확신(hi - lo, S["확신"]["비율상대폭"], po["평균"]),
                        "글": "%s 사후 평균 %.4g(90%% %.4g~%.4g) — 자체 %d해 평균 %.4g · 동종 평균 %.4g. 수준(정상치)의 구간이지 해마다의 범위가 아니다%s"
                             % (이름, po["평균"], lo, hi, len(점), m, 사["평균"], (" — 정의 근사: " + 정의) if 정의 else "")})
        항목.append(x)

    # ── E 노드
    매자, 매자출처 = 자체매출(가정, A3)
    if 진단:
        앵 = 진단.get("기능별앵커탄력성") or {}
        for 기능 in ("매출원가", "판관비"):
            t = 앵.get(기능)
            if isinstance(t, dict) and _수(t.get("b")):
                탄력성항목("기능별 앵커 %s 탄력성" % 기능, "기능별앵커." + 기능, 기능,
                         {"b": float(t["b"]), "se": t.get("se"), "쌍수": t.get("쌍수") or 0, "sxx": None, "구간": t.get("신뢰구간")}, None,
                         "동인진단 기능별앵커탄력성.%s" % 기능, False, "동인진단 기능별앵커탄력성")
        for it in 진단.get("항목") or []:
            if not isinstance(it, dict):
                continue
            노드 = "%s" % it.get("노드")
            판 = it.get("판정") if isinstance(it.get("판정"), dict) else None
            if 노드.startswith("원가줄") or 노드 == "연구개발":
                기능 = S["기능대응"].get(노드)
                if not 기능:
                    continue
                후 = next((c for c in it.get("후보") or [] if isinstance(c, dict) and c.get("동인") == "매출액"), None)
                t = (후 or {}).get("탄력성")
                자체, 출처 = None, "동인진단 후보(매출액).탄력성"
                if isinstance(t, dict) and _수(t.get("b")):
                    자체 = {"b": float(t["b"]), "se": t.get("se"), "쌍수": t.get("쌍수") or 0, "sxx": None, "구간": t.get("신뢰구간")}
                else:
                    r = 회귀(탄력성쌍(_연열(it.get("실적")), 매자, S["최소변동"]))
                    if r:
                        자체 = {"b": r["b"], "se": r["se"], "쌍수": r["쌍수"], "sxx": r["sxx"]}
                        출처 = "노드 실적 · %s 로 다시 잼(동인진단.탄력성 과 같은 식)" % 매자출처
                사판 = ((판 or {}).get("성격판정") or {}).get("사전", {}).get("판정") if 판 else None
                k = re.match(r"원가줄(\d)", 노드)
                자리 = ("A-7%s4" % k.group(1)) if k else "판단칸(연구개발 성격)"
                탄력성항목("%s 매출 탄력성" % 노드, 노드, 기능, 자체, 사판, 자리, True, 출처)
            elif 노드.startswith("운전자본.") and 판:
                for 칸 in 판.get("판단칸") or []:
                    번 = "%s" % (칸.get("번호") or "")
                    지 = S["비율대응"].get(번)
                    if not 지:
                        continue
                    비율항목("%s(판단 칸 %s)" % (지, 번), 노드, 지, _연열(it.get("실적")), "판단칸 %s" % 번, "동인진단 %s 실적" % 노드,
                         정의=(S.get("비율정의근사") or {}).get(번))
    else:
        결과["입력"]["동인진단_없음"] = "E 동인진단 산출이 없다 — 탄력성 · 운전자본 판단 칸은 건너뛴다"

    for 지표 in S["회사비율"]:
        자, 출처 = 자체회사비율(지표, 가정, A3, 투자)
        if 자:
            비율항목(지표, "회사", 지표, 자, {"매출총이익률": "㊼ 운영 동종 띠 · 213 종착 마진 근거(참고)",
                                         "판관비율": "㊼ 운영 동종 띠(참고)",
                                         "매출대비CAPEX": "851 근거(정의 근사 — 851 은 유형만 · 이 비율은 유형 + 무형)"}.get(지표, 지표), 출처)
    if not 항목:
        결과["폴백"] = ("재료 없음 — E 동인진단 · 자체 비율 시계열이 없다. 기존 규칙(E 의 성격 사전 · 실적 범위)을 그대로 쓴다"
                     if not (진단 or A3) else "동종 사전도 자체 항목도 서지 않았다 — 기존 규칙을 그대로 쓴다")
        알림("재료 없음", "전체", None, None, 결과["폴백"], "참고")
    elif not (회사들 or 운영동종):
        결과["폴백"] = "동종 재료 없음 — C2 운영 지표 · 관측.운영동종이 없다. 항목마다 기존 규칙(E 의 성격 사전 · 실적 범위)을 그대로 쓴다"
    return 결과


def 계산(가정, 가정경로, 설정=None):
    """한 번 돈다 → 결과 dict."""
    return 돌기(가정, 가정경로, 설정 or 설정읽기())


def 수축읽기(가정경로):
    """다른 도구가 읽는 자리 — (내용, 경로) 또는 (None, None)."""
    return 정상화.파일찾기("수축.json", 가정경로)


def 찍기(결과):
    L = ["── 경험적 베이즈 수축 (기법 3) ──"]
    if 결과.get("폴백"):
        L.append("폴백 — %s" % 결과["폴백"])
    for k, p in (결과.get("사전") or {}).items():
        if "평균" in p:
            L.append("사전 %s — 평균 %.4g · τ² %.4g · %d곳 (%s)" % (k, p["평균"], p["분산"], p["회사수"], p["방식"]))
        else:
            L.append("사전 %s — %s" % (k, p.get("폴백")))
    for x in 결과["항목"]:
        if x.get("사후"):
            L.append("  %-34s 자체 %-10s 사후 %.4g (90%% %.4g~%.4g) 수축률 %.2f" % (
                x["이름"][:34], ("%.4g" % x["자체"]["추정"]) if x["자체"].get("추정") is not None else "없음",
                x["사후"]["평균"], x["사후"]["90%"][0], x["사후"]["90%"][1], x["수축률"]))
        else:
            L.append("  %-34s 폴백 — %s" % (x["이름"][:34], x.get("폴백")))
    for s in 결과["신호"]:
        L.append("  [%s] %s — %s: %s" % (s["등급"], s["종류"], s["대상"], s["글"][:120]))
    return "\n".join(L)


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                    # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(allow_abbrev=False, description="경험적 베이즈 수축 — 짧은 자체 탄력성 · 비율을 동종 분포 쪽으로")
    ap.add_argument("가정")
    ap.add_argument("--낼", default=None)
    ap.add_argument("--설정", default=None)
    a = ap.parse_args(argv)
    try:
        설정 = 설정읽기(a.설정)
    except (OSError, ValueError) as e:
        print("수축 — 설정을 못 읽었다: %s" % e)
        return 입력오류
    try:
        가정 = json.load(io.open(a.가정, encoding="utf-8"))
    except (OSError, ValueError) as e:
        print("수축 — 가정 파일을 못 읽었다: %s" % e)
        return 입력오류
    결과 = 계산(가정, a.가정, 설정)
    낼 = a.낼 or os.path.join(os.path.dirname(os.path.abspath(a.가정)), "_raw", "수축.json")
    os.makedirs(os.path.dirname(낼), exist_ok=True)
    io.open(낼, "w", encoding="utf-8").write(json.dumps(결과, ensure_ascii=False, indent=1))
    print(찍기(결과))
    print("→ %s" % 낼)
    return 발견 if any(s["등급"] == "경보" for s in 결과["신호"]) else 통과


if __name__ == "__main__":
    sys.exit(main())

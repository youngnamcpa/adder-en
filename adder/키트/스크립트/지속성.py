# -*- coding: utf-8 -*-
"""지속성 — 변수마다 「되돌아가는 속도」를 같은 집단 패널에서 재고, 가정 칸의 경로 형태를 그것에 대 본다 (제안 A · 2026-10-22 신설).

무엇을 하나
  전 상장사 패널(기저율.py 와 같은 공용 캐시 — 표시통화가 KR · US 를 고른다)에서 변수 일곱(매출성장률 · 영업이익률 · 그 변화 · 자산회전율 · 그 변화 ·
  총자산영업이익률 · 영업이익성장률)의 지속성을 넷으로 잰다.
    ① 연도 간 순위상관 r_k(k = 1 · 3 · 5)       — 올해 값이 k년 뒤 값을 얼마나 알려 주나(Mauboussin · Callahan 의 자)
    ② AR(1) 계수 ρ(Huber · 그해 중앙값 편차)     — 절반이 되돌아오는 햇수 = ln 0.5 ÷ ln ρ(Fama · French 의 부분조정)
    ③ 비대칭 — 그해 중앙값 아래 · 위를 따로 잰 ρ   (평균 아래가 더 빨리 돌아오나)
    ④ 10분위 수렴 — 기준 해 10분위 포트폴리오 중앙값의 분산이 k년 뒤 몇 분의 일로 줄었나(Nissim · Penman 의 그림)
    ⑤ 연속 중위 초과(변화형만) — k년 내리 중위를 넘은 회사 비중 대 우연 0.5^k(Chan · Karceski · Lakonishok)
  그 r1 로 변수의 경로 형태(수렴형 · 느린수렴형 · 지속형)를 가르고, 가정 파일의 칸(판매량 증가율 · 단가 변동률 · 원가 줄 비율 · 회전일수 · CAPEX 비율)을
  부류마다 대 본다 — 수렴형 변수를 다섯 열에 한 값으로 두었나, 수준 변수를 크게 옮겨 두었나.

값을 정하지 않는다. 신호와 제안(경로 형태)만 낸다 — 거친 바퀴 한 표에는 실리지 않는다(범위가 아니라 형태라 `근거범위` 가 없다). 읽는 곳은
자체검사 51(신호) · 사람(근거 칸 — 「같은 집단에서 이 변수의 1년 상관은 …」)이다.
엔진을 돌리지 않는다 — 가정 파일의 예측 열만 읽으므로 가정이 바뀌어도 낡지 않는다(엔진값파일이 아니다).

사용
  python 스크립트/지속성.py 가정.json [--회사 고유번호] [--국가 KR|US] [--낼 경로.json] [--설정 지속성설정.json]
읽는 것 — 공용 패널(기저율.패널읽기 · 국가 축) · 가정 파일(읽기만 — 예측 열) · 가정 곁 기업 식별 파일(기저율.대상찾기 — 없으면 전체 집단만) ·
          `지속성설정.json`(결과 전에 정한 값) · `기저율설정.json`(국가별 · 제외 · 규모)
내는 것 — 가정 곁 `_raw/지속성.json`: {형식 · 만든날 · 설정 · 입력 · 패널 · 대상 · 폴백 · 변수[] · 칸[] · 제안[] · 신호[]}. 신호 꼴은 신호파일.py 그대로.
          표시통화가 KRW · USD 아님 · 그 국가 패널 없음이면 「해당 없음」 꼴(기저율.py 와 같다) · rc 0.
종료 코드 — 0 통과(신호가 있어도) · 2 입력오류(가정 깨짐 · 설정 없음).
80% 띠와 사후대조 보정(2026-10-23 밤 W8) — 가정 칸 가운데 패널 변수와 대응하는 칸(`보정대응`)에 같은 집단의 80% 띠 둘(기저율 띠 · 지속성 띠 —
  `사후대조.띠짓기`, 사후대조 층 1 이 포함률을 잰 것과 같은 함수)을 1 · 2년 뒤로 세우고, 공용 캐시의 사후대조 보정표가 **있을 때만** 보정계수 q 로
  양 끝을 옮긴다(가운데는 둔다 — `사후대조.보정띠`). 칸 `띠[]` 에 보정 전 · 보정 뒤를 함께 남기고, 칸 단위로 옮길 수 있는 칸(매출 증가율 · 매출채권
  회전일수 · 상각률)은 제안[] 에 근거범위(보정 뒤 · 없으면 보정 전)와 `근거범위_보정전` 을 싣는다. 보정표의 패널 판이 지금 패널과 다르면 쓰지 않고
  「보정표 낡음」 참고 신호. 값은 바꾸지 않는다. 거친 바퀴의 근거 범위 차례(통계 제안)에는 들지 않는다 — 한 표 비고 「같은 집단 80% 띠」 로만 보인다.
레터 v27(2026-11-10) — 업종 적합(`기저율.업종적합` — 대상 업종 2자리 대 핵심 표본 · 운영 동종의 일치 몫)을 대상 · 산출 머리 `업종적합` 에 싣고,
  집단 「운영 동종 산업」(핵심 표본 · 운영 동종의 산업 2자리 합집합)을 더 잰다. 업종 부적합이면 「같은 산업 2자리」 집단에 `싣기가능: false` 를 달고
  80% 띠의 집단 차례에서 산업을 뺀다(`보정.업종집단뺌`). 집단마다 그 집단의 1년 순위상관으로 매긴 `형태`, 변수마다 `노출`(반감기 숫자를 실어도 되나 —
  집단 차례 운영 동종 산업 → 같은 산업 → 같은 규모 → 전체 · 1년 쌍 1,000 이상 · 반감 0.5~15년 · 그 집단의 형태 = 형태 말일 때만 `싣기가능: true`).
회사 · 업종 이름은 이 도구에 없다(범용). 표준 라이브러리만 쓴다.
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
from 종료코드 import 통과, 입력오류  # noqa: E402
import 기저율 as 기  # noqa: E402

설정경로 = os.path.join(여기, "지속성설정.json")

# 사후대조 보정 대응(2026-10-23 밤 W8 · 연구/축적백테스트_20261023/조문_R.md 4절) — 가정 번호 → (보정표 변수, 칸 단위 환산 배수, 칸 단위로 옮길 수 있나, 딱지).
# 칸 단위로 옮길 수 없는 칸(정의가 다른 칸)은 띠를 그 변수 단위의 참고로만 적는다 — 근거범위로 내지 않는다.
보정대응 = {}
for _n in ("30", "38", "46", "54", "62", "70"):
    보정대응[_n] = ("매출성장률", 1.0, True, "관측")                       # 판매량 · 기타 매출 증가율 ↔ 매출 성장(k년 CAGR — 2년 뒤는 경로의 2년 CAGR 과 견준다)
for _n in ("34", "42", "50", "58", "66", "613", "623", "633", "643", "653"):
    보정대응[_n] = ("매출성장률", 1.0, False, "유추")                      # 판매단가 변동률 — 패널에 단가가 없다(매출 성장 근사)
for _n in ("80", "84", "88", "92", "112", "116", "120", "520"):
    보정대응[_n] = ("영업이익률", 1.0, False, "유추")                      # 원가 줄 비율 — 영업이익률의 조각(단위가 다르다)
보정대응["178"] = ("매출채권비율", 365.0, True, "관측")                    # 매출채권 ÷ 매출액 × 365 = DSO
보정대응["182"] = ("재고비율", 365.0, False, "유추")                       # 재고 ÷ 매출액(엔진 DIO 는 원가 기준 — 정의가 다르다)
보정대응["851"] = ("CAPEX비율", 1.0, False, "유추")                       # 유형자산 취득 ÷ 매출액(엔진 851 은 유지분만 — 위 끝의 참고)
for _n in ("156", "164"):
    보정대응[_n] = ("상각률", 1.0, True, "유추")                           # 감가상각비 ÷ 유형자산(패널은 기말 · 엔진은 기초 순장부)
# 상세변수(2026-10-24 PM · 연구/패널변수_20261024) — 칸마다 후보 차례 [(변수, 환산, 칸 단위, 딱지)]. 패널에 그 변수가 있는 첫 후보를 쓴다(국가마다 변수가 다르다).
# 칸 단위 = 그 띠를 칸 값과 같은 잣대로 견줄 수 있나(정의가 같은가). False 면 띠는 그 변수 단위의 참고로만 — 근거 범위로 내지 않는다.
for _n in ("80", "84", "88", "92"):
    보정대응[_n] = [("매출원가율", 1.0, True, "관측"), ("영업이익률", 1.0, False, "유추")]
for _n in ("112", "116", "120"):
    보정대응[_n] = [("판관비율", 1.0, True, "관측"), ("영업이익률", 1.0, False, "유추")]
보정대응["520"] = [("인건비율", 1.0, True, "관측"), ("영업이익률", 1.0, False, "유추")]
보정대응["182"] = [("재고회전일수_원가", 1.0, True, "관측"), ("재고비율", 365.0, False, "유추")]
보정대응["186"] = [("매입채무회전일수", 1.0, True, "관측")]
보정대응["156"] = [("상각률_기초순액", 1.0, True, "관측"), ("상각률", 1.0, True, "유추")]
보정대응["164"] = [("무형상각률", 1.0, True, "관측"), ("상각률", 1.0, False, "유추")]   # 무형상각 ÷ (기초 무형 순액 + 무형 취득 ÷ 2) — 엔진 164 와 같은 밑(2026-10-24 PN) · 없으면 유형 상각률(정의가 다름)
보정대응["196"] = [("유효세율_3년", 1.0, True, "유추"), ("유효세율", 1.0, True, "유추"), ("유효세율_1년", 1.0, True, "유추")]   # 법정세율 대 실현 세율
보정대응["213"] = [("영업이익률_연차", 1.0, True, "유추"), ("영업이익률", 1.0, True, "유추")]   # 같은 집단 · 같은 10분위의 5 · 10년 뒤 영업이익률(정상 상태 대 실현) — 긴 계열(미국 companyfacts 2009~)이 있으면 먼저(2026-10-24 PN)
for _k in range(1, 8):
    보정대응["7%d1" % _k] = [("설비계수", 1.0, True, "관측")]
보정대응["501"] = [("인원증가율", 1.0, True, "관측"), ("산업고용증가율", 1.0, True, "유추")]   # 미국은 직원 수가 재무제표 밖 — 같은 산업(NAICS 4자리) 고용 증가율(QCEW · 2026-10-24 PN)
보정대응["503"] = [("1인평균급여", "범위환산", True, "유추"), ("산업평균연봉", "범위환산", True, "유추")]   # 공시는 본사 기준 — 범위 환산 배수(아래)
보정대응["504"] = [("1인평균급여증가율", 1.0, True, "관측"), ("산업임금증가율", 1.0, True, "유추")]
for _n in ("801", "802", "803"):
    보정대응[_n] = [("기계장치내용연수", 1.0, True, "유추"), ("평균내용연수", 1.0, True, "유추")]
보정대응["850"] = [("유지율_취득원가", 1.0, True, "유추")]
보정대응["851"] = [("상각매출비율", 1.0, True, "유추"), ("CAPEX비율", 1.0, False, "유추")]   # 유지 CAPEX ÷ 매출 ↔ 감가상각비 ÷ 매출(상각 = 유지 가정)
율부류 = {"이익률수준", "원가율_매출원가", "원가율_판관", "인건비율", "세율", "영구이익률", "임금상승률", "인원증가율"}   # 수준 변화를 %p 로 재는 부류
보정앞날 = (1, 2)
보정앞날대응 = {"213": (5, 10)}                                          # 영구 칸은 5 · 10년 뒤(평균 회귀의 끝점 — 사후대조설정 영업이익률 앞날 5 · 10 · 2026-10-24 PN)
시나리오들 = ("비관", "기준", "낙관")


def 설정읽기(경로=None):
    return json.load(io.open(경로 or 설정경로, encoding="utf-8"))


# ═══════════════════════════════════════════════ 변수 계열

def 변수계열(넓은, 변수이름):
    """{고유번호: {연도: 값}} — 설정 「변수」의 정의대로. 매출 · 영업이익 · 자산총계만 쓴다(KR · US 패널이 같이 가진 열)."""
    낸 = {}
    for 고, d in 넓은.items():
        해 = d["해"]
        m = {}
        for y, r in 해.items():
            s, o, a = r.get("매출액"), r.get("영업이익"), r.get("자산총계")
            p = 해.get(y - 1)
            s0, o0 = (p.get("매출액"), p.get("영업이익")) if p else (None, None)
            v = None
            if 변수이름 == "매출성장률":
                v = (s / s0 - 1) if (s and s0 and s > 0 and s0 > 0) else None
            elif 변수이름 == "영업이익률":
                v = (o / s) if (s and o is not None and s > 0) else None
            elif 변수이름 == "영업이익률변화":
                v = ((o / s) - (o0 / s0)) if (s and s0 and o is not None and o0 is not None and s > 0 and s0 > 0) else None
            elif 변수이름 == "자산회전율":
                v = (s / a) if (s and a and s > 0 and a > 0) else None
            elif 변수이름 == "자산회전율변화":
                a0 = p.get("자산총계") if p else None
                v = ((s / a) - (s0 / a0)) if (s and a and s0 and a0 and s > 0 and a > 0 and s0 > 0 and a0 > 0) else None
            elif 변수이름 == "총자산영업이익률":
                v = (o / a) if (a and o is not None and a > 0) else None
            elif 변수이름 == "영업이익성장률":
                v = (o / o0 - 1) if (o and o0 and o > 0 and o0 > 0) else None
            # 상세 패널 변수(2026-10-22 — KR 일괄 · US FSDS 상세 열이 있을 때만 값이 선다)
            elif 변수이름 == "매출채권비율":
                v = (r.get("매출채권") / s) if (s and s > 0 and r.get("매출채권") is not None and r["매출채권"] >= 0) else None
            elif 변수이름 == "재고비율":
                v = (r.get("재고자산") / s) if (s and s > 0 and r.get("재고자산") is not None and r["재고자산"] >= 0) else None
            elif 변수이름 == "CAPEX비율":
                v = (r.get("CAPEX") / s) if (s and s > 0 and r.get("CAPEX") is not None and r["CAPEX"] >= 0) else None
            elif 변수이름 == "상각매출비율":                                  # 유지 CAPEX ÷ 매출(851)의 통상 대용 — 상각 = 유지 가정 [유추]
                v = (r.get("감가상각비") / s) if (s and s > 0 and r.get("감가상각비") is not None and r["감가상각비"] >= 0) else None
            elif 변수이름 == "상각률":
                a2 = r.get("유형자산")
                v = (r.get("감가상각비") / a2) if (a2 and a2 > 0 and r.get("감가상각비") is not None and r["감가상각비"] >= 0) else None
            else:
                # 상세변수(2026-10-24 PM — 패널 행의 「상세」 dict · 기저율.상세변수읽기) — 이름이 같은 계약 변수를 그대로 읽는다(정의는 짓는 도구의 목록.json)
                v = (r.get("상세") or {}).get(변수이름)
                if v is None and 변수이름 in ("매출원가율", "재고회전일수_원가"):
                    # 상세변수에 없으면 기본 패널의 본표 열로 같은 정의를 잰다(미국 FSDS 매출원가 · 재고자산 — 국내는 상세변수가 있다)
                    c0, inv = r.get("매출원가"), r.get("재고자산")
                    if 변수이름 == "매출원가율":
                        v = (c0 / s) if (s and s > 0 and c0 is not None and 0 <= c0) else None
                    else:
                        v = (inv / c0 * 365.0) if (c0 and c0 > 0 and inv is not None and inv >= 0) else None
            if v is not None and math.isfinite(v):
                m[y] = v
        if m:
            낸[고] = m
    return 낸


def 절단(계열, 분위):
    """전체 값의 [q_lo, q_hi] 밖을 뺀다. (남은 계열, 뺀 비중, 경계)."""
    v = sorted(x for m in 계열.values() for x in m.values())
    if len(v) < 10:
        return 계열, 0.0, None
    lo, hi = 기.분위(v, 분위[0]), 기.분위(v, 분위[1])
    남 = {}
    셈 = 0
    for 고, m in 계열.items():
        mm = {y: x for y, x in m.items() if lo <= x <= hi}
        셈 += len(m) - len(mm)
        if mm:
            남[고] = mm
    return 남, 셈 / len(v), (lo, hi)


# ═══════════════════════════════════════════════ 재기

def 순위(xs):
    """평균 순위(동점은 평균)."""
    순 = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(순):
        j = i
        while j + 1 < len(순) and xs[순[j + 1]] == xs[순[i]]:
            j += 1
        for k in range(i, j + 1):
            r[순[k]] = (i + j) / 2.0 + 1
        i = j + 1
    return r


def 순위상관(xs, ys):
    if len(xs) < 3:
        return None
    a, b = 순위(xs), 순위(ys)
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    sab = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    sa = math.sqrt(sum((x - ma) ** 2 for x in a))
    sb = math.sqrt(sum((y - mb) ** 2 for y in b))
    return (sab / (sa * sb)) if sa > 0 and sb > 0 else None


def 쌍(계열, k, 거르개=None):
    """(x_t, x_{t+k}) 쌍 — 거르개(고유번호 → bool)로 집단을 가른다."""
    xs, ys = [], []
    for 고, m in 계열.items():
        if 거르개 and not 거르개(고):
            continue
        for y, v in m.items():
            w = m.get(y + k)
            if w is not None:
                xs.append(v)
                ys.append(w)
    return xs, ys


def 연중앙값(계열, 거르개=None):
    해별 = {}
    for 고, m in 계열.items():
        if 거르개 and not 거르개(고):
            continue
        for y, v in m.items():
            해별.setdefault(y, []).append(v)
    return {y: statistics.median(v) for y, v in 해별.items()}


def ar1(계열, med, c, 거르개=None, 쪽=None):
    """ρ — Huber(절편 포함)로 (x_t − med_t) → (x_{t+1} − med_{t+1}). 쪽 = "아래" · "위" 면 x_t 가 그해 중앙값 아래 · 위인 쌍만."""
    xs, ys = [], []
    for 고, m in 계열.items():
        if 거르개 and not 거르개(고):
            continue
        for y, v in m.items():
            w = m.get(y + 1)
            if w is None or y not in med or (y + 1) not in med:
                continue
            d = v - med[y]
            if 쪽 == "아래" and d >= 0:
                continue
            if 쪽 == "위" and d <= 0:
                continue
            xs.append(d)
            ys.append(w - med[y + 1])
    if len(xs) < 30:
        return None, len(xs)
    ab = 기.huber(xs, ys, c)
    return ab[1], len(xs)


def 수렴프로필(계열, nq, K, 최소회사, 거르개=None):
    """10분위 수렴 — 기준 해마다 x_t0 로 nq 분위 포트폴리오를 짜고 t0+k 의 분위 중앙값 분산 ÷ t0 의 분산. 기준 해 평균. [1.0, …] 길이 K+1."""
    해들 = sorted({y for m in 계열.values() for y in m})
    비들 = [[] for _ in range(K + 1)]
    기준해수 = 0
    for t0 in 해들:
        ys = [t0 + i for i in range(K + 1)]
        sub = [[m[y] for y in ys] for 고, m in 계열.items() if (not 거르개 or 거르개(고)) and all(y in m for y in ys)]
        if len(sub) < max(최소회사, nq * 3):
            continue
        sub.sort(key=lambda v: v[0])
        n = len(sub)
        meds = []
        for k in range(K + 1):
            meds.append([statistics.median([v[k] for v in sub[i * n // nq:(i + 1) * n // nq]]) for i in range(nq)])
        v0 = statistics.pvariance(meds[0])
        if v0 <= 0:
            continue
        기준해수 += 1
        for k in range(K + 1):
            비들[k].append(statistics.pvariance(meds[k]) / v0)
    if not 기준해수:
        return None, 0
    return [round(sum(b) / len(b), 4) for b in 비들], 기준해수


def 연속초과(계열, med, ks, 거르개=None):
    """k년 내리 그해 중앙값을 넘은 비중 — {k: {비중, 기대, 회사수}}."""
    낸 = {}
    for k in ks:
        셈, 넘 = 0, 0
        for 고, m in 계열.items():
            if 거르개 and not 거르개(고):
                continue
            해 = sorted(m)
            for y in 해:
                ys = [y + i for i in range(k)]
                if not all(yy in m and yy in med for yy in ys):
                    continue
                셈 += 1
                if all(m[yy] > med[yy] for yy in ys):
                    넘 += 1
        낸[str(k)] = {"비중": round(넘 / 셈, 4) if 셈 else None, "기대": round(0.5 ** k, 4), "관측수": 셈}
    return 낸


def 집단거르개(넓은, 대상, 이름):
    if 이름 == "전체":
        return lambda 고: True
    if 이름 == "같은 규모":
        g = 대상.get("규모구간")
        return (lambda 고: 넓은.get(고, {}).get("규모구간") == g) if g else None
    if 이름 == "같은 산업 2자리":
        k2 = 대상.get("KSIC2")
        return (lambda 고: 넓은.get(고, {}).get("KSIC2") == k2) if k2 else None
    if 이름 == "운영 동종 산업":                      # 레터 v27 F2 — 핵심 표본 · 운영 동종(같은 분류 체계)의 산업 2자리 합집합. 대상 업종 하나와 같으면 「같은 산업」 과 겹쳐 세우지 않는다
        산 = set((대상.get("업종적합") or {}).get("운영동종산업") or [])
        if not 산 or 산 == {대상.get("KSIC2")}:
            return None
        return lambda 고: 넓은.get(고, {}).get("KSIC2") in 산
    return None


# 레터 v27 F3 · F4(2026-11-10) — 반감기 숫자를 레터에 실어도 되나. 설정 「노출」 이 있으면 그 값(결과 전에 정한 값)
노출기본 = {"반감_최소쌍": 1000, "반감_범위": [0.5, 15.0]}
노출차례 = ("운영 동종 산업", "같은 산업 2자리", "같은 규모", "전체")


def 형태판정(r1, 설정):
    """1년 순위상관 → 수렴형 · 느린수렴형 · 지속형(설정 「형태」 문턱). r1 이 없으면 None."""
    if r1 is None:
        return None
    F = (설정 or {}).get("형태") or {"수렴형_r1_미만": 0.5, "지속형_r1_이상": 0.7}
    return "수렴형" if r1 < F["수렴형_r1_미만"] else ("지속형" if r1 >= F["지속형_r1_이상"] else "느린수렴형")


def 노출판정(x, 설정):
    """변수 하나의 반감기 노출 → {싣기가능 · 까닭 · 집단 · 집단종류 · 반감햇수 · AR1 · 쌍수1 · 집단형태 · 형태 · 조건}.
    집단 차례 — 운영 동종 산업 → 같은 산업 2자리(업종 부적합이면 건너뜀) → 같은 규모 → 전체 가운데 1년 쌍이 문턱 이상이고 반감기가 선 첫 집단.
    그 집단의 반감기가 범위(기본 0.5~15년) 안이고 그 집단의 1년 순위상관으로 다시 매긴 형태가 변수의 형태 말(전체 집단)과 같을 때만 싣는다 —
    「오래 간다(… 0.4년)」 처럼 형태 말과 숫자가 다른 집단 · 다른 잣대에서 와 서로 어긋나는 문장을 막는다. 못 넘으면 숫자는 참고로만 남긴다."""
    노 = dict(노출기본, **(((설정 or {}).get("노출") or {})))
    최소쌍 = int(노.get("반감_최소쌍") or 노출기본["반감_최소쌍"])
    하, 상 = (노.get("반감_범위") or 노출기본["반감_범위"])[:2]
    조건 = {"최소쌍": 최소쌍, "범위": [하, 상], "차례": list(노출차례)}
    형 = x.get("형태")
    if 형 in (None, "표본 부족"):
        return {"싣기가능": False, "까닭": "변수의 형태가 서지 않았다(%s)" % (형 or "없음"), "형태": 형, "조건": 조건}
    후보 = []
    for 종 in 노출차례:
        for g in x.get("집단") or []:
            if g.get("집단종류") != 종 or g.get("싣기가능") is False:
                continue
            if ((g.get("쌍수") or {}).get("1") or 0) >= 최소쌍 and g.get("반감햇수") is not None:
                후보.append((종, g))
    if not 후보:
        return {"싣기가능": False, "까닭": "1년 쌍 %s개 이상이고 반감기가 선 집단이 없다" % "{:,}".format(최소쌍), "형태": 형, "조건": 조건}
    종, g = 후보[0]
    반 = g["반감햇수"]
    집형 = g.get("형태")
    까닭 = []
    if not (하 <= 반 <= 상):
        까닭.append("반감기 %.2f년이 %.1f~%.0f년 밖이다(추정이 흔들림)" % (반, 하, 상))
    if 집형 != 형:
        까닭.append("그 집단(%s)의 1년 순위상관으로 매긴 형태(%s)가 형태 말(%s — 전체 집단)과 다르다" % (g.get("집단"), 집형 or "없음", 형))
    return {"싣기가능": not 까닭, "까닭": " · ".join(까닭), "집단": g.get("집단"), "집단종류": 종, "반감햇수": 반, "AR1": g.get("AR1"),
            "쌍수1": (g.get("쌍수") or {}).get("1"), "집단형태": 집형, "형태": 형, "조건": 조건}


# ═══════════════════════════════════════════════ 가정 칸

def 예측열(벌):
    """{기간 ID: 값} 에서 TV 를 뺀 예측 열(값이 수인 것) — 파일의 열 차례 그대로."""
    return [(k, v) for k, v in 벌.items() if k != "TV" and isinstance(v, (int, float)) and not isinstance(v, bool)]


def 칸읽기(가정, 번호):
    """가정 번호의 시나리오별 예측 열 — {시나리오: [(열, 값)]} 또는 None. 「공통」이면 셋에 같이.
    시점가정(한 값 — 스칼라 또는 {시나리오: 값})은 [("시점", 값)] 한 열로 읽는다(2026-10-24 PM — 1인당 급여 · 내용연수 · 영구기간 영업이익률 칸)."""
    g = (가정.get("가정") or {}).get(번호)
    if not isinstance(g, dict):
        s = (가정.get("시점가정") or {}).get(번호)
        if isinstance(s, (int, float)) and not isinstance(s, bool):
            return {시: [("시점", float(s))] for 시 in 시나리오들}
        if isinstance(s, dict):
            낸 = {시: [("시점", float(s[시]))] for 시 in 시나리오들 if isinstance(s.get(시), (int, float)) and not isinstance(s.get(시), bool)}
            return 낸 or None
        return None
    if "공통" in g:
        열 = 예측열(g["공통"] or {})
        return {시: 열 for 시 in 시나리오들} if 열 else None
    낸 = {시: 예측열(g.get(시) or {}) for 시 in 시나리오들 if isinstance(g.get(시), dict)}
    낸 = {시: 열 for 시, 열 in 낸.items() if 열}
    return 낸 or None


# ═══════════════════════════════════════════════ 분석

def 분석(가정, 가정경로, 설정=None, 회사=None, 국가=None, 자리=None):
    설정 = 설정 or 설정읽기()
    기설 = 기.설정읽기()
    국, 기설, 까 = 기.국가맞춤(가정, 기설, 국가)
    if not 국:
        return 기.해당없음("지속성 1", 가정경로, 까, 설정, "지속성"), ""
    행, 패널입력 = 기.패널읽기(자리, 기설)
    if not 행:
        return 기.해당없음("지속성 1", 가정경로, "%s 패널이 비었다(%s) — `기저율.py --받기 --국가 %s` 를 먼저" % (국, 패널입력["자리"], 국),
                       설정, "지속성"), ""
    남, 뺀 = 기.자료제외(행, 기설)
    넓은 = 기.넓히기(남)
    M = 설정["측정"]
    신호, 제안 = [], []

    def 신(종류, 대상글, 값, 문턱, 글, 등급="참고"):
        신호.append({"출처": "지속성", "종류": 종류, "대상": 대상글, "값": 값, "문턱": 문턱, "글": 글, "등급": 등급})

    # 대상 — 못 찾아도 멈추지 않는다(전체 집단만)
    고, 산업, 까 = 기.대상찾기(가정, 가정경로, 행, 회사, 기설)
    대상 = {"고유번호": 고, "회사명": (가정.get("메타") or {}).get("회사명"), "국가": 국, "산업분류": 산업,
          "KSIC2": 산업[:2] if 산업 and len(산업) >= 2 else None, "규모구간": None, "식별": "" if 고 else 까}
    if 고 and 고 in 넓은:
        마지막 = max(넓은[고]["해"])
        대상["규모구간"] = 기.규모구간(넓은[고]["해"][마지막].get("매출액"), 기설)
    else:
        배율 = 기._수((가정.get("메타") or {}).get("환산배율")) or 1.0
        원 = (가정.get("원천") or {}).get("62") or {}
        실 = [기._수(v) for k, v in 원.items() if k.endswith("A") and 기._수(v)]
        if 실:
            대상["규모구간"] = 기.규모구간(실[-1] * 배율, 기설)
            대상["규모출처"] = "원천 62(매출액) 마지막 실적 열 × 환산배율"
    for 고2, d in 넓은.items():
        마 = max(d["해"])
        d["규모구간"] = 기.규모구간(d["해"][마].get("매출액"), 기설)
    분류 = 기설.get("_산업분류") or "KSIC"
    대상["업종적합"] = 기.업종적합(가정경로, 대상, 기설, 패널입력["자리"])          # 레터 v27 F1 · F2
    업종부적합 = 대상["업종적합"].get("적합") is False
    집단차례 = list(M["집단"]) + (["운영 동종 산업"] if "운영 동종 산업" not in M["집단"] else [])

    # 변수마다
    변수들 = []
    형태 = {}
    for 변 in 설정["변수"]:
        이름 = 변["이름"]
        계열 = 변수계열(넓은, 이름)
        if 고:
            계열 = {g: m for g, m in 계열.items() if g != 고}      # 대상은 뺀다 — 자기 자신을 같은 집단으로 세지 않게
        계열, 뺀비중, 경계 = 절단(계열, M["절단분위"])
        x = {"이름": 이름, "종류": 변["종류"], "정의": 변["정의"], "관측수": sum(len(m) for m in 계열.values()),
             "회사수": len(계열), "절단비중": round(뺀비중, 4), "절단경계": 경계, "집단": [], "형태": None, "형태근거": None}
        for 집이름 in 집단차례:
            f = 집단거르개(넓은, 대상, 집이름)
            if f is None:
                continue
            라벨 = 집이름 if 집이름 != "같은 산업 2자리" else "%s %s" % (분류, 대상["KSIC2"])
            if 집이름 == "같은 규모":
                라벨 = "같은 규모(%s)" % 대상["규모구간"]
            if 집이름 == "운영 동종 산업":
                라벨 = "운영 동종 산업(%s %s)" % (분류, " · ".join(대상["업종적합"]["운영동종산업"]))
            med = 연중앙값(계열, f)
            한 = {"집단": 라벨, "집단종류": 집이름, "순위상관": {}, "쌍수": {}}
            if 집이름 == "같은 산업 2자리" and 업종부적합:           # F2 — 계산은 하되 노출 후보에서 뺀다
                한["싣기가능"] = False
                한["안싣는까닭"] = "업종 부적합 — %s" % 대상["업종적합"].get("까닭")
            for k in M["상관창_년"]:
                xs, ys = 쌍(계열, k, f)
                한["쌍수"][str(k)] = len(xs)
                한["순위상관"][str(k)] = round(순위상관(xs, ys), 4) if len(xs) >= M["최소쌍"] and 순위상관(xs, ys) is not None else None
            ρ, n1 = ar1(계열, med, M["Huber_c"], f)
            한["AR1"] = round(ρ, 4) if ρ is not None else None
            한["반감햇수"] = round(math.log(0.5) / math.log(ρ), 2) if (ρ is not None and 0 < ρ < 1) else None
            아, _ = ar1(계열, med, M["Huber_c"], f, "아래")
            위, _ = ar1(계열, med, M["Huber_c"], f, "위")
            한["비대칭"] = {"아래": round(아, 4) if 아 is not None else None, "위": round(위, 4) if 위 is not None else None}
            프, 기준해수 = 수렴프로필(계열, M["수렴_분위수"], M["수렴_추적연수"], M["수렴_최소회사"], f)
            한["수렴프로필"] = 프
            한["수렴_기준해수"] = 기준해수
            if 변["종류"] == "변화":
                한["연속초과"] = 연속초과(계열, med, M["연속초과_k"], f)
            한["표본부족"] = (한["쌍수"].get("1", 0) < M["최소쌍"])
            한["형태"] = 형태판정(한["순위상관"].get("1"), 설정)           # F4 — 그 집단의 1년 순위상관으로 매긴 형태(노출 판정이 형태 말과 맞댄다)
            x["집단"].append(한)
        전 = next((g for g in x["집단"] if g["집단"] == "전체"), None)
        r1 = 전["순위상관"].get("1") if 전 else None
        if r1 is None:
            x["형태"], x["형태근거"] = "표본 부족", "전체 집단 1년 쌍이 %d개 미만" % M["최소쌍"]
            신("표본 부족", 이름, 전["쌍수"].get("1") if 전 else 0, M["최소쌍"], "%s 의 1년 쌍이 모자라 지속성을 재지 않았다" % 이름)
        else:
            F = 설정["형태"]
            x["형태"] = "수렴형" if r1 < F["수렴형_r1_미만"] else ("지속형" if r1 >= F["지속형_r1_이상"] else "느린수렴형")
            x["형태근거"] = "전체 집단 1년 순위상관 %.2f(3년 %s · 5년 %s) · AR(1) %s · 반감 %s해 · 아래 %s / 위 %s" % (
                r1, 전["순위상관"].get("3"), 전["순위상관"].get("5"), 전["AR1"], 전["반감햇수"], 전["비대칭"]["아래"], 전["비대칭"]["위"])
            if 변["종류"] == "변화" and 전.get("연속초과"):
                for k, c in 전["연속초과"].items():
                    if c["비중"] is not None and c["비중"] > 2 * c["기대"]:
                        신("연속 초과 — 지속", "%s %s년" % (이름, k), c["비중"], c["기대"],
                          "%s 이 %s년 내리 중위를 넘은 회사 비중 %.1f%% — 우연 %.1f%% 의 두 배 넘음(지속하는 쪽)" % (이름, k, c["비중"] * 100, c["기대"] * 100))
        x["노출"] = 노출판정(x, 설정)                                   # F3 — 레터가 반감기 숫자를 실어도 되나(변수카드가 읽는다)
        형태[이름] = x["형태"]
        변수들.append(x)

    # 가정 칸 대조 — 부류마다
    G = 설정["가정대조"]
    칸들 = []
    부류변수 = {}
    for 변 in 설정["변수"]:
        for 부 in 변.get("닿는부류") or []:
            부류변수.setdefault(부, []).append(변["이름"])
    for 부, 정 in 설정["칸부류"].items():
        if 부.startswith("_"):
            continue
        변이름들 = list(정.get("변수차례") or 부류변수.get(부) or [])
        # 주 변수 — 부류에 닿는 변수 가운데 **형태가 선 첫 것**(상세 패널이 없어 표본 부족이면 다음 변수 — 예: 매출채권비율 → 자산회전율 근사). 차례는 설정 `변수차례`
        주 = next((n for n in 변이름들 if 형태.get(n) not in (None, "표본 부족")), None) or (변이름들[0] if 변이름들 else None)
        주변 = next((x for x in 변수들 if x["이름"] == 주), None) if 주 else None
        근사 = bool(정.get("근사")) or (bool(변이름들) and 주 != 변이름들[0])
        주형태 = 주변["형태"] if 주변 else None
        전 = next((g for g in (주변["집단"] if 주변 else []) if g["집단"] == "전체"), None)
        r1 = (전 or {}).get("순위상관", {}).get("1")
        변화변 = next((x for x in 변수들 if x["이름"] in 변이름들 and x["종류"] == "변화" and x["이름"] != 주), None)
        변화r1 = next((g["순위상관"].get("1") for g in (변화변["집단"] if 변화변 else []) if g["집단"] == "전체"), None)
        # 분위띠 — 수렴형 한 값 판정용(주 변수의 전체 분포)
        띠 = None
        if 주변 and 주형태 == "수렴형":
            v = sorted(x for m in 변수계열(넓은, 주).values() for x in m.values())
            if len(v) >= 10:
                띠 = (기.분위(v, G["한값_분위띠"][0]), 기.분위(v, G["한값_분위띠"][1]))
        적힌 = []
        for 번호 in 정["번호"]:
            열들 = 칸읽기(가정, 번호)
            if not 열들:
                continue
            칸 = {"번호": 번호, "부류": 부, "변수": 주, "근사": 근사, "형태": 주형태, "시나리오": {}, "판정": []}
            for 시, 열 in 열들.items():
                값 = [v for _k, v in 열]
                한값 = (max(값) - min(값)) <= G["한값_문턱"]
                s = {"열수": len(값), "첫": 값[0], "끝": 값[-1], "한값": 한값}
                칸["시나리오"][시] = s
                if 주형태 == "수렴형" and 한값 and len(값) >= 3 and not (G.get("한값_영은_제외", True) and abs(값[0]) <= 1e-12):
                    밖 = bool(띠 and (값[0] < 띠[0] or 값[0] > 띠[1]))
                    등급 = "경보" if 밖 else "참고"
                    글 = ("%s 의 %s 열 %d개가 한 값(%.4g)이다 — 같은 집단에서 %s 의 1년 순위상관은 %.2f(수렴형 — 올해 값이 내년을 거의 못 알려 준다)%s. "
                          "한 값으로 둔 까닭(계약 · 능력 · 외부 제약)을 근거 칸에 적는다"
                          % (시, "A-%s" % 번호, len(값), 값[0], 주, r1, (" · 그 값은 패널 분포의 25~75%% 띠(%.3f~%.3f) 밖" % 띠) if 밖 else ""))
                    칸["판정"].append({"시나리오": 시, "종류": "수렴형 한 값", "등급": 등급})
                    신("수렴형 변수를 한 값으로", "%s A-%s%s" % (시, 번호, "(근사)" if 근사 else ""), 값[0],
                      "1년 상관 %.2f" % r1, 글, 등급)
                elif 주형태 in ("지속형", "느린수렴형") and len(값) >= 2:
                    차 = 값[-1] - 값[0]
                    크다 = (abs(차) > G["수준변화_문턱_p"]) if 부 in 율부류 else (abs(차) > G["회전변화_상대문턱"] * abs(값[0]) if 값[0] else False)
                    if 크다:
                        칸["판정"].append({"시나리오": 시, "종류": "수준 변화 가정", "등급": "참고"})
                        신("수준 변수를 옮기는 가정", "%s A-%s%s" % (시, 번호, "(근사)" if 근사 else ""), round(차, 4),
                          ("%.0f%%p" % (G["수준변화_문턱_p"] * 100)) if 부 in 율부류 else ("%.0f%%" % (G["회전변화_상대문턱"] * 100)),
                          "%s 의 %s 가 첫 열 %.4g 에서 끝 열 %.4g 로 옮겨 간다 — 같은 집단에서 %s 수준의 1년 상관은 %.2f(지속)이지만 그 **변화**의 1년 상관은 %s(일시적). "
                          "옮겨 간 수준이 지속되는 근거(능력 · 계약 · 동종 수준)를 근거 칸에 적는다"
                          % (시, "A-%s" % 번호, 값[0], 값[-1], 주, r1, ("%.2f" % 변화r1) if 변화r1 is not None else "표본 부족"))
            칸들.append(칸)
            적힌.append(번호)
        if 적힌 and 주변:
            제안.append({"자리": " · ".join("A-%s" % n for n in 적힌) + "(%s)" % 정["글"], "값": None, "근거범위": None,
                        "딱지": "[%s — 같은 집단 지속성(%s %s)]" % ("유추" if 근사 else "관측", 국, 주),
                        "확신": "중" if (전 and not 전.get("표본부족")) else "약",
                        "글": "경로 형태 %s — %s" % (주형태, 주변["형태근거"])})

    # ── 80% 띠와 사후대조 보정(2026-10-23 밤 W8) — 칸마다 1 · 2년 뒤 · 보정표가 있을 때만 보정
    #   F2 — 업종 부적합이면 띠의 집단 차례에서 산업 2자리를 뺀다(같은 규모 → 전체로 선다 · 산출에 「업종집단뺌」)
    대상띠 = dict(대상, KSIC2=None) if 업종부적합 else 대상
    보정상태 = 보정띠붙이기(넓은, 기설, 대상띠, 칸들, 제안, 신, 국, 패널입력["자리"], 설정.get("보정"), 덮개=자산군대응(가정))
    if 업종부적합 and isinstance(보정상태, dict):
        보정상태["업종집단뺌"] = True
        보정상태["업종집단뺌_까닭"] = 대상["업종적합"].get("까닭")

    사유 = {}
    for x in 뺀:
        사유[x[3]] = 사유.get(x[3], 0) + 1
    낸 = {"형식": "지속성 1", "만든날": datetime.date.today().isoformat(), "설정": 설정,
          "입력": {"가정": os.path.abspath(가정경로), "국가": 국, "패널자리": 패널입력["자리"], "패널연도": 패널입력["연도"],
                 "기저율설정_국가블록": (기설.get("국가별") or {}).get(국)},
          "패널": {"회사연도": len(행), "정리후_회사연도": len(남), "정리후_회사수": len(넓은), "제외_사유별": 사유},
          "대상": 대상, "폴백": None if any(x["형태"] not in (None, "표본 부족") for x in 변수들) else "전 변수 표본 부족 — 기존 규칙(곧은 선) 그대로",
          "변수": 변수들, "형태요약": 형태, "칸": 칸들, "제안": 제안, "신호": 신호, "보정": 보정상태, "업종적합": 대상["업종적합"]}
    if not 고:
        신("대상 식별 못함", "대상회사", None, None, "%s — 전체 집단 · 매출 규모 구간만으로 쟀다(같은 산업 집단 없음)" % 까)
    return 낸, ""


def _환산(쌍, 배):
    return [쌍[0] * 배, 쌍[1] * 배] if 쌍 else None


def _범위환산(넓은, 대상, 변수, 칸):
    """범위 환산 배수(P1 — 1인당 급여 503) = 칸의 첫 값 ÷ 대상 회사의 그 변수 마지막 패널 값. 공시(본사 · 별도)와 모델(연결 급여 ÷ 본사 인원)의 범위 차이를
    그 회사 한 곳의 비율로 옮긴다 — 같은 집단 띠에 곱하면 「같은 범위의 급여 수준이었다면」 의 띠가 된다. 대상의 패널 값이 없으면 (None, None) — 띠를 세우지 않는다."""
    고 = 대상.get("고유번호")
    d = 넓은.get(고) if 고 else None
    if not d:
        return None, None
    값들 = [(y, (r.get("상세") or {}).get(변수)) for y, r in d["해"].items()]
    값들 = [(y, v) for y, v in 값들 if v]
    시 = (칸.get("시나리오") or {}).get("기준") or next(iter((칸.get("시나리오") or {}).values()), None)
    첫 = (시 or {}).get("첫")
    if not 값들 or not 첫:
        return None, None
    y, v = max(값들)
    return 첫 / v, "범위 환산 배수 %.4g = 칸 첫 값 %.4g ÷ 대상의 %s %d년 %.4g(공시 본사 기준 → 모델 범위)" % (첫 / v, 첫, 변수, y, v)


def 자산군대응(가정):
    """내용연수 칸(80g)의 후보를 자산군 이름으로 가른다(2026-10-24 PM) — 기계 · 설비 · 장치 · 공구면 기계장치 내용연수(같은 정의), 자산군이 하나뿐이면
    평균 내용연수(유형자산 전체 — 같은 정의), 그 밖(건물 등)은 평균 내용연수를 정의가 다른 참고로만. → {번호: [후보]}."""
    군 = (((가정.get("구조") or {}).get("투자") or {}).get("자산군")) or []
    군 = [x for x in 군 if isinstance(x, dict) and x.get("번호")]
    낸 = {}
    for x in 군:
        번 = "80%d" % int(x["번호"])
        이 = "%s" % (x.get("이름") or "")
        if any(w in 이 for w in ("기계", "설비", "장치", "공구", "machinery", "Machinery", "equipment", "Equipment")):
            낸[번] = [("기계장치내용연수", 1.0, True, "관측"), ("평균내용연수", 1.0, False, "유추")]
        elif len(군) == 1:
            낸[번] = [("평균내용연수", 1.0, True, "유추")]
        else:
            낸[번] = [("평균내용연수", 1.0, False, "유추")]
    return 낸


def 보정띠붙이기(넓은, 기설, 대상, 칸들, 제안, 신, 국, 패널자리, 끄기=None, 덮개=None):
    """칸들(가정 칸 대조 결과)에 `띠[]` 를 붙이고 칸 단위로 옮길 수 있는 칸은 제안을 더한다 → 보정 상태 dict.
    띠 = [{k · 변수 · 환산 · 칸단위 · 딱지 · 기저율{띠집단 · n · 보정전 · 가운데 · 보정뒤 · 보정} · 지속성{…}}] — 값은 칸 단위(환산 뒤)."""
    import 사후대조 as 사후                                     # noqa: PLC0415
    if 끄기 is False:
        return {"상태": "끔", "글": "지속성설정 「보정」: false — 띠를 세우지 않았다"}
    표, 상태, 글 = 사후.보정표읽기(국, 패널자리)
    if 상태 == "낡음":
        신("보정표 낡음", "사후대조 보정표", None, None, 글)
    낸 = {"상태": 상태, "글": 글, "패널판": ((표 or {}).get("패널") or {}).get("판"), "칸수": 0, "보정칸수": 0}
    for 칸 in 칸들:
        대 = (덮개 or {}).get("%s" % 칸["번호"]) or 보정대응.get("%s" % 칸["번호"])
        if not 대:
            continue
        후보들 = 대 if isinstance(대, list) else [대]
        띠들, 못 = [], []
        for 변수, 배, 칸단위, 딱 in 후보들:                          # 패널에 띠가 서는 첫 후보(국가마다 변수가 다르다 — 2026-10-24 PM)
            배글 = None
            if 배 == "범위환산":
                배, 배글 = _범위환산(넓은, 대상, 변수, 칸)
                if 배 is None:
                    못.append("%s — 범위 환산 배수를 못 구함" % 변수)
                    continue
            for k in 보정앞날대응.get("%s" % 칸["번호"], 보정앞날):
                b = 사후.띠짓기(넓은, 변수, k, 기설, 대상)
                if not b or not (b.get("기저율") or b.get("지속성")):
                    continue
                보 = 사후.보정띠(b, 표, 대상)
                한 = {"k": k, "변수": 변수, "환산": 배, "칸단위": 칸단위, "딱지": 딱, "기준값": (b["값"] * 배) if b.get("값") is not None else None,
                     "기준해": b.get("해")}
                if 배글:
                    한["환산글"] = 배글
                for 종류, v in 보.items():
                    한[종류] = dict(v, 보정전=_환산(v["보정전"], 배), 보정뒤=_환산(v["보정뒤"], 배), 가운데=v["가운데"] * 배)
                띠들.append(한)
            if 띠들:
                break
            못.append("%s — %s" % (변수, "이 나라 패널에 없음" if not any(변수계열(넓은, 변수).values()) else "같은 집단 표본 부족"))
        if not 띠들:
            칸["띠없음"] = 못                                     # 빈칸 금지(P1 기준 ③) — 띠가 왜 없는지 이름을 남긴다
            continue
        칸["띠"] = 띠들
        낸["칸수"] += 1
        if any((t.get(종) or {}).get("보정뒤") for t in 띠들 for 종 in ("기저율", "지속성")):
            낸["보정칸수"] += 1
        if not 칸단위:
            continue
        근, 근전, 보정들 = {}, {}, []
        for t in 띠들:
            주 = t.get("지속성") or t.get("기저율")                 # 회사의 지금 자리를 보는 띠(지속성)가 먼저 — 없으면 기저율 띠
            if not 주:
                continue
            라 = "%d년 뒤" % t["k"]
            근전[라] = 주["보정전"]
            근[라] = 주["보정뒤"] or 주["보정전"]
            if 주.get("보정"):
                보정들.append("%s %s(%s)" % (라, 사후.q글(주["보정"]), 주["띠집단"]))
        if not 근:
            continue
        종류말 = "지속성" if 띠들[0].get("지속성") else "기저율"
        제안.append({"자리": "A-%s(같은 집단 80%% 띠 — %s)" % (칸["번호"], 변수), "값": None, "근거범위": 근, "근거범위_보정전": 근전,
                    "보정": 보정들 or None,
                    "딱지": "[%s — 같은 집단 80%% 띠(%s %s)%s]" % (딱, 국, 종류말, (" · 사후대조 보정 " + " · ".join(보정들)) if 보정들 else " · 보정 없음"),
                    "확신": "중" if 보정들 else "약",
                    "글": "같은 집단에서 1 · 2년 뒤 값의 10~90%% 분위(%s 띠)%s — 값을 정하지 않는다"
                         % (종류말, " · 사후대조 보정표로 양 끝을 옮겼다(가운데는 그대로)" if 보정들 else "")})
    return 낸


def _q글(보):
    """W9 — 보정 dict 의 q 를 한 말로(꼬리별이 다르면 「q 아래 a · 위 b」). 사후대조.q글 과 같다 — 표찍기는 사후대조를 부르지 않고 쓴다."""
    import 사후대조 as 사후                                     # noqa: PLC0415
    return 사후.q글(보)


def 표찍기(낸):
    대 = 낸["대상"]
    print("지속성 — %s(%s) · 패널 %s %d 회사-연도(정리 후 %d · 회사 %d)"
          % (대.get("회사명"), 대.get("고유번호") or "식별 못함", 낸["입력"]["국가"], 낸["패널"]["회사연도"], 낸["패널"]["정리후_회사연도"], 낸["패널"]["정리후_회사수"]))
    print("  %-12s %-8s %6s %6s %6s %6s %7s  %-16s %s" % ("변수", "형태", "r1", "r3", "r5", "AR1", "반감", "아래/위", "10분위 수렴(k=1..5)"))
    for x in 낸["변수"]:
        전 = next((g for g in x["집단"] if g["집단"] == "전체"), None) or {}
        rc = 전.get("순위상관") or {}
        f = lambda v: ("%.2f" % v) if isinstance(v, (int, float)) else "-"                        # noqa: E731
        비 = 전.get("비대칭") or {}
        프 = 전.get("수렴프로필")
        print("  %-12s %-8s %6s %6s %6s %6s %7s  %-16s %s" % (x["이름"], x["형태"] or "-", f(rc.get("1")), f(rc.get("3")), f(rc.get("5")),
                                                          f(전.get("AR1")), f(전.get("반감햇수")), "%s / %s" % (f(비.get("아래")), f(비.get("위"))),
                                                          " ".join("%.2f" % p for p in 프[1:]) if 프 else "-"))
    print("  칸 %d · 제안 %d · 신호 %d건" % (len(낸["칸"]), len(낸["제안"]), len(낸["신호"])))
    보 = 낸.get("보정") or {}
    if 보:
        print("  80%% 띠 — 칸 %s · 보정한 칸 %s · %s" % (보.get("칸수", 0), 보.get("보정칸수", 0), 보.get("글")))
        for 칸 in 낸["칸"]:
            for t in 칸.get("띠") or []:
                v = t.get("지속성") or t.get("기저율")
                if not v or not t.get("칸단위"):
                    continue
                뒤 = v.get("보정뒤")
                print("    A-%s %d년 뒤 %s 띠(%s · n %d) %.4g ~ %.4g%s" % (칸["번호"], t["k"], "지속성" if t.get("지속성") else "기저율", v["띠집단"], v["n"],
                                                                v["보정전"][0], v["보정전"][1],
                                                                (" → 보정 %.4g ~ %.4g(%s)" % (뒤[0], 뒤[1], _q글(v["보정"]))) if 뒤 else " · 보정 없음"))
    for s in 낸["신호"]:
        print("   · [%s] %s — %s: %s" % (s["등급"], s["종류"], s["대상"], s["글"][:160]))


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="지속성 — 변수마다 되돌아가는 속도를 같은 집단에서 재고 가정 칸의 경로 형태를 대 본다")
    ap.add_argument("가정")
    ap.add_argument("--회사", help="대상 고유번호(KR 8자리 · US CIK)")
    ap.add_argument("--국가", help="패널 국가(KR · US) — 기본은 가정 메타.표시통화")
    ap.add_argument("--낼", help="산출 경로(기본: 가정 곁 _raw/지속성.json)")
    ap.add_argument("--설정", help="설정 파일(기본: 스크립트 곁 지속성설정.json)")
    a = ap.parse_args()
    try:
        가정 = json.load(io.open(a.가정, encoding="utf-8"))
        설정 = 설정읽기(a.설정)
    except (OSError, ValueError) as e:
        print("가정 · 설정 파일을 못 읽었다 — %s" % e)
        return 입력오류
    낸, 까 = 분석(가정, a.가정, 설정, a.회사, a.국가)
    if 낸 is None:
        print("입력오류 — %s" % 까)
        return 입력오류
    p = a.낼 or os.path.join(os.path.dirname(os.path.abspath(a.가정)), "_raw", "지속성.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, "w", encoding="utf-8").write(json.dumps(낸, ensure_ascii=False, indent=1, default=str))
    if 낸.get("해당없음"):
        print("지속성 — 해당 없음: %s" % 낸["해당없음"])
    else:
        표찍기(낸)
    print("→ %s" % p)
    return 통과


if __name__ == "__main__":
    sys.exit(main())

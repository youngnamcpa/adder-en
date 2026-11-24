# -*- coding: utf-8 -*-
"""사후대조 — 근거 범위가 실제로 몇 %를 담았나(패널 백테스트)와, 지난 회차 예측이 실적과 얼마나 갈렸나(회차 대조) (2026-10-23 밤 신설).

왜 만들었나
  거친 바퀴 · 멈춤 문항의 「근거 범위」는 같은 집단의 분위(기저율.py)와 되돌아가는 속도(지속성.py)에서 온다. 그 띠가 **실제로 다음 해 값을
  몇 % 담는지** 잰 적이 없었다 — 80% 띠라 부르면서 60%만 담으면 시나리오 폭이 좁고, 95%를 담으면 넓다. 실무 백테스트의 빈자리이기도 하다
  (연구/ADDER_개선방향_총정리_20261023.md 2-5 ③ — 사후대조 1순위 · 연구/참고_AI현금흐름예측.md 「백테스트 없음」).
  **값을 정하지 않는다.** 층 1 은 띠의 폭을 얼마나 넓히거나 좁혀야 목표 포함률이 나오는지(보정계수)를 집단마다 내고, 층 2 는 지난 회차의
  예측과 새 실적의 차이를 항목마다 내고 동인 그래프 상류의 손잡이를 짚을 뿐이다. 무엇을 고칠지는 사람이 정한다.

층 1 — 패널 전수(공용 캐시의 기저율 패널 · 국내 KR · 미국 US)
  기준 해 T0 마다 **T0 에 알 수 있던 관측만으로**(결과가 T0 이전에 끝난 쌍만) 띠 둘을 다시 세운다.
    기저율 띠  같은 집단의 k년 뒤 값 분포(성장은 k년 CAGR) — 회사의 지금 자리를 보지 않는다
    지속성 띠  같은 집단 · 같은 10분위(T0 값)의 k년 뒤 값 분포 — 수준 변수는 「지금 값 + 변화량 분위」, 성장은 CAGR 분위
  그리고 T0 + k 실현값이 P10~P90(80%) · P25~P75(50%)에 든 비율 · PIT(실현값이 띠 표본의 몇 분위였나 — 고르면 띠가 맞다) · 대조군 오차
  (직전 값 그대로 · 직전 3년 평균(성장은 3년 CAGR) · 띠 가운데)를 집단(전체 · 규모 · 산업 2자리)마다 낸다.
  보정계수 — 분할 등각 예측(split conformal)의 꼴: 정규화 거리 s = |실현 − 가운데| ÷ (가운데에서 그쪽 띠 끝까지)를 앞 절반 기준 해에서 재
  목표 분위(⌈(n+1)·0.8⌉/n)를 q 로 두고, 뒤 절반 기준 해에서 「q 배로 늘린 띠」의 포함률을 검증한다. q > 1 = 띠가 좁다 · q < 1 = 넓다.
  모든 기준 해로 잰 q(보정계수_전체)가 다음 회차가 읽을 값이다(`~/.dcf캐시/사후대조/보정표_<국가>.json`).
  2026-10-24 W9 — **꼬리별 보정**(위 · 아래 끝을 따로: 위 거리 u = (실현 − 가운데) ÷ (위 끝 − 가운데) · 아래 거리 d 의 목표 분위
  1 − (1 − 목표)/2 = 0.9 를 각각 — 대칭 q 는 max(u, d) 의 0.8 분위) · **최근 창 보정**(최근 기준 해 몇 개로만 맞춘 `보정계수_최근`) ·
  **정직 평가**(기준 해 T 를 평가할 때 결과가 T 까지 끝난 기준 해(T − k 이하)로만 맞춘 q — rolling origin)로 네 방식(대칭 · 꼬리별 × 전체 창 ·
  최근 창)과 보정 없음의 포함률 · 위 꼬리 · 아래 꼬리를 집단마다 잰다(`정직평가`). 다음 회차가 읽는 방식은 설정 「보정.채택」 이 정한다(보정표에 적힌다).
층 2 — 회차 대조(틀)
  지난 회차 가정의 예측 열(엔진 결과)과 새 회차 가정의 실적 열을 기간(시작일 · 종료일)으로 맞대 항목(매출 · 원가 · 판관 · 영업이익 ·
  CAPEX · 순운전자본 · 법인세)과 비율(영업이익률 · 원가율 · 판관비율 · 실효세율)의 오차를 낸다. 반기 예측은 새 회계연도 실적 − 지난 회차의
  누계 실적으로 맞댄다(흐름 줄만). 오차가 큰 줄은 지난 회차 `_raw/동인그래프.json` 의 상류를 짚어 손잡이(가정 번호)를 적고, 그 가운데
  근거 칸에 「[판단]」 이 있는 칸(사람이 정한 칸)을 따로 표시한다.

사용
  python 스크립트/사후대조.py 패널 --국가 KR [--표본 0.3] [--출력 보정표.json] [--md 요약.md]
  python 스크립트/사후대조.py 회차 --지난 <지난 회차>/가정_X.json --새 <새 회차>/가정_X.json [--그래프 <지난>/_raw/동인그래프.json] [--출력 …]
읽는 것 — 기저율.패널읽기 · 자료제외 · 넓히기 · 규모구간(국가 축) · 지속성.변수계열 · 절단(변수 정의를 두 벌 두지 않는다) · `사후대조설정.json` · 엔진(층 2)
종료 코드 — 0 통과 · 1 발견(패널이 비었다 · 맞댈 기간이 없다) · 2 입력오류. 회사 · 업종 이름은 이 도구에 없다(범용). 표준 라이브러리만 쓴다.
"""
from __future__ import annotations

import argparse
import bisect
import collections
import datetime
import hashlib
import io
import json
import math
import os
import random
import re
import sys
import time
from array import array

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류  # noqa: E402

형식 = "사후대조 보정표 1"
설정경로 = os.path.join(여기, "사후대조설정.json")


def 설정읽기(경로=None):
    return json.load(io.open(경로 or 설정경로, encoding="utf-8"))


def 공용뿌리():
    return (os.environ.get("DCF_공용캐시") or os.environ.get("DCF_SHARED_CACHE")
            or os.path.join(os.path.expanduser("~"), ".dcf캐시"))


def 분위(xs, q):
    """선형 보간 분위(xs 는 정렬됨) — 기저율.분위와 같은 방식."""
    if not xs:
        return None
    pos = q * (len(xs) - 1)
    lo, hi = int(math.floor(pos)), int(math.ceil(pos))
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def 등각분위(점수, 목표):
    """분할 등각 예측의 분위 — ⌈(n+1)·목표⌉ 번째 작은 값(n 이 작아 그 자리가 n 을 넘으면 무한대 = 띠를 정할 수 없다)."""
    n = len(점수)
    if not n:
        return None
    k = math.ceil((n + 1) * 목표)
    if k > n:
        return float("inf")
    return sorted(점수)[k - 1]


# ══════════════════════════════════════════════════════════ 층 1 — 관측

def 관측짓기(넓은, 변, k, 기설, 절단분위, 지속, 자리=None):
    """변수 하나 · 앞날 k → [(고유번호, t, x(조건 값), 결과, 직전값 예측, 직전3년 예측, 규모, 산업2)] 와 {t: 정렬된 x} (10분위 경계용).
    설정 변수에 「원천」: 「상세변수」 가 있으면 계열을 상세변수 계약 CSV 에서 그대로 읽는다 — 본표 패널 행이 없는 해까지(2026-10-24 PN ·
    213 의 5 · 10년 뒤는 기준 해가 2k 넘게 있어야 정직 평가가 선다). 회사는 넓은(제외 산업 · 매출 하한을 거친 패널)에 있는 곳만이고,
    그 해 본표 행이 없으면 규모 집단이 서지 않는다(전체 · 산업 집단으로만 센다)."""
    import 기저율 as 기                                       # noqa: PLC0415
    낸 = []
    if 변["종류"] == "성장":
        g = 지속.변수계열(넓은, "매출성장률")
        g, _, _ = 지속.절단(g, 절단분위)
        하한 = 기설["자료_제외"]["기준연도_매출_하한_원"]
        for 고, d in 넓은.items():
            해, gi = d["해"], g.get(고) or {}
            for t, r in 해.items():
                s0 = r.get("매출액")
                if t not in gi or not s0 or s0 < 하한:
                    continue
                r1 = 해.get(t + k)
                if not (r1 and r1.get("매출액") and r1["매출액"] > 0):
                    continue
                r3 = 해.get(t - 3)
                n3 = (s0 / r3["매출액"]) ** (1.0 / 3) - 1 if (r3 and r3.get("매출액") and r3["매출액"] > 0) else None
                낸.append((고, t, gi[t], (r1["매출액"] / s0) ** (1.0 / k) - 1, gi[t], n3, 기.규모구간(s0, 기설), d.get("KSIC2")))
        계열 = g
    else:
        if 변.get("원천") == "상세변수":
            상 = 기.상세변수읽기(자리 or 기.패널자리(기설), 기설.get("_국가"), int(기설.get("_고유번호자릿수") or 8)).get(변["이름"]) or {}
            계열 = {고: dict(상[고]) for 고 in 넓은 if 상.get(고)}
        else:
            계열 = 지속.변수계열(넓은, 변["이름"])
        계열, _, _ = 지속.절단(계열, 절단분위)
        for 고, m in 계열.items():
            d = 넓은[고]
            for t, v in m.items():
                y = m.get(t + k)
                if y is None:
                    continue
                앞 = [m.get(t - j) for j in range(3)]
                n3 = sum(앞) / 3 if all(x is not None for x in 앞) else None
                s0 = (d["해"].get(t) or {}).get("매출액")
                낸.append((고, t, v, y, v, n3, 기.규모구간(s0, 기설), d.get("KSIC2")))
    경계 = collections.defaultdict(list)
    for 고, m in 계열.items():
        for t, v in m.items():
            경계[t].append(v)
    return 낸, {t: sorted(v) for t, v in 경계.items()}


def _십분위(경계t, x, nq):
    if not 경계t:
        return None
    n = len(경계t)
    i = bisect.bisect_right(경계t, x)
    return min(nq - 1, int(i * nq / (n + 1e-12)))


class 모음:
    """한 열쇠(변수 · k · 띠 · 가족 · 집단)의 포함 · PIT · 점수 · 오차 — 기준 해 절반마다."""
    __slots__ = ("n", "in80", "in50", "pit", "위점", "아래점", "해", "abs가", "abs1", "abs3", "n1", "n3", "물러섬", "e가", "e1", "e3")

    def __init__(self, 칸수):
        self.n, self.in80, self.in50 = 0, 0, 0
        self.pit = [0] * 칸수
        # 위 거리 u = (y − 가운데) ÷ (위 끝 − 가운데) · 아래 거리 d = (가운데 − y) ÷ (가운데 − 아래 끝) — 반대쪽이면 음수. 대칭 점수 = max(u, d)(W9)
        self.위점, self.아래점, self.해 = array("f"), array("f"), array("h")
        self.abs가, self.abs1, self.abs3, self.n1, self.n3, self.물러섬 = 0.0, 0.0, 0.0, 0, 0, 0
        self.e가, self.e1, self.e3 = array("f"), array("f"), array("f")      # 절대오차(중앙값용 — 작은 회사의 극단 비율이 평균을 끈다)


def 층1(국가, 설정=None, 표본=None, 씨=20261023, 자리=None, 조용=False):
    """패널 백테스트 → 보정표 dict."""
    import 기저율 as 기                                       # noqa: PLC0415
    import 지속성 as 지속                                     # noqa: PLC0415
    설정 = 설정 or 설정읽기()
    L = 설정["층1"]
    기설 = 기.국가설정(기.설정읽기(), 국가)
    시 = time.time()
    행, 입 = 기.패널읽기(자리, 기설)
    if not 행:
        return None, "%s 패널이 비었다(%s) — `기저율.py --받기 --국가 %s` 를 먼저" % (국가, 입["자리"], 국가)
    남, 뺀 = 기.자료제외(행, 기설)
    넓은 = 기.넓히기(남)
    if 표본 and 0 < 표본 < 1:
        rnd = random.Random(씨)
        넓은 = {c: d for c, d in 넓은.items() if rnd.random() < 표본}
    띠 = L["띠"]
    nq, 최소, 칸수 = L["분위수"], L["최소관측"], L["PIT_칸수"]
    가족들 = L["집단"]
    결과 = {}
    기준해전체 = set()
    for 변 in L["변수"]:
        for k in (변.get("앞날") or L["앞날"]):                 # 변수마다 앞날을 덮을 수 있다(영업이익률 5년 뒤 — 영구기간 영업이익률의 재료 · 2026-10-24 PM)
            관, 경계 = 관측짓기(넓은, 변, k, 기설, L["절단분위"], 지속, 입["자리"])
            if not 관:
                continue
            t별 = collections.defaultdict(list)
            for r in 관:
                t별[r[1]].append(r)
            해들 = sorted(t별)
            풀기 = collections.defaultdict(list)            # (가족, 집단) → 결과
            풀지 = collections.defaultdict(list)            # (가족, 집단, 10분위) → 수준: 변화량 · 성장: 결과
            for T0 in range(해들[0], 해들[-1] + 1):
                for r in t별.get(T0 - k, ()):              # 결과가 T0 에 끝난 쌍 — T0 에 알 수 있었다
                    _, t, x, y, _, _, 규, 산 = r
                    dq = _십분위(경계.get(t), x, nq)
                    v = (y - x) if 변["종류"] == "수준" else y
                    for 가 in 가족들:
                        집 = {"전체": "전체", "규모": 규, "산업2": 산}[가]
                        if 집 is None:
                            continue
                        풀기[(가, 집)].append(y)
                        if dq is not None:
                            풀지[(가, 집, dq)].append(v)
                평가 = t별.get(T0)
                if not 평가 or T0 - k < 해들[0]:
                    continue
                정렬 = {}

                def 표(풀, 열쇠):
                    if 열쇠 not in 정렬:
                        정렬[열쇠] = sorted(풀.get(열쇠) or ())
                    return 정렬[열쇠]
                쓴 = False
                for r in 평가:
                    고, t, x, y, n1, n3, 규, 산 = r
                    dq = _십분위(경계.get(t), x, nq)
                    for 가 in 가족들:
                        집 = {"전체": "전체", "규모": 규, "산업2": 산}[가]
                        if 집 is None:
                            continue
                        for 종류 in ("기저율", "지속성"):
                            if 종류 == "기저율":
                                표본값, 물 = 표(풀기, (가, 집)), False
                                if len(표본값) < 최소:
                                    표본값, 물 = 표(풀기, ("전체", "전체")), True
                                기준점 = 0.0
                            else:
                                if dq is None:
                                    continue
                                표본값, 물 = 표(풀지, (가, 집, dq)), False
                                if len(표본값) < 최소:
                                    표본값, 물 = 표(풀지, ("전체", "전체", dq)), True
                                기준점 = x if 변["종류"] == "수준" else 0.0
                            if len(표본값) < 최소:
                                continue
                            p10, p25, p50, p75, p90 = (기준점 + 분위(표본값, 띠[q]) for q in ("아래", "안아래", "가운데", "안위", "위"))
                            쓴 = True
                            for 열 in ((변["이름"], k, 종류, 가, 집),) if 가 == "전체" else ((변["이름"], k, 종류, 가, 집), (변["이름"], k, 종류, 가, "*")):
                                m = 결과.get(열)
                                if m is None:
                                    m = 결과[열] = 모음(칸수)
                                m.n += 1
                                m.in80 += p10 <= y <= p90
                                m.in50 += p25 <= y <= p75
                                pit = bisect.bisect_right(표본값, y - 기준점) / (len(표본값) + 1.0)
                                m.pit[min(칸수 - 1, int(pit * 칸수))] += 1
                                u, d = 거리둘(y, p10, p50, p90)
                                m.위점.append(u)
                                m.아래점.append(d)
                                m.해.append(T0)
                                m.abs가 += abs(y - p50)
                                m.e가.append(abs(y - p50))
                                if n1 is not None:
                                    m.abs1 += abs(y - n1)
                                    m.e1.append(abs(y - n1))
                                    m.n1 += 1
                                if n3 is not None:
                                    m.abs3 += abs(y - n3)
                                    m.e3.append(abs(y - n3))
                                    m.n3 += 1
                                m.물러섬 += 물
                if 쓴:
                    기준해전체.add(T0)
            if not 조용:
                print("  %s k=%d — 관측 %d · 기준 해 %d~%d (%.0f초)" % (변["이름"], k, len(관), 해들[0], 해들[-1], time.time() - 시), flush=True)
    해목록 = sorted(기준해전체)
    가운데해 = 해목록[len(해목록) // 2] if 해목록 else None
    목표 = L["보정"]["목표포함률"]
    꼬목 = 꼬리목표(목표)
    창 = int(L["보정"].get("최근창") or 5)
    창해 = set(해목록[-창:])
    줄들 = []
    for (이름, k, 종류, 가, 집), m in sorted(결과.items(), key=lambda kv: tuple(str(x) for x in kv[0])):
        if m.n < 최소:
            continue
        점수 = [max(u, d) for u, d in zip(m.위점, m.아래점)]
        앞점 = [s for s, t in zip(점수, m.해) if t < 가운데해]
        뒤점 = [s for s, t in zip(점수, m.해) if t >= 가운데해]
        q앞 = 등각분위(앞점, 목표) if len(앞점) >= 최소 else None
        검 = None
        if q앞 is not None and len(뒤점) >= 최소:
            검 = {"n": len(뒤점), "원포함률": round(sum(s <= 1.0 for s in 뒤점) / len(뒤점), 4),
                 "보정포함률": round(sum(s <= q앞 for s in 뒤점) / len(뒤점), 4) if math.isfinite(q앞) else None}
        q전 = 등각분위(점수, 목표)
        꼬전 = {"아래": _반올림(등각분위(list(m.아래점), 꼬목)), "위": _반올림(등각분위(list(m.위점), 꼬목))}
        창i = [i for i, t in enumerate(m.해) if t in 창해]
        최근 = None
        if len(창i) >= 최소:
            최근 = {"창": [min(창해), max(창해)], "n": len(창i),
                   "대칭": _반올림(등각분위([점수[i] for i in 창i], 목표)),
                   "아래": _반올림(등각분위([m.아래점[i] for i in 창i], 꼬목)), "위": _반올림(등각분위([m.위점[i] for i in 창i], 꼬목))}
        한줄 = {"변수": 이름, "앞날": k, "띠": 종류, "가족": 가, "집단": 집, "n": m.n,
              "포함률80": round(m.in80 / m.n, 4), "포함률50": round(m.in50 / m.n, 4),
              "PIT": [round(c / m.n, 4) for c in m.pit],
              "위꼬리": round(sum(1 for u in m.위점 if u > 1.0) / m.n, 4), "아래꼬리": round(sum(1 for d in m.아래점 if d > 1.0) / m.n, 4),
              "보정계수_앞": _반올림(q앞), "검증": 검, "보정계수_전체": _반올림(q전),
              "보정계수_꼬리": 꼬전, "보정계수_최근": 최근,
              "MAE": {"띠가운데": _나눠(m.abs가, m.n), "직전값": _나눠(m.abs1, m.n1), "직전3년": _나눠(m.abs3, m.n3)},
              "MdAE": {"띠가운데": _중앙(m.e가), "직전값": _중앙(m.e1), "직전3년": _중앙(m.e3)},
              "물러섬": m.물러섬, "물러섬비중": round(m.물러섬 / m.n, 4)}
        if 집 != "*":                                         # 「*」 는 집단 줄을 모은 것 — 정직 평가는 집단 줄마다(다음 회차가 읽는 자리와 같게)
            한줄["정직"], 한줄["정직q"] = 정직평가(m.위점, m.아래점, m.해, k, 목표, 창, 최소)
        줄들.append(한줄)
    패널판 = 패널판계산(입["자리"])
    낸 = {"형식": 형식, "국가": 국가, "만든날": datetime.date.today().isoformat(), "걸린초": round(time.time() - 시, 1),
         "패널": {"자리": 입["자리"], "연도": 입["연도"], "판": 패널판, "회사수": len(넓은), "뺀_회사연도": len(뺀),
                "상세_회사연도": 입.get("상세_회사연도"), "표본": 표본},
         "설정": L, "기준해": 해목록, "가르기": {"보정": [t for t in 해목록 if t < 가운데해], "검증": [t for t in 해목록 if t >= 가운데해]},
         "최근창": {"해": sorted(창해), "길이": 창}, "채택": dict(L["보정"].get("채택") or 기본채택),
         "결과": 줄들}
    낸["정직평가"] = 정직요약(줄들)
    낸["정직판정"] = 정직판정(낸["정직평가"], 낸["채택"], L["보정"].get("받아들임") or 기본받아들임)
    낸["요약"] = 요약(낸)
    return 낸, ""


기본받아들임 = {"포함": [0.77, 0.83], "꼬리": [0.07, 0.13]}      # P1 성공 기준 ② — 채택 방식의 정직 평가(가족 「전체」)


def 정직판정(정직, 채택, 받):
    """(변수 · 앞날 · 띠)마다 채택 방식의 정직 평가가 받아들임 문턱 안인가(2026-10-24 PM) → {"변수|k|띠": {통과 · 포함 · 위 · 아래 · n · 방식}}.
    통과하지 못한 (변수 · k · 띠)는 다음 회차가 보정을 쓰지 않는다(`보정찾기` — 「보정 없음」). 정직 평가가 서지 않은 변수는 이 표에 없다 — 역시 보정 없음."""
    채 = 채택 or 기본채택
    방 = ("꼬리" if 채.get("꼬리별") else "대칭") + ("최근" if 채.get("창") == "최근" else "전체")
    낸 = {}
    for r in 정직 or []:
        if r.get("가족") != "전체" or r.get("변수") == "*":
            continue
        m = (r.get("방식") or {}).get(방)
        if not m:
            continue
        통 = (받["포함"][0] <= m["포함"] <= 받["포함"][1] and 받["꼬리"][0] <= m["위꼬리"] <= 받["꼬리"][1]
             and 받["꼬리"][0] <= m["아래꼬리"] <= 받["꼬리"][1])
        낸["%s|%s|%s" % (r["변수"], r["앞날"], r["띠"])] = {"통과": bool(통), "포함": m["포함"], "위": m["위꼬리"], "아래": m["아래꼬리"], "n": r["n"], "방식": 방}
    return 낸


# ══════════════════════════════════════════════════════════ 보정 방식 — 꼬리별 · 최근 창 · 정직 평가(W9 · 2026-10-24)

방식들 = ("무보정", "대칭전체", "꼬리전체", "대칭최근", "꼬리최근")
기본채택 = {"꼬리별": False, "창": "전체"}                    # 보정표에 「채택」 이 없으면(옛 보정표) — 대칭 · 전체 창(2026-10-23 판과 같다)


def 꼬리목표(목표):
    """두 꼬리를 같게 — 목표 포함률 0.8 이면 꼬리마다 0.1 → 각 꼬리 거리의 0.9 분위."""
    return 1.0 - (1.0 - 목표) / 2.0


def 거리둘(y, p10, p50, p90):
    """(위 거리 u, 아래 거리 d) — u = (y − 가운데) ÷ (위 끝 − 가운데) · d = (가운데 − y) ÷ (가운데 − 아래 끝). 반대쪽이면 음수.
    띠 폭이 0 이면 그쪽 거리는 ±1e6(가운데와 같으면 0). 대칭 점수 max(u, d) 는 2026-10-23 판의 점수와 같다."""
    def 한쪽(차, 폭):
        if 폭 > 0:
            return max(-1e6, min(1e6, 차 / 폭))
        return 0.0 if 차 == 0 else (1e6 if 차 > 0 else -1e6)
    return 한쪽(y - p50, p90 - p50), 한쪽(p50 - y, p50 - p10)


def _q셋(위s, 아래s, 목표):
    """거리 목록 → (대칭 q, 아래 q, 위 q)."""
    꼬 = 꼬리목표(목표)
    return 등각분위([max(u, d) for u, d in zip(위s, 아래s)], 목표), 등각분위(list(아래s), 꼬), 등각분위(list(위s), 꼬)


def 정직평가(위점, 아래점, 해들, k, 목표, 창, 최소):
    """rolling origin — 기준 해 T 의 판을 그 T 에 알 수 있던 보정(결과가 T 까지 끝난 기준 해 T' ≤ T − k)으로 잰다.
    전체 창 = T' ≤ T − k 전부 · 최근 창 = T − k − 창 + 1 ≤ T' ≤ T − k. 두 창 모두 관측이 최소 이상인 해만 센다(방식끼리 같은 판을 맞댄다).
    → (셈 {방식: [n, 안, 위꼬리, 아래꼬리]}, 해별 q {T: {방식: q 또는 [아래, 위]}})."""
    해별 = collections.defaultdict(list)
    for i, t in enumerate(해들):
        해별[t].append(i)
    셈 = {방: [0, 0, 0, 0] for 방 in 방식들}
    qs = {}
    for T in sorted(해별):
        전i = [i for t in 해별 if t <= T - k for i in 해별[t]]
        창i = [i for t in 해별 if T - k - 창 + 1 <= t <= T - k for i in 해별[t]]
        if len(전i) < 최소 or len(창i) < 최소:
            continue
        대전, 아전, 위전 = _q셋([위점[i] for i in 전i], [아래점[i] for i in 전i], 목표)
        대창, 아창, 위창 = _q셋([위점[i] for i in 창i], [아래점[i] for i in 창i], 목표)
        쓸 = {"무보정": (1.0, 1.0), "대칭전체": (대전, 대전), "꼬리전체": (아전, 위전), "대칭최근": (대창, 대창), "꼬리최근": (아창, 위창)}
        qs[str(T)] = {"대칭전체": _반올림(대전), "꼬리전체": [_반올림(아전), _반올림(위전)],
                      "대칭최근": _반올림(대창), "꼬리최근": [_반올림(아창), _반올림(위창)]}
        for i in 해별[T]:
            u, d = 위점[i], 아래점[i]
            for 방, (qa, qw) in 쓸.items():
                c = 셈[방]
                c[0] += 1
                위밖, 아밖 = u > qw, d > qa
                c[1] += not (위밖 or 아밖)
                c[2] += 위밖
                c[3] += 아밖
    return 셈, qs


def 정직요약(줄들):
    """집단 줄(「*」 제외)의 정직 셈을 (가족 · 변수 · 앞날 · 띠) · (가족 · 띠) · 가족별로 모은다 → 방식마다 포함 · 위 꼬리 · 아래 꼬리."""
    모 = collections.defaultdict(lambda: {방: [0, 0, 0, 0] for 방 in 방식들})
    for r in 줄들:
        셈 = r.get("정직")
        if not 셈:
            continue
        for 열쇠 in ((r["가족"], r["변수"], r["앞날"], r["띠"]), (r["가족"], "*", 0, r["띠"]), (r["가족"], "*", 0, "*")):
            for 방 in 방식들:
                a, b = 모[열쇠][방], 셈[방]
                for j in range(4):
                    a[j] += b[j]
    낸 = []
    for (가, 변, k, 띠), m in sorted(모.items(), key=lambda kv: tuple(str(x) for x in kv[0])):
        n = m["무보정"][0]
        if not n:
            continue
        낸.append({"가족": 가, "변수": 변, "앞날": k, "띠": 띠, "n": n,
                   "방식": {방: {"포함": round(c[1] / c[0], 4), "위꼬리": round(c[2] / c[0], 4), "아래꼬리": round(c[3] / c[0], 4)}
                           for 방, c in m.items() if c[0]}})
    return 낸


def _수(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and v > 0 else None


def 고른q(r, 채택=None):
    """보정표 줄 하나 + 채택 방식 → {"아래", "위", "대칭", "방식"} | None. 최근 창(채택이 「최근」 일 때) → 전체 창 차례.
    꼬리별을 골랐는데 꼬리 값이 없으면(옛 보정표) 대칭 q 를 두 끝에 쓴다."""
    채 = 채택 or 기본채택
    꼬, 창 = bool(채.get("꼬리별")), 채.get("창") or "전체"
    후 = []
    if 창 == "최근" and isinstance(r.get("보정계수_최근"), dict):
        c = r["보정계수_최근"]
        후.append(("최근 %s~%s" % tuple(c.get("창") or ("?", "?")), c.get("아래"), c.get("위"), c.get("대칭")))
    c = r.get("보정계수_꼬리") if isinstance(r.get("보정계수_꼬리"), dict) else {}
    후.append(("전체", c.get("아래"), c.get("위"), r.get("보정계수_전체")))
    for 창말, a, w, s in 후:
        if 꼬 and _수(a) and _수(w):
            return {"아래": a, "위": w, "대칭": _수(s) or max(a, w), "방식": "꼬리별 · %s 창" % 창말}
        if not 꼬 and _수(s):
            return {"아래": s, "위": s, "대칭": s, "방식": "대칭 · %s 창" % 창말}
    for 창말, a, w, s in 후:
        if _수(s):
            return {"아래": s, "위": s, "대칭": s, "방식": "대칭 · %s 창(꼬리 값 없음)" % 창말}
    return None


def q글(보정):
    """보정 dict → 「q 1.12」 · 「q 아래 0.95 · 위 1.30」(꼬리별 q 가 다르면)."""
    if not 보정:
        return "보정 없음"
    a, w = 보정.get("아래"), 보정.get("위")
    if isinstance(a, (int, float)) and isinstance(w, (int, float)) and abs(a - w) > 1e-9:
        return "q 아래 %.2f · 위 %.2f" % (a, w)
    s = 보정.get("보정계수")
    s = s if isinstance(s, (int, float)) else a
    return ("q %.2f" % s) if isinstance(s, (int, float)) else "보정 없음"


def _반올림(v):
    if v is None:
        return None
    return round(v, 4) if math.isfinite(v) else "무한"


def _중앙(xs):
    if not xs:
        return None
    v = sorted(xs)
    n = len(v)
    return round((v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2), 5)


def _나눠(a, b):
    return round(a / b, 5) if b else None


def 요약(낸):
    """사람이 읽을 줄 — 가족 「전체」 · 집단 「*」(모든 집단을 합친 것)의 변수 × 띠 × 앞날."""
    줄 = []
    for r in 낸["결과"]:
        if r["가족"] != "전체":
            continue
        검 = r.get("검증") or {}
        줄.append("%s k=%d %s — 80%% 띠 포함률 %.1f%% · 50%% 띠 %.1f%% · 보정계수 %s(검증: 원 %s → 보정 %s) · 중앙 절대오차 띠가운데 %s / 직전값 %s / 직전3년 %s" % (
            r["변수"], r["앞날"], r["띠"], r["포함률80"] * 100, r["포함률50"] * 100, r["보정계수_전체"],
            ("%.1f%%" % (검["원포함률"] * 100)) if 검.get("원포함률") is not None else "—",
            ("%.1f%%" % (검["보정포함률"] * 100)) if 검.get("보정포함률") is not None else "—",
            r["MdAE"]["띠가운데"], r["MdAE"]["직전값"], r["MdAE"]["직전3년"]))
    return 줄


def 집단상위(낸, 가족, 셋=3, 기준="포함률80"):
    """가족(규모 · 산업2)에서 목표(80%)에서 가장 먼 집단 셋 — [(변수, k, 띠, 집단, n, 포함률, 보정계수)]."""
    후 = [r for r in 낸["결과"] if r["가족"] == 가족 and r["집단"] != "*"]
    후.sort(key=lambda r: -abs(r[기준] - 0.80))
    return [(r["변수"], r["앞날"], r["띠"], r["집단"], r["n"], r[기준], r["보정계수_전체"]) for r in 후[:셋]]


def 보정찾기(보정표, 변수, k, 띠="지속성", 집단들=None):
    """다음 회차가 읽는 자리 — 집단 후보(예: [("산업2", "26"), ("규모", "1조~10조"), ("전체", "전체")]) 가운데 먼저 있는 것의 보정계수.
    방식은 보정표의 「채택」(없으면 대칭 · 전체 창 — 옛 보정표)을 따른다(`고른q` — 최근 창 → 전체 창). 없으면 None.
    그 집단 띠가 절반 넘게 「전체」 로 물러서 잰 줄은 그 집단의 띠가 아니라 건너뛴다. 기저율 · 지속성이 「있을 때만」 이 함수로 읽는다.
    → {"보정계수"(대칭 — 표시 · 옛 소비처), "아래", "위"(양 끝에 쓰는 q), "방식", "가족", "집단", "n", "포함률80"}."""
    후 = 집단들 or [("전체", "전체")]
    판 = (보정표 or {}).get("정직판정")
    if isinstance(판, dict) and not (판.get("%s|%s|%s" % (변수, k, 띠)) or {}).get("통과"):
        return None                                        # 정직 평가가 받아들임 문턱 밖이거나 서지 않았다 — 보정 없음(2026-10-24 PM · P1 성공 기준 ②)
    색 = {(r["변수"], r["앞날"], r["띠"], r["가족"], r["집단"]): r for r in (보정표 or {}).get("결과") or []}
    채 = (보정표 or {}).get("채택")
    for 가, 집 in 후:
        r = 색.get((변수, k, 띠, 가, 집))
        if not r or (r.get("물러섬비중") or 0) >= 0.5:
            continue
        q = 고른q(r, 채)
        if q:
            return {"보정계수": q["대칭"], "아래": q["아래"], "위": q["위"], "방식": q["방식"],
                    "가족": 가, "집단": 집, "n": r["n"], "포함률80": r["포함률80"]}
    return None


def 패널판계산(자리):
    """패널 파일 이름 · 크기의 지문(16자) — 보정표의 「패널 판」. 층 1 과 보정표를 읽는 쪽이 같은 함수로 잰다(지금 패널과 같은 판인가)."""
    import 기저율 as 기                                       # noqa: PLC0415
    return hashlib.sha256(json.dumps([[os.path.basename(p), os.path.getsize(p)] for _, p in sorted(기.패널파일들(자리).items())],
                                     ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def 보정표읽기(국가, 패널자리=None, 경로=None):
    """→ (보정표 또는 None, 상태, 글). 상태: 「있음」 · 「없음」(파일이 없다 — 종전대로) · 「낡음」(보정표의 패널 판 ≠ 지금 패널 — 쓰지 않는다) ·
    「깨짐」. 패널자리를 주면 판을 맞댄다(주지 않으면 맞대지 않고 「있음」). 2026-10-23 밤 W8 — 근거 범위 보정을 「있을 때만」 읽는 자리."""
    p = 경로 or os.path.join(공용뿌리(), "사후대조", "보정표_%s.json" % 국가)
    if not os.path.exists(p):
        return None, "없음", "사후대조 보정표가 없다(%s) — 보정하지 않는다(`사후대조.py 패널 --국가 %s`)" % (os.path.basename(p), 국가)
    try:
        표 = json.load(io.open(p, encoding="utf-8"))
    except (OSError, ValueError) as e:
        return None, "깨짐", "사후대조 보정표를 읽지 못했다(%s) — 보정하지 않는다" % type(e).__name__
    if 표.get("형식") != 형식:
        return None, "깨짐", "사후대조 보정표 형식이 다르다(%s) — 보정하지 않는다" % 표.get("형식")
    판 = ((표.get("패널") or {}).get("판"))
    if 패널자리:
        지금판 = 패널판계산(패널자리)
        if 판 != 지금판:
            return None, "낡음", ("사후대조 보정표(패널 판 %s)가 지금 패널(판 %s)과 다르다 — 쓰지 않는다 · `사후대조.py 패널 --국가 %s` 를 다시"
                               % (판, 지금판, 국가))
    return 표, "있음", "사후대조 보정표(패널 판 %s · 만든날 %s)" % (판, 표.get("만든날"))


def 대상집단(대상):
    """대상 dict(KSIC2 · 규모구간) → 보정찾기 · 띠짓기의 집단 차례 [(가족, 집단)] — 산업 2자리 → 규모 → 전체."""
    후 = []
    if 대상.get("KSIC2"):
        후.append(("산업2", "%s" % 대상["KSIC2"]))
    if 대상.get("규모구간"):
        후.append(("규모", 대상["규모구간"]))
    후.append(("전체", "전체"))
    return 후


_관측캐시 = {}
변수하한 = {"매출성장률": -1.0, "자산회전율": 0.0, "매출채권비율": 0.0, "재고비율": 0.0, "CAPEX비율": 0.0, "상각률": 0.0}   # 정의상 그 아래가 없는 변수 — 띠 끝을 자른다


def 띠짓기(넓은, 변수이름, k, 기설, 대상, 설정=None, 값=None, 해=None):
    """회사 한 곳의 「80% 띠」 둘 — 층 1 이 포함률을 잰 것과 같은 정의 · 같은 함수(관측짓기)로 지금 패널 전체에서 세운다.
      기저율 띠  같은 집단의 k년 뒤 값 분포(성장은 k년 CAGR) — 회사의 지금 자리를 보지 않는다
      지속성 띠  같은 집단 · 같은 10분위(기준 해 값)에서 k년 뒤 값 — 수준은 「지금 값 + 변화량 분위」, 성장은 CAGR 분위
    대상 = {"고유번호", "KSIC2", "규모구간"}. 값 · 해 = 기준 값과 그 해(주지 않으면 패널의 대상 마지막 해 값 — 대상이 패널에 없으면 지속성 띠는 서지 않는다).
    집단은 산업 2자리 → 규모 → 전체 차례로, 관측이 최소관측보다 적으면 다음 집단으로 물러선다. 대상 자신의 관측은 뺀다.
    → {"변수", "k", "값", "해", "십분위", "기저율": {가족 · 집단 · n · 아래 · 가운데 · 위} | None, "지속성": {…} | None}."""
    import 지속성 as 지속                                     # noqa: PLC0415
    설정 = 설정 or 설정읽기()
    L = 설정["층1"]
    변 = next((v for v in L["변수"] if v["이름"] == 변수이름), None)
    if 변 is None:
        return None
    if _관측캐시.get("넓은") is not 넓은:                    # 같은 패널 객체 안에서만 관측을 다시 쓴다(변수 · k 마다 한 번)
        _관측캐시.clear()
        _관측캐시["넓은"] = 넓은
    열쇠 = (변수이름, k)
    if 열쇠 not in _관측캐시:
        _관측캐시[열쇠] = 관측짓기(넓은, 변, k, 기설, L["절단분위"], 지속)
    관, 경계 = _관측캐시[열쇠]
    고 = 대상.get("고유번호")
    if 값 is None and 고 and 고 in 넓은:
        계 = 지속.변수계열({고: 넓은[고]}, 변수이름 if 변["종류"] != "성장" else "매출성장률").get(고) or {}
        if 계:
            해 = max(계)
            값 = 계[해]
    nq, 최소 = L["분위수"], L["최소관측"]
    띠 = L["띠"]
    dq = None
    if 값 is not None and 경계:
        t경 = 해 if (해 in 경계) else max([t for t in 경계 if 해 is None or t <= 해] or [max(경계)])
        dq = _십분위(경계.get(t경), 값, nq)
    낸 = {"변수": 변수이름, "k": k, "값": 값, "해": 해, "십분위": dq, "기저율": None, "지속성": None}
    for 종류 in ("기저율", "지속성"):
        if 종류 == "지속성" and dq is None:
            continue
        for 가, 집 in 대상집단(대상):
            표본 = []
            for r in 관:
                if r[0] == 고:
                    continue
                if 가 == "규모" and r[6] != 집:
                    continue
                if 가 == "산업2" and ("%s" % r[7]) != 집:
                    continue
                if 종류 == "기저율":
                    표본.append(r[3])
                else:
                    t경r = r[1]
                    if _십분위(경계.get(t경r), r[2], nq) != dq:
                        continue
                    표본.append((r[3] - r[2]) if 변["종류"] == "수준" else r[3])
            if len(표본) < 최소:
                continue
            표본.sort()
            기준점 = (값 if (종류 == "지속성" and 변["종류"] == "수준") else 0.0)
            하 = 변수하한.get(변수이름)
            아, 가운, 위 = (기준점 + 분위(표본, 띠[q]) for q in ("아래", "가운데", "위"))
            if 하 is not None:
                아, 가운, 위 = max(아, 하), max(가운, 하), max(위, 하)
            낸[종류] = {"가족": 가, "집단": 집, "n": len(표본), "아래": 아, "가운데": 가운, "위": 위}
            break
    return 낸


def 보정적용(띠하나, q, 하한=None):
    """가운데는 두고 양 끝만 옮긴다 — 아래 끝 = 가운데 − q아래 × (가운데 − 아래 끝) · 위 끝 = 가운데 + q위 × (위 끝 − 가운데) → (아래, 위).
    q 는 수 하나(대칭) · (아래, 위) · 보정찾기 결과 dict({"아래", "위"} — 없으면 「보정계수」) 가운데 하나(W9 — 꼬리별).
    하한(정의상 그 아래가 없는 변수 — `변수하한`)이 있으면 아래 끝을 자른다."""
    if isinstance(q, dict):
        qa, qw = q.get("아래", q.get("보정계수")), q.get("위", q.get("보정계수"))
    elif isinstance(q, (tuple, list)):
        qa, qw = q[0], q[1]
    else:
        qa = qw = q
    m = 띠하나["가운데"]
    아 = m - qa * (m - 띠하나["아래"])
    if 하한 is not None:
        아 = max(아, 하한)
    return (아, m + qw * (띠하나["위"] - m))


def 보정띠(띠결과, 보정표, 대상):
    """띠짓기 결과 + 보정표 → 종류마다 {보정전: [아래, 위], 가운데, 보정뒤: [아래, 위] | None, 보정: {보정계수 · 가족 · 집단 · n · 포함률80} | None}.
    보정표가 없거나 그 변수 · k · 띠 · 집단의 줄이 없으면(물러섬비중 ≥ 0.5 줄은 건너뛴다 — 보정찾기) 보정뒤 = None(보정 전 띠만)."""
    낸 = {}
    for 종류 in ("기저율", "지속성"):
        b = (띠결과 or {}).get(종류)
        if not b:
            continue
        후 = 대상집단(대상)                                     # 띠를 세운 집단부터(더 좁은 집단의 q 를 넓은 집단 띠에 쓰지 않는다) → 그보다 넓은 집단
        i = next((j for j, (가, 집) in enumerate(후) if 가 == b["가족"] and 집 == b["집단"]), 0)
        r = 보정찾기(보정표, 띠결과["변수"], 띠결과["k"], 종류, 후[i:]) if 보정표 else None
        한 = {"띠집단": "%s %s" % (b["가족"], b["집단"]), "n": b["n"], "보정전": [b["아래"], b["위"]], "가운데": b["가운데"], "보정뒤": None, "보정": r}
        if r and _수(r.get("아래")) and _수(r.get("위")):
            한["보정뒤"] = list(보정적용(b, r, 변수하한.get(띠결과["변수"])))
        낸[종류] = 한
    return 낸


# ══════════════════════════════════════════════════════════ 층 2 — 회차 대조

def _날(s):
    return datetime.date.fromisoformat(s) if isinstance(s, str) and len(s) >= 10 else None


def _값(R, 시트, 줄, 열):
    v = ((R.get(시트) or {}).get(줄) or {})
    v = v.get(열) if isinstance(v, dict) else None
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def 기간맞대기(속0, 속1):
    """지난 회차 예측 열 → [(예측 열, 맞댄 방식, 새 실적 열, 빼는 지난 누계 열)]. 방식: 같은기간 · 회계연도차감(흐름만)."""
    실1 = {c: a for c, a in 속1.items() if a.get("구분") == "실적"}
    낸 = []
    for c, a in 속0.items():
        if a.get("구분") != "예측" or not a.get("시작일"):
            continue
        같 = [c1 for c1, b in 실1.items() if b.get("시작일") == a["시작일"] and b.get("종료일") == a["종료일"]]
        if 같:
            낸.append((c, "같은기간", 같[0], None))
            continue
        끝같 = [c1 for c1, b in 실1.items() if b.get("종료일") == a["종료일"] and b.get("회계연도") == a.get("회계연도")]
        누 = [c0 for c0, b in 속0.items() if b.get("구분") == "실적" and b.get("회계연도") == a.get("회계연도")
             and _날(b.get("종료일")) and _날(a.get("시작일")) and _날(b["종료일"]) + datetime.timedelta(days=1) == _날(a["시작일"])]
        if 끝같 and 누:
            낸.append((c, "회계연도차감", 끝같[0], 누[0]))
        elif 끝같:
            낸.append((c, "잔액만", 끝같[0], None))
    return 낸


def 상류(그래프, 시작, 깊이=4):
    """동인 그래프에서 시작 노드의 상류 노드 · 손잡이(가정 번호) — 깊이까지."""
    if not 그래프:
        return [], []
    노 = {n["id"]: n for n in 그래프.get("노드") or []}
    if 시작 not in 노:
        return [], []
    엣 = 그래프.get("엣지") or []
    본, 손, 앞 = [시작], [], [시작]
    for _ in range(깊이):
        새 = []
        for e in 엣:
            if any(h in 앞 for h in e.get("하류") or []):
                for u in e.get("상류") or []:
                    if u not in 본:
                        본.append(u)
                        새.append(u)
                for h in e.get("손잡이") or []:
                    if h not in 손:
                        손.append(h)
        앞 = 새
        if not 앞:
            break
    return 본[1:], 손


def 판단칸(가정):
    """근거 칸에 「[판단]」 이 있는 가정 번호 — 사람(또는 본선)이 근거를 달아 정한 칸."""
    낸 = set()
    for 번, v in (가정.get("근거") or {}).items():
        글 = " ".join(x for x in (v if isinstance(v, list) else [v]) if isinstance(x, str))
        if "[판단]" in 글:
            낸.add("%s" % 번)
    return 낸


def 층2(지난경로, 새경로, 설정=None, 그래프경로=None, 시나리오="기준"):
    설정 = 설정 or 설정읽기()
    T = 설정["층2"]
    from 엔진 import 계산                                     # noqa: PLC0415
    가0 = json.load(io.open(지난경로, encoding="utf-8"))
    가1 = json.load(io.open(새경로, encoding="utf-8"))
    R0, R1 = 계산(가0, 시나리오), 계산(가1, "기준")
    속0, 속1 = R0["기간"]["속성"], R1["기간"]["속성"]
    짝 = 기간맞대기(속0, 속1)
    그래프 = json.load(io.open(그래프경로, encoding="utf-8")) if 그래프경로 and os.path.exists(그래프경로) else None
    판 = 판단칸(가0)
    줄들 = []
    for c, 방식, c1, 누 in 짝:
        한 = {"예측열": c, "실적열": c1, "방식": 방식, "줄": {}, "비율": {}}
        for 줄 in T["줄"]:
            예 = _값(R0, 줄["시트"], 줄["줄"], c)
            실 = _값(R1, 줄["시트"], 줄["줄"], c1)
            if 방식 == "회계연도차감" and 줄["꼴"] == "흐름":
                누값 = _값(R0, 줄["시트"], 줄["줄"], 누)
                실 = (실 - 누값) if (실 is not None and 누값 is not None) else None
            elif 방식 == "잔액만" and 줄["꼴"] != "잔액":
                실 = None
            오 = (예 - 실) if (예 is not None and 실 is not None) else None
            율 = (오 / abs(실)) if (오 is not None and 실) else None
            한["줄"][줄["이름"]] = {"예측": 예, "실적": 실, "오차": 오, "오차율": 율}
        for b in T["비율"]:
            v = []
            for 쪽 in ("예측", "실적"):
                a, d = 한["줄"].get(b["분자"], {}).get(쪽), 한["줄"].get(b["분모"], {}).get(쪽)
                v.append((a / d) if (a is not None and d) else None)
            한["비율"][b["이름"]] = {"예측": v[0], "실적": v[1], "차_p": (v[0] - v[1]) if None not in v else None}
        짚 = []
        for 줄 in T["줄"]:
            x = 한["줄"][줄["이름"]]
            if x["오차율"] is not None and abs(x["오차율"]) > T["큰오차_문턱"]:
                노드, 손 = 상류(그래프, "%s:%s" % (줄["시트"], 줄["줄"]))
                짚.append({"줄": 줄["이름"], "오차율": x["오차율"], "상류노드": 노드[:12], "손잡이": 손,
                          "판단칸": sorted(h for h in 손 if re.sub(r"\D", "", "%s" % h) in 판)})
        한["짚기"] = 짚
        줄들.append(한)
    return {"형식": "사후대조 회차 1", "만든날": datetime.date.today().isoformat(), "지난": os.path.abspath(지난경로), "새": os.path.abspath(새경로),
            "지난기준일": (가0.get("메타") or {}).get("평가기준일"), "새기준일": (가1.get("메타") or {}).get("평가기준일"),
            "시나리오": 시나리오, "그래프": bool(그래프), "판단칸수": len(판), "맞댄기간": 줄들}


# ══════════════════════════════════════════════════════════ 실행

def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="사후대조 — 근거 범위의 포함률(패널)과 지난 회차 예측의 오차(회차)")
    sp = ap.add_subparsers(dest="명령")
    p = sp.add_parser("패널", allow_abbrev=False)
    p.add_argument("--국가", required=True, choices=["KR", "US"])
    p.add_argument("--표본", type=float, help="회사 표본 비율(0~1) — 시간이 길 때")
    p.add_argument("--출력", help="기본 <공용>/사후대조/보정표_<국가>.json")
    p.add_argument("--md")
    p.add_argument("--설정")
    p = sp.add_parser("회차", allow_abbrev=False)
    p.add_argument("--지난", required=True)
    p.add_argument("--새", required=True)
    p.add_argument("--그래프")
    p.add_argument("--시나리오", default="기준")
    p.add_argument("--출력")
    p.add_argument("--설정")
    a = ap.parse_args(argv)
    if a.명령 == "패널":
        try:
            설정 = 설정읽기(a.설정)
        except (OSError, ValueError) as e:
            print("입력 오류 — 설정(%s)" % e)
            return 입력오류
        낸, 까 = 층1(a.국가, 설정, a.표본)
        if not 낸:
            print("발견 — %s" % 까)
            return 발견
        출 = a.출력 or os.path.join(공용뿌리(), "사후대조", "보정표_%s.json" % a.국가)
        os.makedirs(os.path.dirname(os.path.abspath(출)), exist_ok=True)
        임시 = 출 + ".쓰는중"                                   # 다른 회차가 읽는 중일 수 있다 — 다 쓴 뒤 바꿔 끼운다
        with io.open(임시, "w", encoding="utf-8") as f:
            json.dump(낸, f, ensure_ascii=False, indent=1)
        os.replace(임시, 출)
        for 줄 in 낸["요약"]:
            print(줄)
        print("정직 평가(rolling origin — 기준 해 T 를 T − k 까지의 보정으로) · 채택 %s" % 낸["채택"])
        for r in 낸["정직평가"]:
            if r["변수"] != "*":
                continue
            print("  %s · 띠 %s · n %d — %s" % (r["가족"], r["띠"], r["n"], " / ".join(
                "%s 포함 %.1f%%(위 %.1f · 아래 %.1f)" % (방, v["포함"] * 100, v["위꼬리"] * 100, v["아래꼬리"] * 100) for 방, v in r["방식"].items())))
        for 가 in ("규모", "산업2"):
            for x in 집단상위(낸, 가):
                print("  목표에서 먼 %s 집단 — %s k=%d %s · %s · n %d · 포함률 %.1f%% · 보정계수 %s" % (가, x[0], x[1], x[2], x[3], x[4], x[5] * 100, x[6]))
        if a.md:
            with io.open(a.md, "w", encoding="utf-8") as f:
                f.write("# 사후대조 층 1 — %s (%s · %s초)\n\n" % (a.국가, 낸["만든날"], 낸["걸린초"]))
                f.write("\n".join("- " + x for x in 낸["요약"]) + "\n")
        print("→ %s (%d줄 · %.0f초)" % (출, len(낸["결과"]), 낸["걸린초"]))
        return 통과
    if a.명령 == "회차":
        try:
            낸 = 층2(a.지난, a.새, 설정읽기(a.설정), a.그래프, a.시나리오)
        except (OSError, ValueError, KeyError) as e:
            print("입력 오류 — %s: %s" % (type(e).__name__, e))
            return 입력오류
        if a.출력:
            with io.open(a.출력, "w", encoding="utf-8") as f:
                json.dump(낸, f, ensure_ascii=False, indent=1)
        if not 낸["맞댄기간"]:
            print("발견 — 맞댈 기간이 없다(지난 %s · 새 %s — 새 회차의 실적 열이 지난 회차의 예측 기간을 덮지 않는다)" % (낸["지난기준일"], 낸["새기준일"]))
            return 발견
        for x in 낸["맞댄기간"]:
            print("%s ↔ %s(%s)" % (x["예측열"], x["실적열"], x["방식"]))
            for 이름, v in x["줄"].items():
                if v["오차율"] is not None:
                    print("  %-8s 예측 %s · 실적 %s · 오차율 %+.1f%%" % (이름, _수글(v["예측"]), _수글(v["실적"]), v["오차율"] * 100))
            for s in x["짚기"]:
                print("  ↳ %s 상류 손잡이 %s%s" % (s["줄"], " · ".join(s["손잡이"][:8]) or "(그래프 없음)",
                                              (" · 판단칸 %s" % " · ".join(s["판단칸"])) if s["판단칸"] else ""))
        return 통과
    ap.print_help()
    return 입력오류


def _수글(v):
    return "—" if v is None else "{:,.0f}".format(v)


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""개체연결 — 표기가 다른 같은 실물(라인 · 프로젝트 · 능력 단위 · 기집행)을 이름 유사도 + 속성 제약으로 짝짓는다 (기법 5 · 2026-10-21).

    python 스크립트/개체연결.py 가정.json                 # → 가정 곁 _raw/개체연결.json · 표를 찍는다
    python 스크립트/개체연결.py 가정.json --낼 경로.json --설정 수축연결설정.json

무엇 — 연결 검사 ㊷(능력–투자 값 짝, R-156)는 라인(`구조.매출구분[].라인`)과 F 투자능력(`_raw/투자능력.json`)의 `단위능력당투자비[]` ·
       `값짝[]` 을 **`라인` 번호나 이름이 글자 그대로 같을 때만** 짝짓고, 가정 프로젝트는 `구조.투자.프로젝트[].라인` 이 적혀 있어야 라인에 묶는다.
       표기가 조금만 달라도(「K2」 · 「K2(확장동)」 · 「K2 공장」) 짝을 못 찾아 목록으로 흘리거나 「능력이 늘어나는데 프로젝트 CAPEX 가 없다」
       경보가 운다. 이 도구는 그 자리의 **짝 후보**를 낸다.
         이름  문자 2 · 3-gram 코사인 — 흔한 꼬리 낱말(라인 · 팹 · 공장 · 설비 …, 설정)을 뺀 핵심 이름 × 핵심가중 + 전체 이름 × (1 − 핵심가중).
               괄호 안 · 밖을 따로 떼어 본 변형 가운데 가장 높은 값(「K2(확장동)」 ↔ 「K2」)
         속성  연도(프로젝트 투자 해 ↔ 라인 능력이 처음 느는 해 — ㊷ ③ 의 창 [첫 투자, 마지막 투자 + 리드타임 + 2] · F 프로젝트는 착공 · 완공 · 금액 해 ↔
               가정 프로젝트 투자 해의 겹침) · 금액 자릿수(1 − |log10 비| ÷ 2) · 통화(둘 다 있고 다르면 짝 금지) · 위치 낱말(설정 — 키트 기본은 비움)
         점수  이름 × 0.6 + 속성 × 0.4(있는 속성만으로 다시 나눔) — 가중은 설정. 이름이 한 글자도 안 겹치면 0, 있는 속성 하나가 0(연도가 창에서
               세 해 넘게 · 금액이 두 자릿수 넘게 어긋남)이면 짝 금지(설정 `속성0거부`)
       짝 — 한 대 하나인 집합은 **헝가리안 최대 가중 매칭**(직사각 행렬은 0 점 더미로 채운다):
              F 능력단위 ↔ 라인(엔진자리가 가리키면 그것이 먼저) · F 프로젝트 ↔ 가정 프로젝트(헝가리안 뒤 남은 가정 프로젝트는 같은 F 프로젝트를 나눠 가진
              분할 짝 — 「건물」 · 「장비」로 쪼갠 회차 — 을 행마다 최고로 다시 본다)
            여럿이 한 곳으로 가는 집합은 행마다 가장 높은 점수: 가정 프로젝트 → 라인 · F 단위능력당투자비 · 값짝 → 라인 · F 기집행 → 라인.
            문턱(설정) 밑은 짝 없음
       두 단계 — ① 라인에 별칭(F 능력단위 짝 · F 프로젝트의 `능력단위` 이름)을 붙이고 ② 그 별칭으로 프로젝트 · 단위투자비 · 값짝 · 기집행을 잇는다.
       기집행은 F 프로젝트 → 가정 프로젝트 짝이 서면 그 프로젝트의 라인으로 간다(라인 ↔ 프로젝트 ↔ 기집행).
왜 — ㊷ 는 「투자가 능력을 사고 능력이 매출을 낸다」를 줄로 따로 적고 검사로 짝을 본다. 짝을 글자 일치로만 찾으면 표기 차이가 경보가 되고 사람이
     `라인` 칸을 손으로 채운다. **값을 쓰지 않는다** — `대응제안` · `제안` 은 ㊷ 가 읽는 자리(`라인` 칸 · 표 1600 + j)에 옮길 후보이고, 옮기는 것은 본선이다.
사용 — 본선이 F 투자능력 뒤 · 자체검사 앞에 돌린다. `개체연결읽기(가정경로)` 로 다른 도구가 읽는다.
읽는 것 — 가정(`구조.매출구분[].라인` · `구조.투자.프로젝트[]` · 가정 668 + 2j(평균 능력) · 669 + 2j(기말 능력 — 평가기준일 열) · 860 + p(기준 시나리오) ·
           표 1600 + j) · 가정 곁 `_raw/투자능력.json`(`능력단위[]` · `프로젝트[]` · `기집행[]` · `단위능력당투자비[]` · `값짝[]`) — `정상화.파일찾기` 차례
내는 것 — `_raw/개체연결.json`: 형식 · 만든날 · 설정 · 입력 · 폴백 · 라인 · 짝[{라인, 프로젝트, 기집행, 점수, 이름점수, 속성점수, 근거, 종류, 왼쪽, 오른쪽,
           원본: {파일, 칸, 번호}}](원본 = 짝의 왼쪽이 어느 파일 · 어느 칸 · 몇 번째인가 — ㊷ 가 기계로 찾는 자리) ·
           짝없음 · 구분대응 · 대응제안 · 제안 · 신호
           신호 종류: 「이름이 달라 짝을 못 찾던 라인 — 후보 있음」(참고) · 「점수 문턱 밑 — 사람이 대응을 적는다」(경보) ·
           「적힌 라인과 이름 짝이 다르다」(참고) · 「F 성장 프로젝트에 가정 짝이 없다」(참고) · 「재료 없음」(참고)
폴백 — 라인도 프로젝트도 없으면 「재료 없음」 — 기존 규칙(㊷ 의 글자 일치 · `라인` 칸)을 그대로 쓴다. 투자능력.json 이 없으면 가정 프로젝트 → 라인만 본다.
종료 코드 — 0 경보 없음 · 1 경보 있음 · 2 입력 오류(가정 없음 · JSON 파손 · 설정 없음).
회사 · 업종 이름으로 가르는 분기가 없다(범용 — 위치 낱말은 회차가 설정으로 덧붙인다).
"""
from __future__ import annotations

import argparse
import datetime
import io
import itertools
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
출처이름 = "개체연결"


def 설정읽기(p=None):
    return json.load(io.open(p or 설정파일, encoding="utf-8"))


def _수(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


# ─────────────────────────────────────────────── 이름 유사도

def 정규화(이름):
    s = ("%s" % (이름 or "")).lower()
    return re.sub(r"[\s\(\)\[\]\{\}「」『』<>·,./\\_\-–—:;'\"&+]+", "", s)


def 변형(이름):
    """이름 · 괄호 밖 · 괄호 안 — 「K2(확장동)」 → [원래, 「K2」, 「확장동」]."""
    s = "%s" % (이름 or "")
    낸 = [s]
    밖 = re.sub(r"[\(\[（][^\)\]）]*[\)\]）]", " ", s).strip()
    if 밖 and 밖 != s:
        낸.append(밖)
    for 안 in re.findall(r"[\(\[（]([^\)\]）]+)[\)\]）]", s):
        if 안.strip():
            낸.append(안.strip())
    return 낸


def 핵심(이름, 꼬리):
    s = 정규화(이름)
    for t in sorted((정규화(x) for x in 꼬리), key=len, reverse=True):
        if t:
            s = s.replace(t, "")
    return s


def 그램(s, ns):
    낸 = {}
    for n in ns:
        if len(s) < n:
            if s and n == ns[0]:
                낸[s] = 낸.get(s, 0) + 1          # 가장 짧은 n 보다 짧은 이름은 그 글자 통째로
            continue
        for i in range(len(s) - n + 1):
            g = s[i:i + n]
            낸[g] = 낸.get(g, 0) + 1
    return 낸


def 코사인(a, b):
    if not a or not b:
        return 0.0
    dot = sum(v * b.get(k, 0) for k, v in a.items())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def _한쌍(x, y, E):
    if 정규화(x) == 정규화(y):
        return 1.0
    ns = E["ngram"]
    cx, cy = 핵심(x, E["꼬리낱말"]), 핵심(y, E["꼬리낱말"])
    전 = 코사인(그램(정규화(x), ns), 그램(정규화(y), ns))
    if cx and cy and cx == cy:
        핵 = 1.0                                          # 꼬리 낱말만 다르다(「K2」 ↔ 「K2 공장」)
    else:
        핵 = 코사인(그램(cx, ns), 그램(cy, ns)) if (cx and cy) else 전
    v = E["핵심가중"] * 핵 + (1 - E["핵심가중"]) * 전
    for 위 in E.get("위치낱말") or []:
        w = 정규화(위)
        if w and w in 정규화(x) and w in 정규화(y):
            v = min(1.0, v + E.get("위치가산", 0.2))
    return v


def 이름점수(a, b, E):
    """a · b 는 이름 목록(별칭 포함) — 변형까지 펼친 짝 가운데 가장 높은 점수."""
    최 = 0.0
    for x in a:
        for y in b:
            if not x or not y:
                continue
            for xv in 변형(x):
                for yv in 변형(y):
                    if 정규화(xv) and 정규화(yv):
                        최 = max(최, _한쌍(xv, yv, E))
                        if 최 >= 1.0:
                            return 1.0
    return 최


# ─────────────────────────────────────────────── 속성

def _연(c):
    s = "%s" % c
    m = re.search(r"((?:19|20)\d{2})", s)
    if m:
        return int(m.group(1))
    m = re.match(r"[12]H(\d{2})", s)
    return 2000 + int(m.group(1)) if m else None


def _순(c):
    """열 차례 — 1H26 · 2H26 · FY2027 …"""
    s = "%s" % c
    y = _연(s)
    반 = 1 if s.startswith("1H") else 2
    return (y or 9999, 반, s)


def 연도점수(투자해, 능력해, 리드, 여유):
    """프로젝트 투자 해 [a, b] 와 라인 능력이 처음 느는 해 c — c 가 [a, b + 리드 + 여유] 안이면 1, 밖이면 한 해마다 1/3 씩(㊷ ③ 과 같은 창)."""
    if not 투자해 or 능력해 is None:
        return None
    a, b = min(투자해), max(투자해) + (리드 or 0) + 여유
    if a <= 능력해 <= b:
        return 1.0
    거 = (a - 능력해) if 능력해 < a else (능력해 - b)
    return max(0.0, 1.0 - 거 / 3.0)


def 구간점수(해1, 해2):
    """두 해 집합이 겹치면 1, 떨어지면 한 해마다 1/3 씩."""
    if not 해1 or not 해2:
        return None
    a1, b1, a2, b2 = min(해1), max(해1), min(해2), max(해2)
    if a1 <= b2 and a2 <= b1:
        return 1.0
    거 = (a2 - b1) if a2 > b1 else (a1 - b2)
    return max(0.0, 1.0 - 거 / 3.0)


def 금액점수(a, b, 자릿수):
    if not (_수(a) and _수(b)) or a <= 0 or b <= 0:
        return None
    return max(0.0, 1.0 - abs(math.log10(a / b)) / 자릿수)


def 합점수(이름, 속성들, 가중, 거부=True):
    """속성들 = {"연도": 점수 또는 None, "금액": …} → (점수, 속성점수 또는 None). 통화 금지는 부르는 쪽이 0 을 준다.
    이름이 한 글자도 안 겹치면(0) 속성만으로 짝짓지 않는다(0 점). 거부(설정 `속성0거부`)면 있는 속성 하나라도 0 — 연도가 창에서 세 해 넘게
    떨어졌거나 금액이 자릿수 문턱만큼 다르다 — 이면 짝 금지(0 점)."""
    있 = {k: v for k, v in 속성들.items() if v is not None and k in 가중}
    if 이름 < 1e-9:
        return 0.0, (sum(가중[k] * v for k, v in 있.items()) / sum(가중[k] for k in 있)) if 있 else None
    if not 있:
        return 이름, None
    w = sum(가중[k] for k in 있)
    속 = sum(가중[k] * v for k, v in 있.items()) / w
    if 거부 and any(v <= 0 for v in 있.values()):
        return 0.0, 속
    wn = 가중["이름"]
    return wn * 이름 + (1 - wn) * 속, 속


# ─────────────────────────────────────────────── 헝가리안

def 헝가리안(점수):
    """최대 가중 매칭 — 점수[i][j](행 n × 열 m, 0 이상). 직사각은 0 점 더미로 채워 N × N 으로 푼다 → [(i, j)](더미 짝은 뺀다).
    Kuhn–Munkres(잠재값 u · v · O(N³)) — 비용 = 최대점 − 점수의 최소화."""
    n = len(점수)
    m = len(점수[0]) if n else 0
    if n == 0 or m == 0:
        return []
    N = max(n, m)
    큰 = max(max(r) for r in 점수)
    C = [[(큰 - (점수[i][j] if (i < n and j < m) else 0.0)) for j in range(N)] for i in range(N)]
    INF = float("inf")
    u, v = [0.0] * (N + 1), [0.0] * (N + 1)
    p, way = [0] * (N + 1), [0] * (N + 1)
    for i in range(1, N + 1):
        p[0] = i
        j0 = 0
        minv = [INF] * (N + 1)
        used = [False] * (N + 1)
        while True:
            used[j0] = True
            i0, delta, j1 = p[j0], INF, 0
            for j in range(1, N + 1):
                if not used[j]:
                    cur = C[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j], way[j] = cur, j0
                    if minv[j] < delta:
                        delta, j1 = minv[j], j
            for j in range(N + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break
    짝 = []
    for j in range(1, N + 1):
        i = p[j]
        if i and i - 1 < n and j - 1 < m:
            짝.append((i - 1, j - 1))
    return sorted(짝)


def 무차별(점수):
    """시험용 — 모든 배치를 견줘 최대 합을 낸다(더미 짝은 0 점) → (합, 짝)."""
    n, m = len(점수), len(점수[0])
    최, 짝 = -1.0, None
    if n <= m:
        for perm in itertools.permutations(range(m), n):
            s = sum(점수[i][perm[i]] for i in range(n))
            if s > 최 + 1e-12:
                최, 짝 = s, [(i, perm[i]) for i in range(n)]
    else:
        for perm in itertools.permutations(range(n), m):
            s = sum(점수[perm[j]][j] for j in range(m))
            if s > 최 + 1e-12:
                최, 짝 = s, sorted((perm[j], j) for j in range(m))
    return 최, 짝


# ─────────────────────────────────────────────── 재료

def _열값(가정, 번호, 시="기준"):
    v = (가정.get("가정") or {}).get(str(번호))
    if not isinstance(v, dict):
        return {}
    if isinstance(v.get(시), dict):
        v = v[시]
    elif any(isinstance(x, dict) for x in v.values()):
        return {}
    return {k: x for k, x in v.items() if _수(x) and _연(k)}


def 라인들(가정):
    """[{번호, 이름, 구분, 판매량산정, 능력해, 별칭: []}] — 능력해 = 기준 시나리오에서 평균 능력(668 + 2j)이 기준일 기말 능력(669 + 2j 의
    평가기준일 열 — 668 + 2j 에 없는 열)을 처음 넘는 열의 해(㊷ 의 증열과 같다)."""
    낸 = []
    for g in ((가정.get("구조") or {}).get("매출구분") or []):
        if not isinstance(g, dict):
            continue
        for L in g.get("라인") or []:
            if not isinstance(L, dict) or not L.get("번호"):
                continue
            j = int(L["번호"])
            cap, 기말 = _열값(가정, 668 + 2 * j), _열값(가정, 669 + 2 * j)
            순 = sorted(cap, key=_순)
            기준일열 = sorted((k for k in 기말 if k not in cap), key=_순)
            시작 = 기말[기준일열[-1]] if 기준일열 else (cap[순[0]] if 순 else None)
            처음 = next((_연(k) for k in 순 if 시작 is not None and cap[k] > 시작 * (1 + 1e-6) + 1e-9), None)
            낸.append({"번호": j, "이름": L.get("이름") or "라인 %d" % j, "구분": g.get("번호"), "판매량산정": g.get("판매량산정"),
                       "능력해": 처음, "별칭": []})
    return 낸


def 프로젝트들(가정):
    낸 = []
    for x in (((가정.get("구조") or {}).get("투자") or {}).get("프로젝트") or []):
        if not isinstance(x, dict) or not x.get("번호"):
            continue
        p = int(x["번호"])
        v = _열값(가정, 860 + p)
        해 = sorted({_연(k) for k, z in v.items() if z > 0})
        총 = sum(z for z in v.values() if z > 0)
        낸.append({"번호": p, "이름": x.get("이름") or "프로젝트 %d" % p, "라인": (x.get("라인") or 0) or None,
                   "구분": (x.get("구분") or 0) or None, "리드타임": int(x.get("리드타임") or 0), "투자해": 해,
                   "총액": 총 or None, "통화": x.get("통화")})
    return 낸


def _F해(x):
    해 = set()
    for k in ("착공", "완공", "기간"):
        for m in re.findall(r"((?:19|20)\d{2})", "%s" % (x.get(k) or "")):
            해.add(int(m))
    for k, v in (x.get("금액") or {}).items():
        y = _연(k)
        if y and _수(v) and v > 0:
            해.add(y)
    return sorted(해)


def _F총액(x):
    if _수(x.get("총액")) and x["총액"] > 0:
        return x["총액"]
    s = sum(v for v in (x.get("금액") or {}).values() if _수(v) and v > 0)
    return s or None


def _엔진자리라인(글):
    m = re.search(r"라인\[(\d+)\]", "%s" % (글 or ""))
    return int(m.group(1)) if m else None


# ─────────────────────────────────────────────── 돌기

def 돌기(가정, 가정경로, 설정):
    E = 설정["개체연결"]
    문턱 = E["문턱"]
    투, 투곳 = 정상화.파일찾기("투자능력.json", 가정경로)
    투 = 투 if isinstance(투, dict) else {}
    L = 라인들(가정)
    P = 프로젝트들(가정)
    표 = 가정.get("표") or {}
    결과 = {"형식": "개체연결 1", "만든날": datetime.date.today().isoformat(),
          "설정": {k: E[k] for k in ("ngram", "핵심가중", "가중", "연도여유", "금액자릿수", "문턱")},
          "입력": {"가정": os.path.abspath(가정경로) if 가정경로 else None, "투자능력": 투곳,
                 "라인수": len(L), "프로젝트수": len(P)},
          "폴백": None, "라인": [], "짝": [], "짝없음": [], "구분대응": [], "대응제안": [], "제안": [], "신호": []}
    신호 = 결과["신호"]

    def 알림(종류, 대상, 값, 문턱_, 글, 등급):
        신호.append({"출처": 출처이름, "종류": 종류, "대상": 대상, "값": 값, "문턱": 문턱_, "글": 글, "등급": 등급})

    if not L and not P:
        결과["폴백"] = ("재료 없음 — 라인(구조.매출구분[].라인)도 프로젝트(구조.투자.프로젝트[])도 없다. 기존 규칙(㊷ 의 글자 일치 · `라인` 칸)을 그대로 쓴다"
                     "(능력 구분이 없으면 ㊷ 는 「해당 없음」)")
        알림("재료 없음", "전체", None, None, 결과["폴백"], "참고")
        return 결과
    if not 투곳:
        결과["폴백"] = "투자능력.json 없음 — F 쪽(능력단위 · 단위투자비 · 값짝 · 기집행) 짝은 건너뛰고 가정 프로젝트 → 라인만 본다(나머지는 기존 규칙 그대로)"
    번호로 = {x["번호"]: x for x in L}

    def 짝적기(종류, 왼, 오, 점, 이점, 속점, 근거, 라인=None, 프로젝트=None, 기집행=None, **더):
        it = {"라인": 라인, "프로젝트": 프로젝트, "기집행": 기집행, "점수": round(점, 4), "이름점수": round(이점, 4),
              "속성점수": (round(속점, 4) if 속점 is not None else None), "근거": 근거, "종류": 종류, "왼쪽": 왼, "오른쪽": 오}
        it.update(더)
        결과["짝"].append(it)
        return it

    def 제안(자리, 값, 이점, 속점, 점, 글):
        결과["제안"].append({"자리": 자리, "값": 값, "근거범위": None,
                         "딱지": "[계산 — 개체 연결(이름 %.2f · 속성 %s · 문턱 %.2f)]" % (이점, ("%.2f" % 속점) if 속점 is not None else "없음", 문턱),
                         "확신": "강" if 점 >= 0.75 else "보통", "글": 글})

    # ── ① F 능력단위 → 라인(한 대 하나 — 엔진자리가 가리키면 그것, 아니면 헝가리안)
    능력단위 = [dict(x, _번호=k) for k, x in enumerate(투.get("능력단위") or []) if isinstance(x, dict) and x.get("이름")]
    남은 = []
    for x in 능력단위:
        j = _엔진자리라인(x.get("엔진자리"))
        if j and j in 번호로:
            번호로[j]["별칭"].append(x["이름"])
            짝적기("능력단위→라인", x["이름"], 번호로[j]["이름"], 1.0, 이름점수([x["이름"]], [번호로[j]["이름"]], E), None,
                 "엔진자리 %s" % x.get("엔진자리"), 라인=j, 원본={"파일": "투자능력.json", "칸": "능력단위", "번호": x["_번호"]})
        else:
            남은.append(x)
    if 남은 and L:
        M = [[이름점수([x["이름"]], [l["이름"]], E) for l in L] for x in 남은]
        짝된 = set()
        for i, jj in 헝가리안(M):
            점 = M[i][jj]
            if 점 >= 문턱:
                짝된.add(i)
                L[jj]["별칭"].append(남은[i]["이름"])
                짝적기("능력단위→라인", 남은[i]["이름"], L[jj]["이름"], 점, 점, None, "이름(헝가리안)", 라인=L[jj]["번호"],
                     원본={"파일": "투자능력.json", "칸": "능력단위", "번호": 남은[i]["_번호"]})
        for i, x in enumerate(남은):
            if i not in 짝된:
                결과["짝없음"].append({"종류": "능력단위", "이름": x["이름"], "최고점수": round(max(M[i]), 4)})
    # F 프로젝트가 능력단위 이름을 적었으면 그 이름으로 라인을 찾는다(이미 짝된 능력단위면 그 라인)
    별칭능력 = {x["이름"]: l["번호"] for l in L for x in 능력단위 if x["이름"] in l["별칭"]}

    def 라인이름들(l):
        return [l["이름"]] + l["별칭"]

    def 가장가까운라인(이름들, 투자해=None, 리드=0):
        최 = None
        for l in L:
            이 = 이름점수(이름들, 라인이름들(l), E)
            연 = 연도점수(투자해, l["능력해"], 리드, E["연도여유"]) if 투자해 else None
            점, 속 = 합점수(이, {"연도": 연}, E["가중"], E.get("속성0거부", True))
            if 최 is None or 점 > 최[0] + 1e-12:
                최 = (점, 이, 속, l)
        return 최

    # ── ② 가정 프로젝트 → 라인(여럿이 한 곳 — 행마다 최고)
    능력있음 = any(l["판매량산정"] == "능력" for l in L)
    후보라인 = {}                                         # 가정 프로젝트 번호 → ② 가 낸 후보 라인(⑤ 기집행이 쓴다)
    for x in P:
        대상 = "프로젝트 %d 「%s」" % (x["번호"], x["이름"])
        if x["라인"]:
            최 = 가장가까운라인([x["이름"]], x["투자해"], x["리드타임"]) if L else None
            if 최 and 최[3]["번호"] != x["라인"] and 최[0] >= 문턱 and x["라인"] in 번호로:
                적힌 = 이름점수([x["이름"]], 라인이름들(번호로[x["라인"]]), E)
                if 최[1] > 적힌 + 0.25:
                    알림("적힌 라인과 이름 짝이 다르다", 대상, 최[3]["번호"], x["라인"],
                       "%s 은 라인 %d 로 적혀 있는데 이름은 라인 %d 「%s」 와 더 닮았다(이름 점수 %.2f 대 %.2f) — 적힌 라인이 맞는지 본다"
                       % (대상, x["라인"], 최[3]["번호"], 최[3]["이름"], 최[1], 적힌), "참고")
            continue
        if x["구분"]:
            결과["구분대응"].append({"프로젝트": x["번호"], "이름": x["이름"], "구분": x["구분"],
                                 "글": "구분 %s 에 묶였다(라인 짝 대상 아님 — ㊷ 는 라인 짝에 넣지 않고 저량 구분이면 ④ 에서 본다)" % x["구분"]})
            continue
        if not L:
            continue
        최 = 가장가까운라인([x["이름"]], x["투자해"], x["리드타임"])
        if 최[0] >= 문턱:
            l = 최[3]
            후보라인[x["번호"]] = l["번호"]
            짝적기("프로젝트→라인", 대상, l["이름"], 최[0], 최[1], 최[2], "이름 + 투자 해 ↔ 능력 해", 라인=l["번호"], 프로젝트=x["번호"],
                 원본={"파일": "가정", "칸": "구조.투자.프로젝트", "번호": x["번호"]})
            결과["대응제안"].append("가정 구조.투자.프로젝트[번호=%d].라인 = %d   (「%s」 → 라인 「%s」 · 점수 %.2f)"
                               % (x["번호"], l["번호"], x["이름"], l["이름"], 최[0]))
            제안("구조.투자.프로젝트[번호=%d].라인" % x["번호"], l["번호"], 최[1], 최[2], 최[0],
               "㊷ 가 이 프로젝트 CAPEX 를 라인 %d 「%s」 의 능력 증분과 견주게 된다" % (l["번호"], l["이름"]))
            알림("이름이 달라 짝을 못 찾던 라인 — 후보 있음", 대상, l["번호"], 문턱,
               "%s 에 라인이 비어 ㊷ 가 어느 능력과도 견주지 못했다 — 라인 %d 「%s」 가 후보다(점수 %.2f). 맞으면 `라인` 칸에 적는다"
               % (대상, l["번호"], l["이름"], 최[0]), "참고")
        else:
            결과["짝없음"].append({"종류": "프로젝트", "이름": x["이름"], "번호": x["번호"], "최고점수": round(최[0], 4),
                               "가까운라인": 최[3]["이름"]})
            if 능력있음:
                알림("점수 문턱 밑 — 사람이 대응을 적는다", 대상, round(최[0], 4), 문턱,
                   "%s 에 라인이 없고 이름 · 투자 해로도 닮은 라인이 없다(최고 %.2f · 「%s」) — ㊷ 는 이 투자를 어느 능력과도 견주지 못한다. "
                   "라인 · 구분을 적거나(구조.투자.프로젝트[].라인 · 구분) 능력 밖의 투자라는 까닭을 근거(86p)에 적는다"
                   % (대상, 최[0], 최[3]["이름"]), "경보")

    # ── ③ F 단위능력당투자비 · 값짝 → 라인(㊷ 가 글자로 못 찾는 것만)
    def 글자짝(이름):
        이름 = ("%s" % (이름 or "")).strip()
        return next((l["번호"] for l in L if l["이름"] == 이름), None)

    for 칸, 키, 이름키 in (("단위능력당투자비", "값", "대상"), ("값짝", "차이율", "능력단위")):
        for i, x in enumerate(투.get(칸) or []):
            if not isinstance(x, dict) or not _수(x.get(키)):
                continue
            if isinstance(x.get("라인"), int) and x["라인"]:
                continue
            if 글자짝(x.get(이름키)) or not L:
                continue
            대상 = "%s[%d] 「%s」" % (칸, i, x.get(이름키))
            최 = 가장가까운라인([x.get(이름키) or ""])
            if 최[0] >= 문턱:
                l = 최[3]
                짝적기("%s→라인" % 칸, 대상, l["이름"], 최[0], 최[1], 최[2], "이름(라인 이름 + 별칭)", 라인=l["번호"],
                     원본={"파일": "투자능력.json", "칸": 칸, "번호": i})
                결과["대응제안"].append("투자능력.json %s[%d].라인 = %d   (「%s」 → 라인 「%s」 · 점수 %.2f)"
                                   % (칸, i, l["번호"], x.get(이름키), l["이름"], 최[0]))
                제안("투자능력.json %s[%d].라인" % (칸, i), l["번호"], 최[1], 최[2], 최[0],
                   "㊷ 가 이 F 실측을 라인 %d 「%s」 의 단위 투자비와 명시 대응으로 견주게 된다" % (l["번호"], l["이름"]))
                알림("이름이 달라 짝을 못 찾던 라인 — 후보 있음", 대상, l["번호"], 문턱,
                   "F %s 「%s」 는 ㊷ 가 글자로 짝을 못 찾는다 — 라인 %d 「%s」 가 후보다(점수 %.2f). 맞으면 `라인` 칸에 적는다"
                   % (칸, x.get(이름키), l["번호"], l["이름"], 최[0]), "참고")
            else:
                결과["짝없음"].append({"종류": 칸, "이름": x.get(이름키), "최고점수": round(최[0], 4)})
                if (x.get(이름키) or "").strip():
                    알림("점수 문턱 밑 — 사람이 대응을 적는다", 대상, round(최[0], 4), 문턱,
                       "F %s 「%s」 와 닮은 라인이 없다(최고 %.2f) — ㊷ 는 회사 전체 값으로 목록에 나란히 적는다. 한 라인의 값이면 `라인` 칸에 적는다"
                       % (칸, x.get(이름키), 최[0]), "경보")

    # ── ④ F 프로젝트 ↔ 가정 프로젝트(한 대 하나 — 헝가리안, 남은 가정 프로젝트는 분할 짝)
    FP = [dict(x, _번호=k) for k, x in enumerate(투.get("프로젝트") or []) if isinstance(x, dict) and x.get("이름")]
    F짝 = {}                                             # F 프로젝트 이름 → [(가정 프로젝트, 점수)]
    if FP and P:
        M, 속표 = [], []
        for x in FP:
            줄, 속줄 = [], []
            for y in P:
                이 = 이름점수([x["이름"]], [y["이름"]], E)
                연 = 구간점수(_F해(x), y["투자해"])
                금 = 금액점수(_F총액(x), y["총액"], E["금액자릿수"])
                점, 속 = 합점수(이, {"연도": 연, "금액": 금}, E["가중"], E.get("속성0거부", True))
                if x.get("통화") and y.get("통화") and x["통화"] != y["통화"]:
                    점 = 0.0
                줄.append(점)
                속줄.append((이, 속))
            M.append(줄)
            속표.append(속줄)
        가정짝된 = set()
        for i, jj in 헝가리안(M):
            if M[i][jj] >= 문턱:
                가정짝된.add(jj)
                F짝.setdefault(FP[i]["이름"], []).append((P[jj], M[i][jj]))
                짝적기("F프로젝트→프로젝트", "F 「%s」" % FP[i]["이름"], "프로젝트 %d 「%s」" % (P[jj]["번호"], P[jj]["이름"]), M[i][jj],
                     속표[i][jj][0], 속표[i][jj][1], "이름 + 연도 구간 + 금액 자릿수(헝가리안)", 라인=P[jj]["라인"], 프로젝트=P[jj]["번호"],
                     F총액=_F총액(FP[i]), 가정예측합=P[jj]["총액"], 원본={"파일": "투자능력.json", "칸": "프로젝트", "번호": FP[i]["_번호"]})
        for jj, y in enumerate(P):                       # 분할 짝 — 헝가리안이 남긴 가정 프로젝트
            if jj in 가정짝된:
                continue
            i = max(range(len(FP)), key=lambda k: M[k][jj])
            if M[i][jj] >= 문턱 and FP[i]["이름"] in F짝:
                F짝[FP[i]["이름"]].append((y, M[i][jj]))
                짝적기("F프로젝트→프로젝트", "F 「%s」" % FP[i]["이름"], "프로젝트 %d 「%s」" % (y["번호"], y["이름"]), M[i][jj],
                     속표[i][jj][0], 속표[i][jj][1], "분할 짝(헝가리안 뒤 남은 가정 프로젝트 — 같은 F 프로젝트를 나눠 가짐)", 라인=y["라인"], 프로젝트=y["번호"],
                     F총액=_F총액(FP[i]), 가정예측합=y["총액"], 원본={"파일": "투자능력.json", "칸": "프로젝트", "번호": FP[i]["_번호"]})
        for i, x in enumerate(FP):
            if x["이름"] not in F짝:
                결과["짝없음"].append({"종류": "F프로젝트", "이름": x["이름"], "최고점수": round(max(M[i]), 4), "성격": x.get("성격")})
                if (x.get("성격") or "성장") == "성장":
                    k = max(range(len(P)), key=lambda c: M[i][c])
                    알림("F 성장 프로젝트에 가정 짝이 없다", "F 프로젝트 「%s」" % x["이름"], round(max(M[i]), 4), 문턱,
                       "F 가 찾은 성장 프로젝트 「%s」(총액 %s)에 닮은 가정 프로젝트가 없다(최고 %.2f · 「%s」) — 가정에 없는 투자인지, 단계로 쪼개 이름이 갈렸는지"
                       "(묶음 총액 대 단계 금액) 본선이 본다" % (x["이름"], _F총액(x), max(M[i]), P[k]["이름"]), "참고")
                continue
            # F 프로젝트의 능력단위가 라인을 가리키는데 짝 가정 프로젝트에 라인 · 구분이 없으면 — 두 단계 대응
            j = 별칭능력.get(x.get("능력단위") or "")
            if not j and (x.get("능력단위") or "").strip() and L:
                최 = 가장가까운라인([x["능력단위"]])
                j = 최[3]["번호"] if 최[0] >= 문턱 else None
            for y, 점 in F짝[x["이름"]]:
                if j and not y["라인"] and not y["구분"] and y["번호"] not in 후보라인:
                    후보라인[y["번호"]] = j
                    결과["대응제안"].append("가정 구조.투자.프로젝트[번호=%d].라인 = %d   (F 프로젝트 「%s」 의 능력단위 「%s」 — 두 단계 짝)"
                                       % (y["번호"], j, x["이름"], x["능력단위"]))
                    제안("구조.투자.프로젝트[번호=%d].라인" % y["번호"], j, 점, None, 점,
                       "F 프로젝트 「%s」 의 능력단위 「%s」 가 라인 %d 와 짝이다(라인 ↔ F 프로젝트 ↔ 가정 프로젝트)" % (x["이름"], x["능력단위"], j))

    # ── ⑤ F 기집행 → 라인(가정 프로젝트의 라인 — 적힌 것 또는 ② · ④ 후보 → 이름)
    def 라인of(y):
        return y["라인"] or 후보라인.get(y["번호"])

    for i, x in enumerate(투.get("기집행") or []):
        if not isinstance(x, dict) or not _수(x.get("금액")) or not x.get("금액"):
            continue
        if isinstance(x.get("라인"), int) and x["라인"]:
            continue
        대상 = "기집행[%d] 「%s」" % (i, x.get("프로젝트"))
        j, 근, 점, 이점 = None, None, 0.0, 0.0
        후 = [(y, s) for y, s in F짝.get(x.get("프로젝트"), []) if 라인of(y)]
        같은 = [y for y in P if 라인of(y) and 정규화(y["이름"]) == 정규화(x.get("프로젝트"))]
        if 같은:
            j, 근, 점, 이점 = 라인of(같은[0]), "가정 프로젝트 %d(이름 같음)의 라인%s" % (같은[0]["번호"], "" if 같은[0]["라인"] else "(② 후보)"), 1.0, 1.0
        elif 후 and len({라인of(y) for y, _s in 후}) == 1:
            y, s = max(후, key=lambda t: t[1])
            j, 근, 점, 이점 = 라인of(y), "F 프로젝트 짝 → 가정 프로젝트 %d 의 라인%s" % (y["번호"], "" if y["라인"] else "(② 후보)"), s, s
        elif L:
            최 = 가장가까운라인([x.get("프로젝트") or ""])
            if 최[0] >= 문턱:
                j, 근, 점, 이점 = 최[3]["번호"], "이름(라인 이름 + 별칭)", 최[0], 최[1]
        if j:
            있 = 표.get(str(1600 + j))
            짝적기("기집행→라인", 대상, "라인 %d 「%s」" % (j, 번호로[j]["이름"] if j in 번호로 else "?"), 점, 이점, None, 근, 라인=j,
                 기집행="표 %d" % (1600 + j), 원본={"파일": "투자능력.json", "칸": "기집행", "번호": i})
            결과["대응제안"].append("가정 표.%d 기집행 ← 투자능력.json 기집행[%d] 「%s」 %s   (%s%s)"
                               % (1600 + j, i, x.get("프로젝트"), x.get("금액"), 근, " · 표에 이미 값이 있다 — 겹치는지 본다" if 있 else ""))
            제안("표.%d" % (1600 + j), x.get("금액"), 이점, None, 점,
               "F 기집행 「%s」 을 라인 %d 의 기집행 투자(자산군별 — `자산군별` 칸)로 옮긴다%s"
               % (x.get("프로젝트"), j, " — 표에 이미 값이 있다" if 있 else ""))
        else:
            결과["짝없음"].append({"종류": "기집행", "이름": x.get("프로젝트"), "최고점수": None})
            알림("점수 문턱 밑 — 사람이 대응을 적는다", 대상, None, 문턱,
               "F 기집행 「%s」 이 어느 라인에도 닿지 않는다 — 표 1600 + j 의 어느 줄로 옮길지 사람이 정한다" % x.get("프로젝트"), "경보")
    결과["라인"] = [{"번호": l["번호"], "이름": l["이름"], "구분": l["구분"], "판매량산정": l["판매량산정"], "능력해": l["능력해"],
                   "별칭": l["별칭"]} for l in L]
    return 결과


def 계산(가정, 가정경로, 설정=None):
    return 돌기(가정, 가정경로, 설정 or 설정읽기())


def 개체연결읽기(가정경로):
    """다른 도구가 읽는 자리 — (내용, 경로) 또는 (None, None)."""
    return 정상화.파일찾기("개체연결.json", 가정경로)


def 찍기(결과):
    L = ["── 개체 연결 (기법 5) ──"]
    if 결과.get("폴백"):
        L.append("폴백 — %s" % 결과["폴백"])
    for l in 결과.get("라인") or []:
        L.append("  라인 %d 「%s」 구분 %s · 능력 첫 증가 %s · 별칭 %s"
                 % (l["번호"], l["이름"], l["구분"], l["능력해"] or "-", " · ".join(l["별칭"]) or "-"))
    for x in 결과["짝"]:
        L.append("  짝 %-14s %s → %s  점수 %.2f (이름 %.2f · 속성 %s) — %s"
                 % (x["종류"], x["왼쪽"], x["오른쪽"], x["점수"], x["이름점수"],
                    ("%.2f" % x["속성점수"]) if x.get("속성점수") is not None else "-", x["근거"]))
    for x in 결과["짝없음"]:
        L.append("  짝 없음 %s 「%s」 최고 %s" % (x["종류"], x.get("이름"), x.get("최고점수")))
    for x in 결과.get("구분대응") or []:
        L.append("  구분 대응 프로젝트 %d 「%s」 → 구분 %s" % (x["프로젝트"], x["이름"], x["구분"]))
    for z in 결과["대응제안"]:
        L.append("  대응제안 — %s" % z)
    for s in 결과["신호"]:
        L.append("  [%s] %s — %s" % (s["등급"], s["종류"], s["글"]))
    return "\n".join(L)


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                    # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(allow_abbrev=False, description="개체 연결 — 라인 · 프로젝트 · 능력 단위 · 기집행의 짝 후보")
    ap.add_argument("가정")
    ap.add_argument("--낼", default=None)
    ap.add_argument("--설정", default=None)
    a = ap.parse_args(argv)
    try:
        설정 = 설정읽기(a.설정)
    except (OSError, ValueError) as e:
        print("개체연결 — 설정을 못 읽었다: %s" % e)
        return 입력오류
    try:
        가정 = json.load(io.open(a.가정, encoding="utf-8"))
    except (OSError, ValueError) as e:
        print("개체연결 — 가정 파일을 못 읽었다: %s" % e)
        return 입력오류
    if not isinstance(가정, dict):
        print("개체연결 — 가정 파일이 객체가 아니다")
        return 입력오류
    결과 = 계산(가정, a.가정, 설정)
    낼 = a.낼 or os.path.join(os.path.dirname(os.path.abspath(a.가정)), "_raw", "개체연결.json")
    os.makedirs(os.path.dirname(낼), exist_ok=True)
    io.open(낼, "w", encoding="utf-8").write(json.dumps(결과, ensure_ascii=False, indent=1))
    print(찍기(결과))
    print("→ %s" % 낼)
    return 발견 if any(s["등급"] == "경보" for s in 결과["신호"]) else 통과


if __name__ == "__main__":
    sys.exit(main())

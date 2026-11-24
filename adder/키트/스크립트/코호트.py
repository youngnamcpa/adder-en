# -*- coding: utf-8 -*-
"""코호트 — 베이지안 코호트 분해(기법 7 · 2026-10-21). 합산 저량(가입자 · 점포 · 좌석 · 설치기반)과 기간 유입만 주어졌을 때,
유입 연도별 잔존을 **이동 베타-기하(sBG — Fader & Hardie)** 로 풀어 신규 코호트의 높은 초기 이탈과 성숙 코호트의 낮은 이탈을 가른다.

왜 있나 — 엔진의 저량 굴림(`판매량산정 = 저량`, 엔진 매출.py `_저량굴림`)은 기초 저량 전체에 **단일 유출률**(A-57(5+s))을 곱한다.
급성장기에 신규 유입이 많았던 회사는 초기 이탈이 섞여 관측 유출률이 부풀고, 그것을 미래에 그대로 밀면 성숙 기반을 과소평가한다
(반대로 유입이 멈춘 회사는 남은 기반이 늙어 유출률이 내려간다). 이 도구는 **코호트 구성 변화가 만드는 연도별 유효 유출률 경로**와
그 상하한을 엔진의 단일 가정과 나란히 낸다. **값을 쓰지 않는다** — 가정 575+s 를 고치는 것은 본선이고, 거친 바퀴 손잡이의 근거범위 후보다.

모형(설정은 `진실코호트설정.json` 「코호트」 — 결과를 보기 전에 정한 값)
  · 한 고객(점포)의 기간 이탈 확률 θ ~ Beta(α, β). 가입 뒤 t년 잔존 S(t) = B(α, β + t) / B(α, β)(연속 t — 반기 열도 같은 식)
  · 첫 관측 시점의 저량은 「성숙」 구성 — 해마다 같은 유입이 쌓인 정상 상태(나이 a 의 몫 ∝ S(a), a = 0 … 최대나이)로 쪼갠다
  · 구간마다 기존 코호트는 S(나이 + 길이)/S(나이) 만큼 남고, 그 구간의 유입(13번 605+s — 기간 양)이 나이 0 코호트로 들어온다
    (엔진과 같다 — 기말 = 기초 + 유입 − 기초 × 유출률 × 기간)
  · (α, β) 는 로그 공간 격자 + 좌표 탐색으로 Σ(ln 기대 저량 − ln 관측 저량)² 을 줄인다. 근사 신용 영역 = 잔차제곱합이
    최솟값 × (1 + χ²₂(0.90) ÷ (n − 2)) 안인 점들
  · 예측 — 가정의 유입 경로(A-57s · 열별 · 설정 시나리오)를 그대로 두고 코호트를 굴려 열마다 유효 유출률
    = (1 − 남은 기존분 ÷ 기초) ÷ 기간(년). 신용 영역의 점마다 같은 일을 해 열마다 최소 · 최대 = 근거범위

    python 스크립트/코호트.py 가정.json [--설정 경로] [--낼 경로] [--계열 계열.json]

읽는 것  가정의 `구조.매출구분[]`(경로 = 수준 · 판매량산정 = 저량 · 판매량꼴 = 저량) · 원천 13번 600+s(기말 저량) · 605+s(기간 유입) ·
         가정 570+s(유입) · 575+s(유출률) · 시점가정 590+s(기준일 저량 — 저량공시 = 아니오). 13번에 실적이 몇 해 안 되면
         `--계열`(`{"<s>": {"저량": {기간 ID: 값}, "유입": {기간 ID: 값}}}` — A3 사업지표 · 회사 IR 의 긴 계열)로 늘린다
내는 것  `_raw/코호트.json` — 형식 · 만든날 · 설정 · 입력 · 폴백 · 구분[] · 제안[] · 신호[]. 읽기 함수 `코호트읽기(가정경로)`
종료 코드 0 경보 없음(해당 없음 · 표본 부족 포함) · 1 경보 신호(유효 유출률이 단일 가정과 갈림) · 2 입력 오류
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import math
import os
import re
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)

from 종료코드 import 통과, 발견, 입력오류  # noqa: E402
import 정상화  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                            # noqa: BLE001
    pass

형식이름 = "코호트 1"
산출이름 = "코호트.json"
유입번호 = lambda s: 570 + s          # noqa: E731 — 엔진 매출.py 저량유입번호
유출률번호 = lambda s: 575 + s        # noqa: E731 — 저량유출률번호(A-57(5+s))
기준일저량번호 = lambda s: 590 + s     # noqa: E731
기말저량원천 = lambda s: 600 + s      # noqa: E731
저량유입원천 = lambda s: 605 + s      # noqa: E731


def 설정읽기(경로=None):
    p = 경로 or os.path.join(여기, "진실코호트설정.json")
    return json.load(io.open(p, encoding="utf-8"))["코호트"]


# ───────────────────────────────────────────── sBG 잔존

def 로그생존(t, a, b):
    """ln S(t), S(t) = B(a, b + t) / B(a, b)."""
    return math.lgamma(b + t) + math.lgamma(a + b) - math.lgamma(b) - math.lgamma(a + b + t)


def 생존(t, a, b):
    return math.exp(로그생존(t, a, b))


def 잔존비(나이, 길이, a, b):
    """나이 a 코호트가 길이 L 동안 남는 비 S(a + L) / S(a)."""
    return math.exp(math.lgamma(b + 나이 + 길이) - math.lgamma(b + 나이) - math.lgamma(a + b + 나이 + 길이) + math.lgamma(a + b + 나이))


def 성숙구성(기초, a, b, 최대나이):
    w = [생존(k, a, b) for k in range(int(최대나이) + 1)]
    s = sum(w)
    return [[기초 * x / s, float(k)] for k, x in enumerate(w)]


def 굴리기(코, 구간들, a, b):
    """코호트 [[수, 나이]…] 를 구간 [(길이, 유입)…] 대로 굴린다 → (구간마다 [기초, 기존 생존분, 기말], 마지막 코호트)."""
    코 = [list(x) for x in 코]
    낸 = []
    for L, I in 구간들:
        기초 = sum(n for n, _ in 코)
        새 = [[n * 잔존비(나이, L, a, b), 나이 + L] for n, 나이 in 코]
        남 = sum(n for n, _ in 새)
        새.append([max(I, 0.0), 0.0])
        코 = 새
        낸.append((기초, 남, sum(n for n, _ in 코)))
    return 낸, 코


def 정상유출률(a, b, 최대나이):
    """성숙 구성의 한 해 유출률 = 1 − Σ 몫 × S(a + 1)/S(a)."""
    코 = 성숙구성(1.0, a, b, 최대나이)
    return 1.0 - sum(n * 잔존비(나이, 1.0, a, b) for n, 나이 in 코)


# ───────────────────────────────────────────── 적합

def 잔차(a, b, 관측, 최대나이):
    """관측 = [(길이, 유입, 저량)…] (첫 줄은 기초 저량 — 길이 · 유입 None). → (잔차제곱합, 기대 저량 목록)."""
    기초 = 관측[0][2]
    구간들 = [(L, I) for L, I, _ in 관측[1:]]
    낸, _ = 굴리기(성숙구성(기초, a, b, 최대나이), 구간들, a, b)
    sse, 기대 = 0.0, []
    for (_, _, o), (_, _, e) in zip(관측[1:], 낸):
        기대.append(e)
        if o > 0 and e > 0:
            sse += (math.log(e) - math.log(o)) ** 2
        else:
            sse += 1e6
    return sse, 기대


def 적합(관측, 설정):
    """로그 공간 격자 → 좌표 탐색. → {"α", "β", "sse", "격자": [(la, lb, sse)…]}."""
    A = 설정["최대나이"]
    la0, la1, na = 설정["격자_로그알파"]
    lb0, lb1, nb = 설정["격자_로그베타"]
    격자 = []
    for i in range(int(na)):
        la = la0 + (la1 - la0) * i / (int(na) - 1)
        for j in range(int(nb)):
            lb = lb0 + (lb1 - lb0) * j / (int(nb) - 1)
            격자.append((la, lb, 잔차(math.exp(la), math.exp(lb), 관측, A)[0]))
    la, lb, _best = min(격자, key=lambda x: x[2])

    def f(p):
        v = 잔차(math.exp(p[0]), math.exp(p[1]), 관측, A)[0]
        격자.append((p[0], p[1], v))                          # 정밀화 중에 본 점도 신용 영역의 후보다(최적점 곁이 촘촘해진다)
        return v
    (la, lb), best = _넬더미드(f, [la, lb], 0.3, int(설정["정밀화_반복"]))
    return {"α": math.exp(la), "β": math.exp(lb), "sse": best, "격자": 격자}


def _넬더미드(f, x0, 단계, 최대):
    """2차원 넬더–미드(로그 공간) — 결정적. sBG 의 (α, β) 는 평균 이탈 방향의 능선이 길어 좌표 탐색이 덜 수렴한다."""
    점 = [list(x0), [x0[0] + 단계, x0[1]], [x0[0], x0[1] + 단계]]
    값 = [f(p) for p in 점]
    for _ in range(최대):
        차례 = sorted(range(3), key=lambda i: 값[i])
        점, 값 = [점[i] for i in 차례], [값[i] for i in 차례]
        크기 = max(abs(점[i][j] - 점[0][j]) for i in (1, 2) for j in (0, 1))
        if 크기 < 1e-7:
            break
        c = [(점[0][0] + 점[1][0]) / 2.0, (점[0][1] + 점[1][1]) / 2.0]
        r = [c[0] + (c[0] - 점[2][0]), c[1] + (c[1] - 점[2][1])]
        fr = f(r)
        if fr < 값[0]:
            e = [c[0] + 2.0 * (c[0] - 점[2][0]), c[1] + 2.0 * (c[1] - 점[2][1])]
            fe = f(e)
            점[2], 값[2] = (e, fe) if fe < fr else (r, fr)
        elif fr < 값[1]:
            점[2], 값[2] = r, fr
        else:
            k = [c[0] + 0.5 * (점[2][0] - c[0]), c[1] + 0.5 * (점[2][1] - c[1])]
            fk = f(k)
            if fk < 값[2]:
                점[2], 값[2] = k, fk
            else:
                for i in (1, 2):
                    점[i] = [점[0][0] + 0.5 * (점[i][0] - 점[0][0]), 점[0][1] + 0.5 * (점[i][1] - 점[0][1])]
                    값[i] = f(점[i])
    i = min(range(3), key=lambda j: 값[j])
    return 점[i], 값[i]


def 신용영역(적, n, 설정):
    문턱 = 적["sse"] * (1.0 + float(설정["신용영역_카이제곱_자유도2_0.90"]) / max(n - 2, 1)) + 1e-12
    점 = [(math.exp(la), math.exp(lb)) for la, lb, v in 적["격자"] if v <= 문턱]
    if len(점) > 200:                                          # 결정적으로 고르게 솎는다
        k = len(점) / 200.0
        점 = [점[int(i * k)] for i in range(200)]
    return 점, 문턱


# ───────────────────────────────────────────── 계열 읽기

def _끝달(ID, 축, 결산월):
    """기간 ID → 끝나는 달(연 × 12 + 월). 축에 있으면 축의 종료일을 쓴다."""
    if 축 is not None and ID in 축.ID:
        d = 축.열[축.ID.index(ID)].종료일
        return d.year * 12 + d.month
    m = re.fullmatch(r"FY(\d{4})[AE]?", ID)
    if m:
        return int(m.group(1)) * 12 + 결산월
    m = re.fullmatch(r"([12])H(\d{2})[AE]?", ID)
    if m:
        return (2000 + int(m.group(2))) * 12 + 결산월 - 12 + 6 * int(m.group(1))
    m = re.fullmatch(r"([1-4])Q(\d{2})[AE]?", ID)
    if m:
        return (2000 + int(m.group(2))) * 12 + 결산월 - 12 + 3 * int(m.group(1))
    return None


def _수(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def 관측짓기(저량, 유입, 축, 결산월):
    """{ID: 저량} · {ID: 유입} → 끝달 차례의 가장 긴 이어진 사슬 [(길이, 유입, 저량)…](첫 줄은 기초). 사슬 ID 목록과 함께."""
    점 = sorted(((_끝달(k, 축, 결산월), k, _수(v)) for k, v in (저량 or {}).items()
               if _끝달(k, 축, 결산월) is not None and _수(v) is not None and _수(v) > 0), key=lambda x: x[0])
    사슬, 지금 = [], []
    for 끝, k, v in 점:
        if not 지금:
            지금 = [(None, None, v, k, 끝)]
            continue
        I = _수((유입 or {}).get(k))
        L = (끝 - 지금[-1][4]) / 12.0
        if I is None or L <= 0:
            사슬.append(지금)
            지금 = [(None, None, v, k, 끝)]
            continue
        지금.append((L, I, v, k, 끝))
    if 지금:
        사슬.append(지금)
    긴 = max(사슬, key=len) if 사슬 else []
    return [(L, I, v) for L, I, v, _, _ in 긴], [k for *_, k, _ in 긴]


# ───────────────────────────────────────────── 구분 하나

def _가정줄(가정, 번호, 시나리오):
    v = ((가정.get("가정") or {}).get(str(번호)) or {}).get(시나리오)
    return v if isinstance(v, dict) else {}


def 구분하나(가정, 구분, 축, 설정, 덧계열=None):
    s = 구분.get("번호")
    이름 = 구분.get("이름") or "매출 구분 %s" % s
    줄 = {"매출구분": s, "이름": 이름, "판정": None, "까닭": "", "관측": [], "α": None, "β": None, "평균유출률": None,
         "적합오차": None, "정상상태유출률": None, "유효유출률경로": {}, "근거범위": {}, "엔진유출률": {}, "신용영역점수": 0}
    if 구분.get("판매량꼴") != "저량":
        줄["판정"], 줄["까닭"] = "해당 없음", "판매량꼴 = 유량(잔고 소진 — 수주잔고 · 계약 잔액)은 고객 잔존 모형의 대상이 아니다"
        return 줄
    결산월 = int(((가정.get("기간") or {}).get("결산월")) or 12)
    원 = 가정.get("원천") or {}
    저량 = dict(원.get(str(기말저량원천(s))) or {})
    유입 = dict(원.get(str(저량유입원천(s))) or {})
    출처 = "13번 %d · %d" % (기말저량원천(s), 저량유입원천(s))
    if 덧계열 and str(s) in 덧계열:
        더 = 덧계열[str(s)]
        for k, v in (더.get("저량") or {}).items():
            저량.setdefault(k, v)
        for k, v in (더.get("유입") or {}).items():
            유입.setdefault(k, v)
        출처 += " + 덧계열"
    관측, ID들 = 관측짓기(저량, 유입, 축, 결산월)
    for i, (L, I, v) in enumerate(관측):
        한 = {"ID": ID들[i], "저량": v, "유입": I}
        if i > 0 and 관측[i - 1][2] > 0 and L:
            한["관측유출률"] = (관측[i - 1][2] + I - v) / 관측[i - 1][2] / L
        줄["관측"].append(한)
    시 = 설정["시나리오"]
    엔 = _가정줄(가정, 유출률번호(s), 시)
    줄["엔진유출률"] = {축.ID[i]: _수(엔.get(축.ID[i])) for i in 축.예측}
    if len(관측) < int(설정["최소관측"]):
        줄["판정"] = "표본 부족"
        줄["까닭"] = "이어진 저량 관측 %d개(%s) — 최소 %d개. 13번 실적 열이 짧으면 `--계열` 로 긴 계열(A3 사업지표 · IR)을 준다" % (
            len(관측), 출처, int(설정["최소관측"]))
        return 줄
    적 = 적합(관측, 설정)
    a, b = 적["α"], 적["β"]
    n = len(관측) - 1
    rmse = math.sqrt(적["sse"] / n)
    영역, _문턱 = 신용영역(적, n, 설정)
    if (a, b) not in 영역:
        영역.append((a, b))
    줄.update({"α": a, "β": b, "평균유출률": a / (a + b), "적합오차": rmse, "신용영역점수": len(영역),
              "정상상태유출률": 정상유출률(a, b, 설정["최대나이"])})
    # 기준일 구성 — 적합한 굴림의 마지막 코호트를 기준일 저량에 맞춰 늘이고 줄인다
    _, 코 = 굴리기(성숙구성(관측[0][2], a, b, 설정["최대나이"]), [(L, I) for L, I, _ in 관측[1:]], a, b)
    기준ID = 축.ID[축.기준일]
    기준값 = _수(저량.get(기준ID))
    if 기준값 is None:
        기준값 = _수((가정.get("시점가정") or {}).get(str(기준일저량번호(s))))
    마지막 = 관측[-1][2]
    if 기준값 is None or ID들[-1] != 기준ID:
        줄["까닭"] += "기준일(%s) 저량이 사슬의 끝이 아니다 — 마지막 관측(%s)에서 굴린다. " % (기준ID, ID들[-1])
        기준값 = 마지막
    합 = sum(x for x, _ in 코) or 1.0
    코 = [[x * 기준값 / 합, 나이] for x, 나이 in 코]
    유 = _가정줄(가정, 유입번호(s), 시)
    구간 = []
    for i in 축.예측:
        L = 축.열[i].년
        I연 = _수(유.get(축.ID[i]))
        구간.append((축.ID[i], L, (I연 or 0.0) * L, I연 is None))
    if any(x[3] for x in 구간):
        줄["까닭"] += "유입(A-%d) 이 빈 열은 유입 0 으로 굴렸다. " % 유입번호(s)

    def 경로(aa, bb, 시작코):
        r = {}
        코2 = [list(x) for x in 시작코]
        for ID, L, I, _빈 in 구간:
            낸, 코2 = 굴리기(코2, [(L, I)], aa, bb)
            기초, 남, _ = 낸[0]
            r[ID] = (1.0 - 남 / 기초) / L if 기초 > 0 and L > 0 else None
        return r
    줄["유효유출률경로"] = 경로(a, b, 코)
    범 = {ID: [None, None] for ID, *_ in 구간}
    for aa, bb in 영역:
        # 영역의 점마다 같은 관측으로 다시 굴려 기준일 구성을 만든다(구성도 모수를 따라 움직인다)
        _, 코e = 굴리기(성숙구성(관측[0][2], aa, bb, 설정["최대나이"]), [(L, I) for L, I, _ in 관측[1:]], aa, bb)
        합e = sum(x for x, _ in 코e) or 1.0
        코e = [[x * 기준값 / 합e, 나이] for x, 나이 in 코e]
        for ID, v in 경로(aa, bb, 코e).items():
            if v is None:
                continue
            lo, hi = 범[ID]
            범[ID] = [v if lo is None else min(lo, v), v if hi is None else max(hi, v)]
    줄["근거범위"] = 범
    줄["판정"] = "적합 불량" if rmse > float(설정["적합불량_로그RMSE"]) else "적합"
    줄["까닭"] += "관측 %d개(%s) · 로그 RMSE %.3f · 평균 이탈 확률 α/(α+β) %.3f · 정상 상태 한 해 유출률 %.3f" % (
        len(관측), 출처, rmse, a / (a + b), 줄["정상상태유출률"])
    return 줄


# ───────────────────────────────────────────── 신호 · 제안 · 돌기

def _퍼(v):
    return "-" if v is None else "%.1f%%" % (v * 100)


def 신호짓기(구분들, 폴백, 설정):
    신 = []
    for 줄 in 구분들:
        대상 = "매출 구분 %s(%s)" % (줄["매출구분"], 줄["이름"])
        if 줄["판정"] == "표본 부족":
            신.append({"출처": "코호트", "종류": "표본 부족", "대상": 대상, "값": len(줄["관측"]), "문턱": int(설정["최소관측"]),
                      "글": "%s — 종전 규칙(단일 유출률 A-%d)대로 간다" % (줄["까닭"], 유출률번호(줄["매출구분"])), "등급": "참고"})
            continue
        if 줄["판정"] not in ("적합", "적합 불량"):
            continue
        관 = [x.get("관측유출률") for x in 줄["관측"] if x.get("관측유출률") is not None]
        최근 = sum(관[-2:]) / len(관[-2:]) if 관 else None
        정 = 줄["정상상태유출률"]
        if 최근 is not None and 정 and 최근 > 정 * (1 + float(설정["부풂_문턱"])):
            유입몫 = [x["유입"] / 줄["관측"][i - 1]["저량"] for i, x in enumerate(줄["관측"]) if i > 0 and 줄["관측"][i - 1]["저량"]]
            신.append({"출처": "코호트", "종류": "관측 유출률이 신규 코호트 비중으로 부풀었을 가능성", "대상": 대상,
                      "값": "최근 관측 %s · 정상 상태 %s" % (_퍼(최근), _퍼(정)), "문턱": "정상 상태 × %.2f" % (1 + float(설정["부풂_문턱"])),
                      "글": "최근 관측 유출률이 성숙 구성의 유출률보다 높다 — 유입이 기초의 %s 수준으로 들어와 첫해 이탈이 큰 코호트가 섞였다. "
                           "그 율을 미래에 그대로 밀면 성숙 기반을 과소평가한다" % (_퍼(유입몫[-1]) if 유입몫 else "-"),
                      "등급": "참고"})
        유, 엔 = 줄["유효유출률경로"], 줄["엔진유출률"]
        차 = [(abs(유[k] - 엔[k]), k) for k in 유 if 유.get(k) is not None and 엔.get(k) is not None]
        if 차:
            d, k = max(차)
            상대 = d / max(abs(엔[k]), 1e-9)
            if d > float(설정["갈림_문턱_절대"]) or 상대 > float(설정["갈림_문턱_상대"]):
                신.append({"출처": "코호트", "종류": "유효 유출률이 단일 가정과 갈림", "대상": 대상,
                          "값": "%s 열 유효 %s · 가정 %s" % (k, _퍼(유[k]), _퍼(엔[k])),
                          "문턱": "차 > %.1f%%p 또는 상대 > %.0f%%" % (float(설정["갈림_문턱_절대"]) * 100, float(설정["갈림_문턱_상대"]) * 100),
                          "글": "코호트 구성 변화를 넣으면 A-%d 의 유출률 경로가 단일 가정과 %s 갈린다(근거범위 %s ~ %s). 가정의 유출률이 그 범위의 "
                               "어디에 서는지와 그 까닭을 근거 칸에 적는다" % (
                                   유출률번호(줄["매출구분"]), "%.1f%%p" % (d * 100), _퍼(줄["근거범위"][k][0]), _퍼(줄["근거범위"][k][1])),
                          "등급": "경보" if 줄["판정"] == "적합" else "참고"})
        if 줄["판정"] == "적합 불량":
            신.append({"출처": "코호트", "종류": "적합 불량", "대상": 대상, "값": round(줄["적합오차"], 4),
                      "문턱": float(설정["적합불량_로그RMSE"]), "글": "sBG 굴림이 관측 저량을 잘 못 따라간다 — 유입 정의(총 유입인지 순증인지) · "
                      "연결 범위 변화(인수한 점포 · 가입자)를 먼저 본다. 경로는 참고로만 쓴다", "등급": "참고"})
    if 폴백:
        신.append({"출처": "코호트", "종류": "해당 없음" if 폴백.startswith("해당 없음") else "표본 부족", "대상": "저량 매출 구분",
                  "값": "-", "문턱": "-", "글": 폴백, "등급": "참고"})
    return 신


def 제안짓기(구분들):
    낸 = []
    for 줄 in 구분들:
        if 줄["판정"] not in ("적합", "적합 불량"):
            continue
        낸.append({"자리": "A-%d" % 유출률번호(줄["매출구분"]), "매출구분": 줄["매출구분"], "경로": 줄["유효유출률경로"], "근거범위": 줄["근거범위"],
                  "근거": "[계산 — 이동 베타-기하(sBG) 코호트 분해: α %.3g · β %.3g · 관측 %d개 · 로그 RMSE %.3f%s]" % (
                      줄["α"], 줄["β"], len(줄["관측"]), 줄["적합오차"], " · 적합 불량 — 참고" if 줄["판정"] == "적합 불량" else ""),
                  "쓰는 법": "4단계 유출률 경로 후보 · 거친 바퀴 손잡이의 근거범위 — 값을 넣는 것은 본선이다"})
    return 낸


def 돌기(가정경로, 설정, 덧계열=None):
    가정 = json.load(io.open(가정경로, encoding="utf-8"))
    from 기간축 import 기간축                                  # noqa: PLC0415
    축 = 기간축(가정)
    구분들 = [x for x in ((가정.get("구조") or {}).get("매출구분") or [])
            if isinstance(x, dict) and x.get("경로") == "수준" and x.get("판매량산정") == "저량"]
    낸 = [구분하나(가정, x, 축, 설정, 덧계열) for x in 구분들]
    폴백 = None
    if not 구분들:
        폴백 = "해당 없음 — 판매량산정 = 저량 인 매출 구분이 없다(코호트 잔존은 가입자 · 점포 · 좌석 · 설치기반 회사의 도구다)"
    elif not any(x["판정"] in ("적합", "적합 불량") for x in 낸):
        폴백 = ("해당 없음 — 저량 구분이 모두 잔고 소진형이다" if all(x["판정"] == "해당 없음" for x in 낸)
              else "표본 부족 — 적합할 만큼 긴 저량 계열이 없다(종전 단일 유출률)")
    return {"형식": 형식이름, "만든날": datetime.date.today().isoformat(), "설정": 설정,
            "입력": {"가정": os.path.abspath(가정경로), "저량구분": [x.get("번호") for x in 구분들], "덧계열": bool(덧계열)},
            "폴백": 폴백, "구분": 낸, "제안": 제안짓기(낸), "신호": 신호짓기(낸, 폴백, 설정)}


def 코호트읽기(가정경로):
    """→ 산출 dict(파일이 없거나 형식이 다르면 None). 거친 바퀴 · 4단계가 `제안[]` 의 경로 · 근거범위를 읽는다."""
    내용, _곳 = 정상화.파일찾기(산출이름, 가정경로)
    if not isinstance(내용, dict) or 내용.get("형식") != 형식이름:
        return None
    return 내용


def 찍기(결과):
    print("── 코호트 분해 — 저량 구분 %d ──" % len(결과["구분"]))
    for x in 결과["구분"]:
        print("  구분 %s(%s) %s — %s" % (x["매출구분"], x["이름"], x["판정"], x["까닭"][:140]))
        if x["유효유출률경로"]:
            print("    유효 유출률 " + " · ".join("%s %s" % (k, _퍼(v)) for k, v in x["유효유출률경로"].items()))
    if 결과["폴백"]:
        print("  폴백 — %s" % 결과["폴백"])
    for s in 결과["신호"]:
        print("  [%s] %s — %s" % (s["등급"], s["종류"], s["대상"]))


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="베이지안 코호트 분해 — 합산 저량 속 신규 · 성숙 코호트의 유효 유출률 경로")
    ap.add_argument("가정")
    ap.add_argument("--설정", default=None)
    ap.add_argument("--낼", default=None)
    ap.add_argument("--계열", default=None, help="긴 저량 · 유입 계열 JSON {\"<s>\": {\"저량\": {ID: 값}, \"유입\": {ID: 값}}}")
    a = ap.parse_args(argv)
    try:
        json.load(io.open(a.가정, encoding="utf-8"))
        설정 = 설정읽기(a.설정)
        덧 = json.load(io.open(a.계열, encoding="utf-8")) if a.계열 else None
    except (OSError, ValueError, KeyError) as e:
        print("입력을 읽지 못했습니다: %s" % e)
        return 입력오류
    try:
        결과 = 돌기(a.가정, 설정, 덧)
    except Exception as e:                                   # noqa: BLE001 — 기간축오류 등
        print("가정의 기간 축을 짓지 못했습니다: %s" % e)
        return 입력오류
    밖 = a.낼 or os.path.join(os.path.dirname(os.path.abspath(a.가정)), "_raw", 산출이름)
    os.makedirs(os.path.dirname(밖), exist_ok=True)
    io.open(밖, "w", encoding="utf-8").write(json.dumps(결과, ensure_ascii=False, indent=1))
    찍기(결과)
    print("→ %s" % 밖)
    return 발견 if any(s["등급"] == "경보" for s in 결과["신호"]) else 통과


if __name__ == "__main__":
    sys.exit(main())

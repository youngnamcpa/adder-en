# -*- coding: utf-8 -*-
"""조합 이례도 — 하나씩 보면 범위 안인데 셋이 함께 나타난 적이 드문 가정 조합을 잰다(마할라노비스 D² · MCD 강건 공분산).

무엇을 하나
  ① 패널 D² — 회사-5년 창의 (5년 매출 CAGR, 5년 매출가중 평균 영업이익률, 5년 영업이익률 폭) 분포를 MCD 로 잡고, 시나리오 경로의
     같은 세 값이 그 분포에서 얼마나 먼지 낸다. 비교 집단(전체 · 같은 규모 · 같은 KSIC 3자리 · 2자리) × 설정(주분석 · 겹치지 않는 창 ·
     표시 제외 · 구분 섞임 · support 0.5 · 0.9 · 시드 둘)을 다 돌려 **설정을 바꿔도 걸리는지** 본다.
  ② 자기 과거 최근접 — 예측 해마다 (매출성장률, 영업이익률)이 회사 자신의 실적 해 가운데 가장 가까운 해와 얼마나 먼가.
     키트 규칙 「서로 다른 시기에서 가져온 값을 한 시나리오에 섞으면 표시한다」를 숫자로 만든 것이다.
  값을 정하지 않는다. 판정은 χ² 가 아니라 **비교 표본 안 D² 경험 백분위**로 한다(2026-10-21 실험: 표본의 17~26% 가 χ²(0.99) 를 넘었다).
  D² 는 방향을 모르므로 변수별 강건 z · 두 변수씩 D² · **같은 쪽 꼬리 수**(D² 가 대상 이상이고 지배 변수 z 부호가 같은 관측)를 함께 낸다.

사용
  python 스크립트/조합이례도.py 가정.json [--회사 고유번호] [--낼 경로.json] [--빠르게]
  (--빠르게 = 민감도 설정을 주분석 하나로 — 시험 · 확인용)

읽는 것
  기저율.py 와 같은 공용 패널 · 설정(`기저율설정.json` 의 「조합이례도」 · 「최근접」) · 가정 파일(엔진 경로) ·
  자기 과거 = `정상화.관측시계열`(관측.대상영업이익률 → `_raw/dart_앵커시계열.json` · `_raw/앵커_시계열.json` → A3 동인원천 → 원천 13번),
  그것이 최소 해 수보다 짧으면 패널 안의 대상회사 행.
내는 것
  가정 곁 `_raw/조합이례도.json` — {형식 · 만든날 · 설정 · 입력 · 적합 · 대상 · 최근접 · 신호}.
  패널은 국가 축(2026-10-22 — 기저율.py 「국가 축」)을 따른다: 표시통화 KRW → KR · USD → US(`--국가` 로 덮는다).
  대상이 패널의 비교 대상이 아니면(표시통화 KRW · USD 아님 · 그 국가 패널 없음 · 고유번호 못 찾음) 「해당 없음」 꼴(기저율.py 와 같다)을 내고 0 으로 끝낸다.
종료 코드 — 0 통과(신호가 있어도 · 해당 없음이어도 0) · 2 입력오류(가정 깨짐 · 공용 패널 없음 · 엔진 계산 실패).
속도 — 실측(2026-10-21, 패널 22,712 회사-연도 · 전체 집단 9,183 창 · 시작 200 · 부분표본 1,500): 전체 집단 주분석 한 번 5~7초,
네 집단 × 여덟 설정 60~130초(기계 부하에 따라). `--빠르게` 는 주분석만.
표준 라이브러리만 쓴다(FastMCD 축약 — 무작위 시작 · C-step 은 부분표본에서,
상위 10개만 전체 표본에서 수렴). 회사 · 업종 이름은 이 도구에 없다.
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import math
import os
import random
import statistics
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
import 기저율 as 기  # noqa: E402
from 종료코드 import 통과, 입력오류  # noqa: E402

변수 = ("CAGR5", "평균이익률5", "이익률폭5")


# ═══════════════════════════════════════════════ 작은 선형대수

def 역행렬(A):
    """가우스-조르단. 특이하면 None."""
    n = len(A)
    M = [list(map(float, r)) + [1.0 if i == j else 0.0 for j in range(n)] for i, r in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        if abs(M[p][c]) < 1e-300:
            return None
        M[c], M[p] = M[p], M[c]
        piv = M[c][c]
        M[c] = [v / piv for v in M[c]]
        for r in range(n):
            if r != c and M[r][c] != 0.0:
                f = M[r][c]
                M[r] = [a - f * b for a, b in zip(M[r], M[c])]
    return [r[n:] for r in M]


def 로그행렬식(A):
    n = len(A)
    M = [list(map(float, r)) for r in A]
    s = 0.0
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        if abs(M[p][c]) < 1e-300:
            return -math.inf
        if p != c:
            M[c], M[p] = M[p], M[c]
        s += math.log(abs(M[c][c]))
        for r in range(c + 1, n):
            f = M[r][c] / M[c][c]
            if f:
                M[r] = [a - f * b for a, b in zip(M[r], M[c])]
    return s


def 평균공분산(X, idx):
    n = len(idx)
    p = len(X[0])
    mu = [sum(X[i][j] for i in idx) / n for j in range(p)]
    S = [[0.0] * p for _ in range(p)]
    for i in idx:
        d = [X[i][j] - mu[j] for j in range(p)]
        for a in range(p):
            for b in range(a, p):
                S[a][b] += d[a] * d[b]
    for a in range(p):
        for b in range(a, p):
            S[a][b] /= n
            S[b][a] = S[a][b]
    return mu, S


def d2(x, mu, Si):
    d = [a - b for a, b in zip(x, mu)]
    return sum(d[a] * sum(Si[a][b] * d[b] for b in range(len(d))) for a in range(len(d)))


def 전부d2(X, mu, Si):
    return [d2(x, mu, Si) for x in X]


def chi2_상위확률(x, 자유도):
    """χ² 생존함수 — 자유도 1 · 2 · 3 만(닫힌 꼴)."""
    if x is None or x < 0:
        return None
    if 자유도 == 1:
        return math.erfc(math.sqrt(x / 2))
    if 자유도 == 2:
        return math.exp(-x / 2)
    if 자유도 == 3:
        return math.erfc(math.sqrt(x / 2)) + math.sqrt(2 * x / math.pi) * math.exp(-x / 2)
    return None


def mcd(X, 비율, 시작수, 시드, 부분상한, chi2):
    """FastMCD 축약. (위치, 공분산, 재가중 표본 수). chi2 = {"0.5": …, "0.975": …}(변수 수 자유도)."""
    n, p = len(X), len(X[0])
    rng = random.Random(시드)
    전체 = list(range(n))
    부분 = 전체 if n <= 부분상한 else sorted(rng.sample(전체, 부분상한))

    def cstep(idx_pool, mu, S, 회, h):
        Si = 역행렬(S)
        if Si is None:
            return None
        ld = 로그행렬식(S)
        for t in range(회):
            d = [d2(X[i], mu, Si) for i in idx_pool]
            keep = [idx_pool[j] for j in sorted(range(len(idx_pool)), key=d.__getitem__)[:h]]
            mu2, S2 = 평균공분산(X, keep)
            ld2 = 로그행렬식(S2)
            Si2 = 역행렬(S2)
            if Si2 is None or ld2 == -math.inf:
                return mu2, S2, ld2
            if t >= 2 and abs(ld2 - ld) < 1e-10:
                return mu2, S2, ld2
            mu, S, Si, ld = mu2, S2, Si2, ld2
        return mu, S, ld

    h부 = int(math.ceil(비율 * len(부분)))
    후보 = []
    for _ in range(시작수):
        k = p + 1
        while True:
            idx = rng.sample(부분, min(k, len(부분)))
            mu, S = 평균공분산(X, idx)
            if 로그행렬식(S) > -math.inf or k >= len(부분):
                break
            k += 1
        r = cstep(부분, mu, S, 2, h부)
        if r and r[2] > -math.inf:
            후보.append(r)
    if not 후보:
        mu, S = 평균공분산(X, 전체)
        return mu, S, n
    후보.sort(key=lambda c: c[2])
    h = int(math.ceil(비율 * n))
    끝 = [cstep(전체, m, s, 100, h) for m, s, _ in 후보[:10]]
    끝 = [c for c in 끝 if c and c[2] > -math.inf]
    mu, S, _ld = min(끝, key=lambda c: c[2]) if 끝 else 후보[0]
    Si = 역행렬(S)
    d = 전부d2(X, mu, Si)
    배 = statistics.median(d) / chi2["0.5"]
    S = [[v * 배 for v in r] for r in S]
    Si = 역행렬(S)
    d = 전부d2(X, mu, Si)
    keep = [i for i in 전체 if d[i] <= chi2["0.975"]]
    if len(keep) > p:
        mu, S = 평균공분산(X, keep)
    return mu, S, len(keep)


# ═══════════════════════════════════════════════ 분석

def 창표시(조):
    """세 창 변수의 Modified Z 로 「표시_조합」 을 붙인다(지우지 않는다)."""
    thr = 3.5
    for v in 변수:
        zs = 기.mz([w[v] for w in 조])
        for w, z in zip(조, zs):
            w["MZ_" + v] = z
    for w in 조:
        w["표시_조합"] = any(w.get("MZ_" + v) is not None and abs(w["MZ_" + v]) > thr for v in 변수) or bool(w.get("표시_연도"))
    return 조


def 자기과거(가정, 가정경로, 넓은, 고, 최소):
    """[(해, 매출성장률, 영업이익률)] · 출처."""
    해들 = []
    출처 = ""
    try:
        import 정상화                                        # noqa: PLC0415
        관 = 정상화.관측시계열(가정, 가정경로)
        해들 = [x for x in 관.get("해") or [] if x.get("해") and x.get("매출") and x.get("영업이익률") is not None]
        출처 = 관.get("출처") or ""
    except Exception as e:                                   # noqa: BLE001
        출처 = "정상화.관측시계열 실패 — %s" % e
    벡 = []
    해들.sort(key=lambda x: x["해"])
    for a, b in zip(해들, 해들[1:]):
        if b["해"] == a["해"] + 1 and a["매출"] > 0:
            벡.append((b["해"], b["매출"] / a["매출"] - 1, b["영업이익률"]))
    if len(벡) < 최소 and 고 in 넓은:
        h = 넓은[고]["해"]
        벡2 = []
        for y in sorted(h):
            if y - 1 in h and h[y - 1]["매출액"] and h[y]["영업이익률"] is not None:
                벡2.append((y, h[y]["매출액"] / h[y - 1]["매출액"] - 1, h[y]["영업이익률"]))
        if len(벡2) > len(벡):
            return 벡2, "패널 안의 대상회사 행(%s 이 %d해라 짧아서)" % (출처 or "관측 시계열", len(벡))
    return 벡, 출처


def 패널척도(넓은, 고):
    gs, ms = [], []
    for c, d in 넓은.items():
        if c == 고:
            continue
        h = d["해"]
        for y, r in h.items():
            if r["영업이익률"] is not None:
                ms.append(r["영업이익률"])
            if y - 1 in h and h[y - 1]["매출액"] and h[y - 1]["재무제표구분"] == r["재무제표구분"]:
                gs.append(r["매출액"] / h[y - 1]["매출액"] - 1)

    def rsd(v):
        med = statistics.median(v)
        return statistics.median([abs(x - med) for x in v]) * 1.4826
    return (rsd(gs) if gs else None), (rsd(ms) if ms else None)


def 분석(가정, 가정경로, 설정=None, 회사=None, 빠르게=False, 자리=None, 국가=None):
    설정 = 설정 or 기.설정읽기()
    C = 설정["조합이례도"]
    국, 설정, 까 = 기.국가맞춤(가정, 설정, 국가)          # 국가 축(2026-10-22) — KRW → KR · USD → US 패널 · 설정 덮기
    if not 국:
        return 기.해당없음("조합이례도 1", 가정경로, 까, 설정, "조합이례도"), ""
    행, 패널입력 = 기.패널읽기(자리, 설정)
    if not 행:
        if 국 != "KR":
            return 기.해당없음("조합이례도 1", 가정경로, "%s 패널이 비었다(%s) — `기저율.py --받기 --국가 %s` 를 먼저"
                           % (국, 패널입력["자리"], 국), 설정, "조합이례도"), ""
        return None, "공용 패널이 비었다(%s) — `기저율.py --받기` 또는 `--씨앗` 을 먼저" % 패널입력["자리"]
    고, 산업, 까 = 기.대상찾기(가정, 가정경로, 행, 회사, 설정)
    if not 고:
        return 기.해당없음("조합이례도 1", 가정경로, 까, 설정, "조합이례도"), ""
    남, _뺀 = 기.자료제외(행, 설정)
    기.이익률표시(남, 설정)
    넓은 = 기.넓히기(남)
    길, 엔진오류 = 기.경로(가정)
    if not 길:
        return None, "엔진이 가정을 계산하지 못했다 — %s" % " / ".join(엔진오류)
    첫 = next(iter(길.values()))
    마실, 첫예 = 첫["마지막실적해"], 첫["첫예측해"]
    배율 = 기._수((가정.get("메타") or {}).get("환산배율")) or 1.0
    기준매출 = ((넓은.get(고) or {}).get("해", {}).get(마실) or {}).get("매출액")
    if 기준매출 is None and 마실 in 첫["해"]:
        기준매출 = 첫["해"][마실]["매출"] * 배율
    대상 = {"KSIC3": 산업[:3] if 산업 and len(산업) >= 3 else None, "KSIC2": 산업[:2] if 산업 and len(산업) >= 2 else None,
          "규모구간": 기.규모구간(기준매출, 설정)}
    집 = 기.집단들(대상, 설정)
    조 = 창표시(기.조합창(넓은, 설정))
    자기창 = [w for w in 조 if w["고유번호"] == 고]
    W = [w for w in 조 if w["고유번호"] != 고]
    t0들 = sorted({w["t0"] for w in W})
    겹안 = {t0들[0], t0들[0] + 5} if t0들 else set()
    후보 = []
    for 시, 경 in 길.items():
        for 창이름, t0 in (("마지막 실적 해 시작", 마실), ("첫 예측 해 시작", 첫예)):
            if t0 is None:
                continue
            v = 기.경로벡터(경["해"], t0)
            if all(v.get(k) is not None for k in 변수):
                후보.append(("%s %d→%d" % (시, t0, t0 + 5), 시, 창이름, [v[k] for k in 변수]))
    for w in 자기창:
        후보.append(("자기 과거 t0=%d" % w["t0"], "자기 과거", "실적", [w[k] for k in 변수]))
    민감 = C["민감도"][:1] if 빠르게 else C["민감도"]
    chi2 = C["chi2_자유도3"]
    문턱 = C["경험백분위_문턱"]
    최소 = C["최소관측"]
    적합, 줄들 = [], []
    시작 = time.time()
    for s in 민감:
        비율 = s.get("support_fraction", C["support_fraction"])
        시드 = s.get("시드", C["시드"])
        for 이름, f in 집:
            g = [w for w in W if f(w)
                 and (s.get("구분섞임포함") or w["같은구분"])
                 and (not s.get("겹치지않는창") or w["t0"] in 겹안)
                 and (not s.get("표시제외") or not w["표시_조합"])]
            if len(g) < max(최소, 5 * len(변수)):
                적합.append({"설정": s["이름"], "집단": 이름, "관측수": len(g), "비고": "표본 부족"})
                continue
            X = [[w[k] for k in 변수] for w in g]
            t1 = time.time()
            mu, S, nrw = mcd(X, 비율, C["무작위시작_수"], 시드, C["부분표본_상한"], chi2)
            Si = 역행렬(S)
            if Si is None:
                적합.append({"설정": s["이름"], "집단": 이름, "관측수": len(g), "비고": "공분산 특이"})
                continue
            sd = [math.sqrt(S[j][j]) for j in range(len(변수))]
            dd = 전부d2(X, mu, Si)
            Z = [[(x[j] - mu[j]) / sd[j] for j in range(len(변수))] for x in X]
            적합.append({"설정": s["이름"], "집단": 이름, "관측수": len(g), "회사수": len({w["고유번호"] for w in g}),
                        "재가중표본": nrw, "위치": dict(zip(변수, mu)), "강건표준편차": dict(zip(변수, sd)),
                        "chi2_0.99_넘는비중": sum(1 for v in dd if v > chi2["0.99"]) / len(dd), "초": round(time.time() - t1, 2)})
            for 라벨, 시, 창이름, x in 후보:
                D2 = d2(x, mu, Si)
                z = [(x[j] - mu[j]) / sd[j] for j in range(len(변수))]
                주변 = max(range(len(변수)), key=lambda j: abs(z[j]))
                쌍 = {}
                for a in range(len(변수)):
                    for b in range(a + 1, len(변수)):
                        sub = [[S[a][a], S[a][b]], [S[b][a], S[b][b]]]
                        si = 역행렬(sub)
                        쌍["%s×%s" % (변수[a], 변수[b])] = d2([x[a], x[b]], [mu[a], mu[b]], si) if si else None
                같은쪽 = sum(1 for v, zz in zip(dd, Z) if v >= D2 and (zz[주변] > 0) == (z[주변] > 0))
                줄들.append({"설정": s["이름"], "집단": 이름, "관측수": len(g), "대상": 라벨, "시나리오": 시, "창": 창이름,
                           "값": dict(zip(변수, x)), "z": dict(zip(변수, z)), "지배변수": 변수[주변], "D2": D2,
                           "경험백분위": sum(1 for v in dd if v < D2) / len(dd), "D2이상_관측": sum(1 for v in dd if v >= D2),
                           "같은쪽꼬리": 같은쪽, "chi2_상위확률": chi2_상위확률(D2, len(변수)), "쌍별D2": 쌍,
                           "문턱넘음": sum(1 for v in dd if v < D2) / len(dd) >= 문턱})
    걸린초 = round(time.time() - 시작, 1)

    # ② 자기 과거 최근접
    N = 설정["최근접"]
    벡, 출처 = 자기과거(가정, 가정경로, 넓은, 고, N["최소_실적해"])
    sg, sm = 패널척도(넓은, 고)
    최근접 = []
    if len(벡) >= N["최소_실적해"] and sg and sm:
        for 시, 경 in 길.items():
            해 = 경["해"]
            for y in sorted(해):
                h = 해[y]
                if not h["예측포함"] or y - 1 not in 해 or not 해[y - 1]["매출"] or h["영업이익률"] is None:
                    continue
                g = h["매출"] / 해[y - 1]["매출"] - 1
                m = h["영업이익률"]
                거, 해0 = min((math.sqrt(((g - gy) / sg) ** 2 + ((m - my) / sm) ** 2), yy) for yy, gy, my in 벡)
                최근접.append({"시나리오": 시, "연도": y, "실적섞임": bool(h.get("실적섞임")),
                            "매출성장률": g, "영업이익률": m, "가장가까운실적해": 해0, "거리": 거, "문턱넘음": 거 > N["거리_문턱"]})

    # ③ 신호
    신호 = []

    def 신(종류, 대상글, 값, 문턱글, 글, 등급="경보"):
        신호.append({"출처": "조합이례도", "종류": 종류, "대상": 대상글, "값": 값, "문턱": 문턱글, "글": 글, "등급": 등급})

    주 = [x for x in 줄들 if x["설정"] == "주분석" and x["시나리오"] != "자기 과거"]
    for 라벨 in sorted({x["대상"] for x in 주}):
        a = [x for x in 주 if x["대상"] == 라벨]
        걸 = [x for x in a if x["문턱넘음"]]
        if 걸:
            x0 = max(걸, key=lambda x: x["경험백분위"])
            자기 = [x for x in 줄들 if x["설정"] == "주분석" and x["시나리오"] == "자기 과거" and x["집단"] == x0["집단"]]
            자기말 = (" · 대상회사 자기 과거 창의 D² 는 %.0f~%.0f" % (min(x["D2"] for x in 자기), max(x["D2"] for x in 자기))) if 자기 else ""
            경보 = len(걸) >= min(2, len({x["집단"] for x in a}))      # 2026-10-23 밤 — 비교 집단 둘 이상에서 넘을 때만 경보(한 집단만이면 참고 · 03 4-6)
            신("조합 이례", 라벨, round(x0["D2"], 1), "경험 백분위 ≥ %.0f%% · 경보는 비교 집단 둘 이상" % (문턱 * 100),
              "%s 의 (5년 CAGR · 평균 이익률 · 이익률 폭) 조합이 %s 에서 백분위 %s — 지배 변수는 %s(z %.1f) · 같은 쪽 꼬리 %d건%s. "
              "그 변수의 근거를 적는다%s" % (라벨, " · ".join(x["집단"] for x in 걸), " · ".join("%.1f%%" % (x["경험백분위"] * 100) for x in 걸),
                                      x0["지배변수"], x0["z"][x0["지배변수"]], x0["같은쪽꼬리"], 자기말, "" if 경보 else " · 한 집단에서만 넘어 참고로 둔다"),
              "경보" if 경보 else "참고")
        # 같은 비교 집단 안에서 설정만 바꿨을 때 판정이 뒤집히는가(강의 원칙 — 설정을 바꿔도 걸리는 것이 진짜다)
        갈린집단 = []
        for 이름, _f in 집:
            전 = [x for x in 줄들 if x["대상"] == 라벨 and x["집단"] == 이름]
            if len({x["문턱넘음"] for x in 전}) == 2:
                갈린집단.append("%s(%d설정 중 %d)" % (이름, len(전), sum(1 for x in 전 if x["문턱넘음"])))
        if 갈린집단:
            신("설정에 따라 갈림", 라벨, None, "민감도 %d설정" % len(민감),
              "%s 의 조합 이례 판정이 같은 비교 집단 안에서 설정만 바꿔도 뒤집힌다 — %s. 그 집단의 판정은 결론으로 쓰지 않고 갈린 설정을 함께 적는다"
              % (라벨, " · ".join(갈린집단)), "참고")
    # 자기 과거 밖 — 시나리오 · 연도마다 한 줄이던 것을 같은 해 묶음끼리 한 줄로(2026-10-23 밤 · 03 4-6 — 같은 뿌리를 반복 세지 않는다)
    밖 = {}
    for x in 최근접:
        if x["문턱넘음"]:
            밖.setdefault(x["시나리오"], []).append(x)
    해묶 = {}
    for 시, xs in 밖.items():
        해묶.setdefault(tuple(sorted(x["연도"] for x in xs)), []).append(시)
    for 해들, 시들 in 해묶.items():
        xs = [x for 시 in 시들 for x in 밖[시]]
        x0 = max(xs, key=lambda x: x["거리"])
        시말 = ("%s 모두" % " · ".join(시들)) if len(시들) == len(밖) == 3 else " · ".join(시들)
        신("자기 과거 밖 조합", "%s %s" % (시말, " · ".join("%d" % y for y in 해들)), round(x0["거리"], 2), N["거리_문턱"],
          "%s 시나리오의 %s년 (가장 먼 해: %s %d년%s — 매출성장률 %.1f%% · 영업이익률 %.1f%%) 은 회사 자신의 실적 해 가운데 가장 가까운 %d년에서도 강건 표준편차 %.1f개만큼 "
          "멀다 — 함께 나타난 적이 없는 조합이면 그 이유를 세계 서술에 적는다"
          % (시말, " · ".join("%d" % y for y in 해들), x0["시나리오"], x0["연도"], "(실적 열이 섞인 해)" if x0.get("실적섞임") else "",
             x0["매출성장률"] * 100, x0["영업이익률"] * 100, x0["가장가까운실적해"], x0["거리"]))
    for f in 적합:
        if f.get("비고") == "표본 부족" and f["설정"] == "주분석":
            신("표본 부족", f["집단"], f["관측수"], 최소, "%s 의 5년 창이 %d개라 조합 이례도를 재지 않았다" % (f["집단"], f["관측수"]), "참고")
    if len(벡) < N["최소_실적해"]:
        신("자기 과거 부족", "최근접", len(벡), N["최소_실적해"], "회사 자신의 실적 해가 %d개라 최근접 거리를 재지 않았다(%s)" % (len(벡), 출처), "참고")

    낸 = {"형식": "조합이례도 1", "만든날": datetime.date.today().isoformat(),
          "설정": {"조합이례도": C, "최근접": N, "민감도_돈것": [s["이름"] for s in 민감]},
          "입력": {"가정": os.path.abspath(가정경로), "패널자리": 패널입력["자리"], "패널연도": 패널입력["연도"], "회사": 고,
                 "산업분류": 산업, "자기과거_출처": 출처, "척도": {"매출성장률": sg, "영업이익률": sm}, "걸린초": 걸린초},
          "적합": 적합, "대상": 줄들, "최근접": 최근접, "신호": 신호}
    return 낸, ""


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="조합 이례도 — 가정 조합이 같은 집단 · 자기 과거에서 얼마나 드문가")
    ap.add_argument("가정")
    ap.add_argument("--회사")
    ap.add_argument("--낼")
    ap.add_argument("--빠르게", action="store_true", help="민감도 설정을 주분석 하나로")
    ap.add_argument("--설정")
    ap.add_argument("--국가", help="패널 국가(KR · US) — 기본은 가정 메타.표시통화가 고른다(KRW → KR · USD → US)")
    a = ap.parse_args()
    try:
        가정 = json.load(io.open(a.가정, encoding="utf-8"))
    except (OSError, ValueError) as e:
        print("가정 파일을 못 읽었다 — %s" % e)
        return 입력오류
    낸, 까 = 분석(가정, a.가정, 기.설정읽기(a.설정), a.회사, a.빠르게, 국가=a.국가)
    if 낸 is None:
        print("입력오류 — %s" % 까)
        return 입력오류
    p = a.낼 or os.path.join(os.path.dirname(os.path.abspath(a.가정)), "_raw", "조합이례도.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, "w", encoding="utf-8").write(json.dumps(낸, ensure_ascii=False, indent=1, default=str))
    if 낸.get("해당없음"):
        print("조합 이례도 — 해당 없음: %s\n→ %s" % (낸["해당없음"], p))
        return 통과
    print("조합 이례도 — 적합 %d · 대상 줄 %d · 최근접 %d · 신호 %d · %.1f초"
          % (len(낸["적합"]), len(낸["대상"]), len(낸["최근접"]), len(낸["신호"]), 낸["입력"]["걸린초"]))
    for s in 낸["신호"]:
        print("   · [%s] %s — %s" % (s["등급"], s["종류"], s["글"]))
    print("→ %s" % p)
    return 통과


if __name__ == "__main__":
    sys.exit(main())

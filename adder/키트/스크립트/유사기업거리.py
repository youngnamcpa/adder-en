# -*- coding: utf-8 -*-
"""유사기업거리 — C2 재료 표에서 대상회사와 후보마다 규모 · 성장 · 수익성 · 부채 조합이 얼마나 먼지 강건한 거리로 잰다 (2026-10-21).

    python 스크립트/유사기업거리.py 가정.json                          # 가정 곁 _raw/peers/유사기업_재료_*.csv 가운데 가장 최근
    python 스크립트/유사기업거리.py 가정.json --재료 유사기업_재료_핵심.csv

왜 있나
    후보 하나하나를 규모대 · 매출 로그거리처럼 변수 하나씩으로만 보면, 변수마다는 범위 안인데 조합이 대상과 동떨어진 후보를 못 본다.
    이 도구는 **재료 열 하나**(거리 · 순위 · 변수별 z)를 더할 뿐 **선정하지 않는다** — 먼 후보는 「규모대 · 사업 접점의 근거를 적으라」는
    참고 신호다. 변수 넷(시가총액 · 매출 CAGR · 영업이익률 · D/E)은 결과(βU · 상관 · 수익률)가 아니라 회사의 속성이다.

방법
    기본 — 변수마다 후보(대상 제외)의 중앙값 · MAD(× 1.4826)로 척도를 잡고, 대상과의 차이를 z 로 바꿔 유클리드 거리(√Σz²)를 낸다.
           한 회사라도 비었거나 확인 불가인 변수는 그 회사에서만 빼고 몇 변수로 쟀는지 적는다(`쓴변수수`). 비교용 RMS(√(Σz² ÷ 쓴변수수))도 낸다.
    MCD  — 모든 변수가 찬 후보가 `MCD_최소배수` × 변수 수 이상이면 이 파일 안의 작은 MCD(FastMCD 축약 — 무작위 시작 + C-step ·
           일치성 보정 · χ²(0.975) 재가중, 표준 라이브러리)로 강건 공분산을 세우고 대상과의 마할라노비스 거리 √((x − 대상)ᵀ Σ⁻¹ (x − 대상))
           를 낸다. 순위는 쓴 방식의 거리로 매기고, 변수가 덜 찬 후보는 순위 없이 유클리드만 싣는다.
    먼 후보 — 거리² 가 χ²(자유도 = 쓴 변수 수)의 0.975 분위(Wilson-Hilferty 근사)를 넘으면 참고 신호. 문턱 · 시드 · 변수는 `조항설정.json`
           「유사기업거리」(결과를 보기 전에 정했다).

읽는 것
    `_raw/peers/유사기업_재료_{표본}.csv` — `peer_조립.py` 산출. 대상회사 참고행(`경로` 가 「-」 이거나 `회사명` 이 「(대상)」 으로 끝남).
        열: `시가총액` · `매출CAGR{n}y` · `영업이익률_{연도}`(가장 늦은 해) · `DE`
    `_raw/peers/핵심표본.json` — 있으면 후보의 구분(핵심 · 예비)을 붙인다

내는 것
    `_raw/peers/유사기업거리.json` {"형식": "유사기업거리 1", "만든날", "설정", "입력", "대상", "방식", "척도", "후보": [...], "신호": [...]}
    `_raw/peers/유사기업거리.csv`  고유번호 · 종목코드 · 회사명 · 구분 · 거리 · 순위 · 방식 · 쓴변수수 · z_{변수} · 거리_유클리드 ·
                                   거리_RMS · 거리_마할라노비스 · 상태
    신호 종류 — 「먼 후보」(참고) · 「변수 부족」(참고)

종료 코드 — 0 통과(먼 후보는 참고 신호라 rc 에 들지 않는다) · 2 입력오류(가정 · 재료 표 · 대상 참고행 없음 · 변수 부족).
회사 · 업종 이름은 이 도구에 한 글자도 없다.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import glob
import io
import json
import math
import os
import random
import re
import statistics
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                            # noqa: BLE001
    pass

여기 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, 여기)
from 종료코드 import 통과, 입력오류  # noqa: E402

기본설정 = os.path.join(여기, "조항설정.json")


def 설정읽기(p=None):
    return json.load(io.open(p or 기본설정, encoding="utf-8"))["유사기업거리"]


def _f(v):
    try:
        s = str(v).replace(",", "").strip()
        if s in ("", "None", "nan", "NaN", "확인 불가", "-"):
            return None
        x = float(s)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


# ── χ² 분위(Wilson-Hilferty) ──────────────────────────────────────────────
_z = {0.5: 0.0, 0.975: 1.959963985}


def 카이분위(확률, k):
    z = _z[확률]
    a = 2.0 / (9.0 * k)
    return k * (1.0 - a + z * math.sqrt(a)) ** 3


# ── 작은 선형대수 ─────────────────────────────────────────────────────────
def 평균(X):
    n = len(X)
    return [sum(r[j] for r in X) / n for j in range(len(X[0]))]


def 공분산(X):
    n, p = len(X), len(X[0])
    m = 평균(X)
    S = [[0.0] * p for _ in range(p)]
    for r in X:
        d = [r[j] - m[j] for j in range(p)]
        for a in range(p):
            for b in range(a, p):
                S[a][b] += d[a] * d[b]
    for a in range(p):
        for b in range(a, p):
            S[a][b] /= n
            S[b][a] = S[a][b]
    return m, S


def 역행렬(A):
    p = len(A)
    M = [list(map(float, A[i])) + [1.0 if i == j else 0.0 for j in range(p)] for i in range(p)]
    for c in range(p):
        piv = max(range(c, p), key=lambda r: abs(M[r][c]))
        if abs(M[piv][c]) < 1e-14:
            return None
        M[c], M[piv] = M[piv], M[c]
        v = M[c][c]
        M[c] = [x / v for x in M[c]]
        for r in range(p):
            if r != c and M[r][c]:
                f = M[r][c]
                M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    return [row[p:] for row in M]


def 로그행렬식(A):
    p = len(A)
    M = [list(map(float, r)) for r in A]
    s = 0.0
    for c in range(p):
        piv = max(range(c, p), key=lambda r: abs(M[r][c]))
        if abs(M[piv][c]) < 1e-300:
            return -float("inf")
        M[c], M[piv] = M[piv], M[c]
        s += math.log(abs(M[c][c]))
        for r in range(c + 1, p):
            f = M[r][c] / M[c][c]
            if f:
                M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    return s


def 마할(x, m, Si):
    d = [a - b for a, b in zip(x, m)]
    return sum(d[i] * sum(Si[i][j] * d[j] for j in range(len(d))) for i in range(len(d)))


def mcd(X, frac=0.75, 시작수=200, 시드=42):
    """FastMCD 축약판(표준 라이브러리) → (위치, 공분산) 또는 None(특이)."""
    n, p = len(X), len(X[0])
    h = int(math.ceil(frac * n))
    rnd = random.Random(시드)

    def cstep(m, S, 회):
        Si = 역행렬(S)
        if Si is None:
            return None
        ld = 로그행렬식(S)
        for k in range(회):
            d = sorted(range(n), key=lambda i: 마할(X[i], m, Si))[:h]
            m2, S2 = 공분산([X[i] for i in d])
            Si2 = 역행렬(S2)
            if Si2 is None:
                return None
            ld2 = 로그행렬식(S2)
            m, S, Si = m2, S2, Si2
            if 회 > 2 and abs(ld2 - ld) < 1e-10:
                return m, S, ld2
            ld = ld2
        return m, S, ld

    후 = []
    for _ in range(시작수):
        k = p + 1
        while k <= n:
            idx = rnd.sample(range(n), k)
            m, S = 공분산([X[i] for i in idx])
            if 역행렬(S) is not None:
                break
            k += 1
        else:
            continue
        r = cstep(m, S, 2)
        if r:
            후.append(r)
    if not 후:
        return None
    후.sort(key=lambda t: t[2])
    best = None
    for m, S, _ in 후[:10]:
        r = cstep(m, S, 100)
        if r and (best is None or r[2] < best[2]):
            best = r
    if not best:
        return None
    m, S, _ = best
    Si = 역행렬(S)
    d = [마할(x, m, Si) for x in X]
    c = statistics.median(d) / 카이분위(0.5, p)
    if c > 0:
        S = [[v * c for v in row] for row in S]
    Si = 역행렬(S)
    if Si is None:
        return None
    안 = [x for x in X if 마할(x, m, Si) <= 카이분위(0.975, p)]
    if len(안) > p:
        m, S = 공분산(안)
    return (m, S) if 역행렬(S) is not None else None


# ── 재료 표 ───────────────────────────────────────────────────────────────
def 재료고르기(peers, 지정=None):
    if 지정:
        p = 지정 if os.path.isabs(지정) or os.path.exists(지정) else os.path.join(peers, 지정)
        return p if os.path.exists(p) else None
    후 = glob.glob(os.path.join(peers, "유사기업_재료_*.csv")) + glob.glob(os.path.join(peers, "유사기업_재료.csv"))
    return max(후, key=os.path.getmtime) if 후 else None


def 열고르기(머리, 변수):
    if 변수.get("열"):
        return 변수["열"] if 변수["열"] in 머리 else None
    식 = re.compile(변수["열꼴"])
    맞 = [(c, 식.match(c)) for c in 머리 if 식.match(c)]
    if not 맞:
        return None

    def 키(t):
        g = t[1].groups()
        return int(g[0]) if g and g[0] and g[0].isdigit() else 0
    return max(맞, key=키)[0]


def 대상인가(r):
    return (r.get("경로") or "").strip() == "-" or (r.get("회사명") or "").strip().endswith("(대상)")


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="유사기업 후보와 대상의 강건 거리 — 선정하지 않는다")
    ap.add_argument("가정")
    ap.add_argument("--재료", default=None)
    ap.add_argument("--설정", default=None)
    a = ap.parse_args(argv)
    if not os.path.exists(a.가정):
        print("가정 파일이 없다: %s" % a.가정)
        return 입력오류
    try:
        S = 설정읽기(a.설정)
    except (ValueError, IOError, OSError, KeyError) as e:
        print("설정을 못 읽었다 — %s" % e)
        return 입력오류
    방 = os.path.dirname(os.path.abspath(a.가정))
    peers = os.path.join(방, "_raw", "peers")
    p = 재료고르기(peers, a.재료)
    if not p:
        print("C2 재료 표가 없다 — %s 에 유사기업_재료_*.csv(peer_조립.py) 가 필요하다" % peers)
        return 입력오류
    rows = list(csv.DictReader(io.open(p, encoding="utf-8-sig")))
    if not rows:
        print("재료 표가 비었다: %s" % p)
        return 입력오류
    머리 = list(rows[0].keys())
    t = [r for r in rows if 대상인가(r)]
    if not t:
        print("대상회사 참고행이 없다(경로 「-」 · 회사명 「(대상)」) — peer_조립.py 산출이 맞는지 본다")
        return 입력오류
    t = t[0]
    후보 = [r for r in rows if not 대상인가(r)]
    구분표 = {}
    kp = os.path.join(peers, "핵심표본.json")
    if os.path.exists(kp):
        try:
            k = json.load(io.open(kp, encoding="utf-8"))
            for 구 in ("핵심", "예비"):
                for c in k.get(구) or []:
                    for 키 in ("고유번호", "종목코드"):
                        if c.get(키):
                            구분표[str(c[키]).strip()] = 구
        except ValueError:
            pass

    변수 = []
    for v in S["변수"]:
        c = 열고르기(머리, v)
        변수.append(dict(v, 실제열=c))

    def 값(r, v):
        if not v["실제열"]:
            return None
        x = _f(r.get(v["실제열"]))
        if x is not None and v.get("변환") == "로그":
            x = math.log(x) if x > 0 else None
        return x

    척도, 쓸 = {}, []
    for v in 변수:
        tv = 값(t, v)
        xs = [x for x in (값(r, v) for r in 후보) if x is not None]
        if v["실제열"] is None:
            척도[v["이름"]] = {"상태": "열 없음"}
            continue
        if tv is None:
            척도[v["이름"]] = {"열": v["실제열"], "상태": "대상 값 없음 — 이 변수는 거리에서 뺀다"}
            continue
        if len(xs) < 3:
            척도[v["이름"]] = {"열": v["실제열"], "상태": "후보 값 3개 미만"}
            continue
        med = statistics.median(xs)
        s = 1.4826 * statistics.median([abs(x - med) for x in xs])
        how = "MAD"
        if s <= 0:
            s, how = statistics.pstdev(xs), "표준편차(MAD 0)"
        if s <= 0:
            척도[v["이름"]] = {"열": v["실제열"], "상태": "척도 0 — 뺀다"}
            continue
        척도[v["이름"]] = {"열": v["실제열"], "중앙값": med, "척도": s, "척도방식": how, "대상값": tv, "후보수": len(xs)}
        쓸.append(v)

    k = len(쓸)
    if k < S["최소변수"]:
        print("쓸 수 있는 변수가 %d개 — 최소 %d개가 필요하다(%s)" % (k, S["최소변수"], 척도))
        return 입력오류
    out = []
    for r in 후보:
        z = {}
        for v in 쓸:
            x = 값(r, v)
            if x is not None:
                c = 척도[v["이름"]]
                z[v["이름"]] = (x - c["대상값"]) / c["척도"]
        e = {"고유번호": r.get("고유번호") or "", "종목코드": r.get("종목코드") or "", "회사명": r.get("회사명") or "",
             "구분": 구분표.get((r.get("고유번호") or "").strip()) or 구분표.get((r.get("종목코드") or "").strip()) or "",
             "쓴변수수": len(z), "_z": z, "_x": [값(r, v) for v in 쓸]}
        for v in 변수:
            e["z_" + v["이름"]] = round(z[v["이름"]], 4) if v["이름"] in z else None
        if len(z) >= S["최소변수"]:
            ss = sum(x * x for x in z.values())
            e["거리_유클리드"] = round(math.sqrt(ss), 4)
            e["거리_RMS"] = round(math.sqrt(ss / len(z)), 4)
            e["_ss"] = ss
            e["상태"] = "잰" if len(z) == k else "변수 일부(%d/%d)" % (len(z), k)
        else:
            e["거리_유클리드"] = e["거리_RMS"] = None
            e["상태"] = "변수 부족"
        out.append(e)

    full = [e for e in out if e["쓴변수수"] == k and None not in e["_x"]]
    방식, 적합 = "MAD 유클리드", None
    if len(full) >= S["MCD_최소배수"] * k:
        적합 = mcd([e["_x"] for e in full], S["support_fraction"], S["무작위시작"], S["시드"])
        if 적합:
            방식 = "MCD 마할라노비스"
    tx = [척도[v["이름"]]["대상값"] for v in 쓸]
    if 적합:
        Si = 역행렬(적합[1])
        for e in full:
            d2 = 마할(e["_x"], tx, Si)
            e["거리_마할라노비스"] = round(math.sqrt(max(d2, 0.0)), 4)
            e["_d2"] = d2
    for e in out:
        e.setdefault("거리_마할라노비스", None)
        e["방식"] = 방식 if (적합 and "_d2" in e) else ("MAD 유클리드" if e["거리_유클리드"] is not None else "")
        e["거리"] = e["거리_마할라노비스"] if (적합 and "_d2" in e) else (e["거리_유클리드"] if not 적합 else None)
    순 = [e for e in out if e["거리"] is not None]
    순.sort(key=lambda e: e["거리"])
    for i, e in enumerate(순, 1):
        e["순위"] = i
    for e in out:
        e.setdefault("순위", None)

    신호 = []
    for e in out:
        d2 = e.get("_d2") if 적합 and "_d2" in e else e.get("_ss")
        kk = k if (적합 and "_d2" in e) else e["쓴변수수"]
        if d2 is None or kk < 1:
            continue
        문 = 카이분위(0.975, kk)
        if d2 > 문:
            큰 = max(e["_z"].items(), key=lambda t: abs(t[1])) if e["_z"] else ("", 0)
            신호.append({"출처": "유사기업거리", "종류": "먼 후보", "대상": e["회사명"] or e["고유번호"],
                       "값": round(math.sqrt(d2), 3), "문턱": round(math.sqrt(문), 3),
                       "글": "%s%s 의 규모 · 성장 · 수익성 · 부채 조합이 대상과 멀다(%s 거리 %.2f > 문턱 %.2f · 가장 큰 차이 %s z %.1f) — "
                             "빼라는 뜻이 아니다. 규모대 · 사업 접점의 근거를 핵심표본에 적는다"
                             % (e["회사명"] or e["고유번호"], "(%s)" % e["구분"] if e["구분"] else "", e["방식"],
                                math.sqrt(d2), math.sqrt(문), 큰[0], 큰[1]),
                       "등급": "참고"})
    부족 = [e for e in out if e["상태"] == "변수 부족"]
    if 부족:
        신호.append({"출처": "유사기업거리", "종류": "변수 부족", "대상": "후보 %d곳" % len(부족), "값": len(부족),
                   "문턱": "변수 %d개 이상" % S["최소변수"],
                   "글": "후보 %d곳(%s)은 재료 표의 변수가 %d개 미만이라 거리를 못 쟀다 — 재료(시가총액 · 매출 · 영업이익 · D/E)를 채운 뒤 다시 돌린다"
                         % (len(부족), ", ".join((e["회사명"] or e["고유번호"]) for e in 부족[:5]), S["최소변수"]),
                   "등급": "참고"})

    for e in out:
        for kx in ("_z", "_x", "_ss", "_d2"):
            e.pop(kx, None)
    대상 = {"회사명": t.get("회사명"), "고유번호": t.get("고유번호"), "종목코드": t.get("종목코드"),
          "값": {v["이름"]: 척도[v["이름"]]["대상값"] for v in 쓸}}
    결과 = {"형식": "유사기업거리 1", "만든날": datetime.date.today().isoformat(), "설정": S,
          "입력": {"재료": os.path.basename(p), "열": {v["이름"]: v["실제열"] for v in 변수},
                 "핵심표본": os.path.basename(kp) if os.path.exists(kp) else None},
          "대상": 대상, "방식": 방식, "척도": 척도, "후보": out, "신호": 신호}
    io.open(os.path.join(peers, "유사기업거리.json"), "w", encoding="utf-8").write(json.dumps(결과, ensure_ascii=False, indent=1))
    cols = (["고유번호", "종목코드", "회사명", "구분", "거리", "순위", "방식", "쓴변수수"] + ["z_" + v["이름"] for v in 변수]
            + ["거리_유클리드", "거리_RMS", "거리_마할라노비스", "상태"])
    with io.open(os.path.join(peers, "유사기업거리.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for e in sorted(out, key=lambda e: (e["순위"] is None, e["순위"] or 0)):
            w.writerow(e)
    print("후보 %d곳 — %s · 변수 %d(%s) · 먼 후보 %d (선정하지 않는다)"
          % (len(out), 방식, k, " · ".join("%s=%s" % (v["이름"], v["실제열"]) for v in 쓸),
             sum(1 for s in 신호 if s["종류"] == "먼 후보")))
    print("→ %s" % os.path.join(peers, "유사기업거리.json"))
    return 통과


if __name__ == "__main__":
    sys.exit(main())

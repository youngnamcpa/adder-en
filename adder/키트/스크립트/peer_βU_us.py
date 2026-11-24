# -*- coding: utf-8 -*-
"""미국 유사기업 관측 재료 표 — βU(개별)·D/E·**현금보정**·세 방식·성장·수익성·PER·PBR (캐시 전용, 네트워크 0).

왜 이 파일이 있나 (세일즈포스 회차 2026-09-13 · 세3)
  `peer_조립_us.py` 는 βL·잔차상관·시가총액까지만 내고 βU·D/E·성장성·현금보정 칸이 없었다
  (국내 `peer_조립.py` 에는 βU 가 있다). 그래서 C2 가 `_raw/peers/C2_조립_βU.py` 를 손으로 만들었고,
  **현금보정은 아무 도구에도 없어 통째로 빠졌다** — 검증 V1(H9)이 잡아 βU 가 1.0841 → 1.1485,
  주당가치 130.75 → 126.38 달러로 바뀌었다. 그 두 회차 스크립트를 이 파일과 `현금보정.py` 로 흡수했다.

규칙 (베타 입력 규칙 · 이자부부채 판정 규칙)
  · 무차입화는 개별로: βU = βL ÷ [1 + (1−t)·D/E], E = 시가총액, D = 차입금(확정 > 자동).
  · **현금보정도 개별로**: βU(보정) = βU ÷ (1 − (현금+단기투자) ÷ (시가총액 + D)) 한 뒤 중앙값.
  · 세 방식을 전부 낸다 — (a) 평균 βL ÷ [1+(1−t)·평균 D/E] · (b) 개별 βU 중앙값(**기본값**) · (c) 평균.
    보정 전·후 둘 다. 참고로 「중앙값 βU ÷ (1 − 중앙값 현금비중)」도 병기(다른 방식 병기는 좋다).
  · 벌어짐을 만드는 회사를 위·아래 각 둘 지목, 세 값이 0.01 안에 모이면 그 사실을 적는다.
  · 핵심/예비 구분·미래사업 슬롯은 `핵심표본.json` 에서 읽는다. 핵심·전체를 나란히, 미래사업 슬롯이
    있으면 포함/제외를 나란히(차이 0.15 초과면 경보).
  · 담보부 차입(창고금융)을 넣은 회사는 제외 대조 βU 를 병기한다(XYZ 실측).
  · **세율 기본값 없음**(HWO-26). 산출물은 관측 재료 표다 — 재차입·Ke 는 3단계 본선 소유.

**본값 규칙(2026-10-17, S7-03 · 06 · 07 · 17 — `βU본값.py` 가 정본, 국내 조립기 · 병합 조립기와 같은 규칙)**
  · 본값에서 빼는 회사 — ★주석 큐(차입 미확정) · 차입 미포착 · 캡티브 의심(D ÷ 부채총계 < 5% · 부채 ÷ 자산 > 50%) · 시가총액 없음 ·
    현금비중 ≥ 50% · 결정계수 < 0.10 · 표본 < 156주. **빼도 표에서 지우지 않고 「포함 시 값」을 나란히 낸다.** 주석으로 확정되면 들어간다
  · 회사별 세율(`--세율표` {티커: 세율} — 없으면 `--세율`) · D/E · 현금은 **회귀 창 연차 기말 점 평균**(companyfacts 의 그 날 차입
    · 현금 · 주식수와 주봉 종가로 E 를 다시 세운다) · D/E ≥ 2 면 부채베타(βD = 합성등급 스프레드 ÷ ERP — 이자보상배율은 companyfacts
    영업이익 ÷ 이자비용) · βL 표준오차 · 중앙값 부트스트랩 95% 구간 · 3년 창 대안(조립 csv 의 `베타_3년`)
  · 다모다란 산업 βU 대조 — `--대상거래소티커`(예: NasdaqGS:TSLA, 없으면 `--대상` 티커로 매핑표를 찾는다) 의 매핑 줄 GLOBAL · 지역 ·
    US 현금보정 βU 를 싣고, 핵심 본값 중앙값이 GLOBAL · 지역 둘 다에서 ±30% 밖이면 ★

사용:
    python 스크립트/peer_βU_us.py --세율 0.229 --기준일 2026-07-31 \
           --조립csv 유사기업_재료_C2_명단_CP.csv --스크린 C2_CP1스크린.json --출력 βU_핵심예비

입력(`--캐시`, 기본 `_raw/peers/`): 조립 csv(βL·R²·상관·시가총액) · 스크린 json(시가총액 근거, 선택) ·
debt_{T}.json(peer_차입금 자동) · 차입금_확정.json(주석 확인 덮어쓰기, 선택) · cf_{T}.json · 핵심표본.json(선택)
"""
from __future__ import annotations

import argparse
import csv
import datetime as _d
import io
import json
import math
import os
import statistics
import sys

sys.stdout.reconfigure(encoding="utf-8")
여기 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, 여기)
# 2026-10-25 FX4-P — DCF_RUN_ROOT(사슬 `--폴더` 가 넘긴다)면 그 회차에 쓴다 — 본체 경로로 돌려도 본체 _raw 에 쌓지 않게
ROOT = os.environ.get("DCF_RUN_ROOT") or os.path.dirname(여기)
PEER = os.path.join(ROOT, "_raw", "peers")
from 현금보정 import 현금비중, 보정  # noqa: E402

매출태그 = ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues",
         "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet", "Revenue"]
순이익태그 = ["NetIncomeLoss", "ProfitLoss", "ProfitLossAttributableToOwnersOfParent"]
영업이익태그 = ["OperatingIncomeLoss", "ProfitLossFromOperatingActivities"]
자본태그 = ["StockholdersEquity", "EquityAttributableToOwnersOfParent"]
연차서식 = ("10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A", "10-KT")


def 읽(p):
    return json.load(io.open(p, encoding="utf-8"))


def 연간(cf, 태그들, 통화, 기준일):
    """연차(350~380일) 사실을 끝일별로 — 태그 우선순위대로 빈 해를 채운다."""
    out = {}
    for tax in ("us-gaap", "ifrs-full"):
        g = cf["facts"].get(tax, {})
        for rank, tag in enumerate(태그들):
            if tag not in g:
                continue
            for x in g[tag]["units"].get(통화, []):
                if not x.get("start") or x["end"] > 기준일 or x.get("form") not in 연차서식:
                    continue
                일수 = (_d.date.fromisoformat(x["end"]) - _d.date.fromisoformat(x["start"])).days
                if not (350 <= 일수 <= 380):
                    continue
                k = x["end"]
                if k in out and (out[k][2] < rank or (out[k][2] == rank and out[k][3] >= x.get("filed", ""))):
                    continue   # 앞 순위 태그가 이긴다 · 같은 태그면 늦게 낸 서류
                out[k] = (x["val"], "%s/%s %s" % (tax, tag, 통화), rank, x.get("filed", ""))
    return [(k, out[k][0], out[k][1]) for k in sorted(out)]


def 보고통화(cf, 기준일):
    """매출 연차 사실이 가장 최근에 실린 통화(USD 편의환산과 원통화가 같이 있으면 원통화)."""
    best = {}
    for tax in ("us-gaap", "ifrs-full"):
        g = cf["facts"].get(tax, {})
        for tag in 매출태그:
            for u, arr in (g.get(tag, {}).get("units") or {}).items():
                for x in arr:
                    if x.get("start") and x["end"] <= 기준일 and x.get("form") in 연차서식:
                        best[u] = max(best.get(u, ""), x["end"])
    if not best:
        return "USD"
    최근 = max(best.values())
    같은날 = [u for u, e in best.items() if e == 최근]
    return next((u for u in 같은날 if u != "USD"), "USD")


def 최근시점(cf, 태그들, 통화, 기준일):
    best = None
    for tax in ("us-gaap", "ifrs-full"):
        g = cf["facts"].get(tax, {})
        for tag in 태그들:
            for x in (g.get(tag, {}).get("units") or {}).get(통화, []):
                if x.get("start") or x["end"] > 기준일:
                    continue
                if best is None or (x["end"], x.get("filed", "")) > (best["end"], best.get("filed", "")):
                    best = dict(x, 태그=tag)
    return best


def 최근과2년전(시계열):
    if not 시계열:
        return None, None
    last = 시계열[-1]
    e = _d.date.fromisoformat(last[0])
    prev2 = [s for s in 시계열 if abs((e - _d.date.fromisoformat(s[0])).days - 730) <= 20]
    return last, (prev2[-1] if prev2 else None)


def cagr(a, b):
    if not a or not b or a[1] is None or b[1] is None or a[1] <= 0 or b[1] <= 0:
        return None
    return (a[1] / b[1]) ** 0.5 - 1


def 재무(cf, 시총, 기준일):
    재 = {}
    통화 = 보고통화(cf, 기준일)
    rev = 연간(cf, 매출태그, 통화, 기준일)
    ni = 연간(cf, 순이익태그, 통화, 기준일)
    oi = 연간(cf, 영업이익태그, 통화, 기준일)
    r0, r2 = 최근과2년전(rev)
    n0, n2 = 최근과2년전(ni)
    o0 = next((x for x in reversed(oi) if r0 and x[0] == r0[0]), None)
    재.update({"통화": 통화, "매출_최근FY": r0, "매출_2년전FY": r2, "순이익_최근FY": n0, "순이익_2년전FY": n2,
              "매출CAGR2": cagr(r0, r2), "순이익CAGR2": cagr(n0, n2)})
    if o0 and r0 and r0[1]:
        재["영업이익률"], 재["영업이익_출처"] = o0[1] / r0[1], o0[2]
    else:
        재["영업이익률"] = None
        재["영업이익_출처"] = "확인 불가 — 최근 FY(%s) 영업이익 태그 없음(항목 부재)" % (r0[0] if r0 else "-")
    # PER·PBR 은 시가총액(USD)과 같은 통화여야 한다 — 원통화 회사는 같은 FY 의 USD 편의환산만 쓴다
    if 통화 == "USD":
        niu, eq = n0, 최근시점(cf, 자본태그, "USD", 기준일)
    else:
        niu_s = 연간(cf, 순이익태그, "USD", 기준일)
        niu = next((x for x in reversed(niu_s) if n0 and x[0] == n0[0]), None)
        eq = 최근시점(cf, 자본태그, "USD", 기준일)
        재["PER_비고"] = "원통화 %s — 같은 FY 의 USD 편의환산 사실만 씀(없으면 확인 불가)" % 통화
    재["PER"] = (시총 / niu[1]) if (시총 and niu and niu[1] and niu[1] > 0) else None
    재["PER_분모"] = ("순이익 %s %s" % (niu[0], niu[2])) if niu else "확인 불가"
    재["PBR"] = (시총 / eq["val"]) if (시총 and eq and eq["val"] > 0) else None
    재["PBR_분모"] = ("자본 %s %s" % (eq["end"], eq.get("form"))) if eq else "확인 불가"
    return 재


def _f(v):
    try:
        return float(v) if v not in (None, "") else None
    except ValueError:
        return None


def 세방식(행들, 세율, 키="βU", 비중키=None):
    """(a) 평균βL÷[1+(1−t)평균DE] · (b) 중앙값 · (c) 평균 — 비중키가 있으면 보정판. 행에 `세율` 이 있으면 그 평균(회사별 세율)."""
    ok = [z for z in 행들 if z.get(키) is not None]
    if not ok:
        return {"표본수": 0}
    v = [z[키] for z in ok]
    평균βL = statistics.mean(z["βL"] for z in ok)
    평균DE = statistics.mean(z["DE"] for z in ok)
    세율 = statistics.mean((z.get("세율") if z.get("세율") is not None else 세율) for z in ok)
    a = 평균βL / (1 + (1 - 세율) * 평균DE)
    if 비중키:
        평균비중 = statistics.mean(z[비중키] for z in ok)
        a = a / (1 - 평균비중)
    b, c = statistics.median(v), statistics.mean(v)
    순 = sorted(ok, key=lambda z: z[키])
    out = {"표본수": len(v), "(a)평균합산": a, "(b)개별중앙값_기본": b, "(c)개별평균": c,
           "최소": min(v), "최대": max(v), "티커": [z["티커"] for z in ok],
           "아래둘": [(z["티커"], round(z[키], 4)) for z in 순[:2]],
           "위둘": [(z["티커"], round(z[키], 4)) for z in 순[-2:]],
           "세값폭": max(a, b, c) - min(a, b, c)}
    out["세값_0.01안"] = out["세값폭"] <= 0.01
    return out


# 2026-10-25 FX4-P — IFRS 「FinanceCosts」(금융원가)는 이자비용이 아니다(외환 · 파생 · 평가손실이 섞여 이자보상배율이 낮게 나오고
# 스프레드가 커진다). 이자비용 태그가 없으면 스프레드를 세우지 않고 D/E ≥ 2 동종은 본값 밖(βU본값 ⑧)
이자태그 = ["InterestExpense", "InterestExpenseNonoperating", "InterestExpenseDebt", "InterestAndDebtExpense",
         "InterestExpenseNet", "InterestExpenseOnBorrowings"]


def _주식수(cf, d):
    """그 날(≤ d) 가장 가까운 유통주식수 — dei 표지 → us-gaap. (날짜, 값) 또는 None. 그날까지 제출된 값(filed ≤ d)을 먼저 —
    없을 때만 시점이 d 이하인 뒤 제출 값(2026-10-24 W18 · 평가기준일 뒤에 낸 표지를 기준일 자료로 쓰지 않는다)."""
    for tax, tags in (("dei", ("EntityCommonStockSharesOutstanding",)), ("us-gaap", ("CommonStockSharesOutstanding",))):
        best, 뒤 = None, None
        for tag in tags:
            for arr in ((cf.get("facts", {}).get(tax) or {}).get(tag, {}).get("units") or {}).values():
                for x in arr:
                    e = x.get("end") or ""
                    if e > d:
                        continue
                    if (x.get("filed") or "") > d:
                        if 뒤 is None or e > 뒤[0]:
                            뒤 = (e, x["val"])
                    elif best is None or e > best[0]:
                        best = (e, x["val"])
        if best or 뒤:
            return best or 뒤
    return None


분할비 = (1.5, 2, 3, 4, 5, 6, 7, 8, 10, 12, 15, 20, 25, 30, 40, 50, 100)      # 액면분할 · 병합에서 쓰는 비(그 역수는 병합)


def _분할배수(cf, d, T):
    """그 날 d 의 주식수를 평가기준일 T 의 주식 단위로 옮기는 배수(G4 — 액면분할 · 병합). 분할이 없거나 못 재면 1.0.

    주봉 종가는 분할 조정 값인데 그날의 유통주식수(표지)는 분할 전 수다 — 둘을 곱하면 분할 뒤 회사의 창 시점 시가총액이 배수만큼 작다.
    표지 주식수(dei → us-gaap)는 제 날의 값이라 뒤 공시가 다시 적지 않는다 — d 에서 T 까지 시점 차례로 이웃한 두 값의 비가 분할 비
    (1.5 · 2 · 3 · … · 100 또는 그 역수) 가운데 하나에서 4% 안이면 그 비를 분할로 보고 곱한다(자사주 매입 · 발행의 작은 변동은 분할이 아니다)."""
    for tax, tag in (("dei", "EntityCommonStockSharesOutstanding"), ("us-gaap", "CommonStockSharesOutstanding")):
        점 = {}
        for arr in (((cf.get("facts") or {}).get(tax) or {}).get(tag, {}).get("units") or {}).values():
            for x in arr:
                e, f, v = x.get("end") or "", x.get("filed") or "", x.get("val")
                if e and f and f <= T and e <= T and isinstance(v, (int, float)) and v > 0:
                    점.setdefault(e, (f, float(v)))
                    if f < 점[e][0]:
                        점[e] = (f, float(v))                    # 같은 날 값은 처음 낸 것(뒤에 다시 적은 값이 아니라)
        시작 = _주식수(cf, d)
        if not 점 or not 시작:
            continue
        줄 = [(시작[0], float(시작[1]))] + sorted((e, v) for e, (f, v) in 점.items() if e > 시작[0])
        배 = 1.0
        for (_e1, v1), (_e2, v2) in zip(줄, 줄[1:]):
            r = v2 / v1
            for n in 분할비:
                for 비 in (n, 1.0 / n):
                    if abs(r / 비 - 1) <= 0.04:
                        배 *= 비
                        break
                else:
                    continue
                break
        return 배
    return 1.0


def _주봉종가(rows, d8):
    """[(YYYYMMDD, 종가)] 에서 d8 이하 마지막 종가."""
    x = [v for dd, v in rows if dd <= d8]
    return x[-1] if x else None


확정갈림문턱 = 0.20     # 확정 D 와 같은 날 자동 D 가 이 비율보다 더 갈리면 자동 차입 계열(태그를 못 잡은 회사)을 창 평균에서 뺀다


def 창점들(cf, 시총, 기준일, 창시작, rows, 환율, 재무기준일=None, 확정=None):
    """회귀 창 안 연차 기말(+ 최신 재무상태표일)마다 (날짜, D, E, D/E, 현금비중). E = 시총 × (P_t ÷ P_0) × (S_t ÷ S_0).

    날짜 둘 — 장부 점(연차 기말 · 최신 재무상태표일과 그날의 차입 · 현금)은 재무기준일 F 이하의 마지막 값, 종가 · 주식수의 바탕(P_0 · S_0 —
    T 이하에 제출된 주식수)은 평가기준일 T 다. `재무기준일` 을 안 주면 F = T(옛 꼴).
    확정(`차입금_확정.json` 의 그 회사 줄 — {D, 기준일})이 있으면 그 날 점의 D 는 확정값이다(기준일이 없으면 최신 재무상태표일 · 그 날 점이
    없으면 더한다 · 기준일이 F 뒤면 창 점에 쓰지 않는다). 그 날 자동 D 가 확정 D 와 `확정갈림문턱` 보다 더 갈리면 자동 차입 계열을 믿을 수 없다 —
    다른 점은 표에 남기되 「평균밖」 으로 표시한다(창 평균 D/E · 현금비중은 평균밖이 아닌 점만 · 점이 둘 미만이면 βU본값이 기준일 한 점으로 간다)."""
    from peer_차입금 import 계산 as _차입, 사실표 as _표
    재기 = 재무기준일 or 기준일
    표 = _표(cf, 재기)
    연차 = sorted(set(표.연차날짜들("Assets")) | set(표.연차날짜들("Liabilities")))
    앵커 = max([표.최신일(t) for t in ("Assets", "Liabilities") if 표.최신일(t)], default=None)
    점 = {d for d in 연차 if d.replace("-", "") >= 창시작} | ({앵커} if 앵커 else set())
    확D = float(확정["D"]) if isinstance(확정, dict) and isinstance(확정.get("D"), (int, float)) and not isinstance(확정.get("D"), bool) else None
    확일 = ((확정.get("기준일") or 앵커) if 확D is not None else None)
    if 확일 and not (확일.replace("-", "") >= 창시작 and 확일 <= 재기):
        확일 = None                                          # F 뒤 · 창 밖 확정은 창 점에 쓰지 않는다(본 줄 D 는 그대로 확정)
    if 확일:
        점.add(확일)
    P0 = _주봉종가(rows, 기준일.replace("-", ""))
    S0 = _주식수(cf, 기준일)
    out, 자동계열뺌 = [], False
    for d in sorted(점):
        try:
            D = _차입(cf, d, 환율경로=환율).get("총차입금")
        except Exception:                                   # noqa: BLE001
            D = None
        덧 = {"D출처": "자동"}
        if d == 확일:
            갈림 = (abs(D - 확D) / abs(확D)) if (D is not None and 확D) else None
            자동계열뺌 = D is None or (갈림 is not None and 갈림 > 확정갈림문턱)
            덧 = {"D출처": "확정", "자동D": D, "갈림": 갈림}
            D = 확D
        Pd, Sd = _주봉종가(rows, d.replace("-", "")), _주식수(cf, d)
        if D is None or not (P0 and Pd and 시총):
            continue
        배 = _분할배수(cf, d, 기준일) if Sd else 1.0          # G4 — 주봉 종가는 분할 조정 값 · 그날 주식수는 분할 전 수
        E = 시총 * (Pd / P0) * ((Sd[1] * 배 / S0[1]) if (Sd and S0 and S0[1]) else 1.0)
        현 = 현금비중(cf, d, E, D, 환율경로=환율)
        out.append(dict({"날짜": d, "D": D, "E": E, "DE": D / E if E else None, "현금비중": 현.get("비중"),
                         "주식수": ("그날 · 분할 배수 %.4g" % 배 if 배 != 1.0 else "그날") if Sd else "기준일 고정"}, **덧))
    if 자동계열뺌:
        for p in out:
            if p["D출처"] == "자동":
                p["평균밖"] = True
    return out


def 이자보상(cf, 기준일):
    """(EBIT ÷ 이자비용, 근거) — 최근 연차. 이자비용 태그가 없으면 (None, 사유)."""
    통화 = 보고통화(cf, 기준일)
    oi = 연간(cf, 영업이익태그, 통화, 기준일)
    ie = 연간(cf, 이자태그, 통화, 기준일)
    if not oi or not ie:
        return None, "영업이익 또는 이자비용 연차 태그 없음"
    o, i = oi[-1], next((x for x in reversed(ie) if x[0] == oi[-1][0]), None)
    if not i:
        return None, "같은 회계연도의 이자비용 없음"
    if not i[1]:
        return float("inf"), "이자비용 0 — 무차입 취급"
    return o[1] / abs(i[1]), "%s 영업이익 ÷ 이자비용(%s)" % (o[0], i[2])


def main():
    ap = argparse.ArgumentParser(description="미국 유사기업 βU·현금보정·세 방식 (캐시 전용)", allow_abbrev=False)
    ap.add_argument("--세율", type=float, default=None,
                    help="무차입화 한계세율 — 숫자 기본값 없음(HWO-26). 빼면 무차입세율.py 단일 출처(시장데이터 캐시 US 국가 한계세율) · 주면 대조")
    ap.add_argument("--기준일", "--평가기준일", dest="기준일", required=True, help="평가기준일 T(분석일 · 시장 쪽 — 종가 · 시가총액 · 주식수 · 베타 창 끝 · 환율 · 법령 시행일) YYYY-MM-DD")
    ap.add_argument("--재무기준일", default=None, help="재무 자료 기준일 F(회사 장부 쪽 — 차입 · 현금 · 자산 · 이자보상 · 연간 재무). 비우면 평가기준일과 같다(1.1.2 · 날짜 둘)")
    ap.add_argument("--조립csv", required=True, help="peer_조립_us.py 산출 csv (회차 폴더 또는 캐시 기준)")
    ap.add_argument("--스크린", default=None, help="sec_peer_screen 산출 json — 시가총액을 여기서 읽는다(선택)")
    ap.add_argument("--핵심표본", default="핵심표본.json")
    ap.add_argument("--차입확정", default=None, help="주석 확인 D 덮어쓰기 json (기본: 차입금_확정.json → C2_차입금_확정.json)")
    ap.add_argument("--캐시", default=None)
    ap.add_argument("--환율", default=None)
    ap.add_argument("--출력", default=None, help="산출 이름(확장자 없이, 캐시 폴더에 json)")
    ap.add_argument("--세율표", default=None, help='회사별 세율 {"티커": 세율} json(경로 또는 글) — 소재국 세율. 없는 회사는 --세율')
    ap.add_argument("--ERP", type=float, default=None, help="부채베타 βD = 스프레드 ÷ ERP 의 ERP. 없으면 시장데이터 캐시(US) 성숙 + 국가")
    ap.add_argument("--부채스프레드", type=float, default=None, help="이자보상배율을 못 낸 D/E ≥ 2 회사의 스프레드(없으면 부채베타 미반영)")
    ap.add_argument("--대상", default=None, help="대상 티커 — 산업 βU 대조의 매핑 줄을 찾는다")
    ap.add_argument("--대상거래소티커", default=None, help="매핑표 「거래소:티커」(예: NasdaqGS:TSLA · KOSE:A000660)")
    ap.add_argument("--창평균", default="예", choices=["예", "아니오"], help="D/E · 현금을 회귀 창 연차 기말 점 평균으로(기본 예)")
    ap.add_argument("--국면", default=None, help="대상 A3 동인원천(국면) — 기본 회차 _raw/동인원천.json(S7-20)")
    ap.add_argument("--산업줄", default=None, help="산업 βU 대조 줄(다모다란 Industry Group)을 사람이 정한다 — 대상 매핑 줄이 사업과 다를 때(분류경보)")
    ap.add_argument("--기본값규칙", default="축소", choices=["축소", "본값"],
                    help="3단계 βU 기본값 — 축소(기본 · 1.1.3 정밀도 가중 축소 — 본값 (b) 와 업종 βU) / 본값(옛 순서)")
    ap.add_argument("--가정", default=None, help="1.1.4(R4) — 가정 파일: 대상 자체 회귀(주봉 캐시 · 엔진 3번 D/E)를 축소의 회귀 βU 에 넣고 서열 하한을 적는다")
    ap.add_argument("--지수", default="_INX", help="대상 자체 회귀의 지수 주봉 키(기본 _INX — 동종 조립과 같은 창구)")
    a = ap.parse_args()
    재기 = a.재무기준일 or a.기준일                             # 1.1.2(P10) — 장부 값은 F, 시장 값(시가총액 · 창)은 T
    try:
        import 무차입세율 as _무세
        a.세율, _세경보, _세출처 = _무세.대조(a.세율, "US", a.기준일)
    except ImportError:                                  # 도구만 따로 옮겨 쓴 자리 — 사람이 준 세율로(단일 출처 대조 없음)
        _세경보, _세출처 = None, "--세율(사람 · 무차입세율.py 없음 — 단일 출처 대조 못 함)" if a.세율 is not None else "무차입세율.py 없음"
    if a.세율 is None:
        sys.exit("무차입 세율을 정하지 못했습니다(%s) — --세율 을 주십시오." % _세출처)
    if _세경보:
        print("[세율 경보] " + _세경보)
    캐시 = a.캐시 or PEER
    회차 = os.path.dirname(os.path.dirname(os.path.abspath(캐시)))

    def 찾기(이름):
        if not 이름:
            return None
        for p in (이름, os.path.join(캐시, 이름), os.path.join(회차, 이름)):
            if os.path.exists(p):
                return p
        return None

    조립p = 찾기(a.조립csv)
    if not 조립p:
        sys.exit("조립 csv 가 없습니다: %s" % a.조립csv)
    with io.open(조립p, encoding="utf-8-sig") as f:
        행들 = list(csv.DictReader(f))
    스 = {}
    if a.스크린:
        sp = 찾기(a.스크린)
        if not sp:
            sys.exit("스크린 json 이 없습니다: %s" % a.스크린)
        j = 읽(sp)
        스 = {r["티커"]: r for r in (j.get("행") if isinstance(j, dict) else j)}
    구분, 슬롯, 목적 = {}, {}, {}
    hp = 찾기(a.핵심표본)
    if not hp and a.핵심표본:                      # 2026-10-24 W16 — 「_raw/peers/핵심표본.json」 처럼 작업 폴더 기준 상대 경로도
        import 피어경로 as _pp
        _p = _pp.명단경로(a.핵심표본, 캐시, 회차)
        hp = _p if os.path.exists(_p) else None
    if hp:
        # 2026-10-24 W16 — C1 의 핵심[] · 예비[] · 운영동종전용[] 이 정본(컷통과전체 구분은 그 밖의 회사에만). 종전에는 컷통과전체[].구분 만
        # 읽어 그 칸이 비면 핵심 묶음이 비고 본값 0곳으로 떨어졌다(유니버스 조사 물결 실측). 옛 꼴(티커 문자열 목록)은 전부 핵심(S7-19)
        import 핵심표본읽기 as _hr
        for k, v in _hr.구분표(읽(hp)).items():
            if v["시장"] == "KR":                     # 국내 회사는 미국 조립의 몫이 아니다
                continue
            구분[k] = v["구분"]
            슬롯[k] = v["슬롯"]
            목적[k] = v.get("목적") or []
    확정 = {}
    for 이름 in ([a.차입확정] if a.차입확정 else ["차입금_확정.json", "C2_차입금_확정.json"]):
        p = 찾기(이름)
        if p:
            확정 = {k: v for k, v in 읽(p).items() if isinstance(v, dict)}
            확정출처 = os.path.basename(p)
            break
    환율 = a.환율 or os.path.join(캐시, "환율_%s.json" % a.기준일.replace("-", ""))
    환율 = 환율 if os.path.exists(환율) else None
    세율표 = {}
    if a.세율표:
        # 2026-10-24 W17 — 이름 · 작업 폴더 기준 상대 경로 · 절대 경로를 명단과 같은 규칙으로 먼저 찾고, 없을 때만 JSON 글로(LIG디펜스 조사 — 이름만 주면 JSONDecodeError)
        import 피어경로 as _pk
        _sp = a.세율표 if a.세율표.lstrip().startswith("{") else _pk.명단경로(a.세율표, PEER, ROOT)
        if not a.세율표.lstrip().startswith("{") and os.path.exists(_sp):
            세율표 = json.load(io.open(_sp, encoding="utf-8"))
        else:
            try:
                세율표 = json.loads(a.세율표)
            except ValueError:
                sys.exit("--세율표 「%s」 — 파일도 JSON 글도 아니다(찾은 자리: %s). {\"티커\": 세율} 글이나 _raw/peers 의 파일 이름을 주십시오" % (a.세율표, _sp))
    # 시장데이터 캐시(US) — 부채베타의 ERP · 합성등급 표. 없으면 부채베타 미반영(지어내지 않는다)
    등급표, ERP, ERP근거 = None, a.ERP, "--ERP" if a.ERP else ""
    try:
        import market_data as _md
        _d, _곳 = _md.캐시읽기("US", a.기준일)
        if _d:
            등급표 = (_d.get("합성등급 스프레드 표") or {}).get("값")
            if ERP is None:
                _성, _국 = (_d.get("성숙시장 위험프리미엄") or {}).get("값"), (_d.get("국가위험프리미엄 (CRP)") or {}).get("값")
                ERP = (_성 + _국) if (_성 is not None and _국 is not None) else (_d.get("시장위험프리미엄 (ERP)") or {}).get("값")
                ERP근거 = "시장데이터 캐시 US(%s)" % _곳
    except Exception:                                       # noqa: BLE001
        pass

    out = []
    for r in 행들:
        t = r["티커"]
        s = 스.get(t, {})
        시총 = _f(s.get("시가총액")) if s else _f(r.get("시가총액"))
        βL = _f(r.get("베타"))
        dp = os.path.join(캐시, "debt_%s.json" % t)
        자동 = 읽(dp) if os.path.exists(dp) else None
        cfp = os.path.join(캐시, "cf_%s.json" % t)
        # 날짜 둘 — debt_ 파일이 평가기준일 T 로 셈해 앵커가 재무기준일 F 뒤면(T 앞 최신 분기) F 로 다시 센다(`peer_차입금 --재무기준일` 과 같은 셈)
        if 자동 and 재기 != a.기준일 and (자동.get("앵커일") or "") > 재기 and os.path.exists(cfp):
            try:
                from peer_차입금 import 계산 as _차입계산
                _옛앵 = 자동.get("앵커일")
                자동 = dict(_차입계산(읽(cfp), 재기, 환율경로=환율), 티커=t, 기준일=a.기준일, 재무기준일=재기,
                          다시셈="debt_ 파일 앵커 %s 가 재무기준일 %s 뒤 — F 로 다시 셈" % (_옛앵, 재기))
            except Exception as e:                          # noqa: BLE001
                자동 = dict(자동, 다시셈="F 로 다시 세지 못함(%s) — debt_ 파일 그대로(앵커 %s)" % (type(e).__name__, 자동.get("앵커일")))
        D2 = None
        if t in 확정 and 확정[t].get("D") is not None:
            D = 확정[t]["D"]
            D근거 = "%s — %s" % (확정[t].get("판정"), 확정[t].get("근거"))
            D일 = 확정[t].get("기준일")
            D2 = 확정[t].get("D_창고금융제외") or 확정[t].get("D_담보부제외")
            D판정 = "확정(%s)" % 확정출처
            if D일 and D일 > 재기:                            # 날짜 둘 — 장부 값은 F 이하여야 한다(경보만 — 「★」 는 βU본값이 본값에서 빼는 표지라 쓰지 않는다)
                D판정 += " · 경보: 확정 기준일 %s 이 재무기준일 %s 뒤" % (D일, 재기)
        elif 자동 and 자동.get("총차입금") is not None:
            D, D일 = 자동["총차입금"], 자동.get("차입구조일") or 자동.get("기본차입일")
            D근거 = "자동 — %s" % " / ".join((자동.get("잡힌것") or [])[-6:])
            if 자동.get("담보부가산"):
                D2 = 자동.get("총차입금_담보부제외")
            D판정 = "자동%s" % (" · ★주석 큐: " + " / ".join(자동.get("주석큐사유") or []) if 자동.get("주석확인_필요") else " 통과")
            if 자동.get("다시셈"):
                D근거 = "%s · %s" % (자동["다시셈"], D근거)
        else:
            D, D일, D근거, D판정 = None, None, "확인 불가 — debt 산출 없음 또는 환산 불가", "확인 불가"
        DE = (D / 시총) if (D is not None and 시총) else None
        # 2026-10-24 W18 — βU 도 그 회사 세율(--세율표 · 소재국)로 벗긴다. 종전에는 행의 세율 칸은 세율표 값인데 βU · 현금보정은
        # 공통 --세율로 벗겨 본값(행 세율)과 보정전 · 현금보정 요약(공통 세율)이 갈렸다
        _t = 세율표.get(t, a.세율)
        βU = (βL / (1 + (1 - _t) * DE)) if (βL is not None and DE is not None) else None
        βU2 = (βL / (1 + (1 - _t) * D2 / 시총)) if (D2 and βL is not None and 시총) else None

        재, 현 = {}, None
        if os.path.exists(cfp):
            cf = 읽(cfp)
            재 = 재무(cf, 시총, 재기)
            현 = 현금비중(cf, 재기, 시총, D, 환율경로=환율)
        βU보정 = 보정(βU, 현["비중"]) if 현 else None
        # ── 본값 사양 재료(S7-03 · 06) — 회사별 세율 · 창 평균 D/E · 현금 · 이자보상(합성등급 스프레드) · 부채총계 · 자산 ──
        덧 = {"세율": 세율표.get(t, a.세율), "세율출처": "--세율표" if t in 세율표 else "--세율(공통)",
             "부채총계": (자동 or {}).get("부채총계"), "자산총계": None, "DE_점들": [], "현금비중_점들": [], "창점": [],
             "부채스프레드": a.부채스프레드, "부채스프레드_근거": "--부채스프레드" if a.부채스프레드 is not None else ""}
        if os.path.exists(cfp):
            try:
                from peer_차입금 import 사실표 as _표
                _p = _표(cf, 재기)
                _앵 = _p.최신일("Assets")
                덧["자산총계"] = (_p.값("Assets", _앵) or [None])[0] if _앵 else None
                if 덧["부채총계"] is None and _p.최신일("Liabilities"):
                    덧["부채총계"] = (_p.값("Liabilities", _p.최신일("Liabilities")) or [None])[0]
                # 2026-10-24 W16 — 계약부채 · 고객 선수금(수주 산업 — 캡티브 오탐을 막는 재료 · βU본값)
                _계 = 0.0
                for _쌍 in (("ContractWithCustomerLiabilityCurrent", "ContractWithCustomerLiabilityNoncurrent"),
                           ("ContractWithCustomerLiability",), ("CustomerAdvancesCurrent", "CustomerAdvancesNoncurrent"),
                           ("DeferredRevenueCurrent", "DeferredRevenueNoncurrent"), ("DeferredRevenue",)):
                    _값 = [((_p.값(t, _p.최신일(t)) or [None])[0] if _p.최신일(t) else None) for t in _쌍]
                    _값 = [v for v in _값 if isinstance(v, (int, float))]
                    if _값:
                        _계 = max(_계, sum(_값))
                덧["계약부채"] = _계 or None
            except Exception:                               # noqa: BLE001
                pass
            if a.창평균 == "예" and 시총:
                _rows = 읽(os.path.join(캐시, "wk_%s.json" % t)) if os.path.exists(os.path.join(캐시, "wk_%s.json" % t)) else []
                _창 = "%04d%s" % (int(a.기준일[:4]) - 5, a.기준일[4:].replace("-", ""))
                try:
                    # 장부 점은 F 이하 · 확정 D 가 있으면 그 날 점은 확정값(자동 계열이 크게 갈리면 자동 점은 평균밖 — 창점들)
                    덧["창점"] = 창점들(cf, 시총, a.기준일, _창, _rows, 환율, 재무기준일=재기, 확정=확정.get(t))
                except Exception as e:                      # noqa: BLE001
                    덧["창점"] = []
                    덧["창점_오류"] = type(e).__name__
                _쓴점 = [p for p in 덧["창점"] if not p.get("평균밖")]
                덧["DE_점들"] = [p["DE"] for p in _쓴점 if p.get("DE") is not None]
                덧["현금비중_점들"] = [p["현금비중"] for p in _쓴점 if p.get("현금비중") is not None]
                _확점 = next((p for p in 덧["창점"] if p.get("D출처") == "확정"), None)
                if _확점 and len(_쓴점) < len(덧["창점"]):
                    덧["창점_경보"] = ("자동 차입(%s)이 확정 D(%s · %s)와 %s 갈린다 — 자동 점 %d개를 창 평균에서 뺐다(확정 점만)"
                                   % ("없음" if _확점.get("자동D") is None else "%.0f" % _확점["자동D"], "%.0f" % _확점["D"], _확점["날짜"],
                                      "—" if _확점.get("갈림") is None else "%.0f%%" % (_확점["갈림"] * 100), len(덧["창점"]) - len(_쓴점)))
            if 등급표:
                cov, 근 = 이자보상(cf, 재기)
                if cov is None:                              # 2026-10-25 FX4-P — 까닭을 남긴다(D/E ≥ 2 면 βU본값 ⑧ 본값 밖)
                    덧["부채스프레드_근거"] = "스프레드 못 세움 — %s(금융원가 FinanceCosts 는 이자비용으로 쓰지 않음)" % 근
                if cov is not None:
                    import 합성등급 as _hg
                    r합 = _hg.판정(cov if cov != float("inf") else None, 1.0 if cov != float("inf") else 0.0, 시총, 등급표)
                    if cov == float("inf"):
                        r합["이자보상배율"] = None
                    덧["부채스프레드"] = r합.get("스프레드")
                    덧["이자보상배율"] = r합.get("이자보상배율")       # 2026-10-25 FX3-b — βU본값 ⑧ 부실 신용 판정
                    덧["부채스프레드_근거"] = "합성등급 %s(%s · %s · %s)" % (r합.get("등급"), 근, r합.get("표"), r합.get("판정사유"))
        out.append({
            "티커": t, "회사명": r.get("회사명"), "구분": 구분.get(t), "핵심": 구분.get(t) == "핵심",
            "미래사업슬롯": "미래" in (슬롯.get(t) or ""),
            # 2026-10-25 FX3-b — 병합 표의 부문 가중(세 겹 ①)이 해외 행도 슬롯으로 묶게 슬롯 · 목적을 싣는다(종전에는 None — 부문 가중에서 빠졌다)
            "슬롯": 슬롯.get(t) or "", "목적": 목적.get(t) or [],
            "시가총액": 시총, "시가총액출처": "스크린" if s else "조립csv",
            "βL": βL, "R2": _f(r.get("결정계수")), "회귀표본": int(float(r["상관표본"])) if r.get("상관표본") else None,
            "단순상관": _f(r.get("단순상관")), "잔차상관": _f(r.get("잔차상관")),
            "D": D, "D기준일": D일, "D판정": D판정, "D근거": D근거, "DE": DE, "세율": a.세율,
            "βU": βU, "βU_담보부제외": βU2,
            "현금·단기투자": 현["합계"] if 현 else None, "현금잔액일": 현["잔액일"] if 현 else None,
            "현금비중": 현["비중"] if 현 else None, "βU_현금보정": βU보정,
            "현금보정_경보": (현["경보"] if 현 else ["companyfacts 캐시 없음"]),
            "현금보정_확인불가": (현["확인불가"] if 현 else "companyfacts 캐시 없음"),
            "재무": 재, "표본주": _f(r.get("표본주")) and int(_f(r.get("표본주"))),
            "βL_3년": _f(r.get("베타_3년")), "R2_3년": _f(r.get("결정계수_3년")),
            **덧,
        })
    out.sort(key=lambda z: -(z["잔차상관"] if z["잔차상관"] is not None else -9))

    핵 = [z for z in out if z["핵심"]] if 구분 else out
    요약 = {}
    for 이름, 묶음 in (("핵심", 핵), ("전체", out)):
        요약[이름] = {"보정전": 세방식(묶음, a.세율),
                    "현금보정": 세방식([z for z in 묶음 if z["βU_현금보정"] is not None], a.세율,
                                   키="βU_현금보정", 비중키="현금비중")}
        ok = [z for z in 묶음 if z["βU_현금보정"] is not None]
        if ok:
            중βU = statistics.median(z["βU"] for z in ok)
            중비중 = statistics.median(z["현금비중"] for z in ok)
            요약[이름]["참고_중앙값βU÷(1−중앙값현금비중)"] = 중βU / (1 - 중비중)
        요약[이름]["현금보정_제외"] = [(z["티커"], z["현금보정_확인불가"]) for z in 묶음
                                  if z["βU"] is not None and z["βU_현금보정"] is None]
    if any(z["미래사업슬롯"] for z in 핵):
        포함 = 세방식([z for z in 핵 if z["βU_현금보정"] is not None], a.세율, "βU_현금보정", "현금비중")
        제외 = 세방식([z for z in 핵 if z["βU_현금보정"] is not None and not z["미래사업슬롯"]],
                   a.세율, "βU_현금보정", "현금비중")
        요약["미래사업슬롯"] = {"포함": 포함, "제외": 제외}
        if 포함.get("표본수") and 제외.get("표본수"):
            차 = abs(포함["(b)개별중앙값_기본"] - 제외["(b)개별중앙값_기본"])
            요약["미래사업슬롯"]["중앙값차"] = 차
            요약["미래사업슬롯"]["경보"] = 차 > 0.15
    if any(z["βU_담보부제외"] for z in 핵):
        대조 = [dict(z, βU=(z["βU_담보부제외"] or z["βU"])) for z in 핵]
        for z in 대조:
            if z["βU_담보부제외"] and z["현금비중"] is not None:
                z["βU_현금보정"] = 보정(z["βU"], z["현금비중"])
        요약["핵심_담보부제외대조"] = 세방식([z for z in 대조 if z["βU_현금보정"] is not None], a.세율,
                                    "βU_현금보정", "현금비중")
    # ── 본값(S7-03 · 06 · 07) — βU본값.py 규칙. 본값 · 포함 · 3년 창 · 95% 구간 · 산업 βU 대조 ──
    import βU본값 as 본
    for z in out:
        본.본값행(z, ERP)
    for 이름, 묶음 in (("핵심", 핵), ("전체", out)):
        요약[이름]["본값규칙"] = 본.요약(묶음, a.세율, ERP)
    산업 = None
    try:
        import 산업베타 as _ib
        티커들 = [a.대상거래소티커] if a.대상거래소티커 else (_ib.거래소티커후보(a.대상) if a.대상 else [])
        if 티커들 or a.대상:
            b = 요약["핵심"]["본값규칙"]["본값"]
            _동 = [_ib.거래소티커후보(z["티커"]) for z in 핵 if z.get("티커")]       # 2026-10-24 W18 — 동종 다수 줄 대조 · `--산업줄`
            _사 = None
            try:
                _사 = (읽(os.path.join(캐시, "sub_%s.json" % a.대상.upper())) or {}).get("name") if a.대상 else None
            except Exception:                               # noqa: BLE001
                _사 = None
            산업 = _ib.대조값(티커들, b.get("(b)개별중앙값_기본"), a.기준일, a.산업줄, None, None if a.산업줄 else _동, _사)
    except SystemExit as e:
        산업 = {"문장": "산업 βU 대조 불가 — %s" % e, "★": False}
    except Exception as e:                                  # noqa: BLE001
        산업 = {"문장": "산업 βU 대조 불가 — %s" % type(e).__name__, "★": False}
    # 1.1.3(B1) — 정밀도 가중 축소: 본값 (b)(표본 셋 이상 · 부트스트랩 구간의 표준오차)를 업종 βU 쪽으로(국내 조립기와 같은 규칙).
    # 1.1.4(R4) — `--가정` 이면 대상 자체 회귀(동종과 같은 주봉 캐시 · 엔진 3번 D/E)를 회귀 βU 에 넣는다(종전에는 이 조립기 밖이라 빠졌다)
    대상자체 = 대상판정 = W서열 = None
    이동 = None
    if getattr(a, "가정", None) and a.대상:
        try:
            from 엔진.계산 import 계산 as _계산
            _가 = json.load(io.open(a.가정, encoding="utf-8"))
            W서열 = (_계산(_가, "기준").get("WACC") or {}).get("예측기간")
            대상자체, _까 = 본.대상자체주봉(캐시, a.대상.upper(), a.지수, a.기준일, W서열, 이동개월=본._축소설정().get("창이동개월"), 세율=a.세율)
            if 대상자체:
                대상판정 = 본.대상자체판정(대상자체, {})
                if isinstance(대상자체.get("창이동"), dict):
                    이동 = {"대상 자체": 대상자체["창이동"]["차"]}
            else:
                print("  대상 자체 회귀 못 냄 — %s" % _까)
        except Exception as e:                              # noqa: BLE001
            print("  대상 자체 회귀 못 냄 — %s" % e)
    축 = 본.축소규칙(핵, None, 산업, 대상자체, 대상판정, (요약["핵심"]["본값규칙"] or {}).get("구간95"), None, 이동)
    if W서열 and 축.get("적용"):
        축["서열"] = 본.서열하한(축["사후"], W서열, float(본._축소설정().get("서열문턱", 0.01)))
    if getattr(a, "기본값규칙", "축소") == "축소" and 축.get("적용"):
        요약["핵심"]["본값규칙"]["기본값_옛규칙"] = 요약["핵심"]["본값규칙"].get("기본값")
        요약["핵심"]["본값규칙"]["기본값"] = 본.축소기본값(요약["핵심"]["본값규칙"].get("기본값"), 축)
    _창 = "%04d%s" % (int(a.기준일[:4]) - 5, a.기준일[4:].replace("-", ""))
    국면 = 본.국면창점검(a.국면 or os.path.join(회차, "_raw", "동인원천.json"), _창, a.기준일.replace("-", ""))
    n = statistics.median([z["회귀표본"] for z in out if z["회귀표본"]]) if any(z["회귀표본"] for z in out) else None
    문턱 = 2 / math.sqrt(n) if n else None
    결과 = {"세율": a.세율, "세율출처": _세출처, "세율경보": _세경보, "기준일": a.기준일, "재무기준일": 재기, "조립csv": os.path.basename(조립p),
          "식": "βU = βL/(1+(1−t)D/E) · βU(보정) = βU ÷ (1 − (현금+단기투자)/(시가총액+D)) — 개별 보정 뒤 중앙값",
          "표": out, "요약": 요약,
          "본값": {"핵심": 요약["핵심"]["본값규칙"], "판정": 요약["핵심"]["본값규칙"].get("판정"), "기본값": 요약["핵심"]["본값규칙"].get("기본값"), "ERP": ERP, "ERP근거": ERP근거, "산업대조": 산업, "국면창": 국면,
                 "축소": 축, "기본값규칙": getattr(a, "기본값규칙", "축소"), "대상자체": 대상자체, "대상자체판정": 대상판정,
                 "쓰는법": "3단계 WACC 의 무차입 베타 기본값은 `본값.핵심.기본값.값`(출처 칸 — 본값 셋 이상이면 본값 (b), 아니면 포함 (b), 그것도 셋 미만이면 산업 βU 선택지 ★ · S7R1-N1) — 「포함」 · 「대안_3년창」 · "
                         "「구간95」 · 산업 βU 를 근거 칸과 민감도 WACC 폭에 함께 싣는다"},
          "잡음문턱": {"표본주": n, "문턱": 문턱,
                   "넘는수": sum(1 for z in out if 문턱 and (z["잔차상관"] or 0) > 문턱), "전체": len(out)}}
    이름 = a.출력 or ("βU_" + os.path.splitext(os.path.basename(조립p))[0])
    op = os.path.join(캐시, 이름 + ".json")
    json.dump(결과, io.open(op, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    f = lambda v, fm="%6.3f": ("   n/a" if v is None else fm % v)
    print("세율 %.4f · 기준일 %s · 잡음 문턱 %s · 넘는 곳 %d/%d" % (a.세율, a.기준일, f(문턱), 결과["잡음문턱"]["넘는수"], len(out)))
    print("%-5s %-2s %8s %6s %6s %8s %6s %6s %7s %6s %7s %7s %6s %6s" % (
        "티커", "구", "시총bn", "βL", "잔차", "D bn", "D/E", "βU", "현금%", "βU보정", "매출g", "영익률", "PER", "PBR"))
    for z in out:
        재 = z["재무"]
        print("%-5s %-2s %8.2f %s %s %8s %s %s %s %s %s %s %s %s" % (
            z["티커"], (z["구분"] or "")[:2], (z["시가총액"] or 0) / 1e9, f(z["βL"]), f(z["잔차상관"]),
            ("%.2f" % (z["D"] / 1e9)) if z["D"] is not None else "n/a", f(z["DE"]), f(z["βU"]),
            f(z["현금비중"] * 100 if z["현금비중"] is not None else None, "%6.2f%%"), f(z["βU_현금보정"]),
            f(재.get("매출CAGR2"), "%7.3f"), f(재.get("영업이익률"), "%7.3f"), f(재.get("PER"), "%6.1f"),
            f(재.get("PBR"), "%6.1f")))
        _본비 = z.get("현금비중_본")
        if _본비 is not None and z["현금비중"] is not None and abs(_본비 - z["현금비중"]) >= 0.10:
            # 2026-10-24 W17 — 이 줄의 현금% · βU보정은 기준일 한 점이다. 본값은 창 평균(현금비중_본 · βU_본)을 쓴다 — 두 값이 갈리면 함께 보인다(LS ELECTRIC 조사 · POWL 5.7% 대 68.2%)
            print("        본값 사양: 현금(창 평균) %.1f%% · βU본 %s — 기준일 한 점 %.1f%% 와 다르다(병합 · 본값은 창 평균)" % (
                _본비 * 100, f(z.get("βU_본")), z["현금비중"] * 100))
        for w in z["현금보정_경보"]:
            print("        현금 경보: %s" % w)
        if z["현금보정_확인불가"]:
            print("        현금보정 제외: %s" % z["현금보정_확인불가"])
        if "주석 큐" in (z["D판정"] or ""):
            print("        D: %s" % z["D판정"])
        if z.get("창점_경보"):
            print("        창 평균: %s" % z["창점_경보"])
    for 이름2, s2 in 요약.items():
        if not isinstance(s2, dict):
            continue
        for k, v in s2.items():
            if isinstance(v, dict) and v.get("표본수"):
                print("%s·%s: n=%d (a) %.4f · (b) %.4f[기본] · (c) %.4f · 폭 %.4f%s · 아래 %s · 위 %s" % (
                    이름2, k, v["표본수"], v["(a)평균합산"], v["(b)개별중앙값_기본"], v["(c)개별평균"],
                    v["세값폭"], " (0.01 안)" if v["세값_0.01안"] else "", v["아래둘"], v["위둘"]))
            elif k.startswith("참고"):
                print("%s·%s: %.4f" % (이름2, k, v))
            elif k == "현금보정_제외" and v:
                print("%s·현금보정 제외: %s" % (이름2, v))
    print("── 본값(βU본값.py) ── " + 본.문장(요약["핵심"]["본값규칙"], 산업))
    if 요약["핵심"]["본값규칙"].get("경보"):
        print("  ※ " + 요약["핵심"]["본값규칙"]["경보"])
    if 산업 and 산업.get("★"):
        print("  ★ 산업 βU 대조 — 핵심 본값 중앙값이 산업 βU 의 ±30% 밖이다. 확정 신뢰도 ★(문항) — 유사기업 βU 규칙")
    if 국면:
        print("  국면 창 — " + 국면["문장"])
    print("→ %s" % op)


if __name__ == "__main__":
    main()

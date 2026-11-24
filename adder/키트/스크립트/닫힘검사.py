# -*- coding: utf-8 -*-
"""닫힘검사 — 항등식 · 역사 밴드 · 단위 · 격자 검산 · 재료 신선도를 한 번에 보고 **master check 한 값**을 낸다 (2026-10-23 · 연구/동인연동_업그레이드_연구.md P5).

    python 스크립트/닫힘검사.py 가정.json                 # → 가정 곁 _raw/닫힘검사.json · 표를 찍는다
    python 스크립트/닫힘검사.py 가정.json --격자없이      # 민감도 격자 검산(엔진 75바퀴)을 건너뛴다

다섯 + 둘(값을 바꾸지 않는다 · 엔진 산식을 고치지 않는다 · 자체검사 ㊹ · ㊼ · ㉕ 이 보는 것은 되풀이하지 않고 그 사이를 본다)
  ① 성장 출처 ↔ 반응(Mauboussin · Rappaport 의 factor 층) — 비관 · 낙관이 기준과 갈린 마지막 예측 해에서 Δln 매출을 물량(4번 191 전사 판매량 지수)과 가격(나머지)으로
     가르고, **가격 주도**인데 CAPEX ÷ 매출이 움직였으면(투자가 매출액에 묶여 있다 — 매출연동 · Sales-to-Capital) 참고, **물량 주도**인데 영업이익률이 그대로면(고정비가
     없다 — 전부 매출액비율) 참고. 191 이 없으면(전부 증가율 경로 · 원가가중 미선언) 건너뛴다
  ② 효율 성장(다모다란 [[1권 p.188~189]] — g = 재투자율 × ROC + ΔROC ÷ ROC) — 예측기간 NOPLAT 성장률에서 재투자율 × 기초 ROIC 를 뺀 **효율 성장 항**과 그 가운데
     마진 개선 몫 · 회전 개선 몫을 숫자로 낸다(참고 — 경보는 ㊹ ③ 이 낸다). 효율 항이 양인데 마진 · 회전 어느 쪽도 개선이 없으면 참고(「재투자 없는 성장」의 출처 불명)
  ③ 역사 밴드(McKinsey 「비율로 예측」) — 매출원가율 · 판관비율 · 감가상각 ÷ 매출 · 순운전자본 ÷ 매출의 예측 · 영구 열이 회사 자신의 회계연도 실적 범위 ±15% 밖이면 참고,
     ±50% 밖이면 경보(CAPEX ÷ 매출 · 매출 ÷ 유무형자산은 ㊹ ① 이 본다 — 되풀이하지 않는다). 실적 열 둘 미만이면 건너뛴다
  ④ 단위 — `_raw/동인그래프.json`(P1)의 단위 검사 결과를 받는다(경보 수 · 참고 수). 없으면 「동인그래프.py 를 먼저」 참고
  ⑤ master check — 이 도구의 경보 + 신호 파일 목록(`신호파일.목록`)의 경보 합이 0 이면 「닫힘」. ICAEW Financial Modelling Code #17(따로 계산되지만 같아야 하는 값마다
     등식 검사 · master check 한 셀)의 자리 — 15번 판정을 대신하지 않는다(자체검사 · 모순 장부는 그대로)
  ⑥ 격자 검산(Anthropic dcf-model 스킬) — 14번 표 Ⅰ · Ⅱ(엔진 `민감도.표다섯`)의 가운데 칸(가감 0 × 0)이 모델 주당가치와 같은가(차 1e-6 넘으면 경보 —
     격자 축이 기준을 안 지난다는 뜻). `--격자없이` 로 건너뛴다
  ⑦ 재료 신선도(무디스 context layer 의 temporal validity 자리) — 가정 곁 `_raw/*.json` 의 만든날 · 조회일 · 작성이 가정 파일보다 오래되면 「가정 뒤에 안 돌린 도구」(참고),
     평가기준일보다 180일 넘게 뒤의 조회일(참고 — 기준일 뒤 자료는 사후 정보일 수 있다). 날짜 칸이 없는 파일은 세지 않는다
종료 코드 — 0 경보 없음 · 1 경보 있음 · 2 입력 오류. 회사 · 업종 이름이 코드에 없다.
"""
from __future__ import annotations

import argparse
import datetime
import glob
import importlib
import io
import json
import math
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass
여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류           # noqa: E402
from 기간축 import 기간축                              # noqa: E402
import 신호파일                                        # noqa: E402

출처이름 = "닫힘검사"
형식 = "닫힘검사 1"
밴드폭, 밴드경보폭 = 0.15, 0.50
신선도일수 = 180


def _수(v):
    try:
        return None if (v is None or isinstance(v, bool)) else float(v)
    except (TypeError, ValueError):
        return None


def _줄(R, 시트, 번호, ID):
    v = (R.get(시트) or {}).get(str(번호))
    if isinstance(v, dict):
        return [_수(v.get(c)) for c in ID]
    return [None] * len(ID)


def _비(a, b):
    return (a / b) if (a is not None and b not in (None, 0)) else None


# ────────────────────────────────────────────────────────────── 검사들

def 성장출처검사(R들, 축, 신):
    ID, 끝 = 축.ID, 축.끝예측
    기 = R들["기준"]
    Q기 = _줄(기, "4.Sales", "191", ID)[끝]
    if not Q기:
        return {"건너뜀": "4번 191(전사 판매량 지수)이 없다 — 물량 · 가격을 가를 수 없다"}
    낸 = {}
    for 시 in ("비관", "낙관"):
        R = R들[시]
        S기, S시 = _줄(기, "4.Sales", "54", ID)[끝], _줄(R, "4.Sales", "54", ID)[끝]
        Q시 = _줄(R, "4.Sales", "191", ID)[끝]
        if not (S기 and S시 and Q시 and S기 > 0 and S시 > 0):
            continue
        dS, dQ = math.log(S시 / S기), math.log(Q시 / Q기)
        dP = dS - dQ
        m기 = _비(_줄(기, "2.DCF", "15", ID)[끝], S기)
        m시 = _비(_줄(R, "2.DCF", "15", ID)[끝], S시)
        c기 = _비(abs(_줄(기, "8.CapEx", "31", ID)[끝] or 0), S기)
        c시 = _비(abs(_줄(R, "8.CapEx", "31", ID)[끝] or 0), S시)
        한 = {"Δln매출": dS, "Δln물량": dQ, "Δln가격": dP, "Δ영업이익률": (m시 - m기) if (m기 is not None and m시 is not None) else None,
             "ΔCAPEX비율": (c시 - c기) if (c기 is not None and c시 is not None) else None}
        if abs(dS) < 0.005:
            한["판정"] = "기준과 매출이 같다"
        elif abs(dP) > 2 * abs(dQ):
            한["판정"] = "가격 주도"
            if 한["ΔCAPEX비율"] is not None and abs(한["ΔCAPEX비율"]) > 0.005:
                신("성장 출처 ↔ 투자", 시, 한["ΔCAPEX비율"], 0.005,
                  "%s 의 매출 차이는 가격(Δln %.3f)이 물량(%.3f)보다 큰데 CAPEX ÷ 매출이 %+.1f%%p 움직였다 — 가격이 올라도 설비는 그대로여야 한다. 투자가 매출액에 묶여 있지 않은지(매출연동 851 · Sales-to-Capital 859)를 본다"
                  % (시, dP, dQ, 한["ΔCAPEX비율"] * 100), "참고")
        elif abs(dQ) > 2 * abs(dP):
            한["판정"] = "물량 주도"
            if 한["Δ영업이익률"] is not None and abs(한["Δ영업이익률"]) < 0.001:
                신("성장 출처 ↔ 마진", 시, 한["Δ영업이익률"], 0.001,
                  "%s 의 매출 차이는 물량(Δln %.3f)인데 영업이익률이 그대로다(%+.2f%%p) — 고정비가 없는 모형이다(원가 줄 전부 매출액비율?). 영업레버리지가 서려면 물가연동 · 설비계수 줄이 있어야 한다"
                  % (시, dQ, 한["Δ영업이익률"] * 100), "참고")
        else:
            한["판정"] = "섞임"
        낸[시] = 한
    return 낸


def 효율성장검사(R들, 축, 신):
    ID = 축.ID
    기 = R들["기준"]
    예 = [i for i in 축.예측 if 축.열[i].개월 >= 12] if hasattr(축, "열") else 축.예측
    if len(예) < 2:
        return {"건너뜀": "연간 예측 열이 둘 미만"}
    n19 = _줄(기, "2.DCF", "19", ID)
    a, b = 예[0], 예[-1]
    if not (n19[a] and n19[b] and n19[a] > 0 and n19[b] > 0):
        return {"건너뜀": "NOPLAT 이 양수가 아니다"}
    g = (n19[b] / n19[a]) ** (1.0 / (b - a)) - 1
    cap, da, wc = _줄(기, "2.DCF", "21", ID), _줄(기, "2.DCF", "20", ID), _줄(기, "2.DCF", "22", ID)
    wc14, t21, n28 = _줄(기, "9.WC", "14", ID), _줄(기, "8.CapEx", "21", ID), _줄(기, "8.CapEx", "28", ID)
    S = _줄(기, "4.Sales", "54", ID)
    RR, ROIC = [], []
    for i in 예[:-1]:
        if n19[i] and n19[i] > 0:
            RR.append(((cap[i] or 0) - (da[i] or 0) + (wc[i] or 0)) / n19[i])
        기초 = (wc14[i - 1] or 0) + (t21[i - 1] or 0) + (n28[i - 1] or 0) if i > 0 else None
        if 기초 and n19[i]:
            ROIC.append(n19[i] / 기초)
    if not RR or not ROIC:
        return {"건너뜀": "재투자율 · ROIC 를 못 냈다"}
    rr, roic = sum(RR) / len(RR), sum(ROIC) / len(ROIC)
    펀 = rr * roic
    효율 = g - 펀
    m_a, m_b = _비(_줄(기, "2.DCF", "15", ID)[a], S[a]), _비(_줄(기, "2.DCF", "15", ID)[b], S[b])
    turn_a = _비(S[a], (wc14[a] or 0) + (t21[a] or 0) + (n28[a] or 0))
    turn_b = _비(S[b], (wc14[b] or 0) + (t21[b] or 0) + (n28[b] or 0))
    마진몫 = ((m_b / m_a) ** (1.0 / (b - a)) - 1) if (m_a and m_b and m_a > 0 and m_b > 0) else None
    회전몫 = ((turn_b / turn_a) ** (1.0 / (b - a)) - 1) if (turn_a and turn_b and turn_a > 0 and turn_b > 0) else None
    낸 = {"NOPLAT성장률": g, "재투자율": rr, "기초ROIC": roic, "펀더멘털성장": 펀, "효율성장항": 효율, "마진개선률_연": 마진몫, "회전개선률_연": 회전몫,
         "열": [ID[a], ID[b]]}
    if 효율 > 0.03 and (마진몫 is None or 마진몫 <= 0.002) and (회전몫 is None or 회전몫 <= 0.002):
        신("효율 성장의 출처 불명", "기준", 효율, 0.03,
          "NOPLAT 성장 %.1f%% 가운데 재투자율 %.2f × ROIC %.1f%% = %.1f%% 를 뺀 효율 성장 %.1f%%p 가 남는데 마진도 회전도 개선되지 않는다 — 어디서 오는 성장인가(㊹ ③ 과 같은 자리의 분해)"
          % (g * 100, rr, roic * 100, 펀 * 100, 효율 * 100), "참고")
    return 낸


_밴드항목 = (("매출원가율", "5.COGS", "17", "흐름"), ("판관비율", "6.SG&A", "16", "흐름"), ("감가상각÷매출", "8.CapEx", "32", "흐름"), ("순운전자본÷매출", "9.WC", "14", "저량"))


def _매출자(R, ID, 꼴):
    """흐름(원가 · 상각)은 그 열의 매출(54 — 잔여 기간 열도 같은 기간), 저량(순운전자본 잔액)은 연환산 매출(55)."""
    S = _줄(R, "4.Sales", "55" if 꼴 == "저량" else "54", ID)
    S2 = _줄(R, "4.Sales", "54", ID)
    return [S[i] if S[i] else S2[i] for i in range(len(ID))]


def 역사밴드검사(R들, 축, 신):
    ID = 축.ID
    기 = R들["기준"]
    낸 = {}
    for 이름, 시트, 줄, 꼴 in _밴드항목:
        S = _매출자(기, ID, 꼴)
        v = _줄(기, 시트, 줄, ID)
        실 = [v[i] / S[i] for i in 축.FY실적 if v[i] is not None and S[i]]
        if len(실) < 2:
            낸[이름] = {"건너뜀": "실적 열 둘 미만"}
            continue
        lo, hi = min(실), max(실)
        폭 = max(abs(lo), abs(hi), 1e-9)
        밖, 멀리 = {}, {}
        for 시, R in R들.items():
            vv, ss = _줄(R, 시트, 줄, ID), _매출자(R, ID, 꼴)
            for i in 축.예측 + [축.영구]:
                if vv[i] is None or not ss[i]:
                    continue
                x = vv[i] / ss[i]
                if x < lo - 밴드경보폭 * 폭 or x > hi + 밴드경보폭 * 폭:
                    멀리.setdefault(시, []).append(ID[i])
                elif x < lo - 밴드폭 * 폭 or x > hi + 밴드폭 * 폭:
                    밖.setdefault(시, []).append(ID[i])
        낸[이름] = {"실적범위": [lo, hi], "밖": 밖, "멀리": 멀리}
        if 멀리:
            신("역사 밴드 멀리 밖", 이름, {k: len(v) for k, v in 멀리.items()}, "±50%",
              "%s 의 예측이 회사 실적 범위 %.3f~%.3f 에서 ±50%% 넘게 벗어난다 — %s. 외부 제약 · 구조 변화의 근거가 있어야 한다"
              % (이름, lo, hi, " / ".join("%s %s" % (k, " · ".join(v[:4])) for k, v in 멀리.items())), "경보")
        elif 밖:
            신("역사 밴드 밖", 이름, {k: len(v) for k, v in 밖.items()}, "±15%",
              "%s 의 예측이 회사 실적 범위 %.3f~%.3f 의 ±15%% 밖 — %s(㊹ · ㊼ 이 보지 않는 비율)" % (이름, lo, hi, " / ".join("%s %s" % (k, " · ".join(v[:4])) for k, v in 밖.items())), "참고")
    return 낸


def 단위검사받기(가정경로, 신):
    p = os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw", "동인그래프.json") if 가정경로 else None
    if not p or not os.path.exists(p):
        신("단위 검사 없음", "동인그래프.json", None, None, "동인 그래프가 없다 — `python 스크립트/동인그래프.py 가정.json` 을 먼저 돌리면 단위 검사가 여기 든다", "참고")
        return {"있음": False}
    try:
        j = json.load(io.open(p, encoding="utf-8"))
    except (OSError, ValueError):
        return {"있음": False, "문제": "JSON 깨짐"}
    단 = j.get("단위검사") or []
    경 = [s for s in 단 if s.get("등급") == "경보"]
    return {"있음": True, "경보": len(경), "참고": len(단) - len(경), "만든날": j.get("만든날"), "구조지문": j.get("구조지문")}


def 격자검산(가정, 신):
    M = importlib.import_module("엔진.민감도")
    T = M.표다섯(가정, (가정.get("스위치") or {}).get("적용시나리오") or "기준")
    낸 = {"주당가치": T.get("주당가치")}
    for k in ("표1", "표2"):
        t = T.get(k)
        if not isinstance(t, dict) or not t.get("값"):
            continue
        세, 가 = t.get("세로가감") or [], t.get("가로가감") or []
        i = next((n for n, x in enumerate(세) if _수(x) is not None and abs(_수(x)) < 1e-12), None)
        j = next((n for n, x in enumerate(가) if _수(x) is not None and abs(_수(x)) < 1e-12), None)
        if i is None or j is None:
            낸[k] = {"가운데": None, "까닭": "가감 0 인 축 칸이 없다(홀수 칸 · 가운데 = 기준이어야 한다)"}
            신("격자 가운데 칸 없음", k, None, "가감 0", "%s 의 축에 가감 0(기준) 칸이 없다 — 홀수 칸 · 가운데 = 기준 주당가치여야 검산이 된다" % k, "경보")
            continue
        v = _수(t["값"][i][j])
        낸[k] = {"가운데": v, "자리": [i, j]}
        if v is None or T.get("주당가치") is None or abs(v - T["주당가치"]) > 1e-6 * max(1.0, abs(T["주당가치"])):
            신("격자 가운데 ≠ 주당가치", k, v, T.get("주당가치"), "%s 의 가운데 칸 %s 가 모델 주당가치 %s 와 다르다 — 격자 축이 기준을 지나지 않는다(손잡이 · 가감이 어긋났다)" % (k, v, T.get("주당가치")), "경보")
    return 낸


def 신선도검사(가정, 가정경로, 신):
    if not 가정경로:
        return {"건너뜀": "가정 경로 없음"}
    raw = os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw")
    if not os.path.isdir(raw):
        return {"건너뜀": "_raw 없음"}
    기준일 = None
    try:
        기준일 = datetime.date.fromisoformat(("%s" % ((가정.get("메타") or {}).get("평가기준일") or ""))[:10])
    except ValueError:
        pass
    낡음, 사후, 본 = [], [], 0
    for p in sorted(glob.glob(os.path.join(raw, "*.json"))):
        if os.path.basename(p) == "닫힘검사.json":
            continue
        try:
            j = json.load(io.open(p, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(j, dict):
            continue
        날 = next((j[k] for k in ("만든날", "조회일", "작성", "작성일") if isinstance(j.get(k), str)), None)
        if not 날:
            continue
        본 += 1
        if os.path.getmtime(p) < os.path.getmtime(가정경로) - 60:
            낡음.append(os.path.basename(p))
        조 = j.get("조회일") if isinstance(j.get("조회일"), str) else None       # 사후 정보는 바깥 자료를 조회한 날로만 본다(도구가 만든 날이 아니다)
        if 조 and 기준일:
            try:
                d = datetime.date.fromisoformat(조[:10])
            except ValueError:
                continue
            if d > 기준일 + datetime.timedelta(days=신선도일수):
                사후.append("%s(%s)" % (os.path.basename(p), d.isoformat()))
    if 낡음:
        신("가정 뒤에 안 돌린 도구", "_raw", len(낡음), 0, "가정 파일이 이 재료보다 새것이다 — %s. 가정이 바뀐 뒤 다시 돌리지 않았다(엔진 값을 읽는 도구면 낡은 신호다)" % " · ".join(낡음[:8]), "참고")
    if 사후:
        신("평가기준일 뒤 자료", "_raw", len(사후), 신선도일수, "평가기준일 %s 보다 %d일 넘게 뒤에 조회한 재료 — %s. 기준일 뒤 정보(사후 정보)가 가정에 섞이지 않았는지 본다" % (기준일, 신선도일수, " · ".join(사후[:6])), "참고")
    return {"본파일": 본, "낡음": 낡음, "사후": 사후}


# ────────────────────────────────────────────────────────────── 조립

def 분석(가정, 가정경로=None, 격자=True):
    신호 = []

    def 신(종류, 대상, 값, 문턱, 글, 등급="참고"):
        신호.append({"출처": 출처이름, "종류": 종류, "대상": 대상, "값": 값, "문턱": 문턱, "글": 글, "등급": 등급})
    try:
        축 = 기간축(가정)
        E = importlib.import_module("dcf엔진")
        R들 = {s: E.계산(가정, s) for s in ("비관", "기준", "낙관")}
    except Exception as e:                           # noqa: BLE001
        return None, "엔진이 가정을 계산하지 못했다 — %s" % ("%s" % e)[:200]
    낸 = {"형식": 형식, "만든날": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "가정": os.path.basename(가정경로) if 가정경로 else None,
         "구조지문": (R들["기준"].get("요약") or {}).get("구조지문")}
    낸["성장출처"] = 성장출처검사(R들, 축, 신)
    낸["효율성장"] = 효율성장검사(R들, 축, 신)
    낸["역사밴드"] = 역사밴드검사(R들, 축, 신)
    낸["단위"] = 단위검사받기(가정경로, 신)
    if 격자:
        try:
            낸["격자"] = 격자검산(가정, 신)
        except Exception as e:                       # noqa: BLE001
            낸["격자"] = {"건너뜀": "격자를 못 냈다 — %s" % ("%s" % e)[:120]}
    else:
        낸["격자"] = {"건너뜀": "--격자없이"}
    낸["신선도"] = 신선도검사(가정, 가정경로, 신)
    # master check — 이 도구 + 신호 파일 목록의 경보
    raw = os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw") if 가정경로 else None
    파일들 = 신호파일.읽기(raw) if raw else []
    파일경보 = {x["이름"]: sum(1 for s in x["신호"] if s.get("등급") == "경보") for x in 파일들 if x["이름"] != "닫힘검사.json"}
    내경보 = sum(1 for s in 신호 if s["등급"] == "경보")
    단위경보 = (낸["단위"].get("경보") or 0) if 낸["단위"].get("있음") else 0
    낸["master"] = {"이도구_경보": 내경보, "신호파일_경보": 파일경보, "신호파일_경보합": sum(파일경보.values()), "단위_경보": 단위경보,
                  "닫힘": 내경보 == 0 and sum(파일경보.values()) == 0,
                  "뜻": "닫힘 = 이 도구의 경보 0 ∧ 신호 파일 경보 0. 자체검사 · 모순 장부 · 15번 판정은 따로다(이 값이 그것을 대신하지 않는다)"}
    낸["신호"] = 신호
    return 낸, ""


def 쓰기(낸, 가정경로, 낼=None):
    p = 낼 or os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw", "닫힘검사.json")
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with io.open(p, "w", encoding="utf-8") as f:
        json.dump(낸, f, ensure_ascii=False, indent=1, default=str)
    return p


def 표찍기(낸):
    m = 낸["master"]
    print("닫힘검사 — master %s (이 도구 경보 %d · 신호 파일 경보 %d · 단위 경보 %d)" % ("닫힘" if m["닫힘"] else "열림", m["이도구_경보"], m["신호파일_경보합"], m["단위_경보"]))
    for 시, h in (낸["성장출처"] or {}).items():
        if isinstance(h, dict) and "판정" in h:
            print("  성장 출처 %s — %s(Δln 매출 %.3f = 물량 %.3f + 가격 %.3f · Δ마진 %s · ΔCAPEX비율 %s)" % (
                시, h["판정"], h["Δln매출"], h["Δln물량"], h["Δln가격"], ("%+.2f%%p" % (h["Δ영업이익률"] * 100)) if h["Δ영업이익률"] is not None else "-",
                ("%+.2f%%p" % (h["ΔCAPEX비율"] * 100)) if h["ΔCAPEX비율"] is not None else "-"))
    e = 낸["효율성장"]
    if "NOPLAT성장률" in e:
        print("  효율 성장 — NOPLAT %.1f%% = 재투자율 %.2f × ROIC %.1f%%(%.1f%%) + 효율 %.1f%%p(마진 %s · 회전 %s)" % (
            e["NOPLAT성장률"] * 100, e["재투자율"], e["기초ROIC"] * 100, e["펀더멘털성장"] * 100, e["효율성장항"] * 100,
            ("%+.1f%%/년" % (e["마진개선률_연"] * 100)) if e["마진개선률_연"] is not None else "-", ("%+.1f%%/년" % (e["회전개선률_연"] * 100)) if e["회전개선률_연"] is not None else "-"))
    for 이름, b in 낸["역사밴드"].items():
        if "실적범위" in b:
            print("  역사 밴드 %s — 실적 %.3f~%.3f · 밖 %s · 멀리 %s" % (이름, b["실적범위"][0], b["실적범위"][1], b["밖"] or "-", b["멀리"] or "-"))
    g = 낸.get("격자") or {}
    for k in ("표1", "표2"):
        if k in g:
            print("  격자 %s 가운데 %s (주당 %s)" % (k, g[k].get("가운데"), g.get("주당가치")))
    for s in 낸["신호"]:
        print("  [%s] %s — %s: %s" % (s["등급"], s["종류"], s["대상"], s["글"]))


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description=__doc__.split("\n")[0])
    ap.add_argument("가정")
    ap.add_argument("--낼")
    ap.add_argument("--격자없이", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(a.가정):
        print("가정 파일이 없다: %s" % a.가정)
        return 입력오류
    try:
        가정 = json.load(io.open(a.가정, encoding="utf-8"))
    except ValueError as e:
        print("가정 JSON 파손 — %s" % e)
        return 입력오류
    낸, 까 = 분석(가정, a.가정, 격자=not a.격자없이)
    if 낸 is None:
        print("입력 오류 — %s" % 까)
        return 입력오류
    print("→ %s" % 쓰기(낸, a.가정, a.낼))
    표찍기(낸)
    return 발견 if 낸["master"]["이도구_경보"] else 통과


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""원형판정 — 회사의 **재무 지문**으로 회사 유형 원형(`원형.json` — 열둘)의 후보 2~3개를 세우고, 후보마다 출발할 구조 블록과 채울 가정 칸을 낸다
(2026-10-23 · 연구/동인연동_업그레이드_연구.md P3 · R5 업종 원형). **사람이 고른다** — 도구는 후보와 까닭만 낸다.

    python 스크립트/원형판정.py 가정.json                      # 원천 13번의 마지막 회계연도로 지문 → _raw/원형판정.json
    python 스크립트/원형판정.py 가정.json --패널               # 패널(기저율) 행도 읽어 같은 집단 백분위를 붙인다
    python 스크립트/원형판정.py --지문 "유형자산÷매출=0.9,상각÷매출=0.12,매출원가율=0.72,재고일수=60"   # 가정 없이

지문 일곱 — 유형자산 ÷ 매출 · 감가상각 ÷ 매출 · 매출원가율 · 재고일수 · 매출채권일수 · 매입채무일수 · 영업이익률(원천 17 · 77 · 62 · 63 · 11 · 10 · 34 · 66). 원형마다 지문 범위(판단 초안 —
근거강도 「추정」)가 있다. 2026-10-23 밤(연구/레터워크북_최적화_20261023/03 4-1) 점수를 **특이도 가중**으로 바꿨다 — 다섯 회사 중 넷이 범위가 넓은
원형(파이프라인)에 100% 로 몰렸다. 지금 꼴:
  · 지문 = 최근 3 회계연도(사이클 회사 5)의 해마다 비율의 **중앙값** — 정점 한 해에 흔들리지 않게
  · 값이 없거나 매출원가가 0(기능별로 매출원가를 따로 표시하지 않는 회사)이면 그 변수 · 원가를 분모로 쓰는 변수는 「본 변수」에서 뺀다
  · 변수 k 의 흔함 p_k = 같은 집단(패널)에서 그 범위에 드는 비율 · 패널이 없으면 라이브러리 전체 범위 폭(또는 `_지문.기준폭`)에서 그 범위가 차지하는 몫
  · 근거점수 = Σ [범위 안이면 ln(0.95 ÷ p_k) · 밖이면 ln(0.05 ÷ (1 − p_k))] — 원형 대 모집단의 우도비(naive Bayes · Hand & Yu 2001)
  · 점수(표시) = 맞은 변수의 정보량(−ln p_k) ÷ 본 변수의 정보량 — 넓은 범위 하나 맞은 것은 거의 세지 않는다
  · 본 변수가 셋 미만인 원형은 후보에서 뺀다(모두 빠지면 근거점수 위 둘 + 「지문 부족」 참고)
  · 원형 하나가 지문 무리 둘 이상을 품으면 `지문꼴[]` 로 상자를 더 둔다 — 근거점수 · 맞은 변수는 가장 잘 맞는 꼴(하위 무리)의 것(`맞은꼴`).
    2026-11-14 조립 제조에 「설계 · 외주 생산 중심」 꼴(사람이 확인한 정답 34곳으로 잰 판정 시험)
  · 원형의 `경계`(사람이 정한 경계 기준 한 줄)는 후보에 실어 고르는 사람이 읽게 한다 — 점수에는 들지 않는다
  · 2026-11-15 — 가정 곁 `_raw/동인원천.json`(A3 — 사업보고서 · 10-K 글과 수주잔고로 낸 회사 유형)이 있으면 `원형.json` 의 `_A3대응` 으로
    원형에 이어 **대응한 원형 안에서만** 후보를 세운다. 그 안의 순서는 지문 근거점수이고, 수주잔고 ÷ 연환산 매출이 `수주잔고문턱`(2.0) 이상이면
    수주 산업이 앞. 지문만으로는 네 변수 범위가 겹치는 원형(조립 · 수주 · 유통)을 못 가른다. 재무 지문만의 후보는 `지문후보` 에 나란히 둔다.
    A3 가 없거나 대응이 비면 종전과 같다(`--지문만` 으로 끈다)
같은 근거점수면 구조가 이미 선언된 갈래(능력 · 저량 · 설비계수 …)와 닮은 쪽이 앞. 후보마다 원형의
구조 묶음 · KPI 자리(출처) · 2차 연동 기본 · 출발 템플릿 · 채울 가정 칸(그 구조로 동인 그래프를 세워 손잡이를 모은 것 — 엔진 틀의 기본값으로 메운 임시 구조)을 낸다.
업종(KSIC · SIC) ↔ 원형 대응표는 없다 — 범용. 회사 · 업종 이름이 코드에 없다. 신호는 「후보 — 사람이 고른다」 · 「지문을 못 냈다」 참고와,
가정 `메타.원형` 이 원형 라이브러리 이름이 아닐 때의 「원형 이름 밖」 경보(2026-11-15 — 자체검사 51 이 읽는다)뿐이다(값을 정하지 않는다).
종료 코드 — 0 · 2 입력 오류.
"""
from __future__ import annotations

import argparse
import datetime
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
from 종료코드 import 통과, 입력오류                  # noqa: E402

원형경로 = os.path.join(여기, "원형.json")
출처이름 = "원형판정"
형식 = "원형판정 1"
원천번호 = {"유형자산": "17", "감가상각비": "77", "매출": "62", "매출원가": "63", "재고": "11", "매출채권": "10", "매입채무": "34", "영업이익": "66"}


def 원형읽기(p=None):
    return json.load(io.open(p or 원형경로, encoding="utf-8"))


def _수(v):
    try:
        return None if (v is None or isinstance(v, bool)) else float(v)
    except (TypeError, ValueError):
        return None


def _해지문(원, c):
    """한 회계연도 열 c 의 지문(비율 여섯). 매출원가가 0 이하면 매출원가율 · 재고일수 · 매입채무일수를 내지 않는다(표시하지 않은 것)."""
    def v(k):
        return _수((원.get(원천번호[k]) or {}).get(c))
    S, 원가 = v("매출"), v("매출원가")
    지 = {}
    if not (S and S > 0):
        return 지
    if v("유형자산") is not None:
        지["유형자산÷매출"] = v("유형자산") / S
    if v("감가상각비") is not None:
        지["상각÷매출"] = abs(v("감가상각비")) / S
    if v("매출채권") is not None:
        지["채권일수"] = v("매출채권") / S * 365
    if v("영업이익") is not None:
        지["영업이익률"] = v("영업이익") / S
    if 원가 is not None and 원가 > 0:
        지["매출원가율"] = 원가 / S
        if v("재고") is not None:
            지["재고일수"] = v("재고") / 원가 * 365
        if v("매입채무") is not None:
            지["매입채무일수"] = v("매입채무") / 원가 * 365
    return 지


def 사이클인가(가정):
    """메타.생애주기(단계 「사이클」 · 덧표지 「경기순환」) 또는 구조의 정상화 계단 — 지문 창을 다섯 해로."""
    생 = ((가정 or {}).get("메타") or {}).get("생애주기") or {}
    if isinstance(생, dict):
        if "사이클" in ("%s" % (생.get("단계") or "")) or any("순환" in ("%s" % x) or "사이클" in ("%s" % x) for x in (생.get("덧표지") or [])):
            return True
    return bool(((가정 or {}).get("구조") or {}).get("정상화계단"))


def _중앙(v):
    v = sorted(v)
    n = len(v)
    return None if not n else (v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0)


def 지문짓기(가정, 해수=None):
    """원천 13번의 최근 회계연도들(기본 3 · 사이클 회사 5)의 해마다 지문 → 변수마다 중앙값. → (지문, 쓴 열 글) 또는 ({}, None)."""
    원 = (가정 or {}).get("원천") or {}
    매 = 원.get(원천번호["매출"]) or {}
    열들 = sorted(c for c, v in 매.items() if isinstance(c, str) and c.startswith("FY") and _수(v))
    if not 열들:
        return {}, None
    n = 해수 or (5 if 사이클인가(가정) else 3)
    쓴 = 열들[-n:]
    모 = {}
    for c in 쓴:
        for k, x in _해지문(원, c).items():
            모.setdefault(k, []).append(x)
    지 = {k: _중앙(v) for k, v in 모.items() if v}
    if not 지:
        return {}, None
    return 지, (쓴[0] if len(쓴) == 1 else "%s~%s 중앙값(%d해)" % (쓴[0], 쓴[-1], len(쓴)))


def 지문글풀기(글):
    지 = {}
    for 토 in (글 or "").split(","):
        if "=" in 토:
            k, v = 토.split("=", 1)
            if _수(v) is not None:
                지[k.strip()] = float(v)
    return 지


def 구조닮음(원형, 구):
    """가정의 구조가 원형의 묶음과 닮은 정도 — 선언된 갈래 몇이 맞나(동점 가르기용)."""
    if not isinstance(구, dict):
        return 0
    점 = 0
    o = 원형["구조"]
    구분 = (구.get("매출구분") or [{}])[0] if 구.get("매출구분") else {}
    if 구분.get("판매량산정") and 구분["판매량산정"] in (o.get("매출구분") or {}).get("판매량산정", ""):
        점 += 1
    if 구분.get("단가경로") and 구분["단가경로"] in (o.get("매출구분") or {}).get("단가경로", ""):
        점 += 1
    산식들 = {x.get("산식") for x in (구.get("원가줄") or []) if isinstance(x, dict)}
    if any(s and s in (o.get("원가줄") or {}).get("주", "") for s in 산식들):
        점 += 1
    if ((구.get("투자") or {}).get("유지규칙") or "") in (o.get("투자") or {}).get("유지규칙", "") and (구.get("투자") or {}).get("유지규칙"):
        점 += 1
    return 점


def 채울칸(가정, 원형):
    """원형의 템플릿 구조로 동인 그래프를 세워 손잡이(가정 번호)를 모은다 — 「이 원형으로 가면 채울 칸」. 못 세우면 []."""
    try:
        import 동인그래프 as DG                               # noqa: PLC0415
        뿌리 = os.path.dirname(여기)
        이름 = (원형.get("템플릿") or "").split("(")[0].strip()
        p = os.path.join(뿌리, 이름)
        if not os.path.exists(p):
            return []
        틀 = json.load(io.open(p, encoding="utf-8"))
        가 = dict(틀)
        for k in ("메타", "기간", "스위치"):
            if isinstance((가정 or {}).get(k), dict):
                가[k] = 가정[k]
        가["구조"] = 틀["구조"]
        G = DG.그래프(DG.판(가)).짓기()
        손 = sorted({h for e in G.엣지 for h in e["손잡이"]}, key=lambda a: int(a[2:]))
        return [{"번호": h[2:], "이름": G.노드[h]["이름"], "단위": G.노드[h]["단위"]} for h in 손]
    except Exception:                                # noqa: BLE001
        return []


_최소본변수 = 3


def 강도(근거점수):
    """근거점수(ln 우도비 합) → 말 — 3 넘으면 강함(우도비 20배 넘음) · 1~3 보통 · 0~1 약함 · 0 이하 없음."""
    return "강함" if 근거점수 > 3 else "보통" if 근거점수 > 1 else "약함" if 근거점수 > 0 else "없음"
_원형안 = 0.95         # 그 원형의 회사가 원형 범위 안에 들 확률(범위를 90~95% 구간으로 그었다는 판단) — 우도비의 분자. 0.9 이면 원가 구조가 어긋난 원형이 3위에 남았다(손 지문 시험 C3)


def 흔함(라이브러리):
    """패널이 없을 때의 p_k — 변수마다 라이브러리 전체 범위(모든 원형 범위의 합집합 폭)에서 이 범위가 차지하는 몫."""
    폭 = {}
    기준 = ((라이브러리.get("_지문") or {}).get("기준폭") or {})
    for o in 라이브러리["원형"]:
        for k, (lo, hi) in (o.get("지문") or {}).items():
            a, b = 폭.get(k, (lo, hi))
            폭[k] = (min(a, lo), max(b, hi))
    for k, v in 기준.items():                          # 기준 폭이 있는 변수는 그 폭이 모집단 폭이다(원형 범위는 그 안으로 자른다) — 한 원형만 둔 변수의 p 가 1 에 붙지 않게
        if isinstance(v, list) and len(v) == 2 and v[1] > v[0]:
            폭[k] = (v[0], v[1])

    def p(k, 범, 패널값=None):
        v = (패널값 or {}).get(k)
        if v and len(v) >= 30:
            q = sum(1 for x in v if 범[0] <= x <= 범[1]) / float(len(v))
            출 = "패널"
        else:
            lo, hi = 폭.get(k, 범)
            q = (min(범[1], hi) - max(범[0], lo)) / float(hi - lo) if hi > lo else 1.0
            출 = "라이브러리 폭"
        return min(0.98, max(0.02, q)), 출
    return p


def _상자근거(범, 지, p, 패널값):
    """지문 상자 하나(변수 → [하, 상])의 근거점수(Σ ln 우도비) · 본 변수 · 맞은 변수 · 정보량 · 흔함 출처."""
    본 = [k for k in 범 if k in 지]
    맞 = [k for k in 본 if 범[k][0] <= 지[k] <= 범[k][1]]
    정보, 근거, 출처 = {}, 0.0, set()
    for k in 본:
        q, 출 = p(k, 범[k], 패널값)
        출처.add(출)
        정보[k] = -math.log(q)
        근거 += math.log(_원형안 / q) if k in 맞 else math.log((1 - _원형안) / (1 - q))
    return {"근거": 근거, "본": 본, "맞": 맞, "정보": 정보, "출처": 출처, "범": 범}


def 원형근거(원, 지, p, 패널값=None):
    """원형 하나의 근거 — 기본 `지문` 과 `지문꼴[]`(2026-11-14) 상자마다 근거를 내고 **가장 잘 맞는 꼴**의 것을 쓴다(꼴은 그 원형의 하위 무리다 —
    같은 무게 혼합(우도비 평균)은 꼴 하나만 맞는 전형 회사의 근거를 ln(꼴 수)만큼 깎아 꼴이 없는 원형과의 동점을 잃게 했다). 본 변수가 `_최소본변수`
    미만인 꼴은 고르지 않는다(모두 미만이면 기본 상자). 꼴이 없으면 종전과 같다."""
    상자들 = [dict(_상자근거(원.get("지문") or {}, 지, p, 패널값), 꼴="기본")]
    for j, c in enumerate(원.get("지문꼴") or []):
        상자들.append(dict(_상자근거(c.get("지문") or {}, 지, p, 패널값), 꼴=c.get("꼴") or "꼴 %d" % (j + 2)))
    쓸 = [s for s in 상자들 if len(s["본"]) >= _최소본변수] or 상자들[:1]
    return dict(max(쓸, key=lambda s: s["근거"]), 꼴수=len(쓸))


def A3읽기(가정경로=None, raw=None):
    """A3(동인원천)의 회사 유형 판정 — `_raw/동인원천.json` 의 유형.판정 · 유형.신호.수주잔고÷매출(없으면 `_raw/매출구분판정.json` 의 유형).
    → {"판정": [유형 이름], "수주잔고÷매출": 수 또는 None, "출처": 파일 이름} · 둘 다 없거나 깨졌으면 None (2026-11-15)."""
    d = raw or (os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw") if 가정경로 else None)
    if not d:
        return None
    for 이름 in ("동인원천.json", "매출구분판정.json"):
        p = os.path.join(d, 이름)
        if not os.path.exists(p):
            continue
        try:
            u = (json.load(io.open(p, encoding="utf-8")) or {}).get("유형")
        except (ValueError, OSError, AttributeError):
            continue
        비 = None
        if isinstance(u, dict):
            비 = _수((u.get("신호") or {}).get("수주잔고÷매출"))
            u = u.get("판정")
        판 = [x for x in (u if isinstance(u, list) else [u]) if isinstance(x, str) and x.strip()]
        if 판:
            return {"판정": 판, "수주잔고÷매출": 비, "출처": "_raw/" + 이름}
    return None


def A3원형(A3, L):
    """A3 유형 → 대응 원형 이름(차례 유지 · 중복 없음) — `원형.json` 의 `_A3대응.대응`. 대응이 없으면 []."""
    대 = ((L or {}).get("_A3대응") or {}).get("대응") or {}
    낸 = []
    for t in (A3 or {}).get("판정") or []:
        for o in 대.get(t) or []:
            if o not in 낸:
                낸.append(o)
    return 낸


def 판정(가정, 지문=None, 라이브러리=None, 패널백분위=None, 패널값=None, A3=None):
    L = 라이브러리 or 원형읽기()
    지, 열 = (지문, "--지문") if 지문 else 지문짓기(가정 or {})
    p = 흔함(L)
    신호 = []
    후보 = []
    for 원 in L["원형"]:
        s = 원형근거(원, 지, p, 패널값)
        범, 본, 맞, 정보, 근거, 출처 = s["범"], s["본"], s["맞"], s["정보"], s["근거"], s["출처"]
        합 = sum(정보.values())
        점 = (sum(정보[k] for k in 맞) / 합) if 합 > 0 else 0.0
        후보.append({"원형": 원["이름"], "뜻": 원["뜻"], "경계": 원.get("경계"), "점수": round(점, 3), "근거점수": round(근거, 3), "근거강도등급": 강도(근거),
                   "맞은꼴": s["꼴"], "꼴수": s["꼴수"],
                   "정보량": {k: round(v, 3) for k, v in 정보.items()}, "흔함출처": sorted(출처), "맞은변수": 맞, "본변수": 본,
                   "어긋난변수": [{"변수": k, "값": 지[k], "범위": 범[k]} for k in 본 if k not in 맞],
                   "구조닮음": 구조닮음(원, (가정 or {}).get("구조")), "구조": 원["구조"], "KPI": 원["KPI"], "이차연동기본": 원["이차연동기본"],
                   "템플릿": 원.get("템플릿"), "근거": 원.get("근거"), "근거강도": "추정(지문 범위는 판단 초안)"})
    후보.sort(key=lambda x: (-x["근거점수"], -x["구조닮음"], -len(x["본변수"])))
    자격 = [x for x in 후보 if len(x["본변수"]) >= _최소본변수]
    상위 = [x for x in 자격 if x["근거점수"] > 0][:3]
    if len(상위) < 2:
        상위 = (상위 + [x for x in 자격 if x not in 상위])[:2] if len(자격) >= 2 else 후보[:2]
    지문상위 = list(상위)
    지문후보 = [x["원형"] for x in 지문상위]
    부족 = len(자격) < 2
    # 2026-11-15 — A3 유형(글 · 수주잔고)이 있으면 대응한 원형 안에서만 후보를 세운다. 그 안의 순서는 지문 근거점수 ·
    #   수주잔고 ÷ 연환산 매출이 `_A3대응.수주잔고문턱` 이상이면 수주 산업이 앞. 지문으로는 범위가 겹치는 원형을 못 가른다
    대응 = A3원형(A3, L)
    수주앞 = False
    if 대응:
        좁 = [x for x in 후보 if x["원형"] in 대응]
        문 = _수(((L.get("_A3대응") or {}).get("수주잔고문턱")))
        if 문 is not None and _수((A3 or {}).get("수주잔고÷매출")) is not None and A3["수주잔고÷매출"] >= 문 and any(x["원형"] == "수주 산업" for x in 좁):
            좁.sort(key=lambda x: x["원형"] != "수주 산업")
            수주앞 = True
        상위 = 좁[:3]
        if len(상위) < 2:
            상위 += [x for x in (자격 or 후보) if x not in 상위][:2 - len(상위)]
    for x in 후보:
        x["A3대응"] = x["원형"] in 대응
    for x in 상위:
        x["채울칸"] = 채울칸(가정, next(o for o in L["원형"] if o["이름"] == x["원형"]))
    if not 지:
        신호.append({"출처": 출처이름, "종류": "지문 없음", "대상": "원천 13번", "값": None, "문턱": None,
                   "글": "원천 13번에 회계연도 매출 · 유형자산 · 매출원가 · 재고 · 채권이 없어 지문을 못 냈다 — `--지문` 으로 주거나 원천을 채운다", "등급": "참고"})
    if 대응:
        신호.append({"출처": 출처이름, "종류": "원형 후보(A3 유형으로 좁힘)", "대상": "구조", "값": [x["원형"] for x in 상위], "문턱": "사람이 고른다",
                   "글": "A3 유형(%s · %s%s)이 대응하는 원형(%s) 안에서 세운 후보 — %s. 그 안의 순서는 재무 지문 근거점수%s. 재무 지문만의 후보는 %s. 고르는 것은 사람"
                         % (" · ".join(A3["판정"]), A3.get("출처"), (" · 수주잔고 ÷ 연환산 매출 %.2f" % A3["수주잔고÷매출"]) if A3.get("수주잔고÷매출") is not None else "",
                            " · ".join(대응), " · ".join(x["원형"] for x in 상위),
                            " — 수주잔고가 매출 %.1f해치 이상이라 수주 산업을 앞에 둠" % 문 if 수주앞 else "", " · ".join(지문후보) or "없음"), "등급": "참고"})
    if 지:
        신호.append({"출처": 출처이름, "종류": "원형 후보", "대상": "구조", "값": 지문후보, "문턱": "사람이 고른다",
                   "글": "재무 지문(%s · %s)으로 세운 원형 후보 — %s. 점수는 맞은 변수의 정보량 몫(흔한 범위는 적게 센다). 부문이 여럿이면 부문마다 판정한다. 값이 아니라 배선 묶음이다 — 고르는 것은 사람"
                         % (열, " · ".join("%s %.3g" % (k, v) for k, v in 지.items()), " · ".join("%s(%.0f%% · 근거 %s)" % (x["원형"], x["점수"] * 100, x["근거강도등급"]) for x in 지문상위)), "등급": "참고"})
        if 부족:
            신호.append({"출처": 출처이름, "종류": "지문 부족", "대상": "구조", "값": len(지), "문턱": _최소본변수,
                       "글": "지문 변수가 원형마다 %d개 미만이라(매출원가를 따로 표시하지 않는 회사 따위) 판정이 약하다 — 후보는 근거점수 위 둘. 구조는 사업 서술로 고른다" % _최소본변수,
                       "등급": "참고"})
        elif not any(x["근거점수"] > 0 for x in 지문상위):
            신호.append({"출처": 출처이름, "종류": "맞는 원형 없음", "대상": "구조", "값": 지문상위[0]["원형"], "문턱": "근거점수 > 0",
                       "글": "어느 원형도 모집단보다 이 지문을 더 잘 설명하지 못한다 — 라이브러리 밖 유형일 수 있다. 후보는 참고로만", "등급": "참고"})
    # 2026-11-15 — 가정 `메타.원형` 이 원형 라이브러리 이름이 아니면 경보(값은 바꾸지 않는다). 원형을 이름으로 찾는 곳(레터 원고의 업황 지표 ·
    #   경쟁 기준)이 그 원형을 못 찾아 모든 원형의 합집합으로 조용히 떨어진다. A3 유형 이름과 원형 이름이 섞여 들어가는 일이 있었다
    원이름 = [o["이름"] for o in L["원형"]]
    메원 = ((가정 or {}).get("메타") or {}).get("원형")
    for v in ([메원] if isinstance(메원, str) else (메원 if isinstance(메원, list) else [])):
        if isinstance(v, str) and v.strip() and v.strip() not in 원이름:
            제 = A3원형({"판정": [v.strip()]}, L) or [x["원형"] for x in 상위[:1]]
            신호.append({"출처": 출처이름, "종류": "원형 이름 밖", "대상": "메타.원형", "값": v, "문턱": "원형 라이브러리 이름 %d개" % len(원이름),
                       "글": "가정 메타.원형 「%s」 은 원형 라이브러리 이름이 아니다 — 원형을 이름으로 찾는 곳(레터 원고의 업황 지표 · 경쟁 기준)이 모든 원형의 "
                             "합집합으로 떨어진다. 라이브러리 이름(%s 등)으로 고치거나 비운다(값은 바꾸지 않는다)" % (v, " · ".join(제) or "원형 후보"), "등급": "경보"})
    낸 = {"형식": 형식, "만든날": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "지문": 지, "지문열": 열, "패널백분위": 패널백분위,
         "라이프사이클": L.get("_라이프사이클"), "메타생애주기": ((가정 or {}).get("메타") or {}).get("생애주기"),
         "점수식": "특이도 가중 — 근거점수 Σ ln 우도비(안 0.95 ÷ p · 밖 0.05 ÷ (1 − p)) · 점수 = 맞은 정보량 ÷ 본 정보량 · 본 변수 %d 미만 제외" % _최소본변수,
         "후보": 상위, "지문후보": 지문후보,
         "A3": (dict(A3, 대응원형=대응, 수주앞=수주앞) if A3 else None),
         "전체": [{k: x[k] for k in ("원형", "점수", "근거점수", "근거강도등급", "맞은변수", "본변수", "구조닮음", "A3대응")} for x in 후보], "신호": 신호}
    return 낸


_패널식 = {"유형자산÷매출": lambda r: r["유형자산"] / r["매출액"] if r.get("유형자산") is not None else None,
         "상각÷매출": lambda r: abs(r["감가상각비"]) / r["매출액"] if r.get("감가상각비") is not None else None,
         "매출원가율": lambda r: r["매출원가"] / r["매출액"] if r.get("매출원가") else None,
         "재고일수": lambda r: r["재고자산"] / r["매출원가"] * 365 if (r.get("재고자산") is not None and r.get("매출원가")) else None,
         "채권일수": lambda r: r["매출채권"] / r["매출액"] * 365 if r.get("매출채권") is not None else None,
         "매입채무일수": lambda r: r["매입채무"] / r["매출원가"] * 365 if (r.get("매입채무") is not None and r.get("매출원가")) else None,
         "영업이익률": lambda r: r["영업이익"] / r["매출액"] if r.get("영업이익") is not None else None}


def 패널값읽기(가정):
    """같은 집단(전체 · 마지막 패널 연도)의 지문 변수 값 목록 {변수: [값]} — 기저율 패널이 있을 때만. 없으면 None."""
    try:
        import 기저율 as 기                                   # noqa: PLC0415
        s = 기.설정읽기()
        국, s, _ = 기.국가맞춤(가정, s)
        if not 국:
            return None
        행, _ = 기.패널읽기(None, s)
        남, _ = 기.자료제외(행, s)
        끝 = max(r["연도"] for r in 남)
        rows = [r for r in 남 if r["연도"] == 끝 and r.get("매출액")]
        낸 = {}
        for k, f in _패널식.items():
            v = []
            for r in rows:
                try:
                    x = f(r)
                except (TypeError, ZeroDivisionError):
                    x = None
                if x is not None:
                    v.append(x)
            if len(v) >= 30:
                낸[k] = sorted(v)
        return 낸 or None, 끝
    except Exception:                                # noqa: BLE001
        return None


def 패널자리(가정, 가정경로, 지, 패널값=None, 연도=None):
    """같은 집단(전체)에서 지문 변수의 백분위 — 기저율 패널이 있을 때만. 없으면 None."""
    if 패널값 is None:
        r = 패널값읽기(가정)
        if not r:
            return None
        패널값, 연도 = r
    if not 패널값:
        return None
    낸 = {}
    for k, v in 패널값.items():
        if k in 지:
            낸[k] = {"백분위": round(sum(1 for x in v if x <= 지[k]) / len(v), 3), "관측수": len(v), "연도": 연도}
    return 낸 or None


def 쓰기(낸, 가정경로, 낼=None):
    p = 낼 or os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw", "원형판정.json")
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with io.open(p, "w", encoding="utf-8") as f:
        json.dump(낸, f, ensure_ascii=False, indent=1, default=str)
    return p


def 표찍기(낸):
    print("원형판정 — 지문(%s): %s" % (낸.get("지문열"), " · ".join("%s %.3g" % (k, v) for k, v in (낸["지문"] or {}).items()) or "없음"))
    if 낸.get("패널백분위"):
        print("  같은 집단 백분위: " + " · ".join("%s %.0f%%" % (k, v["백분위"] * 100) for k, v in 낸["패널백분위"].items()))
    if 낸.get("A3"):
        a3 = 낸["A3"]
        print("  A3 유형: %s(%s%s) → 원형 %s%s · 재무 지문만의 후보 %s" % (" · ".join(a3["판정"]), a3.get("출처"),
              (" · 수주잔고 ÷ 매출 %.2f" % a3["수주잔고÷매출"]) if a3.get("수주잔고÷매출") is not None else "", " · ".join(a3.get("대응원형") or []) or "대응 없음",
              " · 수주 산업 앞" if a3.get("수주앞") else "", " · ".join(낸.get("지문후보") or []) or "없음"))
    for i, x in enumerate(낸["후보"], 1):
        print("  후보 %d  %s — 점수 %.0f%% · 근거점수 %.2f(%s)(%s 맞음%s) · 구조 닮음 %d" % (i, x["원형"], x["점수"] * 100, x.get("근거점수", 0), x.get("근거강도등급"), " · ".join(x["맞은변수"]) or "없음",
                                                               (" · 어긋남 " + " · ".join("%s %.3g∉[%s~%s]" % (a["변수"], a["값"], a["범위"][0], a["범위"][1]) for a in x["어긋난변수"])) if x["어긋난변수"] else "", x["구조닮음"]))
        if x.get("맞은꼴") and x["맞은꼴"] != "기본":
            print("         맞은 지문꼴: %s" % x["맞은꼴"])
        if x.get("경계"):
            print("         경계: %s" % x["경계"])
        print("         구조: %s" % json.dumps(x["구조"], ensure_ascii=False)[:200])
        print("         KPI 자리: %s" % " / ".join("%s — %s" % (k["자리"], k["이름"]) for k in x["KPI"]))
        print("         2차 연동 기본: %s · 템플릿 %s · 채울 칸 %d개" % (" · ".join(x["이차연동기본"]), x.get("템플릿"), len(x.get("채울칸") or [])))
    for s in 낸["신호"]:
        print("  [%s] %s — %s" % (s["등급"], s["종류"], s["글"]))


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description=__doc__.split("\n")[0])
    ap.add_argument("가정", nargs="?")
    ap.add_argument("--지문")
    ap.add_argument("--패널", action="store_true")
    ap.add_argument("--지문만", action="store_true", help="A3 유형(_raw/동인원천.json)을 읽지 않고 재무 지문만으로 후보를 세운다")
    ap.add_argument("--낼")
    a = ap.parse_args()
    가정 = None
    if a.가정:
        if not os.path.exists(a.가정):
            print("가정 파일이 없다: %s" % a.가정)
            return 입력오류
        try:
            가정 = json.load(io.open(a.가정, encoding="utf-8"))
        except ValueError as e:
            print("가정 JSON 파손 — %s" % e)
            return 입력오류
    elif not a.지문:
        print("가정 파일이나 --지문 을 준다")
        return 입력오류
    지 = 지문글풀기(a.지문) if a.지문 else None
    백 = 값 = None
    if a.패널 and 가정:
        지0 = 지 or 지문짓기(가정)[0]
        r = 패널값읽기(가정)
        if r:
            값, 연 = r
            백 = 패널자리(가정, a.가정, 지0, 값, 연)
    a3 = None if (a.지문만 or not a.가정) else A3읽기(a.가정)
    낸 = 판정(가정, 지, None, 백, 값, a3)
    if a.가정:
        print("→ %s" % 쓰기(낸, a.가정, a.낼))
    표찍기(낸)
    return 통과


if __name__ == "__main__":
    sys.exit(main())

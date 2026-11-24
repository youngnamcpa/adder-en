# -*- coding: utf-8 -*-
"""정상화 — 사이클 · 정상 수준의 재료를 계산한다(S8-07 · S8-02, 2026-10-17).

  python 스크립트/정상화.py 가정.json                    # → 가정 곁 _raw/정상화.json · 표를 찍는다
  python 스크립트/정상화.py 가정.json --낼 경로.json
  python 스크립트/정상화.py 가정.json --관측넣기          # 가정 파일의 `관측.대상영업이익률`(비었을 때) · `관측.정상화` 에 재료를 적는다(값 칸은 안 건드린다)

하는 일 — 네트워크 없이 이미 받은 파일만 읽는다(A1 · A3 직후에 돈다)
  ① 관측 시계열 — `관측.대상영업이익률` → 앵커(`_raw/dart_앵커시계열.json` · 미국 `_raw/앵커_시계열.json`) → A3 `_raw/동인원천.json`
     (운전자본.영업이익률 · 매출연) → 원천 13번(62 · 66) 차례로, 네 해 이상인 첫 원천을 쓴다(모자라면 가장 긴 것). 매출은 그 해의 매출을
     가진 첫 원천에서 붙인다(매출 가중에 쓴다)
  ② 사이클 신호 — A3 `국면()` 과 같은 자(S6 결정 ①): 네 해 이상 · 영업이익률 폭 10%p 이상 · 매출 증감 부호 전환(±3% 평탄)이나
     영업이익률 5%p 넘는 방향 전환이 둘 이상. 여기에 A3 국면(`사이클` 칸) · `메타.생애주기.덧표지`(경기순환 · 원자재) · 옛 자(영업이익률
     부호 전환 2회)를 겹친다 — 하나라도 서면 사이클이다(`사이클판정`). 자체검사 ㊲ · ㉝ 예외 · ⓪ ② · ⑥ 이 이 한 함수를 쓴다
  ③ 사이클 블록 — **매출 고점에서 다음 매출 고점까지**(고점 = 다음 해 매출이 3% 넘게 줄어드는 해). 블록마다 매출가중 영업이익률 ·
     매출총이익률 · 산술평균을 내고, 첫 고점 앞 · 마지막 고점 뒤는 「미완」으로 표에만 싣는다(평균에서 뺀다). 마지막 고점 뒤가 이미 저점과
     그 고점을 넘는 회복을 다 겪었으면 「저점 · 고점을 겪음 — 별도 판정」을 단다
  ④ 사이클끼리는 같은 무게 — 완결 블록들의 매출가중 영업이익률의 산술평균이 「사이클 평균」이다. 전체 해 산술평균 · 매출가중도 병기한다
  ⑤ 운영 동종 정상 마진 — `관측.운영동종.지표.정상영업이익률.값` 의 중앙값(C2)
  ⑥ 제안(고르지 않는다) — 213(대조 기준값) 후보 = 사이클 평균(사이클이면) · 운영 동종 정상 마진 · 전체 매출가중, 950 · 951 후보 = 완결 블록
     평균의 최소 · 최대(사이클 평균과 운영 동종을 함께 품게 넓힌다). 사람이 근거와 함께 고른다(「정규화 마진의 준거는 여럿을 나란히」)
`사이클연수` 는 같은 고점 자로 저점까지 찾아 고점 → 저점(하강) · 저점 → 고점(상승) 연수를 낸다 — 거친 바퀴의 고점구간 · 도달연도 근거 범위(S9R2).
구조 블록(사업 구조가 바뀐 해 뒤만 쓰는 블록)은 `관측.구조블록시작연도` 가 있으면 그 해 앞을 표에서 「구조 전」으로 표시하고 평균에서 뺀다.
  ⑦ 통계 제안(2026-10-21 — 파일이 있을 때만) — `_raw/변화점.json`(PELT)의 「구조 변화 후보」 · 구조블록시작연도 제안과
     `_raw/국면.json`(HMM)의 평가기준일 국면 확률 · 정점 영구화 금지 제안을 `통계제안` 에 나란히 싣는다. **고르지 않는다** —
     `관측.구조블록시작연도` 를 바꾸는 것은 사람이고, 바꾸지 않으면 표 · 평균은 종전 그대로다
회사 · 업종 이름은 이 도구에 한 글자도 없다.
"""
import argparse
import copy
import io
import json
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

해최소 = 4                 # A3 국면과 같은 자 — 네 해 미만이면 사이클을 판정하지 않는다
폭문턱 = 0.10              # 영업이익률 폭 10%p
평탄 = 0.03                # 매출 증감 ±3% 안은 평탄(부호를 세지 않는다)
이익전환문턱 = 0.05        # 영업이익률 5%p 넘는 방향 전환
고점하락 = 0.03            # 고점 = 다음 해 매출이 3% 넘게 줄어드는 해
국면표지 = ("경기순환", "원자재")
앵커이름 = ("dart_앵커시계열.json", "앵커_시계열.json")


def _수(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _해(글):
    m = re.search(r"(19|20)(\d{2})", "%s" % (글 or ""))
    return int(m.group(0)) if m else None


def 파일찾기(이름, 가정경로=None):
    """갈래 산출물 — 가정 곁 `_raw/` → 가정 폴더 → 위 폴더 `_raw/` → 작업 폴더 `_raw/`. (내용, 경로) 또는 (None, None)."""
    후보 = []
    if 가정경로:
        d = os.path.dirname(os.path.abspath(가정경로))
        후보 += [os.path.join(d, "_raw", 이름), os.path.join(d, 이름), os.path.join(os.path.dirname(d), "_raw", 이름)]
    후보.append(os.path.join(os.getcwd(), "_raw", 이름))
    for p in 후보:
        if os.path.exists(p):
            try:
                return json.load(io.open(p, encoding="utf-8")), p
            except (OSError, ValueError):
                return None, p
    return None, None


# ────────────────────────────────────────────────────────────── ① 관측 시계열

def _관측키(가정):
    v = (가정.get("관측") or {}).get("대상영업이익률")
    목록 = v.get("값") if isinstance(v, dict) else v
    낸 = []
    for x in 목록 or []:
        if isinstance(x, dict):
            값 = next((x[k] for k in ("값", "영업이익률", "마진") if _수(x.get(k))), None)
            if 값 is not None:
                낸.append({"해": _해(x.get("라벨") or x.get("이름") or x.get("해")), "영업이익률": float(값),
                          "매출": x.get("매출") if _수(x.get("매출")) else None})
        elif _수(x):
            낸.append({"해": None, "영업이익률": float(x), "매출": None})
    return 낸


def _앵커(가정경로):
    j, p = 파일찾기("dart_앵커시계열.json", 가정경로)
    낸 = []
    if isinstance(j, dict) and isinstance(j.get("해"), list):
        import 앵커읽기                                       # noqa: PLC0415
        for h in j["해"]:
            y, m, r = 앵커읽기.해마진(h)
            if m is not None:
                낸.append({"해": int(y), "영업이익률": m, "매출": r if _수(r) else None})
        return sorted(낸, key=lambda x: x["해"]), p
    j, p = 파일찾기("앵커_시계열.json", 가정경로)
    if isinstance(j, dict) and isinstance(j.get("표"), list):
        for r in j["표"]:
            if _수(r.get("영업이익률")):
                gpm = None
                if _수(r.get("매출")) and _수(r.get("매출원가")) and r["매출"]:
                    gpm = 1 - r["매출원가"] / r["매출"]
                낸.append({"해": _해(r.get("사업연도")), "영업이익률": r["영업이익률"], "매출": r.get("매출") if _수(r.get("매출")) else None,
                          "매출총이익률": gpm})
        return sorted([x for x in 낸 if x["해"]], key=lambda x: x["해"]), p
    return [], None


def _동인원천(가정경로):
    j, p = 파일찾기("동인원천.json", 가정경로)
    운 = ((j or {}).get("운전자본") or {}) if isinstance(j, dict) else {}
    마, 매 = 운.get("영업이익률") or {}, 운.get("매출연") or {}
    낸 = []
    if isinstance(마, dict):
        for c, v in 마.items():
            if ("%s" % c).startswith("FY") and _수(v):
                낸.append({"해": _해(c), "영업이익률": v, "매출": 매.get(c) if isinstance(매, dict) and _수(매.get(c)) else None})
    국면 = [x for x in (운.get("국면") or []) if isinstance(x, dict)] if isinstance(운, dict) else []
    return sorted([x for x in 낸 if x["해"]], key=lambda x: x["해"]), (p if 낸 else None), 국면


def _원천(가정):
    원 = 가정.get("원천") or {}
    매, 영 = 원.get("62") or {}, 원.get("66") or {}
    원가, 판 = 원.get("63") or {}, 원.get("65") or {}
    낸 = []
    for c, r in 매.items():
        if not ("%s" % c).startswith("FY") or not _수(r) or not r:
            continue
        o = 영.get(c)
        if not _수(o) and _수(원가.get(c)):
            o = r - 원가[c] - (판.get(c) or 0.0)
        if _수(o):
            gpm = (1 - 원가[c] / r) if _수(원가.get(c)) else None
            낸.append({"해": _해(c), "영업이익률": o / r, "매출": r, "매출총이익률": gpm})
    return sorted([x for x in 낸 if x["해"]], key=lambda x: x["해"])


def 관측시계열(가정, 가정경로=None):
    """{"해": [{해 · 영업이익률 · 매출 · 매출총이익률}], "출처": 글, "원천들": {이름: 해 수}, "국면": A3 국면 표}."""
    키 = _관측키(가정)
    앵, 앵곳 = _앵커(가정경로)
    a3, a3곳, 국면 = _동인원천(가정경로)
    원 = _원천(가정)
    원천들 = [("관측.대상영업이익률", 키), ("앵커 %s" % os.path.basename(앵곳 or ""), 앵), ("A3 동인원천 운전자본.영업이익률", a3), ("원천 13번 62 · 66", 원)]
    고른 = next(((n, v) for n, v in 원천들 if len(v) >= 해최소), None) or max(원천들, key=lambda x: len(x[1]))
    해들 = [dict(x) for x in 고른[1]]
    매출원 = {}
    for _n, v in 원천들[1:] + 원천들[:1]:
        for x in v:
            if x.get("해") and _수(x.get("매출")):
                매출원.setdefault(x["해"], x["매출"])
            if x.get("해") and _수(x.get("매출총이익률")):
                매출원.setdefault(("gpm", x["해"]), x["매출총이익률"])
    for x in 해들:
        if not _수(x.get("매출")) and x.get("해") in 매출원:
            x["매출"] = 매출원[x["해"]]
        if not _수(x.get("매출총이익률")) and ("gpm", x.get("해")) in 매출원:
            x["매출총이익률"] = 매출원[("gpm", x["해"])]
    return {"해": 해들, "출처": 고른[0], "원천들": {n: len(v) for n, v in 원천들}, "국면": 국면}


# ────────────────────────────────────────────────────────────── ② 사이클 신호

def _뒤집힘(값들, 문턱):
    if len(값들) < 3:
        return 0
    방향, 극, 수 = 0, 값들[0], 0
    위 = 아래 = 값들[0]
    for x in 값들[1:]:
        if 방향 == 0:
            위, 아래 = max(위, x), min(아래, x)
            if x - 아래 > 문턱:
                방향, 극 = 1, x
            elif 위 - x > 문턱:
                방향, 극 = -1, x
        elif 방향 == 1:
            if x > 극:
                극 = x
            elif 극 - x > 문턱:
                방향, 극, 수 = -1, x, 수 + 1
        else:
            if x < 극:
                극 = x
            elif x - 극 > 문턱:
                방향, 극, 수 = 1, x, 수 + 1
    return 수


def 사이클신호(해들):
    """A3 국면과 같은 자 — {"사이클": 참 · 거짓 · None(네 해 미만), "근거", "매출전환", "이익전환", "폭", "부호전환", "점수"}."""
    마 = [x["영업이익률"] for x in 해들 if _수(x.get("영업이익률"))]
    if len(마) < 해최소:
        return {"사이클": None, "근거": "관측 %d해 — 네 해 미만이라 판정하지 않는다" % len(마), "점수": len(마)}
    매 = [x.get("매출") for x in 해들]
    부호 = []
    for a, b in zip(매, 매[1:]):
        if _수(a) and _수(b) and a > 0:
            g = b / a - 1
            if abs(g) > 평탄:
                부호.append(1 if g > 0 else -1)
    매출전환 = sum(1 for a, b in zip(부호, 부호[1:]) if a != b)
    이익전환 = _뒤집힘(마, 이익전환문턱)
    폭 = max(마) - min(마)
    부호전환 = sum(1 for a, b in zip(마, 마[1:]) if (a >= 0) != (b >= 0))
    사이클 = 폭 >= 폭문턱 and (매출전환 >= 2 or 이익전환 >= 2)
    글 = "매출 증감 부호 전환 %d번 · 영업이익률 5%%p 넘는 방향 전환 %d번 · 폭 %.1f%%p · 영업이익률 부호 전환 %d번 · %d해" % (
        매출전환, 이익전환, 폭 * 100, 부호전환, len(마))
    return {"사이클": bool(사이클), "근거": 글, "매출전환": 매출전환, "이익전환": 이익전환, "폭": 폭, "부호전환": 부호전환, "점수": len(마)}


def 사이클판정(가정, 가정경로=None, 시계열=None):
    """사이클 회사인가 — 넷 중 하나라도 서면 참. {"사이클": 참 · 거짓 · None(재료 없음), "근거": [글], "시계열": …, "신호": …}.

      ① A3 국면(`_raw/동인원천.json` 운전자본.국면 — `사이클` 칸)  ② `메타.생애주기.덧표지` 의 경기순환 · 원자재
      ③ 관측 시계열의 S6 신호(`사이클신호`)  ④ 옛 자 — 영업이익률 부호 전환 2회 이상
    재료가 하나도 없으면(국면 · 표지 · 네 해 이상의 시계열 모두 없음) None."""
    시 = 시계열 or 관측시계열(가정, 가정경로)
    근거, 재료 = [], False
    국면 = 시.get("국면") or []
    if 국면:
        재료 = True
        if any(x.get("사이클") is True or (x.get("사이클") is None and x.get("이름") in ("저점", "정점", "중간")) for x in 국면):
            근거.append("A3 국면 — 사이클(%s)" % ((국면[0].get("근거") or "")[:80]))
    생 = ((가정.get("메타") or {}).get("생애주기") or {})
    덧 = [("%s" % x) for x in ((생.get("덧표지") if isinstance(생, dict) else None) or [])]
    표지 = [x for x in 덧 if x in 국면표지]
    if isinstance(생, dict) and 생.get("덧표지") is not None:
        재료 = True
    if 표지:
        근거.append("덧표지 — %s" % " · ".join(표지))
    신호 = 사이클신호(시["해"])
    if 신호.get("사이클") is not None:
        재료 = True
        if 신호["사이클"]:
            근거.append("관측 시계열(%s) — %s" % (시["출처"], 신호["근거"]))
        if 신호.get("부호전환", 0) >= 2:
            근거.append("영업이익률 부호 전환 %d번(옛 자)" % 신호["부호전환"])
    return {"사이클": (bool(근거) if 재료 else None), "근거": 근거, "시계열": 시, "신호": 신호}


# ────────────────────────────────────────────────────────────── ③ 사이클 블록

def _가중(해들, 키="영업이익률"):
    짝 = [(x["매출"], x[키]) for x in 해들 if _수(x.get("매출")) and _수(x.get(키))]
    합 = sum(r for r, _ in 짝)
    return (sum(r * m for r, m in 짝) / 합) if 합 else None


def _산술(해들, 키="영업이익률"):
    v = [x[키] for x in 해들 if _수(x.get(키))]
    return (sum(v) / len(v)) if v else None


def 사이클블록(해들, 구조시작=None):
    """매출 고점 → 다음 고점. [{"해": [첫, 끝], "완결": 참 · 거짓, "표시", "매출가중영업이익률", "산술영업이익률", "매출가중매출총이익률"}]."""
    쓸 = [x for x in 해들 if x.get("해") and _수(x.get("매출"))]
    if 구조시작:
        쓸 = [x for x in 쓸 if x["해"] >= 구조시작]
    if len(쓸) < 3:
        return []
    고점 = [i for i in range(len(쓸) - 1)
          if (i == 0 or 쓸[i]["매출"] >= 쓸[i - 1]["매출"]) and 쓸[i + 1]["매출"] < 쓸[i]["매출"] * (1 - 고점하락)]
    블록 = []

    def 블(조각, 완결, 표시):
        블록.append({"해": [조각[0]["해"], 조각[-1]["해"]], "완결": 완결, "표시": 표시, "해수": len(조각),
                   "매출가중영업이익률": _가중(조각), "산술영업이익률": _산술(조각),
                   "매출가중매출총이익률": _가중(조각, "매출총이익률")})
    if not 고점:
        블(쓸, False, "고점 없음 — 한 사이클이 끝나지 않았다(평균에서 뺀다)")
        return 블록
    if 고점[0] > 0:
        블(쓸[:고점[0] + 1], False, "첫 고점 앞 — 시작을 모른다(미완 · 평균에서 뺀다)")
    for a, b in zip(고점, 고점[1:]):
        블(쓸[a + 1:b + 1], True, "고점 %d → 고점 %d" % (쓸[a]["해"], 쓸[b]["해"]))
    뒤 = 쓸[고점[-1] + 1:]
    if 뒤:
        저 = min(x["매출"] for x in 뒤)
        겪음 = 저 < 쓸[고점[-1]]["매출"] and 뒤[-1]["매출"] > 쓸[고점[-1]]["매출"]
        블(뒤, False, ("마지막 고점 %d 뒤 — 저점과 그 고점을 넘는 회복을 다 겪었다(별도 판정 — 평균에는 넣지 않는다)" if 겪음
                    else "마지막 고점 %d 뒤 — 끝나지 않은 사이클(평균에서 뺀다)") % 쓸[고점[-1]]["해"])
    return 블록


def 사이클연수(해들, 구조시작=None):
    """S9R2 — 관측 매출의 고점 · 저점과 그 사이 연수(거친 바퀴의 고점구간 · 도달연도 근거 범위). 고점은 `사이클블록` 과 같은 자(다음 해 매출이 3% 넘게
    줄어드는 해), 저점은 고점 뒤 처음으로 다음 해 매출이 3% 넘게 느는 해(또는 그 뒤 매출이 다시 고점을 안 넘은 채 끝나면 없음).
    → {"고점": [해], "저점": [해], "하강": [고점 → 다음 저점 연수], "하강폭": [그 하강의 저점 매출 ÷ 고점 매출 − 1 — 하강과 같은 차례],
       "상승": [저점 → 다음 고점 연수], "마지막저점": 해 · None, "마지막고점": 해 · None}.
    하강폭은 거친 바퀴 도달연도의 깊이 잣대(고점 구간 수준 → 정상 수준의 거리 ÷ 과거 하락 속도)가 읽는다(2026-10-26).
    관측 매출이 세 해 미만이면 빈 목록들. 회사 · 업종 이름은 없다 — 매출 숫자의 모양만 본다."""
    쓸 = [x for x in 해들 if x.get("해") and _수(x.get("매출"))]
    if 구조시작:
        쓸 = [x for x in 쓸 if x["해"] >= 구조시작]
    낸 = {"고점": [], "저점": [], "하강": [], "하강폭": [], "상승": [], "마지막저점": None, "마지막고점": None}
    if len(쓸) < 3:
        return 낸
    고 = [i for i in range(len(쓸) - 1)
         if (i == 0 or 쓸[i]["매출"] >= 쓸[i - 1]["매출"]) and 쓸[i + 1]["매출"] < 쓸[i]["매출"] * (1 - 고점하락)]
    저 = []
    for a, b in zip(고, 고[1:] + [len(쓸) - 1]):
        구간 = list(range(a + 1, b + 1 if b > a else a + 1))
        for j in 구간:
            if j + 1 < len(쓸) and 쓸[j]["매출"] <= 쓸[j - 1]["매출"] and 쓸[j + 1]["매출"] > 쓸[j]["매출"] * (1 + 고점하락):
                저.append(j)
                break
    낸["고점"] = [쓸[i]["해"] for i in 고]
    낸["저점"] = [쓸[j]["해"] for j in 저]
    for i in 고:
        뒤 = [j for j in 저 if j > i]
        if 뒤:
            낸["하강"].append(쓸[뒤[0]]["해"] - 쓸[i]["해"])
            낸["하강폭"].append(쓸[뒤[0]]["매출"] / 쓸[i]["매출"] - 1 if 쓸[i]["매출"] else None)
    for j in 저:
        뒤 = [i for i in 고 if i > j]
        if 뒤:
            낸["상승"].append(쓸[뒤[0]]["해"] - 쓸[j]["해"])
    낸["마지막고점"] = 낸["고점"][-1] if 낸["고점"] else None
    if 저 and (not 고 or 저[-1] > 고[-1]):
        낸["마지막저점"] = 쓸[저[-1]]["해"]
    return 낸


# ────────────────────────────────────────────────────────────── ④ ~ ⑥ 표 · 제안

def 운영동종정상마진(가정):
    운 = ((가정.get("관측") or {}).get("운영동종") or {})
    d = ((운.get("지표") or {}).get("정상영업이익률") or {}) if isinstance(운, dict) else {}
    값 = [x.get("값") for x in (d.get("값") or []) if isinstance(x, dict) and _수(x.get("값"))]
    return (statistics.median(값), len(값)) if 값 else (None, 0)


def 통계제안(가정경로=None):
    """⑦ — `_raw/변화점.json` · `_raw/국면.json` 의 제안을 읽는다(없으면 빈 dict). 값은 바꾸지 않는다."""
    낸 = {}
    변, _p = 파일찾기("변화점.json", 가정경로) if 가정경로 else (None, None)
    if isinstance(변, dict):
        낸["변화점"] = {"폴백": 변.get("폴백"), "구조블록시작연도_제안": 변.get("구조블록시작연도_제안"),
                     "구조변화후보": [{"연도": x.get("연도"), "확률": x.get("확률"), "변수": x.get("변수")}
                                for x in (변.get("변화점") or []) if isinstance(x, dict) and x.get("분류") == "구조 변화 후보"],
                     "국면전환": [x.get("연도") for x in (변.get("변화점") or []) if isinstance(x, dict) and x.get("분류") != "구조 변화 후보"]}
    국, _p = 파일찾기("국면.json", 가정경로) if 가정경로 else (None, None)
    if isinstance(국, dict):
        정점 = next((x for x in (국.get("제안") or []) if isinstance(x, dict) and "정점영구화금지" in ("%s" % x.get("자리"))), None)
        낸["국면"] = {"폴백": 국.get("폴백"), "선택": 국.get("선택"), "평가기준일국면": 국.get("평가기준일국면"),
                    "정점영구화금지": bool(정점), "글": (정점 or {}).get("글")}
    return 낸


def 정상화표(가정, 가정경로=None):
    판 = 사이클판정(가정, 가정경로)
    시 = 판["시계열"]
    구조시작 = (가정.get("관측") or {}).get("구조블록시작연도")
    구조시작 = int(구조시작) if _수(구조시작) else None
    블록 = 사이클블록(시["해"], 구조시작)
    완결 = [b for b in 블록 if b["완결"] and _수(b["매출가중영업이익률"])]
    사이클평균 = (sum(b["매출가중영업이익률"] for b in 완결) / len(완결)) if 완결 else None
    쓸 = [x for x in 시["해"] if not 구조시작 or (x.get("해") or 0) >= 구조시작]
    전체가중, 전체산술 = _가중(쓸), _산술(쓸)
    동, 동수 = 운영동종정상마진(가정)
    후보 = []
    if 사이클평균 is not None:
        후보.append({"이름": "사이클 평균(완결 블록 %d개 — 블록 안 매출가중 · 블록끼리 같은 무게)" % len(완결), "값": 사이클평균})
    if 동 is not None:
        후보.append({"이름": "운영 동종 정상 영업이익률 중앙값(%d곳)" % 동수, "값": 동})
    매출해 = len([x for x in 쓸 if _수(x.get("매출")) and _수(x.get("영업이익률"))])
    if 전체가중 is not None:
        후보.append({"이름": "전체 관측 매출가중(매출이 있는 %d해 — 사이클을 가르지 않은 값 · 참고)" % 매출해, "값": 전체가중})
    if 전체산술 is not None and 매출해 < len(쓸):
        후보.append({"이름": "전체 관측 산술평균(%d해 — 매출이 없는 해가 %d해라 매출가중과 함께 본다 · 참고)" % (len(쓸), len(쓸) - 매출해),
                   "값": 전체산술})
    띠 = None
    if 완결:
        값들 = [b["매출가중영업이익률"] for b in 완결] + ([동] if 동 is not None else [])
        띠 = {"950": min(값들), "951": max(값들), "근거": "완결 블록 평균의 최소 · 최대(운영 동종 정상 마진을 함께 품게 넓혔다)"}
    elif 동 is not None and 전체가중 is not None:
        띠 = {"950": min(동, 전체가중), "951": max(동, 전체가중), "근거": "완결 사이클이 없어 운영 동종 정상 마진과 전체 매출가중 사이"}
    return {"판정": {"사이클": 판["사이클"], "근거": 판["근거"], "신호": 판["신호"]},
            "시계열": {"출처": 시["출처"], "원천들": 시["원천들"], "해": 시["해"]},
            "구조블록시작연도": 구조시작, "블록": 블록, "매출이있는해": 매출해,
            "사이클평균": 사이클평균, "전체매출가중": 전체가중, "전체산술": 전체산술,
            "산술대비": (None if (사이클평균 is None) else (_산술([{"영업이익률": b["산술영업이익률"]} for b in 완결]) or 0) - 사이클평균),
            "운영동종정상마진": 동, "운영동종수": 동수, "통계제안": 통계제안(가정경로),
            "제안": {"213후보": 후보, "950·951후보": 띠,
                   "관측.대상영업이익률": [{"라벨": "FY%d" % x["해"], "값": x["영업이익률"]} for x in 시["해"] if x.get("해")],
                   "주의": "고르지 않는다 — 사람이 근거와 함께 고르고 12번 213 · 950 · 951 근거 칸에 적는다(「정규화 마진의 준거는 여럿을 나란히」)"}}


def _퍼(x):
    return "—" if not _수(x) else "%.2f%%" % (x * 100)


def 표글(t):
    줄 = ["정상화 재료 — 관측 %s(%d해) · 사이클 %s" % (t["시계열"]["출처"], len(t["시계열"]["해"]),
                                              {True: "예", False: "아니오", None: "재료 없음"}[t["판정"]["사이클"]])]
    for x in t["판정"]["근거"]:
        줄.append("  근거 · " + x)
    줄.append("  신호 · %s" % t["판정"]["신호"].get("근거"))
    for b in t["블록"]:
        줄.append("  블록 %s~%s(%d해) %s — 매출가중 OPM %s · 산술 %s · 매출가중 GPM %s" % (
            b["해"][0], b["해"][1], b["해수"], b["표시"], _퍼(b["매출가중영업이익률"]), _퍼(b["산술영업이익률"]), _퍼(b["매출가중매출총이익률"])))
    줄.append("  사이클 평균 %s · 전체 매출가중 %s · 전체 산술 %s · 운영 동종 정상 %s(%d곳)" % (
        _퍼(t["사이클평균"]), _퍼(t["전체매출가중"]), _퍼(t["전체산술"]), _퍼(t["운영동종정상마진"]), t["운영동종수"]))
    for h in t["제안"]["213후보"]:
        줄.append("  213 후보 · %s %s" % (h["이름"], _퍼(h["값"])))
    if t["제안"]["950·951후보"]:
        d = t["제안"]["950·951후보"]
        줄.append("  950 · 951 후보 · %s ~ %s (%s)" % (_퍼(d["950"]), _퍼(d["951"]), d["근거"]))
    통 = t.get("통계제안") or {}
    if 통.get("변화점"):
        v = 통["변화점"]
        줄.append("  변화점(PELT) · 구조 변화 후보 %s · 국면 전환 %s · 구조블록시작연도 제안 %s%s" % (
            " · ".join("%s(확률 %.2f)" % (x["연도"], x["확률"] or 0) for x in v["구조변화후보"]) or "없음",
            " · ".join("%s" % y for y in v["국면전환"]) or "없음", v["구조블록시작연도_제안"] or "없음",
            (" · 폴백 " + v["폴백"]) if v.get("폴백") else ""))
    if 통.get("국면"):
        g = 통["국면"]
        줄.append("  국면(HMM %s) · 평가기준일 %s%s%s" % (
            g.get("선택") or "-", " · ".join("%s %.2f" % (k, p) for k, p in (g.get("평가기준일국면") or {}).items()) or "-",
            " · 정점 영구화 금지 제안" if g.get("정점영구화금지") else "", (" · 폴백 " + g["폴백"]) if g.get("폴백") else ""))
    줄.append("  " + t["제안"]["주의"])
    return "\n".join(줄)


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(allow_abbrev=False, description="정상화 재료 — 사이클 블록 · 매출가중 · 운영 동종 정상 마진")
    ap.add_argument("가정")
    ap.add_argument("--낼", default=None)
    ap.add_argument("--관측넣기", action="store_true")
    a = ap.parse_args(argv)
    try:
        g = json.load(io.open(a.가정, encoding="utf-8"))
    except (OSError, ValueError) as e:
        print("입력오류 — %s" % e)
        return 2
    t = 정상화표(g, a.가정)
    print(표글(t))
    낼 = a.낼 or os.path.join(os.path.dirname(os.path.abspath(a.가정)), "_raw", "정상화.json")
    os.makedirs(os.path.dirname(낼), exist_ok=True)
    with io.open(낼, "w", encoding="utf-8", newline="\n") as f:
        json.dump(t, f, ensure_ascii=False, indent=1)
    print("낸 파일: %s" % 낼)
    if a.관측넣기:
        새 = copy.deepcopy(g)
        관 = 새.setdefault("관측", {})
        if not _관측키(새) and t["제안"]["관측.대상영업이익률"]:
            관["대상영업이익률"] = {"값": t["제안"]["관측.대상영업이익률"], "출처": "정상화.py — %s" % t["시계열"]["출처"]}
        관["정상화"] = {"사이클": t["판정"]["사이클"], "사이클평균영업이익률": t["사이클평균"], "전체매출가중영업이익률": t["전체매출가중"],
                     "운영동종정상영업이익률": t["운영동종정상마진"], "출처": "정상화.py (_raw/정상화.json)"}
        with io.open(a.가정, "w", encoding="utf-8", newline="\n") as f:
            json.dump(새, f, ensure_ascii=False, indent=1)
            f.write("\n")
        print("가정 파일의 관측에 적었다: %s" % a.가정)
    return 0


if __name__ == "__main__":
    sys.exit(main())

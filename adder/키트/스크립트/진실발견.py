# -*- coding: utf-8 -*-
"""진실발견 — 다중 출처 진실 발견(기법 4 · 2026-10-21). 같은 대상을 여러 출처가 다른 숫자로 말할 때, **반올림 · 시점 차이(단봉)**인지
**분모 · 정의 충돌(양봉)**인지를 가르고, 단봉이면 출처 신뢰도로 가중한 병합 후보와 근거범위를 낸다.

왜 있나 — `스트림병합.py` 는 B1 · B2 의 같은 칸 값이 조금만 달라도 충돌로 올리고(모순 장부 M-09), 사람이 반올림 차이인지 분모 차이인지를
줄마다 읽었다. 이 도구는 그 판정의 재료를 숫자로 낸다. **병합하지 않는다 · 값을 쓰지 않는다** — 병합 후보 · 근거범위 · 판정 · 신호만 낸다.
M-09 를 낮출지는 모순 장부가 이 산출의 `판정` 을 읽어 정한다(오케스트레이터 연결 — 키는 `스트림병합.충돌모으기` 의 `키` 그대로).

방법(설정은 `진실코호트설정.json` 「진실발견」 — 결과를 보기 전에 정한 값)
  ① 묶음 — (가) 합본 `_raw/매출스트림_웹조사.json` 의 `충돌[]`(+ `_raw/매출스트림_심화.json` 의 `충돌[]`)을 `스트림병합.충돌모으기` 로
     정리한 것(키 · 값들 · 출처 · 국면) (나) 세 산출(웹조사 · 심화 · `_raw/투자능력.json`)의 값 칸(설정 `값칸` — market_size · 관측치 · 능력 …)에서
     항목 이름 · 기간이 같은 줄을 모은 것. 한 값으로 못 읽는 글(「58% / 21% …」 · 화살표 경로)은 뺀다
  ② 수치 읽기 — 「1,469억 달러」 · 「$54B」 · 「약 50%」 · 「+13~18%」(범위 → 가운데) · 「8~9배」. 연도 · 분기 · 괄호 안 단서는 숫자로 읽지 않는다.
     단위 종류(% · %p · 배 · 통화 · 수)가 갈리면 비교 불가(양봉 쪽 — 정의가 다르다)
  ③ 출처 유형 — 딱지 · 출처 글의 낱말로 공시·법령 > 공개통계 > 조사기관·기술분석 > IR·회사주장 > 2차웹 > 불명의 사전 신뢰도.
     `출처_성격`(원문 · 2차정리 · 검색요약 · 불명) · `확신도`(상 · 중 · 하)가 배수로 곱해진다
  ④ TruthFinder 꼴 반복 — 묶음마다 신뢰도 가중 중앙값(양수면 로그 공간) → 출처마다 오차(척도로 나눈 거리의 평균) → 신뢰도 = 사전 × e^(−감쇠 × 오차).
     수렴 문턱 · 반복 상한
  ⑤ 혼합 판정 — 둘이면 상대 차이 문턱, 셋 이상이면 정렬한 값의 가장 큰 틈이 덩어리 안 강건 척도(MAD)의 설정 배수를 넘고 양쪽 신뢰도 질량이
     하한 이상이면 「양봉」. 두 값(덩어리)의 비가 10^k(k ≥ 2)에 가까우면 「자릿수 의심」. 그 밖은 「단봉」
  ⑥ 단봉이면 신뢰도 가중 중앙값 · 가중 분위(근거범위), 양봉이면 덩어리를 나란히. **시장 규모(설정 `병합금지_칸`)는 병합값을 내지 않는다**

    python 스크립트/진실발견.py 가정.json [--설정 경로] [--낼 경로]

읽는 것  가정 곁 `_raw/매출스트림_웹조사.json` · `_raw/매출스트림_심화.json` · `_raw/투자능력.json`(`정상화.파일찾기` 차례) — 없으면 그 파일만 건너뛴다
내는 것  `_raw/진실발견.json` — 형식 · 만든날 · 설정 · 입력 · 폴백 · 대상[] · 출처신뢰도 · 제안[] · 신호[]
         읽기 함수 `진실발견읽기(가정경로)` → {키: 대상 줄} (파일 없으면 None)
종료 코드 0 경보 없음 · 1 경보 신호(양봉 · 자릿수 의심) · 2 입력 오류(가정 · 설정을 못 읽음)
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
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
from 스트림병합 import 충돌모으기, _정규  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                            # noqa: BLE001
    pass

형식이름 = "진실발견 1"
산출이름 = "진실발견.json"
입력파일 = ("매출스트림_웹조사.json", "매출스트림_심화.json", "투자능력.json")
이름칸 = ("항목", "이름", "공장", "설비", "name", "내용", "지표", "제품", "대상", "시장", "보고서")


def 설정읽기(경로=None):
    p = 경로 or os.path.join(여기, "진실코호트설정.json")
    return json.load(io.open(p, encoding="utf-8"))["진실발견"]


# ───────────────────────────────────────────── ② 수치 읽기

_한배수 = {"조": 1e12, "억": 1e8, "만": 1e4, "천": 1e3}
_영배수 = {"k": 1e3, "thousand": 1e3, "m": 1e6, "mn": 1e6, "million": 1e6, "b": 1e9, "bn": 1e9, "billion": 1e9,
         "t": 1e12, "tn": 1e12, "trillion": 1e12}
_통화 = {"$": "USD", "달러": "USD", "usd": "USD", "₩": "KRW", "원": "KRW", "krw": "KRW", "€": "EUR", "유로": "EUR", "eur": "EUR",
       "¥": "JPY", "엔": "JPY", "jpy": "JPY", "위안": "CNY", "cny": "CNY", "rmb": "CNY"}
_빼기 = [r"\*+", r"\([^()]*\)", r"（[^（）]*）", r"\[[^\[\]]*\]",
        r"\d{4}[-./]\d{1,2}(?:[-./]\d{1,2})?", r"(?:19|20)\d{2}\s*년", r"\b(?:FY|CY)\s*\d{2,4}[AEF]?\b", r"\b(?:19|20)\d{2}[AEF]\b",
        r"\b[1-4]\s*Q\s*\d{2}\b", r"\bQ[1-4]\b", r"\b[12]\s*H\s*\d{2}\b", r"\d+\s*분기", r"\d{1,2}\s*월\s*\d{1,2}\s*일", r"\d{1,2}\s*월(?!\s*\d)",
        r"\d+\s*nm\b", r"\d+\s*단\b", r"\d+\s*세대", r"\b(?:19|20)\d{2}\b(?![\d,.])"]
_수 = re.compile(
    r"(?P<부호>[+\-−–])?\s*(?P<앞통화>[$₩€¥])?\s*(?P<수>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s*"
    r"(?P<배>조|억|만|천|thousand|million|billion|trillion|bn|mn|tn|[kKmMbBtT](?![a-zA-Z]))?\s*"
    r"(?P<단위>%p|%|배|개월|일|달러|원|엔|위안|유로|USD|KRW|JPY|EUR|CNY|RMB|usd|krw)?")
_범위사이 = re.compile(r"^\s*(?:~|〜|∼|-|–|—|to|에서)\s*$")


def _단위종류(단위, 앞통화):
    if 단위 in ("%", "%p", "배", "일", "개월"):
        return 단위
    c = _통화.get((단위 or "").lower()) or _통화.get(단위 or "") or _통화.get(앞통화 or "")
    return ("통화:" + c) if c else "수"


def 수치읽기(글):
    """한 값으로 읽히면 {"값", "단위", "범위"(또는 None)}, 아니면 None. 범위(「13~18%」)는 가운데 값."""
    if 글 is None or isinstance(글, bool):
        return None
    if isinstance(글, (int, float)):
        return {"값": float(글), "단위": "수", "범위": None} if math.isfinite(글) else None
    s = "%s" % 글
    for p in _빼기:
        s = re.sub(p, " ", s, flags=re.I)
    조각 = []
    for m in _수.finditer(s):
        v = float(m.group("수").replace(",", ""))
        배 = m.group("배")
        if 배:
            v *= _한배수.get(배) or _영배수.get(배.lower(), 1.0)
        if m.group("부호") in ("-", "−", "–") and (m.start() == 0 or not s[m.start() - 1].isdigit()):
            v = -v
        조각.append({"값": v, "단위원": m.group("단위"), "앞통화": m.group("앞통화"), "배": 배, "시작": m.start(), "끝": m.end()})
    if not 조각:
        return None
    if len(조각) == 1:
        x = 조각[0]
        return {"값": x["값"], "단위": _단위종류(x["단위원"], x["앞통화"]), "범위": None}
    사이 = s[조각[0]["끝"]:조각[1]["시작"]] if len(조각) == 2 else ""
    # 「10-20%」 — 뒤 수의 앞 대시가 부호로 먹혔으면(앞이 숫자라 음수로 읽지 않았다) 그 대시가 범위의 사이다
    붙은대시 = len(조각) == 2 and not 사이.strip() and s[조각[1]["시작"]:조각[1]["시작"] + 1] in ("-", "–", "—")
    if len(조각) == 2 and (_범위사이.match(사이) or 붙은대시):
        a, b = 조각
        단 = b["단위원"] or a["단위원"]
        앞 = a["앞통화"] or b["앞통화"]
        av = a["값"]
        if not a["배"] and b["배"]:                       # 「160~190K」 — 배수는 뒤에서 앞으로
            av *= _한배수.get(b["배"]) or _영배수.get(b["배"].lower(), 1.0)
        lo, hi = sorted((av, b["값"]))
        return {"값": (lo + hi) / 2.0, "단위": _단위종류(단, 앞), "범위": [lo, hi]}
    return None


# ───────────────────────────────────────────── ③ 출처 유형 · 사전 신뢰도

def 출처유형(출처, 설정):
    t = "%s" % (출처 or "")
    낮 = t.lower()
    for 유형 in 설정["유형판정_차례"]:
        for w in 설정["유형판정_낱말"].get(유형, []):
            if (w.lower() in 낮) if w.isascii() else (w in t):
                return 유형
    return "불명"


def 출처배수(출처, 성격, 확신, 설정):
    글 = "%s %s" % (출처 or "", 성격 or "")
    배 = [v for k, v in 설정["출처성격_배수"].items() if k in 글]
    a = min(배) if 배 else 1.0
    b = 설정["확신도_배수"].get(("%s" % (확신 or "")).strip()[:1], 1.0)
    return a * b


def 출처키(출처):
    t = re.sub(r"\d{4}[-./]\d{1,2}(?:[-./]\d{1,2})?|\b[1-4]Q\d{2}\b|\b[12]H\d{2}\b|\((?:[^()]*)\)", " ", "%s" % (출처 or ""))
    k = _정규(t)[:40]
    return k or "출처미상"


def _출처나누기(출처):
    """「A · B」(충돌모으기가 합친 출처) → [A, B]."""
    벌 = [x.strip() for x in re.split(r"\s+·\s+|;", "%s" % (출처 or "")) if x.strip()]
    return 벌 or [""]


# ───────────────────────────────────────────── ① 묶음 모으기

def _주장(값, 출처, 성격, 확신, 국면, 설정):
    r = 수치읽기(값)
    return {"값": "%s" % (값 if 값 is not None else ""), "수치": r["값"] if r else None, "단위": r["단위"] if r else None,
            "범위": r["범위"] if r else None, "출처": "%s" % (출처 or ""), "성격": "%s" % (성격 or ""), "확신도": "%s" % (확신 or ""),
            "국면": 국면 or "", "유형": 출처유형("%s %s" % (출처 or "", 성격 or ""), 설정),
            "배수": 출처배수(출처, 성격, 확신, 설정), "출처키": 출처키(출처)}


def 묶음모으기(파일들, 설정):
    """→ (묶음 목록, 셈). 묶음 = {"키", "출처칸", "칸", "대상", "기간", "M09ID", "주장"[]}."""
    묶 = []
    셈 = {"충돌": 0, "값칸묶음": 0, "한출처묶음": 0, "못읽은값": 0}
    # (가) 충돌 — 합본 웹조사(모순장부 M-09 와 같은 입력) · 심화
    벌 = []
    for 이름, 기록 in (("매출스트림_웹조사.json", "합본"), ("매출스트림_심화.json", "심화")):
        j = 파일들.get(이름)
        if isinstance(j, dict) and isinstance(j.get("충돌"), list) and j["충돌"]:
            벌.append((기록, j["충돌"]))
    if 벌:
        정리, _ = 충돌모으기(벌)
        for x in 정리:
            주 = []
            for v in x["값들"]:
                for 출 in _출처나누기(v.get("출처")):
                    주.append(_주장(v.get("값"), 출, "", "", v.get("국면"), 설정))
            묶.append({"키": x["키"], "출처칸": "충돌", "칸": x["칸"], "대상": x["대상"], "기간": "",
                      "M09ID": "M-09-" + hashlib.sha1(x["키"].encode("utf-8")).hexdigest()[:6], "주장": 주})
            셈["충돌"] += 1
    # (나) 값 칸 — 항목 이름 · 기간이 같은 줄
    모 = {}
    for 이름 in 입력파일:
        j = 파일들.get(이름)
        if not isinstance(j, dict):
            continue
        for 칸 in 설정["값칸"]:
            줄들 = j.get(칸)
            if not isinstance(줄들, list):
                continue
            for 줄 in 줄들:
                if not isinstance(줄, dict) or "값" not in 줄:
                    continue
                nm = next(("%s" % 줄[k] for k in 이름칸 if 줄.get(k) not in (None, "")), "")
                if not nm:
                    continue
                기간 = "%s" % (줄.get("기간") or "")
                키 = "값칸|%s|%s|%s" % (칸, _정규(nm), _정규(기간))
                출 = 줄.get("출처")
                if isinstance(출, (list, dict)):
                    출 = json.dumps(출, ensure_ascii=False)
                모.setdefault(키, {"키": 키, "출처칸": "값칸", "칸": 칸, "대상": nm, "기간": 기간, "M09ID": None, "주장": [], "파일": set()})
                모[키]["주장"].append(_주장(줄.get("값"), 출, 줄.get("출처_성격"), 줄.get("확신도"), 이름.replace(".json", ""), 설정))
                모[키]["파일"].add(이름)
    for 키, g in 모.items():
        g["파일"] = sorted(g["파일"])
        if len(g["주장"]) < 2:
            셈["한출처묶음"] += 1
            continue
        묶.append(g)
        셈["값칸묶음"] += 1
    for g in 묶:
        셈["못읽은값"] += sum(1 for c in g["주장"] if c["수치"] is None)
    return 묶, 셈


# ───────────────────────────────────────────── ④ 가중 통계

def _가중중앙(xs, ws):
    return _가중분위(xs, ws, 0.5)


def _가중분위(xs, ws, q):
    짝 = sorted(zip(xs, ws))
    전 = sum(w for _, w in 짝)
    if 전 <= 0:
        짝 = [(x, 1.0) for x, _ in 짝]
        전 = float(len(짝))
    누 = 0.0
    for x, w in 짝:
        누 += w
        if 누 >= q * 전 - 1e-12:
            return x
    return 짝[-1][0]


def _중앙(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def _mad(xs):
    m = _중앙(xs)
    return _중앙([abs(x - m) for x in xs])


def _평가할(g):
    """수치가 둘 이상 · 단위 종류가 하나인 주장만. → (주장 목록, 단위 종류들)."""
    읽힌 = [c for c in g["주장"] if c["수치"] is not None]
    return 읽힌, sorted({c["단위"] for c in 읽힌})


def _공간(읽힌):
    return "로그" if all(c["수치"] > 0 for c in 읽힌) else "선형"


def _변환(c, 공):
    return math.log(c["수치"]) if 공 == "로그" else c["수치"]


def _바닥(공, 중심, 설정):
    r = 설정["오차_척도_하한_상대"]
    return math.log1p(r) if 공 == "로그" else max(r * abs(중심), 1e-9)


def 반복(묶음들, 설정):
    """TruthFinder 꼴 — 출처 신뢰도 ↔ 대상 참값을 번갈아. → (출처신뢰도 dict, 반복수, 수렴)."""
    사전 = 설정["출처유형_사전신뢰도"]
    출처 = {}
    평가 = []
    for g in 묶음들:
        읽힌, 단위들 = _평가할(g)
        if len(읽힌) >= 2 and len(단위들) == 1:
            평가.append((g, 읽힌, _공간(읽힌)))
            for c in 읽힌:
                출처.setdefault(c["출처키"], {"유형": c["유형"], "사전": 사전.get(c["유형"], 사전["불명"]), "신뢰": None, "주장수": 0})
                출처[c["출처키"]]["주장수"] += 1
    for s in 출처.values():
        s["신뢰"] = s["사전"]
    n, 수렴 = 0, True
    for n in range(1, int(설정["반복_상한"]) + 1):
        오차 = {k: [] for k in 출처}
        for g, 읽힌, 공 in 평가:
            xs = [_변환(c, 공) for c in 읽힌]
            ws = [출처[c["출처키"]]["신뢰"] * c["배수"] for c in 읽힌]
            v = _가중중앙(xs, ws)
            척 = max(1.4826 * _mad(xs), _바닥(공, v, 설정))
            for c, x in zip(읽힌, xs):
                오차[c["출처키"]].append(abs(x - v) / 척)
        바뀜 = 0.0
        for k, s in 출처.items():
            e = sum(오차[k]) / len(오차[k]) if 오차[k] else 0.0
            새 = s["사전"] * math.exp(-float(설정["신뢰_감쇠"]) * e)
            바뀜 = max(바뀜, abs(새 - s["신뢰"]))
            s["신뢰"] = 새
        if 바뀜 < float(설정["수렴_문턱"]):
            break
    else:
        수렴 = False
    return 출처, n, 수렴


# ───────────────────────────────────────────── ⑤ 혼합 판정 · ⑥ 병합 후보

def _자릿수(a, b, 설정):
    """두 양수의 비가 10^k(k ≥ 최소지수)에 가까우면 k, 아니면 None."""
    if a <= 0 or b <= 0:
        return None
    r = math.log10(max(a, b) / min(a, b))
    k = round(r)
    return k if (k >= int(설정["자릿수_최소지수"]) and abs(r - k) <= float(설정["자릿수_허용"])) else None


def _되돌림(v, 공):
    return math.exp(v) if 공 == "로그" else v


def 판정하기(g, 출처, 설정):
    """묶음 하나 → 대상 줄(판정 · 병합값 · 근거범위 · 덩어리)."""
    읽힌, 단위들 = _평가할(g)
    줄 = {"키": g["키"], "출처칸": g["출처칸"], "칸": g["칸"], "대상": g["대상"], "기간": g.get("기간", ""), "M09ID": g.get("M09ID"),
         "값들": [], "판정": None, "까닭": "", "병합값": None, "근거범위": None, "덩어리": None, "공간": None,
         "병합금지": g["칸"] in 설정["병합금지_칸"]}
    for c in g["주장"]:
        줄["값들"].append({"값": c["값"], "수치": c["수치"], "단위": c["단위"], "범위": c["범위"], "출처": c["출처"], "유형": c["유형"],
                         "사전": 설정["출처유형_사전신뢰도"].get(c["유형"], 설정["출처유형_사전신뢰도"]["불명"]),
                         "신뢰도": round((출처.get(c["출처키"], {}).get("신뢰") or 0.0) * c["배수"], 4) if c["수치"] is not None else None})
    if len(읽힌) < 2:
        줄["판정"], 줄["까닭"] = "표본 부족", "한 값으로 읽히는 수치가 %d개뿐이다(복합 글 · 「제시되지 않음」은 숫자로 안 읽는다)" % len(읽힌)
        return 줄
    if len(단위들) > 1:
        줄["판정"], 줄["까닭"] = "양봉", "단위 종류가 갈린다(%s) — 같은 대상을 다른 정의로 말한다" % " · ".join(단위들)
        줄["덩어리"] = [{"단위": u, "값들": [c["값"] for c in 읽힌 if c["단위"] == u]} for u in 단위들]
        return 줄
    공 = _공간(읽힌)
    줄["공간"] = 공
    xs = [_변환(c, 공) for c in 읽힌]
    ws = [(출처[c["출처키"]]["신뢰"] if c["출처키"] in 출처 else 0.0) * c["배수"] for c in 읽힌]
    전 = sum(ws) or 1.0
    순 = sorted(range(len(xs)), key=lambda i: xs[i])
    덩 = None
    if len(xs) == 2:
        a, b = (읽힌[0]["수치"], 읽힌[1]["수치"])
        작 = min(abs(a), abs(b))
        상대 = abs(a - b) / 작 if 작 > 0 else float("inf")
        if 상대 > float(설정["둘일때_상대차이_문턱"]):
            덩 = ([순[0]], [순[1]])
            줄["까닭"] = "두 값의 상대 차이 %.0f%% — 문턱 %.0f%% 를 넘는다" % (상대 * 100, float(설정["둘일때_상대차이_문턱"]) * 100)
        else:
            줄["까닭"] = "두 값의 상대 차이 %.1f%% — 문턱 안" % (상대 * 100)
    else:
        틈 = [(xs[순[i + 1]] - xs[순[i]], i) for i in range(len(순) - 1)]
        큰, k = max(틈)
        왼, 오 = 순[:k + 1], 순[k + 1:]
        안 = []
        for 편 in (왼, 오):
            m = _중앙([xs[i] for i in 편])
            안 += [abs(xs[i] - m) for i in 편]
        척 = max(1.4826 * _중앙(안), _바닥(공, _가중중앙(xs, ws), 설정))
        질왼, 질오 = sum(ws[i] for i in 왼) / 전, sum(ws[i] for i in 오) / 전
        if 큰 > float(설정["양봉_틈배수"]) * 척 and min(질왼, 질오) >= float(설정["양봉_양쪽질량_하한"]):
            덩 = (왼, 오)
            줄["까닭"] = "가장 큰 틈 %.3g — 덩어리 안 척도 %.3g 의 %.1f배(문턱 %.1f배) · 양쪽 신뢰도 질량 %.0f%% · %.0f%%" % (
                큰, 척, 큰 / 척, float(설정["양봉_틈배수"]), 질왼 * 100, 질오 * 100)
        else:
            줄["까닭"] = "가장 큰 틈 %.3g — 덩어리 안 척도 %.3g 의 %.1f배(문턱 %.1f배) · 양쪽 질량 %.0f%% · %.0f%%" % (
                큰, 척, 큰 / 척 if 척 else 0.0, float(설정["양봉_틈배수"]), 질왼 * 100, 질오 * 100)
    if 덩:
        중심 = []
        for 편 in 덩:
            v = _되돌림(_가중중앙([xs[i] for i in 편], [ws[i] or 1e-12 for i in 편]), 공)
            중심.append(v)
        줄["덩어리"] = [{"중앙값": 중심[j], "값들": [읽힌[i]["값"] for i in 편], "출처": [읽힌[i]["출처"] for i in 편],
                       "신뢰도질량": round(sum(ws[i] for i in 편) / 전, 4)} for j, 편 in enumerate(덩)]
        k = _자릿수(abs(중심[0]), abs(중심[1]), 설정) if 공 == "로그" or all(v > 0 for v in 중심) else None
        if k is not None:
            줄["판정"] = "자릿수 의심"
            줄["까닭"] += " · 두 덩어리의 비가 10^%d 에 가깝다 — 단위(천 · 백만 · 억 · %% 와 소수)를 잘못 옮겼을 수 있다" % k
        else:
            줄["판정"] = "양봉"
        return 줄
    줄["판정"] = "단봉"
    lo_q, hi_q = 설정["근거범위_분위"]
    lo = _되돌림(_가중분위(xs, ws, lo_q), 공)
    hi = _되돌림(_가중분위(xs, ws, hi_q), 공)
    범들 = [c["범위"] for c in 읽힌 if c["범위"]]
    if 범들:                                                    # 출처가 범위로 준 값은 그 끝까지 근거범위에 넣는다
        lo = min([lo] + [r[0] for r in 범들])
        hi = max([hi] + [r[1] for r in 범들])
    줄["근거범위"] = [lo, hi]
    if 줄["병합금지"]:
        줄["까닭"] += " · %s" % 설정["병합금지_까닭"]
    else:
        줄["병합값"] = _되돌림(_가중중앙(xs, ws), 공)
    return 줄


# ───────────────────────────────────────────── 신호 · 제안 · 돌기

def _자리(줄):
    return "%s · %s%s" % (줄["칸"] or 줄["출처칸"], 줄["대상"] or "이름 없음", (" (%s)" % 줄["기간"]) if 줄.get("기간") else "")


def _짧게(v):
    if v is None:
        return "-"
    a = abs(v)
    if a >= 1e12:
        return "%.3g조" % (v / 1e12)
    if a >= 1e8:
        return "%.4g억" % (v / 1e8)
    return "%.4g" % v


def 신호짓기(대상들, 셈, 폴백, 설정):
    신 = []
    for 줄 in 대상들:
        if 줄["판정"] == "양봉":
            덩 = 줄.get("덩어리") or []
            값글 = " / ".join(_짧게(d.get("중앙값")) if "중앙값" in d else "%s(%s)" % (d.get("단위"), ", ".join(d.get("값들") or [])) for d in 덩)
            신.append({"출처": "진실발견", "종류": "양봉 — 분모 정의 충돌", "대상": _자리(줄), "값": 값글,
                      "문턱": "틈 > %.1f × 척도 · 양쪽 질량 ≥ %.0f%% (둘이면 상대 차이 > %.0f%%)" % (
                          float(설정["양봉_틈배수"]), float(설정["양봉_양쪽질량_하한"]) * 100, float(설정["둘일때_상대차이_문턱"]) * 100),
                      "글": "같은 대상을 출처들이 서로 다른 두 덩어리로 말한다(%s) — 반올림이 아니라 분모 · 정의가 다를 가능성이 높다. "
                           "두 출처의 정의(단위 · 기준연도 · 집계 주체 · 물량인지 금액인지)를 대조해 고르거나 둘 다 태그로 남긴다" % 줄["까닭"],
                      "등급": "경보"})
        elif 줄["판정"] == "자릿수 의심":
            신.append({"출처": "진실발견", "종류": "자릿수 의심", "대상": _자리(줄),
                      "값": " / ".join(_짧게(d["중앙값"]) for d in 줄["덩어리"]), "문턱": "비 ≈ 10^k (k ≥ %d, 허용 %.2f)" % (
                          int(설정["자릿수_최소지수"]), float(설정["자릿수_허용"])),
                      "글": "두 덩어리의 비가 10의 거듭제곱에 가깝다 — 단위를 옮기다 자릿수가 틀렸을 수 있다. 원문의 단위를 다시 읽는다",
                      "등급": "경보"})
        elif 줄["판정"] == "단봉" and 줄["출처칸"] == "충돌":
            값 = 줄["병합값"]
            신.append({"출처": "진실발견", "종류": "단봉 — 반올림 · 시점 차이로 병합 가능", "대상": _자리(줄),
                      "값": _짧게(값) if 값 is not None else "병합 안 함(병합금지 칸)",
                      "문턱": "근거범위 %s ~ %s" % (_짧게(줄["근거범위"][0]), _짧게(줄["근거범위"][1])),
                      "글": "충돌로 올라온 값들이 한 덩어리다(%s) — 반올림 · 시점 차이로 읽힌다. 신뢰도 가중 중앙값을 후보로, 양 끝을 근거범위로 "
                           "쓸 수 있다(고르는 것은 본선)" % 줄["까닭"], "등급": "참고"})
    if 폴백:
        신.append({"출처": "진실발견", "종류": "표본 부족", "대상": "다중 출처 수치", "값": 셈.get("충돌", 0) + 셈.get("값칸묶음", 0),
                  "문턱": "같은 대상을 둘 이상의 출처가 한 값으로 말한 묶음 ≥ 1", "글": "%s — 진실 발견을 돌릴 묶음이 없다(종전 규칙: 충돌은 모순 장부 M-09 에 "
                  "그대로 · 시장 규모는 출처별로 나란히)" % 폴백, "등급": "참고"})
    return 신


def 제안짓기(대상들):
    낸 = []
    for 줄 in 대상들:
        if 줄["판정"] == "단봉":
            낸.append({"자리": _자리(줄), "키": 줄["키"], "M09ID": 줄.get("M09ID"), "병합후보": 줄["병합값"], "근거범위": 줄["근거범위"],
                      "근거": "[계산 — 출처 신뢰도 가중 중앙값(진실 발견 · TruthFinder 꼴) · 가중 분위 %s]" % ("시장 규모라 병합값 없음" if 줄["병합금지"] else ""),
                      "쓰는 법": "축 · 판단 칸의 근거범위 후보 — 값을 넣는 것은 본선이다"})
        elif 줄["판정"] in ("양봉", "자릿수 의심"):
            낸.append({"자리": _자리(줄), "키": 줄["키"], "M09ID": 줄.get("M09ID"), "병합후보": None, "덩어리": 줄["덩어리"],
                      "근거": "[판단 대기 — %s · 병합하지 않는다]" % 줄["판정"], "쓰는 법": "정의를 사람이 대조한다(모순 장부 M-09 · X-계열)"})
    return 낸


def 돌기(가정경로, 설정):
    파일들, 입력 = {}, {}
    for 이름 in 입력파일:
        내용, 곳 = 정상화.파일찾기(이름, 가정경로)
        입력[이름] = 곳
        if isinstance(내용, dict):
            파일들[이름] = 내용
    묶음들, 셈 = 묶음모으기(파일들, 설정)
    출처, 회, 수렴 = 반복(묶음들, 설정)
    대상들 = [판정하기(g, 출처, 설정) for g in 묶음들]
    평가됨 = [x for x in 대상들 if x["판정"] != "표본 부족"]
    폴백 = None
    if not 파일들:
        폴백 = "재료 없음 — 웹조사 · 심화 · 투자능력 산출이 없다"
    elif not 평가됨:
        폴백 = "표본 부족 — 같은 대상을 둘 이상의 출처가 한 값으로 말한 묶음이 없다"
    return {"형식": 형식이름, "만든날": datetime.date.today().isoformat(), "설정": 설정,
            "입력": {"가정": os.path.abspath(가정경로), "파일": 입력, "셈": 셈, "반복수": 회, "수렴": 수렴},
            "폴백": 폴백, "대상": 대상들,
            "출처신뢰도": {k: {"유형": v["유형"], "사전": v["사전"], "학습": round(v["신뢰"], 4), "주장수": v["주장수"]} for k, v in 출처.items()},
            "제안": 제안짓기(대상들), "신호": 신호짓기(대상들, 셈, 폴백, 설정)}


def 진실발견읽기(가정경로):
    """→ {키: 대상 줄}(파일이 없거나 형식이 다르면 None). 모순 장부 M-09 · 스트림병합이 이 판정을 읽는다."""
    내용, _곳 = 정상화.파일찾기(산출이름, 가정경로)
    if not isinstance(내용, dict) or 내용.get("형식") != 형식이름:
        return None
    return {x["키"]: x for x in 내용.get("대상") or [] if isinstance(x, dict) and x.get("키")}


def 찍기(결과):
    print("── 진실 발견 — 묶음 %d(충돌 %d · 값 칸 %d) · 반복 %d%s ──" % (
        len(결과["대상"]), 결과["입력"]["셈"]["충돌"], 결과["입력"]["셈"]["값칸묶음"], 결과["입력"]["반복수"],
        "" if 결과["입력"]["수렴"] else "(수렴 안 함)"))
    for x in 결과["대상"]:
        print("  %-10s %-44s %s" % (x["판정"], _자리(x)[:44], x["까닭"][:110]))
    if 결과["폴백"]:
        print("  폴백 — %s" % 결과["폴백"])
    for s in 결과["신호"]:
        print("  [%s] %s — %s" % (s["등급"], s["종류"], s["대상"]))


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="다중 출처 진실 발견 — 같은 대상의 숫자가 반올림 차이(단봉)인지 정의 충돌(양봉)인지")
    ap.add_argument("가정")
    ap.add_argument("--설정", default=None)
    ap.add_argument("--낼", default=None)
    a = ap.parse_args(argv)
    try:
        json.load(io.open(a.가정, encoding="utf-8"))
    except (OSError, ValueError) as e:
        print("가정 파일을 읽지 못했습니다: %s" % e)
        return 입력오류
    try:
        설정 = 설정읽기(a.설정)
    except (OSError, ValueError, KeyError) as e:
        print("설정 파일을 읽지 못했습니다: %s" % e)
        return 입력오류
    결과 = 돌기(a.가정, 설정)
    밖 = a.낼 or os.path.join(os.path.dirname(os.path.abspath(a.가정)), "_raw", 산출이름)
    os.makedirs(os.path.dirname(밖), exist_ok=True)
    io.open(밖, "w", encoding="utf-8").write(json.dumps(결과, ensure_ascii=False, indent=1))
    찍기(결과)
    print("→ %s" % 밖)
    return 발견 if any(s["등급"] == "경보" for s in 결과["신호"]) else 통과


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""미국원천읽기 — 받아 둔 미국 원천(companyfacts · submissions · 10-K · 10-Q · 20-F · 6-K 원문)을 읽어 `_raw/미국원천.json` 을 낸다
(2026-10-25 FX-C · 설계 `연구/F도구수리_20261025/설계.md` 4-2 「미국원천/1」 · 뿌리 R6 · R7).

왜 만들었나
  유니버스 F 물결에서 미국 21곳 모두가 같은 자리에서 손으로 메웠다 — 약정(구매의무 · 미개시 리스 · capex 약정)이 도구판 0 / 21,
  capex 가이던스 문장 · 기준일 분기 누계(1H · 9M) · RPO · 유형자산 자산군 표 · 인원 · 능력 문장을 읽는 곳이 없었다(F2 · F3 · F6 · F8 · F12 ·
  F14 · F21 · F24 · F28 · F35 · F37 · F38 · F43 · F44 · F48 · F56 · F59 · F61). 동인원천(FX-A)은 이 파일이 있으면 읽고, 투자능력(FX-B)은
  직접 읽는다.

무엇을 읽나(네트워크 0 — 받는 일은 `sec_fetch.py --기준일`)
  submissions.json   공시 목록 → 「기준일분기 · 직전 · 뒤」 표지(기간 끝 ≤ 기준일 + 7일 중 가장 늦은 정기 보고 = 기준일분기 · 52/53주 결산 허용)
  companyfacts.json  약정 · RPO · 기준일 누계 · 유형자산 자산군 — 태그는 `미국약정태그.json`(설정 — 회사 이름 없음) · us-gaap / ifrs-full 둘 다
  10K_ · 10Q_ · 20F_ · 6K_ · 8K_*.htm   Item 1 · Item 2 · MD&A 조각 · 약정 문장 · capex 가이던스 문장 · 능력 문장 · 유형자산 표(태그가 없을 때)
  직원수_10K.json    PN 갈래(`sec_상세변수.py 직원수`) 산출 — 있으면 그것, 없으면 그 갈래의 `본문직원()` 을 10-K 에 대서(같은 정규식을 두 곳에 두지 않는다)

숫자 — 한 파일 안에서 원 단위 하나(태그 값은 이미 원 단위 · 표 머리 「in thousands / millions / billions」 · 문장 「$ 16.4 million」을 곱해 맞춘다).
인용 — 문장을 길게 옮기지 않는다(capex 가이던스는 수치와 기간만 요약 · 약정 문장은 120자 안).

    python 스크립트/미국원천읽기.py --기준일 2026-06-30 [--raw _raw] [-o _raw/미국원천.json]

종료 코드 — 0 통과 · 1 발견(기준일 분기 보고 없음 등 경보) · 2 입력오류(companyfacts · submissions 없음).
"""
from __future__ import annotations

import argparse
import datetime
import glob
import html as _html
import io
import json
import os
import re
import sys
from html.parser import HTMLParser

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류  # noqa: E402

형식 = "미국원천/1"
허용일 = 7                                             # 52/53주 결산 — 기간 끝이 기준일 ± 7일이면 같은 분기
정기양식 = ("10-K", "10-Q", "20-F", "40-F", "10-KT")
연차양식 = ("10-K", "20-F", "40-F", "10-KT")
본뜻공간 = ("us-gaap", "ifrs-full", "dei", "srt", "invest", "ecd", "ffd")
설정파일 = os.path.join(여기, "미국약정태그.json")


def _읽기(p, 기본=None):
    try:
        with io.open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return 기본


def 설정():
    return _읽기(설정파일) or {}


def 날(s):
    try:
        return datetime.date.fromisoformat((s or "")[:10])
    except ValueError:
        return None


# ══════════════════════════════════════════════════════════ 공시 고르기 (R7)

def 공시표(sub):
    """submissions → [{양식 · 기간끝 · 제출일 · accession · 문서}] (recent 만 — 최근 천 건)."""
    rec = ((sub or {}).get("filings") or {}).get("recent") or {}
    양 = rec.get("form") or []
    낸 = []
    for i, f in enumerate(양):
        def 칸(k):
            v = rec.get(k) or []
            return v[i] if i < len(v) else None
        낸.append({"양식": f, "기간끝": 칸("reportDate") or None, "제출일": 칸("filingDate"), "accession": 칸("accessionNumber"),
                  "문서": 칸("primaryDocument")})
    return 낸


def 공시고르기(sub, 기준일, 허용=허용일):
    """기준일을 담은 분기 공시를 고른다 → {"기준": 행 | None, "직전": 행 | None, "연차": 행 | None, "뒤": [행 …], "해외6K후보": [행 …], "경보": […]}.
    · 기준 = 기간 끝 ≤ 기준일 + 허용 인 정기 보고(10-K · 10-Q · 20-F · 40-F) 가운데 가장 늦은 기간(같은 기간이면 먼저 낸 원본)
      — 제출이 기준일 뒤여도 그 기간을 담았으면 첫 출처다(국내 반기보고서와 같은 자리 · F35 · F38)
    · 직전 = 그보다 앞 기간의 정기 보고 하나 · 연차 = 기준일 앞 마지막 연차 보고(기준과 같을 수 있다)
    · 뒤 = 기간 끝이 기준일 + 허용 뒤인 정기 보고(「평가기준일 뒤 정보」 — 값 칸에 섞지 않는다)
    · 해외6K후보 = 연차 양식이 20-F · 40-F 인 회사의 6-K 가운데 제출이 기준일 − 30일 ~ + 120일(기준일 분기 실적이 6-K 로 온다 — 기간은 원문으로 가린다)"""
    기 = 날(기준일)
    한 = 기 + datetime.timedelta(days=허용)
    표 = 공시표(sub)
    정 = [r for r in 표 if r["양식"] in 정기양식 and 날(r["기간끝"])]
    앞 = sorted([r for r in 정 if 날(r["기간끝"]) <= 한], key=lambda r: (r["기간끝"], r["제출일"] or ""))
    낸 = {"기준": None, "직전": None, "연차": None, "뒤": [], "해외6K후보": [], "경보": []}
    if 앞:
        끝 = 앞[-1]["기간끝"]
        같은 = [r for r in 앞 if r["기간끝"] == 끝]
        낸["기준"] = min(같은, key=lambda r: r["제출일"] or "")
        먼저 = [r for r in 앞 if r["기간끝"] < 끝]
        if 먼저:
            p = 먼저[-1]["기간끝"]
            낸["직전"] = min([r for r in 먼저 if r["기간끝"] == p], key=lambda r: r["제출일"] or "")
        연 = [r for r in 앞 if r["양식"] in 연차양식]
        if 연:
            낸["연차"] = 연[-1]
    else:
        낸["경보"].append("기준일(%s) 앞 기간의 정기 보고가 submissions 에 없다" % 기준일)
    낸["뒤"] = sorted([r for r in 정 if 날(r["기간끝"]) > 한], key=lambda r: (r["기간끝"], r["제출일"] or ""))
    해외 = bool(낸["연차"] and 낸["연차"]["양식"] in ("20-F", "40-F")) or any(r["양식"] in ("20-F", "40-F") for r in 정)
    if 해외:
        아래, 위 = 기 - datetime.timedelta(days=30), 기 + datetime.timedelta(days=120)
        낸["해외6K후보"] = sorted([r for r in 표 if r["양식"] == "6-K" and 날(r["제출일"]) and 아래 <= 날(r["제출일"]) <= 위],
                              key=lambda r: r["제출일"])
    if 낸["기준"] and (기 - 날(낸["기준"]["기간끝"])).days > 100 and not 해외:
        낸["경보"].append("기준일 분기 보고가 아직 없다 — 마지막 정기 보고 기간 끝 %s(%s)" % (낸["기준"]["기간끝"], 낸["기준"]["양식"]))
    return 낸


def 표지(r, 고름):
    """행 하나의 「기준일과」 — 기준일분기 · 직전 · 뒤 · 이전."""
    if not r:
        return None
    if 고름.get("기준") and r["accession"] == 고름["기준"]["accession"]:
        return "기준일분기"
    if any(x and r["accession"] == x["accession"] for x in (고름.get("직전"), 고름.get("연차"))):
        return "직전"
    if any(r["accession"] == x["accession"] for x in 고름.get("뒤") or []):
        return "뒤"
    return "이전"


def 파일이름(양식, 기간끝):
    """sec_fetch 가 쓰는 원문 이름 — `10Q_202606.htm`(동인원천 · 조항추출이 이 꼴을 읽는다)."""
    return "%s_%s.htm" % (양식.replace("-", ""), (기간끝 or "")[:7].replace("-", ""))


# ══════════════════════════════════════════════════════════ 원문 → 글 · 절

def 글로(htm):
    h = re.sub(r"(?is)<(script|style|ix:header)[^>]*>.*?</\1>", " ", htm or "")
    h = re.sub(r"(?i)<br\s*/?>|</(p|div|tr|table|h\d|li|td|th)>", "\n", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    h = _html.unescape(h).replace("\xa0", " ").replace("​", "")
    h = h.replace(" ", " ").replace(" ", " ").replace(" ", " ")     # 좁은 빈칸(「December 31, 2025」 사이) — 날짜 · 수 꼴이 끊기지 않게
    h = re.sub(r"[ \t\r\f\v]+", " ", h)
    h = re.sub(r"\n\s*\n+", "\n", h)
    return h.strip()


def 절찾기(글, 시작꼴, 끝꼴, 최대=200_000):
    """목차의 짧은 줄을 건너뛰려 시작 · 끝 짝 가운데 가장 긴 구간을 고른다. → (조각 | "", 찾음)."""
    시작들 = [m.start() for m in re.finditer(시작꼴, 글, re.I)]
    best = (0, None)
    for s in 시작들:
        m = re.search(끝꼴, 글[s + 20:], re.I)
        e = s + 20 + m.start() if m else min(len(글), s + 최대)
        if e - s > best[0]:
            best = (e - s, (s, e))
    if not best[1] or best[0] < 400:
        return "", False
    s, e = best[1]
    return 글[s:e][:최대], True


def _느(말):
    """머리 낱말을 글자 사이 빈칸을 허용하는 꼴로 — 원문이 글자 모양(작은 대문자)으로 「B USINESS」처럼 끊긴다(F3 · F38)."""
    return r"\s*".join(re.escape(c) if c != " " else r"\s+" for c in 말).replace(r"\s*\s+\s*", r"\s+")


_항 = r"item\s*%s\s*[.:\-–—]?\s*"
_절꼴 = {
    "10-K": {"Item1": (_항 % "1" + _느("business") + r"\b", _항 % "1a" + _느("risk factors")),
             "Item2": (_항 % "2" + _느("properties") + r"\b", _항 % "3" + _느("legal")),
             "MDA": (_항 % "7" + _느("management") + r".{0,3}s?\s*" + _느("discussion"),
                     _항 % "7a" + r"|" + _항 % "8" + _느("financial statements"))},
    "10-Q": {"MDA": (_항 % "2" + _느("management") + r".{0,3}s?\s*" + _느("discussion"),
                     _항 % "3" + _느("quantitative") + r"|" + _항 % "4" + _느("controls"))},
    "20-F": {"Item1": (_항 % "4" + _느("information on the company"), _항 % "4a" + r"|" + _항 % "5" + _느("operating")),
             "Item2": (r"(?:4\s*\.?\s*d\s*\.?|\bd\s*\.)\s*" + _느("property") + r",?\s+" + _느("plant") + r"s?\s+" + _느("and equipment"),
                       _항 % "4a" + r"|" + _항 % "5" + _느("operating")),
             "MDA": (_항 % "5" + _느("operating and financial review"), _항 % "6" + _느("directors"))},
}
_절꼴["40-F"] = _절꼴["20-F"]
_절꼴["10-KT"] = _절꼴["10-K"]
# 항목 번호 없이 「Our Business」 · 「Management's Discussion and Analysis」 머리만 쓰고 끝에 교차 색인을 붙인 꼴(F3) — 번호 꼴을 못 찾을 때만
_절꼴대체 = {
    "Item1": (r"(?:^|\n)\s*(?:" + _느("our business") + r"|" + _느("business overview") + r"|" + _느("business") + r")\s*\n",
              _느("management") + r".{0,3}s?\s*" + _느("discussion") + r"|" + _느("risk factors") + r"\s*\n"),
    "MDA": (_느("management") + r".{0,3}s?\s*" + _느("discussion and analysis"),
            _느("quantitative and qualitative") + r"|" + _느("controls and procedures") + r"|" + _느("financial statements and supplementary") +
            r"|(?:^|\n)\s*" + _느("risk factors") + r"\s*\n"),
}


def 절찾기들(글, 양식, 키):
    """양식의 번호 꼴 → 못 찾으면 대체 꼴. → (조각, 찾음, 대체였나)."""
    꼴 = _절꼴.get(양식, _절꼴["10-K"]).get(키)
    if 꼴:
        조각, ok = 절찾기(글, *꼴)
        if ok:
            return 조각, True, False
    if 키 in _절꼴대체:
        조각, ok = 절찾기(글, *_절꼴대체[키])
        if ok:
            return 조각, True, True
    return "", False, False


def 원문들(raw):
    """`_raw` 의 미국 원문 → [{"양식", "파일", "기간끝키"}] — 이름 꼴: 10K_YYYYMM · 10Q_YYYYMM · 20F_YYYYMM · 40F_YYYYMM · 6K_YYYYMMDD_* · 8K_*
    (6-K 는 손으로 받은 폴더 `_raw/6k/` 의 ex99 조각도 줍는다)."""
    낸 = []
    for p in sorted(glob.glob(os.path.join(raw, "*.htm")) + glob.glob(os.path.join(raw, "*.html"))):
        n = os.path.basename(p)
        m = re.match(r"^(10K|10Q|20F|40F|10KT)_(\d{6})\.html?$", n)
        if m:
            낸.append({"양식": {"10K": "10-K", "10Q": "10-Q", "20F": "20-F", "40F": "40-F", "10KT": "10-KT"}[m.group(1)], "파일": p,
                      "기간키": m.group(2)})
            continue
        m = re.match(r"^(6K|8K)_([0-9\-]{6,10})", n, re.I)
        if m:
            낸.append({"양식": "6-K" if m.group(1).upper() == "6K" else "8-K", "파일": p, "기간키": re.sub(r"\D", "", m.group(2))})
    for p in sorted(glob.glob(os.path.join(raw, "6[kK]", "*.htm"))):
        if re.search(r"(?i)ex[-_]?99", os.path.basename(p)):
            낸.append({"양식": "6-K", "파일": p, "기간키": ""})
    return 낸


def _원문읽기(p):
    try:
        with io.open(p, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


def 원문짝(원, 행):
    """공시 행 → 그 원문 파일(이름의 기간 키로) | None."""
    if not 행:
        return None
    키 = (행.get("기간끝") or "")[:7].replace("-", "")
    for x in 원:
        if x["양식"] == 행["양식"] and x["기간키"] == 키:
            return x
    return None


# ══════════════════════════════════════════════════════════ companyfacts

def 개념틀(cf):
    f = (cf or {}).get("facts") or {}
    u, i = len(f.get("us-gaap") or {}), len(f.get("ifrs-full") or {})
    return "ifrs-full" if i > u else "us-gaap"


def _사실(cf, ns, 태그):
    """→ [(단위, 사실)] — 한 개념의 모든 단위."""
    낸 = []
    for 단위, xs in ((((cf or {}).get("facts") or {}).get(ns) or {}).get(태그) or {}).get("units", {}).items():
        for x in xs or []:
            낸.append((단위, x))
    return 낸


def _돈단위(u):
    return bool(re.fullmatch(r"[A-Z]{3}", u or ""))


def 통화들(cf, ns):
    """매출 · 자산 개념의 단위별 기간 → {단위: [가장 이른 끝, 가장 늦은 끝]} — 한 개념에 통화가 섞였는지(F61)."""
    낸 = {}
    for 태그 in ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "Assets", "Revenue"):
        for 단위, x in _사실(cf, ns, 태그):
            if not _돈단위(단위) or not x.get("end"):
                continue
            a = 낸.setdefault(단위, [x["end"], x["end"]])
            a[0], a[1] = min(a[0], x["end"]), max(a[1], x["end"])
    return 낸


def 주통화(cf, ns, 목표끝=None):
    통 = 통화들(cf, ns)
    if not 통:
        return "USD"
    if 목표끝:
        가 = [u for u, (a, b) in 통.items() if b >= 목표끝 >= a or b >= 목표끝]
        if 가:
            return max(가, key=lambda u: 통[u][1])
    return max(통, key=lambda u: 통[u][1])


def 시점값(cf, ns, 태그들, 한, 통화, 선호accn=None, 끝=None):
    """시점(instant) 값 — 끝 ≤ 한 가운데 가장 늦은 끝(끝 을 주면 그 끝 ± 3일만) · 같은 끝이면 선호 accession → 늦게 낸 것.
    → {"값", "끝", "accn", "양식", "제출", "태그", "단위"} | None."""
    후 = []
    for 태그 in 태그들:
        for 단위, x in _사실(cf, ns, 태그):
            if 통화 == "pure":
                if _돈단위(단위):                            # 사람 수 · 비율 — 돈 단위는 받지 않는다
                    continue
            elif 단위 != 통화:                              # 통화가 섞인 개념(F61)은 고른 통화만
                continue
            e = 날(x.get("end"))
            if not e or x.get("val") is None or e > 한:
                continue
            if 끝 and abs((e - 날(끝)).days) > 3:
                continue
            if x.get("start") and 태그 not in ("CapitalExpendituresIncurredButNotYetPaid",):
                continue
            후.append((x["end"], 1 if (선호accn and x.get("accn") == 선호accn) else 0, x.get("filed") or "", 태그들.index(태그), 태그, 단위, x))
    if not 후:
        return None
    후.sort(key=lambda t: (t[0], t[1], t[2], -t[3]))
    e, _, _, _, 태그, 단위, x = 후[-1]
    return {"값": x["val"], "끝": e, "accn": x.get("accn"), "양식": x.get("form"), "제출": x.get("filed"), "태그": "%s:%s" % (ns, 태그), "단위": 단위}


_fp길이 = {"Q1": 91, "Q2": 182, "H1": 182, "Q3": 273, "Q4": 365, "FY": 365}


def 보고fp(cf, ns, accn):
    """그 보고서(accession)의 fp(Q1 · Q2 · Q3 · FY) — 사실의 fp 칸에서."""
    if not accn:
        return None
    for 태그, 몸 in (((cf or {}).get("facts") or {}).get(ns) or {}).items():
        for xs in (몸.get("units") or {}).values():
            for x in xs:
                if x.get("accn") == accn and x.get("fp"):
                    return x["fp"]
    return None


def 누계값(cf, ns, 태그들, 목표끝, 통화, 선호accn=None, fp=None):
    """기간(duration) 값 — 끝이 목표끝 ± 3일 · **회계연도 누계 길이**(그 보고서의 fp: Q1 91 · Q2 182 · Q3 273 · FY 365일 ± 20일 —
    분기 보고서에 함께 실린 직전 12개월(TTM) 값을 고르지 않는다) · fp 를 모르면 372일 안에서 가장 긴 것 · 같은 길이면 선호 accession."""
    t = 날(목표끝)
    목길이 = _fp길이.get((fp or "").upper())
    후 = []
    for 태그 in 태그들:
        for 단위, x in _사실(cf, ns, 태그):
            if _돈단위(단위) and 단위 != 통화:
                continue
            s, e = 날(x.get("start")), 날(x.get("end"))
            if not (s and e and t) or x.get("val") is None or abs((e - t).days) > 3:
                continue
            길이 = (e - s).days
            if 길이 > 372 or 길이 < 60:
                continue
            if 목길이 and abs(길이 - 목길이) > 20:
                continue
            후.append((길이, 1 if (선호accn and x.get("accn") == 선호accn) else 0, -태그들.index(태그), x.get("filed") or "", 태그, x))
    if not 후:
        return None
    후.sort(key=lambda z: (z[0], z[1], z[2], z[3]))
    길이, _, _, _, 태그, x = 후[-1]
    return {"값": x["val"], "시작": x["start"], "끝": x["end"], "accn": x.get("accn"), "양식": x.get("form"), "fy": x.get("fy"), "fp": x.get("fp"),
            "태그": "%s:%s" % (ns, 태그), "길이": 길이}


def 기간ID(시작, 끝, fy=None):
    s, e = 날(시작), 날(끝)
    if not (s and e):
        return None
    달 = round((e - s).days / 30.44)
    머 = {3: "1Q", 6: "1H", 9: "9M", 12: "FY"}.get(달, "%dM" % 달)
    yy = ("%s" % (fy or e.year))[-2:]
    return "%s%sA" % (머, yy)


# ══════════════════════════════════════════════════════════ 숫자 · 문장

_배수 = {"thousand": 1e3, "thousands": 1e3, "million": 1e6, "millions": 1e6, "billion": 1e9, "billions": 1e9, "trillion": 1e12}
_돈꼴 = re.compile(r"\$\s?([0-9][0-9,]*(?:\.[0-9]+)?)\s*(thousand|million|billion|trillion)?\b", re.I)


def 돈(글):
    """첫 「$ 수 (million|billion)」 → 원 단위 수 | None."""
    m = _돈꼴.search(글 or "")
    if not m:
        return None
    try:
        v = float(m.group(1).replace(",", ""))
    except ValueError:
        return None
    return round(v * _배수.get((m.group(2) or "").lower(), 1.0), 2)


def 문장들(글):
    return [s.strip() for s in re.split(r"(?<=[.;])\s+(?=[A-Z(\"“])|\n", 글 or "") if len(s.strip()) > 20]


_약정낱말 = re.compile(r"(?i)(non-?cancel+able (?:purchase )?(?:commitments?|obligations?|orders?)|purchase obligations?|purchase commitments?|"
                    r"unconditional purchase|capital commitments?|funding commitments?|"
                    r"commit(?:ted|ments?) (?:for|to) (?:the )?(?:construction|capital|purchase)|committed\s+\$[^.;]{0,40}?\s(?:for|to)\s+(?:the\s+)?"
                    r"(?:construction|purchase|capital)|contractual (?:commitments?|obligations?)|leases? (?:that )?(?:have )?not yet commenced|"
                    r"not yet commenced|minimum (?:purchase|payment) commitments?|capacity (?:agreements?|commitments?|reservation))")
_성격꼴 = [("사용권", r"(?i)lease"), ("보증", r"(?i)guarant"),
         ("지분", r"(?i)equity (?:investment|interest|method)|capital contribution|joint venture|\bJVs?\b|funding commitment|\bfunds?\b|investment in|our investment"),
         ("설비취득", r"(?i)construction|capital expenditure|property(?:,)? (?:plant )?and equipment|equipment purchase|manufacturing equipment|buildings?"),
         ("재고공급", r"(?i)inventor|component|supplier|wafer|substrate|contract manufactur|raw material|supply"),
         ("비용", r"(?i)cloud|hosting|service|licen|software|marketing|energy|power|electricit|utilit"),
         ("혼합", r"(?i)purchase")]


def 성격추정(글):
    for 이름, 꼴 in _성격꼴:
        if re.search(꼴, 글 or ""):
            return 이름
    return "모름"


def _표위치들(htm):
    """원문의 표 → [(시작 자리, 줄들)] — 줄은 빈칸 · 「$」 · 「)」 · 보이지 않는 글자를 뺀 칸 목록."""
    낸 = []
    for m in re.finditer(r"(?is)<table\b.*?</table>", htm or ""):
        t = 표들(m.group(0))
        if not t:
            continue
        줄들 = []
        for r in t[0]:
            칸 = [re.sub(r"[​‌‍﻿]", "", c).strip() for c in r]
            칸 = [c for c in 칸 if c not in ("", "$", ")", "%", "(")]
            if 칸:
                줄들.append(칸)
        if 줄들:
            낸.append((m.start(), 줄들))
    return 낸


def _표배수(htm, 자리, 줄들):
    """표 머리 · 바로 앞 글 → 넓혀 가며(1,500자 → 4만 자 — 재무제표 첫머리 「(In millions of U.S. dollars)」) 단위 낱말을 찾는다."""
    표머리 = " ".join(" ".join(r) for r in 줄들[:3])
    for 폭 in (6000, 60000, 240000):
        앞 = 글로((htm or "")[max(0, 자리 - 폭):자리])
        앞 = 앞[-1500:] if 폭 == 6000 else 앞
        m = re.findall(r"(?i)\bin\s+(thousands|millions|billions)\b", 앞 + " " + 표머리)
        if m:
            return {"thousands": 1e3, "millions": 1e6, "billions": 1e9}[m[-1].lower()]
    return 1.0


_약정줄 = re.compile(r"(?i)^(?:total\s+)?(purchase (?:commitments?|obligations?)|construction commitments?|capital commitments?|unconditional purchase|"
                   r"(?:operating (?:and finance )?)?leases? (?:that )?(?:have )?not yet commenced|capacity (?:agreements?|commitments?)|"
                   r"(?:other|contractual) commitments?|non-?cancel+able purchase|funding commitments?|minimum purchase)")


def 약정표(htm, 출처, 기본기준일):
    """계약상 의무 · 약정 표(「(In millions) … Total」) → [{약정 한 줄}] — 합계 열 · 첫 해 열."""
    낸 = []
    for 자리, 줄들 in _표위치들(htm):
        머리 = next((r for r in 줄들[:4] if any(re.fullmatch(r"(?i)total", c) for c in r)), None)
        if not 머리:
            continue
        열 = [c for c in 머리 if not re.search(r"(?i)^\(?in (thousands|millions|billions)", c)]
        배 = _표배수(htm, 자리, 줄들)
        for r in 줄들:
            if not _약정줄.search(r[0]):
                continue
            수들 = [v for v in (_수칸(c) for c in r[1:]) if v is not None]
            if not 수들:
                continue
            열들 = 열[-len(수들):] if len(열) >= len(수들) else [None] * len(수들)
            ti = next((i for i, c in enumerate(열들) if c and re.fullmatch(r"(?i)total", c)), len(수들) - 1)
            첫 = 수들[0] * 배 if (len(수들) >= 2 and 열들[0] and re.search(r"(?i)less than|within|^1 year|^20\d\d$|next", 열들[0])) else None
            이름 = re.sub(r"\s*\([a-z0-9]\)\s*$", "", r[0]).strip()
            낸.append({"이름": 이름.lower(), "금액": 수들[ti] * 배, "통화": "USD", "기준일": 기본기준일, "성격후보": 성격추정(이름), "원천": "표",
                      "태그": None, "기간별": {"1년내": 첫, "이후": (수들[ti] * 배 - 첫) if 첫 is not None else None}, "출처": 출처,
                      "근거": " ; ".join(r)[:120]})
    return 낸


_날꼴 = re.compile(r"(?i)(?:as of|at)\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s*(20\d\d)")
_달 = {m: i + 1 for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november",
                                         "december"])}


def 문장날(s):
    m = _날꼴.search(s or "")
    if not m:
        return None
    try:
        return datetime.date(int(m.group(3)), _달[m.group(1).lower()], int(m.group(2))).isoformat()
    except ValueError:
        return None


def 돈확실(글):
    """「$ 수 + (million|billion…)」 꼴만 — 단위 낱말이 없는 작은 수(표 단위를 문장이 생략한 「$ 6.8 in 2026」)는 단위를 몰라 버린다."""
    m = _돈꼴.search(글 or "")
    if not m:
        return None
    try:
        v = float(m.group(1).replace(",", ""))
    except ValueError:
        return None
    if not m.group(2) and v < 1e5:
        return None
    return round(v * _배수.get((m.group(2) or "").lower(), 1.0), 2)


def _약정이름(s):
    s = re.sub(r"(?i)\$\s?[\d.,]+\s*(?:thousand|million|billion|trillion)?\s*", "", (s or "").strip().lower())
    return re.sub(r"\s+", " ", s)[:60].strip()


def 약정문장(글, 출처, 기본기준일):
    """약정 문장 → [{이름 · 금액 · 기준일 · 성격후보 · 원천 "문장" · 출처 · 근거(120자 안)}]. 금액이 「$ … million/billion」로 붙은 문장만 ·
    그 문서 기간 끝보다 앞 날짜(비교 기간)의 문장은 버린다."""
    낸 = []
    기본 = 날(기본기준일)
    for s in 문장들(글):
        m = _약정낱말.search(s)
        if not m or re.search(r"(?i)prepayments?|prepaid|we paid|were paid|have been funded|funded as of", s[m.start() - 80 if m.start() > 80 else 0:m.start()]):
            continue
        v = 돈확실(s[m.start():]) or (돈확실(s[:m.start()]) if "committed" not in m.group(1).lower() else None)
        if not v:
            continue
        날짜 = 문장날(s) or 기본기준일
        if 기본 and 날(날짜) and (기본 - 날(날짜)).days > 허용일:
            continue
        낸.append({"이름": _약정이름(m.group(1)), "금액": v, "통화": "USD", "기준일": 날짜, "성격후보": 성격추정(s), "원천": "문장",
                  "태그": None, "기간별": {"1년내": None, "이후": None}, "출처": 출처, "근거": s[:120],
                  "결산일후": bool(re.search(r"(?i)subsequent to (?:the )?(?:end of|period|year|quarter|[A-Z][a-z]+ \d)", s))})
    return 낸


_capex말 = re.compile(r"(?i)(capital expenditures?|capex|capital spending|capital investments?|purchases of property(?:,)? (?:plant )?and equipment|"
                     r"investments? in property(?:,)? (?:plant )?and equipment)")
_기대말 = re.compile(r"(?i)\b(expect|anticipat|estimat|plan(?:s|ned)? to|project(?:ed|s)?|guid|outlook|forecast|intend|will be|to be (?:in the range|approximately|between))")
_범위꼴 = re.compile(r"(?i)\$\s?([0-9][0-9,]*(?:\.[0-9]+)?)\s*(thousand|million|billion)?\s*(?:to|-|–|and)\s*(?:U\.?S\.?\s?)?\$?\s?([0-9][0-9,]*(?:\.[0-9]+)?)\s*(thousand|million|billion)")
_넘꼴 = re.compile(r"(?i)(more than|greater than|over|in excess of|at least|exceed(?:ing)?)\s+\$\s?([0-9][0-9,]*(?:\.[0-9]+)?)\s*(thousand|million|billion)?")
_기간꼴 = re.compile(r"(?i)(fiscal(?: year)?\s*(?:20)?\d\d|calendar(?: year)?\s*20\d\d|\b20\d\d\b|full[- ]year|next (?:twelve|12) months|remainder of (?:the )?(?:fiscal )?(?:year|20\d\d))")


_주어꼴 = re.compile(r"(?i)\b(we|our|us|the company|management)\b")
_과거말 = re.compile(r"(?i)(were|was|totaled|totalled|amounted to|spent|incurred|paid)")
_자금조달꼴 = re.compile(r"(?i)\b(net proceeds|offering|notes due|issuance of|borrowings? under|credit facility|use of proceeds)\b")


def _돈글(v):
    return ("$%.3gB" % (v / 1e9)) if abs(v) >= 1e9 else ("$%.3gM" % (v / 1e6))
_단위투자꼴 = re.compile(r"(?i)\b(?:per|each|every|for each)\s+(?:each\s+)?(?:additional\s+|incremental\s+)?"
                     r"(gigawatt|GW|megawatt|MW|GWh|unit|wafer|vehicle|ton)s?\b")


def _금액들(s):
    """문장 → (하한, 상한) | None — 범위 · 「… 이상」 · 단일 값."""
    m = _범위꼴.search(s)
    if m:
        b2 = _배수.get((m.group(4) or "").lower(), 1.0)
        b1 = _배수.get((m.group(2) or "").lower(), b2)
        return round(float(m.group(1).replace(",", "")) * b1, 2), round(float(m.group(3).replace(",", "")) * b2, 2)
    m2 = _넘꼴.search(s)
    if m2 and (m2.group(3) or float(m2.group(2).replace(",", "")) >= 1e5):
        return round(float(m2.group(2).replace(",", "")) * _배수.get((m2.group(3) or "").lower(), 1.0), 2), None
    v = 돈확실(s)
    return (v, v) if v else None


def 단위투자문장(글, 출처):
    """「추가 1 GW 마다 $100~150 million」 꼴 — capex 가이던스가 아니라 능력 한 단위당 투자의 회사 발언 → 능력문장 줄."""
    낸 = []
    for s in 문장들(글):
        u = _단위투자꼴.search(s)
        if not (u and _capex말.search(s) and "$" in s):
            continue
        g = _금액들(s)
        if not g:
            continue
        낸.append({"문장": s[:120], "값": g[0], "상한": g[1], "단위": "USD per %s(투자)" % u.group(1), "출처": 출처})
    return 낸


# 금액 없는 방향 가이던스(R7 — 2026-10-25 FX2-C) — 「we expect … capital expenditures … to increase (relative to 2025)」 꼴. 연차 · 분기 보고의 MD&A 는
# 금액을 콜에서만 말하고 보고서에는 방향만 적는 일이 많다(유니버스 미국 21곳 실측 — 금액 문장 4곳 · 방향 문장 더 여럿).
# 방향 낱말은 **동사의 보어 자리**에서만 — 「to (significantly) increase」 · 「to be higher than」 · 「increased capital investments」.
# 「to support growth」 · 「to expand production capacity」(목적) 는 방향이 아니다.
_부사 = r"(?:(?:significantly|substantially|meaningfully|materially|modestly|slightly|further|continue to|again)\s+){0,2}"
_방향말 = [("증가", re.compile(r"(?i)^\W*(?:\w+\W+){0,8}?(?:to\s+" + _부사 + r"(?:increase|grow|rise|accelerate|step up)\b|to\s+be\s+" + _부사
                                + r"(?:higher|greater|above)\b|(?:increased|higher|elevated|greater)\s+(?:capital|capex|investments?|spending)\b)")),
          ("감소", re.compile(r"(?i)^\W*(?:\w+\W+){0,8}?(?:to\s+" + _부사 + r"(?:decrease|decline|fall|moderate)\b|to\s+be\s+" + _부사
                                + r"(?:lower|below)\b|(?:decreased|lower|reduced)\s+(?:capital|capex|investments?|spending)\b)")),
          ("유사", re.compile(r"(?i)^\W*(?:\w+\W+){0,8}?(?:to\s+(?:be|remain)\s+" + _부사
                                + r"(?:similar to|comparable to|consistent with|in line with|flat|roughly the same|approximately the same|about the same)\b)"))]
_기대동사 = re.compile(r"(?i)\b(expect\w*|anticipat\w*|plan(?:s|ned)? to|intend\w*|project(?:s|ed)? (?:that|to)|estimat\w* (?:that|to)|will)\b")
_불확실말 = re.compile(r"(?i)\b(may|might|could)\b|forward-looking statement|risk factors?|there can be no assurance")
_비교꼴 = re.compile(r"(?i)(?:relative to|compared (?:to|with)|than|over|versus|vs\.?)\s+(?:the\s+)?(?:fiscal\s+(?:year\s+)?|calendar\s+(?:year\s+)?|year\s+)?((?:20)?\d\d)\b")
_해꼴 = re.compile(r"(?i)\b(?:in|for|during|through)\s+(?:the\s+)?(?:fiscal\s+(?:year\s+)?|calendar\s+(?:year\s+)?|year\s+)?(20\d\d)\b|\bfiscal\s+(?:year\s+)?(20\d\d|\d\d)\b")


def 방향가이던스(s, 공표일):
    """문장 하나 → {방향 · 기간 · 비교기간} | None — 회사 주어 · 미래 동사 뒤 120자 안에 방향 낱말 · 동사 앞뒤 150자 안에 capex 낱말.
    가정 · 위험 문장(may · could · forward-looking · risk factors)과 자금 조달 문장은 아니다. 기간이 공표 해보다 앞이면 지난 이야기다."""
    if _불확실말.search(s) or _자금조달꼴.search(s) or _단위투자꼴.search(s) or not _주어꼴.search(s):
        return None
    for v in _기대동사.finditer(s):
        뒤 = s[v.end():v.end() + 120]
        if not _capex말.search(s[max(0, v.start() - 350):v.end() + 150]):
            continue                                          # 「Cash capital expenditures were … , both of which we expect to increase」 — 앞말을 받는 문장
        방 = None
        for 이름, 꼴 in _방향말:
            m = 꼴.search(뒤)
            if m and (방 is None or m.start() < 방[1]):
                방 = (이름, m.start())
        if not 방:
            continue
        창 = s[max(0, v.start() - 80):v.end() + 150]
        비 = _비교꼴.search(창)
        비교 = None
        if 비:
            y = 비.group(1)
            비교 = y if len(y) == 4 else "20" + y
        해들 = []
        for m in _해꼴.finditer(창):
            y = m.group(1) or m.group(2)
            y = y if len(y) == 4 else "20" + y
            if y != 비교:
                해들.append(y)
        기간 = None
        if 해들:
            뒤해 = [y for y in 해들 if not 공표일 or int(y) >= int(공표일[:4])]
            기간 = (뒤해 or 해들)[0]
        if 기간 and 공표일 and int(기간) < int(공표일[:4]):
            return None                                       # 지난 해 이야기
        return {"방향": 방[0], "기간": 기간, "비교기간": 비교}
    return None


def capex가이던스(글, 출처, 공표일, 기준일):
    """capex 가이던스 문장 → [{문장(요약) · 기간 · 하한 · 상한 · 통화 · 금융리스포함 · 공표일 · 기준일뒤 · 출처 · 방향 · 비교기간}].
    회사가 주어인 문장(we · our)만 · 「per GW」 꼴은 단위 투자(능력문장)로 보낸다 · 금액은 capex 낱말 둘레 200자 안.
    금액이 없으면 **방향 가이던스**(증가 · 감소 · 유사 — `방향가이던스`)를 하한 · 상한 없이 낸다(2026-10-25 R7)."""
    낸, 본 = [], set()
    for s in 문장들(글):
        c = _capex말.search(s)
        금액문장 = bool(c and _기대말.search(s) and "$" in s and _주어꼴.search(s)) and not _단위투자꼴.search(s) and not _자금조달꼴.search(s)
        if not 금액문장 or not _금액가이던스있나(s, c, 공표일):
            if c:
                방 = 방향가이던스(s, 공표일)
                if 방:
                    키 = (방["기간"], 방["방향"], 방["비교기간"])
                    if 키 not in 본:
                        본.add(키)
                        리 = (True if re.search(r"(?i)including (?:principal payments on )?finance leases?", s)
                              else False if re.search(r"(?i)exclud\w* finance leases?", s) else None)
                        낸.append({"문장": "capex %s %s(%s · 금액 없음)" % (방["기간"] or "(기간 미상)", 방["방향"],
                                                                     ("%s 대비" % 방["비교기간"]) if 방["비교기간"] else "비교 기간 없음"),
                                  "기간": 방["기간"], "하한": None, "상한": None, "통화": "USD", "금융리스포함": 리, "공표일": 공표일,
                                  "기준일뒤": bool(공표일 and 기준일 and 공표일 > 기준일), "출처": 출처,
                                  "방향": 방["방향"], "비교기간": 방["비교기간"]})
            continue
        창 = s[max(0, c.start() - 200):c.end() + 200]
        돈자리 = _돈꼴.search(창)
        if not 돈자리:
            continue
        앞 = 창[max(0, 돈자리.start() - 160):돈자리.start()]
        if not _기대말.search(앞) or _과거말.search(앞[(_기대말.search(앞).end()):] if _기대말.search(앞) else 앞):
            continue
        g = _금액들(창[max(0, 돈자리.start() - 40):])
        if not g:
            continue
        하, 상 = g
        p = _기간꼴.search(창) or _기간꼴.search(s)
        기간 = re.sub(r"\s+", " ", p.group(1)).strip() if p else None
        연 = re.search(r"(20\d\d)|(?:fiscal(?: year)?\s*)(\d\d)", 기간 or "")
        if 연 and 공표일:
            y = int(연.group(1)) if 연.group(1) else 2000 + int(연.group(2))
            if y < int(공표일[:4]):
                continue                                         # 지난 해 기간의 금액 — 가이던스가 아니다
        리스 = (True if re.search(r"(?i)including (?:principal payments on )?finance leases?", s)
              else False if re.search(r"(?i)exclud\w* finance leases?", s) else None)
        키 = (기간, 하, 상)
        if 키 in 본:
            continue
        본.add(키)
        요약 = "capex %s %s" % (기간 or "(기간 미상)",
                              ("%s~%s" % (_돈글(하), _돈글(상))) if (상 and 하 != 상) else (("%s 이상" % _돈글(하)) if 상 is None else _돈글(하)))
        낸.append({"문장": 요약, "기간": 기간, "하한": 하, "상한": 상, "통화": "USD", "금융리스포함": 리스, "공표일": 공표일,
                  "기준일뒤": bool(공표일 and 기준일 and 공표일 > 기준일), "출처": 출처, "방향": None, "비교기간": None})
    return 낸


def _금액가이던스있나(s, c, 공표일):
    """금액 가이던스 문장인가(아래 금액 길과 같은 거름) — 아니면 방향 가이던스 길로 보낸다."""
    창 = s[max(0, c.start() - 200):c.end() + 200]
    돈자리 = _돈꼴.search(창)
    if not 돈자리:
        return False
    앞 = 창[max(0, 돈자리.start() - 160):돈자리.start()]
    기 = _기대말.search(앞)
    if not 기 or _과거말.search(앞[기.end():]):
        return False
    return bool(_금액들(창[max(0, 돈자리.start() - 40):]))


_능력꼴 = re.compile(r"(?i)(\d[\d,]*(?:\.\d+)?)\s*(gigawatts?|GW|megawatts?|MW|GWh|MWh|wafers?\s+(?:starts\s+)?per\s+(?:month|year)|"
                    r"units?\s+per\s+(?:year|annum)|vehicles?\s+per\s+year|(?:metric\s+)?tons?\s+per\s+(?:year|annum)|square\s+feet)\b")
_능력맥 = re.compile(r"(?i)capacity|capable|produc|manufactur|data cent|facilit|power|plant|\bfab\b|factory|cleanroom")


def 능력문장(글, 출처, 최대=30):
    낸, 본 = [], set()
    for s in 문장들(글):
        for m in _능력꼴.finditer(s):
            단 = re.sub(r"\s+", " ", m.group(2)).strip()
            if "square" in 단.lower() and not re.search(r"(?i)manufactur|production|fab\b|cleanroom|factory", s):
                continue
            if not _능력맥.search(s):
                continue
            try:
                v = float(m.group(1).replace(",", ""))
            except ValueError:
                continue
            키 = (v, 단.lower())
            if 키 in 본:
                continue
            본.add(키)
            낸.append({"문장": s[:120], "값": v, "단위": 단, "출처": 출처})
            if len(낸) >= 최대:
                return 낸
    return 낸


# ══════════════════════════════════════════════════════════ 원문 표(유형자산 자산군 — 태그가 없을 때)

class _표모음(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.표들, self._표, self._줄, self._칸, self._깊이 = [], None, None, None, 0

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t == "table":
            self._깊이 += 1
            if self._깊이 == 1:
                self._표 = []
        elif self._표 is not None:
            if t == "tr":
                self._줄 = []
            elif t in ("td", "th") and self._줄 is not None:
                self._칸 = []

    def handle_endtag(self, tag):
        t = tag.lower()
        if t == "table":
            self._깊이 -= 1
            if self._깊이 == 0 and self._표 is not None:
                self.표들.append(self._표)
                self._표 = None
        elif t in ("td", "th") and self._칸 is not None and self._줄 is not None:
            self._줄.append(re.sub(r"\s+", " ", "".join(self._칸)).strip())
            self._칸 = None
        elif t == "tr" and self._줄 is not None and self._표 is not None:
            self._표.append(self._줄)
            self._줄 = None

    def handle_data(self, d):
        if self._칸 is not None:
            self._칸.append(d)


def 표들(htm):
    p = _표모음()
    try:
        p.feed(htm or "")
    except Exception:                                # noqa: BLE001 — 깨진 원문은 표 없음으로
        return []
    return p.표들


def _수칸(c):
    c = (c or "").replace("$", "").replace(",", "").strip()
    if c in ("", "—", "–", "-"):
        return None
    음 = c.startswith("(") and c.endswith(")")
    c = c.strip("()").strip()
    try:
        v = float(c)
    except ValueError:
        return None
    return -v if 음 else v


_자산군낱말 = re.compile(r"(?i)^(land|buildings?|building and|construction in progress|machinery|equipment|servers?|network|leasehold|furniture|computer|"
                      r"vehicles?|software|production equipment|manufacturing equipment|technical infrastructure|data cent|facilit|aircraft|tools)")
_합계낱말 = re.compile(r"(?i)(total property|property(?:,)? (?:plant )?and equipment(?:,)?\s*(?:at cost|gross|in service)|^gross property|^total$|"
                     r"total, at cost|property and equipment, gross|gross carrying|^property(?:,)? (?:plant )?and equipment\s*(?:\(\d\))?$)")
_미가동낱말 = re.compile(r"(?i)(not yet (?:in|placed (?:in|into)) service|assets not yet in use|construction in progress)")


def 유형자산표_원문(htm, 기간끝):
    """10-K 유형자산 주석 표 → {"자산군": {줄 이름: 값}, "합계", "검산차", "단위배", "열연도"} | None.
    연도 열은 **머리의 연도로** 고른다(위치로 고르면 연도 열이 뒤바뀐 표에서 틀린다 — F37)."""
    목표연도 = (기간끝 or "")[:4]
    if not 목표연도:
        return None
    글 = htm or ""
    for 자리, 줄들 in _표위치들(글):
        이름들 = [r[0] for r in 줄들 if r]
        군수 = sum(1 for n in 이름들 if _자산군낱말.search(n))
        if not (군수 >= 2 or (군수 >= 1 and any(_합계낱말.search(n) for n in 이름들))):
            continue
        if not any(re.search(r"(?i)accumulated depreciation", n) for n in 이름들):
            continue
        연도열 = None
        for r in 줄들[:6]:
            ys = [re.search(r"\b(20\d\d)\b", c).group(1) for c in r if re.search(r"\b(20\d\d)\b", c)]
            if len(ys) >= 2:
                연도열 = ys
                break
        if not 연도열 or 목표연도 not in 연도열:
            continue
        k = 연도열.index(목표연도)
        자, 합, 상각뒤 = {}, None, False
        for r in 줄들:
            n = r[0]
            if not re.search(r"[A-Za-z]", n) or re.fullmatch(r"(?i)[\s\-–—]*(december|june|september|march|as of).*", n):
                continue                                          # 머리 줄(연도 · 날짜) — 값 줄이 아니다
            수들 = [v for v in (_수칸(c) for c in r[1:]) if v is not None]
            if len(수들) < len(연도열):
                continue
            v = 수들[-len(연도열):][k]
            if re.search(r"(?i)accumulated depreciation|^less\b", n):
                상각뒤 = True
                continue
            if 상각뒤:
                # 「Add: assets not yet in service」 — 상각 줄 뒤에 붙는 미가동 자산(총액에 더한다 · 순액 줄은 버린다)
                if _미가동낱말.search(n) and not re.search(r"(?i)\bnet\b", n):
                    자[re.sub(r"(?i)^add:\s*", "", n)] = v
                    합 = (합 or 0) + v if 합 is not None else None
                continue
            if _합계낱말.search(n):
                합 = v
            elif _자산군낱말.search(n) or not re.search(r"(?i)total", n):
                자[n] = v
        if not 자:
            continue
        배 = _표배수(글, 자리, 줄들)
        자 = {n: round(v * 배, 2) for n, v in 자.items()}
        합 = round(합 * 배, 2) if 합 is not None else None
        차 = round((sum(자.values()) - 합) / 합, 6) if 합 else None
        return {"자산군": 자, "합계": 합, "검산차": 차, "단위배": 배, "열연도": 연도열}
    return None


def _묵음(끝, 목표끝, 날수=400):
    """값의 끝이 목표끝보다 날수 넘게 앞이면 묵은 값 — 태그를 그만 쓴 회사의 옛 값(F37 · 합계와 자산군의 기간이 갈린다)."""
    return bool(끝 and 목표끝 and (날(목표끝) - 날(끝)).days > 날수)


def 유형자산표_태그(cf, ns, 설, 한, 통화, accn, 목표끝=None):
    군설 = (설.get("유형자산군") or {})
    합 = 시점값(cf, ns, (군설.get("합계") or {}).get(ns) or [], 한, 통화, accn)
    if not 합 or _묵음(합["끝"], 목표끝):
        return None
    자 = {}
    for 이름, 태그들 in (군설.get("군") or {}).items():
        v = 시점값(cf, ns, 태그들, 한, 통화, accn, 끝=합["끝"])
        if v:
            자[이름] = v["값"]
    꼴 = re.compile(군설.get("확장정규식") or r"^$")
    for 공간, 태그들 in (((cf or {}).get("facts") or {}).items()):
        if 공간 in 본뜻공간:
            continue
        for 태그 in 태그들:
            if 꼴.search(태그):
                v = 시점값(cf, 공간, [태그], 한, 통화, accn, 끝=합["끝"])
                if v:
                    자[태그] = v["값"]
    차 = round((sum(자.values()) - 합["값"]) / 합["값"], 6) if (자 and 합["값"]) else None
    return {"기준일": 합["끝"], "자산군": 자, "합계": 합["값"], "검산차": 차, "단위": 통화, "출처": "companyfacts %s(%s)" % (합["태그"], 합["accn"])}


# ══════════════════════════════════════════════════════════ 조립

def 약정_태그(cf, ns, 설, 한, 통화, accn, 목표끝=None):
    낸 = []
    목록 = 설.get("약정") if ns == "us-gaap" else 설.get("약정_ifrs")
    for e in 목록 or []:
        if e.get("꼴") == "기간":
            v = None
            for 단위, x in _사실(cf, ns, e["태그"]):
                d = 날(x.get("end"))
                if 단위 == 통화 and d and d <= 한 and (v is None or x["end"] > v["끝"] or (x["end"] == v["끝"] and x.get("accn") == accn)):
                    v = {"값": x["val"], "끝": x["end"], "accn": x.get("accn"), "태그": "%s:%s" % (ns, e["태그"])}
        else:
            v = 시점값(cf, ns, [e["태그"]], 한, 통화, accn)
        if not v or _묵음(v["끝"], 목표끝):
            continue
        일년 = None
        for t in ((e.get("기간별") or {}).get("1년내") or []):
            w = 시점값(cf, ns, [t], 한, 통화, accn, 끝=v["끝"])
            if w:
                일년 = w["값"]
                break
        낸.append({"이름": e.get("이름") or e["태그"], "금액": v["값"], "통화": 통화, "기준일": v["끝"], "성격후보": e.get("성격후보") or "모름",
                  "원천": "태그", "태그": v["태그"], "기간별": {"1년내": 일년, "이후": (v["값"] - 일년) if 일년 is not None else None},
                  "출처": "companyfacts %s(%s)" % (v["태그"], v.get("accn"))})
    # 회사 확장 태그
    꼴들 = [re.compile(x) for x in 설.get("약정_확장정규식") or []]
    성꼴 = [(re.compile(a), b) for a, b in 설.get("확장_성격") or []]
    for 공간, 태그들 in (((cf or {}).get("facts") or {}).items()):
        if 공간 in 본뜻공간:
            continue
        for 태그 in 태그들:
            if not any(c.search(태그) for c in 꼴들):
                continue
            v = 시점값(cf, 공간, [태그], 한, 통화, accn)
            if not v or _묵음(v["끝"], 목표끝):
                continue
            성 = next((b for a, b in 성꼴 if a.search(태그)), "모름")
            낸.append({"이름": 태그, "금액": v["값"], "통화": 통화, "기준일": v["끝"], "성격후보": 성, "원천": "태그", "태그": v["태그"],
                      "기간별": {"1년내": None, "이후": None}, "출처": "companyfacts %s(%s)" % (v["태그"], v.get("accn"))})
    return 낸


def _겹침(a, 목록):
    for b in 목록:
        if a.get("금액") and b.get("금액") and abs(a["금액"] - b["금액"]) <= 0.01 * max(abs(a["금액"]), abs(b["금액"])):
            return True
    return False


_인원수 = r"([0-9]{1,3}(?:,[0-9]{3})+|[0-9]{2,7}(?:\.[0-9]+)?(?:\s*(?:million|thousand))?)"
_인원낱말 = r"(?:full[- ]time\s+|part[- ]time\s+|regular\s+|total\s+)?(?:employees|people|persons|team members|associates|staff|workers|personnel|individuals)"
_날말 = r"((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+20\d\d|\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+20\d\d)"
_인원꼴들 = [
    # 「As of December 31, 2025, <회사> had 190,820 employees」 · 「As of …, we employed approximately 1,576,000 full-time and part-time employees」
    ("기준일문장", re.compile(r"(?i)(?:as of|as at|at)\s+" + _날말 + r",?\s+[^.;]{0,80}?\b(?:had|has|have|employed|employs|employ)\s+"
                             r"(?:a\s+(?:total\s+)?(?:of\s+)?|an?\s+)?(?:approximately|about|around|over|more than|nearly|roughly|some)?\s*" + _인원수
                             + r"(?:\s+\d{1,2})?\s+(?:[\w\-]+\s+){0,5}?" + _인원낱말 + r"\b")),
    # 「we had a 1,132 person-strong team」
    ("사람팀", re.compile(r"(?i)" + _인원수 + r"[\s\-]+person(?:[\s\-]+strong)?\s+(?:team|workforce)")),
    # 「our workforce, which was comprised of 85,100 1 people as of December 27, 2025」(각주 번호가 수와 낱말 사이에 낀다)
    ("인력문장", re.compile(r"(?i)(?:workforce|headcount)[,]?\s+(?:which\s+)?(?:was\s+|is\s+|were\s+)?(?:comprised of|composed of|consisted of|consisting of|"
                            r"totaled|totalled|numbered|of|was|is)\s+(?:approximately\s+|about\s+|over\s+|more than\s+)?" + _인원수
                            + r"(?:\s+\d{1,2})?\s+(?:[\w\-]+\s+){0,3}?(?:people|employees|persons)(?:\s+as of\s+" + _날말 + r")?")),
]


def _인원값(g):
    g = (g or "").lower().replace(",", "").strip()
    try:
        if "million" in g:
            return int(float(g.replace("million", "").strip()) * 1_000_000)
        if "thousand" in g:
            return int(float(g.replace("thousand", "").strip()) * 1_000)
        return int(float(g))
    except ValueError:
        return None


def _글날(s):
    """「December 31, 2025」 · 「31 December 2025」 → date | None."""
    if not s:
        return None
    m = re.match(r"(?i)([a-z]+)\s+(\d{1,2}),?\s+(20\d\d)", s.strip())
    if m and m.group(1).lower() in _달:
        try:
            return datetime.date(int(m.group(3)), _달[m.group(1).lower()], int(m.group(2)))
        except ValueError:
            return None
    m = re.match(r"(?i)(\d{1,2})\s+([a-z]+)\s+(20\d\d)", s.strip())
    if m and m.group(2).lower() in _달:
        try:
            return datetime.date(int(m.group(3)), _달[m.group(2).lower()], int(m.group(1)))
        except ValueError:
            return None
    return None


def _인원표(글, 한):
    """20-F 「Employees」 절의 표 — 머리의 연도 열 · 「Total」 줄 → (값, 연도) | None. 기준일 해 이하 가장 늦은 열."""
    for m in re.finditer(r"(?im)^\s*(?:[A-Z]\.\s*)?employees(?:\s+and\s+[\w ]{0,40})?\s*$", 글):
        조각 = 글[m.end():m.end() + 4000]
        줄들 = [x.strip() for x in 조각.split("\n") if x.strip()]
        해들, 합 = [], None
        for i, x in enumerate(줄들):
            if re.fullmatch(r"20\d\d", x) and not 합:
                if 해들 and int(x) != int(해들[-1]) + 1:
                    해들 = []
                해들.append(x)
            elif re.fullmatch(r"(?i)total", x) and len(해들) >= 1:
                수들 = []
                for y in 줄들[i + 1:i + 1 + len(해들)]:
                    v = _인원값(y) if re.fullmatch(r"[0-9][0-9,]*", y) else None
                    if v is None:
                        break
                    수들.append(v)
                if len(수들) == len(해들):
                    짝 = [(int(h), v) for h, v in zip(해들, 수들) if int(h) <= 한.year]
                    if 짝:
                        h, v = max(짝)
                        if 10 <= v <= 5_000_000:
                            return v, h
                break
    return None


def 본문인원(글, 한):
    """연차 보고 본문(글로) → {값 · 기준일 · 근거 · 꼴} | None — PN 정규식이 못 읽은 꼴(기준일 문장 · 「N person-strong team」 ·
    각주 번호가 낀 「workforce … N 1 people」 · 20-F 「Employees」 표). 기준일(+허용) 뒤 날짜는 버리고 가장 늦은 날짜 → 큰 수."""
    후 = []
    for 꼴이름, 꼴 in _인원꼴들:
        for m in 꼴.finditer(글 or ""):
            수자리 = [g for g in m.groups() if g and re.match(r"^[0-9]", g) and not _글날(g)]
            if not 수자리:
                continue
            g = 수자리[0]
            if re.fullmatch(r"(19|20)\d\d", g.replace(",", "")) and "," not in g:
                continue                                      # 연도
            v = _인원값(g)
            if v is None or v < 10 or v > 5_000_000:
                continue
            날 = next((d for d in (_글날(x) for x in m.groups() if x) if d), None)
            if not 날:
                앞 = (글 or "")[max(0, m.start() - 160):m.start()]
                날 = next((d for d in (_글날(x.group(1)) for x in re.finditer(r"(?i)(?:as of|as at)\s+" + _날말, 앞)) if d), None)
            if 날 and 날 > 한:
                continue
            후.append((날 or datetime.date(1900, 1, 1), v, 꼴이름, re.sub(r"\s+", " ", m.group(0))[:160]))
    표 = _인원표(글 or "", 한)
    if 표:
        v, h = 표
        후.append((datetime.date(h, 12, 31), v, "20-F 표", "Employees 표 Total %d" % h))
    if not 후:
        return None
    후.sort(key=lambda x: (x[0], x[2] == "20-F 표", x[1]), reverse=True)
    날, v, 꼴이름, 근거 = 후[0]
    return {"값": v, "기준일": None if 날.year == 1900 else 날.isoformat(), "근거": 근거, "꼴": 꼴이름}


def 인원(raw, 연차원문, cf, 한):
    p = os.path.join(raw, "직원수_10K.json")
    j = _읽기(p)
    if isinstance(j, dict):
        행 = [r for r in j.get("행") or [] if r.get("직원수") and 날(r.get("기간끝")) and 날(r["기간끝"]) <= 한]
        if 행:
            r = max(행, key=lambda r: r["기간끝"])
            return {"값": r["직원수"], "기준일": r["기간끝"], "출처": "직원수_10K.json %s %s(%s)" % (r.get("양식"), r.get("접수번호"), r.get("자리")),
                    "원천": "PN"}
    v = 시점값(cf, "dei", ["EntityNumberOfEmployees"], 한, "pure")
    if v:
        return {"값": v["값"], "기준일": v["끝"], "출처": "companyfacts dei:EntityNumberOfEmployees(%s)" % v.get("accn"), "원천": "태그"}
    if 연차원문:
        try:
            import sec_상세변수 as _P                        # noqa: PLC0415 — PN 갈래의 정규식(같은 꼴을 두 곳에 두지 않는다)
            n, 자리, 글 = _P.본문직원(_원문읽기(연차원문["파일"]))
        except Exception:                            # noqa: BLE001
            n = None
        if n:
            return {"값": n, "기준일": None, "출처": "%s 본문(%s · sec_상세변수.본문직원)" % (os.path.basename(연차원문["파일"]), 자리), "원천": "본문"}
        # PN 정규식이 못 읽은 꼴 — 기준일 문장 · 「person-strong team」 · 각주가 낀 workforce 문장 · 20-F 표(R6 — 2026-10-25)
        b = 본문인원(글로(_원문읽기(연차원문["파일"])), 한)
        if b:
            return {"값": b["값"], "기준일": b["기준일"], "출처": "%s 본문(%s · %s)" % (os.path.basename(연차원문["파일"]), b["꼴"], b["근거"][:80]),
                    "원천": "본문"}
    return None


def _기준일말들(기준일):
    기 = 날(기준일)
    달이름 = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    낸 = []
    for d in range(-허용일, 허용일 + 1):
        x = 기 + datetime.timedelta(days=d)
        낸 += ["%s %d, %d" % (달이름[x.month - 1], x.day, x.year), "%d %s %d" % (x.day, 달이름[x.month - 1], x.year), x.isoformat()]
    if 기.month in (3, 6, 9, 12) and 기.day >= 28:
        q = 기.month // 3
        낸 += ["%dQ%02d" % (q, 기.year % 100), "Q%d %d" % (q, 기.year), "%s quarter of %d" % (["first", "second", "third", "fourth"][q - 1], 기.year)]
    return 낸


def 기준일6K인가(글, 기준일):
    """6-K 첨부가 기준일 분기를 담았나 — 「(three|six|nine) months ended <기준일>」 · 「as of <기준일>」 · 분기 이름(2Q26 · second quarter of 2026)만.
    날짜가 그냥 나오는 글(주총 · 배당 기준일 안내)은 아니다."""
    낮 = re.sub(r"\s+", " ", (글 or "").lower())
    날말 = [s.lower() for s in _기준일말들(기준일)]
    for s in 날말:
        if re.search(r"\d{4}", s) and re.search(r"(?:months|quarter|period|year)s?\s+ended\s+%s|(?:as of|as at)\s+%s" % (re.escape(s), re.escape(s)), 낮):
            return True
    return any(s in 낮 for s in 날말 if not re.search(r"[a-z]+ \d{1,2}, \d{4}|^\d{1,2} [a-z]+ \d{4}$|^\d{4}-\d{2}-\d{2}$", s))


def _이름뿌리(s):
    s = re.sub(r"(?i)\b(inc|corp(oration)?|co|ltd|limited|plc|n\.?v|s\.?a|ag|holdings?|group|company|the)\b\.?", " ", s or "")
    w = re.findall(r"[a-z0-9]+", s.lower())
    return w[0] if w else ""


def 연매출(cf, ns):
    """연차(길이 330~372일) 매출 → {끝: (값, 단위)}."""
    낸 = {}
    for 태그 in ((설정().get("누계") or {}).get("매출") or {}).get(ns) or []:
        for 단위, x in _사실(cf, ns, 태그):
            s, e = 날(x.get("start")), 날(x.get("end"))
            if s and e and 330 <= (e - s).days <= 372 and x.get("val") and _돈단위(단위):
                낸.setdefault(x["end"], (x["val"], 단위))
    return 낸


def 구조단절(sub, cf, ns):
    """구조 단절 후보 → [{시점 · 근거 · 강도 「강|약」}] — 이름 바뀜(뿌리 낱말이 바뀌고 그 둘레 1년 안에 통화가 바뀌거나 연 매출이 반 넘게 줄면 「강」) ·
    통화 섞임(「강」). 같은 뿌리 이름 바뀜(대소문자 · 법인 꼬리)은 「약」 — 경보로 올리지 않는다."""
    낸 = []
    통 = 통화들(cf, ns)
    바뀜날 = [날(a) for u, (a, b) in 통.items()] if len(통) > 1 else []
    매 = sorted((날(k), v) for k, v in 연매출(cf, ns).items())
    급감 = [e for (e0, (v0, u0)), (e, (v, u)) in zip(매, 매[1:]) if u == u0 and v0 and v / v0 < 0.5]
    지금이름 = _이름뿌리((sub or {}).get("name"))
    for x in (sub or {}).get("formerNames") or []:
        t = 날((x.get("to") or "")[:10])
        if not t:
            continue
        뿌리같음 = _이름뿌리(x.get("name")) == 지금이름
        근처 = any(d and abs((d - t).days) <= 400 for d in 바뀜날 + 급감)
        강 = (not 뿌리같음) and 근처
        낸.append({"시점": t.isoformat(), "근거": "회사 이름 바뀜(옛 이름 %s)%s" % (x.get("name") or "", " · 둘레 1년 안 통화 바뀜 · 매출 급감" if 근처 else ""),
                  "강도": "강" if 강 else "약"})
    if len(통) > 1:
        for u, (a, b) in sorted(통.items(), key=lambda z: z[1][0]):
            낸.append({"시점": a, "근거": "통화 %s 기간 %s ~ %s — companyfacts 한 개념에 통화가 섞였다(단위별로 갈라 읽는다)" % (u, a, b), "강도": "강"})
    return 낸


def 짓기(raw, 기준일, 조회일=None, 평가기준일=None):
    """`_raw` → 미국원천/1 dict. 입력이 없으면 ValueError."""
    sub = _읽기(os.path.join(raw, "submissions.json"))
    cf = _읽기(os.path.join(raw, "companyfacts.json"))
    if not isinstance(sub, dict) or not isinstance(cf, dict):
        raise ValueError("submissions.json · companyfacts.json 이 `%s` 에 없다 — sec_fetch.py --기준일 로 받는다" % raw)
    설 = 설정()
    기 = 날(기준일)
    한 = 기 + datetime.timedelta(days=허용일)
    고름 = 공시고르기(sub, 기준일)
    ns = 개념틀(cf)
    기준 = 고름["기준"]
    목표끝 = 기준["기간끝"] if 기준 else 기준일
    통화 = 주통화(cf, ns, 목표끝)
    accn = 기준["accession"] if 기준 else None
    원 = 원문들(raw)
    경보, 확인불가 = list(고름["경보"]), []

    # 공시 목록(고른 것 + 원문이 있는 것)
    공시 = []
    본accn = set()
    for 역, r in [("기준일분기", 기준), ("직전", 고름["직전"]), ("직전", 고름["연차"])] + [("뒤", r) for r in 고름["뒤"][:2]]:
        if not r or r["accession"] in 본accn:
            continue
        본accn.add(r["accession"])
        짝 = 원문짝(원, r)
        공시.append({"양식": r["양식"], "기간끝": r["기간끝"], "제출일": r["제출일"], "accession": r["accession"],
                   "파일": os.path.basename(짝["파일"]) if 짝 else None, "기준일과": 역})
        if not 짝:
            확인불가.append({"항목": "%s 원문(%s · 기간 끝 %s)" % (r["양식"], 역, r["기간끝"]),
                         "원인": "`_raw` 에 %s 가 없다 — sec_fetch.py --기준일 %s 로 받는다" % (파일이름(r["양식"], r["기간끝"]), 기준일)})
    if 기준 and not 원문짝(원, 기준) and "기준일 분기" not in " ".join(경보):
        경보.append("기준일 분기 보고(%s · 기간 끝 %s) 원문이 `_raw` 에 없다 — 본문 · 문장 재료가 빈다" % (기준["양식"], 기준["기간끝"]))
    # 해외 발행사 6-K — 원문에서 기준일 분기를 가린다
    육 = [x for x in 원 if x["양식"] == "6-K"]
    육기준 = [x for x in 육 if 기준일6K인가(글로(_원문읽기(x["파일"]))[:200000], 기준일)]
    for x in 육기준:
        공시.append({"양식": "6-K", "기간끝": 기준일, "제출일": None, "accession": None, "파일": os.path.relpath(x["파일"], raw).replace("\\", "/"),
                   "기준일과": "기준일분기"})
    if 고름["해외6K후보"] and not 육기준:
        경보.append("해외 발행사 — 기준일 분기 실적이 6-K 로 오는데 `_raw` 에 기준일 분기를 담은 6-K 원문이 없다(sec_fetch.py --기준일 이 받는다)")

    # 본문 조각
    본문 = {"Item1": "", "Item2": "", "MDA_capex": "", "찾음": {"Item1": False, "Item2": False, "MDA": False, "10Q": False}, "대체": []}
    연차원문 = 원문짝(원, 고름["연차"])
    if 연차원문:
        글 = 글로(_원문읽기(연차원문["파일"]))
        양 = 고름["연차"]["양식"]
        for k in ("Item1", "Item2"):
            조각, ok, 대 = 절찾기들(글, 양, k)
            본문[k], 본문["찾음"][k] = 조각, ok
            if 대:
                본문["대체"].append(k)
        연MDA, ok, 대 = 절찾기들(글, 양, "MDA")
        본문["찾음"]["MDA"] = ok
        if 대:
            본문["대체"].append("MDA")
    else:
        글, 연MDA = "", ""
        확인불가.append({"항목": "연차 보고 본문(Item 1 · 2 · 7)", "원인": "연차 보고(10-K · 20-F) 원문이 `_raw` 에 없다"})
    분원문 = 원문짝(원, 기준) if (기준 and 기준["양식"] == "10-Q") else None
    분MDA = ""
    if 분원문:
        분글 = 글로(_원문읽기(분원문["파일"]))
        분MDA, ok, 대 = 절찾기들(분글, "10-Q", "MDA")
        본문["찾음"]["10Q"] = ok
        if 대:
            본문["대체"].append("10Q")
    else:
        분글 = ""
    capex글 = [s for s in 문장들(분MDA or 연MDA) if _capex말.search(s)]
    본문["MDA_capex"] = " ".join(capex글)[:20000]
    if 연차원문 and not 본문["찾음"]["Item1"]:
        경보.append("연차 보고에서 Item 1(사업) 머리를 못 찾았다 — 유형 판정 낱말이 빈다(머리 꼴을 본다)")

    # 약정 — 태그 먼저, 표 · 문장으로 더한다(같은 금액은 한 번 · 같은 이름은 늦은 기준일 하나)
    약정 = 약정_태그(cf, ns, 설, 한, 통화, accn, 목표끝)
    for 출, 글_, 기본 in ((분원문, 분글, 기준["기간끝"] if 기준 else None), (연차원문, 글, 고름["연차"]["기간끝"] if 고름["연차"] else None)):
        if not 출 or not 글_:
            continue
        이름 = os.path.basename(출["파일"])
        더 = 약정표(_원문읽기(출["파일"]), "%s 약정 표" % 이름, 기본) + 약정문장(글_, "%s 본문" % 이름, 기본)
        for a in 더:
            if 날(a["기준일"]) and 날(a["기준일"]) > 한:
                continue
            if _겹침(a, 약정):
                continue
            옛 = next((b for b in 약정 if b["원천"] != "태그" and b["이름"] == a["이름"]), None)
            if 옛:
                if (a["기준일"] or "") > (옛["기준일"] or ""):
                    약정[약정.index(옛)] = a
                continue
            약정.append(a)
    if not 약정:
        확인불가.append({"항목": "약정", "원인": "구매의무 · 약정 태그도 「commitments」 문장도 없다(공시 없음일 수 있다 — 본선이 주석을 본다)"})

    # capex 가이던스 — 기준일분기 · 연차 · 뒤 · 6-K · 8-K
    가이드 = []
    for x in 원:
        행 = next((r for r in [기준, 고름["직전"], 고름["연차"]] + 고름["뒤"] if r and x["양식"] == r["양식"] and x["기간키"] == (r["기간끝"] or "")[:7].replace("-", "")), None)
        if x["양식"] in ("6-K", "8-K"):
            공표 = None
            m = re.match(r"(\d{4})(\d{2})(\d{2})", x["기간키"] or "")
            if m:
                공표 = "%s-%s-%s" % m.groups()
        elif 행:
            공표 = 행["제출일"]
        else:
            continue
        x글 = 글로(_원문읽기(x["파일"]))
        조각 = 절찾기(x글, *_절꼴.get(x["양식"], {}).get("MDA", (r"$^", r"$^")))[0] if x["양식"] in _절꼴 else x글
        # 날짜 둘(2026-10-25) — 보고 고르기는 재무기준일 F, 가이던스 공표의 「기준일뒤」 경계는 평가기준일 T((F, T] 공표는 쓴다 · 없으면 F = T)
        가이드 += capex가이던스(조각 or x글, "%s %s" % (x["양식"], os.path.basename(x["파일"])), 공표, 평가기준일 or 기준일)

    # RPO
    rpo = 시점값(cf, ns, ((설.get("RPO") or {}).get(ns) or []), 한, 통화, accn)
    비 = 시점값(cf, ns, ((설.get("RPO비중") or {}).get(ns) or []), 한, "pure", accn, 끝=rpo["끝"] if rpo else None) if rpo else None
    RPO = ({"값": rpo["값"], "기준일": rpo["끝"], "12개월내비중": (비["값"] if 비 else None), "출처": "companyfacts %s(%s)" % (rpo["태그"], rpo["accn"])}
           if rpo else {"값": None, "기준일": None, "12개월내비중": None, "출처": None})

    # 기준일 누계
    누 = {"기간ID": None, "시작": None, "끝": None, "값": {}, "출처": None}
    if 기준:
        fp = 보고fp(cf, ns, accn) or ("FY" if 기준["양식"] in 연차양식 else None)
        매 = 누계값(cf, ns, ((설.get("누계") or {}).get("매출") or {}).get(ns) or [], 목표끝, 통화, accn, fp)
        if 매:
            누.update({"기간ID": 기간ID(매["시작"], 매["끝"], 매.get("fy")), "시작": 매["시작"], "끝": 매["끝"],
                      "출처": "companyfacts %s(%s · %s)" % (기준["양식"], accn, 매["태그"])})
        for 키, 태그사전 in (설.get("누계") or {}).items():
            태그들 = (태그사전 or {}).get(ns) or []
            if 키 == "미지급설비":
                continue
            v = 누계값(cf, ns, 태그들, 목표끝, 통화, accn, fp)
            if v and 매 and v["시작"] != 매["시작"]:
                v = None                                       # 매출과 다른 기간(분기만 낸 개념 등) — 섞지 않는다
            누["값"][키] = v["값"] if v else None
        미 = (설.get("누계") or {}).get("미지급설비") or {}
        지금 = 시점값(cf, ns, 미.get(ns) or [], 한, 통화, accn, 끝=목표끝)
        누["값"]["미지급설비"] = 지금["값"] if 지금 else None
        누["값"]["미지급설비증감"] = None
        if 지금 and 매:
            전 = 시점값(cf, ns, 미.get(ns) or [], 날(매["시작"]) - datetime.timedelta(days=1), 통화)
            if 전 and abs((날(전["끝"]) - 날(매["시작"])).days) <= 10:
                누["값"]["미지급설비증감"] = 지금["값"] - 전["값"]
        if not 매:
            확인불가.append({"항목": "기준일 누계(매출)", "원인": "companyfacts 에 기간 끝 %s 의 누계 매출 사실이 없다(6-K 회사는 XBRL 이 없다)" % 목표끝})
        if 누["값"].get("유형상각") is None and 누["값"].get("DandA") is not None:
            경보.append("유형 상각 태그가 없고 D&A 합산만 있다 — CAPEX ÷ 상각은 하한값(F28 · F44)")

    # 유형자산 자산군 — 태그 자산군이 비거나 합계와 2% 넘게 어긋나면 연차 보고 주석 표를 읽어 더 맞는 쪽을 쓴다(F24 · F37)
    유 = 유형자산표_태그(cf, ns, 설, 한, 통화, accn, 목표끝)
    태그나쁨 = (not 유) or (not 유["자산군"]) or (유.get("검산차") is not None and abs(유["검산차"]) > 0.02)
    if 태그나쁨 and 연차원문:
        t = 유형자산표_원문(_원문읽기(연차원문["파일"]), 고름["연차"]["기간끝"])
        if t and (not 유 or not 유["자산군"] or t["검산차"] is None or abs(t["검산차"]) < abs(유["검산차"] or 0)):
            유 = {"기준일": 고름["연차"]["기간끝"], "자산군": t["자산군"], "합계": t["합계"], "검산차": t["검산차"], "단위": 통화,
                 "출처": "%s 유형자산 주석 표(열 연도 %s · ×%g)" % (os.path.basename(연차원문["파일"]), "/".join(t["열연도"]), t["단위배"])}
    if 유 and 유.get("검산차") is not None and abs(유["검산차"]) > 0.02:
        경보.append("유형자산 자산군 합이 합계와 %.1f%% 어긋난다 — 자산군 누락 · 열 밀림을 본다(F24 · F37)" % (유["검산차"] * 100))
    if not 유:
        유 = {"기준일": None, "자산군": {}, "합계": None, "검산차": None, "단위": 통화, "출처": None}
        확인불가.append({"항목": "유형자산 자산군", "원인": "자산군 태그도 연차 보고 주석 표도 못 읽었다"})

    # 능력 문장 · 인원
    능 = []
    for 조각, 출 in ((본문["Item1"], "Item1"), (본문["Item2"], "Item2"), (연MDA, "MDA"), (분MDA, "10-Q MDA")):
        능 += [x for x in 능력문장(조각, 출) + 단위투자문장(조각, 출)
              if not any(x["값"] == y["값"] and x["단위"].lower() == y["단위"].lower() for y in 능)]
    사람 = 인원(raw, 연차원문, cf, 한) or {"값": None, "기준일": None, "출처": None, "원천": None}

    # 통화 · 구조 단절
    통 = 통화들(cf, ns)
    if len(통) > 1:
        경보.append("companyfacts 한 개념에 통화가 섞였다(%s) — 값은 %s 로만 읽었다(F61)" % (" · ".join(sorted(통)), 통화))
    단절 = 구조단절(sub, cf, ns)
    for x in 단절:
        if "이름 바뀜" in x["근거"] and x["강도"] == "강":
            경보.append("구조 단절 후보 %s — %s · 그 앞 CAPEX 시계열은 다른 사업일 수 있다(F61)" % (x["시점"], x["근거"]))

    return {"형식": 형식, "회사": (sub or {}).get("name") or (cf or {}).get("entityName"), "CIK": "%s" % ((sub or {}).get("cik") or (cf or {}).get("cik") or ""),
            "평가기준일": 평가기준일 or 기준일, "재무기준일": 기준일, "조회일": 조회일 or datetime.date.today().isoformat(),
            "공시": 공시, "본문": 본문, "약정": 약정, "capex가이던스": 가이드, "RPO": RPO, "누계": 누, "유형자산표": 유,
            "능력문장": 능, "인원": 사람, "개념틀": ns, "통화": 통화, "구조단절후보": 단절, "경보": 경보, "확인불가": 확인불가}


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="미국 원천 읽기 — `_raw` → 미국원천.json (네트워크 0)")
    ap.add_argument("--기준일", "--재무기준일", dest="기준일", default=None,
                    help="재무기준일 F YYYY-MM-DD — 기준일 분기 · 직전 · 연차 · 뒤 보고를 이 날로 가른다(옛 이름 --기준일 은 지금 뜻 그대로)")
    ap.add_argument("--평가기준일", default=None,
                    help="평가기준일 T YYYY-MM-DD — capex 가이던스 공표의 「기준일뒤」 경계((F, T] 공표는 쓴다) · 산출 머리. 없으면 F = T")
    ap.add_argument("--가정", default=None, help="가정 파일 — 날짜 인자를 비우면 기준일.py 로 F · T 를 푼다(F 가 없으면 F = T)")
    ap.add_argument("--raw", default="_raw")
    ap.add_argument("-o", "--출력")
    ap.add_argument("--조회일")
    a = ap.parse_args(argv)
    import 기준일인자 as _기인                                  # noqa: PLC0415 — 날짜 둘(2026-10-25)
    a.기준일 = _기인.풀기(a.기준일, a.가정, _기인.재무, 인자="--기준일")
    a.평가기준일 = _기인.풀기(a.평가기준일, a.가정, _기인.평가, 인자="--평가기준일")
    if not a.기준일:
        ap.error("--기준일(재무기준일) 또는 --가정 이 있어야 합니다")
    if a.평가기준일 and not 날(a.평가기준일):
        print("입력 오류 — --평가기준일 은 YYYY-MM-DD")
        return 입력오류
    if not 날(a.기준일):
        print("입력 오류 — --기준일 은 YYYY-MM-DD")
        return 입력오류
    try:
        낸 = 짓기(a.raw, a.기준일, a.조회일, 평가기준일=a.평가기준일)
    except ValueError as e:
        print("입력 오류 — %s" % e)
        return 입력오류
    p = a.출력 or os.path.join(a.raw, "미국원천.json")
    os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    with io.open(p, "w", encoding="utf-8") as f:
        json.dump(낸, f, ensure_ascii=False, indent=1)
    기 = next((x for x in 낸["공시"] if x["기준일과"] == "기준일분기"), None)
    print("미국원천 %s — 기준일분기 %s · 약정 %d · capex 가이던스 %d(기준일 뒤 %d) · RPO %s · 누계 %s · 자산군 %d · 능력 문장 %d · 인원 %s · 경보 %d · 확인불가 %d → %s" % (
        낸["회사"], ("%s %s" % (기["양식"], 기["기간끝"])) if 기 else "없음", len(낸["약정"]), len(낸["capex가이던스"]),
        sum(1 for x in 낸["capex가이던스"] if x["기준일뒤"]), "있음" if 낸["RPO"]["값"] else "없음", 낸["누계"]["기간ID"] or "없음",
        len(낸["유형자산표"]["자산군"]), len(낸["능력문장"]), 낸["인원"]["값"], len(낸["경보"]), len(낸["확인불가"]), p))
    for x in 낸["경보"]:
        print("  경보 — %s" % x)
    return 통과 if 기 and not any("기준일 분기" in x for x in 낸["경보"]) else 발견


if __name__ == "__main__":
    sys.exit(main())

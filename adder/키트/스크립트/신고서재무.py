# -*- coding: utf-8 -*-
"""신고서재무 — 증권신고서 · 투자설명서(미국 S-1 · F-1 · 424B · 10-12B / 국내 증권신고서 · 투자설명서 · 분할회사 공시)의 감사받은
연간 재무를 키트가 읽는 한 꼴 「신고서재무/1」(`_raw/신고서재무.json`)로 옮긴다 (2026-10-25 Y1 · 설계 `연구/재무이력없음_20261025/02_설계.md` 2-1 ·
계약 `03_Y1계약.md`).

왜 만들었나
  정기보고서(10-K · 20-F · 사업보고서)에 연간 재무가 3해 미만인 회사도 신고서에는 감사받은 3개년 손익 · 현금흐름, 2개년 재무상태표,
  부문 주석이 있다. 키트 원천 도구는 정기보고서만 받았다 — 이력이 없는 것이 아니라 서류를 안 받은 것이었다.
  미국 신고서 재무는 XBRL 로 태깅되지 않는 일이 많아(companyfacts 연간 사실 0건 실측) HTML 표를 읽는다.

무엇을 읽나(네트워크 0 — 받는 일은 `sec_fetch.py --신고서` · 국내는 `dart_fetch.py` 의 발행공시 스위치)
  미국  `_raw/신고서_<양식>_<접수번호>.txt`(htm2txt 산출 — 없으면 .htm 을 글로 바꾼다) · `sec_공시고르기.json` 의 「신고서」 · `submissions.json`
        ① 재무제표 절(INDEX TO … FINANCIAL STATEMENTS)과 감사인 보고서 문단의 기간 → 감사구분(덮는 기간만 「감사」)
        ② 연간 재무상태표 · 손익계산서 · 현금흐름표, 중간 재무(「미감사 중간」)
        ③ 부문 주석(Segment)과 매출 분해 표(Revenue 주석)
        ④ 보고실체변화 문장 — 공통지배 소급 결합(common control · retrospective) · 주식분할 소급(retroactively) · 분할(spin-off · carve-out)
        ⑤ 검산 셋 — 자산총계 = 부채총계(+ 중간자본) + 자본총계 · 매출 − 비용 = 영업이익 · 부문 매출 합 = 매출
  국내  `--시장 KR` — 국내 갈래의 `신고서재무_국내.읽기(raw, 기준일)` 를 부른다(공통 함수는 이 파일의 것을 import 해 쓴다)

표 꼴 둘을 다 읽는다
  칸 줄    HTML 표가 한 줄에 「이름 | 값 | 값」 으로 온 꼴(정기보고서 대부분)
  세로 줄  위치 지정 레이아웃(PDF 에서 옮긴 신고서) — 점선이 붙은 머리 줄 뒤에 기간 수만큼 숫자 줄이 하나씩 온다
           (칸 앞에 「 | 」 가 붙어 한 칸씩 내려온 꼴도 같다)
  괄호 = 음수(닫는 괄호가 따로 떨어져 나간 「(2,589」 도 음수) · `$` · 쉼표 · 각주 표시 「(a)」 「(1)」 「*」 · 대시 = 0 ·
  머리 「(in millions …)」 · 「(단위 : 백만원)」 을 읽어 백만 단위로 맞춘다(주당 값은 그대로).

규칙 — 값은 원문 표에서만(웹 · 언론 숫자 금지) · 표준 줄은 원문 줄 이름의 낱말로 짝짓고 짝지은 원문 줄 이름을 근거에 남긴다
  (회사마다 이름이 다르다 — 가정하지 않는다) · 못 짝지은 표준 줄은 비우고 `확인불가` 에 · 검산이 어긋나면 값을 고치지 않고
  「어긋남」 과 차를 적는다 · 부호는 원문 표시 그대로(비용 · 투자 유출이 괄호로 표시됐으면 음수) · 회사 이름을 규칙에 박지 않는다.

    python 스크립트/신고서재무.py --raw _raw --기준일 2026-06-30 [--시장 US|KR] [--원문 파일] [-o _raw/신고서재무.json]

종료 코드 — 0 통과 · 1 발견(검산 어긋남 · 매출 못 읽음 · 표준 줄 항목 부재) · 2 입력오류(신고서 원문 없음 · 국내 모듈 없음).
"""
from __future__ import annotations

import argparse
import calendar
import datetime
import glob
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류  # noqa: E402

형식 = "신고서재무/1"
표준줄이름 = ("매출", "매출원가", "연구개발비", "판매비와관리비", "영업이익", "이자비용", "법인세차감전이익", "법인세비용", "당기순이익",
         "감가상각비", "영업활동현금흐름", "유형자산취득", "자산총계", "부채총계", "자본총계", "현금및현금성자산", "차입금")
표준줄구분 = {"매출": ("손익",), "매출원가": ("손익",), "연구개발비": ("손익",), "판매비와관리비": ("손익",), "영업이익": ("손익",),
          "이자비용": ("손익",), "법인세차감전이익": ("손익",), "법인세비용": ("손익",), "당기순이익": ("손익",),
          "감가상각비": ("현금흐름", "손익"), "영업활동현금흐름": ("현금흐름",), "유형자산취득": ("현금흐름",),
          "자산총계": ("재무상태",), "부채총계": ("재무상태",), "자본총계": ("재무상태",), "현금및현금성자산": ("재무상태",), "차입금": ("재무상태",)}
감사구분값 = ("감사", "검토", "미감사 중간", "경영진 배부")
허용차 = 1.0                                         # 검산 — 백만 단위 반올림 1 까지는 통과(차는 그대로 적는다)

# ══════════════════════════════════════════════════════════ 공통 — 기간 id · 날 · 수 · 단위

_달이름 = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
_달 = {m: i + 1 for i, m in enumerate(_달이름)}
_달꼴 = "(?:" + "|".join(_달이름) + ")"


def _날(s):
    if isinstance(s, datetime.date):
        return s
    try:
        return datetime.date.fromisoformat((s or "")[:10])
    except ValueError:
        return None


def 기간id(끝, 개월, 꼬리="", 연말월=12, 연간=False):
    """기간 끝 · 개월 수 → 「FY2025A」(12개월) · 「1Q26A」 · 「2Q26A」(3개월 — 분기 번호는 결산월에서 센다) · 「1H23A」 · 「9M25A」 ·
    그 밖 「10M24A」. 꼬리를 주면 「FY2023A_분할전」. 회계연도 이름은 기간 끝의 해다(결산월이 12월이 아니어도 같다).
    `연간=True` 면 12개월이 아니어도 FY 로 부른다 — 설립 · 분할로 짧은 첫 사업연도(10개월 등)는 사업보고서가 연간 보고서라서다.
    개월 수는 `기간` 칸의 `개월` 에 남아 짧은기임이 지워지지 않는다(국내 · 미국 공통 — 2026-10-25 본선이 두 갈래의 판을 하나로)."""
    e = _날(끝)
    if e is None or not 개월:
        return None
    개월 = int(개월)
    머 = {3: "1Q", 6: "1H", 9: "9M", 12: "FY"}.get(개월)
    if 머 == "FY" or 연간:
        s = "FY%dA" % e.year
    elif 개월 == 3:
        s = "%dQ%02dA" % (((e.month - int(연말월 or 12) - 1) % 12) // 3 + 1, e.year % 100)
    elif 머:
        s = "%s%02dA" % (머, e.year % 100)
    else:
        s = "%dM%02dA" % (개월, e.year % 100)
    return s + ("_" + 꼬리 if 꼬리 else "")


def 기간시작(끝, 개월):
    """기간 끝 · 개월 → 시작일(달 말 결산이면 그 달 첫날로 맞춘다)."""
    e = _날(끝)
    if e is None or not 개월:
        return None
    y, m = e.year, e.month - int(개월)
    while m <= 0:
        m += 12
        y -= 1
    말 = calendar.monthrange(y, m)[1]
    if e.day == calendar.monthrange(e.year, e.month)[1]:
        d = datetime.date(y, m, 말)
    else:
        d = datetime.date(y, m, min(e.day, 말))
    return (d + datetime.timedelta(days=1)).isoformat()


_수꼴 = re.compile(r"^(?P<l>\()?\s*(?P<m>-)?\s*\$?\s*(?P<l2>\()?\s*\$?\s*(?P<n>\d{1,3}(?:,\d{3})+|\d+)(?P<d>\.\d+)?\s*(?P<r>\))?\s*(?P<p>%)?"
                 r"\s*(?P<f>\((?:[a-z]|\d)\)|\*+|†+)?$")


def 수읽기(칸):
    """표 칸 하나 → 수 | None. 괄호 = 음수(닫는 괄호가 떨어져 나간 「(2,589」 도) · `$` · 쉼표 · 각주 표시 「(a)」 「(1)」 「*」 · 대시(— – -) = 0."""
    c = (칸 or "").strip().replace("−", "-").replace("–", "-").replace("—", "-").replace("\xa0", " ")
    if not c:
        return None
    if re.fullmatch(r"\$?\s*-+\s*\$?", c):
        return 0.0
    m = _수꼴.match(c)
    if not m:
        return None
    v = float(m.group("n").replace(",", "") + (m.group("d") or ""))
    return -v if (m.group("l") or m.group("l2") or m.group("m")) else v


def 퍼센트칸(칸):
    return bool(re.search(r"%\s*\)?\s*$", (칸 or "").strip()))


_단위영 = re.compile(r"(?i)\bin\s+(thousands|millions|billions)\b")
_단위한 = re.compile(r"단위\s*[:：]?\s*(백만\s*원|천\s*원|억\s*원|원|백만\s*달러|천\s*달러|달러|USD\s*millions?|USD\s*thousands?)")
_단위배 = {"thousands": 0.001, "millions": 1.0, "billions": 1000.0,
         "백만원": 1.0, "천원": 0.001, "억원": 100.0, "원": 1e-6, "백만달러": 1.0, "천달러": 0.001, "달러": 1e-6,
         "USDmillion": 1.0, "USDmillions": 1.0, "USDthousand": 0.001, "USDthousands": 0.001}


def 단위읽기(글):
    """머리 「(in millions, except per share data)」 · 「(단위 : 백만원)」 → 백만 단위로 맞추는 배수(값 × 배 = 백만) | None."""
    m = _단위영.search(글 or "")
    if m:
        return _단위배[m.group(1).lower()]
    m = _단위한.search(글 or "")
    if m:
        return _단위배.get(re.sub(r"\s+", "", m.group(1)))
    return None


def 정수로(v):
    if v is None:
        return None
    v = round(float(v), 6)
    return int(v) if v.is_integer() else v


# ══════════════════════════════════════════════════════════ 공통 — 표준 줄 짝짓기

_이익 = r"(?:income|loss|earnings|profit|income \(loss\)|\(loss\) income|loss \(income\)|earnings \(loss\)|\(loss\) earnings|profit \(loss\))"
표준규칙 = {
    "매출": [r"^total (?:net )?revenues?$", r"^total net sales$", r"^(?:net )?revenues?(?:, net)?$", r"^net sales$", r"^sales$",
           r"^total revenues? and other income$",
           r"^매출액$", r"^수익\s*\(매출액\)$", r"^영업수익$", r"^매출$"],
    "매출원가": [r"^total cost of (?:revenues?|sales)$", r"^cost of (?:revenues?|sales|goods sold|net revenues?)\b", r"^매출원가$"],
    "연구개발비": [r"^research and development\b", r"^research, development\b", r"^경상연구개발비$", r"^연구개발비$"],
    "판매비와관리비": [r"^selling, general,? (?:and|&) administrative\b", r"^sales, general,? (?:and|&) administrative\b",
                r"^general (?:and|&) administrative\b", r"^판매비\s*(?:와|및)\s*관리비$"],
    "영업이익": [r"^operating " + _이익 + r"$", r"^" + _이익 + r" from operations$", r"^영업\s*이익(?:\s*\(손실\))?$", r"^영업\s*손실$", r"^영업손익$"],
    "이자비용": [r"^interest expense\b", r"^이자비용$"],
    "법인세차감전이익": [r"^" + _이익 + r" before (?:provision for |benefit from |\(benefit from\) |\(provision for\) |provision for \(benefit from\) |"
                   r"benefit from \(provision for\) )?income tax", r"before income tax", r"^법인세\s*비용\s*차감\s*전", r"^법인세차감전"],
    "법인세비용": [r"^(?:provision for|benefit from|\(benefit from\)|\(provision for\)|provision for \(benefit from\)|benefit from \(provision for\)|"
              r"\(benefit from\) provision for) income tax", r"^income tax (?:expense|provision|benefit|\(benefit\)|expense \(benefit\)|\(expense\) benefit)",
              r"^income taxes?$", r"^법인세\s*비용(?:\s*\(수익\))?$", r"^법인세\s*수익$"],
    "당기순이익": [r"^net " + _이익 + r"$", r"^당기\s*순\s*이익(?:\s*\(손실\))?$", r"^당기\s*순\s*손익$", r"^당기\s*순\s*손실$"],
    "감가상각비": [r"^depreciation(?:,)? (?:and|&) amortization\b", r"^depreciation, amortization\b", r"^depreciation\b", r"^감가상각비$"],
    "영업활동현금흐름": [r"^net cash (?:provided by|used in|provided by \(used in\)|\(used in\) provided by|from|generated from|generated by|"
                   r"used for|\(used in\) from)(?: \(used in\))? operating activities",
                   r"^영업활동\s*(?:으로\s*인한|으로\s*부터의|에서\s*창출된)?\s*(?:순)?현금\s*흐름", r"^영업활동\s*현금\s*흐름"],
    "유형자산취득": [r"^(?:purchases?|acquisitions?|additions?|payments for|expenditures for) (?:of |to |for )?property(?:,)? (?:plant(?:,)? )?(?:and |& )?equipment",
                 r"^capital expenditures\b", r"^purchases? of property and equipment", r"^유형자산\s*의?\s*취득$"],
    "자산총계": [r"^total assets$", r"^자산\s*총계$"],
    "부채총계": [r"^total liabilities$", r"^부채\s*총계$"],
    "자본총계": [r"^total equity(?: \(deficit\))?$", r"^total (?:shareholders'?|stockholders'?|members'?) (?:equity|deficit|equity \(deficit\)|\(deficit\) equity)$",
              r"^자본\s*총계$"],
    "현금및현금성자산": [r"^cash and cash equivalents$", r"^cash and equivalents$", r"^cash$", r"^현금\s*및\s*현금성\s*자산$"],
}
_차입금줄 = re.compile(r"(?i)^(?:short-term |long-term |current portion of (?:long-term )?|current maturities of (?:long-term )?)?"
                    r"(?:debt|borrowings?|notes payable|loans? payable|term loans?|convertible (?:senior )?notes|senior notes)\b|"
                    r"^debt and finance leases?\b|^단기\s*차입금$|^장기\s*차입금$|^유동성\s*장기\s*차입금$|^사채$|^유동성\s*사채$")
_차입금아님 = re.compile(r"(?i)issuance|securities|receivable|investment|discount|interest|extinguishment|^total")
_차입금합계 = re.compile(r"(?i)^total (?:debt|borrowings)$|^차입금\s*합계$")


def 줄다듬(이름):
    """원문 줄 이름 → 짝짓기용(점선 · 각주 표시 「(a)」 · 「(related party …)」 같은 괄호 설명을 떼고 소문자)."""
    s = (이름 or "").replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("\xa0", " ")
    s = re.sub(r"(?:\s*\.){3,}\s*", " ", s)
    s = re.sub(r"\((?:[a-z]|\d{1,2})\)", " ", s)
    s = re.sub(r"(?i)\((?:related part|including|net of|of which|see note|note \d)[^)]*\)", " ", s)
    s = re.sub(r"\s+", " ", s).strip(" :;,")
    return s.lower()


def 표준짝(행들, 표준, 규칙=None):
    """행들 [{"줄", "값": {id: v}, …}] → 표준 줄 하나의 (원문 줄 이름, {id: v}, 행) | None. 규칙 목록 순서가 우선순위(합계 줄 먼저)."""
    for 꼴 in (규칙 or 표준규칙).get(표준, []):
        r = re.compile(꼴, re.I)
        for 행 in 행들:
            if 행.get("값") and r.search(줄다듬(행["줄"])):
                return 행["줄"], dict(행["값"]), 행
    return None


def 차입금짝(행들):
    """재무상태표 행들 → (원문 줄 이름들, {id: 합}) | None. 「Total debt」 가 있으면 그 줄, 없으면 유동 · 비유동 차입 줄을 더한다."""
    for 행 in 행들:
        if 행.get("값") and _차입금합계.search(줄다듬(행["줄"])):
            return [행["줄"]], dict(행["값"])
    짝 = [행 for 행 in 행들 if 행.get("값") and _차입금줄.search(줄다듬(행["줄"])) and not _차입금아님.search(줄다듬(행["줄"]))]
    if not 짝:
        return None
    합 = {}
    for 행 in 짝:
        for k, v in 행["값"].items():
            합[k] = 정수로((합.get(k) or 0) + v)
    return [행["줄"] for 행 in 짝], 합


# ══════════════════════════════════════════════════════════ 공통 — 뼈대 · 검산 · 저장

def 뼈대(시장="US"):
    return {"형식": 형식, "시장": 시장, "회사": None, "식별": {}, "평가기준일": None, "조회일": datetime.date.today().isoformat(),
            "단위": "백만달러" if 시장 == "US" else "백만원", "통화": "USD" if 시장 == "US" else "KRW", "원단위배": 1000000,
            "서류": [], "기간": [], "표준줄": {k: {} for k in 표준줄이름}, "원표": {"손익": [], "현금흐름": [], "재무상태": [], "부문": []},
            "근거": {}, "보고실체변화": [], "검산": [], "확인불가": [], "경보": []}


def _판정(차, 허용=허용차):
    return "통과" if 차 is not None and abs(차) <= 허용 else "어긋남"


def 검산셋(표준, 덧=None):
    """표준줄 · 덧(선택) → 검산 목록. 덧 = {"중간자본": {id: v}, "영업비용": {id: (v, 설명)}, "부문매출": {id: (합, 내역)}}.
    ① 자산총계 = 부채총계 + (중간자본) + 자본총계 ② 매출 − 비용 = 영업이익(비용이 없으면 이 줄을 내지 않는다) ③ 부문 매출 합 = 매출."""
    덧 = 덧 or {}
    낸 = []
    A, L, E = 표준.get("자산총계") or {}, 표준.get("부채총계") or {}, 표준.get("자본총계") or {}
    중 = 덧.get("중간자본") or {}
    for k in sorted(A, key=_기간정렬):
        if k not in L or k not in E:
            continue
        m = 중.get(k)
        차 = 정수로(A[k] - L[k] - E[k] - (m or 0))
        항 = {"항목": "자산총계 = 부채총계 + 자본총계" if m is None else "자산총계 = 부채총계 + 중간자본 + 자본총계", "기간": k, "차": 차, "판정": _판정(차)}
        if m is not None:
            항["중간자본"] = 정수로(m)
            항["비고"] = "부채와 자본 사이에 따로 선 줄(상환 가능 우선주 등) — 부채총계 · 자본총계 어디에도 들지 않는다"
        낸.append(항)
    S, O = 표준.get("매출") or {}, 표준.get("영업이익") or {}
    for k, (비용, 설명) in sorted((덧.get("영업비용") or {}).items(), key=lambda t: _기간정렬(t[0])):
        if k in S and k in O:
            차 = 정수로(S[k] - 비용 - O[k])
            낸.append({"항목": "매출 − 비용 = 영업이익", "기간": k, "차": 차, "판정": _판정(차), "비고": 설명})
    for k, (합, 내역) in sorted((덧.get("부문매출") or {}).items(), key=lambda t: _기간정렬(t[0])):
        if k in S:
            차 = 정수로(합 - S[k])
            낸.append({"항목": "부문 매출 합 = 매출", "기간": k, "차": 차, "판정": _판정(차), "비고": 내역})
    return 낸


def _기간정렬(k):
    """「FY2025A」 · 「1Q26A」 → 정렬 열쇠(최신 먼저가 아니라 시간순)."""
    m = re.match(r"^FY(\d{4})A", k or "")
    if m:
        return (int(m.group(1)), 12, k)
    m = re.match(r"^(\d)([QH])(\d\d)A|^(\d+)M(\d\d)A", k or "")
    if m:
        if m.group(1):
            달 = int(m.group(1)) * (3 if m.group(2) == "Q" else 6)
            return (2000 + int(m.group(3)), 달, k)
        return (2000 + int(m.group(5)), int(m.group(4)), k)
    return (0, 0, k or "")


def 저장(결과, raw, 경로=None):
    """`경로` 가 없으면 `<raw>/신고서재무.json`. 쓰는 중 파일에 쓴 뒤 바꿔 넣는다(읽는 쪽이 반쯤 쓴 파일을 보지 않게)."""
    p = 경로 or os.path.join(raw, "신고서재무.json")
    os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    임 = p + ".쓰는중"
    with io.open(임, "w", encoding="utf-8") as f:
        json.dump(결과, f, ensure_ascii=False, indent=1)
    os.replace(임, p)
    return p


def _읽기(p, 기본=None):
    try:
        with io.open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return 기본


# ══════════════════════════════════════════════════════════ 미국 — 표 읽기(두 꼴)

_쪽꼴 = re.compile(r"^(?:F-\d{1,3}|Table of Contents|TABLE OF CONTENTS)$")
_쪽번호꼴 = re.compile(r"^F-(\d{1,3})$")
_해꼴 = re.compile(r"^(?:19|20)\d\d$")
_날꼴 = re.compile(r"(?i)^(%s)\s+(\d{1,2}),\s*((?:19|20)\d\d),?$" % _달꼴)
_월일꼴 = re.compile(r"(?i)^(?:as of\s+|at\s+)?(%s)\s+(\d{1,2}),?$" % _달꼴)
_기간말꼴 = re.compile(r"(?i)^(?:for\s+the\s+)?(?:fiscal\s+)?(years?|three\s+months|six\s+months|nine\s+months|twelve\s+months|quarters?|"
                    r"thirteen\s+weeks|twenty-six\s+weeks|thirty-nine\s+weeks|fifty-two\s+weeks|fifty-three\s+weeks|(?:13|26|39|52|53)\s+weeks)"
                    r"\s+ended\s*(.*)$")
_기간달 = {"year": 12, "years": 12, "three months": 3, "six months": 6, "nine months": 9, "twelve months": 12, "quarter": 3, "quarters": 3,
         "thirteen weeks": 3, "twenty-six weeks": 6, "thirty-nine weeks": 9, "fifty-two weeks": 12, "fifty-three weeks": 12,
         "13 weeks": 3, "26 weeks": 6, "39 weeks": 9, "52 weeks": 12, "53 weeks": 12}
_노트머리꼴 = re.compile(r"(?i)^(?:note\s+(\d{1,2})\s*[-–—.:]?\s*(.{2,90})|(\d{1,2})\s*[.:)]\s+([A-Z][^.]{2,80}))$")
_멈춤꼴 = re.compile(r"(?i)^the accompanying notes|^see accompanying notes|^_{3,}")


def _칸들(줄):
    cs = [c.strip() for c in (줄 or "").replace("\xa0", " ").split("|")]
    return [c for c in cs if c and c not in ("$", ")", "(", "%", "$)", "($", ")%")]


def _점선떼기(t):
    m = re.search(r"(?:\s*\.){3,}\s*$|…+\s*$", t or "")
    return (t[:m.start()].rstrip(), True) if m else ((t or "").strip(), False)


_이음말 = re.compile(r"(?i)(?:,|;|\b(?:of|and|or|to|for|in|the|by|from|on|at|with|including|excluding|between|under|per)|[-&])$")


def _이어짐(앞, 뒤):
    """앞 줄 이름이 뒤 줄로 이어지나 — 괄호가 안 닫혔거나 · 이음말로 끝나거나 · 뒤가 소문자 · 숫자 · $ · ( 로 시작하면."""
    앞 = (앞 or "").strip()
    if not 앞:
        return False
    if 앞.count("(") > 앞.count(")"):
        return True
    if _이음말.search(앞):
        return True
    return bool(re.match(r"^[a-z0-9$(]", 뒤 or ""))


def 노트머리(글):
    m = _노트머리꼴.match((글 or "").strip())
    if not m:
        return None
    번호, 제목 = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
    제목 = 제목.strip()
    if 제목.endswith(".") or len(제목) > 90:
        return None
    return int(번호), 제목


def 기간말(글):
    """「Year Ended December 31,」 · 「Three Months Ended March 31,」 → {"개월", "월일", "날짜"} | None."""
    m = _기간말꼴.match((글 or "").strip())
    if not m:
        return None
    개월 = _기간달.get(re.sub(r"\s+", " ", m.group(1).lower()))
    나머지 = m.group(2).strip()
    낸 = {"개월": 개월, "월일": None, "날짜": None}
    d = _날꼴.match(나머지)
    if d:
        낸["날짜"] = datetime.date(int(d.group(3)), _달[d.group(1).lower()], int(d.group(2)))
        낸["월일"] = (낸["날짜"].month, 낸["날짜"].day)
    else:
        md = _월일꼴.match(나머지)
        if md:
            낸["월일"] = (_달[md.group(1).lower()], int(md.group(2)))
    return 낸


def _날짜칸(c):
    d = _날꼴.match((c or "").strip())
    return datetime.date(int(d.group(3)), _달[d.group(1).lower()], int(d.group(2))) if d else None


def _머리훑기(줄들, k, 같은줄칸=()):
    """쪽 넘김 머리 — k 부터 해 · 날짜 줄을 모은다 → (다음 줄번호, 해들, 날들)."""
    해 = [int(c) for c in 같은줄칸 if _해꼴.match(c)]
    날 = [d for d in (_날짜칸(c) for c in 같은줄칸) if d]
    while k < len(줄들):
        cs = _칸들(줄들[k])
        if not cs:
            k += 1
            continue
        if all(_해꼴.match(c) for c in cs):
            해 += [int(c) for c in cs]
        elif all(_날짜칸(c) for c in cs):
            날 += [_날짜칸(c) for c in cs]
        elif len(cs) == 1 and _월일꼴.match(cs[0]):
            pass
        else:
            break
        k += 1
    return k, 해, 날


def 표읽기(줄들, i, 배=None, 최대=1500):
    """줄들[i:] 에서 표 하나를 읽는다(두 꼴). → {"시작", "끝", "배", "미감사", "개월", "월일", "해들", "날들", "이름후보", "행": [{"줄", "값": [수…], "머리", "줄번호", "퍼센트"}]}.
    멈춤 — 「The accompanying notes」 · 밑줄 각주 · 주석 머리 · 열이 다른 새 기간 머리 · 값 없는 줄글 일곱 줄."""
    표 = {"시작": i, "끝": i, "배": 배, "미감사": False, "개월": None, "월일": None, "해들": [], "날들": [], "이름후보": [], "행": []}
    st = {"라벨": [], "끝남": False, "값": [], "퍼센트": False, "머리": None, "줄번호": i}

    def 닫기():
        if st["값"]:
            표["행"].append({"줄": " ".join(st["라벨"]).strip(), "값": list(st["값"]), "머리": st["머리"], "줄번호": st["줄번호"],
                           "퍼센트": st["퍼센트"]})
        elif st["라벨"]:
            st["머리"] = " ".join(st["라벨"]).strip()
        st["라벨"], st["값"], st["끝남"], st["퍼센트"] = [], [], False, False

    def 라벨더하기(t, 끝남, j):
        if st["라벨"] and (st["끝남"] or not _이어짐(st["라벨"][-1], t)):
            닫기()
        if not st["라벨"]:
            st["줄번호"] = j
        st["라벨"].append(t)
        st["끝남"] = 끝남

    본문 = False
    끝 = min(len(줄들), i + 최대)
    j = i
    while j < 끝:
        cs = _칸들(줄들[j])
        if not cs:
            j += 1
            continue
        글 = " ".join(cs)
        if _멈춤꼴.match(글):
            break
        if 본문 and not st["값"] and 노트머리(글):
            break
        if _쪽꼴.match(글):
            j += 1
            continue
        if not 본문:
            if 글.startswith("(") or "단위" in 글:
                u = 단위읽기(글)
                if u is not None and len(글) < 90:
                    표["배"] = u
                    j += 1
                    continue
            if re.fullmatch(r"(?i)\(?\s*unaudited\s*\)?", 글):
                표["미감사"] = True
                j += 1
                continue
        p = 기간말(cs[0])
        if p:
            if 본문:
                k, 해, 날 = _머리훑기(줄들, j + 1, cs[1:])
                if p["날짜"]:
                    날 = [p["날짜"]] + 날
                if p["개월"] == 표["개월"] and ((해 and 해 == 표["해들"]) or (날 and 날 == 표["날들"])):
                    닫기()
                    j = k
                    continue
                break
            표["개월"] = p["개월"]
            if p["월일"]:
                표["월일"] = p["월일"]
            if p["날짜"]:
                표["날들"].append(p["날짜"])
            표["해들"] += [int(c) for c in cs[1:] if _해꼴.match(c)]
            j += 1
            continue
        if not 본문 and not st["값"]:
            if all(_해꼴.match(c) for c in cs):
                표["해들"] += [int(c) for c in cs]
                j += 1
                continue
            if all(_날짜칸(c) for c in cs):
                표["날들"] += [_날짜칸(c) for c in cs]
                j += 1
                continue
            if len(cs) == 1 and _월일꼴.match(cs[0]):
                md = _월일꼴.match(cs[0])
                표["월일"] = (_달[md.group(1).lower()], int(md.group(2)))
                j += 1
                continue
        수들 = [수읽기(c) for c in cs]
        if 수들[0] is None and len(cs) >= 2 and any(v is not None for v in 수들[1:]):
            # 칸 줄 — 「이름 | 값 | 값」
            if st["값"]:
                닫기()
            글칸 = [c for c, v in zip(cs, 수들) if v is None]
            t, _ = _점선떼기(" ".join(글칸))
            라벨더하기(t, True, j)
            st["값"] = [v for v in 수들 if v is not None]
            st["퍼센트"] = any(퍼센트칸(c) for c in cs)
            본문 = True
            닫기()
        elif all(v is not None for v in 수들):
            # 세로 줄 — 숫자만 있는 줄(한 칸 또는 여러 칸)
            if not st["라벨"] and not st["값"] and not 본문:
                j += 1                                      # 머리 앞의 떠돌이 숫자
                continue
            st["값"].extend(수들)
            st["퍼센트"] = st["퍼센트"] or any(퍼센트칸(c) for c in cs)
            본문 = True
        else:
            if st["값"]:
                닫기()
            if not 본문 and not st["라벨"] and (len(표["해들"]) + len(표["날들"]) == 1):
                tt = [_점선떼기(c) for c in cs]
                if not any(e for _, e in tt):
                    표["이름후보"] += [t for t, _ in tt]   # 한 기간 표의 열 이름(부문 표)
                    j += 1
                    continue
            t, 끝남 = _점선떼기(글)
            라벨더하기(t, 끝남, j)
            if 본문 and len(st["라벨"]) > 6:
                st["라벨"] = []
                break
        j += 1
    닫기()
    표["끝"] = j
    return 표


def 열이름정하기(표):
    """한 기간 표의 열 이름 후보를 값 개수에 맞춘다 — 「Total Reportable」 · 「Segments」 처럼 두 줄로 쪼개진 이름을 뒤에서부터 잇는다."""
    후 = list(표.get("이름후보") or [])
    if not 후 or (len(표["해들"]) + len(표["날들"])) > 1:
        return []
    셈 = {}
    for r in 표["행"]:
        셈[len(r["값"])] = 셈.get(len(r["값"]), 0) + 1
    if not 셈:
        return []
    n = max(셈, key=lambda x: (셈[x], x))
    if n < 2 or len(후) < n:
        return []
    while len(후) > n:
        후[-2] = 후[-2] + " " + 후[-1]
        후.pop()
    return 후


def 열끝들(표, 연말=(12, 31)):
    """표의 기간 열 → [기간 끝 날짜 …]. 날짜 머리가 있으면 그것, 해만 있으면 월일(머리 · 없으면 회사 연말)."""
    if 표["날들"]:
        return list(표["날들"])
    md = 표["월일"] or 연말
    낸 = []
    for y in 표["해들"]:
        말 = calendar.monthrange(y, md[0])[1]
        낸.append(datetime.date(y, md[0], min(md[1], 말)))
    return 낸


def 열개월(끝, 표개월, 연말):
    """흐름 표는 머리의 개월, 재무상태표(개월 없음)는 회사 연말에서 몇 달 지났나(연말 = 12)."""
    if 표개월:
        return 표개월
    if (끝.month, 끝.day) == tuple(연말) or (끝.month == 연말[0] and abs(끝.day - 연말[1]) <= 7):
        return 12
    n = (끝.month - 연말[0]) % 12
    return n or 12


def _주당행(r):
    """주당 값 줄(EPS · 주당 배당) — 백만 단위로 바꾸지 않는다. 가중평균 주식 수 줄은 단위 머리를 따른다."""
    글 = (r.get("줄") or "") + " " + (r.get("머리") or "")
    return bool(re.search(r"(?i)per (?:common )?share|per unit|주당", 글)) and not re.search(r"(?i)weighted|shares used|number of shares|주식\s*수", 글)


# ══════════════════════════════════════════════════════════ 미국 — 재무제표 절 · 감사 · 주석

_표제목 = {
    "재무상태": re.compile(r"(?i)^(?:condensed )?(?:consolidated |combined )?(?:balance sheets?|statements? of financial (?:position|condition))(?:\s*\(unaudited\))?$"),
    "손익": re.compile(r"(?i)^(?:condensed )?(?:consolidated |combined )?statements? of (?:operations|income|earnings|loss|"
                     r"(?:operations|income|loss|earnings) and comprehensive (?:income|loss|earnings)(?: \(loss\))?|"
                     r"income \(loss\)|\(loss\) income|operations and comprehensive (?:income \(loss\)|loss \(income\)))(?:\s*\(unaudited\))?$"),
    "현금흐름": re.compile(r"(?i)^(?:condensed )?(?:consolidated |combined )?statements? of cash flows?(?:\s*\(unaudited\))?$"),
}
_색인꼴 = re.compile(r"(?i)^index to (?:the )?(?:audited )?(?:consolidated |combined )?financial statements$")
_수낱말 = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
         "twelve": 12, "fifteen": 15, "twenty": 20, "twenty-five": 25, "thirty": 30, "forty": 40, "fifty": 50, "hundred": 100}


def _낱말수(w):
    w = (w or "").lower().strip()
    if w.isdigit():
        return int(w)
    return _수낱말.get(w)


def _쪽찾기(줄들, j):
    """줄 j 가 놓인 쪽 — 그 앞 마지막 「F-n」 표지(위치 지정 신고서는 쪽 표지가 쪽 머리에 온다)."""
    for k in range(min(j, len(줄들) - 1), -1, -1):
        m = _쪽번호꼴.match("".join(_칸들(줄들[k])))
        if m:
            return "F-" + m.group(1)
    return None


def 감사기간(글):
    """감사인 보고서 의견 문단 → {"재무상태": {날짜…}, "흐름": {(끝날짜, 개월)…}, "문장": 요약}. 덮는 기간만 「감사」 다."""
    낸 = {"재무상태": set(), "흐름": set()}
    평 = re.sub(r"\s+", " ", 글 or "")
    for m in re.finditer(r"(?i)balance sheets?\b.{0,300}?\bas of\s+(%s)\s+(\d{1,2}),\s*(\d{4})((?:\s*(?:,|and|,\s*and)\s*(?:(?:%s)\s+\d{1,2},\s*)?\d{4})*)"
                         % (_달꼴, _달꼴), 평):
        md = (_달[m.group(1).lower()], int(m.group(2)))
        낸["재무상태"].add(datetime.date(int(m.group(3)), *md))
        for y in re.finditer(r"(?:(%s)\s+(\d{1,2}),\s*)?(\d{4})" % _달꼴, m.group(4) or ""):
            md2 = (_달[y.group(1).lower()], int(y.group(2))) if y.group(1) else md
            낸["재무상태"].add(datetime.date(int(y.group(3)), *md2))
    for m in re.finditer(r"(?i)for each of the ([\w-]+) years in the (?:three-year |two-year )?period ended\s+(%s)\s+(\d{1,2}),\s*(\d{4})" % _달꼴, 평):
        n = _낱말수(m.group(1)) or 0
        md = (_달[m.group(2).lower()], int(m.group(3)))
        for k in range(n):
            낸["흐름"].add((datetime.date(int(m.group(4)) - k, *md), 12))
    for m in re.finditer(r"(?i)for the (?:fiscal )?years? ended\s+(%s)\s+(\d{1,2}),\s*(\d{4})((?:\s*(?:,|and|,\s*and)\s*(?:(?:%s)\s+\d{1,2},\s*)?\d{4})*)"
                         % (_달꼴, _달꼴), 평):
        md = (_달[m.group(1).lower()], int(m.group(2)))
        낸["흐름"].add((datetime.date(int(m.group(3)), *md), 12))
        for y in re.finditer(r"(?:(%s)\s+(\d{1,2}),\s*)?(\d{4})" % _달꼴, m.group(4) or ""):
            md2 = (_달[y.group(1).lower()], int(y.group(2))) if y.group(1) else md
            낸["흐름"].add((datetime.date(int(y.group(3)), *md2), 12))
    return 낸


def 재무절찾기(줄들):
    """→ {"시작": 색인 줄 | None, "감사문단": [글…], "제목": [(줄번호, 종류)…]}."""
    시작 = None
    for j, l in enumerate(줄들):
        if _색인꼴.match(" ".join(_칸들(l))):
            시작 = j
            break
    a = 시작 or 0
    감사 = []
    for j in range(a, len(줄들)):
        if re.match(r"(?i)^\s*\|?\s*we have audited\b", 줄들[j]):
            글 = []
            for k in range(j, min(len(줄들), j + 40)):
                if re.match(r"(?i)^\s*\|?\s*(basis for opinion|change in accounting principle|critical audit matter)", 줄들[k]):
                    break
                글.append(" ".join(_칸들(줄들[k])))
            감사.append(" ".join(글))
    제목 = []
    for j in range(a, len(줄들)):
        t = " ".join(_칸들(줄들[j]))
        if len(t) > 140:
            continue
        for 종류, r in _표제목.items():
            if r.match(t):
                제목.append((j, 종류))
                break
    return {"시작": 시작, "감사문단": 감사, "제목": 제목}


def _노트구간들(줄들, a, b):
    """[a, b) 안의 주석 머리 → [(시작, 끝, 번호, 제목)]."""
    머리 = []
    for j in range(a, min(b, len(줄들))):
        cs = _칸들(줄들[j])
        if len(cs) != 1:
            continue
        n = 노트머리(cs[0])
        if n:
            머리.append((j, n[0], n[1]))
    낸 = []
    for i, (j, 번호, 제목) in enumerate(머리):
        끝 = 머리[i + 1][0] if i + 1 < len(머리) else b
        낸.append((j, 끝, 번호, 제목))
    return 낸


def 구간표들(줄들, a, b, 배=None):
    """[a, b) 에서 기간 머리로 시작하는 표를 모두 읽는다 → [(표, 앞글)]. 앞글 = 표 바로 앞의 설명 줄(「Revenue disaggregated by … :」)."""
    낸 = []
    앞글 = None
    j = a
    while j < b:
        cs = _칸들(줄들[j])
        if not cs:
            j += 1
            continue
        if 기간말(cs[0]):
            표 = 표읽기(줄들, j, 배=배, 최대=max(50, b - j))
            if 표["행"]:
                낸.append((표, 앞글))
            j = max(j + 1, 표["끝"])
            앞글 = None
            continue
        t = " ".join(cs)
        if len(t) > 15 and not _쪽꼴.match(t) and 수읽기(t) is None:
            앞글 = t
        j += 1
    return 낸


def _주석단위(줄들, a, b):
    for j in range(a, min(b, len(줄들))):
        t = " ".join(_칸들(줄들[j]))
        if re.search(r"(?i)\(tables? in (thousands|millions|billions)", t):
            return 단위읽기(t)
    return None


def _평글(줄들, a, b):
    """줄들[a:b] 를 한 글로(줄바꿈 → 빈칸 · 길이 그대로 — 위치로 줄을 되찾는다) → (글, 줄 시작 위치들)."""
    시작들, 조각 = [], []
    n = 0
    for k in range(a, min(b, len(줄들))):
        시작들.append(n)
        s = " ".join(_칸들(줄들[k]))
        조각.append(s)
        n += len(s) + 1
    return " ".join(조각), 시작들


def _위치줄(시작들, pos, a):
    lo = 0
    for i, s in enumerate(시작들):
        if s <= pos:
            lo = i
        else:
            break
    return a + lo


def _짧은인용(글, 낱말=12):
    w = (글 or "").split()
    return " ".join(w[:낱말])


def 보고실체변화_영문(줄들, a, b):
    """공통지배 소급 결합 · 주식분할 소급 · 분할 문장 → 계약 꼴 목록. 인용은 15낱말 미만 · 쪽 표지."""
    평, 시작들 = _평글(줄들, a, b)
    낸, 본 = [], set()

    def 쪽(pos):
        return _쪽찾기(줄들, _위치줄(시작들, pos, a))

    # ① 공통지배 소급 결합
    공 = re.search(r"(?i)accounted for as (?:a |an )?(?:\w+ ){0,3}?(?:of )?entit(?:y|ies) under common control|"
                  r"(?:reorganizations?|combinations?|transactions?) (?:of|between) entit(?:y|ies) under common control|common control transactions?", 평)
    if 공:
        주변 = 평[max(0, 공.start() - 3500): 공.end() + 2000]
        보고실체 = bool(re.search(r"(?i)change in (?:the )?reporting entity", 주변))
        소급 = bool(re.search(r"(?i)retrospective(?:ly)?|retroactive(?:ly)?|for all periods presented", 주변))
        인용 = "%s · %s" % (_짧은인용(공.group(0), 12), 쪽(공.start()) or "쪽 미상")
        for m in re.finditer(r"(?i)\bon\s+((%s)\s+(\d{1,2}),\s*(\d{4})),?\s+[^.]{0,140}?\b(?:completed|consummated|closed)\s+(?:its|the|a)\s+"
                             r"(?:acquisition|merger|combination|purchase)\s+(?:of|with)\s+(.{3,80}?)(?=\s*\(|,|\s+in which|\s+pursuant|\.\s|$)" % _달꼴, 주변):
            대상 = m.group(5).strip().rstrip(".,")
            날 = datetime.date(int(m.group(4)), _달[m.group(2).lower()], int(m.group(3)))
            열쇠 = ("공통지배 소급 결합", 날.year, 대상.lower())
            if 열쇠 in 본:
                continue
            본.add(열쇠)
            낸.append({"해": str(날.year), "종류": "공통지배 소급 결합", "대상": 대상, "일자": 날.isoformat(),
                      "내용": "%s 결합(%s) — 공통지배 거래로 처리해 %s 장부가로 결합%s" % (
                          대상, 날.isoformat(), "전 기간에 소급해" if 소급 else "", " · 보고실체 변경(change in reporting entity)" if 보고실체 else ""),
                      "근거": "「%s」" % 인용})
        if not any(x["종류"] == "공통지배 소급 결합" for x in 낸):
            낸.append({"해": None, "종류": "공통지배 소급 결합", "대상": None, "일자": None,
                      "내용": "공통지배 결합 문장은 있으나 대상 · 일자 문장을 못 읽었다 — 원문 확인", "근거": "「%s」" % 인용})
    # ② 주식분할 소급
    for m in re.finditer(r"(?i)(?:\bon\s+((%s)\s+(\d{1,2}),\s*(\d{4})),?\s+[^.]{0,120}?)?\b([\w]+)-for-([\w]+)\s+(forward\s+|reverse\s+)?(?:stock|share)\s+split" % _달꼴, 평):
        가, 나 = _낱말수(m.group(5)), _낱말수(m.group(6))
        if not (가 and 나):
            continue
        뒤 = 평[m.end(): m.end() + 900]
        if not re.search(r"(?i)retroactive(?:ly)?|retrospective(?:ly)?|for all periods presented", 뒤):
            continue
        날 = datetime.date(int(m.group(4)), _달[m.group(2).lower()], int(m.group(3))) if m.group(1) else None
        if 날 is None:
            d = re.search(r"(?i)(%s)\s+(\d{1,2}),\s*(\d{4})" % _달꼴, 평[max(0, m.start() - 200): m.end() + 200])
            날 = datetime.date(int(d.group(3)), _달[d.group(1).lower()], int(d.group(2))) if d else None
        역 = (m.group(7) or "").strip().lower() == "reverse" or 가 < 나
        열쇠 = ("주식분할 소급", 날.year if 날 else None, "%d:%d" % (가, 나))
        if 열쇠 in 본:
            continue
        본.add(열쇠)
        낸.append({"해": str(날.year) if 날 else None, "종류": "주식분할 소급", "대상": None, "일자": 날.isoformat() if 날 else None,
                  "배율": "%d대%d" % (가, 나),
                  "내용": "%d대%d %s(%s) — 전 기간 주식 수 · 주당 정보 소급 조정" % (가, 나, "주식병합(역분할)" if 역 else "주식분할", 날.isoformat() if 날 else "일자 미상"),
                  "근거": "「%s」 · %s" % (_짧은인용(평[m.start(5): m.end()], 10), 쪽(m.start(5)) or "쪽 미상")})
    # ③ 분할(spin-off · carve-out) — 분할 신설회사의 결합재무제표
    m = re.search(r"(?i)\b(spin-off|spin off|separation and distribution|carve-out)\b", 평)
    if m and re.search(r"(?i)combined financial statements|carve-out financial statements|derived from the (?:consolidated )?(?:financial statements|accounting records)", 평):
        d = re.search(r"(?i)(%s)\s+(\d{1,2}),\s*(\d{4})" % _달꼴, 평[max(0, m.start() - 300): m.end() + 300])
        낸.append({"해": d.group(3) if d else None, "종류": "분할", "대상": None, "일자": None,
                  "내용": "분할 신설회사의 결합 · 분리 재무제표 — 모회사 장부에서 떼어 낸 숫자",
                  "근거": "「%s」 · %s" % (_짧은인용(평[m.start(): m.start() + 80], 10), 쪽(m.start()) or "쪽 미상")})
    return 낸


# ══════════════════════════════════════════════════════════ 미국 — 조립

_우선 = {"424B4": 0, "424B1": 1, "S-1/A": 2, "F-1/A": 2, "10-12B/A": 2, "S-1": 3, "F-1": 3, "10-12B": 3}
_파일꼴 = re.compile(r"^신고서_(?P<양식>.+?)_(?P<접수>\d{10}-\d{2}-\d{6})\.(?:htm|txt)$")


def _양식복원(s):
    return {"S-1A": "S-1/A", "F-1A": "F-1/A", "10-12BA": "10-12B/A"}.get(s, s)


def 신고서원문(raw, 원문=None):
    """→ (글 파일 경로 | None, 서류 정보 | None). sec_공시고르기.json 의 「신고서」 → 없으면 `신고서_*` 파일 가운데 확정 판 우선."""
    판 = _읽기(os.path.join(raw, "sec_공시고르기.json"), {}) or {}
    신 = (판.get("신고서") or {}).get("고른") or None
    if 원문:
        return 원문, 신
    후보 = []
    if 신 and 신.get("파일"):
        후보.append(os.path.join(raw, 신["파일"]))
    for p in sorted(glob.glob(os.path.join(raw, "신고서_*.htm")) + glob.glob(os.path.join(raw, "신고서_*.txt"))):
        m = _파일꼴.match(os.path.basename(p))
        if m:
            후보.append(p)
    if not 후보:
        return None, 신

    def 순(p):
        m = _파일꼴.match(os.path.basename(p))
        return (_우선.get(_양식복원(m.group("양식")), 9) if m else 9, -(os.path.getmtime(p) if os.path.exists(p) else 0))
    p = 후보[0] if (신 and 신.get("파일")) else sorted(후보, key=순)[0]
    txt = os.path.splitext(p)[0] + ".txt"
    if os.path.exists(txt):
        return txt, 신
    if os.path.exists(p):
        return p, 신
    return None, 신


def 글읽기(p):
    """txt(htm2txt 산출)면 그대로, htm 이면 미국원천읽기.글로 로 바꾼다(줄마다 칸 하나 — 세로 줄 꼴로 읽힌다)."""
    with io.open(p, encoding="utf-8", errors="ignore") as f:
        s = f.read()
    if p.lower().endswith((".htm", ".html")):
        import 미국원천읽기 as U                                # noqa: PLC0415
        s = U.글로(s)
    return s


def 미국읽기(raw, 기준일, 원문=None, 서류=None):
    """받아 둔 미국 신고서 → 「신고서재무/1」 dict. 원문(파일)을 주면 그것을 읽는다(시험 · 사람이 고른 판)."""
    낸 = 뼈대("US")
    낸["평가기준일"] = 기준일
    p, 신 = 신고서원문(raw, 원문)
    서류 = dict(서류 or 신 or {})
    if not p:
        낸["경보"].append("신고서 원문이 없다 — `sec_fetch.py --기준일 … --신고서` 로 받는다")
        낸["확인불가"].append({"항목": "신고서 재무", "원인": "조회 경로 문제", "대안": "sec_fetch.py --신고서"})
        return 낸
    sub = _읽기(os.path.join(raw, "submissions.json"), {}) or {}
    판 = _읽기(os.path.join(raw, "sec_공시고르기.json"), {}) or {}
    m = _파일꼴.match(os.path.basename(p))
    양식 = 서류.get("양식") or (_양식복원(m.group("양식")) if m else None)
    접수 = 서류.get("accession") or 서류.get("접수번호") or (m.group("접수") if m else None)
    cik = 판.get("CIK") or ("%010d" % int(sub["cik"]) if str(sub.get("cik") or "").isdigit() else None)
    낸["회사"] = sub.get("name") or 서류.get("제출인")
    낸["식별"] = {"CIK": cik, "티커": 판.get("티커") or ((sub.get("tickers") or [None])[0])}
    원문이름 = os.path.basename(p)
    낸["서류"].append({"종류": 양식, "접수번호": 접수, "제출인": {"이름": 낸["회사"], "식별": cik}, "제출일": 서류.get("제출일"),
                     "원문": "_raw/" + (서류.get("파일") or 원문이름), "고른까닭": 서류.get("고른까닭") or "사람이 준 원문(--원문) 또는 _raw 의 신고서 파일"})
    출처머리 = " ".join(x for x in (양식 or "신고서", 접수) if x)
    줄들 = 글읽기(p).splitlines()
    절 = 재무절찾기(줄들)
    if 절["시작"] is None:
        낸["경보"].append("재무제표 절 머리(INDEX TO … FINANCIAL STATEMENTS)를 못 찾았다 — 원문 전체에서 표 제목을 찾았다")
    감 = {"재무상태": set(), "흐름": set()}
    for 문단 in 절["감사문단"]:
        g = 감사기간(문단)
        감["재무상태"] |= g["재무상태"]
        감["흐름"] |= g["흐름"]
    if not 절["감사문단"]:
        낸["경보"].append("감사인 보고서 의견 문단(We have audited …)을 못 찾았다 — 연간 표도 「감사」 로 적지 않는다")

    # ── 표 제목마다 표를 읽고 연간 · 중간으로 가른다
    읽은 = []
    for j, 종류 in 절["제목"]:
        표 = 표읽기(줄들, j + 1)
        if not 표["행"]:
            continue
        표["종류"], 표["제목"], 표["제목줄"] = 종류, " ".join(_칸들(줄들[j])), j
        읽은.append(표)
    연말 = (12, 31)
    for 표 in 읽은:
        if 표["종류"] != "재무상태" and 표["개월"] == 12 and 표["월일"]:
            연말 = 표["월일"]
            break
    연간, 중간, 남은 = {}, {}, []
    for 표 in 읽은:
        if 표["종류"] == "재무상태":
            끝들 = 열끝들(표, 연말)
            중간표 = 표["미감사"] or any(열개월(e, None, 연말) != 12 for e in 끝들[:1])
        else:
            중간표 = 표["미감사"] or (표["개월"] or 12) < 12
        칸 = 중간 if 중간표 else 연간
        if 표["종류"] in 칸:
            남은.append(표)
            continue
        칸[표["종류"]] = 표
    if 남은:
        낸["경보"].append("같은 종류의 재무제표가 %d벌 더 있다(다른 실체 · 피취득회사 재무제표일 수 있다) — 첫 벌만 읽었다: %s"
                        % (len(남은), " · ".join("%s(%s)" % (t["제목"], _쪽찾기(줄들, t["제목줄"]) or "쪽 미상") for t in 남은[:5])))
    if not 연간:
        낸["경보"].append("연간 재무제표 표를 못 읽었다")
    단위들 = {t.get("배") for t in list(연간.values()) + list(중간.values()) if t.get("배") is not None}
    if not 단위들:
        낸["경보"].append("표 머리의 단위(in millions …)를 못 읽었다 — 원문 수를 그대로 백만 단위로 보았다")

    기간표 = {}                                         # id → {"끝", "개월", "감사구분"}
    기준 = _날(기준일)

    def 감사구분(끝, 개월, 종류, 중간표):
        if 중간표:
            return "미감사 중간"
        if 종류 == "재무상태":
            return "감사" if 끝 in 감["재무상태"] else "미감사"
        return "감사" if (끝, 개월) in 감["흐름"] else "미감사"

    def 표행들(표, 중간표):
        """표 → (열 [(id, 끝, 개월)], 행 [{"줄", "값": {id: v}, "머리", "줄번호"}])."""
        끝들 = 열끝들(표, 연말)
        열 = []
        for e in 끝들:
            개 = 열개월(e, 표["개월"] if 표["종류"] != "재무상태" else None, 연말)
            열.append((기간id(e, 개, 연말월=연말[0]), e, 개))
        배 = 표.get("배") if 표.get("배") is not None else 1.0
        행 = []
        for r in 표["행"]:
            if r["퍼센트"]:
                continue
            값 = {}
            for (k, e, 개), v in zip(열, r["값"]):
                if 기준 and e > 기준 + datetime.timedelta(days=7):
                    continue
                값[k] = 정수로(v if _주당행(r) else v * 배)
            if 값:
                행.append({"줄": r["줄"], "값": 값, "머리": r["머리"], "줄번호": r["줄번호"], **({"주당": True} if _주당행(r) else {})})
        return 열, 행

    표준 = 낸["표준줄"]
    근거 = 낸["근거"]
    원행 = {"손익": [], "현금흐름": [], "재무상태": []}
    연간id = set()
    for 중간표, 칸 in ((False, 연간), (True, 중간)):
        for 종류 in ("재무상태", "손익", "현금흐름"):
            표 = 칸.get(종류)
            if not 표:
                continue
            열, 행 = 표행들(표, 중간표)
            if 기준 and any(e > 기준 + datetime.timedelta(days=7) for _, e, _ in 열):
                낸["경보"].append("%s — 평가기준일 뒤 기간 열은 뺐다" % 표["제목"])
            새열 = [k for k, e, 개 in 열 if not (중간표 and k in 연간id)]      # 중간 표의 비교 열(연말)은 연간 감사 표가 이미 준다
            for k, e, 개 in 열:
                if k in 새열 and (not 기준 or e <= 기준 + datetime.timedelta(days=7)):
                    x = 기간표.setdefault(k, {"끝": e, "개월": 개, "감사구분": None, "표": set()})
                    x["표"].add(종류)
                    if x["감사구분"] in (None, "미감사"):
                        x["감사구분"] = 감사구분(e, 개, 종류, 중간표)
            if not 중간표:
                연간id.update(새열)
            행 = [dict(r, 값={k: v for k, v in r["값"].items() if k in 새열}) for r in 행]
            행 = [r for r in 행 if r["값"]]
            쪽 = _쪽찾기(줄들, 표["제목줄"])
            for r in 행:
                원행[종류].append(r)
                낸["원표"][종류].append({"줄": r["줄"], "값": r["값"], "표": "%s%s · %s" % (표["제목"], " (미감사 중간)" if 중간표 else "", 쪽 or "쪽 미상"),
                                     **({"머리": r["머리"]} if r.get("머리") else {}), **({"주당": True} if r.get("주당") else {})})
            상태 = "미감사 중간(신고서)" if 중간표 else None
            for 이름 in 표준줄이름:
                if 종류 not in 표준줄구분[이름]:
                    continue
                if 이름 == "차입금":
                    짝 = 차입금짝(행)
                    if not 짝:
                        continue
                    줄이름, 값 = " + ".join(짝[0]), 짝[1]
                else:
                    짝 = 표준짝(행, 이름)
                    if not 짝:
                        continue
                    줄이름, 값 = 짝[0], 짝[1]
                for k, v in 값.items():
                    if k in 표준[이름]:
                        continue
                    표준[이름][k] = v
                    구 = 상태 or ("감사(신고서)" if 기간표.get(k, {}).get("감사구분") == "감사" else "미감사(신고서)")
                    근거.setdefault(이름, {})[k] = {"출처": "%s · %s %s · 원문 줄 「%s」" % (출처머리, 쪽 or "쪽 미상", 표["제목"], 줄이름),
                                                 "기준일": 기간표.get(k, {}).get("끝").isoformat() if 기간표.get(k) else None,
                                                 "확인상태": 구}
    # ── 기간 목록 · 보고실체변화
    주석구간끝 = min([t["제목줄"] for t in 중간.values()] or [len(줄들)])
    주석구간시작 = max([t["끝"] for t in 연간.values()] or [절["시작"] or 0])
    변화 = 보고실체변화_영문(줄들, 주석구간시작, 주석구간끝)
    if not 변화 and 절["시작"] is not None:
        변화 = 보고실체변화_영문(줄들, 절["시작"], len(줄들))
    낸["보고실체변화"] = 변화
    결합 = [x for x in 변화 if x["종류"] == "공통지배 소급 결합" and x.get("대상")]
    보고실체 = "등록회사 연결"
    if 결합:
        보고실체 = "등록회사 연결 — 공통지배 소급 결합 뒤 보고 실체(%s 를 전 기간에 결합한 숫자)" % " · ".join(x["대상"] for x in 결합)
    if any(x["종류"] == "분할" for x in 변화):
        보고실체 = "분할 신설회사 결합 재무제표(모회사 장부에서 떼어 낸 숫자)"
    for k in sorted(기간표, key=lambda k: (기간표[k]["감사구분"] == "미감사 중간", -기간표[k]["끝"].toordinal())):
        x = 기간표[k]
        if x["감사구분"] == "미감사":
            낸["경보"].append("%s — 감사인 보고서가 덮는 기간으로 읽히지 않았다(감사구분 「미감사」)" % k)
        낸["기간"].append({"id": k, "시작": 기간시작(x["끝"], x["개월"]), "끝": x["끝"].isoformat(), "개월": x["개월"], "감사구분": x["감사구분"],
                         "원천종류": "신고서", "보고실체": 보고실체, "참고이력": False, "표": sorted(x["표"])})

    # ── 부문 주석 · 매출 분해(연간 주석 구간 · 중간 주석 구간)
    낸["원표"]["매출분해"] = []
    부문 = {}
    부문매출 = {}
    구간들 = [(주석구간시작, 주석구간끝, False)]
    if 중간:
        구간들.append((max(t["끝"] for t in 중간.values()), len(줄들), True))
    for a, b, 중간표 in 구간들:
        배 = _주석단위(줄들, a, min(b, a + 400))
        for s, e, 번호, 제목 in _노트구간들(줄들, a, b):
            if re.search(r"(?i)segment", 제목):
                표들 = 구간표들(줄들, s + 1, e, 배)
                가꼴 = [(t, 앞) for t, 앞 in 표들 if 열이름정하기(t)]
                for t, 앞 in 가꼴:
                    이름들 = 열이름정하기(t)
                    끝들 = 열끝들(t, 연말)
                    if len(끝들) != 1:
                        continue
                    k = 기간id(끝들[0], t["개월"] or 12, 연말월=연말[0])
                    if k not in 기간표 or (기준 and 끝들[0] > 기준 + datetime.timedelta(days=7)):
                        continue
                    tb = t.get("배") if t.get("배") is not None else (배 if 배 is not None else 1.0)
                    for r in t["행"]:
                        if r["퍼센트"]:
                            continue
                        if len(r["값"]) == len(이름들):
                            짝 = list(zip(이름들, r["값"]))
                        elif len(r["값"]) == 1:
                            짝 = [(이름들[-1], r["값"][0])]
                        else:
                            continue
                        for 이름, v in 짝:
                            열쇠 = (이름, r["줄"])
                            x = 부문.setdefault(열쇠, {"부문": 이름, "줄": r["줄"], "값": {}, "표": "Note %d %s · %s" % (번호, 제목, _쪽찾기(줄들, r["줄번호"]) or "쪽 미상")})
                            if re.match(r"(?i)^total\b|consolidated|^합계", 이름):
                                x["합계"] = True
                            x["값"][k] = 정수로(v * tb)
                    매출행 = 표준짝([{"줄": r["줄"], "값": {"_": 1}} for r in t["행"] if len(r["값"]) == len(이름들)], "매출")
                    if 매출행:
                        r = next(r for r in t["행"] if r["줄"] == 매출행[0] and len(r["값"]) == len(이름들))
                        나눔 = [(n, v) for n, v in zip(이름들, r["값"]) if not re.match(r"(?i)^total\b|consolidated|^합계", n)]
                        if 나눔:
                            부문매출[k] = (정수로(sum(v for _, v in 나눔) * tb), " + ".join("%s %s" % (n, 정수로(v * tb)) for n, v in 나눔))
                if not 가꼴:
                    for t, 앞 in 표들:
                        if 앞 and re.search(r"(?i)geograph|countr|region", 앞):
                            continue
                        끝들 = 열끝들(t, 연말)
                        tb = t.get("배") if t.get("배") is not None else (배 if 배 is not None else 1.0)
                        ids = [기간id(e, t["개월"] or 12, 연말월=연말[0]) for e in 끝들]
                        for r in t["행"]:
                            if r["퍼센트"] or not re.match(r"(?i)^(?:total )?(?:net )?(?:revenues?|net sales|sales)\s*:?$", 줄다듬(r["머리"] or "")):
                                continue
                            if re.match(r"(?i)^total\b", 줄다듬(r["줄"])):
                                continue
                            값 = {k: 정수로(v * tb) for k, v in zip(ids, r["값"]) if k in 기간표}
                            if 값:
                                x = 부문.setdefault((r["줄"], r["머리"]), {"부문": r["줄"], "줄": r["머리"], "값": {}, "표": "Note %d %s" % (번호, 제목)})
                                x["값"].update(값)
                    if 부문:
                        for k in 기간표:
                            ks = [x["값"][k] for x in 부문.values() if k in x["값"] and not x.get("합계")]
                            if ks:
                                부문매출[k] = (정수로(sum(ks)), "부문 행 %d개 합" % len(ks))
            elif re.search(r"(?i)\brevenues?\b|disaggregat", 제목) and not 중간표:
                for t, 앞 in 구간표들(줄들, s + 1, e, 배):
                    if 열이름정하기(t):
                        continue
                    끝들 = 열끝들(t, 연말)
                    ids = [기간id(e2, t["개월"] or 12, 연말월=연말[0]) for e2 in 끝들]
                    tb = t.get("배") if t.get("배") is not None else (배 if 배 is not None else 1.0)
                    for r in t["행"]:
                        if r["퍼센트"]:
                            continue
                        값 = {k: 정수로(v * tb) for k, v in zip(ids, r["값"]) if k in 기간표}
                        if 값:
                            낸["원표"]["매출분해"].append({"표": (앞 or "Note %d %s" % (번호, 제목))[:120], "줄": r["줄"], "값": 값,
                                                         "쪽": _쪽찾기(줄들, r["줄번호"])})
    낸["원표"]["부문"] = list(부문.values())
    if not 부문:
        낸["확인불가"].append({"항목": "부문 주석", "원인": "항목 부재", "대안": "부문 주석(Segment)이 없거나 표 꼴을 못 읽었다 — 원문 확인"})

    # ── 검산
    중간자본 = {}
    for r in 원행["재무상태"]:
        if re.match(r"(?i)^(?:total )?(?:redeemable|temporary equity|mezzanine)", 줄다듬(r["줄"])) and not re.search(r"(?i)liabilities", 줄다듬(r["줄"])):
            for k, v in r["값"].items():
                중간자본[k] = 정수로((중간자본.get(k) or 0) + v)
    영업비용 = {}
    for r in 원행["손익"]:
        if re.match(r"(?i)^total (?:operating )?costs and expenses$|^total costs and operating expenses$", 줄다듬(r["줄"])):
            for k, v in r["값"].items():
                영업비용.setdefault(k, (v, "원문 줄 「%s」" % r["줄"]))
    if not 영업비용:
        for 칸 in (연간, 중간):
            표 = 칸.get("손익")
            if not 표:
                continue
            _, 행 = 표행들(표, 칸 is 중간)
            가 = next((i for i, r in enumerate(행) if 표준짝([r], "매출")), None)
            나 = next((i for i, r in enumerate(행) if 표준짝([r], "영업이익")), None)
            if 가 is None or 나 is None or 나 <= 가 + 1:
                continue
            사이 = [r for r in 행[가 + 1: 나] if not re.match(r"(?i)^(?:total|gross)\b", 줄다듬(r["줄"]))]
            for k in 행[가]["값"]:
                if all(k in r["값"] for r in 사이):
                    영업비용.setdefault(k, (sum(r["값"][k] for r in 사이), "매출과 영업이익 사이 %d줄의 합" % len(사이)))
    낸["검산"] = 검산셋(표준, {"중간자본": {k: v for k, v in 중간자본.items() if k in (표준.get("자산총계") or {})},
                       "영업비용": 영업비용, "부문매출": 부문매출})

    # ── 확인불가
    for 이름 in 표준줄이름:
        if not 표준[이름]:
            낸["확인불가"].append({"항목": 이름, "원인": "항목 부재", "대안": "원표에서 다른 이름의 줄을 사람이 확인(짝짓기 낱말에 안 걸렸다)"})
    흐름해 = sorted(k for k, x in 기간표.items() if "손익" in x["표"] and k.startswith("FY"))
    상태해 = {k for k, x in 기간표.items() if "재무상태" in x["표"]}
    for k in 흐름해:
        if k not in 상태해:
            낸["확인불가"].append({"항목": "재무상태표 %s" % k, "원인": "보고 의무 없음",
                                "대안": "신고서는 재무상태표를 최근 2개년만 싣는다 — 더 앞은 이전 신고서 · 정기보고서"})
    return 낸


# ══════════════════════════════════════════════════════════ 입구

def 국내읽기(raw, 기준일):
    try:
        import 신고서재무_국내 as K                             # noqa: PLC0415
    except ImportError:
        return None
    return K.읽기(raw, 기준일)


def 읽기(raw, 기준일, 시장="US", 원문=None):
    if 시장 == "KR":
        return 국내읽기(raw, 기준일)
    return 미국읽기(raw, 기준일, 원문=원문)


def 종료판정(낸):
    """종료 1(발견) = 검산 어긋남 · 매출 못 읽음 · 서류 없음. 확인불가의 「항목 부재」 는 정보라 세지 않는다 — 분할 부문 표처럼 늘 몇 줄이 없는
    서류가 있어서다(2026-10-25 본선 — 국내 단독 입구와 같은 잣대로 맞춤). 항목 부재는 산출의 `확인불가` 에 그대로 남는다."""
    if any(x.get("판정") == "어긋남" for x in 낸.get("검산") or []):
        return 발견
    if not (낸.get("표준줄") or {}).get("매출"):
        return 발견
    if not 낸.get("서류"):
        return 발견
    return 통과


def _시장짐작(raw):
    if os.path.exists(os.path.join(raw, "sec_공시고르기.json")) or glob.glob(os.path.join(raw, "신고서_*")):
        return "US"
    if glob.glob(os.path.join(raw, "dart_*")):
        return "KR"
    return "US"


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="신고서 · 투자설명서 재무 → 「신고서재무/1」")
    ap.add_argument("--raw", default=os.path.join(os.path.dirname(여기), "_raw"), help="받아 둔 원천 폴더(기본: 키트의 _raw)")
    ap.add_argument("--기준일", "--재무기준일", dest="기준일", default=None,
                    help="재무기준일 F YYYY-MM-DD — 이 날 뒤 기간 열은 뺀다(평가기준일 전에 제출된 마지막 분기말 · 옛 이름 --기준일 은 지금 뜻 그대로)")
    ap.add_argument("--평가기준일", default=None, help="평가기준일 T YYYY-MM-DD — 산출 머리에만 적는다(읽는 값은 바꾸지 않는다)")
    ap.add_argument("--가정", default=None, help="가정 파일 — 날짜 인자를 비우면 기준일.py 로 F · T 를 푼다(F 가 없으면 F = T)")
    ap.add_argument("--시장", choices=("US", "KR"), default=None, help="없으면 _raw 의 파일로 짐작")
    ap.add_argument("--원문", default=None, help="읽을 신고서 글 · htm 파일(없으면 sec_공시고르기.json 의 「신고서」)")
    ap.add_argument("-o", "--출력", default=None, help="기본: <raw>/신고서재무.json")
    a = ap.parse_args(argv)
    import 기준일인자 as _기인                                  # noqa: PLC0415 — 날짜 둘(2026-10-25)
    a.기준일 = _기인.풀기(a.기준일, a.가정, _기인.재무, 인자="--기준일")
    a.평가기준일 = _기인.풀기(a.평가기준일, a.가정, _기인.평가, 인자="--평가기준일")
    if not a.기준일:
        ap.error("--기준일(재무기준일) 또는 --가정 이 있어야 합니다")
    if not os.path.isdir(a.raw):
        print("원천 폴더가 없습니다: %s" % a.raw)
        return 입력오류
    시장 = a.시장 or _시장짐작(a.raw)
    낸 = 읽기(a.raw, a.기준일, 시장, 원문=a.원문)
    if 낸 is None:
        print("국내 모듈 없음 — 스크립트/신고서재무_국내.py(국내 갈래)가 없다. --시장 KR 은 그 파일의 읽기(raw, 기준일)를 부른다")
        return 입력오류
    _기인.머리(낸, a.기준일, a.평가기준일)                     # 재무기준일 = F · 평가기준일 = T(알면)
    if 시장 == "US" and not 낸.get("서류"):
        p = 저장(낸, a.raw, a.출력)
        print("신고서 원문이 없습니다 — sec_fetch.py --기준일 … --신고서 로 받으십시오(%s)" % p)
        return 입력오류
    p = 저장(낸, a.raw, a.출력)
    S = (낸.get("표준줄") or {}).get("매출") or {}
    print("신고서재무 저장: %s" % p)
    print("  서류 %s · 기간 %s" % (" · ".join("%s %s" % (d.get("종류"), d.get("접수번호")) for d in 낸.get("서류") or []),
                                " · ".join("%s(%s)" % (x["id"], x["감사구분"]) for x in 낸.get("기간") or [])))
    print("  매출 %s" % " · ".join("%s %s" % (k, S[k]) for k in sorted(S, key=_기간정렬)))
    print("  보고실체변화 %d건 · 검산 %d건(어긋남 %d) · 확인불가 %d · 경보 %d" % (
        len(낸.get("보고실체변화") or []), len(낸.get("검산") or []), sum(1 for x in 낸.get("검산") or [] if x.get("판정") == "어긋남"),
        len(낸.get("확인불가") or []), len(낸.get("경보") or [])))
    for x in 낸.get("경보") or []:
        print("  ※ " + x)
    return 종료판정(낸)


if __name__ == "__main__":
    sys.exit(main())

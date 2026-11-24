# -*- coding: utf-8 -*-
"""sec_부문 — 정기 공시(10-K · 10-Q · 20-F · 40-F · XBRL 있는 6-K)의 XBRL 인스턴스에서 **부문(사업부) 축 차원 사실**을 읽어
`_raw/부문매출.json`(「부문매출/1」)으로 낸다 (2026-10-25 Y3-2 C · 계약 `연구/재무이력없음_20261025/07_Y3-2계약.md` 0절 7).

왜 만들었나
  SEC companyfacts 는 비차원 사실만 싣는다 — 부문 매출 · 부문 영업이익은 부문 축(멤버)이 붙은 맥락이라 어느 도구에도 오지 않았다.
  그래서 평가기준일이 기중이면(반기 · 분기 첫 열) 부문 누계 실적을 사람이 10-Q 원문 Segments 표에서 손으로 읽었다(T3 재현 4절 ⑥).
  같은 공시의 XBRL 인스턴스에는 그 표가 차원 사실로 들어 있다 — 원문 HTML 표 읽기보다 이 길이 먼저다(계약 0절 7).
  **회사 · 업종과 무관하다** — 축 · 개념 · 멤버를 이름 꼴과 실측 덮음으로 고르고, 회사 확장 멤버는 공시가 적은 이름 그대로 싣는다.

무엇을 읽나
  공시 색인의 인스턴스(`*_htm.xml` — 받기는 `sec_xbrl보충.받기` 를 그대로 쓴다) · 같은 이름의 라벨 링크베이스(`*_lab.xml` — 있으면 멤버의 표시 이름).
  고르는 공시(인자 없으면): `_raw/submissions.json` 의 XBRL 정기 공시 가운데 기간 끝 ≤ 기준일 + 7일인 것 — 가장 늦은 연차 보고서 하나와 그 뒤 분기
  보고서(해외 발행인은 XBRL 6-K)를 늦은 것부터 `--최대` 개. `--접수번호` 를 주면 그것만.

규칙
  · 부문 축 = 표준 이름공간(us-gaap · ifrs-full · srt)의 `…SegmentsAxis` 꼴(StatementBusinessSegmentsAxis · SegmentsAxis · ReportableSegmentsAxis …).
    회사 확장 축은 쓰지 않고 「확장 부문 축 후보」로 경보에 적는다.
  · 맥락 꼴 — 부문 축 하나만 · 부문 축 + 통합 항목 축(ConsolidationItemsAxis · SegmentConsolidationItemsAxis)의 영업부문 멤버 = 그 부문의 값.
    부문 축 + 다른 축(제품 · 지역 분해) · 부문 축 + 통합 항목 축의 조정 멤버 = 부문 안 분해라 뺀다(센다).
    통합 항목 축 하나만 — 영업부문 멤버면 「부문 합(공시)」, 그 밖 멤버(부문 간 제거 · 전사 · 조정)면 「축 밖 조정」 — 검산에 쓴다.
  · 멤버 종류 — 합계(ReportableSegments · OperatingSegments 꼴 멤버가 부문 축에 선 것) · 조정(Elimination · Intersegment · Corporate · NonSegment ·
    Reconciling · Unallocated) · 기타(AllOther) · 보고부문(그 밖).
  · 개념 — 매출 · 손익 두 갈래마다 후보를 여럿 두고(`매출후보` · `손익후보` — 회사 확장 손익 개념은 이름 꼴로 받는다), 공시마다 **보고부문 × 기간을 가장 많이
    덮는 것 → 부문 합 = 비차원 총액 검산을 지나는 것 → 후보 차례** 로 고른다. 고른 까닭과 후보별 덮음 수를 `개념고름` 에 남긴다.
  · 같은 (멤버 · 개념 · 기간)이 여러 공시에 있으면 접수일이 늦은 공시의 값을 `값표` 에 쓰고, 다른 값이면 `이전값` 에 남긴다(재작성 · 부문 재편).
  · 기간 id — 키트 기간축 · `미국원천읽기` 기준일 누계 표지와 같은 꼴: 회계연도 = 그 기간이 속한 회계연도(종료일이 속한 해 · 52/53주 7일 허용),
    12개월 FY2025A · 3개월 분기 2Q26A(결산월에서 센 분기 번호) · 누계 1H26A · 9M26A · 그 밖 nM26A. 12월 결산이면 `신고서재무.기간id` 와 글자까지 같다.
  · 값은 인스턴스 값 그대로(원 단위 · 부호 그대로). 13번으로 옮기는 일은 `공시채움.py` 의 부문 갈래가 하고(사람이 구분 ↔ 멤버를 적었을 때만) 환산배율로 나눈다.
  · 연락처는 환경변수 SEC_CONTACT_EMAIL 에서 읽고 찍지 않는다. 초당 열 건 한도 안에서 천천히(요청 사이 0.2초 이상).

사용:
    python 스크립트/sec_부문.py                                   # _raw/submissions.json 에서 공시를 골라 받고 _raw/부문매출.json
    python 스크립트/sec_부문.py --기준일 2026-06-30 --최대 3
    python 스크립트/sec_부문.py --cik 0000000000 --접수번호 0000000000-26-000000 [--접수번호 …]
    python 스크립트/sec_부문.py --인스턴스 a.xml [--라벨 a_lab.xml] --접수번호 … --양식 10-Q --접수일 2026-08-04   # 받아 둔 파일(네트워크 0)
    python 스크립트/sec_부문.py … --보태기                          # 있던 부문매출.json 의 다른 공시 사실을 남기고 더한다
종료 코드 — 0 통과(부문 사실을 읽었고 매출 검산 어긋남 없음) / 1 발견(부문 사실 없음 · 매출 검산 어긋남 · 받지 못한 공시) / 2 입력오류.
"""
from __future__ import annotations

import argparse
import calendar
import datetime
import io
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
import sec_xbrl보충 as X                              # noqa: E402  받기 · 단위 · 이름공간은 그 파일의 것(읽기만)
from 종료코드 import 통과, 발견, 입력오류              # noqa: E402

ROOT = os.path.dirname(여기)
형식 = "부문매출/1"
도구표지 = "sec_부문.py"
분기양식 = ("10-Q", "10-Q/A", "6-K", "6-K/A")
연차양식 = X.연차양식
고를양식 = tuple(X.정기양식) + ("6-K", "6-K/A")
표준 = ("us-gaap", "ifrs-full", "srt")
_LINK = "http://www.xbrl.org/2003/linkbase"
_XL = "http://www.w3.org/1999/xlink"

부문축꼴 = re.compile(r"^(?:StatementBusiness|Reportable|Operating|Business)?SegmentsAxis$")
통합축꼴 = re.compile(r"^(?:Segment)?ConsolidationItemsAxis$")
영업부문멤버꼴 = re.compile(r"^OperatingSegmentsMember$")
합계멤버꼴 = re.compile(r"^(?:ReportableSegments|OperatingSegments|TotalReportableSegments|SegmentsTotal)(?:Aggregation)?Member$")
# 「Corporate」 는 멤버 이름 전체가 전사 · 기타 꼴일 때만(「CorporateAndInvestmentBank」 같은 보고부문 이름을 조정으로 읽지 않는다)
조정멤버꼴 = re.compile(r"(?i)(Eliminat|Intersegment|Reconcil|Unallocated|NonSegment|^Corporate(AndOther|Other|Activities|Items|AndEliminations?)?Member$)")
기타멤버꼴 = re.compile(r"(?i)AllOther")

# 개념 후보 — 차례가 우선순위(덮음 · 검산이 같을 때). 이름공간 없는 이름은 us-gaap · ifrs-full 어느 쪽이든 받는다
매출후보 = ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "RevenueFromContractWithCustomerIncludingAssessedTax",
        "Revenue", "RevenueFromContractsWithCustomers", "SegmentReportingInformationRevenue", "SalesRevenueNet",
        "SegmentReportingInformationRevenueFromExternalCustomers", "RevenueFromExternalCustomers", "RevenuesNetOfInterestExpense",
        "SalesRevenueGoodsNet", "SalesRevenueServicesNet", "RevenueFromSaleOfGoods", "RevenueFromRenderingOfServices")
손익후보 = ("OperatingIncomeLoss", "SegmentReportingInformationOperatingIncomeLoss", "SegmentReportingSegmentOperatingProfitLoss",
        "ProfitLossFromOperatingActivities", "(확장)", "GrossProfit",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments", "ProfitLossBeforeTax")
# 회사 확장 손익 개념(부문 손익 측정치를 확장 태그로 내는 회사 — ASU 2023-07 뒤 흔하다)의 이름 꼴. 매출 · 비용 · 자산 이름은 뺀다
확장손익꼴 = re.compile(r"(?i)(Operating(Income|Profit)|Segment(Operating)?(Profit|Income|Earnings|Contribution)|Adjusted.*(EBITDA|OperatingIncome)|EBITDA)")
확장제외꼴 = re.compile(r"(?i)(Revenue|Sales|Expense|Cost|Asset|Liabilit|Margin|Percent|Ratio)")


# ══════════════════════════════════════════════════════════ 기간 id

def _날(s):
    if isinstance(s, datetime.date):
        return s
    try:
        return datetime.date.fromisoformat(("%s" % s)[:10])
    except (TypeError, ValueError):
        return None


def 연말읽기(글):
    """dei:CurrentFiscalYearEndDate(「--12-31」) · submissions fiscalYearEnd(「1231」) → (월, 일) | None."""
    m = re.search(r"(\d{2})-?(\d{2})\s*$", ("%s" % (글 or "")).strip())
    if not m:
        return None
    월, 일 = int(m.group(1)), int(m.group(2))
    return (월, 일) if 1 <= 월 <= 12 and 1 <= 일 <= 31 else None


def _연말(해, 연말):
    월, 일 = 연말
    return datetime.date(해, 월, min(일, calendar.monthrange(해, 월)[1]))


def 회계연도(끝, 연말=(12, 31)):
    """기간 끝이 속한 회계연도 — 그 끝(− 7일) 뒤의 첫 결산일이 속한 해(52/53주 결산이 결산월 밖 며칠로 넘어가도 같은 해)."""
    e = _날(끝)
    기 = e - datetime.timedelta(days=7)
    해 = 기.year
    while _연말(해, 연말) < 기:
        해 += 1
    return 해


def 기간정보(시작, 끝, 연말=(12, 31)):
    """(시작, 끝) → {id, 시작, 끝, 개월, 회계연도, 종류(연간 · 분기 · 누계 · 기타)}. 시점(시작 없음)은 None."""
    s, e = _날(시작), _날(끝)
    if not (s and e) or e < s:
        return None
    fy = 회계연도(e, 연말)
    fy시작 = _연말(fy - 1, 연말) + datetime.timedelta(days=1)
    누계 = abs((s - fy시작).days) <= 7
    개월 = int(round(((e - s).days + 1) / 30.44))
    yy = fy % 100
    if 개월 == 12 and 누계:
        return {"id": "FY%dA" % fy, "시작": s.isoformat(), "끝": e.isoformat(), "개월": 12, "회계연도": fy, "종류": "연간"}
    if 개월 == 3:
        q = max(1, min(4, int(round(((e - fy시작).days + 1) / 30.44 / 3))))
        return {"id": "%dQ%02dA" % (q, yy), "시작": s.isoformat(), "끝": e.isoformat(), "개월": 3, "회계연도": fy,
                "종류": "누계" if 누계 else "분기"}
    if 누계 and 개월 in (6, 9):
        return {"id": "%s%02dA" % ({6: "1H", 9: "9M"}[개월], yy), "시작": s.isoformat(), "끝": e.isoformat(), "개월": 개월, "회계연도": fy, "종류": "누계"}
    return {"id": "%dM%02dA%s" % (개월, yy, "" if 누계 else "_" + e.strftime("%m%d")), "시작": s.isoformat(), "끝": e.isoformat(), "개월": 개월,
            "회계연도": fy, "종류": "누계" if 누계 else "기타"}


# ══════════════════════════════════════════════════════════ 인스턴스 · 라벨 파싱

def _이름공간표(내용):
    """접두사 → URI(인스턴스가 선언한 그대로 — QName 글의 접두사를 풀 때 쓴다)."""
    표 = {}
    for 사건, (접두, uri) in ET.iterparse(io.BytesIO(내용), events=("start-ns",)):
        표.setdefault(접두 or "", uri)
    return 표


def _짧은이름(uri, 거꾸로):
    return X.이름공간(uri) or 거꾸로.get(uri) or uri


def _큐네임(글, 표, 거꾸로):
    """「us-gaap:StatementBusinessSegmentsAxis」 꼴 글 → 표준 접두사로 고친 QName(회사 확장은 인스턴스 접두사 그대로)."""
    글 = (글 or "").strip()
    if ":" not in 글:
        return 글
    p, 이름 = 글.split(":", 1)
    uri = 표.get(p)
    return "%s:%s" % (_짧은이름(uri, 거꾸로) if uri else p, 이름)


def 차원파싱(내용):
    """XBRL 인스턴스(바이트) → {맥락, 사실, dei}. `sec_xbrl보충.파싱` 이 일부러 빼는 차원 맥락을 여기서 읽는다(그 파일은 고치지 않는다).
    맥락 {id: {시작 | None, 끝, 차원 {축: 멤버}, 형식차원(bool)}} · 사실 [{개념(ns:이름), 표준(bool), 맥락, 단위, 값, decimals}] · dei {이름: 글}."""
    표 = _이름공간표(내용)
    거꾸로 = {}
    for p, uri in 표.items():
        if p and not X.이름공간(uri):
            거꾸로.setdefault(uri, p)
    뿌리 = ET.fromstring(내용)
    맥락, 단위 = {}, {}
    for c in 뿌리.findall("{%s}context" % X._XBRLI):
        p = c.find("{%s}period" % X._XBRLI)
        if p is None:
            continue
        즉 = p.find("{%s}instant" % X._XBRLI)
        if 즉 is not None:
            s, e = None, (즉.text or "").strip()[:10]
        else:
            ss, ee = p.find("{%s}startDate" % X._XBRLI), p.find("{%s}endDate" % X._XBRLI)
            if ss is None or ee is None:
                continue
            s, e = (ss.text or "").strip()[:10], (ee.text or "").strip()[:10]
        차원 = {}
        for m in c.iter("{%s}explicitMember" % X._XBRLDI):
            차원[_큐네임(m.get("dimension"), 표, 거꾸로)] = _큐네임(m.text, 표, 거꾸로)
        형식차원 = any(True for _ in c.iter("{%s}typedMember" % X._XBRLDI))
        맥락[c.get("id")] = {"시작": s, "끝": e, "차원": 차원, "형식차원": 형식차원}
    for u in 뿌리.findall("{%s}unit" % X._XBRLI):
        단위[u.get("id")] = X._단위글(u)
    사실, dei, 본 = [], {}, set()
    for el in 뿌리:
        if not isinstance(el.tag, str) or not el.tag.startswith("{") or el.get("contextRef") is None:
            continue
        uri, 태그 = el.tag[1:].split("}", 1)
        ns = _짧은이름(uri, 거꾸로)
        글 = (el.text or "").strip()
        if ns == "dei":
            if 글 and not (맥락.get(el.get("contextRef")) or {}).get("차원"):
                dei.setdefault(태그, 글)
            continue
        if uri in (X._XBRLI, X._XBRLDI, _LINK, _XL) or el.get("unitRef") is None:
            continue
        if el.get("{http://www.w3.org/2001/XMLSchema-instance}nil") == "true":
            continue
        try:
            v = float(글)
        except ValueError:
            continue
        if v.is_integer() and abs(v) < 1e18:
            v = int(v)
        열쇠 = (ns, 태그, el.get("contextRef"), v)
        if 열쇠 in 본:
            continue
        본.add(열쇠)
        d = el.get("decimals")
        사실.append({"개념": "%s:%s" % (ns, 태그), "표준": ns in 표준, "맥락": el.get("contextRef"),
                   "단위": 단위.get(el.get("unitRef")) or el.get("unitRef"), "값": v,
                   "decimals": (int(d) if d and re.fullmatch(r"-?\d+", d) else d)})
    return {"맥락": 맥락, "사실": 사실, "dei": dei}


def 라벨파싱(내용):
    """라벨 링크베이스(바이트) → {요소 id(「spcx_SpaceMember」): 표시 이름}. 역할 label > terseLabel > 그 밖 · 영어 먼저."""
    try:
        뿌리 = ET.fromstring(내용)
    except ET.ParseError:
        return {}
    차례 = {"http://www.xbrl.org/2003/role/label": 0, "http://www.xbrl.org/2003/role/terseLabel": 1}
    고른 = {}
    for lk in 뿌리.iter("{%s}labelLink" % _LINK):
        loc = {l.get("{%s}label" % _XL): (l.get("{%s}href" % _XL) or "").split("#")[-1] for l in lk.findall("{%s}loc" % _LINK)}
        자원 = {}
        for lab in lk.findall("{%s}label" % _LINK):
            자원.setdefault(lab.get("{%s}label" % _XL), []).append(
                (lab.get("{%s}role" % _XL), (lab.text or "").strip(), (lab.get("{http://www.w3.org/XML/1998/namespace}lang") or "")))
        for arc in lk.findall("{%s}labelArc" % _LINK):
            요소 = loc.get(arc.get("{%s}from" % _XL))
            if not 요소:
                continue
            for 역할, 글, 말 in 자원.get(arc.get("{%s}to" % _XL)) or []:
                if not 글:
                    continue
                점 = (차례.get(역할, 5), 0 if 말.lower().startswith("en") else 1)
                if 요소 not in 고른 or 점 < 고른[요소][0]:
                    고른[요소] = (점, 글)
    return {k: v[1] for k, v in 고른.items()}


def 표시이름(멤버, 라벨):
    """멤버 QName → 라벨의 표시 이름(「[Member]」 꼬리를 걷는다) | None."""
    p, _, 이름 = 멤버.partition(":")
    글 = 라벨.get("%s_%s" % (p, 이름)) or next((v for k, v in 라벨.items() if k.split("_", 1)[-1] == 이름), None)
    return re.sub(r"\s*\[(Member|Domain)\]\s*$", "", 글).strip() if 글 else None


# ══════════════════════════════════════════════════════════ 부문 사실 고르기

def _이름(q):
    return q.split(":", 1)[-1]


def _부문축인가(축):
    ns, 이름 = (축.split(":", 1) + [""])[:2] if ":" in 축 else ("", 축)
    return ns in 표준 and bool(부문축꼴.match(이름))


def _통합축인가(축):
    ns, 이름 = (축.split(":", 1) + [""])[:2] if ":" in 축 else ("", 축)
    return ns in 표준 and bool(통합축꼴.match(이름))


def 멤버종류(멤버):
    이름 = _이름(멤버)
    if 합계멤버꼴.match(이름) and 멤버.split(":", 1)[0] in 표준:
        return "합계"
    if 조정멤버꼴.search(이름):
        return "조정"
    if 기타멤버꼴.search(이름):
        return "기타"
    return "보고부문"


def 맥락꼴(차원):
    """차원 {축: 멤버} → (꼴, 축, 멤버). 꼴: 비차원 · 부문 · 부문합 · 축밖조정 · 부문안분해 · 무관."""
    if not 차원:
        return "비차원", None, None
    부 = [(a, m) for a, m in 차원.items() if _부문축인가(a)]
    통 = [(a, m) for a, m in 차원.items() if _통합축인가(a)]
    남 = [a for a in 차원 if not _부문축인가(a) and not _통합축인가(a)]
    if len(부) == 1 and not 남 and (not 통 or (len(통) == 1 and 영업부문멤버꼴.match(_이름(통[0][1])))):
        return "부문", 부[0][0], 부[0][1]
    if 부:
        return "부문안분해", 부[0][0], 부[0][1]
    if len(통) == 1 and not 남:
        return ("부문합" if 영업부문멤버꼴.match(_이름(통[0][1])) else "축밖조정"), 통[0][0], 통[0][1]
    return "무관", None, None


def _후보차례(개념, 후보):
    이름 = _이름(개념)
    if 개념.split(":", 1)[0] in 표준 and 이름 in 후보:
        return 후보.index(이름)
    if "(확장)" in 후보 and 개념.split(":", 1)[0] not in 표준 and 확장손익꼴.search(이름) and not 확장제외꼴.search(이름):
        return 후보.index("(확장)")
    return None


def _돈단위(단위):
    return bool(단위) and "/" not in 단위 and 단위.lower() not in ("shares", "pure")


def 한공시(파싱결과, 서류, 연말, 라벨=None):
    """한 공시의 파싱 결과 → {사실[], 검산[], 개념고름{}, 멤버{}, 축{}, 걸러냄{}, 경보[]}."""
    라벨 = 라벨 or {}
    맥 = 파싱결과["맥락"]
    축수, 걸러냄, 경보, 확장축 = {}, {"부문안분해": 0, "형식차원": 0, "시점": 0, "돈 아닌 단위": 0}, [], {}
    부문사실, 합사실, 조정사실, 비차원 = [], [], [], {}
    for x in 파싱결과["사실"]:
        c = 맥.get(x["맥락"])
        if not c:
            continue
        for a in c["차원"]:
            if a.split(":", 1)[0] not in 표준 and "Segment" in a:
                확장축[a] = 확장축.get(a, 0) + 1
        꼴, 축, 멤버 = 맥락꼴(c["차원"])
        if 꼴 == "무관":
            continue
        if c["형식차원"]:
            걸러냄["형식차원"] += 1
            continue
        if c["시작"] is None:
            if 꼴 != "비차원":
                걸러냄["시점"] += 1
            continue
        if not _돈단위(x["단위"]):
            if 꼴 != "비차원":
                걸러냄["돈 아닌 단위"] += 1
            continue
        기 = 기간정보(c["시작"], c["끝"], 연말)
        if not 기:
            continue
        한 = dict(x, 시작=c["시작"], 끝=c["끝"], 기간=기, 축=축, 멤버=멤버)
        if 꼴 == "비차원":
            비차원.setdefault((x["개념"], c["시작"], c["끝"], x["단위"]), x["값"])
        elif 꼴 == "부문":
            축수[축] = 축수.get(축, 0) + 1
            부문사실.append(한)
        elif 꼴 == "부문안분해":
            걸러냄["부문안분해"] += 1
        elif 꼴 == "부문합":
            합사실.append(한)
        elif 꼴 == "축밖조정":
            조정사실.append(한)
    if 확장축:
        경보.append("확장 부문 축 후보(쓰지 않음): %s" % " · ".join("%s %d" % kv for kv in sorted(확장축.items())))

    # 같은 (개념 · 축 · 멤버 · 기간 · 단위) 가 두 맥락 꼴(부문만 · 부문 + 영업부문)로 오면 하나로. 값이 다르면 경보
    묶 = {}
    for x in 부문사실:
        k = (x["개념"], x["축"], x["멤버"], x["시작"], x["끝"], x["단위"])
        if k in 묶 and 묶[k]["값"] != x["값"]:
            경보.append("같은 부문 사실이 두 값 — %s %s %s~%s : %s · %s(앞의 것을 씀)" % (x["개념"], x["멤버"], x["시작"], x["끝"], 묶[k]["값"], x["값"]))
            continue
        묶.setdefault(k, x)
    부문사실 = list(묶.values())

    def 총액(개념, s, e, 단위):
        v = 비차원.get((개념, s, e, 단위))
        if v is not None:
            return v, 개념
        for 후 in 매출후보:
            for ns in ("us-gaap", "ifrs-full"):
                v = 비차원.get(("%s:%s" % (ns, 후), s, e, 단위))
                if v is not None:
                    return v, "%s:%s" % (ns, 후)
        return None, None

    def 검산(종류, 개념):
        낸 = []
        기간들 = sorted({(x["시작"], x["끝"], x["단위"]) for x in 부문사실 if x["개념"] == 개념})
        for s, e, 단위 in 기간들:
            줄 = [x for x in 부문사실 if x["개념"] == 개념 and (x["시작"], x["끝"], x["단위"]) == (s, e, 단위)]
            보 = [x for x in 줄 if 멤버종류(x["멤버"]) == "보고부문"]
            기 = [x for x in 줄 if 멤버종류(x["멤버"]) == "기타"]
            축조 = [x for x in 줄 if 멤버종류(x["멤버"]) == "조정"]
            합멤 = [x for x in 줄 if 멤버종류(x["멤버"]) == "합계"]
            밖 = [x for x in 조정사실 if x["개념"] == 개념 and (x["시작"], x["끝"], x["단위"]) == (s, e, 단위)]
            공시합 = next((x["값"] for x in 합사실 if x["개념"] == 개념 and (x["시작"], x["끝"], x["단위"]) == (s, e, 단위)), None)
            if 공시합 is None and 합멤:
                공시합 = 합멤[0]["값"]
            보합 = sum(x["값"] for x in 보)
            전합 = 보합 + sum(x["값"] for x in 기) + sum(x["값"] for x in 축조) + sum(x["값"] for x in 밖)
            if 종류 == "손익":
                총, 총개념 = 비차원.get((개념, s, e, 단위)), (개념 if 비차원.get((개념, s, e, 단위)) is not None else None)
            else:
                총, 총개념 = 총액(개념, s, e, 단위)
            소수 = [x.get("decimals") for x in 줄 + 밖 if isinstance(x.get("decimals"), int)]
            허용 = float(10 ** (-min(소수))) if 소수 else 1.0           # 공시 정밀도 한 눈금(decimals −6 → 백만) — 신고서재무 「백만 단위 반올림 1」 과 같은 자
            if 총 is None:
                판정, 차, 차보 = "총액 없음", None, None
            else:
                차보, 차 = 총 - 보합, 총 - 전합
                if abs(차보) <= 허용:
                    판정 = "맞음"
                elif abs(차) <= 허용:
                    판정 = "맞음(조정 포함)"
                else:
                    판정 = "어긋남" if 종류 == "매출" else "참고(부문 손익 합 ≠ 연결 — 미배분 · 조정)"
                # 총액을 다른 매출 개념에서 왔으면(부문 = 고객과의 계약 매출 · 총 = 전체 매출) 계약 외 매출(비차원)이 차를 메우는지 본다 — 실측: 전사 수준 헤지 손익
                if 판정 == "어긋남" and 총개념 and 총개념 != 개념:
                    for 덧 in ("us-gaap:RevenueNotFromContractWithCustomer",):
                        v = 비차원.get((덧, s, e, 단위))
                        if v is not None and abs(차 - v) <= 허용:
                            판정 = "맞음(총 개념 차 — %s %s)" % (덧, "{:,.0f}".format(v))
                            break
            기간 = 보[0]["기간"] if 보 else 줄[0]["기간"]
            낸.append({"종류": 종류, "개념": 개념, "기간id": 기간["id"], "시작": s, "끝": e, "단위": 단위, "접수번호": 서류["접수번호"], "양식": 서류["양식"],
                      "보고부문수": len(보), "보고부문합": 보합, "기타합": sum(x["값"] for x in 기), "부문축조정합": sum(x["값"] for x in 축조),
                      "축밖조정": [{"멤버": x["멤버"], "값": x["값"]} for x in 밖], "부문합공시": 공시합,
                      "총": 총, "총개념": 총개념, "차": 차, "차_보고부문": 차보, "허용": 허용, "판정": 판정})
        return 낸

    # 개념 고르기 — 보고부문 × 기간 덮음 → 검산 통과 → 후보 차례
    고름, 검산들, 쓴개념 = {}, [], {}
    for 종류, 후보 in (("매출", 매출후보), ("손익", 손익후보)):
        점수 = {}
        for x in 부문사실:
            차 = _후보차례(x["개념"], 후보)
            if 차 is None or 멤버종류(x["멤버"]) != "보고부문":
                continue
            점수.setdefault(x["개념"], {"차례": 차, "덮음": set()})["덮음"].add((x["멤버"], x["시작"], x["끝"]))
        if not 점수:
            고름[종류] = {"고른것": None, "후보": {}, "까닭": "부문 축에 %s 후보 개념이 없다" % 종류}
            continue
        통과수 = {}
        for 개 in 점수:
            통과수[개] = sum(1 for z in 검산(종류, 개) if z["판정"].startswith("맞음"))
        차례 = sorted(점수, key=lambda k: (-len(점수[k]["덮음"]), -통과수[k], 점수[k]["차례"]))
        고른 = 차례[0]
        고름[종류] = {"고른것": 고른, "후보": {k: {"덮음": len(점수[k]["덮음"]), "검산맞음": 통과수[k]} for k in 차례},
                    "까닭": "보고부문 × 기간 덮음 %d · 검산 맞음 %d · 후보 차례 %d%s" % (
                        len(점수[고른]["덮음"]), 통과수[고른], 점수[고른]["차례"] + 1, "" if 고른.split(":", 1)[0] in 표준 else " · 회사 확장 개념")}
        쓴개념[종류] = 고른
        검산들 += 검산(종류, 고른)

    낸사실, 멤버 = [], {}
    for 종류, 개념 in 쓴개념.items():
        for x in sorted((y for y in 부문사실 if y["개념"] == 개념), key=lambda y: (y["멤버"], y["시작"], y["끝"])):
            멤버.setdefault(x["멤버"], {"멤버": x["멤버"], "이름": 표시이름(x["멤버"], 라벨), "종류": 멤버종류(x["멤버"]), "축": x["축"]})
            낸사실.append({"종류": 종류, "개념": 개념, "축": x["축"], "멤버": x["멤버"], "이름": 멤버[x["멤버"]]["이름"],
                         "시작": x["시작"], "끝": x["끝"], "기간id": x["기간"]["id"], "기간종류": x["기간"]["종류"], "개월": x["기간"]["개월"],
                         "값": x["값"], "단위": x["단위"], "decimals": x.get("decimals"),
                         "접수번호": 서류["접수번호"], "양식": 서류["양식"], "접수일": 서류["접수일"]})
    return {"사실": 낸사실, "검산": 검산들, "개념고름": 고름, "멤버": 멤버, "축": 축수, "걸러냄": 걸러냄, "경보": 경보,
            "부문축개념수": len({x["개념"] for x in 부문사실})}


# ══════════════════════════════════════════════════════════ 받기 · 고르기

def 라벨받기(인스턴스주소, 곳, 접수번호):
    """인스턴스 주소(`…_htm.xml` · `….xml`) 곁의 라벨 링크베이스(`…_lab.xml`)를 받는다 → (경로 | None, 주소 | None)."""
    import requests                                  # noqa: PLC0415
    if not 인스턴스주소 or not 인스턴스주소.lower().endswith(".xml"):
        return None, None
    주소 = re.sub(r"(?i)(_htm)?\.xml$", "_lab.xml", 인스턴스주소)
    time.sleep(0.25)
    r = requests.get(주소, headers=X._머리(), timeout=120)
    if r.status_code != 200:
        return None, None
    p = os.path.join(곳, "%s_lab.xml" % 접수번호)
    with open(p, "wb") as f:
        f.write(r.content)
    time.sleep(0.2)
    return p, 주소


def 공시고르기(sub, 기준일=None, 최대=4):
    """submissions → 고를 공시 [{접수번호, 양식, 접수일, 기간끝, 문서, 기준일과}] — 기간 끝 ≤ 기준일 + 7일 · XBRL 있음 · 가장 늦은 연차 하나 + 그 뒤 분기(늦은 것부터)."""
    r = ((sub or {}).get("filings") or {}).get("recent") or {}
    한 = (_날(기준일) + datetime.timedelta(days=7)) if 기준일 else None
    줄 = []
    for i, 양식 in enumerate(r.get("form") or []):
        if 양식 not in 고를양식:
            continue
        if not (r.get("isXBRL") or [0] * (i + 1))[i]:
            continue
        끝 = (r.get("reportDate") or [""] * (i + 1))[i] or ""
        if not _날(끝) or (한 and _날(끝) > 한):
            continue
        줄.append({"접수번호": r["accessionNumber"][i], "양식": 양식, "접수일": r["filingDate"][i], "기간끝": 끝,
                  "문서": (r.get("primaryDocument") or [""] * (i + 1))[i]})
    # 같은 기간 끝의 고침 판(/A)은 원판이 있으면 뺀다
    원판 = {(x["기간끝"], x["양식"].replace("/A", "")) for x in 줄 if not x["양식"].endswith("/A")}
    줄 = [x for x in 줄 if not (x["양식"].endswith("/A") and (x["기간끝"], x["양식"].replace("/A", "")) in 원판)]
    줄.sort(key=lambda x: (x["기간끝"], x["접수일"]), reverse=True)
    연 = next((x for x in 줄 if x["양식"] in 연차양식), None)
    분 = [x for x in 줄 if x["양식"] in 분기양식 and (not 연 or x["기간끝"] > 연["기간끝"])]
    낸 = 분[:max(0, 최대 - (1 if 연 else 0))] + ([연] if 연 else [])
    for j, x in enumerate(낸):
        x["기준일과"] = "연차" if x is 연 else ("기준일분기" if j == 0 else "이전")
    return 낸


def _조회(cik):
    import requests                                  # noqa: PLC0415
    r = requests.get("https://data.sec.gov/submissions/CIK%010d.json" % int(cik), headers=X._머리(), timeout=60)
    r.raise_for_status()
    time.sleep(0.2)
    return r.json()


# ══════════════════════════════════════════════════════════ 모으기

def 값표짓기(사실):
    """[사실] → {종류: {멤버: {기간id: {값 · 시작 · 끝 · 개념 · 단위 · 접수번호 · 양식 · 접수일 · 이전값?}}}} — 같은 칸은 접수일이 늦은 공시."""
    낸 = {}
    for x in sorted(사실, key=lambda y: (y["접수일"] or "", y["접수번호"])):
        칸 = 낸.setdefault(x["종류"], {}).setdefault(x["멤버"], {})
        새 = {k: x[k] for k in ("값", "시작", "끝", "개월", "기간종류", "개념", "단위", "접수번호", "양식", "접수일")}
        옛 = 칸.get(x["기간id"])
        if 옛 and (옛["시작"], 옛["끝"]) == (x["시작"], x["끝"]):
            이전 = list(옛.get("이전값") or [])
            if 옛["값"] != x["값"]:
                이전.append({"값": 옛["값"], "접수번호": 옛["접수번호"], "양식": 옛["양식"], "접수일": 옛["접수일"]})
            if 이전:
                새["이전값"] = 이전
        칸[x["기간id"]] = 새
    return 낸


def 모으기(공시들, 회사=None, 식별=None, 기준일=None, 조회일=None, 있던=None):
    """[(서류, 파싱결과, 라벨)] → 「부문매출/1」 dict. `있던` 을 주면 그 파일의 다른 접수번호 사실 · 검산 · 서류를 남긴다."""
    조회일 = 조회일 or datetime.date.today().isoformat()
    서류들, 사실, 검산, 고름, 멤버, 축, 경보, 확인불가 = [], [], [], {}, {}, {}, [], []
    새접수 = {s["접수번호"] for s, _p, _l in 공시들}
    if 있던:
        for s in 있던.get("서류") or []:
            if s.get("접수번호") not in 새접수:
                서류들.append(s)
        사실 += [x for x in 있던.get("사실") or [] if x.get("접수번호") not in 새접수]
        검산 += [x for x in 있던.get("검산") or [] if x.get("접수번호") not in 새접수]
        for m in 있던.get("멤버") or []:
            멤버.setdefault(m["멤버"], m)
        고름.update({k: v for k, v in (있던.get("개념고름") or {}).items() if k not in 새접수})
    for 서류, 파, 라벨 in 공시들:
        연말 = 연말읽기(파["dei"].get("CurrentFiscalYearEndDate")) or 서류.get("연말") or (12, 31)
        한 = 한공시(파, 서류, 연말, 라벨)
        서류 = dict(서류, 사실수=len(한["사실"]), 부문축개념수=한["부문축개념수"], 걸러냄=한["걸러냄"], 축=한["축"], 조회일=조회일,
                  연말="--%02d-%02d" % 연말, dei={k: 파["dei"].get(k) for k in ("DocumentType", "DocumentPeriodEndDate", "DocumentFiscalYearFocus",
                                                                       "DocumentFiscalPeriodFocus", "EntityRegistrantName") if 파["dei"].get(k)})
        서류.pop("파일", None)
        서류들.append(서류)
        사실 += 한["사실"]
        검산 += 한["검산"]
        고름[서류["접수번호"]] = 한["개념고름"]
        for k, v in 한["멤버"].items():
            if k not in 멤버 or (not 멤버[k].get("이름") and v.get("이름")):
                멤버[k] = v
        for a, n in 한["축"].items():
            축[a] = 축.get(a, 0) + n
        경보 += ["%s %s — %s" % (서류["양식"], 서류["접수번호"], g) for g in 한["경보"]]
        if not 한["사실"]:
            확인불가.append({"항목": "부문 사실", "원인": "항목 부재", "대안": "%s %s 인스턴스에 표준 부문 축(…SegmentsAxis)의 매출 · 손익 사실이 없다 — 부문이 하나이거나 "
                                                         "회사 확장 축을 쓴다(경보의 확장 부문 축 후보) · 원문 Segments 주석 확인" % (서류["양식"], 서류["접수번호"])})
        for z in 한["검산"]:
            if z["판정"] == "어긋남":
                경보.append("%s %s %s %s — 부문 매출 합 %s 대 총매출 %s(차 %s)" % (서류["양식"], 서류["접수번호"], z["기간id"], z["개념"],
                                                                    "{:,.0f}".format(z["보고부문합"]), "{:,.0f}".format(z["총"]), "{:,.0f}".format(z["차"])))
    통화들 = sorted({x["단위"] for x in 사실})
    기간 = {}
    for x in 사실:
        기간.setdefault(x["기간id"], {"id": x["기간id"], "시작": x["시작"], "끝": x["끝"], "개월": x["개월"], "종류": x["기간종류"]})
    return {"형식": 형식, "도구": 도구표지, "회사": 회사, "식별": 식별 or {}, "기준일": 기준일, "조회일": 조회일,
            "통화": 통화들[0] if len(통화들) == 1 else (통화들 or None), "단위": "공시 값 그대로(원 단위 · 부호 그대로) — 13번으로 옮길 때 메타.환산배율로 나눈다",
            "서류": 서류들, "축": [{"축": a, "사실수": n} for a, n in sorted(축.items(), key=lambda t: -t[1])],
            "개념고름": 고름, "멤버": sorted(멤버.values(), key=lambda m: ({"보고부문": 0, "기타": 1, "조정": 2, "합계": 3}[m["종류"]], m["멤버"])),
            "기간": sorted(기간.values(), key=lambda p: (p["끝"], -p["개월"])),
            "사실": 사실, "값표": 값표짓기(사실), "검산": 검산, "경보": 경보, "확인불가": 확인불가}


def 종료(낸, 실패=0):
    if 실패 or not 낸["사실"] or any(z["판정"] == "어긋남" for z in 낸["검산"]):
        return 발견
    return 통과


def 화면(낸):
    print("부문매출 %s — 서류 %d · 멤버 %d · 사실 %d · 검산 %d(어긋남 %d) · 경보 %d · 확인불가 %d" % (
        낸.get("회사") or "-", len(낸["서류"]), len(낸["멤버"]), len(낸["사실"]), len(낸["검산"]),
        sum(1 for z in 낸["검산"] if z["판정"] == "어긋남"), len(낸["경보"]), len(낸["확인불가"])))
    for a in 낸["축"]:
        print("  축 %s — 사실 %d" % (a["축"], a["사실수"]))
    for 접, g in 낸["개념고름"].items():
        for 종류, v in g.items():
            print("  개념 %s %s → %s (%s)" % (접, 종류, v.get("고른것"), v.get("까닭")))
    for m in 낸["멤버"]:
        print("  멤버 %-45s %-8s %s" % (m["멤버"], m["종류"], m.get("이름") or ""))
    for z in 낸["검산"]:
        if z["종류"] == "매출" or z["판정"] != "맞음":
            print("  검산 %s %-6s %-6s 부문 %s · 총 %s · 차 %s → %s" % (z["접수번호"], z["종류"], z["기간id"], "{:,.0f}".format(z["보고부문합"]),
                                                              "-" if z["총"] is None else "{:,.0f}".format(z["총"]),
                                                              "-" if z["차"] is None else "{:,.0f}".format(z["차"]), z["판정"]))
    for g in 낸["경보"][:20]:
        print("  경보 %s" % g)


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="정기 공시 XBRL 인스턴스의 부문 축 차원 사실 → _raw/부문매출.json(「부문매출/1」)")
    ap.add_argument("--raw", default=os.path.join(ROOT, "_raw"))
    ap.add_argument("-o", "--출력", default=None, help="기본 <raw>/부문매출.json")
    ap.add_argument("--기준일", default=None, help="이 날 + 7일까지 기간이 끝난 공시만(기본: sec_공시고르기.json 의 기준일)")
    ap.add_argument("--최대", type=int, default=4)
    ap.add_argument("--cik", default=None)
    ap.add_argument("--접수번호", action="append", default=[])
    ap.add_argument("--인스턴스", help="받아 둔 인스턴스(네트워크 0) — --접수번호 하나 · --양식 · --접수일 과 함께")
    ap.add_argument("--라벨", help="받아 둔 라벨 링크베이스(선택)")
    ap.add_argument("--양식")
    ap.add_argument("--접수일")
    ap.add_argument("--다시받기", action="store_true", help="받아 둔 인스턴스가 있어도 다시 받는다")
    ap.add_argument("--보태기", action="store_true", help="있던 부문매출.json 의 다른 공시를 남긴다")
    a = ap.parse_args(argv)
    출력 = a.출력 or os.path.join(a.raw, "부문매출.json")
    for 곳 in (a.raw, os.path.dirname(os.path.abspath(출력))):        # 본체(정본 키트)의 _raw 에 회차 원본을 쌓지 않는다 — sec_fetch 와 같은 가드
        if os.path.abspath(곳).startswith(os.path.abspath(ROOT) + os.sep) or os.path.abspath(곳) == os.path.abspath(ROOT):
            import 본체가드                                  # noqa: PLC0415
            본체가드.본체면멈춘다(ROOT)
            break

    def 읽기(p):
        try:
            return json.load(io.open(p, encoding="utf-8"))
        except (OSError, ValueError):
            return None
    sub = 읽기(os.path.join(a.raw, "submissions.json"))
    고르기기록 = 읽기(os.path.join(a.raw, "sec_공시고르기.json")) or {}
    기준일 = a.기준일 or 고르기기록.get("기준일")
    cik = a.cik or (sub or {}).get("cik") or 고르기기록.get("CIK")
    공시들, 실패 = [], 0
    if a.인스턴스:
        if len(a.접수번호) != 1 or not (a.양식 and a.접수일):
            print("--인스턴스 에는 --접수번호 하나 · --양식 · --접수일 을 함께 준다")
            return 입력오류
        try:
            파 = 차원파싱(open(a.인스턴스, "rb").read())
        except (OSError, ET.ParseError) as e:
            print("인스턴스를 못 읽었다 — %s: %s" % (type(e).__name__, e))
            return 입력오류
        라벨 = 라벨파싱(open(a.라벨, "rb").read()) if a.라벨 and os.path.exists(a.라벨) else {}
        공시들.append(({"접수번호": a.접수번호[0], "양식": a.양식, "접수일": a.접수일, "기간끝": 파["dei"].get("DocumentPeriodEndDate"),
                      "인스턴스": "(받아 둔 파일) %s" % os.path.basename(a.인스턴스),
                      "라벨": ("(받아 둔 파일) %s" % os.path.basename(a.라벨)) if 라벨 else None}, 파, 라벨))
    else:
        if not cik:
            print("CIK 를 모른다 — --cik 를 주거나 sec_fetch 로 _raw/submissions.json 을 먼저")
            return 입력오류
        if a.접수번호:
            if sub is None:
                try:
                    sub = _조회(cik)
                except Exception as e:                   # noqa: BLE001
                    print("submissions 를 못 받았다 — %s(양식 · 접수일은 인스턴스 표지에서)" % type(e).__name__)
                    sub = {}
            r = ((sub or {}).get("filings") or {}).get("recent") or {}
            색 = {acc: i for i, acc in enumerate(r.get("accessionNumber") or [])}
            할일 = []
            for acc in a.접수번호:
                i = 색.get(acc)
                할일.append({"접수번호": acc, "양식": r["form"][i] if i is not None else None, "접수일": r["filingDate"][i] if i is not None else None,
                           "기간끝": (r.get("reportDate") or [None] * (i + 1))[i] if i is not None else None, "기준일과": "지정"})
        else:
            if sub is None:
                print("_raw/submissions.json 이 없다 — sec_fetch 를 먼저 하거나 --cik · --접수번호 를 준다")
                return 입력오류
            할일 = 공시고르기(sub, 기준일, a.최대)
            if not 할일:
                print("고를 XBRL 정기 공시가 없다(기준일 %s)" % (기준일 or "-"))
                return 발견
        곳 = os.path.join(a.raw, "xbrl")
        os.makedirs(곳, exist_ok=True)
        for x in 할일:
            try:
                p = os.path.join(곳, "%s.xml" % x["접수번호"])
                lp = os.path.join(곳, "%s_lab.xml" % x["접수번호"])
                if os.path.exists(p) and not a.다시받기:
                    주소 = "(받아 둔 파일) xbrl/%s" % os.path.basename(p)
                    라주소 = ("(받아 둔 파일) xbrl/%s" % os.path.basename(lp)) if os.path.exists(lp) else None
                else:
                    p, 주소 = X.받기(cik, x["접수번호"], 곳)
                    lp, 라주소 = 라벨받기(주소, 곳, x["접수번호"])
                파 = 차원파싱(open(p, "rb").read())
                라벨 = 라벨파싱(open(lp, "rb").read()) if lp and os.path.exists(lp) else {}
                x = dict(x, 양식=x.get("양식") or 파["dei"].get("DocumentType"), 접수일=x.get("접수일") or a.접수일,
                         기간끝=x.get("기간끝") or 파["dei"].get("DocumentPeriodEndDate"), 인스턴스=주소, 라벨=라주소,
                         연말=연말읽기((sub or {}).get("fiscalYearEnd")))
                공시들.append((x, 파, 라벨))
                print("읽음: %s %s(접수 %s · 기간 끝 %s) — 맥락 %d · 사실 %d · 라벨 %d" % (x["양식"], x["접수번호"], x["접수일"], x["기간끝"],
                                                                         len(파["맥락"]), len(파["사실"]), len(라벨)))
            except Exception as e:                       # noqa: BLE001
                실패 += 1
                print("받지 못함: %s %s — %s: %s" % (x.get("양식"), x["접수번호"], type(e).__name__, str(e)[:160]))
    if not 공시들:
        return 발견
    회사 = (sub or {}).get("name") or next((p["dei"].get("EntityRegistrantName") for _s, p, _l in 공시들 if p["dei"].get("EntityRegistrantName")), None)
    식별 = {"CIK": ("%010d" % int(cik)) if cik and ("%s" % cik).isdigit() else cik, "티커": ((sub or {}).get("tickers") or [None])[0]}
    있던 = 읽기(출력) if a.보태기 else None
    낸 = 모으기(공시들, 회사, 식별, 기준일, 있던=있던 if isinstance(있던, dict) and 있던.get("형식") == 형식 else None)
    os.makedirs(os.path.dirname(os.path.abspath(출력)), exist_ok=True)
    io.open(출력, "w", encoding="utf-8").write(json.dumps(낸, ensure_ascii=False, indent=1))
    화면(낸)
    print("저장: %s" % 출력)
    return 종료(낸, 실패)


if __name__ == "__main__":
    sys.exit(main())

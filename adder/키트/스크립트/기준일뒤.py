# -*- coding: utf-8 -*-
"""기준일뒤 — 조사 산출의 출처가 **평가기준일 뒤 정보**인지 가려 표지를 단다(2026-10-24 W18 · 유니버스 조사 물결 실측).

왜 있는가
    조사 지시 「평가기준일을 지킨다」 — 근거 범위의 첫 출처는 평가기준일까지의 기간을 담은 공시이고, 기준일 뒤 기간의 공시 · 실적발표 · 콜과
    기준일 뒤에 나온 보도 · 리포트는 버리지 않되 `기준일뒤: true` 를 달아 「평가기준일 뒤 정보」(부록 G 재료)로 둔다 — 축의 근거 범위에 섞지 않는다.
    규칙이 생기기 전에 쌓인 조사(한 회사는 기준일 뒤 분기의 10-Q 를 축 근거 범위의 첫 출처로 썼다)는 표지가 없었다.

판정(값을 보기 전에 정한 규칙 — 출처 글을 「 · 」 · 「;」 로 조각내 조각마다)
    ① 기간 표지가 있으면 기간으로 — 분기(「3Q26」 · 「Q3 2026」 · 「2026년 3분기」 · 「2026 3분기」 · 「FY26 Q3」 — 달력 분기로 근사) ·
       반기(「1H26」 · 「2026년 상반기」) · 공시 이름 뒤 날짜(「10-Q 2026-09-30」 · 「반기보고서(2026.06)」). 기간 끝이 기준일 뒤면 「뒤」.
       회사 정기 공시 · 실적발표 · 콜은 **기간**이 정한다 — 기준일까지의 기간을 담은 반기보고서 · 2분기 콜은 기준일 뒤에 나와도 「안」.
    ② 기간 표지가 없으면 공표일로 — 온전한 날짜(YYYY-MM-DD · YYYY.MM.DD · YYYY년 M월 D일)가 기준일 뒤 · 조사일 이하면 「뒤」. 조사일보다 늦은
       날짜는 공표일이 될 수 없어(목표 · 전망 시점) 세지 않는다.
    ③ 조각마다 뒤 · 안 · 모름 → 출처 전체는 전부 뒤면 「뒤」, 뒤와 안이 섞이면 「섞임」, 뒤가 없으면 「안」 또는 「모름」.
표지
    · 출처 항목(출처 · url · 발행일 따위 칸을 가진 잎 사전) — 「뒤」 면 `기준일뒤: true` · `기준일뒤_사유` (지우지 않는다). 이미 표지가 있으면 그대로
    · 축(`scenario_axes[]`)의 `근거범위` — 출처가 「뒤」 면 `근거범위_기준일뒤` 로 옮기고 `근거범위` 를 비운다(빈 축 경보로 이어진다) ·
      「섞임」 이면 옮기지 않고 `근거범위_기준일뒤섞임` 경보(사람이 기준일 안 출처만으로 다시 잡는다) · `근거범위_밴드` 의 「뒤」 표현은
      `근거범위_밴드_기준일뒤` 로 옮긴다

날짜 둘(2026-10-25 결정 — 평가기준일 T = 분석일 · 재무기준일 F = T 전에 제출된 마지막 정기보고서의 기간 끝)
    경계는 **평가기준일 T** 다. 「뒤」 는 T 뒤에 처음 생긴 것만이다. 재무기준일을 주면(`재무기준일=` — `기준일.py` 가 푼 F) 세 칸으로 가른다.
      · 「뒤」   기간 끝 > T · 공표일 > T. 기간 끝이 (F, T] 이어도 공표가 T 뒤면 「뒤」 — 그날 시장이 알 수 없던 정보다.
                (F, T] 기간의 **정기보고서**(10-Q · 분기보고서 …)는 재무기준일의 정의상 T 뒤 제출이라 「뒤」 다. 글에 T 이하 제출일이 보이면 「사이」 로
                두고 「재무기준일을 그 기간 끝으로 옮길 후보」 를 사유에 적는다(`기준일.py` 경보와 같은 결)
      · 「사이」 기간 끝 · 공표일이 (F, T] — **쓴다.** 첫 예측 열 추정의 근거(잠정실적 · 가이던스 · 새 계약 · 가격 동향)와 이월 다리의 자본거래다.
                잠정실적은 검토 전 숫자라 실적 열에 넣지 않는다. 출처 항목에 `기준일사이: true` · `기준일사이_사유` 를 단다. 축 근거 범위는 옮기지 않는다
      · 「안」   기간 끝 · 공표일 ≤ F. 기간 끝이 F 이하인 정기보고서는 지금처럼 기간이 정한다(실적)
    재무기준일이 없거나 T 와 같으면 「사이」 는 생기지 않고 판정 · 표지 · 셈이 날짜 둘 전과 글자까지 같다(옛 가정 · 옛 회차).
    **옛 경계의 자동 표지를 다시 본다** — 재무기준일이 T 보다 이르면, T 보다 이른 경계(옛 평가기준일 = 재무 분기말)로 단 자동 표지(`…(자동 표지 — 기준일뒤.py)`)와
    그 표지로 옮긴 근거 범위 · 밴드를 T 로 다시 판정해 「뒤」 가 아니면 거두고(`기준일뒤_거둠`) 근거 범위를 되돌린다(`근거범위_거둠`). 사람이 단 표지는 그대로.
회사 · 업종 이름은 이 도구에 없다(범용).
"""
from __future__ import annotations

import calendar
import datetime
import re

출처칸 = ("출처", "source", "url", "URL", "링크", "발행처", "리포트", "문서", "원문접수", "accession", "발행일", "공표일", "발표일",
        "게재일", "제출일", "filed", "published", "날짜", "date")
식별칸 = 출처칸 + ("무엇", "제목", "title", "자료", "이름", "기간", "분기", "period", "콜", "행사", "출처_성격")
공표칸 = ("발행일", "공표일", "발표일", "게재일", "제출일", "filed", "published", "날짜", "date")

_분기꼴 = [
    (re.compile(r"(?<![A-Za-z0-9])([1-4])\s?Q\s?'?(\d{2})(?!\d)", re.I), "qy"),             # 3Q26 · 3Q '26
    (re.compile(r"(?<![A-Za-z0-9])([1-4])Q\s?(20\d\d)(?!\d)", re.I), "qY"),                # 3Q 2026
    (re.compile(r"(?<![A-Za-z0-9])Q([1-4])\s?'?(20\d\d|\d{2})(?!\d)", re.I), "Qy"),           # Q3 2026 · Q3'26
    (re.compile(r"(20\d\d)\s?년?\s?([1-4])\s?분기"), "Y분기"),                                  # 2026년 3분기 · 2026 3분기
    (re.compile(r"(20\d\d)\s?(?:년\s?)?([1-4])Q(?![A-Za-z0-9])", re.I), "YQ"),               # 2026 3Q · 2026년 3Q
    (re.compile(r"(20\d\d)\s?Q([1-4])(?!\d)", re.I), "YQ"),                                   # 2026 Q2
]
_반기꼴 = [
    (re.compile(r"(?<![A-Za-z0-9])([12])H\s?'?(\d{2}|20\d\d)(?!\d)", re.I), "hy"),          # 1H26 · 2H 2026
    (re.compile(r"(20\d\d)\s?년?\s?(상|하)반기"), "Y반기"),
]
# 회계연도 표지(「Q2 FY27」 · 「FY26 Q4」 · 「FQ4」)는 결산월을 모르면 달력 기간으로 옮길 수 없다 — 지우고 본다(오독하면 기준일 안의 콜을 뒤로 민다)
_회계꼴 = re.compile(r"(?<![A-Za-z0-9])(?:Q[1-4]\s?FY\s?'?\d{2,4}|FY\s?'?\d{2,4}\s?Q[1-4]|F[1-4]?Q[1-4]?\s?'?\d{0,4})(?![A-Za-z0-9])", re.I)
# 회계연도의 분기를 밝힌 꼴(A18) — 결산월을 알면 그 분기의 끝 달로 푼다(「회계 2026 4분기」 · 「회계연도 2026년 3분기」 · 「FY2026 4분기」 · 「Q2 FY27」 · 「FY26 Q4」).
# 결산월을 모르면 지우고 본다(달력 분기로 읽으면 비달력 결산 회사의 기준일 안 콜을 뒤로 민다)
_회계분기꼴 = [
    (re.compile(r"(?:회계\s?(?:연도)?|FY)\s?'?(20\d\d|\d{2})\s?(?:년\s?)?(?:회계\s?)?([1-4])\s?분기", re.I), "YQ"),
    (re.compile(r"(?<![A-Za-z0-9])Q([1-4])\s?FY\s?'?(20\d\d|\d{2})(?![A-Za-z0-9])", re.I), "QY"),
    (re.compile(r"(?<![A-Za-z0-9])FY\s?'?(20\d\d|\d{2})\s?Q([1-4])(?![A-Za-z0-9])", re.I), "YQ"),
]
결산월 = None            # 표지(…, 결산월=) 가 도는 동안 쓴다 — 회계 분기 풀기(A18)


def 회계분기끝(y, q, 월):
    """회계연도 y(그 해 결산월 월에 끝나는 해)의 q 분기 끝 날."""
    m = 월 - 3 * (4 - q)
    while m <= 0:
        m += 12
        y -= 1
    return _달끝(y, m)


def _회계분기들(s, 월):
    """글 속 회계 분기 표지 → (그 분기 끝들, 표지를 지운 글). 월이 없으면 끝은 비고 표지만 지운다."""
    낸 = []
    for 꼴, 종 in _회계분기꼴:
        for m in 꼴.finditer(s):
            if 월:
                try:
                    y, q = (_해(m.group(1)), int(m.group(2))) if 종 == "YQ" else (_해(m.group(2)), int(m.group(1)))
                    if 2000 <= y <= 2099:
                        낸.append(회계분기끝(y, q, int(월)))
                except ValueError:
                    pass
        s = 꼴.sub(" ", s)
    return 낸, s
_공시날꼴 = re.compile(r"(10-Q|10-K|20-F|6-K|40-F|반기보고서|분기보고서|사업보고서)\s*[\(（]?\s*(20\d\d)[-./](\d{1,2})(?:[-./](\d{1,2}))?", re.I)
_날꼴 = [
    re.compile(r"(?<!\d)(20\d\d)-(\d{1,2})-(\d{1,2})(?!\d)"),
    re.compile(r"(?<!\d)(20\d\d)\.(\d{1,2})\.(\d{1,2})(?!\d)"),
    re.compile(r"(?<!\d)(20\d\d)년\s?(\d{1,2})월\s?(\d{1,2})일"),
]
_접수번호 = re.compile(r"\d{10}-\d{2}-\d{6}")          # SEC accession(날짜로 오독하지 않게 지운다)
# 전망 · 가이던스 낱말이 있는 조각의 기준일 뒤 기간은 「그 기간에 대한 전망」(출처의 기간이 아니다) — 세지 않는다
_전망꼴 = re.compile(r"전망|가이던스|예상|목표|계획|guidance|outlook|forecast|expect|target|plan", re.I)
# 정기보고서 이름(날짜 둘 — (F, T] 기간의 정기보고서는 재무기준일 정의상 T 뒤 제출) · 자동 표지의 경계(옛 사유 글에서 읽는다)
_정기꼴 = re.compile(r"10-Q|10-K|20-F|40-F|반기보고서|분기보고서|사업보고서", re.I)
_경계꼴 = re.compile(r"평가기준일 (20\d\d-\d\d-\d\d)")
자동꼬리 = "(자동 표지 — 기준일뒤.py)"


def 날(v):
    """'YYYY-MM-DD' · 'YYYYMMDD' · date → date | None."""
    if isinstance(v, datetime.date):
        return v
    s = ("%s" % (v or "")).strip()
    m = re.match(r"^(\d{4})-?(\d{2})-?(\d{2})", s)
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _달끝(y, mo):
    return datetime.date(y, mo, calendar.monthrange(y, mo)[1])


_달이름 = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}


def 공표날(v):
    """공표일 칸 → date | None. 온전한 날짜는 그날, 달까지만 밝힌 꼴은 그 달 끝날(A16 — 월간 발간물 · 「July 2026」).
    판정은 그 달 끝날로 한다 — 그 달 안 어느 날 나왔는지 모르니 늦은 쪽으로 본다(기준일 안 정보를 뒤로 미는 쪽이 아니라 앞당기지 않는 쪽)."""
    d = 날(v)
    if d is not None:
        return d
    s = ("%s" % (v or "")).strip()
    m = (re.match(r"^(20\d\d)[-./](\d{1,2})$", s) or re.match(r"^(20\d\d)\s?년\s?(\d{1,2})\s?월$", s))
    try:
        if m:
            return _달끝(int(m.group(1)), int(m.group(2)))
        m = re.match(r"^([A-Za-z]{3})[A-Za-z]*\.?\s+(20\d\d)$", s)
        if m and m.group(1).lower() in _달이름:
            return _달끝(int(m.group(2)), _달이름[m.group(1).lower()])
    except ValueError:
        return None
    return None


def _해(s):
    y = int(s)
    return y + 2000 if y < 100 else y


def 기간끝들(글):
    """글 속 기간 표지 → [date(기간 끝)]."""
    회끝, s = _회계분기들(_접수번호.sub(" ", 글 or ""), 결산월)
    s = _회계꼴.sub(" ", s)
    낸 = list(회끝)
    for 꼴, 종 in _분기꼴:
        for m in 꼴.finditer(s):
            try:
                if 종 in ("qy", "qY"):
                    q, y = int(m.group(1)), _해(m.group(2))
                elif 종 == "Qy":
                    q, y = int(m.group(1)), _해(m.group(2))
                elif 종 == "FYQ":
                    y, q = _해(m.group(1)), int(m.group(2))
                else:
                    y, q = int(m.group(1)), int(m.group(2))
                if 2000 <= y <= 2099:
                    낸.append(_달끝(y, q * 3))
            except ValueError:
                continue
    for 꼴, 종 in _반기꼴:
        for m in 꼴.finditer(s):
            if 종 == "hy":
                h, y = int(m.group(1)), _해(m.group(2))
            else:
                y, h = int(m.group(1)), (1 if m.group(2) == "상" else 2)
            낸.append(_달끝(y, 6 * h))
    for m in _공시날꼴.finditer(s):
        try:
            y, mo = int(m.group(2)), int(m.group(3))
            if not m.group(4):
                낸.append(_달끝(y, mo))
                continue
            d = datetime.date(y, mo, int(m.group(4)))
            if d == _달끝(y, mo) and mo % 3 == 0:
                낸.append(d)                                   # 「10-Q 2026-09-30」 — 기간 끝
            else:                                              # 「반기보고서 2026-08-14」 — 제출일 → 그 앞의 마지막 분기 끝
                q = (mo - 1) // 3 * 3
                낸.append(_달끝(y, q) if q else datetime.date(y - 1, 12, 31))
        except ValueError:
            continue
    return 낸


def 날짜들(글):
    s = _접수번호.sub(" ", 글 or "")
    낸 = []
    for 꼴 in _날꼴:
        for m in 꼴.finditer(s):
            try:
                낸.append(datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
            except ValueError:
                continue
    return 낸


def 조각들(글):
    """맨 바깥 「 · 」 · 「;」 · 「 / 」 로 조각낸다(괄호 안은 자르지 않는다)."""
    낸, 깊, 버 = [], 0, []
    s = 글 or ""
    i = 0
    while i < len(s):
        c = s[i]
        if c in "(（[":
            깊 += 1
        elif c in ")）]":
            깊 = max(0, 깊 - 1)
        if 깊 == 0 and (s.startswith(" · ", i) or c == ";" or s.startswith(" / ", i)):
            낸.append("".join(버))
            버 = []
            i += 3 if s.startswith((" · ", " / "), i) else 1
            continue
        버.append(c)
        i += 1
    낸.append("".join(버))
    return [x.strip() for x in 낸 if x.strip()]


def _재(재무기준일, 기):
    """재무기준일 F(없거나 꼴이 아니거나 T 보다 늦으면 T — 「사이」 가 생기지 않는 옛 판)."""
    f = 날(재무기준일)
    return f if (f is not None and 기 is not None and f < 기) else 기


def 날판정(d, 기준일, 재무기준일=None):
    """날짜 하나 → 뒤(> T) | 사이((F, T]) | 안(≤ F) | 모름. 다른 도구(수시공시 · 레터)가 같은 경계를 쓰게 한 곳에 둔다."""
    dd, 기 = 날(d), 날(기준일)
    if dd is None or 기 is None:
        return "모름"
    재 = _재(재무기준일, 기)
    return "뒤" if dd > 기 else ("사이" if dd > 재 else "안")


def 조각판정(조각, 기준일, 조사일=None, 재무기준일=None):
    """→ (뒤 | 사이 | 안 | 섞임 | 모름, 사유). 기준일 = 평가기준일 T · 재무기준일 F(없으면 T — 「사이」 없음)."""
    기, 조 = 날(기준일), 날(조사일) or datetime.date.today()
    재 = _재(재무기준일, 기)
    끝들 = 기간끝들(조각)
    if 끝들 and _전망꼴.search(조각):
        끝들 = [d for d in 끝들 if d <= 기]
    if 끝들:
        뒤 = [d for d in 끝들 if d > 기]
        if 뒤 and len(뒤) < len(끝들):
            return "섞임", "기간 %s ~ %s(기준일 %s 을 걸침)" % (min(끝들), max(끝들), 기)
        if 뒤:
            return "뒤", "기간 끝 %s > 평가기준일 %s" % (max(뒤), 기)
        사이 = [d for d in 끝들 if d > 재]
        if 사이:
            끝 = max(사이)
            공표 = [d for d in 날짜들(조각) if 끝 < d <= 조]          # 기간 끝 뒤의 날짜 — 공표 · 제출일 후보
            if 공표 and all(d > 기 for d in 공표):
                return "뒤", "기간 끝 %s 은 재무기준일 %s 뒤 · 공표 %s > 평가기준일 %s" % (끝, 재, min(공표), 기)
            정기 = bool(_정기꼴.search(조각))
            if 정기 and not 공표:
                return "뒤", ("기간 끝 %s 의 정기보고서 — 재무기준일 %s 뒤 기간의 정기보고서는 평가기준일 %s 뒤 제출이다(재무기준일의 정의)"
                             % (끝, 재, 기))
            덧 = (" · 정기보고서가 평가기준일 전(%s)에 제출됐다 — 재무기준일을 %s 로 옮길 후보(기준일.py)" % (min(공표), 끝)) if 정기 else ""
            return "사이", "기간 끝 %s — 재무기준일 %s 과 평가기준일 %s 사이(추정의 근거 · 실적 열이 아니다)%s" % (끝, 재, 기, 덧)
        return "안", "기간 끝 %s ≤ 평가기준일" % max(끝들)
    날들 = [d for d in 날짜들(조각) if d <= 조]
    if not 날들:
        return "모름", ""
    뒤 = [d for d in 날들 if d > 기]
    if 뒤 and len(뒤) == len(날들):
        return "뒤", "공표일 %s > 평가기준일 %s" % (max(뒤), 기)
    if 뒤:
        return "섞임", "날짜 %s ~ %s(기준일 %s 을 걸침)" % (min(날들), max(날들), 기)
    사이 = [d for d in 날들 if d > 재]
    if 사이:
        return "사이", "공표일 %s — 재무기준일 %s 과 평가기준일 %s 사이(추정의 근거)" % (max(사이), 재, 기)
    return "안", "공표일 %s ≤ 평가기준일" % max(날들)


def 글판정(글, 기준일, 조사일=None, 재무기준일=None):
    """출처 글 하나 → (뒤 | 사이 | 안 | 섞임 | 모름, 사유). 「사이」 는 「안」 과 같이 쓰는 쪽이다(뒤와 섞이면 섞임)."""
    판 = [조각판정(x, 기준일, 조사일, 재무기준일) for x in 조각들(글)]
    뒤 = [p for p in 판 if p[0] == "뒤"]
    사이 = [p for p in 판 if p[0] == "사이"]
    안 = [p for p in 판 if p[0] == "안"]
    섞 = [p for p in 판 if p[0] == "섞임"]
    if 섞 or (뒤 and (안 or 사이)):
        return "섞임", " · ".join(p[1] for p in (섞 + 뒤 + 사이 + 안))[:300]
    if 뒤:
        return "뒤", " · ".join(p[1] for p in 뒤)[:300]
    if 사이:
        return "사이", " · ".join(p[1] for p in 사이)[:300]
    if 안:
        return "안", 안[0][1]
    return "모름", ""


def _출처를품나(v):
    """값이 출처 항목(제 출처 칸을 가진 사전)을 품었나 — 사전 · 사전 목록을 한 겹 본다."""
    if isinstance(v, dict):
        return any(k in v for k in 출처칸)
    if isinstance(v, list):
        return any(isinstance(x, dict) and any(k in x for k in 출처칸) for x in v)
    return False


def _잎출처인가(d):
    """출처 항목인가 — 제 자리에 출처 칸이 있고, 값 가운데 다른 출처 항목을 품은 것이 없다(A23 — 기준{} · 점유율{} 같은 속성 사전은 품어도 된다)."""
    if not isinstance(d, dict) or "근거범위" in d or "scenario_axes" in d:
        return False
    if any(_출처를품나(v) for v in d.values()):
        return False
    return any(k in d for k in 출처칸)


def _항목글(d, 빼기=()):
    글들 = []
    for k in 식별칸:
        if k in 빼기:
            continue
        v = d.get(k)
        if isinstance(v, str):
            글들.append(v)
        elif isinstance(v, list):
            글들 += [x for x in v if isinstance(x, str)]
    return " · ".join(글들)


def 항목판정(d, 기준일, 조사일=None, 재무기준일=None):
    """출처 항목(잎 사전) → (상태, 사유). 공표일 칸이 있으면 그 칸을 공표일로 본다(기간 표지가 우선).
    재무기준일 F 가 T 보다 이르면(날짜 둘) 기간 판정에서 공표일 칸을 따로 본다 — (F, T] 기간이어도 공표일 칸이 T 뒤면 「뒤」,
    (F, T] 기간의 정기보고서도 공표일 칸이 T 이하면 「사이」(재무기준일을 옮길 후보)."""
    기 = 날(기준일)
    재 = _재(재무기준일, 기)
    조 = 날(조사일) or datetime.date.today()
    if 재 is not None and 기 is not None and 재 < 기:
        공 = [(k, 공표날(d.get(k))) for k in 공표칸 if 공표날(d.get(k)) is not None and 공표날(d.get(k)) <= 조]
        본2 = _항목글(d, 빼기=공표칸)
        끝들 = 기간끝들(본2)
        if 끝들:
            상, 사 = 글판정(본2, 기준일, 조사일, 재무기준일)
            if 공 and 상 == "사이":
                k, p = min(공, key=lambda x: x[1])
                if p > 기:
                    return "뒤", "기간은 재무기준일 %s 뒤 · %s %s > 평가기준일 %s" % (재, k, p, 기)
            if 공 and 상 == "뒤" and _정기꼴.search(본2) and max(끝들) <= 기 and all(p <= 기 for _, p in 공):
                k, p = max(공, key=lambda x: x[1])
                return "사이", ("기간 끝 %s — 재무기준일 %s 과 평가기준일 %s 사이 · 정기보고서가 평가기준일 전(%s %s)에 제출됐다 — "
                              "재무기준일을 %s 로 옮길 후보(기준일.py)" % (max(끝들), 재, 기, k, p, max(끝들)))
            return 상, 사
        for k, dd in 공:
            if 기 < dd:
                return "뒤", "%s %s > 평가기준일 %s" % (k, dd, 기)
            if 재 < dd:
                return "사이", "%s %s — 재무기준일 %s 과 평가기준일 %s 사이(추정의 근거)" % (k, dd, 재, 기)
            return "안", "%s %s ≤ 평가기준일" % (k, dd)
        return 글판정(_항목글(d), 기준일, 조사일, 재무기준일)
    본 = _항목글(d)
    if 기간끝들(본):
        return 글판정(본, 기준일, 조사일)
    for k in 공표칸:
        dd = 공표날(d.get(k))
        if dd is not None:
            if 날(기준일) < dd <= 조:
                return "뒤", "%s %s > 평가기준일 %s" % (k, dd, 날(기준일))
            if dd <= 날(기준일):
                return "안", "%s %s ≤ 평가기준일" % (k, dd)
    return 글판정(본, 기준일, 조사일)


def 자동경계(사유):
    """자동 표지 사유 글 → 그 표지를 단 경계(평가기준일) date | None. 사람이 단 표지(자동 꼬리 없음)는 None."""
    s = "%s" % (사유 or "")
    if 자동꼬리 not in s:
        return None
    ds = [날(m.group(1)) for m in _경계꼴.finditer(s)]
    ds = [d for d in ds if d is not None]
    return max(ds) if ds else None


_옮김까닭 = "근거 범위의 출처가 평가기준일 뒤 정보뿐 — `근거범위_기준일뒤` 로 옮김(부록 G 재료). 기준일 안 출처로 다시 잡는다"


def 표지(j, 기준일, 조사일=None, 재무기준일=None, 결산월=None):
    """결산월(1~12)을 주면 회계 분기 표지를 그 결산월로 푼다(A18). 아래 설명은 그대로다."""
    앞 = globals()["결산월"]
    globals()["결산월"] = 결산월
    try:
        return _표지(j, 기준일, 조사일, 재무기준일)
    finally:
        globals()["결산월"] = 앞


def _표지(j, 기준일, 조사일=None, 재무기준일=None):
    """조사 산출 하나(사전)에 표지를 단다(제자리) → 셈 dict. 같은 산출에 두 번 돌려도 더 바뀌지 않는다(`바뀜` 거짓).
    기준일 = 평가기준일 T. 재무기준일 F 가 T 보다 이르면(날짜 둘) (F, T] 출처에 「사이」 표지를 달고 옛 경계의 자동 표지를 다시 본다 —
    셈에 사이표지(이번에 단 것) · 사이수(지금 상태) · 거둠 · 축되돌림 · 밴드되돌림 · 축사이가 더해진다(F 가 없으면 셈 · 산출이 날짜 둘 전과 같다).

    셈 — 새표지 · 이미(출처 항목) · 축옮김 · 밴드옮김(이번에 옮긴 것) · 축섞임 · 축기준일뒤 · 밴드기준일뒤(지금 상태) · 바뀜 · 보기."""
    셈 = {"새표지": 0, "이미": 0, "축옮김": 0, "축섞임": 0, "밴드옮김": 0, "축기준일뒤": 0, "밴드기준일뒤": 0, "바뀜": False, "보기": []}
    if not 날(기준일):
        셈["까닭"] = "평가기준일 없음"
        return 셈
    기 = 날(기준일)
    재 = _재(재무기준일, 기)
    둘 = 재 < 기                                           # 날짜 둘 — 「사이」 가 생기는 판
    if 둘:
        셈.update({"사이표지": 0, "사이수": 0, "거둠": 0, "축되돌림": 0, "밴드되돌림": 0, "축사이": 0})

    def _사이달기(x, 사):
        if "기준일사이" not in x:
            x["기준일사이"] = True
            x["기준일사이_사유"] = "%s %s" % (사, 자동꼬리)
            셈["사이표지"] += 1
            셈["바뀜"] = True

    def 잎(x, 경로):
        if x.get("기준일뒤") is True:
            b = 자동경계(x.get("기준일뒤_사유")) if 둘 else None
            if b is not None and b < 기:
                상, 사 = 항목판정(x, 기준일, 조사일, 재)
                if 상 != "뒤":                                  # 옛 경계(재무 분기말)로 단 자동 표지 — T 로 보니 뒤가 아니다
                    x.pop("기준일뒤", None)
                    x.pop("기준일뒤_사유", None)
                    x["기준일뒤_거둠"] = "옛 경계 %s 의 자동 표지를 평가기준일 %s 로 다시 봤다 — %s" % (b, 기, 상)
                    셈["거둠"] += 1
                    셈["바뀜"] = True
                    if 상 == "사이":
                        _사이달기(x, 사)
                    return
            셈["이미"] += 1
        elif "기준일뒤" not in x or x.get("기준일뒤") is False:
            상, 사 = 항목판정(x, 기준일, 조사일, 재무기준일)
            if 상 == "뒤":
                if x.get("기준일뒤") is False:
                    x["기준일뒤_손"] = False                  # 손으로 적은 값 — 도구 판정이 덮었다(A3)
                x["기준일뒤"] = True
                x["기준일뒤_사유"] = "%s %s" % (사, 자동꼬리)
                셈["새표지"] += 1
                셈["바뀜"] = True
                if len(셈["보기"]) < 8:
                    셈["보기"].append("%s — %s" % (경로, 사))
            elif 상 == "사이" and 둘:
                _사이달기(x, 사)

    def 걷기(x, 경로):
        if isinstance(x, dict):
            if _잎출처인가(x):
                잎(x, 경로)
                if 둘 and x.get("기준일사이") is True and x.get("기준일뒤") is not True:
                    셈["사이수"] += 1                           # 지금 상태(새로 단 것 + 이미 있던 것)
                return
            for k, v in x.items():
                if k in ("근거범위", "근거범위_기준일뒤", "보강_B2"):        # 축의 근거 범위는 아래 축 규칙이 본다(출처 항목이 아니다)
                    continue
                걷기(v, "%s.%s" % (경로, k) if 경로 else k)
        elif isinstance(x, list):
            for i, v in enumerate(x):
                걷기(v, "%s[%d]" % (경로, i))

    for ax in (j.get("scenario_axes") or []) if isinstance(j, dict) else []:
        if not isinstance(ax, dict):
            continue
        옛 = ax.get("근거범위_기준일뒤")
        if 둘 and ax.get("근거범위") is None and isinstance(옛, dict) and isinstance(옛.get("출처"), str):
            b = 자동경계("%s %s" % (옛.get("사유") or "", 자동꼬리))           # 옮긴 근거 범위의 사유 글 — 그때의 경계
            if b is not None and b < 기:
                상, 사 = 글판정(옛["출처"], 기준일, 조사일, 재)
                if 상 != "뒤":                                  # 옛 경계로 옮긴 범위 — T 로 보니 뒤가 아니다 → 되돌린다
                    ax["근거범위"] = {k: v for k, v in 옛.items() if k != "사유"}
                    ax.pop("근거범위_기준일뒤", None)
                    if ax.get("근거범위_까닭") == _옮김까닭:
                        ax.pop("근거범위_까닭")
                    ax["근거범위_거둠"] = "옛 경계 %s 로 옮긴 근거 범위를 평가기준일 %s 로 다시 봤다(%s) — 되돌렸다" % (b, 기, 상)
                    셈["축되돌림"] += 1
                    셈["바뀜"] = True
        r = ax.get("근거범위")
        if isinstance(r, dict) and isinstance(r.get("출처"), str) and r.get("출처").strip():
            상, 사 = 글판정(r["출처"], 기준일, 조사일, 재무기준일)
            if 상 == "뒤":
                ax["근거범위_기준일뒤"] = dict(r, 사유=사)
                ax["근거범위"] = None
                ax.setdefault("근거범위_까닭", _옮김까닭)
                셈["축옮김"] += 1
                셈["바뀜"] = True
            elif 상 == "섞임":
                글 = "근거 범위 출처에 평가기준일 뒤 정보가 섞였다(%s) — 기준일 안 출처만으로 다시 잡는다" % 사
                if ax.get("근거범위_기준일뒤섞임") != 글:
                    ax["근거범위_기준일뒤섞임"] = 글
                    셈["바뀜"] = True
            elif ax.get("근거범위_기준일뒤섞임"):           # 출처가 고쳐져 더 섞이지 않으면 경보를 거둔다
                ax.pop("근거범위_기준일뒤섞임")
                셈["바뀜"] = True
            if 둘:
                글 = ("근거 범위 출처에 재무기준일과 평가기준일 사이의 정보가 있다(%s) — 추정의 근거로 쓴다 · 실적 열이 아니다" % 사) if 상 == "사이" else None
                if 글 and ax.get("근거범위_기준일사이") != 글:
                    ax["근거범위_기준일사이"] = 글
                    셈["바뀜"] = True
                elif not 글 and ax.get("근거범위_기준일사이"):
                    ax.pop("근거범위_기준일사이")
                    셈["바뀜"] = True
        if 둘 and isinstance(ax.get("근거범위_밴드_기준일뒤"), list) and ax["근거범위_밴드_기준일뒤"]:
            되, 둠 = [], []
            for e in ax["근거범위_밴드_기준일뒤"]:
                (둠 if not isinstance(e, str) or 글판정(e, 기준일, 조사일, 재)[0] == "뒤" else 되).append(e)
            if 되:                                              # 옛 경계로 옮긴 밴드 표현 — T 로 보니 뒤가 아니다
                ax["근거범위_밴드"] = (ax.get("근거범위_밴드") or []) + 되
                if 둠:
                    ax["근거범위_밴드_기준일뒤"] = 둠
                else:
                    ax.pop("근거범위_밴드_기준일뒤")
                셈["밴드되돌림"] += len(되)
                셈["바뀜"] = True
        밴 = ax.get("근거범위_밴드")
        if isinstance(밴, list) and 밴:
            남, 뒤 = [], []
            for e in 밴:
                (뒤 if isinstance(e, str) and 글판정(e, 기준일, 조사일, 재무기준일)[0] == "뒤" else 남).append(e)
            if 뒤:
                ax["근거범위_밴드"] = 남
                ax["근거범위_밴드_기준일뒤"] = (ax.get("근거범위_밴드_기준일뒤") or []) + 뒤
                셈["밴드옮김"] += len(뒤)
                셈["바뀜"] = True
        if 둘:
            셈["축사이"] += 1 if ax.get("근거범위_기준일사이") else 0
        셈["축섞임"] += 1 if ax.get("근거범위_기준일뒤섞임") else 0
        셈["축기준일뒤"] += 1 if ax.get("근거범위_기준일뒤") else 0
        셈["밴드기준일뒤"] += len(ax.get("근거범위_밴드_기준일뒤") or [])
    걷기(j, "")
    return 셈

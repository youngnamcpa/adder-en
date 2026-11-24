# -*- coding: utf-8 -*-
"""**공시표** — DART 공시 원문 XML(dart4.xsd)의 표를 **격자**로 읽는다(FX-A · R2, 2026-10-25).

왜 — `dart_fetch.원문` 은 받은 XML 곁에 태그를 벗긴 txt 를 둔다. txt 에서는 ROWSPAN · COLSPAN 이 사라져 병합 행이 한 칸씩 밀린다
(투자계획 표가 55조각 · 「5,208」 이 프로젝트 이름 · 토지 「-」 칸 때문에 상각이 한 열 밀려 CAPEX ÷ 상각 8.27 ↔ 4.36 — F 물결 결함 F5 · F17 · F22).
XML 은 곁에 그대로 있다 — 이 모듈은 그 XML 을 읽어 표마다 칸의 자리를 지킨 격자를 낸다. 업종 · 회사와 무관한 원문 꼴의 규칙이다.

    import 공시표
    문 = 공시표.읽기("…/반기/20260812000829.xml")          # {"형식판", "문서이름", "기간", "표": [표 …]} — 경로마다 한 번만 읽는다(캐시)
    for 표 in 공시표.찾기(문, r"생산\\s*능력"):            # 앞글 · 제목 · 머리에 그 낱말이 있는 표
        print(표["열이름"], 공시표.줄들(표))

문서의 문단 — `문["글"]` = [(제목경로 튜플, 문단 글)] (표 밖 문단 · 문서 차례 — 가동률 · 수주잔고 문장을 찾는 데 쓴다).
표 하나 — {"번호", "제목경로": [큰 제목 …], "앞글": [표 앞 문단 …], "뒷글": [표 뒤 문단 …], "단위": "백만원" | None,
           "격자": [[칸 글 …] …], "병합": [[bool …] …](ROWSPAN · COLSPAN 으로 복사된 칸 = True), "머리줄수": n, "열이름": [열마다 머리 글],
           "연결": True | False | None(연결 · 별도 주석 구획), "줄수", "열수"}
- 칸 자리를 지킨다: 「-」 · 빈 칸도 그 자리에 둔다(옮기지 않는다). 병합 칸은 펼친 자리마다 같은 글을 복사하고 `병합` 에 표시한다
  (줄 이름 · 머리는 복사가 쓸모 있고, 수를 더할 때는 복사 칸을 건너뛴다).
- 표 경계 = XML 의 TABLE 요소 하나(한 절 안 표 둘도 갈린다). 「(단위 : 백만원)」 한 칸짜리 표는 표가 아니라 다음 표의 단위 글로 붙인다.
"""
from __future__ import annotations

import html
import io
import os
import re

_캐시 = {}
_토큰 = re.compile(r"<(/?)([A-Za-z][A-Za-z0-9\-]*)((?:\s+[^>]*?)?)\s*(/?)>|([^<]+)", re.S)
_속성 = re.compile(r'([A-Za-z\-]+)\s*=\s*"([^"]*)"')
_칸태그 = ("TD", "TH", "TE", "TU")
_단위re = re.compile(r"\(?\s*단\s*위\s*[:：]\s*([^)\n]+?)\s*\)?\s*$")
_단위배 = {"원": 1.0, "천원": 1e3, "백만원": 1e6, "억원": 1e8, "십억원": 1e9, "조원": 1e12}


def 글정리(s):
    """XML 글 → 한 줄 글(엔티티 풀기 · &cr; 와 줄바꿈은 빈칸 · 빈칸 하나로)."""
    s = (s or "").replace("&cr;", " ").replace("&amp;cr;", " ")
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s.replace("　", " ").replace("\xa0", " ")).strip()


def 수(c):
    """칸 글 → 수. 괄호 · 「△」 · 「-」 앞 = 음수, 「-」 · 「－」 한 글자 = 0, 「%」 는 떼고 그대로(30.5% → 30.5). 수가 아니면 None."""
    if c is None:
        return None
    c = c.strip().replace(" ", "")
    if c in ("-", "－", "—", "–"):
        return 0.0
    c = c.rstrip("%")
    m = re.fullmatch(r"(\()?([△▲\-－])?\(?([0-9][0-9,]*(?:\.[0-9]+)?)\)?(\))?", c)
    if not m:
        return None
    v = float(m.group(3).replace(",", ""))
    음 = bool(m.group(1) and m.group(4)) or (m.group(2) in ("△", "-", "－"))
    return -v if 음 else v


def _외화단위(u):
    """「US$1,000」 · 「USD 1,000」 · 「천USD」 · 「백만달러」 → 「천USD」 · 「백만USD」 꼴(외화 — 원화 배수는 없다). 아니면 None."""
    k = re.sub(r"\s+", "", u or "")
    m = re.match(r"^(US\$|USD|\$|미화|EUR|€|JPY|￥|CNY|위안)(1,000,000|1,000|천|백만)?", k, re.I)
    m2 = re.match(r"^(천|백만|억)?(USD|US\$|달러|미불|EUR|유로|JPY|엔|CNY|위안)", k, re.I)
    통 = None
    if m:
        통, 배 = m.group(1), {"1,000": "천", "천": "천", "1,000,000": "백만", "백만": "백만"}.get(m.group(2) or "", "")
    elif m2:
        통, 배 = m2.group(2), m2.group(1) or ""
    if not 통:
        return None
    통 = {"US$": "USD", "$": "USD", "미화": "USD", "달러": "USD", "미불": "USD", "€": "EUR", "유로": "EUR", "￥": "JPY", "엔": "JPY", "위안": "CNY"}.get(통, 통.upper())
    return 배 + 통


def 단위목록(글):
    """「(단위 : ㎡, 백만원)」 → ["㎡", "백만원"] — 쉼표로 갈린 단위를 모두(외화는 「천USD」 꼴)."""
    낸 = []
    for 조각 in re.findall(r"\(\s*단\s*위\s*[:：][^)]*\)|단\s*위\s*[:：][^)\n]{0,40}", 글 or ""):
        m = re.search(r"단\s*위\s*[:：]\s*(.+?)\s*\)?$", 조각)
        if not m:
            continue
        몸 = m.group(1)
        while re.search(r"\d,\d{3}", 몸):
            몸 = re.sub(r"(\d),(\d{3})", r"\1\2", 몸)          # 「US$1,000」 의 쉼표는 단위를 가르지 않는다
        for u in re.split(r"[,，·]", 몸):
            u = re.sub(r"\s+", "", u)
            if not u:
                continue
            외 = _외화단위(u.replace("1000000", "1,000,000").replace("1000", "1,000"))
            if 외:
                낸.append(외)
                continue
            for k in sorted(_단위배, key=len, reverse=True):
                if u.startswith(k) or u.endswith(k):
                    u = k
                    break
            낸.append(u)
    return 낸


def 단위읽기(글):
    """「(단위 : 백만원)」 · 「(단위: 천원, 주)」 → 「백만원」(쉼표 앞 첫 단위 · 외화는 「천USD」). 없으면 None."""
    목 = 단위목록(글)
    return 목[0] if 목 else None


def _연결(제목경로):
    글 = " ".join(제목경로[-3:])
    if re.search(r"연결\s*재무\s*제표|\(연결\)", 글):
        return True
    if re.search(r"재무\s*제표\s*(주석|등)?", 글):
        return False
    return None


def _격자(줄들):
    """[(칸 글, ROWSPAN, COLSPAN, 머리)] 줄 목록 → (격자, 병합, 머리 격자). ROWSPAN · COLSPAN 을 펼치고 자리를 지킨다."""
    자리, 병, 머 = {}, {}, {}
    끝열 = 0
    for i, 줄 in enumerate(줄들):
        j = 0
        for 글, rs, cs, h in 줄:
            while (i, j) in 자리:
                j += 1
            for di in range(rs):
                for dj in range(cs):
                    자리[(i + di, j + dj)] = 글
                    병[(i + di, j + dj)] = (di, dj) != (0, 0)
                    머[(i + di, j + dj)] = h
            j += cs
            끝열 = max(끝열, j)
    n = len(줄들)
    격 = [[자리.get((i, j), "") for j in range(끝열)] for i in range(n)]
    병합 = [[병.get((i, j), False) for j in range(끝열)] for i in range(n)]
    머리 = [[머.get((i, j), False) for j in range(끝열)] for i in range(n)]
    return 격, 병합, 머리


def _수칸인가(c):
    return 수(c) is not None and bool(re.search(r"\d", c or ""))


def _머리줄수(격, 머리, thead수):
    if thead수:
        return min(thead수, len(격))
    k = 0
    while k < len(격) and 머리[k] and all(머리[k][j] or not 격[k][j] for j in range(len(격[k]))) and any(머리[k]):
        k += 1
    if k:
        return k
    # TH 가 없다 — 수 칸이 없는 앞 줄(최대 3)이 머리다(그 뒤에 수 줄이 있을 때만)
    while k < min(3, len(격) - 1) and not any(_수칸인가(c) for c in 격[k][1:]) and any(c for c in 격[k]):
        k += 1
    return k if k < len(격) else 0


def _열이름(격, k):
    """머리 k 줄을 위에서 아래로 이어 열마다 이름(같은 글이 겹치면 한 번) — 「수주잔고 금액」 꼴."""
    if not 격:
        return []
    낸 = []
    for j in range(len(격[0])):
        조각 = []
        for i in range(k):
            c = 격[i][j]
            if c and (not 조각 or 조각[-1] != c):
                조각.append(c)
        낸.append(" ".join(조각))
    return 낸


def 읽기(경로):
    """XML → {"형식판", "문서이름", "기간": {"시작", "끝"} | None, "표": [표 …]}. 경로마다 한 번만 읽는다. 파일이 없으면 None."""
    경로 = os.path.abspath(경로)
    if 경로 in _캐시:
        return _캐시[경로]
    if not os.path.exists(경로):
        return None
    t = io.open(경로, encoding="utf-8", errors="ignore").read()
    문 = {"경로": 경로, "형식판": None, "문서이름": None, "기간": None, "표": [], "글": []}
    m = re.search(r"<FORMULA-VERSION[^>]*>([^<]*)<", t)
    문["형식판"] = m.group(1).strip() if m else None
    m = re.search(r"<DOCUMENT-NAME[^>]*>([^<]*)<", t)
    문["문서이름"] = 글정리(m.group(1)) if m else None
    시 = re.search(r'AUNIT="PERIODFROM"[^>]*AUNITVALUE="(\d{8})"', t) or re.search(r'AUNITVALUE="(\d{8})"[^>]*AUNIT="PERIODFROM"', t)
    끝 = re.search(r'AUNIT="PERIODTO"[^>]*AUNITVALUE="(\d{8})"', t) or re.search(r'AUNITVALUE="(\d{8})"[^>]*AUNIT="PERIODTO"', t)
    if 시 and 끝:
        문["기간"] = {"시작": "%s-%s-%s" % (시.group(1)[:4], 시.group(1)[4:6], 시.group(1)[6:]),
                    "끝": "%s-%s-%s" % (끝.group(1)[:4], 끝.group(1)[4:6], 끝.group(1)[6:])}
    사건 = []                       # ("글", 글) · ("표", 표) — 문서 차례
    제목 = {}                       # 깊이 → 제목 글
    깊이 = 0
    표쌓 = []                       # 표 안(중첩 표가 드물게 있다) — [{"줄": [...], "지금줄": [...], "thead": n, "in_thead": bool}]
    칸 = None                       # 지금 칸 {"글": [...], "rs", "cs", "h"}
    제목글 = None
    문단 = None
    그룹 = 0                        # TABLE-GROUP 깊이 — XBRL 주석(DART 6.x)은 TABLE-GROUP 안 TITLE 이 주석 제목이다(구획 제목을 덮지 않게 따로 둔다)
    그룹제목 = None
    번호머리 = None                 # 옛 꼴 주석 — 「36. 우발부채와 약정사항」 같은 번호 문단(그룹 제목이 없을 때 주석 제목)

    def _경로():
        return [제목[d] for d in sorted(제목)] + ([그룹제목] if 그룹제목 else [])
    for m in _토큰.finditer(t):
        닫, 태그, 속, _홀, 글 = m.group(1), (m.group(2) or "").upper(), m.group(3) or "", m.group(4), m.group(5)
        if 글 is not None:
            if 칸 is not None:
                칸["글"].append(글)
            elif 제목글 is not None:
                제목글.append(글)
            elif 문단 is not None and not 표쌓:
                문단.append(글)
            continue
        if not 닫:
            if 태그.startswith("SECTION-"):
                깊이 += 1
                for d in [d for d in 제목 if d >= 깊이]:
                    del 제목[d]
            elif 태그 == "TITLE":
                제목글 = []
            elif 태그 == "TABLE-GROUP":
                그룹 += 1
            elif 태그 == "P" and not 표쌓 and 칸 is None:
                문단 = []
            elif 태그 == "TABLE":
                표쌓.append({"줄": [], "지금줄": None, "thead": 0, "in_thead": False})
            elif 태그 == "THEAD" and 표쌓:
                표쌓[-1]["in_thead"] = True
            elif 태그 == "TR" and 표쌓:
                표쌓[-1]["지금줄"] = []
            elif 태그 in _칸태그 and 표쌓:
                a = dict((k.upper(), v) for k, v in _속성.findall(속))
                try:
                    rs = max(1, int(a.get("ROWSPAN", "1") or 1))
                except ValueError:
                    rs = 1
                try:
                    cs = max(1, int(a.get("COLSPAN", "1") or 1))
                except ValueError:
                    cs = 1
                칸 = {"글": [], "rs": min(rs, 200), "cs": min(cs, 60), "h": 태그 == "TH" or 표쌓[-1]["in_thead"]}
            elif 태그 in ("BR",) and 칸 is not None:
                칸["글"].append(" ")
            continue
        # 닫는 태그
        if 태그.startswith("SECTION-"):
            깊이 = max(0, 깊이 - 1)
            그룹제목, 번호머리 = None, None
        elif 태그 == "TABLE-GROUP":
            그룹 = max(0, 그룹 - 1)
            if 그룹 == 0:
                그룹제목 = None
        elif 태그 == "TITLE" and 제목글 is not None:
            제목s = 글정리("".join(제목글))
            if 그룹:
                그룹제목 = 제목s
            else:
                제목[깊이] = 제목s
                for d in [d for d in 제목 if d > 깊이]:
                    del 제목[d]
                그룹제목, 번호머리 = None, None
            사건.append(("제목", 제목s))
            제목글 = None
        elif 태그 == "P" and 문단 is not None:
            s = 글정리("".join(문단))
            if s:
                사건.append(("글", s))
                문["글"].append((tuple(_경로()), s))
                if re.match(r"^\d{1,2}\.\s*[^\d\s]", s) and len(s) <= 80:
                    번호머리 = s
            문단 = None
        elif 태그 in _칸태그 and 칸 is not None and 표쌓:
            if 표쌓[-1]["지금줄"] is None:
                표쌓[-1]["지금줄"] = []
            표쌓[-1]["지금줄"].append((글정리("".join(칸["글"])), 칸["rs"], 칸["cs"], 칸["h"]))
            칸 = None
        elif 태그 == "TR" and 표쌓:
            if 표쌓[-1]["지금줄"] is not None:
                표쌓[-1]["줄"].append(표쌓[-1]["지금줄"])
                if 표쌓[-1]["in_thead"]:
                    표쌓[-1]["thead"] += 1
            표쌓[-1]["지금줄"] = None
        elif 태그 == "THEAD" and 표쌓:
            표쌓[-1]["in_thead"] = False
        elif 태그 == "TABLE" and 표쌓:
            s = 표쌓.pop()
            if 표쌓:                                 # 중첩 표 — 바깥 표의 지금 칸 글로 붙인다
                continue
            줄 = s["줄"]
            셀수 = sum(len(r) for r in 줄)
            열수0 = max((sum(c[2] for c in r) for r in 줄), default=0)
            수있음 = any(_수칸인가(c[0]) for r in 줄 for c in r)
            if not 수있음 and (열수0 <= 1 or 셀수 <= 4 or (len(줄) <= 2 and 단위읽기(" ".join(c[0] for r in 줄 for c in r if c[0])))):
                # 글뿐인 표 — 「(단위 : 백만원)」 줄 · XBRL 주석의 글 덩이(한 열) · 표 이름 줄은 표가 아니라 다음 표의 앞글이다
                for r in 줄:
                    글r = " ".join(c[0] for c in r if c[0])
                    if 글r:
                        사건.append(("글", 글r))
                        문["글"].append((tuple(_경로()), 글r))
                continue
            if not 줄:
                continue
            격, 병합, 머리 = _격자([[c for c in r] for r in 줄])
            k = _머리줄수(격, 머리, s["thead"])
            경로들 = _경로()
            사건.append(("표", {"격자": 격, "병합": 병합, "머리줄수": k, "열이름": _열이름(격, k), "제목경로": 경로들,
                              "주석": 그룹제목 or 번호머리, "줄수": len(격), "열수": len(격[0]) if 격 else 0,
                              "연결": _연결([제목[d] for d in sorted(제목)] + [그룹제목 or 번호머리 or ""])}))
    # 앞글 · 뒷글 · 단위 · 번호
    표들 = []
    앞 = []
    for i, (종, x) in enumerate(사건):
        if 종 in ("글", "제목"):
            앞.append(x)
            continue
        x["번호"] = len(표들)
        x["앞글"] = 앞[-8:]
        뒤 = []
        for 종2, y in 사건[i + 1:]:
            if 종2 == "표":
                break
            if 종2 == "글":
                뒤.append(y)
            if len(뒤) >= 4:
                break
        x["뒷글"] = 뒤
        u = None
        for 글 in reversed(앞[-5:]):
            u = 단위읽기(글)
            if u:
                break
        if not u and x["격자"]:
            for r in x["격자"][:max(1, x["머리줄수"])]:
                u = 단위읽기(" ".join(r))
                if u:
                    break
        x["단위"] = u
        표들.append(x)
        앞 = []
    문["표"] = 표들
    _캐시[경로] = 문
    return 문


def 비우기():
    _캐시.clear()


def 표준(s):
    return re.sub(r"\s+", "", s or "")


def 맥락(표, 앞글수=3):
    """표를 찾을 때 보는 글 — 제목경로 마지막 둘 + 주석 제목 + 앞글 마지막 앞글수 줄."""
    return " ".join(표["제목경로"][-2:] + ([표["주석"]] if 표.get("주석") else []) + 표["앞글"][-앞글수:])


def 찾기(문, 글정규식, 머리정규식=None, 연결=None, 앞글수=3):
    """앞글 · 제목(맥락)에 글정규식이 걸리고(머리정규식이 있으면 열 이름에도 걸리는) 표 목록. 연결 = True · False 면 그 구획만."""
    if not 문:
        return []
    g = re.compile(글정규식)
    h = re.compile(머리정규식) if 머리정규식 else None
    낸 = []
    for 표 in 문["표"]:
        if 연결 is not None and 표["연결"] is not None and 표["연결"] != 연결:
            continue
        if not g.search(맥락(표, 앞글수)):
            continue
        if h and not any(h.search(표준(x)) for x in 표["열이름"]):
            continue
        낸.append(표)
    return 낸


def 줄들(표, 이름열수=None):
    """자료 줄 → [(줄 이름, [칸 글 …](이름 열 뒤), 줄 번호)]. 줄 이름 = 앞쪽 글 칸(수가 아닌 칸)을 이은 것 — 이름열수를 주면 그 수만큼.
    병합으로 복사된 이름 칸도 쓴다(「구분」 병합 행이 줄마다 이름을 갖게)."""
    낸 = []
    for i in range(표["머리줄수"], 표["줄수"]):
        r = 표["격자"][i]
        if 이름열수 is None:
            k = 0
            while k < len(r) and not _수칸인가(r[k]) and k < len(r) - 1:
                k += 1
            if k == 0:
                k = 1
        else:
            k = 이름열수
        이름 = " ".join(dict.fromkeys(c for c in r[:k] if c))
        낸.append((이름, r[k:], i))
    return 낸


def 열찾기(표, 정규식, 시작=0):
    """열 이름(빈칸 뺀 글)이 정규식에 걸리는 첫 열 번호(시작 열부터). 없으면 None."""
    r = re.compile(정규식)
    for j, x in enumerate(표["열이름"]):
        if j >= 시작 and r.search(표준(x)):
            return j
    return None


def 열들찾기(표, 정규식):
    r = re.compile(정규식)
    return [j for j, x in enumerate(표["열이름"]) if r.search(표준(x))]


def 칸수(표, i, j, 복사포함=False):
    """(i, j) 칸의 수 — 병합 복사 칸은 None(복사포함 = True 면 그대로)."""
    if i >= 표["줄수"] or j is None or j >= 표["열수"]:
        return None
    if 표["병합"][i][j] and not 복사포함:
        return None
    return 수(표["격자"][i][j])


def 단위배수(u):
    return _단위배.get((u or "").replace(" ", ""), None)


def 곁XML(txt경로):
    """원문 txt 경로 → 같은 이름의 XML 경로(없으면 None). 「…/20260812000829.txt」 → 「…/20260812000829.xml」."""
    if not txt경로:
        return None
    p = re.sub(r"\.txt(\.gz)?$", ".xml", txt경로)
    return p if p != txt경로 and os.path.exists(p) else None

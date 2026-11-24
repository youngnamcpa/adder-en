# -*- coding: utf-8 -*-
"""신고서재무_국내 — 국내 신고서 · 투자설명서 · 분할회사 공시에서 **감사받은 연간 재무**를 읽어 「신고서재무/1」 꼴로 (2026-10-25 Y1 국내 갈래).

왜 만들었나 — 설계 `연구/재무이력없음_20261025/02_설계.md` 2-1
  정기보고서(사업보고서)에 연간 재무가 3해 미만인 회사(상장 직후 · 분할 신설)는 감사받은 이력이 신고서 · 투자설명서와 분할회사 감사보고서
  주석에 있다. `dart_fetch.py --신고서` 가 그 원문을 `_raw/신고서/<접수번호>/` 에 받고 무엇을 왜 골랐는지 `_raw/dart_신고서고르기.json` 에 적는다.
  이 도구는 그 원문을 **`공시표.py` 격자로** 읽는다(txt 로 읽지 않는다 — 병합 칸이 밀린다).

읽는 것
  ① 대상 자신의 증권신고서(지분증권) · 투자설명서 「재무에 관한 사항」 — 요약재무정보(감사인 · 감사의견 · 기간 줄이 든 표)와 연결재무제표 표
     (감사의견이 적정 · 한정인 12개월 열만 「감사」, 중간 열은 「미감사 중간」 — 검토 기관은 따로 적는다)
  ② 분할 신고서 · 투자설명서의 분할 대상 사업부문 재무(매출액 · 영업손익 · 당기순이익 · 자산총계 표) — 「검토」(재상장 요건표의 검토 기관이
     있을 때) 또는 「경영진 배부」 · `참고이력: true` · 배부 기준 문장과 검토 기관을 근거에
  ③ 분할회사 감사보고서 주석의 분할 · 중단영업 — 중단영업 손익 · 현금흐름(당기 · 전기)과 소유주 분배 자산 · 부채(감사 · 원천종류 「분할회사 주석」 ·
     보고실체 = 분할 대상 사업)
  ④ 대상 자신의 사업보고서 연간(원천종류 「정기」) — `dart_fetch` 의 앵커 시계열(fnlttSinglAcntAll) · 짧은 첫 사업연도는 `개월` 로 표시
     (기간은 사업보고서 원문의 기간 칸 · 「…부터 …까지」 문장 · 기업개황 설립일 차례로 정한다)
  ⑤ 보고실체변화(분할 · 공통지배 · 사업결합 · 주식분할 — 원문 문장) ⑥ 검산(자산 = 부채 + 자본 · 매출 − 비용 = 영업이익 · 부문 매출 합 = 매출)

규칙(계약 「신고서재무/1」 — `연구/재무이력없음_20261025/03_Y1계약.md`)
  · 값은 원문 표에서만. 괄호는 음수. 표의 「(단위 : 원)」 을 읽어 백만원으로 맞춘다(작은 단위에서 오면 백만원 정수로 반올림 — 원문 값 · 단위는 원표에)
  · 표준 줄은 원문 줄 이름의 낱말로 짝짓고 짝지은 원문 줄 이름을 근거에 남긴다. 못 짝지은 표준 줄은 비우고 확인불가에
  · 검산이 어긋나면 값을 고치지 않고 `판정: 어긋남` 과 차를 적는다
  · 회사 · 업종 이름은 이 도구에 없다(범용)

명령
  python 스크립트/신고서재무_국내.py --raw _raw --기준일 2026-06-30 [--출력 _raw/신고서재무.json] [--조회일 YYYY-MM-DD]
종료 코드 — 0 통과 · 1 발견(읽을 서류 없음 · 검산 어긋남) · 2 입력오류.

공통 함수(기간 id 짓기 · 표준 줄 이름 · 검산 · 저장)는 미국 갈래의 `신고서재무.py` 에 둘 예정이다 — 이 파일 안의 같은 이름 함수
(`기간id` · `표준줄들` · `검산짓기` · `저장`)는 그 전까지의 임시 판이다(본선이 합친다).
"""
from __future__ import annotations

import argparse
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
import 공시표 as 표도구  # noqa: E402
from 종료코드 import 통과, 발견, 입력오류  # noqa: E402

형식 = "신고서재무/1"
출력파일 = "신고서재무.json"
고르기파일 = "dart_신고서고르기.json"

# ══════════════════════════════════════════════════════════ 공통(임시 — 신고서재무.py 로 옮길 것)

표준줄들 = ("매출", "매출원가", "연구개발비", "판매비와관리비", "영업이익", "이자비용", "법인세차감전이익", "법인세비용", "당기순이익",
         "감가상각비", "영업활동현금흐름", "유형자산취득", "자산총계", "부채총계", "자본총계", "현금및현금성자산", "차입금")
_시점줄 = ("자산총계", "부채총계", "자본총계", "현금및현금성자산", "차입금")


def _날(s):
    return datetime.date.fromisoformat(s)


def 개월수(시작, 끝):
    """「2024-03-01」 ~ 「2024-12-31」 → 10. 날 수를 평균 달 길이로 나눠 반올림."""
    return int(round(((_날(끝) - _날(시작)).days + 1) / 30.436875))


def 기간id(시작, 끝, 접미=None, 연간=None, 결산월=12):
    """기간 id 는 공통 함수 `신고서재무.기간id` 하나로 짓는다(2026-10-25 본선 — 두 갈래의 판을 하나로). 여기는 (시작, 끝) 을 개월 수로 바꿔 넘기는 감싸개다.
    국내 결산월이 12월이 아니면 `결산월` 을 준다(분기 번호를 결산월에서 센다)."""
    import 신고서재무 as 공                                  # noqa: PLC0415 — 늦게(서로 부르는 두 모듈)
    return 공.기간id(끝, 개월수(시작, 끝), 접미 or "", 연말월=결산월, 연간=bool(연간))


def 저장(결과, 경로):
    """공통 `신고서재무.저장`(쓰는 중 파일 → 바꿔 넣기)을 부른다."""
    import 신고서재무 as 공                                  # noqa: PLC0415
    return 공.저장(결과, os.path.dirname(os.path.abspath(경로)), 경로)


# ══════════════════════════════════════════════════════════ 원문 줄 이름 → 표준 줄

def 이름꼴(s):
    """원문 줄 이름의 대조 꼴 — 앞 기호(ㆍ · [ ] · 번호 머리) · 「(손실)」 꼴 · 「(주N)」 · 빈칸을 뗀다."""
    s = (s or "").strip()
    s = re.sub(r"^[\[\]ㆍ·•\-\s]+|[\[\]\s]+$", "", s)
    s = re.sub(r"^\s*(?:[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+\s*[\.．]?|[IVX]+\s*[\.．]|\d+\s*[\.．\)]|[가-하]\s*[\.．\)]|\(\s*[\d가-하]+\s*\))\s*", "", s)
    s = re.sub(r"\((?:주|주석)\s*[\d,\s]*\)", "", s)
    s = re.sub(r"\((?:손실|이익|수익|비용|손익)\)", "", s)
    return re.sub(r"\s+", "", s)


_짝 = [   # (표준 줄, 대조 꼴 정규식, 표 종류 — None 이면 어느 표든)
    ("매출", r"(?:매출액|영업수익|수익\(매출액\)|매출|매출액합계|영업수익합계)", ("손익",)),
    ("매출원가", r"매출원가", ("손익",)),
    ("연구개발비", r"(?:경상)?연구개발비", ("손익",)),
    ("판매비와관리비", r"판매비(?:와|및)관리비|판관비", ("손익",)),
    ("영업이익", r"영업(?:이익|손익|손실)", ("손익",)),
    ("이자비용", r"이자비용", ("손익",)),
    ("법인세차감전이익", r"(?:법인세(?:비용)?차감전|세전)(?:계속영업|중단영업)?순?(?:이익|손익|손실)", ("손익",)),
    ("법인세비용", r"법인세(?:비용|수익)", ("손익",)),
    ("당기순이익", r"(?:연결)?(?:당기|분기|반기)?순(?:이익|손익|손실)|세후중단영업순(?:이익|손익|손실)", ("손익",)),
    ("감가상각비", r"(?:유형자산)?감가상각비", ("손익", "현금흐름")),
    ("영업활동현금흐름", r"영업활동(?:으로인한|으로부터의|에서의)?순?현금흐름", ("현금흐름",)),
    ("유형자산취득", r"유형자산(?:의)?(?:취득|증가)", ("현금흐름",)),
    ("자산총계", r"자산총계", ("재무상태",)),
    ("부채총계", r"부채총계", ("재무상태",)),
    ("자본총계", r"자본총계", ("재무상태",)),
    ("현금및현금성자산", r"현금및현금성자산", ("재무상태",)),
]
_차입금꼴 = re.compile(r"^(?:단기|장기|유동성장기|유동성)?(?:차입금|사채)$")
_영업비용꼴 = re.compile(r"^영업비용$")


def 표준줄짝(이름, 표종류):
    """원문 줄 이름 → 표준 줄 | None(차입금은 합이라 따로 — `_차입금꼴`)."""
    k = 이름꼴(이름)
    for 줄, 꼴, 종류들 in _짝:
        if 표종류 and 종류들 and 표종류 not in 종류들:
            continue
        if re.fullmatch(꼴, k):
            return 줄
    return None


# ══════════════════════════════════════════════════════════ 결과 그릇

class 그릇:
    """기간 · 표준줄 · 원표 · 근거 · 검산재료를 모은다. 값은 백만원(float — 낼 때 반올림)."""

    def __init__(self):
        self.기간 = {}
        self.줄 = {k: {} for k in 표준줄들}
        self.근거 = {}
        self.원표 = {"손익": [], "현금흐름": [], "재무상태": [], "부문": []}
        self.영업비용 = {}                                  # 검산 재료(원표에도 실린다)
        self.차입금줄 = {}                                  # 기간 → [(이름, 값)]
        self.경보 = []
        self.확인불가 = []
        self.보고실체변화 = []

    def 기간더하기(self, k, 시작, 끝, 감사구분, 원천종류, 보고실체, 참고이력=False, **덧):
        if k in self.기간:
            return k
        d = {"id": k, "시작": 시작, "끝": 끝, "개월": 개월수(시작, 끝) if 시작 and 끝 and 시작 <= 끝 else 0,
             "감사구분": 감사구분, "원천종류": 원천종류, "보고실체": 보고실체, "참고이력": bool(참고이력)}
        d.update({a: b for a, b in 덧.items() if b is not None})
        self.기간[k] = d
        return k

    def 값(self, 줄, k, v, 출처, 기준일, 확인상태, 원문줄):
        if v is None:
            return
        옛 = self.줄[줄].get(k)
        if 옛 is not None:
            if abs(옛 - v) > 1:
                self.경보.append("%s %s — 두 원천 값이 다르다(%s ↔ %s · 먼저 읽은 값을 둔다) — %s" % (줄, k, _표시(옛), _표시(v), 출처))
            return
        self.줄[줄][k] = v
        self.근거.setdefault(줄, {})[k] = {"출처": 출처, "기준일": 기준일, "확인상태": 확인상태, "원문줄": 원문줄}

    def 원표줄(self, 표이름, 줄이름, 값들, 원문단위, 부문=None, 출처=None):
        것 = {"줄": 줄이름, "값": {k: _정수(v) for k, v in 값들.items()}, "원문단위": 원문단위}
        if 출처:
            것["출처"] = 출처
        if 부문:
            것 = dict({"부문": 부문}, **것)
            self.원표["부문"].append(것)
        else:
            self.원표[표이름].append(것)


def _정수(v):
    return None if v is None else int(round(v))


def _표시(v):
    return "{:,.0f}".format(v) if v is not None else "-"


def _배수(단위):
    """표 단위 → 백만원으로 나눌 수(원 1e6 · 천원 1e3 · 백만원 1 · 억원 0.01). 모르는 단위는 None."""
    b = 표도구.단위배수(단위 or "")
    return None if b is None else 1e6 / b


# ══════════════════════════════════════════════════════════ 날짜 · 기간 글

_날글 = r"(20\d\d|19\d\d)\s*[년.\-/]\s*(\d{1,2})\s*[월.\-/]\s*(\d{1,2})\s*일?"


def _iso(y, m, d):
    try:
        return datetime.date(int(y), int(m), int(d)).isoformat()
    except ValueError:
        return None


def _달끝(y, m):
    d = datetime.date(int(y) + (int(m) // 12), int(m) % 12 + 1, 1) - datetime.timedelta(days=1)
    return d.isoformat()


def _앞달첫날(끝, n):
    """끝 날이 든 달에서 n − 1 달 앞 달의 첫날 — 「2026-03-31」 · 3 → 「2026-01-01」, 「2025-12-31」 · 12 → 「2025-01-01」."""
    e = _날(끝)
    m = e.year * 12 + (e.month - 1) - (n - 1)
    return datetime.date(m // 12, m % 12 + 1, 1).isoformat()


def 기수기간들(글들):
    """「제13(당)기 1분기 2026년 01월 01일부터 2026년 03월 31일까지」 · 「제12(전)기 기말 2025년 12월 31일 현재」 →
    {(기수, 구분): {"시작", "끝"} | {"시점"}} — 구분은 「1분기 · 반기 · 3분기」 또는 「연」."""
    낸 = {}
    꼴 = re.compile(r"제\s*(\d+)\s*(?:\(\s*(?:당|전|전전)\s*\))?\s*기\s*(1\s*분기|반기|3\s*분기)?\s*(?:말|기말)?\s*:?\s*" + _날글 +
                   r"\s*(?:(부터)\s*" + _날글 + r"\s*까지|현재)")
    for t in 글들:
        for m in 꼴.finditer(t or ""):
            기수, 구분 = int(m.group(1)), re.sub(r"\s+", "", m.group(2) or "") or "연"
            a = _iso(m.group(3), m.group(4), m.group(5))
            if m.group(6):
                b = _iso(m.group(7), m.group(8), m.group(9))
                낸.setdefault((기수, 구분), {})["시작"], 낸[(기수, 구분)]["끝"] = a, b
            else:
                낸.setdefault((기수, 구분), {})["시점"] = a
    return 낸


def 머리기수(머리):
    """열 머리 「제 13(당) 1분기말」 · 「제 12(전) 기말」 · 「2026년 1분기(제 13기)」 → (기수, 구분) | None."""
    s = re.sub(r"\s+", "", 머리 or "")
    m = re.search(r"제(\d+)(?:\((?:당|전|전전)\))?기?(1분기|반기|3분기)?", s)
    if not m:
        return None
    구분 = m.group(2)
    if not 구분:
        구분 = "1분기" if "1분기" in s else "반기" if "반기" in s else "3분기" if "3분기" in s else "연"
    return int(m.group(1)), 구분


# ══════════════════════════════════════════════════════════ 표 읽기 도우미

def 수(c):
    """칸 글 → 수. **괄호는 음수**(「(7,722)」 → −7722) · 「△」 · 「-」 앞 = 음수 · 「-」 한 글자 = 0 · 수가 아니면 None.
    (`공시표.수` 는 안쪽 선택 괄호가 닫는 괄호를 먹어 「(3,122)」 를 3122 로 읽는다 — 2026-10-25 실측 · 본선에 보고 · 고칠 때까지 이 함수를 쓴다)"""
    if c is None:
        return None
    s = re.sub(r"\s+", "", c)
    if s in ("-", "－", "—", "–"):
        return 0.0
    m = re.fullmatch(r"([(（])?([△\-－])?([0-9][0-9,]*(?:\.[0-9]+)?)([)）])?%?", s)
    if not m or bool(m.group(1)) != bool(m.group(4)):
        return None
    v = float(m.group(3).replace(",", ""))
    return -v if (m.group(1) or m.group(2)) else v


def 칸수(표, i, j):
    """(i, j) 칸의 수 — 병합으로 복사된 칸은 None."""
    if i >= 표["줄수"] or j is None or j >= 표["열수"] or 표["병합"][i][j]:
        return None
    return 수(표["격자"][i][j])


def 표종류(표):
    """표 앞글 · 제목으로 재무상태 · 손익 · 현금흐름 · 자본변동 · None."""
    글 = 표도구.표준(" ".join(표["앞글"][-4:] + 표["제목경로"][-1:] + ([표.get("주석")] if 표.get("주석") else [])))
    if re.search(r"자본변동표", 글):
        return "자본변동"
    if re.search(r"현금흐름표", 글):
        return "현금흐름"
    if re.search(r"손익계산서", 글):
        return "손익"
    if re.search(r"재무상태표|대차대조표", 글):
        return "재무상태"
    return None


def 열무리(표, 시작열=1):
    """열 머리가 같은 이웃 열을 한 무리로 — 「제 13(당) 1분기 | 제 13(당) 1분기」 두 칸 꼴(소계 칸 · 합계 칸). → [(머리, [열 …])]."""
    낸 = []
    for j in range(시작열, 표["열수"]):
        이름 = 표["열이름"][j]
        if 표도구.표준(이름) in ("주석", "주", "비고"):
            continue
        if 낸 and 낸[-1][0] == 이름 and 낸[-1][1][-1] == j - 1:
            낸[-1][1].append(j)
        else:
            낸.append((이름, [j]))
    return 낸


def 무리값(표, i, 열들):
    """한 줄 · 한 열 무리의 값 — 무리 안 수 칸 가운데 마지막(합계 칸). 병합 복사 칸은 건너뛴다."""
    v = None
    for j in 열들:
        x = 칸수(표, i, j)
        if x is not None and re.search(r"\d", 표["격자"][i][j] or ""):
            v = x
    return v


def _출처(서류, 표, 줄이름=None):
    제 = " > ".join(표["제목경로"][-2:]) or (표.get("주석") or "")
    머 = (표.get("주석") or "") if 표.get("주석") and 표.get("주석") not in 제 else ""
    return "%s · %s%s%s" % (서류["접수번호"], 제, (" · " + 머[:60]) if 머 else "", (" · 「%s」" % 줄이름) if 줄이름 else "")


def _발췌(t, 꼴, 앞=20, 뒤=50):
    m = re.search(꼴, t or "")
    if not m:
        return None
    a = max(0, m.start() - 앞)
    return re.sub(r"\s+", " ", t[a:m.end() + 뒤]).strip()


# ══════════════════════════════════════════════════════════ ① 대상 자신의 신고서 — 요약재무정보 · 재무제표

def _감사의견들(문):
    """{기수: {"감사인", "의견"}} — 요약재무정보의 「감사인 · 감사의견」 줄과 「회계감사인의 명칭 및 감사의견」 표에서."""
    낸 = {}
    for 표 in 문["표"]:
        for i in range(표["줄수"]):
            r = 표["격자"][i]
            if not r:
                continue
            m = re.match(r"^제(\d+)기", 표도구.표준(r[0]))
            if m and len(r) >= 3 and re.search(r"회계법인|감사반|회계사", " ".join(r[1:3])):
                의 = next((c for c in r[2:] if re.search(r"적정|한정|부적정|의견거절|검토", c or "")), None)
                if 의:
                    인 = next((c for c in r[1:3] if re.search(r"회계법인|감사반|회계사", c or "")), r[1])
                    낸.setdefault(int(m.group(1)), {"감사인": 인, "의견": re.sub(r"\s+", "", 의)[:10]})
    return 낸


def 요약재무읽기(문, 서류, 그, 별도도=False):
    """「요약 (연결)재무정보」 표 — 열마다 기간(손익 줄의 「YYYY년 M월~M월」 · 머리의 「YYYY년 1분기(제 N기)」) · 감사인 · 감사의견 줄 → 기간 · 표준줄.
    연결 표가 있으면 연결만 읽는다(별도는 별도도 = True 일 때). → 읽은 기간 id 목록."""
    표들 = [t for t in 문["표"] if re.search(r"요약\s*연결\s*재무\s*정보", 표도구.맥락(t, 4))]
    연결 = True
    if not 표들:
        표들 = [t for t in 문["표"] if re.search(r"요약\s*(?:별도\s*)?재무\s*정보", 표도구.맥락(t, 4))]
        연결 = False
    읽은 = []
    for 표 in 표들[:1] if not 별도도 else 표들:
        배 = _배수(표["단위"])
        if 배 is None:
            그.경보.append("요약재무정보 표의 단위를 못 읽었다(%s) — 건너뛴다" % _출처(서류, 표))
            continue
        줄이름 = [(i, 표["격자"][i][0]) for i in range(표["머리줄수"], 표["줄수"])]
        모든줄 = [(i, 표["격자"][i][0]) for i in range(표["줄수"])]          # 「감사인」 줄은 머리에 들기도 한다

        def 줄값(정규식, j):
            for i, n in 모든줄:
                if re.search(정규식, 표도구.표준(n)):
                    return 표["격자"][i][j]
            return None
        for j in range(1, 표["열수"]):
            머 = 표["열이름"][j]
            ym = re.search(r"(20\d\d)\s*년", 머)
            if not ym:
                continue
            y = int(ym.group(1))
            기수 = 머리기수(머)
            손 = 줄값(r"손익계산서", j) or ""
            rm = re.search(r"(?:(20\d\d)\s*년\s*)?(\d{1,2})\s*월\s*[~\-－]\s*(?:(20\d\d)\s*년\s*)?(\d{1,2})\s*월", 손)
            if rm:
                시작 = _iso(rm.group(1) or y, rm.group(2), 1)
                끝 = _달끝(rm.group(3) or y, rm.group(4))
            else:
                n = 3 if "1분기" in 머 else 6 if "반기" in 머 else 9 if "3분기" in 머 else 12
                시작, 끝 = _iso(y, 1, 1), _달끝(y, n)
            의견 = 표도구.표준(줄값(r"^감사의견$", j) or "")
            감사인 = (줄값(r"^감사인$", j) or "").strip() or None
            n = 개월수(시작, 끝)
            if n >= 12 and re.search(r"적정|한정", 의견) and not re.search(r"부적정", 의견):
                구분 = "감사"
            elif n >= 12:
                구분 = "미감사" if 의견 else "확인 불가"
            else:
                구분 = "미감사 중간"
            k = 기간id(시작, 끝)
            그.기간더하기(k, 시작, 끝, 구분, "신고서", "대상 %s 재무제표(신고서 요약재무정보)" % ("연결" if 연결 else "별도"),
                       감사인=감사인, 감사의견=의견 or None, 기수=기수[0] if 기수 else None,
                       검토기관=(감사인 if "검토" in 의견 else None))
            읽은.append(k)
            확 = "감사(신고서)" if 구분 == "감사" else "%s(신고서)" % 구분
            for i, n0 in 줄이름:
                v = 칸수(표, i, j)
                if v is None or not re.search(r"\d", 표["격자"][i][j] or "") or "단위:원" in 표도구.표준(n0) or "주당" in n0:
                    continue
                v = v / 배
                for 종 in ("손익", "재무상태"):
                    줄 = 표준줄짝(n0, 종)
                    if 줄:
                        그.값(줄, k, v, _출처(서류, 표, n0), 끝, 확, n0)
                        break
                if _영업비용꼴.match(이름꼴(n0)):
                    그.영업비용.setdefault(k, v)
    return 읽은


def 재무제표읽기(문, 서류, 그, 감사의견):
    """「2. 연결재무제표」(없으면 「4. 재무제표」) 절의 재무상태표 · 손익계산서 · 현금흐름표 — 열 머리의 기수 · 분기를 앞글의
    「제N기 … 부터 … 까지 / 현재」 에 대 기간을 정한다. → 읽은 기간 id 목록."""
    절표 = [t for t in 문["표"] if any(re.search(r"연결\s*재무\s*제표$", x) for x in t["제목경로"][-1:])]
    연결 = True
    if not 절표:
        절표 = [t for t in 문["표"] if any(re.search(r"^\d+\.\s*재무\s*제표$", x) for x in t["제목경로"][-1:])]
        연결 = False
    읽은 = []
    for 표 in 절표:
        종 = 표종류(표)
        if 종 not in ("재무상태", "손익", "현금흐름"):
            continue
        배 = _배수(표["단위"])
        if 배 is None:
            continue
        기간들 = 기수기간들(표["앞글"])
        for 머, 열들 in 열무리(표):
            키 = 머리기수(머)
            if not 키:
                continue
            p = 기간들.get(키) or (기간들.get((키[0], "연")) if 키[1] == "연" else None)
            if not p:
                continue
            if 종 == "재무상태":
                끝 = p.get("시점") or p.get("끝")
                if not 끝:
                    continue
                # 시점의 기간 id — 그 시점에서 끝나는 흐름 기간(연 12 · 1분기 3 · 반기 6 · 3분기 9개월)의 id 를 쓴다
                시작 = _앞달첫날(끝, {"1분기": 3, "반기": 6, "3분기": 9}.get(키[1], 12))
            else:
                시작, 끝 = p.get("시작"), p.get("끝")
                if not (시작 and 끝):
                    continue
            k = 기간id(시작, 끝)
            n = 개월수(시작, 끝)
            의 = 감사의견.get(키[0]) or {}
            if k not in 그.기간:
                구분 = "감사" if (n >= 12 and re.search(r"적정|한정", 의.get("의견") or "") and "부적정" not in (의.get("의견") or "")) else \
                    ("미감사 중간" if n < 12 else "확인 불가")
                if re.search(r"검토\s*받지\s*않은|감사\s*받지\s*않은", 머):
                    구분 = "미감사 중간" if n < 12 else "미감사"
                그.기간더하기(k, 시작, 끝, 구분, "신고서", "대상 %s 재무제표(신고서)" % ("연결" if 연결 else "별도"), 기수=키[0],
                           감사인=(의.get("감사인") if n >= 12 else None))
            읽은.append(k)
            구분 = 그.기간[k]["감사구분"]
            확 = "감사(신고서)" if 구분 == "감사" else "%s(신고서)" % 구분
            값들 = {}
            for i in range(표["머리줄수"], 표["줄수"]):
                n0 = 표["격자"][i][0]
                v = 무리값(표, i, 열들)
                if v is None:
                    continue
                v = v / 배
                줄 = 표준줄짝(n0, 종)
                if 줄:
                    그.값(줄, k, v, _출처(서류, 표, n0), 끝, 확, n0)
                if 종 == "재무상태" and _차입금꼴.match(이름꼴(n0)):
                    그.차입금줄.setdefault(k, []).append((n0, v, _출처(서류, 표, n0), 끝, 확))
                if 종 == "손익" and _영업비용꼴.match(이름꼴(n0)):
                    그.영업비용.setdefault(k, v)
                값들[n0] = v
    return sorted(set(읽은))


# ══════════════════════════════════════════════════════════ ② 분할 신고서 · 투자설명서 — 분할 대상 부문

_부문표꼴 = r"분할\s*(?:신설|대상).{0,20}사업\s*부문.{0,30}매출액"


def _검토기관들(문):
    """재상장 요건표 등 「2023년 반기: 검토 (안진회계법인)」 꼴 → {(해, 반기냐): (구분, 기관)}."""
    낸 = {}
    글들 = [" ".join(r) for t in 문["표"] for r in t["격자"]] + [t for _p, t in 문["글"]]
    for t in 글들:
        for m in re.finditer(r"(20\d\d)\s*년\s*(반기|1분기|3분기)?\s*[:：]\s*(검토|감사)\s*\(\s*([^)]+?)\s*\)", t):
            낸.setdefault((int(m.group(1)), m.group(2) or ""), (m.group(3), m.group(4)))
    return 낸


def _배부기준(문):
    """배부 · 배분 기준 문장(짧게) | None."""
    for _p, t in 문["글"]:
        if re.search(r"배부\s*(?:및\s*손익\s*배분\s*)?기준", t) and re.search(r"경영진|직접\s*귀속|배부", t):
            s = _발췌(t, r"직접\s*귀속되지\s*않는\s*항목은.{0,40}?(?:에\s*따라|으로)\s*배부", 0, 0) or _발췌(t, r"배부\s*기준", 10, 60)
            return s
    return None


def 분할부문읽기(문, 서류, 그):
    """분할 신고서 · 투자설명서의 분할 대상 부문 표 → 기간(「_분할부문」 · 참고이력) · 표준줄 · 원표 부문. → 읽은 기간 id 목록."""
    표들 = [t for t in 문["표"] if re.search(_부문표꼴, 표도구.맥락(t, 4)) and any(re.search(r"20\d\d\s*년", x) for x in t["열이름"])]
    if not 표들:
        return []
    표 = 표들[0]
    배 = _배수(표["단위"])
    if 배 is None:
        그.경보.append("분할 부문 표의 단위를 못 읽었다 — %s" % _출처(서류, 표))
        return []
    검토 = _검토기관들(문)
    배부 = _배부기준(문)
    기준글 = " ".join(표["뒷글"][:2])
    별도 = "별도" if re.search(r"별도\s*재무\s*제표", 기준글) else ("연결" if re.search(r"연결\s*재무\s*제표", 기준글) else "기준 미기재")
    부문이름 = None
    for 글 in reversed(표["앞글"]):
        m = re.search(r"\[\s*(분할\s*신설\s*회사[^\]]*)\]", 글)
        if m:
            부문이름 = re.sub(r"\s+", " ", m.group(1)).strip()
            break
    부문 = "분할 대상 사업부문(%s · %s 재무제표 기초)" % (부문이름 or "분할신설회사", 별도)
    읽은, 열기간 = [], {}
    for j in range(1, 표["열수"]):
        머 = 표["열이름"][j]
        ym = re.search(r"(20\d\d)\s*년\s*(반기|1분기|3분기)?", 머)
        if not ym:
            continue
        y, 반 = int(ym.group(1)), ym.group(2) or ""
        n = {"반기": 6, "1분기": 3, "3분기": 9}.get(반, 12)
        시작, 끝 = _iso(y, 1, 1), _달끝(y, n)
        구분, 기관 = 검토.get((y, 반)) or (None, None)
        감사구분 = "검토" if 구분 == "검토" else ("경영진 배부" if not 구분 else "검토")
        k = 기간id(시작, 끝, "분할부문", 연간=(n == 12))
        그.기간더하기(k, 시작, 끝, 감사구분, "신고서", 부문, 참고이력=True, 검토기관=기관, 배부기준=배부, 재무제표기준=별도)
        열기간[j] = k
        읽은.append(k)
    for i in range(표["머리줄수"], 표["줄수"]):
        n0 = 표["격자"][i][0]
        값들 = {}
        for j, k in 열기간.items():
            v = 칸수(표, i, j)
            if v is None or not re.search(r"\d", 표["격자"][i][j] or ""):
                continue
            v = v / 배
            값들[k] = v
            줄 = 표준줄짝(n0, "손익") or 표준줄짝(n0, "재무상태")
            if 줄:
                p = 그.기간[k]
                확 = "%s(분할 신고서 · 참고이력)%s" % (p["감사구분"], (" — " + p["검토기관"]) if p.get("검토기관") else "")
                그.값(줄, k, v, _출처(서류, 표, n0) + (" · 배부: " + 배부 if 배부 else ""), p["끝"], 확, n0)
        if 값들:
            그.원표줄("부문", n0, 값들, 표["단위"], 부문=부문, 출처=_출처(서류, 표))
    return 읽은


# ══════════════════════════════════════════════════════════ ③ 분할회사 감사보고서 주석 — 분할 · 중단영업

def _분할대상이름(글들):
    for t in 글들:
        m = re.search(r"분할\s*기일\s*로\s*(?:하여\s*)?(.{2,40}?사업\s*부문)\s*을\s*(?:단순\s*[ㆍ·]?\s*)?(?:인적|물적)?\s*분할", t) or \
            re.search(r"([^\s,.]{2,20}(?:\s*및\s*[^\s,.]{1,20})*\s*사업\s*부문)\s*을\s*(?:단순\s*[ㆍ·]?\s*)?(?:인적|물적)\s*분할", t)
        if m:
            return re.sub(r"\s+", " ", m.group(1)).strip()
    return None


def _분할기일(글들):
    셈 = {}
    for t in 글들:
        for m in list(re.finditer(_날글 + r"\s*(?:을|를)?\s*분할\s*기일", t)) + list(re.finditer(r"분할\s*기일\s*(?:인|은|:|：)?\s*" + _날글, t)):
            d = _iso(m.group(1), m.group(2), m.group(3))
            if d:
                셈[d] = 셈.get(d, 0) + 1
    return max(셈.items(), key=lambda kv: kv[1])[0] if 셈 else None


def 분할주석읽기(문, 서류, 그, 분할기일=None):
    """분할회사 (연결)감사보고서 주석의 분할 · 중단영업 표 → 기간(「_분할전」 · 감사 · 분할회사 주석) · 표준줄 · 원표. → 읽은 기간 id 목록."""
    주석표 = [t for t in 문["표"] if re.search(r"분할|중단\s*영업", t.get("주석") or "") or re.search(r"중단\s*영업", " ".join(t["앞글"][-2:]))]
    if not 주석표:
        return []
    주석글 = [t for p, t in 문["글"] if re.search(r"(?:인적|물적)\s*분할|중단\s*영업", t)]
    분할기일 = 분할기일 or _분할기일(주석글)                    # 대상 원문에서 찾은 분할기일(고르기 기록)이 먼저 — 분할회사 주석의 다른 분할(옛 분할 · 액면분할)에 끌리지 않게
    대상이름 = _분할대상이름(주석글)
    보고실체 = "분할 대상 사업%s — 분할회사 %s 중단영업(감사보고서 주석)" % (
        ("(%s)" % 대상이름) if 대상이름 else "", "연결" if re.search(r"연결", 문.get("문서이름") or "") else "별도")
    기 = 문.get("기간") or {}
    if not (기.get("시작") and 기.get("끝")):
        그.경보.append("분할회사 감사보고서의 보고 기간을 못 읽었다 — %s" % 서류["접수번호"])
        return []
    당시작, 당끝 = 기["시작"], 기["끝"]
    전시작 = _iso(int(당시작[:4]) - 1, int(당시작[5:7]), int(당시작[8:10]))
    전끝 = (_날(당시작) - datetime.timedelta(days=1)).isoformat()
    당끝분할 = (_날(분할기일) - datetime.timedelta(days=1)).isoformat() if 분할기일 and 당시작 <= 분할기일 <= 당끝 else 당끝
    열기간 = {"당기": (당시작, 당끝분할), "전기": (전시작, 전끝)}
    확 = "감사(분할회사 주석)"
    읽은 = []
    근거글 = _발췌(" ".join(주석글), r"사업\s*부문\s*을\s*(?:인적|물적)?\s*분할", 40, 30)
    for 표 in 주석표:
        배 = _배수(표["단위"])
        if 배 is None:
            continue
        이름들 = [표도구.표준(r[0]) for r in 표["격자"]]
        if any(re.search(r"영업수익|매출액", x) for x in 이름들) and any(re.search(r"영업(이익|손익)", x) for x in 이름들):
            종 = "손익"
        elif any(re.search(r"영업활동.*현금흐름", x) for x in 이름들):
            종 = "현금흐름"
        elif any(re.search(r"분배(자산|부채)|순자산장부금액", x) for x in 이름들):
            분배읽기(표, 서류, 그, 분할기일 or 당끝, 배, 보고실체, 확)
            continue
        else:
            continue
        열 = {}
        for j in range(1, 표["열수"]):
            머 = 표도구.표준(표["열이름"][j])
            for 이름, (a, b) in 열기간.items():
                if 머.startswith(이름) and (이름 != "전기" or not 머.startswith("전전기")):
                    k = 기간id(a, b, "분할전")
                    그.기간더하기(k, a, b, "감사", "분할회사 주석", 보고실체, 참고이력=False,
                               분할기일=분할기일, 근거문장=근거글)
                    열[j] = k
                    읽은.append(k)
        for i in range(표["머리줄수"], 표["줄수"]):
            n0 = 표["격자"][i][0]
            값들 = {}
            for j, k in 열.items():
                v = 칸수(표, i, j)
                if v is None or not re.search(r"\d", 표["격자"][i][j] or ""):
                    continue
                v = v / 배
                값들[k] = v
                줄 = 표준줄짝(n0, 종)
                if 줄:
                    그.값(줄, k, v, _출처(서류, 표, n0), 그.기간[k]["끝"], 확, n0)
                if 종 == "손익" and _영업비용꼴.match(이름꼴(n0)):
                    그.영업비용.setdefault(k, v)
            if 값들:
                그.원표줄(종, n0, 값들, 표["단위"], 출처=_출처(서류, 표))
    if 분할기일:
        그.보고실체변화.append({"해": 분할기일[:4], "종류": "분할", "내용": "분할기일 %s · 분할회사 %s · 떼어 낸 사업: %s — 대상은 이 날 신설됐고 그 앞 기간의 숫자는 "
                                                               "분할회사 안 부문의 숫자다" % (분할기일, (서류.get("제출인") or {}).get("이름") or "-",
                                                                                     대상이름 or "분할 대상 사업"),
                           "근거": "%s · %s" % (서류["접수번호"], 근거글 or "분할 주석")})
    return sorted(set(읽은))


def 분배읽기(표, 서류, 그, 시점, 배, 보고실체, 확):
    """소유주 분배 자산 · 부채 표 — 자산 구획 「합계」 = 자산총계 · 부채 구획 「합계」 = 부채총계 · 「순자산 장부금액」 = 자본총계."""
    k = "분배%s" % 시점
    그.기간더하기(k, 시점, 시점, "감사", "분할회사 주석", 보고실체 + " · 분할기일 분배 자산 · 부채", 참고이력=False)
    구획 = None
    값들 = {}
    for i in range(표["줄수"]):                                   # 머리 줄에 「소유주 분배자산」 구획 이름이 드는 꼴이 있어 0 줄부터 본다
        r = 표["격자"][i]
        n0 = 표도구.표준(r[0])
        if re.search(r"분배자산", n0):
            구획 = "자산"
            continue
        if re.search(r"분배부채", n0):
            구획 = "부채"
            continue
        v = next((칸수(표, i, j) for j in range(1, 표["열수"]) if 칸수(표, i, j) is not None and re.search(r"\d", r[j] or "")), None)
        if v is None:
            continue
        v = v / 배
        값들["%s:%s" % (구획 or "", r[0])] = v
        if re.fullmatch(r"합계", n0):
            줄 = "자산총계" if 구획 == "자산" else "부채총계" if 구획 == "부채" else None
        elif re.search(r"순자산장부금액", n0):
            줄 = "자본총계"
        else:
            줄 = 표준줄짝(r[0], "재무상태")
        if 줄:
            그.값(줄, k, v, _출처(서류, 표, ("%s 구획 " % 구획 if 구획 and 줄 in ("자산총계", "부채총계") else "") + r[0]), 시점, 확, r[0])
    for 이름, v in 값들.items():
        그.원표줄("재무상태", 이름, {k: v}, 표["단위"], 출처=_출처(서류, 표))


# ══════════════════════════════════════════════════════════ ④ 대상 자신의 사업보고서(정기)

_코드짝 = {
    "매출": ("ifrs-full_Revenue",), "매출원가": ("ifrs-full_CostOfSales",), "판매비와관리비": ("dart_TotalSellingGeneralAdministrativeExpenses",),
    "영업이익": ("dart_OperatingIncomeLoss",), "법인세차감전이익": ("ifrs-full_ProfitLossBeforeTax",),
    "법인세비용": ("ifrs-full_IncomeTaxExpenseContinuingOperations",), "당기순이익": ("ifrs-full_ProfitLoss",),
    "영업활동현금흐름": ("ifrs-full_CashFlowsFromUsedInOperatingActivities",), "유형자산취득": ("ifrs-full_PurchaseOfPropertyPlantAndEquipment",),
    "자산총계": ("ifrs-full_Assets",), "부채총계": ("ifrs-full_Liabilities",), "자본총계": ("ifrs-full_Equity",),
    "현금및현금성자산": ("ifrs-full_CashAndCashEquivalents",),
}
_표종류API = {"BS": "재무상태", "IS": "손익", "CIS": "손익", "CF": "현금흐름"}


def _정기기간후보(raw):
    """대상 사업보고서 원문(`raw/사업*/*.xml`)의 기간 칸 · 「…부터 …까지」 문장 → {끝: 시작}."""
    낸 = {}
    for p in sorted(glob.glob(os.path.join(raw, "사업*", "*.xml"))):
        문 = 표도구.읽기(p)
        if not 문:
            continue
        기 = 문.get("기간") or {}
        if 기.get("시작") and 기.get("끝"):
            낸.setdefault(기["끝"], 기["시작"])
        for _p, t in 문["글"]:
            for m in re.finditer(_날글 + r"\s*부터\s*" + _날글 + r"\s*까지", t):
                a, b = _iso(*m.group(1, 2, 3)), _iso(*m.group(4, 5, 6))
                if a and b and a < b:
                    낸.setdefault(b, a)
    return 낸


def 정기읽기(raw, 그, 개황):
    """`raw/dart_앵커시계열.json`(없으면 `dart_재무_연결_YYYY_11011.json`)의 연간 → 기간 FY{y}A(원천종류 정기 · 짧은 첫 기는 개월).
    → 읽은 기간 id 목록."""
    해들 = []
    p = os.path.join(raw, "dart_앵커시계열.json")
    if os.path.exists(p):
        j = json.load(io.open(p, encoding="utf-8"))
        # 2026-10-25 Y2 — `이력판정.py --앵커에보태기` 가 보탠 해(`원천` 표지 — 신고서 · 분할회사 주석)는 정기가 아니다. 다시 읽으면
        # 보탠 값이 「정기」 로 되돌아와 셈이 제 꼬리를 문다(이력판정 갈래 실측) — 건너뛴다
        해들 = [(h["사업연도"], h.get("list") or [], h.get("재무구분") or "CFS") for h in j.get("해") or [] if not h.get("원천")]
    for q in glob.glob(os.path.join(raw, "dart_재무_연결_*_11011.json")):
        y = int(re.search(r"_(\d{4})_11011", q).group(1))
        if y not in {h[0] for h in 해들}:
            해들.append((y, (json.load(io.open(q, encoding="utf-8")) or {}).get("list") or [], "CFS"))
    if not 해들:
        return []
    후보 = _정기기간후보(raw)
    결산월 = int(("%s" % ((개황 or {}).get("acc_mt") or "12")).strip() or 12)
    설립 = (개황 or {}).get("est_dt") or ""
    설립 = _iso(설립[:4], 설립[4:6], 설립[6:8]) if re.fullmatch(r"\d{8}", 설립) else None
    읽은 = []
    for y, 목록, 구분 in sorted(해들):
        끝 = _달끝(y, 결산월)
        기본시작 = (_날(끝) - datetime.timedelta(days=364)).replace(day=1).isoformat() if 결산월 != 12 else _iso(y, 1, 1)
        시작, 출처 = 후보.get(끝), "사업보고서 원문 기간"
        if not 시작:
            if 설립 and 기본시작 < 설립 <= 끝:
                시작, 출처 = 설립, "기업개황 설립일(원문 기간 미확인)"
            else:
                시작, 출처 = 기본시작, "결산월 기준 12개월"
        k = 기간id(시작, 끝, 연간=True)
        n = 개월수(시작, 끝)
        그.기간더하기(k, 시작, 끝, "감사", "정기", "대상 %s 재무제표(사업보고서)%s" % ("연결" if 구분 == "CFS" else "별도",
                                                                 (" · 첫 사업연도 %d개월" % n) if n < 12 else ""),
                   기간출처=출처, 짧은기=(True if n < 12 else None))
        읽은.append(k)
        접 = next((it.get("rcept_no") for it in 목록 if it.get("rcept_no")), None) or "-"
        for it in 목록:
            종 = _표종류API.get((it.get("sj_div") or "").strip())
            if not 종:
                continue
            s = (it.get("thstrm_amount") or "").replace(",", "").strip()
            if not s or s in ("-", "--"):
                continue
            try:
                v = float(s) / 1e6
            except ValueError:
                continue
            이름 = (it.get("account_nm") or "").strip()
            코드 = (it.get("account_id") or "").strip()
            줄 = next((z for z, cs in _코드짝.items() if 코드 in cs and _짝종류(z, 종)), None) or 표준줄짝(이름, 종)
            출 = "%s · fnlttSinglAcntAll %s %d 사업보고서 · %s 「%s」%s" % (접, 구분, y, 종, 이름, (" (%s)" % 코드) if 코드.startswith(("ifrs", "dart")) else "")
            if 줄:
                그.값(줄, k, v, 출, 끝, "감사(정기)", 이름)
            if 종 == "재무상태" and _차입금꼴.match(이름꼴(이름)):
                그.차입금줄.setdefault(k, []).append((이름, v, 출, 끝, "감사(정기)"))
    return 읽은


def _짝종류(줄, 종):
    for z, _꼴, 종류들 in _짝:
        if z == 줄:
            return 종 in 종류들
    return True


# ══════════════════════════════════════════════════════════ ⑤ 보고실체변화(신고서 본문)

_변화꼴 = [(r"공통\s*지배", "공통지배 소급 결합"), (r"(?:액면|주식)\s*분할", "주식분할 소급"), (r"(?:인적|물적)\s*분할", "분할"),
         (r"사업\s*결합|흡수\s*합병|합병", "사업결합")]


def 보고실체변화찾기(문, 서류, 그):
    """신고서 「재무에 관한 사항」 · 회사 개요 문단의 공통지배 · 분할 · 사업결합 · 주식분할(액면분할) 문장 → 보고실체변화(해 · 종류 · 근거)."""
    본 = {(x["종류"], x["해"]) for x in 그.보고실체변화}
    for 경로, t in 문["글"]:
        자리 = " ".join(경로[-3:])
        if not re.search(r"재무|회사의\s*개요|연혁|일반\s*사항", 자리):
            continue
        for 꼴, 종류 in _변화꼴:
            m = re.search(꼴, t)
            if not m:
                continue
            앞 = t[max(0, m.start() - 80):m.end() + 40]
            ym = re.search(r"(20\d\d|19\d\d)\s*년", 앞)
            if not ym or "해당사항" in 앞 or "없습니다" in t[m.end():m.end() + 15]:
                continue
            키 = (종류, ym.group(1))
            if 키 in 본:
                continue
            본.add(키)
            그.보고실체변화.append({"해": ym.group(1), "종류": 종류, "내용": "%s 문장 — %s" % (종류, " > ".join(경로[-2:])),
                                "근거": "%s · %s" % (서류["접수번호"], re.sub(r"\s+", " ", 앞).strip()[:90])})
            break


# ══════════════════════════════════════════════════════════ ⑥ 검산 · 확인불가

def 검산짓기(그):
    """자산총계 = 부채총계 + 자본총계 · 매출 − 비용 = 영업이익(매출원가 + 판관비 또는 영업비용) · 부문 매출 합 = 매출. 차는 백만원."""
    낸 = []
    z = 그.줄
    for k in sorted(그.기간):
        a, b, c = z["자산총계"].get(k), z["부채총계"].get(k), z["자본총계"].get(k)
        if None not in (a, b, c):
            d = a - b - c
            낸.append({"항목": "자산총계 = 부채총계 + 자본총계", "기간": k, "차": round(d, 3), "판정": "통과" if abs(d) <= 1 else "어긋남"})
        매, 영 = z["매출"].get(k), z["영업이익"].get(k)
        if 매 is not None and 영 is not None:
            if k in 그.영업비용:
                비 = abs(그.영업비용[k])
                d, 식 = 매 - 비 - 영, "매출 − 영업비용 = 영업이익"
            elif z["매출원가"].get(k) is not None and z["판매비와관리비"].get(k) is not None:
                d, 식 = 매 - z["매출원가"][k] - z["판매비와관리비"][k] - 영, "매출 − 매출원가 − 판매비와관리비 = 영업이익"
            else:
                d = None
            if d is not None:
                낸.append({"항목": 식, "기간": k, "차": round(d, 3), "판정": "통과" if abs(d) <= 1 else "어긋남"})
    부문매출 = {}
    for r in 그.원표["부문"]:
        if 표준줄짝(r["줄"], "손익") == "매출":
            for k, v in r["값"].items():
                부문매출.setdefault(k, {})[r["부문"]] = v
    for k, 묶 in 부문매출.items():
        if len(묶) >= 2 and z["매출"].get(k) is not None:
            d = sum(묶.values()) - z["매출"][k]
            낸.append({"항목": "부문 매출 합 = 매출", "기간": k, "차": round(d, 3), "판정": "통과" if abs(d) <= 1 else "어긋남"})
    return 낸


def 부호맞추기(그):
    """부호 꼴을 하나로 — 원문 재무제표의 표시 꼴(미국 갈래와 같다): 유형자산취득은 현금흐름표 유출이라 음수, 법인세비용은 손익계산서 비용이라
    양수(세전 − 법인세비용 = 당기순이익이 되게). API(fnlttSinglAcntAll)는 유출을 양수로 주고 분할회사 주석은 차감 항목을 괄호로 적어 둘이 섞이므로
    맞춘다. 바꾼 자리는 근거의 「부호」 칸에 적는다."""
    for k, v in list(그.줄["유형자산취득"].items()):
        if v > 0:
            그.줄["유형자산취득"][k] = -v
            그.근거["유형자산취득"][k]["부호"] = "API 양수 → 현금흐름표 유출 표시(음수)"
    z = 그.줄
    for k, 법 in list(z["법인세비용"].items()):
        세, 순 = z["법인세차감전이익"].get(k), z["당기순이익"].get(k)
        if 세 is None or 순 is None:
            continue
        if abs(세 - 법 - 순) > 1 and abs(세 + 법 - 순) <= 1:
            z["법인세비용"][k] = -법
            그.근거["법인세비용"][k]["부호"] = "원문 표시(차감 괄호) → 비용 양수(세전 − 법인세비용 = 당기순이익)"
        elif abs(세 - 법 - 순) > 1:
            그.경보.append("%s — 법인세차감전이익 − 법인세비용 ≠ 당기순이익(차 %s · 중단영업 · 비지배 등 확인)" % (k, _표시(세 - 법 - 순)))


def 차입금합(그):
    for k, 줄들 in 그.차입금줄.items():
        if k in 그.줄["차입금"]:
            continue
        본 = {}
        for 이름, v, 출, 끝, 확 in 줄들:
            본.setdefault(이름꼴(이름), (이름, v, 출, 끝, 확))
        합 = sum(x[1] for x in 본.values())
        그.줄["차입금"][k] = 합
        첫 = next(iter(본.values()))
        그.근거.setdefault("차입금", {})[k] = {"출처": "%s — 합: %s" % (첫[2].rsplit(" · ", 1)[0], " + ".join(x[0] for x in 본.values())),
                                        "기준일": 첫[3], "확인상태": 첫[4], "원문줄": " + ".join(x[0] for x in 본.values())}


_대안 = {"정기": "사업보고서 원문 주석(성격별 비용 · 차입금 · 현금흐름표) — `dart_원천.py` · A2",
        "신고서": "신고서 「재무에 관한 사항」 의 연결재무제표 · 주석, 또는 같은 해 사업보고서 원문",
        "분할회사 주석": "분할회사 감사보고서 주석에 그 줄이 없다 — 분할 신고서의 부문 표(참고이력)나 대상 첫 사업보고서의 전기 칸"}


def 확인불가짓기(그):
    for k, p in sorted(그.기간.items()):
        if k.startswith("분배"):
            continue
        빈 = [z for z in 표준줄들 if k not in 그.줄[z] and not (p["개월"] == 0 and z not in _시점줄)]
        if p.get("참고이력") and p["원천종류"] == "신고서":
            원인, 대안 = "항목 부재", "분할 신고서 부문 표는 매출액 · 영업손익 · 당기순이익 · 자산총계 네 줄뿐 — 손익 상세 · 현금흐름은 분할회사 주석(중단영업)에서"
        else:
            원인, 대안 = "항목 부재", _대안.get(p["원천종류"], "-")
        if 빈:
            그.확인불가.append({"항목": "%s: %s" % (k, " · ".join(빈)), "원인": 원인, "대안": 대안})


# ══════════════════════════════════════════════════════════ 서류 찾기 · 읽기 입구

def _원문폴더(raw, 원문):
    s = (원문 or "").replace("\\", "/")
    if s.startswith("_raw/"):
        return os.path.join(raw, s[5:])
    return s if os.path.isabs(s) else os.path.join(raw, s)


def 서류목록(raw, 대상고유=None):
    """`dart_신고서고르기.json` 의 서류 → [서류 dict + "폴더"]. 없으면 `raw/신고서/*/` 를 훑어 문서 이름 · 제출인 고유번호로 가른다."""
    j = None
    p = os.path.join(raw, 고르기파일)
    if os.path.exists(p):
        j = json.load(io.open(p, encoding="utf-8"))
    낸 = []
    if j and j.get("서류"):
        for d in j["서류"]:
            낸.append(dict(d, 폴더=_원문폴더(raw, d.get("원문"))))
        return 낸, j
    for 폴더 in sorted(glob.glob(os.path.join(raw, "신고서", "*"))):
        접 = os.path.basename(폴더)
        주 = os.path.join(폴더, 접 + ".xml")
        if not os.path.exists(주):
            continue
        t = io.open(주, encoding="utf-8", errors="ignore").read(4000)
        이름 = 표도구.글정리((re.search(r"<DOCUMENT-NAME[^>]*>([^<]*)<", t) or [None, ""])[1])
        식 = (re.search(r'AREGCIK="(\d{8})"', t) or [None, None])[1]
        회 = 표도구.글정리((re.search(r"<COMPANY-NAME[^>]*>([^<]*)<", t) or [None, ""])[1])
        if re.search(r"사업보고서", 이름):
            역할 = "분할회사 사업보고서"
        elif re.search(r"분할", 이름) or (대상고유 and 식 and 식 != 대상고유):
            역할 = "분할 신고서"
        else:
            역할 = "대상 신고서"
        낸.append({"종류": 이름, "역할": 역할, "접수번호": 접, "제출인": {"이름": 회, "식별": 식}, "제출일": None,
                  "원문": "_raw/신고서/%s" % 접, "고른까닭": "고르기 기록 없음 — 폴더를 훑어 문서 이름으로 갈랐다", "폴더": 폴더})
    return 낸, None


def _폴더문서들(폴더, 접):
    """폴더의 XML → [(문서이름, 공시표 문)] — 연결감사보고서 · 감사보고서 · 본문 차례."""
    낸 = []
    for p in sorted(glob.glob(os.path.join(폴더, "*.xml"))):
        문 = 표도구.읽기(p)
        if 문:
            낸.append((문.get("문서이름") or "", 문))
    차례 = lambda x: (0 if re.search(r"연결감사보고서", x[0]) else 1 if re.search(r"감사보고서", x[0]) else 2)   # noqa: E731
    return sorted(낸, key=차례)


def 읽기(raw, 기준일, 조회일=None):
    """`raw`(회차 `_raw`) · 평가기준일 → 「신고서재무/1」 dict. 네트워크 0."""
    raw = os.path.abspath(raw)
    개황 = {}
    p = os.path.join(raw, "dart_기업개황.json")
    if os.path.exists(p):
        개황 = json.load(io.open(p, encoding="utf-8")) or {}
    서류들, 고르기 = 서류목록(raw, 개황.get("corp_code"))
    그 = 그릇()
    분할기일 = ((고르기 or {}).get("분할") or {}).get("분할기일")
    낸서류 = []
    for d in 서류들:
        폴더 = d.get("폴더")
        if not 폴더 or not os.path.isdir(폴더):
            그.경보.append("서류 %s 의 원문 폴더가 없다(%s)" % (d.get("접수번호"), d.get("원문")))
            continue
        낸서류.append({k: d.get(k) for k in ("종류", "역할", "접수번호", "보고서명", "제출인", "제출일", "원문", "고른까닭")})
        문들 = _폴더문서들(폴더, d["접수번호"])
        if d["역할"] == "대상 신고서":
            for _이름, 문 in 문들:
                의견 = _감사의견들(문)
                a = 요약재무읽기(문, d, 그)
                for k in a:                                       # 요약재무정보 열의 기수 · 감사인 · 감사의견을 재무제표 열에도
                    p = 그.기간[k]
                    if p.get("기수") and p["개월"] >= 12 and p.get("감사의견"):
                        의견.setdefault(p["기수"], {"감사인": p.get("감사인"), "의견": p["감사의견"]})
                b = 재무제표읽기(문, d, 그, 의견)
                보고실체변화찾기(문, d, 그)
                if not (a or b):
                    그.경보.append("대상 신고서 %s 에서 요약재무정보 · 재무제표 표를 못 찾았다" % d["접수번호"])
        elif d["역할"] == "분할 신고서":
            읽음 = False
            for _이름, 문 in 문들:
                if 분할부문읽기(문, d, 그):
                    읽음 = True
                    break
            if not 읽음:
                그.경보.append("분할 신고서 %s 에서 분할 대상 부문 재무 표를 못 찾았다" % d["접수번호"])
        elif d["역할"] == "분할회사 사업보고서":
            읽음 = False
            for _이름, 문 in 문들:
                if 분할주석읽기(문, d, 그, 분할기일):
                    읽음 = True
                    break
            if not 읽음:
                그.경보.append("분할회사 사업보고서 %s 의 감사보고서 주석에서 분할 · 중단영업 표를 못 찾았다" % d["접수번호"])
    정 = 정기읽기(raw, 그, 개황)
    차입금합(그)
    부호맞추기(그)
    if 분할기일 and not any(x["종류"] == "분할" for x in 그.보고실체변화):
        그.보고실체변화.append({"해": 분할기일[:4], "종류": "분할", "내용": "분할기일 %s — 대상은 분할로 신설됐다(고르기 기록)" % 분할기일,
                           "근거": "dart_신고서고르기.json · 분할 문장 %s" % "; ".join(x.get("글", "")[:60] for x in ((고르기 or {}).get("분할") or {}).get("문장") or [] if isinstance(x, dict))})
    확인불가짓기(그)
    if not 서류들:
        그.확인불가.append({"항목": "신고서 · 투자설명서 · 분할회사 공시", "원인": "조회 경로 문제",
                       "대안": "`dart_fetch.py --회사 <고유번호> --기준일 <날> --신고서` 로 받는다(받지 않았거나 받을 서류가 없다)"})
    감사연 = sorted({p["끝"][:4] for p in 그.기간.values() if p["감사구분"] == "감사" and p["개월"] >= 12})
    짧은 = [k for k, p in 그.기간.items() if p["원천종류"] == "정기" and 0 < p["개월"] < 12]
    if 짧은:
        그.경보.append("짧은 사업연도 — %s (개월: %s) · 연간 비교 · 성장률에 그대로 쓰지 않는다" % (
            " · ".join(짧은), " · ".join(str(그.기간[k]["개월"]) for k in 짧은)))
    if any(p.get("참고이력") for p in 그.기간.values()):
        그.경보.append("참고 이력(감사받지 않은 부문 재무 — 검토 · 경영진 배부)이 있다 — 근거 범위 · 상한 · 하한 산정에서 뺀다(설계 2-2)")
    분전 = [k for k, p in 그.기간.items() if p["원천종류"] == "분할회사 주석" and p["개월"] >= 12]
    분부 = [k for k, p in 그.기간.items() if p.get("참고이력")]
    if 분전 and 분부:
        그.경보.append("분할 부문 표(%s)와 분할회사 중단영업(%s)은 재무제표 기준(별도 배부 ↔ 연결 중단영업)과 해가 달라 잇지 않았다 — 두 값을 하나의 시계열로 "
                     "쓰지 않는다" % (분부[0], 분전[0]))
    결과 = {
        "형식": 형식, "시장": "KR", "회사": 개황.get("corp_name") or ((고르기 or {}).get("대상") or {}).get("이름"),
        "식별": {"고유번호": 개황.get("corp_code") or ((고르기 or {}).get("대상") or {}).get("고유번호"),
               "종목코드": 개황.get("stock_code") or ((고르기 or {}).get("대상") or {}).get("종목코드")},
        "평가기준일": 기준일, "조회일": 조회일 or datetime.date.today().isoformat(),
        "단위": "백만원", "통화": "KRW", "원단위배": 1000000,
        "서류": 낸서류,
        "기간": [그.기간[k] for k in sorted(그.기간, key=lambda x: (그.기간[x]["끝"], x))],
        "표준줄": {z: {k: _정수(v) for k, v in sorted(그.줄[z].items())} for z in 표준줄들},
        "원표": 그.원표,
        "근거": 그.근거,
        "보고실체변화": sorted(그.보고실체변화, key=lambda x: x["해"]),
        "검산": 검산짓기(그),
        "확인불가": 그.확인불가,
        "경보": 그.경보,
        "요약": {"감사받은연간해": 감사연, "감사받은연간해수": len(감사연), "정기기간": 정, "분할기일": 분할기일},
    }
    return 결과


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="국내 신고서 · 투자설명서 · 분할회사 공시 재무 → 신고서재무/1")
    ap.add_argument("--raw", default=None, help="회차 `_raw` 폴더(기본: 이 키트의 `_raw`)")
    ap.add_argument("--기준일", "--재무기준일", dest="기준일", default=None,
                    help="재무기준일 F YYYY-MM-DD(평가기준일 전에 제출된 마지막 분기말 · 옛 이름 --기준일 은 지금 뜻 그대로)")
    ap.add_argument("--평가기준일", default=None, help="평가기준일 T YYYY-MM-DD — 산출 머리에만 적는다(읽는 값은 바꾸지 않는다)")
    ap.add_argument("--가정", default=None, help="가정 파일 — 날짜 인자를 비우면 기준일.py 로 F · T 를 푼다(F 가 없으면 F = T)")
    ap.add_argument("--출력", default=None, help="기본 `<raw>/신고서재무.json`")
    ap.add_argument("--조회일", default=None)
    a = ap.parse_args(argv)
    import 기준일인자 as _기인                                  # noqa: PLC0415 — 날짜 둘(2026-10-25)
    a.기준일 = _기인.풀기(a.기준일, a.가정, _기인.재무, 인자="--기준일")
    a.평가기준일 = _기인.풀기(a.평가기준일, a.가정, _기인.평가, 인자="--평가기준일")
    if not a.기준일:
        ap.error("--기준일(재무기준일) 또는 --가정 이 있어야 합니다")
    raw = a.raw or os.path.join(os.path.dirname(여기), "_raw")
    if not os.path.isdir(raw):
        sys.stderr.write("raw 폴더가 없다 — %s\n" % raw)
        return 입력오류
    try:
        datetime.date.fromisoformat(a.기준일)
    except ValueError:
        sys.stderr.write("기준일 꼴이 아니다 — %s\n" % a.기준일)
        return 입력오류
    r = 읽기(raw, a.기준일, a.조회일)
    _기인.머리(r, a.기준일, a.평가기준일)                       # 재무기준일 = F · 평가기준일 = T(알면)
    p = 저장(r, a.출력 or os.path.join(raw, 출력파일))
    어 = [x for x in r["검산"] if x["판정"] != "통과"]
    print("신고서재무(KR) — 서류 %d · 기간 %d · 감사 연간 %d해(%s) · 검산 %d(어긋남 %d) · 확인불가 %d · 경보 %d → %s" % (
        len(r["서류"]), len(r["기간"]), r["요약"]["감사받은연간해수"], " · ".join(r["요약"]["감사받은연간해"]), len(r["검산"]), len(어),
        len(r["확인불가"]), len(r["경보"]), p))
    return 발견 if (not r["서류"] or 어) else 통과


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""**동인원천(A3)** — 회사 유형을 판정하고, 그 유형의 원가 동인 원천을 공시 원문 · API 에서 찾아 `_raw/동인원천.json` 과 13번 5xx 로 낸다.
업종 중립이다 — 회사 이름 · 업종 이름이 코드 분기에 없다. 무엇이 있는지는 공시의 표 · 낱말 · 재무 비율로 탐지하고, 없는 원천은
「해당 없음」(그 유형에 원래 없다)과 「확인 불가」(있어야 하는데 못 찾았다)로 가른다.

    python 스크립트/동인원천.py --원천폴더 _raw                                 # 받아 둔 원문 · DART 응답만(가정 없이 — 기본 대응을 제안)
    python 스크립트/동인원천.py --원천폴더 _raw --가정 가정.json               # 구조(원가 줄 · 자산군) · 실적 열 · 금액 단위를 가정에서
    python 스크립트/동인원천.py --원천폴더 _raw --가정 가정.json --받기        # 실적 열에 필요한 해의 사업보고서 원문이 없으면 DART 에서(제출이력)
    python 스크립트/동인원천.py --원천폴더 _raw --자산군 "1=건물;2=나머지" --원가줄 "6=성격;7=나머지"
    python 스크립트/동인원천.py --미국 _raw/companyfacts.json --단위 원 --원천통화단위 백만달러   # 미국 — companyfacts 에서 되는 만큼
    python 스크립트/동인원천.py … --대조 이전회차/가정.json                     # 그 가정의 원천(5xx)과 같은 칸 같은 값인지(회귀 확인)

날짜 둘(2026-10-25 · `기준일.py`) — 재무 쪽 도구다. 「기준일 보고서」 · 원천근거 둘째 칸 · 출처 시점은 **재무기준일 F**(메타.재무기준일,
없으면 메타.평가기준일 — 옛 가정은 지금과 같다)로 선다. `--기준일`(별칭 `--재무기준일`)을 주면 그 값이 F 다. 산출 머리는 `재무기준일`(F) ·
`평가기준일`(T — 가정의 메타.평가기준일) 둘을 적는다.

왜 — 엔진 v13 은 원가 줄 실적(57k) · 종업원급여(531~) · 직원 수(541~) · 자산군 취득원가(56g) · 건설중인자산(567) · 편입액(569)을
읽는데(엔진/원가.py · 인건비.py · 투자.py) 그 행을 채우는 도구가 없었다 — `dart_원천.py` 는 재무제표 본표 줄만 잡는다(교수 리뷰 마-2 ·
0_결정 2026-10-16 4). 회사 유형마다 동인이 사는 곳이 다르다: 제조는 유형자산 주석 · 생산 실적, 소프트웨어 · 플랫폼은 인원 · 사용자 ·
거래액, 유통 · 소매는 매장 · 면적 · 상품 매입. 이 도구는 유형을 먼저 판정하고(`유형`) 그 유형의 원천을 찾는다.

회사 유형 판정(`유형판정`) — 「사업의 내용」의 유형 낱말 빈도(`유형낱말`)와 재무 비율(유형자산 ÷ 매출 · 재고 ÷ 매출 · 상품 매입 ÷ 총비용 ·
  인건비 ÷ 총비용)로 겹칠 수 있게 고른다. 판정과 근거는 `유형` 에 — 확정은 본선이 한다. 미국은 companyfacts 곁의 10-K 원문(10K_*.txt · .htm)
  Item 1 낱말(`미국유형낱말`)과 재무 비율로 고르고(2026-10-16 — 원문이 없을 때만 「판정 보류」), Human Capital 의 직원 수 · 인도 대수 같은 수량 문장도 읽는다.
  `구분별` 은 연결 주석 영업부문 표의 부문 이름 · 설명과 사업의 내용 줄로 고른 후보다
동인 원천(업종 중립 범주)과 찾는 자리(국내 · 미국)
  물량        판매량 · 생산량 · 출하 — 「매출 · 판매 · 생산 실적」 표 가운데 머리에 수량이 있는 표(`판매량공시` — 값만, 구분 대응은 합류)
  능력        생산능력 · 매장 · 면적 · 좌석 · 객실 — 사업의 내용 표 · 문장(`사업지표`), 미국은 companyfacts 의 NumberOf… 태그
  단위 경제   사용자 · 가입자 · ARPU · 거래액 · 주문 · 테이크레이트 — 같은 자리(`사업지표`)
  인원        직원 현황(국내 = 본사 범위) · 10-K 표지의 직원 수(연결) → 541~543 · 549
  자산군      유형자산 주석(장부금액 표 · 변동 표 · 다단 머리 XBRL 표) · 「생산설비의 현황」 → 56g · 56(3+g) · 59(6+g) · 567 · 569 (미국은 PP&E 태그).
              편입 = 취득 + 대체(사업결합은 `사업결합` 으로 따로 — S5-10) · 유형 몫 상각 · 사용권 신규 · 회계정책 내용연수(S5-17) · 공시 투자계획 표(S5-19) ·
              현금흐름표 CAPEX(…ClassifiedAsInvestingActivities) · 무형 취득 · 사업결합 취득(S5-15)
  연구개발    「연구개발비용」 표(제NN기 세 열) → 535~537 (미국은 R&D 태그)
  수주잔고    사업의 내용의 수주 표 · 미국 RemainingPerformanceObligation → `사업지표.수주잔고`
  판가 · 가동률  「주요 제품 등의 가격변동추이」 표(`판가공시` — 품목별 기간 단가) · 「생산실적 및 가동률」의 가동률(`가동률공시` — 0~1).
              값만(구분 대응은 합류 — `매출구분초안.py`). 자체검사 ⑨ 가 가동률 관측 최고로 능력 경로의 가동률 상한을 잰다(S2-13)
  성격별 비용 「비용의 성격별 분류」 · 단일 표시 회사의 「영업비용」 주석 — 표의 모든 줄을 `성격별비용.분류` 로 자리 매김 → 57k · 531 · 540 · 546 ·
              578 · 579(미국은 「해당 없음」 — `기능별비용` 으로 대신)
  운전자본    API 잔액 → 회전일수(기말 · 반기 연환산) · 선수금 · 계약부채 · 계약자산 비율 · `국면`(영업이익률 사분위 — 폭이 작으면 「구분 없음」)
13번 행(값 단위 = 가정의 메타.금액단위 · `--단위` · 기본 백만원)
  57k  원가 줄 k — 대응 `나머지`(합계 − 인건비 − 복리후생 − 상각 − 재고 변동(반영 = 예) − 다른 원가 줄) · `성격`(그 원가 줄로 분류된 줄의 합).
       가정이 없으면 비용 표시로 정한다: 매출원가 줄이 있으면 원가 줄 1 나머지, 영업수익 · 영업비용 단일 표시면 5 · 6 성격 + 7 나머지
  532~534 판관비 주석 · 538 · 548 · 539 퇴직급여 · 544 · 545 종업원 관련 부채 · 546 주식보상 · 547 종업원급여(별도) · 568 취득 약정액
  551~560 판매량 · 587~592 기준 기간 판매량 — 이 도구는 붓지 않는다(구분 대응은 합류의 본선)

FX-A(2026-10-25) — 보고 기간은 표지의 점 날짜 · 정정 보고서도 읽고(`원문읽음` · `원문버림` · `원문경보`), 표는 곁의 XML 을 격자로 읽는다(`공시표.py` —
  `생산능력표` · `가동률공시[].기준` · `수주잔고표` · `투자계획.진행중` · `유형자산.약정줄 · 변동표 · 취득약정근거` · `재무시계열[].CAPEX구성`), 유형은 구조 신호
  (`유형.신호` — 수주잔고 표 · RPO · 외주 · 합작 · 데이터센터 · 지주)를 먼저 본다. `_raw/미국원천.json`(FX-C)이 있으면 미국 본문 · 누계 · 인원을 받는다.
**지어내지 않는다** — 못 찾은 값은 키를 빼고 `확인불가[]` 에, 그 유형에 없는 값은 `해당없음[]` 에 적는다. 0 은 「공시가 0 이라 적었다」는 뜻이다.
**검산** — 성격별 합계 = 매출원가 + 판관비(API, `성격별비용.합계검산`) · 직원 정규 + 기간제 = 합계 · 같은 칸 두 출처의 값이 다르면 `주의`.
산출 꼴은 `가정_스키마.md` 「갈래 산출물」 절의 `_raw/동인원천.json` 이 정본이다(공통 머리 · 성격별비용 · 기능별비용 · 사업지표 · 인건비 ·
유형자산 · 운전자본 · 판매량공시 · 원천행 + 원천근거(4칸 꼴)). 가정 파일에 옮기는 일은 본선이 한다.
상한(0_결정 2026-10-16 7): 국내 10분 · 미국 12분 벽시계 — `--상한분`, 넘으면 받은 데까지 적고 `status: 부분`.
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
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass
여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
import 성격별비용                                      # noqa: E402
import 공시표                                         # noqa: E402  FX-A R2 — DART 원문 XML 표(격자)
from 기간축 import 기간ID, FY실적, 누계실적              # noqa: E402

ROOT = os.path.dirname(여기)
단위배 = {"원": 1.0, "천원": 1e3, "백만원": 1e6, "억원": 1e8, "십억원": 1e9}
_시작 = time.time()


# ────────────────────────────────────────────────────────────── 원문 → 행(표의 줄) · 칸

def 수(c):
    """칸 글 → 수(괄호 = 음수, 「-」 = 0). 수가 아니면 None."""
    if c is None:
        return None
    c = c.strip()
    if c in ("-", "－", "—", "–"):
        return 0.0
    m = re.fullmatch(r"\(?\s*(-)?\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*\)?", c)
    if not m:
        return None
    v = float(m.group(2).replace(",", ""))
    return -v if (c.startswith("(") or m.group(1)) else v


def 행들(글):
    """원문 txt → 표의 줄 목록(칸 목록). 빈 줄이 줄을 가르고(dart_fetch 의 태그 벗기기 꼴), 한 줄 안의 탭도 칸을 가른다. 빈 칸 = ''."""
    낸, 지금 = [], []
    for L in 글.split("\n"):
        s = L.strip(" \t\r")
        if s == "":
            if 지금:
                낸.append(지금)
                지금 = []
            continue
        for c in (s.split("\t") if "\t" in s else [s]):
            지금.append(c.strip())          # 전각 빈칸(「　」)은 strip 으로 '' 가 된다 — 빈 칸
    if 지금:
        낸.append(지금)
    return 낸


def 표준(s):
    return re.sub(r"\s+", "", s or "")


_단위re = re.compile(r"\(\s*단위\s*[:：]\s*([^)]+?)\s*\)")
_기간표지 = {"당기": "당", "당기말": "당", "당반기": "당", "당반기말": "당", "당분기": "당", "당분기말": "당", "당기누적": "당",
          "전기": "전기", "전기말": "전기", "전전기": "전전기", "전전기말": "전전기", "전반기": "전반", "전분기": "전반",
          "전반기말": "전반", "전분기말": "전반"}


_표지끝re = re.compile(r"(?:^|[.。]\s*|\s)[①-⑳]?\s*(당\s*기\s*말?|당\s*반\s*기\s*말?|당\s*분\s*기\s*말?|당\s*기\s*누\s*적|전\s*전\s*기\s*말?|"
                    r"전\s*기\s*말?|전\s*반\s*기\s*말?|전\s*분\s*기\s*말?)\s*$")


def 표지읽기(c):
    """칸 글 → 기간 표지(당 · 전기 · 전전기 · 전반) 또는 None. 「당기」 한 칸만이 아니라 「① 당기」 · 「(1) 당기말」처럼 번호가 앞에 붙은 칸,
    「…변동내역은 다음과 같습니다.① 당기」처럼 설명 글 끝에 붙은 표지도 읽는다(S5-08 — 옛 사업보고서의 유형자산 변동 표가 이 꼴이라
    여러 해 주석이 2~3해에서 멈췄다). 회사 · 업종과 무관한 원문 꼴의 규칙이다."""
    k = 표준(c)
    if k in _기간표지:
        return _기간표지[k]
    k2 = re.sub(r"^(?:[①-⑳]|\(?[0-9]{1,2}\)|\(?[가-하]\))", "", k)
    if k2 in _기간표지:
        return _기간표지[k2]
    m = _표지끝re.search((c or "").strip())
    if m and (m.group(0).lstrip().startswith(tuple("①②③④⑤⑥⑦⑧⑨⑩")) or "." in m.group(0) or "。" in m.group(0)):
        return _기간표지.get(표준(m.group(1)))
    return None


def 단위읽기(줄):
    for c in 줄:
        m = _단위re.search(c or "")
        if m:
            u = m.group(1).replace(" ", "")
            for k in sorted(단위배, key=len, reverse=True):
                if u.endswith(k):
                    return k
            return u
    return None


_날글 = r"(\d{4})\s*(?:년|[.\-/])\s*(\d{1,2})\s*(?:월|[.\-/])\s*(\d{1,2})\s*일?"
_사업연도re = re.compile(r"사업\s*연도\s*" + _날글 + r"\s*부\s*터\s*" + _날글 + r"\s*까\s*지")
_정정re = re.compile(r"정\s*정\s*신\s*고|정정\s*대상\s*공시\s*서류|기재\s*정정")


def _날짜(y, m, d):
    try:
        return datetime.date(int(y), int(m), int(d))
    except ValueError:
        return None


def _그럴듯한기간(시, 끝):
    """두 날짜가 보고 기간(3 · 6 · 9 · 12개월, 시작 = 달 첫날 언저리)인가 — 정정 표지 날짜(「2024-03-29 · 2024-03-12」) 따위를 거른다."""
    if not 시 or not 끝 or 끝 <= 시:
        return False
    개월 = (끝.year - 시.year) * 12 + 끝.month - 시.month + 1
    return 개월 in (3, 6, 9, 12) and 시.day <= 3


def 보고기간읽기(행, 최대줄=None):
    """원문 행 → (시작, 끝, 기수, 표지 위치 글) — 표지의 「사업연도 YYYY년 MM월 DD일 부터 … 까지」 · 「사업연도 YYYY.MM.DD 부터 … 까지」(DART 문서 6.x 판
    점 날짜 — FX-A R1, 2026-10-25: 정규식이 한글 날짜만 받아 최신 사업보고서 · 기준일 반기 9개 파일이 통째로 버려졌다). 정정 보고서는 앞에
    「정정신고」 쪽이 수천 줄 붙어도 표지까지 내려가 읽는다 — 정정 표지의 날짜(정정일 · 최초제출일)를 사업연도로 읽지 않는다(회계연도 +1 이 그 원인).
    기수 = 표지 바로 앞의 「(제 N 기)」. 못 찾으면 (None, None, None, None)."""
    for n in ((3000, None) if 최대줄 is None else (최대줄,)):
        글 = " ".join(" ".join(r) for r in (행[:n] if n else 행))
        for m in _사업연도re.finditer(글):
            시, 끝 = _날짜(*m.group(1, 2, 3)), _날짜(*m.group(4, 5, 6))
            if not _그럴듯한기간(시, 끝):
                continue
            앞 = 글[max(0, m.start() - 300): m.start()]
            k = re.findall(r"\(\s*제\s*(\d+)\s*기", 앞)
            return 시, 끝, (int(k[-1]) if k else None), 글[max(0, m.start() - 40): m.end()]
    return None, None, None, None


class 보고서:
    """원문 txt 하나 — 종류 · 기간 · 행. `정정`(정정 보고서인가) · `형식판`(DART 문서 서식 판 — 「6.3」) · `기간읽음`(어디서 기간을 읽었나)도 둔다."""

    def __init__(self, 경로):
        self.경로 = 경로
        self.접수 = re.sub(r"\D.*$", "", os.path.basename(경로)) or os.path.basename(경로)
        글 = io.open(경로, encoding="utf-8", errors="ignore").read()
        self.행 = 행들(글)
        머리 = " ".join(" ".join(r) for r in self.행[:30])
        self.종류 = ("사업" if "사업보고서" in 머리[:60] else "반기" if "반기보고서" in 머리[:60] else
                   "분기" if "분기보고서" in 머리[:60] else None)
        self.정정 = bool(_정정re.search(머리))
        self.형식판 = next((c.strip() for r in self.행[:3] for c in r[:4] if re.fullmatch(r"\d{1,2}\.\d{1,2}", (c or "").strip())), None)
        # 표지의 「사업연도 … 부터 … 까지」 두 날짜(한글 날짜 · 점 날짜). 정정 보고서는 앞에 「정정신고」 쪽이 붙는다 — 표지까지 내려간다
        시, 끝, 기수, _곳 = 보고기간읽기(self.행)
        self.기간읽음 = "표지" if 끝 else None
        if not 끝:
            # 표지를 못 찾았다 — 곁의 XML 표지(PERIODFROM · PERIODTO 속성)를 본다(FX-A R1)
            try:
                import 공시표                                       # noqa: PLC0415
                p = 공시표.곁XML(경로)
                문 = 공시표.읽기(p) if p else None
                if 문 and 문.get("기간"):
                    시, 끝 = (datetime.date.fromisoformat(문["기간"]["시작"]), datetime.date.fromisoformat(문["기간"]["끝"]))
                    self.기간읽음 = "XML 표지"
                    self.형식판 = self.형식판 or 문.get("형식판")
            except Exception:                                      # noqa: BLE001
                pass
        if not 끝 and not self.정정:
            # 옛 꼴 — 첫 30줄의 한글 날짜 둘(정정 보고서는 이 길을 쓰지 않는다: 정정 표지의 정정일 · 최초제출일이 걸린다)
            날 = re.findall(r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일", 머리)
            if len(날) >= 2 and _그럴듯한기간(_날짜(*날[0]), _날짜(*날[1])):
                시, 끝 = _날짜(*날[0]), _날짜(*날[1])
                self.기간읽음 = "머리 날짜"
        self.시작, self.끝 = 시, 끝
        긴머리 = " ".join(" ".join(r) for r in self.행[:3000])
        m = re.search(r"\(\s*제\s*(\d+)\s*기", 머리) if not self.정정 else None
        self.기수 = 기수 if 기수 is not None else (int(m.group(1)) if m else (
            int(re.search(r"제\s*(\d+)\s*기", 긴머리).group(1)) if re.search(r"제\s*(\d+)\s*기", 긴머리) else None))
        # 행마다 연결 주석 안인가 — 「3. 연결재무제표 주석」 · 「5. 재무제표 주석」 같은 큰 머리와 주석 머리의 「(연결)」로 가린다.
        # 연결 구획이 아예 없으면(별도만 내는 회사) 모두 참으로 둔다
        self.연결, 지금, 있음 = [], None, False
        for r in self.행:
            c = (r[0] if r else "") or ""
            if len(r) == 1 and re.fullmatch(r"\d{1,2}\.\s*연결\s*재무제표(\s*주석)?", c):
                지금, 있음 = True, True
            elif len(r) == 1 and re.fullmatch(r"\d{1,2}\.\s*재무제표(\s*주석)?", c):
                지금 = False
            elif len(r) == 1 and re.fullmatch(r"\d{1,2}\.\s*\S.{0,40}\(연결\)", c):
                지금, 있음 = True, True
            self.연결.append(지금)
        if not 있음:
            self.연결 = [True] * len(self.행)
        if self.시작 and self.끝:
            self.개월 = (self.끝.year - self.시작.year) * 12 + self.끝.month - self.시작.month + 1
            self.회계연도 = self.끝.year if self.종류 == "사업" else (self.시작.year if self.시작.month == 1 else self.끝.year)
        else:
            self.개월, self.회계연도 = None, None

    def 쓸만한가(self):
        return self.종류 is not None and self.끝 is not None

    def 열(self, 표지, 흐름=True):
        """기간 표지(당 · 전기 · 전전기 · 전반) → 기간 ID. 흐름(손익 · 변동) 표의 「전반」(전년 같은 기간)은 모델 열이 아니라 None."""
        if self.종류 == "사업":
            return {"당": 기간ID(FY실적, self.회계연도), "전기": 기간ID(FY실적, self.회계연도 - 1),
                    "전전기": 기간ID(FY실적, self.회계연도 - 2)}.get(표지)
        if 표지 == "당":
            return 기간ID(누계실적, self.회계연도, self.개월)
        if 표지 == "전기" and not 흐름:
            return 기간ID(FY실적, self.회계연도 - 1)
        return None

    def 글(self):
        return "%s보고서 %s(접수 %s)" % (self.종류, self.끝.isoformat() if self.끝 else "?", self.접수)


def 머리찾기(행, 정규식, 시작=0):
    r = re.compile(정규식)
    return [i for i in range(시작, len(행)) if any(r.search(c or "") for c in 행[i][:3])]


def 연결머리(보, 정규식):
    """연결 주석 안의 머리만(연결 구획이 없는 회사는 전부)."""
    return [i for i in 머리찾기(보.행, 정규식) if 보.연결[i]]


def _주석머리(줄):
    c = (줄[0] if 줄 else "") or ""
    return len(줄) == 1 and bool(re.match(r"^\d{1,2}\.\s*\S", c)) and len(c) < 60


def _나누기(줄들):
    """줄 모양(칸이 한 줄에 모인 표) — (머리줄들, 자료줄들). 날짜 · 「기중변동액」 같은 구획 줄은 자료 사이에 둔다."""
    머리, 자료 = [], []
    for r in 줄들:
        수들 = [수(c) for c in r[1:]]
        if len(r) >= 2 and any(v is not None for v in 수들):
            자료.append(r)
        elif not 자료:
            머리.append(r)
        else:
            자료.append(r)
    return 머리, 자료


def _다시묶기(줄들):
    """칸마다 빈 줄로 갈린 표(줄 구조가 없는 원문 — 같은 회사도 해마다 꼴이 바뀐다) — 칸을 한 줄로 펴서 다시 묶는다.

    머리 = 첫 수 앞의 글 칸들(빈 칸 무시). 첫 수 바로 앞 글 칸이 첫 줄 이름, 그 뒤 잇단 수(빈 칸 포함) 개수 n 이 열 수다.
    그 뒤로는 「이름 + n 칸」씩 묶고, 이름 뒤에 바로 이름이 오면 구획 줄(날짜 · 「기중변동액」)로 둔다."""
    셀 = [c for r in 줄들 for c in r]
    k = next((i for i, c in enumerate(셀) if c != "" and 수(c) is not None), None)
    if k is None:
        return [[c for c in 셀 if c != ""]], []
    앞 = [c for c in 셀[:k] if c != ""]
    if not 앞:
        return [], []
    이름 = 앞.pop()
    n = 0
    while k + n < len(셀) and (셀[k + n] == "" or 수(셀[k + n]) is not None):
        n += 1
    머리 = [앞] if 앞 else []
    자료 = [[이름] + 셀[k: k + n]]
    i = k + n
    while i < len(셀):
        c = 셀[i]
        if c == "":
            i += 1
            continue
        if 수(c) is not None:          # 이름 없이 수가 남았다 — 묶음이 어긋났다. 여기서 멈춘다
            break
        뒤 = 셀[i + 1: i + 1 + n]
        if len(뒤) == n and all(x == "" or 수(x) is not None for x in 뒤) and any(수(x) is not None for x in 뒤):
            자료.append([c] + 뒤)
            i += 1 + n
        else:
            자료.append([c])
            i += 1
    return 머리, 자료


def 블록들(행, i0, 최대=500, 첫블록만=False):
    """머리 i0 뒤의 기간 블록 — [(표지, 단위, 머리줄들, 자료줄들, 단위 줄 번호)]. 단위 칸이 있는 줄에서 블록이 서고, 다음 단위 줄 · 주석 머리 · 긴 글에서 끝난다.
    블록의 줄이 거의 다 한 칸이면(칸마다 빈 줄로 갈린 원문) `_다시묶기` 로 줄을 되살린다."""
    낸 = []
    i, 끝 = i0 + 1, min(len(행), i0 + 최대)
    if 0 <= i0 < len(행) and 단위읽기(행[i0]) is not None:      # 옛 원문 — 머리 글 끝에 「(단위:천원)」이 붙는다
        i = i0
    while i < 끝:
        줄 = 행[i]
        if i > i0 + 1 and _주석머리(줄):
            break
        u = 단위읽기(줄)
        if u is None:
            i += 1
            continue
        표지 = None
        for c in 줄 + (행[i - 1] if i > 0 else []):
            표지 = 표지읽기(c)
            if 표지:
                break
        줄들 = []
        j = i + 1
        while j < 끝:
            r = 행[j]
            if 단위읽기(r) is not None or _주석머리(r):
                break
            if len(r) == 1 and len(r[0]) <= 60 and 표지읽기(r[0]):      # 다음 블록의 표지 줄(「② 전기」 꼴 포함)
                break
            if len(r) == 1 and len(r[0]) > 60:              # 설명 글 — 표가 끝났다
                break
            줄들.append(r)
            j += 1
        한칸 = sum(1 for r in 줄들 if len(r) == 1)
        머리, 자료 = _다시묶기(줄들) if (len(줄들) >= 6 and 한칸 >= 0.8 * len(줄들)) else _나누기(줄들)
        낸.append((표지, u, 머리, 자료, i))
        if 첫블록만:
            break
        i = j
    return 낸


def 열이름(머리, n):
    """머리줄들 → 자료 칸 n 개의 이름(오른쪽 맞춤 — 첫 칸(구분 · 과목)은 머리에 없을 수 있다)."""
    for r in reversed(머리):
        이름 = [c for c in r if c != ""]
        if len(이름) >= n:
            return 이름[-n:]
    return [""] * n


def 표값(자료, 라벨, 열=None, 열들=None, k=0):
    """자료줄들에서 라벨(공백 무시 · 정규식)인 줄의 값. 열 = 열 이름(정규식) — 없으면 k 번째 수."""
    r = re.compile(라벨)
    for 줄 in 자료:
        if len(줄) < 2 or not r.fullmatch(표준(줄[0])):
            continue
        값 = [수(c) for c in 줄[1:]]
        if 열 is not None and 열들:
            for 이름, v in zip(열들[-len(값):], 값):
                if re.search(열, 표준(이름)) and v is not None:
                    return v
            return None
        수들 = [v for v in 값 if v is not None]
        return 수들[k] if len(수들) > k else None
    return None


# ────────────────────────────────────────────────────────────── 모으기

class 모음:
    def __init__(self, 목표단위):
        self.단위 = 목표단위
        self.원천, self.출처 = {}, {}
        self.확인불가, self.대조, self.기록 = {}, [], []
        self.관측 = {}
        self.성격별 = {}
        self.유형원 = {}
        self.해당없음, self.주의, self.합계검산 = [], [], {}
        self.회전, self.회전출처 = {}, ""
        self.기능별, self.기능별출처 = {}, []
        self.운영, self.판매량 = {}, []
        self.판가, self.가동률 = [], []
        self.미국본문 = None              # 미국 — 10-K 본문 읽기(미국본문읽기)
        self.계리 = None                  # 미국 — 연금 주석의 보상 상승률 가정(S4-03 — 국내는 원문의 퇴직급여 주석에서 읽는다)
        self.설립일, self.구조단절, self.이상회전 = None, [], []
        # S5 — 내용연수 · 상각방법(회계정책) · 사용권 신규 · 투자계획 표 · 투자 발화 · 유형 몫 상각(사용권 · 무형 상각 뺀) · 무형 상각
        self.내용연수, self.사용권신규, self.투자계획, self.투자발화 = None, {}, [], []
        self.유형상각, self.무형상각 = {}, {}
        # FX-A(2026-10-25) — XML 격자 재료 · 원문 고르기 기록
        self.투자진행, self.생산능력표, self.약정줄, self.변동표, self.비현금 = [], [], [], None, {}
        self.변동표상각 = {}
        self.수주표, self.수주문장, self.원문버림 = None, [], []

    def 넣기(self, 행, 열, 값, 표단위, 출처, 순위):
        """순위가 높은 출처(그 기간의 「당기」 보고서 = 2, 뒤 보고서의 「전기」 = 1)가 이긴다. 같은 순위면 먼저 넣은 것."""
        if 열 is None or 값 is None:
            return
        v = 값 * 단위배.get(표단위, 1.0) / 단위배[self.단위] if 표단위 not in (None, "명", "인원") else 값
        행 = "%s" % 행
        옛 = self.출처.get(행, {}).get(열)
        if 옛 is not None and 옛[1] >= 순위:
            if abs((self.원천[행][열] or 0) - v) > max(0.5, abs(v) * 1e-9) and 옛[1] == 순위:
                self.대조.append({"이름": "같은 칸 두 출처", "행": 행, "열": 열, "값": self.원천[행][열], "다른값": v,
                                "출처": 옛[0], "다른출처": 출처})
            return
        self.원천.setdefault(행, {})[열] = v
        self.출처.setdefault(행, {})[열] = (출처, 순위)


def _순위(보, 표지):
    """그 기간이 「당기」인 보고서의 주석이 먼저(3), 뒤 보고서의 「전기」가 다음(1.5). 「생산설비의 현황」은 기말 2 · 기초 1."""
    return 3 if 표지 == "당" else 1.5


_성격머리 = r"비용의\s*성격별|성격별\s*(비용|분류)|영업비용에\s*대한|영업비용의\s*(내역|구성|성격)|^\d{1,2}\.\s*영업비용"
_합계라벨 = {"영업비용", "영업비용계", "비용계", "매출원가및판매비와관리비", "매출원가및판매비와관리비합계"}


def 줄라벨값(r):
    """표 줄 → (라벨, [값 …]) — 라벨 = 첫 수 앞의 마지막 글 칸(「영업비용 | 급여」처럼 두 칸이면 뒤 칸), 값 = 그 뒤 칸(빈 칸 None)."""
    k = next((i for i, c in enumerate(r) if c != "" and 수(c) is not None), None)
    if not k:
        return None, []
    글칸 = [c for c in r[:k] if c != ""]
    if not 글칸:
        return None, []
    return 글칸[-1], [수(c) if c != "" else None for c in r[k:]]


def 성격별읽기(보, 연결=True, 단일표시=False):
    """「비용의 성격별 분류」(단일 표시 회사는 「영업비용」 주석) → {기간 ID: {"줄": [(라벨, 값, 항목, 자리 키)], "합계": 값, "단위", "출처"}}.

    줄 이름은 회사 · 업종마다 다르다(종업원급여 · 급여 · 퇴직급여 · 재고자산의 매입 · 지급수수료 · 통신비 …) — 줄마다 `성격별비용.분류` 로 자리를
    정한다. 분류되는 줄이 셋 미만인 블록은 성격별 표가 아니라고 보고 건너뛴다. 열 — 「3개월 | 누적」이면 누적, 「당기 | 전기」(옆으로 놓인
    옛 꼴)면 열마다 그 기간, 한 열이면 블록 표지(당기 · 전기)."""
    낸, 본 = {}, set()
    별도있음 = any(not x for x in 보.연결)          # 연결 구획이 없는 회사(별도만)는 모두 참 — 별도 표를 따로 가를 수 없다
    for i0 in 머리찾기(보.행, _성격머리):
        if bool(보.연결[i0]) != 연결 or (not 연결 and not 별도있음):
            continue
        for 표지, u, 머리줄, 자료, 블번호 in 블록들(보.행, i0, 최대=400):
            if 블번호 in 본:
                continue
            본.add(블번호)
            줄들 = [줄라벨값(r) for r in 자료]
            줄들 = [(l, v) for l, v in 줄들 if l]
            n = max((len(v) for _, v in 줄들), default=0)
            if n == 0:
                continue
            열들 = 열이름(머리줄, n)
            if any("누적" in 표준(x) for x in 열들):
                칸표 = [(열들.index([x for x in 열들 if "누적" in 표준(x)][0]), 표지)]
            elif sum(1 for x in 열들 if 표준(x) in _기간표지) >= 2:
                칸표 = [(j, _기간표지[표준(x)]) for j, x in enumerate(열들) if 표준(x) in _기간표지]
            else:
                칸표 = [(0, 표지)]
            for j, 표 in 칸표:
                c = 보.열(표) if 표 else None
                if c is None or c in 낸:
                    continue
                기록, 합계, 바닥합계, 내역 = [], None, False, []
                for l, v in 줄들:
                    x = v[j] if len(v) > j else None
                    if x is None:
                        continue
                    # 바닥 합계 뒤의 줄은 내역이다(2026-10-23 — 「스톡그랜트와 관련된 비용, 종업원급여」 같은 각주 · 구성 표시, 「매출원가 · 판관비」 배분 줄).
                    #   더하면 그 성격이 두 번 실린다(실측: 종업원급여 531 이 내역 줄만큼 두 번). 합계가 표 위에 선 꼴은 뒤의 줄이 구성 줄이라 그대로 읽는다
                    if 바닥합계:
                        내역.append((l, x))
                        continue
                    if 표준(l) in _합계라벨 and 합계 is None and not 기록:
                        합계 = x
                        continue
                    # 합계 라벨은 표 아래에도 선다(S3-06 — 표 맨 위에서만 잡아 바닥의 「영업비용」 합계가 미분류 줄로 원가 줄 7 에 더해져
                    #   그 해 비용이 두 배가 됐다). 라벨이 합계 꼴이고 값이 앞 줄 합과 1% 안이면 합계다
                    앞합 = sum(y for _, y, _, _ in 기록)
                    if 표준(l) in _합계라벨 and 합계 is None and 기록:
                        if 앞합 and abs(x - 앞합) <= 0.01 * abs(앞합):
                            합계, 바닥합계 = x, True
                            continue
                    분 = 성격별비용.분류(l, 단일표시)
                    if 분 and 분[1] == "합계":
                        합계 = x
                        바닥합계 = bool(기록) and bool(앞합) and abs(x - 앞합) <= 0.01 * abs(앞합)
                        continue
                    기록.append((l, x, 분[0] if 분 else "미분류", 분[1] if 분 else ("원가7" if 단일표시 else "원가4")))
                if sum(1 for _, _, 항, _ in 기록 if 항 != "미분류") < 3:
                    continue
                낸[c] = {"줄": 기록, "합계": 합계, "단위": u or "원",
                        "출처": "%s 「비용의 성격별 분류」(%s) %s" % (보.글(), "연결" if 연결 else "별도", 표 or "")}
                if 내역:
                    낸[c]["합계뒤내역"] = 내역                 # 더하지 않은 줄(바닥 합계 뒤) — 사람이 볼 수 있게 남긴다
    return 낸


인건비성키 = ("인건비", "복리후생", "주식보상")     # 13번 531 = 7번이 세우는 인건비 총액 — 성격별 표의 이 키 줄의 합(S4-01). 540 · 546 은 그 안의 내역


def 성격별모으기(보들, 모, 구, 별도도=True):
    """57k · 578 · 579 · 531 · 540 · 546 (연결) · 547(별도) — 그리고 `성격별비용` 칸(항목 · 대응 · 합계검산의 재료).

    **531 은 7번이 세우는 인건비 총액이다(S4-01 · 2026-10-17)** — 성격별 표의 인건비성 줄(급여 · 퇴직급여 · 복리후생 · 주식보상)의 합. 엔진 7번이
    급여 = 531 − 성과급 − 퇴직 538 · 539 − 복리후생 540 으로 떼므로 복리후생 · 주식보상 줄이 따로 있는 서식(플랫폼 · 유통 · 게임 · 서비스에 흔하다)에서
    531 에 그 줄을 빼고 부으면 복리후생이 사라지고, 주식보상은 원가 줄 나머지(57k)와 인건비에 두 번 실릴 수 있었다. 540 · 546 은 그 안의 내역이고,
    원가 줄 나머지는 인건비성 줄을 모두 뺀다. 주식보상은 인원 × 1인당 급여(503) 쪽에 든다 — FCFF 에 가산하지 않는다."""
    원가줄 = 구["원가줄"]
    단일 = 구.get("단일표시", False)
    for 보 in 보들:
        for 연결 in ((True, False) if 별도도 else (True,)):
            표들 = 성격별읽기(보, 연결, 단일)
            for 열, 표 in 표들.items():
                u, 출처, 합계 = 표["단위"], 표["출처"], 표["합계"]
                순 = 3 if 열 == 보.열("당") else 1.5
                키합 = {}
                for l, x, 항, 키 in 표["줄"]:
                    키합[키] = 키합.get(키, 0.0) + x
                인건합 = sum(키합.get(k, 0.0) for k in 인건비성키) if any(k in 키합 for k in 인건비성키) else None
                인건줄 = " · ".join(l for l, _, _, k in 표["줄"] if k in 인건비성키)
                if not 연결:
                    if 인건합 is not None:
                        모.넣기(547, 열, 인건합, u, 출처 + " — 인건비성 줄 합(%s)" % 인건줄, 순)
                    continue
                if 열 not in 모.성격별:
                    모.성격별[열] = {"줄": 표["줄"], "합계": 합계, "단위": u, "출처": 출처}
                if 인건합 is not None:
                    모.넣기(531, 열, 인건합, u, 출처 + " — 인건비성 줄 합(%s — 급여 · 퇴직 · 복리후생 · 주식보상)" % 인건줄, 순)
                if "복리후생" in 키합:
                    모.넣기(540, 열, 키합["복리후생"], u, 출처, 순)
                if "주식보상" in 키합:
                    모.넣기(546, 열, 키합["주식보상"], u, 출처 + " — 성격별 줄", 1)
                if "상각" in 키합:
                    모.넣기(579, 열, 키합["상각"], u, 출처 + " — 상각 줄 합(%s)" % " · ".join(
                        l for l, _, _, k in 표["줄"] if k == "상각"), 순)
                if "재고변동" in 키합 and 구["재고변동반영"]:
                    모.넣기(578, 열, 키합["재고변동"], u, 출처, 순)
                # 원가 줄 — 성격 대응 먼저, 나머지는 끝에(나머지 = 합계 − 인건비성(인건비 · 복리후생 · 주식보상 — 531) − 상각 − 재고 변동(반영 = 예) −
                # 다른 원가 줄. 대체(개발비 자산화) · 미분류는 나머지에 남는다)
                줄값 = {}
                for x in 원가줄:
                    if x["대응"] == "성격" and ("원가%d" % x["번호"]) in 키합:
                        줄값[x["번호"]] = 키합["원가%d" % x["번호"]]
                for x in 원가줄:
                    if x["대응"] == "나머지":
                        if 합계 is None:
                            모.확인불가.setdefault("57%d" % x["번호"], "성격별 표의 합계를 못 읽은 기간이 있음(%s)" % 열)
                            continue
                        줄값[x["번호"]] = 합계 - sum(키합.get(k, 0.0) for k in 인건비성키 + ("상각",)) - (
                            키합.get("재고변동", 0.0) if 구["재고변동반영"] else 0.0) - sum(v for k, v in 줄값.items() if k != x["번호"])
                for k, v in 줄값.items():
                    모.넣기("57%d" % k, 열, v, u, 출처 + " — 원가 줄 %d(%s)" % (k, [x for x in 원가줄 if x["번호"] == k][0]["대응"]), 순)


def 직원모으기(보들, 모):
    """541 직원 수 · 542 연간급여 총액 · 543 1인 평균 급여액 · 549 소속 외 근로자 — 「직원 현황」 표(공시 범위 그대로 — 대개 본사).

    표준 서식의 칸 차례: [사업부문 · 성별] 정규 전체 · (단시간) · 기간제 전체 · (단시간) · 합계 · 평균근속연수 · 연간급여총액 · 1인평균급여액 ·
    소속 외 근로자 남 · 여 · 계 · 비고. 칸 자리로 읽는다(근속연수가 「7년0개월」처럼 글이어도 어긋나지 않게)."""
    def 값칸(줄):
        k = 0
        while k < len(줄) and 수(줄[k]) is None and not re.search(r"[0-9]", 줄[k] or ""):
            k += 1
        return 줄[k:]
    for 보 in 보들:
        for i0 in 머리찾기(보.행, r"직원(의|[ ]*등)?[ ]*현황"):
            u = None
            for 줄 in 보.행[i0: i0 + 8]:
                u = u or 단위읽기(줄)
            if u is None:
                continue
            합계줄, 첫줄 = None, None
            for 줄 in 보.행[i0: i0 + 40]:
                v = 값칸(줄)
                if len(v) < 8 or 수(v[0]) is None or 수(v[4]) is None:
                    continue
                if re.fullmatch(r"합계|총계|계", 표준(줄[0])):
                    합계줄 = v
                    break
                if 첫줄 is None:
                    첫줄 = v
            if not 합계줄:
                continue
            열 = 보.열("당", 흐름=False)
            출처 = "%s 「직원 현황」(%s 기준 — 공시 범위)" % (보.글(), 보.끝.isoformat())
            정, 기간제, 합 = 수(합계줄[0]), 수(합계줄[2]) or 0.0, 수(합계줄[4])
            if 정 is None or abs(정 + 기간제 - 합) > 0.5:
                모.대조.append({"이름": "직원 수 정규 + 기간제 = 합계", "열": 열, "값": (정 or 0) + 기간제, "다른값": 합, "출처": 출처})
                continue
            모.넣기(541, 열, 합, "명", 출처, 3)
            모.넣기(542, 열, 수(합계줄[6]), u, 출처, 3)
            모.넣기(543, 열, 수(합계줄[7]), u, 출처, 3)
            if 첫줄 and len(첫줄) >= 11 and all(re.search(r"[0-9]", 첫줄[x] or "") for x in (8, 9, 10)):
                남, 여, 계 = (수(첫줄[x]) for x in (8, 9, 10))
                if None not in (남, 여, 계) and abs(남 + 여 - 계) <= 0.5:
                    모.넣기(549, 열, 계, "명", 출처 + " — 소속 외 근로자 계", 3)
            break


def 라벨모으기(보들, 모):
    """주석의 라벨 값 — 판관비 명세 · 퇴직급여 · 기타지급채무 · 주식보상비용 · 약정액."""
    표들 = [  # (행, 머리 정규식, 라벨 정규식(공백 뺀 글), 열 정규식, 흐름인가)
        (532, r"판매비와\s*관리비에\s*대한\s*공시|판매비와\s*관리비\s*\(연결\)", r"급여", r"누적|공시금액|금액", True),
        (533, r"판매비와\s*관리비에\s*대한\s*공시|판매비와\s*관리비\s*\(연결\)", r"퇴직급여", r"누적|공시금액|금액", True),
        (534, r"판매비와\s*관리비에\s*대한\s*공시|판매비와\s*관리비\s*\(연결\)", r"복리후생비", r"누적|공시금액|금액", True),
        (539, r"확정기여제도에\s*대한\s*공시|확정기여제도", r"퇴직급여비용,?확정기여제도|확정기여형?퇴직급여|확정기여제도.*비용", r"누적|공시금액|금액", True),
        (544, r"기타\s*채무에\s*대한\s*공시|기타지급채무", r"단기미지급비용|미지급비용", r"공시금액|금액|유동", False),
        (545, r"기타\s*채무에\s*대한\s*공시|기타지급채무|기타\s*부채에\s*대한\s*공시|기타부채", r"기타장기종업원급여부채|장기종업원급여부채", None, False),
        (546, r"주식보상비용에\s*대한\s*공시|주식기준보상.{0,20}비용에\s*대한\s*공시", r"주식보상비용|주식기준보상비용", r"누적|공시금액|금액", True),
        (568, r"유형자산을\s*취득하기\s*위한\s*약정액", r"유형자산을취득하기위한약정액", None, False),
    ]
    for 행, 머리, 라벨, 열, 흐름 in 표들:
        for 보 in 보들:
            for i0 in 연결머리(보, 머리):
                for 표지, u, 머리줄, 자료, _ in 블록들(보.행, i0, 최대=200):
                    if 표지 is None:
                        continue
                    c = 보.열(표지, 흐름=흐름)
                    if c is None:
                        continue
                    n = max((len(r) - 1 for r in 자료), default=0)
                    v = 표값(자료, 라벨, 열=열, 열들=열이름(머리줄, n)) if 열 else 표값(자료, 라벨)
                    if v is None and 열:
                        v = 표값(자료, 라벨, k=1 if "누적" in " ".join(sum(머리줄, [])) else 0)
                    if v is not None:
                        모.넣기(행, c, v, u, "%s 주석 「%s」 %s" % (보.글(), 보.행[i0][0][:30], 표지), _순위(보, 표지))
                if "%s" % 행 in 모.원천 and any(x[0].startswith(보.글()) for x in 모.출처["%s" % 행].values()):
                    break


def 퇴직급여모으기(보들, 모):
    """538 확정급여 퇴직급여비용(기능별 합계) · 548 그 중 매출원가 — 「당기손익에 포함되는 퇴직급여비용」 표의 「합계」 줄(매출원가 열이 있을 때)."""
    for 보 in 보들:
        for i0 in 연결머리(보, r"당기손익에\s*포함되는\s*퇴직급여비용|퇴직급여비용의\s*배분"):
            for 표지, u, 머리줄, 자료, _ in 블록들(보.행, i0, 최대=60):
                c = 보.열(표지)
                if c is None:
                    continue
                n = max((len(r) - 1 for r in 자료), default=0)
                열들 = 열이름(머리줄, n)
                출처 = "%s 주석 「당기손익에 포함되는 퇴직급여비용」 %s" % (보.글(), 표지)
                if any("매출원가" in 표준(x) for x in 열들):          # 기능별 배분 열(매출원가 · 판관비 · 합계)이 있는 표
                    모.넣기(538, c, 표값(자료, r"합계", 열=r"기능별항목합계|합계", 열들=열들), u, 출처, _순위(보, 표지))
                    모.넣기(548, c, 표값(자료, r"합계", 열=r"매출원가", 열들=열들), u, 출처 + " — 매출원가 열", _순위(보, 표지))
                elif (any("누적" in 표준(x) for x in 열들) or n == 1) and any("근무원가" in 표준(r[0]) for r in 자료 if r):
                    # 원가 구성만 있는 표(반기 3개월 | 누적 · 연간 한 열)
                    모.넣기(538, c, 표값(자료, r"합계", 열=r"누적|공시금액|금액|당기", 열들=열들) if n > 1 else 표값(자료, r"합계"),
                          u, 출처, _순위(보, 표지))
            if 538 in 모.원천 or "538" in 모.원천:
                break


def 연구개발모으기(보들, 모):
    """535 인건비 · 536 연구개발비용 합계 · 537 개발비(무형자산) — 「연구개발비용」 표(열 = 제NN기 · 대개 셋)."""
    for 보 in 보들:
        if 보.기수 is None:
            continue
        합줄 = [i for i, r in enumerate(보.행) if any(re.fullmatch(r"연구개발비용(합계|계)", 표준(c)) for c in r[:2])]
        for i합 in 합줄:
            단위줄 = [i for i in range(max(0, i합 - 20), i합) if 단위읽기(보.행[i]) is not None]
            if not 단위줄:
                continue
            블 = 블록들(보.행, 단위줄[-1] - 1, 최대=40, 첫블록만=True)
            if not 블:
                continue
            표지, u, 머리줄, 자료, _ = 블[0]
            기열 = []
            for r in 머리줄:
                for c in r:
                    m = re.search(r"제\s*(\d+)\s*기", c)
                    if m:
                        기열.append((int(m.group(1)), bool(re.search(r"반기|분기", c))))
            if not 기열:
                continue

            def 줄값(라벨):
                for r in 자료:
                    for j in range(min(2, len(r))):
                        if re.fullmatch(라벨, 표준(r[j])):
                            수들 = [수(c) for c in r[j + 1:]]
                            return [v for v in 수들 if v is not None][:len(기열)]
                return None
            for 행, 라벨 in ((535, r"인건비"), (536, r"연구개발비용(합계|계)"), (537, r"개발비\(무형자산\)|개발비자산화|개발비\(자산\)")):
                값들 = 줄값(라벨)
                for (기, 중간), v in zip(기열, 값들 or []):
                    c = 보.열("당") if 중간 else 기간ID(FY실적, 보.회계연도 - (보.기수 - 기))
                    모.넣기(행, c, v, u, "%s 「연구개발비용」 표(제%d기%s)" % (보.글(), 기, " 누계" if 중간 else ""),
                          3 if (기 == 보.기수) else 1.5)
            break


_자산종류re = re.compile(r"토지|건물|구축물|기계|장치|설비|차량|운반구|비품|공구|기구|인테리어|시설|선박|항공|건설중|사용권|기타|합계|금형|"
                       r"집기|전산|서버|임차|개량|선로|전송|통신|광학|탱크|궤도|열차")


def _유형열(이름):
    k = 표준(이름)
    if re.search(r"합계|총계", k) or k in ("유형자산", "계"):
        return "합계"
    if "토지" in k:
        return "토지"
    if "건설중" in k:
        return "건설중"
    return k


def 자산군나누기(열이름들, 대응):
    """유형자산 표의 자산 종류 → 자산군 g. 대응 = {g: [이름…] 또는 "나머지"}. 토지 · 건설중인자산 · 합계는 어느 자산군에도 넣지 않는다."""
    낸, 쓴 = {}, set()
    for g, 이름들 in sorted(대응.items()):
        if 이름들 == "나머지":
            continue
        for c in 열이름들:
            if any(표준(n) == _유형열(c) or 표준(n) in 표준(c) for n in 이름들):
                낸.setdefault(g, []).append(c)
                쓴.add(c)
    for g, 이름들 in 대응.items():
        if 이름들 == "나머지":
            낸[g] = [c for c in 열이름들 if c not in 쓴 and _유형열(c) not in ("합계", "토지", "건설중")]
    return 낸


def _종류줄(머리줄):
    """머리줄 가운데 자산 종류 이름이 가장 많은 줄의 종류 목록(빈 칸 · 「유형자산」 같은 묶음 머리는 뺀다)."""
    best = []
    for r in 머리줄:
        이름 = [c for c in r if c and _자산종류re.search(표준(c)) and 표준(c) not in ("유형자산",)]
        if len(이름) > len(best):
            best = 이름
    return best


def 유형표읽기(머리줄, 자료):
    """유형자산 주석의 블록 하나 → ("장부" | "변동" | "다단", {종류: …}) 또는 None.

    세 꼴을 읽는다. ① 장부금액 표(줄 = 자산 종류 · 열 = 취득원가 … 장부금액) ② 변동 표(줄 = 기초 · 취득 · 대체 · 감가상각 · 기말 ·
    열 = 자산 종류) ③ 다단 머리(XBRL — 열이 「자산 종류 × 총장부금액 · 상각누계액 · … · 장부금액 합계」로 겹쳐 펼쳐진 변동 표). ③ 은 종류마다
    첫 측정 = 총장부금액(취득원가), 마지막 측정 = 장부금액 합계로 읽는다."""
    줄들 = [(l, v) for l, v in (줄라벨값(r) for r in 자료) if l]
    if not 줄들:
        return None
    n = max(len(v) for _, v in 줄들)
    열들 = 열이름(머리줄, n)
    종류 = _종류줄(머리줄)
    if any(re.search(r"취득원가|총장부금액", 표준(x)) for x in 열들) and any(_자산종류re.search(표준(l)) for l, _ in 줄들):
        표 = {}
        for l, v in 줄들:
            d = list(zip(열들[-len(v):], v))
            원 = next((x for k, x in d if re.search(r"취득원가|총장부금액", 표준(k)) and x is not None), None)
            장 = next((x for k, x in d if "장부금액" in 표준(k) and "총장부금액" not in 표준(k) and x is not None), None)
            표[l] = {"취득원가": 원, "순장부": 장}
        return "장부", 표
    if len(종류) >= 2 and n > len(종류) and (n % len(종류) == 0 or (n - 1) % len(종류) == 0):
        m = n // len(종류) if n % len(종류) == 0 else (n - 1) // len(종류)       # 끝에 전체 합계 열 하나가 붙는 꼴도 있다
        표 = {}
        for l, v in 줄들:
            if len(v) > n:
                continue
            v = list(v) + [None] * (n - len(v))                  # 끝의 빈 칸이 생략된 줄
            for q, 이름 in enumerate(종류):
                묶 = v[q * m:(q + 1) * m]
                끝 = 묶[-1] if 묶[-1] is not None else next((x for x in 묶 if x is not None), None)
                표.setdefault(이름, {})[표준(l)] = {"첫": 묶[0], "끝": 끝}
        return "다단", 표
    if any(_유형열(x) == "합계" for x in 열들) and any(re.match(r"(기초|취득)", 표준(l)) for l, _ in 줄들):
        표 = {}
        for l, v in 줄들:
            for 이름, x in zip(열들[-len(v):], v):
                표.setdefault(이름, {})[표준(l)] = x
        return "변동", 표
    return None


# FX-A R2(2026-10-25) — 「사업결합 이외의 증가」 는 사업결합이 아니라 취득이다(부정 접두 — F33 · F60). 투자부동산과 오간 대체는 편입(취득 + 대체)에
# 넣지 않고 `투자부동산대체` 로 따로 둔다(CAPEX 밖 — 양방향, F15 · F40 · F53)
_변동줄 = {"기말": r"기말.*", "취득": r"취득.*|증가|자본적지출.*|사업결합\s*(이외|외|제외).*",
          "대체": r"(?!.*투자부동산)(?!매각예정).*대체(\(\*\d*\))?", "사업결합": r"(?!.*(이외|제외|외의))(사업결합|연결범위변동).*",
          "투자부동산대체": r".*투자부동산.*",
          "상각": r"감가상각(비)?|상각(비)?", "처분": r"처분.*|폐기"}


def _변동값(줄표, 키, 끝=True):
    """변동 표의 줄 이름(공백 뺀 글) → 값. 다단 머리 꼴이면 {"첫", "끝"} 가운데 끝(장부금액 합계) 또는 첫(총장부금액)."""
    for 이름, x in 줄표.items():
        if re.fullmatch(_변동줄[키], re.sub(r",?유형자산$", "", re.sub(r"^유형자산의?", "", 이름))):
            if isinstance(x, dict):
                return x.get("끝" if 끝 else "첫")
            return x
    return None


def 유형모으기(보들, 모, 구):
    """유형자산 주석(연결)과 「생산설비의 현황」을 자산 종류별 원 자료(`모.유형원`)로 모은 뒤 자산군으로 묶어 56g · 56(3+g) · 59(6+g) ·
    567 · 569 를 낸다. 자산군 대응이 없으면(가정 없음) 최근 취득원가가 큰 두 종류 + 나머지(토지 · 건설중 제외)로 셋을 제안한다."""
    원 = 모.유형원                                         # {종류: {측정: {열: (값, 단위, 출처, 순위)}}}

    def 둠(종류, 측정, 열, 값, u, 출처, 순위):
        if 열 is None or 값 is None:
            return
        종류 = 표준(종류).replace("기타의", "기타").replace("의유형자산", "유형자산")    # 표마다 다른 표기(「기타의유형자산」 · 「기타유형자산」)를 하나로
        옛 = 원.setdefault(종류, {}).setdefault(측정, {}).get(열)
        if 옛 is None or 옛[3] < 순위:
            원[종류][측정][열] = (값, u, 출처, 순위)
    for 보 in 보들:
        시작들 = [i for i in range(len(보.행)) if 보.연결[i] and _주석머리(보.행[i]) and re.search(r"유형자산", 보.행[i][0])
                 and not re.search(r"무형|사용권|투자부동산|처분|손상|매각", 보.행[i][0])]
        if not 시작들:
            시작들 = 연결머리(보, r"유형자산.{0,12}(장부금액|세부\s*정보|변동|금액)")
        본 = set()
        for i0 in 시작들:
            블들 = [b for b in 블록들(보.행, i0, 최대=3000) if b[4] not in 본]
            # 표지 없는 변동 표(S5-08) — 옛 원문은 「나. 당기 및 전기 중 … 변동내역」 아래에 표지 줄 없이 당기 · 전기 표를 차례로 둔다.
            # 한 주석 안에서 표지가 하나도 없는 변동 표가 꼭 둘이면 차례대로 당 · 전기로 읽는다(셋 이상이면 어느 것이 어느 해인지 몰라 읽지 않는다)
            무표 = [k for k, b in enumerate(블들) if b[0] is None and (유형표읽기(b[2], b[3]) or ("",))[0] == "변동"]
            if len(무표) == 2 and not any(b[0] for b in 블들 if (유형표읽기(b[2], b[3]) or ("",))[0] == "변동"):
                for k, 표지 in zip(무표, ("당", "전기")):
                    블들[k] = (표지,) + tuple(블들[k][1:])
            for 표지, u, 머리줄, 자료, 블번호 in 블들:
                if 블번호 in 본 or 표지 is None:
                    continue
                본.add(블번호)
                읽 = 유형표읽기(머리줄, 자료)
                if not 읽:
                    continue
                꼴, 표 = 읽
                순 = 3 if 표지 == "당" else 1.5
                if 꼴 == "장부":
                    c = 보.열(표지, 흐름=False)
                    for 종류, d in 표.items():
                        둠(종류, "취득원가", c, d["취득원가"], u, "%s 주석 「유형자산」 장부금액 %s" % (보.글(), 표지), 순)
                        둠(종류, "순장부", c, d["순장부"], u, "%s 주석 「유형자산」 장부금액 %s" % (보.글(), 표지), 순)
                    continue
                c, cb = 보.열(표지), 보.열(표지, 흐름=False)
                출처 = "%s 주석 「유형자산」 변동 %s" % (보.글(), 표지)
                for 종류, 줄표 in 표.items():
                    둠(종류, "순장부", cb, _변동값(줄표, "기말"), u, 출처, 순)
                    if 꼴 == "다단":
                        둠(종류, "취득원가", cb, _변동값(줄표, "기말", 끝=False), u, 출처 + " — 총장부금액", 순)
                    x = _변동값(줄표, "상각")
                    둠(종류, "상각", c, abs(x) if x is not None else None, u, 출처, 순)
                    # S5-10 · S5-15 — 편입 = 취득 + 대체(유지 · 증설 편입 — 스키마 569 정의). 사업결합(회사를 사는 돈 · 연결범위 변동)은
                    # 편입에 넣지 않고 `사업결합` 으로 따로 둔다(「회사를 사는 돈이 섞였는지」). 취득 · 대체도 따로 둔다(E · F 가 나눠 읽는다)
                    편 = {k: _변동값(줄표, k) for k in ("취득", "대체", "사업결합", "투자부동산대체")}
                    for k, v in 편.items():
                        if v is not None:
                            둠(종류, k, c, v, u, 출처, 순)
                    편.pop("투자부동산대체", None)
                    if 편["취득"] is not None or 편["대체"] is not None:
                        둠(종류, "편입", c, (편["취득"] or 0.0) + (편["대체"] or 0.0), u, 출처 + " — 취득 + 대체(사업결합 뺌)", 순)
                    x = _변동값(줄표, "처분")
                    둠(종류, "처분", c, abs(x) if x is not None else None, u, 출처, 순)
        # 「생산설비의 현황」(사업의 내용 — 행 = 취득원가 · 순장부 · 변동, 날짜 구획, 열 = 자산 종류)
        for i0 in 머리찾기(보.행, r"생산설비의\s*현황"):
            for 표지, u, 머리줄, 자료, _ in 블록들(보.행, i0, 최대=60, 첫블록만=True):
                n = max((len(r) - 1 for r in 자료), default=0)
                열들 = 열이름(머리줄, n)
                if not any(_유형열(x) == "합계" for x in 열들):
                    continue

                def 날짜줄(r):
                    return bool(r) and bool(re.fullmatch(r"\d{4}\.\d{2}\.\d{2}", r[0].strip())) and all(x in ("", "-") for x in r[1:])
                날, 구획 = None, {}
                for r in 머리줄:
                    if 날짜줄(r):
                        날 = r[0].strip()
                for r in 자료:
                    if 날짜줄(r):
                        날 = r[0].strip()
                        continue
                    if len(r) < 2:
                        continue
                    값 = [수(x) for x in r[1:]]
                    구획.setdefault(날, {})[표준(r[0])] = dict(zip(열들[-len(값):], 값))
                날들 = sorted(d for d in 구획 if d)
                if not 날들:
                    continue
                출처 = "%s 「생산설비의 현황」" % 보.글()
                c끝, c처음 = 보.열("당", 흐름=False), 기간ID(FY실적, 보.회계연도 - 1)
                for 날짜, c, 순 in ((날들[0], c처음, 1), (날들[-1], c끝, 2)):
                    for 종류, x in (구획[날짜].get("취득원가") or {}).items():
                        둠(종류, "취득원가", c, x, u, 출처 + " " + 날짜, 순)
                for k, c, 순 in (("기초순장부금액", c처음, 1), ("기말순장부금액", c끝, 2)):
                    for d in 날들 + [None]:
                        if k in (구획.get(d) or {}):
                            for 종류, x in 구획[d][k].items():
                                둠(종류, "순장부", c, x, u, 출처 + " " + k, 순)
                            break
                편 = {}
                for d in 날들 + [None]:
                    for k, 표 in (구획.get(d) or {}).items():
                        if re.fullmatch(r"취득|대체(\(\*\d*\))?", k):          # 사업결합은 편입이 아니다(S5-10)
                            for x, v in 표.items():
                                if v is not None:
                                    편[x] = 편.get(x, 0.0) + v
                        if re.fullmatch(r"감가상각(비)?", k):
                            for x, v in 표.items():
                                둠(x, "상각", c끝, abs(v) if v is not None else None, u, 출처 + " 감가상각", 2)
                for x, v in 편.items():
                    둠(x, "편입", c끝, v, u, 출처 + " — 취득 + 대체", 2)
    # 자산군으로 묶기
    종류들 = [k for k in 원 if _유형열(k) not in ("합계", "토지", "건설중")]
    대응 = 구["자산군대응"]
    if not 대응 and 종류들:
        def 최근원가(k):
            d = 원[k].get("취득원가") or 원[k].get("순장부") or {}
            return d[max(d)][0] if d else 0.0
        큰 = sorted(종류들, key=lambda k: -(최근원가(k) or 0.0))[:2]
        대응 = {g + 1: [k] for g, k in enumerate(큰)}
        if len(종류들) > len(큰):
            대응[len(큰) + 1] = "나머지"
        구["자산군대응"] = 대응
        구["자산군제안"] = True
    g열 = 자산군나누기(종류들, 대응)
    for g, 열들 in g열.items():
        for 측정, 번호 in (("취득원가", 560 + g), ("순장부", 563 + g), ("상각", 596 + g)):
            있는 = [x for x in 열들 if 원.get(x, {}).get(측정)]
            기간 = set().union(*(원[x][측정].keys() for x in 있는)) if 있는 else set()
            for c in 기간:
                칸 = [원[x][측정][c] for x in 있는 if c in 원[x][측정]]
                if len(칸) != len(있는):
                    continue                                   # 그 기간에 자산군의 종류 일부만 있으면 합을 내지 않는다
                v = sum(t[0] * 단위배.get(t[1], 1.0) for t in 칸) / 단위배.get(칸[0][1], 1.0)
                모.넣기(번호, c, v, 칸[0][1], 칸[0][2] + " — 자산군 %d(%s)" % (g, " · ".join(열들)), min(t[3] for t in 칸))
    for x in 원:
        if _유형열(x) == "건설중":
            for c, t in 원[x].get("순장부", {}).items():
                모.넣기(567, c, t[0], t[1], t[2] + " — 건설중인자산", t[3])
    기준g = 구["유지기준자산군"]
    if 기준g in g열:
        있는 = [x for x in g열[기준g] if 원.get(x, {}).get("편입")]
        기간 = set().union(*(원[x]["편입"].keys() for x in 있는)) if 있는 else set()
        for c in 기간:
            칸 = [원[x]["편입"][c] for x in 있는 if c in 원[x]["편입"]]
            if len(칸) == len(있는):
                모.넣기(569, c, sum(t[0] for t in 칸), 칸[0][1], 칸[0][2] + " — 자산군 %d 편입" % 기준g, min(t[3] for t in 칸))


# ────────────────────────────────────────────────────────────── S5 — 내용연수 · 상각방법 · 사용권 신규 · 투자계획(공시) — 업종 중립

_연수re = re.compile(r"(\d{1,2})\s*(?:년)?\s*(?:~|∼|-|–|—|내지|에서)\s*(\d{1,2})\s*년|(\d{1,2})\s*년")
_상각법re = re.compile(r"정액법|정률법|생산량\s*비례법|연수\s*합계법|이중체감법")


def 내용연수모으기(보들):
    """유형자산 회계정책 문단의 「추정 내용연수」 표(자산 종류 · 연수)와 상각방법(정액 · 정률 · 생산량비례) — 가장 최근 보고서에서(S5-17).
    → {"종류": {이름: [하, 상]}, "상각방법": [..], "출처": 글} 또는 None. 회계정책 문단은 연결 주석 「유의적 회계정책」 안에 있다."""
    for 보 in 보들:
        for i in range(len(보.행)):
            c = " ".join(보.행[i])
            if not (보.연결[i] and re.search(r"내용\s*연(수|한)", c) and re.search(r"유형자산|추정|다음과", c)):
                continue
            앞글 = " ".join(" ".join(r) for r in 보.행[max(0, i - 8): i + 1])
            if "무형" in 앞글[-120:] and "유형자산" not in 앞글[-200:]:
                continue
            종류, 칸들 = {}, []
            for r in 보.행[i + 1: i + 60]:
                if len(r) == 1 and (_주석머리(r) or len(r[0]) > 80):
                    break
                칸들 += [x for x in r if x]
            이름 = None
            for x in 칸들:
                m = _연수re.search(x)
                if m and len(x) <= 30:
                    if 이름 and not re.fullmatch(r"구\s*분|내\s*용\s*(연|년)\s*수|추정\s*내용연수", 이름):
                        lo, hi = (int(m.group(1)), int(m.group(2))) if m.group(1) else (int(m.group(3)), int(m.group(3)))
                        종류[표준(이름)] = [min(lo, hi), max(lo, hi)]
                    이름 = None
                elif not 수(x) and len(x) <= 30:
                    이름 = x
            if len(종류) >= 2:
                방법 = sorted(set(표준(m.group(0)) for m in _상각법re.finditer(" ".join(" ".join(r) for r in 보.행[max(0, i - 12): i + 3]))))
                return {"종류": 종류, "상각방법": 방법 or ["확인 불가"], "출처": "%s 회계정책 「%s」" % (보.글(), c[:40])}
    return None


_사용권증가문 = re.compile(r"(?:당기|당반기|당분기)\s*중\s*(?:증가된|증가한|신규로\s*인식한|새로\s*인식한)\s*사용권자산(?:은|의\s*금액은)\s*([\d,]+)\s*(백만원|천원|원)"
                     r"\s*(?:\(\s*전(?:기|반기|분기)\s*:?\s*([\d,]+)\s*(백만원|천원|원)?\s*\))?")


def 사용권모으기(보들, 모):
    """사용권자산 신규(리스 주석의 사용권자산 변동 표 「증가 · 취득 · 신규」의 합계 열) — 매장 · 임차 설비 회사의 점포 투자가 리스로 오는 몫(S5-14 · S5-15).
    유형자산 주석에 사용권 열이 있으면(유형모으기의 종류 「사용권」) 그쪽을 쓴다. → {열: 값} (목표 단위)"""
    낸 = {}
    for 보 in 보들:
        for i0 in [i for i in range(len(보.행)) if 보.연결[i] and _주석머리(보.행[i]) and re.search(r"사용권자산|리스", 보.행[i][0])]:
            for 표지, u, 머리줄, 자료, _ in 블록들(보.행, i0, 최대=600):
                if 표지 is None:
                    continue
                읽 = 유형표읽기(머리줄, 자료)
                if not 읽 or 읽[0] != "변동":
                    continue
                합 = next((v for k, v in 읽[1].items() if _유형열(k) == "합계"), None)
                if not 합:
                    continue
                x = None
                for 이름, v in 합.items():
                    if re.fullmatch(r"(증가|취득|신규|신규계약|신규리스|추가|증가\(신규계약\)).*", 이름):
                        x = v.get("끝") if isinstance(v, dict) else v
                        break
                c = 보.열(표지)
                if x is not None and c and c not in 낸:
                    낸[c] = abs(x) * 단위배.get(u, 1.0) / 단위배[모.단위]
        # 변동 표가 없고 문장(「당기 중 증가된 사용권자산은 836,842백만원(전기: 53,053백만원)입니다」)과 값 하나짜리 공시금액 표만 있는 서식
        # (2026-10-23 실측 — 사용권신규가 비었다). 연결 구획의 문장에서 당기 · 전기 값을 읽는다(흐름이라 반기 보고서의 전기는 모델 열이 아니다)
        for i, 행 in enumerate(보.행):
            if not 보.연결[i]:
                continue
            m = _사용권증가문.search(" ".join("%s" % x for x in 행 if x))
            if not m:
                continue
            for 값, 단, 표지 in ((m.group(1), m.group(2), "당"), (m.group(3), m.group(4) or m.group(2), "전기")):
                c = 보.열(표지) if 값 else None
                if c and c not in 낸:
                    낸[c] = float(값.replace(",", "")) * 단위배.get(단, 1.0) / 단위배[모.단위]
            break
    for 종류, 측정 in 모.유형원.items():
        if "사용권" in 종류 and 측정.get("취득"):
            for c, t_ in 측정["취득"].items():
                낸.setdefault(c, abs(t_[0]) * 단위배.get(t_[1], 1.0) / 단위배[모.단위])
    return 낸


_투자머리 = re.compile(r"구\s*분|투자\s*대상|투자\s*효과|투자\s*기간|기\s*투자|향후\s*투자|총\s*투자|예상\s*투자|투자\s*(금액|내용|계획)|비\s*고|"
                     r"사업\s*부문|계획\s*명칭|당기\s*투자|투자\s*액")


def 투자계획모으기(보들, 모):
    """사업의 내용 「투자계획(현황)」 · 「설비의 신설 · 매입 계획」 표 — 줄마다 {구분, 대상, 효과, 기간, 총투자, 기투자, 향후투자, 단위, 출처}(S5-19 · S5-20).
    가장 최근 보고서 하나에서 읽는다. 금액은 목표 단위로 바꾼다. 「공정공시 · 신규시설투자」 문장의 투자 규모(「총 15조원 규모」)는 `발화` 로 따로 둔다
    — 회사 발화다(공시 표가 아니다). 프로젝트 · 기집행을 이 표로 세우는 것은 F 갈래(CP1)다.
    FX-A R2(2026-10-25) — 곁에 XML 이 있으면 격자로 읽는다(`투자계획XML` — 병합 행 열 밀림 · 「총액(기지출)」 꼴 · 연도 열 · 한 절 안 표 둘 ·
    「진행 중인 투자」). XML 이 하나도 없을 때만 아래 txt 길. 줄에 `종류`(진행중 · 계획) · `표번호` · `검산` · `주` 를 더한다."""
    x = 투자계획XML(보들, 모)
    if x is not None:
        return x["표"], 투자발화모으기(보들, 모), x["진행중"]
    낸, 발화 = [], []
    for 보 in 보들:
        for i0 in 머리찾기(보.행, r"투자\s*계획|설비의\s*신설|설비\s*투자\s*(계획|현황)|신설\s*·?\s*매입"):
            if len(보.행[i0][0]) > 40 or not re.search(r"투자|설비", 보.행[i0][0]):
                continue
            u = None
            j = i0 + 1
            while j < min(len(보.행), i0 + 12):
                u = 단위읽기(보.행[j]) or u
                if any(_투자머리.fullmatch(표준(x) or "") or _투자머리.match(x or "") for x in 보.행[j] if x) and u:
                    break
                j += 1
            if not u or j >= min(len(보.행), i0 + 12):
                continue
            칸 = []
            for r in 보.행[j: j + 120]:
                if len(r) == 1 and (_주석머리(r) or re.match(r"^\d\.\s", r[0] or "")) and 칸:
                    break
                칸 += [x for x in r if x != ""]
            머리 = []
            while 칸 and _투자머리.match(칸[0]) and len(칸[0]) <= 20:
                머리.append(표준(칸.pop(0)))
            n = len(머리)
            if n < 3 or not any(re.search(r"투자", h) for h in 머리):
                continue
            배 = 단위배.get(u.replace("(", "").replace(")", ""), None) or {"십억원": 1e9, "조원": 1e12}.get(u, 1.0)
            while len(칸) >= 2:
                if re.fullmatch(r"합\s*계|계|총\s*계", 칸[0] or ""):
                    break
                줄, 칸 = 칸[:n], 칸[n:]
                if len(줄) < n:
                    break
                d = dict(zip(머리, 줄))
                y = {"구분": d.get("구분") or 줄[0], "단위": u, "출처": "%s 「%s」" % (보.글(), 보.행[i0][0][:30])}
                for h, v in d.items():
                    if re.search(r"대상", h):
                        y["대상"] = v
                    elif re.search(r"효과", h):
                        y["효과"] = v
                    elif re.search(r"기간", h):
                        y["기간"] = v
                    elif re.search(r"기투자|당기투자|누적", h) and 수(v) is not None:
                        y["기투자"] = 수(v) * 배 / 단위배[모.단위]
                    elif re.search(r"향후|예상|잔여", h) and 수(v) is not None:
                        y["향후투자"] = 수(v) * 배 / 단위배[모.단위]
                    elif re.search(r"총", h) and 수(v) is not None:
                        y["총투자"] = 수(v) * 배 / 단위배[모.단위]
                낸.append(y)
            if 낸:
                break
        # 공시 문장 — 「장래사업 · 경영계획」 · 「신규시설투자」 제목 줄의 투자 규모(조 · 억원)
        for i, r in enumerate(보.행):
            c = " ".join(r)
            if "제목" in c and "투자" in c and re.search(r"(\d[\d,.]*)\s*(조|억)\s*원", c):
                for m in re.finditer(r"(?:총|약)?\s*(\d[\d,.]*)\s*(조|억)\s*원", c):
                    try:
                        v = float(m.group(1).replace(",", "")) * (1e12 if m.group(2) == "조" else 1e8)
                    except ValueError:
                        continue
                    발화.append({"문장": c[max(0, m.start() - 80): m.end() + 20][:200], "금액": v / 단위배[모.단위], "출처": 보.글(), "딱지": "[회사주장]"})
                    break
        if 낸 or 발화:
            break
    return 낸, 발화[:12], []


def 투자발화모으기(보들, 모):
    """공시 문장 — 「장래사업 · 경영계획」 · 「신규시설투자」 제목 줄의 투자 규모(조 · 억원) — 가장 최근에 그런 줄이 있는 보고서에서(회사 발화)."""
    발화 = []
    for 보 in 보들:
        for i, r in enumerate(보.행):
            c = " ".join(r)
            if "제목" in c and "투자" in c and re.search(r"(\d[\d,.]*)\s*(조|억)\s*원", c):
                for m in re.finditer(r"(?:총|약)?\s*(\d[\d,.]*)\s*(조|억)\s*원", c):
                    try:
                        v = float(m.group(1).replace(",", "")) * (1e12 if m.group(2) == "조" else 1e8)
                    except ValueError:
                        continue
                    발화.append({"문장": c[max(0, m.start() - 80): m.end() + 20][:200], "금액": v / 단위배[모.단위], "출처": 보.글(), "딱지": "[회사주장]"})
                    break
        if 발화:
            break
    return 발화[:12]


# ────────────────────────────────────────────────────────────── FX-A R2 — 공시 원문 XML 표(격자)로 읽기 — 업종 중립
# txt 줄 읽기는 ROWSPAN · COLSPAN 이 사라져 병합 행이 한 칸씩 밀린다(투자계획 표 55조각 · 「5,208」 이 프로젝트 이름 · F5 · F17 · F22). 곁의 XML 이
# 있으면 `공시표` 격자로 읽는다 — 칸 자리를 지키고, 표 경계는 XML 의 TABLE 하나다. XML 이 없으면 옛 txt 길이 그대로 돈다(옛 회차 호환).
# 읽는 보고서 차례(`_읽을보고서`): 가장 늦은 기간의 보고서(기준일 반기 · 분기 포함 — R1) 먼저, 그다음 사업보고서를 늦은 것부터.

def _문(보):
    """보고서 곁의 XML(공시표 문서) — 없으면 None(보고서마다 한 번만 읽는다)."""
    if not hasattr(보, "_문서"):
        p = 공시표.곁XML(getattr(보, "경로", None))
        보._문서 = 공시표.읽기(p) if p else None
    return 보._문서


def _읽을보고서(보들, 다년=True):
    """표 읽기의 보고서 차례 — 가장 늦은 기간의 보고서(기준일 반기 · 분기 포함) 먼저, 그다음 사업보고서를 늦은 것부터(다년 = False 면 최신 사업보고서 하나만)."""
    def 쓸만(b):
        f = getattr(b, "쓸만한가", None)
        return f() if callable(f) else bool(getattr(b, "종류", None))
    늦은 = sorted([b for b in 보들 if 쓸만(b)], key=lambda b: (getattr(b, "끝", None) or datetime.date.min, getattr(b, "종류", "") == "사업",
                                                       getattr(b, "접수", "")), reverse=True)
    if not 늦은:
        return []
    사업 = [b for b in 늦은 if b.종류 == "사업" and b is not 늦은[0]]
    return [늦은[0]] + (사업 if 다년 else 사업[:1])


def _사업표(문):
    return [t for t in ((문 or {}).get("표") or []) if any(re.search(r"사업의\s*내용", x) for x in t["제목경로"])]


def _주석표(문, 연결=True):
    """연결(또는 별도) 주석 구획의 표 — 제목경로로 가른다(연결 구획이 없는 회사는 구획 모름 표도 쓴다)."""
    표들 = (문 or {}).get("표") or []
    있음 = any(t["연결"] is True for t in 표들)
    return [t for t in 표들 if t["연결"] is 연결 or (not 있음 and t["연결"] is None)]


_주제re = (("능력", r"생산\s*능력"), ("실적", r"생산\s*실적|판매\s*실적|매출\s*실적|생산\s*및\s*판매|매출\s*현황"), ("가동률", r"가\s*동\s*률"),
          ("수주", r"수주\s*(상황|현황|잔고|잔량)|계약\s*잔액"),
          ("투자", r"투자\s*(계획|현황)|진행\s*중인\s*투자|설비의\s*신설|신설\s*·?\s*매입|(시설|설비)\s*투자|투자\s*계획"),
          ("가격", r"가격\s*변동"), ("원재료", r"원\s*재\s*료"))


def _표주제(표):
    """표 바로 앞 머리 글(단위 줄 뺀 마지막 셋)에서 표의 주제 — ① 번호 머리(「(3) 가동률」 · 「나. 생산실적 및 가동률 (1) 생산실적」 ·
    「2) 향후 투자 계획」)에 붙은 주제 가운데 가장 뒤의 것 ② 번호 머리가 없으면 각주(※ · * · 주1))가 아닌 글의 마지막 주제 낱말.
    각주는 앞 표에 딸린 글이다(「※ 상기 생산능력은 …」 이 생산실적 표 앞에 있어 실적 표를 능력 표로 읽던 함정)."""
    앞 = [x for x in 표["앞글"] if not (공시표.단위읽기(x) and len(x) <= 60)][-3:]
    글 = " ".join(앞) or " ".join(표["제목경로"][-1:])
    고른 = None
    for mk in re.finditer(r"(?:\(\d{1,2}\)|\d{1,2}\)|[가-하]\.|\d{1,2}(?:-\d{1,2})?\.)\s*", 글):
        창 = 글[mk.end(): mk.end() + 16]
        첫 = None
        for 이름, p in _주제re:
            m = re.search(p, 창)
            if m and (첫 is None or m.start() < 첫[0]):
                첫 = (m.start(), 이름)
        if 첫:
            고른 = 첫[1]                     # 번호 머리 바로 뒤의 첫 주제 — 가장 뒤의 번호 머리가 이긴다
    if 고른:
        return 고른
    끝 = {}
    글2 = " ".join(x for x in 앞 if not re.match(r"^\s*(※|\*|주\s*\d*\)|\(주\d*\))", x))
    for 이름, p in _주제re:
        for m in re.finditer(p, 글2):
            끝[이름] = m.end()
    return max(끝, key=끝.get) if 끝 else None

def _기간이름(x, 보):
    """표 머리 열 이름 → 기간 ID — 「제27기 반기(2026년 반기)」 · 「제26기(2025년)」 · 「제27기 (2026.01.01~6.30)」 · 「2025년」 · 「당기」. 모르면 None."""
    k = 표준(x)
    if not k:
        return None
    끝달 = re.search(r"~\s*(?:\d{4}[.\-])?(\d{1,2})[.\-]\d{1,2}", k)
    부분 = bool(re.search(r"반기|분기|누적|\d{1,2}월", k)) or bool(끝달 and int(끝달.group(1)) != 12)
    if 부분:
        return 보.열("당", 흐름=False) if 보.종류 in ("반기", "분기") else None
    m = re.search(r"제(\d+)기", k)
    if m and 보.기수 and 보.회계연도:
        return 기간ID(FY실적, 보.회계연도 - (보.기수 - int(m.group(1))) - (0 if 보.종류 == "사업" else 0))
    y = re.search(r"(20\d\d)년?", k)
    if y:
        return 기간ID(FY실적, int(y.group(1)))
    if k in _기간표지:
        return 보.열(_기간표지[k], 흐름=False)
    return None


def _산출기준(단위, 글=""):
    """생산능력 줄의 산출 기준 — 인시(MH · 공수) · 시간 · 실적기준(「생산실적 기준」 — 능력 = 실적, 상한 아님) · 금액(원 단위) · 물량 · 모름."""
    u = 표준(단위)
    if re.search(r"(?i)M/?H|공수|인시|MANHOUR", u):
        return "인시"
    if re.search(r"시간|^H$|^Hr$", u):
        return "시간"
    if re.search(r"생산\s*실적\s*기준|실적\s*기준|생산량\s*기준|역산|생산\s*실적\s*(대비|÷|/|을)\s*(평균\s*)?가동률", 글 or ""):
        return "실적기준"
    if re.search(r"원$|달러|USD|KRW", u):
        return "금액"
    return "물량" if u else "모름"


def 생산능력표모으기(보들):
    """FX-A R2 — 사업의 내용 「생산능력」 표(XML 격자) → [{"품목", "단위", "값": {기간: 값}, "산출기준", "주석글", "출처"}].
    품목 · 단위가 같은 줄은 보고서를 건너 하나로 묶는다(늦은 보고서의 값이 이긴다). 합계 줄은 단위가 하나일 때만 남긴다.
    F 의 능력단위 재료다(도구판 능력단위 1 / 42 의 원인 — 공시 「생산능력」 표를 F 로 못 넘겼다). 값만 낸다 — 상한 판정은 F."""
    묶, 차례 = {}, []
    for 보 in _읽을보고서(보들):
        for 표 in _사업표(_문(보)):
            if _표주제(표) != "능력":
                continue
            열기간 = [_기간이름(x, 보) for x in 표["열이름"]]
            if any(re.search(r"능력", 표준(x)) for x in 표["열이름"]):
                # 「생산능력, 생산실적 및 가동률」 한 표 — 능력 열만(실적 · 가동률 열은 가동률 쪽이 읽는다)
                열기간 = [c if (c and not re.search(r"실적|가동", 표준(x))) else None for c, x in zip(열기간, 표["열이름"])]
            j단 = 공시표.열찾기(표, r"^단위$")
            if not any(열기간):
                # 「생산능력 | 생산실적 | 산출근거」 열 꼴(기간 열이 없고 능력이 한 열) — 그 열이 보고서 당기의 능력이다(FX4-F M4)
                j능 = [j for j, x in enumerate(표["열이름"]) if re.search(r"능력|CAPA", 표준(x), re.I) and not re.search(r"실적|가동|산출|근거|기준", 표준(x))]
                수열 = [j for j in range(표["열수"]) if j != j단 and any(공시표.칸수(표, i, j) is not None for i in range(표["머리줄수"], 표["줄수"]))]
                if len(j능) == 1 and j능[0] in 수열:
                    열기간[j능[0]] = 보.열("당", 흐름=False)
                elif len(수열) == 1:
                    열기간[수열[0]] = 보.열("당", 흐름=False)
            첫 = min((j for j, c in enumerate(열기간) if c), default=None)
            if 첫 is None:
                continue
            주석 = next((x for x in 표["뒷글"][:4] if re.search(r"산출|산정|기준|역산|계산", x)), "")
            단위들 = set()
            줄모음 = []
            for i in range(표["머리줄수"], 표["줄수"]):
                r = 표["격자"][i]
                이름 = " ".join(dict.fromkeys(r[j] for j in range(첫) if j != j단 and r[j] and 공시표.수(r[j]) is None))
                if not 이름:
                    continue
                u = (r[j단] if j단 is not None and j단 < len(r) else "") or 표["단위"] or ""
                값 = {}
                for j, c in enumerate(열기간):
                    v = 공시표.칸수(표, i, j) if c else None
                    if c and v is not None:
                        값[c] = v
                if 값:
                    줄모음.append((이름, u, 값))
                    if not re.fullmatch(r"합\s*계|소\s*계|총\s*계|계", 이름):
                        단위들.add(u)
            for 이름, u, 값 in 줄모음:
                if re.fullmatch(r"합\s*계|소\s*계|총\s*계|계", 이름) and len(단위들) != 1:
                    continue
                키 = (표준(이름), 표준(u))
                if 키 not in 묶:
                    묶[키] = {"품목": 이름, "단위": u, "값": {}, "산출기준": _산출기준(u, 주석), "주석글": 주석[:240],
                             "출처": "%s 「%s」 표" % (보.글(), (표["앞글"][-1] if 표["앞글"] else "생산능력")[:40])}
                    차례.append(키)
                for c, v in 값.items():
                    묶[키]["값"].setdefault(c, v)
    return [묶[k] for k in 차례]


def _가동률기준(글):
    k = 표준(글)
    if re.search(r"(?i)M/?H|공수|인시|MANHOUR", k):
        return "인시"
    if re.search(r"시간", k):
        return "시간"
    if re.search(r"수량|생산량|물량|톤|대수|생산가능량|CAPA", k):
        return "물량"
    if re.search(r"금액|백만원|천원", k):
        return "금액"
    return "모름"


def _가동률XML(보):
    """XML 격자의 「가동률」 표(가동률 열 · % 칸)와 사업의 내용 문단의 「(평균)가동률 = 95.1%」 → [{"공시이름", "단위", "값": {기간: 0~1}, "출처", "기준"}].
    XML 이 없으면 None(옛 txt 길). 표 줄이 있으면 문장 줄은 더하지 않는다(소비처가 줄 하나면 그 줄을 쓴다)."""
    문 = _문(보)
    if not 문:
        return None
    낸 = []
    당 = 보.열("당", 흐름=False)
    for 표 in _사업표(문):
        주제 = _표주제(표)
        j률 = [j for j, x in enumerate(표["열이름"]) if re.search(r"가\s*동\s*률", x)]
        # FX4-F D5 — 머리 글이 단위 줄과 한 줄(「(3) 가동률 (단위 : MH, %)」)이면 주제 읽기가 단위 줄로 걸러 앞 절 제목(「원재료 및 생산설비」)을 주제로
        # 잡는다 — 가동률 열이 있고 앞글 · 열 머리가 가동률 · 가동가능 · 실제가동을 말하면 가동률 표로 읽는다(인시 MH 표)
        가동머리 = bool(j률) and (bool(re.search(r"가\s*동\s*률", " ".join(표["앞글"][-2:]))) or
                             any(re.search(r"가동\s*가능|실제\s*가동|계획\s*(표준)?\s*생산|M\s*/?\s*H", x) for x in 표["열이름"]))
        if 주제 != "가동률" and not (주제 in ("능력", "실적") and j률) and not 가동머리:
            continue
        기준 = _가동률기준(" ".join(표["열이름"]) + " " + (표["단위"] or "") + " " + " ".join(표["앞글"][-2:]) + " " + " ".join(표["뒷글"][:1]))
        줄 = []
        for i in range(표["머리줄수"], 표["줄수"]):
            r = 표["격자"][i]
            열들 = j률 or [j for j, c in enumerate(r) if "%" in (c or "")]
            if not 열들:
                continue
            이름 = " ".join(dict.fromkeys(c for c in r[:min(열들)] if c and 공시표.수(c) is None))
            if not 이름:
                continue
            for j in 열들:
                c = r[j] if j < len(r) else ""
                v = 공시표.칸수(표, i, j)
                if v is None:
                    continue
                v = v / 100.0 if ("%" in c or v > 1.5) else v
                if not 0 <= v <= 3:
                    continue
                기간 = (_기간이름(표["열이름"][j], 보) if len(열들) > 1 else None) or 당
                줄.append({"공시이름": 이름, "단위": "%", "값": {기간: round(v, 6)},
                          "출처": "%s 「%s」 표" % (보.글(), (표["앞글"][-1] if 표["앞글"] else "가동률")[:30]), "기준": 기준})
        if len([x for x in 줄 if not re.fullmatch(r"합\s*계|평\s*균|계", x["공시이름"])]) >= 1:
            줄 = [x for x in 줄 if not re.fullmatch(r"합\s*계|계", x["공시이름"])] or 줄
        낸 += 줄
    if not 낸:
        for 경로, 글 in 문.get("글") or []:
            if not any(re.search(r"사업의\s*내용", x) for x in 경로):
                continue
            for m in re.finditer(r"(평균\s*)?가\s*동\s*률\s*(?:은|는|이|가|=|:|：)?\s*(?:약\s*)?([0-9]+(?:\.[0-9]+)?)\s*%", 글):
                x = float(m.group(2))
                if 0 <= x <= 300:
                    낸.append({"공시이름": "문장 — " + re.sub(r"\s*(?:은|는|이|가|=|:|：)?\s*(?:약\s*)?[0-9.]+\s*%$", "", 글[max(0, m.start() - 20): m.end()].strip()).strip(" ①②③④⑤-·"),
                              "단위": "%", "값": {당: round(x / 100.0, 6)},
                              "출처": "%s 사업의 내용 문장" % 보.글(), "기준": _가동률기준(글[max(0, m.start() - 200): m.end() + 200])})
                    break
            if 낸:
                break
    return 낸


def 수주잔고표모으기(보들, 해=None):
    """FX-A R3 — 사업의 내용 「수주상황」 표(XML 격자 — 「수주잔고」 가 열 머리에 있어 줄 이름 정규식이 못 잡던 꼴) →
    ({"줄": [{"품목", "수주총액", "기납품", "잔고", "단위", "기준일", "출처", "합계"}], "잔고합계": 원 · None, "기준일", "보고서"}, 문장 목록).
    가장 늦은 보고서(기준일 반기)에서 그런 표가 있는 첫 보고서를 쓴다. 무형자산 「수주잔고」(영업권 표의 열)는 거른다(줄에 기초 · 기말)."""
    문장 = []
    for 보 in _읽을보고서(보들):
        문 = _문(보)
        if not 문:
            continue
        if not 문장:
            for 경로, 글 in 문.get("글") or []:
                if any(re.search(r"사업의\s*내용", x) for x in 경로) and re.search(r"(수주\s*잔고|계약\s*잔액|수주\s*잔량)[^.。]{0,60}?\d", 글):
                    m = re.search(r"(수주\s*잔고|계약\s*잔액|수주\s*잔량)", 글)
                    문장.append({"글": 글[max(0, m.start() - 40): m.start() + 160], "출처": "%s 사업의 내용 문장" % 보.글()})
                    if len(문장) >= 3:
                        break
        for 표 in _사업표(문):
            맥 = 공시표.맥락(표, 3)
            if not re.search(r"수주|계약\s*잔액", 맥 + " ".join(표["열이름"])):
                continue
            j잔들 = 공시표.열들찾기(표, r"수주잔고|수주잔량|계약잔액|잔고|잔액|잔량")
            if not j잔들 and _표주제(표) == "수주":
                j잔들 = 공시표.열들찾기(표, r"^기말|^당기말|^당반기말")          # 「기초 · 증감 · 매출계상액 · 기말」 꼴 수주상황 표
            if not j잔들 or 공시표.열찾기(표, r"영업권|무형") is not None:
                continue
            이름들 = [n for n, _, _ in 공시표.줄들(표)]
            if any(re.fullmatch(r"기초|기말|취득|상각", 표준(n)) for n in 이름들):
                continue

            def 금액열(js):
                js = list(js)
                return next((j for j in reversed(js) if "금액" in 표준(표["열이름"][j])), js[-1] if js else None)
            j잔 = 금액열(j잔들)
            j총 = 금액열(공시표.열들찾기(표, r"수주총액|기본도급|계약금액|수주금액|총수주|수주액|계약총액"))
            j납 = 금액열(공시표.열들찾기(표, r"기납품|완성공사|기성|매출인식|매출계상|납품액|누적매출"))
            첫수 = min(j for j in (j잔, j총, j납) if j is not None)
            목 = 공시표.단위목록(" ".join(표["앞글"][-4:]) + " " + " ".join(표["열이름"]))
            원화 = next((x for x in 목 if 공시표.단위배수(x)), None)
            금액머리 = "금액" in 표준(표["열이름"][j잔]) or not re.search(r"수량", 표준(표["열이름"][j잔]))
            u = (원화 if (금액머리 and 원화) else (표["단위"] or (목[0] if 목 else ""))) or ""
            m = re.search(r"기준\s*일?\s*[:：]\s*(\d{4})\s*년?\s*[.\-]?\s*(\d{1,2})\s*월?\s*[.\-]?\s*(\d{1,2})", " ".join(표["앞글"][-2:]))
            기준일 = ("%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3)))) if m else (보.끝.isoformat() if 보.끝 else "")
            줄 = []
            for i in range(표["머리줄수"], 표["줄수"]):
                r = 표["격자"][i]
                이름 = " ".join(dict.fromkeys(c for c in r[:첫수] if c and 공시표.수(c) is None and not re.search(r"\d{4}\s*[.년]", c))) or                     (r[0] if r and r[0] and 공시표.수(r[0]) is None else "")          # 줄 이름이 기간뿐인 표(「제25기(2026년 2분기) | 수주잔액」)
                잔 = 공시표.칸수(표, i, j잔, 복사포함=False)
                if not 이름 or 잔 is None:
                    continue
                합 = bool(re.search(r"합\s*계|총\s*계|^계$|합$", 표준(이름)))
                줄.append({"품목": 이름, "수주총액": 공시표.칸수(표, i, j총) if j총 is not None else None,
                          "기납품": abs(공시표.칸수(표, i, j납)) if (j납 is not None and 공시표.칸수(표, i, j납) is not None) else None,
                          "잔고": 잔, "단위": u, "기준일": 기준일, "합계": 합,
                          "출처": "%s 「%s」 표" % (보.글(), (표["앞글"][-1] if 표["앞글"] else "수주상황")[:30])})
            if not 줄:
                continue
            합줄 = [x for x in 줄 if x["합계"]]
            잔합 = 합줄[-1]["잔고"] if 합줄 else sum(x["잔고"] for x in 줄)
            배 = 공시표.단위배수(u)
            return ({"줄": 줄, "잔고합계": (잔합 * 배) if 배 else None, "잔고합계_공시단위": 잔합, "단위": u, "기준일": 기준일,
                     "보고서": 보.글(), "기간": 보.열("당", 흐름=False)}, 문장)
    return None, 문장


_투자이름머리 = r"회사|법인|사업\s*부문|부문|구\s*분|투자\s*명|계획\s*명칭|프로젝트|사업장|투자\s*내용|내\s*용"


def _투자칸(c):
    """「1,000(500)」 · 「1,000 (기지출 500)」 → (총액, 기지출) · 수 하나면 (값, None)."""
    s = (c or "").replace(" ", "")
    m = re.fullmatch(r"\(?([0-9][0-9,]*(?:\.[0-9]+)?)\)?\((?:기지출|기투자|집행)?:?([0-9][0-9,]*(?:\.[0-9]+)?)\)", s)
    if m:
        return float(m.group(1).replace(",", "")), float(m.group(2).replace(",", ""))
    return 공시표.수(c), None


def 투자계획XML(보들, 모):
    """FX-A R2 — 「투자계획 · 투자현황 · 진행 중인 투자 · 설비의 신설 · 매입 계획」 표(XML 격자) → {"표": [줄], "진행중": [줄]} 또는 None(XML 없음).
    가장 늦은 보고서(기준일 반기)에서 그런 표가 있는 첫 보고서를 읽는다(그 보고서의 표는 모두 — 한 절 안 표 둘은 `표번호` 로 가른다).
    줄 = {"구분", "대상", "효과", "기간", "총투자", "기투자", "향후투자", "연도별": {해: 값}, "단위", "출처", "종류": 진행중 | 계획, "표번호",
          "총액기지출": bool, "검산": 글 · None, "주": [각주]} — 금액은 목표 단위. 합계 줄은 줄로 내지 않고 `합계` 로 둔다."""
    XML있음 = False
    for 보 in _읽을보고서(보들):
        문 = _문(보)
        if not 문:
            continue
        XML있음 = True
        표들 = [t for t in _사업표(문) if _표주제(t) == "투자" and any(re.search(r"투자|금액|지출|계획|예산", 표준(x)) for x in t["열이름"])]
        if not 표들:
            continue
        낸, 진행 = [], []
        for k, 표 in enumerate(표들):
            맥 = " ".join([x for x in 표["앞글"] if not (공시표.단위읽기(x) and len(x) <= 60)][-2:])
            종류 = "진행중" if re.search(r"진행\s*중", 맥) else "계획"
            머리글 = next((x for x in reversed(표["앞글"]) if re.search(dict(_주제re)["투자"], x) and len(x) <= 80), None) or 맥
            u = 표["단위"] or ""
            배 = 공시표.단위배수(u)
            if 배 is None:
                배 = {"십억원": 1e9, "조원": 1e12}.get(표준(u), None)
            열 = 표["열이름"]
            j이름 = [j for j, x in enumerate(열) if re.search(_투자이름머리, 표준(x)) and not re.search(r"금액|투자액|기간", 표준(x))]
            j대상 = 공시표.열찾기(표, r"대상|자산형태|투자자산")
            j효과 = 공시표.열찾기(표, r"효과|목적")
            j기간 = 공시표.열찾기(표, r"기간|일정|시기")
            j총 = 공시표.열찾기(표, r"총투자|총액|투자총액|총예상|총계획|계획금액|예산")
            j기 = 공시표.열찾기(표, r"기투자|기지출|기집행|누적투자|당기투자|집행액|투자실적")
            j향 = 공시표.열찾기(표, r"향후|잔여|예상투자|미투자|투자예정")
            j해 = {j: int(m.group(1)) for j, x in enumerate(열) for m in [re.search(r"(20\d\d)\s*년|'(\d\d)\s*년", x)] if m and m.group(1)}
            for j, x in enumerate(열):
                m = re.search(r"'(\d\d)\s*년", x)
                if m and j not in j해:
                    j해[j] = 2000 + int(m.group(1))
            if j향 is not None and j향 in j해 and len(j해) == 1:
                j해 = {}                              # 「예상투자액(2026년 7월~12월)」 — 연도 열이 아니라 향후 투자 열이다
            총기 = bool(j총 is not None and re.search(r"기지출|기투자", 표준(열[j총])))
            if 총기 and j기 == j총:
                j기 = None                            # 「총액(기지출)」 한 열 — 기지출은 칸 안 괄호에서 읽는다
            주 = [x[:200] for x in 표["뒷글"][:3] if re.search(r"^\s*(\(?주\d*\)?|※|\*)|미반영|제외|포함|기준", x)][:2]
            합계 = None
            for i in range(표["머리줄수"], 표["줄수"]):
                r = 표["격자"][i]
                이름 = " ".join(dict.fromkeys(r[j] for j in (j이름 or [0]) if j < len(r) and r[j] and 공시표.수(r[j]) is None))
                if not 이름:
                    continue

                def 금(j):
                    if j is None or j >= len(r) or 표["병합"][i][j]:
                        return None, None
                    a, b = _투자칸(r[j])
                    f = 배 / 단위배[모.단위] if 배 else None
                    return (a * f if (a is not None and f) else None), (b * f if (b is not None and f) else None)
                총, 총기지출 = 금(j총)
                기, _ = 금(j기)
                향, _ = 금(j향)
                if 총기지출 is not None and 기 is None:
                    기 = 총기지출
                연도별 = {}
                for j, y in j해.items():
                    v, _b = 금(j)
                    if v is not None:
                        연도별[y] = v
                if all(v is None for v in (총, 기, 향)) and not 연도별:
                    continue
                if re.search(r"^(합\s*계|총\s*계|계|소\s*계)$", 이름.strip()):
                    합계 = {"총투자": 총, "기투자": 기, "향후투자": 향, "연도별": 연도별 or None}
                    continue
                y = {"구분": 이름, "단위": u, "출처": "%s 「%s」 표" % (보.글(), (머리글 or "투자")[:40]), "종류": 종류, "표번호": k}
                for 키, j in (("대상", j대상), ("효과", j효과), ("기간", j기간)):
                    if j is not None and j < len(r) and r[j]:
                        y[키] = r[j]
                for 키, v in (("총투자", 총), ("기투자", 기), ("향후투자", 향)):
                    if v is not None:
                        y[키] = v
                if 연도별:
                    y["연도별"] = 연도별
                if 총기지출 is not None:
                    y["총액기지출"] = True
                if 총 is not None and 기 is not None and 기 > 총 * 1.001 + 1e-9:
                    y["검산"] = "기투자 %s > 총투자 %s — 표 읽기 · 공시 확인" % ("{:,.0f}".format(기), "{:,.0f}".format(총))
                if 주:
                    y["주"] = 주
                (진행 if 종류 == "진행중" else 낸).append(y)
                if 종류 == "진행중":
                    낸.append(dict(y))                # 옛 소비처(투자능력 CP1)는 `표` 만 읽는다 — 진행 중 줄도 표에 둔다(종류로 가른다)
            if 합계 and (낸 or 진행):
                (진행 if 종류 == "진행중" else 낸)[-1].setdefault("_표합계", 합계)
        if 낸 or 진행:
            return {"표": 낸, "진행중": 진행}
    return {"표": [], "진행중": []} if XML있음 else None


_약정표re = r"약정|우발\s*부채|약정\s*사항|계약\s*(사항|현황)|매입\s*약정|건설\s*계약|담보|지급\s*보증"
_약정성격 = (("설비취득", r"(유형자산|설비|시설|공장|토지|건물|기계|건설중|공사|장비).{0,30}(취득|매입|구입|약정|계약|공사)|(취득|매입)\s*약정|자본적\s*지출|건설\s*계약"),
            ("재고공급", r"원\s*재료|원자재|재고|구매\s*약정|공급\s*계약|장기\s*공급|구매\s*계약"),
            ("사용권", r"리스|임차|사용권"),
            ("지분", r"출자|지분|투자\s*약정|펀드|약정\s*출자|주식"),
            ("보증", r"보증|담보|이행\s*보증|지급\s*보증|견질|보험"),
            ("금융", r"한도|차입|여신|대출|사채|당좌|무역\s*금융|신용\s*공여|파생|통화"),
            ("보조금조건", r"보조금|지원금|리쇼어링|투자\s*유치"),
            ("비용", r"용역|서비스|라이선스|클라우드|전력|에너지"))


def 약정줄모으기(보들, 단위):
    """FX-A R2 — 연결 주석 「약정 · 우발부채 · 담보 · 보증」 표의 금액 칸(XML 격자) → [{"이름", "금액", "통화", "단위글", "상대", "특수관계", "성격후보",
    "기준일", "거슬러찾음", "출처"}] — 가장 늦은 보고서(기준일)에서, 없으면 직전 사업보고서로 내려간다(`거슬러찾음`).
    칸마다 읽는다 — XBRL 꼴(열 = 상대 · 약정 유형, 줄 = 「약정 금액, USD [USD, 백만]」)과 옛 꼴(줄 = 항목, 열 = 금액) 모두. 이름 = 표 이름 · 열 · 줄.
    원화 칸은 목표 단위로, 외화 칸은 공시 수 그대로 두고 `통화` · `단위글` 에 적는다(환산 안 함). 소송 · 파생 · 위험관리 표는 거른다.
    성격 후보는 이름 낱말로만 단다(설비취득 · 재고공급 · 사용권 · 지분 · 보증 · 금융 · 보조금조건 · 비용 · 미분류 — 확정은 F)."""
    for k, 보 in enumerate(_읽을보고서(보들)):
        문 = _문(보)
        if not 문:
            continue
        낸 = []
        for 표 in _주석표(문, True):
            주 = 표.get("주석") or ""
            제 = " ".join(x for x in 표["앞글"][-2:] if not (공시표.단위읽기(x) and len(x) <= 40))
            if not (re.search(r"약정|우발", 주) or re.search(r"약정|지급\s*보증|우발", 제)):
                continue
            if re.search(r"사용이?\s*제한|담보로\s*제공된\s*(예금|금융)|차입금|사채", 주) and not re.search(r"약정", 제):
                continue
            if re.search(r"소송|파생|위험\s*관리|공정\s*가치|환\s*율|이자율|민감도", 제 + " " + " ".join(표["열이름"][:3])):
                continue
            # FX2-A R8(2026-10-25) — 주식기준보상 약정(부여 수량 · 공정가치 · 변동성 표)은 금액 약정이 아니다(「약정」 낱말이 같아 걸렸다 — 수량 47만 주가
            # 금액 칸으로 들어가 「지분」 약정이 됐다)
            if re.search(r"주식\s*기준\s*보상|주식\s*선택권|양도\s*제한\s*조건부|스톡\s*옵션|성과\s*조건부\s*주식", 주 + " " + 제 + " " + " ".join(표["열이름"][:3])):
                continue
            u = 표["단위"] or ""
            if re.search(r"^\s*주\s*$|단위\s*[:：]\s*주\b", u):
                continue                                      # 표 단위가 「주」(수량) — 금액 약정 표가 아니다
            배 = 공시표.단위배수(u)
            for i in range(표["머리줄수"], 표["줄수"]):
                r = 표["격자"][i]
                줄이름 = r[0] if r else ""
                if re.search(r"환율|이자율|비율|기간|만기|담보설정|기술|내용|성격|종류$|제공받는\s*자|채무자|금융기관$", 줄이름):
                    continue
                # FX2-A R8 — 수량 · 주당 값 · 백분율 줄(「단위 : 주」 · 「(단위 : 원)」 주당 공정가치 · 변동성 · 배당률)은 금액 약정이 아니다
                if re.search(r"단위\s*[:：]\s*주\)|수량|주당|백분율|변동성|배당\s*(금|률)|행사\s*가격|부여일", 줄이름):
                    continue
                m = re.search(r"\b(USD|EUR|JPY|CNY|GBP|HKD|SGD|AUD|CAD|CHF|TWD|INR|VND|PLN|HUF|MXN|BRL|KRW)\b", 줄이름)
                통 = m.group(1) if m else ""
                sc = re.search(r"\[\s*[A-Z]{3}\s*,\s*(백만|천|억|원)\s*\]", 줄이름)
                for j in range(1, len(r)):
                    v = 공시표.칸수(표, i, j)
                    if v is None or v == 0:
                        continue
                    열 = 표["열이름"][j] if j < len(표["열이름"]) else ""
                    열짧 = re.sub(r"^.*?(거래상대방|약정의\s*유형|지급보증의\s*구분|구분)\s*", "", 열).strip() or 열
                    이름 = " — ".join(x for x in (제[:40], 열짧[:60], 줄이름[:40]) if x)
                    통j = 통 or next((t for t in ("USD", "EUR", "JPY", "CNY", "GBP") if t in 열), "")
                    원화 = (not 통j or 통j == "KRW") and 배
                    성 = next((n for n, p in _약정성격 if re.search(p, 열짧 + " " + 줄이름)), None) or \
                        next((n for n, p in _약정성격 if re.search(p, 제)), "미분류")
                    상 = ""
                    m2 = re.search(r"거래상대방\s*(.+?)\s*약정의", 열)
                    if m2:
                        상 = m2.group(1)
                    낸.append({"이름": 이름[:140], "금액": (v * 배 / 단위배[단위]) if 원화 else v,
                              "통화": 통j or ("KRW" if 배 else u), "단위글": ("%s %s" % (통j, sc.group(1))) if (sc and 통j) else (단위 if 원화 else u),
                              "상대": 상[:60], "특수관계": bool(re.search(r"특수\s*관계", 이름 + 주)), "성격후보": 성,
                              "기준일": 보.끝.isoformat() if 보.끝 else "", "거슬러찾음": k > 0,
                              "출처": "%s 연결 주석 「%s」 표" % (보.글(), (주 or 제)[:40])})
                    if len(낸) >= 80:
                        break
        if 낸:
            return 낸
    return []


def _변동표들(보, 단위, 전기도=False):
    """한 보고서의 연결 주석 「유형자산」 변동 표(XML 격자) → [(표지 「당」 · 「전기」, d)] — d 꼴은 `유형변동표XML` 과 같다.
    전기도 = False 면 당기 표만(첫 것). 무형 · 사용권 · 투자부동산 변동 표는 거른다(F42)."""
    낸 = []
    문 = _문(보)
    if not 문:
        return 낸
    for 표 in _주석표(문, True):
        맥 = " ".join(표["제목경로"][-1:] + ([표["주석"]] if 표.get("주석") else []) + [x for x in 표["앞글"][-3:]])
        제 = " ".join(표["앞글"][-2:]) + " " + (표.get("주석") or "")
        if not re.search(r"유형\s*자산", 맥) or re.search(r"무형|투자\s*부동산|영업권|리스\s*(자산|부채)|재평가|차입\s*원가", 제) or                 (re.search(r"사용권", 제) and not re.search(r"포함", 제)):
            continue
        앞2 = " ".join(표["앞글"][-2:])
        전 = bool(re.search(r"전\s*(기|반기|분기)", 앞2)) and not re.search(r"당\s*(기|반기|분기)", 앞2)
        if 전 and not 전기도:
            continue
        # 이름 열 수 = 수 칸이 처음 나오는 열(XBRL 꼴은 줄 이름이 두 열 — 「유형자산의 변동 | 취득」)
        첫수 = min((next((j for j, c in enumerate(r) if j > 0 and 공시표.수(c) is not None and re.search(r"\d", c or "")), 99)
                   for r in 표["격자"][표["머리줄수"]:]), default=99)
        첫수 = 1 if 첫수 >= 99 else 첫수
        줄들 = [(next((c for c in reversed(r[:첫수]) if c), ""), i) for i, r in enumerate(표["격자"]) if i >= 표["머리줄수"]]
        줄이름 = [표준(n) for n, _ in 줄들]
        열 = 표["열이름"][첫수:]
        배 = 공시표.단위배수(표["단위"]) or 1.0
        f = 배 / 단위배[단위]
        # 가로 · 세로가 바뀐 꼴(FX4-F D1 — 줄 = 자산 종류 · 열 = 움직임 「기초 | 취득 | … | 감가상각 | 기말」)은 돌려 세운다
        전치 = (sum(1 for x in 열 if re.search(r"기초|기말|감가\s*상각|취득", 표준(x))) >= 3 and
              not any(re.search(r"기초|기말", x) for x in 줄이름) and sum(1 for x in 줄이름 if _자산종류re.search(x)) >= 2)
        줄 = {}
        if 전치:
            자산들 = [(n, i) for n, i in 줄들 if n]
            for j, 움 in enumerate(열):
                if 움 and 움 not in 줄:
                    줄[움] = [(lambda x: x * f if x is not None else None)(공시표.칸수(표, i, 첫수 + j)) for _n, i in 자산들]
            열 = [n for n, _i in 자산들]
        자산열 = sum(1 for x in 열 if _자산종류re.search(표준(x)))
        한열 = len(열) == 1 and re.search(r"공시금액|금액|합계|장부금액", 표준(열[0]) if 열 else "")
        if not ((전치 or any(re.search(r"기초|기말", x) for x in 줄이름)) and (자산열 >= 2 or 한열)):
            continue
        if not 전치:
            for n, i in 줄들:
                if n and n not in 줄:
                    줄[n] = [(lambda x: x * f if x is not None else None)(공시표.칸수(표, i, j)) for j in range(첫수, 표["열수"])]
        합j = 0 if 한열 else next((j for j, x in enumerate(열) if _유형열(_변동열짧게(x)) == "합계"), None)
        검 = None
        끝 = next((v for k, v in 줄.items() if re.search(r"기말", 표준(k))), None)
        if 끝 and 합j is not None and not 한열 and 끝[합j] and 자산열 >= 3:
            s_ = sum(x for j, x in enumerate(끝) if j != 합j and x is not None)
            검 = round((s_ - 끝[합j]) / abs(끝[합j]), 6)
        짧 = ["합계"] if 한열 else [_변동열짧게(x) for x in 열]
        표지 = "전기" if 전 else "당"
        d = {"열": 열, "종류": 짧, "줄": 줄, "검산차": 검,
             "모르는열": [x for x, y in zip(열, 짧) if x and not _자산종류re.search(표준(y)) and _유형열(y) != "합계"],
             "기간": 보.열(표지), "단위": 단위, "출처": "%s 연결 주석 「%s」 표" % (보.글(), (표["앞글"][-1] if 표["앞글"] else "유형자산")[:40])}
        낸.append((표지, d, 자산열))
        if not 전기도 or (any(t == "당" for t, *_ in 낸) and any(t == "전기" for t, *_ in 낸)):
            break
    return 낸


def 유형변동표XML(보들, 단위):
    """FX-A R2 — 연결 주석 「유형자산」 변동 표(당기 · XML 격자) → {"열": [머리 이름 그대로], "종류": [짧은 자산 종류], "줄": {줄 이름: [값]}, "검산차",
    "모르는열", "기간", "단위", "출처", "자산군표": {같은 꼴 — 자산 종류별 표} | 없음}.
    낯선 자산군 열도 이름 그대로 살린다(「포토부스」 — 고정 이름 목록으로 고르다 열이 한 칸 밀린 F60). 무형 · 사용권 · 투자부동산 변동 표는 거른다(F42).
    줄 = 움직임(기초 · 취득 · 대체 · 상각 · 처분 · 사업결합 · 기말), 열 = 자산 종류. 기준일 보고서(반기)가 합계 한 열만 주면(「공시금액」) 그것을 쓰고,
    자산 종류별 표는 가장 늦은 사업보고서에서 `자산군표` 로 곁에 둔다. 금액은 목표 단위. 검산차 = (자산 종류 열 합 − 합계 열) ÷ 합계(기말 줄)."""
    첫, 군 = None, None
    for 보 in _읽을보고서(보들):
        for _표지, d, 자산열 in _변동표들(보, 단위):
            if 첫 is None:
                첫 = d
            if 자산열 >= 2 and 군 is None:
                군 = d
        if 첫 is not None and 군 is not None:
            break
    if 첫 is None:
        return None
    if 군 is not None and 군 is not 첫:
        첫["자산군표"] = 군
    return 첫


def 변동표상각(d):
    """변동 표 하나(`_변동표들` 꼴) → 유형 몫 감가상각(양수) — 합계 열(사용권 열이 따로 있으면 뺌) · 합계 열이 없으면 자산 열 합(토지 · 건설중 · 사용권 뺌).
    감가상각 줄이 없으면 None."""
    줄 = next((v for k, v in (d.get("줄") or {}).items() if re.search(r"감가\s*상각", 표준(k)) and not re.search(r"누계|손상", 표준(k))), None)
    if not 줄:
        return None
    종류 = d.get("종류") or []
    합들 = [j for j, x in enumerate(종류) if _유형열(x) == "합계" and j < len(줄) and 줄[j] is not None]
    사용권 = sum(abs(줄[j]) for j, x in enumerate(종류) if j < len(줄) and 줄[j] is not None and re.search(r"사용권", "%s" % x))
    값 = [abs(줄[j]) for j, x in enumerate(종류) if j < len(줄) and 줄[j] is not None and _유형열(x) not in ("토지", "건설중", "합계")
         and not re.search(r"사용권", "%s" % x)]
    자합 = sum(값) if 값 else None
    if len(합들) == 1:
        return abs(줄[합들[0]]) - 사용권
    if len(합들) > 1:
        # 다단 XBRL 머리(자산마다 총장부금액 · 상각누계액 · 보조금 · 「합계」 소계) — 「합계」 가 자산마다 있어 하나를 고르면 그 자산 몫만 된다(주성 꼴 —
        # 건물 소계 11,435 를 전체로 읽었다). 자산 열(누계액 열에 감가상각이 선다)의 합을 쓴다
        return 자합 if 자합 else max(abs(줄[j]) for j in 합들)
    return 자합


def 변동표상각들(보들, 단위):
    """FX4-F D1 — 보고서마다 연결 주석 유형자산 변동 표의 감가상각(유형 몫 · 합계 열) → {기간: (값, 출처)}. 당기 표가 먼저, 사업보고서의 전기 표는
    그 해 사업보고서가 없을 때만 채운다. 자산 종류별 표의 합(`_유형상각합`)보다 앞선다 — 종류 이름이 표마다 달라 합이 빠지거나 겹쳤다(조선사 FY2025
    85,822 ↔ 합계 열 반기만 99,407)."""
    낸, 전 = {}, {}
    for 보 in _읽을보고서(보들):
        for 표지, d, _자산열 in _변동표들(보, 단위, 전기도=(보.종류 == "사업")):
            v = 변동표상각(d)
            c = d.get("기간")
            if v is None or not c or v <= 0:
                continue
            (낸 if 표지 == "당" else 전).setdefault(c, (round(v, 6), d.get("출처")))
    for c, t in 전.items():
        낸.setdefault(c, t)
    return 낸


def _변동열짧게(x):
    """XBRL 차원 머리(「운용리스상태별 유형자산 운용리스 대상이 아닌 유형자산 유형자산의 분류 건물 및 구축물」) → 자산 종류 짧은 이름(「건물 및 구축물」).
    운용리스 대상인 몫은 「(운용리스 자산)」 을 붙여 가른다. 차원 꼴이 아니면 그대로."""
    t = (x or "").strip()
    짧 = re.split(r"분류\s+", t)[-1].strip() if "분류" in t else t
    if re.search(r"합계$", t) and not re.search(r"분류", t):
        짧 = "합계"
    if re.search(r"운용리스\s*대상인", t):
        짧 += "(운용리스 자산)"
    return 짧


def 비현금설비(보들, 단위):
    """FX-A R2 — 연결 주석 「현금의 유입과 유출이 없는 거래」(비현금 거래) 표에서 유형자산 미지급금 증감 · 비현금 취득(사채 · 주식 · 현물로 낸 유형자산)
    → {기간: {"미지급설비증감": 값, "비현금취득": 값, "출처"}} — 보고서마다 당기 열(목표 단위). CAPEX 발생 기준의 재료다(F35 · F36 · F40)."""
    낸 = {}
    for 보 in _읽을보고서(보들):
        문 = _문(보)
        if not 문:
            continue
        for 표 in _주석표(문, True):
            맥 = 공시표.맥락(표, 3) + " " + " ".join(표["제목경로"][-1:])
            if not re.search(r"현금의?\s*유입과?\s*유출이?\s*없는|비현금\s*(거래|항목|투자)|중요한\s*비현금|현금흐름표", 맥):
                continue
            배 = 공시표.단위배수(표["단위"]) or 1.0
            c = 보.열("당")
            for 이름, 칸, i in 공시표.줄들(표):
                k = 표준(이름)
                v = next((x for x in (공시표.수(y) for y in 칸) if x is not None), None)
                if v is None or not c:
                    continue
                d = 낸.setdefault(c, {})
                if re.search(r"(유형자산|설비|건설중|기계|건물).{0,20}(미지급|미지급금|미지급비용)|(미지급|미지급금).{0,20}(유형자산|설비|건설중)", k):
                    d.setdefault("미지급설비증감", v * 배 / 단위배[단위])
                    d.setdefault("출처", "%s 연결 주석 「%s」" % (보.글(), 이름[:40]))
                elif re.search(r"(사채|주식|출자|현물|전환|교환).{0,30}(유형자산|토지|건물|설비)|(유형자산|토지|건물|설비).{0,30}(사채|현물|출자|주식\s*발행)", k):
                    d["비현금취득"] = d.get("비현금취득", 0.0) + abs(v) * 배 / 단위배[단위]
                    d.setdefault("출처", "%s 연결 주석 「%s」" % (보.글(), 이름[:40]))
    return 낸


def 부문상세(보들, 구분별, 단위):
    """FX-A R4 — 연결 주석 영업부문 표(XML 격자)의 부문별 매출 · 자산(당기 누적) → {부문: {"유형": 후보 글, "근거", "자산", "매출"}}(목표 단위).
    부문 이름은 열(XBRL 차원 머리 — 「… 보고부문 Home Appliance Solution 누적」)에서 읽고, 「3개월 · 누적」 이 함께 있으면 누적을 쓴다.
    비율 줄(매출액비율) · 단위 없는 표는 쓰지 않는다. 자산을 부문에 배분하지 않는 회사는 자산 None(회사 전체로 판정 — F29 · F38)."""
    def 부이름(x):
        t = re.sub(r"\s*(3개월|누적|당기|전기|당반기|전반기|당분기|전분기)$", "", (x or "").strip())
        t = re.split(r"(?:보고\s*부문|영업\s*부문|부문)\s+", t)[-1].strip()
        return t
    for 보 in _읽을보고서(보들, 다년=False):
        문 = _문(보)
        if not 문:
            continue
        for 표 in _주석표(문, True):
            맥 = 공시표.맥락(표, 3) + " " + " ".join(표["제목경로"][-1:])
            if not re.search(r"영업\s*부문|부문\s*(별|정보)", 맥) or not 표["단위"] or re.search(r"전\s*(반기|분기|기)\b", " ".join(표["앞글"][-1:])):
                continue
            배 = 공시표.단위배수(표["단위"])
            if not 배:
                continue
            f = 배 / 단위배[단위]
            줄들 = 공시표.줄들(표, 이름열수=1)
            매줄 = next(((n, i) for n, _, i in 줄들 if re.search(r"(외부|순)?\s*(매출액?|영업수익|수익)", 표준(n))
                        and not re.search(r"내부|원가|이익|부문간|비율|비중|%|손익", 표준(n))), None)
            자줄 = next(((n, i) for n, _, i in 줄들 if re.search(r"^(부문)?자산|자산총계|자산합계|^자산$", 표준(n))), None)
            if not 매줄:
                continue
            낸, 누적있음 = {}, {}
            for j in range(1, 표["열수"]):
                열 = 표["열이름"][j] if j < len(표["열이름"]) else ""
                부 = 표준(부이름(열))
                if not 부 or re.search(r"합계|조정|연결|제거|소계|계$|단위|전체", 부):
                    continue
                매 = 공시표.칸수(표, 매줄[1], j)
                if 매 is None:
                    continue
                누 = bool(re.search(r"누적$", 열.strip()))
                if 부 in 낸 and 누적있음.get(부) and not 누:
                    continue
                자 = 공시표.칸수(표, 자줄[1], j) if 자줄 else None
                낸[부] = {"유형": 구분별.get(부, ""), "근거": "%s 연결 주석 영업부문 표(%s)" % (보.글(), "누적" if 누 else "당기"),
                         "매출": round(매 * f, 6), "자산": round(자 * f, 6) if 자 is not None else None}
                누적있음[부] = 누적있음.get(부) or 누
            if 낸:
                return 낸
    return {부: {"유형": t, "근거": "영업부문 주석 낱말 후보(XML 표 없음 — 매출 · 자산 확인 불가)", "매출": None, "자산": None} for 부, t in 구분별.items()}


def _연환산매출(해, 기간=None):
    """해(API — 원 단위) 가운데 기간(없으면 가장 늦은 열)의 매출을 연환산 — (값, 열)."""
    열들 = [c for c in 해 if (해[c] or {}).get("매출")]
    if not 열들:
        return None, None
    c = 기간 if (기간 in 열들) else max(열들, key=lambda x: _열때(x))
    return 해[c]["매출"] * 12.0 / (해[c].get("_개월") or 12), c


# ────────────────────────────────────────────────────────────── 회사 유형 · 운영 지표 · 판매량 · 성과급 — 업종 중립 탐지 규칙
# 유형 이름과 판정 문턱은 아래 표가 정한다(키트 CLAUDE.md 「동인 지도 규칙」의 유형 목록). 회사 이름은 어디에도 없다 — 공시의 낱말 빈도와
# 재무 비율(유형자산 ÷ 매출 · 재고 ÷ 매출 · 상품 매입 ÷ 총비용 · 인건비 ÷ 총비용)만 본다. 겹칠 수 있다.

유형낱말 = {   # 유형 → (사업의 내용에서 셀 낱말 정규식, 최소 건수)
    # 「게임 · 콘텐츠」를 따로 둔다(2026-10-16, S1 리뷰 — 종전에는 게임 · 콘텐츠 낱말이 「소프트웨어 · 구독」에 들어가 게임 회사가
    # SaaS 후보로 진단됐다). 소비재 브랜드 · 금융 · 에너지/유틸리티도 더한다(금융은 형태 규칙으로 보내는 신호다)
    "소프트웨어 · 구독": (r"소프트웨어|라이선스|구독|SaaS|클라우드\s*서비스|솔루션", 8),
    "플랫폼 · 중개": (r"플랫폼|중개|거래액|커머스|수수료\s*수익|광고\s*(매출|수익)|이용자|사용자", 10),
    "게임 · 콘텐츠": (r"게임|퍼블리싱|콘텐츠|신작|타이틀|MMORPG|아이템\s*판매|유료\s*이용자|웹툰|음원|IP\s*(사업|확장)", 12),
    "유통 · 소매": (r"점포|매장|가맹|편의점|할인점|백화점|직영점|출점", 10),
    "소비재 브랜드": (r"브랜드|화장품|식품|음료|제과|의류|생활용품|소비자\s*(제품|브랜드)|대리점|면세", 14),
    "수주 산업": (r"수주\s*잔고|수주\s*잔량|공정률|진행률|발주처", 6),
    "바이오 · 제약": (r"임상|신약|파이프라인|품목\s*허가|기술\s*이전|바이오", 10),
    "숙박 · 운송 · 통신": (r"객실|좌석|항공기|기단|선박|노선|기지국|가입\s*회선|탑승률|운항", 10),
    "금융": (r"예금|대출\s*(채권|자산)|이자\s*수익|보험료|여신|수신|위탁\s*매매|보험\s*계약", 10),
    "에너지 · 유틸리티": (r"발전소|발전\s*(설비|용량)|송배전|전력\s*(판매|거래)|정산\s*단가|SMP|연료비\s*연동|열\s*공급|가스\s*공급|요금\s*(규제|인상)", 8),
    "제조": (r"생산\s*능력|가동률|생산\s*실적|공장|생산\s*라인|생산\s*설비", 12),
    # FX-A R4(2026-10-25 · J4) — 클라우드 · 데이터센터(전력 용량 · GPU 클러스터가 투자 동인 — 낱말 문턱 + 재무 지문 유형자산 ÷ 매출 ≥ 0.3 일 때만)
    "클라우드 · 데이터센터": (r"데이터\s*센터|IDC|GPU\s*(서버|클러스터|팜)|클라우드\s*인프라|AI\s*(인프라|데이터\s*센터)", 10),
}
# 미국 10-K Item 1(Business) — 같은 유형 이름에 영어 낱말(2026-10-16, S1 리뷰: 미국은 「판정 보류」 고정이었다). 회사 이름은 없다
미국유형낱말 = {
    "소프트웨어 · 구독": (r"\b(subscriptions?|SaaS|software|cloud services?|licen[cs]es?|recurring revenue)\b", 15),
    "플랫폼 · 중개": (r"\b(marketplaces?|take rate|gross bookings|gross merchandise|advertis\w+|two-sided|payment volume|transaction volume)\b", 15),
    "게임 · 콘텐츠": (r"\b(video games?|game titles?|players|in-game|live services|content library|streaming)\b", 12),
    "유통 · 소매": (r"\b(stores|retail locations?|merchandise|comparable sales|same-store|warehouse clubs?|franchise\w*)\b", 15),
    "소비재 브랜드": (r"\b(brands?|consumer products?|beverages?|snacks?|apparel|footwear|cosmetics|household products)\b", 15),
    "수주 산업": (r"\b(backlog|remaining performance obligations?|percentage[- ]of[- ]completion|contract awards?|book-to-bill)\b", 6),
    "바이오 · 제약": (r"\b(clinical trials?|FDA approval|drug candidates?|biologics?|Phase [123I]+)\b", 10),
    "숙박 · 운송 · 통신": (r"\b(aircraft|passengers?|available seat|hotel rooms?|RevPAR|wireless subscribers|spectrum|load factor)\b", 10),
    "금융": (r"\b(deposits|loan portfolio|net interest income|insurance premiums|underwriting|broker-dealer|assets under management)\b", 10),
    "에너지 · 유틸리티": (r"\b(electric utilit\w+|rate base|rate case|kilowatt|natural gas distribution|regulated utilit\w+)\b", 8),
    "제조": (r"\b(manufactur\w+|factor(?:y|ies)|production capacity|gigafactor\w*|fabs?|wafers?|assembly plants?|production lines?)\b", 15),
    # 자기 데이터센터(짓고 · 빌리고 · 돌리는) 문장만 — 「data center end market」 처럼 데이터센터에 **파는** 회사의 낱말은 세지 않는다.
    # FX2-A R4(2026-10-25) — 붙여 쓴 「datacenter」 · 「our global network of datacenters」 · 「datacenters that deploy …」 · 용량 임대(IaaS ·
    # on-demand compute) 문장도 센다(종전 꼴은 띄어 쓴 「our data centers」 만 받아 클라우드 회사가 0건 → 재무 지문 「설비 집약 제조」 로 갔다).
    # 문턱은 5 — 낱말이 「자기 설비 · 용량 임대」 꼴로 좁고, 유형자산 ÷ 매출 ≥ 0.3 이 함께 걸린다(유형고르기)
    "클라우드 · 데이터센터": (r"(?i)\b(our (?:\w+ ){0,3}data ?cent(?:er|re)s?|network of data ?cent(?:er|re)s?|"
                           r"data ?cent(?:er|re)s? (?:that|which) (?:deploy|host|run|power|coordinate|house)\w*|"
                           r"data ?cent(?:er|re) (?:capacity|construction|campus(?:es)?|leases?|footprint|build-?outs?|infrastructure|regions?)|"
                           r"(?:own|operate|lease|build|construct)\w* (?:\w+ ){0,3}data ?cent(?:er|re)s?|compute capacity|megawatts?|gigawatts?|GPU clusters?|"
                           r"AI infrastructure|infrastructure as a service|IaaS|cloud (?:computing|infrastructure) (?:services|platform)|"
                           r"on-demand (?:technology|computing|cloud|compute) services)\b", 5),
}
# FX-A R4 — 낱말이 다른 뜻으로 쓰인 자리는 세지 않는다(낱말 앞뒤 25자에 이 낱말이 있으면): 선박 · 항공기 · 철도를 **만드는** 회사의 「선박」 은
# 운송 낱말이 아니고(F22 · F34 · F50 · F51), 아파트 · 주택 「브랜드」 는 소비재 브랜드 낱말이 아니다(F13). 회사 이름이 아니라 낱말의 맥락이다
낱말맥락제외 = {"숙박 · 운송 · 통신": r"건조|제작|제조|생산|수주|납품|조립|설계|인도|발주|건설|공장|진수",
             "소비재 브랜드": r"아파트|주택|단지|분양|오피스텔|건축|시공|재개발|재건축|건설",
             # 데이터센터에 **파는** 회사(메모리 · 전력기기 · 소재)의 낱말 — 수요 · 시장 · 고객 · 납품 맥락은 자기 설비가 아니다
             "클라우드 · 데이터센터": r"수요|시장|고객|향\s|향의|용\s|용도|납품|공급|판매|수주|전망|성장|확대|증가|투자\s*확대|빅테크|하이퍼스케일러|업체"}
미국낱말맥락제외 = {"숙박 · 운송 · 통신": r"(?i)manufactur|build|assembl|deliver(?:ed|ies)|production|backlog|orders?",
              # 「on-demand」 의 demand 는 수요 낱말이 아니다(용량 임대 꼴 「on-demand compute」 — FX2-A R4)
              "클라우드 · 데이터센터": r"(?i)customers?|(?<!on-)demand|markets?|sell|sold|sales to|end markets?|for data cent|in data cent|hyperscalers?"}
# 서비스 낱말 — 숙박 · 운송 · 통신 유형은 이 낱말이 셋 이상일 때만 탈것 낱말까지 센다(셋 미만이면 서비스 낱말 수만). 선박 · 항공기를 만들거나
# 빌려 주는 회사는 탈것 낱말만 많다(F22 · F34 · F50 · F51)
# FX2-A R11(2026-10-25) — 일반 낱말(브랜드 · 플랫폼 · 사용자 · 솔루션 · 대리점)은 그 유형의 **핵심 낱말**이 셋 이상일 때만 센다. 완성차 · 건설 ·
# 중공업 · 전력기기의 「브랜드 · 대리점」, 전자 · 방산의 「플랫폼 · 사용자」, 건설의 「솔루션」 이 소비재 · 플랫폼 · 소프트웨어 유형으로 켜지던 잡음.
# 회사 이름이 아니라 낱말의 짝이다 — 화장품 · 식품 회사의 「브랜드」, 커머스 · 광고 회사의 「플랫폼」 은 핵심 낱말과 함께 나온다
낱말필수 = {"숙박 · 운송 · 통신": (r"객실|좌석|노선|기지국|가입\s*회선|탑승률|여객|투숙|통신\s*서비스|운항\s*(편|횟수|노선)|항공\s*운송|해상\s*운송|화물\s*운송", 3),
         "소비재 브랜드": (r"화장품|식품|음료|제과|의류|패션|뷰티|생활\s*용품|주류|담배|소비자\s*(제품|브랜드)|건강\s*기능|생활\s*가전|완구|가공\s*식품", 3),
         "플랫폼 · 중개": (r"중개|거래액|커머스|수수료\s*수익|광고\s*(매출|수익)|입점|판매자|광고주|결제\s*(금액|수수료)|테이크\s*레이트|트래픽", 3),
         "소프트웨어 · 구독": (r"소프트웨어|SaaS|구독|클라우드\s*서비스|유지\s*보수\s*(매출|수익)|사용료\s*(매출|수익)", 3)}
미국낱말필수 = {"숙박 · 운송 · 통신": (r"(?i)\b(passengers?|available seat|hotel rooms?|RevPAR|wireless subscribers|load factor|freight rates?|charter|occupancy)\b", 3),
           "소비재 브랜드": (r"(?i)\b(consumer products?|beverages?|snacks?|apparel|footwear|cosmetics|household products|foods?|tobacco|beauty|personal care|spirits)\b", 3)}
# 위탁 생산 · 합작 생산 · 지주 문장(사업의 내용 · Item 1) — 유형 신호의 재료. 강한 문장(팹리스 · 생산 시설 없음)이면 제조 유형을 위탁 생산으로 바꾼다
_외주강re = re.compile(r"팹리스|fabless|(생산|제조)\s*(시설|설비|공장)\s*(을|를)?\s*(보유|소유)\s*하?\s*(지\s*)?(않|없)|자체\s*(생산|제조)\s*(시설|설비|공장)\s*(이|가|은|는)?\s*없|"
                    r"(?i:do(?:es)? not own or operate (?:any )?(?:wafer )?(?:fabrication|manufacturing)|outsourc\w*\s+(?:all|substantially all)\s+(?:of\s+)?(?:our\s+)?(?:manufactur|fabricat|production))")
_외주re = re.compile(r"외주\s*(생산|제조|가공|조립)|위탁\s*(생산|제조|가공)|(?<![A-Za-z])(?:OEM|ODM)(?![A-Za-z])|생산\s*(을|를)?\s*(외부|협력사)\s*에?\s*(위탁|의뢰)|"
                    r"(?i:contract manufactur\w*|third[- ]party (?:foundr\w*|manufactur\w*)|outsourc\w* (?:manufactur|assembl|fabricat|production)|"
                    r"outsourcing partners?|manufactured (?:\w+ ){0,4}by (?:third[- ]part\w*|outsourcing|contract))")
# 합작 · 지분법 생산 — 약한 문장(합작 · 지분법 낱말 + 생산 낱말이 가까이)은 근거로만 적고, **강한 문장**(그 피투자회사에서 생산물을 받는다 ·
# 설비투자를 나눠 낸다)일 때만 「합작 생산」 신호다(FX2-A R2 — 「joint venture」 낱말만으로 세면 파운드리 · 위탁 고객 문장에서 켜진다)
_합작re = re.compile(r"합작\s*(법인|회사|투자)?.{0,40}(생산|공장|웨이퍼|라인)|지분법.{0,40}(생산|공장)|"
                    r"(?i:joint venture.{0,80}(?:manufactur|wafer|fab\b|production|supply))")
_합작강re = re.compile(r"(합작\s*(법인|회사)?|지분법\s*(피투자|적용)?\s*(회사|기업)?|관계\s*기업|공동\s*기업)\s*(으?로부터|에서)\s*.{0,30}(매입|구매|공급\s*받|조달)|"
                     r"(설비|시설)\s*투자\s*(비용|금액)?\s*(을|를)?\s*.{0,20}분담|투자\s*비용\s*(을|를)?\s*.{0,10}(공동\s*부담|분담)|"
                     r"(?i:(?:obtain|purchas|sourc|procur|acquir|buy)\w*\s+(?:[\w,’'-]+\s+){0,6}from\s+(?:our\s+|its\s+|the\s+|these\s+)?(?:[\w’'-]+\s+){0,2}"
                     r"(?:joint\s+ventures?|business\s+ventures?|ventures|equity[- ]method\s+investees?)|"
                     r"(?:joint\s+ventures?|ventures)\s+(?:[\w,’'-]+\s+){0,4}(?:provide|supply|sell)\w*\s+(?:\w+\s+){0,3}(?:us|the\s+company)\b|"
                     r"share\w*\s+(?:\w+\s+){0,3}(?:capital\s+(?:expenditures|investments?)|equipment\s+(?:costs?|investments?)|fixed\s+costs?)"
                     r"\s+(?:\w+\s+){0,6}(?:joint\s+ventures?|ventures|partner))")
# FX2-A R4 · R11 — 용량을 빌려 주는 매출 문장(클라우드 · 데이터센터 유형의 조건 — 자기 데이터센터가 투자 동인일 뿐인 플랫폼 · 제조사는 이 유형이 아니다)과
# 자기 공장 능력 문장(미국 — 국내의 생산능력 표 몫. 「third-party · contract」 가 낀 문장은 남의 공장이다)
_용량임대re = re.compile(r"클라우드\s*(서비스|사업|인프라)|IDC\s*(서비스|사업|매출)|코로케이션|GPU\s*(임대|클라우드|서비스)|AI\s*클라우드|"
                      r"(?i:cloud (?:services?|computing|infrastructure|platform)|infrastructure as a service|\bIaaS\b|on-demand (?:compute|computing|technology|cloud)|"
                      r"GPU (?:cloud|as a service)|AI cloud|colocation)")
_자기공장re = re.compile(r"(?i)\b(?:our|we (?:own|operate|lease|built|opened))\b[^.]{0,80}\b(?:factor(?:y|ies)|gigafactor\w*|manufacturing (?:facilit\w+|plants?|sites?|lines?)|"
                      r"production (?:facilit\w+|plants?|lines?)|fabs?|fabrication facilit\w+)\b[^.]{0,100}\b(?:capacity|produc\w+|output)\b")
_남의공장re = re.compile(r"(?i)third[- ]party|contract manufactur|outsourc|competitors?|suppliers?|subcontract")
# 합작 몫 대용치 재료 — 지분법 투자 자산 · 피투자회사 설비 몫 문장(F 가 합작 몫 CAPEX 곁 칸을 세울 때 근거로 읽는다 — J2)
_합작몫re = re.compile(r"지분법\s*(적용)?\s*투자\s*(주식|자산)|관계\s*기업\s*(및\s*공동\s*기업\s*)?투자|(합작|지분법).{0,30}(유형자산|설비|감가상각)|"
                     r"(?i:equity[- ]method investments?|investments? in (?:\w+ ){0,3}ventures?|our share of (?:\w+ ){0,4}"
                     r"(?:property|equipment|capital expenditures|depreciation|fixed costs?))")
_데이터센터re = re.compile(r"데이터\s*센터|IDC|GPU|(?i:data cent(?:er|re)s?|compute capacity|megawatts?|gigawatts?)")
_지주re = re.compile(r"(순수|사업)?\s*지주\s*회사|(?i:holding company)")
수주구조문턱 = 0.3        # 수주잔고 표의 잔고 ÷ 연환산 매출이 이 이상이면 「수주 산업」(구조 신호 — 낱말 · 상대 문턱과 무관)
미국RPO문턱 = 3.0        # 미국 RPO ÷ 연환산 매출 — 구독 회사(1~2배) · 장기 공급 계약 회사(2~3배)와 가르려고 높게 둔다
위탁비율문턱 = 0.2       # 외주 · 위탁 문장 + 유형자산 ÷ 매출이 이 아래면 「위탁 생산」(0.08 하나뿐이던 문턱이 0.12 회사를 놓쳤다 — F56)
데이터센터비율문턱 = 0.3


def 유형점수(글, 낱말표, 맥락제외=None, 필수=None):
    """낱말 표 → {유형: 건수} — 맥락 제외 낱말이 앞뒤 25자에 있는 자리는 세지 않는다. 「광학솔루션」 처럼 앞 글자에 붙은 「솔루션」 은 부문 · 상호
    이름이라 소프트웨어 낱말로 세지 않는다(F31). 필수 = {유형: (정규식, 최소)} — 그 낱말이 최소에 못 미치면 그 낱말 수만 센다."""
    낸 = {}
    if 필수 is None:
        필수 = 낱말필수 if 낱말표 is 유형낱말 else (미국낱말필수 if 낱말표 is 미국유형낱말 else {})
    for k, (p, _) in 낱말표.items():
        if k in 필수:
            제외0 = (맥락제외 or {}).get(k)
            n필 = sum(1 for m in re.finditer(필수[k][0], 글 or "")
                     if not (제외0 and re.search(제외0, 글[max(0, m.start() - 25): m.end() + 25])))
            if n필 < 필수[k][1]:
                낸[k] = n필
                continue
        제외 = (맥락제외 or {}).get(k)
        n = 0
        for m in re.finditer(p, 글 or ""):
            if k == "소프트웨어 · 구독" and m.group(0) == "솔루션" and m.start() > 0 and re.match(r"[가-힣A-Za-z]", 글[m.start() - 1]):
                continue
            if 제외 and re.search(제외, 글[max(0, m.start() - 25): m.end() + 25]):
                continue
            n += 1
        낸[k] = n
    return 낸


def 유형신호(글, 해=None, 수주=None, 가동률=None, 사업의내용찾음=True, RPO=None, 신호글=None, 생산능력표=None, 지분법투자=None, 유형자산비=None):
    """FX-A R3 · R4 — 낱말이 아닌 **구조 신호** → {"수주잔고표", "수주잔고÷매출", "외주생산문장", "외주생산강함", "합작생산문장", "데이터센터문장",
    "지주문장", "가동률있음", "사업의내용찾음", "RPO÷매출"}. F 의 능력 상한 판정(판정 순서 ① 수주 ② 가동률 ③ 숫자 ④ 문장)이 읽는다.
    FX2-A R2 · R11(2026-10-25) — 더한 키: `합작생산강함`(피투자회사에서 생산물을 받는다 · 설비투자를 나눠 낸다 문장 — 「joint venture」 낱말만으로는
    켜지지 않는다) · `합작생산강한문장` · `합작몫문장`(지분법 투자 자산 · 피투자회사 설비 몫 문장 — 합작 몫 대용치 재료) · `지분법투자÷매출`(있으면) ·
    `합작주력`(강한 문장 + 유형자산 ÷ 매출 < 위탁비율문턱 — 자기 설비가 작고 생산이 합작에서 온다) · `생산능력표있음`(자기 공장 능력 공시 — 약한 외주
    문장이 「위탁 생산」 으로 가지 않게). `신호글` = 외주 · 합작 문장을 찾을 넓은 글(미국: Item 1 ~ Item 2 — 위험 요인 · 설비 절에 외주 문장이 있다)."""
    넓은 = 신호글 if 신호글 else 글

    def 조각(r, n=3, 글=None):
        글 = 글 if 글 is not None else 넓은
        return [글[max(0, m.start() - 50): m.end() + 70].strip() for m in list(r.finditer(글 or ""))[:n]]
    잔비 = None
    if 수주 and 수주.get("잔고합계") and 해:
        매, _c = _연환산매출(해, 수주.get("기간"))
        if 매:
            잔비 = round(수주["잔고합계"] / 매, 4)
    rpo비 = None
    if RPO and 해:
        매, _c = _연환산매출(해)
        if 매:
            rpo비 = round(RPO / 매, 4)
    지비 = None
    if 지분법투자 and 해:
        매, _c = _연환산매출(해)
        if 매:
            지비 = round(지분법투자 / 매, 4)
    강한 = 조각(_합작강re)
    공장 = [m.group(0)[:160] for m in _자기공장re.finditer(넓은 or "") if not _남의공장re.search(m.group(0))][:5]
    return {"수주잔고표": bool(수주 and 수주.get("줄")), "수주잔고÷매출": 잔비, "외주생산문장": 조각(_외주re), "외주생산강함": bool(_외주강re.search(넓은 or "")),
            "용량임대문장": 조각(_용량임대re, 글=글), "자기공장문장": 공장,
            "합작생산문장": 조각(_합작re), "합작생산강함": bool(강한), "합작생산강한문장": 강한, "합작몫문장": 조각(_합작몫re),
            "지분법투자÷매출": 지비,
            "합작주력": bool(강한) and 유형자산비 is not None and 유형자산비 < 위탁비율문턱,
            "데이터센터문장": 조각(_데이터센터re, 글=글), "지주문장": 조각(_지주re, 1, 글=글),
            "가동률있음": bool(가동률), "생산능력표있음": bool(생산능력표) or len(공장) >= 2, "사업의내용찾음": bool(사업의내용찾음), "RPO÷매출": rpo비}
운영지표틀 = {   # 이름 → (줄 이름 · 문장 정규식, 단위 낱말)
    "매장수": (r"(점포|매장|가맹점|직영점|지점)\s*(의\s*)?수|점포\s*현황|매장\s*현황", r"개|점|곳"),
    "면적": (r"(매장|영업|임대|연)\s*면적", r"㎡|평|m2"),
    "사용자수": (r"이용자\s*수|사용자\s*수|활성\s*(이용자|사용자)|MAU|DAU", r"명|만명|천명"),
    "가입자수": (r"가입자\s*수|회원\s*수|유료\s*가입", r"명|만명|천명|회선"),
    "거래액": (r"거래액|GMV|취급고|결제\s*금액|거래\s*금액", r"원|억원|조원|백만원"),
    "주문건수": (r"주문\s*(건수|수)|거래\s*건수", r"건|천건|만건"),
    "수주잔고": (r"수주\s*잔고|수주\s*잔량", r"원|억원|백만원|척|톤"),
    "좌석수": (r"좌석\s*수|공급\s*좌석|병상\s*수", r"석|병상"),
    "객실수": (r"객실\s*수", r"실|객실"),
    "ARPU": (r"ARPU|가입자당\s*평균\s*(매출|수익)|이용자당\s*평균\s*(매출|수익)", r"원|달러"),
    "테이크레이트": (r"테이크\s*레이트|take\s*rate|수수료율", r"%"),
    "생산능력": (r"생산\s*능력", r"톤|대|개|장|백만원|천원|원"),
    # S5-14 — 능력 지표의 표준 이름을 넓힌다(서버 · 데이터센터 용량 · 회선 · 편대 · 파이프라인 — CLAUDE 「동인 지도 규칙」의 능력)
    "서버수": (r"서버\s*(수|대수|보유)", r"대|천대|만대"),
    "데이터센터용량": (r"(데이터\s*센터|IDC).{0,12}(용량|전력|수전)", r"MW|㎿|kW|메가와트"),
    "회선수": (r"(가입\s*)?회선\s*수|회선\s*현황", r"회선|만회선|천회선"),
    "편대": (r"(보유|운용)\s*(항공기|기단|선박|선대)|기단\s*(규모|현황)|선대\s*(규모|현황)", r"대|척|기"),
    "파이프라인": (r"파이프라인\s*(수|현황)|임상\s*(과제|파이프라인)\s*수", r"개|건|종"),
}


def 사업내용(보):
    """「II. 사업의 내용」(없으면 「III. 재무에 관한 사항」 앞까지) 줄 번호 범위."""
    # FX-A R1(2026-10-25) — 머리 줄이 다음 글과 한 줄로 붙은 원문(빈 줄 없이 「II. 사업의 내용 | 당사가 영위하는 …」)도 머리로 본다 — 줄의 첫 칸이
    # 머리 글 그대로면 된다(종전엔 칸이 하나인 줄만 받아 최신 사업보고서의 사업의 내용을 못 찾고 유형 낱말이 0 이 됐다 — F40 · F49)
    후보 = [i for i, r in enumerate(보.행) if r and re.fullmatch(r"\s*(II|Ⅱ)\.\s*사업의\s*내용\s*", r[0] or "")]
    if not 후보:
        return 0, 0
    시작 = 후보[-1]                     # 첫머리 차례(목차)에도 같은 머리가 있다 — 마지막 것이 본문이다
    끝 = next((i for i in range(시작 + 1, len(보.행)) if 보.행[i] and re.match(r"^\s*(III|Ⅲ)\.\s*재무에\s*관한", 보.행[i][0] or "")
              and len(보.행[i][0] or "") <= 30), min(len(보.행), 시작 + 4000))
    return 시작, 끝


유형상대문턱 = 0.25        # S10-15 — 문턱을 넘은 유형 가운데 최다 유형 건수의 이만큼에 못 미치는 유형은 뺀다(게임 243건에 소프트웨어 10 · 플랫폼 21 따위)
보류우세비율 = 0.5         # FX2-A R4 — 판정 보류 때 맨 앞 유형이 자기 문턱의 이만큼 이상이고
보류우세배수 = 2.0         # 둘째 유형(문턱 비율)의 이 배수 이상이면 그 유형으로 정한다(낱말이 짧은 Item 1 — 광고 플랫폼 13/15 · 소프트웨어 4/15 따위)


def 보류후보(점수, 낱말표, 재무, 신호=None):
    """FX2-A R4(2026-10-25) — 판정 보류 회사의 후보 목록(문턱 비율 큰 차례) + 재무 지문 · 본문 신호 후보.
    → [{"유형", "점수", "문턱비율", "둘째대비", "상대우세", "까닭"}]. 「제조」 · 「클라우드 · 데이터센터」 는 재무 비율이 함께 걸려야 해서 상대 우세로
    정하지 않는다(재무 지문 후보 줄로 따로 낸다). 회사 이름 없음 — 낱말 점수 · 재무 비율 · 구조 신호만."""
    신 = 신호 or {}
    r = 재무.get("유형자산÷매출")
    비 = sorted(((k, 점수.get(k, 0), 점수.get(k, 0) / float(문턱 or 1)) for k, (_p, 문턱) in 낱말표.items() if 점수.get(k, 0)),
               key=lambda x: -x[2])
    낸 = []
    # 둘째는 낱말로만 정해지는 유형끼리 견준다(제조 · 클라우드는 재무 비율이 함께 걸려 상대 우세의 맞수가 아니다)
    낱말만 = [x for x in 비 if x[0] not in ("제조", "클라우드 · 데이터센터")]
    for i, (k, n, b) in enumerate(비[:4]):
        둘 = next((x[2] for x in 낱말만 if x[0] != k), 0.0)
        둘대 = (b / 둘) if (i == 0 and 둘) else None
        우세 = (i == 0 and k not in ("제조", "클라우드 · 데이터센터") and b >= 보류우세비율 and (둘 == 0 or b >= 보류우세배수 * 둘))
        낸.append({"유형": k, "점수": n, "문턱비율": round(b, 3), "둘째대비": round(둘대, 2) if 둘대 else None, "상대우세": bool(우세),
                  "까닭": "낱말 %d건 · 문턱의 %.0f%%" % (n, b * 100)})
    if r is not None:
        if r >= 0.4:
            낸.append({"유형": "설비 집약 제조", "점수": 점수.get("제조", 0), "문턱비율": None, "둘째대비": None, "상대우세": False,
                      "까닭": "재무 지문 — 유형자산 ÷ 매출 %.2f" % r})
        if r >= 데이터센터비율문턱 and 신.get("데이터센터문장"):
            낸.append({"유형": "클라우드 · 데이터센터", "점수": 점수.get("클라우드 · 데이터센터", 0), "문턱비율": None, "둘째대비": None, "상대우세": False,
                      "까닭": "본문 데이터센터 문장 %d개 + 유형자산 ÷ 매출 %.2f" % (len(신["데이터센터문장"]), r)})
        if r < 위탁비율문턱 and 신.get("외주생산문장"):
            낸.append({"유형": "위탁 생산", "점수": None, "문턱비율": None, "둘째대비": None, "상대우세": False,
                      "까닭": "외주 · 위탁 문장 %d개 + 유형자산 ÷ 매출 %.3f" % (len(신["외주생산문장"]), r)})
    return 낸


def 유형고르기(점수, 낱말표, 재무, 근거=None, 신호=None):
    """낱말 점수 + 재무 비율 → (판정 목록, 근거 문장 목록). 국내 · 미국이 같은 규칙을 쓴다(낱말 표만 다르다).
    S10-15 — 절대 문턱(유형마다)을 넘고 **최다 유형 건수의 25% 이상**인 유형만 판정에 든다(상대 문턱 — 낮은 문턱으로 다 들어가면 그 유형의
    동인 지표가 「있어야 하는데 못 찾았다(확인 불가)」로 남는다). 뺀 유형은 근거에 적는다.
    FX-A R3 · R4(2026-10-25) — 신호(`유형신호`)가 있으면 낱말보다 구조를 먼저 본다: ① 수주잔고 표(잔고 ÷ 연환산 매출 ≥ 0.3) · 미국 RPO(≥ 3배)면
    「수주 산업」(상대 문턱에 걸려 일곱 번 빠졌다) ② 외주 · 위탁 문장 + 유형자산 ÷ 매출 < 0.2 면 「위탁 생산」(팹리스 · 생산 시설 없음 문장이면
    제조 유형을 뺀다) ③ 합작 · 지분법 생산 문장 + 유형자산 ÷ 매출 < 0.2 면 「합작 생산」 ④ 「클라우드 · 데이터센터」 낱말은 유형자산 ÷ 매출 ≥ 0.3 일 때만
    (상대 문턱과 무관) ⑤ 낱말이 문턱에 못 미쳐도 유형자산 ÷ 매출 ≥ 0.4 이고 제조 낱말이 있으면 「설비 집약 제조」 후보(판정 보류로 멈추지 않는다 — F20)."""
    판정, 근거 = [], list(근거 or [])
    신 = 신호 or {}
    r = 재무.get("유형자산÷매출")
    넘은 = [(k, 점수.get(k, 0)) for k, (p, 문턱) in 낱말표.items() if 점수.get(k, 0) >= 문턱]
    최다 = max((n for _k, n in 넘은 if _k != "클라우드 · 데이터센터"), default=0)
    for k, n in 넘은:
        if k == "클라우드 · 데이터센터":
            if r is not None and r >= 데이터센터비율문턱 and "용량임대문장" in 신 and not 신.get("용량임대문장"):
                # FX2-A R4 — 자기 데이터센터는 있으나 용량을 빌려 주는 매출 문장(클라우드 서비스 · IaaS · GPU 클라우드)이 없다 — 투자 동인일 뿐 이 유형이 아니다
                근거.append("%s %d건 · 유형자산 ÷ 매출 %.2f — 자기 데이터센터(투자 동인)이나 용량 임대 매출 문장이 없어 유형에 넣지 않았다" % (k, n, r))
            elif r is not None and r >= 데이터센터비율문턱:
                판정.append(k)
                근거.append("%s %d건 · 유형자산 ÷ 매출 %.2f(설비가 투자 동인)" % (k, n, r))
            else:
                근거.append("%s %d건은 유형자산 ÷ 매출이 %.2f 이상이 아니라 판정에서 뺐다(데이터센터를 빌려 쓰거나 낱말만 있다)" % (k, n, 데이터센터비율문턱))
            continue
        if n >= 유형상대문턱 * 최다:
            판정.append(k)
            근거.append("%s %d건" % (k, n))
        else:
            근거.append("%s %d건은 최다 유형 %d건의 %.0f%% 미만이라 판정에서 뺐다(상대 문턱 — S10-15)" % (k, n, 최다, 유형상대문턱 * 100))
    if 신.get("수주잔고표") and "수주 산업" not in 판정:
        if 신.get("수주잔고÷매출") is not None and 신["수주잔고÷매출"] >= 수주구조문턱:
            판정.append("수주 산업")
            근거.append("수주 산업 — 구조 신호: 공시 수주잔고 표 · 잔고 ÷ 연환산 매출 %.2f년(낱말 · 상대 문턱과 무관 — FX-A R3)" % 신["수주잔고÷매출"])
        else:
            근거.append("수주잔고 표가 있으나 %s — 수주 산업 판정에 넣지 않았다(잔고가 외화 · 수량 단위이거나 매출의 %.0f%% 미만)" % (
                ("잔고 ÷ 연환산 매출 %.2f" % 신["수주잔고÷매출"]) if 신.get("수주잔고÷매출") is not None else "잔고 ÷ 매출을 잴 수 없어", 수주구조문턱 * 100))
    elif 신.get("RPO÷매출") is not None and 신["RPO÷매출"] >= 미국RPO문턱 and "수주 산업" not in 판정:
        판정.append("수주 산업")
        근거.append("수주 산업 — 구조 신호: RPO(잔여 이행 의무) ÷ 연환산 매출 %.1f배(≥ %.1f)" % (신["RPO÷매출"], 미국RPO문턱))
    if "소프트웨어 · 구독" in 판정 and (재무.get("재고÷매출", 0) >= 0.05 or 재무.get("유형자산÷매출", 0) >= 0.6):
        if "클라우드 · 데이터센터" in 판정 and 재무.get("재고÷매출", 0) < 0.05:
            # FX2-A R4 — 큰 설비가 데이터센터면(클라우드 유형이 섰다) 소프트웨어 낱말은 그대로 유형 근거다(설비가 소프트웨어 매출을 돌린다)
            근거.append("소프트웨어 낱말 %d건 — 유형자산이 크지만 클라우드 · 데이터센터 유형이 그 설비를 설명해 남겼다" % 점수.get("소프트웨어 · 구독", 0))
        else:
            판정.remove("소프트웨어 · 구독")                 # 재고 · 설비가 큰 회사의 「솔루션」 낱말은 유형 근거가 아니다
            근거.append("소프트웨어 낱말 %d건은 재고 · 유형자산 비율로 뺐다" % 점수.get("소프트웨어 · 구독", 0))
    if "제조" in 판정:
        판정.remove("제조")
        판정.insert(0, "설비 집약 제조" if 재무.get("유형자산÷매출", 0) >= 0.4 else "조립 · 경공업 제조")
    if 재무.get("상품매입÷총비용", 0) >= 0.4 and "유통 · 소매" not in 판정:
        판정.append("유통 · 소매")
        근거.append("상품 매입이 총비용의 %.0f%%" % (재무["상품매입÷총비용"] * 100))
    # 2026-10-24 W10(회차 20261024) — 낱말 점수가 모두 0 이면(사업의 내용 구간을 못 찾은 것) 경보를 남기고 재무 지문으로만 후보를 낸다.
    # 「서비스(인력)」 폴백은 설비가 작은 회사(유형자산 ÷ 매출 < 0.4)에서만 — 설비가 매출의 80% 인 회사의 인건비 비중은 이익 연동 성과급으로도 오른다
    낱말없음 = not any(n for n in 점수.values())
    if 낱말없음:
        근거.append("경보 — 유형 낱말 점수가 모두 0이다(사업의 내용 구간을 못 찾았을 수 있다) · 재무 지문으로만 후보를 낸다(본선 확인)")
        if 재무.get("유형자산÷매출", 0) >= 0.4 and not 판정:
            판정.append("설비 집약 제조")
            근거.append("유형자산이 매출의 %.0f%% — 재무 지문 후보(낱말 근거 없음)" % (재무["유형자산÷매출"] * 100))
    if 재무.get("인건비÷총비용", 0) >= 0.4 and not 판정 and 재무.get("유형자산÷매출", 0) < 0.4:
        판정.append("서비스(인력)")
        근거.append("인건비가 총비용의 %.0f%%%s" % (재무["인건비÷총비용"] * 100, " — 재무 지문 후보(낱말 근거 없음)" if 낱말없음 else ""))
    제조들 = ("설비 집약 제조", "조립 · 경공업 제조")
    # FX2-A R2 — 합작 생산은 **강한 문장**(피투자회사에서 생산물을 받는다 · 설비투자를 나눠 낸다)일 때만. 약한 문장(합작 낱말 + 생산 낱말)은 근거로만
    합작강 = bool(신.get("합작생산강함"))
    if 합작강 and r is not None and r < 위탁비율문턱 and "합작 생산" not in 판정:
        뺀 = [x for x in 판정 if x in 제조들]
        판정[:] = [x for x in 판정 if x not in 제조들]
        판정.insert(0, "합작 생산")
        근거.append("합작 생산 — 피투자회사(합작 · 지분법)에서 생산물을 받는다는 문장 + 유형자산 ÷ 매출 %.3f < %.2f(능력은 합작 몫으로 본다)%s" % (
            r, 위탁비율문턱, (" — 제조 유형(%s)을 뺐다: 공장이 합작에 있다" % " · ".join(뺀)) if 뺀 else ""))
    elif 신.get("합작생산문장") and not 합작강:
        근거.append("합작 · 지분법 생산 낱말 문장 %d개 — 피투자회사에서 생산물을 받는다는 문장이 아니라 「합작 생산」 으로 보지 않았다(약한 신호)" % len(신["합작생산문장"]))
    elif 합작강 and r is not None and r >= 위탁비율문턱:
        근거.append("합작 공급 문장이 있으나 유형자산 ÷ 매출 %.2f — 자기 설비가 주력이라 합작은 곁 공급원으로 본다" % r)
    if 신.get("외주생산문장") and r is not None and r < 위탁비율문턱 and "위탁 생산" not in 판정:
        if 신.get("외주생산강함"):
            뺀 = [x for x in 판정 if x in 제조들]
            판정[:] = [x for x in 판정 if x not in 제조들]
            판정.insert(0, "위탁 생산")
            근거.append("위탁 생산 — 팹리스 · 생산 시설 없음 문장 + 유형자산 ÷ 매출 %.3f < %.2f%s" % (r, 위탁비율문턱, (" — 제조 유형(%s)을 뺐다" % " · ".join(뺀)) if 뺀 else ""))
        elif 신.get("가동률있음") or 신.get("생산능력표있음"):
            # FX2-A R11 — 자기 공장의 생산능력 · 가동률을 공시한 회사의 약한 외주 문장(부품 외주 가공 · OEM 일부)은 위탁 생산 유형이 아니다
            근거.append("외주 · 위탁 생산 문장 %d개 — 자기 공장의 생산능력 · 가동률을 공시해 「위탁 생산」 으로 보지 않았다(일부 외주)" % len(신["외주생산문장"]))
        elif "합작 생산" in 판정:
            근거.append("외주 · 위탁 생산 문장 %d개 — 생산의 주력이 합작이라 「위탁 생산」 은 곁으로 적었다(후공정 외주 등)" % len(신["외주생산문장"]))
        else:
            판정.append("위탁 생산")
            근거.append("위탁 생산 — 외주 · 위탁 생산 문장 %d개 + 유형자산 ÷ 매출 %.3f < %.2f(일부 위탁 — 부문별로 본다)" % (len(신["외주생산문장"]), r, 위탁비율문턱))
    if not 판정 and r is not None and r >= 0.4 and 점수.get("제조", 0) >= 3:
        # FX2-A R4 — 재무 지문 후보는 제조 낱말이 다른 유형 낱말보다 (문턱 비율로) 앞설 때만(유통 · 플랫폼 낱말이 앞서는 회사의 물류 · 데이터센터
        # 설비를 「설비 집약 제조」 로 부르던 오판)
        제비 = 점수.get("제조", 0) / float(낱말표.get("제조", ("", 15))[1] or 15)
        앞선 = [k for k, (p, 문턱) in 낱말표.items() if k != "제조" and 점수.get(k, 0) / float(문턱 or 1) > 제비]
        if not 앞선:
            판정.append("설비 집약 제조")
            근거.append("설비 집약 제조 — 재무 지문 후보: 유형자산 ÷ 매출 %.2f · 제조 낱말 %d건(문턱 미달 — 판정 보류로 멈추지 않는다)" % (r, 점수.get("제조", 0)))
        else:
            근거.append("재무 지문(유형자산 ÷ 매출 %.2f)은 설비 집약이나 제조 낱말 %d건이 %s 낱말보다 적어 「설비 집약 제조」 로 정하지 않았다(보류 후보)" % (
                r, 점수.get("제조", 0), " · ".join(앞선[:3])))
    if not 판정:
        후 = 보류후보(점수, 낱말표, 재무, 신)
        if 후 and 후[0].get("상대우세"):
            판정.append(후[0]["유형"])
            근거.append("%s — 낱말 문턱 미달이나 다른 유형보다 크게 앞선다(문턱 비율 %.2f · 둘째의 %.1f배 — 보류 후보 중 상대 우세)" % (
                후[0]["유형"], 후[0]["문턱비율"], 후[0].get("둘째대비") or 0))
    if 신.get("지주문장"):
        근거.append("지주 — 사업의 내용이 지주회사라고 적었다: 연결 낱말이 여러 유형으로 갈린다 · 부문별로 판정한다(구분별상세)")
    return 판정, 근거


_부문아님 = re.compile(r"합계|소계|조정|연결|제거|단위|구분|부문간|내부|자산|부채|자본|현금|채권|채무|당기|전기|비율|위험|이자|"
                     r"감가상각|법인세|금융|손익|매출|수익|비용|이익|^기타$|^[A-Z]{3}$")


def 부문이름들(보):
    """연결 주석 「영업부문」 표의 부문 줄 — [(부문 이름, 설명 글)]. 줄 꼴: 이름 + 수(영업수익 · 비율) + 설명 글.
    「영업부문 합계」 줄에서 멈춘다. 계정 · 기간 낱말(자산 · 당기 · 위험 …)이 이름이면 부문이 아니다."""
    낸 = []
    for i in [k for k in 연결머리(보, r"영업\s*부문") if _주석머리(보.행[k])]:
        for r in 보.행[i + 1: i + 200]:
            if _주석머리(r) and 낸:
                break
            l, v = 줄라벨값(r)
            if not l or not v or all(x is None for x in v):
                continue
            c = 표준(l)
            if re.search(r"합계", c) and 낸:
                break
            if _부문아님.search(c) or len(c) > 20 or len(c) < 2:
                continue
            설명 = " ".join(x for x in r if x and 수(x) is None and 표준(x) not in (c, "영업부문"))
            if c not in [n for n, _ in 낸]:
                낸.append((c, 설명))
            if len(낸) >= 8:
                break
        if 낸:
            break
    return 낸


def 유형판정(보들, 해, 모, 수주=None):
    """→ {"판정": [유형 …], "근거": "…", "점수": {유형: 건수}, "재무": {…}, "구분별": {부문: "유형 · 유형"}, "신호": {…}}.
    가장 최근 사업보고서의 사업의 내용 + API 재무 비율. 구분별은 영업부문 주석의 부문 이름 주변(±3줄) 낱말로 고른 **후보**다.
    FX-A R1 · R3 · R4(2026-10-25) — 최신 사업보고서에서 「사업의 내용」 구간을 못 찾으면 다음 보고서(반기 포함)로 내려간다(낱말 0 의 원인 진단 —
    `신호.사업의내용찾음`). 낱말은 맥락을 본다(`유형점수` — 만드는 회사의 「선박」 · 아파트 「브랜드」 · 붙은 「솔루션」 은 세지 않는다).
    구조 신호(`유형신호` — 수주잔고 표 · 외주 · 합작 · 데이터센터 · 지주 문장 · 가동률)를 판정에 넣고 `신호` 로 낸다."""
    사업 = [b for b in 보들 if b.종류 == "사업"] or 보들
    차례 = 사업 + [b for b in 보들 if b not in 사업]
    고른, 글 = (사업[0] if 사업 else None), ""
    for 보 in 차례:
        a, b = 사업내용(보)
        if b > a:
            고른, 글 = 보, " ".join(" ".join(c for c in r if c) for r in 보.행[a:b])
            break
    if 고른 is not None and 사업 and 고른 is not 사업[0]:
        모.주의.append("유형 판정 — 최신 사업보고서(%s)에서 「사업의 내용」 구간을 못 찾아 %s 의 사업의 내용으로 판정했다" % (사업[0].글(), 고른.글()))
    사업 = [고른] if 고른 is not None else 사업
    점수 = 유형점수(글, 유형낱말, 낱말맥락제외)
    # 재무 비율 — 최근 FY
    fy = sorted(c for c in 해 if c.startswith("FY") and (해[c] or {}).get("매출"))
    재무 = {}
    if fy:
        v = 해[fy[-1]]
        매 = v.get("매출") or 0.0
        if 매:
            재무 = {"유형자산÷매출": (v.get("유형자산") or 0.0) / 매, "재고÷매출": (v.get("재고") or 0.0) / 매}
    표 = 모.성격별.get(max(모.성격별)) if 모.성격별 else None
    if 표:
        총 = sum(x for _, x, _, k in 표["줄"] if k not in ("합계", "대체")) or 0.0
        if 총:
            # 「원재료 및 상품 매입액」 같은 묶음 줄은 상품 매입이 아니다(원재료가 섞였다 — 유통 · 소매 오판 F16 · F17)
            재무["상품매입÷총비용"] = sum(x for l, x, 항, _ in 표["줄"] if 항 == "상품매입" and not re.search(r"원\s*재료|원자재|재료", l or "")) / 총
            재무["인건비÷총비용"] = sum(x for _, x, _, k in 표["줄"] if k in ("인건비", "복리후생", "주식보상")) / 총
    신호 = 유형신호(글, 해, 수주, 모.가동률, 사업의내용찾음=bool(글), 생산능력표=getattr(모, "생산능력표", None),
                유형자산비=재무.get("유형자산÷매출"))
    판정, 근거 = 유형고르기(점수, 유형낱말, 재무, 신호=신호)
    보류 = None
    if not 판정:
        판정 = ["판정 보류"]
        근거.append("사업의 내용에서 유형 낱말이 문턱을 넘지 않았다 — 본선이 정한다(보류후보 참고)")
        보류 = 보류후보(점수, 유형낱말, 재무, 신호)
    # 구분별 — 부문 이름이 나오는 줄 ±3줄의 낱말(문턱 2건) — 후보
    구분별 = {}
    if 사업:
        a, b = 사업내용(사업[0])
        for 부, 설명 in 부문이름들(사업[0]):
            핵 = re.sub(r"(부문|사업)$", "", 부)
            if len(핵) < 2:
                continue
            조각 = [부, 설명]            # 부문 이름 · 부문 표의 설명 칸 · 사업의 내용에서 그 이름이 나오는 줄(그 줄만 — 이웃 줄은 다른 부문 글이 섞인다)
            for i in range(a, b):
                줄 = " ".join(c for c in 사업[0].행[i] if c)
                if 핵 in 줄 and len(줄) < 600:
                    조각.append(줄)
            덩 = " ".join(조각)
            점 = 유형점수(덩, 유형낱말, 낱말맥락제외)
            고 = [k for k, n in sorted(점.items(), key=lambda kv: -kv[1]) if n >= 2 and n >= max(점.values()) / 2][:2]
            if 고:
                구분별[부] = " · ".join(("설비 집약 제조" if 재무.get("유형자산÷매출", 0) >= 0.4 else "조립 · 경공업 제조") if k == "제조" else k
                                     for k in 고)
    출처 = ("%s 「사업의 내용」" % 사업[0].글()) if 사업 else "원문 없음"
    근거목록 = [{"출처": 출처, "문장 요약": x} for x in 근거]
    if 재무:
        근거목록.append({"출처": "DART 재무제표 API · 성격별 주석", "문장 요약": " · ".join("%s %.2f" % kv for kv in 재무.items())})
    if 구분별:
        근거목록.append({"출처": "%s 영업부문 주석 · 사업의 내용" % (사업[0].글() if 사업 else ""),
                      "문장 요약": "구분별은 부문 이름 주변 낱말로 고른 후보 — 확정은 E · 본선"})
    경보 = [x for x in 근거 if ("%s" % x).startswith("경보 —")]
    if not 신호["사업의내용찾음"]:
        경보.append("경보 — 어느 보고서에서도 「II. 사업의 내용」 구간을 찾지 못했다(머리 꼴이 다르거나 원문이 없다) — 유형 낱말 0 의 원인")
    낸 = {"판정": 판정, "근거": 근거목록, "구분별": 구분별, "점수": 점수, "경보": 경보, "신호": 신호}
    if 보류:
        낸["보류후보"] = 보류
    return 낸


def _기간열들(머리줄, 보, n):
    """표 머리의 열 이름 → 기간 ID(「제78기」 · 「2025년」 · 「당기」 · 「전기」). 모르면 None."""
    열들 = 열이름(머리줄, n)
    낸 = []
    for x in 열들:
        k = 표준(x)
        m = re.search(r"제(\d+)기", k)
        y = re.search(r"(20\d\d)년?", k)
        if m and 보.기수:
            낸.append(보.열("당") if re.search(r"반기|분기", k) else 기간ID(FY실적, 보.회계연도 - (보.기수 - int(m.group(1)))))
        elif y and not re.search(r"반기|분기|\d월", k):
            낸.append(기간ID(FY실적, int(y.group(1))))
        elif k in _기간표지:
            낸.append(보.열(_기간표지[k], 흐름=False))
        else:
            낸.append(None)
    return 낸


_시장표 = re.compile(r"시장\s*(규모|전체|점유)|산업\s*(규모|전체|동향|현황)|소매\s*판매액|통계청|산업통상|전체\s*(시장|거래액|규모)|업계\s*(전체|합계)|"
                   r"국내\s*(전체|시장)|점유율|비중")


def _시장표인가(보, i, a, 라벨):
    """S10-15 — 그 줄이 회사 지표가 아니라 시장 · 산업 통계 표의 줄인가(줄 이름 · 위로 12줄의 표 머리 · 출처 줄에 시장 · 산업 · 소매판매액 · 통계청 ·
    점유율 · 비중 낱말). 회사의 거래액을 「소매판매액 중 온라인쇼핑 거래액」 시장 표에서 잡지 않는다."""
    if _시장표.search(표준(라벨 or "")):
        return True
    for k in range(i - 1, max(a, i - 12) - 1, -1):
        글 = " ".join(x for x in (보.행[k] or []) if x)
        if _시장표.search(글):
            return True
    for k in range(i + 1, min(len(보.행), i + 4)):
        글 = " ".join(x for x in (보.행[k] or []) if x)
        if re.search(r"출처\s*[:：]|자료\s*[:：]", 글) and _시장표.search(글):
            return True
    return False


def 운영지표모으기(보들, 모):
    """사업의 내용에서 운영 지표(매장 수 · 면적 · 사용자 · 가입자 · 거래액 · 주문 · 수주잔고 · 좌석 · 객실 · 생산능력)를 값만 모은다.
    표의 줄 이름이 맞으면 그 줄의 값(머리가 기간이면 기간마다), 문장이면 「점포 수는 18,000개」 꼴의 첫 수(보고서 기간)."""
    낸 = {}
    for 보 in [b for b in 보들 if b.종류 == "사업"][:1] + [b for b in 보들 if b.종류 != "사업"][:1]:
        a, b = 사업내용(보)
        for 이름, (p, 단위p) in 운영지표틀.items():
            r_ = re.compile(p)
            문장후보 = None                     # 표가 먼저다 — 표에서 못 찾을 때만 문장의 수를 쓴다
            for i in range(a, b):
                r = 보.행[i]
                if not r or not r_.search(r[0] or ""):
                    continue
                l, v = 줄라벨값(r)
                if l and v and any(x is not None for x in v) and _시장표인가(보, i, a, l):
                    모.주의.append("사업지표.%s — %s 줄 %d 「%s」 은 시장 · 산업 통계 표라 회사 지표에서 뺐다(S10-15)" % (이름, 보.글(), i, l[:30]))
                    continue
                if l and v and any(x is not None for x in v):
                    # 그 표의 머리(위로 가장 가까운 단위 줄 다음) — 기간 열을 찾는다
                    머리 = []
                    for k in range(i - 1, max(a, i - 12), -1):
                        if 단위읽기(보.행[k]) is not None:
                            머리 = 보.행[k + 1: i]
                            u = 단위읽기(보.행[k])
                            break
                    else:
                        u = None
                    기간들 = _기간열들(머리, 보, len(v))
                    값 = {}
                    for c, x in zip(기간들, v):
                        if c and x is not None:
                            값[c] = x
                    if not 값 and v[0] is not None:
                        값[보.열("당", 흐름=False)] = v[0]
                    if 값:
                        낸.setdefault(이름, []).append({"공시이름": l, "단위": u or "", "값": 값, "출처": "%s 사업의 내용 표(줄 %d)" % (보.글(), i)})
                        문장후보 = None
                        break
                elif len(r) == 1 and len(r[0]) < 400 and 문장후보 is None:
                    m = re.search("(" + p + r")[^0-9.]{0,25}([0-9][0-9,]*(?:\.[0-9]+)?)\s*(" + 단위p + ")", r[0])
                    if m and _시장표.search(r[0][:max(0, m.start()) + 40]):          # S10-15 — 시장 · 산업 문장의 수는 회사 지표가 아니다
                        m = None
                    if m:
                        문장후보 = {"공시이름": m.group(1), "단위": m.group(m.lastindex), "값": {보.열("당", 흐름=False): 수(m.group(m.lastindex - 1))},
                                  "출처": "%s 사업의 내용 문장(줄 %d)" % (보.글(), i)}
            if 문장후보:
                낸.setdefault(이름, []).append(문장후보)
    return 낸


_단위환산 = {"만명": (1e4, "명"), "천명": (1e3, "명"), "백만명": (1e6, "명"), "만건": (1e4, "건"), "천건": (1e3, "건"),
          "백만건": (1e6, "건"), "천개": (1e3, "개"), "만개": (1e4, "개"), "백만개": (1e6, "개"), "천대": (1e3, "대"),
          "만대": (1e4, "대"), "천톤": (1e3, "톤"), "만톤": (1e4, "톤"), "천원": (1e3, "원"), "백만원": (1e6, "원"),
          "십억원": (1e9, "원"), "억원": (1e8, "원"), "조원": (1e12, "원"), "만회선": (1e4, "회선"), "천회선": (1e3, "회선")}
_화폐단위 = re.compile(r"원|달러|USD|KRW|\$")


def 단위표준(u):
    """공시 단위 글 → (배수, 표준 단위). 「점,%」 같은 겹친 단위는 첫 것만, 「만명」은 (10,000, 명)."""
    u = (u or "").strip()
    u = re.split(r"[,，/·%()]", u)[0].strip().replace(" ", "") if u else ""
    return _단위환산.get(u, (1.0, u))


def 이웃도약(값):
    """기간 순서로 이웃한 두 값의 비가 10 을 넘거나 1/10 아래면 그 자리 글 — 아니면 None(음수 · 0 은 보지 않는다)."""
    열 = sorted(값, key=lambda c: (int(re.sub(r"\D", "", c)[-4:]) if c.startswith("FY") else 2000 + int(re.sub(r"\D", "", c)[-2:]),
                               not c.startswith("FY")))
    for a, b in zip(열, 열[1:]):
        x, y = 값[a], 값[b]
        if x and y and x > 0 and y > 0 and (y / x > 10 or y / x < 0.1):
            return "%s → %s %.0f배" % (a, b, y / x) if y / x > 1 else "%s → %s 1/%.0f" % (a, b, x / y)
    return None


def 판매량모으기(보들):
    """「매출실적 · 판매실적 · 생산실적」 표 가운데 머리에 수량(수량 · 판매량 · 생산량 · 톤 · 대 · 개)이 있는 표의 줄 — 값만(구분 대응은 합류)."""
    낸 = []
    for 보 in [b for b in 보들 if b.종류 == "사업"][:1]:
        a, b = 사업내용(보)
        for i0 in [i for i in 머리찾기(보.행, r"(매출|판매|생산)\s*실적") if a <= i < b]:
            for 표지, u, 머리줄, 자료, _ in 블록들(보.행, i0, 최대=80, 첫블록만=True):
                머리글 = " ".join(" ".join(r) for r in 머리줄) + " " + (u or "")
                if not re.search(r"수량|판매량|생산량|출하량|\(\s*단위\s*[:：]\s*(톤|대|개|천개|백만개|장|EA|ea|kg|㎘)", 머리글):
                    continue
                n = max((len(v) for _, v in (줄라벨값(r) for r in 자료)), default=0)
                기간들 = _기간열들(머리줄, 보, n)
                for r in 자료:
                    l, v = 줄라벨값(r)
                    if not l or re.search(r"합계|소계|금액", 표준(l)):
                        continue
                    값 = {c: x for c, x in zip(기간들, v) if c and x is not None}
                    if 값:
                        낸.append({"공시이름": " · ".join(c for c in r[:2] if c and 수(c) is None), "단위": u or "",
                                  "값": 값, "출처": "%s 「%s」 표" % (보.글(), 보.행[i0][0][:20])})
    return 낸


def 가격변동모으기(보들):
    """「주요 제품 등의 가격변동추이」 표 — 품목 줄의 기간별 단가(값만 · 구분 대응은 합류). S2-13 — 국내 사업보고서가 제조 · 소비재 회사에
    거의 다 주는 판가 원천이다. 원재료의 가격변동은 받지 않는다(원가 쪽). 표 없이 문장만 있으면 빈 목록(부르는 쪽이 까닭을 적는다)."""
    낸 = []
    for 보 in [b for b in 보들 if b.종류 == "사업"][:1]:
        a, b = 사업내용(보)
        for i0 in [i for i in 머리찾기(보.행, r"가격\s*변동\s*(추이|현황)") if a <= i < b]:
            if re.search(r"원재료|원자재|원료", " ".join(보.행[i0][:2])):
                continue
            for 표지, u, 머리줄, 자료, _ in 블록들(보.행, i0, 최대=60, 첫블록만=True):
                n = max((len(v) for _, v in (줄라벨값(r) for r in 자료)), default=0)
                기간들 = _기간열들(머리줄, 보, n)
                if not any(기간들):
                    continue
                for r in 자료:
                    l, v = 줄라벨값(r)
                    if not l or re.search(r"합계|소계|평균$", 표준(l)):
                        continue
                    값 = {c: x for c, x in zip(기간들, v) if c and x is not None}
                    if 값:
                        낸.append({"공시이름": l, "단위": u or "", "값": 값, "출처": "%s 「%s」 표" % (보.글(), (보.행[i0][0] or "")[:24])})
    return 낸


def 가동률모으기(보들):
    """「생산실적 및 가동률」의 가동률 표(머리에 「가동률」 열) · 문장(「평균가동률은 100%」) — 줄마다 그 기간의 가동률(0~1, 값만).
    S2-13 — 자체검사 ⑨ 가 능력 경로의 가동률 상한(관측 최고)을 이 값으로 잰다. 보고서 기간(당기)의 값이다.
    FX-A R1 · R2(2026-10-25) — 기준일 반기와 사업보고서 여러 해를 읽고(종전엔 최신 사업보고서 하나 — 기준일 반기의 표가 안 읽혔다 · F53 · F22),
    곁에 XML 이 있으면 격자로 읽는다. 같은 공시 이름의 줄은 한 줄로 묶어 `값` 에 기간마다 둔다(소비처가 줄 하나의 여러 해를 읽는다).
    줄마다 `기준`(시간 · 인시 · 물량 · 금액 · 모름 — 표 머리 · 단위 · 설명 글)과 `기간`(값이 있는 기간 목록)을 더한다."""
    묶, 차례 = {}, []
    for 보 in _읽을보고서(보들):
        줄들 = _가동률XML(보)
        if 줄들 is None:
            줄들 = _가동률txt(보)
        for y in 줄들:
            키 = 표준(y["공시이름"])
            if 키 not in 묶:
                묶[키] = dict(y, 값={})
                차례.append(키)
            for c, v in y["값"].items():
                묶[키]["값"].setdefault(c, v)
            if 묶[키].get("기준") in (None, "모름") and y.get("기준"):
                묶[키]["기준"] = y["기준"]
    낸 = []
    for k in 차례:
        y = 묶[k]
        y["기간"] = sorted(y["값"], key=_열때)
        y.setdefault("기준", "모름")
        낸.append(y)
    return 낸


def _가동률txt(보):
    """옛 txt 길(XML 이 없는 원문) — 보고서 하나의 가동률 줄 목록."""
    낸 = []
    for 보 in [보]:
        a, b = 사업내용(보)
        당 = 보.열("당", 흐름=False)
        본줄 = set()                                       # 머리가 겹쳐(「라. 생산실적 및 가동률」 · 「(2) 가동률」) 같은 줄을 두 번 읽지 않게
        for i0 in [i for i in 머리찾기(보.행, r"가동\s*률") if a <= i < b]:
            머리글 = " ".join(보.행[i0][:2])
            m = re.search(r"가동률[은는이가\s]*([0-9]+(?:\.[0-9]+)?)\s*%", 머리글)
            if m and len(머리글) < 400:
                낸.append({"공시이름": "문장 — " + 머리글[max(0, m.start() - 20): m.end()].strip(), "단위": "%",
                          "값": {당: float(m.group(1)) / 100.0}, "출처": "%s 사업의 내용 문장(줄 %d)" % (보.글(), i0), "기준": _가동률기준(머리글)})
                continue
            # 표 — 머리 뒤 60줄 안에서(다음 절 머리 「3.」 · 「마.」 에서 멈춘다) 「29.1%」 꼴 칸을 그 앞의 가장 가까운 이름 칸과 짝짓는다.
            # 칸마다 빈 줄로 갈린 원문은 「29.1%」 가 수로 안 읽혀 블록 묶기가 어긋난다 — 줄을 직접 훑는다(회사 · 업종 무관)
            이름 = None
            for j in range(i0 + 1, min(b, i0 + 60)):
                줄 = 보.행[j]
                수칸 = len(줄) == 1 and re.fullmatch(r"[0-9.,]+\s*%?", (줄[0] or "").strip())     # 「29.1%」 한 칸 줄은 절 머리(「3.」)가 아니다
                if j > i0 + 1 and not 수칸 and (_주석머리(줄) or (len(줄) == 1 and re.match(r"^[가-하]\.\s*\S", 줄[0] or "") and len(줄[0]) < 60)):
                    break
                for c in 줄:
                    c = (c or "").strip()
                    mm = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*%", c)
                    if mm and 이름 and j not in 본줄:
                        x = float(mm.group(1))
                        본줄.add(j)
                        if 0 <= x <= 300:
                            낸.append({"공시이름": 이름, "단위": "%", "값": {당: round(x / 100.0, 6)},
                                      "출처": "%s 「%s」 표(줄 %d)" % (보.글(), (보.행[i0][0] or "")[:24], j),
                                      "기준": _가동률기준(" ".join(" ".join(보.행[k]) for k in range(i0, min(b, i0 + 4))))})
                    elif c and 수(c) is None and len(c) < 40 and not re.search(r"단위|가동|생산능력|생산실적|시간|합\s*계|소\s*계|^※|^주\d", c):
                        이름 = c
    return 낸


_성과급re = re.compile(r"성과급|초과\s*이익\s*분배|이익\s*분배|성과\s*인센티브|Profit\s*Sharing")
# 「영업이익의 10%」 · 「초과이익의 20%」 · 「EVA 의 x%」 — 이익에 묶인 지급률(PS). 「기본급의 x%」(PI · 목표 연동)는 잡지 않는다
_성과율re = re.compile(r"(?:영업\s*이익|초과\s*이익|당기\s*순이익|세전\s*이익|EVA)\s*(?:의|에서|중)?\s*(\d{1,2}(?:\.\d+)?)\s*%")


def 성과급원문(보들):
    """성과급 · 이익 연동 보상 제도 서술 → (위치 글, [{"위치", "글"}], 율 칸) — 판정은 E 의 몫(S4-02).
    율 칸 = {"값": 0.10, "문장", "위치"} — 「영업이익의 x%」 꼴(이익에 묶인 지급률 · PS)이 원문에 있을 때만. 기본급 비례(PI)는 율로 잡지 않는다."""
    위치, 문장, 율 = [], [], None
    for 보 in 보들[:3]:
        for i, r in enumerate(보.행):
            글 = " ".join(c or "" for c in r[:3])
            if not _성과급re.search(글):
                continue
            곳 = "%s 줄 %d" % (보.글(), i)
            if len(위치) < 3:
                위치.append(곳)
                문장.append({"위치": 곳, "글": 글.strip()[:300]})
            m = _성과율re.search(글)
            if m and 율 is None:
                v = float(m.group(1)) / 100.0
                if 0 < v <= 0.5:
                    율 = {"값": v, "문장": 글.strip()[:300], "위치": 곳}
    return (" · ".join(위치) if 위치 else "확인 불가"), 문장, (율 or _확인불가)


_계리re = re.compile(r"(미래)?\s*(임금|급여)\s*(상승|인상)\s*률")


def 계리임금모으기(보들):
    """S4-03 — 퇴직급여 주석의 보험수리적 가정 「미래임금상승률」 → {"연결": {"범위": [낮은, 높은], "출처"}, "별도": {…}}(가장 최근 사업 · 반기 보고서의
    첫 표 — 당기). 민감도 표(금액 칸이 있는 줄)는 뺀다. 값 꼴: 0.0300 · 3.00% · 3.00%~6.04%."""
    낸 = {}
    for 보 in sorted(보들, key=lambda b: (b.끝 or datetime.date.min), reverse=True):
        for i, r in enumerate(보.행):
            if not r or not _계리re.search(r[0] or "") or len(r[0] or "") > 40:
                continue
            범위이름 = "연결" if 보.연결[i] else "별도"
            if 범위이름 in 낸:
                continue
            값, 금액칸 = [], False
            for c in r[1:]:
                c = (c or "").strip()
                if not c:
                    continue
                for a in re.findall(r"(\d+(?:\.\d+)?)\s*%", c):
                    값.append(float(a) / 100.0)
                if "%" not in c:
                    v = 수(c)
                    if v is not None:
                        if 0.003 <= abs(v) <= 0.3 and re.fullmatch(r"0\.\d+", c):
                            값.append(v)
                        else:
                            금액칸 = True
            값 = [v for v in 값 if 0.003 <= v <= 0.3]
            if 금액칸 or not 값 or (len(값) == 1 and abs(값[0] - 0.01) < 1e-9 and "민감" in " ".join(보.행[max(0, i - 6)][0:1])):
                continue
            낸[범위이름] = {"범위": sorted({round(min(값[:2]), 6), round(max(값[:2]), 6)}), "출처": "%s 줄 %d 「%s」" % (보.글(), i, (r[0] or "")[:20])}
        if 낸:
            return 낸
    return 낸 or _확인불가


_세주석re = re.compile(r"세액\s*공제|이월\s*결손금|세무상\s*결손금|미사용\s*세무|최저한세|글로벌\s*최저|필라\s*2|Pillar\s*2|추가\s*세액|"
                      r"인식하지\s*(아니한|않은)\s*(이연|차감|일시)")
_글최re = re.compile(r"글로벌\s*최저한세|필라\s*2|Pillar\s*2|Pillar\s*Two|추가세액|top-?up\s*tax", re.I)


_정책문re = re.compile(r"회계정책|인식한다|측정한다|인식하지\s*않는다|발생하는\s*이연법인세자산은|가능성이\s*높은\s*경우")
_미인식만료re = re.compile(r"(인식되지|인식하지)\s*(아니한|않은).{0,40}(결손금|세액\s*공제)|만료\s*시기|만료\s*연도")


def 법인세주석후보(보들):
    """S6-07 — 연결 주석 「법인세」 구획에서 세액공제 · 이월결손금 · 최저한세 · 글로벌 최저한세 · 미인식 일시차이 줄을 후보로 뽑는다(값은 사람이 옮긴다).
    → ([{"위치", "글", "숫자", "정책"}], 글로벌 최저한세 위치 또는 None).
    S6R1-N2(S9 이월) — **사업보고서를 먼저** 읽고(반기 줄로 멈추지 않는다), 보고서마다 「법인세」 머리를 **모두** 훑는다(첫 머리 하나가 아니다).
    회계정책 문장(인식 · 측정 기준 — 금액 칸이 없는 상투 문장)은 `정책` 표지를 단다 — 「공제 자료 있음」 은 금액 칸이 있는 줄로만 세운다(`법인세블록`).
    금액 칸이 있는 세액공제 줄을 사업보고서에서 찾으면 멈춘다."""
    후보, 글최 = [], None
    차례 = sorted(list(보들[:4]), key=lambda b: 0 if getattr(b, "종류", "") == "사업" else 1)
    for 보 in 차례:
        머리 = [i for i, r in enumerate(보.행) if _주석머리(r) and re.search(r"법인세", r[0] or "") and 보.연결[i]]
        for i in 머리:
            끝 = next((j for j in range(i + 1, min(len(보.행), i + 800)) if _주석머리(보.행[j])), min(len(보.행), i + 800))
            for j in range(i + 1, 끝):
                글 = " ".join(c for c in 보.행[j] if c).strip()
                if (_세주석re.search(글) or _미인식만료re.search(글)) and len(후보) < 24:
                    숫 = [v for v in (수(c) for c in 보.행[j][1:]) if v is not None][:6]
                    후보.append({"위치": "%s 줄 %d" % (보.글(), j), "글": 글[:240], "숫자": 숫,
                               "정책": bool(_정책문re.search(글)) and not 숫, "보고서": getattr(보, "종류", "")})
        if 글최 is None:
            for j, r in enumerate(보.행):
                if 보.연결[j] and _글최re.search(" ".join(c for c in r[:3] if c)):
                    글최 = "%s 줄 %d" % (보.글(), j)
                    break
        if getattr(보, "종류", "") == "사업" and any(re.search(r"세액\s*공제", x["글"]) and x["숫자"] for x in 후보):
            break
    if 글최 is None:                                     # 글로벌 최저한세 서술은 반기 · 분기에만 있을 수 있다 — 멈춘 뒤에도 남은 보고서를 훑는다
        for 보 in 차례:
            for j, r in enumerate(보.행):
                if 보.연결[j] and _글최re.search(" ".join(c for c in r[:3] if c)):
                    글최 = "%s 줄 %d" % (보.글(), j)
                    break
            if 글최:
                break
    return 후보, 글최


def 법인세블록(모, 보들, a, 판):
    """S6-07 — 법인세 재료: 해마다 실효세율(법인세비용 ÷ 세전이익) · 현금유효세율(법인세 납부 ÷ 세전이익) · 이연법인세 · 결손금 · 평가충당금 · 공제
    (미국 companyfacts 태그 · 국내 API + 법인세 주석 후보 줄). E 법인세 노드가 결정 9 의 갈래(공제 자료가 있으면 법정 + 공제 따로)를 판정하는 재료다."""
    회 = 모.회전
    시계 = {c: {k[3:]: round(v, 6) for k, v in d.items() if k.startswith("_세_")} for c, d in sorted(회.items(), key=lambda t: _열때(t[0]))}
    시계 = {c: v for c, v in 시계.items() if v}
    실효 = {c: round(d["_실효세율"], 6) for c, d in 회.items() if "_실효세율" in d and c.startswith("FY")}
    현금 = {c: round(d["_현금유효세율"], 6) for c, d in 회.items() if "_현금유효세율" in d and c.startswith("FY")}
    후보, 글최 = 법인세주석후보(보들) if 보들 else ([], None)
    끝 = 시계[max(시계, key=_열때)] if 시계 else {}
    if a.미국:
        공제 = [k for k in ("공제_연구개발", "공제_합계", "이월세액공제", "연구개발공제이월") if any(abs(v.get(k) or 0) > 0 for v in 시계.values())]
        연구 = any(abs(v.get("공제_연구개발") or 0) > 0 or abs(v.get("연구개발공제이월") or 0) > 0 for v in 시계.values())
        공제글 = ("있음 — companyfacts %s" % " · ".join(공제)) if 공제 else "없음 — companyfacts 에 세액공제 태그(연구개발 · 합계 · 이월)가 없다(10-K 세율 조정표에서 확인)"
    else:
        # S6R1-N2 — 「있음」 은 금액 칸이 있는 세액공제 줄(세율 조정표 · 미사용 세액공제 표)로만 세운다. 정책 문장 · 금액 없는 줄만 있으면 확인 불가
        공줄 = [x for x in 후보 if re.search(r"세액\s*공제", x["글"]) and x.get("숫자")]
        글만 = [x for x in 후보 if re.search(r"세액\s*공제", x["글"]) and not x.get("숫자")]
        연구 = any(re.search(r"연구", x["글"]) for x in 공줄)
        공제글 = ("있음 — 법인세 주석의 금액 줄 %d개(%s)" % (len(공줄), 공줄[0]["위치"])) if 공줄 else (
            ("%s — 세액공제 낱말은 있으나 금액 칸이 있는 줄이 없다(정책 · 서술 문장 %d줄 — %s). 세율 조정표 · 미사용 세액공제 표를 사람이 본다"
             % (_확인불가, len(글만), 글만[0]["위치"])) if 글만 else
            ("없음 — 법인세 주석에서 세액공제 줄을 찾지 못했다(읽은 보고서 %d개 · 사업보고서 먼저)" % len(보들) if 보들 else "확인 불가 — 원문 없음"))
    return {"실효세율": 실효 or _확인불가, "현금유효세율": 현금 or _확인불가, "시계열": 시계,
            "주석후보": 후보 if 후보 else ("%s — 연결 주석 「법인세」 구획에서 세액공제 · 결손금 줄을 못 찾았다" % _확인불가 if not a.미국 else _해당없음),
            "공제자료": 공제글, "연구개발공제따로": ("예 — " + ("companyfacts 연구개발 공제 태그" if a.미국 else "법인세 주석에 연구개발 세액공제 줄")) if 연구 else "아니오",
            "이연법인세자산": {c: v["이연법인세자산"] for c, v in 시계.items() if "이연법인세자산" in v} or _확인불가,
            "이연법인세부채": {c: v["이연법인세부채"] for c, v in 시계.items() if "이연법인세부채" in v} or _확인불가,
            "이월결손금": ({c: v["이월결손금"] for c, v in 시계.items() if "이월결손금" in v} or
                      ("%s — %s" % (_확인불가, "companyfacts OperatingLossCarryforwards 없음" if a.미국 else "법인세 주석 후보 줄에서 사람이 옮긴다"))),
            "이월세액공제": ({c: v["이월세액공제"] for c, v in 시계.items() if "이월세액공제" in v} or
                       ("%s — %s" % (_확인불가, "companyfacts TaxCreditCarryforwardAmount 없음" if a.미국 else "법인세 주석 후보 줄에서 사람이 옮긴다(원천 580)"))),
            "미인식만료": [x for x in 후보 if _미인식만료re.search(x["글"]) and x.get("숫자")] or None,       # S6R1-N2 — 인식되지 않은 결손금 · 공제의 잔액 · 만료 줄
            "글로벌최저한세": ("공시 있음 — %s" % 글최) if 글최 else ("%s — 원문에서 글로벌 최저한세(Pillar 2) 서술을 못 찾았다" % _확인불가 if 보들 else
                                                     "%s — 원문 없음(미국은 10-K 세율 조정표 · Pillar Two 서술)" % _확인불가),
            "출처": "DART 재무제표 API(세전이익 · 법인세비용 · 법인세 납부 · 이연법인세) · 연결 주석 「법인세」" if not a.미국 else
                    "SEC companyfacts(IncomeTaxExpenseBenefit · IncomeTaxesPaidNet · OperatingLossCarryforwards · DeferredTaxAssetsValuationAllowance · UnrecognizedTaxBenefits · IncomeTaxReconciliation…)",
            "_끝": 끝}


_계약머리re = re.compile(r"경영상의\s*주요\s*계약|주요\s*계약\s*(및|등)")
_계약줄re = re.compile(r"계약|라이선스|마일스톤|기술\s*이전|공급|보조금|협약|만료|종료")
_날re = re.compile(r"(20\d{2})\s*[.\-년/]\s*(\d{1,2})(?:\s*[.\-월/]\s*(\d{1,2}))?")


_기간쌍re = re.compile(r"(20\d{2})\s*[.\-년/]\s*(\d{1,2})(?:\s*[.\-월/]\s*(\d{1,2}))?\s*일?\s*(?:~|∼|부터|–|-)\s*"
                     r"(20\d{2})\s*[.\-년/]\s*(\d{1,2})(?:\s*[.\-월/]\s*(\d{1,2}))?")
_조건끝re = re.compile(r"로열티\s*(지급)?\s*기간|출시\s*(후|일로부터|이후)|특허\s*(만료|존속)|존속\s*기간|만료\s*시\s*까지|종료\s*시\s*까지|해지\s*시\s*까지|"
                     r"별도\s*(합의|약정)\s*시\s*까지|상업화\s*(후|이후)|자동\s*(연장|갱신)|판매\s*(종료|중단)\s*시|"
                     # FX2-A R9 — 끝이 사건인 꼴(상용화 · 허가 승인 · 첫 수출 · 수취 완료 · 지급 의무 만료 · 영구 · 「…로부터 N년」 · 계약종료일 칸이 날짜가 아님)
                     r"상용화\s*(될\s*때\s*까지|시\s*까지|후|이후)|허가\s*(승인)?\s*(일|후)\s*(로부터)?|첫\s*수출\s*일|수취\s*완료|지급\s*의무.{0,8}만료|"
                     r"계약\s*종료\s*일?\s*[:：]\s*영구|로부터\s*\d{1,2}\s*년\s*간?|계약\s*종료\s*일?\s*[:：]\s*(?!\s*\d{4})[가-힣A-Za-z]")
_체결re = re.compile(r"체결|계약\s*일|서명|계약\s*시점")
_끝말re = re.compile(r"만료|종료|까지|만기|기한")


def _날글(t):
    y, m, d = t
    return "%s-%02d%s" % (y, int(m), ("-%02d" % int(d)) if d else "")


_자사주계약re = re.compile(r"자기\s*주식|자사주|신탁\s*계약\s*(해지|체결)|연결\s*제외|해지\s*(완료|됨|하였)|계약\s*(해지|해제|종료)\s*(완료|됨|하였)|청산\s*완료")


def 계약시한후보(보들, 기준일=None):
    """S6-13 — 사업보고서 「경영상의 주요계약」 절에서 끝나는 날이 적힌 계약 줄(기술이전 · 마일스톤 · 장기공급 · 라이선스 · 보조금 협약)을 후보로 뽑는다.
    FX2-A R9(2026-10-25) — 자기주식 신탁 · 해지 · 연결 제외 줄(이미 끝난 일)은 뺀다. `기준일`(「YYYY-MM-DD」)을 주면 끝나는날이 기준일 달보다 앞선
    날짜 계약도 뺀다 — 계약시한은 기준일 뒤 끝나는 돈의 후보다(조건형 · 끝 모름은 남긴다).
    → [{"이름", "끝나는날", "글", "출처", "끝꼴", "시작일", "조건글"}] — 금액 경로 · 상대는 본선이 원문에서 옮긴다(F `계약시한[]` → `구조.한시적현금흐름[]`).
    FX-A R2(2026-10-25) — ① 「2020.01.01 ~ 2029.12.31」 기간 쌍이면 시작 · 끝을 가른다 ② 날짜가 하나뿐이고 체결 · 계약일 낱말 곁이면 그것은 **시작일**이다
    (체결일을 끝나는날로 적던 결함 — F33 · F46) ③ 끝이 날짜가 아니라 조건(로열티 기간 · 출시 후 10년 · 특허 만료)이면 `끝꼴: 조건` · `조건글`
    ④ 날짜 없는 소제목 · 날짜가 셋 넘는 연혁 줄은 뺀다(F39 · F62) ⑤ 기준일 반기의 같은 절도 읽는다(같은 계약은 한 번). 「끝나는날」 은 끝꼴이 날짜일 때만."""
    낸, 본 = [], set()
    for 보 in _읽을보고서(보들, 다년=False):
        머리 = [i for i, r in enumerate(보.행) if any(_계약머리re.search(c or "") for c in r[:2]) and len(" ".join(c for c in r if c)) < 60]
        for i in 머리[:1]:
            for j in range(i + 1, min(len(보.행), i + 120)):
                r = 보.행[j]
                글 = " ".join(c for c in r if c).strip()
                if j > i + 3 and _주석머리(r) and not _계약줄re.search(글):
                    break
                if not _계약줄re.search(글) or len(낸) >= 12:
                    continue
                날 = _날re.findall(글)
                쌍 = _기간쌍re.search(글)
                조건 = _조건끝re.search(글)
                if len(날) > 3 and not 쌍:
                    continue                                  # 연혁 · 경과 나열 줄(날짜가 셋 넘게)은 계약 기간이 아니다
                if not 날 and not 조건:
                    continue
                y = {"이름": (r[0] or "")[:40], "글": 글[:240], "출처": "%s 줄 %d 「경영상의 주요계약」" % (보.글(), j)}
                if 쌍:
                    y.update(시작일=_날글(쌍.group(1, 2, 3)), 끝나는날=_날글(쌍.group(4, 5, 6)), 끝꼴="날짜")
                elif 조건:
                    y.update(끝나는날="", 끝꼴="조건", 조건글=글[max(0, 조건.start() - 40): 조건.end() + 40].strip())
                    if 날:
                        y["시작일"] = _날글(날[0])
                elif len(날) == 1 and _체결re.search(글[:max(0, 글.find(날[0][0])) + 1][-30:] + 글) and not _끝말re.search(글):
                    y.update(끝나는날="", 끝꼴="모름", 시작일=_날글(날[0]), 조건글="체결일만 적혔다 — 끝은 원문 계약 조건에서 본선이 옮긴다")
                else:
                    # FX2-A R9 — 「…일까지 · 만료 · 종료」 가 바로 뒤에 붙은 날짜가 끝이다(그런 날짜가 없으면 마지막 날짜 — 종전 길). 「2033년 12월 31일까지
                    # 서비스 라이선스 유지 … 2022년 9월 매각 완료」 를 마지막 날짜(2022-09)로 읽어 이미 끝난 계약으로 버리던 꼴
                    끝후보 = [(m.group(1), m.group(2), m.group(3)) for m in _날re.finditer(글)
                            if re.match(r"\s*일?\s*(까지|만료|종료|만기)", 글[m.end(): m.end() + 8])]
                    y.update(끝나는날=_날글(max(끝후보, key=lambda t: (int(t[0]), int(t[1]), int(t[2] or 0))) if 끝후보 else 날[-1]), 끝꼴="날짜")
                    if len(날) >= 2:
                        y["시작일"] = _날글(날[0])
                if len(y["글"]) < 40 and not 쌍 and re.match(r"^\s*(\(?\d{1,2}\)|[가-하]\.|\d{1,2}\.)\s", 글):
                    continue                                  # 「(1) 기술이전 계약」 꼴 소제목
                if _자사주계약re.search(글):
                    continue                                  # FX2-A R9 — 자기주식 신탁 해지 · 연결 제외 · 해지 완료 줄은 끝나는 계약이 아니다
                if 기준일 and y.get("끝꼴") == "날짜" and y.get("끝나는날") and y["끝나는날"][:7] < 기준일[:7]:
                    continue                                  # FX2-A R9 — 기준일 앞에 이미 끝난 계약
                키 = (표준(y["이름"]), y.get("끝나는날"), y.get("시작일"))
                if 키 in 본:
                    continue
                본.add(키)
                낸.append(y)
    return 낸


def 해당없음판정(보들, 유형, 해):
    """그 유형에 원래 없는 원천 — [{"항목", "까닭"}]. 「해당 사항 없음」 문구가 공시에 있으면 그것이 근거다."""
    낸 = []
    판 = 유형["판정"]
    재고있음 = any((v or {}).get("재고") for v in 해.values())
    if 해 and not 재고있음:
        낸.append({"항목": "재고자산회전일수", "까닭": "재무상태표에 재고자산이 없다"})
    사업 = [b for b in 보들 if b.종류 == "사업"][:1]
    글 = ""
    if 사업:
        a, b = 사업내용(사업[0])
        글 = " ".join(" ".join(c for c in r if c) for r in 사업[0].행[a:b])
    for 항목, p in (("생산능력", r"생산\s*능력[^.。]{0,60}해당\s*(사항)?\s*(이\s*)?없"),
                   ("수주잔고", r"수주[^.。]{0,40}해당\s*(사항)?\s*(이\s*)?없"),
                   ("연구개발", r"연구\s*개발[^.。]{0,40}해당\s*(사항)?\s*(이\s*)?없")):
        if re.search(p, 글):
            낸.append({"항목": 항목, "까닭": "공시가 「해당 사항 없음」이라고 적었다"})
    if not any(x in 판 for x in ("설비 집약 제조", "조립 · 경공업 제조")) and not any(x["항목"] == "생산능력" for x in 낸) \
            and not re.search(r"생산\s*능력", 글):
        낸.append({"항목": "생산능력", "까닭": "유형(%s) — 사업의 내용에 생산능력 표가 없다" % " · ".join(판)})
    if "수주 산업" not in 판 and not any(x["항목"] == "수주잔고" for x in 낸) and not re.search(r"수주\s*잔고", 글):
        낸.append({"항목": "수주잔고", "까닭": "유형(%s) — 수주잔고 공시가 없다" % " · ".join(판)})
    return 낸


def _열때(c):
    """기간 ID → (회계연도, 끝 달) — FY2025A → (2025, 12) · 1H26A → (2026, 6) · 1Q26A → (2026, 3) · 9M26A → (2026, 9)."""
    m = re.match(r"FY(\d{4})", c or "")
    if m:
        return int(m.group(1)), 12
    m = re.match(r"(\d)([QHM])(\d{2})", c or "")
    if m:
        n = int(m.group(1))
        return 2000 + int(m.group(3)), {"Q": 3 * n, "H": 6 * n, "M": n}[m.group(2)]
    return 0, 0


def _뒤집힘(값들, 문턱):
    """지그재그 — 직전 극점에서 문턱 넘게 거꾸로 움직인 방향 전환 횟수(작은 흔들림은 세지 않는다)."""
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


def 국면(회전):
    """사이클 신호로 국면을 가른다(2026-10-17 S6-01 — 종전에는 영업이익률 사분위만 봐서 성장 · 흑자 전환 · 구조조정을 「저점 · 정점」으로 불렀다).

    ① **사이클인가** — 회계연도 매출 증감의 부호 전환(±3% 안은 평탄 — 세지 않는다)이 둘 이상이거나, 영업이익률이 5%p 넘게 오르내린
       방향 전환(지그재그)이 둘 이상이고, 영업이익률 폭이 10%p 이상일 때만 사이클이다. 해가 넷 미만이면 판정하지 않는다.
    ② **사이클이 아니면**(성장 · 흑자 전환 · 구조조정 · 안정) 「구분 없음 — 몇 개년 범위」 항목 하나다(E 가 몇 개년 범위를 쓴다).
       초기 적자 램프업 해는 `회전일수` 가 구조 단절 후보로 이미 뺐다.
    ③ **사이클이면** 영업이익률 사분위(회계연도로 문턱을 잰다)로 정점 · 저점 · 중간을 가른다. 연속한 같은 이름만 한 구간으로 묶고, 같은 이름의
       구간이 여럿이면 여럿을 그대로 낸다(E · ㊺ 가 이름별로 **모든 구간을 합쳐** 범위를 잰다).
    ④ 마지막 회계연도 뒤의 반기 · 분기 누계 열(연환산)도 같은 문턱으로 국면에 넣는다 — 정점이 반기 열에 있는 회사(㊺ 정점 열)."""
    열들 = sorted((c for c, d in 회전.items() if d.get("영업이익률") is not None), key=_열때)
    fy = [(c, 회전[c]["영업이익률"]) for c in 열들 if c.startswith("FY")]
    끝fy = _열때(fy[-1][0]) if fy else (0, 0)
    뒤 = [c for c in 열들 if not c.startswith("FY") and _열때(c) > 끝fy]
    뒤 = 뒤[-1:]                                                     # 가장 늦은 누계 열 하나(연환산 — 1H26A)
    폭 = (max(x for _, x in fy) - min(x for _, x in fy)) if fy else 0.0
    매 = [(회전[c].get("_매출연") or 0.0) for c, _ in fy]
    부호 = []
    for a, b in zip(매, 매[1:]):
        if a > 0 and b:
            g = b / a - 1
            if abs(g) > 0.03:
                부호.append(1 if g > 0 else -1)
    매출전환 = sum(1 for a, b in zip(부호, 부호[1:]) if a != b)
    이익전환 = _뒤집힘([x for _, x in fy], 0.05)
    신호 = "매출 증감 부호 전환 %d번 · 영업이익률 5%%p 넘는 방향 전환 %d번 · 영업이익률 폭 %.1f%%p · %d해" % (매출전환, 이익전환, 폭 * 100, len(fy))
    if len(fy) < 4 or 폭 < 0.10 or (매출전환 < 2 and 이익전환 < 2):
        까닭 = "해가 넷 미만" if len(fy) < 4 else ("영업이익률 폭이 10%p 안" if 폭 < 0.10 else "사이클 신호 없음(추세 · 성장 · 구조 변화)")
        return [{"기간": [c for c, _ in fy] + 뒤, "이름": "구분 없음 — 몇 개년 범위", "사이클": False, "근거": "%s — %s" % (까닭, 신호)}]
    값 = sorted(x for _, x in fy)
    q1, q3 = 값[len(값) // 4], 값[(3 * len(값)) // 4]
    낸 = []
    for c in [c for c, _ in fy] + 뒤:
        x = 회전[c]["영업이익률"]
        이름 = "저점" if x <= q1 else ("정점" if x >= q3 else "중간")
        근 = "사이클(%s) · 영업이익률 사분위(하 %.1f%% · 상 %.1f%%)%s" % (신호, q1 * 100, q3 * 100, "" if c.startswith("FY") else " · 누계 열 연환산")
        if 낸 and 낸[-1]["이름"] == 이름:
            낸[-1]["기간"].append(c)
        else:
            낸.append({"기간": [c], "이름": 이름, "사이클": True, "근거": 근})
    return 낸


# ────────────────────────────────────────────────────────────── API — 대조 · 회전일수 실적

_API = {"매출": ("ifrs-full_Revenue",), "매출원가": ("ifrs-full_CostOfSales",),
        "판관비": ("dart_TotalSellingGeneralAdministrativeExpenses",), "영업이익": ("dart_OperatingIncomeLoss",),
        "매출채권": ("ifrs-full_CurrentTradeReceivables", "ifrs-full_TradeAndOtherCurrentReceivables", "dart_ShortTermTradeReceivable"),
        "재고": ("ifrs-full_Inventories",),
        "매입채무": ("ifrs-full_TradeAndOtherCurrentPayablesToTradeSuppliers", "ifrs-full_CurrentTradePayables",
                  "dart_ShortTermTradePayables", "ifrs-full_TradeAndOtherCurrentPayables"),
        "유형자산": ("ifrs-full_PropertyPlantAndEquipment",),
        "계약부채": ("ifrs-full_CurrentContractLiabilities", "ifrs-full_ContractLiabilities"),
        "계약자산": ("ifrs-full_CurrentContractAssets", "ifrs-full_ContractAssets"),
        "선수금": ("dart_ShortTermAdvancesCustomers", "ifrs-full_CurrentAdvancesReceived"),
        # 현금흐름표 투자활동 — DART 표준 계정 ID 는 「…ClassifiedAsInvestingActivities」가 붙는다(S5-15 — 붙지 않은 ID 만 찾아
        # 국내 전 회사에서 현금 CAPEX 가 빠졌다). 무형자산의 취득 · 사업결합(종속기업 취득)은 따로 둔다 — CAPEX 비율 · ㊹ 가 나눠 읽는다
        "CAPEX": ("ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities", "ifrs-full_PurchaseOfPropertyPlantAndEquipment",
                  "dart_PurchaseOfPropertyPlantAndEquipment"),
        "무형취득": ("ifrs-full_PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities", "ifrs-full_PurchaseOfIntangibleAssets",
                 "dart_PurchaseOfIntangibleAssets"),
        "사업결합취득": ("ifrs-full_CashFlowsUsedInObtainingControlOfSubsidiariesOrOtherBusinessesClassifiedAsInvestingActivities",
                   "dart_AcquisitionOfSubsidiaries")}
_API이름 = {"매출": ("매출액", "수익(매출액)", "영업수익", "매출"), "매출원가": ("매출원가",), "판관비": ("판매비와관리비", "영업비용"),
          "재고": ("재고자산",), "계약부채": ("계약부채", "유동계약부채"), "계약자산": ("계약자산", "유동계약자산"),
          "선수금": ("선수금",), "매출채권": ("매출채권", "매출채권및기타채권"), "매입채무": ("매입채무", "매입채무및기타채무"),
          "CAPEX": ("유형자산의취득", "유형자산의 취득", "유형자산취득"), "무형취득": ("무형자산의취득", "무형자산의 취득", "무형자산취득"),
          "사업결합취득": ("종속기업의취득", "종속기업취득으로인한순현금흐름", "사업결합으로인한순현금유출")}
_API흐름 = ("CAPEX", "무형취득", "사업결합취득")        # 현금흐름표 줄 — 이름 대체도 CF 에서 찾는다
# FX-A R2 · R8 재료(2026-10-25) — 현금흐름표 투자활동의 자산군별 취득 줄(「토지의 취득」 · 「기계장치의 취득」 …). 「유형자산의 취득」 한 줄 없이
# 자산군별로만 적는 회사는 CAPEX 가 「확인 불가」였다(F18) — 그 합을 CAPEX 로 쓰고 `CAPEX구성.자산군별` 에 남긴다
_자산군취득re = re.compile(r"^(토지|건물|구축물|기계장치|건설중인자산|차량운반구|공구와기구|공구기구|공기구비품|비품|집기비품|선박|항공기|시설장치|"
                       r"기타의?유형자산|기타유형자산|금형|탱크|구축물및기계장치|건물및구축물|임차시설물|인테리어|전산장비|업무용비품|생산설비)의?(취득|증가|구입)$")


def _CAPEX구성(목록, 누계=False):
    """현금흐름표(CF) 줄 → {"자산군별": {자산군: 값}, "개발비자본화", "투자부동산취득"}(원 · 절댓값). 없으면 빈 칸."""
    d = {"자산군별": {}}
    for x in 목록:
        if x.get("sj_div") != "CF":
            continue
        k = 표준(x.get("account_nm"))
        v = _api숫자(x, 누계)
        if v is None:
            continue
        m = _자산군취득re.match(k)
        if m:
            d["자산군별"][m.group(1)] = d["자산군별"].get(m.group(1), 0.0) + abs(v)
        elif re.match(r"^개발비의?(취득|증가|지출|자본화)$", k):
            d["개발비자본화"] = d.get("개발비자본화", 0.0) + abs(v)
        elif re.match(r"^투자부동산의?(취득|증가)$", k):
            d["투자부동산취득"] = d.get("투자부동산취득", 0.0) + abs(v)
    return d


def _api숫자(x, 누계=False):
    s = x.get("thstrm_add_amount") if (누계 and x.get("sj_div") not in ("BS", "CF") and x.get("thstrm_add_amount")) else x.get("thstrm_amount")
    try:
        return float(str(s).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _api값(목록, 키, 누계=False, 출처=False):
    """표준 태그 → 계정 이름 차례로 첫 값. 출처=True 면 (값, 잡은 태그 · 이름) — 묶음 태그(매출채권 및 기타채권 · 매입채무 및 기타채무)를
    가르려고 쓴다(S6-06)."""
    for aid in _API[키]:
        for x in 목록:
            if (x.get("account_id") or "") == aid and x.get("sj_div") in ("BS", "IS", "CIS", "CF"):
                v = _api숫자(x, 누계)
                if v is not None:
                    return (v, aid) if 출처 else v
    for 이름 in _API이름.get(키, ()):            # 표준 태그가 없는 회사 — 계정 이름(같은 이름이 둘이면 첫 줄)
        for x in 목록:
            if 표준(x.get("account_nm")) == 표준(이름) and x.get("sj_div") in (("CF",) if 키 in _API흐름 else ("BS", "IS", "CIS")):
                v = _api숫자(x, 누계)
                if v is not None:
                    return (v, 이름) if 출처 else v
    return (None, None) if 출처 else None


# S6-05 · S6-02 — 엔진 190(기타 순운전자본)의 자: 13번 원천 14 + 15 − 35 − 36 − 40 − 43(가정_스키마 「190 은 채우는 행」). A3 는 A2(원천 조립)의
# 태그 표를 그대로 읽어 같은 행을 잰다 — 같은 값을 다른 태그로 다시 뽑으면 기준이 다른 두 값이 생긴다(A3 지시서 「A2 의 13번 행을 다시 만들지 않는다」)
기타행부호 = ((14, 1), (15, 1), (35, -1), (36, -1), (40, -1), (43, -1))
# 묶음 태그 — 매출채권 · 매입채무 회전일수에 미지급금 · 미수금이 섞인다(CLAUDE.md 운전자본 규칙 「묶음 계정은 통째로 넣지 않는다」 — S6-06)
묶음태그 = {"ifrs-full_TradeAndOtherCurrentReceivables", "매출채권및기타채권", "ifrs-full_TradeAndOtherCurrentPayables", "매입채무및기타채무",
          "AccountsPayableAndOtherAccruedLiabilitiesCurrent", "AccountsPayableAndAccruedLiabilitiesCurrent",
          "AccountsPayableAndAccruedLiabilitiesCurrentAndNoncurrent", "ReceivablesNetCurrent"}


def _api13(목록, 행, 누계=False):
    """13번 행 하나 — A2 `dart_원천.표` 의 (합산, 태그, 이름)과 보탬 태그로 잰다. 합산 행(15 · 43)은 걸리는 태그를 모두 더한다."""
    import dart_원천 as A2                                    # noqa: PLC0415
    합산, 태그들, 이름들 = A2.표.get(행, (False, (), ()))
    태그들 = tuple(태그들) + tuple(A2._보탬.get(행, ()))
    합, 찾음 = 0.0, False
    for aid in 태그들:
        for x in 목록:
            if (x.get("account_id") or "") == aid and x.get("sj_div") == "BS":
                v = _api숫자(x, 누계)
                if v is not None:
                    합 += v
                    찾음 = True
                    break
        if 찾음 and not 합산 and aid not in A2._보탬.get(행, ()):
            for b in A2._보탬.get(행, ()):                    # 주 태그를 찾았으면 보탬 태그만 더 본다
                for x in 목록:
                    if (x.get("account_id") or "") == b and x.get("sj_div") == "BS":
                        v = _api숫자(x, 누계)
                        if v is not None:
                            합 += v
                            break
            break
    if not 찾음:
        for 이름 in 이름들:
            for x in 목록:
                if 표준(x.get("account_nm")) == 표준(이름) and x.get("sj_div") == "BS":
                    v = _api숫자(x, 누계)
                    if v is not None:
                        return v
    return 합 if 찾음 else None


def _기타모으기(목록, 누계=False):
    """기타 순운전자본 행 여섯과 법인세 재료(S6-07) — {"_13_14": …, "세전이익", "법인세비용", "법인세납부", "이연법인세자산", "이연법인세부채", "미지급비용"}."""
    d = {"_13_%d" % 행: _api13(목록, 행, 누계) for 행, _ in 기타행부호}
    for 키, 태그들, 이름들, sj in (("세전이익", ("ifrs-full_ProfitLossBeforeTax",), ("법인세비용차감전순이익", "법인세비용차감전이익"), ("IS", "CIS")),
                               ("법인세비용", ("ifrs-full_IncomeTaxExpenseContinuingOperations",), ("법인세비용", "법인세 비용"), ("IS", "CIS")),
                               ("법인세납부", ("ifrs-full_IncomeTaxesPaidRefundClassifiedAsOperatingActivities", "ifrs-full_IncomeTaxesPaidRefund"),
                                ("법인세의납부", "법인세납부", "법인세의 납부", "법인세납부액"), ("CF",)),
                               ("이연법인세자산", ("ifrs-full_DeferredTaxAssets",), ("이연법인세자산",), ("BS",)),
                               ("이연법인세부채", ("ifrs-full_DeferredTaxLiabilities",), ("이연법인세부채",), ("BS",)),
                               ("미지급비용", ("dart_ShortTermAccruedExpenses", "ifrs-full_CurrentAccruedExpensesAndOtherCurrentLiabilities"),
                                ("미지급비용",), ("BS",))):
        v = None
        for aid in 태그들:
            for x in 목록:
                if (x.get("account_id") or "") == aid and x.get("sj_div") in sj:
                    v = _api숫자(x, 누계)
                    if v is not None:
                        break
            if v is not None:
                break
        if v is None:
            for 이름 in 이름들:
                for x in 목록:
                    if 표준(x.get("account_nm")) == 표준(이름) and x.get("sj_div") in sj:
                        v = _api숫자(x, 누계)
                        if v is not None:
                            break
                if v is not None:
                    break
        d[키] = abs(v) if (v is not None and 키 == "법인세납부") else v
    return d


def _묶음키(목록, 누계=False):
    """매출채권 · 매입채무를 묶음 태그(… 및 기타채권 · 채무)로 잡았으면 그 키 목록(S6-06)."""
    return [k for k in ("매출채권", "매입채무") if (_api값(목록, k, 누계, 출처=True)[1] or "") in 묶음태그]


def API모으기(폴더들, 모):
    """해마다(앵커 시계열) · 누계(재무_연결) — {열: {매출 · 매출원가 · …}}(원)."""
    해 = {}
    for 폴더 in 폴더들:
        for p in glob.glob(os.path.join(폴더, "dart_앵커시계열.json")):
            for h in json.load(io.open(p, encoding="utf-8")).get("해") or []:
                열 = 기간ID(FY실적, int(h["사업연도"]))
                해.setdefault(열, dict({k: _api값(h.get("list") or [], k) for k in _API}, **_기타모으기(h.get("list") or []),
                                     _묶음=_묶음키(h.get("list") or []), _CAPEX구성=_CAPEX구성(h.get("list") or [])))
                # 비용 줄을 음수로 적은 해가 있다(같은 회사도 해마다 부호가 다르다) — 크기로 읽는다.
                # **해마다** 고친다(2026-10-16, S1 리뷰 — 종전에는 이 줄이 해 고리 밖에 있어 마지막 해만 고쳐졌다.
                # 실측 NAVER 2022: 영업비용 −6.9조가 그대로 남아 재고 −0.46일 · 매입채무 −65.7일이 나갔다)
                for k in ("매출원가", "판관비") + _API흐름:
                    if 해[열].get(k) is not None:
                        해[열][k] = abs(해[열][k])
        for p in glob.glob(os.path.join(폴더, "dart_기업개황.json")):
            try:
                est = (json.load(io.open(p, encoding="utf-8")).get("est_dt") or "").strip()
                if len(est) == 8 and est.isdigit():
                    모.설립일 = datetime.date(int(est[:4]), int(est[4:6]), int(est[6:]))
            except (OSError, ValueError):
                pass
        for p in glob.glob(os.path.join(폴더, "dart_재무_연결_*_*.json")):
            m = re.search(r"_(\d{4})_(\d{5})\.json$", p)
            if not m or m.group(2) == "11011":
                continue
            개월 = {"11012": 6, "11013": 3, "11014": 9}[m.group(2)]
            열 = 기간ID(누계실적, int(m.group(1)), 개월)
            목록 = json.load(io.open(p, encoding="utf-8")).get("list") or []
            해.setdefault(열, dict({k: _api값(목록, k, 누계=True) for k in _API}, _개월=개월, _묶음=_묶음키(목록, 누계=True),
                                 _CAPEX구성=_CAPEX구성(목록, 누계=True), **_기타모으기(목록, 누계=True)))
            for k in ("매출원가", "판관비") + _API흐름:
                if 해[열].get(k) is not None:
                    해[열][k] = abs(해[열][k])
    # 「유형자산의 취득」 한 줄이 없고 자산군별 취득 줄만 있는 해 — 그 합을 CAPEX 로(FX-A · F18). 출처 표지 `_CAPEX출처`
    for 열, v in 해.items():
        군 = ((v.get("_CAPEX구성") or {}).get("자산군별") or {})
        if v.get("CAPEX") is None and 군:
            v["CAPEX"] = sum(군.values())
            v["_CAPEX출처"] = "자산군별 취득 줄의 합(%s)" % " · ".join(sorted(군))
    return 해


def 범위제외해(해, 모):
    """회전일수 · 국면 범위에서 뺄 해 — (2026-10-16, S1 리뷰 · 결정 6 「회전일수는 실적 범위에서」의 범위 끝을 이상치가 정하지 않게)
      ① 항등식이 어긋난 해 — 매출 − 매출원가 − 판관비(단일 표시면 영업비용) ≠ 영업이익(매출의 1% 넘게)
      ② 부분 연도 — 기업개황 설립일(분할 · 신설)이 그 해 1월 2일 뒤면 그 해 손익은 열두 달이 아니다
      ③ 구조 단절 후보 — 매출이 이듬해의 1/3 미만(부분 연도 · 처분 전)이면 그 해
    빼는 해는 `모.주의` 와 `모.구조단절` 에 적는다(끊을지는 사람이 정한다 — 도구는 범위에서만 뺀다)."""
    제외, 글 = set(), []
    fy = sorted(c for c in 해 if c.startswith("FY"))
    for c in fy:
        v = 해[c]
        매, 원, 판, 영 = v.get("매출"), v.get("매출원가"), v.get("판관비"), v.get("영업이익")
        if 매 and 판 is not None and 영 is not None and abs(매 - (원 or 0.0) - 판 - 영) > abs(매) * 0.01:
            제외.add(c)
            글.append(("%s 매출원가가 비었는데 판관비만으로 영업이익이 안 닫힌다(차 매출의 %.1f%%) — 회전일수 분모 불명" if 원 is None
                      else "%s 항등식 어긋남(차 매출의 %.1f%%)") % (c, (매 - (원 or 0.0) - 판 - 영) / 매 * 100))
    설립 = getattr(모, "설립일", None)
    if 설립 and (설립.month, 설립.day) > (1, 2):
        c = 기간ID(FY실적, 설립.year)
        if c in 해:
            제외.add(c)
            글.append("%s 부분 연도(설립 · 분할 %s)" % (c, 설립.isoformat()))
    for a, b in zip(fy, fy[1:]):
        x, y = (해[a] or {}).get("매출"), (해[b] or {}).get("매출")
        if x and y and x > 0 and y / x > 3.0 and a not in 제외:
            제외.add(a)
            글.append("%s 매출이 이듬해의 1/%.1f — 구조 단절 후보(부분 연도 · 분할 · 처분)" % (a, y / x))
    if 글:
        모.구조단절 = 글
        모.주의.append("회전일수 · 국면 범위에서 뺀 해: %s — 앵커 표를 구조 블록으로 끊을지는 사람이 정한다" % " · ".join(글))
    return 제외


def 램프업해(해, 제외=()):
    """초기 적자 램프업 해 — 앞쪽부터 이어진 영업적자 해이고, 그 뒤에 흑자 해가 셋 이상 이어지며, 그 적자 구간의 매출이 해마다 20% 넘게 컸다.
    회전일수 · 국면 범위에서 「구조 단절 후보(초기 램프업)」로 뺀다(S6-01 — 실측 Tesla FY2009~2019 적자 성장기의 재고일수 191.7 이 비관 재료가 됐다).
    끊을지는 사람이 정한다."""
    fy = [c for c in sorted((c for c in 해 if c.startswith("FY")), key=_열때) if c not in 제외]
    률 = {c: (해[c].get("영업이익") / 해[c]["매출"]) for c in fy if 해[c].get("매출") and 해[c].get("영업이익") is not None}
    fy = [c for c in fy if c in 률]
    k = 0
    while k < len(fy) and 률[fy[k]] < 0:
        k += 1
    if k == 0 or k > len(fy) - 3 or not all(률[c] >= 0 for c in fy[k:k + 3]):
        return []
    성 = [해[b]["매출"] / 해[a]["매출"] - 1 for a, b in zip(fy[:k + 1], fy[1:k + 1]) if 해[a].get("매출")]
    if not 성 or sorted(성)[len(성) // 2] <= 0.20:
        return []
    return fy[:k]


def 회전일수(해, 모, 출처):
    """기말 잔액 ÷ 기간 금액 × 365(누계는 × 12 ÷ 개월로 연환산) — 매출채권 ÷ 매출 · 재고 ÷ 매출원가 · 매입채무 ÷ 매출원가.
    매출원가가 없는 회사(영업수익 · 영업비용 단일 표시)는 재고 · 매입채무를 영업비용(판관비 칸)으로 잰다 — 그 사실을 `주의` 에.
    선수금 · 계약부채 · 계약자산은 매출 대비 비율(연환산 매출).
    S6 — `_매출연`(연환산 매출 · 국면 재료) · `기타순운전자본비율`(엔진 190 의 자 — 13번 14 + 15 − 35 − 36 − 40 − 43 ÷ 연환산 매출) ·
    `미지급비용회전일수`(미지급 비용 ÷ 판관비(단일 표시면 영업비용) × 365 — 서비스 · SaaS 의 운전자본 몫, 엔진 190 안의 대조) ·
    `_묶음`(매출채권 · 매입채무를 묶음 태그로 잡은 열) · 잔액(E 가 엔진의 회전 기준으로 다시 잰다) · 법인세 재료(S6-07)."""
    낸 = {}
    단일 = False
    제외 = 범위제외해(해, 모)
    램프 = 램프업해(해, 제외)
    if 램프:
        글 = "%s~%s 초기 적자 램프업(그 뒤 흑자 셋 이상 · 적자 구간 매출 성장 중앙값 20%% 넘음) — 구조 단절 후보" % (램프[0], 램프[-1])
        모.구조단절.append(글)
        모.주의.append("회전일수 · 국면 범위에서 뺀 해: %s — 끊을지는 사람이 정한다" % 글)
        제외 = set(제외) | set(램프)
    for 열, v in sorted(해.items()):
        년 = (v.get("_개월") or 12) / 12.0
        if 열 in 제외:
            continue
        매, 원 = v.get("매출"), v.get("매출원가")
        if not 원 and v.get("판관비") and 매:
            원, 단일 = v.get("판관비"), True
        d = {}
        if 매:
            d["_매출연"] = 매 / 년 / 단위배[모.단위]
        if 매 and v.get("매출채권") is not None:
            d["매출채권"] = v["매출채권"] / (매 / 년) * 365
        if 원 and v.get("재고"):
            d["재고자산"] = v["재고"] / (원 / 년) * 365
        if 원 and v.get("매입채무") is not None:
            d["매입채무"] = v["매입채무"] / (원 / 년) * 365
        if 매 and v.get("영업이익") is not None:
            d["영업이익률"] = v["영업이익"] / 매
        if 매 and v.get("매출원가") is not None:
            d["매출총이익률"] = (매 - v["매출원가"]) / 매
        선 = (v.get("선수금") or 0.0) + (v.get("계약부채") or 0.0)
        if 매 and 선:
            d["선수금계약부채비율"] = 선 / (매 / 년)
        if 매 and v.get("계약자산"):
            d["계약자산비율"] = v["계약자산"] / (매 / 년)
        for k in ("선수금", "계약부채", "계약자산"):
            if v.get(k):
                d["_" + k] = v[k] / 단위배[모.단위]
        기 = [(v.get("_13_%d" % 행), 부) for 행, 부 in 기타행부호]
        if 매 and any(x is not None for x, _ in 기):
            d["기타순운전자본비율"] = sum((x or 0.0) * 부 for x, 부 in 기) / (매 / 년)
            d["_기타행"] = {"%d" % 행: round((x or 0.0) / 단위배[모.단위], 6) for (x, _), (행, _부) in zip(기, 기타행부호) if x is not None}
        판 = v.get("판관비") or ((매 - (v.get("매출원가") or 0.0) - v["영업이익"]) if (매 and v.get("영업이익") is not None) else None)
        if 판 and 판 > 0 and v.get("미지급비용"):
            d["미지급비용회전일수"] = v["미지급비용"] / (판 / 년) * 365
        for k, 키 in (("재고", "_재고잔액"), ("매입채무", "_매입채무잔액"), ("매출채권", "_매출채권잔액")):
            if v.get(k) is not None:
                d[키] = v[k] / 단위배[모.단위]
        if 매 and v.get("재고") is not None:
            d["_재고매출비"] = v["재고"] / (매 / 년)
        if v.get("_묶음"):
            d["_묶음"] = list(v["_묶음"])
        # 법인세 재료(S6-07) — 실효세율 · 현금유효세율(세전이익 대비) · 잔액(이연법인세 · 결손금 · 평가충당금 · 공제)
        세전, 세비 = v.get("세전이익"), v.get("법인세비용")
        if 세전 and 세비 is not None:
            d["_실효세율"] = 세비 / 세전
        if 세전 and v.get("법인세납부") is not None:
            d["_현금유효세율"] = v["법인세납부"] / 세전
        for k in ("세전이익", "법인세비용", "법인세납부", "이연법인세자산", "이연법인세부채", "이월결손금", "평가충당금", "미인식세무효익",
                  "이월세액공제", "연구개발공제이월", "공제_연구개발", "공제_합계", "공제_외국세율차", "공제_주세", "공제_FDII"):
            if v.get(k) is not None:
                d["_세_" + k] = v[k] / 단위배[모.단위]
        if v.get("실효세율공시") is not None:
            d["_세_실효세율공시"] = v["실효세율공시"]
        # 회전일수가 음수이거나 한 해(365일)를 넘으면 산식 재료가 이상한 해다 — 범위에 넣지 않는다(확인 불가)
        for k in ("매출채권", "재고자산", "매입채무", "미지급비용회전일수"):
            if k in d and not (0 <= d[k] <= 365):
                모.이상회전.append("%s %s %.1f일" % (열, k, d[k]))
                del d[k]
        if d:
            낸[열] = d
    if 모.이상회전:
        모.주의.append("회전일수가 음수이거나 365일을 넘는 칸은 범위에서 뺐다(확인 불가 — 산식 재료 이상): %s" % " · ".join(모.이상회전))
    모.회전 = 낸
    모.회전출처 = 출처
    모.단일회전 = 단일
    if 단일:
        모.주의.append("매출원가가 없는 기간은 재고 · 매입채무 회전일수를 영업비용 기준으로 쟀다(영업수익 · 영업비용 단일 표시)")


def 회전기준별(모):
    """S6-03 — 엔진의 회전 기준(`구조.운전자본.재고회전기준` · `매입채무회전기준`)마다 실적 회전일수를 낸다.
      재고자산  매출원가(종전 칸) · 발생원가 = 성격별 줄 합(재고 변동 · 대체 뺌 — 엔진 5번 161 의 자: 원가 줄 + 인건비 + 상각)
               · 발생원가_성과급뺌 = 발생원가 − 성과급율 × max(영업이익, 0)(A3 `성과급율` 이 있을 때 — 엔진은 인건비 산정이 인원이면 성과급 뺀 7번 34 를 읽는다)
      매입채무  매출원가(종전 칸) · 재료비및경비 = 성격별 원가 줄(인건비 · 상각 · 재고 변동 · 대체 뺌 — 엔진 9번 113 의 자)
    성격별 표가 없는 해는 칸을 두지 않는다(본선이 「확인 불가 — 그 해 사업보고서 성격별 주석」으로 적는다)."""
    낸 = {"재고자산": {"발생원가": {}, "발생원가_성과급뺌": {}}, "매입채무": {"재료비및경비": {}}}
    액 = {"발생원가": {}, "재료비및경비": {}}
    율 = getattr(모, "성과급율값", None)
    for 열, 표 in 모.성격별.items():
        d = 모.회전.get(열) or {}
        u = 단위배.get(표.get("단위"), 1.0) / 단위배[모.단위]
        발 = 재 = 0.0
        for _l, x, _항, 키 in 표["줄"]:
            if x is None or 키 in ("재고변동", "대체"):
                continue
            발 += x * u
            if 키 not in ("인건비", "복리후생", "주식보상", "상각"):
                재 += x * u
        년 = 12.0 / _열때(열)[1] if not 열.startswith("FY") and _열때(열)[1] else 1.0
        if 발 > 0:
            액["발생원가"][열] = round(발 * 년, 6)
        if 재 > 0:
            액["재료비및경비"][열] = round(재 * 년, 6)
        if 발 > 0 and d.get("_재고잔액") is not None:
            낸["재고자산"]["발생원가"][열] = d["_재고잔액"] / (발 * 년) * 365
            영 = (d.get("영업이익률") or 0.0) * (d.get("_매출연") or 0.0)
            if 율 and 영 is not None:
                낸["재고자산"]["발생원가_성과급뺌"][열] = d["_재고잔액"] / (발 * 년 - 율 * max(영, 0.0)) * 365
        if 재 > 0 and d.get("_매입채무잔액") is not None:
            낸["매입채무"]["재료비및경비"][열] = d["_매입채무잔액"] / (재 * 년) * 365
    for k in 낸:
        for j in list(낸[k]):
            낸[k][j] = {c: round(v, 4) for c, v in sorted(낸[k][j].items(), key=lambda t: _열때(t[0])) if 0 <= v <= 365} or None
            if 낸[k][j] is None:
                del 낸[k][j]
    낸["기준액"] = {k: dict(sorted(v.items(), key=lambda t: _열때(t[0]))) for k, v in 액.items() if v}
    return 낸


def API대조(해, 모):
    """성격별 합계 = 매출원가 + 판관비(단일 표시 회사는 영업비용) — 해마다."""
    for 열, 표 in 모.성격별.items():
        a = 해.get(열) or {}
        if 표.get("합계") is None or a.get("판관비") is None:
            continue
        u = 표["단위"]
        좌 = 표["합계"] * 단위배.get(u, 1.0)
        우 = (a.get("매출원가") or 0.0) + a["판관비"]
        모.합계검산[열] = {"성격별합계": 좌 / 단위배[모.단위], "원가와판관": 우 / 단위배[모.단위], "차이": (좌 - 우) / 단위배[모.단위]}
        if abs(좌 - 우) > 단위배.get(u, 1.0):
            모.주의.append("성격별 합계 ≠ 매출원가 + 판관비 — %s 차이 %s" % (열, "{:,.1f}".format((좌 - 우) / 단위배[모.단위])))


# ────────────────────────────────────────────────────────────── 미국 — companyfacts

미국태그 = {
    "579": ("DepreciationDepletionAndAmortization", "DepreciationAmortizationAndAccretionNet", "DepreciationAndAmortization"),
    "546": ("ShareBasedCompensation", "AllocatedShareBasedCompensationExpense"),
    "536": ("ResearchAndDevelopmentExpense", "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost"),
    "567": ("ConstructionInProgressGross",),
    "531": ("LaborAndRelatedExpense",),
}
미국기능별 = {"매출원가": ("CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold"),
          "연구개발": ("ResearchAndDevelopmentExpense", "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost"),
          "판매및마케팅": ("SellingAndMarketingExpense", "MarketingAndAdvertisingExpense"),
          "일반관리": ("GeneralAndAdministrativeExpense",), "판관비합계": ("SellingGeneralAndAdministrativeExpense",)}
미국자산태그 = {"기계장치": ("MachineryAndEquipmentGross",), "건물": ("BuildingsAndImprovementsGross",),
            "토지": ("LandAndLandImprovements", "Land"), "건설중": ("ConstructionInProgressGross",),
            "합계": ("PropertyPlantAndEquipmentGross",)}
미국회전 = {"매출": ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"),
          "매출원가": ("CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold"),
          "매출채권": ("AccountsReceivableNetCurrent", "ReceivablesNetCurrent"), "재고": ("InventoryNet",),
          "매입채무": ("AccountsPayableCurrent",), "영업이익": ("OperatingIncomeLoss",),
          # S6-07 — 법인세 재료(세전이익 · 법인세비용 · 현금 납부 · 이연법인세 · 결손금 · 평가충당금 · 미인식 세무효익 · 공제)
          "세전이익": ("IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
                   "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"),
          "법인세비용": ("IncomeTaxExpenseBenefit",), "법인세납부": ("IncomeTaxesPaidNet", "IncomeTaxesPaid"),
          "유형자산": ("PropertyPlantAndEquipmentNet",
                   "PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetAfterAccumulatedDepreciationAndAmortization"),
          "계약부채": ("ContractWithCustomerLiabilityCurrent", "DeferredRevenueCurrent"),
          "계약자산": ("ContractWithCustomerAssetNetCurrent",),
          "CAPEX": ("PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"),
          "무형취득": ("PaymentsToAcquireIntangibleAssets",),
          "사업결합취득": ("PaymentsToAcquireBusinessesNetOfCashAcquired", "PaymentsToAcquireBusinessesGross")}
미국운영 = {   # 운영 지표 — 태그 이름 정규식(모든 네임스페이스 · 회사 확장 태그 포함)
    "매장수": r"^NumberOf(Stores|Restaurants|Locations|Retail\w*|Units\w*Operat\w*|Clubs|Warehouses)$",
    "면적": r"^(AreaOfRealEstateProperty|NetRentableArea\w*|\w*SquareFeet\w*)$",
    "사용자수": r"^(NumberOf\w*(Users|Members|Customers)\w*|MonthlyActiveUsers\w*|DailyActiveUsers\w*)$",
    "가입자수": r"^(NumberOf\w*Subscri\w*|\w*PaidMemberships\w*|\w*Subscribers)$",
    "거래액": r"^(GrossMerchandiseVolume\w*|GrossBookings\w*|GrossOrderValue\w*|TotalPaymentVolume\w*)$",
    "주문건수": r"^(NumberOf\w*Orders\w*|\w*OrdersPlaced\w*)$",
    "수주잔고": r"^RevenueRemainingPerformanceObligation$",
    "좌석수": r"^NumberOf(Seats|Beds)$",
    "편대": r"^NumberOf(Aircraft\w*|Vessels|Ships|Railcars|Trucks)$",                       # S5-14 — 편대는 좌석과 따로
    "서버수": r"^NumberOf\w*Servers\w*$",
    "데이터센터용량": r"^\w*DataCenter\w*(Capacity|Megawatts?)\w*$",
    "회선수": r"^NumberOf\w*(Lines|Connections|Circuits)\w*$",
    "객실수": r"^NumberOf(Rooms|HotelRooms)$",
    "ARPU": r"^\w*AverageRevenuePer\w*$",
}


def _미국연간(cf, 태그들, 통화="USD", 흐름=True, 이름공간=("us-gaap", "dei")):
    """10-K 의 연간 값 {회계연도 끝 해: 값} — 흐름은 기간 ≈ 1년, 잔액은 시점. 같은 끝날은 늦게 낸 것.

    **후보 태그를 잇는다** — `sec_앵커.태그잇기` 와 같은 함수(2026-10-16, S1 리뷰). 종전에는 첫 태그에서 값이 나오면 바로 돌려줘
    회사가 태그를 갈아탄 해부터 통째로 비었다(실측 CRM: `CostOfRevenue` FY2008~2014 에서 멈춰 `CostOfGoodsAndServicesSold`
    FY2017~2026 을 안 읽음 → 기능별 매출원가 · 회전일수가 최근 12년 빈칸). 최근 해에 닿는 사슬을 씨앗으로, 겹치는 해의 값이
    0.5% 안에서 맞을 때만 옛 태그를 붙인다(겹치지 않거나 갈리면 안 잇는다 — 뜻이 다른 태그로 빈 해를 메우지 않는다)."""
    import sec_앵커                                           # noqa: PLC0415
    for ns in 이름공간:
        받은 = {}
        for t in 태그들:
            f = ((cf.get("facts") or {}).get(ns) or {}).get(t)
            if not f:
                continue
            낸 = {}
            for u, 목록 in (f.get("units") or {}).items():
                if ns == "us-gaap" and u not in (통화, "pure") and 흐름:
                    continue
                for x in 목록:
                    if x.get("form") not in ("10-K", "10-K/A", "20-F", "40-F"):
                        continue
                    if x.get("start"):
                        d = (datetime.date.fromisoformat(x["end"]) - datetime.date.fromisoformat(x["start"])).days
                        if not 흐름 or not 330 <= d <= 380:
                            continue
                    elif 흐름:
                        continue
                    y = int(x["end"][:4])
                    if y not in 낸 or x.get("filed", "") >= 낸[y][1]:
                        낸[y] = (float(x["val"]), x.get("filed", ""))
            if 낸:
                받은[t] = {"%04d" % y: v for y, v in 낸.items()}
        if 받은:
            채움, _이음, _단절 = sec_앵커.태그잇기(받은, list(태그들))
            쓴 = [t for t in 태그들 if any(v[0] == t for v in 채움.values())]
            return {int(k): v[1][0] for k, v in 채움.items()}, "%s:%s" % (ns, "+".join(쓴))
    return {}, None


# ────────────────────────────────────────────────────────────── 미국 — 10-K 본문(Item 1 · Human Capital · 수량 문장)
# companyfacts 에 없는 셋을 받아 둔 10-K 원문(sec_fetch 가 `_raw/10K_YYYYMM.htm` 으로 받는다)에서 읽는다 — 유형 판정의 낱말 ·
# 직원 수(Human Capital) · 인도 · 매장 · 사용자 같은 수량 문장. 문장에서 읽은 값은 「10-K 본문 문장」으로 출처를 달고 사람이 확인한다.

def _html벗기기(h):
    h = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?i)<br\s*/?>|</(p|div|tr|li|h\d)>", "\n", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    for a, b in (("&nbsp;", " "), ("&#160;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&#8217;", "'"), ("&#8212;", "-")):
        h = h.replace(a, b)
    return re.sub(r"[ \t]+", " ", h)


def 미국10K들(폴더):
    """폴더의 10-K 원문 — [(회계연도 끝 해, 경로)] 최근 먼저. 이름 꼴 `10K_YYYYMM` · `10K_YYYY`(.txt 가 있으면 .txt)."""
    낸 = {}
    for p in glob.glob(os.path.join(폴더, "10K_*.*")):
        m = re.match(r"10K_(\d{4})(\d{2})?\.(txt|htm|html)$", os.path.basename(p), re.I)
        if not m:
            continue
        y = int(m.group(1))
        if y not in 낸 or p.lower().endswith(".txt"):
            낸[y] = p
    return sorted(낸.items(), reverse=True)


def _10K글(p):
    글 = io.open(p, encoding="utf-8", errors="ignore").read()
    return _html벗기기(글) if p.lower().endswith((".htm", ".html")) else 글


def _항목1(글):
    """Item 1(Business) 본문 — 차례의 「Item 1.」 말고 본문의 것. FX-A R4(2026-10-25) — 머리 꼴(「Item 1. Business」 · 「ITEM 1: BUSINESS」 ·
    「Item 1 — Business」)마다 다음 「Item 1A」 까지의 구간을 재고 **가장 긴 구간**을 쓴다(종전엔 마지막 머리 하나 — 차례 머리를 고르면 몇 줄짜리
    구간이 나와 낱말이 0 이 됐다 · F3 · F38). 머리가 없으면 앞 20만 자."""
    머리 = [m.start() for m in re.finditer(r"(?i)item\s*1\s*[.:\-–—]?\s*\|?\s*business\b", 글)]
    if not 머리:
        return 글[:200000]
    best = ""
    for 시작 in 머리:
        m = re.search(r"(?i)item\s*1a\.", 글[시작 + 20:])
        if not m:
            continue                                      # 끝(Item 1A)이 없는 구간은 본문이 아니다(뒤쪽 교차 참조 — 재무제표까지 딸려 온다)
        조각 = 글[시작: 시작 + 20 + m.start()]
        if len(조각) > len(best):
            best = 조각
    if best:
        return best
    시작 = 머리[-1] if len(머리) > 1 else 머리[0]                  # 옛 길
    return 글[시작: 시작 + 200000]


_직원re = (re.compile(r"(?i)headcount[^.]{0,60}?(?:was|of|totaled)\s+(?:approximately\s+|about\s+)?(\d{1,3}(?:,\d{3})+|\d{4,})"),
          re.compile(r"(?i)as of [^.]{0,60}?(?:we|the company)\s+(?:had|employed)\s+(?:approximately\s+|about\s+|over\s+)?"
                     r"(\d{1,3}(?:,\d{3})+|\d{4,})\s+(?:full[- ]time\s+)?(?:employees|people|team members|associates)"),
          re.compile(r"(?i)(?:we|the company)\s+(?:had|employed)\s+(?:approximately\s+|about\s+|over\s+)?"
                     r"(\d{1,3}(?:,\d{3})+|\d{4,})\s+(?:full[- ]time\s+)?(?:employees|people|team members|associates)"))
_수량re = {   # 이름 → (정규식 · 단위) — 판매량 · 사업지표 문장(회사 이름 없이 일반 꼴)
    "판매량": (re.compile(r"(?i)\b(delivered|shipped|sold)\s+(?:approximately\s+|about\s+|over\s+)?([\d.,]+)\s*(million|thousand)?\s+"
                       r"(?:[a-z-]+\s+){0,2}(vehicles|units|cars|aircraft|homes|devices|systems)"), "대"),
    "생산량": (re.compile(r"(?i)\b(produced|manufactured)\s+(?:approximately\s+|about\s+|over\s+)?([\d.,]+)\s*(million|thousand)?\s+"
                       r"(?:[a-z-]+\s+){0,2}(vehicles|units|cars|aircraft|homes|devices|systems)"), "대"),
    "매장수": (re.compile(r"(?i)\b(operated|had|total of|operate)\s+(?:approximately\s+|about\s+|over\s+)?([\d.,]+)\s*(thousand)?\s+"
                       r"(?:[a-z-]+\s+){0,2}(stores|restaurants|warehouses|clubs|locations)"), "개"),
    "가입자수": (re.compile(r"(?i)\b(approximately|about|over|had|of)\s+([\d.,]+)\s*(million|billion|thousand)?\s+"
                        r"(paid\s+)?(subscribers|members|memberships|paying customers)"), "명"),
    "사용자수": (re.compile(r"(?i)\b(approximately|about|over|had|of)\s+([\d.,]+)\s*(million|billion|thousand)?\s+"
                        r"(monthly active users|daily active users|active users|MAUs|DAUs)"), "명"),
}
_배수 = {"million": 1e6, "billion": 1e9, "thousand": 1e3}
# 품목별 출하량 문장(2026-10-23 — 「<품목> shipment volume (in the United States) was 61.8 billion units in 2025」 · 품목이 여럿인 10-K 가 흔하다).
# 품목마다 한 줄로 낸다 — 단위 칸에 품목을 붙여 서로 다른 품목이 같은 단위로 더해지지 않게 한다(동인진단은 같은 단위의 판매량 공시를 더한다)
_출하re = re.compile(r"(?i)([A-Za-z’'&,\- ]{3,90}?)\bshipment volumes?(?:\s+in\s+the\s+[A-Z][A-Za-z.]+(?:\s+[A-Z][A-Za-z.]+){0,2})?\s+"
                    r"(?:was|were|of|totaled)\s+(?:approximately\s+|about\s+)?([\d.,]+)\s*(billion|million|thousand)?\s+"
                    r"(units|sticks|cans|cartons|cases|vehicles|devices|tons|barrels|gallons)\s+in\s+(\d{4})")


def _문장조각(글, m):
    return 글[max(0, m.start() - 40): m.end() + 10].replace("\n", " ").strip()[:160]


_미국연수re = re.compile(r"(?i)([A-Z][A-Za-z,&/\- ]{2,60}?)\s*[|:]?\s*(\d{1,2})\s*(?:to|-|–|—)\s*(\d{1,2})\s*years|"
                       r"([A-Z][A-Za-z,&/\- ]{2,60}?)\s*[|:]?\s*(\d{1,2})\s*years")


def _미국내용연수(글, 이름):
    """10-K 의 「estimated useful lives」 문단 · 표 — {"종류": {이름: [하, 상]}, "상각방법": [..], "출처"} 또는 None(S5-17)."""
    m = re.search(r"(?i)estimated useful li(?:fe|ves)", 글)
    while m:
        창 = 글[m.start(): m.start() + 2500]
        if re.search(r"(?i)property|equipment|buildings", 창):
            종류 = {}
            for x in _미국연수re.finditer(창):
                n = (x.group(1) or x.group(4) or "").strip(" ,|:-")
                n = re.sub(r"(?i)^(and|the|over|of|range|ranging|from)\s+", "", n)[-40:].strip()
                if not n or re.search(r"(?i)useful|estimated|lives|lease term|shorter", n):
                    continue
                lo, hi = (int(x.group(2)), int(x.group(3))) if x.group(2) else (int(x.group(5)), int(x.group(5)))
                if 0 < lo <= hi <= 60:
                    종류.setdefault(n, [lo, hi])
            if len(종류) >= 1:
                방법 = ["정액법"] if re.search(r"(?i)straight[- ]line", 창) else ["확인 불가"]
                return {"종류": 종류, "상각방법": 방법, "출처": "%s 「estimated useful lives」" % 이름}
        m = re.search(r"(?i)estimated useful li(?:fe|ves)", 글[m.end():]) and re.compile(r"(?i)estimated useful li(?:fe|ves)").search(글, m.end())
    return None


_유형합계라벨 = re.compile(r"(?i)^total\b|\bgross$|^property,?\s*(?:plant,?\s*)?(?:and\s*)?equipment(?:,?\s*at cost)?$")


def _표수(x):
    """10-K 표 칸 → 수(「20,864」 · 「( 20,173 )」 · 「—」 = 0). 수가 아니면 None."""
    t = ("%s" % x).replace(",", "").replace("$", "").strip()
    if t in ("—", "–", "-"):
        return 0.0
    m = re.fullmatch(r"\(\s*([\d.]+)\s*\)|([\d.]+)", t)
    if not m:
        return None
    return -float(m.group(1)) if m.group(1) else float(m.group(2))


def 유형종류(라):
    """PP&E 표 줄 이름 → 자산군 종류(미국자산태그 의 키 · 기타). 회사 이름 없이 줄 이름의 낱말로만."""
    l = 라.lower()
    if re.search(r"construction in pro(?:gress|cess)", l):
        return "건설중"
    if re.match(r"land\b", l) and not re.search(r"building", l):
        return "토지"
    if re.search(r"building|leasehold", l):
        return "건물"
    if re.search(r"machiner|equipment|tooling|vehicle|furniture|computer|hardware|software|infrastructure|fixture", l):
        return "기계장치"
    return "기타"


def 미국유형표(raw, 이름=""):
    """10-K PP&E 표(취득원가 구성 → 감가상각누계) → {"줄": [(라벨, [당기, 전기])], "합계": [..] · None, "배수", "출처"} 또는 None (2026-10-23).
    companyfacts 에 종류별 취득원가 태그가 없는 회사(실측 셋 모두)는 56g · 567 이 비었다 — 주석 표(또는 재무상태표 표면의 「… at cost」 구획)를 읽는다.
    「Construction in progress/process」 와 「accumulated depreciation」 이 함께 있는 첫 표 · 줄 합이 합계 줄과 1% 안일 때만 낸다."""
    import html as _html                                     # noqa: PLC0415
    for m in re.finditer(r"(?is)<table.*?</table>", raw or ""):
        tb = m.group(0)
        txt = _html.unescape(re.sub(r"<[^>]+>", " ", tb))
        if not (re.search(r"(?i)construction in pro(?:gress|cess)", txt) and re.search(r"(?i)accumulated depreciation", txt)):
            continue
        행들 = []
        for tr in re.findall(r"(?is)<tr.*?</tr>", tb):
            칸 = [re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", td))).strip() for td in re.findall(r"(?is)<t[dh].*?</t[dh]>", tr)]
            칸 = [x for x in 칸 if x and x not in ("$", ")", "%")]
            if 칸:
                행들.append(칸)
        시작 = 0
        for i, r in enumerate(행들):                          # 재무상태표 표면 꼴 — 「Property, plant and equipment, at cost:」 머리 뒤부터
            if re.search(r"(?i)at cost", r[0]) and re.search(r"(?i)property|equipment", r[0]):
                시작 = i + 1
        줄, 합 = [], None
        for r in 행들[시작:]:
            if re.search(r"(?i)accumulated depreciation", r[0]):
                break
            수 = [_표수(x) for x in r[1:3]]
            if len(r) < 3 or any(v is None for v in 수):
                continue
            if _유형합계라벨.search(r[0].strip(" :")):
                합 = 수
                continue
            줄.append((r[0], 수))
        if not any(유형종류(l) == "건설중" for l, _ in 줄):
            continue
        if 합 and any(abs(sum(v[j] for _, v in 줄) - 합[j]) > 0.01 * abs(합[j]) for j in (0, 1) if 합[j]):
            return {"줄": [], "합계": 합, "배수": None, "출처": 이름, "주의": "PP&E 표의 줄 합이 합계 줄과 1% 넘게 다르다 — 쓰지 않는다(구획을 잘못 잡았을 수 있다)"}
        배수 = 1e3 if re.search(r"(?i)in thousands", txt) else 1e6        # 10-K 표는 대개 「in millions」 — 표 안에 다른 단위가 적혔으면 그것
        return {"줄": 줄, "합계": 합, "배수": 배수, "출처": "%s PP&E 표(%d줄 · 합계 %s)" % (이름, len(줄), "있음" if 합 else "없음")}
    return None


def 미국본문읽기(폴더):
    """→ {"유형점수": {}, "출처": 경로, "직원": {해: 값}, "직원출처": {해: 글}, "수량": {이름: [{해, 값, 단위, 문장}]}} — 10-K 가 없으면 None."""
    파일들 = 미국10K들(폴더)
    if not 파일들:
        return None
    낸 = {"직원": {}, "직원출처": {}, "수량": {}, "유형점수": {}, "출처": 파일들[0][1], "읽은": []}
    for k, (y, p) in enumerate(파일들):
        글 = _10K글(p)
        낸["읽은"].append(os.path.basename(p))
        if k == 0:
            본 = _항목1(글)
            낸["유형점수"] = 유형점수(본, 미국유형낱말, 미국낱말맥락제외)
            낸["_항목1"] = 본
            낸["_신호글"] = _항목1부터2(글) or 본          # FX2-A R4 — 외주 · 합작 문장은 Item 1 ~ Item 2 전체에서 찾는다
        if k == 0:                                     # S5-17 — 유형자산 estimated useful lives(가장 최근 10-K)
            낸["내용연수"] = _미국내용연수(글, os.path.basename(p))
            # PP&E 표는 원문 표(htm)에서 읽는다 — .txt 를 먼저 고른 해라도 같은 해의 .htm 이 곁에 있으면 그것(2026-10-23)
            htm = next(iter(sorted(glob.glob(os.path.join(os.path.dirname(p), "10K_%d*.htm" % y)))), None) or (p if p.lower().endswith((".htm", ".html")) else None)
            if htm:
                표 = 미국유형표(io.open(htm, encoding="utf-8", errors="ignore").read(), os.path.basename(htm))
                if 표:
                    표["해"] = y
                    낸["유형표"] = 표
        # 인원 문장은 「Human Capital」 절에 있지만 그 낱말이 앞쪽(차례 · 위험 요인)에 먼저 나오는 10-K 가 있다 — 첫 자리 뒤 6,000자만 보면 놓친다
        # (실측 2026-10-23: 「Employees and Labor Relations — we employed approximately N people」 을 놓쳐 541 이 비었다). 인원 절 머리가 나오는
        # 자리마다 창을 열고(앞에서부터) 그래도 없으면 전문을 본다 — 창마다 같은 정규식 차례
        창들 = [글[x.start(): x.start() + 6000] for x in re.finditer(
            r"(?i)human capital|employees and labor relations|\bour employees\b|\bemployees\s*(?:\||:)", 글)] + [글]
        for 창 in 창들:
            m = next((r.search(창) for r in _직원re if r.search(창)), None)
            if m:
                낸["직원"][y] = float(m.group(1).replace(",", ""))
                낸["직원출처"][y] = "%s 「%s」" % (os.path.basename(p), _문장조각(창, m))
                break
        for 이름, (r, u) in _수량re.items():
            m = r.search(글)
            if not m:
                continue
            try:
                v = float(m.group(2).replace(",", "")) * _배수.get((m.group(3) or "").lower(), 1.0)
            except ValueError:
                continue
            낸["수량"].setdefault(이름, []).append({"해": y, "값": v, "단위": u,
                                                  "문장": "%s 「%s」" % (os.path.basename(p), _문장조각(글, m))})
        for m in _출하re.finditer(글):
            품 = re.sub(r"(?i)^(?:.*\b(?:the|and|our|total)\s+)", "", m.group(1)).strip(" ,’'-") or "품목"
            품 = re.sub(r"(?i)^.*\bsegment[’']s\s+", "", 품)                               # 「○○ segment’s cigarettes」 → cigarettes
            품 = re.sub(r"(?i)(?:\s*(?:segment|products?)[’']?s?)+\s*$", "", 품).strip() or 품
            try:
                v = float(m.group(2).replace(",", "")) * _배수.get((m.group(3) or "").lower(), 1.0)
            except ValueError:
                continue
            해 = int(m.group(5)) if m.group(5) else y
            if any(z["해"] == 해 for z in 낸.setdefault("출하", {}).get(품, [])):
                continue
            낸["출하"].setdefault(품, []).append({"해": 해, "값": v, "단위": "%s(%s)" % (m.group(4).lower(), 품),
                                                "문장": "%s 「%s」" % (os.path.basename(p), _문장조각(글, m))})
    return 낸


def 미국원천불러오기(폴더들):
    """FX-C 의 `_raw/미국원천.json`(계약 4-2 — 형식 「미국원천/1」) — 있으면 (자료, 경로), 없으면 (None, None). 옛 회차는 없다(그때는 10K_* 를 직접 읽는다)."""
    for 폴더 in 폴더들:
        p = os.path.join(폴더, "미국원천.json")
        if os.path.exists(p):
            try:
                d = json.load(io.open(p, encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if isinstance(d, dict):
                return d, p
    return None, None


def _파일날(파일):
    """FX2-A R14 — 원문 파일 이름의 날짜(「6K_20260811_1.htm」 → 2026-08-11). 없으면 None. 미국원천 공시 목록에 제출일이 빈 6-K 꼴."""
    m = re.search(r"(20\d{2})(\d{2})(\d{2})", 파일 or "")
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
    except ValueError:
        return None


def _미국역할(x):
    """FX2-A R14 — 미국원천 공시 한 줄의 역할(기준일분기 · 직전 · 연차 · 뒤). FX-C 의 `기준일과` 를 따르되, 기준일분기 · 뒤가 아닌 연차 양식(10-K · 20-F)은 「연차」."""
    역 = x.get("기준일과") or ""
    if 역 in ("기준일분기", "뒤"):
        return 역
    if re.match(r"(10-K|20-F|40-F)", x.get("양식") or ""):
        return "연차"
    return 역 or "직전"


def _접수날(접수):
    """국내 접수번호(「20260814003665」)의 앞 8자리 → 제출일 「2026-08-14」. 꼴이 아니면 None."""
    m = re.match(r"(20\d{2})(\d{2})(\d{2})\d*$", 접수 or "")
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
    except ValueError:
        return None


def 역할매기기(원문읽음, 평가일):
    """FX2-A R14 — 국내 원문읽음 줄마다 `역할`(기준일분기 · 직전 · 연차 · 뒤 · 이전)을 단다(제자리). 기간 끝이 기준일 뒤 = 뒤, 같으면 기준일분기,
    기준일 앞의 사업보고서 = 연차, 기준일 앞의 반기 · 분기 가운데 가장 늦은 것 = 직전, 나머지 = 이전. 기준일이 없으면 기간 끝만으로(가장 늦은 것 = 기준일분기)."""
    끝들 = [x.get("기간끝") for x in 원문읽음 if x.get("기간끝")]
    기준 = 평가일 or (max(끝들) if 끝들 else "")
    중간 = sorted((x.get("기간끝") for x in 원문읽음 if x.get("기간끝") and x["기간끝"] < 기준 and x.get("종류") in ("반기", "분기")), reverse=True)
    직전끝 = 중간[0] if 중간 else None
    for x in 원문읽음:
        끝 = x.get("기간끝") or ""
        if not 끝 or not 기준:
            x["역할"] = "이전"
        elif 끝 > 기준:
            x["역할"] = "뒤"
        elif 끝 == 기준:
            x["역할"] = "기준일분기"
        elif x.get("종류") == "사업":
            x["역할"] = "연차"
        elif 끝 == 직전끝:
            x["역할"] = "직전"
        else:
            x["역할"] = "이전"
    return 원문읽음


def 출처시점고르기(원문읽음, 평가일):
    """FX2-A R14 — 출처 시점 대표값 → {"기간끝", "제출일", "접수", "종류", "근거", "뒤뺌"} | None. 「뒤」 역할(기준일 뒤 기간 · 기준일 뒤 첫 공시)은 뺀다 —
    값은 기준일 보고서로 냈는데 「뒤」 원문의 제출일이 대표가 되면 「조사 시점 뒤만 잇는다」 의 잣대가 흔들린다(R-run R14).
    차례: ① 역할 기준일분기(국내 정정판보다 원본 · 같은 기간이면 늦게 낸 것) ② 없으면 기준일 이전 원문 가운데 기간 끝이 가장 늦은 것."""
    쓸 = [x for x in 원문읽음 if x.get("역할") != "뒤" and x.get("기간끝") and (not 평가일 or x.get("역할") == "기준일분기" or x["기간끝"] <= 평가일)]
    뒤뺌 = sum(1 for x in 원문읽음 if x.get("역할") == "뒤")
    if not 쓸:
        return None
    기준 = [x for x in 쓸 if x.get("역할") == "기준일분기" or x.get("기준일보고서")]
    고를 = 기준 or 쓸
    근 = "기준일 보고서" if 기준 else "기준일 이전 가장 늦은 원문"
    x = max(고를, key=lambda y: (y["기간끝"], not y.get("정정"), y.get("제출일") or ""))
    return {"기간끝": x["기간끝"], "제출일": x.get("제출일"), "접수": x.get("접수"), "종류": x.get("종류"), "근거": 근, "뒤뺌": 뒤뺌}


def _인원해(미원):
    """FX2-A R5 — 미국원천 `인원` 의 회계연도 → (해 · None, 근거 글). ① 인원.기준일 ② 출처 파일 이름의 결산월(10K_YYYYMM · 20F_YYYYMM)
    ③ 미국원천 공시 목록에서 기준일 뒤가 아닌 가장 늦은 연차 보고서의 기간 끝."""
    인 = 미원.get("인원") or {}
    d = ("%s" % (인.get("기준일") or ""))[:4]
    if d.isdigit():
        return int(d), "인원 기준일"
    m = re.search(r"(?:10K|20F|40F)_(20\d{2})(\d{2})?", 인.get("출처") or "")
    if m:
        return int(m.group(1)), "출처 파일 결산월"
    연 = [x for x in (미원.get("공시") or []) if isinstance(x, dict) and re.match(r"(10-K|20-F|40-F)", x.get("양식") or "")
         and x.get("기준일과") != "뒤" and x.get("기간끝")]
    if 연:
        끝 = max(x["기간끝"] for x in 연)
        return int(끝[:4]), "공시 목록 연차 보고서 기간 끝 %s" % 끝
    return None, ""


def _ifrs재무지문(cf):
    """FX2-A R4 — companyfacts `ifrs-full` 연차(20-F · 40-F) 값으로 재무 지문 {유형자산÷매출, 재고÷매출}. 매출은 1년 기간 값만. 없으면 {}."""
    ifr = ((cf or {}).get("facts") or {}).get("ifrs-full") or {}

    def 최근(태그들, 흐름):
        for t in 태그들:
            f = ifr.get(t)
            if not f:
                continue
            값 = []
            for _u, 목록 in (f.get("units") or {}).items():
                for v in 목록:
                    if not isinstance(v.get("val"), (int, float)) or not v.get("end"):
                        continue
                    if v.get("form") and not re.match(r"(20-F|40-F|10-K)", v["form"]):
                        continue
                    if 흐름:
                        try:
                            일 = (datetime.date.fromisoformat(v["end"]) - datetime.date.fromisoformat(v.get("start") or v["end"])).days
                        except ValueError:
                            continue
                        if 일 < 300:
                            continue
                    값.append((v["end"], v.get("filed") or "", float(v["val"])))
            if 값:
                return max(값)
        return None
    매 = 최근(("Revenue", "RevenueFromContractsWithCustomers"), True)
    유 = 최근(("PropertyPlantAndEquipment",), False)
    재 = 최근(("Inventories",), False)
    if not 매 or not 매[2] or not 유:
        return {}
    return {"유형자산÷매출": 유[2] / 매[2], "재고÷매출": ((재[2] if 재 else 0.0) / 매[2])}


def _지분법투자(cf):
    """FX2-A R2 — 지분법 투자 자산(원 통화) — us-gaap EquityMethodInvestments · ifrs-full InvestmentsAccountedForUsingEquityMethod 의 가장 늦은 값. 없으면 None.
    합작 몫 대용치 재료(F 가 합작 몫 CAPEX 곁 칸 근거로 읽는다 — J2). 엔진 값으로 쓰지 않는다."""
    facts = (cf or {}).get("facts") or {}
    for 공간, 태그 in (("us-gaap", "EquityMethodInvestments"), ("us-gaap", "EquityMethodInvestmentsFairValueDisclosure"),
                    ("ifrs-full", "InvestmentsAccountedForUsingEquityMethod")):
        f = (facts.get(공간) or {}).get(태그)
        if not f:
            continue
        값 = [(v["end"], v.get("filed") or "", float(v["val"])) for 목록 in (f.get("units") or {}).values() for v in 목록
             if isinstance(v.get("val"), (int, float)) and v.get("end")]
        if 값:
            return max(값)[2]
    return None


def _항목1부터2(글):
    """FX2-A R4 — 10-K 의 Item 1 머리부터 Item 3(Legal Proceedings) 앞까지(Item 1 · 1A · 1B · 1C · 2) — 외주 · 합작 공급 문장은 위험 요인 · 설비 절에
    많다(「manufactured by outsourcing partners」 가 Item 1 이 아니라 1A 에 있는 꼴). 머리를 못 찾으면 빈 글(그때는 Item 1 만 쓴다). 상한 50만 자."""
    머리 = [m.start() for m in re.finditer(r"(?i)item\s*1\s*[.:\-–—]?\s*\|?\s*business\b", 글)]
    best = ""
    for 시작 in 머리:
        m = re.search(r"(?i)item\s*3\s*[.:\-–—]?\s*\|?\s*legal\s+proceedings", 글[시작 + 20:])
        if not m:
            continue
        조각 = 글[시작: 시작 + 20 + m.start()]
        if len(조각) > len(best):
            best = 조각
    return best[:500000]


def _미국RPO(cf, 미원=None):
    """RPO(잔여 이행 의무) — 미국원천.json 의 `RPO.값` 이 먼저, 없으면 companyfacts RevenueRemainingPerformanceObligation 의 가장 늦은 값. 없으면 None."""
    x = ((미원 or {}).get("RPO") or {}).get("값")
    if isinstance(x, (int, float)) and x > 0:
        return float(x)
    f = (((cf or {}).get("facts") or {}).get("us-gaap") or {}).get("RevenueRemainingPerformanceObligation") or {}
    값 = [v for u in (f.get("units") or {}).values() for v in u if isinstance(v.get("val"), (int, float)) and v.get("end")]
    if not 값:
        return None
    return float(max(값, key=lambda v: (v["end"], v.get("filed") or ""))["val"])


def _미국누계(cf, 태그들, 시작, 끝, 통화="USD"):
    """10-Q · 10-K 의 누계 값(start = 회계연도 첫날 · end = 기준일 — 분기 · 반기 · 9개월 YTD) → (값 · None, 태그). 같은 기간은 늦게 낸 것."""
    us = (cf.get("facts") or {}).get("us-gaap") or {}
    for t in 태그들:
        f = us.get(t)
        if not f:
            continue
        고른 = None
        for u, 목록 in (f.get("units") or {}).items():
            if u != 통화:
                continue
            for x in 목록:
                if x.get("form") not in ("10-Q", "10-Q/A", "10-K", "10-K/A") or not x.get("start"):
                    continue
                if x["start"] == 시작 and x["end"] == 끝 and (고른 is None or x.get("filed", "") >= 고른[1]):
                    고른 = (float(x["val"]), x.get("filed", ""))
        if 고른:
            return 고른[0], "us-gaap:%s" % t
    return None, None


미국기능대응 = {1: "매출원가", 5: "연구개발", 6: "판매및마케팅", 7: "일반관리"}     # E `기능별노드` 와 같은 대응(원가 줄 번호 → 기능 — 업종 아님)


def 미국기능별원천(cf, 모, 구, 배, 누계=None):
    """S10-21(손개입 개선 1 · 2026-10-18) — 성격별 주석이 없는 서식(미국 GAAP)은 **기능별 총액이 곧 원가 줄의 공시 실적**이다. 가정의 구조.원가줄 이
    기능별 넷(1 매출원가 · 5 연구개발 · 6 판매및마케팅 · 7 일반관리 — 6 이 없으면 판관비합계)으로 서 있으면 57k 를 companyfacts 에서 채운다 —
    연간은 10-K(`_미국연간`), 기준일 누계 열은 10-Q YTD(`_미국누계` — `누계` = (열 ID, 시작일, 끝날)). 종전에는 57k 가 전부 「확인 불가」로 남아
    본선이 손으로 옮겼다(S10 재리뷰 2 — 미국 회차 가정 조립 불가)."""
    번호들 = {x["번호"] for x in (구.get("원가줄") or [])}
    for x in (구.get("원가줄") or []):
        k = x["번호"]
        이름 = 미국기능대응.get(k)
        if not 이름:
            continue
        태그들 = 미국기능별[이름]
        v, 태그 = _미국연간(cf, 태그들)
        if 이름 == "일반관리" and 6 not in 번호들:                      # 원가 줄 6 이 없으면 7 = 판관비 전체(판관비합계 — S&M 을 따로 세우지 않은 구조)
            합, 태그합 = _미국연간(cf, 미국기능별["판관비합계"])
            if 합 and (not v or max(합) > max(v)):
                v, 태그, 태그들 = 합, 태그합, 미국기능별["판관비합계"]
        elif 이름 == "일반관리" and not v:                              # G&A 태그가 없으면 판관비합계 − 판매및마케팅
            합, 태그합 = _미국연간(cf, 미국기능별["판관비합계"])
            sm, _t = _미국연간(cf, 미국기능별["판매및마케팅"])
            if 합 and sm:
                v = {y: 합[y] - sm[y] for y in 합 if y in sm and 합[y] - sm[y] > 0}
                태그 = "%s − %s" % (태그합, _t)
        if not v:
            모.확인불가.setdefault("57%d" % k, "companyfacts 에 기능별 %s 태그(%s)가 없다 — 10-K 손익계산서에서 사람이 옮긴다" % (이름, " · ".join(태그들)))
            continue
        for y, val in v.items():
            모.넣기("57%d" % k, 기간ID(FY실적, y), val * 배 * 단위배[모.단위], "원",
                  "SEC companyfacts %s(10-K — 기능별 총액 = 원가 줄 %d %s)" % (태그, k, 이름), 3)
        if 누계 and 누계[0]:
            ID, 시작, 끝 = 누계
            val, 태그q = _미국누계(cf, 태그들, 시작, 끝)
            if val is None and 이름 == "일반관리" and 6 in 번호들:
                합, 태그합 = _미국누계(cf, 미국기능별["판관비합계"], 시작, 끝)
                sm, 태그sm = _미국누계(cf, 미국기능별["판매및마케팅"], 시작, 끝)
                if 합 is not None and sm is not None:
                    val, 태그q = 합 - sm, "%s − %s" % (태그합, 태그sm)
            if val is not None:
                모.넣기("57%d" % k, ID, val * 배 * 단위배[모.단위], "원",
                      "SEC companyfacts %s(10-Q 누계 %s~%s — 기능별 총액 = 원가 줄 %d %s)" % (태그q, 시작, 끝, k, 이름), 3)
            else:
                모.주의.append("57%d %s — companyfacts 에 %s~%s 누계(10-Q YTD) 값이 없다(연간만 채움)" % (k, ID, 시작, 끝))


def 미국모으기(cf, 모, 구, 단위, 누계=None):
    배 = 1.0 / {"원": 1.0, "천원": 1e3, "백만원": 1e6, "달러": 1.0, "천달러": 1e3, "백만달러": 1e6}.get(단위, 1e6)
    for 행, 태그들 in 미국태그.items():
        v, 태그 = _미국연간(cf, 태그들, 흐름=행 not in ("567",))
        if not v:
            모.확인불가.setdefault(행, "companyfacts 에 %s 없음" % " · ".join(태그들))
            continue
        for y, x in v.items():
            모.넣기(행, 기간ID(FY실적, y), x * 배 * 단위배[모.단위], "원", "SEC companyfacts %s(10-K)" % 태그, 3)
    # S5-10 · S5-15 · S5-17 — 유형 몫 상각(us-gaap:Depreciation — PP&E 만) · 무형 상각(인수 무형 포함) · 사용권 신규(새 리스로 얻은 사용권)
    for 속, 태그들 in (("유형상각", ("Depreciation", "DepreciationExpenseOnPropertyPlantAndEquipment")),
                    # 손개입 개선 1 — 인수 무형 상각을 다른 이름으로 내는 회사(실측: AmortizationOfIntangibleAssets 가 FY2017 에서 멈추고 그 뒤는 Acquired…)
                    ("무형상각", ("AmortizationOfIntangibleAssets", "AmortizationOfAcquiredIntangibleAssets", "FiniteLivedIntangibleAssetsAmortizationExpense")),
                    ("사용권신규", ("RightOfUseAssetObtainedInExchangeForOperatingLeaseLiability",
                               "RightOfUseAssetObtainedInExchangeForFinanceLeaseLiability"))):
        v, 태그 = _미국연간(cf, 태그들)
        if v:
            setattr(모, 속, {기간ID(FY실적, y): round(x * 배 * 단위배[모.단위] / 단위배[모.단위], 6) for y, x in sorted(v.items())})
    if (모.미국본문 or {}).get("내용연수"):
        모.내용연수 = 모.미국본문["내용연수"]
    v, 태그 = _미국연간(cf, ("EntityNumberOfEmployees",), 흐름=False)
    for y, x in v.items():
        모.넣기(541, 기간ID(FY실적, y), x, "명", "SEC companyfacts %s(연결 — 10-K 표지)" % 태그, 3)
    # S4-03 — 확정급여 연금 주석의 보상 상승률 가정(DB 제도가 있는 회사만 — SaaS · 설계 회사 다수는 없다)
    v, 태그 = _미국연간(cf, ("DefinedBenefitPlanAssumptionsUsedCalculatingBenefitObligationRateOfCompensationIncrease",), 흐름=False)
    if v:
        y = max(v)
        모.계리 = {"연결": {"범위": [round(v[y], 6)], "출처": "SEC companyfacts %s FY%s" % (태그, y)}}
    # 10-K 본문 「Human Capital」 — companyfacts 에 직원 수가 없는 회사가 대부분이다(2026-10-16, S1 리뷰)
    본 = 모.미국본문 or {}
    for y, x in (본.get("직원") or {}).items():
        if not v.get(y):
            모.넣기(541, 기간ID(FY실적, y), x, "명", "10-K 본문 Human Capital 문장 %s(연결)" % 본["직원출처"].get(y, ""), 2)
    if not v and not 본.get("직원"):
        모.확인불가.setdefault("541", "companyfacts 에 dei:EntityNumberOfEmployees 없음 · 10-K 본문 「Human Capital」에서도 직원 수 문장을 못 찾았다"
                                    "%s — 사람이 옮긴다" % ("" if 본 else "(폴더에 10-K 원문이 없다 — sec_fetch.py 가 받는다)"))
    # 기능별 비용(미국 — 성격별 주석이 없다)
    for k, t in 미국기능별.items():
        v, 태그 = _미국연간(cf, t)
        if v:
            모.기능별[k] = {기간ID(FY실적, y): x * 배 for y, x in v.items()}
            모.기능별출처.append("%s %s" % (k, 태그))
    if 구.get("원가줄"):                                               # S10-21(손개입) — 구조.원가줄 이 서 있으면 기능별 총액 = 57k 공시 실적
        미국기능별원천(cf, 모, 구, 배, 누계)
    # 운영 지표 — 모든 네임스페이스의 태그 이름을 정규식으로 훑는다(회사 확장 태그 포함)
    for 이름, p in 미국운영.items():
        r_ = re.compile(p)
        for ns, 표 in (cf.get("facts") or {}).items():
            for t in 표:
                if r_.match(t):
                    v, 태그 = _미국연간(cf, (t,), 흐름=False, 이름공간=(ns,))
                    if v:
                        모.운영.setdefault(이름, []).append({"공시이름": 태그, "단위": " · ".join((표[t].get("units") or {}).keys()),
                                                         "값": {기간ID(FY실적, y): x for y, x in v.items()}, "출처": "SEC companyfacts %s" % 태그})
    # 10-K 본문의 수량 문장 — 매장 · 가입자 · 사용자는 사업지표로, 인도 · 판매 · 생산 대수는 판매량 공시로(값만 · 구분 대응은 합류)
    for 이름, 목록 in ((모.미국본문 or {}).get("수량") or {}).items():
        값 = {기간ID(FY실적, z["해"]): z["값"] for z in 목록}
        출 = " · ".join(z["문장"] for z in 목록[:3])
        if 이름 == "판매량":           # 생산량은 판매량과 더하면 안 된다(동인진단은 같은 단위의 판매량 공시를 더한다) — 사업지표로
            모.판매량.append({"공시이름": "%s(10-K 본문 문장)" % 이름, "단위": 목록[0]["단위"], "값": 값, "출처": 출})
        elif 이름 not in 모.운영:
            모.운영.setdefault(이름, []).append({"공시이름": "10-K 본문 문장", "단위": 목록[0]["단위"], "값": 값, "출처": 출})
    for 품, 목록 in ((모.미국본문 or {}).get("출하") or {}).items():     # 품목별 출하량 — 품목마다 판매량 공시 한 줄(단위에 품목)
        모.판매량.append({"공시이름": "%s 출하량(10-K 본문 문장)" % 품, "단위": 목록[0]["단위"],
                       "값": {기간ID(FY실적, z["해"]): z["값"] for z in 목록}, "출처": " · ".join(z["문장"] for z in 목록[:3])})
    # 자산군 — 종류 태그
    종류 = {k: _미국연간(cf, t, 흐름=False)[0] for k, t in 미국자산태그.items()}
    출처 = {k: {y: "SEC companyfacts %s" % 미국자산태그[k][0] for y in d} for k, d in 종류.items()}
    # 태그가 빈 종류 · 해는 10-K PP&E 표에서(2026-10-23 — 태그 없는 회사의 56g · 567 이 비었다). 같은 종류의 줄은 더한다 · 태그 값은 덮지 않는다
    표 = (모.미국본문 or {}).get("유형표") or {}
    표종류 = {}
    for 라, 수 in 표.get("줄") or []:
        for j, v in enumerate(수[:2]):
            표종류.setdefault(유형종류(라), {}).setdefault(표["해"] - j, []).append((라, v * 표["배수"]))
    for k, 해들 in 표종류.items():
        for y, 줄들 in 해들.items():
            if y not in 종류.setdefault(k, {}):
                종류[k][y] = sum(v for _, v in 줄들)
                출처.setdefault(k, {})[y] = "%s — %s" % (표["출처"], " + ".join(l for l, _ in 줄들))
    for k, d in 종류.items():
        for y, x in d.items():
            모.유형원.setdefault(k, {}).setdefault("취득원가", {})[기간ID(FY실적, y)] = (x * 배, "원", 출처[k][y], 3)
    if not 모.원천.get("567"):
        for y, x in (종류.get("건설중") or {}).items():
            if "PP&E 표" in 출처["건설중"][y]:
                모.넣기(567, 기간ID(FY실적, y), x * 배 * 단위배[모.단위], "원", 출처["건설중"][y] + " — 건설중인자산", 3)
    if 표.get("주의"):
        모.주의.append("10-K %s — %s" % (표.get("출처"), 표["주의"]))
    대응 = 구["자산군대응"] or ({1: ["기계장치"], 2: ["건물"]} if 종류.get("기계장치") or 종류.get("건물") else {})
    for g, 이름들 in sorted(대응.items()):
        if 이름들 == "나머지":
            continue
        키 = [k for k in 미국자산태그 if any(k in 표준(n) or 표준(n) in k for n in 이름들)]
        for y in set().union(*(종류.get(k, {}) for k in 키)) if 키 else ():
            모.넣기(560 + g, 기간ID(FY실적, y), sum(종류[k].get(y, 0.0) for k in 키) * 배 * 단위배[모.단위], "원",
                  " + ".join(출처[k][y] for k in 키 if y in (종류.get(k) or {})), 3)
    if not any(re.fullmatch(r"56[123]", k) for k in 모.원천):
        모.확인불가.setdefault("56g", "companyfacts 에 자산 종류별 취득원가 태그가 없다 — 10-K 주석 Property, Plant and Equipment 표에서 사람이 옮긴다")
    for 행 in ("532", "533", "534", "535", "537", "538", "539", "542", "543", "544", "545", "547", "548", "549", "568", "569", "578"):
        모.확인불가.setdefault(행, "미국 — companyfacts 에 이 줄의 표준 태그가 없다(10-K 주석에서 사람이 옮긴다)")
    해 = {}
    for k, t in 미국회전.items():
        for y, v in _미국연간(cf, t, 흐름=k in ("매출", "매출원가", "영업이익", "세전이익", "법인세비용", "법인세납부") + _API흐름)[0].items():
            해.setdefault(기간ID(FY실적, y), {})[k] = v * 배 * 단위배[모.단위]
    # S6-06 — 매입채무만 따로 낸 태그가 끊긴 해(회사가 묶음 태그로 갈아탄 해)는 묶음 태그로 메우고 「묶음」 표시를 단다
    #   실측(CRM): AccountsPayableCurrent 가 FY2017~19 에서 멈추고 FY2020 부터 AccountsPayableAndOtherAccruedLiabilitiesCurrent 하나다
    for k, 태그들 in (("매입채무", ("AccountsPayableAndOtherAccruedLiabilitiesCurrent", "AccountsPayableAndAccruedLiabilitiesCurrent")),
                    ("매출채권", ("ReceivablesNetCurrent",))):
        v, _t = _미국연간(cf, 태그들, 흐름=False)
        for y, x in v.items():
            d = 해.setdefault(기간ID(FY실적, y), {})
            if d.get(k) is None:
                d[k] = x * 배 * 단위배[모.단위]
                d.setdefault("_묶음", []).append(k)
    # S6-05 · S6-02 — 엔진 190 의 자(13번 14 + 15 − 35 − 36 − 40 − 43)를 A2(sec_원천.잔액표)의 같은 태그로 · S6-06 미지급 비용(급여 미지급 포함)
    import sec_원천 as A2u                                    # noqa: PLC0415
    for 행, _부 in 기타행부호:
        합산, 태그들 = A2u.잔액표.get(행, (False, ()))
        for t in (태그들 if 합산 else 태그들[:1]) if 태그들 else ():
            v, _t = _미국연간(cf, (t,) if 합산 else 태그들, 흐름=False)
            for y, x in v.items():
                d = 해.setdefault(기간ID(FY실적, y), {})
                d["_13_%d" % 행] = (d.get("_13_%d" % 행) or 0.0) + x * 배 * 단위배[모.단위]
    for 키, 태그들 in (("미지급비용", ("AccruedLiabilitiesCurrent",)), ("_급여미지급", ("EmployeeRelatedLiabilitiesCurrent",)),
                     ("이연법인세자산", ("DeferredTaxAssetsNet", "DeferredIncomeTaxAssetsNet", "DeferredTaxAssetsNetOfValuationAllowance")),
                     ("이연법인세부채", ("DeferredTaxLiabilities", "DeferredIncomeTaxLiabilitiesNet", "DeferredTaxLiabilitiesNoncurrent")),
                     ("이월결손금", ("OperatingLossCarryforwards",)), ("평가충당금", ("DeferredTaxAssetsValuationAllowance",)),
                     ("미인식세무효익", ("UnrecognizedTaxBenefits",)),
                     ("이월세액공제", ("TaxCreditCarryforwardAmount", "DeferredTaxAssetsTaxCreditCarryforwards")),
                     ("연구개발공제이월", ("DeferredTaxAssetsTaxCreditCarryforwardsResearch",))):
        v, _t = _미국연간(cf, 태그들, 흐름=False)
        for y, x in v.items():
            해.setdefault(기간ID(FY실적, y), {})[키] = x * 배 * 단위배[모.단위]
            if 키 == "이월세액공제":                      # 원천 580(A-941 의 원천 — A3 소유)
                모.넣기(580, 기간ID(FY실적, y), x * 배 * 단위배[모.단위], "원", "SEC companyfacts %s(10-K 법인세 주석)" % _t, 3)
    for 키, 태그들 in (("실효세율공시", ("EffectiveIncomeTaxRateContinuingOperations",)),):
        v, _t = _미국연간(cf, 태그들, 흐름=True)
        for y, x in v.items():
            해.setdefault(기간ID(FY실적, y), {})[키] = x
    for 키, 태그들 in (("공제_연구개발", ("IncomeTaxReconciliationTaxCreditsResearch",)), ("공제_합계", ("IncomeTaxReconciliationTaxCredits",)),
                     ("공제_외국세율차", ("IncomeTaxReconciliationForeignIncomeTaxRateDifferential",)),
                     ("공제_주세", ("IncomeTaxReconciliationStateAndLocalIncomeTaxes",)),
                     ("공제_FDII", ("IncomeTaxReconciliationDeductionsForeignDerivedIntangibleIncome",
                                  "EffectiveIncomeTaxRateReconciliationForeignDerivedIntangibleIncomeAmount"))):
        v, _t = _미국연간(cf, 태그들, 흐름=True)
        for y, x in v.items():
            해.setdefault(기간ID(FY실적, y), {})[키] = x * 배 * 단위배[모.단위]
    for d in 해.values():
        for k in _API:
            d.setdefault(k, None)
        if d.get("_급여미지급") is not None:
            d["미지급비용"] = (d.get("미지급비용") or 0.0) + d.pop("_급여미지급")
    회전일수(해, 모, "SEC companyfacts(10-K)")
    return 해


# ────────────────────────────────────────────────────────────── 구조 · 실행

def 대응읽기(글, 기본):
    """「1=기계장치;2=건물,구축물」 · 「1=나머지」 → {번호: [이름] 또는 "나머지"}."""
    if not 글:
        return 기본
    낸 = {}
    for 조각 in 글.split(";"):
        if not 조각.strip():
            continue
        k, v = 조각.split("=", 1)
        v = v.strip()
        낸[int(k)] = v if v in ("나머지", "성격") else [x.strip() for x in v.split(",") if x.strip()]
    return 낸


def 구조읽기(a, 가정, 단일표시):
    """원가 줄 대응 · 자산군 대응 · 유지 기준 자산군 · 재고 변동 반영. 가정이 없으면 비용 표시로 기본을 정한다 —
    기능별 표시(매출원가 줄이 있다) = 원가 줄 1 나머지 / 단일 표시 = 원가 줄 5 · 6 성격 + 7 나머지(키트 CLAUDE.md 「장별 입력 규칙」)."""
    구 = (가정 or {}).get("구조") or {}
    원가줄 = []
    가정대응 = {}
    for x in 구.get("원가줄") or []:
        if x.get("실적", "공시") == "공시" and x.get("옛식", "아니오") != "예":
            원가줄.append({"번호": int(x["번호"]), "이름": x.get("이름")})
            if x.get("_대응") in ("나머지", "성격"):            # S10-05 — E 구조초안이 실어 둔 대응(나머지 · 성격)
                가정대응[int(x["번호"])] = x["_대응"]
    준 = 대응읽기(a.원가줄, {})
    if not 원가줄 and 준:
        # S10-05 — 가정에 원가 줄이 없으면 `--원가줄` 의 번호가 줄을 세운다(E 의 A3재실행인자 「3=성격;4=나머지;…」 그대로 다시 돌릴 수 있게)
        원가줄 = [{"번호": k, "이름": "원가 줄 %d" % k} for k in sorted(준)]
    elif 원가줄 and 준:
        있는 = {x["번호"] for x in 원가줄}
        원가줄 += [{"번호": k, "이름": "원가 줄 %d" % k} for k in sorted(준) if k not in 있는]
    if not 원가줄:
        원가줄 = ([{"번호": 5, "이름": "원가 줄 5"}, {"번호": 6, "이름": "원가 줄 6"}, {"번호": 7, "이름": "원가 줄 7"}] if 단일표시
               else [{"번호": 1, "이름": "원가 줄 1"}])
    for x in 원가줄:
        기본 = "나머지" if (len(원가줄) == 1 or (not 가정 and not 준 and x["번호"] == 7 and 단일표시)) else "성격"
        x["대응"] = 준.get(x["번호"]) or 가정대응.get(x["번호"]) or 기본
        if isinstance(x["대응"], list):
            x["대응"] = "성격"
    투 = 구.get("투자") or {}
    기본대응 = {}
    for x in 투.get("자산군") or []:
        이름 = (x.get("이름") or "").strip()
        기본대응[int(x["번호"])] = "나머지" if (이름.endswith(" 등") or "그 밖" in 이름 or 이름 in ("", "기타")) else [이름]
    return {"원가줄": 원가줄, "재고변동반영": ((구.get("원가") or {}).get("재고변동반영", "예" if (not 가정 and not 단일표시) else "아니오") == "예"),
            "자산군대응": 대응읽기(a.자산군, 기본대응), "유지기준자산군": int(투.get("유지기준자산군") or 1), "단일표시": 단일표시}


def 실적열(가정):
    if not 가정:
        return None
    try:
        from 기간축 import 기간축
        축 = 기간축(가정)
        return [축.ID[i] for i in 축.실적]
    except Exception:                                         # noqa: BLE001
        return None


def 원문받기(폴더, 연도들, 모):
    """제출이력(dart_제출이력.json)에서 그 해 사업보고서 접수번호를 찾아 원문을 받는다 — dart_fetch.원문(같은 공시 원문)."""
    p = os.path.join(폴더, "dart_제출이력.json")
    if not os.path.exists(p):
        모.기록.append("받기 — %s 가 없어 받을 접수번호를 모른다" % p)
        return
    목록 = json.load(io.open(p, encoding="utf-8")).get("list") or []
    import dart_fetch                                          # noqa: PLC0415
    dart_fetch.RAW = 폴더
    for y in 연도들:
        후보 = [x for x in 목록 if re.search(r"사업보고서\s*\(%d\.\d{2}\)" % y, x.get("report_nm", ""))]
        if not 후보:
            모.기록.append("받기 — %d 사업보고서가 제출이력에 없다" % y)
            continue
        접수 = sorted(후보, key=lambda x: x["rcept_no"])[-1]["rcept_no"]
        if glob.glob(os.path.join(폴더, "**", 접수 + ".txt"), recursive=True):
            continue
        try:
            dart_fetch._준비()
            dart_fetch.원문(접수, "사업%d" % y)
            모.기록.append("받기 — %d 사업보고서 원문(접수 %s)" % (y, 접수))
        except SystemExit as e:
            모.기록.append("받기 실패 — %d: %s" % (y, e))
        except Exception as e:                                # noqa: BLE001
            모.기록.append("받기 실패 — %d: %s" % (y, e))


def _대상고유번호(폴더들):
    """폴더(최상위)의 `dart_기업개황.json` 의 고유번호(8자리) — 없으면 None."""
    for 폴더 in 폴더들:
        p = os.path.join(폴더, "dart_기업개황.json")
        try:
            c = ("%s" % (json.load(io.open(p, encoding="utf-8")).get("corp_code") or "")).strip()
        except (OSError, ValueError):
            continue
        if re.fullmatch(r"\d{8}", c):
            return c
    return None


def 원문고유번호(txt경로):
    """원문 txt 곁 XML 표지의 제출인 고유번호(`<COMPANY-NAME AREGCIK="…">`) — 바이트로 읽는다(옛 수시공시 XML 은 EUC-KR). 없으면 None."""
    try:
        import 공시표                                              # noqa: PLC0415
        x = 공시표.곁XML(txt경로)
    except Exception:                                            # noqa: BLE001
        x = None
    if not x:
        return None
    try:
        with open(x, "rb") as f:
            m = re.search(rb'AREGCIK="(\d{8})"', f.read(4000))
        return m.group(1).decode() if m else None
    except OSError:
        return None


def 원문들(폴더들, 버림=None, 고유번호=None):
    """폴더들의 공시 원문 txt → 보고서 목록(최근 먼저). 버림(목록)을 주면 종류 · 기간을 못 읽어 버린 본문 파일을 [{"파일", "까닭"}] 로 적는다
    (첨부 감사보고서 `…_00760.txt` 는 본문이 아니라 적지 않는다) — FX-A R1: 9개 파일이 말없이 버려졌다.
    **남의 회사 원문은 읽지 않는다**(FX4-F D1 — 2026-10-25): 수시공시 받기가 상장 종속회사의 사업보고서까지 `_raw/수시공시원문/` 에 두자
    A3 가 그것을 대상 회사 보고서로 읽어 상각 · 579 · 생산능력 표가 종속회사 값으로 덮였다(자동차 회사 FY2025 579 5.0조 → 1.8조 · CAPEX ÷ 상각 202).
    대상 고유번호(인자 · 없으면 폴더 최상위 `dart_기업개황.json`)와 곁 XML 표지의 제출인 고유번호(AREGCIK)가 다르면 버리고 버림에 적는다.
    고유번호를 모르거나 XML 이 없으면 거르지 않는다(옛 회차 호환)."""
    보들, 본 = [], set()
    고유번호 = 고유번호 or _대상고유번호(폴더들)
    남들 = {}
    for 폴더 in 폴더들:
        for p in sorted(glob.glob(os.path.join(폴더, "**", "*.txt"), recursive=True)):
            이름 = os.path.basename(p)
            if not re.fullmatch(r"\d{14}(_\d+)?\.txt", 이름):
                continue
            if 고유번호:
                남 = 원문고유번호(p)
                if 남 and 남 != 고유번호:
                    if "_" not in 이름:
                        남들[남] = 남들.get(남, 0) + 1
                    continue
            보 = 보고서(p)
            if not 보.쓸만한가():
                if 버림 is not None and "_" not in 이름 and 보.종류:
                    버림.append({"파일": os.path.relpath(p, 폴더), "까닭": "%s보고서인데 보고 기간(사업연도 … 부터 … 까지)을 못 읽었다" % 보.종류})
                continue
            키 = (보.종류, 보.끝, 보.접수[:14])
            if 키 in 본:
                continue
            본.add(키)
            보들.append(보)
    if 남들 and 버림 is not None:
        버림.append({"파일": "(남의 회사 원문 %d편 — 제출인 %d곳: %s%s)" % (sum(남들.values()), len(남들),
                                                              " · ".join("%s %d" % kv for kv in sorted(남들.items(), key=lambda kv: -kv[1])[:5]),
                                                              " …" if len(남들) > 5 else ""),
                   "까닭": "대상 고유번호 %s 와 다른 회사(상장 종속회사 · 자회사)의 원문 — 대상 회사 보고서로 읽지 않음" % 고유번호})
    # 최근 보고서 먼저 — 같은 순위면 먼저 넣은 것이 이긴다(최근 공시가 재작성한 값)
    보들.sort(key=lambda b: (b.끝, b.종류 == "사업", b.접수), reverse=True)      # 같은 기간이면 늦게 낸(정정) 것 먼저
    return 보들


_해당없음 = "해당 없음"
_확인불가 = "확인 불가"


def _열값(d, 실=None):
    return {c: round(v, 6) for c, v in sorted(d.items()) if v is not None and (not 실 or c in 실)}


def 판매량칸(모, 보들, 해당, a):
    """판매량 공시 칸 — 찾은 줄 목록, 없으면 **빈 목록 대신 까닭을 적은 문자열**(빈칸 금지 — 가정_스키마 「갈래 산출물」, S1 리뷰).
    「해당 없음」 = 그 유형에 원래 없다(생산능력 해당 없음) · 「확인 불가」 = 있을 수 있는데 공시에서 못 찾았거나 원문이 없다."""
    if 모.판매량:
        return 모.판매량
    if "생산능력" in 해당:
        return _해당없음
    if a.미국:
        return ("%s — 10-K 본문에서 판매 · 인도 수량 문장을 찾지 못했다%s. MD&A · Item 1 의 수량 표는 본선이 읽는다"
                % (_확인불가, "" if 모.미국본문 else "(10-K 원문 없음)"))
    if any(b.종류 == "사업" for b in 보들):
        return "%s — 확인했고 없었다: 사업의 내용 「매출 · 판매 · 생산 실적」 표에 수량 열이 없다(금액만 공시)" % _확인불가
    return "%s — 사업보고서 원문을 읽지 못했다(원문 없음)" % _확인불가


def 공시칸(값, 보들, a, 무엇, 표머리):
    """판가공시 · 가동률공시 칸(S2-13) — 찾은 줄 목록, 없으면 까닭을 적은 문자열(빈칸 금지)."""
    if 값:
        return 값
    if a.미국:
        return "%s — 미국 10-K 에는 %s 표의 정해진 자리가 없다. MD&A 의 문장은 본선이 읽는다" % (_확인불가, 무엇)
    if any(b.종류 == "사업" for b in 보들):
        return "%s — 확인했고 없었다: 사업의 내용 「%s」에 수치 표 · 문장이 없다(문장 서술만이거나 그 절이 없다)" % (_확인불가, 표머리)
    return "%s — 사업보고서 원문을 읽지 못했다(원문 없음)" % _확인불가


def 조립(a):
    가정 = json.load(io.open(a.가정, encoding="utf-8")) if a.가정 else None
    단위 = a.단위 or ((가정 or {}).get("메타") or {}).get("금액단위") or "백만원"
    if 단위 not in 단위배:
        단위배[단위] = 1.0
    모 = 모음(단위)
    보들, 해 = [], {}
    if a.미국:
        cf = json.load(io.open(a.미국, encoding="utf-8"))
        구 = 구조읽기(a, 가정, False)
        # 10-K 본문 — companyfacts 곁(또는 --원천폴더)의 10K_*.txt/htm (2026-10-16, S1 리뷰: 종전에는 「판정 보류」 고정이었다)
        미폴더들 = [os.path.dirname(os.path.abspath(a.미국))] + [os.path.abspath(x) for x in (a.원천폴더 or [])]
        for 폴더 in 미폴더들:
            모.미국본문 = 미국본문읽기(폴더)
            if 모.미국본문:
                break
        # FX-A — FX-C 의 `_raw/미국원천.json` 이 있으면 ① Item 1 · 10-Q 본문 조각(유형 낱말) ② 기준일 누계 열 ③ 인원 · 능력 문장을 받는다(없으면 옛 길)
        미원, 미원경로 = 미국원천불러오기(미폴더들)
        if 미원:
            본문 = (미원.get("본문") or {})
            i1 = 본문.get("Item1") if isinstance(본문.get("Item1"), str) else ""
            i2 = 본문.get("Item2") if isinstance(본문.get("Item2"), str) else ""
            글1 = " ".join(x for x in (i1, i2) if x)
            if 글1 and (not 모.미국본문 or not any((모.미국본문.get("유형점수") or {}).values())):
                모.미국본문 = dict(모.미국본문 or {"직원": {}, "직원출처": {}, "수량": {}, "읽은": []},
                               유형점수=유형점수(글1, 미국유형낱말, 미국낱말맥락제외), _항목1=글1, _신호글=글1,
                               출처=미원경로, 읽은=list((모.미국본문 or {}).get("읽은") or []) + ["미국원천.json(본문 조각)"])
            elif 글1 and 모.미국본문:
                # FX2-A R4(2026-10-25) — 10-K 를 직접 읽은 Item 1 이 있어도 미국원천.json 의 Item 1(더 길면) · Item 2(설비 · 데이터센터 · 공장 면적)를
                # 낱말 점수에 넣는다 — Item 2 는 회사의 물리적 꼴(공장 · 물류 · 데이터센터)을 적는 절이다
                직1 = 모.미국본문.get("_항목1") or ""
                점글 = " ".join(x for x in ((i1 if len(i1) > len(직1) else 직1), i2) if x)
                모.미국본문["유형점수"] = 유형점수(점글, 미국유형낱말, 미국낱말맥락제외)
                모.미국본문["_항목1"] = 점글
                모.미국본문["읽은"] = list(모.미국본문.get("읽은") or []) + ["미국원천.json(Item 1 · 2 조각)"]
            모.미국원문읽음 = [{"종류": x.get("양식"), "기간끝": x.get("기간끝"), "접수": x.get("accession"),
                            "제출일": x.get("제출일") or _파일날(x.get("파일")), "파일": x.get("파일"),
                            "기준일보고서": x.get("기준일과") == "기준일분기", "기준일과": x.get("기준일과"),
                            "역할": _미국역할(x)} for x in (미원.get("공시") or []) if isinstance(x, dict)]
            모.기록.append("미국원천.json 읽음(%s — 공시 %d건)" % (os.path.basename(미원경로), len(모.미국원문읽음)))
        누계 = None
        if 가정:                                                      # S10-21(손개입) — 기준일 누계 열(10-Q YTD)의 ID · 시작일 · 끝날
            try:
                from 기간축 import 기간축 as _기간축                       # noqa: PLC0415
                _축 = _기간축(가정)
                if _축.누계 is not None:
                    _c = _축.열[_축.누계]
                    누계 = (_c.ID, _c.시작일.isoformat(), _c.종료일.isoformat())
            except Exception:                                           # noqa: BLE001
                누계 = None
        if 누계 is None and 미원 and isinstance(미원.get("누계"), dict):
            _n = 미원["누계"]
            if _n.get("기간ID") and _n.get("시작") and _n.get("끝"):
                누계 = (_n["기간ID"], _n["시작"], _n["끝"])                # 가정 없이도 기준일 누계 열(10-Q YTD)을 세운다
        해 = 미국모으기(cf, 모, 구, a.원천통화단위, 누계)
        if 미원 and isinstance(미원.get("인원"), dict) and isinstance(미원["인원"].get("값"), (int, float)) and not 모.원천.get("541"):
            # FX2-A R5(2026-10-25) — 인원의 기준일이 비면(본문 「Human Capital」 절 — 기준일 없이 10-K 파일 이름만 남는다) 출처 파일 이름의 결산월 ·
            # 미국원천 공시 목록의 가장 늦은 연차 보고서 기간 끝에서 회계연도를 잡는다(종전엔 기준일이 비면 버려 541 · 사업지표.직원수가 「확인 불가」)
            _d, _근 = _인원해(미원)
            if _d:
                모.넣기(541, 기간ID(FY실적, _d), float(미원["인원"]["값"]), "명",
                       "미국원천.json 인원(%s · %s · 회계연도 %s)" % (미원["인원"].get("원천") or "?", 미원["인원"].get("출처") or "", _근), 1)
                모.확인불가.pop("541", None)
                모.기록.append("미국원천.json 인원 %s명 → 541 FY%d(%s)" % ("{:,.0f}".format(미원["인원"]["값"]), _d, _근))
        본 = 모.미국본문
        if 본:
            fy = sorted(c for c in 해 if c.startswith("FY") and (해[c] or {}).get("매출"))
            재무 = {}
            if fy and 해[fy[-1]].get("매출"):
                v = 해[fy[-1]]
                재무 = {"유형자산÷매출": (v.get("유형자산") or 0.0) / v["매출"], "재고÷매출": (v.get("재고") or 0.0) / v["매출"]}
            재무출처 = "SEC companyfacts"
            if not 재무:
                # FX2-A R4(2026-10-25) — IFRS 20-F 회사(companyfacts 가 `ifrs-full` 만)는 미국모으기의 해가 비어 재무 지문이 0 이었다(파운드리가
                # 「조립 · 경공업 제조」 로 갔다) — ifrs-full 연차 값으로 비율만 잰다(단위가 없는 비율이라 통화 환산이 필요 없다)
                재무 = _ifrs재무지문(cf)
                if 재무:
                    재무출처 = "SEC companyfacts(ifrs-full · 20-F 연차)"
            _rpo = _미국RPO(cf, 미원)                                        # 원 통화(달러) — 해는 원천통화단위로 나뉘어 있다
            _rpo배 = 1.0 / {"원": 1.0, "천원": 1e3, "백만원": 1e6, "달러": 1.0, "천달러": 1e3, "백만달러": 1e6}.get(a.원천통화단위, 1e6)
            _지분 = _지분법투자(cf)
            미신호 = 유형신호(본.get("_항목1") or "", 해, None, None, 사업의내용찾음=bool(본.get("_항목1")),
                         RPO=(_rpo * _rpo배) if _rpo else None, 신호글=본.get("_신호글") or 본.get("_항목1") or "",
                         지분법투자=(_지분 * _rpo배) if _지분 else None, 유형자산비=재무.get("유형자산÷매출"))
            판, 근 = 유형고르기(본["유형점수"], 미국유형낱말, 재무, 신호=미신호)
            근거 = [{"출처": "%s Item 1(Business)" % os.path.basename(본["출처"]), "문장 요약": x} for x in 근]
            if 재무:
                근거.append({"출처": 재무출처, "문장 요약": " · ".join("%s %.2f" % kv for kv in 재무.items())})
            보류 = None
            if not 판:
                판 = ["판정 보류"]
                근거.append({"출처": "%s Item 1" % os.path.basename(본["출처"]), "문장 요약": "유형 낱말이 문턱을 넘지 않았다 — 본선이 Item 1 · segment 주석으로 정한다(보류후보 참고)"})
                보류 = 보류후보(본["유형점수"], 미국유형낱말, 재무, 미신호)
            유형 = {"판정": 판, "구분별": {}, "근거": 근거, "점수": 본["유형점수"], "신호": 미신호}
            if 보류:
                유형["보류후보"] = 보류
            모.기록.append("10-K 본문 %d건 읽음(%s)" % (len(본["읽은"]), " · ".join(본["읽은"])))
        else:
            유형 = {"판정": ["판정 보류"], "구분별": {}, "근거": [{"출처": "SEC companyfacts", "문장 요약":
                    "미국 — companyfacts 곁에 10-K 원문(10K_*.htm · .txt)이 없어 Item 1 을 읽지 못했다. sec_fetch.py 가 받는다 — 없으면 본선이 Item 1 · segment 주석으로 정한다"}]}
        모.해당없음.append({"항목": "성격별비용", "까닭": "미국 GAAP 서식 — 비용의 성격별 분류 주석이 없다. 기능별비용 · 사업지표로 대신한다"})
        if 해 and not any((v or {}).get("재고") for v in 해.values()):
            모.해당없음.append({"항목": "재고자산회전일수", "까닭": "companyfacts 에 재고자산(InventoryNet)이 없다"})
    else:
        폴더들 = [os.path.abspath(p) for p in (a.원천폴더 or [os.path.join(ROOT, "_raw")])]
        보들 = 원문들(폴더들, 모.원문버림)
        if a.받기:
            있는해 = {b.회계연도 for b in 보들 if b.종류 == "사업"}
            실 = 실적열(가정) or []
            최근 = max(있는해) if 있는해 else datetime.date.today().year - 1
            필요 = sorted(({int(x[2:6]) + 1 for x in 실 if x.startswith("FY")} |
                         set(range(최근 - a.해수 + 2, 최근 + 1))) - 있는해)      # 사업보고서 하나가 당기 · 전기 두 해를 준다
            if 필요 and time.time() - _시작 < a.상한분 * 60:
                원문받기(폴더들[0], 필요, 모)
                모.원문버림[:] = []
                보들 = 원문들(폴더들, 모.원문버림)
        해 = API모으기(폴더들, 모)
        # 단일 표시(영업수익 · 영업비용) 판정 — 매출이 있는 최근 세 해 가운데 과반이 매출원가 없음(None · 0)이면 단일. 종전에는 모든 해가 None 이어야 해서
        # 한 해(옛 서식)의 매출원가 태그 · 0.0 칸에 판정이 뒤집혔다(2026-10-23 실측 — 원가 줄이 매출원가 쪽에 서고 매입채무 회전 기준이 0 이 됐다)
        _최근 = [v for _k, v in sorted(해.items()) if v.get("매출") is not None][-3:]
        단일 = bool(_최근) and sum(1 for v in _최근 if not v.get("매출원가")) * 2 > len(_최근)
        구 = 구조읽기(a, 가정, 단일)
        for 일, f in (("성격별", lambda: 성격별모으기(보들, 모, 구)), ("직원", lambda: 직원모으기(보들, 모)),
                     ("라벨", lambda: 라벨모으기(보들, 모)), ("퇴직급여", lambda: 퇴직급여모으기(보들, 모)),
                     ("연구개발", lambda: 연구개발모으기(보들, 모)), ("유형자산", lambda: 유형모으기(보들, 모, 구)),
                     ("내용연수", lambda: setattr(모, "내용연수", 내용연수모으기(보들))),
                     ("사용권", lambda: setattr(모, "사용권신규", 사용권모으기(보들, 모))),
                     ("투자계획", lambda: (lambda r: (setattr(모, "투자계획", r[0]), setattr(모, "투자발화", r[1]),
                                                     setattr(모, "투자진행", r[2] if len(r) > 2 else [])))(투자계획모으기(보들, 모)))):
            if time.time() - _시작 > a.상한분 * 60:
                모.기록.append("벽시계 상한 %d분에 닿아 「%s」부터 돌리지 않았다" % (a.상한분, 일))
                break
            f()
        회전일수(해, 모, "DART 재무제표 API(dart_앵커시계열.json · dart_재무_연결_*.json)")
        API대조(해, 모)
        # FX-A — 유형 신호의 재료(가동률 · 수주잔고 표)를 유형 판정 앞에서 읽는다
        모.가동률 = 가동률모으기(보들)
        모.수주표, 모.수주문장 = 수주잔고표모으기(보들, 해)
        모.생산능력표 = 생산능력표모으기(보들)          # FX2-A R11 — 유형 판정 앞(자기 공장 능력 공시가 약한 외주 문장을 누른다)
        유형 = 유형판정(보들, 해, 모, 수주=모.수주표)
        유형["구분별상세"] = 부문상세(보들, 유형.get("구분별") or {}, 단위)
        모.운영 = 운영지표모으기(보들, 모)
        모.판매량 = 판매량모으기(보들)
        모.판가 = 가격변동모으기(보들)
        모.약정줄 = 약정줄모으기(보들, 단위)
        모.변동표 = 유형변동표XML(보들, 단위)
        모.변동표상각 = 변동표상각들(보들, 단위)
        모.비현금 = 비현금설비(보들, 단위)
        모.해당없음.extend(해당없음판정(보들, 유형, 해))
        if not 모.성격별:
            모.확인불가.setdefault("성격별비용", "원문에서 「비용의 성격별 분류」 · 「영업비용」 주석 표를 찾지 못했다(읽은 보고서 %d개)" % len(보들))
    # S10-15 — 반기 · 분기 보고서에 「직원 현황」이 없으면(보고 시점 — 사업보고서에만 있는 회사) 기준일 인원(541)이 비어 예측 인건비가 0 이 된다.
    #   직전 회계연도 직원 수를 기준일 열의 **후보**로 낸다(출처 · 「후보」 표시 — 근거 칸 확인상태 「추정」, 사람이 확인한다)
    실0 = 실적열(가정)
    끝0 = 실0[-1] if 실0 else (max(보들, key=lambda b: b.끝).열("당", 흐름=False) if (not a.미국 and 보들) else None)
    d541 = 모.원천.get("541") or {}
    if 끝0 and not str(끝0).startswith("FY") and 끝0 not in d541:
        앞 = max((x for x in d541 if str(x).startswith("FY")), key=lambda x: int(re.sub(r"\D", "", x)[-4:]), default=None)
        if 앞:
            모.넣기(541, 끝0, d541[앞], "명", "후보 — 직전 회계연도(%s) 직원 수 · %s 보고서에 직원 현황이 없다(보고 시점 — 사람 확인)" % (앞, 끝0), 0.5)
            모.주의.append("541 %s — 반기 · 분기 보고서에 직원 현황이 없어 %s 직원 수를 기준일 인원 후보로 냈다(근거 확인상태 「추정」 — 사람 확인)" % (끝0, 앞))
    # 실적 열 — 가정이 있으면 그 축의 실적 열로 거른다(원천행만. 시계열 칸은 전부 둔다 — E 가 열 해를 잰다)
    실 = 실적열(가정)
    원천행 = {}
    for 행 in sorted(모.원천, key=lambda x: int(re.sub(r"\D", "", x) or 0)):
        v = _열값(모.원천[행], 실)
        if v:
            원천행[행] = v
    해당 = {x["항목"] for x in 모.해당없음}
    성격키 = {k for 표 in 모.성격별.values() for _, _, _, k in 표["줄"]}
    for x in 구["원가줄"]:
        if x["대응"] == "성격" and ("원가%d" % x["번호"]) not in 성격키 and 모.성격별:
            모.해당없음.append({"항목": "57%d" % x["번호"], "까닭": "성격별 표에 원가 줄 %d 로 가는 줄이 없다(다른 줄에 흩어져 있다)" % x["번호"]})
    필요행 = (["531", "541", "542", "543", "567", "579"] + (["578"] if 구["재고변동반영"] else []) +
             (["569"] if 구["자산군대응"] else []) + ["56%d" % g for g in 구["자산군대응"]] +
             ["57%d" % x["번호"] for x in 구["원가줄"] if not (x["대응"] == "성격" and ("원가%d" % x["번호"]) not in 성격키 and 모.성격별)])
    for 행 in 필요행:
        if 행 not in 원천행 and 행 not in 모.확인불가:
            모.확인불가[행] = ("companyfacts 에서 이 줄의 태그를 찾지 못했다(10-K 주석에서 사람이 옮긴다)" if a.미국 else
                           "원문에서 이 줄을 찾지 못했다(읽은 보고서 %d개)" % len(보들))
    재무일, _평가일T = 가정두날(가정)                                # 날짜 둘 — 재무 쪽은 F(기준일.재무기준일 · 없으면 T = 옛 꼴)
    기준일 = a.기준일 or (max(b.끝 for b in 보들).isoformat() if 보들 else 재무일)
    평가일 = a.기준일 or 재무일 or ""                                  # 「기준일 보고서」 를 가르는 날 = 재무기준일 F(이름은 옛 그대로)
    원문읽음 = [{"종류": b.종류, "기간끝": b.끝.isoformat() if b.끝 else None, "접수": b.접수, "정정": bool(getattr(b, "정정", False)),
             "형식판": getattr(b, "형식판", None), "XML": bool(_문(b)), "기준일보고서": bool(평가일 and b.끝 and b.끝.isoformat() == 평가일),
             "제출일": _접수날(b.접수)}
            for b in 보들] if not a.미국 else (모.미국원문읽음 if getattr(모, "미국원문읽음", None) else [])
    if not a.미국:
        역할매기기(원문읽음, 평가일)
    출처시점 = 출처시점고르기(원문읽음, 평가일)
    원문경보 = []
    if 평가일 and not a.미국 and 보들 and not any(x["기준일보고서"] for x in 원문읽음):
        원문경보.append("경보 — 평가기준일(%s) 보고서를 읽지 못했다(읽은 가장 늦은 기간 %s)%s" % (
            평가일, max(b.끝 for b in 보들).isoformat(), (" · 버린 본문 %d개" % len(모.원문버림)) if 모.원문버림 else ""))
    _기간버림 = [x for x in 모.원문버림 if not ("%s" % x.get("파일", "")).startswith("(남의 회사")]
    if _기간버림:
        원문경보.append("경보 — 종류는 읽었는데 보고 기간을 못 읽어 버린 본문 %d개: %s" % (len(_기간버림), " · ".join(x["파일"] for x in _기간버림[:4])))
    for x in 모.원문버림:
        if ("%s" % x.get("파일", "")).startswith("(남의 회사"):
            원문경보.append("알림 — %s %s" % (x["파일"].split(" — ")[0].strip("("), "— 대상 회사 보고서로 읽지 않았다(제출인 고유번호가 다르다)"))
    모.주의.extend(원문경보)
    근거 = {}
    for 행, 열들 in 모.출처.items():
        if 행 not in 원천행:
            continue
        글 = sorted({"%s: %s" % (열, 출처) for 열, (출처, _) in 열들.items() if 열 in 원천행[행]})
        근거[행] = ["[동인원천] " + " · ".join(글), 기준일, "추정 — 사람 확인(후보 값이 있다)" if any("후보 —" in x for x in 글) else "확인완료", None]
    # 성격별비용 칸
    if 모.성격별:
        항목, 대응 = {}, {}
        for 열, 표 in 모.성격별.items():
            for l, x, 항, 키 in 표["줄"]:
                항목.setdefault(l, {})[열] = x * 단위배.get(표["단위"], 1.0) / 단위배[단위]
                대응[l] = {"인건비": "인건비", "복리후생": "인건비", "주식보상": "인건비", "상각": "상각", "재고변동": "재고변동",
                          "대체": "대체"}.get(키, ("원가줄%s" % 키[2:]) if 키.startswith("원가") else "미분류")
        # `성격` — 줄마다 성격 사전의 값(변동 · 고정 · 준변동 · 혼합 · 빈 글 — `성격별비용.항목표`). E 가 고정 · 변동 판정의 사전으로 쓴다(S3-10)
        성 = {}
        for l in 항목:
            분 = 성격별비용.분류(l, 구.get("단일표시", False))
            성[l] = 분[2] if 분 else ""
        성격 = {"항목": {k: _열값(v) for k, v in 항목.items()}, "대응": 대응, "성격": 성, "합계검산": 모.합계검산}
    else:
        성격 = _해당없음 if any(x["항목"] == "성격별비용" for x in 모.해당없음) else _확인불가
    # 운전자본
    회 = 모.회전
    판 = 유형["판정"]
    # S6-06 — 재고가 매출의 0.5% 에 못 미치면(서비스 · 플랫폼 · 게임) 재고일수 노드는 「해당 없음 — 비중 미미」
    재고비중 = [d["_재고매출비"] for d in 회.values() if d.get("_재고매출비") is not None]
    if 재고비중 and max(재고비중) < 0.005 and "재고자산회전일수" not in 해당:
        모.해당없음.append({"항목": "재고자산회전일수", "까닭": "비중 미미 — 재고 ÷ 연환산 매출이 모든 해 0.5%% 미만(최대 %.2f%%)" % (max(재고비중) * 100)})
        해당.add("재고자산회전일수")
    # S6-02 — 계약부채 · 선수금 표준 태그가 없을 때 「해당 없음」으로 단정하지 않는다(CLAUDE 동인 지도 규칙 「있어야 하는데 못 찾았으면 확인 불가」).
    #   선수 업종(구독 · 게임 · 플랫폼 · 수주)이거나 기타유동부채(13번 43)가 연환산 매출의 1% 이상이면 「확인 불가 — 주석에서 구성을 연다」
    선수업종 = [x for x in ("소프트웨어 · 구독", "플랫폼 · 중개", "게임 · 콘텐츠", "수주 산업") if x in 판]
    끝열 = max((c for c, d in 회.items() if (d.get("_기타행") or {}).get("43") is not None and d.get("_매출연")), key=_열때, default=None)
    기타43 = ((회[끝열]["_기타행"]["43"], 회[끝열]["_기타행"]["43"] / 회[끝열]["_매출연"]) if 끝열 else None)
    계약글 = None
    if not any(("_선수금" in d or "_계약부채" in d) for d in 회.values()):
        if 선수업종 or (기타43 and 기타43[1] >= 0.01):
            계약글 = ("%s — 계약부채 · 선수금 표준 태그가 없다. %s유형(%s)상 운전자본이 매출보다 먼저 들어오는 몫이 클 수 있다 — 주석에서 기타유동부채 · "
                    "기타지급채무의 구성(계약부채 · 선수수익 · 이연수익 · 예수금 · 정산채무)을 열어 옮긴다" % (
                        _확인불가, ("기타유동부채(13번 43) %s %s(연환산 매출의 %.1f%%) · " % (끝열, "{:,.0f}".format(기타43[0]), 기타43[1] * 100)) if 기타43 else "",
                        " · ".join(선수업종) or "선수 업종 아님 — 기타유동부채가 매출의 1% 이상"))
            모.확인불가.setdefault("운전자본.선수금계약부채", 계약글[len(_확인불가) + 3:])
            if 선수업종:
                모.주의.append("선수 업종(%s) — 계약부채 · 선수금이 표준 태그로 안 잡혔다. %s 운전자본의 주 몫일 수 있다(S6-02)" % (
                    " · ".join(선수업종), ("기타유동부채 %s %s(매출의 %.1f%%)가" % (끝열, "{:,.0f}".format(기타43[0]), 기타43[1] * 100)) if 기타43 else "주석의 계약부채가"))

    def _칸(키, 기본=_해당없음):
        return {c: d[키] for c, d in 회.items() if 키 in d} or (계약글 or 기본)
    묶음 = {}
    for c, d in 회.items():
        for k in d.get("_묶음") or []:
            묶음.setdefault(k, []).append(c)
    if 묶음:
        모.주의.append("묶음 태그로 잡은 회전일수 — %s. 미수금 · 미지급금 · 미지급비용이 섞였다(주석 미분리 — 「묶음 계정은 통째로 넣지 않는다」). "
                     "E 는 그 칸의 기저를 「다른범위」로 둔다" % " · ".join("%s %s" % (k, " · ".join(sorted(v, key=_열때))) for k, v in 묶음.items()))
    운 = {"기준": "기말", "출처": 모.회전출처,
         # 종전 칸의 회전 기준 — 매출채권 = 매출, 재고 · 매입채무 = 매출원가(단일 표시 열은 영업비용). 엔진 기준이 다르면 `회전기준별` 을 본다(S6-03)
         "회전기준": {"매출채권회전일수": "매출", "재고자산회전일수": "영업비용" if getattr(모, "단일회전", False) else "매출원가",
                  "매입채무회전일수": "영업비용" if getattr(모, "단일회전", False) else "매출원가"},
         "매출채권회전일수": {c: d["매출채권"] for c, d in 회.items() if "매출채권" in d} or _확인불가,
         "재고자산회전일수": (_해당없음 if "재고자산회전일수" in 해당 else ({c: d["재고자산"] for c, d in 회.items() if "재고자산" in d} or _확인불가)),
         "매입채무회전일수": {c: d["매입채무"] for c, d in 회.items() if "매입채무" in d} or _확인불가,
         "선수금": _칸("_선수금"), "계약부채": _칸("_계약부채"),
         "계약자산": {c: d["_계약자산"] for c, d in 회.items() if "_계약자산" in d} or _해당없음,
         "선수금계약부채비율": _칸("선수금계약부채비율"),
         "계약자산비율": {c: d["계약자산비율"] for c, d in 회.items() if "계약자산비율" in d} or _해당없음,
         # S6-02 · S6-05 — 엔진 190 의 자(13번 14 + 15 − 35 − 36 − 40 − 43 ÷ 연환산 매출, 자산 부호)와 그 행들의 잔액
         "기타순운전자본비율": {c: d["기타순운전자본비율"] for c, d in 회.items() if "기타순운전자본비율" in d} or _확인불가,
         "기타행": {c: d["_기타행"] for c, d in 회.items() if d.get("_기타행")},
         # S6-06 — 미지급 비용(미국 AccruedLiabilities + EmployeeRelated · 국내 미지급비용) ÷ 판관비 × 365 — 엔진 190 안의 대조(서비스 · SaaS)
         "미지급비용회전일수": {c: d["미지급비용회전일수"] for c, d in 회.items() if "미지급비용회전일수" in d} or _확인불가,
         "묶음": 묶음,
         "잔액": {c: {k[1:-2]: d[k] for k in ("_재고잔액", "_매입채무잔액", "_매출채권잔액") if k in d} for c, d in 회.items()
                if any(k in d for k in ("_재고잔액", "_매입채무잔액", "_매출채권잔액"))},
         "매출연": {c: d["_매출연"] for c, d in 회.items() if "_매출연" in d},
         "영업이익률": {c: d["영업이익률"] for c, d in 회.items() if "영업이익률" in d},
         "국면": 국면(회)}
    # 유형자산
    자산군 = []
    for g, 이름들 in sorted(구["자산군대응"].items()):
        자산군.append({"번호": g, "이름": "나머지" if 이름들 == "나머지" else " · ".join(이름들),
                     "취득원가": 모.원천.get("%d" % (560 + g), {}),           # 시계열 칸은 실적 열로 거르지 않는다(E 가 열 해를 잰다)
                     "순장부": 모.원천.get("%d" % (563 + g), {}), "감가상각비": 모.원천.get("%d" % (596 + g), {}),
                     "편입": 모.원천.get("569", {}) if g == 구["유지기준자산군"] else {}, "처분": {}})
    if 구.get("자산군제안"):
        모.주의.append("자산군을 가정 없이 묶었다 — 최근 취득원가가 큰 두 종류 + 나머지(토지 · 건설중 제외). 확정은 E · 본선")
    유 = {"자산군": 자산군, "건설중인자산": 모.원천.get("567", {}) or _확인불가, "취득약정액": 모.원천.get("568", {}) or _확인불가,
         "종류별": {k: {m: {c: t[0] * 단위배.get(t[1], 1.0) / 단위배[단위] for c, t in d.items()} for m, d in v.items()} for k, v in 모.유형원.items()},
         # 유형자산 순장부 합계(재무상태표 — 자산군 주석이 없는 회사 · 미국의 감가상각 동인 재료, 2026-10-16 S1 리뷰)
         "순장부합계": {c: round(v["유형자산"] / 단위배[단위], 6) for c, v in sorted(해.items())
                    if c.startswith("FY") and v.get("유형자산") is not None},
         # S5-17 — 회계정책의 추정 내용연수(자산 종류별 [하, 상] 년) · 상각방법. 미국은 10-K 본문의 estimated useful lives
         "내용연수": (모.내용연수 or _확인불가),
         # S5-10 · S5-15 — 유형 몫 상각(사용권 · 무형 상각 뺀 — 국내는 유형자산 주석 종류별 상각의 합(토지 · 건설중 · 사용권 · 합계 열 뺌),
         # 미국은 us-gaap:Depreciation) · 무형 상각 · 사용권 신규(리스 주석 증가)
         "상각유형": _상각검산(모, 모.유형상각 or _상각합치기(_유형상각합(모, 단위), getattr(모, "변동표상각", None))) or _확인불가,
         "상각무형": 모.무형상각 or _확인불가,
         "상각유형출처": ("미국 Depreciation 태그" if 모.유형상각 else
                      {c: t[1] for c, t in sorted((getattr(모, "변동표상각", None) or {}).items())} or "자산 종류별 상각의 합(유형자산 주석)"),
         "사용권신규": 모.사용권신규 or _확인불가,
         # 종류별 사업결합(연결범위 변동) — 편입에 넣지 않는다(S5-10). 연도별 합
         "사업결합": _종류합(모, "사업결합", 단위) or _해당없음,
         # FX-A R2(2026-10-25) — 투자부동산과 오간 대체(편입 밖 · CAPEX 밖) · 약정 주석의 모든 금액 줄(성격 후보) · 취득 약정액의 기준일 · 거슬러 찾음 ·
         # 유형자산 변동표(머리 이름 그대로 — 낯선 자산군도 살린다)
         "투자부동산대체": _종류합(모, "투자부동산대체", 단위) or _해당없음,
         "약정줄": 모.약정줄 or (("%s — 연결 주석 「약정 · 우발부채」 표에서 금액 줄을 찾지 못했다(XML 격자)" % _확인불가) if any(_문(b) for b in 보들)
                              else ("%s — 원문 XML 이 없다(약정 주석은 txt 로 읽지 않는다)" % _확인불가 if 보들 else _확인불가)),
         "취득약정근거": _취득약정근거(모, 보들),
         "변동표": 모.변동표 or (_확인불가 if not a.미국 else _해당없음)}
    # 운영 지표 — 단위를 표준으로 맞춘 뒤 합친다(2026-10-16, S1 리뷰: 표 · 문장의 단위가 달라 펄어비스 가입자수가 FY2025 4,000 ·
    # 1H26 40(만명)으로 100배 갈렸다). 이웃 기간 사이 10배 넘는 도약은 정의가 다른 값이 섞인 것으로 보고 「확인 불가」로 돌린다.
    # 화폐 단위의 「생산능력」은 물리 능력이 아니다 — `생산능력금액` 으로 이름을 바꿔 E 가 능력 동인으로 쓰지 않게 한다
    운영 = {}
    for 이름, 목록 in 모.운영.items():
        값, 단위들 = {}, []
        for x in 목록:
            배, u = 단위표준(x.get("단위"))
            if u:
                단위들.append(u)
            for c, v in x["값"].items():
                if c and v is not None:
                    값.setdefault(c, v * 배)
        if not 값:
            continue
        단 = 단위들[0] if 단위들 else ""
        키 = 이름
        if 이름 == "생산능력" and _화폐단위.search(단 or ""):
            키 = "생산능력금액"
            모.주의.append("생산능력의 단위가 화폐(%s)라 물리 능력이 아니다 — `사업지표.생산능력금액` 으로 두었다(능력 동인으로 쓰지 않는다)" % 단)
        도약 = 이웃도약(값)
        if 도약:
            모.확인불가["사업지표." + 키] = ("정의 상이 의심 — 이웃 기간 사이 %s(단위 %s · 값 %s). 공시 원문에서 같은 정의의 값만 골라 사람이 옮긴다"
                                     % (도약, " · ".join(dict.fromkeys(x.get("단위") or "공란" for x in 목록)),
                                        " · ".join("%s %s" % (c, "{:,.4g}".format(v)) for c, v in sorted(값.items()))))
            continue
        if not 단:
            모.주의.append("사업지표.%s 의 단위가 공시에서 읽히지 않았다(공란) — 원문 표의 단위 줄을 확인한다" % 키)
        운영[키] = {"단위": 단, "값": 값, "출처": " · ".join(dict.fromkeys(x["출처"] for x in 목록)),
                   "공시이름": 목록[0]["공시이름"]}
    if "면적" in 운영 and not ({"유통 · 소매", "숙박 · 운송 · 통신"} & set(유형.get("판정") or [])):
        x = 운영.pop("면적")                                  # S10-15 — 면적은 유통 · 숙박의 능력 — 그 밖 유형에서는 사무실 · 임대 면적이다
        모.주의.append("사업지표.면적(%s) — 유형(%s)이 유통 · 숙박이 아니라 사무실 · 임대 면적으로 보고 사업지표에서 뺐다(S10-15)"
                     % (x.get("공시이름"), " · ".join(유형.get("판정") or ["판정 보류"])))
    if "수주잔고" not in 운영 and 모.수주표 and 모.수주표.get("잔고합계_공시단위") is not None:
        배, u = 단위표준(모.수주표.get("단위"))
        운영["수주잔고"] = {"단위": u, "값": {모.수주표["기간"]: 모.수주표["잔고합계_공시단위"] * 배},
                         "출처": "%s 「수주상황」 표 잔고 합계(FX-A — XML 격자)" % 모.수주표["보고서"], "공시이름": "수주잔고 합계"}
    모.해당없음[:] = [x for x in 모.해당없음 if x["항목"] not in 운영]       # 공시에서 찾은 지표는 「해당 없음」이 아니다
    if 모.원천.get("541"):
        운영["직원수"] = {"단위": "명", "값": dict(모.원천["541"]), "출처": "원천행 541(%s)" % ("본사 — 직원 현황" if not a.미국 else "연결 — 10-K 표지")}
    판 = 유형["판정"]
    기대 = {"유통 · 소매": ("매장수", "면적"), "플랫폼 · 중개": ("사용자수", "거래액", "주문건수", "테이크레이트"),
           "소프트웨어 · 구독": ("사용자수", "가입자수", "ARPU"), "숙박 · 운송 · 통신": ("좌석수", "객실수", "가입자수"), "수주 산업": ("수주잔고",)}
    있어야 = {x for k in 판 for x in 기대.get(k, ())} | {"직원수"}
    보류 = []
    for 이름 in ("매장수", "면적", "사용자수", "가입자수", "직원수", "수주잔고", "좌석수", "객실수", "ARPU", "테이크레이트", "거래액", "주문건수"):
        if 이름 in 운영 or any(x["항목"] == 이름 for x in 모.해당없음):
            continue
        if "판정 보류" in 판 and 이름 not in 있어야:
            보류.append(이름)
            continue
        if 이름 in 있어야:
            모.확인불가.setdefault("사업지표." + 이름, "유형(%s)에 있어야 할 지표인데 공시(사업의 내용%s)에서 표 · 문장을 찾지 못했다" % (
                " · ".join(판), "" if not a.미국 else " — companyfacts 태그") )
        else:
            모.해당없음.append({"항목": "사업지표." + 이름, "까닭": "유형(%s)의 동인 지표가 아니다" % " · ".join(판)})
    if 보류:
        모.확인불가["사업지표(유형 판정 보류)"] = "유형을 정하지 못해 해당 여부를 가르지 않은 지표: %s — 본선이 유형을 정한 뒤 가른다" % " · ".join(보류)
    확인불가 = [{"항목": k, "원인": v} for k, v in sorted(모.확인불가.items())]
    성위치, 성문장, 성율 = 성과급원문(보들) if 보들 else (_확인불가, [], _확인불가)
    모.성과급율값 = 성율.get("값") if isinstance(성율, dict) else None
    운["회전기준별"] = 회전기준별(모) if 모.성격별 else ("%s — 성격별 비용 표가 없다(발생원가 · 재료비및경비 기준의 실적을 잴 수 없다)" % (
        _해당없음 if a.미국 else _확인불가))
    세 = 법인세블록(모, 보들, a, 판)
    세.pop("_끝", None)
    계약 = 계약시한후보(보들, 기준일=평가일 or None) if 보들 else []
    계리 = 계리임금모으기(보들) if 보들 else (모.계리 or _확인불가)
    인건비 = {"종업원급여": 모.원천.get("531", {}) or _확인불가, "퇴직급여": 모.원천.get("533", {}) or 모.원천.get("538", {}) or _확인불가,
            "복리후생비": 모.원천.get("540", {}) or 모.원천.get("534", {}) or _확인불가, "주식보상비용": 모.원천.get("546", {}) or _확인불가,
            "급여범위": "연결" if not a.미국 else _확인불가, "인원": 모.원천.get("541", {}) or _확인불가,
            "인원범위": "연결" if a.미국 else "본사", "성과급제도": 성위치,
            # S4-02 · S4-03 · S4-06 — 성과급 원문 문장 · 이익 연동 율 · 계리 가정 미래임금상승률 · 같은 범위 급여(직원 현황 1인 평균 · 별도 인건비) — 전체 시계열
            "성과급문장": 성문장, "성과급율": 성율, "계리임금상승률": 계리,
            "1인평균급여": 모.원천.get("543", {}) or _확인불가, "별도인건비": 모.원천.get("547", {}) or _확인불가,
            "531정의": "7번이 세우는 인건비 총액 — 성격별 인건비성 줄(급여 · 퇴직 · 복리후생 · 주식보상)의 합. 540 · 546 은 그 안의 내역(S4-01)"}
    기간 = sorted({c for d in 회.values() for c in [None]} - {None} | set(회) | {c for v in 원천행.values() for c in v},
                key=lambda c: (int(re.sub(r"\D", "", c)[-4:]) if c.startswith("FY") else 2000 + int(re.sub(r"\D", "", c)[-2:]), not c.startswith("FY")))
    status = "완료" if not 모.기록 or not any("상한" in x for x in 모.기록) else "부분"
    return {"회사": ((가정 or {}).get("메타") or {}).get("회사명") or a.회사 or "", "평가기준일": _평가일T or 기준일,
            "재무기준일": 평가일 or 기준일,
            "조회일": datetime.date.today().isoformat(), "유형": 유형, "status": status, "사유": "; ".join(모.기록),
            "도구판": "도구", "예산실측": {"분": round((time.time() - _시작) / 60, 2), "문서": len(보들),
                                     # 출처 종류 꼴은 모든 갈래가 같다 — {종류: 봤다 · 봤고 없었다 · 못 봤다(까닭)}(가정_스키마 「갈래 산출물」)
                                     "출처종류": ({"SEC companyfacts": "봤다", "10-K 본문": ("봤다(%s)" % " · ".join(모.미국본문["읽은"])
                                                                                       if 모.미국본문 else "못 봤다(원문 없음)")}
                                              if a.미국 else {"DART API": "봤다" if 해 else "못 봤다(응답 없음)",
                                                              "DART 원문": ("봤다(%d건)" % len(보들)) if 보들 else "못 봤다(원문 없음)"})},
            "확인불가": 확인불가, "해당없음": 모.해당없음, "주의": 모.주의 + ["같은 칸 두 출처 %s %s — %s vs %s" % (x["행"], x["열"], x["값"], x["다른값"])
                                                          for x in 모.대조 if x.get("이름") == "같은 칸 두 출처" and (not 실 or x["열"] in 실)],
            "기간": 기간, "반기연환산": {c: round(12 / (해.get(c) or {}).get("_개월", 12), 4) for c in 기간 if not c.startswith("FY")},
            "단위": 단위, "성격별비용": 성격,
            "기능별비용": ({"항목": 모.기능별, "출처": " · ".join(모.기능별출처)} if 모.기능별 else (_해당없음 if not a.미국 else _확인불가)),
            "사업지표": 운영, "인건비": 인건비, "유형자산": 유, "운전자본": 운, "법인세": 세,
            # S6-13 — 법령이 아니라 계약이 끝을 정한 돈의 후보(경영상의 주요계약) — F `계약시한[]` 이 옮기고 본선이 한시적 현금흐름으로 붓는다
            "계약시한후보": 계약 or ("%s — 「경영상의 주요계약」 절에서 끝나는 날이 적힌 계약 줄을 못 찾았다" % _확인불가 if 보들 else
                                ("%s — 원문 없음(미국은 10-K Item 1 · commitments 주석 · Exhibit 10 의 계약 만료를 본선이 본다)" % _확인불가)),
            # S5-19 · S5-20 — 공시 투자계획 표(총투자 · 기투자 · 향후투자 · 기간 · 효과)와 투자 규모 발화(공정공시 · 신규시설투자 제목) — F 가 CP1 에서 읽는다
            "투자계획": ({"표": 모.투자계획, "발화": 모.투자발화, "진행중": 모.투자진행} if (모.투자계획 or 모.투자발화 or 모.투자진행) else
                     (_확인불가 if not a.미국 else _해당없음)),
            # FX-A R1 — 읽은 원문(종류 · 기간 끝 · 정정 · 서식 판 · 기준일 보고서인가) · 못 읽고 버린 본문 파일
            "원문읽음": 원문읽음, "원문버림": 모.원문버림, "원문경보": 원문경보,
            # FX2-A R14 — 출처 시점 대표값(조사축적 넣기의 「출처」 날짜): 기준일 보고서(없으면 기준일 이전 가장 늦은 원문)의 기간 끝 · 제출일. 「뒤」 역할은 뺀다
            "출처시점": 출처시점,
            # FX-A R2 · R3 — 생산능력 표(품목 · 단위 · 기간 값 · 산출기준) · 수주상황 표(품목 · 수주총액 · 기납품 · 잔고)
            "생산능력표": 모.생산능력표 or (("%s — 사업의 내용 「생산능력」 표를 찾지 못했다(XML 격자)" % _확인불가) if any(_문(b) for b in 보들)
                                       else (_해당없음 if a.미국 else "%s — 원문 XML 이 없다" % _확인불가)),
            "수주잔고표": (모.수주표 or {}).get("줄") or (_해당없음 if a.미국 else "%s — 사업의 내용 「수주상황」 표를 찾지 못했다(XML 격자)" % _확인불가),
            "수주잔고요약": ({k: v for k, v in 모.수주표.items() if k != "줄"} if 모.수주표 else None),
            "수주잔고문장": 모.수주문장,
            # 해당 없음은 **지금** 목록으로 본다 — 위에서 공시로 찾은 지표(생산능력 따위)를 해당 없음에서 걷었다(S2-13 · 종전엔 걷기 전 목록으로
            # 「생산능력 해당 없음 → 판매량 해당 없음」을 냈다 — 오이솔루션 실측: 생산능력 2,160 이 있는데 판매량공시가 「해당 없음」)
            "판매량공시": 판매량칸(모, 보들, {x["항목"] for x in 모.해당없음}, a),
            "판가공시": 공시칸(모.판가, 보들, a, "제품 가격변동추이", "주요 제품 등의 가격변동추이"),
            "가동률공시": (_해당없음 if "생산능력" in {x["항목"] for x in 모.해당없음} and not 모.가동률
                       else 공시칸(모.가동률, 보들, a, "생산실적 · 가동률", "생산실적 및 가동률")),
            "원천행": 원천행, "원천근거": 근거,
            "재무시계열": {c: dict({k: round(v[k] / 단위배[단위] * (1.0 if a.미국 else 1.0), 6) for k in ("매출", "매출원가", "판관비", "영업이익", "유형자산", "재고") + _API흐름
                                    if v.get(k) is not None}, **_CAPEX구성칸(v, 모, c, 단위)) for c, v in sorted(해.items())},
            "구조": {"원가줄": 구["원가줄"], "자산군대응": {"%d" % k: v for k, v in 구["자산군대응"].items()},
                   "유지기준자산군": 구["유지기준자산군"], "재고변동반영": 구["재고변동반영"], "단일표시": 구["단일표시"]},
            "기록": {"도구": "스크립트/동인원천.py", "읽은 원문": [b.글() for b in 보들], "알림": 모.기록,
                   "걸린 시간(초)": round(time.time() - _시작, 1)}}


def _CAPEX구성칸(v, 모, c, 단위):
    """재무시계열 한 열의 `CAPEX구성` 칸(목표 단위) — 유형취득 · 자산군별 · 무형취득 · 개발비자본화 · 사업결합 · 투자부동산대체 · 미지급설비증감 ·
    비현금취득(FX-A · R8 재료). 재료가 하나도 없으면 빈 사전(칸을 만들지 않는다)."""
    구 = v.get("_CAPEX구성") or {}
    f = 1.0 / 단위배[단위]
    d = {}
    if v.get("CAPEX") is not None:
        d["유형취득"] = round(v["CAPEX"] * f, 6)
    if 구.get("자산군별"):
        d["자산군별"] = {k: round(x * f, 6) for k, x in sorted(구["자산군별"].items())}
    for k, 키 in (("무형취득", "무형취득"), ("개발비자본화", "개발비자본화"), ("사업결합", "사업결합취득"), ("투자부동산취득", "투자부동산취득")):
        x = v.get(키) if 키 in ("무형취득", "사업결합취득") else 구.get(키)
        if x is not None:
            d[k] = round(x * f, 6)
    투 = (_종류합(모, "투자부동산대체", 단위) or {}).get(c)
    if 투 is not None:
        d["투자부동산대체"] = 투
    비 = (모.비현금 or {}).get(c) or {}
    d["미지급설비증감"] = 비.get("미지급설비증감")
    d["비현금취득"] = 비.get("비현금취득")
    if v.get("_CAPEX출처"):
        d["유형취득출처"] = v["_CAPEX출처"]
    if not [k for k, x in d.items() if x is not None]:
        return {}
    return {"CAPEX구성": d}


def _취득약정근거(모, 보들):
    """568(유형자산을 취득하기 위한 약정액)의 기준일 · 출처 · 거슬러찾음(기준일 보고서에 없어 직전 사업보고서 값을 쓴다 — F5 #3)."""
    d = 모.원천.get("568") or {}
    if not d:
        설 = [x for x in (모.약정줄 or []) if x.get("성격후보") == "설비취득"]
        return ({"기준일": 설[0]["기준일"], "출처": 설[0]["출처"], "거슬러찾음": bool(설[0].get("거슬러찾음")), "값": None,
                 "주": "568 줄 이름으로는 못 찾았다 — 약정 주석의 설비 취득 성격 줄 %d개(약정줄)" % len(설)} if 설 else _확인불가)
    끝열 = max(d, key=_열때)
    늦은 = max((b for b in 보들 if b.끝), key=lambda b: b.끝, default=None)
    기준열 = 늦은.열("당", 흐름=False) if 늦은 else None
    return {"기준일": 끝열, "값": d[끝열], "출처": ((모.출처.get("568") or {}).get(끝열) or ("", 0))[0],
            "거슬러찾음": bool(기준열 and 끝열 != 기준열)}


def _종류합(모, 측정, 단위, 뺄=("합계", "토지", "건설중")):
    """종류별 측정(취득 · 대체 · 사업결합 · 상각)의 열별 합 — 합계 · 토지 · 건설중 열은 뺀다. 그 열에 값이 하나도 없으면 빈 사전."""
    합 = {}
    for 종류, 측정들 in 모.유형원.items():
        if _유형열(종류) in 뺄 or "합계" in 종류 or 종류 in ("유형자산", "계"):
            continue
        for c, t_ in (측정들.get(측정) or {}).items():
            합[c] = 합.get(c, 0.0) + abs(t_[0]) * 단위배.get(t_[1], 1.0) / 단위배[단위]
    return {c: round(v, 6) for c, v in sorted(합.items())}


def _상각검산(모, 상):
    """FX4-F D1 — 유형 몫 상각(자산 종류별 상각의 합)을 같은 기간의 총 상각(579 — 유형 + 사용권 + 무형)에 대 본다. 유형 몫 ÷ 579 가 0.05 ~ 1.02 밖이면
    그 기간은 자릿수(원 · 천원 · 백만원) · 열(감가상각 ↔ 손상 · 대체) · 표(남의 회사 · 별도 · 종속회사 주석)가 어긋난 것이라 내지 않고 `주의` 에 적는다.
    579 가 없는 기간은 순장부 유형자산에 대 본다(상각 ÷ 순유형 0.003 ~ 0.8). 대 볼 것이 없으면 그대로 둔다."""
    if not 상:
        return 상
    총 = 모.원천.get("579") or {}
    낸, 뺀 = {}, []
    for c, v in 상.items():
        t = 총.get(c)
        if t:
            r = (v or 0.0) / t
            if 0.05 <= r <= 1.02:
                낸[c] = v
            else:
                뺀.append("%s(유형 몫 %.0f ÷ 총 상각 %.0f = %.3f)" % (c, v or 0.0, t, r))
            continue
        낸[c] = v
    if 뺀:
        모.주의.append("유형 몫 상각 검산 — 총 상각(579)과 어긋나 뺀 기간: %s — 자산 종류별 표의 자릿수 · 열 · 출처(별도 · 종속회사 표)를 본다(FX4-F D1)"
                     % " · ".join(뺀))
    return 낸


def _상각합치기(종류합, 변동):
    """기간마다 변동 표 합계 열의 감가상각(`변동표상각들`)이 자산 종류별 합보다 앞선다(FX4-F D1)."""
    낸 = dict(종류합 or {})
    for c, t in (변동 or {}).items():
        낸[c] = t[0]
    return {c: 낸[c] for c in sorted(낸)}


def _유형상각합(모, 단위):
    """국내 — 유형자산 주석 종류별 상각의 합(사용권 열 뺌). 사용권 · 무형 상각이 섞인 579 대신 E 감가상각 노드가 읽는다(S5-10 · S5-17)."""
    합 = {}
    for 종류, 측정들 in 모.유형원.items():
        if _유형열(종류) in ("합계", "토지", "건설중") or "합계" in 종류 or "사용권" in 종류 or 종류 in ("유형자산", "계"):
            continue
        for c, t_ in (측정들.get("상각") or {}).items():
            합[c] = 합.get(c, 0.0) + abs(t_[0]) * 단위배.get(t_[1], 1.0) / 단위배[단위]
    return {c: round(v, 6) for c, v in sorted(합.items())}


def 견주기(낸, 가정경로):
    """그 가정 파일의 원천과 같은 칸 같은 값인지 — {같음, 다름, 새칸(도구만), 빠짐(가정만)} (이 도구가 맡는 5xx 행만)."""
    g = json.load(io.open(가정경로, encoding="utf-8"))
    원 = g.get("원천") or {}
    결과 = {"같음": [], "다름": [], "새칸": [], "빠짐": []}
    소유 = re.compile(r"5[34]\d|5[5-7]\d|59[7-9]")         # 이 도구가 맡는 줄(531~549 · 551~579 · 597~599) — 581~596(기준 기간 · 환율)은 아니다
    행들_ = sorted({k for k in 원 if 소유.fullmatch(k)} | {k for k in 낸["원천행"] if 소유.fullmatch(k)}, key=int)
    for 행 in 행들_:
        a, b = 낸["원천행"].get(행) or {}, 원.get(행) or {}
        for 열 in sorted(set(a) | set(b)):
            if 열 == "기준기간":
                continue
            if 열 in a and 열 in b:
                (결과["같음"] if abs(a[열] - float(b[열])) <= 0.5 else 결과["다름"]).append((행, 열, a[열], b[열]))
            elif 열 in a:
                결과["새칸"].append((행, 열, a[열], None))
            else:
                결과["빠짐"].append((행, 열, None, b[열]))
    return 결과


def 가정두날(가정):
    """가정 → (재무기준일 F, 평가기준일 T) 글 — `기준일.py` 로 푼다(메타.재무기준일이 없으면 F = T · 옛 가정은 지금과 같다).
    가정이 없거나 날이 없으면 ('', ''). 날짜 꼴이 아니면 메타의 글을 그대로(옛 동작)."""
    m = ((가정 or {}).get("메타") or {}) if isinstance(가정, dict) else {}
    if not m.get("평가기준일"):
        return ("%s" % (m.get("재무기준일") or "")), ""
    try:
        import 기준일 as _기                                    # noqa: PLC0415
        return _기.재무기준일(가정).isoformat(), _기.평가기준일(가정).isoformat()
    except Exception:                                            # noqa: BLE001
        return ("%s" % (m.get("재무기준일") or m.get("평가기준일") or "")), "%s" % m.get("평가기준일")


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="13번 5xx(원가 동인의 원천)와 동인 시계열을 공시 원문 · API 에서 조립 — A3 동인원천(업종 중립)")
    ap.add_argument("--원천폴더", nargs="*", help="원문 txt · DART 응답이 든 폴더(여럿). 기본 _raw")
    ap.add_argument("--가정", help="구조(원가 줄 · 자산군 · 유지 기준 자산군 · 재고 변동 반영) · 실적 열 · 금액 단위를 읽을 가정 파일")
    ap.add_argument("--회사", default=None, help="머리의 회사 이름(가정이 없을 때)")
    ap.add_argument("--원가줄", help="원가 줄 대응 「1=나머지;5=성격」 — 기본: 실적이 공시인 줄이 하나면 나머지, 여럿이면 모두 성격. "
                                   "가정이 없으면 비용 표시로 정한다(기능별 = 1 나머지 · 단일 표시 = 5 · 6 성격 + 7 나머지)")
    ap.add_argument("--자산군", help="자산군 대응 「1=기계장치;2=나머지」 — 기본: 구조.투자.자산군의 이름(「… 등」은 나머지), 가정이 없으면 "
                                   "최근 취득원가가 큰 두 종류 + 나머지")
    ap.add_argument("--단위", default=None, help="13번 원천의 금액 단위(기본: 가정의 메타.금액단위, 없으면 백만원)")
    ap.add_argument("--기준일", "--재무기준일", dest="기준일", default=None,
                    help="재무기준일 F — 원천근거 둘째 칸 · 기준일 보고서(기본: 가정의 재무기준일, 없으면 읽은 보고서의 가장 늦은 기간 끝날)")
    ap.add_argument("--미국", help="미국 — companyfacts.json 경로(원문 대신)")
    ap.add_argument("--원천통화단위", default="달러", help="미국 — 13번 금액 단위가 그 통화의 무엇인가(달러 · 천달러 · 백만달러). --단위 와 짝")
    ap.add_argument("--받기", action="store_true", help="실적 열에 필요한 과거 해의 사업보고서 원문이 없으면 받는다 — 보충일 뿐이다. 원문의 주인은 A1"
                                                     "(`dart_fetch.py` 통째로 받기가 기준일 보고서 · 최신 · 과거 사업보고서를 받는다) — 같은 함수(dart_fetch.원문)로 "
                                                     "이미 받은 접수번호는 건너뛴다(OPENDART_API_KEY · 제출이력)")
    ap.add_argument("--해수", type=int, default=6, help="--받기 때 갖출 관측 회계연도 수(기본 6 — 동인진단은 다섯 해 이상이면 「실측」)")
    ap.add_argument("--상한분", type=float, default=None, help="벽시계 상한(분) — 기본 국내 10 · 미국 12")
    ap.add_argument("--대조", help="이 가정 파일의 원천(5xx)과 같은 칸 같은 값인지 견준다(회귀 확인)")
    ap.add_argument("-o", "--출력", default=None, help="기본 <첫 원천폴더>/동인원천.json")
    a = ap.parse_args()
    if a.상한분 is None:
        a.상한분 = 12.0 if a.미국 else 10.0
    if a.미국 and not a.단위:
        a.단위 = "원"           # 미국은 「원」 자리에 통화 단위 그대로(배 = 1) — 13번이 달러면 --단위 원 --원천통화단위 달러
    낸 = 조립(a)
    밖 = a.출력 or os.path.join(os.path.abspath((a.원천폴더 or [os.path.join(ROOT, "_raw")])[0]) if not a.미국 else os.path.dirname(os.path.abspath(a.미국)),
                              "동인원천.json")
    os.makedirs(os.path.dirname(os.path.abspath(밖)), exist_ok=True)

    def 쓰기():
        with io.open(밖, "w", encoding="utf-8", newline="\n") as f:
            json.dump(낸, f, ensure_ascii=False, indent=1, default=str)
            f.write("\n")
    쓰기()
    print("동인원천 — %s" % 밖)
    print("  유형 %s — %s" % (" · ".join(낸["유형"]["판정"]), " · ".join(x["문장 요약"] for x in 낸["유형"]["근거"])[:200]))
    print("  읽은 원문 %d · 원천행 %d줄 %d칸 · 확인 불가 %d · 해당 없음 %d · %.1f초" % (
        len(낸["기록"]["읽은 원문"]), len(낸["원천행"]), sum(len(v) for v in 낸["원천행"].values()), len(낸["확인불가"]), len(낸["해당없음"]),
        낸["기록"]["걸린 시간(초)"]))
    for 행, v in 낸["원천행"].items():
        print("  %-4s %s" % (행, " · ".join("%s %s" % (c, "{:,.0f}".format(x)) for c, x in v.items())))
    for x in 낸["해당없음"]:
        print("  해당 없음 %s — %s" % (x["항목"], x["까닭"]))
    for x in 낸["확인불가"]:
        print("  확인 불가 %s — %s" % (x["항목"], x["원인"]))
    for x in 낸["주의"]:
        print("  주의 %s" % x)
    rc = 0
    if a.대조:
        견 = 견주기(낸, a.대조)
        print("── 대조: %s — 같음 %d · 다름 %d · 새 칸(도구만) %d · 빠짐(가정만) %d" % (
            os.path.basename(a.대조), len(견["같음"]), len(견["다름"]), len(견["새칸"]), len(견["빠짐"])))
        for 종류 in ("다름", "빠짐", "새칸"):
            for 행, 열, x, y in 견[종류]:
                print("  %s %s %s — 도구 %s · 가정 %s" % (종류, 행, 열, "-" if x is None else "{:,.2f}".format(x),
                                                    "-" if y is None else "{:,.2f}".format(float(y))))
        낸["대조결과"] = {k: [list(t) for t in v] for k, v in 견.items()}
        쓰기()
        rc = 1 if 견["다름"] else 0
    sys.exit(rc)


if __name__ == "__main__":
    main()

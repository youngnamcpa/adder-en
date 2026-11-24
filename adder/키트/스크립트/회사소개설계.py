# -*- coding: utf-8 -*-
"""회사소개설계 — 3분 레터 회사 소개(첫머리)를 무엇을 어떤 차례로 말할지 코드가 사실 카드에서 짓는다(레터 문체 3단계 B5 · 2026-10-26).

왜 있나
    레터 문장이 원천과 뜻이 어긋나는 일은 문장이 사실을 다시 말하는 순간 생긴다. 그래서 사실은 문장 밖 카드에 먼저 적고(`카드.py`),
    **무엇을 어떤 차례로 말할지는 코드가 카드의 유무 · 등급 · 장부와 시세를 보고 정한다.** 작가(LLM)는 이 설계를 문장으로 옮기기만 한다
    (연구/레터_문체체계_독립설계안_20261026.md 3-2 ③ · 4절 · 5절 — 실험에서 설계를 v1 → v2 로 고친 차례를 따른다).
    이 파일은 카드를 고치지 않는다. 카드의 꼴은 `카드.py`, 셈한 카드는 `카드_계산.py` 가 정한다.

짓는 것(산출 `_raw/회사소개설계.json`)
    긴장      설계안 4-3 표의 일곱 꼴 가운데 하나를 계산 카드(영업이익률 시계열 · 주가 경로)에서 고른다. 판정에 쓴 카드 id 와 숫자,
              물음의 「방향」만 낸다(문형은 작가 — 모든 레터에 서는 자리의 문형을 정하면 수백 레터가 같은 문장으로 시작한다)
    다섯 수   1 정체와 생활 접점 → 2 긴장(실적 · 주가 · 물음 한 번) → 3 이익을 끌어올린 힘과 돈을 내는 쪽 → 4 끌어내릴 수 있는 힘 →
              5 평가가 보는 숫자와 질문. 수마다 카드 다섯 장 안. 카드의 「수」(또는 갈래가 남긴 「_수」) 칸이 있으면 그 목록 안에서만 놓고,
              없으면 등급 · 계산 카드의 꼴 · 풀이용어 · 고유명사 · 낱말로 고른다. 여러 수를 적은 카드는 앞 수부터 지원하고 수가 차례로
              고른다(지연 수락 — 밀린 카드는 다음 수로)
    3분 층    등급의 「3분」이 거짓인 카드 · 층제한에 3분이 있는 카드는 뺀다. 평가기준일 뒤 카드는 **뺀다** — 「평가기준일 뒤 · 반영하지 않음」
              표지를 붙여 따로 두고(날짜 문단 · 본편이 쓸 수 있게) 수에는 넣지 않는다. 까닭은 아래 「평가기준일 뒤」
    경로      주가 경로 카드의 꺾임 가운데 3분 레터에 실을 점을 고른다. 아래 「경로 문턱」
    반드시 풀이 문서의 결론에_나오는_용어와, 고른 카드가 쓰는 용어(어느 카드의 풀이용어인 말)를 처음 나오는 수와 함께 낸다. 풀이 카드는
              그 수로 당겨 넣는다(카드의 수 칸 밖이어도 — 용어는 처음 나오는 자리에서 푼다). 풀이 카드가 없으면 「풀이 카드 없음」.
              풀이용어로 적히지 않은 영문 약어는 「풀이 후보」로 따로 낸다(낱말로 주운 것 — 경고)
    분량      1,000~1,300자(A-1). 수마다 글자 · 문장 예산을 카드 수로 나눈다(카드 한 장 40~90자). 카드가 모자라 상한을 다 더해도 하한에 못 미치면
              「하한 미달」 — 그 첫머리는 서지 않는다
    물러서기  필요한 카드가 없으면 그 수의 문장을 빼고 까닭을 적는다(설계안 4-4). 고객 이름이 없으면 고객 산업 · 지역으로, 업계 화제가 없으면
              실적 변화 자체를 화제로(수 2), 경쟁사 이름이 없으면 점유율 · 과점 서술로, 비상장이면 주가 없이 실적 방향만
    지을 카드 비어 있는 자리에 어느 만든 곳(p · g · j · r)이 어떤 카드를 지으면 서는지

긴장 판정(설계안 4-3)
    이익 — 바탕은 누계 · 전년 같은 기간 → 분기 · 전년 같은 분기 → 연간 · 앞 해 차례로 처음 서는 것. 영업이익률 차를 앞 기간 이익률로 나눈
           상대 폭(분모는 5% 아래로 내리지 않는다)이 10% 넘으면 「약함」, 25% 넘으면 「뚜렷」. 이익률이 없으면 영업이익 증감률로. 나머지 바탕은
           보조 근거 — 방향이 엇갈리면 「엇갈림」에 적는다
    주가 — 창 = 평가기준일이 든 해의 첫 거래일(평가기준일까지 120일이 안 되면 시세 첫날) ~ 평가기준일. 창 안 최고에서 평가기준일까지
           문턱 넘게 내렸으면 ↓, 창 시작에서 문턱 넘게 올랐으면 ↑. 문턱의 두 배를 넘으면 「뚜렷」. 문턱은 경로 문턱과 같다
    차례 — 주가 카드 없음 → 「주가 없음(비상장)」(하위 꼴은 실적 방향) · 최근 영업이익 < 0 또는 매출 0 → 「적자 · 매출 전」 ·
           매출 정체(최근 여섯 해 이하의 연율 |g| ≤ 5%) · 이익률 안정(표준편차 ≤ 2%p 또는 평균의 10%) 이고 주가가 「뚜렷」하지 않으면
           「성장 없는 성숙」(성숙은 여러 해의 성질이고 주가의 한 해 움직임이 크지 않으면 그것이 평가의 물음을 정한다) · 나머지는 이익 × 주가.
           한 축이 「미미」(문턱 아래)면 확신을 낮추고 반대 꼴을 대안으로 적는다

경로 문턱 — B2 가 넘긴 문제(3단계 계획 9절) · 시험대 세 회사로 정함(연구/문체3단계_20261026/B5_보고.md 4절)
    회사마다 고정 문턱이 아니라 **변동성에 비례**한다 — 문턱 = max(카드 문턱, 한 달 변동폭). 한 달 변동폭 = 평가기준일까지 최근 252거래일의
    하루 로그 등락 표준편차 × √21. 카드 문턱(카드_계산 기본 20%)이 바닥인 까닭은 그보다 작은 꺾임이 카드에 없기 때문이다(카드에 없는 점은
    작가가 쓸 수 없다). 고르는 규칙 —
      ① 긴장의 기점 = 창 안 최고(주가 ↓) · 창 안 최저(주가 ↑). 기점 뒤 경로가 긴장 그 자체라 문턱 넘는 꺾임을 모두 싣는다
      ② 기점 앞은 한 움직임으로 묶는다. 문턱의 두 배를 넘는 되돌림만 싣는다. 창 시작이 기점과 문턱 안이면 기점이 시작이다
      ③ 창 안 최고 · 최저는 늘 싣는다. 끝의 꺾임이 평가기준일과 문턱 안이면(미확정 꺾임 포함) 평가기준일로 합친다
      ④ 경로 카드의 필수 한정 「경로」가 있는데 고른 점이 한 방향뿐이면 카드의 꺾임에서 가장 큰 되돌림 한 쌍을 되돌려 넣는다
    시세 파일을 못 읽으면 카드 문턱만 쓴다(그 사실을 적는다).

평가기준일 뒤 카드를 빼는 까닭
    ① 긴장은 평가가 쓴 정보로 판정해야 물음이 이 평가의 물음이 된다 ② 카드설정의 「회사 발화 — 평가기준일까지만」 원칙을 모든 등급에
    ③ 1,000~1,300자 안에서 표지 문장 하나가 40~80자와 날짜 둘을 먹는다 ④ 옛 회차 3분 레터가 평가기준일 뒤 하락을 한 하락 구간으로 묶은
    사고(문체 2단계 8절) — 섞일 자리를 없앤다. 그래도 독자가 지금 보는 가격과 잇는 정보이므로 「평가기준일뒤」 칸에 표지와 함께 남긴다.
    단 공시 · 계산 카드가 사건일 없이 공표일만 평가기준일 뒤이고 기간(「2026년 상반기」 같은 말)이 재무기준일 안에서 끝나면 보고 기간의 사실로
    보고 되살린다(평가기준일 = 재무기준일인 회차는 반기보고서 공표일이 늘 평가기준일 뒤다 — 카드.기준일뒤 는 공표일로 판정한다)

쓰는 법
    python 스크립트/회사소개설계.py <회차 폴더>                    # _raw/사실카드.json(없으면 _raw/카드/*.json) → _raw/회사소개설계.json
    python 스크립트/회사소개설계.py <카드.json> [<카드.json> …] --낼 경로.json [--회차 폴더] [--시세 레터_주가.csv]
    여러 조각은 `카드.합치기` 와 같은 규칙으로 합쳐 읽는다(회사 · 평가기준일 · 재무기준일이 같아야 하고 id 가 겹치면 안 된다 · 함정 메모 ·
    결론에_나오는_용어 · 못지음을 모은다). 회사 이름은 법인 표기(「(주)」 · 「㈜」 · 「, Inc.」 …)를 떼고 견준다(조각마다 꼴이 달랐다 — 경고로 남김).
    「카드」 칸이 없고 「없음」 칸이 있는 문서(공시 갈래의 「없음」 기록)는 물러서기의 근거로만 읽는다.
    종료 코드 — 0 지음 · 1 지었으나 꼴 오류 카드를 빼고 지음 · 2 입력 오류(쓰지 않음)

회사 · 업종 이름은 이 파일에 없다.
"""
from __future__ import annotations

import argparse
import ast
import datetime as _dt
import glob
import io
import json
import math
import os
import re
import sys
from fractions import Fraction

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
import 카드 as K            # noqa: E402
import 카드_계산 as KC      # noqa: E402

판 = "회사소개설계 v1"
형식 = "회사소개설계 1"
산출 = os.path.join("_raw", "회사소개설계.json")

# ══════════════════════════════════════════════════════ 0. 설정 — 결정 · 문턱이 바뀌면 여기만 고친다

분량 = {"하한": 1000, "상한": 1300}             # A-1(2026-10-26 확정 · 독립 설계안 7-1)
문장상한 = 24                                    # 설계안 4-2 「전체 문장 스물넷 안」
수당카드 = 5                                     # 설계안 4-2 「수마다 카드 다섯 장 안」
카드당글자 = (40, 90)                            # 카드 한 장 ≈ 한 문장 안팎(실험 A2 약 60자)
문장셈 = {"상한": 55, "하한": 70}                # 글자 ÷ 이 값 = 문장 수(상한은 짧은 문장으로, 하한은 긴 문장으로 셈)
물음몫 = 1                                       # 수 2 의 물음 문장 — 카드 한 장 몫으로 센다
이익문턱 = {"약함": Fraction(1, 10), "뚜렷": Fraction(1, 4), "최소폭": Fraction(1, 100), "분모바닥": Fraction(5, 100)}
성숙문턱 = {"매출연율": 0.05, "이익률편차": 0.02, "이익률편차비": 0.10, "최소해": 4, "볼해": 6}
주가설정 = {"창최소일": 120, "변동성일": 252, "변동성최소": 40, "한달": 21, "앞구간배수": 2, "뚜렷배수": 2}

긴장표 = [   # 설계안 4-3 — 꼴 · 판정 재료 · 물음의 방향(문형은 작가가 정한다)
    {"꼴": "이익 ↑ · 주가 ↓", "재료": "최근 영업이익률 상승 · 주가 고점 대비 큰 하락",
     "방향": "이익이 최대인데 왜 시장은 등을 돌렸나 → 지금 이익이 얼마나 오래가나"},
    {"꼴": "이익 ↑ · 주가 ↑", "재료": "둘 다 상승", "방향": "이미 오른 주가가 무엇을 담았나"},
    {"꼴": "이익 ↓ · 주가 ↓", "재료": "둘 다 하락", "방향": "어디까지 내려가나, 바닥을 무엇으로 알아보나"},
    {"꼴": "이익 ↓ · 주가 ↑", "재료": "이익 하락 · 주가 상승", "방향": "시장은 무엇을 미리 보나"},
    {"꼴": "적자 · 매출 전", "재료": "영업손실 · 매출 없음", "방향": "언제 돈을 벌고, 그때까지 현금이 버티나"},
    {"꼴": "성장 없는 성숙", "재료": "매출 정체 · 이익률 안정", "방향": "성장 없이 무엇으로 값이 나오나(배당 · 가격 결정력)"},
    {"꼴": "주가 없음(비상장)", "재료": "—", "방향": "실적의 방향만으로 고른다"},
]
긴장꼴 = {x["꼴"]: x for x in 긴장표}

수표 = {     # 설계 v2(연구/문체독립설계_20261026 의 v2 설계 파일)의 차례를 업종 말 없이
    1: {"이름": "정체와 생활 접점", "할 일": "무엇을 파나, 독자는 그것을 어디서 만나나, 무엇이 돈을 버나(매출 비중)",
        "등급순": ["공시", "계산", "일반설명", "회사 발화", "고객사 · 협력사 발표", "레터정의", "평가판단"]},
    2: {"이름": "긴장", "할 일": "실적과 주가를 비교 기준과 함께(얼마에서 얼마로, 언제와 견줘), 물음은 한 번",
        "등급순": ["계산", "공시", "회사 발화", "평가판단", "레터정의", "고객사 · 협력사 발표", "일반설명"]},
    3: {"이름": "이익을 끌어올린 힘과 그 돈을 내는 쪽", "할 일": "업계의 변화와 회사의 자리, 대표 고객사의 발표, 고객 집중도와 지역",
        "등급순": ["공시", "계산", "고객사 · 협력사 발표", "회사 발화", "일반설명", "평가판단", "레터정의"]},
    4: {"이름": "이익을 끌어내릴 수 있는 힘과 하락의 정황", "할 일": "회사가 적은 업종의 방식(반대 진술까지), 경쟁사와 증설, 평가가 가르지 못한 원인",
        "등급순": ["공시", "평가판단", "회사 발화", "계산", "고객사 · 협력사 발표", "일반설명", "레터정의"]},
    5: {"이름": "평가가 보는 숫자와 질문", "할 일": "평가가 쓰는 숫자의 정의와 지금 값, 정상 수준, 이 평가의 질문",
        "등급순": ["레터정의", "평가판단", "공시", "계산", "일반설명", "회사 발화", "고객사 · 협력사 발표"]},
}
이름바꿈 = {   # 긴장 꼴에 따라 수 3 · 4 의 이름만 바꾼다(할 일은 같다)
    "↓": {3: "이익을 받치는 힘과 그 돈을 내는 쪽", 4: "이익을 끌어내린 힘과 하락의 정황"},
    "성숙": {3: "이익을 지키는 힘(가격 결정력 같은 것)과 그 돈을 내는 쪽", 4: "이익을 줄일 수 있는 힘"},
}
낱말 = {       # 수마다 그 수의 일을 하는 카드에 흔한 말(업종 말 없음) — 같은 등급 안에서 차례를 가른다
    1: r"주력|제품|판매|판다|만든|만들|쓰이|쓰인|용도|서비스|사업|매출|비중|운영",
    2: r"매출|영업이익|이익률|주가|종가|사상 최대|최고|최저",
    3: r"수요|가격|출하|판매|고객|매출처|지역|점유율|시장|성장|공급|수주|투자",
    4: r"경기|변동|경쟁|과점|공급|위험|환율|규제|증설|하락|감소|줄어|줄었|불황|계약|수급|소송|대체",
    5: r"정의|정상|부르|부른|원재료|생산능력|가동률|단위|질문|기준으로",
}
역할말 = {
    "정체": r"주력|주된 제품|주요 제품|사업은|사업을|을 판다|를 판다|만드는 회사|운영하는|운영한다",
    "비중": r"비중|차지|가운데",
    "실적": r"매출|영업이익|이익률|순이익|주가|종가",
    "돈": r"고객|매출처|지역|소재지|점유율|판매 경로|판매경로|직판|대리점",
    "고객": r"고객|매출처",
    "지역": r"지역|소재지",
    "점유율": r"점유율",
    "경쟁": r"점유율|과점|경쟁",
    "하락원인": r"가를 수 없|가르지 못|단정하지 못|단정할 수 없|단정",
    "질문": r"질문",
    "안풂": r"풀지 않|풀이는 일반설명|뜻을 적지 않",
}
독자약어 = {"AI", "IT", "PC", "TV", "USB", "CEO", "CFO", "GDP", "OK", "SNS", "IR", "ESG", "FY", "Q", "IPO", "M&A"}
통화약어 = set(KC.통화말)


class 입력오류(Exception):
    pass


# ══════════════════════════════════════════════════════ 1. 숫자 · 날짜

def _날(s):
    try:
        return _dt.date.fromisoformat(str(s)[:10])
    except (TypeError, ValueError):
        return None


_식함수 = {"abs": abs, "min": min, "max": max, "sum": sum}


def 식값(식):
    """카드 계산 칸의 식 → 정확한 분수(숫자 · 사칙 · min · max · abs · sum 만). 못 셈하면 None."""
    try:
        나무 = ast.parse(str(식), mode="eval")
    except SyntaxError:
        return None

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
            return Fraction(str(n.value))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
            v = ev(n.operand)
            return -v if isinstance(n.op, ast.USub) else v
        if isinstance(n, ast.BinOp):
            a, b = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Add):
                return a + b
            if isinstance(n.op, ast.Sub):
                return a - b
            if isinstance(n.op, ast.Mult):
                return a * b
            if isinstance(n.op, ast.Div):
                return a / b
            raise ValueError("연산")
        if isinstance(n, (ast.List, ast.Tuple)):
            return [ev(x) for x in n.elts]
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in _식함수 and not n.keywords:
            return _식함수[n.func.id](*[ev(a) for a in n.args])
        raise ValueError("꼴")

    try:
        v = ev(나무)
    except (ValueError, ZeroDivisionError, TypeError):
        return None
    return v if isinstance(v, Fraction) else None


_단위수 = {"조": 10 ** 12, "억": 10 ** 8, "만": 10 ** 4}


def 금액수(글_):
    """「131.90조 원」 · 「7,195억 원」 · 「291만 9,000원」 · 「71.95달러」 → 기본 단위의 분수. 못 읽으면 None."""
    t = str(글_ or "").strip().replace("−", "-").replace(",", "")
    부 = -1 if t.startswith("-") else 1
    t = t.lstrip("+-").strip()
    m = re.fullmatch(r"((?:\d+(?:\.\d+)?\s*(?:조|억|만)?\s*)+)([가-힣]+)", t)
    if not m:
        return None
    합 = Fraction(0)
    for 수, 단 in re.findall(r"(\d+(?:\.\d+)?)\s*(조|억|만)?", m.group(1)):
        합 += Fraction(수) * _단위수.get(단, 1)
    return 부 * 합


def 비수(글_):
    """「+32.65%p」 · 「−54.71%」 · 「74.42%」 → 비 · 「5.89배」 → 배. → (수, 꼴) · 못 읽으면 (None, None)."""
    t = str(글_ or "").strip().replace("−", "-").replace(",", "")
    m = re.fullmatch(r"([+-]?\d+(?:\.\d+)?)%p", t)
    if m:
        return Fraction(m.group(1)) / 100, "포인트"
    m = re.fullmatch(r"([+-]?\d+(?:\.\d+)?)%", t)
    if m:
        return Fraction(m.group(1)) / 100, "비율"
    m = re.fullmatch(r"([+-]?\d+(?:\.\d+)?)배", t)
    if m:
        return Fraction(m.group(1)), "배"
    return None, None


def 퍼(fr, 자리=1, 부호=False):
    return KC.퍼글(fr, 자리, 부호) if fr is not None else None


def 포(fr, 자리=1):
    return KC.포글(fr, 자리) if fr is not None else None


def 기간끝(기간):
    """카드 「기간」 글의 끝날 — 「2026년 상반기」 → 2026-06-30 · 「2026년 2분기」 → 2026-06-30 · 「2022~2025년」 → 2025-12-31 · 「2025년」 → 2025-12-31.
    날짜가 든 글이면 그 날. 못 읽으면 None(평가기준일 뒤 되살림에 쓰지 않는다)."""
    t = str(기간 or "")
    m = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", t)
    if m:
        return _날("%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3))))
    m = re.search(r"(\d{4})\s*~\s*(\d{4})년", t)
    if m:
        return _dt.date(int(m.group(2)), 12, 31)
    m = re.match(r"\s*(\d{4})년\s*(상반기|하반기|1~3분기|([1-4])분기)?", t)
    if not m:
        return None
    y = int(m.group(1))
    if m.group(2) == "상반기":
        return _dt.date(y, 6, 30)
    if m.group(2) == "1~3분기":
        return _dt.date(y, 9, 30)
    if m.group(3):
        q = int(m.group(3))
        return _dt.date(y, 3 * q, 30 if q in (2, 3) else 31)
    return _dt.date(y, 12, 31)


# ══════════════════════════════════════════════════════ 2. 카드를 읽는 눈

def 값들(c):
    return [v for v in (c.get("값") or []) if isinstance(v, dict)]


def 글(c):
    return str(c.get("주장") or "")


def 수칸(c):
    """카드의 수 칸(「수」 · 갈래가 남긴 「_수」) → 1~5 목록 · 없으면 None."""
    x = c.get("수", c.get("_수"))
    if x is None:
        return None
    if not isinstance(x, list):
        x = [x]
    밖 = []
    for y in x:
        try:
            n = int(y)
        except (TypeError, ValueError):
            continue
        if 1 <= n <= 5 and n not in 밖:
            밖.append(n)
    return 밖 or None


_k꼴 = [(r"^k01$", "경로"), (r"^k02$", "종가"), (r"^k03$", "뒤"), (r"^k21[a-z]?$", "연간"), (r"^k22[a-z]?$", "누계"),
       (r"^k23[a-z]?$", "분기"), (r"^k24[a-z]?$", "극값"), (r"^k3\d[a-z]?$", "비중"), (r"^k1\d\d[a-z]?$", "순위")]


def 계산꼴(c):
    """셈한 카드의 꼴 — 경로 · 순위 · 비중 · 연간 · 누계 · 분기 · 극값 · 종가 · 뒤 · None. 꼴의 정본은 `카드_계산.py` 머리의 카드 목록(k 접두)이다.
    밑줄 칸(_경로 · _창 · _구분)이 있으면 그것으로 먼저 본다."""
    if c.get("_경로"):
        return "경로"
    if c.get("_창"):
        return "순위"
    if any(v.get("_구분") for v in 값들(c)):
        return "비중"
    cid = str(c.get("id", ""))
    if cid.startswith("k"):
        for 꼴, 이름 in _k꼴:
            if re.match(꼴, cid):
                return 이름
    return None


def 정의다름(c):
    """매출의 정의가 다른 시계열(카드_계산 의 덧글자 b · 함정에 「정의가 다르」)."""
    if 계산꼴(c) in ("연간", "누계", "분기", "극값") and re.search(r"\d+b$", str(c.get("id", ""))):
        return True
    return any(re.search(r"정의가 다르|정의가 다름", str(h)) for h in (c.get("함정") or []))


def 실적카드(c):
    if 계산꼴(c) in ("연간", "누계", "분기", "극값", "경로", "종가"):
        return True
    return bool(값들(c)) and bool(re.search(역할말["실적"], 글(c)))


def 낱말점수(c, n):
    return len(re.findall(낱말[n], 글(c)))


def 필수종류(c):
    return [str(f.get("종류")) for f in (c.get("필수") or []) if isinstance(f, dict)]


def 하락원인판단(c):
    if c.get("등급") != "평가판단":
        return False
    겉 = 글(c) + " " + " ".join(str(f.get("정규식", "")) for f in (c.get("필수") or []) if isinstance(f, dict))
    return bool(re.search(역할말["하락원인"], 겉))


def 질문판단(c):
    return c.get("등급") == "평가판단" and bool(re.search(역할말["질문"], 글(c)))


def 계산값(c, 이름):
    """계산 칸에서 이름이 같은 식을 셈 → (값, 글) · 없으면 (None, None)."""
    for k in c.get("계산") or []:
        if isinstance(k, dict) and k.get("이름") == 이름:
            v = 식값(k.get("식", ""))
            if v is not None:
                return v, str(k.get("글", ""))
    return None, None


def 값찾기(c, 기간=None, 무엇=None, 꼴없이=True):
    for v in 값들(c):
        if 기간 is not None and v.get("_기간") != 기간:
            continue
        if 무엇 is not None and v.get("_무엇") != 무엇:
            continue
        if 꼴없이 and v.get("_꼴"):
            continue
        return v
    return None


def 기간목록(c):
    밖 = []
    for v in 값들(c):
        p = v.get("_기간")
        if p and p not in 밖:
            밖.append(p)
    return 밖


def 기간값(c, p):
    """카드 c 의 기간 p 의 매출 · 영업이익(기본 단위) · 영업이익률(비)과 그 글."""
    d = {"기간": p}
    for 무, 칸 in (("매출", "매출"), ("영업이익", "영업")):
        v = 값찾기(c, p, 무)
        if v:
            d[칸] = 금액수(v.get("본편") or v.get("글"))
            d[칸 + "글"] = v.get("글")
    v = 값찾기(c, p, "영업이익률")
    if v:
        x, _ = 계산값(c, "%s 영업이익률" % p)
        d["이익률"] = x if x is not None else 비수(v.get("본편") or v.get("글"))[0]
        d["이익률글"] = v.get("글")
    return d


def 증감값(c, 이름):
    """카드의 「영업이익 전년 같은 기간 대비」 같은 증감 → (증가율, 글). 배 꼴이면 배 − 1."""
    v = 값찾기(c, None, 이름)
    x, 식글 = 계산값(c, 이름)
    글_ = (v or {}).get("글") or 식글
    if x is None:
        if not v:
            return None, None
        수, 꼴 = 비수(v.get("본편") or v.get("글"))
        if 수 is None:
            return None, None
        return (수 - 1 if 꼴 == "배" else 수), 글_
    return (x - 1 if str(글_).endswith("배") else x), 글_


# ══════════════════════════════════════════════════════ 3. 읽기 — 카드.합치기 와 같은 규칙

def _회사꼴(s):
    t = re.sub(r"\(주\)|㈜|주식회사", "", str(s or ""))
    t = re.sub(r"[\s,.]+", "", t)
    return re.sub(r"(?i)(inc|corp|corporation|co|ltd|llc|plc)$", "", t)


def 읽기(입력들):
    """입력(회차 폴더 하나 또는 카드 문서들) → (합친 문서, 없음 기록, 읽은 파일, 경고, 회차). 어긋나면 입력오류."""
    회차 = None
    if len(입력들) == 1 and os.path.isdir(입력들[0]):
        회차 = 입력들[0]
        한 = os.path.join(회차, "_raw", "사실카드.json")
        파일들 = [한] if os.path.isfile(한) else sorted(glob.glob(os.path.join(회차, "_raw", "카드", "*.json")))
        if not 파일들:
            raise 입력오류("카드가 없음 — %s 의 _raw/사실카드.json · _raw/카드/*.json" % 회차)
    else:
        파일들 = list(입력들)
    경고, 없음, 읽은 = [], [], []
    밖 = None
    for p in 파일들:
        if not os.path.isfile(p):
            raise 입력오류("파일이 없음 — %s" % p)
        try:
            d = json.load(io.open(p, encoding="utf-8-sig"))
        except ValueError as e:
            raise 입력오류("JSON 을 읽지 못함 — %s (%s)" % (p, e))
        이름 = os.path.basename(p)
        if not isinstance(d, dict):
            경고.append("%s — 사전이 아니라 건너뜀" % 이름)
            continue
        if not isinstance(d.get("카드"), list):
            if isinstance(d.get("없음"), list):
                for x in d["없음"]:
                    if isinstance(x, dict):
                        없음.append(dict(x, 조각=이름))
                읽은.append(p)
            else:
                경고.append("%s — 「카드」 · 「없음」 칸이 없어 건너뜀" % 이름)
            continue
        읽은.append(p)
        if 밖 is None:
            밖 = {k: v for k, v in d.items() if k != "카드"}
            밖["판"] = K.판
            밖["카드"], 밖["함정_메모"], 밖["결론에_나오는_용어"], 밖["못지음"], 밖["_조각"] = [], [], [], [], []
        for k in ("평가기준일", "재무기준일"):
            if d.get(k) != 밖.get(k):
                raise 입력오류("%s 의 %s 「%s」가 다른 조각 「%s」와 다름" % (이름, k, d.get(k), 밖.get(k)))
        if d.get("회사") != 밖.get("회사"):
            if _회사꼴(d.get("회사")) != _회사꼴(밖.get("회사")):
                raise 입력오류("%s 의 회사 「%s」가 다른 조각 「%s」와 다름" % (이름, d.get("회사"), 밖.get("회사")))
            경고.append("회사 이름 꼴이 조각마다 다름 — 「%s」 · 「%s」(법인 표기를 떼면 같아 합침 · 카드.합치기 는 오류로 본다)"
                      % (밖.get("회사"), d.get("회사")))
        밖["카드"].extend(d["카드"])
        for k in ("함정_메모", "결론에_나오는_용어"):
            for x in d.get(k, []) or []:
                if x not in 밖[k]:
                    밖[k].append(x)
        for x in d.get("못지음", []) or []:
            밖["못지음"].append(dict(x, 조각=이름) if isinstance(x, dict) else {"무엇": str(x), "조각": 이름})
        밖["_조각"].append(이름)
    if 밖 is None:
        raise 입력오류("카드 문서가 없음(「카드」 칸이 있는 파일 0)")
    return 밖, 없음, 읽은, 경고, 회차


# ══════════════════════════════════════════════════════ 4. 3분 층 거르기

def 거르기(문서, 꼴오류):
    """→ (쓸 카드 {id: 카드}, 뺀 카드 [{id, 까닭}], 평가기준일 뒤 [{id, 표지, …}], 되살림 [글])."""
    F = _날(문서.get("재무기준일"))
    쓸, 뺀, 뒤, 되살림 = {}, [], [], []
    for c in 문서["카드"]:
        cid = str(c.get("id"))
        등 = c.get("등급")
        if cid in 꼴오류:
            뺀.append({"id": cid, "까닭": "꼴 오류 — " + "; ".join(꼴오류[cid][:3])})
            continue
        if "3분" in (c.get("층제한") or []):
            뺀.append({"id": cid, "까닭": "층제한 「3분」 — 이 층에 쓰지 않는 카드"})
            continue
        if not K.등급표.get(등, {}).get("3분"):
            뺀.append({"id": cid, "까닭": "등급 「%s」는 3분 레터에 싣지 않음(카드설정 「3분」 칸 · A-2)" % 등})
            continue
        if c.get("평가기준일뒤"):
            끝 = 기간끝(c.get("기간"))
            if 등 in ("공시", "계산") and not c.get("사건일") and 끝 and F and 끝 <= F:
                되살림.append("%s — 공표일 %s 은 평가기준일 뒤이나 기간(%s)이 재무기준일 %s 안에서 끝나 보고 기간의 사실로 봄"
                            % (cid, c.get("공표일"), c.get("기간"), F.isoformat()))
            else:
                뒤.append({"id": cid, "표지": "평가기준일 뒤 · 반영하지 않음", "날": c.get("사건일") or c.get("공표일"),
                          "주장": 글(c)[:120], "자리": "회사 소개에 넣지 않음 — 날짜 문단(고정문) · 본편에서 이 표지와 함께"})
                continue
        쓸[cid] = c
    return 쓸, 뺀, 뒤, 되살림


# ══════════════════════════════════════════════════════ 5. 이익 · 주가 · 긴장

def _해(p):
    m = re.search(r"(\d{4})", str(p))
    return int(m.group(1)) if m else 0


def _비교(c, 바탕, 지금, 전, 증감머리):
    a, b = 기간값(c, 지금), 기간값(c, 전)
    d = {"바탕": 바탕, "카드": c["id"], "지금": 지금, "전": 전, "이익률": [a.get("이익률"), b.get("이익률")],
         "영업": [a.get("영업"), b.get("영업")], "매출": [a.get("매출"), b.get("매출")],
         "글": {"이익률": [a.get("이익률글"), b.get("이익률글")], "영업": [a.get("영업글"), b.get("영업글")],
               "매출": [a.get("매출글"), b.get("매출글")]}}
    if 증감머리:
        for 무, 이름 in (("영업증가", "영업이익 " + 증감머리), ("매출증가", "매출 " + 증감머리)):
            g, 글_ = 증감값(c, 이름)
            if g is not None:
                d[무], d[무 + "글"] = g, 글_
        v = 값찾기(c, None, "영업이익률 차 " + 증감머리)
        if v:
            d["이익률차글"] = v.get("글")
    for 무, 칸 in (("영업증가", "영업"), ("매출증가", "매출")):
        x1, x0 = d[칸]
        if d.get(무) is None and x1 is not None and x0 is not None and x0 > 0:
            d[무] = x1 / x0 - 1
    return d


def 실적읽기(쓸):
    """계산 카드에서 이익 판정의 바탕들 · 연간 시계열 · 극값."""
    바탕, 연간, 연간b, 극값 = [], [], [], []
    for c in sorted(쓸.values(), key=lambda c: str(c["id"])):
        꼴 = 계산꼴(c)
        if 꼴 == "누계" and not 정의다름(c):
            ps = sorted(기간목록(c), key=_해)
            if len(ps) >= 2:
                바탕.append((0, _비교(c, "누계 · 전년 같은 기간", ps[-1], ps[-2], "전년 같은 기간 대비")))
            elif ps:
                바탕.append((9, {"바탕": "누계(비교 기간 없음)", "카드": c["id"], "지금": ps[-1], "전": None, "단독": 기간값(c, ps[-1])}))
        elif 꼴 == "분기" and not 정의다름(c):
            qs = []
            for p in 기간목록(c):
                m = re.match(r"(\d{4})년 ([1-4])분기$", p)
                if m:
                    qs.append((int(m.group(1)), int(m.group(2)), p))
            if qs:
                y, q, p = max(qs)
                전 = next((x[2] for x in qs if x[0] == y - 1 and x[1] == q), None)
                if 전:
                    바탕.append((1, _비교(c, "분기 · 전년 같은 분기", p, 전, "전년 같은 분기 대비")))
        elif 꼴 == "연간":
            ys = sorted((_해(p), p) for p in 기간목록(c) if _해(p))
            열 = [dict(기간값(c, p), 해=y, 카드=c["id"]) for y, p in ys]
            (연간b if 정의다름(c) else 연간).append((c["id"], 열))
            if not 정의다름(c) and len(ys) >= 2:
                바탕.append((2, _비교(c, "연간 · 앞 해", ys[-1][1], ys[-2][1], None)))
        elif 꼴 == "극값":
            최고 = 값찾기(c, None, "영업이익률 최고")
            최저 = 값찾기(c, None, "영업이익률 최저")
            극값.append({"카드": c["id"], "정의다름": 정의다름(c),
                       "최고": (비수(최고.get("본편") or 최고.get("글"))[0], 최고.get("글"), 최고.get("_기간")) if 최고 else None,
                       "최저": (비수(최저.get("본편") or 최저.get("글"))[0], 최저.get("글"), 최저.get("_기간")) if 최저 else None})
    바탕.sort(key=lambda x: x[0])
    return [b for _, b in 바탕], 연간, 연간b, 극값


def _세기(rel):
    a = abs(rel)
    if a >= 이익문턱["뚜렷"]:
        return "뚜렷"
    if a >= 이익문턱["약함"]:
        return "약함"
    return "미미"


def 이익재기(b):
    """바탕 하나 → {방향, 세기, 잼, 근거 글} · 못 재면 None."""
    if b.get("단독"):
        return None
    m1, m0 = b["이익률"]
    o1, o0 = b["영업"]
    if o1 is not None and o0 is not None and o0 != 0 and (o1 < 0) != (o0 < 0):
        방향 = "↑" if o1 > 0 else "↓"
        return {"방향": 방향, "세기": "뚜렷", "잼": "흑자 전환" if 방향 == "↑" else "적자 전환",
                "근거": "%s 영업이익 %s · %s %s" % (b["지금"], b["글"]["영업"][0], b["전"], b["글"]["영업"][1])}
    if m1 is not None and m0 is not None:
        d = m1 - m0
        rel = d / max(abs(m0), 이익문턱["분모바닥"])
        세 = "미미" if abs(d) < 이익문턱["최소폭"] else _세기(rel)
        차글 = b.get("이익률차글") or 포(d, 1)
        return {"방향": "↑" if d >= 0 else "↓", "세기": 세, "잼": "영업이익률 차", "차": 차글, "상대": 퍼(rel, 0, 부호=True),
                "근거": "%s 영업이익률 %s · %s %s(차 %s · 앞 기간 이익률 대비 %s)" % (
                    b["지금"], b["글"]["이익률"][0], b["전"], b["글"]["이익률"][1], 차글, 퍼(rel, 0, 부호=True))}
    g = b.get("영업증가")
    if g is not None:
        return {"방향": "↑" if g >= 0 else "↓", "세기": _세기(g), "잼": "영업이익 증감률", "상대": 퍼(g, 1, 부호=True),
                "근거": "%s 영업이익 %s · %s %s(%s)" % (b["지금"], b["글"]["영업"][0] or "", b["전"], b["글"]["영업"][1] or "—",
                                                 b.get("영업증가글") or 퍼(g, 1, 부호=True))}
    return None


def 성숙재기(연간, 연간b):
    """여러 해의 매출 정체 · 이익률 안정 → dict · 재료가 모자라면 None."""
    for 열들, 덧 in ((연간, None), (연간b, "매출 정의가 다른 시계열 — 판정에 쓰고, 글에서는 다른 실적 카드와 한 문장에 섞지 않는다")):
        for cid, 열 in 열들:
            쓸 = [x for x in 열 if x.get("매출") is not None and x.get("이익률") is not None][-성숙문턱["볼해"]:]
            if len(쓸) < 성숙문턱["최소해"]:
                continue
            처, 끝 = 쓸[0], 쓸[-1]
            n = 끝["해"] - 처["해"]
            if n <= 0 or 처["매출"] <= 0 or 끝["매출"] <= 0:
                continue
            연율 = (float(끝["매출"]) / float(처["매출"])) ** (1.0 / n) - 1
            ms = [float(x["이익률"]) for x in 쓸]
            평 = sum(ms) / len(ms)
            편 = math.sqrt(sum((x - 평) ** 2 for x in ms) / (len(ms) - 1))
            한 = max(성숙문턱["이익률편차"], 성숙문턱["이익률편차비"] * abs(평))
            정체 = abs(연율) <= 성숙문턱["매출연율"]
            안정 = 편 <= 한 and min(ms) > 0
            return {"카드": cid, "덧": 덧, "해": [처["해"], 끝["해"]], "매출연율": round(연율, 4), "이익률평균": round(평, 4),
                    "이익률편차": round(편, 4), "편차문턱": round(한, 4), "정체": 정체, "안정": 안정, "성숙": 정체 and 안정,
                    "근거": "%d~%d년 매출 %s → %s(연율 %+.1f%%) · 영업이익률 평균 %.1f%% · 표준편차 %.1f%%p(문턱 %.1f%%p)" % (
                        처["해"], 끝["해"], 처.get("매출글"), 끝.get("매출글"), 연율 * 100, 평 * 100, 편 * 100, 한 * 100)}
    return None


class _점:
    __slots__ = ("날", "d", "v", "글", "본편", "무엇", "확정", "종류")

    def __init__(self, 날, v, 글_=None, 본편=None, 무엇=None, 확정=True, 종류=None):
        self.날, self.d, self.v = 날, _날(날), Fraction(str(v))
        self.글, self.본편, self.무엇, self.확정, self.종류 = 글_, 본편, 무엇, 확정, 종류


def 변동성(시세, T):
    """시세 파일 → 한 달 변동폭 · 연 변동성(평가기준일까지 최근 252거래일 하루 로그 등락의 표본 표준편차). 못 읽으면 None."""
    if not 시세 or not os.path.isfile(시세):
        return None
    try:
        _출처, 행들 = KC.주가읽기(시세)
    except (OSError, ValueError):
        return None
    행들 = [r for r in 행들 if T is None or r.d <= T]
    rs = [math.log(float(행들[i].v / 행들[i - 1].v)) for i in range(1, len(행들))][-주가설정["변동성일"]:]
    if len(rs) < 주가설정["변동성최소"]:
        return None
    평 = sum(rs) / len(rs)
    sd = math.sqrt(sum((x - 평) ** 2 for x in rs) / (len(rs) - 1))
    return {"하루": round(sd, 6), "연": round(sd * math.sqrt(252), 4), "한달": round(sd * math.sqrt(주가설정["한달"]), 4),
            "날수": len(rs), "구간": [행들[-len(rs) - 1].날, 행들[-1].날], "파일": os.path.basename(시세),
            "식": "하루 로그 등락의 표본 표준편차 × √%d(평가기준일까지 최근 %d거래일)" % (주가설정["한달"], len(rs))}


def 경로점(c, T):
    """경로 카드 → {시작, 끝, 꺾임, 최고, 최저, 카드문턱, 파일}. 종가는 계산 칸의 식(원자료 ÷ 나눗수)에서 되찾는다 — 값 글은 어림이다."""
    경 = c.get("_경로") or {}
    색 = {}                                          # 값 칸은 글이 같으면 하나만 남기므로(카드_계산 의 겹 없애기) 날짜 색인은 보조로만
    for v in 값들(c):
        if v.get("_날") and v.get("단위") == "금액":
            색.setdefault(v["_날"], v)
    역, 원종, 계글 = {}, {}, {}
    for k in c.get("계산") or []:
        if not isinstance(k, dict):
            continue
        m = re.fullmatch(r"(.+?) 종가\((\d{4}-\d{2}-\d{2})\)", str(k.get("이름", "")))
        n = re.match(r"\s*(\d+(?:\.\d+)?)", str(k.get("식", "")))
        if not (m and n):
            continue
        무, 날 = m.group(1), m.group(2)
        원종[날], 계글[날] = n.group(1), k.get("글")
        if re.fullmatch(r"\d{4}년 첫 거래일", 무):
            역["첫해"] = (날, 무)
        elif 무 in ("평가기준일", "평가기준일 앞 마지막 거래일"):
            역["끝"] = (날, 무)
        elif 무 in ("구간 첫날", "구간 최고", "구간 최저"):
            역[무] = (날, 무)

    def 점(쌍, 무엇):
        if not 쌍 or 쌍[0] not in 원종:
            return None
        v = 색.get(쌍[0], {})
        return _점(쌍[0], 원종[쌍[0]], v.get("글") or 계글.get(쌍[0]), v.get("본편"), 무엇)

    Tp = 점(역.get("끝"), "평가기준일")
    if Tp is None:
        return None
    시작 = None
    첫해 = 역.get("첫해")
    if 첫해 is not None and (Tp.d - _날(첫해[0])).days >= 주가설정["창최소일"]:
        시작 = 점(첫해, "창 시작(%s)" % 첫해[1])
    if 시작 is None:
        시작 = 점(역.get("구간 첫날"), "창 시작(시세 첫날)")
    꺾 = []
    for x in 경.get("꺾임") or []:
        v = 색.get(x.get("날"), {})
        꺾.append(_점(x["날"], x["종가"], v.get("글") or 계글.get(x.get("날")), v.get("본편"), "꺾임 %s점" % x.get("종류"),
                     bool(x.get("확정")), x.get("종류")))
    return {"시작": 시작, "끝": Tp, "꺾임": 꺾, "최고": 점(역.get("구간 최고"), "구간 최고"), "최저": 점(역.get("구간 최저"), "구간 최저"),
            "카드문턱": Fraction(str(경.get("문턱"))) if 경.get("문턱") is not None else None, "파일": 경.get("파일")}


def 지그재그(점들, th):
    """점 목록(날짜 차례)의 꺾임 — 카드_계산.꺾임찾기 와 같은 셈 → 꺾임 자리 집합."""
    if len(점들) < 2:
        return set()
    return {x["i"] for x in KC.꺾임찾기(점들, th)}


def _창점(자료):
    S, T = 자료["시작"], 자료["끝"]
    창 = [p for p in 자료["꺾임"] if S.d < p.d < T.d]
    for 극 in (자료["최고"], 자료["최저"]):
        if 극 is not None and S.d < 극.d < T.d and all(극.날 != p.날 for p in 창):
            창.append(극)
    창.sort(key=lambda p: p.d)
    전부 = [S] + 창 + [T]
    최고 = max(전부, key=lambda p: (p.v, -p.d.toordinal()))
    최저 = min(전부, key=lambda p: (p.v, p.d.toordinal()))
    return 창, 전부, 최고, 최저


def 경로고르기(자료, th, 방향, 필수경로):
    """3분 레터에 실을 주가 경로의 점 — 파일 머리 「경로 문턱」 ①~④. → (고른 점, 뺀 꺾임, 주의, 기점)."""
    S, T = 자료["시작"], 자료["끝"]
    창, 전부, 최고, 최저 = _창점(자료)
    주의, 뺌 = [], []
    기점 = 최고 if 방향 == "↓" else (최저 if 방향 == "↑" else None)
    if 기점 is None:
        고름 = sorted({p.날: p for p in (S, 최고, 최저, T)}.values(), key=lambda p: p.d)
        for p in 창:
            if p not in 고름:
                뺌.append({"날": p.날, "종가": p.글, "까닭": "주가 방향이 문턱 아래라 창 시작 · 최고 · 최저 · 평가기준일만 싣는다"})
        return 고름, 뺌, 주의, None
    i기 = 전부.index(기점)
    앞, 뒤 = 전부[: i기 + 1], 전부[i기:]
    th2 = th * 주가설정["앞구간배수"]
    앞꺾 = {i for i in 지그재그(앞, th2) if 0 < i < len(앞) - 1}
    고름 = []
    if 기점 is not S:
        if abs(기점.v / S.v - 1) >= th:
            고름.append(S)
        else:
            주의.append("창 시작 %s 이 기점 %s 와 문턱(%s) 안이라 기점을 시작으로 둠" % (S.날, 기점.날, 퍼(th, 1)))
    for i, p in enumerate(앞):
        if 0 < i < len(앞) - 1:
            if i in 앞꺾 or p is 최고 or p is 최저:
                고름.append(p)
            else:
                뺌.append({"날": p.날, "종가": p.글, "까닭": "기점(%s) 앞 되돌림 — 문턱의 %d배(%s)에 못 미쳐 한 움직임으로 묶음" % (
                    기점.날, 주가설정["앞구간배수"], 퍼(th2, 1))})
    고름.append(기점)
    뒤꺾 = {i for i in 지그재그(뒤, th) if 0 < i < len(뒤) - 1}
    for i, p in enumerate(뒤):
        if 0 < i < len(뒤) - 1:
            if i in 뒤꺾 or p is 최고 or p is 최저:
                고름.append(p)
            else:
                뺌.append({"날": p.날, "종가": p.글, "까닭": "기점 뒤이나 이웃 꺾임과 문턱(%s) 안" % 퍼(th, 1)})
    고름 = sorted({p.날: p for p in 고름}.values(), key=lambda p: p.d)
    # ③ 끝 — 마지막 꺾임이 평가기준일과 문턱 안이면 합친다(기점 · 창 최고 · 최저는 남긴다)
    while 고름 and 고름[-1] is not 기점 and 고름[-1] is not 최고 and 고름[-1] is not 최저 and abs(T.v / 고름[-1].v - 1) < th:
        p = 고름.pop()
        뺌.append({"날": p.날, "종가": p.글, "까닭": "끝의 %s점(%s)이 평가기준일과 문턱 안(%s) — 평가기준일로 합침%s" % (
            p.종류 or "", "미확정" if not p.확정 else "확정", 퍼(T.v / p.v - 1, 1, 부호=True),
            " · 「바닥 · 꼭대기」로 쓰지 않는다(카드 함정)" if not p.확정 else "")})
    고름.append(T)
    # ④ 필수 「경로」 — 기점 뒤가 한 방향뿐이면 카드의 꺾임에서 가장 큰 되돌림 한 쌍을 되돌려 넣는다
    if 필수경로:
        뒤점 = [p for p in 고름 if p.d >= 기점.d]
        반대 = [1 for a, b in zip(뒤점, 뒤점[1:]) if (b.v > a.v) == (방향 == "↓")]
        if not 반대:
            후보 = [p for p in 창 if p.d > 기점.d and p not in 고름]
            best = None
            for a in 후보:
                for b in 후보:
                    if a.d < b.d:
                        r = b.v / a.v - 1
                        if (r > 0) == (방향 == "↓") and (best is None or abs(r) > abs(best[2])):
                            best = (a, b, r)
            if best:
                고름 = sorted({p.날: p for p in 고름 + [best[0], best[1]]}.values(), key=lambda p: p.d)
                뺌 = [x for x in 뺌 if x["날"] not in (best[0].날, best[1].날)]
                주의.append("카드의 필수 한정 「경로」 — 기점 뒤가 한 방향뿐이라 가장 큰 되돌림 %s → %s(%s)을 되돌려 넣음" % (
                    best[0].날, best[1].날, 퍼(best[2], 1, 부호=True)))
    return 고름, 뺌, 주의, 기점


def 주가재기(자료, th):
    """창의 주가 방향 — (방향, 세기, 근거 dict)."""
    S, T = 자료["시작"], 자료["끝"]
    _창, _전부, 최고, 최저 = _창점(자료)
    dd = T.v / 최고.v - 1
    chg = T.v / S.v - 1
    if dd <= -th or chg <= -th:
        방향, 잼 = "↓", min(dd, chg)
    elif chg >= th:
        방향, 잼 = "↑", chg
    else:
        방향, 잼 = ("↑" if chg >= 0 else "↓"), chg
    세 = "뚜렷" if abs(잼) >= th * 주가설정["뚜렷배수"] else ("약함" if abs(잼) >= th else "미미")
    근 = {"창": [S.날, T.날], "창 시작": [S.날, S.글], "창 안 최고": [최고.날, 최고.글], "창 안 최저": [최저.날, 최저.글],
         "평가기준일": [T.날, T.글], "고점 대비": 퍼(dd, 1, 부호=True), "창 시작 대비": 퍼(chg, 1, 부호=True), "문턱": 퍼(th, 1),
         "뚜렷 문턱": 퍼(th * 주가설정["뚜렷배수"], 1),
         "셈": "고점 대비 = 평가기준일 종가 ÷ 창 안 최고 − 1 · 창 시작 대비 = 평가기준일 종가 ÷ 창 시작 종가 − 1"
              "(카드 계산 칸의 원자료 종가로 셈한 판정용 숫자 — 카드 값에 없으면 글에 쓰지 않는다)"}
    return 방향, 세, 근


def 긴장재기(쓸, 문서, 시세):
    """→ (긴장 dict, 강제 카드 {id: 수}, 경로 dict 또는 None)."""
    T = _날(문서.get("평가기준일"))
    바탕들, 연간, 연간b, 극값 = 실적읽기(쓸)
    잰 = [(b, 이익재기(b)) for b in 바탕들]
    잰 = [(b, r) for b, r in 잰 if r]
    강제 = {}
    이익 = None
    if 잰:
        b0, r0 = 잰[0]
        이익 = dict(r0, 바탕=b0["바탕"], 카드=b0["카드"], 지금=b0["지금"], 전=b0["전"])
        강제[b0["카드"]] = 2
        이익["보조"] = [dict(r, 바탕=b["바탕"], 카드=b["카드"]) for b, r in 잰[1:]]
        이익["엇갈림"] = ["%s(%s)는 %s — %s" % (x["바탕"], x["카드"], x["방향"], x["근거"]) for x in 이익["보조"]
                       if x["방향"] != 이익["방향"]] or None
    최근영업 = 최근매출 = None
    for b in 바탕들:
        if b.get("단독"):
            o, s, 글o = b["단독"].get("영업"), b["단독"].get("매출"), b["단독"].get("영업글")
        else:
            o, s, 글o = b["영업"][0], b["매출"][0], b["글"]["영업"][0]
        if o is not None and 최근영업 is None:
            최근영업 = (o, b["카드"], b["지금"], 글o)
        if s is not None and 최근매출 is None:
            최근매출 = (s, b["카드"], b["지금"])
    기록 = None
    if 이익 and 극값:
        e = next((x for x in 극값 if not x["정의다름"]), None)
        b0 = next((b for b in 바탕들 if b["카드"] == 이익["카드"]), {})
        m1 = (b0.get("이익률") or [None])[0]
        if e and e["최고"] and m1 is not None and e["최고"][0] is not None:
            기록 = {"카드": e["카드"], "넘음": bool(m1 > e["최고"][0]), "시계열 최고": "%s(%s)" % (e["최고"][1], e["최고"][2]),
                   "지금": "%s %s" % (b0.get("지금"), (b0.get("글") or {}).get("이익률", [None])[0])}
    성숙 = 성숙재기(연간, 연간b)
    경카 = next((c for c in sorted(쓸.values(), key=lambda c: str(c["id"])) if 계산꼴(c) == "경로"), None)
    자료 = 경로점(경카, T) if 경카 else None
    주가 = 경로 = None
    if 자료 and 자료["시작"] is not None:
        시세p = 시세 or (os.path.join(문서["_회차"], 자료["파일"]) if 문서.get("_회차") and 자료.get("파일") else None)
        vol = 변동성(시세p, T)
        카드th = 자료["카드문턱"] or Fraction(1, 5)
        th = max(카드th, Fraction(str(vol["한달"]))) if vol else 카드th
        방향, 세, 근 = 주가재기(자료, th)
        주가 = {"방향": 방향, "세기": 세, "카드": 경카["id"], "근거": 근}
        강제[경카["id"]] = 2
        필수경로 = "경로" in 필수종류(경카)
        고름, 뺌, 주의, 기점 = 경로고르기(자료, th, 방향 if 세 != "미미" else None, 필수경로)
        다리 = [(a, b, b.v / a.v - 1) for a, b in zip(고름, 고름[1:])]
        기뒤 = [x for x in 다리 if 기점 is not None and x[0].d >= 기점.d]
        경로 = {"카드": 경카["id"],
               "문턱": {"쓴 문턱": 퍼(th, 1), "카드 문턱": 퍼(카드th, 0),
                      "한 달 변동폭": 퍼(Fraction(str(vol["한달"])), 1) if vol else None,
                      "연 변동성": 퍼(Fraction(str(vol["연"])), 1) if vol else None, "앞 구간 문턱": 퍼(th * 주가설정["앞구간배수"], 1),
                      "규칙": "문턱 = max(카드 문턱, 한 달 변동폭) — 변동성 비례 · 카드 문턱이 바닥", "변동성": vol,
                      "변동성 없음": None if vol else "시세 파일을 읽지 못해 카드 문턱만 씀 — --시세 또는 --회차 로 시세 파일을 주면 변동성으로 잰다"},
               "기점": {"날": 기점.날, "무엇": "창 안 최고" if 방향 == "↓" else "창 안 최저", "글": 기점.글} if 기점 is not None else None,
               "고른 점": [{"날": p.날, "글": p.글, "본편": p.본편, "무엇": p.무엇} for p in 고름],
               "다리": [{"앞": a.날, "뒤": b.날, "움직임": 퍼(r, 1, 부호=True), "일수": (b.d - a.d).days} for a, b, r in 다리],
               "기점 뒤 하락": sum(1 for x in 기뒤 if x[2] <= -th), "기점 뒤 상승": sum(1 for x in 기뒤 if x[2] >= th),
               "뺀 꺾임": 뺌 or None,
               "주의": 주의 + ["고른 점을 날짜 차례로 옮긴다 · 고점 · 저점 · 되오름을 함께(카드 필수 한정 「경로」)" if 필수경로
                             else "고른 점을 날짜 차례로 옮긴다"],
               "필수 경로": 필수경로}
    # 꼴 고르기
    대안, 차례 = [], []
    하위 = None
    if 주가 is None:
        꼴 = "주가 없음(비상장)"
        차례.append("주가 경로 카드가 없음 → 「주가 없음(비상장)」 — 실적의 방향만으로")
        if 최근영업 and 최근영업[0] < 0:
            하위 = "적자 · 매출 전"
        elif 성숙 and 성숙["성숙"]:
            하위 = "성장 없는 성숙"
        elif 이익:
            하위 = "이익 %s" % 이익["방향"]
    elif (최근영업 and 최근영업[0] < 0) or (최근매출 and 최근매출[0] <= 0):
        꼴 = "적자 · 매출 전"
        차례.append("최근 영업이익 %s(%s · %s) — 영업손실이거나 매출이 없어 「적자 · 매출 전」" % (
            최근영업[3] if 최근영업 else "—", 최근영업[1] if 최근영업 else "", 최근영업[2] if 최근영업 else ""))
    elif 성숙 and 성숙["성숙"] and 주가["세기"] != "뚜렷":
        꼴 = "성장 없는 성숙"
        차례.append("매출 정체 · 이익률 안정(%s) 이고 주가 움직임이 「%s」 — 「성장 없는 성숙」" % (성숙["근거"], 주가["세기"]))
        if 이익:
            대안.append({"꼴": "이익 %s · 주가 %s" % (이익["방향"], 주가["방향"]),
                       "까닭": "성숙을 앞세우지 않으면 — 이익 %s(%s) · 주가 %s(%s)" % (이익["방향"], 이익["세기"], 주가["방향"], 주가["세기"])})
        강제[성숙["카드"]] = 2
    elif 이익 is None:
        꼴 = None
        차례.append("이익을 잴 바탕(누계 · 분기 · 연간의 비교)이 없음 — 긴장을 고르지 못함")
    else:
        꼴 = "이익 %s · 주가 %s" % (이익["방향"], 주가["방향"])
        차례.append("이익 %s(%s · %s) × 주가 %s(%s · 고점 대비 %s · 창 시작 대비 %s)" % (
            이익["방향"], 이익["세기"], 이익["바탕"], 주가["방향"], 주가["세기"], 주가["근거"]["고점 대비"], 주가["근거"]["창 시작 대비"]))
        if 성숙 and 성숙["성숙"]:
            대안.append({"꼴": "성장 없는 성숙", "까닭": "매출 정체 · 이익률 안정이나 주가 움직임이 「뚜렷」해 뒤로 둠 — %s" % 성숙["근거"]})
        if 이익["세기"] == "미미":
            대안.append({"꼴": "이익 %s · 주가 %s" % ("↓" if 이익["방향"] == "↑" else "↑", 주가["방향"]), "까닭": "이익 움직임이 문턱 아래(미미)"})
        if 주가["세기"] == "미미":
            대안.append({"꼴": "이익 %s · 주가 %s" % (이익["방향"], "↓" if 주가["방향"] == "↑" else "↑"), "까닭": "주가 움직임이 문턱 아래(미미)"})
    if 꼴 and 꼴.startswith("이익 ") and 이익["세기"] == "뚜렷" and 주가["세기"] != "미미" and not 이익.get("엇갈림"):
        확신 = "높음"
    elif any("미미" in x["까닭"] for x in 대안) or (이익 and 이익.get("엇갈림")) or 꼴 is None:
        확신 = "낮음"
    else:
        확신 = "보통"
    표 = 긴장꼴.get(꼴 or "", {})
    방향글 = 표.get("방향")
    if 방향글 and " → " in 방향글:
        시장, 평가 = 방향글.split(" → ", 1)
    else:
        시장 = 평가 = 방향글
    조건 = []
    if 꼴 and 꼴.startswith("이익 ↑"):
        if 기록 is not None:
            조건.append("「최대」는 시계열 최고를 넘을 때만 — %s(%s: %s · 시계열 최고 %s)" % (
                "넘음" if 기록["넘음"] else "넘지 않음 · 「최대」로 쓰지 않는다", 기록["카드"], 기록["지금"], 기록["시계열 최고"]))
        else:
            조건.append("「최대」는 시계열 최고와 견준 카드(극값)가 없어 쓰지 않는다")
    if 경로 and 주가 and 주가["방향"] == "↓" and 경로["기점 뒤 하락"] >= 2:
        조건.append("기점 뒤 하락은 %d번 — 「한 번 내렸다」로 쓰지 않는다(경로)" % 경로["기점 뒤 하락"])
    if 이익 and 이익.get("엇갈림"):
        조건.append("이익의 바탕이 엇갈림 — 판정 바탕(%s)의 기간을 문장에 남긴다" % 이익["바탕"])
    긴장 = {"꼴": 꼴, "하위": 하위, "재료": 표.get("재료"), "물음 방향": 방향글, "시장의 물음": 시장, "평가의 물음": 평가,
           "다리": "시장의 물음(수 2) → 끌어내릴 힘(수 4) → 평가의 물음(수 5) — 물음은 수 2 에서 한 번, 답의 방향은 수 4 · 5 에서",
           "확신": 확신, "대안": 대안 or None, "판정 차례": 차례, "이익": 이익, "주가": 주가, "성숙": 성숙, "기록": 기록,
           "최근 영업이익": {"글": 최근영업[3], "카드": 최근영업[1], "기간": 최근영업[2]} if 최근영업 else None, "조건": 조건 or None}
    return 긴장, 강제, 경로


# ══════════════════════════════════════════════════════ 6. 수 — 후보 · 차례 · 배치

def 수후보(c, 쓸):
    """→ (수 목록, 까닭)."""
    칸 = 수칸(c)
    if 칸:
        return 칸, "카드의 수 칸 %s" % 칸
    꼴 = 계산꼴(c)
    등 = c.get("등급")
    if 꼴 in ("경로", "종가", "연간", "누계", "분기", "극값"):
        return [2], "규칙 — 셈한 실적 · 시세(%s) → 수 2(긴장)" % 꼴
    if 꼴 == "비중":
        return [1], "규칙 — 셈한 매출 구성 비중 → 수 1(무엇이 돈을 버나)"
    if 꼴 == "순위":
        return [4], "규칙 — 하루 등락 순위 → 수 4(하락의 정황)"
    if 꼴 == "뒤":
        return [], "평가기준일 뒤 시세"
    if 등 == "레터정의":
        return [5], "규칙 — 레터정의 → 수 5(평가가 보는 숫자)"
    if 등 == "평가판단":
        if 하락원인판단(c):
            return [4, 5], "규칙 — 평가판단(원인을 가르지 못함) → 수 4 · 5"
        return [5, 4], "규칙 — 평가판단 → 수 5 · 4"
    if 등 == "일반설명":
        이름들 = [str(g.get("이름")) for g in (c.get("고유명사") or []) if isinstance(g, dict) and g.get("이름")]
        for d in sorted(쓸.values(), key=lambda x: str(x["id"])):
            if d is c or d.get("등급") == "일반설명":
                continue
            if any(n in 글(d) for n in 이름들):
                목 = 수칸(d) or 수후보(d, 쓸)[0]
                if 목:
                    return [목[0]], "규칙 — 일반설명(고유명사 소개) → 「%s」가 쓰이는 카드 %s 의 수" % (이름들[0], d["id"])
        return [1], "규칙 — 일반설명 → 수 1(생활 접점)"
    if 등 in ("회사 발화", "고객사 · 협력사 발표"):
        return ([4, 3] if 낱말점수(c, 4) > 낱말점수(c, 3) else [3, 4]), "규칙 — %s → 수 3 · 4(낱말)" % 등
    점 = sorted(((낱말점수(c, n), -n) for n in range(1, 6)), reverse=True)
    목 = [-n for s, n in 점 if s > 0][:2]
    if 실적카드(c) and 2 not in 목:
        목 = [2] + 목[:1]
    return (목 or [1]), "규칙 — 낱말 %s" % (목 or [1])


def 역할(c, n, 맥락):
    """수 n 안에서의 역할 차례(작을수록 앞) · 부류(수 3 의 화제 · 돈)."""
    t = 글(c)
    등 = c.get("등급")
    꼴 = 계산꼴(c)
    if n == 1:
        if 꼴 == "비중" or (등 == "계산" and re.search(역할말["비중"], t) and 값들(c)):
            return 0, None
        if re.search(역할말["정체"], t):
            return 0, None
        if c.get("풀이용어") or 등 == "일반설명":
            return 1, None
        return 2, None
    if n == 2:
        차례 = {"경로": 0, "극값": 1, "분기": 3, "누계": 4, "연간": 5, "종가": 6}
        if 꼴 in 차례:
            return 차례[꼴], None
        return (2 if 실적카드(c) else 9), None
    if n == 3:
        if 등 == "고객사 · 협력사 발표" or re.search(역할말["돈"], t):
            if 등 == "고객사 · 협력사 발표" or re.search(역할말["고객"], t):
                return 0, "돈"
            if re.search(역할말["지역"], t):
                return 1, "돈"
            if re.search(역할말["점유율"], t):
                return 2, "돈"
            return 3, "돈"
        if 2 in (수칸(c) or []) or 등 == "회사 발화":
            return 0, "화제"
        return 1, "화제"
    if n == 4:
        if "반대진술" in 필수종류(c):
            return 0, None
        if 하락원인판단(c):
            return 1, None
        if 맥락.get("경쟁물러서기") and re.search(역할말["경쟁"], t):
            return 1, None
        if 꼴 == "순위":
            return 3, None
        return 2, None
    if 등 == "레터정의" or 질문판단(c):
        return 0, None
    if 등 == "평가판단":
        return 1, None
    if c.get("풀이용어"):
        return 2, None
    return 3, None


def _위치(맥락, cid, n):
    목 = 맥락["후보"].get(cid) or []
    return 목.index(n) if n in 목 else 9


def 차례키(c, n, 맥락, 교차=None):
    cid = c["id"]
    강 = 0 if 맥락["강제"].get(cid) == n else (1 if cid in 맥락["보호"].get(n, set()) else 2)
    if n == 3 and 교차 is not None:
        _r, 부 = 역할(c, 3, 맥락)
        return (강, 교차.get(cid, 99), 0 if 부 == "화제" else 1, str(cid))
    등순 = 수표[n]["등급순"]
    r, _부 = 역할(c, n, 맥락)
    return (강, r, 등순.index(c.get("등급")) if c.get("등급") in 등순 else 9, -낱말점수(c, n), _위치(맥락, cid, n), str(cid))


def 수3교차(쓸, 맥락):
    """수 3 의 차례 — 화제(이익을 끌어올린 힘)와 돈을 내는 쪽을 번갈아. → {id: 무리 안 자리}."""
    무리 = {"화제": [], "돈": []}
    등순 = 수표[3]["등급순"]
    for cid, c in 쓸.items():
        if 3 in (맥락["후보"].get(cid) or []) or 맥락["강제"].get(cid) == 3:
            r, 부 = 역할(c, 3, 맥락)
            무리[부].append(((r, 등순.index(c.get("등급")) if c.get("등급") in 등순 else 9, -낱말점수(c, 3), _위치(맥락, cid, 3), str(cid)), cid))
    밖 = {}
    for 목 in 무리.values():
        for i, (_k, cid) in enumerate(sorted(목)):
            밖[cid] = i
    return 밖


def 배치(쓸, 맥락):
    """지연 수락 — 카드는 수 목록 차례로 지원하고, 수는 다섯 장까지 차례로 고른다. 밀린 카드는 다음 수로. → ({수: [id]}, {id: 까닭})."""
    교차 = 수3교차(쓸, 맥락)
    선택 = {n: [] for n in 수표}
    다음 = {cid: 0 for cid in 쓸}
    밀림 = {}
    대기 = sorted(쓸)
    while 대기:
        cid = 대기.pop(0)
        목 = [맥락["강제"][cid]] if cid in 맥락["강제"] else (맥락["후보"].get(cid) or [])
        if 다음[cid] >= len(목):
            continue
        n = 목[다음[cid]]
        선택[n].append(cid)
        선택[n].sort(key=lambda x: 차례키(쓸[x], n, 맥락, 교차 if n == 3 else None))
        if len(선택[n]) > 수당카드:
            밀 = 선택[n].pop()
            다음[밀] += 1
            밀림.setdefault(밀, []).append(n)
            대기.append(밀)
    놓인 = {x for v in 선택.values() for x in v}
    빠짐 = {cid: "수 %s — 다섯 장이 찼고 그 수에서 차례가 낮음(본편 2절 회사 소개 후보)" % " · ".join(str(x) for x in 밀림[cid])
          for cid in 쓸 if cid not in 놓인 and 밀림.get(cid)}
    return 선택, 빠짐


def 읽기순(c, n, 맥락, 강제):
    """수 안에서 읽는 차례(고르는 차례와 다르다) — 수 1 정체 → 정의 → 비중 · 수 2 이익 → 극값 · 실적 → 경로(물음은 끝) ·
    수 3 화제 → 돈을 내는 쪽 · 수 4 업종의 방식(반대 진술) → 경쟁 · 위험 → 평가의 판단 → 정황 · 수 5 정의 → 지금 값 → 질문."""
    t, 등, 꼴 = 글(c), c.get("등급"), 계산꼴(c)
    if n == 1:
        if re.search(역할말["정체"], t) and 꼴 != "비중":
            return 0
        if c.get("풀이용어") or 등 == "일반설명":
            return 1
        return 2 if (꼴 == "비중" or re.search(역할말["비중"], t)) else 3
    if n == 2:
        if 꼴 == "경로":
            return 9
        if c["id"] in 강제 and 꼴 != "경로" and 실적카드(c):
            return 0
        return {"극값": 1, "분기": 2, "누계": 2, "연간": 3, "종가": 4}.get(꼴, 2 if 실적카드(c) else 5)
    if n == 3:
        return 0 if 역할(c, 3, 맥락)[1] == "화제" else 1
    if n == 4:
        if "반대진술" in 필수종류(c):
            return 0
        if 등 == "평가판단":
            return 2
        return 3 if 꼴 == "순위" else 1
    if 질문판단(c):
        return 3
    return {"레터정의": 0, "공시": 1, "일반설명": 1, "계산": 2, "평가판단": 2}.get(등, 2)


_숫자꼴 = re.compile(r"\d+(?:\.\d+)?\s*(?:%|조|억|만|배|달러|원)")


def 읽는차례(선택, 쓸, 맥락, 강제, V):
    """수마다 읽는 차례로 — 같은 읽기순 안에서는 고르는 차례(강제 표시는 빼고). 풀이 카드는 같은 수에서 그 용어를 처음 쓴 카드 바로 뒤로
    (용어가 그 카드에 나오는 차례대로). 풀이 카드가 이미 앞에 있으면 그대로 — 처음 나오는 자리에서 풀이하는 셈이다."""
    맥 = dict(맥락, 강제={}, 보호={})
    교차 = 수3교차(쓸, dict(맥락, 강제={cid: n for cid, n in 맥락["강제"].items() if n == 3}))
    밖 = {}
    for n, ids in 선택.items():
        목 = sorted(ids, key=lambda x: (읽기순(쓸[x], n, 맥락, 강제), len(_숫자꼴.findall(글(쓸[x]))),     # 같은 읽기순이면 주장(숫자 적은 것) → 근거
                                       차례키(쓸[x], n, 맥, 교차 if n == 3 else None)))
        옮긴, i = set(), 0
        while i < len(목):
            x = 목[i]
            t = 글(쓸[x])
            j = i + 1
            for _pos, u in sorted((t.find(u), u) for u in V if u in t):
                for d in V[u]:
                    if d in 목 and d != x and d not in 옮긴 and 목.index(d) > i:
                        목.remove(d)
                        목.insert(j, d)
                        옮긴.add(d)
                        j += 1
            i += 1
        밖[n] = 목
    return 밖


# ══════════════════════════════════════════════════════ 7. 용어 · 고유명사

def 용어사전(카드들):
    V = {}
    for c in 카드들:
        for t in c.get("풀이용어") or []:
            t = str(t).strip()
            if t:
                V.setdefault(t, [])
                if c.get("id") not in V[t]:
                    V[t].append(c.get("id"))
    return V


def 첫등장(선택, 쓸, 용어들):
    """용어 → (첫 수, 처음 쓴 카드)."""
    밖 = {}
    for n in sorted(선택):
        for cid in 선택[n]:
            t = 글(쓸[cid])
            for u in 용어들:
                if u not in 밖 and u in t:
                    밖[u] = (n, cid)
    return 밖


def _영문토큰(글_):
    t = re.sub(r"(?<=[가-힣])\s*\([^()]*\)", " ", 글_)                 # 「한글(영문)」 괄호 병기는 이미 풀이된 것
    t = re.sub(r"(?<=[A-Za-z0-9])\s*\([A-Za-z][^()]*\)", " ", t)         # 「약어(긴 영문 이름)」
    return re.findall(r"[A-Za-z][A-Za-z0-9!+\-/&]*(?:\s+[A-Z][A-Za-z0-9!+\-/&]*)*", t)


def 풀이후보(선택, 쓸, V, 고유):
    """풀이용어로 적히지 않은 영문 약어 — 고른 카드에서 낱말로 줍는다(경고)."""
    밖, 본 = [], set()
    for n in sorted(선택):
        for cid in 선택[n]:
            c = 쓸[cid]
            if 계산꼴(c) is not None and str(cid).startswith("k"):
                if 계산꼴(c) != "비중":
                    continue
                t = " ".join(str(v.get("_구분")) for v in 값들(c) if v.get("_구분"))
            else:
                t = 글(c)
            for tok in _영문토큰(t):
                w = tok.strip()
                if len(w) < 2 or w in 본 or w.upper() in 독자약어 or w.upper() in 통화약어 or not re.search(r"[A-Z0-9]", w):
                    continue
                if any(v in w for v in V) or any(w in g or g in w for g in 고유):
                    continue
                본.add(w)
                밖.append({"용어": w, "첫 수": n, "카드": cid, "상태": "풀이 카드 없음", "근거": "낱말로 주움(영문 약어) — 업종 용어 후보 · 경고"})
    return 밖


# ══════════════════════════════════════════════════════ 8. 짓기

def _기간머리(c):
    """카드가 가리키는 기간의 머리(「2026년상반기」) — 기간 칸 · 값의 첫 _기간 · 주장 차례로."""
    첫기간 = next((str(v.get("_기간")) for v in 값들(c) if v.get("_기간")), "")
    for t in (str(c.get("기간") or ""), 첫기간, 글(c)):
        m = re.search(r"\d{4}년(?:\s*(?:상반기|하반기|[1-4]분기|1~3분기))?", t)
        if m:
            return m.group(0).replace(" ", "")
    return None


def _퍼값(c):
    return {str(v.get("글")) for v in 값들(c) if re.fullmatch(r"[+−-]?\d+(?:\.\d+)?%", str(v.get("글", "")))}


def 짓기(입력들, 시세=None, 회차=None):
    """→ (설계 dict, 종료 코드, 화면 줄들)."""
    문서, 없음, 읽은, 읽기경고, 입력회차 = 읽기(입력들)
    회차 = 회차 or 입력회차
    오, 경, 판정 = K.문서검사(문서)
    문서오 = [x for x in 오 if not re.match(r"^[a-z]\d{2,3}[a-z]?: ", x)]
    if 문서오:
        raise 입력오류("; ".join(문서오))
    꼴오류 = {}
    for x in 오:
        m = re.match(r"^([a-z]\d{2,3}[a-z]?): (.*)$", x)
        if m:
            꼴오류.setdefault(m.group(1), []).append(m.group(2))
    판정["_회차"] = 회차
    쓸, 뺀, 뒤, 되살림 = 거르기(판정, 꼴오류)
    맥락 = {"강제": {}, "보호": {}, "후보": {}, "경쟁물러서기": False}

    # ── 긴장
    긴장, 강제, 경로 = 긴장재기(쓸, 판정, 시세)
    맥락["강제"] = dict(강제)

    # ── 물러서기의 근거 — 못지음 · 없음 기록
    기록글 = ["%s %s" % (x.get("무엇", ""), x.get("까닭", "")) for x in 판정.get("못지음") or [] if isinstance(x, dict)] + \
           ["%s %s" % (x.get("항목", ""), x.get("결과", "")) for x in 없음]
    고객없음근거 = [s for s in 기록글 if re.search(r"고객", s) and re.search(r"이름", s)]
    경쟁없음근거 = [s for s in 기록글 if re.search(r"경쟁사", s)]
    고객카드 = [cid for cid, c in 쓸.items() if c.get("등급") == "고객사 · 협력사 발표"
             or any(re.search(r"고객", str(g.get("소개", ""))) for g in (c.get("고유명사") or []) if isinstance(g, dict))]
    맥락["경쟁물러서기"] = bool(경쟁없음근거)

    # ── 수 후보 · 거르기(같은 사실 · 정의 다른 시계열 · 순위 · 수 5 · 수 2 는 실적만)
    후보까닭 = {}
    for cid, c in 쓸.items():
        목, 까 = 수후보(c, 쓸)
        맥락["후보"][cid], 후보까닭[cid] = list(목), 까
    빼기 = {}
    셈카드 = sorted((c for c in 쓸.values() if c.get("등급") == "계산" and 계산꼴(c) != "경로"),
                 key=lambda c: (0 if 계산꼴(c) else 1, str(c["id"])))
    for i, a in enumerate(셈카드):
        if a["id"] in 빼기:
            continue
        for b in 셈카드[i + 1:]:
            if b["id"] in 빼기:
                continue
            if 계산꼴(a) == "비중" and 계산꼴(b) == "비중":
                if {v.get("_구분") for v in 값들(a) if v.get("_구분")} == {v.get("_구분") for v in 값들(b) if v.get("_구분")}:
                    빼기[b["id"]] = "같은 구성의 다른 기간 — 남긴 카드 %s(카드 차례가 앞인 쪽 · 재무기준일 열)" % a["id"]
                continue
            if 계산꼴(b) or not 계산꼴(a):
                continue                       # 같은 사실 견주기는 코드 카드(k) 하나와 갈래가 셈한 카드 하나 사이에서만 — 코드 카드끼리는 서로 다른 사실로 지었다
            공 = _퍼값(a) & _퍼값(b)
            if _기간머리(a) and _기간머리(a) == _기간머리(b) and (len(공) >= 2 or any("." in x for x in 공)):
                빼기[b["id"]] = "같은 사실(%s · %s) — 남긴 카드 %s(셈할 수 있는 주장은 코드가 원자료로 셈한 카드로 · 설계안 5-8 ②)" % (
                    _기간머리(a), " · ".join(sorted(공)), a["id"])
    for cid, c in 쓸.items():
        if 정의다름(c) and cid not in 맥락["강제"] and cid not in 빼기:
            빼기[cid] = "매출 정의가 다른 시계열(카드 함정) — 3분 레터에는 모델 기준 카드만(긴장 판정에 쓰이면 남김)"
    하락원인 = [cid for cid, c in 쓸.items() if 하락원인판단(c)]
    for cid, c in 쓸.items():
        if 계산꼴(c) != "순위" or cid in 빼기:
            continue
        창 = c.get("_창") or {}
        기점 = ((경로 or {}).get("기점") or {}).get("날")
        if not 긴장.get("주가") or 긴장["주가"]["방향"] != "↓":
            빼기[cid] = "하루 등락 순위 — 긴장 꼴이 주가 하락이 아님"
        elif 창.get("방향") != "하락" or not 기점 or str(창.get("시작", "")) < 기점:
            빼기[cid] = "하루 등락 순위 — 기점(%s) 뒤 하락 구간의 순위가 아님" % 기점
        elif not 하락원인:
            빼기[cid] = "하루 등락 순위 — 하락 원인을 다루는 평가판단 카드가 없어 싣지 않음(순위만 두면 독자가 원인을 짐작한다 · 설계안 4-2 · 8절)"
    수5섬 = any(c.get("등급") in ("레터정의", "평가판단") for cid, c in 쓸.items() if cid not in 빼기)
    for cid in sorted(쓸):
        if cid in 빼기:
            continue
        목 = 맥락["후보"][cid]
        if not 수5섬 and 5 in 목:
            목 = [n for n in 목 if n != 5]
            if not 목:
                빼기[cid] = "수 5 가 서지 않음(평가 카드 j — 레터정의 · 평가판단이 없음) — 평가 카드가 오면 수 5 의 뒷받침 후보"
                continue
            후보까닭[cid] += " · 수 5 는 서지 않아 목록에서 뺌"
        if 2 in 목 and not 실적카드(쓸[cid]) and len(목) > 1:
            목 = [n for n in 목 if n != 2]
            후보까닭[cid] += " · 수 2 는 실적 · 주가 카드만(설계 v2) — 다음 수로"
        맥락["후보"][cid] = 목
    for cid, 까 in 빼기.items():
        뺀.append({"id": cid, "까닭": 까})
    남 = {cid: c for cid, c in 쓸.items() if cid not in 빼기}

    # ── 배치 + 용어 풀이 당기기(되풀이 — 강제는 늘기만 한다)
    모든카드 = 판정["카드"]
    V = 용어사전(모든카드)
    V남 = {u: [d for d in ds if d in 남] for u, ds in V.items()}
    결론 = [str(x) for x in 판정.get("결론에_나오는_용어") or []]
    옮김 = {}
    for _ in range(12):
        선택, _밀린 = 배치(남, 맥락)
        자리 = {cid: n for n, ids in 선택.items() for cid in ids}
        첫 = 첫등장(선택, 남, set(V) | set(결론))
        추가 = {}
        for u in sorted(set(첫) | set(결론)):
            defs = V남.get(u) or []
            if not defs:
                continue
            n0 = 첫[u][0] if u in 첫 else ((맥락["후보"].get(defs[0]) or [수칸(남[defs[0]]) or 5])[0])
            if any(자리.get(d) is not None and 자리[d] <= n0 for d in defs):
                continue
            d = sorted(defs, key=lambda x: (0 if 자리.get(x) else 1,
                                            ["공시", "레터정의", "일반설명"].index(남[x].get("등급")) if 남[x].get("등급") in ("공시", "레터정의", "일반설명") else 3,
                                            str(x)))[0]
            if 맥락["강제"].get(d) != n0:
                추가[d] = n0
                if n0 not in (맥락["후보"].get(d) or []):
                    옮김[d] = "수 목록 %s 밖으로 옮김 — 용어 「%s」가 수 %d 에 처음 나와 풀이를 그 수로(용어는 처음 나오는 자리에서 푼다)" % (
                        맥락["후보"].get(d), u, n0)
            if u in 첫:
                맥락["보호"].setdefault(n0, set()).add(첫[u][1])
        if not 추가:
            break
        맥락["강제"].update(추가)
    선택, 밀린 = 배치(남, 맥락)
    선택 = 읽는차례(선택, 남, 맥락, 강제, V)
    자리 = {cid: n for n, ids in 선택.items() for cid in ids}
    for cid, 까 in 밀린.items():
        뺀.append({"id": cid, "까닭": 까})
    for cid in 남:
        if cid not in 자리 and cid not in 밀린:
            뺀.append({"id": cid, "까닭": "놓을 수가 없음(%s)" % 후보까닭.get(cid)})

    # ── 반드시 풀이
    첫 = 첫등장(선택, 남, set(V) | set(결론))
    반드시 = []
    for u in sorted(set(첫) | set(결론), key=lambda u: (첫.get(u, (9, ""))[0], u)):
        defs = V.get(u, [])
        까닭 = (["결론에 나오는 용어"] if u in 결론 else []) + (["고른 카드 %s(수 %d)에 나옴" % (첫[u][1], 첫[u][0])] if u in 첫 else [])
        놓인 = [d for d in defs if d in 자리]
        함정 = ["%s: %s" % (d, h) for d in defs for h in (next((c for c in 모든카드 if c.get("id") == d), {}).get("함정") or [])
              if u in str(h) and re.search(역할말["안풂"], str(h))]
        if 놓인 and not 함정:
            상태 = "풀이 카드 있음"
        elif 놓인:
            상태 = "풀이 카드 없음(정의 카드가 뜻을 풀지 않음 — 카드 함정)"
        elif defs:
            상태 = "풀이 카드 없음(풀이 카드 %s 가 3분 층에서 빠짐)" % " · ".join(str(x) for x in defs)
        else:
            상태 = "풀이 카드 없음"
        반드시.append({"용어": u, "까닭": 까닭, "첫 수": 첫.get(u, (None,))[0], "풀이 카드": 놓인,
                     "풀이 수": sorted({자리[d] for d in 놓인}) or None, "상태": 상태, "함정": 함정 or None})
    고유 = {str(g.get("이름")) for c in 모든카드 for g in (c.get("고유명사") or []) if isinstance(g, dict) and g.get("이름")}
    후보용어 = 풀이후보(선택, 남, V, 고유)

    # ── 고유명사 첫 소개
    고첫, 본 = [], set()
    차례 = [(n, cid) for n in sorted(선택) for cid in 선택[n]]
    for k, (n, cid) in enumerate(차례):
        for g in 남[cid].get("고유명사") or []:
            if not isinstance(g, dict) or not g.get("이름") or g["이름"] in 본:
                continue
            본.add(g["이름"])
            앞 = next(((m, d) for m, d in 차례[:k] if g["이름"] in 글(남[d])), None)
            고첫.append({"이름": g["이름"], "소개": g.get("소개"), "카드": cid, "수": n,
                       "주의": ("앞 수의 카드 %s(수 %d)에 먼저 나옴 — 그 자리에서 소개" % (앞[1], 앞[0])) if 앞 else None})

    # ── 물러서기 · 지을 카드
    지을 = []
    수물 = {n: [] for n in 수표}
    if 긴장["꼴"] == "주가 없음(비상장)":
        수물[2].append("주가 경로 카드가 없음 → 주가 없이 실적 방향만(설계안 4-4 · 비상장)")
    if 선택[3] and not 고객카드:
        근 = (" — 근거: " + 고객없음근거[0][:160]) if 고객없음근거 else ""
        수물[3].append("고객 이름을 적은 카드가 3분 층에 없음 → 고객 산업 · 고객 집중도 · 지역별 매출 카드로(설계안 4-4)%s" % 근)
    화제 = [cid for cid in 선택[3] if 역할(남[cid], 3, 맥락)[1] == "화제"]
    if not 화제:
        수물[2].append("업계 화제 카드가 없음 → 실적 변화 자체를 화제로(수 2) — 설계안 4-4 「수 2를 수 4에 합친다」(v1 차례)를 v2 차례로 옮긴 것")
        if 선택[3]:
            수물[3].append("업계 화제 문장을 빼고 돈을 내는 쪽만")
    if 경쟁없음근거:
        경쟁카드 = [cid for n in (3, 4) for cid in 선택[n] if re.search(역할말["경쟁"], 글(남[cid]))]
        if 경쟁카드:
            수물[4].append("경쟁사 이름이 공시에 없음 → 점유율 · 과점 서술 카드(%s)로(설계안 4-4) — 거론된 수를 전체 수로 쓰지 않는다(열거비망라)"
                         % " · ".join(경쟁카드))
        else:
            수물[4].append("경쟁사 이름도 점유율 카드도 없음 → 경쟁 문장을 뺀다(설계안 4-4)")
    if 긴장.get("주가") and 긴장["주가"]["방향"] == "↓" and not 하락원인:
        수물[4].append("하락 원인을 다루는 평가판단 카드가 없음 → 「왜 내렸나」의 답 문장을 뺀다(물음의 답은 평가판단 카드로만 — 설계 v2)")
        지을.append({"만든곳": "j", "수": 4, "무엇": "주가가 내린 원인에 대한 이 평가의 판단(가를 수 없으면 그렇게 — 필수 한정 「귀속」)"})
    빈까닭 = {1: "정체 · 비중 · 제품 정의 카드가 없음(공시 카드 p · 비중 카드 k)",
            2: "실적 · 주가 카드가 없음(계산 카드 k)",
            3: "업계의 변화 · 고객 · 지역 · 점유율 카드가 없음(공시 카드 p · 조사 카드 r)",
            4: "업종의 방식 · 경쟁 · 위험 카드가 없음(공시 카드 p · 조사 카드 r · 평가판단 j)",
            5: "평가 카드(j — 레터정의 · 평가판단)가 없음 — 평가가 보는 숫자의 정의와 질문은 가정 파일 · 레터 원고에서 짓는 카드"}
    for n in 수표:
        if not 선택[n]:
            수물[n].append("이 수의 문장을 뺀다 — " + 빈까닭[n])
    if 선택[1] and not any(남[cid].get("등급") == "일반설명" for cid in 선택[1]):
        지을.append({"만든곳": "g", "수": 1, "무엇": "생활 접점 — 독자가 이 회사의 제품 · 서비스를 어디서 만나는지(숫자 없이)"})
    if not any(re.search(역할말["정체"], 글(남[cid])) for cid in 선택[1]):
        지을.append({"만든곳": "p", "수": 1, "무엇": "정체 — 공시 「사업의 개요 · 주요 제품」(P 갈래)"})
    for n, 무엇, 곳 in ((3, "업계의 변화 · 고객 · 지역 · 점유율(P 갈래 · 매출스트림 조사의 고객 · 화제 칸)", "p · r"),
                      (4, "회사가 적은 업종의 방식(경기변동 · 경쟁요소 — 반대 진술까지)", "p"),
                      (5, "평가가 보는 숫자의 정의(레터정의) · 지금 값 · 이 평가의 질문(평가판단)", "j")):
        if not 선택[n]:
            지을.append({"만든곳": 곳, "수": n, "무엇": 무엇})
    for x in 반드시 + 후보용어:
        if x["상태"].startswith("풀이 카드 없음"):
            지을.append({"만든곳": "g 또는 j", "수": x.get("첫 수"), "무엇": "용어 「%s」 풀이" % x["용어"]})
    물러서기 = ["수 %d — %s" % (n, s) for n in 수표 for s in 수물[n]]

    # ── 분량
    몫 = {n: len(선택[n]) + (물음몫 if n == 2 and 선택[2] and 긴장["꼴"] else 0) for n in 수표}
    합몫 = sum(몫.values())
    카당 = max(카드당글자[0], min(카드당글자[1], (분량["상한"] // 합몫) if 합몫 else 0))
    수글자 = {n: {"하한": (몫[n] * 카당 * 분량["하한"]) // 분량["상한"], "상한": 몫[n] * 카당} for n in 수표}
    합상 = sum(x["상한"] for x in 수글자.values())
    수문장 = {n: {"하한": max(1, round(수글자[n]["하한"] / 문장셈["하한"])), "상한": max(1, round(수글자[n]["상한"] / 문장셈["상한"]))}
           for n in 수표 if 몫[n]}
    문합 = sum(x["상한"] for x in 수문장.values())
    if 문합 > 문장상한:
        for n in 수문장:
            수문장[n]["상한"] = max(수문장[n]["하한"], (수문장[n]["상한"] * 문장상한) // 문합)
    분량상태 = ("예산 안" if 합상 >= 분량["하한"] else
              "하한 미달 — 카드가 모자라 상한을 다 더해도 %d자(하한 %d자 · A-1). 빠진 수를 채울 카드가 오기 전에는 첫머리가 서지 않는다"
              % (합상, 분량["하한"]))

    # ── 수 문서
    방 = (긴장.get("이익") or {}).get("방향")
    바꿈 = 이름바꿈["성숙"] if 긴장["꼴"] == "성장 없는 성숙" else (이름바꿈["↓"] if 방 == "↓" and (긴장["꼴"] or "").startswith("이익") else {})
    수목록 = []
    for n in 수표:
        ids = 선택[n]
        까닭 = {}
        for cid in ids:
            s = []
            if 맥락["강제"].get(cid) == n:
                if cid in 강제:
                    s.append("긴장 재료(뺄 수 없음)")
                else:
                    u = [x["용어"] for x in 반드시 if cid in x["풀이 카드"]]
                    s.append(("풀이 카드 — 「%s」" % " · ".join(u)) if u else "풀이 카드")
            s.append(후보까닭.get(cid, ""))
            if cid in 옮김:
                s.append(옮김[cid])
            까닭[cid] = " · ".join(x for x in s if x)
        주의 = []
        for cid in ids:
            c = 남[cid]
            if 정의다름(c):
                주의.append("%s 는 매출 정의가 다른 시계열 — 같은 수의 다른 실적 카드와 한 문장에 섞지 않는다(카드 함정)" % cid)
            for f in c.get("필수") or []:
                if isinstance(f, dict) and f.get("종류") in ("반대진술", "귀속", "결의단계", "열거비망라", "경로"):
                    주의.append("%s 필수 한정 「%s」 — %s" % (cid, f.get("종류"), f.get("설명") or f.get("정규식")))
        if n == 2 and 긴장["꼴"] and ids:
            주의.append("물음은 이 수 끝에 한 번 — 방향 「%s」 · 문형은 작가가 정한다(설계안 4-3)" % 긴장["물음 방향"])
        수목록.append({"차례": n, "이름": 바꿈.get(n, 수표[n]["이름"]), "할 일": 수표[n]["할 일"], "선다": bool(ids), "카드": ids,
                    "까닭": 까닭 or None, "글자": 수글자[n] if ids else None, "문장": 수문장.get(n) if ids else None,
                    "물러서기": 수물[n] or None, "주의": 주의 or None})

    설계 = {"형식": 형식, "판": 판, "회사": 판정.get("회사"), "평가기준일": 판정.get("평가기준일"), "재무기준일": 판정.get("재무기준일"),
          "자리": "3분 레터 — 결론 띠 바로 뒤 회사 소개(첫머리)",
          "_만든곳": "스크립트/회사소개설계.py(%s)" % 판,
          "_입력": [os.path.abspath(p).replace("\\", "/") for p in 읽은],
          "_설명": "작가는 수를 차례대로 한 수 한 문단으로 옮긴다(수 5 는 두 문단까지). 수의 「카드」는 읽는 차례다(정체 → 정의 → 비중 · 이익 → 경로 → 물음 · "
                 "화제 → 돈을 내는 쪽 · 업종의 방식 → 경쟁 · 위험 · 정의 → 값 → 질문). 카드에 없는 숫자 · 날짜 · 이름을 쓰지 않는다. "
                 "「할 일」은 작가에게 주는 설명이다 — 연결 문장으로 옮기지 않는다(A-7: 연결 문장에 인과 · 평가 낱말을 넣지 않는다)",
          "분량": {"글자": [분량["하한"], 분량["상한"]], "문장 상한": 문장상한, "수마다 카드": 수당카드, "카드당 글자": 카당,
                 "상한 합": 합상, "상태": 분량상태,
                 "셈": "수마다 (카드 수 + 수 2 의 물음 한 몫) × 카드당 글자 · 카드당 = 1,300 ÷ 몫의 합(%d~%d자 안) · 하한 = 상한 × 1,000 ÷ 1,300 · "
                      "문장 = 글자 ÷ %d(상한) · ÷ %d(하한), 합이 %d 를 넘으면 줄임" % (카드당글자 + (문장셈["상한"], 문장셈["하한"], 문장상한))},
          "긴장": 긴장, "경로": 경로, "수": 수목록, "반드시_풀이": 반드시, "풀이_후보": 후보용어 or None, "고유명사_첫소개": 고첫 or None,
          "평가기준일뒤": 뒤 or None, "평가기준일뒤_되살림": 되살림 or None, "빠진카드": sorted(뺀, key=lambda x: str(x["id"])),
          "물러서기": 물러서기 or None, "지을카드": 지을 or None, "못지음": 판정.get("못지음") or None,
          "함정_메모": 판정.get("함정_메모") or None,
          "검사": {"카드 꼴 오류": [x for x in 오 if re.match(r"^[a-z]\d", x)] or None, "꼴 경고": len(경), "읽기 경고": 읽기경고 or None}}
    코드 = 1 if 꼴오류 else 0
    화면 = ["회사 소개 설계 — %s · 평가기준일 %s" % (설계["회사"], 설계["평가기준일"]),
          "  긴장 %s%s · 확신 %s" % (긴장["꼴"], (" (%s)" % 긴장["하위"]) if 긴장.get("하위") else "", 긴장["확신"])]
    화면 += ["    " + x for x in 긴장["판정 차례"]]
    if 경로:
        화면.append("  경로 — 문턱 %s(카드 %s · 한 달 변동폭 %s) · %s · 기점 뒤 하락 %d번 · 상승 %d번" % (
            경로["문턱"]["쓴 문턱"], 경로["문턱"]["카드 문턱"], 경로["문턱"]["한 달 변동폭"],
            " → ".join("%s %s" % (p["날"][2:], p["글"]) for p in 경로["고른 점"]), 경로["기점 뒤 하락"], 경로["기점 뒤 상승"]))
    for s in 수목록:
        화면.append("  수 %d %s — %s%s" % (s["차례"], s["이름"], " · ".join(s["카드"]) or "(서지 않음)",
                                       (" · 글자 %d~%d · 문장 %d~%d" % (s["글자"]["하한"], s["글자"]["상한"], s["문장"]["하한"], s["문장"]["상한"]))
                                       if s["글자"] else ""))
    화면.append("  분량 — %s" % 분량상태)
    화면.append("  반드시 풀이 — %s" % (" · ".join("%s(%s)" % (x["용어"], x["상태"]) for x in 반드시) or "없음"))
    if 후보용어:
        화면.append("  풀이 후보(경고) — %s" % " · ".join(x["용어"] for x in 후보용어))
    화면.append("  빠진 카드 %d · 평가기준일 뒤 %d · 물러서기 %d · 지을 카드 %d" % (len(뺀), len(뒤), len(물러서기), len(지을)))
    return 설계, 코드, 화면


def main(argv=None):
    ap = argparse.ArgumentParser(description="회사 소개 설계 — 사실 카드에서 다섯 수 · 긴장 · 반드시 풀이 · 분량을 짓는다")
    ap.add_argument("입력", nargs="+", help="회차 폴더 하나 또는 카드 문서(.json) 여럿")
    ap.add_argument("--낼", help="쓸 곳(기본 <회차>/_raw/회사소개설계.json · 파일 입력이면 첫 파일 옆)")
    ap.add_argument("--회차", help="시세 파일(경로 카드의 _경로.파일)을 찾을 회차 폴더 — 읽기만 한다")
    ap.add_argument("--시세", help="시세 파일을 바로 준다(변동성 문턱에 쓴다 · 읽기만 한다)")
    인 = ap.parse_args(argv)
    try:
        설계, 코드, 화면 = 짓기(인.입력, 인.시세, 인.회차)
    except 입력오류 as e:
        print("입력 오류 — %s" % e)
        return 2
    낼 = 인.낼
    if not 낼:
        if len(인.입력) == 1 and os.path.isdir(인.입력[0]):
            낼 = os.path.join(인.입력[0], 산출)
        else:
            낼 = os.path.join(os.path.dirname(os.path.abspath(인.입력[0])), "회사소개설계.json")
    os.makedirs(os.path.dirname(os.path.abspath(낼)), exist_ok=True)
    io.open(낼, "w", encoding="utf-8").write(json.dumps(설계, ensure_ascii=False, indent=1))
    for L in 화면:
        print(L)
    print("→ %s%s" % (낼, " (꼴 오류 카드를 빼고 지음)" if 코드 else ""))
    return 코드


if __name__ == "__main__":
    sys.exit(main())

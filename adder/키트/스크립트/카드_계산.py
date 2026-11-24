# -*- coding: utf-8 -*-
"""카드_계산 — 셈할 수 있는 사실을 코드가 원자료로 빠짐없이 셈해 사실 카드로 짓는다(레터 문체 3단계 B2 · 2026-10-26).

왜 있나
    순위 · 최고 · 최저 · 비중 · 증감 · 주가 경로처럼 셈할 수 있는 사실을 작가(LLM)가 고르거나 다른 글(레터 본편 포함)을 인용해
    카드에 옮기면 그 글의 틀린 사실이 그대로 옮겨진다(실측 2026-10-26 — 현행 회차 레터의 「두 하락에서 가장 크게 내린 날」 문장이
    같은 레터의 시세 CSV 로 셈한 순위와 달랐다. 실험 0회차의 두 초안은 고점 뒤 되오름을 빠뜨려 하락이 한 번뿐인 것처럼 썼다).
    그래서 이 갈래는 원자료만 읽어 셈하고, 어느 점을 실을지 고르지 않는다 — 문턱을 넘는 꺾임은 모두 싣는다.
    카드의 꼴은 `카드.py` 가 정한다(이 파일은 그 꼴을 바꾸지 않는다). 지은 문서는 `카드.문서검사` 를 통과해야 쓴다.

읽는 원자료(회차 폴더 기준 · 네트워크로 받지 않는다)
    레터_주가.csv                     일별 종가(「#」 주석 줄 = 출처 · 머리 date,close · 날짜 20260630 또는 2026-06-30)
    가정_<회사>.json                  메타(회사명 · 평가기준일 · 재무기준일 · 표시통화 · 금액단위 · 주당단위) · 기간 · 13번 원천
                                      (62 매출액 · 66 영업이익 · 85 + s 매출 구분 s 의 실적 — 가정_스키마.md) · 구조.매출구분
    레터_초안.장부.json               (있으면) 값과 3분 글이 같은 장부 키를 카드 값에 붙인다. 회차에 가정 파일이 여럿이면 장부의 가정해시로 고른다
    _raw/dart_앵커시계열.json         (국내) 사업보고서 손익의 연간 매출 · 영업이익(당기 · 전기 · 전전기 — 그 해의 보고서를 먼저)
    _raw/dart_재무_연결_<해>_<보고서>.json  (국내) 재무기준일 정기보고서 — 3개월(thstrm) · 누계(thstrm_add) · 전년 같은 기간(frmtrm_q · frmtrm_add)
    _raw/앵커_시계열.json · _raw/companyfacts.json   (미국) 연간 시계열 · 10-Q 분기 · 누계(태그 후보는 sec_앵커.TAGS)

짓는 카드(id 접두 k · 등급 「계산」)
    k01        주가 경로 — 조회 구간(시세 첫날 ~ 평가기준일)의 꺾임 전부(직전 극값에서 문턱 넘게 되돌린 고점 · 저점 · 끝의 극값) ·
               구간 최고 · 최저 · 기준점(구간 첫날 · 평가기준일이 든 해의 첫 거래일 · 재무기준일 · 평가기준일). 필수 한정 「경로」
    k02        평가기준일 종가 · 재무기준일 종가(두 날이 다르면 그사이 변화)
    k03        평가기준일 뒤 주가(시세 파일에 있을 때) — 사건일 = 파일의 마지막 날 → 카드 검사가 「평가기준일뒤」 로 판정
    k101 …     꺾임 사이 구간마다 하루 등락 순위 — 하락 구간은 내린 날, 상승 구간은 오른 날. 보이는 자릿수에서 같으면 동률을 함께 적는다
    k21        연간 실적 — 매출 · 영업이익 · 영업이익률(해마다)
    k22        재무기준일 누계 실적과 전년 같은 기간
    k23        최근 분기 · 앞 분기 · 전년 같은 분기
    k24        연간 최고 · 최저 · 직전 사이클 정점(가장 낮은 해 앞의 최고) · 최근 누계와의 견줌
    k31 · k32  매출 구성 비중(재무기준일 열 · 최근 연간 열) — 13번 원천에 맨 위 구분 둘 이상의 실적이 있을 때만
    덧글자 b   앵커 시계열의 매출 정의가 모델 매출(원천 62)과 다르면 그 시계열을 따로 짓는다(k21b · k24b) — 섞지 않는다
    지을 수 없는 것은 문서의 「못지음」 목록에 까닭과 함께 남긴다(지어내지 않는다).

반올림 — 사람 눈의 반올림(ROUND_HALF_UP)
    종가 · 금액을 원자료에 적힌 글자 그대로 십진수로 읽어 정확한 비(분수)를 만든 뒤, 보일 자리에서 **한 번만** 반올림한다.
    반올림한 값을 다시 반올림하지 않는다(−14.6476% 를 소수 둘째 −14.65% 로 적은 뒤 첫째로 다시 올리면 −14.7% 가 되는 잘못).
    동률 = 보이는 자릿수(하루 등락은 3분 레터의 소수 첫째 자리 %)에서 같은 글이 나오는 것. 그때는 처음 갈리는 자리의 값을 함께 적는다.
    3분 레터의 꼴(값.글)은 레터.py 의 어림 꼴(어림주당 · 어림금액 · 퍼N)과 같은 규칙이되 반올림만 ROUND_HALF_UP 이다
    (레터.py 는 파이썬 round · format 이라 정확히 반에 걸린 값에서 짝수 쪽으로 간다 — 2,925,000원 → 「292만 원」).
    본편 꼴은 값의 「본편」 칸(주가 「291만 9,000원」 · 「71.95달러」, 금액 「131.90조 원」, 하루 등락은 소수 둘째 자리).
    등락 값에는 부호 없는 크기 글(「15.4%」 — 「내렸다」와 함께 쓰는 꼴)도 함께 싣는다(값의 「_꼴」 = 크기).

계산 칸의 식(카드설정 「식.이름」 — 카드 감사가 다시 셈한다)
    숫자는 원자료의 글자 그대로. 글이 「%」 로 끝나면 식은 비(0.744)이고 「%p」 면 식이 이미 ×100 이다. 「자리」 = 글의 소수 자리.
    csv_max(파일) · csv_min(파일)          파일 전체 종가의 최고 · 최저
    csv_max(파일, 시작, 끝) · csv_min(…)  시작 ≤ 날 ≤ 끝(YYYY-MM-DD · 양끝 포함)의 최고 · 최저 — 카드 감사가 구현할 뜻(제안)
    순위 카드의 「_창」 칸은 그 순위를 다시 셀 창(파일 · 시작 다음 거래일 ~ 끝 · 방향 · 순위수)이다.

쓰는 법
    python 스크립트/카드_계산.py <회차 폴더>                          # → <회차>/_raw/카드/계산.json
    python 스크립트/카드_계산.py <회차> --낼 경로.json [--가정 가정_X.json] [--문턱 0.2] [--순위 3] [--시작 YYYY-MM-DD]
    종료 코드 — 0 지음 · 1 카드 검사 오류(쓰지 않음) · 2 입력 오류

회사 · 업종 이름은 이 파일에 없다.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import glob
import io
import json
import os
import re
import sys
from decimal import ROUND_HALF_UP, Decimal, localcontext
from fractions import Fraction

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
import 카드 as K            # noqa: E402
import 기준일 as 기준        # noqa: E402
import 기간축 as 축모듈      # noqa: E402
import 앵커읽기 as 앵        # noqa: E402

판 = "카드_계산 v1"
주가파일 = "레터_주가.csv"
장부파일 = "레터_초안.장부.json"
기본문턱 = 0.20            # 종가가 직전 극값에서 이만큼 넘게 되돌려야 꺾임으로 센다
기본순위 = 3               # 구간마다 싣는 하루 등락의 수(끝 자리와 보이는 자릿수에서 같은 날은 더 싣는다)
보이는자리 = 1             # 하루 등락의 3분 레터 자릿수(소수 첫째 자리 %)
매출줄, 영업줄 = "62", "66"   # 13번 원천 — 매출액 · 영업이익(가정_스키마.md)
구분줄밑 = 85              # 매출 구분 s 의 실적 = 원천 85 + s(86~90 · 기타 91)
통화말 = {"KRW": "원", "USD": "달러", "JPY": "엔", "EUR": "유로", "GBP": "파운드", "CNY": "위안", "TWD": "대만달러", "HKD": "홍콩달러"}
# ↑ 레터._통화말 과 같다(_카드계산시험 이 맞댄다)
_서수 = ["", "가장", "둘째로", "셋째로", "넷째로", "다섯째로", "여섯째로", "일곱째로", "여덟째로", "아홉째로", "열째로"]
_차례 = ["", "첫", "둘째", "셋째", "넷째", "다섯째", "여섯째", "일곱째", "여덟째", "아홉째", "열째"]
_한글수 = ["영", "한", "두", "세", "네", "다섯", "여섯", "일곱", "여덟", "아홉", "열", "열한", "열두", "열세", "열네", "열다섯", "열여섯", "열일곱",
        "열여덟", "열아홉", "스무"]


def _몇(n, 단위):
    """「두 번」 · 「열두 해」 · 스물이 넘으면 「23번」."""
    return ("%s %s" % (_한글수[n], 단위)) if 0 < n < len(_한글수) else "%d%s" % (n, 단위)
_크기꼴 = "크기(부호 없이 — 「내렸다 · 올랐다」와 함께)"


class 입력오류(Exception):
    pass


# ══════════════════════════════════════════════════════ 1. 숫자 · 날짜의 꼴

def 분(x):
    """원자료의 숫자 → 정확한 분수. 글은 글자 그대로(쉼표만 뗀다), 실수는 repr(가장 짧은 되돌림 글)로 읽는다."""
    if isinstance(x, Fraction):
        return x
    if x is None or isinstance(x, bool):
        raise ValueError("숫자가 아님")
    if isinstance(x, int):
        return Fraction(x)
    if isinstance(x, float):
        return Fraction(Decimal(repr(x)))
    return Fraction(Decimal(str(x).replace(",", "").strip()))


def 수글(x):
    """식에 넣는 숫자 글 — 원자료에 적힌 꼴(정수로 떨어지는 실수는 정수로)."""
    if isinstance(x, str):
        return x.replace(",", "").strip()
    if isinstance(x, float):
        return str(int(x)) if x.is_integer() else repr(x)
    if isinstance(x, Fraction):
        return str(x.numerator) if x.denominator == 1 else "(%d / %d)" % (x.numerator, x.denominator)
    return str(x)


def 십(fr, 자리):
    """분수 → 십진수, 자리에서 사람 눈의 반올림 한 번(자리가 음수면 십 · 백 자리)."""
    fr = 분(fr)
    with localcontext() as c:
        c.prec = 80
        d = Decimal(fr.numerator) / Decimal(fr.denominator)
        return d.quantize(Decimal(1).scaleb(-자리), rounding=ROUND_HALF_UP)


def _자릿수(a):
    """|a| 의 가장 높은 자리(10 의 몇 제곱) — 0 이면 0."""
    a = abs(분(a))
    if not a:
        return 0
    with localcontext() as c:
        c.prec = 80
        return (Decimal(a.numerator) / Decimal(a.denominator)).adjusted()


def _쉼(q, 자리):
    return ("{:,.%df}" % max(자리, 0)).format(q)


def _음(fr, 글, q):
    return ("−" + 글) if (fr < 0 and q != 0) else 글


def 퍼글(fr, 자리=1, 부호=False):
    """비 → 「74.4%」 · 「−15.4%」(부호 = 양수에도 +)."""
    fr = 분(fr)
    q = 십(abs(fr) * 100, 자리)
    글 = _쉼(q, 자리) + "%"
    if q == 0:
        return 글
    if fr < 0:
        return "−" + 글
    return ("+" + 글) if 부호 else 글


def 포글(fr, 자리=1):
    """비의 차 → 「+33.3%p」."""
    fr = 분(fr)
    q = 십(abs(fr) * 100, 자리)
    글 = _쉼(q, 자리) + "%p"
    return 글 if q == 0 else (("−" if fr < 0 else "+") + 글)


def 배글(fr, 자리=1):
    fr = 분(fr)
    q = 십(abs(fr), 자리)
    return _음(fr, _쉼(q, 자리) + "배", q)


def 주가3(v, 단위):
    """3분 레터의 주가(레터.어림주당글 과 같은 규칙) → (글, 나눗수, 자리)."""
    v = 분(v)
    a = abs(v)
    if 단위 in ("원", "엔"):
        n = 십(a / 10000, 0)
        if n >= 10:
            return _음(v, "{:,}만 {}".format(int(n), 단위), n), 10000, 0
        if a >= 10000:
            q = 십(a / 10000, 1)
            return _음(v, "{:.1f}만 {}".format(q, 단위), q), 10000, 1
        자 = 1 - _자릿수(a)
        q = 십(a, 자)
        return _음(v, "{:,.0f}{}".format(q, 단위), q), 1, min(0, 자)
    자 = 2 - _자릿수(a)
    q = 십(a, 자)
    표 = 0 if q >= 100 else (1 if q >= 10 else (2 if q >= 1 else 3))
    return _음(v, ("{:,.%df}{}" % 표).format(q, 단위), q), 1, min(표, 자)


def 주가본(v, 단위):
    """본편의 주가 — 원 · 엔은 「291만 9,000원」, 그 밖은 소수 둘째 「71.95달러」."""
    v = 분(v)
    a = abs(v)
    if 단위 in ("원", "엔") and a.denominator == 1:
        n = int(a)
        만, 나 = divmod(n, 10000)
        if 만:
            글 = "{:,}만 {:,}{}".format(만, 나, 단위) if 나 else "{:,}만 {}".format(만, 단위)
        else:
            글 = "{:,}{}".format(n, 단위)
        return ("−" + 글) if v < 0 else 글
    q = 십(a, 2)
    return _음(v, "{:,.2f}{}".format(q, 단위), q)


def 금액3(v, 통화):
    """3분 레터의 금액(레터.어림금액글 과 같은 규칙) — v 는 통화 단위의 절대 금액 → (글, 표시 단위, 자리)."""
    v = 분(v)
    a = abs(v)
    if 통화 == "KRW":
        if a >= 10 ** 13:
            u, 자, 말 = 10 ** 12, 0, "조 원"
        elif a >= 10 ** 12:
            u, 자, 말 = 10 ** 12, 1, "조 원"
        elif a >= 10 ** 8:
            u, 자, 말 = 10 ** 8, 0, "억 원"
        else:
            u, 자, 말 = 10 ** 4, 0, "만 원"
    else:
        m = 통화말.get(통화, 통화)
        if a >= 10 ** 9:
            u, 자, 말 = 10 ** 8, 0, "억 " + m
        elif a >= 10 ** 7:
            u, 자, 말 = 10 ** 8, 1, "억 " + m
        else:
            u, 자, 말 = 10 ** 4, 0, "만 " + m
    q = 십(a / u, 자)
    return _음(v, _쉼(q, 자) + 말, q), u, 자


def 금액본(v, 통화):
    """본편의 금액(레터.금액글 과 같은 규칙)."""
    v = 분(v)
    a = abs(v)
    if 통화 == "KRW":
        표 = ((10 ** 12, 10 ** 12, 2, "조 원"), (10 ** 10, 10 ** 8, 0, "억 원"), (10 ** 9, 10 ** 8, 1, "억 원"),
             (10 ** 8, 10 ** 8, 2, "억 원"), (10 ** 4, 10 ** 4, 0, "만 원"), (0, 1, 0, "원"))
    else:
        m = 통화말.get(통화, 통화)
        표 = ((10 ** 10, 10 ** 8, 0, "억 " + m), (10 ** 8, 10 ** 8, 1, "억 " + m), (10 ** 4, 10 ** 4, 0, "만 " + m), (0, 1, 0, m))
    for 문턱, u, 자, 말 in 표:
        if a >= 문턱:
            q = 십(a / u, 자)
            return _음(v, _쉼(q, 자) + 말, q)
    return "0"


def 나눔식(수, 나눗):
    """「수 / 나눗」 — 나눗이 1 보다 작으면 곱셈으로."""
    나눗 = 분(나눗)
    if 나눗 == 1:
        return 수
    if 나눗.denominator == 1:
        return "%s / %d" % (수, 나눗.numerator)
    if 나눗.numerator == 1:
        return "%s * %d" % (수, 나눗.denominator)
    return "%s * %d / %d" % (수, 나눗.denominator, 나눗.numerator)


def 날(s):
    if isinstance(s, _dt.date):
        return s
    return _dt.date.fromisoformat(str(s)[:10])


def 긴날(d):
    d = 날(d)
    return "%d년 %d월 %d일" % (d.year, d.month, d.day)


def 날들(d, 해):
    """카드 「날짜」 칸 — 긴 꼴, 평가기준일이 든 해면 짧은 꼴도(다른 해의 짧은 꼴은 해가 헷갈려 넣지 않는다)."""
    d = 날(d)
    return [긴날(d)] + (["%d월 %d일" % (d.month, d.day)] if d.year == 해 else [])


def 말날(d, 해):
    """주장 글의 날짜 — 평가기준일이 든 해면 짧은 꼴."""
    d = 날(d)
    return ("%d월 %d일" % (d.month, d.day)) if d.year == 해 else 긴날(d)


_숫자받침 = {"0": True, "1": True, "2": False, "3": True, "4": False, "5": False, "6": True, "7": True, "8": True, "9": False}


def _괄호앞(말):
    """조사를 고를 말 — 끝에 붙은 괄호 덧말 「(…)」 은 떼고 그 앞의 말을 본다(레터.괄호앞 과 같은 규칙)."""
    s = ("%s" % (말 or "")).rstrip("`”’\"' ")
    for _ in range(4):
        if not s.endswith(")"):
            break
        깊, i = 0, len(s) - 1
        while i >= 0:
            if s[i] == ")":
                깊 += 1
            elif s[i] == "(":
                깊 -= 1
                if 깊 == 0:
                    break
            i -= 1
        if i < 0:
            s = s[:-1].rstrip("`”’\"' ")
            continue
        앞 = s[:i].rstrip("`”’\"' ")
        s = 앞 if 앞 else s[i + 1:-1].strip()
    return s


def 조(말, 있음, 없음):
    """말 + 받침에 맞는 조사(레터.조사 와 같은 규칙 — ㄹ 받침 · 1 · 7 · 8 뒤 「으로」 는 「로」, % 는 받침 없음, 숫자는 읽는 소리, 영문은 음가)."""
    글 = _괄호앞(말)
    끝 = 글[-1] if 글 else ""
    if "가" <= 끝 <= "힣":
        종 = (ord(끝) - 0xAC00) % 28
        if 종 == 8 and 있음.startswith("으로"):
            return 말 + 없음
        return 말 + (없음 if 종 == 0 else 있음)
    if 끝 == "%":
        return 말 + 없음
    if 끝 in _숫자받침:
        if 끝 in "178" and 있음.startswith("으로"):
            return 말 + 없음
        return 말 + (있음 if _숫자받침[끝] else 없음)
    if 끝.isascii() and 끝.isalpha():
        받 = 끝.upper() in "LMNR"
        if 받 and 끝.upper() in "LR" and 있음.startswith("으로"):
            return 말 + 없음
        return 말 + (있음 if 받 else 없음)
    return 말 + 있음


def 변화글(앞, 뒤):
    """앞 → 뒤 — 두 배 이상이면 배수, 그 밖은 부호 붙은 %."""
    r = 분(뒤) / 분(앞)
    return 배글(r, 1) if r >= 2 else 퍼글(r - 1, 1, 부호=True)


def 움직임(앞, 뒤):
    """「6.1% 올랐다」 · 「52.3% 내렸다」 · 「4.3배가 됐다」."""
    r = 분(뒤) / 분(앞)
    if r >= 2:
        return 조(배글(r, 1), "이", "가") + " 됐다"
    if r > 1:
        return 퍼글(r - 1, 1) + " 올랐다"
    if r < 1:
        return 퍼글(1 - r, 1) + " 내렸다"
    return "같았다"


def 견줌(앞, 뒤):
    """뒤가 앞보다 「56.7% 낮다」 · 「2.1배다」."""
    r = 분(뒤) / 분(앞)
    if r >= 2:
        return 조(배글(r, 1), "이다", "다")
    if r > 1:
        return 퍼글(r - 1, 1) + " 높다"
    if r < 1:
        return 퍼글(1 - r, 1) + " 낮다"
    return "같다"


def _날글csv(t):
    t = ("%s" % t).strip()
    if re.match(r"^\d{8}$", t):
        return "%s-%s-%s" % (t[:4], t[4:6], t[6:])
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", t)
    return "%04d-%02d-%02d" % (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def _해앞(d, 해수=1):
    """같은 달 · 날의 앞 해(2월 29일은 28일로)."""
    return _dt.date(d.year - 해수, d.month, min(d.day, 28) if d.month == 2 else d.day)


# ══════════════════════════════════════════════════════ 2. 카드 조각

def _값(글, 본편=None, 장부=None, 단위=None, **덧):
    v = {"글": 글}
    if 본편 and 본편 != 글:
        v["본편"] = 본편
    if 장부:
        v["장부"] = 장부
    if 단위:
        v["단위"] = 단위
    for k, x in 덧.items():
        if x is not None:
            v["_" + k] = x
    return v


def _계(이름, 식, 글, 자리=None):
    k = {"이름": 이름, "식": 식, "글": 글}
    if 자리 is not None:
        k["자리"] = 자리
    return k


def _필(종류, 정규식, 설명):
    re.compile(정규식)
    return {"종류": 종류, "정규식": 정규식, "설명": 설명}


def _겹없이(목록, 열쇠=None):
    본, 밖 = set(), []
    for x in 목록:
        k = 열쇠(x) if 열쇠 else json.dumps(x, ensure_ascii=False, sort_keys=True)
        if k in 본:
            continue
        본.add(k)
        밖.append(x)
    return 밖


def _변화값(앞, 뒤, 앞수, 뒤수, 이름):
    """앞 → 뒤 의 변화 — 두 배 이상 오르면 배수, 그 밖은 부호 붙은 %(와 부호 없는 크기). → (값 목록, 계산)."""
    r = 분(뒤) / 분(앞)
    if r >= 2:
        글 = 배글(r, 1)
        return [_값(글, 배글(r, 2), 단위="배수")], _계(이름, "%s / %s" % (뒤수, 앞수), 글, 1)
    d = r - 1
    글 = 퍼글(d, 1, 부호=True)
    값들 = [_값(글, 퍼글(d, 2, 부호=True), 단위="비율")]
    크기 = 퍼글(abs(d), 1)
    if 크기 != 글:
        값들.append(_값(크기, 단위="비율", 꼴=_크기꼴))
    정 = 퍼글(abs(d), 0)                              # 3분 레터가 흔히 쓰는 정수 자리(「55% 내렸다」) — 같은 값의 다른 자릿수(순위 카드에는 싣지 않는다)
    if 정 != 크기:
        값들.append(_값(정, 단위="비율", 꼴="정수 자리 · 부호 없이"))
    return 값들, _계(이름, "%s / %s - 1" % (뒤수, 앞수), 글, 1)


# ══════════════════════════════════════════════════════ 3. 원자료 읽기

class 원천글:
    """인용이 원천에 글자 그대로 있는지 — 있을 때만 「인용」 을 붙인다(공백 정규화 · JSON 은 다시 쓴 꼴도 — 실험 검사기 F4 와 같은 눈)."""

    def __init__(self, 회차):
        self.회차 = 회차
        self.캐시 = {}

    def 글(self, 파일):
        if 파일 not in self.캐시:
            p = os.path.join(self.회차, 파일)
            try:
                t = io.open(p, encoding="utf-8-sig", errors="replace").read()
            except OSError:
                t = ""
            if 파일.endswith(".json") and t:
                try:
                    t = t + "\n" + json.dumps(json.loads(t), ensure_ascii=False)
                except ValueError:
                    pass
            self.캐시[파일] = re.sub(r"\s+", " ", t)
        return self.캐시[파일]

    def 원(self, 파일, 인용=None, **덧):
        o = {"파일": 파일}
        if 인용 and re.sub(r"\s+", " ", 인용).strip() in self.글(파일):
            o["인용"] = 인용
        for k, x in 덧.items():
            if x is not None:
                o[k] = x
        return o


class 행:
    __slots__ = ("날", "d", "v", "글", "줄")

    def __init__(self, 날iso, v, 글, 줄):
        self.날, self.d, self.v, self.글, self.줄 = 날iso, _dt.date.fromisoformat(날iso), v, 글, 줄


def 주가읽기(p):
    """레터_주가.csv → (출처 주석 줄들, [행 …] 날짜 차례). 같은 날이 두 번이면 뒤엣것."""
    출처, 머리, 모음 = [], None, {}
    for L in io.open(p, encoding="utf-8-sig").read().splitlines():
        t = L.strip()
        if not t:
            continue
        if t.startswith("#"):
            출처.append(t.lstrip("#").strip())
            continue
        칸 = [c.strip() for c in t.split(",")]
        if 머리 is None:
            머리 = [c.lower() for c in 칸]
            continue
        try:
            d = _날글csv(칸[머리.index("date")])
            글 = 칸[머리.index("close")]
            v = 분(글)
        except (ValueError, IndexError, ArithmeticError):
            continue
        if d and v > 0:
            모음[d] = 행(d, v, 수글(글), t)
    return 출처, [모음[k] for k in sorted(모음)]


class 장부색인:
    """레터 장부의 숫자 — 값과 3분 글이 같은 키를 카드 값에 붙인다. 값만 같고 글이 다르면 「_장부값같음」 으로."""

    def __init__(self, 회차):
        self.키 = {}
        self.있음 = False
        self.가정해시 = None
        p = os.path.join(회차, 장부파일)
        if os.path.isfile(p):
            d = json.load(io.open(p, encoding="utf-8"))
            self.있음 = True
            self.가정해시 = d.get("가정해시")
            for x in d.get("숫자", []) or []:
                if x.get("키"):
                    self.키.setdefault(x["키"], []).append(x)

    @staticmethod
    def _같(a, b):
        try:
            a = 분(a)
        except (ValueError, ArithmeticError, TypeError):
            return False
        b = 분(b)
        return abs(a - b) <= Fraction(1, 10 ** 9) * max(1, abs(b))

    def _붙(self, 후보, v, 글):
        글맞음 = sorted(k for k in 후보 if any(self._같(x.get("값"), v) and x.get("글") == 글 for x in self.키.get(k, [])))
        값맞음 = sorted(k for k in 후보 if any(self._같(x.get("값"), v) for x in self.키.get(k, [])))
        return (글맞음[0] if 글맞음 else None), (값맞음[0] if (값맞음 and not 글맞음) else None)

    def 종가(self, 날iso, v, 글):
        후보 = []
        if "주:종가:" + 날iso in self.키:
            후보.append("주:종가:" + 날iso)
        for k in self.키:
            if k.startswith("주:") and k.endswith(":종가") and k not in 후보:
                날키 = k[: -len("종가")] + "날말"
                if any(x.get("글") == 긴날(날iso) for x in self.키.get(날키, [])):
                    후보.append(k)
        return self._붙(후보, v, 글)

    def 실적(self, 열, v, 글):
        return self._붙([k for k in self.키 if k.startswith("R:기준:") and k.endswith(":" + 열)], v, 글)


def 가정찾기(회차, 지정, 장부):
    if 지정:
        p = 지정 if os.path.isabs(지정) else os.path.join(회차, 지정)
        if not os.path.isfile(p):
            raise 입력오류("가정 파일이 없음 — %s" % p)
        return p
    후보 = [p for p in sorted(glob.glob(os.path.join(회차, "가정_*.json")))
          if not re.search(r"가정_(예시|템플릿|스키마)", os.path.basename(p))]
    if len(후보) == 1:
        return 후보[0]
    if 장부.가정해시:
        import 가정해시                                  # noqa: PLC0415
        맞음 = [p for p in 후보 if 가정해시.전체(json.load(io.open(p, encoding="utf-8"))) == 장부.가정해시]
        if len(맞음) == 1:
            return 맞음[0]
    raise 입력오류("가정 파일을 하나로 정하지 못함(후보 %s) — --가정 으로 지정하십시오" % [os.path.basename(p) for p in 후보])


def _단위배(메타):
    """메타.금액단위 → 곱수(백만원 → 1e6). 레터.단위배 와 같은 읽기."""
    글 = ("%s" % ((메타 or {}).get("금액단위") or "")).strip()
    for 말, 곱 in (("십억", 10 ** 9), ("백만", 10 ** 6), ("억", 10 ** 8), ("천", 10 ** 3), ("만", 10 ** 4)):
        if 글.startswith(말):
            return Fraction(곱)
    return Fraction(1)


# ══════════════════════════════════════════════════════ 4. 주가 경로 · 순위

def 꺾임찾기(행들, 문턱):
    """종가의 꺾임 — 직전 극값에서 문턱 넘게 되돌린 고점 · 저점(번갈아). → [{"i", "종류": 고 · 저, "확정"}].
    확정 = 그 뒤로 문턱만큼 되돌렸다. 끝의 극값(문턱만큼 되돌리기 전에 구간이 끝남)은 확정 거짓으로 덧붙인다.
    아직 문턱만큼 떨어지지 않은 극점을 넘어서면(저점 아래 · 고점 위) 그 극점을 옮긴다 — 그래서 이웃한 고점 사이의 저점은 그 사이의 최저다."""
    th = 분(문턱)
    n = len(행들)
    점, 확 = [], False
    hi = lo = ext = 0
    for i in range(1, n):
        v = 행들[i].v
        if not 점:
            if v > 행들[hi].v:
                hi = i
            if v < 행들[lo].v:
                lo = i
            if lo < i and v >= 행들[lo].v * (1 + th):
                점, ext, 확 = [[lo, "저"]], i, True
            elif hi < i and v <= 행들[hi].v * (1 - th):
                점, ext, 확 = [[hi, "고"]], i, True
            continue
        끝점 = 점[-1]
        if 끝점[1] == "저":
            if 확 and v <= 행들[ext].v * (1 - th):
                점.append([ext, "고"])
                ext, 확 = i, True
                continue
            if v < 행들[끝점[0]].v:
                끝점[0], ext, 확 = i, i, False
                continue
            if v > 행들[ext].v:
                ext = i
            if not 확 and 행들[ext].v >= 행들[끝점[0]].v * (1 + th):
                확 = True
        else:
            if 확 and v >= 행들[ext].v * (1 + th):
                점.append([ext, "저"])
                ext, 확 = i, True
                continue
            if v > 행들[끝점[0]].v:
                끝점[0], ext, 확 = i, i, False
                continue
            if v < 행들[ext].v:
                ext = i
            if not 확 and 행들[ext].v <= 행들[끝점[0]].v * (1 - th):
                확 = True
    밖 = [{"i": i, "종류": k, "확정": True} for i, k in 점]
    if 밖:
        밖[-1]["확정"] = 확
        if 확 and ext != 밖[-1]["i"]:
            밖.append({"i": ext, "종류": "고" if 밖[-1]["종류"] == "저" else "저", "확정": False})
    return 밖


def _csv식(함수, 파일, 시작, 끝, 전체):
    if 전체:
        return "%s('%s')" % (함수, 파일)
    return "%s('%s', '%s', '%s')" % (함수, 파일, 시작, 끝)


def 하루등락(행들, a, b):
    """(a, b] 의 하루 등락 — [(행, 앞 행, 비 − 1) …]."""
    return [(행들[j], 행들[j - 1], 행들[j].v / 행들[j - 1].v - 1) for j in range(a + 1, b + 1)]


def 순위고르기(등락, 방향, 순위수, 자리=보이는자리):
    """방향(하락 · 상승) 쪽 날만 정확한 값으로 줄 세워 순위수만큼 — 끝 자리와 보이는 자릿수에서 같은 날은 더 싣는다.
    → [[(행, 앞, r, 글) …] 보이는 자릿수의 동률 묶음 …]."""
    쪽 = [x for x in 등락 if (x[2] < 0 if 방향 == "하락" else x[2] > 0)]
    쪽.sort(key=lambda x: (x[2] if 방향 == "하락" else -x[2], x[0].날))
    글 = [퍼글(x[2], 자리, 부호=True) for x in 쪽]
    k = min(순위수, len(쪽))
    while 0 < k < len(쪽) and 글[k] == 글[k - 1]:
        k += 1
    묶음 = []
    for x, g in zip(쪽[:k], 글[:k]):
        if 묶음 and 묶음[-1][0][3] == g:
            묶음[-1].append(x + (g,))
        else:
            묶음.append([x + (g,)])
    return 묶음


def _갈리는자리(rs, 시작=보이는자리 + 1, 끝=8):
    for 자 in range(시작, 끝 + 1):
        if len({퍼글(r, 자, 부호=True) for r in rs}) == len(rs):
            return 자
    return None


def _자리말(자):
    return {2: "둘째", 3: "셋째", 4: "넷째", 5: "다섯째", 6: "여섯째"}.get(자, "%d번째" % 자)


def 주가카드(문, 회차, 원천, 장부, 메타, T, F, 문턱, 순위수, 시작=None):
    """(가) 경로 · (나) 구간마다 하루 등락 순위 · (다) 평가기준일 · 재무기준일 종가 · (라) 평가기준일 뒤."""
    p = os.path.join(회차, 주가파일)
    if not os.path.isfile(p):
        문["못지음"].append({"무엇": "주가 카드 전부(k01 · k02 · k03 · k1xx)", "까닭": "회차 폴더에 %s 가 없음" % 주가파일})
        return []
    출처, 전부 = 주가읽기(p)
    단위 = ("%s" % (메타.get("주당단위") or "")).strip() or 통화말.get(메타["_통화"], 메타["_통화"])
    if 단위.upper() in 통화말:
        단위 = 통화말[단위.upper()]
    해 = T.year
    시 = 날(시작) if 시작 else None
    구간 = [r for r in 전부 if r.d <= T and (시 is None or r.d >= 시)]
    뒤 = [r for r in 전부 if r.d > T]
    if len(구간) < 2:
        문["못지음"].append({"무엇": "주가 경로 · 순위", "까닭": "조회 구간(평가기준일까지)의 종가가 둘 미만"})
        return []
    전체 = (구간[0].날 == 전부[0].날 and not 뒤)
    출처글 = " · ".join(출처)
    출처원 = [원천.원(주가파일, 출처[0])] if 출처 else []
    카드들, 순위카드 = [], []
    문턱글 = 퍼글(문턱, 0)

    def 가(r, 이름):
        """종가 한 점 → (값, 계산, 원천)."""
        글, 나눗, 자 = 주가3(r.v, 단위)
        장, 장값 = 장부.종가(r.날, r.v, 글)
        return (_값(글, 주가본(r.v, 단위), 장, "금액", 날=r.날, 무엇=이름, 장부값같음=장값),
                _계("%s 종가(%s)" % (이름, r.날), 나눔식(r.글, 나눗), 글, 자),
                원천.원(주가파일, r.줄))

    # ── (가) 경로 ───────────────────────────────────────────────────
    꺾 = 꺾임찾기(구간, 문턱)
    최고 = max(구간, key=lambda r: (r.v, -r.d.toordinal()))
    최저 = min(구간, key=lambda r: (r.v, r.d.toordinal()))
    최고들 = [r for r in 구간 if r.v == 최고.v]
    최저들 = [r for r in 구간 if r.v == 최저.v]
    연초 = next((r for r in 구간 if r.d.year == 해), None)
    재무들 = [r for r in 구간 if r.d <= F]
    재무 = 재무들[-1] if 재무들 else None
    끝 = 구간[-1]
    값, 계, 원, 날짜, 함정, 문장 = [], [], list(출처원), [], [], []
    기준점 = [("구간 첫날", 구간[0])]
    if 연초 and 연초 is not 구간[0]:
        기준점.append(("%d년 첫 거래일" % 해, 연초))
    if 재무 and 재무 is not 끝 and 재무 is not 구간[0]:
        기준점.append(("재무기준일" if 재무.d == F else "재무기준일 앞 마지막 거래일", 재무))
    기준점.append(("평가기준일" if 끝.d == T else "평가기준일 앞 마지막 거래일", 끝))
    for 이름, r in 기준점 + [("구간 최고", 최고), ("구간 최저", 최저)] + [("꺾임 %s점" % x["종류"], 구간[x["i"]]) for x in 꺾]:
        a, b, c = 가(r, 이름)
        값.append(a)
        계.append(b)
        원.append(c)
        날짜 += 날들(r.d, 해)
    계.append(_계("구간 최고", _csv식("csv_max", 주가파일, 구간[0].날, 끝.날, 전체) + " == " + 최고.글, "참"))
    계.append(_계("구간 최저", _csv식("csv_min", 주가파일, 구간[0].날, 끝.날, 전체) + " == " + 최저.글, "참"))
    for k, x in enumerate(꺾):
        앞날 = 구간[꺾[k - 1]["i"]].날 if k else 구간[0].날
        뒷날 = 구간[꺾[k + 1]["i"]].날 if k + 1 < len(꺾) else 끝.날
        r = 구간[x["i"]]
        계.append(_계("꺾임 %s점 %s 이 %s~%s 사이의 %s" % (x["종류"], r.날, 앞날, 뒷날, "최고" if x["종류"] == "고" else "최저"),
                     _csv식("csv_max" if x["종류"] == "고" else "csv_min", 주가파일, 앞날, 뒷날, False) + " == " + r.글, "참"))
    다리 = []
    for k in range(1, len(꺾)):
        a, b = 구간[꺾[k - 1]["i"]], 구간[꺾[k]["i"]]
        vs, kc = _변화값(a.v, b.v, a.글, b.글, "%s → %s" % (a.날, b.날))
        값 += vs
        계.append(kc)
        일 = (b.d - a.d).days
        값.append(_값("%d일" % 일, 단위="일수"))
        계.append(_계("%s → %s 일수" % (a.날, b.날),
                     "(date(%d,%d,%d) - date(%d,%d,%d)).days" % (b.d.year, b.d.month, b.d.day, a.d.year, a.d.month, a.d.day), "%d일" % 일))
        다리.append((vs[0]["글"], 일))
    문장.append("종가 기준으로 %s부터 %s까지 주가는 %s %s 가장 높았고 %s %s 가장 낮았다." % (
        긴날(구간[0].d), 긴날(끝.d), 말날(최고.d, 해), 조(주가본(최고.v, 단위), "으로", "로"), 말날(최저.d, 해), 조(주가본(최저.v, 단위), "으로", "로")))
    if len(최고들) > 1:
        문장.append("가장 높은 종가는 %s에도 같았다." % " · ".join(말날(r.d, 해) for r in 최고들[1:]))
    if len(최저들) > 1:
        문장.append("가장 낮은 종가는 %s에도 같았다." % " · ".join(말날(r.d, 해) for r in 최저들[1:]))
    if 꺾:
        조각 = []
        for k, x in enumerate(꺾):
            r = 구간[x["i"]]
            덧 = ["%s · %d일" % 다리[k - 1]] if k else []
            if not x["확정"]:
                덧.append("구간 끝의 %s점이라 꺾임 미확정" % x["종류"])
            조각.append("%s %s점 %s%s" % (말날(r.d, 해), x["종류"], 주가본(r.v, 단위), ("(%s)" % " · ".join(덧)) if 덧 else ""))
        문장.append("직전 극값에서 %s 넘게 되돌린 꺾임은 %s이다 — %s." % (문턱글, _몇(len(꺾), "번"), ", ".join(조각)))
        r0 = 구간[꺾[-1]["i"]]
        if r0 is not 끝:
            vs, kc = _변화값(r0.v, 끝.v, r0.글, 끝.글, "%s → %s(마지막 꺾임 뒤)" % (r0.날, 끝.날))
            값 += vs
            계.append(kc)
            문장.append("마지막 꺾임 뒤 %s 종가는 %s %s(문턱 아래)." % (말날(끝.d, 해), 조(주가본(끝.v, 단위), "으로", "로"), 움직임(r0.v, 끝.v)))
    else:
        문장.append("직전 극값에서 %s 넘게 되돌린 꺾임은 없다." % 문턱글)
    if 연초 and 연초 is not 구간[0] and 최고.d > 연초.d:
        vs, kc = _변화값(연초.v, 최고.v, 연초.글, 최고.글, "%d년 첫 거래일 → 구간 최고" % 해)
        값 += vs
        계.append(kc)
        문장.append("%d년 첫 거래일(%s) 종가 %s에서 최고까지 %s." % (해, 말날(연초.d, 해), 주가본(연초.v, 단위), 움직임(연초.v, 최고.v)))
    if 최고.d < 끝.d:
        vs, kc = _변화값(최고.v, 끝.v, 최고.글, 끝.글, "구간 최고 → 평가기준일")
        값 += vs
        계.append(kc)
        문장.append("평가기준일(%s) 종가 %s 최고보다 %s." % (말날(끝.d, 해), 조(주가본(끝.v, 단위), "은", "는"), 견줌(최고.v, 끝.v)))
    고뒤 = [x for x in 꺾 if 구간[x["i"]].d > 최고.d]
    고뒤저 = [x for x in 고뒤 if x["종류"] == "저"]
    되오름 = [x for x in 고뒤 if x["종류"] == "고"]
    if 되오름:
        문장.append("최고 뒤 하락은 %s이었고, 그 사이 %s까지 되올랐다." % (
            _몇(len(고뒤저), "번"), " · ".join("%s %s" % (말날(구간[x["i"]].d, 해), 주가본(구간[x["i"]].v, 단위)) for x in 되오름)))
    필수 = [_필("범위", "종가|주가", "장 마감 가격의 경로다")]
    if len(꺾) >= 3 or 되오름:
        필수.append(_필("경로", "되올|반등|다시|두 번|세 번|네 번|여러 번|오르내", "고점 · 저점 · 되오름을 함께 — 한 번의 움직임처럼 쓰지 않는다"))
    if 꺾 and not 꺾[-1]["확정"]:
        함정.append("%s %s점은 구간 끝의 극값이다 — 그 뒤 문턱(%s)만큼 되돌리지 않아 꺾임이 확정되지 않았다. 「바닥」 · 「꼭대기」로 단정하지 않는다"
                  % (긴날(구간[꺾[-1]["i"]].d), 꺾[-1]["종류"], 문턱글))
    if 끝.d != T and (T - 끝.d).days > 7:
        함정.append("시세 파일이 평가기준일 %d일 앞(%s)에서 끝난다" % ((T - 끝.d).days, 끝.날))
    if re.search(r"수정|조정", 출처글):
        함정.append("시세 파일의 종가는 원자료가 밝힌 대로 조정된 가격이다(%s) — 그날 실제로 거래된 가격과 다를 수 있다" % 출처글)
    카드들.append({"id": "k01", "주장": " ".join(문장), "등급": "계산",
                "값": _겹없이(값, lambda v: (v["글"], v.get("장부"))), "날짜": _겹없이(날짜, str),
                "기간": "%s~%s" % (긴날(구간[0].d), 긴날(끝.d)), "계산": _겹없이(계), "필수": 필수,
                "권장": [_필("기간", "%d년|%s" % (구간[0].d.year, re.escape(말날(구간[0].d, 해))), "조회 구간의 시작을 함께 — 「사상 최고」로 읽히지 않게")],
                "원천": _겹없이(원), "함정": 함정,
                "_경로": {"파일": 주가파일, "출처": 출처글, "구간": [구간[0].날, 끝.날], "문턱": float(문턱),
                         "꺾임": [{"날": 구간[x["i"]].날, "종가": 구간[x["i"]].글, "종류": x["종류"], "확정": x["확정"]} for x in 꺾],
                         "최고": [r.날 for r in 최고들], "최저": [r.날 for r in 최저들]}})

    # ── (나) 꺾임 사이 구간마다 하루 등락 순위 ───────────────────────────
    점들 = [x["i"] for x in 꺾]
    if len(점들) >= 2:
        창들 = [(점들[k - 1], 점들[k], "하락" if 구간[점들[k]].v < 구간[점들[k - 1]].v else "상승") for k in range(1, len(점들))]
    else:
        창들 = [(0, len(구간) - 1, "하락"), (0, len(구간) - 1, "상승")]
    차 = {"하락": 0, "상승": 0}
    고뒤차 = {"하락": 0, "상승": 0}
    for a, b, 방향 in 창들:
        A, B = 구간[a], 구간[b]
        등락 = 하루등락(구간, a, b)
        묶음 = 순위고르기(등락, 방향, 순위수)
        차[방향] += 1
        if len(점들) < 2:
            이름 = "조회 구간 전체의 %s" % 방향
        elif A.d >= 최고.d:
            고뒤차[방향] += 1
            이름 = "최고 뒤 %s %s" % (_차례[min(고뒤차[방향], 10)], "하락" if 방향 == "하락" else "되오름")
        else:
            이름 = "%s %s" % (_차례[min(차[방향], 10)], 방향)
        if not 묶음:
            문["못지음"].append({"무엇": "%s(%s~%s)의 하루 등락 순위" % (이름, A.날, B.날), "까닭": "그 방향으로 움직인 날이 없음"})
            continue
        동사 = "내린" if 방향 == "하락" else "오른"
        조각, 값, 계, 원, 날짜, 함정, 동률묶음 = [], [], [], [], [], [], []
        자리순 = 1
        for g in 묶음:
            말 = " · ".join("%s(%s)" % (말날(x[0].d, 해), x[3]) for x in g)
            조각.append("%s 크게 %s 날은 %s" % (_서수[자리순] if 자리순 <= 10 else "%d번째로" % 자리순, 동사, 말))
            if len(g) > 1:
                동률묶음.append(g)
            for x in g:
                값.append(_값(x[3], 퍼글(x[2], 2, 부호=True), 단위="비율", 날=x[0].날))
                값.append(_값(퍼글(abs(x[2]), 보이는자리), 단위="비율", 날=x[0].날, 꼴=_크기꼴))
                계.append(_계("%s 하루 등락" % x[0].날, "%s / %s - 1" % (x[0].글, x[1].글), x[3], 보이는자리))
                원 += [원천.원(주가파일, x[0].줄), 원천.원(주가파일, x[1].줄)]
                날짜 += 날들(x[0].d, 해)
            자리순 += len(g)
        맨 = 묶음[0][0]
        계.append(_계("%s 이 창에서 가장 크게 %s 날" % (맨[0].날, 동사),
                     "%s([%s]) == %s / %s" % ("min" if 방향 == "하락" else "max", ", ".join("%s / %s" % (y[0].글, y[1].글) for y in 등락), 맨[0].글, 맨[1].글),
                     "참"))
        변 = (", " + 변화글(A.v, B.v)) if len(점들) >= 2 else ""
        주장 = "%s(%s %s → %s %s%s)에서 하루 등락(종가 기준 · 앞 거래일 대비)이 %s." % (
            이름, 말날(A.d, 해), 주가본(A.v, 단위), 말날(B.d, 해), 주가본(B.v, 단위), 변, 조(", ".join(조각), "이다", "다"))
        for g in 동률묶음:
            자 = _갈리는자리([x[2] for x in g])
            풀이 = ("소수 %s 자리까지는 %s" % (_자리말(자), " · ".join("%s %s" % (말날(x[0].d, 해), 퍼글(x[2], 자, 부호=True)) for x in g))) if 자 \
                else "종가 비가 정확히 같다"
            날말들 = " · ".join(말날(x[0].d, 해) for x in g)
            주장 += " %s 보이는 자릿수(소수 첫째 자리)에서 %s 같다(%s)." % (조(날말들, "은", "는"), 조(g[0][3], "으로", "로"), 풀이)
            함정.append("%s 소수 첫째 자리에서 %s 같다 — 한 날만 꼽아 순서를 세우지 않는다(%s)" % (조(날말들, "은", "는"), 조(g[0][3], "으로", "로"), 풀이))
        실은 = [x for g in 묶음 for x in g]
        정수같음 = [x for x in 실은[1:] if 퍼글(x[2], 0, 부호=True) == 퍼글(실은[0][2], 0, 부호=True) and x[3] != 실은[0][3]]
        if 정수같음:
            함정.append("정수 자리로 적으면 %s %s 모두 %s 같아진다 — 순위를 말할 때는 소수 첫째 자리로 적는다(이 카드의 값에 정수 자리 글은 없다)" % (
                말날(실은[0][0].d, 해), 조(" · ".join(말날(x[0].d, 해) for x in 정수같음), "이", "가"), 조(퍼글(실은[0][2], 0, 부호=True), "으로", "로")))
        필수 = [_필("범위", "하루|일일|하룻", "하루 등락이다 — 구간 전체의 등락률로 읽히지 않게")]
        권장 = [_필("기간", "%s|%s" % (re.escape(말날(A.d, 해)), re.escape(말날(B.d, 해))), "어느 구간의 순위인지")]
        if len(묶음[0]) > 1:
            필수.append(_필("양상", "같|나란|동률|공동", "가장 큰 날이 보이는 자릿수에서 둘 이상이다 — 하나만 꼽지 않는다"))
        elif 동률묶음:
            권장.append(_필("양상", "같|나란|동률|공동", "순위 안에 보이는 자릿수의 동률이 있다 — 둘째 아래를 하나로 꼽을 때"))
        날짜 += 날들(A.d, 해) + 날들(B.d, 해)
        순위카드.append({"id": "k1%02d" % (len(순위카드) + 1), "주장": 주장, "등급": "계산",
                     "값": _겹없이(값, lambda v: (v["글"], v.get("_날"))), "날짜": _겹없이(날짜, str),
                     "기간": "%s~%s" % (긴날(A.d), 긴날(B.d)), "계산": 계, "필수": 필수, "권장": 권장, "원천": _겹없이(원), "함정": 함정,
                     "_창": {"파일": 주가파일, "시작": A.날, "끝": B.날, "방향": 방향, "날수": len(등락), "이름": 이름,
                            "기준": "종가 · 앞 거래일 대비 · 시작 날 다음 거래일부터 끝 날까지", "순위수": 순위수,
                            "보이는자리": 보이는자리, "반올림": "ROUND_HALF_UP(정확한 비에서 한 번)"}})
    카드들 += 순위카드

    # ── (다) 평가기준일 · 재무기준일 종가 ─────────────────────────────
    값, 계, 원, 날짜, 함정 = [], [], [], [], []
    a, b, c = 가(끝, "평가기준일")
    값.append(a)
    계.append(b)
    원.append(c)
    날짜 += 날들(끝.d, 해) + 날들(T, 해)
    if 끝.d == T:
        주장 = "평가기준일 %s 종가는 %s." % (긴날(T), 조(주가본(끝.v, 단위), "이다", "다"))
    else:
        주장 = "평가기준일 %s에는 종가가 없어 앞 마지막 거래일 %s 종가 %s 쓴다." % (긴날(T), 긴날(끝.d), 조(주가본(끝.v, 단위), "을", "를"))
        함정.append("평가기준일(%s)에 종가가 없다 — 앞 마지막 거래일 %s 의 종가다" % (T.isoformat(), 끝.날))
    기간말 = ["평가기준일", re.escape(말날(T, 해))]
    if F != T:
        fr = [r for r in 전부 if r.d <= F]
        if fr:
            fr = fr[-1]
            a, b, c = 가(fr, "재무기준일")
            값.append(a)
            계.append(b)
            원.append(c)
            날짜 += 날들(fr.d, 해) + 날들(F, 해)
            vs, kc = _변화값(fr.v, 끝.v, fr.글, 끝.글, "재무기준일 → 평가기준일")
            값 += vs
            계.append(kc)
            주장 += " 재무기준일 %s 종가는 %s, 재무기준일에서 평가기준일까지 %s." % (
                긴날(F) if fr.d == F else "%s(앞 마지막 거래일 %s)" % (긴날(F), 긴날(fr.d)), 조(주가본(fr.v, 단위), "이고", "고"), 움직임(fr.v, 끝.v))
            기간말 += ["재무기준일", re.escape(말날(F, 해))]
        else:
            문["못지음"].append({"무엇": "재무기준일 종가(k02)", "까닭": "시세 파일이 재무기준일(%s)보다 늦게 시작" % F.isoformat()})
    else:
        주장 += " 재무기준일도 같은 날이다."
    카드들.append({"id": "k02", "주장": 주장, "등급": "계산", "값": _겹없이(값, lambda v: (v["글"], v.get("장부"))), "날짜": _겹없이(날짜, str),
                "계산": 계, "필수": [_필("범위", "종가|주가", "장 마감 가격이다"), _필("기간", "|".join(기간말), "어느 날의 종가인지")],
                "원천": _겹없이(원), "함정": 함정})

    # ── (라) 평가기준일 뒤 ───────────────────────────────────────────
    if 뒤:
        L = 뒤[-1]
        hi_ = max(뒤, key=lambda r: (r.v, -r.d.toordinal()))
        lo_ = min(뒤, key=lambda r: (r.v, r.d.toordinal()))
        값, 계, 원, 날짜 = [], [], [], []
        for 이름, r in (("평가기준일 뒤 마지막 날", L), ("평가기준일 뒤 최고", hi_), ("평가기준일 뒤 최저", lo_), ("평가기준일", 끝)):
            a, b, c = 가(r, 이름)
            값.append(a)
            계.append(b)
            원.append(c)
            날짜 += 날들(r.d, 해)
        vs, kc = _변화값(끝.v, L.v, 끝.글, L.글, "평가기준일 → 평가기준일 뒤 마지막 날")
        값 += vs
        계.append(kc)
        계.append(_계("평가기준일 뒤 최고", _csv식("csv_max", 주가파일, 뒤[0].날, L.날, False) + " == " + hi_.글, "참"))
        계.append(_계("평가기준일 뒤 최저", _csv식("csv_min", 주가파일, 뒤[0].날, L.날, False) + " == " + lo_.글, "참"))
        카드들.append({"id": "k03", "등급": "계산", "사건일": L.날,
                    "주장": "평가기준일(%s) 뒤 시세 파일의 마지막 날 %s 종가는 %s 평가기준일 종가 %s보다 %s. 그사이(%s~%s · %d거래일) 종가 최고는 %s %s, 최저는 %s %s." % (
                        긴날(T), 긴날(L.d), 조(주가본(L.v, 단위), "으로", "로"), 주가본(끝.v, 단위), 견줌(끝.v, L.v), 말날(뒤[0].d, 해), 말날(L.d, 해), len(뒤),
                        말날(hi_.d, 해), 주가본(hi_.v, 단위), 말날(lo_.d, 해), 조(주가본(lo_.v, 단위), "이다", "다")),
                    "값": _겹없이(값, lambda v: (v["글"], v.get("장부"))), "날짜": _겹없이(날짜, str), "기간": "%s~%s" % (긴날(뒤[0].d), 긴날(L.d)),
                    "계산": 계, "필수": [_필("기간", "평가기준일 뒤|기준일 뒤|이후|뒤에|지난 뒤", "평가기준일 뒤의 일이다 — 평가에 쓴 정보로 읽히지 않게"),
                                      _필("범위", "종가|주가", "장 마감 가격이다")],
                    "원천": _겹없이(원 + 출처원), "함정": ["평가기준일 뒤의 시세다 — 이 평가의 값에 들어간 정보가 아니다"]})
    return 카드들


# ══════════════════════════════════════════════════════ 5. 실적 시계열

def _항(v, 수, 배, 원, 장부=None, 장부값=None):
    """금액 한 칸 — v 는 통화 단위의 절대 금액(분수), 수 · 배 는 원자료의 글과 그 단위."""
    return {"v": 분(v), "수": 수, "배": 분(배), "원천": 원, "장부": 장부, "장부값": 장부값}


def _절대식(h):
    return h["수"] if h["배"] == 1 else "%s * %d" % (h["수"], h["배"])


def _비식(분자, 분모):
    """두 항의 비 — 같은 단위면 원자료 글끼리, 다르면 통화 단위로 맞춘다."""
    if 분자["배"] == 분모["배"]:
        return "%s / %s" % (분자["수"], 분모["수"])
    return "(%s) / (%s)" % (_절대식(분자), _절대식(분모))


def _차항(a, b):
    """a − b(같은 보고서의 누계 − 분기 따위)."""
    if a["배"] == b["배"]:
        return _항(a["v"] - b["v"], "(%s - %s)" % (a["수"], b["수"]), a["배"], a["원천"] + b["원천"])
    return _항(a["v"] - b["v"], "(%s - %s)" % (_절대식(a), _절대식(b)), 1, a["원천"] + b["원천"])


def _같음(a, b, 배):
    """금액 둘이 같은가 — 모델 금액 단위 하나(반올림) 또는 백만분의 일 안."""
    a, b = 분(a), 분(b)
    return abs(a - b) <= max(분(배), abs(b) * Fraction(1, 10 ** 6))


def 누계이름(해, m, 결산월):
    if 결산월 == 12:
        return {3: "%d년 1분기", 6: "%d년 상반기", 9: "%d년 1~3분기 누계"}.get(m, "%%d년 %s개월 누계" % m) % 해
    return "FY%d 첫 %s개월 누계" % (해, m)


def 열이름(c, 결산월):
    if c.종류 == 축모듈.FY실적:
        return "%d년" % c.회계연도 if 결산월 == 12 else "FY%d(%s~%s)" % (c.회계연도, c.시작일.isoformat(), c.종료일.isoformat())
    m = int(c.개월) if float(c.개월) == int(c.개월) else c.개월
    return 누계이름(c.회계연도, m, 결산월)


def 누계기간말(m):
    return {3: "1분기|분기", 6: "상반기|반기|누계", 9: "1~3분기|누계|9월까지"}.get(m, "누계|개월")


def 모델실적(가정, 가정파일, 축, 배, 통화, 장부, 원천):
    """13번 원천 62 · 66 의 실적 열 → [기간값 …]."""
    원 = 가정.get("원천") or {}
    밖 = []
    for c in 축.열:
        if c.구분 != "실적":
            continue
        m = (원.get(매출줄) or {}).get(c.ID)
        o = (원.get(영업줄) or {}).get(c.ID)
        if m is None and o is None:
            continue

        def 항(raw, 줄, c=c):
            if raw is None:
                return None
            v = 분(raw) * 배
            글 = 금액3(v, 통화)[0]
            k, kv = 장부.실적(c.ID, 분(raw), 글)
            return _항(v, 수글(raw), 배, [원천.원(가정파일, '"%s": %s' % (c.ID, json.dumps(raw)), 자리="원천.%s.%s" % (줄, c.ID))], k, kv)

        밖.append({"열": c.ID, "이름": 열이름(c, 축.결산월), "개월": c.개월, "끝": c.종료일, "해": c.회계연도,
                   "종류": "연간" if c.종류 == 축모듈.FY실적 else "누계", "매출": 항(m, 매출줄), "영업": 항(o, 영업줄), "출처": "모델"})
    return 밖


def _칸바꿔(items, 칸):
    return [dict(it, thstrm_amount=it.get(칸)) for it in items or []]


def _칸글(items, 칸, 이름):
    """손익 항목에서 계정 이름(원래 꼴)의 칸 글."""
    for it in items or []:
        if (it.get("sj_div") or "").strip() in ("IS", "CIS") and (it.get("account_nm") or "").strip() == 이름:
            s = (it.get(칸) or "").replace(",", "").strip()
            return s if s and s not in ("-", "--") else None
    return None


def _국내한칸(items, 칸, 파일, 원천, 자리머리):
    it2 = _칸바꿔(items, 칸)
    _mv, 나m, 금 = 앵.매출한해(it2)
    _ov, 나o = 앵.영업한해(it2)
    m글 = _칸글(items, 칸, 나m) if 나m else None
    o글 = _칸글(items, 칸, 나o) if 나o else None
    return ({"매출": _항(분(m글), m글, 1, [원천.원(파일, m글, 자리="%s · %s" % (자리머리, 나m))]) if m글 else None,
             "영업": _항(분(o글), o글, 1, [원천.원(파일, o글, 자리="%s · %s" % (자리머리, 나o))]) if o글 else None},
            나m, 금)


def 국내앵커(회차, 원천):
    파일 = "_raw/dart_앵커시계열.json"
    p = os.path.join(회차, 파일)
    if not os.path.isfile(p):
        return None
    d = json.load(io.open(p, encoding="utf-8"))
    해 = {}
    for h in d.get("해", []) or []:
        try:
            Y = int(h.get("사업연도"))
        except (TypeError, ValueError):
            continue
        items = h.get("list") or []
        접수 = items[0].get("rcept_no") if items else None
        for 덜, 칸 in ((0, "thstrm_amount"), (1, "frmtrm_amount"), (2, "bfefrmtrm_amount")):
            y = Y - 덜
            if y in 해 and 해[y]["_덜"] <= 덜:
                continue
            한, 나m, 금 = _국내한칸(items, 칸, 파일, 원천, "사업보고서(접수 %s) %s" % (접수, {0: "당기", 1: "전기", 2: "전전기"}[덜]))
            if not 한["매출"]:
                continue
            해[y] = {"열": "A%d" % y, "해": y, "개월": 12, "종류": "연간", "매출": 한["매출"], "영업": 한["영업"], "_덜": 덜,
                     "출처": "앵커", "계정": 나m, "금융업": 금}
    return {"파일": 파일, "해": 해, "말": "DART 사업보고서 손익", "연결": True}


def 미국앵커(회차, 원천):
    파일 = "_raw/앵커_시계열.json"
    p = os.path.join(회차, 파일)
    if not os.path.isfile(p):
        return None
    d = json.load(io.open(p, encoding="utf-8"))
    해 = {}
    for r in d.get("표", []) or []:
        mm = re.search(r"(\d{4})", str(r.get("사업연도") or ""))
        if not mm or not r.get("매출"):
            continue
        y = int(mm.group(1))
        m, o = r.get("매출"), r.get("영업이익")
        mo = _항(분(m), 수글(m), 1, [원천.원(파일, 수글(m), 자리="표[%s].매출" % r.get("사업연도"))])
        oo = _항(분(o), 수글(o), 1, [원천.원(파일, 수글(o), 자리="표[%s].영업이익" % r.get("사업연도"))]) if o is not None else None
        해[y] = {"열": "A%d" % y, "해": y, "개월": 12, "종류": "연간", "매출": mo, "영업": oo, "출처": "앵커", "끝": r.get("종료일"), "계정": None}
    이음 = [x for x in (d.get("태그_이음") or []) if isinstance(x, str) and re.match(r"^매출\s*—", x)]
    return {"파일": 파일, "해": 해, "말": "SEC companyfacts 앵커 시계열", "연결": False,
            "함정": ["앵커 시계열의 매출 태그를 해마다 이어 붙였다 — %s" % x for x in 이음],
            "원천": [원천.원(파일, x, 자리="태그_이음") for x in 이음]}


def 국내분기(회차, 누열, 모델누, 원천):
    """재무기준일 정기보고서의 3개월 · 누계 · 전년 같은 기간. 보고서 누계가 모델(원천 62 · 66)과 같을 때만 같은 기준으로 쓴다."""
    m = int(누열.개월) if float(누열.개월) == int(누열.개월) else None
    코드 = {3: "11013", 6: "11012", 9: "11014"}.get(m)
    if not 코드:
        return None, "누계 열이 3 · 6 · 9개월이 아님"
    후보 = sorted(glob.glob(os.path.join(회차, "_raw", "dart_재무_연결_*_%s.json" % 코드)))
    if not 후보:
        return None, "재무기준일 정기보고서 재무(_raw/dart_재무_연결_*_%s.json)가 회차에 없음" % 코드
    까닭 = "정기보고서의 누계 매출이 모델 매출(원천 62 · %s)과 다름" % 누열.ID
    for p in 후보:
        try:
            items = json.load(io.open(p, encoding="utf-8")).get("list") or []
        except ValueError:
            continue
        파일 = os.path.relpath(p, 회차).replace("\\", "/")
        접수 = items[0].get("rcept_no") if items else None
        밖 = {}
        for 이름, 칸 in (("누계", "thstrm_add_amount"), ("분기", "thstrm_amount"), ("전년분기", "frmtrm_q_amount"), ("전년누계", "frmtrm_add_amount")):
            밖[이름], _n, _g = _국내한칸(items, 칸, 파일, 원천, "정기보고서(접수 %s) %s" % (접수, 칸))
        if m == 3:
            for a, b in (("누계", "분기"), ("전년누계", "전년분기")):
                for 항목 in ("매출", "영업"):
                    밖[a][항목] = 밖[a][항목] or 밖[b][항목]
        누 = 밖["누계"]
        if not (누["매출"] and 모델누.get("매출") and _같음(누["매출"]["v"], 모델누["매출"]["v"], 모델누["매출"]["배"])):
            continue
        밖["_까닭"] = []
        if 누["영업"] and 모델누.get("영업") and not _같음(누["영업"]["v"], 모델누["영업"]["v"], 모델누["영업"]["배"]):
            for 이름 in ("누계", "분기", "전년분기", "전년누계"):
                밖[이름]["영업"] = None
            밖["_까닭"].append("영업이익 — 정기보고서 누계가 모델(원천 66)과 다름")
        밖["_파일"] = 파일
        return 밖, None
    return None, 까닭


def 미국분기(회차, 누열, 모델누, 원천, 통화):
    """companyfacts 의 10-Q 분기 · 누계 · 전년 같은 기간 — 누계가 모델(원천 62 · 66)과 같은 태그만 쓴다(항목마다)."""
    파일 = "_raw/companyfacts.json"
    p = os.path.join(회차, 파일)
    if not os.path.isfile(p):
        return None, "%s 이 회차에 없음" % 파일
    try:
        import sec_앵커                                   # noqa: PLC0415
        태그 = sec_앵커.TAGS["us-gaap"]
    except Exception:                                 # noqa: BLE001
        태그 = {"매출": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"], "영업이익": ["OperatingIncomeLoss"]}
    g = (json.load(io.open(p, encoding="utf-8")).get("facts") or {}).get("us-gaap") or {}
    F, 시 = 누열.종료일, 누열.시작일
    F1, 시1 = _해앞(F), _해앞(시)

    def 찾(tag, 끝, 처음=None, 석달=False):
        맞 = []
        for r in ((g.get(tag) or {}).get("units") or {}).get(통화) or []:
            try:
                e = _dt.date.fromisoformat(r["end"])
                s = _dt.date.fromisoformat(r.get("start") or r["end"])
            except (KeyError, ValueError):
                continue
            if abs((e - 끝).days) > 7 or (석달 and not 80 <= (e - s).days <= 100) or (처음 and abs((s - 처음).days) > 7):
                continue
            맞.append(r)
        맞.sort(key=lambda r: r.get("filed") or "")
        return 맞[-1] if 맞 else None

    밖 = {"누계": {}, "분기": {}, "전년분기": {}, "전년누계": {}, "_까닭": [], "_파일": 파일}
    for 항목, 키, 줄 in (("매출", "매출", 매출줄), ("영업", "영업이익", 영업줄)):
        쓴 = None
        for tag in 태그.get(키, []):
            누 = 찾(tag, F, 처음=시)
            if not 누:
                continue
            if not (모델누.get(항목) and _같음(분(누["val"]), 모델누[항목]["v"], 모델누[항목]["배"])):
                밖["_까닭"].append("%s — 10-Q 누계(%s %s)가 모델(원천 %s · %s)과 다름" % (
                    "매출" if 항목 == "매출" else "영업이익", tag, 누["val"], 줄, 금액본(모델누[항목]["v"], 통화) if 모델누.get(항목) else "없음"))
                continue
            쓴 = tag
            break
        if not 쓴:
            continue
        for 이름, (끝, 처음, 석) in (("누계", (F, 시, False)), ("분기", (F, None, True)), ("전년분기", (F1, None, True)), ("전년누계", (F1, 시1, False))):
            r = 찾(쓴, 끝, 처음=처음, 석달=석)
            if r:
                밖[이름][항목] = _항(분(r["val"]), 수글(r["val"]), 1,
                                 [원천.원(파일, 수글(r["val"]), 자리="us-gaap/%s %s~%s(%s · 제출 %s)" % (쓴, r.get("start"), r["end"], r.get("form"), r.get("filed")))])
    if not 밖["분기"]:
        return None, "; ".join(밖["_까닭"]) or "companyfacts 에 재무기준일 분기 값이 없음"
    return 밖, None


def _기간카드(cid, 기간들, 주장머리, 통화, 필수, 권장, 기간글, 덧계=None, 덧값=None, 덧주장=""):
    """기간값 목록 → 매출 · 영업이익 · 영업이익률 카드."""
    값, 계, 원, 조각 = [], [], [], []
    for p in 기간들:
        글들 = []
        for 항목, 말 in (("매출", "매출"), ("영업", "영업이익")):
            h = p.get(항목)
            if not h:
                continue
            글, u, 자 = 금액3(h["v"], 통화)
            값.append(_값(글, 금액본(h["v"], 통화), h.get("장부"), "금액", 기간=p["이름"], 무엇=말, 장부값같음=h.get("장부값")))
            계.append(_계("%s %s" % (p["이름"], 말), 나눔식(h["수"], Fraction(u) / h["배"]), 글, 자))
            원 += h["원천"]
            글들.append("%s %s" % (말, 금액본(h["v"], 통화)))
        if p.get("매출") and p.get("영업") and p["매출"]["v"]:
            r = p["영업"]["v"] / p["매출"]["v"]
            글 = 퍼글(r, 1)
            값.append(_값(글, 퍼글(r, 2), None, "비율", 기간=p["이름"], 무엇="영업이익률"))
            계.append(_계("%s 영업이익률" % p["이름"], _비식(p["영업"], p["매출"]), 글, 1))
            if 퍼글(r, 0) != 글:                          # 공시 서술의 정수 자리(「76%」) — 같은 값의 다른 자릿수
                값.append(_값(퍼글(r, 0), None, None, "비율", 기간=p["이름"], 무엇="영업이익률", 꼴="정수 자리"))
                계.append(_계("%s 영업이익률(정수 자리)" % p["이름"], _비식(p["영업"], p["매출"]), 퍼글(r, 0), 0))
            글들.append("영업이익률 %s" % 글)
        if 글들:
            조각.append("%s %s" % (p["이름"], " · ".join(글들)))
    if not 조각:
        return None
    return {"id": cid, "주장": "%s %s.%s" % (주장머리, 조(", ".join(조각), "이다", "다"), 덧주장), "등급": "계산",
            "값": _겹없이(값 + (덧값 or []), lambda v: (v["글"], v.get("_기간"), v.get("_무엇"))), "기간": 기간글,
            "계산": 계 + (덧계 or []), "필수": 필수, "권장": 권장, "원천": _겹없이(원)}


def _증감(이름, 지금, 전, 통화):
    """지금 · 전 기간값 → (값, 계산, 글 조각). 부호가 바뀌면 증감률을 적지 않는다."""
    값, 계, 조각 = [], [], []
    for 항목, 말 in (("매출", "매출"), ("영업", "영업이익")):
        a, b = 지금.get(항목), 전.get(항목)
        if not (a and b) or b["v"] == 0:
            continue
        if b["v"] < 0 or a["v"] < 0:
            조각.append("%s %s에서 %s로(부호가 음수라 증감률을 적지 않음)" % (말, 금액본(b["v"], 통화), 금액본(a["v"], 통화)))
            continue
        r = a["v"] / b["v"]
        if r >= 2:
            글 = 배글(r, 1)
            값.append(_값(글, 배글(r, 2), 단위="배수", 무엇="%s %s" % (말, 이름)))
            계.append(_계("%s %s" % (말, 이름), _비식(a, b), 글, 1))
        else:
            글 = 퍼글(r - 1, 1, 부호=True)
            값.append(_값(글, 퍼글(r - 1, 2, 부호=True), 단위="비율", 무엇="%s %s" % (말, 이름)))
            if 퍼글(abs(r - 1), 1) != 글:
                값.append(_값(퍼글(abs(r - 1), 1), 단위="비율", 무엇="%s %s" % (말, 이름), 꼴=_크기꼴))
            계.append(_계("%s %s" % (말, 이름), _비식(a, b) + " - 1", 글, 1))
        조각.append("%s %s" % (말, 글))
    if all(지금.get(k) for k in ("매출", "영업")) and all(전.get(k) for k in ("매출", "영업")) and 지금["매출"]["v"] and 전["매출"]["v"]:
        d = 지금["영업"]["v"] / 지금["매출"]["v"] - 전["영업"]["v"] / 전["매출"]["v"]
        글 = 포글(d, 1)
        값.append(_값(글, 포글(d, 2), 단위="비율", 무엇="영업이익률 차 %s" % 이름))
        계.append(_계("영업이익률 차 %s" % 이름, "(%s - %s) * 100" % (_비식(지금["영업"], 지금["매출"]), _비식(전["영업"], 전["매출"])), 글, 1))
        조각.append("영업이익률 %s" % 글)
    return 값, 계, 조각


def 실적카드(문, 회차, 원천, 장부, 가정, 가정파일, 메타):
    """(마) 실적 시계열 — k21 · k22 · k23 · k24 (기준이 다른 앵커는 k21b · k24b)."""
    통화, 배 = 메타["_통화"], 메타["_배"]
    try:
        축 = 축모듈.기간축(가정)
    except Exception as e:                               # noqa: BLE001
        문["못지음"].append({"무엇": "실적 카드 전부(k21~k24)", "까닭": "기간 축을 세우지 못함 — %s" % e})
        return [], None
    모델 = 모델실적(가정, 가정파일, 축, 배, 통화, 장부, 원천)
    if not 모델:
        문["못지음"].append({"무엇": "실적 카드 전부(k21~k24)", "까닭": "13번 원천 62 · 66 에 실적 열 값이 없음"})
        return [], 축
    결산월 = 축.결산월
    연모델 = [p for p in 모델 if p["종류"] == "연간"]
    누 = next((p for p in 모델 if p["종류"] == "누계"), None)
    국내 = os.path.isfile(os.path.join(회차, "_raw", "dart_앵커시계열.json")) or (
        통화 == "KRW" and not os.path.isfile(os.path.join(회차, "_raw", "앵커_시계열.json")))
    앵커 = 국내앵커(회차, 원천) if 국내 else 미국앵커(회차, 원천)
    근 = [x for x in ((가정.get("원천근거") or {}).get(매출줄) or []) if isinstance(x, str) and x]
    연결 = bool(앵커 and 앵커.get("연결")) or any("연결" in x for x in 근)
    기준말 = "연결 · " if 연결 else ""
    카드들 = []

    # 앵커 기준 판정 — 겹치는 해가 모두 같으면 잇는다(매출 정의가 다르면 섞지 않는다)
    같은기준 = False
    if 앵커 and 앵커["해"]:
        겹 = []
        for p in 연모델:
            a = 앵커["해"].get(p["해"])
            if not a:
                continue
            ok = (_같음(a["매출"]["v"], p["매출"]["v"], 배) if (a.get("매출") and p.get("매출")) else True) and \
                 (_같음(a["영업"]["v"], p["영업"]["v"], 배) if (a.get("영업") and p.get("영업")) else True)
            겹.append((p, a, ok))
        같은기준 = bool(겹) and all(x[2] for x in 겹)
        if not 같은기준:
            틀린 = [x for x in 겹 if not x[2]]
            if 틀린:
                p, a, _ok = 틀린[0]
                문["함정_메모"].append("연간 앵커 시계열(%s)의 %d년 매출 %s 모델 매출(13번 원천 62 · %s) %s 다르다 — 매출의 정의가 다르니 한 문장에서 섞지 않는다"
                                    "(k21 · k22 · k23 은 모델 기준, k21b · k24b 는 앵커 기준)%s" % (
                                        앵커["파일"], a["해"], 조(금액본(a["매출"]["v"], 통화), "과", "와"), p["열"], 조(금액본(p["매출"]["v"], 통화), "이", "가"),
                                        (" · 모델 매출의 근거: %s" % " / ".join(근)) if 근 else ""))
            else:
                문["함정_메모"].append("연간 앵커 시계열(%s)과 모델 실적 열이 겹치는 해가 없어 기준이 같은지 확인하지 못했다 — 따로 짓는다(k21b · k24b)" % 앵커["파일"])
    elif not 앵커:
        문["못지음"].append({"무엇": "연간 실적의 긴 역사", "까닭": "앵커 시계열(_raw/dart_앵커시계열.json · _raw/앵커_시계열.json)이 회차에 없음 — 모델 실적 열만 지음"})

    def 앵커이름(y):
        return "%d년" % y if 결산월 == 12 else (("사업연도 %d" % y) if 국내 else "FY%d" % y)

    연간 = list(연모델)
    if 같은기준:
        있는해 = {p["해"] for p in 연모델}
        연간 += [dict(a, 이름=앵커이름(y)) for y, a in 앵커["해"].items() if y not in 있는해]
    연간.sort(key=lambda p: p["해"])
    앵연 = sorted([dict(a, 이름=앵커이름(y)) for y, a in 앵커["해"].items()], key=lambda p: p["해"]) if (앵커 and 앵커["해"] and not 같은기준) else []
    계정 = next((a.get("계정") for a in ((앵커 or {}).get("해") or {}).values() if a.get("계정")), None)
    계정말 = (" · 공시 계정 「%s」" % 계정) if 계정 and 계정 not in ("매출액", "매출") else ""
    권장율 = [_필("단위", "영업이익률|이익률|매출 대비", "비율이 무엇의 비율인지")]
    권장연결 = [_필("기준", "연결", "연결 기준")] if 연결 else []

    def 덧붙임(c, 목록):
        """앵커에서 온 해가 든 카드 — 비교 열(전기 · 전전기)에서 온 해 · 태그 이음을 함정과 원천에."""
        if not c:
            return c
        함 = list(c.get("함정") or [])
        비교 = [p for p in 목록 if p.get("_덜")]
        if 비교:
            함.append("%s 값은 그 뒤 해 사업보고서의 비교 열(전기 · 전전기)에서 왔다 — 재작성된 값일 수 있어 그 해 보고서에 처음 적힌 값과 다를 수 있다"
                     % " · ".join(p["이름"] for p in 비교))
        if any(p.get("출처") == "앵커" for p in 목록) and 앵커:
            함 += 앵커.get("함정") or []
            c["원천"] = _겹없이(c["원천"] + (앵커.get("원천") or []))
        if 함:
            c["함정"] = 함
        return c

    def 연간카드(cid, 목록, 머리):
        if not 목록:
            return None
        return 덧붙임(_기간카드(cid, 목록, 머리, 통화, [_필("기간", r"\d{4}년|연간|한 해|FY", "연간 값이다 — 반기 · 분기 값과 섞지 않는다")],
                             권장율 + 권장연결, "%s~%s" % (목록[0]["이름"], 목록[-1]["이름"])), 목록)

    if 같은기준:
        머리 = "매출(%s%s — 모델 실적 열과 겹치는 해가 같음%s)과 영업이익의 연간 실적은" % (기준말, 앵커["말"], 계정말)
    else:
        머리 = "매출(%s모델 기준 · 13번 원천 62%s)과 영업이익의 연간 실적은" % (기준말, 계정말)
    c = 연간카드("k21", 연간, 머리)
    if c:
        카드들.append(c)
    if 앵연:
        c = 연간카드("k21b", 앵연, "매출(%s — 모델 매출과 정의가 다름)과 영업이익의 연간 실적은" % 앵커["말"])
        if c:
            c["함정"] = ["이 시계열의 매출은 모델 매출(13번 원천 62)과 정의가 다르다 — k21 · k22 · k23 과 한 문장에서 섞지 않는다"] + (c.get("함정") or [])
            카드들.append(c)

    # 누계 · 분기
    if 누:
        누열 = next(c for c in 축.열 if c.ID == 누["열"])
        m = int(누열.개월) if float(누열.개월) == int(누열.개월) else None
        if 국내:
            분기, 까닭 = 국내분기(회차, 누열, 누, 원천)
        else:
            분기, 까닭 = 미국분기(회차, 누열, 누, 원천, 통화)
        if not 분기:
            문["못지음"].append({"무엇": "최근 분기(k23) · 전년 같은 기간(k22)", "까닭": 까닭})
        for x in (분기 or {}).get("_까닭") or []:
            문["못지음"].append({"무엇": "분기 · 전년 같은 기간의 한 항목", "까닭": x})
        전누 = (분기 or {}).get("전년누계") or {}
        기간들 = [누]
        덧값, 덧계, 덧말 = [], [], ""
        if 전누.get("매출") or 전누.get("영업"):
            전p = {"이름": 누계이름(누열.회계연도 - 1, m, 결산월) if m else "전년 같은 기간", "매출": 전누.get("매출"), "영업": 전누.get("영업")}
            기간들.append(전p)
            덧값, 덧계, 조각 = _증감("전년 같은 기간 대비", 누, 전p, 통화)
            if 조각:
                덧말 = " 전년 같은 기간 대비 %s." % 조(", ".join(조각), "이다", "다")
        c = _기간카드("k22", 기간들, "%s 누계 실적(%s모델 기준 · 13번 원천 62 · 66%s)은" % (누["이름"], 기준말, 계정말), 통화,
                    [_필("기간", 누계기간말(m), "누계 값이다 — 연간 값으로 읽히지 않게")], 권장율 + 권장연결, 누["이름"], 덧계, 덧값, 덧말)
        if c:
            카드들.append(c)
        if 분기 and (분기["분기"].get("매출") or 분기["분기"].get("영업")):
            q = m // 3 if m else None
            if 결산월 == 12:
                분이름, 앞이름, 전이름 = "%d년 %d분기" % (누열.회계연도, q), ("%d년 %d분기" % (누열.회계연도, q - 1) if q > 1 else None), "%d년 %d분기" % (누열.회계연도 - 1, q)
            else:
                분이름, 앞이름, 전이름 = "FY%d %d분기" % (누열.회계연도, q), ("FY%d %d분기" % (누열.회계연도, q - 1) if q > 1 else None), "FY%d %d분기" % (누열.회계연도 - 1, q)
            지금 = dict(분기["분기"], 이름=분이름)
            기간들 = [지금]
            덧값, 덧계, 덧말들 = [], [], []
            if m == 6 and 앞이름:
                앞 = {"이름": 앞이름}
                for 항목 in ("매출", "영업"):
                    if 분기["누계"].get(항목) and 지금.get(항목):
                        앞[항목] = _차항(분기["누계"][항목], 지금[항목])
                if 앞.get("매출") or 앞.get("영업"):
                    기간들.append(앞)
                    v, k, 조각 = _증감("앞 분기 대비", 지금, 앞, 통화)
                    덧값 += v
                    덧계 += k
                    if 조각:
                        덧말들.append("앞 분기 대비 %s" % ", ".join(조각))
            전 = 분기.get("전년분기") or {}
            if 전.get("매출") or 전.get("영업"):
                전p = dict(전, 이름=전이름)
                기간들.append(전p)
                v, k, 조각 = _증감("전년 같은 분기 대비", 지금, 전p, 통화)
                덧값 += v
                덧계 += k
                if 조각:
                    덧말들.append("전년 같은 분기 대비 %s" % ", ".join(조각))
            c = _기간카드("k23", 기간들, "분기 실적(%s3개월 · 재무기준일 정기보고서)은" % 기준말, 통화,
                        [_필("기간", "분기", "3개월 값이다 — 누계 · 연간으로 읽히지 않게")], 권장율 + 권장연결, 분이름, 덧계, 덧값,
                        "".join(" %s." % 조(x, "이다", "다") for x in 덧말들))
            if c:
                if 분기.get("_까닭"):
                    c["함정"] = ["이 카드에 없는 항목은 기준이 모델과 달라 싣지 않았다 — %s" % "; ".join(분기["_까닭"])]
                카드들.append(c)

    # 최고 · 최저 · 직전 사이클 정점
    for cid, 목록, 기준글 in (("k24", 연간, (앵커["말"] if 같은기준 else "모델 기준 · 13번 원천 62 · 66")),
                           ("k24b", 앵연, (앵커 or {}).get("말", ""))):
        목록 = [p for p in 목록 if p.get("매출") and p.get("영업") and p["매출"]["v"] > 0]
        if len(목록) < 3:
            if cid == "k24" or 앵연:
                문["못지음"].append({"무엇": "연간 최고 · 최저(%s)" % cid, "까닭": "매출 · 영업이익이 함께 있는 연간 값이 셋 미만(%d해)" % len(목록)})
            continue
        율 = [(p, p["영업"]["v"] / p["매출"]["v"]) for p in 목록]
        고 = max(율, key=lambda x: x[1])
        저 = min(율, key=lambda x: x[1])
        매고 = max(목록, key=lambda p: p["매출"]["v"])
        영고 = max(목록, key=lambda p: p["영업"]["v"])
        영저 = min(목록, key=lambda p: p["영업"]["v"])
        범 = "%s~%s %s" % (목록[0]["이름"], 목록[-1]["이름"], _몇(len(목록), "해"))
        비목 = ", ".join(_비식(p["영업"], p["매출"]) for p in 목록)
        값, 계 = [], []
        조각 = ["%s 가운데 영업이익률이 가장 높은 해는 %s(%s), 가장 낮은 해는 %s" % (범, 고[0]["이름"], 퍼글(고[1], 1), 조("%s(%s)" % (저[0]["이름"], 퍼글(저[1], 1)), "이다", "다"))]
        for p, r, 말 in ((고[0], 고[1], "최고"), (저[0], 저[1], "최저")):
            값.append(_값(퍼글(r, 1), 퍼글(r, 2), 단위="비율", 기간=p["이름"], 무엇="영업이익률 %s" % 말))
            계.append(_계("%s 영업이익률의 %s" % (범, 말), "%s([%s]) == %s" % ("max" if 말 == "최고" else "min", 비목, _비식(p["영업"], p["매출"])), "참"))
            계.append(_계("%s 영업이익률" % p["이름"], _비식(p["영업"], p["매출"]), 퍼글(r, 1), 1))
        for p, 항목, 말, 함수 in ((매고, "매출", "매출 최대", "max"), (영고, "영업", "영업이익 최대", "max"), (영저, "영업", "영업이익 최소", "min")):
            글, u, 자 = 금액3(p[항목]["v"], 통화)
            값.append(_값(글, 금액본(p[항목]["v"], 통화), p[항목].get("장부"), "금액", 기간=p["이름"], 무엇=말))
            계.append(_계("%s %s" % (범, 말), "%s([%s]) == %s" % (함수, ", ".join(_절대식(q[항목]) for q in 목록), _절대식(p[항목])), "참"))
            계.append(_계("%s %s" % (p["이름"], 말), 나눔식(p[항목]["수"], Fraction(u) / p[항목]["배"]), 글, 자))
        끝말 = ("%s(%s), 가장 작았던 해는 %s(%s)" % (영고["이름"], 금액본(영고["영업"]["v"], 통화), 영저["이름"], 금액본(영저["영업"]["v"], 통화))) \
            if 영저 is not 영고 else "%s(%s)" % (영고["이름"], 금액본(영고["영업"]["v"], 통화))
        조각.append("매출이 가장 컸던 해는 %s(%s), 영업이익이 가장 컸던 해는 %s" % (매고["이름"], 금액본(매고["매출"]["v"], 통화), 조(끝말, "이다", "다")))
        앞 = [x for x in 율 if x[0]["해"] < 저[0]["해"]]
        함정 = ["「직전 사이클 정점」은 가장 낮은 해 앞에서 영업이익률이 가장 높았던 해를 가리키는 계산상의 이름이다 — 그 오르내림이 사이클인지는 이 카드가 판단하지 않는다"]
        if 앞:
            정 = max(앞, key=lambda x: x[1])
            첫 = 정[0] is 목록[0]
            조각.append("가장 낮은 해(%s) 앞에서 가장 높았던 해, 곧 직전 사이클 정점은 %s" % (
                저[0]["이름"], 조("%s(%s%s)" % (정[0]["이름"], 퍼글(정[1], 1), " · 이 시계열의 첫 해라 그 앞은 이 자료에 없음" if 첫 else ""), "이다", "다")))
            if 첫:
                함정.append("직전 정점 %s 시계열의 첫 해다 — 그 앞의 해가 더 높았을 수 있다(이 자료 밖)" % 조(정[0]["이름"], "은", "는"))
            값.append(_값(퍼글(정[1], 1), 퍼글(정[1], 2), 단위="비율", 기간=정[0]["이름"], 무엇="직전 사이클 정점"))
            if len(앞) > 1:
                계.append(_계("%s 앞의 최고" % 저[0]["이름"], "max([%s]) == %s" % (", ".join(_비식(x[0]["영업"], x[0]["매출"]) for x in 앞), _비식(정[0]["영업"], 정[0]["매출"])), "참"))
        else:
            조각.append("가장 낮은 해가 첫 해(%s)라 그 앞의 정점은 이 시계열에 없다" % 저[0]["이름"])
        if cid == "k24" and 누 and 누.get("매출") and 누.get("영업") and 누["매출"]["v"]:
            r = 누["영업"]["v"] / 누["매출"]["v"]
            말 = "높다" if r > 고[1] else ("낮다" if r < 고[1] else "같다")
            조각.append("%s 누계 영업이익률 %s 연간 최고 %s보다 %s" % (누["이름"], 조(퍼글(r, 1), "은", "는"), 퍼글(고[1], 1), 말))
            값.append(_값(퍼글(r, 1), 퍼글(r, 2), 단위="비율", 기간=누["이름"], 무엇="영업이익률"))
            계.append(_계("%s 누계 영업이익률이 연간 최고보다 %s" % (누["이름"], 말),
                         "%s %s %s" % (_비식(누["영업"], 누["매출"]), {"높다": ">", "낮다": "<", "같다": "=="}[말], _비식(고[0]["영업"], 고[0]["매출"])), "참"))
        c = {"id": cid, "주장": "%s연간 실적(%s)으로 보면 %s." % ("앵커 기준 " if cid == "k24b" else "", 기준글, ". ".join(조각)), "등급": "계산",
             "값": _겹없이(값, lambda v: (v["글"], v.get("_기간"), v.get("_무엇"))), "기간": 범, "계산": 계,
             "필수": [_필("범위", "가운데|중에서|중 |사이|동안|~|부터", "견준 해의 범위를 함께 — 「사상 최고」로 읽히지 않게"),
                    _필("기간", r"\d{4}년|FY", "어느 해인지")],
             "권장": 권장율,
             "원천": _겹없이([o for p in 목록 for 항목 in ("매출", "영업") for o in p[항목]["원천"]])}
        c["함정"] = ((["이 시계열의 매출은 모델 매출(13번 원천 62)과 정의가 다르다 — 이익률을 k21 · k22 · k23 과 섞어 견주지 않는다"] if cid == "k24b" else [])
                    + 함정)
        카드들.append(덧붙임(c, 목록))
    return 카드들, 축


# ══════════════════════════════════════════════════════ 6. 매출 구성 비중

def 비중카드(문, 원천, 장부, 가정, 가정파일, 메타, 축):
    """(바) 13번 원천 85 + s 의 맨 위 구분 실적 ÷ 원천 62 — 재무기준일 열(k31)과 최근 연간 열(k32)."""
    if 축 is None:
        return []
    통화, 배 = 메타["_통화"], 메타["_배"]
    구분 = ((가정.get("구조") or {}).get("매출구분")) or []
    원 = 가정.get("원천") or {}
    근 = 가정.get("원천근거") or {}
    위 = [s for s in 구분 if not s.get("상위") and s.get("번호") is not None]
    if len(위) < 2:
        문["못지음"].append({"무엇": "매출 구성 비중(k31 · k32)", "까닭": "맨 위 매출 구분이 %d개 — 비중을 셀 구성이 없음(매출이 한 줄)" % len(위)})
        return []
    열들 = [c for c in 축.열 if c.구분 == "실적"]
    고를 = []
    if 열들:
        고를.append(("k31", 열들[-1]))
        연 = [c for c in 열들 if c.종류 == 축모듈.FY실적]
        if 연 and 연[-1] is not 열들[-1]:
            고를.append(("k32", 연[-1]))
    카드들 = []
    for cid, c in 고를:
        합 = (원.get(매출줄) or {}).get(c.ID)
        조각값 = [(s, str(구분줄밑 + int(s["번호"])), (원.get(str(구분줄밑 + int(s["번호"]))) or {}).get(c.ID)) for s in 위]
        빈 = [s.get("이름") for s, _줄, v in 조각값 if v is None]
        if 합 is None or 빈 or not 분(합):
            문["못지음"].append({"무엇": "매출 구성 비중 %s(%s)" % (cid, c.ID), "까닭": "매출액(원천 62) 또는 구분 실적(원천 85 + s)이 빔 — %s" % (빈 or "매출액")})
            continue
        이름 = 열이름(c, 축.결산월)
        합v = 분(합)
        값, 계, 원목, 조각, 함정 = [], [], [], [], []
        원목.append(원천.원(가정파일, '"%s": %s' % (c.ID, json.dumps(합)), 자리="원천.%s.%s" % (매출줄, c.ID)))
        글합 = Fraction(0)
        for s, 줄, v in 조각값:
            r = 분(v) / 합v
            자 = 0 if r >= Fraction(1, 10) else 1
            글 = 퍼글(r, 자)
            글합 += Fraction(str(십(r * 100, 자)))
            값.append(_값(글, 퍼글(r, 1), 단위="비율", 구분=s.get("이름")))
            계.append(_계("%s 비중(%s)" % (s.get("이름"), c.ID), "%s / %s" % (수글(v), 수글(합)), 글, 자))
            g, u, 자금 = 금액3(분(v) * 배, 통화)
            장, 장값 = 장부.실적(c.ID, 분(v), g)
            값.append(_값(g, 금액본(분(v) * 배, 통화), 장, "금액", 구분=s.get("이름"), 장부값같음=장값))
            계.append(_계("%s 매출(%s)" % (s.get("이름"), c.ID), 나눔식(수글(v), Fraction(u) / 배), g, 자금))
            원목.append(원천.원(가정파일, '"%s": %s' % (c.ID, json.dumps(v)), 자리="원천.%s.%s" % (줄, c.ID)))
            for x in 근.get(줄) or []:
                if isinstance(x, str) and x.startswith("[판단]"):
                    함정.append("구분 「%s」는 이 평가가 묶은 것이다 — %s" % (s.get("이름"), x))
                    원목.append(원천.원(가정파일, x, 자리="원천근거.%s" % 줄))
            조각.append("%s %s(%s)" % (s.get("이름"), 퍼글(r, 1), 금액본(분(v) * 배, 통화)))
        g, u, 자금 = 금액3(합v * 배, 통화)
        장, 장값 = 장부.실적(c.ID, 합v, g)
        값.append(_값(g, 금액본(합v * 배, 통화), 장, "금액", 구분="합계", 장부값같음=장값))
        계.append(_계("매출액(%s)" % c.ID, 나눔식(수글(합), Fraction(u) / 배), g, 자금))
        차 = 합v - sum(분(v) for _s, _줄, v in 조각값)
        주장 = "%s 매출 %s 가운데 %s다." % (이름, 금액본(합v * 배, 통화), ", ".join(조각))
        if abs(차) > Fraction(1, 2):
            주장 += " 구분의 합은 매출액과 %s 다르다." % 금액본(차 * 배, 통화)
            함정.append("구분 실적의 합이 매출액(원천 62)과 %s 다르다" % 금액본(차 * 배, 통화))
        else:
            계.append(_계("구분 합 = 매출액(%s)" % c.ID, "abs(%s - (%s)) <= 0.5" % (수글(합), " + ".join(수글(v) for _s, _줄, v in 조각값)), "참"))
        if 글합 != 100:
            함정.append("보이는 자릿수의 비중을 더하면 %s%%다 — 반올림 차이다(10%% 이상은 정수 · 그 아래는 소수 첫째 자리)" % _쉼(십(글합, 1), 1))
        기 = 누계기간말(int(c.개월)) if c.종류 != 축모듈.FY실적 else r"\d{4}년|연간"
        카드들.append({"id": cid, "주장": 주장, "등급": "계산", "값": _겹없이(값, lambda v: (v["글"], v.get("_구분"))), "기간": 이름,
                    "계산": 계, "필수": [_필("기간", 기, "어느 기간의 비중인지"), _필("단위", "매출|비중", "매출 가운데의 비중이다")],
                    "원천": _겹없이(원목), "함정": 함정})
    return 카드들


# ══════════════════════════════════════════════════════ 7. 짓기

def 짓기(회차, 가정=None, 문턱=기본문턱, 순위수=기본순위, 시작=None):
    """→ (카드 문서, 오류, 경고). 오류가 있으면 문서를 쓰지 않는다."""
    회차 = os.path.abspath(회차)
    if not os.path.isdir(회차):
        raise 입력오류("회차 폴더가 없음 — %s" % 회차)
    if not 0 < float(문턱) < 1:
        raise 입력오류("문턱은 0 과 1 사이 — %s" % 문턱)
    if int(순위수) < 1:
        raise 입력오류("순위는 1 이상 — %s" % 순위수)
    장부 = 장부색인(회차)
    gp = 가정찾기(회차, 가정, 장부)
    가 = json.load(io.open(gp, encoding="utf-8"))
    가정파일 = os.path.relpath(gp, 회차).replace("\\", "/")
    T = 기준.평가기준일(가)
    F = 기준.재무기준일(가)
    메타 = dict(가.get("메타") or {})
    메타["_통화"] = ("%s" % (메타.get("표시통화") or "KRW")).upper()
    메타["_배"] = _단위배(메타)
    원천 = 원천글(회차)
    문 = {"판": K.판, "회사": 메타.get("회사명"), "평가기준일": T.isoformat(), "재무기준일": F.isoformat(), "카드": [],
         "함정_메모": [], "결론에_나오는_용어": [], "못지음": [],
         "_만든곳": "스크립트/카드_계산.py(%s)" % 판, "_가정": 가정파일,
         "_설정": {"문턱": float(문턱), "순위수": int(순위수), "보이는자리": 보이는자리, "반올림": "ROUND_HALF_UP — 정확한 비에서 한 번",
                 "표시통화": 메타["_통화"], "금액단위": 메타.get("금액단위"), "주당단위": 메타.get("주당단위"),
                 "장부": 장부파일 if 장부.있음 else None, "시작": 시작}}
    문["카드"] += 주가카드(문, 회차, 원천, 장부, 메타, T, F, 분(str(문턱)), int(순위수), 시작)
    c, 축 = 실적카드(문, 회차, 원천, 장부, 가, 가정파일, 메타)
    문["카드"] += c
    문["카드"] += 비중카드(문, 원천, 장부, 가, 가정파일, 메타, 축)
    for c in 문["카드"]:
        for 칸 in ("함정", "권장", "날짜"):
            if 칸 in c and not c[칸]:
                del c[칸]
    오, 경, 판정 = K.문서검사(문)
    return 판정, 오, 경


def main(argv=None):
    ap = argparse.ArgumentParser(description="계산 카드 — 시세 · 실적 · 비중을 원자료로 셈해 사실 카드로")
    ap.add_argument("회차")
    ap.add_argument("--낼", help="쓸 곳(기본 <회차>/_raw/카드/계산.json)")
    ap.add_argument("--가정", help="가정 파일(회차 폴더 기준 · 기본 자동)")
    ap.add_argument("--문턱", type=float, default=기본문턱, help="꺾임으로 셀 되돌림(기본 %.2f)" % 기본문턱)
    ap.add_argument("--순위", type=int, default=기본순위, help="구간마다 싣는 하루 등락의 수(기본 %d)" % 기본순위)
    ap.add_argument("--시작", help="조회 구간의 첫날(YYYY-MM-DD · 기본 시세 파일의 첫날)")
    인 = ap.parse_args(argv)
    try:
        문, 오, 경 = 짓기(인.회차, 인.가정, 인.문턱, 인.순위, 인.시작)
    except (입력오류, 기준.기준일오류) as e:
        print("입력 오류 — %s" % e)
        return 2
    for x in 오:
        print("오류 " + x)
    for x in 경:
        print("경고 " + x)
    if 오:
        print("카드 검사 오류 %d — 쓰지 않음" % len(오))
        return 1
    낼 = 인.낼 or os.path.join(인.회차, "_raw", "카드", "계산.json")
    os.makedirs(os.path.dirname(os.path.abspath(낼)), exist_ok=True)
    io.open(낼, "w", encoding="utf-8").write(json.dumps(문, ensure_ascii=False, indent=1))
    print("계산 카드 %d장 · 못 지음 %d · 경고 %d → %s" % (len(문["카드"]), len(문["못지음"]), len(경), 낼))
    for c in 문["카드"]:
        print("  %-5s %s" % (c["id"], c["주장"][:120]))
    for x in 문["못지음"]:
        print("  못 지음 — %s: %s" % (x["무엇"], x["까닭"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

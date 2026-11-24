# -*- coding: utf-8 -*-
"""카드감사 — 사실 카드가 참인지 글을 쓰기 전에 한 번 본다(레터 문체 3단계 B4 · 2026-10-26).

왜 있나
    글은 카드를 옮긴 것이다(연구/레터_문체체계_독립설계안_20261026.md 3-1). 그래서 카드가 틀리면 문장 단계의 국소 대조는 그 틀림을
    볼 수 없다 — 실험에서 국소 대조가 놓친 것은 모두 카드 쪽 문제(등급 · 기준 · 같은 원천 안의 다른 서술 · 레터 자신의 원자료와
    어긋난 순위 주장)였다(설계안 5-3 · 5-5). 카드 감사는 그것을 카드를 지을 때 한 번 잡는다(설계안 3-2 ② · 3-5).
    코드로 셀 수 있는 것은 이 파일이 보고, 셀 수 없는 것(같은 대상의 다른 서술 · 같은 문단의 반대 진술과 조건 · 주장이 인용보다
    센가 · 측정 기준 · 아래 「후보」의 판정)은 큰 모델이 회사당 한 번 본다(`.claude/갈래/V5_카드감사.md`). 이 파일은 그 모델이
    원천 파일을 다시 열지 않게 카드와 원천 문단을 한 파일(묶음)에 모아 준다(설계안 3-6 — 비용은 도구 왕복이 만든다).
    **카드 문서를 고치지 않는다.** 고칠 제안만 낸다.

보는 것(규칙 이름은 연구/문체3단계_20261026/검사기규칙_v0.md 2절)
    꼴    카드.문서검사(B1) 그대로 — 꼴이 틀린 카드는 아래 셈이 믿을 수 없다
    F4    인용 실재 — 공시절.인용대조(B3) 그대로. 불일치 · 파일없음 · 인용없음 · 원천없음 = 오류, 일치(빈칸) = 경고(글자는 같고 빈칸만 다름)
    F4b   주장의 숫자가 인용 · 계산에 있나 — 카드는 인용만으로 선다(설계안 3-5). 글 원천 카드만 · 경고
    F5    계산 재현 — 카드설정 「식.이름」의 함수만 쓰는 식을 이 파일의 셈기로 다시 셈한다(eval 을 쓰지 않는다 · 정확한 분수).
          csv_max(파일[, 시작, 끝]) · csv_min(…) = 시작 ≤ 날 ≤ 끝(YYYY-MM-DD · 양끝 포함)의 최고 · 최저 종가, 범위가 없으면 파일 전체.
          csv_at(파일, 날) = 그날 종가. 장부(키) = 장부 「숫자」의 그 키 값. round(x, n) 도 ROUND_HALF_UP.
          값과 글의 대조는 **ROUND_HALF_UP** — 「자리」(없으면 글의 소수 자리)에서 정확한 값을 한 번만 반올림한다.
          글이 「%」 로 끝나면 식은 비(×100 해서 견줌), 「%p」 면 식이 이미 ×100. 「참」 · 「거짓」 은 식의 참 거짓.
          「67만 7,000원」 같은 겹친 단위 글은 원 단위 합으로도 견준다. 계산의 글이 카드 값에 없으면 경고
    F5b   장부 키 대조 — 값.장부 의 키가 장부(기본 = 회차의 레터_초안.장부.json · --장부)에 있고 그 키의 글에 값.글(또는 본편)이 있나
    F14   순위 주장 — 셀 수 있는 순위 · 최고 · 최저 · 「가장 크게」 · 1위(극값)와 합 · 비중(카드감사설정 「순위주장」)을 주장에 담은 카드가
          (가) 계산 칸이 없고 글(레터 · 원고 — 「글원천」)을 인용했거나 평가판단 · 레터정의 · 보도 · 검색 요약 등급이면 오류(판정 보기 K01),
          (나) 계산 칸이 없고 그 순위 말이 인용에도 없으면 오류, (다) 계산 칸이 없고 원천(공시 · 회사 발화 …)의 화자가 한 말이면 경고,
          (라) 계산 칸은 있는데 극값을 받치는 식(max · min · csv_max · csv_min · 비교식)이 없으면 경고.
          순위 창(「창」 또는 「_창」 — 파일 · 시작 · 끝 · 방향 · 순위수 · 보이는자리)이 있으면 원자료로 순위를 다시 세어 값의 날짜와 견준다
          (보이는 자릿수에서 끝 자리와 같은 날은 함께 — 카드_계산의 규칙). 다르면 오류. 같은 회차의 계산 카드가 그 날짜를 창에 품으면 그 id 를 제안한다
    F16   「없음」 기록 — 「없음」 문서(`_raw/카드/*_없음.json` · --없음)의 항목마다 항목 · 찾은 칸(찾은블록 · 찾은곳) · 검색어 · 결과가 있나,
          대신_지은카드가 카드에 있나, 찾은블록의 블록 번호가 공시절에 있나. 「없다 · 공개하지 않는다」를 주장하는 카드는 원천 인용이 스스로
          없음을 말하거나(글 원천이 아닌 것) 「없음」 항목의 대신_지은카드에 있어야 한다. 모두 경고(검사기규칙 F16)
    등급  등급 옮김 — 원천이 조사 산출(`매출스트림*.json`)의 항목이면 그 항목(없으면 가장 가까운 윗 항목)의 출처 성격 · 확신도를 카드설정의 등급으로
          옮겨(카드감사설정 「성격옮김」) 카드 등급이 그보다 세면 오류(판정 보기 K02). 그 항목에 성격이 없으면 같은 숫자 · 대상 낱말을 가진
          다른 항목의 성격을 쓴다. 계산 카드는 원자료의 등급이 3분 레터에 못 쓰는 것인데 층제한이 없으면 오류.
          원천이 글(레터)인 카드는 같은 숫자가 조사 산출에 낮은 성격으로 있으면 후보로 낸다(레터의 원천 등급을 카드가 옮겼나)
    공표일 원천 파일 경로의 접수번호(14자리 앞 여덟 자리 = 접수일)로 공표일을 제안한다(카드에 없으면 제안 · 다르면 경고)
    후보  같은 대상의 다른 숫자 — 카드 값(카드감사설정 「후보.단위」 — 기본 % · %p)의 대상 낱말을 카드 원천 · 회차 레터 글에서 찾아,
          같은 대상 곁에 보이는 자릿수에서 다른 숫자가 있으면 후보(판정 보기 K04). 코드가 셈한 카드(등급 계산 · 원천이 모두 원자료)는 찾지 않는다.
          측정 기준 — 인용이 든 공시절 블록의 머리에 「(… 기준)」이 있는데 카드의 주장 · 한정에 그 말이 없으면 후보(판정 보기 K03).
          후보의 판정은 V5 가 한다(같은 값 · 다른 기간 · 다른 대상 · 함정 메모 · 카드 오류)

「없음」 문서의 꼴 (F16 이 읽는 꼴 — B3 의 `공시카드 없음 1` 과 같다. 만든 곳마다 「형식」 앞말만 다르다)
    {"형식": "<만든 곳> 없음 1", "회사", "평가기준일", "재무기준일", "_원천": "찾은 원천(선택)",
     "없음": [{"항목": "찾았는데 없던 것", "찾은블록": ["공시절 블록 번호 + 제목" …] (또는 "찾은곳": ["파일 · 칸" …]),
              "검색어": ["…"], "결과": "원천이 무엇을 어떻게 적었나(없다는 것을 보여 주는 말)", "대신_지은카드": ["p13" …], "조사산출": "(선택)"}]}

내는 것
    <낼>(기본 회차 `_raw/카드감사.json`) — {"형식": "카드감사 1", 회사 · 평가기준일 · 재무기준일 · 회차 · 카드문서 · 없음문서 · 장부(판 · 일시 · 글해시) · 공시절,
      "셈": {카드 · 인용 · 계산 · 장부키 · 오류 · 경고 · 후보 · 규칙별}, "통과": 오류 0, "걸림": [{규칙 · 등급 · id · 무엇 · 근거 · 제안 · 후보}],
      "후보": [{번호 · id · 종류 · 값 · 대상 · 다른값 · 파일 · 줄 · 글 · 같은기간 · 같은원천 · 점수}], "제안": [{id · 칸 · 제안 · 까닭}],
      "반올림경계": [파이썬 round 와 ROUND_HALF_UP 이 갈리는 계산 — 이 감사는 뒤의 것으로 셈], "확인함": {…}, "묶음": 경로}
    <낼 이름>.md — 사람이 읽는 요약(오류 · 경고 · 제안 · 후보 수)
    <낼 폴더>/카드감사_V5묶음.md — V5 가 한 번에 읽는 카드 + 원천 문단 + 코드 감사 + 후보(--묶음 으로 바꾼다 · --묶음없이 로 끈다).
      원천 문단은 한 번씩만 싣는다 — 공시 인용은 공시절 블록 전체(길면 인용 둘레)와 같은 절의 윗 · 아래 블록, 레터는 빈 줄 사이 문단
      (표면 머리 두 줄과 그 줄), 조사 산출은 인용이 든 항목(출처 성격 · 확신도가 있는 가장 가까운 사전). 시세 · 장부 · 재무 JSON 은 싣지 않는다

쓰는 법(회차 폴더 = 카드 원천 경로의 기준 · 레터_초안.장부.json 이 있는 곳)
    python 스크립트/카드감사.py --회차 <폴더>                                   # _raw/사실카드.json(없으면 _raw/카드/*.json) → _raw/카드감사.json
    python 스크립트/카드감사.py <카드.json> [<카드.json> …] --회차 <폴더> --낼 <경로.json> [--장부 <경로>] [--없음 <경로>] [--공시절 <경로>]
    종료 코드 — 0 오류 없음 · 1 오류 있음(경고 · 후보는 막지 않는다) · 2 입력 오류(카드 · 회차 · 장부 파일 없음 · JSON 깨짐)

회사 · 업종 이름은 이 파일에 없다. 회사마다 다른 것은 카드 · 원천 · 장부뿐이다.
"""
from __future__ import annotations

import argparse
import ast
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
import 카드 as K                                     # noqa: E402
import 공시절 as P                                   # noqa: E402
from 종료코드 import 통과, 발견, 입력오류            # noqa: E402

형식 = "카드감사 1"
설정 = json.load(io.open(os.path.join(여기, "카드감사설정.json"), encoding="utf-8"))
등급세기 = {k: v for k, v in 설정["등급세기"].items() if not k.startswith("_")}
정규 = P.정규


class 셈오류(Exception):
    pass


class 입력문제(Exception):
    pass


def _읽기(p):
    try:
        return json.load(io.open(p, encoding="utf-8-sig"))
    except OSError as e:
        raise 입력문제("파일을 못 읽음 — %s (%s)" % (p, e))
    except ValueError as e:
        raise 입력문제("JSON 이 깨짐 — %s (%s)" % (p, e))


def _rel(p, 회차):
    try:
        return os.path.relpath(p, 회차).replace("\\", "/")
    except ValueError:
        return p.replace("\\", "/")


def _꼴(키):
    return re.compile(설정[키]["이름꼴"])


글원천꼴 = _꼴("글원천")
자료원천꼴 = _꼴("자료원천")
조사파일꼴 = _꼴("조사파일")


def 글원천(파일):
    return bool(글원천꼴.search(str(파일 or "").replace("\\", "/")))


def 자료원천(파일):
    return bool(자료원천꼴.search(str(파일 or "").replace("\\", "/")))


def 조사원천(파일):
    return bool(조사파일꼴.search(str(파일 or "").replace("\\", "/")))


def 원천들(c):
    return [o for o in (c.get("원천") or []) if isinstance(o, dict)]


def 코드카드(c):
    """코드가 원자료로 셈한 카드 — 등급 계산이고 원천이 모두 원자료(시세 · 장부 · 재무 JSON)."""
    원 = 원천들(c)
    return c.get("등급") == "계산" and bool(원) and all(자료원천(o.get("파일")) for o in 원)


# ══ 숫자 — 정확한 분수와 ROUND_HALF_UP ══════════════════════════════════════════════════════════════════

def 분수(x):
    if isinstance(x, bool):
        raise 셈오류("참 거짓은 숫자가 아님")
    if isinstance(x, Fraction):
        return x
    if isinstance(x, int):
        return Fraction(x)
    if isinstance(x, float):
        return Fraction(Decimal(repr(x)))
    if isinstance(x, Decimal):
        return Fraction(x)
    s = str(x).replace(",", "").replace("−", "-").strip()
    try:
        return Fraction(Decimal(s))
    except Exception:                                # noqa: BLE001
        raise 셈오류("숫자로 읽지 못함 — %r" % (x,))


def 반올림(v, 자리):
    """정확한 값 v(분수)를 소수 자리 「자리」에서 한 번 ROUND_HALF_UP(0 에서 먼 쪽 — 사람 눈의 반올림)."""
    v = 분수(v)
    with localcontext() as ctx:
        ctx.prec = 80
        d = Decimal(v.numerator) / Decimal(v.denominator)
        return d.quantize(Decimal(1).scaleb(-int(자리)), rounding=ROUND_HALF_UP)


_수글 = re.compile(r"([−\-+]?)\s*(\d[\d,]*(?:\.\d+)?)")
_겹수 = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(조|억|만)?")
_겹단위 = {"조": 10 ** 12, "억": 10 ** 8, "만": 10 ** 4, None: 1, "": 1}


def 글수(글):
    """글의 첫 숫자 → (부호 붙은 Decimal, 소수 자리). 없으면 None."""
    m = _수글.search(str(글))
    if not m:
        return None
    t = m.group(2).replace(",", "")
    d = Decimal(t)
    if m.group(1) in ("−", "-"):
        d = -d
    return d, (len(t.split(".")[1]) if "." in t else 0)


def 겹수(글):
    """「67만 7,000원」 · 「131조 8,950억 원」 → 원 단위 합(Decimal). 겹친 단위가 아니면 None."""
    s = str(글)
    짝 = [(m.group(1), m.group(2)) for m in _겹수.finditer(s)]
    if len(짝) < 2 or not 짝[0][1]:
        return None
    합 = sum(Decimal(n.replace(",", "")) * _겹단위[u] for n, u in 짝)
    return -합 if s.strip()[:1] in ("−", "-") else 합


def 글맞음(v, 글, 자리=None):
    """식 값 v 가 글과 맞나 → (맞음, 반올림한 값 글, 파이썬 round 로 셈한 글 또는 None)."""
    글 = str(글).strip()
    if 글 in ("참", "거짓"):
        return (isinstance(v, bool) and v == (글 == "참")) or (not isinstance(v, bool) and bool(v) == (글 == "참")), str(bool(v)), None
    if isinstance(v, bool) or not isinstance(v, (Fraction, int, float)):
        return False, repr(v), None
    v = 분수(v)
    읽 = 글수(글)
    if 읽 is None:
        return False, "글에 숫자가 없음", None
    n, 글자리 = 읽
    배 = 100 if re.search(r"%(?!\s*p)", 글) else 1
    자 = int(자리) if 자리 is not None else 글자리
    q = 반올림(v * 배, 자)
    파이썬 = None
    try:
        f = round(float(v * 배), 자)
        if Decimal(repr(f)).quantize(Decimal(1).scaleb(-자)) != q:
            파이썬 = str(Decimal(repr(f)).quantize(Decimal(1).scaleb(-자)))
    except (OverflowError, ValueError):
        pass
    if q == n.quantize(Decimal(1).scaleb(-자), rounding=ROUND_HALF_UP):
        return True, str(q), 파이썬
    겹 = 겹수(글)
    if 겹 is not None and 반올림(v, 0) == 겹.quantize(Decimal(1), rounding=ROUND_HALF_UP):
        return True, str(반올림(v, 0)), None
    return False, str(q), 파이썬


# ══ 셈기 — 카드설정 「식.이름」만 아는 작은 해석기(eval 을 쓰지 않는다) ════════════════════════════════════

def _날글(s):
    s = str(s).strip()
    if re.fullmatch(r"\d{8}", s):
        s = "%s-%s-%s" % (s[:4], s[4:6], s[6:])
    try:
        return _dt.date.fromisoformat(s).isoformat()
    except ValueError:
        raise 셈오류("날짜 꼴이 아님 — %r" % s)


def 시세읽기(경로):
    """일별 종가 CSV — 「#」 줄 · 머리 줄(date,close)을 건너뛰고 [(YYYY-MM-DD, 분수)] 를 날짜 차례로. 머리에 close 가 있으면 그 칸."""
    줄들 = []
    칸 = 1
    for 줄 in io.open(경로, encoding="utf-8-sig"):
        s = 줄.strip()
        if not s or s.startswith("#"):
            continue
        쪽 = [x.strip() for x in s.split(",")]
        if not re.match(r"\d", 쪽[0]):
            머리 = [x.lower() for x in 쪽]
            if "close" in 머리:
                칸 = 머리.index("close")
            continue
        try:
            줄들.append((_날글(쪽[0]), 분수(쪽[칸])))
        except (셈오류, IndexError):
            continue
    줄들.sort()
    return 줄들


class 셈기:
    def __init__(self, 회차, 장부=None):
        self.회차 = 회차
        self.장부 = 장부 or {}
        self._시세 = {}
        self.이름 = set(K.식이름)

    def 시세(self, 파일):
        p = 파일 if os.path.isabs(파일) else os.path.join(self.회차, 파일)
        if p not in self._시세:
            if not os.path.exists(p):
                raise 셈오류("시세 파일이 없음 — %s" % 파일)
            self._시세[p] = 시세읽기(p)
        return self._시세[p]

    def _창값(self, 파일, 시작=None, 끝=None):
        s = _날글(시작) if 시작 is not None else None
        e = _날글(끝) if 끝 is not None else None
        값 = [v for d, v in self.시세(파일) if (s is None or d >= s) and (e is None or d <= e)]
        if not 값:
            raise 셈오류("창 안에 시세가 없음 — %s %s~%s" % (파일, 시작, 끝))
        return 값

    def 함수(self, 이름, 인):
        if 이름 not in self.이름:
            raise 셈오류("쓸 수 없는 이름 %s" % 이름)
        if 이름 == "date":
            return _dt.date(*[int(분수(x)) for x in 인])
        if 이름 == "abs":
            return abs(인[0])
        if 이름 == "round":
            자 = int(분수(인[1])) if len(인) > 1 else 0
            return Fraction(반올림(인[0], 자))
        if 이름 in ("min", "max", "sum"):
            목 = list(인[0]) if len(인) == 1 and isinstance(인[0], list) else list(인)
            if not 목:
                raise 셈오류("%s 에 넣은 것이 없음" % 이름)
            return {"min": min, "max": max, "sum": lambda x: sum(x, Fraction(0))}[이름](목)
        if 이름 in ("csv_max", "csv_min"):
            if not 1 <= len(인) <= 3 or len(인) == 2:
                raise 셈오류("%s(파일[, 시작, 끝]) 꼴이 아님" % 이름)
            값 = self._창값(*인)
            return max(값) if 이름 == "csv_max" else min(값)
        if 이름 == "csv_at":
            날 = _날글(인[1])
            for d, v in self.시세(인[0]):
                if d == 날:
                    return v
            raise 셈오류("그날 시세가 없음 — %s %s" % (인[0], 날))
        if 이름 == "장부":
            키 = str(인[0])
            if not self.장부:
                raise 셈오류("장부가 없음")
            값 = {x for x in self.장부.get(키, {}).get("값", [])}
            if not 값:
                raise 셈오류("장부에 없는 키(또는 값 없음) — %s" % 키)
            if len(값) > 1:
                raise 셈오류("장부의 같은 키에 값이 여럿 — %s" % 키)
            return 분수(next(iter(값)))
        raise 셈오류("셈기가 모르는 이름 %s" % 이름)

    def 값(self, 식):
        try:
            나무 = ast.parse(식, mode="eval")
        except SyntaxError as e:
            raise 셈오류("식을 읽지 못함 — %s" % e.msg)
        return self._e(나무.body)

    def _e(self, n):
        if isinstance(n, ast.Constant):
            v = n.value
            if isinstance(v, bool) or isinstance(v, str):
                return v
            if isinstance(v, (int, float)):
                return 분수(v)
            raise 셈오류("쓸 수 없는 값")
        if isinstance(n, (ast.List, ast.Tuple)):
            return [self._e(x) for x in n.elts]
        if isinstance(n, ast.UnaryOp):
            v = self._e(n.operand)
            if isinstance(n.op, ast.USub):
                return -v
            if isinstance(n.op, ast.UAdd):
                return +v
            if isinstance(n.op, ast.Not):
                return not v
            raise 셈오류("쓸 수 없는 단항")
        if isinstance(n, ast.BinOp):
            a, b = self._e(n.left), self._e(n.right)
            try:
                if isinstance(n.op, ast.Add):
                    return a + b
                if isinstance(n.op, ast.Sub):
                    r = a - b
                    return r
                if isinstance(n.op, ast.Mult):
                    return a * b
                if isinstance(n.op, ast.Div):
                    return Fraction(a) / Fraction(b)
                if isinstance(n.op, ast.FloorDiv):
                    return Fraction(a // b)
                if isinstance(n.op, ast.Mod):
                    return Fraction(a % b)
                if isinstance(n.op, ast.Pow):
                    if isinstance(b, Fraction) and b.denominator == 1:
                        return Fraction(a) ** int(b)
                    return 분수(float(a) ** float(b))
            except ZeroDivisionError:
                raise 셈오류("0 으로 나눔")
            except TypeError as e:
                raise 셈오류("셈할 수 없는 짝 — %s" % e)
            raise 셈오류("쓸 수 없는 셈")
        if isinstance(n, ast.Compare):
            왼 = self._e(n.left)
            for op, 오른식 in zip(n.ops, n.comparators):
                오른 = self._e(오른식)
                try:
                    ok = {ast.Eq: lambda x, y: x == y, ast.NotEq: lambda x, y: x != y, ast.Lt: lambda x, y: x < y,
                          ast.LtE: lambda x, y: x <= y, ast.Gt: lambda x, y: x > y, ast.GtE: lambda x, y: x >= y}[type(op)](왼, 오른)
                except KeyError:
                    raise 셈오류("쓸 수 없는 비교")
                except TypeError as e:
                    raise 셈오류("견줄 수 없는 짝 — %s" % e)
                if not ok:
                    return False
                왼 = 오른
            return True
        if isinstance(n, ast.BoolOp):
            값들 = [self._e(x) for x in n.values]
            return all(값들) if isinstance(n.op, ast.And) else any(값들)
        if isinstance(n, ast.Call):
            if not isinstance(n.func, ast.Name) or n.keywords:
                raise 셈오류("함수는 이름으로만 · 이름 붙은 인자 없이")
            return self.함수(n.func.id, [self._e(x) for x in n.args])
        if isinstance(n, ast.Attribute):
            v = self._e(n.value)
            if n.attr == "days" and isinstance(v, _dt.timedelta):
                return v.days
            raise 셈오류("쓸 수 없는 속성 %s" % n.attr)
        if isinstance(n, ast.Name):
            raise 셈오류("이름 %s 는 함수로만 쓴다" % n.id)
        raise 셈오류("쓸 수 없는 꼴 %s" % type(n).__name__)


# ══ 장부 ══════════════════════════════════════════════════════════════════════════════════════════════

def 장부읽기(경로):
    """레터_초안.장부.json → ({키: {"글": set, "값": set}}, 머리)."""
    d = _읽기(경로)
    표 = {}
    for x in d.get("숫자", []) or []:
        if not isinstance(x, dict) or "키" not in x:
            continue
        e = 표.setdefault(x["키"], {"글": set(), "값": set()})
        if x.get("글") is not None:
            e["글"].add(str(x["글"]))
        if isinstance(x.get("값"), (int, float)) and not isinstance(x.get("값"), bool):
            e["값"].add(x["값"])
    머리 = {k: d.get(k) for k in ("판", "일시", "가정해시", "글해시", "회사")}
    return 표, 머리


# ══ 원천 글 · 문맥 ════════════════════════════════════════════════════════════════════════════════════

_글캐시 = {}


def 원천원글(경로):
    """문맥을 뽑을 글(줄바꿈 남김). htm 은 조항추출.원문글, xml 은 같은 이름 txt 가 있으면 그것."""
    k = os.path.abspath(경로)
    if k not in _글캐시:
        확 = os.path.splitext(경로)[1].lower()
        if 확 == ".xml" and os.path.exists(os.path.splitext(경로)[0] + ".txt"):
            경로 = os.path.splitext(경로)[0] + ".txt"
        try:
            _글캐시[k] = P.원천글(경로)
        except OSError:
            _글캐시[k] = ""
    return _글캐시[k]


def _인용식(인용):
    조각 = [re.escape(x) for x in 정규(인용).split(" ") if x]
    if not 조각:
        return None
    try:
        return re.compile(r"\s*".join(조각) if len(정규(인용)) <= 400 else r"\s+".join(조각))
    except re.error:
        return None


def 인용자리(글, 인용, 상한=3):
    식 = _인용식(인용)
    if not 식:
        return []
    return [m.span() for _i, m in zip(range(상한), 식.finditer(글))]


def _자름(s, 상한):
    s = 정규(s)
    return s if len(s) <= 상한 else s[:상한] + " …"


class 공시절색인:
    """공시절.json 의 블록 — 인용이 든 블록 · 제목경로 · 블록 번호."""

    def __init__(self, 경로):
        self.경로 = 경로
        self.블록 = []
        self.번호 = set()
        if 경로 and os.path.exists(경로):
            d = _읽기(경로)
            for b in d.get("절", []) or []:
                글 = 정규(" ".join(b.get("글", []) or []))
                self.블록.append((b, 글, re.sub(r"\s+", "", 글)))
                self.번호.add(str(b.get("번호")))

    def 찾기(self, 파일, 인용, 상한=3, 자리=None):
        """인용이 든 블록. 원천의 「자리」가 블록 번호(「공시절 1-075 …」)를 가리키면 그 블록을 먼저 · 거기 없으면 모든 블록."""
        q = 정규(인용)
        q0 = re.sub(r"\s+", "", q)
        밖 = []
        for b, 글, 글0 in self.블록:
            if 파일 and b.get("파일") and os.path.splitext(os.path.basename(str(b.get("파일"))))[0] != os.path.splitext(os.path.basename(str(파일)))[0]:
                continue
            if q and (q in 글 or q0 in 글0):
                밖.append((b, 글))
        m = re.search(r"(\d+-\d+)", str(자리 or ""))
        if m:
            그 = [x for x in 밖 if str(x[0].get("번호")) == m.group(1)]
            if 그:
                return 그
        return 밖[:상한]

    def 이웃(self, b, 상한=3):
        """같은 절의 윗 블록(제목경로가 b 의 앞머리) · 아래 블록(b 의 제목경로로 시작) — [(블록, 「윗 블록」|「아래 블록」)]."""
        길 = list(b.get("제목경로") or [])
        if len(길) < 2:
            return []
        밖 = []
        for x, _g, _g0 in self.블록:
            if x is b or x.get("파일") != b.get("파일"):
                continue
            x길 = list(x.get("제목경로") or [])
            if len(x길) == len(길) - 1 and x길 == 길[:-1]:
                밖.append((x, "윗 블록"))
            elif len(x길) == len(길) + 1 and x길[:-1] == 길:
                밖.append((x, "아래 블록"))
        return 밖[:상한]


def _창글(글, 자리들, 창, 상한):
    if not 자리들:
        return _자름(글, 상한)
    조각 = []
    for s, e in 자리들:
        조각.append([max(0, s - 창), min(len(글), e + 창)])
    조각.sort()
    합 = [조각[0]]
    for a, b in 조각[1:]:
        if a <= 합[-1][1]:
            합[-1][1] = max(합[-1][1], b)
        else:
            합.append([a, b])
    밖 = []
    for a, b in 합:
        밖.append(("… " if a > 0 else "") + 정규(글[a:b]) + (" …" if b < len(글) else ""))
    return _자름(" ".join(밖), 상한)


def _조사항목(데이터, 인용):
    """조사 산출 JSON 에서 인용이 든 문자열 잎과 그 윗 사전들 → [(자리 이름, 잎에서 가까운 차례의 사전들)]."""
    q = 정규(인용)
    q0 = re.sub(r"\s+", "", q)
    밖 = []

    def 걷(x, 길, 사전들):
        if isinstance(x, dict):
            for k, v in x.items():
                걷(v, 길 + [str(k)], 사전들 + [x])
        elif isinstance(x, list):
            for i, v in enumerate(x):
                걷(v, 길 + ["[%d]" % i], 사전들)
        elif isinstance(x, str):
            n = 정규(x)
            if q and (q in n or q0 in re.sub(r"\s+", "", n)):
                밖.append((".".join(길).replace(".[", "["), list(reversed(사전들))))
    걷(데이터, [], [])
    return 밖


def 성격칸(d):
    for k in 설정["조사파일"]["성격칸"]:
        if d.get(k):
            return str(d[k])
    return None


def 확신칸(d):
    for k in 설정["조사파일"]["확신칸"]:
        if d.get(k):
            return str(d[k])
    return None


def 성격등급(성격, 확신=None):
    """출처 성격 글 → 카드가 가질 수 있는 가장 센 등급(카드설정 등급 이름) · 없으면 None."""
    if not 성격:
        return None
    if 성격 in K.등급표:
        등 = 성격
    else:
        등 = None
        for 식, 이름 in 설정["성격옮김"]["줄"]:
            if re.search(식, 성격):
                등 = 이름
                break
    if 등 and 확신:
        cap = 설정["성격옮김"]["확신도"].get(str(확신).strip()[:1])
        if cap and 등급세기.get(cap, 9) < 등급세기.get(등, 9):
            등 = cap
    return 등


# ══ 대상 낱말 · 후보 ══════════════════════════════════════════════════════════════════════════════════

후보설정 = 설정["후보"]
_기간말 = re.compile(후보설정["기간말"])
_멈춤 = set(후보설정["멈춤말"])
_조사 = sorted(후보설정["조사"], key=len, reverse=True)
_후보수 = re.compile(r"(?<![\d.])([−\-+]?)(\d+(?:\.\d+)?)\s*(%p|%포인트|%)")


def _낱말다듬기(t):
    t = t.strip("「」『』“”\"'()[]{}<>·,.:;!?~—–-")
    if t in _조사:
        return ""
    for j in _조사:
        if len(t) - len(j) >= 2 and t.endswith(j):      # 줄기는 두 글자 넘게 남긴다(「할인」의 「인」 · 「차이」의 「이」를 떼지 않는다)
            t = t[: -len(j)]
            break
    return t


def 대상낱말(주장, 값글):
    """주장에서 값 글 앞의 낱말(대상) — 마지막이 머리 낱말. 숫자 · 날짜 · 기간 말 · 멈춤 말은 뺀다."""
    s = 정규(주장).replace("−", "-")
    g = 정규(값글).replace("−", "-").lstrip("+-")
    밖 = []
    for m in re.finditer(re.escape(g), s):
        앞 = s[max(0, m.start() - 후보설정["앞창"]): m.start()]
        for 끊 in (". ", "다. ", " — ", ";", ", ", "고 ", "며 "):
            if 끊 in 앞:
                앞 = 앞.rsplit(끊, 1)[1]
        앞 = _기간말.sub(" ", 앞)
        앞 = re.sub(r"\d[\d,.]*\s*(?:조|억|만)?\s*(?:원|달러|배|일|%p|%)?(?:으로|로|에서|이고|이며|이다|에)?", " ", 앞)
        낱 = []
        for t in re.split(r"[\s·,()/\[\]「」→~]+", 앞):
            t = _낱말다듬기(t)
            if len(t) < 2 or t in _멈춤 or re.fullmatch(r"[\W\d_]+", t):
                continue
            낱.append(t)
        if 낱:
            밖.append(낱[-후보설정["대상낱말수"]:])
    return 밖


def _낱말머리(문, 자리0):
    """빈칸을 지운 글의 자리 자리0 이 원래 글에서 낱말의 머리(앞이 빈칸 · 기호 · 글 머리)인가."""
    n = -1
    for i, ch in enumerate(문):
        if ch.isspace():
            continue
        n += 1
        if n == 자리0:
            return i == 0 or not (문[i - 1].isalnum() or "가" <= 문[i - 1] <= "힣")
    return False


def _머리꼴(낱):
    """머리 낱말과 그 뒷말(네 글자 넘는 겹낱말이면 끝 세 글자 · 두 글자도) — 「소매점유율」 → 점유율."""
    꼴 = [낱]
    if len(낱) >= 4 and re.fullmatch(r"[가-힣]+", 낱):
        꼴 += [낱[-3:], 낱[-2:]]
    return 꼴


class 글더미:
    """후보를 찾을 글 — 파일마다 문장(줄 · 문장 끝 · 조사 산출의 문자열 잎) 목록."""

    def __init__(self, 회차):
        self.회차 = 회차
        self.문장 = {}

    def 넣기(self, 파일):
        p = 파일 if os.path.isabs(파일) else os.path.join(self.회차, 파일)
        키 = _rel(p, self.회차)
        if 키 in self.문장 or not os.path.exists(p) or 자료원천(키) or p.lower().endswith(".csv"):
            return
        if p.lower().endswith(".json"):
            try:
                데 = _읽기(p)
            except 입력문제:
                return
            잎 = []

            def 걷(x, 길):
                if isinstance(x, dict):
                    for k, v in x.items():
                        걷(v, 길 + "." + str(k))
                elif isinstance(x, list):
                    for i, v in enumerate(x):
                        걷(v, 길 + "[%d]" % i)
                elif isinstance(x, str) and len(x) > 6:
                    잎.append((길.lstrip("."), 정규(x)))
            걷(데, "")
            self.문장[키] = [(길, s, re.sub(r"\s+", "", s).replace("−", "-"), s) for 길, s in 잎]
            return
        글 = 원천원글(p)
        밖 = []
        for i, 줄 in enumerate(글.split("\n"), 1):
            줄 = 정규(줄)
            if len(줄) < 6:
                continue
            for 문 in re.split(r"(?<=다\.)\s+|(?<=[.?!])\s+(?=[A-Z가-힣])", 줄):
                if len(문) >= 6:
                    밖.append(("%d줄" % i, 문, re.sub(r"\s+", "", 문).replace("−", "-"), 줄))
        self.문장[키] = 밖


def _같은값(a, 자리a, 값들):
    """후보 숫자 a(자리a)가 카드 값 가운데 하나와 보이는 자릿수에서 같나 — 부호는 보지 않는다(「내렸다」 · 「−」)."""
    for b, 자리b in 값들:
        자 = min(자리a, 자리b)
        if 반올림(abs(분수(a)), 자) == 반올림(abs(분수(b)), 자):
            return True
    return False


def _가깝나(a, b):
    """후보 a 가 카드 값 b 와 가깝나(카드감사설정 「후보.가까움」) — 크기로 견준다."""
    가 = 후보설정.get("가까움") or {}
    a, b = abs(Decimal(a)), abs(Decimal(b))
    return abs(a - b) <= max(Decimal(str(가.get("비", 1))) * b, Decimal(str(가.get("차", 0))))


def 후보찾기(c, 더미, 원천파일들, 번호시작=1):
    """같은 대상 곁의 다른 숫자 → 후보 목록."""
    단위들 = set(후보설정["단위"])
    값글 = []
    for v in c.get("값", []) or []:
        for 칸 in ("글", "본편"):
            g = str((v or {}).get(칸) or "")
            m = _후보수.search(g.replace("−", "-"))
            if m and (m.group(3) in 단위들 or (m.group(3) == "%포인트" and "%p" in 단위들)):
                값글.append(g)
    if not 값글:
        for m in _후보수.finditer(str(c.get("주장", "")).replace("−", "-")):
            if m.group(3) in 단위들:
                값글.append(m.group(0))
    카드값 = []
    for m in _후보수.finditer(" ".join(값글 + [str(c.get("주장", ""))]).replace("−", "-")):
        t = m.group(2)
        카드값.append((Decimal(t), len(t.split(".")[1]) if "." in t else 0))
    카드기간 = set(x.replace(" ", "") for x in _기간말.findall(str(c.get("주장", "")) + " " + str(c.get("기간", ""))))
    본 = set()
    밖 = []
    for g in dict.fromkeys(값글):
        m0 = _후보수.search(g.replace("−", "-"))
        단 = m0.group(3)
        for 낱 in 대상낱말(c.get("주장", ""), g):
            머리 = 낱[-1]
            남 = 낱[:-1]
            for 파일, 문장들 in 더미.문장.items():
                같은원천 = 파일 in 원천파일들
                for 자리, 문, 문0, 줄글 in 문장들:
                    if not 남 and (not re.fullmatch(r"[가-힣]{4,}", 머리) or not (카드기간 and any(x in 문0 for x in 카드기간))):
                        continue      # 낱말 하나뿐인 대상은 한글 겹낱말(네 글자 이상) · 같은 기간 말이 있을 때만 — 「매출」 · 제품 이름 하나로는 시끄럽다
                    # 머리 낱말이 나오는 자리마다(겹낱말의 뒷말 포함) — 「신흥시장」 속의 「시장」처럼 다른 낱말 속은 뺀다
                    머리자리들 = []
                    for i_꼴, 꼴 in enumerate(_머리꼴(머리)):
                        p = 문0.find(꼴)
                        while p >= 0:
                            if (i_꼴 > 0 or _낱말머리(문, p)) and p not in 머리자리들:
                                머리자리들.append(p)
                            p = 문0.find(꼴, p + 1)
                    m, 맞은 = None, []
                    for 머리자리 in sorted(머리자리들):
                        # 대상의 다른 낱말은 머리 바로 앞(「곁」 글자 안)에 있어야 같은 대상이다
                        곁 = 문0[max(0, 머리자리 - 후보설정.get("곁", 16)): 머리자리]
                        맞은 = [t for t in 남 if t in 곁]
                        if 남 and not 맞은:
                            continue
                        뒤 = 문0[머리자리: 머리자리 + 후보설정["뒤창"] + len(머리)]
                        m = next((x for x in _후보수.finditer(뒤) if x.group(3) == 단 or (단 == "%p" and x.group(3) == "%포인트")), None)
                        if m:
                            break
                    for m in [m] if m else []:
                        if m.group(3) != 단 and not (단 == "%p" and m.group(3) == "%포인트"):
                            continue
                        t = m.group(2)
                        자 = len(t.split(".")[1]) if "." in t else 0
                        if _같은값(Decimal(t), 자, 카드값) or not _가깝나(t, m0.group(2)):
                            break
                        키 = (g, t, 정규(문)[:120])
                        if 키 in 본:
                            continue
                        본.add(키)
                        같은기간 = bool(카드기간) and any(x in 문0 for x in 카드기간)
                        점수 = len(맞은) + (2 if 같은기간 else 0) + (1 if 같은원천 else 0)
                        밖.append({"id": c.get("id"), "종류": "같은 대상 다른 숫자", "값": g, "대상": " ".join(낱),
                                  "다른값": (m.group(1) or "") + t + m.group(3), "파일": 파일, "줄": 자리,
                                  "글": _자름(문, 360), "같은기간": 같은기간, "같은원천": 같은원천, "점수": 점수,
                                  **({"문단": _창글(줄글, [(줄글.find(문[:20]), 줄글.find(문[:20]) + len(문))], 300, 900)} if 줄글 != 문 and 줄글.find(문[:20]) >= 0 else {})})
                        break
    밖.sort(key=lambda x: (-x["점수"], x["파일"], x["줄"]))
    # 같은 다른값 · 같은 글은 한 번만(레터 사본 여러 판에 같은 문장이 있다)
    줄임, 본2 = [], {}
    for x in 밖:
        k2 = (x["값"], x["다른값"], x["글"][:80])
        if k2 in 본2:
            본2[k2].setdefault("다른곳", []).append("%s %s" % (x["파일"], x["줄"]))
            continue
        본2[k2] = x
        줄임.append(x)
    return 줄임[: 후보설정["카드당상한"]]


_기준머리 = re.compile(설정["기준후보"]["머리꼴"])
_기준뺌 = re.compile(설정["기준후보"]["뺌"])


def 기준후보(c, 블록들):
    """인용이 든 공시절 블록의 머리에 측정 기준이 있는데 카드에 그 말이 없으면 후보."""
    밖 = []
    글 = " ".join([str(c.get("주장", ""))] + [str(f.get("정규식", "")) + " " + str(f.get("설명", ""))
                                          for 칸 in ("필수", "권장") for f in (c.get(칸) or []) if isinstance(f, dict)])
    본 = set()
    for b in 블록들:
        머리들 = list(b.get("제목경로") or []) + [b.get("제목") or ""]
        for 머리 in 머리들:
            for m in _기준머리.finditer(str(머리)):
                말 = m.group(1).strip()
                if not 말 or _기준뺌.search(말) or 말 in 본:
                    continue
                본.add(말)
                핵 = re.sub(r"\s+", "", 말)
                if 핵 in re.sub(r"\s+", "", 글):
                    continue
                # 그 머리가 카드의 대상과 닿아야 한다 — 머리 낱말(「지역별」 → 지역) 하나가 주장에 있을 것
                머리낱 = [re.sub(r"별$", "", t) for t in re.findall(r"[가-힣A-Za-z]{2,}", _기준머리.sub(" ", str(머리)))]
                if not any(len(t) >= 2 and t in str(c.get("주장", "")) for t in 머리낱):
                    continue
                밖.append({"id": c.get("id"), "종류": "측정 기준", "값": "", "대상": 말 + " 기준", "다른값": "",
                          "파일": b.get("파일"), "줄": "공시절 %s %s" % (b.get("번호"), b.get("제목")),
                          "글": "인용이 든 블록의 머리 「%s」 — 카드의 주장 · 필수 · 권장에 「%s」이 없다" % (머리, 말),
                          "같은기간": False, "같은원천": True, "점수": 3})
    return 밖


# ══ 감사 ══════════════════════════════════════════════════════════════════════════════════════════════

_순위설정 = 설정["순위주장"]
_극값식 = re.compile(_순위설정["극값"])
_합비중식 = re.compile(_순위설정["합비중"])
_없음설정 = 설정["없음주장"]
_없음주장 = re.compile(_없음설정["주장"])
_없음인용 = re.compile(_없음설정["인용"], re.I)
_접수 = re.compile(설정["공표일"]["접수꼴"])
_날짜꼴 = re.compile(r"(?:(\d{4})년\s*)?(\d{1,2})월\s*(\d{1,2})일")


class 감사기:
    def __init__(self, 회차, 장부경로=None, 공시절경로=None):
        self.회차 = 회차
        self.걸림 = []
        self.후보 = []
        self.제안 = []
        self.경계 = []
        self.확인 = {}
        self.장부, self.장부머리, self.장부경로 = {}, None, None
        p = 장부경로 or os.path.join(회차, "레터_초안.장부.json")
        if 장부경로 and not os.path.exists(장부경로):
            raise 입력문제("장부 파일이 없음 — %s" % 장부경로)
        if os.path.exists(p):
            self.장부, self.장부머리 = 장부읽기(p)
            self.장부경로 = p
        self.셈 = 셈기(회차, self.장부)
        공 = 공시절경로 or os.path.join(회차, "_raw", "공시절.json")
        self.공시절 = 공시절색인(공 if os.path.exists(공) else None)
        self._조사 = {}

    def 걸(self, 규칙, 등급, cid, 무엇, 근거=None, 제안=None, 후보=None):
        d = {"규칙": 규칙, "등급": 등급, "id": cid, "무엇": 무엇}
        if 근거 is not None:
            d["근거"] = 근거
        if 제안:
            d["제안"] = 제안
        if 후보:
            d["후보"] = 후보
        self.걸림.append(d)

    def 셈하기(self, 칸):
        self.확인[칸] = self.확인.get(칸, 0) + 1

    # ── 꼴 · F4 ───────────────────────────────────────────────────────────────
    def 꼴(self, 문서, 이름):
        오, 경, _ = K.문서검사(문서)
        for x in 오:
            cid, _, 말 = x.partition(": ")
            self.걸("꼴", "오류", cid if 말 else None, (말 or x) + " (%s)" % 이름)
        for x in 경:
            cid, _, 말 = x.partition(": ")
            self.걸("꼴", "경고", cid if 말 else None, (말 or x) + " (%s)" % 이름)

    def 인용(self, 문서):
        결 = P.인용대조(문서, self.회차)
        for x in 결["줄"]:
            판 = x["판정"]
            if 판 in ("일치", "파일만"):
                self.셈하기("인용 " + 판)
                continue
            등 = "경고" if 판 == "일치(빈칸)" else "오류"
            self.걸("F4", 등, x["id"], "%s — %s" % (판, x.get("까닭") or ""),
                   근거={"파일": x.get("파일"), "순번": x.get("순번"), "인용": _자름(x.get("인용") or "", 160)},
                   제안="원천 파일에서 인용을 다시 복사한다(기억으로 옮겨 적지 않는다)" if 판 == "불일치" else None)
        return 결

    def 숫자인용(self, c):
        """F4b — 글 원천 카드의 주장 숫자가 인용 · 계산 글 · 값에 있나."""
        원 = 원천들(c)
        if not 원 or 코드카드(c) or c.get("등급") == "일반설명":
            return
        인용글 = re.sub(r"[\s,]", "", " ".join(str(o.get("인용") or "") for o in 원)).replace("−", "-")
        계산글 = re.sub(r"[\s,]", "", " ".join(str(k.get("글") or "") for k in c.get("계산", []) or [])
                       + " ".join(str((v or {}).get(칸) or "") for v in c.get("값", []) or [] for 칸 in ("글", "본편")
                                  if (v or {}).get("장부") or c.get("계산"))).replace("−", "-")
        주장 = _날짜꼴.sub(" ", str(c.get("주장", "")))
        주장 = re.sub(r"(?:19|20)\d{2}\s*[~∼\-–]\s*(?:19|20)\d{2}\s*년?|(?:19|20)\d{2}\s*년|\d\s*분기|\d{1,2}\s*월|[1-4]Q\d{2}|Q[1-4]|\d{4}-\d{2}-\d{2}", " ", 주장)
        주장 = re.sub(r"[A-Za-z]+\d+[A-Za-z]*|\d+\s*기(?![가-힣])", " ", 주장)
        for m in re.finditer(r"(?<![\d.])\d[\d,]*(?:\.\d+)?", 주장):
            t = m.group(0).replace(",", "")
            if len(t.replace(".", "")) < 2 and "." not in t:
                continue
            if t in 인용글 or t in 계산글:
                continue
            self.걸("F4b", "경고", c.get("id"), "주장의 숫자 「%s」가 인용 · 계산에 없다 — 카드는 인용만으로 선다" % m.group(0),
                   제안="그 숫자가 든 원천 글을 인용에 더하거나, 셈한 값이면 계산 칸에 식을 적는다")

    # ── F5 · F5b ─────────────────────────────────────────────────────────────
    def 계산(self, c):
        값글 = {str((v or {}).get(칸)) for v in c.get("값", []) or [] for 칸 in ("글", "본편") if (v or {}).get(칸)}
        for k in c.get("계산", []) or []:
            if not isinstance(k, dict) or not k.get("식"):
                continue
            문제 = K.식검사(k["식"])
            이름 = k.get("이름") or k["식"][:40]
            if 문제:
                continue      # 꼴 검사(카드.문서검사)가 이미 오류로 냈다 — 같은 것을 두 번 세지 않는다
            try:
                v = self.셈.값(k["식"])
            except 셈오류 as e:
                self.걸("F5", "오류", c.get("id"), "계산 「%s」을 다시 셈하지 못함 — %s" % (이름, e), 근거={"식": _자름(k["식"], 200)})
                continue
            ok, 셈글, 파이썬 = 글맞음(v, k.get("글", ""), k.get("자리"))
            if 파이썬 is not None:
                self.경계.append({"id": c.get("id"), "이름": 이름, "식": _자름(k["식"], 160), "글": k.get("글"),
                                "ROUND_HALF_UP": 셈글, "파이썬round": 파이썬, "맞음": ok})
            if not ok:
                self.걸("F5", "오류", c.get("id"), "계산 「%s」 — 다시 셈하면 %s, 글은 「%s」(자리 %s · ROUND_HALF_UP)" % (이름, 셈글, k.get("글"), k.get("자리")),
                       근거={"식": _자름(k["식"], 200)}, 제안="원자료로 다시 셈한 값으로 글 · 값을 고친다")
            else:
                self.셈하기("계산 맞음")
            g = str(k.get("글", ""))
            if g not in ("참", "거짓") and 값글 and g not in 값글:
                self.걸("F5", "경고", c.get("id"), "계산 「%s」의 글 「%s」가 카드 값에 없다" % (이름, g), 제안="값에 그 글을 더한다(검사기 F2 가 값에 있는 숫자만 받는다)")

    def 장부대조(self, c):
        for v in c.get("값", []) or []:
            키 = (v or {}).get("장부")
            if not 키:
                continue
            if not self.장부:
                self.걸("F5b", "경고", c.get("id"), "장부가 없어 장부 키 %s 를 대 보지 못함" % 키)
                continue
            if 키 not in self.장부:
                self.걸("F5b", "오류", c.get("id"), "장부에 없는 키 %s" % 키, 제안="장부의 키를 쓰거나 「장부」 칸을 지우고 계산 칸에 식을 적는다")
                continue
            글들 = self.장부[키]["글"]
            if 글들 and str(v.get("글")) not in 글들 and str(v.get("본편")) not in 글들:
                self.걸("F5b", "오류", c.get("id"), "장부 글 불일치 %s — 카드 「%s」 · 장부 %s" % (키, v.get("글"), sorted(글들)[:3]))
            else:
                self.셈하기("장부 맞음")

    # ── F14 ───────────────────────────────────────────────────────────────────
    def 순위(self, c, 모든카드):
        주장 = str(c.get("주장", ""))
        극 = [m.group(0) for m in _극값식.finditer(주장)]
        합 = [m.group(0) for m in _합비중식.finditer(주장)]
        창 = c.get("창") or c.get("_창")
        창맞음 = self.창다시셈(c, 창) if 창 else None
        if not 극 and not 합:
            return
        if _없음주장.search(주장) and not re.search(r"\d", 주장):
            return        # 「비중을 공개하지 않는다」는 비중 주장이 아니라 「없다」 주장이다(F16 이 본다)
        계 = [k for k in c.get("계산", []) or [] if isinstance(k, dict) and k.get("식")]
        말 = " · ".join(dict.fromkeys(극 + 합))
        if 계:
            if 극:
                받침 = 창맞음 or any(re.search(r"\b(%s)\s*\(" % "|".join(_순위설정["받치는함수"]), k["식"]) or re.search(r"==|!=|<|>", k["식"]) for k in 계)
                if not 받침:
                    self.걸("F14", "경고", c.get("id"), "순위 · 극값 주장(「%s」)인데 계산이 순위를 받치지 않는다(max · min · csv_max · csv_min · 비교식이 없음)" % 말,
                           제안="창 안 모든 값을 셈한 식(min([…]) == … 꼴)을 계산 칸에 더한다 — 코드 카드(카드_계산)의 순위 카드를 쓰는 편이 낫다")
                    return
            self.셈하기("순위 주장 계산으로 받침")
            return
        원 = 원천들(c)
        글인용 = [o for o in 원 if 글원천(o.get("파일"))]
        인용글 = " ".join(정규(str(o.get("인용") or "")) for o in 원)
        인용에있음 = any(re.search(re.escape(x), 인용글) for x in 극 + 합)
        제 = self._계산카드제안(c, 모든카드)
        if 글인용 or c.get("등급") in ("평가판단", "레터정의", "보도", "검색 요약"):
            self.걸("F14", "오류", c.get("id"),
                   "셀 수 있는 순위 · 극값 · 합 · 비중 주장(「%s」)을 계산 없이 %s 카드" % (말, "글(%s)을 인용한" % 글인용[0].get("파일") if 글인용 else "「%s」 등급" % c.get("등급")),
                   근거={"인용": [_자름(o.get("인용") or "", 120) for o in (글인용 or 원)][:3]},
                   제안=("원자료로 셈한 계산 카드 %s 를 쓰고 이 카드에서 그 주장을 뺀다" % " · ".join(제)) if 제 else
                   "원자료(시세 · 장부 · 공시 표)로 다시 셈한 계산 카드로 바꾼다(카드_계산) — 글의 순위를 옮기지 않는다")
        elif not 인용에있음:
            self.걸("F14", "오류", c.get("id"), "순위 · 극값 · 합 · 비중 주장(「%s」)이 인용에도 계산에도 없다" % 말,
                   제안="원자료로 셈한 계산 칸을 더하거나 그 주장을 뺀다")
        else:
            self.걸("F14", "경고", c.get("id"), "원천의 화자가 한 순위 · 극값 주장(「%s」) — 회차 원자료로 셀 수 있으면 계산 카드로, 없으면 화자를 주장에 세운다" % 말,
                   제안="필수 한정 「귀속」 또는 「출처」(회사는 … 라고 적었다)")

    def _계산카드제안(self, c, 모든카드):
        """카드가 말하는 날짜를 창에 품는 계산 카드 id."""
        날들 = set()
        해 = str(self.평가기준일 or "")[:4]
        for s in [str(c.get("주장", ""))] + [str(x) for x in c.get("날짜", []) or []]:
            for m in _날짜꼴.finditer(s):
                날들.add("%s-%02d-%02d" % (m.group(1) or 해, int(m.group(2)), int(m.group(3))))
        밖 = []
        for d in 모든카드:
            w = d.get("창") or d.get("_창")
            if not w or d is c:
                continue
            if any(str(w.get("시작")) < x <= str(w.get("끝")) for x in 날들):
                밖.append(d.get("id"))
        return 밖

    def 창다시셈(self, c, w):
        try:
            줄 = self.셈.시세(w["파일"])
            시작, 끝 = _날글(w["시작"]), _날글(w["끝"])
        except (셈오류, KeyError) as e:
            self.걸("F14", "오류", c.get("id"), "순위 창을 다시 셈하지 못함 — %s" % e)
            return
        방향 = str(w.get("방향", ""))
        내림 = any(x in 방향 for x in ("하락", "내림", "down"))
        날들 = [(d, v / p - 1) for (pd_, p), (d, v) in zip(줄, 줄[1:]) if 시작 < d <= 끝 and p]
        if not 날들:
            self.걸("F14", "오류", c.get("id"), "순위 창 안에 거래일이 없다 — %s~%s" % (시작, 끝))
            return
        차례 = sorted(날들, key=lambda t: t[1], reverse=not 내림)
        n = int(w.get("순위수") or 3)
        자 = int(w.get("보이는자리") if w.get("보이는자리") is not None else 1)
        끝값 = 반올림(차례[min(n, len(차례)) - 1][1] * 100, 자)
        위 = [d for d, r in 차례 if (반올림(r * 100, 자) <= 끝값 if 내림 else 반올림(r * 100, 자) >= 끝값)]
        든 = list(dict.fromkeys(v.get("_날") for v in c.get("값", []) or []
                               if isinstance(v, dict) and v.get("_날") and not v.get("_꼴") and v.get("단위", "비율") == "비율"))
        if not 든:
            self.걸("F14", "경고", c.get("id"), "순위 창이 있는데 값에 날짜(_날)가 없어 견주지 못함")
            return
        첫값 = 반올림(차례[0][1] * 100, 자)
        첫무리 = {d for d, r in 차례 if 반올림(r * 100, 자) == 첫값}
        if set(든) != set(위) or 든[0] not in 첫무리:
            self.걸("F14", "오류", c.get("id"), "창 안 순위가 원자료와 다르다 — 카드 %s · 다시 셈 %s" % (든, 위),
                   근거={"창": "%s~%s %s" % (시작, 끝, 방향), "다시 셈": ["%s %s%%" % (d, 반올림(r * 100, 2)) for d, r in 차례[: max(n, len(위)) + 1]]})
            return False
        self.셈하기("창 순위 맞음")
        return True

    # ── 등급 옮김 ──────────────────────────────────────────────────────────────
    def 조사(self, 파일):
        p = 파일 if os.path.isabs(파일) else os.path.join(self.회차, 파일)
        if p not in self._조사:
            self._조사[p] = _읽기(p) if os.path.exists(p) else None
        return self._조사[p]

    def _같은숫자항목(self, 데이터, c):
        """성격이 적힌 조사 항목 가운데 카드의 % 값과 대상 낱말을 모두 가진 것 → [(자리, 성격, 확신)]."""
        수들 = []
        for v in c.get("값", []) or []:
            m = _후보수.search(str((v or {}).get("글") or "").replace("−", "-"))
            if m:
                수들.append(m.group(2))
        if not 수들:
            수들 = [m.group(2) for m in _후보수.finditer(str(c.get("주장", "")).replace("−", "-"))]
        if not 수들:
            return []
        낱들 = {t for 낱 in (대상낱말(c.get("주장", ""), 수들[0]) or []) for t in 낱}
        밖 = []

        def 걷(x, 길):
            if isinstance(x, dict):
                성 = 성격칸(x)
                if 성:
                    s = re.sub(r"\s+", "", json.dumps(x, ensure_ascii=False))
                    if all(re.search(r"(?<![\d.])%s(?![\d])" % re.escape(n), s) for n in 수들) and (not 낱들 or any(t in s for t in 낱들)):
                        밖.append((길, 성, 확신칸(x)))
                for k, v in x.items():
                    걷(v, 길 + "." + str(k))
            elif isinstance(x, list):
                for i, v in enumerate(x):
                    걷(v, 길 + "[%d]" % i)
        걷(데이터, "")
        return [(길.lstrip("."), 성, 확) for 길, 성, 확 in 밖]

    def 등급(self, c):
        등 = c.get("등급")
        세기 = 등급세기.get(등)
        원 = 원천들(c)
        조사원 = [o for o in 원 if 조사원천(o.get("파일"))]
        if 조사원:
            근거 = []
            허용 = []
            for o in 조사원:
                데 = self.조사(o["파일"])
                if 데 is None:
                    continue
                for 자리, 사전들 in _조사항목(데, o.get("인용") or ""):
                    성, 확 = None, None
                    for d in 사전들:
                        성, 확 = 성격칸(d), 확신칸(d)
                        if 성 or 확:
                            break
                    if 성:
                        g = 성격등급(성, 확)
                        근거.append({"자리": 자리, "출처_성격": 성, "확신도": 확, "옮긴 등급": g, "어떻게": "인용이 든 항목"})
                        if g:
                            허용.append(g)
                        else:
                            self.걸("등급", "경고", c.get("id"), "조사 항목 %s 의 출처 성격 「%s」를 등급으로 옮기지 못함" % (자리, 성))
                    else:
                        같 = self._같은숫자항목(데, c)
                        if 같:
                            for 자2, 성2, 확2 in 같:
                                g = 성격등급(성2, 확2)
                                근거.append({"자리": 자2, "출처_성격": 성2, "확신도": 확2, "옮긴 등급": g,
                                           "어떻게": "인용이 든 항목(%s)에 성격이 없어 같은 숫자 · 대상 낱말의 항목에서" % 자리})
                                if g:
                                    허용.append(g)
                        else:
                            근거.append({"자리": 자리, "출처_성격": None, "확신도": None, "옮긴 등급": None, "어떻게": "성격 없음"})
                            self.걸("등급", "경고", c.get("id"), "조사 항목 %s 에 출처 성격 · 확신도가 없다 — 등급을 옮길 수 없다" % 자리,
                                   제안="조사 산출의 그 항목에 출처_성격 · 확신도를 적거나, 같은 사실의 성격이 적힌 항목을 인용한다")
            if 허용:
                최약 = min(허용, key=lambda g: 등급세기.get(g, 0))
                if 세기 is not None:
                    if 세기 > 등급세기.get(최약, 0):
                        self.걸("등급", "오류", c.get("id"), "카드 등급 「%s」가 원천 기록의 등급 「%s」보다 세다" % (등, 최약), 근거=근거,
                               제안="등급을 「%s」로%s" % (최약, "" if K.등급표.get(최약, {}).get("3분", True) else " · 층제한 [\"3분\"]"))
                    else:
                        self.셈하기("등급 옮김 맞음")
                        if any(str(x.get("확신도") or "")[:1] in 설정["성격옮김"]["확신도경고"] and 세기 >= 설정["성격옮김"]["확신도경고"][str(x.get("확신도"))[:1]] for x in 근거):
                            self.걸("등급", "경고", c.get("id"), "원천 기록의 확신도가 「중」인데 카드 등급이 「%s」" % 등, 근거=근거)
                elif 등 == "계산":
                    if not K.등급표.get(최약, {}).get("3분", True) and "3분" not in (c.get("층제한") or []):
                        self.걸("등급", "오류", c.get("id"), "계산 카드의 원자료 등급이 「%s」 — 3분 레터에 못 쓰는데 층제한이 없다" % 최약, 근거=근거,
                               제안="층제한 [\"3분\"]")
                    else:
                        self.셈하기("등급 옮김 맞음")
            return
        # 원천이 글(레터)인 카드 — 같은 숫자가 조사 산출에 낮은 성격으로 있나(후보)
        if 세기 is None or not any(글원천(o.get("파일")) for o in 원):
            return
        조사파일 = sorted(glob.glob(os.path.join(self.회차, "_raw", "매출스트림*.json")))
        for p in 조사파일[:1]:
            데 = self.조사(p)
            if not 데:
                continue
            for 자리, 성, 확 in self._같은숫자항목(데, c)[:3]:
                g = 성격등급(성, 확)
                if g and 등급세기.get(g, 0) < 세기:
                    self.후보.append({"id": c.get("id"), "종류": "원천 등급", "값": "", "대상": "",
                                    "다른값": "", "파일": _rel(p, self.회차), "줄": 자리,
                                    "글": "카드는 글(레터)을 인용해 「%s」인데 같은 숫자가 조사 산출 %s 에 「%s · 확신도 %s」(→ %s)로 있다 — 레터의 원천 등급을 카드에 옮겼나" % (등, 자리, 성, 확, g),
                                    "같은기간": False, "같은원천": False, "점수": 3})

    # ── 공표일 ─────────────────────────────────────────────────────────────────
    def 공표일(self, c):
        날들 = {}
        for o in 원천들(c):
            for m in _접수.finditer(str(o.get("파일") or "")):
                y = m.group(1)
                try:
                    날 = _dt.date(int(y[:4]), int(y[4:6]), int(y[6:8])).isoformat()
                except ValueError:
                    continue
                날들[날] = m.group(0)
        if not 날들:
            return
        첫 = min(날들)
        까닭 = "원천 경로의 접수번호 %s 앞 여덟 자리" % 날들[첫] + (" · 접수일이 여럿(%s) — 가장 이른 날" % " · ".join(sorted(날들)) if len(날들) > 1 else "")
        뒤 = bool(self.평가기준일) and 첫 > str(self.평가기준일)
        if not c.get("공표일"):
            self.제안.append({"id": c.get("id"), "칸": "공표일", "제안": 첫, "까닭": 까닭, "평가기준일뒤": 뒤})
        elif str(c.get("공표일")) != 첫 and str(c.get("공표일")) not in 날들:
            self.걸("공표일", "경고", c.get("id"), "카드 공표일 %s 가 원천 접수일 %s 와 다르다" % (c.get("공표일"), 첫), 제안="공표일 %s (%s)" % (첫, 까닭))
        else:
            self.셈하기("공표일 접수번호와 같음")

    # ── F16 ───────────────────────────────────────────────────────────────────
    def 없음(self, 카드들, 없음문서들):
        아이디 = {c.get("id") for c in 카드들}
        대신 = {}
        for 경로, d in 없음문서들:
            이름 = os.path.basename(경로)
            if not str(d.get("형식", "")).endswith("없음 1"):
                self.걸("F16", "경고", None, "「없음」 문서 꼴이 아님(형식 「… 없음 1」) — %s" % 이름)
            if self.평가기준일 and d.get("평가기준일") and d.get("평가기준일") != self.평가기준일:
                self.걸("F16", "경고", None, "「없음」 문서의 평가기준일 %s 가 카드와 다르다 — %s" % (d.get("평가기준일"), 이름))
            for i, x in enumerate(d.get("없음") or []):
                if not isinstance(x, dict):
                    self.걸("F16", "경고", None, "「없음」 항목이 사전이 아님 — %s[%d]" % (이름, i))
                    continue
                머 = "%s「%s」" % (이름, x.get("항목") or "[%d]" % i)
                빠짐 = [k for k in _없음설정["반드시"] if not x.get(k)]
                찾은 = next((x.get(k) for k in _없음설정["찾은칸"] if x.get(k)), None)
                if not 찾은:
                    빠짐.insert(0, "찾은블록(또는 찾은곳)")
                if 빠짐:
                    self.걸("F16", "경고", None, "「없음」 %s 에 %s 이 없다 — 안 본 것과 보고 없던 것을 가를 수 없다" % (머, " · ".join(빠짐)))
                else:
                    self.셈하기("없음 기록 갖춤")
                if 찾은 and self.공시절.번호:
                    for 블 in 찾은 if isinstance(찾은, list) else [찾은]:
                        m = re.match(r"\s*(\d+-\d+)", str(블))
                        if m and m.group(1) not in self.공시절.번호:
                            self.걸("F16", "경고", None, "「없음」 %s 의 찾은블록 %s 이 공시절에 없다" % (머, m.group(1)))
                for cid in x.get("대신_지은카드") or []:
                    대신.setdefault(cid, []).append(x.get("항목"))
                    if cid not in 아이디:
                        self.걸("F16", "경고", None, "「없음」 %s 의 대신_지은카드 %s 가 카드에 없다" % (머, cid))
        for c in 카드들:
            주 = str(c.get("주장", ""))
            if not _없음주장.search(주) or 코드카드(c):
                continue
            원인용 = [o for o in 원천들(c) if not 글원천(o.get("파일")) and _없음인용.search(str(o.get("인용") or ""))]
            if 원인용 or c.get("id") in 대신:
                self.셈하기("「없다」 주장 기록 있음")
                continue
            글인용 = [o for o in 원천들(c) if 글원천(o.get("파일")) and _없음인용.search(str(o.get("인용") or ""))]
            self.걸("F16", "경고", c.get("id"),
                   "「없다 · 공개하지 않는다」 주장에 검색 기록이 없다" + (" — 글(%s)의 「없다」를 옮겼다" % 글인용[0].get("파일") if 글인용 else ""),
                   제안="원천(공시 · 조사 산출)에서 찾은 칸 · 검색어 · 결과를 「없음」 문서에 적고 대신_지은카드에 이 카드를 넣는다 — 또는 원천이 스스로 없음을 말한 문장을 인용한다")

    # ── 묶음용 문맥 ────────────────────────────────────────────────────────────
    def 문맥(self, c, 문맥표):
        """카드 원천마다 문맥 id(묶음의 「원천 문단」) · 나온 횟수 · 블록. 문맥표 = {키: {"id", "머리", "글"}}."""
        묶 = 설정["묶음"]
        밖 = []
        for o in 원천들(c):
            파일 = o.get("파일")
            인 = o.get("인용") or ""
            줄 = {"파일": 파일, "자리": o.get("자리"), "인용": 인, "문맥": [], "횟수": None}
            if not 파일 or 자료원천(파일) or not 인:
                줄["문맥"] = []
                줄["원자료"] = bool(파일 and 자료원천(파일))
                밖.append(줄)
                continue
            p = 파일 if os.path.isabs(파일) else os.path.join(self.회차, 파일)
            if not os.path.exists(p):
                밖.append(줄)
                continue
            블록들 = self.공시절.찾기(파일, 인, 묶["인용당자리"], o.get("자리")) if p.lower().endswith((".txt", ".xml", ".htm", ".html")) else []
            if 블록들:
                줄["횟수"] = len(블록들)
                for b, 글 in 블록들:
                    키 = ("블록", b.get("번호"))
                    if 키 not in 문맥표:
                        문맥표[키] = {"id": "S%03d" % (len(문맥표) + 1), "머리": "%s · 공시절 %s · %s" % (파일, b.get("번호"), " > ".join(b.get("제목경로") or [b.get("제목") or ""])),
                                    "글": 글, "자리들": [], "상한": 묶["블록상한"], "블록": b}
                    문맥표[키]["자리들"] += 인용자리(문맥표[키]["글"], 인)
                    줄["문맥"].append(문맥표[키]["id"])
                    # 같은 절의 윗 블록 · 아래 블록 — 반대 진술 · 조건이 이웃 블록에 있는 일이 잦다(경기변동 절과 그 아래 [제품] 블록)
                    for 이웃, 관계 in self.공시절.이웃(b, 묶["이웃상한"]):
                        k2 = ("블록", 이웃.get("번호"))
                        if k2 not in 문맥표:
                            문맥표[k2] = {"id": "S%03d" % (len(문맥표) + 1), "머리": "%s · 공시절 %s · %s · 같은 절의 %s" % (
                                파일, 이웃.get("번호"), " > ".join(이웃.get("제목경로") or [이웃.get("제목") or ""]), 관계),
                                "글": 정규(" ".join(이웃.get("글", []) or [])), "자리들": [], "상한": 묶["이웃글상한"], "블록": 이웃}
                        if 문맥표[k2]["id"] not in 줄.setdefault("이웃", []):
                            줄["이웃"].append(문맥표[k2]["id"])
                밖.append(줄)
                continue
            if 조사원천(파일):
                데 = self.조사(파일)
                항목들 = _조사항목(데, 인) if 데 else []
                줄["횟수"] = len(항목들)
                for 자리, 사전들 in 항목들[: 묶["인용당자리"]]:
                    d = next((x for x in 사전들 if 성격칸(x) or 확신칸(x)), 사전들[0] if 사전들 else {})
                    키 = ("조사", 파일, json.dumps(d, ensure_ascii=False, sort_keys=True)[:200])
                    if 키 not in 문맥표:
                        문맥표[키] = {"id": "S%03d" % (len(문맥표) + 1), "머리": "%s · %s" % (파일, 자리), "글": json.dumps(d, ensure_ascii=False),
                                    "자리들": [], "상한": 묶["항목상한"]}
                    줄["문맥"].append(문맥표[키]["id"])
                밖.append(줄)
                continue
            글 = 원천원글(p)
            자리들 = 인용자리(글, 인, 묶["인용당자리"])
            줄["횟수"] = len(자리들)
            for s, e in 자리들:
                # 문단 = 빈 줄 사이 · 길면 그 줄 · 표(「|」 줄)면 그 표의 머리 두 줄을 함께
                a = 글.rfind("\n\n", 0, s)
                b = 글.find("\n\n", e)
                a = 0 if a < 0 else a + 2
                b = len(글) if b < 0 else b
                머리줄 = ""
                if 글[a:b].lstrip().startswith("|"):
                    머리줄 = " / ".join(x.strip() for x in 글[a:b].split("\n")[:2] if x.strip())
                if b - a > 묶["문단창"] * 3:
                    a2 = 글.rfind("\n", 0, s)
                    b2 = 글.find("\n", e)
                    a, b = (0 if a2 < 0 else a2 + 1), (len(글) if b2 < 0 else b2)
                키 = ("글", 파일, a)
                if 키 not in 문맥표:
                    문맥표[키] = {"id": "S%03d" % (len(문맥표) + 1), "머리": "%s · %d줄" % (파일, 글.count("\n", 0, a) + 1) + (" · 표 머리 %s" % _자름(머리줄, 200) if 머리줄 else ""),
                                "글": 글[a:b], "자리들": [], "상한": 묶["블록상한"]}
                문맥표[키]["자리들"].append((s - a, e - a))
                줄["문맥"].append(문맥표[키]["id"])
            밖.append(줄)
        return 밖

    # ── 한 판 ─────────────────────────────────────────────────────────────────
    def 돌리기(self, 문서들, 없음문서들, 후보끔=False):
        첫 = 문서들[0][1]
        self.회사, self.평가기준일, self.재무기준일 = 첫.get("회사"), 첫.get("평가기준일"), 첫.get("재무기준일")
        카드들, 출처 = [], {}
        for 경로, d in 문서들:
            for k in ("평가기준일", "재무기준일"):
                if d.get(k) != 첫.get(k):
                    self.걸("꼴", "오류", None, "카드 문서의 %s 가 다르다 — %s 「%s」 · 첫 문서 「%s」" % (k, os.path.basename(경로), d.get(k), 첫.get(k)))
            self.꼴(d, os.path.basename(경로))
            self.인용(d)
            for c in d.get("카드", []) or []:
                if not isinstance(c, dict):
                    continue
                if c.get("id") in 출처:
                    self.걸("꼴", "오류", c.get("id"), "id 겹침 — %s · %s" % (출처[c.get("id")], os.path.basename(경로)))
                출처[c.get("id")] = os.path.basename(경로)
                카드들.append(c)
        더미 = 글더미(self.회차)
        if not 후보끔:
            for 꼴 in 후보설정["레터꼴"]:
                for p in sorted(glob.glob(os.path.join(self.회차, 꼴))):
                    if not re.search(후보설정["레터뺌"], os.path.basename(p)):
                        더미.넣기(p)
        for c in 카드들:
            self.숫자인용(c)
            self.계산(c)
            self.장부대조(c)
            self.순위(c, 카드들)
            self.등급(c)
            self.공표일(c)
            if not 후보끔 and not 코드카드(c):
                원파일 = set()
                for o in 원천들(c):
                    if o.get("파일") and not 자료원천(o.get("파일")):
                        더미.넣기(o["파일"])
                        원파일.add(_rel(o["파일"] if os.path.isabs(o["파일"]) else os.path.join(self.회차, o["파일"]), self.회차))
                self.후보 += 후보찾기(c, 더미, 원파일)
                블록들 = [b for o in 원천들(c) if o.get("인용") for b, _g in self.공시절.찾기(o.get("파일"), o.get("인용"), 3, o.get("자리"))]
                self.후보 += 기준후보(c, 블록들)
        self.없음(카드들, 없음문서들)
        self.후보 = self.후보[: 후보설정["전체상한"]]
        for i, x in enumerate(self.후보, 1):
            x["번호"] = "C%03d" % i
            self.걸("후보", "후보", x["id"], "%s — %s%s" % (x["종류"], (x["대상"] + " 곁의 " + x["다른값"] + " (카드 " + x["값"] + ")") if x["다른값"] else x["글"][:120],
                                                       " · %s %s" % (x["파일"], x["줄"]) if x["다른값"] else ""), 후보=x["번호"])
        return 카드들


# ══ 산출 ══════════════════════════════════════════════════════════════════════════════════════════════

def 셈표(걸림):
    표 = {}
    for x in 걸림:
        표.setdefault(x["규칙"], {}).setdefault(x["등급"], 0)
        표[x["규칙"]][x["등급"]] += 1
    return 표


def 요약글(결):
    셈 = 결["셈"]
    줄 = ["# 카드 감사 — %s · 평가기준일 %s" % (결.get("회사"), 결.get("평가기준일")), "",
         "- 카드 %d장 · 인용 %d건 · 계산 %d건 · 장부 키 %d건 · 카드 문서 %s" % (셈["카드"], 셈["인용"], 셈["계산"], 셈["장부키"], " · ".join(결["카드문서"])),
         "- **오류 %d · 경고 %d · 후보 %d** — %s" % (셈["오류"], 셈["경고"], 셈["후보"], "통과(오류 0)" if 결["통과"] else "오류가 있다(카드를 고쳐 다시 돌린다)"),
         "- 장부: %s" % ("%s (판 %s · %s)" % (결["장부"]["파일"], 결["장부"].get("판"), 결["장부"].get("일시")) if 결.get("장부") else "없음 — F5b 를 보지 못함"),
         "- 공시절: %s · 「없음」 문서: %s" % (결.get("공시절") or "없음", " · ".join(결.get("없음문서") or []) or "없음"),
         "- 확인함: " + " · ".join("%s %d" % kv for kv in sorted(결["확인함"].items())), "",
         "| 규칙 | 오류 | 경고 | 후보 |", "|---|---:|---:|---:|"]
    for 규 in sorted(셈["규칙별"]):
        v = 셈["규칙별"][규]
        줄.append("| %s | %d | %d | %d |" % (규, v.get("오류", 0), v.get("경고", 0), v.get("후보", 0)))
    for 등 in ("오류", "경고"):
        목 = [x for x in 결["걸림"] if x["등급"] == 등]
        if not 목:
            continue
        줄 += ["", "## %s %d" % (등, len(목)), ""]
        for x in 목[:200]:
            줄.append("- [%s] %s — %s%s" % (x["규칙"], x.get("id") or "문서", x["무엇"], ("  → 제안: " + x["제안"]) if x.get("제안") else ""))
        if len(목) > 200:
            줄.append("- … %d건 더(JSON 「걸림」)" % (len(목) - 200))
    if 결["제안"]:
        줄 += ["", "## 제안 %d (카드 문서는 고치지 않았다)" % len(결["제안"]), ""]
        for x in 결["제안"]:
            줄.append("- %s · %s = %s — %s%s" % (x["id"], x["칸"], x["제안"], x["까닭"], " · 평가기준일 뒤" if x.get("평가기준일뒤") else ""))
    if 결["후보"]:
        줄 += ["", "## 후보 %d (판정은 V5 — `.claude/갈래/V5_카드감사.md`)" % len(결["후보"]), ""]
        for x in 결["후보"][:80]:
            줄.append("- %s %s · %s — %s%s" % (x["번호"], x["id"], x["종류"], ("「%s」 곁 %s (카드 %s) · %s %s · " % (x["대상"], x["다른값"], x["값"], x["파일"], x["줄"])) if x["다른값"] else "", x["글"][:200]))
    if 결["반올림경계"]:
        줄 += ["", "## 반올림 경계 %d — 파이썬 round 와 ROUND_HALF_UP 이 갈리는 계산(이 감사는 ROUND_HALF_UP)" % len(결["반올림경계"]), ""]
        for x in 결["반올림경계"][:40]:
            줄.append("- %s 「%s」 %s → 글 %s · ROUND_HALF_UP %s · 파이썬 round %s" % (x["id"], x["이름"], x["식"][:60], x["글"], x["ROUND_HALF_UP"], x["파이썬round"]))
    return "\n".join(줄) + "\n"


def 묶음글(결, 기, 카드들, 문서들, 없음문서들):
    """V5 가 한 번에 읽는 묶음 — 카드 · 코드 감사 · 후보 · 원천 문단(중복 없이)."""
    묶 = 설정["묶음"]
    문맥표 = {}
    카드문맥 = {c.get("id"): 기.문맥(c, 문맥표) for c in 카드들}
    걸림 = {}
    for x in 결["걸림"]:
        걸림.setdefault(x.get("id"), []).append(x)
    후보 = {}
    for x in 결["후보"]:
        후보.setdefault(x["id"], []).append(x)
    상한 = 묶["줄상한"]

    def 줄나눔(s):
        s = str(s)
        if len(s) <= 상한:
            return [s]
        밖, 남 = [], s
        while len(남) > 상한:
            i = 남.rfind(" ", 0, 상한)
            i = 상한 if i < 상한 // 2 else i
            밖.append(남[:i])
            남 = "    " + 남[i:].lstrip()
        return 밖 + [남]

    줄 = ["# 카드 감사 묶음 — V5 입력 · %s · 평가기준일 %s · 재무기준일 %s" % (결.get("회사"), 결.get("평가기준일"), 결.get("재무기준일")), "",
         "- 만든 곳: 스크립트/카드감사.py (%s) · 카드 %d장 · 원천 문단 %d개 · 후보 %d개 · 코드 오류 %d · 경고 %d" % (
             결["만든날"], len(카드들), len(문맥표), len(결["후보"]), 결["셈"]["오류"], 결["셈"]["경고"]),
         "- 카드 문서: " + " · ".join(결["카드문서"]),
         "- 읽는 법: 카드마다 〔카드〕 · 〔코드〕(이 파일이 이미 잡은 것 — 다시 판정하지 않는다) · 〔원천〕(인용 → 원천 문단 id) · 〔후보〕(V5 가 판정할 것). "
         "원천 문단은 맨 뒤 「원천 문단」 절에 한 번씩만 싣는다(«» 안이 원천 글자 그대로 · 공백만 정규화 · … 는 줄인 자리). "
         "〔원천〕 끝의 「(같은 절 S…)」 는 인용이 든 공시 블록의 윗 · 아래 블록이다(반대 진술 · 조건이 이웃 블록에 있는 일이 잦다). "
         "〔원자료〕 는 시세 · 장부 · 재무 JSON 이라 문단이 없다 — 코드가 다시 셈했다", ""]
    for _경로, d in 문서들:
        for x in d.get("함정_메모") or []:
            줄 += 줄나눔("- 함정 메모(%s): %s" % (os.path.basename(_경로), 정규(str(x))))
    for 경로, d in 없음문서들:
        for x in d.get("없음") or []:
            if isinstance(x, dict):
                줄 += 줄나눔("- 「없음」(%s): %s — %s · 대신 %s" % (os.path.basename(경로), x.get("항목"), 정규(str(x.get("결과") or "")), " ".join(x.get("대신_지은카드") or [])))
    줄 += ["", "## 카드", ""]
    for c in 카드들:
        cid = c.get("id")
        머 = "### %s · %s" % (cid, c.get("등급"))
        for k in ("공표일", "사건일", "기간"):
            if c.get(k):
                머 += " · %s %s" % (k, c[k])
        if c.get("층제한"):
            머 += " · 층제한 %s" % "/".join(c["층제한"])
        if 코드카드(c):
            머 += " · 코드 카드"
        줄 += [머]
        줄 += 줄나눔("주장: " + 정규(str(c.get("주장", ""))))
        값 = [str(v.get("글")) + ("(본편 %s)" % v["본편"] if v.get("본편") else "") + ("[장부]" if v.get("장부") else "")
             for v in c.get("값", []) or [] if isinstance(v, dict) and v.get("글") and not v.get("_꼴")]
        if 값:
            n = 12 if 코드카드(c) else 40
            줄 += 줄나눔("값: " + " · ".join(값[:n]) + (" … 모두 %d" % len(값) if len(값) > n else ""))
        for 칸 in ("필수", "권장"):
            f = ["%s /%s/" % (x.get("종류"), x.get("정규식")) for x in c.get(칸, []) or [] if isinstance(x, dict)]
            if f:
                줄 += 줄나눔("%s: %s" % (칸, " · ".join(f)))
        for 칸 in ("함정", "고유명사"):
            if c.get(칸):
                v = c[칸]
                v = [("%s(%s)" % (x.get("이름"), x.get("소개")) if isinstance(x, dict) else str(x)) for x in v]
                줄 += 줄나눔("%s: %s" % (칸, " / ".join(정규(x) for x in v)))
        if c.get("계산") and not 코드카드(c):
            줄 += 줄나눔("계산: " + " · ".join("%s = %s" % (_자름(k.get("식", ""), 80), k.get("글")) for k in c["계산"][:8] if isinstance(k, dict)))
        for x in 걸림.get(cid, []):
            if x["등급"] != "후보":
                근 = ""
                if x["규칙"] == "등급" and isinstance(x.get("근거"), list):
                    근 = " · 근거 " + " / ".join("%s「%s · 확신도 %s」%s" % (g.get("자리"), g.get("출처_성격"), g.get("확신도"), "(같은 숫자의 항목)" if "성격이 없어" in str(g.get("어떻게")) else "")
                                              for g in x["근거"][:4])
                줄 += 줄나눔("〔코드 %s %s〕 %s%s" % (x["등급"], x["규칙"], x["무엇"], 근))
        원자료 = [o for o in 카드문맥.get(cid, []) if o.get("원자료")]
        if 원자료:
            파일셈 = {}
            for o in 원자료:
                파일셈[o["파일"]] = 파일셈.get(o["파일"], 0) + 1
            줄 += 줄나눔("〔원자료〕 " + " · ".join("%s %d건" % kv for kv in 파일셈.items()) + " — 코드가 다시 셈했다(F5)")
        for o in 카드문맥.get(cid, []):
            if o.get("원자료"):
                continue
            횟 = "" if o.get("횟수") in (None, 1) else " · 원천에 %s번" % o.get("횟수")
            줄 += 줄나눔("〔원천〕 %s%s%s — «%s» → %s%s" % (o["파일"], (" · " + str(o["자리"])) if o.get("자리") else "", 횟,
                                                   _자름(o.get("인용") or "", 300), " · ".join(o["문맥"]) or "문맥 못 찾음",
                                                   (" (같은 절 %s)" % " · ".join(o["이웃"])) if o.get("이웃") else ""))
        for x in 후보.get(cid, []):
            if x["다른값"]:
                줄 += 줄나눔("〔후보 %s〕 %s — 「%s」 곁 %s (카드 %s) · %s %s%s%s — «%s»" % (
                    x["번호"], x["종류"], x["대상"], x["다른값"], x["값"], x["파일"], x["줄"], " · 같은 기간 말" if x["같은기간"] else "",
                    " · 다른 자리 %d" % len(x["다른곳"]) if x.get("다른곳") else "", x.get("문단") or x["글"]))
            else:
                줄 += 줄나눔("〔후보 %s〕 %s — %s · %s %s" % (x["번호"], x["종류"], x["글"], x["파일"], x["줄"]))
        줄.append("")
    줄 += ["## 원천 문단", ""]
    for _k, s in sorted(문맥표.items(), key=lambda kv: kv[1]["id"]):
        줄 += 줄나눔("[%s] %s" % (s["id"], s["머리"]))
        글 = s["글"]
        본문 = _자름(글, s["상한"]) if len(정규(글)) <= s["상한"] else _창글(글, s["자리들"], 묶["문단창"], s["상한"])
        줄 += 줄나눔("«%s»" % 본문)
        줄.append("")
    return "\n".join(줄) + "\n"


def 감사(카드경로들, 회차, 장부경로=None, 없음경로들=None, 공시절경로=None, 후보끔=False):
    """카드 문서들을 감사 → (결과, 감사기, 카드들, 문서들, 없음문서들)."""
    if not os.path.isdir(회차):
        raise 입력문제("회차 폴더가 없음 — %s" % 회차)
    문서들 = []
    for p in 카드경로들:
        if not os.path.exists(p):
            raise 입력문제("카드 파일이 없음 — %s" % p)
        d = _읽기(p)
        if not isinstance(d, dict) or not isinstance(d.get("카드"), list):
            raise 입력문제("카드 문서 꼴이 아님(「카드」 목록이 없음) — %s" % p)
        문서들.append((p, d))
    if not 문서들:
        raise 입력문제("감사할 카드 문서가 없음")
    없음목 = list(없음경로들 or [])
    if 없음경로들 is None:
        후보들 = glob.glob(os.path.join(회차, "_raw", "카드", "*_없음.json"))
        for p, _d in 문서들:
            후보들 += glob.glob(os.path.join(os.path.dirname(os.path.abspath(p)), "*_없음.json"))
        없음목 = sorted({os.path.abspath(x) for x in 후보들})
    없음문서들 = []
    for p in 없음목:
        if not os.path.exists(p):
            raise 입력문제("「없음」 파일이 없음 — %s" % p)
        없음문서들.append((p, _읽기(p)))
    기 = 감사기(회차, 장부경로, 공시절경로)
    카드들 = 기.돌리기(문서들, 없음문서들, 후보끔)
    인용수 = sum(len(원천들(c)) for c in 카드들)
    계산수 = sum(len(c.get("계산", []) or []) for c in 카드들)
    장부키 = sum(1 for c in 카드들 for v in c.get("값", []) or [] if isinstance(v, dict) and v.get("장부"))
    셈 = {"카드": len(카드들), "인용": 인용수, "계산": 계산수, "장부키": 장부키,
          "오류": sum(1 for x in 기.걸림 if x["등급"] == "오류"), "경고": sum(1 for x in 기.걸림 if x["등급"] == "경고"),
          "후보": len(기.후보), "규칙별": 셈표(기.걸림)}
    결 = {"형식": 형식, "만든날": _dt.datetime.now().isoformat(timespec="seconds"), "도구": "스크립트/카드감사.py",
         "회사": 기.회사, "평가기준일": 기.평가기준일, "재무기준일": 기.재무기준일, "회차": 회차.replace("\\", "/"),
         "카드문서": [_rel(os.path.abspath(p), 회차) if os.path.abspath(p).startswith(os.path.abspath(회차)) else os.path.abspath(p).replace("\\", "/") for p, _ in 문서들],
         "없음문서": [os.path.abspath(p).replace("\\", "/") for p, _ in 없음문서들],
         "장부": dict(기.장부머리 or {}, 파일=기.장부경로.replace("\\", "/")) if 기.장부경로 else None,
         "공시절": 기.공시절.경로.replace("\\", "/") if 기.공시절.경로 else None,
         "셈": 셈, "통과": 셈["오류"] == 0, "걸림": 기.걸림, "후보": 기.후보, "제안": 기.제안, "반올림경계": 기.경계, "확인함": 기.확인}
    return 결, 기, 카드들, 문서들, 없음문서들


def 기본카드(회차):
    p = os.path.join(회차, "_raw", "사실카드.json")
    if os.path.exists(p):
        return [p]
    return [x for x in sorted(glob.glob(os.path.join(회차, "_raw", "카드", "*.json")))
            if not re.search(r"_없음\.json$|_인용대조\.json$", x)]


def main(argv=None):
    ap = argparse.ArgumentParser(description="사실 카드 감사 — 인용 · 계산 · 장부 · 순위 · 「없음」 · 등급 · 공표일 · 후보(B4)")
    ap.add_argument("카드", nargs="*", help="카드 문서(여럿 · 없으면 회차 _raw/사실카드.json 또는 _raw/카드/*.json)")
    ap.add_argument("--회차", default=os.path.dirname(여기), help="카드 원천 경로의 기준 폴더(기본: 이 스크립트 폴더의 부모)")
    ap.add_argument("--낼", default=None, help="감사 JSON(기본 <회차>/_raw/카드감사.json · 요약은 같은 이름 .md)")
    ap.add_argument("--장부", default=None, help="장부 파일(기본 <회차>/레터_초안.장부.json)")
    ap.add_argument("--없음", action="append", default=None, help="「없음」 문서(여러 번 · 기본 _raw/카드/*_없음.json 과 카드 문서 곁의 *_없음.json)")
    ap.add_argument("--공시절", default=None, help="공시절.json(기본 <회차>/_raw/공시절.json)")
    ap.add_argument("--묶음", default=None, help="V5 묶음 경로(기본 <낼 폴더>/카드감사_V5묶음.md)")
    ap.add_argument("--묶음없이", action="store_true")
    ap.add_argument("--후보없이", action="store_true", help="같은 대상 후보 찾기를 끈다(빠르게)")
    a = ap.parse_args(argv)
    회차 = os.path.abspath(a.회차)
    try:
        카드경로 = a.카드 or 기본카드(회차)
        결, 기, 카드들, 문서들, 없음문서들 = 감사(카드경로, 회차, a.장부, a.없음, a.공시절, a.후보없이)
    except 입력문제 as e:
        print("입력 오류 — %s" % e)
        return 입력오류
    낼 = a.낼 or os.path.join(회차, "_raw", "카드감사.json")
    os.makedirs(os.path.dirname(os.path.abspath(낼)), exist_ok=True)
    if not a.묶음없이:
        묶 = a.묶음 or os.path.join(os.path.dirname(os.path.abspath(낼)), "카드감사_V5묶음.md")
        글 = 묶음글(결, 기, 카드들, 문서들, 없음문서들)
        io.open(묶, "w", encoding="utf-8").write(글)
        결["묶음"] = {"파일": 묶.replace("\\", "/"), "글자": len(글), "줄": 글.count("\n")}
    io.open(낼, "w", encoding="utf-8").write(json.dumps(결, ensure_ascii=False, indent=1))
    io.open(os.path.splitext(낼)[0] + ".md", "w", encoding="utf-8").write(요약글(결))
    셈 = 결["셈"]
    print("카드 감사 — 카드 %d장 · 인용 %d · 계산 %d · 장부 키 %d → 오류 %d · 경고 %d · 후보 %d" % (
        셈["카드"], 셈["인용"], 셈["계산"], 셈["장부키"], 셈["오류"], 셈["경고"], 셈["후보"]))
    for x in 결["걸림"]:
        if x["등급"] == "오류":
            print("  오류 [%s] %s — %s" % (x["규칙"], x.get("id") or "문서", x["무엇"][:160]))
    print("→ %s" % 낼)
    if 결.get("묶음"):
        print("→ %s (%d자)" % (결["묶음"]["파일"], 결["묶음"]["글자"]))
    return 통과 if 결["통과"] else 발견


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""문체검사 — 레터 초안의 결정형 문체 검사(LLM 없음 · 레터 문체 3단계 B6 · 2026-10-26).

왜 있나
    레터 문장이 원천과 뜻이 어긋나지 않게, 사실은 문장 밖 사실 카드(`카드.py`)에 먼저 적고 작가(LLM)는 문장마다 카드 꼬리표
    `[p04,k21]` 를 단다. 이 검사기는 LLM 없이 문장과 꼬리표 카드를 맞대고, 셀 수 있는 문체 규칙을 잰다.
    원칙 — 규칙은 검사기에, 견본은 작가에게(연구/레터_문체체계_독립설계안_20261026.md 3-4). 규칙의 정본은
    연구/문체3단계_20261026/검사기규칙_v0.md 이고, 정규식 · 문턱 · 스위치 · 참조는 `문체검사규칙.json` 에 있다(코드에 박지 않는다).
    출발점은 독립 설계 실험의 검증기(F1~F10 · H1~H16)다. 같은 입력 · 같은 규칙판이면 같은 결과를 낸다(`_문체검사시험.py` 가 맞댄다).

검사
    사실 층  F0 카드 꼴(카드.문서검사) · F1 꼬리표 · F2 숫자 · 날짜 ⊂ 꼬리표 카드 · F3 필수 · 권장 한정 · F4 인용 실재(공시절.인용대조)
             F5 계산 재현(정확한 분수 · ROUND_HALF_UP) · F5b 장부 대조 · F6 원천 등급과 문장 꼴 · F7 고유명사 소개 · F8 용어 첫 등장 풀이
             F9 결론 용어 · F10 그 층에 쓰지 않는 카드(층제한 · 등급 바닥) · F11 평가기준일 뒤 · 예정 · F12 지수를 % 로
             F13 3분 레터 회사 소개에 주당가치 · 시나리오 값 · F16 「없다」 문장의 검색 기록(경고)
    문장 층  H1 끝맺음 · ~죠 · H2 길이 · H3 숫자 수(증감 묶음은 하나) · H4 「·」 나열 · H5 괄호 · H6 연산 기호 · H7 금칙 · 권유
             H8 내부어 · 가정 이름 · H9 글 구조 안내 · 물음 · H10 추상 주어(면책 고정문 예외) · H11 같은 날짜 · H12 대체어 · H13 「입니다」 연속
             H14 대구 · H15 문단 문장 수(코드 고정 블록 예외) · H16 복제 · H17 고정문 승인 문형 · H18 「값」 홀로 · H19 「N 가지입니다」
             H20 금액 정밀도 · H21 「약」 · H22 단위 섞임 · %p · H23 시나리오 순서 · A~B · H24 날짜 이름 꼴 · H25 병기 순서(스위치)
             H26 병기 두 번 · H27 한 개념 두 이름 · H28 상호 · H29 동작 예고 · 연결 문장 · H30 맞춤법 · H31 1단계 정규식 패턴(정밀도를 잰 것)
             H32 같은 서술어 · H33 3분 레터 풀이 수
    넣지 않은 것 — F14(순위 · 최고 · 합 주장을 원자료로 다시 셈)는 카드 감사(B4), F15(카드가 바뀐 문장 되돌림)는 고리(B9)의 몫이다.

초안 꼴
    문단은 빈 줄로 가른다. 「#」 머리 줄 · 「|」 표 · 「<!-- -->」 주석 · 「$$」 · 「```」 블록은 문장으로 세지 않는다(표는 H26 이 본다).
    문장 끝에 꼬리표 `[카드 id, …]` — 카드 id · 「연결」(카드 없이 잇는 문장) · 「고정:종류」(코드가 꽂는 고정문 — 안내 · 날짜 · 면책 · 결론 …).
    문단 머리의 `<!-- 고정:면책 -->` 표지는 그 문단 전체를 고정문으로 둔다. 「그림 N.」 · 「표 N.」 으로 여는 문단은 그림 머리(명사구)다.
    꼬리표 꼴이 아닌 대괄호(마크다운 링크 [본편](#본편) 따위)는 글로 둔다.

카드
    `카드.py` 의 꼴(카드 v1). 옛 실험 카드(c · g 접두 · 「회차폴더」 칸)를 주면 `카드.옮기기` 로 옮겨 읽고(옛 등급은 `_옛등급` 에 남김),
    초안의 옛 꼬리표(c01)는 옮긴 카드의 `_옛id` 로 찾는다 — 보고에는 초안에 적힌 꼬리표를 쓴다. 카드를 안 주면 문장 층만 돈다.
    회차 폴더 = --회차 > 카드 문서의 「회차폴더」 · 「_회차」(상대 경로는 카드 파일 곳 기준) > 카드 파일이 _raw(/카드) 아래면 그 부모 > 초안 곳.
    가정 = --가정 > 회차의 가정_<회사>.json > 가정_*.json 하나(예시 · 템플릿 · 스키마 제외). 장부 = --장부 > 회차의 레터_초안.장부.json.

쓰는 법
    python 스크립트/문체검사.py <초안.md> [<사실카드.json>] [--회차 폴더] [--층 3분|본편] [--규칙 덧규칙.json …]
        [--참조 이름=경로 …] [--시험대 glob …] [--원천 이름=경로 …] [--고정문 파일] [--가정 파일] [--장부 파일] [--감사 끔] [--낼 밑경로]
    낸 것 — <초안>_문체검사.json · <초안>_문체검사.md (--낼 을 주면 그 밑경로로)
    종료 코드 — 0 오류 없음 · 1 오류 있음 · 2 입력 오류

회사 · 업종 이름은 이 파일에 없다. 회사마다 다른 것은 사실 카드 · 회차 파일 · 규칙 파일의 참조뿐이다.
"""
from __future__ import annotations

import argparse
import ast
import copy
import datetime as _dt
import glob
import io
import json
import operator
import os
import re
import statistics as st
import sys
from decimal import ROUND_HALF_UP, Decimal, localcontext
from fractions import Fraction

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass

여기 = os.path.dirname(os.path.abspath(__file__))
키트 = os.path.dirname(여기)
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
import 카드 as K                                    # noqa: E402
try:
    import 어투                                     # noqa: E402  — 끝맺음 판정(레터 게이트 ③ 의 「평서체 끝」 과 같은 함수)
except Exception:                                    # noqa: BLE001
    어투 = None

try:
    import 공시절 as 절                             # noqa: E402  — 인용 대조 규칙(조항추출.정규)을 빌려 쓴다
except Exception:                                    # noqa: BLE001
    절 = None

판 = "문체검사 1"
규칙파일 = os.path.join(여기, "문체검사규칙.json")
새검사 = ["F0", "F11", "F12", "F13", "F16"] + ["H%d" % n for n in range(17, 34)]


# ══ 바탕 ═══════════════════════════════════════════════════════════════════════════════════════════════
def 읽기(p):
    return io.open(p, encoding="utf-8-sig").read()


def 공백(s):
    return re.sub(r"\s+", " ", s).strip()


def 정규(x):
    return x.replace(" ", "").replace("−", "-")


def 합침(a, b):
    for k, v in (b or {}).items():
        if isinstance(v, dict) and isinstance(a.get(k), dict):
            합침(a[k], v)
        else:
            a[k] = copy.deepcopy(v)
    return a


def 규칙읽기(덧=()):
    규 = json.load(io.open(규칙파일, encoding="utf-8"))
    for p in 덧 or ():
        합침(규, json.load(io.open(p, encoding="utf-8")))
    return 규


def _날(s):
    try:
        return _dt.date.fromisoformat(str(s))
    except (TypeError, ValueError):
        return None


def _키트경로(p):
    return p if os.path.isabs(p) else os.path.join(키트, p)


# ══ 카드 ═══════════════════════════════════════════════════════════════════════════════════════════════
def 옛꼴인가(문서):
    if 문서.get("판") == K.판:
        return False
    if "회차폴더" in 문서:
        return True
    return any(isinstance(c, dict) and ("용어" in c or "사용" in c or re.match(r"^c\d", str(c.get("id", "")))) for c in 문서.get("카드", []))


def 카드읽기(경로):
    """카드 문서 → (고친 문서, 꼴 오류, 꼴 경고, 옛 꼴이었나). 옛 꼴이면 카드.옮기기 로 옮기고 옛 등급을 `_옛등급` 으로 남긴다."""
    문서 = json.load(io.open(경로, encoding="utf-8"))
    옛 = 옛꼴인가(문서)
    if 옛:
        옛등급 = {c.get("id"): c.get("등급") for c in 문서.get("카드", []) if isinstance(c, dict)}
        문서 = K.옮기기(문서)
        for c in 문서["카드"]:
            if c.get("_옛id") in 옛등급:
                c["_옛등급"] = 옛등급[c["_옛id"]]
    오, 경, 고친 = K.문서검사(문서)
    return 고친, 오, 경, 옛


def 회차찾기(인자회차, 문서, 카드경로, 초안경로):
    if 인자회차:
        return os.path.abspath(인자회차)
    for k in ("회차폴더", "_회차"):
        v = (문서 or {}).get(k)
        if v:
            p = v if os.path.isabs(v) else os.path.join(os.path.dirname(os.path.abspath(카드경로)), v)
            if os.path.isdir(p):
                return os.path.abspath(p)
    if 카드경로:
        d = os.path.dirname(os.path.abspath(카드경로))
        if os.path.basename(d) == "카드" and os.path.basename(os.path.dirname(d)) == "_raw":
            return os.path.dirname(os.path.dirname(d))
        if os.path.basename(d) == "_raw":
            return os.path.dirname(d)
    return os.path.dirname(os.path.abspath(초안경로))


def 가정찾기(회차, 회사, 지정):
    if 지정:
        return 지정
    if 회사 and os.path.isfile(os.path.join(회차, "가정_%s.json" % 회사)):
        return os.path.join(회차, "가정_%s.json" % 회사)
    후보 = [f for f in glob.glob(os.path.join(회차, "가정_*.json")) if not re.search(r"가정_(예시|템플릿|스키마)", os.path.basename(f))]
    return 후보[0] if len(후보) == 1 else None


# ══ 초안 읽기 ══════════════════════════════════════════════════════════════════════════════════════════
def 초안읽기(원문, 규):
    """→ (문단 [{글, 고정, 표앞, 그림}], 표 [글], 문장 [{p, i, 글, 꼬리, 고정, 그림}])."""
    꼬리꼴 = re.compile(규["꼬리표"]["꼴"])
    표지 = re.compile(규["꼬리표"]["고정표지"])
    그림 = re.compile(규["꼬리표"]["그림머리"])
    문단, 표 = [], []
    대기 = None
    for b in re.split(r"\n\s*\n", 원문):
        s = b.strip()
        if not s:
            continue
        m = 표지.match(s)
        if m:
            대기 = m.group(1)
            s = s[m.end():].strip()
            if not s:
                continue
        줄 = s.split("\n")
        while 줄 and 줄[0].lstrip().startswith("#"):
            줄 = 줄[1:]
        s = "\n".join(줄).strip()
        if not s:
            대기 = None
            continue
        if s.startswith("|"):
            표.append(s)
            if 문단:
                문단[-1]["표앞"] = True
            continue
        if s.startswith(("<!--", "```", "$$")):
            continue
        문단.append({"글": s, "고정": 대기, "표앞": False, "그림": bool(그림.match(s))})
        대기 = None
    문장들 = []
    for pi, p in enumerate(문단):
        글 = 공백(p["글"])
        시작 = 0
        조각 = []
        for m in re.finditer(r"\s*\[([^\[\]]+)\](?!\()", 글):
            토 = [t.strip() for t in m.group(1).split(",") if t.strip()]
            if not 토 or not all(꼬리꼴.match(t) for t in 토):
                continue
            본 = 글[시작:m.start()].strip()
            if 본:
                조각.append((본, 토))
            시작 = m.end()
        남 = 글[시작:].strip()
        if 남:                                      # 꼬리표 없는 끝 — 문장 끝(. ? !) 뒤 빈칸에서 나눈다
            조각 += [(x, []) for x in re.split(r"(?<=[.?!])\s+", 남) if x.strip()]
        for 본, 토 in 조각:
            고정 = p["고정"]
            for t in 토:
                if t.startswith("고정"):
                    고정 = t.split(":", 1)[1] if ":" in t else "고정"
            꼬리 = [t for t in 토 if not t.startswith("고정")]
            문장들.append({"p": pi, "i": len(문장들), "글": 본, "꼬리": 꼬리, "고정": 고정, "그림": p["그림"]})
    return 문단, 표, 문장들


# ══ 숫자 ═══════════════════════════════════════════════════════════════════════════════════════════════
class 숫자틀:
    def __init__(self, 규):
        q = 규["숫자"]
        self.날짜 = re.compile(q["날짜"])
        단위 = "(?:" + "|".join(re.escape(x) for x in q["단위"]) + ")"
        self.수식 = r"(?<![A-Za-z0-9.,])[−\-]?\d[\d,]*(?:\.\d+)?\s?" + 단위
        if q.get("합성금액"):                          # 「50만 7,971원」 · 「131조 8,950억 원」 은 숫자 하나
            self.수식 = "(?:%s)|(?:%s)" % (q["합성금액"], self.수식)
        self.수 = re.compile(self.수식)
        self.걷기 = [re.compile(x) for x in q["먼저걷기"]]
        self.맨 = re.compile(r"(?<![A-Za-z0-9.,%])\d[\d,.]*(?![\d,.]*\s?(?:" + "|".join(re.escape(x) for x in q["맨숫자뒤제외"]) + "))")

    def 본(self, 글):
        본 = self.날짜.sub(" ", 글)
        for r in self.걷기:
            본 = r.sub(" ", 본)
        return 본

    def 뽑기(self, 글):
        본 = self.본(글)
        return [m.group(0).strip() for m in self.수.finditer(본)], [m.group(0) for m in self.맨.finditer(본)]

    def 묶음셈(self, 글):
        """「얼마에서 얼마로 · 까지」 를 하나로 센 숫자 목록."""
        본 = self.본(글)
        ms = list(self.수.finditer(본))
        밖, i = [], 0
        while i < len(ms):
            if i + 1 < len(ms) and re.match(r"\s*에서", 본[ms[i].end():]) and re.match(r"\s*(?:으로|로|까지)", 본[ms[i + 1].end():]):
                밖.append(ms[i].group(0).strip() + "에서 " + ms[i + 1].group(0).strip())
                i += 2
                continue
            밖.append(ms[i].group(0).strip())
            i += 1
        return 밖


_금액식 = re.compile(r"((?:(?<![\d,.])\d[\d,]*(?:\.\d+)?\s?(?:조|억|만)\s?)+(?:\d[\d,]*\s?)?원|(?<![\d,.])\d[\d,]*(?:\.\d+)?\s?원)")
_달러식 = re.compile(r"(?<![\d,.])(\d[\d,]*(?:\.\d+)?)\s?(억|만)?\s?달러")


def 금액들(글):
    """[(통화, 큰 단위, (작은 단위, 소수 자리), 글)] — 금액 꼴 하나마다."""
    밖 = []
    for m in _금액식.finditer(글):
        조각 = re.findall(r"(\d[\d,]*(?:\.\d+)?)\s?(조|억|만)?", m.group(0))
        if not 조각:
            continue
        큰 = 조각[0][1] or "원"
        끝수, 끝단 = 조각[-1]
        소 = len(끝수.split(".")[1]) if "." in 끝수 else 0
        밖.append(("원", 큰, (끝단 or "원", 소), m.group(0).strip()))
    for m in _달러식.finditer(글):
        소 = len(m.group(1).split(".")[1]) if "." in m.group(1) else 0
        밖.append(("달러", m.group(2) or "달러", (m.group(2) or "달러", 소), m.group(0).strip()))
    return 밖


# ══ 식 다시 셈(F5) — 나무를 걸어 셈 · 정확한 분수 · ROUND_HALF_UP ══════════════════════════════════════
_이항 = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
       ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow}
_견줌 = {ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt, ast.LtE: operator.le, ast.Gt: operator.gt, ast.GtE: operator.ge}


def 식셈(식, 함수):
    """카드 계산 식을 eval 없이 센다 — 숫자 상수는 분수로, 함수는 「함수」 사전의 것만."""
    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant):
            v = n.value
            if isinstance(v, (bool, str)):
                return v
            if isinstance(v, int):
                return Fraction(v)
            if isinstance(v, float):
                return Fraction(repr(v))
            raise ValueError("상수 꼴")
        if isinstance(n, ast.UnaryOp):
            v = ev(n.operand)
            if isinstance(n.op, ast.USub):
                return -v
            if isinstance(n.op, ast.UAdd):
                return +v
            if isinstance(n.op, ast.Not):
                return not v
        if isinstance(n, ast.BinOp) and type(n.op) in _이항:
            return _이항[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.Compare):
            왼 = ev(n.left)
            for op, 오른식 in zip(n.ops, n.comparators):
                오른 = ev(오른식)
                if not _견줌[type(op)](왼, 오른):
                    return False
                왼 = 오른
            return True
        if isinstance(n, ast.BoolOp):
            v = isinstance(n.op, ast.And)
            for x in n.values:
                v = ev(x)
                if isinstance(n.op, ast.And) and not v:
                    return v
                if isinstance(n.op, ast.Or) and v:
                    return v
            return v
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in 함수:
            return 함수[n.func.id](*[ev(a) for a in n.args])
        if isinstance(n, ast.Attribute) and n.attr == "days":
            return Fraction(ev(n.value).days)
        if isinstance(n, (ast.List, ast.Tuple)):
            return [ev(e) for e in n.elts]
        raise ValueError("셀 수 없는 꼴 %s" % type(n).__name__)
    return ev(ast.parse(식, mode="eval"))


def 반올림(v, 자리):
    with localcontext() as 틀:
        틀.prec = 60
        d = Decimal(v.numerator) / Decimal(v.denominator) if isinstance(v, Fraction) else Decimal(str(v))
        return d.quantize(Decimal(1).scaleb(-자리), rounding=ROUND_HALF_UP)


def 시세읽기(p):
    행 = []
    for 줄 in io.open(p, encoding="utf-8-sig"):
        t = 줄.strip()
        if not t or t.startswith("#") or t.lower().startswith("date"):
            continue
        칸 = [c.strip() for c in t.split(",")]
        try:
            d = 칸[0].replace("-", "")
            행.append(("%s-%s-%s" % (d[:4], d[4:6], d[6:8]), Fraction(칸[1].replace(",", ""))))
        except (IndexError, ValueError, ZeroDivisionError):
            continue
    return 행


# ══ 검사 ═══════════════════════════════════════════════════════════════════════════════════════════════
class 검사:
    _ㅆ = None

    def __init__(self, 초안경로, 규, 카드경로=None, 회차=None, 층=None, 가정=None, 장부=None, 참조=(), 시험대=(), 원천=(), 고정문=None, 감사=True):
        self.규 = 규
        self.끔 = set(규.get("검사", {}).get("끔", []))
        self.층 = 층 or 규["층"]["기본"]
        self.초안경로 = 초안경로
        self.원문 = 읽기(초안경로)
        self.문단, self.표, self.문장들 = 초안읽기(self.원문, 규)
        self.수 = 숫자틀(규)
        self.걸림, self.정보 = [], []
        self.위치걸림 = {}
        self.감사 = 감사
        self.카드, self.별칭 = {}, {}
        self.문서 = None
        self.카드경로 = 카드경로
        self.옛꼴 = False
        self.인용수 = self.계산수 = self.장부수 = 0
        self.승인통과 = set()
        self._원천캐시 = {}
        if 카드경로:
            self.문서, 꼴오, 꼴경, self.옛꼴 = 카드읽기(카드경로)
            for c in self.문서.get("카드", []):
                if isinstance(c, dict) and c.get("id"):
                    self.카드[c["id"]] = c
                    if c.get("_옛id"):
                        self.별칭[c["_옛id"]] = c["id"]
            if self.켬("F0"):
                for x in 꼴오:
                    self.걸("사실", "F0", "오류", "카드", "카드 꼴 — " + x)
                if 꼴경:
                    self.걸("사실", "F0", "정보", "카드", "카드 꼴 경고 %d건(첫째: %s)" % (len(꼴경), 꼴경[0]))
        self.회차 = 회차찾기(회차, self.문서, 카드경로, 초안경로)
        self.회사 = (self.문서 or {}).get("회사")
        self.가정경로 = 가정찾기(self.회차, self.회사, 가정) if (self.문서 is not None or 가정) else None
        self.장부경로 = 장부 or os.path.join(self.회차, "레터_초안.장부.json")
        self.참조추가, self.시험대추가, self.원천추가, self.고정문 = list(참조), list(시험대), list(원천), 고정문

    # ── 기록 ──
    def 켬(self, 코드):
        return 코드 not in self.끔

    def 걸(self, 층, 코드, 등급, s, 설명):
        위치 = "문단%d·문장%d" % (s["p"] + 1, s["i"] + 1) if isinstance(s, dict) else str(s)
        self.걸림.append({"층": 층, "코드": 코드, "등급": 등급, "위치": 위치, "문장": (s["글"][:70] if isinstance(s, dict) else ""), "설명": 설명})
        self.위치걸림.setdefault(위치, set()).add(코드)

    # ── 카드 찾기 ──
    def 조회(self, t):
        if t in self.카드:
            return self.카드[t]
        if t in self.별칭:
            return self.카드[self.별칭[t]]
        return None

    def 표시(self, cid):
        return (self.카드.get(cid) or {}).get("_옛id") or cid

    def 등급글(self, c):
        return c.get(self.규["F6"].get("등급칸", "등급")) or c.get("등급") or ""

    def 문장카드(self, s):
        return [c for c in (self.조회(t) for t in s["꼬리"]) if c]

    def 쓴카드인가(self, s, c):
        return any(self.조회(t) is c for t in s["꼬리"])

    def 원천글(self, 파일):
        """H16 · F16 이 보는 원천 글(공백 정규화) — 실험 검증기와 같은 규칙(.json 은 글 + 풀어 쓴 JSON), .xml · .htm 은 공시절 규칙."""
        if 파일 not in self._원천캐시:
            p = 파일 if os.path.isabs(파일) else os.path.join(self.회차, 파일)
            t = ""
            if 파일 and os.path.isfile(p):
                확 = os.path.splitext(p)[1].lower()
                if 확 in (".xml", ".htm", ".html") and 절:
                    t = 절.원천글(p)
                else:
                    t = 읽기(p)
                    if 확 == ".json":
                        try:
                            t = t + "\n" + json.dumps(json.loads(t), ensure_ascii=False)
                        except ValueError:
                            pass
            self._원천캐시[파일] = 공백(t)
        return self._원천캐시[파일]

    def 장부색인(self):
        if not hasattr(self, "_장부"):
            self._장부 = {}
            if os.path.isfile(self.장부경로):
                for x in json.load(io.open(self.장부경로, encoding="utf-8")).get("숫자", []):
                    self._장부.setdefault(x.get("키"), []).append(x)
        return self._장부

    # ══ 사실 층 ══
    def 사실층(self):
        if not self.문서:
            self.정보.append("카드를 받지 않아 사실 층(F)을 돌리지 않았다 — 문장 층만")
            return
        S = self.문장들
        규 = self.규
        if self.켬("F1"):
            for s in S:
                if s["고정"] or s["그림"]:
                    continue
                if not s["꼬리"]:
                    self.걸("사실", "F1", "오류", s, "꼬리표 없음")
                for t in s["꼬리"]:
                    if t != "연결" and not self.조회(t):
                        self.걸("사실", "F1", "오류", s, "없는 카드 %s" % t)
        지수단위 = set(규["F12"]["지수단위"])
        for s in S:
            카 = self.문장카드(s)
            if not 카 and (s["고정"] or s["그림"]):
                continue
            허수 = set()
            for c in 카:
                for v in c.get("값", []) or []:
                    허수.add(정규(str(v.get("글", ""))))
                    if self.층 == "본편" and v.get("본편"):
                        허수.add(정규(str(v["본편"])))
            허날 = {d for c in 카 for d in (c.get("날짜") or [])}
            수, 맨 = self.수.뽑기(s["글"])
            지수퍼 = set()
            if self.켬("F12"):
                지수값 = {정규(str(v.get("글", ""))) for c in 카 for v in (c.get("값") or []) if v.get("단위") in 지수단위}
                for m in re.finditer(r"([−\-]?\d[\d,]*(?:\.\d+)?)\s?%(?!p)", s["글"]):
                    if 정규(m.group(1)) in 지수값:
                        지수퍼.add(정규(m.group(0)))
                        self.걸("사실", "F12", "오류", s, "단위가 지수인 카드 값 「%s」을 %%로 씀 — 지수 숫자 그대로" % m.group(1))
            if self.켬("F2"):
                for x in 수:
                    if 정규(x) not in 허수 and 정규(x) not in 지수퍼:
                        self.걸("사실", "F2", "오류", s, "카드에 없는 숫자 「%s」" % x)
                for x in 맨:
                    self.걸("사실", "F2", "경고", s, "단위 없는 숫자 「%s」" % x)
                for d in self.수.날짜.findall(s["글"]):
                    if d not in 허날 and not any(d.endswith(h) or h.endswith(d) for h in 허날):
                        self.걸("사실", "F2", "오류", s, "카드에 없는 날짜 「%s」" % d)
                if "연결" in s["꼬리"] and (수 or self.수.날짜.search(s["글"])):
                    self.걸("사실", "F2", "오류", s, "연결 문장에 숫자 · 날짜")
            if self.켬("F10"):
                for t in s["꼬리"]:
                    c = self.조회(t)
                    if not c:
                        continue
                    제한 = self.층 in (c.get("층제한") or [])
                    바닥 = bool(규["F10"].get("등급바닥")) and self.층 == "3분" and K.등급표.get(c.get("등급"), {}).get("3분") is False
                    if 제한 or 바닥:
                        self.걸("사실", "F10", "오류", s, "%s 는 원천 등급 때문에 이 층에 쓰지 않는 카드(%s)" % (t, self.등급글(c)))
            if self.켬("F13") and self.층 == "3분" and not s["고정"]:
                for t in s["꼬리"]:
                    c = self.조회(t)
                    if c and self.시나리오카드(c):
                        self.걸("사실", "F13", "오류", s, "%s 는 주당가치 · 시나리오 값 카드 — 3분 레터 회사 소개에 쓰지 않는다(결론 띠의 몫)" % t)
        if self.켬("F3"):
            self.한정()
        if self.켬("F11"):
            self.기준일뒤()
        if self.감사:
            self.인용대조()
            self.계산재현()
            self.장부대조()
        else:
            self.정보.append("--감사 끔 — F4 · F5 · F5b(카드 감사의 몫)를 돌리지 않았다")
        self.등급꼴()
        self.고유명사()
        self.용어()
        if self.켬("F16"):
            self.없음기록()

    def 문단별카드(self, pi):
        쓴 = {}
        for s in self.문장들:
            if s["p"] == pi:
                for c in self.문장카드(s):
                    if s not in 쓴.setdefault(c["id"], []):
                        쓴[c["id"]].append(s)
        return 쓴

    def 한정(self):
        S = self.문장들
        for pi in range(len(self.문단)):
            for cid, ss in self.문단별카드(pi).items():
                c = self.카드[cid]
                글합 = " ".join(x["글"] for x in ss)
                for 필 in c.get("필수", []) or []:
                    범위글 = " ".join(x["글"] for x in S if self.쓴카드인가(x, c)) if 필.get("종류") == "경로" else 글합
                    if not re.search(필["정규식"], 범위글):
                        self.걸("사실", "F3", "오류", ss[0], "%s 필수 한정 빠짐 — %s(%s)" % (self.표시(cid), 필.get("종류"), 필.get("설명", "")))
                for 권 in c.get("권장", []) or []:
                    if not re.search(권["정규식"], 글합):
                        self.걸("사실", "F3", "경고", ss[0], "%s 권장 한정 빠짐 — %s(%s)" % (self.표시(cid), 권.get("종류"), 권.get("설명", "")))

    def 기준일뒤(self):
        """F11 — 평가기준일 뒤 사실(공표일 · 사건일이 뒤)은 「평가기준일 뒤」와 「반영하지 않았다」를 함께, 평가기준일 뒤 일정은 「예정」."""
        q = self.규["F11"]
        T = _날(self.문서.get("평가기준일"))
        if not T:
            return
        for pi in range(len(self.문단)):
            for cid, ss in self.문단별카드(pi).items():
                c = self.카드[cid]
                공, 사 = _날(c.get("공표일")), _날(c.get("사건일"))
                일정 = bool(사 and 사 > T and (not 공 or 사 > 공))
                뒤사실 = bool((공 and 공 > T) or (사 and 사 > T and not 일정) or (c.get("평가기준일뒤") and not 일정 and not 공 and not 사))
                글합 = " ".join(x["글"] for x in ss)
                if 뒤사실 and not (re.search(q["뒤"], 글합) and re.search(q["반영안함"], 글합)):
                    self.걸("사실", "F11", "오류", ss[0], "%s 는 평가기준일 뒤의 사실 — 「평가기준일 뒤」와 「주당가치에 반영하지 않았다」를 함께 쓴다" % self.표시(cid))
                if 일정 and not re.search(q["예정"], 글합):
                    self.걸("사실", "F11", "오류", ss[0], "%s 는 평가기준일 뒤의 일정 — 「예정」으로 쓴다" % self.표시(cid))

    def 시나리오카드(self, c):
        q = self.규["F13"]
        if not (c.get("값") or []):
            return False
        장부 = self.장부색인()
        for v in c.get("값") or []:
            k = str(v.get("장부") or "")
            if not k:
                continue
            if any(re.search(x, k) for x in q["장부키"]):
                return True
            if re.search(q["장부꼴"]["접두"], k) and any(x.get("꼴") in q["장부꼴"]["꼴"] for x in 장부.get(k, [])):
                return True
        return bool(re.search(q["주장"], str(c.get("주장", ""))))

    def 인용대조(self):
        if not self.켬("F4"):
            return
        if 절 is not None:
            결 = 절.인용대조(self.문서, self.회차)
            self.인용수 = 결["인용수"]
            말 = {"불일치": "인용이 원천에 없음 — %s 「%s」", "파일없음": "원천 파일이 없음 — %s 「%s」", "인용없음": "인용이 비었음 — %s 「%s」"}
            for z in 결["줄"]:
                if z["판정"] in 말:
                    self.걸("사실", "F4", "오류", self.표시(z["id"]), 말[z["판정"]] % (z.get("파일"), str(z.get("인용") or "")[:40]))
                elif z["판정"] == "원천없음":
                    self.걸("사실", "F4", "오류", self.표시(z["id"]), "원천이 없음 — %s" % z.get("까닭", ""))
            return
        for c in self.카드.values():                          # 공시절을 못 불렀을 때 — 실험 검증기의 규칙
            for o in c.get("원천", []) or []:
                self.인용수 += 1
                if 공백(str(o.get("인용", ""))) not in self.원천글(o.get("파일", "")):
                    self.걸("사실", "F4", "오류", self.표시(c["id"]), "인용이 원천에 없음 — %s 「%s」" % (o.get("파일"), str(o.get("인용", ""))[:40]))

    def 계산재현(self):
        if not self.켬("F5"):
            return
        캐시 = {}

        def 시세(파일):
            if 파일 not in 캐시:
                캐시[파일] = 시세읽기(os.path.join(self.회차, 파일))
            return 캐시[파일]

        def 고름(파일, 시작=None, 끝=None):
            return [v for d, v in 시세(파일) if (시작 is None or d >= str(시작)) and (끝 is None or d <= str(끝))]

        def 장부값(키):
            for x in self.장부색인().get(키, []):
                if isinstance(x.get("값"), (int, float)):
                    return Fraction(repr(float(x["값"])))
            raise ValueError("장부에 없는 키 %s" % 키)
        함수 = {"date": lambda *a: _dt.date(*[int(x) for x in a]), "abs": abs, "round": round, "min": min, "max": max, "sum": sum,
              "csv_max": lambda f, a=None, b=None: max(고름(f, a, b)), "csv_min": lambda f, a=None, b=None: min(고름(f, a, b)),
              "csv_at": lambda f, d: next(v for dd, v in 시세(f) if dd == str(d)), "장부": 장부값}
        for c in self.카드.values():
            for k in c.get("계산", []) or []:
                self.계산수 += 1
                try:
                    v = 식셈(k["식"], 함수)
                except Exception as e:                       # noqa: BLE001
                    self.걸("사실", "F5", "오류", self.표시(c["id"]), "계산을 다시 셀 수 없음 — %s: %s (%s)" % (k.get("이름"), k.get("식"), e))
                    continue
                글 = str(k.get("글", ""))
                if 글 == "참":
                    ok = bool(v)
                else:
                    m = re.search(r"[−\-]?\d[\d,]*(?:\.\d+)?", 글)
                    if not m:
                        self.걸("사실", "F5", "오류", self.표시(c["id"]), "계산 글에 숫자가 없음 — %s" % k.get("이름"))
                        continue
                    자 = int(k.get("자리") or 0)
                    n = Decimal(m.group(0).replace(",", "").replace("−", "-")).quantize(Decimal(1).scaleb(-자))
                    비 = v * 100 if 글.endswith("%") else v
                    ok = 반올림(비, 자) == n
                if not ok:
                    self.걸("사실", "F5", "오류", self.표시(c["id"]), "계산 불일치 — %s: %s → %s" % (k.get("이름"), k.get("식"), float(v) if isinstance(v, Fraction) else v))

    def 장부대조(self):
        if not self.켬("F5b"):
            return
        있는키 = any((v.get("장부") and not str(v["장부"]).startswith("식:")) for c in self.카드.values() for v in c.get("값", []) or [])
        if 있는키 and not os.path.isfile(self.장부경로):
            self.정보.append("장부 파일이 없어 F5b 를 돌리지 않았다 — %s" % self.장부경로)
            return
        장부글 = {k: {x.get("글") for x in xs} for k, xs in self.장부색인().items()}
        for c in self.카드.values():
            for v in c.get("값", []) or []:
                k = v.get("장부")
                if k and not str(k).startswith("식:"):
                    self.장부수 += 1
                    if k not in 장부글:
                        self.걸("사실", "F5b", "오류", self.표시(c["id"]), "장부에 없는 키 %s" % k)
                    elif v.get("글") not in 장부글[k]:
                        self.걸("사실", "F5b", "오류", self.표시(c["id"]), "장부 글 불일치 %s: %s ≠ %s" % (k, v.get("글"), 장부글[k]))

    def 등급꼴(self):
        if not self.켬("F6"):
            return
        q = self.규["F6"]
        포함 = q.get("맞춤") == "포함"
        for s in self.문장들:
            for t in s["꼬리"]:
                c = self.조회(t)
                if not c:
                    continue
                등 = self.등급글(c)
                for 이름, 식 in q["꼴"]:
                    if ((이름 in 등) if 포함 else (이름 == 등)) and not re.search(식, s["글"]):
                        앞 = [x for x in self.문장들 if x["p"] == s["p"] and x["i"] < s["i"] and self.쓴카드인가(x, c) and re.search(식, x["글"])]
                        self.걸("사실", "F6", "경고" if 앞 else "오류", s, "%s(%s) 카드인데 문장에 출처 꼴이 없음" % (t, 등))
                if c.get("등급") == q["일반설명"] and all((self.조회(x) or {}).get("등급") == q["일반설명"] for x in s["꼬리"]) and self.수.뽑기(s["글"])[0]:
                    self.걸("사실", "F6", "오류", s, "일반설명 문장에 숫자")

    def 고유명사(self):
        if not self.켬("F7"):
            return
        명 = {}
        for c in self.카드.values():
            for g in c.get("고유명사", []) or []:
                명[g["이름"]] = g["소개"]
        for 이름, 소개 in 명.items():
            첫 = next((s for s in self.문장들 if 이름 in s["글"]), None)
            if 첫 and not re.search(소개, 첫["글"]):
                self.걸("사실", "F7", "오류", 첫, "고유명사 「%s」 첫 등장에 소개 없음" % 이름)

    def 용어카드(self):
        밖 = {}
        for c in self.카드.values():
            for u in (c.get("풀이용어") or c.get("용어") or []):
                밖[u] = c["id"]
        return 밖

    def 첫등장(self, u, 용어들):
        """용어 u 가 처음 나오는 문장. u 를 품은 더 긴 용어(「범용 X」 · 「X당 매출」 꼴)는 지우고 보고, 로마자 용어는 로마자 경계를 본다."""
        긴 = sorted([w for w in 용어들 if w != u and u in w], key=len, reverse=True)
        앞 = r"(?<![A-Za-z])" if re.match(r"[A-Za-z]", u) else ""
        뒤 = r"(?![A-Za-z])" if re.search(r"[A-Za-z]$", u) else ""
        식 = re.compile(앞 + re.escape(u) + 뒤)
        for s in self.문장들:
            글 = s["글"]
            for w in 긴:
                글 = 글.replace(w, " ")
            if 식.search(글):
                return s
        return None

    def 용어(self):
        용 = self.용어카드()
        if self.켬("F8"):
            for u, cid in 용.items():
                s = self.첫등장(u, 용)
                if s is None:
                    continue
                다음 = [x for x in self.문장들 if x["i"] == s["i"] + 1]
                if cid not in [c["id"] for c in self.문장카드(s)] and not (다음 and cid in [c["id"] for c in self.문장카드(다음[0])]):
                    self.걸("사실", "F8", "오류", s, "용어 「%s」 첫 등장(또는 다음 문장)에 풀이 카드 %s 없음" % (u, self.표시(cid)))
        if self.켬("F9"):
            for u in self.문서.get("결론에_나오는_용어", []) or []:
                if self.첫등장(u, 용) is None:
                    self.걸("사실", "F9", "오류", "전체", "결론에 나오는 용어 「%s」를 회사 소개에서 풀지 않음" % u)

    def 없음기록(self):
        q = self.규["F16"]
        말 = re.compile(q["없다는말"])
        걸릴 = [s for s in self.문장들 if 말.search(s["글"])]
        if not 걸릴:
            return
        기록, 꼴틀림 = {}, []
        for p in sorted(glob.glob(os.path.join(self.회차, q["기록파일"]))):
            try:
                d = json.load(io.open(p, encoding="utf-8"))
            except ValueError:
                꼴틀림.append(os.path.basename(p))
                continue
            항 = d.get("없음") if isinstance(d, dict) else None
            if not (isinstance(d, dict) and str(d.get("형식", "")).startswith(q["기록형식"])) or not isinstance(항, list):
                꼴틀림.append(os.path.basename(p))
                continue
            for x in 항:
                if not (isinstance(x, dict) and all(x.get(k) for k in q["기록칸"])):
                    꼴틀림.append("%s 「%s」" % (os.path.basename(p), (x or {}).get("항목") if isinstance(x, dict) else x))
                    continue
                for cid in x.get("대신_지은카드", []) or []:
                    기록.setdefault(cid, []).append(x.get("항목"))
        for f in 꼴틀림:
            self.걸("사실", "F16", "경고", "기록", "「없음」 기록 꼴이 다름 — %s(카드 감사 B4 가 꼴을 정하면 맞춘다)" % f)
        카말 = re.compile(q["카드의없다는말"])
        for s in 걸릴:
            ok = False
            for c in self.문장카드(s):
                if c["id"] in 기록 or c.get("_옛id") in 기록:
                    ok = True
                    break
                글 = str(c.get("주장", "")) + " ".join(str(o.get("인용", "")) for o in c.get("원천", []) or [])
                if "✱" not in s["글"] and 카말.search(글):
                    ok = True
                    break
            if not ok:
                self.걸("사실", "F16", "경고", s, "「없다」 · 자리표시 문장인데 검색 기록(_raw/카드/*없음*.json)이나 「없음」을 적은 카드가 꼬리표에 없음")

    # ══ 문장 층(H1 ~ H16) ══
    def 가정이름들(self):
        밖 = set()
        if not (self.가정경로 and os.path.isfile(self.가정경로)):
            return 밖
        q = self.규["H8"]["가정이름"]

        def 훑(x):
            if isinstance(x, dict):
                for k, v in x.items():
                    if k == "이름" and isinstance(v, str) and len(v) >= q["최소글자"] and (" " in v or not q["빈칸"]):
                        밖.add(v)
                    훑(v)
            elif isinstance(x, list):
                for v in x:
                    훑(v)
        try:
            훑(json.load(io.open(self.가정경로, encoding="utf-8")))
        except ValueError:
            pass
        return 밖

    def 문장층(self):
        규 = self.규
        S = self.문장들
        가정이름 = self.가정이름들() if self.켬("H8") else set()
        끝 = re.compile(규["H1"]["끝맺음"])
        죠 = re.compile(규["H1"]["죠"])
        식들 = [(규["H7"]["금칙"], "H7", "저자 금칙어"), (규["H7"]["권유"], "H7", "권유 · 가치판단"), (규["H8"]["내부어"], "H8", "모델 내부 말"),
              (규["H9"]["안내"], "H9", "글 구조 안내"), (규["H10"]["추상"], "H10", "추상 주어 + 판단 동사")]
        예외 = {"H9": set(규["H9"].get("예외고정", [])), "H10": set(규["H10"].get("예외고정", []))}
        대체 = re.compile(규["H12"]["대체어"])
        잇 = 죠수 = 물음 = 0
        for s in S:
            g = s["글"]
            수, _ = self.수.뽑기(g)
            if self.켬("H1") and not s["그림"]:
                꼴 = 어투.끝꼴(g) if 어투 else None          # v27 — 평서체 끝(~다)의 판정은 레터 게이트 ③ 과 한 함수(`어투.끝꼴`)
                if 꼴 == "평서":
                    self.걸("문장", "H1", "오류", s, "평서체 끝맺음(~다)")
                elif 꼴 != "합쇼" and not 끝.search(g):
                    self.걸("문장", "H1", "오류", s, "합쇼체 끝맺음 아님")
            if self.켬("H2"):
                if len(g) > 규["H2"]["오류"]:
                    self.걸("문장", "H2", "오류", s, "%d자" % len(g))
                elif len(g) > 규["H2"]["경고"]:
                    self.걸("문장", "H2", "경고", s, "%d자" % len(g))
            if self.켬("H3"):
                셈 = self.수.묶음셈(g) if 규["H3"].get("증감묶음") else 수
                if len(셈) > 규["H3"]["상한"]:
                    self.걸("문장", "H3", "오류", s, "숫자 %d개 %s" % (len(셈), 셈))
            if self.켬("H4"):
                for 덩 in re.findall(규["H4"]["나열"], g):
                    self.걸("문장", "H4", "오류", s, "「·」 셋 이상 「%s」" % 덩)
            if self.켬("H5") and (g.count("(") > 1 or re.search(r"\([^)]*\(", g)):
                self.걸("문장", "H5", "오류", s, "괄호 둘 이상 · 겹괄호")
            if self.켬("H6") and re.search(규["H6"]["기호"], g):
                self.걸("문장", "H6", "오류", s, "연산 기호")
            for 식, 코, 설 in 식들:
                if not self.켬(코) or (s["고정"] in 예외.get(코, ())):
                    continue
                m = re.search(식, g)
                if m:
                    self.걸("문장", 코, "오류", s, "%s 「%s」" % (설, m.group(0)))
            for n in 가정이름:
                if n in g:
                    self.걸("문장", "H8", "오류", s, "가정 이름 「%s」" % n)
            if self.켬("H12"):
                m = 대체.search(g)
                if m:
                    self.걸("문장", "H12", "경고", s, "대체어 「%s」" % m.group(0))
            잇 = 잇 + 1 if g.endswith("입니다.") or g.endswith("입니다") else 0
            if self.켬("H13") and 잇 >= 규["H13"]["연속"]:
                self.걸("문장", "H13", "경고", s, "「입니다」 %d연속" % 규["H13"]["연속"])
            if 죠.search(g):
                죠수 += 1
                if self.켬("H1") and 수:
                    self.걸("문장", "H1", "오류", s, "숫자 든 문장에 「~죠」")
            if g.endswith("?"):
                물음 += 1
        if self.켬("H1") and 죠수 > 규["H1"]["죠상한"]:
            self.걸("문장", "H1", "경고", "전체", "「~죠」 %d회" % 죠수)
        if self.켬("H9") and 물음 > 규["H9"]["물음상한"]:
            self.걸("문장", "H9", "경고", "전체", "물음 %d회" % 물음)
        대구식 = [re.compile(x) for x in 규["H14"]["대구"]]
        for pi in range(len(self.문단)):
            ss = [s for s in S if s["p"] == pi]
            if self.켬("H11"):
                날 = [d for s in ss for d in self.수.날짜.findall(s["글"])]
                for d in sorted(set(날), key=날.index):
                    if 날.count(d) > 1:
                        self.걸("문장", "H11", "오류", "문단%d" % (pi + 1), "같은 날짜 「%s」 %d회" % (d, 날.count(d)))
            if self.켬("H14"):
                대구 = sum(len(r.findall(s["글"])) for s in ss for r in 대구식)
                if 대구 > 규["H14"]["문단상한"]:
                    말 = "「A가 아니라 B」" if len(대구식) == 1 else "대조 대구(「A가 아니라 B」 · 「A인지, B인지」)"
                    self.걸("문장", "H14", "경고", "문단%d" % (pi + 1), "%s %d회" % (말, 대구))
            if self.켬("H15"):
                p = self.문단[pi]
                고정문단 = bool(p["고정"] or p["그림"] or p["표앞"] or (ss and all(s["고정"] for s in ss)))
                하, 상 = 규["H15"].get(self.층, 규["H15"]["3분"])
                if not 고정문단 and not (하 <= len(ss) <= 상):
                    self.걸("문장", "H15", "경고", "문단%d" % (pi + 1), "문단 문장 수 %d" % len(ss))
        if self.켬("H16"):
            self.복제()

    def 복제(self):
        """H16 — 작가 지시 · 견본 문단 풀 · 시험대의 다른 회사 레터와 15자 넘게 같은 글자열. 그 문장 카드의 원천에도 있으면 정보."""
        q = self.규["H16"]
        창 = q["창"]
        참조 = {}
        for r in q.get("참조", []):
            for p in sorted(glob.glob(_키트경로(r["경로"]))):
                참조[("%s %s" % (r["이름"], os.path.basename(p))) if "*" in r["경로"] else r["이름"]] = p
        for x in self.참조추가:
            이름, _, p = x.partition("=")
            참조[이름] = p
        회사 = self.회사 or ""
        for g in list(q.get("시험대", [])) + self.시험대추가:
            for p in sorted(glob.glob(_키트경로(g))):
                if 회사 and (회사 in os.path.basename(p) or 회사 in os.path.basename(os.path.dirname(p))):
                    continue
                참조["시험대 %s" % os.path.basename(os.path.dirname(p)) + "/" + os.path.basename(p)] = p
        원천 = {}
        for g in q.get("원천", []):
            if "{회사}" in g and not 회사:
                continue
            for p in sorted(glob.glob(os.path.join(self.회차, g.replace("{회사}", 회사)))):
                원천["현행 레터" if not 원천 else "현행 레터 %s" % os.path.basename(p)] = p
        for x in self.원천추가:
            이름, _, p = x.partition("=")
            원천[이름 if p else "원천"] = p or 이름
        참조글 = {k: 공백(읽기(v)) for k, v in 참조.items() if os.path.isfile(v)}
        원천글들 = {k: 공백(읽기(v)) for k, v in 원천.items() if os.path.isfile(v)}
        self.복제참조 = sorted(참조글) + ["(원천) %s" % k for k in sorted(원천글들)]
        if not 참조글:
            self.정보.append("H16 — 비교할 작가 지시 · 견본 문단 풀 · 시험대 레터가 없다(규칙 파일 H16 · --참조 · --시험대)")

        def 겹침(g, 글):
            구간, i = [], 0
            while i + 창 <= len(g):
                if g[i:i + 창] in 글:
                    j = i + 창
                    while j < len(g) and g[i:j + 1] in 글:
                        j += 1
                    구간.append(g[i:j])
                    i = j
                else:
                    i += 1
            return 구간
        for s in self.문장들:
            원천합 = " ".join(self.원천글(o.get("파일", "")) for c in self.문장카드(s) for o in c.get("원천", []) or [])
            for k, t in 참조글.items():
                for x in 겹침(s["글"], t):
                    if len(re.findall(r"[가-힣]", x)) < q.get("최소한글", 0):
                        continue                            # 용어 이름 · 숫자뿐인 겹침(「 Unlevered Beta」)은 복제가 아니다
                    원천말 = any(y in 원천합 for y in [x[i:i + 창] for i in range(0, max(1, len(x) - 창 + 1))])
                    self.걸("문장", "H16", "정보" if 원천말 else "경고", s, "「%s」와 %d자 겹침%s 「%s」" % (k, len(x), "(원천에서 온 말)" if 원천말 else "", x))
            for k, t in 원천글들.items():
                for x in 겹침(s["글"], t):
                    self.걸("문장", "H16", "정보", s, "원천 「%s」와 %d자 겹침 「%s」" % (k, len(x), x))

    # ══ 새 문장 검사(H17 ~ H33) ══
    def 새문장층(self):
        규 = self.규
        S = self.문장들
        if self.켬("H17"):
            self.고정문대조()
        for s in S:
            g = s["글"]
            if self.켬("H18"):
                m = re.search(규["H18"]["값"], g)
                if m:
                    self.걸("문장", "H18", "경고", s, "「값」을 홀로 주어 · 지시어로 · 「주식 가치」 「%s」 — 무엇의 값인지(주당가치 · 가정값)" % m.group(0).strip(" ,."))
            if self.켬("H19") and re.search(규["H19"]["개수"], g):
                self.걸("문장", "H19", "경고", s, "「~은 N 가지입니다」 꼴 — 개수를 따로 말하지 않고 서술어 문장 안에 넣는다")
            if self.켬("H21") and self.문서:
                self.약검사(s)
            if self.켬("H22"):
                큰 = sorted({x[1] for x in 금액들(g) if x[0] == "원"})
                if len(큰) > 1:
                    self.걸("문장", "H22", "경고", s, "한 문장에 금액 단위가 섞임 — %s" % " · ".join(("%s 원" % u) if u != "원" else "원" for u in 큰))
                for m in re.finditer(r"([−\-]?\d[\d.]*)%에서[^%]{0,40}?([−\-]?\d[\d.]*)%(?:로|까지)[^%]{0,40}?(\d[\d.]*)%(?!p)", g):
                    try:
                        a, b, c = (float(x.replace("−", "-")) for x in m.groups())
                    except ValueError:
                        continue
                    if c and abs(abs(b - a) - c) <= 규["H22"]["퍼센트포인트허용"]:
                        self.걸("문장", "H22", "경고", s, "비율의 차이 「%s%%」는 %%p 로 쓴다" % m.group(3))
            if self.켬("H23"):
                self.순서검사(s)
            if self.켬("H29"):
                m = re.search(규["H29"]["동작예고"], g)
                if m:
                    self.걸("문장", "H29", "경고", s, "동작 예고 「%s」" % m.group(0))
                if "연결" in s["꼬리"]:
                    for 이름, 식 in (("인과", 규["H29"]["연결인과"]), ("평가", 규["H29"]["연결평가"])):
                        m = re.search(식, g)
                        if m:
                            self.걸("문장", "H29", "경고", s, "연결 문장에 %s 낱말 「%s」 — 카드에 없는 %s이 된다" % (이름, m.group(0), 이름))
            if self.켬("H30"):
                self.맞춤법(s)
            if self.켬("H32"):
                self.같은서술어(s)
        if self.켬("H20"):
            for pi in range(len(self.문단)):
                무리 = {}
                for s in S:
                    if s["p"] == pi:
                        for 통, 큰, 작, 글 in 금액들(s["글"]):
                            무리.setdefault((통, 큰), {}).setdefault(작, 글)
                for (통, 큰), 작들 in 무리.items():
                    if len(작들) > 1:
                        self.걸("문장", "H20", "경고", "문단%d" % (pi + 1), "한 문단 안에서 금액 정밀도가 섞임 — %s" % " · ".join("「%s」" % v for v in 작들.values()))
        if self.켬("H24"):
            self.날짜이름()
        if self.켬("H25") or self.켬("H26"):
            self.병기()
        if self.켬("H27"):
            self.한이름()
        if self.켬("H28"):
            self.상호()
        if self.켬("H33") and self.층 == "3분" and self.문서:
            self.풀이수()
        if self.켬("H31"):
            self.일단계()

    def 고정문대조(self):
        q = self.규["H17"]
        p = self.고정문 or _키트경로(q["승인문형"])
        문형 = []
        if os.path.isfile(p):
            try:
                문형 = json.load(io.open(p, encoding="utf-8")).get("문형", []) or []
            except ValueError:
                문형 = []
        묶음 = []
        for pi in range(len(self.문단)):
            앞 = None
            for s in self.문장들:
                if s["p"] != pi:
                    continue
                if not s["고정"]:
                    앞 = None
                    continue
                if 앞 and 앞["종류"] == s["고정"]:
                    앞["문장"].append(s)
                else:
                    앞 = {"종류": s["고정"], "문장": [s]}
                    묶음.append(앞)
        if not 묶음:
            return
        if not 문형:
            self.걸("문장", "H17", "정보", "전체", "저자 승인 문형이 없어(%s) 고정문 %d 묶음을 대조하지 못함" % (os.path.basename(p), len(묶음)))
            return
        자리 = {"날짜": r"(?:\d{4}년 )?\d{1,2}월 \d{1,2}일", "금액": r"[−\-]?\d[\d,.]*\s?(?:조|억|만)?\s?(?:\d[\d,]*\s?)?(?:원|달러)",
              "수": r"[−\-+]?\d[\d,.]*\s?(?:%p|%|배)?", "이름": r"[^,.]{1,40}?"}

        def 식(글):
            t = re.escape(공백(글))
            for k, v in 자리.items():
                t = t.replace(re.escape("{%s}" % k), v)
            return re.compile("^" + t + "$")
        for b in 묶음:
            후보 = [x for x in 문형 if x.get("종류") == b["종류"] or b["종류"] == "고정"]
            글 = " ".join(s["글"] for s in b["문장"])
            if not 후보:
                self.걸("문장", "H17", "경고", b["문장"][0], "고정문 종류 「%s」의 승인 문형이 없음" % b["종류"])
            elif any(식(x.get("글", "")).match(공백(글)) for x in 후보):
                for s in b["문장"]:
                    self.승인통과.add(s["i"])
            else:
                self.걸("문장", "H17", "오류", b["문장"][0], "고정문 「%s」이 저자 승인 문형과 글자까지 같지 않음" % b["종류"])

    def 약검사(self, s):
        for m in re.finditer(r"약\s?(" + self.수.수식 + ")", s["글"]):
            숫 = m.group(1).strip()
            ok = False
            for c in self.문장카드(s):
                for v in c.get("값", []) or []:
                    vg = str(v.get("글", ""))
                    if (vg.startswith("약") and 정규(vg[1:]) == 정규(숫)) or (정규(vg) == 정규(숫) and (v.get("대표") or v.get("어림"))):
                        ok = True
                글 = str(c.get("주장", "")) + " " + " ".join(str(o.get("인용", "")) for o in c.get("원천", []) or [])
                if re.search(r"약\s?" + re.escape(숫), 글):
                    ok = True
            if not ok:
                self.걸("문장", "H21", "경고", s, "「약 %s」 — 「약」은 대표값으로 줄인 카드 값에만(카드 · 원천에 「약」이 없음)" % 숫)

    def 순서검사(self, s):
        q = self.규["H23"]
        g = s["글"]
        if re.search(q["범위"], g):
            self.걸("문장", "H23", "경고", s, "범위를 「A~B」로 씀 — 「A에서 B까지」")
        if not re.search("비관|낙관", g):
            return
        본 = re.sub(q["기준비교"], " ", g)
        자리 = []
        for 이름 in q["순서"]:
            식 = 이름 if 이름 != "기준" else r"기준(?! ?일|으로|에서| 대비|보다)"
            m = re.search(식, 본)
            if m:
                자리.append((m.start(), q["순서"].index(이름), 이름))
        자리.sort()
        차례 = [x[1] for x in 자리]
        if 차례 != sorted(차례):
            self.걸("문장", "H23", "경고", s, "시나리오 순서가 %s — 비관 · 기준 · 낙관 순으로" % " · ".join(x[2] for x in 자리))

    def 맞춤법(self, s):
        q = self.규["H30"]
        g = s["글"]
        if q.get("률율"):
            for m in re.finditer(r"([가-힣]*?)([가-힣])([률율])([가-힣]*)", g):
                받침 = (ord(m.group(2)) - 0xAC00) % 28
                바름 = "율" if 받침 in (0, 4) else "률"
                if m.group(3) != 바름:
                    self.걸("문장", "H30", "경고", s, "맞춤법 「%s」 → 「%s%s%s%s」(모음 · ㄴ 받침 뒤는 율, 그 밖의 받침 뒤는 률)"
                           % (m.group(0), m.group(1), m.group(2), 바름, m.group(4)))
        for 틀, 바 in q.get("사이시옷", []):
            if 틀 in g:
                self.걸("문장", "H30", "경고", s, "맞춤법 「%s」 → 「%s」" % (틀, 바))
        for 틀, 바 in q.get("띄어쓰기", []):
            m = re.search(틀, g)
            if m:
                self.걸("문장", "H30", "경고", s, "띄어쓰기 「%s」 → 「%s」" % (m.group(0), m.expand(바)))

    def 같은서술어(self, s):
        q = self.규["H32"]
        if 검사._ㅆ is None:
            ㅆ = "".join(chr(0xAC00 + b * 28 + 20) for b in range(399))
            검사._ㅆ = re.compile(q["끝"].replace("{ㅆ}", "[" + ㅆ + "]"))
        본 = {}
        for 토 in re.findall(r"[가-힣]+", s["글"]):
            m = 검사._ㅆ.search(토)
            if not m or m.start() == 0:
                continue
            어간 = 토[:m.start()]
            if 어간 in q["가벼운말"]:
                continue
            본.setdefault(어간, []).append(토)
        for 어간, 토들 in 본.items():
            if len(토들) > 1:
                self.걸("문장", "H32", "경고", s, "같은 서술어 두 번 「%s」(어간 「%s」)" % (" · ".join(토들), 어간))

    def 날짜이름(self):
        """H24 — 날짜 이름은 「평가기준일(2026년 10월 23일)」 꼴로 한 번 정의하고 그 뒤로는 이름만."""
        이름식 = "|".join(re.escape(x) for x in sorted(self.규["H24"]["이름"], key=len, reverse=True))
        날 = r"((?:\d{4}년 )?(\d{1,2}월 \d{1,2}일))"
        바른 = re.compile(r"(%s)\s?\(\s?%s\s?\)" % (이름식, 날))
        틀1 = re.compile(r"(%s)(?:인|은|는|이|:)?\s?%s" % (이름식, 날))
        틀2 = re.compile(r"%s\s?\((%s)\)" % (날, 이름식))
        정의 = {}
        for s in self.문장들:
            g = s["글"]
            이번 = set()
            for m in 바른.finditer(g):
                정의.setdefault(m.group(3), m.group(1))
                이번.add(m.group(3))
            for m in 틀1.finditer(g):
                if m.group(3) in 이번:
                    continue
                self.걸("문장", "H24", "경고", s, "날짜 이름의 정의 꼴이 아님 「%s」 — 「%s(%s)」 꼴로" % (m.group(0), m.group(1), m.group(2)))
                정의.setdefault(m.group(3), m.group(1))
                이번.add(m.group(3))
            for m in 틀2.finditer(g):
                if m.group(2) in 이번:
                    continue
                self.걸("문장", "H24", "경고", s, "날짜 이름의 정의 꼴이 아님 「%s」 — 「%s(%s)」 꼴로" % (m.group(0), m.group(3), m.group(1)))
                정의.setdefault(m.group(2), m.group(3))
                이번.add(m.group(2))
            for m in self.수.날짜.finditer(g):
                md = re.search(r"\d{1,2}월 \d{1,2}일", m.group(0)).group(0)
                if md in 정의 and md not in 이번:
                    self.걸("문장", "H24", "경고", s, "「%s」로 정의한 날짜를 날짜 「%s」로 다시 씀 — 이름만" % (정의[md], m.group(0)))

    def 병기(self):
        """H25 병기 순서(스위치 — 끄면 정보) · H26 같은 용어를 두 번 병기(첫 병기가 표여도)."""
        q = self.규["H25"]
        영어 = {x.lower() for x in q["영어목록"]}
        켬 = bool(q.get("켬"))
        한영 = re.compile(r"([가-힣][가-힣 ·]{0,20}?)\s?\(([A-Za-z][A-Za-z0-9 .\-/&']*[A-Za-z0-9]|[A-Za-z])\)")
        영한 = re.compile(r"(?<![A-Za-z0-9])([A-Za-z][A-Za-z0-9 .\-/&']*[A-Za-z0-9]|[A-Za-z])\s?\(([가-힣][^()]{0,30})\)")
        표병기 = set()
        for t in self.표:
            for m in 한영.finditer(t):
                표병기.add(m.group(2).strip().lower())
            for m in 영한.finditer(t):
                표병기.add(m.group(1).strip().lower())
        첫글 = {}
        for s in self.문장들:
            for m in 한영.finditer(s["글"]):
                w = m.group(2).strip().lower()
                if self.켬("H25") and w in 영어:
                    self.걸("문장", "H25", "오류" if 켬 else "정보", s, "병기 순서 — 「%s」는 용어표가 영어로 쓰기로 정한 말이라 영어(한국어)로" % m.group(2))
                첫글.setdefault(w, []).append(s)
            for m in 영한.finditer(s["글"]):
                w = m.group(1).strip().lower()
                if self.켬("H25") and w not in 영어:
                    self.걸("문장", "H25", "오류" if 켬 else "정보", s, "병기 순서 — 「%s(%s)」는 한국어(영문)로【결정 2 제안안】" % (m.group(1), m.group(2)))
                첫글.setdefault(w, []).append(s)
        if self.켬("H26"):
            for w, ss in 첫글.items():
                for s in (ss if w in 표병기 else ss[1:]):
                    self.걸("문장", "H26", "경고", s, "같은 용어 「%s」를 한 레터에서 두 번 병기%s" % (w, "(첫 병기는 표)" if w in 표병기 and s is ss[0] else ""))

    def 한이름(self):
        용 = list(self.용어카드()) if self.문서 else []
        묶음들 = list(self.규["H27"]["묶음"]) + [x for x in ((self.문서 or {}).get("동의어") or []) if isinstance(x, list) and len(x) > 1]
        for 묶 in 묶음들:
            첫 = {}
            for 말 in 묶:
                앞 = r"(?<![A-Za-z])" if re.match(r"[A-Za-z]", 말) else r"(?<![가-힣])"
                뒤 = (r"(?![A-Za-z])" if re.search(r"[A-Za-z]$", 말) else
                     r"(?=$|[^가-힣]|(?:은|는|이|가|을|를|의|에|과|와|도|만|으로|로|에서|보다|까지|부터|이다|입니다)(?![가-힣]))")
                식 = re.compile(앞 + 말 + 뒤)
                for s in self.문장들:
                    글 = s["글"]
                    for w in 용:
                        if w != 말 and re.search(말, w):
                            글 = 글.replace(w, " ")
                    if 식.search(글):
                        첫[말] = s
                        break
            if len(첫) > 1:
                나중 = max(첫.values(), key=lambda v: v["i"])
                self.걸("문장", "H27", "경고", 나중, "한 개념 두 이름 — %s" % " · ".join("「%s」(문단%d)" % (re.sub(r"\(\?:[^)]*\)\??", "", k), v["p"] + 1) for k, v in 첫.items()))

    def 상호(self):
        짧 = (self.문서 or {}).get("짧은이름") or self.회사
        정 = (self.문서 or {}).get("정식상호")
        if not 정 and self.가정경로 and os.path.isfile(self.가정경로):
            try:
                정 = (json.load(io.open(self.가정경로, encoding="utf-8")).get("메타") or {}).get("회사명")
            except ValueError:
                정 = None
        if not 정 or not 짧 or 정 == 짧:
            return
        정자리 = [s for s in self.문장들 if 정 in s["글"]]
        짧자리 = [s for s in self.문장들 if 짧 in s["글"].replace(정, " ")]
        if not 정자리:
            self.걸("문장", "H28", "정보", "전체", "정식 상호 「%s」가 이 초안에 없음 — 레터 머리 · 고정문이 먼저 쓰면 괜찮다" % 정)
            return
        if 짧자리 and 짧자리[0]["i"] < 정자리[0]["i"]:
            self.걸("문장", "H28", "경고", 짧자리[0], "상호 첫 등장이 짧은 이름 「%s」 — 첫 등장은 정식 상호 「%s」" % (짧, 정))
        for s in 정자리[1:]:
            self.걸("문장", "H28", "경고", s, "정식 상호 「%s」를 다시 씀 — 그 뒤는 「%s」" % (정, 짧))

    def 풀이수(self):
        용 = self.용어카드()
        쓴카드 = {c["id"] for s in self.문장들 for c in self.문장카드(s)}
        결론 = set(self.문서.get("결론에_나오는_용어", []) or [])
        밖 = sorted(u for u, cid in 용.items() if cid in 쓴카드 and u not in 결론 and self.첫등장(u, 용))
        if len(밖) > self.규["H33"]["상한"]:
            self.걸("문장", "H33", "경고", "전체", "결론 용어 밖의 풀이 %d개(%s) — 3분 레터는 %d개까지" % (len(밖), " · ".join(밖), self.규["H33"]["상한"]))

    def 일단계(self):
        """H31 — 1단계 정규식 패턴 가운데 정밀도를 재어 남긴 것. 겹침 규칙이 그 문장에 이미 걸렸으면 내지 않는다 · 한 문장에 경고 하나로 묶는다."""
        패 = [(p, re.compile(p["정규식"])) for p in self.규["H31"]["패턴"]]
        for s in self.문장들:
            if s["i"] in self.승인통과:
                continue
            이미 = self.위치걸림.get("문단%d·문장%d" % (s["p"] + 1, s["i"] + 1), set()) | self.위치걸림.get("문단%d" % (s["p"] + 1), set())
            if s["고정"]:                                # 고정문이 예외인 규칙(H9 · H10 의 면책 · 안내)과 겹치는 패턴은 그 고정문에 내지 않는다
                이미 = 이미 | {k for k in ("H9", "H10") if s["고정"] in set(self.규[k].get("예외고정", []))}
            이름 = [p["이름"] for p, r in 패 if r.search(s["글"]) and not (set(p.get("겹침", [])) & 이미)]
            if 이름:
                self.걸("문장", "H31", "경고", s, "1단계 패턴 %s" % " · ".join("「%s」" % x for x in 이름))

    # ══ 지표 · 내기 ══
    def 지표(self, 문들, 문단수, 글자):
        길 = [len(x) for x in 문들] or [0]
        길s = sorted(길)
        글자 = max(1, 글자)
        return {"문장": len(문들), "문단": 문단수, "글자": 글자, "평균": round(st.mean(길), 1), "중앙": st.median(길),
                "90분위": 길s[int(0.9 * (len(길s) - 1))], "최장": max(길), "문단당 문장": round(len(문들) / max(1, 문단수), 2),
                "물음 /천자": round(sum(x.endswith("?") for x in 문들) * 1000 / 글자, 2),
                "죠 /천자": round(sum(bool(re.search(r"죠[.?]?$", x)) for x in 문들) * 1000 / 글자, 2),
                "이 평가 /천자": round(sum(x.count("이 평가") for x in 문들) * 1000 / 글자, 2)}

    def 돌리기(self):
        self.사실층()
        self.문장층()
        self.새문장층()
        초지 = self.지표([s["글"] for s in self.문장들], len(self.문단), sum(len(s["글"]) for s in self.문장들))
        견지 = None
        견 = (self.규.get("지표") or {}).get("견줌")
        if 견 and os.path.isfile(_키트경로(견)):
            견글 = re.split(r"(?m)^## [^\n]*메모", 읽기(_키트경로(견)))[0]      # 견줌 글 끝의 메모 절(「## … 메모」)은 본문이 아니다 — 그 앞까지만 잰다
            견문단 = [p for p in re.split(r"\n\s*\n", 견글) if p.strip() and not p.lstrip().startswith(("#", ">", "|", "$$"))]
            견문 = []
            for p in 견문단:
                견문 += [x.strip() for x in re.split(r"(?<=[.?!])\s+", 공백(p)) if len(re.findall(r"[가-힣]", x)) >= 4]
            견지 = self.지표(견문, len(견문단), sum(len(x) for x in 견문))
        요약 = {}
        for x in self.걸림:
            k = "%s·%s" % (x["층"], x["등급"])
            요약[k] = 요약.get(k, 0) + 1
        self.결과 = {"판": 판, "초안": os.path.basename(self.초안경로), "층": self.층, "카드파일": self.카드경로 and os.path.basename(self.카드경로),
                   "옛꼴카드": self.옛꼴, "회차": self.회차, "문장": len(self.문장들), "카드": len(self.카드), "인용 대조": self.인용수,
                   "계산 재현": self.계산수, "장부 대조": self.장부수, "끈 검사": sorted(self.끔), "요약": dict(sorted(요약.items())), "지표": 초지,
                   "견줌 지표": 견지, "정보": self.정보, "복제 참조": getattr(self, "복제참조", []), "걸림": self.걸림}
        return self.결과

    def 내기(self, 밑=None):
        r = self.결과
        밑 = 밑 or os.path.splitext(self.초안경로)[0] + "_문체검사"
        io.open(밑 + ".json", "w", encoding="utf-8").write(json.dumps(r, ensure_ascii=False, indent=1))
        견 = r["견줌 지표"]
        줄 = ["# 문체 검사 — %s" % r["초안"], "",
              "층 %s · 문장 %d · 카드 %d · 인용 대조 %d · 계산 재현 %d · 장부 대조 %d" % (r["층"], r["문장"], r["카드"], r["인용 대조"], r["계산 재현"], r["장부 대조"]), "",
              "| 층 · 등급 | 건수 |", "|---|---:|"] + ["| %s | %d |" % kv for kv in r["요약"].items()]
        if r["정보"]:
            줄 += [""] + ["- %s" % x for x in r["정보"]]
        줄 += ["", "| 지표 | 이 초안 |" + (" 견줌 |" if 견 else ""), "|---|---:|" + ("---:|" if 견 else "")]
        줄 += ["| %s | %s |%s" % (k, v, (" %s |" % 견[k]) if 견 else "") for k, v in r["지표"].items()]
        줄 += ["", "| 층 | 코드 | 등급 | 위치 | 설명 | 문장 |", "|---|---|---|---|---|---|"]
        줄 += ["| %s | %s | %s | %s | %s | %s |" % (x["층"], x["코드"], x["등급"], x["위치"], x["설명"].replace("|", "/"), x["문장"].replace("|", "/")) for x in r["걸림"]]
        io.open(밑 + ".md", "w", encoding="utf-8").write("\n".join(줄) + "\n")
        return 밑


def main(argv=None):
    ap = argparse.ArgumentParser(description="레터 초안의 결정형 문체 검사(LLM 없음)")
    ap.add_argument("초안")
    ap.add_argument("카드", nargs="?", default=None, help="사실 카드 문서(.json). 비우면 --회차 의 _raw/사실카드.json, 그것도 없으면 문장 층만")
    ap.add_argument("--회차")
    ap.add_argument("--층", choices=["3분", "본편"])
    ap.add_argument("--규칙", action="append", default=[], help="규칙 파일 위에 덧씌울 JSON(여럿이면 차례로)")
    ap.add_argument("--참조", action="append", default=[], help="복제 검사 참조 「이름=경로」")
    ap.add_argument("--시험대", action="append", default=[], help="복제 검사 — 회귀 시험대 레터 glob(키트 기준 또는 절대)")
    ap.add_argument("--원천", action="append", default=[], help="복제 검사 — 겹쳐도 정보인 원천 「이름=경로」")
    ap.add_argument("--고정문", help="저자 승인 고정문 파일(규칙 파일 H17 을 덮음)")
    ap.add_argument("--가정")
    ap.add_argument("--장부")
    ap.add_argument("--감사", choices=["켬", "끔"], default="켬", help="F4 · F5 · F5b(카드 감사가 이미 봤으면 끔)")
    ap.add_argument("--낼", help="산출 밑경로(확장자 없이)")
    ap.add_argument("--조용히", action="store_true")
    a = ap.parse_args(argv)
    if not os.path.isfile(a.초안):
        print("입력 오류 — 초안이 없다: %s" % a.초안)
        return 2
    카드경로 = a.카드
    if not 카드경로 and a.회차 and os.path.isfile(os.path.join(a.회차, "_raw", "사실카드.json")):
        카드경로 = os.path.join(a.회차, "_raw", "사실카드.json")
    if 카드경로 and not os.path.isfile(카드경로):
        print("입력 오류 — 카드 문서가 없다: %s" % 카드경로)
        return 2
    try:
        규 = 규칙읽기(a.규칙)
        검 = 검사(a.초안, 규, 카드경로=카드경로, 회차=a.회차, 층=a.층, 가정=a.가정, 장부=a.장부, 참조=a.참조, 시험대=a.시험대, 원천=a.원천,
               고정문=a.고정문, 감사=(a.감사 == "켬"))
    except (ValueError, KeyError, re.error, OSError) as e:
        print("입력 오류 — %s" % e)
        return 2
    r = 검.돌리기()
    밑 = 검.내기(a.낼)
    if not a.조용히:
        print("문장 %d · 걸림 %d (%s) → %s.json · .md" % (r["문장"], len(r["걸림"]), r["요약"], 밑))
    return 1 if any(x["등급"] == "오류" for x in r["걸림"]) else 0


if __name__ == "__main__":
    sys.exit(main())

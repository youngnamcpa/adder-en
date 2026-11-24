# -*- coding: utf-8 -*-
"""구조펴기 — 줄 무늬 명세의 줄을 가정 파일의 `구조` 선언대로 편다 (W3a. 설계/6_산식_설계.md 4-1 · 4-2 · 4-4 · 4-5 · 6-5 · 9-5).

`기간` 이 열을 정하듯 `구조` 가 줄을 정한다. 줄 무늬 명세의 줄 하나는 **틀**일 수 있다 — 되풀이해 여러 줄이 되고, 구조에 따라 수식이 갈리고,
쓰지 않는 경로면 짓지 않는다. 줄무늬.읽기가 시트 파일을 읽은 바로 뒤에 이 모듈로 줄을 편다. 편 줄은 보통 줄과 같은 꼴이라 짓기 · 납품 배치 ·
범위 지문 · 좌표 지도는 편 줄만 본다.

줄에 적는 열쇠 (수식문법.md 15절)
  되풀이   "s" | ["s", "j"]   되풀이 변수 — 책.json 의 「되풀이」 표가 변수마다 구조의 목록을 댄다({"s": "매출구분", "j": "매출구분[].라인"}).
                             이어진 줄들이 같은 변수로 시작하는 「되풀이」를 적었으면 한 묶음으로 되풀이한다(s = 1 의 줄들, s = 2 의 줄들 …).
  묶음끝   true              이 줄에서 묶음을 끊는다(다음 줄이 같은 변수여도 새 묶음 — 줄마다 따로 되풀이할 때)
  조건     "식"              참일 때만 짓는다. 거짓이면 좌표 지도의 「안지은줄」에 남는다
  갈래     [{"조건": "식", …덮을 열쇠}, {"고름": "식", "값1": {…}, "값2": {…}, "그밖": {…}}]
                             참인 갈래마다 차례로 줄에 덮는다(무늬 · 글 · 값은 열쇠 단위로, 그 밖은 통째로). 「고름」은 식의 값과 같은 이름의 것 하나.
                             덮을 것에 "짓지않음": true 가 있으면 그 줄을 짓지 않는다
  시나리오 "예" | "공통"      예 = 비관 · 기준 · 낙관 세 줄 + 적용값 줄(가정 번호 500 미만은 머리 + 1 · 2 · 3, 500 이상은 머리 × 10 + 1 · 2 · 3).
                             「적용열」(열 구간)에 적용값 수식이 서고 세 줄의 그 열이 입력 칸이다. 쓰임이 「시점」 꼴(비관 · 기준 · 낙관 · 적용 별칭)인
                             줄은 세 줄을 짓지 않고 「적용」 칸의 수식만 짓는다. 공통 = 한 줄(그 줄이 곧 입력 칸 — 짓는 것 없음)
  빈칸허용 true              적용값 수식을 =IF(INDEX(…)="","",INDEX(…)) 로 짓는다(빈칸이 0 이 되지 않는다). 좌표 지도의 「줄속성」에 실린다
  표 · 표머리 "T1"           표 구획의 줄 · 그 표의 열 머리 줄(시트 머리의 「표」가 칸 이름을 댄다). 칸은 별칭으로 부른다 — [행]@$칸이름
  칸서식   {열 구간: 서식 이름}  그 칸만 다른 숫자 서식(표 구획의 줄은 시트 머리 「표」의 「서식」을 받는다)

자리 채우기 — 틀인 줄의 모든 글(id · 이름 · 무늬의 열쇠와 수식 …)에서
  {식}          식의 값(정수 · 글)을 넣는다                     S04R1{s}5 · [S12R{668+2*j}]@. · {p.이름}
  {식:03d}      숫자 서식을 붙여                                S04R{68+3*(s-1):03d}
  {모두 p 「+」: 항}             되풀이 변수 p 의 값마다 항을 지어 「+」로 잇는다. 하나도 없으면 0
  {모두 p 만 식 「+」: 항}       식이 참인 것만
  {모두 p 「」: -항}             잇는 글이 비고 항이 제 연산자(+ · -)로 시작하면 하나도 없을 때 빈 글(앞 피연산자에 이어 붙는 꼴)
식은 파이썬의 식 꼴이다 — 정수 · '글' · + - * // % · 견줌(== != < <= > >= in) · and or not · a if c else b · any/all/len/max/min/sum/int/str ·
(x.키 for x in 목록 if …). 이름은 되풀이 변수 · 구조의 맨 위 키(매출구분 · 환율 · 투자 …) · 「기간」(예측열수 · 실적열수 · 상세열수 · 수렴열수 ·
누계 · 잔여 · 이월 — 재무기준일 ≠ 평가기준일인 축이면 참, 2026-10-25 날짜 둘)이고, 점으로 안쪽 키를 읽는다(환율.경로 · s.경로 · p.리드타임). 목록의 항목은 셈에서는 그 「번호」다. 구조에 없는 키를 읽으면 오류다 —
기본값은 책.json 의 「구조기본」에 적는다(목록 항목의 기본은 "매출구분[]": {…}).

구조가 없는 읽기(틀 읽기 — 명세를 고치는 도구)는 책.json 의 「기본구조」(없으면 빈 구조)로 편다.
틀인 줄(위 열쇠나 { } 자리가 있는 줄)은 「다시쓰기」가 적힌 그대로 되돌려 적는다(덧붙인 이름을 맞춰 주지 않는다).
"""
import ast
import copy
import json
import os
import re
from collections import OrderedDict

from 공통 import 손오류, 배치오류

새행열쇠 = ("되풀이", "묶음끝", "조건", "갈래", "시나리오", "적용열", "빈칸허용", "표", "표머리", "칸서식")
틀열쇠 = ("되풀이", "묶음끝", "조건", "갈래", "시나리오", "표", "표머리", "칸서식", "빈칸허용")      # 하나라도 있으면 틀인 줄
기본시나리오칸 = "[$S12R013 시나리오 번호]@$값"
시나리오이름 = ("비관", "기준", "낙관")
시점별칭 = ("비관", "기준", "낙관", "적용")
새번호부터 = 500               # 가정 번호가 이보다 작으면 세 줄 = 머리 + 1 · 2 · 3, 크거나 같으면 머리 × 10 + 1 · 2 · 3 (4-2)
표칸묶음 = "표칸"               # 표 구획의 칸이 놓이는 열 묶음 — 값 열(시간축 열 · 값 열)과 그 뒤에 더한 덧 열
값열종류 = ("실적", "예측", "영구", "값")
덧열머리 = "표덧"
갈래덮는열쇠 = ("이름", "단위", "종류", "서식", "쓰임", "선", "들여", "굵게", "높이", "입력", "무늬", "글", "값", "축값", "병합", "메모", "적용열",
          "빈칸허용", "시나리오", "칸서식", "짓지않음")
_re행ID = re.compile(r"^([SX]\d+R)(\d+)$")


def 구조오류(설명, **덧):
    return 손오류(설명, 종류="구조", **덧)


# ───────────────────────── 선언을 감싼 값 ─────────────────────────
class 묶(dict):
    """구조의 사전 — 점으로 키를 읽는다(환율.경로). 없는 키는 오류다."""

    def __getattr__(self, 키):
        if 키.startswith("_"):
            raise AttributeError(키)
        if 키 not in self:
            raise 구조오류("구조에 「%s」 가 없다(%s) — 기본값은 책.json 의 「구조기본」에 적는다" % (
                키, " · ".join(str(k) for k in self) or "빈 사전"))
        return self[키]


class 항(int):
    """구조 목록의 항목 — 셈에서는 「번호」, 점으로 그 항목의 키를 읽는다(s.경로 · p.리드타임)."""

    def __new__(cls, 번호, 속=None):
        o = int.__new__(cls, 번호)
        o._속 = 속 or {}
        return o

    def __getattr__(self, 키):
        if 키.startswith("_"):
            raise AttributeError(키)
        if 키 not in self._속:
            raise 구조오류("구조의 목록 항목(번호 %d)에 「%s」 가 없다(%s) — 기본값은 책.json 의 「구조기본」의 \"목록이름[]\" 에 적는다" % (
                int(self), 키, " · ".join(str(k) for k in self._속) or "빈 항목"))
        return self._속[키]

    def __deepcopy__(self, memo):
        return self


def 싸기(v):
    if isinstance(v, dict):
        return 묶((k, 싸기(x)) for k, x in v.items())
    if isinstance(v, list):
        낸 = []
        for i, x in enumerate(v, 1):
            if isinstance(x, dict):
                번 = x.get("번호", i)
                낸.append(항(번 if isinstance(번, int) and not isinstance(번, bool) else i, 싸기(x)))
            elif isinstance(x, int) and not isinstance(x, bool):
                낸.append(항(x))
            else:
                낸.append(싸기(x))
        return 낸
    return v


def 기본채우기(준, 기본):
    """구조(준 것)에 「구조기본」을 채운다 — 사전은 키마다, 목록의 항목은 "이름[]" 의 기본으로. 기본에 목록 "이름[]" 만 있고 준 것이 없으면 빈 목록."""
    낸 = OrderedDict()
    준 = 준 if isinstance(준, dict) else {}
    for k, v in (기본 or {}).items():
        if k.endswith("[]"):
            if k[:-2] not in 준:
                낸[k[:-2]] = []
        elif isinstance(v, dict):
            낸[k] = 기본채우기(준.get(k), v)
        elif k not in 준:
            낸[k] = copy.deepcopy(v)
    for k, v in 준.items():
        if isinstance(v, dict):
            낸[k] = 기본채우기(v, (기본 or {}).get(k) if isinstance((기본 or {}).get(k), dict) else {})
        elif isinstance(v, list):
            항기본 = (기본 or {}).get(k + "[]")
            낸[k] = [기본채우기(x, 항기본) if isinstance(x, dict) and isinstance(항기본, dict) else copy.deepcopy(x) for x in v]
        else:
            낸[k] = v
    return 낸


_키트구조 = []


def 키트구조모듈():
    """키트의 `스크립트/엔진/구조.py`(구조의 기본값과 검증의 한 벌) → 모듈, 못 찾으면 None.

    기간축.py 를 찾는 것과 같은 자리에서 찾는다(환경 변수 「기간축곳」의 폴더 · ../키트/스크립트 · ../스크립트)."""
    if _키트구조:
        return _키트구조[0]
    import importlib
    import sys
    여기 = os.path.dirname(os.path.abspath(__file__))
    후보 = [os.path.dirname(os.environ["기간축곳"]) if os.environ.get("기간축곳") else None,
          os.path.normpath(os.path.join(여기, "..", "키트", "스크립트")), os.path.normpath(os.path.join(여기, "..", "스크립트"))]
    모듈 = None
    for 곳 in 후보:
        if 곳 and os.path.isfile(os.path.join(곳, "엔진", "구조.py")):
            if 곳 not in sys.path:
                sys.path.append(곳)
            try:
                모듈 = importlib.import_module("엔진.구조")
            except Exception:                                    # noqa: BLE001 — 키트의 엔진을 못 불러오면 채우지 않는다
                모듈 = None
            break
    _키트구조.append(모듈)
    return 모듈


def 키트채움(준):
    """가정의 `구조`(적힌 그대로) → 키트의 `구조틀` 로 기본값을 채운 것. **구조의 기본값은 키트의 `엔진/구조.py` 한 벌이다**(W3 맞물림).

    키트의 엔진을 못 찾거나 그 틀로 읽을 수 없는 구조(합성 명세의 지어낸 키 · 목록 밖 값)면 적힌 그대로 돌려준다 —
    그때는 책.json 의 「구조기본」만 채워진다. 구조 지문도 이 함수가 돌려준 것으로 낸다(`좌표지도.가정구조지문` · 키트 `좌표.지문구조`)."""
    if not isinstance(준, dict):
        return 준
    m = 키트구조모듈()
    if m is None or not hasattr(m, "기본채움"):
        return 준
    채운, 오류 = m.기본채움(준)
    return 준 if 오류 else 채운


def 가정읽기(무엇):
    """가정 사전 · 가정 파일 경로 → 가정 사전. 그 밖(기간 사전 · 축 객체 · None)이면 None."""
    if isinstance(무엇, str):
        try:
            with open(무엇, encoding="utf-8") as f:
                무엇 = json.load(f)
        except (OSError, ValueError):
            return None
    if isinstance(무엇, dict) and (isinstance(무엇.get("기간"), dict) or "구조" in 무엇 or "메타" in 무엇):
        return 무엇
    return None


# ───────────────────────── 식 ─────────────────────────
_허용노드 = (ast.Expression, ast.BoolOp, ast.And, ast.Or, ast.UnaryOp, ast.Not, ast.USub, ast.BinOp, ast.Add, ast.Sub, ast.Mult,
         ast.FloorDiv, ast.Mod, ast.Compare, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.In, ast.NotIn, ast.Name,
         ast.Load, ast.Store, ast.Attribute, ast.Constant, ast.Tuple, ast.List, ast.Call, ast.GeneratorExp, ast.ListComp,
         ast.comprehension, ast.IfExp)
_함수 = {"any": any, "all": all, "len": len, "max": max, "min": min, "sum": sum, "int": int, "str": str, "abs": abs}
_식기억 = {}


def 식(글, env):
    """식 글 → 값. 허용한 꼴만 받는다(이름 · 점 · 셈 · 견줌 · 논리 · 몇 함수 · 줄임 식)."""
    if not isinstance(글, str) or not 글.strip():
        raise 구조오류("식이 비었다: %r" % (글,))
    코드 = _식기억.get(글)
    if 코드 is None:
        try:
            나무 = ast.parse(글.strip(), mode="eval")
        except SyntaxError as e:
            raise 구조오류("식을 읽을 수 없다: 「%s」 — %s" % (글, e.msg))
        for 마디 in ast.walk(나무):
            if not isinstance(마디, _허용노드):
                raise 구조오류("식에 쓸 수 없는 꼴이 있다: 「%s」 (%s)" % (글, type(마디).__name__))
            if isinstance(마디, ast.Attribute) and 마디.attr.startswith("_") or isinstance(마디, ast.Name) and 마디.id.startswith("_"):
                raise 구조오류("식에 밑줄로 시작하는 이름은 못 쓴다: 「%s」" % 글)
            if isinstance(마디, ast.Call) and not (isinstance(마디.func, ast.Name) and 마디.func.id in _함수 and not 마디.keywords):
                raise 구조오류("식에서 부를 수 있는 함수는 %s 뿐이다: 「%s」" % (" · ".join(_함수), 글))
            if isinstance(마디, ast.Constant) and not (마디.value is None or isinstance(마디.value, (int, str, bool))):
                raise 구조오류("식의 상수는 정수 · 글 · 참거짓만 쓴다: 「%s」" % 글)
        코드 = _식기억[글] = compile(나무, "<식>", "eval")
    try:
        return eval(코드, dict(env, __builtins__={}, **_함수))      # noqa: S307 — 위에서 꼴을 가렸다
    except 배치오류:
        raise
    except NameError as e:
        raise 구조오류("식 「%s」 — 모르는 이름이다(%s). 쓸 수 있는 이름: %s" % (글, e, " · ".join(k for k in env if not k.startswith("_"))))
    except Exception as e:      # noqa: BLE001
        raise 구조오류("식 「%s」 을 셈하지 못했다 — %s: %s" % (글, type(e).__name__, e))


_re모두 = re.compile(r"^모두\s+([^\s「]+)(?:\s+만\s+(.+?))?\s*「([^」]*)」\s*:(.*)$", re.S)
_re서식꼬리 = re.compile(r"^(.*):(0?\d*d)$", re.S)


def _짝괄호(글, i):
    """글[i] 가 「{」 일 때 짝인 「}」 의 자리. 없으면 오류."""
    깊이 = 0
    for j in range(i, len(글)):
        if 글[j] == "{":
            깊이 += 1
        elif 글[j] == "}":
            깊이 -= 1
            if 깊이 == 0:
                return j
    raise 구조오류("「{」 의 짝이 없다: %s" % 글[i:i + 60])


class 선언:
    """한 번의 읽기에 쓰는 구조 선언 — 구조(기본을 채운 것) · 기간 · 되풀이 표."""

    def __init__(self, 책, 가정=None, 축=None):
        self.되풀이표 = OrderedDict(책.get("되풀이") or {})
        준 = 가정.get("구조") if isinstance(가정, dict) and isinstance(가정.get("구조"), dict) else None
        self.틀읽기 = 준 is None
        준 = 키트채움(준)             # 키트의 구조틀로 기본값을 채운다 — 책.json 의 「구조기본」은 그 틀에 없는 키(합성 명세)만 채운다
        self.준구조 = 준 if 준 is not None else (책.get("기본구조") or {})
        # 틀 읽기(가정 없이 — 범위 지문 · 함수 목록 · 기본 기간으로 짓기)에서도 조건의 식이 구조의 키를 읽는다 — 키트의 기본값을 채워 둔다
        self.구조 = 기본채우기(키트채움(self.준구조) if self.틀읽기 else self.준구조, 책.get("구조기본") or {})
        self.가정 = 가정 if isinstance(가정, dict) else {}
        self.축 = 축
        self.시나리오칸 = 책.get("시나리오칸") or 기본시나리오칸
        self.괄호푼다 = any(k in 책 for k in ("되풀이", "구조기본", "기본구조"))      # 틀의 열쇠 없이 { } 자리만 있는 줄도 틀로 보는가
        self.쓴경로 = OrderedDict()      # 가정 파일에서 읽은 값(「@가정:경로」) — 구조 지문의 재료
        기간 = OrderedDict(예측열수=0, 실적열수=0, 상세열수=0, 수렴열수=0, 누계=False, 잔여=False, 열수=0,
                         이월=bool(축 and (축.get("이월연수") or 0) > 0))       # 날짜 둘 — 엔진 `엔진.읽개.이월판` 과 같은 판정
        self.예측열 = []
        if 축:
            for ID in 축.get("열") or ():
                속 = (축.get("속성") or {}).get(ID) or {}
                구분, 갈래 = 속.get("구분"), 속.get("종류")
                기간["열수"] += 1
                if 구분 == "예측":
                    기간["예측열수"] += 1
                    self.예측열.append(ID)
                    기간["상세열수" if 속.get("구간") != "수렴" else "수렴열수"] += 1
                elif 구분 == "실적":
                    기간["실적열수"] += 1
                기간["누계"] = 기간["누계"] or 갈래 == "누계실적"
                기간["잔여"] = 기간["잔여"] or 갈래 == "잔여예측"
        self.기간 = 기간
        self.바탕 = OrderedDict((k, 싸기(v)) for k, v in self.구조.items())
        self.바탕["기간"] = 묶(기간)
        for 변수 in self.되풀이표:
            if 변수 in self.바탕 or 변수 in _함수:
                raise 구조오류("책.json 의 되풀이 변수 「%s」 가 구조의 맨 위 키(또는 함수 이름)와 겹친다" % 변수)

    # ── 되풀이 ──
    def _목록(self, 뿌리, 길):
        v = 뿌리
        for 키 in [x for x in 길.split(".") if x]:
            if isinstance(v, 항):
                v = v._속
            if not isinstance(v, dict) or 키 not in v:
                return []
            v = v[키]
        return v if isinstance(v, list) else []

    def _끝값(self, v, env):
        if isinstance(v, int) and not isinstance(v, bool):
            return v
        if isinstance(v, str) and v.startswith("@가정:"):
            길, 값 = v[len("@가정:"):], self.가정
            for 키 in 길.split("."):
                값 = 값.get(키) if isinstance(값, dict) else None
            if isinstance(값, dict) and "기준" in 값:      # 시나리오마다 다른 값은 구조를 정할 수 없다 — 기준 값을 쓴다
                값 = 값["기준"]
            if isinstance(값, float) and float(값) == int(값):
                값 = int(값)
            if not (isinstance(값, int) and not isinstance(값, bool)):
                if self.틀읽기 and 값 is None:
                    값 = 0
                else:
                    raise 구조오류("가정 파일의 「%s」 가 정수가 아니다: %r (되풀이의 끝값으로 읽는다)" % (길, 값))
            self.쓴경로[길] = 값
            return 값
        if isinstance(v, str):
            값 = 식(v, env)
            if isinstance(값, int) and not isinstance(값, bool):
                return int(값)
        raise 구조오류("되풀이의 끝값은 정수 · 식 · 「@가정:경로」 로 적는다: %r" % (v,))

    def 되풀이값(self, 변수, env):
        """되풀이 변수 → [{변수: 값, (부모 변수: 값)}] — 그 변수가 도는 값마다 더할 이름표."""
        정의 = self.되풀이표.get(변수)
        if 정의 is None:
            raise 구조오류("되풀이 변수 「%s」 를 모른다 — 책.json 의 「되풀이」 에 적는다(지금: %s)" % (변수, " · ".join(self.되풀이표) or "없음"))
        if isinstance(정의, dict):
            모름 = [k for k in 정의 if k not in ("부터", "까지", "메모")]
            if 모름 or "까지" not in 정의:
                raise 구조오류("되풀이 변수 「%s」 의 정의는 {\"부터\": a, \"까지\": b} 로 적는다" % 변수)
            return [{변수: 항(k)} for k in range(self._끝값(정의.get("부터", 1), env), self._끝값(정의["까지"], env) + 1)]
        if not isinstance(정의, str):
            raise 구조오류("되풀이 변수 「%s」 의 정의는 구조의 목록 경로(글)나 {부터, 까지} 로 적는다" % 변수)
        if 정의 == "@예측":
            return [{변수: 항(k, {"열": ID})} for k, ID in enumerate(self.예측열, 1)]
        if "[]." in 정의:
            부모길, 자식 = 정의.split("[].", 1)
            부모변수 = next((v for v, d in self.되풀이표.items() if d == 부모길), None)
            부모들 = [env[부모변수]] if 부모변수 and 부모변수 in env else self._목록(self.바탕, 부모길)
            낸 = []
            for 부 in 부모들:
                for x in self._목록(부, 자식):
                    낸.append(dict({변수: x}, **({부모변수: 부} if 부모변수 else {})))
            return 낸
        return [{변수: x} for x in self._목록(self.바탕, 정의)]

    # ── 자리 채우기 ──
    def 채우기(self, 글, env):
        """글의 { } 자리를 채운 글."""
        if not isinstance(글, str) or "{" not in 글:
            return 글
        낸, i = [], 0
        while True:
            a = 글.find("{", i)
            if a < 0:
                낸.append(글[i:])
                break
            낸.append(글[i:a])
            b = _짝괄호(글, a)
            낸.append(self._자리(글[a + 1:b], env))
            i = b + 1
        return "".join(낸)

    def _자리(self, 속, env):
        m = _re모두.match(속)
        if m:
            변수, 조건, 잇는글, 몸 = m.group(1), m.group(2), m.group(3), m.group(4)
            항들 = []
            for 묶임 in self.되풀이값(변수, env):
                env2 = dict(env, **묶임)
                if 조건 is None or 식(조건, env2):
                    항들.append(self.채우기(몸.strip(), env2))
            if 항들:
                return 잇는글.join(항들)
            # 잇는 글이 비고 항이 제 연산자(「+…」 · 「-…」)를 달고 오면 앞 피연산자에 이어 붙는 꼴이다 — 하나도 없으면 빈 글
            # (「…@.{모두 c 만 … 「」: -[행]@.}」 에 0 을 적으면 「@.0」 이 되어 손 수식을 풀지 못한다). 그 밖은 0 (홀로 선 합)
            return "" if not 잇는글 and 몸.strip()[:1] in ("+", "-") else "0"
        if 속.startswith("모두 ") or 속.startswith("모두\t"):
            raise 구조오류("「{모두 …}」 를 읽을 수 없다: {%s} — {모두 변수 [만 식] 「잇는 글」: 항} 으로 적는다" % 속[:60])
        꼴 = None
        m = _re서식꼬리.match(속)
        if m:
            속, 꼴 = m.group(1), m.group(2)
        v = 식(속, env)
        if isinstance(v, bool) or v is None:
            raise 구조오류("자리 {%s} 의 값이 정수 · 글이 아니다: %r" % (속, v))
        if isinstance(v, int):
            return format(int(v), 꼴 or "d")
        if isinstance(v, str):
            if 꼴:
                raise 구조오류("자리 {%s:%s} — 글에는 숫자 서식을 못 붙인다" % (속, 꼴))
            return v
        raise 구조오류("자리 {%s} 의 값이 정수 · 글이 아니다: %r" % (속, v))

    def 모두채우기(self, v, env):
        """사전 · 목록 · 글을 속까지 채운다(사전의 열쇠도)."""
        if isinstance(v, str):
            return self.채우기(v, env)
        if isinstance(v, list):
            return [self.모두채우기(x, env) for x in v]
        if isinstance(v, dict):
            낸 = OrderedDict()
            for k, x in v.items():
                k2 = self.채우기(k, env)
                if k2 in 낸:
                    raise 구조오류("자리를 채우니 열쇠가 겹친다: 「%s」" % k2)
                낸[k2] = self.모두채우기(x, env)
            return 낸
        return v


def _조각잇기(d):
    """조각 목록으로 적은 글(이름 · 단위 · 메모 · 무늬와 글의 값)을 글 하나로 — 갈래 안쪽까지. { } 자리가 조각에 걸쳐 있어도 채워지게."""
    def 잇(v):
        return "".join(v) if isinstance(v, list) and v and all(isinstance(x, str) for x in v) else v
    for 키 in ("이름", "단위", "메모"):
        if 키 in d:
            d[키] = 잇(d[키])
    for 키 in ("무늬", "글"):
        if isinstance(d.get(키), dict):
            for k in list(d[키]):
                d[키][k] = 잇(d[키][k])
    for 한 in d.get("갈래") or () if isinstance(d.get("갈래"), list) else ():
        if isinstance(한, dict):
            if "고름" in 한:
                for k, v in 한.items():
                    if isinstance(v, dict):
                        _조각잇기(v)
            else:
                _조각잇기(한)
    return d


def 괄호있나(v):
    if isinstance(v, str):
        return "{" in v
    if isinstance(v, dict):
        return any("{" in k or 괄호있나(x) for k, x in v.items())
    if isinstance(v, list):
        return any(괄호있나(x) for x in v)
    return False


def 틀인가(낸, 괄호=True):
    """틀인 줄인가 — 틀의 열쇠가 있거나, (괄호=True 면) 글에 { } 자리가 있다.

    { } 자리만 있는 줄은 책.json 에 「되풀이」·「구조기본」·「기본구조」 가운데 하나라도 적은 명세에서만 틀로 본다(선언.괄호푼다) —
    옛 스캐폴드에서 뽑은 명세의 수식에는 엑셀의 배열 상수({1,2,3})가 있다. 그런 명세의 중괄호는 건드리지 않는다."""
    return any(k in 낸 for k in 틀열쇠) or (괄호 and 괄호있나(dict(낸)))


def _되풀이목록(낸):
    되 = 낸.get("되풀이")
    if 되 is None:
        return []
    if isinstance(되, str):
        return [되]
    if isinstance(되, list) and all(isinstance(x, str) for x in 되):
        return list(되)
    raise 구조오류("%s 의 「되풀이」 는 변수 이름 하나나 그 목록으로 적는다" % 낸.get("id"))


def 세줄번호(rid):
    """가정 머리 줄의 행 ID → 비관 · 기준 · 낙관 세 줄의 행 ID (4-2). 번호 꼴이 아니면 None."""
    m = _re행ID.match(rid or "")
    if not m:
        return None
    n, 폭 = int(m.group(2)), len(m.group(2))
    if n < 새번호부터:
        return ["%s%0*d" % (m.group(1), 폭, n + k) for k in (1, 2, 3)]
    return ["%s%d" % (m.group(1), n * 10 + k) for k in (1, 2, 3)]


def 표칸들(정의, 선):
    """시트 머리의 표 정의 → 칸 이름 목록. 칸에 {"되풀이": 변수, "칸": "Y{y}"} 를 적으면 그 변수의 값마다 한 칸."""
    칸 = []
    for 한 in 정의.get("칸") or ():
        if isinstance(한, str):
            칸.append(선.채우기(한, 선.바탕))
        elif isinstance(한, dict) and isinstance(한.get("되풀이"), str) and isinstance(한.get("칸"), str):
            for 묶임 in 선.되풀이값(한["되풀이"], 선.바탕):
                칸.append(선.채우기(한["칸"], dict(선.바탕, **묶임)))
        else:
            raise 구조오류("표의 「칸」 은 칸 이름(글)이나 {\"되풀이\": 변수, \"칸\": \"이름{변수}\"} 로 적는다: %r" % (한,))
    if len(set(칸)) != len(칸) or not all(칸):
        raise 구조오류("표의 칸 이름이 비었거나 겹친다: %s" % " · ".join(칸))
    return 칸


# ───────────────────────── 시트의 줄을 편다 ─────────────────────────
class _편이:
    def __init__(self, 머리, 선, 오류, 읽기오류):
        self.머리, self.선, self.오류, self.읽기오류 = 머리, 선, 오류, 읽기오류
        self.sid = 머리.get("시트")
        self.낸 = []
        self.안지은 = OrderedDict()      # 행 ID(자리를 못 채우면 틀의 id) → 까닭
        self.틀 = []                     # 되풀이 틀마다 {"id": 틀의 id, "되풀이": […], "지은": [행 ID …]}
        self._틀기록 = {}
        self.표정의 = 머리.get("표") if isinstance(머리.get("표"), dict) else {}
        self.표칸 = {}                   # 표 이름 → 칸 이름 목록(처음 쓰일 때 편다)
        self.표줄 = OrderedDict()        # 표 이름 → [행 ID …]
        self.쓰임표 = 머리.get("쓰임") or {}

    def 틀림(self, 낸, 설명):
        self.오류.append(self.읽기오류(낸, 설명))

    def 묶어펴기(self, 줄들, 깊이, env):
        i = 0
        while i < len(줄들):
            낸 = 줄들[i]
            try:
                되 = _되풀이목록(낸)
            except 배치오류 as e:
                self.틀림(낸, e.오류목록[0]["설명"])
                i += 1
                continue
            if len(되) <= 깊이:
                self.한줄(낸, env)
                i += 1
                continue
            변수, j = 되[깊이], i
            while j < len(줄들):
                try:
                    되2 = _되풀이목록(줄들[j])
                except 배치오류:
                    break
                if len(되2) <= 깊이 or 되2[:깊이 + 1] != 되[:깊이 + 1]:
                    break
                j += 1
                if 줄들[j - 1].get("묶음끝") and len(되2) == 깊이 + 1:
                    break
            try:
                값들 = self.선.되풀이값(변수, env)
            except 배치오류 as e:
                self.틀림(낸, e.오류목록[0]["설명"])
                값들 = []
            if not 값들:
                for 한 in 줄들[i:j]:
                    self._기록(한)
                    self.안지은.setdefault(한.get("id"), "되풀이 「%s」 — 구조에 선언한 항목이 없다" % 변수)
            for 묶임 in 값들:
                self.묶어펴기(줄들[i:j], 깊이 + 1, dict(env, **묶임))
            i = j

    def _기록(self, 낸):
        if 낸.get("되풀이") is None:
            return None
        키 = id(낸)
        if 키 not in self._틀기록:
            self._틀기록[키] = {"id": 낸.get("id"), "되풀이": _되풀이목록(낸), "지은": []}
            self.틀.append(self._틀기록[키])
        return self._틀기록[키]

    def 한줄(self, 낸, env):
        if not 틀인가(낸, self.선.괄호푼다):
            self.낸.append(낸)
            return
        기록 = self._기록(낸)
        try:
            for 새 in self._틀펴기(낸, env):
                한 = type(낸)(새)
                한.파일, 한.줄번호, 한.틀줄 = getattr(낸, "파일", None), getattr(낸, "줄번호", None), 낸
                self.낸.append(한)
                if 기록 is not None and not 새.get("_세줄"):
                    기록["지은"].append(새["id"])
                한.pop("_세줄", None)
        except 배치오류 as e:
            for o in e.오류목록:
                self.틀림(낸, "%s — %s" % (낸.get("id"), o["설명"]))

    def _틀펴기(self, 낸, env):
        선 = self.선
        d = _조각잇기(json.loads(json.dumps(낸, ensure_ascii=False), object_pairs_hook=OrderedDict))
        rid = 선.채우기(d.get("id"), env)
        for 키 in ("묶음끝",):
            if 키 in d and not isinstance(d[키], bool):
                raise 구조오류("「%s」 는 true / false 로 적는다" % 키)
        if d.get("조건") is not None and not 식(d["조건"], env):
            self.안지은[rid] = "조건 「%s」 이 거짓" % d["조건"]
            return []
        # 갈래 — 참인 것마다 차례로 덮는다
        갈래 = d.get("갈래")
        if 갈래 is not None and not (isinstance(갈래, list) and all(isinstance(x, dict) for x in 갈래)):
            raise 구조오류("「갈래」 는 [{\"조건\": 식, …} | {\"고름\": 식, 값: {…}}] 로 적는다")
        for 한 in 갈래 or ():
            if "고름" in 한:
                값 = 식(한["고름"], env)
                값 = "%d" % 값 if isinstance(값, int) and not isinstance(값, bool) else 값
                if isinstance(값, str) and 값 in 한 and 값 not in ("고름", "그밖", "메모"):
                    덮을 = 한[값]
                elif "그밖" in 한:
                    덮을 = 한["그밖"]
                else:
                    raise 구조오류("갈래의 고름 「%s」 = %r — 그 값의 갈래가 없다(%s). 아무것도 덮지 않을 것이면 \"그밖\": {} 를 적는다" % (
                        한["고름"], 값, " · ".join(k for k in 한 if k not in ("고름", "메모"))))
            else:
                모름 = [k for k in 한 if k not in 갈래덮는열쇠 + ("조건",)]
                if 모름:
                    raise 구조오류("갈래의 모르는 열쇠: 「%s」 (쓸 수 있는 열쇠: 조건 · 고름 · %s)" % (모름[0], " · ".join(갈래덮는열쇠)))
                if 한.get("조건") is not None and not 식(한["조건"], env):
                    continue
                덮을 = OrderedDict((k, v) for k, v in 한.items() if k != "조건")
            if not isinstance(덮을, dict) or [k for k in 덮을 if k not in 갈래덮는열쇠]:
                raise 구조오류("갈래가 덮을 것은 {%s} 가운데서 적는다: %s" % (" · ".join(갈래덮는열쇠), json.dumps(덮을, ensure_ascii=False)[:80]))
            for k, v in 덮을.items():
                if k in ("무늬", "글", "값", "칸서식") and isinstance(v, dict):
                    안 = d.setdefault(k, OrderedDict())
                    for 열쇠, x in v.items():
                        if x is None:
                            안.pop(열쇠, None)
                        else:
                            안[열쇠] = x
                else:
                    d[k] = v
        if d.pop("짓지않음", None):
            self.안지은[rid] = "갈래가 짓지 않는다"
            return []
        for 키 in ("되풀이", "묶음끝", "조건", "갈래"):
            d.pop(키, None)
        # 시나리오 · 빈칸허용 — 적용값 수식과 세 줄
        시나 = d.get("시나리오")
        if 시나 is not None and 시나 not in ("예", "공통"):
            raise 구조오류("「시나리오」 는 \"예\" · \"공통\" 으로 적는다: %r" % (시나,))
        if d.get("빈칸허용") is not None and not isinstance(d["빈칸허용"], bool):
            raise 구조오류("「빈칸허용」 은 true / false 로 적는다")
        세줄, env2 = [], env
        if 시나 == "예":
            시점꼴 = d.get("쓰임") and all(k in (self.쓰임표.get(d["쓰임"]) or {}) for k in 시점별칭)
            if 시점꼴:
                env2 = dict(env, 머리=rid)
                if "적용" not in (d.get("무늬") or {}):
                    색 = "INDEX([%s]@$비관:[%s]@$낙관,%s)" % (rid, rid, 선.시나리오칸)
                    d.setdefault("무늬", OrderedDict())["적용"] = ('=IF(%s="","",%s)' % (색, 색)) if d.get("빈칸허용") else "=" + 색
                d.pop("적용열", None)
            else:
                세 = 세줄번호(rid)
                if 세 is None:
                    raise 구조오류("「시나리오」 를 적은 줄의 id 가 행 ID 꼴이 아니다: %s" % rid)
                적용열 = d.pop("적용열", None)
                if not isinstance(적용열, str) or not 적용열:
                    raise 구조오류("「시나리오」: \"예\" 인 줄에는 「적용열」(적용값 수식이 서는 열 구간 — 예측 · 예측영구 …)을 적는다")
                env2 = dict(env, 머리=rid, 비관=세[0], 기준=세[1], 낙관=세[2])
                색 = "INDEX([%s 비관]@.:[%s 낙관]@.,%s)" % (세[0], 세[2], 선.시나리오칸)
                if 적용열 in (d.get("무늬") or {}):
                    raise 구조오류("「적용열」 %s 에 무늬가 이미 적혀 있다 — 적용값 수식은 생성기가 짓는다" % 적용열)
                새무늬 = OrderedDict([(적용열, ('=IF(%s="","",%s)' % (색, 색)) if d.get("빈칸허용") else "=" + 색)])
                새무늬.update(d.get("무늬") or {})
                d["무늬"] = 새무늬
                for 번, 이름 in zip(세, 시나리오이름):
                    한 = OrderedDict([("id", 번), ("이름", 이름), ("종류", "입력")])
                    if d.get("서식"):
                        한["서식"] = d["서식"]
                    한["들여"] = 2
                    한["입력"] = [적용열]
                    한["_세줄"] = True
                    세줄.append(한)
        elif "적용열" in d:
            raise 구조오류("「적용열」 은 「시나리오」: \"예\" 인 줄에만 적는다")
        d = 선.모두채우기(d, env2)
        if not _re행ID.match(d.get("id") or "") or not d["id"].startswith(self.sid + "R"):
            raise 구조오류("자리를 채운 행 ID 가 이 시트(%s)의 꼴이 아니다: %r" % (self.sid, d.get("id")))
        # 표 구획 — 표의 줄 · 표의 열 머리 줄
        표이름 = d.get("표") or d.get("표머리")
        if 표이름 is not None:
            if d.get("표") is not None and d.get("표머리") is not None:
                raise 구조오류("「표」 와 「표머리」 를 한 줄에 함께 적지 않는다")
            if 표이름 not in self.표정의:
                raise 구조오류("표 「%s」 가 이 시트 머리의 「표」 에 없다(%s)" % (표이름, " · ".join(self.표정의) or "표가 없다"))
            if d.get("쓰임") not in (None, 표이름):
                raise 구조오류("표의 줄에는 「쓰임」 을 적지 않는다(칸의 별칭 묶음은 표가 준다)")
            if 표이름 not in self.표칸:
                self.표칸[표이름] = 표칸들(self.표정의[표이름], 선)
            d["쓰임"] = 표이름
            self.표줄.setdefault(표이름, []).append(d["id"])
            정의 = self.표정의[표이름]
            if d.get("표머리") is not None:
                d.setdefault("종류", "머리")
                글 = OrderedDict((칸, (정의.get("머리글") or {}).get(칸, 칸)) for 칸 in self.표칸[표이름])
                글.update(d.get("글") or {})
                d["글"] = 글
            elif isinstance(정의.get("서식"), dict):
                칸서식 = OrderedDict((k, v) for k, v in 정의["서식"].items() if k in self.표칸[표이름])
                칸서식.update(d.get("칸서식") or {})
                d["칸서식"] = 칸서식
        if d.get("칸서식") is not None and not (isinstance(d["칸서식"], dict) and all(isinstance(v, str) for v in d["칸서식"].values())):
            raise 구조오류("「칸서식」 은 {열 구간: 서식 이름} 으로 적는다")
        return [d] + 세줄


def 시트펴기(머리, 줄들, 선, 오류, 읽기오류):
    """시트의 날것 줄 → (편 줄, 정보). 틀이 아닌 줄은 받은 객체 그대로다(차례도).

    읽기오류(낸, 설명) : 오류 한 건을 짓는 함수(파일 이름 · 줄 번호를 붙인다).
    정보 = {"안지은": {행 ID: 까닭}, "틀": [{id, 되풀이, 지은}], "표칸": {표: [칸 …]}, "표줄": {표: [행 ID …]}}
    """
    편 = _편이(머리, 선, 오류, 읽기오류)
    표 = 머리.get("표")
    if 표 is not None and not (isinstance(표, dict) and all(isinstance(v, dict) and isinstance(v.get("칸"), list) for v in 표.values())):
        오류.append(읽기오류(머리, "시트 머리의 「표」 는 {표 이름: {\"칸\": [칸 이름 …], \"머리글\": {…}, \"서식\": {…}}} 로 적는다"))
        편.표정의 = {}
    for 이름, 정의 in 편.표정의.items():
        모름 = [k for k in 정의 if k not in ("칸", "머리글", "서식", "메모")]
        if 모름:
            오류.append(읽기오류(머리, "표 「%s」 의 모르는 열쇠: 「%s」 (칸 · 머리글 · 서식 · 메모)" % (이름, 모름[0])))
        if 이름 in (머리.get("쓰임") or {}):
            오류.append(읽기오류(머리, "표 이름 「%s」 가 이 시트의 쓰임 이름과 겹친다" % 이름))
    편.묶어펴기(줄들, 0, dict(선.바탕))
    return 편.낸, {"안지은": 편.안지은, "틀": 편.틀, "표칸": 편.표칸, "표줄": 편.표줄}


def 표입히기(머리, 표칸):
    """표 구획이 선 시트의 머리(기간을 입힌 뒤)에 표의 칸 별칭(쓰임)과 묶음 「표칸」, 모자라는 덧 열을 더한다 — 머리를 고쳐 돌려준다.

    표의 칸은 그 시트의 첫 값 열(시간축 열 · 값 열)부터 오른쪽으로 놓인다. 칸이 값 열보다 많으면 마지막 값 열 바로 뒤에 덧 열(표덧1 …)을
    더한다(4-4 — 칸 수는 시간축의 열 수와 무관하다. 인쇄 영역은 값 열의 끝까지라 덧 열을 따라 넓어진다).
    """
    if not 표칸:
        return 머리
    열 = 머리.get("열") or []
    값자리 = [i for i, c in enumerate(열) if c.get("종류", "기타") in 값열종류]
    if not 값자리:
        raise 구조오류("%s — 표 구획을 놓을 값 열(종류 %s)이 없다" % (머리.get("시트"), " · ".join(값열종류)))
    모자람 = max(len(칸) for 칸 in 표칸.values()) - len(값자리)
    if 모자람 > 0:
        있는 = {c["id"] for c in 열}
        끝 = 열[값자리[-1]]
        덧 = []
        for k in range(1, 모자람 + 1):
            if 덧열머리 + str(k) in 있는:
                raise 구조오류("%s — 덧 열 이름 「%s%d」 이 이미 있는 열 ID 와 겹친다" % (머리.get("시트"), 덧열머리, k))
            한 = OrderedDict(id=덧열머리 + str(k), 종류="값")
            if 끝.get("폭"):
                한["폭"] = 끝["폭"]
            덧.append(한)
        머리["열"] = 열[:값자리[-1] + 1] + 덧 + 열[값자리[-1] + 1:]
    있는종류 = {c.get("종류", "기타") for c in 머리["열"]}
    묶음 = OrderedDict(머리.get("묶음") or {})
    if 표칸묶음 in 묶음 and 묶음[표칸묶음] != [k for k in 값열종류 if k in 있는종류]:
        raise 구조오류("%s — 묶음 이름 「%s」 는 표 구획이 쓴다" % (머리.get("시트"), 표칸묶음))
    묶음[표칸묶음] = [k for k in 값열종류 if k in 있는종류]
    머리["묶음"] = 묶음
    쓰임 = OrderedDict(머리.get("쓰임") or {})
    for 이름, 칸 in 표칸.items():
        쓰임[이름] = OrderedDict((한, "%s.%d" % (표칸묶음, k)) for k, 한 in enumerate(칸, 1))
    머리["쓰임"] = 쓰임
    return 머리

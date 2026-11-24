# -*- coding: utf-8 -*-
"""레터교열 — 레터 v27 「교열 검토」 단계의 도구(문장 원칙 열셋 · 다시 쓰기 고리 · 교열 대장).

글을 쓴 호출과 다른 호출(교열자 — `.claude/갈래/L2_레터교열.md`)이 레터를 읽고 걸리는 문장을 표시하면, 이 도구가 표시를 검사하고
**표시된 문장만** 다시 쓴다. 원고 문장은 원고 묶음(`_raw/레터원고/*.json`)을 고쳐 넣기부터 다시 돌고, 코드 문장은 편집 목록의
「다시쓰기」 항목으로 편집 단계(`회차실행.편집적용`)가 적용한다. 두 번 고친 뒤에도 남은 표시는 목록으로 사람에게 넘긴다.
이 도구는 문장을 짓지 않는다 — 교열자가 낸 고친 문장이 조건(숫자 · 열쇠 말 · 꼴)에 맞나 보고 옮길 뿐이다. 회사 · 업종 이름은 이 파일에 없다.

    python 스크립트/레터교열.py 준비 레터_초안.md [--회 1]         # 구조 검사 자리 · 열쇠 줄 · 산문 보기 → _raw/교열/준비_<회>.json · 산문_<회>.txt
    python 스크립트/레터교열.py 검사 _raw/교열/표시_1.json         # 표시의 꼴 · 원문 · 몫 · 고친 문장의 조건(거절이 있으면 종료 1)
    python 스크립트/레터교열.py 고리 _raw/교열/표시_1.json         # 원고 → 묶음 고침 · 코드 → 편집 목록 「다시쓰기」 · 기록 · 교열 대장
    python 스크립트/레터교열.py 남은                               # 두 번 고친 뒤 남은 표시 → _raw/교열/남은목록.md · .json
    python 스크립트/레터교열.py 대장 [회차 폴더 …]                 # 교열 대장 셈(폴더 여럿이면 합친 셈 — 레터 묶음의 유형 분포)
    python 스크립트/레터교열.py 확인                               # 회차실행 「교열」 단계와 같은 확인(기록이 섰나)
    python 스크립트/레터교열.py 되돌림 --회 1 --줄 15,1530 --까닭 "게이트 ⑭"   # 게이트가 막은 다시 쓰기만 옛 글로(남은 목록 · 사람 몫)

회차 폴더는 지금 폴더(또는 `--회차`). 레터 장부는 `레터_초안.장부.json`(또는 `--장부`).

표시 파일(형식 「교열표시/1」) — {"레터", "글해시", "회", "표시": [{"줄", "원문", "원칙": [번호], "유형", "까닭", "고친문장"}], "넘김": [{"줄", "지표", "까닭"}]}
  원문 — 레터의 글자 그대로(문장 하나 또는 이어진 문장 몇). 고친문장 — 빈 글이면 그 문장을 지우고, null 이면 표시만 한다(사람 몫).
  몫(코드 · 원고 · 섞임) · 절 · 줄은 이 도구가 단다(장부의 원고 조각 — `레터구조.원고판`).

다시 쓰기의 숫자 조건(`숫자조건`) — 고친 문장의 숫자(자리표시를 편 뒤)는 원문의 숫자 안에서만 나온다. 새 숫자 · 바뀐 숫자는 없고,
  단위가 붙은 값은 단위까지 같다(부호는 보지 않는다 — 방향은 낱말로 쓴다). 값은 장부 자리표시 「{키|꼴}」 로 쓰고(장부에서 키 · 꼴이 같은 줄로
  편다 · 없는 키는 거절), **원문에 같은 글자로 있는 숫자는 글자로 써도 된다** — 다시 쓰기 항목은 원문이 초안의 글자 그대로일 때만 적용되므로
  엔진 값이 바뀌어 초안이 달라지면 그 항목은 적용되지 않는다(옛 숫자가 새 판에 남을 길이 없다). 원고 묶음에 적을 때는 글자로 쓴 값이 옛 문장의
  자리표시가 편 글과 같으면 그 자리표시로 되돌려 적는다(장부 키가 끊기지 않는다). 그래서 묶음의 자리표시는 옛 문장의 것 안에서만 나온다.
열쇠 말(`열쇠말`) — 게이트 · 인터랙티브 판이 줄을 찾는 말(결론 다섯 줄의 머리 · 「→ 이 판단은」 · 「가정에 반영한 Narrative는」)은 고친 문장에도 남긴다.
1.1.19 — 고리(와 「쓰지 않는 고리」 인 검사)는 길을 정한 뒤 시험 초안(묶음 고침은 레터의 같은 글 자리 모두에 · 편집 목록은 편집 단계와 같은 함수로)을 지어
  게이트 판정을 표시 전 · 뒤 글에 함께 돌리고 뒤에만 선 막음 · 편집 「안 됨」 을 그 표시에 돌려 거절한다(`게이트차이`). 같은 원문 표시는 하나로 합치고
  (「합침」), 표 칸 · 긴 문장 안에도 있는 원문은 「모두」 대신 한 번만 나오는 문맥으로 낸다(`편집항목들`). 같은 원고 조각은 한 길로만 가고, 묶음 고침은
  이 회 · 앞 회 편집 항목의 원문 · 새글에도 따라 고친다(`항목맞추기`).
  부호를 늘 찍는 꼴(「증N」 · 「퍼pN」)의 값에서 부호를 떼고 방향을 낱말로 쓰면 묶음에는 크기 꼴 「{키|폭N}」 · 「{키|폭pN}」 으로 되돌려 적는다
  (`자리되돌림` · `묶음조건`). 연산 자리표시의 장부 키는 레터와 같은 셈(`레터이야기.식만들기` — 겹친 식)으로 찾는다.
"""
from __future__ import annotations

import argparse
import collections
import datetime
import difflib
import glob
import hashlib
import io
import json
import os
import re
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)

import 레터구조  # noqa: E402

판 = "교열 1"
표시형식, 준비형식, 고리형식, 대장형식, 남은형식 = "교열표시/1", "교열준비/1", "교열고리/1", "교열대장/1", "교열남은/1"
곳 = os.path.join("_raw", "교열")
대장곳 = os.path.join("_기록", "교열대장")
회상한 = 2                                     # 다시 쓰기는 두 번까지 — 그 뒤 남은 표시는 목록으로(사람 몫)
남은처리 = ("표시만", "거절", "남김", "구조", "되돌림", "확인 읽기")

# 유형 — 교열자가 문장마다 하나 고른다(짧은 이름 → 긴 이름)
유형표 = collections.OrderedDict([
    ("비문", "비문"),
    ("번역투", "번역한 글처럼 읽히는 문형"),
    ("개념이름", "일상어를 개념 이름으로 쓴 말 · 도구 안에서만 통하는 말"),
    ("사람처럼", "숫자 · 모델이 사람처럼 행동하는 서술"),
    ("반복", "같은 구조의 반복"),
    ("지시불명", "가리키는 대상이 불분명한 지시어"),
    ("군더더기", "지워도 잃는 정보가 없는 문장"),
    ("예측단정", "예측을 사실처럼 단정한 문장"),
    ("어긋남", "앞뒤 문장과 어긋나는 문장"),
    ("방식불일치", "이 회사의 추정 방식과 맞지 않는 문장"),
    ("기타", "기타"),
])
원칙말 = {1: "개념의 이름", 2: "실무 영어 용어", 3: "문서 · 모델 설명", 4: "주어", 5: "주어가 할 수 있는 동작", 6: "숫자의 단위 · 기간 · 방향",
        7: "사실 · 가정 · 추정 구분", 8: "지시어", 9: "문장 길이 · 끝맺음", 10: "절의 첫 문장", 11: "같은 구조", 12: "고정 문장의 자리",
        13: "한 문장은 한쪽이 쓴다"}
처리말 = collections.OrderedDict([("묶음", "원고 묶음을 고침"), ("편집목록", "편집 목록 다시 쓰기"), ("표시만", "고친 문장 없음(사람 몫)"),
                               ("거절", "조건에 맞지 않아 옮기지 않음"), ("남김", "옮길 길이 없음(사람 몫)"), ("구조", "구조 검사 자리 — 교열자가 다루지 않음"),
                               ("되돌림", "게이트가 막아 옛 글로 되돌림(사람 몫)"),
                               ("합침", "같은 원문 · 같은 원고 조각을 앞 표시가 같은 글로 고침(앞 표시가 함께 고친다)")])

# 게이트 ⑦ 의 값 토큰과 같은 꼴(단위가 붙은 값)
값꼴 = re.compile(r"(?<![\w.,])[−\-+]?\d[\d,]*(?:\.\d+)?(?:조 원|억 원|만 원|억 달러|만 달러|억 유로|억 엔|%p|%|배|원|달러|엔|유로|명|일(?![가-힣]))")
_덩이 = re.compile(r"\d[\d,]*(?:\.\d+)?")
_문장끝 = re.compile(r"(?<=[.!?])\s+")
_안넣는키 = ("근거대장", "옛글처리", "status", "묶음", "_메모", "_묶음")


def _sha(글):
    return hashlib.sha256(글.encode("utf-8")).hexdigest()


def _읽기(p, 기본=None):
    try:
        with io.open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return 기본


def _쓰기(p, d):
    os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(d, ensure_ascii=False, indent=1) + "\n")


def _글읽기(p):
    with open(p, "rb") as f:
        return f.read().decode("utf-8").replace("\r\n", "\n")


def _맨(s):
    """맞대는 꼴 — 빈칸 · 굵은 표시를 걷고 끝 마침표를 뗀다(`레터구조` 와 같은 셈)."""
    return re.sub(r"\s|\*\*", "", "%s" % s).rstrip(".")


def _띄움맨(s):
    """띄어쓰기는 남긴 맞대는 꼴 — 굵은 표시를 걷고 빈칸 여럿을 하나로, 끝 마침표를 뗀다(같음 판정: 띄어쓰기만 다른 고침은 다른 글)."""
    return re.sub(r"\s+", " ", re.sub(r"\*\*", "", "%s" % s)).strip().rstrip(".").rstrip()


# ══════════════════════════════════════════════════════════════════ 숫자 조건
def _수(t):
    return t.replace(",", "")


def _값(t):
    return re.sub(r"^[−\-+]", "", t).replace(",", "")


def 숫자조건(원문, 새글):
    """다시 쓴 문장(자리표시를 편 글)의 숫자가 원문의 숫자 안에서만 나오나 → 걸림 [글]. 단위가 붙은 값은 단위까지, 부호는 보지 않는다."""
    걸 = []
    옛수 = {_수(x) for x in _덩이.findall(원문 or "")}
    옛값 = {_값(x) for x in 값꼴.findall(원문 or "")}
    for x in _덩이.findall(새글 or ""):
        if _수(x) not in 옛수:
            걸.append("원문에 없는 숫자 「%s」" % x)
    for x in 값꼴.findall(새글 or ""):
        if _수(_덩이.search(x).group(0)) in 옛수 and _값(x) not in 옛값:
            걸.append("단위가 바뀐 값 「%s」" % x)
    return sorted(set(걸), key=걸.index)


# ══════════════════════════════════════════════════════════════════ 장부 자리표시
class 장부글:
    """레터 장부의 숫자 줄 → 자리표시 「{키|꼴}」 를 편 글(장부가 이미 찍은 글만 — 새 값을 셈하지 않는다)."""

    def __init__(self, 장부):
        import 레터이야기 as _N                               # noqa: PLC0415 — 자리표시 꼴 · 연산 · 어림 꼴은 레터와 한 곳
        self._N = _N
        self.글 = {}
        self.꼴들 = collections.defaultdict(list)
        for x in (장부 or {}).get("숫자") or []:
            if not isinstance(x, dict) or x.get("키") is None or x.get("글") is None:
                continue
            k, f = "%s" % x["키"], "%s" % (x.get("꼴") or "")
            if (k, f) not in self.글:
                self.글[(k, f)] = "%s" % x["글"]
                self.꼴들[k].append(f)
        self.값글 = {g for g in self.글.values() if g and re.search(r"\d", g)}

    def 풀기(self, 안, 꼴=None, 어림=False):
        안, 꼴 = ("%s" % 안).strip(), ("%s" % (꼴 or "")).strip()
        if not 꼴 and "·" in 안 and ":" not in 안.rsplit("·", 1)[1] and " " not in 안.rsplit("·", 1)[1].strip():
            안, 꼴 = 안.rsplit("·", 1)[0].strip(), 안.rsplit("·", 1)[1].strip()
        키 = self.키(안)
        if 키 is None:
            return None
        if 키 != 안:
            꼴 = 꼴 or "지수2"
        if 꼴:
            후보 = [self._N._어림꼴.get(꼴, 꼴), 꼴] if 어림 else [꼴, self._N._어림꼴.get(꼴, 꼴)]
        else:
            후보 = list(self.꼴들.get(키) or [])
            if len(set(후보)) > 1 and not 어림:
                후보 = [f for f in 후보 if not f.startswith("어림")] + [f for f in 후보 if f.startswith("어림")]
        for f in 후보:
            if (키, f) in self.글:
                return self.글[(키, f)]
        m = re.fullmatch(r"폭(p?)(\d)", 꼴)                    # 1.1.19 — 크기 꼴(「폭N」 · 「폭pN」)은 부호를 늘 찍는 꼴(「증N」 · 「퍼pN」)의 글에서 부호만 뗀 글이다
        if m:                                                 # (자리되돌림이 부호를 뗀 값을 이 꼴로 되돌린다 — 다음 초안이 장부에 이 꼴을 적기 전에도 편다)
            g = self.글.get((키, ("퍼p" if m.group(1) else "증") + m.group(2)))
            if g is not None:
                return re.sub(r"^[−\-+]", "", g)
        return None

    def 키(self, 안):
        """자리표시 안 → 장부 키. 연산이면 「식:[…]」 — 레터가 장부에 적는 꼴(`레터이야기.식만들기` — 겹친 식 「÷ 음 A B」 도 같은 셈).
        식을 짓지 못하면(항이 모자람) None."""
        부 = ("%s" % 안).split()
        if not 부 or 부[0] not in self._N._연산:
            return 안
        try:
            식 = self._N.식만들기(부)
        except ValueError:
            return None
        return "식:" + json.dumps(식, ensure_ascii=False)

    def 꼴고름(self, 안, 꼴=None):
        """자리표시의 꼴 — 적혀 있으면 그것, 없으면 지금 장부 글을 고르는 꼴(연산은 「지수2」 · 키는 장부가 찍은 첫 꼴)."""
        안, 꼴 = ("%s" % 안).strip(), ("%s" % (꼴 or "")).strip()
        if 꼴:
            return 꼴
        return "지수2" if self.키(안) != 안 else next(iter(self.꼴들.get(안) or []), "")


_크기꼴 = {"증": "폭", "퍼p": "폭p"}                          # 1.1.19 — 부호를 늘 찍는 꼴 → 부호 없는 크기 꼴(같은 자리 수)


def 크기꼴(꼴):
    """부호를 늘 찍는 꼴(「증N」 · 「퍼pN」) → 크기 꼴(「폭N」 · 「폭pN」). 아니면 None."""
    m = re.fullmatch(r"(증|퍼p)(\d)", "%s" % (꼴 or ""))
    return (_크기꼴[m.group(1)] + m.group(2)) if m else None


def 펴기(글, 맵, 어림=False):
    """글의 자리표시를 장부 글로 편다(뒤 조사는 레터와 같은 규칙으로 맞춘다) → (편 글, 못 편 자리표시[])."""
    못 = []

    def 바꿈(m):
        g = 맵.풀기(m.group(1), m.group(2), 어림)
        if g is None:
            못.append(m.group(0))
            return m.group(0)
        return g
    return 맵._N.조사맞춰펴기(글 or "", 바꿈), 못


def _자리표식():
    import 레터이야기 as _N                                   # noqa: PLC0415
    return _N._자리표


# ══════════════════════════════════════════════════════════════════ 레터 글
def 본문(글):
    i = 글.find("\n# 부록")
    return 글 if i < 0 else 글[:i + 1]


def 절찾기(줄들, n):
    """n 줄(1부터)이 든 절 — 가장 가까운 위의 「## 」 · 「# 」 머리(「3분 레터」 · 「1. 결론」 …)."""
    for i in range(min(n, len(줄들)) - 1, -1, -1):
        t = 줄들[i].strip()
        if t.startswith("## ") or t.startswith("# "):
            return re.sub(r"^#+\s*", "", t)[:40]
    return ""


def 열쇠말():
    """게이트 · 인터랙티브 판이 줄을 찾는 말 — 다시 쓴 문장에도 남아야 한다(결론 다섯 줄 머리는 `레터이야기.결론머리` 한 곳)."""
    낸 = ["→ 이 판단은", "가정에 반영한 Narrative는", "이 절이 담은 Narrative",
         "세 시나리오 범위 밖"]                                # 게이트 ⑭ 「범위 밖」 — 종가가 세 시나리오 밖이면 결론 두 자리에 이 말을 센다
    try:                                                      # 1.1.13 — 그 말의 정본은 `레터갭.범위밖말`(바뀌면 따라간다)
        import 레터갭 as _갭                                  # noqa: PLC0415
        낸[-1] = _갭.범위밖말
    except Exception:                                         # noqa: BLE001
        pass
    try:
        import 레터이야기 as _N                               # noqa: PLC0415
        for v in _N.결론머리.values():
            낸 += [v] if isinstance(v, str) else list(v)
        낸.append(_N.판단머리)
    except Exception:                                          # noqa: BLE001
        pass
    try:
        import 레터3분 as _S                                  # noqa: PLC0415 — 게이트 ⑭ DCF 적합성 고지(결론 · 3분 레터 두 자리에 이 문장을 센다)
        if isinstance(getattr(_S, "적합성머리", None), str):
            낸.append(_S.적합성머리.rstrip("."))
    except Exception:                                          # noqa: BLE001
        pass
    return sorted({x for x in 낸 if x}, key=len, reverse=True)


def 열쇠조건(원문, 새글, 말들=None):
    return ["열쇠 말 「%s」 을 지웠다(게이트가 이 말로 줄을 찾는다)" % 말 for 말 in (말들 or 열쇠말()) if 말 in (원문 or "") and 말 not in (새글 or "")]


def 결론줄인가(줄, 절=""):
    """결론 다섯 줄(값 · 가격 · 갈림 · 근거 · 틀림 — 3분 레터 · 본편 1절 · 인터랙티브 머리에 같은 글)인가 — 3분 레터 · 본편 1절에서 결론 머리 말이 든 줄."""
    if not re.match(r"^(?:3분 레터|1\. |결론)", 절 or ""):
        return False
    try:
        import 레터이야기 as _N                               # noqa: PLC0415
        머리 = [m for v in _N.결론머리.values() for m in ([v] if isinstance(v, str) else v)]
    except Exception:                                          # noqa: BLE001
        return False
    return any(m in (줄 or "") for m in 머리)


def 결론수조건(원문, 새글):
    """결론 줄의 숫자는 장부 「결론」 과 인터랙티브 판 머리가 줄마다 차례까지 맞댄다(⑦-2 · ⑯) — 다시 써도 숫자의 차례 · 개수가 같다."""
    옛, 새 = [_수(x) for x in _덩이.findall(원문 or "")], [_수(x) for x in _덩이.findall(새글 or "")]
    return [] if 옛 == 새 else ["결론 줄의 숫자 차례가 바뀌었다(%s → %s — 결론 줄은 숫자를 같은 차례로 모두 남긴다)" % (" · ".join(옛[:5]), " · ".join(새[:5]))]


def 꼴조건(새글, 길이상한=120):
    """고친 문장의 꼴 — 합쇼체 끝 · 문장 길이 · 원고 검수(문체 · 빈 슬롯 · 자기 지시 · 경로 · 권유 — 원고 조각과 같은 판정)."""
    import 어투                                               # noqa: PLC0415
    import 레터                                               # noqa: PLC0415
    걸 = []
    for s in [x.strip() for x in _문장끝.split((새글 or "").strip()) if x.strip()]:
        if 어투.끝꼴(s) == "평서":
            걸.append("평서체 끝 「%s」" % s[-12:])
        if len(s.replace("**", "")) > 길이상한:
            걸.append("%d자 문장(%d자 이내)" % (len(s.replace("**", "")), 길이상한))
    걸 += ["원고 검수 %s" % x for x in 레터.원고검사(새글 or "")]
    걸 += ["이름 검수 %s" % m for _n, m, _c in 레터.이름검수(새글 or "")]          # 게이트 ⑫ — 「종가」 는 날짜와 함께 · 번호식 이름
    return 걸


def 가정찾기(회차):
    """회차 폴더의 가정 파일(가정_*.json — 예시 · 템플릿 뺌 · 회차실행과 같은 고름). 없으면 None."""
    후 = [p for p in sorted(glob.glob(os.path.join(회차, "가정_*.json"))) if not re.search(r"예시|템플릿", os.path.basename(p))]
    return 후[0] if 후 else None


def 갈래말들(가정):
    """게이트 ⑧(선언한 갈래만)의 낱말 — [(설명, [낱말])]. 가정의 구조를 못 읽으면 빈 목록."""
    if not isinstance(가정, dict):
        return []
    try:
        import importlib                                      # noqa: PLC0415
        import 레터                                           # noqa: PLC0415
        _오, _경, 구조, _축 = importlib.import_module("엔진.스키마").검증전부(가정)
        return list(레터.갈래말(구조)) if 구조 is not None and not _오 else []
    except Exception:                                         # noqa: BLE001
        return []


def 문장점검조건(원문, 새글, 몫=None, 갈래=()):
    """1.1.15 — 게이트가 다시 쓴 문장을 막던 규칙 가운데 문장 하나로 볼 수 있는 것: ⑬ 문장 점검(조사 · 번역투 · 괄호 — 「6를」 · 「WACC가」)과
    ⑧ 선언하지 않은 갈래의 낱말(원고 조각은 게이트가 빼므로 코드 · 섞임 문장만). 원문에 이미 있던 걸림은 세지 않는다(새로 생긴 것만)."""
    import 레터문장                                           # noqa: PLC0415

    def 오류들(t):
        if not (t or "").strip():
            return collections.Counter()
        z = [x for x in 레터문장.문장점검(t) + 레터문장.용어조사점검(t) if x[0] == "오류"]
        return collections.Counter(x[2] for x in z if not x[2].startswith("문장 길이"))     # 길이는 꼴조건이 본다
    걸 = ["게이트 ⑬ %s" % k for k in (오류들(새글) - 오류들(원문))]
    if 몫 != "원고":
        for 설명, 낱말들 in 갈래 or ():
            for w in 낱말들:
                if w in (새글 or "") and w not in (원문 or ""):
                    걸.append("게이트 ⑧ 선언하지 않은 갈래의 낱말 「%s」 — %s" % (w, 설명))
    return 걸


def 일관조건(글, 표시들, 장부, 가정=None):
    """1.1.15 — 게이트 ⑱(같은 이름 다른 값 · 상호참조 · 서술 값 …)은 레터 전체를 본다. 받은 고친 문장을 모두 끼운 레터와 지금 레터의 막음을 견주고,
    새로 생긴 막음이 가리키는 줄을 담은 표시에 돌린다 → ({표시 번호(1부터): [까닭]}, [가르지 못한 새 막음])."""
    import 레터게이트 as _G                                   # noqa: PLC0415
    import 레터정합 as _J                                     # noqa: PLC0415

    def 막음(t):
        z = (_G.이름일관(t, 장부, False, 가정 if isinstance(가정, dict) else None)    # 1.1.19 — 가상 · 실제 같은 글자를 자리표시 키로 가른다(게이트와 같은 판정)
             + (_J.검사18(t, 장부, 가정) if isinstance(가정, dict) else []))
        return [x for x in z if x.get("등급") == "막음"]

    def 열쇠(x):
        return (x.get("항목"), re.sub(r"\d+\s?행", "", "%s" % x.get("내용")))
    받 = sorted([(i, x) for i, x in enumerate(표시들, 1) if x.get("처리") != "거절" and isinstance(x.get("고친문장"), str) and x.get("_자리")],
               key=lambda p: p[1]["_자리"][0])
    if not 받:
        return {}, []
    조각, 끝, 새자리 = [], 0, {}
    for i, x in 받:
        a, b = x["_자리"]
        if a < 끝:
            continue
        조각.append(글[끝:a])
        시작 = sum(len(c) for c in 조각)
        새 = x.get("_편") if x["고친문장"] else ""
        조각.append(새 or "")
        새자리[i] = (시작, 시작 + len(새 or ""))
        끝 = b
    조각.append(글[끝:])
    새글 = "".join(조각)
    try:
        옛, 새 = collections.Counter(열쇠(x) for x in 막음(글)), 막음(새글)
    except Exception as e:                                    # noqa: BLE001
        return {}, ["⑱ 대조를 돌리지 못했다(%s: %s)" % (type(e).__name__, ("%s" % e)[:120])]
    줄범위 = {i: (새글.count("\n", 0, s) + 1, 새글.count("\n", 0, e) + 1) for i, (s, e) in 새자리.items()}
    낸, 못 = {}, []
    for x in 새:
        k = 열쇠(x)
        if 옛[k] > 0:
            옛[k] -= 1
            continue
        행들 = [int(n) for n in re.findall(r"(\d+)\s?행", "%s %s" % (x.get("자리"), x.get("내용")))]
        누구 = [i for i, (p, q) in 줄범위.items() if any(p <= n <= q for n in 행들)]
        편들 = {i: (x2.get("_편") or "") for i, x2 in 받}
        말 = re.findall(r"「([^」]{2,40})」", "%s" % x.get("내용")) + re.findall(r"\d[\d,]*(?:\.\d+)?", "%s" % x.get("내용"))
        좁 = [i for i in 누구 if any(m in 편들.get(i, "") for m in 말)]       # 한 줄에 표시가 여럿이면 걸림의 이름 · 값이 든 문장으로 좁힌다
        누구 = 좁 or 누구
        if not 누구:                                           # 줄을 못 가리면 내용의 조각(낫표 안)이 고친 문장에 든 표시
            누구 = [i for i, _x in 받 if any(m in 편들[i] for m in re.findall(r"「([^」]{2,40})」", "%s" % x.get("내용")))]
        if 누구:
            for i in 누구:
                낸.setdefault(i, []).append("게이트 ⑱ %s — %s" % (x.get("항목"), ("%s" % x.get("내용"))[:120]))
        else:
            못.append("⑱ %s — %s" % (x.get("항목"), ("%s" % x.get("내용"))[:120]))
    return 낸, 못


def _경계(글, i, j):
    """[i, j) 가 문장 경계인가 — 앞은 줄 머리 · 불릿 · 문장 끝 뒤 빈칸, 뒤는 줄 끝 · 빈칸."""
    앞 = 글[:i]
    줄머리 = 앞.rsplit("\n", 1)[-1]
    앞됨 = (not 줄머리.strip()) or re.fullmatch(r"\s*(?:[-*+]|\d+\.)\s+(?:\*\*)?", 줄머리) is not None \
        or re.search(r"[.!?)」\]](?:\*\*)?\s+$", 줄머리) is not None
    뒤 = 글[j:j + 1]
    뒤됨 = 뒤 in ("", "\n", " ", "\t") or 글[j:j + 2] == "**"
    return bool(앞됨 and 뒤됨)


def 원문찾기(글, 원문, 줄=None):
    """레터 본문(부록 앞)에서 원문 자리 → (시작, 끝, 글자 그대로의 원문) 또는 None. 여러 번이면 준 줄에 가장 가까운 것.
    글자 그대로가 없으면 빈칸만 다른 꼴을 찾는다(교열자가 줄바꿈 · 빈칸을 바꿔 옮긴 경우)."""
    본 = 본문(글)
    자리 = []
    i = 본.find(원문)
    while i >= 0:
        자리.append((i, i + len(원문)))
        i = 본.find(원문, i + 1)
    if not 자리:
        조 = [re.escape(x) for x in re.split(r"\s+", 원문.strip()) if x]
        if not 조:
            return None
        for m in re.finditer(r"\s+".join(조), 본):
            자리.append((m.start(), m.end()))
    if not 자리:
        return None
    if 줄:
        자리.sort(key=lambda t: abs(본.count("\n", 0, t[0]) + 1 - int(줄)))
    a, b = 자리[0]
    return a, b, 본[a:b], len(자리)


def 문장들(원문):
    return [x.strip() for x in _문장끝.split((원문 or "").strip()) if x.strip()]


def 몫가르기(판정, 원문):
    """원문(문장 하나 이상)의 몫 — 모두 원고면 원고, 모두 코드면 코드, 그 밖은 섞임. 원고 조각이 없으면 None."""
    if not 판정:
        return None
    몫들 = {판정.몫(s) for s in 문장들(원문)} or {판정.몫(원문)}
    if 몫들 == {"원고"}:
        return "원고"
    if 몫들 == {"코드"}:
        return "코드"
    return "섞임"


def 유형맞춤(v):
    """교열자가 적은 유형 → 짧은 이름(긴 이름 · 앞부분도 받는다). 모르면 None."""
    v = ("%s" % (v or "")).strip()
    if not v:
        return None
    if v in 유형표:
        return v
    for k, 긴 in 유형표.items():
        if v == 긴 or 긴.startswith(v) or v.startswith(긴) or (len(v) >= 3 and v in 긴):
            return k
    v2 = v.replace(" ", "")
    for k, 긴 in 유형표.items():
        if v2 == k or v2 in 긴.replace(" ", ""):
            return k
    return None


def 원칙맞춤(v):
    if v is None or v == "":
        return []
    if not isinstance(v, list):
        v = [v]
    낸 = []
    for x in v:
        m = re.search(r"\d+", "%s" % x)
        if m and 1 <= int(m.group(0)) <= 13:
            낸.append(int(m.group(0)))
        else:
            return None
    return sorted(set(낸))


# ══════════════════════════════════════════════════════════════════ 준비 — 교열자가 먼저 읽는 것
def 산문보기(글):
    """교열자가 읽을 글 — 3분 레터와 본편(부록 앞)의 머리 · 산문 줄을 줄 번호와 함께(표 · 주석 · 그림 띠 · 목차는 뺀다).
    본편 1절의 합본 표지 안(3분 레터와 같은 글)은 싣지 않고 한 줄로 알린다 — 3분 레터 쪽에 한 번만 표시하면 도구가 둘을 함께 고친다."""
    합본 = 레터구조.읽기(글)["합본"]
    낸, 건넘 = [], []
    for n, t in enumerate(본문(글).split("\n"), 1):
        s = t.strip()
        if n in 합본:
            if s:
                건넘.append(n)
            continue
        if 건넘:
            낸.append("%d\t(%d ~ %d행 — 3분 레터와 같은 글이라 싣지 않았다)" % (건넘[0], 건넘[0], 건넘[-1]))
            건넘 = []
        if not s or s.startswith(("|", "<!--", "```", "![", "> 원문")) or re.match(r"^[-*] \[[^\]]+\]\(#", s):
            continue
        낸.append("%d\t%s" % (n, s))
    return "\n".join(낸) + "\n"


def 준비(글, 장부, 회=1, 앞=None, 레터이름="레터_초안.md"):
    """구조 검사 자리(막음 지표 먼저 · 표시 지표 다음) · 열쇠 줄 · (셋째 회부터) 다시 볼 문장 → 준비 dict."""
    원고 = (장부 or {}).get("원고") or []
    값 = 레터구조.지표(글, (), 원고)
    자리들 = []
    for 키, x in (값.get("항목") or {}).items():
        for z in x.get("자리") or []:
            자리들.append({"지표": 키, "이름": x.get("이름"), "원칙": x.get("원칙"), "등급": x.get("등급"), "넘음": bool(x.get("넘음")),
                        "줄": z.get("줄"), "말": z.get("말"), "글": z.get("글"), "몫": z.get("몫")})
    자리들.sort(key=lambda z: (0 if (z["등급"] == "막음" and z["넘음"]) else 1, z.get("줄") or 0))
    줄들 = 글.split("\n")
    말들 = 열쇠말()
    열쇠 = []
    for n, t in enumerate(본문(글).split("\n"), 1):
        걸린 = [m for m in 말들 if m in t]
        if 걸린:
            열쇠.append({"줄": n, "말": 걸린[0], "절": 절찾기(줄들, n)})
    d = {"형식": 준비형식, "판": 판, "회": 회, "레터": 레터이름, "글해시": _sha(글), "산문글자": 값.get("산문글자"), "문장": 값.get("문장"),
         "구조한줄": 레터구조.한줄(값), "구조": 자리들, "열쇠말": 말들, "열쇠": 열쇠,
         "읽을것": "3분 레터와 본편의 산문(「# 부록」 앞) — 표 · 부록 · 숫자의 옳고 그름은 보지 않는다"}
    if 회 > 회상한:
        본맨, 본 = _맨(본문(글)), set()
        d["다시볼"] = []
        for x in 다시볼문장(앞 or []):                        # 지금 레터에 남아 있는 문장만 · 같은 글은 한 번
            머 = _맨((문장들(x.get("글")) or [""])[0])[:30]
            if 머 and 머 in 본맨 and 머 not in 본:
                본.add(머)
                d["다시볼"].append(x)
        d["읽을것"] = "확인 읽기 — 「다시볼」 의 문장과 그 앞뒤 문장만 읽는다(앞 회에 다시 쓴 문장 · 남은 표시)"
    elif 앞:
        d["앞회남은"] = 다시볼문장(앞[-1:], 다시쓴=False)       # 앞 회에 고치지 못한 표시와 그 까닭(거절 · 되돌림) — 같은 문장을 다시 보면 그 까닭을 피해 고친다
    return d


def 다시볼문장(고리들, 다시쓴=True):
    """확인 읽기의 대상 — 앞 회들에 다시 쓴 문장(새 글)과 고치지 못한 표시(까닭과 함께)."""
    낸 = []
    for g in 고리들:
        for x in g.get("표시") or []:
            if 다시쓴 and x.get("처리") in ("묶음", "편집목록", "합침") and x.get("고친문장"):
                낸.append({"회": g.get("회"), "글": x["고친문장"], "까닭": "다시 쓴 문장"})
            elif x.get("처리") in 남은처리:
                낸.append({"회": g.get("회"), "글": x.get("원문"), "까닭": "남은 표시(%s)" % x.get("처리"),
                          "남은까닭": x.get("남은까닭") or " · ".join(x.get("거절") or [])})
    return 낸


# ══════════════════════════════════════════════════════════════════ 검사 — 표시 파일
def 검사(표시, 글, 장부, 묶음조각=None, 가정=None, 일관=True):
    """표시 파일을 검사하고 줄 · 절 · 몫 · 원문(글자 그대로)을 단다 → {"표시": [...], "거절": [(번호, 까닭)], "경보": [...]}.
    거절된 표시는 옮기지 않는다(「처리」 = 거절). 겹치는 원문은 앞의 것만 받는다. 가정을 주면 게이트 ⑧ · ⑱ 도 본다(1.1.15).
    일관 — 거짓이면 ⑱ 의 레터 전체 대조(`일관조건`)를 건너뛴다(1.1.19 — 고리는 길을 정한 뒤 `게이트차이` 로 게이트 판정 전부를 견준다)."""
    거절, 경보, 낸 = [], [], []
    if not isinstance(표시, dict) or not isinstance(표시.get("표시"), list):
        return {"표시": [], "거절": [(0, "표시 파일 꼴이 아니다 — {\"표시\": [...]}")], "경보": []}
    줄들 = 글.split("\n")
    판정 = 레터구조.원고판((장부 or {}).get("원고") or [])
    맵 = 장부글(장부)
    말들 = 열쇠말()
    갈래 = 갈래말들(가정)
    쓴자리 = []
    for i, x in enumerate(표시["표시"], 1):
        y = dict(x) if isinstance(x, dict) else {}
        왜 = []
        원 = y.get("원문")
        if not isinstance(원, str) or len(원.strip()) < 4:
            거절.append((i, "원문이 없다"))
            y.update({"처리": "거절", "거절": ["원문이 없다"]})
            낸.append(y)
            continue
        자 = 원문찾기(글, 원.strip(), y.get("줄"))
        if not 자:
            왜.append("원문을 레터 본문에서 찾지 못했다(글자 그대로 옮긴다 · 부록 · 표는 다루지 않는다)")
        else:
            a, b, 원2, 수 = 자
            y["원문"], y["줄"] = 원2, 글.count("\n", 0, a) + 1
            y["_자리"] = [a, b]
            if 수 > 1:
                y["여러번"] = 수
            if not _경계(글, a, b):
                왜.append("원문이 문장 경계에서 시작 · 끝나지 않는다(문장 단위로 옮긴다)")
            if any(not (b <= c or d <= a) for c, d in 쓴자리):
                왜.append("앞 표시와 원문이 겹친다")
            t = 줄들[y["줄"] - 1].strip() if 0 < y["줄"] <= len(줄들) else ""
            if t.startswith(("#", "|")):
                왜.append("제목 · 표 줄은 다루지 않는다")
        y["절"] = 절찾기(줄들, y.get("줄") or 1) if y.get("줄") else ""
        유 = 유형맞춤(y.get("유형"))
        if 유 is None:
            왜.append("유형이 목록에 없다: %s" % y.get("유형"))
        y["유형"] = 유 or y.get("유형")
        원칙 = 원칙맞춤(y.get("원칙"))
        if 원칙 is None:
            왜.append("원칙 번호가 1 ~ 13 이 아니다: %s" % y.get("원칙"))
        y["원칙"] = 원칙 or []
        if not y["원칙"] and 유 not in ("어긋남", "방식불일치", "기타"):
            경보.append("%d — 원칙 번호가 없다(유형 %s)" % (i, 유))
        if 유 == "기타" and len(("%s" % (y.get("까닭") or "")).strip()) < 4:
            왜.append("유형 기타는 까닭을 적는다")
        y["몫"] = 몫가르기(판정, y["원문"]) if not 왜 or 자 else None
        고 = y.get("고친문장")
        if 고 is not None and not isinstance(고, str):
            왜.append("고친문장은 글 · 빈 글 · null 가운데 하나")
        elif isinstance(고, str) and 고.strip():
            고 = 고.strip()
            y["고친문장"] = 고
            편, 못 = 펴기(고, 맵)
            if 못:
                왜.append("장부에 없는 자리표시 %s" % " · ".join(못[:3]))
            y["_편"] = 편
            if 자:
                왜 += 숫자조건(y["원문"], 편)
                왜 += 열쇠조건(y["원문"], 편, 말들)
                if (y["절"] or "").startswith("3분 레터") and len(_맨(편)) > len(_맨(y["원문"])):
                    왜.append("3분 레터는 길이 상한이 있다(게이트 ⑳) — 고친 문장이 원문보다 길다(%d → %d자)" % (len(_맨(y["원문"])), len(_맨(편))))
                if 결론줄인가(줄들[y["줄"] - 1], y["절"]):
                    왜 += 결론수조건(y["원문"], 편)
                왜 += 문장점검조건(y["원문"], 편, y.get("몫"), 갈래)
            왜 += 꼴조건(편)
            if _띄움맨(편) == _띄움맨(y["원문"]):           # 1.1.20 — 띄어쓰기만 고친 문장(「20% 에서」 → 「20%에서」)은 고친 것이다(⑬ 띄어 쓴 조사를 고칠 길)
                왜.append("고친 문장이 원문과 같다")
        elif isinstance(고, str):
            y["고친문장"] = ""
            if 자:
                왜 += 열쇠조건(y["원문"], "", 말들)
                if 결론줄인가(줄들[y["줄"] - 1], y["절"]):
                    왜 += 결론수조건(y["원문"], "")
        if 왜:
            거절.append((i, " · ".join(왜)))
            y["처리"], y["거절"] = "거절", 왜
        elif 자:
            쓴자리.append(tuple(y["_자리"]))
        낸.append(y)
    if 장부 and 일관:                                         # 1.1.15 — 게이트 ⑱ 은 레터 전체를 본다(받은 고친 문장을 모두 끼워 견준다)
        걸18, 못18 = 일관조건(글, 낸, 장부, 가정)
        for i, 까 in sorted(걸18.items()):
            y = 낸[i - 1]
            거절.append((i, " · ".join(까)))
            y["처리"], y["거절"] = "거절", list(y.get("거절") or []) + 까
        경보 += 못18
    return {"표시": 낸, "거절": 거절, "경보": 경보}


def 구조합치기(결, 준비값):
    """구조 검사가 표시한 막음 지표 자리 가운데 교열 표시가 덮지 않은 것 → 「구조」 표시로 더한다(고친 문장 없음 — 남으면 사람 몫)."""
    덮 = [(x.get("줄"), _맨(x.get("원문") or "")) for x in 결["표시"] if x.get("처리") != "거절"]
    더 = []
    for z in (준비값 or {}).get("구조") or []:
        if not (z.get("등급") == "막음" and z.get("넘음")):
            continue
        머 = _맨(z.get("글") or "")[:24]
        if any(n == z.get("줄") and (머 in 맨 or 맨[:24] in _맨(z.get("글") or "")) for n, 맨 in 덮):
            continue
        더.append({"줄": z.get("줄"), "원문": z.get("글"), "원칙": [z.get("원칙")] if z.get("원칙") else [], "유형": None,
                  "까닭": "구조 검사 %s %s" % (z.get("지표"), z.get("이름")), "고친문장": None, "몫": z.get("몫"), "처리": "구조",
                  "지표": z.get("지표")})
    결["표시"] += 더
    return 결


# ══════════════════════════════════════════════════════════════════ 원고 묶음
def 묶음읽기(회차):
    낸 = collections.OrderedDict()
    for p in sorted(glob.glob(os.path.join(회차, "_raw", "레터원고", "*.json"))):
        n = os.path.basename(p)
        if n.startswith("_"):
            continue
        d = _읽기(p)
        if isinstance(d, dict):
            낸[n] = d
    return 낸


def _잎들(d, 길=(), 맨위=True):
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(k, str) and (k.startswith("_") or (맨위 and k in _안넣는키)):
                continue
            for x in _잎들(v, 길 + (k,), False):
                yield x
    elif isinstance(d, list):
        for i, v in enumerate(d):
            for x in _잎들(v, 길 + (i,), False):
                yield x
    elif isinstance(d, str):
        yield 길, d


def _길쓰기(d, 길, 값):
    for k in 길[:-1]:
        d = d[k]
    d[길[-1]] = 값


def _문장자리(t):
    """글의 문장 자리 [(시작, 끝)] — 레터와 같은 가름(마침표 · 물음표 뒤 빈칸)."""
    낸, i = [], 0
    for m in _문장끝.finditer(t):
        낸.append((i, m.start()))
        i = m.end()
    낸.append((i, len(t)))
    return [(a, b) for a, b in 낸 if t[a:b].strip()]


def _변형들(e):
    """레터가 원고 조각에 거는 말 바꿈(옛말 → 지금 말 · 독자 말)까지 견줄 꼴들."""
    낸 = [e]
    try:
        import 레터문장 as _M                                 # noqa: PLC0415 — 결론 줄 대조와 같은 차례(옛말 → 독자 말 → 조어)
        낸.append(_M._결론독자말(e))
    except Exception:                                          # noqa: BLE001
        pass
    return {_맨(x) for x in 낸 if x}


class 묶음색인:
    """원고 묶음의 잎 글을 문장 자리(한 문장 ~ 이어진 세 문장)마다 장부 글로 편 꼴로 색인한다 — 레터의 원고 문장이 묶음의 어느 자리에서
    왔나를 찾는다. 잎을 고치면 그 잎만 다시 색인한다."""

    def __init__(self, 묶음들, 맵, 폭=3):
        self.묶음들, self.맵, self.폭 = 묶음들, 맵, 폭
        self.칸 = []
        for 이름, d in 묶음들.items():
            for 길, 잎 in _잎들(d):
                self._넣기(이름, 길, 잎)

    def _넣기(self, 이름, 길, 잎):
        if len(잎) < 8:
            return
        자 = _문장자리(잎)
        for k in range(len(자)):
            for 폭 in range(1, min(self.폭, len(자) - k) + 1):
                a, b = 자[k][0], 자[k + 폭 - 1][1]
                raw = 잎[a:b]
                for 어림 in ((False, True) if "{" in raw else (False,)):
                    e, 못 = 펴기(raw, self.맵, 어림)
                    맨들 = _변형들(re.sub(r"\{[^{}]*\}", "", e)) if 못 else _변형들(e)
                    self.칸.append({"묶음": 이름, "길": list(길), "잎": 잎, "a": a, "b": b, "옛": raw, "어림": 어림, "맨들": 맨들,
                                   "못": bool(못), "폭": 폭})

    def 다시(self, 이름, 길, 잎):
        self.칸 = [c for c in self.칸 if not (c["묶음"] == 이름 and c["길"] == list(길))]
        self._넣기(이름, tuple(길), 잎)

    def 찾기(self, 원문):
        """원문(레터 글자)을 쓴 묶음 자리 → {"묶음", "길", "잎", "a", "b", "옛", "어림", "닮음"} 또는 None. 편 꼴이 같은 자리가 하나면 그것,
        없으면 닮음 0.92 이상이고 둘째 자리보다 0.03 넘게 높은 하나."""
        목표 = _맨(원문)
        같 = [c for c in self.칸 if not c["못"] and 목표 in c["맨들"]]
        자리 = {(c["묶음"], tuple(c["길"]), c["a"], c["b"]) for c in 같}
        if len(자리) == 1:
            return dict(같[0], 닮음=1.0)
        if len(자리) > 1:
            return None                                       # 같은 글이 묶음 두 자리에 — 어느 쪽인지 모른다(사람 몫)
        후보 = []
        for c in self.칸:
            for m in c["맨들"]:
                if abs(len(m) - len(목표)) <= max(8, len(목표) // 6):
                    r = difflib.SequenceMatcher(None, m, 목표).ratio()
                    if r >= 0.85:
                        후보.append((r, c))
        if not 후보:
            return None
        후보.sort(key=lambda t: -t[0])
        r0, c0 = 후보[0]
        둘째 = next((r for r, c in 후보[1:] if (c["묶음"], c["길"], c["a"]) != (c0["묶음"], c0["길"], c0["a"])), 0)
        return dict(c0, 닮음=round(r0, 3)) if r0 >= 0.92 and r0 - 둘째 > 0.03 else None


def 자리되돌림(새글, 옛raw, 맵, 어림=False):
    """고친 문장(글자로 쓴 값)을 묶음에 적을 꼴로 — 옛 문장의 자리표시가 편 글이 새 글에 있으면 그 자리표시로 되돌린다(긴 글부터)."""
    자리 = []
    for m in 맵._N._자리표.finditer(옛raw):
        g = 맵.풀기(m.group(1), m.group(2), 어림)
        if g:
            자리.append((m.group(0), g))
    out = 새글
    남은 = []
    for 원자리, g in sorted(자리, key=lambda t: -len(t[1])):
        a, b = _밖찾기(out, g)
        if a is None:
            남은.append((원자리, g))
            continue
        out = out[:a] + 원자리 + out[b:]
    # 부호를 떼고 방향을 낱말로 쓴 값(「−12%」 → 「12% 줄어든다」) — 음수 값은 「{음 키|꼴}」(장부의 부호 뒤집기 셈)로 되돌린다.
    # 양수에도 부호를 찍는 꼴(장부에 「+」 로 시작하는 글이 있는 꼴)은 뒤집으면 「+」 가 붙으므로 되돌리지 않는다(글자 숫자로 남아 거절된다)
    # 1.1.19 — 부호를 늘 찍는 꼴(「증N」 · 「퍼pN」 — 「+14.0%」 · 「−3.4%」)에서 부호를 뗀 값은 부호와 상관없이 크기 꼴 「{키|폭N}」 · 「{키|폭pN}」 으로
    # 되돌린다(방향은 교열자가 쓴 낱말이 말한다 · 연산 자리표시도 같다). 이 꼴에 「{음 …}」 을 쓰면 「+」 가 붙으므로 아래 길로 가지 않는다
    부호꼴 = {f for (k, f), g in 맵.글.items() if g.startswith("+")}
    for 원자리, g in 남은:
        m = 맵._N._자리표.fullmatch(원자리)
        안, 꼴 = m.group(1).strip(), 맵.꼴고름(m.group(1), m.group(2))
        폭 = 크기꼴(꼴)
        if 폭:
            if g.startswith(("+", "−", "-")):
                a, b = _밖찾기(out, g[1:])
                if a is not None:
                    out = out[:a] + "{%s|%s}" % (안, 폭) + out[b:]
            continue
        if not g.startswith(("−", "-")):
            continue
        if not 꼴 or 꼴 in 부호꼴 or 안.split()[0] in 맵._N._연산:
            continue
        a, b = _밖찾기(out, g[1:])
        if a is not None:
            out = out[:a] + "{음 %s|%s}" % (안, 꼴) + out[b:]
    return out


def _밖찾기(out, g):
    """out 에서 숫자 글 g 의 첫 자리(앞뒤가 숫자가 아니고 자리표시 「{…}」 밖) → (a, b) 또는 (None, None)."""
    for m in re.finditer(r"(?<![\d.,−\-+])" + re.escape(g) + r"(?![\d])", out):
        if out.rfind("{", 0, m.start()) <= out.rfind("}", 0, m.start()):
            return m.start(), m.end()
    return None, None


def 묶음조건(옛raw, 새raw, 맵=None):
    """묶음에 적을 새 글 — 자리표시는 옛 글의 것 안에서, 자리표시 밖의 숫자는 옛 글의 자리표시 밖 숫자 안에서 → 걸림 [].
    자리되돌림이 낸 두 바꿈은 옛 자리표시의 것으로 본다 — 「{음 키|꼴}」(옛 글의 키) · 크기 꼴 「{키|폭N}」 · 「{키|폭pN}」(옛 글의 같은 키가
    부호를 늘 찍는 꼴 「증N」 · 「퍼pN」 — 꼴이 안 적혔으면 맵이 고르는 꼴)."""
    표 = _자리표식()
    옛자, 새자 = collections.Counter(m.group(0) for m in 표.finditer(옛raw)), collections.Counter(m.group(0) for m in 표.finditer(새raw))
    옛안 = {m.group(1).strip() for m in 표.finditer(옛raw)}
    옛꼴 = collections.defaultdict(set)
    for m in 표.finditer(옛raw):
        옛꼴[m.group(1).strip()].add(맵.꼴고름(m.group(1), m.group(2)) if 맵 is not None else (m.group(2) or "").strip())

    def 되돌린것(k):
        f = 표.fullmatch(k)
        if not f:
            return False
        안, 꼴 = f.group(1).strip(), (f.group(2) or "").strip()
        if re.match(r"^음 ", 안) and 안[2:].strip() in 옛안:
            return True
        return bool(꼴) and any(크기꼴(o) == 꼴 for o in 옛꼴.get(안, ()))
    걸 = ["옛 문장에 없는 자리표시 %s" % k for k in 새자 if k not in 옛자 and not 되돌린것(k)]
    옛밖 = {_수(x) for x in _덩이.findall(표.sub(" ", 옛raw))}
    걸 += ["자리표시 밖의 새 숫자 「%s」" % x for x in _덩이.findall(표.sub(" ", 새raw)) if _수(x) not in 옛밖]
    return 걸


def 묶음고침(묶음들, 찾은, 고친, 맵):
    """찾은 자리(묶음 · 길 · 잎의 [a, b))를 고친 문장으로 → (바뀐 잎, 새 raw) 또는 (None, 까닭). 고친 = "" 이면 지운다(이웃 빈칸 하나와 함께)."""
    잎, a, b = 찾은["잎"], 찾은["a"], 찾은["b"]
    if 고친 == "":
        if b < len(잎) and 잎[b:b + 1].isspace():
            b += 1
        elif a > 0 and 잎[a - 1:a].isspace():
            a -= 1
        새잎 = 잎[:a] + 잎[b:]
        if not 새잎.strip():
            return None, "지우면 원고 문단이 빈다(원고 요건) — 사람 몫"
        return 새잎, {"앞": 잎[max(0, a - 30):a], "옛": 잎[a:b], "새": ""}
    새raw = 자리되돌림(고친, 찾은["옛"], 맵, 찾은.get("어림"))
    걸 = 묶음조건(찾은["옛"], 새raw, 맵)
    if 걸:
        return None, " · ".join(걸)
    끝 = 찾은["옛"][len(찾은["옛"].rstrip()):]
    return 잎[:a] + 새raw.rstrip() + 끝 + 잎[b:], {"앞": 잎[max(0, a - 30):a], "옛": 잎[a:b], "새": 새raw.rstrip() + 끝}


def 묶음되돌림(잎, 바꿈):
    """묶음고침이 남긴 바꿈({앞, 옛, 새})을 지금 잎에서 되돌린다 → 새 잎 또는 None(자리를 못 찾음)."""
    앞, 옛, 새 = 바꿈.get("앞") or "", 바꿈.get("옛") or "", 바꿈.get("새") or ""
    if 앞 + 새 and (앞 + 새) in 잎:
        return 잎.replace(앞 + 새, 앞 + 옛, 1)
    if 새 and 잎.count(새) == 1:
        return 잎.replace(새, 옛, 1)
    return None


def _맨자리(s):
    """빈칸 · 굵은 표시를 걷은 글과, 그 글자마다 원래 글의 자리."""
    글자, 자리, i = [], [], 0
    while i < len(s):
        if s[i:i + 2] == "**":
            i += 2
            continue
        if not s[i].isspace():
            글자.append(s[i])
            자리.append(i)
        i += 1
    return "".join(글자), 자리


def 든조각(원문, 원고):
    """원문 안에 든 원고 조각(장부 「원고」 — 빈칸 · 굵은 표시를 걷고 맞댄다) → [(시작, 끝)](원문의 자리 · 긴 것부터 · 겹치지 않게)."""
    맨, 자리 = _맨자리(원문)
    낸 = []
    for g in sorted({_맨(x) for x in (원고 or []) if isinstance(x, str)}, key=len, reverse=True):
        if len(g) < 8:
            continue
        i = 맨.find(g)
        if i < 0:
            continue
        a, b = 자리[i], 자리[i + len(g) - 1] + 1
        if any(not (b <= c or d <= a) for c, d in 낸):
            continue
        낸.append((a, b))
    return sorted(낸)


def 섞임가르기(원문, 고친, 원고):
    """섞임 문장(코드 글 + 원고 조각)에서 코드 틀이 그대로면 원고 조각만 바뀐 것으로 본다 → (옛 조각(레터 글자), 새 조각) 또는 None."""
    for a, b in sorted(든조각(원문, 원고), key=lambda t: t[0] - t[1]):
        앞, 뒤 = 원문[:a], 원문[b:]
        if 고친.startswith(앞) and 고친.endswith(뒤) and len(고친) >= len(앞) + len(뒤):
            새 = 고친[len(앞):len(고친) - len(뒤)]
            if 새.strip() and 새 != 원문[a:b]:
                return 원문[a:b], 새
    return None


def 장부밖값(글, 맵):
    """글의 값 꼴 숫자 가운데 장부 글(또는 그 일부)이 아닌 것 — 게이트 ⑦ 의 숫자 훑기가 원고 조각 밖에서 잡을 값."""
    return [t for t in 값꼴.findall(글 or "") if not any(_값(t) in _값(g) for g in 맵.값글)]


# ══════════════════════════════════════════════════════════════════ 다시 쓰기 — 편집 목록 항목(회차실행 편집 단계가 부른다)
def 다시쓰기펴기(원문, 새글, 장부=None):
    """편집 목록 「다시쓰기」 항목의 새 글을 장부로 펴고 조건을 본다 → (편 글, 걸림 []). 걸림이 있으면 적용하지 않는다."""
    if 새글 == "":
        return "", 열쇠조건(원문, "")
    맵 = 장부글(장부)
    편, 못 = 펴기(새글, 맵)
    걸 = ["장부에 없는 자리표시 %s" % " · ".join(못[:3])] if 못 else []
    return 편, 걸 + 숫자조건(원문, 편) + 열쇠조건(원문, 편)


def 편집항목(x, 회):
    """검사를 지난 표시 하나 → 편집 목록 「다시쓰기」 항목."""
    d = collections.OrderedDict([("종류", "다시쓰기"), ("원문", x["원문"]), ("새글", x.get("고친문장") or ""), ("회", 회),
                                 ("줄", x.get("줄")), ("원칙", x.get("원칙")), ("유형", x.get("유형")), ("몫", x.get("몫")),
                                 ("까닭", x.get("까닭"))])
    if x.get("여러번"):
        d["모두"] = True
    return d


def _지움원문(글, x):
    """지울 문장의 원문에 이웃 빈칸 하나를 붙인다(문단 가운데 문장을 지워도 빈칸이 둘 남지 않게)."""
    a, b = x.get("_자리") or (None, None)
    원 = x["원문"]
    if a is None:
        return 원
    if 글[b:b + 1] == " ":
        return 원 + " "
    if a > 0 and 글[a - 1:a] == " ":
        return " " + 원
    return 원


# ══════════════════════════════════════════════════════════════════ 1.1.19 — 같은 원문 · 같은 원고 조각 · 게이트 차이
# 검사를 지난 표시가 고리 · 편집 뒤 게이트에서 막히던 꼴(⑧ ⑬ ⑮ ⑱ ⑳ · 편집 「안 됨」 · 표 칸 바뀜)을 고리 안에서 미리 잡는다.
# 길(묶음 · 편집 목록)을 정한 뒤 「시험 초안」 — 원고 묶음의 고침은 넣기 · 초안이 레터 모든 자리에 다시 세우는 꼴로, 편집 목록은 편집 단계와 같은
# 함수(`회차실행.편집적용`)로 — 을 지어, 게이트가 쓰는 판정 함수를 표시 전 · 뒤 두 글에 돌리고 뒤에만 선 막음을 그 줄 · 이름이 든 표시에 돌린다.
_비산문머리 = ("|", "#", "<!--", "![", "```", ">")


def _줄자리(글, i):
    s = 글.rfind("\n", 0, i) + 1
    e = 글.find("\n", i)
    return s, (len(글) if e < 0 else e)


def _산문자리(글, a, b):
    """[a, b) 가 산문 줄 안의 문장 단위 자리인가 — 표 · 제목 · 주석 · 그림 줄이 아니고 문장 경계에서 시작 · 끝난다."""
    s, e = _줄자리(글, a)
    return b <= e and not 글[s:e].strip().startswith(_비산문머리) and _경계(글, a, b)


def _모든자리(본, 원문):
    낸, i = [], (본.find(원문) if 원문 else -1)
    while i >= 0:
        낸.append((i, i + len(원문)))
        i = 본.find(원문, i + 1)
    return 낸


def _지움자리(글, a, b):
    """지울 문장 자리에 이웃 빈칸 하나를 붙인다(`_지움원문` 과 같은 셈)."""
    if 글[b:b + 1] == " ":
        return a, b + 1
    if a > 0 and 글[a - 1:a] == " ":
        return a - 1, b
    return a, b


def _고유문맥(본, a, b, 막힌=()):
    """[a, b) 를 같은 줄의 이웃 문장으로 넓혀 본문에서 한 번만 나오는 가장 좁은 자리 (c, d) → 없으면 None.
    다른 표시의 자리(막힌)와 겹치는 넓힘은 쓰지 않는다(두 편집 항목이 같은 글을 고치면 둘째가 「안 됨」 이 된다)."""
    s, e = _줄자리(본, a)
    if b > e:
        return None
    자 = [(s + p, s + q) for p, q in _문장자리(본[s:e])]
    왼 = [p for p, q in 자 if q <= a]
    오 = [q for p, q in 자 if p >= b]
    for _n, L, R in sorted((L + R, L, R) for L in range(len(왼) + 1) for R in range(len(오) + 1) if L or R):
        c, d = (왼[-L] if L else a), (오[R - 1] if R else b)
        if any(not (d <= p or q <= c) for p, q in 막힌):
            continue
        if 본.count(본[c:d]) == 1:
            return c, d
    return None


def 편집항목들(글, x, 회, 막힌=(), 퍼뜨림=True):
    """편집 목록으로 갈 표시 하나 → ([항목], 까닭). 원문이 본문에 한 번이면 항목 하나. 여러 번이면(같은 코드 문장이 여러 절에) —
    모든 자리가 산문 문장이면 「모두」 항목 하나(같은 코드 문장은 한 번 표시하면 모든 자리를 고친다), 표 · 제목 줄이나 더 긴 문장 안에도 있으면
    산문 자리마다 같은 줄의 이웃 문장을 붙여 한 번만 나오는 원문으로 항목을 낸다(표 칸까지 바뀌지 않게 — 게이트 ④).
    퍼뜨림이 거짓이면(같은 원문에 다른 고친 문장이 둘 — 자리마다 따로) 표시 자리 하나만. 지움은 이웃 빈칸 하나까지. 길이 없으면 ([], 까닭)."""
    본 = 본문(글)
    고 = x.get("고친문장") or ""
    a, b = x["_자리"]
    자들 = _모든자리(본, x["원문"])
    if len(자들) <= 1:
        항 = 편집항목(x, 회)
        항.pop("모두", None)
        if 고 == "":
            항["원문"] = _지움원문(글, x)
        return [항], None
    산 = sorted({(p, q) for p, q in 자들 if _산문자리(본, p, q)} | {(a, b)})
    if 퍼뜨림 and len(산) == len(자들):
        항 = 편집항목(x, 회)
        항["모두"] = True
        if 고 != "":
            return [항], None
        지 = [_지움자리(본, p, q) for p, q in 산]
        if len({(p - p2, q2 - q) for (p, q), (p2, q2) in zip(산, 지)}) == 1:
            원 = 본[지[0][0]:지[0][1]]
            if len(_모든자리(본, 원)) == len(자들):
                항["원문"] = 원
                return [항], None
    낸 = []
    for p, q in (산 if 퍼뜨림 else [(a, b)]):
        p2, q2 = _지움자리(본, p, q) if 고 == "" else (p, q)
        r = (p2, q2) if 본.count(본[p2:q2]) == 1 else _고유문맥(본, p2, q2, [z for z in 막힌 if z != (a, b)])
        if r is None:
            return [], ("같은 원문이 본문에 %d번 나오고 일부는 표 · 제목 줄이나 더 긴 문장 안이다 — 같은 줄의 이웃 문장을 붙여도 한 번만 나오는 글이 "
                        "되지 않아 그 자리만 고칠 수 없다(사람 몫)" % len(자들))
        c, d = r
        항 = 편집항목(x, 회)
        항.pop("모두", None)
        항["원문"], 항["새글"] = 본[c:d], 본[c:p2] + 고 + 본[q2:d]
        if (c, d) != (p2, q2):
            항["문맥"] = True
        낸.append(항)
    return 낸, None


def _조각꼴(옛, 신):
    """원고 조각의 맞댈 꼴 — 그대로 · 끝 마침표를 뗀 낫표 인용(「…」 안에는 마침표 없이 실린다)."""
    낸 = [(옛, 신)]
    if 옛.endswith(".") and (신 == "" or 신.endswith(".")):
        낸.append((옛[:-1] + "」", (신[:-1] if 신 else "") + "」"))
    return 낸


def 조각적용(t, 바뀐조각):
    """원고 묶음의 고침(옛 레터 글 → 새 편 글)을 글 전체의 같은 글 자리에 — 넣기 · 초안이 그 조각을 레터 모든 자리에 다시 세우는 꼴."""
    for _i, 옛, 신 in 바뀐조각:
        if len(_맨(옛)) < 8:
            continue
        if 신 == "":
            for p, q in reversed(_모든자리(t, 옛)):
                p2, q2 = _지움자리(t, p, q)
                t = t[:p2] + t[q2:]
            continue
        for o, n in _조각꼴(옛, 신):
            t = t.replace(o, n)
    return t


def 항목맞추기(항목들, 바뀐조각):
    """원고 묶음이 고친 조각(옛 → 새 — 넣기 · 초안 뒤 레터 모든 자리에 새 글로 선다)을 편집 목록 항목의 원문 · 새글에도 따라 고친다.
    앞 회의 항목(1회 코드 문장의 지움 · 다시 쓰기)이 2회가 고친 낫표 인용 때문에 「안 됨」 이 되지 않게. → (새 항목들, 맞춤 기록 []).
    맞춤 기록 {표시, 항목, 옛원문, 새원문, 옛새글, 새새글, 엇갈림} — 엇갈림 = 원문에는 그 조각이 있는데 새글은 그 조각을 다른 글로 고쳤다."""
    낸, 기록 = [], []
    for k, h in enumerate(항목들):
        if not isinstance(h, dict) or not isinstance(h.get("원문"), str):
            낸.append(h)
            continue
        원, 새 = h["원문"], h.get("새글")
        for i, 옛, 신 in 바뀐조각:
            if len(_맨(옛)) < 8:
                continue
            for o, n in _조각꼴(옛, 신):
                if o not in 원:
                    continue
                들 = isinstance(새, str) and o in 새
                새2 = 새.replace(o, n) if 들 else 새
                기록.append({"표시": i, "항목": k, "옛원문": 원, "새원문": 원.replace(o, n), "옛새글": 새, "새새글": 새2,
                           "엇갈림": bool(isinstance(새, str) and 새.strip() and not 들 and n not in 새)})
                원, 새 = 원.replace(o, n), 새2
                break
        낸.append(dict(h, 원문=원, 새글=새) if (원, 새) != (h["원문"], h.get("새글")) else h)
    return 낸, 기록


def _행들(z):
    낸 = [int(n) for n in re.findall(r"(\d+)\s?행", "%s %s" % (z.get("자리"), z.get("내용")))]
    if isinstance(z.get("자리"), int):
        낸.append(z["자리"])
    return 낸


def 판정모음(t, 장부, 가정, 경로=None):
    """게이트가 막는 판정 가운데 엔진을 다시 돌리지 않고 글 · 장부 · 가정으로 서는 것 → [{번호, 항목, 자리, 내용}].
    ③ 문장 · 구조 · 조판 검수 · ⑦ 장부 밖 숫자 · ⑧ 선언 밖 갈래 낱말 · ⑨ 권유 · ⑩ 경로 · ⑫ 이름 · ⑬ 문장 점검(오류) · ⑭ 편집본 요소 문단 ·
    ⑮ 지렛대 이름(다시 셈은 빼고 세 글 자리) · ⑱ ⑲ ⑳ 막음 — 게이트(`레터게이트.main`)와 같은 함수 · 같은 인자다. 못 돈 판정은 「돌리지 못함」 한 줄."""
    import importlib                                          # noqa: PLC0415
    import 레터 as 본                                         # noqa: PLC0415
    import 레터게이트 as G                                    # noqa: PLC0415
    장부 = 장부 or {}
    낸 = []

    def 덧(번, f):
        try:
            for z in f():
                낸.append(dict(z, 번호=번))
        except Exception as e:                                # noqa: BLE001
            낸.append({"번호": 번, "항목": "돌리지 못함", "자리": "-", "내용": "%s: %s" % (type(e).__name__, ("%s" % e)[:100])})
    try:
        구 = importlib.import_module("엔진.스키마").검증전부(가정)[2] if isinstance(가정, dict) else None
    except Exception:                                         # noqa: BLE001
        구 = None
    덧("③", lambda: [{"항목": m, "자리": n, "내용": "%s" % (c or "")} for n, m, c in 본.문장검수(t)]
      + [{"항목": "%s(%s)" % (m, g), "자리": n, "내용": "%s" % (c or "")} for g, n, m, c in 본.구조검수(t)]
      + [{"항목": m, "자리": n, "내용": "%s" % (c or "")} for n, m, c in 본.조판검수(t)])
    if 장부:
        덧("⑦", lambda: [{"항목": "장부에 없는 숫자", "자리": s.split(" ", 1)[0], "내용": re.sub(r"「[−\-+]", "「", s.split(" ", 1)[-1])}
                        for s in G.장부밖숫자(t, 장부)])                    # 부호를 떼고 방향을 낱말로 쓴 값은 같은 값(교열 원칙 6)
    if 구 is not None:
        def 갈래():
            본글 = G._원고뺀(t, list(장부.get("원고") or []) + [x.get("글") for x in 장부.get("숫자") or [] if x.get("꼴") == "글"])
            return [{"항목": "선언 밖 갈래 낱말", "자리": "-", "내용": "「%s」 — %s" % (w, 설명)}
                    for 설명, 낱말들 in 본.갈래말(구) for w in 낱말들 if w in 본글]
        덧("⑧", 갈래)
    덧("⑨", lambda: [{"항목": m, "자리": n, "내용": "%s" % (c or "")} for n, m, c in 본.권유검수(t)])
    덧("⑩", lambda: [{"항목": m, "자리": n, "내용": "%s" % (c or "")} for n, m, c in 본.경로검수(t)])
    덧("⑫", lambda: [{"항목": m, "자리": n, "내용": "%s" % (c or "")} for n, m, c in 본.이름검수(t, 구)])

    def 문장():
        import 레터문장 as M                                  # noqa: PLC0415
        보호 = [x.get("글") for x in 장부.get("숫자") or [] if x.get("꼴") == "글"] + list(장부.get("바깥") or [])
        return [{"항목": 항, "자리": n, "내용": "%s" % (조 or "")} for 등, n, 항, 조 in M.점검(t, None, 장부 or None, 보호) if 등 == "오류"]
    덧("⑬", 문장)
    if 구 is not None:                                        # ⑬ 같은 대상의 숫자 둘 — 게이트는 엔진의 구조로 매출 구분 이름을 모은다(엔진 없이 가정의 구조로 같게)
        import 레터문장 as M                                  # noqa: PLC0415
        덧("⑬", lambda: [{"항목": 항, "자리": n, "내용": "%s" % (조 or "")} for 등, n, 항, 조
                        in M.대상숫자점검(t, 장부.get("원고") or [], 구, 장부.get("가격성립입력")) if 등 == "오류"])
    요 = (장부.get("원고요건") or {}).get("요건")
    if isinstance(요, list) and 요:
        덧("⑭", lambda: [{"항목": "원고 요건", "자리": x.get("자리"), "내용": x.get("까닭")}
                        for x in importlib.import_module("레터원고").편집대조(요, 장부.get("원고자리"), t)])
    if isinstance(가정, dict) and 장부.get("지렛대"):
        덧("⑮", lambda: [{"항목": "지렛대", "자리": "-", "내용": s} for s in G.지렛대검사(본, 가정, 장부, None, t, {})[0]
                        if not s.startswith(("지렛대를 다시 셈하지", "지렛대가 장부와 다르다"))])
    try:
        일 = G.일관검사(t, 장부, 가정, 구, None, 경로=경로)
        for 번 in ("⑱", "⑲", "⑳"):
            낸 += [dict(z, 번호=번) for z in 일.get(번) or [] if z.get("등급") == "막음"]
    except Exception as e:                                    # noqa: BLE001
        낸.append({"번호": "⑱", "항목": "돌리지 못함", "자리": "-", "내용": "%s: %s" % (type(e).__name__, ("%s" % e)[:100])})
    return 낸


def _자리열쇠(z):
    """막음의 자리가 줄 번호가 아닌 이름(절 머리 · 가정 칸)이면 그 이름 — 내용 글만 달라진 같은 막음을 가린다. 줄 번호 자리는 빈 글."""
    자 = ("%s" % (z.get("자리") if z.get("자리") is not None else "")).strip()
    if not 자 or 자 == "-" or isinstance(z.get("자리"), int) or re.search(r"\d+\s?행|^\d+$", 자):
        return ""
    return 자


def _판정열쇠(z):
    줄뺌 = lambda s: re.sub(r"\d+\s?행|^\d+$", "", "%s" % s)       # noqa: E731
    return (z.get("번호"), 줄뺌(z.get("항목")), 줄뺌(z.get("내용")))


def _절범위(t, z):
    """막음의 자리 · 내용이 가리키는 절의 줄 범위들 [(첫 줄, 끝 줄, 첫 산문 줄)] — 머리 줄 글 · 「3분 레터」 · 「본편 결론」 · 「민감도 절」."""
    import 레터게이트 as G                                    # noqa: PLC0415
    줄들 = t.split("\n")
    낸 = []

    def 범(s):
        e = next((k for k in range(s + 1, len(줄들)) if 줄들[k].startswith("#") and len(re.match(r"#+", 줄들[k]).group(0))
                  <= len(re.match(r"#+", 줄들[s]).group(0))), len(줄들))
        첫 = next((k for k in range(s + 1, e) if 줄들[k].strip() and not 줄들[k].strip().startswith(("|", "<!--", "#", "**그림"))), s)
        낸.append((s + 1, e, 첫 + 1))
    자리 = ("%s" % z.get("자리")).strip()
    if 자리.startswith("#"):
        for k, 줄 in enumerate(줄들):
            if 줄.startswith(자리[:40]):
                범(k)
                break
    말 = "%s %s" % (자리, z.get("내용"))
    for 단서, f in (("3분 레터", lambda: G._삼분글(t)), ("결론", lambda: G._절글(t, "결론")), ("민감도", lambda: G._절글(t, "민감도"))):
        if 단서 in 말:
            try:
                g = f()
            except Exception:                                 # noqa: BLE001
                g = None
            i = t.find(g) if g else -1
            if i >= 0:
                범(t.count("\n", 0, i) + (1 if g.startswith("\n") else 0))
    return 낸


def _주인줄(새글, 글, 결, 바뀐조각):
    """표시 번호 → 시험 초안에서 그 표시가 선 줄 범위들 · 새 글 · 옛 글(원문). 지운 표시는 옛 자리 앞 글이 선 줄."""
    새편 = {i: 신 for i, _o, 신 in 바뀐조각}
    줄, 편들, 원들 = {}, {}, {}
    for i, x in enumerate(결["표시"], 1):
        if x.get("처리") not in ("묶음", "편집목록"):
            continue
        신 = 새편.get(i) if x.get("처리") == "묶음" else (x.get("_편") or "")
        if x.get("처리") == "묶음" and 신 is None:
            신 = x.get("_편") or ""
        편들[i], 원들[i] = 신 or "", x.get("원문") or ""
        자 = [(새글.count("\n", 0, p) + 1, 새글.count("\n", 0, q) + 1) for p, q in (_모든자리(새글, 신) if 신 else [])]
        if not 자:
            a = (x.get("_자리") or [0])[0]
            앞 = 글[max(0, a - 40):a].strip()[-30:]
            k = 새글.find(앞) if len(앞) >= 8 else -1
            if k >= 0:
                n = 새글.count("\n", 0, k + len(앞)) + 1
                자 = [(n, n)]
        줄[i] = 자
    return 줄, 편들, 원들


def _느슨(s):
    return re.sub(r"\([^)]*\)|\s|\*\*", "", "%s" % s)


def _돌릴곳(z, 주인, 새글, 편들, 원들):
    """새로 선 막음 하나 → 그 막음을 낸 표시 번호들. 줄 → 낫표 안의 이름 · 글(그 말을 새로 넣거나 뺀 표시) → 절 단서(첫 산문 줄 먼저) 차례로 좁힌다."""
    행들 = _행들(z)
    누구 = [i for i, rs in 주인.items() if any(p <= n <= q for n in 행들 for p, q in rs)]
    조각 = [m.strip(" …·.") for m in re.findall(r"「([^」]{2,80})」", "%s %s" % (z.get("자리"), z.get("내용")))]
    조각 = [m for m in 조각 if len(m) >= 2]
    부분 = {_느슨(u) for m in 조각 for u in [m] + re.split(r"\s*[·,]\s*|\s+(?:와|과|및)\s+", m)}
    부분 = [u for u in 부분 if len(u) >= 4]

    def 건드림(i):                                             # 그 말을 새로 넣었거나(편에만) 뺐다(원문에만)
        편, 원 = _느슨(편들.get(i)), _느슨(원들.get(i))
        return any((u in 편) != (u in 원) for u in 부분)
    if len(누구) > 1 and 조각:
        누구 = [i for i in 누구 if any(m in 편들[i] for m in 조각)] or [i for i in 누구 if 건드림(i)] or 누구
    if not 누구 and 조각:
        누구 = [i for i in 주인 if 편들[i] and any(m in 편들[i] for m in 조각)] or [i for i in 주인 if 건드림(i)]
    if not 누구:
        for s, e, 첫 in _절범위(새글, z):
            안 = [i for i, rs in 주인.items() if any(not (q < s or e < p) for p, q in rs)]
            앞 = [i for i in 안 if any(p <= 첫 <= q for p, q in 주인[i])]
            누구 = [i for i in 안 if 건드림(i)] or 앞 or 안
            if 누구:
                break
    return sorted(set(누구))


def _편집돌림(바탕, 목록, 장부):
    """`회차실행.편집적용` 을 돌린다 → (글, 「안 됨」 [(목록 번호(1부터), 글)]) — 부록이 달라지면 (None, [(0, 까닭)])."""
    import 회차실행 as R                                      # noqa: PLC0415
    try:
        새, _됨, 안 = R.편집적용(바탕, 목록, 장부 if isinstance(장부, dict) else None)
    except ValueError as e:
        return None, [(0, "%s" % e)]
    낸 = []
    for s in 안:
        m = re.match(r"(\d+) — (.*)", s)
        낸.append((int(m.group(1)), m.group(2)) if m else (0, s))
    return 새, 낸


def 게이트차이(회차, 글, 결, 장부, 가정, 회, 앞목록, 맞춘앞, 맞춘새, 바뀐조각, 새묶음=None, 옛=None):
    """시험 초안(원고 묶음의 고침은 레터 모든 같은 글 자리에 · 편집 목록은 `회차실행.편집적용` 으로)과 표시 전 글에 게이트 판정(`판정모음`)을 함께 돌려
    뒤에만 선 막음을 그 표시에 돌린다. 편집 단계의 「안 됨」 도 미리 본다(이번 항목 → 그 표시 · 앞 회 항목이 새로 안 되면 겹친 묶음 표시).
    → ({표시 번호: [까닭]}, [가르지 못한 알림], 옛 캐시)."""
    import copy                                               # noqa: PLC0415
    import 레터게이트 as G                                    # noqa: PLC0415
    바탕, 쓸앞 = 글, False                                    # 바탕 — 장부의 초안(글 해시가 같으면)에 이 회 앞의 편집 목록을 · 없으면 지금 레터만
    초p = os.path.join(회차, "레터_초안.md")
    if os.path.isfile(초p):
        t = _글읽기(초p)
        if _sha(t) == (장부 or {}).get("글해시"):
            바탕, 쓸앞 = t, True
    if 옛 is None:
        옛글, 옛안 = _편집돌림(바탕, 앞목록 if 쓸앞 else [], 장부)
        옛글 = 옛글 if 옛글 is not None else 글
        옛 = {"글": 옛글, "안됨": {(앞목록[k - 1].get("원문") if 쓸앞 and 0 < k <= len(앞목록) else k) for k, _s in 옛안},
             "목록": 판정모음(옛글, 장부, 가정, 회차)}
        옛["판정"] = collections.Counter(_판정열쇠(z) for z in 옛["목록"])
    걸, 알 = {}, []
    목 = (list(맞춘앞) if 쓸앞 else []) + list(맞춘새)
    새글, 안 = _편집돌림(조각적용(바탕, 바뀐조각), 목, 장부)
    n앞 = len(목) - len(맞춘새)
    for k, s in 안:
        if k > n앞:
            i = 맞춘새[k - n앞 - 1].get("_주인")
            if i:
                걸.setdefault(i, []).append("편집 단계 「안 됨」 — %s" % s[:160])
                continue
        elif 0 < k <= n앞:
            옛원 = 앞목록[k - 1].get("원문") if k - 1 < len(앞목록) else None
            if 옛원 in 옛["안됨"]:
                continue
            누 = [i for i, o, _n in 바뀐조각 if any(len(u) >= 8 and u in (옛원 or "") for u in 문장들(o))]
            if 누:
                for i in 누:
                    걸.setdefault(i, []).append("앞 회 편집 항목 %d 이 이 고침 뒤 「안 됨」 이 된다(원고 조각의 일부만 그 항목에 들었다) — %s" % (k, s[:120]))
                continue
        알.append("편집 시험 「안 됨」 — %s" % s[:160])
    if 새글 is None:
        return 걸, 알, 옛
    if G._표줄(본문(조각적용(바탕, 바뀐조각))) != G._표줄(본문(새글)):     # ④ — 편집 항목이 표 줄까지 바꿨다
        표줄 = set(G._표줄(본문(조각적용(바탕, 바뀐조각)))) - set(G._표줄(본문(새글)))
        for h in 맞춘새:
            if h.get("_주인") and any(h.get("원문") and h["원문"] in 줄 for 줄 in 표줄):
                걸.setdefault(h["_주인"], []).append("게이트 ④ 편집 항목이 본문 표 줄까지 바꾼다 — 「%s」" % h["원문"][:60])
    장t = dict(장부 or {})
    if 바뀐조각 and 장t.get("원고"):
        새원고 = []
        for g in 장t["원고"]:
            for _i, o, n in 바뀐조각:
                if isinstance(g, str) and len(_맨(o)) >= 8:
                    for o2, n2 in _조각꼴(o, n):
                        g = g.replace(o2, n2)
            새원고.append(g)
        장t["원고"] = 새원고
    음들, 폭들 = [], []                                        # 묶음에 새로 선 부호 뒤집기 자리표시(「{음 키|꼴}」) — 넣기 · 초안 뒤 장부에 그 값(부호 반대 · 부호 뗀 글)이 선다
    표식 = _자리표식()
    for x in 결["표시"]:
        if x.get("처리") == "묶음":
            바 = x.get("바꿈") or {}
            for m in 표식.finditer(바.get("새") or ""):
                안 = m.group(1).strip()
                if 안.startswith("음 ") and m.group(0) not in (바.get("옛") or ""):
                    음들.append((안[2:].strip(), (m.group(2) or "").strip()))
                elif re.fullmatch(r"폭p?\d", (m.group(2) or "").strip()) and m.group(0) not in (바.get("옛") or ""):
                    폭들.append((안, (m.group(2) or "").strip()))      # 1.1.19 — 크기 꼴(부호를 늘 찍는 꼴에서 부호를 뗀 값 — 자리되돌림)
    if 음들 or 폭들:
        숫자t = list(장t.get("숫자") or [])
        for 키, 꼴 in 음들:
            y = next((y for y in 숫자t if isinstance(y, dict) and "%s" % y.get("키") == 키 and (not 꼴 or y.get("꼴") == 꼴)
                      and isinstance(y.get("값"), (int, float)) and y.get("글")), None)
            if y is not None:
                숫자t.append(dict(y, 키="음 " + 키, 값=-y["값"], 글=re.sub(r"^[−\-+]", "", "%s" % y["글"])))
        맵t = 장부글(장t) if 폭들 else None
        for 안, 꼴 in 폭들:                                   # 넣기 · 초안 뒤 장부에 같은 키 · 크기 꼴 줄(같은 값 · 부호 뗀 글)이 선다
            키 = 맵t.키(안)
            if 키 is None or (키, 꼴) in 맵t.글:
                continue
            원꼴 = ("퍼p" if 꼴.startswith("폭p") else "증") + 꼴[-1]
            y = next((y for y in 숫자t if isinstance(y, dict) and "%s" % y.get("키") == 키 and y.get("꼴") == 원꼴 and y.get("글")), None)
            if y is not None:
                숫자t.append(dict(y, 꼴=꼴, 글=re.sub(r"^[−\-+]", "", "%s" % y["글"])))
                맵t.글[(키, 꼴)] = 숫자t[-1]["글"]
        장t["숫자"] = 숫자t
    if 바뀐조각 and isinstance(장t.get("원고자리"), dict):          # ⑭ 편집본 대조의 요소 문단도 넣기 뒤의 글로
        자리t = {}
        for k, v in 장t["원고자리"].items():
            if isinstance(v, dict) and isinstance(v.get("글"), str):
                g = v["글"]
                for _i, o, n in 바뀐조각:
                    if len(_맨(o)) >= 8:
                        for o2, n2 in _조각꼴(o, n):
                            g = g.replace(o2, n2)
                v = dict(v, 글=g)
            자리t[k] = v
        장t["원고자리"] = 자리t
    가t = 가정
    if 새묶음 and isinstance(가정, dict):
        try:
            import 레터원고 as _W                             # noqa: PLC0415
            가t = _W.넣기(copy.deepcopy(가정), [(n, copy.deepcopy(d)) for n, d in 새묶음.items()], None, 방식="묶음우선")[0]
        except Exception as e:                                # noqa: BLE001
            알.append("시험 초안의 가정을 넣지 못해 지금 가정으로 판정했다(%s)" % type(e).__name__)
    옛셈 = collections.Counter(옛["판정"])
    주인, 편들, 원들 = _주인줄(새글, 글, 결, 바뀐조각)
    새판 = 판정모음(새글, 장t, 가t, 회차)
    남판 = []
    for z in 새판:                                            # 같은 막음(번호 · 항목 · 내용 — 줄 번호 뺌)은 표시 전에도 있었다
        k = _판정열쇠(z)
        if 옛셈[k] > 0:
            옛셈[k] -= 1
        else:
            남판.append(z)
    남옛, 옛자리 = collections.Counter(옛셈), collections.Counter()
    for z in 옛["목록"]:
        k = _판정열쇠(z)
        if 남옛[k] > 0:
            남옛[k] -= 1
            if _자리열쇠(z):
                옛자리[(k[0], k[1], _자리열쇠(z))] += 1
    for z in 남판:
        k = _판정열쇠(z)
        r = (k[0], k[1], _자리열쇠(z))
        if r[2] and 옛자리[r] > 0:                            # 자리(절 머리 · 가정 칸)가 같은 막음이 표시 전에도 있었다 — 내용 글만 달라졌다
            옛자리[r] -= 1
            continue
        누구 = _돌릴곳(z, 주인, 새글, 편들, 원들)
        말 = "게이트 %s %s — %s" % (z.get("번호"), z.get("항목"), ("%s" % z.get("내용"))[:140])
        if 누구:
            for i in 누구:
                걸.setdefault(i, []).append(말)
        else:
            알.append("시험 초안의 새 막음(표시로 가르지 못함) %s" % 말)
    return 걸, 알, 옛


# ══════════════════════════════════════════════════════════════════ 고리 — 표시된 문장만 다시 쓴다
def _묶음자리(묶음들, 색인, x, 원고, 맵):
    """표시 하나의 다시 쓰기를 묶음에서 찾고 고친 잎을 짓는다 → (찾은, 잎, 까닭, 옛조각, 새조각). 찾지 못하면 찾은이 None."""
    옛조각, 새조각 = x["원문"], x["고친문장"]
    if x.get("몫") == "섞임":
        옛조각, 새조각 = 섞임가르기(x["원문"], x["고친문장"], 원고) or (None, None)
    찾은 = 색인.찾기(옛조각) if 옛조각 is not None else None
    if not 찾은:
        return None, None, None, 옛조각, 새조각
    잎, 까 = 묶음고침(묶음들, 찾은, 새조각, 맵)
    return 찾은, 잎, 까, 옛조각, 새조각


def 요건거절(회차, 가정, 장부, 표시들, 새묶음, 맵, 원고):
    """1.1.15 — 묶음으로 간 다시 쓰기가 원고 요건(블록 요건 — 「밖」 판정 키 · 「한계」 두 문장 · 줄의 가정 · 결과 키 …)을 깨나.
    옛 묶음 · 새 묶음을 메모리에서 가정에 넣고 장부의 요건(`원고요건.요건`)으로 대조해 새로 생긴 누락만 본다(넣기 · 게이트 ⑭ 와 같은 대조).
    누락을 낸 표시는 하나씩 옛 묶음에 얹어 가린다. 하나로 가려지지 않으면(둘이 함께 낸 누락) 그 자리 절의 묶음 표시 모두
    → ({표시 번호(1부터): [까닭]}, [알림])."""
    import copy                                               # noqa: PLC0415
    요 = ((장부 or {}).get("원고요건") or {}).get("요건") or []
    if not isinstance(가정, dict):
        return {}, ["가정 파일을 찾지 못해 묶음 다시 쓰기의 원고 요건을 대조하지 않았다(`--가정`)"]
    if not 요:
        return {}, ["장부에 원고 요건이 없어 묶음 다시 쓰기의 원고 요건을 대조하지 않았다"]
    import 레터                                               # noqa: PLC0415
    import 레터원고 as _W                                     # noqa: PLC0415

    def 누락(묶):
        g, _보, _바 = _W.넣기(copy.deepcopy(가정), [(n, copy.deepcopy(d)) for n, d in 묶.items()], None, 방식="묶음우선")
        return {(x.get("자리"), x.get("까닭")) for x in _W.대조(g, 요, 레터.원고검사)}
    try:
        옛묶 = 묶음읽기(회차)
        옛누 = 누락(옛묶)
        새누 = 누락(새묶음) - 옛누
    except Exception as e:                                    # noqa: BLE001
        return {}, ["묶음 다시 쓰기의 요건 대조를 돌리지 못했다(%s: %s)" % (type(e).__name__, ("%s" % e)[:120])]
    if not 새누:
        return {}, []
    묶표 = [(i, x) for i, x in enumerate(표시들, 1) if x.get("처리") == "묶음"]
    낸 = {}
    for i, x in 묶표:
        한 = copy.deepcopy(옛묶)
        찾은, 잎, _까, _o, _n = _묶음자리(한, 묶음색인(한, 맵), x, 원고, 맵)
        if not 찾은 or 잎 is None:
            continue
        _길쓰기(한[찾은["묶음"]], 찾은["길"], 잎)
        z = (누락(한) - 옛누) & 새누
        if z:
            낸[i] = ["원고 요건 — %s: %s" % (a, b) for a, b in sorted(z)]
    가린 = {k for v in 낸.values() for k in v}
    남 = [(a, b) for a, b in sorted(새누) if "원고 요건 — %s: %s" % (a, b) not in 가린]
    for a, b in 남:                                            # 함께 낸 누락 — 그 자리(Narrative.절글.<절>)를 고친 묶음 표시 모두
        자리말 = "%s" % a
        for i, x in 묶표:
            길 = ".".join("%s" % k for k in (x.get("길") or []))
            길들 = (길, "Narrative." + 길)                      # 묶음의 맨 위 「절글」 은 가정의 Narrative.절글 로 들어간다
            if 자리말 and any(g == 자리말 or g.startswith(자리말 + ".") for g in 길들):
                낸.setdefault(i, []).append("원고 요건(함께 고친 문장과) — %s: %s" % (a, b))
    알림 = ["묶음 다시 쓰기가 낸 요건 누락을 표시로 가르지 못했다 — %s: %s" % (a, b) for a, b in 남 if not any(
        "%s: %s" % (a, b) in w for v in 낸.values() for w in v)]
    return 낸, 알림


def 고리(회차, 표시경로, 장부경로=None, 쓰기=True, 말=print, 가정경로=None):
    """표시 파일 하나를 옮긴다 → 고리 기록 dict. 원고 → 묶음(넣기부터 다시) · 섞임은 코드 틀이 같으면 원고 조각만 묶음으로 ·
    코드 → 편집 목록 「다시쓰기」. 묶음에 없는 원고 조각은 편집 목록으로 옮기되 그 문장의 값이 모두 장부 글일 때만(게이트 ⑦ 의 숫자 훑기).
    1.1.15 — 가정 파일(`가정경로` · 없으면 회차 폴더에서 고름)이 있으면 검사가 게이트 ⑧ · ⑱ 을 보고, 묶음으로 간 다시 쓰기는 메모리에서 넣어
    원고 요건으로 대조한다 — 새 누락을 낸 표시는 거절(남은 목록 · 사람 몫)하고 나머지로 다시 옮긴다.
    1.1.19 — 길을 정한 뒤 시험 초안을 지어 게이트 판정을 표시 전 · 뒤 두 글에 돌리고(`게이트차이`) 뒤에만 선 막음 · 편집 「안 됨」 을 낸 표시를
    거절한다. 같은 원문 표시는 하나로 합치고(`편집항목들`), 원고 묶음이 고친 조각은 편집 목록 항목에도 따라 고친다(`항목맞추기`)."""
    표시 = _읽기(표시경로)
    if not isinstance(표시, dict):
        raise ValueError("표시 파일을 읽지 못했다: %s" % 표시경로)
    회 = int(표시.get("회") or 1)
    레터p = os.path.join(회차, 표시.get("레터") or "레터_초안.md")
    글 = _글읽기(레터p)
    장부 = _읽기(장부경로 or os.path.join(회차, "레터_초안.장부.json"), {}) or {}
    if 표시.get("글해시") and 표시["글해시"] != _sha(글):
        raise ValueError("표시가 지금 %s 과 다른 판을 읽었다(글 해시) — 지금 판으로 다시 읽는다" % os.path.basename(레터p))
    가정p = 가정경로 or 가정찾기(회차)
    가정 = _읽기(가정p) if 가정p else None
    가정 = 가정 if isinstance(가정, dict) else None
    결 = 검사(표시, 글, 장부, 가정=가정, 일관=not 장부)
    준비값 = _읽기(os.path.join(회차, 곳, "준비_%d.json" % 회))
    if 준비값 and 준비값.get("글해시") == _sha(글):
        구조합치기(결, 준비값)
    맵 = 장부글(장부)
    원고 = 장부.get("원고") or []
    편목p = os.path.join(회차, "_raw", "편집목록.json")
    편목 = _읽기(편목p, []) or []
    if not isinstance(편목, list):
        raise ValueError("편집 목록이 목록 꼴이 아니다: %s" % 편목p)
    앞목록 = [h for h in 편목 if not (isinstance(h, dict) and h.get("종류") == "다시쓰기" and h.get("회") == 회)]   # 같은 회를 다시 돌리면 갈음
    옛판 = None
    for _돌 in range(10):
        묶음들, 바뀐묶음, 새항목, 바뀐조각 = 옮기기(결, 글, 묶음읽기(회차), 맵, 원고, 회)
        맞춘앞, 맞춤1 = 항목맞추기(앞목록, 바뀐조각)
        맞춘새, 맞춤2 = 항목맞추기(새항목, 바뀐조각)
        걸 = {}
        for r in 맞춤2:                                       # 같은 원고 조각을 묶음과 편집 목록이 다르게 고쳤다(두 길) — 편집 쪽 표시를 거절
            i = 맞춘새[r["항목"]].get("_주인")
            if r["엇갈림"] and i and i != r["표시"]:
                걸.setdefault(i, []).append("표시 %d 이 원고 묶음에서 고친 조각 「%s」 을 이 표시가 다른 글로 고쳤다 — 같은 원고 조각은 한 표시로 고친다"
                                          "(낫표 안을 그 표시의 고친 글로 맞추거나 표시를 하나로 합친다)" % (r["표시"], _조각이름(바뀐조각, r["표시"])))
        if 바뀐묶음:
            걸요, 알 = 요건거절(회차, 가정, 장부, 결["표시"], 묶음들, 맵, 원고)
            결["경보"] += [w for w in 알 if w not in 결["경보"]]
            for i, 까 in 걸요.items():
                걸.setdefault(i, []).extend(까)
        if 장부:
            걸게, 알게, 옛판 = 게이트차이(회차, 글, 결, 장부, 가정, 회, 앞목록, 맞춘앞, 맞춘새, 바뀐조각, 묶음들 if 바뀐묶음 else None, 옛판)
            for i, 까 in 걸게.items():
                걸.setdefault(i, []).extend(까)
            결["경보"] += [w for w in 알게 if w not in 결["경보"] and w.startswith("시험 초안의 가정")]
            if not 걸:
                결["경보"] += [w for w in 알게 if w not in 결["경보"]]
        걸 = {i: 까 for i, 까 in 걸.items() if 결["표시"][i - 1].get("처리") != "거절"}
        if not 걸:
            break
        for i, 까 in sorted(걸.items()):
            x = 결["표시"][i - 1]
            결["거절"].append((i, " · ".join(까)))
            x["처리"], x["거절"] = "거절", list(x.get("거절") or []) + 까
            for k in ("묶음", "길", "닮음", "바꿈", "원고조각", "값블록", "편집원문", "합친곳", "항목맞춤", "옮김"):
                x.pop(k, None)
    for x in 결["표시"]:                                      # 편집원문 — 맞춘 뒤의 원문(되돌림이 이 표시가 낸 항목만 뺀다)
        if x.get("처리") == "편집목록":
            x["편집원문"] = []
    for i, h in [(h.get("_주인"), h) for h in 맞춘새 if isinstance(h, dict)]:
        if i and 결["표시"][i - 1].get("처리") == "편집목록":
            결["표시"][i - 1]["편집원문"].append(h["원문"])
    for r in 맞춤1 + 맞춤2:                                   # 되돌림이 묶음 고침을 되돌리면 따라 고친 항목도 되돌린다
        x = 결["표시"][r["표시"] - 1]
        if x.get("처리") == "묶음":
            x.setdefault("항목맞춤", []).append({k: r[k] for k in ("옛원문", "새원문", "옛새글", "새새글")})
    새편목 = [{k: v for k, v in h.items() if not k.startswith("_")} if isinstance(h, dict) else h for h in 맞춘앞 + 맞춘새]
    return 고리마침(회차, 결, 글, 장부, 표시, 회, 새편목, 편목p, 묶음들, 바뀐묶음, len(맞춘새), 쓰기, 말,
                 맞춘수=len({r["항목"] for r in 맞춤1}))


def _조각이름(바뀐조각, i):
    return next((o[:40] for j, o, _n in 바뀐조각 if j == i), "")


def 옮기기(결, 글, 묶음들, 맵, 원고, 회):
    """검사를 지난 표시를 옮긴다 — 원고 · 섞임은 묶음(자리를 찾으면) · 그 밖은 편집 목록 항목 → (묶음들, 바뀐 묶음, 새 편집 항목, 바뀐 조각).
    바뀐 조각 = [(표시 번호, 옛 레터 글, 새 편 글)] — 묶음 고침이 넣기 · 초안 뒤 레터에 세울 글. 새 편집 항목은 「_주인」(표시 번호)을 단다.
    1.1.19 — 같은 원고 조각을 앞 표시가 이미 고쳤으면 같은 글이면 「합침」, 다른 글이면 거절(한 조각이 묶음 · 편집 목록 두 길로 가지 않게).
    같은 원문의 편집 표시가 둘 이상이면 고친 문장이 같으면 앞 표시 하나로 합치고(뒤는 「합침」), 다르면 자리마다 따로 항목을 낸다."""
    색인 = 묶음색인(묶음들, 맵)
    바뀐묶음 = set()
    새항목, 바뀐조각, 편길 = [], [], []
    for i, x in enumerate(결["표시"], 1):
        if x.get("처리") in ("거절", "구조"):
            continue
        for k in ("남은까닭", "옮김", "묶음", "길", "닮음", "바꿈", "원고조각", "값블록", "편집원문", "합친곳", "항목맞춤"):   # 다시 옮길 때 앞 판의 자취를 지운다
            x.pop(k, None)
        x["처리"] = None
        if x.get("고친문장") is None:
            x["처리"] = "표시만"
            continue
        고친 = x["고친문장"]
        몫 = x.get("몫")
        옮김 = None
        if 몫 in ("원고", "섞임"):
            옛조각, 새조각 = x["원문"], 고친
            if 몫 == "섞임":
                옛조각, 새조각 = 섞임가르기(x["원문"], 고친, 원고) or (None, None)
            if 옛조각 is not None:
                새편 = (x.get("_편") or "") if 몫 == "원고" else 펴기(새조각, 맵)[0]
                앞 = next(((j, n) for j, o, n in 바뀐조각 if _맨(o) == _맨(옛조각)), None)
                if 앞:
                    if _맨(앞[1]) == _맨(새편):
                        x["처리"], x["합친곳"] = "합침", 앞[0]
                    else:
                        까 = "표시 %d 이 같은 원고 조각을 다른 글로 고쳤다 — 같은 조각은 한 표시로 고친다" % 앞[0]
                        x["처리"], x["거절"] = "거절", list(x.get("거절") or []) + [까]
                        결["거절"].append((i, 까))
                    continue
            찾은, 잎, 까, 옛조각, 새조각 = _묶음자리(묶음들, 색인, x, 원고, 맵)
            if 찾은:
                if 잎 is None:
                    x["처리"], x["남은까닭"] = "남김", 까
                    continue
                _길쓰기(묶음들[찾은["묶음"]], 찾은["길"], 잎)
                색인.다시(찾은["묶음"], 찾은["길"], 잎)
                바뀐묶음.add(찾은["묶음"])
                x.update({"처리": "묶음", "묶음": 찾은["묶음"], "길": 찾은["길"], "닮음": 찾은["닮음"], "바꿈": 까})
                바뀐조각.append((i, 옛조각, (x.get("_편") or "") if 몫 == "원고" else (펴기(새조각, 맵)[0] if 새조각 else "")))
                if 몫 == "섞임":
                    x["원고조각"] = [옛조각, 새조각]
                if 찾은["길"] and 찾은["길"][0] in ("신호", "서술", "메타"):
                    x["값블록"] = True
                continue
            # 묶음에서 자리를 찾지 못했다 — 편집 목록으로 옮기되, 원고 조각이 바뀐 글의 값은 모두 장부 글이어야 한다(게이트 ⑦ 이 원고 조각만 숫자 훑기에서 뺀다)
            if 몫 == "섞임" and 옛조각 is not None:
                바뀐글 = 새조각
            elif 몫 == "원고":
                바뀐글 = 고친
            else:                                             # 코드 틀을 바꾼 섞임 — 원고 조각이 글자 그대로 남으면 바뀐 원고 글은 없다
                남는다 = all(_맨(x["원문"][a:b]) in _맨(고친) for a, b in 든조각(x["원문"], 원고))
                바뀐글 = "" if 남는다 else 고친
            밖 = 장부밖값(펴기(바뀐글, 맵)[0], 맵)
            if 밖:
                x["처리"], x["남은까닭"] = "남김", "원고 묶음에서 자리를 찾지 못했고 바뀐 원고 글에 장부 밖 값이 있다(%s)" % " · ".join(밖[:3])
                continue
            옮김 = "편집목록(%s — 묶음 자리 없음)" % 몫
        편길.append((i, x, 옮김))
    # 같은 원문 표시 묶기 — 같은 코드 문장이 여러 자리에 있고 표시가 둘 이상이면(교열자가 자리마다 표시) 하나로
    무리 = collections.OrderedDict()
    for t in 편길:
        무리.setdefault(t[1]["원문"], []).append(t)
    막힌 = [tuple(y["_자리"]) for y in 결["표시"] if y.get("_자리") and y.get("처리") not in ("거절", "구조", "표시만", "남김", "합침")]
    for _원, 떼 in 무리.items():
        머 = 떼[0][1]
        같은 = [t for t in 떼[1:] if _맨(t[1].get("고친문장") or "") == _맨(머.get("고친문장") or "")]
        다른 = [t for t in 떼[1:] if t not in 같은]
        머됨 = True
        for i, x, 옮김 in [떼[0]] + 다른:
            항들, 왜 = 편집항목들(글, x, 회, [z for z in 막힌 if z != tuple(x["_자리"])], 퍼뜨림=not 다른)
            if 왜:
                x["처리"], x["남은까닭"] = "남김", 왜
                머됨 = 머됨 and x is not 머
                continue
            for h in 항들:
                h["_주인"] = i
            새항목 += 항들
            x["처리"], x["편집원문"] = "편집목록", [h["원문"] for h in 항들]
            if 옮김:
                x["옮김"] = 옮김
        for _i, y, _o in 같은:
            if 머됨:
                y["처리"], y["합친곳"] = "합침", 떼[0][0]
            else:
                y["처리"], y["남은까닭"] = "남김", 머.get("남은까닭")
    return 묶음들, 바뀐묶음, 새항목, 바뀐조각


def 고리마침(회차, 결, 글, 장부, 표시, 회, 편목, 편목p, 묶음들, 바뀐묶음, 새수, 쓰기, 말, 맞춘수=0):
    """고리의 끝 — 편집 목록(앞 회 항목 + 이 회 항목 — 이미 맞춘 것) · 묶음 · 고리 기록 · 교열 대장을 쓰고 한 줄로 알린다 → 고리 기록."""
    셈 = 대장셈(결["표시"], 글)
    기록 = collections.OrderedDict([("형식", 고리형식), ("판", 판), ("회", 회), ("레터", 표시.get("레터") or "레터_초안.md"),
                                    ("글해시", _sha(글)), ("일시", datetime.datetime.now().replace(microsecond=0).isoformat()),
                                    ("셈", 셈), ("바뀐묶음", sorted(바뀐묶음)), ("편집목록덧", 새수), ("앞항목맞춤", 맞춘수),
                                    ("값블록", any(x.get("값블록") for x in 결["표시"])), ("거절", 결["거절"]), ("경보", 결["경보"]),
                                    ("표시", [{k: v for k, v in x.items() if not k.startswith("_")} for x in 결["표시"]])])
    if 쓰기:
        if 바뀐묶음:
            뒤곳 = os.path.join(회차, 곳, "묶음_전_%d" % 회)
            os.makedirs(뒤곳, exist_ok=True)
            for n in 바뀐묶음:
                src = os.path.join(회차, "_raw", "레터원고", n)
                dst = os.path.join(뒤곳, n)
                if not os.path.exists(dst):
                    with open(src, "rb") as f, open(dst, "wb") as g:
                        g.write(f.read())
                _쓰기(src, 묶음들[n])
        if 새수 or 맞춘수 or os.path.isfile(편목p):
            _쓰기(편목p, 편목)
        _쓰기(os.path.join(회차, 곳, "고리_%d.json" % 회), 기록)
        대장덧(회차, 기록, 장부)
    말("교열 고리 %d회 — 표시 %d · 묶음 %d(파일 %d) · 편집 목록 %d · 합침 %d · 표시만 %d · 거절 %d · 남김 %d · 구조 %d" % (
        회, 셈["표시"], 셈["처리"].get("묶음", 0), len(바뀐묶음), 셈["처리"].get("편집목록", 0), 셈["처리"].get("합침", 0),
        셈["처리"].get("표시만", 0), 셈["처리"].get("거절", 0), 셈["처리"].get("남김", 0), 셈["처리"].get("구조", 0)))
    if 맞춘수:
        말("  앞 회 편집 항목 %d개의 원문 · 새글을 이번 원고 묶음 고침에 맞췄다(넣기 뒤 초안의 글과 같게)" % 맞춘수)
    if 바뀐묶음:
        말("  원고 묶음이 바뀌었다 — 넣기 → 초안 → 편집 → 게이트를 다시 돈다(`회차실행.py --단계 넣기,초안,교열,편집,게이트`)")
    if 기록["값블록"]:
        말("  ! 값 해시 안의 블록(신호 · 서술 · 메타)을 고쳤다 — 붓기 → 워크북 마감을 한 번 더 돈다")
    return 기록


# ══════════════════════════════════════════════════════════════════ 교열 대장
def 대장셈(표시들, 글, 자=None):
    자 = 자 if 자 is not None else len(re.sub(r"\s", "", "\n".join(t for _n, t in 레터구조.읽기(글)["본편"])))
    교 = [x for x in 표시들 if x.get("처리") != "구조"]
    처 = collections.Counter(x.get("처리") or "?" for x in 표시들)
    return collections.OrderedDict([
        ("산문글자", 자), ("표시", len(교)), ("만자당", round(len(교) * 10000.0 / max(자, 1), 1)),
        ("원칙", dict(sorted(collections.Counter("%d" % n for x in 교 for n in (x.get("원칙") or [])).items(), key=lambda t: int(t[0])))),
        ("유형", dict(collections.Counter(x.get("유형") or "?" for x in 교))),
        ("몫", dict(collections.Counter(x.get("몫") or "?" for x in 교))),
        ("처리", dict(처)),
        ("고친", 처.get("묶음", 0) + 처.get("편집목록", 0) + 처.get("합침", 0)),
        ("남은", sum(처.get(k, 0) for k in 남은처리)),
    ])


def 되돌림(회차, 회, 줄들=(), 번호들=(), 까닭="게이트가 막음", 편집경로=None, 장부경로=None, 말=print):
    """게이트가 막은 다시 쓰기를 되돌린다 — 편집본의 줄(게이트가 알린 행) 또는 고리 기록의 표시 번호(1부터)로 고른 표시를
    옛 글로 되돌리고(편집 목록 「다시쓰기」 항목은 빼고 · 묶음 자리는 고리가 남긴 바꿈으로) 처리를 「되돌림」 으로 적는다(남은 목록 · 사람 몫).
    다시 쓴 문장이 게이트 · 인터랙티브 판이 찾는 말이나 이름 · 값 짝(⑱)을 건드리면 그 문장만 되돌리고 다시 돈다. → 되돌린 수."""
    p = os.path.join(회차, 곳, "고리_%d.json" % 회)
    g = _읽기(p)
    if not isinstance(g, dict):
        raise ValueError("고리 기록이 없다: %s" % p)
    편p = 편집경로 or os.path.join(회차, "레터_편집.md")
    줄글 = _글읽기(편p).split("\n") if os.path.isfile(편p) else []
    고를 = []
    표들 = g.get("표시") or []
    for i, x in enumerate(표들, 1):
        if x.get("처리") not in ("묶음", "편집목록"):
            continue
        if i in 번호들:
            고를.append(i)
            continue
        보 = x["원고조각"][1] if x.get("원고조각") else x.get("고친문장")
        머 = _맨((문장들(보) or [""])[0])[:30] if 보 else ""
        if 머 and any(0 < n <= len(줄글) and 머 in _맨(줄글[n - 1]) for n in 줄들):
            고를.append(i)
    묶음들 = 묶음읽기(회차)
    바뀐 = set()
    편목p = os.path.join(회차, "_raw", "편집목록.json")
    편목 = _읽기(편목p, []) or []
    n = 0
    for i in 고를:
        x = 표들[i - 1]
        if x["처리"] == "편집목록":
            뺄 = x.get("편집원문")                            # 1.1.19 — 이 표시가 낸 항목만(같은 원문의 다른 표시가 낸 항목 · 지움은 둔다)
            if isinstance(뺄, list):
                남길, 뺄 = [], list(뺄)
                for h in 편목:
                    if isinstance(h, dict) and h.get("종류") == "다시쓰기" and h.get("회") == 회 and h.get("원문") in 뺄:
                        뺄.remove(h.get("원문"))
                        continue
                    남길.append(h)
                편목 = 남길
            else:                                             # 옛 고리 기록(1.1.18 앞) — 원문으로
                편목 = [h for h in 편목 if not (isinstance(h, dict) and h.get("종류") == "다시쓰기" and h.get("회") == 회
                                             and (h.get("원문") or "").strip() == x["원문"].strip())]
        else:
            d = 묶음들.get(x.get("묶음"))
            잎 = d
            for k in x.get("길") or []:
                잎 = 잎[k] if isinstance(잎, (dict, list)) else None
            새잎 = 묶음되돌림(잎, x.get("바꿈") or {}) if isinstance(잎, str) else None
            if 새잎 is None:
                말("  ! 묶음 자리를 찾지 못해 되돌리지 못했다 — %s" % x["원문"][:60])
                continue
            _길쓰기(d, x["길"], 새잎)
            바뀐.add(x["묶음"])
            for r in x.get("항목맞춤") or []:                  # 1.1.19 — 이 묶음 고침에 맞춰 고친 편집 항목도 옛 글로(초안이 옛 조각으로 돌아온다)
                for h in 편목:
                    if isinstance(h, dict) and h.get("원문") == r.get("새원문") and h.get("새글") == r.get("새새글"):
                        h["원문"], h["새글"] = r.get("옛원문"), r.get("옛새글")
                        break
        x["처리"], x["남은까닭"] = "되돌림", 까닭
        n += 1
        for y in 표들:                                         # 1.1.19 — 이 표시에 합친 표시(같은 원문 · 같은 조각)도 함께 되돌림
            if y.get("처리") == "합침" and y.get("합친곳") == i:
                y["처리"], y["남은까닭"] = "되돌림", "%s(표시 %d 와 함께)" % (까닭, i)
    if n:
        for 이름 in 바뀐:
            _쓰기(os.path.join(회차, "_raw", "레터원고", 이름), 묶음들[이름])
        _쓰기(편목p, 편목)
        g["셈"] = 대장셈(g["표시"], "", (g.get("셈") or {}).get("산문글자") or 0)
        g["되돌림"] = (g.get("되돌림") or []) + [{"줄": list(줄들), "번호": list(번호들), "까닭": 까닭, "수": n}]
        _쓰기(p, g)
        대장덧(회차, g, _읽기(장부경로 or os.path.join(회차, "레터_초안.장부.json"), {}))
    말("교열 되돌림 %d회 — %d건(묶음 파일 %d)%s" % (회, n, len(바뀐), " — 묶음이 바뀌었으니 넣기부터 다시 돈다" if 바뀐 else ""))
    return n


def _회사(장부, 회차):
    return ("%s" % ((장부 or {}).get("회사") or "")).strip() or os.path.basename(os.path.abspath(회차))


def 대장덧(회차, 기록, 장부=None):
    """고리 기록 하나를 교열 대장(`_기록/교열대장.json` · `.md`)에 쌓는다 — 같은 회 · 같은 글 해시는 갈음한다.
    줄 꼴은 지적 대장과 같은 여섯 칸(날짜 · 회사 · 절 · 원문 · 고친 문장 · 유형)에 원칙 · 몫 · 회 · 처리를 더한 것이다."""
    p = os.path.join(회차, 대장곳 + ".json")
    d = _읽기(p) or {"형식": 대장형식, "회차": [], "줄": []}
    날 = (기록.get("일시") or "")[:10]
    회사 = _회사(장부, 회차)
    열 = (기록["회"], 기록["글해시"])
    d["회차"] = [x for x in d.get("회차") or [] if (x.get("회"), x.get("글해시")) != 열]
    d["줄"] = [x for x in d.get("줄") or [] if (x.get("회"), x.get("글해시")) != 열]
    d["회차"].append(collections.OrderedDict([("날짜", 날), ("회사", 회사), ("레터", 기록.get("레터")), ("글해시", 기록["글해시"]),
                                             ("회", 기록["회"])] + list(기록["셈"].items())))
    for x in 기록.get("표시") or []:
        d["줄"].append(collections.OrderedDict([("날짜", 날), ("회사", 회사), ("절", x.get("절") or ""), ("원문", x.get("원문") or ""),
                                               ("고친문장", x.get("고친문장")), ("유형", x.get("유형")), ("원칙", x.get("원칙") or []),
                                               ("몫", x.get("몫")), ("회", 기록["회"]), ("처리", x.get("처리")), ("글해시", 기록["글해시"])]))
    _쓰기(p, d)
    with io.open(os.path.join(회차, 대장곳 + ".md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(대장글(d))
    return d


def _칸(s, n=None):
    s = re.sub(r"\s+", " ", "%s" % ("" if s is None else s)).replace("|", "/").strip()
    return (s[:n] + "…") if n and len(s) > n else s


def 대장글(d):
    줄 = ["# 교열 대장", "", "레터마다 교열 검토의 지적 건수와 유형 분포 — 회마다 한 줄(만 자당 = 3분 레터와 본편 산문 글자 기준).", "",
         "| 날짜 | 회사 | 회 | 산문 글자 | 지적 | 만 자당 | 원칙별 | 유형별 | 코드 · 원고 · 섞임 | 고친 | 남은 |", "|---|---|---:|---:|---:|---:|---|---|---|---:|---:|"]
    for x in d.get("회차") or []:
        줄.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            x.get("날짜"), _칸(x.get("회사")), x.get("회"), format(x.get("산문글자") or 0, ","), x.get("표시"), x.get("만자당"),
            " · ".join("%s:%s" % kv for kv in (x.get("원칙") or {}).items()), " · ".join("%s:%s" % kv for kv in (x.get("유형") or {}).items()),
            " · ".join("%s:%s" % kv for kv in (x.get("몫") or {}).items()), x.get("고친"), x.get("남은")))
    줄 += ["", "## 지적 줄", "", "| 날짜 | 회사 | 절 | 원문 | 고친 문장 | 유형 | 원칙 | 몫 | 회 | 처리 |", "|---|---|---|---|---|---|---|---|---:|---|"]
    for x in d.get("줄") or []:
        고 = x.get("고친문장")
        줄.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            x.get("날짜"), _칸(x.get("회사")), _칸(x.get("절"), 30), _칸(x.get("원문"), 160),
            "(지움)" if 고 == "" else ("—" if 고 is None else _칸(고, 160)), x.get("유형") or "—",
            " · ".join("%s" % n for n in x.get("원칙") or []) or "—", x.get("몫") or "—", x.get("회"), x.get("처리")))
    return "\n".join(줄) + "\n"


def 대장합(폴더들):
    """회차 여럿의 교열 대장을 합친 셈 — 회사마다 마지막 회차의 첫 회(초안 읽기) 줄과 모두의 원칙 · 유형 · 몫 분포."""
    줄, 합원칙, 합유형, 합몫 = [], collections.Counter(), collections.Counter(), collections.Counter()
    for p in 폴더들:
        d = _읽기(os.path.join(p, 대장곳 + ".json"))
        if not d:
            continue
        첫 = [x for x in d.get("회차") or [] if x.get("회") == 1]
        if not 첫:
            continue
        x = 첫[-1]
        줄.append(x)
        합원칙.update({k: v for k, v in (x.get("원칙") or {}).items()})
        합유형.update(x.get("유형") or {})
        합몫.update(x.get("몫") or {})
    return {"회사": 줄, "원칙": dict(합원칙), "유형": dict(합유형), "몫": dict(합몫)}


# ══════════════════════════════════════════════════════════════════ 남은 목록 · 확인
def 고리들(회차):
    낸 = []
    for p in glob.glob(os.path.join(회차, 곳, "고리_*.json")):
        d = _읽기(p)
        if isinstance(d, dict):
            낸.append(d)
    return sorted(낸, key=lambda d: int(d.get("회") or 0))


def 표시들(회차):
    낸 = []
    for p in glob.glob(os.path.join(회차, 곳, "표시_*.json")):
        d = _읽기(p)
        if isinstance(d, dict):
            낸.append((int(d.get("회") or 0), p, d))
    return sorted(낸, key=lambda t: t[0])


def 남은(회차, 편집경로=None, 장부경로=None):
    """두 번 고친 뒤에 남은 표시 → 남은 목록 dict. 마지막 고리의 표시만 · 거절 · 남김 · 구조 · 되돌림 + 앞 회의 남은 표시 가운데 원문이 지금
    편집본에 그대로 있고 마지막 고리가 다시 다루지 않은 것 + 확인 읽기(고리 없는 마지막 표시 파일)의 표시 + 지금 편집본의 막음 지표 자리."""
    고 = 고리들(회차)
    표 = 표시들(회차)
    남 = []
    편p = 편집경로 or os.path.join(회차, "레터_편집.md")
    글 = _글읽기(편p) if os.path.isfile(편p) else ""
    본맨 = _맨(본문(글))
    마지막고리 = 고[-1] if 고 else None
    if 마지막고리:
        for x in 마지막고리.get("표시") or []:
            if x.get("처리") in 남은처리:
                남.append(dict(x, 출처="%d회 고리" % 마지막고리["회"]))
        다룬 = [_맨(x.get("원문") or "") for x in 마지막고리.get("표시") or []]
        for g in 고[:-1]:
            for x in g.get("표시") or []:
                맨 = _맨(x.get("원문") or "")
                if x.get("처리") in 남은처리 and 맨 and 맨 in 본맨 and not any(맨 in d or d in 맨 for d in 다룬 if d):
                    남.append(dict(x, 출처="%d회 고리(뒤 회가 다루지 않음)" % g.get("회")))
    고회 = {g.get("회") for g in 고}
    확 = []
    for n, _p, d in 표:
        if n not in 고회 and n > (마지막고리 or {}).get("회", 0):
            for x in d.get("표시") or []:
                if isinstance(x, dict):
                    확.append(dict(x, 처리="확인 읽기", 출처="%d회 확인 읽기" % n))
    if 확:                                                    # 확인 읽기가 다시 짚은 앞 회의 남은 표시는 확인 읽기 쪽 하나로(새 까닭 · 제안)
        확맨 = [_맨(x.get("원문") or "") for x in 확]
        남 = [x for x in 남 if not any(m and (_맨(x.get("원문") or "") in m or m in _맨(x.get("원문") or "")) for m in 확맨)]
    남 = 확 + 남
    구조남 = []
    if 글:
        장부 = _읽기(장부경로 or os.path.join(회차, "레터_초안.장부.json"), {}) or {}
        값 = 레터구조.지표(글, (), 장부.get("원고") or [])
        for 등, n, 항, 조 in 레터구조.막음걸림(값, 뺄=()):
            구조남.append({"줄": n, "항목": 항, "글": 조, "등급": 등})
    d = collections.OrderedDict([("형식", 남은형식), ("판", 판), ("회", [g.get("회") for g in 고]), ("남은", 남), ("구조", 구조남),
                                 ("셈", {"표시": len(남), "구조": len(구조남)})])
    return d


def 확인읽기대장(회차, 장부경로=None):
    """확인 읽기(고리 없는 마지막 표시 파일)도 교열 대장에 한 줄 — 다시 쓰기 두 회 뒤에 남은 지적의 수와 유형(처리 「확인 읽기」)."""
    고회 = {g.get("회") for g in 고리들(회차)}
    for n, _p, d in 표시들(회차):
        if n in 고회 or not isinstance(d.get("표시"), list):
            continue
        레터p = os.path.join(회차, d.get("레터") or "레터_편집.md")
        글 = _글읽기(레터p) if os.path.isfile(레터p) else ""
        줄들 = 글.split("\n")
        표 = [dict(x, 처리="확인 읽기", 절=절찾기(줄들, int(x.get("줄") or 1))) for x in d["표시"] if isinstance(x, dict)]
        판정 = 레터구조.원고판((_읽기(장부경로 or os.path.join(회차, "레터_초안.장부.json"), {}) or {}).get("원고") or [])
        for x in 표:
            x["몫"] = 몫가르기(판정, x.get("원문") or "") if x.get("원문") else None
            x["유형"] = 유형맞춤(x.get("유형")) or x.get("유형")
        기록 = {"회": n, "글해시": d.get("글해시") or _sha(글), "레터": d.get("레터"), "셈": 대장셈(표, 글),
              "일시": datetime.datetime.now().replace(microsecond=0).isoformat(), "표시": 표}
        대장덧(회차, 기록, _읽기(장부경로 or os.path.join(회차, "레터_초안.장부.json"), {}))


def 남은글(d):
    줄 = ["# 교열 — 남은 표시(사람 몫)", "", "다시 쓰기를 두 번 돈 뒤에도 남은 문장이다. 고친 문장이 조건에 맞지 않았거나(거절), 옮길 길이 없었거나(남김),",
         "교열자가 고친 문장을 내지 않았거나(표시만), 확인 읽기에서 새로 걸린 문장이다.", "",
         "| 줄 | 절 | 원문 | 유형 | 원칙 | 몫 | 까닭 | 남은 까닭 |", "|---:|---|---|---|---|---|---|---|"]
    for x in d.get("남은") or []:
        줄.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
            x.get("줄") or "", _칸(x.get("절"), 24), _칸(x.get("원문"), 180), x.get("유형") or "—",
            " · ".join("%s" % n for n in x.get("원칙") or []) or "—", x.get("몫") or "—", _칸(x.get("까닭"), 80),
            _칸(x.get("남은까닭") or " · ".join(x.get("거절") or []) or x.get("처리"), 80)))
    if d.get("구조"):
        줄 += ["", "## 지금 편집본에 남은 구조 검사 막음 자리", "", "| 줄 | 등급 | 항목 | 글 |", "|---:|---|---|---|"]
        for x in d["구조"]:
            줄.append("| %s | %s | %s | %s |" % (x.get("줄"), x.get("등급"), _칸(x.get("항목"), 80), _칸(x.get("글"), 120)))
    return "\n".join(줄) + "\n"


def 확인(회차):
    """회차실행 「교열」 단계 — 기록이 섰나(판단 구간 L2 의 산출을 읽기만 한다) → (rc, 줄들). 0 = 두 회 고리 + 남은 목록이 섰다
    (또는 두 회 고리 · 대장이 섰고 남은 목록 전 — 남은 목록은 편집 뒤에 낸다 · 「다음 할 일」 줄) ·
    1 = 기록이 없거나 덜 돌았다(발견 — 실행기는 허용하고 진행판에 남긴다)."""
    표 = 표시들(회차)
    고 = 고리들(회차)
    줄 = []
    if not 표:
        return 1, ["교열 검토 기록이 없다 — 판단 구간(교열 검토 · `.claude/갈래/L2_레터교열.md`): 준비 → 교열자 표시 → 고리"]
    for g in 고:
        s = g.get("셈") or {}
        줄.append("%s회 — 지적 %s(만 자당 %s) · 고친 %s · 남은 %s · 묶음 파일 %d · 편집 목록 %s" % (
            g.get("회"), s.get("표시"), s.get("만자당"), s.get("고친"), s.get("남은"), len(g.get("바뀐묶음") or []), g.get("편집목록덧")))
    대 = _읽기(os.path.join(회차, 대장곳 + ".json"))
    if not 대:
        줄.append("교열 대장(_기록/교열대장.json)이 없다")
    남p = os.path.join(회차, 곳, "남은목록.json")
    if len(고) < 회상한 and not os.path.isfile(남p):
        줄.append("다시 쓰기가 %d회다 — 두 회를 돌고 남은 목록을 낸다(`레터교열.py 남은`)" % len(고))
        return 1, 줄
    if not os.path.isfile(남p):
        if 대:                                                # 1.1.19 — 고리 두 회 · 대장이 섰고 남은 목록만 없으면 정상 흐름(남은 목록은 편집본을 읽는다 —
            줄.append("다음 할 일: 편집 단계 뒤 `레터교열.py 남은`(다시 쓰기 %d회가 섰다 · 남은 목록은 편집본 레터_편집.md 를 읽는다)" % len(고))
            return 0, 줄                                      # 사슬 차례 초안 → 교열 → 편집. 회차실행 `교열남은차례` 와 같은 판정)
        줄.append("남은 목록이 없다 — `레터교열.py 남은`")
        return 1, 줄
    남 = _읽기(남p) or {}
    n = (남.get("셈") or {}).get("표시", 0)
    줄.append("남은 표시 %s · 남은 구조 막음 자리 %s(사람 몫 — _raw/교열/남은목록.md)" % (n, (남.get("셈") or {}).get("구조", 0)))
    return (1 if (n or (남.get("셈") or {}).get("구조")) else 0) if 대 else 1, 줄


# ══════════════════════════════════════════════════════════════════ 게이트용 — 문장 단위 대조(다른 갈래가 게이트에 잇는다)
def 문장대조(초안, 편집, 적용=None):
    """편집본 본문의 문장 가운데 초안에 없는 것(바뀐 · 새 문장)마다 숫자가 그 문장을 낸 편집 항목의 원문 안에서만 나오나 → 걸림 [글].
    적용 = 편집 단계 기록(`_raw/편집적용.json` 의 「항목」 — [{원문, 새글}]). 기록이 없으면 None(종전 대조 — 글 전체 숫자 집합 ⊆).
    게이트 ② 의 대조 단위를 글에서 문장으로 내리는 함수다."""
    if 적용 is None:
        return None
    초문 = {_맨(s) for 줄 in 본문(초안).split("\n") for s in 문장들(줄) if not 줄.strip().startswith("|")}
    걸 = []
    for n, 줄 in enumerate(본문(편집).split("\n"), 1):
        if 줄.strip().startswith(("|", "#")):
            continue
        for s in 문장들(줄):
            if _맨(s) in 초문 or not _덩이.search(s):
                continue
            낸 = [x for x in 적용 if isinstance(x, dict) and _맨(s) and _맨(s) in _맨(x.get("새글") or "")]
            if not 낸:
                if any(_수(t) not in {_수(u) for y in 초문 for u in _덩이.findall(y)} for t in _덩이.findall(s)):
                    걸.append("%d행 편집 기록에 없는 새 문장의 숫자 — %s" % (n, s[:60]))
                continue
            if all(숫자조건(x.get("원문") or "", s) for x in 낸):
                걸.append("%d행 원문에 없는 숫자 — %s" % (n, s[:60]))
    return 걸


# ══════════════════════════════════════════════════════════════════ 명령
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(allow_abbrev=False, description="레터 교열 검토 — 준비 · 검사 · 고리 · 남은 · 대장 · 확인")
    ap.add_argument("일", choices=("준비", "검사", "고리", "남은", "대장", "확인", "되돌림"))
    ap.add_argument("대상", nargs="*", help="준비: 레터(.md) · 검사 · 고리: 표시 파일 · 대장: 회차 폴더(여럿이면 합친 셈)")
    ap.add_argument("--회차", default=".", help="회차 폴더(기본 지금 폴더)")
    ap.add_argument("--장부", default=None, help="레터 장부(기본 회차의 레터_초안.장부.json)")
    ap.add_argument("--회", type=int, default=None, help="준비: 몇째 회인가(기본 — 고리 기록 수 + 1)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--줄", default="", help="되돌림: 게이트가 알린 편집본의 행(쉼표)")
    ap.add_argument("--번호", default="", help="되돌림: 고리 기록의 표시 번호(1부터 · 쉼표)")
    ap.add_argument("--까닭", default="게이트가 막음", help="되돌림: 남은 목록에 적을 까닭")
    ap.add_argument("--가정", default=None, help="검사 · 고리: 가정 파일(기본 — 회차 폴더의 가정_*.json · 예시 · 템플릿 뺌). 게이트 ⑧ · ⑱ · 원고 요건 대조에 쓴다")
    a = ap.parse_args()
    회차 = os.path.abspath(a.회차)
    장부p = a.장부 or os.path.join(회차, "레터_초안.장부.json")
    if a.일 == "준비":
        레터p = os.path.join(회차, a.대상[0]) if a.대상 else os.path.join(회차, "레터_초안.md")
        회 = a.회 or (len(고리들(회차)) + 1)
        글 = _글읽기(레터p)
        d = 준비(글, _읽기(장부p, {}) or {}, 회, 고리들(회차), os.path.relpath(레터p, 회차).replace("\\", "/"))
        _쓰기(os.path.join(회차, 곳, "준비_%d.json" % 회), d)
        with io.open(os.path.join(회차, 곳, "산문_%d.txt" % 회), "w", encoding="utf-8", newline="\n") as f:
            f.write(산문보기(글))
        막 = [z for z in d["구조"] if z["등급"] == "막음" and z["넘음"]]
        print("교열 준비 %d회 — %s · 산문 %s자 · 문장 %s · 구조 자리 %d(막음 %d) · 열쇠 줄 %d → %s" % (
            회, d["레터"], format(d["산문글자"] or 0, ","), d["문장"], len(d["구조"]), len(막), len(d["열쇠"]),
            os.path.join(곳, "준비_%d.json" % 회)))
        print(d["구조한줄"])
        return 0
    if a.일 in ("검사", "고리"):
        if not a.대상:
            print("표시 파일을 준다")
            return 2
        p = a.대상[0] if os.path.isabs(a.대상[0]) else os.path.join(회차, a.대상[0])
        가정p = os.path.abspath(a.가정) if a.가정 else None
        if a.일 == "고리":
            try:
                g = 고리(회차, p, 장부p, 가정경로=가정p)
            except ValueError as e:
                print("교열 고리 — %s" % e)
                return 2
            for i, w in g["거절"]:
                print("  거절 %d — %s" % (i, w))
            return 1 if g["거절"] else 0
        표시 = _읽기(p)                                       # 검사 = 쓰지 않는 고리(1.1.15 — 게이트 ⑧ · ⑱ · 묶음 다시 쓰기의 원고 요건까지 본다)
        try:
            g = 고리(회차, p, 장부p, 쓰기=False, 말=lambda *_a: None, 가정경로=가정p)
        except ValueError as e:
            print("교열 검사 — %s" % e)
            return 2
        셈 = collections.Counter(x.get("몫") or "?" for x in g["표시"] if x.get("처리") != "거절")
        print("교열 검사 — 표시 %d · 거절 %d · 경보 %d · 몫 %s" % (len((표시 or {}).get("표시") or []), len(g["거절"]), len(g["경보"]),
                                                       " · ".join("%s %d" % kv for kv in 셈.items())))
        for i, w in g["거절"]:
            print("  거절 %d — %s" % (i, w))
        for w in g["경보"]:
            print("  경보 %s" % w)
        return 1 if g["거절"] else 0
    if a.일 == "되돌림":
        수들 = lambda t: tuple(int(x) for x in re.findall(r"\d+", t or ""))
        try:
            n = 되돌림(회차, a.회 or len(고리들(회차)), 수들(a.줄), 수들(a.번호), a.까닭, 장부경로=장부p)
        except ValueError as e:
            print("교열 되돌림 — %s" % e)
            return 2
        return 0 if n else 1
    if a.일 == "남은":
        d = 남은(회차, 장부경로=장부p)
        _쓰기(os.path.join(회차, 곳, "남은목록.json"), d)
        확인읽기대장(회차, 장부p)
        with io.open(os.path.join(회차, 곳, "남은목록.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(남은글(d))
        print("교열 남은 목록 — 표시 %d · 구조 막음 자리 %d → %s" % (d["셈"]["표시"], d["셈"]["구조"], os.path.join(곳, "남은목록.md")))
        return 0
    if a.일 == "대장":
        폴더 = [os.path.abspath(x) for x in a.대상] or [회차]
        if len(폴더) == 1:
            d = _읽기(os.path.join(폴더[0], 대장곳 + ".json"))
            if not d:
                print("교열 대장이 없다 — %s" % os.path.join(폴더[0], 대장곳 + ".json"))
                return 1
            print(json.dumps(d["회차"], ensure_ascii=False, indent=1) if a.json else 대장글(d).split("\n## 지적 줄")[0])
            return 0
        d = 대장합(폴더)
        print(json.dumps(d, ensure_ascii=False, indent=1))
        return 0
    rc, 줄 = 확인(회차)
    for x in 줄:
        print(x)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

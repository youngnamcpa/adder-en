# -*- coding: utf-8 -*-
"""용어 — 용어표(`용어표.json`)를 읽는 한 곳 (L2 · 2026-10-09 결정).

레터 · 레터 게이트 · 조사 함수가 이 파일로 용어표를 읽는다.

  표()                    용어 목록(용어표의 「용어」 — 병기 꼴을 더해서)
  받침(말)                말 끝이 용어표의 영어 낱말이면 그 읽는 소리의 받침 — "있음" · "없음" · "ㄹ" · "미정", 아니면 None
  병기꼴(용어)            「가중평균자본비용(WACC)」 · 「Terminal Value(영구가치)」
  병기(글, 보호=())       문서 첫 등장에 우리말을 병기하고, 그 뒤로는 영어만 쓴다 → (새 글, 고친 자리 [(시작, 끝, 옛 조각, 새 조각)])
                          머리줄(#) · 코드 · 보호 구간(엔진 글 따위)은 건드리지 않는다. 고친 자리 뒤의 조사는 새 꼴의 받침으로 다시 고른다
  옛말목록() · 옛말로(글, 보호=())  용어표 「옛말」(걷어 낸 옛 이름 → 지금 말 · 2026-10-27) — 레터 전체(머리줄 · 표 · 부록까지)를 바꾼다.
                          코드 블록 · 「> 원문」 인용 · 그림 표지 · 보호 글은 그대로. 뒤의 조사는 지금 말의 받침으로 다시 고른다
  점검(글)                게이트 ⑬ 의 용어 항목 → [(등급, 줄 번호, 항목, 조각)] — 등급 「오류」 · 「경보」
                          오류: 영어로 쓰기로 한 자리를 우리말로만 썼다 · 병기 꼴이 용어표와 다르다 · 영어 꼴 용어의 금지 풀이 · 한국어 꼴 용어의 금지 영어
                          경보: 첫 등장에 병기가 없다 · 두 번째부터 병기했다

    python 스크립트/용어.py --점검          용어표의 꼴을 본다(필수 칸 · 겹치는 이름)
    python 스크립트/용어.py <글.md>         그 글의 용어 점검 결과
    python 스크립트/용어.py --고치기 <가정.json | 레터부록.json | 레터_가격성립.json> [--낼 <새 파일>]
                                           저자 글의 우리말 풀이를 영어 용어로(「무차입 베타」 → 「Unlevered Beta」 · 「고대역폭 메모리」 → 「HBM」 —
                                           뒤의 조사도 고른다). 가정 파일은 독자층 글 키만(서사 · 서사연결 · 서술 · 시나리오이야기 · 독자근거 · 검토의견 ·
                                           관측 · Narrative · 신호 · 3P), 레터 입력 둘은 모든 글. 고친 곳을 찍는다(근거 칸 · 구조 이름은 건드리지 않는다)
                                           옛말(용어표 「옛말」)도 지금 말로 바꾼다(2026-10-27)
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
표파일 = os.path.join(여기, "용어표.json")
꼴들 = ("병기", "영어", "한국어")
받침들 = ("있음", "없음", "ㄹ", "미정")
_캐시 = {}

# 조사 짝 — (받침 있을 때, 없을 때). 긴 것부터 본다. 뒤에 한글이 바로 와도 되는 꼴(이다 · 이고 …)과 안 되는 꼴(은 · 이 …)을 가른다.
조사짝 = (("으로", "로"), ("이다", "다"), ("이고", "고"), ("이며", "며"), ("이라", "라"), ("이나", "나"),
        ("은", "는"), ("이", "가"), ("을", "를"), ("과", "와"))
_뒤한글허용 = {"으로", "로", "이다", "다", "이고", "고", "이며", "며", "이라", "라", "이나", "나"}


def 표():
    """용어표의 용어 목록. 각 항목에 「병기꼴」을 더한다(꼴이 병기일 때)."""
    if "표" not in _캐시:
        with io.open(표파일, encoding="utf-8") as f:
            d = json.load(f)
        목록 = []
        for x in d.get("용어") or []:
            y = dict(x)
            if y.get("꼴") == "병기":
                y["병기꼴"] = 병기꼴(y)
            목록.append(y)
        _캐시["표"] = 목록
        _캐시["기호괄호"] = list(d.get("기호괄호") or [])
    return _캐시["표"]


def 기호괄호():
    표()
    return _캐시["기호괄호"]


def 병기꼴(x):
    """용어(항목 또는 이름) → 병기 꼴. 약어는 「우리말(영어)」, 그 밖은 「영어(우리말)」."""
    if isinstance(x, str):
        x = next((y for y in 표() if y["용어"] == x), None)
        if x is None:
            raise KeyError("용어표에 없다: %s" % x)
    if x.get("순서") == "우리말먼저":
        return "%s(%s)" % (x["우리말"], x["용어"])
    return "%s(%s)" % (x["용어"], x["우리말"])


def 항목(용어):
    return next((y for y in 표() if y["용어"] == 용어), None)


def _영어끝(말):
    """말 끝에 붙은 용어표의 영어 낱말(가장 긴 것) — 항목 또는 None."""
    for x in sorted((y for y in 표() if y.get("꼴") in ("병기", "영어") and y.get("받침")), key=lambda y: -len(y["용어"])):
        e = x["용어"]
        if 말.endswith(e) and (len(말) == len(e) or not re.match(r"[A-Za-z0-9]", 말[-len(e) - 1])):
            return x
    return None


def 받침(말):
    """말 끝이 용어표의 영어 낱말이면 그 받침(있음 · 없음 · ㄹ · 미정), 아니면 None."""
    x = _영어끝(("%s" % (말 or "")).rstrip())
    return x.get("받침") if x else None


def 영단어받침(말):
    """말 끝의 영문 낱말이 소문자가 섞인 낱말(iPhone · Azure · Lumentum)이면 읽는 소리의 받침(있음 · 없음 · ㄹ), 대문자 약어(AMD · NAND)면 None
    (약어는 글자 이름으로 읽는다 — 부르는 쪽의 L · M · N · R 규칙). 1.1.10 — 「iPhone는」(아이폰 — ㄴ 받침)을 막는다.
    끝 소리: ng · n · m → 있음 · l → ㄹ · 자음 + e(묵음): ne · me → 있음, le → ㄹ, 그 밖(Azure · Nike) → 없음 · 그 밖의 자음 · 모음 → 없음(Microsoft · Docker · Meta)."""
    m = re.search(r"[A-Za-z]+$", ("%s" % (말 or "")).rstrip())
    if not m:
        return None
    w = m.group(0)
    if len(w) < 3 or not any(c.islower() for c in w):
        return None
    w = w.lower()
    if w.endswith(("ng", "n", "m")):
        return "있음"
    if w.endswith("l"):
        return "ㄹ"
    if len(w) >= 4 and w[-1] == "e" and w[-2] not in "aeiouy":
        return {"n": "있음", "m": "있음", "l": "ㄹ"}.get(w[-2], "없음")
    return "없음"


def 조사고르기(받, 있, 없):
    """받침 갈래 → 조사. ㄹ 받침 뒤 「으로」 는 「로」. 미정은 받침 있는 꼴(조사를 붙이지 않게 틀을 짠다 — 게이트 ⑬ 이 잡는다)."""
    if 받 == "없음":
        return 없
    if 받 == "ㄹ" and 있.startswith("으로"):
        return 없
    return 있


# ══════════════════════════════════════════════════════════════════ 병기 — 문서 첫 등장에 우리말, 그 뒤로는 영어만

def _보호구간(글, 보호=()):
    """건드리지 않는 구간 — 머리줄(#) · 코드 블록 · 보호 글(엔진 글 따위)이 나온 자리."""
    구간 = []
    코드 = False
    i = 0
    for 줄 in 글.split("\n"):
        t = 줄.strip()
        끝 = i + len(줄)
        if t.startswith("```"):
            구간.append((i, 끝))
            코드 = not 코드
        elif 코드 or t.startswith("#") or t.startswith(">") or t.startswith("<!--") or re.match(r"^- \[[^\]]+\]\(#[^)]+\)$", t):
            구간.append((i, 끝))                                  # 머리줄 · 인용(견본 띠) · 그림 표지 · 목차 줄(R1b)은 병기 · 점검 밖
        i = 끝 + 1
    for g in 보호 or ():
        if g and len(g) >= 2:
            for m in re.finditer(re.escape(g), 글):
                구간.append((m.start(), m.end()))
    return 구간


def _안(구간, s, e):
    return any(a <= s and e <= b for a, b in 구간)


def _겹침(구간, s, e):
    return any(s < b and a < e for a, b in 구간)


def _영어패턴(e):
    return re.compile(r"(?<![A-Za-z0-9])%s(?![A-Za-z0-9])" % re.escape(e))


def _자리들(글, x, 막은):
    """용어 x 의 등장 — [(시작, 끝, 갈래)] 갈래 = 「병기」(표의 병기 꼴) · 「영어」. 막은 구간(긴 용어가 먼저 차지한 자리)은 뺀다."""
    낸 = []
    # 이미 펼친 꼴 — 표의 병기 꼴과 괄호 앞에 띄어쓰기를 둔 꼴(「가중평균자본비용 (WACC)」 · 엔진 · 도구 이름)을 같은 등장으로 본다.
    # 띈 꼴을 영어 등장으로 세면 괄호 안 영어에 병기가 또 걸려 「가중평균자본비용 (가중평균자본비용(WACC))」 겹괄호가 된다(2026-11-01)
    앞, 뒤 = (x["우리말"], x["용어"]) if x.get("순서") == "우리말먼저" else (x["용어"], x["우리말"])
    for m in re.finditer(r"%s[ \t]*\(%s\)" % (re.escape(앞), re.escape(뒤)), 글):
        if not _겹침(막은, m.start(), m.end()):
            낸.append((m.start(), m.end(), "병기"))
    for m in _영어패턴(x["용어"]).finditer(글):
        if _겹침(막은, m.start(), m.end()) or any(a <= m.start() < b for a, b, _g in 낸):
            continue
        낸.append((m.start(), m.end(), "영어"))
    return sorted(낸)


def _조사다시(글, 끝, 새말):
    """끝 자리 바로 뒤에 붙은 조사를 새말의 받침으로 다시 고른다 → (조사 길이, 새 조사) 또는 None."""
    import 레터                                                    # noqa: PLC0415 — 조사 규칙은 레터.조사 한 곳
    뒤 = 글[끝:끝 + 4]
    for 있, 없 in 조사짝:
        for 붙 in (있, 없):
            if 뒤.startswith(붙):
                다음 = 뒤[len(붙):len(붙) + 1]
                if 다음 and "가" <= 다음 <= "힣" and 붙 not in _뒤한글허용:
                    continue
                return len(붙), 레터.조사(새말, 있, 없)
    return None


def 병기(글, 보호=()):
    """문서 첫 등장에 병기, 그 뒤로는 영어만. → (새 글, 고친 자리 [(시작, 끝, 옛 조각, 새 조각)] — 시작 · 끝은 옛 글의 자리).
    등장 = 영어 꼴(「WACC」) 또는 표의 병기 꼴(「가중평균자본비용(WACC)」). 우리말만 쓴 자리는 고치지 않는다(게이트가 잡는다)."""
    구간 = _보호구간(글, 보호)
    막은 = []
    고침 = []
    for x in sorted((y for y in 표() if y.get("꼴") == "병기"), key=lambda y: -len(y["용어"])):
        자리 = [(s, e, g) for s, e, g in _자리들(글, x, 막은) if not _안(구간, s, e)]
        for k, (s, e, g) in enumerate(자리):
            막은.append((s, e))
            새 = x["병기꼴"] if k == 0 else x["용어"]
            옛 = 글[s:e]
            if 옛 == 새:
                continue
            조 = _조사다시(글, e, 새)
            if 조:
                n, 새조 = 조
                고침.append((s, e + n, 글[s:e + n], 새 + 새조))
            else:
                고침.append((s, e, 옛, 새))
    고침.sort()
    낸, i = [], 0
    for s, e, _옛, 새 in 고침:
        낸.append(글[i:s])
        낸.append(새)
        i = e
    낸.append(글[i:])
    return "".join(낸), 고침


# ══════════════════════════════════════════════════════════════════ 독자 층 — 병기 · 영어 용어를 쉬운 말로(통독 v3)
# (2026-10-15 결정으로 바뀜) 독자 층(`## 3분 레터` 부터 `# 깊이 층` 앞까지)도 실무 표준 용어(영어 · 약어 포함)를 쓰고 문서 첫 등장에
# 병기한다. 조어(용어표 「조어」)는 표준 용어로 바꾸고(`조어로`) 남으면 게이트 오류(`독자점검`). 「독자」 칸이 있는 용어만 쉬운 말로(지금 없음).

def 독자말(x):
    """용어 항목 → 독자 층의 말(바꾸지 않으면 None). 2026-10-15 결정 — 독자 층도 실무 표준 용어를 쓰고 첫 등장에 병기한다:
    「독자」 칸에 말을 적은 것만 바꾼다(지금 용어표는 모두 null — 바꾸는 것 없음)."""
    return x.get("독자") or None


def 조어목록():
    """용어표 「조어」 — [{조어, 표준, 풀이?}] (쉬운 말로 풀려다 만든 조어 → 실무 표준 용어)."""
    if "조어" not in _캐시:
        with io.open(표파일, encoding="utf-8") as f:
            _캐시["조어"] = [x for x in (json.load(f).get("조어") or []) if x.get("조어") and x.get("표준")]
    return _캐시["조어"]


def 조어로(글, 보호=()):
    """독자 층의 조어를 표준 용어로(2026-10-15 결정 — 「한 주 값」 → 「주당가치」 · 「주주의 몫」 → 「주주가치」 …) → (새 글, 고친 자리).
    풀이가 있으면 독자 층 첫 자리에 「표준(풀이)」. 머리줄 · 보호 글은 건드리지 않는다(머리줄은 생성기가 표준 용어로 쓴다 — 게이트가 본다).
    뒤의 조사는 표준 용어의 받침으로 다시 고른다."""
    범 = 독자구간(글)
    if not 범:
        return 글, []
    구간 = _보호구간(글, 보호)
    고침, 막은 = [], []
    for x in sorted(조어목록(), key=lambda y: -len(y["조어"])):
        첫 = True
        for m in re.finditer(re.escape(x["조어"]), 글):
            s, e = m.start(), m.end()
            if not (범[0] <= s and e <= 범[1]) or _안(구간, s, e) or _겹침(막은, s, e):
                continue
            막은.append((s, e))
            새 = x["표준"]
            if 첫 and x.get("풀이") and not 글[e:e + 1] == "(":
                새 = "%s(%s)" % (새, x["풀이"])
            첫 = False
            조 = _조사다시(글, e, 새)
            if 조:
                n, 새조 = 조
                고침.append((s, e + n, 글[s:e + n], 새 + 새조))
            else:
                고침.append((s, e, 글[s:e], 새))
    if not 고침:
        return 글, []
    고침.sort()
    낸, i = [], 0
    for s, e, _옛, 새 in 고침:
        낸.append(글[i:s])
        낸.append(새)
        i = e
    낸.append(글[i:])
    return "".join(낸), 고침


def 옛말목록():
    """용어표 「옛말」 — [{옛말, 지금말, 패턴, 조사, 까닭}] (2026-10-27 — 걷어 낸 레터 말). 패턴이 없으면 옛말 글자 그대로."""
    if "옛말" not in _캐시:
        with io.open(표파일, encoding="utf-8") as f:
            목 = [x for x in (json.load(f).get("옛말") or []) if x.get("옛말") and x.get("지금말")]
        _캐시["옛말"] = [dict(x, 패턴=x.get("패턴") or re.escape(x["옛말"])) for x in 목]
    return _캐시["옛말"]


def _옛말막을곳(글, 보호=()):
    """옛말로 가 건드리지 않는 구간 — 코드 블록 · 원문 인용 줄(「> 원문」) · 그림 표지(<!-- -->) · 보호 글(엔진 글 따위). 머리줄 · 표 · 부록은 바꾼다."""
    구간, 코드, i = [], False, 0
    for 줄 in 글.split("\n"):
        t = 줄.strip()
        끝 = i + len(줄)
        if t.startswith("```"):
            구간.append((i, 끝))
            코드 = not 코드
        elif 코드 or t.startswith("> 원문") or t.startswith("<!--"):
            구간.append((i, 끝))
        i = 끝 + 1
    for g in 보호 or ():
        if g and len(g) >= 2:
            for m in re.finditer(re.escape(g), 글):
                구간.append((m.start(), m.end()))
    return 구간


def 옛말로(글, 보호=()):
    """레터 전체의 옛말을 지금 말로(용어표 「옛말」 — 2026-10-27) → (새 글, 고친 자리 [(시작, 끝, 옛 조각, 새 조각)]).
    긴 옛말이 먼저 자리를 차지한다. 뒤의 조사는 지금 말의 받침으로 다시 고른다(`_조사다시` — 「문턱을」 → 「임계치를」 · 「3P test로는」 → 「3P 기준으로는」)."""
    구간 = _옛말막을곳(글, 보호)
    고침, 막은 = [], []
    for x in sorted(옛말목록(), key=lambda y: -len(y["옛말"])):
        for m in re.finditer(x["패턴"], 글):
            s, e = m.start(), m.end()
            if s == e or _겹침(구간, s, e) or _겹침(막은, s, e):
                continue
            막은.append((s, e))
            새 = x["지금말"]
            조 = _조사다시(글, e, 새) if x.get("조사", True) else None
            if 조:
                n, 새조 = 조
                고침.append((s, e + n, 글[s:e + n], 새 + 새조))
            else:
                고침.append((s, e, 글[s:e], 새))
    if not 고침:
        return 글, []
    고침.sort()
    낸, i = [], 0
    for s, e, _옛, 새 in 고침:
        낸.append(글[i:s])
        낸.append(새)
        i = e
    낸.append(글[i:])
    return "".join(낸), 고침


def 독자구간(글):
    """(시작, 끝) 글자 자리 — `## 3분 레터` 줄부터 `# 본편`(2026-10-16 — 옛 `# 깊이 층`) · `# 부록` 줄 앞까지. 없으면 None."""
    m = re.search(r"(?m)^## 3분 레터\s*$", 글)
    if not m:
        return None
    n = re.search(r"(?m)^# (?:본편\s*$|깊이 층|부록)", 글[m.end():])
    return m.start(), (m.end() + n.start()) if n else len(글)


def 독자로(글, 보호=()):
    """독자 층의 병기 · 영어 용어를 독자 말로 → (새 글, 고친 자리 [(시작, 끝, 옛 조각, 새 조각)] — `병기` 와 같은 꼴).
    머리줄 · 그림 표지 · 목차 · 보호 글은 건드리지 않는다. 뒤의 조사는 새 말의 받침으로 다시 고르고, 읽는 소리 미정(WACC) 뒤에 붙인 「 값」 은 걷는다."""
    범 = 독자구간(글)
    if not 범:
        return 글, []
    구간 = _보호구간(글, 보호)
    고침, 막은 = [], []
    for x in sorted(표(), key=lambda y: -len(y["용어"])):
        새말 = 독자말(x)
        if not 새말 or x.get("꼴") not in ("병기", "영어"):
            continue
        자리 = []
        if x.get("꼴") == "병기":
            자리 += [(m.start(), m.end()) for m in re.finditer(re.escape(x["병기꼴"]), 글)]
        for m in _영어패턴(x["용어"]).finditer(글):
            if not any(a <= m.start() < b for a, b in 자리):
                자리.append((m.start(), m.end()))
        for s, e in sorted(자리):
            if not (범[0] <= s and e <= 범[1]) or _안(구간, s, e) or _겹침(막은, s, e):
                continue
            막은.append((s, e))
            if x.get("받침") == "미정" and 글[e:e + 2] == " 값":
                e += 2
            조 = _조사다시(글, e, 새말)
            if 조:
                n, 새조 = 조
                고침.append((s, e + n, 글[s:e + n], 새말 + 새조))
            else:
                고침.append((s, e, 글[s:e], 새말))
    고침.sort()
    낸, i = [], 0
    for s, e, _옛, 새 in 고침:
        낸.append(글[i:s])
        낸.append(새)
        i = e
    낸.append(글[i:])
    return "".join(낸), 고침


def _판정어들():
    """정합설정 「판정어.말」 — 독자 글(본편 · 부록 포함)에서 우리말로 바꾸는 영문 판정어(1.1.2)."""
    try:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "정합설정.json")
        return list(((json.load(io.open(p, encoding="utf-8")).get("판정어") or {}).get("말")) or [])
    except (OSError, ValueError):
        return []


def 판정어로(글, 보호=()):
    """1.1.2 — 영문 판정어(Possible · Plausible · Probable · shift · change · break)를 레터 전체(3분 레터 · 본편 · 부록)에서 용어표 「독자」 말로
    → (새 글, 고친 자리). 병기 꼴(「shift(세부 조정)」)은 우리말 하나로 접는다. 머리줄 · 코드 블록 · 인용 · 보호 글은 그대로."""
    말 = set(_판정어들())
    if not 말:
        return 글, []
    구간 = _보호구간(글, 보호)
    고침, 막은 = [], []
    for x in sorted(표(), key=lambda y: -len(y["용어"])):
        새말 = 독자말(x)
        if x.get("용어") not in 말 or not 새말:
            continue
        자리 = []
        if x.get("병기꼴"):
            자리 += [(m.start(), m.end()) for m in re.finditer(re.escape(x["병기꼴"]), 글)]
        for m in _영어패턴(x["용어"]).finditer(글):
            if not any(a <= m.start() < b for a, b in 자리):
                자리.append((m.start(), m.end()))
        for s, e in sorted(자리):
            if _안(구간, s, e) or _겹침(막은, s, e):
                continue
            막은.append((s, e))
            조 = _조사다시(글, e, 새말)
            if 조:
                n, 새조 = 조
                고침.append((s, e + n, 글[s:e + n], 새말 + 새조))
            else:
                고침.append((s, e, 글[s:e], 새말))
    고침.sort()
    낸, i = [], 0
    for s, e, _옛, 새 in 고침:
        낸.append(글[i:s])
        낸.append(새)
        i = e
    낸.append(글[i:])
    return "".join(낸), 고침


def 관할로(글, 보호=(), 관할="KR"):
    """1.1.2 — 대상회사 관할에 맞지 않는 제도 용어를 정합설정 「관할.<관할>.치환」 으로 → (새 글, 고친 자리). 보호 구간은 그대로."""
    try:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "정합설정.json")
        표_ = ((((json.load(io.open(p, encoding="utf-8")).get("관할") or {}).get(관할)) or {}).get("치환")) or []
    except (OSError, ValueError):
        표_ = []
    if not 표_:
        return 글, []
    구간, 코드, i = [], False, 0                              # 머리줄은 바꾼다(제도 용어는 제목에서도 틀린다) — 코드 · 인용 · 표지 · 보호 글만 그대로
    for 줄 in 글.split(chr(10)):
        t = 줄.strip()
        if t.startswith("```"):
            코드 = not 코드
            구간.append((i, i + len(줄)))
        elif 코드 or t.startswith((">", "<!--")):
            구간.append((i, i + len(줄)))
        i += len(줄) + 1
    for g in 보호 or ():
        if g and len(g) >= 2:
            구간 += [(m.start(), m.end()) for m in re.finditer(re.escape(g), 글)]
    고침, 막은 = [], []
    for a, b in sorted(표_, key=lambda t: -len(t[0])):
        for m in re.finditer(re.escape(a), 글):
            s, e = m.start(), m.end()
            if _겹침(막은, s, e) or _겹침(구간, s, e):
                continue
            막은.append((s, e))
            고침.append((s, e, a, b))
    고침.sort()
    낸, i = [], 0
    for s, e, _옛, 새 in 고침:
        낸.append(글[i:s])
        낸.append(새)
        i = e
    낸.append(글[i:])
    return "".join(낸), 고침


def 독자점검(글):
    """게이트 ⑬ — 독자 층에 남은 조어(용어표 「조어」 — 머리줄 포함) · 「독자」 칸이 있는 영어 용어 → [(오류, 줄, 항목, 조각)].
    2026-10-15 결정 — 실무 표준 용어(영어 · 약어 포함)는 통과, 조어는 오류."""
    범 = 독자구간(글)
    if not 범:
        return []
    구간 = _보호구간(글)
    낸 = []
    for x in 조어목록():
        for m in re.finditer(re.escape(x["조어"]), 글, ):
            if 범[0] <= m.start() < 범[1]:
                줄시작 = 글.rfind(chr(10), 0, m.start()) + 1
                줄끝 = 글.find(chr(10), m.end())
                낸.append(("오류", _줄번호(글, m.start()), "용어:독자 층의 조어 「%s」 → 표준 용어 「%s」" % (x["조어"], x["표준"]),
                           글[줄시작:줄끝 if 줄끝 >= 0 else len(글)].strip()[:90]))
    for x in 표():
        if not 독자말(x) or x.get("꼴") not in ("병기", "영어"):
            continue
        for m in _영어패턴(x["용어"]).finditer(글, 범[0], 범[1]):
            if not _안(구간, m.start(), m.end()):
                줄시작 = 글.rfind("\n", 0, m.start()) + 1
                줄끝 = 글.find("\n", m.end())
                낸.append(("오류", _줄번호(글, m.start()), "용어:독자 층의 영어 「%s」 → 「%s」" % (x["용어"], 독자말(x)),
                           글[줄시작:줄끝 if 줄끝 >= 0 else len(글)].strip()[:90]))
    return 낸


def 조각옮기기(조각들, 옛글, 고침):
    """옛 글에 든 조각(원고 따위)이 병기로 바뀐 꼴 — 조각마다 옛 글의 자리를 찾아 그 안의 고침을 얹은 새 조각 목록(바뀐 것만)."""
    낸 = []
    for g in 조각들 or ():
        if not g:
            continue
        for m in re.finditer(re.escape(g), 옛글):
            s0, e0 = m.start(), m.end()
            안 = [(s, e, 새) for s, e, _옛, 새 in 고침 if s0 <= s and e <= e0]
            if not 안:
                continue
            조, i = [], s0
            for s, e, 새 in 안:
                조.append(옛글[i:s])
                조.append(새)
                i = e
            조.append(옛글[i:e0])
            새조각 = "".join(조)
            if 새조각 != g and 새조각 not in 낸:
                낸.append(새조각)
    return 낸


# ══════════════════════════════════════════════════════════════════ 점검 — 게이트 ⑬ 의 용어 항목

def _줄번호(글, i):
    return 글.count("\n", 0, i) + 1


def _우리말패턴(x):
    return re.compile(r"(?<![가-힣])" + re.escape(x["우리말"]))


def 점검(글):
    """→ [(등급, 줄, 항목, 조각)]. 머리줄 · 코드는 건너뛴다(머리줄은 영어 꼴 · 우리말 꼴을 보지 않는다 — 절 이름은 「Narrative」 그대로)."""
    구간0 = _보호구간(글)
    범 = 독자구간(글)
    구간 = 구간0 + ([범] if 범 else [])                       # 독자 층은 쉬운 말로 쓴다 — 병기 · 우리말 점검은 깊이 층부터(독자점검이 영어를 본다)
    낸 = 독자점검(글)
    막은 = []
    병전부 = [(m.start(), m.end()) for y in 표() if y.get("꼴") == "병기" for m in re.finditer(re.escape(y["병기꼴"]), 글)]

    def 조각(s, e):
        줄시작 = 글.rfind("\n", 0, s) + 1
        줄끝 = 글.find("\n", e)
        return 글[줄시작:줄끝 if 줄끝 >= 0 else len(글)].strip()[:90]
    for x in sorted(표(), key=lambda y: -len(y["용어"])):
        꼴 = x.get("꼴")
        if 꼴 == "병기":
            자리 = [(s, e, g) for s, e, g in _자리들(글, x, 막은) if not _안(구간, s, e)]
            for s, e, _g in 자리:
                막은.append((s, e))
            if 자리:
                s, e, g = 자리[0]
                if g != "병기":
                    낸.append(("경보", _줄번호(글, s), "용어:첫 등장에 병기가 없다 「%s」 → 「%s」" % (x["용어"], x["병기꼴"]), 조각(s, e)))
                for s, e, g in 자리[1:]:
                    if g == "병기":
                        낸.append(("경보", _줄번호(글, s), "용어:두 번째부터 병기했다 「%s」" % x["병기꼴"], 조각(s, e)))
            # 병기 꼴이 표와 다르다 — 순서가 뒤집혔거나 괄호 앞에 빈칸
            영, 우 = re.escape(x["용어"]), re.escape(x["우리말"])
            for 패 in (r"(?<![A-Za-z0-9])%s\s*\(\s*%s\s*\)" % (영, 우) if x.get("순서") == "우리말먼저" else r"%s\s*\(\s*%s\s*\)" % (우, 영),
                      (r"%s\s+\(\s*%s\s*\)" % (우, 영)) if x.get("순서") == "우리말먼저" else (r"(?<![A-Za-z0-9])%s\s+\(\s*%s\s*\)" % (영, 우))):
                for m in re.finditer(패, 글):
                    if not _안(구간, m.start(), m.end()):
                        낸.append(("오류", _줄번호(글, m.start()), "용어:병기 꼴이 용어표와 다르다 「%s」 → 「%s」" % (m.group(0), x["병기꼴"]),
                                   조각(m.start(), m.end())))
            if x.get("우리말검사", True):
                for m in _우리말패턴(x).finditer(글):
                    s, e = m.start(), m.end()
                    if _안(구간, s, e) or any(a <= s < b for a, b in 병전부):      # 어느 용어든 병기 꼴 안이면 뺀다
                        continue
                    낸.append(("오류", _줄번호(글, s), "용어:영어로 쓰기로 한 자리를 우리말로 썼다 「%s」 → 「%s」" % (x["우리말"], x["용어"]),
                               조각(s, e)))
        elif 꼴 == "영어":
            for 금 in x.get("금지") or []:
                for m in re.finditer(re.escape(금), 글):
                    if not _안(구간0, m.start(), m.end()):
                        낸.append(("오류", _줄번호(글, m.start()), "용어:「%s」 는 영어로만 쓴다(「%s」 금지)" % (x["용어"], 금),
                                   조각(m.start(), m.end())))
        elif 꼴 == "한국어":
            for 금 in x.get("금지") or []:
                for m in _영어패턴(금).finditer(글):
                    if not _안(구간0, m.start(), m.end()):
                        낸.append(("오류", _줄번호(글, m.start()), "용어:「%s」 는 우리말로 쓴다(「%s」 금지)" % (x["용어"], 금),
                                   조각(m.start(), m.end())))
    return sorted(set(낸), key=lambda t: (t[1], t[2]))


def 영어로(글):
    """우리말 풀이(병기 용어의 우리말만 쓴 자리 · 영어 꼴 용어의 금지 풀이)를 영어 용어로 → (새 글, 고친 수). 병기 꼴 안은 건드리지 않는다.
    뒤에 붙은 조사는 영어 용어의 읽는 소리로 다시 고른다(용어.병기 와 같은 규칙)."""
    if not isinstance(글, str) or not 글:
        return 글, 0
    수 = 0
    병전부 = [(m.start(), m.end()) for y in 표() if y.get("꼴") == "병기" for m in re.finditer(re.escape(y["병기꼴"]), 글)]
    바꿀 = []
    for x in sorted(표(), key=lambda y: -len(y.get("우리말") or "")):
        말들 = []
        if x.get("꼴") == "병기" and x.get("우리말검사", True):
            말들.append(x["우리말"])
        if x.get("꼴") == "영어":
            말들 += list(x.get("금지") or [])
        for 말 in 말들:
            for m in re.finditer(r"(?<![가-힣])" + re.escape(말) + r"(?:\s?\(" + re.escape(x["용어"]) + r"\))?", 글):
                s, e = m.start(), m.end()                    # 「고대역폭 메모리(HBM)」 처럼 영어를 괄호에 단 꼴은 괄호까지 걷는다
                if any(a <= s < b for a, b in 병전부) or any(not (e <= a or b <= s) for a, b, _x in 바꿀):
                    continue
                바꿀.append((s, e, x["용어"]))
    if not 바꿀:
        return _조사붙이기(글)
    낸, i = [], 0
    for s, e, 새 in sorted(바꿀):
        낸.append(글[i:s])
        조 = _조사다시(글, e, 새)
        if 조:
            낸.append(새 + 조[1])
            i = e + 조[0]
        else:
            낸.append(새)
            i = e
        수 += 1
    낸.append(글[i:])
    새글, n = _조사붙이기("".join(낸))
    return 새글, 수 + n


def _조사붙이기(글):
    """영어 용어 뒤에 띄어 쓴 조사(「DRAM 과」 · 「ROIC 를」)를 붙이고 읽는 소리로 다시 고른다 → (새 글, 고친 수). 읽는 소리가 정해지지
    않은 말(WACC)은 「값」 을 넣는다(「WACC 를」 → 「WACC 값을」)."""
    import 레터                                                    # noqa: PLC0415
    수 = 0
    짝들 = "|".join(sorted({x for 짝 in 조사짝 for x in 짝}, key=len, reverse=True))
    for x in sorted((y for y in 표() if y.get("꼴") in ("병기", "영어") and y.get("받침")), key=lambda y: -len(y["용어"])):
        패 = re.compile(r"(?<![A-Za-z0-9])(%s) (%s)(?=[\s.,)」·:;!?]|$)" % (re.escape(x["용어"]), 짝들))

        def 바꿈(m):
            짝 = next(((있, 없) for 있, 없 in 조사짝 if m.group(2) in (있, 없)), None)
            if 짝 and m.group(2) == 짝[0] and 짝[0].startswith("이") and len(짝[0]) == 2 and x.get("받침") != "미정":
                return m.group(1) + m.group(2)                 # 서술격 조사의 온꼴(「NAND 이고」 → 「NAND이고」)은 그대로 붙인다
            return m.group(1) + 레터.조사(m.group(1), 짝[0], 짝[1]) if 짝 else m.group(0)
        글, n = 패.subn(바꿈, 글)
        수 += n
    return 글, 수


_고칠키 = ("서사", "서사연결", "서술", "시나리오이야기", "독자근거", "관측", "Narrative", "신호", "3P", "검토의견")
_자리표시 = re.compile(r"\{[^{}]*\}")


def _자리표시밖만(글):
    """영어로() 를 자리표시(「{R:기준:요약:영구가치비중}」 · 「{A:30:기준:FY2027E}」) 밖에만 — 키 안의 「영구가치」 를 고치면 자리표시가 깨진다
    (회차 20261023 NVDA). → (새 글, 고친 수)."""
    낸, 수, i = [], 0, 0
    for m in _자리표시.finditer(글):
        새, n = 영어로(글[i:m.start()])
        낸 += [새, m.group(0)]
        수 += n
        i = m.end()
    새, n = 영어로(글[i:])
    낸.append(새)
    return "".join(낸), 수 + n


def 고치기(d, 전부=False):
    """JSON 의 글을 영어로() — 가정 파일은 독자층 글 키만, 전부=True 면 모든 글. → (새 d, [(자리, 옛, 새)])."""
    고친 = []

    def 걷기(v, 자리):
        if isinstance(v, str):
            새, n = _자리표시밖만(v)
            새, 옛고침 = 옛말로(새)                        # 2026-10-27 — 옛말도 지금 말로(용어표 「옛말」)
            if n or 옛고침:
                고친.append((자리, v, 새))
            return 새
        if isinstance(v, dict):
            return {k: 걷기(x, "%s.%s" % (자리, k) if 자리 else "%s" % k) for k, x in v.items()}
        if isinstance(v, list):
            return [걷기(x, "%s[%d]" % (자리, i)) for i, x in enumerate(v)]
        return v
    if 전부:
        return 걷기(d, ""), 고친
    d = dict(d)
    for k in _고칠키:
        if k in d:
            d[k] = 걷기(d[k], k)
    return d, 고친


def 표점검():
    """용어표의 꼴 — 필수 칸 · 목록 밖 값 · 겹치는 이름. → 걸린 목록."""
    걸린 = []
    본 = set()
    for x in 표():
        e = x.get("용어")
        if not e:
            걸린.append("용어 칸이 빈 항목 — %s" % x)
            continue
        if e in 본:
            걸린.append("겹친 용어 — %s" % e)
        본.add(e)
        if x.get("꼴") not in 꼴들:
            걸린.append("%s — 꼴은 %s 가운데 하나다" % (e, " · ".join(꼴들)))
        if x.get("꼴") == "병기" and (not x.get("우리말") or x.get("순서") not in ("우리말먼저", "영어먼저")):
            걸린.append("%s — 병기 용어에는 우리말 · 순서(우리말먼저 · 영어먼저)가 있어야 한다" % e)
        if x.get("꼴") in ("병기", "영어") and x.get("받침") not in 받침들:
            걸린.append("%s — 받침은 %s 가운데 하나다" % (e, " · ".join(받침들)))
    return 걸린


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    인자 = sys.argv[1:]
    if 인자 and 인자[0] == "--고치기":
        p = 인자[1]
        d = json.load(io.open(p, encoding="utf-8"))
        가정꼴 = isinstance(d, dict) and "스키마버전" in d
        새, 고친 = 고치기(d, 전부=not 가정꼴)
        for 자리, 옛, 새글 in 고친:
            print("  %s · %s → %s" % (자리, 옛[:100], 새글[:100]))
        낼 = 인자[인자.index("--낼") + 1] if "--낼" in 인자 else p
        with io.open(낼, "w", encoding="utf-8", newline=chr(10)) as f:
            json.dump(새, f, ensure_ascii=False, indent=1)
            f.write(chr(10))
        print("용어 고치기 — %d곳 → %s" % (len(고친), 낼))
        raise SystemExit(0)
    if not 인자 or 인자[0] == "--점검":
        걸린 = 표점검()
        for x in 걸린:
            print("  · %s" % x)
        print("용어표 — %d개 · 걸린 것 %d" % (len(표()), len(걸린)))
        raise SystemExit(1 if 걸린 else 0)
    글 = io.open(인자[0], encoding="utf-8").read()
    걸린 = 점검(글)
    for 등급, n, 항목, 조 in 걸린:
        print("%s  %4d행  %s  %s" % (등급, n, 항목, 조))
    print("용어 점검 — 오류 %d · 경보 %d" % (sum(1 for x in 걸린 if x[0] == "오류"), sum(1 for x in 걸린 if x[0] == "경보")))
    raise SystemExit(1 if any(x[0] == "오류" for x in 걸린) else 0)


if __name__ == "__main__":
    main()


# 1.1.9 — 권유어(매수 · 매도)가 회계 · 법령 용어 안에 든 자리. 권유어 · 금지어 검사 전에 걷는다(종전에는 「매도가능 채무증권」 ·
#   「주식매수청구권」 이 권유로 걸려 레터 · 인터랙티브 합본이 막혔다 — 유니버스 B 본진). 걷는 것은 이 용어뿐이다
회계용어속권유 = re.compile(r"매도\s?가능|(?:주식)?매수\s?(?:청구권|선택권)|매수\s?가격\s?조정")


def 권유어밖(글):
    """글에서 회계 · 법령 용어 안의 「매수 · 매도」 를 걷은 글(권유어 · 금지어 검사용 — 레터에 싣는 글이 아니다)."""
    return 회계용어속권유.sub(" ", 글 or "")

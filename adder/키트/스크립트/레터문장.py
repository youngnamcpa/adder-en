# -*- coding: utf-8 -*-
"""레터문장 — 게이트 ⑬ 문장 점검 (L2 · 기획/레터_고도화_제안 3절 (나), 2026-10-08 결정 2).

  점검(글, 원=None, 장부=None, 보호=()) → [(등급, 줄, 항목, 조각)]   등급 「오류」 이면 게이트 미통과, 「경보」 는 적고 지나간다

| 점검 | 기준 | 판정 |
| 번역투 낱말 | 「되어지」 「에 있어서」 는 오류 · 「를 통해」 「에 의해」 「로부터」 「하는 것이 가능」 「라고 할 수 있다」 「을 가지」 「에 대한」 은 경보 | 오류 · 경보 |
| 문장 길이 | 91~120자 경보 · 121자 이상 오류(본문 줄글과 불릿 · 문턱은 `정합설정.json` 「구조검사.길이」 — 구조 지표 ⑨ 와 한 셈 `긴문장들`) | 경보 · 오류 |
| 괄호 | 한 문장 3개 이상 · 괄호 안 21자 이상 경보 · 겹괄호 오류 · 본문의 기호 괄호(「영구성장률 (g)」) 경보 — 용어표의 병기 꼴은 세지 않는다 | 경보 · 오류 |
| 문형 반복 | 한 문단에서 같은 끝맺음 · 같은 첫 낱말 3연속 | 경보 |
| 조사 | 숫자 · 단위 · 용어표 낱말 뒤 조사가 읽는 소리의 받침과 어긋남 · 읽는 소리가 정해지지 않은 말(WACC) 뒤 조사 → 오류, 띄어 쓴 조사 → 경보 | 오류 · 경보 |
| 용어 | 영어로 쓰기로 한 자리를 우리말로 썼다 · 병기 꼴이 용어표와 다르다 → 오류 / 첫 등장에 병기가 없다 · 두 번째부터 병기 → 경보(`용어.점검`) | 오류 · 경보 |
| 명사 나열 | 조사 없는 한글 낱말 5개 이상 연속(형태소 분석 없이 어림) | 경보 |
| 표 칸 | 40자 넘는 칸 | 경보 |
| Narrative 숫자 | 저자 Narrative 글의 숫자가 장부에 없다 · 눈금 낱말이 장부의 기준과 다르다(`레터이야기.숫자대조` — M2) | 오류 |
| 앞부분 다섯 | 「# 본편」 이 있는 레터 — 앞부분 다섯(추정 구조 · 역산 · 매출 방법 · 실적 열 · 비중 표)과 Narrative 의 「→ 이 판단은」 셋 · 절 순서(`앞부분점검`) | 오류 |
결론형 표현(⑨ + 제안 6절 후보)은 게이트 ⑨ 가 본다(`레터.권유검수`).
| 구조 지표 | 문장 원칙 열셋의 지표 열셋(`레터구조.py` — 문서 지칭 · 되풀이 구조 · 주제어 겹침 · 이름 끼움 · 내부 표기 …). 막음 지표가 문턱을 넘으면 오류 · 표시 지표는 값만(`구조지표`) | 오류 |

    python 스크립트/레터문장.py 레터.md        글만으로 볼 수 있는 항목(Narrative 숫자 빼고)
"""
from __future__ import annotations

import difflib
import io
import re
import sys
import os

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)

import 용어  # noqa: E402
import 어투  # noqa: E402
import 레터구조  # noqa: E402

번역투오류 = (r"되어[지진졌질]", r"에 있어서")
조사오류꼴 = ((r"[률율]다(?=[.\s,)」]|$)", "조사:「률다」 → 「률이다」"),)      # 2026-10-22 — ㄹ 받침 명사(변동률 · 성장률) 뒤 「다」(견본 실측: 「변동률다」)
번역투경보 = (r"[를을] 통해", r"[를을] 통하여", r"에 의해", r"에 의하여", r"(?<![가-힣])으?로부터", r"하는 것이 가능", r"라고 할 수 있다",
          r"[을를] 가지(?:고|는|며|게|다)", r"[을를] 가진다", r"에 대한")
길이경보, 길이오류 = 레터구조.설정()["길이"]["경보"], 레터구조.설정()["길이"]["오류"]     # v27 — 120자를 넘으면 오류(종전 131 · 문장 원칙 9)
잡음꼴 = ("이다", "이고", "이며", "이라", "이나")          # 서술격 조사의 온꼴 — 받침 없는 말 뒤에서 「다」 로 줄여도 되고 안 줄여도 된다
_끝낱말 = re.compile(r"(\S+?)[.!?]?$")
조사짝 = 용어.조사짝
_조사패턴 = "|".join(sorted({x for 짝 in 조사짝 for x in 짝}, key=len, reverse=True))
_단위 = r"조 원|억 원|만 원|억 달러|만 달러|%p|%|배|원|달러|년|개월|월|일|곳|명|주|개|건"
_수조사 = re.compile(r"(?<![\w.,])([−\-+]?\d[\d,]*(?:\.\d+)?(?:\s?(?:%s))?)(%s)(?=[\s.,)」·:;!?]|$)" % (_단위, _조사패턴))
_수띄운조사 = re.compile(r"(?<![\w.,])([−\-+]?\d[\d,]*(?:\.\d+)?\s?(?:%s)) (은|는|이|가|을|를|과|와|으로|로)(?=[\s.,)])" % _단위)
_조사끝 = ("은", "는", "이", "가", "을", "를", "의", "에", "로", "과", "와", "도", "만", "서", "고", "며", "면", "다", "게", "지", "니", "나",
         "요", "께", "까", "야", "든", "듯", "며", "라", "랑", "엔", "론", "보다", "처럼", "부터", "까지", "에서", "으로", "에게", "한", "된",
         "인", "던", "는데", "하고", "하며", "했고", "한다", "했다", "이다", "이며", "이고", "였다", "있다", "없다", "된다", "본다", "든다", "낸다",
         "운", "올", "갈", "할", "될", "적", "을", "뒤", "때", "중", "간", "말", "초", "후", "전", "안", "밖", "쪽", "편", "끝")


def _본문(글):
    """(본문 줄 번호 → 줄) — 부록 머리(`# 부록`) 앞까지."""
    i = 글.find("\n# 부록")
    return 글 if i < 0 else 글[:i + 1]


def _블록들(본문):
    """줄글 · 불릿 문단 — [(첫 줄 번호, [(줄 번호, 글)])]. 머리줄 · 표 · 코드 · 인용(견본 띠)은 뺀다. 빈 줄이 문단을 가른다."""
    블록, 지금, 코드 = [], [], False
    for n, 줄 in enumerate(본문.split("\n"), 1):
        t = 줄.strip()
        if t.startswith("```"):
            코드 = not 코드
            continue
        if 코드 or not t or t.startswith("#") or t.startswith("|") or t.startswith(">"):
            if 지금:
                블록.append(지금)
                지금 = []
            continue
        지금.append((n, t[2:].strip() if t.startswith("- ") else t))
    if 지금:
        블록.append(지금)
    return 블록


def 문장나누기(t):
    """한 줄을 문장으로 — 마침표 · 물음표 뒤 빈칸에서 자른다(소수점 · 줄임은 자르지 않는다)."""
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+", t) if x.strip()]


def _병기걷기(s):
    """괄호 세기 전에 용어표의 병기 꼴을 영어만으로 — 병기는 용어 규칙이 정한 괄호다."""
    for x in 용어.표():
        if x.get("꼴") == "병기":
            s = s.replace(x["병기꼴"], x["용어"])
    return s


def _괄호(s):
    """→ (괄호 수, 가장 긴 괄호 안 글자 수, 겹괄호인가)."""
    깊, 수, 겹, 길, 시작 = 0, 0, False, 0, []
    for i, c in enumerate(s):
        if c == "(":
            if 깊 >= 1:
                겹 = True
            깊 += 1
            수 += 1
            시작.append(i)
        elif c == ")" and 깊 > 0:
            깊 -= 1
            a = 시작.pop()
            길 = max(길, i - a - 1)
    return 수, 길, 겹


def _끝맺음(s):
    """끝맺음 — 문장의 마지막 낱말(숫자가 든 낱말은 값의 서술이라 세지 않는다)."""
    m = _끝낱말.search(s.rstrip(" .").replace("**", ""))
    w = m.group(1) if m else None
    return None if (not w or re.search(r"\d", w) or not re.search(r"[가-힣]", w)) else w


def _첫낱말(s):
    m = re.match(r"^\**([^\s*]+)", s)
    return m.group(1) if m else None


def _맨낱말(w):
    """조사 없는 한글 낱말인가(명사 나열 어림) — 한글만이고 흔한 조사 · 어미로 끝나지 않는다."""
    if not re.fullmatch(r"[가-힣]+", w):
        return False
    return not w.endswith(_조사끝)


def _길이(s):
    """문장 길이 — 굵은 표시(**)를 뺀 글자 수."""
    return len(s.replace("**", ""))


def 긴문장들(글, 문턱=None):
    """본문(부록 앞) 줄글 · 불릿에서 문턱(기본 `길이오류`) 이상인 문장 → [(줄, 길이, 문장)]. 게이트 ⑬ 의 문장 길이 오류와 구조 지표 ⑨ 가 같은 셈을 쓴다."""
    문턱 = 길이오류 if 문턱 is None else 문턱
    return [(n, _길이(s), s.replace("**", "")) for 블록 in _블록들(_본문(글)) for n, t in 블록 for s in 문장나누기(t) if _길이(s) >= 문턱]


def 문장점검(글):
    """본문 줄글 · 불릿의 문장 점검 — 번역투 · 길이 · 괄호 · 문형 반복 · 명사 나열 · 조사(숫자 · 띄어 쓴 조사)."""
    import 레터                                                # noqa: PLC0415 — 조사 규칙은 레터.조사 한 곳
    낸 = []
    기호 = [re.escape("(%s)" % x) for x in 용어.기호괄호()]
    for 블록 in _블록들(_본문(글)):
        끝들, 첫들 = [], []
        for n, t in 블록:
            for s in 문장나누기(t):
                맨 = s.replace("**", "")
                for 패, 항 in 조사오류꼴:
                    if re.search(패, 맨):
                        낸.append(("오류", n, 항, 맨[:90]))
                for 패 in 번역투오류:
                    if re.search(패, 맨):
                        낸.append(("오류", n, "번역투:%s" % 패, 맨[:90]))
                for 패 in 번역투경보:
                    if re.search(패, 맨) or re.search(패, 어투.평서로(맨)):     # v27 — 평서체로 적은 꼴을 합쇼체 글에도
                        낸.append(("경보", n, "번역투:%s" % 패, 맨[:90]))
                길이 = _길이(s)
                if 길이 >= 길이오류:
                    낸.append(("오류", n, "문장 길이 %d자" % 길이, 맨[:90]))
                elif 길이 >= 길이경보:
                    낸.append(("경보", n, "문장 길이 %d자" % 길이, 맨[:90]))
                수, 길, 겹 = _괄호(_병기걷기(맨))
                if 겹:
                    낸.append(("오류", n, "괄호:겹괄호", 맨[:90]))
                if 수 >= 3:
                    낸.append(("경보", n, "괄호:한 문장 %d개" % 수, 맨[:90]))
                if 길 >= 21:
                    낸.append(("경보", n, "괄호:괄호 안 %d자" % 길, 맨[:90]))
                for 패 in 기호:
                    if re.search(패, 맨):
                        낸.append(("경보", n, "괄호:본문의 기호 괄호 %s" % 패.replace("\\", ""), 맨[:90]))
                        break
                낱 = [w.strip(",.:;()「」·*") for w in 맨.split()]
                연, 최 = 0, 0
                for w in 낱:
                    연 = 연 + 1 if (w and _맨낱말(w)) else 0
                    최 = max(최, 연)
                if 최 >= 5:
                    낸.append(("경보", n, "명사 나열 %d낱말" % 최, 맨[:90]))
                for m in _수조사.finditer(맨):
                    말, 붙 = m.group(1), m.group(2)
                    짝 = next(((있, 없) for 있, 없 in 조사짝 if 붙 in (있, 없)), None)
                    if 짝 and 짝[0] in 잡음꼴 and 붙 == 짝[0]:
                        continue                             # 「2.03배이고」 — 잡음꼴(이다 · 이고 …)의 온꼴은 받침이 없어도 맞다
                    if 짝 and 붙 != 레터.조사(말, 짝[0], 짝[1]):
                        낸.append(("오류", n, "조사:「%s%s」 → 「%s%s」" % (말, 붙, 말, 레터.조사(말, 짝[0], 짝[1])), 맨[:90]))
                for m in _수띄운조사.finditer(맨):
                    낸.append(("경보", n, "조사:띄어 쓴 조사 「%s」" % m.group(0), 맨[:90]))
                끝들.append((n, _끝맺음(맨), 맨))
                첫들.append((n, _첫낱말(맨), 맨))
        for 줄, 이름 in ((끝들, "같은 끝맺음"), (첫들, "같은 첫 낱말")):
            연 = 1
            for i in range(1, len(줄)):
                if 줄[i][1] and 줄[i][1] == 줄[i - 1][1]:
                    연 += 1
                    if 연 == 3:
                        낸.append(("경보", 줄[i][0], "문형 반복:%s 「%s」 3연속" % (이름, 줄[i][1]), 줄[i][2][:90]))
                else:
                    연 = 1
    return 낸


def 용어조사점검(글, 보호=()):
    """용어표 낱말 뒤 조사 — 받침과 어긋나면 오류 · 읽는 소리 미정(WACC) 뒤 조사는 오류 · 띄어 쓴 조사는 경보. 보호 구간(엔진 글)은 뺀다."""
    낸 = []
    본 = _본문(글)
    가림 = 본
    for g in 보호 or ():
        if g and len(g) >= 2:
            가림 = 가림.replace(g, "\0" * len(g))
    for x in 용어.표():
        if x.get("꼴") not in ("병기", "영어") or not x.get("받침"):
            continue
        e = re.escape(x["용어"])
        for m in re.finditer(r"(?<![A-Za-z0-9])%s(?![A-Za-z0-9(])( ?)(%s)(?=[\s.,)」·:;!?]|$)" % (e, _조사패턴), 가림):
            n = 본.count("\n", 0, m.start()) + 1
            줄 = 본.split("\n")[n - 1].strip()
            if 줄.startswith(("#", "|")):
                continue
            띄, 붙 = m.group(1), m.group(2)
            짝 = next(((있, 없) for 있, 없 in 조사짝 if 붙 in (있, 없)), None)
            if not 짝:
                continue
            if x["받침"] == "미정":
                낸.append(("오류", n, "조사:읽는 소리가 정해지지 않은 「%s」 뒤에 조사 「%s」 — 조사가 바로 붙지 않게 쓴다" % (x["용어"], 붙), 줄[:90]))
                continue
            맞 = 용어.조사고르기(x["받침"], 짝[0], 짝[1])
            if 짝[0] in 잡음꼴 and 붙 == 짝[0]:
                맞 = 붙
            if 붙 != 맞:
                낸.append(("오류", n, "조사:「%s%s」 → 「%s%s」" % (x["용어"], 붙, x["용어"], 맞), 줄[:90]))
            elif 띄:
                낸.append(("경보", n, "조사:띄어 쓴 조사 「%s %s」" % (x["용어"], 붙), 줄[:90]))
    return 낸


def 표칸점검(글):
    낸 = []
    for n, 줄 in enumerate(_본문(글).split("\n"), 1):
        t = 줄.strip()
        if not t.startswith("|") or re.match(r"^\|[-:| ]+\|$", t):
            continue
        for c in t.strip("|").split("|"):
            c = c.strip().replace("**", "")
            if len(c) > 40:
                낸.append(("경보", n, "표 칸 %d자" % len(c), c[:90]))
    return 낸


# ══════════════════════════════════════════════════════════════════ 독자 층의 눈금(R1c 뒤)
# 독자 층(3분 레터 · 1~5막 — `## 3분 레터` 부터 `# 깊이 층` 앞까지)에는 지수 · 배수로 가정을 설명하지 않는다: 가격 변수는 기준 기간 = 100, 값은 돈,
# 과거 비교. 단위 없는 소수(「0.90」 · 「2.74」) · 소수 배수(「1.98배」) · 「메모리 값」(웨이퍼당 매출은 비트 가격이 아니다)은 오류다. 깊이 층 · 부록은 보지 않는다.
# 2026-10-15 — 실무 표준 용어(주당가치 · 영업가치 · PER · WACC · FCFF …)는 독자 층에서도 쓰고 첫 등장에 풀이한다(조어는 용어.독자점검).

_독자단위 = r"(?:배|%p|%|조\s?원|조|억\s?원|억|만\s?원|만|천\s?원|천|원|달러|엔|위안|년|해치|일|개월|분기|주|명|곳|개|건|장|초|쪽|화면|시간|bp)"
_독자소수 = re.compile(r"(?<![\d.,\w])[−\-+]?\d[\d,]*\.\d+(?![\d.])(?!\s?%s)" % _독자단위)
_독자배 = re.compile(r"(?<![\w.])\d[\d,]*\.\d+\s?배(?![분율당수치포정열웅])")     # 2026-10-15 — 소수 배수(가정을 배수로 설명)만, 결과의 정수 배수는 통과


def 독자층범위(글):
    """(시작 줄 번호, 끝 줄 번호) — `## 3분 레터` 부터 `# 본편`(옛 `# 깊이 층`) 앞까지(1부터 센다). 없으면 None."""
    줄 = 글.split("\n")
    시 = next((n for n, x in enumerate(줄, 1) if x.strip() == "## 3분 레터"), None)
    if 시 is None:
        return None
    끝 = next((n for n, x in enumerate(줄, 1) if n > 시 and (x.startswith("# 깊이 층") or x.strip() in ("# 부록", "# 본편"))), len(줄) + 1)
    return 시, 끝


def 독자층점검(글):
    """독자 층의 지수 · 배수 · 「메모리 값」 → [(오류, 줄, 항목, 조각)]. HTML 주석(그림 · 모션 자리)은 뺀다."""
    범 = 독자층범위(글)
    if not 범:
        return []
    낸 = []
    for n, 줄 in enumerate(글.split("\n"), 1):
        if not 범[0] <= n < 범[1]:
            continue
        t = re.sub(r"<!--.*?-->", "", 줄)
        for 패, 항목 in ((_독자소수, "독자 층 지수(단위 없는 소수 — 기준 기간 = 100 · 돈으로)"), (_독자배, "독자 층 배수")):
            for m in 패.finditer(t):
                낸.append(("오류", n, 항목, "%s — %s" % (m.group(0).strip(), t.strip()[:80])))
        if "메모리 값" in t:
            낸.append(("오류", n, "독자 층 「메모리 값」(웨이퍼당 매출 ≠ 비트 가격)", t.strip()[:90]))
    return 낸


# ══════════════════════════════════════════════════════════════════ 제목 규칙(2026-10-15)
# 제목 · 그림 이름 · 모션 이름 · 절 이름 · 표 이름은 「대상 + 무엇을 보여 주는지」 를 평서로 쓴다(회계사가 읽고 바로 아는 말).
# 비유 · 구호형 이름(「가치는 어디서 오나」 · 「더 커지지만 덜 빨라진다」 · 「35일의 퍼즐」 · 「주가 눈금자」 · 「사이클 시계」 · 「계기판」 ·
# 「가격 쪽 읽기」 · 「…의 길」 · 「다리」 · 「국면」 · 「신호등」)은 오류다. 가격 변수는 「…당 매출」 — 「버는 돈」 은 이익으로 읽혀 독자 층에서도 오류다.
_구호말 = ("퍼즐", "눈금자", "사이클 시계", "계기판", "어디서 오나", "덜 빨라", "더 빨라", "국면", "가는 길", "의 길", "신호등", "버는 돈", "다리",
         "쪽 읽기", "셈법")


def 제목점검(글):
    """머리줄(#) · 그림 이름(굵은 「그림 …」 의 굵은 몫)에 비유 · 구호형 말 → [(오류, 줄, 항목, 조각)]. 독자 층 본문의 「버는 돈」 도 오류."""
    낸 = []
    범 = 독자층범위(글)
    for n, 줄 in enumerate(글.split(chr(10)), 1):
        t = 줄.strip()
        이름 = None
        if t.startswith("#"):
            이름 = t.lstrip("#").strip()
        else:
            m = re.match(r"^\*\*((?:그림|표)[^*]*)\*\*", t)
            if m:
                이름 = m.group(1)
        if 이름:
            걸 = [w for w in _구호말 if w in 이름]
            if 걸:
                낸.append(("오류", n, "비유 · 구호형 제목(「대상 + 보여 주는 것」 으로) — %s" % " · ".join(걸), 이름[:90]))
        elif 범 and 범[0] <= n < 범[1] and re.search(r"(?:한 장으로|하나로) 버는 돈", t):
            낸.append(("오류", n, "독자 층 「버는 돈」(매출을 이익으로 읽게 한다 — 「…당 매출」)", t[:90]))
    return 낸


# ══════════════════════════════════════════════════════════════════ 「앞부분에 반드시 들어가는 다섯」(2026-10-16)
# 본편(「# 본편」 아래, 부록 앞)에 ① 추정 구조(출발값 · 추정 순서 · 정합 조건 소절 + 설정한 가정 / 산출된 값을 가른 표, 저자의 추정 순서 글)
# ② Reverse DCF(값을 다 보인 뒤 · 한계 앞) ③ 매출 방법 표(매출 구분 · 추정 방법) ④ 실적 열(원가 구성 표가 출발값 표의 실적 열을 모두 싣는다)
# ⑤ 매출 대비 비중 표(Δ 열) 가 있어야 한다. 더해 Narrative 절의 「→ 이 판단은」 셋과 절 순서(매출 → 비용 → 재투자 → 영구 → 브리지 → 시나리오 → 역산 → 한계).
# 하나라도 빠지면 오류(게이트 미통과). 「# 본편」 이 없는 레터(옛 짜임)에는 걸지 않는다.

def _표머리들(줄들, 처, 끝):
    """[처, 끝) 줄 범위의 표 머리 → [(줄번호, [칸])]. 머리 = 바로 아래 줄이 「|---」 인 표 줄."""
    낸 = []
    for i in range(처, min(끝, len(줄들)) - 1):
        t, u = 줄들[i].strip(), 줄들[i + 1].strip()
        if t.startswith("|") and u.startswith("|") and set(u.replace("|", "").replace(":", "").replace(" ", "")) <= {"-"}:
            낸.append((i + 1, [c.strip() for c in t.strip("|").split("|")]))
    return 낸


def 앞부분점검(글, 원=None):
    """앞부분 다섯 → [(「오류」, 줄, 항목, 조각)]."""
    import 레터 as _L                                        # noqa: PLC0415
    import 레터본문 as _B                                    # noqa: PLC0415
    줄들 = 글.split(chr(10))
    처 = next((i for i, t in enumerate(줄들) if t.strip() == _L.본편머리), None)
    if 처 is None:
        return []
    끝 = next((i for i in range(처 + 1, len(줄들)) if 줄들[i].strip().startswith(_L.부록머리)), len(줄들))
    낸 = []
    절 = {}
    for i in range(처, 끝):
        m = re.match(r"^## (\d+)\. (.+)$", 줄들[i].strip())
        if m:
            for 키, 제목 in _B._제목기본.items():                  # 제목의 앞(「실무 용어」)으로 — 뒤는 구조에 따라 달라진다
                if m.group(2).strip().split(" : ")[0] == 제목.split(" : ")[0]:
                    절[키] = i
    절끝 = {}
    자리 = sorted(절.values())
    for 키, i in 절.items():
        뒤 = [j for j in 자리 if j > i]
        절끝[키] = 뒤[0] if 뒤 else 끝

    def 없음(항목, 줄=0):
        낸.append(("오류", 줄 or (처 + 1), "앞부분 다섯:%s" % 항목, ""))

    def 표제목있나(키, 말):                                  # 레터 v27 6단계 — 추정 블록의 「가정과 결과」 표 · 장 머리 「추정 흐름」 표
        return 키 in 절 and any(줄들[k].startswith("**표") and 말 in 줄들[k] for k in range(절[키], 절끝[키]))
    # ① 추정 구조
    if "구조" not in 절:
        없음("추정 구조 절이 없다(출발값 · 추정 순서 · 정합 조건)")
    else:
        i, j = 절["구조"], 절끝["구조"]
        소 = [줄들[k].strip() for k in range(i, j) if 줄들[k].startswith("### ")]
        for 말 in ("출발값", "추정 순서", "정합 조건"):
            if not any(x[4:].startswith(말) for x in 소):
                없음("추정 구조 절에 「%s」 소절이 없다" % 말, i + 1)
        머 = [h for h in _표머리들(줄들, i, j) if "성격" in h[1]]
        몸 = chr(10).join(줄들[i:j])
        if not 표제목있나("구조", "추정 흐름") and (not 머 or "설정한 가정" not in 몸 or "산출된 값" not in 몸):
            없음("추정 구조 절에 설정한 가정과 산출된 값을 가른 표가 없다", i + 1)
        if 원 is not None:
            N = ((원.get("가정") or {}).get("Narrative") or {}) if isinstance(원, dict) else {}
            선 = N.get("추정구조") if isinstance(N.get("추정구조"), dict) else {}
            if isinstance(N, dict) and N and not ("%s" % (선.get("순서") or "")).strip():      # 저자층(Narrative)이 있는 레터만
                없음("추정 순서를 택한 까닭(Narrative.추정구조.순서)이 없다 — 「매출을 정하고 단가를 산출했다」 류의 주장을 저자가 적는다", i + 1)
    # ② Reverse DCF
    if "역산" not in 절:
        없음("Reverse DCF 절이 없다")
    # ③ 매출 방법 표
    if "매출" not in 절:
        없음("매출 절이 없다")
    elif not 표제목있나("매출", "가정과 결과") and not any("추정 방법" in h[1] for h in _표머리들(줄들, 절["매출"], 절끝["매출"])):
        없음("매출 절에 매출 구분마다의 추정 방법 표가 없다", 절["매출"] + 1)
    # ④ 실적 열 — 원가 구성 표가 출발값 표의 실적 열을 모두 싣는다(추정 블록의 꼴이면 원가 구성 · 비중 표는 부록 — 블록 표가 실적 열을 싣는다)
    블록비용 = 표제목있나("비용", "가정과 결과")
    if 블록비용:
        pass
    elif "구조" in 절 and "비용" in 절:
        실 = None
        for _n, h in _표머리들(줄들, 절["구조"], 절끝["구조"]):
            c = [x for x in h[1:] if "(실적)" in x]
            if c:
                실 = c
                break
        원가 = [h for h in _표머리들(줄들, 절["비용"], 절끝["비용"]) if h[1] and h[1][0].startswith("원가 구성")]
        if not 원가:
            없음("영업비용 절에 원가 구성 표가 없다", 절["비용"] + 1)
        elif 실:
            빠 = [x for x in 실 if x not in 원가[0][1]]
            if 빠:
                없음("원가 구성 표에 실적 열이 빠졌다(%s)" % " · ".join(빠), 원가[0][0])
    elif "비용" not in 절:
        없음("영업비용 절이 없다")
    # ⑤ 매출 대비 비중 표(Δ)
    if "비용" in 절 and not 블록비용 and not any(h[1] and h[1][0].startswith("매출 대비") and any(x.startswith("Δ") for x in h[1])
                               for h in _표머리들(줄들, 절["비용"], 절끝["비용"])):
        없음("영업비용 절에 매출 대비 비중 표(첫 예측 열 · 마지막 열 · Δ)가 없다", 절["비용"] + 1)
    # Narrative 의 「→ 이 판단은」 셋
    if "Narrative" in 절:                                     # 판단 문단(그림 · 표 앞의 문단)마다 「→ 이 판단은」 이 붙는다(Narrative 세 문단)
        # 2026-11-01 — 그림 · 표 · 표지 줄은 건너뛰고 소제목(### 이하)에서 멈춘다. 마지막 「→」 뒤에 남은 문단(절 맺음 · 표 안내)은 판단 문단으로
        # 세지 않는다 — 그림 하나 · 안내 한 줄이 끼었다고 판단 문단 셈이 흔들리지 않게
        차 = []
        for k in range(절["Narrative"] + 1, 절끝["Narrative"]):
            t = 줄들[k].strip()
            if not t or t.startswith(("<!--", "|", "**그림")):
                continue
            if t.startswith("#"):
                break
            차.append("A" if t.startswith("→ 이 판단은") else "P")
        while 차 and 차[-1] == "P":
            차.pop()
        문단, 화살 = 차.count("P"), 차.count("A")
        if 화살 == 0 or 화살 < 문단:
            없음("Narrative 절의 판단 문단 %d개 가운데 「→ 이 판단은 ○절 ○○ 가정으로 간다」 가 붙은 것이 %d개다" % (문단, 화살), 절["Narrative"] + 1)
    # 절 순서 — 모델을 만든 순서
    차례 = [k for k in ("매출", "비용", "재투자", "영구", "주주가치", "시나리오", "역산", "자리") if k in 절]
    if [절[k] for k in 차례] != sorted(절[k] for k in 차례):
        없음("절 순서가 모델을 만든 순서(매출 → 비용 → 재투자 → 영구 → 브리지 → 시나리오 → 역산 → 한계)와 다르다")
    return 낸


# ══════════════════════════════════════════════════════════════════ ⑯ 결론 다섯 줄(2026-10-25 레터 재구성 R2 · 계약 0절 3)
# (옛 꼴) 본편 1절과 3분 레터 맨 앞(「### 결론」)에 같은 결론 줄(`레터이야기.결론줄들` — 값 · 가격 · 갈림 · 근거 · 틀림)이 선다(새 꼴은 아래 `_결론새꼴`). 값 · 갈림은 늘, 가격은 종가가 있으면
# (띠에 종가 줄) 두 자리에 다 있어야 하고, 두 자리의 글은 3분 레터의 독자 층 용어 바꿈(`용어.독자로` · `조어로`)만 다르다 — 숫자가 다르면 오류, 말만 다르면 경보.
# 권유어(목표주가 · 저평가 · 고평가 · 매수 · 매도 · 상승 여력 · 적정가치)가 결론 줄에 있으면 오류. 「# 본편」 이 없는 레터(옛 짜임)에는 걸지 않는다.
결론권유어 = ("목표주가", "저평가", "고평가", "매수", "매도", "상승 여력", "적정가치", "upside")
_결론수 = re.compile(r"[−\-+]?\d[\d,]*(?:\.\d+)?\s?(?:조 원|억 원|만 원|억 달러|만 달러|%p|%|배|원|달러)?")


def _결론독자말(s):
    s, _ = 용어.옛말로(s)                                    # 2026-10-27 — 레터를 쓸 때와 같은 차례(옛말 먼저)
    t, _ = 용어.독자로("## 3분 레터" + chr(10) * 2 + s + chr(10) * 2 + "# 본편")
    t, _ = 용어.조어로(t)
    t = t[t.index(chr(10) * 2) + 2:t.rindex(chr(10) * 2 + "# 본편")]
    return re.sub(r"\s+", " ", t).strip()


def _결론줄찾기(문단들):
    import 레터이야기 as N                                   # noqa: PLC0415
    낸 = {}
    for 자리 in N.결론자리:
        머 = N.결론머리[자리]
        머 = (머,) if isinstance(머, str) else 머
        x = next(((n, s) for n, s in 문단들 if any(m in s for m in 머)), None)
        if x:
            낸[자리] = x
    return 낸


def _종가있나(줄들, 처, 본처, 본끝, 장부):
    """⑯ 의 가격 줄을 볼 판인가 — 장부(결론의 「가격」 자리 · 종가 키) · 본편 1절의 표 줄 · (옛 짜임) 3분 레터 표 줄에 종가가 있으면 참.
    2026-11-01 — 3분 레터가 표 하나(손익 요약)로 줄어 「종가」 표 줄이 사라지자 가격 줄 대조가 소리 없이 건너뛰어졌다."""
    if isinstance(장부, dict):
        if any(isinstance(z, dict) and z.get("자리") == "가격" for z in ((장부.get("결론") or {}).get("줄") or [])):
            return True
        if any(re.search(r"(?:^|:)종가(?::|$)", "%s" % (x.get("키") or "")) for x in 장부.get("숫자") or [] if isinstance(x, dict)):
            return True
    if 본처 is not None and any("종가" in x and x.startswith("|") for x in 줄들[본처:본끝]):
        return True
    return any("종가" in x and x.startswith("|") for x in 줄들[:처])


# 레터 v27 5단계 — 3분 레터의 결론은 핵심 숫자 표(머리 「| 항목 | 값 |」) + 그 회사의 판단과 까닭 문단이다(`레터이야기.삼분결론`). 본편 1절의 결론
# 줄은 그대로 다섯 줄이다. 새 꼴의 대조: ① 표 줄마다 결론 자리(`레터이야기.결론표자리`)를 찾아 칸의 숫자가 본편 1절 그 자리 줄의 숫자 안에 있는가
# (이름 · 다음 점검 칸은 글이 그 줄 안에 있는가) — 다르면 오류 ② 3분 레터 문단의 문장마다 본편 1절 결론 줄 안에 있는가 — 숫자가 다르면 오류,
# 말만 다르면 경보 ③ 본편 1절 줄에서 3분 레터에 문장으로 와야 할 문장(표 · 본편 몫 표지 `레터이야기.결론삼분밖` 밖)이 3분 레터에 있는가 — 없으면 오류
# ④ 값 · 갈림 · (종가가 있으면) 가격의 표 줄이 있는가.
_가름 = re.compile(r"(?<=[.!?])\s+")


def _수목록(s):
    return [m.group(0).strip() for m in _결론수.finditer(s) if re.search(r"\d", m.group(0))]


def _결론표읽기(줄들, 시, 끝):
    """3분 레터 「### 결론」 블록의 핵심 숫자 표(머리 「| 항목 | 값 |」) → [(줄 번호, 줄 이름, 칸)]. 표가 없으면 None(옛 꼴 — 결론 다섯 줄)."""
    for i in range(시, 끝):
        t = 줄들[i].strip()
        if t.startswith("|") and [c.strip() for c in t.strip("|").split("|")] == ["항목", "값"]:
            낸 = []
            for j in range(i + 1, 끝):
                u = 줄들[j].strip()
                if not u.startswith("|"):
                    break
                if re.match(r"^\|[-:| ]+\|$", u):
                    continue
                c = [x.strip() for x in u.strip("|").split("|")]
                if len(c) >= 2:
                    낸.append((j + 1, c[0].replace("**", "").strip(), c[1].replace("**", "").strip()))
            return 낸
    return None


def _결론새꼴(본, 표, 삼문단, 종가, 삼줄):
    """⑯ 새 꼴(레터 v27 5단계) — 3분 레터의 핵심 숫자 표 · 판단 문단을 본편 1절의 결론 줄과 맞댄다. → [(등급, 줄, 항목, 조각)]."""
    import 레터이야기 as N                                   # noqa: PLC0415
    낸 = []
    본말 = {자리: _결론독자말(s) for 자리, (_n, s) in 본.items()}
    본수 = {자리: _수목록(v) for 자리, v in 본말.items()}
    모든수 = [x for v in 본수.values() for x in v]
    선 = set()
    for n, 이름, 칸 in 표:
        z = N.결론표자리(이름)
        if not z:
            continue                                         # 결론 자리가 아닌 줄(편집이 더한 줄)은 대조하지 않는다 — 숫자는 ⑦ 이 장부와 맞댄다
        자리, 꼴 = z
        대 = [x for x in ([자리] + (["값"] if 자리 == "가격" else [])) if x in 본]     # 종가는 [가격] 줄(없으면 [값] 줄의 범위 밖 문장)에
        if not 대:
            낸.append(("오류", n, "결론 다섯 줄:3분 레터 표의 「%s」 줄이 본편 1절에 없는 「%s」 줄이다" % (이름, 자리), 칸[:80]))
            continue
        if 이름 == N.결론표머리["기준"] or 이름 in N.결론표머리["가정"] or 자리 == "가격":
            선.add(자리)                                       # 꼭 있어야 할 줄 — 기준 주당가치 · 좌우하는 가정 · 날짜와 종가
        c = re.sub(r"\s+", " ", 칸).strip()
        풀 = [y for x in 대 for y in 본수[x]]
        if 꼴 == "글":
            c = re.sub(r"\s*뒤$", "", c) if 자리 == "틀림" else c
            if not any(c in 본말[x] for x in 대):
                수c = _수목록(c)
                낸.append(("오류" if any(v not in 풀 for v in 수c) else "경보", n, "결론 다섯 줄:「%s」 줄이 본편 1절과 3분 레터 표에서 %s(「%s」)" % (
                    자리, "숫자가 다르다" if any(v not in 풀 for v in 수c) else "말이 다르다(숫자는 같다)", 이름), c[:80]))
        else:
            수c = _수목록(c)
            if not 수c or any(v not in 풀 for v in 수c):
                낸.append(("오류", n, "결론 다섯 줄:「%s」 줄이 본편 1절과 3분 레터 표에서 숫자가 다르다(「%s」)" % (자리, 이름), c[:80]))
    for 자리 in ("값", "갈림") + (("가격",) if 종가 else ()):
        if 자리 in 본 and 자리 not in 선:
            낸.append(("오류", 삼줄, "결론 다섯 줄:3분 레터 결론 표에 「%s」 줄이 없다" % 자리, ""))
    이름들 = [이름 for _n, 이름, _c in 표]
    if "값" in 본 and N.결론표머리["범위"] not in 이름들:
        낸.append(("오류", 삼줄, "결론 다섯 줄:3분 레터 결론 표에 「%s」 줄이 없다" % N.결론표머리["범위"], ""))
    if "틀림" in 본 and "다음 점검은" in 본말["틀림"] and N.결론표머리["다음"] not in 이름들:
        낸.append(("오류", 삼줄, "결론 다섯 줄:3분 레터 결론 표에 「%s」 줄이 없다(본편 1절 「틀림」 줄에 있다)" % N.결론표머리["다음"], ""))
    삼문 = [(n, x.strip()) for n, p in 삼문단 for x in _가름.split(re.sub(r"\s+", " ", p)) if x.strip()]
    다른말 = []
    for n, s in 삼문:
        if any(s in v for v in 본말.values()):
            continue
        같은수 = all(v in 모든수 for v in _수목록(s))
        if 같은수:
            다른말.append(s)
        낸.append(("경보" if 같은수 else "오류", n, "결론 다섯 줄:3분 레터의 결론 문장이 본편 1절 결론 줄과 %s" % (
            "말이 다르다(숫자는 같다)" if 같은수 else "숫자가 다르다"), s[:80]))
    삼전 = " ".join(s for _n, s in 삼문)
    # 1.1.21 — 3분 레터가 결론 표의 줄로 실은 「틀림」 글 칸(먼저 볼 지표 · 그 지표의 임계치 · 다음 점검)이 그대로 든 1절 문장은 표가 실은 것으로 본다
    #   (교열이 1절의 신호 문장을 둘로 나눠 다시 써도 — 「먼저 확인할 지표는 …입니다. …면 경보입니다」)
    표수 = {}
    for _n, 이름, c in 표:
        z = N.결론표자리(이름)
        if z:
            표수.setdefault(z[0], []).extend(_수목록(re.sub(r"\s+", " ", "%s %s" % (이름, c))))      # 줄 이름의 해(「그때 2031년 매출」)도
    틀칸 = [re.sub(r"\s*뒤$", "", re.sub(r"\s+", " ", c).strip()) for _n, 이름, c in 표 if N.결론표자리(이름) == ("틀림", "글")]
    for 자리, (n, _s) in 본.items():
        for s in _가름.split(본말[자리]):
            s = s.strip()
            if not s or any(m in s for m in N.결론삼분밖) or s in 삼전:
                continue
            if 자리 == "틀림" and any(len(c) >= 6 and c in s for c in 틀칸):
                continue
            수s = _수목록(s)                                  # 1.1.21 — 교열이 다시 쓴 「가격 · 틀림」 문장: 숫자가 모두 그 자리의 표 칸에 있으면 표가 실은 것
            if 자리 in ("가격", "틀림") and 수s and all(v in 표수.get(자리, []) for v in 수s):
                continue
            if any(_수목록(u) == _수목록(s) and difflib.SequenceMatcher(None, s, u).ratio() >= 0.6 for u in 다른말):
                continue                                     # 말만 다른 같은 문장 — 위에서 경보로 냈다
            낸.append(("오류", n, "결론 다섯 줄:본편 1절 「%s」 줄의 문장이 3분 레터 결론에 없다" % 자리, s[:80]))
    return 낸


def 결론점검(글, 장부=None):
    """⑯ → [(등급, 줄, 항목, 조각)]. 장부를 주면 종가 판정(가격 줄을 볼지)을 장부로 한다.
    3분 레터의 결론에 핵심 숫자 표(「| 항목 | 값 |」)가 있으면 새 꼴(레터 v27 5단계 — `_결론새꼴`), 없으면 옛 꼴(두 자리의 결론 다섯 줄이 같은 글)로 잰다."""
    줄들 = 글.split(chr(10))
    처 = next((i for i, x in enumerate(줄들) if x.strip() == "# 본편"), None)
    if 처 is None:
        return []
    낸 = []
    본처 = next((i for i in range(처, len(줄들)) if re.match(r"^## 1\. ", 줄들[i])), None)
    본끝 = next((i for i in range((본처 or 처) + 1, len(줄들)) if 줄들[i].startswith("## ")), len(줄들)) if 본처 is not None else None
    삼처 = next((i for i, x in enumerate(줄들[:처]) if x.strip() == "### 결론"), None)
    # 결론 블록은 다음 머리(#) 또는 고지 표지(5단계 — 회사와 쟁점이 서지 않은 판은 고지 문단이 결론 바로 뒤에 온다)에서 끝난다
    삼끝 = next((i for i in range((삼처 or 0) + 1, 처) if 줄들[i].startswith("#") or 줄들[i].strip().startswith("<!-- 고지")), 처) if 삼처 is not None else None

    def 문단(시, 끝):
        return [(n + 1, 줄들[n].strip()) for n in range(시, 끝) if 줄들[n].strip() and not 줄들[n].strip().startswith(("|", "<!--", "#", "**그림"))]
    if 본처 is None:
        return [("오류", 처 + 1, "결론 다섯 줄:본편 1절이 없다", "")]
    본 = _결론줄찾기(문단(본처, 본끝))
    종가 = _종가있나(줄들, 처, 본처, 본끝, 장부)
    표 = _결론표읽기(줄들, 삼처, 삼끝) if 삼처 is not None else None
    if 표 is not None:                                        # 레터 v27 5단계 — 핵심 숫자 표 + 판단 문단(새 꼴)
        낸 += _결론새꼴(본, 표, 문단(삼처, 삼끝), 종가, 삼처 + 1)
        for 자리 in ("값", "갈림") + (("가격",) if 종가 else ()):
            if 자리 not in 본:
                낸.append(("오류", 본처 + 1, "결론 다섯 줄:본편 1절에 「%s」 줄이 없다" % 자리, ""))
        for 자리, (n, s) in 본.items():
            걸 = [w for w in 결론권유어 if w in 용어.권유어밖(s)]     # 1.1.9 — 회계 용어 안의 매수 · 매도는 뺀다
            if 걸:
                낸.append(("오류", n, "결론 다섯 줄:권유어 「%s」(「%s」 줄)" % (" · ".join(걸), 자리), s[:80]))
        for n, s in [(n, "%s %s" % (이름, 칸)) for n, 이름, 칸 in 표] + 문단(삼처, 삼끝):
            걸 = [w for w in 결론권유어 if w in 용어.권유어밖(s)]
            if 걸:
                낸.append(("오류", n, "결론 다섯 줄:권유어 「%s」(3분 레터 결론)" % " · ".join(걸), s[:80]))
        return 낸
    if 삼처 is None:
        낸.append(("오류", 처 + 1, "결론 다섯 줄:3분 레터 맨 앞에 「### 결론」 블록이 없다(본편 1절과 같은 결론 줄)", ""))
        삼 = {}
    else:
        삼 = _결론줄찾기(문단(삼처, 삼끝))
    for 자리 in ("값", "갈림") + (("가격",) if 종가 else ()):
        for 판, 곳 in ((본, "본편 1절"), (삼, "3분 레터")):
            if 삼처 is None and 곳 == "3분 레터":
                continue
            if 자리 not in 판:
                낸.append(("오류", (본처 if 곳 == "본편 1절" else 삼처) + 1, "결론 다섯 줄:%s에 「%s」 줄이 없다" % (곳, 자리), ""))
    for 자리 in set(본) | set(삼):
        if 삼처 is None:
            break
        if (자리 in 본) != (자리 in 삼):
            n, s = 본.get(자리) or 삼.get(자리)
            낸.append(("오류", n, "결론 다섯 줄:「%s」 줄이 %s에만 있다" % (자리, "본편 1절" if 자리 in 본 else "3분 레터"), s[:80]))
            continue
        a, b = _결론독자말(본[자리][1]), re.sub(r"\s+", " ", 삼[자리][1]).strip()
        if a != b:
            수a = [m.group(0).strip() for m in _결론수.finditer(a) if re.search(r"\d", m.group(0))]
            수b = [m.group(0).strip() for m in _결론수.finditer(b) if re.search(r"\d", m.group(0))]
            낸.append(("오류" if 수a != 수b else "경보", 삼[자리][0], "결론 다섯 줄:「%s」 줄이 본편 1절과 3분 레터에서 %s" % (
                자리, "숫자가 다르다" if 수a != 수b else "말이 다르다(숫자는 같다)"), b[:80]))
    for 판 in (본, 삼):
        for 자리, (n, s) in 판.items():
            걸 = [w for w in 결론권유어 if w in 용어.권유어밖(s)]     # 1.1.9 — 회계 용어 안의 매수 · 매도는 뺀다
            if 걸:
                낸.append(("오류", n, "결론 다섯 줄:권유어 「%s」(「%s」 줄)" % (" · ".join(걸), 자리), s[:80]))
    return 낸


def _길이몫(낸, 글, 장부):
    """⑬ 문장 길이 오류 가운데 원고 몫(장부의 원고 조각 안 · 섞임표시 지표의 섞임)이고 「원고오류」(기본 131자) 밑인 것은 경보로 —
    원고 문장은 교열 검토 단계가 고친다(`레터구조` 의 몫 규칙과 같다 · 설정 「원고막음」 이 참이면 그대로 오류). 원고 조각이 없으면 그대로."""
    원고 = (장부 or {}).get("원고") if isinstance(장부, dict) else None
    if not 원고:
        return 낸
    설 = 레터구조.설정()
    한 = int((설.get("길이") or {}).get("원고오류") or 길이오류)
    if 한 <= 길이오류:
        return 낸
    판정 = 레터구조.원고판(원고)
    규 = {"원고막음": bool(설.get("원고막음")), "섞임표시": list(설.get("섞임표시") or ())}
    전 = {(n, L): s for n, L, s in 긴문장들(글)}
    새 = []
    for x in 낸:
        m = re.match(r"^문장 길이 (\d+)자$", x[2]) if x[0] == "오류" else None
        if m and int(m.group(1)) < 한:
            s = 전.get((x[1], int(m.group(1))))
            몫 = 판정.몫(s) if s else None
            if 몫 and not 레터구조.막는몫(규, "⑨", 몫):
                x = ("경보", x[1], "문장 길이 %s자 — 원고 몫(%s · 교열 검토가 고친다 · %d자부터 오류)" % (m.group(1), 몫, 한), x[3])
        새.append(x)
    return 새


def 구조점검(글, 장부=None, 구조값=None):
    """구조 지표(`레터구조`) — 막음 지표가 문턱을 넘은 자리(코드 몫 오류 · 원고 몫 경보). → (걸린 [(등급, 줄, 항목, 조각)], 지표 값 또는 None)."""
    try:
        값 = 구조값 if 구조값 is not None else 레터구조.지표(글, (), (장부 or {}).get("원고") if isinstance(장부, dict) else ())
    except Exception as e:                                   # noqa: BLE001
        return [("오류", 0, "구조 검사를 돌리지 못했다(%s: %s)" % (type(e).__name__, str(e)[:120]), "")], None
    return 레터구조.막음걸림(값), 값


def 점검(글, 원=None, 장부=None, 보호=(), 구조값=None):
    """게이트 ⑬ — 글의 점검 전부 + (원 · 장부를 주면) Narrative 숫자(M2) · 같은 대상의 숫자 둘(R1b · L18) + 구조 지표의 막음(`레터구조`).
    구조값 — 게이트가 미리 잰 지표(말뭉치를 준 판). 비우면 여기서 잰다(장부의 원고 조각으로 몫을 가른다). → [(등급, 줄 또는 자리, 항목, 조각)]."""
    보호 = list(보호 or ())
    낸 = (_길이몫(문장점검(글), 글, 장부) + 용어조사점검(글, 보호) + 표칸점검(글) + 독자층점검(글) + 제목점검(글) + 앞부분점검(글, 원)
         + 결론점검(글, 장부) + 구조점검(글, 장부, 구조값)[0])
    for 등급, n, 항목, 조 in 용어.점검(_가리기(글, 보호)):
        낸.append((등급, n, 항목, 조))
    if 원 is not None and 장부 is not None:
        import 레터이야기                                       # noqa: PLC0415
        본 = set()
        for 등급, 자리, 항목, 조 in 레터이야기.숫자대조(원, 장부.get("숫자") or [], 장부.get("가격성립입력")):
            k = (자리, 항목)
            if k not in 본:
                본.add(k)
                낸.append((등급, 자리, 항목, 조))
    if 장부 is not None:
        구 = ((원 or {}).get("가정") or {}).get("구조") if 원 is not None else None
        낸 += 대상숫자점검(글, 장부.get("원고") or [], 구, 장부.get("가격성립입력"))
    return 낸


# ══════════════════════════════════════════════════════════════════ R1b(L18) — 같은 대상의 숫자가 둘이면 오류
# 저자 글(장부의 원고 조각 — 레터에 실린 것)에서 「대상(구조 · 가격 성립 입력의 이름) + 금액 명사(투자 · 장비 · 건물 · 매출) + 금액」 을 모아,
# 같은 대상 · 같은 명사에 다른 금액이 둘 이상이면 오류다(앞 판의 「용인 1기 투자 124조 원」 과 「115조 원」, 「장비 15.5조 원 × 6」 과 「84조 원」).
# 「× N」 이 붙으면 곱한 값으로 견준다. 「합한 · 모두 · 합계」 는 투자 합계로 본다. 대상이 「A · B」 로 이어지면 묶음 하나로 본다.

_금액명사 = {"투자액": "투자", "투자": "투자", "설비투자": "투자", "CAPEX": "투자", "합한": "투자", "모두": "투자", "합계": "투자",
           "장비": "장비", "건물": "건물", "연매출": "매출", "매출": "매출"}
_금액토큰 = re.compile(r"(?<![\d.,])(\d[\d,]*(?:\.\d+)?)\s?(조|억)(?:\s?원)?(?:\s?×\s?(\d+(?:\.\d+)?))?")
_이음 = re.compile(r"^\s*(?:·|,|와|과|및)\s*$")
# 기간 말 — 같은 대상 · 같은 명사라도 기간이 다르면 다른 숫자다(분기 매출 890억 과 연 매출 1,152억 · 2025년 과 2026년). 금액 앞 가장 가까운 것
_기간말 = re.compile(r"(?:19|20)\d\d\s?(?:년\s?)?회계연도(?:\s?(?:[1-4]분기|상반기|하반기))?|회계연도\s?(?:19|20)\d\d|"     # 1.1.10 — 「2027 회계연도」(미국 · 비 12월 결산)
                    r"(?:FY|CY)\s?(?:19|20)?\d\d(?:\s?(?:Q[1-4]|H[12]))?|(?:19|20)\d\d년(?:\s?(?:[1-4]분기|상반기|하반기|\d+개월))?|[1-4]분기|상반기|하반기|반기|분기|\d+개월|연간|한 해")
# 1.1.19 — 시나리오 이름(엔진의 시나리오 셋). 같은 대상 · 기간이라도 비관 · 낙관 값은 기준 값과 다른 숫자다. 「기준」 은 「기준 시나리오」 일 때만(「… 기준으로」 는 낱말이다)
_시나리오말 = re.compile(r"(?<![가-힣])(?:비관|낙관)|(?<![가-힣])기준\s?시나리오")
_받는말 = re.compile(r"^\s*(?:이|그)\s?(?:경우|때|시나리오)")             # 앞 문장을 받는 첫머리 — 그 문장의 시나리오를 잇는다
# 금액 명사 뒤에 붙을 수 있는 토씨 — 이것 말고 한글이 이어지면 다른 낱말이다(「매출원가」 · 「투자자」 는 매출 · 투자가 아니다)
_명사뒤 = re.compile(r"^(?:은|는|이|가|을|를|의|도|과|와|에|에서|로|으로|만|까지|부터|보다|액|이며|이고|이다|이었고|였고|입니다|이었습니다)?(?![가-힣])")
_주어토 = re.compile(r"[가-힣A-Za-z]+(?:은|는|이|가)$")


def _대상이름들(구, 가성):
    이름 = set()
    for x in (구 or {}).get("매출구분") or []:
        이름.add(("%s" % (x.get("이름") or "")).strip())
        for j in x.get("라인") or []:
            이름.add(("%s" % (j.get("이름") or "")).strip())
    for q in ((구 or {}).get("투자") or {}).get("프로젝트") or []:
        이름.add(("%s" % (q.get("이름") or "")).strip())
    for 칸 in ("증설", "조합"):
        for x in (가성 or {}).get(칸) or []:
            이름.add(("%s" % (x.get("이름") or "")).strip() if isinstance(x, dict) else "")
    return sorted({x for x in 이름 if len(x) >= 2 and not x.startswith("기타")}, key=len, reverse=True)


def _창명사(창):
    """창(대상 · 앞 금액 뒤부터 이 금액 앞까지)에서 마지막 금액 명사 → (명사 종류, 그 낱말 끝 자리). 낱말째 맞는 것만(1.1.19 —
    「Services 비중이 오르며 … 제품 매출원가는」 의 「매출」 을 Services 매출로 읽었다)."""
    best = (None, -1, -1)
    for n in sorted(_금액명사, key=len, reverse=True):
        for m in re.finditer(re.escape(n), 창):
            뒤 = _명사뒤.match(창[m.end():])
            if not 뒤:
                continue
            if m.start() > best[1]:
                best = (_금액명사[n], m.start(), m.end() + len(뒤.group(0)))
    return best[0], best[2]


def _주어바뀜(뒤):
    """금액 명사 뒤 · 금액 앞 글에 다른 주어 · 화제(「회사가」 · 「금액은」 · 「비중이」)가 서는가 — 서면 그 금액은 다른 것의 금액이다."""
    for w in re.split(r"[\s,·()「」]+", 뒤):
        w = w.strip(".:;")
        if len(w) >= 2 and _주어토.search(w) and not _기간말.fullmatch(w) and not re.match(r"^[\d.,%]", w):
            return True
    return False


def 대상숫자점검(글, 원고, 구=None, 가성=None):
    """→ [(「오류」, 0, 「같은 대상의 숫자 둘: …」, 조각)] — 레터에 실린 저자 글 조각만 본다."""
    이름들 = _대상이름들(구, 가성)
    if not 이름들:
        return []
    패 = re.compile("|".join(re.escape(x) for x in 이름들))
    모은 = {}                                                # (대상, 명사, 기간, 시나리오) → {값: 조각}
    for 조각 in dict.fromkeys(g for g in 원고 if g and g in 글):
        앞시 = "기준"
        for 문 in re.split(r"(?<=[.!?])\s+|\n", 조각):
            대상들 = list(패.finditer(문))
            문시 = 앞시 if _받는말.match(문) else "기준"            # 「이 경우 …」 — 앞 문장의 시나리오를 잇는다
            끝시 = list(_시나리오말.finditer(문))
            앞시 = (("기준" if 끝시[-1].group(0).startswith("기준") else 끝시[-1].group(0)) if 끝시 else 문시)
            앞끝 = 0
            for m in _금액토큰.finditer(문):
                앞 = [d for d in 대상들 if d.end() <= m.start()]
                전끝, 앞끝 = 앞끝, m.end()
                if not 앞 or re.search(r"당\s?$", 문[:m.start()]):          # 「1천 장/월당 0.24조 원」 — 단가는 다른 대상
                    continue
                묶 = [앞[-1]]
                for d in reversed(앞[:-1]):                  # 「용인 2기 · 청주 M17」 — 이어진 이름은 묶음 하나
                    if _이음.match(문[d.end():묶[0].start()]):
                        묶.insert(0, d)
                    else:
                        break
                창 = 문[max(묶[-1].end(), 전끝):m.start()]        # 앞 금액(또는 대상) 뒤부터 이 금액 앞까지
                명, 명끝 = _창명사(창) if 창 else (None, -1)
                if 명 is None or _주어바뀜(창[명끝:]):              # 1.1.19 — 명사 뒤에 다른 주어(「회사가 밝힌」 · 「… 금액은」)가 서면 이 대상의 그 금액이 아니다
                    continue
                v = float(m.group(1).replace(",", "")) * (1e4 if m.group(2) == "조" else 1.0)
                if m.group(3):
                    v *= float(m.group(3))
                기 = [x.group(0) for x in _기간말.finditer(문[:m.start()])]
                시 = list(_시나리오말.finditer(문[:m.start()]))       # 1.1.19 — 금액 앞 가장 가까운 시나리오 이름(비관 · 낙관 값은 기준 값과 다른 대상)
                이시 = ("기준" if 시[-1].group(0).startswith("기준") else 시[-1].group(0)) if 시 else 문시
                열쇠 = (" · ".join(d.group(0) for d in 묶), 명, re.sub(r"\s+", "", 기[-1]) if 기 else "", 이시)
                모은.setdefault(열쇠, {})
                if not any(abs(v - w) <= 0.005 * max(abs(v), abs(w)) for w in 모은[열쇠]):
                    모은[열쇠][v] = m.group(0)
    낸 = []
    for (대상, 명, 기, 시), 값들 in 모은.items():
        if len(값들) > 1:
            덧 = " · ".join(x for x in (기, "" if 시 == "기준" else 시 + " 시나리오") if x)
            낸.append(("오류", 0, "같은 대상의 숫자 둘:%s %s%s — %s" % (대상, 명, (" (%s)" % 덧) if 덧 else "", " · ".join(값들[v] for v in sorted(값들))), 대상))
    return 낸


def _가리기(글, 보호):
    """보호 글(엔진 글 · 도구 이름)을 같은 길이의 빈칸으로 — 용어 점검이 보지 않는다(줄 번호는 그대로)."""
    for g in sorted(set(x for x in 보호 if x and len(x) >= 2), key=len, reverse=True):
        글 = 글.replace(g, re.sub(r"[^\n]", " ", g))
    return 글


def 요약(걸린):
    오 = sum(1 for x in 걸린 if x[0] == "오류")
    return 오, len(걸린) - 오


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)
    글 = io.open(sys.argv[1], encoding="utf-8").read()
    걸린 = 점검(글)
    for 등급, n, 항목, 조 in 걸린:
        print("%s  %s  %s  %s" % (등급, n, 항목, 조))
    오, 경 = 요약(걸린)
    print("⑬ 문장 점검 — 오류 %d · 경보 %d" % (오, 경))
    raise SystemExit(1 if 오 else 0)


if __name__ == "__main__":
    main()

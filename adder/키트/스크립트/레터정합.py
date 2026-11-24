# -*- coding: utf-8 -*-
"""레터정합 — 게이트 ⑱ · ⑳ 의 덧 검사(1.1.2). 숫자가 엔진과 같아도(⑦) 독자가 읽는 글이 틀리는 자리를 막는다.

    python 스크립트/레터정합.py 레터_편집.md [--장부 레터_초안.장부.json] [--가정 가정.json]     # 걸린 것을 찍는다(종료 1 = 막음 있음)

설정은 `정합설정.json` 한 곳이다(생성기 · 게이트가 같은 값을 읽는다). 회사 · 업종 이름은 어디에도 없다.

⑱ 이름 · 정의 일관에 더하는 것
  빈 부록 참조[막음]       본문 · 3분 레터가 「부록 X에 있다 · 밝혔다 · 적었다」 로 가리키는 부록이 비었다(빈말이 있고 데이터 줄이 둘 미만)
  표 구성 합 ≠ 합계[막음]  합계 줄(합계 · 계 · 순운전자본 · 순차입금 …)과 나머지 같은 단위 줄의 어떤 부호 조합 합도 열마다 맞지 않는다 — 숨은 「기타」 줄
  서술 같은 이름 다른 값   설정의 이름 뒤에 붙은 본문 숫자가 두 값 — 둘 다 장부의 다른 실제 키면 막음, 장부 밖 값이 끼면 경보
  격자 채택값[막음]        두 축 격자(머리 「가로 \\ 세로」)의 칸에 기준 주당가치가 없다 — 채택값이 어느 축에도 없다
  열 정의[막음]            실적 열과 추정 열이 함께 선 표에 설정의 이름 줄(CAPEX · 이자부부채 …)이 있는데 표 머리 · 표 바로 뒤에 두 열의 정의가 없다
  3분 범위 밖 역산값[막음]  3분 레터 · 본편 1절이 역산 표에서 실적 · 정상화 · 시나리오 범위 밖(안 0곳)인 단일 역산값을 그 가정 이름과 함께 싣는다
  사실 조건[막음]          「가이던스 범위에 맞췄다」 류 문장 — `관측.외부범위` 에 그 항목이 없거나 엔진 값이 범위 밖
⑳ 독자 글에 더하는 것
  관할 용어[막음]          대상회사 관할에 없는 제도 용어(미국 회사의 지방소득세 · 사업보고서 따위)
  영문 판정어[막음]        Possible · Plausible · Probable · shift · change · break 가 독자 글(부록 포함)에 그대로
  괄호 숫자 코드[막음]     낱말 바로 뒤 괄호 속 세 자리 숫자(가정 · 행 번호)
  같은 그림 제목[막음] · 본편 그림 상한[경보 — 「상한막음」 을 주면 막음]
  판단대장 회피[막음]      판단대장에 검사를 피하려고 판단을 바꾼 기록
"""
from __future__ import annotations

import importlib
import io
import json
import os
import re
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
설정파일 = os.path.join(여기, "정합설정.json")


def 설정():
    try:
        return json.load(io.open(설정파일, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _G():
    import 레터게이트 as G                                   # noqa: PLC0415 — 게이트의 줄 · 표 · 값 읽기를 그대로 쓴다
    return G


def _걸(등급, 항목, 자리, 내용):
    return {"등급": 등급, "항목": 항목, "자리": 자리, "내용": 내용}


# ══════════════════════════════════════════════════════════════════ 부록 · 상호참조
_가리킴식 = re.compile(r"부록 ([A-Z])(?:[에의은는과와](?:\s|$)|[에]서|\s*표|\s*에)")


def 부록들(줄들):
    """{글자: {"행", "제목", "줄": [(행, 글)]}} — 「## 부록 X. 제목」 부터 다음 「## 」 앞까지."""
    낸, 지금 = {}, None
    for n, t, 몫 in 줄들:
        m = re.match(r"^## 부록 ([A-Z])\.\s*(.*)$", t)
        if m:
            지금 = m.group(1)
            낸[지금] = {"행": n, "제목": m.group(2).strip(), "줄": []}
            continue
        if t.startswith("## ") or t.startswith("# "):
            지금 = None
            continue
        if 지금:
            낸[지금]["줄"].append((n, t))
    return 낸


def 빈부록(줄들, 설=None):
    """빈 부록 글자 집합 — 빈말이 있고 데이터 줄(표의 가름 줄 · 머리 뺀 줄)이 둘 미만, 또는 본문이 한 줄도 없다."""
    설 = (설 or 설정()).get("빈부록") or {}
    빈말 = 설.get("빈말") or []
    낸 = set()
    for 글자, b in 부록들(줄들).items():
        줄 = [t for _n, t in b["줄"] if t.strip() and not t.startswith("<!--")]
        표줄 = [t for t in 줄 if t.startswith("|")]
        자료줄 = max(0, len([t for t in 표줄 if not re.match(r"^\|\s*:?-{2,}", t)]) - (1 if 표줄 else 0))
        글 = " ".join(t for t in 줄 if not t.startswith("|"))
        목록 = [t for t in 줄 if t.lstrip().startswith(("- ", "* "))]
        if not 줄 or (any(w in 글 for w in 빈말) and 자료줄 < 2 and len(목록) < 2):
            낸.add(글자)
    return 낸


def 빈부록참조(편, 설=None):
    G = _G()
    설 = 설 or 설정()
    줄들 = G._쪼갬(편)
    빈 = 빈부록(줄들, 설)
    허용 = (설.get("빈부록") or {}).get("가리키되_허용말") or []
    걸 = []
    for n, t, 몫 in 줄들:
        if 몫 not in ("삼분", "본편") or t.startswith(("#", "<!--")):
            continue
        for m in re.finditer(r"부록 ([A-Z])(?![A-Za-z0-9])", t):
            if m.group(1) not in 빈:
                continue
            월 = t[max(0, t.rfind(".", 0, m.start()) + 1):]
            끝 = 월.find(".", m.end() - (len(t) - len(월)))
            월 = 월[:끝 + 1] if 끝 >= 0 else 월
            if any(w in 월 for w in 허용):
                continue
            걸.append(_걸("막음", "빈 부록 참조", "%d행" % n, "「%s」 — 부록 %s 이(가) 비었다(본문이 가리키는 내용이 없다)" % (월.strip()[:70], m.group(1))))
    return 걸


# ══════════════════════════════════════════════════════════════════ 표 구성 합 ≠ 합계
def _칸값(G, c):
    c = (c or "").strip().strip("*").strip()
    if not c or c in ("—", "-", "–"):
        return None
    c = c.replace("−", "-").replace("(", "-").replace(")", "") if re.fullmatch(r"\(\s*[\d,.]+[^)]*\)", c) else c.replace("−", "-")
    m = G.값토큰.fullmatch(c) or re.fullmatch(r"-?\d[\d,]*(?:\.\d+)?", c)
    if not m:
        return None
    음 = c.startswith("-")
    v = G._수값(c.lstrip("-+"))
    if not v:
        return None
    단, 값, 오 = v
    return 단, (-값 if 음 else 값), 오


def _합계줄인가(이름, 설):
    s = re.sub(r"\*\*|\s*\([^)]*\)\s*$", "", 이름 or "").strip()
    for x in 설.get("합계이름") or []:
        if s == x or (x in ("합계",) and s.endswith(x)):
            return True
    return False


def _뺄말든가(말, 이름):
    """구성에서 뺄 줄인가 — 한 글자 한글 말(「배」)은 낱말로 설 때만(「배송비」 · 「배당」 은 아니다 · 1.1.10). 나머지는 글 안에 있으면."""
    if len(말) == 1 and "가" <= 말 <= "힣":
        return re.search(r"(?<![가-힣])%s(?![가-힣])" % re.escape(말), 이름 or "") is not None
    return 말 in (이름 or "")


def 표합계(편, 설=None):
    import itertools                                         # noqa: PLC0415
    G = _G()
    설 = (설 or 설정()).get("합계") or {}
    뺄 = 설.get("구성뺄말") or []
    최대 = int(설.get("구성최대") or 9)
    걸 = []
    for t in G._표들(G._쪼갬(편)):
        if t["몫"] not in ("삼분", "본편", "부록") or len(t["줄"]) < 3:
            continue
        줄 = [(n, 칸) for n, 칸 in t["줄"] if 칸 and 칸[0].strip()]
        구분열 = next((j for j, h in enumerate(t["머리"]) if (h or "").strip() == "구분"), None)     # 레터 v27 6단계 — 「가정과 결과」 표의 가정 · 밑 줄은 구성이 아니다
        if 구분열:
            줄 = [(n, 칸) for n, 칸 in 줄 if not (구분열 < len(칸) and (칸[구분열] or "").strip() in ("가정", "밑", "규칙"))]
        합 = [(n, 칸) for n, 칸 in 줄 if _합계줄인가(칸[0], 설)
             and not (구분열 and 구분열 < len(칸) and (칸[구분열] or "").strip() != "합계")]       # 구분 칸이 있는 표는 「합계」 로 표시한 줄만 합계다
        if len(합) != 1:
            continue
        hn, h칸 = 합[0]
        앞쪽 = [(n, 칸) for n, 칸 in 줄 if n < hn]               # 합계 줄 앞의 줄이 구성이다(합계 뒤 줄은 참고 줄 — 감가상각비 · 비율). 합계가 첫 줄이면 뒤 줄
        구성 = [(n, 칸) for n, 칸 in (앞쪽 or [(n, 칸) for n, 칸 in 줄 if n > hn])
              if not any(_뺄말든가(w, 칸[0]) for w in 뺄) and not 칸[0].startswith("　")]
        이름들 = [re.sub(r"\*\*", "", 칸[0]).strip() for _n, 칸 in 구성]     # 하위 줄(「A — 매출 연동분」)은 윗줄 A 의 내역이다 — 구성에서 뺀다
        구성 = [(n, 칸) for n, 칸 in 구성 if not any(re.sub(r"\*\*", "", 칸[0]).strip().startswith(p + " — ") for p in 이름들)]
        이름합 = re.sub(r"\*\*|\s*\([^)]*\)\s*$", "", h칸[0]).strip()
        if len(구성) < (1 if 이름합.endswith("계") else 2) or len(구성) > 최대:
            continue
        열들 = []
        for j in range(1, len(t["머리"])):
            hv = _칸값(G, h칸[j] if j < len(h칸) else "")
            if hv is None:
                continue
            cv = [_칸값(G, 칸[j] if j < len(칸) else "") for _n, 칸 in 구성]
            if any(x is None for x in cv) or any(x[0] != hv[0] for x in cv):
                continue
            열들.append((j, hv, cv))
        if not 열들:
            continue
        맞음 = False
        for 부호 in itertools.product((1, -1), repeat=len(구성)):
            if all(abs(sum(s * c[1] for s, c in zip(부호, cv)) - hv[1]) <= sum(c[2] for c in cv) + hv[2] + 1e-9 * max(1.0, abs(hv[1]))
                   for _j, hv, cv in 열들):
                맞음 = True
                break
        if not 맞음:
            j, hv, cv = 열들[0]
            걸.append(_걸("막음", "표 구성 합 ≠ 합계", "%d행" % hn,
                         "「%s」 줄(%s)이 구성 줄 %d개(%s)의 어떤 부호 조합 합과도 맞지 않는다 — 숨은 구성(기타) 줄을 싣는다"
                         % (h칸[0].strip("* "), (h칸[j] or "").strip(), len(구성), " · ".join(칸[0].strip("* ") for _n, 칸 in 구성)[:80])))
    return 걸


# ══════════════════════════════════════════════════════════════════ 서술 값 · 격자 · 열 정의 · 3분 역산
def 서술값(편, 장부, 설=None):
    G = _G()
    이름들 = ((설 or 설정()).get("서술이름") or {}).get("이름") or []
    줄들 = G._쪼갬(편)
    표행 = {n for n, t, _몫 in 줄들 if t.startswith("|")}
    글표 = G._장부글표(장부)
    값식 = G.값토큰.pattern.replace("(?<![\\w.,])", "")
    걸 = []
    본 = {}
    for 이름 in sorted(이름들, key=len, reverse=True):
        식 = re.compile(r"(?<![가-힣A-Za-z])" + re.escape(이름) + r"(?:\([^)]{1,30}\))?(?:은|는|이|가|을|를|도|만|의)?\s*(?:약\s*)?(" + 값식 + ")")
        for n, 월, _앞, 몫, 절 in G._글월(줄들, ("삼분", "본편")):
            if n in 표행:
                continue                                   # 1.1.19 — 표 칸은 서술이 아니다(본편 토네이도 표 「옮긴 범위」 의 줄마다 다른 「근거 범위」 를 같은 이름 다른 값으로 막던 결함 · 표 이름은 `이름일관` 이 따로 본다)
            for m in 식.finditer(월):
                if any(m.start() >= a and m.start() < b for a, b in 본.get((n, 월), [])):
                    continue
                뒤 = 월[m.end():]
                if re.match(r"\s*(?:\([^)]*\)\s*)?(?:만큼|더|높|낮|내려|올라|오르|달라|늘|줄|움직|차이|빠|커|작|변|포인트|p)", 뒤) or m.group(1)[:1] in "+−-":
                    continue
                if G.문턱값(뒤):
                    continue                               # 1.1.19 「시가총액이 8조 원을 넘어」 — 견준 문턱이지 그 이름의 값이 아니다(⑱ `레터게이트.문턱값` 과 같은 판정)
                if re.search(r"[가-힣](?:면|라면|어도|아도|더라도)\s|경우|대안|가정하면|바꾸|옮기", 월[:m.start()]) or \
                        re.match(r"\s*(?:로|으로)\s*(?:두|놓|바꾸|올리|낮추|옮기|잡)", 뒤):
                    continue
                if re.search(r"(?:19|20)\d\d", 월[max(0, m.start() - 14):m.start()]):
                    continue                               # 연도가 앞에 붙은 값(「2025년 이자부부채」)은 그 해의 값이다 — 같은 대상이 아니다
                본.setdefault((n, 월), []).append((m.start(), m.end()))
                맥 = G._맥(월)
                if 맥 == ("기준",):
                    맥 = G._맥(절)
                본.setdefault(이름, []).append((n, m.group(1), 맥))
    for 이름 in 이름들:
        목록 = 본.get(이름) or []
        for 맥 in {x[2] for x in 목록}:
            if 맥 == ("여럿",):
                continue
            같 = [x for x in 목록 if x[2] == 맥]
            for b in 같[1:]:
                a = 같[0]
                if not G._다른값(a[1], b[1]):
                    continue
                ka, kb = 글표.get(a[1]) or [], 글표.get(b[1]) or []
                fa, fb = G._값갈래(ka), G._값갈래(kb)
                if "가상" in (fa, fb) or set(ka) & set(kb):
                    continue
                sa, sb = G._키시나리오(ka), G._키시나리오(kb)
                if sa and sb and not (sa & sb):
                    continue
                등 = "막음" if fa == fb == "실제" else "경보"
                걸.append(_걸(등, "서술 같은 이름 다른 값", "%d행 · %d행" % (a[0], b[0]),
                             "「%s」 이(가) %s 와 %s%s" % (이름, a[1], b[1], (" · 장부 키 %s · %s" % (ka[0][:40], kb[0][:40])) if 등 == "막음"
                                                    else " · 장부에 없는 값이 있다")))
                break
    return 걸


def _기준주당(장부):
    for x in (장부 or {}).get("숫자") or []:
        if (x.get("키") or "") == "R:기준:2.DCF:68" and isinstance(x.get("값"), (int, float)):
            return float(x["값"])
    return None


def 격자채택(편, 장부):
    G = _G()
    기 = _기준주당(장부)
    if 기 is None:
        return []
    걸 = []
    for t in G._표들(G._쪼갬(편)):
        머 = (t["머리"] or [""])[0]
        if "\\" not in 머 or len(t["줄"]) < 3 or len(t["머리"]) < 4:
            continue
        if any(w in (t["앞"] or "") for w in ("비관 시나리오", "낙관 시나리오")):
            continue
        값들 = []
        for _n, 칸 in t["줄"]:
            for c in 칸[1:]:
                v = _칸값(G, re.sub(r"\s*\([^)]*\)\s*$", "", (c or "").replace("**", "").strip()))   # 「1,300,707원 (기준의 자리)」
                if v is not None:
                    값들.append(v)
        if len(값들) < 6:
            continue
        if not any(abs(abs(v[1]) - abs(기)) <= v[2] + 1e-9 * abs(기) for v in 값들):
            걸.append(_걸("막음", "격자에 채택값 칸 없음", "%d행" % t["행"],
                         "「%s」 격자의 칸에 기준 주당가치가 없다 — 두 축 가운데 하나에 채택값이 없다(눈금에 채택값을 넣는다)" % 머[:50]))
    return 걸


def 열정의(편, 설=None):
    G = _G()
    설 = (설 or 설정()).get("열정의") or {}
    이름 = 설.get("이름") or []
    정의말 = 설.get("정의말") or []
    줄들 = G._쪼갬(편)
    다음줄 = {}
    for i, (n, t, _몫) in enumerate(줄들):
        다음줄[n] = t
    걸 = []
    for t in G._표들(줄들):
        if t["몫"] not in ("본편", "부록"):
            continue
        머 = " ".join(t["머리"])
        if "실적" not in 머 or not ("추정" in 머 or "예측" in 머):
            continue
        걸린 = [칸[0] for _n, 칸 in t["줄"] if 칸 and any(x in 칸[0] for x in 이름)]
        if not 걸린:
            continue
        끝 = t["줄"][-1][0] if t["줄"] else t["행"]
        뒤 = ""
        for k in range(끝 + 1, 끝 + 4):
            s = (다음줄.get(k) or "").strip()
            if s:
                뒤 = s
                break
        글 = (t["앞"] or "") + " " + 뒤 + " " + 머
        if "실적" in 글.replace(머, "") and any(w in 글 for w in 정의말):
            continue
        걸.append(_걸("막음", "열 정의 — 실적 열과 추정 열", "%d행" % t["행"],
                     "「%s」 줄이 실적 · 추정 열에 함께 섰는데 표 머리 · 표 바로 뒤에 두 열의 정의(무엇을 포함 · 제외했나)가 없다" % 걸린[0].strip("* ")[:40]))
    return 걸


def 역산범위밖(줄들):
    """본편 역산 표(머리에 「이 가격에 필요한 값」 · 「실적」 · 「세 시나리오」)에서 범위 칸에 「안」 이 하나도 없고 「밖」 이 있는 줄 → {가정 이름: 필요 값 글}."""
    G = _G()
    낸 = {}
    for t in G._표들(줄들):
        머 = t["머리"]
        if not 머 or "이 가격에 필요한 값" not in 머 or not any("시나리오" in h for h in 머):
            continue
        j필 = 머.index("이 가격에 필요한 값")
        범 = [j for j, h in enumerate(머) if h in ("실적", "세 시나리오", "대안 사양", "대안 산정 방법") or "범위" in h]   # v27 — 표 머리 「대안 산정 방법」
        for _n, 칸 in t["줄"]:
            칸들 = [칸[j] if j < len(칸) else "" for j in 범]
            if any(c.strip().endswith(" 안") or c.strip() == "안" for c in 칸들):
                continue
            if any(c.strip().endswith(" 밖") for c in 칸들) and j필 < len(칸) and 칸[j필].strip() not in ("", "—"):
                낸[칸[0].strip()] = 칸[j필].strip()
    return 낸


def 삼분역산(편):
    G = _G()
    줄들 = G._쪼갬(편)
    밖 = 역산범위밖(줄들)
    if not 밖:
        return []
    걸 = []
    본처 = None
    for n, t, 몫 in 줄들:
        if 몫 == "본편" and re.match(r"^## 1\. ", t):
            본처 = n
        elif 본처 and 몫 == "본편" and t.startswith("## "):
            본처 = -1
        자리 = 몫 == "삼분" or (몫 == "본편" and 본처 and 본처 > 0)
        if not 자리 or t.startswith(("|", "#", "<!--")):
            continue
        for 이름, 값 in 밖.items():
            핵 = re.sub(r"\s*\([^)]*\)", "", 이름)
            if 값 in t and (핵 in t or 핵.replace("영구기간 ", "") in t or "이익률" in 핵 and "이익률" in t):
                걸.append(_걸("막음", "3분 범위 밖 역산값", "%d행" % n,
                             "「%s」 을(를) %s 로 전제한다는 단일 역산값이 실적 · 정상화 · 시나리오 범위 밖이다 — 첫 장에는 「가정 하나로는 설명되지 않는다」 와 "
                             "범위 안의 두 변수 조합 · 브리지 역산을 싣는다" % (이름, 값)))
                break
    return 걸


def _외부범위(가정):
    v = (((가정 or {}).get("관측") or {}).get("외부범위")) if isinstance(가정, dict) else None
    return [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []


def 사실조건(편, 가정, 설=None, 엔진값=None):
    """「가이던스 범위에 맞췄다」 류 — 관측.외부범위 [{항목, 기간, 하한, 상한, 단위, 출처, 엔진(선택 — 비교 값)}] 에 그 문장의 항목이 있고
    엔진 값(엔진값(항목) 또는 줄의 「엔진」)이 범위 안이어야 한다."""
    G = _G()
    설 = 설 or 설정()
    식 = re.compile(((설.get("사실조건") or {}).get("주장식")) or r"(가이던스)[^.]{0,24}(에|안에)\s*(맞췄|맞춘)")
    범들 = _외부범위(가정)
    걸 = []
    for n, 월, _앞, 몫, _절 in G._글월(G._쪼갬(편), ("삼분", "본편")):
        m = 식.search(월)
        if not m:
            continue
        맞 = [x for x in 범들 if ("%s" % (x.get("항목") or "")).strip() and any(w in 월 for w in [("%s" % x["항목"]).strip()] + list(x.get("말") or []))]
        if not 맞:
            걸.append(_걸("막음", "사실 조건 — 외부 범위 없음", "%d행" % n,
                         "「%s」 — 관측.외부범위 에 이 문장의 항목 · 범위가 없다(범위를 적거나 문장을 사실대로 고친다)" % 월[:70]))
            continue
        for x in 맞:
            v = 엔진값(x) if 엔진값 else x.get("엔진")
            lo, hi = x.get("하한"), x.get("상한")
            if not isinstance(v, (int, float)):
                걸.append(_걸("막음", "사실 조건 — 엔진 값 없음", "%d행" % n, "「%s」 — %s 의 엔진 값을 셈하지 못했다" % (월[:60], x.get("항목"))))
            elif (isinstance(lo, (int, float)) and v < lo - 1e-9 * max(1.0, abs(lo))) or (isinstance(hi, (int, float)) and v > hi + 1e-9 * max(1.0, abs(hi))):
                걸.append(_걸("막음", "사실 조건 — 범위 밖", "%d행" % n,
                             "「%s」 — %s 엔진 값 %s 이(가) 외부 범위 %s~%s 밖이다" % (월[:60], x.get("항목"), format(v, ",.4g"), lo, hi)))
    return 걸


def 외부범위엔진값(가정, x, _캐={}):
    """관측.외부범위 한 줄의 엔진 값 — 「엔진」(수)이 있으면 그것, 「줄」(<시트>:<줄> — 예 8.CapEx:31) · 「회계연도」 가 있으면 기준 시나리오에서
    그 회계연도에 든 실적 · 예측 열의 합(누계 실적 + 잔여 예측 — 반기 열이 있어도 한 해 합). 못 내면 None."""
    if isinstance(x.get("엔진"), (int, float)):
        return float(x["엔진"])
    줄, 해 = ("%s" % (x.get("줄") or "")).strip(), x.get("회계연도")
    if ":" not in 줄 or not isinstance(해, int):
        return None
    try:
        import importlib                                     # noqa: PLC0415
        계 = importlib.import_module("엔진.계산")
        k = id(가정)
        if k not in _캐:
            _캐.clear()
            _캐[k] = 계.계산(가정, "기준")
        R = _캐[k]
        시트, 번 = 줄.rsplit(":", 1)
        P = R["기간"]
        열 = [c for c in P["열"] if (P["속성"].get(c) or {}).get("회계연도") == 해 and (P["속성"].get(c) or {}).get("구분") in ("실적", "예측")]
        값 = [R[시트][번].get(c) for c in 열]
        return float(sum(v for v in 값 if isinstance(v, (int, float)))) if 열 and any(isinstance(v, (int, float)) for v in 값) else None
    except Exception:                                        # noqa: BLE001
        return None


_값명사 = ("주당가치", "영업가치", "주주가치", "기업가치", "금액", "배수", "비율", "이익률", "증가율", "WACC", "주식수", "주식 수", "시가총액")
_적었다식 = re.compile(r"([가-힣A-Za-z][가-힣A-Za-z0-9 ·]{1,24}?)(?:을|를)\s*(?:함께|따로|아래에|표에|나란히)\s*(?:적었|실었|밝혔)(?:다|습니다)")


def 적었다대상(편):
    """「X를 함께 적었다 · 실었다」 문장 — X 가 레터의 다른 자리(표 줄 · 머리 · 그 뒤 숫자가 붙은 글)에 없으면 막음(Q8 — 대상 표 실재)."""
    G = _G()
    줄들 = G._쪼갬(편)
    전부 = [(n, t) for n, t, 몫 in 줄들 if 몫 in ("삼분", "본편", "부록")]
    걸 = []
    값식 = G.값토큰.pattern.replace("(?<![\w.,])", "")
    for n, t in 전부:
        if t.startswith(("|", "#", "<!--")):
            continue
        for m in _적었다식.finditer(t):
            x = re.sub(r"^(?:이를 넣은|그것을 넣은|이를|그|이)\s*", "", m.group(1).strip()).strip()
            핵 = x.split()[-1] if x.split() else x
            if len(x) < 3 or not any(핵.endswith(w) for w in _값명사):   # 셀 수 있는 값(주당가치 · 금액 · 비율 …)을 적었다는 말만 본다 — 「길 · 까닭」 같은 서술은 보지 않는다
                continue
            있 = any(k != n and (x in s) and (s.startswith("#") or re.search(re.escape(x) + r"[^.|]{0,20}?" + 값식, s)) for k, s in 전부)
            if not 있:
                걸.append(_걸("막음", "사실 조건 — 적었다는 대상이 없다", "%d행" % n,
                             "「%s」 — 「%s」 이(가) 레터의 다른 자리(표 · 머리 · 숫자와 함께)에 없다" % (m.group(0)[:60], x)))
    return 걸


# ══════════════════════════════════════════════════════════════════ ⑳ 독자 글
def 관할(가정):
    m = ((가정.get("메타") if isinstance(가정, dict) else None) or {})
    k = ("%s" % (m.get("관할") or "")).strip().upper()
    if k:
        return k
    통 = ("%s" % (m.get("표시통화") or "KRW")).strip().upper()
    return {"KRW": "KR", "USD": "US"}.get(통, "기타")


def 관할치환(글, 관, 설=None):
    """생성 쪽 — 관할 사전의 「치환」 을 차례로(긴 것 먼저). → 새 글."""
    표 = (((설 or 설정()).get("관할") or {}).get(관) or {}).get("치환") or []
    for a, b in sorted(표, key=lambda x: -len(x[0])):
        글 = 글.replace(a, b)
    return 글


def 관할용어(편, 가정, 설=None):
    G = _G()
    관 = 관할(가정)
    금 = ((((설 or 설정()).get("관할") or {}).get(관) or {}).get("금지")) or []
    걸 = []
    for n, t, 몫 in G._쪼갬(편):
        if 몫 not in ("삼분", "본편", "부록") or t.startswith("<!--"):
            continue
        for w in 금:
            if w in t:
                걸.append(_걸("막음", "관할 용어", "%d행" % n, "「%s」 — 대상회사 관할(%s)의 제도 용어가 아니다" % (w, 관)))
                break
    return 걸


def 판정어(편, 설=None):
    G = _G()
    말 = (((설 or 설정()).get("판정어") or {}).get("말")) or []
    if not 말:
        return []
    식 = re.compile(r"(?<![A-Za-z\-])(" + "|".join(re.escape(w) for w in 말) + r")(?![A-Za-z\-])")
    걸 = []
    코드 = False
    for n, t, 몫 in G._쪼갬(편):
        if t.strip().startswith("```"):
            코드 = not 코드
            continue
        if 코드 or 몫 not in ("삼분", "본편", "부록") or t.startswith(("<!--", "> 원문")):
            continue
        s = re.sub(r"https?://\S+|「[^」]*」|\"[^\"]*\"|“[^”]*”", " ", t)
        m = 식.search(s)
        if m:
            걸.append(_걸("막음", "영문 판정어", "%d행" % n, "「%s」 — 독자 글에는 우리말 판정어를 쓴다(용어표 「독자」)" % m.group(1)))
    return 걸


def 괄호코드(편, 설=None):
    G = _G()
    식 = re.compile((((설 or 설정()).get("괄호코드") or {}).get("식")) or r"(?<=[가-힣A-Za-z)])\((\d{3})\)")
    걸 = []
    for n, t, 몫 in G._쪼갬(편):
        if 몫 not in ("삼분", "본편") or t.startswith("<!--"):
            continue
        m = 식.search(t)
        if m:
            걸.append(_걸("막음", "도구 내부 표기 — 괄호 숫자 코드", "%d행" % n, "「%s」" % t[max(0, m.start() - 12):m.end()]))
    return 걸


_자리표식 = re.compile(r"\{(?:[RSANTHGW]|가|민|대안|대안β|역둘|반|위|파일|목|독|주|상|메|절|눈금|백|CAGR|합|÷|×|−|괴리|음)[:\s][^{}\n]{0,160}\}")


def 자리표시(편):
    """Q23 — 펴지지 않은 장부 자리표시(「{가:홀로:비관:30·주당}」 · 「{A:30:기준:FY2027E|증1}」)가 독자 글에 남았나 → 막음. 코드 블록은 뺀다."""
    G = _G()
    걸, 코드 = [], False
    for n, t, 몫 in G._쪼갬(편):
        if t.strip().startswith("```"):
            코드 = not 코드
            continue
        if 코드 or 몫 not in ("삼분", "본편", "부록") or t.startswith("<!--"):
            continue
        m = _자리표식.search(t)
        if m:
            걸.append(_걸("막음", "펴지지 않은 자리표시", "%d행" % n, "「%s」 — 원고의 장부 키를 펴지 못했다(키 이름 · 꼴을 고친다)" % m.group(0)[:60]))
    return 걸


def 그림(편, 설=None):
    G = _G()
    설 = (설 or 설정()).get("그림") or {}
    상 = int(설.get("본편상한") or 0)
    막 = int(설.get("상한막음") or 0)
    제목 = {}
    본수 = 0
    for n, t, 몫 in G._쪼갬(편):
        m = re.match(r"^\*\*그림 (\d+)\.\s*(.+?)\*\*", t)
        if not m:
            continue
        if 몫 == "본편":
            본수 += 1
        제목.setdefault(re.sub(r"\s+", " ", m.group(2)).strip(), []).append((n, m.group(1)))
    걸 = []
    for 이름, 자리 in 제목.items():
        if len(자리) > 1:
            걸.append(_걸("막음", "같은 그림 제목", " · ".join("%d행" % x[0] for x in 자리),
                         "「%s」 — 그림 %s 의 제목이 같다(같은 데이터는 그림 하나 · 다르면 무엇이 다른지 제목에)" % (이름[:50], " · ".join(x[1] for x in 자리))))
    if 상 and 본수 > 상:
        걸.append(_걸("막음" if (막 and 본수 > 막) else "경보", "본편 그림 상한", "-", "본편 그림 %d개 — 상한 %d개(같은 데이터의 그림 · 표는 하나만)" % (본수, 상)))
    return 걸


def 판단대장(경로, 설=None):
    """판단대장 파일(또는 그 파일이 든 폴더의 `_기록/판단대장.md`)에서 검사 회피 기록 → 막음."""
    말 = (((설 or 설정()).get("판단대장") or {}).get("회피말")) or []
    if not 경로:
        return []
    후보 = [경로] if os.path.isfile(경로) else [os.path.join(경로, "_기록", "판단대장.md"), os.path.join(경로, "판단대장.md")]
    걸 = []
    for p in 후보:
        if not os.path.isfile(p):
            continue
        for n, t in enumerate(io.open(p, encoding="utf-8", errors="replace").read().split("\n"), 1):
            w = next((x for x in 말 if x in t), None)
            if w and not re.search(r"금지|하지 않는다|않았다|되돌", t[t.find(w):t.find(w) + 40]):
                걸.append(_걸("막음", "판단대장 — 검사 회피 판단", "%s %d행" % (os.path.basename(p), n),
                             "「%s」 — 문구 검사는 문구만 고친다. 판단은 원래 근거로 되돌리고 그 근거를 적는다" % t.strip()[:80]))
        break
    return 걸


# ══════════════════════════════════════════════════════════════════ 모음
_대기 = ("빈 부록 참조", "사실 조건 — 적었다는", "표 구성 합", "서술 같은 이름", "격자에 채택값", "열 정의", "3분 범위 밖", "사실 조건", "관할 용어", "영문 판정어",
       "도구 내부 표기 — 괄호", "같은 그림 제목", "판단대장", "펴지지 않은 자리표시")       # 1.1.2 에 선 막음 — `--일관경보` 로 옛 판 레터를 읽을 때 경보로 내린다


_부호어 = re.compile(r"(?<![가-힣])(음의|마이너스인?|적자인|양의|플러스인?)\s")
_배수어 = re.compile(r"(두|세|네|다섯|열) ?배(?:를|가)?\s*(넘게|이상|넘는|를 넘|가 넘|넘어)|(절반|반)\s*(?:에|도|이)?\s*(못 미|아래|이하|밑)")
_배수값 = {"두": 2.0, "세": 3.0, "네": 4.0, "다섯": 5.0, "열": 10.0}


def 비교어(편, 장부, 설=None):
    """1.1.4(B) — 부호어(「음의 운전자본」 · 「마이너스」 · 「적자인」 · 「양의」)와 배수어(「두 배 넘게」 · 「절반에 못 미친다」)를 그 문장의 장부 숫자로
    판정한다[막음]. 숫자 글이 장부의 한 값으로 풀릴 때만 본다(장부 밖 숫자 · 저자 글의 맥락 낱말은 건드리지 않는다).
      부호어 — 그 낱말 바로 뒤(18자 안)의 숫자가 장부 값의 부호와 반대면 막는다(「음의 운전자본(1,234억 원)」 인데 장부 값 +)
      배수어 — 그 문장에 장부 숫자가 꼭 둘이면 큰 값 ÷ 작은 값이 그 배수 이상(「n 배 넘게」)인지 · 0.5 이하(「절반에 못 미친다」)인지 본다"""
    G = _G()
    걸 = []
    try:
        값표 = {}
        for x in (장부 or {}).get("숫자") or []:
            if isinstance(x, dict) and x.get("꼴") != "글" and x.get("글") and isinstance(x.get("값"), (int, float)) and not isinstance(x.get("값"), bool):
                값표.setdefault(("%s" % x["글"]).strip(), set()).add(float(x["값"]))
        def 값(글):
            s = 값표.get(글)
            return next(iter(s)) if s and len(s) == 1 else None
        for n, 월, _앞, _몫, _절 in G._글월(G._쪼갬(편), ("삼분", "본편")):
            for m in _부호어.finditer(월):
                뒤 = 월[m.end():m.end() + 30]
                t = G.값토큰.search(뒤)
                if not t or not re.match(r"^[가-힣A-Za-z ·]{0,18}(?:은|는|이|가|도)?\s*(?:\(|약\s*)?\s*$", 뒤[:t.start()]):
                    continue
                v = 값(t.group(0))
                if v is None or v == 0:
                    continue
                음 = m.group(1).startswith(("음", "마이너스", "적자"))
                if (음 and v > 0) or (not 음 and v < 0):
                    걸.append(_걸("막음", "부호어와 장부 값의 부호가 다르다", "%d행" % n,
                                "「%s … %s」 — 장부 값 %s(부호 %s) — 낱말을 값의 부호에 맞추거나 값을 고친다" % (m.group(1), t.group(0), "%.6g" % v, "+" if v > 0 else "−")))
            b = _배수어.search(월)
            if b:
                수들 = [x.group(0) for x in G.값토큰.finditer(월) if 값(x.group(0)) is not None]
                if len(수들) == 2:
                    a1, a2 = abs(값(수들[0])), abs(값(수들[1]))
                    if a1 and a2:
                        비 = max(a1, a2) / min(a1, a2)
                        if b.group(1):
                            k = _배수값.get(b.group(1))
                            if k and 비 < k - 1e-9:
                                걸.append(_걸("막음", "배수어와 장부 값이 맞지 않는다", "%d행" % n,
                                            "「%s 배 %s」 — %s 와 %s 의 비는 %.2f배다" % (b.group(1), b.group(2), 수들[0], 수들[1], 비)))
                        elif b.group(3) and 비 < 2.0 - 1e-9:
                            걸.append(_걸("막음", "배수어와 장부 값이 맞지 않는다", "%d행" % n,
                                        "「절반 %s」 — %s 와 %s 의 비는 %.2f배다(절반이면 2배 이상)" % (b.group(4), 수들[0], 수들[1], 비)))
    except Exception:                                        # noqa: BLE001 — 판정 보조 검사: 못 돌면 막지 않는다(다른 ⑱ 검사가 그대로 선다)
        return []
    return 걸


# ══════════════════════════════════════════════════════════════════ 국면 판정 둘(1.1.20)
# 2절 생애주기 문장의 「업황으로는 …」(가정 `메타.생애주기.위치`)과 업황 절의 국면 판정 문장(업황 원고)은 다른 재료가 쓴다. 어느 쪽이 맞는지 정할
# 구조 재료가 코드에 없으므로 고치지 않고 경보로 둘을 맞대게 한다. 국면 이름을 사이클 위의 자리(바닥 0 · 회복 1 · 확장 2 · 고점 3 · 하강 4)로,
# 앞뒤 말(초입 · 중반 · 후반 …)을 그 자리 안의 치우침으로 읽는다 — 낱말을 막는 목록이 아니라 위치 눈금이다(설정 `국면` 으로 바꿀 수 있다).
_국면기본 = {"자리": {"바닥": 0, "저점": 0, "회복": 1, "확장": 2, "상승": 2, "호황": 3, "고점": 3, "정점": 3,
                     "둔화": 4, "하강": 4, "조정": 4, "수축": 4, "침체": 4},
           "치우침": {"초입": -0.25, "초반": -0.25, "초기": -0.25, "앞부분": -0.25, "앞쪽": -0.25,
                     "중반": 0, "한가운데": 0, "가운데": 0, "중후반": 0.25, "후반": 0.4, "뒷부분": 0.4, "막바지": 0.4, "끝": 0.4},
           "문턱": 0.5}


def _국면설정(설=None):
    d = dict(_국면기본)
    d.update(((설 or {}).get("국면") or {}) if isinstance((설 or {}).get("국면"), dict) else {})
    return d


def 국면자리(글, 설=None, 이름앞만=False):
    """글 → 사이클 위 자리 구간 (아래, 위) 또는 None. 이름앞만 — 「… 국면 · 구간」 바로 앞 어절의 국면 이름만 읽는다(업황 절의 판정 문장)."""
    c = _국면설정(설)
    자, 치 = c["자리"], c["치우침"]
    이름식 = "|".join(sorted(map(re.escape, 자), key=len, reverse=True))
    치식 = "|".join(sorted(map(re.escape, 치), key=len, reverse=True))
    if 이름앞만:
        m = re.search(r"(?<![가-힣])(?:[가-힣]+의\s+)?(%s)(?:기)?\s*(?:국면|구간)(?:의)?\s*(%s)?" % (이름식, 치식), 글)
        if not m:
            return None
        v = 자[m.group(1)] + (치.get(m.group(2)) or 0 if m.group(2) else 0)
        return (v, v)
    든 = [(mm.start(), 자[mm.group(1)]) for mm in re.finditer(r"(%s)" % 이름식, 글)]
    if not 든:
        return None
    끝말 = [mm.group(1) for mm in re.finditer(r"(%s)" % 치식, 글)]
    아래, 위 = min(v for _i, v in 든), max(v for _i, v in 든)
    if 끝말:
        위 = 위 + 치[끝말[-1]]
        아래 = min(아래, 위)
    return (아래, 위)


def 국면판정(편, 가정=None, 설=None):
    """⑱ 국면 판정 둘이 다름 [경보] — 2절 「업황으로는 X에 있는」 과 업황 절의 「… 국면 · 구간 …(으)로 판단 · 판정 · 보았다」 가운데 맞는 것이 없다."""
    G = _G()
    c = _국면설정(설)
    줄들 = G._쪼갬(편)
    가 = None
    for n, 월, _앞, 몫, 절 in G._글월(줄들, ("본편",)):
        m = re.search(r"업황으로는\s*(.+?)(?:에서|에)\s*있", 월)
        if m and not 월.startswith("|"):
            가 = (n, m.group(1).strip())
            break
    if not 가:
        return []
    a = 국면자리(가[1], 설)
    if a is None:
        return []
    판 = []
    for n, 월, _앞, 몫, 절 in G._글월(줄들, ("본편",)):
        if "업황" not in (절 or "") or n == 가[0] or n in {x for x, t, _m in 줄들 if t.startswith("|")}:
            continue
        if not re.search(r"(?:국면|구간)", 월) or not re.search(r"판단했|판정했|보았|봤|봅니다|판단합니다", 월):
            continue
        b = 국면자리(월, 설, 이름앞만=True)
        if b is not None:
            판.append((n, 월, b))
    if not 판:
        return []
    거리 = [(max(0.0, b[0] - a[1], a[0] - b[1]), n, 월) for n, 월, b in 판]
    if min(d for d, _n, _w in 거리) < float(c.get("문턱") or 0.5):
        return []
    d, n, 월 = min(거리, key=lambda x: x[0])
    return [_걸("경보", "국면 판정 둘이 다름", "%d행 · %d행" % (가[0], n),
               "생애주기 문장의 업황 「%s」 과 업황 절의 판정 「%s」 이 사이클의 다른 자리를 말한다 — 같은 재료로 한쪽에 맞춘다(메타.생애주기.위치 또는 업황 원고)"
               % (가[1][:40], 월[:80]))]


def 검사18(편, 장부, 가정, 엔진값=None):
    설 = 설정()
    낸 = []
    for f in (lambda: 빈부록참조(편, 설), lambda: 표합계(편, 설), lambda: 서술값(편, 장부, 설), lambda: 격자채택(편, 장부),
              lambda: 열정의(편, 설), lambda: 삼분역산(편), lambda: 사실조건(편, 가정, 설, 엔진값 or (lambda x: 외부범위엔진값(가정, x))),
              lambda: 적었다대상(편), lambda: 비교어(편, 장부, 설), lambda: 국면판정(편, 가정, 설)):
        try:
            낸 += f()
        except Exception as e:                               # noqa: BLE001
            낸.append(_걸("막음", "검사를 돌리지 못했다(정합)", "-", "%s: %s" % (type(e).__name__, str(e)[:160])))
    return 낸


판단전파뺄머리 = ("파일:", "H:", "상:", "메:", "주:", "목:", "독:", "G:")


def _수(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


_지금원 = {}


def _지금원천(가정, 경로, 장부=None):
    """옛 장부의 키를 지금 가정으로 다시 셈할 원천 — 게이트 ⑦ 과 같은 재료(가격 성립 · 부록 · 주가 · 목표 · 독자 입력 · 재료 파일)를
    지금 장부에서 싣는다(1.1.19 — 「가:」 · 「파일:」 키가 재료 없이 풀리지 않아 값이 그대로인 키를 「바뀐 값」 으로 읽었다). 한 번 짓는다."""
    import 레터 as L                                          # noqa: PLC0415
    k0 = (id(가정), id(장부), 경로)
    if _지금원.get("id") != k0:
        장 = 장부 if isinstance(장부, dict) else {}
        재료 = {}
        try:
            재료 = L.재료파일읽기(경로, 장.get("재료파일"), 가정)[0] if 경로 else {}
        except Exception:                                    # noqa: BLE001
            재료 = {}
        _지금원.clear()
        _지금원.update({"id": k0, "원": L.원천만들기(가정, 표다섯=False, 가성=장.get("가격성립입력"), 부록=장.get("부록입력"),
                                                   주가=장.get("주가입력"), 목표=장.get("목표입력"), 독자=장.get("독자입력"),
                                                   파일=재료, 경로=경로)})
    return _지금원["원"]


def _지금키값(가정, 경로, 키, 장부=None, 식=None):
    """옛 장부의 키를 지금 가정으로 다시 셈한 값(못 풀면 None). 식 키(「식:[연산, …]」 — CAGR · 괴리 · 차 따위)는 그 식을 다시 셈한다
    (1.1.19 — 식 키를 `키풀기` 에 넘겨 늘 None 이 되어, 원고가 더 부르지 않은 CAGR 의 옛 글과 같은 외부 수치를 「옛 값」 으로 막았다)."""
    try:
        import 레터 as L                                      # noqa: PLC0415
        원 = _지금원천(가정, 경로, 장부)
        if 식 is None and isinstance(키, str) and 키.startswith("식:"):
            식 = json.loads(키[2:])
        if isinstance(식, list) and 식:
            return L.식값(식, 원)
        return L.키풀기(키, 원)
    except Exception:                                        # noqa: BLE001
        return None


def 판단전파(편, 장부, 가정, 경로, 설=None):
    """1.1.4(A) — 판단 변경 전파 관문[막음]. 재실행에서 값 · 판단을 바꿨는데 손 문장 · 방법 서술 · 부록 E 검토의견 · 부록 H 가 옛 값 · 옛 근거를 그대로
    적는 자리를 막는다(1.1.3 재채점 8곳 모두 — 원고의 글자 숫자는 근거대장이 받쳐 ⑦ 이 장부와 맞대지 않았다).
      ① 옛 장부(`<초안>.장부.옛.json` — 다른 키트 판으로 낸 장부를 레터.py 가 남긴다)의 숫자 가운데 지금 값이 바뀐 키의 옛 글(「104,468원」 · 「0.367」)이
         지금 장부의 어느 글과도 같지 않은데 레터에 남았으면 막는다(숫자 경계로 찾는다 · 4자 미만 글은 보지 않는다)
      ② 가정 `관측.판단변경[]` 의 「옛」(버린 근거 · 옛 판단 문구 — 저자가 판단대장에서 바꾼 자리)이 레터에 남았으면 막는다
    「불일치 0」 같은 자기 진술은 이 검사를 지난 레터에만 설 수 있다(이 검사가 막으면 게이트가 레터를 내지 않는다)."""
    설 = 설 or 설정()
    낸 = []
    본문 = 편
    조각들 = [("%s" % x) for x in ((장부 or {}).get("원고") or []) if x]
    def 바깥줄(i):                                         # 1.1.9 — 출처 주소가 붙은 줄은 외부 자료(업황 지표 · 반대 대조 따위)다 — 우연히 같은 옛 장부 글을 막지 않는다
        시 = 본문.rfind("\n", 0, i) + 1
        끝 = 본문.find("\n", i)
        return bool(re.search(r"https?://", 본문[시:끝 if 끝 >= 0 else len(본문)]))

    지금글 = sorted({("%s" % x.get("글")).strip() for x in (장부 or {}).get("숫자") or []
                    if isinstance(x, dict) and x.get("글") is not None and re.search(r"\d", "%s" % x.get("글"))}, key=len, reverse=True)

    def 지금글자리(i, 조각):
        """1.1.19 — 본문 i 의 옛 글이 지금 장부 글(자리표시가 편 글 — 「+5.6%」 · 「41.5%p」)의 한 부분인가. 지금 키가 찍은 글이면
        옛 값의 잔재가 아니다(옛 글 「5.6%」 와 지금 글 「+5.6%」 는 글이 달라 아래 `새글` 로는 걸러지지 않았다)."""
        for G in 지금글:
            if len(G) <= len(조각) or 조각 not in G:
                continue
            for m in re.finditer(re.escape(조각), G):
                시 = i - m.start()
                if 시 >= 0 and 본문[시:시 + len(G)] == G:
                    return True
        return False

    def 남은자리(패, 조각, 시, 끝, 줄시=None):
        for m in re.finditer(패, 본문[시:끝]):
            i = 시 + m.start()
            if not 바깥줄(i if 줄시 is None else 줄시) and not 지금글자리(i, 조각):
                return 본문.count("\n", 0, 줄시 if 줄시 is not None else i) + 1
        return None

    def 찾기(조각):
        패 = r"(?<![\d.,])" + re.escape(조각) + r"(?![\d])"
        if 조각들:                                           # 저자 글 조각 가운데 그 옛 글이 든 조각이 편집본에도 남았나
            for g in 조각들:
                if re.search(패, g):
                    m = re.search(re.escape(g[:60]), 본문)
                    줄 = 남은자리(패, 조각, m.start(), m.start() + len(g) + 40, m.start()) if m else None
                    if 줄:
                        return 줄
            return None
        return 남은자리(패, 조각, 0, len(본문))
    옛이름 = (장부 or {}).get("옛장부")
    if 경로 and 옛이름 and os.path.exists(os.path.join(경로, 옛이름)):
        try:
            옛 = json.load(io.open(os.path.join(경로, 옛이름), encoding="utf-8"))
        except (OSError, ValueError):
            옛 = {}
        새값 = {x.get("키"): x.get("값") for x in (장부 or {}).get("숫자") or [] if isinstance(x, dict)}
        새글 = {("%s" % x.get("글")).strip() for x in (장부 or {}).get("숫자") or [] if isinstance(x, dict) and x.get("글") is not None}
        본 = set()
        최소 = int(((설.get("판단전파") or {}).get("최소글자")) or 4)
        for x in 옛.get("숫자") or []:
            if not isinstance(x, dict):
                continue
            k, v, g = x.get("키"), x.get("값"), ("%s" % (x.get("글") or "")).strip()
            if ("%s" % k).startswith(판단전파뺄머리):              # 재료 표 · 원천 · 상수 — 다시 지은 표의 값이라 저자 글의 같은 숫자는 대개 우연이다(카나리 — Peer 표 현금 비중)
                continue
            if not g or g in 새글 or g in 본 or len(g) < 최소 or not re.search(r"\d", g) or re.match(r"^\d{4}(년|\.)?$", g):
                continue
            nv = 새값.get(k)
            try:
                같음 = nv is not None and v is not None and abs(float(nv) - float(v)) <= 1e-9 * max(1.0, abs(float(v)))
            except (TypeError, ValueError):
                같음 = nv == v
            if not 같음 and nv is None and _수(v) is not None:  # v27 — 키만 바뀌고 값은 그대로(「−36.1% 움직였다」 → 「36.1% 내렸습니다」 의 「음」 식)면 바뀐 값이 아니다
                같음 = any(_수(w) is not None and min(abs(_수(w) - _수(v)), abs(_수(w) + _수(v))) <= 1e-9 * max(1.0, abs(_수(v)))
                         for w in 새값.values())
            if not 같음 and nv is None and 가정:                  # 레터 v27 6단계 — 지금 레터가 그 키를 찍지 않았을 뿐(추정 블록의 표가 줄었다)이면 엔진으로 지금 값을 다시 셈한다
                지금값 = _지금키값(가정, 경로, k, 장부, x.get("식"))
                try:
                    같음 = 지금값 is not None and v is not None and abs(float(지금값) - float(v)) <= 1e-9 * max(1.0, abs(float(v)))
                except (TypeError, ValueError):
                    같음 = 지금값 == v
                if not 같음 and 지금값 is not None and x.get("꼴"):      # 1.1.19 — 지금 값을 같은 꼴로 찍은 글이 옛 글과 같으면(엔진 판이 바뀌어 끝자리만 움직였다) 남은 옛 값이 아니다
                    try:
                        import 레터 as L                              # noqa: PLC0415
                        같음 = L.꼴글(지금값, x.get("꼴"), (가정 or {}).get("메타") or {}).strip() == g
                    except Exception:                                # noqa: BLE001
                        pass
            if 같음:
                continue
            줄 = 찾기(g)
            if 줄:
                본.add(g)
                낸.append(_걸("막음", "판단 변경 전파 — 옛 값이 레터에 남았다", "%d행" % 줄,
                            "「%s」(키 %s — 옛 장부 %s · 지금 %s) — 그 문장을 지금 값의 장부 키(「{키|꼴}」)로 다시 쓴다" % (
                                g, k, g, ("%s" % nv) if nv is not None else "장부에 없음")))
    for i, x in enumerate(((가정 or {}).get("관측") or {}).get("판단변경") or []):
        if not isinstance(x, dict):
            continue
        for 옛글 in (x.get("옛") if isinstance(x.get("옛"), list) else [x.get("옛")]):
            옛글 = ("%s" % (옛글 or "")).strip()
            if len(옛글) >= 2 and 옛글 in 본문:
                줄 = 본문.count("\n", 0, 본문.find(옛글)) + 1
                낸.append(_걸("막음", "판단 변경 전파 — 버린 판단의 글이 레터에 남았다", "%d행" % 줄,
                            "「%s」(관측.판단변경[%d] %s) — 바꾼 판단으로 다시 쓴다" % (옛글[:60], i, x.get("항목") or "")))
    return 낸


def 부록G빈칸(편, 가정):
    """1.1.4(C) — 날짜 둘 판에서 근거 날짜가 재무 자료 기준일 뒤인 가정(`레터.기준일뒤자동`)이 있는데 부록 G 에 표가 없으면 막는다
    (본문은 평가기준일 판 시장 자료 · 사이 기간 자료를 쓰면서 부록 G 는 「쓰지 않았다」 · 「받지 않았다」 로 비던 자리 — 1.1.3 재채점 7/8)."""
    try:
        자 = importlib.import_module("레터").기준일뒤자동(가정 or {})
    except Exception:                                        # noqa: BLE001
        return []
    if not 자:
        return []
    m = re.search(r"(?ms)^## 부록 G\..*?(?=^## 부록 |\Z)", 편)
    if not m:
        return [_걸("막음", "부록 G 가 없다", "-", "근거 날짜가 재무 자료 기준일 뒤인 가정 %d건이 있는데 부록 G 절이 없다" % len(자))]
    if not re.search(r"(?m)^\|", m.group(0)):
        return [_걸("막음", "부록 G 가 비었다", "%d행" % (편.count(chr(10), 0, m.start()) + 1),
                   "근거 날짜가 재무 자료 기준일 뒤인 가정 %d건(%s)이 있는데 부록 G 에 표가 없다 — 초안을 다시 짓는다" % (
                       len(자), " · ".join(x["가정"][0] for x in 자[:6])))]
    return []


def 검사20(편, 가정, 경로=None, 장부=None):
    설 = 설정()
    낸 = []
    for f in (lambda: 자리표시(편), lambda: 관할용어(편, 가정, 설), lambda: 판정어(편, 설), lambda: 괄호코드(편, 설), lambda: 그림(편, 설),
              lambda: 판단대장(경로, 설), lambda: 판단전파(편, 장부, 가정, 경로, 설), lambda: 부록G빈칸(편, 가정)):
        try:
            낸 += f()
        except Exception as e:                               # noqa: BLE001
            낸.append(_걸("막음", "검사를 돌리지 못했다(정합)", "-", "%s: %s" % (type(e).__name__, str(e)[:160])))
    return 낸


def main():
    import argparse                                          # noqa: PLC0415
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                        # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(allow_abbrev=False, description="레터 정합 검사(게이트 ⑱ · ⑳ 의 덧 검사)")
    ap.add_argument("편집")
    ap.add_argument("--장부", default=None)
    ap.add_argument("--가정", default=None)
    a = ap.parse_args()
    편 = io.open(a.편집, encoding="utf-8").read()
    장부 = json.load(io.open(a.장부, encoding="utf-8")) if a.장부 else {}
    가정 = json.load(io.open(a.가정, encoding="utf-8")) if a.가정 else {}
    낸 = 검사18(편, 장부, 가정) + 검사20(편, 가정, os.path.dirname(os.path.abspath(a.가정)) if a.가정 else None)
    for x in 낸:
        print("%s  %s  %s  %s" % (x["등급"], x["항목"], x["자리"], x["내용"]))
    print("레터 정합 — 막음 %d · 경보 %d" % (sum(1 for x in 낸 if x["등급"] == "막음"), sum(1 for x in 낸 if x["등급"] != "막음")))
    sys.exit(1 if any(x["등급"] == "막음" for x in 낸) else 0)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""레터그림판 — 모션 짝 그림 넷(가치 · 길 · 자 · 토네이도)을 두 판(넓은 · 좁은)으로 그린다 (v4e — 2026-10-16 디자이너 리뷰 통독 v4d).

계산하지 않는다(`레터그림` 과 같은 원칙). 레터의 그림 표 글(장부 키로 찍힌 글)을 좌표로만 바꾸고, 주석 숫자(「약 2.1배」 · 「−50%」 ·
「−21.9%」 · 「매출 합계의 35%」)도 표의 칸(레터 생성기가 장부 키로 셈해 찍은 글)에서 읽는다 — 그림이 숫자를 새로 만들지 않는다.

판
  넓은  viewBox 폭 560 — 데스크톱 그림 상자 560px 에 1:1(주 글 14px · 보조 12.5px · 축 12px). 영상(mp4 · gif)은 이 판을 2배(1120px)로 굽는다
  좁은  viewBox 폭 340 — 휴대폰(≤640px). 390px 화면의 그림 폭 358px 에서 배율 1.05(주 14.5 · 보조 13 · 축 12.5 → 렌더 12px 이상).
        글 자리 · 줄바꿈을 따로 짠다(NYT · FT 처럼 같은 숫자를 휴대폰 배치로 다시 그린다 — 줄이지 않는다)
색은 본문 토큰(`레터그림.CSS` 의 --vz-*): 초점 --accent · 대비 --flag · 맥락선 --vz-ctx · 면 맥락 --rule(테두리 1px) — 대비는 `레터그림검사`.

움직임 = 정적 그림 + 주석(data-m)
  움직이는 요소에 data-m = [[키, 속성, 처음 값, 끝 값], …] 를 단다. 끝 값은 정적 그림의 속성 값이다. 진행 {키: 0~1} 을 주면
  `진행적용` 이 속성을 바꾼다 — 같은 속성에 걸린 주석은 차례대로 읽어 「시작한 마지막 주석」 의 값을 쓴다(아직 아무것도 시작 안 했으면 첫 처음 값).
  모든 주석이 끝났으면(진행 1) 속성을 건드리지 않는다 — 진행이 다 1 이면 정적 그림과 같은 글이다.
  영상(`레터모션`)은 이 함수로 프레임을 만들고, 웹(`레터HTML` 의 스크립트)은 같은 규칙을 브라우저에서 돌린다(한 출처).
"""
from __future__ import annotations

import hashlib
import html
import json
import re

import 레터그림 as G

_e = G._e
수읽기 = G.수읽기
_폭 = G._폭

판치수 = {"넓은": {"W": 560, "주": 14.0, "보": 12.5, "축": 12.0, "줄": 18.0},
        "좁은": {"W": 340, "주": 14.5, "보": 13.0, "축": 12.5, "줄": 19.0}}
두판 = ("넓은", "좁은")


# ══════════════════════════════════════════════════════════════════ 움직임 주석 · 진행 적용

def _m(*주석):
    """data-m 속성 글 — 주석 = (키, 속성, 처음, 끝)."""
    if not 주석:
        return ""
    return ' data-m="%s"' % html.escape(json.dumps([[k, a, round(float(f), 3), round(float(t), 3)] for k, a, f, t in 주석], ensure_ascii=False),
                                       quote=True)


_태그 = re.compile(r'<([a-zA-Z]+)((?:\s+[^\s=<>]+="[^"]*")*?)\s+data-m="([^"]*)"((?:\s+[^\s=<>]+="[^"]*")*)(\s*/?)>')


def _수글(v):
    t = "%.3f" % v
    return t.rstrip("0").rstrip(".") if "." in t else t


def 진행적용(svg, 진행):
    """정적 그림 글 + 진행 {키: 0~1} → 그 순간의 그림 글. 없는 키는 1(다 된 상태)."""
    if not 진행:
        return svg

    def p(키):
        v = 진행.get(키)
        return 1.0 if v is None else max(0.0, min(1.0, float(v)))

    def 바꿈(mt):
        이름, 앞, 주, 뒤, 닫 = mt.group(1), mt.group(2), mt.group(3), mt.group(4), mt.group(5)
        묶 = {}
        for k, a, f, t in json.loads(html.unescape(주)):
            묶.setdefault(a, []).append((k, f, t))
        속 = 앞 + ' data-m="%s"' % 주 + 뒤
        바뀜 = False
        for a, 들 in 묶.items():
            v, 다 = 들[0][1], True
            for k, f, t in 들:
                q = p(k)
                if q > 0:
                    v = f + (t - f) * q
                if q < 1:
                    다 = False
            if 다:
                continue
            바뀜 = True
            새 = ' %s="%s"' % (a, _수글(v))
            if re.search(r'\s%s="[^"]*"' % re.escape(a), 속):
                속 = re.sub(r'\s%s="[^"]*"' % re.escape(a), lambda _x: 새, 속, count=1)
            else:
                속 += 새
        return "<%s%s%s>" % (이름, 속, 닫) if 바뀜 else mt.group(0)
    return _태그.sub(바꿈, svg)


# ══════════════════════════════════════════════════════════════════ 글 · 도형 조각

def _글(x, y, 글, 크기, 갈="viz-label", 앵="start", m="", 덧=""):
    return '<text x="%.1f" y="%.1f" class="%s" text-anchor="%s" dominant-baseline="middle" style="font-size:%gpx"%s%s>%s</text>' % (
        x, y, 갈, 앵, 크기, m, 덧, _e(글))


def _접기(글, 폭, 크기):
    """낱말 사이 줄바꿈 — 괄호 안에서는 줄을 바꾸지 않고(「바닥(2023년 / 평균)」 ✗), 마지막 줄이 두 글자 이하로 떨어지면(고아) 앞 줄의 끝 낱말을
    내려 둘을 고르게 한다."""
    낱, 묶 = [], None
    for w in ("%s" % 글).split():
        if 묶 is not None:
            묶 += " " + w
            if ")" in w:
                낱.append(묶)
                묶 = None
            continue
        if "(" in w and ")" not in w.split("(", 1)[1]:
            묶 = w
            continue
        낱.append(w)
    if 묶 is not None:
        낱.append(묶)
    줄 = [x.replace(" ", " ") for x in G._접기폭(" ".join(낱), 폭, 크기)]
    if len(줄) >= 2 and len(줄[-1].replace(" ", "")) <= 2:
        앞 = 줄[-2].split()
        if len(앞) >= 2:
            줄[-2], 줄[-1] = " ".join(앞[:-1]), 앞[-1] + " " + 줄[-1]
    return 줄


def _맑게(c):
    return re.sub(r"\*", "", "%s" % c).strip()


_단위꼴 = re.compile(r"^[−\-+]?[\d,]+(?:\.\d+)?\s*(조 원|억 원|만 원|억 달러|만 달러|원|%|배)$")


def _공통단위(글들):
    """금액 글들이 모두 같은 단위로 끝나면 그 단위(「조 원」), 아니면 빈 글."""
    단 = set()
    for g in 글들:
        m = _단위꼴.match(_맑게(g))
        if not m:
            return ""
        단.add(m.group(1))
    return 단.pop() if len(단) == 1 else ""


def _뗀(글, 단위):
    """「1,609조 원」 → 「1,609」(단위가 머리에 있을 때). 단위가 없으면 그대로."""
    g = _맑게(글)
    return re.sub(r"\s*%s$" % re.escape(단위), "", g) if 단위 and g.endswith(단위) else g


# ══════════════════════════════════════════════════════════════════ 가치 — 매출에서 주당가치까지(모션 A 짝)

def _이름말(이름):
    """표의 단계 이름 → 그림의 이름 — 괄호 덧말(기간)을 떼고 셈 표지를 부호로(「(+) …」 → 「+ …」)."""
    t = re.sub(r"\s*\([^()]*\)\s*$", "", 이름.strip())
    for 머, 부 in (("(+)", "+ "), ("(−)", "− "), ("(-)", "− "), ("(÷)", "÷ "), ("(±)", "± ")):
        if t.startswith(머):
            return 부 + t[len(머):].strip()
    return t


def 가치(표들, 제목="", 진행=None, 판="넓은"):
    """매출에서 주당가치까지 — 줄마다 이름(위 왼쪽) · 금액(위 오른쪽 숫자 열) · 막대(아래). 부호화 하나(리뷰 A):
    단계 막대 = --accent 채움 · 빠진 몫(앞 줄 길이의 유령 · 차감 항목) = 면 맥락 + 1px 테두리 · 더해지는 몫 = 연한 강조 면 + 1.5px 강조 테두리 ·
    합계(= 줄) = --ink 채움 · 높이 1.5배. 빠진 몫의 글(「−570 영업비용」)은 유령의 오른끝 아래 줄. 단위는 머리에 한 번.
    주식 수로 나누는 줄부터는 막대 없이 식 한 줄(「950조 원 ÷ 약 7억 1,100만 주 = 약 134만 원」 — 결과만 크게).
    넷째 칸(비교)의 글은 그 줄의 주석(「매출 합계의 35%」).
    움직임(모션 A) — 막대:k(줄여 감: 오른끝이 유령 끝에서 제 끝으로 · + : 왼끝에서 자람 · − : 합계 끝에서 왼쪽으로) · 글:k(금액 · 빠진 몫 · 주석 · = 막대)."""
    if 진행:
        return 진행적용(가치(표들, 제목, None, 판), 진행)
    항 = G.가치항(표들)
    if not 항:
        return ""
    c = 판치수[판]
    W, 주, 보 = c["W"], c["주"], c["보"]
    좁 = 판 == "좁은"
    막 = [d for d in 항 if d["a"] is not None]
    단위 = _공통단위([d["금액"] for d in 막])
    x0, x1 = 4.0, W - 4.0
    최대 = max([d["b"] for d in 막] + [d["앞b"] for d in 막 if d["앞b"] is not None] + [1.0])

    def X(v):
        return x0 + (x1 - x0) * v / 최대
    기간 = ""
    m0 = re.search(r"\(([^()]*합계)\)\s*$", 항[0]["이름"])
    if m0:
        기간 = m0.group(1)
    s, y = [], 6.0
    머 = "단위: %s" % 단위 if 단위 else ""
    if 기간:
        머 += (" · " if 머 else "") + "위 넷은 %s" % 기간
    if 머:
        for j, 줄 in enumerate(_접기(머, W - 8, 보) if 좁 else [머]):
            s.append(_글(x0, y + 8 + (보 + 4) * j, 줄, 보, "viz-tick"))
        y += 8 + (보 + 4) * (len(_접기(머, W - 8, 보)) if 좁 else 1) + 8
    나눔 = next((k for k, d in enumerate(항) if d["a"] is None), None)
    for k, d in enumerate(항):
        if d["a"] is None:
            continue
        셈 = d["셈"]
        합 = 셈 == "="
        bh = 18.0 if 합 else 12.0
        글m = _m(("글:%d" % k, "opacity", 0, 1)) if k else ""
        값 = _뗀(d["금액"], 단위)
        if 셈 in ("+", "−"):
            값 = 셈 + 값
        이 = _이름말(d["이름"])
        주석 = d.get("주석") or ""
        w값 = _폭(값, 주) * 1.04
        # 이름 줄 — 이름 · (주석) · 금액
        y이 = y + 9
        s.append(_글(x0, y이, 이, 주, "viz-label viz-strong" if 합 else "viz-label"))
        s.append(_글(x1, y이, 값, 주, "viz-label viz-value viz-strong" if 합 else "viz-label viz-value", "end", 글m))
        주석줄 = None
        if 주석:
            w주 = _폭(주석, 보) * 1.04
            if not 좁 and x0 + _폭(이, 주) * 1.04 + 16 + w주 <= x1 - w값 - 14:
                s.append(_글(x1 - w값 - 14, y이, 주석, 보, "viz-note", "end", 글m))
            else:
                주석줄 = (주석, w주)
        y막 = y + 22
        a, b2 = d["a"], d["b"]
        if d["앞b"] is not None:                              # 줄여 감 — 유령(앞 줄 길이)은 처음부터 제자리, 제 막대가 그 안에 선다
            s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%g" class="vz-gone"/>' % (X(0), y막, X(d["앞b"]) - X(0), bh))
            s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%g" class="vz-step"%s><title>%s %s</title></rect>' % (
                X(0), y막, max(X(b2) - X(0), 1.0), bh, _m(("막대:%d" % k, "width", X(d["앞b"]) - X(0), max(X(b2) - X(0), 1.0))), _e(이), _e(d["금액"])))
        elif 셈 == "+":
            w = max(X(b2) - X(a), 1.0)
            s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%g" class="vz-add"%s><title>%s %s</title></rect>' % (
                X(a), y막, w, bh, _m(("막대:%d" % k, "width", 0, w)), _e(이), _e(d["금액"])))
        elif 셈 == "−":
            w = max(X(b2) - X(a), 1.0)
            s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%g" class="vz-gone"%s><title>%s %s</title></rect>' % (
                X(a), y막, w, bh, _m(("막대:%d" % k, "x", X(b2), X(a)), ("막대:%d" % k, "width", 0, w)), _e(이), _e(d["금액"])))
        elif 합:
            s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%g" class="vz-sum"%s><title>%s %s</title></rect>' % (
                X(a), y막, max(X(b2) - X(a), 1.0), bh, 글m, _e(이), _e(d["금액"])))
        else:
            s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%g" class="vz-step"><title>%s %s</title></rect>' % (
                X(a), y막, max(X(b2) - X(a), 1.0), bh, _e(이), _e(d["금액"])))
        y = y막 + bh
        아래 = []                                            # 막대 아래 줄 — 빠진 몫(유령 오른끝에 붙임) · 좁은 판의 주석(왼쪽)
        if d["앞b"] is not None and d["빠짐"]:
            m = re.match(r"^(.*?)\s*([−\-]?[\d,]+(?:\.\d+)?\s*(?:조 원|억 원|만 원|억 달러|만 달러|원)?)$", d["빠짐"])
            말 = ("−%s %s" % (_뗀(m.group(2), 단위), m.group(1))) if m else d["빠짐"]
            w = _폭(말, 보) * 1.04
            ex = max(X(d["앞b"]), x0 + w)
            아래.append((ex - w, ex, 말, "viz-tick", "end", ex))
        if 주석줄:
            아래.append((x0, x0 + 주석줄[1], 주석줄[0], "viz-note", "start", x0))
        줄수 = 0
        놓인 = []
        for l0, r0, 말, 갈, 앵, ax in 아래:                     # 빠진 몫의 글이 먼저(첫 줄), 주석은 그 뒤
            줄 = 0
            while any(q == 줄 and not (r0 + 8 <= a2 or b3 + 8 <= l0) for a2, b3, q in 놓인):
                줄 += 1
            놓인.append((l0, r0, 줄))
            s.append(_글(ax, y + 4 + 보 / 2 + (보 + 5) * 줄, 말, 보, 갈, 앵, 글m))
            줄수 = max(줄수, 줄 + 1)
        y += 4 + (보 + 5) * 줄수 + 10
    if 나눔 is not None:                                      # 주식 수로 나누기 — 단위가 바뀌므로 막대 없이 식 한 줄(컷)
        뒤 = 항[나눔:]
        m = _m(("글:%d" % 나눔, "opacity", 0, 1))
        앞합 = next((d for d in reversed(항[:나눔]) if d["셈"] == "="), None)
        if len(뒤) == 2 and 뒤[0]["셈"] == "÷" and 뒤[1]["셈"] == "=" and 앞합 is not None:
            왼 = "%s ÷ %s =" % (_맑게(앞합["금액"]), _맑게(뒤[0]["금액"]))
            결 = _맑게(뒤[1]["금액"])
            큰 = 18.0
            y += 4
            if not 좁 and _폭(왼, 주) * 1.04 + 8 + _폭(결, 큰) * 1.04 <= x1 - x0:
                s.append(_글(x0, y + 11, 왼, 주, "viz-label", "start", m))
                s.append(_글(x0 + _폭(왼, 주) * 1.04 + 8, y + 11, 결, 큰, "viz-label viz-strong viz-value", "start", m))
                y += 26
            else:
                s.append(_글(x0, y + 10, 왼, 주, "viz-label", "start", m))
                s.append(_글(x0, y + 10 + 주 + 14, 결, 큰, "viz-label viz-strong viz-value", "start", m))
                y += 10 + 주 + 14 + 14
        else:
            for d in 뒤:
                s.append(_글(x0, y + 10, _이름말(d["이름"]), 주, "viz-label", "start", m))
                s.append(_글(x1, y + 10, _맑게(d["금액"]), 주, "viz-label viz-value", "end", m))
                y += 24
    H = y + 6
    return ('<svg class="viz viz-%s vz-value" viewBox="0 0 %d %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">' % (
        "wide" if not 좁 else "narrow", W, int(round(H)), _e(제목 or "그림")) + "".join(s) + "</svg>")


# ══════════════════════════════════════════════════════════════════ 길 — 경로와 기준선(모션 B 짝)

def _때(머리):
    """기간 머리 → 달력 위 자리(해 + 몫) · 영구인가. 「2026년 2분기」 → 2026.375 · 「2026 하반기(추정)」 → 2026.75 · 「2027(추정)」 → 2027.5 ·
    「2032년~」 → (2032.5, 영구). v4f — 「2026 9개월(추정)」(평가기준일이 3월 말 · 9월 말인 회사의 잔여 기간 열 — `레터.열이름`)은 그해의 끝
    N개월(2026.625), 「(실적)」 이면 그해의 앞 N개월(2026.375). 못 읽으면 None."""
    실적 = "실적" in ("%s" % 머리) and "추정" not in ("%s" % 머리)
    t = re.sub(r"\((?:추정|실적)\)", "", 머리).strip()
    m = re.match(r"^(\d{4})년?\s*(.*)$", t)
    if not m:
        return None
    해, 덧 = int(m.group(1)), m.group(2).strip()
    if 덧 in ("~", "이후"):
        return 해 + 0.5, True
    q = re.match(r"^(\d)분기$", 덧)
    if q:
        return 해 + (int(q.group(1)) - 0.5) / 4.0, False
    if 덧 == "상반기":
        return 해 + 0.25, False
    if 덧 == "하반기":
        return 해 + 0.75, False
    if 덧 in ("", "평균", "연간"):
        return 해 + 0.5, False
    q = re.match(r"^(\d{1,2}(?:\.\d)?)\s?개월$", 덧)              # 「5.8개월」(52/53주 · 월중 기준일 — 레터.열이름 소수 한 자리)
    if q and 0 < float(q.group(1)) < 12:
        k = float(q.group(1))
        return (해 + k / 24.0) if 실적 else (해 + 1 - k / 24.0), False
    return None


_해평균 = re.compile(r"(\d{4})년 평균")


def 길자료(표들, 제목=""):
    """그림 「길」 의 재료 → dict 또는 None.
    경로(첫 표의 그릴 줄 — 첫 열이 실적이면 실적 점), 가로선(둘째 표), 실적 점(첫 열 + 이름에 「YYYY년 평균」 이 든 가로선 — 그해 가운데),
    눈금 기준선(이름이 「YYYY년 평균」 뿐인 선 — 가로선을 긋지 않고 실적 점으로만), 주석(셋째 표의 「A ÷ B」 줄 — 그 구분 칸의 글)."""
    계열, 값, 선들 = G._길선들(표들, 제목)
    if not 계열:
        return None
    머리 = 표들[0][0][1:]
    때 = [_때(h) for h in 머리]
    if any(x is None for x in 때):
        때 = [(float(i), False) for i in range(len(머리))]
        달력 = False
    else:
        달력 = True
    경로 = [(때[i][0], v, 머리[i], 계열[i + 1]) for i, v in enumerate(값) if v is not None]
    실적 = []
    if 머리 and "추정" not in 머리[0] and not 때[0][1] and 값 and 값[0] is not None:
        실적.append((때[0][0], 값[0], 머리[0]))
    선 = []
    for i, d in enumerate(선들):
        m = _해평균.search(d["이름"])
        순수 = bool(re.match(r"^\d{4}년 평균$", d["이름"].strip()))
        if m and 달력:
            실적.append((int(m.group(1)) + 0.5, d["v"], d["이름"]))
        if 순수 and 달력:
            continue
        선.append(dict(d, i=i))
    실적.sort()
    이름 = re.sub(r"\s*\(.*$", "", 계열[0]).strip()
    주석 = None
    if len(표들) > 2:
        머3, 줄3 = 표들[2]
        k = next((j for j, h in enumerate(머3[1:], 1) if h.strip() == 이름), 1)
        for r in 줄3:
            if " ÷ " in r[0] and len(r) > k and 수읽기(r[k]) is not None:
                a, b = [x.strip() for x in r[0].split(" ÷ ", 1)]
                주석 = {"위": a, "아래": b, "글": _맑게(r[k])}
                break
    return {"계열": 계열, "경로": 경로, "실적": 실적, "선": 선, "주석": 주석, "영구": any(x[1] for x in 때), "달력": 달력,
            "끝값": next((v for v in reversed(값) if v is not None), None)}


def 길차례(표들, 제목=""):
    """모션 B 의 공개 순서 — 경로 → 경로 끝 이름 → 맥락 가로선(함께) → 강조 가로선(주가 · 종가) → 주석 괄호.
    → {"맥락": [가로선 번호], "강조": [가로선 번호], "경로글": 번호 또는 None, "주석": bool}."""
    z = 길자료(표들, 제목)
    if not z:
        return {"맥락": [], "강조": [], "경로글": None, "주석": False}
    맥, 강, 경 = [], [], None
    for d in z["선"]:
        if d["경로"]:
            경 = d["i"]
        elif d["cls"] == "viz-ref-2":
            강.append(d["i"])
        else:
            맥.append(d["i"])
    return {"맥락": sorted(맥, key=lambda i: G._길선들(표들, 제목)[2][i]["v"]), "강조": 강, "경로글": 경, "주석": z["주석"] is not None}


def 길(표들, 제목="", 진행=None, 판="넓은"):
    """경로와 기준선 — 가로축은 달력 시간에 비례(분기 · 반기 · 해의 가운데), 실적은 회색 선 · 점(맥락), 첫 실적 열 오른쪽은 「추정」 띠.
    경로(--accent)는 실적 점에서 출발해 영구기간까지 간다. 가로선: 주가 · 종가의 전제(--flag 실선) · 그 밖(맥락선 점선). 이 평가의 기준이 경로
    끝값과 같으면 가로선 없이 경로 끝 이름. 이름이 「YYYY년 평균」 뿐인 선(눈금 기준)은 선을 긋지 않고 실적 점으로. 주석 괄호(셋째 표 —
    「주가가 전제한 정상 수준 ÷ 이 평가의 기준」 → 「약 2.1배」)가 이 그림의 유일한 굵은 글이다.
    넓은 판은 이름을 플롯 오른쪽 열에, 좁은 판은 오른쪽에 값만 두고 이름은 그림 아래 범례 줄로.
    움직임(모션 B) — 선(경로를 x 몫으로 — 잘라 보이는 사각형의 폭) · 선글 · 가로:i(왼쪽에서 긋기) · 가로글:i · 주석."""
    if 진행:
        return 진행적용(길(표들, 제목, None, 판), 진행)
    z = 길자료(표들, 제목)
    if not z or len(z["경로"]) < 2:
        return ""
    c = 판치수[판]
    W, 주, 보, 축 = c["W"], c["주"], c["보"], c["축"]
    좁 = 판 == "좁은"
    선 = z["선"]
    경로선 = next((d for d in 선 if d["경로"]), None)
    보이는선 = [d for d in 선 if not d["경로"]]
    # 가로 범위 — 실적 점부터 영구기간 끝까지
    ts = [t for t, *_r in z["경로"]] + [t for t, *_r in z["실적"]]
    t0, t1 = min(ts), max(ts)
    if z["달력"]:
        t0 = float(int(t0))
        t1 = float(int(t1)) + 1.0
    else:
        t0, t1 = t0 - 0.5, t1 + 0.5
    # 세로 — 0 부터 깔끔한 눈금
    vs = [v for _t, v, *_r in z["경로"]] + [d["v"] for d in 선] + [v for _t, v, _n in z["실적"]]
    눈 = G._눈금(max(vs) * 1.04)
    if len(눈) <= 4:
        날 = (눈[1] - 눈[0]) / 2.0
        눈 = [round(날 * i, 10) for i in range(int(round(눈[-1] / 날)) + 1)]
    top = 눈[-1]
    l = 8 + _폭("{:,.0f}".format(top), 축) * 1.05
    값폭 = max([_폭(d["값글"], 주) * 1.04 for d in 선] + [0.0])
    if 좁:
        pr = W - 값폭 - 18
    else:
        이름폭 = 178.0
        pr = W - (값폭 + 8 + 이름폭) - 12
    pt, ph = 30.0, (W * (0.62 if not 좁 else 0.66))
    pb = pt + ph

    def X(t):
        return l + (pr - l) * (t - t0) / ((t1 - t0) or 1.0)

    def Y(v):
        return pb - ph * v / top
    s = []
    m선 = "vzc" + hashlib.md5(("%s|%s|%s" % (제목, 판, 표들)).encode("utf-8")).hexdigest()[:10]      # 잘라 보이는 사각형의 id — 글이 같으면 같다
    글자리 = []                                              # v4f — 축 글 상자(「실적」 이름이 눈금 · 해 글과 겹치지 않게)

    def 축글(x, y, 글, 크기, 앵="start"):
        글자리.append(G._글상자(x, y, 글, 크기, 앵, True))
        return _글(x, y, 글, 크기, "viz-tick", 앵)
    # 추정 띠 — 첫 실적 열(경로 첫 점) 오른쪽
    x추 = X(z["경로"][0][0]) if z["실적"] else None
    if x추 is not None:
        s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" class="vz-band"/>' % (x추, pt - 16, pr - x추, ph + 16))
        s.append(축글(x추 + 5, pt - 8, "추정", 축))
    for g in 눈:                                            # 눈금선 · 세로 눈금 글
        s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="viz-grid"/>' % (l, pr, Y(g), Y(g)))
        s.append(축글(l - 5, Y(g), "{:,.0f}".format(g), 축, "end"))
    # 가로축 — 해의 가운데에 해 이름(붐비면 첫 해만 네 자리)
    if z["달력"]:
        해들 = list(range(int(t0), int(t1)))
        영구해 = int(z["경로"][-1][0]) if z["영구"] else None
        글들 = []
        for k, h in enumerate(해들):
            g = "%d" % h if k == 0 else ("%02d" % (h % 100) if 좁 or len(해들) > 8 else "%d" % h)
            if 영구해 is not None and h == 영구해:
                g += "~"
            글들.append((X(h + 0.5), g))
        for x, g in 글들:
            s.append(축글(x, pb + 14, g, 축, "middle"))
        for h in 해들 + [int(t1)]:
            s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="viz-axis-tick"/>' % (X(h), X(h), pb, pb + 4))
    else:                                                   # v4f — 달력으로 못 읽는 머리: 해 · 덧말 두 줄, 붐비면 솎는다(`레터그림._x축글` — 글이 겹치지 않게)
        for x, 줄, g in G._x축글([X(t) for t, *_r in z["경로"]], [h for _t, _v, h, _g in z["경로"]], 축, 2, W - 2):
            s.append(축글(x, pb + (14 if 줄 == 1 else 27), g, 축, "middle"))
    s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="viz-axis"/>' % (l, pr, pb, pb))
    # 실적 — 회색 선 · 점(맥락, 처음부터)
    실pts = [(X(t), Y(v)) for t, v, _n in z["실적"]]
    if len(z["실적"]) >= 2:
        s.append('<polyline points="%s" class="vz-past"/>' % " ".join("%.1f,%.1f" % p for p in 실pts))
    for t, v, n in z["실적"]:
        if abs(t - z["경로"][0][0]) < 1e-9 and abs(v - z["경로"][0][1]) < 1e-9:
            continue                                         # 경로의 첫 점과 같은 실적 점은 경로 점(강조) 하나로
        s.append('<circle cx="%.1f" cy="%.1f" r="3.5" class="vz-past-dot"><title>%s %s</title></circle>' % (X(t), Y(v), _e(n), "{:,.0f}".format(v)))
    if len(z["실적"]) >= 2:                                 # 「실적」 — 끝에서 둘째 실적 점 곁 · 마지막 실적 선의 가운데 위(v4f — 가로선 · 경로 · 축 글을 덮지 않는 첫 자리)
        (ax, ay), (bx2, by2) = 실pts[-2], 실pts[-1]
        경pts = [(X(t), Y(v)) for t, v, *_r in z["경로"]] + ([(pr, Y(z["경로"][-1][1]))] if z["영구"] else [])
        마 = (G._선분들(실pts) + G._선분들(경pts) + [("점", (x, y, 3.5)) for x, y in 실pts] + [("점", (경pts[0][0], 경pts[0][1], 4.5))]
             + [("선", (l, Y(d["v"]), pr, Y(d["v"]))) for d in 보이는선])
        mx, my = (ax + bx2) / 2.0, (ay + by2) / 2.0
        후 = [(ax - 8, ay - 12, "end"), (mx - 6, my - 10, "end"), (mx + 6, my - 10, "start"), (ax + 8, ay - 12, "start"), (ax - 8, ay + 14, "end"),
             (ax + 8, ay + 14, "start"), (mx - 6, my + 12, "end"), (ax, ay - 16, "middle"), (mx, my - 22, "middle")]
        고른 = G._첫자리([(G._글상자(x, y, "실적", 보, 앵, True), (x, y, 앵)) for x, y, 앵 in 후
                       if 2 <= G._글상자(x, y, "실적", 보, 앵, True)[0] and G._글상자(x, y, "실적", 보, 앵, True)[2] <= pr - 2
                       and G._글상자(x, y, "실적", 보, 앵, True)[3] <= pb - 1], 글자리, 마크=마) or 후[0]
        s.append(_글(고른[0], 고른[1], "실적", 보, "viz-tick", 고른[2]))
    # 가로선 — 왼쪽에서 오른쪽으로(가로:i)
    자 = []
    for d in 보이는선:
        강 = d["cls"] == "viz-ref-2"
        갈 = "vz-ref-flag" if 강 else "vz-ref-ctx"
        s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="%s"%s><title>%s %s</title></line>' % (
            l, pr, Y(d["v"]), Y(d["v"]), 갈, _m(("가로:%d" % d["i"], "x2", l, pr)), _e(d["이름"]), _e(d["값글"])))
        자.append((Y(d["v"]), 1 if 강 else 2, d, "가로글:%d" % d["i"]))
    # 경로 — x(시간) 몫으로 그린다: 잘라 보이는 사각형의 폭(선형)
    pts = [(X(t), Y(v)) for t, v, *_r in z["경로"]]
    if z["영구"]:
        pts.append((pr, pts[-1][1]))
    cx0 = pts[0][0] - 6
    s.append('<clipPath id="%s"><rect x="%.1f" y="0" width="%.1f" height="%.1f"%s/></clipPath>' % (
        m선, cx0, pr - cx0 + 8, pb + 20, _m(("선", "width", 6, pr - cx0 + 8))))
    s.append('<polyline points="%s" class="vz-path" clip-path="url(#%s)"/>' % (" ".join("%.1f,%.1f" % p for p in pts), m선))
    s.append('<circle cx="%.1f" cy="%.1f" r="4.5" class="vz-dot-acc"><title>%s %s</title></circle>' % (
        pts[0][0], pts[0][1], _e(z["경로"][0][2]), _e(z["경로"][0][3])))
    for t, v, h, g in z["경로"][1:]:
        s.append('<circle cx="%.1f" cy="%.1f" r="8" class="viz-hit"><title>%s %s</title></circle>' % (X(t), Y(v), _e(h), _e(g)))
    if 경로선 is not None:
        자.append((pts[-1][1], 0, 경로선, "선글"))
    # 주석 괄호 — 「위 ÷ 아래」: 두 선(아래가 경로 끝 이름이면 경로 끝값)의 높이 사이
    주석 = z["주석"]
    if 주석:
        위 = next((d for d in 선 if d["이름"] == 주석["위"]), None)
        아 = next((d for d in 선 if d["이름"] == 주석["아래"]), None)
        if 위 is not None and 아 is not None:
            ya, yb = Y(위["v"]), Y(아["v"])
            bx = pr - 10
            m주 = _m(("주석", "opacity", 0, 1))
            s.append('<path d="M%.1f %.1f h-5 V%.1f h5" class="vz-bracket"%s/>' % (bx, ya + 2, yb - 2, m주))
            말 = "약 %s" % 주석["글"]
            w말 = _폭(말, 주) * 1.04                             # v4f — 경로 선 · 점 · 가로선을 덮지 않는 높이(괄호 안 — 가운데에서 위아래로 2씩,
            위끝, 아래끝 = min(ya, yb) + 주 / 2 + 1, max(ya, yb) - 주 / 2 - 1     # 그다음 괄호 위 끝 바로 위 · 아래 끝 바로 밑), 없으면 가운데
            가 = (ya + yb) / 2.0
            후 = [가] + [y for k in range(1, 80) for y in (가 - 2 * k, 가 + 2 * k) if 위끝 <= y <= 아래끝] + [min(ya, yb) - 주 / 2 - 2, max(ya, yb) + 주 / 2 + 2]
            마크 = G._선분들(pts) + [("점", (pts[0][0], pts[0][1], 4.5))] + [("선", (l, Y(d["v"]), pr, Y(d["v"]))) for d in 보이는선]
            y말 = next((y for y in 후 if not G._마크덮나((bx - 9 - w말, y - 주 / 2, bx - 9, y + 주 / 2), 마크)), 가)
            s.append(_글(bx - 9, y말, 말, 주, "viz-note viz-strong", "end", m주))
    # 이름 · 값 — 넓은 판: 오른쪽 열(값 + 이름), 좁은 판: 값만 오른쪽(이름은 범례)
    블 = []
    for y0, 순, d, 키 in 자:
        이름 = d["이름"]
        줄 = [] if 좁 else _접기(이름, 이름폭, 보)
        블.append(dict(y0=y0, 순=순, d=d, 키=키, 줄=줄, h=max(주 + 3, (보 + 3) * max(1, len(줄)))))
    놓 = G._비켜놓기([(b["y0"], b["순"], b["h"]) for b in 블], 3, pt - 12, pb + 6)
    vx = pr + 10 + 값폭
    for b, ty in zip(블, 놓):
        m = _m((b["키"], "opacity", 0, 1))
        if abs(ty - b["y0"]) > 1.5:
            s.append('<polyline points="%.1f,%.1f %.1f,%.1f %.1f,%.1f" class="viz-leader"%s/>' % (pr + 1, b["y0"], pr + 4, b["y0"], pr + 8, ty, m))
        s.append(_글(vx, ty, b["d"]["값글"], 주, "viz-label viz-value", "end", m))
        y줄 = ty - (보 + 3) * (len(b["줄"]) - 1) / 2.0
        for j, g in enumerate(b["줄"]):
            s.append(_글(vx + 6, y줄 + (보 + 3) * j, g, 보, "viz-label", "start", m))
    H = pb + (26 if z["달력"] else 39)
    if 좁:                                                 # 범례 — 위에서 아래로 값의 차례(선 견본 · 값 · 이름)
        H += 4
        for b in sorted(블, key=lambda b: b["y0"]):
            m = _m((b["키"], "opacity", 0, 1))
            갈 = "vz-path" if b["키"] == "선글" else ("vz-ref-flag" if b["d"]["cls"] == "viz-ref-2" else "vz-ref-ctx")
            s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="%s"%s/>' % (l, l + 18, H + 9, H + 9, 갈, m))
            s.append(_글(l + 24, H + 9, b["d"]["값글"], 주, "viz-label viz-value", "start", m))
            줄 = _접기(b["d"]["이름"], W - (l + 30 + _폭(b["d"]["값글"], 주) * 1.04) - 4, 보)
            xx = l + 30 + _폭(b["d"]["값글"], 주) * 1.04
            for j, g in enumerate(줄):
                s.append(_글(xx, H + 9 + (보 + 3) * j, g, 보, "viz-label", "start", m))
            H += max(20, (보 + 3) * len(줄) + 6)
        H += 4
    return ('<svg class="viz viz-%s vz-path-fig" viewBox="0 0 %d %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">' % (
        "wide" if not 좁 else "narrow", W, int(round(H)), _e(제목 or "그림")) + "".join(s) + "</svg>")


# ══════════════════════════════════════════════════════════════════ 자 — 주가별로 전제된 정상 수준(모션 C 짝)

def _수준머리(h):
    return re.sub(r"\s*(?:정상 수준|바닥)$", "", h.strip())


def _자눈(lo, hi, 칸수=5):
    """자의 눈금 자리 — lo~hi 안의 고른 수(1 · 2 · 2.5 · 5 × 10^k 의 배수). 글을 달지 않는 눈금이라 숫자를 새로 찍지 않는다."""
    import math
    폭 = hi - lo
    if 폭 <= 0:
        return []
    날 = 폭 / 칸수
    k = 10 ** math.floor(math.log10(날))
    걸음 = next(m * k for m in (1, 2, 2.5, 5, 10) if m * k >= 날 - 1e-12)
    v = math.ceil(lo / 걸음 - 1e-9) * 걸음
    낸 = []
    while v <= hi + 1e-9:
        낸.append(v)
        v += 걸음
    return 낸


_말달 = {1: "한 달", 2: "두 달", 3: "석 달", 4: "넉 달", 5: "다섯 달", 6: "여섯 달"}


def _동안(앞, 뒤):
    """두 종가 줄 이름(「2026년 6월 30일 종가가 …」)의 날짜 사이가 달로 딱 떨어지면 「한 달」 · 「두 달」 …(여섯 달까지), 아니면 빈 글.
    날짜는 표의 글이고, 숫자를 새로 찍지 않으려고 말로 적는다."""
    import calendar
    m1 = re.search(r"(\d{4})년\s?(\d{1,2})월\s?(\d{1,2})일", "%s" % 앞)
    m2 = re.search(r"(\d{4})년\s?(\d{1,2})월\s?(\d{1,2})일", "%s" % 뒤)
    if not m1 or not m2:
        return ""
    y1, n1, d1 = (int(x) for x in m1.groups())
    y2, n2, d2 = (int(x) for x in m2.groups())
    달 = (y2 - y1) * 12 + (n2 - n1)
    말1 = d1 == calendar.monthrange(y1, n1)[1]
    말2 = d2 == calendar.monthrange(y2, n2)[1]
    if 달 <= 0 or not (d1 == d2 or (말1 and 말2)):
        return ""
    return _말달.get(달, "")


def _짧은날(이름, 해=None):
    """「2026년 6월 22일 종가가 …」 → 「6.22」(칸 아래 날 글 — 해는 싣지 않는다: 칸이 날 차례이고, 해가 끝 날과 다른 줄은 오른쪽 줄 이름이
    「2025년 12월 30일 종가」 로 해를 단다). 날짜가 없으면 빈 글."""
    m = re.search(r"(\d{1,2})월\s?(\d{1,2})일", "%s" % 이름)
    return "%d.%d" % (int(m.group(1)), int(m.group(2))) if m else ""


def _날이름(이름, 해=None):
    """종가 줄 이름 → 「6월 22일 종가」(해가 끝 날의 해와 다르면 「2025년 12월 3일 종가」)."""
    m = re.search(r"(?:(\d{4})년\s?)?(\d{1,2})월\s?(\d{1,2})일", "%s" % 이름)
    if not m:
        return "종가"
    y = m.group(1)
    return ("%s년 %s월 %s일 종가" % (y, m.group(2), m.group(3))) if (y and 해 and y != 해) else "%s월 %s일 종가" % (m.group(2), m.group(3))


def _해(이름):
    m = re.search(r"(\d{4})년", "%s" % 이름)
    return m.group(1) if m else None


def 자(표들, 제목="", 진행=None, 판="넓은"):
    """주당가치와 그 값이 전제하는 정상 수준 — 가운데 세로 자에 시나리오 점, 그 왼쪽 따로 선 주가 트랙에 종가 표시(가림 없음).
    트랙 위 표시는 앞 종가 자리에 빈 원(흔적)을 남기고 꼬리선 · 화살촉으로 다음 종가까지 간다 — 정적 그림이 방향을 갖는다.
    오른쪽은 줄마다 값 · 이름 · 구분별 정상 수준 열(머리 = 구분 이름). 빈 점(다른 가정까지 바뀐 시나리오)의 뜻은 그림 아래 범례.
    마지막 종가 줄의 「기준일 대비」 칸(장부 키로 셈한 글 — 「−50%」)이 화살표 곁 주석이다.
    움직임(모션 C) — 점0 · 내림:j(앞 종가 글을 진한 글에서 흐린 글로) · 옮김:j(표시 이동 · 꼬리선 · 흔적 원) · 글:j(새 글 · 화살촉 · 주석).
    2026-10-27 — 종가 줄이 셋 이상이면(주가 경로의 꺾임 · 평가기준일 — 오르내림이 섞인다) 한 줄 트랙 대신 **주가 경로**를 그린다: 종가마다
    한 칸씩 오른쪽(차례 — 달력 비례가 아니다) · 높이는 자의 눈금 그대로 · 칸 아래 날(「6.22」 — 붐비면 두 줄로 엇갈림) · 점에서 자까지 옅은
    길잡이 선. 표시는 꺾은선을 따라 옮겨 가고(꼬리선이 겹치지 않는다) 오른쪽 종가 줄 이름은 날(「6월 22일 종가」)이다. 변화율 주석은 싣지 않는다
    (움직임이 여럿이라 하나만 짚으면 다른 움직임을 가린다 — 값은 표의 「앞 종가 대비」 칸)."""
    if 진행:
        return 진행적용(자(표들, 제목, None, 판), 진행)
    if not 표들:
        return ""
    머리, 줄들 = 표들[0]
    c = 판치수[판]
    W, 주, 보 = c["W"], c["주"], c["보"]
    좁 = 판 == "좁은"
    종 = G.자종가(표들)
    길모드 = len(종) >= 3
    i대비 = next((i for i, h in enumerate(머리) if "대비" in h), None)
    수준칸 = [i for i in range(2, len(머리)) if i != i대비]
    점들 = []
    for k, r in enumerate(줄들):
        v = 수읽기(r[1]) if len(r) > 1 else None
        if v is None:
            continue
        바 = [(r[i].strip() if i < len(r) else "—") for i in 수준칸]
        빈 = all(수읽기(x) is None for x in 바)
        대비 = r[i대비].strip() if (i대비 is not None and i대비 < len(r) and 수읽기(r[i대비]) is not None) else ""
        점들.append({"이름": _맑게(r[0]), "값글": _맑게(r[1]), "값": v, "바": 바, "빈": 빈, "j": 종.index(k) if k in 종 else None, "대비": 대비})
    if not 점들:
        return ""
    lo, hi = min(p["값"] for p in 점들), max(p["값"] for p in 점들)
    폭 = (hi - lo) or abs(hi) or 1.0
    lo, hi = lo - 폭 * 0.05, hi + 폭 * 0.05
    종점 = sorted([p for p in 점들 if p["j"] is not None], key=lambda p: p["j"])
    끝해 = _해(종점[-1]["이름"]) if 종점 else None
    if 좁:
        트x, 축x, 값x = 72.0, 94.0, 108.0
        if not 길모드:
            # 2026-10-26 — 날짜 글(「10월 23일」 처럼 두 자리 달)이 트랙 왼쪽 12 에서 끝나 그림 밖으로 나가면 트랙 · 자 · 값을 함께 민다
            넓 = max([_폭(re.search(r"(\d{1,2}월 \d{1,2}일)", p["이름"]).group(1) if re.search(r"(\d{1,2}월 \d{1,2}일)", p["이름"]) else "종가", 주) * 1.04
                     for p in 점들 if p["j"] is not None] or [0.0])
            밀 = max(0.0, 넓 + 12 + 3 - 트x)
            트x, 축x, 값x = 트x + 밀, 축x + 밀, 값x + 밀
        # 2026-11-01 — 구분 열 간격은 머리 글(구분 이름)의 폭을 따른다(「OLED 패널」 같은 긴 이름이 옆 열 머리와 겹쳤다 — 그림검사 ② 라벨 겹침)
        열간 = max([50.0] + [_폭(_수준머리(머리[i]), 보) * 1.04 + 6 for i in 수준칸])
        열끝 = [W - 4 - 열간 * (len(수준칸) - 1 - k) for k in range(len(수준칸))]
        줄h = 주 + 보 + 12
    else:
        트x, 축x = 118.0, 142.0
        값x = 축x + 98
        열간 = max([60.0] + [_폭(_수준머리(머리[i]), 보) * 1.04 + 6 for i in 수준칸])
        열끝 = [W - 6 - 열간 * (len(수준칸) - 1 - k) for k in range(len(수준칸))]
        줄h = 주 + 6
    # 길모드 — 칸 간격 · 날 글 줄(한 줄이 들어가면 한 줄, 아니면 두 줄로 엇갈림) · 칸이 그림 왼쪽 밖으로 나가면 트랙 · 자 · 값을 함께 민다
    날글 = [_짧은날(p["이름"], 끝해) for p in 종점]
    날폭 = max([_폭(x, 보) * 1.04 for x in 날글] or [0.0])
    두줄 = False
    칸 = 0.0
    if 길모드:
        n = len(종점)
        한줄칸 = max(날폭 + 8, 22.0)
        두줄칸 = max(날폭 / 2.0 + 8, 22.0)
        # 민 만큼 오른쪽 줄 글이 구분 열 · 그림 끝에 닿지 않아야 한다 — 넓은 판은 이름이 값 오른쪽 같은 줄, 좁은 판은 값 아래 줄
        이름폭 = max([_폭(_날이름(p["이름"], 끝해) if p["j"] is not None else p["이름"], 보) * 1.04 for p in 점들] or [0.0])
        값폭 = max([_폭(p["값글"], 주) * 1.04 for p in 점들] or [0.0])
        수준폭 = max([_폭(b, 주) * 1.04 for p in 점들 for b in p["바"][:1] if b not in ("—", "-", "")] or [0.0])
        왼끝 = (열끝[0] - 수준폭 - 10) if 수준칸 else (W - 6)
        if 좁:
            값한 = min(왼끝 - 값폭, W - 4 - 이름폭)
        else:
            값한 = 왼끝 - 8 - 이름폭
        밀1 = max(0.0, 4 + 날폭 / 2.0 - (트x - (n - 1) * 한줄칸))
        if 값x + 밀1 <= 값한:                                  # 날 글이 한 줄에 들면 한 줄 · 아니면 두 줄로 엇갈림(칸이 좁아진다)
            칸 = 한줄칸
        else:
            칸, 두줄 = 두줄칸, True
        밀 = max(0.0, 4 + 날폭 / 2.0 - (트x - (n - 1) * 칸))
        트x, 축x, 값x = 트x + 밀, 축x + 밀, 값x + 밀
    t = 52.0
    n점 = len(점들)
    ph = max(260.0 if not 좁 else 300.0, 줄h * n점 * 1.25)
    빈있음 = any(p["빈"] for p in 점들)

    def Y(v):
        return t + ph * (1 - (v - lo) / (hi - lo))
    s = []
    for p in 점들:
        p["y"] = Y(p["값"])
    xs = [트x - (len(종점) - 1 - p["j"]) * 칸 for p in 종점] if 길모드 else [트x for _p in 종점]
    # 머리 — 주가(트랙) · 주당가치 · 구분 이름
    s.append(_글((xs[0] + xs[-1]) / 2.0 if 길모드 else 트x, 32, "주가", 보, "viz-tick", "middle"))
    s.append(_글(값x if 좁 else 값x, 32, "주당가치", 보, "viz-tick", "start" if 좁 else "end"))
    for x, i in zip(열끝, 수준칸):
        s.append(_글(x, 32, _수준머리(머리[i]), 보, "viz-tick", "end"))
    if len(수준칸) > 1:                                     # 구분 열들을 덮는 머리 한 줄
        s.append(_글(열끝[-1], 13, "정상 수준", 보, "viz-tick", "end"))
        s.append('<line x1="%.1f" x2="%.1f" y1="21" y2="21" class="viz-grid"/>' % (열끝[0] - _폭(_수준머리(머리[수준칸[0]]), 보) * 1.04, 열끝[-1]))
    if not 길모드:
        s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="vz-track"/>' % (트x, 트x, t - 6, t + ph + 6))
    s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="viz-axis"/>' % (축x, 축x, t - 6, t + ph + 6))
    for v in _자눈(lo, hi):                                   # v4f(리뷰 C-6) — 자의 고른 간격 눈금(글 없음 — 간격이 고른 것을 보인다. 값은 점마다의 글)
        s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="viz-axis-tick"/>' % (축x - 3, 축x + 3, Y(v), Y(v)))
    # 오른쪽 줄 자리 — 값의 차례 그대로, 겹치면 민다(차례 보존)
    자리 = G._비켜놓기([(p["y"], 0 if p["j"] is not None else (1 if "기준" in p["이름"] else 2), 줄h) for p in 점들], 3, t - 8, t + ph + 30)
    n종 = len(종)

    def 글키(p):
        if p["j"] is None:
            return None
        return "점0" if p["j"] == 0 else "글:%d" % p["j"]
    # 시나리오 점 — 자 위(종가 줄은 트랙에)
    for p in sorted(점들, key=lambda p: ("기준" in p["이름"], -p["y"])):
        if p["j"] is not None:
            continue
        기준 = "기준" in p["이름"] and not p["빈"]
        cls = "vz-dot-hollow" if p["빈"] else ("vz-dot-acc" if 기준 else "vz-dot-ctx")
        s.append('<circle cx="%.1f" cy="%.1f" r="%s" class="%s"><title>%s %s</title></circle>' % (
            축x, p["y"], "5.5" if 기준 else "4.5", cls, _e(p["이름"]), _e(p["값글"])))
    # 줄 글
    글끝 = t + ph + 6                                        # v4f — 줄 글 · 날짜 글의 아래 끝(범례가 그 밑에 선다 — 겹치던 자리)
    for p, ty in zip(점들, 자리):
        글끝 = max(글끝, (ty + 주 / 2 + 3 + 보 / 2) if 좁 else (ty + 주 / 2))
        키 = 글키(p)
        m = _m((키, "opacity", 0, 1)) if 키 else ""
        강 = p["j"] is not None and p["j"] == n종 - 1
        기준 = "기준" in p["이름"] and not p["빈"]
        끝x = (값x - 4) if 좁 else (값x - _폭(p["값글"], 주) * 1.04 - 6)
        y값 = ty - (보 / 2 + 3 if 좁 else 0)
        if abs(ty - p["y"]) > 1.0:                            # 종가 줄도 자 오른쪽에서만 잇는다(트랙에서 자를 건너는 선은 자 위의 점과 엉킨다)
            s.append('<polyline points="%.1f,%.1f %.1f,%.1f %.1f,%.1f" class="viz-leader"%s/>' % (축x + 6, p["y"], 축x + 10, p["y"], 끝x, y값, m))
        이름 = p["이름"]
        if p["j"] is not None:                                # 종가 줄 — 날짜는 트랙 곁 글에 있다(길모드는 칸 아래 짧은 날 — 줄 이름이 날)
            이름 = _날이름(이름, 끝해) if 길모드 else re.sub(r"^(?:\d{4}년\s)?\d{1,2}월 \d{1,2}일\s", "", 이름)
        갈값 = "viz-label viz-value" + (" viz-strong" if (강 or 기준) else "") +             (" viz-note-flag" if p["j"] is not None else (" viz-note" if 기준 else ""))   # 값 글의 색 = 점의 색(트랙의 종가 · 자의 기준) — 가까운 두 값이 어느 점의 것인지
        if 길모드 and p["j"] is not None and not 강:           # 길모드 — 지난 종가 줄의 값은 다음 종가로 옮겨 갈 때 진한 글에서 보통 글로(끝 그림 = 보통 글)
            갈진 = "viz-label viz-value viz-strong viz-note-flag"
            m진 = _m((키, "opacity", 0, 1), ("내림:%d" % (p["j"] + 1), "opacity", 1, 0))
            m보 = _m(("내림:%d" % (p["j"] + 1), "opacity", 0, 1))
            if 좁:
                s.append(_글(값x, ty - 보 / 2 - 3, p["값글"], 주, 갈진, "start", m진, ' opacity="0" aria-hidden="true"'))
                s.append(_글(값x, ty - 보 / 2 - 3, p["값글"], 주, 갈값, "start", m보))
            else:
                s.append(_글(값x, ty, p["값글"], 주, 갈진, "end", m진, ' opacity="0" aria-hidden="true"'))
                s.append(_글(값x, ty, p["값글"], 주, 갈값, "end", m보))
        elif 좁:
            s.append(_글(값x, ty - 보 / 2 - 3, p["값글"], 주, 갈값, "start", m))
        else:
            s.append(_글(값x, ty, p["값글"], 주, 갈값, "end", m))
        if 좁:
            for x, b in zip(열끝, p["바"]):
                if b not in ("—", "-", ""):
                    s.append(_글(x, ty - 보 / 2 - 3, b, 주, "viz-label viz-value", "end", m))
            s.append(_글(값x, ty + 주 / 2 + 3, 이름, 보, "viz-tick", "start", m))
        else:
            s.append(_글(값x + 8, ty, 이름, 보, "viz-label" if not p["빈"] else "viz-tick", "start", m))
            for x, b in zip(열끝, p["바"]):
                if b not in ("—", "-", ""):
                    s.append(_글(x, ty, b, 주, "viz-label viz-value", "end", m))
    if 종점 and 길모드:
        # 주가 경로 — 칸 아래 날 줄 · 점에서 자까지 길잡이 · 꼬리선(꺾은선) · 흔적 원 · 화살촉 · 움직이는 표시 · 날 글
        ys = [p["y"] for p in 종점]
        n = len(종점)
        yb = t + ph + 10
        s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="viz-axis"/>' % (xs[0] - 8, xs[-1] + 8, yb, yb))
        for j in range(n):
            키 = "점0" if j == 0 else "글:%d" % j
            s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="viz-axis-tick"/>' % (xs[j], xs[j], yb, yb + 3))
            s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="viz-leader"%s/>' % (xs[j] + 7, 축x - 3, ys[j], ys[j], _m((키, "opacity", 0, 1))))
        for j in range(1, n):
            ax, ay, bx, by = xs[j - 1], ys[j - 1], xs[j], ys[j]
            dl = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5 or 1.0
            ux, uy = (bx - ax) / dl, (by - ay) / dl
            sx, sy, ex, ey = ax + ux * 6.5, ay + uy * 6.5, bx - ux * 9, by - uy * 9
            s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="vz-tail"%s/>' % (
                sx, ex, sy, ey, _m(("옮김:%d" % j, "x2", sx, ex), ("옮김:%d" % j, "y2", sy, ey))))
            s.append('<circle cx="%.1f" cy="%.1f" r="5.5" class="vz-trace"%s><title>%s %s</title></circle>' % (
                ax, ay, _m(("옮김:%d" % j, "opacity", 0, 1)), _e(종점[j - 1]["이름"]), _e(종점[j - 1]["값글"])))
        ax, ay, bx, by = xs[-2], ys[-2], xs[-1], ys[-1]
        dl = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5 or 1.0
        ux, uy = (bx - ax) / dl, (by - ay) / dl
        nx, ny = -uy, ux
        끝x, 끝y = bx - ux * 4, by - uy * 4
        밑x, 밑y = bx - ux * 10, by - uy * 10
        s.append('<path d="M%.1f %.1f L%.1f %.1f L%.1f %.1f Z" class="vz-arrow"%s/>' % (
            밑x + nx * 4.5, 밑y + ny * 4.5, 밑x - nx * 4.5, 밑y - ny * 4.5, 끝x, 끝y, _m(("글:%d" % (n - 1), "opacity", 0, 1))))
        mm = [("점0", "opacity", 0, 1)]
        for j in range(1, n):
            mm += [("옮김:%d" % j, "cx", xs[j - 1], xs[j]), ("옮김:%d" % j, "cy", ys[j - 1], ys[j])]
        s.append('<circle cx="%.1f" cy="%.1f" r="5.5" class="vz-dot-flag"%s><title>%s %s</title></circle>' % (
            xs[-1], ys[-1], _m(*mm), _e(종점[-1]["이름"]), _e(종점[-1]["값글"])))
        y1 = yb + 5 + 보 / 2.0
        for j, p in enumerate(종점):
            키 = "점0" if j == 0 else "글:%d" % j
            yy = y1 + ((보 + 4) if (두줄 and j % 2) else 0.0)
            if j < n - 1:
                s.append(_글(xs[j], yy, 날글[j], 보, "viz-label viz-strong", "middle", _m((키, "opacity", 0, 1), ("내림:%d" % (j + 1), "opacity", 1, 0)),
                            ' opacity="0" aria-hidden="true"'))
                s.append(_글(xs[j], yy, 날글[j], 보, "viz-tick", "middle", _m(("내림:%d" % (j + 1), "opacity", 0, 1))))
            else:
                s.append(_글(xs[j], yy, 날글[j], 보, "viz-label viz-strong", "middle", _m((키, "opacity", 0, 1))))
            글끝 = max(글끝, yy + 보 / 2.0)
    elif 종점:
        # 주가 트랙 — 종가 차례로: 흔적 원 · 꼬리선 · 움직이는 표시 · 날짜 글
        ys = [p["y"] for p in 종점]
        for j in range(1, len(종점)):
            a, b = ys[j - 1], ys[j]
            d = 1 if b > a else -1
            끝y = b - d * 9
            s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="vz-tail"%s/>' % (트x, 트x, a + d * 6, 끝y, _m(("옮김:%d" % j, "y2", a + d * 6, 끝y))))
            s.append('<circle cx="%.1f" cy="%.1f" r="5.5" class="vz-trace"%s><title>%s %s</title></circle>' % (
                트x, a, _m(("옮김:%d" % j, "opacity", 0, 1)), _e(종점[j - 1]["이름"]), _e(종점[j - 1]["값글"])))
        j끝 = len(종점) - 1
        if j끝 >= 1:
            a, b = ys[j끝 - 1], ys[j끝]
            d = 1 if b > a else -1
            m화 = _m(("글:%d" % j끝, "opacity", 0, 1))
            s.append('<path d="M%.1f %.1f L%.1f %.1f L%.1f %.1f Z" class="vz-arrow"%s/>' % (
                트x - 4.5, b - d * 10, 트x + 4.5, b - d * 10, 트x, b - d * 4, m화))
            대 = 종점[j끝]["대비"]
            if 대:
                s.append(_글(트x - 10, (a + b) / 2.0, 대, 주, "viz-note-flag viz-strong", "end", m화))
                동안 = _동안(종점[j끝 - 1]["이름"], 종점[j끝]["이름"])       # v4f(리뷰 C) — 「한 달, −50%」 의 앞말(두 종가 날짜에서 — 숫자 없음)
                y동 = (a + b) / 2.0 - 주 / 2.0 - 보 / 2.0 - 3
                아래끝 = (주 + 6 + 보 / 2.0) if 좁 else 주 / 2.0              # 위쪽 날짜 글(좁은 판은 「종가」 줄까지)이 차지하는 아래쪽
                위칸 = (min(a, b) + 아래끝 + 2, max(a, b) - 주 / 2.0 - 2)      # 두 날짜 글 사이의 빈칸
                if 동안 and 위칸[0] <= y동 - 보 / 2.0 and (a + b) / 2.0 + 주 / 2.0 <= 위칸[1]:
                    s.append(_글(트x - 10, y동, 동안 + ",", 보, "viz-note-flag", "end", m화))
        # 움직이는 표시 — 첫 종가 자리에 서서 차례로 옮겨 간다(정적 그림 = 마지막 종가 자리)
        mm = [("점0", "opacity", 0, 1)] + [("옮김:%d" % j, "cy", ys[j - 1], ys[j]) for j in range(1, len(종점))]
        s.append('<circle cx="%.1f" cy="%.1f" r="5.5" class="vz-dot-flag"%s><title>%s %s</title></circle>' % (
            트x, ys[-1], _m(*mm), _e(종점[-1]["이름"]), _e(종점[-1]["값글"])))
        # 날짜 글 — 지난 종가는 흐린 글(내림:j+1 에서 진한 글과 바뀐다), 마지막 종가는 진한 글
        for p in 종점:
            j = p["j"]
            날 = re.search(r"(\d{1,2}월 \d{1,2}일)", p["이름"])
            말 = (날.group(1) if 날 else "종가") + ("" if 좁 else " 종가")
            키 = "점0" if j == 0 else "글:%d" % j
            if j < len(종점) - 1:
                s.append(_글(트x - 12, p["y"], 말, 주, "viz-label viz-strong", "end", _m((키, "opacity", 0, 1), ("내림:%d" % (j + 1), "opacity", 1, 0)),
                            ' opacity="0" aria-hidden="true"'))
                s.append(_글(트x - 12, p["y"], 말, 주, "viz-tick", "end", _m(("내림:%d" % (j + 1), "opacity", 0, 1))))
            else:
                s.append(_글(트x - 12, p["y"], 말, 주, "viz-label viz-strong", "end", _m((키, "opacity", 0, 1))))
            if 좁:
                s.append(_글(트x - 12, p["y"] + 주 + 6, "종가", 보, "viz-tick", "end", _m((키, "opacity", 0, 1))))
                글끝 = max(글끝, p["y"] + 주 + 6 + 보 / 2)
    H = max(t + ph + 30, 글끝 + 보 / 2 + 10) if 빈있음 else max(t + ph + 30, 글끝 + 6)
    if 빈있음:                                              # 범례 — 점 종류의 뜻
        y = H - 4
        s.append('<circle cx="%.1f" cy="%.1f" r="4.5" class="vz-dot-ctx"/>' % (8, y))
        s.append(_글(18, y, "정상 수준만 바꾼 값", 보, "viz-tick"))
        if 좁:
            y += 보 + 9
            x2 = 8.0
        else:
            x2 = 18 + _폭("정상 수준만 바꾼 값", 보) * 1.04 + 22
        s.append('<circle cx="%.1f" cy="%.1f" r="4.5" class="vz-dot-hollow"/>' % (x2, y))
        s.append(_글(x2 + 10, y, "모든 가정을 바꾼 값", 보, "viz-tick"))
        H = y + 14
    return ('<svg class="viz viz-%s vz-ruler" viewBox="0 0 %d %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">' % (
        "wide" if not 좁 else "narrow", W, int(round(H)), _e(제목 or "그림")) + "".join(s) + "</svg>")


# ══════════════════════════════════════════════════════════════════ 토네이도 — 가정 하나씩 근거 범위 끝으로(정적 — v4e 모션 폐기)

def _토라벨(d, 기):
    """줄 하나의 끝 라벨을 기준선의 왼쪽 · 오른쪽으로 → {"왼": (값 · 변화율 글 · 금액 글), "오": (…)} — 빈 쪽은 (None, "", "").
    표의 칸(낮은 쪽 · 높은 쪽)이 아니라 값의 자리로 가른다(레터 v27 P5 — 시나리오 쪽으로 붙인 표는 비관 값이 기준 위에 설 수 있다).
    한쪽에 두 끝이 서면 먼 끝의 라벨만 싣는다(가까운 끝은 막대 안 — 두 값은 표에 있다). 변화율 칸의 표지 괄호(「(비관 값)」)는 그림 라벨에서 뗀다
    (라벨 폭이 그림 여백을 정한다 — 긴 라벨 하나가 모든 줄의 막대를 좁힌다)."""
    import re                                                 # noqa: PLC0415
    낸 = {}
    for 쪽, 든 in (("왼", lambda v: v < 기), ("오", lambda v: v >= 기)):
        끝 = [(d[k], re.sub(r"\([^()]*\)\s*$", "", d.get(k + "율") or "").strip(), _뗀(d[k + "글"], " 원")) for k in ("낮", "높")
             if d[k] is not None and 든(d[k])]
        낸[쪽] = max(끝, key=lambda t: abs(t[0] - 기)) if 끝 else (None, "", "")
    return 낸


def 토네이도(표들, 제목="", 진행=None, 판="넓은"):
    """가정 하나씩(다른 가정은 그대로) 근거 범위의 끝으로 옮겼을 때의 주당가치 — 정적(리뷰 D: 「하나씩 · 나머지 고정」 은 형식이 이미 말한다).
    막대 하나의 색(--accent) · 방향은 자리로 읽는다. 막대 끝 바깥에 변화율(주 — 표의 「변화율」 칸, 장부 키로 셈한 글)과 금액(보조 — 괄호).
    가로축 눈금(그리드) · 기준선(--ink) 머리 「기준 …」 · 한쪽만 있는 줄은 빈 쪽에 「높이는 경우 해당 없음」. 넓은 판은 이름 열 왼쪽,
    좁은 판은 이름을 막대 위 한 줄로."""
    기, 기글, 줄 = G.토네이도줄(표들)
    if 기 is None or not 줄:
        return ""
    c = 판치수[판]
    W, 주, 보, 축 = c["W"], c["주"], c["보"], c["축"]
    좁 = 판 == "좁은"
    단위 = _공통단위([d["낮글"] for d in 줄 if d["낮"] is not None] + [d["높글"] for d in 줄 if d["높"] is not None] + [기글])
    모든 = [기] + [v for d in 줄 for v in (d["낮"], d["높"]) if v is not None]
    눈 = _눈범위(min(모든), max(모든))
    lo, hi = 눈[0], 눈[-1]
    라들 = [_토라벨(d, 기) for d in 줄]
    라벨폭 = max([_폭(율, 주) for r in 라들 for v, 율, _g in r.values() if v is not None] + [_폭("(%s)" % g, 보) for r in 라들 for v, _율, g in r.values() if v is not None]
              + [40.0]) * 1.06 + 8
    이름폭 = 0.0 if 좁 else 222.0
    px0 = (4 + 이름폭 + 12 if not 좁 else 4) + 라벨폭
    px1 = W - 4 - 라벨폭
    # 1.1.4 — 한쪽만 있는 줄의 「… 해당 없음」 은 기준선 옆(빈 쪽)에 선다. 기준선이 그림 끝에 붙으면 그 글이 그림 밖으로 넘친다(⑬) —
    # 그 쪽 끝만 글 폭만큼 안으로 당긴다(양쪽 여백을 통째로 넓히면 눈금이 겹친다)
    r기 = (기 - lo) / ((hi - lo) or 1.0)
    w없음 = _폭("높이는 경우 해당 없음", 보) * 1.04
    if any(r["오"][0] is None for r in 라들) and r기 > 0:
        px1 = min(px1, px0 + (W - 4 - 8 - w없음 - px0) / r기)
    if any(r["왼"][0] is None for r in 라들) and r기 < 1:
        왼 = (4 + 이름폭 + 12) if not 좁 else 4
        px0 = max(px0, (왼 + 8 + w없음 - px1 * r기) / (1 - r기))

    def X(v):
        return px0 + (px1 - px0) * (v - lo) / ((hi - lo) or 1.0)
    s = []
    머 = "변화율은 기준 대비%s" % ((", 괄호 안은 주당가치(%s)" % 단위) if 단위 else "")
    s.append(_글(4, 12, 머, 보, "viz-tick"))
    xb = X(기)
    기말 = "기준 %s" % 기글
    w기 = _폭(기말, 주) * 1.04
    y = 34.0
    s.append(_글(min(max(xb, px0 + w기 / 2), W - 4 - w기 / 2), y, 기말, 주, "viz-label viz-strong", "middle"))
    y += 14
    위 = y
    줄들 = []
    for d in 줄:
        if 좁:
            이줄 = [d["이름"]]
            범 = [d["범위"]] if d["범위"] and d["범위"] not in ("—", "-") else []
            이줄 = _접기(d["이름"], W - 8, 주)
            범 = _접기(d["범위"], W - 8, 보) if 범 else []
            h = (주 + 4) * len(이줄) + (보 + 4) * len(범) + 6 + 2 * (주 + 4) + 8
        else:
            이줄 = _접기(d["이름"], 이름폭, 주)
            범 = _접기(d["범위"], 이름폭, 보) if d["범위"] and d["범위"] not in ("—", "-") else []
            h = max((주 + 4) * len(이줄) + (보 + 4) * len(범) + 10, 2 * (주 + 4) + 14)
        줄들.append((d, 이줄, 범, h))
    아래 = 위 + sum(h for *_r, h in 줄들)
    for g in 눈:                                            # 눈금 — 그리드와 아래 눈금 글
        s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="viz-grid"/>' % (X(g), X(g), 위 - 4, 아래))
        s.append(_글(X(g), 아래 + 12, _눈금글(g, 단위, (눈[1] - 눈[0]) if len(눈) > 1 else None), 축, "viz-tick", "middle"))
    if not 좁:
        s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="vz-base"/>' % (xb, xb, 위 - 8, 아래))
    else:
        s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="vz-base"/>' % (xb, xb, 위 - 8, 위))
    for d, 이줄, 범, h in 줄들:
        if 좁:
            yy = y + 4 + 주 / 2
            for g in 이줄:
                s.append(_글(4, yy, g, 주, "viz-label"))
                yy += 주 + 4
            for g in 범:
                s.append(_글(4, yy - 1, g, 보, "viz-tick"))
                yy += 보 + 4
            가 = yy + 2 + 주 / 2 + 4
            s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="vz-base"/>' % (xb, xb, 가 - 주 - 4, 가 + 주 + 4))
        else:
            블높 = (주 + 4) * len(이줄) + (보 + 4) * len(범)
            yy = y + (h - 블높) / 2.0 + 주 / 2
            for g in 이줄:
                s.append(_글(4, yy, g, 주, "viz-label"))
                yy += 주 + 4
            for g in 범:
                s.append(_글(4, yy - 1, g, 보, "viz-tick"))
                yy += 보 + 4
            가 = y + h / 2.0
        값들 = [v for v in (d["낮"], d["높"]) if v is not None]
        xa, xz = X(min(값들 + [기])), X(max(값들 + [기]))      # 레터 v27 P5 — 막대는 기준선에서 먼 끝까지(두 끝이 기준의 같은 쪽이어도)
        s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="14" rx="2" class="vz-step"><title>%s %s ~ %s</title></rect>' % (
            xa, 가 - 7, max(xz - xa, 1.5), _e(d["이름"]), _e(d["낮글"]), _e(d["높글"])))
        for 쪽, (v, 율, 글) in _토라벨(d, 기).items():
            앵 = "end" if 쪽 == "왼" else "start"
            if v is None:
                말 = "%s는 경우 해당 없음" % ("낮추" if 쪽 == "왼" else "높이")
                s.append(_글(xb + (8 if 쪽 == "오" else -8), 가, 말, 보, "viz-tick", 앵))
                continue
            xv = X(v) - 6 if 쪽 == "왼" else X(v) + 6
            if 율:
                s.append(_글(xv, 가 - 주 / 2 - 1, 율, 주, "viz-label viz-value", 앵))
                s.append(_글(xv, 가 + 보 / 2 + 2, "(%s)" % 글, 보, "viz-tick viz-value", 앵))
            else:
                s.append(_글(xv, 가, 글, 주, "viz-label viz-value", 앵))
        y += h
    H = 아래 + 22
    return ('<svg class="viz viz-%s vz-tornado" viewBox="0 0 %d %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">' % (
        "wide" if not 좁 else "narrow", W, int(round(H)), _e(제목 or "그림")) + "".join(s) + "</svg>")


def _눈범위(lo, hi, 칸수=5):
    """lo~hi 를 덮는 깔끔한 눈금(0 을 억지로 품지 않는다) — 100만~200만 · 20만 간격 꼴."""
    import math
    폭 = (hi - lo) or abs(hi) or 1.0
    날 = 폭 / 칸수
    자 = 10 ** math.floor(math.log10(날))
    칸 = next(자 * k for k in (1, 2, 2.5, 5, 10) if 자 * k >= 날 - 1e-12)
    a = math.floor(lo / 칸 + 1e-9) * 칸
    b = math.ceil(hi / 칸 - 1e-9) * 칸
    return [round(a + 칸 * i, 6) for i in range(int(round((b - a) / 칸)) + 1)]


def _눈금글(v, 단위, 칸=None):
    """눈금 글 — 칸(눈금 간격)이 단위보다 작으면 소수 자리를 늘려 이웃 눈금이 같은 글(「2만」 · 「2만」)이 되지 않게 한다(1.1.4 · 게이트 ⑬ 라벨 겹침)."""
    import math
    나눔, 꼬리 = {"만 원": (1e4, "만"), "조 원": (1e12, "조")}.get(단위, (1.0, ""))
    자리 = 0
    if 칸 and 칸 > 0:
        자리 = max(0, min(2, -int(math.floor(math.log10(칸 / 나눔) + 1e-9))))
    return ("{:,.%df}" % 자리).format(v / 나눔) + 꼬리


그림들 = {"가치": 가치, "길": 길, "자": 자, "토네이도": 토네이도}

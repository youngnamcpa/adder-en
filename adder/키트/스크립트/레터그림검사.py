# -*- coding: utf-8 -*-
"""레터그림검사 — 그림이 「읽히는가」 를 잰다 (v4e — 2026-10-16 디자이너 리뷰 6순위: 숫자가 맞는지는 잡았지만 읽히는지는 못 잡았다).

브라우저 없이 그림 글(SVG)과 페이지 CSS(`레터HTML.머리` · `레터그림.CSS`)를 읽어 셈한다 — 게이트(⑬)와 꼴 시험이 같은 함수를 쓴다.
  ① 글자 크기 — 렌더 크기 = font-size × (표시 폭 ÷ viewBox 폭) ≥ 12px. 표시 폭: 넓은 판(viz-wide) 560px(데스크톱 그림 상자),
     좁은 판(viz-narrow)과 한 판 그림은 358px(390px 휴대폰 화면의 그림 폭 — 가장 좁은 자리에서 잰다). v4f — 그보다 좁은 화면(375px 등)에서는
     그림이 본문 여백 쪽으로 나와 358px 를 지킨다(`레터그림.CSS` — 화면 끝과 4px, 360px 화면은 352px)
  ② 라벨 겹침 — 글 상자끼리 겹침 0, 그림(viewBox) 밖으로 나간 글 0. 상자 = 어림 폭(`레터그림._폭` — 한글 1em · 숫자 0.58em) × 글자 높이
     (1em, 가운데 맞춤이면 위아래 반씩). 불투명도 0 인 글(움직임용으로 숨긴 짝 글)은 뺀다
  ③ 대비(WCAG 2.x) — 마크는 채움 또는 테두리가 바탕과 3:1(1.4.11 그래픽), 글은 4.5:1(1.4.3) — 밝은 · 어두운 화면 둘 다. 투명도는 바탕에 섞어 잰다.
     글의 바탕은 그 글 가운데를 덮는 앞선 채움 도형(없으면 종이색). 장식 · 길잡이는 뺀다: 눈금선 · 지시선 · 축 눈금 · 띠 · 표지 · 마우스 자리 ·
     잘라 보이는 사각형(clipPath) · 민감도 격자의 칸(값을 칸 안 글이 같이 말한다 — 글 대비는 칸 색 위에서 잰다)
  ④ 가려진 점 — 끝 그림(정적 그림)에서 점(원) 넓이의 절반 넘게를 뒤에 그린 불투명한 원 · 사각형이 덮으면 가린 것(리뷰 C 의 134만 원 점)
  ⑤ 라벨과 마크 겹침(v4f — 리뷰 6순위 (2)의 뒷부분) — 글 상자가 데이터 마크(막대 · 면 · 점 · 데이터 선 · 기준선)를 덮으면 겹침이다.
     바탕색 테두리(halo)가 글을 읽히게 해도 그 밑의 막대 · 점 · 선은 글 모양으로 패이고(리뷰 A 「유령 위 라벨이 막대를 갉아먹는다」),
     값 글이 남의 점 · 기준선 위에 서면 둘이 한 값처럼 읽힌다(모션 리뷰 M1 「22 점 라벨이 기준 가로선과 같은 높이」).
     장식(눈금선 · 지시선 · 축 눈금 · 띠 · 표지 · 마우스 자리 · 잘라 보이는 사각형 · 격자 칸)과 축 · 주가 트랙은 뺀다(글이 걸쳐도 데이터를
     가리지 않는다). 닿기만 한 것은 겹침이 아니다 — 글 상자를 면 · 점은 1, 선은 2 그림 단위 안쪽으로 줄여 잰다.
     `그림검사(…, 마크=True)` · `문서검사(…, 마크=True)` 로 켠다(기본은 꺼짐 — 게이트 ⑬ 배선은 따로)
2026-10-25 R5 — 절 규칙(`절검사` — 변수 절마다 그림 · 본편 그림마다 출처 줄 · 단위)과 상황 규칙(`그림규칙.json`)은 편집 등급이다(막지 않는다 — 편집 대장:
`python 스크립트/레터그림검사.py 초안.md --가정 가정.json -o 편집대장.json`).
"""
from __future__ import annotations

import html
import re

import 레터그림 as G

표시폭 = {"넓은": 560.0, "좁은": 358.0, "한판": 358.0}
최소글 = 12.0
장식 = {"viz-grid", "viz-hit", "viz-band", "vz-band", "viz-mark", "viz-leader", "viz-axis-tick", "viz-ring", "vz-hi", "vz-lo"}
점갈 = re.compile(r"(dot|trace)")


# ══════════════════════════════════════════════════════════════════ CSS 읽기

def _미디어걷기(css, 남길=()):
    """@media 블록을 걷는다(괄호 짝을 센다). 남길 = 그 블록의 안쪽을 남길 조건 글(없으면 다 걷는다)."""
    낸, i = [], 0
    while True:
        j = css.find("@media", i)
        if j < 0:
            낸.append(css[i:])
            break
        낸.append(css[i:j])
        k = css.find("{", j)
        깊, m = 1, k + 1
        while 깊 and m < len(css):
            깊 += {"{": 1, "}": -1}.get(css[m], 0)
            m += 1
        if any(x in css[j:k] for x in 남길):
            낸.append(css[k + 1:m - 1])
        i = m
    return "".join(낸)


def _선언(몸):
    d = {}
    for x in 몸.split(";"):
        if ":" in x:
            a, b = x.split(":", 1)
            d[a.strip()] = b.strip()
    return d


_캐시 = {}


def 페이지CSS():
    """→ (토큰 {"밝은": {...}, "어두운": {...}}, 규칙 [(클래스 집합 또는 "text", 선언)])."""
    if "c" in _캐시:
        return _캐시["c"]
    import 레터HTML                                         # noqa: PLC0415
    css = re.sub(r"/\*.*?\*/", "", 레터HTML.머리.split("<style>", 1)[1].split("</style>", 1)[0] + G.CSS, flags=re.S)
    밖 = _미디어걷기(css)
    밝은, 어두운 = {}, {}
    for sel, 몸 in re.findall(r"([^{}]+)\{([^{}]*)\}", 밖):
        for s in [x.strip() for x in sel.split(",")]:
            if s == ":root":
                밝은.update({k: v for k, v in _선언(몸).items() if k.startswith("--")})
            elif s == ':root[data-theme="dark"]':
                어두운.update({k: v for k, v in _선언(몸).items() if k.startswith("--")})
    어 = dict(밝은)
    어.update(어두운)
    규칙 = []
    for sel, 몸 in re.findall(r"([^{}]+)\{([^{}]*)\}", 밖):
        for s in [x.strip() for x in sel.split(",")]:
            if s == ".viz text":
                규칙.append(("text", _선언(몸)))
                continue
            m = re.match(r"^\.viz\s+((?:\.[\w-]+)+)$", s)
            if m:
                규칙.append((frozenset(m.group(1).strip(".").split(".")), _선언(몸)))
    _캐시["c"] = ({"밝은": 밝은, "어두운": 어}, 규칙)
    return _캐시["c"]


def _색(v, 토큰, 깊이=0):
    """CSS 값 → '#RRGGBB' 또는 None(none · transparent)."""
    if v is None:
        return None
    v = v.strip()
    m = re.match(r"^var\((--[\w-]+)\)$", v)
    if m:
        return _색(토큰.get(m.group(1)), 토큰, 깊이 + 1) if 깊이 < 8 else None
    if v in ("none", "transparent", ""):
        return None
    if re.match(r"^#[0-9a-fA-F]{6}$", v):
        return v.upper()
    if re.match(r"^#[0-9a-fA-F]{3}$", v):
        return "#" + "".join(c * 2 for c in v[1:]).upper()
    return None


def _수(v, 토큰, 기본=None):
    if v is None:
        return 기본
    m = re.match(r"^var\((--[\w-]+)\)$", v.strip())
    if m:
        return _수(토큰.get(m.group(1)), 토큰, 기본)
    m = re.match(r"^(-?[\d.]+)(px)?$", v.strip())
    return float(m.group(1)) if m else 기본


def _밝기(h):
    r, g, b = [int(h[i:i + 2], 16) / 255.0 for i in (1, 3, 5)]
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def 대비(a, b):
    x, y = sorted((_밝기(a), _밝기(b)))
    return (y + 0.05) / (x + 0.05)


def _섞기(앞, 뒤, 알파):
    if 알파 >= 1:
        return 앞
    p = [int(앞[i:i + 2], 16) for i in (1, 3, 5)]
    q = [int(뒤[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02X%02X%02X" % tuple(int(round(a * 알파 + b * (1 - 알파))) for a, b in zip(p, q))


# ══════════════════════════════════════════════════════════════════ SVG 읽기

_요소 = re.compile(r"<(/?)(svg|text|rect|circle|line|polyline|path|polygon|clipPath|g)\b([^>]*?)(/?)>(?:([^<]*)(?:<title>[^<]*</title>)?</text>)?", re.S)
_속 = re.compile(r'([\w:-]+)="([^"]*)"')


def 요소들(svg):
    """SVG 글 → [{"꼴", "속", "글", "clip"}] (그린 차례)."""
    낸, clip = [], 0
    for m in _요소.finditer(svg):
        닫, 이름, 속, 홀, 글 = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
        if 이름 == "clipPath":
            clip += -1 if 닫 else (0 if 홀 else 1)
            continue
        if 닫 or 이름 in ("g",):
            continue
        d = {k: html.unescape(v) for k, v in _속.findall(속)}
        낸.append({"꼴": 이름, "속": d, "글": html.unescape(글 or ""), "clip": clip > 0})
    return 낸


def _꼴(el, 토큰, 규칙):
    """요소의 계산된 꼴 → {fill, stroke, stroke-width, opacity, font-size, fill-opacity}."""
    갈 = set(el["속"].get("class", "").split())
    p = {}
    for 고른, 선 in 규칙:
        if (고른 == "text" and el["꼴"] == "text") or (고른 != "text" and 고른 <= 갈):
            p.update(선)
    for k in ("fill", "stroke", "stroke-width", "opacity", "fill-opacity"):
        if k in el["속"] and k not in p:
            p[k] = el["속"][k]
    p.update(_선언(el["속"].get("style", "")))
    알 = _수(p.get("opacity"), 토큰, 1.0) * (_수(el["속"].get("opacity"), 토큰, 1.0) if "opacity" in el["속"] else 1.0)
    return {"fill": _색(p.get("fill", "#000000" if el["꼴"] != "line" else "none"), 토큰), "stroke": _색(p.get("stroke"), 토큰),
            "sw": _수(p.get("stroke-width"), 토큰, 1.0), "알": 알, "채움알": _수(p.get("fill-opacity"), 토큰, 1.0),
            "크기": _수(p.get("font-size"), 토큰, 16.0), "갈": 갈}


def _f(d, k, 기본=0.0):
    try:
        return float(d.get(k, 기본))
    except (TypeError, ValueError):
        return 기본


def _글상자(el, 크기):
    x, y = _f(el["속"], "x"), _f(el["속"], "y")
    w = G._폭(el["글"], 크기)
    앵 = el["속"].get("text-anchor", "start")
    x0 = x - (w / 2.0 if 앵 == "middle" else (w if 앵 == "end" else 0.0))
    if el["속"].get("dominant-baseline") == "middle":
        y0, y1 = y - 크기 / 2.0, y + 크기 / 2.0
    else:
        y0, y1 = y - 0.8 * 크기, y + 0.2 * 크기
    return (x0, y0, x0 + w, y1)


def _덮는가(el, px, py):
    a = el["속"]
    if el["꼴"] == "circle":
        return (px - _f(a, "cx")) ** 2 + (py - _f(a, "cy")) ** 2 <= _f(a, "r") ** 2
    if el["꼴"] == "rect":
        x, y, w, h = _f(a, "x"), _f(a, "y"), _f(a, "width"), _f(a, "height")
        return x <= px <= x + w and y <= py <= y + h
    return False


비마크 = {"viz-axis", "viz-zero", "viz-axis-tick", "vz-track"}          # ⑤ — 축 · 주가 트랙(글이 걸쳐도 데이터를 가리지 않는다)
틈면, 틈선 = 1.0, 2.0                                                   # ⑤ — 글 상자를 안쪽으로 줄이는 폭(닿기만 한 것은 겹침이 아니다)


def 마크모양(el, k):
    """마크 요소의 모양 → [("면", 상자) · ("점", (cx, cy, r)) · ("선", (x1, y1, x2, y2))] — 채운 사각형은 면, 테두리만 있으면 네 변,
    선 · 꺾은선 · 다각형은 선분들(테두리 색이 없으면 없음)."""
    a, f = el["속"], _f
    if el["꼴"] == "rect":
        x, y, w, h = f(a, "x"), f(a, "y"), f(a, "width"), f(a, "height")
        if k["fill"] and k["알"] * k["채움알"] > 0.05:
            return [("면", (x, y, x + w, y + h))]
        if k["stroke"]:
            return [("선", s) for s in ((x, y, x + w, y), (x + w, y, x + w, y + h), (x, y + h, x + w, y + h), (x, y, x, y + h))]
        return []
    if el["꼴"] == "circle":
        return [("점", (f(a, "cx"), f(a, "cy"), f(a, "r")))]
    if el["꼴"] == "line":
        return [("선", (f(a, "x1"), f(a, "y1"), f(a, "x2"), f(a, "y2")))] if k["stroke"] else []
    if el["꼴"] in ("polyline", "polygon"):
        pts = []
        for p in a.get("points", "").split():
            try:
                pts.append(tuple(float(v) for v in p.split(",")[:2]))
            except ValueError:
                continue
        if el["꼴"] == "polygon" and pts:
            pts.append(pts[0])
        return [("선", (p[0], p[1], q[0], q[1])) for p, q in zip(pts, pts[1:]) if len(p) == 2 and len(q) == 2] if k["stroke"] else []
    return []


def 마크겹침(svg):
    """⑤ 글 상자가 데이터 마크를 덮는 자리 → [("⑤", 내용)] (끝 그림 · 밝은 화면의 꼴로 잰다 — 자리는 테마와 무관하다)."""
    토큰들, 규칙 = 페이지CSS()
    토큰 = 토큰들["밝은"]
    글, 마크 = [], []
    for el in 요소들(svg):
        if el["clip"]:
            continue
        k = _꼴(el, 토큰, 규칙)
        if k["알"] <= 0.05:
            continue
        if el["꼴"] == "text":
            if el["글"].strip():
                글.append((_글상자(el, k["크기"]), el["글"]))
            continue
        if k["갈"] & (장식 | 비마크) or "viz-hit" in k["갈"]:
            continue
        이름 = " ".join(sorted(k["갈"])) or el["꼴"]
        for 종, g in 마크모양(el, k):
            마크.append((종, g, 이름))
    낸 = []
    for b, t in 글:
        for 종, g, 이름 in 마크:
            if G._마크덮나(b, [(종, g)], 틈면, 틈선):          # 그림이 글 자리를 고를 때와 같은 잣대(`레터그림._마크덮나`)
                낸.append(("⑤", "라벨이 %s 덮음 「%s」 — %s" % ({"면": "막대 · 면을", "점": "점을"}.get(종, "선을"), t[:16], 이름)))
    본, 걸 = set(), []
    for x in 낸:
        if x not in 본:
            본.add(x)
            걸.append(x)
    return 걸


def 그림검사(svg, 판=None, 마크=False):
    """그림 하나 → [(번호, 내용)] — 번호 ①~④(마크 = True 면 ⑤ 도). 판 = 넓은 · 좁은 · 한판(없으면 SVG 의 class 로)."""
    토큰들, 규칙 = 페이지CSS()
    m = re.search(r'<svg[^>]*class="([^"]*)"[^>]*viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    if not m:
        return []
    갈 = m.group(1).split()
    vbw, vbh = float(m.group(2)), float(m.group(3))
    판 = 판 or ("넓은" if "viz-wide" in 갈 else ("좁은" if "viz-narrow" in 갈 else "한판"))
    배율 = 표시폭[판] / vbw
    els = 요소들(svg)
    낸 = []
    글상자 = []
    for 테마, 토큰 in 토큰들.items():
        종이 = _색("var(--paper)", 토큰)
        for i, el in enumerate(els):
            if el["clip"]:
                continue
            k = _꼴(el, 토큰, 규칙)
            if el["꼴"] == "text":
                if k["알"] <= 0.05 or not el["글"].strip():
                    continue
                if 테마 == "밝은":
                    렌 = k["크기"] * 배율
                    if 렌 < 최소글 - 0.05:
                        낸.append(("①", "글자 %.1fpx(표시 폭 %.0fpx) 「%s」" % (렌, 표시폭[판], el["글"][:24])))
                    글상자.append((_글상자(el, k["크기"]), el["글"]))
                바탕 = 종이
                상 = _글상자(el, k["크기"])
                cx, cy = (상[0] + 상[2]) / 2.0, (상[1] + 상[3]) / 2.0
                for q in reversed(els[:i]):
                    if q["꼴"] in ("rect", "circle") and not q["clip"] and _덮는가(q, cx, cy):
                        kq = _꼴(q, 토큰, 규칙)
                        if kq["fill"] and kq["알"] * kq["채움알"] > 0.05 and "viz-hit" not in kq["갈"]:
                            바탕 = _섞기(kq["fill"], 종이, kq["알"] * kq["채움알"])
                            break
                색 = k["fill"] or "#000000"
                c = 대비(_섞기(색, 바탕, k["알"]), 바탕)
                if c < 4.5 - 0.005:
                    낸.append(("③", "글 대비 %.2f(%s 화면) 「%s」 %s on %s" % (c, 테마, el["글"][:20], 색, 바탕)))
                continue
            if el["꼴"] not in ("rect", "circle", "line", "polyline", "path", "polygon") or k["갈"] & 장식 or k["알"] <= 0.05:
                continue
            if "viz-hit" in k["갈"]:
                continue
            후보 = []
            if k["fill"] and el["꼴"] not in ("line",):
                후보.append(대비(_섞기(k["fill"], 종이, k["알"] * k["채움알"]), 종이))
            if k["stroke"] and k["sw"] >= 1.0:
                후보.append(대비(_섞기(k["stroke"], 종이, k["알"]), 종이))
            if 후보 and max(후보) < 3.0 - 0.005:
                낸.append(("③", "마크 대비 %.2f(%s 화면) <%s class=\"%s\">" % (max(후보), 테마, el["꼴"], " ".join(sorted(k["갈"])))))
    for 상, 글 in 글상자:                                     # ② 그림 밖
        if 상[0] < -1.0 or 상[2] > vbw + 1.0 or 상[1] < -1.0 or 상[3] > vbh + 1.0:
            낸.append(("②", "라벨이 그림 밖 「%s」" % 글[:16]))
    for a in range(len(글상자)):                             # ② 겹침
        for b in range(a + 1, len(글상자)):
            p, q = 글상자[a][0], 글상자[b][0]
            if p[0] + 0.5 < q[2] and q[0] + 0.5 < p[2] and p[1] + 0.5 < q[3] and q[1] + 0.5 < p[3]:
                낸.append(("②", "라벨 겹침 「%s」 · 「%s」" % (글상자[a][1][:16], 글상자[b][1][:16])))
    토큰 = 토큰들["밝은"]
    for i, el in enumerate(els):                             # ④ 가려진 점
        if el["꼴"] != "circle" or el["clip"]:
            continue
        k = _꼴(el, 토큰, 규칙)
        if not 점갈.search(" ".join(k["갈"])) or k["알"] <= 0.05:
            continue
        cx, cy, r = _f(el["속"], "cx"), _f(el["속"], "cy"), _f(el["속"], "r")
        if r <= 0:
            continue
        위 = [q for q in els[i + 1:] if q["꼴"] in ("circle", "rect") and not q["clip"]]
        위 = [q for q in 위 if (lambda kq: kq["fill"] and kq["알"] >= 0.5 and "viz-hit" not in kq["갈"] and not (kq["갈"] & 장식))(_꼴(q, 토큰, 규칙))]
        if not 위:
            continue
        표, 덮 = 0, 0
        for a in range(9):
            for b in range(9):
                px, py = cx - r + (a + 0.5) * 2 * r / 9, cy - r + (b + 0.5) * 2 * r / 9
                if (px - cx) ** 2 + (py - cy) ** 2 > r * r:
                    continue
                표 += 1
                if any(_덮는가(q, px, py) for q in 위):
                    덮 += 1
        if 표 and 덮 / float(표) > 0.5:
            t = re.search(r"<circle[^>]*cx=\"%s\"[^>]*cy=\"%s\"[^>]*>(?:<title>([^<]*)</title>)?" % (re.escape(el["속"].get("cx", "")), re.escape(el["속"].get("cy", ""))), svg)
            낸.append(("④", "가려진 점 %.0f%% 「%s」" % (100.0 * 덮 / 표, (t.group(1) if t and t.group(1) else "%s,%s" % (cx, cy))[:24])))
    if 마크:
        낸 += 마크겹침(svg)
    본, 걸 = set(), []
    for x in 낸:
        if x not in 본:
            본.add(x)
            걸.append(x)
    return 걸


# ══════════════════════════════════════════════════════════════════ 상황별 그림 규칙(2026-10-23 — `그림규칙.json`) · 절 규칙(2026-10-25 R5)
# 2026-10-25 레터 재구성 R5(연구/레터재구성_20261025/조문_그림.md) — 규칙을 상황에서 절로 넓히고 알림을 편집 등급으로 올렸다.
#   ① 변수 절(매출 · 영업비용 · 인건비 · 설비투자 · 운전자본 · 법인세와 FCFF · 할인율 · Terminal Value · 시나리오 · 민감도 · Reverse DCF)마다 그림 하나 이상
#   ② 그 밖의 본편 절은 그림 또는 표 하나 이상(이해관계와 한계 · 모델 점검 · 모델 파일은 글의 절이라 뺀다)
#   ③ 본편 그림마다 출처 줄(굵은 제목 줄의 「출처:」 — 그 그림 숫자의 장부 키에서 지은 문장) · 단위(제목 괄호 · 줄 이름 · 열 머리 · 칸 글 가운데 한 곳)
#   ④ 상황 규칙 — 구조 · 재료 · 글이 그 상황이면 그 절에 그 그림(`그림규칙.json` 「규칙」 — 그림이 둘 이상이면 그 가운데 하나)
# 등급은 「편집」 — 초안 · 게이트를 막지 않고 편집 대장(`python 스크립트/레터그림검사.py 초안.md --가정 가정.json -o 편집대장.json`)에 오른다.
# 글자 · 겹침 · 대비 · 가림(①~⑤ 그림검사)은 그대로 게이트 ⑬ 의 오류다.

def 규칙읽기():
    import io as _io                                         # noqa: PLC0415
    import json as _json                                     # noqa: PLC0415
    import os as _os                                         # noqa: PLC0415
    p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "그림규칙.json")
    return _json.load(_io.open(p, encoding="utf-8"))


_절말 = {"결론": "결론", "Narrative": "Narrative", "업황과 경쟁": "업황", "추정 구조": "구조", "매출 추정": "매출", "영업비용 추정": "비용", "인건비 추정": "인건비",
       "설비투자와 감가상각": "재투자", "운전자본 추정": "운전자본", "법인세와 FCFF": "세금", "할인율": "할인율", "Terminal Value": "영구",
       "가치 브리지": "주주가치", "시나리오 분석": "시나리오", "민감도 분석": "민감도", "Reverse DCF": "역산", "모니터링": "신호",
       "평가자의 이해관계와 평가의 한계": "자리", "모델 점검": "점검", "평가 모델 파일": "파일", "지난 평가와의 차이": "다리"}
_머리 = re.compile(r"^##\s+(\d+)\.\s+(.+?)\s*$")


def 본편절들(글):
    """본편(「# 본편」 아래 · 「# 부록」 앞)의 절 → [{"번호", "제목", "키", "줄들"}]. 「# 본편」 이 없으면 빈 목록(옛 짜임 · 조각 글)."""
    줄 = (글 or "").split("\n")
    처 = next((i for i, t in enumerate(줄) if t.strip() == "# 본편"), None)
    if 처 is None:
        return []
    끝 = next((i for i in range(처 + 1, len(줄)) if 줄[i].strip().startswith("# 부록") or 줄[i].strip().startswith("# Part II")), len(줄))
    낸 = []
    for i in range(처 + 1, 끝):
        m = _머리.match(줄[i].strip())
        if m:
            앞 = m.group(2).split(" : ")[0].strip()
            키 = _절말.get(앞) or next((v for k, v in _절말.items() if 앞.startswith(k)), None)
            낸.append({"번호": int(m.group(1)), "제목": m.group(2), "키": 키, "줄들": []})
        elif 낸:
            낸[-1]["줄들"].append(줄[i])
    return 낸


def _그림셈(줄들):
    """절 줄들 → (그림 블록 [(종류, 제목 줄, 표들)], 그림 밖의 표 수)."""
    import 레터모션                                         # noqa: PLC0415
    글 = "\n".join(줄들)
    블 = [(종, 제, 표) for 종, _모, 제, 표 in 레터모션._블록들(글)]
    표수, 안 = 0, False
    i = 0
    while i < len(줄들):
        t = 줄들[i].strip()
        if t.startswith("<!-- 그림:"):
            안 = True
        elif t.startswith("|") and i + 1 < len(줄들) and re.match(r"^\|[\s\-:|]+\|$", 줄들[i + 1].strip()):
            if not 안:
                표수 += 1
            while i < len(줄들) and 줄들[i].strip().startswith("|"):
                i += 1
            continue
        elif t and not t.startswith("|") and not t.startswith("**그림") and 안 and not t.startswith("<!--"):
            안 = False
        i += 1
    return 블, 표수


_단위말 = re.compile(r"(?:%p|%|(?<![가-힣])일(?![가-힣])|(?<![가-힣])명(?![가-힣])|(?<![가-힣])배(?![가-힣])|(?<![가-힣])년(?![가-힣])|원|달러|엔|유로|천 장|= ?100)")
_값단위 = re.compile(r"\d[\d,]*(?:\.\d+)?\s?(?:(?:조|억|만)\s?(?:원|달러|유로|엔|주)|%p|%|배|원|달러|엔|유로|명|일|년|주|장|곳|개|건|조|억|만)")


def _괄호단위(제목):
    """굵은 제목의 괄호 안에 단위가 있나(「(기준 시나리오, 전 열 대비 %)」 · 「(2025년 평균 = 100)」 · 「(%p)」)."""
    굵 = re.match(r"^\*\*(.*?)\*\*", 제목 or "")
    for 안 in re.findall(r"\(([^()]*)\)", 굵.group(1) if 굵 else ""):
        for 칸 in re.split(r"[,·]", 안):
            칸 = 칸.strip()
            if 칸 and (_단위말.fullmatch(칸) or re.search(r"(?:대비|=)\s?(?:%p|%|100%?)$", 칸) or re.search(r"(%p|%|명|배|원|달러)$", 칸)):
                return True
    return False


def 단위있나(제목, 표들):
    """그림의 단위가 어디에든 있나 — 제목(그림 이름 — 「 — 」 앞)의 괄호 · 캡션의 눈금 선언(「= 100」) · 「단위가 없는」 선언 ·
    숫자 칸마다(칸 글 · 줄 이름 · 열 머리 가운데 하나에 단위). 제목은 굵은 표시가 있든 없든 받는다(`레터모션._블록들` 은 별표를 뗀다)."""
    제 = "%s" % (제목 or "")
    이름 = re.split(r"\s—\s", re.sub(r"\*", "", 제))[0]
    if _괄호단위("**%s**" % 이름) or "단위가 없" in 제 or re.search(r"=\s?100", 제):
        return True
    숫자칸 = 0
    for 머, 줄들 in 표들:
        for r in 줄들:
            이름 = r[0] if r else ""
            for j, c in enumerate(r[1:], 1):
                c = re.sub(r"\*", "", "%s" % c).strip()
                if not re.search(r"\d", c) or re.fullmatch(r"(?:19|20)\d\d", c):
                    continue
                숫자칸 += 1
                h = 머[j] if j < len(머) else ""
                if not (_값단위.search(c) or _단위말.search(이름) or _단위말.search(h) or "= 100" in 이름):
                    return False
    return 숫자칸 > 0


def 출처있나(제목):
    return bool(re.search(r"(?:출처|자료):\s*\S", 제목 or ""))


_출처면제 = ("띠", "신호")                                    # 요약 띠 · 신호 카드(HTML) — 숫자는 결론 · 신호 표의 것
_글절 = ("자리", "점검", "파일")


def _상황자리(가정, 재료, 절들):
    """상황 → 그 상황이 선 절 키의 모음(「*」 = 어느 절이든). 구조 · 재료로 서는 상황(조건은 여기 · 뜻은 그림규칙.json)과 글에서 서는 상황(본편 절의 표)."""
    import 레터1부                                           # noqa: PLC0415 — 매출명칭인가(증가율 경로 구분의 판매량명칭이 매출 그 자체인가)
    구 = (가정 or {}).get("구조") or {}
    구분들 = [x for x in (구.get("매출구분") or []) if isinstance(x, dict)]
    키들 = {d["키"] for d in 절들 if d["키"]}

    def 절(k):
        return {k} if (not 절들 or k in 키들) else set()
    낸 = {}

    def 더(상, 자리):
        if 자리:
            낸.setdefault(상, set()).update(자리)
    더("세시나리오", {"*"} | 절("시나리오"))
    if isinstance(((가정 or {}).get("Narrative") or {}).get("동인"), dict) and ((가정 or {}).get("Narrative") or {})["동인"].get("표"):
        더("민감도", 절("민감도"))
    if any(x.get("경로") == "수준" for x in 구분들):
        더("수준경로구분", 절("매출"))
    if any(x.get("경로") == "수준" and x.get("단가경로") == "수렴" and (x.get("번호") or 9) < 6 for x in 구분들):
        더("정상수준", {"*"})
        if isinstance(가정, dict) and _외부지표충분(가정) and ((가정.get("관측") or {}).get("업황지표")):     # 2026-10-31 L1 — 외부 지표가 위치를 정했을 때만
            더("업황위치", 절("업황"))
    if any(x.get("판매량산정") == "능력" for x in 구분들) and (구.get("투자") or {}).get("공장표") == "예":
        더("능력구분", 절("재투자"))
    인 = 구.get("인건비") or {}
    if 인.get("산정방식") == "인원" and 인.get("성과급") not in (None, "없음"):
        더("성과급", 절("인건비"))
    if 인.get("산정방식") == "인원":
        더("인원인건비", 절("인건비"))
    종가 = ((가정 or {}).get("시점가정") or {}).get("099") or ((가정 or {}).get("원천") or {}).get("99")
    if 종가 or ((가정 or {}).get("관측") or {}).get("종가"):
        더("종가있음", {"*"})
        if "정상수준" in 낸:
            더("정상수준역산", {"*"})
    기 = (재료 or {}).get("기저율") or {}
    if any(isinstance(x, dict) and x.get("자리") for x in (기.get("비율자리") or [])):
        더("같은집단자리", {"*"})
    if (가정 or {}).get("지난") or (재료 or {}).get("지난평가"):
        더("지난평가", {"*"})
    if any((x.get("경로") == "수준" or (x.get("경로") == "증가율" and not 레터1부.매출명칭인가(x))) and (x.get("번호") or 9) < 6 for x in 구분들):
        더("매출구분나눔", 절("매출"))
    for k, 상 in (("재투자", "투자"), ("세금", "FCFF"), ("할인율", "WACC"), ("영구", "TV")):
        if 절들 and k in 키들:
            더(상, {k})
    # 레터 v27 7단계(다) — 회사의 구조가 고르는 그림(`레터회사그림` 의 생성 조건과 같은 판정)
    import 레터회사그림                                       # noqa: PLC0415
    if 레터회사그림.물량연동원가인가(구):
        더("물량연동원가", 절("비용"))
    if 레터회사그림.저량구분들(구):
        더("저량구분", 절("매출"))
    공제 = (((가정 or {}).get("가정") or {}).get("204") or {}).get("기준") or {}
    if any(isinstance(v, (int, float)) and not isinstance(v, bool) and v and k != "TV" for k, v in 공제.items()):
        더("결손금사용", 절("세금"))
    # 글에서 서는 상황 — 본편 절의 표
    for d in 절들:
        k = d["키"]
        글 = "\n".join(d["줄들"])
        if re.search(r"^\| 가정 \| 이 평가의 값 \|.*(?:근거 범위|상장사 80% 구간|상장사 80% 띠)", 글, re.M) and re.search(r"\|\s*[−\-+]?\d[^|]*~\s*[−\-+]?\d[^|]*\|", 글):
            더("근거범위", {k})
        if k == "비용":
            성 = set(re.findall(r"^\|[^|]+\|[^|]+\|\s*(변동비|준고정비|인건비|이익 연동 비용|고정비|조정|계단비|이익 연동비)\s*\|", 글, re.M))
            if len(성) >= 2:
                더("원가성격", {k})
        if k == "운전자본" and re.search(r"^\| (?:매출채권|재고자산|매입채무) 회전일수 \|.*\d", 글, re.M):
            더("회전일수", {k})
        if k == "할인율" and len(re.findall(r"^\| (?!\*\*)[^|]+ \| \d+\.\d{3} \|$", 글.split("| Peer group | Unlevered Beta |", 1)[1], re.M) if "| Peer group | Unlevered Beta |" in 글 else []) >= 2:
            더("유사기업표", {k})
        if k == "역산" and "| 가정 | 이 가격에 필요한 값 |" in 글 and "정상수준" not in 낸:
            더("증가율역산", {k})
            if re.search(r"^\| 영구기간 영업이익률 \| [−\-]?\d", 글, re.M):
                더("증가율역산곡선", {k})
    return 낸


def _외부지표충분(가정):
    """사이클 위치 그림의 금지 조건 — 가정의 외부 관측 지표(`관측.업황지표`)가 `레터원고.업황지표최소` 이상인가. 가정이 없으면 참(판정 재료 없음 — 걸지 않는다)."""
    if not isinstance(가정, dict):
        return True
    import 레터원고                                          # noqa: PLC0415
    return 레터원고.업황지표충분(가정)


def 절검사(글, 가정=None, 재료=None, 규칙=None):
    """레터(마크다운) · 가정 · 재료 → 편집 등급 목록 [{"등급": "편집", "절", "항목", "내용"}] (막지 않는다 — 편집 대장).
    본편이 없는 글(조각 · 빈 글)은 상황 규칙만 본다(그림을 글 어디서든 찾는다)."""
    규 = 규칙 if 규칙 is not None else 규칙읽기()
    룰 = 규.get("규칙") if isinstance(규, dict) else 규
    절규 = (규.get("절규칙") or {}) if isinstance(규, dict) else {}
    변수절 = set(절규.get("변수절") or ())
    등급 = (규.get("등급") if isinstance(규, dict) else None) or "편집"
    절들 = 본편절들(글)
    낸 = []

    def 더(절, 항목, 내용):
        낸.append({"등급": 등급, "절": 절, "항목": 항목, "내용": 내용})
    셈 = {}
    import 레터그림배치                                       # noqa: PLC0415 — 1.1.7 본편 그림 상한으로 부록에 옮긴 그림(가리킴 표지)도 그 절의 그림으로 센다
    for d in 절들:
        블, 표수 = _그림셈(d["줄들"])
        옮 = 레터그림배치.옮긴종류(d["줄들"])
        이름 = "%d절 「%s」" % (d["번호"], d["제목"].split(" : ")[0])
        셈[d["키"] or d["제목"]] = (블, 표수, 이름, 옮)
        if d["키"] in 변수절 and not 블 and not 옮:
            더(이름, "그림 없음", "변수 절에 그림이 하나도 없다(「절마다 그림 또는 표」 — 변수 절은 그림 하나 이상)")
        elif d["키"] not in 변수절 and d["키"] not in _글절 and not 블 and not 표수 and not 옮:
            더(이름, "그림 · 표 없음", "절에 그림도 표도 없다")
        for 종, 제, 표들 in 블:
            if 종 in _출처면제:
                continue
            짧 = re.sub(r"\*", "", 제)[:40]
            if not 출처있나(제):
                더(이름, "출처 줄 없음", "그림 「%s」(%s)의 제목 줄에 「출처:」 문장이 없다" % (짧, 종))
            if 종 != "연결" and not 단위있나(제, 표들):
                더(이름, "단위 없음", "그림 「%s」(%s)에 단위가 없다(제목 괄호 · 줄 이름 · 열 머리 · 칸 글 어디에도)" % (짧, 종))
    있는전부 = set(re.findall(r"<!--\s*그림:(\S+)", 글 or ""))
    자리 = _상황자리(가정, 재료, 절들)
    for r in 룰 or []:
        상 = r.get("상황")
        if 상 not in 자리:
            continue
        그림 = r.get("그림")
        그림들 = [그림] if isinstance(그림, str) else list(그림 or [])
        절키 = r.get("절")
        for k in sorted(자리[상]):
            if 절키 and k != "*" and k != 절키:
                continue
            if 절키 and k == "*" and 절키 in 셈:
                k = 절키
            if k != "*" and k in 셈:
                있 = {종 for 종, _제, _표 in 셈[k][0]} | set(셈[k][3])
                곳 = 셈[k][2]
            else:
                있, 곳 = 있는전부, "레터"
            if not (set(그림들) & 있):
                더(곳, "상황 그림 없음", "상황 「%s」(%s)인데 그림 「%s」가 없다 — %s(%s)" % (상, r.get("뜻", ""), " · ".join(그림들), r.get("자리", ""), r.get("왜", "")))
    # 2026-10-31(독립 검토 L1) 금지 규칙 — 그 상황이면 그 그림을 싣지 않는다(`그림규칙.json` 「금지」). 생성이 먼저 막고 여기는 손으로 넣은 그림을 잡는다
    for r in (규.get("금지") or []) if isinstance(규, dict) else []:
        if r.get("이름") == "자기출처위치" and r.get("그림") in 있는전부 and not _외부지표충분(가정):
            더("레터", "금지 그림", "그림 「%s」 — %s(%s)" % (r.get("그림"), r.get("뜻", ""), r.get("왜", "")))
    본, 걸 = set(), []
    for x in 낸:
        k = (x["절"], x["항목"], x["내용"])
        if k not in 본:
            본.add(k)
            걸.append(x)
    return 걸


def 상황검사(글, 가정, 재료=None, 규칙=None):
    """레터(마크다운) · 가정 · 재료 → 「편집 등급 — …」 글 목록(막지 않는다 — 레터.py 가 초안을 낼 때 찍는다). 규칙은 `그림규칙.json`.
    2026-10-25 R5 — 상황 규칙에 절 규칙(변수 절의 그림 · 그림마다 출처 줄 · 단위)을 더하고 등급을 알림에서 편집으로 올렸다."""
    return ["%s 등급 — %s: %s" % (x["등급"], x["절"], x["내용"]) for x in 절검사(글, 가정, 재료, 규칙)]


def 절그림셈(글):
    """본편 절마다 (번호, 제목, 그림 수, 그림 밖의 표 수, 그림 종류) — 실측용."""
    낸 = []
    for d in 본편절들(글):
        블, 표수 = _그림셈(d["줄들"])
        낸.append((d["번호"], d["제목"], len(블), 표수, [종 for 종, _제, _표 in 블]))
    return 낸


def 문서검사(글, 마크=False):
    """레터(마크다운) → 그림마다 검사 결과 글 목록(오류). 두 판 그림은 넓은 · 좁은 판 둘 다, 한 판 그림은 휴대폰 폭으로 잰다.
    마크 = True 면 ⑤ 라벨과 마크 겹침도(v4f — 게이트 ⑬ 에 걸 때 이 인자로 켠다)."""
    import 레터모션                                         # noqa: PLC0415
    낸 = []
    for 종, _모, 제목, 표들 in 레터모션._블록들(글):
        f = G.그림들.get(종)
        if not f:
            continue
        제 = re.sub(r"\*", "", 제목)
        판들 = [("넓은", f(표들, 제, 판="넓은")), ("좁은", f(표들, 제, 판="좁은"))] if 종 in G.두판 else [("한판", f(표들, 제))]
        이름 = re.split(r"\s—\s", 제)[0][:30]
        for 판, svg in 판들:
            for s in re.findall(r"<svg\b.*?</svg>", svg or "", re.S):
                for 번, 말 in 그림검사(s, 판, 마크):
                    낸.append("%s 「%s」(%s · %s) %s" % (번, 이름, 종, {"넓은": "넓은 판", "좁은": "좁은 판"}.get(판, "한 판"), 말))
    return 낸


def main(argv=None):
    """편집 대장 — 초안(마크다운)의 절 규칙 · 상황 규칙(편집 등급)과 그림검사 ①~⑤(게이트 ⑬ 오류)를 한 번에 낸다.
        python 스크립트/레터그림검사.py 레터_초안.md [--가정 가정.json] [-o 레터_초안.그림편집.json]
    재료(기저율 등)는 가정 곁 `_raw/` 에서 `레터.재료파일읽기` 로 읽는다. 편집 등급은 막지 않는다 — 종료 코드는 ①~⑤ 오류가 있을 때만 1."""
    import argparse                                          # noqa: PLC0415
    import io as _io                                         # noqa: PLC0415
    import json as _json                                     # noqa: PLC0415
    import os as _os                                         # noqa: PLC0415
    import sys as _sys                                       # noqa: PLC0415
    ap = argparse.ArgumentParser(description="레터 그림 편집 대장(절 규칙 · 상황 규칙 · 그림검사)")
    ap.add_argument("글")
    ap.add_argument("--가정", default=None)
    ap.add_argument("-o", "--출력", default=None)
    a = ap.parse_args(argv)
    try:
        _sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                        # noqa: BLE001
        pass
    글 = _io.open(a.글, encoding="utf-8").read()
    가정, 재료 = None, None
    if a.가정:
        가정 = _json.load(_io.open(a.가정, encoding="utf-8"))
        try:
            import 레터                                      # noqa: PLC0415
            재료 = 레터.재료파일읽기(a.가정)[0]
        except Exception:                                    # noqa: BLE001
            재료 = None
    편 = 절검사(글, 가정, 재료)
    오 = 문서검사(글, 마크=True)
    셈 = 절그림셈(글)
    print("편집 대장(그림) — 편집 등급 %d건 · 그림검사 오류 %d건 · 본편 그림 %d개" % (len(편), len(오), sum(n for _b, _t, n, _s, _k in 셈)))
    for x in 편:
        print("  [%s] %s · %s — %s" % (x["등급"], x["절"], x["항목"], x["내용"]))
    for x in 오[:40]:
        print("  [오류] %s" % x)
    if a.출력:
        _io.open(a.출력, "w", encoding="utf-8").write(_json.dumps({"형식": "그림편집/1", "글": _os.path.basename(a.글), "편집": 편, "그림검사": 오,
                                                                   "절": [{"번호": b, "제목": t2, "그림": n, "표": s, "종류": k} for b, t2, n, s, k in 셈]},
                                                                  ensure_ascii=False, indent=1))
        print("→ %s" % a.출력)
    return 1 if 오 else 0


if __name__ == "__main__":
    import sys as _s
    _s.exit(main())

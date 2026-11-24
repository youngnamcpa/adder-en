# -*- coding: utf-8 -*-
"""레터그림본편 — 본편(모델을 세운 순서)의 그림 (2026-10-16 결정 — 모델 설계를 그림으로 보인다).

계산하지 않는다. 레터(마크다운)에 실린 그림 표의 글(장부의 숫자를 꼴대로 찍은 글)을 좌표로만 바꾼다(`레터그림` 과 같은 원칙).
그림의 숫자는 모두 그 표에 있고, 표의 숫자는 게이트가 장부와 맞댄다. 그림은 휴대폰 폭(viewBox 360)에 맞추고 색은 CSS 변수 —
밝은 · 어두운 화면 · 인쇄가 같은 그림을 쓴다. 색만으로 계열을 가르지 않는다(선 모양 · 끝 이름 · 칸 이름을 함께 둔다).

  연결(표)     변수 연결도 — HTML 상자. 표: 단계 · 변수 · 가정 · 넘기는 값. 「물량」 · 「가격」 줄은 매출 구분마다 짝(물량 × 가격)으로 나란히.
               정적이다(v4d — 순서가 이미 공간에 있다). 웹에서 마우스를 올린 상자에서 아래로 가치까지의 경로만 진하게(CSS · 움직임 없음 · 인쇄 무관)
  스트림(표)   매출 구분 하나의 판 여럿 — 줄 이름 「판 이름 · 계열」(계열 = 실적 · 비관 · 기준 · 낙관), 머리 = 기간
  쌓기(표)     쌓은 막대 — 줄 = 칸(음수는 0 아래로), 「(선)」 으로 끝나는 줄은 선, 머리 = 기간
  비중(표)     매출 대비 비중의 변화(%p) — 가로 막대(0 을 가운데로)
  공장(표)     공장별 ROIC 가로 막대 + 「(선)」 줄(영구기간 WACC)의 세로 기준선
  격자(표)     두 변수 민감도 격자 — 칸의 색은 가운데 칸(기준)에서 멀어진 정도, 값 글은 칸 안에, 기준 칸은 굵은 테두리
  곡선(표들)   주가 → 그 주가가 전제한 정상 수준(구분마다 선) + 둘째 표의 가로선(이 평가의 기준). v4f — 웹에서는 범위 단추로 주가를 격자 칸마다
               옮겨 그 칸의 정상 수준(증가율 경로 판은 영구기간 영업이익률 — data-steps 의 「말」)을 읽는다(svg 의 data-steps · `레터HTML.단계JS` — 보간 없음, 정적 그림 · 인쇄는 그대로)
"""
from __future__ import annotations

import json
import math
import re

import 레터그림 as G

_e = G._e
수읽기 = G.수읽기
_폭 = G._폭


def _맑게(c):
    return re.sub(r"\*", "", "%s" % c).strip()


def _단위말(머리, 글들=()):
    """판의 눈금 단위 — 칸 글의 돈 단위(「조 원」 · 「억 달러」 …)가 있으면 그것(v4e — 판 이름에 박힌 「조 원」 보다 칸 글이 먼저),
    없으면 판 이름의 「(조 원 …)」 · 「(억 원 …)」."""
    if any(G._돈꼴.search("%s" % g) for g in 글들):
        return G.돈단위(글들)[0][0]
    return "조" if "조 원" in 머리 else ("억" if "억 원" in 머리 else "")


def _돈말(글들):
    """칸 글의 돈 단위 글(「억 달러」 · 「조 원」) — 없으면 빈 글(2026-10-25 R5 — 눈금 옆 「단위: …」)."""
    return G.돈단위(글들)[0] if any(G._돈꼴.search("%s" % g) for g in 글들) else ""


def _퍼말(글들):
    """칸 글이 모두 퍼센트면 눈금 글에 붙일 단위 — 「%p」 · 「%」(돈 · 수 그림은 빈 글 · 2026-10-25 R5)."""
    수칸 = [_맑게(g) for g in 글들 if re.search(r"\d", "%s" % g)]
    if 수칸 and all(re.search(r"%p$", g) for g in 수칸):
        return "%p"
    if 수칸 and all(re.search(r"%$", g) for g in 수칸):
        return "%"
    return ""


def _눈글(v, 단):
    if 단 == "조":
        v = v / 1e12
    elif 단 == "억":
        v = v / 1e8
    elif 단 == "만":
        v = v / 1e4
    return G._눈금수(v)


# ══════════════════════════════════════════════════════════════════ 연결 — 변수 연결도(HTML)

def 연결(표들, 제목=""):
    if not 표들:
        return ""
    머리, 줄들 = 표들[0]
    줄들 = [[_맑게(c) for c in r] + [""] * (4 - len(r)) for r in 줄들 if r and _맑게(r[0])]
    if len(줄들) < 3:
        return ""

    def 상자(r, 갈=""):
        단, 변, 가, 값 = r[0], r[1], r[2], r[3]
        return ('<div class="flow-box%s"><span class="flow-tag">%s</span><b>%s</b>%s%s</div>' % (
            (" " + 갈) if 갈 else "", _e(단), _e(변), ('<span class="flow-a">%s</span>' % _e(가)) if 가 and 가 not in ("—", "-") else "",
            ('<span class="flow-v">%s</span>' % _e(값)) if 값 and 값 not in ("—", "-") else ""))
    낸 = ['<div class="flow" role="group" aria-label="%s">' % _e(제목 or "변수 연결도")]
    i = 0
    첫 = True
    while i < len(줄들):
        if 줄들[i][0] in ("물량", "가격"):
            짝들 = []
            while i < len(줄들) and 줄들[i][0] in ("물량", "가격"):
                if 줄들[i][0] == "물량" and i + 1 < len(줄들) and 줄들[i + 1][0] == "가격":
                    짝들.append((줄들[i], 줄들[i + 1]))
                    i += 2
                else:
                    짝들.append((줄들[i], None) if 줄들[i][0] == "물량" else (None, 줄들[i]))
                    i += 1
            if not 첫:
                낸.append('<div class="flow-arrow" aria-hidden="true"></div>')
            낸.append('<div class="flow-streams">')
            for 물, 가 in 짝들:
                낸.append('<div class="flow-pair">%s%s%s</div>' % (
                    상자(물) if 물 else "", '<span class="flow-times" aria-label="곱하기">×</span>' if (물 and 가) else "", 상자(가) if 가 else ""))
            낸.append("</div>")
        else:
            if not 첫:
                낸.append('<div class="flow-arrow" aria-hidden="true"></div>')
            낸.append(상자(줄들[i], "flow-main"))
            i += 1
        첫 = False
    낸.append("</div>")
    return "".join(낸)


# ══════════════════════════════════════════════════════════════════ 선 그림의 바탕

_계열꼴 = {"기준": ("vz-s1", 0), "비관": ("vz-s2", 1), "낙관": ("vz-s3", 2), "실적": ("vz-act", 3)}


def _판들(줄들):
    """줄 이름 「판 · 계열」 → [(판, [(계열, 값들, 글들)])] (나온 차례)."""
    판 = []
    for r in 줄들:
        이 = _맑게(r[0])
        if " · " in 이:
            p, s = 이.rsplit(" · ", 1)
        else:
            p, s = 이, "기준"
        if not 판 or 판[-1][0] != p:
            판.append((p, []))
        판[-1][1].append((s, [수읽기(c) for c in r[1:]], [_맑게(c) for c in r[1:]]))
    return 판


def _끝이름(s, 계열글, 높이, 위, 아래):
    """끝 이름 자리(겹치지 않게) — [(가운데 y, 순위, 높이)] → y 목록."""
    return G._비켜놓기([(y, 순, 높이) for y, 순 in s], 2, 위, 아래)


def _선축(lo, hi, 칸수=3):
    """선만 그리는 판의 세로 범위 — 값의 최소 ~ 최대에 여백을 두고 0 을 끼우지 않는다(지수 선 · 막대 없음). → (눈금, 아래 끝, 위 끝)."""
    import math                                               # noqa: PLC0415
    폭 = (hi - lo) or abs(hi) * 0.1 or 1.0
    밑, 위 = lo - 폭 * 0.12, hi + 폭 * 0.12
    날 = (위 - 밑) / 칸수
    자 = 10 ** math.floor(math.log10(날))
    칸 = next(자 * k for k in (1, 2, 2.5, 5, 10) if 자 * k >= 날 - 1e-12)   # 레터그림._범위눈금 과 같은 간격(0 을 끼우지 않는다)
    g = math.ceil(밑 / 칸 - 1e-9) * 칸
    눈 = []
    while g <= 위 + 1e-9:
        눈.append(round(g, 10))
        g += 칸
    return 눈, 밑, 위


def 스트림(표들, 제목="", 바닥0=True):
    """바닥0 이 거짓이면(지수 선 — 원가두선) 눈금이 값의 최소에서 선다(막대가 아니라 선이라 0 을 지키지 않는다)."""
    if not 표들:
        return ""
    머리, 줄들 = 표들[0]
    x머리 = [_맑게(h) for h in 머리[1:]]
    판들 = _판들(줄들)
    if not 판들:
        return ""
    n = len(x머리)
    끝글들 = ["%s %s" % (계, g.replace(" 원", "")) for _p, 계들 in 판들 for 계, vs, gs in 계들 if 계 != "실적"
             for g in [next((gs[i] for i in range(len(vs) - 1, -1, -1) if vs[i] is not None), "")]]
    # 왼쪽 여백은 가장 긴 눈금 글을 품는다(2026-10-23 — 「10,000」 같은 다섯 자리 눈금이 그림 밖으로 나갔다)
    눈글들 = []
    for _p, 계들 in 판들:
        값들 = [v for _s, vs, _g in 계들 for v in vs if v is not None]
        if 값들:
            단 = _단위말(_p, [g for _s, _v, gs in 계들 for g in gs])
            눈, _밑, _위 = G._축(min(값들 + [0.0]) if min(값들) < 0 else 0.0, max(값들), 3) if 바닥0 else _선축(min(값들), max(값들))
            눈글들 += [_눈글(g, 단) for g in 눈]
    W, l = 360, max(38, int(max([_폭(x, 12.5) for x in 눈글들] + [0.0]) + 8))
    rr = min(118.0, max([_폭(x, 12.5) * 1.04 for x in 끝글들] + [60.0]) + 9)    # v4e — 끝 이름이 그림 안에
    판높, 판틈, 위여백 = 112, 30, 24
    pw = W - l - rr
    H = 위여백 + len(판들) * (판높 + 판틈) + 30

    def X(i):
        return l + (pw * i / (n - 1) if n > 1 else pw / 2)
    s = ['<svg class="viz viz-stream" viewBox="0 0 %d %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">' % (W, H, _e(제목 or "그림"))]
    # 범례 — 선 모양과 이름(색만으로 가르지 않는다). 레터 v27 7단계 — 계열이 시나리오가 아니면(매출 · 매출원가 따위) 그 이름으로
    맞춤 = {}
    for _p, 계들 in 판들:
        for 계, _v, _g in 계들:
            if 계 not in _계열꼴 and 계 not in 맞춤 and len(맞춤) < 3:
                맞춤[계] = (("vz-s1", 0), ("vz-s2", 1), ("vz-s3", 2))[len(맞춤)]
    lx = l
    for 이, (cls, _k) in (list(맞춤.items()) if 맞춤 else (("기준", _계열꼴["기준"]), ("비관", _계열꼴["비관"]), ("낙관", _계열꼴["낙관"]))):
        s.append('<line x1="%d" x2="%d" y1="9" y2="9" class="%s"/>' % (lx, lx + 18, cls))
        s.append('<text x="%d" y="13" class="viz-tick">%s</text>' % (lx + 22, 이))
        lx += 22 + int(_폭(이, 12.5)) + 14
    if any(계 == "실적" for _p, 계들 in 판들 for 계, _v, _g in 계들):
        s.append('<circle cx="%d" cy="9" r="3.5" class="vz-act"/>' % (lx + 4))
        s.append('<text x="%d" y="13" class="viz-tick">실적</text>' % (lx + 12))
    for k, (판이름, 계들) in enumerate(판들):
        t = 위여백 + k * (판높 + 판틈) + 16
        h = 판높 - 16
        값들 = [v for _s, vs, _g in 계들 for v in vs if v is not None]
        if not 값들:
            continue
        단 = _단위말(판이름, [g for _s, _v, gs in 계들 for g in gs])
        눈, 밑, 위 = G._축(min(값들 + [0.0]) if min(값들) < 0 else 0.0, max(값들), 3) if 바닥0 else _선축(min(값들), max(값들))

        def Y(v, t=t, h=h, 밑=밑, 위=위):
            return t + h * (1 - (v - 밑) / ((위 - 밑) or 1.0))
        돈 = _돈말([g for _s, _v, gs in 계들 for g in gs])               # 2026-10-25 R5 — 돈 판은 판 이름에 단위(눈금이 그 단위의 수다)
        판말 = 판이름 if (not 돈 or 돈 in 판이름) else (("%s, %s)" % (판이름[:-1], 돈)) if 판이름.endswith(")") else "%s(%s)" % (판이름, 돈))
        s.append('<text x="%d" y="%d" class="viz-label viz-strong" style="font-size:12.5px">%s</text>' % (l - 34, t - 12, _e(판말)))
        for g in 눈:
            s.append('<line x1="%d" x2="%.1f" y1="%.1f" y2="%.1f" class="viz-grid"/>' % (l, l + pw, Y(g), Y(g)))
            s.append('<text x="%d" y="%.1f" class="viz-tick" text-anchor="end" dominant-baseline="middle">%s</text>' % (l - 4, Y(g), _눈글(g, 단)))
        끝들 = []
        for 계, vs, gs in 계들:
            cls, 순 = _계열꼴.get(계) or 맞춤.get(계, ("vz-s1", 0))
            pts = [(X(i), Y(v)) for i, v in enumerate(vs) if v is not None]
            if not pts:
                continue
            if 계 == "실적":
                for (x, y), (i, v) in zip(pts, [(i, v) for i, v in enumerate(vs) if v is not None]):
                    s.append('<circle cx="%.1f" cy="%.1f" r="3.5" class="vz-act"><title>%s 실적 %s</title></circle>' % (x, y, _e(x머리[i]), _e(gs[i])))
                continue
            s.append('<polyline points="%s" class="%s"/>' % (" ".join("%.1f,%.1f" % p for p in pts), cls))
            for i, v in enumerate(vs):
                if v is not None:
                    s.append('<circle cx="%.1f" cy="%.1f" r="7" class="viz-hit"><title>%s %s %s</title></circle>' % (X(i), Y(v), _e(x머리[i]), 계, _e(gs[i])))
            i끝 = max(i for i, v in enumerate(vs) if v is not None)
            끝들.append((계, Y(vs[i끝]), 순, gs[i끝]))
        자리 = G._비켜놓기([(y, 순, 13) for _c, y, 순, _g in 끝들], 1, t - 4, t + h + 8)
        for (계, y0, _순, 글), y in zip(끝들, 자리):
            s.append('<text x="%.1f" y="%.1f" class="viz-tick%s" dominant-baseline="middle">%s %s</text>' % (
                l + pw + 5, y, " viz-strong" if 계 == "기준" else "", 계, _e(글.replace(" 원", ""))))
        if k == len(판들) - 1:
            for x, 줄, 글 in G._x축글([X(i) for i in range(n)], x머리, 12.5, 2, l + pw + 4):
                s.append('<text x="%.1f" y="%.1f" class="viz-tick" text-anchor="middle" style="font-size:12.5px">%s</text>' % (x, t + h + (18 if 줄 == 1 else 31), _e(글)))
    s.append("</svg>")
    return "".join(s)


# ══════════════════════════════════════════════════════════════════ 쌓기

def 쌓기(표들, 제목=""):
    if not 표들:
        return ""
    머리, 줄들 = 표들[0]
    x머리 = [_맑게(h) for h in 머리[1:]]
    n = len(x머리)
    칸들 = [(_맑게(r[0]), [수읽기(c) for c in r[1:]], [_맑게(c) for c in r[1:]]) for r in 줄들 if r and not _맑게(r[0]).endswith("(선)")]
    선들 = [(re.sub(r"\s*\(선\)$", "", _맑게(r[0])), [수읽기(c) for c in r[1:]], [_맑게(c) for c in r[1:]]) for r in 줄들 if r and _맑게(r[0]).endswith("(선)")]
    if not 칸들 or n < 2:
        return ""
    위들, 아래들 = [], []
    for i in range(n):
        양 = sum(v[i] for _n2, v, _g in 칸들 if v[i] is not None and v[i] > 0)
        음 = sum(v[i] for _n2, v, _g in 칸들 if v[i] is not None and v[i] < 0)
        위들.append(양)
        아래들.append(음)
    for _n2, v, _g in 선들:
        위들 += [x for x in v if x is not None]
        아래들 += [x for x in v if x is not None]
    단 = _단위말("", [g for _n2, _v, gs in 칸들 + 선들 for g in gs])
    퍼 = _퍼말([g for _n2, _v, gs in 칸들 + 선들 for g in gs])         # 2026-10-25 R5 — 칸 글이 모두 % · %p 면 눈금 글에도 단위(동인 분해 · 매출 대비 비중)
    눈, 밑, 위 = G._축(min(아래들 + [0.0]), max(위들 + [0.0]), 4)
    W, t, b = 360, 26, 40
    l = max(36.0, max(_폭(_눈글(g, 단) + 퍼, 12.5) * 1.04 for g in 눈) + 9)        # v4e — 눈금 글이 그림 안에
    끝이름 = [이 for 이, *_r in 칸들 + 선들]
    끝다 = max([_폭(x, 12.5) * 1.04 for x in 끝이름] + [0.0]) <= 120        # v4e — 끝 이름이 한 줄에 들 때만 막대 옆에(아니면 범례가 맡는다)
    rr = (max([_폭(x, 12.5) * 1.04 for x in 끝이름] + [40.0]) + 12) if 끝다 else 14.0
    범례 = []                                                # 범례 — 이름 폭대로 흘려 놓고 넘치면 다음 줄, 한 줄보다 긴 이름은 접는다(v4e)
    lx, ly = float(l), 4.0
    for k, (이, _v, _g) in enumerate(칸들 + 선들):
        줄 = G._접기폭(이, W - 4 - l - 15, 12.5)
        w = 15 + max(_폭(z, 12.5) for z in 줄) * 1.04 + 14
        if lx + w > W - 4 and lx > l:
            lx, ly = float(l), ly + 17
        범례.append((k, 줄, lx, ly))
        lx += w
        if len(줄) > 1:
            lx, ly = float(l), ly + 17 * len(줄)
    t += ly + 13
    돈 = _돈말([g for _n2, _v, gs in 칸들 + 선들 for g in gs])          # 2026-10-25 R5 — 돈 그림은 눈금 위에 「단위: …」(가치 그림과 같은 꼴)
    H = t + 190 + b
    ph = H - t - b
    pw = W - l - rr
    칸폭 = pw / n

    def X(i):
        return l + 칸폭 * (i + 0.5)

    def Y(v):
        return t + ph * (1 - (v - 밑) / ((위 - 밑) or 1.0))
    s = ['<svg class="viz viz-stack" viewBox="0 0 %d %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">' % (W, H, _e(제목 or "그림"))]
    for k, 줄, x0, y0 in 범례:                              # 범례 — 칸마다 견본과 이름
        if k < len(칸들):
            s.append('<rect x="%.1f" y="%.1f" width="11" height="9" rx="2" class="vz-c%d"/>' % (x0, y0 + 2, k % 6 + 1))
        else:
            s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="vz-ln"/>' % (x0, x0 + 11, y0 + 7, y0 + 7))
        for j, z in enumerate(줄):
            s.append('<text x="%.1f" y="%.1f" class="viz-tick">%s</text>' % (x0 + 15, y0 + 10 + 17 * j, _e(z)))
    if 돈:
        s.append('<text x="4" y="%.1f" class="viz-tick">단위: %s</text>' % (t - 13, _e(돈)))
    for g in 눈:
        s.append('<line x1="%d" x2="%.1f" y1="%.1f" y2="%.1f" class="%s"/>' % (l, l + pw, Y(g), Y(g), "viz-zero" if g == 0 and 밑 < 0 else "viz-grid"))
        s.append('<text x="%d" y="%.1f" class="viz-tick" text-anchor="end" dominant-baseline="middle">%s</text>' % (l - 4, Y(g), _눈글(g, 단) + 퍼))
    끝칸 = []
    for i in range(n):
        양, 음 = 0.0, 0.0
        bw = min(30.0, 칸폭 * 0.66)
        for k, (이, v, gs) in enumerate(칸들):
            x = v[i]
            if x is None or x == 0:
                continue
            if x > 0:
                a, b2 = 양, 양 + x
                양 = b2
            else:
                a, b2 = 음 + x, 음
                음 = a
            y1, y2 = sorted((Y(a), Y(b2)))
            s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" class="vz-c%d"><title>%s %s %s</title></rect>' % (
                X(i) - bw / 2, y1, bw, max(y2 - y1, .6), k % 6 + 1, _e(x머리[i]), _e(이), _e(gs[i])))
            if i == n - 1:
                끝칸.append((이, (y1 + y2) / 2, k, gs[i]))
    for 이, v, gs in 선들:
        pts = [(X(i), Y(x)) for i, x in enumerate(v) if x is not None]
        if len(pts) >= 2:
            s.append('<polyline points="%s" class="vz-ln"/>' % " ".join("%.1f,%.1f" % p for p in pts))
        for (x, y), i in zip(pts, [i for i, x in enumerate(v) if x is not None]):
            s.append('<circle cx="%.1f" cy="%.1f" r="3" class="vz-ln-dot"><title>%s %s %s</title></circle>' % (x, y, _e(x머리[i]), _e(이), _e(gs[i])))
        if pts:
            끝칸.append((이, pts[-1][1], 99, gs[len(gs) - 1]))
    if not 끝다:
        끝칸 = []
    끝줄 = [G._접기폭(이, rr - 10, 12.5) for 이, _y, _k, _g in 끝칸]
    자리 = G._비켜놓기([(y, 0 if k == 99 else 1, 14 * len(z)) for (_i, y, k, _g), z in zip(끝칸, 끝줄)], 1, t, t + ph)
    for (이, y0, k, 글), y, z in zip(끝칸, 자리, 끝줄):
        if abs(y - y0) > 2:
            s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="viz-leader"/>' % (l + pw - 2, l + pw + 3, y0, y))
        for j, g in enumerate(z):
            s.append('<text x="%.1f" y="%.1f" class="viz-tick%s" dominant-baseline="middle">%s</text>' % (
                l + pw + 5, y + 14 * (j - (len(z) - 1) / 2.0), " viz-strong" if k == 99 else "", _e(g)))
    for x, 줄, 글 in G._x축글([X(i) for i in range(n)], x머리, 12.5, 2, l + pw):
        s.append('<text x="%.1f" y="%.1f" class="viz-tick" text-anchor="middle" style="font-size:12.5px">%s</text>' % (x, H - b + (18 if 줄 == 1 else 31), _e(글)))
    s.append("</svg>")
    return "".join(s)


# ══════════════════════════════════════════════════════════════════ 비중 · 공장 — 가로 막대

def _가로막대(항, 제목, 가운데0=True, 기준선=None, 단위="%p", 갈=""):
    """항 = [(이름, 값, 글)] → 가로 막대(이름 왼쪽 · 값 오른쪽). 가운데0 이면 0 을 축으로 양음, 기준선 = (이름, 값, 글)."""
    W, lx, 이름폭, px0, px1 = 360, 4, 132, 142, 300
    크, 줄높 = 12, 14
    값들 = [v for _n2, v, _g in 항 if v is not None] + ([기준선[1]] if 기준선 else []) + [0.0]
    lo, hi = min(값들), max(값들)
    if 가운데0:
        m = max(abs(lo), abs(hi)) or 1.0
        lo, hi = -m, m
    else:
        lo = 0.0
        hi = hi * 1.08 or 1.0

    def X(v):
        return px0 + (px1 - px0) * (v - lo) / ((hi - lo) or 1.0)
    줄 = [G._접기폭(n2, 이름폭, 크) for n2, _v, _g in 항]
    높 = [max(24, 줄높 * len(z) + 8) for z in 줄]
    위 = 10 + (16 if 기준선 else 0)
    H = 위 + sum(높) + 10
    s = ['<svg class="viz %s" viewBox="0 0 %d %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">' % (갈, W, H, _e(제목 or "그림"))]
    s.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" class="viz-axis"/>' % (X(0), X(0), 위 - 4, H - 6))
    y = 위
    for (n2, v, g), z, h in zip(항, 줄, 높):
        가 = y + h / 2.0
        for j, tt in enumerate(z):
            s.append('<text x="%d" y="%.1f" class="viz-name" dominant-baseline="middle">%s</text>' % (lx, 가 + 줄높 * (j - (len(z) - 1) / 2.0), _e(tt)))
        if v is not None:
            x0, x1 = sorted((X(0), X(v)))
            cls = ("viz-down" if v > 0 else "viz-up") if 가운데0 else "viz-bar"
            s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="12" rx="2" class="%s"><title>%s %s</title></rect>' % (x0, 가 - 6, max(x1 - x0, 1.5), cls, _e(n2), _e(g)))
        s.append('<text x="%d" y="%.1f" class="viz-tick viz-value" text-anchor="end" dominant-baseline="middle">%s</text>' % (W - 4, 가, _e(g)))
        y += h
    if 기준선:
        xx = X(기준선[1])
        s.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" class="vz-ref"/>' % (xx, xx, 위 - 8, H - 6))
        s.append('<text x="%.1f" y="%d" class="viz-tick viz-strong" text-anchor="middle">%s %s</text>' % (min(max(xx, px0 + 40), px1 - 40), 12, _e(기준선[0]), _e(기준선[2])))
    s.append("</svg>")
    return "".join(s)


def 비중(표들, 제목=""):
    if not 표들:
        return ""
    _m, 줄들 = 표들[0]
    항 = [(_맑게(r[0]), 수읽기(r[1]), _맑게(r[1])) for r in 줄들 if len(r) >= 2]
    return _가로막대(항, 제목, 가운데0=True, 갈="viz-share") if len(항) >= 2 else ""


def 공장(표들, 제목=""):
    if not 표들:
        return ""
    _m, 줄들 = 표들[0]
    항 = [(_맑게(r[0]), 수읽기(r[1]), _맑게(r[1])) for r in 줄들 if len(r) >= 2 and not _맑게(r[0]).endswith("(선)")]
    선 = next(((re.sub(r"\s*\(선\)$", "", _맑게(r[0])), 수읽기(r[1]), _맑게(r[1])) for r in 줄들 if len(r) >= 2 and _맑게(r[0]).endswith("(선)")), None)
    return _가로막대(항, 제목, 가운데0=False, 기준선=선, 갈="viz-fab") if 항 else ""


# ══════════════════════════════════════════════════════════════════ 격자 — 두 변수 민감도

def _짧은값(글):
    v = 수읽기(글)
    if v is None:
        return 글
    if "원" in 글 and abs(v) >= 1e4:
        return "{:,.0f}만".format(v / 1e4) if abs(v) >= 1e6 else "{:,.1f}만".format(v / 1e4)
    return 글


def 격자(표들, 제목=""):
    if not 표들:
        return ""
    머리, 줄들 = 표들[0]
    가로 = [_맑게(h) for h in 머리[1:]]
    줄들 = [r for r in 줄들 if len(r) >= 2]
    if len(줄들) < 2 or len(가로) < 2:
        return ""
    값 = [[수읽기(c) for c in r[1:]] for r in 줄들]
    ci, cj = len(줄들) // 2, len(가로) // 2
    기 = 값[ci][cj] if ci < len(값) and cj < len(값[ci]) else None
    if not 기:
        return ""
    축 = [x.strip() for x in _맑게(머리[0]).split("\\")]
    W, l, t = 360, 50, 34 + (16 if len(축) == 2 else 0)
    칸w = (W - l - 4) / len(가로)
    칸h = 26
    H = t + 칸h * len(줄들) + 8
    떨 = max(abs(v / 기 - 1) for r in 값 for v in r if v is not None) or 1.0
    s = ['<svg class="viz viz-grid2" viewBox="0 0 %d %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">' % (W, H, _e(제목 or "그림"))]
    if len(축) == 2:                                          # v4e — 두 줄(한 줄이면 그림 밖으로 나간다)
        s.append('<text x="4" y="12" class="viz-tick">가로: %s</text>' % _e(축[1]))
        s.append('<text x="4" y="28" class="viz-tick">세로: %s</text>' % _e(축[0]))
    for j, h in enumerate(가로):
        s.append('<text x="%.1f" y="%d" class="viz-tick viz-strong" text-anchor="middle">%s</text>' % (l + 칸w * (j + 0.5), t - 6, _e(h)))
    for i, r in enumerate(줄들):
        y = t + 칸h * i
        s.append('<text x="%d" y="%.1f" class="viz-tick viz-strong" text-anchor="end" dominant-baseline="middle">%s</text>' % (l - 5, y + 칸h / 2, _e(_맑게(r[0]))))
        for j in range(len(가로)):
            v = 값[i][j] if j < len(값[i]) else None
            x = l + 칸w * j
            if v is None:
                continue
            d = v / 기 - 1
            세 = min(1.0, abs(d) / 떨)
            cls = "vz-hi" if d > 0 else "vz-lo"
            s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%d" class="%s" style="fill-opacity:%.2f"/>' % (x + 1, y + 1, 칸w - 2, 칸h - 2, cls, 0.06 + 0.34 * 세))     # v4e — 칸 위 글 대비 4.5:1(어두운 화면)
            if i == ci and j == cj:
                s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%d" class="vz-base"/>' % (x + 1, y + 1, 칸w - 2, 칸h - 2))
            짧 = _짧은값(_맑게(r[j + 1]))
            if _폭(짧, 12.5) > 칸w - 4:                       # 2026-10-25 R5 — 칸보다 긴 글(「105.42달러」)은 통화 이름을 뗀다(단위는 표 · 제목에 있다)
                짧 = re.sub(r"\s?(?:달러|엔|유로|원)$", "", 짧)
            s.append('<text x="%.1f" y="%.1f" class="viz-tick viz-value%s" text-anchor="middle" dominant-baseline="middle" style="fill:var(--ink)">%s<title>%s</title></text>' % (
                x + 칸w / 2, y + 칸h / 2, " viz-strong" if (i == ci and j == cj) else "", _e(짧), _e(_맑게(r[j + 1]))))
    s.append("</svg>")
    return "".join(s)


# ══════════════════════════════════════════════════════════════════ 곡선 — 주가 → 전제한 정상 수준

def 곡선(표들, 제목=""):
    if not 표들:
        return ""
    머리, 줄들 = 표들[0]
    계열 = [_맑게(h) for h in 머리[1:]]
    xs = [수읽기(r[0]) for r in 줄들]
    ys = [[수읽기(c) for c in r[1:]] for r in 줄들]
    if len(xs) < 3 or any(x is None for x in xs):
        return ""
    선들 = []
    if len(표들) > 1:
        m2, r2 = 표들[1]
        for r in r2:
            선들.append((_맑게(r[0]), [수읽기(c) for c in r[1:]], [_맑게(c) for c in r[1:]]))
    세로 = []                                                  # 2026-10-25 R5 — 셋째 표(있으면): 세로선(이름 · 가로축 값 — 「종가」 의 자리)
    if len(표들) > 2:
        for r in 표들[2][1]:
            if len(r) >= 2 and 수읽기(r[1]) is not None:
                세로.append((_맑게(r[0]), 수읽기(r[1]), _맑게(r[1])))
    모든 = [v for r in ys for v in r if v is not None] + [v for _n2, vs, _g in 선들 for v in vs if v is not None]
    구이 = [re.sub(r"\s*정상 수준$", "", 이) for 이 in 계열]          # 끝 이름 — 구분 이름(「범용 DRAM」) · 가로선은 「범용 DRAM 기준 91」
    끝글 = 구이 + ["%s 기준 %s" % (구이[k] if k < len(구이) else "", g) for _n2, vs, gs in 선들 for k, g in enumerate(gs) if k < len(vs) and vs[k] is not None]
    밑0 = min(모든) if (세로 and min(모든) > 0 and min(모든) > 0.5 * max(모든)) else 0.0      # 세로선 판(증가율 경로의 역산 곡선)은 값 가까이에서 연다
    눈, 밑, 위 = _가까운축(min(모든), max(모든)) if 밑0 else G._축(0.0, max(모든), 4)
    W, t, b = 360, 14 + 16 * len(세로), 34
    l = max(34, int(max([_폭(G._눈금수(g), 12.5) for g in 눈] + [0.0]) + 8))     # 눈금 글이 그림 안에(2026-10-23 — 스트림과 같은 병)
    rr = max([_폭(x, 12.5) * 1.04 for x in 끝글] + [40.0]) + 10       # v4e — 끝 이름이 그림 밖으로 나가지 않게(레터그림검사 ②)
    H = 230 + 16 * len(세로)
    pw, ph = W - l - rr, H - t - b
    x0, x1 = min(xs + [v for _n2, v, _g in 세로]), max(xs + [v for _n2, v, _g in 세로])

    def X(v):
        return l + pw * (v - x0) / ((x1 - x0) or 1.0)

    def Y(v):
        return t + ph * (1 - (v - 밑) / ((위 - 밑) or 1.0))
    # v4f(모션 리뷰 하-12 「웹판 2단계」) — 격자 칸에서만 서는 주가 단계(보간 없음): 칸마다 자리와 표의 글을 svg 에 싣고, 레터HTML 의 스크립트가
    # 범위 단추로 한 칸씩 옮긴다(정적 그림 · 인쇄 · 스크립트 꺼짐은 그대로). 숫자는 표의 칸 글뿐이다.
    기준0 = next((vs[0] for _n2, vs, _g in 선들 if vs and vs[0] is not None), None)
    처음 = min(range(len(xs)), key=lambda i: abs((ys[i][0] if ys[i] and ys[i][0] is not None else 1e30) - 기준0)) if 기준0 is not None else len(xs) // 2
    단계 = {"x": [round(X(x), 1) for x in xs], "y": [[(round(Y(v), 1) if v is not None else None) for v in r] for r in ys],
           "가격": [_맑게(r[0]) for r in 줄들], "값": [[_맑게(c) for c in r[1:]] for r in 줄들], "구분": 구이, "위": t, "아래": round(t + ph, 1), "처음": 처음}
    # 단추가 읽어 주는 말(2026-10-25 R5 마무리 — 레터HTML.단계JS 의 「말」) — 세로축이 무엇인지는 계열 이름이 말한다. 계열이 모두 「… 정상 수준」 이면
    # 수준 경로 판(말을 싣지 않는다 — 기본 「전제한 정상 수준」), 아니면 그 계열(증가율 경로 판의 「영구기간 영업이익률」)을 「전제한 ○○」 으로.
    # 종전에는 단추 글이 「정상 수준」 으로 박혀 있어 세로선 판(증가율 경로의 역산 곡선)에 단추를 달지 않았다.
    if 계열 and not all(re.search(r"정상 수준$", 이) for 이 in 계열):
        단계["말"] = ("전제한 %s" % 계열[0]) if len(계열) == 1 else "전제한 값"
    s = ['<svg class="viz viz-curve" viewBox="0 0 %d %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg" data-steps="%s">' % (
        W, H, _e(제목 or "그림"), _e(json.dumps(단계, ensure_ascii=False, separators=(",", ":"))))]
    for g in 눈:
        s.append('<line x1="%d" x2="%.1f" y1="%.1f" y2="%.1f" class="viz-grid"/>' % (l, l + pw, Y(g), Y(g)))
        s.append('<text x="%d" y="%.1f" class="viz-tick" text-anchor="end" dominant-baseline="middle">%s</text>' % (l - 4, Y(g), G._눈금수(g)))
    끝 = []
    for k, 이 in enumerate(계열):
        pts = [(X(xs[i]), Y(ys[i][k])) for i in range(len(xs)) if k < len(ys[i]) and ys[i][k] is not None]
        cls = ("vz-s1", "vz-s2", "vz-s3")[k % 3]
        if len(pts) >= 2:
            s.append('<polyline points="%s" class="%s"/>' % (" ".join("%.1f,%.1f" % p for p in pts), cls))
            for i in range(len(xs)):
                if k < len(ys[i]) and ys[i][k] is not None:
                    s.append('<circle cx="%.1f" cy="%.1f" r="7" class="viz-hit"><title>주가 %s · %s %s</title></circle>' % (
                        X(xs[i]), Y(ys[i][k]), _e(_맑게(줄들[i][0])), _e(이), _e(_맑게(줄들[i][k + 1]))))
            끝.append((구이[k], pts[-1][1], k))
    for 이, vs, gs in 선들:
        for k, v in enumerate(vs):
            if v is None:
                continue
            s.append('<line x1="%d" x2="%.1f" y1="%.1f" y2="%.1f" class="vz-ref vz-ref%d"><title>%s %s %s</title></line>' % (
                l, l + pw, Y(v), Y(v), k % 3 + 1, _e(이), _e(계열[k] if k < len(계열) else ""), _e(gs[k])))
            끝.append(("%s 기준 %s" % (구이[k] if k < len(구이) else "", gs[k]), Y(v), 10 + k))
    자리 = G._비켜놓기([(y, 0 if k < 10 else 1, 13) for _n2, y, k in 끝], 1, t, t + ph)
    for (이, y0, k), y in zip(끝, 자리):
        s.append('<text x="%.1f" y="%.1f" class="viz-tick%s" dominant-baseline="middle">%s</text>' % (l + pw + 5, y, " viz-strong" if k < 10 else "", _e(이)))
    for k, (이, v, g) in enumerate(세로):                       # 세로선 — 그 가로축 값(종가)의 자리 · 이름은 그림 위 띠에(선 · 곡선을 덮지 않게)
        xx = X(v)
        s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="vz-ref vz-ref2"><title>%s %s</title></line>' % (xx, xx, t, t + ph, _e(이), _e(g)))
        글 = "%s %s" % (이, g)
        w = _폭(글, 12.5)
        cx = min(max(xx, 4 + w / 2.0), W - 4 - w / 2.0)
        s.append('<text x="%.1f" y="%d" class="viz-tick viz-strong" text-anchor="middle">%s</text>' % (cx, 12 + 16 * k, _e(글)))
    걸 = max(1, int(math.ceil(len(xs) / 5.0)))
    간 = pw * (max(xs) - min(xs)) / (((x1 - x0) or 1.0) * max(1, len(xs) - 1))            # 눈금 글 사이 평균 간격 — 글이 길면(「72.21달러」) 더 솎는다(2026-10-25 R5)
    if 간 > 0:
        걸 = max(걸, int(math.ceil((max(_폭(_맑게(r[0]).replace(" 원", ""), 12.5) for r in 줄들) + 6) / 간)))
    끝글x = l
    for i, x in enumerate(xs):
        if i % 걸 == 0:
            g = _맑게(줄들[i][0]).replace(" 원", "")
            s.append('<text x="%.1f" y="%d" class="viz-tick" text-anchor="middle" style="font-size:12.5px">%s</text>' % (X(x), H - b + 18, _e(g)))
            끝글x = X(x) + _폭(g, 12.5) / 2.0
    s.append('<text x="%.1f" y="%d" class="viz-tick">주가</text>' % (max(l + pw + 5, 끝글x + 6), H - b + 18))     # v4f — 축 이름은 눈금 줄의 오른끝에(가운데 눈금 글 밑에 붙으면 「175만 주가」 로 읽혔다)
    s.append("</svg>")
    return "".join(s)


def _가까운축(lo, hi, 칸수=4):
    """0 을 품지 않는 축(값 가까이에서 연다 — 2026-10-25 R5 역산 곡선): 깔끔한 간격의 눈금과 그 범위를 조금 넓힌 끝."""
    폭 = (hi - lo) or abs(hi) or 1.0
    날 = 폭 / 칸수
    자 = 10 ** math.floor(math.log10(날))
    칸 = next(자 * k for k in (1, 2, 2.5, 5, 10) if 자 * k >= 날 - 1e-12)
    아 = math.floor(lo / 칸 + 1e-9) * 칸
    위 = math.ceil(hi / 칸 - 1e-9) * 칸
    n = int(round((위 - 아) / 칸))
    return [round(아 + 칸 * i, 10) for i in range(n + 1)], 아 - 0.04 * (위 - 아), 위 + 0.04 * (위 - 아)


def _분포끝글(xa, xb, y, 왼글, 오글, 왼끝, W, 크):
    """분포 띠 아래 10% · 90% 글(1.1.19). 띠가 두 글 폭보다 좁으면(이 평가의 점이 분포 밖 멀리 서 축이 늘면) 두 글이 겹친다 —
    그때는 「10%~90%」 한 글로 묶고, 그림 안에 들어가게 띠 왼끝(넘치면 띠 오른끝 · 그래도 넘치면 그림 오른끝)에 맞춘다. 폭은 그림검사 ② 와 같은 어림(`_폭`)."""
    틀 = '<text x="%.1f" y="%.1f" class="viz-tick" text-anchor="%s" dominant-baseline="middle">%s</text>'
    if xb - xa >= _폭(왼글, 크) + _폭(오글, 크) + 6:
        return [틀 % (xa, y, "start", _e(왼글)), 틀 % (xb, y, "end", _e(오글))]
    글 = "%s~%s" % (왼글, 오글)
    w = _폭(글, 크)
    if xa + w <= W - 2:
        return [틀 % (xa, y, "start", _e(글))]
    if xb - w >= 왼끝:
        return [틀 % (xb, y, "end", _e(글))]
    return [틀 % (W - 2, y, "end", _e(글))]


def 분포자리(표들, 제목=""):
    """그림 「분포자리」(2026-10-23 · 연구/레터그림_참고_외부사례.md) — 가정 칸이 같은 집단 회사들의 분포에서 서는 자리.
    표: 항목 · 집단 · 10% · 25% · 50% · 75% · 90% · 기준 첫 · 기준 끝. 줄마다 띠(10~90% — 맥락) · 진한 띠(25~75%) · 중앙값 눈금 · 이 평가의 점 둘(첫 · 끝).
    줄마다 제 눈금(항목이 달라 한 축으로 못 놓는다). 숫자는 표의 글 그대로(장부의 글)."""
    if not 표들:
        return ""
    머리, 줄들 = 표들[0]
    줄들 = [[_맑게(c) for c in r] for r in 줄들 if r and len(r) >= 9 and _맑게(r[0])]
    if not 줄들:
        return ""
    W, lx, x0, x1 = 360, 4, 128, 346
    줄높, 크 = 46, 12.5
    H = 12 + 줄높 * len(줄들) + 6
    s = ['<svg class="viz viz-dist" viewBox="0 0 %d %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">' % (W, H, _e(제목 or "같은 집단에서 서는 자리"))]
    for n, r in enumerate(줄들):
        항, 집 = r[0], r[1]
        q = [수읽기(c) for c in r[2:7]]
        첫, 끝 = 수읽기(r[7]), 수읽기(r[8])
        y = 12 + 줄높 * n + 22
        s.append('<text x="%d" y="%.1f" class="viz-name" dominant-baseline="middle">%s</text>' % (lx, y - 8, _e(G._접기폭(항, 118, 크)[0] if G._접기폭(항, 118, 크) else 항)))
        집줄 = G._접기폭(집, x0 - lx - 10, 12) or [집]        # 집단 이름이 길면(「같은 규모(…)(n곳)」) 두 줄로 — 띠를 덮지 않게(2026-10-23 W3 · 그림검사 ② · ⑤)
        집줄 = 집줄[:1] + ([" ".join(집줄[1:])] if len(집줄) > 1 else [])
        for k, t in enumerate(집줄):
            s.append('<text x="%d" y="%.1f" class="viz-tick" dominant-baseline="middle">%s</text>' % (lx, y + 8 + 12 * k, _e(t)))
        값들 = [v for v in q + [첫, 끝] if v is not None]
        if len(값들) < 3 or None in q:
            continue
        lo, hi = min(값들), max(값들)
        폭 = (hi - lo) or abs(hi) or 1.0
        lo, hi = lo - 0.08 * 폭, hi + 0.08 * 폭

        def X(v):
            return x0 + (x1 - x0) * (v - lo) / (hi - lo)
        s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="12" rx="2" class="vz-band-ctx"><title>10~90%%: %s~%s</title></rect>' % (X(q[0]), y - 6, max(X(q[4]) - X(q[0]), 1.5), _e(r[2]), _e(r[6])))
        s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="12" rx="2" class="vz-iqr"><title>25~75%%: %s~%s</title></rect>' % (X(q[1]), y - 6, max(X(q[3]) - X(q[1]), 1.5), _e(r[3]), _e(r[5])))
        s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="vz-med"><title>중앙값 %s</title></line>' % (X(q[2]), X(q[2]), y - 8, y + 8, _e(r[4])))
        s += _분포끝글(X(q[0]), X(q[4]), y + 17, r[2], r[6], x0, W, 크)
        같음 = 첫 is not None and 끝 is not None and abs(X(첫) - X(끝)) < 3.0        # 첫 · 끝이 같은 값이면 점 하나(가려진 점을 만들지 않는다 — 검사 ④)
        if 첫 is not None and not 같음:
            s.append('<circle cx="%.1f" cy="%.1f" r="4" class="vz-dot-hollow"><title>기준 첫 예측 %s</title></circle>' % (X(첫), y, _e(r[7])))
        if 끝 is not None:
            s.append('<circle cx="%.1f" cy="%.1f" r="4.5" class="vz-dot-flag"><title>기준 %s예측 %s</title></circle>' % (X(끝), y, "첫 · 마지막 " if 같음 else "마지막 ", _e(r[8])))
            앵 = "end" if X(끝) > (x0 + x1) / 2 else "start"
            s.append('<text x="%.1f" y="%.1f" class="viz-tick viz-strong" text-anchor="%s" dominant-baseline="middle">%s</text>' % (X(끝) + (-7 if 앵 == "end" else 7), y - 13, 앵, _e(r[8])))
    s.append("</svg>")
    return "".join(s)


# ══════════════════════════════════════════════════════════════════ 2026-10-25 R5 — 변수 절 그림(연구/레터재구성_20261025/조문_그림.md)
# 그림의 숫자는 모두 표의 글이다(장부 키로 찍힌 글) — 아래 그림은 표 글을 좌표로만 바꾼다. 색만으로 계열을 가르지 않는다(범례 · 셈 글 · 이름).

def _범례(이름들, 견본, 왼, W, 크=12.5, 견폭=15):
    """범례 — 이름마다 견본(svg 조각을 내는 함수(x, y))과 이름을 폭대로 흘려 놓고 넘치면 다음 줄. → (svg 조각들, 마지막 줄의 y)."""
    s, lx, ly = [], float(왼), 4.0
    for 이, f in zip(이름들, 견본):
        줄 = G._접기폭(이, W - 8 - 견폭, 크) or [이]
        w = 견폭 + max(_폭(z, 크) for z in 줄) * 1.04 + 14
        if lx + w > W - 4 and lx > 왼:
            lx, ly = float(왼), ly + 17
        s.append(f(lx, ly))
        for j, z in enumerate(줄):
            s.append('<text x="%.1f" y="%.1f" class="viz-tick">%s</text>' % (lx + 견폭, ly + 10 + 17 * j, _e(z)))
        lx += w
        if len(줄) > 1:
            lx, ly = float(왼), ly + 17 * len(줄)
    return s, ly


def 가로쌓기(표들, 제목=""):
    """가로로 쌓은 막대(그림 「WACC」 — 자본비용을 쌓은 셈) — 표: 막대 · 칸 · 값. 「합계」 칸은 막대 끝의 글이다. 칸 이름이 같으면 막대가 달라도
    같은 색(무위험이자율 따위). 막대 아래에 그 막대의 셈(「4.22% + 3.52% = 7.74%」 — 표의 글)을 적는다. 0 이하의 칸은 막대에 싣지 않는다(셈 글에는 남는다)."""
    if not 표들:
        return ""
    _m, 줄들 = 표들[0]
    막대 = []
    for r in 줄들:
        if len(r) < 3:
            continue
        이, 칸, 글 = _맑게(r[0]), _맑게(r[1]), _맑게(r[2])
        if not 이 or not 칸:
            continue
        if not 막대 or 막대[-1][0] != 이:
            막대.append([이, [], None])
        v = 수읽기(글)
        if 칸 == "합계":
            막대[-1][2] = (v, 글)
        elif v is not None:
            막대[-1][1].append((칸, v, 글))
    막대 = [b for b in 막대 if b[1]]
    if not 막대:
        return ""
    칸이름 = list(dict.fromkeys(칸 for _b, 칸들, _t in 막대 for 칸, v, _g in 칸들 if v > 0))
    색 = {이: k % 6 + 1 for k, 이 in enumerate(칸이름)}
    W = 360
    끝글 = [(t[1] if t else "") for _b, _c, t in 막대]
    rr = max([_폭(g, 12.5) * 1.04 + 12 for g in 끝글] + [24.0])
    x0, x1 = 4.0, W - rr
    합들 = [sum(v for _c, v, _g in 칸들 if v > 0) for _b, 칸들, _t in 막대] + [t[0] for _b, _c, t in 막대 if t and t[0] is not None]
    최대 = max(합들 + [1e-12])

    def X(v):
        return x0 + (x1 - x0) * v / 최대
    범, ly = _범례(칸이름, [(lambda x, y, k=색[이]: '<rect x="%.1f" y="%.1f" width="11" height="9" rx="2" class="vz-c%d"/>' % (x, y + 2, k)) for 이 in 칸이름], x0, W)
    셈들 = []
    for _b, 칸들, 합 in 막대:
        셈 = " + ".join(g for _c, _v, g in 칸들) + ((" = " + 합[1]) if 합 else "")
        셈들.append(G._접기폭(셈, W - 8, 12.5) or [셈])
    t = ly + 34
    높들 = [44 + 15 * len(z) for z in 셈들]
    H = int(t + sum(높들) - 12)
    s = ['<svg class="viz viz-hstack" viewBox="0 0 %d %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">' % (W, H, _e(제목 or "그림"))]
    s += 범
    y = t
    for (이, 칸들, 합), 셈, h in zip(막대, 셈들, 높들):
        s.append('<text x="%.1f" y="%.1f" class="viz-label viz-strong" style="font-size:12.5px">%s</text>' % (x0, y, _e(이)))
        누 = 0.0
        for 칸, v, g in 칸들:
            if v <= 0:
                continue
            s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="16" class="vz-c%d"><title>%s %s %s</title></rect>' % (
                X(누), y + 6, max(X(누 + v) - X(누), 1.0), 색[칸], _e(이), _e(칸), _e(g)))
            누 += v
        if 합:
            s.append('<text x="%.1f" y="%.1f" class="viz-tick viz-strong" dominant-baseline="middle">%s</text>' % (X(max(누, 합[0] or 0.0)) + 6, y + 14, _e(합[1])))
        for j, z in enumerate(셈):
            s.append('<text x="%.1f" y="%.1f" class="viz-tick">%s</text>' % (x0, y + 38 + 15 * j, _e(z)))
        y += h
    s.append("</svg>")
    return "".join(s)


def 표본(표들, 제목=""):
    """표본 점(그림 「표본」 — 유사기업 베타 따위) — 표: 이름 · 값. 줄마다 점 하나, 「(선)」 으로 끝나는 줄은 세로 기준선(대표값 · 채택값 —
    이름은 그림 위 띠에 줄마다). 한 눈금(표본의 단위가 같다)."""
    if not 표들:
        return ""
    _m, 줄들 = 표들[0]
    점 = [(_맑게(r[0]), 수읽기(r[1]), _맑게(r[1])) for r in 줄들 if len(r) >= 2 and not _맑게(r[0]).endswith("(선)")]
    선 = [(re.sub(r"\s*\(선\)$", "", _맑게(r[0])), 수읽기(r[1]), _맑게(r[1])) for r in 줄들 if len(r) >= 2 and _맑게(r[0]).endswith("(선)")]
    점 = [x for x in 점 if x[1] is not None]
    선 = [x for x in 선 if x[1] is not None]
    if len(점) < 2:
        return ""
    W, lx, 크 = 360, 4, 12.5
    값폭 = max(_폭(g, 크) for _n2, _v, g in 점) * 1.04
    px0, px1 = 136.0, W - 4 - 값폭 - 12
    vs = [v for _n2, v, _g in 점 + 선]
    lo, hi = min(vs), max(vs)
    폭 = (hi - lo) or abs(hi) or 1.0
    lo, hi = lo - 0.08 * 폭, hi + 0.08 * 폭

    def X(v):
        return px0 + (px1 - px0) * (v - lo) / (hi - lo)
    위 = 12 + 16 * len(선) + 6
    줄 = [G._접기폭(n2, px0 - lx - 10, 12) or [n2] for n2, _v, _g in 점]
    높 = [max(24, 14 * len(z) + 8) for z in 줄]
    H = int(위 + sum(높) + 8)
    s = ['<svg class="viz viz-sample" viewBox="0 0 %d %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">' % (W, H, _e(제목 or "그림"))]
    for k, (n2, v, g) in enumerate(선):
        xx = X(v)
        s.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" class="vz-ref vz-ref%d"><title>%s %s</title></line>' % (xx, xx, 위 - 2, H - 4, (k + 1) % 3 + 1, _e(n2), _e(g)))
        글 = "%s %s" % (n2, g)
        w = _폭(글, 크)
        cx = min(max(xx, lx + w / 2.0), W - 4 - w / 2.0)
        s.append('<text x="%.1f" y="%d" class="viz-tick viz-strong" text-anchor="middle">%s</text>' % (cx, 12 + 16 * k, _e(글)))
    y = 위
    for (n2, v, g), z, h in zip(점, 줄, 높):
        가 = y + h / 2.0
        for j, tt in enumerate(z):
            s.append('<text x="%d" y="%.1f" class="viz-name" dominant-baseline="middle">%s</text>' % (lx, 가 + 14 * (j - (len(z) - 1) / 2.0), _e(tt)))
        s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="viz-grid"/>' % (px0, px1, 가, 가))
        s.append('<circle cx="%.1f" cy="%.1f" r="4.5" class="vz-dot-acc"><title>%s %s</title></circle>' % (X(v), 가, _e(n2), _e(g)))
        s.append('<text x="%d" y="%.1f" class="viz-tick viz-value" text-anchor="end" dominant-baseline="middle">%s</text>' % (W - 4, 가, _e(g)))
        y += h
    s.append("</svg>")
    return "".join(s)


def 전파(표들, 제목=""):
    """시나리오 × 줄별 변화(그림 「전파」) — 표: 항목 · 쪽마다(「비관 − 기준」 · 「낙관 − 기준」) 기준 대비 변화율 글 · 「같음」 · 「—」.
    줄마다 쪽 막대(0 이 가운데 · 한 눈금), 오른쪽 열에 값 글. 막대 색은 쪽(범례 · 값 글의 차례로도 가른다), 「같음」 은 0 위의 빈 점."""
    if not 표들:
        return ""
    머리, 줄들 = 표들[0]
    쪽 = [_맑게(h) for h in 머리[1:3]]
    줄들 = [[_맑게(c) for c in r] + [""] * (3 - len(r)) for r in 줄들 if r and _맑게(r[0])]
    if len(쪽) < 1 or len(줄들) < 2:
        return ""
    W, lx, 크 = 360, 4, 12.5
    값들 = [수읽기(r[1 + k]) for r in 줄들 for k in range(len(쪽))]
    m = max([abs(v) for v in 값들 if v is not None] + [1e-12])
    값폭 = max([_폭(r[1 + k], 크) for r in 줄들 for k in range(len(쪽))] + [20.0]) * 1.04
    cx0, cx1 = 124.0, W - 4 - 값폭 - 10
    중 = (cx0 + cx1) / 2.0

    def X(v):
        return 중 + (cx1 - cx0) / 2.0 * v / m
    범, ly = _범례(쪽, [(lambda x, y, k=k: '<rect x="%.1f" y="%.1f" width="11" height="9" rx="2" class="vz-c%d"/>' % (x, y + 2, (3, 1)[k % 2])) for k in range(len(쪽))], lx, W)
    위 = ly + 24
    이줄 = [G._접기폭(r[0], cx0 - lx - 8, 크) or [r[0]] for r in 줄들]
    높 = [max(14 * len(쪽) + 8, 14 * len(z) + 6) for z in 이줄]
    H = int(위 + sum(높) + 6)
    s = ['<svg class="viz viz-spread" viewBox="0 0 %d %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">' % (W, H, _e(제목 or "그림"))]
    s += 범
    s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="viz-axis"/>' % (중, 중, 위 - 4, H - 4))
    y = 위
    for r, z, h in zip(줄들, 이줄, 높):
        가 = y + h / 2.0
        for j, tt in enumerate(z):
            s.append('<text x="%d" y="%.1f" class="viz-name" dominant-baseline="middle" style="font-size:12.5px">%s</text>' % (lx, 가 + 14 * (j - (len(z) - 1) / 2.0), _e(tt)))
        for k in range(len(쪽)):
            yk = 가 + 14 * (k - (len(쪽) - 1) / 2.0)
            g = r[1 + k]
            v = 수읽기(g)
            if g == "같음":
                s.append('<circle cx="%.1f" cy="%.1f" r="3" class="vz-dot-hollow"><title>%s %s 같음</title></circle>' % (중, yk, _e(r[0]), _e(쪽[k])))
            elif v is not None and abs(v) > 0:
                a, b = sorted((X(0), X(v)))
                s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="9" rx="1.5" class="vz-c%d"><title>%s %s %s</title></rect>' % (
                    a, yk - 4.5, max(b - a, 1.2), (3, 1)[k % 2], _e(r[0]), _e(쪽[k]), _e(g)))
            if g:
                s.append('<text x="%d" y="%.1f" class="viz-tick viz-value%s" text-anchor="end" dominant-baseline="middle" style="font-size:12.5px">%s</text>' % (
                    W - 4, yk, "" if (v is not None or g == "같음") else " viz-muted", _e(g)))
        y += h
    s.append("</svg>")
    return "".join(s)


def _자리꼴(이름):
    """범위띠 점의 꼴 — (순위, 갈래, 반지름): 가격 · 종가 = 대비색(가장 위) · 기준 · 채택 · 마지막 · 끝 = 초점색 · 첫 = 빈 점 · 그 밖 = 맥락색 작은 점."""
    if "가격" in 이름 or "종가" in 이름:
        return 3, "vz-dot-flag", 4.5
    if "첫" in 이름:
        return 1, "vz-dot-hollow", 4.0
    if any(w in 이름 for w in ("기준", "채택", "마지막", "끝", "이 평가")):
        return 2, "vz-dot-acc", 4.5
    return 0, "vz-dot-ctx", 3.5


_띠꼴 = ("vz-band-ctx", "vz-iqr", "vz-band-out")


def 범위띠(표들, 제목=""):
    """가정 칸이 범위의 어디에 서나(그림 「범위띠」 · 「역산자」 — 2026-10-25 R5) — 표: 항목 · 「○○ 아래」 · 「○○ 위」 짝(띠) · 그 밖의 열(점).
    띠는 짝마다 한 겹(첫째 회색 면 · 둘째 초점색 테두리 면 · 셋째 점선 테두리), 점은 열 이름으로 꼴을 고른다(`_자리꼴`). 줄마다 제 눈금(항목의
    단위가 다르다). 같은 자리에 겹치는 점은 순위가 높은 것만 그린다(가려진 점을 만들지 않는다 — 검사 ④). 점 글은 초점 · 대비 점에만(괄호 덧말은 뗀다)."""
    if not 표들:
        return ""
    머리, 줄들 = 표들[0]
    열 = [_맑게(h) for h in 머리[1:]]
    띠, 점 = [], []
    i = 0
    while i < len(열):
        if 열[i].endswith(" 아래") and i + 1 < len(열) and 열[i + 1] == 열[i][:-3] + " 위":
            띠.append((열[i][:-3], i, i + 1))
            i += 2
        else:
            점.append((열[i], i))
            i += 1
    줄들 = [[_맑게(c) for c in r] for r in 줄들 if r and _맑게(r[0])]
    if not 줄들 or not (띠 or len(점) >= 2):
        return ""
    W, lx, x0, x1, 크 = 360, 4, 132, 346, 12.5
    견 = [(lambda x, y, k=k: '<rect x="%.1f" y="%.1f" width="13" height="9" rx="2" class="%s"/>' % (x, y + 2, _띠꼴[min(k, 2)])) for k in range(len(띠))]
    견 += [(lambda x, y, c=_자리꼴(n2)[1], r=_자리꼴(n2)[2]: '<circle cx="%.1f" cy="%.1f" r="%.1f" class="%s"/>' % (x + 5.5, y + 6.5, r, c)) for n2, _j in 점]
    범, ly = _범례([n2 for n2, _a, _b in 띠] + [n2 for n2, _j in 점], 견, lx, W, 견폭=18)
    줄높 = 50
    위 = ly + 42
    이줄들 = [G._접기폭(r[0], x0 - lx - 10, 크) or [r[0]] for r in 줄들]      # N6 — 접힌 줄을 다 둔다(셋째 줄을 둘째에 이어 붙이면 띠를 덮었다)
    높들 = [max(줄높, 14 * len(z) + 22) for z in 이줄들]                     # 이름 줄 수만큼 자리
    ys = [위 + sum(높들[:n]) + (높들[n] - 줄높) / 2.0 for n in range(len(줄들))]
    H = int(위 + sum(높들) - 18)
    s = ['<svg class="viz viz-range" viewBox="0 0 %d %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">' % (W, H, _e(제목 or "그림"))]
    s += 범
    for n, r in enumerate(줄들):
        y = ys[n]
        이줄 = 이줄들[n]
        for k, tt in enumerate(이줄):
            s.append('<text x="%d" y="%.1f" class="viz-name" dominant-baseline="middle">%s</text>' % (lx, y - 7 * max(1, len(이줄) - 1) + 14 * k, _e(tt)))

        def 칸(j, r=r):
            return r[1 + j] if 1 + j < len(r) else ""
        띠값 = [(n2, 수읽기(칸(a)), 수읽기(칸(b)), 칸(a), 칸(b), k) for k, (n2, a, b) in enumerate(띠)]
        띠값 = [x for x in 띠값 if x[1] is not None and x[2] is not None]
        점값 = [(n2, 수읽기(칸(j)), 칸(j)) for n2, j in 점]
        점값 = [x for x in 점값 if x[1] is not None]
        vs = [v for x in 띠값 for v in (x[1], x[2])] + [v for _n2, v, _g in 점값]
        if not vs:
            continue
        lo, hi = min(vs), max(vs)
        폭 = (hi - lo) or abs(hi) or 1.0
        lo, hi = lo - 0.08 * 폭, hi + 0.08 * 폭

        def X(v, lo=lo, hi=hi):
            return x0 + (x1 - x0) * (v - lo) / (hi - lo)
        s.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" class="viz-grid"/>' % (x0, x1, y, y))
        for n2, a, b, ga, gb, k in 띠값:
            a2, b2 = sorted((a, b))
            s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="12" rx="2" class="%s"><title>%s: %s ~ %s</title></rect>' % (
                X(a2), y - 6, max(X(b2) - X(a2), 1.5), _띠꼴[min(k, 2)], _e(n2), _e(ga), _e(gb)))
        if 띠값:                                                # 첫 띠의 두 끝 글(띠 아래) — 겹치면 민다
            _n2, a, b, ga, gb, _k = 띠값[0]
            짝 = sorted(((X(a), re.sub(r"\([^()]*\)", "", ga).strip()), (X(b), re.sub(r"\([^()]*\)", "", gb).strip())))
            if 짝[0][1] == 짝[1][1]:
                짝 = 짝[:1]
            항 = [(짝[0][0] + _폭(짝[0][1], 12.5) / 2.0, _폭(짝[0][1], 12.5))] + ([(짝[1][0] - _폭(짝[1][1], 12.5) / 2.0, _폭(짝[1][1], 12.5))] if len(짝) > 1 else [])
            for xx, (_x, g) in zip(G._가로놓기(항, lx, W - 4, 6.0), 짝):
                s.append('<text x="%.1f" y="%.1f" class="viz-tick" text-anchor="middle" dominant-baseline="middle" style="font-size:12.5px">%s</text>' % (xx, y + 17, _e(g)))
        놓인 = []
        for n2, v, g in sorted(점값, key=lambda t: -_자리꼴(t[0])[0]):
            순, 갈, rr = _자리꼴(n2)
            if any(abs(X(v) - X(v2)) < rr + r2 - 1.0 for _n3, v2, _g, _s, _c, r2 in 놓인):
                continue
            놓인.append((n2, v, g, 순, 갈, rr))
        for n2, v, g, 순, 갈, rr in sorted(놓인, key=lambda t: t[3]):
            s.append('<circle cx="%.1f" cy="%.1f" r="%.1f" class="%s"><title>%s %s</title></circle>' % (X(v), y, rr, 갈, _e(n2), _e(g)))
        고른 = [x for x in 놓인 if x[3] >= 2] or sorted(놓인, key=lambda t: -t[3])[:1]       # 초점 · 대비 점이 없으면 가장 높은 순위의 점 하나에 글
        글들 = sorted([(X(v), re.sub(r"\([^()]*\)", "", g).strip()) for _n2, v, g, _s, _c, _r in 고른], key=lambda t: t[0])
        if 글들:
            for xx, (_x, g) in zip(G._가로놓기([(x, _폭(g, 크)) for x, g in 글들], lx, W - 4, 6.0), 글들):
                s.append('<text x="%.1f" y="%.1f" class="viz-tick viz-strong" text-anchor="middle">%s</text>' % (xx, y - 12, _e(g)))
    s.append("</svg>")
    return "".join(s)


# ══════════════════════════════════════════════════════════════════ 범위(결론 — 레터 v27 7단계)
def 범위(표들, 제목=""):
    """세 시나리오의 주당가치와 평가기준일 종가(그림 「범위」 — 3분 레터 결론 · 어느 회사에나). 표: 구분 · 주당가치. 「… 시나리오」 줄은 점
    (기준은 1계열 · 굵은 이름, 비관 · 낙관은 2계열), 비관에서 낙관까지 띠, 「종가」 가 든 줄은 세로선. 값 글은 점 위(시나리오) · 축 아래(종가)에
    겹치지 않게 놓는다. 숫자는 표의 글 그대로다.
    축은 세 시나리오에 맞춘다. 종가가 시나리오 폭의 1.5배 넘게 떨어져 있으면 축에 넣지 않고 그쪽 끝에 삼각 표지와 「그림 밖」 을 단다(종가 하나 때문에
    세 점이 한쪽에 몰려 서로 가리던 것 — 테슬라 닻). 점끼리 겹치면 기준을 축에 두고 다른 점을 축 아래로 비킨다."""
    if not 표들:
        return ""
    _머, 줄들 = 표들[0]
    점들, 종 = [], None
    for r in 줄들:
        if len(r) < 2:
            continue
        이, 글 = _맑게(r[0]), _맑게(r[1])
        v = 수읽기(글)
        if v is None:
            continue
        if "종가" in 이:
            종 = (이, 글, v)
        else:
            점들.append((이.replace(" 시나리오", ""), 글, v))
    if len(점들) < 2:
        return ""
    시값 = [v for _i, _g, v in 점들]
    폭 = (max(시값) - min(시값)) or abs(max(시값)) * 0.1 or 1.0
    종안 = bool(종) and min(시값) - 1.5 * 폭 <= 종[2] <= max(시값) + 1.5 * 폭
    값 = 시값 + ([종[2]] if 종안 else [])
    lo, hi = min(값), max(값)
    여 = (hi - lo) * 0.06 or (abs(hi) * 0.1) or 1.0
    lo, hi = lo - 여, hi + 여
    W, l, r_ = 360, 12, 12
    pw = W - l - r_
    축y = 50
    H = 96 if 종 else 72

    def X(v):
        return l + (v - lo) / ((hi - lo) or 1.0) * pw
    s = ['<svg class="viz viz-range" viewBox="0 0 %d %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">' % (W, H, _e(제목 or "그림"))]
    s.append('<line x1="%d" x2="%d" y1="%d" y2="%d" class="viz-axis"/>' % (l, W - r_, 축y, 축y))
    시 = {i: v for i, _g, v in 점들}
    if "비관" in 시 and "낙관" in 시:
        a, b = sorted((X(시["비관"]), X(시["낙관"])))
        s.append('<rect x="%.1f" y="%d" width="%.1f" height="10" class="vz-band vz-band-s"/>' % (a, 축y - 5, max(2.0, b - a)))     # 장식 띠(대비 검사 밖 — 값은 점과 글이 싣는다)
    종x = None
    if 종 and 종안:
        종x = X(종[2])
        s.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" class="vz-close"/>' % (종x, 종x, 축y - 9, 축y + 12))
    elif 종:                                                   # 축 밖 — 그쪽 끝에 바깥을 가리키는 삼각 표지
        오른 = 종[2] > max(시값)
        종x = (W - r_) if 오른 else l
        d = 1 if 오른 else -1
        s.append('<path d="M%.1f %d L%.1f %d L%.1f %d Z" class="vz-close-mark"/>' % (종x - 7 * d, 축y - 6, 종x, 축y, 종x - 7 * d, 축y + 6))
    # 점 — 기준을 먼저 축에 놓고, 다른 점이 앞서 놓은 점과 겹치면 축 아래로 비킨다(늦게 그린 점이 앞 점을 가리지 않게)
    차례 = sorted(range(len(점들)), key=lambda k: (점들[k][0] != "기준", k))
    놓은 = []
    for k in 차례:
        i, _g, v = 점들[k]
        r = 5.5 if i == "기준" else 4.5
        x = X(v)
        cy = 축y
        for 후보 in (축y, 축y + 11, 축y + 22):
            if all(abs(x - px) >= r + pr + 1 or abs(후보 - py) >= r + pr + 1 for px, py, pr in 놓은):
                cy = 후보
                break
        놓은.append((x, cy, r))
        s.append('<circle cx="%.1f" cy="%d" r="%s" class="%s"/>' % (x, cy, r, "viz-dot" if i == "기준" else "viz-dot-2"))
    글들 = [("%s %s" % (i, g), X(v), 0 if i == "기준" else 1, i == "기준") for i, g, v in 점들]
    폭들 = [_폭(t, 12.5) * 1.06 for t, _x, _r, _b in 글들]
    # 바라는 자리를 먼저 그림 안으로 당긴다(끝의 점 — 박은 기준 이름표가 그림 밖으로 나가던 것 · 생성글게이트 시험 ⑬)
    자리 = G._비켜놓기([(min(max(x, l + w / 2), W - r_ - w / 2), 순, w) for (t, x, 순, _b), w in zip(글들, 폭들)], 8, l, W - r_)
    for (t, _x, _순, 굵), x in zip(글들, 자리):
        s.append('<text x="%.1f" y="%d" class="viz-label%s" text-anchor="middle">%s</text>' % (x, 축y - 16, " viz-strong" if 굵 else "", _e(t)))
    if 종:
        t = "%s %s%s" % (종[0], 종[1], "" if 종안 else " · 그림 밖")
        w = _폭(t, 12.5) * 1.06
        x = min(max(종x, l + w / 2), W - r_ - w / 2)
        아래 = max([cy + r for _x, cy, r in 놓은] + [축y + 12])
        s.append('<text x="%.1f" y="%d" class="viz-label" text-anchor="middle">%s</text>' % (x, 아래 + 18, _e(t)))
        H = max(H, int(아래 + 18 + 8))
        s[0] = s[0].replace('viewBox="0 0 %d 96"' % W, 'viewBox="0 0 %d %d"' % (W, H))
    s.append("</svg>")
    return "".join(s)


def 원가두선(표들, 제목=""):
    """매출과 매출원가 지수 두 선(그림 「원가두선」 — `레터회사그림`) — 스트림과 같고 눈금은 값의 최소에서(두 선의 간격이 보이게)."""
    return 스트림(표들, 제목, 바닥0=False)


그림들 = {"연결": 연결, "스트림": 스트림, "쌓기": 쌓기, "비중": 비중, "공장": 공장, "격자": 격자, "곡선": 곡선, "분포자리": 분포자리,
        # 2026-10-25 R5 — 변수 절 그림. 이름이 다른 종류는 같은 그리개를 쓰되 그림 규칙(`그림규칙.json`)이 절마다 종류로 센다
        "동인": 쌓기, "레버리지": 쌓기, "투자": 쌓기, "FCFF": 쌓기, "TV몫": 쌓기, "인원": 스트림, "회전": 스트림, "정합": 공장,
        "WACC": 가로쌓기, "가로쌓기": 가로쌓기, "표본": 표본, "전파": 전파, "범위띠": 범위띠, "역산자": 범위띠,
        # 레터 v27 7단계(다) — 회사의 구조가 고르는 그림(`레터회사그림`) · 결론의 범위
        "남은기간": 쌓기, "저량": 쌓기, "결손금": 쌓기, "원가두선": 원가두선, "범위": 범위}
HTML그림 = ("연결",)                 # 그림이 곧 글(상자) — 「그림의 숫자」 를 따로 달지 않는다

CSS = """
.viz .vz-s1{fill:none; stroke:var(--s1); stroke-width:2.4; stroke-linejoin:round; stroke-linecap:round}
.viz .vz-s2{fill:none; stroke:var(--s2); stroke-width:1.8; stroke-dasharray:6 3; stroke-linejoin:round}
.viz .vz-s3{fill:none; stroke:var(--vz-ctx); stroke-width:1.8; stroke-dasharray:2 3; stroke-linecap:round}
.viz .vz-act{fill:var(--ink); stroke:var(--paper); stroke-width:1.5}
.viz .vz-band-s{fill:var(--s1-soft)} .viz .vz-close{stroke:var(--ink); stroke-width:1.5} .viz .vz-close-mark{fill:var(--ink)}
.viz .vz-c1{fill:var(--s1)} .viz .vz-c2{fill:var(--vz-c2)} .viz .vz-c3{fill:var(--s2)}
.viz .vz-c4{fill:var(--vz-c4)} .viz .vz-c5{fill:var(--vz-c5)} .viz .vz-c6{fill:var(--vz-c6)}
.viz-stack rect[class^="vz-c"]{stroke:var(--paper); stroke-width:.8}
.viz .vz-ln{fill:none; stroke:var(--ink); stroke-width:1.8}
.viz .vz-ln-dot{fill:var(--ink); stroke:var(--paper); stroke-width:1.5}
.viz .vz-ref{stroke:var(--ink-2); stroke-width:1.3; stroke-dasharray:4 3}
.viz .vz-ref1{stroke:var(--s1)} .viz .vz-ref2{stroke:var(--s2)} .viz .vz-ref3{stroke:var(--vz-ctx)}
.viz .vz-hi{fill:var(--s1)} .viz .vz-lo{fill:var(--s2)}
.viz .vz-band-ctx{fill:var(--rule); stroke:var(--vz-ctx); stroke-width:1}
.viz .vz-iqr{fill:var(--s1-soft); stroke:var(--s1); stroke-width:1.2}
.viz .vz-med{stroke:var(--ink); stroke-width:2}
.viz .vz-base{fill:none; stroke:var(--ink); stroke-width:2}
.viz .vz-band-out{fill:none; stroke:var(--vz-ctx); stroke-width:1.2; stroke-dasharray:3 2}
.viz-hstack rect[class^="vz-c"], .viz-spread rect[class^="vz-c"]{stroke:var(--paper); stroke-width:.8}
.flow{display:flex; flex-direction:column; align-items:stretch; gap:0; margin:.6rem 0 .4rem; font-size:.84rem; line-height:1.45}
.flow-streams{display:flex; flex-direction:column; gap:.45rem}
.flow-pair{display:grid; grid-template-columns:minmax(0,1fr) auto minmax(0,1fr); gap:.4rem; align-items:stretch}
.flow-times{align-self:center; font-weight:700; color:var(--muted)}
.flow-box{border:1px solid var(--rule-2); border-left:3px solid var(--accent); border-radius:3px; background:var(--paper-2); padding:.4rem .55rem;
  display:flex; flex-direction:column; gap:.12rem; min-width:0}
.flow-box.flow-main{border-left-color:var(--ink-2)}
.flow-tag{font-size:.7rem; letter-spacing:.04em; color:var(--muted)}
.flow-box b{font-weight:700; color:var(--ink)}
.flow-a{color:var(--ink-2); font-size:.8rem; overflow-wrap:anywhere}
.flow-v{color:var(--accent); font-weight:500; font-variant-numeric:tabular-nums}
.flow-arrow{height:1.1rem; position:relative}
.flow-arrow::before{content:""; position:absolute; left:50%; top:.1rem; bottom:.25rem; border-left:1.5px solid var(--rule-2)}
.flow-arrow::after{content:""; position:absolute; left:calc(50% - 4px); bottom:0; border:4.5px solid transparent; border-top:6px solid var(--muted); border-bottom:0}
@media (max-width:640px){ .flow-pair{grid-template-columns:1fr} .flow-times{justify-self:center} }
@media (hover:hover) and (pointer:fine){
  .flow:has(.flow-box:hover) .flow-box, .flow:has(.flow-box:hover) .flow-arrow, .flow:has(.flow-box:hover) .flow-times{opacity:.35}
  .flow .flow-box:hover, .flow > .flow-box:hover ~ .flow-box, .flow > .flow-box:hover ~ .flow-arrow, .flow > .flow-box:hover ~ .flow-streams .flow-box,
  .flow-streams:has(.flow-box:hover) ~ .flow-box, .flow-streams:has(.flow-box:hover) ~ .flow-arrow{opacity:1}
  .flow .flow-box:hover{border-left-color:var(--flag)} }
@media print{ .flow{font-size:8pt} .flow-box{padding:.15rem .35rem; break-inside:avoid} .flow-arrow{height:.6rem} .flow-pair{grid-template-columns:minmax(0,1fr) auto minmax(0,1fr)} }
.viz .vz-step-line{stroke:var(--ink-2); stroke-width:1; stroke-dasharray:3 3}
.viz .vz-step-dot{stroke:var(--paper); stroke-width:2}
.viz .vz-step-dot1{fill:var(--s1)} .viz .vz-step-dot2{fill:var(--s2)} .viz .vz-step-dot3{fill:var(--vz-ctx)}
.step-ctl{display:flex; flex-wrap:wrap; align-items:center; gap:.3rem .7rem; max-width:28rem; margin:.3rem 0 .1rem; font-size:13px; color:var(--ink-2)}
.step-ctl label{display:flex; align-items:center; gap:.5rem; flex:1 1 12rem; min-width:0}
.step-ctl input[type=range]{flex:1; min-width:6rem; accent-color:var(--accent); min-height:28px}
.step-ctl output{font-variant-numeric:tabular-nums; color:var(--ink)}
@media (pointer:coarse){ .step-ctl input[type=range]{min-height:44px} }
@media print{ .step-ctl, .viz .vz-step-mark{display:none !important} }
"""

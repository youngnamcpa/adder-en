# -*- coding: utf-8 -*-
"""레터그림 — 3분 레터의 그림 셋을 그린다 (R1b · L3).

계산하지 않는다. 레터(마크다운)에 실린 그림 표의 글(장부의 숫자를 꼴대로 찍은 글)을 읽어 좌표로만 바꾼다.
그림의 숫자는 모두 그 표에 있고, 표의 숫자는 레터 게이트가 장부와 맞댄다(⑦). 표는 HTML 에서 그림 밑의 「그림의 숫자」로 접힌다.

  마크다운의 꼴 — 표지 줄 「<!-- 그림:길 -->」 · 「<!-- 그림:자 -->」 · 「<!-- 그림:신호 -->」, 그 아래 굵은 제목 줄, 그 아래 표(길은 둘)
  길(표들)     그림 1 — 가격 변수의 길(기준 기간 = 100). 첫 표: 머리 = 기간, 첫 줄 = 그리는 계열. 둘째 표: 가로선(이름 · 구분마다 값)
  자(표)       그림 2 — 주당가치와 그 값이 전제하는 정상 수준. 줄 = 이름 · 주당가치 · 구분마다 바닥(「—」 면 다른 가정까지 바뀐 시나리오의 점)
  신호(표)     그림 3 — 신호등. 줄 = 신호 · 문턱 · 켜지면 · 지금 · 상태(켜짐 · 다가감 · 꺼짐) — HTML 카드
  띠(표)       3분 레터 첫 화면의 요약 띠 — 줄 = 요약 · 값 · 덧말(1~4줄) — HTML(통독 v4 상-3)
글 자리(통독 v4) — 이름 · 값 글은 `_비켜놓기`(세로, 차례 보존 · 점과 짝인 글은 제자리) · `_가로놓기`(눈금 이름)로 겹치지 않게 놓고,
모든 글에 바탕색 테두리(halo)를 둘러 선 위에서도 읽힌다. 모션 프레임은 같은 함수에 진행 값만 주므로 자리 셈도 같다.

그림은 휴대폰 폭(약 360px)에 맞춰 그리고 넓은 화면에서는 늘어난다. 색은 페이지의 CSS 변수(--viz-*)를 따른다 — 밝은 · 어두운 화면 ·
인쇄가 같은 그림을 쓴다. 색은 dataviz 기준 팔레트의 1 · 2번(파랑 · 주황)과 상태색(좋음 · 주의 · 위험)이고 검사기를 지났다.
"""
from __future__ import annotations

import html
import math
import re

_수 = re.compile(r"([−\-+]?)(\d[\d,]*(?:\.\d+)?)\s*(만|억|조)?\s*(원|달러|엔|유로|%)?")


def 수읽기(글):
    """「130만 원」 → 1300000 · 「3.3만 원」 → 33000 · 「1,303,162원」 → 1303162 · 「38」 → 38 · 「—」 → None."""
    t = re.sub(r"<[^>]+>|\*", "", "%s" % (글 or "")).strip()
    m = _수.search(t)
    if not m or t in ("—", "-"):
        return None
    v = float(m.group(2).replace(",", ""))
    v *= {"만": 1e4, "억": 1e8, "조": 1e12}.get(m.group(3) or "", 1.0)
    return -v if m.group(1) in ("−", "-") else v


def _e(s):
    return html.escape("%s" % s, quote=True)


# ── 글 자리 잡기(통독 v4 디자이너 상-4 · 중-6 · 중-8) — 그림마다 따로 짜지 않고 같은 셈을 쓴다. 글자 폭은 어림(한글 1em · 숫자 0.58em)이다.
def _폭(글, 크기):
    """글의 어림 폭(그림 단위) — 한글 · 한자 1em, 숫자 · 라틴 0.58~0.62em, 공백 0.3em, 괄호 · 점 0.35em."""
    w = 0.0
    for ch in "%s" % 글:
        o = ord(ch)
        if ch == " ":
            w += 0.3
        elif 0xAC00 <= o <= 0xD7A3 or 0x3130 <= o <= 0x318F or 0x4E00 <= o <= 0x9FFF:
            w += 1.0
        elif ch in "()[]·,.:;'|!":
            w += 0.35
        elif ch.isdigit():
            w += 0.58
        else:
            w += 0.62
    return w * 크기


def _접기폭(글, 폭, 크기):
    """낱말 사이에서 줄을 접는다 — 한 줄의 어림 폭이 폭(그림 단위)을 넘지 않게(한 낱말이 넘으면 그 낱말만 한 줄)."""
    줄, 지금 = [], ""
    for w in ("%s" % 글).split():
        시험 = (지금 + " " + w).strip()
        if 지금 and _폭(시험, 크기) > 폭:
            줄.append(지금)
            지금 = w
        else:
            지금 = 시험
    return 줄 + ([지금] if 지금 else [])


def _비켜놓기(원함, 틈, 위=None, 아래=None):
    """세로 한 줄로 글 상자를 놓는다. 원함 = [(가운데 y, 순위, 높이)] → 놓은 가운데 y 목록.
    상자의 위아래 차례는 원래 자리의 차례 그대로 둔다(선과 이름의 차례가 뒤집히지 않게). 순위 0 인 상자는 제자리에 박고(점과 글의 짝 — 서로
    겹치면 뒤엣것은 박지 않는다) 나머지를 겹치지 않게(높이 반씩 + 틈) 밀어낸다. 위 · 아래 끝을 넘지 않게 되민다."""
    n = len(원함)
    if not n:
        return []
    차 = sorted(range(n), key=lambda k: (원함[k][0], 원함[k][1]))
    자리 = [float(원함[k][0]) for k in range(n)]
    h = [float(원함[k][2]) for k in range(n)]
    박 = set()
    for k in sorted(range(n), key=lambda k: 원함[k][1]):
        if 원함[k][1] == 0 and all(abs(자리[k] - 자리[j]) >= (h[k] + h[j]) / 2.0 + 틈 for j in 박):
            박.add(k)
    for _ in range(400):
        움직 = False
        for a, b in zip(차, 차[1:]):
            필요 = (h[a] + h[b]) / 2.0 + 틈
            겹 = 필요 - (자리[b] - 자리[a])
            if 겹 > 1e-6:
                if a in 박 and b not in 박:
                    자리[b] += 겹
                elif b in 박 and a not in 박:
                    자리[a] -= 겹
                else:
                    자리[a] -= 겹 / 2.0
                    자리[b] += 겹 / 2.0
                움직 = True
        for k in 차:
            if k in 박:
                continue
            if 위 is not None and 자리[k] - h[k] / 2.0 < 위 - 1e-6:
                자리[k] = 위 + h[k] / 2.0
                움직 = True
            if 아래 is not None and 자리[k] + h[k] / 2.0 > 아래 + 1e-6:
                자리[k] = 아래 - h[k] / 2.0
                움직 = True
        if not 움직:
            break
    겹침 = any((h[a] + h[b]) / 2.0 + 틈 - (자리[b] - 자리[a]) > 0.5 for a, b in zip(차, 차[1:]))
    if 박 and 겹침:                                        # 박은 자리로는 다 못 놓는다(끝에 막힘) — 박지 않고 덩어리로 다시
        return _덩어리놓기(원함, 틈, 위, 아래)
    return 자리


def _덩어리놓기(원함, 틈, 위=None, 아래=None):
    """겹치는 글 상자를 덩어리로 묶어 덩어리마다 원래 자리에 가장 가깝게(평균) 놓는다(차례 보존 · 위아래 끝 안)."""
    n = len(원함)
    차 = sorted(range(n), key=lambda k: (원함[k][0], 원함[k][1]))
    덩 = []                                               # [항목들, 위끝]

    def 맞춤(항):
        off, 앞h, 오프 = 0.0, None, []
        for k in 항:
            hk = 원함[k][2]
            off = hk / 2.0 if 앞h is None else off + (앞h + hk) / 2.0 + 틈
            오프.append(off)
            앞h = hk
        전체 = 오프[-1] + 원함[항[-1]][2] / 2.0
        T = sum(원함[k][0] - o for k, o in zip(항, 오프)) / len(항)
        if 아래 is not None:
            T = min(T, 아래 - 전체)
        if 위 is not None:
            T = max(T, 위)
        return T, 오프, 전체
    for k in 차:
        덩.append([k])
        while len(덩) > 1:
            T1, _o1, 전1 = 맞춤(덩[-2])
            T2, _o2, _전2 = 맞춤(덩[-1])
            if T1 + 전1 + 틈 > T2 + 1e-6:
                덩[-2:] = [덩[-2] + 덩[-1]]
            else:
                break
    자리 = [0.0] * n
    for 항 in 덩:
        T, 오프, _전 = 맞춤(항)
        for k, o in zip(항, 오프):
            자리[k] = T + o
    return 자리


def _가로놓기(항목, 왼=None, 오른=None, 틈=4.0):
    """가로 한 줄 글(눈금 이름)을 겹치지 않게 민다. 항목 = [(가운데 x, 폭)] → 가운데 x 목록(차례는 그대로, 양 끝 안)."""
    if not 항목:
        return []
    xs = [x for x, _w in 항목]
    for _ in range(40):
        움직 = False
        for i in range(len(항목) - 1):
            겹 = (xs[i] + 항목[i][1] / 2.0 + 틈) - (xs[i + 1] - 항목[i + 1][1] / 2.0)
            if 겹 > 0.01:
                xs[i] -= 겹 / 2.0
                xs[i + 1] += 겹 / 2.0
                움직 = True
        if 왼 is not None and xs[0] - 항목[0][1] / 2.0 < 왼:
            d = 왼 - (xs[0] - 항목[0][1] / 2.0)
            xs = [x + d for x in xs]
            움직 = True
        if 오른 is not None and xs[-1] + 항목[-1][1] / 2.0 > 오른:
            d = xs[-1] + 항목[-1][1] / 2.0 - 오른
            xs = [x - d for x in xs]
            움직 = True
        if not 움직:
            break
    return xs


def _상자겹침(a, b, 틈=1.0):
    """두 상자(x0, y0, x1, y1)가 겹치나."""
    return not (a[2] + 틈 <= b[0] or b[2] + 틈 <= a[0] or a[3] + 틈 <= b[1] or b[3] + 틈 <= a[1])


_돈꼴 = re.compile(r"(조 원|억 원|만 원|억 달러|만 달러|억 엔|억 유로)\**\s*$")
_돈배 = {"조": 1e12, "억": 1e8, "만": 1e4}


def 돈단위(글들, 기본=("조 원", 1e12)):
    """칸 글들의 돈 단위 — 가장 많이 쓴 단위(「조 원」 · 「억 달러」 …)와 그 배수. 눈금 글을 그 단위로 적는다(v4e — 「조 원」 이 박혀 있던 그림을
    다른 통화 · 규모의 회사에서도 맞게). 못 찾으면 기본."""
    셈 = {}
    for g in 글들:
        m = _돈꼴.search("%s" % g)
        if m:
            셈[m.group(1)] = 셈.get(m.group(1), 0) + 1
    if not 셈:
        return 기본
    단 = max(셈, key=lambda k: 셈[k])
    return 단, _돈배[단[0]]


def _눈금수(v):
    """눈금 글 — 0 아래는 레터 글과 같은 빼기표(「−50」 — v4f, 붙임표 「-」 가 아니다)."""
    a = abs(v)
    g = "{:,.0f}".format(v) if a >= 100 or a == 0 or abs(a - round(a)) < 1e-9 else ("{:,.1f}".format(v) if a >= 1 else "{:,.2f}".format(v))
    return "−" + g[1:] if g.startswith("-") else g


def _글상자(x, y, 글, 크기, 앵="start", 가운데=False):
    """글 상자(그림 단위) — 어림 폭 × 글자 높이(가운데 맞춤이면 위아래 반, 아니면 바탕선 위 0.8 · 아래 0.2). `레터그림검사` 와 같은 정의."""
    w = _폭(글, 크기)
    x0 = x - (w / 2.0 if 앵 == "middle" else (w if 앵 == "end" else 0.0))
    return (x0, y - 크기 / 2.0, x0 + w, y + 크기 / 2.0) if 가운데 else (x0, y - 0.8 * 크기, x0 + w, y + 0.2 * 크기)


def _안겹치게(후보, 놓인, 틈=1.0, 마크=()):
    """후보 [(상자, 무엇)] 를 차례로 — 이미 놓인 상자와 겹치거나 데이터 마크(`_마크덮나` — 점 · 선분 · 면)를 덮는 것은 버린다
    (차례 = 중요한 것부터). → 놓은 것들의 무엇."""
    낸 = []
    for 상, 무엇 in 후보:
        if any(_상자겹침(상, q, 틈) for q in 놓인) or _마크덮나(상, 마크):
            continue
        놓인.append(상)
        낸.append(무엇)
    return 낸


def _첫자리(후보, 놓인, 틈=1.0, 마크=()):
    """한 글의 자리 후보 [(상자, 무엇)] 가운데 놓인 글 · 마크를 덮지 않는 첫 자리 → 무엇(없으면 None). 고른 상자를 놓인 데 더한다."""
    for 상, 무엇 in 후보:
        if not any(_상자겹침(상, q, 틈) for q in 놓인) and not _마크덮나(상, 마크):
            놓인.append(상)
            return 무엇
    return None


def _선분상자(x1, y1, x2, y2, b):
    """선분이 상자(x0, y0, x1, y1) 안을 지나는가(Liang–Barsky). `레터그림검사` ⑤ 와 같은 함수."""
    dx, dy = x2 - x1, y2 - y1
    u0, u1 = 0.0, 1.0
    for p, q in ((-dx, x1 - b[0]), (dx, b[2] - x1), (-dy, y1 - b[1]), (dy, b[3] - y1)):
        if abs(p) < 1e-12:
            if q < 0:
                return False
            continue
        t = q / p
        if p < 0:
            u0 = max(u0, t)
        else:
            u1 = min(u1, t)
        if u0 > u1:
            return False
    return True


def _마크덮나(상, 마크, 틈면=1.0, 틈선=2.0):
    """글 상자가 데이터 마크를 덮나 — 마크 = [("점", (cx, cy, r)) · ("선", (x1, y1, x2, y2)) · ("면", 상자)]. 잣대는 `레터그림검사` ⑤ 와 같다
    (닿기만 한 것은 겹침이 아니다 — 면 · 점은 1, 선은 2 그림 단위 안쪽으로 줄여 잰다)."""
    for 종, g in 마크:
        s = 틈선 if 종 == "선" else 틈면
        b = (상[0] + s, 상[1] + s, 상[2] - s, 상[3] - s)
        if b[0] >= b[2] or b[1] >= b[3]:
            continue
        if 종 == "면":
            if b[0] < g[2] and g[0] < b[2] and b[1] < g[3] and g[1] < b[3]:
                return True
        elif 종 == "점":
            cx, cy, r = g
            nx, ny = min(max(cx, b[0]), b[2]), min(max(cy, b[1]), b[3])
            if (nx - cx) ** 2 + (ny - cy) ** 2 < r * r:
                return True
        elif _선분상자(g[0], g[1], g[2], g[3], b):
            return True
    return False


def _선분들(pts):
    """점 목록 → 선분 마크 목록."""
    return [("선", (a[0], a[1], b[0], b[1])) for a, b in zip(pts, pts[1:])]


def _범위눈금(lo, hi, 칸수=4):
    """y 축 눈금 — 음수를 품는 범위(lo ≤ 0 ≤ hi 또는 그 밖)를 깔끔한 간격으로. → (눈금 목록, 아래 끝, 위 끝)."""
    lo, hi = min(lo, 0.0), max(hi, 0.0)
    폭 = (hi - lo) or 1.0
    날 = 폭 / 칸수
    자 = 10 ** math.floor(math.log10(날))
    칸 = next(자 * k for k in (1, 2, 2.5, 5, 10) if 자 * k >= 날 - 1e-12)
    아 = math.floor(lo / 칸 + 1e-9) * 칸
    위 = math.ceil(hi / 칸 - 1e-9) * 칸
    n = int(round((위 - 아) / 칸))
    return [round(아 + 칸 * i, 10) for i in range(n + 1)], 아, 위


def _축(lo, hi, 칸수=4):
    """판의 세로 범위와 눈금 — 범위는 값에 맞춰 조금 띄우고(눈금 끝에 붙이지 않는다), 눈금은 그 안의 깔끔한 값만. → (눈금, 아래 끝, 위 끝)."""
    눈, _a, _b = _범위눈금(lo, hi, 칸수)
    위 = max(hi, 0.0) * 1.06 if hi > 0 else 0.0
    밑 = min(lo, 0.0) - (위 - min(lo, 0.0)) * 0.05 if lo < 0 else 0.0
    if 위 == 밑:
        위 = 밑 + 1.0
    return [g for g in 눈 if 밑 - 1e-9 <= g <= 위 + 1e-9], 밑, 위


def _눈금(최대):
    """y 축 눈금 — 0 부터 깔끔한 간격(10 · 20 · 25 · 50 …)으로 최대를 덮는다."""
    if 최대 <= 0:
        return [0, 1]
    날 = 최대 / 4
    자 = 10 ** math.floor(math.log10(날))
    for k in (1, 2, 2.5, 5, 10):
        if 자 * k >= 날:
            칸 = 자 * k
            break
    n = int(math.ceil(최대 / 칸 - 1e-9))
    return [round(칸 * i, 10) for i in range(n + 1)]


def _x말(머리):
    """기간 머리(「2026 하반기(추정)」 · 「2027(추정)」 · 「2032년~」 · 「2026년 2분기」) → 두 줄 눈금 글(해 · 덧말)."""
    t = re.sub(r"\((?:추정|실적)\)", "", 머리).strip()
    m = re.match(r"^(\d{4})년?\s*(.*)$", t)
    if not m:
        return t, ""
    덧 = m.group(2).strip()
    if 덧 == "~":
        덧 = "이후"
    return m.group(1), 덧


def _부분선(pts, p):
    """점 목록의 앞 몫 p(0~1)만 — 마지막 칸은 두 점 사이를 잇는다(모션의 한 프레임 · 좌표만 — 숫자를 새로 찍지 않는다)."""
    if p is None or p >= 1 or len(pts) < 2:
        return pts
    if p <= 0:
        return pts[:1]
    k = p * (len(pts) - 1)
    i = int(k)
    f = k - i
    a, b = pts[i], pts[min(i + 1, len(pts) - 1)]
    return pts[:i + 1] + [(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)]



def _투(o):
    """불투명도 속성 — 1 이면 빈 글(정적 그림과 같은 글이 나오게), 그 아래면 opacity 속성."""
    return "" if o is None or o >= 1 else ' opacity="%.3f"' % max(0.0, o)


def _진(진행, 키, 기본=1.0):
    """진행 값 하나 — 없으면 기본(1 = 다 된 상태 = 정적 그림)."""
    v = (진행 or {}).get(키)
    return 기본 if v is None else max(0.0, min(1.0, float(v)))


def _가로선종류(이름, k):
    """가로선의 위계 — 이 평가의 답(「기준」)이 가장 진하고, 주가 · 종가가 전제한 수준은 강조색, 그 밖(비관 · 지난 바닥 따위)은 회색 점선."""
    if "기준" in 이름:
        return "viz-ref-1"
    if "주가" in 이름 or "종가" in 이름:
        return "viz-ref-2"
    return "viz-ref-3" if k > 1 or any(m in 이름 for m in ("비관", "낙관", "바닥", "지난")) else ("viz-ref-1", "viz-ref-2")[k]


def _x축글(xs, 머리들, 크기, 왼, 오른):
    """기간 머리 → 두 줄 눈금 글(해는 바뀔 때 한 번 — 같은 해가 이어지면 가운데에 하나, 덧말은 칸마다). 겹치면 옆으로 민다. → [(x, 줄, 글)]."""
    말 = [_x말(h) for h in 머리들]
    낸 = []
    묶 = []
    for i, (해, _d) in enumerate(말):
        if 묶 and 묶[-1][0] == 해:
            묶[-1][1].append(i)
        else:
            묶.append((해, [i]))
    한 = [(sum(xs[i] for i in ix) / len(ix), _폭(해, 크기), 해) for 해, ix in 묶]
    if any(b[0] - a[0] < (a[1] + b[1]) / 2.0 + 4 for a, b in zip(한, 한[1:])):     # 붐비면 첫 해만 네 자리(「2026 · 27 · 28」)
        한 = [(x, _폭(g if k == 0 or not re.match(r"^\d{4}$", g) else g[2:], 크기), g if k == 0 or not re.match(r"^\d{4}$", g) else g[2:])
             for k, (x, _w, g) in enumerate(한)]
    한 = _솎기(한, 왼, 오른)
    for x, (_x0, _w, 글) in zip(_가로놓기([(a, w) for a, w, _g in 한], 왼, 오른), 한):
        낸.append((x, 1, 글))
    둘 = _솎기([(xs[i], _폭(d, 크기), d) for i, (_h, d) in enumerate(말) if d], 왼, 오른)
    for x, (_x0, _w, 글) in zip(_가로놓기([(a, w) for a, w, _g in 둘], 왼, 오른), 둘):
        낸.append((x, 2, 글))
    return 낸


def _솎기(항목, 왼, 오른, 틈=4.0):
    """눈금 글이 자리에 다 들지 않으면 하나 걸러, 둘 걸러 … 남긴다(처음 · 끝은 늘 남긴다 — v4e: 해가 많은 회사에서 글이 그림 밖으로 밀려났다)."""
    if len(항목) < 3:
        return 항목
    for k in range(1, len(항목)):
        고른 = [t for i, t in enumerate(항목) if i % k == 0 or i == len(항목) - 1]
        if len(고른) >= 2 and 고른[-1] is 항목[-1] and 고른[-2] is not 항목[-1] and (len(항목) - 1) % k:
            고른 = 고른[:-2] + [고른[-1]] if 고른[-1][0] - 고른[-2][0] < (고른[-1][1] + 고른[-2][1]) / 2.0 + 틈 else 고른
        if sum(w for _x, w, _g in 고른) + 틈 * (len(고른) - 1) <= (오른 - 왼) and                 all(b[0] - a[0] >= (a[1] + b[1]) / 2.0 + 틈 for a, b in zip(고른, 고른[1:])):
            return 고른
    return [항목[0], 항목[-1]]


def _길선들(표들, 제목=""):
    """그림 1(길)의 재료 → (계열 줄, 값 목록, 가로선 [{이름, 값글, v, cls, 경로}]). 경로 = 이 평가의 기준 선의 값이 경로의 끝값과 같아
    가로선을 따로 긋지 않고 경로 끝의 이름으로 적는 선(v4d · 조사 설계 B — 경로 자체가 기준이다)."""
    if not 표들:
        return None, [], []
    머리, 줄들 = 표들[0]
    계열 = _그릴줄(줄들, 제목)
    if not 계열:
        return None, [], []
    값 = [수읽기(c) for c in 계열[1:]]
    선들 = []
    if len(표들) > 1:
        머2, 줄2 = 표들[1]
        k = 1
        이름 = re.sub(r"\s*\(.*$", "", 계열[0]).strip()
        for i, h in enumerate(머2[1:], 1):              # 계열의 구분 이름과 같은 칸
            if h.strip() == 이름:
                k = i
        for r in 줄2:
            v = 수읽기(r[k]) if len(r) > k else None
            if v is not None:
                선들.append({"이름": r[0].strip(), "값글": r[k].strip(), "v": v})
    끝 = next((v for v in reversed(값) if v is not None), None)
    경로됨 = False
    for k, d in enumerate(선들):
        d["cls"] = _가로선종류(d["이름"], k)
        d["경로"] = (not 경로됨 and d["cls"] == "viz-ref-1" and 끝 is not None and abs(d["v"] - 끝) <= max(0.5, abs(끝) * 0.005))
        경로됨 = 경로됨 or d["경로"]
    return 계열, 값, 선들




def _그릴줄(줄들, 제목):
    """그림 1 이 선으로 그리는 줄 — 줄 이름(괄호 앞)이 제목에 든 줄(가장 긴 이름), 없으면 첫 줄. 「지난 사이클」 줄은 따로 그린다."""
    후보 = [r for r in 줄들 if r and not r[0].startswith("지난 사이클")]
    머 = re.split(r"\s—\s", re.sub(r"\*", "", 제목 or ""))[0]          # 제목의 이름 부분(설명 앞)만 본다
    맞 = [r for r in 후보 if re.sub(r"\s*\(.*$", "", r[0]).strip() and re.sub(r"\s*\(.*$", "", r[0]).strip() in 머]
    if 맞:
        return max(맞, key=lambda r: len(re.sub(r"\s*\(.*$", "", r[0]).strip()))
    return 후보[0] if 후보 else None


def _수준말(머리):
    """그림 2 · 궤적의 칸 머리(「범용 DRAM 정상 수준」 · 「NAND 바닥」) → 「정상 수준」 · 「바닥」 (끝 낱말)."""
    for 말 in ("정상 수준", "바닥"):
        if any(("%s" % h).strip().endswith(말) for h in 머리):
            return 말
    return "정상 수준"


def 자종가(표들):
    """그림 2 의 종가 줄 번호(표의 차례) — 모션 C 의 정지점."""
    if not 표들:
        return []
    return [k for k, r in enumerate(표들[0][1]) if r and "종가" in r[0] and len(r) > 1 and 수읽기(r[1]) is not None]




_상태 = {"켜짐": "viz-st-on", "다가감": "viz-st-near", "꺼짐": "viz-st-off",
        "경보": "viz-st-on", "임계치 근접": "viz-st-near", "경보 없음": "viz-st-off"}     # 2026-10-27 — 레터에 찍는 상태 말(레터이야기.신호상태말)


def 신호(표들, 제목=""):
    """그림 3 — 신호등 카드(HTML). 열 이름으로 칸을 찾는다(관측 신호 · 임계치 · 경보 시 가치 방향 · 지금 · 상태 — 옛 이름 신호 · 문턱 · 켜지면도 ·
    없는 칸은 건너뛴다)."""
    if not 표들:
        return ""
    머리, 줄들 = 표들[0]
    칸 = {h.strip(): i for i, h in enumerate(머리)}

    def 집(r, 이름):
        i = 칸.get(이름)
        v = r[i].strip() if i is not None and i < len(r) else ""
        return "" if v in ("—", "-") else v
    s = ['<ul class="viz-signals" aria-label="%s">' % _e(제목 or "신호")]
    for r in 줄들:
        상 = 집(r, "상태")
        cls = _상태.get(상, "viz-st-none")
        s.append('<li><span class="viz-light %s" aria-hidden="true"></span><div><p class="viz-sig-name">%s%s</p>' % (
            cls, _e(r[0]), ('<span class="viz-sig-state">%s</span>' % _e(상)) if 상 else ""))
        for 이름들, 말 in ((("임계치", "문턱"), "임계치"), (("경보 시 가치 방향", "켜지면"), "경보 시 가치 방향"), (("지금",), "지금")):
            v = next((집(r, 이름) for 이름 in 이름들 if 집(r, 이름)), "")
            if v:
                s.append('<p class="viz-sig-row"><span class="viz-sig-key">%s</span><span>%s</span></p>' % (_e(말), _e(v)))
        s.append("</div></li>")
    s.append("</ul>")
    return "".join(s)


def _줄임(글, n):
    return 글 if len(글) <= n else 글[:n - 1] + "…"


def 폭포(표들, 제목=""):
    """본편의 그림 — 기준에서 시나리오로 가는 길(가정 묶음마다 주당가치가 움직인 몫). 표: 묶음 · 시나리오마다 걸음(「−9.7만 원」 · 「−91,280원」).
    시나리오마다 판 하나 — 가로 막대가 앞까지의 누적에서 이번 누적까지 간다(오름 파랑 · 내림 주황). 옛 「합계」 줄은 그리지 않는다.
    통독 v4 중-6 — 첫 줄이 「기준 시나리오…」 면 출발 합계 막대, 마지막 굵은 줄(「**시나리오 주당가치**」 따위)이면 도착 합계 막대를 0 부터 그린다.
    이름은 두세 줄로 접고(말줄임 없음), 값은 표의 글 그대로(단위가 표와 같다). 두 판은 같은 눈금을 쓴다."""
    if not 표들:
        return ""
    머리, 줄들 = 표들[0]
    줄들 = [r for r in 줄들 if r and "합계" not in r[0]]

    def 맑게(c):
        return re.sub(r"\*", "", "%s" % c).strip()
    처음 = 줄들[0] if 줄들 and 맑게(줄들[0][0]).startswith("기준 시나리오") else None
    끝 = 줄들[-1] if 줄들 and 줄들[-1] is not 처음 and (줄들[-1][0].strip().startswith("**") or "주당가치" in 맑게(줄들[-1][0])) else None
    걸음줄 = [r for r in 줄들 if r is not 처음 and r is not 끝]
    판들 = []
    for k in range(1, len(머리)):
        시작 = 수읽기(처음[k]) if 처음 is not None and len(처음) > k else None
        걸음 = [(맑게(r[0]), 맑게(r[k]), 수읽기(r[k])) for r in 걸음줄 if len(r) > k and 수읽기(r[k]) not in (None, 0.0)]
        도착 = 수읽기(끝[k]) if 끝 is not None and len(끝) > k else None
        if 걸음 or 도착 is not None:
            판들.append((맑게(머리[k]), 시작, 걸음, 도착, 맑게(처음[k]) if 시작 is not None else "", 맑게(끝[k]) if 도착 is not None else ""))
    if not 판들:
        return ""
    누들 = []
    for _이, 시작, 걸음, 도착, _a, _b in 판들:
        누 = [시작 or 0.0]
        for _n, _g, v in 걸음:
            누.append(누[-1] + v)
        누들.append(누)
    모든 = [v for 누 in 누들 for v in 누] + [p[3] for p in 판들 if p[3] is not None] + [0.0]
    lo, hi = min(모든), max(모든)
    폭 = (hi - lo) or 1.0
    W, 위, 아래 = 360, 28, 8
    lx, 이름폭, px0, px1 = 4, 128, 138, 284
    크, 줄높 = 12, 14
    값글들 = [g for _이, _s, 걸음, _d, a, b in 판들 for g in [a, b] + [x[1] for x in 걸음] if g]
    if 값글들:                                                   # 1.1.10 — 값 글(「1,157.44달러」)이 길면 막대 끝이 값 글을 덮었다(게이트 그림 ⑤) — 막대 칸을 줄인다
        px1 = max(px0 + 80, min(px1, W - 4 - int(max(_폭(g, 크) for g in 값글들) + 0.999) - 8))

    def X(v):
        return px0 + (px1 - px0) * (v - lo) / 폭
    s = []
    for (이름, 시작, 걸음, 도착, 시작글, 도착글), 누 in zip(판들, 누들):
        항 = []                                                     # (이름, 값글, 막대 a, 막대 b, 종류)
        if 시작 is not None:
            항.append((맑게(처음[0]), 시작글, 0.0, 시작, "viz-total"))
        for i, (n, g, v) in enumerate(걸음):
            항.append((n, g, 누[i], 누[i + 1], "viz-up" if v > 0 else "viz-down"))
        if 도착 is not None:                                       # 1.1.10 — 도착 이름이 「시나리오 …」 면 판의 시나리오 이름을 앞에(「비관 시나리오 주당가치」)
            끝이름 = 맑게(끝[0])
            항.append((("%s %s" % (이름.replace("으로", ""), 끝이름)) if 끝이름.startswith("시나리오") else 끝이름, 도착글, 0.0, 도착, "viz-total"))
        줄 = [_접기폭(n, 이름폭, 크) for n, *_x in 항]
        높 = [max(24, 줄높 * len(z) + 9) for z in 줄]
        H = 위 + sum(높) + 아래
        s.append('<svg class="viz" viewBox="0 0 %d %d" role="img" aria-label="%s — %s" xmlns="http://www.w3.org/2000/svg">' % (W, H, _e(제목 or "그림"), _e(이름)))
        s.append('<text x="%d" y="16" class="viz-label viz-strong">%s</text>' % (lx, _e("기준 → " + 이름.replace("으로", ""))))
        s.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" class="viz-axis"/>' % (X(0), X(0), 위 - 4, H - 아래 + 2))
        y = 위
        앞끝 = None
        for (n, g, a, b2, 종), z, h in zip(항, 줄, 높):
            가 = y + h / 2.0
            합 = 종 == "viz-total"
            for j, t in enumerate(z):
                s.append('<text x="%d" y="%.1f" class="viz-name%s" dominant-baseline="middle">%s</text>' % (
                    lx, 가 + 줄높 * (j - (len(z) - 1) / 2.0), " viz-strong" if 합 else "", _e(t)))
            x0, x1 = sorted((X(a), X(b2)))
            if 앞끝 is not None:
                s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="viz-leader"/>' % (X(앞끝), X(앞끝), y - 4, 가 - 6))
            s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="12" rx="2" class="%s"><title>%s %s</title></rect>' % (
                x0, 가 - 6, max(x1 - x0, 1.5), 종, _e(n), _e(g)))
            s.append('<text x="%d" y="%.1f" class="viz-tick viz-value%s" text-anchor="end" dominant-baseline="middle">%s</text>' % (
                W - 4, 가, " viz-strong" if 합 else "", _e(g)))
            앞끝 = b2
            y += h
        s.append("</svg>")
    return "".join(s)


def _날말(머):
    """「2026-06-30」 · 「2026년 6월 30일」 → (해, 「6월」)."""
    m = re.match(r"^(\d{4})[-년]\s?(\d{1,2})", 머)
    return (m.group(1), "%d월" % int(m.group(2))) if m else (머, "")


def _월일(머):
    """「2026-06-30」 · 「2026년 6월 30일」 → 「6.30」(표의 날 글을 줄인 것 — 새 숫자가 아니다). 못 읽으면 빈 글."""
    m = re.match(r"^\s*\d{4}[-.년]\s?(\d{1,2})[-.월]\s?(\d{1,2})", "%s" % 머)
    return "%d.%d" % (int(m.group(1)), int(m.group(2))) if m else ""


def _핀줄(xs, 폭들, 왼, 오른):
    """핀 이름의 자리 — 이름은 세로선 머리에 깃발처럼(선 오른쪽, 오른 끝에 닿으면 왼쪽) 하나씩 단다. 줄은 핀마다 따로 주되,
    남의 선이 내 이름을 지나지 않게(내 이름 폭 안에 선이 있는 핀은 나보다 낮은 줄) 고른다. → [(줄, 오른쪽인가)]."""
    n = len(xs)
    def 빔(k, a, b):
        return not any(j != k and a - 1 <= xs[j] <= b + 1 for j in range(n))
    오 = []
    for k in range(n):
        ro = xs[k] + 3 + 폭들[k] <= 오른
        lo = xs[k] - 3 - 폭들[k] >= 왼
        r빔 = ro and 빔(k, xs[k] + 3, xs[k] + 3 + 폭들[k])
        l빔 = lo and 빔(k, xs[k] - 3 - 폭들[k], xs[k] - 3)
        오.append(True if r빔 else (False if l빔 else ro))
    폭 = [(xs[k] + 3, xs[k] + 3 + 폭들[k]) if 오[k] else (xs[k] - 3 - 폭들[k], xs[k] - 3) for k in range(n)]
    남 = set(range(n))
    줄 = {}
    r = 0
    while 남:
        후 = [k for k in 남 if not any(j != k and 폭[k][0] - 1 <= xs[j] <= 폭[k][1] + 1 for j in 남)]
        k = min(후 or 남, key=lambda k: (xs[k], k))
        줄[k] = r
        남.discard(k)
        r += 1
    return [(줄[k], 오[k]) for k in range(n)]


def 궤적(표들, 제목="", 진행=None):
    """그림(R1c · N1 · M1 짝) — 시장이 전제한 가정의 1년. 위 판: 종가(만 원), 아래 판: 그날 주가가 전제한 바닥(기준 기간 = 100) + 「이 평가의 기준」 선.
    두 판이 가로축(날)을 함께 쓴다(축을 둘 쓰지 않는다). 표: 머리 = 날 · 종가 · 바닥(첫 구분) …, 「핀」 칸이 있으면 그 줄에 핀.
    둘째 표(있으면): 가로선(이름 · 값). 진행(모션) = {"선": 0~1, "핀": 보이는 수}.
    통독 v4 중-8 — 핀 이름은 세로선 머리에 하나씩(겹치지 않게 줄을 달리한다), 아래 판 점의 값은 점 위로 띄우고 겹치면 비킨다,
    가로축은 「2025.8 · 10 · 2026.1」(해가 바뀔 때만 해). 「표시한 날」 칸이 「참고 구간 끝」 인 줄은 핀이 아니다 — 처음 날부터 그날까지 옅은 띠."""
    if not 표들:
        return ""
    머리, 줄들 = 표들[0]
    진행 = 진행 or {}
    칸 = {h.strip(): i for i, h in enumerate(머리)}
    i종 = next((i for h, i in 칸.items() if "종가" in h or h == "주가"), 1)
    i바 = next((i for h, i in 칸.items() if "바닥" in h or "정상 수준" in h), 2)
    i핀 = next((i for h, i in 칸.items() if h in ("핀", "표시한 날")), None)
    점 = []
    for r in 줄들:
        if len(r) <= max(i종, i바):
            continue
        점.append({"날": r[0], "종": 수읽기(r[i종]), "바": 수읽기(r[i바]), "핀": (r[i핀].strip() if i핀 is not None and i핀 < len(r) else ""),
                  "종글": r[i종], "바글": r[i바]})
    점 = [p for p in 점 if p["종"] is not None]
    if len(점) < 2:
        return ""
    참고 = next((i for i, p in enumerate(점) if p["핀"] == "참고 구간 끝"), None)
    for p in 점:
        if p["핀"] == "참고 구간 끝":
            p["핀"] = ""
    선들 = []
    if len(표들) > 1:
        for r in 표들[1][1]:
            v = 수읽기(r[1]) if len(r) > 1 else None
            if v is not None:
                선들.append((r[0], v))
    W = 360
    l, r_, h1, gap, h2, b = 40, 12, 110, 46, 110, 30
    n = len(점)

    def X(i):
        return l + (W - l - r_) * i / (n - 1)
    핀 = [(i, p) for i, p in enumerate(점) if p["핀"]]
    핀날 = [_월일(p["날"]) for _i, p in 핀]                   # v4f(모션 리뷰 M1) — 세로선 머리에 이름과 그 날(「고점 6.22」) — 어느 선이 어느 날인지
    핀폭 = [_폭(p["핀"], 12.5) + ((4 + _폭(d, 12.5)) if d else 0) for (_i, p), d in zip(핀, 핀날)]
    핀자리 = _핀줄([X(i) for i, _p in 핀], [w + 2 for w in 핀폭], l, W - 2)      # 선과 이름 사이 5(꺾는 깃발 4)
    줄수 = max([z for z, _o in 핀자리] + [-1]) + 1
    t1 = 22 + 13 * 줄수 + (6 if 줄수 else 0)
    t2 = t1 + h1 + gap
    H = t2 + h2 + b
    종max = max(p["종"] for p in 점)
    눈1 = _눈금(종max * 1.05)
    바값 = [p["바"] for p in 점 if p["바"] is not None] + [v for _n, v in 선들]
    눈2 = _눈금(max(바값 + [1]) * 1.08)

    def Y1(v):
        return t1 + h1 * (1 - v / 눈1[-1])

    def Y2(v):
        return t2 + h2 * (1 - v / 눈2[-1])
    s = ['<svg class="viz" viewBox="0 0 %d %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">' % (W, H, _e(제목 or "그림"))]
    s.append('<text x="%d" y="%d" class="viz-tick">주가(만 원)</text>' % (l, 13))
    축말 = _접기폭(_궤적축말(머리[i바] if i바 < len(머리) else "", 제목), W - l - 4, 12.5)      # v4e — 길면 두 줄(그림 밖으로 나가지 않게)
    for j, g in enumerate(축말):
        s.append('<text x="%d" y="%d" class="viz-tick">%s</text>' % (l, t2 - 10 - 15 * (len(축말) - 1 - j), _e(g)))
    if 참고 is not None and 참고 > 0:                       # 참고 구간 — 처음 날부터 표시한 날까지(그날 시장의 생각으로 읽지 않는 앞쪽 날들)
        for 위, 높 in ((t1, h1), (t2, h2)):
            s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" class="viz-band"/>' % (X(0), 위, X(참고) - X(0), 높))
        앞쪽 = [Y1(p["종"]) for p in 점[:max(2, int(참고 * 0.3) + 1)]]
        아래쪽 = sum(앞쪽) / len(앞쪽) > t1 + h1 / 2.0            # 선이 아래 반에 있으면 글은 위에, 아니면 아래에
        s.append('<text x="%.1f" y="%.1f" class="viz-tick">참고 구간</text>' % (X(0) + 4, (t1 + 14) if 아래쪽 else (t1 + h1 - 6)))
    for g in 눈1:
        s.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" class="viz-grid"/>' % (l, W - r_, Y1(g), Y1(g)))
        s.append('<text x="%d" y="%.1f" class="viz-tick" text-anchor="end" dominant-baseline="middle">%s</text>' % (l - 5, Y1(g), "{:,.0f}".format(g / 1e4)))
    for g in 눈2:
        s.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" class="viz-grid"/>' % (l, W - r_, Y2(g), Y2(g)))
        s.append('<text x="%d" y="%.1f" class="viz-tick" text-anchor="end" dominant-baseline="middle">%s</text>' % (l - 5, Y2(g), "{:,.0f}".format(g)))
    앞달, 앞해, 앞끝 = None, None, -1e9                        # 가로축 — 석 달마다(달이 바뀌는 첫 점), 해는 바뀔 때만
    for i, p in enumerate(점):
        y, m = _날말(p["날"])
        if m == 앞달:
            continue
        앞달 = m
        mm = int(m[:-1]) if m[:-1].isdigit() else 0
        if not (mm % 3 == 1 or i == 0):
            continue
        글 = ("%s.%d" % (y, mm)) if y != 앞해 else "%d" % mm
        w = _폭(글, 12.5)
        x = min(max(X(i), w / 2 + 2), W - 2 - w / 2)
        if x - w / 2 < 앞끝 + 6:
            continue
        앞해, 앞끝 = y, x + w / 2
        s.append('<text x="%.1f" y="%d" class="viz-tick" text-anchor="middle">%s</text>' % (x, H - b + 16, _e(글)))
    놓인 = []                                               # 아래 판 글 상자(겹침 피하기)
    아래선 = []                                              # v4f — 아래 판 선분 · 핀 점(가로선 이름이 덮지 않게 — 레터그림검사 ⑤)
    앞 = None
    for i, p in enumerate(점):
        q = (X(i), Y2(p["바"])) if p["바"] is not None else None
        if q and 앞:
            아래선.append(("선", (앞[0], 앞[1], q[0], q[1])))
        앞 = q
    아래선 += [("점", (X(i), Y2(p["바"]), 3.5)) for i, p in enumerate(점) if p["핀"] and p["바"] is not None]
    for 이름, v in 선들:                                     # 통독 v3 중-17 — 가로선 이름은 선과 계열이 먼 쪽 끝에
        s.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" class="viz-ref-1"><title>%s</title></line>' % (l, W - r_, Y2(v), Y2(v), _e(이름)))
        바들 = [(i, p["바"]) for i, p in enumerate(점) if p["바"] is not None]
        쪽 = []
        for 왼 in (True, False):
            구 = [b2 for i, b2 in 바들 if (i <= 0.35 * (n - 1) if 왼 else i >= 0.65 * (n - 1))]
            if 구:
                쪽.append((min(abs(b2 - v) for b2 in 구), 왼, sum(구) / len(구) < v))
        _c, 왼, 밑 = max(쪽) if 쪽 else (0, False, True)
        w = _폭(이름, 13)
        후 = []
        for 왼2, 밑2 in ((왼, 밑), (왼, not 밑), (not 왼, 밑), (not 왼, not 밑)):        # v4f — 계열이 먼 쪽 끝이 먼저, 막히면 나머지 셋
            tx, ty = (l + 4 if 왼2 else W - r_ - 4), (Y2(v) - 5 if 밑2 else Y2(v) + 13)
            후.append(((tx if 왼2 else tx - w, ty - 11, tx + w if 왼2 else tx, ty + 3), (tx, ty, 왼2)))
        남선 = [("선", (l, Y2(v2), W - r_, Y2(v2))) for n2, v2 in 선들 if n2 != 이름]
        고른 = _첫자리(후, 놓인, 마크=아래선 + 남선)
        if 고른 is None:
            고른 = 후[0][1]
            놓인.append(후[0][0])
        tx, ty, 왼2 = 고른
        s.append('<text x="%d" y="%.1f" text-anchor="%s" class="viz-label viz-muted">%s</text>' % (tx, ty, "start" if 왼2 else "end", _e(이름)))
    p선 = 진행.get("선")
    pts1 = _부분선([(X(i), Y1(p["종"])) for i, p in enumerate(점)], p선)
    s.append('<polyline points="%s" class="viz-line viz-line-thin"/>' % " ".join("%.1f,%.1f" % q for q in pts1))
    조각, 지금 = [], []
    for i, p in enumerate(점):
        if p["바"] is None:
            if 지금:
                조각.append(지금)
            지금 = []
        else:
            지금.append((X(i), Y2(p["바"])))
    if 지금:
        조각.append(지금)
    끝x = pts1[-1][0] if pts1 else W
    for c in 조각:
        c = [q for q in c if q[0] <= 끝x + 0.01]
        if len(c) >= 2:
            s.append('<polyline points="%s" class="viz-line-2"/>' % " ".join("%.1f,%.1f" % q for q in c))
    보일 = 진행.get("핀", len(핀))
    for k, (i, p) in enumerate(핀[:보일]):
        x = X(i)
        줄, 오른 = 핀자리[k]
        y핀 = t1 - 6 - 13 * 줄
        ym = y핀 - 4.5                                       # 이름 글의 가운데 높이 — 세로선이 거기서 시작해 이름 쪽으로 꺾인다(깃발)
        s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%d" class="viz-leader"/>' % (x, x, ym, t1 + h1))
        s.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="viz-leader"/>' % (x, x + (4 if 오른 else -4), ym, ym))
        s.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" class="viz-leader"/>' % (x, x, t2, t2 + h2))
        d = 핀날[k]
        if 오른:
            s.append('<text x="%.1f" y="%.1f" class="viz-tick" text-anchor="start">%s</text>' % (x + 5, y핀, _e(p["핀"])))
            if d:
                s.append('<text x="%.1f" y="%.1f" class="viz-tick viz-value" text-anchor="start">%s</text>' % (x + 5 + _폭(p["핀"], 12.5) + 4, y핀, _e(d)))
        else:
            s.append('<text x="%.1f" y="%.1f" class="viz-tick" text-anchor="end">%s</text>' % (x - 5 - ((_폭(d, 12.5) + 4) if d else 0), y핀, _e(p["핀"])))
            if d:
                s.append('<text x="%.1f" y="%.1f" class="viz-tick viz-value" text-anchor="end">%s</text>' % (x - 5, y핀, _e(d)))
    아래마크 = [("선", (l, Y2(v), W - r_, Y2(v))) for _n, v in 선들]          # v4f — 값 글이 덮지 않을 것(레터그림검사 ⑤ 와 같은 잣대): 아래 판 선 · 가로선 · 점
    for c in 조각:
        아래마크 += _선분들([q for q in c if q[0] <= 끝x + 0.01])
    아래마크 += [("점", (X(i), Y2(p["바"]), 3.5)) for i, p in 핀[:보일] if p["바"] is not None]
    for k, (i, p) in enumerate(핀[:보일]):                    # 점과 값 — 선 위에 그린다. 값은 점 위로 띄우고(halo) 남의 글 · 점 · 선과 겹치면 비킨다
        x = X(i)
        s.append('<circle cx="%.1f" cy="%.1f" r="3.5" class="viz-dot"><title>%s %s</title></circle>' % (x, Y1(p["종"]), _e(p["날"]), _e(p["종글"])))
        if p["바"] is None:
            continue
        y = Y2(p["바"])
        s.append('<circle cx="%.1f" cy="%.1f" r="3.5" class="viz-dot-2"><title>%s %s</title></circle>' % (x, y, _e(p["날"]), _e(p["바글"])))
        w = _폭(p["바글"], 13) * 1.05                       # 상자는 `_글상자` 와 같은 정의(레터그림검사 ②와 같은 잣대) + 여백
        후보 = [(x, y - 10, "middle"), (x + 5, y - 9, "start"), (x - 5, y - 9, "end"), (x + 3, y - 10, "end"), (x - 3, y - 10, "start"),
               (x, y - 23, "middle"), (x + 3, y - 23, "end"), (x - 3, y - 23, "start"), (x + 9, y - 21, "start"), (x - 9, y - 21, "end"),
               (x + 6, y + 17, "start"), (x - 6, y + 17, "end"), (x, y + 18, "middle"), (x + 8, y + 3, "start"), (x - 8, y + 3, "end"),
               (x, y - 36, "middle"), (x + 3, y - 36, "end"), (x - 3, y - 36, "start"), (x + 9, y + 30, "start"), (x - 9, y + 30, "end")]
        남점 = [(X(j), Y2(q["바"])) for j, q in 핀[:보일] if q["바"] is not None and j != i]
        고른 = None
        for cx, cy, an in 후보:
            x0 = cx - w / 2 if an == "middle" else (cx if an == "start" else cx - w)
            상 = (x0 - 1, cy - 0.8 * 13 - 1, x0 + w + 1, cy + 0.2 * 13 + 1)
            if x0 < l - 2 or x0 + w > W - 1 or 상[1] < t2 - 8 or 상[3] > t2 + h2 + 2:
                continue
            중x, 중y = (상[0] + 상[2]) / 2.0, (상[1] + 상[3]) / 2.0     # v4f — 값 글은 남의 점보다 제 점에 가까워야 한다(모션 리뷰 M1 — 두 값이 한 값처럼 읽힌다)
            if any((중x - a) ** 2 + (중y - b2) ** 2 <= (중x - x) ** 2 + (중y - y) ** 2 for a, b2 in 남점):
                continue
            if not any(_상자겹침(상, q) for q in 놓인) and not _마크덮나(상, 아래마크):
                고른 = (cx, cy, an, 상)
                break
        if 고른 is None:                                    # v4e — 빈 자리가 없으면 값 글을 달지 않는다(점의 값은 마우스 · 「그림의 숫자」 표에 있다)
            continue
        놓인.append(고른[3])
        s.append('<text x="%.1f" y="%.1f" class="viz-label viz-strong viz-value" text-anchor="%s">%s</text>' % (고른[0], 고른[1], 고른[2], _e(p["바글"])))
    s.append("</svg>")
    return "".join(s)


def _궤적축말(머, 제목):
    """궤적 아래 판의 축 이름 — 칸 머리(「NAND 정상 수준」)와 제목의 눈금(「2026년 2분기 = 100」)으로(통독 v3 — 눈금 이름 하나)."""
    눈 = re.search(r"(\d{4}년 \d분기 = 100|\d{4}년 = 100)", 제목 or "")
    return "그날 주가가 전제한 %s(%s)" % ((머 or "정상 수준").strip(), 눈.group(1) if 눈 else "기준 기간 = 100")


def _작은눈(x):
    """x(> 0) 이하의 가장 큰 고른 수(1 · 2 · 2.5 · 5 × 10^k) — 0 아래 값에 다는 눈금 하나. x ≤ 0 이면 None."""
    if not x or x <= 0:
        return None
    k = 10 ** math.floor(math.log10(x))
    return next((m * k for m in (5, 2.5, 2, 1) if m * k <= x + 1e-12), None)


def 꺾인해(값들):
    """증가율 줄에서 「증가율 하락 시작」 의 해 — 증가율이 오르다가(앞의 최고를 넘은 해가 있고) 그때까지의 최고였던 해 바로 다음 해에 낮아지면
    그 해의 자리(없으면 None — 첫 값부터 내리기만 하는 줄은 꺾인 것이 아니다). 표의 값만 견준다(새 숫자를 만들지 않는다)."""
    보 = [(i, g) for i, g in enumerate(값들) if g is not None]
    최대, 오름 = None, False
    for (i0, g0), (i1, g1) in zip(보, 보[1:]):
        if 최대 is not None and g0 > 최대:
            오름 = True
        최대 = g0 if 최대 is None else max(최대, g0)
        if 오름 and i1 == i0 + 1 and g1 < g0 and g0 >= 최대:
            return i1
    return None


def 계단(표들, 제목="", 진행=None):
    """그림(R1c · L19 STAIRS · M5 짝 — 모션은 v4d 에 폐기, 정적) — 해마다 영업이익 막대(계단)와 증가율(아래 판 — 0 선 위아래). 표: 머리 = 구분 · 해 …,
    줄 「영업이익」 · 「증가율」(· 「영업이익과 증가율의 변화」 글 · 「그중 실적」). 두 판이 가로축을 함께 쓴다.
    v4f(모션 리뷰 M5 · 중-5) — ① 실적과 추정이 섞인 해(머리에 「추정」, 「그중 실적」 줄에 그해 실적 몫)는 막대를 실적(진한) · 추정(연한)으로 쌓는다
    ② 증가율이 0 아래로 가는데 0 아래 눈금이 없으면 고른 수 눈금 하나(「−50」)를 더하고, 눈금 글이 0 과 겹치지 않게 아래 판을 높인다(160 까지)
    ③ 오르던 증가율이 그때까지의 최고 바로 다음 해에 낮아지면 그 해에 「증가율 하락 시작」 주석 하나(그림의 결론 — 이익은 크고 증가율은 꺾인다).
    금액 · 증가율 값 글과 주석은 남의 글 · 막대 · 선 · 점을 덮지 않는 첫 자리에 달고, 자리가 없으면 달지 않는다(값은 「그림의 숫자」 표에 있다).
    진행(M5) = {"막대": 보이는 수(소수 — 마지막 막대가 자라는 몫), "표지": 그해의 변화 글을 적을 해의 자리}."""
    if not 표들:
        return ""
    머리, 줄들 = 표들[0]
    진행 = 진행 or {}
    해 = 머리[1:]
    이 = next((r for r in 줄들 if "영업이익" in r[0] and "률" not in r[0]), None)
    증 = next((r for r in 줄들 if "증가율" in r[0]), None)
    실 = next((r for r in 줄들 if re.sub(r"[*()\s]", "", r[0]).startswith("그중실적")), None)
    if not 이:
        return ""
    이값 = [수읽기(c) for c in 이[1:]]
    증값 = [수읽기(c) for c in 증[1:]] if 증 else [None] * len(이값)
    실값 = [수읽기(c) for c in 실[1:]] if 실 else [None] * len(이값)
    soft = ["추정" in h for h in 해]
    범례 = any(soft) and not all(soft)
    l, r_, t1, h1, gap, h2, b = 40, 12, 18, 120, 30, 70, 30 + (18 if 범례 else 0)
    t2 = t1 + h1 + gap
    W = 360
    n = len(해)
    칸 = (W - l - r_) / n
    이들 = [v for v in 이값 if v is not None] or [0.0]
    눈1, 밑1, 위1 = _축(min(이들), max(이들), 4)            # 통독 v4 중-9 — 음수 막대는 0 선 아래로
    증들 = [v for v in 증값 if v is not None] or [0.0]
    눈2, lo, hi = _축(min(증들), max(증들), 3)
    if min(증들) < 0 and not any(g < 0 for g in 눈2):      # ② 0 아래 증가율의 눈금
        n음 = _작은눈(-min(증들))
        if n음 and lo <= -n음 + 1e-9:
            필요 = 14.0 * (hi - lo) / n음                    # 0 과 −n음 의 눈금 글(12.5px)이 겹치지 않는 판 높이
            if 필요 <= 160:
                h2 = max(h2, 필요)
                눈2 = sorted(눈2 + [-n음])
    H = t2 + h2 + 12 + b
    폭 = (hi - lo) or 1.0
    돈, 배 = 돈단위(이[1:])
    l = max(l, int(max([_폭(_눈금수(g / 배), 12.5) for g in 눈1] + [_폭(_눈금수(g), 12.5) for g in 눈2] + [0.0]) + 9))     # 2026-10-25 R5 — 다섯 자리 눈금(「10,000」)이 그림 밖으로
    칸 = (W - l - r_) / n

    def X(i):
        return l + 칸 * (i + 0.5)

    def Y1(v):
        return t1 + h1 * (위1 - v) / ((위1 - 밑1) or 1.0)

    def Y2(v):
        return t2 + h2 * (hi - v) / 폭
    s = ['<svg class="viz" viewBox="0 0 %d %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">' % (W, H, _e(제목 or "그림"))]
    돈, 배 = 돈단위(이[1:])
    s.append('<text x="%d" y="%d" class="viz-tick">영업이익(%s)</text>' % (l, t1 - 6, 돈))
    s.append('<text x="%d" y="%d" class="viz-tick">증가율(%%)</text>' % (l, t2 - 8))
    for g in 눈1:
        s.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" class="%s"/>' % (l, W - r_, Y1(g), Y1(g), "viz-zero" if g == 0 and 밑1 < 0 else "viz-grid"))
        s.append('<text x="%d" y="%.1f" class="viz-tick" text-anchor="end" dominant-baseline="middle">%s</text>' % (l - 5, Y1(g), _눈금수(g / 배)))
    for g in 눈2:
        s.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" class="%s"/>' % (l, W - r_, Y2(g), Y2(g), "viz-axis" if g == 0 else "viz-grid"))
        s.append('<text x="%d" y="%.1f" class="viz-tick" text-anchor="end" dominant-baseline="middle">%s</text>' % (l - 5, Y2(g), _눈금수(g)))
    if 범례:                                                # 진한 막대 = 머리에 「추정」 이 없는 해(실적) · 연한 막대 = 「추정」 이 든 해
        ly = H - 8
        s.append('<rect x="%d" y="%d" width="12" height="9" rx="2" class="viz-bar"/>' % (l, ly - 8))
        s.append('<text x="%d" y="%d" class="viz-tick">실적</text>' % (l + 16, ly))
        x2 = l + 16 + _폭("실적", 12.5) + 14
        s.append('<rect x="%.1f" y="%d" width="12" height="9" rx="2" class="viz-bar viz-bar-soft"/>' % (x2, ly - 8))
        s.append('<text x="%.1f" y="%d" class="viz-tick">추정</text>' % (x2 + 16, ly))
    보일 = 진행.get("막대", n)                                  # M5 — 막대 수(소수면 마지막 막대가 그만큼 자란다)
    다 = int(math.floor(보일 + 1e-9))
    자람 = 보일 - 다
    pts = []
    막대마 = []                                              # v4f — 막대 상자(금액 글이 남의 막대를 덮지 않게 — 레터그림검사 ⑤)
    for i in range(n):
        v = 이값[i]
        bx0, bw = X(i) - min(18, 칸 * 0.36), min(36, 칸 * 0.72)
        if v is not None and (i < 다 or (i == 다 and 자람 > 1e-9)):
            a = 실값[i] if i < 다 else None
            if soft[i] and a is not None and a * v > 0 and abs(a) < abs(v):      # ① 실적 몫(진한) 위에 추정 몫(연한)
                for 끝0, 끝1, 갈, 말, 글 in ((0.0, a, "", "그중 실적", 실[i + 1]), (a, v, " viz-bar-soft", "", 이[i + 1])):
                    y0, y1_ = sorted((Y1(끝0), Y1(끝1)))
                    s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="2" class="viz-bar%s"><title>%s %s</title></rect>' % (
                        bx0, y0, bw, max(y1_ - y0, 0.8), 갈, _e((해[i] + " " + 말).strip()), _e(글)))
                    막대마.append(("면", (bx0, y0, bx0 + bw, y0 + max(y1_ - y0, 0.8))))
            else:
                y = Y1(v * (1.0 if i < 다 else 자람))
                y0, y1_ = sorted((Y1(0), y))
                s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="2" class="viz-bar%s"><title>%s %s</title></rect>' % (
                    bx0, y0, bw, max(y1_ - y0, 0.8), " viz-bar-soft" if soft[i] else "", _e(해[i]), _e(이[i + 1])))
                막대마.append(("면", (bx0, y0, bx0 + bw, y0 + max(y1_ - y0, 0.8))))
        g = 증값[i]
        if g is not None and i < 다:
            pts.append((X(i), Y2(g)))
    해글 = [_x말(h)[0] for h in 해]                            # v4e — 해가 많으면 첫 해만 네 자리(「2024 · 25 · 26」), 그래도 붐비면 하나 걸러
    if n and 칸 < _폭("2024", 12.5) + 4:
        해글 = [g if k == 0 or not re.match(r"^\d{4}$", g) else g[2:] for k, g in enumerate(해글)]
    걸러 = 2 if (n and 칸 < _폭("24", 12.5) + 8) else 1
    for i in range(n):
        if i % 걸러 == 0 or i == n - 1:
            s.append('<text x="%.1f" y="%d" class="viz-tick" text-anchor="middle">%s</text>' % (X(i), H - b + 14, _e(해글[i])))
    놓인 = [_글상자(l - 5, Y1(g), _눈금수(g / 배), 12.5, "end", True) for g in 눈1] +          [_글상자(l - 5, Y2(g), _눈금수(g), 12.5, "end", True) for g in 눈2]
    후보 = []                                                # v4d — 0 아래 막대(적자)는 금액 글을 막대 밑에(가장 깊은 것부터 — 겹치면 버린다)
    for i in sorted([i for i in range(min(n, 다)) if 이값[i] is not None and 이값[i] < 0], key=lambda i: 이값[i]):
        글 = 이[i + 1].strip()
        w = _폭(글, 12.5) * 1.04
        x = min(max(X(i), l + 4 + w / 2), W - r_ - w / 2)
        후보.append((_글상자(x, Y1(이값[i]) + 13, 글, 12.5, "middle"), (x, Y1(이값[i]) + 13, "middle", 글)))
    for x, y, 앵, 글 in _안겹치게(후보, 놓인, 마크=막대마):       # v4f — 남의 막대를 덮는 자리면 달지 않는다(값은 「그림의 숫자」 표에)
        s.append('<text x="%.1f" y="%.1f" class="viz-tick viz-value" text-anchor="%s" style="font-size:12.5px">%s</text>' % (x, y, 앵, _e(글)))
    if len(pts) >= 2:
        s.append('<polyline points="%s" class="viz-line-2"/>' % " ".join("%.1f,%.1f" % q for q in pts))
    for q in pts:
        s.append('<circle cx="%.1f" cy="%.1f" r="3" class="viz-dot-2"/>' % q)
    선마 = _선분들(pts) + [("점", (x, y, 3.0)) for x, y in pts]
    if 증 and 다 >= n:                                       # v4d — 증가율의 크기: 가장 높은 해와 0 아래인 해는 점 곁에 값 글(표의 글 그대로)
        보 = [(i, 증값[i]) for i in range(n) if 증값[i] is not None]
        if 보:
            최고 = max(보, key=lambda t: t[1])[0]
            for i, g in sorted(보, key=lambda t: (t[0] != 최고, t[1])):     # 가장 높은 해 먼저, 그다음 0 아래 해(깊은 것부터)
                글 = 증[i + 1].strip()
                px, py = X(i), Y2(g)
                if i == 최고 and g > 0:                      # v4f — 자리 후보 여럿(선 · 점 · 남의 글을 덮지 않는 첫 자리 — 없으면 달지 않는다)
                    자 = ([(px + 6, py + 4, "start")] if i < n - 1 else [(px - 6, py + 4, "end")]) + [
                        (px, py - 8, "middle"), (px + 6, py - 6, "start"), (px - 6, py - 6, "end"), (px - 6, py + 4, "end"), (px + 8, py + 12, "start"),
                        (px - 8, py + 12, "end")]
                elif g < 0:                                     # 점 밑 가운데 → 점 위 가운데 → 밑 오른쪽 · 왼쪽(왼쪽 끝 해는 눈금 글 곁에 붙어 한 글처럼 읽힌다)
                    자 = [(px, py + 14, "middle"), (px, py - 8, "middle"), (px + 6, py + 12, "start"), (px - 6, py + 12, "end")]
                else:
                    continue
                고른 = _첫자리([(_글상자(x, y, 글, 12.5, 앵), (x, y, 앵)) for x, y, 앵 in 자
                              if _글상자(x, y, 글, 12.5, 앵)[0] >= l - 2 and _글상자(x, y, 글, 12.5, 앵)[2] <= W - 2], 놓인, 마크=선마)
                if 고른:
                    s.append('<text x="%.1f" y="%.1f" class="viz-tick viz-value" text-anchor="%s" style="font-size:12.5px">%s</text>' % (
                        고른[0], 고른[1], 고른[2], _e(글)))
        꺾 = 꺾인해(증값)                                    # ③ 주석 하나 — 점 · 선 · 남의 글을 덮지 않는 자리(없으면 달지 않는다)
        if 꺾 is not None and 증값[꺾] is not None:
            말 = "증가율 하락 시작"
            px, py = X(꺾), Y2(증값[꺾])
            마 = _선분들(pts) + [("점", (x, y, 3.0)) for x, y in pts]
            후보 = []
            for x, y, 앵 in ((px + 8, py - 8, "start"), (px - 8, py - 8, "end"), (px + 8, py + 15, "start"), (px - 8, py + 15, "end"),
                            (px, py - 13, "middle"), (px, py + 18, "middle"), (px + 8, py - 20, "start"), (px - 8, py - 20, "end")):
                상 = _글상자(x, y, 말, 12.5, 앵)
                if 상[0] >= 2 and 상[2] <= W - 2 and 상[1] >= t2 - 4 and 상[3] <= t2 + h2 + 10:
                    후보.append((상, (x, y, 앵)))
            놓 = _첫자리(후보, 놓인, 마크=마)
            if 놓:
                x, y, 앵 = 놓
                s.append('<text x="%.1f" y="%.1f" class="viz-note-flag viz-strong" text-anchor="%s" style="font-size:12.5px">%s</text>' % (x, y, 앵, 말))
    표 = 진행.get("표지")                                       # M5 — 그해의 변화(표의 「영업이익과 증가율의 변화」 줄 글)를 위 오른쪽에. 정적 그림에는 없다
    변 = next((r for r in 줄들 if "변화" in r[0] or r[0].strip() == "국면"), None)
    if 표 is not None and 변 and 0 <= 표 < n and 표 + 1 < len(변) and 변[표 + 1].strip() not in ("", "—"):
        s.append('<text x="%d" y="%d" class="viz-label viz-strong" text-anchor="end">%s</text>' % (W - r_, t1 - 6, _e("%s · %s" % (_x말(해[표])[0], 변[표 + 1].strip()))))
        s.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" rx="3" class="viz-mark"/>' % (X(표) - 칸 / 2 + 1, t1 - 2, 칸 - 2, H - b - t1 + 4))
    s.append("</svg>")
    return "".join(s)


def _접기(글, 폭):
    """낱말 사이에서 줄을 접는다(한 줄 폭 글자 수 안)."""
    줄, 지금 = [], ""
    for w in 글.split():
        if 지금 and len(지금) + 1 + len(w) > 폭:
            줄.append(지금)
            지금 = w
        else:
            지금 = (지금 + " " + w).strip()
    return 줄 + ([지금] if 지금 else [])


def 시계(표들, 제목="", 진행=None):
    """그림(R1c · L21) — 사이클 시계. 표: 단계 · 해 · 지금(「◀ 지금」 표시가 든 줄이 지금의 자리). 단계를 시계 방향으로 둥글게 놓고
    지금의 자리에 바늘을 둔다. 해는 모델 경로의 해(장부)."""
    if not 표들:
        return ""
    import math
    머리, 줄들 = 표들[0]
    단 = [(r[0], r[1] if len(r) > 1 else "", any("지금" in c for c in r[2:])) for r in 줄들]
    if len(단) < 3:
        return ""
    W, H, cx, cy, R = 360, 300, 180, 150, 78
    s = ['<svg class="viz" viewBox="0 0 %d %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg"><title>%s</title>' % (
        W, H, _e(제목 or "그림"), _e(제목 or "그림"))]
    s.append('<circle cx="%d" cy="%d" r="%d" class="viz-ring"/>' % (cx, cy, R))
    n = len(단)
    지금 = next((k for k, d in enumerate(단) if d[2]), None)
    for k, (이름, 해, 지) in enumerate(단):
        a = -math.pi / 2 + 2 * math.pi * k / n
        x, y = cx + R * math.cos(a), cy + R * math.sin(a)
        s.append('<circle cx="%.1f" cy="%.1f" r="%s" class="%s"/>' % (x, y, "7" if 지 else "5", "viz-dot-2" if 지 else "viz-dot"))
        lx, ly = cx + (R + 16) * math.cos(a), cy + (R + 16) * math.sin(a)
        anc = "start" if math.cos(a) > 0.2 else ("end" if math.cos(a) < -0.2 else "middle")
        dy = -4 if math.sin(a) < -0.5 else (12 if math.sin(a) > 0.5 else 0)
        여유 = (W - 4 - lx) if anc == "start" else ((lx - 4) if anc == "end" else 2 * min(lx - 4, W - 4 - lx))
        줄 = _접기폭(이름, max(60, min(여유, 130)), 13)
        n줄 = len(줄) + (1 if 해 else 0)                    # v4f — 해 줄까지 한 덩어리로(위쪽 단계의 해 줄이 점을 덮었다 — 레터그림검사 ⑤)
        if math.sin(a) < -0.5:
            dy -= 13 * (n줄 - 1)
        elif math.sin(a) <= 0.5:
            dy = 4 - 6.5 * (n줄 - 1)                         # 옆 단계 — 글 덩어리의 가운데를 점 높이에
        for j, t in enumerate(줄):
            s.append('<text x="%.1f" y="%.1f" class="viz-label%s" text-anchor="%s">%s</text>' % (lx, ly + dy + 13 * j, " viz-strong" if 지 else "", anc, _e(t)))
        if 해:
            s.append('<text x="%.1f" y="%.1f" class="viz-tick" text-anchor="%s">%s</text>' % (lx, ly + dy + 13 * len(줄), anc, _e(해)))
        a2 = -math.pi / 2 + 2 * math.pi * (k + 0.5) / n
        s.append('<path d="M %.1f %.1f L %.1f %.1f" class="viz-leader"/>' % (cx + (R - 6) * math.cos(a2), cy + (R - 6) * math.sin(a2),
                                                                       cx + (R + 6) * math.cos(a2), cy + (R + 6) * math.sin(a2)))
    if 지금 is not None:
        a = -math.pi / 2 + 2 * math.pi * 지금 / n
        s.append('<line x1="%d" y1="%d" x2="%.1f" y2="%.1f" class="viz-hand"/>' % (cx, cy, cx + (R - 14) * math.cos(a), cy + (R - 14) * math.sin(a)))
        s.append('<circle cx="%d" cy="%d" r="4" class="viz-dot-2"/>' % (cx, cy))
        s.append('<text x="%d" y="%d" class="viz-label viz-strong" text-anchor="middle">지금</text>' % (cx, cy + 22))
    s.append("</svg>")
    return "".join(s)


def _단계(이름):
    """계산 단계 줄의 셈 — 「(+) …」 더함 · 「(−) …」 뺌 · 「(÷) …」 나눔 · 「= …」 합 · 그 밖은 줄여 감(앞 줄에서 덜어 낸 남은 금액)."""
    t = 이름.strip()
    for 머, 셈 in (("(+)", "+"), ("(−)", "−"), ("(-)", "−"), ("(÷)", "÷"), ("=", "=")):
        if t.startswith(머):
            return 셈, t[len(머):].strip()
    return "", t


def 가치항(표들):
    """그림 「가치」 의 줄 → [{이름, 금액, 셈, a, b, 앞b, 빠짐}] — 셈: 「」 줄여 감(앞 줄 막대에서 줄어든다 · 줄어든 몫 = 유령) · + 쌓기 · − 덜기 ·
    = 0 부터 · ÷ 와 그 뒤는 막대 없이 글(돈의 눈금이 바뀐다). 빠짐 = 셋째 칸의 글(앞 단계에서 빠진 몫 — 「영업비용 570조 원」).
    주석 = 넷째 칸(머리 「비교」 — v4e: 레터 생성기가 장부 키로 셈한 비율 글 「매출 합계의 35%」)."""
    if not 표들:
        return []
    머리, 줄들 = 표들[0]
    i비 = next((i for i, h in enumerate(머리) if i >= 3 and h.strip() == "비교"), None)
    줄들 = [r for r in 줄들 if len(r) >= 2 and r[0].strip()]
    항 = []
    누, 막대끝, 앞b = 0.0, True, None
    for r in 줄들:
        셈, _이름 = _단계(r[0])
        v = 수읽기(r[1])
        빠짐 = r[2].strip() if len(r) > 2 and r[2].strip() not in ("", "—", "-") else ""
        주석 = r[i비].strip() if (i비 is not None and len(r) > i비 and r[i비].strip() not in ("", "—", "-")) else ""
        if 셈 == "÷":
            막대끝 = False
        if not 막대끝 or v is None:
            항.append({"이름": r[0].strip(), "금액": r[1].strip(), "셈": 셈, "a": None, "b": None, "앞b": None, "빠짐": "", "주석": 주석})
            continue
        if 셈 == "+":
            a, b2 = 누, 누 + v
            누 = b2
        elif 셈 == "−":
            a, b2 = 누 - v, 누
            누 = a
        else:
            a, b2 = 0.0, v
            누 = v
        항.append({"이름": r[0].strip(), "금액": r[1].strip(), "셈": 셈, "a": a, "b": b2,
                  "앞b": 앞b if (셈 == "" and 앞b is not None) else None, "빠짐": 빠짐 if 셈 == "" else "", "주석": 주석})
        앞b = b2
    return 항 if len(항) >= 3 else []



def 토네이도줄(표들):
    """그림 「토네이도」 의 줄 → (기준 값, 기준 글, [{이름, 범위, 낮, 높, 낮글, 높글, 낮율, 높율, 폭}]) — 폭(주당가치가 움직인 범위)이 큰 차례.
    표: 가정 · 옮긴 범위 · 낮은 쪽 · 높은 쪽(한쪽만 있으면 다른 칸 「—」)(· 낮은 쪽 변화율 · 높은 쪽 변화율 — v4e, 장부 키로 셈한 글),
    이름이 「기준」 으로 시작하는 줄이 기준."""
    if not 표들:
        return None, "", []
    머리, 줄들 = 표들[0]
    i율 = {쪽: next((i for i, h in enumerate(머리) if 쪽 in h and "변화율" in h), None) for 쪽 in ("낮", "높")}
    기, 기글, 줄 = None, "", []
    for r in 줄들:
        if not r or not r[0].strip():
            continue
        이름 = re.sub(r"\*", "", r[0]).strip()
        칸 = [c.strip() for c in r[1:]]
        if 이름.startswith("기준"):
            for c in 칸:
                if 수읽기(c) is not None:
                    기, 기글 = 수읽기(c), re.sub(r"\*", "", c)
                    break
            continue
        if len(칸) < 3:
            continue
        율 = {쪽 + "율": (re.sub(r"\*", "", r[i]).strip() if (i is not None and i < len(r) and 수읽기(r[i]) is not None) else "")
             for 쪽, i in i율.items()}
        줄.append(dict({"이름": 이름, "범위": 칸[0], "낮글": 칸[1], "높글": 칸[2], "낮": 수읽기(칸[1]), "높": 수읽기(칸[2])}, **율))
    if 기 is None:
        return None, "", []
    줄 = [d for d in 줄 if d["낮"] is not None or d["높"] is not None]
    for d in 줄:
        lo = d["낮"] if d["낮"] is not None else 기
        hi = d["높"] if d["높"] is not None else 기
        d["폭"] = max(lo, hi, 기) - min(lo, hi, 기)
    줄.sort(key=lambda d: -d["폭"])
    return 기, 기글, 줄



def 띠(표들, 제목=""):
    """3분 레터 첫 화면의 요약 띠(통독 v4 상-3) — HTML. 표: 요약 · 값 · 덧말(1~4줄). 값은 표의 글 그대로 크게(숫자는 표 = 장부의 글).
    「그림의 숫자」 를 달지 않는다(띠의 글이 곧 숫자다)."""
    if not 표들:
        return ""
    머리, 줄들 = 표들[0]
    칸 = {h.strip(): i for i, h in enumerate(머리)}
    i값 = 칸.get("값", 1)
    i덧 = 칸.get("덧말", 2)
    항 = []
    for r in 줄들:
        if not r or not r[0].strip():
            continue
        값 = r[i값].strip() if i값 < len(r) else ""
        덧 = r[i덧].strip() if i덧 < len(r) else ""
        if not 값 or 값 in ("—", "-"):
            continue
        항.append('<div class="stat"><span class="stat-k">%s</span><b>%s</b>%s</div>' % (
            _e(re.sub(r"\*", "", r[0]).strip()), _e(re.sub(r"\*", "", 값)),
            ('<span class="stat-d">%s</span>' % _e(re.sub(r"\*", "", 덧))) if 덧 and 덧 not in ("—", "-") else ""))
    if not 항:
        return ""
    return '<div class="stat-row" role="group" aria-label="%s" style="--n:%d">%s</div>' % (_e(제목 or "요약"), min(len(항), 4), "".join(항))


그림들 = {"띠": 띠, "신호": 신호, "폭포": 폭포, "궤적": 궤적, "계단": 계단, "시계": 시계}      # 가치 · 길 · 자 · 토네이도는 `레터그림판`(두 판)

# 페이지에 넣는 CSS — v4e(2026-10-16 디자이너 리뷰 2순위): 그림의 색은 본문 토큰 하나로 — 초점 --accent · 대비 --flag · 맥락선 --vz-ctx ·
# 면 맥락 --rule(+ 1px 맥락선 테두리) · 눈금선 --vz-grid · 글 --ink · --ink-2 · --muted. 회색은 본문과 같은 푸른 회색 하나.
# 맥락선은 리뷰 제안 #8B95A1 이 밝은 바탕 대비 2.94 라 그래픽 3:1(WCAG 1.4.11)을 못 넘어 #848E9A(3.21)로 한 칸 진하게 — 어두운 쪽 #5C6570(3.15) 은 그대로.
# 옛 이름(--viz-1 · --viz-2 · --viz-muted …)은 그대로 두고 토큰을 가리키게 했다(그림 열아홉이 같은 토큰). 대비 · 글자 크기 · 겹침 · 가림은 `레터그림검사`.
# v4f — 화면 폭 420px 이하에서는 그림(SVG)만 본문 여백 쪽으로 나와 358px(390px 휴대폰의 그림 폭 — `레터그림검사` ① 이 재는 폭)를 쓴다.
# 375px 화면에서 본문 폭 343px 에 그대로 두면 한 판 그림(viewBox 360)의 눈금 글 12.5 가 11.9px 로 줄었다(실측). 화면 끝과는 4px 이상 띄우고
# (360px 화면은 352px — 눈금 글 12.2px), 그림 판 · 글 자리는 그대로다(크기만 바뀐다). 인쇄 · 데스크톱은 그대로.
CSS = """
.viz-fig{margin:1.6rem 0}
.viz-fig .viz{display:block; width:100%; max-width:28rem; height:auto; margin:.4rem 0 .2rem}
.viz-fig .viz.viz-wide{max-width:560px}
.viz-fig .viz.viz-narrow{display:none}
@media (max-width:640px){ .viz-fig .viz.viz-wide{display:none} .viz-fig .viz.viz-narrow{display:block; max-width:none} }
@media screen and (max-width:420px){ .viz-fig .viz{width:max(100%, min(358px, 100vw - 8px)); max-width:none;
  margin-left:calc((100% - max(100%, min(358px, 100vw - 8px))) / 2)} }
.viz-fig figcaption{font-size:.9rem; color:var(--ink-2); margin:.2rem 0 .4rem}
.viz-fig figcaption strong{color:var(--ink)}
.viz-fig details{margin:.3rem 0 0; font-size:.85rem; color:var(--muted)}
.viz-fig details summary{cursor:pointer}
.viz-src{font-size:12px; line-height:1.5; color:var(--muted); margin:.25rem 0 0; max-width:560px}
:root{--vz-ctx:#8D8D8D; --vz-grid:#E8E8E8; --vz-c2:#1192E8; --vz-c4:#9F1853; --vz-c5:#6F6F6F; --vz-c6:#B28600;
  --viz-1:var(--s1); --viz-2:var(--s2); --viz-grid:var(--vz-grid); --viz-axis:var(--vz-ctx); --viz-muted:var(--muted);
  --viz-warn:#B7791F; --viz-crit:var(--flag)}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){--vz-ctx:#8D8D8D; --vz-grid:#393939; --vz-c2:#33B1FF; --vz-c4:#FF7EB6; --vz-c5:#A8A8A8; --vz-c6:#D2A106;
  --viz-warn:#D9A23A} }
:root[data-theme="dark"]{--vz-ctx:#8D8D8D; --vz-grid:#393939; --vz-c2:#33B1FF; --vz-c4:#FF7EB6; --vz-c5:#A8A8A8; --vz-c6:#D2A106; --viz-warn:#D9A23A}
.viz text{font-family:var(--sans); fill:var(--ink);
  paint-order:stroke; stroke:var(--paper); stroke-width:3px; stroke-linejoin:round}
.viz .viz-tick{font-size:12.5px; fill:var(--muted); font-variant-numeric:tabular-nums}
.viz .viz-label{font-size:13px; fill:var(--ink-2)}
.viz .viz-name{fill:var(--ink-2); font-size:12.5px}
.viz .viz-value{font-variant-numeric:tabular-nums}
.viz .viz-strong{font-weight:700; fill:var(--ink)}
.viz .viz-muted{fill:var(--muted)}
.viz .viz-note{fill:var(--ink-2)}
.viz .viz-note-flag{fill:var(--flag)}
.viz .viz-grid{stroke:var(--vz-grid); stroke-width:1}
.viz .viz-axis{stroke:var(--vz-ctx); stroke-width:1}
.viz .viz-axis-tick{stroke:var(--vz-ctx); stroke-width:1}
.viz .viz-zero{stroke:var(--ink-2); stroke-width:1}
.viz .viz-leader{stroke:var(--vz-ctx); stroke-width:1; fill:none}
.viz .viz-line{fill:none; stroke:var(--s1); stroke-width:2; stroke-linejoin:round; stroke-linecap:round}
.viz .viz-ref-1{stroke:var(--s1); stroke-width:2}
.viz .viz-ref-2{stroke:var(--s2); stroke-width:1.5}
.viz .viz-ref-3{stroke:var(--vz-ctx); stroke-width:1.2; stroke-dasharray:4 3}
.viz .viz-dot{fill:var(--s1); stroke:var(--paper); stroke-width:2}
.viz .viz-dot-soft{fill:var(--vz-ctx); stroke:var(--paper); stroke-width:2}
.viz .viz-dot-2{fill:var(--s2); stroke:var(--paper); stroke-width:2}
.viz .viz-dot-hollow{fill:var(--paper); stroke:var(--vz-ctx); stroke-width:2}
.viz .viz-hit{fill:transparent}
.viz .viz-line-thin{stroke-width:1.6}
.viz .viz-line-past{fill:none; stroke:var(--vz-ctx); stroke-width:1.6; stroke-dasharray:4 3}
.viz .viz-line-2{fill:none; stroke:var(--s2); stroke-width:2; stroke-linejoin:round; stroke-linecap:round}
.viz .viz-bar{fill:var(--s1)}
.viz .viz-bar-soft{fill:var(--s1-soft); stroke:var(--s1); stroke-width:1.5}
.viz .viz-total{fill:var(--ink-2)}
.viz .viz-band{fill:var(--paper-2)}
.viz .viz-mark{fill:var(--flag); opacity:.08}
.viz .viz-ring{fill:none; stroke:var(--vz-grid); stroke-width:10}
.viz .viz-hand{stroke:var(--ink); stroke-width:3; stroke-linecap:round}
.viz .vz-step{fill:var(--s1)}
.viz .vz-gone{fill:var(--rule); stroke:var(--vz-ctx); stroke-width:1}
.viz .vz-add{fill:var(--s1-soft); stroke:var(--s1); stroke-width:1.5}
.viz .vz-sum{fill:var(--ink)}
.viz .vz-band{fill:var(--paper-2)}
.viz .vz-past{fill:none; stroke:var(--vz-ctx); stroke-width:1.5; stroke-linejoin:round}
.viz .vz-past-dot{fill:var(--vz-ctx); stroke:var(--paper); stroke-width:1.5}
.viz .vz-path{fill:none; stroke:var(--s1); stroke-width:2.4; stroke-linejoin:round; stroke-linecap:round}
.viz .vz-dot-acc{fill:var(--s1); stroke:var(--paper); stroke-width:2}
.viz .vz-dot-ctx{fill:var(--vz-ctx); stroke:var(--paper); stroke-width:2}
.viz .vz-dot-hollow{fill:var(--paper); stroke:var(--vz-ctx); stroke-width:2}
.viz .vz-dot-flag{fill:var(--flag); stroke:var(--paper); stroke-width:2}
.viz .vz-trace{fill:var(--paper); stroke:var(--ink); stroke-width:2}
.viz .vz-tail{stroke:var(--ink); stroke-width:1.5}
.viz .vz-arrow{fill:var(--ink)}
.viz .vz-ref-flag{stroke:var(--flag); stroke-width:1.5}
.viz .vz-ref-ctx{stroke:var(--vz-ctx); stroke-width:1.2; stroke-dasharray:4 3}
.viz .vz-bracket{fill:none; stroke:var(--ink); stroke-width:1.2}
.viz .vz-track{stroke:var(--vz-ctx); stroke-width:1}
.viz .vz-base{fill:none; stroke:var(--ink); stroke-width:1.5}
.motion-fig{margin:1.6rem 0}
.motion-ctl{display:flex; flex-wrap:wrap; align-items:center; justify-content:flex-end; gap:.45rem; max-width:560px; margin:.35rem 0 .1rem}
.motion-ctl button{font:500 13px/1.2 var(--sans); color:var(--ink-2); background:var(--paper);
  border:1px solid var(--rule-2); border-radius:3px; padding:.35rem .7rem; min-height:34px; display:inline-flex; align-items:center; gap:.4rem;
  cursor:pointer; font-variant-numeric:tabular-nums}
.motion-ctl button:hover{color:var(--ink); border-color:var(--muted)}
.motion-ctl button:disabled{opacity:.45; cursor:default}
.motion-ctl button svg{width:10px; height:10px; fill:currentColor; flex:none}
.motion-ctl .m-dots{display:inline-flex; gap:5px; margin-right:.2rem} .motion-ctl .m-dots i{width:7px; height:7px; border-radius:50%; background:var(--rule-2)}
.motion-ctl .m-dots i.on{background:var(--accent)}
.motion-ctl [hidden]{display:none !important}
.motion-ctl .m-say{position:absolute; width:1px; height:1px; overflow:hidden; clip-path:inset(50%); white-space:nowrap}
@media (pointer:coarse){ .motion-ctl button{min-height:44px; min-width:44px} }
.to-top.motion-near{opacity:0 !important; pointer-events:none !important}
h2 small.old{display:block; font-family:var(--sans); font-size:.82rem; font-weight:400; color:var(--muted);
  margin-top:.2rem; letter-spacing:0}
@media (prefers-reduced-motion: reduce){ .motion-ctl{display:none !important} }
@media print{ .motion-ctl{display:none !important} .viz-fig .viz.viz-narrow{display:none !important} .viz-fig .viz.viz-wide{display:block !important} }
.viz .viz-up{fill:var(--s1)} .viz .viz-down{fill:var(--s2)}
.viz-signals{list-style:none; padding:0; margin:.6rem 0}
.viz-signals li{display:flex; gap:.7rem; padding:.7rem 0; border-top:1px solid var(--rule)}
.viz-signals li:last-child{border-bottom:1px solid var(--rule)}
.viz-signals p{margin:0; line-height:1.55}
.viz-light{flex:0 0 auto; width:.8rem; height:.8rem; margin-top:.35rem; border-radius:50%; background:var(--viz-axis); box-sizing:border-box}
.viz-st-on{background:var(--viz-crit)} .viz-st-near{background:var(--viz-warn)}
.viz-st-off{background:transparent; border:2px solid var(--viz-muted)}
.viz-sig-name{font-weight:700}
.viz-sig-state{font-weight:500; font-size:.85rem; color:var(--ink-2); margin-left:.5rem}
.viz-sig-row{font-size:.92rem; color:var(--ink-2); display:grid; grid-template-columns:3.2rem 1fr}
.viz-sig-key{color:var(--muted); font-size:.85rem; padding-top:.08rem}
.stat-row{display:grid; grid-template-columns:repeat(var(--n,3), minmax(0,1fr)); gap:1rem 1.2rem; margin:1.4rem 0 1.8rem;
  border-top:2px solid var(--ink); padding-top:.9rem}
.stat{min-width:0; display:grid; grid-row:span 3; grid-template-rows:subgrid; row-gap:0}
.stat .stat-k{display:block; font-size:.8rem; line-height:1.4; color:var(--muted); align-self:end}
.stat b{display:block; font:700 1.9rem/1.15 var(--sans); font-variant-numeric:tabular-nums;
  color:var(--ink); margin:.25rem 0 .2rem; letter-spacing:-.01em; word-break:keep-all}
.stat .stat-d{display:block; font-size:.8rem; line-height:1.45; color:var(--ink-2)}
@media (max-width:640px){ .stat-row{grid-template-columns:1fr 1fr} .stat:first-child{grid-column:1/-1} .stat b{font-size:1.65rem} }
@media print{ .viz-fig{break-inside:avoid} .viz-fig details{display:none} .viz-signals li{break-inside:avoid}
  .viz-fig .viz, .viz-fig .viz.viz-wide{max-height:95mm; width:auto; max-width:min(100%, 118mm)} .viz-src{font-size:7.5pt; margin:.1rem 0 0}
  .stat-row{gap:.4rem .9rem; margin:.5rem 0 .7rem; padding-top:.4rem; border-top-width:1.5px; break-inside:avoid}
  .stat b{font-size:15pt; margin:.08rem 0} .stat .stat-k, .stat .stat-d{font-size:7.5pt; line-height:1.3} }
"""

# 2026-10-16 — 본편(모델을 세운 순서)의 그림: 변수 연결도 · 매출 구분별 물량 · 가격 · 매출 · 쌓은 막대 · 비중 변화 · 공장 ROIC · 민감도 격자 · 주가 곡선
import 레터그림본편 as _본편  # noqa: E402
import 레터그림판 as _판  # noqa: E402

그림들.update(_본편.그림들)
그림들.update(_판.그림들)
두판 = tuple(_판.그림들)                 # 넓은 · 좁은 두 판으로 그리는 그림(HTML 이 둘 다 싣고 화면 폭으로 고른다)
길, 자, 가치, 토네이도, 길차례 = _판.길, _판.자, _판.가치, _판.토네이도, _판.길차례      # 옛 이름으로 부르는 곳(시험 · 미리보기)을 위해
CSS += _본편.CSS

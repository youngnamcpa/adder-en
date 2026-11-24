# -*- coding: utf-8 -*-
"""민감도격자 — 인터랙티브 레터(`레터인터랙티브.py`)가 읽는 격자를 파이썬 엔진으로 미리 낸다(2026-10-23 · 연구/레터_인터랙티브판_제안검토_20261023.md 2절 ①).

**JS 로 DCF 를 다시 셈하지 않는다** — 화면의 슬라이더 · 히트맵은 이 파일의 칸을 고를 뿐이다(칸 사이 보간 없음). 엔진은 하나, 값은 전부 엔진 결과의 줄이다.

    python -X utf8 스크립트/민감도격자.py 가정.json [--낼 경로] [--칸 11] [--시나리오 기준]

내는 것 — 가정 곁 `_raw/민감도격자.json`(레터의 재료 파일 — 장부에 sha256 이 남고 게이트 ⑦ 이 맞춘다)
  기준       기준 시나리오 결과(주당가치 · WACC · 영구가치 비중 · 영구기간 영업이익률 · 연도 칸 매출 · 영업이익률 · FCFF · 모션 재료)
  표1        WACC(가로) × 영구성장률(세로) — 칸 N × N(기본 11 · 각 ±1.0%p · 0.2%p 간격). 엔진이 막는 칸(g ≥ WACC)은 「해당 없음」
  표2        WACC(가로) × 영구기간 영업이익률(세로) — 칸 N × N(±2.0%p · 0.4%p)
  역산곡선   WACC 칸마다 종가가 성립하는 역산 축의 값(가정 `역산.축` · 없으면 엔진의 유형 기본 축) — 풀이가 없으면 까닭(엔진 역산 그대로)
  손잡이     `Narrative.동인.표`(에이전트가 추린 변수)의 장부 키를 엔진 손잡이로 — `가:눈` → 정상 수준을 비관 ~ 기준 ~ 낙관 선 위로 ·
             `민:요약:i` → 엔진 요약 민감도 i 번째(0부터) · `대안:a:b` → WACC(근거 범위 = 그 행의 두 대안). 표가 없으면 엔진 요약 목록 +
             매출 증가율 · 예측 끝 영업이익률 + WACC 가운데 근거 범위 안에서 주당가치를 가장 크게 움직인 넷. 꼴마다 눈금 규칙(`자동눈금`)
  짝         근거 범위 안에서 가장 크게 움직인 두 손잡이의 짝 격자(함께 옮긴 칸)
  드릴       기준 시나리오 가치 다리의 현금성 · 이자부부채 세부(11번 줄 — 이름은 스캐폴드와 좌표 지도에서)
  모(결과마다) 구분별 매출 쌓기(잎 구분 — 하위가 없는 구분 · 실적 몫은 한 덩어리) · 매출 → 영업이익 → NOPLAT → FCFF(2번 11 · 15 · 19 · 23) ·
             현가계수(35) · FCFF 현가(36) · 영구가치(50 · 46 · 47 · 51 · 53 · 54) · 그 끝없는 흐름의 해마다 몫(그림값) · 가치 다리(40 · 54 ·
             영업가치 조정 · 58 · 59~65 · 66 · 152 · 68)
검산(결과마다 — 어긋나면 멈춘다): 36 = 23 × 35 · 40 = Σ36 · 54 = 51 × 53 · 흐름의 끝없는 합 = 54 · 잎 구분 합 = 매출액(남으면 「그 밖의 매출」)
지렛대(2026-10-25 레터 재구성 R3) — 레터의 「값을 가르는 가정」(`레터이야기.지렛대독립` — 결론 · 민감도 · 3분과 같은 가정)이 손잡이에 없으면 더한다
             (시나리오가 가른 가정은 꼴 「시나리오보간」 — 비관 −1 ~ 낙관 +1 사이를 열마다 선형 · 민감도 표 Ⅲ 의 지렛대는 그 손잡이). 후보를 넷으로 줄일 때도 남긴다.
             손잡이 이름은 본편 가정 표의 이름이다(내부 번호 「A-182」 를 화면에 내지 않는다 — `레터이야기.손잡이본편이름`).
값을 정하지 않는다. 회사 · 업종 이름은 이 도구에 없다. 날짜 키는 `만든날`(닫힘 검사 ⑦ 이 「평가기준일 뒤 자료」로 잡지 않게).
종료 코드 — 0 통과 · 2 입력 오류(가정을 엔진이 계산하지 못함 · 파일 없음).
"""
from __future__ import annotations

import argparse
import ast
import datetime
import hashlib
import importlib
import io
import json
import os
import re
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass
여기 = os.path.dirname(os.path.abspath(__file__))
키트 = os.path.dirname(여기)
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 입력오류  # noqa: E402

형식 = "민감도격자 1"
흐름수 = 12                                           # 영구가치 그림에 그리는 해의 수(나머지는 「그 뒤 해들」 한 덩어리)
금액줄 = {1: "13", 2: "21", 3: "27", 4: "33", 5: "39", 6: "44"}        # 엔진 4번 — 구분 s 의 매출액(그 기간 금액) 줄
드릴줄 = {"현금성": (18, 19, 20), "이자부부채": (23, 24, 25, 26, 28, 29, 106, 107)}   # 11번 — 엔진 noa 의 현금성 · 차입 줄


def _n(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def 가정해시(가정):
    """레터 장부 · 워크북 마감과 같은 셈(정렬한 키 · 공백 없는 JSON 의 sha256 · `_경로` 키 뺌) — 파일 바이트로 재면 같은 가정이어도 장부와 갈린다(2026-10-23)."""
    깨끗 = {k: v for k, v in 가정.items() if not ("%s" % k).startswith("_경로")}
    return hashlib.sha256(json.dumps(깨끗, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def _엔진():
    import 엔진                                          # noqa: F401
    from 엔진 import 계산, 가정오류                       # noqa: PLC0415
    민 = importlib.import_module("엔진.민감도")            # 꾸러미의 `민감도` 는 같은 이름의 함수가 가린다 — 모듈을 이름으로
    return 계산, 가정오류, 민


def 엔진지문():
    파일 = sorted(os.path.join(여기, "엔진", f) for f in os.listdir(os.path.join(여기, "엔진")) if f.endswith(".py")) + [os.path.join(여기, "기간축.py")]
    return hashlib.sha256(b"".join(open(p, "rb").read() for p in 파일)).hexdigest()[:16]


def 조정줄이름():
    """레터가 쓰는 영업가치 조정 줄 이름(`레터.영업가치조정줄`) — 레터를 불러오지 않고 글로 읽는다. 못 읽으면 빈 목록(남은 몫은 「그 밖의」 한 줄)."""
    try:
        src = io.open(os.path.join(여기, "레터.py"), encoding="utf-8").read()
        for node in ast.parse(src).body:
            if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "영업가치조정줄" for t in node.targets):
                return [list(x) for x in ast.literal_eval(node.value)]
    except Exception:                                # noqa: BLE001
        pass
    return []


_줄이름캐시 = {}


def 줄이름(시트, 번호):
    """스캐폴드의 그 줄 이름 — 좌표 지도(`좌표.지도찾기`)가 정한 이름 칸에서 읽는다(칸 주소를 손으로 세지 않는다). 못 찾으면 None."""
    k = (시트, int(번호))
    if k in _줄이름캐시:
        return _줄이름캐시[k]
    이 = None
    try:
        import openpyxl                              # noqa: PLC0415
        import 좌표                                   # noqa: PLC0415
        if "_wb" not in _줄이름캐시:
            틀 = os.path.join(키트, "DCF_워크북_스캐폴드.xlsx")
            _줄이름캐시["_지"] = 좌표.지도찾기(틀)
            _줄이름캐시["_wb"] = openpyxl.load_workbook(틀, read_only=True)
        지, wb = _줄이름캐시["_지"], _줄이름캐시["_wb"]
        열ID = 지.이름열ID(시트)
        if 열ID is not None:
            시트명, a = 지.자리(시트, 열ID, int(번호))
            if a is not None and 시트명 in wb.sheetnames:
                v = wb[시트명][a].value
                이 = ("%s" % v).strip() if v else None
    except Exception:                                # noqa: BLE001
        이 = None
    _줄이름캐시[k] = 이
    return 이


# ────────────────────────────────────────────────── 단위 · 기간

def 단위정하기(메타, 기준영업가치):
    """금액 표시 단위 — 금액단위(백만원 · 백만달러 …)와 영업가치의 크기로. 나눔 = 엔진 금액을 나눌 값."""
    단 = (메타.get("금액단위") or "").replace(" ", "")
    v = abs(기준영업가치 or 0)
    if 단 == "백만원":
        if v >= 1e6:
            return {"글": "조 원", "나눔": 1e6}
        if v >= 1e2:
            return {"글": "억 원", "나눔": 1e2}
        return {"글": "백만 원", "나눔": 1.0}
    if 단 == "백만달러":
        if v >= 1e2:
            return {"글": "억 달러", "나눔": 1e2}
        return {"글": "백만 달러", "나눔": 1.0}
    return {"글": 메타.get("금액단위") or "", "나눔": 1.0}


def 잎구분(가정):
    """매출 구분 가운데 하위 구분이 없는 것(잎) — 예측 열에서 잎의 합 = 매출액 합계(54). [(번호, 이름)]."""
    구분 = (가정.get("구조") or {}).get("매출구분") or []
    상위들 = {x.get("상위") for x in 구분 if x.get("상위")}
    return [(x["번호"], x.get("이름") or "구분 %d" % x["번호"]) for x in 구분 if x["번호"] not in 상위들 and x["번호"] in 금액줄]


def 열이름(p, 결산월):
    """기간 속성 → 화면 이름. 12개월 열은 회계연도(결산월이 12월이 아니면 FY), 짧은 열은 상반기 · 하반기 · m~n월."""
    y = p["회계연도"]
    if p["구분"] == "영구기간":
        return "%d~" % y if 결산월 == 12 else "FY%d~" % y
    if (p.get("개월") or 12) >= 12:
        return ("%d" % y) if 결산월 == 12 else "FY%d" % y
    m1, m2 = int(p["시작일"][5:7]), int(p["종료일"][5:7])
    if (m1, m2) == (7, 12):
        return "%d 하반기" % y
    if (m1, m2) == (1, 6):
        return "%d 상반기" % y
    return "%d %d~%d월" % (y, m1, m2)


def 연도축(R):
    """기간 축 → 연도 칸(같은 회계연도의 열은 한 칸으로 더한다). 영구기간은 「영구」."""
    속 = R["기간"]["속성"]
    칸, 본 = [], {}
    for cid, p in 속.items():
        키 = "영구" if p["구분"] == "영구기간" else str(p["회계연도"])
        if 키 not in 본:
            본[키] = len(칸)
            칸.append({"이름": 키, "열": [], "실적": False, "추정": False})
        c = 칸[본[키]]
        c["열"].append(cid)
        c["실적" if p["구분"] == "실적" else "추정"] = True
    return 칸


# ────────────────────────────────────────────────── 결과에서 페이지가 쓰는 것만

def 뽑기(R, 칸, 단위, 조정줄, 잎):
    d, s = R["2.DCF"], R["요약"]
    k = 1.0 / 단위["나눔"]
    속 = R["기간"]["속성"]
    예측 = [c for c, p in 속.items() if p["구분"] == "예측"]

    def 합(줄, 열들):
        vs = [_n(d[줄].get(c)) for c in 열들]
        vs = [v for v in vs if v is not None]
        return sum(vs) if vs else None

    S4 = R["4.Sales"]
    쌓기 = []
    for c in 칸:
        실 = sum(_n(d["11"].get(x)) or 0.0 for x in c["열"] if 속[x]["구분"] == "실적")
        추 = [x for x in c["열"] if 속[x]["구분"] != "실적"]
        조각 = [sum(_n((S4.get(금액줄[b]) or {}).get(x)) or 0.0 for x in 추) for b, _이 in 잎]
        전체 = sum(_n(d["11"].get(x)) or 0.0 for x in c["열"])
        남 = 전체 - 실 - sum(조각)
        if not 추 and abs(남) > 1e-6 * max(1.0, abs(전체)):
            raise AssertionError("실적 칸의 매출이 맞지 않는다")
        쌓기.append([round(실 * k, 5)] + [round(v * k, 5) for v in 조각] + [round(남 * k, 5) if abs(남) > 0.5 else 0.0])
    단계 = [[round((_n(d[줄][c]) or 0.0) * k, 6) for 줄 in ("11", "15", "19", "23")] for c in 예측]
    매, 이, 현 = [], [], []
    for c in 칸:
        m, o = 합("11", c["열"]), 합("15", c["열"])
        매.append(None if m is None else round(m * k, 5))
        이.append(None if (not m or o is None) else round(o / m, 5))
        f = 합("23", c["열"])
        현.append(None if f is None else round(f * k, 5))
    F = [_n(d["23"][c]) for c in 예측]
    계수 = [_n(d["35"][c]) for c in 예측]
    현가 = [_n(d["36"][c]) for c in 예측]
    for f, a, v in zip(F, 계수, 현가):
        if abs(f * a - v) > 1e-6 * max(1.0, abs(v)):
            raise AssertionError("36 ≠ 23 × 35")
    if abs(sum(현가) - d["40"]) > 1e-6 * max(1.0, abs(d["40"])):
        raise AssertionError("40 ≠ Σ36")
    F0, W, g, V, a53, V54 = d["50"], d["46"], d["47"], d["51"], d["53"], d["54"]
    if abs(V * a53 - V54) > 1e-6 * max(1.0, abs(V54)):
        raise AssertionError("54 ≠ 51 × 53")
    흐름 = [F0 * (1 + g) ** (j - 1) / (1 + W) ** j * a53 for j in range(1, 흐름수 + 1)]
    명목 = [F0 * (1 + g) ** (j - 1) for j in range(1, 흐름수 + 1)]
    if abs(F0 / (W - g) * a53 - V54) > 1e-6 * max(1.0, abs(V54)):    # Σ_{j≥1} 흐름 의 닫힌 꼴 = 54
        raise AssertionError("영구가치 흐름의 합 ≠ 54")
    조정 = []
    for 키, 말 in 조정줄:
        v = _n(d.get(키))
        if v:
            조정.append([말, round(v * k, 6)])
    남 = d["58"] - d["40"] - d["54"] - sum(_n(d.get(키)) or 0.0 for 키, _ in 조정줄)
    if abs(남) > 0.5:
        조정.append(["(±) 그 밖의 영업가치 조정", round(남 * k, 6)])
    더뺌 = [("59", "(+) 비영업자산", 1), ("60", "(+) 현금 및 단기금융자산", 1), ("61", "(−) 이자부부채", -1), ("62", "(−) 우선주", -1),
          ("63", "(−) 비지배지분", -1), ("64", "(−) 순확정급여부채", -1), ("65", "(±) 기타 조정항목", 1)]
    주주 = []
    for 키, 말, 부 in 더뺌:
        v = _n(d.get(키))
        if v:
            주주.append([말, round(부 * v * k, 6), 키])
    # 2026-10-25 날짜 둘 — 이월 판(2번 161 이 선 판)은 차감 뒤 남는 것이 재무 자료 기준일 주주가치(161)이고, 평가기준일 주주가치(66)까지는
    # 이월 계수 · 두 날 사이 자본거래가 잇는다 — 「그 밖의 조정」 에 섞지 않고 따로 한 줄(옛 판은 161 이 없어 그대로)
    재주 = _n(d.get("161")) if "161" in d else None
    남2 = (재주 if 재주 is not None else d["66"]) - d["58"] - sum(부 * (_n(d.get(키)) or 0.0) for 키, _말, 부 in 더뺌)
    if abs(남2) > 0.5:
        주주.append(["(±) 그 밖의 조정", round(남2 * k, 6), None])
    if 재주 is not None:
        주주.append(["(±) 평가기준일로 이월 · 자본거래", round((d["66"] - 재주) * k, 6), None])
    모 = {"쌓기": 쌓기, "단계": 단계, "F": [round(x * k, 6) for x in F], "계수": [round(x, 8) for x in 계수], "현가": [round(x * k, 6) for x in 현가],
         "합": round(d["40"] * k, 6),
         "TV": {"F": round(F0 * k, 6), "W": W, "g": g, "V": round(V * k, 6), "계수": round(a53, 8), "현가": round(V54 * k, 6)},
         "흐름": [round(x * k, 6) for x in 흐름], "명목": [round(x * k, 6) for x in 명목],
         "조정": 조정, "영업": round(d["58"] * k, 6), "더뺌": 주주, "주주": round(d["66"] * k, 6), "주식": d["152"], "주당": round(d["68"], 4)}
    return {"주": round(s["주당가치"], 4), "W": round(s["예측기간WACC"], 6), "TV비중": round(s["영구가치비중"], 5),
            "TV이익률": round(s["영구기간영업이익률"], 5), "매출": 매, "이익률": 이, "FCFF": 현, "모": 모}


def _엔진문장(e):
    """엔진 오류 문장 — 끝의 설계 문서 꼬리표(「(설계/… 의 6)」)만 뗀다. 나머지는 엔진이 낸 그대로."""
    return re.sub(r"\(설계/[^)]*\)\s*$", "", ("%s" % e).strip()).strip()


# ────────────────────────────────────────────────── 손잡이 — 동인 표 · 요약 민감도에서

def _연도칸인가(가정, 대상):
    for n in 대상:
        벌 = (가정.get("시점가정") or {}).get(n)
        if not isinstance(벌, dict):
            return False
        v = 벌.get("기준", 벌.get("공통"))
        if not (isinstance(v, (int, float)) and float(v).is_integer() and 1900 <= v <= 2200):
            return False
    return bool(대상)


def 동인손잡이(가정, 민):
    """`Narrative.동인.표` → 손잡이 선언 목록. 표가 없으면 엔진 요약 민감도 목록 + 매출 증가율 · 예측 끝 영업이익률 + WACC(후보)."""
    표 = (((가정.get("Narrative") or {}).get("동인") or {}).get("표")) or []
    요 = 민.요약목록(가정)
    낸, 본 = [], set()
    for x in 표:
        키 = next((x.get(k) for k in ("낮음", "높음") if x.get(k)), None)
        if not 키:
            continue
        p = 키.split(":")
        if p[:2] == ["가", "눈"]:
            d = {"id": "정상수준", "이름": x.get("이름"), "꼴": "시나리오축", "엔진손잡이": "정상수준", "범위글": x.get("범위")}
        elif p[:2] == ["민", "요약"] and len(p) >= 3 and p[2].isdigit() and int(p[2]) < len(요):
            d = {"id": "요약%s" % p[2], "이름": x.get("이름"), "꼴": None, "엔진손잡이": 요[int(p[2])], "범위글": x.get("범위")}
        elif p[0] == "대안":
            vs = []
            for k in ("낮음", "높음"):
                q = (x.get(k) or "").split(":")
                if len(q) >= 3 and q[0] == "대안":
                    vs.append(float(q[1]))
            d = {"id": "WACC", "이름": x.get("이름"), "꼴": "값", "엔진손잡이": "WACC", "범위글": x.get("범위"),
                 "근거범위": {"값": [min(vs), max(vs)]} if len(vs) == 2 else None}
        else:
            continue
        if d["id"] not in 본:
            본.add(d["id"])
            낸.append(d)
    if not 낸:
        for i, h in enumerate(요):
            낸.append({"id": "요약%d" % i, "이름": h["이름"], "꼴": None, "엔진손잡이": h, "_후보": True})
        for 이 in ("매출성장", "목표마진"):
            낸.append({"id": 이, "이름": None, "꼴": None, "엔진손잡이": 이, "_후보": True})
        낸.append({"id": "WACC", "이름": "WACC", "꼴": "값", "엔진손잡이": "WACC", "_후보": True})
    return 낸


def 퍼(v, 자):
    return ("%." + str(자) + "f%%") % (v * 100)


_구조캐시 = {}


def _구조(가정):
    """레터가 쓰는 구조(`엔진.스키마.검증전부` 의 셋째 — 기본값을 채운 구조). 못 읽으면 가정의 「구조」 그대로."""
    k = id(가정)
    v = _구조캐시.get(k)
    if v is None or v[0] is not 가정:                     # 같은 객체일 때만 다시 쓴다(객체를 쥐고 있어 id 가 다른 가정에 다시 쓰이지 않는다)
        try:
            구 = importlib.import_module("엔진.스키마").검증전부(가정)[2] or {}
        except Exception:                                # noqa: BLE001
            구 = (가정 or {}).get("구조") or {}
        v = _구조캐시[k] = (가정, 구)
    return v[1]


def _가정이름(가정, n):
    """가정 번호 → 본편 가정 표의 이름(레터 · 부록 가정 일람과 같은 셈 — `레터.가정이름` · `레터이야기.이름다듬기`). 모르면 ""(내부 번호를 내지 않는다)."""
    try:
        import 레터 as _L                                    # noqa: PLC0415
        import 레터이야기 as _N                               # noqa: PLC0415
        이 = _L.가정이름("%s" % n, _구조(가정))
        return _N.이름다듬기(이) if 이 else ""
    except Exception:                                    # noqa: BLE001
        return ""


def 구분이름(가정, n):
    """정상 수준 칸(6s6)의 매출 구분 이름 — 화면에서 그 칸 값 앞에 붙는다(「NAND 0.85」). 구분을 못 찾으면 본편 가정 이름(내부 번호 「A-626」 를 내지 않는다)."""
    if not ("%s" % n).isdigit():
        return 칸말(n, 가정)
    s = (int(n) - 600) // 10
    for x in (가정.get("구조") or {}).get("매출구분") or []:
        if x.get("번호") == s:
            return x.get("이름")
    return _가정이름(가정, n)


_6칸말 = {6: "정상 수준", 8: "유지 종료", 9: "정상 수준 도달"}


def 칸말(n, 가정=None):
    """손잡이 대상 → 화면에서 그 칸 값 앞에 붙는 이름(2026-10-25 레터 재구성 마무리 — 종전에는 번호의 끝자리만 보아 6s 칸 밖의 번호
    (가동률 298 · 348)가 「유지 종료」 로 찍혔다). 매출 구분의 6s 칸(610 ~ 659 — `레터.가정이름` 의 6s 와 같은 범위) 가운데 정상 수준 · 유지 종료 ·
    정상 수준 도달은 짧은 말(구분은 손잡이 이름이 이미 말한다), 그 밖의 번호는 본편 가정 이름, 엔진 전용 대상(WACC.<구간> · 영구ROIC …)은 그 뜻의 이름."""
    s = "%s" % n
    if not s.isdigit():
        if s.startswith("WACC."):
            return "%s WACC" % s.split(".", 1)[1]
        try:
            import 레터이야기 as _N                           # noqa: PLC0415
            return _N._엔진손잡이말.get(s, s)
        except Exception:                                # noqa: BLE001
            return s
    k = int(s)
    if 610 <= k <= 659 and k % 10 in _6칸말:
        return _6칸말[k % 10]
    return _가정이름(가정, s)


class 손잡이틀:
    def __init__(self, d, 가정, 민, R0):
        self.d, self.가정, self.민 = d, 가정, 민
        self.h = 민.손잡이풀기(d["엔진손잡이"], 가정)
        self.대상 = ["%s" % x for x in self.h["대상"]]
        self.꼴 = d.get("꼴") or ("정수가산" if _연도칸인가(가정, self.대상) else "가산")
        if self.꼴 == "시나리오보간":                            # 2026-10-25 R3 — 열별 가정까지 비관 · 기준 · 낙관 사이를 선형으로(`레터이야기.시나리오보간`)
            import 레터이야기 as _N                               # noqa: PLC0415
            self._보간 = _N.시나리오보간
        self.이름 = d.get("이름") or self.h.get("이름")
        if self.꼴 == "시나리오축":
            self.벌 = {n: 가정["시점가정"][n] for n in self.대상}
        self.기준값 = 민.적용값(가정, self.h, "기준", R0) if self.꼴 == "값" else 0
        self.눈금 = sorted(set(d["눈금"] if d.get("눈금") else self.자동눈금(R0)) | {self.기준값})

    def 자동눈금(self, R0):
        if self.꼴 == "시나리오보간":
            return [-1.5, -1.0, -0.5, 0, 0.5, 1.0, 1.5]
        if self.꼴 == "시나리오축":
            return [-1.5, -1.0, -0.5, 0, 0.5, 1.0, 1.5, 2.0, 2.5]
        if self.꼴 == "정수가산":
            return [-2, -1, 0, 1, 2]
        if self.꼴 == "가산":
            범 = self.h.get("범위")
            if 범:
                lo, hi = 범
                if hi == 0 and lo < 0:
                    return [round(3 * lo * (1 - i / 6.0), 10) for i in range(7)]
                if lo == 0 and hi > 0:
                    return [round(3 * hi * i / 6.0, 10) for i in range(7)]
                w = hi - lo
                return [round(lo - w + 3 * w * i / 8.0, 10) for i in range(9)]
            폭 = self.h.get("폭") or 0.01
            if "영구ROIC" in self.대상 and R0 is not None:  # RONIC — 영구성장률 위에서(0 에 가까우면 재투자율이 터진다)
                b, g = R0["요약"]["영구ROIC"], R0["요약"]["영구성장률"]
                lo = max(g + 0.005, b - 0.06) - b
                return sorted({round(lo + (0 - lo) * i / 3.0, 10) for i in range(4)} | {round(0.025 * i, 10) for i in range(1, 6)})
            return [round(폭 * i, 10) for i in range(-4, 5)]
        g = R0["요약"]["영구성장률"]                   # 값(WACC) — 엔진이 막는 눈금 · 막히기 직전 · 그 사이 기하 셋 · 근거 범위 끝 · 기준 · 위쪽 하나
        b0 = self.기준값
        범 = self.근거범위()[0] or [b0 - 0.01, b0 + 0.01]
        lo = min(범[0], b0)
        r = ((lo - g) / 0.005) ** 0.25 if lo - g > 0.005 else 1.0
        return [g - 0.005, g + 0.005] + [g + 0.005 * r ** i for i in (1, 2, 3)] + [범[0], 범[1], b0 + 0.055]

    def 칸값(self, t):
        낸 = {}
        for n, 벌 in self.벌.items():
            b, lo, hi = 벌["기준"], 벌["비관"], 벌["낙관"]
            낸[n] = b + t * ((hi - b) if t >= 0 else (b - lo))
        return 낸

    def 옮기기(self, a, x):
        움 = self.민.움직이기
        if self.꼴 == "시나리오보간":
            return self._보간(self.가정, self.대상, x, 바탕=a)
        if self.꼴 == "시나리오축":
            for n, v in self.칸값(x).items():
                a = 움(a, {"이름": n, "대상": [n], "방식": "값"}, v)
            return a
        if self.꼴 == "값":
            return 움(a, dict(self.h, 방식="값"), x)
        return 움(a, dict(self.h, 방식="가산"), x)

    def 근거범위(self):
        d = self.d
        글 = d.get("근거출처")
        시들 = ("비관", "기준", "낙관")
        if self.꼴 == "시나리오보간":
            return [-1.0, 1.0], 글 or "비관 · 낙관 시나리오의 값(그 사이는 열마다 선형으로 옮긴 값 · −1 = 비관 · +1 = 낙관)"
        # 근거 글은 독자 말로(2026-10-25 레터 재구성 마무리 — 인터랙티브 판이 화면에 싣는다): 내부 번호(「가정 A-626」) · 내부어(「엔진 손잡이」) ·
        # 작업 메모(「색을 바꾸지 않는다」)를 쓰지 않는다. 가정의 이름은 화면의 손잡이 이름이 이미 말하므로 범위의 출처만 적는다.
        if self.꼴 == "시나리오축":
            배 = 지수눈금(self.가정)["배율"]
            끝 = (lambda v: "%d" % round(v * 배)) if 배 != 1 else (lambda v: "%.2f" % v)     # 화면의 눈금과 같은 꼴(「2025년 평균 = 100」 이면 × 100)
            쪽 = " · ".join(("%s %s ~ %s" % (구분이름(self.가정, n) or "", 끝(self.벌[n]["비관"]), 끝(self.벌[n]["낙관"]))).strip() for n in self.대상)
            return [-1.0, 1.0], 글 or "비관 · 낙관 시나리오의 값(%s)" % 쪽
        if self.꼴 == "정수가산":
            안 = [x for x in (self.d.get("눈금") or self.자동눈금(None))
                 if all(min(self.가정["시점가정"][n][s] for s in 시들) <= self.가정["시점가정"][n]["기준"] + x
                        <= max(self.가정["시점가정"][n][s] for s in 시들) for n in self.대상)]
            묶 = {}
            for n in self.대상:
                벌 = self.가정["시점가정"][n]
                묶.setdefault(칸말(n, self.가정), set()).add((min(벌[s] for s in 시들), max(벌[s] for s in 시들)))
            쪽 = " · ".join(("%s %s" % (말, " / ".join("%d ~ %d년" % ab for ab in sorted(v)))).strip() for 말, v in 묶.items())
            return ([min(안), max(안)] if 안 else None), 글 or "비관 · 낙관 시나리오의 값(%s)" % 쪽
        if (d.get("근거범위") or {}).get("값"):
            lo, hi = d["근거범위"]["값"]
            return [lo, hi], 글 or "%s(%s ~ %s)" % (d.get("범위글") or "근거 범위", 퍼(lo, 2), 퍼(hi, 2))
        vs = []
        for s in 시들:
            try:
                vs.append(self.민.적용값(self.가정, self.h, s))
            except Exception:                        # noqa: BLE001
                pass
        vs = [v for v in vs if _n(v) is not None]
        b = self.민.적용값(self.가정, self.h, "기준")
        if len(vs) == 3 and max(vs) - min(vs) > 1e-9 and self.꼴 == "가산" and _n(b) is not None:
            return [min(vs) - b, max(vs) - b], 글 or "비관 · 낙관 시나리오의 값(%s ~ %s)" % (퍼(min(vs), 1), 퍼(max(vs), 1))
        if self.h.get("범위"):
            lo, hi = self.h["범위"]
            return [lo, hi], 글 or (d.get("범위글") or "민감도 분석에서 정한 폭")      # 저자가 동인 표에 적은 범위 글 그대로(없으면 민감도 표의 폭)
        return None, 글 or "근거 범위를 정하지 않은 가정"

    def 표시(self, a):
        if self.꼴 == "시나리오보간":
            return {n: (self.민._시점값(a, n, "기준") if n in (a.get("시점가정") or {}) else None) for n in self.대상}
        if self.꼴 == "시나리오축":
            return {n: round(self.민._시점값(a, n, "기준"), 6) for n in self.대상}
        if self.꼴 == "정수가산":
            return {n: self.민._시점값(a, n, "기준") for n in self.대상}
        return {"값": self.민.적용값(a, self.h, "기준")}


def 지수눈금(가정):
    """정상 수준 지수의 읽는 눈금 — 가정의 `Narrative.독자.눈금`(예: 2025년 평균 = 100)이 있으면 × 100, 없으면 그대로."""
    눈 = ((가정.get("Narrative") or {}).get("독자") or {}).get("눈금") or {}
    if 눈.get("이름"):
        return {"배율": 100, "글": "%s = 100" % 눈["이름"]}
    return {"배율": 1, "글": ""}


# ────────────────────────────────────────────────── 만들기

def 만들기(가정경로, 시="기준", 칸수=11, 로그=print):
    계산, 가정오류, 민 = _엔진()
    가정 = json.load(io.open(가정경로, encoding="utf-8"))
    메타 = 가정["메타"]
    t0 = time.time()
    횟수 = [0]
    R0 = 계산(가정, 시)
    단위 = 단위정하기(메타, R0["2.DCF"]["58"])
    칸 = 연도축(R0)
    조정줄 = 조정줄이름()
    잎 = 잎구분(가정)

    def 돌리기(만들기_):
        횟수[0] += 1
        try:
            return 뽑기(계산(만들기_(), 시), 칸, 단위, 조정줄, 잎)
        except 가정오류 as e:
            return {"막힘": _엔진문장(e)}

    기준 = 뽑기(R0, 칸, 단위, 조정줄, 잎)
    종가 = 민.종가(가정)

    # 표1 · 표2 — 엔진의 격자(막힌 칸은 「해당 없음」)
    반 = (칸수 - 1) // 2
    성장가감 = [round(0.002 * (i - 반) * (5.0 / 반), 10) for i in range(칸수)]           # ±1.0%p
    W가감 = list(성장가감)
    이익가감 = [round(0.004 * (i - 반) * (5.0 / 반), 10) for i in range(칸수)]           # ±2.0%p
    hW, hg, hm = 민.손잡이풀기("WACC", 가정), 민.손잡이풀기("영구성장률", 가정), 민.손잡이풀기("영구이익률", 가정)
    t = time.time()
    표1 = 민._격자(가정, 시, (hg, 성장가감), (hW, W가감), R0)
    표2 = 민._격자(가정, 시, (hm, 이익가감), (hW, W가감), R0)
    횟수[0] += 2 * 칸수 * 칸수
    로그("표1 · 표2 %d × %d — %.1f초" % (칸수, 칸수, time.time() - t))

    def 표꼴(표, 세로말, 가로말):
        return {"세로이름": 세로말, "가로이름": 가로말, "세로값": 표["세로값"], "가로값": 표["가로값"], "기준칸": [반, 반],
                "값": [[(round(v, 4) if isinstance(v, (int, float)) else (v if v is not None else None)) for v in 줄] for 줄 in 표["값"]]}

    # 역산 곡선 — WACC 칸마다 종가가 성립하는 역산 축의 값
    역 = None
    if 종가:
        t = time.time()
        축 = 민.역산축(가정)
        점 = []
        for d_ in W가감:
            try:
                a = 민.움직이기(가정, dict(hW, 방식="가산"), d_, 시)
                w = 계산(a, 시)["요약"]["예측기간WACC"]
                r = 민.역산(a, 종가, 시, 축=축)
                점.append({"WACC": w, "값": r.get("값") if r.get("결과") is None else None,
                          "까닭": r.get("결과") or r.get("비고"), "가감": r.get("가감")})
            except 가정오류 as e:
                점.append({"WACC": None, "값": None, "까닭": _엔진문장(e)})
            횟수[0] += 1
        역 = {"축이름": 축.get("이름"), "대상": ["%s" % x for x in 축.get("대상") or []], "방식": 축.get("방식"), "종가": 종가, "점": 점,
             "기준값": 민.적용값(가정, 축, 시, R0)}
        로그("역산 곡선 %d점 — %.1f초" % (len(점), time.time() - t))

    # 드릴 — 현금성 · 이자부부채 세부(기준 시나리오 순평가)
    noa = R0["11.NOA"]
    k = 1.0 / 단위["나눔"]
    드릴 = {}
    for 묶, 줄들 in 드릴줄.items():
        목 = []
        for 번 in 줄들:
            v = _n((noa.get("%d" % 번) or {}).get("순평가"))
            if v:
                목.append({"이름": 줄이름("S11", 번) or "11번 %d" % 번, "값": round(v * k, 6), "줄": 번})
        드릴[묶] = 목

    # 손잡이 · 짝
    선언 = 동인손잡이(가정, 민)
    손 = {}
    for d in 선언:
        try:
            손[d["id"]] = 손잡이틀(d, 가정, 민, R0)
        except Exception as e:                       # noqa: BLE001 — 이 회사에 서지 않는 손잡이는 뺀다
            로그("손잡이 %s 를 세우지 못해 뺐다: %s" % (d.get("id"), e))
    지렛대 = None
    import 레터이야기 as _N                                       # noqa: PLC0415
    try:                                                     # 2026-10-25 R3 — 레터의 「값을 가르는 가정」 이 격자 손잡이에 있게
        지렛대 = _N.지렛대독립(가정, 가정경로)
    except Exception as e:                                   # noqa: BLE001
        로그("지렛대를 셈하지 못했다: %s" % e)
    if 지렛대:
        번 = {b for b in 지렛대.get("번호들") or [] if ("%s" % b).isdigit()}
        대 = ["%s" % x for x in 지렛대.get("대상") or []]
        덮 = any((번 and 번 <= set(kk.대상)) or (대 and all(x.startswith("WACC") for x in 대) and any(x.startswith("WACC") for x in kk.대상))
                for kk in 손.values())
        if not 덮:
            if 지렛대.get("잣대") == "시나리오":
                d = {"id": "지렛대", "이름": 지렛대.get("이름"), "꼴": "시나리오보간",
                     "엔진손잡이": {"이름": 지렛대.get("이름"), "대상": [b for b in 지렛대["번호들"] if _N._변동(가정, b)], "방식": "가산"}}
            elif 지렛대.get("표3") is not None:
                r = _N.표3손잡이(가정)[지렛대["표3"]]
                d = {"id": "지렛대", "이름": 지렛대.get("이름"), "꼴": "값" if 대 and all(x.startswith("WACC") for x in 대) else None,
                     "엔진손잡이": "WACC" if 대 and all(x.startswith("WACC") for x in 대) else
                     {"이름": 지렛대.get("이름"), "대상": list(r["대상"]), "방식": r.get("방식") or "가산", "폭": r.get("폭"), **({"범위": r["범위"]} if r.get("범위") else {})}}
            elif 지렛대.get("잣대") == "대안":              # 1.1.7 — 할인율 대안 사양 지렛대는 WACC 손잡이로
                d = {"id": "지렛대", "이름": 지렛대.get("이름"), "꼴": "값", "엔진손잡이": "WACC"}
            else:
                d = None
            if d:
                try:
                    손["지렛대"] = 손잡이틀(d, 가정, 민, R0)
                except Exception as e:                       # noqa: BLE001
                    로그("지렛대 손잡이를 세우지 못했다: %s" % e)
    구 = None
    try:
        구 = importlib.import_module("엔진.스키마").검증전부(가정)[2]
    except Exception:                                        # noqa: BLE001
        pass
    for kk in 손.values():                                   # 손잡이 이름은 본편 가정 표의 이름(화면에 「A-번호」 를 내지 않는다)
        try:
            if not kk.d.get("이름") or re.search(r"A-\d", "%s" % kk.이름) or any(("%s" % x).isdigit() for x in kk.대상):
                kk.이름 = _N.손잡이본편이름(구, kk.대상, kk.이름)
        except Exception:                                    # noqa: BLE001
            pass
    하나 = {}
    for kid, kk in 손.items():
        결과, 표시 = [], []
        for x in kk.눈금:
            결과.append(돌리기(lambda kk=kk, x=x: kk.옮기기(가정, x)))
            try:
                표시.append(kk.표시(kk.옮기기(가정, x)))
            except Exception:                        # noqa: BLE001
                표시.append({"값": x} if kk.꼴 == "값" else None)
        범위, 출처 = kk.근거범위()
        하나[kid] = {"이름": kk.이름, "꼴": kk.꼴, "눈금": kk.눈금, "기준": min(range(len(kk.눈금)), key=lambda i: abs(kk.눈금[i] - kk.기준값)),
                   "근거범위": 범위, "근거출처": 출처, "대상": kk.대상, "표시": 표시, "결과": 결과,
                   "대상이름": {n: (구분이름(가정, n) if kk.꼴 == "시나리오축" else 칸말(n, 가정)) for n in kk.대상}}

    def 무게(kid):
        v = 하나[kid]
        범 = v["근거범위"]
        쓸 = [r["주"] for x, r in zip(v["눈금"], v["결과"]) if "막힘" not in r and (
            (범 and 범[0] - 1e-12 <= x <= 범[1] + 1e-12) or (not 범 and abs(v["눈금"].index(x) - v["기준"]) <= 1))]
        return (max(쓸) - min(쓸)) if 쓸 else 0.0
    if any(d.get("_후보") for d in 선언):
        남길 = sorted([k for k in 손 if k != "지렛대"], key=무게, reverse=True)[:4] + (["지렛대"] if "지렛대" in 손 else [])
        for kid in [x for x in 손 if x not in 남길]:
            손.pop(kid)
            하나.pop(kid)
    순서 = sorted(손, key=무게, reverse=True)
    짝자료 = None
    if len(순서) >= 2:
        ks, kg = 손[순서[0]], 손[순서[1]]
        짝자료 = {"세로": 순서[0], "가로": 순서[1],
                "결과": [[돌리기(lambda xs=xs, xg=xg: kg.옮기기(ks.옮기기(가정, xs), xg)) for xg in kg.눈금] for xs in ks.눈금]}
    속 = R0["기간"]["속성"]
    결산월 = 가정["기간"].get("결산월", 12)
    예측 = [c for c, p in 속.items() if p["구분"] == "예측"]
    영구 = [c for c, p in 속.items() if p["구분"] == "영구기간"][0]
    이월 = (_n((R0.get("요약") or {}).get("이월연수")) or 0) > 0          # 2026-10-25 날짜 둘 — 이월 판이면 재무 자료 기준일도 싣는다(옛 판은 칸 없음)
    return {
        "형식": 형식, "만든날": datetime.date.today().isoformat(), "시나리오": 시,
        "회사": 메타.get("회사명"), "평가기준일": 메타.get("평가기준일"), "통화": 메타.get("표시통화"), "주당단위": 메타.get("주당단위") or "원",
        **({"재무기준일": (R0.get("요약") or {}).get("재무기준일") or 메타.get("재무기준일")} if 이월 else {}),
        "단위": 단위, "종가": 종가, "종가날짜": 메타.get("평가기준일"),
        "가정해시": 가정해시(가정), "엔진지문": 엔진지문(), "구조지문": R0["요약"].get("구조지문"),
        "칸": [{"이름": c["이름"], "실적": c["실적"], "추정": c["추정"]} for c in 칸],
        "모열": [열이름(속[c], 결산월) for c in 예측], "영구열": 열이름(속[영구], 결산월), "흐름수": 흐름수,
        "잎": [이 for _b, 이 in 잎], "조정줄": [말 for _k, 말 in 조정줄], "지수눈금": 지수눈금(가정),
        "기준": 기준, "표1": 표꼴(표1, "영구성장률", "WACC"), "표2": 표꼴(표2, "영구기간 영업이익률", "WACC"), "역산곡선": 역, "드릴": 드릴,
        "손잡이": {kid: 하나[kid] for kid in 순서}, "짝": 짝자료,
        "엔진실행": 횟수[0] + 1, "걸린초": round(time.time() - t0, 1), "신호": [],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="인터랙티브 레터의 격자를 엔진으로 미리 낸다(JS 재계산 없음)")
    ap.add_argument("가정")
    ap.add_argument("--낼")
    ap.add_argument("--칸", type=int, default=11, help="표1 · 표2 의 한 변 칸 수(홀수 · 기본 11)")
    ap.add_argument("--시나리오", default="기준")
    a = ap.parse_args(argv)
    if not os.path.exists(a.가정) or a.칸 < 3 or a.칸 % 2 == 0:
        print("입력 오류 — 가정 파일이 없거나 --칸 이 3 이상 홀수가 아니다")
        return 입력오류
    try:
        d = 만들기(a.가정, a.시나리오, a.칸)
    except Exception as e:                           # noqa: BLE001
        print("입력 오류 — 엔진이 이 가정을 계산하지 못했다: %s" % _엔진문장(e))
        return 입력오류
    p = a.낼 or os.path.join(os.path.dirname(os.path.abspath(a.가정)), "_raw", "민감도격자.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
    print("민감도격자 — 손잡이 %s · 짝 %s · 표1 · 표2 %d×%d · 역산 %s · 엔진 %d회 · %.1f초 · %s(%d바이트)" % (
        " / ".join("%s(%s %d)" % (v["이름"], v["꼴"], len(v["눈금"])) for v in d["손잡이"].values()),
        "%s × %s" % (d["짝"]["세로"], d["짝"]["가로"]) if d["짝"] else "없음", a.칸, a.칸,
        "%d점" % len(d["역산곡선"]["점"]) if d["역산곡선"] else "없음(종가 없음)", d["엔진실행"], d["걸린초"], p, os.path.getsize(p)))
    return 통과


if __name__ == "__main__":
    sys.exit(main())

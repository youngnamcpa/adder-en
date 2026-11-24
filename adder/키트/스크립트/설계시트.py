# -*- coding: utf-8 -*-
"""설계시트 — 워크북 「17. 동인 지도와 근거」 의 내용 (W4 · 2026-10-23 · 연구/레터워크북_최적화_20261023/05_최적설계.md 3절 W4).

붓기(`_설계붓기`)가 부른다. 레터 3 · 5절이 글로 쓰는 모델 설계(무엇이 무엇을 미는가 · 원가의 성격 · 근거 범위)를 워크북에도 셀로 남긴다.
  내용(가정, 가정경로) → {"줄": [{열 ID: 값}], "서식": [{열 ID: 서식 이름}], "노드수": n 또는 None, "재료글": 글, "못실음": n}

줄은 동인 지도(`_raw/동인지도.json`)의 노드마다, 노드의 판단 칸(`판단칸`)마다 한 줄이다(판단 칸이 없는 노드는 한 줄).
  노드 · 연동(선택) · 성격 · 산식(엔진 자리) · 근거 강도 · 근거 · 상위 노드          ← 동인 지도
  가정 번호 · 단위 · 적용 값 · 근거 범위 하 · 상 · 범위 출처                         ← 판단 칸(거친 바퀴가 쓰는 범위)
  같은 집단 자리 · 지속성 · 연동 계수와 수축 w · 민감도                             ← 변수 카드(`_raw/변수카드.json`)
  결합 몫                                                                            ← 결합 민감도(`_raw/결합민감도.json` 분해.주효과)
재료 파일이 없으면 그 열을 비우고 재료 글에 「없음(도구 이름)」 을 적는다. 값을 정하지 않는다 — 옮겨 적을 뿐이다.

성격(변동비 · 준고정비 · 인건비 · 이익 연동 비용 · 고정비 · 조정 — 2026-10-27, 옛 계단비 · 준고정비(인건비) · 이익 연동비)은 레터 5절과 같은 판정이다 — `레터본문._산식성격` · `_수준연동` 을 읽고,
읽지 못하면(레터 모듈이 없는 배포) 같은 표의 사본을 쓴다. 회사 · 업종 이름은 이 도구에 없다.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)

최대줄 = 80                          # 17번 노드 줄 수(생성기 납품시트/S17.jsonl 의 S17R101 ~ S17R180)
분류말 = {"변동": "변동비", "계단": "준고정비", "준고정": "인건비", "이익": "이익 연동 비용", "고정": "고정비", "조정": "조정"}     # 2026-10-27 — 비용 성격 구분(계단식 고정비 = 준고정비 · 인원 × 급여 = 인건비). 열쇠(계단 · 준고정 …)는 그대로
# 레터본문._산식성격 · _수준연동 의 사본(레터 모듈을 못 읽을 때만 쓴다 — 둘이 갈리면 레터 쪽이 정본)
_산식성격사본 = {"매출액비율": ("변동", "매출에 비례"), "물량단위원가": ("변동", "판매량에 비례"),
           "설비계수": ("계단", "설비 취득원가에 비례"), "물가연동": ("고정", "물가에 연동")}
_수준연동사본 = {"소비자물가": "물가에 연동", "임금": "임금에 연동", "인력": "임금 × 인원에 연동", "자체": "자체 단위원가 변동률에 연동"}
# 판단 칸의 척도 → 붓기의 숫자 서식 이름(생성기 서식표의 것)
척도서식 = {"비율": "비율2", "증가율": "비율2", "율": "비율2", "비중": "비율2", "변동률": "비율2", "일수": "일수", "배수": "배수",
        "금액": "금액", "연수": "연수", "연도": "연도"}


def _읽기(p):
    try:
        with io.open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _n(x):
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def _성격표():
    try:
        import importlib                                     # noqa: PLC0415
        본 = importlib.import_module("레터본문")
        return ({k: v[:2] for k, v in 본._산식성격.items()}, {k: v[0] for k, v in 본._수준연동.items()})
    except Exception:                                        # noqa: BLE001 — 레터 모듈이 없거나 고치는 중이면 사본
        return _산식성격사본, _수준연동사본


def _원가성격(x, 산식표, 수준표):
    """구조.원가줄 한 줄 → (성격 글, 연동 글) — 레터본문.원가조각 과 같은 판정(주 산식 · 보조 산식)."""
    산 = x.get("산식")
    주 = 산식표.get(산, ("고정", "기준 금액"))
    if 산 == "물가연동":
        주 = (주[0], 수준표.get(x.get("수준지수") or "소비자물가", 주[1]))
    elif 산 == "매출액비율" and x.get("연동기준") == "판매량":
        주 = ("변동", "판매량에 비례")
    보 = x.get("보조산식") or "없음"
    if 보 != "없음":
        보성 = 산식표.get(보, ("고정", "기준 금액"))
        if 보 == "물가연동":
            보성 = (보성[0], 수준표.get(x.get("수준지수") or "소비자물가", 보성[1]))
        return "%s · %s" % (분류말[주[0]], 분류말[보성[0]]), "주 산식 %s · 보조 산식 %s" % (주[1], 보성[1])
    return 분류말[주[0]], 주[1]


def 노드성격(노드, 구조, 산식표=None, 수준표=None):
    """동인 지도 노드 → 성격 글(원가 노드만 · 그 밖은 「—」)."""
    if 산식표 is None:
        산식표, 수준표 = _성격표()
    이 = ("%s" % (노드.get("노드") or "")).strip()
    원가줄 = {int(x.get("번호")): x for x in (구조.get("원가줄") or []) if isinstance(x, dict) and str(x.get("번호", "")).isdigit()}
    m = re.match(r"^원가줄(\d+)$", 이)
    if m and int(m.group(1)) in 원가줄:
        return _원가성격(원가줄[int(m.group(1))], 산식표, 수준표)[0]
    if 이 == "연구개발" and 5 in 원가줄:
        return _원가성격(원가줄[5], 산식표, 수준표)[0]
    if 이 == "감가상각":
        return 분류말["계단"]
    if 이 == "인건비":
        인 = 구조.get("인건비") or {}
        방 = 인.get("산정방식")
        if 방 == "인원":
            글 = 분류말["준고정"]
        elif 방 == "매출액비율":
            글 = 분류말["변동"]
        else:
            return "—"
        return 글 + (" · %s(성과급)" % 분류말["이익"] if (인.get("성과급") or "없음") != "없음" else "")
    if 이.startswith("재고") and (구조.get("원가") or {}).get("재고변동반영") == "예":
        return 분류말["조정"]
    return "—"


def _w(딱지):
    m = re.search(r"w\s*([0-9.]+)", 딱지 or "")
    return m.group(1) if m else None


def _계수글(카드):
    for 제 in 카드.get("사전제안") or ():
        v, 범 = _n(제.get("값")), 제.get("근거범위") or []
        if v is None:
            continue
        w = 제.get("w") if 제.get("w") is not None else _w(제.get("딱지"))
        글 = "%s %.4g" % (제.get("출처") or "사전", v)
        if len(범) == 2 and all(_n(x) is not None for x in 범):
            글 += " [%.4g ~ %.4g]" % (범[0], 범[1])
        if w is not None:
            글 += " · w %s" % w
        return 글
    return ""


def _띠글(카드):
    """같은 처지 상장사의 80% 띠(변수 카드 「같은집단띠」 — 2026-10-24 PM) 한 줄. 칸 단위가 아니면 「정의가 다름 — 변수」."""
    띠 = 카드.get("같은집단띠")
    if isinstance(띠, dict) and 띠.get("없음"):
        return "80%% 구간 없음(%s)" % " · ".join(띠["없음"])
    if not isinstance(띠, dict) or not isinstance(띠.get("범위"), list) or len(띠["범위"]) != 2:
        return ""
    if not 띠.get("칸단위"):
        return "80%% 구간 — 정의가 다름(%s)" % (띠.get("변수") or "")
    lo, hi = 띠["범위"]
    return "80%% 구간 %.4g ~ %.4g(%s년 뒤 · %s · %s%s)" % (lo, hi, 띠.get("k") or 1, "비슷한 자리" if 띠.get("종류") == "지속성" else "같은 집단 전체",
                                                    띠.get("변수") or "", " · 백테스트 보정" if 띠.get("보정") else " · 보정 없음")


def _노드띠글(n, 카드):
    """판단 칸이 없는 노드 — 엔진 자리(산식)에 적힌 가정 번호(「A-80 · A-711~718」 · 「A-501 · 503 · 504」 꼴)의 80% 띠를 모은다(2026-10-24 PM).
    띠가 있는 카드의 번호만 싣는다(산식의 다른 숫자는 걸러진다)."""
    s = "%s" % (n.get("엔진자리") or "")
    i = s.find("A-")
    if i < 0:
        return ""
    번들 = []
    for a, b in re.findall(r"(\d+)(?:\s*~\s*(\d+))?", s[i:]):
        lo, hi = int(a), int(b) if b else int(a)
        if 0 <= hi - lo <= 50:
            for x in range(lo, hi + 1):
                if "%s" % x not in 번들:
                    번들.append("%s" % x)
    글 = [("A-%03d " % int(x)) + _띠글(카드[x]) for x in 번들 if x in 카드 and _띠글(카드[x])]
    return " / ".join(글)


def _집단글(카드):
    """같은 집단 자리 — 꼬리 판정이 있는 집단을 먼저, 없으면 가장 좁은 산업 집단 하나(첫 · 끝 열의 백분위). 끝에 같은 처지 80% 띠(있으면)."""
    띠글 = _띠글(카드)
    글0 = _집단글_자리(카드)
    return " / ".join(x for x in (글0, 띠글) if x)


def _집단글_자리(카드):
    자리 = [x for x in (카드.get("같은집단자리") or ()) if isinstance(x, dict) and _n(x.get("백분위")) is not None]
    if not 자리:
        return ""
    집단들 = []
    for x in 자리:
        if x["집단"] not in 집단들:
            집단들.append(x["집단"])
    꼬리 = [g for g in 집단들 if any(x["집단"] == g and x.get("판정") for x in 자리)]
    산업 = [g for g in 집단들 if g != "전체" and not g.startswith("같은 규모")]
    고른 = 꼬리[:1] or 산업[-1:] or 집단들[:1]
    글 = []
    for g in 고른:
        조 = ["%s %.0f%%%s" % (x["열"].split("(")[0], x["백분위"] * 100, ("(%s)" % x["판정"]) if x.get("판정") else "")
             for x in 자리 if x["집단"] == g]
        글.append("%s %s" % (g, " · ".join(조)))
    return " / ".join(글)


def _결합몫(결):
    """결합 민감도 → {가정 번호: 몫}(손잡이의 대상 번호로 주효과 몫을 잇는다)."""
    if not isinstance(결, dict):
        return {}
    이름몫 = {x.get("이름"): _n(x.get("몫")) for x in ((결.get("분해") or {}).get("주효과") or ()) if isinstance(x, dict)}
    낸 = {}
    for h in 결.get("손잡이") or ():
        몫 = 이름몫.get(h.get("이름"))
        if 몫 is None:
            continue
        for t in h.get("대상") or ():
            낸["%s" % t] = 낸.get("%s" % t, 0.0) + 몫
    return 낸


def 재료(가정경로):
    d = os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw")
    return {"동인지도": _읽기(os.path.join(d, "동인지도.json")), "변수카드": _읽기(os.path.join(d, "변수카드.json")),
            "결합민감도": _읽기(os.path.join(d, "결합민감도.json"))}


def 내용(가정, 가정경로):
    구조 = 가정.get("구조") if isinstance(가정.get("구조"), dict) else {}
    재 = 재료(가정경로)
    지도, 카드판, 결 = 재["동인지도"], 재["변수카드"], 재["결합민감도"]
    도구 = {"동인지도": "동인지도짓기.py", "변수카드": "변수카드.py", "결합민감도": "결합민감도.py"}
    재료글 = []
    for k, v in 재.items():
        if v is None:
            재료글.append("%s 없음(%s)" % (k, 도구[k]))
        elif k == "동인지도":
            재료글.append("동인지도 노드 %d" % len(v.get("노드") or []))
        elif k == "변수카드":
            재료글.append("변수카드 %d장(%s)" % (len(v.get("카드") or []), v.get("만든날") or "날짜 없음"))
        else:
            재료글.append("결합민감도 %s판(%s)" % (v.get("판") or "?", v.get("만든날") or "날짜 없음"))
    카드 = {("%s" % c.get("번호")): c for c in ((카드판 or {}).get("카드") or ()) if isinstance(c, dict) and c.get("번호") is not None}
    몫 = _결합몫(결)
    산식표, 수준표 = _성격표()
    줄, 서식 = [], []
    for n in ((지도 or {}).get("노드") or ()):
        if not isinstance(n, dict):
            continue
        머 = {"노드": " · ".join(x for x in ("%s" % (n.get("노드") or ""), "%s" % (n.get("이름") or "")) if x.strip()),
             "연동": n.get("선택") or "", "성격": 노드성격(n, 구조, 산식표, 수준표), "산식": n.get("엔진자리") or "",
             "강도": n.get("근거강도") or "", "근거": n.get("근거") or "",
             "상위": " · ".join("%s" % x for x in (n.get("상위노드") or ()))}
        if not 머["연동"] and n.get("해당없음까닭"):
            머["연동"] = "해당 없음 — %s" % n["해당없음까닭"]
        칸들 = [x for x in (n.get("판단칸") or ()) if isinstance(x, dict)] or [None]
        for 칸 in 칸들:
            한 = dict(머)
            서 = {}
            if 칸 is not None:
                번 = "%s" % 칸.get("번호")
                c = 카드.get(번) or {}
                한["가정"] = ("A-%03d" % int(번)) if 번.isdigit() else 번          # 12번 번호 열과 같은 꼴(A-080)
                한["척도"] = 칸.get("척도") or c.get("단위") or ""
                fs = 척도서식.get(한["척도"], "계수")
                v = _n(칸.get("값"))
                if v is None:
                    값 = c.get("값") or {}
                    v = _n(값.get("끝예측")) if isinstance(값, dict) else _n(값)
                범 = 칸.get("범위") or []
                for k, x in (("적용", v), ("하", 범[0] if len(범) == 2 else None), ("상", 범[1] if len(범) == 2 else None)):
                    if _n(x) is not None:
                        한[k] = _n(x)
                        서[k] = fs
                출 = [x for x in (칸.get("범위출처"), 칸.get("까닭")) if x]
                한["출처"] = " — ".join(출)
                한["집단"] = _집단글(c)
                한["지속"] = ((c.get("지속성형태") or {}).get("형태") or "") if isinstance(c.get("지속성형태"), dict) else ""
                한["계수"] = _계수글(c)
                if _n(c.get("민감도")) is not None:
                    한["민감"], 서["민감"] = _n(c.get("민감도")), "비율"
                if 번 in 몫:
                    한["몫"], 서["몫"] = 몫[번], "비율"
            else:
                띠글 = _노드띠글(n, 카드)
                if 띠글:
                    한["집단"] = 띠글
            줄.append(한)
            서식.append(서)
    if not 줄 and 카드:                                     # 동인 지도가 없으면 변수 카드의 가정 칸(주당가치에 닿는 것 · 민감도 순)으로 대신 — 노드 수 검증은 그대로 걸린다
        재료글.append("동인 지도 대신 변수 카드의 가정 칸")
        고른 = sorted((c for c in 카드.values() if c.get("종류") == "가정" and c.get("주당가치에닿나")),
                    key=lambda c: -(_n(c.get("민감도")) or 0.0))
        for c in 고른:
            번 = "%s" % c.get("번호")
            값 = c.get("값") or {}
            근 = c.get("근거") if isinstance(c.get("근거"), dict) else {}
            한 = {"노드": c.get("이름") or "", "연동": c.get("첫엣지") or "", "상위": c.get("상류") or "",
                 "가정": ("A-%03d" % int(번)) if 번.isdigit() else 번, "척도": c.get("단위") or "", "강도": c.get("근거강도") or "",
                 "근거": " · ".join(x for x in (근.get("출처"), 근.get("산정근거")) if x), "출처": c.get("폭출처") or "",
                 "집단": _집단글(c), "계수": _계수글(c),
                 "지속": ((c.get("지속성형태") or {}).get("형태") or "") if isinstance(c.get("지속성형태"), dict) else ""}
            서 = {}
            v = _n(값.get("끝예측")) if isinstance(값, dict) else _n(값)
            if v is not None:
                한["적용"], 서["적용"] = v, 척도서식.get(한["척도"], "계수")
            if _n(c.get("민감도")) is not None:
                한["민감"], 서["민감"] = _n(c.get("민감도")), "비율"
            if 번 in 몫:
                한["몫"], 서["몫"] = 몫[번], "비율"
            줄.append(한)
            서식.append(서)
    못 = max(0, len(줄) - 최대줄)
    if 못:
        재료글.append("줄 %d개 가운데 %d개를 싣지 못했다(시트 줄 %d)" % (len(줄), 못, 최대줄))
    return {"줄": 줄[:최대줄], "서식": 서식[:최대줄], "노드수": len((지도 or {}).get("노드") or []) if 지도 else None,
            "재료글": " · ".join(재료글), "못실음": 못}


def 결합요약(가정경로, 종가=None):
    """14번 결합 민감도 구획의 내용 — 결합민감도.json 이 없으면 None."""
    결 = 재료(가정경로)["결합민감도"]
    if not isinstance(결, dict) or not 결.get("분포"):
        return None
    분해 = 결.get("분해") or {}
    방식 = {h.get("이름"): h.get("방식") for h in 결.get("손잡이") or ()}
    주 = sorted([x for x in 분해.get("주효과") or () if isinstance(x, dict) and _n(x.get("몫")) is not None], key=lambda x: -x["몫"])[:6]

    def 범위글(x):
        범 = x.get("범위") or []
        if len(범) != 2 or not all(_n(v) is not None for v in 범):
            return ""
        하, 상 = 범
        if 방식.get(x.get("이름")) == "배율":
            return "×(1 %+.1f%%) ~ ×(1 %+.1f%%)" % (하 * 100, 상 * 100)
        if 방식.get(x.get("이름")) == "값":
            return "%.4g ~ %.4g" % (하, 상)
        if max(abs(하), abs(상)) <= 1:
            return "%+.2f%%p ~ %+.2f%%p" % (하 * 100, 상 * 100)
        return "%+.4g ~ %+.4g" % (하, 상)
    쌍 = sorted([x for x in 분해.get("쌍") or () if isinstance(x, dict) and _n(x.get("주효과대비")) is not None],
               key=lambda x: -x["주효과대비"])[:3]
    분 = 결["분포"]
    표 = [v for v in (결.get("표본주당") or ()) if _n(v) is not None]
    종가자리 = (sum(1 for v in 표 if v <= 종가) / len(표)) if (표 and _n(종가) is not None) else None
    기준 = _n(결.get("기준주당"))
    return {"주효과": [{"이름": x.get("이름"), "범위": 범위글(x), "몫": x["몫"], "계수": _n(x.get("표준화계수")), "출처": x.get("출처") or ""}
                     for x in 주],
            "쌍": [{"이름": " × ".join("%s" % s for s in (x.get("쌍") or ())), "대비": x["주효과대비"]} for x in 쌍],
            "분위": [_n(분.get(k)) for k in ("P5", "P25", "P50", "P75", "P95")],
            "설명": "%s판(실패 %s) · 주효과 R² %.1f%% · 상호작용 · 비선형 몫 %.1f%%" % (
                결.get("판"), 결.get("실패", 0), (_n(분해.get("주효과R2")) or 0) * 100, (_n(분해.get("상호작용비선형몫")) or 0) * 100),
            "자리": "기준 주당가치 %s — 판 가운데 %.0f%% 자리%s" % (
                "{:,.2f}".format(기준) if 기준 is not None else "?", (_n(분.get("기준위치")) or 0) * 100,
                (" · 종가 %s — %.0f%% 자리" % ("{:,.2f}".format(종가), 종가자리 * 100)) if 종가자리 is not None else " · 종가 없음"),
            "몫": _결합몫(결)}

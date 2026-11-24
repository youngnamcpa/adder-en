# -*- coding: utf-8 -*-
"""변수카드 — 가정 칸마다 **카드 한 장**(정의 · 단위 · 값 · 상류 · 하류 · 근거 · 근거 강도 · 민감도 · 정보가치 · 지속성 · 같은 집단 자리 · 사전 제안 · 출처 달린 한 줄)을
가정 곁 `_raw/` 의 산출물에서 모아 낸다 (2026-10-23 · 연구/동인연동_업그레이드_연구.md P6). 레터 독자근거 · 워크북 설명 셀의 **공통 원천**이다.

    python 스크립트/변수카드.py 가정.json                 # → _raw/변수카드.json · _raw/변수카드.md · 표를 찍는다
    python 스크립트/변수카드.py 가정.json --번호 273,616  # 그 칸만 찍는다

읽는 것(있는 것만 — 없으면 그 칸은 비고 「재료 없음」) — 가정 `근거`(출처 딱지 · 기준일 · 근거 · 비고) · `_raw/동인그래프.json`(P1 — 이름 · 단위 · 값 · 첫 엣지 · 다음 · 홉 · 갈림 · 전파) ·
  `_raw/동인지도.json`(노드 근거강도 · 판단칸) · `_raw/거친바퀴.json`(민감도 · 문항 · 폭출처) · `_raw/정보가치.json`(정보가치 · 조사순위 · 좁힐 갈래) · `_raw/지속성.json`(형태) ·
  `_raw/기저율.json`(비율 자리 — 같은 집단 백분위) · `_raw/계수사전.json` · `_raw/수축.json`(제안 — 적용값 · 범위 · w) · `_raw/원형판정.json`(1순위 원형 · KPI 자리) ·
  `_raw/직원수_10K.json`(미국 — 대상 회사 한 곳의 인원 증가율 실적 범위 → 501 `회사실적` · 같은 집단 띠가 아니다 · 2026-10-24 PN).
한 줄(sourced sentence) — 「<이름> <값>(<출처 딱지> · <기준일>) → <첫 엣지> → … → 주당가치 · 민감도 ±x%」. 값 · 출처 · 날짜가 한 몸이다(출처가 비면 「출처 없음」을 그대로 찍는다 —
  무디스 「decision-grade」 의 추적 가능 조건). 신호 — 갈렸거나 민감도 상위인데 근거 칸에 출처 딱지가 없다(참고) · 재료가 하나도 없다(참고). 값을 바꾸지 않는다.
레터 v27(2026-11-10) — 싣기 표지: 지속성 `반감싣기가능`(false 면 `반감햇수` None · 숫자는 `반감햇수_참고`) · 계수사전 · 기저율의 `싣기가능: false` 제안 ·
  자리는 `사전제안_뺌` · `같은집단자리_뺌` 으로 옮긴다 · 결합 손잡이가 「시나리오」 방식이면 결합범위를 위치(−1 ~ 1)가 아니라 비관 · 낙관 값으로 ·
  머리 `업종적합`(기저율 · 지속성의 업종 적합 판정).
종료 코드 — 0 · 2 입력 오류. 회사 · 업종 이름이 코드에 없다.
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass
여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 입력오류                  # noqa: E402

출처이름 = "변수카드"
형식 = "변수카드 1"
딱지들 = ("[공시]", "[계산]", "[관측]", "[판단]", "[법령]", "[동종]", "[제약]", "[추정]")


def _읽기(raw, 이름):
    p = os.path.join(raw, 이름)
    if not os.path.exists(p):
        return None
    try:
        j = json.load(io.open(p, encoding="utf-8"))
        return j if isinstance(j, dict) else None
    except (OSError, ValueError):
        return None


def _n(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _번호들(글):
    return {m for m in re.findall(r"A-([0-9]+)", "%s" % 글)} | {m for m in re.findall(r"판단칸\s*([0-9]+)", "%s" % 글)}


def _수글(v):
    if v is None:
        return "—"
    if isinstance(v, (int, float)):
        return "{:,.0f}".format(v) if abs(v) >= 1000 else ("%.4g" % v)
    return "%s" % v


def 모으기(가정, raw):
    그래프 = _읽기(raw, "동인그래프.json") or {}
    지도 = _읽기(raw, "동인지도.json") or {}
    바퀴 = _읽기(raw, "거친바퀴.json") or {}
    정보 = _읽기(raw, "정보가치.json") or {}
    지속 = _읽기(raw, "지속성.json") or {}
    기저 = _읽기(raw, "기저율.json") or {}
    계수 = _읽기(raw, "계수사전.json") or {}
    수축 = _읽기(raw, "수축.json") or {}
    원형 = _읽기(raw, "원형판정.json") or {}
    결합 = _읽기(raw, "결합민감도.json") or {}
    직원 = _읽기(raw, "직원수_10K.json") or {}
    재료 = {"직원수10K": bool(직원), "결합민감도": bool(결합), "동인그래프": bool(그래프), "동인지도": bool(지도), "거친바퀴": bool(바퀴), "정보가치": bool(정보), "지속성": bool(지속), "기저율": bool(기저),
          "계수사전": bool(계수), "수축": bool(수축), "원형판정": bool(원형)}
    카드 = {}

    def 칸(번):
        번 = "%s" % 번
        if 번 not in 카드:
            카드[번] = {"번호": 번, "이름": None, "단위": None, "종류": None, "값": None, "갈림": None, "상류": None, "첫엣지": None, "다음": [], "홉": None,
                      "주당가치에닿나": None, "근거": None, "출처딱지": None, "기준일": None, "근거강도": None, "판단칸": None, "민감도": None, "문항": None, "폭출처": None,
                      "정보가치": None, "조사순위": None, "좁힐갈래": None, "지속성형태": None, "같은집단자리": [], "사전제안": [], "원형KPI": None, "한줄": None, "비고": [],
                      "결합범위": None, "같은집단띠": None, "회사실적": None}
        return 카드[번]
    # ① 그래프 — 가정 · 거시 노드와 설명 체인
    for n in 그래프.get("노드") or []:
        if n.get("종류") in ("가정", "거시"):
            c = 칸(n["번호"])
            c.update({"이름": n.get("이름"), "단위": n.get("단위"), "종류": n.get("종류"), "값": n.get("값"), "갈림": n.get("갈림")})
            if n.get("민감도") is not None:
                c["민감도"] = n["민감도"]
    for ch in 그래프.get("설명체인") or []:
        c = 칸(ch["노드"][2:])
        c.update({"첫엣지": ch.get("첫엣지"), "다음": ch.get("다음") or [], "홉": ch.get("홉"), "주당가치에닿나": ch.get("주당가치에닿나")})
        if not ch.get("읽힘"):
            c["비고"].append("이 구조가 안 읽는 칸")
    # ② 근거 4칸
    for 번, 근 in (가정.get("근거") or {}).items():
        if not isinstance(근, list) or not 번.isdigit():
            continue
        c = 칸(번)
        c["근거"] = {"출처": 근[0] if len(근) > 0 else None, "기준일": 근[1] if len(근) > 1 else None, "산정근거": 근[2] if len(근) > 2 else None, "비고": 근[3] if len(근) > 3 else None}
        글 = "%s" % (근[0] if 근 else "")
        c["출처딱지"] = next((d for d in 딱지들 if 글.startswith(d)), ("미사용" if 글.startswith("미사용") else None))
        c["기준일"] = 근[1] if len(근) > 1 else None
    # ③ 동인 지도 — 노드 근거강도 · 판단칸
    for 노 in 지도.get("노드") or []:
        for k in 노.get("판단칸") or []:
            번 = "%s" % (k.get("번호") or "")
            if 번.isdigit():
                c = 칸(번)
                c["판단칸"] = {"노드": 노.get("노드"), "범위": k.get("범위"), "척도": k.get("척도"), "근거강도": k.get("근거강도") or 노.get("근거강도"), "문항": k.get("문항")}
                c["근거강도"] = c["근거강도"] or k.get("근거강도") or 노.get("근거강도")
    # ④ 거친 바퀴 — 표 · 범위없음
    for r in (바퀴.get("표") or []) + (바퀴.get("범위없음") or []):
        if not isinstance(r, dict):
            continue
        대상 = r.get("대상") or (r.get("손잡이") or {}).get("대상") or []
        번들 = {("%s" % d).replace("A-", "") for d in (대상 if isinstance(대상, list) else [대상]) if ("%s" % d).replace("A-", "").isdigit()}
        번들 |= _번호들(json.dumps(대상, ensure_ascii=False)) | ({"%s" % r["번호"]} if r.get("번호") else set())
        for 번 in 번들:
            c = 칸(번)
            if r.get("민감도") is not None:
                c["민감도"] = r["민감도"]
            if r.get("문항") is not None:
                c["문항"] = bool(r["문항"])
            if r.get("폭출처"):
                c["폭출처"] = r["폭출처"]
    # ⑤ 정보가치
    for k in 정보.get("칸") or []:
        번 = "%s" % (k.get("번호") or "")
        if 번.isdigit():
            c = 칸(번)
            c.update({"정보가치": k.get("정보가치"), "조사순위": k.get("조사순위"), "좁힐갈래": k.get("좁힐_갈래")})
            if c["민감도"] is None and k.get("최대변화") is not None:
                c["민감도"] = k["최대변화"]
    # ⑥ 지속성 — 형태 + 같은 집단 80% 띠(2026-10-24 PM — 칸 단위 · 보정 뒤가 있으면 그것 · 1년 뒤(영구 칸은 5년 뒤) · 지속성 띠가 먼저)
    변수표 = {("%s" % (v.get("이름") or "")): v for v in (지속.get("변수") or []) if isinstance(v, dict)}
    for k in 지속.get("칸") or []:
        번 = "%s" % (k.get("번호") or "")
        if 번.isdigit():
            칸(번)["지속성형태"] = {"변수": k.get("변수"), "형태": k.get("형태"), "판정": k.get("판정"), **지속성숫자(변수표.get("%s" % (k.get("변수") or "")))}
            띠 = 같은집단띠(k)
            if 띠:
                칸(번)["같은집단띠"] = 띠
            elif k.get("띠없음"):
                칸(번)["같은집단띠"] = {"없음": list(k["띠없음"])}         # 대응 변수는 있는데 띠가 안 섰다 — 까닭(레터 · 17번 시트가 이름으로 적는다)
    # ⑦ 기저율 비율 자리 — 레터 v27 F5: `싣기가능: false`(업종 부적합 집단) 자리는 싣지 않고 `같은집단자리_뺌` 에 까닭과 남긴다
    for x in 기저.get("비율자리") or []:
        번 = "%s" % (x.get("번호") or "")
        if 번.isdigit():
            for a in x.get("자리") or []:
                한 = {"집단": a.get("집단"), "열": a.get("열"), "백분위": a.get("백분위"), "판정": a.get("판정")}
                if a.get("싣기가능") is False:
                    칸(번).setdefault("같은집단자리_뺌", []).append(dict(한, 까닭=a.get("안싣는까닭")))
                    continue
                칸(번)["같은집단자리"].append(한)
    # ⑧ 사전 제안 — 계수사전 · 수축. 레터 v27 P11 · F5: `싣기가능: false`(물리 범위 밖 · 산업 표본 30곳 미만 · 업종 부적합) 제안은 `사전제안_뺌` 으로
    for 출, d in (("계수사전", 계수), ("수축", 수축)):
        for x in d.get("제안") or []:
            for 번 in _번호들(x.get("자리")):
                한 = {"출처": 출, "값": x.get("값"), "근거범위": x.get("근거범위"), "딱지": x.get("딱지"), "w": ((계수.get("수축") or {}).get(_계수이름(x), {}) or {}).get("w") if 출 == "계수사전" else None}
                if x.get("싣기가능") is False:
                    칸(번).setdefault("사전제안_뺌", []).append(dict(한, 까닭=x.get("안싣는까닭")))
                    continue
                칸(번)["사전제안"].append(한)
    # ⑩ 결합 민감도 손잡이의 근거 범위 — 판단 칸이 없는 칸(영구성장률 · 영구기간 ROIC 따위)의 범위 재료(2026-10-24 W10 · 회차 20261024)
    #   「값」 방식은 범위 그대로, 「가산」 방식은 그 칸의 지금 값(그래프 노드 값)에 더한 범위. 지금 값을 모르면 싣지 않는다
    for h in 결합.get("손잡이") or []:
        if not isinstance(h, dict) or _n(h.get("하")) is None or _n(h.get("상")) is None:
            continue
        for d in h.get("대상") or []:
            번 = {"영구ROIC": "219", "영구성장률": "212"}.get("%s" % d, ("%s" % d).replace("A-", ""))
            if not 번.isdigit():
                continue
            c = 칸(번)
            방 = h.get("방식") or "가산"
            if 방 == "시나리오":                            # 레터 v27 — 시나리오 손잡이의 하 · 상은 위치(−1 ~ 1)다. 값에 더하지 않고 비관 · 낙관 값으로 되돌린다
                r = 시나리오범위(가정, 번)
                if r:
                    c["결합범위"] = {"범위": [r[0], r[1]], "출처": h.get("출처"), "방식": 방, "열": r[2],
                                   "뜻": "비관 · 낙관 시나리오 값(손잡이 위치 −1 ~ 1 을 값으로 되돌림 · 열별 가정은 시나리오가 처음 갈리는 열)"}
                continue
            if 방 == "값":
                lo, hi = sorted((_n(h["하"]), _n(h["상"])))
            else:
                v = c.get("값")
                기 = _n((v or {}).get("값") if isinstance(v, dict) and "값" in v else (v or {}).get("기준") if isinstance(v, dict) else v)
                if 기 is None:
                    continue
                if 방 == "배율":
                    lo, hi = sorted((기 * (1 + _n(h["하"])), 기 * (1 + _n(h["상"]))))
                else:
                    lo, hi = sorted((기 + _n(h["하"]), 기 + _n(h["상"])))
            c["결합범위"] = {"범위": [lo, hi], "출처": h.get("출처"), "방식": 방}
    # ⑪ 회사 실적 범위 — 미국 10-K 직원 수(sec_상세변수 직원수 · 2026-10-24 PN). 인원 증가율(501)의 대상 회사 한 곳 실적 — 같은 집단 띠와 따로 싣는다
    if isinstance(직원.get("실적범위"), list) and len(직원["실적범위"]) == 2 and all(_n(x) is not None for x in 직원["실적범위"]):
        증 = [x for x in 직원.get("증가율") or [] if _n(x.get("값")) is not None]
        칸("501")["회사실적"] = {"범위": [min(직원["실적범위"]), max(직원["실적범위"])], "해": [x.get("기간끝") for x in 증],
                              "원천": "연차 보고서 직원 수(%s · %d해)" % (직원.get("종목") or 직원.get("cik") or "", len(증)), "뜻": 직원.get("뜻")}
    # ⑨ 원형 KPI 자리 — 1순위 원형
    후보 = (원형.get("후보") or [None])[0]
    if 후보:
        for 번, c in 카드.items():
            if c.get("종류") == "가정" and 번 in {h["번호"] for h in (후보.get("채울칸") or [])}:
                c["원형KPI"] = 후보["원형"]
    # 한 줄
    for c in 카드.values():
        c["한줄"] = 한줄(c)
    return 카드, 재료


노출기본 = {"반감_최소쌍": 1000, "반감_범위": [0.5, 15.0]}          # 지속성.노출기본 과 같은 값(옛 지속성.json — `노출` 이 없을 때만 여기서 판정)
_형태문턱 = {"수렴형_r1_미만": 0.5, "지속형_r1_이상": 0.7}


def _집단종류(g):
    """지속성 집단 → 종류(운영 동종 산업 · 같은 산업 2자리 · 같은 규모 · 전체). 새 산출은 `집단종류` 를 싣고, 옛 산출은 이름으로 가른다."""
    종 = g.get("집단종류")
    if 종:
        return 종
    이 = "%s" % (g.get("집단") or "")
    return "전체" if 이 == "전체" else ("같은 규모" if 이.startswith("같은 규모") else ("운영 동종 산업" if 이.startswith("운영 동종") else "같은 산업 2자리"))


def _집단말(g, 종=None):
    이 = "%s" % (g.get("집단") or "")
    종 = 종 or _집단종류(g)
    if 종 == "전체":
        return "상장사 전체"
    if 종 == "같은 규모":
        return "%s 상장사" % 이
    if 종 == "운영 동종 산업":
        m = re.search(r"\(([^)]*)\)", 이)
        return "사업이 비슷한 회사들의 업종(%s) 상장사" % (m.group(1) if m else 이)
    return "같은 업종(%s) 상장사" % 이


def _옛노출(v):
    """옛 지속성.json(변수에 `노출` 이 없다) — 같은 규칙을 기본 문턱으로 여기서 판정한다(지속성.노출판정 과 같은 차례 · 같은 조건)."""
    형 = v.get("형태")
    if 형 in (None, "표본 부족"):
        return {"싣기가능": False, "까닭": "변수의 형태가 서지 않았다(%s)" % (형 or "없음")}
    하, 상 = 노출기본["반감_범위"]
    후보 = []
    for 종 in ("운영 동종 산업", "같은 산업 2자리", "같은 규모", "전체"):
        for g in v.get("집단") or []:
            if isinstance(g, dict) and _집단종류(g) == 종 and g.get("싣기가능") is not False and \
                    ((g.get("쌍수") or {}).get("1") or 0) >= 노출기본["반감_최소쌍"] and _n(g.get("반감햇수")) is not None:
                후보.append((종, g))
    if not 후보:
        return {"싣기가능": False, "까닭": "1년 쌍 %s개 이상이고 반감기가 선 집단이 없다" % "{:,}".format(노출기본["반감_최소쌍"])}
    종, g = 후보[0]
    r1 = _n((g.get("순위상관") or {}).get("1"))
    집형 = g.get("형태") or (None if r1 is None else ("수렴형" if r1 < _형태문턱["수렴형_r1_미만"] else ("지속형" if r1 >= _형태문턱["지속형_r1_이상"] else "느린수렴형")))
    반 = _n(g.get("반감햇수"))
    까닭 = []
    if not (하 <= 반 <= 상):
        까닭.append("반감기 %.2f년이 %.1f~%.0f년 밖이다(추정이 흔들림)" % (반, 하, 상))
    if 집형 != 형:
        까닭.append("그 집단(%s)의 1년 순위상관으로 매긴 형태(%s)가 형태 말(%s — 전체 집단)과 다르다" % (g.get("집단"), 집형 or "없음", 형))
    return {"싣기가능": not 까닭, "까닭": " · ".join(까닭), "집단": g.get("집단"), "집단종류": 종, "반감햇수": 반, "AR1": _n(g.get("AR1"))}


def 시나리오범위(가정, 번):
    """가정 번호의 비관 · 기준 · 낙관 값 범위 → (아래, 위, 열) 또는 None. 한 값(시점가정)은 세 값의 최소 · 최대(열 「시점」),
    열별 가정은 세 시나리오가 처음 갈리는 열의 세 값(레터 시나리오 표와 같은 자리). 세 값이 모두 같으면 None."""
    시들 = ("비관", "기준", "낙관")
    s = (가정.get("시점가정") or {}).get("%s" % 번)
    if isinstance(s, dict) and all(_n(s.get(시)) is not None for 시 in 시들):
        값 = [_n(s[시]) for 시 in 시들]
        return (min(값), max(값), "시점") if max(값) > min(값) else None
    g = (가정.get("가정") or {}).get("%s" % 번)
    if not isinstance(g, dict) or not all(isinstance(g.get(시), dict) for 시 in 시들):
        return None
    for 열 in g["기준"]:
        값 = [_n(g[시].get(열)) for 시 in 시들]
        if any(v is None for v in 값):
            continue
        if max(값) - min(값) > 1e-12:
            return min(값), max(값), 열
    return None


def 지속성숫자(v):
    """지속성 패널 변수 하나 → {반감햇수 · AR1 · 집단 · 반감싣기가능 · (반감안싣는까닭 · 반감햇수_참고 · 집단_참고)}
    (2026-10-25 레터 재구성 R7 — 근거 표 「움직임」 열의 숫자 · 2026-11-10 레터 v27 F3).
    지속성 산출의 `노출`(없으면 같은 규칙을 여기서) — 집단 차례 운영 동종 산업 → 같은 산업(업종 적합일 때만) → 같은 규모 → 전체 가운데 1년 쌍 1,000 이상인
    첫 집단의 반감기가 0.5~15년 안이고 그 집단의 형태가 형태 말과 같을 때만 숫자를 싣는다(`반감햇수`). 아니면 `반감햇수` 는 None(레터는 형태 말만)이고
    숫자는 `반감햇수_참고` 에 남긴다. 변수가 없으면 빈 dict."""
    if not isinstance(v, dict):
        return {}
    노 = v.get("노출") if isinstance(v.get("노출"), dict) else _옛노출(v)
    g = next((x for x in v.get("집단") or [] if isinstance(x, dict) and x.get("집단") == 노.get("집단")), None)
    말 = _집단말(g, 노.get("집단종류")) if g else None
    if 노.get("싣기가능"):
        return {"반감햇수": _n(노.get("반감햇수")), "AR1": _n(노.get("AR1")), "집단": 말, "반감싣기가능": True}
    return {"반감햇수": None, "AR1": None, "집단": None, "반감싣기가능": False, "반감안싣는까닭": 노.get("까닭") or "노출 조건을 넘지 못했다",
            "반감햇수_참고": _n(노.get("반감햇수")), "집단_참고": 말}


def _띠포함():
    """80% 띠의 포함 목표(사후대조설정 층1 띠 위 − 아래) — 레터가 「80% 띠」 의 80% 를 장부 숫자로 싣는다. 못 읽으면 None."""
    try:
        import 사후대조 as 사                              # noqa: PLC0415
        띠 = 사.설정읽기()["층1"]["띠"]
        return round(float(띠["위"]) - float(띠["아래"]), 6)
    except Exception:                                    # noqa: BLE001
        return None


def 같은집단띠(k):
    """지속성 칸 하나의 `띠[]` → 카드에 싣는 띠 하나 — {범위 [하, 상](칸 단위) · 변수 · 종류(지속성 · 기저율) · k · 칸단위 · 딱지 · 보정 · 띠집단 · n · 환산글}.
    차례: 가장 짧은 앞날의 지속성 띠(회사의 지금 자리를 본다) → 기저율 띠. 양 끝은 보정 뒤가 있으면 그것(사후대조 보정표)."""
    for t in sorted(k.get("띠") or [], key=lambda t: t.get("k") or 99):
        for 종류 in ("지속성", "기저율"):
            v = t.get(종류) or {}
            r = v.get("보정뒤") or v.get("보정전")
            if isinstance(r, list) and len(r) == 2 and all(_n(x) is not None for x in r):
                보 = v.get("보정") or {}
                return {"범위": [min(r), max(r)], "변수": t.get("변수"), "종류": 종류, "k": t.get("k"), "칸단위": bool(t.get("칸단위")),
                        "딱지": t.get("딱지"), "보정": bool(v.get("보정뒤")), "q": 보.get("보정계수"), "띠집단": v.get("띠집단"), "n": v.get("n"),
                        "환산글": t.get("환산글"), "포함": _띠포함()}
    return None


def _계수이름(x):
    m = re.search(r"\((S2C_incr|잔존연수|β1_SGA|b_COGS)", "%s" % x.get("글"))
    return m.group(1) if m else ""


def 한줄(c):
    값 = c.get("값") or {}
    if "값" in 값:
        값글 = _수글(값["값"])
    elif 값:
        값글 = "%s → %s" % (_수글(값.get("첫예측")), _수글(값.get("끝예측")))
    else:
        값글 = "값 없음"
    출처 = (c.get("출처딱지") or "출처 없음")
    날 = c.get("기준일") or "날짜 없음"
    길 = (" → [%s] %s → … → 주당가치(%s홉)" % (c["첫엣지"], " · ".join(c["다음"][:2]), c.get("홉"))) if c.get("첫엣지") and c.get("주당가치에닿나") else \
        ((" → [%s](주당가치에 안 닿음)" % c["첫엣지"]) if c.get("첫엣지") else " → (어느 엣지도 읽지 않음)")
    민 = (" · 민감도 ±%.1f%%" % (abs(c["민감도"]) * 100)) if isinstance(c.get("민감도"), (int, float)) else ""
    강 = (" · %s" % c["근거강도"]) if c.get("근거강도") else ""
    return "%s(A-%s) %s(%s · %s%s)%s%s" % (c.get("이름") or "A-%s" % c["번호"], c["번호"], 값글, 출처, 날, 강, 길, 민)


def 분석(가정, 가정경로):
    raw = os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw")
    카드, 재료 = 모으기(가정, raw)
    신호 = []
    for 번, c in 카드.items():
        if c.get("종류") not in ("가정", "거시"):
            continue
        무거움 = c.get("갈림") or (isinstance(c.get("민감도"), (int, float)) and abs(c["민감도"]) >= 0.05)
        if 무거움 and not c.get("출처딱지") and c.get("주당가치에닿나"):
            신호.append({"출처": 출처이름, "종류": "근거 없는 축", "대상": "A-%s" % 번, "값": c.get("민감도"), "문턱": "출처 딱지",
                       "글": "%s(A-%s) — 시나리오별로 갈렸거나 민감도 ±5%% 넘는 칸인데 근거 칸에 출처 딱지가 없다(값 · 출처 · 날짜가 한 몸이어야 한다)" % (c.get("이름") or "", 번), "등급": "참고"})
    if not any(재료.values()):
        신호.append({"출처": 출처이름, "종류": "재료 없음", "대상": "_raw", "값": None, "문턱": None, "글": "가정 곁 _raw 에 동인그래프 · 거친바퀴 · 정보가치 … 가 없다 — 근거 4칸만으로 카드를 냈다", "등급": "참고"})
    순 = sorted(카드.values(), key=lambda c: (-(abs(c["민감도"]) if isinstance(c.get("민감도"), (int, float)) else -1), int(c["번호"])))
    낸 = {"형식": 형식, "만든날": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "가정": os.path.basename(가정경로), "재료": 재료,
         "요약": {"카드": len(카드), "출처딱지있음": sum(1 for c in 카드.values() if c.get("출처딱지") and c["출처딱지"] != "미사용"), "갈린칸": sum(1 for c in 카드.values() if c.get("갈림")),
                "민감도있음": sum(1 for c in 카드.values() if isinstance(c.get("민감도"), (int, float)))},
         "카드": 순, "신호": 신호}
    # 레터 v27 F5 — 업종 적합 판정(기저율 · 지속성이 같은 함수로 낸다)을 머리에 옮긴다. 적합이 false 면 레터가 「업종 분류가 사업과 엇갈려 같은 규모 상장사로 쟀다」 각주를 단다
    업 = (_읽기(raw, "기저율.json") or {}).get("업종적합") or (_읽기(raw, "지속성.json") or {}).get("업종적합")
    낸["업종적합"] = {k: 업.get(k) for k in ("적합", "몫", "같은체계", "일치", "문턱", "운영동종산업", "까닭")} if isinstance(업, dict) else None
    return 낸


def 마크다운(낸, 번호들=None):
    L = ["# 변수 카드 — %s (%s)" % (낸["가정"], 낸["만든날"]), "",
         "재료: " + " · ".join("%s %s" % (k, "○" if v else "×") for k, v in 낸["재료"].items()), ""]
    for c in 낸["카드"]:
        if 번호들 and c["번호"] not in 번호들:
            continue
        L.append("## A-%s %s" % (c["번호"], c.get("이름") or ""))
        L.append("- " + c["한줄"])
        if c.get("근거"):
            L.append("- 근거: %s / %s / %s" % (c["근거"].get("출처") or "—", c["근거"].get("산정근거") or "—", c["근거"].get("비고") or "—"))
        if c.get("판단칸"):
            L.append("- 판단 칸: 노드 %s · 범위 %s · 척도 %s · 강도 %s" % (c["판단칸"].get("노드"), c["판단칸"].get("범위"), c["판단칸"].get("척도"), c["판단칸"].get("근거강도")))
        if c.get("정보가치") is not None:
            L.append("- 정보가치 %.4g · 조사 순위 %s · 좁힐 갈래 %s" % (c["정보가치"], c.get("조사순위"), c.get("좁힐갈래")))
        if c.get("지속성형태"):
            L.append("- 지속성: %s %s" % (c["지속성형태"].get("변수"), c["지속성형태"].get("형태")))
        if c.get("회사실적"):
            L.append("- 회사 실적 범위(%s): %s ~ %s" % (c["회사실적"]["원천"], _수글(c["회사실적"]["범위"][0]), _수글(c["회사실적"]["범위"][1])))
        for a in c.get("같은집단자리") or []:
            L.append("- 같은 집단 %s %s 백분위 %s(%s)" % (a.get("집단"), a.get("열"), a.get("백분위"), a.get("판정")))
        for s in c.get("사전제안") or []:
            L.append("- 사전 제안(%s): %s 범위 %s%s %s" % (s["출처"], _수글(s.get("값")), s.get("근거범위"), (" · w %.2f" % s["w"]) if s.get("w") is not None else "", s.get("딱지") or ""))
        if c.get("원형KPI"):
            L.append("- 원형 「%s」 가 채우는 칸" % c["원형KPI"])
        for b in c.get("비고") or []:
            L.append("- 비고: %s" % b)
        L.append("")
    if 낸["신호"]:
        L.append("## 신호")
        L += ["- [%s] %s — %s" % (s["등급"], s["종류"], s["글"]) for s in 낸["신호"]]
    return "\n".join(L) + "\n"


def 쓰기(낸, 가정경로):
    raw = os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw")
    os.makedirs(raw, exist_ok=True)
    p = os.path.join(raw, "변수카드.json")
    with io.open(p, "w", encoding="utf-8") as f:
        json.dump(낸, f, ensure_ascii=False, indent=1, default=str)
    with io.open(os.path.join(raw, "변수카드.md"), "w", encoding="utf-8") as f:
        f.write(마크다운(낸))
    return p


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description=__doc__.split("\n")[0])
    ap.add_argument("가정")
    ap.add_argument("--번호")
    a = ap.parse_args()
    if not os.path.exists(a.가정):
        print("가정 파일이 없다: %s" % a.가정)
        return 입력오류
    try:
        가정 = json.load(io.open(a.가정, encoding="utf-8"))
    except ValueError as e:
        print("가정 JSON 파손 — %s" % e)
        return 입력오류
    낸 = 분석(가정, a.가정)
    print("→ %s" % 쓰기(낸, a.가정))
    번호들 = {x.strip() for x in a.번호.split(",")} if a.번호 else None
    요 = 낸["요약"]
    print("변수카드 — 카드 %d · 출처 딱지 있음 %d · 갈린 칸 %d · 민감도 있음 %d · 재료 %s" % (요["카드"], 요["출처딱지있음"], 요["갈린칸"], 요["민감도있음"],
                                                                     " · ".join(k for k, v in 낸["재료"].items() if v) or "없음"))
    for c in 낸["카드"]:
        if 번호들 and c["번호"] not in 번호들:
            continue
        print("  " + c["한줄"])
    for s in 낸["신호"]:
        print("  [%s] %s — %s" % (s["등급"], s["종류"], s["글"]))
    return 통과


if __name__ == "__main__":
    sys.exit(main())

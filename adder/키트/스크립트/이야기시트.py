# -*- coding: utf-8 -*-
"""이야기시트 — 워크북 「16. Narrative와 숫자」 의 내용 (L2 · 기획/레터_고도화_제안 5절 M11 — 다모다란 Stories to Numbers 시트의 우리판).

붓기(`_이야기붓기`)가 부른다. 값은 엔진의 적용 시나리오 결과, 글은 가정 파일(Narrative · 서사 · 메타.생애주기 · 서사연결 · 서술.이름 · 3P).
  내용(가정) → {"글": {줄: 글}, "머리": {줄: [W1 … W5]}, "값": {줄: [W1 … W4]}, "연결": {줄: 글}, "서식": {줄: 서식}}
  줄 11~16 Narrative 글(W5 — 줄바꿈 글 열) · 21 칸 머리 · 22~27 가정 여섯 줄(평가기준일 전 실적 · 첫 예측 기간 · 최종 예측 연도 · 영구기간) + Link to story ·
  31~33 세 시나리오의 이름 · 주당가치 · 3P test 판정
저자 글의 장부 키 「{키|꼴}」 는 엔진 값으로 편다(레터와 같은 꼴).
"""
from __future__ import annotations

import importlib
import os
import re
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)

시나리오들 = ("비관", "기준", "낙관")
_절줄 = {22: ("매출",), 23: ("비용", "영구"), 24: ("재투자",), 25: ("세금",), 26: ("할인율",), 27: ("영구",)}
_줄번호 = {22: ("4.Sales", "56"), 23: None, 24: None, 25: None, 26: ("2.DCF", "33"), 27: None}


def _n(x):
    try:
        if x is None or isinstance(x, bool):
            return None
        return float(x)
    except (TypeError, ValueError):
        return None


def _칸(R, 시트, 줄, 열):
    v = (R.get(시트) or {}).get(줄)
    return _n(v.get(열)) if isinstance(v, dict) else None


def _투하(R, 열):
    투 = [_칸(R, "9.WC", "14", 열), _칸(R, "8.CapEx", "21", 열), _칸(R, "8.CapEx", "28", 열)]
    return sum(투) if all(x is not None for x in 투) and sum(투) > 0 else None


def _값(R, 줄, 열, 영구):
    """가정 여섯 줄의 한 칸."""
    P = R["기간"]
    년 = _n((P["속성"].get(열) or {}).get("년")) or 1.0
    매, 익 = _칸(R, "2.DCF", "11", 열), _칸(R, "2.DCF", "15", 열)
    if 줄 == 22:
        return _n(R["요약"]["영구성장률"]) if 영구 else _칸(R, "4.Sales", "56", 열)
    if 줄 == 23:
        if 영구:
            return _n(R["요약"]["영구기간영업이익률"])
        return (익 / 매) if 매 and 익 is not None else None
    if 줄 == 24:
        if 영구:
            return None
        연매 = _칸(R, "4.Sales", "55", 열) or ((매 / 년) if 매 is not None else None)
        투 = _투하(R, 열)
        return (연매 / 투) if 연매 is not None and 투 else None
    if 줄 == 25:
        if 영구:
            return _n((R["2.DCF"] or {}).get("44"))
        세 = _칸(R, "2.DCF", "18", 열)
        return (세 / 익) if 세 is not None and 익 else None
    if 줄 == 26:
        return _n(R["요약"]["영구기간WACC"]) if 영구 else _칸(R, "2.DCF", "33", 열)
    if 줄 == 27:
        if 영구:
            return _n(R["요약"]["영구ROIC"])
        nop = _칸(R, "2.DCF", "19", 열)
        투 = _투하(R, 열)
        return (nop / 년 / 투) if nop is not None and 투 else None
    return None


def _펴기(원, 글, 메타):
    import 레터이야기                                       # noqa: PLC0415
    return 레터이야기.키풀어글(원, 글, 메타) if isinstance(글, str) and "{" in 글 else (글 or "")


def 내용(가정):
    계산 = importlib.import_module("엔진.계산")
    import 레터이야기                                       # noqa: PLC0415
    적용 = (가정.get("스위치") or {}).get("적용시나리오") or "기준"
    R = {s: 계산.계산(가정, s) for s in 시나리오들}
    원 = {"가정": 가정, "R": R, "민": None, "_대안": {}, "가성": None, "지난": None}
    메타 = 가정.get("메타") or {}
    Ra = R[적용]
    P = Ra["기간"]
    자리 = P["자리"]
    열 = [자리.get("FY실적.끝"), (P["묶음"].get("예측") or [None])[0], 자리.get("예측.끝"), 자리.get("영구")]
    N = 가정.get("Narrative") if isinstance(가정.get("Narrative"), dict) else {}
    서사 = 가정.get("서사")
    서사들 = [v for _k, v in sorted(서사.items())] if isinstance(서사, dict) else ([x for x in re.split(r"\n\s*\n", 서사) if x.strip()]
                                                                         if isinstance(서사, str) else [])

    def 글(k, 대신=None):
        v = _펴기(원, N.get(k), 메타)
        return v.strip() if v and v.strip() else (대신 or "")
    생 = 메타.get("생애주기") if isinstance(메타.get("생애주기"), dict) else {}
    생글 = ""
    if 생.get("단계"):
        생글 = "%s%s%s" % (생["단계"], (" · " + " · ".join(생.get("덧표지") or [])) if 생.get("덧표지") else "",
                         (" · " + 생["위치"]) if 생.get("위치") else "")
    낸 = {"글": {11: " ".join(x for x in (글("한줄"), 글("값으로")) if x) or (서사들[2] if len(서사들) > 2 else ""),
               12: " ".join(x for x in (글("정체성"), 글("구성")) if x) or (서사들[0] if 서사들 else ""),
               13: 글("우위", 서사들[1] if len(서사들) > 1 else ""), 14: 글("그러나"), 15: 생글, 16: 글("가격")},
          "머리": {21: ["실적 %s" % (P["속성"].get(열[0], {}).get("표기") or 열[0] or "—"),        # 칸 폭(16) 안 — 서식 점검
                      "첫 예측 %s" % (P["속성"].get(열[1], {}).get("표기") or 열[1] or "—"),
                      "최종 %s" % (P["속성"].get(열[2], {}).get("표기") or 열[2] or "—"),
                      "영구기간", "Link to story"],
                 31: [s for s in 시나리오들]},
          "값": {}, "연결": {}, "서식": {}}
    for 줄 in range(22, 28):
        낸["값"][줄] = [(_값(Ra, 줄, c, i == 3) if c else None) for i, c in enumerate(열)]
    연결 = 가정.get("서사연결") if isinstance(가정.get("서사연결"), dict) else {}
    for 줄, 절들 in _절줄.items():
        for k, v in 연결.items():
            문 = v if isinstance(v, str) else (v or {}).get("문장")
            절 = 레터이야기.절가정("%s" % k)
            if 줄 == 23 and "%s" % k not in ("213",) and 절 != "비용":
                continue
            if 줄 == 27 and "%s" % k != "219":
                continue
            if 절 in 절들 and isinstance(문, str) and 문.strip():
                낸["연결"][줄] = _펴기(원, 문.strip(), 메타)
                break
    이름 = ((가정.get("서술") or {}).get("이름") or {}) if isinstance(가정.get("서술"), dict) else {}
    낸["머리"][31] = [s for s in 시나리오들]                       # 시나리오 이름(서술.이름)은 레터 12절에 — 칸 폭 안
    낸["값"][32] = [_n(R[s]["요약"]["주당가치"]) for s in 시나리오들] + [None]
    P3 = ((가정.get("3P") or {}).get("시나리오") or {}) if isinstance(가정.get("3P"), dict) else {}
    낸["글"][33] = None
    낸["판정"] = [((P3.get(s) or {}).get("판정") or "") for s in 시나리오들]
    return 낸

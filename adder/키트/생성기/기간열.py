# -*- coding: utf-8 -*-
"""기간열 — 가정 파일의 `기간` 과 평가기준일에서 시간축 열을 짓는다 (W2-나).

줄 무늬 명세의 시간축 시트(2 · 4~10 · 12 · 13번)는 열 등록부에 시간축 열의 **틀**을 적어 둔다 —
열마다 「종류」(실적 · 예측 · 영구) 말고도 「갈래」(FY실적 · 누계실적 · 잔여예측 · 연간예측 · 영구)와 「구간」(상세 · 수렴)이 있다.
틀은 지금의 15열 구성(회계연도 실적 2 · 누계 실적 1 · 잔여 기간 1 · 연간 예측 10(상세 5 + 수렴 5) · 영구기간 1)이고
열 ID 는 H1~H3 · E1~E11 · TV 다. 명세의 무늬와 수식은 이 열 ID 를 못 박아 부르지 않는다(묶음 · 자리 이름 · @. · @<-1> · @TV 만).

  틀 읽기(기간을 안 줌)   열 ID 는 틀 그대로. 열의 기간 속성(표기 · 종료일 …)은 책.json 의 「기본기간」에서 자리대로 받는다.
                          범위 지문 · 다시쓰기 · 이름입히기가 이 꼴로 읽는다(명세를 고치는 도구는 틀을 본다).
  축 읽기(기간을 줌)      틀의 시간축 열을 그 회차의 열로 바꾼다. 열 ID = 기간 ID(FY2025A · 1H26A · 2H26E · FY2027E · TV).
                          실적 열 수 · 누계/잔여 열의 유무 · 예측 열 수(상세 · 수렴)가 회차마다 다르다. 워크북은 이 꼴로 짓는다.

열을 짓는 표는 엔진의 `기간축.py`(키트 스크립트) 하나다 — 이 모듈은 그것을 불러 `축.사전()` 을 받는다.
받는 것(`축사전(무엇)`): 가정 사전 · 가정 파일 경로 · {"평가기준일", "결산월", "실적연도수", "상세추정연수", "수렴연수"[, "재무기준일"]} · `기간축` 객체 · `축.사전()` 이 낸 사전.
열은 재무기준일(없으면 평가기준일)로 선다 — 2026-10-25 날짜 둘. 재무기준일 ≠ 평가기준일인 축은 조건식에 `기간.이월` 이 참이다(구조펴기).

쓰기:  python 기간열.py <가정.json | 기간 json>        그 축의 열을 찍는다
"""
import os
import sys
import json
import importlib.util
from collections import OrderedDict
from copy import deepcopy

from 공통 import 손오류, 축갈래

여기 = os.path.dirname(os.path.abspath(__file__))
구분종류 = {"실적": "실적", "예측": "예측", "영구기간": "영구"}      # 기간축의 구분 → 열 등록부의 「종류」
갈래들 = ("FY실적", "누계실적", "잔여예측", "연간예측", "영구")
구간들 = ("상세", "수렴")
축값속성 = ("표기", "ID", "구분", "종료일", "시작일", "개월", "년", "구간", "회계연도", "기말", "기중", "시작", "FY시작")
날짜속성 = ("종료일", "시작일")
기간키 = ("평가기준일", "결산월", "실적연도수", "상세추정연수", "수렴연수", "표기", "재무기준일")
_모듈 = []


def 축모듈():
    """엔진의 기간축.py — 이 폴더 · ../키트/스크립트 · 환경 변수 「기간축곳」 차례로 찾는다."""
    if _모듈:
        return _모듈[0]
    후보 = [os.environ.get("기간축곳"), os.path.join(여기, "기간축.py"),
          os.path.normpath(os.path.join(여기, "..", "키트", "스크립트", "기간축.py")),
          os.path.normpath(os.path.join(여기, "..", "스크립트", "기간축.py"))]
    for 곳 in 후보:
        if 곳 and os.path.exists(곳):
            spec = importlib.util.spec_from_file_location("기간축", 곳)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            _모듈.append(m)
            return m
    raise 손오류("기간축.py 를 찾지 못했다 — 키트의 스크립트/기간축.py 가 있어야 한다(환경 변수 「기간축곳」 으로 줄 수 있다)", 종류="기간")


def 축사전(무엇):
    """→ `기간축.사전()` 꼴의 사전(열 · 속성 · 묶음 · 자리 …). 틀리면 배치오류(종류 「기간」)."""
    if isinstance(무엇, str):
        try:
            with open(무엇, encoding="utf-8") as f:
                무엇 = json.load(f)
        except (OSError, ValueError) as e:
            raise 손오류("기간을 읽을 파일을 읽지 못했다: %s — %s" % (무엇, e), 종류="기간")
    if hasattr(무엇, "사전") and hasattr(무엇, "ID"):
        return 무엇.사전()
    if not isinstance(무엇, dict):
        raise 손오류("기간은 가정 사전 · 가정 파일 경로 · {평가기준일, 결산월, 실적연도수, 상세추정연수, 수렴연수} 로 준다", 종류="기간")
    if isinstance(무엇.get("열"), list) and isinstance(무엇.get("속성"), dict):
        return 무엇
    m = 축모듈()
    try:
        if isinstance(무엇.get("기간"), dict):
            return m.기간축(무엇).사전()
        모름 = [k for k in 무엇 if k not in 기간키]
        if 모름:
            raise 손오류("기간의 모르는 열쇠: %s (쓸 수 있는 열쇠: %s)" % (" · ".join(모름), " · ".join(기간키)), 종류="기간")
        return m.기간축.만들기(무엇.get("평가기준일"), **{k: 무엇[k] for k in 기간키[1:] if k in 무엇}).사전()      # 재무기준일 — 키워드로 넘긴다
    except m.기간축오류 as e:
        raise 손오류("기간에서 열을 짓지 못했다 — %s" % e, 종류="기간")


def 열속성(축, ID):
    """그 열의 등록부 속성 — 종류 · 갈래 · 구간 · 달아님 · 기간(속성 사전)."""
    기 = dict(축["속성"][ID])
    개월 = 기.get("개월")
    return {"종류": 구분종류[기["구분"]], "갈래": 기["종류"], "구간": 기.get("구간"),
            "달아님": 개월 is not None and float(개월) != int(개월), "기간": 기}


def 틀열들(머리):
    """시트 머리의 열 등록부에서 시간축 틀 열(「갈래」가 있는 열)의 자리 목록."""
    return [i for i, c in enumerate(머리.get("열") or ()) if c.get("갈래")]


def 틀인가(머리):
    return bool(틀열들(머리))


def 입히기(머리, 축, 바꿈):
    """시트 머리(날것)의 열 등록부를 축에 맞춘 새 머리를 돌려준다(받은 머리는 고치지 않는다).

    바꿈=False(틀 읽기) : 열 ID 는 틀 그대로. 축(기본기간)이 틀과 같은 꼴이면 열마다 기간 속성을 자리대로 싣는다. 축이 없으면(None) 속성 없이.
    바꿈=True (축 읽기) : 틀의 시간축 열을 축의 열로 바꾼다 — 틀에 있는 종류(실적 · 예측 · 영구)의 열만(13번은 실적 열만).
    머리의 자리 이름(쓰임 · 덧이름 · 틀 고정의 「시간.1」 따위)은 줄무늬.읽기가 푼다.
    """
    새 = deepcopy(머리)
    열 = 새["열"]
    자리 = 틀열들(새)
    if not 자리:
        return 새
    if 자리 != list(range(자리[0], 자리[-1] + 1)):
        raise 손오류("%s 의 시간축 틀 열이 한데 붙어 있지 않다" % 머리.get("시트"), 종류="기간")
    틀 = [열[i] for i in 자리]
    for c in 틀:
        if c.get("갈래") not in 갈래들 or (c.get("구간") is not None and c["구간"] not in 구간들):
            raise 손오류("%s 의 열 %s — 갈래 「%s」 · 구간 「%s」 를 모른다 (갈래: %s · 구간: %s)" % (
                머리.get("시트"), c.get("id"), c.get("갈래"), c.get("구간"), " · ".join(갈래들), " · ".join(구간들)), 종류="기간")
    있는종류 = {c.get("종류") for c in 틀}
    if 축 is None:
        return 새
    축열 = [ID for ID in 축["열"] if 열속성(축, ID)["종류"] in 있는종류]
    if not 바꿈:
        꼴 = [(열속성(축, ID)["갈래"], 열속성(축, ID)["구간"]) for ID in 축열]
        if 꼴 != [(c["갈래"], c.get("구간")) for c in 틀]:
            raise 손오류("%s — 책.json 의 「기본기간」으로 지은 열(%s)이 열 등록부의 틀(%s)과 꼴이 다르다" % (
                머리.get("시트"), " · ".join(축열), " · ".join(c["id"] for c in 틀)), 종류="기간")
        for c, ID in zip(틀, 축열):
            속 = 열속성(축, ID)
            c["기간"] = 속["기간"]
            if 속["달아님"]:
                c["달아님"] = True
        return 새
    본 = {}
    for c in 틀:      # 갈래마다 틀의 첫 열에서 폭 따위를 받는다
        본.setdefault((c["갈래"], c.get("구간")), c)
        본.setdefault(c["종류"], c)
    새열 = []
    남 = {c["id"] for i, c in enumerate(열) if i not in set(자리)}
    for ID in 축열:
        속 = 열속성(축, ID)
        틀한 = 본.get((속["갈래"], 속["구간"])) or 본.get(속["종류"]) or {}
        if ID in 남:
            raise 손오류("%s — 기간 ID 「%s」 가 이 시트의 다른 열 ID 와 겹친다" % (머리.get("시트"), ID), 종류="기간")
        한 = OrderedDict(id=ID, 종류=속["종류"], 갈래=속["갈래"])
        if 속["구간"]:
            한["구간"] = 속["구간"]
        for 키 in ("폭", "숨김", "수준", "접힘"):
            if 틀한.get(키):
                한[키] = 틀한[키]
        한["기간"] = 속["기간"]
        if 속["달아님"]:
            한["달아님"] = True
        if 틀한.get("id"):
            한["틀열"] = 틀한["id"]      # 폭 따위를 받은 틀의 열 — 옛 서식 길이 이 열의 칸 서식을 입힌다
        새열.append(한)
    새["열"] = 열[:자리[0]] + 새열 + 열[자리[-1] + 1:]
    return 새


def 간추림(축):
    """좌표 지도에 실을 축 — 열 · 속성 · 묶음 · 자리 · 평가기준일 · 기간 넷 · 재무기준일 · 이월연수(2026-10-25 — 축이 낼 때)."""
    return OrderedDict((k, 축[k]) for k in ("평가기준일", "재무기준일", "이월연수", "결산월", "실적연도수", "상세추정연수", "수렴연수",
                                           "열", "묶음", "자리", "속성")
                       if k in 축)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    try:
        축 = 축사전(sys.argv[1])
    except Exception as e:      # 배치오류
        print("기간 오류 — %s" % (getattr(e, "오류목록", None) or e))
        sys.exit(1)
    for ID in 축["열"]:
        속 = 열속성(축, ID)
        기 = 속["기간"]
        print("%-9s %-3s %-5s %-3s 종료 %-10s %5s개월%s" % (ID, 속["종류"], 속["갈래"], 속["구간"] or "", 기.get("종료일") or "",
                                                       기.get("개월"), "  (달 단위 아님)" if 속["달아님"] else ""))
    print("자리:", json.dumps(축["자리"], ensure_ascii=False))

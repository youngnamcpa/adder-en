# -*- coding: utf-8 -*-
"""레터자료 — 레터 「평가 방법과 사용 자료」의 자료 수집 표. 회차 `_raw` 에 쌓인 조사 산출물을 세어 한 장으로 적는다.

무엇을 얼마나 모았고 그것이 어느 가정으로 갔는지가 레터 앞부분에 있어야 독자가 「이 숫자를 무엇으로 정했나」를 따라간다(2026-10-22 —
병렬로 모은 자료가 매출 분류와 가정을 거쳐 값까지 가는 사슬을 보여 준다). 표는 수치층이다 — 파일이 없으면 그 줄은
서지 않고(해당 없음은 지운다), 셈은 산출물의 정해진 칸(`가정_스키마.md` 「갈래 산출물」 · 각 도구의 출력 꼴)에서만 한다.
회사 이름 · 종목은 코드에 없다. 「간 자리」는 그 산출물을 쓰는 가정의 자리이고 키트가 정한 것이다.

셈은 「건 · 개 · 개사 · 개 종목」으로 적는다 — 게이트 ⑦ 의 값 꼴(원 · % · 배 · 일 …)이 아니다.
"""
from __future__ import annotations

import glob
import io
import json
import os
import re

_원문 = re.compile(r"^(\d{14})(?:_\d+)?\.(?:txt|xml|html?)$")


def _읽(p):
    try:
        return json.load(io.open(p, encoding="utf-8"))
    except Exception:                                        # noqa: BLE001
        return None


def _수(n):
    return "{:,}".format(int(n))


def _길이(x):
    return len(x) if isinstance(x, (list, dict)) else 0


def _문서수(j):
    """갈래 산출물 공통 머리의 열람 문서 수 — 예산실측.문서 · coverage.문서_열람_성공 · coverage.문서."""
    for 머 in ("예산실측", "coverage"):
        m = j.get(머) if isinstance(j, dict) else None
        if isinstance(m, dict):
            for k in ("문서_열람_성공", "문서"):
                v = m.get(k)
                if isinstance(v, (int, float)) and v > 0:
                    return int(v)
                if isinstance(v, list) and v:
                    return len(v)
    return 0


# 파일 · 자료 이름 · 간 자리 · 셀 칸(키, 말) — 키트 산출물의 정해진 꼴
_갈래 = [
    ("매출스트림_웹조사.json", "매출 구조 조사(회사 발화 · 업계 관측 · 시장 규모)", "매출 구분 · 물량과 가격의 경로 · 시나리오 축",
     [("경제갈래", "경제적 매출 구분 후보"), ("관측치", "업계 관측치"), ("company_voice", "회사 발화"), ("market_size", "시장 규모 자료"),
      ("능력", "설비 · 능력 자료"), ("투자_소식", "투자 소식"), ("제품_로드맵", "제품 일정"), ("원가_구조", "원가 구조 자료"),
      ("scenario_axes", "시나리오 축 후보")]),
    ("매출스트림_심화.json", "매출 구분별 심화 조사", "매출 구분별 물량 · 가격 가정",
     [("구분", "매출 구분"), ("관측치", "관측치"), ("company_voice", "회사 발화")]),
    ("매출구분판정.json", "매출 구분과 추정 방법 판정", "매출 구분 · 매출 구분별 추정 방법", [("구분", "매출 구분")]),
    ("동인원천.json", "비용 · 투자 동인의 공시 원천", "원가 · CAPEX · 운전자본 가정의 출발값", [("원천", "원천 항목"), ("항목", "원천 항목")]),
    ("동인진단.json", "비용 동인 판정", "영업비용의 원가 배선(변동 · 고정 · 계단)", [("항목", "비용 항목")]),
    ("투자능력.json", "생산능력과 투자 일정", "설비투자 · 감가상각 · 판매량 상한", [("능력단위", "능력 단위"), ("단위능력당투자비", "단위 투자비 관측")]),
    ("조항후보.json", "공시 문장의 약정 · 제약 조항", "외부 제약 · 우발 항목", [("후보", "조항 후보")]),
    ("표현실현.json", "회사가 밝힌 계획과 실현값 대조", "회사 발화를 가정에 옮길 때의 조정", [("실현매출", "대조")]),
]


def _공시원문(raw):
    번호 = set()
    for 뿌리, 폴더들, 파일들 in os.walk(raw):
        if os.path.basename(뿌리).lower() in ("peers",):
            폴더들[:] = []
            continue
        for f in 파일들:
            m = _원문.match(f)
            if m:
                번호.add(m.group(1))
    if not 번호:
        return None
    목록 = _읽(os.path.join(raw, "dart_정기보고서_목록.json"))
    종류 = {}
    if isinstance(목록, list):
        이름 = {("%s" % (x.get("rcept_no") or x.get("접수번호") or "")): ("%s" % (x.get("report_nm") or x.get("보고서명") or ""))
               for x in 목록 if isinstance(x, dict)}
        for b in 번호:
            n = 이름.get(b, "")
            k = "사업보고서" if "사업보고서" in n else "반기보고서" if "반기보고서" in n else "분기보고서" if "분기보고서" in n else "그 밖의 공시"
            종류[k] = 종류.get(k, 0) + 1
    범 = (" · ".join("%s %s건" % (k, _수(종류[k])) for k in ("사업보고서", "반기보고서", "분기보고서", "그 밖의 공시") if 종류.get(k))
         if 종류 else "%s건" % _수(len(번호)))
    return ["공시 원문(정기보고서 본문과 주석)", 범, "실적 열 · 매출 구분 · 비용의 성격 · 유형자산 · 운전자본의 출발값"]


def _두날다름(가정):
    """가정의 재무기준일이 평가기준일과 다른가(2026-10-25 날짜 둘 — `기준일.py`). 못 풀면 거짓(옛 글)."""
    try:
        import 기준일 as _기                                  # noqa: PLC0415
        r = _기.기준일들(가정 or {})
        return not r.get("오류") and not r.get("같음")
    except Exception:                                        # noqa: BLE001
        return False


def _재무(raw, 가정=None):
    칸 = []
    for 말, 무늬 in (("연결", "dart_재무_연결_*.json"), ("별도", "dart_재무_별도_*.json")):
        n = max([_길이((_읽(p) or {}).get("list")) for p in glob.glob(os.path.join(raw, 무늬))] or [0])
        if n:
            칸.append("%s %s개 계정" % (말, _수(n)))
    j = _읽(os.path.join(raw, "companyfacts.json"))
    if isinstance(j, dict) and isinstance(j.get("facts"), dict):
        n = sum(_길이(v) for v in j["facts"].values())
        if n:
            칸.append("XBRL 재무 사실 %s개" % _수(n))
    if not 칸:
        return None
    return ["재무제표 계정(전자공시 · XBRL)", " · ".join(칸),
            "실적 열 · %s 재무상태 · 가치 브리지" % ("재무 자료 기준일" if _두날다름(가정) else "평가기준일")]


def _제약(raw):
    j = _읽(os.path.join(raw, "외부제약.json"))
    if not isinstance(j, dict) or not isinstance(j.get("제약"), dict):
        return None
    말 = {"법령": "법령", "산업상한": "산업 상한", "규제가격": "규제 가격", "재무약정": "재무약정"}
    칸 = ["%s %s건" % (말.get(k, k), _수(_길이(v))) for k, v in j["제약"].items() if _길이(v)]
    d = _문서수(j)
    if d:
        칸.insert(0, "열람 문서 %s건" % _수(d))
    if not 칸:
        return None
    return ["외부 제약(법령 · 산업 상한 · 규제 가격 · 재무약정)", " · ".join(칸), "가정의 상한과 하한 · 세액공제 · 일몰기한"]


def _유사(raw, 가정):
    p = os.path.join(raw, "peers")
    if not os.path.isdir(p):
        return None
    칸 = []
    for f in sorted(glob.glob(os.path.join(p, "1차컷_*.csv"))):      # 1차 깔때기 — 산업 · 사업 부문으로 고른 모집단(머리 줄 뺌)
        try:
            n = sum(1 for l in io.open(f, encoding="utf-8-sig") if l.strip()) - 1
        except Exception:                                    # noqa: BLE001
            n = 0
        if n > 0:
            칸.append("1차 모집단(%s) %s개사" % ({"국내": "국내", "해외": "해외"}.get(os.path.basename(f)[4:-4], os.path.basename(f)[4:-4]), _수(n)))
    for f, 말 in (("2차통과.json", "2차 통과(국내)"), ("2차통과_해외.json", "2차 통과(해외)")):
        n = _길이(_읽(os.path.join(p, f)))
        if n:
            칸.append("%s %s개사" % (말, _수(n)))
    W = 가정.get("WACC") if isinstance(가정.get("WACC"), dict) else {}
    n = _길이(W.get("유사기업")) if isinstance(W.get("유사기업"), list) else 0
    if n:
        칸.append("최종 채택 %s개사" % _수(n))
    주가 = len(glob.glob(os.path.join(p, "day_*.json")))
    if 주가:
        칸.append("일별 주가 %s개 종목" % _수(주가))
    if not 칸:
        return None
    return ["Peer group 선정과 주가", " · ".join(칸), "할인율(Unlevered Beta · 자본구조)"]


def _시장(raw):
    ps = sorted(glob.glob(os.path.join(raw, "시장데이터_*.json")))
    j = _읽(ps[-1]) if ps else None
    if not isinstance(j, dict):
        return None
    항 = [_시장말(re.sub(r"\s*\(.*?\)", "", k)) for k, v in j.items() if isinstance(v, dict) and k not in ("거시지표",)]
    if not 항:
        return None
    return ["시장 자료(평가기준일)", " · ".join(dict.fromkeys(항)), "할인율(무위험이자율 · MRP · 타인자본비용)"]


_시장칸말 = {"시장위험프리미엄": "MRP", "국가위험프리미엄": "국가위험프리미엄", "회사채 전 등급": "회사채 수익률(전 등급)", "합성등급 스프레드 표": "합성등급 스프레드"}


def _시장말(k):
    """시장 자료 칸 이름 → 레터의 말(용어표 — 영어로 쓰기로 한 것은 영어로: 시장위험프리미엄 → MRP)."""
    return _시장칸말.get(k.strip(), k.strip())


def _분포(raw):
    j = _읽(os.path.join(raw, "기저율.json"))
    패 = j.get("패널") if isinstance(j, dict) else None
    if not isinstance(패, dict):
        return None
    사, 년 = 패.get("정리후_회사수") or 패.get("회사수"), 패.get("정리후_회사연도") or 패.get("회사연도")
    if not (사 and 년):
        return None
    연 = (j.get("입력") or {}).get("패널연도") if isinstance(j.get("입력"), dict) else None
    기 = ("(%d~%d년)" % (min(연), max(연))) if isinstance(연, list) and 연 else ""
    return ["상장사 실적 분포", "%s개사 · %s개 회사연도%s" % (_수(사), _수(년), 기), "매출 성장률 · 영업이익률 가정이 분포의 어디에 있나"]


# 능력 구분(구조.매출구분[] 의 판매량산정 「능력」)이 없는 회사의 자료 이름 · 간 자리 — 레터가 선언하지 않은 말 묶음(생산능력 · 판매량)을 쓰지 않는다
_능력없을때 = {"투자능력.json": ("설비투자 계획과 투자 일정", "설비투자 · 감가상각")}


def 능력구분있나(가정):
    """가정의 매출 구분 가운데 판매량을 생산능력으로 정하는 것(판매량산정 「능력」)이 있나."""
    구 = (가정 or {}).get("구조") if isinstance(가정, dict) else None
    구분들 = (구 or {}).get("매출구분") if isinstance(구, dict) else None
    return any(isinstance(x, dict) and x.get("판매량산정") == "능력" for x in 구분들 or [])


def 수집표(회차, 가정):
    """→ [[자료, 모은 범위, 간 자리]] — 회차 폴더의 `_raw` 에서. 없으면 빈 목록."""
    raw = os.path.join(회차 or "", "_raw")
    if not 회차 or not os.path.isdir(raw):
        return []
    줄 = [x for x in (_공시원문(raw), _재무(raw, 가정)) if x]
    능력 = 능력구분있나(가정)
    for f, 이름, 자리, 칸들 in _갈래:
        j = _읽(os.path.join(raw, f))
        if not isinstance(j, dict):
            continue
        if f in _능력없을때 and not 능력:            # 능력으로 판매량을 정하는 구분이 없으면 「생산능력 · 판매량 상한」 을 쓰지 않는다(N3)
            이름, 자리 = _능력없을때[f]
        칸 = []
        d = _문서수(j)
        if d:
            칸.append("열람 문서 %s건" % _수(d))
        본 = set()
        for k, 말 in 칸들:
            n = _길이(j.get(k))
            if n and 말 not in 본:
                칸.append("%s %s건" % (말, _수(n)))
                본.add(말)
        if 칸:
            줄.append([이름, " · ".join(칸), 자리])
    줄 += [x for x in (_제약(raw), _유사(raw, 가정), _시장(raw), _분포(raw)) if x]
    return 줄

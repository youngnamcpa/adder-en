# -*- coding: utf-8 -*-
"""상세변수공통 — 국내 상세 패널 변수(`dart_상세변수` · `dart_직원패널` · `dart_주석패널`)의 출력 계약 한 벌 (2026-10-24 PK).

    자리  {공용}/기저율/KR/상세변수/<변수>.csv   (공용 = DCF_공용캐시 · DCF_SHARED_CACHE · 없으면 ~/.dcf캐시)
          {공용}/기저율/KR/상세변수/목록.json
    열    고유번호 · 회계연도 · 값 · 분자 · 분모 · 단위 · 기준(연결/별도) · 원천(접수번호 · 항목) · 기간끝 · 딱지(같음/[유추]) · 비고

통합 갈래(기저율 · 지속성 · 사후대조 · 변수카드)가 이 꼴을 읽는다 — 열 이름 · 순서를 바꾸지 않는다.
커버리지의 분모는 기저율 패널과 같은 규칙(`기저율설정.json` 자료_제외 — 표시통화 KRW · 제외 산업 · 기업인수목적 · 기준연도 매출 하한)으로 센
주요계정 회사 · 연도다. 회사 · 업종 이름은 이 파일에 없다(범용).
"""
from __future__ import annotations

import csv
import datetime
import io
import json
import os
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)

판 = "상세변수 1"
머리 = ["고유번호", "회계연도", "값", "분자", "분모", "단위", "기준", "원천", "기간끝", "딱지", "비고"]
성공창 = (2016, 2025)                                    # P1 성공 기준 — 국내 회사 · 연도 창


def 공용뿌리():
    return (os.environ.get("DCF_공용캐시") or os.environ.get("DCF_SHARED_CACHE")
            or os.path.join(os.path.expanduser("~"), ".dcf캐시"))


def 패널뿌리():
    """국내 기저율 패널 자리(주요계정 · 산업분류 · 일괄 ZIP) — `기저율.패널자리` 와 같은 규칙."""
    try:
        import 기저율 as 기                                  # noqa: PLC0415
        return 기.패널자리(기.국가설정(기.설정읽기(), "KR"))
    except Exception:                                    # noqa: BLE001
        return os.path.join(공용뿌리(), "기저율")


def 자리(뿌리=None):
    p = os.path.join(뿌리 or 패널뿌리(), "KR", "상세변수")
    os.makedirs(p, exist_ok=True)
    return p


def 지금():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def 수(s):
    """「1,234」 · 「-」 · 「」 → float | None."""
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    t = ("%s" % s).strip().replace(",", "")
    if not t or t in ("-", "－"):
        return None
    try:
        return float(t)
    except ValueError:
        return None


def 글(v, 자릿=10):
    if v is None:
        return ""
    if isinstance(v, float):
        if abs(v) >= 1e4 and float(v).is_integer():
            return "%.0f" % v
        return ("%." + str(자릿) + "g") % v if abs(v) < 1e4 else "%.0f" % v
    return "%s" % v


# ═══════════════════════════════════════════════ 분모 — 기저율 패널과 같은 규칙

def 제외규칙():
    try:
        d = json.load(io.open(os.path.join(여기, "기저율설정.json"), encoding="utf-8"))
        z = d.get("자료_제외") or {}
    except Exception:                                    # noqa: BLE001
        z = {}
    return {"통화": z.get("표시통화", "KRW"), "산업": tuple(z.get("제외_산업") or ("64", "65", "66", "68")),
            "이름": tuple(z.get("기업인수목적_이름") or ("스팩", "기업인수목적")), "매출하한": float(z.get("기준연도_매출_하한_원") or 1e9)}


def 산업분류(뿌리=None):
    """{고유번호: {종목코드 · 산업분류코드 · 상장구분 · 회사명 · 결산월}} · {종목코드: 고유번호}."""
    p = os.path.join(뿌리 or 패널뿌리(), "산업분류.csv")
    by고, by종 = {}, {}
    if not os.path.exists(p):
        return by고, by종
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            고 = (r.get("고유번호") or "").strip().zfill(8)
            종 = (r.get("종목코드") or "").strip()
            by고[고] = {"종목코드": 종.zfill(6) if 종 else "", "산업분류코드": (r.get("산업분류코드") or "").strip(),
                       "상장구분": (r.get("상장구분") or "").strip(), "회사명": (r.get("회사명") or "").strip(),
                       "결산월": (r.get("결산월") or "").strip()}
            if 종:
                by종[종.zfill(6)] = 고
    return by고, by종


def 제외인가(고, 산, 이름, 규칙):
    ks = ((산 or {}).get("산업분류코드") or "")[:2]
    if ks and ks in 규칙["산업"]:
        return "제외 산업 %s" % ks
    if any(w in (이름 or "") for w in 규칙["이름"]):
        return "기업인수목적"
    return None


def 분모(뿌리=None, 해들=None):
    """{연도: set(고유번호)} — 주요계정 가운데 표시통화 KRW · 매출 ≥ 하한 · 제외 산업 · 기업인수목적이 아닌 회사."""
    뿌리 = 뿌리 or 패널뿌리()
    규칙 = 제외규칙()
    by고, _ = 산업분류(뿌리)
    낸 = {}
    for y in (해들 or range(2015, 2026)):
        p = os.path.join(뿌리, "주요계정_%d.csv" % y)
        if not os.path.exists(p):
            continue
        s = set()
        with io.open(p, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                고 = (r.get("고유번호") or "").strip().zfill(8)
                if (r.get("표시통화") or "KRW").strip() != 규칙["통화"]:
                    continue
                매 = 수(r.get("매출액"))
                if not 매 or 매 < 규칙["매출하한"]:
                    continue
                if 제외인가(고, by고.get(고), r.get("회사명"), 규칙):
                    continue
                s.add(고)
        낸[y] = s
    return 낸


def 주요계정(뿌리=None, 해들=None):
    """{(고유번호, 연도): 행} — 영업이익률 · 매출 · 자산(5년 평균 · 설비 집약 판정)."""
    뿌리 = 뿌리 or 패널뿌리()
    낸 = {}
    for y in (해들 or range(2015, 2026)):
        p = os.path.join(뿌리, "주요계정_%d.csv" % y)
        if not os.path.exists(p):
            continue
        with io.open(p, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                낸[((r.get("고유번호") or "").strip().zfill(8), y)] = r
    return 낸


# ═══════════════════════════════════════════════ 쓰기 · 목록

def 쓰기(변수, 줄들, 뜻, 뿌리=None, 분모해=None, 창=None, 덧=None):
    """변수 CSV 를 통째로 쓰고 목록.json 의 그 변수 칸을 고친다. 줄 = dict(머리 열). 뜻 = {정의 · 칸 · 단위 · 딱지 · 원천 · 도구}.
    → 목록 칸(해별 회사 수 · 커버리지)."""
    곳 = 자리(뿌리)
    줄들 = sorted(줄들, key=lambda r: (r["고유번호"], int(r["회계연도"])))
    with io.open(os.path.join(곳, "%s.csv" % 변수) + ".part", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=머리)
        w.writeheader()
        for r in 줄들:
            w.writerow({k: 글(r.get(k)) if k in ("값", "분자", "분모") else ("" if r.get(k) is None else r.get(k)) for k in 머리})
    os.replace(os.path.join(곳, "%s.csv" % 변수) + ".part", os.path.join(곳, "%s.csv" % 변수))
    해별 = {}
    for r in 줄들:
        해별[int(r["회계연도"])] = 해별.get(int(r["회계연도"]), 0) + 1
    분 = 분모해 if 분모해 is not None else 분모(뿌리)
    a, b = 창 or 성공창
    회사해 = {(r["고유번호"], int(r["회계연도"])) for r in 줄들}
    덮음 = {y: (len({고 for 고, yy in 회사해 if yy == y} & 분.get(y, set())), len(분.get(y, set()))) for y in sorted(분)}
    전체 = [덮음[y] for y in 덮음 if a <= y <= b]
    칸 = dict(뜻)
    칸.update({"해별회사수": {str(y): n for y, n in sorted(해별.items())},
              "커버리지": {str(y): (round(n / d, 4) if d else None) for y, (n, d) in 덮음.items()},
              "커버리지_창": "%d~%d" % (a, b),
              "커버리지_전체": (round(sum(n for n, _ in 전체) / sum(d for _, d in 전체), 4) if sum(d for _, d in 전체) else None),
              "줄수": len(줄들), "갱신": 지금()})
    if 덧:
        칸.update(덧)
    목록고치기(뿌리, 변수=(변수, 칸))
    return 칸


def 목록읽기(뿌리=None):
    p = os.path.join(자리(뿌리), "목록.json")
    if not os.path.exists(p):
        return {"판": 판, "국가": "KR", "만든날": 지금(), "변수": {}, "이어받기": {}}
    return json.load(io.open(p, encoding="utf-8"))


def 목록고치기(뿌리=None, 변수=None, 이어=None):
    d = 목록읽기(뿌리)
    d["판"] = 판
    d["갱신"] = 지금()
    if 변수:
        d.setdefault("변수", {})[변수[0]] = 변수[1]
    if 이어:
        d.setdefault("이어받기", {})[이어[0]] = 이어[1]
    p = os.path.join(자리(뿌리), "목록.json")
    io.open(p + ".part", "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=1))
    os.replace(p + ".part", p)
    return d


def 읽기(변수, 뿌리=None):
    """{(고유번호, 연도): 행} — 다른 도구(검증 규칙 · 통합 갈래)가 읽는다."""
    p = os.path.join(자리(뿌리), "%s.csv" % 변수)
    if not os.path.exists(p):
        return {}
    with io.open(p, encoding="utf-8", newline="") as f:
        return {(r["고유번호"], int(r["회계연도"])): r for r in csv.DictReader(f)}

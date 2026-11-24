# -*- coding: utf-8 -*-
"""dart_주석패널 — DART XBRL 원본(fnlttXbrl.xml)의 **주석 숫자**로 설비계수 · 내용연수 · 인건비율 · 유지율 패널을 짓는다 (2026-10-24 PK · C 단계).

주석 숫자는 2023 사업연도부터 자산 규모 순으로 단계 도입됐다(P2 실측 — 2023 약 3.8조 이상 · 2024 약 5천억 이상 · 2025 약 3,200억 이상).
그래서 창은 2023~2025 이고, 받는 회사는 기저율 분모(제외 산업 · 기업인수목적 · 매출 하한) 가운데 12월 결산 · 그 해 자산총계가 문턱 이상인 곳이다
(문턱은 실측보다 낮게 둔다 — 받았는데 주석이 없으면 「주석 없음」으로 남고 다음에 다시 받지 않는다).

받기
  ① 사업보고서 목록 — `list.json`(회사 지정 없이 · 석 달 창 · pblntf_detail_ty A001)을 다음 해 1~12월로 훑어 「사업보고서 (YYYY.12)」 의 가장 늦은 접수번호
  ② `fnlttXbrl.xml?rcept_no=…&reprt_code=11011` ZIP 을 `{상세변수}/_원천/주석XBRL/<연도>/<접수번호>.zip` 에(있으면 다시 받지 않는다)
짓기 — 인스턴스(.xbrl)의 컨텍스트 · 사실을 읽는다
  · `dart:ReportedAmountMember`(장부금액 축의 기본 멤버)는 **축 없음**으로 읽는다(P2 함정 ① — 안 그러면 종업원급여 · 유효세율이 거의 다 빠진다)
  · 기준 — 연결 멤버(또는 축 없음)를 먼저, 그 회사 · 연도가 일괄 본표에서 별도만이면 축 없음을 별도로 본다(`상세변수공통` A 단계의 기준 열)
  · 허용 축 밖의 축(부문 · 지역 따위)이 달린 사실은 읽지 않는다

    변수(모델 칸)                 정의                                                                          딱지
    설비계수(7k1)                 (성격별 비용 합계 − 종업원급여 − 감가상각비 − 재고 변동) ÷ 평균 기계장치 총액            같음(기계장치 총액이 없으면 유형자산 총액 — [유추])
                                 · 설비 집약(유형자산 순액 ÷ 매출 ≥ 0.4)인 회사만 · 검증: 성격별 합계 ≈ 매출 − 영업이익(±5%)
    평균내용연수(80g)              (유형자산 총액 − 토지 − 건설중인자산) ÷ 유형자산 감가상각비(변동표)                    [유추] 평균(혼합 연령) · 토지를 못 빼면 그 사실을 비고에
    기계장치내용연수(801 · 802 꼴)  기계장치 총액 ÷ 기계장치 감가상각비(변동표)                                      [유추] 평균
    인건비율(520)                 종업원급여(연결) ÷ 매출 · 검증: 별도 종업원급여 ≥ 직원현황 급여총액 × 0.8(P2 함정 ②)     같음
    유지율_취득원가(850 대용)       유형자산 취득(변동표) ÷ 기초 유형자산 총액                                          [유추] 성장분 포함
    평균유효세율_주석(196 대조)     회사가 주석에 적은 평균 유효세율(AverageEffectiveTaxRate)                           [유추] 실현 세율
    (보강) 상각률_기초순액 · 매입채무회전일수 · 무형상각률 — 일괄 본표에 없는 회사 · 연도를 주석 값으로 메워 A 단계 CSV 에 합친다(`_보강_주석/`).
          같은 ZIP 의 비교 기간(전기)도 읽어 그 회사의 전년 ZIP 이 없으면 전년 줄을 보탠다(호출 0 · 2026-10-24 PN)
    (D) 원문 역보강 — 2019~2022 를 사업보고서 원문 표로(아래 「D」 절 · `--원문역보강`). 정확도를 먼저 재고 통과 항목만 `_보강_원문/`

    python 스크립트/dart_주석패널.py [--부터 2023] [--까지 2025] [--상한 4000] [--짓기만]
    python 스크립트/dart_주석패널.py --원문역보강 [--표본 600] [--부터 2019] [--까지 2022] [--상한 2000] [--짓기만]
키 — 환경변수 OPENDART_API_KEY(값을 찍지 않는다). 종료 코드 — 0 · 2(키 · 분모 없음). 회사 · 업종 이름은 이 도구에 없다(범용).
"""
from __future__ import annotations

import argparse
import csv
import datetime
import glob
import gzip
import io
import json
import os
import re
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass
여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
import 상세변수공통 as 공  # noqa: E402

API = "https://opendart.fss.or.kr/api"
간격 = 0.15
문턱 = {2023: 2.0e12, 2024: 4.0e11, 2025: 2.5e11}           # 자산총계(원) — 실측 도입 문턱보다 낮게
기본문턱 = 2.5e11
멈춤코드 = {"020": "사용 한도 초과", "010": "등록되지 않은 키", "011": "사용할 수 없는 키", "012": "접근할 수 없는 IP", "800": "시스템 점검", "901": "키 만료"}
설비집약 = 0.4

NSX = "{http://www.xbrl.org/2003/instance}"
NSD = "{http://xbrl.org/2006/xbrldi}"
축_기준 = "ConsolidatedAndSeparateFinancialStatementsAxis"
축_장부 = "CarryingAmountAccumulatedDepreciationAmortisationAndImpairmentAndGrossCarryingAmountAxis"
축_자산군 = "ClassesOfPropertyPlantAndEquipmentAxis"
허용축 = {축_기준, 축_장부, 축_자산군}

태그 = {
    "성격별합계": ["ExpenseByNature"],
    "종업원급여": ["EmployeeBenefitsExpense"],
    "감가상각_성격": ["DepreciationAndAmortisationExpense", "DepreciationExpense"],
    "재고변동": ["ChangesInInventoriesOfFinishedGoodsAndWorkInProgress"],
    "매출": ["Revenue", "RevenueFromContractsWithCustomers"],
    "영업이익": ["OperatingIncomeLoss", "ProfitLossFromOperatingActivities"],
    "매출원가": ["CostOfSales"],
    "유형자산": ["PropertyPlantAndEquipment"],
    "유형상각": ["DepreciationPropertyPlantAndEquipment"],
    "유형취득": ["AdditionsOtherThanThroughBusinessCombinationsPropertyPlantAndEquipment"],
    "평균유효세율": ["AverageEffectiveTaxRate"],
    "순수매입채무": ["TradeAndOtherCurrentPayablesToTradeSuppliers", "CurrentTradePayables", "ShortTermTradePayables"],
    # 무형(164 보강 · 2026-10-24 PN) — 순액은 일괄 본표와 같은 차례(영업권 포함 한 줄 → 영업권 제외)
    "무형순액": ["IntangibleAssetsAndGoodwill", "IntangibleAssetsOtherThanGoodwill"],
    "무형상각": ["AmortisationIntangibleAssetsOtherThanGoodwill", "AmortisationExpense"],
    "무형취득": ["AdditionsOtherThanThroughBusinessCombinationsIntangibleAssetsOtherThanGoodwill"],
}


def 원천자리(뿌리=None, y=None):
    p = os.path.join(공.자리(뿌리), "_원천", "주석XBRL")
    if y is not None:
        p = os.path.join(p, str(y))
    os.makedirs(p, exist_ok=True)
    return p


def 보강자리(뿌리=None):
    p = os.path.join(공.자리(뿌리), "_보강_주석")
    os.makedirs(p, exist_ok=True)
    return p


# ═══════════════════════════════════════════════ 받기

def _get(path, 키, 열기=None, 바이트=False, **p):
    p["crtfc_key"] = 키
    u = "%s/%s?%s" % (API, path, urllib.parse.urlencode(p))
    열기 = 열기 or (lambda x: urllib.request.urlopen(x, timeout=90).read())
    for i in range(3):
        try:
            b = 열기(u)
            return b if 바이트 else json.loads(b.decode("utf-8"))
        except Exception:                                # noqa: BLE001
            time.sleep(2.0 * (i + 1))
    return None


def 목록받기(y, 키, 뿌리=None, 열기=None):
    """그 사업연도(12월 결산) 사업보고서 {고유번호: 접수번호} — 다음 해 1~12월 석 달 창. 캐시 `_원천/주석XBRL/<y>/목록.json`."""
    p = os.path.join(원천자리(뿌리, y), "목록.json")
    if os.path.exists(p):
        return json.load(io.open(p, encoding="utf-8")), 0
    낸, 부른 = {}, 0
    for 시작달 in (1, 4, 7, 10):
        bgn = datetime.date(y + 1, 시작달, 1)
        end = (datetime.date(y + 1, 시작달 + 3, 1) - datetime.timedelta(days=1)) if 시작달 < 10 else datetime.date(y + 1, 12, 31)
        쪽 = 1
        while True:
            j = _get("list.json", 키, 열기, bgn_de=bgn.strftime("%Y%m%d"), end_de=end.strftime("%Y%m%d"), pblntf_ty="A", pblntf_detail_ty="A001",
                     page_no=쪽, page_count=100)
            부른 += 1
            time.sleep(간격)
            if not j or j.get("status") != "000":
                if j and j.get("status") in 멈춤코드:
                    raise RuntimeError("OpenDART %s(%s)" % (j["status"], 멈춤코드[j["status"]]))
                break
            for x in j.get("list") or []:
                nm = (x.get("report_nm") or "").replace(" ", "")
                if "사업보고서(%d.12)" % y not in nm:
                    continue
                고 = (x.get("corp_code") or "").zfill(8)
                if 고 not in 낸 or x["rcept_no"] > 낸[고]:
                    낸[고] = x["rcept_no"]
            if 쪽 >= int(j.get("total_page") or 1):
                break
            쪽 += 1
    io.open(p, "w", encoding="utf-8").write(json.dumps(낸, ensure_ascii=False))
    return 낸, 부른


def 대상(y, 뿌리=None):
    """그 해 받을 회사 [(고유번호, 자산총계)] — 분모 ∩ 12월 결산 ∩ 자산총계 ≥ 문턱."""
    분 = 공.분모(뿌리, [y]).get(y, set())
    주 = 공.주요계정(뿌리, [y])
    by고, _ = 공.산업분류(뿌리)
    낸 = []
    for 고 in sorted(분):
        if not ((by고.get(고) or {}).get("결산월") or "12").startswith("12"):
            continue
        자 = 공.수((주.get((고, y)) or {}).get("자산총계"))
        if 자 and 자 >= 문턱.get(y, 기본문턱):
            낸.append((고, 자))
    return 낸


def 받기(뿌리=None, 부터=2023, 까지=2025, 상한=4000, 키=None, 열기=None, 조용=False):
    키 = 키 or os.environ.get("OPENDART_API_KEY")
    if not 키:
        return {"멈춘까닭": "키 없음(OPENDART_API_KEY)", "부른수": 0}
    부른, 받은, 없음, 까닭 = 0, 0, 0, "다 받음"
    시 = time.time()
    해별 = {}
    try:
        for y in range(까지, 부터 - 1, -1):
            목, n = 목록받기(y, 키, 뿌리, 열기)
            부른 += n
            할 = [(고, 목[고]) for 고, _ in 대상(y, 뿌리) if 고 in 목]
            곳 = 원천자리(뿌리, y)
            결과p = os.path.join(곳, "받기결과.json")
            결과 = json.load(io.open(결과p, encoding="utf-8")) if os.path.exists(결과p) else {}
            해별[y] = {"대상": len(대상(y, 뿌리)), "목록에있음": len(할)}
            for 고, rc in 할:
                zp = os.path.join(곳, "%s.zip" % rc)
                if os.path.exists(zp) or 결과.get(rc) in ("ZIP 아님", "013", "014"):
                    continue
                if 부른 >= 상한:
                    까닭 = "상한 %d 에 닿음" % 상한
                    raise StopIteration
                b = _get("fnlttXbrl.xml", 키, 열기, 바이트=True, rcept_no=rc, reprt_code="11011")
                부른 += 1
                time.sleep(간격)
                if b and b[:2] == b"PK":
                    io.open(zp + ".part", "wb").write(b)
                    os.replace(zp + ".part", zp)
                    받은 += 1
                    결과[rc] = "있음"
                else:
                    t = (b or b"")[:400].decode("utf-8", "replace")
                    m = re.search(r"<status>(\d+)</status>|\"status\"\s*:\s*\"(\d+)\"", t)
                    st = (m.group(1) or m.group(2)) if m else "ZIP 아님"
                    if st in 멈춤코드:
                        까닭 = "OpenDART %s(%s) — 멈춤" % (st, 멈춤코드[st])
                        raise StopIteration
                    결과[rc] = st
                    없음 += 1
                if (받은 + 없음) % 100 == 0:
                    io.open(결과p, "w", encoding="utf-8").write(json.dumps(결과, ensure_ascii=False))
                    if not 조용:
                        print("  주석 %d — 받음 %d · 없음 %d · 부름 %d · %.0f초" % (y, 받은, 없음, 부른, time.time() - 시), flush=True)
            io.open(결과p, "w", encoding="utf-8").write(json.dumps(결과, ensure_ascii=False))
    except StopIteration:
        pass
    except RuntimeError as e:
        까닭 = "%s — 멈춤" % e
    상태 = {"마지막실행": 공.지금(), "부른수": 부른, "받은ZIP": 받은, "ZIP없음": 없음, "멈춘까닭": 까닭, "해": "%d~%d" % (부터, 까지),
          "해별": {str(k): v for k, v in 해별.items()}, "문턱_자산총계": {str(k): v for k, v in 문턱.items()}, "걸린초": round(time.time() - 시, 1),
          "원천": "OpenDART fnlttXbrl.xml(사업보고서 XBRL 원본) · list.json"}
    공.목록고치기(뿌리, 이어=("주석XBRL", 상태))
    return 상태


# ═══════════════════════════════════════════════ 읽기

def 인스턴스(zp):
    """ZIP → (컨텍스트 {id: {끝 · 시작 · 멤버}}, 사실 [(로컬 태그, 컨텍스트, 값)])."""
    with zipfile.ZipFile(zp) as z:
        inst = [n for n in z.namelist() if n.lower().endswith(".xbrl")]
        if not inst:
            return {}, []
        root = ET.fromstring(z.read(inst[0]))
    ctx = {}
    for c in root.iter(NSX + "context"):
        per = c.find(NSX + "period")
        if per is None:
            continue
        i, s, e = per.find(NSX + "instant"), per.find(NSX + "startDate"), per.find(NSX + "endDate")
        mem = {}
        for m in c.iter(NSD + "explicitMember"):
            mem[(m.get("dimension") or "").split(":")[-1]] = (m.text or "").split(":")[-1].strip()
        ctx[c.get("id")] = {"끝": ((i.text if i is not None else (e.text if e is not None else "")) or "").strip(),
                            "시작": ((s.text if s is not None else "") or "").strip() or None, "멤버": mem}
    사실 = []
    for el in root:
        cid = el.get("contextRef")
        if cid is None or el.text is None:
            continue
        try:
            v = float(el.text.strip())
        except ValueError:
            continue
        사실.append((el.tag.split("}")[-1], cid, v))
    return ctx, 사실


def _기준(mem, 축없음기준):
    b = mem.get(축_기준)
    if b is None:
        return 축없음기준
    return {"ConsolidatedMember": "연결", "SeparateMember": "별도"}.get(b)


def 값(ctx, 사실, 이름들, 기준, 끝, 시작=None, 장부=None, 자산군=None, 축없음기준="연결"):
    """조건에 맞는 첫 사실 값. 장부 = None(축 없음 · ReportedAmountMember) | "Gross" | "Accumulated" | "아무거나". 자산군 = None(축 없음 = 합계) | 멤버 이름."""
    for 이름 in 이름들:
        for t, cid, v in 사실:
            if t != 이름:
                continue
            c = ctx.get(cid)
            if not c or c["끝"] != 끝:
                continue
            if 시작 is None and c["시작"]:
                continue
            if 시작 is not None and (not c["시작"] or abs((datetime.date.fromisoformat(c["시작"]) - datetime.date.fromisoformat(시작)).days) > 7):
                continue
            mem = c["멤버"]
            if set(mem) - 허용축:
                continue
            if _기준(mem, 축없음기준) != 기준:
                continue
            g = mem.get(축_장부, "ReportedAmountMember")
            if 장부 is None and g != "ReportedAmountMember":
                continue
            if 장부 == "Gross" and g != "GrossCarryingAmountMember":
                continue
            if 장부 == "Accumulated" and "Accumulated" not in g:
                continue
            a = mem.get(축_자산군)
            if 자산군 is None and a not in (None, "PropertyPlantAndEquipmentMember"):
                continue
            if 자산군 is not None and a != 자산군:
                continue
            return v
    return None


def 뽑기(zp, y, 축없음기준="연결", 기간해=None, 미리=None):
    """주석 ZIP 하나 → {기준: {재료 …}} — 연결 · 별도 둘 다(있는 만큼). 기간해 = 같은 ZIP 의 비교 기간(전기 — y − 1)을 읽을 때 ·
    미리 = 이미 읽은 (컨텍스트, 사실)(2026-10-24 PN)."""
    ctx, 사실 = 미리 or 인스턴스(zp)
    y = 기간해 or y
    끝, 앞끝, 시작 = "%d-12-31" % y, "%d-12-31" % (y - 1), "%d-01-01" % y
    낸 = {}
    for 기준 in ("연결", "별도"):
        k = dict(ctx=ctx, 사실=사실, 기준=기준, 축없음기준=축없음기준)
        d = {
            "성격별합계": 값(이름들=태그["성격별합계"], 끝=끝, 시작=시작, **k),
            "종업원급여": 값(이름들=태그["종업원급여"], 끝=끝, 시작=시작, **k),
            "감가상각_성격": 값(이름들=태그["감가상각_성격"], 끝=끝, 시작=시작, **k),
            "재고변동": 값(이름들=태그["재고변동"], 끝=끝, 시작=시작, **k),
            "매출": 값(이름들=태그["매출"], 끝=끝, 시작=시작, **k),
            "영업이익": 값(이름들=태그["영업이익"], 끝=끝, 시작=시작, **k),
            "매출원가": 값(이름들=태그["매출원가"], 끝=끝, 시작=시작, **k),
            "유형순액": 값(이름들=태그["유형자산"], 끝=끝, **k),
            "유형순액_기초": 값(이름들=태그["유형자산"], 끝=앞끝, **k),
            "유형총액": 값(이름들=태그["유형자산"], 끝=끝, 장부="Gross", **k),
            "유형총액_기초": 값(이름들=태그["유형자산"], 끝=앞끝, 장부="Gross", **k),
            "기계총액": 값(이름들=태그["유형자산"], 끝=끝, 장부="Gross", 자산군="MachineryMember", **k),
            "기계총액_기초": 값(이름들=태그["유형자산"], 끝=앞끝, 장부="Gross", 자산군="MachineryMember", **k),
            "토지총액": 값(이름들=태그["유형자산"], 끝=끝, 장부="Gross", 자산군="LandMember", **k),
            "건설중총액": 값(이름들=태그["유형자산"], 끝=끝, 장부="Gross", 자산군="ConstructionInProgressMember", **k),
            "평균유효세율": 값(이름들=태그["평균유효세율"], 끝=끝, 시작=시작, **k),
            "순수매입채무": 값(이름들=태그["순수매입채무"], 끝=끝, **k),
            "무형순액_기초": 값(이름들=태그["무형순액"], 끝=앞끝, **k),
        }
        # 무형 상각 · 취득 — 변동표(장부 축 어느 멤버든) 또는 성격별(축 없음)
        for 키_ in ("무형상각", "무형취득"):
            d[키_] = None
            for 장부 in (None, "Accumulated", "Gross"):
                v = 값(이름들=태그[키_], 끝=끝, 시작=시작, 장부=장부, **k)
                if v is not None:
                    d[키_] = abs(v)
                    break
        # 변동표의 감가상각 · 취득 — 장부 축은 어느 멤버든(누계 · 장부금액), 자산군은 합계 · 기계장치
        for 키_, 자산군 in (("유형상각", None), ("기계상각", "MachineryMember"), ("유형취득", None)):
            태 = 태그["유형취득"] if 키_ == "유형취득" else 태그["유형상각"]
            d[키_] = None
            for 장부 in (None, "Accumulated", "Gross"):
                v = 값(이름들=태, 끝=끝, 시작=시작, 장부=장부, 자산군=자산군, **k)
                if v is not None:
                    d[키_] = abs(v)
                    break
        if any(v is not None for v in d.values()):
            낸[기준] = d
    return 낸


def 보강값(d):
    """주석 재료 → {변수: (값, 분자, 분모, 단위, 비고, 범위)} — 상각률(기초 순액) · 매입채무 · 무형상각률(짓기의 보강과 같은 정의 · 전기 보강용)."""
    낸 = {}
    상, s0 = d.get("유형상각"), d.get("유형순액_기초")
    if 상 and s0 is not None and s0 + (d.get("유형취득") or 0.0) / 2.0 > 0:
        밑 = s0 + (d.get("유형취득") or 0.0) / 2.0
        낸["상각률_기초순액"] = (상 / 밑, 상, 밑, "비율", "주석 변동표 감가상각 ÷ (기초 순액 + 취득 ÷ 2) — 일괄 본표 보강", (1e-6, 2.0))
    mp, 원 = d.get("순수매입채무"), d.get("매출원가")
    if mp is not None and 원 and 원 > 0:
        낸["매입채무회전일수"] = (mp / 원 * 365.0, mp, 원, "일", "주석 순수 매입채무 ÷ 매출원가 × 365 — 일괄 본표 보강", (0.0, 3650.0))
    ma, i0 = d.get("무형상각"), d.get("무형순액_기초")
    if ma and i0 is not None and i0 + (d.get("무형취득") or 0.0) / 2.0 > 0:
        밑 = i0 + (d.get("무형취득") or 0.0) / 2.0
        낸["무형상각률"] = (ma / 밑, ma, 밑, "비율", "주석 무형 상각 ÷ (기초 무형자산 + 취득 ÷ 2) — 일괄 본표 보강"
                       + ("" if d.get("무형취득") is not None else " · 취득 없음(0)"), (1e-6, 2.0))
    return 낸


# ═══════════════════════════════════════════════ 짓기

def 짓기(뿌리=None, 부터=2023, 까지=2025, 조용=False):
    분모해 = 공.분모(뿌리)
    기준표 = {}                                           # A 단계의 기준(연결/별도) — 축 없음 사실을 무엇으로 읽나
    for 변 in ("매출원가율", "판관비율"):
        for (고, y), r in 공.읽기(변, 뿌리).items():
            기준표.setdefault((고, y), r.get("기준") or "연결")
    급여총액 = 공.읽기("급여총액", 뿌리)
    줄 = {k: [] for k in ("설비계수", "평균내용연수", "기계장치내용연수", "인건비율", "유지율_취득원가", "평균유효세율_주석")}
    보강 = {"상각률_기초순액": [], "매입채무회전일수": [], "무형상각률": []}
    제출, 집약제출 = set(), set()                         # 주석 숫자를 낸 회사 · 연도(커버리지의 둘째 분모) · 그 가운데 설비 집약
    당기본 = set()                                       # ZIP 의 당기로 읽은 회사 · 연도 — 전기 보강은 이 밖에서만
    셈 = {"ZIP": 0, "주석있음": 0, "설비집약아님": 0, "성격별검증걸림": 0, "인건비검증걸림": 0, "인건비미대조": 0, "기계없어유형총액": 0, "토지못뺌": 0, "정의역밖": 0}
    for y in range(부터, 까지 + 1):
        곳 = os.path.join(공.자리(뿌리), "_원천", "주석XBRL", str(y))
        if not os.path.isdir(곳):
            continue
        목p = os.path.join(곳, "목록.json")
        rc고 = {v: k for k, v in (json.load(io.open(목p, encoding="utf-8")).items() if os.path.exists(목p) else [])}
        for f in sorted(os.listdir(곳)):
            if not f.endswith(".zip"):
                continue
            rc = f[:-4]
            고 = rc고.get(rc)
            if not 고 or 고 not in 분모해.get(y, set()):
                continue
            셈["ZIP"] += 1
            try:
                미 = 인스턴스(os.path.join(곳, f))
                모 = 뽑기(os.path.join(곳, f), y, 축없음기준=기준표.get((고, y), "연결"), 미리=미)
            except Exception:                            # noqa: BLE001
                continue
            당기본.add((고, y))
            # 전기 보강(같은 ZIP 의 비교 기간 · 호출 0 — 2026-10-24 PN) — 그 회사의 전년 ZIP 이 없을 때만(있으면 그 해 당기 값이 먼저)
            if (고, y - 1) not in 당기본 and 고 in 분모해.get(y - 1, set()):
                try:
                    모전 = 뽑기(os.path.join(곳, f), y, 축없음기준=기준표.get((고, y - 1), "연결"), 기간해=y - 1, 미리=미)
                except Exception:                        # noqa: BLE001
                    모전 = {}
                기전 = "연결" if "연결" in 모전 else ("별도" if "별도" in 모전 else None)
                for 변, (v, 분자, 분모, 단위, 비고, 범위) in (보강값(모전[기전]) if 기전 else {}).items():
                    if 범위[0] <= v <= 범위[1]:
                        보강[변].append({"고유번호": 고, "회계연도": y - 1, "값": v, "분자": 분자, "분모": 분모, "단위": 단위, "기준": 기전,
                                       "원천": "주석 XBRL 접수 %s 전기 · %s" % (rc, 변), "기간끝": "%d-12-31" % (y - 1), "딱지": "같음",
                                       "비고": 비고 + " — 다음 해 ZIP 의 비교 기간"})
                        셈["전기보강"] = 셈.get("전기보강", 0) + 1
            기 = "연결" if "연결" in 모 else ("별도" if "별도" in 모 else None)
            if not 기:
                continue
            d = 모[기]
            if any(d.get(k) is not None for k in ("성격별합계", "유형총액", "평균유효세율", "유형상각")):
                셈["주석있음"] += 1
                제출.add((고, y))
                매_, 순_ = d.get("매출"), d.get("유형순액")
                if 매_ and 순_ and 매_ > 0 and 순_ / 매_ >= 설비집약:
                    집약제출.add((고, y))
            src = "주석 XBRL 접수 %s" % rc

            def 넣(변, v, 분자, 분모, 단위, 딱지, 비고, 범위, 곳줄=None):
                if v is None:
                    return
                if not (범위[0] <= v <= 범위[1]):
                    셈["정의역밖"] += 1
                    return
                (곳줄 if 곳줄 is not None else 줄[변]).append(
                    {"고유번호": 고, "회계연도": y, "값": v, "분자": 분자, "분모": 분모, "단위": 단위, "기준": 기, "원천": src + " · " + 변,
                     "기간끝": "%d-12-31" % y, "딱지": 딱지, "비고": 비고})
            매 = d.get("매출")
            # 설비계수
            합, 종, 감, 재 = d.get("성격별합계"), d.get("종업원급여"), d.get("감가상각_성격"), d.get("재고변동")
            if 합 is not None and 종 is not None and 감 is not None and 매:
                영 = d.get("영업이익")
                기준비용 = (매 - 영) if 영 is not None else None
                if 기준비용 and abs(합 - 기준비용) > 0.05 * abs(기준비용):
                    셈["성격별검증걸림"] += 1
                else:
                    순 = d.get("유형순액")
                    if not (순 and 매 > 0 and 순 / 매 >= 설비집약):
                        셈["설비집약아님"] += 1
                    else:
                        g1, g0 = d.get("기계총액"), d.get("기계총액_기초")
                        밑, 딱, 비 = None, "같음", "재료비 및 경비 ÷ 평균 기계장치 총액"
                        if g1 or g0:
                            밑 = ((g1 or g0) + (g0 or g1)) / 2.0
                        else:
                            u1, u0 = d.get("유형총액"), d.get("유형총액_기초")
                            if u1 or u0:
                                밑 = ((u1 or u0) + (u0 or u1)) / 2.0
                                딱, 비 = "[유추]", "기계장치 총액이 없어 유형자산 총액 — 건물 · 토지 포함"
                                셈["기계없어유형총액"] += 1
                        재료 = 합 - 종 - 감 - (재 or 0.0)
                        if 밑 and 밑 > 0:
                            넣("설비계수", 재료 / 밑, 재료, 밑, "배", 딱, 비 + ("" if 재 is not None else " · 재고 변동 줄 없음(0)"), (1e-6, 50.0))
            # 내용연수
            u1, 상 = d.get("유형총액"), d.get("유형상각")
            if u1 and 상 and 상 > 0:
                땅, 건 = d.get("토지총액"), d.get("건설중총액")
                밑 = u1 - (땅 or 0.0) - (건 or 0.0)
                비 = "토지 · 건설중인자산을 뺀 총액 ÷ 변동표 감가상각"
                if 땅 is None:
                    셈["토지못뺌"] += 1
                    비 = "토지 총액을 못 찾아 빼지 못함(길게 나온다) — 총액 ÷ 변동표 감가상각"
                넣("평균내용연수", 밑 / 상, 밑, 상, "년", "[유추]", 비 + " · 평균(혼합 연령)", (1.0, 100.0))
            m1, m상 = d.get("기계총액"), d.get("기계상각")
            if m1 and m상 and m상 > 0:
                넣("기계장치내용연수", m1 / m상, m1, m상, "년", "[유추]", "기계장치 총액 ÷ 기계장치 감가상각 · 평균(혼합 연령)", (1.0, 80.0))
            # 인건비율 + 검증
            if 종 is not None and 매 and 매 > 0:
                별종 = (모.get("별도") or {}).get("종업원급여")
                g = 급여총액.get((고, y))
                gv = 공.수((g or {}).get("값"))
                if gv:
                    대 = 별종 if 별종 is not None else 종
                    if 대 < 0.8 * gv:
                        셈["인건비검증걸림"] += 1
                    else:
                        넣("인건비율", 종 / 매, 종, 매, "비율", "같음", "종업원급여(%s) ÷ 매출 · 직원현황 급여총액과 대조 통과" % 기, (1e-6, 2.0))
                else:
                    셈["인건비미대조"] += 1
                    넣("인건비율", 종 / 매, 종, 매, "비율", "같음", "종업원급여(%s) ÷ 매출 · 직원현황 미대조" % 기, (1e-6, 2.0))
            # 유지율 · 유효세율
            취, u0 = d.get("유형취득"), d.get("유형총액_기초")
            if 취 is not None and u0 and u0 > 0:
                넣("유지율_취득원가", 취 / u0, 취, u0, "비율", "[유추]", "유형자산 취득 ÷ 기초 총액 — 성장분 포함(유지 CAPEX 대용)", (0.0, 3.0))
            t = d.get("평균유효세율")
            if t is not None:
                tv = t / 100.0 if abs(t) > 1.0 else t
                넣("평균유효세율_주석", tv, None, None, "비율", "[유추]", "회사가 주석에 적은 평균 유효세율", (-1.0, 1.0))
            # 보강 — 상각률(기초 순액) · 매입채무(순수)
            s0 = d.get("유형순액_기초")
            if 상 and s0 is not None:
                밑 = s0 + (d.get("유형취득") or 0.0) / 2.0
                if 밑 > 0:
                    넣("상각률_기초순액", 상 / 밑, 상, 밑, "비율", "같음", "주석 변동표 감가상각 ÷ (기초 순액 + 취득 ÷ 2) — 일괄 본표 보강", (1e-6, 2.0),
                       곳줄=보강["상각률_기초순액"])
            mp, 원 = d.get("순수매입채무"), d.get("매출원가")
            if mp is not None and 원 and 원 > 0:
                넣("매입채무회전일수", mp / 원 * 365.0, mp, 원, "일", "같음", "주석 순수 매입채무 ÷ 매출원가 × 365 — 일괄 본표 보강", (0.0, 3650.0),
                   곳줄=보강["매입채무회전일수"])
            ma, i0 = d.get("무형상각"), d.get("무형순액_기초")
            if ma and i0 is not None:
                밑 = i0 + (d.get("무형취득") or 0.0) / 2.0
                if 밑 > 0:
                    넣("무형상각률", ma / 밑, ma, 밑, "비율", "같음", "주석 무형 상각 ÷ (기초 무형자산 + 취득 ÷ 2) — 일괄 본표 보강"
                       + ("" if d.get("무형취득") is not None else " · 취득 없음(0)"), (1e-6, 2.0), 곳줄=보강["무형상각률"])
    뜻 = {"설비계수": ("(성격별 비용 합계 − 종업원급여 − 감가상각비 − 재고 변동) ÷ 평균 기계장치 총액 · 설비 집약(유형자산 순액 ÷ 매출 ≥ 0.4)만",
                    ["7k1"], "배", "같음"),
         "평균내용연수": ("(유형자산 총액 − 토지 − 건설중인자산) ÷ 유형자산 감가상각비(변동표)", ["80g(801 · 802 · 803)"], "년", "[유추]"),
         "기계장치내용연수": ("기계장치 총액 ÷ 기계장치 감가상각비(변동표)", ["80g(기계장치)"], "년", "[유추]"),
         "인건비율": ("종업원급여 ÷ 매출(성격별 주석) · 직원현황 급여총액 대조", ["520"], "비율", "같음"),
         "유지율_취득원가": ("유형자산 취득 ÷ 기초 유형자산 총액", ["850(대용)"], "비율", "[유추]"),
         "평균유효세율_주석": ("주석의 평균 유효세율(AverageEffectiveTaxRate)", ["196(대조)"], "비율", "[유추]")}
    낸 = {}
    for 변, 줄들 in 줄.items():
        정, 칸, 단, 딱 = 뜻[변]
        덮 = {(r["고유번호"], int(r["회계연도"])) for r in 줄들}
        밑 = 집약제출 if 변 == "설비계수" else 제출
        낸[변] = 공.쓰기(변, 줄들, {"정의": 정, "칸": 칸, "단위": 단, "딱지": 딱, "원천": "DART XBRL 원본 주석(fnlttXbrl.xml)", "도구": "dart_주석패널.py",
                               "적용창": "%d~%d(주석 숫자는 2023 사업연도부터 자산 규모 단계 도입)" % (부터, 까지), "검증": dict(셈),
                               "커버리지_주석제출": round(len(덮 & 밑) / len(밑), 4) if 밑 else None,
                               "주석제출_뜻": "주석 숫자를 낸 회사 · 연도%s(%d)" % (" 가운데 설비 집약" if 변 == "설비계수" else "", len(밑)),
                               "해별_주석제출": {str(y): len({k for k in 밑 if k[1] == y}) for y in range(부터, 까지 + 1)}},
                         뿌리, 분모해, 창=(부터, 까지))
        if not 조용:
            print("  %-14s 줄 %5d · 커버리지 %s(전 상장사 %d~%d) · 주석 제출 대비 %s" % (변, len(줄들), 낸[변]["커버리지_전체"], 부터, 까지,
                                                                          낸[변]["커버리지_주석제출"]), flush=True)
    for 변, 줄들 in 보강.items():
        p = os.path.join(보강자리(뿌리), "%s.csv" % 변)
        with io.open(p, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=공.머리)
            w.writeheader()
            for r in 줄들:
                w.writerow({k: 공.글(r.get(k)) if k in ("값", "분자", "분모") else ("" if r.get(k) is None else r.get(k)) for k in 공.머리})
        if not 조용:
            print("  보강 %-12s 줄 %5d → %s" % (변, len(줄들), p), flush=True)
    if not 조용:
        print("  검증 셈 %s" % json.dumps(셈, ensure_ascii=False), flush=True)
    return 낸, 셈


# ═══════════════════════════════════════════════ D — 원문 역보강(2019~2022 · 2026-10-24 PN)
#
# 주석 XBRL 은 2023 사업연도부터라 상각률(기초 순액) · 매입채무의 2015~2022 는 일괄 본표에 그 줄을 적은 회사뿐이다(상각률 해마다 약 600곳).
# 표본 — 주석 XBRL 2023 · 2024 ZIP 이 있는 회사(첫 XBRL 해의 전기에서 원문 값과 XBRL 값을 맞댈 수 있다) · 설비 집약 먼저 · 매출 큰 차례.
# 원천 — 사업보고서 원문(공용 원천 캐시 → 이 도구의 캐시 → OpenDART document.xml)의 연결 주석 「유형자산」 변동표 합계 열과 「매입채무」 줄.
# **먼저 정확도를 잰다** — 첫 XBRL 해의 전기(그 해 원문은 옛 꼴 표 — 역보강할 해들과 같은 꼴)에서 항목마다 ±1% 일치율을 내고,
# 90% 미만 항목은 역보강에 쓰지 않는다. 통과한 항목만 `_보강_원문/<변수>.csv` 에 「원문 역보강」 딱지로 남긴다(일괄 · 주석 XBRL 이 먼저).

원문계획 = {2023: (2022, 2020), 2024: (2023, 2021, 2019)}     # 첫 XBRL 해 → 받을 사업보고서 해(보고서 하나가 당기 · 전기 두 해를 준다)
일치허용, 일치문턱 = 0.01, 0.90
_변동re = {"기초": r"기초.*", "기말": r"기말.*", "상각": r"감가상각(비)?|상각(비)?",
          "취득": r"(?!.*(취득원가|사업결합|연결범위|처분|매각)).*(취득|자본적지출).*|증가"}     # 「일반취득 및 자본적지출」 꼴 · 「- 취득원가」 하위 줄은 뺀다
_흐름항목 = ("상각", "취득")


def 원문자리(뿌리=None):
    p = os.path.join(공.자리(뿌리), "_원천", "원문")
    os.makedirs(p, exist_ok=True)
    return p


def 원문보강자리(뿌리=None):
    p = os.path.join(공.자리(뿌리), "_보강_원문")
    os.makedirs(p, exist_ok=True)
    return p


def 공용원문색인():
    """{접수번호: [txt 경로 …]} — 공용 원천 캐시(`{공용}/원천/KR/<종목>/원천/사업<해>/` — dart_fetch 꼴)에 이미 받은 사업보고서."""
    낸 = {}
    for p in glob.glob(os.path.join(공.공용뿌리(), "원천", "KR", "*", "원천", "사업*", "*.txt")):
        낸.setdefault(re.split(r"[_.]", os.path.basename(p))[0], []).append(p)
    return 낸


def 원문받기(rc, 키, 뿌리=None, 열기=None, 색인=None):
    """접수번호 → ([txt 경로], 부른 수, 상태). 공용 캐시 → 이 도구의 캐시(`_원천/원문/<rc>*.txt.gz`) → OpenDART document.xml(ZIP).
    ZIP 에서는 본문과 연결 감사보고서(첨부 가운데 머리에 「연결」 이 있는 것)만 글로 옮겨 gzip 으로 둔다(XML 은 두지 않는다 — 크기)."""
    if 색인 and 색인.get(rc):
        return sorted(색인[rc]), 0, "공용 캐시"
    곳 = 원문자리(뿌리)
    있 = sorted(glob.glob(os.path.join(곳, "%s*.txt.gz" % rc)))
    if 있:
        return 있, 0, "캐시"
    if os.path.exists(os.path.join(곳, "%s.없음" % rc)):
        return [], 0, "없음(기록)"
    if not 키:
        return [], 0, "키 없음"
    b = _get("document.xml", 키, 열기, 바이트=True, rcept_no=rc)
    time.sleep(간격)
    if not b or b[:2] != b"PK":
        t = (b or b"")[:400].decode("utf-8", "replace")
        m = re.search(r"<status>(\d+)</status>|\"status\"\s*:\s*\"(\d+)\"", t)
        st = (m.group(1) or m.group(2)) if m else "ZIP 아님"
        if st in 멈춤코드:
            raise RuntimeError("OpenDART %s(%s)" % (st, 멈춤코드[st]))
        io.open(os.path.join(곳, "%s.없음" % rc), "w", encoding="utf-8").write(st)
        return [], 1, st
    from dart_fetch import _태그벗기기                         # noqa: PLC0415 — 원문 → 글은 dart_fetch 와 같은 꼴(동인원천이 읽는 꼴)
    낸 = []
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        for n in z.namelist():
            if not n.lower().endswith(".xml"):
                continue
            이름 = os.path.splitext(os.path.basename(n))[0]
            바 = z.read(n)
            글 = None
            for 인 in ("utf-8", "cp949", "euc-kr"):
                try:
                    글 = 바.decode(인)
                    break
                except UnicodeDecodeError:
                    continue
            if 글 is None:
                continue
            t = _태그벗기기(글)
            if 이름 != rc and "연결" not in t[:800]:
                continue
            p = os.path.join(곳, 이름 + ".txt.gz")
            with gzip.open(p + ".part", "wt", encoding="utf-8") as w:
                w.write(t)
            os.replace(p + ".part", p)
            낸.append(p)
    return sorted(낸), 1, "받음"


def _원문보고서(경로, 해):
    """txt(.gz) → 동인원천.보고서. 첨부(연결 감사보고서)는 머리에 「사업연도」 가 없어 종류 · 해를 목록에서 받고 전부 연결로 둔다."""
    import 동인원천 as D                                        # noqa: PLC0415
    if 경로.endswith(".gz"):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as t:
            t.write(gzip.open(경로, "rt", encoding="utf-8").read())
        try:
            b = D.보고서(t.name)
        finally:
            os.remove(t.name)
        b.경로 = 경로
    else:
        b = D.보고서(경로)
    첨부 = "_" in os.path.basename(경로)
    if 첨부 and "연결" not in " ".join(" ".join(r) for r in b.행[:40]):
        return None                                       # 별도 감사보고서 첨부 — 연결 주석이 아니다
    if 첨부 or not b.쓸만한가() or b.회계연도 != 해:
        b.종류, b.회계연도, b.개월 = "사업", 해, 12
        b.시작, b.끝 = datetime.date(해, 1, 1), datetime.date(해, 12, 31)
    if 첨부:
        b.연결 = [True] * len(b.행)
    return b


def _줄찾기(줄들, 키):
    """변동표 줄(공백 뺀 라벨, 값들) 가운데 그 키(기초 · 기말 · 상각 · 취득)의 첫 줄 번호 — 「유형자산의 …」 머리 · 「…, 유형자산」 꼬리는 떼고 본다.
    수가 없는 줄(구획 머리)은 건너뛴다."""
    for k, (l, v) in enumerate(줄들):
        if v and re.fullmatch(_변동re[키], re.sub(r",?유형자산$", "", re.sub(r"^유형자산의?", "", l))):
            return k
    return None


def _줄값(줄들, 키):
    k = _줄찾기(줄들, 키)
    return None if k is None else 줄들[k][1]


def _정리(s):
    import 동인원천 as D                                        # noqa: PLC0415
    return D.표준((s or "").replace("&cr;", ""))


def _줄들(자료):
    """표 줄 → [(라벨, 값들)] — 라벨 = 첫 수 앞의 글 칸을 모두 이은 것(「전기초 | (*)」 → 「전기초(*)」) · 수가 없는 줄은 값 [](구획 머리 —
    「취득원가」 · 「감가상각누계액」 · 「순장부금액」)."""
    import 동인원천 as D                                        # noqa: PLC0415
    낸 = []
    for r in 자료:
        k = next((i for i, c in enumerate(r) if c != "" and D.수(c) is not None), None)
        글 = [c for c in (r[:k] if k is not None else r) if c != ""]
        if 글:
            낸.append((_정리("".join(글)), [D.수(c) if c != "" else None for c in r[k:]] if k is not None else []))
    return 낸


def _문장표지(행, 번):
    """단위 줄 앞 두 줄의 설명 글에서 기간 — 글 끝의 「… (1) 당기」 가 먼저, 아니면 「(2) 당기 중 … 증감내역」 → 당 · 「(3) 전기 중 …」 → 전기.
    둘 다 있으면(「당기와 전기의 …」) None."""
    글 = " ".join(" ".join(r) for r in 행[max(0, 번 - 2):번]).replace("&cr;", " ").strip()
    m = re.search(r"(당|전)\s*\)?\s*기\s*말?\s*\)?\s*$", 글)                 # 「(1) 당기」 · 「1) 제55(당)기」 · 「(전기)」
    if m:
        return "당" if m.group(1) == "당" else "전기"
    끝줄 = " ".join(행[번 - 1]).replace("&cr;", " ").strip() if 번 >= 1 else ""
    if len(끝줄) > 100:                                            # 앞 표의 긴 주석 글(「(주1) … 전기 중 …」)로 기간을 정하지 않는다
        return None
    당, 전 = bool(re.search(r"당\s*기\s*(중|의|말|와|및|에)", 끝줄)), bool(re.search(r"전\s*기\s*(중|의|말|와|및|에)", 끝줄))
    return "당" if (당 and not 전) else ("전기" if (전 and not 당) else None)


def _맞다(합, 부분):
    return bool(부분) and abs(sum(부분) - 합) <= 0.005 * max(abs(합), 1.0)


def _구획(줄들):
    """수가 없는 구획 머리(취득원가 · 상각누계액 · 장부금액)로 줄을 가른다 → {구획: [줄]}. 구획 머리가 없으면 {None: 줄들}."""
    낸, 지금 = {}, None
    for l, v in 줄들:
        if not v:
            지금 = next((이름 for 이름 in ("원가", "누계", "장부") if re.fullmatch(_구획re[이름], l)), 지금)
            continue
        낸.setdefault(지금, []).append((l, v))
    return 낸


def _행형한(줄들, 배):
    """구획 하나의 줄 = 기초 · 취득 · 상각 · 기말, 열 = 자산 종류(맨 끝 = 합계). 합계 열은 기말 줄에서 나머지 열의 합과 맞아야 한다(±0.5%) —
    기초 · 상각 · 취득 줄도. 열이 하나뿐이면 기초 + 가운데 줄 합 = 기말(±0.5% · 상각이 양수로 적힌 꼴은 뒤집어 한 번 더)."""
    k1 = _줄찾기(줄들, "기말")
    if k1 is None:
        return None
    말 = 줄들[k1][1]
    j = max((k for k, x in enumerate(말) if x is not None), default=None)
    if j is None:
        return None

    def 칸(v):
        return v[j] if (v and len(v) > j) else None

    def 맞나(v):
        return 칸(v) is not None and _맞다(v[j], [x for x in v[:j] if x is not None])
    if any(x is not None for x in 말[:j]):                         # 여러 열 — 합계 열 맞춤
        if not 맞나(말):
            return None
        d = {}
        for 키 in ("기초", "기말", "상각", "취득"):
            v = _줄값(줄들, 키)
            if 칸(v) is not None and (키 == "기말" or 맞나(v)):          # 기초 · 상각 · 취득도 합계 열 맞춤(끝 칸이 빠진 줄의 어긋남을 거른다)
                d[키] = abs(v[j]) * 배 if 키 in _흐름항목 else v[j] * 배
        return d
    k0 = _줄찾기(줄들, "기초")                                     # 한 열 — 이월 맞춤
    if k0 is None or k0 >= k1 or 칸(줄들[k0][1]) is None:
        return None
    가운데 = [(l, 칸(v) or 0.0) for l, v in 줄들[k0 + 1:k1] if v]
    a0, a1 = 칸(줄들[k0][1]), 말[j]
    if not (_맞다(a1 - a0, [x for _, x in 가운데]) or _맞다(a1 - a0, [-abs(x) if re.fullmatch(_변동re["상각"], l) else x for l, x in 가운데])):
        return None
    d = {"기초": a0 * 배, "기말": a1 * 배}
    for 키 in _흐름항목:
        v = _줄값(줄들, 키)
        if 칸(v) is not None:
            d[키] = abs(v[j]) * 배
    return d


def _행형(줄들, 배):
    """줄 꼴 변동표 → {기초 · 기말 · 상각 · 취득} 또는 None. 취득원가 · 상각누계액 · 장부금액 구획으로 갈린 표는 장부 구획의 기초 · 기말(없으면
    취득원가 − 누계액), 누계 구획의 상각, 원가 구획의 취득을 쓴다. **순장부 표만 받는다** — 상각 줄이 없거나(취득원가 표) 기말이 0 이하(누계액 표)면 버린다."""
    구 = _구획(줄들)
    if set(구) - {None}:
        장, 원, 누 = (_행형한(구.get(k) or [], 배) or {} for k in ("장부", "원가", "누계"))
        d = {k: 장[k] for k in ("기초", "기말") if 장.get(k) is not None}
        for k in ("기초", "기말"):
            if k not in d and 원.get(k) is not None and 누.get(k) is not None:
                d[k] = 원[k] - abs(누[k])
        상 = 누.get("상각") or 장.get("상각")
        취 = 원.get("취득") or 장.get("취득")
        if 상:
            d["상각"] = 상
        if 취:
            d["취득"] = 취
    else:
        d = _행형한(줄들, 배) or {}
    return d if (d.get("상각") and (d.get("기말") or 0) > 0) else None


_열re = {"기초": r"(당|전)?기초.*", "기말": r"(당|전)?기말.*", "상각": _변동re["상각"] + r"|감가상각비?\(.*\)", "취득": _변동re["취득"]}
_구획re = {"원가": r".*취득원가.*", "누계": r".*(상각|손상).*누계액.*", "장부": r".*장부금액.*"}
_합계re = r"(합계|총계|계)(\(\*\d*\))?"


def _열이름들(머리, n):
    """머리줄들 → 값 칸 n 개의 이름. 이름 칸이 가장 많은 머리줄에서 첫 칸(구분)을 빼고, 둘로 갈린 이름(「취득 및 | 자본적지출」)을 잇고, 오른쪽에서 n 개."""
    best = []
    for r in 머리:
        이름 = [_정리(c) for c in r if c != ""]
        if len(이름) > len(best):
            best = 이름
    if best and re.fullmatch(r"구분|과목|계정과목", best[0]):
        best = best[1:]
    if len(best) < n:                                              # 머리가 여러 줄로 갈린 표(「… 환율변동 | 1029호 효과 | 기타 · 기말금액」) — 줄을 이어 본다
        flat = [_정리(c) for r in 머리 for c in r if c != ""]
        if flat and re.fullmatch(r"구분|과목|계정과목", flat[0]):
            flat = flat[1:]
        if len(flat) >= n:
            best = flat
    k = 0
    while len(best) > n and k < len(best) - 1:
        if best[k].endswith(("및", "/", "·")) or best[k + 1].startswith(("(", "포함")):
            best[k:k + 2] = [best[k] + best[k + 1]]
        else:
            k += 1
    return best[-n:] if len(best) >= n else [""] * (n - len(best)) + best


def _열형(줄들, 열들, 배):
    """줄 = 자산 종류(합계 줄 하나), 열 = 기초 · 취득 · … · 상각 · 기말(국내 「증감내역」 표의 흔한 꼴). 합계 줄은 기말 열이 다른 줄의 합과 맞거나
    (±0.5%) 기초 + 가운데 열 합 = 기말일 때만. 줄이 취득원가 · 상각누계액 · 장부금액 구획으로 갈린 표는 장부금액 구획만 본다(없으면 읽지 않는다)."""
    이름 = [re.sub(r",?유형자산$", "", re.sub(r"^유형자산의?", "", _정리(x))) for x in 열들]
    자리 = {키: next((k for k, x in enumerate(이름) if re.fullmatch(_열re[키], x)), None) for 키 in ("기초", "기말", "상각", "취득")}
    날 = sorted((m.groups(), k) for k, m in ((k, re.match(_날장부re, x)) for k, x in enumerate(이름)) if m)
    if (자리["기초"] is None or 자리["기말"] is None) and len(날) >= 2:     # 「2019.1.1 장부가액 … 2019.12.31 장부가액」 꼴
        자리["기초"], 자리["기말"] = 날[0][1], 날[-1][1]
    i0, i1 = 자리["기초"], 자리["기말"]
    if i0 is None or i1 is None or i1 <= i0:
        return None
    if any(not v and re.fullmatch(_구획re["원가"] + "|" + _구획re["누계"], l) for l, v in 줄들):
        k장 = next((k for k, (l, v) in enumerate(줄들) if not v and re.fullmatch(_구획re["장부"], l)), None)
        if k장 is None:
            return None
        뒤 = 줄들[k장 + 1:]
        끝 = next((k for k, (l, v) in enumerate(뒤) if not v), len(뒤))
        줄들 = 뒤[:끝]
    n = len(이름)
    합k = next((k for k, (l, v) in enumerate(줄들) if v and re.fullmatch(_합계re, l)), None)
    if 합k is None:
        합k = next((k for k, (l, v) in enumerate(줄들) if v and re.fullmatch(r"소계(\(\*\d*\))?", l)), None)
    if 합k is None:
        return None

    def 펴(v):
        return list(v[-n:]) if len(v) >= n else [None] * (n - len(v)) + list(v)
    합 = 펴(줄들[합k][1])
    if 합[i0] is None or 합[i1] is None:
        return None
    나머지 = [펴(v)[i1] for k, (l, v) in enumerate(줄들) if k < 합k and v and not re.fullmatch(r"(소계|합계|총계|계)(\(\*\d*\))?", l)]
    if not (_맞다(합[i1], [x for x in 나머지 if x is not None]) or _맞다(합[i1] - 합[i0], [x for x in 합[i0 + 1:i1] if x is not None])):
        return None
    d = {"기초": 합[i0] * 배, "기말": 합[i1] * 배}
    for 키 in _흐름항목:
        k = 자리[키]
        if k is not None and i0 < k < i1 and 합[k] is not None:
            d[키] = abs(합[k]) * 배
    return d if (d.get("상각") and d["기말"] > 0) else None             # 순장부 표만(상각 열이 없는 취득원가 표 · 누계액 표는 버린다)


_마커re = r"(전기초|전기말|당기초|당기말)(\(\*\d*\))*"
_날장부re = r"(\d{4})\.(\d{1,2})\.(\d{1,2}).*장부(가액|금액)"


def _기간형(줄들, 배):
    """한 표에 두 해가 이어 적힌 꼴 — 구획(취득원가 · 상각누계액 · 순장부금액)마다 전기초 → (변동) → 전기말 · 당기초 → (변동) → 당기말.
    → {"당": {…}, "전기": {…}} 또는 None. 합계 열 = 당기말 줄의 맨 끝 수 열이고 나머지 열의 합과 맞아야 한다(±0.5%).
    장부금액은 순장부 구획이 있으면 그 값, 없으면 취득원가 − 누계액. 상각 = 누계 구획의 감가상각 줄, 취득 = 원가 구획의 취득 줄(그 기간 안)."""
    if not any(v and re.fullmatch(_마커re, l) for l, v in 줄들):
        return None
    구획, 기간 = "장부", None
    값 = {"원가": {}, "누계": {}, "장부": {}}
    흐 = {"당": {}, "전기": {}}
    j = None
    for l, v in 줄들:
        if not v:
            for 이름 in ("원가", "누계", "장부"):
                if re.fullmatch(_구획re[이름], l):
                    구획, 기간 = 이름, None
            continue
        m = re.fullmatch(_마커re, l)
        if m:
            값[구획][m.group(1)] = v
            기간 = {"전기초": "전기", "당기초": "당"}.get(m.group(1))
            if m.group(1) == "당기말" and j is None:
                j = max((k for k, x in enumerate(v) if x is not None), default=None)
            continue
        if 기간 and 구획 == "누계" and re.fullmatch(_변동re["상각"], l):
            흐[기간].setdefault("상각", v)
        if 기간 and 구획 in ("원가", "장부") and re.fullmatch(_변동re["취득"], l):
            흐[기간].setdefault("취득", v)
    if j is None:
        return None

    def 칸(v):
        return v[j] if (v and len(v) > j and v[j] is not None) else None

    def 순(마):
        if 칸(값["장부"].get(마)) is not None:
            return 칸(값["장부"][마])
        a, b = 칸(값["원가"].get(마)), 칸(값["누계"].get(마))
        return (a - abs(b)) if (a is not None and b is not None) else None
    말 = 값["장부"].get("당기말") or 값["원가"].get("당기말")
    if not (말 and 칸(말) is not None and _맞다(말[j], [x for x in 말[:j] if x is not None])):
        return None
    낸 = {}
    for 표지, 초, 끝 in (("당", ("당기초", "전기말"), "당기말"), ("전기", ("전기초",), "전기말")):
        d = {}
        a1 = 순(끝)
        a0 = next((x for x in (순(마) for 마 in 초) if x is not None), None)
        if a1 is not None:
            d["기말"] = a1 * 배
        if a0 is not None:
            d["기초"] = a0 * 배
        for 키 in _흐름항목:
            if 칸(흐[표지].get(키)) is not None:
                d[키] = abs(칸(흐[표지][키])) * 배
        if d.get("기말") and d["기말"] > 0 and d.get("상각"):
            낸[표지] = d
    return 낸 or None


def 유형합계읽기(보):
    """연결 주석 「유형자산」 변동표의 합계 → {해: {기초 · 기말 · 상각 · 취득}}(원). 세 꼴을 읽는다 — 줄이 기초 · 취득 · 상각 · 기말인 표(`_행형`) ·
    열이 그런 표(`_열형` — 「증감내역」) · 두 해가 구획마다 이어 적힌 표(`_기간형` — 전기초 … 당기말). 어느 꼴이든 합계가 나머지의 합 또는
    이월(기초 + 변동 = 기말)과 맞을 때만 받고(±0.5%), 한 해에 맞는 표가 여럿이면 기말이 가장 큰 표(유형자산 전체 — 리스 · 담보 · 부문 같은
    부분 표가 아닌)를 쓴다. 블록은 그 주석 안에서만(다음 주석 머리 「8. 사용권자산 …」 전까지)."""
    import 동인원천 as D                                        # noqa: PLC0415
    후보 = {}
    시작들 = sorted({i for i in range(len(보.행)) if 보.연결[i] and D._주석머리(보.행[i]) and re.search(r"유형자산", 보.행[i][0])
                    and not re.search(r"무형|사용권|투자부동산|처분|손상|매각", 보.행[i][0])}
                   | set(D.연결머리(보, r"유형자산.{0,12}(장부금액|세부\s*정보|변동|증감|금액)")))   # 주석 머리가 두 칸 줄인 원문(「10. 유형자산 | :」)도
    본 = set()
    for i0 in 시작들:
        끝 = next((i for i in range(i0 + 1, min(len(보.행), i0 + 3000)) if any(re.match(r"^\s*\d{1,2}\.\s*[가-힣]", c or "") and "유형자산" not in (c or "")
                                                                         for c in 보.행[i][:1])), len(보.행))
        블들 = [b for b in D.블록들(보.행, i0, 최대=3000) if b[4] not in 본 and b[4] < 끝]
        블들 = [(b[0] or _문장표지(보.행, b[4]),) + tuple(b[1:]) for b in 블들]
        해석 = []                                                # [표지, 읽은 값, 블록 번호] — 한 해 표
        for 표지, u, 머리, 자료, 번 in 블들:
            if 번 in 본 or D.단위배.get(u) is None:
                continue
            배 = D.단위배[u]
            줄들 = _줄들(자료)
            두해 = _기간형(줄들, 배)
            if 두해:
                for 표, d in 두해.items():
                    후보.setdefault(보.회계연도 - (0 if 표 == "당" else 1), []).append(d)
                본.add(번)
                continue
            n = max((len(v) for _, v in 줄들), default=0)
            이름 = _열이름들(머리, n) if n else []
            d = _행형(줄들, 배) or (_열형(줄들, 이름, 배) if n else None)
            if not (d and d.get("기말")):
                continue
            if 표지 is None:                                       # 열 머리의 「당기말」 · 「전기초」 따위 · 「2019.12.31 장부가액」 의 해
                m = next((m for m in (re.match(r"(당|전)기(초|말)", x) for x in 이름) if m), None)
                날 = [int(m2.group(1)) for m2 in (re.match(_날장부re, x) for x in 이름) if m2 and m2.group(2) == "12"]
                표지 = ("당" if m.group(1) == "당" else "전기") if m else (
                    {보.회계연도: "당", 보.회계연도 - 1: "전기"}.get(max(날)) if 날 else None)
            해석.append([표지, d, 번])
        고리 = set()
        for A in 해석:                                           # 이월 고리 — 당기 표의 기초 = 전기 표의 기말(±0.5%) · 글로 읽은 표지보다 먼저
            for B in 해석:
                if A is not B and id(A) not in 고리 and id(B) not in 고리 and A[1].get("기초") and _맞다(A[1]["기초"], [B[1]["기말"]]):
                    A[0], B[0] = "당", "전기"
                    고리 |= {id(A), id(B)}
        남 = [x for x in 해석 if x[0] is None]
        if len(남) == 2 and len(해석) == 2:                       # 고리가 없고 표지 없는 한 해 표가 꼭 둘이면 차례대로 당기 · 전기(국내 주석의 관례)
            남[0][0], 남[1][0] = "당", "전기"
        for 표지, d, 번 in 해석:
            if 표지 in ("당", "전기"):
                본.add(번)
                후보.setdefault(보.회계연도 - (0 if 표지 == "당" else 1), []).append(d)
    return {t: max(ds, key=lambda d: abs(d["기말"])) for t, ds in 후보.items()}


def 매입채무읽기(보):
    """연결 주석 「매입채무」 머리 아래 표의 「매입채무」 줄 첫 수(유동 · 표지 블록) → {해: 원}. 표지가 없는 표는 열 머리의 당기 · 전기 표지로.
    주석에 없으면 연결재무상태표 본문의 「매입채무」 줄(주석 번호 칸 · 1,000 미만 수는 뺀 첫 수 = 당기말 · 둘째 = 전기말)."""
    import 동인원천 as D                                        # noqa: PLC0415
    낸 = {}
    시작들 = [i for i in range(len(보.행)) if 보.연결[i] and D._주석머리(보.행[i]) and re.search(r"매입채무", 보.행[i][0])]
    for i0 in 시작들:
        for 표지, u, 머리, 자료, _ in D.블록들(보.행, i0, 최대=400):
            배 = D.단위배.get(u)
            if 배 is None:
                continue
            for r in 자료:
                l, v = D.줄라벨값(r)
                if not l or not re.fullmatch(r"매입채무(\(\*\d*\))?", D.표준(l)):
                    continue
                if 표지 in ("당", "전기"):
                    x = next((x for x in v if x), None)                 # 「-」(0) 칸을 건너뛴 첫 수(유동)
                    if x is not None:
                        낸.setdefault(보.회계연도 - (0 if 표지 == "당" else 1), x * 배)
                else:
                    for 이름, x in zip(D.열이름(머리, len(v)), v):
                        t = D.표지읽기(이름)
                        if t in ("당", "전기") and x is not None:
                            낸.setdefault(보.회계연도 - (0 if t == "당" else 1), x * 배)
                break
    if not 낸:
        i = next((i for i in range(len(보.행)) if 보.연결[i] and re.search(r"연\s*결\s*재\s*무\s*상\s*태\s*표", " ".join(보.행[i][:2]))
                  and not re.search(r"주\s*석", " ".join(보.행[i][:2]))), None)
        if i is not None:
            u = next((D.단위읽기(보.행[k]) for k in range(i, min(i + 12, len(보.행))) if D.단위읽기(보.행[k])), None)
            배 = D.단위배.get(u)
            for r in 보.행[i + 1:i + 400] if 배 else []:
                if re.search(r"손\s*익\s*계\s*산\s*서", " ".join(r[:1])):
                    break
                l, v = D.줄라벨값(r)
                if l and re.fullmatch(r"(\d{1,2}\.|[ⅠⅡⅢⅣⅤ]\.)?매입채무(\(주\d+\))?", D.표준(l)):
                    수들 = [x for x in v if x is not None and (abs(x) >= 1000 or x == 0)]
                    for k, x in enumerate(수들[:2]):
                        낸[보.회계연도 - k] = x * 배
                    break
    return 낸


def 원문읽기(경로들, 해):
    """한 사업보고서(본문 + 연결 감사보고서) → {해: {기초 · 기말 · 상각 · 취득 · 매입채무}}. 연결 감사보고서를 먼저 읽는다(본문 주석이 별도뿐인 회사)."""
    낸, 유 = {}, {}
    for p in sorted(경로들, key=lambda x: (0 if "_" in os.path.basename(x) else 1)):
        try:
            보 = _원문보고서(p, 해)
        except Exception:                                   # noqa: BLE001
            continue
        if 보 is None:
            continue
        for t, d in 유형합계읽기(보).items():
            if t not in 유 or abs(d["기말"]) > abs(유[t]["기말"]):   # 파일끼리도 기말이 큰 표(유형자산 전체)
                유[t] = d
        for t, v in 매입채무읽기(보).items():
            낸.setdefault(t, {}).setdefault("매입채무", v)
    for t, d in 유.items():
        낸.setdefault(t, {}).update(d)
    return 낸


def 원문표본(뿌리=None, 수=600, 부터=2019, 까지=2022):
    """[(고유번호, 첫 XBRL 해, ZIP 경로, XBRL 기준)] — 주석 XBRL 2023 · 2024 ZIP 이 있는 분모 회사 가운데 창(부터~까지)에 상각률 · 매입채무가 빈 해가
    있는 곳. 차례: 설비 집약(유형자산 순액 ÷ 매출 ≥ 0.4) → 매출 큰 곳."""
    분 = 공.분모(뿌리, range(부터, 까지 + 1))
    있상, 있매 = set(공.읽기("상각률_기초순액", 뿌리)), set(공.읽기("매입채무회전일수", 뿌리))
    후보, 본 = [], set()
    for y in sorted(원문계획):
        곳 = os.path.join(공.자리(뿌리), "_원천", "주석XBRL", str(y))
        목p = os.path.join(곳, "목록.json")
        if not os.path.exists(목p):
            continue
        rc고 = {v: k for k, v in json.load(io.open(목p, encoding="utf-8")).items()}
        for f in sorted(os.listdir(곳)):
            고 = rc고.get(f[:-4]) if f.endswith(".zip") else None
            if not 고 or 고 in 본 or not any(고 in 분.get(t, set()) for t in range(부터, 까지 + 1)):
                continue
            빈 = sum(1 for t in range(부터, 까지 + 1) if 고 in 분.get(t, set()) and ((고, t) not in 있상 or (고, t) not in 있매))
            if not 빈:
                continue
            try:
                모 = 뽑기(os.path.join(곳, f), y)
            except Exception:                               # noqa: BLE001
                continue
            기 = "연결" if "연결" in 모 else ("별도" if "별도" in 모 else None)
            if not 기:
                continue
            본.add(고)
            매, 순 = 모[기].get("매출"), 모[기].get("유형순액")
            집약 = bool(매 and 순 and 매 > 0 and 순 / 매 >= 설비집약)
            후보.append((not 집약, -(매 or 0.0), 고, y, os.path.join(곳, f), 기))
    후보.sort()
    return [(고, y, zp, 기) for _, _, 고, y, zp, 기 in 후보[:수]]


def 역보강(뿌리=None, 부터=2019, 까지=2022, 수=600, 상한=2000, 키=None, 열기=None, 받기=True, 조용=False):
    """D 단계 — 표본의 사업보고서 원문을 받아(받기) 읽고, 정확도를 잰 뒤 통과 항목만 `_보강_원문/` 에 쓴다. → 상태 dict(목록 「이어받기.원문역보강」 에도)."""
    키 = (키 or os.environ.get("OPENDART_API_KEY")) if 받기 else None
    시 = time.time()
    표본 = 원문표본(뿌리, 수, 부터, 까지)
    색인 = 공용원문색인()
    부른, 까닭 = 0, ("다 받음" if 받기 else "받지 않음(캐시만)")
    셈 = {"표본": len(표본), "보고서": 0, "공용 캐시": 0, "캐시": 0, "받음": 0, "없음": 0, "목록에없음": 0, "읽은해": 0}
    목록 = {}
    값들 = {}                                                    # 고 → {해: {항목: 값}}
    try:
        for 해 in sorted({h for 계 in 원문계획.values() for h in 계}):
            if 받기:
                목록[해], n = 목록받기(해, 키, 뿌리, 열기)
                부른 += n
            else:
                p = os.path.join(원천자리(뿌리, 해), "목록.json")
                목록[해] = json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else {}
        for i, (고, y, zp, 기) in enumerate(표본):
            for 해 in 원문계획[y]:
                rc = 목록.get(해, {}).get(고)
                if not rc:
                    셈["목록에없음"] += 1
                    continue
                if 받기 and 부른 >= 상한:
                    까닭 = "상한 %d 에 닿음" % 상한
                    raise StopIteration
                경로들, n, st = 원문받기(rc, 키, 뿌리, 열기, 색인)
                부른 += n
                셈["보고서"] += 1
                셈[st if st in 셈 else "없음"] += 1
                for t, d in 원문읽기(경로들, 해).items():
                    셈["읽은해"] += 1
                    옛 = 값들.setdefault(고, {}).setdefault(t, {})
                    for k, v in d.items():
                        if t == 해 or k not in 옛:                  # 그 해의 당기 표가 다음 해 보고서의 전기 표보다 먼저
                            옛[k] = v
            if not 조용 and (i + 1) % 50 == 0:
                print("  원문 %d/%d — 부름 %d · %s · %.0f초" % (i + 1, len(표본), 부른, json.dumps(셈, ensure_ascii=False), time.time() - 시), flush=True)
    except StopIteration:
        pass
    except RuntimeError as e:
        까닭 = "%s — 멈춤" % e
    # 정확도 — 첫 XBRL 해의 전기(t0 = y − 1): 원문(옛 꼴 · 그 해 당기 표) ↔ XBRL(같은 ZIP 의 비교 기간)
    짝 = {"상각": "유형상각", "취득": "유형취득", "기말": "유형순액", "기초": "유형순액_기초", "매입채무": "순수매입채무"}
    맞댐 = {k: {"n": 0, "일치": 0, "어긋남": []} for k in 짝}
    for 고, y, zp, 기 in 표본:
        t0 = y - 1
        원 = (값들.get(고) or {}).get(t0)
        if not 원:
            continue
        try:
            x = 뽑기(zp, y, 기간해=t0).get(기) or {}
        except Exception:                                   # noqa: BLE001
            continue
        for k, xk in 짝.items():
            a, b = 원.get(k), x.get(xk)
            if a is None or not b:
                continue
            m = 맞댐[k]
            m["n"] += 1
            if abs(a - b) <= 일치허용 * abs(b):
                m["일치"] += 1
            elif len(m["어긋남"]) < 12:
                m["어긋남"].append({"고유번호": 고, "해": t0, "원문": a, "XBRL": b, "비": round(a / b, 4)})
    for m in 맞댐.values():
        m["일치율"] = round(m["일치"] / m["n"], 4) if m["n"] else None
        m["통과"] = bool(m["n"] >= 30 and m["일치율"] >= 일치문턱)
    통 = {k for k, m in 맞댐.items() if m["통과"]}
    # 쓰기 — 통과한 항목만 · 창(부터~까지) · 정의는 일괄 · 주석과 같다
    원가 = 공.읽기("매출원가율", 뿌리)
    기준 = {고: 기 for 고, _, _, 기 in 표본}
    줄 = {"상각률_기초순액": [], "매입채무회전일수": []}
    for 고, 해들 in 값들.items():
        for t, d in sorted(해들.items()):
            if not (부터 <= t <= 까지):
                continue
            상, 초 = d.get("상각"), d.get("기초")
            if 초 is None and "기말" in 통:
                초 = (해들.get(t - 1) or {}).get("기말")
            if {"상각", "기초"} <= 통 and 상 and 초 is not None:
                취 = d.get("취득") if "취득" in 통 else None
                밑 = 초 + (취 or 0.0) / 2.0
                v = 상 / 밑 if 밑 > 0 else None
                if v is not None and 1e-6 <= v <= 2.0:
                    줄["상각률_기초순액"].append({"고유번호": 고, "회계연도": t, "값": v, "분자": 상, "분모": 밑, "단위": "비율", "기준": 기준.get(고),
                                         "원천": "사업보고서 원문 %d · 상각률_기초순액" % t, "기간끝": "%d-12-31" % t, "딱지": "원문 역보강",
                                         "비고": "정의 같음 — 연결 주석 유형자산 변동표 합계 열(감가상각 ÷ (기초 + 취득 ÷ 2))"
                                                 + ("" if 취 is not None else " · 취득 줄 없음(0)")})
            mp, r = d.get("매입채무"), 원가.get((고, t))
            c = 공.수((r or {}).get("분자"))
            if "매입채무" in 통 and mp is not None and c and c > 0 and ((r or {}).get("기준") or 기준.get(고)) == 기준.get(고):
                v = mp / c * 365.0
                if 0.0 <= v <= 3650.0:
                    줄["매입채무회전일수"].append({"고유번호": 고, "회계연도": t, "값": v, "분자": mp, "분모": c, "단위": "일", "기준": 기준.get(고),
                                          "원천": "사업보고서 원문 %d · 매입채무회전일수" % t, "기간끝": "%d-12-31" % t, "딱지": "원문 역보강",
                                          "비고": "정의 같음 — 원문 주석 매입채무 ÷ 일괄 매출원가 × 365"})
    for 변, 줄들 in 줄.items():
        p = os.path.join(원문보강자리(뿌리), "%s.csv" % 변)
        with io.open(p + ".part", "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=공.머리)
            w.writeheader()
            for r in sorted(줄들, key=lambda r: (r["고유번호"], r["회계연도"])):
                w.writerow({k: 공.글(r.get(k)) if k in ("값", "분자", "분모") else ("" if r.get(k) is None else r.get(k)) for k in 공.머리})
        os.replace(p + ".part", p)
    상태 = {"마지막실행": 공.지금(), "부른수": 부른, "멈춘까닭": 까닭, "창": "%d~%d" % (부터, 까지), "셈": 셈, "정확도": 맞댐,
          "일치": "±%.0f%% · 문턱 %.0f%% · n ≥ 30" % (일치허용 * 100, 일치문턱 * 100), "통과항목": sorted(통),
          "줄": {k: len(v) for k, v in 줄.items()}, "걸린초": round(time.time() - 시, 1),
          "원천": "사업보고서 원문(공용 원천 캐시 · OpenDART document.xml) — 연결 주석 유형자산 변동표 합계 열 · 매입채무 줄"}
    io.open(os.path.join(원문자리(뿌리), "정확도.json"), "w", encoding="utf-8").write(json.dumps(상태, ensure_ascii=False, indent=1))
    공.목록고치기(뿌리, 이어=("원문역보강", 상태))
    return 상태


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="국내 주석 XBRL 패널(C — 2023~2025) · 원문 역보강(D — 2019~2022)")
    ap.add_argument("--부터", type=int, default=None, help="기본 2023(주석) · 2019(원문역보강)")
    ap.add_argument("--까지", type=int, default=None, help="기본 2025(주석) · 2022(원문역보강)")
    ap.add_argument("--상한", type=int, default=None, help="하루 호출 상한 — 기본 4000(주석) · 2000(원문역보강)")
    ap.add_argument("--짓기만", action="store_true")
    ap.add_argument("--원문역보강", action="store_true", help="D 단계 — 사업보고서 원문 표로 2019~2022 상각률 · 매입채무(정확도 먼저)")
    ap.add_argument("--표본", type=int, default=600)
    a = ap.parse_args(argv)
    if a.원문역보강:
        if not a.짓기만 and not os.environ.get("OPENDART_API_KEY"):
            print("입력 오류 — 환경변수 OPENDART_API_KEY 가 없다")
            return 2
        상 = 역보강(None, a.부터 or 2019, a.까지 or 2022, a.표본, a.상한 or 2000, 받기=not a.짓기만)
        print("원문 역보강 — 부름 %d · %s · 통과 %s · 줄 %s · %.0f초" % (상["부른수"], 상["멈춘까닭"], 상["통과항목"], 상["줄"], 상["걸린초"]))
        for k, m in 상["정확도"].items():
            print("  정확도 %-6s n %4d · 일치 %s" % (k, m["n"], m["일치율"]))
        print("→ %s · `dart_상세변수.py` 를 다시 돌려 합친다" % 원문보강자리())
        return 0
    a.부터, a.까지, a.상한 = a.부터 or 2023, a.까지 or 2025, a.상한 or 4000
    if not a.짓기만:
        if not os.environ.get("OPENDART_API_KEY"):
            print("입력 오류 — 환경변수 OPENDART_API_KEY 가 없다")
            return 2
        상 = 받기(None, a.부터, a.까지, a.상한)
        print("주석 받기 — 부름 %d · ZIP %d · 없음 %d · %s · %.0f초" % (상["부른수"], 상.get("받은ZIP", 0), 상.get("ZIP없음", 0), 상["멈춘까닭"], 상.get("걸린초", 0)))
    짓기(None, a.부터, a.까지)
    print("→ %s" % 공.자리())
    return 0


if __name__ == "__main__":
    sys.exit(main())

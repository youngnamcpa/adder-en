# -*- coding: utf-8 -*-
"""dart_상세변수 — 받아 둔 「재무정보 일괄다운로드」 본표(BS · PL · CF)와 주요계정에서 근거 표 공백 칸의 국내 패널 변수를 짓는다 (2026-10-24 PK · A 단계).

새 호출이 없다 — 공용 캐시 `{기저율}/일괄/{연도}_4Q_{표}.zip`(dart_일괄패널.py 가 받은 것)과 `{기저율}/주요계정_{연도}.csv` 만 읽는다.
출력 꼴은 `상세변수공통` 의 계약(`{기저율}/KR/상세변수/<변수>.csv` · `목록.json`).

    변수(모델 칸)                     정의                                                         딱지
    유효세율_1년(196 대조)            법인세비용 ÷ 법인세비용차감전순이익(세전 > 0 · |율| ≤ 1)              [유추] 분모 세전이익 · 실현 세율
    유효세율_3년(196 대조)            Σ법인세비용 ÷ Σ세전이익(t−2 ~ t · 세 해 모두 · Σ세전 > 0)          [유추] 같음
    현금세율_3년(196 대조)            Σ법인세 납부(CF · 지급을 양수로) ÷ Σ세전이익(t−2 ~ t)              [유추] 현금 기준
    영업이익률_5년평균(213 · 영구열)    영업이익 ÷ 매출(주요계정)의 t−4 ~ t 평균(다섯 해 모두)             [유추] 정상 상태 대 실현 5년 평균
    매출원가율(80 꼴)                 매출원가 ÷ 매출액                                            같음(원가 줄이 매출원가 전체일 때)
    판관비율(80 꼴)                   판매비와관리비 ÷ 매출액                                       같음(원가 줄이 판관비 전체일 때)
    매입채무회전일수(186)             순수 매입채무(기말) ÷ 매출원가 × 365 — 「매입채무 및 기타채무」 한 줄 회사는 넣지 않는다     같음(기준 매출원가)
    재고회전일수_원가(182)            재고자산(기말) ÷ 매출원가 × 365                                같음(기준 매출원가)
    상각률_기초순액(156)              유형자산 감가상각비 ÷ (기초 유형자산 순액 + 유형자산 취득(CF) ÷ 2)     같음(상각 + 무형 섞인 줄이면 [유추])
    무형상각률(164)                  무형자산상각비(CF) ÷ (기초 무형자산 + 무형자산 취득(CF) ÷ 2)            같음(13번 원천 18 · 78 · 81 행 코드 · 2026-10-24 PN)

읽는 규칙 — 일괄다운로드 그대로(as filed)
  ① 2015~2018 항목코드 접두 `ifrs_` 를 `ifrs-full_` 로 읽는다(안 그러면 그 네 해가 통째로 빈다 — P2 실측 4 → 1,784곳)
  ② 금융 파일(이름에 금융기타 · 보험 · 은행 · 증권)은 읽지 않고, 기저율 제외 산업(64~66 · 68)은 쓰지 않는다
  ③ 회사 · 연도마다 연결이 있으면 연결만, 없으면 별도만(섞지 않는다 — `기준` 열)
  ④ 감가상각비는 CF 조정 줄의 표준 코드(AdjustmentsForDepreciationExpense …)를 먼저, 없으면 회사 고유 코드의 항목명이 「감가상각비」인 줄(무형 · 사용권 ·
     투자부동산 제외). 감가상각과 무형 상각이 한 줄이면 딱지 [유추]
  ⑤ 비율이 정의역 밖이면 쓰지 않는다(세율 |율| > 1 · 원가율 ≤ 0 또는 > 3 · 일수 < 0 또는 > 3,650 · 상각률 ≤ 0 또는 > 2) — 뺀 수는 목록에 남는다

    python 스크립트/dart_상세변수.py [--부터 2015] [--까지 2025] [--변수 유효세율_3년,…]
종료 코드 — 0 통과 · 2 입력 오류(일괄 ZIP · 주요계정이 없음). 회사 · 업종 이름은 이 도구에 없다(범용).
"""
from __future__ import annotations

import argparse
import csv
import io
import os
import re
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass
여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
import 상세변수공통 as 공  # noqa: E402

금융낱말 = ("금융기타", "보험", "은행", "증권")

# 항목 → (표, [코드 …]) — 앞의 코드가 먼저. 코드는 접두 정규화(ifrs_ → ifrs-full_) 뒤에 맞댄다
항목 = {
    "매출액": ("PL", ["ifrs-full_Revenue", "ifrs-full_RevenueFromContractsWithCustomers", "dart_Revenue", "ifrs-full_RevenueFromSaleOfGoods", "dart_OperatingRevenue"]),
    "매출원가": ("PL", ["ifrs-full_CostOfSales", "dart_CostOfSales", "ifrs-full_CostOfMerchandiseSold"]),
    "판관비": ("PL", ["dart_TotalSellingGeneralAdministrativeExpenses", "ifrs-full_SellingGeneralAndAdministrativeExpense"]),
    "영업이익": ("PL", ["dart_OperatingIncomeLoss", "ifrs-full_ProfitLossFromOperatingActivities"]),
    "세전이익": ("PL", ["ifrs-full_ProfitLossBeforeTax", "dart_ProfitLossBeforeTax"]),
    "법인세비용": ("PL", ["ifrs-full_IncomeTaxExpenseContinuingOperations", "dart_IncomeTaxExpense"]),
    "유형자산": ("BS", ["ifrs-full_PropertyPlantAndEquipment"]),
    "재고자산": ("BS", ["ifrs-full_Inventories", "ifrs-full_InventoriesTotal"]),
    "순수매입채무": ("BS", ["dart_ShortTermTradePayables", "ifrs-full_TradeAndOtherCurrentPayablesToTradeSuppliers", "ifrs-full_CurrentTradePayables",
                       "ifrs-full_TradePayables"]),
    "유형취득": ("CF", ["ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities", "dart_PurchaseOfPropertyPlantAndEquipment",
                     "ifrs-full_PurchaseOfPropertyPlantAndEquipment"]),
    "감가상각비": ("CF", ["ifrs-full_AdjustmentsForDepreciationExpense", "dart_AdjustmentsForDepreciationExpense",
                      "ifrs-full_DepreciationExpense", "ifrs-full_DepreciationPropertyPlantAndEquipment",
                      "ifrs-full_AdjustmentsForDepreciationAndAmortisationExpense", "ifrs-full_DepreciationAndAmortisationExpense"]),
    "법인세납부": ("CF", ["ifrs-full_IncomeTaxesPaidRefundClassifiedAsOperatingActivities", "ifrs-full_IncomeTaxesPaidClassifiedAsOperatingActivities",
                      "ifrs-full_IncomeTaxesPaidRefund", "dart_IncomeTaxesPaid"]),
    # 무형 — 모델 13번 원천 18 · 78 · 81 행과 같은 코드(dart_원천.py) · 엔진 164 의 밑(투자.py x20) · 2026-10-24 PN
    "무형자산": ("BS", ["ifrs-full_IntangibleAssetsAndGoodwill", "ifrs-full_IntangibleAssetsOtherThanGoodwill"]),
    "무형상각비": ("CF", ["ifrs-full_AdjustmentsForAmortisationExpense", "ifrs-full_AmortisationExpense", "dart_AdjustmentsForAmortisationExpense"]),
    "무형취득": ("CF", ["ifrs-full_PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities", "dart_PurchaseOfIntangibleAssets",
                     "ifrs-full_PurchaseOfIntangibleAssets"]),
}
상각섞임코드 = ("ifrs-full_AdjustmentsForDepreciationAndAmortisationExpense", "ifrs-full_DepreciationAndAmortisationExpense")
_감가이름 = re.compile(r"^\s*(유형자산\s*)?감가상각비\s*$")
_순수채무이름 = re.compile(r"^\s*(유동\s*|단기\s*)?매입채무\s*$")
_무형상각이름 = re.compile(r"^\s*무형자산\s*상각비\s*$")
_무형취득이름 = re.compile(r"^\s*무형자산의?\s*취득\s*$")


def 코드정규(c):
    c = (c or "").strip()
    return "ifrs-full_" + c[5:] if c.startswith("ifrs_") else c


def _이름(zi):
    try:
        return zi.filename.encode("cp437").decode("cp949")
    except Exception:                                    # noqa: BLE001
        return zi.filename


def _열(머리, 앞말):
    for i, h in enumerate(머리):
        if h.strip().startswith(앞말):
            return i
    return None


def 풀기(zip경로, 표):
    """ZIP 하나 → {(종목코드, 구분): {"머리": {...}, "항목": {항: (당기, 전기, 코드, 순위)}}}."""
    낸 = {}
    코드표 = {코: (항, 순) for 항, (t, 코들) in 항목.items() if t == 표 for 순, 코 in enumerate(코들)}
    with zipfile.ZipFile(zip경로) as z:
        for zi in z.infolist():
            이름 = _이름(zi)
            if any(w in 이름 for w in 금융낱말):
                continue
            구분 = "연결" if "연결" in 이름 else "별도"
            with io.TextIOWrapper(z.open(zi), encoding="cp949", errors="replace", newline="") as f:
                rd = csv.reader(f, delimiter="\t")
                머리 = next(rd, None)
                if not 머리:
                    continue
                ci, pi = _열(머리, "당기"), _열(머리, "전기")
                if ci is None:
                    continue
                for r in rd:
                    if len(r) <= ci or len(r) < 12:
                        continue
                    코 = 코드정규(r[10])
                    잡 = 코드표.get(코)
                    if 잡 is None and 표 == "CF" and _감가이름.match(r[11] or "") and not re.search(r"무형|사용권|투자부동산", r[11]):
                        잡 = ("감가상각비", 50)                # 회사 고유 코드의 「감가상각비」 줄 — 표준 코드보다 뒤
                    if 잡 is None and 표 == "BS" and 코 == "ifrs-full_TradeAndOtherCurrentPayables" and _순수채무이름.match(r[11] or ""):
                        잡 = ("순수매입채무", 50)              # 「및 기타채무」 코드를 쓰되 항목명이 「매입채무」 뿐인 줄 — 공시 이름 그대로(as filed) 순수로 본다
                    if 잡 is None and 표 == "CF" and _무형상각이름.match(r[11] or ""):
                        잡 = ("무형상각비", 50)                # 회사 고유 코드의 「무형자산상각비」 줄 — 표준 코드보다 뒤
                    if 잡 is None and 표 == "CF" and _무형취득이름.match(r[11] or ""):
                        잡 = ("무형취득", 50)
                    if 잡 is None:
                        continue
                    항, 순 = 잡
                    v = 공.수(r[ci])
                    if v is None:
                        continue
                    pv = 공.수(r[pi]) if (pi is not None and len(r) > pi) else None
                    종 = r[1].strip().strip("[]").zfill(6)
                    d = 낸.setdefault((종, 구분), {"머리": {"결산기준일": r[7].strip(), "통화": r[9].strip(), "회사명": r[2].strip()}, "항목": {}})
                    old = d["항목"].get(항)
                    if old is None or 순 < old[3]:
                        d["항목"][항] = (v, pv, 코, 순)
    return 낸


def 한해(뿌리, y):
    """{종목코드: {"구분", "머리", "항목"}} — 연결이 있으면 연결만."""
    모 = {}
    있 = False
    for 표 in ("PL", "BS", "CF"):
        p = os.path.join(뿌리, "일괄", "%d_4Q_%s.zip" % (y, 표))
        if not os.path.exists(p):
            continue
        있 = True
        for (종, 구분), d in 풀기(p, 표).items():
            e = 모.setdefault(종, {}).setdefault(구분, {"머리": d["머리"], "항목": {}})
            e["항목"].update(d["항목"])
    if not 있:
        return None
    낸 = {}
    for 종, m in 모.items():
        구분 = "연결" if "연결" in m else "별도"
        낸[종] = {"구분": 구분, "머리": m[구분]["머리"], "항목": m[구분]["항목"]}
    return 낸


def 짓기(뿌리=None, 부터=2015, 까지=2025, 고를=None, 조용=False):
    뿌리 = 뿌리 or 공.패널뿌리()
    규칙 = 공.제외규칙()
    by고, by종 = 공.산업분류(뿌리)
    해자료 = {}
    for y in range(부터, 까지 + 1):
        d = 한해(뿌리, y)
        if d is None:
            continue
        해자료[y] = {}
        for 종, e in d.items():
            고 = by종.get(종)
            if not 고:
                continue
            if (e["머리"].get("통화") or "KRW") != 규칙["통화"]:
                continue
            if 공.제외인가(고, by고.get(고), e["머리"].get("회사명"), 규칙):
                continue
            해자료[y][고] = e
        if not 조용:
            print("  일괄 %d — 회사 %d" % (y, len(해자료[y])), flush=True)
    if not 해자료:
        return None
    주 = 공.주요계정(뿌리, range(부터, 까지 + 1))
    분모해 = 공.분모(뿌리, range(부터, 까지 + 1))
    줄 = {k: [] for k in ("유효세율_1년", "유효세율_3년", "현금세율_3년", "영업이익률_5년평균", "매출원가율", "판관비율",
                         "매입채무회전일수", "재고회전일수_원가", "상각률_기초순액", "무형상각률")}
    뺌 = {k: 0 for k in 줄}

    def 값(e, 항, 전기=False):
        v = e["항목"].get(항)
        return None if v is None else (v[1] if 전기 else v[0])

    def 코(e, 항):
        v = e["항목"].get(항)
        return v[2] if v else ""

    def 넣(변수, 고, y, e, 값_, 분자, 분모, 단위, 원천, 딱지, 비고="", 범위=None):
        if 값_ is None:
            return
        if 범위 and not (범위[0] <= 값_ <= 범위[1]):
            뺌[변수] += 1
            return
        줄[변수].append({"고유번호": 고, "회계연도": y, "값": 값_, "분자": 분자, "분모": 분모, "단위": 단위, "기준": e["구분"] if e else "",
                       "원천": 원천, "기간끝": (e or {}).get("머리", {}).get("결산기준일", ""), "딱지": 딱지, "비고": 비고})

    for y, 회사들 in 해자료.items():
        for 고, e in 회사들.items():
            매, 원, 판 = 값(e, "매출액"), 값(e, "매출원가"), 값(e, "판관비")
            세전, 세 = 값(e, "세전이익"), 값(e, "법인세비용")
            src = "일괄 %d_4Q" % y
            # 세율 — 한 해
            if 세전 and 세전 > 0 and 세 is not None:
                넣("유효세율_1년", 고, y, e, 세 / 세전, 세, 세전, "비율", "%s_PL · %s ÷ %s" % (src, 코(e, "법인세비용"), 코(e, "세전이익")),
                   "[유추]", "분모 세전이익 · 실현 세율(모델 196 은 법정세율 · 10번 16 은 영업이익 분모)", (-1.0, 1.0))
            # 세율 — 세 해 누적(같은 기준 셋)
            셋 = [해자료.get(y - j, {}).get(고) for j in range(3)]
            if all(셋) and len({x["구분"] for x in 셋}) == 1:
                ss = [값(x, "세전이익") for x in 셋]
                tt = [값(x, "법인세비용") for x in 셋]
                if all(v is not None for v in ss + tt) and sum(ss) > 0:
                    넣("유효세율_3년", 고, y, e, sum(tt) / sum(ss), sum(tt), sum(ss), "비율", "%s~%d_4Q_PL 세 해 누적 · 법인세비용 ÷ 세전이익" % ("일괄 %d" % (y - 2), y),
                       "[유추]", "분모 세전이익 · 실현 세율 세 해 누적", (-1.0, 1.0))
                pp = [값(x, "법인세납부") for x in 셋]
                if all(v is not None for v in ss + pp) and sum(ss) > 0:
                    # 부호 — 일괄 본표의 법인세 납부 줄은 지급을 양수로 적는 꼴이 다수(2024 실측 약 80%). 음수는 그 해 법인세비용이 양수면 표시 부호가
                    # 뒤집힌 지급으로, 아니면 환급으로 본다
                    납 = sum(v if v >= 0 else (abs(v) if (값(x, "법인세비용") or 0) > 0 else v) for v, x in zip(pp, 셋))
                    넣("현금세율_3년", 고, y, e, 납 / sum(ss), 납, sum(ss), "비율", "%s~%d_4Q CF · 법인세 납부(지급 양수) ÷ 세전이익" % ("일괄 %d" % (y - 2), y),
                       "[유추]", "현금 기준 · 분모 세전이익 · 음수 줄은 법인세비용이 양수인 해면 지급으로 봄", (-1.0, 1.0))
            # 원가율 · 판관비율
            if 매 and 매 > 0:
                if 원 is not None:
                    넣("매출원가율", 고, y, e, 원 / 매, 원, 매, "비율", "%s_PL · %s ÷ %s" % (src, 코(e, "매출원가"), 코(e, "매출액")),
                       "같음", "원가 줄이 매출원가 전체일 때 같음 — 일부면 [유추]", (1e-9, 3.0))
                if 판 is not None:
                    넣("판관비율", 고, y, e, 판 / 매, 판, 매, "비율", "%s_PL · %s ÷ %s" % (src, 코(e, "판관비"), 코(e, "매출액")),
                       "같음", "원가 줄이 판관비 전체일 때 같음 — 일부면 [유추]", (1e-9, 3.0))
            # 회전일수(원가 기준)
            if 원 and 원 > 0:
                mp = 값(e, "순수매입채무")
                if mp is not None:
                    넣("매입채무회전일수", 고, y, e, mp / 원 * 365.0, mp, 원, "일", "%s_BS · %s ÷ PL %s × 365" % (src, 코(e, "순수매입채무"), 코(e, "매출원가")),
                       "같음", "기준 매출원가(모델이 재료비 및 경비 기준이면 [유추])", (0.0, 3650.0))
                inv = 값(e, "재고자산")
                if inv is not None:
                    넣("재고회전일수_원가", 고, y, e, inv / 원 * 365.0, inv, 원, "일", "%s_BS · %s ÷ PL %s × 365" % (src, 코(e, "재고자산"), 코(e, "매출원가")),
                       "같음", "기준 매출원가(모델이 발생원가 기준이면 [유추])", (0.0, 3650.0))
            # 상각률(기초 순액 + 취득 ÷ 2)
            dep, ppe0, capex = 값(e, "감가상각비"), 값(e, "유형자산", 전기=True), 값(e, "유형취득")
            if ppe0 is None:
                prev = 해자료.get(y - 1, {}).get(고)
                if prev and prev["구분"] == e["구분"]:
                    ppe0 = 값(prev, "유형자산")
            if dep is not None and ppe0 is not None:
                dep = abs(dep)
                취 = abs(capex) if capex is not None else 0.0
                밑 = ppe0 + 취 / 2.0
                if 밑 > 0 and dep > 0:
                    섞 = 코(e, "감가상각비") in 상각섞임코드
                    넣("상각률_기초순액", 고, y, e, dep / 밑, dep, 밑, "비율",
                       "%s_CF · %s ÷ (BS 기초 유형자산 + CF %s ÷ 2)" % (src, 코(e, "감가상각비") or "감가상각비(회사 고유 코드)", 코(e, "유형취득") or "취득 없음"),
                       "[유추]" if 섞 else "같음", ("감가상각과 무형 상각이 한 줄" if 섞 else "") + ("" if capex is not None else " · 취득 줄 없음(0 으로)"), (1e-9, 2.0))
            # 무형자산상각률(기초 무형자산 + 무형 취득 ÷ 2) — 엔진 164 의 밑 · 2026-10-24 PN
            am, ia0, ic = 값(e, "무형상각비"), 값(e, "무형자산", 전기=True), 값(e, "무형취득")
            if ia0 is None:
                prev = 해자료.get(y - 1, {}).get(고)
                if prev and prev["구분"] == e["구분"]:
                    ia0 = 값(prev, "무형자산")
            if am is not None and ia0 is not None:
                am = abs(am)
                밑 = ia0 + (abs(ic) if ic is not None else 0.0) / 2.0
                if 밑 > 0 and am > 0:
                    넣("무형상각률", 고, y, e, am / 밑, am, 밑, "비율",
                       "%s_CF · %s ÷ (BS 기초 %s + CF %s ÷ 2)" % (src, 코(e, "무형상각비") or "무형자산상각비(회사 고유 코드)", 코(e, "무형자산"),
                                                             코(e, "무형취득") or "취득 없음"),
                       "같음", ("" if ic is not None else "무형 취득 줄 없음(0 으로 — 엔진도 81 행이 비면 0)")
                       + (" · 기초 무형자산에 영업권 포함(공시 한 줄)" if 코(e, "무형자산") == "ifrs-full_IntangibleAssetsAndGoodwill" else ""), (1e-9, 2.0))
    # 영업이익률 5년 평균 — 주요계정(기저율 패널의 영업이익률과 같은 원천)
    for (고, y), r in 주.items():
        if y < 부터 + 4 or y not in 분모해 or 고 not in 분모해.get(y, set()):
            continue
        률 = []
        for j in range(5):
            rr = 주.get((고, y - j))
            매 = 공.수((rr or {}).get("매출액"))
            영 = 공.수((rr or {}).get("영업이익"))
            if not rr or not 매 or 매 <= 0 or 영 is None:
                break
            률.append(영 / 매)
        if len(률) == 5:
            e = {"구분": "연결" if "연결" in (r.get("재무제표구분") or "") else "별도", "머리": {"결산기준일": "%d-12-31" % y}}
            넣("영업이익률_5년평균", 고, y, e, sum(률) / 5.0, sum(률), 5, "비율", "주요계정_%d~%d · 영업이익 ÷ 매출액 다섯 해 평균" % (y - 4, y),
               "[유추]", "정상 상태(영구열) 대 실현 다섯 해 평균 · 기간끝은 회계연도 말(결산월 다르면 그 해)", (-3.0, 1.0))
    뜻 = {
        "유효세율_1년": {"정의": "법인세비용 ÷ 법인세비용차감전순이익(세전 > 0 · |율| ≤ 1)", "칸": ["196(대조)", "10번 16(대조)"], "단위": "비율", "딱지": "[유추]"},
        "유효세율_3년": {"정의": "Σ법인세비용 ÷ Σ세전이익(t−2 ~ t · 세 해 모두 · 같은 기준)", "칸": ["196(대조)"], "단위": "비율", "딱지": "[유추]"},
        "현금세율_3년": {"정의": "Σ법인세 납부(CF · 지급 양수 — 음수는 법인세비용이 양수인 해면 지급) ÷ Σ세전이익(t−2 ~ t)", "칸": ["196(대조)"], "단위": "비율", "딱지": "[유추]"},
        "영업이익률_5년평균": {"정의": "영업이익 ÷ 매출액(주요계정)의 t−4 ~ t 평균(다섯 해 모두)", "칸": ["213", "영구열 영업이익률"], "단위": "비율", "딱지": "[유추]"},
        "매출원가율": {"정의": "매출원가 ÷ 매출액(일괄 본표)", "칸": ["80 꼴(원가 줄이 매출원가)"], "단위": "비율", "딱지": "같음"},
        "판관비율": {"정의": "판매비와관리비 ÷ 매출액(일괄 본표)", "칸": ["80 꼴(원가 줄이 판관비)"], "단위": "비율", "딱지": "같음"},
        "매입채무회전일수": {"정의": "순수 매입채무(기말) ÷ 매출원가 × 365 — 「매입채무 및 기타채무」 한 줄 회사 제외", "칸": ["186"], "단위": "일", "딱지": "같음"},
        "재고회전일수_원가": {"정의": "재고자산(기말) ÷ 매출원가 × 365", "칸": ["182"], "단위": "일", "딱지": "같음"},
        "상각률_기초순액": {"정의": "유형자산 감가상각비 ÷ (기초 유형자산 순액 + 유형자산 취득 ÷ 2)", "칸": ["156"], "단위": "비율", "딱지": "같음"},
        "무형상각률": {"정의": "무형자산상각비 ÷ (기초 무형자산 + 무형자산 취득 ÷ 2) — 엔진 164 의 밑 · 코드는 13번 원천 18 · 78 · 81 행과 같다(공시 한 줄이 영업권을 품으면 그대로)",
                  "칸": ["164"], "단위": "비율", "딱지": "같음"},
    }
    # 정의 가능 분모 — 정의상 값이 설 수 있는 회사 · 연도(세전 > 0 · 다섯 해 창 · 그 줄을 공시한 회사)에 대한 커버리지(성공 기준을 구조 한계와 가르려고)
    a, b = 공.성공창
    가능 = {k: set() for k in 줄}
    for y, 회사들 in 해자료.items():
        if not (a <= y <= b):
            continue
        for 고, e in 회사들.items():
            if 고 not in 분모해.get(y, set()):
                continue
            세전 = 값(e, "세전이익")
            if 세전 and 세전 > 0:
                가능["유효세율_1년"].add((고, y))
            셋 = [해자료.get(y - j, {}).get(고) for j in range(3)]
            if all(셋) and sum((값(x, "세전이익") or 0) for x in 셋) > 0:
                가능["유효세율_3년"].add((고, y))
                가능["현금세율_3년"].add((고, y))
            if 값(e, "매출액") and 값(e, "매출원가"):
                for k in ("매출원가율", "재고회전일수_원가", "매입채무회전일수"):
                    가능[k].add((고, y))
            if 값(e, "매출액"):
                가능["판관비율"].add((고, y))
            if 값(e, "유형자산") is not None:
                가능["상각률_기초순액"].add((고, y))
            if 값(e, "무형자산"):
                가능["무형상각률"].add((고, y))
    for y in range(max(a, 부터 + 4), b + 1):
        for 고 in 분모해.get(y, set()):
            가능["영업이익률_5년평균"].add((고, y))
    # 주석 보강(C 단계 `dart_주석패널.py` 가 `_보강_주석/<변수>.csv` 에 남긴 줄) — 일괄 본표에 없는 회사 · 연도만 더한다.
    # 그다음 원문 역보강(D 단계 `_보강_원문/` — 정확도를 통과한 항목만 · 2026-10-24 PN) — 일괄 · 주석이 없는 회사 · 연도만
    보강수, 원문수 = {}, {}
    for 곳이름, 변 in [(c, v) for c in ("_보강_주석", "_보강_원문") for v in ("상각률_기초순액", "매입채무회전일수", "무형상각률")]:
        p = os.path.join(공.자리(뿌리), 곳이름, "%s.csv" % 변)
        세기 = 보강수 if 곳이름 == "_보강_주석" else 원문수
        세기[변] = 0
        if not os.path.exists(p):
            continue
        있 = {(r["고유번호"], int(r["회계연도"])) for r in 줄[변]}
        with io.open(p, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                k = (r["고유번호"], int(r["회계연도"]))
                if k in 있 or not (부터 <= k[1] <= 까지):
                    continue
                r = dict(r)
                for c in ("값", "분자", "분모"):
                    r[c] = 공.수(r.get(c))
                줄[변].append(r)
                세기[변] += 1
    낸 = {}
    for 변, 줄들 in 줄.items():
        if 고를 and 변 not in 고를:
            continue
        칸 = dict(뜻[변])
        if 변 in 보강수:
            칸["주석보강_줄"] = 보강수[변]
        if 원문수.get(변):
            칸["원문역보강_줄"] = 원문수[변]
        덮 = {(r["고유번호"], int(r["회계연도"])) for r in 줄들}
        칸["커버리지_정의가능"] = round(len(덮 & 가능[변]) / len(가능[변]), 4) if 가능[변] else None
        칸["정의가능_뜻"] = {"유효세율_1년": "세전이익 > 0 인 회사 · 연도", "유효세율_3년": "세 해가 다 있고 Σ세전 > 0", "현금세율_3년": "세 해가 다 있고 Σ세전 > 0",
                         "영업이익률_5년평균": "패널 첫 해 + 4 이후(다섯 해 창이 설 수 있는 해)", "매출원가율": "매출 · 매출원가를 본표에 적은 회사",
                         "판관비율": "매출을 본표에 적은 회사", "매입채무회전일수": "매출 · 매출원가를 본표에 적은 회사(순수 매입채무 줄은 그 일부만 있다 — 구조 한계)",
                         "재고회전일수_원가": "매출 · 매출원가를 본표에 적은 회사", "상각률_기초순액": "유형자산을 본표에 적은 회사(감가상각비는 현금흐름표 본표에 적은 회사만 — 구조 한계)",
                         "무형상각률": "무형자산을 본표에 적은 회사(무형자산상각비는 현금흐름표 본표에 적은 회사만 — 구조 한계)"}[변]
        칸.update({"원천": "OpenDART 재무정보 일괄다운로드 본표(공용 캐시 일괄/) · 주요계정", "도구": "dart_상세변수.py", "원천asof": "일괄 %d_4Q" % max(해자료),
                  "뺀_정의역밖": 뺌[변]})
        낸[변] = 공.쓰기(변, 줄들, 칸, 뿌리, 분모해)
        if not 조용:
            print("  %-16s 줄 %6d · 커버리지 %s(%s) · 정의 가능 분모 대비 %s · 정의역 밖 %d" % (변, len(줄들), 낸[변]["커버리지_전체"], 낸[변]["커버리지_창"],
                  낸[변]["커버리지_정의가능"], 뺌[변]), flush=True)
    return 낸


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="국내 상세 패널 변수(A — 일괄 본표 · 새 호출 없음)")
    ap.add_argument("--부터", type=int, default=2015)
    ap.add_argument("--까지", type=int, default=2025)
    ap.add_argument("--변수", default="")
    a = ap.parse_args(argv)
    낸 = 짓기(None, a.부터, a.까지, set(x for x in a.변수.split(",") if x) or None)
    if 낸 is None:
        print("입력 오류 — 일괄 ZIP 이 없다(`python 스크립트/dart_일괄패널.py --받기`)")
        return 2
    print("→ %s" % 공.자리())
    return 0


if __name__ == "__main__":
    sys.exit(main())

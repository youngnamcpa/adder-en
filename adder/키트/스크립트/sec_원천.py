# -*- coding: utf-8 -*-
"""미국 종목 **원천(13번) 조립** — 이미 받아 둔 `_raw/companyfacts.json` 한 파일만 읽는다.

**왜 만들었나.** 국내는 `dart_fs_all.py` 가 원천을 조립하는데 미국은 그 짝이 없어
**회차마다 태그 표를 손으로 다시 짰다.** 그래서 같은 실수가 되풀이된다 — 실측(UBER):
`PropertyPlantAndEquipmentNet` 이 2024-09-30 에서 끊기고 그 뒤로는
`PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAsset…` 로 갈아탔는데, 그것을 모르면
**유형자산이 통째로 빈 채로 회차가 돈다.** 상각률(156행)의 밑값이 그 행이다.

조문이 지키라는 것을 코드가 지키게 한다.
  · **태그 이름을 가정하지 않는다** — 후보를 여럿 두고 짧은 이름도 훑는다
  · **못 찾은 것을 비슷한 값으로 메우지 않는다** — 비우고 그 행 이름을 낸다
  · **미국은 리스가 넷이다** — 운용·금융이 각각 유동·비유동. 둘만 가져오면 절반이 빠진다
  · **자본은 비지배지분 포함 여부를 밝힌다**
  · **회사가 태그를 갈아타면 이어 붙인다** — sec_앵커 와 같은 규칙(겹치는 날의 값이
    맞을 때만 잇는다). 뜻이 다른 태그로 빈 날을 메우면 시계열이 거짓이 된다

사용:
    python 스크립트/sec_원천.py --기준일 2026-06-30
    python 스크립트/sec_원천.py --기준일 2026-06-30 --결산월 12 --반기

산출: `_raw/원천_조립.json` — `{"원천": {행: [D,E,F]}, "태그": …, "못찾음": […]}`
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "_raw")

# ── 13번 행 → 태그 후보 ────────────────────────────────────────────
# `합산` 이 True 면 **후보를 다 더한다**(리스처럼 갈려 있는 행). False 면 **먼저 맞는
# 하나만** 쓴다(같은 뜻의 다른 이름). 이 구분을 틀리면 이중계상이 되거나 절반이 빠진다.
잔액표 = {
    7:  (False, ("CashAndCashEquivalentsAtCarryingValue",)),
    8:  (False, ("ShortTermInvestments",)),
    9:  (False, ("MarketableSecuritiesCurrent",
                 "AvailableForSaleSecuritiesDebtSecuritiesCurrent")),
    # AccountsNotesAndLoansReceivableNetCurrent — 구표준을 계속 쓰는 회사가 있다
    # (실측: MCD 2,485M 이 이 태그뿐이라 10행이 비었다).
    10: (False, ("AccountsReceivableNetCurrent", "ReceivablesNetCurrent",
                 "AccountsReceivableNet", "AccountsNotesAndLoansReceivableNetCurrent",
                 "OtherReceivablesNetCurrent")),
    # 수주업(항공기 등)은 재고를 「선수금·중도금 차감」 이름의 긴 태그로 낸다 —
    # 실측(BA): InventoryNet 이 없고 아래 둘째 태그만 있어 재고 88.4B 가 통째로
    # 빠졌고, 기초 재고 0 에서 375일치를 새로 쌓는 가짜 WC 유출로 세 시나리오가
    # 전부 음수가 됐다.
    # InventoryFinishedGoodsNetOfReserves — 완제품만 내는 브랜드 소비재(실측: NKE
    # 7.5B 가 이 태그뿐이라 11행이 비었다).
    11: (False, ("InventoryNet",
                 "InventoryNetOfAllowancesCustomerAdvancesAndProgressBillings",
                 "InventoryFinishedGoodsNetOfReserves")),
    14: (False, ("OtherReceivablesNetCurrent",)),
    # `OtherAssetsCurrent` 는 15(기타유동자산 — 운전자본)다. 미국 공시의 「Other current assets」 는 선급 · 기타 영업 자산이다.
    # 옛 판은 13(기타금융자산 — 비영업)에 두어 운전자본에서 빠지고 비영업자산이 그만큼 부풀었다(2026-11-05 U-02).
    # 선급 · 기타 합계 태그가 없는 열은 선급비용 태그로 대신한다(`_빈자리대체` — 같은 줄의 다른 이름이라 합산 목록에 두지 않는다.
    # 이 표를 태그마다 더해 읽는 도구가 있어 둘을 나란히 두면 선급비용이 두 번 센다). 13 에 따로 두던 때와 합계는 같다.
    15: (True,  ("PrepaidExpenseAndOtherAssetsCurrent", "OtherAssetsCurrent")),
    # **유형자산 — 회사가 갈아타는 대표 자리.** 금융리스 사용권을 합친 태그를 쓰면
    # 그 값에 금융리스 ROU 가 이미 들어 있다. 19행(사용권자산)에는 **운용리스만** 담아야
    # 이중계상이 안 된다. 아래 `_리스겹침` 이 그 판정을 하고 결과에 적는다.
    17: (False, ("PropertyPlantAndEquipmentNet",
                 "PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAsset"
                 "AfterAccumulatedDepreciationAndAmortization",
                 "PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetNet")),
    18: (False, ("IntangibleAssetsNetExcludingGoodwill",
                 "FiniteLivedIntangibleAssetsNet")),
    19: (True,  ("OperatingLeaseRightOfUseAsset", "FinanceLeaseRightOfUseAsset")),
    20: (False, ("EquityMethodInvestments",)),
    21: (False, ("RealEstateInvestmentPropertyNet",)),
    24: (False, ("Goodwill",)),
    27: (False, ("AvailableForSaleSecuritiesDebtSecuritiesNoncurrent",)),
    28: (False, ("EquitySecuritiesFvNiNoncurrent", "EquitySecuritiesFvNiCurrentAndNoncurrent")),
    # 전략적 투자(비상장 지분 등) — 실측(CRM): `OtherLongTermInvestments` 4.9B→11.3B(자산의 10%)가
    # 매핑이 없어 통째로 빠졌다. 13번 29행(기타금융자산 비유동)이 그 자리다.
    29: (False, ("OtherLongTermInvestments",)),
    30: (False, ("OtherReceivablesNetNoncurrent",)),
    31: (False, ("OtherAssetsNoncurrent",)),
    33: (False, ("Assets",)),
    # `AccountsPayableAndOtherAccruedLiabilitiesCurrent` — 실측(CRM): 이 한 줄로만 내서 34행이
    # 필수 빈 행(★)으로 남았다(6.7B~8.3B).
    34: (False, ("AccountsPayableCurrent",
                 "AccountsPayableAndAccruedLiabilitiesCurrent",
                 "AccountsPayableAndOtherAccruedLiabilitiesCurrent",
                 "AccountsPayableAndAccruedLiabilitiesCurrentAndNoncurrent")),
    35: (False, ("AccruedLiabilitiesCurrent",)),
    36: (False, ("OtherAccountsPayableAndAccruedLiabilities",)),
    37: (False, ("ShortTermBorrowings", "OtherShortTermBorrowings",
                 "CommercialPaper")),
    38: (False, ("LongTermDebtCurrent",)),
    39: (True,  ("OperatingLeaseLiabilityCurrent", "FinanceLeaseLiabilityCurrent")),
    40: (False, ("AccruedLiabilitiesCurrentAndNoncurrent",)),
    # 계약부채(고객 선수금)를 합산한다 — 실측(BA): 선수금 64.1B 가 재고 88.4B 의
    # 반대편인데 43 에 안 실려 순 WC 가 두 배 넘게 과대했다. 둘은 배타 계정이라
    # 합산해도 이중계상이 없다. 43 은 엔진 9번 기타 WC(w13)에 음수로 들어간다.
    43: (True,  ("OtherLiabilitiesCurrent", "ContractWithCustomerLiabilityCurrent")),
    45: (False, ("LongTermDebtNoncurrent", "LongTermDebt")),
    46: (False, ("SecuredDebt",)),
    47: (True,  ("OperatingLeaseLiabilityNoncurrent", "FinanceLeaseLiabilityNoncurrent")),
    48: (False, ("DefinedBenefitPensionPlanLiabilitiesNoncurrent",)),
    53: (False, ("OtherLiabilitiesNoncurrent",)),
    55: (False, ("Liabilities",)),
    56: (False, ("StockholdersEquity",)),
    57: (False, ("MinorityInterest", "MinorityInterestInPreferredUnitHolders")),
}

흐름표 = {
    62: (False, ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
                 "RevenueFromContractWithCustomerIncludingAssessedTax",
                 "SalesRevenueNet")),
    63: (False, ("CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold",
                 "CostOfServices",
                 "CostOfRevenueExcludingDepreciationDepletionAndAmortization",
                 "CostOfGoodsAndServiceExcludingDepreciationDepletionAndAmortization")),
    # **판관비는 미국에서 여러 줄로 갈린다** — SG&A · R&D · S&M 을 따로 낸다. 합산한다.
    # R&D 는 변형 태그로 갈아타는 회사가 있다 — 실측: LLY 가 표준 태그를 2023-06
    # 에서 끊고 Excluding… 변형으로 전환(PFE 는 처음부터 변형만). 그 변형이 빠지면
    # 산술 폴백 66 이 R&D 만큼 부풀어 OPM 52%(PFE)·66%(LLY)가 나온다. 같은 기간에
    # 둘을 겹쳐 내는 회사는 관측 42곳에서 없었다(AMD 의 변형은 2010~12 유물).
    65: (True,  ("SellingGeneralAndAdministrativeExpense",
                 "GeneralAndAdministrativeExpense", "SellingAndMarketingExpense",
                 "ResearchAndDevelopmentExpense",
                 "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost")),
    66: (False, ("OperatingIncomeLoss",)),
    71: (False, ("IncomeLossFromContinuingOperationsBeforeIncomeTaxes"
                 "ExtraordinaryItemsNoncontrollingInterest",
                 "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterest"
                 "AndIncomeLossFromEquityMethodInvestments")),
    72: (False, ("IncomeTaxExpenseBenefit",)),
    # DepreciationAndAmortization 도 표준이다 — 실측(V): 이 태그만 있어 77 이 비었다.
    77: (False, ("DepreciationDepletionAndAmortization",
                 "DepreciationAmortizationAndAccretionNet",
                 "DepreciationAndAmortization", "Depreciation")),
    78: (False, ("AmortizationOfIntangibleAssets",)),
    80: (False, ("PaymentsToAcquirePropertyPlantAndEquipment",
                 "PaymentsToAcquireProductiveAssets",
                 "PaymentsToAcquireOtherPropertyPlantAndEquipment",
                 "PaymentsToAcquireCommercialRealEstate")),
    81: (False, ("PaymentsToAcquireIntangibleAssets",)),
}

# ── 20-F(IFRS) 폴백 표 — us-gaap 에서 못 찾은 행만 이 표로 다시 찾는다 ──────
# 실측(TSM): 외국 발행인은 `ifrs-full` 네임스페이스만 있다. 국내 dart_원천 과
# 같은 태그 체계라 표도 같은 계열이다.
IFRS잔액표 = {
    7:  (False, ("CashAndCashEquivalents",)),
    10: (False, ("TradeAndOtherCurrentReceivables", "CurrentTradeReceivables",
                 "TradeReceivables")),
    11: (False, ("Inventories",)),
    17: (False, ("PropertyPlantAndEquipment",)),
    18: (False, ("IntangibleAssetsOtherThanGoodwill", "IntangibleAssetsAndGoodwill")),
    19: (False, ("RightofuseAssets",)),
    20: (False, ("InvestmentsInAssociatesAccountedForUsingEquityMethod",
                 "InvestmentAccountedForUsingEquityMethod")),
    24: (False, ("Goodwill",)),
    33: (False, ("Assets",)),
    34: (False, ("TradeAndOtherCurrentPayables", "TradeAndOtherCurrentPayablesToTradeSuppliers")),
    37: (False, ("ShorttermBorrowings", "CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings")),
    # 38 유동성장기부채 — IFRS 발행인의 1년 안에 갚을 장기차입 · 사채(이자부부채). 표에 없어 통째로 빠졌다(2026-10-24 W13 · TSM 20-F 1,369억 대만달러).
    # 합계 태그를 먼저(사채 + 은행차입의 유동 몫) — 부분 태그(사채만)는 합계가 없을 때만
    38: (False, ("CurrentPortionOfLongtermBorrowings", "CurrentPortionOfNoncurrentBorrowings",
                 "CurrentBondsIssuedAndCurrentPortionOfNoncurrentBondsIssued")),
    39: (True,  ("CurrentLeaseLiabilities",)),
    45: (False, ("NoncurrentPortionOfNoncurrentBondsIssued", "BondsIssued")),
    46: (False, ("LongtermBorrowings", "NoncurrentPortionOfNoncurrentLoansReceived")),
    47: (True,  ("NoncurrentLeaseLiabilities",)),
    55: (False, ("Liabilities",)),
    56: (False, ("Equity", "EquityAttributableToOwnersOfParent")),
    57: (False, ("NoncontrollingInterests",)),
}
IFRS흐름표 = {
    62: (False, ("Revenue", "RevenueFromContractsWithCustomers")),
    63: (False, ("CostOfSales",)),
    65: (True,  ("SellingGeneralAndAdministrativeExpense", "AdministrativeExpense",
                 "SellingExpense", "ResearchAndDevelopmentExpense")),
    66: (False, ("ProfitLossFromOperatingActivities",)),
    71: (False, ("ProfitLossBeforeTax",)),
    72: (False, ("IncomeTaxExpenseContinuingOperations",)),
    77: (False, ("DepreciationExpense", "DepreciationAndAmortisationExpense")),
    78: (False, ("AmortisationExpense", "AmortisationIntangibleAssetsOtherThanGoodwill")),
    80: (False, ("PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",)),
    81: (False, ("PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities",)),
}


def 통화감지(facts):
    """회사가 실제로 쓰는 통화 — 두 네임스페이스의 units 키를 세어 가장 흔한 것.

    실측(TSM): 보고통화가 TWD 라 USD 고정 필터가 전부 걸러냈다. shares 는 제외한다.
    """
    from collections import Counter
    c = Counter()
    for ns in ("us-gaap", "ifrs-full"):
        for v in (facts.get(ns) or {}).values():
            for u in (v.get("units") or {}):
                if u != "shares" and "/" not in u:
                    c[u] += 1
    return c.most_common(1)[0][0] if c else "USD"


주식표 = {
    95: ("CommonStockSharesIssued",),
    96: ("TreasuryStockCommonShares", "TreasuryStockShares"),
    97: ("CommonStockSharesOutstanding",),
}

행이름 = {
    7: "현금및현금성자산", 8: "단기금융상품", 9: "단기투자자산", 10: "매출채권",
    11: "재고자산", 13: "기타금융자산(유동)", 14: "기타수취채권(유동)",
    15: "기타유동자산", 17: "유형자산", 18: "무형자산", 19: "사용권자산",
    20: "관계기업투자", 21: "투자부동산", 24: "영업권", 26: "이연법인세자산", 27: "FVOCI 금융자산",
    28: "FVPL 금융자산", 29: "기타금융자산(비유동)", 30: "기타수취채권(비유동)", 31: "기타비유동자산",
    33: "자산총계", 34: "매입채무", 35: "기타지급채무(유동)", 36: "미지급금",
    37: "단기차입금", 38: "유동성장기부채", 39: "리스부채(유동)", 40: "충당부채(유동)",
    41: "당기법인세부채", 43: "기타유동부채", 45: "사채", 46: "장기차입금", 47: "리스부채(비유동)",
    48: "순확정급여부채", 49: "이연법인세부채", 51: "장기미지급금", 53: "기타비유동부채",
    55: "부채총계", 56: "자본총계",
    57: "비지배지분", 62: "매출액", 63: "매출원가", 65: "판매비와관리비",
    66: "영업이익", 71: "법인세비용차감전순이익", 72: "법인세비용",
    77: "감가상각비", 78: "무형자산상각비", 80: "유형자산 취득", 81: "무형자산 취득",
    95: "발행주식총수", 96: "자기주식수", 97: "유통주식수",
}

# **꼭 있어야 하는 행** — 비면 값이 통째로 어긋난다. 결과에 따로 이름을 낸다.
필수 = (7, 10, 17, 34, 55, 62, 66, 72, 77, 80, 97)


def _일수(a, b):
    """두 ISO 날짜의 차이(일). 하나라도 없으면 큰 수를 낸다."""
    if not a or not b:
        return 10 ** 9
    try:
        return (datetime.date.fromisoformat(a)
                - datetime.date.fromisoformat(b)).days
    except ValueError:
        return 10 ** 9


# **총계 태그가 있으면 그 부분 태그는 더하지 않는다** — 실측(NKE): SG&A(총계
# 16,114)와 G&A(Operating overhead 11,360)·Marketing 을 다 내는 회사에서 합산이
# 이중계상돼 판관율 59%·OPM −16% 가 나왔다(실제 +10%). 포함 관계를 표로 박는다.
_총계부분 = {
    "SellingGeneralAndAdministrativeExpense": (
        "GeneralAndAdministrativeExpense", "SellingAndMarketingExpense",
        "MarketingAndAdvertisingExpense"),
}

# **그 열에 값이 없을 때만 대신 쓰는 같은 줄의 다른 이름** — 합산 행 안에서 한 칸을 열마다 갈아 끼운다(합산 목록에 나란히 두면 겹친다)
_빈자리대체 = {
    "PrepaidExpenseAndOtherAssetsCurrent": ("PrepaidExpenseCurrent",),
}

# ── **소계 대조로만 넣는 표면 줄** (2026-11-05 U-02) ──────────────────────────────
# 미국 10-K · 10-Q 재무상태표에 따로 서는 줄(Accrued compensation · income taxes · unearned revenue · deferred income
# taxes · Equity and other investments)인데, **같은 태그가 다른 회사에서는 묶음 줄(Accrued liabilities · Other liabilities ·
# Other assets)의 주석 내역**으로 온다. 무조건 더하면 주석 내역을 두 번 센다. 그래서 공시 소계와 행 합의 차이를
# **이 후보들의 조합이 정확히 닫을 때만** 넣는다. 한 묶음(같은 줄의 다른 이름)에서는 하나만 쓴다.
#   (줄, 같은 줄의 태그 이름들) — 줄은 13번 행이다. 26 · 49 이연법인세 · 41 · 51 법인세 · 36 미지급(급여) · 43 · 53 선수수익 · 29 장기투자
# 뜻이 자산 · 부채 어느 쪽인지 분명하지 않은 태그(DeferredTaxAssetsLiabilitiesNet · TaxesPayable…)와 파생상품 · 매각예정은
# 넣지 않는다 — 자산과 부채를 같이 봐야 하는 판단이다.
소계후보 = {
    "유동부채": ((36, ("EmployeeRelatedLiabilitiesCurrent", "AccruedSalariesCurrent")),
              (41, ("AccruedIncomeTaxesCurrent",)),
              (43, ("DeferredRevenueCurrent",))),
    "비유동부채": ((51, ("AccruedIncomeTaxesNoncurrent",)),
               (49, ("DeferredIncomeTaxLiabilitiesNet",)),
               (53, ("ContractWithCustomerLiabilityNoncurrent", "DeferredRevenueNoncurrent"))),
    "비유동자산": ((26, ("DeferredIncomeTaxAssetsNet",)),
               (29, ("LongTermInvestments",))),
}
# 표면 묶음 줄이 품는 몫 — `LongTermInvestments`(Equity and other investments)는 지분법 · 지분증권 · 채무증권을 한 줄로 낸다.
# 그 안의 몫이 20 · 27 · 28 · 29 로 이미 잡혀 있을 수 있어, **그 행들의 부분집합을 뺀 나머지**를 29 에 더하는 꼴까지 맞대 본다
# (품은 행의 값은 그대로 두어 지분법 몫이 20 에 남는다).
_묶음품는행 = {"LongTermInvestments": (20, 27, 28, 29)}


def _대신(us, t, 뽑기, 통화="USD"):
    """`t` 가 그 열에 값이 없으면 `_빈자리대체` 의 같은 줄 다른 이름 가운데 값이 있는 첫 태그 — 없으면 `t` 그대로."""
    for x in (t,) + _빈자리대체.get(t, ()):
        for u, a in ((us.get(x) or {}).get("units") or {}).items():
            if u in (통화, "shares") and a and 뽑기(a) is not None:
                return x
    return t


def _고르기(us, 후보, 뽑기, 통화="USD"):
    """후보를 훑어 (값, 쓴 태그들) 을 낸다. `뽑기(arr)` 가 한 태그의 값을 낸다."""
    쓴것, 합 = [], None
    빼기 = set()
    for t in 후보:
        if t in 빼기:
            continue
        t = _대신(us, t, 뽑기, 통화)
        arr = None
        for u, a in ((us.get(t) or {}).get("units") or {}).items():
            if u in (통화, "shares"):
                arr = a
                break
        if not arr:
            continue
        v = 뽑기(arr)
        if v is None:
            continue
        합 = (합 or 0.0) + v
        쓴것.append(t)
        for 부분 in _총계부분.get(t, ()):
            빼기.add(부분)
    return 합, 쓴것


def 조립(cf, 기준일들, 흐름기간들):
    """`기준일들` 은 잔액의 세 날짜, `흐름기간들` 은 (시작, 끝) 셋."""
    us = (cf.get("facts") or {}).get("us-gaap") or {}
    ifrs = (cf.get("facts") or {}).get("ifrs-full") or {}
    통화 = 통화감지(cf.get("facts") or {})
    원천, 태그, 못찾음 = {}, {}, []
    주의 = []
    if 통화 != "USD":
        주의.append("**보고통화가 %s 입니다** — 금액은 전부 %s 단위입니다. "
                   "주당가치·시가총액을 USD 로 읽으면 환산이 통째로 어긋납니다"
                   % (통화, 통화))
    if not us and ifrs:
        주의.append("**20-F(IFRS) 발행인입니다** — us-gaap 이 없어 ifrs-full "
                   "태그로 조립했습니다(국내 DART 와 같은 태그 체계)")
    # companyfacts 가 늦게 싣는 정기 공시(2026-10-24 W13 — 실측 TSM FY2025 20-F) — submissions 가 곁에 있으면 빠진 공시를 알린다(값을 고치지 않는다)
    try:
        _sp = os.path.join(RAW, "submissions.json")
        if os.path.exists(_sp):
            import sec_xbrl보충 as _보                    # noqa: PLC0415
            _빠 = _보.빠진공시(json.load(io.open(_sp, encoding="utf-8")), cf)
            if _빠:
                주의.append("**companyfacts 가 XBRL 정기 공시 %d건을 아직 싣지 않았습니다**(%s) — 최신 열이 비거나 옛 해에서 멈춥니다. "
                           "`python 스크립트/sec_xbrl보충.py` 로 그 공시의 XBRL 인스턴스에서 보충한 뒤 다시 도십시오"
                           % (len(_빠), " · ".join("%s %s" % (x["양식"], x["접수일"]) for x in _빠)))
    except Exception:                                        # noqa: BLE001 — 알림일 뿐 조립을 막지 않는다
        pass
    if any(((x.get("양식") or "").startswith("MOPS")) for x in (cf.get("_보충") or [])):
        주의.append("**대만 공시(MOPS) 재무를 함께 조립했습니다** — `tw_원천.py` 가 넣은 인라인 XBRL 사실(ifrs-full · 대만 확장 태그 몇 줄은 표준 이름으로 다리)")
    쓴날짜 = set()          # (찾던 날, 실제로 쓴 날) — 근접으로 잡은 자리

    # **정확 일치로 찾으면 52/53주 회계연도가 통째로 빈다.** 실측(AMD): 기말이
    # 2025-12-27 처럼 매년 다르다. Apple 은 9월 결산이라 12-31 로는 아예 안 맞는다.
    # ±10일 안에서 가장 가까운 날을 쓴다 — 그 폭 안에 다른 사업연도가 들어올 수 없다.
    근접 = 10

    def _가까운(후보, 날):
        가장, 짧 = None, 10 ** 9
        for x in 후보:
            d = abs(_일수(x.get("end"), 날))
            if d <= 근접 and d < 짧:
                가장, 짧 = x, d
            elif d == 짧 and 가장 is not None:
                # 같은 거리면 나중에 접수된 것(최신 재작성)을 쓴다
                if (x.get("filed") or "") > (가장.get("filed") or ""):
                    가장 = x
        return 가장

    def 잔액뽑기(날):
        def f(arr):
            후보 = [x for x in arr if "start" not in x and x.get("end")]
            정 = [x for x in 후보 if x.get("end") == 날]
            if 정:
                정.sort(key=lambda x: (x.get("filed") or ""))
                return float(정[-1]["val"])
            x = _가까운(후보, 날)
            if x is None:
                return None
            쓴날짜.add((날, x.get("end")))
            return float(x["val"])
        return f

    def 흐름뽑기(시, 끝):
        def f(arr):
            후보 = [x for x in arr if x.get("start") and x.get("end")]
            정 = [x for x in 후보 if x.get("start") == 시 and x.get("end") == 끝]
            if 정:
                정.sort(key=lambda x: (x.get("filed") or ""))
                return float(정[-1]["val"])
            # 시작과 끝이 **둘 다** 근접해야 한다 — 끝만 맞으면 분기가 섞인다
            가까 = [x for x in 후보
                   if abs(_일수(x.get("start"), 시)) <= 근접
                   and abs(_일수(x.get("end"), 끝)) <= 근접]
            if not 가까:
                return None
            가까.sort(key=lambda x: (x.get("filed") or ""))
            쓴날짜.add((끝, 가까[-1].get("end")))
            return float(가까[-1]["val"])
        return f

    for 표, 뽑기들 in ((잔액표, [잔액뽑기(d) for d in 기준일들]),
                    (흐름표, [흐름뽑기(*p) for p in 흐름기간들])):
        for 행, (합산, 후보) in sorted(표.items()):
            셋, 태그들 = [], set()
            for i in range(3):
                if 합산:
                    v, t = _고르기(us, 후보, 뽑기들[i], 통화)
                else:
                    v, t = None, []
                    for one in 후보:
                        v, t = _고르기(us, (one,), 뽑기들[i], 통화)
                        if v is not None:
                            break
                셋.append(v)
                태그들.update(t)
            원천[str(행)] = 셋
            태그[str(행)] = sorted(태그들)
            if all(x is None for x in 셋):
                못찾음.append(행)

    for 행, 후보 in sorted(주식표.items()):
        셋, 태그들 = [], set()
        for i in range(3):
            v, t = None, []
            for one in 후보:
                v, t = _고르기(us, (one,), 잔액뽑기(기준일들[i]))
                if v is not None:
                    break
            셋.append(v)
            태그들.update(t)
        원천[str(행)] = 셋
        태그[str(행)] = sorted(태그들)
        if all(x is None for x in 셋):
            못찾음.append(행)

    # ── 20-F 폴백 — us-gaap 에서 못 찾은 행을 ifrs-full 로 다시 찾는다 ──────
    if ifrs:
        for 뭉치, 뽑기들 in ((IFRS잔액표, [잔액뽑기(d) for d in 기준일들]),
                         (IFRS흐름표, [흐름뽑기(*p) for p in 흐름기간들])):
            for 행, (합산, 후보) in sorted(뭉치.items()):
                if 행 not in 못찾음:
                    continue
                셋, 태그들 = [], set()
                for i in range(3):
                    if 합산:
                        v, t = _고르기(ifrs, 후보, 뽑기들[i], 통화)
                    else:
                        v, t = None, []
                        for one in 후보:
                            v, t = _고르기(ifrs, (one,), 뽑기들[i], 통화)
                            if v is not None:
                                break
                    셋.append(v)
                    태그들.update(t)
                if any(x is not None for x in 셋):
                    원천[str(행)] = 셋
                    태그[str(행)] = ["ifrs:%s" % x for x in sorted(태그들)]
                    못찾음.remove(행)

    # ── **없으면 산술로 구한다.** 지어내는 것이 아니라 재무제표의 셈이다 ──────
    def _값(행, i):
        벌 = 원천.get(str(행)) or [None, None, None]
        return 벌[i] if i < len(벌) else None

    def _채우기(행, 만들기, 어떻게):
        벌 = 원천.get(str(행)) or [None, None, None]
        바뀜 = False
        for i in range(3):
            if 벌[i] is None:
                v = 만들기(i)
                if v is not None:
                    벌[i] = v
                    바뀜 = True
        if 바뀜:
            원천[str(행)] = 벌
            태그[str(행)] = (태그.get(str(행)) or []) + ["계산: %s" % 어떻게]
            if 행 in 못찾음:
                못찾음.remove(행)
            주의.append("**%d행 %s 을(를) 계산으로 채웠습니다** — %s. "
                       "태그가 없어 산술로 구한 값입니다"
                       % (행, 행이름.get(행, ""), 어떻게))

    # ── **판관비(65) 를 잔여와 맞댄다** (2026-09-13, CRM 실측) ─────────────────
    # 합산 계열(SG&A·G&A·S&M·R&D)만 더하면 **구조조정비 같은 별도 영업비용 줄이 빠진다.**
    # 실측(CRM): 21,586/23,338/12,407 — 원문 총영업비용 22,047/23,924/12,581 과 461/586/174
    # (Restructuring) 차이. 스캐폴드 66 = 64 − 65 라 **영업이익이 그만큼 과대**해진다.
    # 잔여(매출 − 매출원가 − 영업이익, 셋 다 태그)가 있을 때만 고친다 — 잔여가 곧 정의상 총영업비용이다.
    #   ① `OperatingExpenses` 가 잔여와 맞으면 그것을 쓴다 (뜻이 회사마다 갈리는 태그라 **맞을 때만**)
    #   ② 합산 + 구조조정비(`RestructuringCharges` 등)가 잔여와 맞으면 그것을 쓴다
    #   ③ 둘 다 아니면 값을 두고 갭을 `주의` 에 적는다 — 메우지 않는다
    _구조조정 = ("RestructuringCharges", "RestructuringCosts",
              "RestructuringCostsAndAssetImpairmentCharges")
    판관보정 = []
    for i in range(3):
        매, 원, 영 = _값(62, i), _값(63, i), _값(66, i)
        if None in (매, 원, 영) or not 매:
            continue
        잔여 = 매 - 원 - 영
        판 = _값(65, i)
        허용 = max(1.0, abs(매) * 0.0005)
        if 판 is not None and abs(판 - 잔여) <= 허용:
            continue
        oe, _t = _고르기(us, ("OperatingExpenses",), 흐름뽑기(*흐름기간들[i]), 통화)
        새, 어떻게 = None, None
        if oe is not None and abs(oe - 잔여) <= 허용:
            새, 어떻게 = oe, "OperatingExpenses(잔여와 일치)"
        else:
            rc, rct = None, []
            for _r in _구조조정:
                rc, rct = _고르기(us, (_r,), 흐름뽑기(*흐름기간들[i]), 통화)
                if rc is not None:
                    break
            if rc is not None and 판 is not None and abs(판 + rc - 잔여) <= 허용:
                새, 어떻게 = 판 + rc, "합산 + %s(잔여와 일치)" % rct[0]
        if 새 is not None:
            판관보정.append((i, 판, 새, 어떻게))
            벌 = 원천.get("65") or [None, None, None]
            벌[i] = 새
            원천["65"] = 벌
            if 65 in 못찾음:
                못찾음.remove(65)
        else:
            주의.append("**65행 판관비 %s열이 잔여(매출 − 매출원가 − 영업이익)와 %s 벌어졌습니다**"
                       "(매출의 %.2f%%). 총영업비용 태그로도 구조조정비로도 안 닫힙니다 — "
                       "10-K/10-Q 손익의 영업비용 줄을 원문으로 세십시오"
                       % ("DEF"[i], format(int((판 or 0) - 잔여), ","),
                          abs((판 or 0) - 잔여) / abs(매) * 100))
    if 판관보정:
        태그["65"] = sorted(set(태그.get("65") or [])) + sorted({"보정: %s" % x[3] for x in 판관보정})
        주의.append("**65행 판관비를 잔여에 맞춰 바꿨습니다** — %s. 합산 계열(SG&A·R&D·S&M·G&A)이 "
                   "구조조정비 같은 별도 영업비용 줄을 빠뜨려 스캐폴드 66(=64−65)이 과대해지는 자리입니다"
                   "(실측 CRM: Restructuring 461/586/174)"
                   % " · ".join("%s열 %s→%s(%s)" % ("DEF"[i], format(int(a or 0), ","),
                                                     format(int(b), ","), c)
                                for i, a, b, c in 판관보정))

    # ── **77행 상각은 세 열을 한 범위(한 태그)로 잡는다** (2026-09-13, CRM 실측) ─────────
    # 옛 판은 열마다 후보를 앞에서부터 훑어 **열마다 다른 태그**가 잡혔다. 실측(CRM):
    # D·E 는 `DepreciationDepletionAndAmortization`(유형자산 상각만 1,000/1,200), F 는 10-Q 에 그 태그가
    # 없어 `DepreciationAndAmortization`(현금흐름표 전체 1,951 — 인수무형 상각 포함)이 잡혔다.
    # 상각률·CapEx 비율이 F 열에서만 세 배로 튄다. 그래서:
    #   ① 세 열을 다 가진 후보 중 **목록 앞의 것**을 기준 태그로 삼는다(없으면 가장 많은 열을 가진 것)
    #   ② 기준 태그가 빈 열은 **다른 태그가 기준 태그와 겹치는 열에서 값이 맞을 때만**(±0.5%) 메운다
    #      — 같은 범위라는 증거가 있을 때만 잇는다(sec_앵커 의 이음 규칙과 같다)
    #   ③ 못 메운 열은 비우고 적는다
    if not any("ifrs:" in t for t in (태그.get("77") or [])):
        후보77 = 흐름표[77][1]
        값표 = {}
        for t in 후보77:
            값표[t] = [_고르기(us, (t,), 흐름뽑기(*흐름기간들[i]), 통화)[0] for i in range(3)]
        가진수 = {t: sum(1 for v in 값표[t] if v is not None) for t in 후보77}
        if any(가진수.values()):
            기준 = sorted(후보77, key=lambda t: (-(가진수[t] == 3), -가진수[t],
                                              후보77.index(t)))[0]
            셋 = list(값표[기준])
            쓴 = [기준]
            for i in range(3):
                if 셋[i] is not None:
                    continue
                for t in 후보77:
                    if t == 기준 or 값표[t][i] is None:
                        continue
                    겹 = [j for j in range(3) if 셋[j] is not None and 값표[t][j] is not None]
                    if 겹 and all(abs(값표[t][j] - 셋[j]) <= abs(셋[j]) * 0.005 for j in 겹):
                        셋[i] = 값표[t][i]
                        쓴.append(t)
                        break
            옛태그 = sorted(태그.get("77") or [])
            옛값 = list(원천.get("77") or [None, None, None])
            원천["77"] = 셋
            태그["77"] = sorted(set(쓴))
            if 옛값 != 셋:
                주의.append(
                    "**77행 상각을 한 범위로 통일했습니다** — 옛 조립은 열마다 다른 태그(%s)를 잡아 %s 였고, "
                    "이제 기준 태그 `%s` 로 %s 입니다. 다른 태그로는 기준 태그와 겹치는 열에서 값이 맞을 때만 "
                    "메웁니다(실측 CRM: 유형자산분 1,000/1,200 과 현금흐름표 전체 1,951 이 한 줄에 섞였다)"
                    % (" · ".join(옛태그) or "없음",
                       " / ".join("—" if v is None else format(int(v), ",") for v in 옛값), 기준,
                       " / ".join("—" if v is None else format(int(v), ",") for v in 셋)))
            if any(v is None for v in 셋):
                주의.append("**77행 상각 %s열이 비었습니다** — 기준 태그 `%s` 가 그 기간에 없고, 같은 범위라고 "
                           "확인되는 다른 태그도 없습니다. 원문 현금흐름표로 채우십시오(범위가 다른 태그로 "
                           "메우지 않습니다)" % ("·".join("DEF"[i] for i in range(3) if 셋[i] is None), 기준))
            if 77 in 못찾음 and any(v is not None for v in 셋):
                못찾음.remove(77)
            if 기준 in ("DepreciationDepletionAndAmortization", "DepreciationAndAmortization",
                      "DepreciationAmortizationAndAccretionNet") and \
                    all(v is None for v in (원천.get("78") or [None] * 3)):
                주의.append("**77행이 `%s`(현금흐름표 상각 합계일 수 있다)이고 78행(무형자산상각)이 비었습니다** — "
                           "77 에 인수무형 상각이 들어 있을 수 있습니다. 손익 각주·무형자산 주석의 상각액으로 "
                           "떼어 78 에 두십시오(실측 CRM: 3,477 − 인수무형 1,651 = 1,826)" % 기준)

    # 영업이익 = 매출 − 매출원가 − 판관비. 「Operating income」 소계를 XBRL 에 안 내는
    # 회사가 미국에는 흔하다(제약·에너지·리츠·보험).
    def _영업(i):
        매, 원, 판 = _값(62, i), _값(63, i), _값(65, i)
        if 매 is None:
            return None
        # 원가(63)가 비면 계산하지 않는다 — 실측(XOM): 63 이 없는데 판관만 빼서
        # 영업이익 195,988(매출의 97%)이 나왔고 범위 검사(±100%)도 통과해 버렸다.
        # 판관(65)만 빈 것은 허용한다 — 63 이 총비용 꼴인 회사(LMT)가 있다.
        if 원 is None:
            return None
        후 = 매 - 원 - (판 or 0.0)
        # 매출 대비 −100%~+100% 밖이면 재료 중 하나가 다른 뜻이다. **버린다.**
        return 후 if (매 and -1.0 <= 후 / 매 <= 1.0) else None
    _채우기(66, _영업, "매출 − 매출원가 − 판관비")

    # 폴백 2단 — 63(원가)이 없는 회사(XOM·CVX 꼴: 원유구입 등 커스텀 스택)는
    # **총비용(CostsAndExpenses)에서 이자를 되돌려** 재구성한다. 이자가 총비용에
    # 없는 회사(별도 표기)면 그대로 빼기만 한다 — 어느 쪽인지 결과에 적는다.
    def _영업2(i):
        매 = _값(62, i)
        if 매 is None:
            return None
        총, _ = _고르기(us, ("CostsAndExpenses",), 흐름뽑기(*흐름기간들[i]), 통화)
        if 총 is None:
            return None
        이자, _ = _고르기(us, ("InterestExpense",), 흐름뽑기(*흐름기간들[i]), 통화)
        후 = 매 - 총 + (이자 or 0.0)
        return 후 if -1.0 <= 후 / 매 <= 1.0 else None
    if any(v is None for v in (원천.get("66") or [None] * 3)):
        _채우기(66, _영업2, "매출 − 총비용(CostsAndExpenses) + 이자(폴백 2단)")

    # 부채총계 = 자산총계 − 자본총계(비지배 포함). `Liabilities` 를 안 내는 회사가 있다.
    def _부채(i):
        자산 = _값(33, i)
        자본, _ = _고르기(us, ("StockholdersEquityIncludingPortionAttributableTo"
                            "NoncontrollingInterest", "StockholdersEquity"),
                       잔액뽑기(기준일들[i]))
        if 자산 is None or 자본 is None:
            return None
        return 자산 - 자본
    _채우기(55, _부채, "자산총계 − 자본총계(비지배 포함)")

    # 유통주식수 — `dei` 네임스페이스의 표지 값이 가장 정확하다(10-K 표지의 그 숫자다).
    dei = (cf.get("facts") or {}).get("dei") or {}
    def _주식(i):
        arr = ((dei.get("EntityCommonStockSharesOutstanding") or {})
               .get("units") or {}).get("shares") or []
        후보 = [x for x in arr if x.get("end")]
        if not 후보:
            return None
        후보.sort(key=lambda x: (x.get("end") or ""))
        # 기준일보다 뒤로 넘어가지 않는 마지막 값
        쓸 = [x for x in 후보 if (x.get("end") or "") <= 기준일들[i]] or 후보[:1]
        # **낡은 표지를 무경고로 쓰지 않는다** — 실측(V): dei 표지가 2010년에서
        # 멈춰 있어(클래스별 커스텀 축 공시로 전환) Class A 만 세던 16년 전 값
        # 469M 이 분모가 됐고 주당가치가 4배 부풀었다. 표지가 기준일에서 550일
        # (약 1.5년) 넘게 낡았으면 버리고 빈 채로 낸다 — 원문 표지를 열라는 신호다.
        끝 = 쓸[-1].get("end") or ""
        기준 = 기준일들[i] or ""
        if 끝 and 기준:
            import datetime as _dt
            낡음 = (_dt.date.fromisoformat(기준) - _dt.date.fromisoformat(끝)).days
            if 낡음 > 550:
                주의.append("**97행 dei 표지가 %d일 낡아 버렸습니다**(%s — 기준일 %s). "
                          "클래스별 커스텀 공시로 전환한 회사면 companyfacts 에 최신 "
                          "주식수가 없습니다 — 10-Q 원문 표지에서 클래스별로 세십시오"
                          % (낡음, 끝, 기준))
                return None
        return float(쓸[-1]["val"])
    _채우기(97, _주식, "dei:EntityCommonStockSharesOutstanding(표지 기재)")

    # **이중 주식 구조면 클래스별로 갈려 집계에서 빠진다.** 실측(META): dei 에
    # `EntityPublicFloat` 만 있고 주식수가 없다. 그때는 가중평균을 쓰되 **그것이
    # 기말 유통주식수가 아니라는 사실을 밝힌다** — 주당가치의 분모라 차이가 값에 얹힌다.
    def _가중주식(i):
        v, _t = _고르기(us, ("WeightedAverageNumberOfSharesOutstandingBasic",
                           "WeightedAverageNumberOfDilutedSharesOutstanding"),
                      흐름뽑기(*흐름기간들[i]))
        return v
    if 97 in 못찾음:
        _채우기(97, _가중주식,
              "**가중평균** 주식수 — 이중 주식 구조라 클래스별로 갈려 "
              "기말 유통주식수를 못 잡았습니다. 기말 수와 다르니 표지에서 확인하십시오")

    # ── **리스 겹침** — 17행이 금융리스를 이미 품었는지 본다 ───────────
    if any("FinanceLeaseRightOfUseAsset" in t for t in 태그.get("17", [])):
        주의.append(
            "**17행(유형자산)이 금융리스 사용권자산을 품은 태그로 잡혔습니다** — "
            "`%s`. 19행(사용권자산)에 금융리스를 또 담으면 **이중계상**입니다. "
            "19행은 운용리스만 두었는지 확인하십시오"
            % (태그["17"][0] if 태그.get("17") else "?"))
        # 19행에서 금융리스를 뺀다 — 지어내는 것이 아니라 겹침을 없애는 것이다
        if "FinanceLeaseRightOfUseAsset" in (태그.get("19") or []):
            셋, _ = [], None
            for i in range(3):
                v, _t = _고르기(us, ("OperatingLeaseRightOfUseAsset",),
                              잔액뽑기(기준일들[i]))
                셋.append(v)
            원천["19"] = 셋
            태그["19"] = ["OperatingLeaseRightOfUseAsset"]
            주의.append("19행에서 금융리스 사용권자산을 뺐습니다 — "
                       "17행이 이미 품고 있어서입니다")

    # ── **소계 대조로 겹침과 빠짐을 가린다** (2026-09-13, CRM 실측) ─────────────────
    # companyfacts 에는 「그 금액이 재무상태표 어느 줄에 들어 있나」가 없다(확장 목록은 숫자가 아니라 안 온다).
    # 그래서 **공시 소계와 행 합을 맞대어** 그 금액 하나로 차이가 정확히 닫힐 때만 움직인다.
    #   · 금융리스부채 — 39·47 에 더했는데 표면에서는 34(AP·accrued)·53(기타비유동부채) 안에 들어 있다.
    #     실측(CRM FY2026): 유동 275 · 비유동 260 이 두 번 세어져 **부채가 535 과대**. 행 합 − 소계 = 금융리스
    #     일 때만 **표면 묶음 줄(34/35/43 · 53)에서 뺀다** — 39·47 은 리스 합산 행이라 그대로 둔다.
    #   · 자본화 계약원가(판매수수료) — 표면에 따로 선 줄인데 매핑이 없어 **유동자산 소계가 안 맞았다**
    #     (CRM 유동 1,971/2,075/2,074 · 비유동 2,475/2,985/2,870). 행 합 + 그 금액 = 소계일 때만 15·31 에 더한다.
    #     다른 줄(기타자산) 안에 이미 들어 있는 회사면 소계가 먼저 맞으므로 더하지 않는다.
    def _잔(t, i):
        return _고르기(us, (t,), 잔액뽑기(기준일들[i]), 통화)[0]

    def _맞나(소계, 합):
        return abs(소계 - 합) <= max(1.0, abs(소계) * 1e-5)

    def _표면줄닫기(이름, i, 소계, 합, 소계보정):
        """`소계후보` 의 조합(묶음마다 0 또는 태그 하나)이 차이를 정확히 닫으면 넣고 새 합을 낸다.

        닫는 조합이 여럿이고 행마다 넣을 금액이 갈리면 **넣지 않고** 알린다 — 어느 것이 표면 줄인지 숫자로 못 가린다.
        이미 다른 행에 쓴 태그는 후보에서 뺀다(두 번 세지 않는다)."""
        import itertools                                    # noqa: PLC0415
        쓴태그 = {t for v in 태그.values() for t in (v or [])}
        묶음들 = []
        for 행, 이름들 in 소계후보[이름]:
            길 = [None]                                       # 이 묶음을 안 쓰는 길
            for t in 이름들:
                if t in 쓴태그:
                    continue
                금 = _잔(t, i)
                if not 금:
                    continue
                품 = [r for r in _묶음품는행.get(t, ()) if _값(r, i)]
                for k in range(len(품) + 1):
                    for 뺄 in itertools.combinations(품, k):
                        차 = 금 - sum(_값(r, i) for r in 뺄)
                        if 차 > 0 or not 뺄:
                            길.append((행, t, 뺄, 차))
            if len(길) > 1:
                묶음들.append(길)
        if not 묶음들:
            return 합
        풀이 = []
        for 고름 in itertools.product(*묶음들):
            쓴 = [g for g in 고름 if g is not None]
            if 쓴 and _맞나(소계, 합 + sum(g[3] for g in 쓴)):
                풀이.append(쓴)
        if not 풀이:
            return 합

        def _행별(쓴):
            d = {}
            for 행, _t, _뺄, 차 in 쓴:
                d[행] = d.get(행, 0.0) + 차
            return sorted((r, round(v)) for r, v in d.items())
        if len({tuple(_행별(s)) for s in 풀이}) > 1:
            주의.append("**%s열 %s — 표면 줄 후보 조합 %d개가 차이 %s 을(를) 똑같이 닫아 넣지 않았습니다** — %s. "
                       "어느 것이 표면 줄인지 원문 재무상태표로 가리십시오"
                       % ("DEF"[i], 이름, len(풀이), format(int(소계 - 합), ","),
                          " / ".join(" + ".join("%d행 %s" % (g[0], g[1]) for g in s) for s in 풀이[:4])))
            return 합
        for 행, t, 뺄, 차 in 풀이[0]:
            벌 = 원천.get(str(행)) or [None, None, None]
            벌[i] = (벌[i] or 0.0) + 차
            원천[str(행)] = 벌
            이름표 = t + "".join(" − %s행" % r for r in 뺄)
            태그[str(행)] = sorted(set(태그.get(str(행)) or []) | {"+ %s(소계 대조)" % 이름표})
            if 행 in 못찾음:
                못찾음.remove(행)
            소계보정.append((i, 이름, 행, "더함", 이름표, 차))
            합 += 차
        return 합

    소계대조, 소계보정 = [], []
    for i in range(3):
        자산, 유동자산 = _값(33, i), _잔("AssetsCurrent", i)
        부채, 유동부채 = _값(55, i), _잔("LiabilitiesCurrent", i)
        비유동자산 = _잔("AssetsNoncurrent", i)
        if 비유동자산 is None and None not in (자산, 유동자산):
            비유동자산 = 자산 - 유동자산
        비유동부채 = _잔("LiabilitiesNoncurrent", i)
        if 비유동부채 is None and None not in (부채, 유동부채):
            비유동부채 = 부채 - 유동부채
        for 이름, 소계, 행들, 조정 in (
                ("유동자산", 유동자산, (7, 8, 9, 10, 11, 12, 13, 14, 15),
                 ("더함", "CapitalizedContractCostNetCurrent", (15,))),
                ("비유동자산", 비유동자산, tuple(range(17, 32)),
                 ("더함", "CapitalizedContractCostNetNoncurrent", (31,))),
                ("유동부채", 유동부채, tuple(range(34, 44)),
                 ("뺌", "FinanceLeaseLiabilityCurrent", (34, 35, 43))),
                ("비유동부채", 비유동부채, tuple(range(45, 54)) + (110, 111),
                 ("뺌", "FinanceLeaseLiabilityNoncurrent", (53,)))):
            if 소계 is None:
                continue
            합 = sum((_값(r, i) or 0.0) for r in 행들 if str(r) in 원천)
            if not _맞나(소계, 합):
                방향, 태그명, 자리들 = 조정
                금액 = _잔(태그명, i)
                리스행 = 39 if 태그명.endswith("Current") else 47
                # 금융리스를 뺄 수 있는 것은 그 금액이 실제로 39·47 에 더해졌을 때뿐이다
                if 금액 and 방향 == "뺌" and 태그명 not in (태그.get(str(리스행)) or []):
                    금액 = None
                if 금액:
                    새합 = 합 + 금액 if 방향 == "더함" else 합 - 금액
                    if _맞나(소계, 새합):
                        자리 = None
                        if 방향 == "더함":
                            자리 = 자리들[0]
                        else:
                            # 표면 묶음 줄 — accrued/other 가 붙은 태그로 잡힌 행을 앞에서부터 고른다
                            for r in 자리들:
                                if _값(r, i) is None or _값(r, i) < 금액:
                                    continue
                                if r == 53 or any(w in t for t in (태그.get(str(r)) or [])
                                                  for w in ("Accrued", "Other")):
                                    자리 = r
                                    break
                        if 자리 is not None:
                            벌 = 원천.get(str(자리)) or [None, None, None]
                            벌[i] = (벌[i] or 0.0) + (금액 if 방향 == "더함" else -금액)
                            원천[str(자리)] = 벌
                            태그[str(자리)] = sorted(set(태그.get(str(자리)) or []) |
                                                  {"%s %s(소계 대조)" % ("+" if 방향 == "더함" else "−", 태그명)})
                            if 자리 in 못찾음:
                                못찾음.remove(자리)
                            소계보정.append((i, 이름, 자리, 방향, 태그명, 금액))
                            합 = 새합
            if not _맞나(소계, 합) and 이름 in 소계후보:
                합 = _표면줄닫기(이름, i, 소계, 합, 소계보정)
            소계대조.append({"열": "DEF"[i], "소계": 이름, "공시": 소계, "행합": 합, "차": 소계 - 합,
                         "결과": "일치" if _맞나(소계, 합) else "불일치"})
    # ── **법인세 부호** — 71 − 72 = 계속영업이익 (2026-10-16, S1 리뷰 — dart_원천 과 같은 줄) ─────────
    # 미국 표에는 73(순이익) 행이 없어 계속영업이익(없으면 순이익) 태그와 맞댄다. 71 의 표준 태그가 지분법손익 앞
    # 소계라 그 몫이 끼면 어긋날 수 있다 — 지분법손익을 더해 맞으면 일치로 본다. 「71 + 72 가 맞을 때」만 부호 반전으로 알린다.
    for i in range(3):
        세전, 세 = _값(71, i), _값(72, i)
        if None in (세전, 세):
            continue
        뽑 = 흐름뽑기(*흐름기간들[i])
        순, 순태그 = None, None
        for t in ("IncomeLossFromContinuingOperations", "ProfitLoss", "NetIncomeLoss"):
            v, _t = _고르기(us, (t,), 뽑, 통화)
            if v is not None:
                순, 순태그 = v, t
                break
        if 순 is None:
            continue
        지분 = _고르기(us, ("IncomeLossFromEquityMethodInvestments",), 뽑, 통화)[0] or 0.0
        허용 = max(1.0, abs(세전) * 0.002)
        맞음 = any(abs(세전 - 세 + x - 순) <= 허용 for x in (0.0, 지분))
        반전 = (not 맞음) and abs(세) >= 1 and any(abs(세전 + 세 + x - 순) <= 허용 for x in (0.0, 지분))
        소계대조.append({"열": "DEF"[i], "소계": "법인세차감전 − 법인세비용 = %s" % 순태그, "공시": 순,
                     "행합": 세전 - 세, "차": 순 - (세전 - 세),
                     "결과": "일치" if 맞음 else ("부호 반전 의심" if 반전 else "불일치")})
        if 반전:
            주의.append(
                "**%s열 법인세비용(72)의 부호 반전 의심 — 71 − 72 가 %s(%s)와 어긋나고 71 + 72 가 맞습니다.** "
                "IncomeTaxExpenseBenefit 의 부호가 거꾸로 태깅된 자리일 수 있습니다 — 10-K 의 법인세 주석(effective rate "
                "reconciliation)으로 부호를 확인하고 근거 칸에 적으십시오(스캐폴드 73 = 71 − 72)"
                % ("DEF"[i], 순태그, format(int(순), ",")))
    if 소계보정:
        주의.append(
            "**소계 대조로 %d칸을 고쳤습니다** — %s. 공시 소계와 행 합의 차이가 그 금액 하나로 정확히 닫힐 때만 "
            "움직였습니다(금융리스는 표면 묶음 줄에서 빼고 39·47 리스 행에 남김 · 자본화 계약원가는 15·31 에 더함 · "
            "급여 · 법인세 · 선수수익 · 이연법인세 · 장기투자 표면 줄은 그 조합이 차이를 정확히 닫을 때만 36 · 41 · 43 · 51 · 49 · 53 · 26 · 29 에 더함). "
            "**어느 줄에 들어 있는지는 원문 주석으로 확인하십시오**(실측 CRM: 10-K 주석6)"
            % (len(소계보정), " · ".join("%s열 %d행 %s %s %s" % ("DEF"[i], 자리, "+" if 방 == "더함" else "−",
                                                           format(int(금), ","), t)
                                        for i, _n, 자리, 방, t, 금 in 소계보정)))
    # 법인세 줄의 단순 불일치(지분법 · 중단영업 · 비지배 몫)는 13번 행 문제가 아니라 소계 어긋남에 세지 않는다 — 부호 반전만 따로 알린다
    어긋난 = [x for x in 소계대조 if x["결과"] != "일치" and not (x["소계"].startswith("법인세") and x["결과"] == "불일치")]
    if 어긋난:
        주의.append(
            "**소계와 행 합이 %d곳 어긋납니다** — %s. 13번 행에 매핑 안 된 표면 줄이 있거나 두 번 센 줄이 "
            "있습니다. **비슷한 값으로 메우지 않습니다** — `tags_us_gaap.txt` 와 원문 재무상태표로 가리십시오"
            % (len(어긋난), " · ".join("%s열 %s 차 %s" % (x["열"], x["소계"], format(int(x["차"]), ","))
                                      for x in 어긋난[:6])))

    # ── **자본총계의 뜻** ───────────────────────────────────────────
    if 원천.get("56") and any(x is not None for x in 원천["56"]):
        주의.append("56행 자본총계는 `StockholdersEquity`(**지배주주 지분만**)입니다. "
                   "비지배지분 포함 총자본이 필요하면 "
                   "`StockholdersEquityIncludingPortionAttributableToNoncontrolling"
                   "Interest` 로 바꾸십시오")

    # **근접으로 잡았으면 그 사실이 보여야 한다.** 52/53주 회계연도는 정상이지만,
    # 결산월을 잘못 짚어 엉뚱한 날을 근접으로 잡은 것일 수도 있다.
    if 쓴날짜:
        주의.append("**날짜를 근접(±%d일)으로 잡은 자리가 있습니다** — %s. "
                   "52/53주 회계연도면 정상이고, 아니면 결산월 판정을 보십시오"
                   % (근접, " · ".join("%s→%s" % p for p in sorted(쓴날짜)[:6])))

    # ── **SIC 코드 신호 — 금융업(6000번대)은 관문 ① 부터 다시 본다** ─────────
    # 실측(JPM): `Revenues` 태그가 있어 매출이 잡히고, 산술 폴백이 「영업이익」까지
    # 만들어 줬다 — 그러나 은행의 이자수익·이자비용 구조에서 그 값은 FCFF 재료가
    # 아니다. submissions.json 의 SIC 로 업종을 미리 알린다(국내 dart_fetch 의
    # 금융업 계정 경고와 같은 자리).
    try:
        _sub길 = os.path.join(RAW, "submissions.json")
        if os.path.exists(_sub길):
            _sub = json.load(io.open(_sub길, encoding="utf-8"))
            _sic = "%s" % (_sub.get("sic") or "")
            if _sic[:1] == "6":
                주의.append(
                    "**SIC %s(%s) — 금융업입니다.** 매출·영업이익이 태그로 잡혀도 "
                    "이자수익이 영업수익이고 차입이 원재료라 「기업가치 = 영업가치 + "
                    "비영업자산」 구조가 성립하지 않습니다. **관문 ①에서 현금흐름"
                    "할인법이 성립하는 회사인지부터 판정하십시오**"
                    % (_sic, _sub.get("sicDescription") or "?"))
    except Exception:                                        # noqa: BLE001
        pass

    빈필수 = [행 for 행 in 필수 if 행 in 못찾음]
    # **필수 행이 여럿 비는 것은 그 자체가 신호다.** 태그를 더 뒤져도 안 나오는 이유는
    # 대개 **그 업종의 재무제표가 우리 그릇과 다르게 생겼기 때문**이다 — 보험사에
    # 「매입채무」가 없고, 리츠의 자산은 유형자산이 아니라 투자부동산이며, 은행은
    # 매출 자체가 이자수익이다. 실측: BRK-B(보험 지주) 4개 · O(리츠) 1개가 남았다.
    if len(빈필수) >= 3:
        주의.append(
            "**꼭 있어야 하는 행이 %d개 비었습니다** — %s. 태그를 더 뒤져도 안 나오면 "
            "**이 회사의 재무제표가 열세 시트의 그릇과 다르게 생긴 것**입니다"
            "(보험·리츠·은행이 그렇습니다). 태그 문제로 보고 시간을 쓰기 전에 "
            "**관문 ①에서 현금흐름할인법이 성립하는 회사인지부터 판정하십시오.**"
            % (len(빈필수),
               " · ".join("%d %s" % (r, 행이름.get(r, "")) for r in 빈필수)))
    # ── 태그 끊김 감지 — 열0·1은 있는데 최신 열만 빈 잔액 행(실측: T 45행 →
    # 부채 134.6B 누락으로 순현금 착시 · CVX 7·45행). 값을 메우지 않고 알린다.
    for 행 in (7, 37, 38, 45, 46, 55, 56):
        벌 = 원천.get(str(행)) or [None, None, None]
        if 벌[0] is not None and 벌[1] is not None and 벌[2] is None:
            주의.append(
                "**%d행 %s — 최신 열만 비었습니다(태그 끊김 의심).** 회사가 태그를 "
                "갈아탄 자리일 수 있습니다(실측: T 의 장기부채가 "
                "…AndCapitalLeaseObligations 로 이동해 브리지가 순현금으로 착시). "
                "**10-Q 원문 BS 로 그 열을 덮으십시오** — 직전 값으로 메우지 않습니다"
                % (행, 행이름.get(행, "")))
    # ── 상각 태그 병존 경고 — 채택값의 2배가 넘는 다른 후보가 있으면 알린다
    # (실측: MCD 가 DepreciationDepletionAndAmortization 457 을 채택했는데 전체는
    #  DepreciationAndAmortization 2,199 — 상각이 1/5 로 잡힐 뻔).
    _상77 = 원천.get("77") or [None, None, None]
    _채택77 = _상77[1]                     # 연간 열끼리 비교(반기와 섞으면 오발)
    if _채택77:
        for _t in ("DepreciationDepletionAndAmortization",
                   "DepreciationAmortizationAndAccretionNet",
                   "DepreciationAndAmortization", "Depreciation"):
            _v, _ = _고르기(us, (_t,), 흐름뽑기(*흐름기간들[1]), 통화)
            if _v and _채택77 and _v > _채택77 * 2:
                주의.append(
                    "**77행 상각 — 채택값(%s)의 2배가 넘는 다른 태그가 있습니다** "
                    "(`%s` = %s). 채택 태그가 부분(세그먼트·일부 자산)일 수 있으니 "
                    "**큰 쪽이 전체인지 원문으로 확인하십시오**(실측: MCD 457 vs 2,199)"
                    % (format(int(_채택77), ","), _t, format(int(_v), ",")))
                break
    # 1.1.3(A5) — 리스 구분(운용 · 금융)을 잔액일마다 따로 적는다. 39 · 47 · 19 는 둘을 합친 행이라 US GAAP 운용리스(리스료가 영업비용에 남는다)를
    #   브리지에서 또 빼면 이중 차감이다 — `리스판정.py` 가 이 칸을 읽어 회계기준 · 리스 구분으로 판정하고 고친다(행 값은 여기서 바꾸지 않는다)
    리스구분 = {"회계기준": "US GAAP" if us else ("IFRS" if ifrs else None), "잔액일": list(기준일들)}
    for 칸, t in (("운용부채유동", "OperatingLeaseLiabilityCurrent"), ("운용부채비유동", "OperatingLeaseLiabilityNoncurrent"),
                 ("금융부채유동", "FinanceLeaseLiabilityCurrent"), ("금융부채비유동", "FinanceLeaseLiabilityNoncurrent"),
                 ("운용사용권", "OperatingLeaseRightOfUseAsset"), ("금융사용권", "FinanceLeaseRightOfUseAsset")):
        리스구분[칸] = [(_고르기(us, (t,), 잔액뽑기(기준일들[i]), 통화)[0] if us else None) for i in range(len(기준일들))]
    리스구분["태그"] = {k: 태그.get(k) for k in ("17", "19", "39", "47")}
    return {"원천": 원천, "태그": 태그, "못찾음": 못찾음, "리스구분": 리스구분,
            "못찾은이름": {str(r): 행이름.get(r, "?") for r in 못찾음},
            "빈필수": 빈필수,
            "빈필수이름": {str(r): 행이름.get(r, "?") for r in 빈필수},
            "주의": 주의, "통화": 통화, "소계대조": 소계대조,
            "잔액일": 기준일들, "흐름기간": 흐름기간들}


def 회사분기말들(cf):
    """회사가 실제로 공시한 기간 끝날(10-Q · 10-K · 20-F · 6-K 의 `Assets` 잔액 날짜) — 오름차순."""
    날 = set()
    for ns in ("us-gaap", "ifrs-full"):
        f = ((cf.get("facts") or {}).get(ns) or {}).get("Assets") or {}
        for arr in (f.get("units") or {}).values():
            for x in arr:
                if x.get("form") in ("10-Q", "10-K", "10-Q/A", "10-K/A", "20-F", "6-K", "40-F") and x.get("end") and "start" not in x:
                    날.add(x["end"])
    return sorted(날)


def 분기말어긋남(cf, 기준일, 근접=10):
    """기준일이 회사의 어떤 분기 종료일(±근접일)에도 맞지 않으면 경보 문장, 맞으면 None.
    회사의 분기말은 공시된 끝날에서 1년 단위로 이어 보아(아직 안 낸 분기도) 가장 가까운 앞뒤 둘을 제안한다."""
    날들 = 회사분기말들(cf)
    if not 날들:
        return None
    d = datetime.date.fromisoformat(기준일)
    실제 = {datetime.date.fromisoformat(e) for e in 날들[-12:]}
    후보 = set(실제)
    for x in 실제:                                                 # 아직 안 낸 분기 — 한 해 앞뒤로 이어 본다(실제 끝날과 겹치지 않는 것만)
        for k in (-1, 1):
            try:
                y = x.replace(year=x.year + k)
            except ValueError:                                     # 2/29
                y = x.replace(year=x.year + k, day=28)
            if not any(abs((y - z).days) <= 근접 for z in 실제):
                후보.add(y)
    if any(abs((y - d).days) <= 근접 for y in 후보):
        return None
    앞 = max((y for y in 후보 if y < d), default=None)
    뒤 = min((y for y in 후보 if y > d), default=None)
    return ("**기준일 %s 이 회사의 분기 종료일이 아닙니다** — 공시된 기간 끝날에서 이어 본 가까운 분기말은 %s 입니다. "
            "기준일을 그 가운데 하나로 고치거나(그때 시장 자료 · 유사기업 · 시세의 기준일도 같이 옮길지 정하십시오), "
            "기준일은 두고 실적 열을 직전 분기말로 두십시오. 셋째 열이 빈 것은 태그 문제가 아닙니다 — 없는 태그를 찾거나 "
            "다른 기간 값으로 손으로 메우지 마십시오"
            % (기준일, " · ".join(y.isoformat() for y in (앞, 뒤) if y)))


def _기간축():
    """곁의 `기간축.py` — 52/53주 판정(가까운 월말 · 결산일 평가 · 결산월 어긋남)을 기간 축과 같은 함수로 한다(1.1.9)."""
    여기 = os.path.dirname(os.path.abspath(__file__))
    if 여기 not in sys.path:
        sys.path.insert(0, 여기)
    import 기간축 as _축                                   # noqa: PLC0415
    return _축


def _결산일평가(기준일, 결산월, 근접=10):
    """재무기준일이 회계연도 말(그 날 또는 가장 가까운 월말(±근접일 — 52/53주 회계연도)이 결산월의 말일)이면 그 회계연도의 끝 해, 아니면 None.
    판정은 `기간축.결산일평가` 하나다 — 원천 조립과 기간 축이 갈리지 않는다(1.1.9)."""
    return _기간축().결산일평가(기준일, 결산월, 근접)


def _직전(기준일, 결산월, 반기):
    """실적 3열의 날짜를 만든다 — 직전 두 사업연도 + 기준일까지의 누계 기간.

    **재무기준일이 회계연도 말이면 결산일 평가 꼴**(2026-11-05 U-01) — 반기 · 잔여 열이 없고 실적 세 열이 모두 연간이다:
    잔액 [FY−2 · FY−1 · 기준일] · 흐름 [FY−2 · FY−1 · FY 연간]. 옛 판은 이때도 [FY−1 · FY · 기준일] 로 세워 셋째 흐름 기간이
    (FY 말 다음 날 ~ FY 말) 빈 기간이 되고 잔액 열이 겹쳤다(FY 가 두 번 · FY−2 빠짐). 회계연도 말은 ±10일로 본다 —
    52/53주 회계연도의 끝날(예: 9월 결산의 9-26 · 12월 결산의 다음 해 1-2)도 결산일이다.
    재무기준일이 회계연도 가운데(분기 말)면 종전 그대로다."""
    d = datetime.date.fromisoformat(기준일)
    끝해 = d.year if (d.month, d.day) >= (결산월, 28) else d.year - 1
    말일 = {1: 31, 3: 31, 5: 31, 7: 31, 8: 31, 10: 31, 12: 31,
           4: 30, 6: 30, 9: 30, 11: 30, 2: 28}[결산월]
    FY = lambda y: "%04d-%02d-%02d" % (y, 결산월, 말일)
    결 = _결산일평가(기준일, 결산월)
    if 결 is not None:
        시0 = lambda y: (datetime.date(y, 결산월, 말일) + datetime.timedelta(days=1)).isoformat()
        return ([FY(결 - 2), FY(결 - 1), 기준일],
                [(시0(결 - 3), FY(결 - 2)), (시0(결 - 2), FY(결 - 1)), (시0(결 - 1), 기준일)])
    잔액 = [FY(끝해 - 1), FY(끝해), 기준일]
    시 = lambda y: (datetime.date(y, 결산월, 말일) +
                   datetime.timedelta(days=1)).isoformat()
    흐름 = [(시(끝해 - 2), FY(끝해 - 1)), (시(끝해 - 1), FY(끝해)),
          (시(끝해), 기준일)]
    if not 반기:
        흐름[2] = (시(끝해), 기준일)
    return 잔액, 흐름


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--기준일", "--재무기준일", dest="기준일", default=None,
                    help="재무기준일 F YYYY-MM-DD(예: 2026-06-30) — 잔액 열 · 흐름 기간이 서는 날(평가기준일 전에 제출된 마지막 정기 보고의 "
                         "기간 끝 · 옛 이름 --기준일 은 지금 뜻 그대로)")
    ap.add_argument("--평가기준일", default=None, help="평가기준일 T YYYY-MM-DD — 산출 머리에만 적는다(조립 값은 바꾸지 않는다)")
    ap.add_argument("--가정", default=None, help="가정 파일 — 날짜 인자를 비우면 기준일.py 로 F · T 를 푼다(F 가 없으면 F = T)")
    ap.add_argument("--결산월", type=int, default=0,
                    help="비우면 companyfacts 에서 감지한다")
    ap.add_argument("--반기", action="store_true",
                    help="셋째 열이 기준일까지의 누계 기간이면(기본 동작)")
    ap.add_argument("--입력", default=os.path.join(RAW, "companyfacts.json"))
    ap.add_argument("--출력", default=os.path.join(RAW, "원천_조립.json"),
                    help="산출 경로(기본: _raw/원천_조립.json)")
    a = ap.parse_args()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import 기준일인자 as _기인                                  # noqa: PLC0415 — 날짜 둘(2026-10-25)
    a.기준일 = _기인.풀기(a.기준일, a.가정, _기인.재무, 인자="--기준일")
    a.평가기준일 = _기인.풀기(a.평가기준일, a.가정, _기인.평가, 인자="--평가기준일")
    if not a.기준일:
        ap.error("--기준일(재무기준일) 또는 --가정 이 있어야 합니다")

    if not os.path.exists(a.입력):
        sys.exit("companyfacts.json 이 없습니다: %s — sec_fetch.py 를 먼저 도십시오"
                 % a.입력)
    cf = json.load(io.open(a.입력, encoding="utf-8"))
    # **결산월을 고정하지 않는다.** Apple 은 9월, Microsoft 는 6월 결산이다.
    # `sec_앵커.py` 와 **같은 판정 함수**를 쓴다 — 두 도구가 갈리면 안 된다.
    결산월 = a.결산월
    if not 결산월:
        try:
            import sec_앵커
            결산월 = sec_앵커.결산월_감지(cf.get("facts") or {})
            print("결산월 감지: %d월" % 결산월)
        except Exception:                                    # noqa: BLE001
            결산월 = 12
            print("결산월을 못 감지해 12월로 둡니다 — `--결산월` 로 지정할 수 있습니다")
    # 52/53주(1.1.9) — 결산월이 재무기준일과 어긋나면(가까운 월말이 그 결산월의 회계연도 말도 분기 말도 아님) 흐름 열이 통째로 빈다.
    # 기간 축과 같은 판정(`기간축.결산월어긋남`)으로 멈추고 바른 결산월을 알린다
    어긋 = _기간축().결산월어긋남(a.기준일, 결산월)
    if 어긋:
        sys.exit("결산월 오류 — %s" % 어긋)
    잔액일, 흐름기간 = _직전(a.기준일, 결산월, True)
    결산일 = _결산일평가(a.기준일, 결산월) is not None
    if 결산일:
        print("재무기준일 %s 이 회계연도 말입니다 — 결산일 평가 꼴(실적 세 열 연간 · 반기 · 잔여 열 없음)" % a.기준일)
    out = 조립(cf, 잔액일, 흐름기간)
    out["결산일평가"] = 결산일
    # **기준일이 회사의 분기 종료일인가 — 태그 경보보다 먼저 본다** (2026-10-16, S1 리뷰).
    # 1월 결산 회사(NVDA · CRM)를 6/30 으로 돌리면 셋째 열이 통째로 비고 「태그 끊김」이 일곱 줄 뜬다 — 태그가 아니라
    # 기준일이 회사의 분기말과 어긋난 것이다. 그러면 없는 태그를 찾느라 상한을 쓰거나 다른 기간 값으로 손으로 메운다.
    어긋 = 분기말어긋남(cf, a.기준일)
    if 어긋:
        끊김 = [s for s in out["주의"] if "태그 끊김 의심" in s]
        out["주의"] = [s for s in out["주의"] if "태그 끊김 의심" not in s]
        out["주의"].insert(0, 어긋 + (" (이 어긋남 때문에 「최신 열만 비었습니다(태그 끊김 의심)」 %d줄을 내리지 않았습니다 — "
                                    "기준일을 고친 뒤 다시 도십시오)" % len(끊김) if 끊김 else ""))
        out["기준일_분기말어긋남"] = True
        print("  ⚠ " + 어긋)

    out["재무기준일"] = a.기준일                                    # 날짜 둘(2026-10-25) — 잔액일 끝 = F
    if a.평가기준일:
        out["평가기준일"] = a.평가기준일
    dst = a.출력
    io.open(dst, "w", encoding="utf-8").write(
        json.dumps(out, ensure_ascii=False, indent=1))

    print("잔액 기준일 %s" % " · ".join(잔액일))
    print("흐름 기간   %s" % " · ".join("%s~%s" % p for p in 흐름기간))
    print()
    for 행 in sorted((int(k) for k in out["원천"]), key=int):
        셋 = out["원천"][str(행)]
        print("%3d %-22s %16s %16s %16s  %s"
              % (행, 행이름.get(행, ""),
                 *["{:,.0f}".format(v) if v is not None else "—" for v in 셋],
                 " · ".join(out["태그"][str(행)]) or "**못 찾음**"))
    if out["주의"]:
        print()
        for s in out["주의"]:
            print("  ※ %s" % s)
    if out["빈필수"]:
        print()
        print("  ★ **꼭 있어야 하는데 빈 행** — %s"
              % " · ".join("%d %s" % (r, 행이름.get(r, "?")) for r in out["빈필수"]))
        print("     태그를 가정하지 말고 `tags_us_gaap.txt` 를 훑어 실제 이름을 "
              "찾으십시오. **비슷한 값으로 메우지 않습니다.**")
    print()
    print("저장: %s" % dst)


if __name__ == "__main__":
    main()

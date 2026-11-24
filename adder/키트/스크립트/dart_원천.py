# -*- coding: utf-8 -*-
"""국내 종목 **원천(13번) 조립** — 이미 받아 둔 `_raw/dart_재무_*.json` 만 읽는다.

**왜 만들었나.** `sec_원천.py`(미국)의 짝이다. 국내도 회차마다 계정 매핑을 손으로
다시 짰다. 대부분은 IFRS 표준 태그(`account_id`)로 기계적으로 잡히는데, 그 기계적인
부분까지 매번 손으로 하느라 **판단이 정말 필요한 자리에 쓸 시간이 줄었다.**

**이 도구가 하는 일과 안 하는 일**
  한다   IFRS 표준 태그로 잡히는 행을 잡는다. 잡은 근거(태그·계정명)를 함께 낸다
         **태그와 계정명이 어긋나면 알린다** — 실측(HMM): 「장기차입금」의 태그가
         `ifrs-full_NoncurrentPortionOfNoncurrentLoansReceivable` 이다. 받을 돈을
         가리키는 태그에 줄 돈 이름이 붙어 있다. 태그만 믿으면 자산을 부채로 읽는다
         **꼭 있어야 하는데 빈 행**을 이름 대어 낸다
         **소계를 공시 소계와 맞대어 빠진 금액을 낸다**(2026-09-13 신설 — 아래)
         **영업수익/영업비용 단일 표시 회사를 알아채 63·65 를 스위치대로 붓는다**(같은 날)
         **앵커 네 줄(매출·매출원가·판관비·영업이익)을 같은 규칙으로 낸다**(같은 날)
  안 한다 **「기타」 계열을 배분하지 않는다.** 기타유동부채·기타금융부채는 주석을
         열어야 무엇이 들었는지 안다(리스인지 예수금인지 미지급금인지). 그것은
         **운전자본으로 갈지 이자부부채로 갈지를 가르는 판단**이라 사람의 몫이다.
         후보만 금액과 함께 내고 배분하지 않는다. **지어내지 않는다.**

## 2026-09-13 수리 (펄어비스 실측 — A2a 가 손으로 메운 자리)
- **dart_ 확장 태그가 표에 없어 행이 통째로 비었다.** 비유동 FVPL `dart_NonCurrentFairValueFinancialAsset`
  (1,976억 — **자산의 15.4%**)·유동 FVPL `dart_CurrentFinancialAssetDesignationAsAtFairValueThroughProfitOrLoss`·
  장기금융상품 `dart_LongTermDepositsNotClassifiedAsCashEquivalents` → 28·13·22 행.
- **아예 표에 없던 행**: 12·26·41·49·50·52(잔액) · 67·69·70·74(손익) · 79·82·83(현금흐름).
- **소계 행**(16·32·44·54·58·59·73)은 스캐폴드에서 수식칸이라 붓지 않는다 — `검산행` 으로 따로 내고
  행 합과 맞댄다(`소계대조`). 이 대조가 있었으면 15% 누락이 첫 실행에서 드러났다.
- 8행 태그가 실제(`ifrs-full_ShorttermDeposits…`)와 달라 **이름으로 우연히 맞았다** — 태그를 바로잡았다.
- **45행(사채) FY2025 열이 비었다.** 둘째 열 잔액을 반기보고서의 전기말(`frmtrm`)에서 받았는데
  반기 재무상태표에 「사채」 줄이 없었다. 이제 **앵커의 그 해 사업보고서 당기말을 먼저** 보고,
  거기 없는 행만 반기 전기말로 메운다(메운 행은 `주의` 에 적는다).
- **영업수익/영업비용 단일 표시**(국내 게임·플랫폼사) — 2017~2023 은 영업비용 총액이
  `dart_TotalSellingGeneralAdministrativeExpenses` 태그에 「영업비용」 이름으로 붙어 와 **판관비로 읽혔다.**
  `--단일표시` 스위치로 처리 경로를 명시한다(기본 `총액65_원가0`).
- **유동 FVPL 은 13행**(스캐폴드 라벨 「기타금융자산 (유동 — 단기대여금·유동 FVPL 등)」)이다. 옛 표는
  `ifrs-full_CurrentFinancialAssetsAtFairValueThroughProfitOrLoss` 를 9행(현금성으로 흐름)에 두었다.
  MMF 성격이면 9행으로 옮기는 판단은 사람이 한다.

사용:
    python 스크립트/dart_원천.py --기준일 2026-06-30
    python 스크립트/dart_원천.py --기준일 2026-06-30 --별도
    python 스크립트/dart_원천.py --기준일 2026-06-30 --원천폴더 D:/회차/_raw --출력 D:/작업/원천_조립.json
    python 스크립트/dart_원천.py --기준일 2026-06-30 --단일표시 총액65_원가비움

산출: `_raw/원천_조립.json`
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "_raw")

# ── 13번 행 → (합산이냐, IFRS 태그 후보, 계정명 후보) ──────────────────
# 태그를 먼저 보고 없으면 계정명으로 간다. **둘 다 보는 이유는 아래 «어긋남» 때문이다.**
# **재무상태표에는 같은 계정명이 유동·비유동에 두 번 나온다**(「충당부채」「기타채무」
# 「당기손익-공정가치측정금융자산」 — 펄어비스 실측). 그런 행은 **이름 후보를 비워 태그로만** 잡는다.
표 = {
    7:  (False, ("ifrs-full_CashAndCashEquivalents",), ("현금및현금성자산",)),
    # 실제 태그는 ifrs-full_ 이다(펄어비스). 옛 표의 dart_ 이름은 이름 매칭으로 우연히 맞았다.
    8:  (False, ("ifrs-full_ShorttermDepositsNotClassifiedAsCashEquivalents",
                 "dart_ShortTermDepositsNotClassifiedAsCashEquivalents"),
                ("단기금융상품", "단기예치금")),
    9:  (False, (), ("단기투자자산",)),
    10: (False, ("ifrs-full_TradeAndOtherCurrentReceivables",
                 "ifrs-full_CurrentTradeReceivables"),
                ("매출채권", "매출채권및기타채권")),
    11: (False, ("ifrs-full_Inventories",), ("재고자산",)),
    12: (False, ("ifrs-full_CurrentTaxAssets",), ("당기법인세자산",)),
    # 유동 FVPL 은 스캐폴드 라벨상 13행(비영업자산)이다 — 기타유동금융자산과 합산한다.
    13: (True,  ("ifrs-full_OtherCurrentFinancialAssets",
                 "ifrs-full_CurrentFinancialAssetsAtFairValueThroughProfitOrLoss",
                 "dart_CurrentFinancialAssetDesignationAsAtFairValueThroughProfitOrLoss",
                 # 1.1.8 — 국내 유니버스 40곳 전수에서 행 없는 계정으로 남던 유동 금융자산 태그(의무 FVPL · 유동 FVOCI · 단기대여금)
                 "ifrs-full_CurrentFinancialAssetsAtFairValueThroughProfitOrLossMandatorilyMeasuredAtFairValue",
                 "ifrs-full_CurrentFinancialAssetsMeasuredAtFairValueThroughOtherComprehensiveIncome",
                 "dart_ShortTermLoansNet"),
                ("기타 유동 금융자산", "기타유동금융자산")),
    # 1.1.8 — 14 기타수취채권(유동 · 운전자본 — 기타 NWC). 미수금 · 기타채권. 이름은 「매출채권및기타채권」 과 겹쳐 태그로만
    14: (True,  ("ifrs-full_OtherCurrentReceivables", "dart_ShortTermOtherReceivablesNet"), ()),
    # 계약자산(미청구공사)을 합산한다 — 43행 계약부채의 반대편(한화에어로 7.1조).
    15: (True,  ("ifrs-full_OtherCurrentAssets", "ifrs-full_ContractAssets",
                 "ifrs-full_CurrentContractAssets",
                 "ifrs-full_CurrentPrepaidExpenses", "ifrs-full_CurrentPrepayments"),       # 1.1.8 — 선급비용 · 선급금(운전자본)
                ("기타 유동 자산", "계약자산", "유동계약자산")),
    16: (False, ("ifrs-full_CurrentAssets",), ("유동자산",)),
    17: (False, ("ifrs-full_PropertyPlantAndEquipment",), ("유형자산",)),
    18: (False, ("ifrs-full_IntangibleAssetsAndGoodwill",
                 "ifrs-full_IntangibleAssetsOtherThanGoodwill"), ("무형자산",)),
    19: (False, ("ifrs-full_RightofuseAssets",), ("사용권자산",)),
    # **둘을 나눈 태그만 두면 합친 표준 태그를 못 잡는다** — 실측(한화오션 2026 반기):
    # `ifrs-full_InvestmentAccountedForUsingEquityMethod` 한 줄로 낸 회사에서
    # **1조 2,354억(자산의 6.1%)** 이 통째로 빠졌다. 합친 태그를 먼저 둔다.
    20: (True,  ("ifrs-full_InvestmentAccountedForUsingEquityMethod",
                 "ifrs-full_InvestmentsInSubsidiariesJointVenturesAndAssociates",
                 "ifrs-full_InvestmentsInAssociatesAccountedForUsingEquityMethod",
                 "ifrs-full_InvestmentsInJointVenturesAccountedForUsingEquityMethod"),
                ("관계기업및공동기업투자", "관계기업투자", "공동기업투자",
                 "관계기업및공동기업에대한투자")),
    21: (False, ("ifrs-full_InvestmentProperty",), ("투자부동산",)),
    22: (False, ("dart_LongTermDepositsNotClassifiedAsCashEquivalents",
                 "ifrs-full_LongtermDepositsNotClassifiedAsCashEquivalents"), ("장기금융상품",)),
    24: (False, ("ifrs-full_Goodwill",), ("영업권",)),
    # 1.1.8 — 25 종업원급여자산(비영업 — 11번 14). 국내 40곳 가운데 18곳이 행 없는 계정으로 남겼다
    25: (False, ("ifrs-full_NoncurrentRecognisedAssetsDefinedBenefitPlan",), ("순확정급여자산",)),
    26: (False, ("ifrs-full_DeferredTaxAssets",), ("이연법인세자산",)),
    # 1.1.8 — FVOCI 는 채무상품 · 지분상품을 따로 잡는 회사가 있어 더한다(태그 셋)
    27: (True,  ("ifrs-full_NoncurrentFinancialAssetsMeasuredAtFairValueThrough"
                 "OtherComprehensiveIncome",
                 "ifrs-full_NoncurrentFinancialAssetsAtFairValueThroughOtherComprehensiveIncome",
                 "ifrs-full_NoncurrentInvestmentsInEquityInstrumentsDesignatedAtFairValueThroughOtherComprehensiveIncome"),
                ("장기투자자산",)),
    28: (True,  ("ifrs-full_NoncurrentFinancialAssetsAtFairValueThroughProfitOrLoss",
                 "dart_NonCurrentFairValueFinancialAsset",
                 "ifrs-full_NoncurrentFinancialAssetsAtFairValueThroughProfitOrLossMandatorilyMeasuredAtFairValue"),
                ()),
    # 1.1.8 — 29 기타금융자산(비유동 · 비영업 — 11번 15). 국내 40곳 가운데 28곳이 행 없는 계정으로 남겼다 · 장기대여금
    29: (True,  ("ifrs-full_OtherNoncurrentFinancialAssets", "dart_LongTermLoansNet"), ()),
    30: (True,  ("ifrs-full_NoncurrentReceivables",
                 "ifrs-full_OtherNoncurrentReceivables", "ifrs-full_NoncurrentTradeReceivables"), ()),   # 1.1.8 — 기타 · 장기매출채권
    31: (False, ("ifrs-full_OtherNoncurrentAssets",), ("기타 비유동 자산",)),
    32: (False, ("ifrs-full_NoncurrentAssets",), ("비유동자산",)),
    33: (False, ("ifrs-full_Assets",), ("자산총계",)),
    34: (False, ("ifrs-full_TradeAndOtherCurrentPayables",),
                ("매입채무", "매입채무및기타채무")),
    35: (False, ("ifrs-full_OtherCurrentFinancialLiabilities",),
                ("기타 유동 금융부채",)),
    37: (False, ("ifrs-full_ShorttermBorrowings",), ("단기차입금",)),
    # 유동성장기차입금 + 유동성사채를 합산한다(펄어비스 FY2024). 둘을 합친 표준 태그가
    # 있으면 그것만 쓴다(`_총계우선`) — 셋을 다 더하면 이중계상이다.
    # 유동성사채의 표준 태그(`…CurrentBondsIssuedAndCurrentPortionOfNoncurrentBondsIssued`)도 합산한다 —
    # 실측(NAVER 2026 반기): 이 태그가 표에 없어 유동성사채 3,028억이 38 에서 빠지고 행 없는 계정으로만 남았다.
    # S7-10 — 유동성 전환사채 · 유동 지정 FVPL(유동 RCPS · CB)도 이자부부채다 — 유동 구획의 D 줄인 여기에 합산한다(비유동은 110)
    38: (True,  ("ifrs-full_CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings",
                 "ifrs-full_CurrentPortionOfLongtermBorrowings", "dart_CurrentPortionOfBonds",
                 "ifrs-full_CurrentBondsIssuedAndCurrentPortionOfNoncurrentBondsIssued",
                 "ifrs-full_CurrentFinancialLiabilitiesAtFairValueThroughProfitOrLossDesignatedUponInitialRecognition"),
                ("유동성장기부채", "유동성사채", "유동성전환사채", "유동성신주인수권부사채", "유동성교환사채")),
    # 1.1.8 — 36 미지급금(운전자본 — 기타 NWC). 이름은 「매입채무및기타채무」 와 겹쳐 태그로만
    36: (True,  ("ifrs-full_OtherCurrentPayables", "dart_ShortTermOtherPayables"), ()),
    39: (False, ("ifrs-full_CurrentLeaseLiabilities",), ("유동성리스부채",)),
    40: (True,  ("ifrs-full_CurrentProvisions", "ifrs-full_OtherShorttermProvisions"), ()),   # 1.1.8 — 기타 단기충당부채(16곳)
    # 같은 계정 「미지급법인세」가 해마다 다른 태그로 온다(펄어비스: FY2024·25 dart_… · 2026 반기 ifrs-full_…).
    41: (False, ("ifrs-full_CurrentTaxLiabilities", "dart_PaymentsOfIncomeTaxesPayable", "ifrs-full_CurrentTaxLiabilitiesCurrent"),
                ("당기법인세부채", "미지급법인세")),
    # 계약부채(수주업 선수금)를 합산한다 — 실측(한화에어로): 계약부채 **15.0조**
    # (연매출의 절반)가 어느 행에도 안 실려 순 WC 가 통째로 어긋났다. BA(64.1B)·
    # LMT(12.2B)의 국내판. 계약자산(7.1조)은 위 15행에 합산한다.
    43: (True,  ("ifrs-full_OtherCurrentLiabilities", "ifrs-full_ContractLiabilities",
                 "ifrs-full_CurrentContractLiabilities",
                 "ifrs-full_CurrentAdvances", "dart_ShortTermDueToCustomersForContractWork"),   # 1.1.8 — 선수금 · 초과청구공사
                ("기타 유동 부채", "계약부채", "유동계약부채")),
    44: (False, ("ifrs-full_CurrentLiabilities",), ("유동부채",)),
    45: (False, ("dart_LongTermBondsIssued", "ifrs-full_NoncurrentPortionOfNoncurrentBondsIssued",
                 "ifrs-full_BondsIssued"), ("사채",)),
    46: (False, ("ifrs-full_LongtermBorrowings",), ("장기차입금",)),
    47: (False, ("ifrs-full_NoncurrentLeaseLiabilities",), ("리스부채",)),
    48: (False, ("dart_PostemploymentBenefitObligations", "ifrs-full_NoncurrentRecognisedLiabilitiesDefinedBenefitPlan"), ("순확정급여부채",)),
    49: (False, ("ifrs-full_DeferredTaxLiabilities",), ("이연법인세부채",)),
    # 계정명 「기타채무」가 유동(34)과 같다 — 태그로만 잡는다.
    50: (True,  ("dart_LongTermTradeAndOtherNonCurrentPayables",
                 "dart_NoncurrentNontradePayables", "ifrs-full_NoncurrentPayables"), ("기타비유동채무",)),   # 1.1.8
    51: (False, ("ifrs-full_OtherNoncurrentPayables",), ()),                                    # 1.1.8 — 장기미지급금
    52: (False, ("ifrs-full_OtherNoncurrentFinancialLiabilities",
                 "ifrs-full_NoncurrentFinancialLiabilitiesAtFairValueThroughProfitOrLoss"),
                ("기타비유동금융부채",)),
    # S7-10 — 전환형 · 상환형 금융부채(13번 110 — 이자부부채). CB · BW · EB · 부채로 분류된 상환(전환)우선주와 **최초 인식 때 당기손익-공정가치로
    # 지정한 금융부채**(국내 상장 초기 · 바이오 · 구조조정 회사의 RCPS · CB 가 흔히 여기) — 비유동분만 이 줄에(유동분은 38 — 아래). 종전에는 지정 FVPL 이
    # 52(기타금융부채 — D 밖)로 가서 D/E 와 브리지가 같이 과소였다. 「사채」(45)에 이미 든 몫은 계정명이 달라 겹치지 않는다
    #   **비유동만 싣는다** — 이 줄은 13번 비유동부채 구획(합계 54 의 범위)에 있다. 유동분(유동성전환사채 · 유동 지정 FVPL)은 38 에 합산한다
    110: (True, ("ifrs-full_NoncurrentFinancialLiabilitiesAtFairValueThroughProfitOrLoss"
                 "DesignatedUponInitialRecognition",),
                ("전환사채", "신주인수권부사채", "교환사채",
                 "상환전환우선주부채", "전환상환우선주부채", "상환우선주부채", "상환전환우선주", "전환상환우선주")),
    # 111 기타 이자부부채 — 이름이 분명한 이자부 장기미지급금만. 기타금융부채의 이자부 몫은 주석으로 갈라 사람이 옮긴다
    111: (True, (), ("장기미지급금(금융)", "금융리스미지급금", "이자부장기미지급금")),
    # 1.1.8 — 비유동 충당부채 · 장기선수금 · 장기종업원급여는 13번에 줄이 없어 기타비유동부채(브리지 밖)에 더한다(국내 40곳 가운데 13 · 12 · 8 · 4곳)
    53: (True,  ("ifrs-full_OtherNoncurrentLiabilities", "ifrs-full_NoncurrentProvisions", "ifrs-full_OtherLongtermProvisions",
                 "ifrs-full_NoncurrentAdvances", "ifrs-full_NoncurrentProvisionsForEmployeeBenefits"), ("기타 비유동 부채",)),
    54: (False, ("ifrs-full_NoncurrentLiabilities",), ("비유동부채",)),
    55: (False, ("ifrs-full_Liabilities",), ("부채총계",)),
    # **56 은 자본총계가 아니라 지배기업소유주지분이다** — 스캐폴드가 58=56+57 로
    # 자본총계를 만든다. 여기에 `ifrs-full_Equity`(자본총계)를 넣으면 **비지배지분이
    # 두 번 더해진다.** 실측(한화오션 2026 반기)에서 잡혔다.
    56: (False, ("ifrs-full_EquityAttributableToOwnersOfParent",),
                ("지배기업의 소유주에게 귀속되는 자본", "지배기업소유주지분",
                 "지배기업의 소유주지분", "지배주주지분")),
    57: (False, ("ifrs-full_NoncontrollingInterests",), ("비지배지분",)),
    58: (False, ("ifrs-full_Equity",), ("자본총계",)),
    59: (False, ("ifrs-full_EquityAndLiabilities",), ("부채와자본총계", "자본과부채총계",
                                                     "부채와 자본총계", "자본과 부채총계")),
    62: (False, ("ifrs-full_Revenue",), ("매출액", "수익(매출액)", "영업수익", "매출")),
    63: (False, ("ifrs-full_CostOfSales",), ("매출원가",)),
    65: (False, ("dart_TotalSellingGeneralAdministrativeExpenses",),
                ("판매비와관리비",)),
    66: (False, ("dart_OperatingIncomeLoss", "ifrs-full_ProfitLossFromOperatingActivities"),
                ("영업이익", "영업이익(손실)", "영업손실", "영업손익")),
    67: (False, ("ifrs-full_FinanceIncome",), ("금융수익",)),
    68: (False, ("ifrs-full_FinanceCosts",), ("금융비용",)),
    69: (False, ("dart_ProfitsOfAssociatesAndJointVenturesAccountedForUsingEquityMethod",
                 "ifrs-full_ShareOfProfitLossOfAssociatesAndJointVenturesAccountedForUsing"
                 "EquityMethod"), ("지분법손익", "지분법이익", "지분법손익(손실)")),
    70: (False, ("dart_NonOperatingProfitLoss",), ("기타손익", "기타영업외손익")),
    71: (False, ("ifrs-full_ProfitLossBeforeTax",), ("법인세비용차감전순이익",)),
    72: (False, ("ifrs-full_IncomeTaxExpenseContinuingOperations",), ("법인세 비용",)),
    73: (False, ("ifrs-full_ProfitLoss",), ("당기순이익", "당기순이익(손실)")),
    74: (False, ("ifrs-full_ProfitLossAttributableToOwnersOfParent",),
                ("지배기업의 소유주에게 귀속되는 당기순이익(손실)", "지배기업소유주지분순이익")),
}
# 현금흐름표(CF)에서 오는 행 — 부호가 뒤집혀 오는 것이 있어 따로 둔다
CF표 = {
    77: (False, ("ifrs-full_AdjustmentsForDepreciationExpense", "ifrs-full_DepreciationExpense",
                 "ifrs-full_DepreciationAndAmortisationExpense"), ("감가상각비",)),
    78: (False, ("ifrs-full_AdjustmentsForAmortisationExpense", "ifrs-full_AmortisationExpense"),
                ("무형자산상각비",)),
    79: (False, ("ifrs-full_CashFlowsFromUsedInOperatingActivities",), ("영업활동현금흐름",)),
    80: (False, ("ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvesting"
                 "Activities",), ("유형자산의 취득", "유형자산의취득")),
    81: (False, ("ifrs-full_PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities",),
                ("무형자산의 취득", "무형자산의취득")),
    82: (False, ("ifrs-full_CashFlowsFromUsedInInvestingActivities",), ("투자활동현금흐름",)),
    83: (False, ("ifrs-full_CashFlowsFromUsedInFinancingActivities",), ("재무활동현금흐름",)),
}

# **합산 행에서 총계 태그가 보이면 그것만 쓴다** — 부분까지 더하면 이중계상이다.
_총계우선 = {38: "ifrs-full_CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings"}

# **행에 보태는 흔한 확장 태그** — 그 행의 주 태그와 따로 공시되는 같은 성격의 줄(2026-10-16, S1 리뷰).
# 실측(SK하이닉스 2026 반기): `dart_CurrentNontradePayables`(기타지급채무 11.8조)가 어느 행에도 안 실려
# 「행 없는 계정」으로만 남았다. 35(기타지급채무 유동)는 운전자본 자리라 미지급금 성격 줄을 여기에 더한다.
# 35 → 37 이동 판정(차입 성격 계정명)은 주 태그 줄로만 한다 — 보탬 줄은 이름이 「미지급금 · 기타지급채무」다.
_보탬 = {35: ("dart_CurrentNontradePayables",)}

# **스캐폴드에서 수식인 행** — 값을 붓지 않는다. `검산행` 으로만 내고 행 합과 맞댄다.
# (33·55·66 은 종전대로 `원천` 에 남긴다 — 대조·검사 도구가 그 키를 읽는다.)
수식칸 = (16, 32, 44, 54, 58, 59, 73)

# 소계 = 구성 행 합 (스캐폴드 수식과 같은 범위)
소계구성 = {16: range(7, 16), 32: range(17, 32), 44: range(34, 44), 54: list(range(45, 54)) + [110, 111]}   # 110 · 111 — 비유동 구획(S7-10)

# 13번 원천 시트의 줄 이름 — 스캐폴드의 라벨(H-0nn)과 같은 말이다. 레터의 계정 표(`레터본문.계정분류`)가 이 사전으로 계정을 부르므로
# 이름이 빠진 줄은 표에서 조용히 빠진다(실측: 미지급금 6.05조 원이 운전자본 계정 표에서 빠졌다 — 2026-10-22). 줄을 더하면 이름도 더한다.
행이름 = {
    7: "현금및현금성자산", 8: "단기금융상품", 9: "단기투자자산", 10: "매출채권",
    11: "재고자산", 12: "당기법인세자산", 13: "기타금융자산(유동·FVPL 포함)",
    14: "기타수취채권(유동)",                                # 14 · 23 · 25 · 29 · 36 · 42 · 51 — 이 도구가 태그로 채우지 않는 줄도 이름은 둔다
    15: "기타유동자산", 16: "유동자산 합계", 17: "유형자산",
    18: "무형자산", 19: "사용권자산", 20: "관계기업·공동기업투자", 21: "투자부동산",
    22: "장기금융상품", 23: "장기투자자산", 24: "영업권", 25: "종업원급여자산", 26: "이연법인세자산", 27: "FVOCI 금융자산",
    28: "FVPL 금융자산(비유동)", 29: "기타금융자산(비유동)", 30: "기타수취채권(비유동)", 31: "기타비유동자산",
    32: "비유동자산 합계", 33: "자산총계",
    34: "매입채무", 35: "기타지급채무(유동)", 36: "미지급금", 37: "단기차입금", 38: "유동성장기부채",
    39: "리스부채(유동)", 40: "충당부채(유동)", 41: "당기법인세부채", 42: "기타금융부채(유동)", 43: "기타유동부채",
    44: "유동부채 합계", 45: "사채",
    46: "장기차입금", 47: "리스부채(비유동)", 48: "순확정급여부채", 49: "이연법인세부채",
    50: "기타지급채무(비유동)", 51: "장기미지급금", 52: "기타금융부채(비유동)", 110: "전환형 · 상환형 금융부채", 111: "기타 이자부부채",
    53: "기타비유동부채", 54: "비유동부채 합계", 55: "부채총계",
    56: "지배기업소유주지분", 57: "비지배지분", 58: "자본총계", 59: "부채와자본총계",
    62: "매출액", 63: "매출원가", 65: "판매비와관리비", 66: "영업이익",
    67: "금융수익", 68: "금융비용", 69: "지분법손익", 70: "기타영업외손익",
    71: "법인세비용차감전순이익", 72: "법인세비용", 73: "당기순이익",
    74: "지배기업소유주 귀속 순이익",
    77: "감가상각비", 78: "무형자산상각비", 79: "영업활동현금흐름", 80: "유형자산 취득",
    81: "무형자산 취득", 82: "투자활동현금흐름", 83: "재무활동현금흐름",
}

필수 = (7, 10, 17, 33, 34, 55, 56, 62, 63, 66, 72, 77, 80)

# **태그와 계정명이 어긋나는지 본다.** 태그의 뜻과 이름의 뜻이 반대면 알린다.
_어긋남표 = (("Receivable", ("차입금", "부채", "채무")),
          ("Payable", ("채권", "자산")),
          ("Asset", ("부채", "채무", "차입금")),
          ("Liabilit", ("자산", "채권")))

# ── 영업수익/영업비용 단일 표시 ────────────────────────────────────────────
# 국내 게임·플랫폼사는 손익을 기능별(매출원가·판관비)로 나누지 않고
# 「영업수익 − 영업비용 = 영업이익」 한 줄로 낸다. 실측(펄어비스 2017~2025 전부).
# 2017~2023 은 영업비용 **총액**이 `dart_TotalSellingGeneralAdministrativeExpenses`(판관비 태그)에
# 「영업비용」 이름으로 붙어 온다 — 태그만 보면 판관비로 읽힌다. 2024~ 는 `ifrs-full_OperatingExpense`.
_영업비용태그 = ("ifrs-full_OperatingExpense",)
_영업비용이름 = ("영업비용", "영업비용합계", "영업비용 합계")
단일표시경로 = {
    "총액65_원가0":   "65 에 영업비용 총액, 63 은 0 — 스캐폴드 64=62−63·66=64−65 가 공시 영업이익과 맞는다. "
                    "**63=0 은 원가가 0 이라는 뜻이 아니라 기능별 분리 공시가 없다는 뜻**이다(원가율 해석 불가)",
    "총액65_원가비움": "65 에 영업비용 총액, 63 은 빈칸 — 13번 111행 미입력으로 세이니 G63 에 「확인 불가(항목 부재 — "
                    "단일 표시)」를 적어야 통과한다",
    "안붓기":         "63·65 둘 다 비운다 — 성격별 비용 주석으로 나눠 사람이 붓는다. 66 은 공시값을 그대로 둔다",
}
단일표시기본 = "총액65_원가0"


def _금액(it, 칸):
    s = ("%s" % (it.get(칸) or "")).replace(",", "").strip()
    if not s or s in ("-", "--"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _비용표시(항목들, 칸, 폴백칸=None):
    """한 열의 손익이 단일 표시인지 본다. → (단일이냐, 영업비용 총액, 근거 문자열)."""
    원가, 총액, 근거 = False, None, None
    for it in 항목들 or []:
        if (it.get("sj_div") or "").strip() not in ("IS", "CIS"):
            continue
        tid = (it.get("account_id") or "").strip()
        nm = (it.get("account_nm") or "").strip()
        if tid == "ifrs-full_CostOfSales" or nm in ("매출원가",):
            원가 = True
        if 총액 is None and (tid in _영업비용태그 or nm in _영업비용이름
                            or (tid == "dart_TotalSellingGeneralAdministrativeExpenses"
                                and "영업비용" in nm and "판매" not in nm)):
            v = _금액(it, 칸)
            if v is None and 폴백칸:
                v = _금액(it, 폴백칸)
            if v is not None:
                총액, 근거 = v, "%s (%s)" % (tid or "태그없음", nm)
    return (총액 is not None and not 원가), 총액, 근거


def 조립(열원천, 단일표시=단일표시기본, 열이름=None):
    """`열원천` 은 실적 열 각각의 (잔액 원천들, 흐름 원천) 이다.

    잔액 원천들 — `[(항목들, 금액칸), …]` **앞에서부터** 본다. 앞 원천에 그 행이 없거나 값이
    비면 다음 원천으로 간다(2026-09-13 — 45행 FY2025 가 반기 전기말에 줄이 없어 비던 자리).
    흐름 원천 — `(항목들, 금액칸, 폴백칸)`.

    **왜 열마다 다른가 — 반기 함정.** 반기보고서의 손익·현금흐름 행은
    `thstrm_amount` 가 3개월이고 `thstrm_add_amount` 가 누계다. 실측(HMM):
    앞엣것을 읽어 반기 매출이 6.12조가 아니라 **3.40조(2분기만)** 로 조립됐다.
    게다가 반기 손익에는 전기 연간 값이 없어(`frmtrm_amount`=None) 연간 두 해는
    **앵커 시계열의 그 해 전체 재무제표**에서 받는다 — 새로 조회하지 않는다.
    """
    if 단일표시 not in 단일표시경로:
        raise ValueError("단일표시는 %s 중 하나다" % " · ".join(단일표시경로))
    열수 = len(열원천)
    열이름 = list(열이름 or ["열%d" % i for i in range(열수)])
    원천, 태그, 못찾음, 주의, 기타후보 = {}, {}, [], [], []
    쓴항목 = set()            # id(항목) — 어느 행이 읽어 간 BS 계정
    메운행 = []               # (행, 열) — 둘째 원천으로 메운 자리
    비교차이 = []             # (행, 열, 앞 원천 값, 뒤 원천 값) — 사업보고서 기말 ≠ 반기 전기말
    이동35 = None             # 35 → 37 로 보낼 차입 성격 줄(37 을 다 본 뒤 합친다)

    def 한칸(항목들, 칸, 후보태그, 후보이름, sj, 폴백칸=None, 합산=False, 행=None):
        """한 열에서 그 행의 값 하나 — (값, 태그, 계정명). 못 찾으면 (None,)*3.

        **`합산=True` 면 후보에 걸리는 것을 전부 더한다.** 15(기타유동자산+계약자산)·
        43(기타유동부채+계약부채)·20(관계기업+공동기업)이 그런 행이다.
        실측(한화오션 2026 반기): 이 갈래가 없어 15행에 계약자산만 잡히고
        **기타유동자산 1.71조**가, 43행에 계약부채만 잡히고 **기타유동부채 0.31조**가
        통째로 빠졌다. 재무상태표 소계 검산으로만 잡히는 종류다.
        같은 계정을 두 번 더하지 않도록 **계정명(없으면 태그)으로 한 번만 센다** —
        「계약자산」에 `ContractAssets` 와 `CurrentContractAssets` 가 같이 붙는 회사가 있다.
        """
        if 합산:
            총계태그 = _총계우선.get(행)
            if 총계태그 and any((it.get("account_id") or "").strip() == 총계태그
                             and (it.get("sj_div") or "").strip() in sj
                             for it in 항목들 or []):
                후보태그, 후보이름 = (총계태그,), ()
            총, 태그들, 이름들, 본것 = None, [], [], set()
            for it in 항목들 or []:
                if (it.get("sj_div") or "").strip() not in sj:
                    continue
                tid = (it.get("account_id") or "").strip()
                nm = (it.get("account_nm") or "").strip()
                if not (tid and tid in 후보태그) and nm not in 후보이름:
                    continue
                키 = nm or tid
                if 키 in 본것:
                    continue
                v = _금액(it, 칸)
                if v is None and 폴백칸:
                    v = _금액(it, 폴백칸)
                if v is None:
                    continue
                본것.add(키)
                쓴항목.add(id(it))
                총 = v if 총 is None else 총 + v
                태그들.append(tid or "태그없음")
                이름들.append(nm)
            if 총 is None:
                return None, None, None
            return 총, "+".join(태그들), "+".join(이름들)
        for it in 항목들 or []:
            if (it.get("sj_div") or "").strip() not in sj:
                continue
            tid = (it.get("account_id") or "").strip()
            if tid and tid in 후보태그:
                v = _금액(it, 칸)
                if v is None and 폴백칸:
                    v = _금액(it, 폴백칸)
                쓴항목.add(id(it))
                return v, tid, (it.get("account_nm") or "").strip()
        for 이름 in 후보이름:
            for it in 항목들 or []:
                if (it.get("sj_div") or "").strip() not in sj:
                    continue
                if (it.get("account_nm") or "").strip() == 이름:
                    v = _금액(it, 칸)
                    if v is None and 폴백칸:
                        v = _금액(it, 폴백칸)
                    쓴항목.add(id(it))
                    return v, (it.get("account_id") or "").strip(), 이름
        return None, None, None

    for 뭉치, sj, 흐름이냐 in ((표, ("BS",), False), (표, ("IS", "CIS"), True),
                          (CF표, ("CF",), True)):
        for 행, (합산, 태그후보, 이름후보) in sorted(뭉치.items()):
            # BS 행은 잔액 갈래로, 손익·CF 행은 흐름 갈래로 — 표가 섞여 있으므로
            # 이 행이 실제로 그 sj 에서 잡히는지로 가른다
            셋, tid, nm = [], None, None
            for 열i, (잔원천들, (흐항목, 흐칸, 흐폴백)) in enumerate(열원천):
                if 흐름이냐:
                    v, t, n = 한칸(흐항목, 흐칸, 태그후보, 이름후보, sj, 흐폴백, 합산, 행)
                else:
                    # **태그로 모든 원천을 먼저 보고, 그래도 없을 때만 이름으로 본다.**
                    # 앞 원천에서 이름으로 잡으면 같은 이름의 다른 줄을 집는다 — 실측(삼성바이오
                    # FY2025 사업보고서): 유동 `CurrentBorrowings…` 줄과 비유동 `LongtermBorrowings` 줄이
                    # **둘 다 「사채」라는 이름**이라, 45행이 유동 3,197억을 잡을 뻔했다(반기 전기말에는
                    # 비유동 사채 태그 `NoncurrentPortionOfNoncurrentBondsIssued` 5,990억이 있다).
                    v, t, n = None, None, None
                    태그값 = []
                    for 순번, (잔항목, 잔칸) in enumerate(잔원천들):
                        v2, t2, n2 = 한칸(잔항목, 잔칸, 태그후보, (), sj, None, 합산, 행)
                        태그값.append(v2)
                        t, n = t or t2, n or n2
                        if v is None and v2 is not None:
                            v = v2
                            if 순번 > 0:
                                메운행.append((행, 열i))
                    if v is None and 이름후보:
                        for 순번, (잔항목, 잔칸) in enumerate(잔원천들):
                            v2, t2, n2 = 한칸(잔항목, 잔칸, (), 이름후보, sj, None, 합산, 행)
                            t, n = t or t2, n or n2
                            if v2 is not None:
                                v = v2
                                if 순번 > 0:
                                    메운행.append((행, 열i))
                                break
                    # 사업보고서 기말과 반기 전기말 비교값이 다르면 재분류·재작성 신호다 — 적어 둔다
                    잡힌 = [x for x in 태그값 if x is not None]
                    if len(잡힌) > 1 and any(abs(x - 잡힌[0]) >= 1 for x in 잡힌[1:]):
                        비교차이.append((행, 열i, 잡힌[0], 잡힌[1]))
                셋.append(v)
                tid, nm = tid or t, nm or n
            if all(v is None for v in 셋) and tid is None:
                continue                     # 이 sj 갈래에는 그 행이 없다 — 다음 갈래로
            if str(행) in 원천 and any(v is not None for v in 원천[str(행)]):
                continue                     # 앞 갈래에서 이미 잡았다
            # **WC 자리(35)에 차입 성격 계정명이 붙으면 37(단기차입금)로 보낸다** —
            # 실측(셀트리온): 「단기금융부채」 3.5조(차입)가
            # OtherCurrentFinancialLiabilities 태그로 35 에 실려, 엔진 9번이
            # 이자부 부채를 운전자본 유출로 셌다(w13 이 연매출의 −71%). 같은
            # 태그가 한화에어로에선 소액 지급채무(46십억)라 — 태그가 아니라
            # **계정명이 성격을 가른다.**
            # **37 을 다 본 뒤에 합친다** (2026-09-13). 옛 판은 35 가 37 보다 먼저 돌아 37 자리를
            # 35 값으로 채웠고, 그러면 진짜 단기차입금 줄이 「이미 잡았다」로 건너뛰어졌다 — 실측(씨젠):
            # 사업보고서의 「기타유동금융부채 0」이 37 을 차지해 단기차입금 350억이 빠졌다.
            # **「기타…금융부채」는 보내지 않는다** (같은 날). 국내 「기타금융부채」는 미지급금·예수보증금
            # 같은 운전자본성 줄이 대부분이다 — 옛 판은 이것까지 37 로 보내면서 진짜 단기차입금을 밀어냈다
            # (실측: 현대차 반기 37행이 단기차입금 10.8조가 아니라 기타금융부채 1,657억 · 크래프톤·롯데케미칼·
            # SGC에너지·CJ프레시웨이도 같은 꼴). 셀트리온의 「단기금융부채」처럼 「기타」가 없는 이름만 보낸다.
            if 행 == 35 and ("차입" in (nm or "") or
                            ("금융부채" in (nm or "") and "기타" not in (nm or ""))):
                이동35 = (셋, tid, nm)
                continue
            원천[str(행)] = 셋
            태그[str(행)] = ["%s (%s)" % (tid or "태그없음", nm or "")]
            # ── 태그와 이름이 어긋나나 ──────────────────────────────
            for 조각, 반대말들 in _어긋남표:
                if 조각 in (tid or "") and any(w in (nm or "") for w in 반대말들):
                    주의.append(
                        "**%d행 %s — 태그와 계정명이 어긋납니다.** 태그 `%s` 에 "
                        "계정명 「%s」 가 붙어 있습니다. 공시 태깅이 틀렸을 수 있으니 "
                        "**어느 쪽이 맞는지 주석으로 확인하십시오** — 태그만 믿으면 "
                        "자산을 부채로 읽습니다"
                        % (행, 행이름.get(행, ""), tid, nm))

    if 이동35:
        셋35, tid35, nm35 = 이동35
        if any(x is not None for x in 셋35):
            옛37 = 원천.get("37") or [None] * 열수
            원천["37"] = [None if (a is None and b is None) else (a or 0.0) + (b or 0.0)
                        for a, b in zip(옛37, 셋35)]
            태그["37"] = (태그.get("37") or []) + ["%s (%s → 35에서 이동·합산)" % (tid35 or "태그없음", nm35 or "")]
        주의.append(
            "**35행 후보 「%s」 는 차입 성격이라 37행(단기차입금)에 합산했습니다** — "
            "운전자본이 아니라 이자부 부채입니다. 주석으로 구성(차입/파생/미지급)을 "
            "확인하십시오" % (nm35 or tid35))
    # ── 보탬 태그 — 그 행에 더한다(이미 다른 행이 읽어 간 줄은 건너뛴다) ─────────────
    for 행, 보탬태그 in _보탬.items():
        더한 = []
        for 열i, (잔원천들, _흐) in enumerate(열원천):
            for 잔항목, 잔칸 in 잔원천들:
                후 = [it for it in (잔항목 or []) if (it.get("sj_div") or "").strip() == "BS"
                     and (it.get("account_id") or "").strip() in 보탬태그 and id(it) not in 쓴항목]
                if not 후:
                    continue
                v = sum((_금액(it, 잔칸) or 0.0) for it in 후)
                for it in 후:
                    쓴항목.add(id(it))
                if v:
                    벌 = 원천.setdefault(str(행), [None] * 열수)
                    벌[열i] = (벌[열i] or 0.0) + v
                    더한.append("%s %s" % (열이름[열i], "/".join(sorted({(it.get("account_nm") or "").strip() for it in 후}))))
                break
        if 더한:
            태그.setdefault(str(행), [])
            태그[str(행)] = (태그[str(행)] or []) + ["%s (보탬 — %s)" % ("+".join(보탬태그), " · ".join(더한[:3]))]
    if 비교차이:
        주의.append(
            "**사업보고서 기말과 반기·분기 보고서의 전기말 비교값이 다른 잔액이 %d칸 있습니다** — %s. "
            "사업보고서 값을 썼습니다. 차이는 재분류·재작성 신호이니 반기 원문 재무상태표 주석을 보십시오"
            % (len(비교차이), " · ".join("%d행 %s %s vs %s" % (r, 열이름[c], "{:,.0f}".format(a), "{:,.0f}".format(b))
                                       for r, c, a, b in 비교차이[:6])))
    if any("CurrentFinancialAssetsAtFairValueThroughProfitOrLoss" in t or
           "CurrentFinancialAssetDesignationAsAtFairValueThroughProfitOrLoss" in t
           for t in (태그.get("13") or [])):
        주의.append(
            "**유동 당기손익-공정가치 금융자산을 13행(기타금융자산 유동 → 비영업자산)에 두었습니다** — "
            "스캐폴드 라벨을 따른 것입니다(옛 판은 9행 단기투자자산 → 현금성). MMF·단기채권형처럼 "
            "현금성이면 9행으로 옮기는 판단은 주석을 보고 사람이 합니다")
    if 메운행:
        주의.append(
            "**잔액 %d칸은 앞 원천(사업보고서 당기말)에 줄이 없어 뒤 원천(반기·분기 전기말 비교)으로 "
            "메웠습니다** — %s. 두 보고서의 표시가 달라진 자리일 수 있으니 원문으로 확인하십시오"
            % (len(메운행), " · ".join("%d행 %s" % (r, 열이름[c] if c < len(열이름) else c)
                                       for r, c in 메운행[:8])))

    # ── 영업수익/영업비용 단일 표시 — 열마다 본다 ─────────────────────────
    비용표시 = []
    for 열i, (_잔, (흐항목, 흐칸, 흐폴백)) in enumerate(열원천):
        단일, 총액, 근거 = _비용표시(흐항목, 흐칸, 흐폴백)
        비용표시.append({"열": 열이름[열i], "표시": "단일" if 단일 else "기능별",
                     "영업비용총액": 총액, "근거": 근거})
    단일열 = [i for i, b in enumerate(비용표시) if b["표시"] == "단일"]
    if 단일열:
        for 행 in (63, 65):
            원천.setdefault(str(행), [None] * 열수)
            태그.setdefault(str(행), [])
        for i in 단일열:
            b = 비용표시[i]
            if 단일표시 == "안붓기":
                원천["63"][i], 원천["65"][i] = None, None
            else:
                원천["65"][i] = b["영업비용총액"]
                원천["63"][i] = 0.0 if 단일표시 == "총액65_원가0" else None
        태그["65"] = ["영업비용 총액(단일 표시) — %s" % " / ".join(
            sorted({비용표시[i]["근거"] for i in 단일열})) if 단일표시 != "안붓기" else "비움(단일 표시)"]
        태그["63"] = ["단일 표시 — %s" % ("0(기능별 분리 없음)" if 단일표시 == "총액65_원가0" else "비움")]
        주의.append(
            "**영업수익/영업비용 단일 표시입니다(%d열: %s)** — 매출원가·판관비를 나누지 않는 회사입니다. "
            "`dart_TotalSellingGeneralAdministrativeExpenses` 태그에 「영업비용」 이름이 붙어 오면 그것은 "
            "**판관비가 아니라 영업비용 총액**입니다. 처리 경로 `--단일표시 %s`: %s. "
            "5번(매출원가)·6번(판관비) 배분은 성격별 비용 주석으로 사람이 정합니다"
            % (len(단일열), " · ".join(비용표시[i]["열"] for i in 단일열), 단일표시,
               단일표시경로[단일표시]))

    # ── 「기타」 계열은 **배분하지 않는다** — 후보만 낸다 ──────────────
    _당기잔항목, _당기잔칸 = 열원천[-1][0][0]
    for it in _당기잔항목 or []:
        if (it.get("sj_div") or "").strip() != "BS":
            continue
        nm = (it.get("account_nm") or "").strip()
        if "기타" not in nm:
            continue
        v = _금액(it, _당기잔칸)
        if v:
            기타후보.append({"계정명": nm, "태그": (it.get("account_id") or "").strip(),
                          "금액": v})
    if 기타후보:
        주의.append(
            "「기타」 계열 %d건은 **배분하지 않았습니다.** 주석을 열어야 무엇이 들었는지 "
            "압니다 — 리스인지 예수금인지 미지급금인지에 따라 **운전자본으로 갈지 "
            "이자부부채로 갈지가 갈립니다.** `기타후보` 목록을 보고 사람이 정하십시오"
            % len(기타후보))

    # ── 수식칸(소계)은 `검산행` 으로 뺀다 ───────────────────────────────
    검산행 = {}
    for 행 in 수식칸:
        if str(행) in 원천:
            검산행[str(행)] = 원천.pop(str(행))
            태그.setdefault("검산:%d" % 행, 태그.pop(str(행), []))
        else:
            검산행[str(행)] = [None] * 열수

    # 두 갈래(BS · 손익/CF)를 다 돈 뒤에 못 찾은 행을 센다
    for 뭉치 in (표, CF표):
        for 행 in 뭉치:
            if 행 in 수식칸:
                continue
            if str(행) not in 원천:
                원천[str(행)] = [None] * 열수
                태그[str(행)] = []
                못찾음.append(행)
            elif all(v is None for v in 원천[str(행)]) and 행 not in 못찾음:
                if not (행 == 63 and 단일열):
                    못찾음.append(행)

    # ── **소계 대조** — 행 합이 공시 소계와 맞나 (2026-09-13 신설) ─────────
    # 펄어비스 실측: 28·13 행이 비어 **자산의 15%** 가 빠졌는데, 이 대조가 없어 사람이 A2a 에서
    # 손으로 잡았다. 틀리는 것을 메우지 않는다 — 빠진 금액과 **13번에 행이 없는 계정 후보**를 낸다.
    def _v(행, i):
        벌 = 원천.get(str(행)) or 검산행.get(str(행)) or [None] * 열수
        return 벌[i]

    소계대조 = []
    영업이익바꿈 = []
    for i in range(열수):
        for 소, 구성 in sorted(소계구성.items()):
            공시 = 검산행[str(소)][i]
            if 공시 is None:
                continue
            합 = sum((_v(r, i) or 0.0) for r in 구성 if str(r) in 원천)
            소계대조.append({"열": 열이름[i], "소계": "%d %s" % (소, 행이름[소]), "공시": 공시,
                         "행합": 합, "차": 공시 - 합,
                         "결과": "일치" if abs(공시 - 합) < 1 else "불일치"})
        for 총, (a, b), 이름 in ((33, (16, 32), "자산총계 = 유동 + 비유동"),
                              (55, (44, 54), "부채총계 = 유동 + 비유동"),
                              (58, (56, 57), "자본총계 = 지배 + 비지배"),
                              (59, (55, 58), "부채와자본총계 = 부채 + 자본")):
            좌, x, y = _v(총, i), _v(a, i), _v(b, i)
            if None in (좌, x, y):
                continue
            소계대조.append({"열": 열이름[i], "소계": 이름, "공시": 좌, "행합": x + y,
                         "차": 좌 - x - y, "결과": "일치" if abs(좌 - x - y) < 1 else "불일치"})
        매, 원, 판, 영 = _v(62, i), _v(63, i), _v(65, i), _v(66, i)
        if None not in (매, 판, 영):
            좌 = 매 - (원 or 0.0) - 판
            소계대조.append({"열": 열이름[i], "소계": "매출 − 매출원가 − 판관비 = 영업이익",
                         "공시": 영, "행합": 좌, "차": 영 - 좌,
                         "결과": "일치" if abs(영 - 좌) < 1 else "불일치"})
            if abs(영 - 좌) >= 1:
                # S10-13 — 13번 66(영업이익)은 스캐폴드에서 수식(매출총이익 − 판관비)이다. 엔진은 원천 66 을 실적 영업이익으로 읽으므로 공시 값을 두면
                #   엔진(공시) ≠ 워크북(수식)으로 6 · 10번 실적 열이 갈린다(실측 기능별 유통 회사 — 27곳). 66 에는 수식과 같은 값을 두고 공시 값은 검산행에 남긴다
                검산행.setdefault("66_공시", [None] * 열수)[i] = 영
                원천["66"][i] = 좌
                영업이익바꿈.append("%s %s → %s(차 %s — 기타영업손익 등)" % (열이름[i], "{:,.0f}".format(영), "{:,.0f}".format(좌), "{:,.0f}".format(영 - 좌)))
        # ── 법인세 부호 — 71 − 72 = 73 (스캐폴드 73 의 식) (2026-10-16, S1 리뷰) ──────────────
        # 키트가 꼽은 조용한 함정 둘 가운데 하나다(CLAUDE.md 「재무제표를 가져올 때」 — SGC에너지 실측: 「세전 + 법인세비용
        # = 순이익」으로 낸 회사). 중단영업이 있으면 73 은 계속영업이익이 아니다 — 계속영업이익 태그가 있으면 그것과 맞댄다.
        세전, 세, 순 = _v(71, i), _v(72, i), _v(73, i)
        흐항목, 흐칸, 흐폴백 = 열원천[i][1]
        계속 = None
        for it in 흐항목 or []:
            if (it.get("sj_div") or "").strip() in ("IS", "CIS") and \
                    (it.get("account_id") or "").strip() == "ifrs-full_ProfitLossFromContinuingOperations":
                계속 = _금액(it, 흐칸)
                if 계속 is None and 흐폴백:
                    계속 = _금액(it, 흐폴백)
                break
        기준 = 계속 if 계속 is not None else 순
        if None not in (세전, 세, 기준):
            좌 = 세전 - 세
            맞음 = abs(좌 - 기준) < 1
            반전 = (not 맞음) and abs(세전 + 세 - 기준) < 1 and abs(세) >= 1
            소계대조.append({"열": 열이름[i], "소계": "법인세차감전 − 법인세비용 = %s" % ("계속영업이익" if 계속 is not None else "당기순이익"),
                         "공시": 기준, "행합": 좌, "차": 기준 - 좌,
                         "결과": "일치" if 맞음 else ("부호 반전 의심" if 반전 else "불일치")})
            if 반전:
                주의.append(
                    "**%s 법인세비용(72)의 부호 반전 의심 — 71 − 72 가 %s(공시 %s)와 어긋나고 71 + 72 가 맞습니다.** "
                    "「세전 + 법인세비용 = 순이익」으로 낸 회사입니다 — 표시된 %s 은 법인세**수익**일 수 있습니다. "
                    "주석의 법인세 조정표로 부호를 확인하고 어느 쪽을 썼는지 근거 칸에 적으십시오(스캐폴드 73 = 71 − 72)"
                    % (열이름[i], "계속영업이익" if 계속 is not None else "당기순이익", "{:,.0f}".format(기준), "{:,.0f}".format(세)))
    if 영업이익바꿈:
        주의.append("**13번 66(영업이익)은 스캐폴드 수식(매출총이익 − 판관비)이라 원천 66 에 수식과 같은 값을 두었습니다** — %s. 공시 영업이익은 "
                  "`검산행.66_공시` 에 남겼습니다. 차가 기타영업손익 따위면 그 성격을 근거 칸에 적고, 원가 줄 · 판관에 넣을지 정하십시오(S10-13 — 엔진 = 워크북)"
                  % " · ".join(영업이익바꿈[:4]))
    어긋난 = [x for x in 소계대조 if x["결과"] != "일치"]
    if 어긋난:
        주의.append(
            "**소계와 행 합이 %d곳 어긋납니다** — %s. 13번에 행이 없는 계정이 섞였거나(아래 "
            "`행없는계정`) 태그를 못 잡은 행이 있습니다. **비슷한 값으로 메우지 않습니다**"
            % (len(어긋난), " · ".join("%s %s 차 %s" % (x["열"], x["소계"], "{:,.0f}".format(x["차"]))
                                      for x in 어긋난[:6])))

    # ── 어느 행도 안 읽어 간 재무상태표 계정(당기 열) ───────────────────────
    행없는계정 = []
    _자본구성 = ("IssuedCapital", "CapitalSurplus", "SharePremium", "RetainedEarnings",
             "ElementsOfOtherStockholdersEquity", "OtherComprehensiveIncomeLossAccumulated",
             "TreasuryShares", "OtherReserves", "OtherEquityInterest",
             "AccumulatedOtherComprehensiveIncome", "AdditionalPaidinCapital",                   # 1.1.8 — 자본 구성 줄이 행 없는 계정으로 섞이던 자리
             "AmountRecognisedInOtherComprehensiveIncomeAndAccumulatedInEquity")
    for 잔항목, 잔칸 in 열원천[-1][0]:
        for it in 잔항목 or []:
            if (it.get("sj_div") or "").strip() != "BS" or id(it) in 쓴항목:
                continue
            tid = (it.get("account_id") or "").strip()
            if any(w in tid for w in _자본구성):
                continue
            v = _금액(it, 잔칸)
            if v:
                행없는계정.append({"계정명": (it.get("account_nm") or "").strip(), "태그": tid,
                               "금액": v})
        break

    # ── **사용권자산 ↔ 리스부채 짝** (2026-10-16, S1 리뷰 — BGF리테일 실측) ──────────────────
    # 리스부채를 「기타금융부채」에 묶어 공시하는 회사가 있다. 그러면 19 사용권자산은 잡히는데 39 · 47 이 비고,
    # 그 금액은 35(운전자본)·52 나 「기타」 후보에 숨는다 — 이자부부채가 통째로 작아진다. IFRS 16 아래 EBITDA 에는
    # 리스비가 빠져 있으므로 부채까지 빠지면 가치가 이중으로 부푼다. 소계 어긋남 속에 묻히지 않게 이름 대어 낸다.
    for i in range(열수):
        사용권 = _v(19, i)
        리스 = [_v(39, i), _v(47, i)]
        if 사용권 and 사용권 > 0 and not any(x for x in 리스 if x):
            후보글 = []
            for 행 in (35, 52, 43, 53):
                v = _v(행, i)
                if v:
                    후보글.append("%d행 %s %s(%s)" % (행, 행이름.get(행, ""), "{:,.0f}".format(v),
                                                  ((태그.get(str(행)) or [""])[0])[:40]))
            if i == 열수 - 1:
                for x in 기타후보 + 행없는계정:
                    if any(k in x["계정명"] for k in ("금융부채", "리스", "기타채무")) or "Lease" in x["태그"]:
                        후보글.append("%s %s" % (x["계정명"], "{:,.0f}".format(x["금액"])))
            주의.append(
                "**%s 사용권자산(19) %s 이 있는데 리스부채(39 · 47)가 비었습니다 — 리스부채 짝 끊김.** "
                "리스부채를 기타금융부채 · 기타채무에 묶어 공시한 회사일 수 있습니다 — 그러면 이자부부채가 그만큼 "
                "작게 잡히고(순차입금 · D/E), EBITDA 에서 빠진 리스비와 겹쳐 가치가 부풉니다. 후보: %s. "
                "**주석(리스)으로 금액을 확인해 39 · 47 로 옮기고, 남은 몫만 운전자본에 두십시오**"
                % (열이름[i], "{:,.0f}".format(사용권), " · ".join(dict.fromkeys(후보글)) or "후보 없음 — 주석을 여십시오"))

    # ── **감가상각비는 주석에만 있는 회사가 많다** ──────────────────────
    # 재무제표 API 의 현금흐름표는 회사에 따라 영업활동 세부(조정 항목)를 안 준다.
    # 실측(HMM): CF 38개 항목에 감가상각비 줄이 아예 없다 — 재무·투자활동만 있다.
    # 그때는 **성격별 비용 주석**에 있고, 그것은 사업보고서 원문을 받아야 나온다.
    # 이 사실을 말하지 않으면 「태그를 못 찾았다」로 읽혀 태그만 계속 뒤진다.
    if 77 in 못찾음 or 78 in 못찾음:
        주의.append(
            "**감가상각비(77)·무형자산상각비(78)를 현금흐름표에서 못 찾았습니다.** "
            "재무제표 API 의 현금흐름표는 회사에 따라 영업활동 세부(조정 항목)를 "
            "주지 않습니다 — 그때는 **성격별 비용 주석**에 있고, 그것은 사업보고서 "
            "원문에만 있습니다. `dart_fetch.py --원문` 으로 받아 여십시오. "
            "**태그를 더 뒤져도 안 나옵니다.**")

    빈필수 = [r for r in 필수 if r in 못찾음]
    return {"원천": 원천, "태그": 태그, "못찾음": 못찾음,
            "못찾은이름": {str(r): 행이름.get(r, "?") for r in 못찾음},
            "빈필수": 빈필수,
            "빈필수이름": {str(r): 행이름.get(r, "?") for r in 빈필수},
            "검산행": 검산행, "수식칸": list(수식칸), "소계대조": 소계대조,
            "행없는계정": 행없는계정,
            "비용표시": 비용표시, "단일표시": 단일표시,
            "기타후보": 기타후보, "주의": 주의}


def 앵커네줄(연간, 단일표시=단일표시기본):
    """앵커 시계열의 해마다 **매출·매출원가·판관비·영업이익** 네 줄 — `조립()` 과 같은 규칙.

    2026-09-13 신설(펄어비스 실측). A2a 가 손으로 뽑을 때 2017~2023 은 「영업수익」이
    `-표준계정코드 미사용-` 이라 태그로는 매출이 비고, `dart_TotalSGA` 태그의 값(=영업비용 총액)을
    판관비로 읽을 뻔했다. 여기서는 이름 폴백과 단일 표시 판정을 조립과 똑같이 태운다.
    """
    해들 = sorted(연간)
    if not 해들:
        return {"시계열": [], "부호전환": [], "부호전환횟수": 0}
    열원천 = [([(연간[y], "thstrm_amount")], (연간[y], "thstrm_amount", None)) for y in 해들]
    o = 조립(열원천, 단일표시, ["FY%d" % y for y in 해들])
    줄 = []
    for i, y in enumerate(해들):
        b = o["비용표시"][i]
        r = {"사업연도": y,
             "매출": o["원천"]["62"][i], "매출원가": o["원천"]["63"][i],
             "판관비": o["원천"]["65"][i],
             # 공시 영업이익(조립이 66 을 워크북 수식 값으로 바꿨으면 `검산행.66_공시` — S10-13). 앵커 항등식은 공시 값으로 본다
             "영업이익": ((o.get("검산행") or {}).get("66_공시") or [None] * len(해들))[i] if ((o.get("검산행") or {}).get("66_공시") or [None] * len(해들))[i] is not None else o["원천"]["66"][i],
             "비용표시": b["표시"], "영업비용총액": b["영업비용총액"]}
        if b["표시"] == "단일":
            r["주의"] = ("단일 표시 — 판관비 칸은 %s" % (
                "영업비용 총액(판관비 아님)" if 단일표시 != "안붓기" else "비움"))
        if r["매출"] and r["영업이익"] is not None:
            r["영업이익률"] = round(r["영업이익"] / r["매출"], 4)
        # **해마다 항등식** — 매출 − 매출원가 − 판관비 = 영업이익 (2026-10-16, S1 리뷰). 실측(NAVER 2022): 영업비용이
        # −6.9조(부호 반전)로 와 회전일수가 음수로 나갔다. 어긋난 해는 범위 산정(회전일수 · 국면)에서 빼라고 표시한다.
        매, 원, 판, 영 = r["매출"], r["매출원가"], r["판관비"], r["영업이익"]
        if None in (매, 판, 영) or not 매:
            r["항등식"] = "재료 없음"
        elif abs(매 - (원 or 0.0) - 판 - 영) <= max(1.0, abs(매) * 0.001):
            r["항등식"] = "일치"
        elif abs(매 - (원 or 0.0) + 판 - 영) <= max(1.0, abs(매) * 0.001) and 판 < 0:
            r["항등식"] = "불일치 — 판관비(영업비용) 부호 반전(크기로 읽으면 맞는다)"
        elif 원 is not None and abs(매 + 원 - abs(판) - 영) <= max(1.0, abs(매) * 0.001) and 원 < 0:
            r["항등식"] = "불일치 — 매출원가 부호 반전(크기로 읽으면 맞는다)"
        else:
            r["항등식"] = "불일치 — 차 %s" % "{:,.0f}".format(매 - (원 or 0.0) - 판 - 영)
        줄.append(r)
    전환, 이전 = [], None
    for r in 줄:
        if r["영업이익"] is None or not r["매출"]:
            continue
        s = 1 if r["영업이익"] >= 0 else -1
        if 이전 is not None and s != 이전[1]:
            전환.append("%d→%d" % (이전[0], r["사업연도"]))
        이전 = (r["사업연도"], s)
    # **구조 단절 후보** — 매출이 전년 대비 1/3 미만이거나 3배를 넘는 해(분할 · 합병 · 부분 연도 · 연결 범위 변화).
    # 끊을지는 사람이 정한다(CLAUDE.md 「앵커 표를 구조 블록으로 끊는다」) — 도구는 자리만 짚는다.
    단절 = []
    for a, b in zip(줄, 줄[1:]):
        if a["매출"] and b["매출"] and a["매출"] > 0 and b["매출"] > 0:
            배 = b["매출"] / a["매출"]
            if 배 > 3.0 or 배 < 1 / 3.0:
                단절.append({"해": "%d→%d" % (a["사업연도"], b["사업연도"]), "매출배수": round(배, 2),
                           "의심": ("%d 이 부분 연도(설립 · 분할 직후)일 수 있다" % a["사업연도"]) if 배 > 3.0
                           else ("%d 에 사업 처분 · 분할이 있었을 수 있다" % b["사업연도"])})
    어긋난해 = [r["사업연도"] for r in 줄 if str(r.get("항등식", "")).startswith("불일치")]
    return {"시계열": 줄, "부호전환": 전환, "부호전환횟수": len(전환), "단일표시": 단일표시,
            "항등식_어긋난해": 어긋난해, "구조단절후보": 단절}


def 폴더조립(raw, 기준일, 별도=False, 입력=None, 단일표시=단일표시기본, 해수=2):
    """`raw` 폴더(받아 둔 `_raw/`)만 읽어 조립한다. 파일을 쓰지 않는다 — 결과 dict 를 낸다.
    해수 = 실적 회계연도 열의 수(S10-16 — 기본 2 · 템플릿 `기간.실적연도수` 와 맞춘다). 셋째 해부터는 앵커 시계열의 그 해 사업보고서(잔액 당기말 ·
    손익 연간)만 읽는다 — 반기보고서의 전기 · 전전기 비교 칸은 둘째 · 첫째 해에만 있다."""
    구분 = "별도" if 별도 else "연결"
    후보 = sorted(glob.glob(os.path.join(raw, "dart_재무_%s_*.json" % 구분)))
    길 = 입력 or (후보[-1] if 후보 else None)
    if not 길 or not os.path.exists(길):
        raise SystemExit("%s/dart_재무_%s_*.json 이 없습니다 — dart_fetch.py 를 먼저 도십시오"
                         % (raw, 구분))

    d = json.loads(io.open(길, encoding="utf-8").read())
    항목 = d.get("list") or []

    # ── 연간 손익 두 해는 **앵커 시계열**에서 받는다 ─────────────────────
    # 반기보고서의 손익에는 전기 연간 값이 없다(frmtrm_amount=None,
    # frmtrm_add_amount 는 전년 **동반기**다). 앵커의 각 해 `list` 가 그 해
    # 사업보고서 전체 재무제표라 거기서 연간 값을 받는다 — 새로 조회하지 않는다.
    앵커길 = os.path.join(raw, "dart_앵커시계열.json")
    연간 = {}
    # **별도 모드에서는 앵커를 섞지 않는다.** 앵커 시계열은 연결 기준이라 별도 열에
    # 연결 연간을 채우면 **두 회사가 한 표에 섞인다** — 실측(두산에너빌리티):
    # 별도 조립의 FY2024 매출이 16.2조(연결)로 찍혔다(별도는 그 절반이 안 된다).
    # 별도 연간 손익은 사업보고서의 별도 재무제표에서 와야 한다 — 없으면 비운다.
    if 별도:
        앵커길 = ""
    보탠 = {}                                   # 2026-10-25 Y2 — `이력판정.py --앵커에보태기` 가 보탠 해(신고서 · 분할회사 주석)
    if 앵커길 and os.path.exists(앵커길):
        try:
            앵 = json.loads(io.open(앵커길, encoding="utf-8").read())
            for h in (앵.get("해") or []):
                연간[int(h.get("사업연도") or 0)] = h.get("list") or []
                if h.get("원천"):
                    보탠[int(h.get("사업연도") or 0)] = h["원천"]
        except Exception:                                    # noqa: BLE001
            pass
    # 보탠 해는 앵커 네 줄(관측 · 관문 ② 재료)에는 남기고 13번 실적 열에는 쓰지 않는다 — 재무상태표 칸이 없고 보고실체가 다를 수 있다
    # (분할 전 사업 · 신고서 소급 결합). 실적 열은 대상 자신의 사업보고서 해만이다
    앵커연간 = 연간
    연간 = {y: v for y, v in 연간.items() if y not in 보탠}
    끝해 = max(연간) if 연간 else int(기준일[:4]) - 1
    해수 = max(2, int(해수 or 2))
    해들 = tuple(range(끝해 - 해수 + 1, 끝해 + 1))
    앞해들 = 해들[:-2]                      # S10-16 — 셋째 해부터(앵커 사업보고서만)
    해들 = 해들[-2:]

    열원천 = [([(연간.get(y), "thstrm_amount")], (연간.get(y), "thstrm_amount", None)) for y in 앞해들] + [
        # (잔액 원천들, 흐름 원천) — 잔액은 앞에서부터 본다, 흐름은 (항목들, 칸, 폴백칸)
        # **반기보고서의 BS 에는 전전기말이 없다**(bfefrmtrm 이 빈다) — 첫 열의
        # 잔액도 앵커 그 해(사업보고서)의 당기말에서 받는다
        ([(연간.get(해들[0]), "thstrm_amount"), (항목, "bfefrmtrm_amount")],
         (연간.get(해들[0]), "thstrm_amount", None)),
        # **둘째 열도 사업보고서 당기말이 먼저다** (2026-09-13, 펄어비스 45행 사채 FY2025 빈칸) —
        # 반기 전기말 비교(frmtrm)에는 줄이 빠진 계정이 있다. 거기 없는 행만 반기 frmtrm 으로 메운다.
        ([(연간.get(해들[1]), "thstrm_amount"), (항목, "frmtrm_amount")],
         (연간.get(해들[1]), "thstrm_amount", None)),
        # **반기 함정** — 손익·CF 는 누계(add)를 먼저 보고, 연차라 add 가 비면
        # thstrm 으로 떨어진다
        ([(항목, "thstrm_amount")], (항목, "thstrm_add_amount", "thstrm_amount")),
    ]
    열이름 = ["FY%d" % y for y in 앞해들] + ["FY%d" % 해들[0], "FY%d" % 해들[1], "당기"]
    out = 조립(열원천, 단일표시, 열이름)
    out["열설명"] = (["FY%d(잔액 · 손익 모두 앵커 그 해 사업보고서 — S10-16)" % y for y in 앞해들] +
                  ["FY%d(잔액 사업보고서 기말·손익 앵커 연간)" % 해들[0],
                   "FY%d(잔액 사업보고서 기말 → 없으면 반기 전기말·손익 앵커 연간)" % 해들[1],
                   "당기(잔액 당기말·손익 누계 add)"])
    out["열이름"] = 열이름
    없는해 = [y for y in 앞해들 if not 연간.get(y)]
    if 없는해:
        out["주의"].append("**앵커에 %s 사업보고서가 없어 그 열을 비웠습니다** — `dart_fetch.py --해수` 로 앵커를 늘리거나 `--해수` 를 줄이십시오"
                          % " · ".join("%d" % y for y in 없는해))

    # ── 현금흐름표 순이익 행이 3개월인지 — dart_fetch 와 같은 판정 ─────────
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import dart_fetch as _DF                                # noqa: PLC0415
        대조 = _DF._현금순이익대조(항목)
    except Exception:                                          # noqa: BLE001
        대조 = None
    if 대조:
        out["현금흐름표_순이익대조"] = {k: v for k, v in 대조.items() if k != "행"}
        out["주의"].append(
            "**당기 열 현금흐름표의 「%s」 행이 손익계산서 누계와 다릅니다 — 판정 %s** "
            "(CF API %s / 손익 3개월 %s / 손익 누계 %s). 이 행을 쓰는 곳은 손익계산서 누계를 쓰십시오"
            % (대조["계정"], 대조["판정"], "{:,.0f}".format(대조["준값"]),
               "{:,.0f}".format(대조["손익_3개월"]) if 대조["손익_3개월"] is not None else "—",
               "{:,.0f}".format(대조["손익_누계"])))

    if 연간 and not 별도:
        out["앵커"] = 앵커네줄(앵커연간, 단일표시)
        앵 = out["앵커"]
        for r in 앵.get("시계열") or []:                     # 보탠 해 표지 — 앵커 표에서 「신고서 · 분할회사 주석」 해로 보이게
            if r.get("사업연도") in 보탠:
                r["원천"] = {k: 보탠[r["사업연도"]].get(k) for k in ("종류", "접수번호", "보고실체", "개월") if 보탠[r["사업연도"]].get(k) is not None}
        if 보탠:
            out["주의"].append("앵커에 신고서 · 분할회사 주석에서 보탠 해 %s 가 있다 — 앵커 네 줄(관측)에만 쓰고 13번 실적 열에는 쓰지 않았다(`이력판정.py`)"
                              % " · ".join("%d" % y for y in sorted(보탠)))
        if 앵.get("항등식_어긋난해"):
            out["주의"].append(
                "**앵커 %d해에서 「매출 − 매출원가 − 판관비 = 영업이익」이 어긋납니다** — %s. "
                "그 해는 회전일수 · 국면 · 상하한 범위 산정에서 빼십시오(부호 반전이면 크기로 읽으면 맞습니다)"
                % (len(앵["항등식_어긋난해"]), " · ".join("%d %s" % (r["사업연도"], r["항등식"][6:])
                                                     for r in 앵["시계열"] if r["사업연도"] in 앵["항등식_어긋난해"])))
        if 앵.get("구조단절후보"):
            out["주의"].append(
                "**앵커에 구조 단절 후보가 %d곳 있습니다** — %s. 앵커 표를 구조 블록으로 끊을지 정하십시오"
                "(분할 · 합병 · 부분 연도는 회전일수와 이익률 범위를 오염시킵니다)"
                % (len(앵["구조단절후보"]), " · ".join("%s 매출 %.2f배(%s)" % (x["해"], x["매출배수"], x["의심"])
                                                   for x in 앵["구조단절후보"])))
    if 별도 and not 연간:
        out["주의"].append(
            "**별도 모드 — 연간 두 해를 비웠습니다.** 앵커 시계열은 연결 기준이라 "
            "섞지 않습니다. 별도 연간 손익이 필요하면 사업보고서의 별도 재무제표를 "
            "받아 넣으십시오")
    elif not 연간:
        out["주의"].append(
            "**앵커 시계열이 없어 연간 손익 두 해를 못 채웠습니다** — "
            "`dart_fetch.py --회사 … --기준일 …` 로 앵커를 먼저 받으십시오. "
            "반기보고서의 손익에는 전기 연간 값이 없습니다")
    # ── S10R1-N1 — 전년 동기 누계(손익 흐름 줄). 기준일 열이 누계(반기 · 분기 · 9개월)면 반기보고서의 `frmtrm_add_amount` 가 전년 같은 기간의
    # 누계다(새로 조회하지 않는다 — 같은 응답). 잔여 기간 열을 「전년 동기 × (1 + g)」로 잡는 길(`잔여기간.py --경로 전년동기`)의 재료다.
    # 연차 보고서(기준일 = 결산일)면 그 칸이 없어 비운다. 값은 원(이 파일의 다른 줄과 같은 단위)
    # N6-b(2026-10-18) — **1분기 보고서(11013)는 누계 = 3개월이라 `frmtrm_add_amount` 가 비는 응답이 있다.** 그때만 `frmtrm_amount`(전년 1분기 3개월
    # = 전년 1분기 누계)로 떨어진다. 반기(11012) · 3분기(11014)는 frmtrm_amount 가 전년 그 분기 3개월이라 누계가 아니므로 폴백하지 않는다.
    보고서코드 = (re.search(r"_(1101[1-4])\.json$", os.path.basename(길)) or [None, None])[1]
    일분기 = 보고서코드 == "11013" or (보고서코드 is None and 기준일[5:7] == "03")
    try:
        전 = 조립([([(None, "frmtrm_amount")], (항목, "frmtrm_add_amount", "frmtrm_amount" if 일분기 else None))], 단일표시, ["전년동기"])   # 잔액 원천 없음 — 흐름 줄만 선다
        전년 = {k: v[0] for k, v in (전.get("원천") or {}).items() if isinstance(v, list) and v and v[0] is not None}
        전년.update({k: v[0] for k, v in (전.get("검산행") or {}).items() if isinstance(v, list) and v and v[0] is not None and k not in 전년})
    except Exception:                                          # noqa: BLE001
        전년 = {}
    if 전년:
        out["전년동기"] = {"설명": "기준일 누계 열의 전년 같은 기간 누계(%s — 손익 흐름 줄만 · 원)" % (
                           "1분기보고서 frmtrm_add_amount, 비면 frmtrm_amount(전년 1분기 3개월 = 누계 — N6-b)" if 일분기 else "반기 · 분기보고서 frmtrm_add_amount"),
                       "보고서코드": 보고서코드,
                       "원천": {k: 전년[k] for k in sorted(전년, key=lambda x: int(x) if x.isdigit() else 9999)}}
    out["원본"] = os.path.basename(길)
    out["기준일"] = 기준일
    out["기준"] = 구분
    return out


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--기준일", "--재무기준일", dest="기준일", default=None,
                    help="재무기준일 F YYYY-MM-DD — 실적 열 · 당기 열이 서는 날(평가기준일 전에 제출된 마지막 분기말 · 옛 이름 --기준일 은 지금 뜻 그대로)")
    ap.add_argument("--평가기준일", default=None, help="평가기준일 T YYYY-MM-DD — 산출 머리에만 적는다(조립 값은 바꾸지 않는다)")
    ap.add_argument("--가정", default=None, help="가정 파일 — 날짜 인자를 비우면 기준일.py 로 F · T 를 푼다(F 가 없으면 F = T)")
    ap.add_argument("--별도", action="store_true", help="연결 대신 별도(OFS)를 쓴다")
    ap.add_argument("--입력", default=None)
    ap.add_argument("--원천폴더", default=RAW,
                    help="받아 둔 _raw 폴더(기본: 스크립트 부모의 _raw). 읽기만 한다")
    ap.add_argument("--출력", default=None,
                    help="산출 경로(기본: 원천폴더/원천_조립.json)")
    ap.add_argument("--해수", type=int, default=2,
                    help="실적 회계연도 열의 수(기본 2) — 가정 템플릿의 기간.실적연도수(기본 3)와 맞춘다. 셋째 해부터는 앵커 시계열의 사업보고서로 채운다(S10-16)")
    ap.add_argument("--단일표시", default=단일표시기본, choices=sorted(단일표시경로),
                    help="영업수익/영업비용 단일 표시 회사의 63·65 처리 경로. " +
                         " / ".join("%s: %s" % (k, v[:40]) for k, v in 단일표시경로.items()))
    a = ap.parse_args()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import 기준일인자 as _기인                                  # noqa: PLC0415 — 날짜 둘(2026-10-25)
    a.기준일 = _기인.풀기(a.기준일, a.가정, _기인.재무, 인자="--기준일")
    a.평가기준일 = _기인.풀기(a.평가기준일, a.가정, _기인.평가, 인자="--평가기준일")
    if not a.기준일:
        ap.error("--기준일(재무기준일) 또는 --가정 이 있어야 합니다")

    raw = a.원천폴더
    # ── 번호↔방 대조 — 실측(HD한국조선): 하드코딩한 고유번호가 다른 회사
    # (자산 394조 HD현대 추정)를 받아 매출이 6배로 보였다. 방 폴더명이 종목코드
    # 꼴이면 기업개황의 종목코드와 대 본다.
    _방 = os.path.basename(os.path.dirname(os.path.abspath(raw)))
    _개황길 = os.path.join(raw, "dart_기업개황.json")
    if _방.isdigit() and len(_방) == 6 and os.path.exists(_개황길):
        try:
            _개황 = json.load(io.open(_개황길, encoding="utf-8"))
            _종목 = (_개황.get("stock_code") or "").strip()
            if _종목 and _종목 != _방:
                sys.exit("**다른 회사의 재무입니다** — 방 폴더는 %s 인데 받아 둔 "
                         "기업개황은 %s(%s)입니다. dart_fetch 의 --회사 고유번호가 "
                         "틀렸습니다(찾기 JSON 을 다시 보십시오)."
                         % (_방, _종목, _개황.get("corp_name")))
        except SystemExit:
            raise
        except Exception:
            pass

    out = 폴더조립(raw, a.기준일, a.별도, a.입력, a.단일표시, a.해수)
    out["재무기준일"] = out.get("기준일") or a.기준일                  # 「기준일」 은 지금 뜻 그대로 재무기준일 F
    if a.평가기준일:
        out["평가기준일"] = a.평가기준일

    dst = a.출력 or os.path.join(raw, "원천_조립.json")
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    io.open(dst, "w", encoding="utf-8").write(
        json.dumps(out, ensure_ascii=False, indent=1))

    def 쉼표(v):
        return "{:,.0f}".format(v) if v is not None else "—"

    print("원본 %s (%s)" % (out["원본"], out["기준"]))
    print()
    for 행 in sorted((int(k) for k in out["원천"]), key=int):
        셋 = out["원천"][str(행)]
        print(("%3d %-20s " + " ".join(["%18s"] * len(셋)) + "  %s")              # S10-16 — 열 수는 --해수 + 1
              % (행, 행이름.get(행, ""), *[쉼표(v) for v in 셋],
                 (out["태그"][str(행)] or ["**못 찾음**"])[0][:52]))
    print()
    print("  검산행(스캐폴드 수식칸 — 붓지 않는다)")
    for 행 in out["수식칸"]:
        print(("%3d %-20s " + " ".join(["%18s"] * len(out["검산행"][str(행)])))
              % (행, 행이름.get(행, ""), *[쉼표(v) for v in out["검산행"][str(행)]]))
    어긋 = [x for x in out["소계대조"] if x["결과"] != "일치"]
    print("  소계 대조 %d건 · 어긋남 %d건" % (len(out["소계대조"]), len(어긋)))
    for x in 어긋:
        print("     %-6s %-28s 공시 %18s 행합 %18s 차 %16s"
              % (x["열"], x["소계"], 쉼표(x["공시"]), 쉼표(x["행합"]), 쉼표(x["차"])))
    if out.get("행없는계정"):
        print("  13번 행이 안 읽어 간 재무상태표 계정(당기)")
        for x in out["행없는계정"]:
            print("     %-28s %18s  %s" % (x["계정명"][:26], 쉼표(x["금액"]), x["태그"][:50]))
    if out["기타후보"]:
        print()
        print("  「기타」 계열 — **배분은 사람이 합니다**")
        for x in out["기타후보"]:
            print("     %-24s %18s  %s"
                  % (x["계정명"][:22], "{:,.0f}".format(x["금액"]), x["태그"][:40]))
    if out.get("앵커"):
        앵 = out["앵커"]
        print()
        print("  앵커 네 줄 — 부호 전환 %d회 %s" % (앵["부호전환횟수"], 앵["부호전환"]))
        for r in 앵["시계열"]:
            print("     %d  매출 %18s  원가 %16s  판관 %18s  영업 %18s  %s"
                  % (r["사업연도"], 쉼표(r["매출"]), 쉼표(r["매출원가"]), 쉼표(r["판관비"]),
                     쉼표(r["영업이익"]), r["비용표시"]))
    if out["주의"]:
        print()
        for s in out["주의"]:
            print("  ※ %s" % s)
    if out["빈필수"]:
        print()
        print("  ★ **꼭 있어야 하는데 빈 행** — %s"
              % " · ".join("%d %s" % (r, 행이름.get(r, "?")) for r in out["빈필수"]))
        print("     계정명을 가정하지 말고 원본 JSON 의 계정 목록을 훑으십시오. "
              "**비슷한 값으로 메우지 않습니다.**")
    print()
    print("저장: %s" % dst)


if __name__ == "__main__":
    main()

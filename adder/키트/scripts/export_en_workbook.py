# -*- coding: utf-8 -*-
"""Convert an ADDER DCF workbook (.xlsx) into a 100% American English 17-sheet workbook (v1.2.1)."""
from __future__ import annotations
import argparse
import io
import json
import os
import re
import sys

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLE_PATH = os.path.join(HERE, "en_workbook_bundle.json")

KO_RE = re.compile(r"[가-힣「」『』]")
ROMAN_RE = re.compile(r"^([IVXLCDM]+)\.\s+(.+)$")
LEFT_RE = re.compile(r'LEFT\(([^()]*(?:\([^()]*\)[^()]*)*),(\d+)\)(\s*(?:<>|=)\s*)"([^"]*)"')

VAR_CODE_MAP = {
    "매출채권비율": "receivables days",
    "매출채권회전일수": "receivables days",
    "재고자산비율": "inventory days",
    "재고자산회전일수": "inventory days",
    "재고회전일수_원가": "inventory days (COGS)",
    "매입채무비율": "payables days",
    "매입채무회전일수": "payables days",
    "기타순운전자본비율": "other NWC ratio",
    "상각률_기초순액": "depreciation rate (opening net PP&E)",
    "상각매출비율": "D&A to revenue",
    "매출원가율": "COGS ratio",
    "영업이익률_연차": "annual operating margin",
    "영업이익률": "operating margin",
    "매출성장률": "revenue growth",
    "연구개발비율": "R&D ratio",
    "판관비율": "SG&A ratio",
    "산업고용증가율": "industry employment growth",
    "산업임금증가율": "industry wage growth",
}

NODE_KEY_MAP = {
    "감가상각": "depreciation",
    "법인세": "income tax",
    "성장CAPEX": "growth CAPEX",
    "유지CAPEX": "maintenance CAPEX",
    "연구개발": "R&D",
    "인건비": "payroll",
    "운전자본": "working capital",
    "운전자본.매출채권": "working capital (receivables)",
    "운전자본.재고자산": "working capital (inventory)",
    "운전자본.매입채무": "working capital (payables)",
    "운전자본.기타": "working capital (other)",
    "운전자본.선수금": "working capital (deferred revenue)",
    "운전자본.미지급비용": "working capital (accrued expenses)",
}


def _tr_var_code(v: str) -> str:
    v = v.strip()
    if v in VAR_CODE_MAP:
        return VAR_CODE_MAP[v]
    m = re.match(r"^(유효세율|실효세율)_(\d+)(?:년|해)$", v)
    if m:
        return f"{m.group(2)}-yr effective tax rate"
    return v.replace("_연차", " (annual)")


def _repl_80_interval(m):
    rng = m.group(1).strip().replace("~", "to")
    k = m.group(2).strip()
    grp = "matched peers" if "비슷한" in m.group(3) else "full peer group"
    var_en = _tr_var_code(m.group(4))
    cal = "backtest-calibrated" if "백테스트" in m.group(5) else "uncalibrated"
    yr_lbl = "1-yr ahead" if k == "1" else f"{k}-yr ahead"
    return f"80% interval {rng} ({yr_lbl}, {grp}, {var_en}, {cal})"


def _repl_peer_pct(m):
    grp_raw, p1, t1, p2, t2 = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
    if grp_raw == "전체":
        grp = "All firms"
    elif grp_raw.startswith("같은 규모"):
        inner = grp_raw[len("같은 규모"):].strip("()")
        inner = re.sub(r"([0-9,]+(?:\.[0-9]+)?)\s*억\s*달러", _eok_usd_repl, inner).replace("이상", "or above")
        grp = f"Same-size peers ({inner})"
    else:
        grp = grp_raw
    t1_en = " (lower tail)" if t1 == "아래 꼬리" else (" (upper tail)" if t1 == "위 꼬리" else "")
    t2_en = " (lower tail)" if t2 == "아래 꼬리" else (" (upper tail)" if t2 == "위 꼬리" else "")
    return f"{grp}: start {p1}{t1_en}, end {p2}{t2_en}"


# Structured regex translators for auto-generated strings across Sheets 1, 13, 14, 16, 17
STRUCTURED_REGEXES = [
    # Sheet 1 & Sheet 14 terminal growth / WACC / Monte Carlo / sensitivity strings
    (re.compile(r"^예측\s*([\d.]+%)\s*[·;]\s*영구\s*([\d.]+%)$"), r"Forecast \1, terminal \2"),
    (re.compile(r"^무위험이자율\s*([\d.]+%)보다 낮음$"), r"Below risk-free rate (\1)"),
    (re.compile(r"^영구성장률 상한\(무위험이자율\s*([\d.]+%)\)\s*초과\s*[—:-]\s*지금 현금흐름이 정상 상태가 아니다$"),
     r"Exceeds terminal growth cap (Rf \1): current cash flow is not steady-state"),
    (re.compile(r"^(.+?)\s*[·;]\s*결합 몫\s*([\d.]+%)$"),
     lambda m: f"{m.group(1).replace('영구기간 ROIC(2)', 'Terminal ROIC (RONIC)').replace('영구기간 ROIC', 'Terminal ROIC').strip()}; joint share {m.group(2)}"),
    (re.compile(r"^(\d+)판\(실패\s*(\d+)\)\s*[·;]\s*주효과 R²\s*([\d.]+%)\s*[·;]\s*상호작용\s*[·;]\s*비선형 몫\s*([\d.]+%)$"),
     r"\1 runs (\2 failed); main-effect R² \3; interaction & nonlinear share \4"),
    (re.compile(r"^기준 주당가치\s*(-?[\d,.]+)\s*[—:-]\s*판 가운데\s*(\d+%)\s*자리\s*[·;]\s*종가\s*(-?[\d,.]+)\s*[—:-]\s*(\d+%)\s*자리$"),
     r"Base value/sh \1 (\2 of runs); close \3 (\4)"),
    (re.compile(r"^기준 주당가치\s*(-?[\d,.]+)\s*[—:-]\s*판 가운데\s*(\d+%)\s*자리\s*[·;]\s*종가 없음$"),
     r"Base value/sh \1 (\2 of runs); no close"),
    (re.compile(r"^근거 범위\s*[—:-]\s*자본비용 대안 사양\s*(\d+)개\(([^)]+)\)$"),
     r"Evidence range: \1 alternative WACC specs (\2)"),
    (re.compile(r"^근거 범위\s*[—:-]\s*영구성장률\s*([^(]+)\(g 기본값\s*([\d.]+%)\s*±\s*([\d.]+)%p.*?\)$"),
     r"Evidence range: terminal g \1 (default \2 +/- \3 pp; capped below WACC & Rf)"),
    (re.compile(r"^통계 제안\s*[—:-]\s*계수사전\(\[계산\s*[—:-]\s*패널 산업 사전\s*(SIC\s*\d+)\((\d+)곳\)\s*[·;]\s*Vasicek w\s*([\d.]+).*?\]?\)$"),
     r"Statistical prior: industry panel \1 (\2 firms); Vasicek w \3"),
    (re.compile(r"^통계 제안\s*[—:-]\s*수축\(\[계산\s*[—:-]\s*경험적 베이즈 수축\(동종\s*(\S+)\s*(\d+)곳\s*[·;]\s*수축률\s*([\d.]+)\)\]\)(?:\s*[·;]\s*국면\(.*\))?$"),
     lambda m: f"Statistical prior: empirical Bayes shrinkage (peer {_tr_var_code(m.group(1))}, {m.group(2)} firms, shrinkage {m.group(3)})"),
    (re.compile(r"^민감도 표의 폭\s*([^\(]+)\(근거 범위 아님\s*[·;]\s*지렛대라 넣었다\)$"),
     r"Sensitivity grid width \1 (reference width; included as high-leverage driver)"),
    (re.compile(r"^엔진 자 실적\(([^)]+)\)\s*([A-Za-z0-9~]+)\((\d+)해\)$"),
     lambda m: f"Reported series ({m.group(1).replace('기타 순운전자본', 'other NWC').replace('원가 줄 금액', 'cost line').replace('매출액', 'revenue')}) {m.group(2)} ({m.group(3)} yrs)"),
    (re.compile(r"^전사 매출 실적\s*[—:-]\s*(\d+~\d+)\s*연 증가율\s*(\d+)개.*$"),
     r"Consolidated reported revenue: \2 annual growth obs. (\1, excl. structural-break years)"),
    (re.compile(r"^외부 제약 경로\s*[—:-]\s*미국 법인세\s*[—:-]\s*(.+)$"),
     r"External statutory constraint (US corporate tax): OBBBA / CAMT & Pillar Two safe-harbor path"),
    (re.compile(r"^외부 제약 경로\s*[—:-]\s*미국 수입 관세\(([^)]+)\).*$"),
     r"External statutory constraint (US import tariffs — Sections 232/301)"),
    (re.compile(r"^선언 손잡이 범위\((.+)\)$"),
     r"Declared driver range (\1)"),

    # Sheet 17 R5 summary
    (re.compile(r"동인지도 노드\s*(\d+)"), r"Driver map \1 nodes"),
    (re.compile(r"변수카드\s*(\d+)장\(([^)]+)\)"), r"variable cards \1 (\2)"),
    (re.compile(r"결합민감도\s*(\d+)판\(([^)]+)\)"), r"joint sensitivity \1 runs (\2)"),
    (re.compile(r"(동인지도|변수카드|결합민감도)\s*없음\(([^)]+)\)"),
     lambda m: f"{ {'동인지도':'Driver map','변수카드':'variable cards','결합민감도':'joint sensitivity'}[m.group(1)] } missing ({m.group(2)})"),

    # Sheet 17 Col C node labels
    (re.compile(r"^매출구분(\d+)\s*P\s*[·;]\s*(.+?)\s*[—:-]\s*판매단가.*$"),
     r"Segment \1 P (\2): unit price / ARPU / take rate"),
    (re.compile(r"^매출구분(\d+)\s*Q\s*[·;]\s*(.+?)\s*[—:-]\s*물량.*$"),
     r"Segment \1 Q (\2): volume / capacity / unit economics"),
    (re.compile(r"^매출구분(\d+)\s*[·;]\s*(.+)$"),
     r"Segment \1: \2"),

    # Sheet 17 Col O & Q statistical interval, peer percentile & shrinkage labels
    (re.compile(r"^((?:A-\d+\s+)?)80% 구간\s*[—:-]\s*정의가 다름\(([^)]+)\)$"),
     lambda m: f"{m.group(1)}80% interval: definition differs ({_tr_var_code(m.group(2))})"),
    (re.compile(r"80% 구간\s*([^\(]+)\((\d+)(?:년|해|\s*yrs)\s*뒤\s*[·;]\s*(비슷한 자리|같은 집단 전체)\s*[·;]\s*([^·;\)]+)\s*[·;]\s*(백테스트 보정|보정 없음)\)"),
     _repl_80_interval),
    (re.compile(r"(SIC\s*\d+|전체|같은 규모\([^)]+\))\s*첫\s*(\d+%)(?:\((아래 꼬리|위 꼬리)\))?\s*[·;]\s*끝\s*(\d+%)(?:\((아래 꼬리|위 꼬리)\))?"),
     _repl_peer_pct),
    (re.compile(r"^계수사전\s+(.+)$"), r"Prior \1"),
    (re.compile(r"^수축\s+(.+)$"), r"Shrinkage \1"),

    # Sheet 17 Col J (`동인지도짓기.py` + `동인진단.py` auto-generated diagnostic basis strings)
    (re.compile(r"^\[판단\]\s*동인진단에\s*원가줄(\d+)\s*항목이 없다.*$"),
     r"[Judgment] No driver-test item for cost line \1; selection carried over from model structure"),
    (re.compile(r"^\[판단\]\s*동인진단\s*(\S+)\s*[—:-]\s*확인 불가.*선택은 가정 구조를 옮겼다$"),
     lambda m: f"[Judgment] Driver test ({NODE_KEY_MAP.get(m.group(1), m.group(1))}): unverifiable; selection carried over from model structure"),
    (re.compile(r"^\[도구\]\s*동인진단\s*(\S+)\s*[—:-]\s*해당 없음$"),
     lambda m: f"[Tool] Driver test ({NODE_KEY_MAP.get(m.group(1), m.group(1))}): N/A"),
    (re.compile(r"^\[도구\]\s*동인진단\s*원가줄(\d+)\s*[—:-]\s*(.+)$", re.S),
     lambda m: _tr_cost_diag(m.group(1), m.group(2))),
    (re.compile(r"^\[도구\]\s*동인진단\s*연구개발\s*[—:-]\s*기능별 R&D.*원가 줄\s*(\d+).*$", re.S),
     r"[Tool] Driver test (R&D): functional R&D modeled as cost line \1 (default inflation-indexed + level adjustment)"),
    (re.compile(r"^\[도구\]\s*동인진단\s*인건비\s*[—:-]\s*산정방식\s*=\s*미분리.*$", re.S),
     r"[Tool] Driver test (payroll): method = combined (functional presentation includes payroll & SBC; functional cost lines indexed to workforce)"),
    (re.compile(r"^\[도구\]\s*동인진단\s*인건비\s*[—:-]\s*산정방식\s*=\s*인원.*$", re.S),
     r"[Tool] Driver test (payroll): method = headcount x pay per employee (headcount path = growth rate)"),
    (re.compile(r"^\[도구\]\s*동인진단\s*유지CAPEX\s*[—:-]\s*(.+)$", re.S),
     lambda m: "[Tool] Driver test (maintenance CAPEX): " + (
         "asset-light profile; maintenance CAPEX linked to revenue" if "자산 경량" in m.group(1)
         else "measured from cash PP&E additions vs. D&A / opening net PP&E")),
    (re.compile(r"^\[도구\]\s*동인진단\s*성장CAPEX\s*[—:-]\s*(.+)$", re.S),
     lambda m: "[Tool] Driver test (growth CAPEX): " + (
         "explicit CAPEX projects modeled (F); residual segments use sales-to-capital if applicable" if "가정에 프로젝트" in m.group(1)
         else "asset-light; revenue-linked maintenance CAPEX covers reinvestment" if ("자산 경량 —" in m.group(1))
         else "sales-to-capital rule (Δrevenue ÷ A-859) paired with D&A-linked maintenance CAPEX")),
    (re.compile(r"^\[도구\]\s*동인진단\s*감가상각\s*[—:-]\s*(.+)$", re.S),
     lambda m: "[Tool] Driver test (depreciation): " + (
         "PP&E depreciation ÷ opening net PP&E; additions >30% of opening net PP&E (vintage noted, rate method used)" if "넘는다" in m.group(1)
         else "observed PP&E depreciation rate applied to opening net PP&E")),
    (re.compile(r"^\[도구\]\s*동인진단\s*(운전자본\.\S+)\s*[—:-]\s*(.+)$", re.S),
     lambda m: f"[Tool] Driver test ({NODE_KEY_MAP.get(m.group(1), m.group(1))}): selected from historical reported turnover/ratio range"),
    (re.compile(r"^\[도구\]\s*동인진단\s*법인세\s*[—:-]\s*(.+)$", re.S),
     lambda m: "[Tool] Driver test (income tax): " + (
         "SEC companyfacts tax-credit & effective-tax-rate series extracted" if "공제 자료 있음" in m.group(1)
         else "no XBRL tax-credit tags in companyfacts (verify in 10-K rate reconciliation); effective tax rate series extracted")),
    (re.compile(r"^\[도구\]\s*합류 매출구분판정\s*[—:-]\s*(.+)$", re.S),
     lambda m: _tr_seg_verdict(m.group(1))),

    # Sheet 17 Col N (`동인진단.py` range-source templates)
    (re.compile(r"^(FY\S+)\s*이연법인세자산\s*([\d,.]+)\s*÷\s*납부 평균\s*([\d,.]+)\s*=\s*([\d.]+)(?:년|해)\(±(\d+%)\).*$", re.S),
     r"\1 deferred tax assets \2 ÷ avg. cash tax paid \3 = \4 yrs (±\5): DTA depletion pace for tax convergence"),
    (re.compile(r"^(FY\S+)\s*이월결손금\s*([\d,.]+)\s*[—:-]\s*결손금 금액 행과 세율 수렴 근사 가운데 하나만.*$", re.S),
     r"\1 NOL carryforward \2: model via either explicit NOL row or tax-rate convergence (no double counting)"),
    (re.compile(r"^(?:(\d+)(?:년|해) 구간|순환 회사\s*[—:-]\s*정점 구간의 마지막 회계연도끼리)\s*Δ매출\s*÷\s*Δ유형자산.*$", re.S),
     r"Historical multi-year Δrevenue ÷ Δnet PP&E (sales-to-capital reinvestment benchmark; paired with D&A-linked maintenance CAPEX)"),
    (re.compile(r"^(?:유형 몫 상각|가정 원천|\d[\d,.]*\(감가상각).*?÷\s*기초.*—\s*(FY.+?)\s*—\s*156\s*은 관측 상각률을 넣는다.*$"),
     r"Observed PP&E depreciation ÷ opening net PP&E (\1); A-156 uses observed depreciation rate"),
    (re.compile(r"^계수 시계열의\s*(국면별\s*[·;]\s*)?최저\s*[·;]\s*최고\(([^)]+)\).*$"),
     lambda m: f"Historical coefficient min–max{' by regime' if m.group(1) else ''} ({m.group(2)}): scenarios selected within historical range"),
    (re.compile(r"^구조 선택\(값 아님\)\s*[—:-]\s*기능별 총액.*$"),
     r"Structural choice (not a numeric cell): functional cost totals already include payroll & SBC; separate headcount modeling requires re-baselining cost lines"),
    (re.compile(r"^구조 선택\(값 아님\)\s*[—:-]\s*(.+?)\s*을\(를\)\s*합류에서 매출 구분 판매량으로 세우면.*$"),
     r"Structural choice: if operational volume metric is modeled on a revenue segment, cost lines link directly to that metric"),
    (re.compile(r"^구조값\s*[—:-]\s*(FY\S+)\s*총액\s*([\d,.]+)\s*−\s*상각 몫\s*([\d,.]+).*$"),
     r"Structural base (\1): functional total \2 less allocated D&A share \3 (D&A modeled separately via A-168/172)"),
    (re.compile(r"^금액의 로그 추세 잔차\s*[—:-]\s*해마다.*?\((FY[^)]+)\).*$"),
     lambda m: f"Detrended log-level residual min–max ({m.group(1).replace('추세 연', 'annual trend')}): normalizes base-year level while inflation/unit-cost index carries trend"),
    (re.compile(r"^매출 탄력성\s*([^\s]+)\s*신뢰구간.*$"),
     r"Revenue elasticity \1 confidence interval (fixed vs. variable split judgment)"),
    (re.compile(r"^성격 사전\s*±\s*([^\(]+)\(자료 부족\).*$"),
     r"Cost-behavior prior ±\1 (limited sample; fixed vs. variable split judgment)"),
    (re.compile(r"^무형 취득\s*÷\s*매출 강건 중심\s*([^\(]+)\(([^)]+)\).*$"),
     r"Intangible additions ÷ revenue robust center \1 (\2); modeled separately via A-852"),
    (re.compile(r"^물가\s*([^~]+)~\s*그 줄 계수의 로그 추세 연율.*$"),
     r"Inflation floor to historical log-trend rate: own level index used when cost trend exceeds CPI"),
    (re.compile(r"^범위 끝\s*=\s*거시\s*([\d.%+-]+).*?하한 물가\s*([\d.%+-]+).*$"),
     r"Nominal wage growth bounds: BLS macro wage growth (\1) and CPI inflation floor (\2)"),
    (re.compile(r"^실적\s*(\S+)\s*국면별\s*[·;]\s*전체\(([^)]+)\)\s*[—:-]\s*사이클 회사.*$"),
     lambda m: f"Reported {_tr_var_code(m.group(1))} by cycle regime & overall ({m.group(2).replace('해', ' yrs').replace(' · ', ', ')}): cyclical company; scenarios vary by regime"),
    (re.compile(r"^실적\s*(\S+)\s*몇 개년\(([^)]+)\)\s*[—:-]\s*사이클이 아니다.*$"),
     lambda m: f"Multi-year reported {_tr_var_code(m.group(1))} ({m.group(2).replace('해', ' yrs').replace(' · ', ', ')}): non-cyclical; scenarios anchored to multi-year range"),
    (re.compile(r"^실효세율 최근\s*(\d+)해.*$"),
     r"Recent \1-yr effective tax rate converging toward statutory marginal rate in terminal period"),
    (re.compile(r"^(?:여러 해의|증설이 작은 해의|증설이 작은 해가 둘 미만\s*[—:-])\s*현금 유형 CAPEX\s*÷\s*매출.*$"),
     r"Historical cash PP&E CAPEX ÷ revenue benchmark (asset-light revenue-linked maintenance CAPEX; intangibles separate via A-852)"),
    (re.compile(r"^확인 불가\s*[—:-]\s*(?:최근 해\()?(FY\S+?)\)?\s*에 상각.*$"),
     r"Not verifiable: no depreciation in \1 to strip from functional cost totals (avoid double-counting D&A)"),
    (re.compile(r"^확인 불가\s*[—:-]\s*(?:\d+(?:년|해) 구간 하나뿐|유형자산 순장부가 늘고 매출도 는).*$", re.S),
     r"Not verifiable: insufficient positive Δrevenue / ΔPP&E intervals; benchmark against Damodaran Sales-to-Capital"),
    (re.compile(r"^확인 불가\s*[—:-]\s*계수\s*(\d+)해.*$"),
     r"Not verifiable: only \1 yr(s) of observations (fewer than 4); base-year amount kept at 1.0x and indexed to inflation"),
    (re.compile(r"^확인 불가\s*[—:-]\s*근거가 하나뿐이거나 없어 범위를 내지 않는다.*$"),
     r"Not verifiable: single/insufficient wage series; anchor nominal wage growth to company pay trend, macro wages, and CPI floor"),
    (re.compile(r"^확인 불가\s*[—:-]\s*기능별 상각 배분 각주 없음.*?\((FY\S+)\s*\S+\s*몫\s*([\d.]+%)\).*$"),
     r"Not verifiable: no functional D&A allocation footnote; D&A stripped pro rata to functional cost (\1 share \2)"),
    (re.compile(r"^확인 불가\s*[—:-]\s*직원 수\s*(\d+)해.*$"),
     r"Not verifiable: only \1 yr(s) of headcount disclosures; range derived from historical median revenue growth x headcount elasticity [0, 1]"),
]


def _tr_cost_diag(line_no: str, body: str) -> str:
    override = ""
    if "/ [판단]" in body:
        body, _ = body.split("/ [판단]", 1)
        override = "; [Judgment] model structure overrides initial E draft"
    m_b = re.search(r"탄력성\s*b\s*=\s*([-\d.]+)\(90%\s*구간\s*([-\d.]+)~([-\d.]+)\)", body)
    elas = f"; revenue/driver elasticity b = {m_b.group(1)} (90% CI {m_b.group(2)} to {m_b.group(3)})" if m_b else ""
    if "활동 동인 매출액" in body:
        m_oos = re.search(r"표본 밖\s*([\d.]+%)", body)
        oos = f" (out-of-sample error {m_oos.group(1)})" if m_oos else ""
        core = f"activity driver = revenue{oos}{elas}"
    elif "순장부" in body:
        m_oos = re.search(r"표본 밖\s*([\d.]+%)", body)
        oos = f" (out-of-sample error {m_oos.group(1)})" if m_oos else ""
        core = f"activity driver = opening net PP&E{oos}{elas}"
    elif "활동 동인 없음" in body:
        core = f"insufficient common-window physical drivers; anchored to functional cost prior{elas}"
    else:
        core = f"cost-behavior test from historical series{elas}"
    return f"[Tool] Driver test (cost line {line_no}): {core}{override}"


def _tr_seg_verdict(body: str) -> str:
    # Translate verdict codes while keeping English metric names intact
    verdict_map = [
        ("판정 부문별 매출만", "verdict: segment revenue only"),
        ("판정 매출이 한 줄", "verdict: single consolidated revenue line"),
        ("판정 매출 + 물량 절대치", "verdict: revenue + absolute volume"),
        ("판정 매출 + 단가 변동률만", "verdict: revenue + price change only"),
        ("판정 매출 + 단가 변동률", "verdict: revenue + price change"),
        ("판정 매출 + 증가 요인 문장", "verdict: revenue + qualitative MD&A drivers"),
        ("Q지표 공시 없음", "Q metric: not disclosed"),
        ("Q지표 미공시", "Q metric: not disclosed"),
        ("Q지표 없음", "Q metric: none"),
        ("P지표 공시 없음", "P metric: not disclosed"),
        ("P지표 미공시", "P metric: not disclosed"),
        ("P지표 없음", "P metric: none"),
        ("Q지표 ", "Q metric: "),
        ("P지표 ", "P metric: "),
    ]
    out = body
    for k, v in verdict_map:
        out = out.replace(k, v)
    # If Korean descriptive notes from a Korean run remain inside Q/P metric, summarize cleanly
    if KO_RE.search(out):
        parts = [p.strip() for p in out.split(" · ")]
        clean_parts = []
        for p in parts:
            if p.startswith("verdict:"):
                clean_parts.append(p)
            elif p.startswith("Q metric:"):
                clean_parts.append("Q metric: disclosed operational indicator" if KO_RE.search(p) else p)
            elif p.startswith("P metric:"):
                clean_parts.append("P metric: disclosed pricing/ASP indicator" if KO_RE.search(p) else p)
        if clean_parts:
            out = "; ".join(clean_parts)
    return f"[Tool] Segment revenue split verdict: {out.replace(' · ', '; ')}"


# Phrase-level dynamic substitutions (NO single-syllable Korean tokens that could collide inside words!)
DYNAMIC_SUBS = [
    ("[공시]", "[Filing]"),
    ("[관측]", "[Observed]"),
    ("[계산]", "[Calculated]"),
    ("[판단]", "[Judgment]"),
    ("[회사 주장]", "[Company claim]"),
    ("[회사주장]", "[Company claim]"),
    ("[외부 추정]", "[External estimate]"),
    ("[외부평가]", "[External estimate]"),
    ("[법령]", "[Statute]"),
    ("[기본값]", "[Default]"),
    ("[미해결]", "[Unresolved]"),
    ("[도구]", "[Tool]"),
    # Sheet 17 Col D / F / H / L structured tokens
    ("결손금처리 세율수렴_예측결손이월", "NOL treatment: converge_carry_losses"),
    ("결손금처리 세율수렴", "NOL treatment: converge"),
    ("결손금처리 결손금행", "NOL treatment: explicit NOL row"),
    ("공제구분 합산", "credits: combined"),
    ("공제구분 연구개발분리", "credits: separate R&D"),
    ("세액공제이월 아니오", "credit carryforward: No"),
    ("세액공제이월 예", "credit carryforward: Yes"),
    ("경로 증가율", "Path: growth rate"),
    ("경로 수준", "Path: level"),
    ("경로 물량단가", "Path: volume x price"),
    ("경로 도착점", "Path: target market share"),
    ("경로 설비", "Path: capacity-driven"),
    ("판매량산정 직접", "volume method: direct"),
    ("판매량산정 점유율", "volume method: market share"),
    ("판매량공시 예", "volume disclosed: Yes"),
    ("판매량공시 아니오", "volume disclosed: No"),
    ("판매량꼴 유량", "volume form: flow"),
    ("판매량꼴 저량", "volume form: stock"),
    ("밑값 실적", "base: actual"),
    ("단가경로 직접", "Price path: direct"),
    ("산식 매출액비율", "Formula: % of revenue"),
    ("산식 물량단위원가", "Formula: unit cost x volume"),
    ("산식 설비계수", "Formula: % of gross PP&E"),
    ("산식 물가연동", "Formula: inflation-indexed"),
    ("산식 지표계수", "Formula: metric coefficient"),
    ("보조산식 물가연동", "secondary formula: inflation-indexed"),
    ("보조산식 없음", "secondary formula: none"),
    ("수준지수 인력", "level index: workforce"),
    ("수준지수 자체", "level index: own"),
    ("수준지수 소비자물가", "level index: CPI"),
    ("연동기준 판매량", "linked to volume"),
    ("연동기준 매출액", "linked to revenue"),
    ("산정방식 미분리", "Method: combined"),
    ("산정방식 인원", "Method: headcount x pay"),
    ("산정방식 매출액비율", "Method: % of revenue"),
    ("인원경로 증가율", "headcount path: growth rate"),
    ("인원경로 물량연동", "headcount path: volume-linked"),
    ("성과급 차감후", "bonus: post-deduction"),
    ("성과급 차감전", "bonus: pre-deduction"),
    ("성장규칙 매출자본비율", "Growth rule: sales-to-capital"),
    ("성장규칙 프로젝트", "Growth rule: explicit projects"),
    ("성장규칙 없음", "Growth rule: none"),
    ("유지규칙 상각연동", "Maintenance rule: D&A-linked"),
    ("유지규칙 매출연동", "Maintenance rule: revenue-linked"),
    ("유지규칙 매출비율", "Maintenance rule: % of revenue"),
    ("유지규칙 판매량연동", "Maintenance rule: volume-linked"),
    ("유지규칙 취득원가비율", "Maintenance rule: % of gross PP&E"),
    ("유지규칙 설비비율", "Maintenance rule: % of PP&E"),
    ("유지규칙 직접", "Maintenance rule: direct"),
    ("상각방식 상각률", "D&A method: depreciation rate"),
    ("상각방식 내용연수", "D&A method: useful life"),
    ("상각방식 빈티지", "D&A method: vintage"),
    ("영구이익기준 영구열", "Terminal earnings: terminal column"),
    ("영구이익기준 정규화", "Terminal earnings: normalized"),
    ("영구상각 추세", "terminal D&A: trend"),
    ("영구상각 유지일치", "terminal D&A: = maintenance CAPEX"),
    ("초과상각조정 아니오", "excess-D&A adj.: No"),
    ("초과상각조정 예", "excess-D&A adj.: Yes"),
    ("정상화계단 예", "normalization step: Yes"),
    ("정상화계단 아니오", "normalization step: No"),
    ("매출 구분 Q(4번 54 · 191 · 1s1)", "Revenue segment Q (4. Sales rows 54, 191, 1s1)"),
    ("인건비(7번 11 인원 · 504)", "Payroll (7. Labor row 11 headcount, 504)"),
    ("투자 자산군(8번 3g1 · 3g7 · 16)", "CAPEX asset group (8. CAPEX rows 3g1, 3g7, 16)"),
    ("매출 구분 Q(인원의 동인)", "Revenue segment Q (headcount driver)"),
    ("영업이익(성과급)", "Operating income (bonus)"),
    ("원가 줄 5 또는 A-942(가름)", "Cost line 5 or A-942 (split)"),
    ("예측 끝 열 전부", "Entire final forecast column"),
    ("가정에 한시적 현금흐름 선언이 없다(법령 경로 · 계약 시한 — D · F 가 주면 선다)",
     "No temporary cash flows declared in assumptions"),
    ("동인원천이 「해당 없음」으로 적었다", "Marked N/A by driver-source extractor"),
    ("companyfacts 에 재고자산(InventoryNet)이 없다", "No InventoryNet tag in SEC companyfacts"),
    (".경로", ".path"),
    (".단가경로", ".price_path"),
    (".산정방식", ".method"),
    (".지표", ".metric"),
    (".유지규칙", ".maintenance_rule"),
    (".성장규칙", ".growth_rule"),
    (".상각방식", ".da_method"),
    (".프로젝트", ".projects"),
    ("판매량산정", "volume_method"),
    ("단가경로", "price_path"),
    ("구조.매출구분", "structure.segment"),
    ("구조.원가줄", "structure.cost_line"),
    ("구조.인건비", "structure.payroll"),
    ("구조.투자", "structure.capex"),
    ("구조.운전자본", "structure.nwc"),
    ("구조.법인세", "structure.tax"),
    ("구조.한시적현금흐름", "structure.temp_cf"),
    ("구조.영구가치", "structure.terminal"),
    ("라인[]", "lines[]"),
    (" 꼴", " form"),
    ("해당 없음", "N/A"),
    ("보정 없음", "uncalibrated"),
    ("종가 없음", "no close"),
    ("확인 불가 — 공시 항목 없음", "Unverifiable: item not disclosed"),
    ("확인 불가()", "not applicable"),
    ("확인 불가(확인 불가)", "not applicable"),
    ("확인 불가", "Unverifiable"),
    ("확인완료", "Confirmed"),
    ("도구 채움", "Auto-populated"),
    ("반영 사건 없음", "no interim events"),
    ("원문 확인", "verified against filing"),
    ("이월 다리", "roll-forward bridge"),
    ("영구기간 ROIC(2)", "Terminal ROIC (RONIC)"),
    ("영구기간 ROIC", "Terminal ROIC"),
    ("매출액 증가율", "revenue growth rate"),
    ("매출 증가율", "revenue growth rate"),
    ("판매량 증가율", "volume growth rate"),
    ("판매단가 변동률", "unit price change rate"),
    ("판가 변동률", "unit price change rate"),
    ("매출원가율", "COGS ratio"),
    ("영업이익률", "operating margin"),
    ("연구개발비율", "R&D ratio"),
    ("매출원가", "Cost of revenue"),
    ("연구개발비", "R&D"),
    ("판매관리비", "SG&A"),
    ("일반관리비", "G&A"),
    ("매출액", "revenue"),
    # SEC & general financial terms
    ("접수)", "filed)"),
    (" 접수", " filed"),
    ("(유동)", "(current)"),
    ("(비유동)", "(non-current)"),
    ("유동 · 선순위 무담보채", "current; senior unsecured notes"),
    ("비유동 · 선순위 무담보채", "non-current; senior unsecured notes"),
    ("(감가상각 포함형)", "(incl. depreciation)"),
    ("(감가상각 제외형)", "(ex-depreciation)"),
    ("(비지배지분 없음)", "(no non-controlling interest)"),
    ("연결재무상태표", "Consolidated Balance Sheets"),
    ("재무상태표", "Balance Sheet"),
    ("연결손익계산서", "Consolidated Statements of Income"),
    ("손익계산서", "Income Statement"),
    ("연결현금흐름표", "Consolidated Statements of Cash Flows"),
    ("현금흐름표", "Cash Flow Statement"),
    ("발행 · 유통 주식수", "issued & outstanding shares"),
    ("유통주식수", "shares outstanding"),
    ("발행주식총수", "total shares issued"),
    ("자기주식수", "treasury shares"),
    ("천 주 → 주", "thousand shares to shares"),
    ("백만 주 → 주", "million shares to shares"),
    ("천 주", " thousand shares"),
    ("백만 주", " million shares"),
    ("백만달러", "USD mn"),
    ("미국 재무부", "US Treasury"),
    ("일별 수익률", "daily par yield curve"),
    ("전년 동기 대비", "YoY"),
    ("전년 대비", "YoY"),
    ("유형 감가상각", "PP&E depreciation"),
    ("무형 상각", "intangible amortization"),
    ("이자부부채 없음", "no other interest-bearing debt"),
    ("기업어음", "commercial paper"),
    ("선순위 무담보채", "senior unsecured notes"),
    ("미지급 법인세", "income taxes payable"),
    ("리스부채", "lease liabilities"),
    ("선수수익", "deferred revenue"),
    ("무형자산", "intangible assets"),
    ("유형자산", "PP&E"),
    ("회계연도", "FY"),
]


def load_bundle():
    with io.open(BUNDLE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _eok_usd_repl(m):
    raw = m.group(1).replace(",", "")
    try:
        val_b = float(raw) / 10.0
        if abs(val_b - round(val_b)) < 1e-9:
            return f"${int(round(val_b)):,}B"
        return f"${val_b:,.1f}B"
    except ValueError:
        return m.group(0)


def clean_units_and_punct(s: str) -> str:
    s = re.sub(r"([0-9,]+(?:\.[0-9]+)?)\s*억\s*달러", _eok_usd_repl, s)
    s = re.sub(r"프로젝트\s*(\d+)개?", r"projects: \1", s)
    s = re.sub(r"(\d+)개", r"\1", s)
    s = re.sub(r"(\d+)해", r"\1 yrs", s)
    s = re.sub(r"(\d+(?:\.\d+)?)년", r"\1 yrs", s)
    s = re.sub(r"([0-9,]+)\s*명\b", r"\1 employees", s)
    s = re.sub(r"([0-9,]+)\s*주\b", r"\1 shares", s)
    s = s.replace("「", '"').replace("」", '"').replace("『", '"').replace("』", '"')
    s = s.replace(" · ", "; ")
    return s


def translate_text(s: str, B: dict) -> str:
    if s in B["values"]:
        return B["values"][s]
    if s in B["units"]:
        return B["units"][s]
    if s in B["cells"]:
        return B["cells"][s]

    m = ROMAN_RE.match(s)
    if m and m.group(2) in B["section_titles"]:
        return f"{m.group(1)}. {B['section_titles'][m.group(2)]}"

    # Sheet 17 `원가줄N · <Name>` or `<NodeKey> · <Name>` compositional pattern
    m_cl = re.match(r"^원가줄(\d+)\s*[·;]\s*(.+)$", s)
    if m_cl:
        return f"Cost line {m_cl.group(1)}: {translate_text(m_cl.group(2).strip(), B)}"
    m_nk = re.match(r"^([가-힣A-Za-z.]+)\s*[·;]\s*(.+)$", s)
    if m_nk and m_nk.group(1) in NODE_KEY_MAP:
        nk_en = NODE_KEY_MAP[m_nk.group(1)]
        nm_en = translate_text(m_nk.group(2).strip(), B)
        return nk_en[:1].upper() + nk_en[1:] if nk_en.lower() == nm_en.lower() else f"{nk_en[:1].upper() + nk_en[1:]}: {nm_en}"

    # Sheet 14 cross-variable header `A × B`
    if " × " in s and KO_RE.search(s) and not s.startswith("["):
        parts = [translate_text(p.strip(), B) for p in s.split(" × ")]
        joined = " × ".join(parts)
        if not KO_RE.search(joined):
            return joined

    # Run structured multi-clause regexes BEFORE generic suffix stripping (so `[도구] ... 변동률` isn't split by ` 변동률`)
    if KO_RE.search(s):
        out = s
        for rx, rep in STRUCTURED_REGEXES:
            out = rx.sub(rep, out)
        if out != s and not KO_RE.search(out):
            return out.replace(" · ", "; ")

    for ko_suf, en_suf in B["suffix_rules"]:
        if s.endswith(ko_suf) and not s.startswith("["):
            stem = s[: -len(ko_suf)]
            if " · " in stem:
                stem_en = "; ".join(translate_text(x.strip(), B) for x in stem.split(" · "))
            else:
                stem_en = translate_text(stem, B)
            return stem_en + en_suf

    for ko_pre, en_pre in B["prefix_rules"]:
        if s.startswith(ko_pre) and not any(s.startswith(x) for x in ("실적 매출채권", "실적 재고자산", "실적 매입채무", "실적 기타순운전자본")):
            rest = s[len(ko_pre) :]
            return en_pre + translate_text(rest, B)

    if KO_RE.search(s):
        out = s
        for rx, rep in STRUCTURED_REGEXES:
            out = rx.sub(rep, out)
        if KO_RE.search(out):
            for ko_tok, en_tok in DYNAMIC_SUBS:
                if ko_tok in out:
                    out = out.replace(ko_tok, en_tok)
            out = clean_units_and_punct(out)
        else:
            out = out.replace(" · ", "; ")
        return out
    return s


def replace_sheet_refs(formula: str, sheets_map: dict) -> str:
    for ko, en in sorted(sheets_map.items(), key=lambda kv: -len(kv[0])):
        if ko != en:
            formula = formula.replace(f"'{ko}'!", f"'{en}'!")
    return formula


def translate_formula(f: str, where: str | None, B: dict, lit_map: dict) -> str:
    if where and where in B["fx_cells"]:
        patch = B["fx_cells"][where]
        if patch["찾기"] in f:
            f = f.replace(patch["찾기"], patch["바꾸기"])
    f = replace_sheet_refs(f, B["sheets"])

    def left_fix(m):
        expr, _n, op, lit = m.group(1), m.group(2), m.group(3), m.group(4)
        if KO_RE.search(lit) and lit in lit_map:
            en = lit_map[lit]
            return f'LEFT({expr},{len(en)}){op}"{en}"'
        return m.group(0)

    f = LEFT_RE.sub(left_fix, f)

    def lit_sub(m):
        s = m.group(1)
        if not KO_RE.search(s):
            return m.group(0)
        if s in lit_map:
            en = lit_map[s].replace('"', '""')
            return f'"{en}"'
        en_dyn = translate_text(s, B).replace('"', '""')
        return f'"{en_dyn}"'

    return re.sub(r'"((?:[^"]|"")*)"', lit_sub, f)


def scrub_openpyxl_props(wb):
    wb.properties.creator = "ADDER Valuation Kit"
    wb.properties.lastModifiedBy = ""
    wb.properties.company = ""
    wb.properties.manager = ""
    wb.properties.description = ""
    wb.properties.keywords = ""
    wb.properties.subject = ""
    wb.properties.category = ""


def recalc_with_excel(xlsx_path: str) -> bool:
    if os.name != "nt":
        return False
    try:
        import pythoncom
        import win32com.client
    except ImportError:
        return False

    abs_p = os.path.abspath(xlsx_path)
    pythoncom.CoInitialize()
    app = None
    try:
        app = win32com.client.DispatchEx("Excel.Application")
        app.Visible = False
        app.DisplayAlerts = False
        wb = app.Workbooks.Open(abs_p)
        try:
            wb.RemovePersonalInformation = True
        except Exception:
            pass
        for prop in ("Author", "Last Author", "Manager", "Company", "Comments", "Keywords", "Subject", "Category"):
            try:
                wb.BuiltinDocumentProperties(prop).Value = "ADDER Valuation Kit" if prop == "Author" else ""
            except Exception:
                pass
        app.CalculateFullRebuild()
        wb.Save()
        wb.Close(SaveChanges=False)
        return True
    except Exception:
        return False
    finally:
        if app is not None:
            try:
                app.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()


def convert_workbook(src_path: str, dst_path: str, recalc: bool = True) -> dict:
    B = load_bundle()
    lit_map = dict(B["values"])
    lit_map.update(B["wildcards"])
    lit_map.update(B["fx_literals"])

    wb = openpyxl.load_workbook(src_path)
    n_cells = 0
    n_formulas = 0

    for ws in wb.worksheets:
        orig_sheet = ws.title
        for row in ws.iter_rows():
            for c in row:
                v = c.value
                if not isinstance(v, str):
                    continue
                coord_key = f"{orig_sheet}!{c.coordinate}"
                if v.startswith("="):
                    nv = translate_formula(v, coord_key, B, lit_map)
                    if nv != v:
                        c.value = nv
                        n_formulas += 1
                elif coord_key in B["universal_cell_labels"]:
                    c.value = B["universal_cell_labels"][coord_key]
                    n_cells += 1
                elif KO_RE.search(v):
                    nv = translate_text(v, B)
                    if nv != v:
                        c.value = nv
                        n_cells += 1

        for cf in ws.conditional_formatting:
            for rule in cf.rules:
                if rule.formula:
                    rule.formula = [
                        translate_formula("=" + x, None, B, lit_map)[1:] if (KO_RE.search(x) or "'" in x) else x
                        for x in rule.formula
                    ]

        if ws.data_validations and ws.data_validations.dataValidation:
            for dv in ws.data_validations.dataValidation:
                for attr in ("formula1", "formula2"):
                    fval = getattr(dv, attr, None)
                    if not isinstance(fval, str):
                        continue
                    if fval.startswith('"') and fval.endswith('"'):
                        items = fval[1:-1].split(",")
                        new_items = [B["values"].get(it.strip(), translate_text(it.strip(), B)) for it in items]
                        setattr(dv, attr, '"' + ",".join(new_items) + '"')
                    elif KO_RE.search(fval) or "'" in fval:
                        prefix = "=" if fval.startswith("=") else ""
                        body = fval[1:] if prefix else fval
                        setattr(dv, attr, prefix + translate_formula("=" + body, None, B, lit_map)[1:])

    s12 = wb["12. 가정_시나리오"] if "12. 가정_시나리오" in wb.sheetnames else None
    curr = str(s12["D5"].value or "").upper() if s12 is not None else "USD"
    if curr in ("USD", "달러", "$", ""):
        fmt = B["cents_format"]["형식"]
        for spec in B["cents_format"]["범위"]:
            sh_ko, rng = spec.split("!")
            if sh_ko in wb.sheetnames:
                ws_t = wb[sh_ko]
                cells_rng = ws_t[rng]
                if isinstance(cells_rng, tuple):
                    for r_tup in cells_rng:
                        for cell in (r_tup if isinstance(r_tup, tuple) else (r_tup,)):
                            cell.number_format = fmt
                else:
                    cells_rng.number_format = fmt

    for ws in wb.worksheets:
        if ws.title in B["sheets"]:
            ws.title = B["sheets"][ws.title]

    if wb.defined_names:
        for dn in wb.defined_names.values():
            if dn.attr_text and ("'" in dn.attr_text or KO_RE.search(dn.attr_text)):
                dn.attr_text = replace_sheet_refs(dn.attr_text, B["sheets"])

    for ws in wb.worksheets:
        for hdr_attr in ("oddHeader", "oddFooter", "evenHeader", "evenFooter", "firstHeader", "firstFooter"):
            hf = getattr(ws, hdr_attr, None)
            if hf is None:
                continue
            for part in ("left", "center", "right"):
                sub = getattr(hf, part, None)
                if sub is not None and isinstance(sub.text, str) and KO_RE.search(sub.text):
                    sub.text = translate_text(sub.text, B)

    scrub_openpyxl_props(wb)
    os.makedirs(os.path.dirname(os.path.abspath(dst_path)) or ".", exist_ok=True)
    wb.save(dst_path)

    recalced = False
    if recalc:
        recalced = recalc_with_excel(dst_path)

    wb_chk = openpyxl.load_workbook(dst_path, data_only=False)
    rem_ko = 0
    for ws in wb_chk.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and KO_RE.search(c.value):
                    rem_ko += 1

    return {
        "translated_cells": n_cells,
        "translated_formulas": n_formulas,
        "excel_recalculated": recalced,
        "remaining_korean_cells": rem_ko,
        "output": os.path.abspath(dst_path),
    }


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Convert an ADDER DCF workbook into 100% American English.")
    ap.add_argument("src", help="Input .xlsx workbook")
    ap.add_argument("dst", nargs="?", default=None, help="Output .xlsx workbook (defaults to overwriting src)")
    ap.add_argument("--no-recalc", action="store_true", help="Skip Excel COM recalculation")
    args = ap.parse_args(argv)

    dst = args.dst or args.src
    info = convert_workbook(args.src, dst, recalc=not args.no_recalc)
    print(
        f"English workbook ready: {info['output']} "
        f"(cells: {info['translated_cells']}, formulas: {info['translated_formulas']}, "
        f"recalc: {info['excel_recalculated']}, remaining Korean cells: {info['remaining_korean_cells']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

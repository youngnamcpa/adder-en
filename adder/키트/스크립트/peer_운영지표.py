# -*- coding: utf-8 -*-
"""C2 CP2b 운영 지표 — 운영 동종의 원가 구조 · 재투자 · 운전자본 지표를 모아 `관측.운영동종` 조각까지 낸다.

왜 있는가 (2026-10-16 · 결정 5)
    위험이 닮은 회사(베타)와 원가 구조가 닮은 회사(마진 · 재투자)는 다를 수 있다. C1 이 회사마다
    `목적`(위험동종 · 운영동종)을 선언하고, C2 는 운영 동종만 골라 운영 지표를 잰다. 소비처는 둘이다 —
    E 비용동인이 대상회사의 계수 · 비율을 견주는 대조와 연결 검사 ㊼(운영 동종 띠). 도구가 없던 동안 C2 는
    사슬 캐시에서 손으로 모아 JSON 을 썼다(「운영 지표 — 손 집계」). 손 집계는 회차마다 정의가 갈린다.

지표 산식은 `.claude/갈래/C2_유사기업재료.md` 「운영 지표 — CP2b」 표를 따르고, 키 이름은 `가정_스키마.md`
「`_raw/peers/운영지표_{표본}.json`」 절 · 「`관측`」 절 `운영동종` 의 열하나 그대로다(2026-10-16 확정).
둘이 갈리는 자리는 하나다 — C2 표의 「매출 ÷ 유형자산」(회전율)과 달리 키 `매출대비유형자산` 은
**유형자산 ÷ 매출액**(매출 1원당 유형자산 — 자본집약도)으로 확정됐다. C2 의 회전율은 `참고지표.매출÷유형자산` 에 둔다.

읽는 것 (캐시가 먼저 — 새 조회는 관측창에 빠진 해만)
    국내  {뿌리}/_raw/peers/fs/{고유번호}_{연도}_11011_{CFS|OFS}.json   dart_fs_all.한곳 과 같은 캐시
          사업보고서 한 벌이 당기 · 전기 · 전전기 세 해를 준다. 관측창이 셋을 넘으면 세 해 앞 보고서를 하나 더 받는다
    미국  {뿌리}/_raw/peers/cf_{티커}.json                                 sec_peer_사슬(peer_차입금)과 같은 캐시
          companyfacts 의 연차(10-K · 20-F · 40-F) 기간값 · 시점값. 기준일 뒤에 낸 값은 쓰지 않는다

내는 것
    {뿌리}/_raw/peers/운영지표_{표본}.json — 회사마다 `재료`(해마다) · `연도별지표` · `지표`(최근 해 + 정상 영업이익률),
    `요약`(지표마다 범위 · 중앙값 · 해당 없음 · 확인 불가), `관측조각`(가정 `관측` 에 그대로 붙이는 `운영동종` 블록)

업종 중립 — 값 자리의 두 구분값 (`가정_스키마.md` 「공통 머리」)
    "해당 없음"  그 유형에 그 지표가 원래 없다
                 · 매출원가 줄이 없는 단일 표시(영업수익 · 영업비용) → 매출총이익률 · 판관비율 · 재고 · 매입채무 회전일수
                   (영업비용 성격별 비율을 손익계산서 본문에서 찾으면 `참고지표` 에 싣고, 없으면 `주의` 에 적는다)
                 · 재고자산이 없거나 0 → 재고자산 회전일수
                 · CAPEX 가 매출의 `--미미문턱`(기본 1%) 미만인 자산 경량 → 매출대비CAPEX · CAPEX대비상각 · 매출대비유형자산
                   (잰 값은 `참고지표` 에 남긴다 — 버리지 않는다)
    "확인 불가"  있어야 하는데 못 찾았다 → `확인불가[]` 에 어느 회사 · 어느 지표 · 왜
    선수금 · 계약부채가 있으면 매출 대비 비율(`매출대비선수금`)을 한 줄 더한다 — 회전일수로 재지 않는다(C2)

명단
    `--명단` 은 C1 의 `핵심표본.json`(핵심 · 예비 · 운영 동종 전용 · 컷통과_전체 · 탈락) 또는 목록 JSON
    ([{"종목코드" | "티커", "고유번호", "이름", "시장", "목적"}]) 이다. 회사마다 `목적` 을 읽어 「운영동종」이 있는 회사만 잰다.
    `목적` 이 아무 데도 없는 옛 표본은 핵심 · 예비(목록이면 전부)를 `목적: ["미선언"]` 으로 재고 `주의` 에 적는다.
    `B1도착` · `보강[]` 은 산출 머리에 옮겨 적는다(어느 판의 표본으로 쟀는지 — 핵심표본.json 은 고치지 않는다).

사용
    python 스크립트/peer_운영지표.py --명단 _raw/peers/핵심표본.json --기준일 2026-06-30
    python 스크립트/peer_운영지표.py --명단 운영.json --표본 운영 --기준일 2026-06-30 --창 5 --대상 005930,00126380,대상회사
    python 스크립트/peer_운영지표.py --명단 us.json --미국 --기준일 2026-06-30 --캐시만 --뿌리 D:/회차

종료 코드(종료코드.py)  0 통과 — 표본 전원의 재료를 읽었다(지표 칸의 확인 불가는 산출에 적힌다)
                         1 발견 — 재료를 한 해도 못 읽은 회사가 있다(status 부분 · 실패)
                         2 입력오류 — 명단 없음 · JSON 파손 · 운영 동종이 한 곳도 없음
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import re
import statistics
import sys
import time

여기 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, 여기)
try:
    from 종료코드 import 통과, 발견, 입력오류          # noqa: E402
except Exception:                                    # noqa: BLE001  — 시험용 복사 폴더
    통과, 발견, 입력오류 = 0, 1, 2

# 2026-10-25 FX4-P — DCF_RUN_ROOT(사슬 `--폴더` 가 넘긴다)면 그 회차에 쓴다 — 본체 경로로 돌려도 본체 _raw 에 쌓지 않게
ROOT = os.environ.get("DCF_RUN_ROOT") or os.path.dirname(여기)

# ── 지표 — 이름과 정의는 C2 갈래 문서 「운영 지표 — CP2b」 표가 정본이다 ──────────────────────
지표정의 = {
    "매출총이익률": "(매출액 − 매출원가) ÷ 매출액",
    "판관비율": "판매비와관리비 ÷ 매출액",
    "연구개발비율": "연구개발비 ÷ 매출액 — 손익계산서 본문 · 연차 태그에 없으면 확인 불가(주석 항목)",
    "매출대비CAPEX": "유형자산 취득(현금흐름표) ÷ 매출액",
    "CAPEX대비상각": "유형자산 취득 ÷ 감가상각비",
    "매출대비유형자산": "유형자산(기말) ÷ 매출액 — C2 표의 「매출 ÷ 유형자산」의 역수(참고지표에 회전율)",
    "매출채권회전일수": "매출채권(기말) ÷ 매출액 × 365",
    "재고자산회전일수": "재고자산(기말) ÷ 매출원가 × 365",
    "매입채무회전일수": "매입채무(기말) ÷ 매출원가 × 365",
    "정상영업이익률": "관측창 영업이익률의 중앙값(--정상 평균 이면 평균 — 사이클 업종은 한 사이클 창)",
    "유효세율": "법인세비용 ÷ 법인세차감전이익(이익이 0 이하인 해는 확인 불가)",
}
# 지표 열하나 밖의 참고 — 회사 `참고지표` · 산출 `요약` 의 「참고_」 칸에만 싣는다(관측조각에는 안 들어간다)
참고정의 = {"매출대비선수금": "선수금 · 계약부채(유동) ÷ 매출액 — 있을 때만(C2: 회전일수로 재지 않는다)",
          "매출÷유형자산": "매출액 ÷ 유형자산(기말) — C2 표의 회전율 꼴",
          "영업비용성격별": "단일 표시 회사의 영업비용 성격별 ÷ 영업수익(손익계산서 본문에 있을 때만)",
          "매입채무회전일수_영업비용기준": "단일 표시 회사 — 매입채무 ÷ 영업비용 × 365",
          "매입채무회전일수_미지급포함": "매입채무를 미지급비용과 한 줄로만 내는 회사 — 그 줄 ÷ 매출원가 × 365",
          "매출대비CAPEX_실측": "자산 경량으로 해당 없음 처리한 해의 실측", "CAPEX대비상각_실측": "같음",
          "매출대비유형자산_실측": "같음", "매출대비(유형+사용권)": "(유형자산 + 사용권자산) ÷ 매출액"}
재료키 = ["매출액", "매출원가", "판관비", "연구개발비", "CAPEX", "감가상각비", "유형자산",
        "매출채권", "재고자산", "매입채무", "선수금", "영업이익", "법인세차감전이익", "법인세비용"]
해당없음, 확인불가 = "해당 없음", "확인 불가"


def _수(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


# ══════════════════════════════════════ 명단 ══════════════════════════════════════
_전용키 = ("운영동종전용", "운영동종_전용", "운영 동종 전용", "운영전용")
_미국시장 = {"US", "미국", "NYSE", "NASDAQ", "AMEX", "NYSEARCA", "OTC"}
_국내시장 = {"KR", "국내", "KOSPI", "KOSDAQ", "KONEX", "유가", "유가증권", "유가증권시장", "코스피", "코스닥", "코넥스", "Y", "K", "N"}


def 목적읽기(x):
    """`목적` 칸 → 목록(띄어쓰기 없앰). 칸이 없으면 None — 「미선언」과 「선언했는데 비었음」을 가른다."""
    v = x.get("목적") if isinstance(x, dict) else None
    if v is None:
        return None
    if isinstance(v, str):
        v = re.split(r"[,·/|]", v)
    return [str(s).replace(" ", "").strip() for s in v if str(s).strip()]


def 표본펼치기(j):
    """명단 JSON → (회사 목록, 표본 메타). 핵심표본.json 이면 묶음(핵심 · 예비 · 전용 · 컷통과_전체)을 `묶음` 칸에 남긴다."""
    메타 = {}
    묶음들 = []
    if isinstance(j, list):
        묶음들 = [("명단", j)]
    elif isinstance(j, dict):
        묶음들 = [("핵심", j.get("핵심") or [])]
        for k in _전용키:
            if isinstance(j.get(k), list):
                묶음들.append(("운영동종전용", j[k]))
        묶음들 += [("예비", j.get("예비") or []), ("명단", j.get("행") or j.get("cands") or []),
                ("컷통과_전체", j.get("컷통과_전체") or [])]
        if "B1도착" in j:
            메타["B1도착"] = j.get("B1도착")
        보강 = j.get("보강")
        if isinstance(보강, list):
            메타["보강수"] = len(보강)
            if 보강:
                끝 = 보강[-1]
                메타["보강마지막"] = 끝.get("시각") if isinstance(끝, dict) else str(끝)
    out, 본 = [], set()
    for 묶음, 목록 in 묶음들:
        for x in 목록:
            if not isinstance(x, dict):
                continue
            코드 = str(x.get("종목코드") or x.get("티커") or (x.get("tickers") or [""])[0] or x.get("코드") or "").strip()
            시장 = str(x.get("시장") or "").strip().upper()
            시장 = "US" if 시장 in _미국시장 else ("KR" if 시장 in _국내시장 or 시장.title() in _국내시장 or
                                                   str(x.get("시장") or "") in _국내시장 else "")
            if not 시장:
                시장 = "KR" if (x.get("고유번호") or re.fullmatch(r"\d{6}", 코드)) else ("US" if 코드 else "")
            if 시장 == "KR" and 코드.isdigit():
                코드 = 코드.zfill(6)
            if 시장 == "US":
                코드 = 코드.upper()
            키 = (시장, 코드 or str(x.get("고유번호") or ""))
            if 키 in 본:
                continue
            본.add(키)
            out.append({"이름": x.get("회사명") or x.get("이름") or x.get("name") or 코드, "코드": 코드,
                        "고유번호": str(x.get("고유번호") or "").zfill(8) if x.get("고유번호") else "",
                        "cik": x.get("cik"), "시장": 시장, "목적": 목적읽기(x), "묶음": 묶음,
                        "핵심값": x.get("핵심") if isinstance(x.get("핵심"), bool) else None})
    return out, 메타


def 운영표본(회사들):
    """목적에 「운영동종」이 있는 회사만. 목적이 하나도 없는 옛 표본은 핵심 · 예비 · 목록 전부(미선언)."""
    선언 = any(c["목적"] is not None for c in 회사들)
    주의, 고른 = [], []
    for c in 회사들:
        c = dict(c)
        if c["목적"] is not None:
            if "운영동종" not in c["목적"]:
                continue
        elif c["묶음"] == "운영동종전용":
            c["목적"] = ["운영동종"]
        elif c["묶음"] in ("핵심", "예비", "명단"):
            c["목적"] = ["미선언"]
        else:
            continue
        c["핵심"] = c["핵심값"] if c["핵심값"] is not None else (c["묶음"] in ("핵심", "운영동종전용", "명단"))
        고른.append(c)
    if not 선언:
        주의.append("명단에 `목적` 칸이 없음(옛 표본) — 핵심 · 예비(목록이면 전부)를 운영 동종으로 보고 목적을 「미선언」으로 적음")
    elif any(c["목적"] == ["미선언"] for c in 고른):
        주의.append("`목적` 이 빠진 회사가 섞임 — 그 회사는 「미선언」으로 재었음: %s"
                  % " · ".join(c["이름"] for c in 고른 if c["목적"] == ["미선언"]))
    return 고른, 주의


# ══════════════════════════════════════ 국내 (DART) ══════════════════════════════════════
# 재료마다 (account_id 우선순위, 계정명 정규식, 재무제표 구분). 이름은 띄어쓰기를 지우고 맞춘다.
국내항목 = {
    "매출액": (["ifrs-full_Revenue"], r"^(매출액|영업수익|수익\(매출액\)|매출|매출액\(영업수익\))$", ("IS", "CIS")),
    "매출원가": (["ifrs-full_CostOfSales"], r"^(매출원가|영업원가)$", ("IS", "CIS")),
    "매출총이익": (["ifrs-full_GrossProfit"], r"^매출총이익(\(손실\))?$", ("IS", "CIS")),
    "판관비": (["dart_TotalSellingGeneralAdministrativeExpenses", "ifrs-full_SellingGeneralAndAdministrativeExpense"],
             r"^판매비(와|및)관리비$", ("IS", "CIS")),
    "영업비용": (["ifrs-full_OperatingExpense", "dart_OperatingExpenses"], r"^영업비용$", ("IS", "CIS")),
    "연구개발비": ([], r"^(경상)?연구개발비$", ("IS", "CIS")),
    "영업이익": (["dart_OperatingIncomeLoss"], r"^영업(이익|손익|손실|이익\(손실\))$", ("IS", "CIS")),
    "법인세차감전이익": (["ifrs-full_ProfitLossBeforeTax"], r"^법인세(비용)?차감전(순)?(이익|손익)(\(손실\))?$", ("IS", "CIS")),
    "법인세비용": (["ifrs-full_IncomeTaxExpenseContinuingOperations"], r"^법인세(비용|수익|비용\(수익\))$", ("IS", "CIS")),
    "CAPEX": (["ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
               "ifrs-full_PurchaseOfPropertyPlantAndEquipment"], r"^유형자산의?취득$", ("CF",)),
    "감가상각비": (["ifrs-full_AdjustmentsForDepreciationExpense"], r"^(유형자산)?감가상각비$", ("CF",)),
    "유형자산": (["ifrs-full_PropertyPlantAndEquipment"], r"^유형자산$", ("BS",)),
    "사용권자산": (["ifrs-full_RightofuseAssets"], r"^사용권자산$", ("BS",)),
    "매출채권": (["ifrs-full_CurrentTradeReceivables", "ifrs-full_TradeAndOtherCurrentReceivables"],
              r"^(유동)?매출채권(및기타(유동)?채권)?$", ("BS",)),
    "재고자산": (["ifrs-full_Inventories"], r"^(유동)?재고자산$", ("BS",)),
    "매입채무": (["ifrs-full_TradeAndOtherCurrentPayablesToTradeSuppliers", "ifrs-full_CurrentTradePayables",
               "ifrs-full_TradeAndOtherCurrentPayables"], r"^(유동)?매입채무(및기타(유동)?채무)?$", ("BS",)),
}
_비유동 = re.compile(r"(Noncurrent|NonCurrent|LongTerm)")
선수패턴 = re.compile(r"^(유동)?(선수금|선수수익|계약부채)$")
성격패턴 = {"인건비": re.compile(r"(종업원급여|인건비|^급여$|급여및)"), "지급수수료": re.compile(r"지급수수료"),
          "감가상각비": re.compile(r"(감가상각비|상각비)"), "광고선전비": re.compile(r"(광고선전비|마케팅비|판매촉진비)")}
_칸 = (("thstrm_amount", 0), ("frmtrm_amount", 1), ("bfefrmtrm_amount", 2))


def _원(s):
    try:
        return float(str(s).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def 국내뽑기(j):
    """사업보고서 응답 한 벌 → {연도: {재료: (값, 근거)}}, 성격별 {연도: {이름: 값}}, 기간 시작 연도."""
    rows = j.get("list") or []
    if not rows:
        return {}, {}, None
    y0 = int(rows[0].get("bsns_year"))
    해 = {y0 - k: {} for _, k in _칸}
    성격 = {y0 - k: {} for _, k in _칸}
    for 재료, (ids, 이름식, 구분) in 국내항목.items():
        식 = re.compile(이름식)
        후보 = []
        for i, r in enumerate(rows):
            sj = (r.get("sj_div") or "").strip()
            if sj not in 구분:
                continue
            aid = (r.get("account_id") or "").strip()
            nm = (r.get("account_nm") or "").replace(" ", "").strip()
            if _비유동.search(aid) or nm.startswith("비유동") or nm.startswith("장기"):
                continue
            if aid in ids:
                순 = (0, 구분.index(sj), ids.index(aid), i)
            elif 식.search(nm):
                순 = (1, 구분.index(sj), 0, i)
            else:
                continue
            후보.append((순, r, aid, nm))
        if not 후보:
            continue
        _, r, aid, nm = min(후보, key=lambda z: z[0])
        for 칸, k in _칸:
            v = _원(r.get(칸))
            if v is not None:
                if 재료 == "CAPEX":
                    v = abs(v)
                해[y0 - k][재료] = (v, "%s %s(%s)" % (r.get("sj_div"), r.get("account_nm"), aid or "-"))
    # 선수금 · 계약부채 — 유동의 서로 다른 줄을 더한다
    본 = set()
    for r in rows:
        nm = (r.get("account_nm") or "").replace(" ", "")
        aid = (r.get("account_id") or "")
        if (r.get("sj_div") or "") != "BS" or not 선수패턴.search(nm) or _비유동.search(aid):
            continue
        for 칸, k in _칸:
            v = _원(r.get(칸))
            if v is None or (nm, k, v) in 본:
                continue
            본.add((nm, k, v))
            옛 = 해[y0 - k].get("선수금")
            해[y0 - k]["선수금"] = ((옛[0] if 옛 else 0) + v, ((옛[1] + " + ") if 옛 else "BS ") + r.get("account_nm"))
    # 영업비용 성격별(단일 표시 회사의 손익계산서 본문에 있을 때만)
    for r in rows:
        if (r.get("sj_div") or "") not in ("IS", "CIS"):
            continue
        nm = (r.get("account_nm") or "").replace(" ", "")
        for 이름, 식 in 성격패턴.items():
            if 식.search(nm):
                for 칸, k in _칸:
                    v = _원(r.get(칸))
                    if v is not None and 이름 not in 성격[y0 - k]:
                        성격[y0 - k][이름] = v
    return 해, 성격, (r.get("rcept_no") if rows else None)


class 국내창구:
    def __init__(self, 뿌리, 캐시만):
        self.캐시 = os.path.join(뿌리, "_raw", "peers", "fs")
        self.뿌리 = 뿌리
        self.캐시만 = 캐시만
        self.센 = {"캐시": 0, "신규": 0, "실패": 0}
        self._fs = None
        self._고유 = None

    def 고유번호(self, c):
        """명단의 고유번호 — 비었으면 corpCode(회차 `_dartcache/corpCode.xml`, 없으면 키트 것 · 키가 있으면 받는다)로 푼다
        (2026-10-16, S1 리뷰: C1 표본에 고유번호가 없으면 「DART 를 부를 수 없음」으로 전부 빠졌다)."""
        if c.get("고유번호"):
            return c["고유번호"]
        종목 = str(c.get("코드") or c.get("종목코드") or "").strip()
        if not 종목.isdigit():
            return None
        if self._고유 is None:
            회차, 키트 = os.path.join(self.뿌리, "_dartcache"), os.path.join(ROOT, "_dartcache")
            캐 = next((x for x in (회차, 키트) if os.path.exists(os.path.join(x, "corpCode.xml"))), None)
            캐 = 캐 or (None if self.캐시만 else 회차)
            self._고유 = {}
            if 캐:
                try:
                    import dart_fetch                              # noqa: PLC0415
                    self._고유 = dart_fetch.고유번호풀기(None, 캐) or {}
                except Exception:                                  # noqa: BLE001
                    self._고유 = {}
        고 = self._고유.get(종목.zfill(6))
        if 고:
            c["고유번호"] = 고
        return 고

    def 한벌(self, 고유, 연도, 구분):
        p = os.path.join(self.캐시, "%s_%s_11011_%s.json" % (고유, 연도, 구분))
        if os.path.exists(p):
            try:
                self.센["캐시"] += 1
                return json.load(io.open(p, encoding="utf-8")), "캐시"
            except ValueError:
                pass
        if self.캐시만:
            return None, "캐시 없음(--캐시만)"
        key = os.environ.get("OPENDART_API_KEY")
        if not key:
            return None, "OPENDART_API_KEY 없음"
        if self._fs is None:
            import dart_fs_all as fs           # 같은 캐시 규약 — 한곳()을 그대로 쓴다
            self._fs = fs
        self._fs.CACHEDIR = self.캐시
        os.makedirs(self.캐시, exist_ok=True)
        j, how = self._fs.한곳(고유, 연도, "11011", 구분, key)
        if how == "신규":
            self.센["신규"] += 1
            time.sleep(0.6)
        elif how == "실패":
            self.센["실패"] += 1
            return None, "조회 실패 — %s" % (j or {}).get("message")
        return j, how

    def 보고서(self, 고유, 연도, 기준일8):
        """(응답, 쓴구분, 사유). CFS 가 없으면 OFS. 접수일이 기준일 뒤면 그 보고서는 기준일에 없던 것이다."""
        사유들 = []
        for 구분 in ("CFS", "OFS"):
            j, how = self.한벌(고유, 연도, 구분)
            if j is None:
                사유들.append("%s %s" % (구분, how))
                continue
            if j.get("status") != "000" or not j.get("list"):
                사유들.append("%s status %s" % (구분, j.get("status")))
                continue
            접수 = str(j["list"][0].get("rcept_no") or "")[:8]
            if 접수 and 접수 > 기준일8:
                # 2026-10-24 W17 — fnlttSinglAcntAll 은 정정본의 접수번호를 준다. 원 보고서가 기준일 앞에 들어왔으면 기준일에 있던 보고서다
                # (GS건설 조사 — 2026-07-01 기재정정 접수일로 2025 · 2024 사업보고서를 둘 다 「기준일 뒤」 로 버려 운영 지표가 비었다). 내용은 정정본
                최초 = self.최초접수(고유, 연도)
                if not (최초 and 최초 <= 기준일8):
                    return None, 구분, "%s 사업보고서 접수일 %s 이 기준일 뒤%s" % (연도, 접수, (" (최초 접수 %s)" % 최초) if 최초 else "")
                j = dict(j, _최초접수=최초)
            return j, 구분, ""
        return None, None, " · ".join(사유들)

    def 최초접수(self, 고유, 연도):
        """그 회계연도 사업보고서의 최초 접수일(정정 전) — DART 공시검색(list.json · 정기공시 A) · 캐시. → 'YYYYMMDD' 또는 None(모름)."""
        p = os.path.join(self.캐시, "%s_%s_사업보고서목록.json" % (고유, 연도))
        j = None
        if os.path.exists(p):
            try:
                j = json.load(io.open(p, encoding="utf-8"))
                self.센["캐시"] += 1
            except ValueError:
                j = None
        if j is None:
            key = os.environ.get("OPENDART_API_KEY")
            if self.캐시만 or not key:
                return None
            import urllib.parse
            import urllib.request
            url = "https://opendart.fss.or.kr/api/list.json?" + urllib.parse.urlencode(
                {"crtfc_key": key, "corp_code": 고유, "bgn_de": "%d0101" % (int(연도) + 1), "end_de": "%d1231" % (int(연도) + 2),
                 "pblntf_ty": "A", "page_count": 100})
            try:
                j = json.loads(urllib.request.urlopen(url, timeout=60).read().decode("utf-8"))
            except Exception:                                   # noqa: BLE001
                return None
            self.센["신규"] += 1
            if j.get("status") in ("000", "013"):
                os.makedirs(self.캐시, exist_ok=True)
                json.dump(j, io.open(p, "w", encoding="utf-8"), ensure_ascii=False)
        표 = "(%s." % 연도
        접수들 = [str(x.get("rcept_dt") or "") for x in (j or {}).get("list") or []
                if "사업보고서" in (x.get("report_nm") or "") and 표 in (x.get("report_nm") or "") and x.get("rcept_dt")]
        return min(접수들) if 접수들 else None

    def 회사(self, c, 기준일, 해수):
        """{연도: {재료: (값, 근거)}}, 성격, 쓴구분, 출처목록, 사유."""
        고유 = self.고유번호(c)
        if not 고유:
            return {}, {}, None, [], "고유번호 없음 — 명단에 없고 corpCode 로도 못 풀었다(DART 를 부를 수 없음)"
        기준일8 = 기준일.strftime("%Y%m%d")
        Y = 기준일.year - 1
        j, 구분, 사유 = self.보고서(고유, Y, 기준일8)
        출처 = []
        if j is None:
            j, 구분, 사유2 = self.보고서(고유, Y - 1, 기준일8)
            if j is None:
                return {}, {}, None, [], "%d 사업보고서: %s / %d 사업보고서: %s" % (Y, 사유, Y - 1, 사유2)
            Y -= 1
        해, 성격, _ = 국내뽑기(j)
        출처.append("DART fnlttSinglAcntAll %s 11011 %s (접수 %s)%s" % (Y, 구분, str(j["list"][0].get("rcept_no")),
                    (" — 정정본 내용 · 최초 접수 %s(기준일 앞)" % j["_최초접수"]) if j.get("_최초접수") else ""))
        if 해수 > 3:
            j2, 구분2, 사유3 = self.보고서(고유, Y - 3, 기준일8)
            if j2 is not None:
                해2, 성격2, _ = 국내뽑기(j2)
                for y, v in 해2.items():
                    해.setdefault(y, v)            # 겹치는 해는 최근 보고서(재작성 반영) 값을 둔다
                    성격.setdefault(y, 성격2.get(y, {}))
                출처.append("DART fnlttSinglAcntAll %s 11011 %s" % (Y - 3, 구분2))
                if 구분2 != 구분:
                    출처.append("※ 앞 보고서는 %s — 연결 · 별도가 섞임" % 구분2)
        return 해, 성격, 구분, 출처, ""


# ══════════════════════════════════════ 미국 (SEC companyfacts) ══════════════════════════════════════
연차서식 = {"10-K", "10-K/A", "10-KT", "20-F", "20-F/A", "40-F", "40-F/A"}
세율미미 = 0.01           # 2026-10-24 W17 — 세전이익 ÷ 매출이 이보다 작은 해는 유효세율을 재지 않는다
# 재료마다 태그 우선순위 — 해마다 앞에서부터 값이 있는 첫 태그(회사가 해마다 태그를 바꾼다: PP&E 실측)
미국항목 = {
    "매출액": [("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"), ("us-gaap", "Revenues"),
            ("us-gaap", "RevenueFromContractWithCustomerIncludingAssessedTax"), ("us-gaap", "SalesRevenueNet"),
            ("ifrs-full", "Revenue")],
    "매출원가": [("us-gaap", "CostOfRevenue"), ("us-gaap", "CostOfGoodsAndServicesSold"), ("us-gaap", "CostOfGoodsSold"),
             ("us-gaap", "CostOfServices"), ("ifrs-full", "CostOfSales")],
    "매출총이익": [("us-gaap", "GrossProfit"), ("ifrs-full", "GrossProfit")],
    "판관비": [("us-gaap", "SellingGeneralAndAdministrativeExpense"),
            ("ifrs-full", "SellingGeneralAndAdministrativeExpense")],
    "판매비": [("us-gaap", "SellingAndMarketingExpense"), ("us-gaap", "SellingExpense"),
            ("ifrs-full", "SellingExpense"), ("ifrs-full", "DistributionCosts")],
    "관리비": [("us-gaap", "GeneralAndAdministrativeExpense"), ("ifrs-full", "AdministrativeExpense")],
    "영업비용": [("us-gaap", "CostsAndExpenses"), ("us-gaap", "OperatingExpenses"), ("ifrs-full", "OperatingExpense")],
    "연구개발비": [("us-gaap", "ResearchAndDevelopmentExpense"),
              ("us-gaap", "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost"),
              ("us-gaap", "ResearchAndDevelopmentExpenseSoftwareExcludingAcquiredInProcessCost"),
              ("ifrs-full", "ResearchAndDevelopmentExpense")],
    "CAPEX": [("us-gaap", "PaymentsToAcquirePropertyPlantAndEquipment"), ("us-gaap", "PaymentsToAcquireProductiveAssets"),
              ("ifrs-full", "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities")],
    "감가상각비": [("us-gaap", "Depreciation"), ("us-gaap", "DepreciationDepletionAndAmortization"),
              ("us-gaap", "DepreciationAmortizationAndAccretionNet"), ("us-gaap", "DepreciationAndAmortization"),
              ("ifrs-full", "AdjustmentsForDepreciationExpense"), ("ifrs-full", "DepreciationAndAmortisationExpense")],
    "유형자산": [("us-gaap", "PropertyPlantAndEquipmentNet"),
             ("us-gaap", "PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetAfterAccumulatedDepreciationAndAmortization"),
             ("ifrs-full", "PropertyPlantAndEquipment")],
    "매출채권": [("us-gaap", "AccountsReceivableNetCurrent"), ("us-gaap", "ReceivablesNetCurrent"),
             ("ifrs-full", "CurrentTradeReceivables"), ("ifrs-full", "TradeAndOtherCurrentReceivables")],
    "재고자산": [("us-gaap", "InventoryNet"), ("us-gaap", "InventoryFinishedGoodsNetOfReserves"), ("ifrs-full", "Inventories")],
    "매입채무": [("us-gaap", "AccountsPayableCurrent"), ("us-gaap", "AccountsPayableTradeCurrent"),
             ("ifrs-full", "CurrentTradePayables"), ("ifrs-full", "TradeAndOtherCurrentPayables")],
    # 매입채무를 미지급비용과 한 태그로만 내는 회사 — 매입채무로 쓰지 않는다(회전일수가 몇 배로 부푼다). 참고지표로만
    "매입채무_미지급포함": [("us-gaap", "AccountsPayableAndAccruedLiabilitiesCurrent"),
                    ("us-gaap", "AccountsPayableAndOtherAccruedLiabilitiesCurrent")],
    "선수금": [("us-gaap", "ContractWithCustomerLiabilityCurrent"), ("us-gaap", "DeferredRevenueCurrent"),
            ("ifrs-full", "CurrentContractLiabilities")],
    "영업이익": [("us-gaap", "OperatingIncomeLoss"), ("ifrs-full", "ProfitLossFromOperatingActivities")],
    "법인세차감전이익": [("us-gaap", "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest"),
                 ("us-gaap", "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"),
                 ("ifrs-full", "ProfitLossBeforeTax")],
    "법인세비용": [("us-gaap", "IncomeTaxExpenseBenefit"), ("ifrs-full", "IncomeTaxExpenseContinuingOperations")],
}
시점재료 = {"유형자산", "매출채권", "재고자산", "매입채무", "매입채무_미지급포함", "선수금"}
# 넓은 태그를 쓰면 정의가 갈린다 — 그 사실을 주의에 남긴다
넓은태그주의 = {
    "PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetAfterAccumulatedDepreciationAndAmortization":
        "유형자산에 금융리스 사용권자산이 섞인 태그",
    "DepreciationAndAmortization": "감가상각에 무형자산 상각이 섞인 태그",
    "DepreciationAmortizationAndAccretionNet": "감가상각에 무형자산 상각이 섞인 태그",
    "DepreciationDepletionAndAmortization": "감가상각에 상각 · 감모가 섞일 수 있는 태그",
    "CostsAndExpenses": "영업비용 총액 태그(매출원가 아님)",
}


def _일수(a, b):
    return (dt.date.fromisoformat(b) - dt.date.fromisoformat(a)).days


class 사실색인:
    """(tax, tag) → {end: val} — 연차 서식 · 기준일까지 낸 값 · 기간값은 330~400일만. 같은 end 는 가장 늦게 낸 값."""

    def __init__(self, cf, 기준일s, 통화=None):
        self.cf, self.기준일s = cf, 기준일s
        self.통화 = 통화 or self._통화()

    def _통화(self):
        for tax, tag in 미국항목["매출액"]:
            u = ((self.cf.get("facts", {}).get(tax) or {}).get(tag) or {}).get("units") or {}
            if "USD" in u:
                return "USD"
            for k in u:
                if len(k) == 3 and k.isupper():
                    return k
        return "USD"

    def 값들(self, tax, tag, 시점):
        arr = ((((self.cf.get("facts") or {}).get(tax) or {}).get(tag) or {}).get("units") or {}).get(self.통화) or []
        out = {}
        for x in arr:
            if x.get("form") not in 연차서식 or (x.get("filed") or "") > self.기준일s or x.get("end", "9") > self.기준일s:
                continue
            if 시점:
                if x.get("start"):
                    continue
            else:
                if not x.get("start") or not 330 <= _일수(x["start"], x["end"]) <= 400:
                    continue
            옛 = out.get(x["end"])
            if 옛 is None or (x.get("filed") or "") > 옛[1]:
                out[x["end"]] = (x["val"], x.get("filed") or "")
        return {k: v[0] for k, v in out.items()}


def 미국뽑기(cf, 기준일s, 해수):
    """{FY라벨: {재료: (값, 근거)}}, {FY라벨: 기말}, 통화, 주의."""
    색 = 사실색인(cf, 기준일s)
    넓은 = {}
    # 회계연도 기말 = 매출 연차 기간값의 끝날 — 태그마다 최댓값(같은 해에 태그가 갈린다)
    매출 = {}
    for tax, tag in 미국항목["매출액"]:
        for end, v in 색.값들(tax, tag, False).items():
            if end not in 매출 or v > 매출[end][0]:
                매출[end] = (v, "%s/%s" % (tax, tag))
    끝들 = sorted(매출)[-해수:]
    해, 기말 = {}, {}
    캐시 = {}
    for end in 끝들:
        라벨 = "FY%s" % end[:4]
        기말[라벨] = end
        m = {"매출액": (매출[end][0], 매출[end][1])}
        for 재료, 태그들 in 미국항목.items():
            if 재료 == "매출액":
                continue
            시점 = 재료 in 시점재료
            for tax, tag in 태그들:
                k = (tax, tag, 시점)
                if k not in 캐시:
                    캐시[k] = 색.값들(tax, tag, 시점)
                v = 캐시[k].get(end)
                if v is not None:
                    m[재료] = (abs(v) if 재료 == "CAPEX" else v, "%s/%s" % (tax, tag))
                    if tag in 넓은태그주의:
                        넓은.setdefault((재료, tag), []).append(라벨)
                    break
        해[라벨] = m
    주의 = ["%s — %s(%s · %s)" % (재료, 넓은태그주의[tag], tag, "·".join(해들)) for (재료, tag), 해들 in 넓은.items()]
    return 해, 기말, 색.통화, 주의


class 미국창구:
    def __init__(self, 뿌리, 캐시만):
        self.peer = os.path.join(뿌리, "_raw", "peers")
        self.캐시만 = 캐시만
        self.센 = {"캐시": 0, "신규": 0, "실패": 0}

    def cik(self, c):
        if c.get("cik"):
            return int(c["cik"])
        p = os.path.join(self.peer, "sub_%s.json" % c["코드"])
        if os.path.exists(p):
            try:
                return int(json.load(io.open(p, encoding="utf-8"))["cik"])
            except (ValueError, KeyError, TypeError):
                pass
        p = os.path.join(self.peer, "company_tickers.json")
        if os.path.exists(p):
            for cik, ts in json.load(io.open(p, encoding="utf-8")).items():
                if c["코드"] in [str(t).upper() for t in (ts if isinstance(ts, list) else [ts])]:
                    return int(cik)
        return None

    def cf(self, c):
        p = os.path.join(self.peer, "cf_%s.json" % c["코드"])
        if os.path.exists(p):
            try:
                self.센["캐시"] += 1
                return json.load(io.open(p, encoding="utf-8")), "캐시 cf_%s.json" % c["코드"]
            except ValueError:
                pass
        if self.캐시만:
            return None, "companyfacts 캐시 없음(--캐시만)"
        contact = os.environ.get("SEC_CONTACT_EMAIL")
        if not contact:
            return None, "SEC_CONTACT_EMAIL 없음 — companyfacts 를 받을 수 없음"
        cik = self.cik(c)
        if not cik:
            return None, "cik 없음(명단 · sub_ · company_tickers 캐시) — sec_peer_사슬 --단계 싼층 을 먼저"
        import requests
        H = {"User-Agent": "DCF-research %s" % contact, "Accept-Encoding": "gzip, deflate"}
        for i in range(3):
            try:
                r = requests.get("https://data.sec.gov/api/xbrl/companyfacts/CIK%010d.json" % cik, headers=H, timeout=300)
                if r.status_code == 200:
                    os.makedirs(self.peer, exist_ok=True)
                    io.open(p, "w", encoding="utf-8").write(r.text)
                    self.센["신규"] += 1
                    time.sleep(0.3)
                    return r.json(), "SEC companyfacts CIK%010d" % cik
            except requests.RequestException:
                pass
            time.sleep(2.0 * (i + 1))
        self.센["실패"] += 1
        return None, "companyfacts 조회 실패"


# ══════════════════════════════════════ 지표 ══════════════════════════════════════
def _비(a, b):
    return a / b if (_수(a) and _수(b) and b) else None


def 한해지표(m, 단일, 미미문턱):
    """재료 한 해 → (지표, 사유, 참고). 사유는 값이 문자열인 칸의 까닭."""
    g = {k: (v[0] if isinstance(v, tuple) else v) for k, v in m.items()}
    매출 = g.get("매출액")
    원가 = g.get("매출원가")
    지, 사유, 참고 = {}, {}, {}

    def 놓기(k, v, 없음사유=None, 구분=확인불가):
        if _수(v):
            지[k] = v
        else:
            지[k] = 구분
            사유[k] = 없음사유 or "재료 없음"
    if not _수(매출) or 매출 <= 0:
        for k in 지표정의:
            if k != "정상영업이익률":
                놓기(k, None, "매출액 없음 또는 0 이하")
        return 지, 사유, 참고
    if 단일:
        for k in ("매출총이익률", "판관비율"):
            놓기(k, None, "매출원가 줄이 없는 단일 표시(영업수익 · 영업비용)", 해당없음)
    else:
        놓기("매출총이익률", _비(매출 - 원가, 매출) if _수(원가) else None, "매출원가 없음")
        놓기("판관비율", _비(g.get("판관비"), 매출), "판매비와관리비 줄 없음")
    놓기("연구개발비율", _비(g.get("연구개발비"), 매출), "연구개발비가 손익계산서 본문 · 연차 태그에 없음 — 주석 항목")
    capex = g.get("CAPEX")
    if _수(capex) and capex / 매출 < 미미문턱:
        for k in ("매출대비CAPEX", "CAPEX대비상각", "매출대비유형자산"):
            놓기(k, None, "자산 경량 — CAPEX 가 매출의 %.2f%%(문턱 %.0f%%)" % (capex / 매출 * 100, 미미문턱 * 100), 해당없음)
        참고["매출대비CAPEX_실측"] = capex / 매출
        if _수(g.get("감가상각비")) and g["감가상각비"]:
            참고["CAPEX대비상각_실측"] = capex / g["감가상각비"]
        if _수(g.get("유형자산")):
            참고["매출대비유형자산_실측"] = g["유형자산"] / 매출
        분자 = sum(v for v in (g.get("유형자산"), g.get("사용권자산")) if _수(v))
        if 분자:
            참고["매출대비(유형+사용권)"] = 분자 / 매출
    else:
        놓기("매출대비CAPEX", _비(capex, 매출), "유형자산 취득 줄 없음")
        놓기("CAPEX대비상각", _비(capex, g.get("감가상각비")),
             "감가상각비 없음(현금흐름표에 따로 없음 — 주석)" if _수(capex) else "유형자산 취득 줄 없음")
        유형 = g.get("유형자산")
        if _수(유형) and 유형 == 0:
            놓기("매출대비유형자산", None, "유형자산 0", 해당없음)
        else:
            놓기("매출대비유형자산", _비(유형, 매출), "유형자산 없음")
            if _수(유형) and 유형:
                참고["매출÷유형자산"] = 매출 / 유형
    놓기("매출채권회전일수", (g["매출채권"] / 매출 * 365) if _수(g.get("매출채권")) else None, "매출채권 줄 없음")
    재고 = g.get("재고자산")
    if not _수(재고) or 재고 == 0:
        놓기("재고자산회전일수", None, "재고자산 없음(재고가 없는 업종)" if not 재고 else "재고자산 0", 해당없음)
    elif 단일 or not _수(원가) or not 원가:
        놓기("재고자산회전일수", None, "매출원가 없음(단일 표시) — 분모가 없다", 해당없음)
    else:
        지["재고자산회전일수"] = 재고 / 원가 * 365
    채무 = g.get("매입채무")
    if not _수(채무):
        넓 = g.get("매입채무_미지급포함")
        if _수(넓) and _수(원가) and 원가:
            참고["매입채무회전일수_미지급포함"] = 넓 / 원가 * 365
        놓기("매입채무회전일수", None, "매입채무를 미지급비용과 한 줄로만 공시 — 참고지표에 미지급 포함 값"
             if _수(넓) else "매입채무 줄 없음")
    elif 단일 or not _수(원가) or not 원가:
        놓기("매입채무회전일수", None, "매출원가 없음(단일 표시) — 분모가 없다", 해당없음)
        if _수(g.get("영업비용")) and g["영업비용"]:
            참고["매입채무회전일수_영업비용기준"] = 채무 / g["영업비용"] * 365
    else:
        지["매입채무회전일수"] = 채무 / 원가 * 365
    세전, 세 = g.get("법인세차감전이익"), g.get("법인세비용")
    if _수(세전) and 세전 <= 0:
        놓기("유효세율", None, "법인세차감전이익이 0 이하")
    elif _수(세전) and _수(매출) and 매출 and 세전 / 매출 < 세율미미:
        # 2026-10-24 W17 — 세전이익이 0 근처인 해는 세율이 흔들린다(LS ELECTRIC 조사 — 대한전선 유효세율 −145.2%)
        놓기("유효세율", None, "법인세차감전이익이 매출의 %.0f%% 미만 — 세율이 흔들린다" % (세율미미 * 100))
    else:
        놓기("유효세율", _비(세, 세전), "법인세비용 또는 세전이익 없음")
    if _수(g.get("선수금")):
        참고["매출대비선수금"] = g["선수금"] / 매출
    지["_영업이익률"] = _비(g.get("영업이익"), 매출)
    return 지, 사유, 참고


def 회사지표(해, 성격, 창, 정상방식, 미미문턱):
    """해마다 지표 → 연도별 · 최근 해 · 정상 영업이익률. 단일 표시는 해마다 판정한다."""
    라벨들 = sorted(해)
    연도별, 사유별, 참고별, 주의 = {}, {}, {}, []
    for y in 라벨들:
        m = 해[y]
        g = {k: (v[0] if isinstance(v, tuple) else v) for k, v in m.items()}
        단일 = not _수(g.get("매출원가")) and (_수(g.get("영업비용")) or not _수(g.get("매출총이익")))
        지, 사유, 참고 = 한해지표(m, 단일, 미미문턱)
        if 단일 and 성격.get(y):
            매출 = g.get("매출액")
            if _수(매출) and 매출:
                참고["영업비용성격별"] = {k: v / 매출 for k, v in 성격[y].items()}
        연도별[y], 사유별[y], 참고별[y] = 지, 사유, 참고
    if not 라벨들:
        return {}, {}, {}, {}, ["재료 없음"], [], False
    최근 = 라벨들[-1]
    창라벨 = 라벨들[-창:]
    마진 = [연도별[y]["_영업이익률"] for y in 창라벨 if _수(연도별[y].get("_영업이익률"))]
    지표 = {k: v for k, v in 연도별[최근].items() if not k.startswith("_")}
    사유 = dict(사유별[최근])
    if 마진:
        지표["정상영업이익률"] = statistics.median(마진) if 정상방식 == "중앙값" else statistics.mean(마진)
        if len(마진) < 창:
            주의.append("정상 영업이익률 — 관측창 %d해 중 %d해로 잼(%s)" % (창, len(마진), "~".join([창라벨[0], 창라벨[-1]])))
    else:
        지표["정상영업이익률"] = 확인불가
        사유["정상영업이익률"] = "관측창에 영업이익 · 매출이 함께 있는 해가 없음"
    단일최근 = 지표.get("매출총이익률") == 해당없음
    if 단일최근:
        if 참고별[최근].get("영업비용성격별"):
            주의.append("단일 표시(영업수익 · 영업비용) — 매출총이익률 · 판관비율 대신 영업비용 성격별 비율(참고지표): %s"
                      % " · ".join("%s %.1f%%" % (k, v * 100) for k, v in 참고별[최근]["영업비용성격별"].items()))
        else:
            주의.append("단일 표시(영업수익 · 영업비용) — 매출총이익률 · 판관비율은 해당 없음. 영업비용 성격별 비율은 "
                      "손익계산서 본문에 없어 주석(비용의 성격별 분류)에서 읽어야 함")
    for y in 라벨들:
        연도별[y] = {k: v for k, v in 연도별[y].items() if not k.startswith("_")} | (
            {"영업이익률": 연도별[y]["_영업이익률"]} if _수(연도별[y].get("_영업이익률")) else {})
    return 지표, 사유, 연도별, 참고별.get(최근, {}), 주의, 창라벨, 단일최근


def 재료표(해):
    """재료 칸 — 스키마의 열넷만, 그 순서로. 못 찾은 재료는 「확인 불가」(까닭은 지표사유). 근거는 `재료근거`,
    지표 판정에 쓴 덧재료(영업비용 · 매출총이익 · 사용권자산 · 매입채무_미지급포함)는 `재료보조` 에 따로 둔다."""
    재, 근, 보 = {}, {}, {}
    덧 = ["영업비용", "매출총이익", "사용권자산", "매입채무_미지급포함"]
    for y in sorted(해):
        재[y] = {k: (해[y][k][0] if k in 해[y] else 확인불가) for k in 재료키}
        근[y] = {k: 해[y][k][1] for k in 재료키 + 덧 if k in 해[y]}
        보[y] = {k: 해[y][k][0] for k in 덧 if k in 해[y]}
    return 재, 근, 보


def 국내해정리(해):
    """국내 재료의 연도 키(int) → FY 라벨. 매출이 없는 해(보고서에 없는 앞 해)는 버린다."""
    return {"FY%d" % y: v for y, v in 해.items() if v.get("매출액") is not None}


def 미국판관비(해):
    """SG&A 한 줄이 없으면 판매비 + 관리비(둘 다 있을 때만) — 더한 사실을 근거에 적는다."""
    for y, m in 해.items():
        if "판관비" not in m and "판매비" in m and "관리비" in m:
            m["판관비"] = (m["판매비"][0] + m["관리비"][0], "%s + %s" % (m["판매비"][1], m["관리비"][1]))
        m.pop("판매비", None)
        m.pop("관리비", None)
        if "매출원가" not in m and "매출총이익" in m:
            m["매출원가"] = (m["매출액"][0] - m["매출총이익"][0], "매출액 − %s" % m["매출총이익"][1])
    return 해


# ══════════════════════════════════════ 조립 ══════════════════════════════════════
def 한회사(c, 창구, 기준일, 해수, 창, 정상방식, 미미문턱):
    t0 = time.time()
    out = {"이름": c["이름"], "코드": c["코드"], "시장": c["시장"], "목적": c.get("목적") or ["미선언"],
           "핵심": bool(c.get("핵심", True)), "묶음": c.get("묶음"), "주의": []}
    if c["시장"] == "KR":
        out["고유번호"] = c.get("고유번호")
        해, 성격, 구분, 출처, 사유 = 창구["KR"].회사(c, 기준일, 해수)
        해 = 국내해정리(해)
        성격 = {"FY%d" % y: v for y, v in 성격.items()}
        해 = {y: 해[y] for y in sorted(해)[-해수:]}
        out.update({"통화": "KRW", "재무구분": {"CFS": "연결", "OFS": "별도"}.get(구분, 구분), "출처": 출처})
        if 구분 == "OFS":
            out["주의"].append("연결재무제표가 없어 별도로 잼")
    elif c["시장"] == "US":
        cf, how = 창구["US"].cf(c)
        if cf is None:
            해, 성격, 사유 = {}, {}, how
            out["출처"] = []
        else:
            해, 기말, 통화, 주의 = 미국뽑기(cf, 기준일.isoformat(), 해수)
            해 = 미국판관비(해)
            성격, 사유 = {}, ""
            out.update({"통화": 통화, "재무구분": "연결", "기말": 기말,
                        "출처": ["%s — 연차 서식(10-K · 20-F · 40-F) · 기준일 %s 까지 낸 값" % (how, 기준일.isoformat())]})
            out["주의"] += sorted(set(주의))
            if 통화 != "USD":
                out["주의"].append("표시통화 %s — 비율이라 그대로 나란히 둔다" % 통화)
    else:
        해, 성격, 사유 = {}, {}, "시장(KR · US)을 정하지 못함 — 명단에 「시장」 칸을 주십시오"
        out["출처"] = []
    if not 해:
        out.update({"status": "실패", "사유": 사유 or "재료 없음", "재료": {}, "지표": {}})
        return out
    지표, 지사유, 연도별, 참고, 주의, 창라벨, _ = 회사지표(해, 성격, 창, 정상방식, 미미문턱)
    재, 근, 보 = 재료표(해)
    out["주의"] += 주의
    if len(해) < 창:
        out["주의"].append("관측창 %d해 중 %d해만 있음" % (창, len(해)))
    out.update({"status": "완료", "관측창": "%s~%s" % (창라벨[0], 창라벨[-1]), "재료": 재, "재료근거": 근, "재료보조": 보,
                "지표": 지표, "지표사유": 지사유, "연도별지표": 연도별, "참고지표": 참고,
                "초": round(time.time() - t0, 2)})
    return out


def 요약내기(회사들, 지표들):
    요 = {}
    선 = [c["참고지표"]["매출대비선수금"] for c in 회사들
         if c.get("status") == "완료" and _수((c.get("참고지표") or {}).get("매출대비선수금"))]
    if 선:
        요["참고_매출대비선수금"] = {"표본수": len(선), "최소": min(선), "최대": max(선), "중앙값": statistics.median(선)}
    for k in 지표들:
        값 = [(c["이름"], c["지표"].get(k), c.get("핵심")) for c in 회사들 if c.get("status") == "완료"]
        수 = [v for _, v, _ in 값 if _수(v)]
        핵수 = [v for _, v, h in 값 if _수(v) and h]
        요[k] = {"표본수": len(수), "최소": min(수) if 수 else None, "최대": max(수) if 수 else None,
                "중앙값": statistics.median(수) if 수 else None,
                "핵심중앙값": statistics.median(핵수) if 핵수 else None,
                "해당없음": [n for n, v, _ in 값 if v == 해당없음],
                "확인불가": [n for n, v, _ in 값 if v == 확인불가]}
    return 요


def 관측조각(회사들, 지표들, 대상, 기준, 출처):
    """가정 `관측.운영동종` 에 그대로 붙이는 블록 — `성숙동종` 과 같은 꼴(`값` 목록 · `핵심`)."""
    지 = {}
    for k in 지표들:
        값 = [{"이름": c["이름"], "값": c["지표"][k], "핵심": bool(c.get("핵심"))}
             for c in 회사들 if c.get("status") == "완료" and _수(c["지표"].get(k))]
        if not 값 and not (대상 and _수((대상.get("지표") or {}).get(k))):
            continue
        t = (대상 or {}).get("지표", {}).get(k) if 대상 and 대상.get("status") == "완료" else None
        지[k] = {"값": 값, "대상회사": t if t is not None else 확인불가}
    return {"운영동종": {"기준": 기준, "출처": 출처, "지표": 지}}


def 대상읽기(s, 시장=None):
    """`종목코드,고유번호,이름` 또는 `티커[,CIK][,이름]`."""
    p = [x.strip() for x in s.split(",")]
    if 시장 is None:
        시장 = "KR" if re.fullmatch(r"\d{6}", p[0]) else "US"
    if 시장 == "KR":
        return {"이름": p[2] if len(p) > 2 else p[0], "코드": p[0], "고유번호": p[1].zfill(8) if len(p) > 1 else "",
                "시장": "KR", "목적": ["대상회사"], "핵심": True, "묶음": "대상"}
    cik = p[1] if len(p) > 1 and p[1].isdigit() else None
    return {"이름": p[-1] if len(p) > 1 and not p[-1].isdigit() else p[0], "코드": p[0].upper(), "cik": cik,
            "시장": "US", "목적": ["대상회사"], "핵심": True, "묶음": "대상"}


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(allow_abbrev=False, description="C2 CP2b 운영 지표 → _raw/peers/운영지표_{표본}.json · 관측.운영동종 조각")
    ap.add_argument("--명단", required=True, help="핵심표본.json 또는 목록 JSON(절대경로 · 뿌리 기준 · _raw/peers 기준)")
    ap.add_argument("--표본", default="운영", help="산출 이름 꼬리(기본 운영 → 운영지표_운영.json)")
    ap.add_argument("--기준일", "--평가기준일", dest="기준일", required=True, help="평가기준일 T(분석일 · 시장 쪽 — 종가 · 시가총액 · 주식수 · 베타 창 끝 · 환율 · 법령 시행일) YYYY-MM-DD(또는 YYYYMMDD)")
    ap.add_argument("--창", type=int, default=6, help="관측창 해 수(기본 6 — 대상 앵커와 같은 자: 최소 여섯 해 · 한 사이클). "
                                                     "2026-10-16 S1 리뷰 — 종전 3해는 사이클 업종에서 정점이나 저점 한쪽만 담았다")
    ap.add_argument("--해수", type=int, default=None, help="재료를 모을 해 수 3~6(기본 = 창). 국내는 셋을 넘으면 보고서를 하나 더 받는다")
    ap.add_argument("--정상", default="중앙값", choices=["중앙값", "평균"], help="정상 영업이익률 — 관측창 중앙값(기본) · 한 사이클 평균")
    ap.add_argument("--미미문턱", type=float, default=0.01, help="CAPEX ÷ 매출이 이보다 작으면 자산 경량(기본 0.01)")
    ap.add_argument("--미국", action="store_true", help="명단 전원을 미국(SEC)으로 본다 — 기본은 회사마다 「시장」 칸 · 코드 꼴")
    ap.add_argument("--대상", default=None, help="대상회사 `종목코드,고유번호,이름` 또는 `티커[,CIK][,이름]` — 같은 창 · 같은 정의로 잰다")
    ap.add_argument("--대상받기", action="store_true",
                    help="대상회사 재무가 캐시에 없으면 받는다(기본은 읽기만 — 대상회사 원천은 A 갈래의 소유)")
    ap.add_argument("--캐시만", action="store_true", help="네트워크를 쓰지 않는다 — 캐시에 없으면 확인 불가")
    ap.add_argument("--뿌리", default=None, help="회차 폴더(_raw 가 있는 곳). 기본은 키트 폴더")
    a = ap.parse_args(argv)
    t0 = time.time()
    뿌리 = os.path.abspath(a.뿌리) if a.뿌리 else ROOT
    peer = os.path.join(뿌리, "_raw", "peers")
    try:
        기준일 = dt.date.fromisoformat(a.기준일 if "-" in a.기준일 else "%s-%s-%s" % (a.기준일[:4], a.기준일[4:6], a.기준일[6:8]))
    except ValueError:
        print("기준일 형식 오류: %s" % a.기준일)
        return 입력오류
    해수 = max(min(a.해수 or a.창, 6), a.창, 1)
    if not 3 <= a.창 <= 6:
        print("※ 관측창 %d해 — C2 기본은 6해(대상 앵커와 같은 자), 재료는 6해까지 모은다" % a.창)
    # S8-07 — 대상의 정상화 재료(`_raw/정상화.json` — 정상화.py)가 사이클이고 완결 블록이 창보다 길면 그 창은 한 사이클을 못 담는다(알리고 설정에 남긴다)
    사이클창경고 = None
    try:
        _정 = json.load(io.open(os.path.join(뿌리, "_raw", "정상화.json"), encoding="utf-8"))
        _길 = max([b.get("해수") or 0 for b in (_정.get("블록") or []) if b.get("완결")] or [0])
        if (_정.get("판정") or {}).get("사이클") and _길 > a.창:
            사이클창경고 = "대상의 완결 사이클 블록이 %d해 — 관측창 %d해는 한 사이클을 못 담는다(재료는 여섯 해까지 · `--정상 평균` 과 그 한계를 근거에)" % (_길, a.창)
            print("※ " + 사이클창경고)
    except (OSError, ValueError, TypeError):
        pass
    후보경로 = [a.명단, os.path.join(뿌리, a.명단), os.path.join(peer, a.명단)]
    p = next((x for x in 후보경로 if os.path.isfile(x)), None)
    if not p:
        print("명단 파일이 없습니다: %s" % a.명단)
        return 입력오류
    try:
        j = json.load(io.open(p, encoding="utf-8"))
    except ValueError as e:
        print("명단 JSON 파손: %s (%s)" % (p, e))
        return 입력오류
    회사들, 메타 = 표본펼치기(j)
    if a.미국:
        for c in 회사들:
            c["시장"], c["코드"] = "US", c["코드"].upper()
    표본, 주의 = 운영표본(회사들)
    if not 표본:
        print("운영 동종이 한 곳도 없습니다 — 명단의 `목적` 에 「운영동종」이 있는 회사가 없음(%s)" % os.path.basename(p))
        return 입력오류
    창구 = {"KR": 국내창구(뿌리, a.캐시만), "US": 미국창구(뿌리, a.캐시만)}
    print("운영 지표 — %s · %d곳 · 기준일 %s · 관측창 %d해(재료 %d해) · %s"
          % (a.표본, len(표본), 기준일, a.창, 해수, "캐시만" if a.캐시만 else "캐시 우선"))
    결과 = [한회사(c, 창구, 기준일, 해수, a.창, a.정상, a.미미문턱) for c in 표본]
    대상 = None
    if a.대상:
        d = 대상읽기(a.대상, "US" if a.미국 else None)
        대상창구 = {"KR": 국내창구(뿌리, a.캐시만 or not a.대상받기), "US": 미국창구(뿌리, a.캐시만 or not a.대상받기)}
        대상 = 한회사(d, 대상창구, 기준일, 해수, a.창, a.정상, a.미미문턱)
        if 대상["status"] != "완료" and not a.대상받기:
            대상["사유"] += " — 대상회사 재무는 A 갈래의 소유라 받지 않음(필요하면 --대상받기)"
    지표들 = list(지표정의)
    불가 = []
    for c in 결과 + ([대상] if 대상 else []):
        if c["status"] != "완료":
            불가.append({"항목": "%s · 재료 전체" % c["이름"], "원인": c["사유"]})
            continue
        for k, v in c["지표"].items():
            if v == 확인불가:
                불가.append({"항목": "%s · %s" % (c["이름"], k), "원인": c["지표사유"].get(k, "")})
    완료 = [c for c in 결과 if c["status"] == "완료"]
    창들 = sorted({c["관측창"] for c in 완료})
    시작 = min((x.split("~")[0] for x in 창들), default="")
    끝 = max((x.split("~")[1] for x in 창들), default="")
    별도 = [c["이름"] for c in 완료 if c.get("재무구분") == "별도"]
    기준 = "%s~%s · 연결%s" % (시작, 끝, (" (별도 %d곳: %s)" % (len(별도), " · ".join(별도))) if 별도 else "")
    if len(창들) > 1:
        주의.append("회사마다 관측창이 다름(회계연도 기말 · 공시 시점): %s" % " · ".join(
            "%s %s" % (c["이름"], c["관측창"]) for c in 완료))
    출처 = "_raw/peers/운영지표_%s.json" % a.표본
    status = "완료" if len(완료) == len(결과) else ("부분" if 완료 else "실패")
    if 메타.get("B1도착") is False:
        주의.append("핵심표본 B1도착=false — B1 뒤 보강 통지로 표본이 바뀔 수 있음(바뀌면 다시 돌린다)")
    산출 = {"표본": a.표본, "기준일": 기준일.isoformat(), "관측창": "%s~%s" % (시작, 끝),
          "평가기준일": 기준일.isoformat(), "조회일": dt.date.today().isoformat(),
          "유형": [], "status": status,
          "사유": "" if status == "완료" else "재료를 못 읽은 회사 %d곳" % (len(결과) - len(완료)),
          "도구판": "도구", "도구": "peer_운영지표.py",
          "예산실측": {"분": round((time.time() - t0) / 60, 2),
                    "문서": sum(x.센["신규"] for x in 창구.values()),
                    "캐시적중": sum(x.센["캐시"] for x in 창구.values()),
                    "출처종류": sorted({"DART fnlttSinglAcntAll(사업보고서)" if c["시장"] == "KR" else "SEC companyfacts"
                                    for c in 결과})},
          "명단": os.path.relpath(p, 뿌리) if p.startswith(뿌리) else p, "표본판": 메타,
          "설정": {"창": a.창, "해수": 해수, "정상": a.정상, "미미문턱": a.미미문턱, "사이클창경고": 사이클창경고},
          "지표정의": 지표정의, "참고정의": 참고정의,
          "회사": 결과, "대상회사": 대상, "요약": 요약내기(결과, 지표들),
          "관측조각": 관측조각(결과, 지표들, 대상, 기준, 출처),
          "확인불가": 불가, "주의": 주의}
    os.makedirs(peer, exist_ok=True)
    op = os.path.join(peer, "운영지표_%s.json" % a.표본)
    # 2026-10-24 W17 — 국내 · 미국 사슬이 같은 꼬리(운영)로 써 뒤에 돈 쪽이 앞 시장 회사를 경고 없이 덮었다(LS ELECTRIC 조사).
    # 있는 파일에 이번 명단에 없는 회사가 있으면 덮기 전에 알리고 옛 파일을 `_이전_운영지표_<표본>.json` 으로 둔다(이름이 `운영지표_*` 가 아니라 소비 도구가 줍지 않는다)
    if os.path.exists(op):
        try:
            옛 = json.load(io.open(op, encoding="utf-8"))
        except (OSError, ValueError):
            옛 = None
        옛코드 = {("%s" % c.get("코드")).upper() for c in (옛 or {}).get("회사") or [] if isinstance(c, dict) and c.get("코드")}
        새코드 = {("%s" % c.get("코드")).upper() for c in 결과 if c.get("코드")}
        빠질 = sorted(옛코드 - 새코드)
        if 빠질:
            보관 = os.path.join(peer, "_이전_운영지표_%s.json" % a.표본)
            json.dump(옛, io.open(보관, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            산출["덮기경보"] = "옛 운영지표_%s.json 의 %d곳(%s)이 이번 명단에 없다 — 옛 파일은 %s · 다른 시장 사슬이면 `--표본` 꼬리를 시장별로(운영_국내 · 운영_해외)" % (
                a.표본, len(빠질), ", ".join(빠질[:8]), os.path.basename(보관))
            print("※ 경보: " + 산출["덮기경보"])
    json.dump(산출, io.open(op, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # ── 화면 ──
    짧 = {"매출총이익률": "GPM", "판관비율": "판관", "연구개발비율": "R&D", "매출대비CAPEX": "CPX/매", "CAPEX대비상각": "CPX/DA",
         "매출대비유형자산": "유형/매", "매출채권회전일수": "AR일", "재고자산회전일수": "재고일", "매입채무회전일수": "AP일",
         "정상영업이익률": "정상OPM", "유효세율": "세율"}

    def 칸(k, v):
        if v == 해당없음:
            return "해당없음"
        if v == 확인불가 or v is None:
            return "확인불가"
        return ("%.0f" % v) if k.endswith("일수") else (("%.2f" % v) if k in ("CAPEX대비상각", "매출대비유형자산") else "%.1f%%" % (v * 100))
    print("%-16s %-3s %-9s " % ("회사", "시장", "창") + " ".join("%8s" % 짧[k] for k in 지표정의))
    for c in 결과 + ([대상] if 대상 else []):
        if c["status"] != "완료":
            print("%-16s %-3s *** %s" % (c["이름"][:16], c["시장"], c["사유"]))
            continue
        print("%-16s %-3s %-9s " % (c["이름"][:16], c["시장"], c["관측창"].replace("FY", "")) +
              " ".join("%8s" % 칸(k, c["지표"].get(k)) for k in 지표정의))
    for x in 주의:
        print("※ %s" % x)
    print("확인 불가 %d칸 · 캐시 %d · 신규 %d → %s" % (len(불가), 산출["예산실측"]["캐시적중"], 산출["예산실측"]["문서"], op))
    return 통과 if status == "완료" else 발견


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""sec_상세변수 — 미국 상장사 패널에 주석까지 담은 상세 변수를 더한다(companyfacts 상세 층 · 2026-10-24 PU).

왜
  지금 미국 패널(`sec_fsds_패널.py` — SEC Financial Statement Data Sets)은 **재무제표 본표만** 담는다. 그래서 유형자산 총액(취득원가) · 유효세율의 짝 ·
  순수 감가상각비처럼 주석에 있는 값이 비고, 레터 근거 표의 세율 · 내용연수 · 설비계수 칸이 「같은 집단 띠」 없이 남았다(연구/패널변수_20261024/P1 · P3).
  SEC 가 매일 다시 짓는 `companyfacts.zip`(회사마다 모든 **비차원** 사실 — 본표 · 주석 · 표지)을 한 번 받아 칸 정의대로 변수를 짓는다.

변수(모델 칸과 1:1 — 정의 글은 `목록.json` 에 같이 남는다)
  유효세율             법인세비용 ÷ 세전이익(세전이익 > 0 · −50~100% 밖 제외)                                   196 대조 · [유추](분모가 세전이익 · 실현 세율)
  유효세율_3년         3년 합 법인세비용 ÷ 3년 합 세전이익(합 > 0)                                              196 대조 · [유추]
  상각률_기초순액      감가상각비 ÷ (기초 유형자산 순액 + 당기 취득 ÷ 2) — 엔진 156 과 같은 밑                    156 · 같음(순수 감가상각비 · 취득이 있을 때)
  평균내용연수         평균 유형자산 총액(취득원가) ÷ 감가상각비                                                 80g 대조 · [유추](토지 · 건설중 포함 · 자산군 전체)
  설비계수             (매출원가 − 감가상각비) ÷ 평균 유형자산 총액                                              7k1 · [유추](원가 줄 하나가 아니라 매출원가 전체)
  매입채무회전일수     기말 매입채무 ÷ 매출원가 × 365                                                           186 · 같음(순수 매입채무 태그일 때)
  영업이익률_5년평균   5년 합 영업이익 ÷ 5년 합 매출(그 해 포함 앞 다섯 해 · 다섯 해가 다 있어야)                 213 재료 · [유추](실현 평균 대 정상 상태)
  무형상각률           무형자산상각비 ÷ (기초 무형 순액(영업권 제외) + 무형 취득 ÷ 2) — 엔진 164 와 같은 밑          164 · 같음(2026-10-24 PN)
  영업이익률_연차      영업이익 ÷ 매출(연차) — FSDS 본표가 없는 해(2009~2013)까지 companyfacts 로                   213 의 5 · 10년 뒤 재료 · [유추](2026-10-24 PN)

잇는 규칙
  ① 연차만 — 양식 10-K · 20-F · 40-F · 10-KT(정정 포함) · fp FY · 흐름은 기간 330~400일 · 시점은 기간 없음. 같은 (항목, 끝날)은 태그 차례가 앞선 것 → 나중에 낸 것.
  ② **FSDS 패널과는 기간 끝날 ±7일로 잇는다**(회계연도 표기로 이으면 1~3월 결산 회사가 한 해 어긋난다 — P3 실측 5.8%). 이은 해는 FSDS 의 회계연도(fy)를 쓴다.
     FSDS 행이 없으면 끝날의 해(1월 1~7일 끝은 전해)를 쓰고 비고에 적는다.
  ③ **본표 항목(매출 · 영업이익 · 매출원가 · CAPEX · 유형자산 순액)은 FSDS 값이 먼저**, 비면 companyfacts. 단 정의 순도가 다른 항목(감가상각비 · 매입채무)은
     순수 태그가 먼저다 — FSDS 감가상각비는 현금흐름표의 「감가상각 · 무형상각 합」인 경우가 많다(태그로 가른다).
  ④ 금액은 회사 하나에서 한 통화만(매출 사실이 가장 많이 쓴 통화) — 통화가 다른 FSDS 값과 섞지 않는다.

증분
  `이어받기` — 판(받은 날)이 183일 안이면 EDGAR 분기 색인(`full-index/{해}/QTR{n}/form.idx`)에서 판 날짜 뒤에 연차를 낸 회사만 골라
  회사별 API(`data.sec.gov/api/xbrl/companyfacts/CIK##########.json`)로 받아 `companyfacts/회사/` 에 두고, 짓기가 그 파일을 zip 안의 같은 회사보다 앞세운다.
  판이 183일을 넘으면 「통째로 다시 받기」를 알린다(`--통째` 면 받는다). SEC 초당 10건 한도 · 연락처는 환경변수 SEC_CONTACT_EMAIL(값을 찍지 않는다).

사용
  python 스크립트/sec_상세변수.py 짓기 [--zip 경로] [--패널 자리] [--다시추출]
  python 스크립트/sec_상세변수.py 받기                         # companyfacts.zip 통째(약 1.4GB · 40분 안팎)
  python 스크립트/sec_상세변수.py 이어받기 [--통째] [--최대 N]
  python 스크립트/sec_상세변수.py 상태
산출 — `<패널>/상세변수/<변수>.csv`(열: CIK · 회계연도 · 값 · 분자 · 분모 · 단위 · 기준 · 원천 · 기간끝 · 딱지 · 비고) · `<패널>/상세변수/목록.json`.
종료 코드 — 0 통과 · 2 입력오류(zip 없음 · 패널 없음). 회사 · 업종 이름은 이 도구에 없다(범용).
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime
import glob
import gzip
import hashlib
import io
import json
import math
import os
import re
import sys
import time
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 입력오류  # noqa: E402

형식 = "미국 상세변수 1"
연차양식 = {"10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A", "10-KT", "10-KT/A", "10-K405"}
판유효일 = 183
ZIP주소 = "https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip"
회사주소 = "https://data.sec.gov/api/xbrl/companyfacts/CIK%s.json"
색인주소 = "https://www.sec.gov/Archives/edgar/full-index/%d/QTR%d/form.idx"
열머리 = ["CIK", "회계연도", "값", "분자", "분모", "단위", "기준", "원천", "기간끝", "딱지", "비고"]

# 항목 → (흐름/시점, 후보 태그 차례). 순도가 다른 태그는 항목을 갈라 둔다(「_순수」 · 「_포함」 · 「_넓음」).
항목태그 = {
    "매출": ("흐름", ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "RevenueFromContractWithCustomerIncludingAssessedTax",
                    "SalesRevenueNet", "SalesRevenueGoodsNet", "Revenue"]),
    "영업이익": ("흐름", ["OperatingIncomeLoss", "ProfitLossFromOperatingActivities"]),
    "법인세비용": ("흐름", ["IncomeTaxExpenseBenefit", "IncomeTaxExpenseContinuingOperations"]),
    "세전이익": ("흐름", ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
                       "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
                       "ProfitLossBeforeTax"]),
    "매출원가": ("흐름", ["CostOfGoodsAndServicesSold", "CostOfRevenue", "CostOfGoodsSold", "CostOfSales"]),
    "감가상각_순수": ("흐름", ["Depreciation", "DepreciationExpense", "AdjustmentsForDepreciationExpense"]),
    "감가상각_포함": ("흐름", ["DepreciationDepletionAndAmortization", "DepreciationAndAmortization", "DepreciationAmortizationAndAccretionNet",
                          "DepreciationAndAmortisationExpense", "AdjustmentsForDepreciationAndAmortisationExpense"]),
    "CAPEX": ("흐름", ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets",
                     "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities"]),
    "총액_순수": ("시점", ["PropertyPlantAndEquipmentGross"]),
    "총액_리스포함": ("시점", ["PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetBeforeAccumulatedDepreciationAndAmortization"]),
    "순액_순수": ("시점", ["PropertyPlantAndEquipmentNet", "PropertyPlantAndEquipment"]),
    "순액_리스포함": ("시점", ["PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetAfterAccumulatedDepreciationAndAmortization"]),
    "매입채무_순수": ("시점", ["AccountsPayableCurrent", "AccountsPayableTradeCurrent"]),
    "매입채무_넓음": ("시점", ["AccountsPayableAndAccruedLiabilitiesCurrent", "TradeAndOtherCurrentPayables"]),
    # 무형 — 모델 13번 원천 18 · 78 · 81 행과 같은 태그(sec_원천.py) — 엔진 164 의 밑(투자.py x20 = (기초 무형 + 취득 ÷ 2) × 164) · 2026-10-24 PN
    "무형상각": ("흐름", ["AmortizationOfIntangibleAssets", "AmortisationIntangibleAssetsOtherThanGoodwill", "AmortisationExpense"]),
    "무형순액": ("시점", ["IntangibleAssetsNetExcludingGoodwill", "FiniteLivedIntangibleAssetsNet", "IntangibleAssetsOtherThanGoodwill"]),
    "무형취득": ("흐름", ["PaymentsToAcquireIntangibleAssets", "PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities"]),
}
태그항목 = {t: (항, i) for 항, (_k, 후보) in 항목태그.items() for i, t in enumerate(후보)}
# FSDS 열 → (항목 · 순도 판정)
FSDS순수감가 = {"Depreciation", "AdjustmentsForDepreciationExpense"}
FSDS순수매입 = {"AccountsPayableCurrent"}

변수정의 = {
    "유효세율": {"모델칸": "196(대조)", "딱지": "[유추]", "단위": "비율",
             "정의": "법인세비용 ÷ 세전이익(연차 · 세전이익 > 0 · −50~100% 밖 제외). 모델 196 은 법정 한계세율 — 이 변수는 같은 업종의 실현 세율 분포(대조)"},
    "유효세율_3년": {"모델칸": "196(대조)", "딱지": "[유추]", "단위": "비율",
                "정의": "그 해 포함 3년 합 법인세비용 ÷ 3년 합 세전이익(합 > 0 · 세 해 모두 있어야) — 일회성을 누그러뜨린 실현 세율"},
    "상각률_기초순액": {"모델칸": "156", "딱지": "같음", "단위": "비율",
                  "정의": "감가상각비 ÷ (기초 유형자산 순액 + 당기 유형자산 취득 ÷ 2) — 엔진 156 과 같은 밑(투자.py x13). 순수 감가상각 태그 · 취득이 있으면 같음, "
                          "무형상각을 품은 태그거나 취득이 없으면 [유추]"},
    "평균내용연수": {"모델칸": "80g(대조)", "딱지": "[유추]", "단위": "년",
                "정의": "평균 유형자산 총액(취득원가 — 기초 · 기말 평균, 기초가 없으면 기말) ÷ 감가상각비. 토지 · 건설중 자산을 품어 자산군 내용연수보다 길게 나온다"},
    "설비계수": {"모델칸": "7k1", "딱지": "[유추]", "단위": "배",
             "정의": "(매출원가 − 감가상각비) ÷ 평균 유형자산 총액(기초 · 기말). 모델 7k1 은 원가 줄 하나 ÷ 자산군 취득원가 — 이 변수는 매출원가 전체 ÷ 유형자산 전체"},
    "매입채무회전일수": {"모델칸": "186", "딱지": "같음", "단위": "일",
                  "정의": "기말 매입채무 ÷ 매출원가 × 365. 순수 매입채무 태그면 같음(모델 186 의 기준이 매출원가일 때), 미지급비용을 품은 태그면 [유추]"},
    "영업이익률_5년평균": {"모델칸": "213(재료)", "딱지": "[유추]", "단위": "비율",
                   "정의": "그 해 포함 앞 다섯 해의 영업이익 합 ÷ 매출 합(다섯 해가 다 있어야). 영구기간 영업이익률(정상 상태)의 같은 집단 재료 — 실현 평균"},
    "무형상각률": {"모델칸": "164", "딱지": "같음", "단위": "비율",
              "정의": "무형자산상각비 ÷ (기초 무형자산 순액(영업권 제외) + 당기 무형자산 취득 ÷ 2) — 엔진 164 와 같은 밑(투자.py x20) · 태그는 13번 원천 "
                      "18 · 78 · 81 행과 같다. 취득 태그가 없으면 0 으로 둔다(엔진도 81 행이 비면 0) — 비고에 적는다"},
    "영업이익률_연차": {"모델칸": "213(재료)", "딱지": "[유추]", "단위": "비율",
                  "정의": "영업이익 ÷ 매출(연차 · 매출 > 0 · −500~100% 밖 제외). 본표 항목은 FSDS 먼저, FSDS 행이 없는 해(2009~2013)는 companyfacts — "
                          "기저율 패널(2014~)보다 앞의 해까지 담아 213 의 5 · 10년 뒤 사후대조(정직 평가는 기준 해가 2k 넘게 있어야 선다)의 재료가 된다"},
}


# ══════════════════════════════════════════════════════════════════ 자리

def 공용뿌리():
    return (os.environ.get("DCF_공용캐시") or os.environ.get("DCF_SHARED_CACHE") or os.path.join(os.path.expanduser("~"), ".dcf캐시"))


def 패널자리기본():
    try:
        import 기저율 as 기                                    # noqa: PLC0415
        return 기.패널자리(기.국가설정(기.설정읽기(), "US"))
    except Exception:                                        # noqa: BLE001
        return os.path.join(공용뿌리(), "기저율", "US")


def 자리들(패널=None):
    p = 패널 or 패널자리기본()
    return {"패널": p, "cf": os.path.join(p, "companyfacts"), "회사": os.path.join(p, "companyfacts", "회사"),
            "상세": os.path.join(p, "상세변수"), "추출": os.path.join(p, "상세변수", "_추출")}


def 최신zip(cf자리):
    zs = sorted(glob.glob(os.path.join(cf자리, "companyfacts_*.zip")))
    return zs[-1] if zs else None


def zip날짜(p):
    m = re.search(r"companyfacts_(\d{8})\.zip$", p or "")
    if m:
        return datetime.date(int(m.group(1)[:4]), int(m.group(1)[4:6]), int(m.group(1)[6:]))
    return datetime.date.fromtimestamp(os.path.getmtime(p)) if p and os.path.exists(p) else None


# ══════════════════════════════════════════════════════════════════ 추출

def _날(s):
    return datetime.date(int(s[:4]), int(s[5:7]), int(s[8:10]))


def _수(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def 통화인가(u):
    return isinstance(u, str) and len(u) == 3 and u.isalpha() and u.isupper()


def 회사추출(js):
    """companyfacts 한 회사 → {"cik", "통화", "기록": {항목: {끝날: [값, 태그, accn, filed, form]}}}. 연차 · fp FY · 흐름 330~400일 · 시점은 기간 없음."""
    F = js.get("facts") or {}
    후보 = collections.defaultdict(dict)                  # 항목 → 끝날 → (차례, filed, 값, 태그, accn, form, 통화)
    통화셈 = collections.Counter()
    for ns in ("us-gaap", "ifrs-full"):
        for t, b in (F.get(ns) or {}).items():
            if t not in 태그항목:
                continue
            항, 순 = 태그항목[t]
            종류 = 항목태그[항][0]
            for unit, arr in (b.get("units") or {}).items():
                if not 통화인가(unit):
                    continue
                for f in arr:
                    if (f.get("form") or "") not in 연차양식 or f.get("fp") != "FY":
                        continue
                    end = f.get("end")
                    v = _수(f.get("val"))
                    if not end or v is None:
                        continue
                    if 종류 == "흐름":
                        st = f.get("start")
                        if not st:
                            continue
                        try:
                            n = (_날(end) - _날(st)).days
                        except ValueError:
                            continue
                        if not (330 <= n <= 400):
                            continue
                        if 항 == "매출":
                            통화셈[unit] += 1
                    elif f.get("start"):
                        continue
                    열쇠 = (unit, end)
                    cur = 후보[항].get(열쇠)
                    새 = (순, f.get("filed") or "", v, t, f.get("accn") or "", f.get("form") or "", unit)
                    if cur is None or 새[0] < cur[0] or (새[0] == cur[0] and 새[1] >= cur[1]):
                        후보[항][열쇠] = 새
    if not 통화셈:
        for 항 in 후보.values():
            for (u, _e) in 항:
                통화셈[u] += 1
    통 = 통화셈.most_common(1)[0][0] if 통화셈 else None
    기록 = {}
    for 항, d in 후보.items():
        m = {e: [x[2], x[3], x[4], x[1], x[5]] for (u, e), x in d.items() if u == 통}
        if m:
            기록[항] = m
    return {"cik": ("%s" % js.get("cik", "")).lstrip("0").zfill(10), "통화": 통, "기록": 기록}


def 추출하기(zip경로, 회사자리, 추출자리, 다시=False, 조용=False):
    """zip(+ 회사별 덮어쓰기) → 추출 캐시 경로. 캐시 이름은 zip 이름 · 크기와 회사 파일 지문으로 — 같으면 다시 훑지 않는다."""
    os.makedirs(추출자리, exist_ok=True)
    회사파일 = sorted(glob.glob(os.path.join(회사자리, "CIK*.json"))) if os.path.isdir(회사자리) else []
    zip지문 = hashlib.sha256(json.dumps([os.path.basename(zip경로) if zip경로 else None, os.path.getsize(zip경로) if zip경로 else 0]).encode()).hexdigest()[:8]
    덮지문 = hashlib.sha256(json.dumps([[os.path.basename(p), os.path.getsize(p), int(os.path.getmtime(p))] for p in 회사파일]).encode()).hexdigest()[:8]
    지문 = "%s_%s" % (zip지문, 덮지문)
    out = os.path.join(추출자리, "추출_%s.jsonl.gz" % 지문)
    if os.path.exists(out) and not 다시:
        return out, 지문
    덮 = {}
    for p in 회사파일:
        덮[os.path.basename(p)[3:13]] = p
    시 = time.time()
    n = 0
    # 같은 zip 의 앞선 추출이 있으면 그 줄을 다시 쓰고(덮어쓴 회사만 빼고) 회사 파일만 새로 추출한다 — 이어받기가 zip 전체를 다시 훑지 않게
    앞선 = None if 다시 else next((p for p in sorted(glob.glob(os.path.join(추출자리, "추출_%s_*.jsonl.gz" % zip지문)), key=os.path.getmtime, reverse=True)
                                 if os.path.abspath(p) != os.path.abspath(out)), None)
    with gzip.open(out + ".part", "wt", encoding="utf-8") as w:
        본 = set()
        if 앞선:
            with gzip.open(앞선, "rt", encoding="utf-8") as f:
                for 줄 in f:
                    cik = json.loads(줄)["cik"]
                    if cik in 덮:
                        continue
                    w.write(줄 if 줄.endswith("\n") else 줄 + "\n")
                    n += 1
            zip경로 = None
        if zip경로:
            z = zipfile.ZipFile(zip경로)
            이름들 = [x for x in z.namelist() if x.endswith(".json")]
            for k, 이름 in enumerate(이름들):
                cik = re.sub(r"\D", "", 이름)[-10:].zfill(10)
                if cik in 덮:
                    continue
                try:
                    js = json.loads(z.read(이름))
                except Exception:                            # noqa: BLE001
                    continue
                r = 회사추출(js)
                if r["기록"]:
                    w.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
                    n += 1
                본.add(cik)
                if not 조용 and k % 2000 == 0:
                    print("  추출 %d / %d (%.0f초)" % (k, len(이름들), time.time() - 시), flush=True)
        for cik, p in 덮.items():
            try:
                js = json.load(io.open(p, encoding="utf-8"))
            except Exception:                                # noqa: BLE001
                continue
            r = 회사추출(js)
            if r["기록"]:
                w.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
                n += 1
    os.replace(out + ".part", out)
    for 옛 in glob.glob(os.path.join(추출자리, "추출_*.jsonl.gz")):
        if os.path.abspath(옛) != os.path.abspath(out):
            os.remove(옛)
    if not 조용:
        print("  추출 끝 — 회사 %d · %.0f초 → %s" % (n, time.time() - 시, os.path.basename(out)), flush=True)
    return out, 지문


# ══════════════════════════════════════════════════════════════════ FSDS 패널

def FSDS읽기(패널자리):
    """주요계정_{fy}.csv → {cik: [{fy, 끝날, 통화, 값들, 태그들, 접수번호}]}."""
    낸 = collections.defaultdict(list)
    for p in sorted(glob.glob(os.path.join(패널자리, "주요계정_*.csv"))):
        m = re.search(r"주요계정_(\d{4})\.csv$", p)
        if not m:
            continue
        fy = int(m.group(1))
        for r in csv.DictReader(io.open(p, encoding="utf-8-sig")):
            cik = (r.get("고유번호") or "").zfill(10)
            e = r.get("기간종료") or ""
            if not (cik.strip("0") and len(e) == 8 and e.isdigit()):
                continue
            낸[cik].append({"fy": fy, "끝날": "%s-%s-%s" % (e[:4], e[4:6], e[6:]), "통화": r.get("표시통화") or "",
                           "매출": _수(r.get("매출액")), "영업이익": _수(r.get("영업이익")), "매출원가": _수(r.get("매출원가")),
                           "CAPEX": _수(r.get("CAPEX")), "순액": _수(r.get("유형자산")), "매입채무": _수(r.get("매입채무")),
                           "감가": _수(r.get("감가상각비")), "감가태그": r.get("감가상각비태그") or "", "매입태그": r.get("매입채무태그") or "",
                           "매출원가태그": r.get("매출원가태그") or "", "접수번호": r.get("접수번호") or ""})
    return 낸


def _끝해(d):
    return d.year - (1 if (d.month == 1 and d.day <= 7) else 0)


def 해잇기(끝날, fsds행들, 창=7):
    """companyfacts 끝날 → (회계연도, 이은 FSDS 행 | None). ±창 일 안의 FSDS 기간종료가 있으면 그 fy.
    없으면 끝날의 해(1월 1~7일 끝은 전해)에 **그 회사 FSDS 의 표기 관례**(fy − 끝날 해 — 1~3월 결산은 대개 −1)를 더한다."""
    d = _날(끝날)
    best = None
    for r in fsds행들:
        k = abs((_날(r["끝날"]) - d).days)
        if k <= 창 and (best is None or k < best[0]):
            best = (k, r)
    if best:
        return best[1]["fy"], best[1]
    차 = collections.Counter(r["fy"] - _끝해(_날(r["끝날"])) for r in fsds행들)
    return _끝해(d) + (차.most_common(1)[0][0] if 차 else 0), None


# ══════════════════════════════════════════════════════════════════ 변수 짓기

def _원(태그, 접):
    return "%s · %s" % (태그, 접) if 접 else 태그


def 회사해들(추, fsds행들):
    """한 회사 → {fy: {항목: (값, 원천, 순수여부)} , "_끝": 끝날, "_이음": bool}. FSDS 먼저(본표) · 순도 규칙(감가 · 매입채무)."""
    해 = {}
    통 = 추.get("통화")
    차 = collections.Counter(r["fy"] - _끝해(_날(r["끝날"])) for r in fsds행들)
    관례 = 차.most_common(1)[0][0] if 차 else 0
    for r in fsds행들:                                      # FSDS 행이 있는 해는 그 끝날 · fy 가 기준
        해[r["fy"]] = {"_끝": r["끝날"], "_이음": True, "_fsds": r, "_거리": {},
                      "_어긋남": (r["fy"] - _끝해(_날(r["끝날"]))) != 관례}   # SEC fy 표기가 그 회사의 다른 해와 다르다(패널 결함 표지)
    cf끝날 = sorted({e for d in 추["기록"].values() for e in d})
    for e in cf끝날:
        fy, fr = 해잇기(e, fsds행들)
        h = 해.setdefault(fy, {"_끝": e, "_이음": False, "_fsds": None, "_거리": {}})
        거리 = abs((_날(h["_끝"]) - _날(e)).days)
        if 거리 > 7:                                         # 같은 해 표기에 끝날이 크게 다른 사실(결산월 변경 · 짧은 해)은 섞지 않는다
            continue
        for 항 in 항목태그:
            x = 추["기록"].get(항, {}).get(e)
            if not x:
                continue
            if 항 not in h or 거리 < h["_거리"].get(항, 99):
                h[항] = (x[0], _원(x[1], x[2]))
                h["_거리"][항] = 거리
    # FSDS 본표 값(통화가 같을 때만) — 본표 항목은 FSDS 먼저
    for fy, h in 해.items():
        fr = h.get("_fsds")
        if not fr or (통 and fr["통화"] and fr["통화"] != 통):
            continue
        for 항, 열, 태그열 in (("매출", "매출", None), ("영업이익", "영업이익", None), ("매출원가", "매출원가", "매출원가태그"),
                           ("CAPEX", "CAPEX", None), ("순액_순수", "순액", None)):
            if fr.get(열) is not None:
                h[항] = (fr[열], _원("FSDS:%s" % (fr.get(태그열) or 열 if 태그열 else 열), fr["접수번호"]))
        if fr.get("감가") is not None:
            if fr["감가태그"] in FSDS순수감가:
                h.setdefault("감가상각_순수", (fr["감가"], _원("FSDS:%s" % fr["감가태그"], fr["접수번호"])))
            else:
                h.setdefault("감가상각_포함", (fr["감가"], _원("FSDS:%s" % (fr["감가태그"] or "감가상각비"), fr["접수번호"])))
        if fr.get("매입채무") is not None:
            if fr["매입태그"] in FSDS순수매입:
                h.setdefault("매입채무_순수", (fr["매입채무"], _원("FSDS:%s" % fr["매입태그"], fr["접수번호"])))
            else:
                h.setdefault("매입채무_넓음", (fr["매입채무"], _원("FSDS:%s" % (fr["매입태그"] or "매입채무"), fr["접수번호"])))
    return 해


def _고른(h, 순수, 넓음):
    if h.get(순수):
        return h[순수][0], h[순수][1], True
    if h.get(넓음):
        return h[넓음][0], h[넓음][1], False
    return None, None, None


def 변수짓기(cik, 해, 통화):
    """→ {변수: [행 dict]} — 열머리 꼴."""
    낸 = collections.defaultdict(list)

    def 행(변, fy, 값, 분자, 분모, 원, 딱지, 비고=""):
        낸[변].append({"CIK": cik, "회계연도": fy, "값": round(값, 6), "분자": 분자, "분모": 분모, "단위": 변수정의[변]["단위"],
                      "기준": "연결", "원천": 원, "기간끝": 해[fy]["_끝"], "딱지": 딱지,
                      "비고": "; ".join(x for x in ((("통화 %s" % 통화) if 통화 and 통화 != "USD" else ""), ("" if 해[fy]["_이음"] else "FSDS 행 없음 — 끝날의 해"),
                                                   ("FSDS 회계연도 표기가 그 회사 관례와 다름(패널 표기 그대로 이음)" if 해[fy].get("_어긋남") else ""), 비고) if x)})
    for fy in sorted(해):
        h = 해[fy]
        앞 = 해.get(fy - 1)
        if 앞 and not (330 <= (_날(h["_끝"]) - _날(앞["_끝"])).days <= 400):
            앞 = None
        # 유효세율
        t, p = h.get("법인세비용"), h.get("세전이익")
        if t and p and p[0] > 0:
            v = t[0] / p[0]
            if -0.5 <= v <= 1.0:
                행("유효세율", fy, v, t[0], p[0], "%s / %s" % (t[1], p[1]), "[유추]")
        # 유효세율 3년
        세 = [해.get(fy - j) for j in range(3)]
        if all(x and x.get("법인세비용") and x.get("세전이익") for x in 세):
            st = sum(x["법인세비용"][0] for x in 세)
            sp = sum(x["세전이익"][0] for x in 세)
            if sp > 0 and -0.5 <= st / sp <= 1.0:
                행("유효세율_3년", fy, st / sp, st, sp, "법인세비용 · 세전이익 %d~%d" % (fy - 2, fy), "[유추]")
        감, 감원, 감순 = _고른(h, "감가상각_순수", "감가상각_포함")
        # 상각률 — 엔진 156 의 밑
        if 감 and 감 > 0 and 앞:
            n0 = 앞.get("순액_순수") or 앞.get("순액_리스포함")
            if n0 and n0[0] > 0:
                cap = h.get("CAPEX")
                분모 = n0[0] + (abs(cap[0]) / 2 if cap else 0.0)
                v = 감 / 분모
                if 0 < v <= 2:
                    같음 = bool(감순 and cap and 앞.get("순액_순수"))
                    비 = [] if 같음 else [x for x in (("무형상각 포함 태그" if not 감순 else ""), ("취득 없음 — 기초 순액만" if not cap else ""),
                                                  ("리스 사용권 포함 순액" if not 앞.get("순액_순수") else "")) if x]
                    행("상각률_기초순액", fy, v, 감, 분모, "%s / 기초 %s%s" % (감원, n0[1], (" + 취득/2 %s" % cap[1]) if cap else ""),
                      "같음" if 같음 else "[유추]", " · ".join(비))
        # 평균 내용연수 · 설비계수 — 유형자산 총액
        g = h.get("총액_순수") or h.get("총액_리스포함")
        g0 = (앞.get("총액_순수") or 앞.get("총액_리스포함")) if 앞 else None
        리스 = (not h.get("총액_순수")) or (g0 is not None and not 앞.get("총액_순수"))
        if g and g[0] > 0 and 감 and 감 > 0:
            평 = (g[0] + g0[0]) / 2 if (g0 and g0[0] > 0) else g[0]
            v = 평 / 감
            if 0.5 <= v <= 100:
                행("평균내용연수", fy, v, 평, 감, "총액 %s%s / %s" % (g[1], (" · 기초 %s" % g0[1]) if g0 else "", 감원), "[유추]",
                  " · ".join(x for x in (("기초 없음 — 기말 총액" if not (g0 and g0[0] > 0) else ""), ("리스 사용권 포함 총액" if 리스 else ""),
                                         ("무형상각 포함 태그" if not 감순 else "")) if x))
        c = h.get("매출원가")
        if c and g and g0 and g[0] > 0 and g0[0] > 0 and 감 is not None:
            평 = (g[0] + g0[0]) / 2
            v = (c[0] - 감) / 평
            if 0 < v <= 50:
                행("설비계수", fy, v, c[0] - 감, 평, "(%s − %s) / 총액 평균 %s" % (c[1], 감원, g[1]), "[유추]",
                  " · ".join(x for x in (("리스 사용권 포함 총액" if 리스 else ""), ("무형상각 포함 태그" if not 감순 else "")) if x))
        # 매입채무 회전일수
        ap, ap원, ap순 = _고른(h, "매입채무_순수", "매입채무_넓음")
        if ap is not None and c and c[0] > 0:
            v = ap / c[0] * 365
            if 0 <= v <= 1000:
                행("매입채무회전일수", fy, v, ap, c[0], "%s / %s" % (ap원, c[1]), "같음" if ap순 else "[유추]", "" if ap순 else "미지급비용 · 기타채무 포함 태그")
        # 무형자산상각률 — 엔진 164 의 밑(기초 무형 순액 + 무형 취득 ÷ 2) · 2026-10-24 PN
        ma = h.get("무형상각")
        if ma and ma[0] > 0 and 앞:
            i0 = 앞.get("무형순액")
            if i0 and i0[0] > 0:
                ic = h.get("무형취득")
                분모 = i0[0] + (abs(ic[0]) / 2 if ic else 0.0)
                v = ma[0] / 분모
                if 0 < v <= 2:
                    행("무형상각률", fy, v, ma[0], 분모, "%s / 기초 %s%s" % (ma[1], i0[1], (" + 취득/2 %s" % ic[1]) if ic else ""),
                      "같음", "" if ic else "무형 취득 태그 없음 — 0 으로(엔진도 81 행이 비면 0)")
        # 영업이익률(연차 · 긴 계열) — 213 의 5 · 10년 뒤(2026-10-24 PN)
        s, o = h.get("매출"), h.get("영업이익")
        if s and o and s[0] > 0:
            v = o[0] / s[0]
            if -5 <= v <= 1:
                행("영업이익률_연차", fy, v, o[0], s[0], "%s / %s" % (o[1], s[1]), "[유추]")
        # 영업이익률 5년 평균
        다섯 = [해.get(fy - j) for j in range(5)]
        if all(x and x.get("매출") and x["매출"][0] > 0 and x.get("영업이익") for x in 다섯):
            so = sum(x["영업이익"][0] for x in 다섯)
            ss = sum(x["매출"][0] for x in 다섯)
            v = so / ss
            if -5 <= v <= 1:
                행("영업이익률_5년평균", fy, v, so, ss, "영업이익 · 매출 %d~%d" % (fy - 4, fy), "[유추]")
    return 낸


def 짓기(패널=None, zip경로=None, 다시=False, 조용=False):
    자 = 자리들(패널)
    if not os.path.isdir(자["패널"]) or not glob.glob(os.path.join(자["패널"], "주요계정_*.csv")):
        print("입력오류 — 미국 패널(주요계정_*.csv)이 없다(%s) — `sec_fsds_패널.py` 를 먼저" % 자["패널"])
        return 입력오류, None
    zp = zip경로 or 최신zip(자["cf"])
    if not zp or not os.path.exists(zp):
        if not glob.glob(os.path.join(자["회사"], "CIK*.json")):
            print("입력오류 — companyfacts.zip 이 없다(%s) — `sec_상세변수.py 받기`" % 자["cf"])
            return 입력오류, None
        zp = None
    시 = time.time()
    추출, 지문 = 추출하기(zp, 자["회사"], 자["추출"], 다시, 조용)
    fsds = FSDS읽기(자["패널"])
    모음 = collections.defaultdict(list)
    회사수 = 0
    with gzip.open(추출, "rt", encoding="utf-8") as f:
        for 줄 in f:
            추 = json.loads(줄)
            cik = 추["cik"]
            해 = 회사해들(추, fsds.get(cik, []))
            for 변, 행들 in 변수짓기(cik, 해, 추.get("통화")).items():
                모음[변].extend(행들)
            회사수 += 1
    os.makedirs(자["상세"], exist_ok=True)
    for 변 in 변수정의:
        행들 = sorted(모음.get(변, []), key=lambda r: (r["CIK"], r["회계연도"]))
        with io.open(os.path.join(자["상세"], "%s.csv" % 변) + ".part", "w", encoding="utf-8", newline="") as w:
            c = csv.DictWriter(w, fieldnames=열머리)
            c.writeheader()
            c.writerows(행들)
        os.replace(os.path.join(자["상세"], "%s.csv" % 변) + ".part", os.path.join(자["상세"], "%s.csv" % 변))
    목 = 목록짓기(자, fsds, 모음, zp, 지문)
    if not 조용:
        print("짓기 끝 — 회사 %d · %.0f초 · %s" % (회사수, time.time() - 시, " · ".join("%s %d" % (k, len(v)) for k, v in sorted(모음.items()))))
    return 통과, 목


def 분모셈(fsds, 하한=1e7):
    """회계연도마다 매출 ≥ 하한인 FSDS 회사 수(커버리지 분모)."""
    셈 = collections.Counter()
    for 행들 in fsds.values():
        for r in 행들:
            if r["매출"] and r["매출"] >= 하한:
                셈[r["fy"]] += 1
    return 셈


def 목록짓기(자, fsds, 모음, zp, 지문):
    p = os.path.join(자["상세"], "목록.json")
    try:
        옛 = json.load(io.open(p, encoding="utf-8"))
    except Exception:                                        # noqa: BLE001
        옛 = {}
    분모 = 분모셈(fsds)
    큰 = {(cik, r["fy"]) for cik, 행들 in fsds.items() for r in 행들 if r["매출"] and r["매출"] >= 1e7}
    변수 = dict(옛.get("변수") or {})
    for 변, 정 in 변수정의.items():
        행들 = 모음.get(변, [])
        해별 = collections.Counter(r["회계연도"] for r in 행들)
        큰해별 = collections.Counter(r["회계연도"] for r in 행들 if (r["CIK"], r["회계연도"]) in 큰)
        같음 = sum(1 for r in 행들 if r["딱지"] == "같음")
        변수[변] = dict(정, **{"해별회사수": {str(y): 해별[y] for y in sorted(해별)},
                         "커버리지": {str(y): round(큰해별.get(y, 0) / 분모[y], 4) for y in sorted(분모) if 분모[y] >= 100},
                         "커버리지_2010_2025": round(sum(큰해별.get(y, 0) for y in range(2010, 2026)) / max(1, sum(분모.get(y, 0) for y in range(2010, 2026))), 4),
                         "같음비중": round(같음 / len(행들), 4) if 행들 else None, "행수": len(행들),
                         "파일": "%s.csv" % 변, "도구": "sec_상세변수.py"})
    zd = zip날짜(zp) if zp else None
    회사덮 = sorted(glob.glob(os.path.join(자["회사"], "CIK*.json"))) if os.path.isdir(자["회사"]) else []
    갱 = dict(옛.get("갱신") or {})
    갱.update({"zip": os.path.basename(zp) if zp else None, "zip날짜": zd.isoformat() if zd else None,
              "회사덮어쓰기": len(회사덮), "추출지문": 지문,
              "판나이일": (datetime.date.today() - zd).days if zd else None,
              "상태": ("통째로 다시 받기(판 %d일 > %d일)" % ((datetime.date.today() - zd).days, 판유효일)) if (zd and (datetime.date.today() - zd).days > 판유효일)
                     else "유효"})
    원천asof = None
    for 행들 in 모음.values():
        for r in 행들:
            if 원천asof is None or r["기간끝"] > 원천asof:
                원천asof = r["기간끝"]
    낸 = {"형식": 형식, "판": hashlib.sha256(json.dumps({k: v.get("행수") for k, v in 변수.items()}, sort_keys=True).encode()
                                          + (지문 or "").encode()).hexdigest()[:16],
          "만든날": datetime.date.today().isoformat(), "패널": 자["패널"], "분모": {"규칙": "FSDS 주요계정 · 매출 ≥ 1,000만(그 해 · 표시통화 금액)",
                                                                       "해별": {str(y): 분모[y] for y in sorted(분모)}},
          "원천asof": {"기간끝최신": 원천asof, "companyfacts": zd.isoformat() if zd else None},
          "갱신": 갱, "열": 열머리, "변수": 변수}
    io.open(p + ".part", "w", encoding="utf-8").write(json.dumps(낸, ensure_ascii=False, indent=1))
    os.replace(p + ".part", p)
    return 낸


# ══════════════════════════════════════════════════════════════════ 받기 · 이어받기

def _헤더():
    c = os.environ.get("SEC_CONTACT_EMAIL")
    if not c:
        return None
    return {"User-Agent": "DCF-research %s" % c, "Accept-Encoding": "gzip, deflate"}


def 받기(패널=None):
    import requests                                          # noqa: PLC0415
    H = _헤더()
    if not H:
        print("입력오류 — 환경변수 SEC_CONTACT_EMAIL 이 없다")
        return 입력오류
    자 = 자리들(패널)
    os.makedirs(자["cf"], exist_ok=True)
    p = os.path.join(자["cf"], "companyfacts_%s.zip" % datetime.date.today().strftime("%Y%m%d"))
    시 = time.time()
    with requests.get(ZIP주소, headers=H, timeout=3600, stream=True) as r:
        if r.status_code != 200:
            print("받지 못했다 — HTTP %s" % r.status_code)
            return 입력오류
        with io.open(p + ".part", "wb") as w:
            for chunk in r.iter_content(1 << 20):
                w.write(chunk)
    os.replace(p + ".part", p)
    zipfile.ZipFile(p).namelist()
    for 옛 in glob.glob(os.path.join(자["cf"], "companyfacts_*.zip")):
        if os.path.abspath(옛) != os.path.abspath(p):
            os.remove(옛)
    if os.path.isdir(자["회사"]):
        for q in glob.glob(os.path.join(자["회사"], "CIK*.json")):
            os.remove(q)                                     # 통째 판이 회사별 덮어쓰기를 다 담는다
    print("받기 끝 — %s · %.1fMB · %.0f초" % (os.path.basename(p), os.path.getsize(p) / 1e6, time.time() - 시))
    return 통과


def 색인읽기(글, 이후, 양식=연차양식):
    """EDGAR form.idx 본문 → {CIK 10자리: 가장 늦은 제출일} — 이후(날짜) 뒤에 연차 양식을 낸 회사."""
    낸 = {}
    줄꼴 = re.compile(r"^(\S+(?: \S+)?)\s{2,}.*?\s{2,}(\d{1,10})\s{2,}(\d{4}-\d{2}-\d{2})\s{2,}\S+\s*$")
    for 줄 in 글.splitlines():
        m = 줄꼴.match(줄)
        if not m:
            continue
        form, cik, 날 = m.group(1).strip(), m.group(2).zfill(10), m.group(3)
        if form in 양식 and 날 > 이후:
            if 날 > 낸.get(cik, ""):
                낸[cik] = 날
    return 낸


def 분기들(시작, 끝):
    y, q = 시작.year, (시작.month - 1) // 3 + 1
    while (y, q) <= (끝.year, (끝.month - 1) // 3 + 1):
        yield y, q
        q += 1
        if q == 5:
            y, q = y + 1, 1


def 이어받기(패널=None, 통째=False, 최대=None):
    import requests                                          # noqa: PLC0415
    H = _헤더()
    if not H:
        print("입력오류 — 환경변수 SEC_CONTACT_EMAIL 이 없다")
        return 입력오류
    자 = 자리들(패널)
    zp = 최신zip(자["cf"])
    zd = zip날짜(zp) if zp else None
    if zd is None or (datetime.date.today() - zd).days > 판유효일:
        print("판이 없거나 %s일을 넘었다(%s) — 통째로 다시 받는다%s" % (판유효일, zd, "" if 통째 else " · `--통째` 를 주면 받는다"))
        if not 통째:
            return 통과
        rc = 받기(패널)
        if rc != 통과:
            return rc
        return 짓기(패널)[0]
    목p = os.path.join(자["상세"], "목록.json")
    try:
        이후 = (json.load(io.open(목p, encoding="utf-8")).get("갱신") or {}).get("이어받은날") or zd.isoformat()
    except Exception:                                        # noqa: BLE001
        이후 = zd.isoformat()
    대상 = {}
    for y, q in 분기들(_날(이후), datetime.date.today()):
        r = requests.get(색인주소 % (y, q), headers=H, timeout=120)
        time.sleep(0.15)
        if r.status_code != 200:
            continue
        for cik, 날 in 색인읽기(r.text, 이후).items():
            대상[cik] = max(날, 대상.get(cik, ""))
    목 = sorted(대상)
    if 최대:
        목 = 목[:최대]
    os.makedirs(자["회사"], exist_ok=True)
    받은 = 실패 = 0
    for cik in 목:
        try:
            r = requests.get(회사주소 % cik, headers=H, timeout=120)
            time.sleep(0.12)
            if r.status_code == 200:
                io.open(os.path.join(자["회사"], "CIK%s.json" % cik), "w", encoding="utf-8").write(r.text)
                받은 += 1
            else:
                실패 += 1
        except requests.RequestException:
            실패 += 1
    print("이어받기 — %s 뒤 연차 제출 %d곳 · 받음 %d · 실패 %d" % (이후, len(대상), 받은, 실패))
    rc, 낸 = 짓기(패널, 조용=True)
    if 낸 is not None:
        낸["갱신"]["이어받은날"] = datetime.date.today().isoformat()
        낸["갱신"]["이어받은회사"] = 받은
        io.open(목p, "w", encoding="utf-8").write(json.dumps(낸, ensure_ascii=False, indent=1))
    return rc


def 상태(패널=None):
    자 = 자리들(패널)
    p = os.path.join(자["상세"], "목록.json")
    if not os.path.exists(p):
        print("상세변수 없음 — `sec_상세변수.py 짓기`")
        return 통과
    m = json.load(io.open(p, encoding="utf-8"))
    print("미국 상세변수 — 판 %s · 만든날 %s · companyfacts %s · 갱신 %s" % (m.get("판"), m.get("만든날"), (m.get("갱신") or {}).get("zip날짜"),
                                                                       (m.get("갱신") or {}).get("상태")))
    for 변, v in (m.get("변수") or {}).items():
        print("  %-14s 행 %6s · 2010~2025 커버리지 %s · 같음 %s" % (변, v.get("행수"), v.get("커버리지_2010_2025"), v.get("같음비중")))
    return 통과


# ══════════════════════════════════════════════════════════════════ 직원 수(대상 회사 한 곳 · 10-K 본문) — 2026-10-24 PN

_직원수 = r"([0-9]{1,3}(?:,[0-9]{3})+|[0-9]{3,7}|[0-9]+(?:\.[0-9]+)?\s*million)"
_직원꼴 = re.compile(_직원수 + r"\s+(?:[A-Za-z\-]+\s+){0,5}?(?:employees|team members|associates|people|persons|workers|staff)\b", re.I)
_전체말 = re.compile(r"(?:as of|we (?:had|employed|employ)|employed|workforce|headcount|total|worldwide|globally|global)", re.I)
# 수가 낱말 뒤에 오는 꼴 — 「our employee headcount was 125,665」 · 「total workforce of approximately 50,000」
_직원뒤꼴 = re.compile(r"(?:employee headcount|headcount|total workforce|workforce|full-time employees|employees)\s+(?:[a-z]+\s+){0,3}?"
                    r"(?:was|were|of|totaled|totalled|numbered|consisted of)\s+(?:approximately\s+|about\s+|over\s+|more than\s+)?" + _직원수, re.I)


def 본문직원(htm):
    """10-K · 20-F 본문 → (직원 수 | None, 자리, 근거 글). 「Human Capital」(없으면 「employees」 낱말) 절에서 수 + 직원 낱말 꼴을 찾고,
    앞 120자에 회사 전체를 말하는 낱말(as of · we had · worldwide …)이 있는 후보 가운데 가장 큰 수 → 없으면 가장 큰 수(P3 표본 33곳 중 26곳 · 정확 92%).
    연도처럼 보이는 수(1990~2035)와 10 미만 · 500만 초과는 뺀다."""
    import html as _h                                       # noqa: PLC0415
    t = re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", " ", htm or "")))
    낮 = t.lower()
    자리들 = [m.start() for m in re.finditer(r"human capital", 낮)] or [m.start() for m in re.finditer(r"\bemployees\b", 낮)][:5]
    후 = []
    for i in 자리들:
        창 = t[i:i + 8000]
        for m in _직원꼴.finditer(창):
            g = m.group(1).lower().replace(",", "").strip()
            try:
                n = int(float(g.replace("million", "").strip()) * 1_000_000) if "million" in g else int(float(g))
            except ValueError:
                continue
            if n < 10 or n > 5_000_000 or 1990 <= n <= 2035:
                continue
            앞 = 창[max(0, m.start() - 120):m.start()]
            후.append((1 if _전체말.search(앞) else 0, n, (앞[-60:] + m.group(0))[:160]))
        for m in _직원뒤꼴.finditer(창):
            g = m.group(1).lower().replace(",", "").strip()
            try:
                n = int(float(g.replace("million", "").strip()) * 1_000_000) if "million" in g else int(float(g))
            except ValueError:
                continue
            if n < 10 or n > 5_000_000 or 1990 <= n <= 2035:
                continue
            후.append((1, n, m.group(0)[:160]))
    if not 후:
        return None, ("절 있음 · 수 없음" if 자리들 else "절 없음"), ""
    후.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return 후[0][1], ("Human Capital 절" if "human capital" in 낮 else "employees 문단"), 후[0][2]


def 직원수받기(종목, raw="_raw", 해수=6, 열기=None):
    """대상 회사 한 곳의 연차 보고서(10-K · 20-F · 40-F) 최근 `해수` 개에서 직원 수를 뽑아 `<raw>/직원수_10K.json` 에 쓴다.
    **패널이 아니다** — 미국 공시에는 직원 수가 체계적으로 없어(dei 2% · P3) 회사 한 곳의 실적 범위(인원 증가율 501 의 「회사 실적」 열)로만 쓴다.
    dei:EntityNumberOfEmployees 가 있으면 그 값을 먼저(같은 해), 없으면 본문 정규식. 종목 = 티커 또는 CIK."""
    H = _헤더()
    if not H and 열기 is None:
        return 입력오류, "환경변수 SEC_CONTACT_EMAIL 이 없다"
    import urllib.request as _u                              # noqa: PLC0415

    def 받(u):
        if 열기:
            return 열기(u)
        time.sleep(0.15)
        r = _u.urlopen(_u.Request(u, headers={"User-Agent": H["User-Agent"]}), timeout=60).read()
        return gzip.decompress(r) if r[:2] == b"\x1f\x8b" else r
    cik = 종목 if re.fullmatch(r"\d{1,10}", 종목 or "") else None
    if not cik:
        tm = json.loads(받("https://www.sec.gov/files/company_tickers.json"))
        cik = next(("%d" % v["cik_str"] for v in tm.values() if (v.get("ticker") or "").upper() == 종목.upper()), None)
        if not cik:
            return 입력오류, "티커 %s 를 SEC 명부에서 못 찾음" % 종목
    cik10 = cik.zfill(10)
    sub = json.loads(받("https://data.sec.gov/submissions/CIK%s.json" % cik10))
    r = (sub.get("filings") or {}).get("recent") or {}
    연 = [i for i, f in enumerate(r.get("form") or []) if f in ("10-K", "20-F", "40-F", "10-K405")][:해수]
    dei = {}
    try:
        cf = json.loads(받("https://data.sec.gov/api/xbrl/companyfacts/CIK%s.json" % cik10))
        for u in (((cf.get("facts") or {}).get("dei") or {}).get("EntityNumberOfEmployees") or {}).get("units", {}).values():
            for x in u:
                if x.get("form") in ("10-K", "20-F", "40-F") and x.get("val"):
                    dei[x.get("accn")] = int(x["val"])
    except Exception:                                        # noqa: BLE001
        pass
    행들 = []
    for i in 연:
        accn, 끝 = r["accessionNumber"][i], r.get("reportDate", [""] * (i + 1))[i]
        n, 자리, 글 = None, "", ""
        if accn in dei:
            n, 자리 = dei[accn], "dei:EntityNumberOfEmployees"
        else:
            try:
                u = "https://www.sec.gov/Archives/edgar/data/%d/%s/%s" % (int(cik), accn.replace("-", ""), r["primaryDocument"][i])
                n, 자리, 글 = 본문직원(받(u).decode("utf-8", errors="replace"))
            except Exception as e:                           # noqa: BLE001
                자리 = "원문 못 받음(%s)" % type(e).__name__
        행들.append({"기간끝": 끝, "양식": r["form"][i], "접수번호": accn, "직원수": n, "자리": 자리, "글": 글})
    행들.sort(key=lambda x: x["기간끝"])
    증 = []
    for a_, b_ in zip(행들, 행들[1:]):
        if a_["직원수"] and b_["직원수"]:
            증.append({"기간끝": b_["기간끝"], "값": round(b_["직원수"] / a_["직원수"] - 1.0, 6)})
    값들 = [x["값"] for x in 증]
    낸 = {"형식": "직원수 10-K 1", "cik": cik10, "종목": 종목, "만든날": datetime.date.today().isoformat(), "행": 행들, "증가율": 증,
          "실적범위": [min(값들), max(값들)] if 값들 else None,
          "뜻": "회사 한 곳의 연차 보고서 직원 수(dei 가 있으면 dei · 없으면 본문 정규식 — P3 표본 정확 92%) · 인원 증가율(501)의 회사 실적 범위 — 같은 집단 띠가 아니다"}
    os.makedirs(raw, exist_ok=True)
    p = os.path.join(raw, "직원수_10K.json")
    io.open(p, "w", encoding="utf-8").write(json.dumps(낸, ensure_ascii=False, indent=1))
    return 통과, p


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="미국 상세변수 — companyfacts 상세 층(세율 · 상각률 · 내용연수 · 설비계수 · 매입채무 · 영업이익률 5년 · 무형상각률) · 직원 수(회사 한 곳)")
    ap.add_argument("명령", choices=["짓기", "받기", "이어받기", "상태", "직원수"])
    ap.add_argument("--패널")
    ap.add_argument("--zip")
    ap.add_argument("--다시추출", action="store_true")
    ap.add_argument("--통째", action="store_true")
    ap.add_argument("--최대", type=int)
    ap.add_argument("--종목", help="직원수 — 티커 또는 CIK")
    ap.add_argument("--raw", default="_raw", help="직원수 — 회차 _raw 폴더")
    ap.add_argument("--해수", type=int, default=6)
    a = ap.parse_args(argv)
    if a.명령 == "직원수":
        rc, 말 = 직원수받기(a.종목, a.raw, a.해수)
        print(("직원수 → %s" if rc == 통과 else "입력오류 — %s") % 말)
        return rc
    if a.명령 == "짓기":
        return 짓기(a.패널, a.zip, a.다시추출)[0]
    if a.명령 == "받기":
        return 받기(a.패널)
    if a.명령 == "이어받기":
        return 이어받기(a.패널, a.통째, a.최대)
    return 상태(a.패널)


if __name__ == "__main__":
    sys.exit(main())

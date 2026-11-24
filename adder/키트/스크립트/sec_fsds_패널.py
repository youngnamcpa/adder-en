# -*- coding: utf-8 -*-
"""SEC FSDS 패널 — 미국 전 제출인의 연간 주요계정 패널을 짓는다(기저율 · 조합이례도의 미국 비교 집단 · 2026-10-22 신설).

무엇을 하나
  SEC 가 분기마다 공표하는 Financial Statement Data Sets(FSDS — 전 제출인 본표 수치의 평탄 파일)를 받아,
  연차 보고서(10-K · 10-KT · 20-F · 40-F · 그 정정본)의 **당해 연도 · 연결 실체 · 비차원** 값만 골라
  회사-회계연도 패널을 낸다. 국내 패널(`dart_peer_screen.py` → `주요계정_{연도}.csv`)과 **같은 열 이름**이라
  `기저율.py` · `조합이례도.py` 가 국가 축 하나로 두 패널을 같은 코드로 읽는다.

    ZIP   https://www.sec.gov/files/dera/data/financial-statement-data-sets/{yyyy}q{n}.zip   (2009q1 ~ · 분기 · 55~125MB)
    sub.txt  제출건(adsh) · cik · name · sic · countryba · afs · fye · form · period · fy · fp · filed
    num.txt  adsh · tag · version · ddate · qtrs · uom · segments · coreg · value   (한 분기 390만 행 안팎)

고르는 규칙 — 전부 「as filed」, 고치지 않는다
  ① form ∈ {10-K, 10-K/A, 10-KT, 10-KT/A, 20-F, 20-F/A, 40-F, 40-F/A} · fp = FY
  ② segments 빈 행(비차원 — 부문 · 멤버가 붙은 값은 뺀다) · coreg 빈 행(연결 실체)
  ③ ddate = 그 제출건의 period(같은 제출건 안의 전기 비교치는 뺀다) · 흐름 값은 qtrs = 4 · 시점 값(자산총계)은 qtrs = 0
  ④ 태그는 회사마다 갈린다 — 항목마다 후보 태그를 차례로 두드리고 **쓴 태그를 열에 남긴다**(`매출태그` · `CAPEX태그`).
     us-gaap 뒤에 ifrs-full(20-F) 후보를 둔다. 2018 ASC 606 전후 매출 태그 변형이 여기서 걸린다
  ⑤ 같은 (cik, fy) 가 여러 제출건에 있으면(정정본 · 재제출) **칸마다 filed 가 가장 늦은 값** — 정정본이 다시 적은 칸은 정정본,
     적지 않은 칸은 원본 값이 남는다(10-K/A 가 손익만 다시 내면 CAPEX 는 원본에서). 접수번호 · 양식 · 제출일은 가장 늦은 제출건의 것
  ⑥ 통화는 uom 열 그대로 둔다(USD 가 아닌 20-F 는 `자료제외` 의 표시통화 규칙이 사유와 함께 뺀다)

한 번 판 ZIP 은 다시 풀지 않는다 — 분기마다 `fsds/추출_{yyyy}q{n}.csv`(수천 행)로 줄여 두고, 합치기는 그 추출본만 다시 읽는다.
새 분기가 나오면 그 ZIP 하나만 받아 풀고 전 연도 CSV 를 다시 합친다(수 초).

사용
  python 스크립트/sec_fsds_패널.py --받기 [--부터 2015] [--까지 YYYY] [--분기 1,2,3,4]   # 없는 ZIP 만 받고 → 풀고 → 합친다
  python 스크립트/sec_fsds_패널.py --오프라인                                           # 받지 않고 있는 ZIP 만 풀고 합친다
  python 스크립트/sec_fsds_패널.py --자리 <폴더>                                         # 기본 자리: 기저율설정.json 국가별.US.패널하위

읽는 것 — 환경변수 SEC_CONTACT_EMAIL(User-Agent 연락처 — 받을 때만 · 화면에 찍지 않는다) · `기저율설정.json`(국가별 · 패널 하위 · 부터)
내는 것 — `{자리}/주요계정_{fy}.csv`(고유번호 = CIK 10자리 · 회사명 · 종목코드 · 표시통화 · 재무제표구분 · 매출액 · 영업이익 · 당기순이익 ·
           자산총계 · 영업현금흐름 · CAPEX · 매출태그 · CAPEX태그 · 양식 · 기간종료 · 제출일 · 접수번호 · 결산월 · 소재국) ·
           `{자리}/산업분류.csv`(고유번호 · 회사명 · 종목코드 · 상장구분(afs) · 산업분류코드(SIC 4자리) · 소재국) · `{자리}/fsds_처리기록.json`
종료 코드 — 0 통과 · 2 입력오류(받아야 하는데 SEC_CONTACT_EMAIL 없음 · 풀 ZIP 이 하나도 없음 · ZIP 깨짐).
회사 · 업종 이름은 이 도구에 없다(범용). 10-K 가 몰리는 1 · 2분기 ZIP 만 받아도 12월 결산 회사는 대부분 덮인다 — 다른 결산월은 나머지 분기에 있다.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import glob
import io
import json
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

ZIP주소 = "https://www.sec.gov/files/dera/data/financial-statement-data-sets/%s.zip"
양식 = {"10-K", "10-K/A", "10-KT", "10-KT/A", "20-F", "20-F/A", "40-F", "40-F/A"}

# 항목 → (후보 태그 차례, 흐름(qtrs 4) 또는 시점(qtrs 0))
항목태그 = {
    "매출액": (["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
             "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet", "SalesRevenueGoodsNet",
             "SalesRevenueServicesNet", "Revenue", "RevenueFromContractsWithCustomers"], 4),
    "영업이익": (["OperatingIncomeLoss", "ProfitLossFromOperatingActivities"], 4),
    "당기순이익": (["NetIncomeLoss", "ProfitLoss", "NetIncomeLossAvailableToCommonStockholdersBasic"], 4),
    "자산총계": (["Assets"], 0),
    "영업현금흐름": (["NetCashProvidedByUsedInOperatingActivities",
                "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
                "CashFlowsFromUsedInOperatingActivities"], 4),
    "CAPEX": (["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets",
              "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities"], 4),
    # 상세 계정(2026-10-22 — 회전일수 · 상각률 · CAPEX 비율의 기저율 · 지속성 자. 국내 상세 패널(dart_일괄패널.py)과 같은 열 이름)
    "매출원가": (["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold", "CostOfSales"], 4),
    "유형자산": (["PropertyPlantAndEquipmentNet", "PropertyPlantAndEquipment"], 0),
    "매출채권": (["AccountsReceivableNetCurrent", "ReceivablesNetCurrent", "TradeAndOtherCurrentReceivables"], 0),
    "재고자산": (["InventoryNet", "Inventories"], 0),
    "매입채무": (["AccountsPayableCurrent", "AccountsPayableAndAccruedLiabilitiesCurrent", "TradeAndOtherCurrentPayables"], 0),
    "감가상각비": (["DepreciationDepletionAndAmortization", "DepreciationAndAmortization", "DepreciationAmortizationAndAccretionNet", "Depreciation",
               "AdjustmentsForDepreciationAndAmortisationExpense"], 4),
}
원하는태그 = {t for 후보, _q in 항목태그.values() for t in 후보}
태그열 = {"매출액": "매출태그", "CAPEX": "CAPEX태그", "매출원가": "매출원가태그", "매출채권": "매출채권태그", "매입채무": "매입채무태그", "감가상각비": "감가상각비태그"}
상세열 = ("매출원가", "유형자산", "매출채권", "재고자산", "매입채무", "감가상각비")

추출머리 = ["adsh", "cik", "name", "sic", "countryba", "afs", "fye", "form", "period", "fy", "filed", "uom",
         "매출액", "매출태그", "영업이익", "당기순이익", "자산총계", "영업현금흐름", "CAPEX", "CAPEX태그",
         "매출원가", "매출원가태그", "유형자산", "매출채권", "매출채권태그", "재고자산", "매입채무", "매입채무태그", "감가상각비", "감가상각비태그"]
패널머리 = ["고유번호", "회사명", "종목코드", "표시통화", "재무제표구분", "매출액", "영업이익", "당기순이익", "자산총계",
         "영업현금흐름", "CAPEX", "매출태그", "CAPEX태그", "양식", "기간종료", "제출일", "접수번호", "결산월", "소재국",
         "매출원가", "유형자산", "매출채권", "재고자산", "매입채무", "감가상각비", "매출원가태그", "매출채권태그", "매입채무태그", "감가상각비태그"]


def 기본자리():
    import 기저율 as 기                                    # noqa: PLC0415
    설정 = 기.설정읽기()
    return 기.패널자리(기.국가설정(설정, "US"))


def 분기들(부터, 까지, 분기):
    for y in range(부터, 까지 + 1):
        for q in 분기:
            yield "%dq%d" % (y, q)


# ═══════════════════════════════════════════════ 받기

def 받기(자리, 부터, 까지, 분기):
    """없는 ZIP 만 받는다. 404(아직 안 나온 분기)는 「없음」으로 적고 멈추지 않는다. (받은, 없음, 실패)."""
    import requests                                      # noqa: PLC0415
    contact = os.environ.get("SEC_CONTACT_EMAIL")
    if not contact:
        print("환경변수 SEC_CONTACT_EMAIL 이 없다 — 받지 못한다(--오프라인 이면 있는 ZIP 만 푼다)")
        return None
    H = {"User-Agent": "DCF-research %s" % contact, "Accept-Encoding": "gzip, deflate"}
    f = os.path.join(자리, "fsds")
    os.makedirs(f, exist_ok=True)
    받은, 없음, 실패 = [], [], []
    for yq in 분기들(부터, 까지, 분기):
        p = os.path.join(f, yq + ".zip")
        if os.path.exists(p) and os.path.getsize(p) > 0:
            continue
        url = ZIP주소 % yq
        ok = False
        for i in range(3):
            try:
                r = requests.get(url, headers=H, timeout=600, stream=True)
                if r.status_code == 404:
                    없음.append(yq)
                    ok = True
                    break
                if r.status_code != 200:
                    time.sleep(2.0 * (i + 1))
                    continue
                with io.open(p + ".part", "wb") as w:
                    for chunk in r.iter_content(1 << 20):
                        w.write(chunk)
                os.replace(p + ".part", p)
                받은.append(yq)
                ok = True
                break
            except requests.RequestException:
                time.sleep(2.0 * (i + 1))
        if not ok:
            실패.append(yq)
        time.sleep(0.5)
    return 받은, 없음, 실패


# ═══════════════════════════════════════════════ 풀기

def _수(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def 풀기(zip경로, 추출경로):
    """ZIP 하나 → 추출 CSV 하나. (제출건 수, 뽑은 행 수). 깨진 ZIP 이면 예외."""
    with zipfile.ZipFile(zip경로) as z:
        제출 = {}
        with io.TextIOWrapper(z.open("sub.txt"), encoding="utf-8", errors="replace", newline="") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                if r.get("form") in 양식 and (r.get("fp") or "").strip() == "FY":
                    제출[r["adsh"]] = {k: (r.get(k) or "").strip() for k in
                                     ("cik", "name", "sic", "countryba", "afs", "fye", "form", "period", "fy", "filed")}
        값 = {}                                            # adsh → uom → 항목 → (태그순위, 태그, 값)
        순위 = {t: i for 후보, _q in 항목태그.values() for i, t in enumerate(후보)}
        항목of = {t: 항 for 항, (후보, _q) in 항목태그.items() for t in 후보}
        q필요 = {항: q for 항, (_후보, q) in 항목태그.items()}
        with io.TextIOWrapper(z.open("num.txt"), encoding="utf-8", errors="replace", newline="") as f:
            next(f)                                        # 머리
            for line in f:
                adsh = line[:20]
                s = 제출.get(adsh)
                if s is None:
                    continue
                c = line.rstrip("\r\n").split("\t")
                if len(c) < 9:
                    continue
                tag = c[1]
                if tag not in 원하는태그 or c[6] or c[7] or c[3] != s["period"]:
                    continue
                항 = 항목of[tag]
                if c[4] != str(q필요[항]):
                    continue
                v = _수(c[8])
                if v is None:
                    continue
                d = 값.setdefault(adsh, {}).setdefault(c[5], {})
                if 항 not in d or 순위[tag] < d[항][0]:
                    d[항] = (순위[tag], tag, v)
    os.makedirs(os.path.dirname(추출경로), exist_ok=True)
    n = 0
    with io.open(추출경로, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=추출머리)
        w.writeheader()
        for adsh, s in 제출.items():
            통화별 = 값.get(adsh)
            if not 통화별:
                continue
            uom = "USD" if "USD" in 통화별 else max(통화별, key=lambda u: len(통화별[u]))
            d = 통화별[uom]
            row = dict(s, adsh=adsh, uom=uom)
            for 항 in 항목태그:
                row[항] = ("%.4f" % d[항][2]).rstrip("0").rstrip(".") if 항 in d else ""
                if 항 in 태그열:
                    row[태그열[항]] = d[항][1] if 항 in d else ""
            w.writerow(row)
            n += 1
    return len(제출), n


def 풀기전부(자리, 다시=False):
    """있는 ZIP 가운데 추출본이 없는 것만 푼다. (푼 목록, 깨진 목록)."""
    f = os.path.join(자리, "fsds")
    푼, 깨진 = [], []
    for zp in sorted(glob.glob(os.path.join(f, "????q?.zip"))):
        yq = os.path.basename(zp)[:-4]
        xp = os.path.join(f, "추출_%s.csv" % yq)
        if os.path.exists(xp) and not 다시:
            continue
        t = time.time()
        try:
            n제출, n행 = 풀기(zp, xp)
        except (zipfile.BadZipFile, KeyError, OSError) as e:
            깨진.append((yq, "%s: %s" % (type(e).__name__, e)))
            continue
        푼.append((yq, n제출, n행, round(time.time() - t, 1)))
        print("  %s — 연차 제출 %d건 · 뽑은 행 %d · %.1f초" % (yq, n제출, n행, time.time() - t))
    return 푼, 깨진


# ═══════════════════════════════════════════════ 합치기

값칸 = ("매출액", "영업이익", "당기순이익", "자산총계", "영업현금흐름", "CAPEX") + 상세열


def 정규끝해(period):
    """기간 끝날(YYYYMMDD · YYYY-MM-DD)의 해 — 끝날이 그 달 7일 이하면 앞 달로 본다(52 · 53주 결산이 다음 달 초로 넘어간 해). 못 읽으면 None."""
    p = re.sub(r"[^0-9]", "", "%s" % (period or ""))
    if len(p) < 8:
        return None
    y, m, d = int(p[:4]), int(p[4:6]), int(p[6:8])
    if d <= 7:
        m -= 1
        if m == 0:
            y -= 1
    return y


def 합치기(자리):
    """추출본 전부 → 회계연도별 주요계정 CSV + 산업분류.csv. 같은 (cik, fy) 는 **칸마다 filed 최신**(정정본이 안 적은 칸은 원본 값).
    {fy: 행수} · 회사수."""
    f = os.path.join(자리, "fsds")
    모든행 = []
    for xp in sorted(glob.glob(os.path.join(f, "추출_????q?.csv"))):
        with io.open(xp, encoding="utf-8-sig", newline="") as g:
            for r in csv.DictReader(g):
                if r.get("cik"):
                    모든행.append(r)
    # 회계연도 열쇠는 기간 끝날에서 다시 매긴다(2026-10-24 PM) — sub.txt 의 fy 는 같은 회사 안에서도 해마다 흔들려(1 · 3월 결산의
    # 최근 연차가 끝날 해로 적혀 앞 해가 빈다 · NVDA fy2025 빈칸 따위 0.4%) 해가 비거나 겹쳤다. 회사마다 「fy − 정규 끝날의 해」 최빈값(그 회사의
    # 표기 관례)을 정하고, 모든 제출건을 정규 끝날의 해 + 그 차로 매긴다. 정규 끝날 = 끝날이 그 달 7일 이하면 앞 달 말(52 · 53주 결산).
    차들 = {}
    for r in 모든행:
        e = 정규끝해(r.get("period"))
        fy = r.get("fy") or ""
        if e is not None and fy.isdigit():
            차들.setdefault(r["cik"].zfill(10), []).append(int(fy) - e)
    관례 = {c: max(set(v), key=lambda d: (v.count(d), -abs(d))) for c, v in 차들.items()}
    묶음 = {}
    for r in 모든행:
        c = r["cik"].zfill(10)
        e = 정규끝해(r.get("period"))
        if e is not None:
            fy = e + 관례.get(c, 0)
        else:
            fy0 = r.get("fy") or ""
            if not fy0.isdigit():
                continue
            fy = int(fy0)
        묶음.setdefault((c, fy), []).append(r)
    최신 = {}
    for k, rs in 묶음.items():
        rs.sort(key=lambda r: (r["filed"], r["adsh"]))
        합 = dict(rs[-1])                                   # 머리(이름 · SIC · 양식 · 접수번호 · 제출일 · 통화)는 가장 늦은 제출건
        for 항 in 값칸:
            값들 = [r for r in rs if r.get(항) not in (None, "") and r.get("uom") == 합["uom"]]
            if 값들:
                합[항] = 값들[-1][항]
                if 항 in 태그열:
                    합[태그열[항]] = 값들[-1][태그열[항]]
        최신[k] = 합
    해별 = {}
    for (cik, fy), r in 최신.items():
        해별.setdefault(fy, []).append((cik, r))
    for p in glob.glob(os.path.join(자리, "주요계정_????.csv")):
        os.remove(p)
    for fy, rows in sorted(해별.items()):
        with io.open(os.path.join(자리, "주요계정_%d.csv" % fy), "w", encoding="utf-8-sig", newline="") as g:
            w = csv.DictWriter(g, fieldnames=패널머리)
            w.writeheader()
            for cik, r in sorted(rows):
                row = {"고유번호": cik, "회사명": r["name"], "종목코드": "", "표시통화": r["uom"], "재무제표구분": "CFS",
                       "매출액": r["매출액"], "영업이익": r["영업이익"], "당기순이익": r["당기순이익"], "자산총계": r["자산총계"],
                       "영업현금흐름": r["영업현금흐름"], "CAPEX": r["CAPEX"], "매출태그": r["매출태그"], "CAPEX태그": r["CAPEX태그"],
                       "양식": r["form"], "기간종료": r["period"], "제출일": r["filed"], "접수번호": r["adsh"],
                       "결산월": r["fye"], "소재국": r["countryba"]}
                for 항 in 상세열:                           # 옛 추출본(상세 열 없음)도 읽힌다 — 빈 칸
                    row[항] = r.get(항, "")
                    if 항 in 태그열:
                        row[태그열[항]] = r.get(태그열[항], "")
                w.writerow(row)
    회사 = {}
    for (cik, fy), r in sorted(최신.items(), key=lambda kv: kv[1]["filed"]):
        회사[cik] = r                                      # 가장 늦게 제출한 것의 이름 · SIC
    with io.open(os.path.join(자리, "산업분류.csv"), "w", encoding="utf-8-sig", newline="") as g:
        w = csv.writer(g)
        w.writerow(["고유번호", "회사명", "종목코드", "상장구분", "산업분류코드", "소재국"])
        for cik, r in sorted(회사.items()):
            w.writerow([cik, r["name"], "", r["afs"], r["sic"], r["countryba"]])
    return {fy: len(rows) for fy, rows in sorted(해별.items())}, len(회사)


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="SEC FSDS → 미국 전 제출인 연간 주요계정 패널(기저율의 미국 비교 집단)")
    ap.add_argument("--자리", help="패널 자리(기본: 기저율설정.json 국가별.US 의 공용 자리)")
    ap.add_argument("--받기", action="store_true", help="없는 분기 ZIP 을 받는다(네트워크)")
    ap.add_argument("--오프라인", action="store_true", help="받지 않고 있는 ZIP 만 푼다")
    ap.add_argument("--부터", type=int)
    ap.add_argument("--까지", type=int)
    ap.add_argument("--분기", default="1,2,3,4", help="받을 분기(기본 1,2,3,4 — 12월 결산만이면 1,2 로도 대부분 덮인다)")
    ap.add_argument("--다시풀기", action="store_true", help="추출본이 있어도 ZIP 을 다시 푼다")
    a = ap.parse_args()
    자리 = a.자리 or 기본자리()
    os.makedirs(자리, exist_ok=True)
    기록 = {"형식": "fsds패널 1", "만든날": datetime.date.today().isoformat(), "자리": 자리, "출처": ZIP주소 % "{yyyy}q{n}",
          "규칙": "연차 양식 · fp=FY · 비차원 · 연결 실체 · ddate=period · 흐름 qtrs 4 · 시점 qtrs 0 · (cik, fy) 칸마다 filed 최신(정정본이 안 적은 칸은 원본)"}
    if a.받기 and not a.오프라인:
        import 기저율 as 기                                # noqa: PLC0415
        설정 = 기.설정읽기()
        부터 = a.부터 or (설정.get("국가별", {}).get("US", {}).get("부터") or 설정["패널"]["부터"])
        까지 = a.까지 or datetime.date.today().year
        분기 = [int(x) for x in a.분기.split(",") if x.strip()]
        r = 받기(자리, 부터, 까지, 분기)
        if r is None:
            return 입력오류
        기록["받기"] = {"받은": r[0], "없음(404)": r[1], "실패": r[2]}
        print("받기 — 새로 %d · 아직 없음 %d · 실패 %d" % (len(r[0]), len(r[1]), len(r[2])))
    푼, 깨진 = 풀기전부(자리, a.다시풀기)
    기록["풀기"] = {"푼": 푼, "깨진": 깨진}
    if 깨진:
        for yq, 까 in 깨진:
            print("  깨진 ZIP %s — %s (지우고 다시 받는다)" % (yq, 까))
    if not glob.glob(os.path.join(자리, "fsds", "추출_????q?.csv")):
        print("입력오류 — 풀 ZIP 이 하나도 없다(%s). --받기 또는 ZIP 을 fsds/ 에 둔다" % os.path.join(자리, "fsds"))
        return 입력오류
    해별, 회사수 = 합치기(자리)
    기록["합치기"] = {"회계연도별_회사수": {str(k): v for k, v in 해별.items()}, "회사수": 회사수}
    io.open(os.path.join(자리, "fsds_처리기록.json"), "w", encoding="utf-8").write(json.dumps(기록, ensure_ascii=False, indent=1))
    print("합치기 — 회계연도 %s · 회사 %d · → %s" % (", ".join("%d(%d)" % kv for kv in 해별.items()), 회사수, 자리))
    return 입력오류 if 깨진 else 통과


if __name__ == "__main__":
    sys.exit(main())

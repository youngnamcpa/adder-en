# -*- coding: utf-8 -*-
"""DART 일괄 패널 — 전자공시 「재무정보 일괄다운로드」로 국내 전 상장사의 본표 전 계정을 받아 상세 패널을 짓는다 (제안 C-한국 · 2026-10-22 신설).

무엇을 하나
  `dart_peer_screen.py`(fnlttMultiAcnt)의 주요계정 열넷에는 매출채권 · 재고 · 매입채무 · 유형자산 · CAPEX · 감가상각이 없어 회전일수 · CAPEX 비율 ·
  상각률의 기저율을 못 냈다(기저율설정 `변수_대체_사유`). OpenDART 공시정보활용마당의 「재무정보 일괄다운로드」는 사업연도 · 보고서 · 재무제표(BS · PL · CF · CE)
  단위 ZIP(탭 구분 TXT · cp949) 하나에 IFRS XBRL 편집기로 제출한 상장사 전체의 **본표 전 계정**을 표준 항목코드(ifrs-full_* · dart_*)로 담는다.
  로그인 · 인증키 없이 세션(main.do → list.do → downloadFnlttZip.do)으로 받힌다(2026-10-22 실측 — 2015~2026 · 분기 · 4종 · 172 ZIP · BS 하나 5~26MB).

    자리  {공용}/기저율/일괄/{연도}_{분기}_{표}.zip (한 번 받으면 다시 받지 않는다) → 상세_{연도}.csv (사업보고서 = 4Q)
    열    종목코드 · 회사명 · 시장구분 · 업종코드 · 결산월 · 결산기준일 · 재무제표구분(연결 · 별도) · 통화 · 매출액 · 매출원가 · 영업이익 · 당기순이익 · 자산총계 ·
          유형자산 · 매출채권 · 재고자산 · 매입채무 · 영업현금흐름 · CAPEX · 감가상각비 · (항목마다 쓴 항목코드)

고르는 규칙 — 전부 「as filed」, 고치지 않는다
  ① 비금융 파일만(파일 이름에 금융기타 · 보험 · 은행 · 증권이 없는 것). 금융업은 매출 개념이 다르다(기저율 제외 산업과 같은 자리)
  ② 회사마다 **연결 파일을 먼저**, 연결에 없으면 별도(dart_peer_screen 과 같은 규칙) — `재무제표구분` 열에 적는다
  ③ 손익은 02_손익계산서와 03_포괄손익계산서 둘을 다 읽는다(단일 포괄손익계산서 회사는 03 에만 있다)
  ④ 항목마다 후보 항목코드를 차례로 두드리고 **쓴 코드를 열에 남긴다**(`매출채권코드` …). 당기 열(「당기」 · 「당기 N분기말」 · 「당기 N분기 누적」)만 쓴다
  ⑤ 금액은 원 단위 그대로(쉼표 제거). 비어 있으면 빈 칸 — 0 으로 메우지 않는다

읽는 곳 — `기저율.패널읽기` 가 같은 연도의 주요계정_{연도}.csv 에 **종목코드로 붙여** 선택 열(매출원가 · 유형자산 · 매출채권 · 재고자산 · 매입채무 ·
          영업현금흐름 · CAPEX · 감가상각비)을 더한다(없으면 없는 대로 — 2026-10-20 판과 같게). 기저율 「비율 자리」 · 지속성 변수가 그 열을 쓴다.
사용
  python 스크립트/dart_일괄패널.py --받기 [--부터 2015] [--까지 YYYY]        # 사업보고서(4Q) BS · PL · CF 를 받아 풀고 상세 CSV 를 짓는다
  python 스크립트/dart_일괄패널.py --오프라인                                # 받지 않고 있는 ZIP 만
  python 스크립트/dart_일괄패널.py --자리 <폴더>
종료 코드 — 0 통과 · 2 입력오류(목록을 못 받음 · ZIP 하나도 없음 · 깨진 ZIP).
인증키를 쓰지 않는다. 회사 · 업종 이름은 이 도구에 없다(범용). 표준 라이브러리 + requests.
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

주소 = "https://opendart.fss.or.kr"
머리H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36", "Accept-Language": "ko-KR,ko;q=0.9"}
표들 = ("BS", "PL", "CF")
금융낱말 = ("금융기타", "보험", "은행", "증권")

# 항목 → (후보 항목코드 차례, 표)
항목코드 = {
    "매출액": (["ifrs-full_Revenue", "ifrs-full_RevenueFromContractsWithCustomers", "dart_Revenue", "ifrs-full_RevenueFromSaleOfGoods", "dart_OperatingRevenue"], "PL"),
    "매출원가": (["ifrs-full_CostOfSales", "dart_CostOfSales", "ifrs-full_CostOfMerchandiseSold"], "PL"),
    "영업이익": (["dart_OperatingIncomeLoss", "ifrs-full_ProfitLossFromOperatingActivities"], "PL"),
    "당기순이익": (["ifrs-full_ProfitLoss", "ifrs-full_ProfitLossAttributableToOwnersOfParent"], "PL"),
    "자산총계": (["ifrs-full_Assets"], "BS"),
    "유형자산": (["ifrs-full_PropertyPlantAndEquipment"], "BS"),
    "매출채권": (["ifrs-full_TradeAndOtherCurrentReceivables", "ifrs-full_CurrentTradeReceivables", "dart_ShortTermTradeReceivable",
             "ifrs-full_TradeReceivables", "ifrs-full_TradeAndOtherReceivables"], "BS"),
    "재고자산": (["ifrs-full_Inventories", "ifrs-full_InventoriesTotal"], "BS"),
    "매입채무": (["ifrs-full_TradeAndOtherCurrentPayables", "dart_ShortTermTradePayables", "ifrs-full_TradeAndOtherCurrentPayablesToTradeSuppliers",
             "ifrs-full_TradeAndOtherPayablesToTradeSuppliers"], "BS"),
    "영업현금흐름": (["ifrs-full_CashFlowsFromUsedInOperatingActivities"], "CF"),
    "CAPEX": (["ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities"], "CF"),
    "감가상각비": (["ifrs-full_AdjustmentsForDepreciationExpense", "ifrs-full_AdjustmentsForDepreciationAndAmortisationExpense", "ifrs-full_DepreciationExpense"], "CF"),
}
상세머리 = (["종목코드", "회사명", "시장구분", "업종코드", "결산월", "결산기준일", "재무제표구분", "통화"] + list(항목코드)
        + ["%s코드" % k for k in 항목코드])


def 기본자리():
    import 기저율 as 기                                    # noqa: PLC0415
    return os.path.join(기.패널자리(기.국가설정(기.설정읽기(), "KR")), "일괄")


# ═══════════════════════════════════════════════ 받기

def 세션():
    import requests                                      # noqa: PLC0415
    s = requests.Session()
    s.get(주소 + "/disclosureinfo/fnltt/dwld/main.do", headers=머리H, timeout=60)
    return s


def 목록(s, 연도):
    """그 사업연도의 ZIP 파일 이름 목록(list.do — 응답 HTML 안의 파일 이름)."""
    h = dict(머리H, Referer=주소 + "/disclosureinfo/fnltt/dwld/main.do")
    h["X-Requested-With"] = "XMLHttpRequest"
    r = s.post(주소 + "/disclosureinfo/fnltt/dwld/list.do", headers=h, data={"bsnsYear": str(연도)}, timeout=60)
    if r.status_code != 200:
        return None
    return sorted(set(re.findall(r"(20\d\d_\dQ_(?:BS|PL|CF|CE)_\d+\.zip)", r.text)))


def 받기(자리, 부터, 까지, 분기=("4Q",), 표=표들):
    """없는 ZIP 만 받는다. (받은, 없음, 실패) 또는 None(목록 실패)."""
    s = 세션()
    os.makedirs(자리, exist_ok=True)
    받은, 없음, 실패 = [], [], []
    h = dict(머리H, Referer=주소 + "/disclosureinfo/fnltt/dwld/main.do")
    전목록 = 목록(s, 부터)                                  # list.do 는 전 연도를 한 번에 준다(2026-10-22 실측 — 172개)
    if 전목록 is None:
        return None
    for y in range(부터, 까지 + 1):
        for q in 분기:
            for t in 표:
                p = os.path.join(자리, "%d_%s_%s.zip" % (y, q, t))
                if os.path.exists(p) and os.path.getsize(p) > 0:
                    continue
                후 = [f for f in 전목록 if f.startswith("%d_%s_%s_" % (y, q, t))]
                if not 후:
                    없음.append("%d_%s_%s" % (y, q, t))
                    continue
                fn = sorted(후)[-1]
                ok = False
                for i in range(3):
                    try:
                        r = s.get(주소 + "/cmm/downloadFnlttZip.do?fl_nm=" + fn, headers=h, timeout=600, stream=True)
                        if r.status_code == 200 and "zip" in (r.headers.get("Content-Disposition") or "") + (r.headers.get("Content-Type") or ""):
                            with io.open(p + ".part", "wb") as w:
                                for c in r.iter_content(1 << 20):
                                    w.write(c)
                            os.replace(p + ".part", p)
                            ok = True
                            break
                    except Exception:                        # noqa: BLE001
                        pass
                    time.sleep(2.0 * (i + 1))
                (받은 if ok else 실패).append("%d_%s_%s" % (y, q, t))
                time.sleep(0.5)
    return 받은, 없음, 실패


# ═══════════════════════════════════════════════ 풀기

def _이름(zi):
    try:
        return zi.filename.encode("cp437").decode("cp949")
    except Exception:                                    # noqa: BLE001
        return zi.filename


def _수(s):
    s = (s or "").strip().replace(",", "")
    if not s or s in ("-",):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _당기열(머리):
    """「당기」 로 시작하는 첫 열의 자리(당기 · 당기 1분기말 · 당기 3분기 누적 …)."""
    for i, h in enumerate(머리):
        if h.strip().startswith("당기"):
            return i
    return None


def 코드정규화(코드):
    """2015~2018 일괄 파일은 표준 항목코드 접두를 `ifrs_` 로 적는다(그 뒤는 `ifrs-full_`) — 같은 코드로 읽는다.
    종전에는 이 접두를 몰라 그 네 해가 통째로 비었다(2016 매출원가 7곳 · 2026-10-24 PM 고침 · PK `dart_상세변수` 와 같은 규칙)."""
    return "ifrs-full_" + 코드[5:] if 코드.startswith("ifrs_") else 코드


def 풀기(zip경로, 표):
    """ZIP 하나 → {(종목코드, 재무제표구분): {항목: (값, 코드)} + 머리 칸}. 비금융 파일만 · 연결 · 별도 둘 다 모은다."""
    낸 = {}
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
                ci = _당기열(머리)
                if ci is None:
                    continue
                for r in rd:
                    if len(r) <= ci or len(r) < 12:
                        continue
                    코드 = 코드정규화(r[10].strip())
                    항들 = [항 for 항, (후보, t) in 항목코드.items() if t == 표 and 코드 in 후보]
                    if not 항들:
                        continue
                    종 = r[1].strip().strip("[]")
                    k = (종, 구분)
                    d = 낸.setdefault(k, {"회사명": r[2].strip(), "시장구분": r[3].strip(), "업종코드": r[4].strip(), "결산월": r[6].strip(),
                                        "결산기준일": r[7].strip(), "통화": r[9].strip(), "항목": {}})
                    v = _수(r[ci])
                    if v is None:
                        continue
                    for 항 in 항들:
                        순위 = 항목코드[항][0].index(코드)
                        old = d["항목"].get(항)
                        if old is None or 순위 < old[2]:
                            d["항목"][항] = (v, 코드, 순위)
    return 낸


def 짓기(자리, 연도):
    """그 연도 4Q 의 BS · PL · CF ZIP → 상세_{연도}.csv. 연결 우선 · 없으면 별도. 쓴 행 수 또는 None(ZIP 없음)."""
    모음 = {}
    있음 = False
    for 표 in 표들:
        p = os.path.join(자리, "%d_4Q_%s.zip" % (연도, 표))
        if not os.path.exists(p):
            continue
        있음 = True
        for (종, 구분), d in 풀기(p, 표).items():
            m = 모음.setdefault(종, {})
            e = m.setdefault(구분, {"회사명": d["회사명"], "시장구분": d["시장구분"], "업종코드": d["업종코드"], "결산월": d["결산월"],
                                  "결산기준일": d["결산기준일"], "통화": d["통화"], "항목": {}})
            e["항목"].update(d["항목"])
    if not 있음:
        return None
    n = 0
    with io.open(os.path.join(자리, "상세_%d.csv" % 연도), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=상세머리)
        w.writeheader()
        for 종 in sorted(모음):
            m = 모음[종]
            구분 = "연결" if "연결" in m else "별도"
            e = m[구분]
            if 구분 == "별도" and "연결" in m:
                e = m["연결"]
            row = {"종목코드": 종, "회사명": e["회사명"], "시장구분": e["시장구분"], "업종코드": e["업종코드"], "결산월": e["결산월"],
                   "결산기준일": e["결산기준일"], "재무제표구분": 구분, "통화": e["통화"]}
            # 연결에 없는 항목(예: 연결 손익만 있고 BS 가 별도만)은 별도에서 메우지 않는다 — 구분이 섞이면 비율이 어긋난다
            for 항 in 항목코드:
                v = e["항목"].get(항)
                row[항] = ("%.0f" % v[0]) if v else ""
                row["%s코드" % 항] = v[1] if v else ""
            w.writerow(row)
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="DART 재무정보 일괄다운로드 → 국내 전 상장사 본표 전 계정 상세 패널")
    ap.add_argument("--자리", help="ZIP · 상세 CSV 자리(기본: 공용 캐시 기저율/일괄)")
    ap.add_argument("--받기", action="store_true")
    ap.add_argument("--오프라인", action="store_true")
    ap.add_argument("--부터", type=int, default=2015)
    ap.add_argument("--까지", type=int, default=datetime.date.today().year - 1)
    a = ap.parse_args()
    자리 = a.자리 or 기본자리()
    os.makedirs(자리, exist_ok=True)
    기록 = {"형식": "dart일괄패널 1", "만든날": datetime.date.today().isoformat(), "자리": 자리, "출처": 주소 + "/disclosureinfo/fnltt/dwld/main.do",
          "규칙": "비금융 파일 · 연결 우선(없으면 별도 · 구분 혼합 금지) · 02 + 03 손익 · 항목코드 차례 · 당기 열 · 원 단위"}
    if a.받기 and not a.오프라인:
        r = 받기(자리, a.부터, a.까지)
        if r is None:
            print("입력오류 — 일괄다운로드 목록(list.do)을 받지 못했다")
            return 입력오류
        기록["받기"] = {"받은": r[0], "없음": r[1], "실패": r[2]}
        print("받기 — 새로 %d · 없음 %d · 실패 %d" % (len(r[0]), len(r[1]), len(r[2])))
    연도들 = sorted({int(os.path.basename(p)[:4]) for p in glob.glob(os.path.join(자리, "????_4Q_*.zip"))})
    if not 연도들:
        print("입력오류 — 풀 ZIP 이 하나도 없다(%s)" % 자리)
        return 입력오류
    결과 = {}
    for y in 연도들:
        t = time.time()
        try:
            n = 짓기(자리, y)
        except zipfile.BadZipFile as e:
            print("  %d 깨진 ZIP — %s" % (y, e))
            결과[str(y)] = "깨짐"
            continue
        결과[str(y)] = n
        print("  %d — 회사 %s · %.1f초" % (y, n, time.time() - t))
    기록["상세"] = 결과
    io.open(os.path.join(자리, "일괄_처리기록.json"), "w", encoding="utf-8").write(json.dumps(기록, ensure_ascii=False, indent=1))
    print("→ %s (상세_{연도}.csv)" % 자리)
    return 입력오류 if "깨짐" in 결과.values() else 통과


if __name__ == "__main__":
    sys.exit(main())

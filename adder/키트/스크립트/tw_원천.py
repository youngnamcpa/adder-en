# -*- coding: utf-8 -*-
"""tw_원천 — 대만 상장사(TWSE · TPEx)의 재무제표를 대만 공시 시스템(MOPS · 公開資訊觀測站) 인라인 XBRL 에서 읽어 companyfacts 꼴로 넣는다.

**왜 만들었나(2026-10-24 W13 · TSMC).** 대만 회사가 미국에 ADR 로 상장해 20-F 를 내도 반기 · 분기 재무는 SEC 에 XBRL 로 오지 않는다
(6-K 문서뿐). 평가기준일이 반기 말이면 원천 조립(13번)의 기준일 열이 빈다. 대만 공시 시스템의 재무제표(`t164sb01` — 연결 · 개별)는
**인라인 XBRL** 이라 금액 칸마다 IFRS 표준 태그(`ifrs-full:CashAndCashEquivalents` …)와 기간 맥락이 붙어 있다. 그것을 SEC companyfacts 와 같은
꼴로 `_raw/companyfacts.json` 에 더하면 **원천 조립(`sec_원천.py`)이 손대지 않고 그대로 조립한다**(ifrs-full 경로 · 보고통화 TWD).
ADR 이 없는 대만 회사는 companyfacts 가 없으니 이 도구가 새로 짓는다(같은 꼴).

규칙(sec_xbrl보충 과 같다)
  · `ifrs-full` 이름공간만 넣는다 — 대만 확장 태그(tifrs-*)는 넣지 않는다(국가 간 같은 태그로 조립하려고).
  · 차원(축 · 멤버) 맥락은 넣지 않는다. scale · sign 을 반영한다(scale 3 = 천 원 단위 → 원 단위로).
  · 접수번호 자리에는 `MOPS:<종목>:<연도>Q<분기>:<연결 C|개별 A>` 를 적는다(되짚어 갈 출처). 양식은 `MOPS-Q<분기>`.
  · 받은 문서는 `_raw/tw/` 에 두고(캐시 — 있으면 다시 받지 않는다) `_보충` 목록에 주소 · 조회일을 적는다.

사용:
    python 스크립트/tw_원천.py --종목 2330 --연도 2026 --분기 2                 # 반기(2분기) 연결 재무 → companyfacts 에 더한다
    python 스크립트/tw_원천.py --종목 2330 --연도 2023,2024,2025 --분기 4       # 연간(4분기 보고서 = 한 해) 셋
    python 스크립트/tw_원천.py --종목 2330 --연도 2026 --분기 2 --파일 받아둔.html   # 네트워크 없이
    python 스크립트/tw_원천.py --종목 2330 --종가 2026-06-30                     # 원주 종가(대만증권거래소 일별 · 그날이 휴장이면 앞 마지막 거래일)
      → `_raw/tw/종가_<종목>_<날짜>.json`. 미국 ADR 은 원주와 값이 다르다(ADR 비율 · 프리미엄) — 역산 · 시가총액은 표시통화 원주 종가로
뒤에 `python 스크립트/sec_원천.py --기준일 2026-06-30` 을 돈다(보고통화 TWD · ifrs-full).
종료 코드 — 0 넣음 / 1 받지 못함 / 2 입력 오류.
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass
여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from sec_xbrl보충 import 합치기  # noqa: E402

ROOT = os.path.dirname(여기)
주소꼴 = "https://mopsov.twse.com.tw/server-java/t164sb01?step=1&CO_ID={종목}&SYEAR={연도}&SSEASON={분기}&REPORT_ID={보고}"
_맥락 = re.compile(r"<xbrli:context\b[^>]*\bid=\"([^\"]+)\"[^>]*>(.*?)</xbrli:context>", re.S)
_사실 = re.compile(r"<ix:nonFraction\b([^>]*)>(.*?)</ix:nonFraction>", re.S)
_속 = re.compile(r"(\w[\w:-]*)=\"([^\"]*)\"")


def 맥락표(글):
    """{맥락 id: (start | None, end, 차원 있음)}."""
    낸 = {}
    for cid, 몸 in _맥락.findall(글):
        차원 = ("explicitMember" in 몸) or ("typedMember" in 몸) or ("<xbrli:scenario" in 몸)
        즉 = re.search(r"<xbrli:instant>\s*([0-9-]{10})", 몸)
        if 즉:
            낸[cid] = (None, 즉.group(1), 차원)
            continue
        s = re.search(r"<xbrli:startDate>\s*([0-9-]{10})", 몸)
        e = re.search(r"<xbrli:endDate>\s*([0-9-]{10})", 몸)
        if s and e:
            낸[cid] = (s.group(1), e.group(1), 차원)
    return 낸


# 대만 확장 태그 · 현금흐름 조정 태그 → 원천 조립이 찾는 IFRS 표준 태그(같은 숫자를 다른 이름으로 단 자리만 · 원래 사실이 없을 때만 다리를 놓는다)
다리 = {"OperatingCosts": "CostOfSales",                                  # 5000 營業成本合計(tifrs-bsci-ci)
      "GrossProfitLossFromOperations": "GrossProfit",                   # 5900 營業毛利
      "AdjustmentsForDepreciationExpense": "DepreciationExpense",       # A20100 折舊費用(현금흐름 조정 = 손익의 감가상각비)
      "AdjustmentsForAmortisationExpense": "AmortisationExpense",       # A20200 攤銷費用
      "LongtermLiabilitiesCurrentPortion": "CurrentPortionOfLongtermBorrowings"}   # 2320 一年或一營業週期內到期長期負債(사채 · 장기차입 유동 몫)
# IFRS 정의상 지급 · 취득은 양수(유출)다. MOPS 는 이 칸에 sign="-" 를 달아 음수로 낸다 — 표준 꼴(SEC companyfacts · 20-F)과 맞추려고 절대값으로
_유출 = re.compile(r"^(PurchaseOf|PaymentsFor|PaymentsOf|PaymentsTo|Acquisition|CashOutflow|InterestPaid|DividendsPaid|IncomeTaxesPaid)")


def 파싱(내용):
    """MOPS 인라인 XBRL(바이트) → 사실 [{이름공간 · 태그 · 단위 · start? · end · val · 보충글?}] — ifrs-full · 비차원 · 숫자만.
    대만 확장(tifrs-*)은 `다리` 표의 줄만 IFRS 표준 이름으로 옮겨 싣고(그 맥락에 표준 사실이 없을 때), 지급 · 취득 칸은 양수로 맞춘다."""
    글 = 내용.decode("utf-8", "replace") if isinstance(내용, (bytes, bytearray)) else 내용
    맥 = 맥락표(글)
    낸, 곁 = [], []
    for 속글, 값글 in _사실.findall(글):
        a = dict(_속.findall(속글))
        이름 = a.get("name") or ""
        if ":" not in 이름:
            continue
        접두, 태그 = 이름.split(":", 1)
        표준 = 접두 == "ifrs-full"
        if not 표준 and 태그 not in 다리:
            continue
        m = 맥.get(a.get("contextRef"))
        if not m or m[2]:
            continue
        t = re.sub(r"<[^>]+>", "", 값글).strip().replace(",", "")
        if not t or t in ("-", "—"):
            continue
        try:
            v = float(t)
        except ValueError:
            continue
        v *= 10 ** int(a.get("scale") or 0)
        if a.get("sign") == "-":
            v = -v
        글보 = None
        if _유출.match(태그) and v < 0:
            v, 글보 = -v, "tw_원천(지급 칸 부호 — 양수로)"
        if v.is_integer() and abs(v) < 1e18:
            v = int(v)
        한 = {"이름공간": "ifrs-full", "태그": 태그, "단위": a.get("unitRef") or "TWD", "end": m[1], "val": v}
        if m[0]:
            한["start"] = m[0]
        if 글보:
            한["보충글"] = 글보
        (낸 if 표준 else 곁).append(한)
    있 = {(x["태그"], x.get("start"), x["end"]) for x in 낸}
    for x in 곁 + [y for y in 낸 if y["태그"] in 다리]:
        목 = 다리[x["태그"]]
        if (목, x.get("start"), x["end"]) in 있:
            continue
        새 = dict(x, 태그=목, 보충글="tw_원천(다리 %s → %s)" % (x["태그"], 목))
        낸.append(새)
        있.add((목, x.get("start"), x["end"]))
    return 낸


def 받기(종목, 연도, 분기, 보고, 곳):
    """MOPS t164sb01 문서를 받아 `_raw/tw/` 에 둔다(있으면 그대로) → (경로, 주소)."""
    import requests                                  # noqa: PLC0415
    주소 = 주소꼴.format(종목=종목, 연도=연도, 분기=분기, 보고=보고)
    os.makedirs(곳, exist_ok=True)
    p = os.path.join(곳, "t164sb01_%s_%sQ%s_%s.html" % (종목, 연도, 분기, 보고))
    if os.path.exists(p) and os.path.getsize(p) > 10000:
        return p, 주소
    r = requests.get(주소, headers={"User-Agent": "Mozilla/5.0"}, timeout=120)
    r.raise_for_status()
    if b"ix:nonFraction" not in r.content:
        raise RuntimeError("재무제표가 없는 응답(%d바이트) — 그 분기 보고서가 아직 없거나 종목 · 보고 구분이 다르다" % len(r.content))
    with open(p, "wb") as f:
        f.write(r.content)
    return p, 주소


def 종가받기(종목, 날짜, 곳):
    """대만증권거래소(TWSE) 일별 시세(STOCK_DAY) → 평가기준일(휴장이면 앞 마지막 거래일)의 원주 종가. 상장 시장이 TPEx(上櫃)면 이 창구에 없다 — 알린다."""
    import requests                                  # noqa: PLC0415
    주소 = "https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?date=%s&stockNo=%s&response=json" % (날짜.replace("-", ""), 종목)
    r = requests.get(주소, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
    r.raise_for_status()
    d = r.json()
    if d.get("stat") != "OK" or not d.get("data"):
        raise RuntimeError("TWSE 일별 시세가 없다(%s) — 상장 시장이 TPEx(上櫃)면 TPEx 일별 시세에서 받는다" % d.get("stat"))
    머 = d.get("fields") or []
    i날, i종 = 머.index("日期"), 머.index("收盤價")
    후 = []
    for 줄 in d["data"]:
        y, m, dd = 줄[i날].strip().split("/")
        iso = "%04d-%s-%s" % (int(y) + 1911, m, dd)            # 민국 연도 → 서기
        if iso <= 날짜:
            후.append((iso, float(줄[i종].replace(",", ""))))
    if not 후:
        raise RuntimeError("그 달에 %s 이전 거래일이 없다 — 앞 달을 본다" % 날짜)
    iso, 값 = 후[-1]
    낸 = {"종목": 종목, "평가기준일": 날짜, "거래일": iso, "종가": 값, "통화": "TWD", "출처": "臺灣證券交易所 個股日成交資訊(STOCK_DAY) 收盤價",
         "주소": 주소, "조회일": datetime.date.today().isoformat(),
         "비고": "평가기준일 당일" if iso == 날짜 else "평가기준일이 휴장이라 앞 마지막 거래일 %s" % iso}
    os.makedirs(곳, exist_ok=True)
    p = os.path.join(곳, "종가_%s_%s.json" % (종목, 날짜))
    json.dump(낸, io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return p, 낸


def 빈뼈대(종목):
    return {"cik": None, "entityName": "TW %s" % 종목, "facts": {}, "_출처": "tw_원천 — MOPS 인라인 XBRL(ADR 이 없는 대만 회사)"}


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="대만 MOPS 인라인 XBRL 재무 → companyfacts 꼴")
    ap.add_argument("--종목", required=True, help="대만 종목코드(예: 2330)")
    ap.add_argument("--연도", help="서기 연도 하나 또는 쉼표로 여럿(2023,2024,2025) — 재무 쪽: 재무기준일 F 의 보고까지")
    ap.add_argument("--분기", type=int, choices=(1, 2, 3, 4), help="4 = 연간 보고서 — 재무 쪽: 재무기준일 F 가 든 분기")
    ap.add_argument("--종가", "--평가기준일", dest="종가", nargs="?", const="",
                    help="평가기준일 T(YYYY-MM-DD) — 원주 종가만 받는다(TWSE 일별 · 시장 쪽). 값 없이 주면 --가정 의 평가기준일")
    ap.add_argument("--가정", default=None, help="가정 파일 — --종가 를 값 없이 주면 기준일.py 로 평가기준일 T 를 푼다")
    ap.add_argument("--개별", action="store_true", help="개별(A) — 기본은 연결(C)")
    ap.add_argument("--raw", default=os.path.join(ROOT, "_raw"))
    ap.add_argument("--파일", help="받아 둔 t164sb01 문서(네트워크 없이 · 연도 하나일 때)")
    a = ap.parse_args(argv)
    if a.종가 is not None and (a.종가 or a.가정):
        import 기준일인자 as _기인                              # noqa: PLC0415 — 날짜 둘(2026-10-25): 종가는 시장 쪽 T
        a.종가 = _기인.풀기(a.종가, a.가정, _기인.평가, 인자="--종가")
    if a.종가 == "":
        print("--종가 에 날짜를 주거나 --가정 을 준다")
        return 2
    if a.종가:
        try:
            p, 낸 = 종가받기(a.종목, a.종가, os.path.join(a.raw, "tw"))
        except Exception as e:                       # noqa: BLE001
            print("종가를 받지 못함 — %s: %s" % (type(e).__name__, str(e)[:160]))
            return 1
        print("종가: %s %s %s 대만달러(%s) → %s" % (a.종목, 낸["거래일"], "{:,.2f}".format(낸["종가"]), 낸["비고"], p))
        return 0
    if not (a.연도 and a.분기):
        print("--연도 와 --분기 를 준다(또는 --종가)")
        return 2
    보고 = "A" if a.개별 else "C"
    연도들 = [y.strip() for y in a.연도.split(",") if y.strip()]
    if a.파일 and len(연도들) != 1:
        print("--파일 은 연도 하나일 때만")
        return 2
    cfp = os.path.join(a.raw, "companyfacts.json")
    cf = json.load(io.open(cfp, encoding="utf-8")) if os.path.exists(cfp) else 빈뼈대(a.종목)
    if os.path.exists(cfp) and not os.path.exists(os.path.join(a.raw, "companyfacts_원본.json")):
        import shutil                                # noqa: PLC0415
        shutil.copyfile(cfp, os.path.join(a.raw, "companyfacts_원본.json"))
    오늘 = datetime.date.today().isoformat()
    실패 = 0
    for y in 연도들:
        try:
            if a.파일:
                p, 주소 = a.파일, "(받아 둔 파일) %s" % os.path.basename(a.파일)
            else:
                p, 주소 = 받기(a.종목, y, a.분기, 보고, os.path.join(a.raw, "tw"))
            사실 = 파싱(open(p, "rb").read())
            접 = "MOPS:%s:%sQ%d:%s" % (a.종목, y, a.분기, 보고)
            양식 = "MOPS-Q%d" % a.분기
            n = 합치기(cf, 사실, 접, 양식, 오늘, y, "FY" if a.분기 == 4 else "Q%d" % a.분기)
            cf.setdefault("_보충", []).append({"접수번호": 접, "양식": 양식, "접수일": 오늘, "사실수": n, "주소": 주소, "조회일": 오늘,
                                             "출처": "대만 공시 시스템(MOPS 公開資訊觀測站) 재무제표 t164sb01 — 인라인 XBRL · ifrs-full 비차원 사실만"})
            print("넣음: %s %s년 %d분기(%s) — 사실 %d건(받은 ifrs-full %d)" % (a.종목, y, a.분기, "연결" if 보고 == "C" else "개별", n, len(사실)))
        except Exception as e:                       # noqa: BLE001
            실패 += 1
            print("받지 못함: %s %s년 %d분기 — %s: %s" % (a.종목, y, a.분기, type(e).__name__, str(e)[:160]))
    os.makedirs(a.raw, exist_ok=True)
    json.dump(cf, io.open(cfp, "w", encoding="utf-8"), ensure_ascii=False)
    print("저장: %s" % cfp)
    return 1 if 실패 else 0


if __name__ == "__main__":
    sys.exit(main())

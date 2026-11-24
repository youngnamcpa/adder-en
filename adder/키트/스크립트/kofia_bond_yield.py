# -*- coding: utf-8 -*-
"""금융투자협회 채권정보센터 채권시가평가수익률(일자별) 조회.

화면(WebSquare)이 쓰는 내부 서비스를 그대로 호출한다. 브라우저 자동화가 필요 없다.

    POST https://www.kofiabond.or.kr/proframeWeb/XMLSERVICES/
    pfmAppName BIS-KOFIABOND / pfmSvcName BISBndSrtPrcSrchSO
    pfmFnName  getHeadList (만기 헤더) / selectDay (본표)

요청 DTO
    standardDt   조회일 YYYYMMDD
    reportCompCd A20000 = 평가사 평균(`23.1.9~)
    applyGbCd    C00 = 본표, C02 = 개별공사·공단채
    val1~val5    선택한 평가사 코드 (전부 선택이 화면 기본 사용법)

사용법
    python kofia_bond_yield.py                     # 최근 영업일, BBB+ 10년
    python kofia_bond_yield.py --date 2026-06-30 --grade AA+
    python kofia_bond_yield.py --date 2026-06-30 --all      # 등급 전체 표
    python kofia_bond_yield.py --가정 가정.json --gov       # 날짜는 가정의 평가기준일 T

날짜 둘(2026-10-25 · `기준일.py`) — 시장 쪽 도구다. `--date`(별칭 `--평가기준일`)는 **평가기준일 T**(분석일)다 — 지금 뜻 그대로.
재무기준일(최근 공시 분기말)로 금리를 받지 않는다. 휴장일이면 직전 영업일 값이고 실제 날짜를 찍는다.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
import time
import xml.etree.ElementTree as ET

import requests

SESSION = requests.Session()      # 연결을 재사용해 연속 호출에서 끊기는 것을 줄인다

URL = "https://www.kofiabond.or.kr/proframeWeb/XMLSERVICES/"
APP, SVC = "BIS-KOFIABOND", "BISBndSrtPrcSrchSO"

# 평가사 코드. 화면의 기관명 체크박스 다섯 개와 같다.
AGENCIES = {
    "val1": "A10002",  # 나이스피앤아이
    "val2": "A10003",  # 한국자산평가
    "val3": "A10004",  # KIS자산평가
    "val4": "A10005",  # 에프앤자산평가
    "val5": "A10006",  # 이지자산평가
}
COMP_AVG = "A20000"  # 평가사 평균(`23.1.9~)

HEADERS = {
    "Content-Type": "application/xml; charset=UTF-8",
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.kofiabond.or.kr/",
}


def _envelope(fn: str, dto: str) -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n<message>\n'
        f"<proframeHeader>\n<pfmAppName>{APP}</pfmAppName>\n"
        f"<pfmSvcName>{SVC}</pfmSvcName>\n<pfmFnName>{fn}</pfmFnName>\n</proframeHeader>\n"
        f"<systemHeader></systemHeader>\n{dto}</message>\n"
    )


def _post(fn: str, dto: str, timeout: int = 20, tries: int = 4) -> ET.Element:
    """서버가 연속 호출에서 연결을 끊는 일이 있어 몇 번 다시 시도한다."""
    body = _envelope(fn, dto).encode("utf-8")
    last = None
    for i in range(tries):
        try:
            r = SESSION.post(URL, data=body, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            return ET.fromstring(r.content)
        except (requests.exceptions.RequestException, ET.ParseError) as e:
            last = e
            if i < tries - 1:
                time.sleep(1.5 * (i + 1))     # 1.5초, 3초, 4.5초
    msg = [
        "금융투자협회 조회가 %d번 다 실패했습니다." % tries,
        "  마지막 오류: %s" % type(last).__name__,
        "  잠시 뒤 다시 돌려 보시고, 계속 실패하면 사이트 규격이 바뀐 것일 수 있습니다.",
        "  값을 비슷한 것으로 메우지 말고 확인 불가로 두십시오.",
    ]
    raise SystemExit(chr(10).join(msg))


def _text(node: ET.Element, tag: str) -> str:
    e = node.find(tag)
    return (e.text or "").strip() if e is not None else ""


def fetch_terms(date: str) -> dict[str, str]:
    """val1~val16 이 각각 어느 만기인지 돌려준다."""
    dto = (f"<BISBndSrtPrcDayDTO><standardDt>{date}</standardDt>"
           f"<applyGbCd>C00</applyGbCd></BISBndSrtPrcDayDTO>")
    root = _post("getHeadList", dto)
    rows = root.iter("BISBndSrtPrcDayDTO")
    return {f"val{i}": _text(n, "remainTrmCtgy") for i, n in enumerate(rows, start=1)}


def fetch_rows(date: str) -> list[dict]:
    """조회일의 시가평가수익률 본표를 돌려준다. 휴장일이면 빈 리스트."""
    vals = "".join(f"<{k}>{v}</{k}>" for k, v in AGENCIES.items())
    dto = (f"<BISBndSrtPrcDayDTO><standardDt>{date}</standardDt>"
           f"<reportCompCd>{COMP_AVG}</reportCompCd><applyGbCd>C00</applyGbCd>"
           f"{vals}</BISBndSrtPrcDayDTO>")
    root = _post("selectDay", dto)
    out = []
    for n in root.iter("BISBndSrtPrcDayDTO"):
        cat = _text(n, "largeCategoryMrk")
        if not cat:
            continue
        row = {"종류": cat, "종류명": _text(n, "typeNmMrk"), "신용등급": _text(n, "creditRnkMrk")}
        for i in range(1, 17):
            row[f"val{i}"] = _text(n, f"val{i}")
        out.append(row)
    return out


def last_business_day(base: dt.date | None = None, max_back: int = 15) -> tuple[str, list[dict]]:
    """조회일을 하루씩 앞으로 물리며 데이터가 있는 날을 찾는다.

    주말과 공휴일을 따로 계산하지 않는다. 데이터가 실제로 있는 날이 영업일이므로
    공휴일 달력을 관리할 필요가 없다.
    """
    d = base or dt.date.today()
    for _ in range(max_back):
        key = d.strftime("%Y%m%d")
        rows = fetch_rows(key)
        if rows:
            return key, rows
        d -= dt.timedelta(days=1)
    raise SystemExit(f"{max_back}일을 거슬러 봐도 데이터가 없습니다. 조회 조건을 확인하세요.")


def main() -> None:
    p = argparse.ArgumentParser(allow_abbrev=False, description="KOFIA 채권시가평가수익률 조회")
    p.add_argument("--date", "--평가기준일", dest="date",
                   help="조회일 = 평가기준일 T YYYY-MM-DD(재무기준일이 아니다). 생략하면 --가정 의 평가기준일, 그것도 없으면 최근 영업일")
    p.add_argument("--가정", default=None, help="가정 파일 — --date 를 비우면 기준일.py 로 평가기준일 T 를 푼다")
    p.add_argument("--grade", default="BBB+", help="신용등급 (기본 BBB+)")
    p.add_argument("--term", default="10년", help="만기 (기본 10년)")
    p.add_argument("--type", default="회사채 I(공모사채)", help="채권 종류")
    p.add_argument("--guarantee", default="무보증", help="보증 구분")
    p.add_argument("--gov", action="store_true",
                   help="국고채 수익률(무위험이자율). --grade 를 무시한다")
    p.add_argument("--all", action="store_true", help="해당 종류의 등급 전체를 표로 출력")
    p.add_argument("--out", default=None,
                   help="저장할 CSV 파일명. 생략하면 조회 조건과 기준일로 이름을 짓는다")
    a = p.parse_args()
    if a.가정:
        import os as _os                                           # noqa: PLC0415
        sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
        import 기준일인자 as _기인                              # noqa: PLC0415 — 날짜 둘(2026-10-25): 시장 쪽은 T
        a.date = _기인.풀기(a.date, a.가정, _기인.평가, 인자="--date")

    if a.out is None:                 # 파일명에 조회 조건을 담는다. 덮어쓰기로 내용과 이름이 어긋나는 것을 막는다
        who = "gov" if a.gov else a.grade.replace("+", "p").replace("-", "m")
        a.out = "kofia_%s_%s_%s.csv" % (who, a.term, (a.date or "latest"))

    if a.date:
        key = dt.datetime.strptime(a.date, "%Y-%m-%d").strftime("%Y%m%d")
        rows = fetch_rows(key)
        if not rows:
            key, rows = last_business_day(dt.datetime.strptime(a.date, "%Y-%m-%d").date())
            print(f"[알림] 지정일은 휴장일입니다. 직전 영업일 {key}로 조회했습니다.")
    else:
        key, rows = last_business_day()

    terms = fetch_terms(key)
    col = next((c for c, t in terms.items() if t == a.term), None)
    if col is None:
        raise SystemExit(f"만기 '{a.term}'을 찾을 수 없습니다. 가능한 값: {sorted(set(terms.values()))}")

    shown = dt.datetime.strptime(key, "%Y%m%d").strftime("%Y-%m-%d")

    if a.gov:                       # 무위험이자율 — 같은 표의 국채 줄에서 뽑는다
        g = next((r for r in rows if r["종류"] == "국채" and r["종류명"] == "국고채권"), None)
        if g is None or not g[col]:
            raise SystemExit(f"{shown} 국고채 {a.term} 수익률이 표에 없습니다.")
        print()
        print(f"조회일 {shown} / 국고채 {a.term} / 평가사 평균(5개사)")
        print(f"수익률: {g[col]} %")
        print("출처: 금융투자협회 채권정보센터 시가평가수익률, 평가사 평균 5개사")
        with open(a.out, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["조회일", "종류", "만기", "수익률(%)", "출처"])
            w.writerow([shown, "국고채", a.term, g[col],
                        "금융투자협회 시가평가, 평가사 평균 5개사"])
        print(f"저장: {a.out}")
        return

    target = [r for r in rows if r["종류"] == a.type and r["종류명"] == a.guarantee]

    print(f"\n조회일 {shown} / {a.type} - {a.guarantee} / 평가사 평균(5개사)")
    print("-" * 52)

    if a.all:
        print(f"{'등급':<8}{a.term:>10}")
        for r in target:
            v = r[col]
            print(f"{r['신용등급']:<8}{(v or '-'):>10}")
        print("-" * 52)

    hit = next((r for r in target if r["신용등급"] == a.grade), None)
    if hit is None:
        have = [r["신용등급"] for r in target]
        msg = (f"등급 '{a.grade}'을 찾을 수 없습니다. 있는 등급: {have}")
        if a.grade[:2] in ("BB", "B0", "B+", "B-", "CC", "C0", "D0"):
            msg += (
                    " "
                    "투기등급은 금융투자협회가 시가평가를 내지 않습니다. BBB- 가 바닥입니다. "
                    " "
                    "다모다란 등급별 스프레드 표로 가서 국고채 + 스프레드로 세우세요.")
        raise SystemExit(msg)
    yld = hit[col]
    if not yld:
        raise SystemExit(f"{a.grade} {a.term} 수익률이 공시되지 않았습니다.")

    print(f"{a.grade} {a.term} 수익률: {yld} %")

    with open(a.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["조회일", "종류", "보증구분", "신용등급", "만기", "수익률(%)"])
        w.writerow([shown, a.type, a.guarantee, a.grade, a.term, yld])
    print(f"저장: {a.out}")


if __name__ == "__main__":
    sys.exit(main())

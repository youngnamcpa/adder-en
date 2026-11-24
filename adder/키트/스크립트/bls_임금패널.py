# -*- coding: utf-8 -*-
"""bls_임금패널 — 미국 산업(NAICS 4자리) 평균 연봉 · 임금 증가율 패널을 BLS QCEW 전국 연간 파일로 짓는다(2026-10-24 PU).

왜
  미국 공시에는 회사 단위 총인건비 · 직원 수가 체계적으로 없다(XBRL 직원 수 태깅 2% · 총급여 태그 24% — 연구/패널변수_20261024/P3).
  그래서 1인당 급여(503) · 임금상승률(504)의 같은 집단 띠는 **산업 통계**로 세운다. QCEW 전국 연간 파일
  `data.bls.gov/cew/data/api/{해}/a/area/US000.csv`(키 없음 · 해마다 약 0.85MB)는 전국 · 소유 형태 · NAICS 2~6자리마다 연평균 고용 ·
  1인당 연평균 임금 · 전년 대비 증감률을 준다. 민간(own_code 5)의 4자리(agglvl 16) · 3자리(agglvl 15) 줄을 쓴다(전국 · 소유 형태별 꼴 — 14 는 2자리 부문).

정의 차이(근거 표에 함께 적는다)
  QCEW 임금 = 실업보험 대상 사업체가 낸 총임금(상여 · 행사된 스톡옵션 · 퇴직금 포함, 고용주 부담 연금 · 의료 · 사회보험 제외) ÷ 평균 고용.
  산업 전체(비상장 · 중소 포함)의 평균이라 회사 값이 아니다 — 두 변수 모두 딱지 [유추]. 임금상승률(504)은 정의가 가깝고, 수준(503)은 참고.

SIC → NAICS
  SEC 패널의 SIC(1987)를 통계청 공개 대응표(1987 SIC → 1997 NAICS · `bls_qcew.py` 가 받아 둔 공용 캐시 `naics/`)로 NAICS 4자리 후보에 잇는다.
  후보가 하나면 그대로, 여럿이면 그 해 QCEW 고용으로 가중한다. SEC 가 쓰는 군 단위 코드(「7370」 · 「8200」 처럼 대응표에 없는 4자리)는
  같은 앞 3자리 SIC 들의 후보 합 → 앞 2자리로 물러서고 비고에 적는다. 1997 이후 개정으로 4자리 번호가 사라진 산업은 3자리로 물러선다(`bls_qcew.py` 와 같은 규칙).
  회사의 회계연도에는 **회계연도 가운데 날(끝날 − 182일)이 든 해**의 QCEW 를 붙인다.

사용
  python 스크립트/bls_임금패널.py 받기 [--부터 2014] [--까지 2025] [--씨앗 폴더]     # 없는 해만 · 씨앗 폴더에 US000_{해}.csv 가 있으면 복사
  python 스크립트/bls_임금패널.py 짓기 [--패널 자리]
산출 — `<패널>/qcew/US000_{해}.csv` · `<패널>/상세변수/산업임금.csv`(NAICS4 · 해 · 평균연봉 · 증가율 · 고용 · 자릿수 · SIC) ·
       `<패널>/상세변수/SIC_NAICS대응.csv` · `<패널>/상세변수/산업평균연봉.csv` · `산업임금증가율.csv`(열은 `sec_상세변수` 와 같다) · `목록.json` 의 두 변수.
종료 코드 — 0 통과 · 2 입력오류(QCEW 파일 · 대응표 · 패널 없음). 회사 · 업종 이름은 이 도구에 없다(범용).
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime
import glob
import io
import json
import os
import re
import shutil
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 입력오류  # noqa: E402
import sec_상세변수 as 상  # noqa: E402

주소 = "https://data.bls.gov/cew/data/api/%d/a/area/US000.csv"
변수정의 = {
    "산업평균연봉": {"모델칸": "503(대조)", "딱지": "[유추]", "단위": "통화(달러)/인",
               "정의": "회사 SIC 를 NAICS 4자리에 이은 산업의 1인당 연평균 임금(QCEW 전국 · 민간 · avg_annual_pay — 상여 · 행사 스톡옵션 포함 · 고용주 부담 제외 · "
                       "비상장 포함). 후보 산업이 여럿이면 고용 가중. 회사 값이 아니다 — 수준은 참고"},
    "산업임금증가율": {"모델칸": "504", "딱지": "[유추]", "단위": "비율",
                "정의": "같은 산업의 1인당 연평균 임금 전년 대비 증감률(QCEW oty_avg_annual_pay_pct_chg ÷ 100) · 후보 여럿이면 고용 가중 — 임금상승률(504)의 같은 산업 띠"},
    "산업고용증가율": {"모델칸": "501", "딱지": "[유추]", "단위": "비율",
                "정의": "같은 산업의 연평균 고용 전년 대비 증감률(QCEW oty_annual_avg_emplvl_pct_chg ÷ 100) · 후보 여럿이면 고용 가중 — 인원 증가율(501)의 같은 산업 띠. "
                        "미국 공시에 회사 직원 수가 체계적으로 없어(dei 2% · P3) 산업 고용으로 대신한다 — 회사 값이 아니다(2026-10-24 PN)"},
}


def 자리(패널=None):
    p = 패널 or 상.패널자리기본()
    return {"패널": p, "qcew": os.path.join(p, "qcew"), "상세": os.path.join(p, "상세변수")}


def _수(v):
    try:
        x = float(v)
        return x if x == x else None
    except (TypeError, ValueError):
        return None


# ══════════════════════════════════════════════════════════════════ 받기

def 받기(패널=None, 부터=2014, 까지=None, 씨앗=None):
    자 = 자리(패널)
    os.makedirs(자["qcew"], exist_ok=True)
    까지 = 까지 or (datetime.date.today().year - 1)
    받은, 복사, 없음 = [], [], []
    for y in range(부터, 까지 + 1):
        p = os.path.join(자["qcew"], "US000_%d.csv" % y)
        if os.path.exists(p) and os.path.getsize(p) > 1000:
            continue
        s = os.path.join(씨앗, "US000_%d.csv" % y) if 씨앗 else None
        if s and os.path.exists(s):
            shutil.copyfile(s, p)
            복사.append(y)
            continue
        try:
            import requests                                  # noqa: PLC0415
            r = requests.get(주소 % y, headers={"User-Agent": "Mozilla/5.0 (DCF research; public statistics)"}, timeout=180)
            time.sleep(0.5)
            if r.status_code == 200 and len(r.content) > 1000:
                io.open(p, "wb").write(r.content)
                받은.append(y)
            else:
                없음.append(y)
        except Exception:                                    # noqa: BLE001
            없음.append(y)
    print("QCEW 받기 — 받음 %s · 복사 %s · 없음 %s" % (받은 or "-", 복사 or "-", 없음 or "-"))
    return 통과


# ══════════════════════════════════════════════════════════════════ 짓기

def QCEW읽기(qcew자리):
    """→ {(NAICS, 해): {고용, 평균연봉, 증가율, 자릿수}} — 전국 · 민간 · 4자리(agglvl 16) · 3자리(15) · 공개 줄만."""
    낸 = {}
    for p in sorted(glob.glob(os.path.join(qcew자리, "US000_*.csv"))):
        for r in csv.DictReader(io.open(p, encoding="utf-8-sig")):
            if r.get("area_fips") != "US000" or r.get("own_code") != "5" or r.get("agglvl_code") not in ("15", "16"):
                continue
            if (r.get("disclosure_code") or "").strip() == "N":
                continue
            y = int(r["year"])
            낸[(r["industry_code"], y)] = {"고용": _수(r.get("annual_avg_emplvl")), "평균연봉": _수(r.get("avg_annual_pay")),
                                         "증가율": (lambda v: v / 100.0 if v is not None else None)(_수(r.get("oty_avg_annual_pay_pct_chg")))
                                         if (r.get("oty_disclosure_code") or "").strip() != "N" else None,
                                         "고용증가율": (lambda v: v / 100.0 if v is not None else None)(_수(r.get("oty_annual_avg_emplvl_pct_chg")))
                                         if (r.get("oty_disclosure_code") or "").strip() != "N" else None,
                                         "자릿수": 4 if r["agglvl_code"] == "16" else 3}
    return 낸


def 대응읽기():
    import bls_qcew as Q                                     # noqa: PLC0415 — 읽기만
    p = os.path.join(Q.공용뿌리(), "naics", "1987_SIC_to_1997_NAICS.xls")
    if not os.path.exists(p):
        p = Q.대응표받기({"User-Agent": "Mozilla/5.0 (DCF research; public statistics)"})
    if not p:
        return None
    return Q.대응읽기(p)


def sic대응찾기(sic, 대응):
    """SIC 4자리 → (NAICS 4자리 후보 목록, 방식). 4자리 대응이 없으면 같은 앞 3자리 SIC 들의 후보 합 → 앞 2자리."""
    목 = 대응.get(sic, [])
    if 목:
        return sorted({n[:4] for n, _t, _p in 목 if len(n) >= 4}), "SIC"
    for k, 이름 in ((3, "SIC 앞 3자리 군"), (2, "SIC 앞 2자리 군")):
        모 = {n[:4] for s, 목2 in 대응.items() if s[:k] == sic[:k] for n, _t, _p in 목2 if len(n) >= 4}
        if 모:
            return sorted(모), 이름
    return [], "없음"


def 산업고르기(후보4, 해, Q):
    """NAICS 4자리 후보들 → 그 해 쓸 산업 [(코드, 고용, 평균연봉, 증가율, 자릿수)] — 4자리가 없으면 3자리로 물러선다(같은 3자리는 한 번)."""
    낸, 본 = [], set()
    for n4 in 후보4:
        x = Q.get((n4, 해))
        if x and x["고용"]:
            if n4 not in 본:
                낸.append((n4, x["고용"], x["평균연봉"], x["증가율"], 4))
                본.add(n4)
            continue
        n3 = n4[:3]
        x = Q.get((n3, 해))
        if x and x["고용"] and n3 not in 본:
            낸.append((n3, x["고용"], x["평균연봉"], x["증가율"], 3))
            본.add(n3)
    return 낸


def 짓기(패널=None, 조용=False):
    자 = 자리(패널)
    Q = QCEW읽기(자["qcew"])
    if not Q:
        print("입력오류 — QCEW 파일이 없다(%s) — `bls_임금패널.py 받기`" % 자["qcew"])
        return 입력오류, None
    대응 = 대응읽기()
    if not 대응:
        print("입력오류 — SIC → NAICS 대응표가 없다(공용 캐시 naics/)")
        return 입력오류, None
    sic표 = {}
    산 = os.path.join(자["패널"], "산업분류.csv")
    if os.path.exists(산):
        for r in csv.DictReader(io.open(산, encoding="utf-8-sig")):
            sic표[(r.get("고유번호") or "").zfill(10)] = (r.get("산업분류코드") or "").strip()
    fsds = 상.FSDS읽기(자["패널"])
    if not fsds:
        print("입력오류 — 미국 패널(주요계정_*.csv)이 없다(%s)" % 자["패널"])
        return 입력오류, None
    os.makedirs(자["상세"], exist_ok=True)
    # SIC → NAICS 4자리 후보(4자리 대응이 없으면 같은 앞 3자리 군 → 앞 2자리 군으로 물러선다 — SEC 는 「7370」 처럼 군 단위 코드를 쓴다)
    sic후보, sic방식 = {}, {}
    for sic in sorted({s for s in sic표.values() if s}):
        목, 방 = sic대응찾기(sic.zfill(4), 대응)
        sic후보[sic], sic방식[sic] = 목, 방
    with io.open(os.path.join(자["상세"], "SIC_NAICS대응.csv"), "w", encoding="utf-8", newline="") as w:
        c = csv.writer(w)
        c.writerow(["SIC", "NAICS4후보", "방식", "비고"])
        for sic, 목 in sorted(sic후보.items()):
            c.writerow([sic, " ".join(목), ("하나" if len(목) == 1 else ("여럿 — 고용 가중" if 목 else "없음")) + ("" if sic방식[sic] == "SIC" else " · " + sic방식[sic]),
                        "" if 목 else "대응표에 그 SIC · 군이 없음(비영업 · 기타 코드)"])
    # 산업임금.csv
    naics_sic = collections.defaultdict(set)
    for sic, 목 in sic후보.items():
        for n4 in 목:
            naics_sic[n4].add(sic)
            naics_sic[n4[:3]].add(sic)
    with io.open(os.path.join(자["상세"], "산업임금.csv"), "w", encoding="utf-8", newline="") as w:
        c = csv.writer(w)
        c.writerow(["NAICS4", "해", "평균연봉", "증가율", "고용", "자릿수", "SIC"])
        for (n, y), x in sorted(Q.items()):
            c.writerow([n, y, x["평균연봉"], "" if x["증가율"] is None else round(x["증가율"], 6), x["고용"], x["자릿수"], " ".join(sorted(naics_sic.get(n, ())))])
    # 회사 × 회계연도
    모음 = {"산업평균연봉": [], "산업임금증가율": [], "산업고용증가율": []}
    못 = collections.Counter()
    for cik, 행들 in fsds.items():
        sic = sic표.get(cik)
        후보 = sic후보.get(sic) if sic else None
        if not 후보:
            못["SIC 없음 · 대응 없음"] += len(행들)
            continue
        for r in 행들:
            가운데 = 상._날(r["끝날"]) - datetime.timedelta(days=182)
            해 = 가운데.year
            산들 = 산업고르기(후보, 해, Q)
            if not 산들:
                못["그 해 QCEW 없음"] += 1
                continue
            w합 = sum(x[1] for x in 산들)
            코드 = "·".join("%s(%d자리)" % (x[0], x[4]) for x in 산들)
            비고 = "SIC %s →%s NAICS %s%s · QCEW %d(회계연도 가운데 날의 해)" % (sic, "" if sic방식[sic] == "SIC" else " (%s)" % sic방식[sic],
                                                                         " · ".join(후보), " · 고용 가중" if len(산들) > 1 else "", 해)
            pay = [(x[1], x[2]) for x in 산들 if x[2]]
            if pay:
                s = sum(a * b for a, b in pay)
                ww = sum(a for a, _b in pay)
                모음["산업평균연봉"].append({"CIK": cik, "회계연도": r["fy"], "값": round(s / ww, 2), "분자": round(s, 2), "분모": ww,
                                       "단위": 변수정의["산업평균연봉"]["단위"], "기준": "산업(NAICS)", "원천": "QCEW US000 own5 %s" % 코드,
                                       "기간끝": r["끝날"], "딱지": "[유추]", "비고": 비고})
            g = [(x[1], x[3]) for x in 산들 if x[3] is not None]
            if g:
                s = sum(a * b for a, b in g)
                ww = sum(a for a, _b in g)
                모음["산업임금증가율"].append({"CIK": cik, "회계연도": r["fy"], "값": round(s / ww, 6), "분자": round(s, 4), "분모": ww,
                                        "단위": 변수정의["산업임금증가율"]["단위"], "기준": "산업(NAICS)", "원천": "QCEW US000 own5 %s" % 코드,
                                        "기간끝": r["끝날"], "딱지": "[유추]", "비고": 비고})
            ge = [(x[0], x[1]) for x in 산들 if Q.get((x[0], 해), {}).get("고용증가율") is not None]
            if ge:
                s = sum(b * Q[(a, 해)]["고용증가율"] for a, b in ge)
                ww = sum(b for _a, b in ge)
                모음["산업고용증가율"].append({"CIK": cik, "회계연도": r["fy"], "값": round(s / ww, 6), "분자": round(s, 4), "분모": ww,
                                        "단위": 변수정의["산업고용증가율"]["단위"], "기준": "산업(NAICS)", "원천": "QCEW US000 own5 %s · 고용 증감률" % 코드,
                                        "기간끝": r["끝날"], "딱지": "[유추]", "비고": 비고})
            _ = w합
    for 변, 행들 in 모음.items():
        p = os.path.join(자["상세"], "%s.csv" % 변)
        with io.open(p + ".part", "w", encoding="utf-8", newline="") as w:
            c = csv.DictWriter(w, fieldnames=상.열머리)
            c.writeheader()
            c.writerows(sorted(행들, key=lambda x: (x["CIK"], x["회계연도"])))
        os.replace(p + ".part", p)
    목 = 목록더하기(자, fsds, 모음, Q, sic후보, 못)
    if not 조용:
        print("짓기 끝 — 산업평균연봉 %d · 산업임금증가율 %d · 못 붙임 %s" % (len(모음["산업평균연봉"]), len(모음["산업임금증가율"]), dict(못)))
    return 통과, 목


def 목록더하기(자, fsds, 모음, Q, sic후보, 못):
    p = os.path.join(자["상세"], "목록.json")
    try:
        목 = json.load(io.open(p, encoding="utf-8"))
    except Exception:                                        # noqa: BLE001
        목 = {"형식": 상.형식, "열": 상.열머리, "변수": {}}
    분모 = 상.분모셈(fsds)
    큰 = {(cik, r["fy"]) for cik, 행들 in fsds.items() for r in 행들 if r["매출"] and r["매출"] >= 1e7}
    해들 = sorted({y for (_n, y) in Q})
    for 변, 정 in 변수정의.items():
        행들 = 모음[변]
        해별 = collections.Counter(r["회계연도"] for r in 행들)
        큰해별 = collections.Counter(r["회계연도"] for r in 행들 if (r["CIK"], r["회계연도"]) in 큰)
        목.setdefault("변수", {})[변] = dict(정, **{"해별회사수": {str(y): 해별[y] for y in sorted(해별)},
                                             "커버리지": {str(y): round(큰해별.get(y, 0) / 분모[y], 4) for y in sorted(분모) if 분모[y] >= 100},
                                             "커버리지_2010_2025": round(sum(큰해별.get(y, 0) for y in range(2010, 2026))
                                                                       / max(1, sum(분모.get(y, 0) for y in range(2010, 2026))), 4),
                                             "같음비중": 0.0, "행수": len(행들), "파일": "%s.csv" % 변, "도구": "bls_임금패널.py",
                                             "QCEW해": [해들[0], 해들[-1]] if 해들 else None})
    목.setdefault("갱신", {})["QCEW"] = {"해": [해들[0], 해들[-1]] if 해들 else None, "SIC수": len(sic후보),
                                        "SIC하나": sum(1 for v in sic후보.values() if len(v) == 1),
                                        "SIC여럿": sum(1 for v in sic후보.values() if len(v) > 1), "SIC없음": sum(1 for v in sic후보.values() if not v),
                                        "못붙임": dict(못), "만든날": datetime.date.today().isoformat()}
    목["만든날"] = datetime.date.today().isoformat()
    io.open(p + ".part", "w", encoding="utf-8").write(json.dumps(목, ensure_ascii=False, indent=1))
    os.replace(p + ".part", p)
    return 목


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="미국 산업 임금 패널(QCEW 전국 연간 — NAICS 4자리 평균 연봉 · 증가율)")
    ap.add_argument("명령", choices=["받기", "짓기"])
    ap.add_argument("--패널")
    ap.add_argument("--부터", type=int, default=2014)
    ap.add_argument("--까지", type=int)
    ap.add_argument("--씨앗")
    a = ap.parse_args(argv)
    if a.명령 == "받기":
        return 받기(a.패널, a.부터, a.까지, a.씨앗)
    return 짓기(a.패널)[0]


if __name__ == "__main__":
    sys.exit(main())

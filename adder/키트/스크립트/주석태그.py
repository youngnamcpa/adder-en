# -*- coding: utf-8 -*-
"""주석 태그 — XBRL 원본의 주석 태그 값(성격별 비용 · 유형자산 변동 · 인건비)을 받아 A3 텍스트 추출값과 대사한다 (제안 E · 2026-10-22 신설).

무엇을 하나
  OpenDART `fnlttXbrl.xml`(접수번호 · 보고서코드 → XBRL 원본 ZIP)의 인스턴스(`*.xbrl`)에는 본표뿐 아니라 **주석의 수치**가 태그로 들어 있다
  (2026-10-22 실측 — ifrs-full:RawMaterials · WagesAndSalaries · DepreciationExpense · ExpenseByNature, 유형자산 변동 AdditionsOtherThanThroughBusinessCombinations …
  · DepreciationPropertyPlantAndEquipment · Disposals … 가 ClassesOfPropertyPlantAndEquipmentAxis 멤버로, dart-gcd:NumberOfEmployee). 2025FY(2026년 3월 제출)부터
  비금융 전 상장사가 주석을 태그로 낸다. A3 동인원천은 같은 항목을 사업보고서 **텍스트**에서 읽는다 — 표 읽기 오류를 거르는 규칙(E 판정 ②)이 있을 만큼 오차가 있다.
  이 도구는 태그 값을 받아 A3 값(`_raw/동인원천.json` 성격별비용.항목 · 유형자산.종류별 · 인건비)과 **같은 기간 · 같은 단위로 대사**하고, 1% 넘게 다르면 경보,
  태그에는 있는데 원천에 없는 항목은 참고로 낸다. 값을 고치지 않는다 — 모순이면 사람이 원문으로 덮는다(모순 장부 규칙).

사용
  python 스크립트/주석태그.py 가정.json [--접수번호 …] [--보고서 11011] [--낼 _raw/주석태그.json]
읽는 것 — OPENDART_API_KEY · 가정(메타.평가기준일 · 금액단위 · 환산배율) · 가정 곁 `_raw/dart_기업개황.json`(corp_code — 접수번호를 안 주면 list API) ·
          `_raw/동인원천.json`(A3 — 있으면 대사 · 없으면 태그 값만) · XBRL ZIP 캐시 `_raw/xbrl/{접수번호}.zip`
내는 것 — {형식 · 만든날 · 입력 · 출처 · 확인상태 「확인완료(XBRL 태그)」 · 태그수 · 기간 · 성격별[{태그 · 라벨 · 값{기간: 원}}] · 유형자산변동[{구분 · 취득 · 상각 · 처분 · 기말}] ·
          인건비{급여 · 종업원수} · 대사[{항목 · 기간 · 태그값 · 원천값 · 차이율 · 판정}] · 신호[]}
종료 코드 — 0 통과(경보가 있어도) · 2 입력오류(키 없음 · 접수번호 못 찾음 · ZIP 깨짐).
회사 · 업종 이름은 이 도구에 없다(범용). 표준 라이브러리 + requests.
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import re
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass
여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 입력오류  # noqa: E402

성격태그 = ["RawMaterialsAndConsumablesUsed", "RawMaterials", "ChangesInInventoriesOfFinishedGoodsAndWorkInProgress", "EmployeeBenefitsExpense", "WagesAndSalaries",
         "DepreciationAndAmortisationExpense", "DepreciationExpense", "AmortisationExpense", "OtherExpenseByNature", "ExpenseByNature", "ProfessionalFeesExpense",
         "TransportationExpense", "AdvertisingExpense", "ResearchAndDevelopmentExpense", "UtilitiesExpense", "RepairsAndMaintenanceExpense", "RentalExpense", "CostOfSales", "Revenue"]
유형자산태그 = {"취득": "AdditionsOtherThanThroughBusinessCombinationsPropertyPlantAndEquipment", "상각": "DepreciationPropertyPlantAndEquipment",
          "처분": "DisposalsPropertyPlantAndEquipment", "대체": "IncreaseDecreaseThroughTransfersPropertyPlantAndEquipment", "기말": "PropertyPlantAndEquipment"}
PPE축 = "ClassesOfPropertyPlantAndEquipmentAxis"
연결축 = "ConsolidatedAndSeparateFinancialStatementsAxis"



def _재무기준일(가정):
    """메타 날짜를 `기준일.py` 로 푼다(날짜 둘 — 2026-10-25). 못 풀면 None."""
    try:
        import 기준일 as _B                                   # noqa: PLC0415
        return _B.재무기준일(가정).isoformat()
    except Exception:                                         # noqa: BLE001
        return None

def 접수번호찾기(corp_code, 기준일, key):
    import requests                                      # noqa: PLC0415
    y = int(기준일[:4])
    for 해 in (y, y - 1):
        r = requests.get("https://opendart.fss.or.kr/api/list.json", params={"crtfc_key": key, "corp_code": corp_code, "bgn_de": "%d0101" % (해 + 1), "end_de": "%d1231" % (해 + 1),
                                                                            "pblntf_detail_ty": "A001", "page_count": 50}, timeout=60)
        j = r.json() if r.status_code == 200 else {}
        후 = sorted([x for x in j.get("list", []) if "사업보고서" in x.get("report_nm", "")], key=lambda x: x["rcept_dt"])
        if 후:
            return 후[-1]["rcept_no"]
    return None


def xbrl받기(접수번호, 보고서, 곁, key):
    import requests                                      # noqa: PLC0415
    d = os.path.join(곁, "_raw", "xbrl")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "%s.zip" % 접수번호)
    if os.path.exists(p) and os.path.getsize(p) > 100:
        return p, "캐시"
    r = requests.get("https://opendart.fss.or.kr/api/fnlttXbrl.xml", params={"crtfc_key": key, "rcept_no": 접수번호, "reprt_code": 보고서}, timeout=180)
    if r.status_code != 200 or r.content[:2] != b"PK":
        return None, "fnlttXbrl 응답 %s — %s" % (r.status_code, r.text[:120] if r.content[:2] != b"PK" else "")
    io.open(p, "wb").write(r.content)
    return p, "받음"


def 인스턴스읽기(zp):
    """(사실[{접두 · 태그 · 문맥 · 단위 · 값}], 문맥{id: {끝 · 시작 · 차원{축: 멤버}}}, 라벨{접두:태그 → 한글})."""
    with zipfile.ZipFile(zp) as z:
        names = z.namelist()
        inst = [n for n in names if n.endswith(".xbrl")] or [n for n in names if n.endswith(".xml") and not re.search(r"_(lab|pre|cal|def)", n)]
        if not inst:
            return None, None, None
        x = z.read(inst[0]).decode("utf-8", "replace")
        라벨 = {}
        for n in names:
            if n.endswith("lab-ko.xml"):
                lab = z.read(n).decode("utf-8", "replace")
                for m in re.finditer(r'<link:label[^>]*xlink:label="lab_([^"]+?)(?:_\d+)?"[^>]*>([^<]+)</link:label>', lab):
                    k = m.group(1).replace("_", ":", 1)
                    라벨.setdefault(k, m.group(2).strip())
    문맥 = {}
    for m in re.finditer(r'<xbrli:context id="([^"]+)">(.*?)</xbrli:context>', x, re.S):
        cid, 몸 = m.group(1), m.group(2)
        끝 = (re.search(r"<xbrli:(?:endDate|instant)>([^<]+)<", 몸) or [None, None])[1]
        시작 = (re.search(r"<xbrli:startDate>([^<]+)<", 몸) or [None, None])[1]
        차원 = dict(re.findall(r'<xbrldi:explicitMember dimension="([^"]+)">([^<]+)<', 몸))
        문맥[cid] = {"끝": 끝, "시작": 시작, "차원": {k.split(":")[-1]: v for k, v in 차원.items()}}
    사실 = []
    for m in re.finditer(r"<([a-zA-Z0-9-]+):([A-Za-z0-9_.]+)\s+([^>]*?)contextRef=\"([^\"]+)\"([^>]*)>([^<]*)<", x):
        접두, 태그, 앞, cid, 뒤, 값 = m.groups()
        u = re.search(r'unitRef="([^"]+)"', 앞 + 뒤)
        dec = re.search(r'decimals="([^"]+)"', 앞 + 뒤)
        v = 값.strip().replace(",", "")
        try:
            fv = float(v)
        except ValueError:
            continue
        사실.append({"접두": 접두, "태그": 태그, "문맥": cid, "단위": u.group(1) if u else None, "값": fv, "decimals": dec.group(1) if dec else None})
    return 사실, 문맥, 라벨


def 기간ID(ctx, 결산월=12):
    """문맥 → 엔진 기간 ID(FY2025A · 1H26A …). 기간형(시작~끝)이 12달이면 FY, 6달이면 1H, 3달이면 Q. 시점형은 끝 해 FY."""
    끝 = ctx.get("끝") or ""
    if not 끝:
        return None
    y = int(끝[:4])
    if not ctx.get("시작"):
        return "FY%dA" % y
    sm, em = int(ctx["시작"][5:7]), int(끝[5:7])
    sy = int(ctx["시작"][:4])
    달 = (y - sy) * 12 + (em - sm) + 1
    if 달 >= 11:
        return "FY%dA" % y
    if 달 in (6, 7):
        return "1H%02dA" % (y % 100)
    if 달 in (3, 4):
        return "%dQ%02dA" % ((em - 1) // 3 + 1, y % 100)
    return None


def 분석(가정, 가정경로, 접수번호=None, 보고서="11011"):
    key = os.environ.get("OPENDART_API_KEY")
    if not key:
        return None, "환경변수 OPENDART_API_KEY 가 없다"
    곁 = os.path.dirname(os.path.abspath(가정경로))
    메타 = 가정.get("메타") or {}
    if not 접수번호:
        p = os.path.join(곁, "_raw", "dart_기업개황.json")
        corp = None
        if os.path.exists(p):
            try:
                corp = (json.load(io.open(p, encoding="utf-8")).get("corp_code") or "").strip()
            except (OSError, ValueError):
                corp = None
        if not corp:
            return None, "접수번호도 없고 _raw/dart_기업개황.json 도 없다 — --접수번호"
        접수번호 = 접수번호찾기(corp, _재무기준일(가정) or datetime.date.today().isoformat(), key)   # 재무 주석 — 재무기준일(F) 보고서(2026-10-25 날짜 둘)
        if not 접수번호:
            return None, "사업보고서 접수번호를 못 찾았다"
    zp, 어떻게 = xbrl받기(접수번호, 보고서, 곁, key)
    if not zp:
        return None, 어떻게
    사실, 문맥, 라벨 = 인스턴스읽기(zp)
    if 사실 is None:
        return None, "ZIP 안에 인스턴스가 없다"
    배율 = float(메타.get("환산배율") or 1.0)        # 가정 · A3 금액단위 → 원
    신호 = []

    def 신(종류, 대상, 값, 문턱, 글, 등급="참고"):
        신호.append({"출처": "주석태그", "종류": 종류, "대상": 대상, "값": 값, "문턱": 문턱, "글": 글, "등급": 등급})

    def 연결인가(ctx):
        d = ctx.get("차원") or {}
        m = d.get(연결축)
        return (m is None) or m.endswith("ConsolidatedMember")

    # 성격별 비용 — 비차원(연결 축만 허용) · 기간형
    성격 = {}
    for f in 사실:
        if f["태그"] not in 성격태그 or f["접두"] not in ("ifrs-full", "dart"):
            continue
        ctx = 문맥.get(f["문맥"]) or {}
        차원 = {k: v for k, v in (ctx.get("차원") or {}).items() if k != 연결축}
        if 차원 or not 연결인가(ctx):
            continue
        기간 = 기간ID(ctx)
        if not 기간:
            continue
        k = "%s:%s" % (f["접두"], f["태그"])
        성격.setdefault(k, {"태그": k, "라벨": 라벨.get(k) or f["태그"], "값": {}})["값"][기간] = f["값"]
    # 유형자산 변동 — 종류별 멤버
    변동 = {}
    for f in 사실:
        if f["태그"] not in 유형자산태그.values() or f["접두"] != "ifrs-full":
            continue
        ctx = 문맥.get(f["문맥"]) or {}
        if not 연결인가(ctx):
            continue
        d = {k: v for k, v in (ctx.get("차원") or {}).items() if k != 연결축}
        종류 = d.get(PPE축, "합계")
        if any(k not in (PPE축,) for k in d):
            continue                                     # 다른 축(총장부 · 누계 상각)이 붙은 값은 뺀다
        기간 = 기간ID(ctx)
        if not 기간:
            continue
        이름 = 라벨.get(종류.replace("Member", "")) or 종류.split(":")[-1].replace("Member", "")
        항 = next(k for k, v in 유형자산태그.items() if v == f["태그"])
        변동.setdefault(이름, {"구분": 이름, "멤버": 종류}).setdefault(항, {})[기간] = f["값"]
    인건비 = {}
    for f in 사실:
        if f["태그"] in ("NumberOfEmployee", "WagesAndSalaries", "EmployeeBenefitsExpense") and 연결인가(문맥.get(f["문맥"]) or {}) and not {k for k in (문맥.get(f["문맥"]) or {}).get("차원", {}) if k != 연결축}:
            기간 = 기간ID(문맥.get(f["문맥"]) or {})
            if 기간:
                인건비.setdefault(f["태그"], {})[기간] = f["값"]
    # 대사 — A3 동인원천
    대사 = []
    p = os.path.join(곁, "_raw", "동인원천.json")
    원천 = None
    if os.path.exists(p):
        try:
            원천 = json.load(io.open(p, encoding="utf-8"))
        except (OSError, ValueError):
            원천 = None
    if 원천:
        항목 = ((원천.get("성격별비용") or {}).get("항목") or {})
        단위 = 원천.get("단위") or 메타.get("금액단위")
        A3배율 = 배율
        def 정규(s):
            return re.sub(r"[\s,·및의등]", "", s or "")
        for k, x in 성격.items():
            라 = 정규(x["라벨"])
            짝 = None
            for 이름 in 항목:
                n = 정규(이름)
                if n and (n in 라 or 라 in n or (("원재료" in n and "원재료" in 라) or ("종업원" in n and ("종업원" in 라 or "급여" in 라)) or ("감가상각" in n and "감가상각" in 라))):
                    짝 = 이름
                    break
            if not 짝:
                대사.append({"항목": x["라벨"], "태그": k, "판정": "원천에 없음", "기간": None, "태그값": None, "원천값": None, "차이율": None})
                continue
            for 기간, v in x["값"].items():
                o = (항목.get(짝) or {}).get(기간)
                if o is None:
                    continue
                o원 = o * A3배율
                차 = (v - o원) / o원 if o원 else None
                판 = "일치" if (차 is not None and abs(차) <= 0.01) else ("다름" if 차 is not None else "비교 불가")
                대사.append({"항목": x["라벨"], "태그": k, "원천항목": 짝, "기간": 기간, "태그값": v, "원천값": o원, "차이율": round(차, 4) if 차 is not None else None, "판정": 판})
        다름 = [d for d in 대사 if d["판정"] == "다름"]
        for d in 다름:
            신("태그 값과 원천 추출값이 다르다", "%s %s" % (d["항목"], d["기간"]), d["차이율"], 0.01,
              "%s(%s)의 XBRL 태그 값 %.0f 과 A3 원천 값 %.0f 이 %.1f%% 다르다 — 어느 쪽이 맞는지 고르지 않는다. 원문으로 덮고 모순 장부에 올린다(단위 %s · 배율 %.0f)"
              % (d["항목"], d["기간"], d["태그값"], d["원천값"], d["차이율"] * 100, 단위, A3배율), "경보")
        없 = [d["항목"] for d in 대사 if d["판정"] == "원천에 없음"]
        if 없:
            신("태그에는 있는데 원천에 없는 항목", " · ".join(없)[:200], len(없), None,
              "성격별 비용 태그 %d개가 A3 성격별비용.항목에 짝이 없다 — 이름이 다르거나 A3 가 못 읽은 줄이다" % len(없))
    else:
        신("재료 없음", "동인원천.json", None, None, "가정 곁 _raw/동인원천.json 이 없어 태그 값만 낸다(대사 없음)")
    낸 = {"형식": "주석태그 1", "만든날": datetime.date.today().isoformat(), "입력": {"가정": os.path.abspath(가정경로), "접수번호": 접수번호, "보고서": 보고서, "xbrl": zp, "받기": 어떻게},
         "출처": "OpenDART fnlttXbrl.xml(접수번호 %s · 보고서 %s) 인스턴스" % (접수번호, 보고서), "확인상태": "확인완료(XBRL 태그 — 제출인이 붙인 값 그대로)",
         "태그수": len({(f["접두"], f["태그"]) for f in 사실}), "문맥수": len(문맥), "성격별": sorted(성격.values(), key=lambda x: x["태그"]),
         "유형자산변동": sorted(변동.values(), key=lambda x: x["구분"]), "인건비": 인건비, "대사": 대사, "신호": 신호}
    return 낸, ""


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="XBRL 주석 태그 — 성격별 비용 · 유형자산 변동 · 인건비를 받아 A3 추출값과 대사")
    ap.add_argument("가정")
    ap.add_argument("--접수번호")
    ap.add_argument("--보고서", default="11011", help="11011 사업보고서 · 11012 반기 · 11013 1분기 · 11014 3분기")
    ap.add_argument("--낼")
    a = ap.parse_args()
    try:
        가정 = json.load(io.open(a.가정, encoding="utf-8"))
    except (OSError, ValueError) as e:
        print("가정 파일을 못 읽었다 — %s" % e)
        return 입력오류
    낸, 까 = 분석(가정, a.가정, a.접수번호, a.보고서)
    if 낸 is None:
        print("입력오류 — %s" % 까)
        return 입력오류
    p = a.낼 or os.path.join(os.path.dirname(os.path.abspath(a.가정)), "_raw", "주석태그.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, "w", encoding="utf-8").write(json.dumps(낸, ensure_ascii=False, indent=1, default=str))
    print("주석 태그 — 접수 %s · 태그 %d종 · 성격별 %d · 유형자산 구분 %d · 대사 %d(다름 %d) · 신호 %d"
          % (낸["입력"]["접수번호"], 낸["태그수"], len(낸["성격별"]), len(낸["유형자산변동"]), len(낸["대사"]), sum(1 for d in 낸["대사"] if d["판정"] == "다름"), len(낸["신호"])))
    for x in 낸["성격별"][:12]:
        print("   %-48s %s" % (x["라벨"][:46], {k: round(v / 1e6) for k, v in sorted(x["값"].items())}))
    for s in 낸["신호"][:8]:
        print("   · [%s] %s — %s: %s" % (s["등급"], s["종류"], s["대상"], s["글"][:150]))
    print("→ %s" % p)
    return 통과


if __name__ == "__main__":
    sys.exit(main())

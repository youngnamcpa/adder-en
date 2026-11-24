# -*- coding: utf-8 -*-
"""전체 재무제표(fnlttSinglAcntAll) 일괄 — **비싼 층**. 핵심 표본 + 예비만 돌린다.

왜 요약본(fnlttMultiAcnt)으로 안 되는가
    요약 주요계정은 열넷뿐이라 **차입금이 없다.** 무차입 베타에는 이자부부채가 필요하고
    그것은 전체 재무제표의 계정 목록에서만 나온다.

여기서 조용히 어긋나는 자리
    - **`fs_div` 칸으로 골라낼 수 없다 — 회신에 그 칸이 아예 없다**(실측).
      「연결로 요청해도 별도가 섞여 온다」는 것은 요약 창구(fnlttMultiAcnt) 이야기다.
      이 창구는 요청한 구분만 오므로 골라낼 필요도, 골라낼 칸도 없다.
      `fs_div` 로 거르는 코드를 넣으면 전부 걸러져 표가 통째로 빈다.
    - **연결재무제표를 아예 안 내는 회사가 있다.** CFS 가 013(자료 없음)이면 OFS 로
      한 번 더 부르고, 어느 쪽을 썼는지 남긴다.
    - **차입금을 「금융부채」 한 줄로 뭉쳐 놓은 회사가 요약 XBRL 의 3분의 1 가까이다.**
      합계가 0으로 나오면 무차입 회사가 아니라 **이름을 못 찾은 것**이다.
      이 스크립트는 0을 그대로 내보내지 않고 `차입금_확인필요` 를 세워 알린다 —
      그때는 그 회사 반기보고서 주석을 열어야 한다.

안전 속도: 2스레드 · 호출 사이 0.6초. 캐시가 있으면 네트워크를 타지 않는다.

**산출 `전체재무_추출.csv` 는 병합된다(펄29)** — 키 (고유번호, 연도, 보고서). CP2 뒤에 CP3 를
돌려도 앞 행이 남는다. 옛 동작(이번 명단분만)은 `--새로`. 자세한 규칙은 `병합쓰기()`.

사용
    python 스크립트/dart_fs_all.py --codes-file 핵심표본.txt --year 2026 --reprt 11012
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import queue
import re
import sys
import threading
import time
import urllib.parse
import urllib.request

API = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
# 2026-10-25 FX4-P — DCF_RUN_ROOT(사슬 `--폴더` 가 넘긴다)면 그 회차에 쓴다 — 본체 경로로 돌려도 본체 _raw 에 쌓지 않게
ROOT = os.environ.get("DCF_RUN_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHEDIR = os.path.join(ROOT, "_raw", "peers", "fs")
PAUSE, THREADS = 0.6, 2

# 이자부부채로 세는 계정. **정규식으로 넓게 잡고 무엇이 잡혔는지 반드시 남긴다.**
# 2026-10-25 FX4-P — 「차입부채」(유동 · 비유동 차입부채)는 이름 그대로 차입이다 — 종전에는 뭉침 후보로만 적어 D = 0 이 됐다(C2 다시 셈 3-1)
차입패턴 = re.compile(
    r"(단기차입금|장기차입금|유동성장기|사채|전환사채|신주인수권부사채|교환사채"
    r"|리스부채|금융리스부채|차입금|차입부채|장기미지급금\(금융\))")
# **제외는 최소로.** 앞의 `sj_div == "BS"` 가 이미 손익·현금흐름을 걸러 내므로
# 여기서 더 걸 것이 거의 없다. 넓게 걸었다가 진짜 차입금을 지운 적이 있다 —
#     옛 판: (차입금의|차입금및|차입원가|이자비용|상환|증가|감소)
#     「**차입금및**」 하나가 「단기차입금및사채」·「장기차입금및사채」·
#     「단기차입금및유동성장기부채」를 통째로 지웠다.
#     실측(SGC에너지 2026 반기): 실제 1조 9,677억이 리스부채 594억으로 줄어
#     **D/E 3.414 가 0.103 이 되고 βU 가 0.089 대신 0.306 — 3.4배 어긋났다.**
#     조회한 24곳 중 7곳이 틀렸고 3곳은 0으로 나왔다. 계정명이 「단기차입금」인
#     회사에서는 안 물려서 앞 회차에서 안 드러났다.
# **넓게 잡고 무엇이 잡혔는지 남기는 쪽**이 옳다. `차입금항목` 에 전부 적어 내보낸다.
제외패턴 = re.compile(r"(차입원가|이자비용|의 차입|의 상환|의 증가|의 감소)")

# **「대체」는 도구가 가를 수 없다.** 같은 낱말이 두 뜻으로 쓰인다 — 실측 두 곳:
#     「장기차입금의 유동성장기부채**로의 대체**」   57.6억  ← 이동액일 수 있다(더하면 이중계상)
#     「장기 차입금(사채 포함)의 유동성 **대체 부분**」 500억  ← 잔액. 그 회사 유일한 차입금
# 빼면 뒤쪽이 틀리고 넣으면 앞쪽이 틀린다. **넣고 알린다** — 이 스크립트의 원칙이
# 「넓게 잡고 무엇이 잡혔는지 남긴다」이므로, 빼서 조용히 줄이는 쪽으로 기울지 않는다.
# 사람이 그 회사 주석을 열어 가른다.
대체주의패턴 = re.compile(r"대체")

# 차입금을 「금융부채」 한 줄로 뭉쳐 놓는 회사가 있다. 이 이름은 매입채무도 섞여 있어
# **더하지 않는다** — 합계가 0일 때 「여기 숨어 있을 수 있다」고 이름만 알린다.
# **차입금이 숨을 수 있는 계정만** 본다. 「기타채무」·「매입채무및기타채무」는 영업부채라
# 차입금이 아니고, 「파생상품 금융부채」도 차입금이 아니다 — 물면 오검출이 된다.
# 실측(한화오션 회차): 옛 패턴이 HD현대중공업의 매입채무 3.29조를 뭉침으로 세었다.
# 진짜 뭉침은 「단기금융부채」·「장기금융부채」처럼 **금융부채가 통째로 한 줄인 경우**다.
뭉침패턴 = re.compile(r"(단기금융부채|장기금융부채|유동금융부채|비유동금융부채)")
뭉침제외 = re.compile(r"(매입채무|기타채무|파생상품|리스)")

# **현금보정의 단기투자(「현금·단기투자」, 2026-09-13).** 조립기가 현금및현금성자산만 알아
# 보정 분자가 작았다. 단기투자는 **이름이 분명한 계정만** 더한다(공백 무시 완전일치) —
# 서로 다른 줄이라 더한다(미국 태그의 「같은 줄의 다른 표현 → 최댓값」과 사정이 다르다).
# 「당기손익-공정가치측정금융자산」·「기타유동금융자산」은 지분증권·미수금·보증금이 섞여 **더하지 않고**
# 이름·금액만 `단기투자_제외후보` 로 남긴다 — 넣을지는 사람이 주석으로 가른다.
단기투자계정 = {"단기금융상품", "단기예금", "단기투자자산", "단기투자증권", "단기금융자산"}
단기투자후보패턴 = re.compile(r"^(유동)?(당기손익|기타유동금융자산|유동금융자산|금융기관예치금)")

# **리스만 잡히고 차입 · 사채가 「기타금융부채」 에 묶인 회사**(2026-10-25 FX3-b — C1 다시 돌리기 3조 실측: HD현대일렉트릭 2026 반기는
# 차입 · 사채 1,145억이 「기타유동/비유동금융부채」 안에 있어 리스부채 678억만 차입금으로 잡혔다). 뭉침패턴은 「유동금융부채」 를 품은
# 이름만 걸었다 — 「기타금융부채」 는 매입채무 · 미지급금 · 보증금이 섞일 수 있어 **더하지 않고** 확인만 세운다
기타금융부채패턴 = re.compile(r"기타(유동|비유동)?금융부채")

# **이자비용(2026-10-25 FX3-b — 고부채 동종의 부채베타 = 합성등급 스프레드 ÷ ERP 의 재료).** 손익의 「이자비용」 이 먼저,
# 없으면 현금흐름표의 이자 지급(금융업 이자 · 영업 아닌 이자수취 줄은 뺀다). 반기 · 분기 손익은 누계(thstrm_add_amount), 현금흐름표는 원래 누계.
# **「금융원가 · 금융비용」 은 이자비용으로 쓰지 않는다**(2026-10-25 FX4-P): 금융비용에는
# 외환차손 · 파생상품 평가손실 · 금융상품 평가손실이 섞여 이자보상배율이 낮게 나오고 합성등급 스프레드가 커져 동종 βU 가 위로 쏠린다
# (하이닉스 2025 실측 — 금융비용 12.5조 중 이자비용 0.92조 · 이자보상배율 3.78배 대 51.1배). 이자비용 줄이 없으면 (None, 까닭) —
# 조립기는 스프레드를 세우지 않고, D/E ≥ 2 동종은 본값 밖(βU본값 ⑧ · 사유 기록). 주석 금융원가 명세의 이자비용은 이 창구(재무제표 API) 밖이다
이자손익패턴 = re.compile(r"^이자비용$")
이자현금패턴 = re.compile(r"^이자(의)?지급(\(영업\)|\(재무\))?$")
금융원가패턴 = re.compile(r"^(금융원가|금융비용)$")              # 쓰지 않는다 — 「있는데 안 썼다」 를 까닭에 적는 데만


def 이자비용뽑기(j, reprt="11011"):
    """fnlttSinglAcntAll 회신 → (이자비용, 근거) — 못 찾으면 (None, 까닭). 캐시 파일을 다시 읽는 쪽(peer_조립)도 쓴다."""
    누계쓴다 = str(reprt) in ("11012", "11013", "11014")
    고른, 금융원가있음 = {}, None
    for it in (j or {}).get("list") or []:
        nm = (it.get("account_nm") or "").replace(" ", "")
        sj = (it.get("sj_div") or "").strip()
        if sj in ("IS", "CIS"):
            v = (_num(it.get("thstrm_add_amount")) if 누계쓴다 else None)
            v = v if v is not None else _num(it.get("thstrm_amount"))
            if 이자손익패턴.search(nm) and v:
                고른.setdefault(1, (abs(v), "손익 「%s」" % it.get("account_nm")))
            elif 금융원가패턴.search(nm) and v:
                금융원가있음 = it.get("account_nm")
        elif sj == "CF" and 이자현금패턴.search(nm) and "금융업" not in nm:
            v = _num(it.get("thstrm_amount"))
            if v:
                고른.setdefault(2, (abs(v), "현금흐름표 「%s」" % it.get("account_nm")))
    if not 고른:
        return None, ("이자비용 줄 없음(손익 「이자비용」 · 현금흐름표 이자 지급)%s — 스프레드를 세우지 않는다" % (
            (" · 손익 「%s」 는 외환 · 파생 · 평가손실이 섞여 이자비용으로 쓰지 않음" % 금융원가있음) if 금융원가있음 else ""))
    return 고른[min(고른)]


def _key():
    k = os.environ.get("OPENDART_API_KEY")
    if not k:
        sys.exit("환경변수 OPENDART_API_KEY 가 없습니다. 값은 화면에 적지 마십시오.")
    return k


def _num(s):
    try:
        return int(str(s).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def 한곳(code, year, reprt, fs_div, key):
    p = os.path.join(CACHEDIR, "%s_%s_%s_%s.json" % (code, year, reprt, fs_div))
    if os.path.exists(p):
        try:
            return json.load(io.open(p, encoding="utf-8")), "캐시"
        except ValueError:
            pass
    url = "%s?%s" % (API, urllib.parse.urlencode(
        {"crtfc_key": key, "corp_code": code, "bsns_year": year,
         "reprt_code": reprt, "fs_div": fs_div}))
    last = None
    for i in range(3):
        try:
            j = json.loads(urllib.request.urlopen(url, timeout=60).read().decode("utf-8"))
            json.dump(j, io.open(p, "w", encoding="utf-8"), ensure_ascii=False)
            return j, "신규"
        except Exception as e:                       # noqa: BLE001
            last = e
            time.sleep(1.5 * (i + 1))
    return {"status": "실패", "message": str(last)}, "실패"


계약부채패턴 = re.compile(r"계약부채|선수금|초과청구|공사선수|선수수익")    # 2026-10-24 W16 — 붙인 계정 이름(공백 없음)에 건다
# 2026-10-25 FX4-P — 결제 · 정산 회사(PG · 간편결제 · 선불)의 고객 예수금 · 미지급 정산금 · 선불 충전금 — 이자부 차입이 아니다.
# 캐피탈 판정(βU본값 「차입 미포착 · 캡티브 의심」)에서 계약부채처럼 부채에서 뺀다(C2 다시 셈 4-9). 자산 계정(예치금 · 정산채권)은 걸지 않는다
예수정산패턴 = re.compile(r"(고객)?예수금|미지급정산|정산미지급|미지급가맹점|가맹점미지급|선불충전|선불전자지급|충전금부채|고객예탁금|예수부채")
예수제외 = re.compile(r"자산|채권|예치금$|미수")

def 뽑기(j, 원하는구분, reprt="11011"):
    """재무상태표·손익계산서에서 쓸 값을 뽑는다.

    **`fnlttSinglAcntAll` 의 회신에는 `fs_div` 칸이 없다**(실측: 키가 아예 없다).
    요약 창구 `fnlttMultiAcnt` 와 달리 요청한 구분만 오므로 골라낼 것이 없다 —
    섞여 오는 함정은 요약 창구 쪽 이야기다. 여기서는 전부 쓴다.
    손익 항목의 `sj_div` 는 `IS` 가 아니라 `CIS`(포괄손익계산서)로 오는 회사가 많다.
    """
    rows = j.get("list") or []
    out = {"차입금항목": [], "차입금합계": 0, "차입금_확인필요": False,
           "뭉침후보": [], "대체행_주의": [], "단기투자항목": [], "단기투자": 0,
           "단기투자_제외후보": [], "계약부채선수금": 0, "기타금융부채": [], "예수정산부채": 0, "예수정산항목": []}
    한번 = set()
    단기한번 = set()
    계약한번 = set()
    # **반기·분기면 손익의 thstrm_amount 는 3개월이다.** 누계는 thstrm_add_amount 다.
    # 재무상태표는 시점값이라 그대로 쓴다 — 손익만 갈라 읽는다.
    누계쓴다 = str(reprt) in ("11012", "11013", "11014")
    for it in rows:
        nm = (it.get("account_nm") or "").strip()
        sj = (it.get("sj_div") or "").strip()
        amt = _num(it.get("thstrm_amount"))
        if sj == "BS" and amt is not None:
            붙인 = nm.replace(" ", "")
            # 2026-10-24 W16 — 수주 산업(조선 · 방산 · 건설)의 계약부채 · 선수금 · 초과청구공사. 캡티브 금융 판정에서 부채총계에서 뺀다(βU본값)
            if 계약부채패턴.search(붙인) and not 붙인.endswith("합계") and (붙인, amt) not in 계약한번:
                계약한번.add((붙인, amt))
                out["계약부채선수금"] += amt
            elif 예수정산패턴.search(붙인) and not 예수제외.search(붙인) and not 붙인.endswith("합계") and (붙인, amt) not in 계약한번:
                계약한번.add((붙인, amt))
                out["예수정산부채"] += amt
                out["예수정산항목"].append({"계정": nm, "금액": amt})
            if 붙인 in 단기투자계정 and (붙인, amt) not in 단기한번:
                단기한번.add((붙인, amt))
                out["단기투자항목"].append({"계정": nm, "금액": amt})
                out["단기투자"] += amt
            elif 단기투자후보패턴.search(붙인) and "비유동" not in 붙인 and "부채" not in 붙인:
                out["단기투자_제외후보"].append({"계정": nm, "금액": amt})
            if 차입패턴.search(nm) and not 제외패턴.search(nm):
                k = (nm, amt)
                if k in 한번:
                    continue
                한번.add(k)
                out["차입금항목"].append({"계정": nm, "금액": amt})
                out["차입금합계"] += amt
                if 대체주의패턴.search(nm):
                    out["대체행_주의"].append({"계정": nm, "금액": amt})
            # 2026-10-25 FX4-P — 띄어 쓴 「유동 금융부채」 도(종전엔 못 물었다). 「기타 (비)유동 금융부채」 는 뭉침이 아니다 — 미지급금 · 보증금이
            # 섞인 계정이라 아래 기타금융부채 줄이 따로 본다(붙여 읽으니 「비유동금융부채」 가 걸려 한국항공우주 같은 동종이 큐로 갔다)
            elif 뭉침패턴.search(붙인) and not 뭉침제외.search(붙인) and "기타" not in 붙인:
                out["뭉침후보"].append({"계정": nm, "금액": amt})
            if 기타금융부채패턴.search(붙인) and "파생" not in 붙인 and amt:
                out["기타금융부채"].append({"계정": nm, "금액": amt})
        for 라벨, 이름들 in (("자산총계", ["자산총계"]), ("부채총계", ["부채총계"]),
                          ("자본총계", ["자본총계"]),
                          ("현금및현금성자산", ["현금및현금성자산",
                                        "현금및현금성자산 ", "현금및 현금성자산"])):
            if nm in 이름들 and sj == "BS" and out.get(라벨) is None:
                out[라벨] = amt
        for 라벨, 이름들 in (("매출액", ["매출액", "수익(매출액)", "영업수익", "매출"]),
                          ("영업이익", ["영업이익", "영업이익(손실)", "영업손실", "영업손익"]),
                          ("당기순이익", ["당기순이익", "당기순이익(손실)"])):
            if nm in 이름들 and sj in ("IS", "CIS") and out.get(라벨) is None:
                out[라벨] = (_num(it.get("thstrm_add_amount")) if 누계쓴다 else None)
                if out[라벨] is None:
                    out[라벨] = amt
    # **뭉침은 차입금이 0 일 때만 보는 것이 아니다.**
    # 옛 판은 `차입금합계 == 0` 안에서만 뭉침을 알렸다 — 차입금이 조금이라도 잡히면
    # 「금융부채」로 뭉친 덩어리가 옆에 있어도 조용했다. 실측(한화오션 회차 유사기업):
    # 차입금이 뭉친 곳이 4곳인데 **한 곳만 플래그가 섰다.** 되살려 보니
    # 세진중공업 D/E 0.008 → 0.342, βU 0.640 → 0.507 로 크게 움직였다.
    # βU 는 D/E 로 무차입화하므로 **차입금을 적게 잡으면 βU 가 부풀고**, 그 βU 가
    # 대상회사에 다시 실리면 자본비용이 통째로 틀린다.
    뭉침합 = sum(x["금액"] for x in out["뭉침후보"])
    if out["차입금합계"] == 0:
        out["차입금_확인필요"] = True
        if out["뭉침후보"]:
            out["차입금_확인필요"] = "금융부채 뭉침 의심(차입금 0) — %s" % (
                " · ".join("%s %s" % (x["계정"], x["금액"]) for x in out["뭉침후보"][:3]))
    elif 뭉침합 and 뭉침합 >= out["차입금합계"] * 0.10:
        # 뭉친 덩어리가 잡힌 차입금의 10% 를 넘으면 **차입금이 있어도 알린다**
        out["차입금_확인필요"] = (
            "금융부채 뭉침 의심 — 차입금 %d 은 잡혔으나 뭉침 후보 %d (차입금의 %.0f%%) 가 "
            "따로 있습니다. **주석에서 그 안의 차입금을 되살리십시오** — 적게 잡으면 βU 가 "
            "부풉니다: %s"
            % (out["차입금합계"], 뭉침합, 뭉침합 / out["차입금합계"] * 100,
               " · ".join("%s %s" % (x["계정"], x["금액"]) for x in out["뭉침후보"][:3])))
    # 2026-10-25 FX3-b — 잡힌 차입금이 리스부채뿐인데 「기타금융부채」 가 따로 크면(리스의 절반 이상 또는 자산 1% 이상) 차입 · 사채가
    # 그 안에 묶였을 수 있다. 더하지 않고 확인을 세운다 — 주석(장단기금융부채)을 읽어 `C2_차입금_확정.json` 으로 확정하면 조립기가 덮는다
    기타합 = sum(x["금액"] for x in out["기타금융부채"])
    리스만 = out["차입금항목"] and all("리스" in x["계정"] for x in out["차입금항목"])
    if 리스만 and 기타합 and not out["차입금_확인필요"] and (
            기타합 >= out["차입금합계"] * 0.5 or (out.get("자산총계") and 기타합 >= out["자산총계"] * 0.01)):
        out["차입금_확인필요"] = (
            "리스부채만 차입금으로 잡힘 · 기타금융부채 %d 따로 — 차입 · 사채가 그 안에 묶였을 수 있다. 주석(장단기금융부채)에서 "
            "되살려 C2_차입금_확정.json 으로 확정하십시오: %s"
            % (기타합, " · ".join("%s %s" % (x["계정"], x["금액"]) for x in out["기타금융부채"][:3])))
    out["뭉침합계"] = 뭉침합
    out["이자비용"], out["이자비용근거"] = 이자비용뽑기(j, reprt)
    return out


열 = ["고유번호", "연도", "보고서", "쓴구분", "status", "자산총계", "부채총계", "자본총계",
     "현금및현금성자산", "매출액", "영업이익", "당기순이익",
     "차입금합계", "차입금_확인필요", "차입금항목", "대체행_주의",
     "단기투자", "단기투자항목", "단기투자_제외후보", "계약부채선수금",
     "이자비용", "이자비용근거", "차입금_확인사유",          # 2026-10-25 FX3-b — 부채베타 재료 · 확인 까닭(종전엔 「예」 만 남아 까닭이 사라졌다)
     "예수정산부채"]                                       # 2026-10-25 FX4-P — 결제 회사 예수금 · 정산금(캡티브 판정에서 뺌)


def 병합쓰기(out, 새행들, 새로=False):
    """`전체재무_추출.csv` 를 **병합**한다 — 키는 (고유번호, 연도, 보고서).

    옛 판은 이번 명단분으로 파일을 통째로 덮었다. 실측(펄어비스 회차 펄29): CP2(핵심+예비 10곳)
    뒤에 CP3(넓은 표본 4곳)를 돌리면 CP2 행이 사라져 조립기가 D 를 못 읽는다 — 회차는
    **14곳을 한꺼번에 다시 돌려** 피했다. 캐시는 층을 나눠 두꺼워져야 하는데 파일이 매번 얇아졌다.

    · 같은 (고유번호, 연도, 보고서) 행은 새 값으로 갈아 끼운다(자리 유지)
    · 다른 연도·보고서 행은 그대로 둔다 — 한 회사가 2025 사업·2026 반기 두 줄을 가질 수 있다.
      읽는 쪽(`peer_조립.py`)이 연도·보고서를 골라 읽는다
    · **연도 칸이 없는 옛 판 행**은 몇 년 치인지 모른다. 이번에 같은 회사를 받았으면 새 행으로
      대체하고(센다), 아니면 연도 빈칸으로 그대로 둔다(센다)
    · `새로=True` 면 옛 동작(이번 명단분만)으로 쓴다
    """
    기존 = []
    if os.path.exists(out) and not 새로:
        기존 = list(csv.DictReader(io.open(out, encoding="utf-8-sig")))
    키 = lambda r: (str(r.get("고유번호") or "").zfill(8), str(r.get("연도") or ""), str(r.get("보고서") or ""))
    새 = {키(r): r for r in 새행들}
    새회사 = {k[0] for k in 새}
    센 = {"추가": 0, "갱신": 0, "유지": 0, "옛행대체": 0, "옛행유지": []}
    결과, 쓴키 = [], set()
    for r in 기존:
        k = 키(r)
        if not k[1]:                                   # 옛 판 행(연도 모름)
            if k[0] in 새회사:
                센["옛행대체"] += 1
                continue
            센["옛행유지"].append(k[0])
            결과.append(r)
            continue
        if k in 새:
            결과.append(새[k])
            쓴키.add(k)
            센["갱신"] += 1
        else:
            결과.append(r)
            센["유지"] += 1
    for r in 새행들:
        if 키(r) not in 쓴키:
            결과.append(r)
            센["추가"] += 1
    with io.open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=열, extrasaction="ignore")
        w.writeheader()
        for r in 결과:
            r = dict(r)
            r["고유번호"] = str(r.get("고유번호") or "").zfill(8)
            w.writerow(r)
    return 센


def 코드풀기(원):
    """1.1.2(HM12) — 8자리는 고유번호 그대로, 6자리(종목코드)는 corpCode 대조표로 고유번호로 푼다. 6자리를 8자리로 0 을 채워 부르면 DART 가 빈 응답을
    줘 조용히 빈 줄이 났다. 못 푼 종목코드는 멈추고 이름을 적는다(조용히 빼지 않는다)."""
    여섯 = [c for c in 원 if len(c) == 6 and c.isdigit()]
    풀 = {}
    if 여섯:
        import dart_fetch as _df                                 # noqa: PLC0415
        풀 = _df.고유번호풀기(여섯)
        못 = [c for c in 여섯 if c not in 풀]
        if 못:
            sys.exit("종목코드(6자리)를 고유번호(8자리)로 풀지 못했다: %s — corpCode 캐시 · 인증키를 확인하거나 고유번호로 준다" % " · ".join(못))
    return [풀[c] if c in 풀 else c.zfill(8) for c in 원]


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--codes")
    ap.add_argument("--codes-file")
    ap.add_argument("--year", required=True)
    ap.add_argument("--reprt", default="11012")
    ap.add_argument("--out", default="전체재무_추출.csv")
    ap.add_argument("--새로", action="store_true",
                    help="기존 파일과 병합하지 않고 이번 명단분만 쓴다(옛 동작)")
    a = ap.parse_args()

    if a.codes_file:
        원 = [l.strip() for l in io.open(a.codes_file, encoding="utf-8") if l.strip()]
    elif a.codes:
        원 = [c.strip() for c in a.codes.split(",") if c.strip()]
    else:
        ap.error("--codes 또는 --codes-file")
    codes = 코드풀기(원)

    os.makedirs(CACHEDIR, exist_ok=True)
    key = _key()
    q = queue.Queue()
    for c in codes:
        q.put(c)
    결과, lock = {}, threading.Lock()

    def 일꾼():
        while True:
            try:
                c = q.get_nowait()
            except queue.Empty:
                return
            j, how = 한곳(c, a.year, a.reprt, "CFS", key)
            쓴것 = "CFS"
            if how == "신규":
                time.sleep(PAUSE)
            if (j or {}).get("status") != "000":
                j2, how2 = 한곳(c, a.year, a.reprt, "OFS", key)
                if how2 == "신규":
                    time.sleep(PAUSE)
                if (j2 or {}).get("status") == "000":
                    j, 쓴것 = j2, "OFS"
            with lock:
                결과[c] = (j, 쓴것)

    ts = [threading.Thread(target=일꾼) for _ in range(THREADS)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()

    out = a.out if os.path.isabs(a.out) else os.path.join(ROOT, a.out)
    확인필요 = []
    새행들 = []
    # 명단 순서대로 쓴다(스레드 완료 순서가 아니라) — 병합 뒤 표를 사람이 읽기 쉽게
    for c in codes:
        if c not in 결과:
            continue
        j, 쓴것 = 결과[c]
        if (j or {}).get("status") != "000":
            새행들.append({"고유번호": c, "연도": str(a.year), "보고서": str(a.reprt),
                        "쓴구분": 쓴것, "status": (j or {}).get("status")})
            확인필요.append(c + "(조회실패)")
            continue
        v = 뽑기(j, "CFS" if 쓴것 == "CFS" else "OFS", a.reprt)
        if v["차입금_확인필요"]:
            확인필요.append(c)
        새행들.append({
            "고유번호": c, "연도": str(a.year), "보고서": str(a.reprt),
            "쓴구분": 쓴것, "status": "000",
            "자산총계": v.get("자산총계"), "부채총계": v.get("부채총계"),
            "자본총계": v.get("자본총계"), "현금및현금성자산": v.get("현금및현금성자산"),
            "계약부채선수금": v.get("계약부채선수금") or "",
            "예수정산부채": v.get("예수정산부채") or "",
            "매출액": v.get("매출액"), "영업이익": v.get("영업이익"),
            "당기순이익": v.get("당기순이익"),
            "차입금합계": v["차입금합계"],
            "차입금_확인필요": "예" if v["차입금_확인필요"] else "",
            "차입금_확인사유": (v["차입금_확인필요"] if isinstance(v["차입금_확인필요"], str) else
                          ("차입금 0" if v["차입금_확인필요"] else "")),
            "이자비용": v.get("이자비용") if v.get("이자비용") is not None else "",
            "이자비용근거": v.get("이자비용근거") or "",
            "차입금항목": "; ".join("%s=%d" % (x["계정"], x["금액"])
                               for x in v["차입금항목"]),
            "대체행_주의": "; ".join("%s=%d" % (x["계정"], x["금액"])
                               for x in v["대체행_주의"]),
            "단기투자": v["단기투자"],
            "단기투자항목": "; ".join("%s=%d" % (x["계정"], x["금액"]) for x in v["단기투자항목"]),
            "단기투자_제외후보": "; ".join("%s=%d" % (x["계정"], x["금액"]) for x in v["단기투자_제외후보"]),
        })
    센 = 병합쓰기(out, 새행들, 새로=a.새로)
    print("%d곳 → %s (병합: 새로 %d · 갱신 %d · 유지 %d%s)"
          % (len(결과), out, 센["추가"], 센["갱신"], 센["유지"],
             (" · 연도 없는 옛 행 대체 %d" % 센["옛행대체"]) if 센["옛행대체"] else ""),
          file=sys.stderr)
    if 센["옛행유지"]:
        print("※ 연도·보고서 칸이 없는 옛 행 %d곳을 그대로 두었습니다 — 몇 년 치인지 모릅니다: %s"
              % (len(센["옛행유지"]), ",".join(센["옛행유지"][:10])), file=sys.stderr)
    if 확인필요:
        print("차입금 합계가 0이거나 조회에 실패한 곳 %d — **무차입 회사로 보지 말 것.** "
              "그 회사 반기보고서 주석을 열어야 한다: %s"
              % (len(확인필요), ",".join(확인필요)), file=sys.stderr)


if __name__ == "__main__":
    main()

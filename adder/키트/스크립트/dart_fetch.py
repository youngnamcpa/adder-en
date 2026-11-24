# -*- coding: utf-8 -*-
"""국내 종목 원본 확보 — OpenDART API 만 쓴다. `sec_fetch.py` 의 국내 짝이다.

**웹 조사로 재무 수치를 받지 않는다.** 여기 있는 모든 값은 OpenDART 응답에서만 온다.
회사 홈페이지·포털·뉴스에서 숫자를 옮겨 적는 일은 이 파일이 하지 않는다.

**인증키는 환경변수 `OPENDART_API_KEY` 에서만 읽고 화면·파일에 출력하지 않는다.**

    python 스크립트/dart_fetch.py --찾기 삼화전자
    python 스크립트/dart_fetch.py --회사 00126380 --기준일 2026-06-30
    python 스크립트/dart_fetch.py --회사 00126380 --기준일 2026-06-30 --신고서      # + 증권신고서 · 투자설명서 · 분할회사(2026-10-25 Y1)
    python 스크립트/dart_fetch.py --회사 00126380 --가정 가정.json                   # 날짜는 가정에서(재무기준일 F · 평가기준일 T)

**날짜 둘(2026-10-25 · `기준일.py`).** `--기준일`(별칭 `--재무기준일`)은 **재무기준일 F** 다 — 평가기준일 전에 제출된 마지막 정기보고서의
기간 끝. 받는 보고서 · 재무 · 원문 · 신고서 창이 모두 이 날에 선다(지금 뜻 그대로). `--평가기준일`(T · 분석일)은 받기를 바꾸지 않고
① 수시공시 창의 끝(`--수시공시`) ② 재무기준일 점검(F 의 보고가 T 뒤에 제출됐나 · T 전에 더 늦은 분기 보고가 있나 — 경보)에만 쓴다.
`--가정` 을 주면 두 날짜를 가정에서 푼다(메타.재무기준일이 없으면 F = T — 옛 가정 파일은 지금과 같다).

두 번째 형태가 한 번에 다 받는다 — 기업개황·제출이력·전체 재무제표(연결/별도)·
주요계정·원문 문서·앵커 시계열. 받은 것은 전부 `_raw/` 에 UTF-8 JSON 으로 남는다
(콘솔이 cp949 라 화면으로 확인하지 않는다).

## 회차마다 다시 짜지 않기 위해 모았다
이 파일이 생기기 전에는 회차마다 조회 스크립트를 새로 만들었다 —
두산에너빌리티 `s01~s09`, 오이솔루션 `dart_step0`·`dart_fetch_main`·`extract_fs`·`unzip_report`.
같은 일을 매번 다시 짜면 그때그때 다른 함정에 빠진다. 두 판을 합쳐 여기 둔다.

## 안전 속도 — 어기면 30분 막힌다
OpenDART 는 **2스레드·호출 사이 0.5초 이상**이다. 그보다 빠르면 응답 없이 연결이 끊기고
30분 안팎 막힌다. 일일 한도 초과는 `status=020` JSON 으로 오므로 구별된다.
이 파일은 호출 사이에 0.6초를 쉬고, 실패하면 늘려 가며 네 번까지 다시 부른다.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import time
import zipfile
import xml.etree.ElementTree as ET

import requests

BASE = "https://opendart.fss.or.kr/api"
KEY = os.environ.get("OPENDART_API_KEY", "")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "_raw")
CACHE = os.path.join(ROOT, "_dartcache")
쉼 = 0.6                       # 호출 사이 (안전 속도)

보고서코드 = {"사업보고서": "11011", "반기보고서": "11012",
           "1분기보고서": "11013", "3분기보고서": "11014"}


def _준비():
    os.makedirs(RAW, exist_ok=True)
    os.makedirs(CACHE, exist_ok=True)
    if not KEY:
        sys.stderr.write("OPENDART_API_KEY 가 환경변수에 없습니다. "
                         "키를 화면에 적지 말고 환경변수로 넣으십시오.\n")
        sys.exit(2)


class 한도초과(Exception):
    """OpenDART 일일 한도(status 020) — 받기를 그 자리에서 멈춘다(2026-10-25 FX-C · 남은 받기는 부르는 쪽이 적는다)."""


호출수 = 0                      # 이 프로세스에서 부른 횟수(수시공시 · 원천축적이 한도를 나눠 쓴다)


def _get(path, **params):
    """OpenDART 한 번 부르기. 실패하면 늘려 가며 네 번까지."""
    global 호출수
    호출수 += 1
    params["crtfc_key"] = KEY
    마지막 = None
    for 회 in range(4):
        try:
            r = requests.get("%s/%s" % (BASE, path), params=params, timeout=40)
            r.raise_for_status()
            time.sleep(쉼)
            return r
        except Exception as e:
            마지막 = e
            time.sleep(1.5 * (회 + 1))
    raise 마지막


def _쓰기(이름, 것):
    p = 이름 if os.path.isabs(이름) else os.path.join(RAW, 이름)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, "w", encoding="utf-8") as f:
        json.dump(것, f, ensure_ascii=False, indent=1)
    return p


def _상태(j, 무엇):
    """OpenDART 는 오류도 200 으로 준다. status 를 반드시 본다."""
    s = (j or {}).get("status")
    if s in (None, "000"):
        return True
    말 = (j or {}).get("message", "")
    if s == "020":
        sys.stderr.write("%s — 일일 한도 초과(020): %s\n" % (무엇, 말))
    elif s == "013":
        sys.stderr.write("%s — 조회된 자료가 없습니다(013). 보고서 코드나 연도를 보십시오\n" % 무엇)
    else:
        sys.stderr.write("%s — status %s: %s\n" % (무엇, s, 말))
    return False


# ══ 고유번호 ══════════════════════════════════════════════════════════════
def 고유번호표():
    """전 상장사 고유번호 대조표(약 30MB). 한 번 받아 캐시한다."""
    p = os.path.join(CACHE, "corpCode.xml")
    if not os.path.exists(p):
        r = _get("corpCode.xml")
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            이름 = [n for n in z.namelist() if n.lower().endswith(".xml")][0]
            바이트 = z.read(이름)
        with open(p, "wb") as f:
            f.write(바이트)
    return ET.parse(p).getroot()


def 고유번호풀기(종목코드들, 캐시=None):
    """종목코드 → 고유번호 {종목코드: 고유번호} — corpCode.xml(캐시)에서 푼다(2026-10-16, S1 리뷰: C1 표본에 고유번호가 없으면
    운영지표 · 사슬 도구가 「DART 를 부를 수 없음」으로 조용히 뺐다 — 펄어비스 표본 10곳 전부). 캐시가 없으면 받는다
    (OPENDART_API_KEY 가 있을 때만). 같은 종목코드가 둘이면 정보갱신일이 늦은 것. 못 푼 종목은 결과에 없다."""
    global CACHE
    p = os.path.join(캐시 or CACHE, "corpCode.xml")
    if not os.path.exists(p):
        if not KEY:
            return {}
        옛 = CACHE
        try:
            CACHE = 캐시 or CACHE
            os.makedirs(CACHE, exist_ok=True)
            고유번호표()
        except Exception:                                      # noqa: BLE001 — 못 받으면 못 푼다(빠진 종목은 부르는 쪽이 적는다)
            return {}
        finally:
            CACHE = 옛
    표, 날 = {}, {}
    for e in ET.parse(p).getroot().iter("list"):
        s = (e.findtext("stock_code") or "").strip()
        if not s:
            continue
        m = (e.findtext("modify_date") or "").strip()
        if s not in 표 or m >= 날[s]:
            표[s], 날[s] = (e.findtext("corp_code") or "").strip(), m
    if 종목코드들 is None:                                    # 표 전체(여러 번 부를 쪽 — 30MB 를 한 번만 읽는다)
        return 표
    return {c.zfill(6): 표[c.zfill(6)] for c in 종목코드들 if c and c.zfill(6) in 표}


def 찾기(부분이름):
    """회사명 부분일치. **상장폐지사가 종목코드를 단 채 남아 있으므로** 종목코드 유무를 함께 낸다."""
    뿌리 = 고유번호표()
    낸것 = []
    for e in 뿌리.iter("list"):
        nm = (e.findtext("corp_name") or "").strip()
        if 부분이름 in nm:
            낸것.append({
                "고유번호": (e.findtext("corp_code") or "").strip(),
                "회사명": nm,
                "종목코드": (e.findtext("stock_code") or "").strip(),
                "정보갱신일": (e.findtext("modify_date") or "").strip(),
            })
    낸것.sort(key=lambda x: (x["종목코드"] == "", x["회사명"]))
    return 낸것


# ══ 한 종목 통째로 ════════════════════════════════════════════════════════
def _직전보고서(기준일):
    """평가기준일이 어느 보고서에 닿는지. (사업연도, 보고서코드, 이름)"""
    y, m, d = int(기준일[:4]), int(기준일[5:7]), int(기준일[8:10])
    if (m, d) >= (12, 31):
        return y, "11011", "사업보고서"
    if (m, d) >= (9, 30):
        return y, "11014", "3분기보고서"
    if (m, d) >= (6, 30):
        return y, "11012", "반기보고서"
    if (m, d) >= (3, 31):
        return y, "11013", "1분기보고서"
    return y - 1, "11011", "사업보고서"


# ══ 반기·분기 손익의 3개월 함정 ═══════════════════════════════════════════
누계필요보고서 = ("11012", "11013", "11014")      # 반기 · 1분기 · 3분기


def _수치(s):
    s = (s or "").replace(",", "").strip()
    if not s or s in ("-", "—"):
        return None
    try:
        return int(s)
    except ValueError:
        try:
            return int(float(s))
        except ValueError:
            return None


# 현금흐름표 앞머리의 항등식 조각들 — account_id 를 먼저 보고, 없으면 계정명으로 본다
_창출 = ("ifrs-full_CashFlowsFromUsedInOperations",)
_순이익CF = ("ifrs-full_ProfitLoss",)
_조정 = ("ifrs-full_AdjustmentsForReconcileProfitLoss",)
_자산부채 = ("dart_AdjustmentsForAssetsLiabilitiesOfOperatingActivities",)


def _현금흐름항등(현금행들):
    """**CF 안의 순이익 행이 3개월인지 항등식으로 잡는다.**

    영업으로부터 창출된 현금흐름 = 순이익 + 조정 + 영업활동 자산·부채 변동.
    어긋나면 순이익 행이 3개월이라는 뜻이고, 그때의 **누계는 나머지 셋에서 역산**된다.
    값을 고치지는 않는다 — 역산값을 알려 주고 사람이 원문과 대조하게 한다.

    실측(현대자동차 2026 반기 연결, 백만원):
        창출 8,137,177 · 조정 13,655,909 · 자산부채 −10,991,620
        API 순이익 2,887,962(3개월) → 항등식 5,552,251 ≠ 8,137,177  **어긋난다**
        역산 순이익 = 8,137,177 − 13,655,909 + 10,991,620 = 5,472,888  **원문과 일치**
    """
    def 고르기(ids):
        for it in 현금행들:
            if (it.get("account_id") or "").strip() in ids:
                return it
        return None

    창, 순, 조, 자 = (고르기(_창출), 고르기(_순이익CF),
                   고르기(_조정), 고르기(_자산부채))
    if not all((창, 순, 조, 자)):
        return None
    v = [_수치(x.get("thstrm_amount")) for x in (창, 순, 조, 자)]
    if any(x is None for x in v):
        return None
    창v, 순v, 조v, 자v = v
    if 창v == 순v + 조v + 자v:
        return None                                  # 항등식이 맞는다 — 누계다
    역산 = 창v - 조v - 자v
    return {"행": 순, "계정": (순.get("account_nm") or "").strip(),
            "준값": 순v, "역산누계": 역산,
            "창출": 창v, "조정": 조v, "자산부채변동": 자v}


_순이익이름 = ("당기순이익", "당기순이익(손실)", "반기순이익", "반기순이익(손실)",
          "분기순이익", "분기순이익(손실)", "연결당기순이익", "연결반기순이익",
          "연결분기순이익", "당기순손익", "반기순손익", "분기순손익")


def _현금순이익대조(목록):
    """**CF 의 당기순이익 행을 손익계산서 누계와 맞대어 3개월인지 잡는다** (2026-09-13 신설,
    펄어비스 실측).

    항등식(`_현금흐름항등`)은 「영업으로부터 창출된 현금흐름」 행이 있어야 돈다. 그 행을 안 내고
    영업활동현금흐름으로 곧장 가는 회사가 있다 — 실측(펄어비스 2026 반기 연결): CF 90행에
    `CashFlowsFromUsedInOperations` 가 없어 항등식이 비켰고, `_읽는법` 은 「CF 갈린 행 0」을 적었다.
    그런데 CF `ifrs-full_ProfitLoss` 는 **99,542,325,760(2분기 3개월)** 이었고 원문 현금흐름표
    누계는 **257,511,315,574** 였다. 이 행에는 `thstrm_add_amount` 짝이 없어 필드 비교로도 안 잡힌다.

    그래서 **같은 보고서 손익계산서의 당기순이익 행**(IS·CIS, 3개월과 누계 둘 다 있다)과 맞댄다.
      CF 값 = 손익 누계     → 멀쩡하다 (None)
      CF 값 = 손익 3개월    → **3개월로 판정** — 쓸 값은 손익 누계
      둘 다 아니다          → **갈림(원인 불명)** — 경보만, 쓸 값을 정하지 않는다
    값을 고치지 않는다 — 판정과 쓸 값을 알려 준다.
    """
    def 수(it, 칸):
        return _수치((it or {}).get(칸))

    def 순이익행(sjs):
        for it in 목록 or []:
            if (it.get("sj_div") or "").strip() not in sjs:
                continue
            if (it.get("account_id") or "").strip() in _순이익CF:
                return it
        for it in 목록 or []:
            if (it.get("sj_div") or "").strip() not in sjs:
                continue
            if (it.get("account_nm") or "").strip() in _순이익이름:
                return it
        return None

    cf = 순이익행(("CF",))
    손 = 순이익행(("IS", "CIS"))
    if cf is None or 손 is None:
        return None
    cfv, 석달, 누계 = 수(cf, "thstrm_amount"), 수(손, "thstrm_amount"), 수(손, "thstrm_add_amount")
    if cfv is None or 누계 is None:
        return None
    if cfv == 누계:
        return None
    판정 = "3개월" if (석달 is not None and cfv == 석달) else "갈림(원인 불명)"
    return {"행": cf, "계정": (cf.get("account_nm") or "").strip(),
            "account_id": (cf.get("account_id") or "").strip(),
            "준값": cfv, "손익_3개월": 석달, "손익_누계": 누계, "판정": 판정,
            "쓸값": 누계 if 판정 == "3개월" else None}


def _손익누계표시(j, 코드):
    """**반기·분기 보고서에서 손익의 `thstrm_amount` 는 3개월이다. 누계가 아니다.**

    실측(SGC에너지 2026 반기 연결):
        수익  thstrm_amount      576,959,944,058   ← 3개월. API 가 주는 기본 칸
              thstrm_add_amount 1,188,440,662,295   ← 누계. 원문과 일치
    원문 손익계산서 머리가 「3개월 | 누적 | 3개월 | 누적」이고 **API 는 3개월 열을 준다.**

    **가장 조용한 종류의 어긋남이다.**
    - 재무상태표(시점값)와 현금흐름표는 멀쩡하다. **손익만 틀린다**
    - 그래서 「자산 = 부채 + 자본」 검산으로는 **절대 안 잡힌다**
    - 마진율은 분자·분모가 같은 기간이라 맞아 보인다. **틀리는 것은 수준이다** —
      매출채권 회전일수처럼 재무상태표와 손익을 섞는 값이 두 배로 튄다
    - `thstrm_nm` 은 3개월이든 누계든 「제 60 기 반기」로 같다. **구분할 칸이 없다**

    ## ⚠ 현금흐름표도 통째로 안전하지는 않다 (2026-09-11 신설 — 현대차 실측)

    종전 판은 `_읽는법` 에 「재무상태표·현금흐름표는 시점값·누계라 thstrm_amount 그대로
    쓴다」고 못 박았다. **CF 시트 안에 손익 개념 행이 섞여 들어오는 것을 못 봤다.**
    실측(현대자동차 2026 반기 연결) — CF 40행 가운데 39행은 누계인데 한 행만 3개월이었다:

        연결반기순이익(ifrs-full_ProfitLoss, sj_div=CF)
            thstrm_amount     2,887,960백만원   ← 2분기 3개월
            원문 현금흐름표    5,472,888백만원   ← 누계

    **합계 검산으로 안 잡힌다.** 「자산 = 부채 + 자본」은 CF 를 안 보고, CF 안에서도
    「영업으로부터 창출된 현금흐름 = 순이익 + 조정 + 자산·부채 변동」 한 줄만 어긋난다.
    그 줄을 안 맞춰 보면 끝까지 조용하다.

    그래서 이제 **CF 시트도 같은 눈으로 훑고**, 갈린 행이 있으면 `_읽는법` 의 문구를
    「그대로 쓴다」에서 「이 행들만 누계를 쓴다」로 바꿔 적는다. `손익값()` 도
    **sj_div 가 아니라 그 행에 `thstrm_add_amount` 가 있는지**로 고르게 넓혔다 —
    시트 이름으로 가르면 이 행이 또 빠진다.

    여기서는 **값을 고치지 않는다**(조회값 가공 금지). 대신 읽는 법을 파일에 박고
    화면에 크게 알린다. 13번 원천에 부을 때 **`thstrm_add_amount` 를 쓴다.**
    """
    if 코드 not in 누계필요보고서 or not isinstance(j, dict):
        return j
    손익 = [it for it in (j.get("list") or [])
           if (it.get("sj_div") or "").strip() in ("IS", "CIS")]
    갈린것 = [it for it in 손익
            if (it.get("thstrm_add_amount") or "").strip()
            and (it.get("thstrm_amount") or "").strip()
            and (it.get("thstrm_add_amount") or "").strip()
            != (it.get("thstrm_amount") or "").strip()]
    # CF 시트에도 손익 개념 행이 섞여 들어온다 — 시트 이름으로 안심하지 않는다.
    # **필드 비교로는 못 잡는다**: 실측(현대차 2026 반기) 그 행에는 `thstrm_add_amount`
    # 자체가 없다. DART 가 3개월 값 하나만 주고 누계 짝을 안 준다. 그래서 **항등식**으로
    # 잡는다 — 영업으로부터 창출된 현금흐름 = 순이익 + 조정 + 영업활동 자산·부채 변동.
    현금 = [it for it in (j.get("list") or [])
           if (it.get("sj_div") or "").strip() == "CF"]
    현금갈린것, 현금항등 = [], _현금흐름항등(현금)
    if 현금항등:
        현금갈린것 = [현금항등["행"]]
    # **항등식 재료가 없어도 순이익 행은 손익계산서 누계와 맞대 본다** (2026-09-13, 펄어비스 실측)
    현금대조 = _현금순이익대조(j.get("list") or [])
    if 현금대조 and not any(x is 현금대조["행"] for x in 현금갈린것):
        현금갈린것.append(현금대조["행"])
    j["_읽는법"] = {
        "보고서코드": 코드,
        "주의": "반기·분기 보고서의 손익(IS·CIS)에서 thstrm_amount 는 **3개월**이다. "
              "누계는 thstrm_add_amount 다. 13번 원천에는 **누계를 붓는다.**",
        "손익행수": len(손익),
        "3개월과_누계가_다른_행": len(갈린것),
        "현금흐름표행수": len(현금),
        "현금흐름표_3개월과_누계가_다른_행": len(현금갈린것),
        "현금흐름표_갈린_계정": [(it.get("account_nm") or "").strip()
                        for it in 현금갈린것][:8],
        "현금흐름표_항등식": (None if not 현금항등 else {
            "계정": 현금항등["계정"],
            "API가_준_값(3개월)": 현금항등["준값"],
            "항등식_역산_누계": 현금항등["역산누계"],
            "쓸_값": "항등식_역산_누계 — 원문 현금흐름표와 대조해 확인하고 쓴다",
        }),
        # 항등식 재료가 없는 회사도 잡는다 — CF 순이익 ↔ 손익계산서 순이익(3개월·누계)
        "현금흐름표_순이익대조": (None if not 현금대조 else {
            "계정": 현금대조["계정"],
            "account_id": 현금대조["account_id"],
            "API가_준_값": 현금대조["준값"],
            "손익계산서_3개월": 현금대조["손익_3개월"],
            "손익계산서_누계": 현금대조["손익_누계"],
            "판정": 현금대조["판정"],
            "쓸_값": (현금대조["쓸값"] if 현금대조["쓸값"] is not None else
                    "정하지 않음 — CF 값이 손익 3개월과도 누계와도 다르다. 원문 현금흐름표를 연다"),
        }),
        "현금흐름표_누계대체": ({현금대조["account_id"] or 현금대조["계정"]: 현금대조["쓸값"]}
                        if (현금대조 and 현금대조["쓸값"] is not None) else {}),
        "재무상태표": "시점값이라 thstrm_amount 그대로 쓴다",
        "현금흐름표": (("대부분 누계라 thstrm_amount 그대로 쓰지만 **「%s」 행은 "
                  "3개월이다** — 그 행에는 누계 짝(thstrm_add_amount)이 아예 없어서 "
                  "필드 비교로는 안 잡힌다. `현금흐름표_항등식`·`현금흐름표_순이익대조` 의 "
                  "쓸 값을 원문과 대조해 쓴다. "
                  "실측(현대차 2026 반기: CF 40행 중 이 한 행만 3개월 · 펄어비스 2026 반기: "
                  "항등식 재료가 없어 손익계산서 누계 대조로만 잡혔다)")
                 % " · ".join(sorted({(it.get("account_nm") or "").strip()
                                      for it in 현금갈린것}))
                 if 현금갈린것 else
                 "이 보고서에서는 갈린 행이 없어 thstrm_amount 그대로 쓴다 "
                 "(다만 시트 이름만 보고 안심하지 않는다 — 손익 개념 행이 섞이면 갈린다)"),
    }
    if 갈린것:
        print("  ※※ 손익 %d행 중 %d행에서 **3개월과 누계가 다르다.** "
              "`thstrm_amount` 는 3개월이다 — 13번 원천에는 `thstrm_add_amount`(누계)를 "
              "부어라. 재무상태표는 시점값이라 그대로 쓴다 "
              "(현금흐름표는 아래 항등식 결과를 보라 — 시트 이름만으로 안심하지 않는다)"
              % (len(손익), len(갈린것)))
        보기 = [it for it in 갈린것
                if (it.get("account_nm") or "").strip()
                in ("매출액", "수익", "수익(매출액)", "영업수익", "영업이익", "영업이익(손실)")]
        for it in 보기[:3]:
            print("       %-12s 3개월 %s / 누계 %s"
                  % ((it.get("account_nm") or "")[:12],
                     it.get("thstrm_amount"), it.get("thstrm_add_amount")))
    if 현금항등:
        print("  ※※ **현금흐름표의 「%s」 행이 3개월이다.** 시트 이름만 보고 "
              "「현금흐름표는 안전하다」로 읽지 마라 — 손익 개념 행이 섞여 들어오고, "
              "**그 행에는 thstrm_add_amount(누계) 짝이 아예 없다.**"
              % 현금항등["계정"])
        print("       API가 준 값(3개월) %s / 항등식 역산 누계 %s"
              % ("{:,}".format(현금항등["준값"]), "{:,}".format(현금항등["역산누계"])))
        print("       항등식: 창출 %s = 순이익 + 조정 %s + 자산·부채변동 %s"
              % ("{:,}".format(현금항등["창출"]), "{:,}".format(현금항등["조정"]),
                 "{:,}".format(현금항등["자산부채변동"])))
        print("       → 13번 원천에는 **역산 누계**를 쓰고 원문 현금흐름표와 대조하라")
    if 현금대조:
        print("  ※※ **현금흐름표의 「%s」 행이 손익계산서 누계와 다르다 — 판정 %s.**"
              % (현금대조["계정"], 현금대조["판정"]))
        print("       CF API 값 %s / 손익 3개월 %s / 손익 누계 %s"
              % ("{:,}".format(현금대조["준값"]),
                 "{:,}".format(현금대조["손익_3개월"]) if 현금대조["손익_3개월"] is not None else "—",
                 "{:,}".format(현금대조["손익_누계"])))
        if 현금대조["쓸값"] is not None:
            print("       → 이 행은 **손익계산서 누계(%s)** 를 쓰고 원문 현금흐름표와 대조하라 "
                  "(`_읽는법.현금흐름표_누계대체`)" % "{:,}".format(현금대조["쓸값"]))
        else:
            print("       → 3개월로도 누계로도 설명되지 않는다. **원문 현금흐름표를 열어라** — 쓸 값을 정하지 않았다")
    return j


def 손익값(항목, 코드, 읽는법=None):
    """한 행에서 그 보고서에 맞는 값을 고른다. 반기·분기면 누계.

    **시트(sj_div)로 가르지 않는다.** 그 행에 `thstrm_add_amount` 가 있으면 그것이
    누계이고, 없으면 `thstrm_amount` 가 유일한 값이다. 종전에는 부르는 쪽이 손익
    시트에서만 이 함수를 써서, **CF 안의 손익 개념 행이 3개월인 채로 빠져나갔다**
    (현대차 2026 반기 「연결반기순이익」 실측). 판정을 행 자신에게 맡긴다.

    **`읽는법`(받은 JSON 의 `_읽는법`)을 넘기면** 누계 짝이 없는 CF 행 가운데
    `현금흐름표_누계대체` 에 오른 행은 그 누계를 쓴다(2026-09-13, 펄어비스 실측 —
    CF 순이익 3개월 99,542,325,760 → 손익계산서 누계 257,511,315,574).
    """
    if 코드 in 누계필요보고서:
        v = (항목.get("thstrm_add_amount") or "").strip()
        if v:
            return v
        if (항목.get("sj_div") or "").strip() == "CF" and isinstance(읽는법, dict):
            대체 = 읽는법.get("현금흐름표_누계대체") or {}
            for 키 in ((항목.get("account_id") or "").strip(),
                      (항목.get("account_nm") or "").strip()):
                if 키 and 대체.get(키) is not None:
                    return str(대체[키])
    return (항목.get("thstrm_amount") or "").strip()


# ══ 앵커 시계열 ═══════════════════════════════════════════════════════════
# 규칙 「**영업이익률의 부호가 두 번 바뀔 때까지, 최소 여섯 개 사업연도.**
# 부호가 안 바뀌면 어디까지 갔는지 적는다」 — 이 조문을 스크립트가 지킨다.
# 해수를 사람이 미리 정하면 그 조문에 닿았는지 아무도 모른다. 실측: 삼화전자공업은
# 기본 4해(6개 사업연도)로는 전환이 0회였고, 12해까지 늘려도 0회였다. 그 사실
# 자체가 관문 ②(평상시라 부를 구간이 없다) 판정의 재료가 됐다.
# **읽기는 `앵커읽기.py` 한 곳이다**(S2-16 — 자체검사 ⑱ 이 같은 함수로 관측 이익률을 읽는다). 이름은 앞의 번호 머리(「Ⅰ.매출액」)와
# 빈칸을 떼고 견주고, 안 걸리면 표준계정코드(매출 `ifrs-full_Revenue` · 영업이익 `dart_OperatingIncomeLoss`), 그다음 금융업 계정이다.
# 실측(S1 재리뷰 R2-01): 「Ⅰ.매출액」 꼴 계정명을 적는 회사는 종전 이름 일치로 해가 통째로 빠졌다(A3 는 코드를 먼저 봐 갈래 사이 관측 해가 갈렸다).
import 앵커읽기 as _앵읽                                        # noqa: E402
_매출이름 = _앵읽.매출이름
_영업이름 = _앵읽.영업이름
# **이름이 안 걸리면 표준계정코드로 한 번 더 본다** (2026-09-13 신설, 펄어비스 실측).
# 2022년부터 계정명이 「영업이익」→「영업손익」으로 바뀌어 네 해가 통째로 빠졌고,
# 흑→적 전환(2022→2023)이 있는데도 앵커가 「부호 전환 0회」를 적었다 — 관문 ② 재료가 뒤집히는 자리다.
_영업코드 = _앵읽.영업코드

# **금융업은 「매출액」 계정이 없다.** 이자수익·보험수익·수수료수익으로 나뉜다.
# 실측(KB금융): 손익의 수익 계열이 「보험수익 · 재보험수익 · 수수료수익 · 이자수익 ·
# 보험금융이자수익 · 당기손익-공정가치로 측정하는 금융자산의 이자수익」이고
# **위 다섯 이름이 하나도 안 걸린다.** 종전에는 조용히 None 이 돌아가 앵커가
# 「매출을 못 읽었다」로만 남았다 — 무엇 때문인지가 안 적혔다.
#
# **잡되, 무엇으로 잡았는지 밝힌다.** 이 값은 FCFF 의 매출과 성질이 다르다 —
# 금융업은 이자수익이 영업수익이고 차입금이 원재료라
# **「기업가치 = 영업가치 + 비영업자산」 구조가 성립하지 않는다.**
# 값이 잡혔다고 DCF 가 되는 것이 아니므로, 이 이름으로 잡히면 그 사실을 함께 낸다.
_금융매출이름 = _앵읽.금융매출이름


def _한해값(items, 이름들):
    """손익 항목에서 한 계정을 뽑는다(이름은 맞춘 꼴로 — 「Ⅰ.매출액」 = 「매출액」). 못 구하면 None(0 으로 메우지 않는다)."""
    return _앵읽.이름값(items, 이름들)[0]


def _한해값코드(items, 코드들):
    """`_한해값` 과 같되 계정명이 아니라 표준계정코드(`account_id`)로 찾는다."""
    return _앵읽.코드값(items, 코드들)[0]


def _매출한해(items):
    """매출을 뽑되 **무엇으로 잡았는지 함께 낸다** — `(값, 어느이름, 금융업이냐)`. 이름(맞춘 꼴) → 표준계정코드 → 금융업 계정 차례.
    금융업 계정으로 잡히면 세 번째 값이 True 다 — **값이 잡혔다고 DCF 가 되는 것이 아니므로** 부르는 쪽이 그 사실을 관문에 올려야 한다."""
    return _앵읽.매출한해(items)


def _부호들(해들):
    """오래된 해부터 영업이익의 부호 목록(못 구한 해는 건너뛴다)."""
    부호 = []
    for h in sorted(해들, key=lambda x: x["사업연도"]):
        매출 = _매출한해(h["list"])[0]
        영업 = _앵읽.영업한해(h["list"])[0]
        if 매출 and 영업 is not None:
            부호.append(1 if 영업 >= 0 else -1)
    return 부호


def _부호전환수(해들):
    """오래된 해부터 영업이익률의 부호가 몇 번 바뀌었나. 못 구한 해는 건너뛴다."""
    부호 = _부호들(해들)
    return sum(1 for a, b in zip(부호, 부호[1:]) if a != b)


def _이익률들(해들):
    """오래된 해부터 영업이익률 목록(못 구한 해는 건너뛴다) — 사이클 진폭을 재는 재료."""
    율 = []
    for h in sorted(해들, key=lambda x: x["사업연도"]):
        매출 = _매출한해(h["list"])[0]
        영업 = _앵읽.영업한해(h["list"])[0]
        if 매출 and 영업 is not None:
            율.append(영업 / 매출)
    return 율


# **흑자 속 사이클의 문턱** (2026-10-16, S1 재리뷰 N-01). 전부 흑자여도 관측 영업이익률의 최고 ÷ 최저가 이 배수 이상이면
# 이익률이 몇 배로 출렁이는 회사다(예: 해운 · 메모리 · 정유 · 화학 소재처럼 흑자를 지키며 국면이 갈리는 유형).
# 그때 여섯 해에서 멈추면 한 국면(대개 상승 국면)만 받는다 — 정상 이익률 · 상하한 · 국면 범위가 정점에 묶인다.
# 문턱 아래(이익률이 고른 흑자 — 유통 · 소비재 · 플랫폼 · SaaS 의 다수)만 여섯 해에서 멈춘다. sec_앵커.사이클진폭 과 같은 정의다.
사이클진폭배수 = 2.0


def 사이클진폭(율들, 배수문턱=사이클진폭배수):
    """관측 이익률 목록 → {최저, 최고, 배수, 사이클}. 배수 = 최고 ÷ 최저(최저가 0 이하이면 None — 부호 전환 쪽이 잰다).
    `사이클` 은 전부 흑자인데 배수가 문턱 이상인가(흑자 속 사이클). 이익률이 둘 미만이면 None."""
    율 = [x for x in (율들 or []) if x is not None]
    if len(율) < 2:
        return None
    lo, hi = min(율), max(율)
    배 = (hi / lo) if lo > 0 else None
    # 모양 — 앞의 고점에서 1/3 넘게 내려간 적과 앞의 저점에서 1.5배 넘게 오른 적이 둘 다 있으면 「오르내림」(사이클),
    # 한쪽만 있으면 「한 방향」(규모의 경제로 이익률이 오르기만 한 회사 · 구조적으로 내리기만 한 회사). 오래된 해부터 준다.
    하락 = any(율[j] <= 율[i] * (2 / 3) for i in range(len(율)) for j in range(i + 1, len(율)) if 율[i] > 0)
    상승 = any(율[j] >= 율[i] * 1.5 for i in range(len(율)) for j in range(i + 1, len(율)) if 율[i] > 0)
    모양 = "오르내림" if (하락 and 상승) else ("한 방향(상승)" if 상승 else ("한 방향(하락)" if 하락 else "고름"))
    return {"최저": round(lo, 4), "최고": round(hi, 4), "배수": (round(배, 2) if 배 is not None else None),
            "사이클": bool(배 is not None and 배 >= 배수문턱), "문턱": 배수문턱, "모양": 모양}


def 진폭문장(진, 꼬리):
    """사이클진폭 결과 → 관문 ② 재료의 진폭 문장(관문 판정과 따로 — 전부 흑자일 때 붙인다)."""
    if 진.get("배수") is None:                                # 최저 이익률 0(흑자 경계) — 배수를 잴 수 없다(S2-20)
        return ("영업이익률 %.1f%%~%.1f%%(최저 이익률 0 — 최고 ÷ 최저 배수를 잴 수 없다). 손익분기 언저리의 해가 있으니 관측 창이 한 국면에만 "
                "걸쳤는지 사람이 보고, %s" % (진["최저"] * 100, 진["최고"] * 100, 꼬리))
    범 = "영업이익률 %.1f%%~%.1f%%(최고 ÷ 최저 %.1f배" % (진["최저"] * 100, 진["최고"] * 100, 진["배수"])
    if not 진["사이클"]:
        return 범 + " < %.0f배) — 평상시 구간이 넓다" % 진["문턱"]
    if 진["모양"] == "오르내림":
        return ("**다만 흑자 속 사이클이다** — %s ≥ %.0f배, 오르내림). 관측 창이 한 국면에만 걸쳤는지 보고(정상 이익률 · 상하한 · "
                "국면 범위가 정점이나 바닥에 묶이지 않게), %s" % (범, 진["문턱"], 꼬리))
    return ("**다만 이익률이 %s으로 크게 옮겨 갔다** — %s ≥ %.0f배). 규모의 경제 · 구조 변화로 옮겨 간 것이면 옛 구간을 평상시에 "
            "섞지 말고 최근 구간이 앞으로의 평상시에 가까운지 본다. 사이클의 한쪽 국면이면 %s" % (진["모양"], 범, 진["문턱"], 꼬리))


def 관문2재료(부호, 이익률=None):
    """부호 목록 → 관문 ② 의 읽기(자체검사 ⓪ 과 같은 정의). **전환 0 회 + 전부 흑자는 「평상시 구간이 넓다」 — 안 걸린다.**
    걸리는 것은 「전부 적자이고 최근이 단조 개선도 아닌」 경우다(그 판정은 이익률 값이 있는 ⓪ 이 한다).
    **관문 판정과 사이클 진폭은 다른 질문이다**(2026-10-16, S1 재리뷰 N-01) — 이익률 목록을 주면 전부 흑자일 때 진폭을 따로 적는다.
    흑자 속 사이클이면 관문 ② 에는 안 걸리지만 관측 창이 한 국면에만 걸쳤는지(정상화 창)를 따로 봐야 한다."""
    전환 = sum(1 for a, b in zip(부호, 부호[1:]) if a != b)
    if not 부호:
        return "재료 없음"
    if 전환 == 0 and all(x > 0 for x in 부호):
        진 = 사이클진폭(이익률)
        if 진 is None:
            return "전부 흑자(전환 0회) — 관문 ② 에 안 걸린다. 사이클 진폭은 이익률 재료가 없어 못 쟀다"
        return "전부 흑자(전환 0회) — 관문 ② 에 안 걸린다. " + 진폭문장(진, "모자라면 앵커를 더 받는다")
    if 전환 == 0:
        return "전부 적자(전환 0회) — 최근이 단조 개선이면 T4(전환 미완)의 예고, 아니면 관문 ② 에 걸린다(자체검사 ⓪ 이 이익률로 가른다)"
    return "부호 전환 %d회 — 한 번 꺾여 돌아오지 않은 것인지, 진폭이 사이클인지 한 번의 사건인지 관문 ② 를 판정하십시오" % 전환


def 앵커받기(고유, 시작연, 기존=None, 최소해수=6, 필요전환=2, 상한=15, 흑자멈춤=True):
    """부호가 두 번 바뀔 때까지 뒤로 거슬러 받는다. **멈춘 이유를 함께 낸다.**

    시작연은 **사업보고서가 있을 수 있는 가장 최근 해**다. 평가기준일이 연중이면
    그 해 사업보고서는 아직 없으므로(status 013) 호출 하나가 그냥 버려진다 —
    부르는 쪽이 시작연을 한 해 낮춰 준다.

    이미 받아 둔 해(`기존`)는 다시 받지 않는다. 앵커를 뒤로 늘릴 때 이 함수만
    다시 부르면 되고, `통째로()` 를 다시 불러 `_raw/` 를 통째로 덮을 일이 없다.

    `흑자멈춤=False`(`--앵커만 --앵커끝까지`)면 「전부 흑자 · 이익률 고름 → 여섯 해에서 멈춤」을 끈다 — 고른 고마진 여섯 해가 사이클의
    정점 국면일 수 있는 유형(경기순환 · 원자재 표지)에서 자료가 마를 때까지 더 받는다(S2-17 · 호출은 늘어난 해 수만큼 — 대개 다섯 이하).
    """
    받은 = list(기존 or [])
    있는해 = {h["사업연도"] for h in 받은}
    연속실패, 멈춤이유 = 0, "상한 %d해 도달" % 상한
    # 재무구분 — 연결(CFS)을 먼저 부르고, 연결을 한 해도 못 받았는데 그 해 연결이 없으면 별도(OFS)로 받아 그 뒤로는 별도로 간다
    # (종속기업이 없어 연결 재무제표를 내지 않는 회사가 앵커 0해로 끝나던 결함 · 2026-10-23 유니버스 선별). 한 앵커 안에서 둘을 섞지 않는다
    구분 = next((h.get("재무구분") for h in 받은 if h.get("재무구분")), "CFS")
    for y in range(시작연, 시작연 - 상한, -1):
        if y not in 있는해:
            j = _get("fnlttSinglAcntAll.json", corp_code=고유, bsns_year=str(y),
                     reprt_code="11011", fs_div=구분).json()
            if (j or {}).get("status") != "000" and 구분 == "CFS" and not 받은:
                j2 = _get("fnlttSinglAcntAll.json", corp_code=고유, bsns_year=str(y),
                          reprt_code="11011", fs_div="OFS").json()
                if (j2 or {}).get("status") == "000":
                    구분, j = "OFS", j2
                    print("  앵커 — 연결 재무제표가 없어 별도(OFS)로 받는다")
            if (j or {}).get("status") == "000":
                받은.append({"사업연도": y, "list": j.get("list") or [], "재무구분": 구분})
                연속실패 = 0
                print("  앵커 %d년 — %d행" % (y, len(j.get("list") or [])))
            else:
                연속실패 += 1
                print("  앵커 %d년 — 없음(%s)" % (y, (j or {}).get("status")))
                # 받은 게 있는데 두 해 내리 비면 자료가 마른 것이다. 더 두드리지 않는다
                if 받은 and 연속실패 >= 2:
                    멈춤이유 = "자료 소진(%d년 아래로 없음)" % (y + 1)
                    break
                continue
        전환 = _부호전환수(받은)
        if len(받은) >= 최소해수 and 전환 >= 필요전환:
            멈춤이유 = "전환 %d회 도달" % 전환
            break
        # **전부 흑자이고 이익률이 고르면 최소 해수에서 멈춘다** (2026-10-16, S1 리뷰 · 재리뷰 N-01). 꾸준히 흑자인 회사(유통 · 소비재 ·
        # 플랫폼 · SaaS 의 다수)는 부호가 영영 안 바뀐다 — 상한까지 거슬러 가는 것은 호출 낭비다. **다만 흑자 속에서 이익률이 몇 배로
        # 출렁이면(최고 ÷ 최저 ≥ 사이클진폭배수) 멈추지 않는다** — 여섯 해가 한 국면(대개 상승 국면)만 담아 정상 이익률이 정점에 묶인다.
        # 그때는 종전대로 전환 2회 · 자료 소진 · 상한까지 간다(최고 ÷ 최저는 해를 더할수록 줄지 않으므로 한 번 넘으면 끝까지 간다).
        _부 = _부호들(받은)
        if 흑자멈춤 and len(받은) >= 최소해수 and len(_부) >= 최소해수 and all(x > 0 for x in _부):
            _진 = 사이클진폭(_이익률들(받은))
            if not (_진 and _진["사이클"]):
                멈춤이유 = ("전부 흑자 · 이익률 진폭 %s배 < %.0f배 — %d해 확보 뒤 멈춤(평상시 구간이 넓다)"
                         % ((_진 or {}).get("배수"), 사이클진폭배수, len(받은)))
                break
    전환 = _부호전환수(받은)
    받은.sort(key=lambda x: x["사업연도"])
    진폭 = 사이클진폭(_이익률들(받은))
    if 진폭 and 진폭["사이클"] and 전환 == 0:
        멈춤이유 += (" — 전부 흑자이나 이익률 진폭 %s배 ≥ %.0f배(%s)라 여섯 해에서 멈추지 않았다"
                  % (진폭["배수"], 사이클진폭배수, "흑자 속 사이클" if 진폭["모양"] == "오르내림" else 진폭["모양"]))
    print("  앵커 %d개 사업연도 · 부호 전환 %d회 · 멈춘 이유: %s"
          % (len(받은), 전환, 멈춤이유))
    관문2 = 관문2재료(_부호들(받은), _이익률들(받은))
    if 전환 < 필요전환 or (진폭 and 진폭["사이클"]):
        # **부호가 두 번 안 바뀐 것 자체는 관문 ② 에 걸린 것이 아니다** (2026-10-16, S1 리뷰 — 종전 문장은 「평상시라 부를
        # 구간이 없을 수 있다」였다. 9년 내내 흑자인 BGF리테일에 그 문장이 떠 관문에 섰다). 정의는 자체검사 ⓪ 과 같다.
        print("  ※ 관문 ② 재료 — %s" % 관문2)

    # **매출을 무엇으로 잡았는지 밝힌다.** 금융업 계정으로 잡혔으면 값이 나왔어도
    # FCFF 의 매출이 아니다 — 조용히 넘어가면 그 값 위에 모델이 서 버린다.
    금융해 = []
    for h in 받은:
        _v, _나, _금 = _매출한해(h["list"])
        if _금:
            금융해.append((h["사업연도"], _나))
    if 금융해:
        print("  ※ **매출을 금융업 계정으로 잡았다** — %s (%d개 사업연도).\n"
              "     이 값은 FCFF 의 매출과 성질이 다르다: 금융업은 이자수익이 영업수익이고\n"
              "     차입금이 원재료라 **「기업가치 = 영업가치 + 비영업자산」 구조가 성립하지\n"
              "     않는다.** 값이 잡혔다고 현금흐름할인법이 되는 것이 아니므로\n"
              "     **관문 ①에서 이 사실을 판정하십시오.**"
              % (" · ".join(sorted({나 for _해, 나 in 금융해})), len(금융해)))
    읽지못한 = [(h["사업연도"], 까닭) for h in 받은 for _y, 율, 까닭 in [_앵읽.해마진(h)] if 율 is None]
    if 읽지못한:
        print("  ※ 읽지 못한 해 %d개 — %s (계정 이름 · 표준계정코드를 다 봤다. 원문 손익계산서에서 그 해를 확인하십시오)"
              % (len(읽지못한), " · ".join("%s %s" % (y, 까) for y, 까 in 읽지못한)))
    return 받은, {"부호전환수": 전환, "멈춘이유": 멈춤이유, "읽지못한해": [{"사업연도": y, "까닭": 까} for y, 까 in 읽지못한],
                "사업연도수": len(받은), "최소해수": 최소해수, "필요전환": 필요전환,
                "관문2재료": 관문2, "이익률진폭": 진폭,
                "금융업계정": sorted({나 for _해, 나 in 금융해}) or None}


def 결산월점검(개황, 결산월확인=False):
    """기업개황의 `acc_mt`(결산월)가 12 가 아니면 멈추고 묻는다 (2026-10-16, S1 리뷰).
    `_직전보고서()` 는 달력 3 · 6 · 9 · 12월로 보고서 코드를 고른다 — 3월 결산 회사의 「반기」는 4~9월이라
    6/30 기준일이면 엉뚱한 보고서를 받는다. 드물지만 조용히 틀리는 종류라 사람이 정하게 한다."""
    acc = ("%s" % ((개황 or {}).get("acc_mt") or "")).strip()
    if not acc or acc in ("12", "012"):
        return None
    글 = ("**결산월이 %s월입니다(기업개황 acc_mt)** — 이 도구는 12월 결산을 전제로 보고서 코드를 고릅니다(반기 = 1~6월). "
         "%s월 결산 회사는 회계연도 · 반기 · 분기의 끝날이 다릅니다. 평가기준일을 그 회사의 분기말로 잡았는지, 받을 보고서(사업연도 · "
         "보고서 코드)가 맞는지 정한 뒤 `--결산월확인` 을 붙여 다시 도십시오. 시장 자료 · 유사기업의 기준일과 갈리면 그 결정도 적으십시오"
         % (acc, acc))
    if not 결산월확인:
        sys.stderr.write("\n[멈춤] " + 글 + "\n")
        raise SystemExit(3)
    print("  ※ " + 글 + " — `--결산월확인` 으로 진행합니다")
    return 글


_보고서딱지 = {"11012": "반기", "11013": "1분기", "11014": "3분기", "11011": "사업"}


def 원문고르기(제출, 기준일, 원문해수=6):
    """제출이력에서 받을 원문 — [(딱지, 접수번호, 보고서명)]. **관문 ③ · C1 슬롯 · A2 · A3 의 공통 입력**(S1 리뷰 S1-10).
      · 기준일 보고서(반기 · 분기 · 사업) — 같은 기간에 [기재정정]이 있으면 정정본(늦게 낸 것)
      · 최신 사업보고서 — 위와 같다
      · 과거 사업보고서 — 하나가 당기 · 전기 두 해를 주므로 한 해 걸러 `원문해수` 개 회계연도를 덮을 만큼"""
    연, 코드, _ = _직전보고서(기준일)
    목록 = (제출 or {}).get("list") or []

    def 최신(정규식):
        후 = [x for x in 목록 if re.search(정규식, x.get("report_nm") or "")]
        return max(후, key=lambda x: x.get("rcept_no") or "") if 후 else None
    낸 = []
    if 코드 != "11011":
        월 = int(기준일[5:7])
        종류 = "반기보고서" if 코드 == "11012" else "분기보고서"
        x = 최신(r"%s\s*\(%d\.%02d\)" % (종류, 연, 월))
        if x:
            낸.append((_보고서딱지[코드], x["rcept_no"], x.get("report_nm")))
    사업끝 = 연 if 코드 == "11011" else 연 - 1
    for y in range(사업끝, 사업끝 - max(1, 원문해수), -2):
        x = 최신(r"사업보고서\s*\(%d\.\d{2}\)" % y)
        if x:
            낸.append(("사업%d" % y, x["rcept_no"], x.get("report_nm")))
    return 낸


def 원문들받기(제출, 기준일, 원문해수=6):
    """`원문고르기` 가 고른 원문을 받는다 — 이미 받아 둔 접수번호는 건너뛴다. 받은 [(딱지, 접수번호)]."""
    받은 = []
    for 딱지, 접수, 이름 in 원문고르기(제출, 기준일, 원문해수):
        if glob_있음(접수):
            continue
        try:
            원문(접수, 딱지)
            받은.append((딱지, 접수))
        except 한도초과:
            raise
        except SystemExit as e:
            sys.stderr.write("원문 %s(%s) 받기 실패 — %s\n" % (딱지, 접수, e))
        except Exception as e:                                # noqa: BLE001
            sys.stderr.write("원문 %s(%s) 받기 실패 — %s\n" % (딱지, 접수, e))
    return 받은


def glob_있음(접수):
    import glob as _g                                          # noqa: PLC0415
    return bool(_g.glob(os.path.join(RAW, "**", 접수 + "*.txt"), recursive=True))


def 통째로(고유, 기준일, 해수=4, 원문해수=6, 결산월확인=False, 원문받기=True, 평가기준일=None):
    """기업개황·제출이력·재무제표·앵커 시계열 · **공시 원문(기준일 보고서 + 최신 · 과거 사업보고서)**을 한 번에.
    받은 파일 목록을 낸다. 원문은 A1 의 산출이다 — 관문 ③(약정 한도) · C1(부문 비중) · A2(주석) · A3(동인 원천)가
    같은 파일을 읽는다(「한 번 연 보고서에서 다 뽑는다 · 먼저 받은 쪽이 쓴다」를 도구로 보장).
    `기준일` 은 재무기준일 F 다. `평가기준일`(T)을 주면 제출이력으로 F 를 대 보고 경보만 낸다(받기는 바꾸지 않는다)."""
    낸것 = []
    연, 코드, 이름 = _직전보고서(기준일)
    print("재무기준일 %s → %d년 %s (코드 %s)" % (기준일, 연, 이름, 코드))

    j = _get("company.json", corp_code=고유).json()
    if _상태(j, "기업개황"):
        낸것.append(_쓰기("dart_기업개황.json", j))
        print("  기업개황 — %s (%s)" % (j.get("corp_name"), j.get("stock_code")))
        결산월점검(j, 결산월확인)

    j = _get("list.json", corp_code=고유, bgn_de="%d0101" % (연 - max(해수, 원문해수 + 1)),
             end_de="%d1231" % 연, pblntf_ty="A", page_count=100).json()
    제출 = None
    if _상태(j, "제출이력"):
        낸것.append(_쓰기("dart_제출이력.json", j))
        제출 = j
        for it in (j.get("list") or [])[:10]:
            print("  %s  %s  %s" % (it.get("rcept_dt"), it.get("rcept_no"),
                                    (it.get("report_nm") or "")[:40]))
        for w in 재무기준일점검(제출, 기준일, 평가기준일):
            print("  ※ 경보 — " + w)

    # 전체 재무제표 — 연결과 별도를 둘 다. **요약본이 아니라 fnlttSinglAcntAll 이다**
    for 구분, 딱지 in (("CFS", "연결"), ("OFS", "별도")):
        j = _get("fnlttSinglAcntAll.json", corp_code=고유, bsns_year=str(연),
                 reprt_code=코드, fs_div=구분).json()
        if _상태(j, "전체재무제표(%s)" % 딱지):
            # 머리글을 진단보다 **먼저** 찍는다 — 종전에는 ※※ 가 먼저 나와
            # 별도 진단이 연결 머리글 뒤에 붙어 읽혔다 (2026-09-29 재현 검증)
            print("  전체 재무제표 %s — %d행" % (딱지, len(j.get("list") or [])))
            j = _손익누계표시(j, 코드)
            낸것.append(_쓰기("dart_재무_%s_%d_%s.json" % (딱지, 연, 코드), j))

    j = _get("fnlttSinglAcnt.json", corp_code=고유, bsns_year=str(연),
             reprt_code=코드).json()
    if _상태(j, "주요계정"):
        낸것.append(_쓰기("dart_주요계정_%d_%s.json" % (연, 코드), j))

    # 앵커 시계열 — **몇 해를 받을지 사람이 정하지 않는다.** 규칙이 요구하는 지점
    # (부호 두 번 전환 · 최소 6개 사업연도)까지 스스로 늘어난다. 앵커받기() 주석 참조.
    # **평가기준일이 연중이면 그 해 사업보고서는 아직 없다** — 시작연을 한 해 낮춰
    # 버려질 호출 하나를 아낀다(안전 속도가 빠듯한 API 다).
    시작연 = 연 if 코드 == "11011" else 연 - 1
    앵커, 앵커기록 = 앵커받기(고유, 시작연)
    if 앵커:
        낸것.append(_쓰기("dart_앵커시계열.json",
                        {"고유번호": 고유, "해": 앵커, "받기기록": 앵커기록}))
    # 공시 원문 — 기준일 보고서(정정본 우선) + 최신 사업보고서 + 과거 사업보고서(원문해수 회계연도를 덮을 만큼)
    if 원문받기 and 제출:
        받은 = 원문들받기(제출, 기준일, 원문해수)
        print("  원문 %d건 — %s" % (len(받은), " · ".join("%s(%s)" % x for x in 받은) or "이미 받아 둠"))
        골라 = 원문고르기(제출, 기준일, 원문해수)
        if 코드 != "11011" and not any(d == _보고서딱지[코드] for d, _, _ in 골라):
            print("  ※ **기준일 %s 보고서가 제출이력에 없습니다** — 아직 제출 전이거나 이름이 다릅니다. 기준일 열의 주석(성격별 · "
                  "인건비 · 사업지표 · 약정 한도)이 비게 됩니다" % 이름)
    return 낸것


# ══ 과거 증설 — 램프업을 그 회사 자신의 과거에서 읽는다 ═══════════════
_capex이름 = ("유형자산의 취득", "유형자산의취득", "유형자산 취득",
            "유형자산의 증가", "설비투자", "유형자산취득")


def _현금흐름값(items, 이름들):
    for it in items or []:
        if (it.get("sj_div") or "").strip() != "CF":
            continue
        if (it.get("account_nm") or "").strip() in 이름들:
            s = (it.get("thstrm_amount") or "").replace(",", "").strip()
            if s and s not in ("-", "--"):
                try:
                    return abs(float(s))
                except ValueError:
                    return None
    return None


def 과거증설(앵커파일="_raw/dart_앵커시계열.json"):
    """앵커 시계열에서 **연도별 매출과 CapEx** 를 뽑아 나란히 낸다.

    **왜 있는가 — 램프업을 무엇으로 정할 것인가.**
    증설이 매출이 되기까지 몇 해 걸리는지는 산업마다 다르다. 만들면 바로 팔리는 회사도
    있고(수요 초과 국면의 반도체·전력), 계약·인증을 채워야 하는 회사도 있다
    (데이터센터 임차인·부품 고객 인증). **그것을 지어내지 않고 읽는 순서가 셋이다.**

        ① 회사가 말한다        「2028.1Q 상업운전, 2029년 정상 가동」
                              대개 IR·보도자료에 있다. 웹조사 갈래가 적어 온다
        ② **회사의 과거가 말한다**  ← 이 함수가 그것이다
                              과거에 크게 투자한 해를 찾고 그 뒤 매출이 몇 해 만에
                              올라왔는지 본다. **그 회사 자신의 관측이다**
        ③ 못 구하면 램프를 안 건다  `[1.0]`. 그리고 그것이 낙관 쪽 가정임을 적는다.
                              업계 통상치를 지어내 넣지 않는다

    **앵커에 이미 들어 있는 자료다.** 앵커는 해마다 전체 재무제표를 통째로 받아 두는데
    거기 현금흐름표가 들어 있다 — 매출·원가·판관·영업이익 네 줄만 읽고 CapEx 를
    안 읽고 있었을 뿐이다. 새 호출이 없다.

    낸다: [{사업연도, 매출, CapEx, CapEx비율, 매출증가율}] · 오래된 해부터
    """
    try:
        j = json.load(io.open(앵커파일, encoding="utf-8"))
    except Exception as e:                            # noqa: BLE001
        print("앵커 파일을 못 읽었다 — %s" % e)
        return []
    줄 = []
    for h in sorted(j.get("해") or [], key=lambda x: x["사업연도"]):
        매출 = _매출한해(h["list"])[0]
        capex = _현금흐름값(h["list"], _capex이름)
        줄.append({"사업연도": h["사업연도"], "매출": 매출, "CapEx": capex,
                  "CapEx비율": (capex / 매출) if (매출 and capex) else None})
    for i in range(1, len(줄)):
        앞, 뒤 = 줄[i - 1]["매출"], 줄[i]["매출"]
        줄[i]["매출증가율"] = (뒤 / 앞 - 1) if (앞 and 뒤) else None
    return 줄


def 과거증설보고(앵커파일="_raw/dart_앵커시계열.json"):
    """과거증설() 을 사람이 읽는 표로. 램프업을 정하는 재료다."""
    줄 = 과거증설(앵커파일)
    if not 줄:
        return
    print("── 과거 증설과 그 뒤 매출 (램프업의 재료) ──")
    print("%-6s %18s %18s %9s %9s" % ("사업연도", "매출", "CapEx", "CapEx/매출", "매출증가율"))
    for r in 줄:
        print("%-6d %18s %18s %9s %9s"
              % (r["사업연도"],
                 "{:,.0f}".format(r["매출"]) if r["매출"] else "-",
                 "{:,.0f}".format(r["CapEx"]) if r["CapEx"] else "-",
                 "{:.1%}".format(r["CapEx비율"]) if r["CapEx비율"] else "-",
                 "{:+.1%}".format(r["매출증가율"]) if r.get("매출증가율") is not None else "-"))
    큰해 = [r for r in 줄 if r["CapEx비율"] and r["CapEx비율"] > 0.08]
    if 큰해:
        print("\n  **CapEx/매출이 8%%를 넘은 해 %d개** — %s"
              % (len(큰해), ", ".join(str(r["사업연도"]) for r in 큰해)))
        print("  그 다음 해들의 매출증가율을 보면 **이 회사의 증설이 몇 해 만에 매출이 되는지**가 보인다.")
        print("  바로 오르면 램프가 없는 회사고, 두세 해 걸리면 그 햇수가 램프다.")
    else:
        print("\n  CapEx/매출이 8%를 넘은 해가 없다 — 관측 기간에 대형 증설이 없었다는 뜻이다.")
        print("  **이 회사의 과거로는 램프업을 읽을 수 없다.** 회사 발언에 기대거나, 없으면 [1.0] 으로 두고 적는다.")


# ══ 공시 원문 ═════════════════════════════════════════════════════════════
def _태그벗기기(h):
    h = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?i)<br\s*/?>", "\n", h)
    h = re.sub(r"(?i)</(p|div|tr|table|h\d)>", "\n", h)
    h = re.sub(r"(?i)</t[dh]>", "\t", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    for a, b in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"),
                 ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'")):
        h = h.replace(a, b)
    h = re.sub(r"[ \t]+\n", "\n", h)
    h = re.sub(r"\n{3,}", "\n\n", h)
    return re.sub(r"[ ]{2,}", " ", h).strip()


def _뷰어우회(접수번호, 딱지):
    """DART 공시뷰어에서 절 단위로 받는다 — `document.xml` 이 막혔을 때만 부른다.

    **`딱지`(폴더 이름)를 넘긴다. 접수번호가 아니다.** 옛 판은 접수번호를 넘겨
    뷰어 도구가 접수번호 이름의 폴더를 찾다가 실패했다(한화오션 회차에서 잡혔다).
    """
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import dart_뷰어원문 as V                              # noqa: PLC0415
    except Exception as e:                                    # noqa: BLE001
        sys.stderr.write("뷰어 우회 도구를 못 불렀습니다 — %s\n" % e)
        return []
    try:
        낸것 = V.받기(딱지, 접수번호=접수번호)
    except Exception as e:                                    # noqa: BLE001
        sys.stderr.write("뷰어 우회도 실패했습니다 — %s\n" % e)
        return []
    print("  ※ document.xml 이 막혀 **뷰어 경로**로 받았습니다 — 같은 공시 원문입니다 "
          "(절 %d개)" % len(낸것 or []))
    return 낸것 or []


def 원문(접수번호, 딱지):
    """공시 원문 zip 을 받아 풀고 텍스트로 옮긴다. **주석은 여기에만 있다.**

    **`document.xml` 이 막히면 뷰어 경로로 스스로 넘어간다.**
    실측(씨젠 회차, 2026-08-28): 이 엔드포인트가 회차 내내 `status 800`(시스템 점검)을
    돌려주었다 — 네 번 재시도 모두 실패. 같은 키로 `company.json` 등 다른 엔드포인트는
    정상이었으니 키·한도 문제가 아니라 **그 엔드포인트만 막힌 것**이다.
    주석(리스·이자비용·성격별 비용·이연법인세·**이월결손금**)은 원문에만 있으므로
    여기서 멈추면 회차가 통째로 막힌다. 그래서 **DART 공시뷰어에서 절 단위로 받는
    우회 경로**(`dart_뷰어원문.py`)로 넘어간다. **같은 공시 원문이다** — 포털·뉴스에서
    옮겨 적는 것이 아니다.
    """
    낼곳 = os.path.join(RAW, 딱지)
    os.makedirs(낼곳, exist_ok=True)
    try:
        r = _get("document.xml", rcept_no=접수번호)
    except Exception as e:                                    # noqa: BLE001
        sys.stderr.write("document.xml 호출 실패(%s) — 뷰어 경로로 넘어갑니다\n" % e)
        return _뷰어우회(접수번호, 딱지)
    if r.content[:2] != b"PK":
        머리 = r.content[:200]
        try:
            if (json.loads(r.content.decode("utf-8", "ignore")) or {}).get("status") == "020":
                raise 한도초과("document.xml %s — 일일 한도 초과(020)" % 접수번호)
        except ValueError:
            pass
        점검 = b"800" in 머리 or "시스템 점검".encode("utf-8") in 머리
        sys.stderr.write("원문이 zip 이 아닙니다%s — 뷰어 경로로 넘어갑니다. 앞머리: %r\n"
                         % ("(시스템 점검으로 보입니다)" if 점검 else "", 머리[:120]))
        return _뷰어우회(접수번호, 딱지)
    낸것 = []
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        for n in z.namelist():
            바이트 = z.read(n)
            p = os.path.join(낼곳, os.path.basename(n))
            with open(p, "wb") as f:
                f.write(바이트)
            낸것.append(p)
            if n.lower().endswith((".xml", ".html", ".htm")):
                글 = None
                for 인코딩 in ("utf-8", "cp949", "euc-kr"):
                    try:
                        글 = 바이트.decode(인코딩)
                        break
                    except Exception:
                        continue
                if 글:
                    t = p.rsplit(".", 1)[0] + ".txt"
                    io.open(t, "w", encoding="utf-8").write(_태그벗기기(글))
                    낸것.append(t)
    print("원문 %s — 파일 %d개 → %s" % (접수번호, len(낸것), 낼곳))
    return 낸것


# ══ 신고서 — 발행공시(C)의 증권신고서(지분증권) · 투자설명서 · 분할회사 잇기 (2026-10-25 Y1) ══════════════
# 왜 — 정기보고서(A)에 연간 재무가 3해 미만인 회사(상장 직후 · 분할 신설)의 **감사받은 연간 재무**는 신고서 · 투자설명서와 분할회사 공시에 있다.
#   이 파일은 정기공시만 받았다(설계 `연구/재무이력없음_20261025/02_설계.md` 2-1). `--신고서` 를 주면 그 서류를 원문으로 받고
#   무엇을 왜 받았는지 `_raw/dart_신고서고르기.json` 에 적는다. 읽기(표준 줄 · 근거 · 검산)는 `신고서재무_국내.py` 가 한다.
# 고르는 규칙(회사 · 업종 이름 없이)
#   · 묶음 — 원 신고서가 묶음을 열고, 같은 종류의 정정([기재정정] · [발행조건확정])과 그 뒤 투자설명서(정정 포함)가 그 묶음에 붙는다
#   · 확정 판 — 기준일 앞에서 투자설명서 마지막 판 > 신고서 정정 마지막 판 > 원 신고서. 첨부만 바꾼 정정([첨부정정] · [첨부추가])과
#     감독원의 [정정제출요구] 단독 공시는 고르지 않는다
#   · 대상 자신의 증권신고서(지분증권)가 있으면 그 마지막 묶음의 확정 판 하나
#   · 없고 대상이 분할로 생긴 회사면 **분할회사를 원문에서 찾아 잇는다** — 대상 사업보고서 원문의 분할 문장(「○○㈜에서 인적분할되어」 ·
#     「분할회사인 ○○」)에서 이름을 뽑아 고유번호 대조표(corpCode) 이름과 **정확히**(㈜ · (주) · 주식회사 · 빈칸만 떼고) 대 본다.
#     가장 많이 가리킨 이름이 하나일 때만 잇고, 동률이거나 같은 이름의 회사가 여럿이면 멈추고 후보를 적는다(`--분할회사 <고유번호>` 로 사람이 준다).
#     이은 뒤 그 회사의 증권신고서(분할) 묶음 확정 판(분할기일 앞) + 분할기일이 든 해의 사업보고서(감사보고서 주석의 분할 · 중단영업)를 받는다
신고서고르기파일 = "dart_신고서고르기.json"
신고서폴더 = "신고서"
_정정꼬리표 = ("기재정정", "발행조건확정", "정정", "첨부정정", "첨부추가", "정정제출요구")


def 공시제목(제목):
    """「[기재정정]증권신고서(지분증권)」 → ("증권신고서(지분증권)", ["기재정정"]) — 빈칸을 뗀 몸과 앞 꼬리표들."""
    t = re.sub(r"\s+", "", 제목 or "")
    머 = re.match(r"^((?:\[[^\]]*\])*)", t).group(1)
    return t[len(머):], re.findall(r"\[([^\]]*)\]", 머)


def 신고서종류(몸):
    """제목 몸 → 「증권신고서(지분증권)」 · 「증권신고서(분할)」 · 「투자설명서」 · 「기타신고서」(묶음을 가르기만 한다) · None.
    「투자설명서(일괄신고)」 · 「일괄신고서」 · 「소액공모공시서류」 · 「증권발행실적보고서」 는 None(묶음 밖)."""
    if 몸 in ("증권신고서(지분증권)", "증권신고서(분할)", "투자설명서"):
        return 몸
    if 몸.startswith("증권신고서("):
        return "기타신고서"
    return None


def 신고서묶음(목록, 기준일=None):
    """발행공시 목록(list.json 항목) → 묶음 [{"종류", "원": 항목 | None, "판": [항목 …](접수 차례)}]. 기준일 뒤 공시는 뺀다."""
    끝 = (기준일 or "9999-12-31").replace("-", "")
    묶음들, 지금 = [], None
    for it in sorted(목록 or [], key=lambda z: z.get("rcept_no") or ""):
        if (it.get("rcept_dt") or "") > 끝:
            continue
        몸, 표 = 공시제목(it.get("report_nm"))
        종 = 신고서종류(몸)
        if not 종:
            continue
        if 종 == "투자설명서":
            if 지금 is not None:
                지금["판"].append(it)
            continue
        정정 = any(k in 표 for k in _정정꼬리표)
        if 정정 and 지금 is not None and 지금["종류"] == 종:
            지금["판"].append(it)
            continue
        지금 = {"종류": 종, "원": None if 정정 else it, "판": [it]}
        묶음들.append(지금)
    return 묶음들


def 확정판(묶음):
    """묶음 → (항목 | None, 까닭) — 투자설명서 마지막 판 > 신고서 정정 마지막 판 > 원 신고서. 첨부 정정 · 정정제출요구 단독은 건너뛴다."""
    def 고를만(it):
        _몸, 표 = 공시제목(it.get("report_nm"))
        if any(k in 표 for k in ("첨부정정", "첨부추가")):
            return False
        if "정정제출요구" in 표 and not any(k in 표 for k in ("기재정정", "발행조건확정")):
            return False
        return True
    판 = [it for it in 묶음.get("판") or [] if 고를만(it)]
    설명 = [it for it in 판 if 공시제목(it.get("report_nm"))[0] == "투자설명서"]
    if 설명:
        return 설명[-1], "투자설명서 마지막 판(묶음 판 %d개 가운데)" % len(묶음.get("판") or [])
    신고 = [it for it in 판 if 공시제목(it.get("report_nm"))[0] != "투자설명서"]
    if 신고:
        return 신고[-1], ("신고서 정정 마지막 판" if 공시제목(신고[-1].get("report_nm"))[1] else "원 신고서") + "(투자설명서 없음)"
    return None, "고를 판 없음(첨부 정정 · 정정제출요구뿐)"


def 이름맞춤(s):
    """회사 이름 대조 꼴 — ㈜ · (주) · 주식회사 · (유) · 유한회사 · 빈칸 · 쉼표 · 마침표를 떼고 소문자로(수시공시 상장 명부와 같은 꼴)."""
    s = re.sub(r"\(주\)|㈜|주식회사|\(유\)|유한회사|\s+|,|\.", "", s or "")
    return s.lower()


def 이름표(뿌리=None):
    """corpCode → {맞춘 이름: [(고유번호, 종목코드, 이름) …]} — 비상장 포함(분할회사가 비상장일 수 있다). 공용 캐시 → `_dartcache` → 받기."""
    if 뿌리 is None:
        공용 = os.environ.get("DCF_공용캐시") or os.environ.get("DCF_SHARED_CACHE") or os.path.join(os.path.expanduser("~"), ".dcf캐시")
        p = os.path.join(공용, "원천", "_dartcache", "corpCode.xml")
        뿌리 = ET.parse(p).getroot() if os.path.exists(p) else 고유번호표()
    표 = {}
    for e in 뿌리.iter("list"):
        n = (e.findtext("corp_name") or "").strip()
        표.setdefault(이름맞춤(n), []).append(((e.findtext("corp_code") or "").strip(), (e.findtext("stock_code") or "").strip(), n))
    return 표


# 분할 문장 — 「분할 전 ○○㈜에서 인적 분할되어」 · 「○○(주)(이하 "분할회사")에서 단순ㆍ인적분할되어」 · 「○○㈜부터 인적분할의 방법으로」 ·
# 「분할회사인 ○○㈜」 · 「분할존속회사인 ○○(주)」. 이름 칸은 빈칸 없는 한 덩이 — 앞에 「주식회사」 가 붙는 꼴도 받는다
_이름칸 = r"(?:주식회사\s*)?([0-9A-Za-z가-힣&·\-]{2,30}?)\s*(?:㈜|\(주\)|주식회사)?"
_분할문장 = [
    re.compile(_이름칸 + r"\s*(?:\(이하[^)]{0,30}\)\s*)?(?:에서|으로부터|로부터|부터)\s*(?:단순\s*[ㆍ·]?\s*)?(?:인적|물적)\s*분할"),
    re.compile(r"분할(?:존속)?회사(?:인|은|는|:)\s*(?:주식회사\s*)?([0-9A-Za-z가-힣&·\-]{2,30}?)\s*(?:㈜|\(주\)|주식회사|(?=[의은는이가을를와과,.\s)]|$))"),
]
_이름아님 = {"당사", "회사", "지배기업", "연결실체", "분할회사", "분할존속회사", "분할신설회사", "존속회사", "신설회사", "동사", "이사회", "주주총회"}


def 분할문장들(글들):
    """[(출처, 문단)] → 분할 문장이 든 [(출처, 문단)] (「분할」 과 「설립 · 신설 · 분할회사 · 분할존속」 이 함께 든 문단)."""
    return [(s, t) for s, t in 글들 if "분할" in t and re.search(r"설립|신설|분할회사|분할존속", t)]


def 분할회사찾기(글들, 대상이름, 표):
    """분할 문장들 → {"판정": "이음" | "후보 여럿" | "없음", "고유번호", "이름", "종목코드", "후보": [{맞춘이름 · 표수 · 회사}], "문장": [근거]}.
    이름을 corpCode 의 맞춘 이름과 **정확히** 대 본다(부분 문자열로 대지 않는다). 대상 자신 · 일반 낱말은 뺀다."""
    대상 = 이름맞춤(대상이름)
    셈, 문장 = {}, {}
    for 출처, t in 분할문장들(글들):
        for 꼴 in _분할문장:
            for m in 꼴.finditer(t):
                k = 이름맞춤(m.group(1))
                if len(k) < 2 or k == 대상 or k in _이름아님 or k not in 표:
                    continue
                셈[k] = 셈.get(k, 0) + 1
                if len(문장.setdefault(k, [])) < 3:
                    a = max(0, m.start() - 20)
                    문장[k].append({"출처": 출처, "글": t[a:m.end() + 30]})
    if not 셈:
        return {"판정": "없음", "후보": [], "문장": []}
    후보 = []
    for k, n in sorted(셈.items(), key=lambda kv: -kv[1]):
        회사들 = 표[k]
        상장 = [c for c in 회사들 if c[1]]
        고른 = 상장 if len(상장) == 1 else (회사들 if len(회사들) == 1 else None)
        후보.append({"맞춘이름": k, "표수": n, "회사": [{"고유번호": c[0], "종목코드": c[1], "이름": c[2]} for c in 회사들][:5],
                    "하나": ({"고유번호": 고른[0][0], "종목코드": 고른[0][1], "이름": 고른[0][2]} if 고른 else None)})
    if len(후보) > 1 and 후보[0]["표수"] == 후보[1]["표수"]:
        return {"판정": "후보 여럿", "까닭": "가리킨 횟수가 같은 이름이 둘 이상", "후보": 후보, "문장": [문장[c["맞춘이름"]] for c in 후보[:2]]}
    첫 = 후보[0]
    if not 첫["하나"]:
        return {"판정": "후보 여럿", "까닭": "같은 이름의 회사가 corpCode 에 여럿", "후보": 후보, "문장": 문장[첫["맞춘이름"]]}
    return dict({"판정": "이음", "후보": 후보, "문장": 문장[첫["맞춘이름"]]}, **첫["하나"])


def 분할기일찾기(글들):
    """「2024년 3월 1일을 분할기일로」 · 「분할기일인 2024년 3월 1일」 → ISO 날짜(여럿이면 가장 많이 나온 것) | None."""
    셈 = {}
    날 = r"(20\d\d)\s*[년.]\s*(\d{1,2})\s*[월.]\s*(\d{1,2})\s*일?"
    for _s, t in 글들:
        for m in list(re.finditer(날 + r"\s*(?:을|를)?\s*분할\s*기일", t)) + list(re.finditer(r"분할\s*기일\s*(?:인|은|:|：)?\s*" + 날, t)):
            try:
                d = "%04d-%02d-%02d" % (int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                continue
            셈[d] = 셈.get(d, 0) + 1
    return max(셈.items(), key=lambda kv: kv[1])[0] if 셈 else None


def _공시목록(고유, 시작, 끝, 종류):
    """list.json — 한 회사 · 한 공시 종류 · 쪽을 넘기며. 020 이면 한도초과. → 항목 목록."""
    낸, 쪽 = [], 1
    while True:
        j = _get("list.json", corp_code=고유, bgn_de=시작, end_de=끝, pblntf_ty=종류, page_no=쪽, page_count=100).json()
        s = (j or {}).get("status")
        if s == "020":
            raise 한도초과("list.json %s %s" % (고유, 종류))
        if s == "013":
            return 낸
        if s not in (None, "000"):
            sys.stderr.write("list.json %s %s — status %s\n" % (고유, 종류, s))
            return 낸
        낸 += j.get("list") or []
        if 쪽 >= int(j.get("total_page") or 1):
            return 낸
        쪽 += 1


def _공시목록캐시(고유, 시작, 끝, 종류):
    """`_raw/dart_공시목록_<종류>_<고유>.json` 이 같은 창이면 다시 부르지 않는다(캐시 먼저). → (목록, 캐시였나)."""
    p = os.path.join(RAW, "dart_공시목록_%s_%s.json" % (종류, 고유))
    if os.path.exists(p):
        j = json.load(io.open(p, encoding="utf-8"))
        if j.get("시작") == 시작 and j.get("끝") == 끝:
            return j.get("list") or [], True
    목 = _공시목록(고유, 시작, 끝, 종류)
    _쓰기(p, {"고유번호": 고유, "종류": 종류, "시작": 시작, "끝": 끝, "list": 목})
    return 목, False


def _신고서원문(접수):
    """`_raw/신고서/<접수번호>/` 에 원문 — 이미 있으면 받지 않는다. → (폴더 상대경로, 이번에 받았나)."""
    딱지 = os.path.join(신고서폴더, 접수)
    if os.path.exists(os.path.join(RAW, 딱지, 접수 + ".xml")):
        return "_raw/%s/%s" % (신고서폴더, 접수), False
    원문(접수, 딱지)
    return "_raw/%s/%s" % (신고서폴더, 접수), True


def 대상분할글들(raw=None):
    """대상 사업보고서 원문(`<raw>/사업YYYY/*.xml`)의 문단과 표 줄 가운데 「분할」 이 든 것 → [(출처, 글)] — 분할 문장을 찾는 재료."""
    import glob as _g                                          # noqa: PLC0415
    import 공시표 as _표                                       # noqa: PLC0415
    raw = raw or RAW
    낸 = []
    for p in sorted(_g.glob(os.path.join(raw, "사업*", "*.xml")), reverse=True):
        문 = _표.읽기(p)
        if not 문:
            continue
        이름 = "%s/%s" % (os.path.basename(os.path.dirname(p)), os.path.basename(p))
        for 경로, t in 문["글"]:
            if "분할" in t:
                낸.append(("%s · %s" % (이름, " > ".join(경로[-2:])), t))
        for 표 in 문["표"]:                                        # 연혁 표 칸(「2024.03 ○○㈜에서 인적분할」 꼴)
            for r in 표["격자"]:
                t = " ".join(dict.fromkeys(c for c in r if c))
                if "분할" in t and len(t) < 400:
                    낸.append(("%s · 표 %d" % (이름, 표["번호"]), t))
    return 낸


def 신고서받기(고유, 기준일, 분할회사=None, 조회일=None, 평가기준일=None):
    """발행공시(C)의 신고서 · 투자설명서를 고르고 원문으로 받는다. 대상 자신의 것이 없고 분할로 생긴 회사면 분할회사를 잇는다.
    기록은 `_raw/dart_신고서고르기.json`(「신고서고르기/1」). 일일 한도(020)면 그 자리에서 멈추고 남은 일을 기록에 적는다 → 기록 dict."""
    import datetime as _dt                                     # noqa: PLC0415
    시작호출 = 호출수
    기 = _dt.date.fromisoformat(기준일)
    기록 = {"형식": "신고서고르기/1", "대상": {"고유번호": 고유}, "평가기준일": 평가기준일 or 기준일, "재무기준일": 기준일,
           "조회일": 조회일 or _dt.date.today().isoformat(), "서류": [], "대상발행공시": None, "분할": None,
           "남은받기": [], "한도초과": None, "경보": [], "호출": 0}
    할일 = []

    def 서류(종류, 역할, it, 제출인, 까닭, 묶음=None):
        폴더, 받음 = _신고서원문(it["rcept_no"])
        기록["서류"].append({"종류": 종류, "역할": 역할, "접수번호": it["rcept_no"], "보고서명": (it.get("report_nm") or "").strip(),
                          "제출인": 제출인, "제출일": "%s-%s-%s" % (it["rcept_dt"][:4], it["rcept_dt"][4:6], it["rcept_dt"][6:8]),
                          "원문": 폴더, "이번에받음": 받음, "고른까닭": 까닭,
                          "묶음": ({"원신고서": (묶음.get("원") or {}).get("rcept_no"), "판수": len(묶음.get("판") or []),
                                   "판": [x["rcept_no"] + " " + (x.get("report_nm") or "").strip() for x in 묶음.get("판") or []]}
                                  if 묶음 else None)})
    try:
        할일 = ["기업개황", "대상 발행공시 목록", "대상 신고서 고르기 · 원문"]
        p = os.path.join(RAW, "dart_기업개황.json")
        개 = json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else None
        if not 개:
            j = _get("company.json", corp_code=고유).json()
            if (j or {}).get("status") == "020":
                raise 한도초과("company.json %s" % 고유)
            if _상태(j, "기업개황"):
                개 = j
                _쓰기("dart_기업개황.json", j)
        개 = 개 or {}
        대상 = {"이름": 개.get("corp_name"), "식별": 고유}
        기록["대상"] = {"고유번호": 고유, "이름": 개.get("corp_name"), "종목코드": 개.get("stock_code"), "설립일": 개.get("est_dt")}
        할일.pop(0)
        목, 캐시 = _공시목록캐시(고유, "%d0101" % (기.year - 7), 기준일.replace("-", ""), "C")
        할일.pop(0)
        묶음들 = 신고서묶음(목, 기준일)
        기록["대상발행공시"] = {"건수": len(목), "캐시": 캐시, "묶음": [{"종류": b["종류"], "판": len(b["판"]),
                                                              "첫접수": b["판"][0]["rcept_no"]} for b in 묶음들]}
        지분 = [b for b in 묶음들 if b["종류"] == "증권신고서(지분증권)"]
        if 지분 and not 분할회사:
            b = 지분[-1]
            it, 까닭 = 확정판(b)
            if it:
                서류(공시제목(it["report_nm"])[0], "대상 신고서", it, 대상,
                   "대상 자신의 증권신고서(지분증권) 묶음(첫 접수 %s · 묶음 %d개 가운데 마지막) — %s" % (b["판"][0]["rcept_no"], len(지분), 까닭), b)
            if len(지분) > 1:
                기록["경보"].append("증권신고서(지분증권) 묶음이 %d개 — 마지막 묶음만 받았다(앞 묶음 첫 접수: %s). 상장 공모가 앞 묶음이면 "
                                  "그 확정 판 접수번호로 `--원문` 을 받는다" % (len(지분), " · ".join(x["판"][0]["rcept_no"] for x in 지분[:-1])))
            할일.pop(0)
            return 기록
        할일 = ["대상 분할 문장(사업보고서 원문)", "분할회사 발행공시 목록", "분할 신고서 원문", "분할회사 정기공시 목록", "분할회사 사업보고서 원문"]
        if not 지분:
            기록["경보"].append("대상 자신의 증권신고서(지분증권)가 기준일 앞 7년 창에 없다(발행공시 %d건)" % len(목))
        글들 = 대상분할글들()
        if not 글들:                                                        # 대상 사업보고서 원문이 없으면 가장 최근 하나를 받는다(분할기일도 여기서 읽는다)
            목A, _ = _공시목록캐시(고유, "%d0101" % (기.year - 3), 기준일.replace("-", ""), "A")
            사 = [x for x in 목A if re.search(r"사업보고서\s*\(\d{4}\.", x.get("report_nm") or "")]
            if 사:
                x = max(사, key=lambda z: z["rcept_no"])
                원문(x["rcept_no"], "사업%s" % re.search(r"\((\d{4})\.", x["report_nm"]).group(1))
                글들 = 대상분할글들()
        분할기일 = 분할기일찾기(글들)
        if 분할회사:
            찾은 = [c for v in 이름표().values() for c in v if c[0] == 분할회사]
            판정 = {"판정": "이음", "방법": "사람이 준 고유번호(--분할회사)", "고유번호": 분할회사,
                  "이름": 찾은[0][2] if 찾은 else None, "종목코드": 찾은[0][1] if 찾은 else None, "후보": [], "문장": []}
        else:
            판정 = 분할회사찾기(글들, 개.get("corp_name"), 이름표())
            판정["방법"] = "대상 사업보고서 원문의 분할 문장 → 이름 → corpCode 정확 일치(분할 문장 %d개)" % len(분할문장들(글들))
        판정["분할기일"] = 분할기일
        기록["분할"] = 판정
        할일.pop(0)
        if 판정["판정"] != "이음":
            기록["경보"].append(("분할회사를 잇지 못했다(%s) — 후보를 보고 `--분할회사 <고유번호>` 로 준다" % 판정.get("까닭"))
                              if 판정["판정"] == "후보 여럿" else
                              "대상 사업보고서 원문에 분할 문장이 없다 — 분할 신설 회사가 아니거나 원문이 없다(받을 신고서 없음)")
            할일 = []
            return 기록
        분고 = 판정["고유번호"]
        분할인 = {"이름": 판정.get("이름"), "식별": 분고}
        끝일 = (분할기일 or 기준일).replace("-", "")
        목2, _ = _공시목록캐시(분고, "%d0101" % (int(끝일[:4]) - 2), 끝일, "C")
        할일.pop(0)
        분묶 = [b for b in 신고서묶음(목2, 분할기일 or 기준일) if b["종류"] == "증권신고서(분할)"]
        if 분묶:
            b = 분묶[-1]
            it, 까닭 = 확정판(b)
            if it:
                서류(공시제목(it["report_nm"])[0], "분할 신고서", it, 분할인,
                   "분할회사의 증권신고서(분할) 묶음(첫 접수 %s · 분할기일 %s 앞 마지막 묶음) — %s" % (b["판"][0]["rcept_no"], 분할기일, 까닭), b)
        else:
            기록["경보"].append("분할회사 %s 의 증권신고서(분할)가 분할기일 앞 2년 창에 없다" % 분고)
        할일.pop(0)
        if not 분할기일:
            기록["경보"].append("분할기일을 원문에서 못 찾았다 — 분할회사 사업보고서를 고르지 않았다")
            할일 = []
            return 기록
        y = int(분할기일[:4])
        목3, _ = _공시목록캐시(분고, "%d0101" % (y + 1), "%d1231" % (y + 1), "A")
        할일.pop(0)
        사 = [x for x in 목3 if re.search(r"사업보고서\s*\(%d\.\d{2}\)" % y, x.get("report_nm") or "")]
        if 사:
            x = max(사, key=lambda z: z["rcept_no"])
            서류("분할회사 사업보고서", "분할회사 사업보고서", x, 분할인,
               "분할기일 %s 이 든 해(%d)의 분할회사 사업보고서(정정이 있으면 늦은 판) — 첨부 감사보고서 주석에 분할 · 중단영업" % (분할기일, y))
        else:
            기록["경보"].append("분할회사 %s 의 %d 사업보고서가 목록에 없다" % (분고, y))
        할일.pop(0)
        return 기록
    except 한도초과 as e:
        기록["한도초과"] = str(e)
        기록["남은받기"] = list(할일)
        sys.stderr.write("[멈춤] 일일 한도 초과(020) — %s · 남은 일 %d개를 `_raw/%s` 에 적었다\n" % (e, len(할일), 신고서고르기파일))
        return 기록
    finally:
        기록["호출"] = 호출수 - 시작호출
        _쓰기(신고서고르기파일, 기록)


def _신고서보고(기):
    print("신고서 — 호출 %d · 서류 %d%s" % (기.get("호출") or 0, len(기.get("서류") or []),
                                     " · 한도 초과로 멈춤(남은 일: %s)" % " · ".join(기["남은받기"]) if 기.get("한도초과") else ""))
    for d in 기.get("서류") or []:
        print("  %s  %s  %s  (%s)" % (d["접수번호"], d["역할"], d["보고서명"][:30], (d["제출인"] or {}).get("이름")))
    분 = 기.get("분할") or {}
    if 분:
        print("  분할회사 — %s %s %s · 분할기일 %s" % (분.get("판정"), 분.get("고유번호") or "", 분.get("이름") or "", 분.get("분할기일")))
    for w in 기.get("경보") or []:
        print("  ※ " + w)
    print("  기록 `_raw/%s` — 읽기는 `python 스크립트/신고서재무_국내.py --raw _raw --기준일 %s`" % (
        신고서고르기파일, 기.get("재무기준일") or 기.get("평가기준일")))


def _보고기간끝(report_nm):
    """「반기보고서 (2026.06)」 → '2026-06-30'(그달 말일) | None."""
    import calendar as _cal                                    # noqa: PLC0415
    m = re.search(r"\((\d{4})\.(\d{2})\)", report_nm or "")
    if not m:
        return None
    y, mo = int(m.group(1)), int(m.group(2))
    return "%04d-%02d-%02d" % (y, mo, _cal.monthrange(y, mo)[1])


def 재무기준일점검(제출, 기준일, 평가기준일):
    """제출이력(list.json 정기공시 A)으로 재무기준일 F 를 평가기준일 T 와 대 본다 → 경보 글 목록(T 가 없거나 F = T 면 빈 목록).
    규칙은 `기준일인자.재무기준일점검` 하나다(F 의 보고가 T 뒤 제출 · T 전에 더 늦은 분기 보고 제출)."""
    if not 평가기준일 or 평가기준일 == 기준일:
        return []
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import 기준일인자                                         # noqa: PLC0415
    보고들 = []
    for it in (제출 or {}).get("list") or []:
        nm = it.get("report_nm") or ""
        if not re.search(r"(사업|반기|분기)보고서", nm):
            continue
        끝 = _보고기간끝(nm)
        if 끝:
            보고들.append({"기간끝": 끝, "제출일": it.get("rcept_dt"), "이름": "%s %s" % (nm.strip(), it.get("rcept_no") or "")})
    return 기준일인자.재무기준일점검(기준일, 평가기준일, 보고들)


def _본체면멈춘다(뿌리):
    """**본체에서 원본을 받으면 정본이 더러워진다.** 회차 폴더에서 돌린다 — 판정은 `본체가드.py`(폴더 이름 「시작키트」 ·
    저장소 안의 회귀기준선 본체). 종전에는 이름 「시작키트」만 봐서 개발 저장소의 본체(`구현/키트`)가 막히지 않았다(S1 리뷰)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import 본체가드                                          # noqa: PLC0415
    본체가드.본체면멈춘다(뿌리)


def main():
    _본체면멈춘다(ROOT)
    _준비()
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--찾기", help="회사명 부분일치로 고유번호 찾기")
    ap.add_argument("--회사", help="고유번호(8자리)")
    ap.add_argument("--기준일", "--재무기준일", dest="기준일",
                    help="재무기준일 F YYYY-MM-DD — 받을 정기보고서 · 재무 · 원문 · 신고서 창의 날(평가기준일 전에 제출된 마지막 분기말). "
                         "옛 이름 --기준일 은 지금 뜻 그대로다")
    ap.add_argument("--평가기준일", default=None,
                    help="평가기준일 T YYYY-MM-DD(분석일) — 받기는 바꾸지 않는다. 수시공시 창의 끝 · 재무기준일 점검(경보)에만 쓴다")
    ap.add_argument("--가정", default=None, help="가정 파일 — 날짜 인자를 비우면 기준일.py 로 F · T 를 푼다(F 가 없으면 F = T)")
    ap.add_argument("--해수", type=int, default=4,
                    help="제출이력을 몇 해 거슬러 받을지. **앵커는 이것으로 정하지 않는다** — "
                         "규칙이 요구하는 지점까지 스스로 늘어난다")
    ap.add_argument("--앵커만", action="store_true",
                    help="앵커 시계열만 늘린다. 이미 받아 둔 해는 다시 받지 않고 "
                         "_raw/ 의 다른 파일도 건드리지 않는다")
    ap.add_argument("--원문", nargs=2, metavar=("접수번호", "딱지"))
    ap.add_argument("--과거증설", action="store_true",
                    help="앵커에서 연도별 매출·CapEx 를 뽑아 램프업의 재료로 낸다")
    ap.add_argument("--원문해수", type=int, default=6,
                    help="통째로 받을 때 원문(사업보고서)이 덮을 회계연도 수(기본 6 — 하나가 두 해를 준다). 0 이면 기준일 · 최신만")
    ap.add_argument("--원문없이", action="store_true", help="통째로 받을 때 공시 원문을 받지 않는다(API 만)")
    ap.add_argument("--앵커끝까지", action="store_true",
                    help="--앵커만 과 함께 — 전부 흑자 · 이익률이 고르더라도 여섯 해에서 멈추지 않고 자료가 마를 때까지(상한 --앵커상한) 받는다. "
                         "고른 고마진 여섯 해가 사이클 정점 국면일 수 있는 유형(경기순환 · 원자재 표지 — 자체검사 ⑧ 이 경보로 부른다)에서 쓴다")
    ap.add_argument("--앵커상한", type=int, default=15, help="앵커를 거슬러 받는 최대 해 수(기본 15)")
    ap.add_argument("--결산월확인", action="store_true",
                    help="결산월(acc_mt)이 12 가 아닌 회사를 사람이 확인했다 — 멈추지 않고 진행한다")
    ap.add_argument("--수시공시", action="store_true",
                    help="통째로 받은 뒤 주요사항 · 거래소 · 발행 공시(B · I · C)와 상장 종속회사 공시도 받아 `_raw/수시공시.json` 을 짓는다"
                         "(`수시공시.py` — 기준일 앞 5년 · 일일 한도 020 이면 멈추고 남은 받기를 적는다)")
    ap.add_argument("--신고서", action="store_true",
                    help="통째로 받은 뒤 발행공시(C)의 증권신고서(지분증권) · 투자설명서 확정 판을 원문으로 받는다 — 대상 자신의 것이 없고 분할로 "
                         "생긴 회사면 분할회사를 원문에서 찾아 그 회사의 증권신고서(분할) · 분할 해 사업보고서를 받는다. 기록 "
                         "`_raw/dart_신고서고르기.json` · 읽기는 `신고서재무_국내.py`")
    ap.add_argument("--신고서만", action="store_true",
                    help="--신고서 와 같되 통째 받기(재무 API · 앵커 · 정기 원문)를 건너뛴다 — 분할 문장이 필요하면 최근 사업보고서 원문 하나만 받는다")
    ap.add_argument("--분할회사", default=None, metavar="고유번호",
                    help="--신고서 · --신고서만 과 함께 — 분할회사 고유번호(8자리)를 사람이 준다(원문에서 찾지 않는다)")
    a = ap.parse_args()
    if a.가정 or a.평가기준일:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import 기준일인자                                     # noqa: PLC0415
        a.기준일 = 기준일인자.풀기(a.기준일, a.가정, 기준일인자.재무, 인자="--기준일")
        a.평가기준일 = 기준일인자.풀기(a.평가기준일, a.가정, 기준일인자.평가, 인자="--평가기준일")

    if a.찾기:
        낸것 = 찾기(a.찾기)
        _쓰기("dart_찾기_%s.json" % a.찾기, {"질의": a.찾기, "결과": 낸것})
        print("「%s」 — %d곳" % (a.찾기, len(낸것)))
        for h in 낸것[:20]:
            print("  %s  %-24s %s  (정보갱신 %s)"
                  % (h["고유번호"], h["회사명"][:24],
                     h["종목코드"] or "(비상장·폐지)", h["정보갱신일"]))
        if len(낸것) > 20:
            print("  … 그 밖 %d곳" % (len(낸것) - 20))
        print("\n※ 종목코드가 비어 있으면 비상장이거나 상장폐지다. "
              "정보갱신일은 상장 상태가 아니라 정보를 고친 날이다 — 그것으로 살아 있는지 판정하지 않는다.")
        return 0

    if a.과거증설:
        과거증설보고()
        return 0

    if a.원문:
        원문(a.원문[0], a.원문[1])
        return 0

    if a.앵커만:
        if not (a.회사 and a.기준일):
            return ap.print_help() or 2
        # **`통째로()` 를 다시 부르면 기업개황·제출이력·재무제표를 전부 다시 받아
        # `_raw/` 를 덮는다.** 앵커만 늘리려고 그럴 수는 없어서 이 길을 낸다.
        연, 코드, _ = _직전보고서(a.기준일)
        경로 = os.path.join(RAW, "dart_앵커시계열.json")
        기존 = []
        if os.path.exists(경로):
            기존 = (json.load(io.open(경로, encoding="utf-8")) or {}).get("해") or []
            print("이미 받아 둔 해 %d개 — 다시 받지 않습니다: %s"
                  % (len(기존), ", ".join(str(h["사업연도"]) for h in 기존)))
        앵커, 앵커기록 = 앵커받기(a.회사, 연 if 코드 == "11011" else 연 - 1, 기존, 상한=a.앵커상한, 흑자멈춤=not a.앵커끝까지)
        if 앵커:
            _쓰기("dart_앵커시계열.json",
                 {"고유번호": a.회사, "해": 앵커, "받기기록": 앵커기록})
        return 0

    if a.신고서만:
        if not (a.회사 and a.기준일):
            return ap.print_help() or 2
        기 = 신고서받기(a.회사, a.기준일, a.분할회사, 평가기준일=a.평가기준일)
        _신고서보고(기)
        return 1 if 기.get("한도초과") else 0

    if a.회사 and a.기준일:
        낸것 = 통째로(a.회사, a.기준일, a.해수, a.원문해수, a.결산월확인, not a.원문없이, 평가기준일=a.평가기준일)
        print("\n받은 파일 %d개" % len(낸것))
        if a.신고서:
            기 = 신고서받기(a.회사, a.기준일, a.분할회사, 평가기준일=a.평가기준일)
            _신고서보고(기)
            if 기.get("한도초과"):
                return 1
        if a.수시공시:
            import 수시공시 as _수시                             # noqa: PLC0415
            # 수시공시는 정보 경계 도구다 — 창의 끝은 평가기준일 T(없으면 재무기준일 F = T · 옛 동작 그대로)
            수시끝 = a.평가기준일 or a.기준일
            r = _수시.받기(a.회사, 수시끝, RAW)
            print("수시공시 — 호출 %d · 목록 %d · 원문 %d%s" % (r["호출"], r["목록"], r["원문받음"],
                                                           " · 한도 초과로 멈춤(남은 받기 `_raw/%s`)" % _수시.남은파일 if r["한도초과"] else ""))
            _수시._쓰기(os.path.join(RAW, _수시.출력파일), _수시.짓기(RAW, 수시끝, None,
                                                                  a.기준일 if (a.평가기준일 and a.평가기준일 != a.기준일) else None))   # F 를 넘겨야 (F, T] 「사이」 표지가 선다(날짜 둘)
        print("※ 주석(리스·이자비용 단독·성격별 비용·이연법인세·결손금)은 재무제표 API 에 없고 원문에 있다 — "
              "기준일 보고서와 사업보고서 원문을 함께 받았다(`_raw/반기` · `_raw/사업YYYY`). 다른 보고서는 --원문 으로.")
        return 0

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

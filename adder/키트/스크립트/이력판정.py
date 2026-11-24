# -*- coding: utf-8 -*-
"""이력판정 — 감사받은 연간 재무의 해 수를 세고(관문 ⑤ 재정의) 경로 · 구조 블록 경계 · 참고 이력 · 관문 ② 재료를 낸다
(2026-10-25 Y2 · 설계 `연구/재무이력없음_20261025/02_설계.md` 2-2 · 계약 `04_Y2계약.md`). 산출 「이력판정/1」 — `_raw/이력판정.json`.

왜 만들었나
  관문 ⑤ 는 정기보고서(사업보고서 · 10-K · 20-F)의 연간 해만 셌다. 신고서 · 투자설명서 · 분할회사 공시에 감사받은 연간 재무가 있는 회사도
  「이력 없음」으로 섰다(Y1 이 그 재무를 `_raw/신고서재무.json` 「신고서재무/1」 로 받는다). 이 도구가 둘을 한 셈으로 합친다.

셈 규칙(회사 · 업종 무관)
  센다      정기 앵커의 해(국내 `dart_앵커시계열.json` 의 `해[]` 가운데 매출 · 영업이익이 읽히는 해 — 읽기는 `앵커읽기.py` · 미국 `앵커_시계열.json` 의
            `표[]` 줄 가운데 매출 · 영업이익이 있는 줄) + `신고서재무.json` 의 기간 가운데 감사구분 「감사」 · 개월 10 이상(짧은 첫 사업연도 포함 —
            `짧은기` 표지) · `참고이력` 아님 · 매출이 있는 기간
  세지 않는다  미감사 중간 · 미감사 · 검토 · 경영진 배부 · 분배 시점(개월 0) · 개월 10 미만 조각(분할 전 2개월 따위) — `제외[]` 에 까닭과 함께
  겹침      같은 회계연도가 정기와 신고서에 다 있으면 **정기가 쥔다**. 매출 · 영업이익을 대 보고 다르면 둘 다 `겹침[]` 에 적고 경보
  경로      해 수 ≥ 3 「평소」 · 1 ~ 2 「젊은 회사」 · 0 「범위 밖」(공시 재무가 없다)
  경계      ① 이웃한 두 해의 **보고실체 갈래**가 다르면 뒤 해에 「원천 바뀜」 — 갈래는 「분할 전 사업」(분할회사 주석 · 신고서의 분할 대상 사업 ·
            결합 재무제표)과 「대상」(정기 · 대상 자신의 신고서) 둘이다. 같은 등록 회사가 신고서에서 정기로 넘어간 것(공모 뒤 첫 정기보고서)은
            원천종류만 바뀌었고 보고실체는 같아 경계가 아니다
            ② `신고서재무.json` 의 `보고실체변화[]` — 분할 · 사업결합은 그 해에 경계, 공통지배 소급 결합 · 주식분할 소급은 경계가 아니라
            「소급」 표지(신고서가 전 기간을 한 보고실체로 고쳐 적었다)
  관문 ②   합친 해로 다시 센다 — 국내는 `dart_fetch` 의 `_부호들` · `_이익률들` · `사이클진폭` · `관문2재료`(해마다 fnltt 항목 꼴로 읽는다),
            미국은 `sec_앵커` 의 `사이클진폭` · `진폭문장`(관문2 문장은 `sec_앵커.만들기` 의 같은 갈래 글). 짧은 첫 사업연도의 이익률도 쓴다(비율)
  참고 이력  `참고이력: true` 기간(분할 부문 · 검토 · 경영진 배부)은 `참고이력[]` 에만 — 해 수 · 관문 ② · 앵커 해 목록 밖

앵커에 보태기(`--앵커에보태기`)
  감사연간 가운데 **정기 앵커에 없는 해**를 앵커 파일에 보탠다(고치기 전 판 `<앵커>_신고서보탬전.json`). 국내는 `해[]` 에 fnltt 항목 꼴
  (`account_nm` · `account_id` · `thstrm_amount`(원 단위 문자열) · `sj_div`)로 매출 · 영업이익(있으면 매출원가 · 판관비) + `원천` 표지,
  미국은 `표[]` 에 `sec_앵커` 줄 꼴 그대로(값은 원문 통화 단위 — 신고서재무 백만 × `원단위배`) + `원천` 표지. 앵커 파일이 없으면 그 꼴의 새 파일.
  참고 이력은 `해[]` · `표[]` 에 넣지 않고 앵커 최상위 `참고이력[]` 에만 둔다(앵커를 읽는 도구들이 고치지 않아도 산정에서 뺀다 — 「회색 행」).
  받기기록(국내 `받기기록` · 미국 머리 칸)의 사업연도수 · 부호전환수 · 관문2재료 · 이익률진폭 · 영업이익률 최저 · 최고 · 평균을 합친 해로
  다시 쓰고 `신고서보탬[]` · `구조블록경계[]` 를 더한다. **부호를 모델 규약으로 바꾸는 자리가 여기다** — 매출 양수 · 영업이익 손실 음수 ·
  매출원가 · 판관비 양수. 바꾼 칸은 `신고서보탬[].부호바꿈` 에. **두 번 돌려도 같은 파일** — 전에 보탠 해(`원천.보탠도구`)를 걷어 내고 다시 짓는다.

    python 스크립트/이력판정.py --raw _raw --기준일 2026-06-30 [--시장 KR|US] [--앵커에보태기] [-o _raw/이력판정.json]

종료 코드 — 0 통과 · 1 발견(겹침 다름 · 경로 「범위 밖」) · 2 입력오류(원천 폴더 없음 · JSON 파손).
네트워크 0 · 회사 이름은 이 도구에 없다.
"""
from __future__ import annotations

import argparse
import copy
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
from 종료코드 import 통과, 발견, 입력오류  # noqa: E402
import 앵커읽기 as 앵읽  # noqa: E402
import dart_fetch as DF  # noqa: E402  — import 때 인증키를 요구하지 않는다(키는 `_준비()` 에서만 본다)
import sec_앵커 as SA  # noqa: E402
import 신고서재무 as 신  # noqa: E402

형식 = "이력판정/1"
도구이름 = "이력판정.py"
최소개월 = 10                  # 짧은 첫 사업연도(설립 · 분할 직후)를 연간으로 세는 하한 — 2개월 분할 전 조각은 세지 않는다
평소해수 = 3                   # 해 수 ≥ 3 → 평소
겹침허용상대 = 0.001           # 정기 ↔ 신고서 같은 해 — 매출 대비 0.1% 또는
겹침허용절대 = 1.0             # 백만 단위 반올림 1 까지는 같음
국내앵커 = "dart_앵커시계열.json"
미국앵커 = "앵커_시계열.json"
신고서파일 = "신고서재무.json"
산출파일 = "이력판정.json"
보탬전꼬리 = "_신고서보탬전"

# 국내 fnltt 항목 꼴 — 보탤 때 쓰는 표준계정코드 · 계정 이름(앵커읽기의 이름 · 코드 목록에 든 것)
_국내항목 = (("매출", "ifrs-full_Revenue", "매출액"), ("매출원가", "ifrs-full_CostOfSales", "매출원가"),
          ("판관비", "dart_TotalSellingGeneralAdministrativeExpenses", "판매비와관리비"),
          ("영업이익", "dart_OperatingIncomeLoss", "영업이익"))
_접수꼴 = re.compile(r"\b(\d{10}-\d{2}-\d{6}|\d{14})\b")
# 보고실체 갈래 — 분할 전 사업(분할회사 안 · 분할 대상 사업 · 결합 재무제표)인가. 원천종류 「정기」 는 언제나 대상이다
_분할전꼴 = re.compile(r"분할\s*대상|분할\s*전|분할회사|carve|combined|결합\s*재무|사업\s*부문|spin", re.I)


# ══════════════════════════════════════════════════════════ 공통

def _읽기(p):
    """(내용, 오류). 파일이 없으면 (None, None) · 파손이면 (None, 까닭)."""
    if not os.path.exists(p):
        return None, None
    try:
        with io.open(p, encoding="utf-8") as f:
            return json.load(f), None
    except (OSError, ValueError) as e:
        return None, "%s 를 못 읽었다(%s)" % (os.path.basename(p), e)


def _수(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _둥(v, n=3):
    return None if v is None else (int(v) if float(v).is_integer() else round(float(v), n))


def 시장짐작(raw):
    """`신고서재무.json` 의 시장 → 없으면 `신고서재무._시장짐작`(받기 기록 · 파일 이름으로 — 같은 꼴)."""
    j, _ = _읽기(os.path.join(raw, 신고서파일))
    if isinstance(j, dict) and j.get("시장") in ("KR", "US"):
        return j["시장"]
    if os.path.exists(os.path.join(raw, 국내앵커)) and not os.path.exists(os.path.join(raw, 미국앵커)):
        return "KR"
    return 신._시장짐작(raw)


def 보탠해인가(것):
    """앵커의 한 해(국내 `해[]`) · 한 줄(미국 `표[]`)이 이 도구가 보탠 것인가."""
    return isinstance(것, dict) and isinstance(것.get("원천"), dict) and 것["원천"].get("보탠도구") == 도구이름


def 실체갈래(원천종류, 보고실체):
    if 원천종류 == "분할회사 주석":
        return "분할 전 사업"
    if 원천종류 != "정기" and _분할전꼴.search(보고실체 or ""):
        return "분할 전 사업"
    return "대상"


def _접수번호(글, 기본=None):
    m = _접수꼴.search(글 or "")
    return m.group(1) if m else 기본


def _연(글):
    m = re.search(r"(19|20)\d\d", "%s" % (글 or ""))
    return int(m.group(0)) if m else None


# ══════════════════════════════════════════════════════════ 정기 앵커

def 정기연간_국내(앵커, 신고=None, 개황=None):
    """국내 앵커의 해 → [항목] · 읽지 못한 해. 보탠 해는 건너뛴다(그 해의 값은 신고서재무에서 다시 온다).
    개월 — 신고서재무의 같은 FY 정기 기간 → 기업개황 설립일(그 해 중간 설립) → 12."""
    낸, 못 = [], []
    기간 = {p.get("id"): p for p in ((신고 or {}).get("기간") or []) if isinstance(p, dict)}
    설 = ("%s" % ((개황 or {}).get("est_dt") or "")).strip()
    for h in sorted([h for h in (앵커 or {}).get("해") or [] if isinstance(h, dict)], key=lambda x: int(x.get("사업연도") or 0)):
        if 보탠해인가(h):
            continue
        y = int(h.get("사업연도") or 0)
        목 = h.get("list") or []
        매, 매무엇, 금융 = 앵읽.매출한해(목)
        영, 영무엇 = 앵읽.영업한해(목)
        if not 매 or 영 is None:
            못.append({"해": y, "까닭": 앵읽.해마진(h)[2] if not 매 or 영 is None else ""})
            continue
        원가, _ = 앵읽.이름값(목, ("매출원가",))
        판관, _ = 앵읽.이름값(목, ("판매비와관리비", "판매비및관리비"))
        p = 기간.get("FY%dA" % y) or {}
        개월, 짧은 = 12, False
        if p.get("원천종류") == "정기" and p.get("개월"):
            개월 = int(p["개월"])
        elif re.fullmatch(r"\d{8}", 설) and int(설[:4]) == y and int(설[4:6]) > 1:
            개월 = 12 - int(설[4:6]) + 1
        짧은 = 개월 < 12
        접 = next((it.get("rcept_no") for it in 목 if it.get("rcept_no")), None)
        구분 = h.get("재무구분") or "CFS"
        낸.append({"해": y, "기간id": "FY%dA" % y, "원천종류": "정기", "보고실체": "정기보고서 %s 재무제표" % ("별도" if 구분 == "OFS" else "연결"),
                  "개월": 개월, "짧은기": 짧은, "매출": _둥(매 / 1e6), "영업이익": _둥(영 / 1e6), "영업이익률": round(영 / 매, 4),
                  "매출원가": _둥(abs(원가) / 1e6) if 원가 is not None else None, "판관비": _둥(abs(판관) / 1e6) if 판관 is not None else None,
                  "단위": "백만원", "출처": "%s · %s %s · 사업보고서 fnlttSinglAcntAll %s · 「%s」 · 「%s」" % (국내앵커, 접 or "-", y, 구분, 매무엇, 영무엇),
                  "접수번호": 접, "금융업계정": bool(금융), "_목록": 목})
    return 낸, 못


def 정기연간_미국(앵커):
    """미국 앵커의 표 줄 → [항목]. 값은 원문 통화 단위(달러)라 백만으로 나눈다. 보탠 줄은 건너뛴다."""
    낸, 못 = [], []
    for r in (앵커 or {}).get("표") or []:
        if not isinstance(r, dict) or 보탠해인가(r):
            continue
        y = _연(r.get("사업연도"))
        매, 영 = r.get("매출"), r.get("영업이익")
        if y is None:
            continue
        if not _수(매) or not 매 or not _수(영):
            못.append({"해": y, "까닭": "매출 · 영업이익이 표 줄에 없다"})
            continue
        판 = r.get("판관비")
        낸.append({"해": y, "기간id": "FY%dA" % y, "원천종류": "정기", "보고실체": "정기보고서 연결 재무제표", "개월": 12, "짧은기": False,
                  "매출": _둥(매 / 1e6), "영업이익": _둥(영 / 1e6), "영업이익률": round(영 / 매, 4),
                  "매출원가": _둥(abs(r["매출원가"]) / 1e6) if _수(r.get("매출원가")) else None,
                  "판관비": _둥(abs(판) / 1e6) if _수(판) else None, "단위": "백만달러",
                  "출처": "%s · %s %s · %s" % (미국앵커, r.get("사업연도"), r.get("서식") or "-", r.get("체계") or "-"), "접수번호": None,
                  "종료일": r.get("종료일")})
    return 낸, 못


# ══════════════════════════════════════════════════════════ 신고서재무

def _값(신고, 줄, k):
    v = ((신고.get("표준줄") or {}).get(줄) or {}).get(k)
    return v if _수(v) else None


def _근거출처(신고, 줄, k):
    return ((((신고.get("근거") or {}).get(줄) or {}).get(k) or {}).get("출처")) or ""


def _서류접수(신고, 원천종류):
    for d in 신고.get("서류") or []:
        역 = d.get("역할") or ""
        if 원천종류 == "분할회사 주석" and ("분할회사" in 역 or "분할회사" in (d.get("종류") or "")):
            return d.get("접수번호")
        if 원천종류 == "신고서" and "분할회사" not in 역 and "분할회사" not in (d.get("종류") or ""):
            return d.get("접수번호")
    return None


def 신고서기간들(신고, 시장):
    """신고서재무의 기간 → (센 후보[항목], 참고이력[], 제외[], 확인불가[]). 값은 모델 부호(비용 양수)로 — 바꾼 칸은 `부호바꿈`."""
    후보, 참고, 제외, 불가 = [], [], [], []
    단위 = (신고 or {}).get("단위") or ("백만원" if 시장 == "KR" else "백만달러")
    for p in (신고 or {}).get("기간") or []:
        if not isinstance(p, dict) or not p.get("id"):
            continue
        k = p["id"]
        개월 = int(p.get("개월") or 0)
        매, 영 = _값(신고, "매출", k), _값(신고, "영업이익", k)
        if p.get("참고이력"):
            근 = _근거출처(신고, "매출", k) or _근거출처(신고, "영업이익", k)
            덧 = [x for x in ("검토 " + p["검토기관"] if p.get("검토기관") else "", "배부: " + p["배부기준"] if p.get("배부기준") else "") if x]
            참고.append({"기간id": k, "감사구분": p.get("감사구분"), "개월": 개월, "시작": p.get("시작"), "끝": p.get("끝"),
                       "보고실체": p.get("보고실체"), "매출": 매, "영업이익": 영,
                       "영업이익률": (round(영 / 매, 4) if (매 and 영 is not None) else None),
                       "근거": " · ".join([근] + [x for x in 덧 if x not in 근]) if 근 else " · ".join(덧)})
            continue
        if p.get("감사구분") != "감사":
            제외.append({"기간id": k, "까닭": "감사구분 「%s」 — 감사받은 연간이 아니다" % p.get("감사구분")})
            continue
        if 개월 < 최소개월:
            제외.append({"기간id": k, "까닭": ("분배 시점(개월 0)" if 개월 == 0 else "%d개월 조각 — %d개월 미만은 연간으로 세지 않는다" % (개월, 최소개월))})
            continue
        if 매 is None:
            제외.append({"기간id": k, "까닭": "매출을 못 읽었다(표준줄 매출 없음)"})
            불가.append({"항목": "%s 매출" % k, "원인": "항목 부재", "대안": "신고서 원문 손익계산서에서 그 기간의 매출 줄을 확인한다"})
            continue
        if 영 is None:
            불가.append({"항목": "%s 영업이익" % k, "원인": "항목 부재", "대안": "신고서 원문 손익계산서에서 영업이익(손실) 줄을 확인한다 — 관문 ② 재료에서 빠진다"})
        바꿈 = []

        def _비용(줄):
            v = _값(신고, 줄, k)
            if v is not None and v < 0:
                바꿈.append("%s: 원문 표시 %s → %s(비용 양수)" % (줄, _둥(v), _둥(-v)))
                v = -v
            return v
        원가 = _비용("매출원가")
        판관 = _비용("판매비와관리비")
        연구 = _비용("연구개발비")
        if 시장 == "US":
            판합 = (판관 or 0) + (연구 or 0) if (판관 is not None or 연구 is not None) else None
            판출처 = "신고서재무 합산(%s)" % " + ".join(x for x, v in (("판매비와관리비", 판관), ("연구개발비", 연구)) if v is not None)
        else:
            판합, 판출처 = 판관, "신고서재무 판매비와관리비"
        if 매 < 0:
            바꿈.append("매출: 원문 표시 %s — 음수 매출(바꾸지 않는다 · 원문 확인)" % _둥(매))
        원천종류 = p.get("원천종류") or "신고서"
        출 = _근거출처(신고, "매출", k)
        끝 = p.get("끝") or ""
        실체 = p.get("보고실체") or ""
        if 원천종류 == "정기":                        # 정기는 앵커의 해와 같은 이름으로(첫 사업연도 꼬리 같은 글 차이로 경계가 서지 않게)
            실체 = "정기보고서 %s 재무제표" % ("별도" if "별도" in 실체 else "연결")
        후보.append({"해": _연(끝) or _연(k), "기간id": k, "원천종류": 원천종류, "보고실체": 실체, "개월": 개월,
                   "짧은기": bool(p.get("짧은기") or 개월 < 12), "매출": 매, "영업이익": 영,
                   "영업이익률": (round(영 / 매, 4) if (매 and 영 is not None) else None),
                   "매출원가": 원가, "판관비": 판합, "판관비출처": 판출처 if 판합 is not None else None, "연구개발비": 연구,
                   "단위": 단위, "출처": 출 or "%s · %s" % (신고서파일, k), "접수번호": _접수번호(출, _서류접수(신고, 원천종류)),
                   "시작": p.get("시작"), "끝": 끝, "부호바꿈": 바꿈})
    return 후보, 참고, 제외, 불가


# ══════════════════════════════════════════════════════════ 관문 ②

def _관문2_미국(부호, 율):
    """`sec_앵커.만들기` 의 관문2 갈래 글과 같은 문장(그 함수 안의 글이라 import 할 수 없다 — 진폭 · 진폭 문장은 sec_앵커 의 것을 쓴다)."""
    전환 = sum(1 for a, b in zip(부호, 부호[1:]) if a != b)
    진 = SA.사이클진폭(율)
    if not 부호:
        return "재료 없음", 진
    if 전환 == 0 and all(x > 0 for x in 부호):
        if 진 is None:
            return "전부 흑자(전환 0회) — 관문 ② 에 안 걸린다. 사이클 진폭은 이익률 재료가 없어 못 쟀다", 진
        return ("전부 흑자(전환 0회) — 관문 ② 에 안 걸린다. " + SA.진폭문장(진, "모자라면 `--최대` 를 늘리거나 기준 단절로 끊은 옛 사슬(`--단절이음`)을 본다"), 진)
    if 전환 == 0:
        return "전부 적자(전환 0회) — 최근이 단조 개선이면 T4(전환 미완)의 예고, 아니면 관문 ② 에 걸린다(자체검사 ⓪ 이 이익률로 가른다)", 진
    return "부호 전환 %d회 — 한 번 꺾여 돌아오지 않은 것인지, 진폭이 사이클인지 한 번의 사건인지 관문 ② 를 판정하십시오" % 전환, 진


def 국내항목목록(e, 고유=None):
    """감사연간 한 해 → fnltt 항목 꼴 목록(원 단위 문자열 · 손익 CIS). 정기 해는 받은 목록 그대로."""
    if e.get("_목록") is not None:
        return e["_목록"]
    낸 = []
    for i, (칸, 코드, 이름) in enumerate(_국내항목):
        v = e.get(칸)
        if v is None:
            continue
        낸.append({"rcept_no": e.get("접수번호") or "-", "bsns_year": str(e["해"]), "corp_code": 고유 or "", "sj_div": "CIS",
                  "sj_nm": "포괄손익계산서", "account_id": 코드, "account_nm": 이름, "account_detail": "-",
                  "thstrm_nm": "보탬(%s · %s)" % (e.get("원천종류"), e.get("기간id")), "thstrm_amount": "%d" % int(round(float(v) * 1e6)),
                  "ord": str(i + 1), "currency": "KRW"})
    return 낸


def 관문2(감사연간, 시장):
    해들 = sorted(감사연간, key=lambda x: x["해"])
    if 시장 == "KR":
        앵 = [{"사업연도": e["해"], "list": 국내항목목록(e)} for e in 해들]
        부호, 율 = DF._부호들(앵), DF._이익률들(앵)
        글, 진 = DF.관문2재료(부호, 율), DF.사이클진폭(율)
        쓴 = [e for e in 해들 if e.get("매출") and e.get("영업이익") is not None]
        지점 = ["%d→%d" % (a["해"], b["해"]) for a, b in zip(쓴, 쓴[1:]) if (a["영업이익"] >= 0) != (b["영업이익"] >= 0)]
    else:
        쓴 = [e for e in 해들 if e.get("매출") and e.get("영업이익") is not None]
        부호 = [1 if e["영업이익"] >= 0 else -1 for e in 쓴]
        율 = [e["영업이익"] / e["매출"] for e in 쓴]
        글, 진 = _관문2_미국(부호, 율)
        지점 = ["FY%d(%s)→FY%d(%s)" % (a["해"], "−" if a["영업이익"] < 0 else "+", b["해"], "−" if b["영업이익"] < 0 else "+")
              for a, b in zip(쓴, 쓴[1:]) if (a["영업이익"] < 0) != (b["영업이익"] < 0)]
    return {"부호": 부호, "부호전환수": sum(1 for a, b in zip(부호, 부호[1:]) if a != b), "부호전환지점": 지점,
            "이익률": [{"해": e["해"], "영업이익률": round(e["영업이익"] / e["매출"], 4)} for e in 쓴],
            "이익률진폭": 진, "관문2재료": 글}


# ══════════════════════════════════════════════════════════ 판정

def 판정(raw, 기준일, 시장=None):
    """`raw`(회차 `_raw`) · 평가기준일 → 「이력판정/1」 dict. 네트워크 0. 파일이 파손이면 ValueError."""
    raw = os.path.abspath(raw)
    시장 = 시장 or 시장짐작(raw)
    신고, 오1 = _읽기(os.path.join(raw, 신고서파일))
    앵커이름 = 국내앵커 if 시장 == "KR" else 미국앵커
    앵커, 오2 = _읽기(os.path.join(raw, 앵커이름))
    개황, _ = _읽기(os.path.join(raw, "dart_기업개황.json"))
    for 오 in (오1, 오2):
        if 오:
            raise ValueError(오)
    경보, 불가, 제외 = [], [], []
    if 시장 == "KR":
        정기, 못 = 정기연간_국내(앵커, 신고, 개황)
    else:
        정기, 못 = 정기연간_미국(앵커)
    for x in 못:
        불가.append({"항목": "정기 앵커 %s 해" % x["해"], "원인": "항목 부재", "대안": "%s — 원문 손익계산서에서 그 해를 확인한다" % x["까닭"]})
    보탠해 = sorted({int(h.get("사업연도") or 0) if 시장 == "KR" else (_연(h.get("사업연도")) or 0)
                  for h in ((앵커 or {}).get("해" if 시장 == "KR" else "표") or []) if 보탠해인가(h)})
    후보, 참고, 제외s, 불가s = 신고서기간들(신고 or {}, 시장)
    제외 += 제외s
    불가 += 불가s
    정기해 = {e["해"]: e for e in 정기}
    쥔 = dict(정기해)
    겹침 = []
    같은해 = {}
    for e in 후보:
        y = e["해"]
        if e["원천종류"] == "정기" and y in 보탠해 and y not in 정기해:
            # 신고서재무가 보탠 뒤의 앵커를 다시 읽어 그 해를 「정기」 로 적은 경우 — 정기가 아니다(원래 원천은 신고서재무의 다른 기간)
            제외.append({"기간id": e["기간id"], "까닭": "앵커에 이 도구가 보탠 해를 신고서재무가 「정기」 로 다시 읽은 것 — 세지 않는다(원래 원천 기간이 따로 있다)"})
            경보.append("신고서재무 %s 는 보탠 앵커 해를 정기로 읽은 것이라 뺐다 — 신고서재무를 `%s%s.json` 판(보탬 전)으로 다시 짓기를 권한다"
                      % (e["기간id"], os.path.splitext(국내앵커)[0], 보탬전꼬리))
            continue
        if y in 정기해:
            g = 정기해[y]
            for 칸 in ("매출", "영업이익"):
                a, b = g.get(칸), e.get(칸)
                if a is None or b is None:
                    continue
                차 = round(float(b) - float(a), 3)
                같다 = abs(차) <= max(겹침허용절대, abs(float(a)) * 겹침허용상대)
                겹침.append({"해": y, "항목": 칸, "정기": a, "신고서": b, "신고서기간id": e["기간id"], "신고서원천종류": e["원천종류"],
                           "차": 차, "판정": "같음" if 같다 else "다름(경보)"})
                if not 같다:
                    경보.append("%d %s — 정기 %s ↔ 신고서재무 %s(%s) · 차 %s · 정기가 쥔다(두 값 다 `겹침` 에)"
                              % (y, 칸, _둥(a), _둥(b), e["기간id"], _둥(차)))
            continue
        같은해.setdefault(y, []).append(e)
    for y, 목 in 같은해.items():
        목.sort(key=lambda x: (0 if x["원천종류"] == "정기" else 1, 0 if "_" not in x["기간id"] else 1, -x["개월"]))
        쥔[y] = 목[0]
        for 남 in 목[1:]:
            제외.append({"기간id": 남["기간id"], "까닭": "같은 회계연도 %d 를 %s 가 쥐었다" % (y, 목[0]["기간id"])})
            경보.append("회계연도 %d 에 감사 연간 기간이 둘 이상 — %s 를 쓰고 %s 는 뺐다" % (y, 목[0]["기간id"], 남["기간id"]))
    감사연간 = [쥔[y] for y in sorted(쥔)]
    for e in 감사연간:
        if e.get("짧은기"):
            경보.append("짧은 사업연도 %s(%d개월)를 연간으로 셌다 — 해 수 · 관문 ② 이익률에는 쓰고, 연 성장률 · 수준 비교에는 그대로 쓰지 않는다"
                      % (e["기간id"], e["개월"]))
    해들 = [e["해"] for e in 감사연간]
    for a, b in zip(해들, 해들[1:]):
        if b - a > 1:
            경보.append("감사 연간이 %d 와 %d 사이에서 빈다 — 이웃한 해가 아니다" % (a, b))
    해수 = len(감사연간)
    경로 = "평소" if 해수 >= 평소해수 else ("젊은 회사" if 해수 >= 1 else "범위 밖")
    목록글 = " · ".join("%d %s%s" % (e["해"], e["원천종류"], "(%d개월)" % e["개월"] if e.get("짧은기") else "") for e in 감사연간)
    경로까닭 = ("감사받은 연간 %d해(%s) — %s" % (해수, 목록글, {"평소": "%d해 이상이라 평소 경로" % 평소해수,
                                                         "젊은 회사": "%d해 미만이라 젊은 회사 경로(시장 규모 · 단위경제성 쪽)" % 평소해수}[경로])
            if 해수 else "감사받은 연간 재무가 없다(정기 앵커 · 신고서재무 모두) — 범위 밖")
    if not 해수:
        불가.append({"항목": "감사받은 연간 재무", "원인": "조회 경로 문제" if not (신고 or 앵커) else "항목 부재",
                   "대안": "`dart_fetch.py --회사 … --기준일 … --신고서` · `sec_fetch.py --신고서` 로 받고 `신고서재무.py` 를 돈 뒤 다시 돈다"})
    if 앵커 is None:
        불가.append({"항목": "정기 앵커(%s)" % 앵커이름, "원인": "조회 경로 문제" if 시장 == "KR" else "항목 부재",
                   "대안": "정기보고서 연간이 없거나 받지 않았다 — 신고서재무만으로 셌다"})
    if 신고 is None:
        불가.append({"항목": 신고서파일, "원인": "조회 경로 문제", "대안": "신고서 · 분할회사 공시가 있으면 `신고서재무.py` 를 먼저 돈다 — 정기 앵커만으로 셌다"})

    # ── 구조 블록 경계 ──
    경계 = []
    for a, b in zip(감사연간, 감사연간[1:]):
        ga, gb = 실체갈래(a["원천종류"], a["보고실체"]), 실체갈래(b["원천종류"], b["보고실체"])
        if ga != gb:
            경계.append({"해": b["해"], "종류": "원천 바뀜", "까닭": "%d %s(%s · %s) → %d %s(%s · %s) — 보고실체가 갈린다"
                        % (a["해"], a["원천종류"], ga, a["보고실체"][:60], b["해"], b["원천종류"], gb, b["보고실체"][:60])})
    for x in (신고 or {}).get("보고실체변화") or []:
        y = _연(x.get("해"))
        종 = x.get("종류") or ""
        if y is None:
            continue
        내 = (x.get("내용") or "")[:160]
        if 종 in ("분할", "사업결합"):
            덧 = "" if (해들 and 해들[0] <= y <= 해들[-1] + 1) else " · 감사 연간 범위 밖의 해"
            경계.append({"해": y, "종류": 종, "까닭": "%s — %s%s" % (종, 내, 덧), "근거": x.get("근거")})
        elif "공통지배" in 종:
            경계.append({"해": y, "종류": "소급", "까닭": "소급 — 한 보고실체로 고쳐 적음(공통지배 소급 결합 · 신고서가 전 기간을 결합 뒤 실체로 다시 적었다 — 경계 아님) · %s" % 내,
                       "근거": x.get("근거")})
        elif "주식분할" in 종:
            경계.append({"해": y, "종류": "소급", "까닭": "소급 — 주식 수 · 주당 정보만 전 기간 고쳐 적음(손익 시계열 경계 아님) · %s" % 내, "근거": x.get("근거")})
        else:
            경계.append({"해": y, "종류": 종 or "소급", "까닭": 내, "근거": x.get("근거")})
    본 = set()
    경계 = [z for z in 경계 if not ((z["해"], z["종류"], z["까닭"]) in 본 or 본.add((z["해"], z["종류"], z["까닭"])))]
    경계.sort(key=lambda z: (z["해"], z["종류"]))

    # ── 해 수는 가장 최근 구조 블록 안에서 센다(2026-10-25 본선 — Y2 실측 뒤) ──
    # 관문 ⑤ 의 뜻은 「같은 회사의 비교 가능한 연간이 세 해 있나」다. 분할 · 사업결합 · 원천 바뀜(분할회사 주석의 분할 대상 사업 → 신설회사 정기) 경계
    # 앞의 해는 보고실체가 달라 그 셈에 넣지 않는다 — 실측(분할 신설회사): 경계 앞 2023 매출이 경계 뒤 2024(10개월)의 1/3.5 였다(연결 범위가 다르다).
    # 경계 앞 해는 버리지 않는다 — 관문 ② 재료(부호 · 진폭)와 앵커 관측(표지 달린 해)에는 그대로 쓴다. 공통지배 소급 결합 · 주식분할은 경계가 아니다
    전체해수 = 해수
    끊는해 = [z["해"] for z in 경계 if z["종류"] in ("원천 바뀜", "분할", "사업결합") and 해들 and 해들[0] < z["해"] <= 해들[-1]]
    블록시작 = max(끊는해) if 끊는해 else None
    if 블록시작 is not None:
        해수 = sum(1 for e in 감사연간 if e["해"] >= 블록시작)
        if 해수 < 전체해수:
            경로 = "평소" if 해수 >= 평소해수 else ("젊은 회사" if 해수 >= 1 else "범위 밖")
            경로까닭 = ("감사받은 연간 %d해 가운데 최근 구조 블록(%d년부터) 안의 해는 %d해 — 경계 앞 %d해는 보고실체가 달라 해 수에서 뺐다"
                     "(관문 ② 재료 · 앵커 관측에는 쓴다) — %s" % (
                         전체해수, 블록시작, 해수, 전체해수 - 해수,
                         {"평소": "%d해 이상이라 평소 경로" % 평소해수, "젊은 회사": "%d해 미만이라 젊은 회사 경로(시장 규모 · 단위경제성 쪽)" % 평소해수,
                          "범위 밖": "범위 밖"}[경로]))

    낸감사 = [{k: v for k, v in e.items() if not k.startswith("_")} for e in 감사연간]
    결과 = {"형식": 형식, "시장": 시장, "회사": (신고 or {}).get("회사") or (개황 or {}).get("corp_name"),
          "식별": (신고 or {}).get("식별") or ({"고유번호": (앵커 or {}).get("고유번호")} if 시장 == "KR" and 앵커 else {}),
          "평가기준일": 기준일, "조회일": datetime.date.today().isoformat(),
          "입력": {"정기앵커": ("_raw/" + 앵커이름) if 앵커 is not None else None, "신고서재무": ("_raw/" + 신고서파일) if 신고 is not None else None,
                 "보탠해(앵커에 이미)": 보탠해},
          "감사연간": 낸감사, "해수": 해수, "전체해수": 전체해수, "블록시작": 블록시작, "경로": 경로, "경로까닭": 경로까닭,
          "구조블록경계": 경계, "참고이력": 참고, "관문2": 관문2(감사연간, 시장),
          "겹침": 겹침, "제외": 제외, "경보": 경보, "확인불가": 불가}
    결과["_내부"] = 감사연간                                     # 앵커에보태기가 쓴다(저장하지 않는다)
    return 결과


# ══════════════════════════════════════════════════════════ 앵커에 보태기

def _율요약(율들):
    """[(해, 율)] → {최저, 최저_해, 최고, 최고_해, 평균}."""
    if not 율들:
        return {"최저": None, "최저_해": None, "최고": None, "최고_해": None, "평균": None}
    lo = min(율들, key=lambda t: t[1])
    hi = max(율들, key=lambda t: t[1])
    return {"최저": round(lo[1], 4), "최저_해": lo[0], "최고": round(hi[1], 4), "최고_해": hi[0],
            "평균": round(sum(t[1] for t in 율들) / len(율들), 4)}


def _원천표지(e):
    return {"종류": e["원천종류"], "기간id": e["기간id"], "접수번호": e.get("접수번호"), "보고실체": e.get("보고실체"),
            "개월": e.get("개월"), "짧은기": bool(e.get("짧은기")), "보탠도구": 도구이름}


def _보탬기록(e, 옛때, 오늘):
    return {"해": e["해"], "기간id": e["기간id"], "원천": e["원천종류"], "접수번호": e.get("접수번호"),
            "때": 옛때.get((e["해"], e["기간id"])) or 오늘, "부호바꿈": list(e.get("부호바꿈") or [])}


def _쓰기(p, 것):
    임 = p + ".쓰는중"
    with io.open(임, "w", encoding="utf-8") as f:
        json.dump(것, f, ensure_ascii=False, indent=1)
    os.replace(임, p)


def 손탔나(원):
    """앵커가 이 도구 손을 탔나 — 보탠 해 · 줄이나 이 도구가 다는 칸(참고이력 · 신고서보탬)이 있나."""
    return bool(any(보탠해인가(h) for 키 in ("해", "표") for h in (원.get(키) or []))
                or 원.get("참고이력") is not None or 원.get("신고서보탬") is not None
                or (원.get("받기기록") or {}).get("신고서보탬") is not None)


def _보존(p, 원):
    """고치기 전 판 `<앵커>_신고서보탬전.json`. 앵커가 이 도구 손을 타지 않은 판(정기 받기를 새로 돈 판)이면 그 판으로 덮어 둔다.
    이미 보탠 판이면 보존본을 건드리지 않고, 보존본이 없을 때만 보탠 것을 걷어 낸 판을 둔다."""
    q = os.path.splitext(p)[0] + 보탬전꼬리 + ".json"
    if not 손탔나(원):
        _쓰기(q, 원)
    elif not os.path.exists(q):
        _쓰기(q, 걷은판(원))
    return q


def 걷은판(원):
    """앵커에서 이 도구가 보탠 것(해 · 표 줄 · 참고이력 · 신고서보탬 · 구조블록경계)을 걷어 낸 판(받기기록 수치는 손대지 않는다)."""
    d = copy.deepcopy(원)
    for 키 in ("해", "표"):
        if isinstance(d.get(키), list):
            d[키] = [h for h in d[키] if not 보탠해인가(h)]
    for 키 in ("참고이력", "신고서보탬", "구조블록경계", "이력판정"):
        d.pop(키, None)
    if isinstance(d.get("받기기록"), dict):
        for 키 in ("신고서보탬", "구조블록경계"):
            d["받기기록"].pop(키, None)
    return d


def _국내보태기(raw, 결, 신고):
    p = os.path.join(raw, 국내앵커)
    원, 오 = _읽기(p)
    if 오:
        raise ValueError(오)
    새파일 = 원 is None
    원 = 원 or {}
    고유 = 원.get("고유번호") or ((신고 or {}).get("식별") or {}).get("고유번호")
    옛기 = (원.get("받기기록") or {})
    옛때 = {(x.get("해"), x.get("기간id")): x.get("때") for x in 옛기.get("신고서보탬") or [] if isinstance(x, dict)}
    오늘 = 결["조회일"]
    해 = [h for h in 원.get("해") or [] if isinstance(h, dict) and not 보탠해인가(h)]
    구분 = next((h.get("재무구분") for h in 해 if h.get("재무구분")), "CFS")
    있는 = {int(h.get("사업연도") or 0) for h in 해}
    보탤 = [e for e in 결["_내부"] if e["해"] not in 있는]
    for e in 보탤:
        해.append({"사업연도": e["해"], "list": 국내항목목록(e, 고유), "재무구분": 구분, "원천": _원천표지(e)})
    해.sort(key=lambda h: int(h.get("사업연도") or 0))
    부호, 율 = DF._부호들(해), DF._이익률들(해)
    율해 = [(int(h["사업연도"]), m) for h in 해 for _y, m, _r in [앵읽.해마진(h)] if m is not None]
    기 = dict(옛기)
    if 새파일:
        기.update({"멈춘이유": "정기 앵커 없음 — 신고서재무(감사 연간)로 만든 해(%s)" % 도구이름, "최소해수": 6, "필요전환": 2, "금융업계정": None})
    기.update({"사업연도수": len(해), "부호전환수": DF._부호전환수(해), "관문2재료": DF.관문2재료(부호, 율), "이익률진폭": DF.사이클진폭(율),
              "영업이익률": _율요약(율해),
              "읽지못한해": [{"사업연도": int(h["사업연도"]), "까닭": 까} for h in 해 for _y, m, 까 in [앵읽.해마진(h)] if m is None],
              "신고서보탬": [_보탬기록(e, 옛때, 오늘) for e in sorted(보탤, key=lambda x: x["해"])],
              "구조블록경계": 결["구조블록경계"]})
    새 = {k: v for k, v in 원.items() if k not in ("해", "받기기록", "참고이력")}
    새.update({"고유번호": 고유, "해": 해, "받기기록": 기, "참고이력": 결["참고이력"]})
    return p, 원, 새, 새파일, [e["해"] for e in 보탤]


def _미국줄(e, 배, 신고):
    매 = e["매출"] * 배
    영 = e["영업이익"] * 배 if e.get("영업이익") is not None else None
    원가 = e["매출원가"] * 배 if e.get("매출원가") is not None else None
    판 = e["판관비"] * 배 if e.get("판관비") is not None else None
    총 = (매 - 원가 - 영) if (원가 is not None and 영 is not None) else None
    서식 = next((d.get("종류") for d in (신고 or {}).get("서류") or [] if d.get("접수번호") == e.get("접수번호")), None)
    return {"사업연도": "FY%d" % e["해"], "종료일": e.get("끝"), "매출": 매, "매출원가": 원가, "판관비": 판, "총영업비용": 총,
            "판관비출처": e.get("판관비출처"), "판관비_잔여갭": (round((판 - 총) / 매, 4) if (판 is not None and 총 is not None and 매) else None),
            "영업이익": 영, "영업이익률": (round(영 / 매, 4) if (영 is not None and 매) else None),
            "영업이익출처": "신고서 감사 연간(%s)" % e["원천종류"], "매출원가_상각포함": None,
            "서식": 서식 or e["원천종류"], "체계": "신고서재무", "기준단절": None, "출처": e.get("출처"), "원천": _원천표지(e)}


def _미국보태기(raw, 결, 신고):
    p = os.path.join(raw, 미국앵커)
    원, 오 = _읽기(p)
    if 오:
        raise ValueError(오)
    새파일 = 원 is None
    원 = 원 or {}
    배 = float((신고 or {}).get("원단위배") or 1e6)
    옛때 = {(x.get("해"), x.get("기간id")): x.get("때") for x in 원.get("신고서보탬") or [] if isinstance(x, dict)}
    표 = [r for r in 원.get("표") or [] if isinstance(r, dict) and not 보탠해인가(r)]
    있는 = {_연(r.get("사업연도")) for r in 표}
    보탤 = [e for e in 결["_내부"] if e["해"] not in 있는]
    for e in 보탤:
        표.append(_미국줄(e, 배, 신고))
    표.sort(key=lambda r: (r.get("종료일") or "", r.get("사업연도") or ""))
    쓴 = [r for r in 표 if _수(r.get("영업이익")) and _수(r.get("매출")) and r["매출"]]
    부호 = [1 if r["영업이익"] >= 0 else -1 for r in 쓴]
    율 = [r["영업이익"] / r["매출"] for r in 쓴]
    글, 진 = _관문2_미국(부호, 율)
    지점 = ["%s(%s)→%s(%s)" % (a["사업연도"], "−" if a["영업이익"] < 0 else "+", b["사업연도"], "−" if b["영업이익"] < 0 else "+")
          for a, b in zip(쓴, 쓴[1:]) if (a["영업이익"] < 0) != (b["영업이익"] < 0)]
    새 = dict(원)
    if 새파일:
        끝달 = next((int(e["끝"][5:7]) for e in 결["_내부"] if e.get("끝")), 12)
        새.update({"통화": (신고 or {}).get("통화") or "USD", "결산월": 끝달, "태그_이음": [],
                  "멈춘_이유": "정기 앵커 없음 — 신고서재무(감사 연간)로 만든 표(%s)" % 도구이름, "단절_옛사슬": [], "단절이음": False,
                  "참고_단절이음": None,
                  "주의": "신고서재무에서 만든 줄이다 — 값은 원문 통화 단위(신고서재무 백만 × 원단위배). 판관비는 신고서의 판매비와관리비 + 연구개발비 합"})
    새.update({"사업연도수": len(표), "표": 표, "부호_전환_횟수": len(지점), "부호_전환_지점": 지점, "관문2재료": 글, "이익률진폭": 진,
              "영업이익률": _율요약([(r["사업연도"], r["영업이익"] / r["매출"]) for r in 쓴]),
              "판관비_잔여와_벌어진_해": [(r["사업연도"], r["판관비_잔여갭"]) for r in 표
                                if r.get("판관비_잔여갭") is not None and abs(r["판관비_잔여갭"]) > 0.01],
              "신고서보탬": [_보탬기록(e, 옛때, 결["조회일"]) for e in sorted(보탤, key=lambda x: x["해"])],
              "구조블록경계": 결["구조블록경계"], "참고이력": 결["참고이력"]})
    return p, 원, 새, 새파일, [e["해"] for e in 보탤]


def 앵커에보태기(raw, 판정결과):
    """판정 결과의 감사연간 가운데 정기 앵커에 없는 해를 앵커 파일에 보탠다 → 기록 dict.
    {앵커, 새파일, 보탠해, 보존, 바뀜, 사업연도수, 부호전환수}. 같은 내용이면 파일을 쓰지 않는다(두 번 돌려도 같은 파일)."""
    raw = os.path.abspath(raw)
    결 = 판정결과
    if "_내부" not in 결:
        raise ValueError("판정 결과에 `_내부`(감사연간 원본)가 없다 — `판정()` 의 반환값을 그대로 준다")
    신고, _ = _읽기(os.path.join(raw, 신고서파일))
    if 결["시장"] == "KR":
        p, 원, 새, 새파일, 보탠 = _국내보태기(raw, 결, 신고)
    else:
        p, 원, 새, 새파일, 보탠 = _미국보태기(raw, 결, 신고)
    if not 결["_내부"] and 새파일:
        return {"앵커": None, "새파일": False, "보탠해": [], "보존": None, "바뀜": False, "까닭": "감사 연간이 없어 앵커를 만들지 않았다"}
    보존 = None
    바뀜 = json.dumps(원, ensure_ascii=False, sort_keys=True) != json.dumps(새, ensure_ascii=False, sort_keys=True)
    if 바뀜:
        if not 새파일:
            보존 = _보존(p, 원)
        _쓰기(p, 새)
    elif not 새파일:
        q = os.path.splitext(p)[0] + 보탬전꼬리 + ".json"
        보존 = q if os.path.exists(q) else None
    기 = 새.get("받기기록") if 결["시장"] == "KR" else 새
    return {"앵커": p, "새파일": 새파일, "보탠해": 보탠, "보존": 보존, "바뀜": 바뀜,
            "사업연도수": 기.get("사업연도수"), "부호전환수": 기.get("부호전환수", 기.get("부호_전환_횟수")),
            "관문2재료": 기.get("관문2재료")}


# ══════════════════════════════════════════════════════════ 입구

def 저장(결과, raw, 경로=None):
    p = 경로 or os.path.join(raw, 산출파일)
    os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    _쓰기(p, {k: v for k, v in 결과.items() if not k.startswith("_")})
    return p


def 종료판정(결과):
    if 결과.get("경로") == "범위 밖":
        return 발견
    if any(x.get("판정") != "같음" for x in 결과.get("겹침") or []):
        return 발견
    return 통과


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="감사받은 연간 해 수 · 경로 · 구조 블록 경계 · 참고 이력 → 「이력판정/1」")
    ap.add_argument("--raw", default=os.path.join(os.path.dirname(여기), "_raw"), help="받아 둔 원천 폴더(기본: 키트의 _raw)")
    ap.add_argument("--기준일", "--재무기준일", dest="기준일", default=None,
                    help="재무기준일 F YYYY-MM-DD(평가기준일 전에 제출된 마지막 분기말 · 옛 이름 --기준일 은 지금 뜻 그대로)")
    ap.add_argument("--평가기준일", default=None, help="평가기준일 T YYYY-MM-DD — 산출 머리에만 적는다(판정은 바꾸지 않는다)")
    ap.add_argument("--가정", default=None, help="가정 파일 — 날짜 인자를 비우면 기준일.py 로 F · T 를 푼다(F 가 없으면 F = T)")
    ap.add_argument("--시장", choices=("KR", "US"), default=None, help="없으면 _raw 의 파일로 짐작")
    ap.add_argument("--앵커에보태기", action="store_true", help="감사연간 가운데 정기 앵커에 없는 해를 앵커 파일에 보탠다(고치기 전 판 보존)")
    ap.add_argument("-o", "--출력", default=None, help="기본: <raw>/이력판정.json")
    a = ap.parse_args(argv)
    import 기준일인자 as _기인                                  # noqa: PLC0415 — 날짜 둘(2026-10-25)
    a.기준일 = _기인.풀기(a.기준일, a.가정, _기인.재무, 인자="--기준일")
    a.평가기준일 = _기인.풀기(a.평가기준일, a.가정, _기인.평가, 인자="--평가기준일")
    if not a.기준일:
        ap.error("--기준일(재무기준일) 또는 --가정 이 있어야 합니다")
    if not os.path.isdir(a.raw):
        print("원천 폴더가 없습니다: %s" % a.raw)
        return 입력오류
    try:
        결 = 판정(a.raw, a.기준일, a.시장)
    except ValueError as e:
        print("입력 오류 — %s" % e)
        return 입력오류
    _기인.머리(결, a.기준일, a.평가기준일)                      # 재무기준일 = F · 평가기준일 = T(알면)
    if a.앵커에보태기:
        try:
            결["앵커보탬"] = 앵커에보태기(a.raw, 결)
        except ValueError as e:
            print("입력 오류 — %s" % e)
            return 입력오류
    p = 저장(결, a.raw, a.출력)
    g = 결["관문2"]
    print("이력판정 저장: %s" % p)
    print("  시장 %s · 해 수 %d · 경로 %s" % (결["시장"], 결["해수"], 결["경로"]))
    print("  " + 결["경로까닭"])
    for e in 결["감사연간"]:
        print("    %d %-10s %-8s %2d개월 매출 %s · 영업이익 %s · %s" % (e["해"], e["기간id"], e["원천종류"], e["개월"], e["매출"], e["영업이익"],
                                                             "%.1f%%" % (e["영업이익률"] * 100) if e.get("영업이익률") is not None else "-"))
    for z in 결["구조블록경계"]:
        print("  경계 %d %s — %s" % (z["해"], z["종류"], z["까닭"][:120]))
    print("  참고 이력 %d · 제외 %d · 겹침 %d(다름 %d)" % (len(결["참고이력"]), len(결["제외"]), len(결["겹침"]),
                                                 sum(1 for x in 결["겹침"] if x["판정"] != "같음")))
    print("  관문 ② — 부호 %s · 전환 %d회 · %s" % (g["부호"], g["부호전환수"], g["관문2재료"]))
    if 결.get("앵커보탬"):
        b = 결["앵커보탬"]
        print("  앵커 보탬 — %s · 보탠 해 %s · %s · 사업연도수 %s · 부호전환 %s · 보존 %s" % (
            b.get("앵커"), b.get("보탠해"), "바뀜" if b.get("바뀜") else "같음(쓰지 않음)", b.get("사업연도수"), b.get("부호전환수"), b.get("보존")))
    for x in 결["경보"]:
        print("  ※ " + x)
    return 종료판정(결)


if __name__ == "__main__":
    sys.exit(main())

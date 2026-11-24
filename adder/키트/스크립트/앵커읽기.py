# -*- coding: utf-8 -*-
"""앵커읽기 — DART 단일회사 전체 재무제표(`fnlttSinglAcntAll`) 한 해의 손익 항목에서 매출 · 영업이익을 읽는 한 곳.

`dart_fetch.py`(앵커 받기 · 관문 ② 재료)와 `자체검사.py`(⑱ 시나리오 스팬의 관측 이익률)가 **같은 읽기**를 쓴다
(S2-16 — 두 갈래가 따로 읽다 한쪽만 해를 잃는 일이 있었다: A3 는 `account_id` 를 먼저 보고 앵커는 이름만 봤다).

읽는 순서 — 회사 유형 무관(계정 이름 · 표준계정코드로만 본다)
  1. 계정 이름을 **맞춘 꼴**로 견준다 — 앞의 번호 머리(「Ⅰ.」 「1.」 「가.」 「(1)」)와 빈칸을 떼고 본다.
     실측(S1 재리뷰 R2-01): 「Ⅰ.매출액」 「Ⅱ. 매출원가」 꼴로 적는 회사의 해가 통째로 빠졌다.
  2. 이름이 하나도 안 걸리면 표준계정코드(`account_id`)로 본다 — 매출 `ifrs-full_Revenue` 꼴, 영업이익 `dart_OperatingIncomeLoss` 꼴.
  3. 그래도 없으면 금융업 계정(이자수익 · 보험수익 …)으로 본다 — 잡히면 「금융업」 표지를 함께 낸다(값이 잡혔다고 DCF 가 되는 것이 아니다).
못 구하면 None 이다(0 으로 메우지 않는다). 부르는 쪽은 「읽지 못한 해」를 목록으로 남긴다.
"""
import re

매출이름 = ("매출액", "수익(매출액)", "영업수익", "매출", "수익")
영업이름 = ("영업이익", "영업이익(손실)", "영업손실", "영업손익", "영업이익(손익)")
# 표준계정코드 — 이름이 안 걸릴 때(2026-09-13 펄어비스: 「영업이익」 → 「영업손익」 으로 바뀐 해가 통째로 빠졌다)
매출코드 = ("ifrs-full_Revenue", "ifrs_Revenue", "dart_Revenue")
영업코드 = ("dart_OperatingIncomeLoss", "ifrs-full_ProfitLossFromOperatingActivities")
# 금융업은 「매출액」 계정이 없다 — 이자수익 · 보험수익 · 수수료수익으로 나뉜다(실측 KB금융)
금융매출이름 = ("이자수익", "보험수익", "수수료수익", "영업수익(이자수익)", "순이자수익", "영업수익 합계")

# 앞의 번호 머리 — 로마 숫자(「Ⅰ.」 · 「II.」) · 아라비아 숫자(「1.」 · 「1)」) · 한글 차례(「가.」) · 괄호 번호(「(1)」 · 「(가)」)
_번호머리 = re.compile(r"^\s*(?:[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ]+\s*[\.．·]?|[IVX]+\s*[\.．]|\d+\s*[\.．\)]|[가-하]\s*[\.．\)]|\(\s*[\d가-하]+\s*\))\s*")


def 이름맞춤(나):
    """계정 이름의 맞춘 꼴 — 앞의 번호 머리와 모든 빈칸을 뗀다(「Ⅰ.매출액」 · 「1. 매 출 액」 → 「매출액」)."""
    s = ("%s" % (나 or "")).strip()
    s = _번호머리.sub("", s, count=1)
    s = re.sub(r"\(\s*주[\d,\s석]*\)\s*$", "", s)          # 뒤의 주석 번호(「매출액(주3)」 · 「(주석 4,5)」)
    return re.sub(r"\s+", "", s)


_맞춘 = {}


def _맞춘묶음(이름들):
    k = tuple(이름들)
    if k not in _맞춘:
        _맞춘[k] = {이름맞춤(x) for x in 이름들}
    return _맞춘[k]


def _손익(it):
    return (it.get("sj_div") or "").strip() in ("IS", "CIS")


def _수(it):
    s = (it.get("thstrm_amount") or "").replace(",", "").strip()
    if not s or s in ("-", "--"):
        return None, False
    음 = s.startswith("(") and s.endswith(")")                  # 괄호 = 음수(원문에서 옮긴 값)
    try:
        v = float(s.strip("()"))
        return (-v if 음 else v), True
    except ValueError:
        return None, True


def 이름값(items, 이름들):
    """손익 항목에서 이름(맞춘 꼴)으로 한 계정을 뽑는다 → (값, 원래 이름). 못 구하면 (None, None).
    **`sj_div` 는 `IS` 가 아니라 `CIS` 로 오는 회사가 많다** — 둘 다 받는다."""
    찾 = _맞춘묶음(이름들)
    for it in items or []:
        if not _손익(it):
            continue
        나 = (it.get("account_nm") or "").strip()
        if 이름맞춤(나) in 찾:
            v, 있다 = _수(it)
            if 있다:
                return v, 나
    return None, None


def 코드값(items, 코드들):
    """`이름값` 과 같되 표준계정코드(`account_id`)로 찾는다 → (값, 코드)."""
    for it in items or []:
        if not _손익(it):
            continue
        c = (it.get("account_id") or "").strip()
        if c in 코드들:
            v, 있다 = _수(it)
            if 있다:
                return v, c
    return None, None


def 매출한해(items):
    """(값, 무엇으로 잡았나, 금융업이냐) — 이름 → 표준계정코드 → 금융업 계정 차례."""
    v, 나 = 이름값(items, 매출이름)
    if 나 is not None:
        return v, 나, False
    v, c = 코드값(items, 매출코드)
    if c is not None:
        return v, c, False
    v, 나 = 이름값(items, 금융매출이름)
    if 나 is not None:
        return v, 나, True
    return None, None, False


def 영업한해(items):
    """(값, 무엇으로 잡았나) — 이름 → 표준계정코드 차례."""
    v, 나 = 이름값(items, 영업이름)
    if 나 is not None and v is not None:
        return v, 나
    v2, c = 코드값(items, 영업코드)
    if c is not None and v2 is not None:
        return v2, c
    return v, 나


def 해마진(해):
    """앵커 한 해({"사업연도", "list"}) → (사업연도, 영업이익률, 매출) 또는 읽지 못했으면 (사업연도, None, 까닭)."""
    매, _무엇, _금 = 매출한해(해.get("list"))
    영, _w = 영업한해(해.get("list"))
    if not 매:
        return 해.get("사업연도"), None, "매출을 못 읽음(이름 · 표준계정코드 · 금융업 계정 모두 안 걸림)"
    if 영 is None:
        return 해.get("사업연도"), None, "영업이익을 못 읽음(이름 · 표준계정코드 모두 안 걸림)"
    return 해.get("사업연도"), 영 / 매, 매

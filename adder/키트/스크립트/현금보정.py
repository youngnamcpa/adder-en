# -*- coding: utf-8 -*-
"""현금보정 — **회사마다 보정한 뒤 중앙값.** βU(보정) = βU ÷ (1 − (현금 + 단기투자) ÷ 기업가치).

왜 본체에 있나 (세일즈포스 회차 2026-09-13)
  미국 조립기에 현금보정 칸이 없어 C2 가 보정을 통째로 빠뜨렸고, 3번 시트가 보정 전 βU 1.0841 로
  섰다가 검증 V1(H9)이 잡았다. 회차가 `_raw/peers/현금보정.py` 를 손으로 만들어 1.1485 로 고쳤고
  주당가치가 130.75 → 126.38 달러로 바뀌었다. 그 스크립트를 일반형으로 올린 것이 이 파일이다.

정의
  기업가치 = 기준일 시가총액 + 차입금(βU 에 쓴 바로 그 D). 현금 = 앵커일(기준일 이전 최신
  재무상태표일)의 현금및현금성자산. 단기투자 = 같은 날의 단기투자 표현 중 최댓값(같은 줄의 다른
  표현이라 더하지 않는다). `CashCashEquivalentsAndShortTermInvestments` 가 있으면 대조한다.

회차가 만난 함정 둘 — 규약(기본값)
  ① **멈춘 단기투자 태그**(INTU 2023-01-31 · XYZ 2023-06-30 · IBM 2018-03-31 실측): 태그가
     앵커일보다 이르게 끝났으면 **합산하지 않고 「최신 연도 없음」 경보**를 단다. 확장 태그로
     옮겼을 수 있으니 값이 크면 주석 확인 사유로 올린다. 조용히 옛 값을 쓰지 않는다.
  ② **외화 공시 회사**(NTES CNY 실측): 같은 날 USD 편의환산 사실이 있으면 그것 → 없으면 같은
     서류의 USD/원통화 비율 → `환율_{기준일}.json`(peer_환율.py 산출, 읽기만) → 그래도 없으면
     **보정에서 제외하고 확인 불가**로 적는다. 잔액일이 기준일보다 6개월 넘게 이르면(20-F 연 1회)
     경보를 단다.
  보정에서 뺀 회사는 보정 전 βU 만 병기하고 표본 수에서 뺀다 — 「못 구한 회사는 보정에서
  빼고 그 사실을 적는다」.

사용 (보통은 peer_βU_us.py 가 불러 쓴다):
    from 현금보정 import 현금비중
    r = 현금비중(cf, "2026-07-31", 시가총액=..., 차입금=..., 환율경로=...)
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peer_차입금 import 사실표, _환산기  # noqa: E402

현금태그 = ("CashAndCashEquivalentsAtCarryingValue", "CashAndCashEquivalents", "Cash",
         "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents")
단기투자태그 = ("ShortTermInvestments", "MarketableSecuritiesCurrent",
           "AvailableForSaleSecuritiesDebtSecuritiesCurrent", "OtherShortTermInvestments",
           "HeldToMaturitySecuritiesCurrent", "DebtSecuritiesCurrent", "CurrentInvestments",
           "ShortTermDepositsNotClassifiedAsCashEquivalents", "TimeDepositsCurrent")
합산태그 = ("CashCashEquivalentsAndShortTermInvestments",)
재무상태표태그 = ("Liabilities", "Assets", "LiabilitiesAndStockholdersEquity", "Equity")


def _개월차(a, b):
    return (int(b[:4]) - int(a[:4])) * 12 + int(b[5:7]) - int(a[5:7])


def 현금비중(cf, 기준일, 시가총액, 차입금, 환율경로=None):
    """한 회사의 현금비중 — dict(현금, 단기투자, 합계, 잔액일, 기업가치, 비중, 경보, 확인불가, 근거)."""
    쓴것, 경보 = [], []
    표 = 사실표(cf, 기준일)
    환산 = _환산기(표, 환율경로, 쓴것, 경보)
    앵커일 = max([표.최신일(t) for t in 재무상태표태그 if 표.최신일(t)], default=None)
    out = {"현금": None, "현금태그": None, "단기투자": 0, "단기투자태그": None, "합계": None,
           "잔액일": 앵커일, "기업가치": None, "비중": None, "경보": 경보, "근거": 쓴것,
           "확인불가": None, "주석확인_필요": False}
    if not 앵커일:
        out["확인불가"] = "재무상태표 사실 없음"
        return out

    def 값(tag):
        v = 표.값(tag, 앵커일)
        if v is None:
            return None
        u = 환산(v[0], v[1], 앵커일)
        return (u, v[1], v[0])

    현금 = None
    for t in 현금태그:
        x = 값(t)
        if x is not None:
            현금 = (t,) + x
            break
    if 현금 is None:
        out["확인불가"] = "앵커일 %s 에 현금 태그 없음" % 앵커일
        return out
    if 현금[1] is None:
        out["확인불가"] = "현금이 %s 이고 USD 로 환산할 근거가 없다" % 현금[2]
        return out
    if 현금[0].startswith("CashCashEquivalentsRestricted"):
        경보.append("현금이 제한현금 포함 태그(%s) — 과대 가능" % 현금[0])
    if 현금[2] != "USD":
        쓴것.append("현금 %s %.0fm → USD %.0fm" % (현금[2], 현금[3] / 1e6, 현금[1] / 1e6))

    # 단기투자 — 앵커일 값의 최댓값 · 멈춘 태그는 경보만
    st = []
    for t in 단기투자태그:
        x = 값(t)
        if x is not None:
            if x[0] is None:
                경보.append("단기투자 %s 환산 불가 — 제외" % t)
                continue
            st.append((t,) + x)
            continue
        d = 표.최신일(t)
        if d and d < 앵커일:
            v = 표.값(t, d)
            if v and v[0]:
                경보.append("단기투자 태그 %s 가 %s(%.0fm %s)에서 멈춤 — 최신 연도 없음, 합산 안 함"
                          % (t, d, v[0] / 1e6, v[1]))
                if _개월차(d, 앵커일) > 15:
                    쓴것.append("멈춘 태그 %s — 확장 태그로 옮겼을 수 있다(재무상태표 확인)" % t)
    단기 = max(st, key=lambda z: z[1]) if st else None
    if 단기:
        out["단기투자"], out["단기투자태그"] = 단기[1], 단기[0]
        if len(st) > 1:
            쓴것.append("단기투자 표현 %s — 최댓값 %s 를 씀(더하지 않음)"
                        % (" · ".join("%s=%.0fm" % (z[0], z[1] / 1e6) for z in st), 단기[0]))
    합계 = 현금[1] + (단기[1] if 단기 else 0)
    합 = 값(합산태그[0])
    if 합 and 합[0] is not None:
        if abs(합[0] - 합계) > 0.01 * max(합[0], 1):
            경보.append("CashCashEquivalentsAndShortTermInvestments %.0fm ≠ 현금+단기 %.0fm → 큰 쪽"
                      % (합[0] / 1e6, 합계 / 1e6))
            합계 = max(합계, 합[0])
        else:
            쓴것.append("합산 태그와 일치(%.0fm)" % (합[0] / 1e6))
    if _개월차(앵커일, 기준일) > 6:
        경보.append("잔액일 %s 가 기준일 %s 보다 6개월 넘게 이르다" % (앵커일, 기준일))
    out.update({"현금": 현금[1], "현금태그": 현금[0], "합계": 합계})
    if not 시가총액:
        out["확인불가"] = "시가총액 없음"
        return out
    if 차입금 is None:
        out["확인불가"] = "차입금 확인 불가 — 기업가치를 세우지 않음"
        return out
    ev = 시가총액 + 차입금
    out["기업가치"] = ev
    out["비중"] = 합계 / ev if ev else None
    if out["비중"] is not None and out["비중"] >= 0.9:
        경보.append("현금비중 %.0f%% — 보정이 발산한다" % (out["비중"] * 100))
    out["주석확인_필요"] = any("멈춤" in w for w in 경보)
    return out


def 보정(βU, 비중):
    if βU is None or 비중 is None or 비중 >= 1:
        return None
    return βU / (1 - 비중)

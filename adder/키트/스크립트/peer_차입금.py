# -*- coding: utf-8 -*-
"""후보의 **차입금**을 companyfacts 전체에서 넓게 훑는다. 태그를 고정하지 않는다.

왜 이렇게 하는가 (실측)
  - **CLSK** 는 `LongTermDebtNoncurrent` 가 2020-12-31 에서 멈추고 실제 차입은
    `LongTermDebt` / `LongTermLoansPayable` 에 1,780m 으로 올라온다.
    한 태그만 보면 **무차입 회사(5m)** 로 잡혀 βU 가 통째로 어긋난다.
  - **HUT** 은 `LongTermDebt*` 가 2024-12-31(301m)에서 멈추고 2026-06-30 차입은
    `DebtInstrumentCarryingAmount` 7,735m 에만 있다.
  - **BTDR**(IFRS)은 `Borrowings`·`ShorttermBorrowings`·`OtherBorrowings` 가 **같은 360m**이다.
    더하면 배로 부푼다.
  - **WULF** 는 `OtherLongTermDebtNoncurrent == LongTermDebtNoncurrent` 라
    전환사채(2,087m)가 그 밖에 따로 있다.

2026-09-13 개정 (세일즈포스 회차 C2 가 주석으로 고친 다섯 곳 — `C2_차입금_확정.json`)
  - **ADBE** — `DebtCurrent` 를 몰라 유동 1,843m 이 통째로 빠졌다(5,240m → 확정 7,065m).
    ADBE 는 `LongTermDebt` 를 **비유동 줄**에 달았다(정의상은 유동 포함). 그래서
    「총액형 태그가 유동을 포함하는가」를 **같은 회사의 다른 날짜에서 대조해** 가른다.
  - **IBM** — `DebtInstrumentCarryingAmount`(유동 포함 총액)에 `ShortTermBorrowings`
    (유동성장기부채 5,772m 포함)를 또 더하고 금융리스를 다시 더했다(73,351m → 확정 65,272m).
    이제 **비유동 + 유동의 구조**를 한 날짜에서 세우고, 총액형은 대조에만 쓴다.
    `LongTermDebtAndCapitalLeaseObligations*` 를 썼으면 금융리스는 안에 있으므로 안 더한다.
  - **NTES** — CNY 리스를 USD 로 더했다. 이제 **모든 성분이 통화를 달고 다니고**,
    USD 가 아니면 같은 서류의 편의환산 비율(20-F) → `환율_{기준일}.json` → 확인 불가 순으로
    환산한다. 환산 못 한 성분은 합계에 넣지 않고 총차입금을 비운다.
  - **SHOP** — 2022-12-31 리스·상환한 전환사채가 남았다. 이제 **최근 연차 재무상태표일보다
    이르게 멈춘 태그는 「멈춘 태그」로 뺀다**(값이 커도).
  - **XYZ** — 창고금융(`SecuredDebt*`). 기본값은 **포함**(D 판정 원칙 셋을 만족) —
    다만 소비자 대출채권 조달이라 캡티브 성격이므로 `총차입금_담보부제외` 를 나란히 낸다.
    비유동 창고금융은 확장 태그라 companyfacts 에 없다(실측 589,556천) → 주석 큐에 올린다.

규칙 (한 줄씩)
  ① 앵커일 = 기준일 이전 최신 재무상태표일(Assets·Liabilities…). 연차일 = 최신 연차서류의 그 날.
  ② 연차일보다 이르게 멈춘 태그는 뺀다(멈춘 태그). 앵커일에 차입 태그가 하나도 없으면
     연차일 이후의 가장 최근 날짜 구조를 쓰고 **주석 큐**에 올린다.
  ③ 한 날짜에서: 비유동(N) + 유동(C). 같은 줄의 다른 표현은 최댓값(더하면 중복).
     C = DebtCurrent 가 있으면 그것, 없으면 유동성장기(L)·단기차입(S)을 포함관계 판정 뒤 합.
     N 이 없으면 총액형(T)을 쓰고, T 가 유동을 포함하는지는 다른 날짜 대조로 가른다.
  ④ 전환사채·담보부 차입은 「포함될 수 없을 때만」 더한다. 리스는 운용·금융·IFRS 묶음별로
     가장 최근 표현을 쓴다.
  ⑤ **판정이 안 서면 합산 쪽으로 가되 경보를 달고 주석 큐에 올린다** — 조용히 고르지 않는다.
  → 잡힌 태그·버린 태그·판정 근거를 `잡힌것` 에, 요약을 `경보` 에 전부 남긴다.

사용:
    python 스크립트/peer_차입금.py --tickers ADBE,IBM --기준일 2026-07-31
    python 스크립트/peer_차입금.py --tickers NTES --기준일 2026-07-31 --캐시 회차/_raw/peers
    python 스크립트/peer_차입금.py --tickers <티커> --기준일 2026-10-23 --재무기준일 2026-06-30   # 날짜 둘 — 앵커일은 F 이하(T 앞 최신 분기가 아니다)
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEER = os.environ.get("DCF_PEER_CACHE") or os.path.join(ROOT, "_raw", "peers")   # 손개입 개선 1 — 사슬 `--캐시` 가 환경변수로 닿는다(종전에는 하위 도구가 키트 _raw/peers 에 썼다)

연차서식 = {"10-K", "10-K/A", "10-KT", "20-F", "20-F/A", "40-F", "40-F/A"}
정기서식 = 연차서식 | {"10-Q", "10-Q/A", "6-K", "6-K/A"}

# 같은 줄의 다른 표현들 — 그룹 안에서는 **더하지 않고 최댓값**
비유동태그 = ("LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations",
          "OtherLongTermDebtNoncurrent", "LongTermLoansPayable", "LongTermNotesPayable",
          "SeniorLongTermNotes", "UnsecuredLongTermDebt", "LongTermLineOfCredit",
          "NoncurrentPortionOfNoncurrentBorrowings", "LongtermBorrowings")
유동장기태그 = ("LongTermDebtCurrent", "LongTermDebtAndCapitalLeaseObligationsCurrent",
            "OtherLongTermDebtCurrent", "LoansPayableCurrent", "LongTermNotesPayableCurrent",
            "CurrentPortionOfNoncurrentBorrowings", "CurrentPortionOfLongtermBorrowings")
단기태그 = ("ShortTermBorrowings", "ShorttermBorrowings", "CommercialPaper", "OtherShortTermBorrowings",
         "ShortTermBankLoansAndNotesPayable", "NotesAndLoansPayable", "NotesPayableCurrent",
         "BankOverdrafts", "LinesOfCreditCurrent", "BridgeLoan", "CurrentBorrowings")
유동총액태그 = ("DebtCurrent",)
총액태그 = ("LongTermDebt", "DebtInstrumentCarryingAmount", "DebtLongtermAndShorttermCombinedAmount",
         "LoansPayable", "DebtAndCapitalLeaseObligations", "Borrowings", "OtherBorrowings")
전환태그 = ("ConvertibleDebtNoncurrent", "ConvertibleDebtCurrent", "ConvertibleDebt",
         "ConvertibleNotesPayable", "ConvertibleNotesPayableCurrent", "ConvertibleLongTermNotesPayable")
담보태그 = ("SecuredDebtCurrent", "SecuredLongTermDebt", "SecuredDebt")
리스묶음 = (("운용", "OperatingLeaseLiability", "OperatingLeaseLiabilityCurrent",
          "OperatingLeaseLiabilityNoncurrent"),
         ("금융", "FinanceLeaseLiability", "FinanceLeaseLiabilityCurrent",
          "FinanceLeaseLiabilityNoncurrent"),
         ("IFRS", "LeaseLiabilities", "CurrentLeaseLiabilities", "NoncurrentLeaseLiabilities"))
재무상태표태그 = ("Liabilities", "Assets", "LiabilitiesAndStockholdersEquity", "Equity",
             "EquityAndLiabilities")
전부차입태그 = 비유동태그 + 유동장기태그 + 단기태그 + 유동총액태그 + 총액태그 + 전환태그 + 담보태그


# ────────────────────────── 네트워크(캐시가 없을 때만) ──────────────────────────
def get_cf(cik, tic, 캐시=None):
    p = os.path.join(캐시 or PEER, "cf_%s.json" % tic)
    if os.path.exists(p):
        return json.load(io.open(p, encoding="utf-8")), "캐시"
    contact = os.environ.get("SEC_CONTACT_EMAIL")
    if not contact:     # 캐시만 쓰는 재실행·시험은 이 변수가 없어도 돈다
        sys.exit("환경변수 SEC_CONTACT_EMAIL 이 없습니다(%s companyfacts 캐시 없음)." % tic)
    import requests
    H = {"User-Agent": "DCF-research %s" % contact, "Accept-Encoding": "gzip, deflate"}
    for i in range(3):
        try:
            r = requests.get("https://data.sec.gov/api/xbrl/companyfacts/CIK%010d.json" % cik,
                             headers=H, timeout=300)
            if r.status_code == 200:
                io.open(p, "w", encoding="utf-8").write(r.text)
                time.sleep(0.3)
                return r.json(), "신규"
        except requests.RequestException:
            pass
        time.sleep(2.0 * (i + 1))
    return None, "조회 실패"


# ────────────────────────── 사실 색인 ──────────────────────────
class 사실표:
    """태그 → {end: {통화: (val, filed, form, accn, tax)}} — 시점값(start 없음)만, 기준일까지."""

    def __init__(self, cf, 기준일):
        self.기준일 = 기준일
        self.표 = {}
        self.서식 = {}
        for tax in ("us-gaap", "ifrs-full"):
            for tag, 몸 in (cf.get("facts", {}).get(tax) or {}).items():
                for u, arr in (몸.get("units") or {}).items():
                    if not isinstance(u, str) or len(u) != 3 or not u.isupper():
                        continue      # 통화 코드만 — 주식수·비율 단위는 뺀다
                    for x in arr:
                        if x.get("start") or x.get("end", "9") > 기준일:
                            continue
                        if x.get("form") and x["form"] not in 정기서식:
                            continue  # 8-K·S-4 의 재작성 표는 쓰지 않는다
                        d = self.표.setdefault(tag, {}).setdefault(x["end"], {})
                        옛 = d.get(u)
                        if 옛 is None or x.get("filed", "") > 옛[1]:
                            d[u] = (x["val"], x.get("filed", ""), x.get("form"), x.get("accn"), tax)
                        # 연차 판정은 **가장 늦게 낸 서류가 아니라 낸 서류 전부**로 한다 — 연차 잔액이
                        # 다음 10-Q 에 비교표로 다시 실려 오면 마지막 서식이 10-Q 가 된다(CDNS·NOW 실측)
                        self.서식.setdefault(tag, {}).setdefault(x["end"], set()).add(x.get("form"))

    def 날짜들(self, tag):
        return sorted((self.표.get(tag) or {}).keys())

    def 최신일(self, tag):
        ds = self.날짜들(tag)
        return ds[-1] if ds else None

    def 값(self, tag, end):
        """(val, 통화, tax) — 같은 날 USD 가 있으면 USD."""
        d = (self.표.get(tag) or {}).get(end)
        if not d:
            return None
        u = "USD" if "USD" in d else sorted(d)[0]
        return d[u][0], u, d[u][4]

    def 연차날짜들(self, tag):
        return sorted(end for end, 폼 in (self.서식.get(tag) or {}).items() if 폼 & 연차서식)


def _환산기(표, 환율경로, 쓴것, 경보):
    """통화 → USD. ① 같은 날 재무상태표의 USD/원통화 편의환산 비율 ② 환율 캐시 ③ 확인 불가."""
    환율 = {}
    환율일 = None
    if 환율경로 and os.path.exists(환율경로):
        try:
            j = json.load(io.open(환율경로, encoding="utf-8"))
            환율 = j.get("USD환산계수(1통화당 USD)") or {}
            환율일 = j.get("기준일")
        except Exception:
            환율 = {}
    적은 = set()

    def 환산(val, 통화, end):
        if val is None or 통화 == "USD":
            return val
        for tag in ("Liabilities", "Assets", "LiabilitiesAndStockholdersEquity"):
            d = (표.표.get(tag) or {}).get(end) or {}
            if "USD" in d and 통화 in d and d[통화][0]:
                r = d["USD"][0] / d[통화][0]
                if (통화, end, "편의") not in 적은:
                    쓴것.append("통화 %s → USD: 같은 서류 편의환산 비율 %s(%s/%s) = 1 %s 당 %.6f USD (%s)"
                                % (통화, tag, "USD", 통화, 통화, r, end))
                    적은.add((통화, end, "편의"))
                return val * r
        if 통화 in 환율:
            if (통화, "환율") not in 적은:
                쓴것.append("통화 %s → USD: 환율 캐시 %s 1 %s = %.6f USD — **잔액일 %s 와 환율일이 다르다**"
                            % (통화, 환율일, 통화, 환율[통화], end))
                경보.append("%s 잔액을 기준일 환율로 환산(잔액일 %s)" % (통화, end))
                적은.add((통화, "환율"))
            return val * 환율[통화]
        if (통화, "불가") not in 적은:
            쓴것.append("**통화 %s 를 USD 로 환산할 근거가 없다** — 편의환산 없음·환율 캐시에 %s 없음" % (통화, 통화))
            경보.append("%s 환산 불가 — 확인 불가" % 통화)
            적은.add((통화, "불가"))
        return None
    return 환산


def 계산(cf, 기준일, 환율경로=None, _원통화=False):
    쓴것, 경보, 큐 = [], [], []
    표 = 사실표(cf, 기준일)
    환산 = (lambda v, c, e: v) if _원통화 else _환산기(표, 환율경로, 쓴것, 경보)

    # ① 앵커일·연차일
    앵커일 = max([표.최신일(t) for t in 재무상태표태그 if 표.최신일(t)], default=None)
    연차 = sorted({d for t in 재무상태표태그 for d in 표.연차날짜들(t)})
    연차일 = 연차[-1] if 연차 else None
    쓴것.append("앵커일(최신 재무상태표) %s · 연차일(최신 연차서류) %s" % (앵커일, 연차일))
    바닥 = 연차일 or 앵커일 or "0000"

    # ② 멈춘 태그
    멈춤 = []
    for t in 전부차입태그 + tuple(x for g in 리스묶음 for x in g[1:]):
        d = 표.최신일(t)
        if d and d < 바닥:
            v = 표.값(t, d)
            if v and v[0]:
                멈춤.append("%s=%.0fm %s@%s" % (t, v[0] / 1e6, v[1], d))
    if 멈춤:
        쓴것.append("멈춘 태그(연차일 %s 보다 이름 · 값이 커도 안 씀): %s" % (바닥, " · ".join(멈춤)))

    # 구조 날짜 — 앵커일에 차입 태그가 없으면 연차일 이후 가장 최근 날짜
    구조태그 = 비유동태그 + 유동장기태그 + 단기태그 + 유동총액태그 + 총액태그
    후보일 = sorted({d for t in 구조태그 for d in 표.날짜들(t) if 바닥 <= d <= (앵커일 or 기준일)})
    구조일 = None
    if 앵커일 and any(표.값(t, 앵커일) for t in 구조태그):
        구조일 = 앵커일
    elif 후보일:
        구조일 = 후보일[-1]
        경보.append("앵커일 %s 에 차입 태그 없음 — %s 구조를 씀" % (앵커일, 구조일))
        큐.append("앵커일에 차입 태그가 없다(확장 태그로 옮겼거나 상환) — 주석에서 %s 잔액 확인" % 앵커일)

    def 그룹(태그들, end):
        """[(tag, val_usd, 통화, 원값)] — 환산 못 한 것은 val_usd=None."""
        out = []
        if not end:
            return out
        for t in 태그들:
            v = 표.값(t, end)
            if v is None:
                continue
            out.append((t, 환산(v[0], v[1], end), v[1], v[0]))
        return out

    def 최대(g):
        ok = [x for x in g if x[1] is not None]
        if not ok:
            return None
        return max(ok, key=lambda x: x[1])

    def 적(이름, g):
        if g:
            쓴것.append("%s @%s: %s" % (이름, 구조일, " · ".join(
                "%s=%s%s" % (t, ("%.0fm" % (u / 1e6)) if u is not None else "환산불가",
                             "" if c == "USD" else "(%s %.0fm)" % (c, o / 1e6)) for t, u, c, o in g)))

    환산불가 = False
    N_g, L_g, S_g = 그룹(비유동태그, 구조일), 그룹(유동장기태그, 구조일), 그룹(단기태그, 구조일)
    DC_g, T_g = 그룹(유동총액태그, 구조일), 그룹(총액태그, 구조일)
    for 이름, g in (("비유동(N)", N_g), ("유동성장기(L)", L_g), ("단기차입(S)", S_g),
                  ("유동총액(DebtCurrent)", DC_g), ("총액형(T)", T_g)):
        적(이름, g)
        if any(x[1] is None for x in g):
            환산불가 = True
    N, L, S, DC = 최대(N_g), 최대(L_g), 최대(S_g), 최대(DC_g)
    Nv, Lv, Sv = (N[1] if N else 0), (L[1] if L else 0), (S[1] if S else 0)
    T_vals = [x for x in T_g if x[1] is not None]

    def 가까운T(합):
        if not T_vals:
            return None
        return min(T_vals, key=lambda x: abs(x[1] - 합))

    # 과거 날짜에서 「DebtCurrent == 단기차입 표현」이면 그 회사의 단기 줄은 유동 총액이다
    def _단기가_유동총액인가():
        for d in 표.날짜들("DebtCurrent"):
            if not (바닥 <= d <= (구조일 or "")):
                continue
            dc = 표.값("DebtCurrent", d)
            for t in 단기태그:
                s = 표.값(t, d)
                if dc and s and dc[1] == s[1] and dc[0] and abs(dc[0] - s[0]) <= 0.005 * abs(dc[0]):
                    return "%s 에 DebtCurrent(%.0fm) == %s" % (d, dc[0] / 1e6, t)
        return None

    # ③-1 유동
    C, C설명 = 0, "유동 차입 태그 없음"
    if DC:
        C, C설명 = DC[1], "DebtCurrent %.0fm (유동성장기·단기차입을 포함하는 정의라 L·S 는 따로 안 더함)" % (DC[1] / 1e6)
    elif L and S and Lv and Sv:
        합, 포함 = Lv + Sv, max(Lv, Sv)
        판정 = None
        t = 가까운T(Nv + 합) if N else None
        if t:
            e합, e포 = abs(Nv + 합 - t[1]), abs(Nv + 포함 - t[1])
            if min(e합, e포) <= 0.03 * t[1] and abs(e합 - e포) > 0.01 * t[1]:
                판정 = ("포함" if e포 < e합 else "합산", "총액형 %s %.0fm 대조(오차 합산 %.0fm · 포함 %.0fm)"
                      % (t[0], t[1] / 1e6, e합 / 1e6, e포 / 1e6))
        if 판정 is None and Sv < 0.99 * Lv:
            판정 = ("합산", "단기 %s %.0fm 이 유동성장기 %.0fm 보다 작다 — 포함일 수 없다" % (S[0], Sv / 1e6, Lv / 1e6))
        if 판정 is None and abs(Sv - Lv) <= 0.01 * max(Sv, Lv):
            판정 = ("포함", "%s %.0fm ≈ %s %.0fm — 같은 줄의 두 표현" % (S[0], Sv / 1e6, L[0], Lv / 1e6))
        if 판정 is None:
            근거 = _단기가_유동총액인가()
            if 근거 and Sv >= Lv:
                판정 = ("포함", "단기차입 줄이 유동 총액이다 — " + 근거)
        if 판정 is None:
            판정 = ("합산", "포함관계 판정 불가 — 합산(과대 가능 %.0fm)" % (min(Lv, Sv) / 1e6))
            경보.append("유동성장기 %s·단기 %s 포함관계 판정 불가 → 합산" % (L[0], S[0]))
            큐.append("유동성장기부채가 단기차입 줄에 포함됐는지 재무상태표로 확인")
        C = 포함 if 판정[0] == "포함" else 합
        C설명 = "유동 = %s %.0fm (%s)" % (판정[0], C / 1e6, 판정[1])
    elif L or S:
        x = L or S
        C, C설명 = x[1], "유동 = %s %.0fm" % (x[0], x[1] / 1e6)
    쓴것.append(C설명)

    # ③-2 비리스 기본
    기본태그 = None
    if N:
        B = Nv + C
        기본태그 = N[0]
        설명 = "비유동 %s %.0fm + 유동 %.0fm" % (N[0], Nv / 1e6, C / 1e6)
        t = 가까운T(B)
        # 2026-10-25 FX4-P — 단기 태그가 여럿(CP · 은행 단기차입 등)이면 「같은 줄의 다른 표현 → 최댓값」 이 틀릴 수 있다 — 서로 다른 줄이면 합이다.
        # 비유동 + 유동성장기 + 단기 줄들의 합이 총액형 태그와 ±1% 안이면 그 조립을 자동 확정한다(포함관계 판정 대신 총액 대조 — C2 다시 셈 2조 ·
        # CP 를 빠뜨려 −4.5% 어긋난 회사)
        _S값 = list(dict.fromkeys(x[1] for x in S_g if x[1]))
        if T_vals and DC is None and len(_S값) >= 2 and not (t and abs(B - t[1]) <= 0.01 * t[1]):
            _B2 = Nv + Lv + sum(_S값)
            _t2 = 가까운T(_B2)
            if _t2 and abs(_B2 - _t2[1]) <= 0.01 * _t2[1]:
                쓴것.append("단기 줄 여럿(%s)이 서로 다른 줄 — 합 %.0fm 으로 조립하면 총액형 %s %.0fm 과 %+.2f%%(±1%% 안 · 자동 확정)" % (
                    " · ".join("%s %.0fm" % (x[0], x[1] / 1e6) for x in S_g if x[1]), sum(_S값) / 1e6, _t2[0], _t2[1] / 1e6, (_B2 / _t2[1] - 1) * 100))
                C, B, t = Lv + sum(_S값), _B2, _t2
                Sv = sum(_S값)
                S = ("+".join(x[0] for x in S_g if x[1]), Sv, S[2] if S else "USD", Sv)
                설명 = "비유동 %s %.0fm + 유동성장기 %.0fm + 단기 줄 합 %.0fm(총액형 대조로 확정)" % (N[0], Nv / 1e6, Lv / 1e6, sum(_S값) / 1e6)
                큐[:] = [q for q in 큐 if "단기차입 줄에 포함" not in q]
                경보[:] = [g for g in 경보 if "포함관계 판정 불가" not in g]
        if T_vals:
            tmax = max(T_vals, key=lambda x: x[1])
            # 한 표현이라도 조립과 2% 안에서 맞으면 구조가 선 것이다. `DebtInstrumentCarryingAmount` 는
            # 이름과 달리 **액면**으로 오는 회사가 많아(MSFT 46,136 vs 장부 40,294 · CIFR 실측)
            # 그것 하나만 크다고 조립을 버리지 않는다
            if t and abs(B - t[1]) <= 0.02 * t[1]:
                tmax = (None, 0)
            if tmax[1] > B * 1.05 and tmax[1] - B > 1e6:
                경보.append("총액형 %s %.0fm 이 조립 %.0fm 보다 5%% 넘게 큼 → 총액형을 씀" % (tmax[0], tmax[1] / 1e6, B / 1e6))
                큐.append("총액형 태그가 비유동+유동 조립보다 크다 — 빠진 줄이 있는지 확인")
                설명 += " → 총액형 %s %.0fm 로 대체(조립이 5%% 넘게 작음)" % (tmax[0], tmax[1] / 1e6)
                B, 기본태그 = tmax[1] + (Sv if (Sv and not DC and C == Lv + Sv) else 0), tmax[0]
            else:
                설명 += " · 총액형 %s %.0fm 과 대조 %+.1f%%" % (t[0], t[1] / 1e6, (B / t[1] - 1) * 100 if t[1] else 0)
    elif T_vals:
        # 장부 표현을 액면(DebtInstrumentCarryingAmount)보다 먼저 쓴다 — 없을 때만 액면
        장부 = [x for x in T_vals if x[0] != "DebtInstrumentCarryingAmount"]
        tmax = max(장부 or T_vals, key=lambda x: x[1])
        if 장부 and len(장부) < len(T_vals):
            쓴것.append("총액형은 장부 표현(%s)을 씀 — DebtInstrumentCarryingAmount 는 액면일 수 있어 대조로만" % tmax[0])
        기본태그 = tmax[0]
        if not (DC or L or S):
            B, 설명 = tmax[1], "총액형 %s %.0fm (여러 표현 중 최댓값 · 유동 태그 없음)" % (tmax[0], tmax[1] / 1e6)
        elif abs(tmax[1] - C) <= 0.005 * max(tmax[1], 1):
            B, 설명 = tmax[1], "총액형 %s %.0fm == 유동 %.0fm — 같은 것(더하지 않음)" % (tmax[0], tmax[1] / 1e6, C / 1e6)
        else:
            # 총액형이 유동을 포함하는가 — 같은 회사의 다른 날짜에서 둘째 총액형(또는 N)과 대조
            판정 = None
            for d in reversed(표.날짜들(tmax[0])):
                if not (바닥 <= d < 구조일):
                    continue
                c_d = 표.값("DebtCurrent", d) or next((표.값(x, d) for x in 유동장기태그 if 표.값(x, d)), None)
                if not c_d or not c_d[0]:
                    continue
                t_d = 표.값(tmax[0], d)
                기준들 = [(x, 표.값(x, d)) for x in 총액태그 if x != tmax[0] and 표.값(x, d)]
                if not 기준들 or not t_d:
                    continue
                x, r = 기준들[0]
                e포함, e제외 = abs(t_d[0] - r[0]), abs(t_d[0] + c_d[0] - r[0])
                if abs(e포함 - e제외) > 0.02 * r[0]:
                    판정 = ("제외" if e제외 < e포함 else "포함",
                          "%s 에 %s %.0fm vs %s %.0fm (유동 %.0fm)" % (d, tmax[0], t_d[0] / 1e6, x, r[0] / 1e6, c_d[0] / 1e6))
                    break
            if 판정 is None:
                if C > tmax[1]:
                    판정 = ("제외", "유동 %.0fm 이 총액형보다 큼 — 포함일 수 없다" % (C / 1e6))
                elif DC is None and L and not S and tmax[0] in ("LongTermDebt", "DebtInstrumentCarryingAmount"):
                    판정 = ("포함", "정의상 %s 는 유동성장기를 포함 — 단기차입 태그 없음" % tmax[0])
                elif DC is None and S and not L and tmax[0] in ("LongTermDebt", "DebtInstrumentCarryingAmount",
                                                               "LoansPayable"):
                    판정 = ("제외", "단기차입(%s)은 정의상 %s 밖이다 — 유동성장기 태그 없음" % (S[0], tmax[0]))
            if 판정 is None:
                판정 = ("제외", "판정 불가 — 유동을 더함(과대 가능 %.0fm)" % (C / 1e6))
                경보.append("총액형 %s 가 유동을 포함하는지 판정 불가 → 더함" % tmax[0])
                큐.append("%s 가 유동분을 포함하는지 재무상태표로 확인" % tmax[0])
            if 판정[0] == "제외":
                B = tmax[1] + C
            else:   # 포함 — 유동성장기는 안에 있고, 단기차입(S)은 LongTermDebt 밖이다
                B = tmax[1] + (Sv if (S and not DC) else 0)
            설명 = "총액형 %s %.0fm 이 유동을 %s (%s) → %.0fm" % (tmax[0], tmax[1] / 1e6, 판정[0], 판정[1], B / 1e6)
    else:
        B = C
        설명 = "비유동·총액형 태그 없음 — 유동만 %.0fm" % (C / 1e6)
        if C:
            기본태그 = (DC or L or S)[0]
    쓴것.append("기본차입: " + 설명)

    # ④-1 전환사채
    전환 = 0
    cv_g = 그룹(전환태그, 구조일 if 구조일 else 앵커일)
    if not cv_g and 앵커일 and 앵커일 != 구조일:
        cv_g = 그룹(전환태그, 앵커일)
    cvd = {t: u for t, u, c, o in cv_g if u is not None}
    전환후보 = max(cvd.get("ConvertibleDebtNoncurrent", 0) + cvd.get("ConvertibleDebtCurrent", 0),
               cvd.get("ConvertibleDebt", 0),
               cvd.get("ConvertibleNotesPayable", 0) + cvd.get("ConvertibleNotesPayableCurrent", 0),
               cvd.get("ConvertibleLongTermNotesPayable", 0))
    otn = 표.값("OtherLongTermDebtNoncurrent", 구조일) if 구조일 else None
    ltn = 표.값("LongTermDebtNoncurrent", 구조일) if 구조일 else None
    if 전환후보:
        별도 = bool((otn and ltn and ltn[0] and abs(otn[0] - ltn[0]) / max(ltn[0], 1) < 0.02)
                  or B == 0 or 전환후보 > B)
        if 별도:
            전환 = 전환후보
            쓴것.append("전환사채 별도 가산 %.0fm — 기본차입(%.0fm)에 포함될 수 없는 크기이거나 "
                      "OtherLongTermDebt == LongTermDebt" % (전환 / 1e6, B / 1e6))
        else:
            쓴것.append("전환사채 태그 있음(%.0fm) — 위 차입 표현에 포함된 것으로 보고 가산하지 않음" % (전환후보 / 1e6))
    elif cv_g:
        쓴것.append("전환사채 태그가 0 으로 명시됨(%s) — 상환·전환 완료로 봄" % ", ".join(x[0] for x in cv_g))

    # ④-2 담보부(창고금융) — 기본 포함, 제외 대조 병기
    담보 = 0
    sg = {t: u for t, u, c, o in 그룹(담보태그, 구조일) if u is not None}
    담보후보 = max(sg.get("SecuredDebtCurrent", 0) + sg.get("SecuredLongTermDebt", 0), sg.get("SecuredDebt", 0))
    if 담보후보:
        조립 = Nv + C if N else B
        t = 가까운T(조립)
        if t and abs(조립 - t[1]) <= 0.01 * t[1]:
            담보 = 담보후보
            쓴것.append("담보부 차입(창고금융 등) %.0fm 가산 — 기본차입이 총액형 %s 로 이미 다 설명돼 "
                      "담보부는 그 밖이다. **기본값 포함**(이자·만기·조달 셋 만족). 캡티브 성격이면 "
                      "총차입금_담보부제외 를 쓴다" % (담보 / 1e6, t[0]))
            경보.append("담보부 차입 %.0fm 포함(기본값) — 제외 대조 병기" % (담보 / 1e6))
        else:
            쓴것.append("담보부 차입 태그 %.0fm — 기본차입에 포함됐는지 판정 불가라 **안 더함**" % (담보후보 / 1e6))
            경보.append("담보부 차입 %.0fm 포함 여부 판정 불가 → 안 더함" % (담보후보 / 1e6))
            큐.append("담보부 차입(창고금융·자산담보부)이 차입금 줄에 포함됐는지 확인")
        if "SecuredDebtCurrent" in sg and "SecuredLongTermDebt" not in sg and "SecuredDebt" not in sg:
            큐.append("담보부 유동분만 표준 태그에 있다 — 비유동분이 확장 태그에 있을 수 있음(주석 확인)")
            경보.append("담보부 비유동분 표준 태그 없음")

    # ④-3 리스
    리스 = 0
    금융리스포함 = any((x or ("",))[0].startswith("LongTermDebtAndCapitalLeaseObligations")
                  for x in (N, L) if x) or 기본태그 == "DebtAndCapitalLeaseObligations"
    for 이름, 총, 유, 비 in 리스묶음:
        if 이름 == "금융" and 금융리스포함:
            fl = 표.최신일(총) or 표.최신일(비)
            if fl and fl >= 바닥:
                쓴것.append("금융리스는 %s 에 포함된 것으로 보고 안 더함" % ((N or L)[0] if (N or L) else 기본태그))
            continue
        cands = []
        dA = 표.최신일(총)
        if dA and dA >= 바닥:
            v = 표.값(총, dA)
            cands.append(("총", dA, 환산(v[0], v[1], dA), "%s@%s" % (총, dA), v[1]))
        du, dn = 표.최신일(유), 표.최신일(비)
        du = du if du and du >= 바닥 else None
        dn = dn if dn and dn >= 바닥 else None
        if du or dn:
            vu = 표.값(유, du) if du else None
            vn = 표.값(비, dn) if dn else None
            uu = 환산(vu[0], vu[1], du) if vu else 0
            nn = 환산(vn[0], vn[1], dn) if vn else 0
            합 = None if (uu is None or nn is None) else (uu or 0) + (nn or 0)
            cands.append(("유비" if (du and dn) else "유비_반쪽", max(x for x in (du, dn) if x), 합,
                          "%s@%s + %s@%s" % (유, du, 비, dn), (vu or vn)[1]))
        if not cands:
            continue
        # 가장 최근 날짜 표현을 쓴다(옛 판은 날짜를 안 보고 큰 쪽 — ADBE 가 2025-11-28 값을 씀)
        # 같은 날이면 유동+비유동 완전한 쪽 > 총 > 반쪽(한쪽만 태깅 — 과소)
        cands.sort(key=lambda x: (x[1] if x[0] != "유비_반쪽" or len(cands) == 1 else "0",
                                  {"유비": 2, "총": 1, "유비_반쪽": 0}[x[0]]))
        골 = cands[-1]
        if 골[2] is None:
            환산불가 = True
            continue
        if 골[0] == "유비_반쪽":
            쓴것.append("리스(%s) 유동·비유동 중 한쪽만 태깅됨 — 과소 가능" % 이름)
            경보.append("리스(%s) 한쪽만 태깅 — 과소 가능" % 이름)
        if 골[0] == "유비" and du and dn and du != dn:
            쓴것.append("리스(%s) 유동·비유동 날짜가 다르다(%s / %s) — 각자 최신값" % (이름, du, dn))
        if 골[2]:
            리스 += 골[2]
            쓴것.append("리스(%s) %.0fm — %s%s" % (이름, 골[2] / 1e6, 골[3],
                                              "" if 골[4] == "USD" else " (%s 환산)" % 골[4]))
            if 앵커일 and 골[1] < 앵커일:
                쓴것.append("  리스(%s) 는 앵커일 %s 보다 이른 %s 값 — 분기에 태깅하지 않는 회사" % (이름, 앵커일, 골[1]))

    # 부채총계
    부채, 부채일, 부채설명 = None, None, None
    if 앵커일:
        v = 표.값("Liabilities", 앵커일)
        if v:
            부채, 부채일 = 환산(v[0], v[1], 앵커일), 앵커일
        else:
            tot = 표.값("LiabilitiesAndStockholdersEquity", 앵커일)
            eq = (표.값("StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest", 앵커일)
                  or 표.값("StockholdersEquity", 앵커일))
            if tot and eq and tot[1] == eq[1]:
                부채, 부채일 = 환산(tot[0] - eq[0], tot[1], 앵커일), 앵커일
                부채설명 = "Liabilities 태그 없음 — 부채와자본총계 − 자본으로 대체"
                쓴것.append(부채설명)

    원통화합 = None
    if 환산불가:
        총 = None
        큐.append("통화 환산 불가 — 원통화 금액만 있다")
        if not _원통화:
            try:
                _r = 계산(cf, 기준일, None, _원통화=True)
                원통화합 = _r["총차입금"]
            except Exception:
                원통화합 = None
    else:
        총 = B + 전환 + 담보 + 리스
    원통화 = None
    for g in (N_g, L_g, S_g, DC_g, T_g):
        for t, u, c, o in g:
            if c != "USD":
                원통화 = c
    if not (N_g or L_g or S_g or DC_g or T_g or cv_g or sg):
        큐.append("차입 태그가 하나도 안 잡힘 — 무차입인지 이름을 못 찾은 것인지 주석 확인")
        경보.append("차입 태그 0 — 주석 큐")

    if 구조일 is None and 앵커일 is None:
        신선 = False
    else:
        _d = 구조일 or 앵커일
        try:
            _y, _m = int(기준일[:4]), int(기준일[5:7])
            _t = _m - 15
            문턱 = "%04d-%02d-%s" % (_y + (_t - 1) // 12, (_t - 1) % 12 + 1, 기준일[8:10])
        except Exception:
            문턱 = "0000"
        신선 = _d >= 문턱
        if not 신선 and (B or 전환):
            쓴것.append("**차입 구조일 %s 가 평가기준일(%s)보다 15개월 이상 이르다 — 확인 필요**" % (_d, 기준일))
            큐.append("차입 구조일이 15개월 넘게 묵음")
    return {"총차입금": 총, "총차입금_담보부제외": (총 - 담보) if 총 is not None else None,
            "총차입금_원통화": 원통화합, 
            "차입기준일_신선": 신선, "앵커일": 앵커일, "연차일": 연차일, "차입구조일": 구조일,
            "기본차입": B, "기본차입태그": 기본태그, "기본차입일": 구조일,
            "기본차입통화": "USD" if not 원통화 else "%s(USD 환산)" % 원통화,
            "유동차입": C, "단기차입": Sv if (S and not DC) else 0, "단기차입태그": S[0] if (S and not DC) else None,
            "전환사채가산": 전환, "담보부가산": 담보, "리스부채": 리스,
            "부채총계": 부채, "부채총계일": 부채일, "부채총계_비고": 부채설명,
            "차입_부채비율": (총 / 부채) if (총 is not None and 부채) else None,
            "멈춘태그": 멈춤, "경보": 경보, "주석확인_필요": bool(큐), "주석큐사유": 큐,
            "잡힌것": 쓴것}


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--tickers", required=True)
    ap.add_argument("--기준일", "--평가기준일", dest="기준일", default="2026-06-30", help="평가기준일 T(분석일 · 시장 쪽 — 종가 · 시가총액 · 주식수 · 베타 창 끝 · 환율 · 법령 시행일) YYYY-MM-DD")
    ap.add_argument("--캐시", default=None, help="_raw/peers 대신 쓸 캐시 폴더")
    ap.add_argument("--재무기준일", default=None, help="재무 자료 기준일 F YYYY-MM-DD — 차입 · 부채총계를 F 이하의 마지막 재무상태표에서 읽는다"
                                                   "(앵커일 = F 이전 최신 재무상태표일). 비우면 평가기준일과 같다(날짜 둘 — 환율은 T)")
    ap.add_argument("--환율", default=None, help="환율_{기준일}.json (없으면 캐시 폴더에서 찾는다)")
    a = ap.parse_args()
    캐시 = a.캐시 or PEER
    재기 = a.재무기준일 or a.기준일                         # 날짜 둘 — 장부 값(차입 · 부채총계)은 F, 환율 · 파일의 기준일은 T
    if 재기.replace("-", "") > a.기준일.replace("-", ""):
        sys.exit("--재무기준일 %s 가 평가기준일 %s 보다 늦다" % (재기, a.기준일))
    환율 = a.환율 or os.path.join(캐시, "환율_%s.json" % a.기준일.replace("-", ""))
    for t in [x.strip().upper() for x in a.tickers.split(",") if x.strip()]:
        sp = os.path.join(캐시, "sub_%s.json" % t)
        cfp = os.path.join(캐시, "cf_%s.json" % t)
        if not os.path.exists(sp) and not os.path.exists(cfp):
            print("%-6s *** sub·companyfacts 캐시 없음" % t)
            continue
        cik = json.load(io.open(sp, encoding="utf-8"))["cik"] if os.path.exists(sp) else None
        cf, how = get_cf(cik, t, 캐시)
        if cf is None:
            print("%-6s *** companyfacts %s — 조용히 빼지 않는다" % (t, how))
            continue
        d = 계산(cf, 재기, 환율경로=환율 if os.path.exists(환율) else None)
        d.update({"티커": t, "cik": cik, "기준일": a.기준일, "재무기준일": 재기})
        json.dump(d, io.open(os.path.join(캐시, "debt_%s.json" % t), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        m = lambda v: ("%.0fm" % (v / 1e6)) if v is not None else "확인 불가"
        print("%-6s [%s] 총차입 %9s = 기본 %s(%s@%s) + 전환 %s + 담보 %s + 리스 %s | 부채총계 %s (비율 %s)%s"
              % (t, how, m(d["총차입금"]), m(d["기본차입"]), d["기본차입태그"], d["차입구조일"],
                 m(d["전환사채가산"]), m(d["담보부가산"]), m(d["리스부채"]),
                 ("%s@%s" % (m(d["부채총계"]), d["부채총계일"])) if d["부채총계"] else "확인 불가",
                 ("%.2f" % d["차입_부채비율"]) if d["차입_부채비율"] else "-",
                 ("\n       ★ 주석 큐: " + " / ".join(d["주석큐사유"])) if d["주석확인_필요"] else ""))
        for w in d["경보"]:
            print("       경보: " + w)


if __name__ == "__main__":
    main()

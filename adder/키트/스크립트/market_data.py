# -*- coding: utf-8 -*-
"""평가기준일 고정 시장데이터를 한 번만 받아 캐시한다.

무위험이자율·시장위험프리미엄·국가위험프리미엄·등급별 부도 스프레드는
평가기준일과 국가가 정해지면 바뀌지 않는 값이다. 등급 하나씩, 값 하나씩
따로 받으면 왕복이 늘고 조회일이 갈라진다. **한 번에 받아 한 파일에 담는다.**

캐시 파일: _raw/시장데이터_{국가}_{평가기준일}.json
  - 이미 있으면 네트워크를 타지 않는다. --refresh 를 줘야 다시 받는다
  - 값마다 값·출처·기준일·확인상태 네 칸을 같이 저장한다. 기준일≠조회일이면 둘 다 남는다
  - 스프레드는 스프레드대로 담는다. Kd = Rf + 스프레드 구조가 캐시에서도 유지된다

**찾는 순서: 작업폴더 `_raw/` → 공용 캐시 → 네트워크.** 받으면 양쪽에 쓴다.
공용 캐시 자리는 `~/.dcf캐시/` 이고 환경변수 `DCF_공용캐시` 로 덮을 수 있다.
평가기준일과 국가가 정해지면 안 바뀌는 값만 공용으로 둔다 — 종목 고유 값은 절대 안 둔다.
공용에서 집어 왔으면 화면과 각 값의 비고 칸에 그 사실을 적는다.

**거시지표(CPI·평균임금 등)는 이 파일이 함께 받는다.** 회사의 매출·이익·자산은
여전히 공시(DART·SEC)에서만 받는다 — 거시지표만 예외이고 그 사실을 근거 칸에 적는다.
저자 가정: 받은 값이 **추정기간 내내 그대로 유지된다.** 연도별로 다르게 만들지 않는다.

**국가 부도위험을 두 번 세지 않는다(2026-10-17, S7-01 — 무위험이자율 · 시장위험프리미엄 입력 규칙).** 표시통화 국채 수익률에는 그 나라의
부도 스프레드가 들어 있고, 다모다란 국가 행의 「Total Equity Risk Premium」 은 성숙시장 ERP + 국가위험프리미엄(CRP)이다.
국채를 그대로 Rf 로 두고 Total 을 MRP 로 곱하면 국가위험이 Rf 와 MRP 에 두 번 들어간다. 다모다란 성숙시장 ERP 자체가
「부도 스프레드를 뺀 달러 무위험이자율」 위에서 계산된 값이다(같은 판 3행 설명). 그래서 이 도구는 국가 행에서 넷을 따로 담는다 —
    국채 수익률(표시통화 10년) · 국가 부도스프레드(Rating-based Default Spread) · 성숙시장 위험프리미엄(같은 판 상단) · 국가위험프리미엄(CRP)
그리고 `--가정제안` 이 가정의 `구조.할인.무위험이자율 = 부도스프레드차감` 과 WACC 넷(`국채수익률 · 부도스프레드 · 성숙시장프리미엄 ·
국가위험프리미엄`)을 낸다. 부도 스프레드 · CRP 는 **같은 판 같은 국가 행**에서 읽는다(판이 섞이면 짝이 어긋난다).

**표시통화 국가(`--country`)는 ISO 두 글자 또는 다모다란 국가 이름이다**(S7-12). KR · US 밖의 나라는 ERP · 부도 스프레드 · CRP 를
같은 ctryprem 국가 행에서 읽고, 국채 수익률은 ① `--국채수익률`(그 나라 재무부 · 중앙은행 공표 값 — 사람이 출처와 함께 준다) 또는
② `--기대물가 현지,미국`(다모다란 대체식 — 미 국채 10년 × (1 + 현지 기대물가) ÷ (1 + 미국 기대물가) − 1)로 낸다. 대체식이면
확인상태가 「참고」다. 둘 다 없으면 국채 수익률은 「확인 불가」로 남긴다 — 비슷한 나라 값으로 메우지 않는다.

**날짜 둘(2026-10-25 · `기준일.py`) — 시장 쪽 도구다.** `--date`(별칭 `--평가기준일`)는 **평가기준일 T**(분석일)다 — 지금 뜻 그대로.
캐시 이름 `시장데이터_{국가}_{T}.json` · 국채 · 회사채 · ERP 판 · CRP · 부도 스프레드 · 국가 한계세율 · 거시지표가 모두 T 에 선다.
재무기준일(F · 최근 공시 분기말)로 받지 않는다. `--가정` 을 주면 `--date` 를 비워도 가정의 메타.평가기준일을 쓴다(F 와 다르면 F 가 아니라 T).

사용:
    python 스크립트/market_data.py --date 2026-06-30 --country US
    python 스크립트/market_data.py --가정 가정.json --country KR                 # 날짜는 가정의 평가기준일 T
    python 스크립트/market_data.py --date 2026-06-30 --country KR
    python 스크립트/market_data.py --date 2026-06-30 --country US --refresh
    python 스크립트/market_data.py --date 2026-06-30 --country KR --가정제안 제안.json
    python 스크립트/market_data.py --date 2026-06-30 --country KR --오프라인
    python 스크립트/market_data.py --date 2026-06-30 --country JP --국채수익률 0.0152 --국채출처 "일본 재무성 국채금리 10년"
    python 스크립트/market_data.py --date 2026-06-30 --country IN --기대물가 0.045,0.025
    python 스크립트/market_data.py --date 2026-06-30 --country TW --국채수익률 0.0170 --국채출처 "…" --물가 0.0166 --물가출처 "…"
      (대만 · 세계은행 표에 없는 나라 — 국채와 물가를 그 나라 공표 기관 값으로 · 2026-10-24)
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import os
import sys

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "_raw")          # 폴더는 쓸 때 만든다(import 때 만들면 본체에 빈 `_raw/` 가 생긴다)
H = {"User-Agent": "Mozilla/5.0"}
TODAY = dt.date.today().isoformat()
# **다모다란 주소를 박아 두지 않는다**(키트 CLAUDE.md 「데이터 소스」 — 자료 페이지의 링크에서 찾는다 · 안 보이면 멈춘다, 2026-10-16 S1 리뷰).
# 자료 페이지를 읽어 파일 링크를 고르고(`다모다란주소`), 그 디렉터리를 판 파일들(July · 보관판)의 바탕으로 쓴다.
# 아래 주소는 링크를 못 찾았을 때 「확인 불가」 안내 문장에만 쓴다 — 받는 데 쓰지 않는다.
자료페이지 = "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datacurrent.html"
_DAMO안내 = "https://pages.stern.nyu.edu/~adamodar/pc/datasets/"
# 캐시 꼴의 판 — 공용 캐시가 이 판이 아니면(옛 꼴) 쓰지 않는다. 꼴(칸 · 경보 규칙)을 바꾸면 올린다
# 2026-10-17(S7-01) — 국가 행 넷(부도 스프레드 · 성숙시장 · CRP · Total)과 차감 무위험이자율 · 국가 세율 칸을 더했다
캐시판 = "2026-10-17"

# ISO 두 글자 → 다모다란 ctryprem 「ERPs by country」 의 국가 이름. 표에 없는 나라는 `--국가이름` 으로 다모다란 표기를 준다
국가이름 = {"KR": "Korea", "US": "United States", "JP": "Japan", "TW": "Taiwan", "CN": "China", "HK": "Hong Kong",
        "SG": "Singapore", "IN": "India", "VN": "Vietnam", "ID": "Indonesia", "TH": "Thailand", "MY": "Malaysia",
        "PH": "Philippines", "AU": "Australia", "NZ": "New Zealand", "CA": "Canada", "MX": "Mexico", "BR": "Brazil",
        "GB": "United Kingdom", "DE": "Germany", "FR": "France", "NL": "Netherlands", "CH": "Switzerland", "IT": "Italy",
        "ES": "Spain", "SE": "Sweden", "DK": "Denmark", "NO": "Norway", "FI": "Finland", "IE": "Ireland", "BE": "Belgium",
        "AT": "Austria", "IL": "Israel", "SA": "Saudi Arabia", "AE": "United Arab Emirates", "ZA": "South Africa",
        "TR": "Turkey", "PL": "Poland"}
# 국채 수익률 칸 이름 — 캐시의 옛 이름을 그대로 둔다(KR · US). 그 밖의 나라는 한 이름
국채칸 = {"KR": "무위험이자율 (국고채 10년)", "US": "무위험이자율 (미 국채 10년)"}


def 국채칸이름(country):
    return 국채칸.get(country, "무위험이자율 (국채 10년)")
_링크표 = None


def 다모다란주소(fn):
    """자료 페이지(datacurrent.html)의 링크에서 파일 `fn` 의 주소 → (주소, None) · 못 찾으면 (None, 까닭)."""
    global _링크표
    import re
    from urllib.parse import urljoin
    if _링크표 is None:
        try:
            r = _get(자료페이지, timeout=60)
            r.raise_for_status()
            _링크표 = {}
            for x in re.findall(r"""href\s*=\s*["']([^"'#]+)["']""", r.text, re.I):
                u = urljoin(자료페이지, x.strip())
                _링크표.setdefault(os.path.basename(u).lower(), u)
        except Exception as e:                               # noqa: BLE001 — 오프라인 · 막힘
            _링크표 = {"__실패": "%s" % type(e).__name__}
    u = _링크표.get(fn.lower())
    if u:
        return u, None
    if "__실패" in _링크표:
        return None, "자료 페이지를 못 열었다(%s) — 받지 않는다. 손으로 확인할 곳: %s · 옛 주소 %s%s" % (
            _링크표["__실패"], 자료페이지, _DAMO안내, fn)
    return None, "자료 페이지에 %s 링크가 없다 — 멈춘다(주소를 짐작하지 않는다). 옛 주소 %s%s 는 손으로만 확인" % (fn, _DAMO안내, fn)


def DAMO바탕():
    """판 파일의 바탕 디렉터리 — 자료 페이지의 ctryprem.xlsx 링크가 든 곳. 못 찾으면 None."""
    u, _ = 다모다란주소("ctryprem.xlsx")
    return (u.rsplit("/", 1)[0] + "/") if u else None


def _four(val, src, base_date, status, note=""):
    return {"값": val, "출처": src, "기준일": base_date, "조회일": TODAY,
            "확인상태": status, "비고": note}


# ══ 공용 캐시 ═══════════════════════════════════════════════════════════
# 「작업 폴더 밖을 만들지 않는다」 규칙의 유일한 예외다. 평가기준일과 국가가
# 정해지면 안 바뀌는 값만 여기 둔다. 종목 고유 값은 절대 두지 않는다.
def 공용캐시폴더():
    d = os.environ.get("DCF_공용캐시") or os.environ.get("DCF_SHARED_CACHE")
    return d or os.path.join(os.path.expanduser("~"), ".dcf캐시")


def 공용캐시경로(country, val_date):
    return os.path.join(공용캐시폴더(), "시장데이터_%s_%s.json" % (country, val_date))


def _공용에쓰기(country, val_date, data):
    """공용 캐시에 같은 내용을 한 벌 더 둔다. 실패해도 본 흐름을 막지 않는다."""
    try:
        p = 공용캐시경로(country, val_date)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump(data, io.open(p, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        return p
    except (OSError, IOError, TypeError, ValueError) as e:    # noqa: BLE001
        return "실패(%s)" % type(e).__name__


def _출처표시(d, 어디):
    """공용에서 집어 왔으면 각 값의 비고 칸에도 그 사실을 남긴다.
    조용히 쓰면 출처가 사라진다."""
    if 어디 == "작업폴더":
        return d
    꼬리 = " · 공용 캐시(%s)에서 가져온 값이다 — 이 종목 폴더에서 새로 받은 것이 아니다" % 어디
    for v in d.values():
        if isinstance(v, dict) and "확인상태" in v:
            if 꼬리.strip(" ·") not in (v.get("비고") or ""):
                v["비고"] = (v.get("비고") or "") + 꼬리
    d["_읽은자리"] = 어디
    return d


def 캐시읽기(country, val_date):
    """작업폴더 → 공용 순으로 본다. 없으면 (None, None).
    **공용 캐시가 지금 판(`캐시판`)이 아니면 쓰지 않는다**(2026-10-16, S1 리뷰 — 옛 꼴 캐시가 경보 붙은 값을 「확인완료」로 모든
    회차에 퍼뜨렸다). 네트워크를 못 타는 실행(--오프라인)에서만 옛 판을 쓰되 확인상태를 「참고」로 낮춘다."""
    작업 = os.path.join(RAW, "시장데이터_%s_%s.json" % (country, val_date))
    if os.path.exists(작업):
        return json.load(io.open(작업, encoding="utf-8")), "작업폴더"
    공용 = 공용캐시경로(country, val_date)
    if os.path.exists(공용):
        d = json.load(io.open(공용, encoding="utf-8"))
        if d.get("_판") != 캐시판:
            if 네트워크:
                return None, None
            for v in d.values():
                if isinstance(v, dict) and "확인상태" in v and v.get("값") is not None:
                    v["확인상태"] = "참고"
                    v["비고"] = ((v.get("비고") or "") + " · 옛 판 공용 캐시(판 %s ≠ %s) — 오프라인이라 참고로만"
                                % (d.get("_판") or "없음", 캐시판)).strip(" ·")
        try:                       # 공용에서 왔으면 작업폴더에도 한 벌 남긴다
            os.makedirs(RAW, exist_ok=True)
            json.dump(d, io.open(작업, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
        except (OSError, IOError):
            pass
        return _출처표시(d, 공용), 공용
    return None, None


# ── 미국: 무위험이자율 — 미 재무부 수익률 곡선 ─────────────────────────
def us_rf(val_date: str):
    p = os.path.join(RAW, "ust_yield_%s.csv" % val_date[:4])
    if not os.path.exists(p):
        u = ("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
             "daily-treasury-rates.csv/%s/all?type=daily_treasury_yield_curve"
             "&field_tdr_date_value=%s&page&_format=csv" % (val_date[:4], val_date[:4]))
        r = requests.get(u, headers=H, timeout=120)
        r.raise_for_status()
        io.open(p, "w", encoding="utf-8").write(r.text)
    rows = list(csv.DictReader(io.open(p, encoding="utf-8")))

    def key(row):
        m, d, y = row["Date"].split("/")
        return "%s-%s-%s" % (y, m, d)

    le = sorted((r for r in rows if key(r) <= val_date), key=key)
    if not le:
        return _four(None, "미국 재무부 Daily Treasury Par Yield Curve", val_date,
                     "확인 불가", "평가기준일 이전 데이터가 연간 CSV 에 없다")
    r = le[-1]
    d = key(r)
    return _four(float(r["10 Yr"]) / 100,
                 "미국 재무부 Daily Treasury Par Yield Curve Rates, 10 Yr",
                 d, "확인완료" if d == val_date else "확인완료(직전영업일)",
                 "평가기준일 당일 값" if d == val_date
                 else "평가기준일이 휴장일이라 직전 영업일 %s 사용" % d)


def 그밖국채(a):
    """KR · US 밖 나라의 10년 국채 수익률(S7-12) — ① 사람이 준 공표 값(--국채수익률 + --국채출처) ② 다모다란 대체식
    (--기대물가 현지,미국: 미 국채 × (1 + 현지) ÷ (1 + 미국) − 1 — 확인상태 참고). 둘 다 없으면 확인 불가(비슷한 나라 값으로 메우지 않는다)."""
    if getattr(a, "국채수익률", None) is not None:
        if not getattr(a, "국채출처", None):
            sys.exit("--국채수익률 에는 --국채출처 를 함께 줍니다(근거 4칸 — 공표 기관 · 자료 이름)")
        return _four(a.국채수익률, a.국채출처, a.국채기준일 or a.date, "확인완료(사람 입력 — 공표 수익률)",
                     "무위험이자율 규칙 — 그 나라 재무부 · 중앙은행 공표 10년 국채. 이 도구가 받지 않고 사람이 준 값이다 — 출처를 다시 볼 수 있게 적는다")
    if getattr(a, "기대물가", None):
        try:
            현지, 미국 = [float(x) for x in a.기대물가.split(",")]
        except ValueError:
            sys.exit("--기대물가 는 「현지,미국」 소수 둘입니다(예: 0.045,0.025)")
        us, 어디 = None, ""
        d, 곳 = 캐시읽기("US", a.date)
        if d and (d.get("무위험이자율 (미 국채 10년)") or {}).get("값") is not None:
            us, 어디 = d["무위험이자율 (미 국채 10년)"], "US 캐시(%s)" % 곳
        elif 네트워크:
            try:
                us, 어디 = us_rf(a.date), "미 재무부"
            except Exception:                                  # noqa: BLE001
                us = None
        if not us or us.get("값") is None:
            return _four(None, "다모다란 대체식(미 국채 × 기대물가 비)", a.date, "확인 불가",
                         "미 국채 10년을 못 읽었다 — `--country US` 캐시를 먼저 받거나 --국채수익률 을 준다")
        v = (1 + us["값"]) * (1 + 현지) / (1 + 미국) - 1
        return _four(v, "다모다란 대체식 — 미 국채 10년 %.4f(%s) × (1 + 현지 기대물가 %.4f) ÷ (1 + 미국 기대물가 %.4f) − 1"
                     % (us["값"], 어디, 현지, 미국), us.get("기준일") or a.date, "참고",
                     "공표 국채가 없거나 못 받을 때의 대체식이다 — 현지 국채에 든 부도 위험이 이미 빠진 값이 아니다. "
                     "이 값에서도 국가 부도스프레드를 뺀다. 기대물가의 출처는 사람이 근거 칸에 적는다")
    return _four(None, "그 나라 재무부 · 중앙은행 공표 10년 국채", a.date, "확인 불가",
                 "KR · US 밖 나라는 이 도구가 국채를 받지 않는다 — --국채수익률(+ --국채출처) 또는 --기대물가 를 준다. "
                 "비슷한 나라 값으로 메우지 않는다")


def WACC제안(d, country):
    """캐시 → 가정 `구조.할인` 과 `WACC.<구간>` 의 무위험이자율 · 시장위험프리미엄 넷 · 근거(101 ~ 104) 제안(S7-01).

    **기본 갈래는 `부도스프레드차감` 이다.** 국채를 그대로 Rf 로 쓰고 Total ERP 를 곱하는 「직접」 은 국가위험을 두 번 센다."""
    g = d.get(국채칸이름(country)) or {}
    부도 = d.get("국가 부도스프레드") or {}
    성숙 = d.get("성숙시장 위험프리미엄") or {}
    국가 = d.get("국가위험프리미엄 (CRP)") or {}
    총 = d.get("시장위험프리미엄 (ERP)") or {}

    def 넷(x, 비고=None):
        return [x.get("출처"), x.get("기준일"), x.get("확인상태"), 비고 if 비고 is not None else x.get("비고")]
    값 = {"국채수익률": g.get("값"), "부도스프레드": 부도.get("값"), "성숙시장프리미엄": 성숙.get("값"), "국가위험프리미엄": 국가.get("값")}
    빈 = [k for k, v in 값.items() if v is None]
    out = {"구조.할인.무위험이자율": "부도스프레드차감",
           "WACC.예측기간": dict(값), "WACC.영구기간": dict(값),
           "WACC근거": {"101": 넷(g), "102": 넷(부도), "103": 넷(성숙), "104": 넷(국가)},
           "무위험이자율_차감후": (값["국채수익률"] - 값["부도스프레드"]) if not ({"국채수익률", "부도스프레드"} & set(빈)) else None,
           "시장위험프리미엄_합": (값["성숙시장프리미엄"] + 값["국가위험프리미엄"])
           if not ({"성숙시장프리미엄", "국가위험프리미엄"} & set(빈)) else None,
           "대조_TotalERP": 총.get("값"),
           "확인불가": 빈,
           "_사용법": ("가정의 `구조.할인.무위험이자율` 을 「부도스프레드차감」 으로 두고 WACC 두 구간에 국채수익률 · 부도스프레드 · "
                    "성숙시장프리미엄 · 국가위험프리미엄 넷을 넣는다(Rf · ERP 옛 키는 넣지 않는다). 근거는 3번 101 ~ 104. "
                    "**「직접」 으로 국채를 그대로 Rf 에 두고 Total ERP 를 곱하지 않는다** — 국가 부도위험이 Rf 와 MRP 에 두 번 든다. "
                    "타인자본비용 = 스프레드 갈래(다모다란 등급 스프레드)는 그 스프레드가 국채 위의 값이라 **스프레드 칸에 등급 스프레드 + 부도스프레드** "
                    "를 넣는다(Kd = 국채 + 등급 스프레드). 관측수익률 갈래(회사채 수익률)는 그대로다")}
    return out


# ── 다모다란 ctryprem: 나라별 ERP·CRP ──────────────────────────────────
# **판 선택 — 발표일이 아니라 「데이터 기준일」로 고른다(펄31 → 2026-09-13 조정자 조문).**
# 숫자 규칙: 「평가기준일 뒤에 나온 문서라도 기준일 **이전의 사실**을 담았으면 쓴다. 기준일 **뒤에
# 처음 생긴** 정보는 값에 넣지 않는다」.
#   · 첫 수리는 Date of update(=발표일)가 기준일 뒤인 판을 전부 버렸다 — 6/30 평가기준일에 7/1판(4.811%)
#     대신 1월판(4.869%, 12/31 자료)을 골랐다. 그런데 7/1판은 **6월 말 자료로 계산한 판**이다(실측 아래).
#   · **데이터 기준일** = 판 안에 날짜가 적힌 산출 자료의 끝 날짜 중 가장 늦은 것:
#       「Default Spreads for Ratings」 머리 `Updated Default Spread (6/30/26)`
#       「10-year CDS Spreads」 머리 `CDS Spread (6/30/26)`
#       「Relative Equity Volatility」 기간 `(July 1, 2021 - June 30, 2026)` 의 끝
#     실측 2026-09-13: ctrypremJuly26 → 셋 다 **2026-06-30** · ctryprem.xlsx(1월판) → 셋 다 2025-12-31.
#     성숙시장 ERP 칸에는 날짜가 없다 — 같은 달 implprem `ERPJuly26.xlsx` 는 「Estimation month (start of)
#     July」·지수 7,499.36 이고, 이 값이 S&P 500 **2026-06-30 종가**(회차 캐시 wk__INX 7,499.36)와 같다.
#     (implprem 대조는 자동으로 하지 않는다 — 비고에 「ERP 칸 날짜 표시 없음」을 적는다)
#   · 기본 정책 「데이터기준일」: 데이터 기준일 ≤ 평가기준일 인 판 중 **가장 늦은 판**. 발표일이 기준일 뒤면
#     **비고로만** 적는다. 데이터 기준일 > 평가기준일 인 판은 고르지 않고 경보(건너뜀 목록).
#     데이터 기준일을 **확인할 수 없는 판**은 「확인 불가」로 적고, 확인되는 판이 하나도 없을 때만
#     **발표일 ≤ 평가기준일** 인 판으로 보수적으로 가며 경보한다.
#   · 판 이름(실측): 7월판 datasets/ctrypremJulyYY.xlsx · 1월판은 날짜판이 없고 현행 datasets/ctryprem.xlsx
#     → 해가 지나면 archives/ctrypremYY.xlsx (ctrypremJan26.xlsx 는 404)
ERP판정책 = "데이터기준일"   # 데이터기준일(기본) / 발표일: 발표일 ≤ 기준일 판만 / 가까운: 옛 동작 + 경보


def _판후보(val_date: str, 정책: str = None):
    """(파일이름, 받을 주소, 명목 데이터 기준일). 현행판은 명목 None(열어서 잰다)."""
    정책 = 정책 or ERP판정책
    y = int(val_date[:4])
    # 바탕은 자료 페이지의 링크에서 — 못 찾으면 주소 없이(None) 후보를 낸다. 받아 둔 판 파일이 `_raw/` 에 있으면 그것을 쓴다
    DAMO = DAMO바탕()
    ARCH = DAMO.replace("/datasets/", "/archives/") if DAMO else None
    july = lambda k: ("ctrypremJuly%02d.xlsx" % (k % 100), (DAMO + "ctrypremJuly%02d.xlsx" % (k % 100)) if DAMO else None,
                      "%04d-06-30" % k)
    jan_arch = lambda k: ("ctryprem%02d_archive.xlsx" % (k % 100), (ARCH + "ctryprem%02d.xlsx" % (k % 100)) if ARCH else None,
                          "%04d-12-31" % (k - 1))
    현행 = ("ctryprem.xlsx", 다모다란주소("ctryprem.xlsx")[0], None)
    if 정책 == "가까운":
        m = int(val_date[5:7])
        return ([july(y)] if m >= 6 else []) + [현행, jan_arch(y), july(y - 1)]
    if 정책 == "발표일":
        return ([july(y)] if val_date >= "%04d-07-01" % y else []) + [현행, jan_arch(y), july(y - 1), jan_arch(y - 1)]
    return [현행, jan_arch(y + 1), july(y), jan_arch(y), july(y - 1), jan_arch(y - 1)]


def _판날짜(p):
    """Date of update(발표일)."""
    import openpyxl
    wb = openpyxl.load_workbook(p, data_only=True, read_only=True)
    ws = wb["ERPs by country"]
    upd = next(ws.iter_rows(min_row=2, max_row=2, values_only=True))[1]
    wb.close()
    return upd.strftime("%Y-%m-%d") if hasattr(upd, "strftime") else str(upd)[:10]


_월 = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def 데이터기준일라벨(칸들):
    """[(시트, 글자)] → [(날짜, 근거)]. 판 안에 적힌 산출 자료 날짜만 읽는다(추측하지 않는다)."""
    import re
    out = []
    for 시트, 글 in 칸들:
        글 = str(글)
        for m in re.finditer(r"(?:Updated Default Spread|CDS Spread)\s*\((\d{1,2})/(\d{1,2})/(\d{2,4})\)", 글):
            yy = int(m.group(3))
            yy = yy + 2000 if yy < 100 else yy
            out.append(("%04d-%02d-%02d" % (yy, int(m.group(1)), int(m.group(2))), "%s 「%s」" % (시트, m.group(0))))
        m = re.search(r"-\s*([A-Za-z]{3})[a-z]*\.?\s+(\d{1,2}),\s*(\d{4})\)", 글)
        if m and m.group(1).lower() in _월 and 시트.startswith("Relative Equity"):
            out.append(("%s-%02d-%02d" % (m.group(3), _월[m.group(1).lower()], int(m.group(2))),
                        "%s 기간 「%s」" % (시트, 글.strip()[:60])))
    return out


def _판데이터기준일(p):
    """(데이터 기준일 또는 None, 근거 목록)."""
    import openpyxl
    wb = openpyxl.load_workbook(p, data_only=True, read_only=True)
    칸들 = []
    for 시트, 줄수 in (("Default Spreads for Ratings", 2), ("10-year CDS Spreads", 2), ("Relative Equity Volatility", 14)):
        if 시트 not in wb.sheetnames:
            continue
        for row in wb[시트].iter_rows(min_row=1, max_row=줄수, values_only=True):
            칸들 += [(시트, v) for v in row if isinstance(v, str)]
    wb.close()
    라벨 = 데이터기준일라벨(칸들)
    근거 = []
    for _, 근 in 라벨:
        if 근 not in 근거:
            근거.append(근)
    return (max(d for d, _ in 라벨) if 라벨 else None), 근거


def _판열기(fn, url):
    p = os.path.join(RAW, fn)
    if os.path.exists(p):
        return p, None
    if not url:
        return None, "%s 주소 확인 불가 — %s" % (fn, 다모다란주소(fn if fn == "ctryprem.xlsx" else "ctryprem.xlsx")[1] or "바탕 없음")
    os.makedirs(RAW, exist_ok=True)
    try:
        r = _get(url, timeout=180)
        if r.status_code == 200 and len(r.content) > 100000:
            open(p, "wb").write(r.content)
            return p, None
        return None, "%s 없음(HTTP %s)" % (fn, r.status_code)
    except requests.RequestException as e:
        return None, "%s 못 받음(%s)" % (fn, type(e).__name__)


def 판고르기(열린, val_date):
    """열어 본 판 [(데이터기준일|None, 발표일, 파일명, …)] → (고른 판, 경보 목록, 방식). 순수 함수(시험용)."""
    경보 = []
    불가 = [x for x in 열린 if x[0] is None]
    뒤 = [x for x in 열린 if x[0] and x[0] > val_date]
    for x in 뒤:
        경보.append("%s 는 데이터 기준일 %s > 평가기준일 — 고르지 않음" % (x[2], x[0]))
    좋은 = sorted([x for x in 열린 if x[0] and x[0] <= val_date], key=lambda x: (x[0], x[1]))
    if 좋은:
        if 불가:
            경보.append("데이터 기준일을 못 읽은 판이 있다: " + " / ".join("%s(발표일 %s)" % (x[2], x[1]) for x in 불가))
        return 좋은[-1], 경보, "데이터기준일"
    보수 = sorted([x for x in 불가 if x[1] <= val_date], key=lambda x: x[1])
    if 보수:
        경보.append("데이터 기준일 확인 불가 — 발표일(%s) ≤ 평가기준일 인 판으로 보수적으로 씀" % 보수[-1][1])
        return 보수[-1], 경보, "보수(발표일)"
    return None, 경보, None


def _ctryprem_file(val_date: str, 정책: str = None):
    """(경로, 파일명, 판 정보 dict, 선택 사유) — 못 찾으면 (None, None, None, 사유).
    판 정보 = {"발표일", "데이터기준일", "데이터기준일_근거", "경보"}."""
    정책 = 정책 or ERP판정책
    본것 = []
    if 정책 in ("가까운", "발표일"):
        for fn, url, 명목 in _판후보(val_date, 정책):
            p, 실패 = _판열기(fn, url)
            if not p:
                본것.append(실패)
                continue
            try:
                upd = _판날짜(p)
                데이터, 근거 = _판데이터기준일(p)
            except Exception as e:                           # noqa: BLE001
                본것.append("%s 날짜 못 읽음(%s)" % (fn, type(e).__name__))
                continue
            if 정책 == "발표일" and upd > val_date:
                본것.append("%s 발표일 %s — 기준일 뒤라 건너뜀" % (fn, upd))
                continue
            경보 = []
            if 데이터 and 데이터 > val_date:
                경보.append("데이터 기준일(%s)이 평가기준일(%s) 뒤다 — 기준일 뒤에 생긴 정보" % (데이터, val_date))
            사유 = "판 선택(%s 정책): %s · 발표일 %s · 데이터 기준일 %s%s" % (
                정책, fn, upd, 데이터 or "확인 불가", (" · 앞서 본 후보: " + " / ".join(본것)) if 본것 else "")
            return p, fn, {"발표일": upd, "데이터기준일": 데이터, "데이터기준일_근거": 근거, "경보": 경보}, \
                ("⚠ 경보 — " + " · ".join(경보) + " · " if 경보 else "") + 사유
        return None, None, None, "판을 못 찾았다: " + (" / ".join(본것) or "후보 없음")

    # 기본 — 데이터 기준일
    열린 = []                       # (데이터기준일, 발표일, fn, p, 근거)
    for fn, url, 명목 in _판후보(val_date, 정책):
        if 명목 and 명목 > val_date:
            continue                # 명목 자료 시점부터 기준일 뒤 — 받지도 않는다
        if 명목 and any(x[0] and 명목 <= x[0] <= val_date for x in 열린):
            continue                # 이미 그보다 늦은(≤ 기준일) 자료의 판을 열었다
        p, 실패 = _판열기(fn, url)
        if not p:
            if 명목:
                본것.append(실패)
            continue
        try:
            열린.append(_판데이터기준일(p)[:1] + (_판날짜(p), fn, p, _판데이터기준일(p)[1]))
        except Exception as e:                               # noqa: BLE001
            본것.append("%s 날짜 못 읽음(%s)" % (fn, type(e).__name__))
    고른, 경보, 방식 = 판고르기(열린, val_date)
    if not 고른:
        return None, None, None, "데이터 기준일 ≤ 평가기준일 인 판을 못 찾았다: " + (" / ".join(본것 + 경보) or "후보 없음")
    데이터, upd, fn, p, 근거 = 고른
    if 방식 == "데이터기준일":
        사유 = ("판 선택(데이터기준일 정책): %s · 데이터 기준일 %s(평가기준일과 %+d일 · 근거 %s) · 발표일 %s%s"
               % (fn, 데이터, (dt.date.fromisoformat(데이터) - dt.date.fromisoformat(val_date)).days,
                  " / ".join(근거), upd,
                  (" — 발표일은 평가기준일 뒤지만 기준일 이전 사실을 담은 판이라 쓴다(비고)" if upd > val_date else "")))
        사유 += " · 성숙시장 ERP 칸에는 날짜 표시가 없다(같은 달 implprem 파일의 월초 추정)"
    else:
        사유 = "판 선택(보수): %s · 발표일 %s · 데이터 기준일 확인 불가" % (fn, upd)
    if 본것:
        사유 += " · 앞서 본 후보: " + " / ".join(본것)
    return p, fn, {"발표일": upd, "데이터기준일": 데이터, "데이터기준일_근거": 근거, "경보": 경보}, \
        ("⚠ 경보 — " + " · ".join(경보) + " · " if 경보 else "") + 사유


def 판경보(d, val_date):
    """캐시(작업폴더·공용)에 담긴 ERP·CRP·스프레드가 **기준일 뒤에 생긴 정보**인지 본다.
    **캐시는 다시 받지 않으므로 옛 판 선택이 조용히 남는다** — 읽을 때마다 센다.
    ERP·CRP 는 `데이터기준일` 칸으로 잰다. 그 칸이 없는 옛 캐시는 기준일 칸이 발표일이라
    사실 시점을 모른다 — 판 파일이 `_raw/` 에 있으면 열어 재고, 없으면 「확인 필요」로 적는다."""
    import re
    out = []
    for k in 다모다란국가칸:
        v = d.get(k) or {}
        if v.get("값") is None:
            continue
        데이터 = v.get("데이터기준일")
        if 데이터:
            if 데이터 > val_date:
                out.append("%s 데이터 기준일 %s > 평가기준일 %s — 기준일 뒤에 생긴 정보" % (k, 데이터, val_date))
            continue
        발표 = str(v.get("기준일") or "")[:10]
        m = re.search(r"(ctryprem\w*\.xlsx)", str(v.get("출처") or ""))
        p = os.path.join(RAW, m.group(1)) if m else None
        if p and os.path.exists(p):
            try:
                데이터 = _판데이터기준일(p)[0]
            except Exception:                                # noqa: BLE001
                데이터 = None
        if 데이터 and 데이터 > val_date:
            out.append("%s 데이터 기준일 %s > 평가기준일 %s(옛 캐시 · %s 로 잼)" % (k, 데이터, val_date, m.group(1)))
        elif not 데이터 and len(발표) == 10 and 발표 > val_date:
            out.append("%s 옛 캐시 — 기준일 칸이 발표일 %s(평가기준일 뒤)이고 데이터 기준일 미기재. 판 파일이 없어 "
                       "사실 시점을 못 쟀다 — 확인 필요(--refresh 면 데이터 기준일을 적는다)" % (k, 발표))
    v = d.get("합성등급 스프레드 표") or {}
    기준 = str(v.get("기준일") or "")[:10]
    if len(기준) == 10 and 기준[4] == "-" and 기준 > val_date:
        꼬리 = ""
        if 기준 == str(v.get("조회일") or "")[:10]:
            꼬리 = " (옛 판 캐시는 조회일을 기준일로 적었다 — 발표일은 --refresh 로 다시 적힌다)"
        out.append("합성등급 스프레드 표 기준일(발표일) %s > 평가기준일 %s — 자료 날짜 표시가 없어 사실 시점 확인 불가%s"
                   % (기준, val_date, 꼬리))
    return out


def 경보낮춤(d, val_date):
    """판경보에 걸린 값(ERP · CRP · 스프레드 표)의 확인상태를 「참고」로 낮춘다 — 「확인완료」로 남으면 4단계 문항이 못 본다
    (2026-10-16, S1 리뷰: 근거 4칸의 기준일이 평가기준일 뒤인 값이 확인완료로 퍼졌다). 낮춘 이름 목록을 낸다."""
    낮춘 = []
    for 줄 in 판경보(d, val_date):
        for k in 다모다란국가칸 + ("합성등급 스프레드 표",):
            v = d.get(k)
            if 줄.startswith(k) and isinstance(v, dict) and v.get("확인상태") != "참고":
                v["확인상태"] = "참고"
                v["비고"] = ((v.get("비고") or "") + " · ⚠ 경보로 확인상태를 「참고」로 낮춤 — " + 줄).strip(" ·")
                낮춘.append(k)
    return 낮춘


# 국가 행에서 담는 칸 — 판경보 · 경보낮춤이 같은 목록을 본다(판 · 데이터 기준일이 같은 한 행이다)
다모다란국가칸 = ("시장위험프리미엄 (ERP)", "국가위험프리미엄 (CRP)", "성숙시장 위험프리미엄", "국가 부도스프레드",
             "국가 한계세율(다모다란)")


def 국가행(val_date: str, country_name: str, 정책: str = None):
    """다모다란 ctryprem 한 판의 국가 행 → {칸 이름: 근거 4칸} — 성숙시장 · 부도 스프레드 · CRP · Total · 국가 세율.

    **같은 판 같은 행에서 넷을 함께 읽는다**(S7-01). 부도 스프레드를 다른 판(예: 1월판)에서, ERP 를 7월판에서 읽으면
    짝이 어긋난다. 칸 위치는 머리줄(8행)의 이름으로 찾는다 — 위치를 박지 않는다(판마다 열이 늘 수 있다)."""
    import openpyxl
    p, fn, 판, 사유 = _ctryprem_file(val_date, 정책)
    if p is None:
        na = _four(None, "다모다란 ctryprem", val_date, "확인 불가",
                   "날짜판·현행판 모두 못 받았다. 비슷한 값으로 메우지 말고 멈춘다 · " + 사유)
        return {k: dict(na) for k in 다모다란국가칸}
    wb = openpyxl.load_workbook(p, data_only=True)
    ws = wb["ERPs by country"]
    mature = ws.cell(row=3, column=5).value
    mature글 = ws.cell(row=3, column=6).value
    배수 = ws.cell(row=6, column=5).value
    머리, hit = None, None
    for row in ws.iter_rows(values_only=True):
        if 머리 is None and row and str(row[0]).strip() == "Country":
            머리 = [str(x or "").strip() for x in row]
            continue
        if row and str(row[0]).strip() == country_name:
            hit = row
            break

    def 열(이름, 기본):
        if 머리:
            for i, h in enumerate(머리):
                if h == 이름:
                    return i
        return 기본
    i등급, i부도, iTotal, iCRP = 열("Moody's rating", 2), 열("Rating-based Default Spread", 3),         열("Total Equity Risk Premium", 4), 열("Country Risk Premium", 5)
    세율 = None
    if "Country Tax Rates" in wb.sheetnames:
        for row in wb["Country Tax Rates"].iter_rows(values_only=True):
            if row and str(row[0]).strip() == country_name and isinstance(row[1], (int, float)):
                세율 = float(row[1])
                break
    upd = 판["발표일"]
    기준 = 판["데이터기준일"] or upd
    src = "Damodaran %s 'ERPs by country' (Date of update %s · 데이터 기준일 %s)" % (fn, upd, 판["데이터기준일"] or "확인 불가")
    상태 = "확인완료" if 판["데이터기준일"] else "확인완료(데이터 기준일 확인 불가)"

    def 칸(값, 비고, 출처=src):
        x = _four(값, 출처, 기준, 상태, 비고)
        x.update({"발표일": upd, "데이터기준일": 판["데이터기준일"], "데이터기준일_근거": 판["데이터기준일_근거"]})
        if 판["경보"]:
            x["경보"] = 판["경보"]
        return x
    out = {}
    out["성숙시장 위험프리미엄"] = 칸(mature, "같은 판 상단 「%s」 — 성숙시장 ERP 는 부도 스프레드를 뺀 달러 무위험이자율 위에서 "
                                   "계산된 값이다. 그래서 짝이 되는 Rf 도 표시통화 국채 − 국가 부도스프레드다. 내재 ERP 의 셈은 시장의 끝 성장을 "
                                   "무위험이자율로 둔다 — 영구성장률은 영구기간 무위험이자율 아래로 짝을 맞춘다(갭해석설정 「영구짝」) · %s"
                                   % (mature글 or "설명 없음", 사유))
    if hit is None:
        for k in ("시장위험프리미엄 (ERP)", "국가위험프리미엄 (CRP)", "국가 부도스프레드"):
            na = 칸(None, "%s 행을 못 찾았다 — `--국가이름` 으로 다모다란 표기를 준다 · %s" % (country_name, 사유))
            na["확인상태"] = "확인 불가"
            out[k] = na
    else:
        총 = hit[iTotal]
        out["시장위험프리미엄 (ERP)"] = 칸(총, "국가 행 Total ERP = 성숙시장 %.4f + CRP %.4f. **이 값을 MRP 로 곱하면 Rf 는 반드시 "
                                         "국채 − 부도스프레드여야 한다**(국채를 그대로 쓰면 국가위험을 두 번 센다 — 시장위험프리미엄 입력 규칙). "
                                         "가정에는 성숙 · 국가 두 줄로 적는다(결정 154). ERPbymonth 는 2018-05 에서 갱신이 멈춘 "
                                         "죽은 파일이라 쓰지 않는다 · %s" % (mature or 0, (hit[iCRP] or 0), 사유))
        out["국가위험프리미엄 (CRP)"] = 칸(hit[iCRP], "국가 행 CRP = 부도 스프레드 %.4f × 주식/채권 변동성 배수 %s. "
                                          "MRP 의 둘째 줄(성숙시장 + 국가)이다 — 자기자본비용 식에 β 밖으로 따로 더하지 않는다 · %s"
                                          % ((hit[i부도] or 0), ("%.4f" % 배수) if isinstance(배수, (int, float)) else 배수, 사유))
        out["국가 부도스프레드"] = 칸(hit[i부도], "국가 행 Rating-based Default Spread(%s 등급 %s). 표시통화 국채 수익률에서 빼서 "
                                       "무위험이자율을 낸다(Aaa 나라는 0). 같은 판 같은 행이라 CRP 와 짝이 맞는다 · %s"
                                       % (country_name, hit[i등급], 사유))
    out["국가 한계세율(다모다란)"] = 칸(세율, "같은 판 「Country Tax Rates」 %s 행 — 유사기업을 소재국 세율로 벗길 때의 "
                                         "대용값이다. 국내 회사는 법령 세율표(한계세율.py)가 먼저다" % country_name)
    if 세율 is None:
        out["국가 한계세율(다모다란)"]["확인상태"] = "확인 불가"
    return out


def ctryprem(val_date: str, country_name: str, 정책: str = None):
    """옛 꼴 — (Total ERP, CRP) 두 칸. 새 코드는 `국가행` 을 쓴다."""
    행 = 국가행(val_date, country_name, 정책)
    return 행["시장위험프리미엄 (ERP)"], 행["국가위험프리미엄 (CRP)"]


def 차감무위험(국채, 부도):
    """국채 수익률 − 국가 부도 스프레드 → 근거 4칸(둘 중 하나라도 없으면 확인 불가)."""
    g, s = (국채 or {}).get("값"), (부도 or {}).get("값")
    if g is None or s is None:
        return _four(None, "국채 수익률 − 국가 부도스프레드", (국채 or {}).get("기준일"), "확인 불가",
                     "국채 수익률 또는 부도 스프레드가 없다 — 차감할 수 없다")
    상태 = "참고" if "참고" in ("%s %s" % ((국채 or {}).get("확인상태"), (부도 or {}).get("확인상태"))) else "확인완료"
    return _four(g - s, "%s − %s" % ((국채 or {}).get("출처"), "다모다란 국가 부도스프레드"), (국채 or {}).get("기준일"), 상태,
                 "Rf = 국채 %.4f − 부도 %.4f. 엔진에는 `구조.할인.무위험이자율 = 부도스프레드차감` 으로 두 값을 따로 넣는다 — "
                 "이 칸은 화면 확인용이다" % (g, s))


# ── 다모다란 ratings.xls: 합성등급 스프레드 전 등급 ───────────────────
# 표 머리말 → 이름. **머리말이 「For 」로 시작하는 줄은 전부 표 경계다(세5).**
# 옛 판은 대형·중소형 두 머리말만 알아서, 그 아래 「For infrastructure companies/Utilities」 표
# 15줄이 「중소형·고위험」에 이어 붙어 **30줄**이 됐다(실측 2026-01 판). 같은 등급이 두 번
# 나오고 구간이 겹쳐 합성등급 조회가 첫 줄/둘째 줄 어느 쪽을 집느냐로 갈린다.
# 모르는 머리말은 표로 싣지 않고 이름만 적는다 — 조용히 옆 표에 붙이지 않는다.
_등급표머리 = (("for large non-fin", "대형 비금융"), ("for smaller", "중소형·고위험"),
             ("for financial service", "금융회사"), ("for infrastructure", "인프라·유틸리티"),
             ("for utilities", "인프라·유틸리티"))


def _등급표이름(글):
    s = str(글).strip().lower()
    if not s.startswith("for "):
        return None, False
    for 앞, 이름 in _등급표머리:
        if s.startswith(앞):
            return 이름, True
    return None, True                          # 경계는 맞는데 모르는 표


def 등급표파싱(행들):
    """시트 행 목록(각 행은 칸 값 목록) → ({표이름: [구간]}, 모르는 머리말 목록).

    한 행에 표가 둘 나란히 놓인다(0~3열 대형 비금융 · 5~8열 금융회사). 칸 묶음마다 따로
    머리말을 추적한다."""
    tables, 모름 = {}, []
    cur = {0: None, 5: None}
    for row in 행들:
        row = list(row) + [""] * (9 - len(row))
        for 시작 in (0, 5):
            이름, 경계 = _등급표이름(row[시작])
            if 경계:
                cur[시작] = 이름
                if 이름 is None:
                    모름.append(str(row[시작]).strip()[:60])
                continue
            try:
                lo = float(row[시작]); hi = float(row[시작 + 1])
                rating = str(row[시작 + 2]).strip()
                sp = float(row[시작 + 3])
            except (ValueError, TypeError):
                continue
            if cur[시작] and rating:
                tables.setdefault(cur[시작], []).append(
                    {"이자보상배율_초과": lo, "이하": hi, "등급": rating, "스프레드": sp})
    return tables, 모름


def _발표일(p):
    """ratings.xls 의 **발표일** — 받을 때 적은 HTTP Last-Modified → 문서 속성 마지막 저장일.
    (날짜, 근거). 둘 다 없으면 (None, 사유). **조회일로 메우지 않는다(세5).**"""
    meta = p + ".meta.json"
    if os.path.exists(meta):
        try:
            m = json.load(io.open(meta, encoding="utf-8"))
            lm = m.get("Last-Modified")
            if lm:
                from email.utils import parsedate_to_datetime
                return parsedate_to_datetime(lm).date().isoformat(), "HTTP Last-Modified(%s)" % lm
        except (ValueError, OSError, TypeError):
            pass
    try:
        import olefile
        with olefile.OleFileIO(p) as o:
            t = o.get_metadata().last_saved_time
        if t:
            return t.date().isoformat(), "문서 속성 마지막 저장일(OLE SummaryInformation)"
    except Exception:                                      # noqa: BLE001
        pass
    return None, "발표일 확인 불가 — Last-Modified 기록도 문서 속성도 없다"


def spreads(val_date: str):
    fn = "ratings.xls"
    p = os.path.join(RAW, fn)
    if not os.path.exists(p):
        주소, 까닭 = 다모다란주소(fn)
        if not 주소:
            return _four(None, "Damodaran ratings.xls", val_date, "확인 불가", 까닭)
        try:
            os.makedirs(RAW, exist_ok=True)
            r = _get(주소, timeout=180)
            r.raise_for_status()
            open(p, "wb").write(r.content)
            json.dump({"URL": 주소, "Last-Modified": r.headers.get("Last-Modified"),
                       "받은날": TODAY}, io.open(p + ".meta.json", "w", encoding="utf-8"),
                      ensure_ascii=False)
        except requests.RequestException as e:
            return _four(None, "Damodaran ratings.xls", val_date, "확인 불가",
                         "다운로드 실패: %s" % type(e).__name__)
    try:
        import xlrd
        sh = xlrd.open_workbook(p).sheet_by_index(0)
        tables, 모름 = 등급표파싱([[sh.cell_value(r, c) for c in range(min(sh.ncols, 9))]
                               for r in range(sh.nrows)])
        if not tables:
            raise ValueError("표를 못 찾았다")
        발표, 근거 = _발표일(p)
        비고 = ("이자보상배율 구간 → 등급 → 스프레드. 무차입(분모 0)은 최상위 구간. "
               "Kd = Rf + 스프레드 로 쓴다 · 표 %s · 기준일은 파일 발표일(%s)"
               % (" · ".join("%s %d줄" % (k, len(v)) for k, v in tables.items()), 근거))
        if 모름:
            비고 += " · 모르는 표 머리말은 싣지 않음: %s" % " / ".join(모름)
        if 발표 and 발표 > val_date:
            # 데이터 기준일 규칙: 발표일이 뒤라도 기준일 이전 사실이면 쓴다 — 그런데 ratings.xls 에는
            # 스프레드의 자료 날짜 표시가 없어 사실 시점을 확인할 수 없다 → 확인 불가 + 경보
            # (날짜판이 없어 「이전 판」으로 물러설 수도 없다)
            비고 += (" · ⚠ 경보 — 발표일 %s 이 평가기준일 %s 뒤이고 파일에 스프레드 자료 날짜 표시가 없다"
                   "(데이터 기준일 확인 불가). ratings.xls 는 날짜판이 없어 이전 판으로 물러설 수 없다" % (발표, val_date))
        return {"값": tables, "출처": "Damodaran ratings.xls (합성등급 스프레드)",
                "기준일": 발표 or "확인 불가", "조회일": TODAY,
                "확인상태": "확인완료" if 발표 else "확인완료(발표일 확인 불가)", "비고": 비고}
    except Exception as e:                                 # noqa: BLE001
        return _four(None, "Damodaran ratings.xls", val_date, "확인 불가",
                     "파일은 _raw/ratings.xls 에 저장됨. 파싱 실패(%s) — 파일을 직접 읽는다"
                     % type(e).__name__)


# ── 한국: 금융투자협회 한 표 — 국고채 + 회사채 전 등급 ─────────────────
def kr_table(val_date: str):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import kofia_bond_yield as kf
    key = val_date.replace("-", "")
    rows = kf.fetch_rows(key)
    shown = val_date
    if not rows:
        key, rows = kf.last_business_day(dt.datetime.strptime(val_date, "%Y-%m-%d").date())
        shown = dt.datetime.strptime(key, "%Y%m%d").strftime("%Y-%m-%d")
    terms = kf.fetch_terms(key)
    col = next((c for c, t in terms.items() if t == "10년"), None)
    src = "금융투자협회 채권정보센터 시가평가수익률, 평가사 평균 5개사"
    status = "확인완료" if shown == val_date else "확인완료(직전영업일)"
    note = "" if shown == val_date else "평가기준일이 휴장일이라 직전 영업일 %s 사용" % shown
    out = {}
    g = next((r for r in rows if r["종류"] == "국채" and r["종류명"] == "국고채권"), None)
    out["무위험이자율 (국고채 10년)"] = _four(
        float(g[col]) / 100 if g and g[col] else None, src, shown,
        status if g and g[col] else "확인 불가", note)
    grades = {}
    for r in rows:
        if r["종류"] == "회사채 I(공모사채)" and r["종류명"] == "무보증" \
                and r["신용등급"] and r[col]:
            grades[r["신용등급"]] = float(r[col]) / 100
    out["회사채 전 등급 (무보증 공모, 10년)"] = {
        "값": grades, "출처": src, "기준일": shown, "조회일": TODAY,
        "확인상태": status if grades else "확인 불가",
        "비고": (note + " · " if note else "") +
                "국고채와 같은 표·같은 조회일이라 스프레드의 짝이 맞는다. "
                "BBB- 아래는 공시되지 않는다 — 그 아래 등급은 국고채 + 다모다란 스프레드로 대용"}
    return out


# ══ 거시지표 — CPI·평균임금 등 ═════════════════════════════════════════
# 회사 재무수치가 아니라 국가 단위 거시지표다. 그래서 공시 밖 출처를 쓴다.
# 다만 확인상태를 한 단계 낮춰 적고, 어디서 왔는지를 값과 함께 들고 다닌다.
네트워크 = True


def _get(url, **kw):
    if not 네트워크:
        raise requests.RequestException("오프라인 지정")
    return requests.get(url, headers=H, timeout=kw.pop("timeout", 60), **kw)


def _worldbank(iso3, ind):
    """세계은행 공개 API — 열쇠도 회원가입도 없다. 연간 값 하나와 그 해를 준다."""
    u = ("https://api.worldbank.org/v2/country/%s/indicator/%s"
         "?format=json&mrnev=1" % (iso3, ind))
    r = _get(u)
    r.raise_for_status()
    d = r.json()
    if not isinstance(d, list) or len(d) < 2 or not d[1]:
        raise ValueError("빈 응답")
    row = d[1][0]
    if row.get("value") is None:
        raise ValueError("값이 비었다")
    return float(row["value"]), str(row["date"]), u


def _bls(series, y0, y1):
    if not 네트워크:
        raise requests.RequestException("오프라인 지정")
    r = requests.post("https://api.bls.gov/publicAPI/v1/timeseries/data/",
                      json={"seriesid": [series], "startyear": str(y0),
                            "endyear": str(y1)},
                      headers={"Content-Type": "application/json"}, timeout=90)
    r.raise_for_status()
    d = r.json()
    if d.get("status") != "REQUEST_SUCCEEDED":
        raise ValueError(str(d.get("status")))
    return d["Results"]["series"][0]["data"]


def _bls_yoy(series, val_date):
    """평가기준일 이하 최신 월과 12개월 전 같은 달을 견줘 전년동월비를 낸다.
    구간을 코드가 계산하므로 사람이 눈으로 옮겨 적는 자리가 없다."""
    y = int(val_date[:4])
    rows = _bls(series, y - 2, y)
    val = {}
    for x in rows:
        if not x["period"].startswith("M") or x["period"] == "M13":
            continue
        try:                       # BLS 는 미발표 월을 "-" 로 준다. 건너뛴다
            val["%s-%s" % (x["year"], x["period"][1:])] = float(x["value"])
        except (ValueError, TypeError):
            continue
    후보 = sorted(k for k in val if k <= val_date[:7])
    if not 후보:
        raise ValueError("평가기준일 이하 월이 없다")
    이번 = 후보[-1]
    작년 = "%d-%s" % (int(이번[:4]) - 1, 이번[5:])
    if 작년 not in val:
        raise ValueError("12개월 전 값이 없다")
    return val[이번] / val[작년] - 1.0, 이번, 작년


# 열쇠 없는 API가 없는 자리는 웹 검색 결과를 여기에 적어 둔다.
# **손으로 적는 표다.** 그래서 확인상태를 「참고(웹 검색)」로 낮추고
# 출처 주소와 적은 날을 함께 남긴다. 표에 없는 국가·항목은 「확인 불가」로 떨어진다.
웹검색_거시 = {
    ("KR", "평균임금 상승률"): {
        "값": 0.034,
        "출처": "고용노동부 사업체노동력조사 2026년 1분기 상용근로자 월평균 명목임금"
                " 455.5만원, 전년동기대비 +3.4%. 곁 확인 — 2026년 6월 단월 +3.1% ·"
                " 2025년 상반기 누계 +3.5%(418.8만원). **단월이 아니라 누계를 쓴다** —"
                " 설 상여 시기가 해마다 달라 단월은 크게 흔들린다(2026년 1월 −7.6%)."
                " (웹 검색으로 확인. korea.kr 정책브리핑 사업체노동력조사 결과 발표 ·"
                " koreabizreview.com 2026-06-22 기사)",
        "기준일": "2026-03-31",
        "적은날": "2026-09-03",
    },
}


def _웹검색값(country, 이름, val_date):
    rec = 웹검색_거시.get((country, 이름))
    if not rec:
        return _four(None, "확인된 출처 없음", val_date, "확인 불가",
                     "열쇠 없는 공개 API가 없고 웹 검색 기록도 없다. 지어내지 않는다")
    # 적어 둔 값의 기준일이 평가기준일에서 멀면 쓰지 않는다.
    # 오래된 기록을 조용히 재활용하면 「구글링해서 나온 값」이 언제 것인지가 사라진다.
    if abs((dt.date.fromisoformat(rec["기준일"])
            - dt.date.fromisoformat(val_date)).days) > 730:
        return _four(None, rec["출처"], rec["기준일"], "확인 불가",
                     "적어 둔 웹 검색 기록의 기준일(%s)이 평가기준일(%s)에서 2년 넘게 떨어져 "
                     "있다. 그대로 쓰지 않는다 — 그 시점 값을 새로 찾아 표에 적는다"
                     % (rec["기준일"], val_date))
    return _four(rec["값"], rec["출처"], rec["기준일"], "참고(웹 검색)",
                 "웹 검색으로 얻은 거시지표다. EIU 같은 유료 자료가 없는 상황에서 할 수 있는 "
                 "최선이고 검증은 잘 되지 않는다 — 회사 재무수치가 아니므로 공시 밖 출처를 "
                 "쓰지만 확인상태를 낮춰 적는다. 표에 적은 날 %s. "
                 "**추정기간 내내 이 값이 유지된다고 가정한다**" % rec["적은날"])


def _API값(부름, 이름, val_date, 낮춤="참고(공개 통계 API)"):
    """부름()이 (값, 출처, 기준일, 비고) 를 내면 근거 4칸으로 감싼다."""
    try:
        v, src, base, note = 부름()
    except Exception as e:                                     # noqa: BLE001
        return _four(None, 이름, val_date, "확인 불가",
                     "받지 못했다(%s). 비슷한 값으로 메우지 않는다" % type(e).__name__)
    return _four(v, src, base, 낮춤,
                 note + " · 회사 재무수치가 아니라 국가 단위 거시지표라 공시 밖 출처를 쓴다. "
                        "**추정기간 내내 이 값이 유지된다고 가정한다**")


_ISO3 = {"KR": "KOR", "US": "USA", "JP": "JPN", "TW": None, "CN": "CHN", "HK": "HKG", "SG": "SGP", "IN": "IND", "VN": "VNM",
         "ID": "IDN", "TH": "THA", "MY": "MYS", "PH": "PHL", "AU": "AUS", "NZ": "NZL", "CA": "CAN", "MX": "MEX", "BR": "BRA",
         "GB": "GBR", "DE": "DEU", "FR": "FRA", "NL": "NLD", "CH": "CHE", "IT": "ITA", "ES": "ESP", "SE": "SWE", "DK": "DNK",
         "NO": "NOR", "FI": "FIN", "IE": "IRL", "BE": "BEL", "AT": "AUT", "IL": "ISR", "SA": "SAU", "AE": "ARE", "ZA": "ZAF",
         "TR": "TUR", "PL": "POL"}     # 대만은 세계은행 표에 없다(None)


def 거시지표(country, val_date, 물가=None):
    """국가 단위 거시지표 한 묶음. 값마다 근거 4칸 + 낮춘 확인상태를 붙인다.
    물가 = (값, 출처, 기준일) — KR · US 밖 나라에서 사람이 그 나라 통계청 공표 물가를 출처와 함께 줄 때(세계은행 표에 없는 나라 — 대만 등 · 2026-10-24)."""
    out = {}
    유지 = "저자 가정에 따라 연도별로 가르지 않고 단일 값으로 낸다"

    def _wb(iso3, ind, 라벨):
        def f():
            v, yr, u = _worldbank(iso3, ind)
            return (v / 100.0, "세계은행 공개 API %s (%s) — %s" % (ind, 라벨, u),
                    "%s-12-31" % yr, "%s 연간 값. %s" % (yr, 유지))
        return f

    def _b(series, 라벨):
        def f():
            v, 이번, 작년 = _bls_yoy(series, val_date)
            return (v, "미국 노동통계국 공개 API 시계열 %s (%s)" % (series, 라벨),
                    이번 + "-01", "%s 대비 %s 전년동월비. %s" % (작년, 이번, 유지))
        return f

    if country == "KR":
        out["소비자물가 상승률 (CPI)"] = _API값(
            _wb("KOR", "FP.CPI.TOTL.ZG", "한국 소비자물가 연간 상승률"),
            "세계은행 CPI", val_date)
        out["평균임금 상승률"] = _웹검색값("KR", "평균임금 상승률", val_date)
        out["생산자물가 상승률"] = _four(
            None, "열쇠 없는 공개 API 없음", val_date, "확인 불가",
            "한국은행 ECOS·KOSIS 는 인증키가 필요해 받지 않았다(회원가입 필요 자료는 쓰지 않는다). "
            "지수 1(원재료류)은 사람이 채운다")
        out["전기요금 상승률"] = _four(
            None, "열쇠 없는 공개 API 없음", val_date, "확인 불가",
            "한전 요금표는 기계로 읽을 자리가 없다. 지수 2(요금류)는 사람이 채운다")
    elif country != "US":
        # KR · US 밖(S7-12) — 세계은행 CPI 만 열쇠 없이 받는다. 나머지는 사람이 채운다(미국 계열을 대신 쓰지 않는다)
        iso3 = _ISO3.get(country)
        if 물가 and 물가[0] is not None:
            out["소비자물가 상승률 (CPI)"] = _four(물가[0], 물가[1], 물가[2] or val_date, "확인완료(사람 입력 — 공표 통계)",
                                             "그 나라 통계청 공표 소비자물가 상승률을 사람이 출처와 함께 준 값이다(이 도구가 받지 않았다). "
                                             "**추정기간 내내 이 값이 유지된다고 가정한다**")
        else:
            out["소비자물가 상승률 (CPI)"] = (_API값(_wb(iso3, "FP.CPI.TOTL.ZG", "%s 소비자물가 연간 상승률" % country),
                                             "세계은행 CPI", val_date) if iso3 else
                                        _four(None, "세계은행 CPI", val_date, "확인 불가",
                                              "세계은행 표에 없는 나라(%s) — `--물가 값 --물가출처 …` 로 그 나라 통계청 공표 값을 준다" % country))
        for 이름 in ("평균임금 상승률", "생산자물가 상승률", "전기요금 상승률"):
            out[이름] = _four(None, "열쇠 없는 공개 API 없음", val_date, "확인 불가",
                            "KR · US 밖 나라의 이 지표는 이 도구가 받지 않는다 — 사람이 그 나라 통계청 공표 값을 채운다")
    else:
        out["소비자물가 상승률 (CPI)"] = _API값(
            _b("CUUR0000SA0", "CPI-U 전 품목"), "미 노동통계국 CPI", val_date)
        if out["소비자물가 상승률 (CPI)"]["값"] is None:
            out["소비자물가 상승률 (CPI)"] = _API값(
                _wb("USA", "FP.CPI.TOTL.ZG", "미국 소비자물가 연간 상승률"),
                "세계은행 CPI", val_date)
        out["평균임금 상승률"] = _API값(
            _b("CES0500000003", "민간 전체 시간당 평균임금"),
            "미 노동통계국 평균임금", val_date)
        out["생산자물가 상승률"] = _API값(
            _b("WPUFD4", "최종수요 생산자물가"), "미 노동통계국 PPI", val_date)
        out["전기요금 상승률"] = _API값(
            _b("CUUR0000SEHF01", "CPI-U 전기"), "미 노동통계국 전기 CPI", val_date)
    return out


# ══ 12번 시트 행 제안값 ═════════════════════════════════════════════════
# 값을 강제로 덮지 않는다 — 사람이 정하는 자리다. 가정 JSON 에 붙일 수 있는
# 모양으로 내주기만 한다.
# 종류가 갈린다. **비율 행에는 상승률을 그대로 넣고, 수준 행에는 넣지 않는다.**
#   비율 행 — 12번 단위 칸이 `%` 다(98·102·106 변동률). 엔진이 (1+값) 으로 지수를 쌓는다
#   수준 행 — 단위 칸이 금액·명·일이다(130 인당 평균인건비). 엔진은 이 값을 **곱한다**:
#             p13(총인건비) = 평균인원 × A[130]. 여기에 0.034 를 넣으면
#             「인당 인건비 34,000원」 이 되어 인건비가 통째로 사라진다
# 수준 행의 기저는 국가 거시가 아니라 **그 회사 실적**(총인건비÷인원)에서 온다.
# 캐시가 지어낼 수 없으므로 상승률만 건네고 기저는 사람이 넣는다.
# ⚠ 행 번호는 **v13 가정 번호**다(2026-10-16 — v12 의 130 「인당 평균인건비(수준)」은 v13 인건비 갈래에서 걷혔다.
# 평균임금 상승률은 504 「임금상승률」(비율 — 인원 갈래), 기준 수준은 503 「1인당 평균급여」(한 값 — 회사 실적)다).
# v10 판(74·78·82·106)이 오래 남아 있었는데 106 은 「일반물가(비율)」라 — 옛 배선을 병합하면
# 평균임금 상승률이 물가 행에 앉는 조용한 사고가 난다. 판올림 때 이 표부터 본다.
행배선 = [
    ("106", "일반물가 변동률", "소비자물가 상승률 (CPI)", None, "비율"),
    ("98", "지수 1 (원재료류)", "생산자물가 상승률", "소비자물가 상승률 (CPI)", "비율"),
    ("102", "지수 2 (요금류)", "전기요금 상승률", "소비자물가 상승률 (CPI)", "비율"),
    ("504", "임금상승률", "평균임금 상승률", None, "비율"),
]


영구비우는행 = ("504",)      # S4-04 — 영구 열 1인당 상승률 = g − 영구 열 인원 증가율(= g). 거시값을 영구 열에 넣지 않는다 — 회차가 212 를 보고 넣는다


def 열배열(값, 예측열수, 영구=True):
    """15칸 배열로 편다. 실적 3칸은 null, 예측 열과 영구 열에 같은 값을 넣는다(영구=False 면 영구 열은 비운다).
    추정기간 내내 같은 값이 유지된다는 저자 가정이 이 모양으로 드러난다."""
    a = [None] * 15
    for i in range(3, min(3 + int(예측열수), 14)):
        a[i] = 값
    a[14] = 값 if 영구 else None
    return a


def 수준행배열(기저, 상승률, 예측열수, 길이=None, 마지막실적길이=None):
    """수준 행(금액·명·일)을 상승률로 편다 — 기저 × (1+g)^t.

    기저는 **그 회사 실적에서 온다**(인당 인건비면 총인건비÷평균인원, 연환산). 국가 거시가
    아니므로 캐시가 지어내지 않는다. 기저 없이 부르면 None 을 낸다 — 비워서 낸다.

    **`t` 는 열 번호가 아니라 흐른 햇수다.** `길이` 를 주면 각 예측 열의 **기간 중점**까지
    실제로 흐른 연수로 복리한다:

        t_i = 마지막실적길이/2 + Σ(앞 예측 열 길이) + 길이_i/2

    안 주면 옛 꼴대로 열마다 한 해씩 센다 — **반기 열이 섞인 회차에서는 반년 만에 한 해치가
    올라 임금이 앞당겨 오른다.** 실측(CJ프레시웨이): 첫 예측 열이 반기(2H2026)라
    2026년 하반기에 이미 연 3.4% 인상이 통째로 실렸다. 반기 열을 쓰는 회차에서는 `길이` 를
    반드시 건넨다(엔진 `기간계산()` 의 `길이`, `마지막실적길이` 는 그 배열의 2번 칸).
    """
    if 기저 is None or 상승률 is None:
        return None
    a = [None] * 15
    g = 1.0 + float(상승률)
    끝 = min(3 + int(예측열수), 14)
    if 길이:
        앞 = (float(마지막실적길이) / 2.0) if 마지막실적길이 else 0.0
        누 = 0.0
        t = 0.0
        for i in range(3, 끝):
            L = float(길이[i]) if (i < len(길이) and 길이[i]) else 1.0
            t = 앞 + 누 + L / 2.0
            a[i] = float(기저) * g ** t
            누 += L
        # 영구 열은 마지막 예측 열에서 한 해 더 간 자리에 둔다(영구는 길이가 1년 기준이다)
        a[14] = float(기저) * g ** (앞 + 누 + 0.5)
        return a
    n = 0
    for i in range(3, 끝):
        n += 1
        a[i] = float(기저) * g ** n
    a[14] = float(기저) * g ** (n + 1)
    return a


def 가정행제안(country, val_date, 예측열수=4, 거시=None):
    """캐시(작업폴더→공용→네트워크)의 거시지표를 12번 시트 행 제안값으로 바꾼다.
    뒷단계가 `import market_data` 로 그대로 끌어다 쓰는 자리다."""
    if 거시 is None:
        d, 어디 = 캐시읽기(country, val_date)
        if d is None:
            raise IOError("시장데이터 캐시가 없다. market_data.py 를 먼저 돌린다")
        거시 = d.get("거시지표") or {}
    제안 = {}
    for 행, 행이름, 순위1, 순위2, 종류 in 행배선:
        원 = 거시.get(순위1) or {}
        쓴것 = 순위1
        if 원.get("값") is None and 순위2:
            원 = 거시.get(순위2) or {}
            쓴것 = 순위2
        if 원.get("값") is None:
            제안[행] = {"행이름": 행이름, "종류": 종류, "값": None, "확인상태": "확인 불가",
                       "비고": "쓸 거시지표가 없다. 사람이 채운다"}
            continue
        대용 = "" if 쓴것 == 순위1 else " (1순위 %s 를 못 받아 %s 로 대신했다)" % (순위1, 쓴것)
        칸 = {
            "행이름": 행이름,
            "종류": 종류,
            "확인상태": 원["확인상태"],
            "근거4칸": [원["출처"], 원["기준일"], 원["확인상태"], 원.get("비고", "")],
        }
        if 종류 == "비율":
            칸["값"] = 원["값"]
            칸["배열"] = 열배열(원["값"], 예측열수, 영구=행 not in 영구비우는행)
            칸["비고"] = ("거시지표 「%s」 에서 왔다%s. 제안값일 뿐 강제로 덮지 않는다 — "
                         "사람이 보고 정한다" % (쓴것, 대용)) + (
                " · **영구 열은 비웠다** — 영구 열 1인당 상승률은 g − 영구 열 인원 증가율(엔진은 인원을 평평하게 두므로 g · S4-04). "
                "회차가 212(영구성장률)를 넣는다. 비워 두면 0 으로 읽혀 자체검사 ㉔ ②-4 가 경보한다" if 행 in 영구비우는행 else "")
        else:
            # 수준 행 — 상승률을 그대로 넣으면 안 된다. 기저가 있어야 배열이 선다.
            칸["값"] = None
            칸["배열"] = None
            칸["상승률"] = 원["값"]
            칸["비고"] = (
                "**이 값은 상승률이다. %s행에 그대로 넣지 마라** — 이 행은 수준(금액·명·일)이고 "
                "엔진이 곱하는 자리다(총인건비 = 평균인원 × 이 행). 상승률을 그대로 넣으면 "
                "인건비가 통째로 사라진다. 기저(그 회사 실적: 총인건비÷평균인원)를 구해 "
                "`수준행배열(기저, 상승률, 예측열수)` 로 편다. 기저는 국가 거시가 아니라 "
                "회사 실적이라 캐시가 지어내지 않는다. 거시지표 「%s」 에서 왔다%s"
                % (행, 쓴것, 대용))
        제안[행] = 칸
    제안["_사용법"] = (
        "**`종류` 를 먼저 본다.** `비율` 이면 `배열` 을 그대로 넣는다. "
        "`수준` 이면 `배열` 이 None 이다 — `상승률` 만 왔으니 그 회사 실적에서 기저를 구해 "
        "`수준행배열(기저, 상승률, 예측열수)` 로 편 뒤 넣는다. "
        "가정 JSON(v13)의 `가정.{행}.{비관|기준|낙관}` 은 `{기간 ID: 값}` 꼴이다 — `배열` 의 예측 칸을 그 회차의 예측 열 ID 에 펴서 넣는다. "
        "세 시나리오를 가르려면 사람이 폭을 정한다 — 캐시는 한 값만 낸다. "
        "`근거4칸` 은 `근거.{행}` 에 그대로 들어간다. "
        "**정식 배선(스키마에 키를 넣는 일)은 이 갈래가 하지 않는다 — 보고서의 제안 문안을 본다.**")
    return 제안


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--date", "--평가기준일", dest="date", default=None,
                    help="평가기준일 T YYYY-MM-DD(분석일) — 시장 자료 · 캐시 이름이 이 날에 선다(재무기준일이 아니다)")
    ap.add_argument("--가정", default=None, help="가정 파일 — --date 를 비우면 기준일.py 로 평가기준일 T 를 푼다")
    ap.add_argument("--country", default="US",
                    help="표시통화 국가 — ISO 두 글자(US · KR · JP · TW · IN …) 또는 다모다란 국가 이름(S7-12)")
    ap.add_argument("--국가이름", default=None, help="다모다란 ctryprem 의 국가 표기를 직접 준다(ISO 표에 없는 나라)")
    ap.add_argument("--국채수익률", type=float, default=None,
                    help="KR · US 밖의 나라 — 그 나라 재무부 · 중앙은행 공표 10년 국채 수익률(소수). 출처를 --국채출처 로 함께 준다")
    ap.add_argument("--국채출처", default=None, help="--국채수익률 의 출처(공표 기관 · 자료 이름)")
    ap.add_argument("--국채기준일", default=None, help="--국채수익률 의 날짜(기본 평가기준일)")
    ap.add_argument("--물가", type=float, default=None,
                    help="KR · US 밖의 나라 — 그 나라 통계청 공표 소비자물가 상승률(소수). 세계은행 표에 없는 나라(대만 등)에 쓴다. --물가출처 와 함께")
    ap.add_argument("--물가출처", default=None, help="--물가 의 출처(공표 기관 · 자료 이름 · 주소)")
    ap.add_argument("--물가기준일", default=None, help="--물가 의 기준일(예: 2025-12-31 — 연간 값이면 그 해 말)")
    ap.add_argument("--기대물가", default=None,
                    help="다모다란 대체식 「현지,미국」 기대물가(소수 둘) — 미 국채 × (1+현지) ÷ (1+미국) − 1. 확인상태 참고")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--오프라인", action="store_true",
                    help="네트워크를 아예 타지 않는다. 캐시가 없으면 전부 「확인 불가」")
    ap.add_argument("--가정제안", default=None,
                    help="12번 시트 74·78·82·106행 제안값을 이 경로에 JSON으로 낸다")
    ap.add_argument("--예측열수", type=int, default=4)
    ap.add_argument("--ERP판", default="데이터기준일", choices=["데이터기준일", "발표일", "가까운"],
                    help="다모다란 ctryprem 판 선택 — 데이터기준일(기본): 판 안 자료 날짜 ≤ 평가기준일 인 가장 늦은 판 / "
                         "발표일: Date of update ≤ 평가기준일 판만 / 가까운: 옛 동작(뒤 판이면 경보)")
    a = ap.parse_args()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import 기준일인자 as _기인                                  # noqa: PLC0415 — 날짜 둘(2026-10-25): 시장 쪽은 T
    a.date = _기인.풀기(a.date, a.가정, _기인.평가, 인자="--date")
    if not a.date:
        ap.error("--date(평가기준일) 또는 --가정 이 있어야 합니다")
    a.country = (a.country or "US").strip()
    if len(a.country) == 2:
        a.country = a.country.upper()
    elif not a.국가이름:                              # 다모다란 이름을 바로 준 경우 — ISO 를 거꾸로 찾는다
        거꾸로 = {v.lower(): k for k, v in 국가이름.items()}
        a.국가이름 = a.country
        a.country = 거꾸로.get(a.country.lower(), a.country.replace(" ", "_"))

    global 네트워크, ERP판정책
    네트워크 = not a.오프라인
    ERP판정책 = a.ERP판

    cache = os.path.join(RAW, "시장데이터_%s_%s.json" % (a.country, a.date))
    if not a.refresh:
        d, 어디 = 캐시읽기(a.country, a.date)
        if d is not None:
            print("캐시 사용(%s): %s  (다시 받으려면 --refresh)"
                  % ("작업폴더" if 어디 == "작업폴더" else "공용 캐시", 어디
                     if 어디 != "작업폴더" else cache))
            if 어디 != "작업폴더":
                print("  ↳ 공용 캐시에서 가져왔다. 각 값의 비고 칸에도 그 사실을 적었다.")
            for 줄 in 판경보(d, a.date):
                print("  ⚠ 경보 — %s. 다시 받으려면 --refresh (기본 정책 「데이터기준일」)" % 줄)
            if "국가 부도스프레드" not in d:
                # 옛 꼴 캐시(S7-01 전) — 국가 행 넷이 없다. 받아 둔 판 파일이 있으면 그 판에서 채운다(네트워크 없이도)
                try:
                    행 = 국가행(a.date, a.국가이름 or 국가이름.get(a.country) or a.country)
                    if 행["국가 부도스프레드"].get("값") is not None:
                        for k, v in 행.items():
                            d.setdefault(k, v)
                        d["무위험이자율 (부도스프레드 차감)"] = 차감무위험(d.get(국채칸이름(a.country)), d.get("국가 부도스프레드"))
                        print("  ↳ 옛 꼴 캐시라 국가 행 넷(부도 스프레드 · 성숙 · CRP · 세율)을 판 파일에서 채웠다")
                        try:                     # 작업 폴더 캐시에 남긴다 — 뒤 도구(합성등급 · 자체검사)가 같은 칸을 읽는다
                            os.makedirs(RAW, exist_ok=True)
                            json.dump(d, io.open(cache, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                        except (OSError, IOError, TypeError, ValueError):
                            pass
                    else:
                        print("  ⚠ 옛 꼴 캐시 — 국가 부도스프레드 · 성숙시장 칸이 없다. --refresh 로 다시 받는다")
                except Exception as e:                       # noqa: BLE001
                    print("  ⚠ 옛 꼴 캐시 — 국가 행을 못 채웠다(%s). --refresh 로 다시 받는다" % type(e).__name__)
            낮춘 = 경보낮춤(d, a.date)
            if 낮춘:
                print("  ↳ 경보 붙은 값의 확인상태를 「참고」로 낮췄다: %s" % " · ".join(낮춘))
            _화면(d)
            if a.가정제안:
                _제안쓰기(a, d)
            return

    os.makedirs(RAW, exist_ok=True)
    out = {"국가": a.country, "평가기준일": a.date, "생성일": TODAY, "_판": 캐시판}

    def _못받음(이름, e):
        return _four(None, 이름, a.date, "확인 불가",
                     "받지 못했다(%s). 비슷한 값으로 메우지 않는다" % type(e).__name__)

    다모이름 = a.국가이름 or 국가이름.get(a.country)
    if not 다모이름:
        sys.exit("국가 %s 의 다모다란 표기를 모릅니다 — --국가이름 으로 ctryprem 「ERPs by country」 의 이름을 주십시오" % a.country)
    out["국가"], out["다모다란국가"] = a.country, 다모이름
    if a.country == "US":
        try:
            out["무위험이자율 (미 국채 10년)"] = us_rf(a.date) if 네트워크 else                 _못받음("미국 재무부", requests.RequestException("오프라인 지정"))
        except Exception as e:                                 # noqa: BLE001
            out["무위험이자율 (미 국채 10년)"] = _못받음("미국 재무부", e)
    elif a.country == "KR":
        try:
            if not 네트워크:
                raise requests.RequestException("오프라인 지정")
            out.update(kr_table(a.date))
        except Exception as e:                                 # noqa: BLE001
            out["무위험이자율 (국고채 10년)"] = _못받음("금융투자협회", e)
            out["회사채 전 등급 (무보증 공모, 10년)"] = _못받음("금융투자협회", e)
    else:
        out[국채칸이름(a.country)] = 그밖국채(a)
    out.update(국가행(a.date, 다모이름))
    out["무위험이자율 (부도스프레드 차감)"] = 차감무위험(out.get(국채칸이름(a.country)), out.get("국가 부도스프레드"))
    # 등급 스프레드 표 — 미국 Kd · 국내 BBB- 미만 · 그 밖 나라의 합성등급 재료
    out["합성등급 스프레드 표"] = spreads(a.date)

    if a.물가 is not None and not a.물가출처:
        sys.exit("--물가 에는 --물가출처 를 함께 줍니다(근거 4칸 — 공표 기관 · 자료 이름)")
    out["거시지표"] = 거시지표(a.country, a.date, (a.물가, a.물가출처, a.물가기준일) if a.물가 is not None else None)
    out["거시지표"]["_가정"] = (
        "여기 값은 추정기간 내내 그대로 유지된다고 가정한다. 연도별로 가르지 않는다. "
        "회사 재무수치가 아니라 국가 단위 거시지표라 공시 밖 출처를 쓰되 확인상태를 낮춰 적는다.")

    낮춘 = 경보낮춤(out, a.date)
    json.dump(out, io.open(cache, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    공용 = _공용에쓰기(a.country, a.date, out)
    if 낮춘:
        print("경보 붙은 값의 확인상태를 「참고」로 낮췄다: %s" % " · ".join(낮춘))
    print("저장: %s" % cache)
    print("공용: %s" % 공용)
    _화면(out)
    for 줄 in 판경보(out, a.date):
        print("  ⚠ 경보 — %s" % 줄)
    bad = [k for k, v in out.items()
           if isinstance(v, dict) and v.get("확인상태") == "확인 불가"]
    bad += ["거시지표." + k for k, v in out["거시지표"].items()
            if isinstance(v, dict) and v.get("확인상태") == "확인 불가"]
    if bad:
        print("확인 불가 %d건 — 비슷한 값으로 메우지 말고 사유를 보고한다: %s"
              % (len(bad), ", ".join(bad)))
    if a.가정제안:
        _제안쓰기(a, out)


def _화면(d):
    for k, v in d.items():
        if isinstance(v, dict) and "확인상태" in v:
            print("  %-32s %s" % (k, v.get("확인상태")))
    for k, v in (d.get("거시지표") or {}).items():
        if isinstance(v, dict) and "확인상태" in v:
            값 = v.get("값")
            print("  거시 %-27s %-18s %s"
                  % (k, ("%.4f" % 값) if isinstance(값, float) else "-",
                     v.get("확인상태")))


def _제안쓰기(a, d):
    제안 = 가정행제안(a.country, a.date, a.예측열수, (d.get("거시지표") or {}))
    제안["WACC"] = WACC제안(d, a.country)
    w = 제안["WACC"]
    print("WACC 제안(구조.할인.무위험이자율 = 부도스프레드차감): 국채 %s − 부도 %s = Rf %s · 성숙 %s + 국가 %s = MRP %s (대조 Total %s)%s" % (tuple(
        ("%.4f" % v) if isinstance(v, (int, float)) else "확인 불가"
        for v in (w["WACC.예측기간"]["국채수익률"], w["WACC.예측기간"]["부도스프레드"], w["무위험이자율_차감후"],
                  w["WACC.예측기간"]["성숙시장프리미엄"], w["WACC.예측기간"]["국가위험프리미엄"], w["시장위험프리미엄_합"],
                  w["대조_TotalERP"])) + (("" if not w["확인불가"] else " · 확인 불가: " + ", ".join(w["확인불가"])),)))
    if not os.path.dirname(a.가정제안):          # S10-20 — 파일 이름만 주면 키트 뿌리가 아니라 _raw/ 에 낸다(캐시와 같은 자리)
        os.makedirs(RAW, exist_ok=True)
        a.가정제안 = os.path.join(RAW, a.가정제안)
    json.dump(제안, io.open(a.가정제안, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("가정 행 제안: %s" % a.가정제안)
    for 행, 행이름, _1, _2, 종류 in 행배선:
        p = 제안.get(행) or {}
        v = p.get("값")
        if 종류 == "수준":
            # 수준 행은 값을 내지 않는다 — 상승률만 건네고 기저는 사람이 넣는다
            g = p.get("상승률")
            낸것 = ("상승률 %.4f (기저 필요)" % g) if isinstance(g, float) else "확인 불가"
        else:
            낸것 = ("%.4f" % v) if isinstance(v, float) else "확인 불가"
        print("  %-4s %-20s %-24s %s" % (행, 행이름, 낸것, p.get("확인상태")))


if __name__ == "__main__":
    main()

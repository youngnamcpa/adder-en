# -*- coding: utf-8 -*-
"""[본체 승격 2026-09-10 · HWO-54] TSLA 회차의 `tsla_환율.py` 를 그대로 올렸다 —
원래부터 티커 인자만 받는 일반형이었고, 회차 전용은 이름뿐이었다. 외국 신고인
(20-F·IFRS)·다종류 주식 예외는 회차마다 나오므로 회차 스크립트로 다시 짜지 않는다.

평가기준일 환율 — 표시통화가 USD 가 아닌 후보의 D/E·PBR 을 재려면 필요하다.

네이버 환율 창구(하나은행 고시)는 **원화 대비**만 준다. USD/JPY 같은 교차환율은
USDKRW ÷ JPYKRW 로 만든다. **JPYKRW 는 100단위 고시**라 100으로 나눈다.
값과 고시일을 같이 남긴다 — 만든 숫자가 아니라 받은 숫자임을 보이기 위해서다.

**통화 추가 (2026-09-13 · L4a 요청 · MO 회차 BTI 실측).** GBP·HKD·CAD·CHF·TWD 가 없어 BTI(GBP)의
D 가 확인 불가로 떨어졌다. 같은 창구(하나은행 고시)에서만 받는다 — 다른 출처로 채우지 않는다.
  · **고시 단위는 추측하지 않는다.** 창구의 종목 정보(`marketindex/exchange/{코드}`)의 fullName 이
    「일본 JPY 100」처럼 100 으로 끝나면 100단위다(실측: JPY 만 100, GBP·HKD·CAD·CHF·CNY·TWD 는 fullName
    없음 = 1단위). 종목 정보를 못 받으면 알려진 목록(JPY)으로 두고 그 사실을 적는다
  · **캐시가 있어도 없는 통화만 이어 받는다** — 옛 캐시(USD·JPY·EUR·CNY)의 값은 건드리지 않는다
  · 기준일 고시가 없으면 직전 거래일(표시)을 쓰고, 끝내 못 받으면 None — 지어내지 않는다

결과: _raw/peers/환율_{기준일}.json
"""
from __future__ import annotations
import argparse, io, json, os, sys, time
import requests
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEER = os.path.join(ROOT, "_raw", "peers")
H = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
# **JPY 만 100단위 고시다.** CNY 를 100으로 나누면 위안이 0.0015 USD 가 되어
# 중국 회사의 D/E 가 통째로 어긋난다(실측으로 잡았다). 종목 정보로 매번 다시 확인한다.
단위100 = {"FX_JPYKRW"}
통화목록 = ["USD", "JPY", "EUR", "CNY", "GBP", "HKD", "CAD", "CHF", "TWD"]


def 고시단위(코드):
    """(단위, 근거) — 창구 종목 정보의 fullName 끝이 100 이면 100단위."""
    try:
        r = requests.get("https://api.stock.naver.com/marketindex/exchange/%s" % 코드, headers=H, timeout=30)
        j = r.json() if r.status_code == 200 else {}
        info = j.get("exchangeInfo") or j
        full = (info.get("fullName") or "").strip()
        if info.get("name") or full:
            단위 = 100 if full.endswith(" 100") else 1
            return 단위, "종목 정보 fullName=%r name=%r" % (full or None, info.get("name"))
    except (requests.RequestException, ValueError):
        pass
    return (100 if 코드 in 단위100 else 1), "종목 정보 못 받음 — 알려진 100단위 목록(%s)으로 둠" % ",".join(sorted(단위100))


def 고시(코드, 기준일, 단위=None):
    나눔 = float(단위 or (100 if 코드 in 단위100 else 1))
    for page in range(1, 20):
        r = requests.get("https://api.stock.naver.com/marketindex/exchange/%s/prices"
                         "?page=%d&pageSize=20" % (코드, page), headers=H, timeout=30)
        if r.status_code != 200:
            return None, "조회 실패 %d" % r.status_code
        rows = r.json()
        if not rows:
            break
        for x in rows:
            if x["localTradedAt"] == 기준일:
                v = float(x["closePrice"].replace(",", ""))
                return v / 나눔, x["localTradedAt"]
        # 기준일보다 과거로 넘어갔으면 직전 거래일을 쓴다
        앞 = [x for x in rows if x["localTradedAt"] <= 기준일]
        if 앞:
            x = 앞[0]
            v = float(x["closePrice"].replace(",", ""))
            return v / 나눔, x["localTradedAt"] + "(직전 거래일)"
        time.sleep(0.2)
    return None, "기준일까지 못 닿음"


def 교차계산(원):
    """원화고시 → {통화: 1통화당 USD}. USD 가 없으면 전부 None."""
    usd = (원.get("FX_USDKRW") or {}).get("원화당")
    교차 = {}
    for 통화 in 통화목록:
        if 통화 == "USD":
            교차["USD"] = 1.0
            continue
        v = (원.get("FX_%sKRW" % 통화) or {}).get("원화당")
        교차[통화] = (v / usd) if (v and usd) else None      # 1 통화 = ? USD
    return 교차


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--기준일", "--평가기준일", dest="기준일", default="2026-06-30", help="평가기준일 T(분석일 · 시장 쪽 — 종가 · 시가총액 · 주식수 · 베타 창 끝 · 환율 · 법령 시행일) YYYY-MM-DD")
    ap.add_argument("--통화", default=",".join(통화목록), help="받을 통화(쉼표). USD 는 늘 받는다")
    a = ap.parse_args()
    p = os.path.join(PEER, "환율_%s.json" % a.기준일.replace("-", ""))
    out = json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else {}
    원 = dict(out.get("원화고시") or {})
    원하는 = ["USD"] + [c.strip().upper() for c in a.통화.split(",") if c.strip() and c.strip().upper() != "USD"]
    빠진 = [c for c in 원하는 if "FX_%sKRW" % c not in 원 or (원["FX_%sKRW" % c] or {}).get("원화당") is None]
    if out and not 빠진:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return
    if out:
        print("캐시 %s 에 없는 통화만 이어 받는다: %s (있는 값은 그대로)" % (os.path.basename(p), ",".join(빠진)))
    for c in 빠진:
        코드 = "FX_%sKRW" % c
        단위, 근거 = 고시단위(코드)
        v, d = 고시(코드, a.기준일, 단위)
        원[코드] = {"원화당": v, "고시일": d, "고시단위": 단위, "단위근거": 근거}
        print("%-10s %s (%s) · 고시단위 %d" % (코드, v, d, 단위))
    교차 = 교차계산(원)
    out.update({"기준일": a.기준일, "출처": "네이버 환율(하나은행 고시) marketindex/exchange",
                "원화고시": 원, "USD환산계수(1통화당 USD)": 교차,
                "주의": "고시단위는 창구 종목 정보(fullName 끝 100)로 확인했다 — 실측 JPY 만 100단위. "
                        "기준일 고시가 없으면 직전 거래일(고시일 칸에 표시)"})
    os.makedirs(PEER, exist_ok=True)
    json.dump(out, io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n1통화당 USD:", {k: (round(v, 6) if v else None) for k, v in 교차.items()})


if __name__ == "__main__":
    main()

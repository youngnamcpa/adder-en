# -*- coding: utf-8 -*-
"""중간 층 — 1차 통과분의 주식수(유통·발행·자기주식)를 개별로 받는다.

시가총액 분모는 **자기주식을 뺀 유통주식수**로 통일한다(대상회사 워크북과 같은 정의).
미국은 `dei/EntityCommonStockSharesOutstanding` 이 표지 기준 **유통주식수**다.
자기주식은 `us-gaap/TreasuryStockCommonShares`(또는 `TreasuryStockShares`)로 따로 확인해
**dei 값이 자기주식을 이미 뺀 값인지** 표시한다. 못 구하면 발행주식수를 썼다고 적는다.

결과는 _raw/peers/shares_{티커}.json 에 캐시한다.

2026-09-13 개정 (세일즈포스 회차 C2 실측)
  - **명단에 cik 칸이 없으면 KeyError 로 죽었다**(넓은 표본 명단). 이제 cik 를 이 순서로 찾는다:
    명단의 cik → `sub_{티커}.json`(sec_peer_meta 캐시) → `company_tickers.json` 캐시 →
    (캐시가 없을 때만) SEC company_tickers.json 1콜. 끝내 못 찾으면 **그 티커를 「cik 확인 불가」로
    적고 넘어간다** — 조용히 빼지도, 전체를 죽이지도 않는다.
  - **캐시가 기준일을 안 봤다.** 6/30 회차의 shares_ 가 7/31 회차에 그대로 쓰일 수 있었다.
    이제 캐시에 `기준일` 을 적고, 다른 기준일로 받은 캐시는 다시 받는다. 기준일이 안 적힌
    옛 캐시는 재사용하되 「기준일 미기재 캐시」로 표시한다.
  - 명단 대신 `--tickers` 로 줄 수 있다. `--캐시` 로 폴더를 바꿀 수 있다(시험용).
  - `SEC_CONTACT_EMAIL` 은 네트워크를 탈 때만 요구한다(캐시만 쓰는 재실행은 없어도 돈다).

사용:  python 스크립트/sec_shares_us.py --기준일 2026-06-30 --명단 1차통과.json
       python 스크립트/sec_shares_us.py --기준일 2026-06-30 --tickers ADBE,IBM
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
호출 = [0]


def _머리():
    contact = os.environ.get("SEC_CONTACT_EMAIL")
    if not contact:
        sys.exit("환경변수 SEC_CONTACT_EMAIL 이 없습니다(네트워크 조회가 필요한 자리).")
    return {"User-Agent": "DCF-research %s" % contact, "Accept-Encoding": "gzip, deflate"}


_로컬 = [None]


def cc(cik, tax, tag):
    # 2026-10-24 W17 — 공용 캐시 companyfacts(`cf로컬.py`)를 먼저 — 그 회사가 로컬에 있으면 네트워크로 다시 묻지 않는다
    L = _로컬[0]
    if L is not None and L.쓸수있음:
        있음, j = L.개념(cik, tax, tag)
        if 있음 and j:                                         # 1.1.2(H12) — 로컬 캐시에 그 분류(dei 따위)가 비었으면 네트워크로 묻는다(null 로 덮지 않는다)
            return j
    import requests
    H = _머리()
    url = "https://data.sec.gov/api/xbrl/companyconcept/CIK%010d/%s/%s.json" % (cik, tax, tag)
    for i in range(3):
        try:
            호출[0] += 1
            r = requests.get(url, headers=H, timeout=60)
            if r.status_code == 200:
                time.sleep(0.12)
                return r.json()
            if r.status_code == 404:
                time.sleep(0.12)
                return None
        except requests.RequestException:
            pass
        time.sleep(1.0 * (i + 1))
    return None


def 최근(j, 기준일, unit="shares"):
    """기준일 이하 시점의 가장 새 값 — **기준일까지 제출된 값(filed ≤ 기준일)을 먼저** 고른다(2026-10-24 W18 · 「평가기준일을 지킨다」).
    기준일까지 낸 값이 없을 때만 기준일 뒤에 낸 값(시점은 기준일 이하)을 쓰고 `기준일뒤: true` · 그 제출일을 단다. 기준일 뒤에 낸 더 새 값은
    `기준일뒤값` 에 적어 둔다(쓰지 않는다)."""
    if not j:
        return None
    안, 뒤 = None, None
    for u, arr in j.get("units", {}).items():
        if u != unit:
            continue
        for x in arr:
            if x["end"] > 기준일:
                continue
            if (x.get("filed") or "") > 기준일:
                if 뒤 is None or x["end"] > 뒤["end"]:
                    뒤 = x
            elif 안 is None or x["end"] > 안["end"]:
                안 = x
    if 안 is not None:
        if 뒤 is not None and 뒤["end"] > 안["end"]:
            안 = dict(안, 기준일뒤값={k: 뒤.get(k) for k in ("val", "end", "filed", "form")})
        return 안
    return dict(뒤, 기준일뒤=True) if 뒤 is not None else None


class cik해석기:
    """명단 cik → sub_ 메타 → company_tickers.json 캐시 → (없을 때만) SEC 1콜."""

    def __init__(self, 캐시, 네트워크=True):
        self.캐시, self.네트워크, self._표 = 캐시, 네트워크, None

    def _티커표(self):
        if self._표 is not None:
            return self._표
        p = os.path.join(self.캐시, "company_tickers.json")
        m = None
        if os.path.exists(p):
            m = json.load(io.open(p, encoding="utf-8"))
        elif self.네트워크:
            import requests
            호출[0] += 1
            r = requests.get("https://www.sec.gov/files/company_tickers.json", headers=_머리(), timeout=60)
            if r.status_code == 200:
                m = {}
                for _, v in r.json().items():   # sec_peer_meta.py 와 같은 캐시 모양 {cik: [티커,…]}
                    m.setdefault(str(int(v["cik_str"])), []).append(v["ticker"])
                json.dump(m, io.open(p, "w", encoding="utf-8"), ensure_ascii=False)
        self._표 = {}
        for cik, ts in (m or {}).items():
            for t in (ts if isinstance(ts, list) else [ts]):
                self._표[str(t).upper()] = int(cik)
        return self._표

    def __call__(self, 행):
        t = 행["티커"].upper()
        if 행.get("cik"):
            return int(행["cik"]), "명단"
        sp = os.path.join(self.캐시, "sub_%s.json" % t)
        if os.path.exists(sp):
            c = json.load(io.open(sp, encoding="utf-8")).get("cik")
            if c:
                return int(c), "sub_ 메타"
        c = self._티커표().get(t)
        if c:
            return c, "company_tickers"
        return None, "확인 불가"


def 명단읽기(a, 캐시):
    if a.tickers:
        return [{"티커": t.strip().upper()} for t in a.tickers.split(",") if t.strip()]
    p = a.명단 if os.path.isabs(a.명단) else os.path.join(캐시, a.명단)
    목록 = json.load(io.open(p, encoding="utf-8"))
    if isinstance(목록, dict):
        목록 = 목록.get("행") or []
    return [x for x in 목록 if x.get("티커")]


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--기준일", default="2026-06-30")
    ap.add_argument("--명단", default="1차통과.json")
    ap.add_argument("--tickers", default=None, help="명단 대신 쉼표 구분 티커")
    ap.add_argument("--캐시", default=None, help="_raw/peers 대신(시험용)")
    ap.add_argument("--네트워크만", action="store_true", help="공용 캐시 companyfacts 를 쓰지 않는다(종전 동작)")
    a = ap.parse_args()
    if not a.네트워크만:
        try:
            import cf로컬
            _로컬[0] = cf로컬.로컬(a.기준일)
        except Exception:                                    # noqa: BLE001
            _로컬[0] = None
    캐시 = os.path.abspath(a.캐시) if a.캐시 else PEER
    후보 = 명단읽기(a, 캐시)
    해석 = cik해석기(캐시)
    적중, 실패 = 0, []
    print("%-7s %-30s %14s %12s %12s %s"
          % ("티커", "회사명", "유통(dei)", "기준일", "자기주식", "비고"))
    for d in 후보:
        t = d["티커"].upper()
        p = os.path.join(캐시, "shares_%s.json" % t)
        비고 = []
        r = None
        if os.path.exists(p):
            r = json.load(io.open(p, encoding="utf-8"))
            옛기준일 = r.get("기준일")
            if 옛기준일 and 옛기준일 != a.기준일:
                비고.append("캐시 기준일 %s ≠ %s — 다시 받음" % (옛기준일, a.기준일))
                r = None
            else:
                적중 += 1
                if not 옛기준일:
                    비고.append("기준일 미기재 캐시(옛 판) — 재사용")
        if r is None:
            cik, 출처 = 해석(d)
            if not cik:
                실패.append(t)
                print("%-7s %-30s %14s %12s %12s %s" % (t, str(d.get("회사명"))[:30], "-", "-", "-",
                                                     "*** cik 확인 불가 — sec_peer_meta 를 먼저 돌리십시오(조용히 빼지 않음)"))
                continue
            if 출처 != "명단":
                비고.append("cik %d ← %s" % (cik, 출처))
            dei = 최근(cc(cik, "dei", "EntityCommonStockSharesOutstanding"), a.기준일)
            tre = None
            for tag in ("TreasuryStockCommonShares", "TreasuryStockShares"):
                tre = 최근(cc(cik, "us-gaap", tag), a.기준일)
                if tre:
                    break
            발행 = None
            for tag in ("CommonStockSharesOutstanding", "CommonStockSharesIssued"):      # 1.1.2(H12) — 유통 태그가 먼저(발행은 자기주식을 담는다)
                발행 = 최근(cc(cik, "us-gaap", tag), a.기준일)
                if 발행:
                    발행 = dict(발행, 태그=tag)
                    break
            # 2026-10-24 W17 — dei 표지 주식수가 기준일보다 1년 넘게 묵었으면 표시한다(F 2011 · HMC 2020 실측) — 중간 층이 표지 큐에 넣는다
            묵음선 = "%04d%s" % (int(a.기준일[:4]) - 1, a.기준일[4:])
            r = {"티커": t, "cik": cik, "기준일": a.기준일,
                 "유통_dei": dei, "자기주식": tre, "발행_usgaap": 발행,
                 "dei묵음": bool(dei and dei["end"] < 묵음선) or (dei is None),
                 "정의": "dei/EntityCommonStockSharesOutstanding = 표지 기준 유통주식수"}
            json.dump(r, io.open(p, "w", encoding="utf-8"), ensure_ascii=False)
        dei, tre = r.get("유통_dei"), r.get("자기주식")
        if not dei:
            비고.append("*** dei 없음 — 발행주식수 대체 필요")
        print("%-7s %-30s %14s %12s %12s %s"
              % (t, str(d.get("회사명"))[:30],
                 ("%d" % dei["val"]) if dei else "확인 불가",
                 dei["end"] if dei else "-",
                 ("%d" % tre["val"]) if tre else "0/없음", " · ".join(비고)))
    print("\n네트워크 호출 %d · 캐시 적중 %d · cik 확인 불가 %d%s"
          % (호출[0], 적중, len(실패), (" (%s)" % ",".join(실패)) if 실패 else ""))


if __name__ == "__main__":
    main()

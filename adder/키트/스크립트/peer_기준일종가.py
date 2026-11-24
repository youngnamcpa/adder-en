# -*- coding: utf-8 -*-
"""평가기준일 **당일** 종가 — 해외 종목도 일봉 창구가 열려 있다.

`naver_price.py` 는 「기간 지정 창구는 국내 전용」이라고 적어 두었는데, 그것은
`api.finance.naver.com/siseJson.naver` 이야기다. **`api.stock.naver.com` 의
`periodType=dayCandle` 은 해외 종목에도 열려 있고 110거래일(약 5개월)을 준다.**
평가기준일이 최근 5개월 안이면 **주봉의 마지막 캔들 대신 당일 종가를 쓸 수 있다.**

왜 중요한가 (실측)
  IREN 의 2026-06-30 종가는 **45.73** 인데, 주봉에서 평가기준일 이전 마지막 캔들은
  2026-06-26 의 **47.21** 이다. 그 주에 주가가 급락해 **3.1% 차이**가 나고,
  시가총액과 규모대 컷이 그만큼 흔들린다.

결과는 _raw/peers/종가_{기준일}.json 에 캐시한다.
"""
from __future__ import annotations

import argparse
import io
import importlib.util
import json
import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 피어경로 as 피경  # noqa: E402 — 명단 경로 · 종가 파일 이름 한 규칙(2026-10-24 W15)

import requests

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEER = 피경.피어폴더(ROOT)                    # 사슬 `--캐시` 가 DCF_PEER_CACHE 로 닿는다(2026-10-24 W15 — 종전에는 이 도구만 키트 _raw/peers 에 썼다)
H = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

spec = importlib.util.spec_from_file_location(
    "naver_price", os.path.join(ROOT, "스크립트", "naver_price.py"))
np = importlib.util.module_from_spec(spec)
spec.loader.exec_module(np)


def 일봉(tic):
    # 캐시 폴더가 없으면 저장이 죽고 except 가 「조회 실패」로 위장한다(국내판 실측)
    os.makedirs(PEER, exist_ok=True)
    p = os.path.join(PEER, "day_%s.json" % tic)
    if os.path.exists(p):
        return json.load(io.open(p, encoding="utf-8")), "캐시"
    rc = np.resolve_code(tic) if not tic.startswith(".") else tic
    if not rc:
        return None, "reutersCode 확인 불가"
    base = ("https://api.stock.naver.com/chart/foreign/index/%s" if tic.startswith(".")
            else "https://api.stock.naver.com/chart/foreign/item/%s")
    for i in range(3):
        try:
            r = requests.get((base % rc) + "?periodType=dayCandle&count=110",
                             headers=H, timeout=40)
            if r.status_code == 200 and r.text.strip() not in ("{}", ""):
                j = r.json()
                infos = j.get("priceInfos") or (j if isinstance(j, list) else None)
                if infos:
                    rows = [(x["localDate"], float(x["closePrice"])) for x in infos]
                    json.dump(rows, io.open(p, "w", encoding="utf-8"))
                    time.sleep(0.2)
                    return rows, "신규"
        except (requests.RequestException, ValueError, KeyError):
            pass
        time.sleep(1.2 * (i + 1))
    return None, "조회 실패"


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--기준일", "--평가기준일", dest="기준일", default="20260630", help="평가기준일 T(분석일 · 시장 쪽 — 종가 · 시가총액 · 주식수 · 베타 창 끝 · 환율 · 법령 시행일) YYYY-MM-DD")
    ap.add_argument("--명단", default="1차통과.json")
    ap.add_argument("--추가", default="")
    a = ap.parse_args()
    # **명단이 없어도 돈다.** 유사기업 갈래를 안 도는 회차에서도 대상회사 종가는
    # 늘 필요하다(원천 99행). 실측(UBER): 명단 파일이 없어 죽었다.
    명단길 = 피경.명단경로(a.명단, PEER, ROOT)
    티커 = []
    if os.path.exists(명단길):
        티커 = [d["티커"] for d in json.load(io.open(명단길, encoding="utf-8"))]
    else:
        print("명단 %s 이 없습니다 — `--추가` 로 준 티커만 받습니다" % a.명단)
    티커 += [x.strip() for x in a.추가.split(",") if x.strip()]
    if not 티커:
        raise SystemExit("받을 티커가 없습니다 — `--추가 UBER` 처럼 지정하십시오")
    # **기존 파일에 병합한다 — 덮어쓰지 않는다.** 실측(미국 사슬 시험 2026-09-10):
    # 층마다 다른 목록으로 두 번 돌리자 두 번째 실행이 첫 실행의 19키를 1키로 덮었다.
    출력경로 = 피경.종가파일(PEER, a.기준일)              # 정본 이름 종가_YYYYMMDD.json — 기준일을 어느 꼴로 줘도 같다(W15)
    종가 = 피경.종가읽기(PEER, a.기준일)                   # 옛 꼴(종가_YYYY-MM-DD.json)도 합쳐 읽는다
    실패 = []
    캐, 신 = 0, 0
    for t in 티커:
        rows, how = 일봉(t)
        if rows is None:
            실패.append((t, how))
            print("%-6s *** 실패: %s — 조용히 빼지 않는다" % (t, how))
            continue
        캐, 신 = (캐 + 1, 신) if how == "캐시" else (캐, 신 + 1)
        # 일봉 날짜는 「20260630」 꼴이다 — 기준일을 「2026-06-30」 으로 주면 비교가
        # 전부 어긋나 「못 닿음」 으로 위장된다(실측: 6곳 일괄 실패, 값은 다 있었다).
        기준 = a.기준일.replace("-", "")
        정 = [x for x in rows if x[0] == 기준]
        앞 = [x for x in rows if x[0] <= 기준]
        if 정:
            종가[t] = {"종가": 정[0][1], "일자": a.기준일, "일치": True}
        elif 앞:
            종가[t] = {"종가": 앞[-1][1], "일자": 앞[-1][0], "일치": False}
        else:
            실패.append((t, "일봉 창구가 평가기준일까지 못 닿음(110거래일 상한)"))
            print("%-6s *** 일봉이 평가기준일에 못 닿음 (시작 %s)" % (t, rows[0][0]))
            continue
        print("%-6s %10.4f  (%s%s) [%s]"
              % (t, 종가[t]["종가"], 종가[t]["일자"],
                 "" if 종가[t]["일치"] else " ← 당일 없음, 직전 거래일", how))
    json.dump(종가, io.open(출력경로, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n캐시 %d · 신규 %d · 실패 %d → %s"
          % (캐, 신, len(실패), 출력경로))
    for t, w in 실패:
        print("  실패 %s: %s" % (t, w))


if __name__ == "__main__":
    main()

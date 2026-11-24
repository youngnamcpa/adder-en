# -*- coding: utf-8 -*-
"""주식 총수 현황(stockTotqySttus) 일괄 — 시가총액 분모를 만드는 **중간 층**.

시가총액의 분모는 **자기주식을 뺀 유통주식수**다. 이 창구가 그것을 바로 준다
(`distb_stock_co`). 발행주식수(`istc_totqy`)와 자기주식수(`tesstk_co`)도 함께 남긴다.

**`isu_stock_totqy` 는 발행주식수가 아니다 — 정관상 「발행할 주식의 총수」(수권주식수)다.**
이름이 비슷해 그대로 분모로 쓰기 쉬운데, 실측으로 삼화전자공업은 수권 49,100,000 대
발행 19,165,785 로 2.6배가 벌어진다. 시가총액이 통째로 부푼다.

**구분(`se`) 값이 회사마다 갈린다.** 「보통주」와 「보통주식」이 섞여 있고,
「합계」·「우선주」·「우선주식」·「-」 도 온다. 한쪽 이름만 찾으면 시가총액이
통째로 빈다 — 그래서 여기서는 이름을 고정하지 않고 **우선주 계열을 뺀 나머지 중
가장 큰 행**을 보통주로 본다. 실제로 잡힌 구분 이름을 CSV 에 함께 남긴다.

또 하나: **숫자 칸에 `-` 가 온다.** 자기주식이 없으면 0 이 아니라 `-` 다. 0 으로 읽는다.

안전 속도: 2스레드 · 호출 사이 0.6초. 캐시가 있으면 네트워크를 타지 않는다.

사용
    python 스크립트/dart_shares.py --codes-file 후보.txt --year 2026 --reprt 11012
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import queue
import sys
import threading
import time
import urllib.parse
import urllib.request

API = "https://opendart.fss.or.kr/api/stockTotqySttus.json"
# 2026-10-25 FX4-P — DCF_RUN_ROOT(사슬 `--폴더` 가 넘긴다)면 그 회차에 쓴다 — 본체 경로로 돌려도 본체 _raw 에 쌓지 않게
ROOT = os.environ.get("DCF_RUN_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHEDIR = os.path.join(ROOT, "_raw", "peers", "shares")
PAUSE, THREADS = 0.6, 2
우선주표시 = ("우선",)


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


def 한곳(code, year, reprt, key):
    p = os.path.join(CACHEDIR, "%s_%s_%s.json" % (code, year, reprt))
    if os.path.exists(p):
        try:
            return json.load(io.open(p, encoding="utf-8")), "캐시"
        except ValueError:
            pass
    url = "%s?%s" % (API, urllib.parse.urlencode(
        {"crtfc_key": key, "corp_code": code, "bsns_year": year, "reprt_code": reprt}))
    last = None
    for i in range(3):
        try:
            j = json.loads(urllib.request.urlopen(url, timeout=30).read().decode("utf-8"))
            json.dump(j, io.open(p, "w", encoding="utf-8"), ensure_ascii=False)
            return j, "신규"
        except Exception as e:                       # noqa: BLE001
            last = e
            time.sleep(1.5 * (i + 1))
    return {"status": "실패", "message": str(last)}, "실패"


def 보통주행(j):
    """우선주 계열을 뺀 행 중 **발행한** 주식 총수가 가장 큰 것. 「합계」 행은 뺀다.

    **`isu_stock_totqy` 는 발행주식수가 아니라 정관상 「발행할 주식의 총수」(수권주식수)다.**
    실측: 삼화전자공업 49,100,000(수권) 대 19,165,785(발행·유통). 이것을 분모로 쓰면
    시가총액이 2.6배로 부푼다. 발행주식수는 `istc_totqy`, 유통은 `distb_stock_co` 다.
    수권주식수 칸이 `-` 인 회사도 있어(실측: 알엔투테크놀로지) 그 칸으로 고르면
    회사가 통째로 빈다 — 고르는 기준도 `istc_totqy` 로 둔다.

    구분(`se`) 이름은 「보통주」·「보통주식」·「의결권있는주식\\n(보통주)」 가 섞여 온다.
    이름을 고정하지 않고 우선주 계열만 뺀다.
    """
    후보 = []
    for it in (j.get("list") or []):
        se = (it.get("se") or "").strip()
        if not se or "우선" in se or se.startswith("합계"):
            continue
        n = _num(it.get("istc_totqy"))
        if n:
            후보.append((n, se, it))
    if not 후보:
        return None
    후보.sort(reverse=True, key=lambda x: x[0])
    return 후보[0][2]


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--codes", "--고유번호", dest="codes",
                    help="DART 고유번호(8자리) 쉼표 목록 — 종목코드(6자리)를 주면 corpCode 캐시로 고유번호로 바꾼다(S10-20)")
    ap.add_argument("--codes-file")
    ap.add_argument("--year", required=True)
    ap.add_argument("--reprt", default="11012")
    ap.add_argument("--out", default="주식수.csv")
    a = ap.parse_args()

    if a.codes_file:
        raw = [l.strip() for l in io.open(a.codes_file, encoding="utf-8") if l.strip()]
    elif a.codes:
        raw = [c.strip() for c in a.codes.split(",") if c.strip()]
    else:
        ap.error("--codes 또는 --codes-file")
    # S10-20 — 종목코드(6자리)를 주면 고유번호(8자리)로 바꾼다. 그대로 두면 0 을 채운 엉뚱한 번호로 물어 status 013 의 빈 줄이 rc 0 으로 남았다
    여섯 = [c for c in raw if len(c) == 6]
    if 여섯:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import dart_fetch as _DF                                  # noqa: PLC0415
        표 = _DF.고유번호풀기(여섯)
        못 = [c for c in 여섯 if not 표.get(c)]
        if 못:
            print("종목코드 %s 의 고유번호를 corpCode 캐시에서 못 찾았습니다 — 고유번호(8자리)를 --고유번호 로 주십시오" % ",".join(못), file=sys.stderr)
            sys.exit(2)
        print("종목코드 6자리 %d개를 고유번호로 바꿨다: %s" % (len(여섯), " · ".join("%s→%s" % (c, 표[c]) for c in 여섯)), file=sys.stderr)
        raw = [표.get(c, c) if len(c) == 6 else c for c in raw]
    codes = [c.zfill(8) for c in raw]

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
            j, how = 한곳(c, a.year, a.reprt, key)
            with lock:
                결과[c] = j
            if how == "신규":
                time.sleep(PAUSE)

    ts = [threading.Thread(target=일꾼) for _ in range(THREADS)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()

    out = a.out if os.path.isabs(a.out) else os.path.join(ROOT, a.out)
    cols = ["고유번호", "구분이름", "수권주식수", "발행주식총수", "자기주식수", "유통주식수", "status"]
    빈곳 = []
    with io.open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for c, j in 결과.items():
            row = 보통주행(j)
            if row is None:
                빈곳.append(c)
                w.writerow({"고유번호": c, "status": j.get("status", "")})
                continue
            수권 = _num(row.get("isu_stock_totqy"))
            발행 = _num(row.get("istc_totqy"))
            자기 = _num(row.get("tesstk_co")) or 0
            유통 = _num(row.get("distb_stock_co"))
            w.writerow({"고유번호": c,
                        "구분이름": " ".join((row.get("se") or "").split()),
                        "수권주식수": 수권, "발행주식총수": 발행, "자기주식수": 자기,
                        "유통주식수": 유통 if 유통 is not None else "",
                        "status": j.get("status", "")})
    print("%d곳 → %s" % (len(결과), out), file=sys.stderr)
    if 빈곳:
        print("보통주 행을 못 찾은 곳 %d — 조용히 빼지 말 것: %s"
              % (len(빈곳), ",".join(빈곳)), file=sys.stderr)
        if len(빈곳) == len(결과):                 # S10-20 — 한 곳도 못 읽었으면 성공으로 끝내지 않는다
            sys.exit(1)


if __name__ == "__main__":
    main()

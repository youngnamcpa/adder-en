# -*- coding: utf-8 -*-
"""기업개황(company.json) 일괄 수집 — **산업분류(induty_code)를 얻는 유일한 창구**.

왜 따로 있는가
    `dart_peer_screen.py` 는 주요계정만 준다. **산업분류는 거기 없다.**
    그런데 유사기업 경로 ①(산업분류가 같은 상장사 전체)은 산업분류가 있어야 시작된다.
    OpenDART 에는 산업분류 일괄 창구가 없고 `company.json` 이 한 번에 한 곳만 답한다.
    그래서 이 파일이 **캐시를 깔고 2스레드로 훑는다.** 한 번 받으면 다시 받지 않는다.

    같이 나오는 것: 종목코드·상장시장(corp_cls Y/K/N/E)·설립일·결산월.
    **상장시장과 설립일은 사업 단계 컷의 재료**이므로 함께 남긴다.

안전 속도
    2스레드 · 각 스레드가 호출 사이 0.6초. 어기면 응답 없이 끊기고 30분 막힌다.
    1,700곳이면 약 9분이다.

사용
    python 스크립트/dart_induty.py --codes-file _raw/peers/1차밴드_고유번호.txt
    python 스크립트/dart_induty.py --codes 00129280,00164779
    python 스크립트/dart_induty.py --codes-file ... --out 산업분류.csv

캐시: _raw/peers/company/{고유번호}.json — 있으면 네트워크를 타지 않는다.
인증키는 환경변수 OPENDART_API_KEY 에서만 읽고 화면·파일에 출력하지 않는다.
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

API = "https://opendart.fss.or.kr/api/company.json"
# 2026-10-25 FX4-P — DCF_RUN_ROOT(사슬 `--폴더` 가 넘긴다)면 그 회차에 쓴다 — 본체 경로로 돌려도 본체 _raw 에 쌓지 않게
ROOT = os.environ.get("DCF_RUN_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHEDIR = os.path.join(ROOT, "_raw", "peers", "company")
PAUSE = 0.6          # 스레드마다 호출 사이 간격
THREADS = 2          # DART 안전 속도 상한


def _key() -> str:
    k = os.environ.get("OPENDART_API_KEY")
    if not k:
        sys.exit("환경변수 OPENDART_API_KEY 가 없습니다. 값은 화면에 적지 마십시오.")
    return k


def 한곳(code: str, key: str):
    """캐시가 있으면 그것을. 없으면 받아서 캐시한다. (dict, '캐시'|'신규'|'실패')"""
    p = os.path.join(CACHEDIR, "%s.json" % code)
    if os.path.exists(p):
        try:
            return json.load(io.open(p, encoding="utf-8")), "캐시"
        except ValueError:
            pass
    url = "%s?%s" % (API, urllib.parse.urlencode({"crtfc_key": key, "corp_code": code}))
    last = None
    for i in range(3):
        try:
            j = json.loads(urllib.request.urlopen(url, timeout=30).read().decode("utf-8"))
            json.dump(j, io.open(p, "w", encoding="utf-8"), ensure_ascii=False)
            return j, "신규"
        except Exception as e:                      # noqa: BLE001
            last = e
            time.sleep(1.5 * (i + 1))
    return {"status": "실패", "message": str(last)}, "실패"


def 훑기(codes, 진행마다=100):
    key = _key()
    os.makedirs(CACHEDIR, exist_ok=True)
    q = queue.Queue()
    for c in codes:
        q.put(c)
    결과, 자물쇠, 셈 = {}, threading.Lock(), {"신규": 0, "캐시": 0, "실패": 0}

    def 일꾼():
        while True:
            try:
                c = q.get_nowait()
            except queue.Empty:
                return
            j, how = 한곳(c, key)
            with 자물쇠:
                결과[c] = j
                셈[how] += 1
                n = len(결과)
                if n % 진행마다 == 0:
                    print("  %d/%d (신규 %d · 캐시 %d · 실패 %d)"
                          % (n, len(codes), 셈["신규"], 셈["캐시"], 셈["실패"]),
                          file=sys.stderr)
            if how == "신규":
                time.sleep(PAUSE)

    ts = [threading.Thread(target=일꾼) for _ in range(THREADS)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return 결과, 셈


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--codes")
    ap.add_argument("--codes-file")
    ap.add_argument("--out", default="산업분류.csv")
    a = ap.parse_args()

    if a.codes_file:
        codes = [l.strip().zfill(8) for l in io.open(a.codes_file, encoding="utf-8")
                 if l.strip()]
    elif a.codes:
        codes = [c.strip().zfill(8) for c in a.codes.split(",") if c.strip()]
    else:
        ap.error("--codes 또는 --codes-file 이 필요합니다")

    t0 = time.time()
    결과, 셈 = 훑기(codes)
    cols = ["고유번호", "회사명", "종목코드", "상장구분", "산업분류코드", "설립일", "결산월", "대표자", "status"]
    out = a.out if os.path.isabs(a.out) else os.path.join(ROOT, a.out)
    with io.open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for c, j in 결과.items():
            w.writerow({
                "고유번호": c,
                "회사명": j.get("corp_name", ""),
                "종목코드": j.get("stock_code", ""),
                "상장구분": j.get("corp_cls", ""),
                "산업분류코드": j.get("induty_code", ""),
                "설립일": j.get("est_dt", ""),
                "결산월": j.get("acc_mt", ""),
                "대표자": j.get("ceo_nm", ""),
                "status": j.get("status", ""),
            })
    print("%d곳 · %.0f초 · 신규 %d · 캐시 %d · 실패 %d → %s"
          % (len(결과), time.time() - t0, 셈["신규"], 셈["캐시"], 셈["실패"], out),
          file=sys.stderr)
    실패 = [c for c, j in 결과.items() if j.get("status") not in ("000", None)]
    if 실패:
        print("status 가 정상이 아닌 곳 %d — 조용히 빼지 말 것: %s"
              % (len(실패), ",".join(실패[:10])), file=sys.stderr)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""상장명부 — 경로 ①(산업분류 스크린)의 전수 병목을 죽인다 (HWO-50).

**병목 실측(한화오션 회차):** 산업분류가 기업개황에만 있어 상장 3,930곳을 한 곳씩
불렀다 — 1,701초. 안전 속도(2스레드·0.5초)를 지키면 그게 최선이었다.

**처방:** KIND 상장법인목록(1콜·0.7초 실측)이 전 상장사의 업종명을 준다.
  · 업종명이 세분류급(「선박 및 보트 건조업」=311)이면 그대로 후보다
  · 업종명이 뭉치는 버킷(「일반 목적용 기계 제조업」=291, 51곳 실측)만
    기업개황으로 세세분류를 확정한다 — 전수 3,930콜이 버킷 수십 콜이 된다
  · KIND 는 **현재 상장사만** 담는다 — corpCode 의 상장폐지·소멸 잔재
    (실측 5곳: 스타코링크·케이조선·대선조선·HD현대미포·트레스)가 자동으로 빠진다.
    그 잔재가 후보로 필요하면(소멸 직전 동종 관측 등) census 캐시에서 본다
  · 한 번 확정한 세세분류는 `산업분류_전수.csv` 캐시에 쌓는다 — 거의 안 변하는
    자료라 다음 회차는 캐시 + 신규상장(KIND 상장일)만 증분한다

사용:
    python 스크립트/상장명부.py --버킷 선박                      # KIND 업종명 부분일치
    python 스크립트/상장명부.py --버킷 선박,기계 --세세분류 311,2911 --확정
    python 스크립트/상장명부.py --새로고침                       # KIND 캐시(30일) 갱신

**인증키는 환경변수 `OPENDART_API_KEY` 에서만 읽는다** (--확정 때만 필요).
안전 속도: DART 는 **2스레드 · 호출 사이 0.5초** — 유사기업-선정 스킬 실측 규칙 그대로.
"""
import argparse
import csv
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8")
캐시칸 = os.path.join(os.getcwd(), "_dartcache")
os.makedirs(캐시칸, exist_ok=True)
KIND경로 = os.path.join(캐시칸, "상장명부_KIND.csv")
전수경로 = os.path.join(os.getcwd(), "산업분류_전수.csv")   # 회차 폴더의 census 캐시에 이어 쓴다
유효일 = 30


def _kind받기():
    url = "https://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    데이터 = urllib.request.urlopen(req, timeout=60).read().decode("euc-kr", errors="ignore")
    행들 = re.findall(r"<tr>(.*?)</tr>", 데이터, re.S)
    표 = {}
    for r in 행들[1:]:
        c = [re.sub(r"<[^>]+>", "", x).strip() for x in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
        if len(c) >= 6 and re.fullmatch(r"\d{6}", c[2]):
            표[c[2]] = {"회사명": c[0], "시장": c[1], "종목코드": c[2],
                       "업종": c[3], "주요제품": c[4][:60], "상장일": c[5]}
    return 표


def _corp조인(표):
    """corpCode.xml(캐시)에서 종목코드 → 고유번호를 붙인다."""
    xml경로 = os.path.join(캐시칸, "corpCode.xml")
    if not os.path.exists(xml경로):
        return 표, "corpCode.xml 캐시가 없어 고유번호를 못 붙였습니다 — dart_fetch 로 먼저 받으십시오"
    본문 = io.open(xml경로, encoding="utf-8", errors="ignore").read()
    짝 = {}
    for m in re.finditer(r"<list>(.*?)</list>", 본문, re.S):
        t = m.group(1)
        s = re.search(r"<stock_code>(\d{6})</stock_code>", t)
        c = re.search(r"<corp_code>(\d{8})</corp_code>", t)
        if s and c:
            짝[s.group(1)] = c.group(1)
    for 코드, v in 표.items():
        v["고유번호"] = 짝.get(코드, "")
    빠짐 = sum(1 for v in 표.values() if not v["고유번호"])
    경고 = "고유번호 미결 %d곳 (corpCode 미등재 신규상장일 수 있음)" % 빠짐 if 빠짐 else None
    return 표, 경고


def 명부(새로고침=False):
    if not 새로고침 and os.path.exists(KIND경로):
        나이 = (time.time() - os.path.getmtime(KIND경로)) / 86400
        if 나이 <= 유효일:
            표 = {r["종목코드"]: r for r in csv.DictReader(io.open(KIND경로, encoding="utf-8-sig"))}
            print("KIND 캐시 사용 (%.0f일 전 · %d곳) — --새로고침 으로 다시 받습니다" % (나이, len(표)))
            # 손개입 개선 1(2026-10-18) — 캐시가 corpCode.xml 보다 먼저 만들어져 고유번호가 비어 있으면 지금 다시 붙이고 캐시를 고쳐 쓴다(실측: 전수 확정이 0곳)
            if any(not (v.get("고유번호") or "") for v in 표.values()) and os.path.exists(os.path.join(캐시칸, "corpCode.xml")):
                표, 경고 = _corp조인(표)
                with io.open(KIND경로, "w", encoding="utf-8-sig", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=["회사명", "시장", "종목코드", "고유번호", "업종", "주요제품", "상장일"], extrasaction="ignore")
                    w.writeheader()
                    for v in 표.values():
                        w.writerow(v)
                print("고유번호를 corpCode.xml 로 다시 붙였습니다 — %d곳%s" % (sum(1 for v in 표.values() if v.get("고유번호")), (" · " + 경고) if 경고 else ""))
            return 표
    t0 = time.time()
    표 = _kind받기()
    표, 경고 = _corp조인(표)
    with io.open(KIND경로, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["회사명", "시장", "종목코드", "고유번호", "업종", "주요제품", "상장일"])
        w.writeheader()
        for v in 표.values():
            w.writerow(v)
    print("KIND %d곳 · %.1f초 · 캐시 %s" % (len(표), time.time() - t0, KIND경로))
    if 경고:
        print("주의:", 경고)
    return 표


def _census읽기():
    if not os.path.exists(전수경로):
        return {}
    return {r["종목코드"]: r for r in csv.DictReader(io.open(전수경로, encoding="utf-8-sig"))}


def 확정(표, 세세분류들):
    """세세분류가 필요한데 KIND 업종명이 뭉치는 부분집합만 기업개황으로 푼다.

    census 캐시(산업분류_전수.csv)에 있는 회사는 다시 부르지 않는다 — 산업분류는
    거의 안 변하는 자료다. 새로 부른 것은 캐시에 이어 써서 다음 회차가 재사용한다."""
    KEY = os.environ.get("OPENDART_API_KEY", "")
    census = _census읽기()
    답 = {}
    미결 = []
    for 코드, v in 표.items():
        c = census.get(코드)
        if c and c.get("산업분류코드"):
            v["산업분류코드"] = c["산업분류코드"]
            답[코드] = v
        elif v.get("고유번호"):
            미결.append(v)
    if 미결 and not KEY:
        sys.stderr.write("OPENDART_API_KEY 가 없어 미결 %d곳의 세세분류를 못 확정합니다\n" % len(미결))
    elif 미결:
        print("기업개황 확정 대상 %d곳 (census 캐시 재사용 %d곳) — 2스레드·0.5초 안전 속도"
              % (len(미결), len(답)))

        def 한곳(v):
            time.sleep(0.5)
            u = "https://opendart.fss.or.kr/api/company.json?" + urllib.parse.urlencode(
                dict(crtfc_key=KEY, corp_code=v["고유번호"]))
            try:
                d = json.loads(urllib.request.urlopen(u, timeout=30).read().decode())
                v["산업분류코드"] = d.get("induty_code", "")
            except Exception as e:
                v["산업분류코드"] = ""
                v["_실패"] = str(e)[:60]
            return v

        t0 = time.time()
        with ThreadPoolExecutor(2) as ex:
            for v in ex.map(한곳, 미결):
                답[v["종목코드"]] = v
        실패 = [v for v in 미결 if v.get("_실패")]
        print("확정 %.0f초 · 실패 %d곳" % (time.time() - t0, len(실패)))
        for v in 실패:
            print("  실패:", v["회사명"], v["_실패"])
        새줄 = [v for v in 미결 if v.get("산업분류코드")]
        if 새줄:
            열 = (list(next(iter(census.values())).keys()) if census else
                 ["고유번호", "회사명", "종목코드", "상장구분", "산업분류코드", "설립일", "결산월", "대표자"])
            처음 = not os.path.exists(전수경로)
            with io.open(전수경로, "a", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=열, extrasaction="ignore")
                if 처음:
                    w.writeheader()
                for v in 새줄:
                    w.writerow({"고유번호": v["고유번호"], "회사명": v["회사명"],
                               "종목코드": v["종목코드"], "상장구분": v["시장"],
                               "산업분류코드": v["산업분류코드"]})
            print("census 캐시에 %d곳 이어 씀 → %s" % (len(새줄), 전수경로))
    걸림 = {}
    for 코드, v in 답.items():
        분류 = str(v.get("산업분류코드", ""))
        if any(분류.startswith(s) for s in 세세분류들):
            걸림[코드] = v
    return 걸림


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="상장명부 — 경로 ① 스크린 (KIND 1콜 + 버킷만 기업개황)")
    ap.add_argument("--버킷", help="KIND 업종명 부분일치 (쉼표로 여러 개)")
    ap.add_argument("--세세분류", help="산업분류코드 접두(쉼표)")
    ap.add_argument("--확정", action="store_true", help="--세세분류의 미결분을 기업개황으로 확정")
    ap.add_argument("--새로고침", action="store_true", help="KIND 캐시를 무시하고 다시 받는다")
    ap.add_argument("-o", "--출력", default=None, help="결과 CSV 경로")
    a = ap.parse_args()
    표 = 명부(a.새로고침)
    결과 = 표
    if a.버킷:
        말들 = [x.strip() for x in a.버킷.split(",") if x.strip()]
        결과 = {k: v for k, v in 표.items() if any(m in v["업종"] for m in 말들)}
        print("버킷 일치 %d곳" % len(결과))
    if a.세세분류:
        접두 = [x.strip() for x in a.세세분류.split(",") if x.strip()]
        if a.확정:
            결과 = 확정(결과, 접두)
        else:
            census = _census읽기()
            결과 = {k: dict(v, 산업분류코드=census.get(k, {}).get("산업분류코드", "?"))
                   for k, v in 결과.items()
                   if any(str(census.get(k, {}).get("산업분류코드", "")).startswith(s) for s in 접두)}
        print("세세분류 %s → %d곳" % (접두, len(결과)))
    for v in sorted(결과.values(), key=lambda x: x["회사명"]):
        print("  %-6s %-14s %-8s %s | 상장 %s" % (v["종목코드"], v["회사명"][:14],
              v.get("산업분류코드", ""), v["업종"][:24], v["상장일"]))
    if a.출력:
        with io.open(a.출력, "w", encoding="utf-8-sig", newline="") as f:
            열 = ["회사명", "시장", "종목코드", "고유번호", "업종", "산업분류코드", "주요제품", "상장일"]
            w = csv.DictWriter(f, fieldnames=열, extrasaction="ignore")
            w.writeheader()
            for v in 결과.values():
                w.writerow(v)
        print("→", a.출력)


if __name__ == "__main__":
    main()

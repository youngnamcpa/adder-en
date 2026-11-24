# -*- coding: utf-8 -*-
"""국내 유사기업 재료 수집 사슬 (HWO-56) — 두 창구를 병렬 차선으로 겹친다.

**병목 실측(한화오션):** 비싼 층(시세·주식수·전체재무) 첫 수집이 약 10분 — 한 갈래가
naver 시세와 DART 재무를 번갈아 순차로 돌았다. **DART 의 안전 속도(2스레드·호출 간
0.5초)는 창구 단위이지 회차 단위가 아니다** — naver 시세는 DART 요율을 안 먹는다.

**처방:** 창구가 다른 두 차선을 병렬로 겹친다. 차선 안은 각 도구의 안전 속도 그대로다.
  차선 A (DART)  : 기업개황(산업분류) → 주식수 → 전체 재무제표
  차선 B (naver) : 평가기준일 종가 → 회귀 창(`--창년`, 기본 5년) 주봉 + 1년 일봉(거래 두께) + 지수

**회귀 창 기본 5년 주간(2026-10-16 결정).** 옛 기본은 기준일−3년이었다. `--창년` 으로 바꾸고
(`--부터` 를 주면 그것이 이긴다) 조립기에도 같은 창년을 넘겨, 더 긴 캐시가 창을 조용히 늘리지 않게 한다.

**운영 동종 전용 회사(2026-10-16 · 결정 5).** 명단의 `목적` 에 「위험동종」이 없는 회사는 βU 를 세우지 않으므로
시세 · 주식수 · 종가를 받지 않고 **재무만** 받는다(비싼 층의 전체 재무제표). `--단계 운영` 은 `peer_운영지표.py`
를 돌려 운영 지표(`_raw/peers/운영지표_{운영표본}.json`)를 낸다 — `전부` 는 중간 → 비싼 → 운영 순이다.
명단은 목록 JSON 이든 C1 `핵심표본.json`(핵심 · 예비 · 운영 동종 전용 · 컷통과_전체)이든 된다. 거를 회사가 있거나
핵심표본 꼴이면 하위 도구에는 `_raw/peers/_사슬명단_{표본}.json`(위험 동종 목록)을 넘긴다.

**컷은 이 사슬의 소유가 아니다** — 선언한 기준으로 사람이 자른다(유사기업-선정 스킬).
사슬은 층 사이의 수집만 묶는다:

    python 스크립트/dart_peer_사슬.py --단계 중간 --명단 1차통과.json --기준일 20260630 --년도 2026
    python 스크립트/dart_peer_사슬.py --단계 비싼 --명단 2차통과.json --기준일 20260630 --년도 2026 \
           --대상 042660 --세율 0.264

명단 파일은 [{"종목코드": ..., "고유번호": ...}, ...] 꼴이면 된다(N차통과.json).
**대상회사의 시세·종가는 함께 받는다**(시세는 이 갈래의 소유 — 소유 배선).
산출 파일명은 기존 도구·조립기의 규약 그대로다: sise_{코드}_week_{부터}_{까지}.json ·
주식수.csv · 전체재무_추출.csv · 종가_{기준일}.json — `peer_조립.py` 가 바로 읽는다.

경로 ①(산업분류 스크린)은 이 사슬 밖이다 — `상장명부.py`(KIND 1콜)를 먼저 쓴다(HWO-50).

**시장지수 — 본값은 넓은 시장 지수(KOSPI)다(2026-10-17, S7-05 · 기본 `--지수 넓은`).** 비싼 차선이 KOSPI · KOSDAQ 주봉을
둘 다 받고, 조립기가 전원을 KOSPI 로 회귀해 본값을 내며 KOSDAQ 상장 회사는 상장시장 지수 회귀를 대안 사양으로 병기한다.
**창 평균 D/E(S7-06, 기본 `--창평균 예`)** — 비싼 층이 회귀 창 안 사업보고서(기준연 − 창년 ~ 기준연 − 1, 11011)도 받아
`전체재무_추출.csv` 에 병합한다(캐시가 있으면 네트워크 0). 조립기가 그 기말들로 D/E · 현금 평균을 낸다.
아래는 옛 기본(`--지수 자동`)의 설명이다.
**(옛 기본) 시장지수는 회사마다 상장시장을 따른다(2026-09-13 · 펄29 · `peer_조립.py` 와 같은 규약).**
옛 판은 `--지수 KOSPI` 기본으로 **지수 주봉을 하나만** 받고 조립기에 그 지수를 넘겨, KOSDAQ 회사가
섞인 표본(펄어비스 회차: 핵심 전원 KOSDAQ · 넓은 표본 5곳 유가)이 한 지수로 회귀됐다.
  · `--지수 자동`: 비싼 차선이 **KOSPI·KOSDAQ 주봉을 둘 다** 받고, 조립기에 `--지수 자동` 을 넘긴다
    — 조립기가 회사마다 상장시장(명단 「시장」 → 기업개황 corp_cls → 산업분류 → KIND)으로 고른다
  · `--지수 KOSPI|KOSDAQ` 는 옛 동작(전원 고정) — 조립기가 상장시장과 다른 회사를 경보로 센다
  · 조립 산출은 표본마다 갈린다 — `--표본`(기본: 명단 파일 이름)을 조립기에 넘긴다
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import requests

sys.stdout.reconfigure(encoding="utf-8")
여기 = os.path.dirname(os.path.abspath(__file__))
# 2026-10-25 FX4-P — `--폴더`(또는 DCF_RUN_ROOT) 면 그 회차가 뿌리 — 본체 경로로 돌려도 하위 도구까지 회차 _raw 에 쓴다(C2 다시 셈 2조)
ROOT = os.environ.get("DCF_RUN_ROOT") or os.path.dirname(여기)
PEER = os.path.join(ROOT, "_raw", "peers")      # 폴더는 main 에서 본체 판정 뒤에 만든다(S1 리뷰)
SISE = "https://api.finance.naver.com/siseJson.naver"
HF = {"User-Agent": "Mozilla/5.0"}


_전용키 = ("운영동종전용", "운영동종_전용", "운영 동종 전용", "운영전용")


def 명단경로(a):
    # 2026-10-24 W16 — 피어경로 한 규칙(절대 · 작업 폴더 기준 「_raw/peers/x.json」 · 이름만)
    import 피어경로 as _pp
    return _pp.명단경로(a.명단, PEER, ROOT)


def 명단원본(a, 단계="비싼"):
    """(회사 목록, 핵심표본 꼴이었나). 핵심표본.json 이면 묶음을 편다 — 중간 층(CP1)은 컷 통과 전체까지,
    비싼 층은 핵심 · 예비 · 운영 동종 전용. 모르는 칸(`보강[]` · `B1도착` …)은 읽고 버리지 않는다(여기서 쓰지 않을 뿐)."""
    import 핵심표본읽기 as _hr
    j = _hr.목록꼴(json.load(io.open(명단경로(a), encoding="utf-8")))
    if isinstance(j, list):
        return [x for x in j if isinstance(x, dict)], False
    # 2026-10-24 W17 — 문자열 줄(해외 티커 — 국내 사슬의 몫 아님)에서 AttributeError 로 멈추던 결함(기아 조사)과,
    # 같은 회사가 예비(위험 동종)와 운영동종전용에 함께 있으면 운영 동종 전용으로만 읽히던 결함(META 조사와 같은 뿌리)을 고친다 —
    # 핵심 · 예비 · 행을 먼저, 운영동종전용을 뒤에 펴고 겹치면 위험 동종 줄에 `겸운영` 을 단다. 종목코드 없는 줄(해외)은 뺀다
    묶음 = [(x, False) for x in list(j.get("핵심") or []) + list(j.get("예비") or []) + list(j.get("행") or [])]
    for k in _전용키:
        묶음 += [(x, True) for x in (j.get(k) or [])]
    if 단계 == "중간":
        묶음 += [(x, False) for x in (j.get("컷통과_전체") or j.get("컷통과전체") or [])]
    본, out = {}, []
    for x, 전용 in 묶음:
        if not isinstance(x, dict):
            continue
        c = str(x.get("종목코드") or "").strip()
        if not c.isdigit():
            continue
        c = c.zfill(6)
        if c in 본:
            if 전용 and not 본[c].get("_전용줄"):
                본[c]["겸운영"] = True
            continue
        x = dict(x, _전용줄=True) if 전용 else dict(x)
        본[c] = x
        out.append(x)
    return out, True


def 운영전용(x):
    """`목적` 을 선언했는데 「위험동종」이 없다 — βU 를 안 세우니 시세 · 주식수 · 종가가 필요 없다."""
    v = x.get("목적")
    if x.get("겸운영"):                      # 2026-10-24 W17 — 위험 동종이면서 운영 동종 전용에도 있는 회사
        return False
    if v is None:
        return bool(x.get("_전용줄"))
    if isinstance(v, str):
        v = re.split(r"[,·/|]", v)
    return "위험동종" not in [str(s).replace(" ", "") for s in v]


def 명단읽기(a, 목록=None):
    목록 = 목록 if 목록 is not None else 명단원본(a)[0]
    쌍 = [(str(x.get("종목코드") or "").zfill(6), str(x.get("고유번호") or ""))
         for x in 목록 if x.get("종목코드")]
    return [x for x in 쌍 if x[0] != "000000"]


def 사슬명단(a, 목록, 핵심표본꼴):
    """하위 도구에 넘길 명단 이름 — 거른 것이 없고 목록 꼴이면 원래 이름, 아니면 위험 동종만 담은 임시 목록."""
    위험 = [x for x in 목록 if not 운영전용(x)]
    if not 핵심표본꼴 and len(위험) == len(목록):
        return 명단경로(a)                              # 2026-10-24 W16 — 하위 도구가 PEER 에 겹쳐 붙이지 않게 절대 경로로(유니버스 조사 물결 실측)
    이름 = "_사슬명단_%s.json" % (a.표본 or os.path.splitext(os.path.basename(a.명단))[0])
    json.dump(위험, io.open(os.path.join(PEER, 이름), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 이름


def 돌림(이름, 인자, 필수=True):
    t0 = time.time()
    r = subprocess.run([sys.executable, os.path.join(여기, 이름)] + 인자,
                       capture_output=True, text=True, encoding="utf-8",
                       env=dict(os.environ, PYTHONIOENCODING="utf-8", DCF_RUN_ROOT=ROOT), cwd=ROOT)
    print("  %s %-24s %5.1f초" % ("OK " if r.returncode == 0 else "실패", 이름, time.time() - t0))
    if r.returncode != 0:
        print((r.stdout or "")[-800:])
        print((r.stderr or "")[-800:])
        if 필수:
            sys.exit("사슬 중단 — %s 가 실패했습니다." % 이름)
    return r


def 시세한벌(code, 부터, 까지, tf):
    """siseJson 기간 창구 — 회차 규약 그대로 sise_{code}_{tf}_{부터}_{까지}.json 에 캐시."""
    key = "%s_%s_%s_%s" % (code, tf, 부터, 까지)
    p = os.path.join(PEER, "sise_%s.json" % key)
    if os.path.exists(p):
        return "캐시"
    url = "%s?symbol=%s&requestType=1&startTime=%s&endTime=%s&timeframe=%s" % (SISE, code, 부터, 까지, tf)
    for a in range(3):
        try:
            r = requests.get(url, headers=HF, timeout=40)
            if r.status_code == 200 and "날짜" in r.text:
                rows = [(m.group(1), float(m.group(2))) for m in re.finditer(
                    r'\["(\d{8})",\s*[\d.]+,\s*[\d.]+,\s*[\d.]+,\s*([\d.]+)', r.text)]
                vols = [(m.group(1), float(m.group(2)), float(m.group(3))) for m in re.finditer(
                    r'\["(\d{8})",\s*[\d.]+,\s*[\d.]+,\s*[\d.]+,\s*([\d.]+),\s*(\d+)', r.text)]
                if rows:
                    json.dump(rows, io.open(p, "w", encoding="utf-8"))
                    if tf == "day":
                        json.dump(vols, io.open(os.path.join(PEER, "vol_%s.json" % key), "w",
                                                encoding="utf-8"))
                    return "신규"
        except (requests.RequestException, ValueError):
            pass
        time.sleep(1.5 * (a + 1))
    return "실패"


def 받을지수(지수):
    """넓은 · 자동이면 둘 다 — 넓은(기본)은 KOSPI 로 본값을 내고 KOSDAQ 상장 회사의 상장시장 지수 회귀를 대안 사양으로 병기한다(S7-05).
    어느 회사가 어느 시장인지는 조립기가 캐시로 가른다(여기서 추측하지 않는다)."""
    return ["KOSPI", "KOSDAQ"] if 지수 in ("자동", "넓은") else [지수]


def 중간빠짐(a, 쌍):
    """위험 동종 (종목, 고유) 마다 종가_{기준일}.json 의 종가 · 주식수.csv 의 행이 있는지 — 없는 회사 이름 목록(2026-10-25 FX3-b).
    **옛 산출이 있는데 새 회사가 빠진 경우**만 잡는다 — 파일 자체가 없으면 조립기가 스스로 멈추므로 여기서는 비워 둔다."""
    p = os.path.join(PEER, "종가_%s.json" % a.기준일)
    if not os.path.exists(p):
        return []
    try:
        종가 = json.load(io.open(p, encoding="utf-8"))
    except (OSError, ValueError):
        return []
    주식 = None
    q = os.path.join(ROOT, "주식수.csv")
    if os.path.exists(q):
        import csv as _csv                                      # noqa: PLC0415
        주식 = {str(r.get("고유번호") or "").zfill(8) for r in _csv.DictReader(io.open(q, encoding="utf-8-sig"))}
    빠진 = []
    for 종, 고 in 쌍:
        없 = [x for x, ok in (("종가", 종 in 종가), ("주식수", 주식 is None or (not 고) or str(고).zfill(8) in 주식)) if not ok]
        if 없:
            빠진.append("%s(%s 없음)" % (종, " · ".join(없)))
    return 빠진


def 조립인자(a, 후보=None):
    인자 = ["--기준일", a.기준일, "--대상", a.대상, "--세율", a.세율, "--지수", a.지수, "--후보", 후보 or a.명단,
          "--창년", str(a.창년)]
    if a.부터:
        인자 += ["--부터", a.부터]
    표본 = a.표본 or (os.path.splitext(os.path.basename(a.명단))[0] if 후보 and 후보 != a.명단 else None)
    if 표본:
        인자 += ["--표본", 표본]
    if a.핵심표본:
        인자 += ["--핵심표본", a.핵심표본]
    if getattr(a, "부채스프레드", None):
        인자 += ["--부채스프레드", str(a.부채스프레드)]
    return 인자


def main():
    global ROOT, PEER
    if "--폴더" in sys.argv:                                 # 2026-10-25 FX4-P — 본체 판정 전에 뿌리를 정한다
        i = sys.argv.index("--폴더")
        if i + 1 < len(sys.argv):
            ROOT = os.path.abspath(sys.argv[i + 1])
            PEER = os.path.join(ROOT, "_raw", "peers")
            os.environ["DCF_RUN_ROOT"] = ROOT
    try:
        import 본체가드                                      # noqa: PLC0415
        본체가드.본체면멈춘다(ROOT)
    except ImportError:                                     # 도구 하나만 복사해 쓰는 자리(시험) — 본체가 아니다
        pass
    os.makedirs(PEER, exist_ok=True)
    ap = argparse.ArgumentParser(allow_abbrev=False, description="국내 유사기업 수집 사슬 — DART·naver 두 차선 병렬")
    ap.add_argument("--폴더", default=None, help="회차 키트 폴더(본체 경로로 돌릴 때 — 하위 도구에도 넘긴다 · 2026-10-25)")
    ap.add_argument("--단계", required=True, choices=["중간", "비싼", "운영", "전부"],
                    help="운영 = peer_운영지표.py(운영 동종의 운영 지표 · CP2b). 전부 = 중간 → 비싼 → 운영")
    ap.add_argument("--명단", required=True)
    ap.add_argument("--기준일", required=True, help="YYYYMMDD")
    ap.add_argument("--년도", required=True, help="주식수·재무 사업연도 (예: 2026)")
    ap.add_argument("--보고서", default="11012", help="11011 사업 / 11012 반기 / 11013·11014 분기")
    ap.add_argument("--대상", default=None,
                    help="대상회사 — 시세·종가에는 종목코드만, 조립에는 「종목,고유번호,이름」 셋을 쓴다")
    ap.add_argument("--세율", default=None, help="조립기 βU 참고값의 한계세율 — 조립을 돌리려면 필수(HWO-26)")
    ap.add_argument("--지수", default="넓은", choices=["넓은", "자동", "KOSPI", "KOSDAQ"],
                    help="넓은(기본 — S7-05): KOSPI·KOSDAQ 둘 다 받고 조립기가 전원 KOSPI 로 본값 · 상장시장 지수는 대안 사양. "
                         "자동: 조립기가 회사별 상장시장으로 고른다(옛 기본)")
    ap.add_argument("--창평균", default="예", choices=["예", "아니오"],
                    help="비싼 층에서 회귀 창 안 사업보고서(11011, 기준연−창년 ~ 기준연−1)도 받는다 — 조립기가 D/E · 현금을 창 평균으로 낸다(S7-06)")
    ap.add_argument("--부채스프레드", default=None, help="조립기에 넘김 — D/E ≥ 2 회사의 부채베타 스프레드")
    ap.add_argument("--표본", default=None, help="조립 산출 이름 꼬리(기본: 명단 파일 이름)")
    ap.add_argument("--핵심표본", default=None, help="조립기에 넘길 C1 핵심표본 JSON(핵심/예비 구분)")
    ap.add_argument("--창년", type=int, default=5,
                    help="회귀 창 해 수(기본 5 — 주간). 시세 창 시작 = 기준일 − 창년. 조립기에도 넘긴다")
    ap.add_argument("--부터", default=None,
                    help="시세 창 시작일 YYYYMMDD (기본 기준일−창년). 회차 간 βL 을 견주려면 같은 값을 쓴다")
    ap.add_argument("--조립", action="store_true", help="비싼 층 뒤에 peer_조립.py 까지 돌린다")
    ap.add_argument("--운영표본", default="운영_국내",
                    help="운영 단계 산출 이름 꼬리(운영지표_{운영표본}.json) — 기본 운영_국내(2026-10-24 W17 · 미국 사슬은 운영_해외 — 같은 꼬리로 서로 덮었다)")
    ap.add_argument("--운영창", default="6", help="운영 단계 관측창 해 수(peer_운영지표 --창) — 기본 6: 대상 앵커(최소 여섯 해 · "
                                                "한 사이클)와 같은 자로 잰다(2026-10-16, S1 리뷰 — 종전 3해는 사이클 한쪽만 담았다)")
    a = ap.parse_args()
    # 2026-10-25 FX3-b — `--대상` 을 종목코드 한 칸만 주면 중간 단계가 대상 주식수 · 기업개황 · 재무를 안 받아 조립의 대상 자체 βU 가
    # 「시가총액 없음」 으로 빠졌다(C1 다시 돌리기 3 · 4조 실측). 고유번호 · 이름을 캐시로 풀어 셋으로 만든다 — 못 풀면 알린다
    if a.대상 and a.대상.count(",") < 2:
        try:
            import peer_조립 as _pj                               # noqa: PLC0415
            _조각 = [x.strip() for x in a.대상.split(",")] + ["", ""]
            _고, _이, _근 = _pj.대상풀기(_조각[0], _조각[1], _조각[2])
        except Exception as e:                                  # noqa: BLE001
            _고, _이, _근 = "", "", "풀기 실패(%s)" % type(e).__name__
        if _고 and _이:
            a.대상 = "%s,%s,%s" % (a.대상.split(",")[0].strip(), _고, _이)
            print("[대상] 한 칸 → %s (%s)" % (a.대상, _근))
        else:
            print("※ [대상] %s — 고유번호 · 이름을 못 풀었다(%s). 대상 자체 βU(세 겹 ③)가 빠진다 — `--대상 종목,고유번호,이름` 셋을 주십시오"
                  % (a.대상, _근))
    중간목록, 꼴 = 명단원본(a, "중간")
    비싼목록, _ = 명단원본(a, "비싼")
    # 고유번호가 빈 회사는 corpCode 로 스스로 푼다(2026-10-16, S1 리뷰 — 종전에는 조용히 뺐다). 못 푼 곳은 이름 대어 알린다
    빈 = sorted({str(x.get("종목코드")).zfill(6) for x in 중간목록 + 비싼목록 if x.get("종목코드") and not x.get("고유번호")})
    if 빈:
        try:
            import dart_fetch                                       # noqa: PLC0415
            풀린 = dart_fetch.고유번호풀기(빈, os.path.join(ROOT, "_dartcache"))
        except Exception:                                           # noqa: BLE001
            풀린 = {}
        for x in 중간목록 + 비싼목록:
            if x.get("종목코드") and not x.get("고유번호"):
                x["고유번호"] = 풀린.get(str(x["종목코드"]).zfill(6), "")
        print("  고유번호 빈 곳 %d — corpCode 로 %d곳 풀었다%s" % (len(빈), len(풀린), (" · 못 푼 곳(빠진다): %s" % ", ".join(
            c for c in 빈 if c not in 풀린)) if len(풀린) < len(빈) else ""))
    전용 = [x for x in 비싼목록 if 운영전용(x)]
    쌍 = 명단읽기(a, 비싼목록)                                   # 전체 재무제표는 운영 동종 전용도 받는다
    위험쌍 = 명단읽기(a, [x for x in 비싼목록 if not 운영전용(x)])
    중간고유 = [g for _, g in 명단읽기(a, [x for x in 중간목록 if not 운영전용(x)]) if g]
    종목들 = [c for c, _ in 위험쌍]
    고유들 = [g for _, g in 쌍 if g]
    위험고유 = [g for _, g in 위험쌍 if g]
    대상종목 = (a.대상 or "").split(",")[0].strip()
    # 2026-10-25 C1 규모 — 상장 대상의 자기 회귀 βU(점검값 · 세 겹 ③)를 조립기가 세우려면 대상의 주식수 · 재무가 필요하다.
    # `--대상 종목,고유번호,이름` 이면 대상 고유번호를 DART 차선(주식수 · 전체 재무 · 창 안 사업보고서)에 함께 싣는다
    대상고유 = (((a.대상 or "").split(",") + ["", ""])[1]).strip()
    if 대상고유:
        for 목 in (중간고유, 고유들, 위험고유):
            if 대상고유 not in 목:
                목.append(대상고유)
    시세종목 = 종목들 + ([대상종목] if 대상종목 and 대상종목 not in 종목들 else [])
    y = int(a.기준일[:4])
    부터 = a.부터 or "%04d%s" % (y - a.창년, a.기준일[4:])
    print("사슬 %s — %d곳 · 기준일 %s · 창 %s~%s (%s)" % (a.단계, len(쌍), a.기준일, 부터, a.기준일,
                                                  "--부터 지정" if a.부터 else "%d년 주간" % a.창년))
    if 전용:
        print("  운영 동종 전용 %d곳 — 시세 · 주식수 · 종가를 받지 않고 재무만: %s"
              % (len(전용), ", ".join(str(x.get("회사명") or x.get("이름") or x.get("종목코드")) for x in 전용)))
    전체t0 = time.time()

    def 중간():
        종가명단 = 사슬명단(a, 중간목록, 꼴)
        with ThreadPoolExecutor(2) as ex:
            A = ex.submit(lambda: (돌림("dart_induty.py", ["--codes", ",".join(중간고유)], False),
                                   돌림("dart_shares.py", ["--codes", ",".join(중간고유),
                                                          "--year", a.년도, "--reprt", a.보고서])))
            B = ex.submit(돌림, "peer_기준일종가_국내.py",
                          ["--기준일", a.기준일, "--명단", 종가명단, "--추가", 대상종목], False)
            A.result(); B.result()

    def 운영():
        기준 = "%s-%s-%s" % (a.기준일[:4], a.기준일[4:6], a.기준일[6:8]) if "-" not in a.기준일 else a.기준일
        # 2026-10-24 W16 — 핵심표본이면 운영 동종(운영동종전용 + 목적에 「운영」)만 · 국내만. 종전에는 컷 통과 전체를 돌아 DART 호출이 늘었다(유니버스 조사 물결 실측)
        운명 = 명단경로(a)
        try:
            원 = json.load(io.open(운명, encoding="utf-8"))
        except (OSError, ValueError):
            원 = None
        if isinstance(원, dict) and any(k in 원 for k in ("핵심", "예비") + _전용키):
            import 핵심표본읽기 as _hr
            운 = _hr.운영명단(원, "KR")
            운명 = os.path.join(PEER, "_운영명단_%s.json" % a.운영표본)
            json.dump(운, io.open(운명, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print("  운영 동종(국내) %d곳: %s" % (len(운), ", ".join(str(x.get("회사명") or x.get("종목코드")) for x in 운)))
        r = 돌림("peer_운영지표.py", ["--명단", 운명, "--기준일", 기준, "--표본", a.운영표본,
                                    "--창", str(a.운영창), "--뿌리", ROOT], False)
        print("\n".join((r.stdout or "").splitlines()[-12:]))

    def 비싼():
        def naver차선():
            t0 = time.time()
            결과 = {"신규": 0, "캐시": 0, "실패": []}
            for c in 시세종목:
                r = 시세한벌(c, 부터, a.기준일, "week")
                if r == "실패":
                    결과["실패"].append(c)
                else:
                    결과[r] = 결과.get(r, 0) + 1
                시세한벌(c, "%04d%s" % (y - 1, a.기준일[4:]), a.기준일, "day")
                time.sleep(0.3)
            지수들 = 받을지수(a.지수)
            지수결과 = {j: 시세한벌(j, 부터, a.기준일, "week") for j in 지수들}
            print("  OK  naver 시세 %d곳(신규 %s·캐시 %s) %5.1f초 · 실패 %s · 지수 %s"
                  % (len(시세종목), 결과.get("신규", 0), 결과.get("캐시", 0),
                     time.time() - t0, 결과["실패"] or "없음",
                     " · ".join("%s %s" % kv for kv in 지수결과.items())))
            빠진 = [j for j, r in 지수결과.items() if r == "실패"]
            if 빠진:
                print("  ※ 지수 주봉을 못 받았습니다: %s — 그 시장 회사는 조립기가 회귀하지 않고 적습니다" % ",".join(빠진))

        def 재무차선():
            돌림("dart_fs_all.py", ["--codes", ",".join(고유들), "--year", a.년도, "--reprt", a.보고서])
            if a.창평균 == "예":
                # 회귀 창 기말 점(S7-06) — 창 안 사업보고서. 병합판이라 앞 행이 남는다(dart_fs_all 머리말). 캐시가 있으면 네트워크 0
                for yy in range(y - a.창년, y):
                    돌림("dart_fs_all.py", ["--codes", ",".join(위험고유), "--year", str(yy), "--reprt", "11011"], False)

        with ThreadPoolExecutor(2) as ex:
            A = ex.submit(재무차선)
            B = ex.submit(naver차선)
            A.result(); B.result()
        if a.조립:
            if not a.대상 or a.대상.count(",") != 2 or not a.세율:
                sys.exit("조립에는 --대상 「종목,고유번호,이름」 셋과 --세율이 필요합니다 — "
                        "세율 기본값은 없습니다(HWO-26)")
            # 2026-10-25 FX3-b — 중간 단계(주식수 · 종가)가 멈췄는데 비싼 단계가 옛 사슬명단 · 옛 주식수로 조용히 돌아 새 핵심을 빼고 표를 냈다
            # (C1 다시 돌리기 2조 실측). 위험 동종마다 종가 · 주식수가 있는지 대조해 빠진 회사가 있으면 멈춘다
            빠진 = 중간빠짐(a, 위험쌍)
            if 빠진:
                sys.exit("중간 단계 산출(종가 · 주식수)이 없는 위험 동종 %d곳 — %s. `--단계 중간` 을 먼저(또는 다시) 돌리십시오 — "
                         "옛 명단 · 옛 주식수로 조립하지 않습니다" % (len(빠진), ", ".join(빠진[:8])))
            돌림("peer_조립.py", 조립인자(a, 사슬명단(a, 비싼목록, 꼴)))

    if a.단계 in ("중간", "전부"):
        중간()
    if a.단계 in ("비싼", "전부"):
        비싼()
    if a.단계 in ("운영", "전부"):
        운영()
    print("사슬 완료 — %.0f초" % (time.time() - 전체t0))


if __name__ == "__main__":
    main()

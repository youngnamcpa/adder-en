# -*- coding: utf-8 -*-
"""미국 유사기업 재료 수집 사슬 (HWO-55) — 건별 직렬 루프를 죽인다.

**병목 실측(TSLA 50분 · MSFT 21분):** 도구는 본체에 다 있는데 그 사이의 글루를
에이전트가 한 건씩 도구 호출로 이었다 — 시세 25건이 20분에 걸쳐 뚝뚝 떨어졌다.
SEC 는 DART(2스레드·0.5초)와 달리 **10요청/초**까지 허용한다(User-Agent 필수).

**처방:** 층별로 묶어 한 번에 돌리고, 창구가 다른 두 차선을 병렬로 겹친다.
  차선 A (SEC data.sec.gov) : frames → meta → concept 보충 → shares → ads·표지 → 차입금
  차선 B (시세·환율 창구)    : 기준일 종가 → 회귀 창 주봉(Yahoo · `--창년` 기본 5년) → 환율
두 차선은 창구가 달라 서로의 요율을 안 먹는다. 차선 안은 순서를 지킨다.

**단계와 갈래 (2026-09-13 개정 · 세일즈포스 회차 세14)**

    C1  --단계 싼층     frames 전수 · meta · concept 보충 · 외화개념     ← **종가를 받지 않는다**
    C1  --단계 후보표   frames 결합 + 매출 규모대 판정(캐시만, 네트워크 0) → 후보표_{표본}.json
    C1  --단계 사업발췌 핵심 후보의 최신 10-K Item 1 / 20-F Item 4 발췌(SEC 원문, 캐시) → item1_{T}.json
    C2  --단계 중간     주식수 · ADS · 표지 · **기준일 종가** · 환율      (CP1)
    C2  --단계 비싼     차입금 · 창년(기본 5년) 주봉 · 조립(+ --세율 이면 βU·현금보정)   (CP2 / CP3)
    C2  --단계 운영     운영 동종의 운영 지표(peer_운영지표.py --미국) → 운영지표_{운영표본}.json   (CP2b)

**회귀 창 기본 5년 주간(2026-10-16 결정).** `--창년`(기본 5)을 `sec_주봉.py` 와 `peer_조립_us.py`
에 넘긴다. 조립기는 기준일 − 창년 앞의 주를 잘라 더 긴 캐시가 창을 늘리지 않게 하고 실제 주 수를 적는다.

**운영 동종 전용 회사(2026-10-16 · 결정 5).** 명단의 `목적` 에 「위험동종」이 없는 회사는 βU 를 세우지 않는다 —
중간 · 비싼 단계가 주식수 · 종가 · 주봉 · 차입금 · 조립에서 빼고(재무는 `운영` 단계가 companyfacts 로 받는다),
그 사실을 화면에 적는다. 명단은 목록이든 C1 `핵심표본.json`(핵심 · 예비 · 운영 동종 전용 · 컷통과전체)이든 된다.

  - 옛 판 `싼층` 은 기준일 종가(중간 층)까지 받아 **C1 이 사슬을 못 썼다**(유사기업-선정 스킬:
    C1 은 싼 층만). 그래서 C1 이 frames 결합·규모대 판정·사업 서술 발췌를 손으로 조립했다
    (증거 `_c1_frames_join.json`·`_c1_item1.json`·`_c1_view.txt`). 그 셋이 `후보표`·`사업발췌` 다.
  - 산출 이름은 **표본마다 갈린다** — `--표본`(기본: 명단 파일 이름). 옛 판은 넓은 표본 조립이
    `유사기업_재료.csv`·`2차통과.json`·`2차탈락.json` 을 덮었다.
  - `--넓은표본` (CP3): 「규모대에서 이미 자른 회사의 companyfacts 를 새로 받지 않는다」를
    도구로 지킨다 — 차입금 단계가 **companyfacts 캐시가 있는 회사만** 돌고, 없는 회사는
    「넓은 표본 · companyfacts 미수집」으로 적는다(주봉은 받는다 — βL 은 시세만으로 선다).
  - **`--캐시` 는 하위 도구에도 닿는다**(2026-10-18 손개입 개선 1) — 사슬이 `DCF_PEER_CACHE` 환경변수로 넘기고 `sec_frames` · `sec_peer_meta` · `sec_concept` ·
    `sec_외화개념` · `sec_shares_us` · `sec_표지주식수` · `sec_ads비율` · `peer_차입금` · `peer_조립_us` · `sec_주봉` 이 기본 자리 대신 그것을 쓴다.
    실측(C1 ⑤ 실측): 사슬만 `--캐시` 를 알아 frames · cc_* 가 키트 `_raw/peers/` 에 쓰였고 후보표가 「frames 캐시가 없습니다」로 멈췄다.
  - `sec_concept.py --병렬`(기본 8) — 회사마다 창구를 나란히(SEC 10요청/초 안 — 공용 간격 0.11초). 실측: 60곳 직렬 40분 → 몇 분.
  - 주봉 캐시가 다른 기준일의 창이면(다른 회차 `wk__INX` 잔재 실측) `sec_주봉.py` 가 스스로 다시 받는다.
    `sec_shares_us.py` 는 명단에 cik 가 없어도 sub 메타·company_tickers 로 찾는다(둘 다 2026-09-13 도구 쪽 수리 —
    사슬의 임시 명단·`--새로` 우회는 걷어냈다).

    python 스크립트/sec_peer_사슬.py --단계 싼층 --명단 후보_전체.json --기준일 2026-06-30
    python 스크립트/sec_peer_사슬.py --단계 후보표 --명단 후보_전체.json --기준일 2026-06-30 \\
           --대상 TSLA --밴드배수 5
    python 스크립트/sec_peer_사슬.py --단계 사업발췌 --tickers ORCL,ADBE,NOW --기준일 2026-06-30
      → (1차 컷: 선언 기준으로 자르고 1차통과.json 을 쓴다 — 컷은 사슬의 소유가 아니다)
    python 스크립트/sec_peer_사슬.py --단계 중간 --명단 1차통과.json --기준일 2026-06-30
    python 스크립트/sec_peer_screen.py --명단 1차통과.json --기준일 2026-06-30 \\
           --대상 TSLA --대상주식수 3225000000 --밴드배수 5
    python 스크립트/sec_peer_사슬.py --단계 비싼 --명단 2차통과_명단.json --기준일 2026-06-30 \\
           --대상 TSLA --대상주식수 3225000000 --세율 0.21 --스크린 2차스크린.json --표본 핵심예비
    python 스크립트/sec_peer_사슬.py --단계 비싼 --명단 넓은_명단.json ... --표본 넓은 --넓은표본

명단 파일은 [{"티커": ...}, ...] 꼴(또는 {"행": [...]})이면 무엇이든 좋다. `--tickers AAA,BBB` 도 된다.

각 도구는 저마다 캐시하므로 사슬 재실행은 캐시 확인 비용뿐이다. 실패한 단계는
그 단계 이름과 출력 꼬리를 남기고 사슬을 멈춘다 — 조용히 건너뛰지 않는다.
"""
from __future__ import annotations

import argparse
import datetime as dt
import csv
import glob
import html as _html
import io
import json
import math
import os
import re
import subprocess
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 피어경로 as 피경  # noqa: E402 — 명단 경로 · 종가 파일 이름 한 규칙(2026-10-24 W15)
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)   # 2026-10-24 W17 — 파일로 돌려도 진행이 보이게(AVGO 조사 — 끝까지 버퍼링)
여기 = os.path.dirname(os.path.abspath(__file__))
# 2026-10-25 FX4-P — DCF_RUN_ROOT(사슬 `--폴더` 가 넘긴다)면 그 회차에 쓴다 — 본체 경로로 돌려도 본체 _raw 에 쌓지 않게
ROOT = os.environ.get("DCF_RUN_ROOT") or os.path.dirname(여기)
PEER = os.path.join(ROOT, "_raw", "peers")


_전용키 = ("운영동종전용", "운영동종_전용", "운영 동종 전용", "운영전용")


def _티커정규(x):
    """행 하나 → 「티커」 칸이 있는 행. `ticker` · `Ticker` · `TICKER` 별칭을 받는다(유니버스 조사 물결 실측)."""
    if not isinstance(x, dict) or x.get("티커"):
        return x
    for k in ("ticker", "Ticker", "TICKER", "symbol"):
        if x.get(k):
            return dict(x, 티커=("%s" % x[k]).strip())
    if isinstance(x.get("tickers"), list) and x["tickers"]:      # sec_sic_screen 의 `sic_*_listed.json` 꼴({cik, name, tickers[]})
        return dict(x, 티커=("%s" % x["tickers"][0]).strip())
    return x


def 명단읽기(p):
    """목록 · {"행"} · C1 핵심표본(핵심 · 예비 · 운영 동종 전용 · 컷통과전체). 모르는 칸은 버리지 않고 쓰지 않을 뿐이다.
    국내 회사(종목코드만 있고 티커가 없는 줄 · 시장 KR)는 미국 사슬의 몫이 아니라 뺀다(2026-10-24 W16 — 「cik 없음」 줄이 섞이던 결함).
    읽은 줄이 0곳인데 파일이 비지 않았으면 받는 꼴을 알리고 멈춘다(경고 없이 0곳으로 끝나지 않게)."""
    낸 = _명단읽기(p)
    import 핵심표본읽기 as _hr
    남 = [x for x in 낸 if not (isinstance(x, dict) and (_hr.시장(x) == "KR" or (x.get("종목코드") and not x.get("티커"))))]
    if len(남) < len(낸):
        print("  국내 회사 %d곳은 미국 사슬에서 뺌(국내 사슬 `dart_peer_사슬` 의 몫)" % (len(낸) - len(남)))
    티없음 = [x for x in 남 if not (isinstance(x, dict) and x.get("티커"))]
    남 = [x for x in 남 if isinstance(x, dict) and x.get("티커")]
    if 티없음:
        print("  티커를 못 읽은 줄 %d곳 — 뺌(받는 칸: 티커 · ticker · Ticker · tickers[])" % len(티없음))
    if not 남:
        try:
            원 = json.load(io.open(p, encoding="utf-8"))
        except (OSError, ValueError):
            원 = None
        if 원 and (not 낸 or 티없음):
            sys.exit("명단에서 티커를 한 곳도 못 읽었다(%s) — 받는 꼴: [{\"티커\": …}] · [\"AAA\", …] · {\"행\": […]} · C1 핵심표본"
                     "(핵심 · 예비 · 운영동종전용 · 컷통과전체). 별칭 ticker · Ticker 도 받는다" % os.path.basename(p))
    return 남


def _명단읽기(p):
    import 핵심표본읽기 as _hr
    목록 = _hr.목록꼴(json.load(io.open(p, encoding="utf-8")))   # 2026-10-24 W17 — {"tickers": […]} · {"티커들": […]} 꼴도(W16 문서와 맞춤)
    문자열 = lambda xs: [_티커정규({"티커": x} if isinstance(x, str) else x) for x in (xs or [])]   # S7-19 — 옛 명단(티커 문자열 목록)도 읽는다
    if isinstance(목록, dict):
        for k in ("핵심", "예비", "행", "cands", "컷통과전체", "컷통과_전체") + _전용키:
            if isinstance(목록.get(k), list):
                목록[k] = 문자열(목록[k])
        if any(k in 목록 for k in ("핵심", "예비") + _전용키):
            # 2026-10-24 W17 — 핵심 · 예비(위험 동종)를 먼저 펴고 운영동종전용을 뒤에 — 같은 회사가 둘 다면 위험 동종 줄을 두고 `겸운영` 을 단다
            # (META 조사 — AMZN · MSFT 가 예비 + 운영 동종 전용이라 운영 동종 전용으로만 읽혀 βU 에서 빠졌다)
            묶음 = [(x, False) for x in (목록.get("핵심") or [])] + [(x, False) for x in (목록.get("예비") or [])]
            for k in _전용키:
                묶음 += [(x, True) for x in (목록.get(k) or [])]
            본, out = {}, []
            for x, 전용 in 묶음:
                t = (x.get("티커") or (x.get("tickers") or [""])[0] or "").upper()
                if not t:
                    continue
                if t in 본:
                    if 전용 and not 본[t].get("_전용줄"):
                        본[t]["겸운영"] = True
                    continue
                x = dict(x, _전용줄=True) if 전용 else dict(x)
                본[t] = x
                out.append(x)
            return out
        목록 = 목록.get("행") or 목록.get("cands") or 목록.get("컷통과전체") or 목록.get("컷통과_전체") or []
    return 문자열(목록)


def 운영전용(x):
    """`목적` 을 선언했는데 「위험동종」이 없다 — βU 를 안 세우니 주식수 · 종가 · 주봉 · 차입금이 필요 없다."""
    v = x.get("목적")
    if x.get("겸운영"):                      # 2026-10-24 W17 — 위험 동종이면서 운영 동종 전용에도 있는 회사
        return False
    if v is None:
        return bool(x.get("_전용줄"))        # 운영동종전용 묶음에서 온 줄은 목적을 안 적었어도 운영 동종 전용
    if isinstance(v, str):
        v = re.split(r"[,·/|]", v)
    return "위험동종" not in [str(s).replace(" ", "") for s in v]


def 명단경로(a):
    return 피경.명단경로(a.명단, PEER, ROOT)


def 티커들(a):
    if a.tickers:
        return [t.strip().upper() for t in a.tickers.split(",") if t.strip()]
    목록 = 명단읽기(명단경로(a))
    out = []
    for x in 목록:
        t = x.get("티커") or (x.get("tickers") or [None])[0]
        if t:
            out.append(t.upper())
    return out


def 전용티커들(a):
    if a.tickers:
        return set()
    return {(x.get("티커") or (x.get("tickers") or [""])[0] or "").upper()
            for x in 명단읽기(명단경로(a)) if 운영전용(x)}


def 돌림(이름, 인자, 필수=True):
    t0 = time.time()
    r = subprocess.run([sys.executable, os.path.join(여기, 이름)] + 인자,
                       capture_output=True, text=True, encoding="utf-8",
                       env=dict(os.environ, PYTHONIOENCODING="utf-8", DCF_PEER_CACHE=PEER), cwd=ROOT)   # --캐시 를 하위 도구에(손개입 개선 1)
    초 = time.time() - t0
    표 = "OK " if r.returncode == 0 else "실패"
    print("  %s %-22s %5.1f초" % (표, 이름, 초))
    if r.returncode != 0:
        print((r.stdout or "")[-800:])
        print((r.stderr or "")[-800:])
        if 필수:
            sys.exit("사슬 중단 — %s 가 실패했습니다. 위 출력을 보십시오." % 이름)
    return r


def _sub(t):
    p = os.path.join(PEER, "sub_%s.json" % t)
    return json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else None


def 외국큐(명단):
    """sub 메타에서 20-F/40-F 신고인을 가른다 — 메타가 없으면 큐에 넣고 사유를 적는다."""
    외국, 메타없음 = [], []
    for t in 명단:
        d = _sub(t)
        if d is None:
            메타없음.append(t)
            continue
        폼들 = set((d.get("최근서류") or {}).keys())
        if 폼들 & {"20-F", "40-F", "20-F/A", "40-F/A"}:
            외국.append(t)
    return 외국, 메타없음


def 보충대상(명단):
    """frames 매출 프레임에 안 잡힌 후보 — 자르기 전에 concept 로 한 번 더 두드릴 목록."""
    있는cik = set()
    for f in glob.glob(os.path.join(PEER, "frame_Revenue*_CY*.json")):
        if f.endswith("I.json"):
            continue
        try:
            d = json.load(io.open(f, encoding="utf-8"))
        except Exception:
            continue
        for x in d.get("data", []):
            있는cik.add(int(x.get("cik") or 0))
    빠짐 = []
    for t in 명단:
        d = _sub(t)
        cik = d.get("cik") if d else None
        if not cik or int(cik) not in 있는cik:
            빠짐.append(t)
    return 빠짐


def _자산색인():
    """frames 자산(시점) 가운데 가장 늦은 CY 의 {cik: 값} — 싼층 보충 대상을 규모로 먼저 거르는 재료."""
    낸 = {}
    for f in sorted(glob.glob(os.path.join(PEER, "frame_Assets_CY*Q4I.json"))):
        try:
            d = json.load(io.open(f, encoding="utf-8"))
        except Exception:                                    # noqa: BLE001
            continue
        for x in d.get("data", []):
            try:
                낸[int(x.get("cik") or 0)] = float(x.get("val"))
            except (TypeError, ValueError):
                pass
    return 낸


def _상장(d):
    """sub 메타의 거래소 — 미국 거래소(Nasdaq · NYSE · CBOE)에 상장돼 있나. 메타가 없으면 None(모름)."""
    if not d:
        return None
    e = "%s" % (d.get("exchanges") or "")
    return any(x in e for x in ("Nasdaq", "NYSE", "CBOE"))


def 우선길이(우선, 원):
    """규모 거름에서 남길 경로 ② · ④ 후보 — 경로 ② 가 낱말 일치가 아니라 업종(SIC) 목록이면(곳 수가 많다) ② 를 남기지 않고 ④ 만 남긴다
    (2026-10-24 W17 · AVGO 조사 — 부문 SIC 두 줄을 ② 로 붙여 402곳 전부가 우선이 되어 규모 거름이 0곳을 걸렀다)."""
    이 = [x for x in 원 if "②" in ("%s" % (x.get("경로") or ""))]
    if len(이) > 60 or (len(원) >= 40 and len(이) > len(원) / 2):
        남 = {(x.get("티커") or "").upper() for x in 원 if "④" in ("%s" % (x.get("경로") or ""))}
        print("  경보: 경로 ② 후보 %d곳(명단 %d곳 중) — 낱말 일치가 아니라 업종 목록으로 보인다. 규모 거름에서 ② 를 남기지 않는다(④ %d곳만) — "
              "SIC 목록은 경로 ① 로 붙인다" % (len(이), len(원), len(남)))
        return set(우선) & 남
    return set(우선)


def 메타전거르기(명단, 대상, 배수=10.0, 우선=(), 대자=None):
    """2026-10-24 W16 — meta(`sub_*.json`)를 받기 **전에** frames 자산으로 규모를 거른다. 큰 SIC(소프트웨어 7372 292곳 · 7370 95곳)에서 meta 를
    전수로 받은 뒤에야 걸러 C1 벽시계를 넘기던 결함(유니버스 조사 물결 실측). 규칙: frames 자산이 있고 대상 자산의 1/배수 ~ 배수 밖이면 meta 를 받지 않는다 —
    경로 ② · ④(낱말 · B1 거론) 후보와 frames 자산이 없는 후보는 남긴다(규모를 모르면 빼지 않는다). → (남김, [(티커, 까닭)])."""
    자산, 표 = _자산색인(), _cik표()
    if 대자 is None:
        대cik = 표.get((대상 or "").upper())
        대자 = 자산.get(대cik) if 대cik else None
    if not 대자:
        return list(명단), []
    남, 뺀 = [], []
    for t in 명단:
        v = 자산.get(표.get(t)) if 표.get(t) else None
        if t in 우선 or v is None or 대자 / 배수 <= v <= 대자 * 배수:
            남.append(t)
        else:
            뺀.append((t, "frames 자산 %.0f백만 — 대상 자산의 1/%.0f~%.0f배 밖(meta 전 거름)" % (v / 1e6, 배수, 배수)))
    return 남, 뺀


def 보충거르기(빠짐, 대상, 배수=10.0, 상한=40, 우선=(), 대형배수=None, 대자=None):
    """frames 매출이 없는 후보(concept · 외화개념 보충 대상)를 **규모로 먼저 거른다**(2026-10-24 W15 · 인텔 시범 — SIC 3674 전수 113곳에
    concept 238초 · 외화개념 331초를 돌려 C1 벽시계를 넘겼다). 규칙: frames 자산이 있으면 대상 자산의 1/배수 ~ 배수 안만 · 자산이 없으면 미국
    거래소 상장만(장외 · 비신고인 뺌) · 그래도 상한을 넘으면 앞에서 상한까지. → (남김, [(티커, 까닭)])."""
    자산 = _자산색인()
    if 대자 is None:
        d대 = _sub(대상) if 대상 else None
        대자 = 자산.get(int(d대["cik"])) if (d대 and d대.get("cik")) else None
    남, 뺀 = [], []
    # 2026-10-24 W16 — frames 자산이 없는 외국 · 소형 신고인(유니버스 조사 물결 실측)이 외화개념을 곳당 1분씩 돌던 자리: 대상이 크면(자산이
    # frames 자산 분포 상위 — `대형배수` 배 넘게 큰 회사가 드물면) 규모를 모르는 후보는 경로 ② · ④ 가 아니면 「규모 미확인」 으로 뺀다(남긴 것은 후보표가 적는다)
    # 2026-10-24 W17 — 순위 문턱(대상보다 1/대형배수 이상 큰 회사가 200곳 이하)만으로는 초대형 대상(META)에서도 은행 · 보험이 많아 「대형」 이 안 섰다 —
    # 절대 문턱(자산 200억 달러 이상)도 함께 본다
    대형 = bool(대자 and 대형배수 and (대자 >= 2e10 or sum(1 for v in 자산.values() if v and v >= 대자 / 대형배수) <= 200))
    for t in 빠짐:
        d = _sub(t)
        cik = int(d["cik"]) if (d and d.get("cik")) else None
        v = 자산.get(cik) if cik else None
        if t in 우선:
            남.append(t)
        elif v is not None and 대자:
            if 대자 / 배수 <= v <= 대자 * 배수:
                남.append(t)
            else:
                뺀.append((t, "자산 %.0f백만 — 대상 자산의 1/%.0f~%.0f배 밖" % (v / 1e6, 배수, 배수)))
        elif _상장(d) is False:
            뺀.append((t, "미국 거래소 상장 아님(장외 · 비신고인)"))
        elif v is None and 대형:
            뺀.append((t, "규모 미확인(frames 자산 없음) — 대상이 대형이라 보충 전 뺌(경로 ② · ④ 면 남김)"))
        else:
            남.append(t)
    if len(남) > 상한:
        뺀 += [(t, "보충 상한 %d 넘음" % 상한) for t in 남[상한:]]
        남 = 남[:상한]
    return 남, 뺀


# ────────────────────────── 후보표 (C1 — frames 결합 + 규모대 판정, 캐시만) ──────────────────────────
매출태그 = ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues",
         "RevenueFromContractWithCustomerIncludingAssessedTax")


def _프레임색인():
    """{(tag, CY): {cik: (val, end, entityName)}}"""
    색 = {}
    for f in glob.glob(os.path.join(PEER, "frame_*_CY*.json")):
        m = re.match(r"frame_(.+)_(CY\d{4}(?:Q4I)?)\.json$", os.path.basename(f))
        if not m:
            continue
        try:
            d = json.load(io.open(f, encoding="utf-8"))
        except Exception:
            continue
        색[(m.group(1), m.group(2))] = {int(x["cik"]): (x["val"], x.get("end"), x.get("entityName"))
                                      for x in d.get("data", [])}
    return 색


def _cik표():
    p = os.path.join(PEER, "company_tickers.json")
    if not os.path.exists(p):
        return {}
    m = json.load(io.open(p, encoding="utf-8"))
    rev = {}
    for cik, ts in m.items():
        for t in (ts if isinstance(ts, list) else [ts]):
            rev[str(t).upper()] = int(cik)
    return rev


def 국내대상매출(종목, 기준):
    """국내 대상의 USD 매출 — 공용 C1 캐시 상장사 주요계정(가장 늦은 해) 매출액(원) ÷ 기준일 USDKRW(환율_YYYYMMDD.json · 없으면 peer_환율.py 를 돌린다).
    → (값, 출처 글) · 못 세우면 (None, 까닭)."""
    뿌 = os.path.join(os.environ.get("DCF_공용캐시") or os.environ.get("DCF_SHARED_CACHE") or os.path.expanduser("~/.dcf캐시"), "C1")
    매출, 해 = None, None
    for p in sorted(glob.glob(os.path.join(뿌, "상장사_주요계정_*.csv")), reverse=True):
        try:
            for r in csv.DictReader(io.open(p, encoding="utf-8-sig")):
                if ("%s" % r.get("종목코드") or "").zfill(6) == 종목 and r.get("매출액"):
                    매출, 해 = float(r["매출액"]), re.search(r"(\d{4})", os.path.basename(p)).group(1)
                    break
        except (OSError, ValueError):
            continue
        if 매출:
            break
    if not 매출:
        return None, "국내 대상 %s 의 매출을 공용 C1 캐시에서 못 찾음 — --대상매출 로" % 종목
    fp = os.path.join(PEER, "환율_%s.json" % 기준.replace("-", ""))
    if not os.path.exists(fp):
        돌림("peer_환율.py", ["--기준일", 기준], False)
    try:
        fx = float(((json.load(io.open(fp, encoding="utf-8")).get("원화고시") or {}).get("FX_USDKRW") or {}).get("원화당"))
    except (OSError, ValueError, TypeError):
        return None, "기준일 USDKRW 환율을 못 읽음(%s) — --대상매출 로" % os.path.basename(fp)
    return 매출 / fx, "국내 대상 %s 매출 %.0f원(C1 캐시 %s) ÷ %.2f원/달러(%s)" % (종목, 매출, 해, fx, os.path.basename(fp))


def 국내대상자산(종목, 기준):
    """국내 대상의 USD 자산 — 공용 C1 캐시 상장사 주요계정(가장 늦은 해) 자산총계(원) ÷ 기준일 USDKRW. 싼층 규모 거르기의 대상 자산
    (2026-10-24 W17 — 국내 대상의 해외 경로 ⑤ 는 대상 자산을 못 세워 거르기가 안 걸리고 후보 28~60곳 전부에 보충을 돌렸다 · 기아 · LIG디펜스 조사).
    → (값 또는 None, 글)."""
    뿌 = os.path.join(os.environ.get("DCF_공용캐시") or os.environ.get("DCF_SHARED_CACHE") or os.path.expanduser("~/.dcf캐시"), "C1")
    자산, 해 = None, None
    for p in sorted(glob.glob(os.path.join(뿌, "상장사_주요계정_*.csv")), reverse=True):
        try:
            for r in csv.DictReader(io.open(p, encoding="utf-8-sig")):
                if ("%s" % r.get("종목코드") or "").zfill(6) == 종목 and r.get("자산총계"):
                    자산, 해 = float(r["자산총계"]), re.search(r"(\d{4})", os.path.basename(p)).group(1)
                    break
        except (OSError, ValueError, AttributeError):
            continue
        if 자산:
            break
    if not 자산:
        return None, "국내 대상 %s 의 자산을 공용 C1 캐시에서 못 찾음" % 종목
    fp = os.path.join(PEER, "환율_%s.json" % 기준.replace("-", ""))
    if not os.path.exists(fp):
        돌림("peer_환율.py", ["--기준일", 기준], False)
    try:
        fx = float(((json.load(io.open(fp, encoding="utf-8")).get("원화고시") or {}).get("FX_USDKRW") or {}).get("원화당"))
    except (OSError, ValueError, TypeError):
        return None, "기준일 USDKRW 환율을 못 읽음"
    return 자산 / fx, "국내 대상 %s 자산 %.0f원(C1 %s) ÷ %.2f" % (종목, 자산, 해, fx)


def 국내대상_(t):
    """`국내대상` 별칭 — 후보표 안에서 같은 이름의 지역 변수(bool)가 함수를 가린다."""
    return 국내대상(t)


def 국내대상(t):
    """「000270」 · 「000270.KS」 · 「000270.KQ」 → 6자리 종목코드, 아니면 None."""
    m = re.match(r"^(\d{6})(?:\.(?:KS|KQ))?$", ("%s" % (t or "")).strip().upper())
    return m.group(1) if m else None


def _환율계수(기준일):
    """환율 캐시(peer_환율.py — `환율_<기준일>.json`)의 「USD환산계수(1통화당 USD)」 → {통화: 계수}. 없으면 {}."""
    d8 = 기준일.replace("-", "")
    for 이름 in ("환율_%s.json" % d8, "환율_%s.json" % 기준일):
        p = os.path.join(PEER, 이름)
        if os.path.exists(p):
            try:
                return json.load(io.open(p, encoding="utf-8")).get("USD환산계수(1통화당 USD)") or {}
            except (OSError, ValueError):
                return {}
    return {}


def 후보표(a, 명단목록, 표본):
    색 = _프레임색인()
    if not 색:
        sys.exit("frames 캐시가 없습니다 — --단계 싼층 을 먼저 돌리십시오")
    cy들 = sorted({k[1] for k in 색 if not k[1].endswith("I")})
    cik표 = _cik표()
    기준 = a.기준일

    def 행만들기(t, x):
        sub = _sub(t)
        cik = (sub or {}).get("cik") or x.get("cik") or cik표.get(t)
        r = {"티커": t, "cik": cik, "회사명": (sub or {}).get("name") or x.get("회사명") or x.get("name"),
             "경로": x.get("경로"), "출처": None}
        if not cik:
            r["밴드"] = "확인 불가 — cik 없음(sec_peer_meta 미실행 또는 티커 없음)"
            return r
        cik = int(cik)
        # 매출이 잡힌 가장 최근 CY — 그 CY 안에서 세 태그 중 최댓값(태그가 회사마다 갈린다).
        # 기준일보다 두 해 넘게 이른 CY 는 쓰지 않는다(2026-10-23 — 외화로만 신고하는 20-F 회사가 옛날 한때의 USD 프레임(CY2013)으로 「통과」 했다)
        for cy in reversed(cy들):
            if int(cy[2:6]) < int(기준[:4]) - 2:
                break
            후 = [(색.get((tag, cy), {}).get(cik), tag) for tag in 매출태그]
            후 = [(v, tag) for v, tag in 후 if v]
            # 2026-10-24 W18 — 결산일이 기준일 뒤이거나 기준일 90일 안이면 그 연차 보고서는 기준일 뒤에 냈다(냈을 수 있다) — 한 해 앞 CY 로 간다
            # (frames 에는 제출일이 없다 · NBIS 조사 APLD 매출끝 2026-05-31 · 07 제출)
            if 후 and max(v[1] for v, _ in 후) > (dt.date.fromisoformat(기준) - dt.timedelta(days=90)).isoformat():
                r.setdefault("기준일뒤회피", []).append("%s 결산 %s — 기준일 90일 안 · 뒤라 제출이 기준일 뒤일 수 있어 한 해 앞 CY" % (cy, max(v[1] for v, _ in 후)))
                continue
            if 후:
                (val, end, 이름), tag = max(후, key=lambda z: z[0][0])
                r.update({"매출": val, "매출기간": cy, "매출끝": end, "매출태그": tag, "출처": "frames"})
                r["회사명"] = r["회사명"] or 이름
                for 키, tg in (("영업이익", "OperatingIncomeLoss"), ("순이익", "NetIncomeLoss")):
                    v = 색.get((tg, cy), {}).get(cik)
                    r[키] = v[0] if v else None
                for 키, tg in (("자산", "Assets"), ("부채", "Liabilities"), ("자본", "StockholdersEquity"),
                              ("현금", "CashAndCashEquivalentsAtCarryingValue")):
                    v = 색.get((tg, cy + "Q4I"), {}).get(cik)
                    r[키] = v[0] if v else None
                break
        if r.get("매출") is None:
            cc = os.path.join(PEER, "cc_%s.json" % t)
            if os.path.exists(cc):
                c = json.load(io.open(cc, encoding="utf-8")).get("값") or {}
                if c.get("매출") and (c["매출"].get("filed") or "") > 기준:
                    r["기준일뒤회피"] = (r.get("기준일뒤회피") or []) + ["concept 매출 %s — 기준일 뒤 제출(%s)이라 쓰지 않음" % (c["매출"]["end"], c["매출"]["filed"])]
                elif c.get("매출"):
                    r.update({"매출": c["매출"]["val"], "매출끝": c["매출"]["end"], "매출기간": "concept",
                              "출처": "concept(cc_)", "제출일": c["매출"].get("filed")})
                    for 키 in ("영업이익", "순이익", "자산", "부채", "자본", "현금"):
                        r[키] = (c.get(키) or {}).get("val")
                    if c["매출"]["end"] < "%04d%s" % (int(기준[:4]) - 2, 기준[4:]):
                        r["경보"] = "concept 매출 끝일 %s 이 기준일보다 2년 넘게 이르다 — 묵은 값" % c["매출"]["end"]
        # 2026-10-24 W18 — 외국 신고인(20-F · IFRS · 외화 태그)은 frames · cc_ 가 USD 만 봐서 「매출없음」 으로 남았다(유니버스 조사 결함 11 · 18 —
        # 중국 IDC · SAP 류). 외화개념(`fx_<티커>.json` — sec_외화개념.py)을 읽고 환율 캐시(`환율_<기준일>.json` — peer_환율.py)로 USD 환산한다.
        # 환율이 없으면 지어내지 않고 「외화 매출 — 환산 못 함」 을 남긴다. 결산이 기준일 90일 안 · 뒤면 쓰지 않는다(제출일을 모른다)
        if r.get("매출") is None:
            fp = os.path.join(PEER, "fx_%s.json" % t)
            if os.path.exists(fp):
                try:
                    fx = (json.load(io.open(fp, encoding="utf-8")).get("값") or {})
                except (OSError, ValueError):
                    fx = {}
                m = fx.get("매출")
                if isinstance(m, list) and len(m) >= 3 and m[1]:
                    통화, 값, 끝 = m[0], m[1], m[2]
                    계수 = _환율계수(기준).get(통화) if 통화 != "USD" else 1.0
                    if 끝 > (dt.date.fromisoformat(기준) - dt.timedelta(days=90)).isoformat():
                        r["기준일뒤회피"] = (r.get("기준일뒤회피") or []) + ["외화 매출 결산 %s — 기준일 90일 안 · 뒤라 쓰지 않음" % 끝]
                    elif 계수:
                        r.update({"매출": 값 * 계수, "매출끝": 끝, "매출기간": "fx", "출처": "외화개념(fx_) %s × 환율 캐시 %.6f" % (통화, 계수),
                                  "매출통화": 통화})
                        for 키 in ("영업이익", "순이익", "자산", "부채", "자본", "현금"):
                            v = fx.get(키)
                            r[키] = (v[1] * 계수) if (isinstance(v, list) and len(v) >= 2 and v[0] == 통화 and v[1] is not None) else r.get(키)
                    else:
                        r["밴드"] = "확인 불가 — 외화 매출 %s %s(%s) · 기준일 환율 캐시에 %s 없음(peer_환율.py 를 돌린다)" % (통화, "{:,.0f}".format(값), 끝, 통화)
        if r.get("매출") and r.get("영업이익") is not None:
            r["영업이익률"] = r["영업이익"] / r["매출"] if r["매출"] else None
        if sub and sub.get("최초제출"):
            r["최초제출"] = sub["최초제출"]
            r["상장경과년"] = round((dt.date.fromisoformat(기준) - dt.date.fromisoformat(sub["최초제출"])).days / 365.25, 1)
        return r

    대상 = None
    국내대상 = bool(a.대상 and (re.fullmatch(r"A?\d{6}", a.대상.strip(), re.I) or 국내대상_(a.대상)))   # 2026-10-24 W17 — 「009830.KS」 도(한화솔루션 조사)
    if a.대상 and not 국내대상:
        대상 = 행만들기(a.대상.upper(), {})
    대상매출 = float(a.대상매출) if a.대상매출 else (대상 or {}).get("매출")
    대상매출출처 = "--대상매출" if a.대상매출 else "frames"
    if not a.대상매출 and 국내대상:
        # 2026-10-24 W16 — 국내 대상(해외 경로 ⑤)의 USD 매출을 사람이 환율로 나눠 넣던 자리(유니버스 조사 물결 실측): 공용 C1 캐시의
        # 상장사 주요계정 매출(원) ÷ 평가기준일 환율(peer_환율 — 하나은행 고시)로 스스로 세운다
        대상매출, 대상매출출처 = 국내대상매출(국내대상_(a.대상) or a.대상.strip().upper().lstrip("A"), 기준)
    elif 대상 and not a.대상매출:
        # 2026-10-24 W16 — frames 연도(달력 해)가 대상의 최신 연차와 어긋나면(유니버스 조사 물결 실측) concept 보충의
        # 기준일 앞 최신 연간 매출을 쓰고 둘 다 적는다
        cp = os.path.join(PEER, "cc_%s.json" % a.대상.upper())
        try:
            c = json.load(io.open(cp, encoding="utf-8")) if os.path.exists(cp) else None
            cm = ((c or {}).get("값") or {}).get("매출") or None
            if cm and cm.get("val") and (대상 or {}).get("매출끝") and cm["end"] > 대상["매출끝"]:
                대상매출출처 = "concept 최신 연간 %s(frames %s %.0f백만 대신)" % (cm["end"], 대상["매출끝"], (대상매출 or 0) / 1e6)
                대상매출 = float(cm["val"])
        except (OSError, ValueError, TypeError):
            pass
    대상자산 = (대상 or {}).get("자산")
    if not 대상매출:
        sys.exit(대상매출출처 if 국내대상 else "대상회사 매출을 frames 에서 못 찾았습니다 — --대상매출 로 주십시오(기억으로 채우지 않습니다)")
    b, rb = a.밴드배수, a.참고밴드배수
    행들 = []
    for x in 명단목록:
        t = (x.get("티커") or (x.get("tickers") or [None])[0] or "").upper()
        if not t or (a.대상 and t == a.대상.upper()):
            continue
        r = 행만들기(t, x)
        if r.get("매출") is None:
            r["밴드"] = r.get("밴드") or "매출없음(frames) — --단계 싼층 의 concept 보충 대상"
        elif r["매출"] <= 0:
            r["밴드"] = "매출없음(0 이하)"
        else:
            배 = r["매출"] / 대상매출
            r["매출배수"] = 배
            r["매출로그거리"] = abs(math.log(배))
            r["밴드"] = ("통과" if 1 / b <= 배 <= b else
                       "밖(1/%g~%g배 안)" % (rb, rb) if 1 / rb <= 배 <= rb else "밖")
            if 대상자산 and r.get("자산"):
                r["자산배수"] = r["자산"] / 대상자산
            # 규모 판정을 믿을 수 없는 값은 자르지도 통과시키지도 않는다(2026-10-23) — 묵은 값 · 매출이 자산의 25배를 넘는 값(신고 단위 오류 의심 —
            # 실측: 매출 1,035억USD · 자산 78백만USD 가 「밖」 으로 갈렸다)
            if "묵은 값" in str(r.get("경보") or ""):
                r["밴드"] = "확인 불가 — %s" % r["경보"]
            elif r.get("자산") and r["자산"] > 0 and r["매출"] / r["자산"] > 25:
                r["경보"] = "매출 ÷ 자산 %.0f배 — 신고 단위 오류 의심(frames · concept 값)" % (r["매출"] / r["자산"])
                r["밴드"] = "확인 불가 — %s" % r["경보"]
        행들.append(r)
    순위 = {"통과": 0}
    행들.sort(key=lambda r: (순위.get(r["밴드"], 1 if str(r["밴드"]).startswith("밖(") else 2),
                          -(r.get("매출") or -1)))
    산출 = {"머리": {"표본": 표본, "기준일": 기준, "대상": a.대상, "대상매출": 대상매출, "대상매출출처": 대상매출출처,
                 "밴드": "매출 1/%g~%g배 = %.0f~%.0f 백만USD" % (b, b, 대상매출 / b / 1e6, 대상매출 * b / 1e6),
                 "참고밴드": "1/%g~%g배" % (rb, rb), "frames_CY": cy들,
                 "주의": "규모대는 매출 기준(C1). 시가총액 재판정은 C2·CP1 의 sec_peer_screen.py 가 한다"},
          "행": 행들}
    op = os.path.join(PEER, "후보표_%s.json" % 표본)
    json.dump(산출, io.open(op, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    from collections import Counter
    print("후보 %d곳 · %s" % (len(행들), dict(Counter(str(r["밴드"]).split(" —")[0] for r in 행들))))
    for r in 행들:
        if r["밴드"] == "통과" or str(r["밴드"]).startswith("밖("):
            print("  %-6s %-6s %-36s 매출 %9.0fm(%s) 영익률 %s 자산 %s 배수 %.2f %s" % (
                r["티커"], r.get("경로") or "", str(r.get("회사명"))[:36], r["매출"] / 1e6, r.get("매출끝"),
                ("%.3f" % r["영업이익률"]) if r.get("영업이익률") is not None else "  n/a",
                ("%.0fm" % (r["자산"] / 1e6)) if r.get("자산") else "n/a", r.get("매출배수", 0), r["밴드"]))
    빠짐 = [r["티커"] for r in 행들 if str(r["밴드"]).startswith("매출없음(frames)")]
    if 빠짐:
        print("  매출없음(frames) %d곳 — 자르기 전에 concept 보충: %s" % (len(빠짐), ",".join(빠짐[:40])))
    print("→ %s" % op)


# ────────────────────────── 사업발췌 (C1 — 10-K Item 1 / 20-F Item 4) ──────────────────────────
def 원문텍스트(s):
    s = re.sub(r"(?is)<(script|style|ix:header)[^>]*>.*?</\1>", " ", s)
    s = re.sub(r"(?i)</(p|div|tr|table|h\d|li)>|<br[^>]*/?>", "\n", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = _html.unescape(s).replace("\xa0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    return re.sub(r"\n\s*\n+", "\n", s)


def 항목발췌(txt, 폼="10-K", 길이=1800):
    """목차의 「Item 1. Business」를 건너뛰고 본문 제목을 찾는다 — 다음 Item 까지 2,000자 넘게 떨어진 첫 자리."""
    if 폼.startswith("20-F"):
        시작, 끝 = r"Item\s*4\.?\s*[:.\-–—]?\s*Information\s+on\s+the\s+Company", r"Item\s*4A"
    else:
        시작, 끝 = r"Item\s*1\.?\s*[:.\-–—]?\s*Business", r"Item\s*1A"
    for m in re.finditer(시작, txt, re.I):
        n = re.search(끝, txt[m.end():], re.I)
        거리 = n.start() if n else len(txt) - m.end()
        if 거리 > 2000:
            본문 = re.sub(r"\s+", " ", txt[m.start(): m.end() + min(거리, 길이 + 200)]).strip()
            return 본문[:길이]
    return None


def 사업발췌(명단, 기준일="9999-12-31"):
    contact = os.environ.get("SEC_CONTACT_EMAIL")
    H = {"User-Agent": "DCF-research %s" % contact, "Accept-Encoding": "gzip, deflate"} if contact else None
    cik표 = _cik표()
    for t in 명단:
        p = os.path.join(PEER, "item1_%s.json" % t)
        if os.path.exists(p):
            # 2026-10-24 W18 — 제출일을 안 적은 옛 캐시 가운데 보고 기간 끝이 기준일 125일 안이면(기준일 뒤에 냈을 수 있다) 다시 고른다
            try:
                옛 = json.load(io.open(p, encoding="utf-8"))
            except (OSError, ValueError):
                옛 = {}
            의심 = (not 옛.get("제출일") and 기준일 < "9999" and (옛.get("reportDate") or "") >
                  (dt.date.fromisoformat(기준일) - dt.timedelta(days=125)).isoformat())
            if not 의심 or not H:
                print("  %-6s 캐시%s" % (t, " — *** 제출일 미기재 · 보고 기간 끝 %s 이 기준일 125일 안(기준일 뒤 제출일 수 있음) — SEC_CONTACT_EMAIL 이 있어야 다시 고른다"
                                       % 옛.get("reportDate") if 의심 else ""))
                continue
        if not H:
            print("  %-6s *** SEC_CONTACT_EMAIL 없음 — 발췌 못 함" % t)
            continue
        import requests
        sub = _sub(t)
        cik = (sub or {}).get("cik") or cik표.get(t)
        if not cik:
            print("  %-6s *** cik 없음 — 조용히 빼지 않는다" % t)
            continue
        try:
            r = requests.get("https://data.sec.gov/submissions/CIK%010d.json" % int(cik), headers=H, timeout=60)
            rec = r.json()["filings"]["recent"]
            연차 = [k for k, f in enumerate(rec["form"]) if f in ("10-K", "20-F", "40-F", "10-K/A", "20-F/A")]
            # 기준일까지 **제출된** 최신 연차서류(2026-10-24 W18 — 보고 기간 끝만 보고 기준일 뒤에 낸 10-K 를 기준일 자료로 쓰던 결함 · NBIS 조사
            # IREN 2026-06-30 결산 · 08 제출, APLD 2026-05-31 결산 · 07 제출). 없으면 기준일 이전 보고기간의 것을 쓰되 `기준일뒤` 표지,
            # 그것도 없으면 가장 최근 것(비고에 적는다)
            안 = [k for k in 연차 if (rec["reportDate"][k] or "") <= 기준일 and (rec["filingDate"][k] or "") <= 기준일]
            앞 = [k for k in 연차 if (rec["reportDate"][k] or "") <= 기준일]
            후 = 안 or 앞 or 연차
            뒤후보 = [k for k in 앞 if (rec["filingDate"][k] or "") > 기준일]
            # 정정본(10-K/A · 20-F/A)은 Item 1 이 없는 일이 흔하다(인텔 시범 — AMD 10-K/A 「제목 못 찾음」) — 같은 보고기간의 원본을 먼저, 정정본은 그다음(2026-10-24 W15)
            원본먼저 = sorted(후[:4], key=lambda k: (rec["reportDate"][k] != rec["reportDate"][후[0]], rec["form"][k].endswith("/A")))
            발췌, i = None, 원본먼저[0]
            for i in 원본먼저[:2]:
                accn = rec["accessionNumber"][i].replace("-", "")
                url = "https://www.sec.gov/Archives/edgar/data/%d/%s/%s" % (int(cik), accn, rec["primaryDocument"][i])
                time.sleep(0.15)
                h = requests.get(url, headers=H, timeout=120)
                발췌 = 항목발췌(원문텍스트(h.text), rec["form"][i])
                if 발췌:
                    break
            d = {"티커": t, "url": url, "폼": rec["form"][i], "reportDate": rec["reportDate"][i], "제출일": rec["filingDate"][i],
                 "발췌": 발췌 or None, "비고": None if 발췌 else "Item 제목을 못 찾음 — 원문을 여십시오"}
            if 기준일 < "9999" and (rec["filingDate"][i] or "") > 기준일:
                d["기준일뒤"] = True
                d["기준일뒤_사유"] = "기준일까지 제출된 연차서류가 없어 기준일 뒤 제출(%s) 문서를 씀 — 사업 서술이 기준일 뒤 사실을 담을 수 있다" % rec["filingDate"][i]
            if 안 and 뒤후보:
                k = 뒤후보[0]
                d["기준일뒤문서"] = {"폼": rec["form"][k], "reportDate": rec["reportDate"][k], "제출일": rec["filingDate"][k], "기준일뒤": True,
                                 "쓰임": "쓰지 않음 — 기준일 뒤 제출(부록 G 재료)"}
            json.dump(d, io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print("  %-6s %s %s %s" % (t, rec["form"][i], rec["reportDate"][i], "발췌 %d자" % len(발췌) if 발췌 else "*** 제목 못 찾음"))
            time.sleep(0.15)
        except Exception as e:  # noqa
            print("  %-6s *** 조회 실패 %r — 조용히 빼지 않는다" % (t, e))


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="미국 유사기업 수집 사슬 — 층 단위 묶음 · 두 차선 병렬")
    ap.add_argument("--단계", required=True, choices=["싼층", "후보표", "사업발췌", "중간", "비싼", "운영", "전부"],
                    help="운영 = peer_운영지표.py --미국(CP2b). 전부 = 싼층 → 중간 → 비싼 → 운영")
    ap.add_argument("--명단", default="후보_전체.json")
    ap.add_argument("--tickers", default=None, help="명단 파일 대신 직접 지정")
    ap.add_argument("--기준일", "--평가기준일", dest="기준일", required=True, help="평가기준일 T(분석일 · 시장 쪽 — 종가 · 시가총액 · 주식수 · 베타 창 끝 · 환율 · 법령 시행일) YYYY-MM-DD")
    ap.add_argument("--재무기준일", default=None, help="재무 자료 기준일 F YYYY-MM-DD — 비싼 층의 peer_차입금 · peer_조립_us(→ peer_βU_us)에 넘긴다"
                                                   "(차입 · 현금 · 장부 값은 F 이하의 마지막 값). 비우면 평가기준일과 같다(날짜 둘)")
    ap.add_argument("--지수", default="^GSPC", help="Yahoo 지수 티커 (저장 키는 _INX)")
    ap.add_argument("--대상", default=None, help="대상회사 티커")
    ap.add_argument("--대상주식수", default=None)
    ap.add_argument("--밴드생략", action="store_true",
                    help="비싼: 해외 동종 경로 ⑤(대상이 다른 시장 — 국내 상장 · 대상은 Yahoo 티커, 예: 005930.KS) — 조립기에 넘긴다")
    ap.add_argument("--대상매출", default=None, help="후보표: frames 에 대상 매출이 없을 때만")
    ap.add_argument("--보충전부", action="store_true", help="싼층: frames 매출 없는 후보 전부에 concept · 외화개념(종전 동작)")
    ap.add_argument("--보충상한", type=int, default=40, help="싼층: 규모로 거른 뒤 보충할 상한(2026-10-24 W15)")
    ap.add_argument("--밴드", default=None, help="규모대 배수 — 조립에 넘긴다")
    ap.add_argument("--밴드배수", type=float, default=5.0, help="후보표: 매출 규모대 배수")
    ap.add_argument("--참고밴드배수", type=float, default=10.0, help="후보표: 참고로 표시할 넓은 배수")
    ap.add_argument("--표본", default=None, help="산출 이름 꼬리(기본: 명단 파일 이름)")
    ap.add_argument("--세율", default=None, help="비싼: 주면 βU·현금보정까지(기본값 없음)")
    ap.add_argument("--세율표", default=None, help='비싼: 회사별 소재국 세율 {"티커": 세율}(경로 또는 글) — 조립 · βU 에 넘긴다(2026-10-24 W16 — 대만 · 일본 동종의 세율이 공통 세율로 들어가던 자리)')
    ap.add_argument("--스크린", default=None, help="비싼: βU 단계가 시가총액을 읽을 sec_peer_screen 산출")
    ap.add_argument("--표지제안채택", action="store_true",
                    help="비싼: 표지 iXBRL 주식수 제안(주식수_제안.json)을 조립기에 넘긴다(--표지제안) — 유니버스 일괄 [판단](2026-10-24 W17)")
    ap.add_argument("--넓은표본", action="store_true",
                    help="비싼(CP3): companyfacts 를 새로 받지 않는다 — 캐시 있는 회사만 차입금")
    ap.add_argument("--캐시", default=None, help="_raw/peers 대신(시험용)")
    ap.add_argument("--창년", type=int, default=5, help="회귀 창 해 수(기본 5 — 주간). sec_주봉 · peer_조립_us 에 넘긴다")
    ap.add_argument("--운영표본", default="운영_해외",
                    help="운영 단계 산출 이름 꼬리(운영지표_{운영표본}.json) — 기본 운영_해외(2026-10-24 W17 · 국내 사슬은 운영_국내 — 같은 꼬리로 서로 덮었다)")
    ap.add_argument("--운영창", default="6", help="운영 단계 관측창 해 수(peer_운영지표 --창) — 기본 6: 대상 앵커(최소 여섯 해 · "
                                                "한 사이클)와 같은 자로 잰다(2026-10-16, S1 리뷰 — 종전 3해는 사이클 한쪽만 담았다)")
    a = ap.parse_args()
    global PEER, ROOT
    if a.캐시:
        PEER = os.path.abspath(a.캐시)
        ROOT = os.path.dirname(os.path.dirname(PEER))
    os.makedirs(PEER, exist_ok=True)
    if not a.대상:                                    # 대상을 주지 않으면 캐시의 대상.json(조립기와 같은 자리)에서 — 중간 층이 대상 종가를 함께 받게(2026-10-24 W15 · 인텔 시범)
        try:
            a.대상 = (json.load(io.open(os.path.join(PEER, "대상.json"), encoding="utf-8")) or {}).get("티커") or None
        except (OSError, ValueError, AttributeError):
            pass
        if a.대상:
            print("  대상 %s — 캐시 대상.json 에서" % a.대상)
    전체명단 = 티커들(a)
    전용 = 전용티커들(a)
    # 운영 동종 전용은 싼층 · 후보표 · 사업발췌(C1 층)에는 남기고, 중간 · 비싼(βU 재료)에서만 뺀다
    명단 = [t for t in 전체명단 if t not in 전용] if a.단계 in ("중간", "비싼", "전부") else 전체명단
    표본 = a.표본 or (os.path.splitext(os.path.basename(a.명단))[0] if not a.tickers else "직접지정")
    if a.단계 == "후보표" and not a.tickers and os.path.basename(명단경로(a)) == "후보표_%s.json" % 표본:
        sys.exit("산출 후보표_%s.json 이 입력 명단과 같습니다 — --표본 을 바꾸십시오" % 표본)
    기준일8 = a.기준일.replace("-", "")
    # 종가·주봉은 **대상회사도 함께** 받는다 — 조립기가 대상 종가·주봉을 같은 캐시에서 읽는다
    종가명단 = 명단 + ([a.대상.upper()] if a.대상 and a.대상.upper() not in 명단 else [])
    print("사슬 %s — %d곳 · 기준일 %s · 표본 %s · 회귀 창 %d년 주간" % (a.단계, len(명단), a.기준일, 표본, a.창년))
    if 전용 and a.단계 in ("중간", "비싼", "운영", "전부"):
        print("  운영 동종 전용 %d곳 — 주식수 · 종가 · 주봉 · 차입금 · 조립에서 뺌(재무는 운영 단계): %s"
              % (len(전용), ",".join(sorted(전용))))
    전체t0 = time.time()

    def 싼층():
        # **C1 의 층 — 종가(중간 층)를 받지 않는다.** 옛 판은 여기서 기준일 종가까지 받아
        # C1 이 사슬을 못 쓰고 frames 를 손으로 이었다(세일즈포스 회차).
        돌림("sec_frames.py", [])
        우선 = set()
        if not a.tickers:                              # 경로 ② · ④(낱말 · B1 거론) 후보는 규모 거름에서 남긴다
            _원 = [x for x in 명단읽기(명단경로(a)) if isinstance(x, dict)]
            우선 = {(x.get("티커") or "").upper() for x in _원 if any(m in ("%s" % (x.get("경로") or "")) for m in ("②", "④"))}
            우선 = 우선길이(우선, _원)
        싼명단 = list(명단)
        대자 = None
        코드 = 국내대상(a.대상)
        if 코드 and not a.보충전부:
            대자, 글 = 국내대상자산(코드, a.기준일)
            print("  대상 자산(규모 거름) — %s" % 글)
        if a.대상 and not a.보충전부:
            if not os.path.exists(os.path.join(PEER, "company_tickers.json")):
                돌림("sec_peer_meta.py", ["--tickers", a.대상.upper()])          # 티커 → cik 표(company_tickers.json)를 먼저
            싼명단, 메타뺀 = 메타전거르기(명단, a.대상, a.참고밴드배수, 우선, 대자=대자)
            if 메타뺀:
                print("  meta 전 규모 거름 %d곳 뺌(--보충전부 면 전부): %s" % (len(메타뺀), " · ".join(t for t, _ in 메타뺀[:12]) + (" 외" if len(메타뺀) > 12 else "")))
                json.dump([{"티커": t, "까닭": w} for t, w in 메타뺀], io.open(os.path.join(PEER, "싼층_메타전거름.json"), "w", encoding="utf-8"),
                          ensure_ascii=False, indent=1)
        돌림("sec_peer_meta.py", ["--tickers", ",".join(싼명단 + ([a.대상.upper()] if a.대상 and a.대상.upper() not in 싼명단 else []))])
        빠짐 = 보충대상(싼명단)
        외국, 메타없음 = 외국큐(싼명단)
        if 빠짐 and not a.보충전부:
            빠짐, 뺀 = 보충거르기(빠짐, a.대상.upper() if a.대상 else None, a.참고밴드배수, a.보충상한, 우선, 대형배수=10.0, 대자=대자)
            외국 = [t for t in 외국 if t not in {x for x, _ in 뺀}]
            if 뺀:
                print("  보충 전 규모 거름 %d곳 뺌(--보충전부 면 전부): %s" % (len(뺀), " · ".join("%s(%s)" % (t, w) for t, w in 뺀[:8])
                                                                         + (" 외" if len(뺀) > 8 else "")))
                json.dump([{"티커": t, "까닭": w} for t, w in 뺀], io.open(os.path.join(PEER, "싼층_보충뺌.json"), "w", encoding="utf-8"),
                          ensure_ascii=False, indent=1)
        if 메타없음:
            print("  주의: 메타 없는 후보 %d곳 — %s" % (len(메타없음), ",".join(메타없음)))
        if 빠짐:
            print("  concept 보충 %d곳 (frames 에 매출 없음): %s" % (len(빠짐), ",".join(빠짐)))
            r = 돌림("sec_concept.py", ["--tickers", ",".join(빠짐), "--기준일", a.기준일], False)
            if r.returncode != 0:            # 2026-10-24 W17 — 보충 일부 실패는 사슬을 멈추지 않는다(제주반도체 조사) — 후보표가 그 회사를 「매출 없음」 으로 둔다
                print("  경보: concept 보충이 rc %s 로 끝났다 — 받은 만큼으로 잇는다(cc_실패.json)" % r.returncode)
        외화 = [t for t in 빠짐 if t in 외국] or 외국
        if 외화:
            print("  외국 신고인 큐 %d곳: %s" % (len(외화), ",".join(외화)))
            돌림("sec_외화개념.py", ["--tickers", ",".join(외화), "--기준일", a.기준일], False)

    def 중간():
        외국, _ = 외국큐(명단)
        # cik 는 sec_shares_us.py 가 sub 메타·company_tickers 로 스스로 찾는다 — 명단을 그대로 넘긴다
        주식인자 = ["--기준일", a.기준일, "--tickers", ",".join(명단)]
        if a.캐시:
            주식인자 += ["--캐시", PEER]
        with ThreadPoolExecutor(2) as ex:
            A = ex.submit(lambda: (돌림("sec_shares_us.py", 주식인자),
                                   돌림("sec_ads비율.py", ["--tickers", ",".join(외국)], False)
                                   if 외국 else None))
            B = ex.submit(lambda: (돌림("peer_기준일종가.py",
                                       ["--기준일", 기준일8, "--추가", ",".join(종가명단)], False),
                                   돌림("peer_환율.py", ["--기준일", a.기준일], False)))
            A.result(); B.result()
        # 표지 주식수 — shares 가 못 채운 곳 + 외국 신고인
        결손 = [t for t in 명단 if not os.path.exists(os.path.join(PEER, "shares_%s.json" % t))]
        for t in 명단:                         # 2026-10-24 W17 — dei 가 1년 넘게 묵었거나 없는 회사(F 2011 · HMC 2020 · 다중 클래스)도 표지 큐로
            sp = os.path.join(PEER, "shares_%s.json" % t)
            if t not in 결손 and os.path.exists(sp):
                try:
                    if json.load(io.open(sp, encoding="utf-8")).get("dei묵음"):
                        결손.append(t)
                except (OSError, ValueError):
                    pass
        표지큐 = sorted(set(결손) | set(외국))
        if 표지큐:
            print("  표지 주식수 큐 %d곳: %s" % (len(표지큐), ",".join(표지큐)))
            돌림("sec_표지주식수.py", ["--tickers", ",".join(표지큐), "--기준일", a.기준일], False)

    def 비싼():
        종가경로 = os.path.join(PEER, "종가_%s.json" % 기준일8)
        if not os.path.exists(종가경로):
            돌림("peer_기준일종가.py", ["--기준일", 기준일8, "--추가", ",".join(종가명단)], False)
        else:
            있는 = set(json.load(io.open(종가경로, encoding="utf-8")).keys())
            빠진 = [t for t in 종가명단 if t not in 있는]
            if 빠진:
                돌림("peer_기준일종가.py", ["--기준일", 기준일8, "--추가", ",".join(빠진)], False)
        차입명단 = 명단
        if a.넓은표본:
            차입명단 = [t for t in 명단 if os.path.exists(os.path.join(PEER, "cf_%s.json" % t))]
            안받음 = [t for t in 명단 if t not in 차입명단]
            if 안받음:
                print("  넓은 표본 · companyfacts 미수집(규모대 밖 회사의 cf 를 새로 받지 않음) %d곳: %s"
                      % (len(안받음), ",".join(안받음)))
        주봉대상 = 명단 + ([a.대상.upper()] if a.대상 and a.대상.upper() not in 명단 else [])
        주봉캐시 = (["--캐시", PEER] if a.캐시 else []) + ["--창년", str(a.창년)]   # 캐시 창 판정은 sec_주봉.py 가 한다
        with ThreadPoolExecutor(2) as ex:
            A = ex.submit(lambda: 돌림("peer_차입금.py",
                                     ["--tickers", ",".join(차입명단), "--기준일", a.기준일]
                                     + (["--재무기준일", a.재무기준일] if a.재무기준일 else [])
                                     + (["--캐시", PEER] if a.캐시 else [])) if 차입명단 else None)
            B = ex.submit(lambda: (
                돌림("sec_주봉.py", ["--tickers", ",".join(주봉대상), "--기준일", a.기준일] + 주봉캐시),
                돌림("sec_주봉.py", ["--tickers", a.지수, "--키", "_INX", "--기준일", a.기준일] + 주봉캐시)))
            A.result(); B.result()
        조립 = ["--기준일", 기준일8, "--지수", "_INX", "--표본", 표본, "--창년", str(a.창년)]
        원 = None if a.tickers else json.load(io.open(명단경로(a), encoding="utf-8"))
        핵심표본꼴 = isinstance(원, dict) and not 원.get("행")        # 조립기는 목록 · {"행"} 만 읽는다
        # 2026-10-24 W17 — 문자열 목록(["FSLR", …])은 중간 단계를 지나 조립기에서 TypeError 로 죽었다(한화솔루션 조사) — dict 줄 목록이 아니면 늘 펴서 넘긴다
        정상꼴 = (isinstance(원, list) and all(isinstance(x, dict) for x in 원)) or (isinstance(원, dict) and bool(원.get("행")))
        if 전용 or 핵심표본꼴 or (원 is not None and not 정상꼴):
            임시 = os.path.join(PEER, "_사슬명단_%s.json" % 표본)
            json.dump([x for x in 명단읽기(명단경로(a)) if not 운영전용(x)],
                      io.open(임시, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            조립 += ["--명단", os.path.basename(임시)]
        elif a.tickers:
            임시 = os.path.join(PEER, "_사슬명단_%s.json" % 표본)
            json.dump([{"티커": t, "경로": "-"} for t in 명단], io.open(임시, "w", encoding="utf-8"))
            조립 += ["--명단", os.path.basename(임시)]
        else:
            조립 += ["--명단", a.명단]
        if a.대상:
            조립 += ["--대상", a.대상]
        if a.대상주식수:
            조립 += ["--대상주식수", a.대상주식수]
        if a.밴드생략:
            조립 += ["--밴드생략"]
        if a.밴드:
            조립 += ["--밴드", a.밴드]
        if a.세율:
            조립 += ["--세율", a.세율]
        if a.세율표:
            # 2026-10-24 W17 — 이름 · 상대 경로를 명단과 같은 규칙으로 절대 경로로(LIG디펜스 조사 — 이름만 주면 하위 도구가 JSON 글로 읽다 멈췄다)
            세 = a.세율표
            if not 세.lstrip().startswith("{"):
                세p = 피경.명단경로(세, PEER, ROOT)
                if not os.path.exists(세p):
                    sys.exit("--세율표 「%s」 — 파일을 못 찾았다(%s) · 티커별 세율 JSON 글이면 중괄호로 시작하게" % (세, 세p))
                세 = 세p
            조립 += ["--세율표", 세]
        if a.표지제안채택:
            조립 += ["--표지제안"]
        if a.재무기준일:
            조립 += ["--재무기준일", a.재무기준일]
        if a.스크린:
            조립 += ["--스크린", a.스크린]
        if a.캐시:
            조립 += ["--캐시", PEER]
        r = 돌림("peer_조립_us.py", 조립)
        print("\n".join((r.stdout or "").splitlines()[-25:]))

    if a.단계 in ("싼층", "전부"):
        싼층()
    if a.단계 == "후보표":
        후보표(a, 명단읽기(명단경로(a)) if not a.tickers else [{"티커": t} for t in 명단], 표본)
    if a.단계 == "사업발췌":
        사업발췌(명단, a.기준일)
    if a.단계 in ("중간", "전부"):
        중간()
    if a.단계 in ("비싼", "전부"):
        비싼()
    if a.단계 in ("운영", "전부"):
        # 2026-10-24 W16 — 운영 단계가 --tickers 를 무시하고 후보_전체.json 을 찾다 멈추던 결함(유니버스 조사 물결 실측)과
        # 핵심표본을 주면 컷 통과 전체 · 국내 회사까지 돌던 결함을 고친다: --tickers 는 그 명단 · 핵심표본은 운영 동종(운영동종전용 + 목적에 「운영」)만
        운명 = 명단경로(a) if not a.tickers else None
        if a.tickers:
            운명 = os.path.join(PEER, "_운영명단_직접지정.json")
            json.dump([{"티커": t} for t in 명단], io.open(운명, "w", encoding="utf-8"), ensure_ascii=False)
        else:
            try:
                원 = json.load(io.open(운명, encoding="utf-8"))
            except (OSError, ValueError):
                원 = None
            if isinstance(원, dict) and any(k in 원 for k in ("핵심", "예비") + _전용키):
                import 핵심표본읽기 as _hr
                운 = [_티커정규(x) for x in _hr.운영명단(원, "US")]
                운명 = os.path.join(PEER, "_운영명단_%s.json" % a.운영표본)
                json.dump(운, io.open(운명, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                print("  운영 동종(미국) %d곳: %s" % (len(운), ", ".join(str(x.get("티커")) for x in 운)))
        인자 = ["--명단", 운명, "--미국", "--기준일", a.기준일, "--표본", a.운영표본,
              "--창", str(a.운영창), "--뿌리", ROOT]
        r = 돌림("peer_운영지표.py", 인자, False)
        print("\n".join((r.stdout or "").splitlines()[-12:]))
    print("사슬 완료 — %.0f초" % (time.time() - 전체t0))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""기저율 — 같은 처지에 있던 다른 회사들이 실제로 어떻게 됐나(참조집단 · reference class)에 가정 경로를 대 본다.

무엇을 하나
  전 상장사 11년 패널(공용 캐시)에서 ① 3 · 5년 매출 CAGR 분위(규모 구간 · 같은 산업) ② 영업이익률 평균 회귀(분위 추적 ·
  Huber 계수)를 내고, 가정 파일의 시나리오 경로(엔진이 계산한 회계연도별 매출 · 영업이익)가 그 분포의 어디에 서는지 적는다.
  값을 정하지 않는다 — 「같은 집단에서 이 경로는 몇 번째인가 · 그런 창이 있었나」라는 관측과 신호만 낸다.

왜 있나
  키트는 시나리오 가정을 회사 자신의 과거(앵커 표의 관측 최저 · 최고)와 외부 제약에만 대 봤다. 2026-10-21 실험(국내 대형 사이클 업종 한 곳)에서
  드문 것은 성장률이 아니라 이익률 수준이었고, 성장률의 자리는 창을 어디서 끊느냐에 따라 82% ↔ 8% 로 뒤집혔다.
  그래서 창을 둘(마지막 실적 해 시작 · 첫 예측 해 시작) 다 잰다.

사용
  python 스크립트/기저율.py --받기 [--부터 2015] [--까지 YYYY]   # KR 공용 패널을 받는다(없는 해만 — 네트워크는 여기서만)
  python 스크립트/기저율.py --받기 --국가 US [--부터 2015]       # US 패널 — sec_fsds_패널.py 에 넘긴다(없는 분기 ZIP 만)
  python 스크립트/기저율.py --씨앗 <폴더> [--국가 US]             # 이미 받은 패널을 공용 자리로 복사(네트워크 0)
  python 스크립트/기저율.py 가정.json [--회사 고유번호] [--낼 경로.json] [--국가 KR|US]

국가 축(2026-10-22) — 패널이 둘이다. 가정 메타.표시통화가 고른다: KRW → KR(`{공용}/기저율/`) · USD → US(`{공용}/기저율/US/`).
  국가 블록(`기저율설정.json` 국가별)이 표시통화 · 제외 산업(KR KSIC 64~66 · 68 / US SIC 60~67) · 매출 하한 · 규모 구간을 덮고,
  나머지 계산(분위 · 평균 회귀 · 창 둘 · 신호)은 같은 코드다. 집단 이름의 산업 표식만 KSIC · SIC 로 갈린다(코드 안 키는 KSIC2 · KSIC3 그대로).
  그 밖의 통화(JPY …)는 종전처럼 「해당 없음」. **US 패널이 아직 없으면 「해당 없음」**(KR 패널 없음은 종전대로 입력오류) —
  파일이 없을 때 2026-10-20 판과 같게 도는 규약.

읽는 것
  KR 패널 `{공용}/기저율/주요계정_{연도}.csv`(dart_peer_screen.py 산출 꼴 — 옛 이름 `상장사_주요계정_{연도}.csv` 도 읽는다) · `산업분류.csv`(dart_induty.py).
  US 패널 `{공용}/기저율/US/주요계정_{회계연도}.csv` · `산업분류.csv`(sec_fsds_패널.py 산출 — 같은 열 이름 · 고유번호 = CIK 10자리 · 산업분류코드 = SIC 4자리).
  공용 = 환경변수 `DCF_공용캐시`(또는 `DCF_SHARED_CACHE`) · 없으면 `~/.dcf캐시`.
  가정 파일(읽기만) · 가정 곁 기업 식별 파일(KR `_raw/dart_기업개황.json` corp_code · induty_code / US `_raw/submissions.json` cik · sic 또는
  `_raw/companyfacts.json` cik — sec_fetch.py 산출) · 설정 `기저율설정.json`(결과 전에 정한 값).
내는 것
  가정 곁 `_raw/기저율.json` — {형식 · 만든날 · 설정 · 입력(국가 포함) · 패널 · 대상(국가 · 산업분류체계) · 경로 · 분위표 · CAGR자리 · 이익률드묾 ·
  평균회귀 · 대상회귀 · 업종적합 · 신호}. 신호 = [{출처 · 종류 · 대상 · 값 · 문턱 · 글 · 등급}] — 자체검사와 모순장부가 이 목록만 읽는다.
  업종적합(레터 v27 F1 · F5) — 대상 산업 2자리 대 핵심 표본 · 운영 동종(같은 분류 체계)의 일치 몫. 문턱(설정 「노출.업종적합_문턱」 · 기본 0.5) 미만이면
  업종 집단 줄(분위표 · CAGR자리 · 이익률드묾 · 비율자리 집단별 · 자리)에 `싣기가능: false` · `안싣는까닭` — 계산은 남기고 레터가 싣지 않는다.
  대상이 패널의 비교 대상이 아니면(표시통화가 KRW · USD 아님 · 그 국가 패널 없음 · 고유번호를 못 찾음) 같은 자리에 「해당 없음」 꼴
  ({형식 · 만든날 · 설정 · 입력 · 해당없음: 까닭 · 신호: [참고 한 줄]})을 내고 0 으로 끝낸다.
종료 코드 — 0 통과(신호가 있어도 · 해당 없음이어도 0 — 신호는 사람이 볼 목록이다) · 2 입력오류(가정 파일 깨짐 · KR 공용 패널 없음 ·
엔진 계산 실패).
인증키는 환경변수 OPENDART_API_KEY(KR 받기) · SEC_CONTACT_EMAIL(US 받기)에서만 읽고(하위 도구가) 화면 · 파일에 쓰지 않는다.
회사 · 업종 이름은 이 도구에 없다.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import glob
import io
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 입력오류  # noqa: E402

설정경로 = os.path.join(여기, "기저율설정.json")
시나리오들 = ("비관", "기준", "낙관")


def 설정읽기(경로=None):
    return json.load(io.open(경로 or 설정경로, encoding="utf-8"))


def 공용뿌리():
    return (os.environ.get("DCF_공용캐시") or os.environ.get("DCF_SHARED_CACHE")
            or os.path.join(os.path.expanduser("~"), ".dcf캐시"))


def 패널자리(설정=None):
    설정 = 설정 or 설정읽기()
    하위 = 설정["패널"].get("공용하위", "기저율")
    if isinstance(하위, (list, tuple)):
        return os.path.join(공용뿌리(), *하위)
    return os.path.join(공용뿌리(), 하위)


# ═══════════════════════════════════════════════ 국가 축 (2026-10-22)

통화국가 = {"KRW": "KR", "USD": "US"}


def 국가판정(가정, 강제=None):
    """가정 메타.표시통화 → 국가(KR · US). 모르는 통화면 None. `강제` 가 있으면 그대로."""
    if 강제:
        return 강제.upper()
    통 = ((가정.get("메타") or {}).get("표시통화") or "").strip().upper()
    return 통화국가.get(통)


def 국가설정(설정, 국가):
    """국가 블록(`국가별.<국가>`)이 `패널.공용하위` · `자료_제외` · `기저율` 의 같은 이름 칸을 덮은 설정 사본. 머리에 `_국가` ·
    `_산업분류` · `_고유번호자릿수` 를 적는다. 블록이 없는 국가(KR 의 옛 설정 파일)는 위 값 그대로 KR 이다."""
    설정 = json.loads(json.dumps(설정))
    국가 = (국가 or "KR").upper()
    블 = (설정.get("국가별") or {}).get(국가) or {}
    if 국가 != "KR" and not 블:
        raise KeyError("기저율설정.json 에 국가별.%s 블록이 없다" % 국가)
    if 블.get("패널하위"):
        설정["패널"]["공용하위"] = 블["패널하위"]
    for k in ("부터", "출처"):
        if k in 블:
            설정["패널"][k] = 블[k]
    for k in ("표시통화", "제외_산업", "제외_산업_까닭", "기업인수목적_이름", "기준연도_매출_하한_원"):
        if k in 블:
            설정["자료_제외"][k] = 블[k]
    for k in ("규모구간_기준", "규모구간_경계_원", "규모구간_이름"):
        if k in 블:
            설정["기저율"][k] = 블[k]
    설정["_국가"] = 국가
    설정["_산업분류"] = 블.get("산업분류") or ("KSIC" if 국가 == "KR" else 국가)
    설정["_고유번호자릿수"] = int(블.get("고유번호자릿수") or (8 if 국가 == "KR" else 10))
    설정["_대상파일"] = 블.get("대상파일")
    return 설정


def 국가맞춤(가정, 설정, 강제=None):
    """(국가, 국가 설정, 까닭). 국가를 못 가르면 (None, 설정, 까닭 글) — 「해당 없음」의 까닭이다."""
    국가 = 국가판정(가정, 강제)
    if not 국가:
        통 = ((가정.get("메타") or {}).get("표시통화") or "").strip()
        return None, 설정, "표시통화 %s — 패널은 %s 표시 회사만 담는다(국가별 블록: %s)" % (
            통 or "(비어 있음)", " · ".join("%s(%s)" % (c, n) for c, n in 통화국가.items()),
            " · ".join(sorted((설정.get("국가별") or {}).keys() - {"_뜻"})) or "KR")
    try:
        return 국가, 국가설정(설정, 국가), ""
    except KeyError as e:
        return None, 설정, str(e)


def _수(s):
    if s is None:
        return None
    if isinstance(s, (int, float)) and not isinstance(s, bool):
        return None if (isinstance(s, float) and math.isnan(s)) else float(s)
    s = ("%s" % s).strip().replace(",", "")
    if not s or s.lower() in ("nan", "none", "null", "-"):
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    return None if math.isnan(v) else v


# ═══════════════════════════════════════════════ 패널

def 패널파일들(자리):
    """{연도: 경로}. 새 이름(주요계정_{연도}.csv)이 옛 이름(상장사_주요계정_{연도}.csv)보다 먼저다."""
    낸 = {}
    for p in sorted(glob.glob(os.path.join(자리, "상장사_주요계정_*.csv")) + glob.glob(os.path.join(자리, "주요계정_*.csv"))):
        m = re.search(r"주요계정_(\d{4})\.csv$", os.path.basename(p))
        if not m:
            continue
        y = int(m.group(1))
        if y not in 낸 or os.path.basename(p).startswith("주요계정_"):
            낸[y] = p
    return 낸


def 산업분류읽기(자리, 자릿수=8):
    p = os.path.join(자리, "산업분류.csv")
    낸 = {}
    if not os.path.exists(p):
        return 낸
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            c = (r.get("고유번호") or "").strip().zfill(자릿수)
            if c.strip("0"):
                낸[c] = {"산업분류코드": (r.get("산업분류코드") or "").strip(), "상장구분": (r.get("상장구분") or "").strip(),
                        "회사명": (r.get("회사명") or "").strip()}
    return 낸


상세열 = ("매출원가", "유형자산", "매출채권", "재고자산", "매입채무", "영업현금흐름", "CAPEX", "감가상각비", "당기순이익")


def 상세읽기(자리, y):
    """국내 상세 패널(`dart_일괄패널.py` → `{자리}/일괄/상세_{연도}.csv`) — {종목코드: 행}. 없으면 빈 dict(2026-10-22)."""
    p = os.path.join(자리, "일괄", "상세_%d.csv" % y)
    if not os.path.exists(p):
        return {}
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        return {(r.get("종목코드") or "").strip().zfill(6): r for r in csv.DictReader(f)}


_상세변수캐시 = {}


def 상세변수자리(자리, 국가=None):
    """상세변수 폴더(`dart_상세변수` · `dart_직원패널` · `dart_주석패널` · `sec_상세변수` · `bls_임금패널` 의 계약 산출 — 2026-10-24 PK · PU) — 없으면 None.
    차례: `{자리}/상세변수` → `{자리}/{국가}/상세변수`(국내 패널 자리는 기저율 뿌리라 국내 상세변수는 KR 아래에 있다)."""
    for p in [os.path.join(자리, "상세변수")] + ([os.path.join(자리, 국가, "상세변수")] if 국가 else []):
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "목록.json")):
            return p
    return None


def 상세변수읽기(자리, 국가=None, 자릿수=8):
    """{변수: {고유번호: {연도: 값}}} — 상세변수 CSV(열: 고유번호 또는 CIK · 회계연도 · 값 · … · 딱지). 없으면 빈 dict. 한 번 읽으면 다시 읽지 않는다.
    값은 「계약」 그대로 — 이 함수는 정의를 고치지 않는다(정의역 거르기는 짓는 도구가 했다)."""
    p = 상세변수자리(자리, 국가)
    if not p:
        return {}
    열쇠 = (os.path.abspath(p), 자릿수)
    if 열쇠 in _상세변수캐시:
        return _상세변수캐시[열쇠]
    낸 = {}
    for fp in sorted(glob.glob(os.path.join(p, "*.csv"))):
        이름 = os.path.splitext(os.path.basename(fp))[0]
        if 이름.startswith("_"):
            continue
        with io.open(fp, encoding="utf-8-sig", newline="") as f:
            rd = csv.DictReader(f)
            if not rd.fieldnames or "값" not in rd.fieldnames or "회계연도" not in rd.fieldnames:
                continue
            키열 = "고유번호" if "고유번호" in rd.fieldnames else ("CIK" if "CIK" in rd.fieldnames else None)
            if not 키열:
                continue
            m = {}
            for r in rd:
                c = (r.get(키열) or "").strip().zfill(자릿수)
                v = _수(r.get("값"))
                y = (r.get("회계연도") or "").strip()
                if v is None or not y.isdigit() or not c.strip("0"):
                    continue
                m.setdefault(c, {})[int(y)] = v
            if m:
                낸[이름] = m
    _상세변수캐시[열쇠] = 낸
    return 낸


def 패널읽기(자리=None, 설정=None):
    """[{고유번호 · 회사명 · 연도 · 표시통화 · 재무제표구분 · 매출액 · 영업이익 · 자산총계 · 산업분류코드 · KSIC2 · KSIC3 · 상장구분 · (상세열 — 있으면)}].
    상세열(매출원가 · 유형자산 · 매출채권 · 재고자산 · 매입채무 · 영업현금흐름 · CAPEX · 감가상각비 · 당기순이익)은 주요계정 CSV 에 그 열이 있으면(US 패널) 거기서,
    없으면 같은 자리 `일괄/상세_{연도}.csv`(KR 상세 패널)를 종목코드로 붙여 채운다. 둘 다 없으면 None — 2026-10-20 판과 같다."""
    설정 = 설정 or 설정읽기()
    자리 = 자리 or 패널자리(설정)
    자릿수 = int(설정.get("_고유번호자릿수") or 8)
    파일 = 패널파일들(자리)
    산업 = 산업분류읽기(자리, 자릿수)
    행 = []
    상세있음 = 0
    for y, p in sorted(파일.items()):
        상세 = 상세읽기(자리, y)
        with io.open(p, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                c = (r.get("고유번호") or "").strip().zfill(자릿수)
                if not c.strip("0"):
                    continue
                s = 산업.get(c, {})
                k = s.get("산업분류코드") or ""
                h = {"고유번호": c, "회사명": (r.get("회사명") or "").strip(), "연도": y,
                     "표시통화": (r.get("표시통화") or "").strip(), "재무제표구분": (r.get("재무제표구분") or "").strip(),
                     "매출액": _수(r.get("매출액")), "영업이익": _수(r.get("영업이익")), "자산총계": _수(r.get("자산총계")),
                     "산업분류코드": k or None, "KSIC2": k[:2] if len(k) >= 2 else None,
                     "KSIC3": k[:3] if len(k) >= 3 else None, "상장구분": s.get("상장구분")}
                s2 = 상세.get((r.get("종목코드") or "").strip().zfill(6)) if 상세 else None
                채움 = False
                for col in 상세열:
                    v = _수(r.get(col)) if col in r else None
                    if v is None and s2 is not None:
                        v = _수(s2.get(col))
                    h[col] = v
                    채움 = 채움 or (v is not None and col != "당기순이익")      # 당기순이익은 주요계정에도 있다 — 상세가 붙었는지의 표식이 아니다
                상세있음 += 채움
                행.append(h)
    # 상세변수(2026-10-24 PM) — 회사 · 연도 행에 「상세」 dict 로 붙인다(지속성.변수계열 · 사후대조 관측이 같은 함수로 읽는다). 없으면 빈 dict
    상변 = 상세변수읽기(자리, 설정.get("_국가"), 자릿수)
    if 상변:
        for h in 행:
            d = {}
            for 이름, m in 상변.items():
                v = (m.get(h["고유번호"]) or {}).get(h["연도"])
                if v is not None:
                    d[이름] = v
            h["상세"] = d
    return 행, {"자리": 자리, "연도": sorted(파일), "산업분류": len(산업), "상세_회사연도": 상세있음,
               "상세변수": {"자리": 상세변수자리(자리, 설정.get("_국가")), "변수": sorted(상변)}}


def 자료제외(행, 설정):
    """비교에 못 쓰는 회사-연도를 사유와 함께 뺀다(이상치 판정이 아니다). (남은 행, 제외 [(고유번호, 회사명, 연도, 사유)])."""
    제 = 설정["자료_제외"]
    통화 = 제.get("표시통화") or "KRW"
    산업 = tuple(제.get("제외_산업") or ())
    이름 = tuple(제.get("기업인수목적_이름") or ())
    분류 = 설정.get("_산업분류") or "KSIC"
    남, 뺀 = [], []
    for r in 행:
        사유 = None
        if r["표시통화"] and r["표시통화"] != 통화:
            사유 = "표시통화 %s 아님" % 통화
        elif r["KSIC2"] and r["KSIC2"] in 산업:
            사유 = "제외 산업(%s %s)" % (분류, r["KSIC2"])
        elif any(x.upper() in r["회사명"].upper() for x in 이름):
            사유 = "기업인수목적회사"
        elif not (r["매출액"] and r["매출액"] > 0):
            사유 = "매출액 결측 또는 0 이하"
        elif not r["산업분류코드"]:
            사유 = "산업분류 미확보"
        if 사유:
            뺀.append((r["고유번호"], r["회사명"], r["연도"], 사유))
            continue
        r = dict(r)
        r["영업이익률"] = (r["영업이익"] / r["매출액"]) if r["영업이익"] is not None else None
        남.append(r)
    return 남, 뺀


def 중앙값(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def mz(xs):
    """Modified Z = 0.6745 (x − 중앙값) / MAD. MAD 가 0 이거나 값이 없으면 None."""
    v = [x for x in xs if x is not None]
    if not v:
        return [None] * len(xs)
    med = statistics.median(v)
    mad = statistics.median([abs(x - med) for x in v])
    if mad == 0:
        return [None] * len(xs)
    return [None if x is None else 0.6745 * (x - med) / mad for x in xs]


def 이익률표시(남, 설정):
    """연도별로 영업이익률의 Modified Z 를 붙인다(지우지 않는다). 표시 비율을 낸다."""
    thr = 설정["이상치_표시"]["문턱"]
    해별 = {}
    for r in 남:
        해별.setdefault(r["연도"], []).append(r)
    셈 = 0
    for _y, rs in 해별.items():
        zs = mz([r["영업이익률"] for r in rs])
        for r, z in zip(rs, zs):
            r["MZ_이익률"] = z
            r["표시_이익률"] = bool(z is not None and abs(z) > thr)
            셈 += r["표시_이익률"]
    return 셈 / len(남) if 남 else 0.0


# ═══════════════════════════════════════════════ 비율 자리 (2026-10-22 — 상세 패널이 있을 때)

def _비율(r, 식):
    """행 하나의 비율 — 설정 「비율자리.항목[].식」(분자/분모[*365]). 분모가 0 · 없음이면 None."""
    m = re.match(r"^(\w+)/(\w+)(\*365)?$", 식.replace(" ", ""))
    if not m:
        return None
    a, b = r.get(m.group(1)), r.get(m.group(2))
    if a is None or not b or b <= 0:
        return None
    v = a / b
    return v * 365 if m.group(3) else v


def _가정칸(가정, 번호, 시나리오="기준"):
    """가정 번호의 예측 열(TV 뺌 · 수만) — [(열, 값)] 또는 []. 「공통」이면 그것."""
    g = (가정.get("가정") or {}).get(번호)
    if not isinstance(g, dict):
        return []
    벌 = g.get("공통") if "공통" in g else g.get(시나리오)
    if not isinstance(벌, dict):
        return []
    return [(k, v) for k, v in 벌.items() if k != "TV" and isinstance(v, (int, float)) and not isinstance(v, bool)]


# 사후대조 보정(2026-10-23 밤 W8) — 비율 자리 번호 → (보정표 변수, 딱지). 182 는 패널 식(재고 ÷ 매출원가)과 보정표 변수(재고 ÷ 매출액)의 분모가
# 달라 띠의 넓고 좁음(q)만 빌린다([유추]). 186(매입채무)은 보정표에 같은 뿌리의 변수가 없어 보정하지 않는다
비율보정변수 = {"178": ("매출채권비율", "관측"), "182": ("재고비율", "유추"), "851": ("CAPEX비율", "관측"), "156": ("상각률", "관측")}


def _보정집단(집이름, 대상, 분류):
    """비율 자리 집단 이름 → 보정표 집단 후보 [(가족, 집단)] — 그 집단부터 더 넓은 집단으로(3자리 산업은 2자리의 q 를 빌린다)."""
    후 = []
    if 집이름.startswith("같은 규모("):
        후.append(("규모", 집이름[len("같은 규모("):-1]))
    elif 집이름.startswith("%s " % 분류):
        k = 집이름.split(" ", 1)[1]
        if 대상.get("KSIC2"):
            후.append(("산업2", "%s" % (k if len(k) == 2 else 대상["KSIC2"])))
        if 대상.get("규모구간"):
            후.append(("규모", 대상["규모구간"]))
    후.append(("전체", "전체"))
    return 후


def 비율자리(넓은, 대상, 가정, 설정, 집, 신, 보정표=None):
    """상세 패널의 비율(회전일수 · CAPEX 비율 · 상각률)마다 같은 집단 분위와 가정 칸(기준 시나리오 첫 · 끝 열)의 자리. 재료가 없는 항목은 「재료 없음」 한 줄.
    → [{번호 · 이름 · 식 · 근사 · 집단별[{집단 · 관측수 · 분위 · 보정}] · 대상실적 · 가정{첫 · 끝} · 자리[{집단 · 열 · 값 · 백분위 · 백분위_보정전 · 보정 q · 판정}]}].
    보정표(사후대조 — 있을 때만)가 있으면 집단의 10~90% 띠를 가운데(중앙값) 기준 q 배로 옮긴 띠(`보정`)를 더하고, 꼬리 판정은 같은 q 로 옮긴
    분포에서 잰다(값 v → 중앙값 + (v − 중앙값) ÷ q 의 백분위 · 첫 열은 1년 뒤 q · 끝 열은 2년 뒤 q). 보정표가 없으면 종전과 같다."""
    import 사후대조 as 사후                                     # noqa: PLC0415
    분류 = 설정.get("_산업분류") or "KSIC"
    B = 설정.get("비율자리") or {}
    if not B.get("항목"):
        return []
    창 = int(B.get("창_년") or 5)
    최소 = int(B.get("최소관측") or 30)
    꼬리 = float(B.get("꼬리") or 0.05)
    qs = 설정["기저율"]["분위"]
    해들 = sorted({y for d in 넓은.values() for y in d["해"]})
    최근 = set(해들[-창:])
    고 = 대상.get("고유번호")
    낸 = []
    for 항 in B["항목"]:
        번호, 식 = 항["번호"], 항["식"]
        값들 = [(c, y, _비율(r, 식)) for c, d in 넓은.items() for y, r in d["해"].items() if y in 최근 and c != 고]
        값들 = [(c, y, v) for c, y, v in 값들 if v is not None and math.isfinite(v) and (v >= 0 or 항.get("음수허용"))]
        x = {"번호": 번호, "이름": 항["이름"], "식": 식, "근사": 항.get("근사"), "척도": 항.get("척도"), "관측수": len(값들), "집단별": [], "자리": [],
             "대상실적": {str(y): round(_비율(r, 식), 4) for y, r in (넓은.get(고) or {}).get("해", {}).items() if _비율(r, 식) is not None} if 고 else {}}
        if len(값들) < 최소:
            x["판정"] = "재료 없음" if not 값들 else "표본 부족"
            낸.append(x)
            continue
        열들 = _가정칸(가정, 번호)
        x["가정"] = {"첫": 열들[0][1], "끝": 열들[-1][1], "열수": len(열들)} if 열들 else None
        보변 = 비율보정변수.get("%s" % 번호)
        for 이름, f in 집:
            g = sorted(v for c, y, v in 값들 if f({"규모구간": 넓은[c].get("규모구간"), "KSIC2": 넓은[c].get("KSIC2"), "KSIC3": 넓은[c].get("KSIC3")}))
            한집 = dict({"집단": 이름, "관측수": len(g)}, **{"q%02d" % round(q * 100): 분위(g, q) for q in qs})
            q값 = {}
            if 보정표 and 보변 and len(g) >= 최소:
                중, 아, 위 = 분위(g, 0.5), 분위(g, 0.1), 분위(g, 0.9)
                보 = {}
                for k in (1, 2):
                    r = 사후.보정찾기(보정표, 보변[0], k, "기저율", _보정집단(이름, 대상, 분류))
                    if r and 사후._수(r.get("아래")) and 사후._수(r.get("위")):
                        q값[k] = (r["아래"], r["위"])                # W9 — 꼬리별(아래 끝 · 위 끝 따로). 대칭이면 둘이 같다
                        보["%d년 뒤" % k] = {"q": r["보정계수"], "q아래": r["아래"], "q위": r["위"], "방식": r.get("방식"),
                                           "보정집단": "%s %s" % (r["가족"], r["집단"]), "딱지": 보변[1],
                                           "보정전": [아, 위], "보정뒤": list(사후.보정적용({"아래": 아, "가운데": 중, "위": 위}, r,
                                                                                 None if 항.get("음수허용") else 0.0))}
                if 보:
                    한집["보정"] = 보
            x["집단별"].append(한집)
            if not 열들 or len(g) < 최소:
                continue
            for 라벨, (열, v) in (("첫", 열들[0]), ("끝", 열들[-1])):
                아래 = sum(1 for u in g if u < v) / len(g)
                qq = q값.get(1 if 라벨 == "첫" else 2)
                원아래 = 아래
                q = None
                if qq:
                    중 = 분위(g, 0.5)
                    q = qq[1] if v >= 중 else qq[0]                 # 값이 선 쪽 꼬리의 q(W9 — 대칭이면 둘이 같다)
                    v2 = 중 + (v - 중) / q
                    아래 = sum(1 for u in g if u < v2) / len(g)
                판 = "위 꼬리" if 아래 >= 1 - 꼬리 else ("아래 꼬리" if 아래 <= 꼬리 else "")
                x["자리"].append({"집단": 이름, "열": "%s(%s)" % (라벨, 열), "값": v, "백분위": round(아래, 4), "판정": 판,
                                "백분위_보정전": round(원아래, 4), "보정q": q})
        걸린 = [a for a in x["자리"] if a["판정"]]
        if 걸린:
            전 = [a for a in 걸린 if a["집단"] == "전체"]
            등급 = "경보" if 전 else "참고"
            a0 = 전[0] if 전 else 걸린[0]
            신("비율 자리 꼬리", "기준 A-%s %s" % (번호, x["이름"]), a0["값"], "백분위 %s %.0f%%" % ("≥" if a0["판정"] == "위 꼬리" else "≤", (1 - 꼬리 if a0["판정"] == "위 꼬리" else 꼬리) * 100),
              "기준 시나리오 A-%s(%s) %s 열 %.4g 이 같은 집단(%s)의 %s(백분위 %.0f%%) — %s. 그 수준을 쓰는 까닭을 근거 칸에 적는다%s"
              % (번호, x["이름"], a0["열"], a0["값"], " · ".join(sorted({a["집단"] for a in 걸린})), a0["판정"], a0["백분위"] * 100,
                 "회사 자신의 최근 실적 %s" % x["대상실적"] if x["대상실적"] else "회사 자신의 실적은 패널에 없다",
                 (" · 근사: %s" % 항["근사"]) if 항.get("근사") else "")
              + ((" · 사후대조 보정 q %.2f 로 옮긴 분포에서 잰 백분위(보정 전 %.0f%%)" % (a0["보정q"], a0["백분위_보정전"] * 100)) if a0.get("보정q") else ""), 등급)
        낸.append(x)
    return 낸


def 넓히기(남):
    """{고유번호: {"해": {연도: 행}, "회사명", "KSIC2", "KSIC3", "산업분류코드"}}."""
    낸 = {}
    for r in 남:
        d = 낸.setdefault(r["고유번호"], {"해": {}, "회사명": r["회사명"], "KSIC2": r["KSIC2"], "KSIC3": r["KSIC3"],
                                         "산업분류코드": r["산업분류코드"]})
        d["해"][r["연도"]] = r
        d["회사명"], d["KSIC2"], d["KSIC3"] = r["회사명"], r["KSIC2"], r["KSIC3"]
    return 낸


def 규모구간(매출원, 설정):
    경계 = 설정["기저율"]["규모구간_경계_원"]
    이름 = 설정["기저율"]["규모구간_이름"]
    if 매출원 is None:
        return None
    for b, n in zip(경계, 이름):
        if 매출원 < b:
            return n
    return 이름[-1]


def cagr창(넓은, k, 설정):
    하한 = 설정["자료_제외"]["기준연도_매출_하한_원"]
    낸 = []
    for c, d in 넓은.items():
        해 = d["해"]
        for t0, a in 해.items():
            b = 해.get(t0 + k)
            if not b or not (a["매출액"] and a["매출액"] >= 하한 and b["매출액"] and b["매출액"] > 0):
                continue
            낸.append({"고유번호": c, "t0": t0, "t1": t0 + k, "매출_t0": a["매출액"],
                      "CAGR": (b["매출액"] / a["매출액"]) ** (1.0 / k) - 1,
                      "같은구분": a["재무제표구분"] == b["재무제표구분"], "규모구간": 규모구간(a["매출액"], 설정),
                      "KSIC2": d["KSIC2"], "KSIC3": d["KSIC3"]})
    return 낸


def 창계산(매출들, 영업들):
    """매출 t0..t0+5 · 영업이익 t0+1..t0+5 → (CAGR5, 매출가중 평균 이익률, 이익률 폭, 최저, 최고)."""
    m = [o / r for o, r in zip(영업들, 매출들[1:])]
    return ((매출들[5] / 매출들[0]) ** 0.2 - 1, sum(영업들) / sum(매출들[1:]), max(m) - min(m), min(m), max(m))


def 조합창(넓은, 설정):
    """회사-5년 창 (5년 CAGR · 5년 매출가중 평균 영업이익률 · 5년 영업이익률 폭). t0..t0+5 가 다 있어야 한다."""
    하한 = 설정["자료_제외"]["기준연도_매출_하한_원"]
    낸 = []
    for c, d in 넓은.items():
        해 = d["해"]
        for t0 in sorted(해):
            ys = [t0 + i for i in range(6)]
            if any(y not in 해 for y in ys):
                continue
            rs = [해[y] for y in ys]
            if not (rs[0]["매출액"] >= 하한 and all(r["매출액"] and r["매출액"] > 0 for r in rs)
                    and all(r["영업이익"] is not None for r in rs[1:])):
                continue
            cg, 평, 폭, 저, 고 = 창계산([r["매출액"] for r in rs], [r["영업이익"] for r in rs[1:]])
            낸.append({"고유번호": c, "회사명": d["회사명"], "t0": t0, "매출_t0": rs[0]["매출액"], "CAGR5": cg, "평균이익률5": 평,
                      "이익률폭5": 폭, "이익률최저": 저, "이익률최고": 고,
                      "같은구분": rs[0]["재무제표구분"] == rs[5]["재무제표구분"],
                      "표시_연도": any(r.get("표시_이익률") for r in rs[1:]),
                      "규모구간": 규모구간(rs[0]["매출액"], 설정), "KSIC2": d["KSIC2"], "KSIC3": d["KSIC3"]})
    return 낸


def 분위(xs, q):
    """선형 보간 분위(numpy 기본과 같은 방식). xs 는 정렬된 목록."""
    if not xs:
        return None
    pos = q * (len(xs) - 1)
    lo, hi = int(math.floor(pos)), int(math.ceil(pos))
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def 집단들(대상, 설정):
    """[(집단 이름, 거르개)] — 전체 · 같은 규모 구간 · 같은 KSIC 3자리 · 2자리. 대상 산업 · 규모를 모르면 그 집단은 없다."""
    낸 = [("전체", lambda w: True)]
    분류 = 설정.get("_산업분류") or "KSIC"            # 집단 이름의 산업 분류 표식(KR KSIC · US SIC) — 키 이름 KSIC2 · KSIC3 은 코드 내부 이름으로 둔다
    if 대상.get("규모구간"):
        g = 대상["규모구간"]
        낸.append(("같은 규모(%s)" % g, lambda w, g=g: w.get("규모구간") == g))
    if 대상.get("KSIC3"):
        k3 = 대상["KSIC3"]
        낸.append(("%s %s" % (분류, k3), lambda w, k3=k3: w.get("KSIC3") == k3))
    if 대상.get("KSIC2"):
        k2 = 대상["KSIC2"]
        낸.append(("%s %s" % (분류, k2), lambda w, k2=k2: w.get("KSIC2") == k2))
    return 낸


# ═══════════════════════════════════════════════ 평균 회귀

def huber(xs, ys, c=1.345, 회=100):
    """절편 있는 Huber IRLS. (절편, 기울기)."""
    def wls(w):
        sw = sum(w)
        if sw <= 0:
            return None
        mx = sum(wi * x for wi, x in zip(w, xs)) / sw
        my = sum(wi * y for wi, y in zip(w, ys)) / sw
        sxx = sum(wi * (x - mx) ** 2 for wi, x in zip(w, xs))
        if sxx <= 0:
            return None
        b = sum(wi * (x - mx) * (y - my) for wi, x, y in zip(w, xs, ys)) / sxx
        return my - b * mx, b
    ab = wls([1.0] * len(xs))
    if ab is None:
        return None
    for _ in range(회):
        a, b = ab
        r = [y - a - b * x for x, y in zip(xs, ys)]
        mr = statistics.median(r)
        s = statistics.median([abs(e - mr) for e in r]) * 1.4826
        if s == 0:
            break
        w = [1.0 if abs(e / s) <= c else c / abs(e / s) for e in r]
        ab2 = wls(w)
        if ab2 is None or (abs(ab2[0] - a) < 1e-12 and abs(ab2[1] - b) < 1e-12):
            ab = ab2 or ab
            break
        ab = ab2
    return ab


def 평균회귀(넓은, 설정, 뺄=()):
    """분위 추적(균형 표본) · Huber 계수(표시 포함 · 제외). 대상은 뺀다."""
    K = 설정["평균회귀"]["추적연수"]
    nq = 설정["평균회귀"]["분위수"]
    c = 설정["평균회귀"]["Huber_c"]
    M, F = {}, {}
    for 고, d in 넓은.items():
        if 고 in 뺄:
            continue
        for y, r in d["해"].items():
            if r.get("영업이익률") is not None:
                M.setdefault(고, {})[y] = r["영업이익률"]
                F.setdefault(고, {})[y] = bool(r.get("표시_이익률"))
    해들 = sorted({y for m in M.values() for y in m})
    med = {y: 중앙값([m[y] for m in M.values() if y in m]) for y in 해들}
    추적 = []
    for t0 in 해들:
        ys = [t0 + i for i in range(K + 1)]
        if any(y not in med for y in ys):
            continue
        sub = [(고, [m[y] for y in ys]) for 고, m in M.items() if all(y in m for y in ys)]
        if len(sub) < nq * 5:
            continue
        sub.sort(key=lambda t: t[1][0])
        n = len(sub)
        for i in range(nq):
            g = sub[i * n // nq:(i + 1) * n // nq]
            for j, y in enumerate(ys):
                추적.append((t0, i + 1, j, len(g), statistics.median([v[1][j] for v in g]), med[y]))
    합 = []
    for i in range(1, nq + 1):
        기편 = None
        for j in range(K + 1):
            rows = [t for t in 추적 if t[1] == i and t[2] == j]
            if not rows:
                continue
            편 = statistics.median([t[4] - t[5] for t in rows])
            if j == 0:
                기편 = 편
            합.append({"분위": i, "k": j, "관측창": len({t[0] for t in rows}), "회사수합": sum(t[3] for t in rows),
                      "분위중앙값": statistics.median([t[4] for t in rows]), "편차": 편,
                      "남는몫": (편 / 기편) if (기편 and abs(기편) > 0.005) else None})
    계수 = []
    for 설정명, 제외 in (("전체", False), ("표시제외", True)):
        for k in range(1, K + 1):
            xs, ys = [], []
            for 고, m in M.items():
                for t0, v0 in m.items():
                    if t0 + k not in m or med.get(t0) is None or med.get(t0 + k) is None:
                        continue
                    if 제외 and (F[고].get(t0) or F[고].get(t0 + k)):
                        continue
                    xs.append(v0 - med[t0])
                    ys.append(m[t0 + k] - med[t0 + k])
            ab = huber(xs, ys, c) if len(xs) >= 30 else None
            계수.append({"설정": 설정명, "k": k, "관측수": len(xs), "절편": ab[0] if ab else None, "기울기(남는몫)": ab[1] if ab else None})
    b = {(x["설정"], x["k"]): x["기울기(남는몫)"] for x in 계수}
    for x in 계수:
        b1 = b.get((x["설정"], 1))
        x["1년계수의k제곱"] = (b1 ** x["k"]) if b1 is not None else None
    반감기 = {}
    for s in ("전체", "표시제외"):
        b1 = b.get((s, 1))
        반감기[s] = round(math.log(0.5) / math.log(b1), 2) if (b1 and 0 < b1 < 1) else None
    갈 = (b.get(("전체", 1)) is not None and b.get(("표시제외", 1)) is not None
          and abs(b[("전체", 1)] - b[("표시제외", 1)]) > 설정["평균회귀"]["갈림_문턱"])
    결론 = ("설정에 따라 갈림 — 분위 추적을 읽는다(표시 포함 1년 계수 %.2f · 제외 %.2f)" % (b[("전체", 1)], b[("표시제외", 1)])
          if 갈 else "표시 포함 · 제외 계수가 갈리지 않음 — 분위 추적과 계수를 함께 읽는다")
    끝해 = max(med) if med else None
    return {"분위추적": 합, "계수": 계수, "반감기": 반감기, "결론": 결론, "중앙값": {str(y): v for y, v in med.items()},
            "마지막해": 끝해, "마지막해_중앙값": med.get(끝해) if 끝해 else None,
            "_분위경계": _분위경계(M, 끝해, nq) if 끝해 else None}


def _분위경계(M, y, nq):
    v = sorted(m[y] for m in M.values() if y in m)
    return [분위(v, i / nq) for i in range(1, nq)] if v else None


# ═══════════════════════════════════════════════ 대상

def _대상파일(가정경로, 국가):
    """회차 `_raw/` 의 기업 식별 파일에서 (고유번호, 산업분류). KR: dart_기업개황.json(corp_code · induty_code).
    US: submissions.json(cik · sic) → companyfacts.json(cik) — sec_fetch.py 산출."""
    곁 = os.path.dirname(os.path.abspath(가정경로))
    if 국가 == "US":
        후보 = (("_raw/submissions.json", "cik", "sic"), ("submissions.json", "cik", "sic"),
              ("_raw/companyfacts.json", "cik", None), ("companyfacts.json", "cik", None))
    else:
        후보 = (("_raw/dart_기업개황.json", "corp_code", "induty_code"), ("dart_기업개황.json", "corp_code", "induty_code"))
    for 상대, k코드, k산업 in 후보:
        p = os.path.join(곁, *상대.split("/"))
        if not os.path.exists(p):
            continue
        try:
            j = json.load(io.open(p, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        코드 = ("%s" % (j.get(k코드) or "")).strip()
        if 코드:
            산업 = ("%s" % (j.get(k산업) or "")).strip() if k산업 else ""
            return 코드, (산업 or None)
    return None, None


def 대상찾기(가정, 가정경로, 행, 회사=None, 설정=None):
    """(고유번호, 산업분류코드, 까닭). --회사 → 가정 곁 기업 식별 파일(국가별 — `_대상파일`) → 회사명 대조.
    고유번호 자릿수는 국가 설정(`_고유번호자릿수` — KR 8 · US 10)."""
    국가 = (설정 or {}).get("_국가") or "KR"
    자릿수 = int((설정 or {}).get("_고유번호자릿수") or 8)
    산업 = None
    if not 회사:
        회사, 산업 = _대상파일(가정경로, 국가)
    if not 회사:
        이름 = ((가정.get("메타") or {}).get("회사명") or "").strip()
        def 맞춤(s):
            s = re.sub(r"\(주\)|㈜|주식회사|\s|[.,]", "", s or "").upper()
            return re.sub(r"(INC|CORP|CORPORATION|CO|LTD|PLC|LIMITED|COMPANY)$", "", s) if 국가 == "US" else s
        if 이름:
            후 = {r["고유번호"] for r in 행 if 맞춤(r["회사명"]) == 맞춤(이름)}
            if len(후) == 1:
                회사 = 후.pop()
            elif len(후) > 1:
                return None, None, "회사명 「%s」 이 패널에서 %d곳과 겹친다 — --회사 고유번호를 준다" % (이름, len(후))
    if not 회사:
        파일 = ((설정 or {}).get("_대상파일") or ("_raw/dart_기업개황.json" if 국가 == "KR" else "_raw/submissions.json"))
        return None, None, "대상 고유번호를 못 찾았다 — --회사 를 주거나 가정 곁 %s 을 둔다" % 파일
    회사 = ("%s" % 회사).strip().zfill(자릿수)
    if not 산업:
        산업 = next((r["산업분류코드"] for r in 행 if r["고유번호"] == 회사 and r["산업분류코드"]), None)
    return 회사, 산업, ""


# ═══════════════════════════════════════════════ 업종 적합(레터 v27 F1 · 2026-11-10)
# 대상의 산업분류 2자리가 사업과 맞는지 — 핵심 표본 · 운영 동종(사람이 사업 접점으로 고른 회사들) 가운데 같은 분류 체계(이 패널의 체계 —
# 국내 KSIC · 미국 SIC)로 식별되는 회사의 2자리가 대상과 같은 몫으로 본다. 몫이 문턱 미만이거나 같은 체계 회사가 0곳이면 「업종 부적합」 —
# 업종(산업 2 · 3자리) 집단의 숫자는 계산은 하되 싣지 않는다(`싣기가능: false`). 핵심 표본 파일이 없거나 대상 산업을 모르면 판정하지 않는다(None).
업종적합문턱 = 0.5


def 노출설정(설정):
    """설정의 「노출」 블록(없으면 빈 dict) — 결과 전에 정한 값을 설정 파일에 두는 관례(없으면 코드 기본값)."""
    return ((설정 or {}).get("노출") or {}) if isinstance(설정, dict) else {}


def _핵심표본파일(가정경로):
    if not 가정경로:
        return None, None
    곁 = os.path.dirname(os.path.abspath(가정경로))
    for p in (os.path.join(곁, "_raw", "peers", "핵심표본.json"), os.path.join(곁, "peers", "핵심표본.json")):
        if os.path.exists(p):
            try:
                j = json.load(io.open(p, encoding="utf-8"))
            except (OSError, ValueError):
                return None, p
            return (j if isinstance(j, dict) else None), p
    return None, None


def _분류표(자리, 자릿수):
    """패널 자리의 산업분류.csv → ({고유번호: 코드}, {종목코드: 코드}). 없으면 빈 dict 둘."""
    p = os.path.join(자리 or "", "산업분류.csv")
    고, 종 = {}, {}
    if not 자리 or not os.path.exists(p):
        return 고, 종
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            k = (r.get("산업분류코드") or "").strip()
            if not k:
                continue
            c = (r.get("고유번호") or "").strip()
            if c.strip("0"):
                고[c.zfill(자릿수)] = k
            t = (r.get("종목코드") or "").strip()
            if t:
                종[t.zfill(6)] = k
    return 고, 종


def 업종적합(가정경로, 대상, 설정=None, 자리=None):
    """대상 산업분류 2자리 대 핵심 표본 · 운영 동종(같은 분류 체계)의 일치 몫 →
    {적합(True · False · None) · 몫 · 같은체계 · 일치 · 문턱 · 보기[] · 운영동종산업[] · 까닭}.
    운영동종산업 = 같은 체계로 식별된 표본 회사의 산업 2자리 합집합(지속성의 「운영 동종 산업」 집단 — 회사가 아니라 산업 집합이라 표본이 크다)."""
    설정 = 설정 or {}
    문턱 = float(노출설정(설정).get("업종적합_문턱", 업종적합문턱))
    낸 = {"적합": None, "몫": None, "같은체계": 0, "일치": 0, "문턱": 문턱, "보기": [], "운영동종산업": [], "까닭": ""}
    산업 = (대상 or {}).get("산업분류") or ""
    목표 = (대상 or {}).get("KSIC2") or (산업[:2] if len(산업) >= 2 else None)
    if not 목표:
        낸["까닭"] = "대상 산업분류를 모른다 — 판정하지 않았다"
        return 낸
    표, p = _핵심표본파일(가정경로)
    if not isinstance(표, dict):
        낸["까닭"] = "핵심 표본 파일(_raw/peers/핵심표본.json)이 없다 — 판정하지 않았다" if p is None else "핵심 표본 파일을 읽지 못했다 — 판정하지 않았다"
        return 낸
    회사들 = [e for 묶 in ("핵심", "운영동종전용") for e in (표.get(묶) or []) if isinstance(e, dict)]
    if not 회사들:
        낸["까닭"] = "핵심 표본 · 운영 동종이 비었다 — 판정하지 않았다"
        return 낸
    국가 = (대상 or {}).get("국가") or 설정.get("_국가") or "KR"
    자릿수 = int(설정.get("_고유번호자릿수") or (10 if 국가 == "US" else 8))
    if not 자리 and 설정.get("패널"):
        자리 = 패널자리(설정)
    고표, 종표 = _분류표(자리, 자릿수)
    산업들 = []
    for e in 회사들:
        코 = None
        if 국가 == "US":
            cik = e.get("CIK") or e.get("cik")
            if cik not in (None, ""):
                코 = 고표.get(("%s" % cik).strip().split(".")[0].zfill(자릿수))
        else:
            if e.get("고유번호"):
                코 = 고표.get(("%s" % e["고유번호"]).strip().zfill(자릿수))
            if not 코 and e.get("종목코드"):
                코 = 종표.get(("%s" % e["종목코드"]).strip().zfill(6))
        if not 코 or len(코) < 2:
            continue
        낸["같은체계"] += 1
        if 코[:2] == 목표:
            낸["일치"] += 1
        산업들.append(코[:2])
        낸["보기"].append("%s:%s" % (e.get("티커") or e.get("종목코드") or e.get("회사명") or "?", 코))
    낸["운영동종산업"] = sorted(set(산업들))
    if not 낸["같은체계"]:
        낸.update({"적합": False, "까닭": "핵심 표본 · 운영 동종 %d곳 가운데 같은 분류 체계로 식별되는 회사가 없다 — 대상 업종 분류(%s)를 사업과 대 볼 수 없다" % (len(회사들), 목표)})
        return 낸
    낸["몫"] = 낸["일치"] / 낸["같은체계"]
    낸["적합"] = 낸["몫"] >= 문턱
    낸["까닭"] = "핵심 표본 · 운영 동종 가운데 같은 체계 %d곳 중 %d곳이 대상 업종 2자리(%s)와 같다(몫 %.2f · 문턱 %.2f)" % (
        낸["같은체계"], 낸["일치"], 목표, 낸["몫"], 문턱)
    return 낸


def 업종집단표지(낸, 집이름들, 적합):
    """업종 부적합이면 업종 집단(산업 2 · 3자리) 줄에 `싣기가능: false` · `안싣는까닭` 을 붙인다(분위표 · CAGR자리 · 이익률드묾 · 비율자리 집단별 · 자리).
    줄을 지우지 않는다 — 계산은 남기고 레터가 싣지 않게 한다. 표지가 없는 줄은 실어도 된다."""
    if 적합 is not False or not 집이름들:
        return 0
    까 = "업종 부적합 — 대상 업종 분류가 핵심 표본 · 운영 동종의 업종과 엇갈린다(같은 규모 · 전체 집단으로 읽는다)"
    셈 = 0
    줄들 = list(낸.get("분위표") or []) + list(낸.get("CAGR자리") or []) + list(낸.get("이익률드묾") or [])
    for x in 낸.get("비율자리") or []:
        줄들 += list(x.get("집단별") or []) + list(x.get("자리") or [])
    for r in 줄들:
        if isinstance(r, dict) and r.get("집단") in 집이름들:
            r["싣기가능"] = False
            r["안싣는까닭"] = 까
            셈 += 1
    return 셈


def 경로(가정, 시나리오목록=시나리오들):
    """엔진으로 시나리오마다 회계연도별 매출 · 영업이익. {시: {"해": {연도: {매출, 영업이익, 영업이익률, 실적, 예측포함}},
    "영구이익률", "마지막실적해", "첫예측해"}} · 오류 목록. 금액은 가정의 금액단위 그대로(비율만 쓴다)."""
    from 엔진.계산 import 계산                              # noqa: PLC0415
    낸, 오류 = {}, []
    for 시 in 시나리오목록:
        try:
            R = 계산(가정, 시)
        except Exception as e:                               # noqa: BLE001
            오류.append("%s: %s" % (시, e))
            continue
        속 = R["기간"]["속성"]
        d = R["2.DCF"]
        해 = {}
        영구 = None
        for 열, p in 속.items():
            매, 영 = _수(d["11"].get(열)), _수(d["15"].get(열))
            if p.get("구분") == "영구기간":
                if 매 and 영 is not None:
                    영구 = 영 / 매
                continue
            y = int(p.get("회계연도"))
            h = 해.setdefault(y, {"매출": 0.0, "영업이익": 0.0, "실적": True, "예측포함": False, "실적섞임": False, "열": []})
            h["매출"] += 매 or 0.0
            h["영업이익"] += 영 or 0.0
            h["열"].append(열)
            if p.get("구분") != "실적":
                h["실적"] = False
                h["예측포함"] = True
            else:
                h["실적섞임"] = True
        for y, h in 해.items():
            h["영업이익률"] = (h["영업이익"] / h["매출"]) if h["매출"] else None
            h["실적섞임"] = bool(h["실적섞임"] and h["예측포함"])      # 한 회계연도에 실적 열(반기 누계 등)과 예측 열이 함께
        실해 = [y for y, h in 해.items() if h["실적"]]
        예해 = [y for y, h in 해.items() if h["예측포함"]]
        낸[시] = {"해": dict(sorted(해.items())), "영구이익률": 영구,
                 "마지막실적해": max(실해) if 실해 else None, "첫예측해": min(예해) if 예해 else None}
    return 낸, 오류


def 경로벡터(해, t0):
    """경로의 t0 창 — CAGR3 · CAGR5 · 5년 평균 이익률 · 폭 · 첫해 · 끝해 이익률. 없는 항은 None."""
    h = lambda y: 해.get(y)                                   # noqa: E731
    낸 = {"t0": t0}
    for k in (3, 5):
        a, b = h(t0), h(t0 + k)
        낸["CAGR%d" % k] = ((b["매출"] / a["매출"]) ** (1.0 / k) - 1) if (a and b and a["매출"] > 0 and b["매출"] > 0) else None
    if all(h(t0 + i) for i in range(6)) and all(h(t0 + i)["매출"] > 0 for i in range(6)):
        cg, 평, 폭, 저, 고 = 창계산([h(t0 + i)["매출"] for i in range(6)], [h(t0 + i)["영업이익"] for i in range(1, 6)])
        낸.update({"CAGR5": cg, "평균이익률5": 평, "이익률폭5": 폭, "이익률최저": 저, "이익률최고": 고})
    else:
        낸.update({"평균이익률5": None, "이익률폭5": None})
    return 낸


# ═══════════════════════════════════════════════ 분석

해당없음글 = "공용 패널(KR · US)이 이 회사의 비교 집단이 아니다 — 그 밖의 나라 기저율은 후속 과제"


def 해당없음(형식, 가정경로, 까닭, 설정, 출처):
    """대상회사가 패널의 비교 대상이 아닐 때(표시통화가 KRW · USD 아님 · 그 국가 패널 없음 · 고유번호 못 찾음)의 산출 — rc 0 으로 끝낸다.
    자체검사 · 모순장부는 「신호」 만 읽으므로 꼴은 같고, 신호는 「참고」 한 줄이다."""
    return {"형식": 형식, "만든날": datetime.date.today().isoformat(), "설정": 설정,
            "입력": {"가정": os.path.abspath(가정경로)}, "해당없음": 까닭,
            "신호": [{"출처": 출처, "종류": "해당 없음", "대상": "대상회사", "값": None, "문턱": None,
                    "글": "%s(%s)" % (해당없음글, 까닭), "등급": "참고"}]}


def 해당여부(가정, 설정, 국가=None):
    """국가를 못 가르면(표시통화가 KRW · USD 아님 · 국가 블록 없음) 까닭 글, 아니면 None. 옛 호출 꼴을 지킨다 — 국가 설정은 `국가맞춤`."""
    _국, _설, 까 = 국가맞춤(가정, 설정, 국가)
    return 까 or None


def 분석(가정, 가정경로, 설정=None, 회사=None, 자리=None, 국가=None):
    """(산출, 까닭). 입력오류면 (None, 까닭). 대상이 패널의 비교 대상이 아니면 「해당없음」 산출.
    국가는 가정 메타.표시통화가 고른다(KRW → KR · USD → US) — `국가` 로 덮을 수 있다. US 패널이 아직 없으면(받지 않음) 「해당없음」이다
    (KR 패널 없음은 종전대로 입력오류 — 2026-10-20 판과 같게)."""
    설정 = 설정 or 설정읽기()
    국, 설정, 까 = 국가맞춤(가정, 설정, 국가)
    if not 국:
        return 해당없음("기저율 1", 가정경로, 까, 설정, "기저율"), ""
    행, 패널입력 = 패널읽기(자리, 설정)
    if not 행:
        if 국 != "KR":
            return 해당없음("기저율 1", 가정경로, "%s 패널이 비었다(%s) — `기저율.py --받기 --국가 %s` 를 먼저"
                        % (국, 패널입력["자리"], 국), 설정, "기저율"), ""
        return None, "공용 패널이 비었다(%s) — `기저율.py --받기` 또는 `--씨앗` 을 먼저" % 패널입력["자리"]
    고, 산업, 까 = 대상찾기(가정, 가정경로, 행, 회사, 설정)
    if not 고:
        return 해당없음("기저율 1", 가정경로, 까, 설정, "기저율"), ""
    남, 뺀 = 자료제외(행, 설정)
    표시비 = 이익률표시(남, 설정)
    넓은 = 넓히기(남)
    길, 엔진오류 = 경로(가정)
    if not 길:
        return None, "엔진이 가정을 계산하지 못했다 — %s" % " / ".join(엔진오류)
    기 = next(iter(길.values()))
    마실, 첫예 = 기["마지막실적해"], 기["첫예측해"]
    배율 = _수((가정.get("메타") or {}).get("환산배율")) or 1.0
    대상행 = (넓은.get(고) or {}).get("해", {})
    기준매출 = (대상행.get(마실) or {}).get("매출액")
    if 기준매출 is None and 마실 and 마실 in 기["해"]:
        기준매출 = 기["해"][마실]["매출"] * 배율
    대상 = {"고유번호": 고, "회사명": (가정.get("메타") or {}).get("회사명"), "국가": 국, "산업분류": 산업,
          "산업분류체계": 설정.get("_산업분류"),
          "KSIC3": 산업[:3] if 산업 and len(산업) >= 3 else None, "KSIC2": 산업[:2] if 산업 and len(산업) >= 2 else None,
          "기준연도매출_원": 기준매출, "규모구간": 규모구간(기준매출, 설정), "마지막실적해": 마실, "첫예측해": 첫예,
          "패널에_있음": bool(대상행), "엔진오류": 엔진오류}
    대상["업종적합"] = 업종적합(가정경로, 대상, 설정, 패널입력["자리"])      # 레터 v27 F1 — 업종 집단 숫자를 실어도 되나
    집 = 집단들(대상, 설정)
    최소 = 설정["기저율"]["최소관측"]
    꼬리 = 설정["기저율"]["꼬리"]
    qs = 설정["기저율"]["분위"]
    신호 = []

    def 신(종류, 대상글, 값, 문턱, 글, 등급="경보"):
        신호.append({"출처": "기저율", "종류": 종류, "대상": 대상글, "값": 값, "문턱": 문턱, "글": 글, "등급": 등급})

    # ── 분위표 · CAGR 자리
    분위표, 자리표 = [], []
    창들 = [("마지막 실적 해 시작", 마실), ("첫 예측 해 시작", 첫예)]
    부족 = set()
    for k in 설정["기저율"]["CAGR_창"]:
        W = [w for w in cagr창(넓은, k, 설정) if w["고유번호"] != 고]
        주 = [w for w in W if w["같은구분"]] if 설정["자료_제외"].get("창_양끝_같은구분", True) else W
        for 이름, f in 집:
            g = sorted(w["CAGR"] for w in 주 if f(w))
            분위표.append(dict({"창(년)": k, "집단": 이름, "관측수": len(g),
                              "회사수": len({w["고유번호"] for w in 주 if f(w)})},
                             **{"q%02d" % round(q * 100): 분위(g, q) for q in qs}))
            for 창이름, t0 in 창들:
                if t0 is None:
                    continue
                for 시, 경 in 길.items():
                    x = 경로벡터(경["해"], t0).get("CAGR%d" % k)
                    if x is None:
                        continue
                    if len(g) < 최소:
                        부족.add(이름)
                        판 = "표본 부족"
                        아래 = 이상 = None
                    else:
                        아래 = sum(1 for v in g if v < x) / len(g)
                        이상 = sum(1 for v in g if v >= x) / len(g)
                        판 = "위 꼬리" if 아래 >= 1 - 꼬리 else ("아래 꼬리" if 아래 <= 꼬리 else "")
                    자리표.append({"창(년)": k, "창": 창이름, "구간": "%d→%d" % (t0, t0 + k), "시나리오": 시, "CAGR": x,
                                 "집단": 이름, "관측수": len(g), "백분위": 아래, "이상비중": 이상, "판정": 판})
    # 경보 묶기(2026-10-23 밤 · 연구/레터워크북_최적화_20261023/03 4-6) — 시나리오 셋 × 창 둘 × 비교 집단 넷의 조합이 같은 뿌리(정점 출발 · 초고성장)를
    # 반복 세어 경보가 20건까지 났다. 이제 경보는 **두 창 모두 · 비교 집단 둘 이상**에서 같은 쪽 꼬리일 때만이고(한 창 · 한 집단만이면 참고),
    # 같은 (창 길이 · 방향 · 등급)은 시나리오를 한 줄로 묶는다. 꼬리 문턱(5%)은 그대로 — 다중 비교를 줄이는 것이지 문턱을 옮기는 것이 아니다
    최소집단 = min(2, len(집))
    묶음 = {}
    for k in 설정["기저율"]["CAGR_창"]:
        for 시 in 길:
            for 방향 in ("위 꼬리", "아래 꼬리"):
                창별 = {}
                for 창이름, t0 in 창들:
                    걸린 = [x for x in 자리표 if x["창"] == 창이름 and x["창(년)"] == k and x["시나리오"] == 시 and x["판정"] == 방향]
                    if 걸린:
                        창별[창이름] = 걸린
                if not 창별:
                    continue
                있는창 = [c for c, t0 in 창들 if t0 is not None]
                등급 = "경보" if (len(창별) == len(있는창) and all(len(v) >= 최소집단 for v in 창별.values())) else "참고"
                묶음.setdefault((k, 방향, 등급), []).append((시, 창별))
    for (k, 방향, 등급), 줄들 in 묶음.items():
        시들 = [시 for 시, _ in 줄들]
        시말 = ("%s 모두" % " · ".join(시들)) if len(시들) == len(길) and len(길) > 1 else " · ".join(시들)
        첫시, 첫창 = 줄들[0]
        조각 = []
        for 창이름, 걸린 in 첫창.items():
            조각.append("%s %s CAGR %.1f%% — %s(백분위 %s)" % (창이름, 걸린[0]["구간"], 걸린[0]["CAGR"] * 100, " · ".join(x["집단"] for x in 걸린),
                                                         " · ".join("%.0f%%" % (x["백분위"] * 100) for x in 걸린)))
        x0 = next(iter(첫창.values()))[0]
        신("CAGR 꼬리", "%s %d년 CAGR(%s)" % (시말, k, 방향), round(x0["CAGR"], 4),
          "백분위 %s %.0f%% · 경보는 두 창 모두 · 비교 집단 %d곳 이상" % ("≥" if 방향 == "위 꼬리" else "≤", (1 - 꼬리 if 방향 == "위 꼬리" else 꼬리) * 100, 최소집단),
          "%s 시나리오의 %d년 매출 CAGR 이 같은 집단에서 %s다(%s 기준: %s)%s — 그 경로가 가능한 근거를 매출 근거 칸에 적는다"
          % (시말, k, 방향, 첫시, " / ".join(조각), "" if 등급 == "경보" else " · 한 창이나 한 집단에서만 걸려 참고로 둔다"), 등급)
    # 창에 따라 판정이 뒤집히는가(사이클 경로)
    for k in 설정["기저율"]["CAGR_창"]:
        for 시 in 길:
            a = [x for x in 자리표 if x["창(년)"] == k and x["시나리오"] == 시 and x["집단"] == "전체" and x["백분위"] is not None]
            if len({x["창"] for x in a}) == 2:
                b = {x["창"]: x["백분위"] for x in a}
                if abs(b["마지막 실적 해 시작"] - b["첫 예측 해 시작"]) >= 0.5:
                    신("창에 따라 뒤집힘", "%s %d년 CAGR" % (시, k), "%.0f%% ↔ %.0f%%" % (b["마지막 실적 해 시작"] * 100, b["첫 예측 해 시작"] * 100),
                      "백분위 차 50%p", "%s 의 %d년 CAGR 백분위가 시작 해에 따라 %.0f%% 와 %.0f%% 로 갈린다 — 경로가 오르내리는 꼴이라 CAGR 하나로 "
                      "요약하지 말고 정점 · 바닥 · 폭을 함께 본다" % (시, k, b["마지막 실적 해 시작"] * 100, b["첫 예측 해 시작"] * 100), "참고")

    # ── 이익률 드묾 — 같은 집단 5년 창에서 그 값 이상인 비중
    조 = [w for w in 조합창(넓은, 설정) if w["고유번호"] != 고]
    조주 = [w for w in 조 if w["같은구분"]] if 설정["자료_제외"].get("창_양끝_같은구분", True) else 조
    드묾 = []
    for 시, 경 in 길.items():
        for 창이름, t0 in 창들:
            if t0 is None:
                continue
            v = 경로벡터(경["해"], t0)
            항목들 = [("5년 평균 영업이익률", v.get("평균이익률5"), "평균이익률5"), ("5년 영업이익률 폭", v.get("이익률폭5"), "이익률폭5")]
            if 창이름 == "마지막 실적 해 시작":
                항목들.append(("영구 정규화 영업이익률", 경["영구이익률"], "평균이익률5"))
            for 항목, x, 열 in 항목들:
                if x is None:
                    continue
                for 이름, f in 집:
                    g = [w[열] for w in 조주 if f(w)]
                    이상 = (sum(1 for u in g if u >= x) / len(g)) if g else None
                    드묾.append({"시나리오": 시, "창": 창이름, "구간": "%d→%d" % (t0, t0 + 5), "항목": 항목, "값": x, "집단": 이름,
                               "관측수": len(g), "이상비중": 이상, "이상건수": sum(1 for u in g if u >= x),
                               "판정": "표본 부족" if len(g) < 최소 else ("0건" if g and not any(u >= x for u in g)
                                                                    else ("드묾" if 이상 is not None and 이상 <= 꼬리 else ""))})
    def _집단글(xs):
        if len(xs) == len(집) and all(x["판정"] == "0건" for x in xs):
            return "비교 집단 %d곳 모두 그 이상 0건" % len(xs)
        return " · ".join("%s %s" % (x["집단"], "0건" if x["판정"] == "0건" else "%.1f%%" % (x["이상비중"] * 100)) for x in xs)

    묶드 = {}
    for 시 in 길:
        for 항목 in ("5년 평균 영업이익률", "영구 정규화 영업이익률", "5년 영업이익률 폭"):
            걸린 = [x for x in 드묾 if x["시나리오"] == 시 and x["항목"] == 항목 and x["판정"] in ("0건", "드묾")]
            if not 걸린:
                continue
            창별 = []
            본창 = sorted({x["창"] for x in 드묾 if x["시나리오"] == 시 and x["항목"] == 항목 and x["판정"] != "표본 부족"})
            모두 = bool(본창)
            for 창이름, _t0 in 창들:
                xs = [x for x in 걸린 if x["창"] == 창이름]
                if xs:
                    창별.append("%s(%.1f%%): %s" % (xs[0]["구간"], xs[0]["값"] * 100, _집단글(xs)))
                if 창이름 in 본창 and len(xs) < min(2, len(집)):
                    모두 = False
            등급 = "경보" if 모두 else "참고"                     # 2026-10-23 밤 — 재어 본 창 모두 · 비교 집단 둘 이상에서 드물 때만 경보(03 4-6)
            묶드.setdefault((항목, 등급), []).append((시, 걸린[0], 창별))
    for (항목, 등급), 줄들 in 묶드.items():
        시들 = [시 for 시, _x, _c in 줄들]
        시말 = ("%s 모두" % " · ".join(시들)) if len(시들) == len(길) and len(길) > 1 else " · ".join(시들)
        첫시, x0, 창별 = 줄들[0]
        영구말 = " — 5년 창의 빈도라 「영구히」 유지되는 빈도의 상한이다" if 항목.startswith("영구") else ""
        신("이익률 드묾" if 항목 != "5년 영업이익률 폭" else "이익률 폭 드묾", "%s %s" % (시말, 항목), round(x0["값"], 4),
          "같은 집단 5년 창 중 그 값 이상 비중 ≤ %.0f%% · 경보는 재어 본 창 모두 · 비교 집단 둘 이상" % (꼬리 * 100),
          "%s 의 %s 이 같은 집단 5년 창에서 드물다(%s 기준 — %s)%s. 이 수준이 지속되는 근거를 시점 가정 근거 칸에 적는다%s"
          % (시말, 항목, 첫시, " / ".join(창별), 영구말, "" if 등급 == "경보" else " · 한 창이나 한 집단에서만 드물어 참고로 둔다"), 등급)

    # ── 평균 회귀 · 대상 회귀
    회 = 평균회귀(넓은, 설정, 뺄={고})
    대상회귀 = []
    K = 설정["평균회귀"]["추적연수"]
    med끝 = 회["마지막해_중앙값"]
    경계 = 회["_분위경계"] or []
    여유 = 설정["평균회귀"]["띠_여유"]
    계수표 = {x["k"]: x["기울기(남는몫)"] for x in 회["계수"] if x["설정"] == "표시제외"}
    for 시, 경 in 길.items():
        t0 = 경["첫예측해"]
        if t0 is None or t0 not in 경["해"] or med끝 is None:
            continue
        m0 = 경["해"][t0]["영업이익률"]
        if m0 is None or abs(m0 - med끝) < 0.01:
            continue
        q = 1 + sum(1 for b in 경계 if b is not None and m0 > b)
        분추 = {x["k"]: x["남는몫"] for x in 회["분위추적"] if x["분위"] == q}
        for k in range(0, K + 1):
            h = 경["해"].get(t0 + k)
            if not h or h["영업이익률"] is None:
                continue
            남몫 = (h["영업이익률"] - med끝) / (m0 - med끝)
            a, b = 분추.get(k), (1.0 if k == 0 else 계수표.get(k))
            띠 = None
            if a is not None and b is not None:
                띠 = (min(a, b) - 여유, max(a, b) + 여유)
            대상회귀.append({"시나리오": 시, "연도": t0 + k, "k": k, "이익률": h["영업이익률"], "남는몫": 남몫, "출발분위": q,
                           "기저율_분위추적": a, "기저율_계수_표시제외": b, "띠": 띠,
                           "판정": ("" if (띠 is None or k == 0 or 띠[0] <= 남몫 <= 띠[1]) else ("빠름" if 남몫 < 띠[0] else "느림"))})
        끝 = [x for x in 대상회귀 if x["시나리오"] == 시 and x["k"] > 0 and x["판정"]]
        if 끝:
            x = 끝[-1]
            신("평균 회귀 띠 밖", "%s %d년 뒤(%d)" % (시, x["k"], x["연도"]), round(x["남는몫"], 3),
              "%.2f ~ %.2f" % x["띠"],
              "%s 의 초과 이익률이 %d년 뒤 %.0f%% 남는다 — 같은 출발 분위(%d분위) 회사들의 기저율 띠(%.0f~%.0f%%)보다 %s. "
              "수렴 연수 · 꺾이는 해의 근거를 적는다" % (시, x["k"], x["남는몫"] * 100, x["출발분위"], x["띠"][0] * 100, x["띠"][1] * 100,
                                          "빨리 돌아온다" if x["판정"] == "빠름" else "느리게 돌아온다"))
    for 이름 in sorted(부족):
        신("표본 부족", 이름, None, 최소, "%s 의 비교 관측이 %d개보다 적어 그 집단 판정을 하지 않았다" % (이름, 최소), "참고")

    # ── 비율 자리(2026-10-22) — 상세 패널(회전일수 · CAPEX 비율 · 상각률)이 있을 때만 · 없으면 「재료 없음」 목록
    for 고2, d in 넓은.items():
        마 = max(d["해"])
        d["규모구간"] = 규모구간(d["해"][마].get("매출액"), 설정)
    import 사후대조 as 사후                                     # noqa: PLC0415 — 보정표(있을 때만 · 2026-10-23 밤 W8)
    보정표, 보정상태, 보정글 = 사후.보정표읽기(국, 패널입력["자리"])
    if 보정상태 == "낡음":
        신("보정표 낡음", "사후대조 보정표", None, None, 보정글, "참고")
    비율 = 비율자리(넓은, 대상, 가정, 설정, 집, 신, 보정표)
    if 비율 and all(x.get("판정") == "재료 없음" for x in 비율):
        신("재료 없음", "비율 자리", None, None, "상세 패널(매출채권 · 재고 · 매입채무 · 유형자산 · CAPEX · 감가상각비)이 없어 회전일수 · CAPEX 비율 · 상각률의 자리를 재지 않았다 — "
          "KR 은 `dart_일괄패널.py --받기`, US 는 `sec_fsds_패널.py --다시풀기`", "참고")

    사유 = {}
    for x in 뺀:
        사유[x[3]] = 사유.get(x[3], 0) + 1
    낸 = {"형식": "기저율 1", "만든날": datetime.date.today().isoformat(), "설정": 설정,
          "입력": {"가정": os.path.abspath(가정경로), "국가": 국, "패널자리": 패널입력["자리"], "패널연도": 패널입력["연도"],
                 "산업분류_회사수": 패널입력["산업분류"]},
          "패널": {"회사연도": len(행), "회사수": len({r["고유번호"] for r in 행}), "정리후_회사연도": len(남),
                 "정리후_회사수": len(넓은), "제외_사유별": 사유, "이익률_표시비율": round(표시비, 4)},
          "대상": 대상,
          "경로": {시: {"해": {str(y): {k2: h[k2] for k2 in ("매출", "영업이익", "영업이익률", "실적", "예측포함", "실적섞임")}
                             for y, h in 경["해"].items()},
                       "영구이익률": 경["영구이익률"]} for 시, 경 in 길.items()},
          "분위표": 분위표, "CAGR자리": 자리표, "이익률드묾": 드묾,
          "평균회귀": {k2: v for k2, v in 회.items() if not k2.startswith("_")}, "대상회귀": 대상회귀, "비율자리": 비율, "신호": 신호,
          "보정": {"상태": 보정상태, "글": 보정글, "패널판": ((보정표 or {}).get("패널") or {}).get("판"),
                 "적용": "비율 자리(10~90% 띠 · 꼬리 판정)만 — CAGR 분위표(3 · 5년 창)는 보정표의 앞날(1 · 2년)과 달라 옮기지 않는다"}}
    낸["패널"]["상세_회사연도"] = 패널입력.get("상세_회사연도", 0)
    # 레터 v27 F5 — 업종 부적합이면 업종 집단 줄에 「싣기가능: false」(레터는 같은 규모 · 전체 집단 백분위로 읽고 각주를 단다)
    분류 = 설정.get("_산업분류") or "KSIC"
    낸["업종적합"] = dict(대상["업종적합"], 표지줄=업종집단표지(낸, {이름 for 이름, _f in 집 if 이름.startswith("%s " % 분류)},
                                                       대상["업종적합"].get("적합")))
    return 낸, ""


def 쓰기(낸, 가정경로, 낼=None):
    p = 낼 or os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw", "기저율.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, "w", encoding="utf-8").write(json.dumps(낸, ensure_ascii=False, indent=1, default=str))
    return p


# ═══════════════════════════════════════════════ 받기 · 씨앗

def 받기(부터, 까지, 설정):
    """KR — 없는 해만 dart_peer_screen 을 공용 자리에서 돌리고, 산업분류를 dart_induty 로 채운다(캐시 우선).
    US — `sec_fsds_패널.py --받기` 에 넘긴다(없는 분기 ZIP 만 받아 풀고 합친다). 국가는 설정 머리 `_국가`(기본 KR)."""
    자리 = 패널자리(설정)
    os.makedirs(자리, exist_ok=True)
    if (설정.get("_국가") or "KR") == "US":
        r = subprocess.run([sys.executable, "-I", os.path.join(여기, "sec_fsds_패널.py"), "--받기", "--자리", 자리,
                            "--부터", str(부터), "--까지", str(까지)])
        return 통과 if r.returncode == 0 else 입력오류
    있음 = 패널파일들(자리)
    화면 = os.path.join(여기, "dart_peer_screen.py")
    for y in range(부터, 까지 + 1):
        if y in 있음:
            print("  %d 있음 — 건너뜀" % y)
            continue
        print("  %d 받기 …" % y)
        r = subprocess.run([sys.executable, "-I", 화면, "--year", str(y)], cwd=자리)
        if r.returncode != 0:
            print("  %d 실패(rc %d) — 멈춘다" % (y, r.returncode))
            return 입력오류
        src = os.path.join(자리, "상장사_주요계정_%d.csv" % y)
        if os.path.exists(src):
            os.replace(src, os.path.join(자리, "주요계정_%d.csv" % y))
        m = os.path.join(자리, "미확보_고유번호.csv")
        if os.path.exists(m):
            os.replace(m, os.path.join(자리, "미확보_고유번호_%d.csv" % y))
    import dart_induty as D                               # noqa: PLC0415
    D.CACHEDIR = os.path.join(자리, "company")
    codes = set()
    for p in 패널파일들(자리).values():
        with io.open(p, encoding="utf-8-sig", newline="") as f:
            codes.update((r.get("고유번호") or "").strip().zfill(8) for r in csv.DictReader(f))
    codes.discard("00000000")
    cf = os.path.join(자리, "패널_고유번호.txt")
    io.open(cf, "w", encoding="utf-8").write("\n".join(sorted(codes)))
    old = sys.argv
    sys.argv = ["dart_induty.py", "--codes-file", cf, "--out", os.path.join(자리, "산업분류.csv")]
    try:
        D.main()
    finally:
        sys.argv = old
    return 통과


def 씨앗(폴더, 설정):
    """이미 받은 패널을 공용 자리로 복사(네트워크 0). 같은 이름이 있으면 덮지 않는다."""
    자리 = 패널자리(설정)
    os.makedirs(자리, exist_ok=True)
    셈 = 0
    for p in glob.glob(os.path.join(폴더, "*.csv")) + glob.glob(os.path.join(폴더, "*.txt")):
        b = os.path.basename(p)
        m = re.match(r"상장사_주요계정_(\d{4})\.csv$", b)
        dst = os.path.join(자리, "주요계정_%s.csv" % m.group(1) if m else b)
        if re.match(r"(주요계정_\d{4}|미확보_고유번호_\d{4}|산업분류|패널_고유번호)\.(csv|txt)$", os.path.basename(dst)) and not os.path.exists(dst):
            shutil.copy2(p, dst)
            셈 += 1
    src = os.path.join(폴더, "company")
    if os.path.isdir(src):
        d = os.path.join(자리, "company")
        os.makedirs(d, exist_ok=True)
        for p in glob.glob(os.path.join(src, "*.json")):
            q = os.path.join(d, os.path.basename(p))
            if not os.path.exists(q):
                shutil.copy2(p, q)
                셈 += 1
    return 자리, 셈


def 표찍기(낸):
    대 = 낸["대상"]
    print("기저율 — 대상 %s(%s · %s) · %s %s · 규모 %s · 마지막 실적 해 %s · 첫 예측 해 %s"
          % (대.get("회사명"), 대["고유번호"], 대.get("국가") or "KR", 대.get("산업분류체계") or "KSIC", 대.get("산업분류"),
             대.get("규모구간"), 대["마지막실적해"], 대["첫예측해"]))
    p = 낸["패널"]
    print("  패널 %d 회사-연도 → 정리 후 %d · 제외 %s · 이익률 표시 %.1f%%"
          % (p["회사연도"], p["정리후_회사연도"], p["제외_사유별"], p["이익률_표시비율"] * 100))
    print("  평균 회귀 — %s" % 낸["평균회귀"]["결론"])
    print("  신호 %d건" % len(낸["신호"]))
    for s in 낸["신호"]:
        print("   · [%s] %s — %s" % (s["등급"], s["종류"], s["글"]))


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="기저율 — 같은 집단의 실제 이력에 가정 경로를 대 본다")
    ap.add_argument("가정", nargs="?")
    ap.add_argument("--회사", help="대상 고유번호(8자리)")
    ap.add_argument("--낼", help="산출 경로(기본: 가정 곁 _raw/기저율.json)")
    ap.add_argument("--받기", action="store_true", help="공용 패널을 받는다(없는 해만 · 네트워크)")
    ap.add_argument("--부터", type=int)
    ap.add_argument("--까지", type=int)
    ap.add_argument("--씨앗", help="이미 받은 패널 폴더를 공용 자리로 복사")
    ap.add_argument("--설정", help="설정 파일(기본: 스크립트 곁 기저율설정.json)")
    ap.add_argument("--국가", help="패널 국가(KR · US). 가정이 있으면 메타.표시통화가 고르고(KRW → KR · USD → US) 이 값은 덮는 것이다. "
                                "--받기 · --씨앗 의 기본은 KR")
    a = ap.parse_args()
    설정 = 설정읽기(a.설정)
    if a.씨앗:
        자리, 셈 = 씨앗(a.씨앗, 국가설정(설정, a.국가 or "KR"))
        print("씨앗 — %d개 파일을 %s 로 복사(이미 있는 것은 건너뜀)" % (셈, 자리))
        return 통과
    if a.받기:
        설정 = 국가설정(설정, a.국가 or "KR")
        return 받기(a.부터 or 설정["패널"]["부터"], a.까지 or (datetime.date.today().year - 1), 설정)
    if not a.가정:
        ap.error("가정 파일 · --받기 · --씨앗 가운데 하나가 필요합니다")
    try:
        가정 = json.load(io.open(a.가정, encoding="utf-8"))
    except (OSError, ValueError) as e:
        print("가정 파일을 못 읽었다 — %s" % e)
        return 입력오류
    낸, 까 = 분석(가정, a.가정, 설정, a.회사, 국가=a.국가)
    if 낸 is None:
        print("입력오류 — %s" % 까)
        return 입력오류
    p = 쓰기(낸, a.가정, a.낼)
    if 낸.get("해당없음"):
        print("기저율 — 해당 없음: %s" % 낸["해당없음"])
    else:
        표찍기(낸)
    print("→ %s" % p)
    return 통과


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""조사축적 — 수집 갈래의 산출(웹 · IR · 증권사 리포트의 축 · 유사기업 · 외부 제약)을 공용 캐시에 쌓고, 다음 사람은 「조사한 시점 뒤」만 본다 (2026-10-24 신설).

왜 만들었나
  공시 원천은 `원천축적.py` 가 쌓는다. 그런데 회차마다 가장 오래 걸리는 것은 수집 갈래 — B1(매출 스트림 웹 조사 · 회사 IR · 컨퍼런스콜 ·
  증권사 모델의 틀) · B2(스트림 심화) · C1 · C2(유사기업 후보 · 재료) · D(외부 제약) · F(투자 능력) · A3(동인 원천)다. 이 산출은 조사일과
  출처 날짜가 붙은 근거라, 쌓아 두면 다음 사람은 그 갈래가 본 가장 늦은 출처 날짜(출처 as-of) 뒤에 나온 자료만 보면 된다
  (2026-10-23 · 24 결정).

무엇을 쌓나 — **갈래 산출(근거)만.** 축 후보 · 신뢰도 · 출처 목록 · 유사기업 후보표 · 외부 제약 항목은 조사 산출이라 쌓는다.
  가정 값 · 판정 · 원고(본선의 `축배선.json` · 동인 지도 · 동인 진단 · 가정 파일 · 레터 원고 · 신호 도구 산출)는 쌓지 않는다 — 키트 공용 캐시 원칙
  「종목 고유의 판단 값은 공용으로 두지 않는다」. 유사기업 갈래가 받은 시세 · 재무 재료(일 · 주 시세 · 주식 수 · 부채 · frame 따위)는
  「재료」로 쌓되 **배포 묶음에서 뺀다**(재배포 조건이 제공처마다 다르다). 다른 회사의 개념 추출(`cc_<티커>.json`)은 `원천축적.py` 종목풀이 맡는다.
  리포트 원문 · 긴 인용은 산출에 없어야 한다(저작권 — 리포트는 축만 가져온다) — 넣기가 긴 인용 칸을 경보한다(`설정.인용문턱` · `글문턱`).

자리 — `<공용>/조사/<KR|US|TW>/<코드>/` (공용 = 환경변수 `DCF_공용캐시` · 없으면 `~/.dcf캐시`)
  목록.json     꼴의 판 · 국가 · 종목 · 회사명 · 갈래마다 {조사일 · 평가기준일 · 출처asof · 출처날짜수 · 리포트식별수 · 키트판 · 넣은날 · 넣은곳 ·
                파일{상대: sha256 · 크기 · 분류(조사 · 재료) · 배포} · 경보} · 이력
  <갈래>/…      그 갈래의 파일(`_raw/` 상대 경로 그대로 · 키트 뿌리의 `유사기업_후보.md` 는 `C1/^유사기업_후보.md`)
  이력/<갈래>/<조사일>/…   더 새 조사가 들어와 바뀐 옛 파일

출처 as-of — 그 갈래 산출의 글 속 날짜(YYYY-MM-DD · YYYY.MM.DD · YYYY년 M월 D일 · 달만 있으면 그달 1일) 가운데 **조사일 이하의 가장 늦은 값**.
  머리 칸(조사일 · 조회일 · 끝난시각 · 만든날 · 평가기준일)은 세지 않는다. 다음 이어 조사는 이 날짜 뒤만 보면 된다(달만 적힌 출처가 있어 보수적으로
  그달 1일 — 그달을 한 번 더 본다). 날짜가 하나도 없으면 평가기준일 · 조사일 차례로.

명령
  python 스크립트/조사축적.py 넣기 --국가 KR --종목 000660 --raw <회차>/키트/_raw        # 회차의 수집 산출을 캐시에(네트워크 0)
  python 스크립트/조사축적.py 씨앗 --국가 KR --종목 000660 --raw <새 회차>/키트/_raw [--덮어쓰기] [--재료빼기] [--낡음일 90]
  python 스크립트/조사축적.py 정리 (--국가 KR --종목 000660 | --모두 [--국가 KR])      # 쌓인 C1 · C2 를 지금 규칙으로 다시 짓기(옛 파일은 이력/)
  python 스크립트/조사축적.py 세율다시 (--국가 KR --종목 000660 | --모두) [--보기] [--json 경로]   # 쌓인 C2 βU 를 단일 출처 세율로 다시 셈(표본 그대로 · 옛 파일은 이력/)
  (정리 · 넣기는 조사 산출에 「평가기준일 뒤 정보」 표지도 단다 — `기준일뒤.py` · 갈래마다 `기준일뒤` 셈 · 바꾼 파일의 옛것은 이력/기준일표지_<날>/)
  python 스크립트/조사축적.py 교차 (--국가 KR --종목 000660 | --모두 [--국가 KR]) [--json 경로]   # 쌓인 F 끼리 같은 시설 후보 표시(넣기가 F 를 넣을 때도 돈다)
  python 스크립트/조사축적.py 상태 [--국가 KR] [--유니버스 유니버스.csv [--판정 대상]] [--json 경로]
  python 스크립트/조사축적.py 이어조사목록 [--유니버스 유니버스.csv [--판정 대상]] [--갈래 B1,B2,C1,C2,D,F,A3] [--json 경로]

유사기업 재료의 범위(2026-10-24) — 회사 하나의 재료 파일(day_ · wk_ · sise_ · shares_ · sub_ · cf_ · 표지_ · item1_ … · peers/fs · company · shares 의
  고유번호 파일)은 그 회차 `peers/핵심표본.json` 의 회사(핵심 · 예비 · 운영동종전용 · 컷통과)와 대상 것만 줍는다. 키트 사본에 남은 다른 회사 캐시 ·
  표본에 못 든 싼층 후보의 재료는 줍지 않고(`목록.표본거름`), 이미 쌓인 것은 `정리` 가 `이력/표본밖_<날>/` 로 옮긴다(지우지 않는다).
병합 — 같은 갈래가 더 늦거나 같은 조사일로 들어오면 그 갈래를 통째로 바꾸고(바뀐 옛 파일은 `이력/`), 더 이른 조사일이면 캐시에 없는 파일만
  더한다(옛 회차를 넣어도 새 조사를 덮지 않는다). 씨앗은 회차 `_raw/조사축적_씨앗.json` 에 「공용 캐시에서 가져왔다 · 조사일 · 출처 as-of」 를 남기고,
  조사일이 `--낡음일`(기본 90일)보다 오래된 갈래는 「낡음 — 이어 조사(출처 as-of 뒤만)」 를 알린다.
유니버스 교차(2026-10-25 FX-D · R12) — 그룹 공동 시설을 두 회사 F 가 각각 세고, 지주가 상장 자회사의 투자계획 줄을 자기 프로젝트로 쓸어 담는다
  (유니버스 F 물결 실측). 넣기가 F 를 넣으면 캐시 안 다른 회사 F 와 견줘 **같은 시설 후보**(총액 ±1% · 통화 같음 · 이름 두 글자 짝 닮음 0.25 이상 —
  한쪽 총액이 비면 닮음 0.5 · 능력단위는 같은 단위 + 닮음 0.5 · 정규화 6글자 미만의 일반 이름은 총액 ±0.1% 일 때만)를 두 쪽 F 의 `프로젝트[] · 능력단위[]` 에 `유니버스중복[]`(상대 · 상대항목 · 근거)으로,
  목록에 `유니버스중복[]` 로 적는다. 값은 고치지 않는다 — 어느 쪽 몫인지(지분율 · 연결 범위)는 본선 판단. 바뀐 F 의 옛것은 `이력/교차_<날>/`.
회사 · 업종 이름은 이 도구에 없다(범용). 종료 코드 — 0 통과 · 1 발견(넣을 것 없음 · 긴 인용 경보 · 이어 조사할 갈래 있음) · 2 입력오류.
"""
from __future__ import annotations

import argparse
import calendar
import csv
import datetime
import hashlib
import io
import json
import os
import re
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류  # noqa: E402

형식 = "조사축적 1"
국가들 = ("KR", "US", "TW")

설정 = {
    "낡음일": 90,                       # 조사일이 이보다 오래되면 「낡음 — 이어 조사」
    "인용문턱": 300,                    # 인용 · 원문 · 발화 꼴 칸의 글이 이보다 길면 경보(저작권 — 리포트는 축만)
    "공시인용문턱": 1200,               # 같은 줄에 공시 접수번호(원문접수 · accession)가 붙은 원문 인용 — 회사 자기 공시라 D 갈래 문턱과 같게(2026-10-24 W17)
    "글문턱": 2000,                     # 어느 칸이든 글이 이보다 길면 경보
    "필수갈래": ["A3", "B1", "B2", "C1", "C2", "D", "F"],
}

# ── 갈래마다 산출 파일(`_raw/` 상대 경로) — 정본은 키트 `.claude/갈래/*.md` 와 `가정_스키마.md` 「갈래 산출물」
갈래꼴 = [
    ("B1", [r"매출스트림_웹조사\.json", r"매출스트림_웹조사_B1\.json"]),
    ("B2", [r"매출스트림_심화\.json"]),
    ("A3", [r"동인원천\.json"]),
    ("D", [r"외부제약\.json", r"조문_[^/]+\.json"]),
    ("F", [r"투자능력\.json"]),
]
뿌리파일 = {"유사기업_후보.md": "C1"}                    # 키트 뿌리(= `_raw` 의 부모)에 놓이는 갈래 산출
# 2026-10-24 W17 — 국내 유사기업 도구(peer_조립 · dart_fs_all · dart_shares · dart_induty · dart_peer_screen)가 키트 뿌리에 쓰는 표(LS ELECTRIC 조사 —
# 넣기가 못 주웠다). 시세 · 재무를 담은 표라 재료(배포 제외)로 쌓는다
뿌리꼴 = [(re.compile(r"^유사기업_재료_.+[.]csv$"), "C2"),
         (re.compile(r"^(전체재무_추출|주식수|산업분류|산업분류_전수)[.]csv$"), "C2"),
         (re.compile(r"^상장사_주요계정_.+[.]csv$"), "C1")]
재료꼴 = re.compile(r"^(day|wk|week|sise|vol|shares|debt|sub|frame|fx|환율|ads|price|주봉|일봉|cf|표지|종가|종가상세)_", re.I)   # 유사기업 시세 · 재무 재료(배포 제외)
# 2026-10-24 W17 — 회사 하나의 재료 파일(이름 둘째 마디가 종목코드 · 티커)과 회사별 하위 폴더(DART 고유번호 8자리로 시작). 넣기는 그 회차 C1 표본
# (`peers/핵심표본.json` — 핵심 · 예비 · 운영동종전용 · 컷통과)과 대상 자신의 것만 줍는다. 키트 사본에 남아 있던 다른 회사 캐시를 그 회사 C2 로
# 쓸어 담던 결함(한화솔루션 조사 — C2 316 파일). 지수 시세(KOSPI · KOSDAQ · _INX)는 공용이라 줍는다
회사파일꼴 = re.compile(r"^(day|wk|week|sise|vol|shares|debt|sub|fx|ads|price|주봉|일봉|cf|item1|표지)_(.*?)(?:_.*)?[.]json$", re.I)
지수이름 = {"", "KOSPI", "KOSDAQ", "KOSPI200", "KS11", "KQ11", "KS200", "INX", "_INX", "SPX", "GSPC", "^GSPC", "NDX", "TWII", "TAIEX"}
고유번호폴더 = ("fs", "company", "shares")
# 2026-10-25 FX4-P — `C2_상태.json` · `C2_차입금_확정*.json` 도 C2 다(종전에는 C1 로 들어가 C2 를 다시 셈해 넣어도 C2 조사일이 옛 날짜로 남았다 · C2 다시 셈 2조)
C2꼴 = re.compile(r"^(βU|BU|beta|운영지표|유사기업거리|C2_)", re.I)
peers뺄꼴 = re.compile(r"^(cc_.+\.json|company_tickers\.json|.+\.log)$", re.I)     # 종목풀(원천축적) · 공개 명단 · 로그
머리칸 = {"조사일", "조회일", "끝난시각", "만든날", "평가기준일", "일시", "넣은날"}
인용칸꼴 = re.compile(r"(인용|원문|발화|표현|전문|quote|text|transcript)", re.I)


def 공용뿌리():
    return (os.environ.get("DCF_공용캐시") or os.environ.get("DCF_SHARED_CACHE")
            or os.path.join(os.path.expanduser("~"), ".dcf캐시"))


def 조사뿌리():
    return os.path.join(공용뿌리(), "조사")


def 종목정리(국가, 종목):
    s = ("%s" % 종목).strip()
    return s.zfill(6) if 국가.upper() == "KR" and s.isdigit() else s.upper()


def 회사자리(국가, 종목):
    return os.path.join(조사뿌리(), 국가.upper(), 종목정리(국가, 종목))


def _지금():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def _해시(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for 덩 in iter(lambda: f.read(1 << 20), b""):
            h.update(덩)
    return h.hexdigest()


def _읽기(p, 기본=None):
    try:
        with io.open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return 기본


def _쓰기(p, 것):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    임 = p + ".쓰는중"
    with io.open(임, "w", encoding="utf-8") as f:
        json.dump(것, f, ensure_ascii=False, indent=1)
    os.replace(임, p)


def 키트판():
    v = _읽기(os.path.join(os.path.dirname(여기), "버전.json")) or {}
    return {k: v.get(k) for k in ("ADDER", "가정스키마") if v.get(k) is not None} or None


# ══════════════════════════════════════════════════════════ 갈래 가르기

def 갈래목록(raw):
    """회차 `_raw/` → [(갈래, 상대경로, 분류, 원본경로)] — 분류: 조사 · 재료. 판단 산출(축배선 · 동인 지도 · 가정 · 원고 · 신호 도구)은 담지 않는다."""
    낸 = []
    if not os.path.isdir(raw):
        return 낸
    for 갈, 꼴들 in 갈래꼴:
        cs = [re.compile("^%s$" % x) for x in 꼴들]
        for 이름 in sorted(os.listdir(raw)):
            p = os.path.join(raw, 이름)
            if os.path.isfile(p) and any(c.match(이름) for c in cs):
                낸.append((갈, 이름, "조사", p))
    pd = os.path.join(raw, "peers")
    if os.path.isdir(pd):
        for 뿌, _ds, fs in os.walk(pd):
            for 이름 in sorted(fs):
                if peers뺄꼴.match(이름):
                    continue
                p = os.path.join(뿌, 이름)
                상 = os.path.relpath(p, raw).replace(os.sep, "/")
                낸.append(peers가르기(상) + (p,))
    bd = os.path.join(raw, "베타회귀")
    if os.path.isdir(bd):
        for 이름 in sorted(os.listdir(bd)):
            p = os.path.join(bd, 이름)
            if os.path.isfile(p):
                낸.append(("C2", "베타회귀/" + 이름, "재료", p))
    부모 = os.path.dirname(os.path.abspath(raw))
    for 이름, 갈 in 뿌리파일.items():
        p = os.path.join(부모, 이름)
        if os.path.isfile(p):
            낸.append((갈, "^" + 이름, "조사", p))
    for 이름 in sorted(os.listdir(부모)) if os.path.isdir(부모) else []:
        p = os.path.join(부모, 이름)
        갈 = next((g for c, g in 뿌리꼴 if c.match(이름)), None)
        if 갈 and os.path.isfile(p):
            낸.append((갈, "^" + 이름, "재료", p))
    return 낸


def peers가르기(상):
    """`peers/…` 상대 경로 → (갈래, 상대, 분류). 하위 폴더(fs · company · shares — DART 회사별 재무 · 주식수)와 사업 발췌(item1_)는 재료다
    (2026-10-24 W17 — 종전에는 C1 조사로 들어가 배포 묶음에 섞였다)."""
    마디 = 상.split("/")
    이름 = 마디[-1]
    if len(마디) > 2:
        return ("C2", 상, "재료")
    if 이름.lower().startswith("item1_"):
        return ("C1", 상, "재료")
    if 재료꼴.match(이름):
        return ("C2", 상, "재료")
    if C2꼴.match(이름):
        return ("C2", 상, "조사")
    return ("C1", 상, "조사")


def 회사열쇠(상):
    """`peers/…` 상대 경로 → ("종목", 열쇠) · ("고유", 8자리) · None(회사 하나의 파일이 아니다 — 지수 · 단면 · 표본 산출)."""
    마디 = 상.split("/")
    if len(마디) > 2 and 마디[-2] in 고유번호폴더:
        m = re.match(r"^(\d{8})", 마디[-1])
        return ("고유", m.group(1)) if m else None
    m = 회사파일꼴.match(마디[-1])
    if not m:
        return None
    열 = m.group(2).upper()
    if 열 in 지수이름 or 열.startswith("_") or 열.startswith("^"):
        return None
    return ("종목", 열)


def 회차표본(peers자리, 종목=None, 회사폴더들=None):
    """회차 `peers/` → (종목 열쇠 집합, 고유번호 집합, 기준 글). 표본 = `핵심표본.json` 의 모든 회사(핵심표본읽기 — 핵심 · 예비 · 운영동종전용 ·
    컷통과) + 대상. 핵심표본이 없으면 None(거르지 않는다)."""
    p = os.path.join(peers자리, "핵심표본.json")
    h = _읽기(p)
    if h is None:
        return None
    try:
        import 핵심표본읽기 as _hr
        표 = _hr.구분표(h)
    except Exception:                                    # noqa: BLE001
        표 = {}
    열 = {("%s" % k).upper() for k in 표}
    고 = set()
    for v in 표.values():
        행 = v.get("행") if isinstance(v, dict) else None
        if isinstance(행, dict) and 행.get("고유번호"):
            고.add(("%s" % 행["고유번호"]).zfill(8))
    if 종목:
        s = ("%s" % 종목).strip().upper()
        열.add(s)
        if s.isdigit():
            열.add(s.zfill(6))
    for d in 회사폴더들 or [os.path.join(peers자리, "company")]:   # 고유번호 ↔ 종목코드 — DART company 응답의 stock_code
        if os.path.isdir(d):
            for f in os.listdir(d):
                j = _읽기(os.path.join(d, f)) or {}
                if isinstance(j, dict) and ("%s" % (j.get("stock_code") or "")).strip() in 열 and j.get("corp_code"):
                    고.add(("%s" % j["corp_code"]).zfill(8))
    return 열, 고, "핵심표본.json %d곳 + 대상" % len(표)


def 표본거름(목록, 표본):
    """[(갈, 상, 분류, p)] → (남, 뺀). 표본 None 이면 그대로."""
    if 표본 is None:
        return 목록, []
    열, 고, _ = 표본
    남, 뺀 = [], []
    for x in 목록:
        상 = x[1]
        k = 회사열쇠(상) if 상.startswith("peers/") else None
        if k and ((k[0] == "종목" and k[1] not in 열) or (k[0] == "고유" and k[1] not in 고)):
            뺀.append(x)
        else:
            남.append(x)
    return 남, 뺀


# ══════════════════════════════════════════════════════════ 날짜 · 경보

_날짜꼴 = [
    (re.compile(r"(?<!\d)(20\d\d)-(\d{1,2})-(\d{1,2})(?!\d)"), "일"),
    (re.compile(r"(?<!\d)(20\d\d)\.(\d{1,2})\.(\d{1,2})(?!\d)"), "일"),
    (re.compile(r"(?<!\d)(20\d\d)/(\d{1,2})/(\d{1,2})(?!\d)"), "일"),
    (re.compile(r"(?<!\d)(20\d\d)년\s?(\d{1,2})월\s?(\d{1,2})일"), "일"),
    (re.compile(r"(?<!\d)(20\d\d)년\s?(\d{1,2})월(?!\s?\d{1,2}일)"), "달"),
    (re.compile(r"(?<!\d)(20\d\d)-(\d{2})(?![-\d])"), "달"),
]


def 글날짜들(글):
    """글 속 날짜 → [date]. 달만 있으면 그달 1일."""
    낸 = []
    for 꼴, 종 in _날짜꼴:
        for m in 꼴.finditer(글 or ""):
            try:
                y, mo = int(m.group(1)), int(m.group(2))
                d = int(m.group(3)) if 종 == "일" else 1
                if 1 <= mo <= 12 and 1 <= d <= calendar.monthrange(y, mo)[1]:
                    낸.append(datetime.date(y, mo, d))
            except (ValueError, IndexError):
                continue
    return 낸


def _날짜(v):
    """머리 칸 값(ISO · 'YYYY-MM-DD HH:MM' · 'YYYY-MM-DDTHH:MM') → date | None."""
    if not isinstance(v, str):
        return None
    m = re.match(r"^\s*(\d{4})-(\d{2})-(\d{2})", v)
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _공시줄인가(x):
    """그 줄이 공시 원문 인용인가 — 원문접수(접수번호 14자리) · accession 이 붙어 있다(AMD 조사 — D 는 1,200자, 축적은 300자에서 경보해 갈렸다)."""
    if not isinstance(x, dict):
        return False
    접 = "%s" % (x.get("원문접수") or x.get("접수번호") or x.get("rcept_no") or "")
    return bool(re.match(r"^[0-9]{14}$", 접.strip())) or bool(x.get("accn") or x.get("accession") or x.get("accessionNumber"))


def _훑기(x, 경로, 칸, 낸글, 경보, 공시=False):
    if isinstance(x, dict):
        공 = 공시 or _공시줄인가(x)
        for k, v in x.items():
            _훑기(v, "%s.%s" % (경로, k) if 경로 else "%s" % k, "%s" % k, 낸글, 경보, 공)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            _훑기(v, "%s[%d]" % (경로, i), 칸, 낸글, 경보, 공시)
    elif isinstance(x, str):
        if 칸 not in 머리칸:
            낸글.append(x)
        n = len(x)
        문턱 = 설정["공시인용문턱"] if 공시 else 설정["인용문턱"]
        if (인용칸꼴.search(칸 or "") and n > 문턱) or n > 설정["글문턱"]:
            경보.append("긴 글 %d자 — %s" % (n, 경로[:120]))


def _제출날(r):
    """원문읽음 한 줄 → 제출일(date) — `제출일` 칸, 없으면 국내 접수번호(YYYYMMDD + 6자리)의 앞 8자리."""
    x = _날짜(r.get("제출일"))
    if x:
        return x
    m = re.match(r"^(\d{4})(\d{2})(\d{2})\d{6}$", "%s" % (r.get("접수") or r.get("접수번호") or ""))
    if m:
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    return None


def 원문읽음날(d):
    """A3 처럼 `원문읽음[]`(기준일보고서 표지 · 역할)을 가진 산출 → 출처 시점(date) | None.
    값을 낸 기준일 보고서의 제출일 — 없으면 기준일까지의 기간을 담은 원문 가운데 가장 늦은 제출일. 「뒤」 역할(기준일 뒤 첫 공시를 대조용으로 받은 것)은
    출처 시점이 아니다(R14 — 2026-10-25: NVDA · ORCL · MRVL 의 A3 출처가 기준일 뒤 10-Q 제출일로 찍혔다)."""
    rs = [r for r in (d.get("원문읽음") or []) if isinstance(r, dict)] if isinstance(d, dict) else []
    if not rs or not any("기준일보고서" in r for r in rs):
        return None
    기준 = [_제출날(r) for r in rs if r.get("기준일보고서") and _제출날(r)]
    if 기준:
        return max(기준)
    기준일 = _날짜(d.get("재무기준일")) or _날짜(d.get("평가기준일"))     # 2026-10-25 날짜 둘 — 원문의 기간은 재무기준일까지(없으면 평가기준일 = 옛 꼴)
    앞 = [_제출날(r) for r in rs if (r.get("역할") or r.get("기준일과")) != "뒤" and _제출날(r)
         and (not 기준일 or not _날짜(r.get("기간끝")) or _날짜(r.get("기간끝")) <= 기준일)]
    return max(앞) if 앞 else None


def 파일읽기(p):
    """→ (머리{조사일 · 평가기준일} · 글 날짜들 · 리포트 식별 수 · 경보). `원문읽음[]` 을 가진 산출(A3)은 글 날짜 대신 그 출처 시점 하나."""
    머리, 글들, 경보 = {}, [], []
    if p.lower().endswith(".json"):
        d = _읽기(p)
        if isinstance(d, dict):
            # 2026-10-25 FX4-P — 머리 칸이 `머리{}` 안에 있는 산출(βU 조립 · 병합)도 본다 · 상태 파일은 완료시각이 조사일보다 늦으면 그것
            후보머리 = [d] + ([d["머리"]] if isinstance(d.get("머리"), dict) else [])
            _날들 = [x.get(k) for x in 후보머리 for k in ("조사일", "조회일", "끝난시각", "만든날", "완료시각") if _날짜(x.get(k))]
            if _날들:
                머리["조사일"] = max(_날들, key=lambda v: _날짜(v))
            if _날짜(d.get("평가기준일")):
                머리["평가기준일"] = d["평가기준일"][:10]
            if _날짜(d.get("재무기준일")):                    # 2026-10-25 날짜 둘 — 산출이 적었을 때만(없으면 F = T)
                머리["재무기준일"] = d["재무기준일"][:10]
            원날 = 원문읽음날(d)
            if 원날:
                머리["원문읽음날"] = 원날.isoformat()
                _훑기(d, "", "", 글들, 경보)
                본 = "\n".join(글들)
                리 = len(set(re.findall(r"(?:report_idx|nid)\s*[=:]\s*\"?(\d+)", 본)))
                return 머리, [원날], 리, 경보
        if d is not None:
            _훑기(d, "", "", 글들, 경보)
    else:
        try:
            t = io.open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            t = ""
        글들.append(t)
        for i, l in enumerate(t.splitlines()):
            if len(l) > 설정["글문턱"]:
                경보.append("긴 줄 %d자 — %d행" % (len(l), i + 1))
    본 = "\n".join(글들)
    리 = len(set(re.findall(r"(?:report_idx|nid)\s*[=:]\s*\"?(\d+)", 본)))
    return 머리, 글날짜들(본), 리, 경보


def 갈래요약(파일들):
    """[(상대, 분류, 원본)] → {조사일 · 평가기준일 · 출처asof · 출처날짜수 · 리포트식별수 · 경보}."""
    조사일들, 기준일, 날들, 리, 경보 = [], None, [], 0, []
    재무 = None
    for 상, 분류, p in 파일들:
        if 분류 != "조사":
            continue
        머, 날, r, 경 = 파일읽기(p)
        if 머.get("조사일"):
            조사일들.append(머["조사일"])
        기준일 = 기준일 or 머.get("평가기준일")
        재무 = 재무 or 머.get("재무기준일")
        날들 += 날
        리 += r
        경보 += ["%s — %s" % (상, x) for x in 경]
    if not 조사일들:
        조사일들 = [datetime.datetime.fromtimestamp(max(os.path.getmtime(p) for _, _, p in 파일들)).replace(microsecond=0).isoformat()]
    조사일 = max(조사일들)
    끝 = _날짜(조사일)
    쓸 = sorted(d for d in 날들 if 끝 is None or d <= 끝)
    asof = 쓸[-1].isoformat() if 쓸 else (기준일 or 조사일[:10])
    낸 = {"조사일": 조사일, "평가기준일": 기준일, "출처asof": asof, "출처날짜수": len(쓸), "리포트식별수": 리, "경보": 경보[:20]}
    if 재무 and 재무 != 기준일:                               # 2026-10-25 날짜 둘 — 재무기준일이 따로 있을 때만 적는다(옛 목록 꼴 그대로)
        낸["재무기준일"] = 재무
    return 낸


# ══════════════════════════════════════════════════════════ 넣기 · 씨앗

def _갈래파일자리(자리, 갈, 상):
    return os.path.join(자리, 갈, 상.replace("/", os.sep))


def 넣기(국가, 종목, raw, 조용=False):
    """회차 `_raw/`(와 그 부모의 갈래 파일)의 수집 산출을 캐시에 → 요약 dict. 네트워크 0."""
    국가 = 국가.upper()
    if 국가 not in 국가들:
        raise ValueError("국가는 %s 가운데 — %s" % (" · ".join(국가들), 국가))
    목록 = 갈래목록(raw)
    표본 = 회차표본(os.path.join(raw, "peers"), 종목정리(국가, 종목))
    목록, 걸러짐 = 표본거름(목록, 표본)
    걸러진상 = {x[1] for x in 걸러짐}
    if not 목록:
        if not 조용:
            print("넣기 %s %s — 넣을 갈래 산출이 없다(%s)" % (국가, 종목정리(국가, 종목), raw))
        return {"국가": 국가, "종목": 종목정리(국가, 종목), "갈래": {}, "경보": [], "넣은갈래": 0}
    자리 = 회사자리(국가, 종목)
    목p = os.path.join(자리, "목록.json")
    목 = _읽기(목p) or {"형식": 형식, "국가": 국가, "종목": 종목정리(국가, 종목), "갈래": {}, "이력": []}
    if 목.get("형식") != 형식:
        raise ValueError("캐시 목록의 꼴이 다르다(%s ≠ %s)" % (목.get("형식"), 형식))
    if not 목.get("회사명"):
        for 상 in ("매출스트림_웹조사.json", "외부제약.json", "동인원천.json"):
            d = _읽기(os.path.join(raw, 상)) or {}
            if isinstance(d, dict) and isinstance(d.get("회사"), str):
                목["회사명"] = d["회사"]
                break
    묶 = {}
    for 갈, 상, 분류, p in 목록:
        묶.setdefault(갈, []).append((상, 분류, p))
    지금 = _지금()
    낸 = {"국가": 국가, "종목": 목["종목"], "자리": 자리, "갈래": {}, "경보": []}
    for 갈, 파일들 in sorted(묶.items()):
        요 = 갈래요약(파일들)
        옛 = 목["갈래"].get(갈)
        새것 = (옛 is None) or (요["조사일"] >= (옛.get("조사일") or ""))
        더, 바, 같, 둠 = 0, 0, 0, 0
        옛파일 = (옛 or {}).get("파일") or {}
        새파일 = dict(옛파일) if 옛 else {}
        if 새것 and 옛:                                          # 그 갈래를 통째로 바꾼다 — 바뀌거나 없어진 옛 파일은 이력으로
            들어온 = {상: p for 상, _, p in 파일들}
            for 상, v in 옛파일.items():
                p = _갈래파일자리(자리, 갈, 상)
                if not os.path.exists(p) or (상 in 들어온 and _해시(들어온[상]) == v.get("sha256")):
                    continue
                if (옛.get("조사일") or "") != 요["조사일"]:     # 다른 조사의 파일만 이력에 남긴다(같은 조사를 다시 넣으면 그냥 바꾼다)
                    ip = os.path.join(자리, "이력", 갈, re.sub(r"[^0-9T]", "", 옛.get("조사일") or "옛"), 상.replace("/", os.sep))
                    os.makedirs(os.path.dirname(ip), exist_ok=True)
                    shutil.move(p, ip)
                if 상 not in 들어온:
                    if os.path.exists(p) and 상 in 걸러진상:      # 표본 밖 회사 재료 — 지우지 않고 이력으로(2026-10-24 W17)
                        ip = os.path.join(자리, "이력", "표본밖_" + datetime.date.today().strftime("%Y%m%d"), 갈, 상.replace("/", os.sep))
                        os.makedirs(os.path.dirname(ip), exist_ok=True)
                        shutil.move(p, ip)
                    elif os.path.exists(p):
                        os.remove(p)
                    새파일.pop(상, None)
        for 상, 분류, p in 파일들:
            h = _해시(p)
            o = 옛파일.get(상)
            if o and o.get("sha256") == h:
                같 += 1
                continue
            if o and not 새것:
                둠 += 1                                          # 옛 조사가 들어왔다 — 캐시의 새 조사를 덮지 않는다
                continue
            dst = _갈래파일자리(자리, 갈, 상)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(p, dst)
            새파일[상] = {"sha256": h, "크기": os.path.getsize(p), "분류": 분류, "배포": 분류 == "조사"}
            if o:
                바 += 1
            else:
                더 += 1
        if 새것:
            목["갈래"][갈] = dict(요, 키트판=키트판(), 넣은날=지금, 넣은곳=os.path.abspath(raw), 파일=새파일)
        else:
            (목["갈래"][갈])["파일"] = 새파일
        낸["갈래"][갈] = {"조사일": (목["갈래"][갈]).get("조사일"), "출처asof": (목["갈래"][갈]).get("출처asof"),
                         "더함": 더, "바꿈": 바, "같음": 같, "옛것이라둠": 둠, "새조사": 새것}
        낸["경보"] += ["%s %s" % (갈, x) for x in 요["경보"]]
        목["이력"].append({"일시": 지금, "동작": "넣기", "갈래": 갈, "조사일": 요["조사일"], "출처asof": 요["출처asof"],
                         "더함": 더, "바꿈": 바, "같음": 같, "옛것이라둠": 둠, "넣은곳": os.path.abspath(raw)})
    if 표본 is not None:
        목["표본거름"] = {"일시": 지금, "기준": 표본[2], "뺀파일": len(걸러짐),
                       "뺀회사": sorted({"%s" % 회사열쇠(x[1])[1] for x in 걸러짐})[:60]}
        낸["표본밖"] = len(걸러짐)
    _쓰기(목p, 목)
    낸["기준일뒤"] = 기준일표지(국가, 목["종목"], 갈래들=sorted(낸["갈래"]), 조용=True)["갈래"]
    if "F" in 낸["갈래"]:                                         # 2026-10-25 FX-D — 같은 시설 후보 교차 표시(R12)
        낸["유니버스중복"] = 유니버스교차(국가, 목["종목"], 조용=True)["짝"]
    낸["넣은갈래"] = len(낸["갈래"])
    if not 조용:
        print("넣기 %s %s — %s%s" % (국가, 목["종목"], " · ".join(
            "%s(조사 %s · 출처 %s · 더함 %d · 바꿈 %d · 같음 %d%s)" % (g, (v["조사일"] or "")[:10], v["출처asof"], v["더함"], v["바꿈"], v["같음"],
                                                          " · 옛것이라 둠 %d" % v["옛것이라둠"] if v["옛것이라둠"] else "")
            for g, v in sorted(낸["갈래"].items())), (" · 경보 %d" % len(낸["경보"])) if 낸["경보"] else ""))
        for x in 낸["경보"][:10]:
            print("  경보 — %s" % x)
        if 걸러짐:
            print("  표본 밖 회사 재료 %d개는 줍지 않음(%s) — 회사 %s" % (len(걸러짐), 표본[2], ", ".join(목["표본거름"]["뺀회사"][:12])))
        elif 표본 is None:
            print("  핵심표본.json 이 없어 회사별 재료를 표본으로 거르지 않았다")
        if 낸.get("유니버스중복"):
            print("  유니버스 교차 — 같은 시설 후보 %d짝(두 쪽 F 의 `유니버스중복` · 어느 쪽 몫인지는 본선 판단): %s" % (len(낸["유니버스중복"]), " · ".join(
                "%s 「%s」" % (z["상대"], z["상대항목"][:24]) for z in 낸["유니버스중복"][:4])))
    return 낸


def 정리(국가, 종목, 조용=False):
    """이미 쌓인 한 회사의 C1 · C2 를 지금 규칙으로 다시 짓는다(2026-10-24 W17) — ① 표본 밖 회사 재료는 `이력/표본밖_<날>/` 로 옮긴다
    (지우지 않는다) ② 분류가 바뀐 파일(하위 폴더 · item1 · cf · 표지 · 종가 — 재료)은 그 갈래 · 분류로 옮긴다. 표본은 캐시의 C1 `peers/핵심표본.json`."""
    국가 = 국가.upper()
    자리 = 회사자리(국가, 종목)
    목p = os.path.join(자리, "목록.json")
    목 = _읽기(목p)
    if not 목:
        return {"국가": 국가, "종목": 종목정리(국가, 종목), "까닭": "캐시에 없다"}
    표본 = 회차표본(os.path.join(자리, "C1", "peers"), 목.get("종목") or 종목정리(국가, 종목),
                [os.path.join(자리, 갈, "peers", "company") for 갈 in ("C1", "C2")])
    오늘 = datetime.date.today().strftime("%Y%m%d")
    옮김, 뺌, 바꿈 = 0, [], 0
    for 갈 in ("C1", "C2"):
        g = (목.get("갈래") or {}).get(갈)
        if not g:
            continue
        for 상, v in sorted(list((g.get("파일") or {}).items())):
            if not 상.startswith("peers/"):
                continue
            src = _갈래파일자리(자리, 갈, 상)
            k = 회사열쇠(상)
            if 표본 is not None and k and ((k[0] == "종목" and k[1] not in 표본[0]) or (k[0] == "고유" and k[1] not in 표본[1])):
                if os.path.exists(src):
                    ip = os.path.join(자리, "이력", "표본밖_" + 오늘, 갈, 상.replace("/", os.sep))
                    os.makedirs(os.path.dirname(ip), exist_ok=True)
                    shutil.move(src, ip)
                g["파일"].pop(상, None)
                뺌.append(k[1])
                continue
            새갈, _, 새분 = peers가르기(상)
            if (새갈, 새분) == (갈, v.get("분류")):
                continue
            if 새갈 != 갈:
                dst = _갈래파일자리(자리, 새갈, 상)
                if os.path.exists(src):
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.move(src, dst)
                ng = 목["갈래"].setdefault(새갈, {k2: g.get(k2) for k2 in ("조사일", "평가기준일", "재무기준일", "출처asof", "출처날짜수",
                                                                        "리포트식별수", "키트판", "넣은날", "넣은곳") if k2 in g})
                ng.setdefault("파일", {})[상] = dict(v, 분류=새분, 배포=새분 == "조사")
                g["파일"].pop(상, None)
                옮김 += 1
            else:
                g["파일"][상] = dict(v, 분류=새분, 배포=새분 == "조사")
                바꿈 += 1
    낸 = {"국가": 국가, "종목": 목.get("종목"), "기준": 표본[2] if 표본 else "핵심표본 없음 — 표본으로 거르지 않음",
         "표본밖": len(뺌), "표본밖회사": sorted(set(뺌))[:60], "갈래옮김": 옮김, "분류바꿈": 바꿈}
    if len(뺌) or 옮김 or 바꿈:
        목.setdefault("이력", []).append({"일시": _지금(), "동작": "정리", "표본밖": len(뺌), "갈래옮김": 옮김, "분류바꿈": 바꿈,
                                       "기준": 낸["기준"], "옮긴곳": "이력/표본밖_" + 오늘 if 뺌 else None})
        if 표본 is not None:
            목["표본거름"] = {"일시": _지금(), "기준": 표본[2], "뺀파일": len(뺌), "뺀회사": 낸["표본밖회사"], "동작": "정리"}
        _쓰기(목p, 목)
    if not 조용:
        print("정리 %s %s — 표본 밖 %d개 이력으로%s · 갈래 옮김 %d · 분류 바꿈 %d (%s)" % (
            국가, 낸["종목"], len(뺌), (" (%s)" % ", ".join(낸["표본밖회사"][:10])) if 뺌 else "", 옮김, 바꿈, 낸["기준"]))
    낸["기준일뒤"] = 기준일표지(국가, 낸["종목"] or 종목, 조용=조용)
    return 낸


표지갈래 = ("B1", "B2", "D", "A3", "F", "C1")


def 기준일표지(국가, 종목, 갈래들=None, 조용=False):
    """쌓인 조사 산출(JSON · 분류 「조사」)에 「평가기준일 뒤 정보」 표지를 단다(2026-10-24 W18 — `기준일뒤.표지`). 바꾼 파일의 옛것은
    `이력/기준일표지_<날>/<갈래>/` 에 복사하고 목록의 해시 · 갈래 `기준일뒤` 셈을 고친다. 지우는 것은 없다(축 근거 범위는 `…_기준일뒤` 칸으로 옮긴다)."""
    import 기준일뒤 as _뒤                                # noqa: PLC0415
    국가 = 국가.upper()
    자리 = 회사자리(국가, 종목)
    목p = os.path.join(자리, "목록.json")
    목 = _읽기(목p)
    낸 = {"국가": 국가, "종목": 종목정리(국가, 종목), "갈래": {}}
    if not 목:
        return 낸
    오늘 = datetime.date.today().strftime("%Y%m%d")
    바뀜 = False
    for 갈 in (갈래들 or 표지갈래):
        g = (목.get("갈래") or {}).get(갈)
        if not g or 갈 not in 표지갈래:
            continue
        셈 = {"새표지": 0, "이미": 0, "축옮김": 0, "축섞임": 0, "밴드옮김": 0, "축기준일뒤": 0, "밴드기준일뒤": 0, "파일": 0}
        for 상, v in sorted((g.get("파일") or {}).items()):
            if v.get("분류") != "조사" or not 상.lower().endswith(".json"):
                continue
            p = _갈래파일자리(자리, 갈, 상)
            d = _읽기(p)
            if not isinstance(d, dict):
                continue
            기준일 = d.get("평가기준일") or g.get("평가기준일") or 목.get("평가기준일")
            if not _날짜(기준일 or ""):
                continue
            # 2026-10-25 날짜 둘 — 산출 · 갈래가 재무기준일을 적었으면 (F, T] 에 「사이」 표지(없으면 F = T — 지금과 같다)
            재무 = (d.get("재무기준일") or g.get("재무기준일") or "")[:10] or None
            c = _뒤.표지(d, 기준일[:10], (d.get("조사일") or g.get("조사일") or "")[:10] or None, 재무)
            for k in ("새표지", "이미", "축옮김", "축섞임", "밴드옮김", "축기준일뒤", "밴드기준일뒤"):
                셈[k] += c.get(k, 0)
            for k in ("사이표지", "사이수", "거둠", "축되돌림", "밴드되돌림", "축사이"):
                if c.get(k):
                    셈[k] = 셈.get(k, 0) + c[k]
            if c["바뀜"]:
                ip = os.path.join(자리, "이력", "기준일표지_" + 오늘, 갈, 상.replace("/", os.sep))
                if not os.path.exists(ip):
                    os.makedirs(os.path.dirname(ip), exist_ok=True)
                    shutil.copy2(p, ip)
                _쓰기(p, d)
                g["파일"][상] = dict(v, sha256=_해시(p), 크기=os.path.getsize(p))
                셈["파일"] += 1
                바뀜 = True
        상태 = {"표지": 셈["이미"] + 셈["새표지"], "축옮김": 셈["축기준일뒤"], "축섞임": 셈["축섞임"], "밴드옮김": 셈["밴드기준일뒤"]}
        if 셈.get("사이수") or 셈.get("축사이"):                   # 2026-10-25 날짜 둘 — 있을 때만(옛 목록 꼴 그대로)
            상태["사이"] = 셈.get("사이수", 0)
            상태["축사이"] = 셈.get("축사이", 0)
        if any(상태.values()) or g.get("기준일뒤"):
            바뀜 = 바뀜 or g.get("기준일뒤") != 상태
            g["기준일뒤"] = 상태
        낸["갈래"][갈] = 셈
    if 바뀜:
        목.setdefault("이력", []).append({"일시": _지금(), "동작": "기준일표지", "셈": 낸["갈래"],
                                       "옮긴곳": "이력/기준일표지_" + 오늘})
        _쓰기(목p, 목)
    if not 조용:
        t = {k: sum(x[k] for x in 낸["갈래"].values()) for k in ("새표지", "이미", "축옮김", "축섞임", "밴드옮김")}
        if any(t.values()):
            print("  기준일 뒤 %s %s — 출처 표지 새 %d · 이미 %d · 근거 범위 옮김 %d축 · 섞임 %d축 · 밴드 옮김 %d" % (
                국가, 낸["종목"], t["새표지"], t["이미"], t["축옮김"], t["축섞임"], t["밴드옮김"]))
    return 낸


def 세율다시(국가, 종목, 쓰기=True, 조용=False):
    """쌓인 C2 의 βU 산출(`peers/βU_*.json`)을 무차입 세율 단일 출처(`무차입세율.py`)로 다시 셈한다(2026-10-24 W18) — 표본 · 행은 그대로,
    세율 · βU · 요약 · 본값만. 옛 파일은 `이력/세율다시_<날>/C2/peers/` 에 복사해 두고 그 자리를 새로 쓴다. → {국가 · 종목 · 표[파일마다]}."""
    import βU다시셈 as _R                                # noqa: PLC0415
    국가 = 국가.upper()
    자리 = 회사자리(국가, 종목)
    폴더 = os.path.join(자리, "C2", "peers")
    목p = os.path.join(자리, "목록.json")
    목 = _읽기(목p)
    if not 목 or not os.path.isdir(폴더):
        return {"국가": 국가, "종목": 종목정리(국가, 종목), "표": [], "까닭": "C2 peers 없음"}
    βU들 = sorted(f for f in os.listdir(폴더) if f.startswith("βU_") and f.endswith(".json"))
    if not βU들:
        return {"국가": 국가, "종목": 목.get("종목"), "표": [], "까닭": "βU 산출 없음"}
    오늘 = datetime.date.today().strftime("%Y%m%d")
    if 쓰기:
        보관 = os.path.join(자리, "이력", "세율다시_" + 오늘, "C2", "peers")
        os.makedirs(보관, exist_ok=True)
        for f in βU들:
            if not os.path.exists(os.path.join(보관, f)):          # 같은 날 두 번 돌려도 처음 옛 파일을 지킨다
                shutil.copy2(os.path.join(폴더, f), os.path.join(보관, f))
    표 = _R.폴더다시셈(폴더, 쓰기)
    if 쓰기:
        g = (목.get("갈래") or {}).get("C2") or {}
        for f in βU들:
            상 = "peers/" + f
            if 상 in (g.get("파일") or {}):
                p = os.path.join(폴더, f)
                g["파일"][상] = dict(g["파일"][상], sha256=_해시(p), 크기=os.path.getsize(p))
        목.setdefault("이력", []).append({"일시": _지금(), "동작": "세율다시", "파일": len(표), "옮긴곳": "이력/세율다시_" + 오늘,
                                       "세율": sorted({"%s" % x.get("세율후") for x in 표 if x.get("세율후") is not None})})
        _쓰기(목p, 목)
    if not 조용:
        for x in 표:
            f = lambda v: "-" if v is None else ("%.4f" % v)
            print("  %s %-8s %-28s %-3s 세율 %s→%s 행 %s · 기본값 %s / %s → %s%s" % (
                국가, 목.get("종목"), x["파일"][:28], x.get("꼴") or "-", f(x.get("세율전")), f(x.get("세율후")), x.get("바꾼행", "-"),
                f(x.get("기본값저장")), f(x.get("기본값옛세율")), f(x.get("기본값후")), (" · " + x["까닭"]) if x.get("까닭") else ""))
    return {"국가": 국가, "종목": 목.get("종목"), "회사명": 목.get("회사명"), "표": 표}


def _낡음(조사일, 낡음일, 오늘=None):
    d = _날짜(조사일 or "")
    오늘 = 오늘 or datetime.date.today()
    if d is None:
        return True, None
    n = (오늘 - d).days
    return n > 낡음일, n


def 씨앗(국가, 종목, raw, 덮어쓰기=False, 재료빼기=False, 낡음일=None, 오늘=None, 조용=False):
    """캐시의 갈래 산출을 새 회차 `_raw/` 로(`유사기업_후보.md` 는 `_raw` 의 부모로). 이미 있는 파일은 덮지 않는다(`--덮어쓰기`).
    기록 `_raw/조사축적_씨앗.json` — 갈래마다 조사일 · 출처 as-of · 낡음."""
    국가 = 국가.upper()
    자리 = 회사자리(국가, 종목)
    목 = _읽기(os.path.join(자리, "목록.json"))
    if not 목:
        if not 조용:
            print("씨앗 — 캐시에 %s %s 가 없다(%s)" % (국가, 종목정리(국가, 종목), 자리))
        return None
    낡음일 = 설정["낡음일"] if 낡음일 is None else 낡음일
    os.makedirs(raw, exist_ok=True)
    부모 = os.path.dirname(os.path.abspath(raw))
    갈들, 옮김, 둠 = {}, 0, 0
    for 갈, g in sorted((목.get("갈래") or {}).items()):
        낡, 일수 = _낡음(g.get("조사일"), 낡음일, 오늘)
        한 = {"조사일": g.get("조사일"), "출처asof": g.get("출처asof"), "평가기준일": g.get("평가기준일"), "낡음": 낡, "지난일수": 일수, "옮김": []}
        for 상, v in sorted((g.get("파일") or {}).items()):
            if 재료빼기 and v.get("분류") == "재료":
                continue
            src = _갈래파일자리(자리, 갈, 상)
            dst = os.path.join(부모, 상[1:]) if 상.startswith("^") else os.path.join(raw, 상.replace("/", os.sep))
            if not os.path.exists(src):
                continue
            if os.path.exists(dst) and not 덮어쓰기:
                둠 += 1
                continue
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            한["옮김"].append(상)
            옮김 += 1
        갈들[갈] = 한
    기록 = {"형식": 형식, "일시": _지금(), "국가": 국가, "종목": 목.get("종목"), "회사명": 목.get("회사명"), "캐시": 자리, "낡음일": 낡음일,
          "갈래": 갈들, "이미있어둠": 둠,
          "알림": "공용 캐시에서 가져왔다 — 이 회차가 새로 조사한 것이 아니다. 낡은 갈래는 출처 as-of 뒤만 이어 조사한다(`조사축적.py 이어조사목록`)"}
    _쓰기(os.path.join(raw, "조사축적_씨앗.json"), 기록)
    if not 조용:
        print("씨앗 %s %s — 옮김 %d · 이미 있어 둠 %d · 공용 캐시에서 가져왔다(새로 조사한 것이 아니다)" % (국가, 목.get("종목"), 옮김, 둠))
        for 갈, 한 in 갈들.items():
            if 한["낡음"]:
                print("  낡음 — %s 조사 %s(%s일 전) · 이어 조사는 출처 %s 뒤만" % (갈, (한["조사일"] or "")[:10], 한["지난일수"], 한["출처asof"]))
    return 기록


# ══════════════════════════════════════════════════════════ 유니버스 교차(2026-10-25 FX-D — R12)
# 그룹 공동 시설(지분을 나눠 가진 한 시설)을 두 회사 F 가 각각 세고, 지주(연결 모회사)가 상장 자회사의 투자계획 줄을 자기 프로젝트로 쓸어 담는다
# (유니버스 F 물결 실측). 캐시 안 다른 회사의 F 산출과 견줘 「같은 시설 후보」 를 두 쪽 모두에 표시한다 — 값을 고치지 않고(어느 쪽 몫인지는 본선
# 판단) 표시만. 회사 이름이 아니라 **총액 · 통화 · 이름 글자 닮음**으로 가린다(범용).
교차설정 = {
    "포함닮음": 0.8,           # 짧은 이름이 긴 이름 안에 거의 다 들어가면(두 글자 짝 포함 계수) — 「필리 조선소투자」 ↔ 「<법인> 필리조선소 투자 생산시설 등 투자」
    "포함최소글자": 6,          # 포함 계수는 정규화 뒤 이 글자 이상인 이름에만
    "금액허용": 0.01,          # 총액 차이 비율 — 이 안이면 「같은 총액」
    "이름닮음_금액같음": 0.25,  # 총액이 같을 때 이름 글자 짝(두 글자) 닮음 하한
    "이름닮음_금액없음": 0.5,   # 한쪽 총액이 비었을 때(회사주장 · 외부평가) 이름만으로 볼 하한
    "이름닮음_능력": 0.5,       # 능력단위 — 같은 단위 + 이 닮음
    "이름최소글자": 6,          # 정규화 뒤 이보다 짧은 이름(「IT 인프라」 · 「정보화」 같은 일반 이름)은 이름만으로 견주지 않는다
    "금액허용_짧은이름": 0.001,  # 짧은 이름은 총액이 거의 같을 때만(지주가 자회사 줄을 그대로 옮겨 적은 것) — 우연 일치를 막는다
}
_법인꼴 = re.compile(r"㈜|\(주\)|주식회사|유한회사|유한공사|\b(inc|corp|corporation|co|ltd|limited|llc|plc|pte|gmbh|ag|sa|nv|bv|holdings?)\b\.?", re.I)


def _이름정규(s):
    t = _법인꼴.sub(" ", ("%s" % (s or "")).lower())
    return re.sub(r"[^0-9a-z가-힣]", "", t)


def _짝(s):
    return {s[i:i + 2] for i in range(len(s) - 1)} if len(s) > 1 else {s}


def _이름닮음(a, b):
    """두 글자 짝(bigram) 자카드 — 어순이 달라도(「A 의 B 투자」 ↔ 「B 투자(A)」) 짝이 겹친다."""
    x, y = _짝(a), _짝(b)
    return len(x & y) / float(len(x | y)) if (x and y) else 0.0


def _포함닮음(a, b):
    """두 글자 짝 포함 계수 |x ∩ y| ÷ min(|x|, |y|) — 짧은 이름이 긴 이름(법인명 · 부문 · 자산 설명이 붙은)에 들어가 있는가(R10)."""
    if min(len(a), len(b)) < 교차설정["포함최소글자"]:
        return 0.0
    x, y = _짝(a), _짝(b)
    return len(x & y) / float(min(len(x), len(y))) if (x and y) else 0.0


# 공시 제목 꼴 · 표의 합계 줄은 시설 이름이 아니다 — 회사 사이 같은 제목(「기타경영사항(자율공시)」 · 「장래사업ㆍ경영계획(공정공시)」)을
# 같은 시설로 잡았다(R15 — 교차 기록 1,004 중 330). 이름으로는 견주지 않고 접수번호 · 총액으로만.
_제목이름꼴 = re.compile(r"자율공시|공정공시|주요경영사항|주요사항보고|장래사업|경영계획|투자판단|신규시설투자\s*등|유형자산\s*(?:의\s*)?(?:취득|처분|양수|양도)\s*결정|"
                     r"^\s*\[?\s*(?:기재정정|첨부추가|첨부정정|정정)\s*\]")
_합계이름꼴 = re.compile(r"^(?:소계|합계|총계|계|기타|해당없음|없음|total|subtotal)+$")


def 이름무효(이름, 정규):
    return bool(_제목이름꼴.search(이름 or "")) or bool(_합계이름꼴.match(정규 or ""))


def _금액(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v) if v else None
    m = re.match(r"^\s*([+\-]?[\d,]+(?:\.\d+)?)\s*$", "%s" % (v or ""))
    if not m:
        return None
    try:
        x = float(m.group(1).replace(",", ""))
    except ValueError:
        return None
    return x or None


def _접수들(*글들):
    """출처 글 → 공시 접수번호 집합(국내 14자리 · 미국 accession)."""
    낸 = set()
    for 글 in 글들:
        t = "%s" % (글 or "")
        낸 |= set(re.findall(r"(?<!\d)(\d{14})(?!\d)", t))
        낸 |= set(re.findall(r"\b(\d{10}-\d{2}-\d{6})\b", t))
    return frozenset(낸)


def F항목들(d):
    """투자능력 산출 → [(종류, 번호, 이름, 정규이름, 총액, 통화, 단위, 접수들, 금액100%, 지분율)].
    금액100% = `금액100%` 칸, 없으면 총액 ÷ 지분율(0 < 지분율 < 1) — 공동 시설을 회사마다 제 몫 금액으로 적은 것을 100% 로 맞춰 견준다(R10)."""
    낸 = []
    if not isinstance(d, dict):
        return 낸
    for i, p in enumerate(d.get("프로젝트") or []):
        if isinstance(p, dict):
            나 = "%s" % (p.get("이름") or "")
            총 = _금액(p.get("총액"))
            지 = p.get("지분율") if isinstance(p.get("지분율"), (int, float)) and not isinstance(p.get("지분율"), bool) else None
            백 = _금액(p.get("금액100%")) or ((총 / 지) if (총 and 지 and 0 < 지 < 1) else None)
            낸.append(("프로젝트", i, 나, _이름정규(나), 총, ("%s" % (p.get("통화") or "")).upper(), "",
                      _접수들(p.get("출처"), p.get("접수번호")), 백, 지))
    for i, u in enumerate(d.get("능력단위") or []):
        if isinstance(u, dict):
            나 = "%s" % (u.get("이름") or "")
            낸.append(("능력단위", i, 나, _이름정규(나), None, "", re.sub(r"\s+", "", "%s" % (u.get("단위") or "")).lower(),
                      frozenset(), None, None))
    return 낸


def _채움(x):
    """옛 7칸 꼴(시험 · 옛 호출)을 10칸으로."""
    x = tuple(x)
    return x + (frozenset(), None, None)[max(0, len(x) - 7):] if len(x) < 10 else x


def _금액짝(가, 나):
    """두 항목의 견줄 금액 짝들 — (총액, 총액) 과 100% 환산 짝 → [(a, b, 뜻)]."""
    짝 = []
    if 가[4] and 나[4]:
        짝.append((가[4], 나[4], "총액"))
    a100, b100 = 가[8] or 가[4], 나[8] or 나[4]
    if (가[8] or 나[8]) and a100 and b100:
        짝.append((a100, b100, "100% 환산"))
    return 짝


def 같은시설(가, 나):
    """F 항목 둘 → 근거 글 | None(같은 시설 후보가 아니다).
    ① 같은 공시 접수번호 → 같은 시설(지주가 상장 자회사의 수시공시를 자기 프로젝트로 쓴 것) ② 공시 제목 꼴 · 합계 줄 이름은 이름으로 견주지 않는다
    ③ 총액(또는 지분율로 100% 환산한 금액)이 같고 이름이 닮거나(자카드) 짧은 이름이 긴 이름에 들어 있다(포함 계수) ④ 한쪽 총액이 없으면 이름이 아주 닮을 때만."""
    가, 나 = _채움(가), _채움(나)
    if 가[0] != 나[0]:
        return None
    겹접수 = (가[7] & 나[7]) if (가[7] and 나[7]) else frozenset()
    if 겹접수:
        return "같은 공시(접수 %s)" % " · ".join(sorted(겹접수)[:2])
    if not 가[3] or not 나[3] or 이름무효(가[2], 가[3]) or 이름무효(나[2], 나[3]):
        return None
    짧음 = min(len(가[3]), len(나[3])) < 교차설정["이름최소글자"]
    닮 = _이름닮음(가[3], 나[3])
    포 = 0.0 if 짧음 else _포함닮음(가[3], 나[3])
    if 가[0] == "능력단위":
        # 능력단위는 자카드만 — 포함 계수는 「데이터센터 용량」 같은 일반 이름이 남의 「<사업> 데이터센터 전력 용량」 에 들어가 거짓 짝을 낸다
        if not 짧음 and 가[6] and 가[6] == 나[6] and 닮 >= 교차설정["이름닮음_능력"]:
            return "같은 단위(%s) · 이름 닮음 %.2f" % (가[6], 닮)
        return None
    짝 = _금액짝(가, 나)
    if 짝:
        if 가[5] and 나[5] and 가[5] != 나[5]:
            return None
        허 = 교차설정["금액허용_짧은이름"] if 짧음 else 교차설정["금액허용"]
        for a, b, 뜻 in 짝:
            if abs(a - b) <= 허 * max(abs(a), abs(b)) and (닮 >= 교차설정["이름닮음_금액같음"] or 포 >= 교차설정["포함닮음"]):
                return "%s 같음(%s ≈ %s) · 이름 닮음 %.2f · 포함 %.2f" % (뜻, ("%g" % a), ("%g" % b), 닮, 포)
        if 가[4] and 나[4]:
            return None
    if not 짧음 and 닮 >= 교차설정["이름닮음_금액없음"]:
        return "이름 닮음 %.2f(총액 한쪽 없음)" % 닮
    return None


def _F자리(국가, 종목):
    자리 = 회사자리(국가, 종목)
    목 = _읽기(os.path.join(자리, "목록.json")) or {}
    g = (목.get("갈래") or {}).get("F") or {}
    상 = next((s for s in (g.get("파일") or {}) if os.path.basename(s) == "투자능력.json"), None)
    return (자리, 목, 상, _갈래파일자리(자리, "F", 상) if 상 else None)


def 유니버스교차(국가, 종목, 조용=False):
    """캐시의 이 회사 F 와 다른 모든 회사 F 를 견줘 같은 시설 후보를 두 쪽 F 파일(`프로젝트[] · 능력단위[]` 의 `유니버스중복[]`)과
    목록(`유니버스중복[]`)에 적는다(제자리 · 같은 짝은 바꿔 적는다 — 두 번 돌려도 같다) → {국가 · 종목 · 짝[] · 바꾼파일}."""
    국가 = 국가.upper()
    나 = "%s/%s" % (국가, 종목정리(국가, 종목))
    자리, 목, 상, p = _F자리(국가, 종목)
    낸 = {"국가": 국가, "종목": 종목정리(국가, 종목), "짝": [], "바꾼파일": 0}
    d = _읽기(p) if p else None
    if not isinstance(d, dict):
        return 낸
    내항 = F항목들(d)
    짝들 = []                                                  # (상대, 내 항목, 상대 항목, 근거)
    상대F = {}
    for 국2, 종2, _ in 캐시회사들():
        너 = "%s/%s" % (국2, 종2)
        if 너 == 나:
            continue
        자2, 목2, 상2, p2 = _F자리(국2, 종2)
        d2 = _읽기(p2) if p2 else None
        if not isinstance(d2, dict):
            continue
        상대F[너] = (자2, 목2, 상2, p2, d2)
        for x in 내항:
            for y in F항목들(d2):
                근 = 같은시설(x, y)
                if 근:
                    짝들.append((너, x, y, 근))
    오늘 = datetime.date.today().strftime("%Y%m%d")

    def 적기(자, 목p_, 목_, 상_, p_, d_, 상대, 내것들):
        """한 회사 F 파일 · 목록에서 상대와의 옛 표시를 지우고 새로 적는다 → 바뀌었나."""
        전 = json.dumps(d_, ensure_ascii=False, sort_keys=True)
        for 칸 in ("프로젝트", "능력단위"):
            for it in d_.get(칸) or []:
                if isinstance(it, dict) and isinstance(it.get("유니버스중복"), list):
                    it["유니버스중복"] = [z for z in it["유니버스중복"] if z.get("상대") != 상대]
                    if not it["유니버스중복"]:
                        it.pop("유니버스중복")
        본것 = set()
        for 종류, 번호, 상대항목, 근 in 내것들:
            if (종류, 번호, 상대항목[:120]) in 본것:
                continue                                       # 상대 쪽에 같은 이름 항목이 여럿이어도 한 번만(R15 ③)
            본것.add((종류, 번호, 상대항목[:120]))
            it = (d_.get(종류) or [])[번호]
            it.setdefault("유니버스중복", []).append({"상대": 상대, "상대항목": 상대항목[:120], "근거": 근,
                                                 "뜻": "같은 시설 후보 — 공동 투자 · 지주와 상장 자회사가 같은 시설을 셀 수 있다(어느 쪽 몫인지는 본선 판단)"})
            it["유니버스중복"].sort(key=lambda z: (z.get("상대") or "", z.get("상대항목") or ""))     # 차례를 고정 — 두 번 돌려도 같다
        바뀜 = json.dumps(d_, ensure_ascii=False, sort_keys=True) != 전
        if 바뀜:
            ip = os.path.join(자, "이력", "교차_" + 오늘, "F", 상_.replace("/", os.sep))
            if not os.path.exists(ip):
                os.makedirs(os.path.dirname(ip), exist_ok=True)
                shutil.copy2(p_, ip)
            _쓰기(p_, d_)
            g = 목_["갈래"]["F"]
            g["파일"][상_] = dict(g["파일"][상_], sha256=_해시(p_), 크기=os.path.getsize(p_))
        요 = [z for z in (목_.get("유니버스중복") or []) if z.get("상대") != 상대]
        본요 = set()
        for 종류, 번호, 상대항목, 근 in 내것들:
            z = {"갈래": "F", "항목종류": 종류, "항목": (d_.get(종류) or [])[번호].get("이름"), "상대": 상대, "상대항목": 상대항목[:120], "근거": 근}
            k = (종류, "%s" % z["항목"], z["상대항목"])
            if k in 본요:
                continue                                       # 목록에는 이름 짝 하나(같은 이름 항목 여럿 · 같은 짝 여러 번 — R15 ③)
            본요.add(k)
            요.append(z)
        요.sort(key=lambda z: (z.get("상대") or "", z.get("항목종류") or "", "%s" % (z.get("항목") or ""), z.get("상대항목") or ""))
        if 요 != (목_.get("유니버스중복") or []):
            if 요:
                목_["유니버스중복"] = 요
            else:
                목_.pop("유니버스중복", None)
            바뀜 = True
        if 바뀜:
            _쓰기(목p_, 목_)
        return 바뀜

    for 너, (자2, 목2, 상2, p2, d2) in sorted(상대F.items()):
        내것 = [(x[0], x[1], y[2], 근) for 상대, x, y, 근 in 짝들 if 상대 == 너]
        네것 = [(y[0], y[1], x[2], 근) for 상대, x, y, 근 in 짝들 if 상대 == 너]
        낸["바꾼파일"] += 1 if 적기(자리, os.path.join(자리, "목록.json"), 목, 상, p, d, 너, 내것) else 0
        낸["바꾼파일"] += 1 if 적기(자2, os.path.join(자2, "목록.json"), 목2, 상2, p2, d2, 나, 네것) else 0
    본짝, 낸["짝"] = set(), []
    for 너, x, y, 근 in 짝들:
        if (너, x[2], y[2]) in 본짝:
            continue
        본짝.add((너, x[2], y[2]))
        낸["짝"].append({"상대": 너, "항목": x[2], "상대항목": y[2], "근거": 근})
    if 낸["바꾼파일"]:
        목 = _읽기(os.path.join(자리, "목록.json")) or 목
        목.setdefault("이력", []).append({"일시": _지금(), "동작": "교차", "짝": len(짝들), "바꾼파일": 낸["바꾼파일"]})
        _쓰기(os.path.join(자리, "목록.json"), 목)
    if not 조용 and 짝들:
        print("  유니버스 교차 %s — 같은 시설 후보 %d짝: %s" % (나, len(짝들), " · ".join(
            "%s 「%s」 ↔ 「%s」" % (z["상대"], z["항목"][:24], z["상대항목"][:24]) for z in 낸["짝"][:4])))
    return 낸


# ══════════════════════════════════════════════════════════ 상태 · 이어조사목록

def 유니버스읽기(경로, 판정=None):
    """유니버스 CSV → [(국가, 종목, 이름)]. 열 — 국가 · 시장 / 종목 · 티커 · 원래코드 · 코드 / 이름 / (판정)."""
    낸 = []
    with io.open(경로, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            국 = (r.get("국가") or r.get("시장") or "").strip().upper()
            if 국 not in 국가들:
                continue
            if 판정 and (r.get("판정") or "").strip() not in 판정:
                continue
            종 = (r.get("종목") or r.get("티커") or r.get("원래코드") or r.get("코드") or "").strip()
            if 종:
                낸.append((국, 종목정리(국, 종), (r.get("이름") or "").strip()))
    return 낸


def 캐시회사들(국가=None):
    낸 = []
    뿌 = 조사뿌리()
    for 국 in 국가들:
        if 국가 and 국 != 국가.upper():
            continue
        d = os.path.join(뿌, 국)
        if not os.path.isdir(d):
            continue
        for 종 in sorted(os.listdir(d)):
            if os.path.exists(os.path.join(d, 종, "목록.json")):
                낸.append((국, 종, ""))
    return 낸


def 상태(국가=None, 유니버스=None, 판정=None, 낡음일=None, 오늘=None):
    """→ [{국가 · 종목 · 회사명 · 갈래{갈: {조사일 · 출처asof · 낡음 · 지난일수} | None}}] — 유니버스를 주면 그 회사 전부(캐시에 없으면 빈 갈래)."""
    낡음일 = 설정["낡음일"] if 낡음일 is None else 낡음일
    대상 = 유니버스읽기(유니버스, 판정) if 유니버스 else 캐시회사들(국가)
    if 국가:
        대상 = [x for x in 대상 if x[0] == 국가.upper()]
    낸 = []
    for 국, 종, 이름 in 대상:
        목 = _읽기(os.path.join(회사자리(국, 종), "목록.json")) or {}
        갈 = {}
        for g in 설정["필수갈래"]:
            v = (목.get("갈래") or {}).get(g)
            if v:
                낡, n = _낡음(v.get("조사일"), 낡음일, 오늘)
                갈[g] = {"조사일": v.get("조사일"), "출처asof": v.get("출처asof"), "낡음": 낡, "지난일수": n,
                        "파일수": len(v.get("파일") or {}), "리포트식별수": v.get("리포트식별수")}
            else:
                갈[g] = None
        낸.append({"국가": 국, "종목": 종, "회사명": 목.get("회사명") or 이름, "갈래": 갈,
                  "유니버스중복": len(목.get("유니버스중복") or [])})
    return 낸


def 이어조사목록(유니버스=None, 판정=None, 갈래=None, 낡음일=None, 오늘=None, 국가=None):
    """→ [{국가 · 종목 · 회사명 · 갈래 · 까닭(빈 · 낡음) · 이후(그 날짜 뒤만 보면 된다 — 빈 갈래는 None = 처음부터)}]."""
    갈래 = 갈래 or 설정["필수갈래"]
    낸 = []
    for r in 상태(국가, 유니버스, 판정, 낡음일, 오늘):
        for g in 갈래:
            v = r["갈래"].get(g)
            if v is None:
                낸.append({"국가": r["국가"], "종목": r["종목"], "회사명": r["회사명"], "갈래": g, "까닭": "빈", "이후": None})
            elif v["낡음"]:
                낸.append({"국가": r["국가"], "종목": r["종목"], "회사명": r["회사명"], "갈래": g,
                          "까닭": "낡음(%s일)" % v["지난일수"], "이후": v["출처asof"] or (v["조사일"] or "")[:10]})
    return 낸


# ══════════════════════════════════════════════════════════ 명령

def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="조사 축적 — 수집 갈래 산출을 공용 캐시에 쌓고 조사 시점 뒤만 잇는다")
    sub = ap.add_subparsers(dest="명령", required=True)
    for 이름 in ("넣기", "씨앗"):
        s = sub.add_parser(이름, allow_abbrev=False)
        s.add_argument("--국가", required=True, type=str.upper, choices=국가들)
        s.add_argument("--종목", required=True)
        s.add_argument("--raw", required=True, help="회차 `_raw/` 폴더")
        if 이름 == "씨앗":
            s.add_argument("--덮어쓰기", action="store_true")
            s.add_argument("--재료빼기", action="store_true", help="유사기업 시세 · 재무 재료는 가져오지 않는다")
            s.add_argument("--낡음일", type=int, default=None)
    s = sub.add_parser("정리", help="이미 쌓인 C1 · C2 를 지금 규칙(표본 밖 회사 재료 · 분류)으로 다시 짓는다 — 옛 파일은 이력으로", allow_abbrev=False)
    s.add_argument("--국가", type=str.upper, choices=국가들)
    s.add_argument("--종목", help="없으면 --모두")
    s.add_argument("--모두", action="store_true", help="캐시의 모든 회사(--국가 로 좁힌다)")
    s = sub.add_parser("세율다시", help="쌓인 C2 의 βU 를 무차입 세율 단일 출처로 다시 셈(표본 그대로) — 옛 파일은 이력으로", allow_abbrev=False)
    s.add_argument("--국가", type=str.upper, choices=국가들)
    s.add_argument("--종목", help="없으면 --모두")
    s.add_argument("--모두", action="store_true", help="캐시의 모든 회사(--국가 로 좁힌다)")
    s.add_argument("--보기", action="store_true", help="쓰지 않고 표만(전 · 후)")
    s.add_argument("--json", help="표를 이 JSON 경로에")
    s = sub.add_parser("교차", help="쌓인 F 를 회사끼리 견줘 같은 시설 후보(공동 투자 · 지주와 상장 자회사)를 두 쪽에 표시한다", allow_abbrev=False)
    s.add_argument("--국가", type=str.upper, choices=국가들)
    s.add_argument("--종목", help="없으면 --모두")
    s.add_argument("--모두", action="store_true", help="캐시의 모든 회사(--국가 로 좁힌다)")
    s.add_argument("--json", help="짝 표를 이 JSON 경로에")
    for 이름 in ("상태", "이어조사목록"):
        s = sub.add_parser(이름, allow_abbrev=False)
        s.add_argument("--국가", type=str.upper, choices=국가들)
        s.add_argument("--유니버스", help="유니버스 CSV(국가 · 시장 / 종목 · 티커 · 원래코드 열)")
        s.add_argument("--판정", help="유니버스의 판정 열 값(쉼표) — 예: 대상")
        s.add_argument("--낡음일", type=int, default=None)
        s.add_argument("--json", help="결과를 이 JSON 경로에")
        if 이름 == "이어조사목록":
            s.add_argument("--갈래", help="쉼표 — 기본 %s" % ",".join(설정["필수갈래"]))
    a = ap.parse_args(argv)
    try:
        if a.명령 == "넣기":
            낸 = 넣기(a.국가, a.종목, a.raw)
            return 발견 if (not 낸["넣은갈래"] or 낸["경보"]) else 통과
        if a.명령 == "씨앗":
            return 통과 if 씨앗(a.국가, a.종목, a.raw, a.덮어쓰기, a.재료빼기, a.낡음일) else 발견
        if a.명령 == "정리":
            if a.종목 and a.국가:
                대상들 = [(a.국가, a.종목)]
            elif a.모두:
                대상들 = [(국, 종) for 국, 종, _ in 캐시회사들(a.국가)]
            else:
                print("입력 오류 — `--국가 --종목` 또는 `--모두`")
                return 입력오류
            합 = [정리(국, 종) for 국, 종 in 대상들]
            print("정리 %d곳 — 표본 밖 재료 %d개 이력으로 · 갈래 옮김 %d · 분류 바꿈 %d" % (
                len(합), sum(x.get("표본밖", 0) for x in 합), sum(x.get("갈래옮김", 0) for x in 합), sum(x.get("분류바꿈", 0) for x in 합)))
            return 통과
        if a.명령 == "세율다시":
            if a.종목 and a.국가:
                대상들 = [(a.국가, a.종목)]
            elif a.모두:
                대상들 = [(국, 종) for 국, 종, _ in 캐시회사들(a.국가)]
            else:
                print("입력 오류 — `--국가 --종목` 또는 `--모두`")
                return 입력오류
            합 = [세율다시(국, 종, not a.보기) for 국, 종 in 대상들]
            n = sum(len(x["표"]) for x in 합)
            틀 = [(x["종목"], y["파일"], y["까닭"]) for x in 합 for y in x["표"] if y.get("까닭")]
            print("세율다시 %d곳 · βU 산출 %d개%s%s" % (len(합), n, " (보기 — 쓰지 않음)" if a.보기 else "",
                                                  (" · 못 셈 %d: %s" % (len(틀), "; ".join("%s %s(%s)" % t for t in 틀[:5]))) if 틀 else ""))
            if a.json:
                _쓰기(a.json, {"형식": 형식, "일시": _지금(), "보기": bool(a.보기), "회사": 합})
            return 발견 if 틀 else 통과
        if a.명령 == "교차":
            if a.종목 and a.국가:
                대상들 = [(a.국가, a.종목)]
            elif a.모두:
                대상들 = [(국, 종) for 국, 종, _ in 캐시회사들(a.국가)]
            else:
                print("입력 오류 — `--국가 --종목` 또는 `--모두`")
                return 입력오류
            합 = [유니버스교차(국, 종) for 국, 종 in 대상들]
            짝 = {tuple(sorted(("%s/%s" % (x["국가"], x["종목"]), z["상대"]))) + tuple(sorted((z["항목"], z["상대항목"])))
                 for x in 합 for z in x["짝"]}
            print("교차 %d곳 — 같은 시설 후보 %d짝 · 바꾼 파일 %d" % (len(합), len(짝), sum(x["바꾼파일"] for x in 합)))
            if a.json:
                _쓰기(a.json, {"형식": 형식, "일시": _지금(), "설정": 교차설정, "회사": 합})
            return 통과
        판 = set(x.strip() for x in a.판정.split(",")) if a.판정 else None
        if a.유니버스 and not os.path.exists(a.유니버스):
            print("입력 오류 — 유니버스 파일이 없다(%s)" % a.유니버스)
            return 입력오류
        if a.명령 == "상태":
            표 = 상태(a.국가, a.유니버스, 판, a.낡음일)
            갈 = 설정["필수갈래"]
            print("조사 축적 상태 — %d곳 · 갈래 %s · 낡음 %d일(%s)" % (len(표), " · ".join(갈), 설정["낡음일"] if a.낡음일 is None else a.낡음일, 조사뿌리()))
            for r in 표:
                칸 = []
                for g in 갈:
                    v = r["갈래"][g]
                    칸.append("%s %s" % (g, "—" if v is None else ("%s%s" % ((v["조사일"] or "")[:10], " 낡음" if v["낡음"] else ""))))
                print("  %s %-8s %-22s %s" % (r["국가"], r["종목"], (r["회사명"] or "")[:22], " · ".join(칸)))
            빈 = sum(1 for r in 표 for v in r["갈래"].values() if v is None)
            print("빈 갈래 %d · 낡은 갈래 %d" % (빈, sum(1 for r in 표 for v in r["갈래"].values() if v and v["낡음"])))
            중 = [r for r in 표 if r.get("유니버스중복")]
            if 중:
                print("유니버스 교차 — 같은 시설 후보가 표시된 회사 %d곳(F 의 `유니버스중복`): %s" % (len(중), " · ".join(
                    "%s %s(%d)" % (r["국가"], r["종목"], r["유니버스중복"]) for r in 중[:10])))
            if a.json:
                _쓰기(a.json, {"형식": 형식, "일시": _지금(), "표": 표})
            return 통과
        목 = 이어조사목록(a.유니버스, 판, [x.strip() for x in a.갈래.split(",")] if a.갈래 else None, a.낡음일, 국가=a.국가)
        for x in 목:
            print("  %s %-8s %-22s %-3s %-12s %s" % (x["국가"], x["종목"], (x["회사명"] or "")[:22], x["갈래"], x["까닭"],
                                                 ("%s 뒤만" % x["이후"]) if x["이후"] else "처음부터"))
        print("이어 조사할 갈래 %d(빈 %d · 낡음 %d)" % (len(목), sum(1 for x in 목 if x["까닭"] == "빈"), sum(1 for x in 목 if x["까닭"] != "빈")))
        if a.json:
            _쓰기(a.json, {"형식": 형식, "일시": _지금(), "목록": 목})
        return 발견 if 목 else 통과
    except ValueError as e:
        print("입력 오류 — %s" % e)
        return 입력오류


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""표현실현 — 회사가 공시에서 **말로 준 물량 · 단가 변동률**과, 그 분기에 **실제로 나온 품목별 매출**을 짝짓는 대장 (NLP ②).

무엇을 하나
  B 갈래가 LLM 으로 적은 표현 행(`_raw/표현추출.json`)을 받아
    ① 원문 대조 — 공시 행의 인용이 그 보고서 원문의 지정 절(기본 「가격변동추이」)에 글자 그대로 있는가. 없으면 버린다
    ② 누락 검사 — 그 절의 크기 표현(정규식)이 어느 인용에도 안 들어갔으면 후보로 올린다
    ③ 밴드 — 표현을 `밴드사전.json`(키트 정본 · 실현을 보기 전에 고정)으로 숫자 구간에 옮긴다
    ④ 실현 — 연결 주석 「고객과의 계약에서 생기는 수익의 품목별 구분」에서 품목별 분기 매출을 뽑는다
       (1분기 = 당분기, 2 · 3분기 = 3개월, 4분기 = 사업보고서 연간 − 3분기 누적. 합계 검산)
    ⑤ 항등식 — 1 + 매출 변동 = (1 + 물량) × (1 + 단가) × (1 + 환율 변동). 한 항의 표현을 믿으면 다른 항이 실제로
       얼마였어야 하는지 구간(「실현 기반 구간」)이 나온다. 그 구간을 사전 밴드와 견준다 — 겹침 / 경계 / 밖
    ⑥ 짝 검사(두 표현의 곱이 실현 매출을 품나) · 채널 대조(공시 · 영문 · 구두) · 표현별 · 계열별 요약 · 가이던스
왜 있나 — 「말로 준 변동률은 밴드로 바꾼다」의 밴드에는 근거가 「증권사 추정 표와 대조」뿐이었다. 그 회사가 같은 말을
  썼을 때 실제로 몇 %였는지(매출이 허용하는 구간)를 근거 칸에 붙이려는 것이다. 첫 실측(2026-10-21 · 실험/표현실현): 국문 「소폭」이
  같은 회사 영문판에서 Low · Mid · High-single 로 갈렸고, 짝 30 중 20 이 실현을 품었다.
**값을 정하지 않는다.** 대장은 「이 회사가 이 말을 쓸 때 실제로 몇 %였나」의 관측만 쌓고, 가정 파일은 읽지도 고치지도 않는다.

사용
    python 스크립트/표현실현.py 가정.json                       # 가정 곁 _raw/표현추출.json → _raw/표현실현.json · _raw/표현실현_대장.csv
    python 스크립트/표현실현.py 가정.json --받기 --환율받기      # 없는 원문 · 제출이력 · 원달러 일별을 받는다(본체에서는 멈춘다)
    python 스크립트/표현실현.py 가정.json --단가통화 USD         # 원 | USD | 둘다(기본 — 둘 다 내고 더 맞는 쪽을 적는다)
    python 스크립트/표현실현.py 가정.json --절 가격변동추이 --품목 "A,B:표의 이름,기타"
    python 스크립트/표현실현.py --추출 경로.json --뿌리 회차폴더   # 가정 없이(시험 · 사본)

읽는 것 — 가정 곁 `_raw/`(또는 --뿌리)
    표현추출.json            B 갈래 산출(꼴은 아래). 영문 채널은 SEC 문서를 파싱하지 않고 갈래가 행으로 적는다
    dart_제출이력.json        dart_fetch 의 list.json 응답(정기공시). 없거나 모자라면 --받기 로 list.json 을 다시 받는다
    dart_기업개황.json        결산월(acc_mt) — 없으면 12월
    **/{접수번호}.txt         원문 텍스트(dart_fetch `원문` 이 `_raw/{딱지}/` 에 남긴 꼴). 없으면 --받기 로 `_raw/표현실현/` 에 받는다
    fx_USDKRW_일별.csv        원달러 일별 종가 캐시(일자,종가) — 네이버 환율 창구(하나은행 고시). 없으면 --환율받기
표현추출.json 꼴(형식 「표현추출 1」)
    {"형식": "표현추출 1", "회사": "…", "결산월": 12, "절": "가격변동추이", "단가통화": "USD" | "원" | null,
     "품목": ["A", {"이름": "B", "표": "표에 적힌 이름"}, "기타"],   ← 품목별 수익 표의 줄 순서 그대로 · 기타까지(합계 검산)
     "대조제외": [{"분기": "2022Q1", "제품": "B", "까닭": "연결 범위가 바뀐 분기"}],
     "행": [{"분기": "2026Q2", "제품": "A", "지표": "물량" | "단가", "채널": "공시" | "영문" | "구두",
             "접수": "<공시면 접수번호 · 아니면 출처 글>", "인용": "<원문 글자 그대로>", "표현": "<사전 꼴 — 소폭 · 30% 중반 · Mid-teen% …>",
             "방향": 1 | -1 | 0, "범위": "연결" | "<다른 범위>", "비고": "…"}],
     "가이던스": [{"대상분기": "2026Q3", "제품": "A", "지표": "물량", "채널": "구두", "출처": "…", "표현": "약 10%", "방향": 1}]}
    분기 = 회계연도 기준(회계연도 끝 해 + Q1~Q4 — 12월 결산이면 달력과 같다). 옛 이름도 읽는다 — 지표 「출하량 · 판매량」 → 물량,
    「ASP · 평균판매가격」 → 단가, 채널 「DART」 → 공시, 「424B4 · SEC」 → 영문.
내는 것
    _raw/표현실현.json — {"형식": "표현실현 1", 만든날, 설정, 입력, 원문대조, 실현매출, 대장, 짝검사, 채널대조, 표현별, 계열별,
                          가이던스, 기준비교, 신호}
    _raw/표현실현_대장.csv — 대장 행
    신호 종류: 인용 불일치 · 원문 없음 · 사전에 없는 표현 · 넓은 표현 · 짝 어긋남 · 채널 갈림 · 「약」 계열 밖 · 가이던스 미도래 ·
               가이던스 밖 · 인용 밖 크기 표현
종료 코드 — 0 통과 · 1 발견(인용이 원문에 없거나 원문이 없어 버린 행, 사전에 없는 표현) · 2 입력오류(추출 파일 없음 · 꼴 깨짐)
회사 · 업종 · 품목 이름은 이 도구에 한 글자도 없다 — 품목은 표현추출.json 의 「품목」 으로만 받는다.
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
import statistics
import sys
import time
import urllib.parse
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                            # noqa: BLE001
    pass

여기 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류  # noqa: E402

INF = float("inf")
사전경로 = os.path.join(여기, "밴드사전.json")
지표이름 = {"물량": "물량", "출하량": "물량", "판매량": "물량", "비트": "물량", "출하": "물량",
         "단가": "단가", "asp": "단가", "평균판매가격": "단가", "가격": "단가", "판매단가": "단가"}
채널이름 = {"공시": "공시", "dart": "공시", "영문": "영문", "424b4": "영문", "sec": "영문", "20-f": "영문",
         "구두": "구두", "컨콜": "구두", "컨퍼런스콜": "구두"}


# ═════════════════════════════════════ 글

def 정규(s):
    return re.sub(r"\s+", " ", (s or "").replace("&cr;", " ")).strip()


def 무공백(s):
    return re.sub(r"\s+", "", (s or "").replace("&cr;", ""))


def 키꼴(표현):
    return re.sub(r"[\s\-·]", "", (표현 or "").strip()).lower()


# ═════════════════════════════════════ 밴드 사전

def 사전읽기(경로=None):
    return json.load(io.open(경로 or 사전경로, encoding="utf-8"))


_없음 = "사전없음"


def 밴드(표현, 사전):
    """(하한, 상한) 절댓값 %. 상한 없음 = INF. 크기 없음 = None. 사전에 없으면 「사전없음」."""
    k = 키꼴(표현)
    고 = {키꼴(a): b for a, b in (사전.get("고정") or {}).items()}
    if k in 고:
        v = 고[k]
        return None if v is None else (float(v[0]), float(v[1]))
    자, 십, 약 = 사전["자릿수칸"], 사전["십단위칸"], float(사전.get("약폭", 1))
    m = re.fullmatch(r"한자릿수(초중반|중후반|초반|중반|후반)", k)
    if m:
        a, b = 자[m.group(1)]
        return (float(a), float(b))
    m = re.fullmatch(r"약?(\d+)0%(초중반|중후반|초반|중반|후반)", k)
    if m:
        n = int(m.group(1)) * 10
        a, b = 십[m.group(2)]
        return (float(n + a), float(n + b))
    m = re.fullmatch(r"약?(\d+(?:\.\d+)?)%이상", k) or re.fullmatch(r"over(\d+(?:\.\d+)?)%", k)
    if m:
        return (float(m.group(1)), INF)
    m = re.fullmatch(r"(\d+(?:\.\d+)?)%미만", k)
    if m:
        return (0.0, float(m.group(1)))
    m = re.fullmatch(r"약?(\d+(?:\.\d+)?)%(?:수준|가량|내외|안팎)?", k) or re.fullmatch(r"around(\d+(?:\.\d+)?)%", k)
    if m:
        n = float(m.group(1))
        return (n - 약, n + 약)
    m = re.fullmatch(r"(low|mid|high|lowmid|midhigh)single%?", k)
    if m:
        a, b = 사전["영문_single"][m.group(1)]
        return (float(a), float(b))
    m = re.fullmatch(r"(low|mid|high|lowmid|midhigh)teens?%?", k)
    if m:
        a, b = 사전["영문_teen"][m.group(1)]
        return (float(a), float(b))
    m = re.fullmatch(r"(low|mid|high|lowmid|midhigh)(\d+)0s?%", k)
    if m:
        n = int(m.group(2)) * 10
        a, b = 사전["영문_십단위"][m.group(1)]
        return (float(n + a), float(n + b))
    return _없음


def 부호밴드(표현, 방향, 사전):
    b = 밴드(표현, 사전)
    if b is None or b == _없음:
        return b
    lo, hi = b
    if 방향 == 0 or (lo < 0 < hi):
        return (min(lo, -hi) if 방향 == 0 and lo >= 0 else lo, hi)
    return (lo, hi) if 방향 > 0 else (-hi, -lo)


def 계열(표현):
    k = 키꼴(표현)
    if re.search(r"소폭|slight", k):
        return "소폭 · Slight"
    if re.search(r"유사|동일|수준$|flat", k) and not re.search(r"\d", k):
        return "유사 · Flat"
    if re.search(r"^약|around|수준|가량|내외|안팎", k) or re.fullmatch(r"\d+(\.\d+)?%", k):
        return "약 N% · Around"
    if re.search(r"이상|over|미만", k):
        return "N% 이상 · Over"
    if re.search(r"초중반|중후반|lowmid|midhigh", k):
        return "두 칸 걸침"
    if re.search(r"중반|^mid", k):
        return "중반 · Mid"
    if re.search(r"초반|^low", k):
        return "초반 · Low"
    if re.search(r"후반|^high", k):
        return "후반 · High"
    return "그 밖"


# ═════════════════════════════════════ 원문

def 원문경로(접수, 뿌리들):
    for 뿌리 in 뿌리들:
        if not 뿌리 or not os.path.isdir(뿌리):
            continue
        정 = glob.glob(os.path.join(뿌리, "**", "%s.txt" % 접수), recursive=True)
        if 정:
            return max(정, key=os.path.getsize)
        덧 = glob.glob(os.path.join(뿌리, "**", "%s*.txt" % 접수), recursive=True)
        if 덧:
            return max(덧, key=os.path.getsize)
    return None


def 원문받기(접수, 딱지="표현실현"):
    """dart_fetch.원문 으로 받는다(뷰어 우회 포함). 본체에서는 멈춘다."""
    import dart_fetch                                        # noqa: PLC0415
    import 본체가드                                          # noqa: PLC0415
    본체가드.본체면멈춘다(dart_fetch.ROOT)
    dart_fetch._준비()
    dart_fetch.원문(접수, 딱지)
    return dart_fetch.RAW


_머리 = re.compile(r"\n\s*(?:\d{1,2}\s?\.|[가-하]\s?\.|\(\d{1,2}\)|[IVX]{1,4}\.)\s*[가-힣A-Za-z]")


def 절조각들(글, 절이름, 최대=3000):
    """절 이름이 나오는 자리마다 다음 머리말(줄 첫머리의 「3.」 「다.」 「(2)」 「III.」)까지 — 목차 자리도 함께 나오므로 전부 돌려준다."""
    조각 = []
    for m in re.finditer(re.escape(절이름), 글):
        뒤 = 글[m.end():m.end() + 최대]
        k = _머리.search(뒤)
        조각.append(정규(글[m.start():m.end() + (k.start() if k else len(뒤))]))
    return 조각


# ═════════════════════════════════════ 보고서 목록 · 분기

def 보고종류(report_nm, 결산월=12):
    """(회계연도 끝 해, 1Q|H|3Q|FY) — 회계연도 끝 해로 이름을 붙인다."""
    m = re.search(r"\((\d{4})\.(\d{2})\)", report_nm or "")
    if not m:
        return None
    y, mm = int(m.group(1)), int(m.group(2))
    if "사업보고서" in report_nm:
        종 = "FY"
    elif "반기보고서" in report_nm:
        종 = "H"
    elif "분기보고서" in report_nm:
        off = (mm - 결산월) % 12
        종 = {3: "1Q", 9: "3Q"}.get(off)
        if 종 is None:
            return None
    else:
        return None
    off = (mm - 결산월) % 12
    회 = y if off == 0 else (y + 1 if mm > 결산월 else y)
    return 회, 종


def 보고서고르기(목록, 결산월=12):
    """{(회계연도, 종류): 행} — 같은 기간에 정정본이 있으면 늦게 낸 것(접수번호가 큰 것)."""
    낸 = {}
    for r in 목록 or []:
        k = 보고종류(r.get("report_nm"), 결산월)
        if not k:
            continue
        if k not in 낸 or (r.get("rcept_no") or "") > (낸[k].get("rcept_no") or ""):
            낸[k] = r
    return 낸


def 분기달(분기, 결산월=12):
    """회계 분기 → 달력 (해, 달) 셋."""
    y, n = int(분기[:4]), int(분기[-1])
    끝 = 결산월 - 3 * (4 - n)
    해 = y
    while 끝 <= 0:
        끝 += 12
        해 -= 1
    달들 = []
    for d in (끝 - 2, 끝 - 1, 끝):
        hh, dd = 해, d
        while dd <= 0:
            dd += 12
            hh -= 1
        달들.append((hh, dd))
    return 달들


def 앞분기(q):
    y, n = int(q[:4]), int(q[-1])
    return "%dQ4" % (y - 1) if n == 1 else "%dQ%d" % (y, n - 1)


def 제출기한(분기, 결산월=12):
    해, 달 = 분기달(분기, 결산월)[-1]
    if 달 == 12:
        말 = datetime.date(해, 12, 31)
    else:
        말 = datetime.date(해, 달 + 1, 1) - datetime.timedelta(days=1)
    return 말 + datetime.timedelta(days=90 if 분기.endswith("Q4") else 45)


# ═════════════════════════════════════ 품목별 수익 표

_수 = r"\(?-?[\d,]+\)?"


def _숫자(s):
    s = s.strip()
    neg = s.startswith("(") or s.startswith("-")
    v = int(re.sub(r"[^\d]", "", s))
    return -v if neg else v


def 품목표(글, 표이름들, 꼴수):
    """연결 표(첫 번째로 합계가 맞는 표)의 당기 값.
    ㄴ꼴 — 「A B 기타 … 수익(매출액) n…」(품목 이름이 머리에 이어 나오고 숫자는 품목 · 합계 순, 꼴수 2 면 3개월 · 누적 짝)
    ㄱ꼴 — 「A n n B n n 기타 n n 합 계 n n」(행마다 숫자 2 · 4개 — 당기[3개월 누적] 전기)
    돌려줌 — ({품목: 값}, {품목: 누적}, 합계, 합계누적, 꼴, 합계차) 또는 None."""
    t = 정규(글)
    n = len(표이름들)
    이음 = r"\s+".join(re.escape(x) for x in 표이름들)
    후보 = []
    for m in re.finditer(r"%s.{0,200}?수익(?:\(매출액\))? ((?:%s ){%d})" % (이음, _수, (n + 1) * 꼴수), t):
        ns = [_숫자(x) for x in m.group(1).split()]
        if 꼴수 == 1:
            값 = dict(zip(표이름들, ns[:n]))
            후보.append((값, {}, ns[n], None, "ㄴ꼴"))
        else:
            값 = {표이름들[i]: ns[2 * i] for i in range(n)}
            누 = {표이름들[i]: ns[2 * i + 1] for i in range(n)}
            후보.append((값, 누, ns[2 * n], ns[2 * n + 1], "ㄴ꼴"))
    줄 = "".join(r"%s ((?:%s ){%d})" % (re.escape(x), _수, 2 * 꼴수) for x in 표이름들)
    for m in re.finditer(줄 + r"합 ?계 ((?:%s ?){%d})" % (_수, 2 * 꼴수), t):
        g = [[_숫자(x) for x in m.group(i).split()] for i in range(1, n + 2)]
        값 = {표이름들[i]: g[i][0] for i in range(n)}
        누 = {표이름들[i]: g[i][1] for i in range(n)} if 꼴수 == 2 else {}
        후보.append((값, 누, g[n][0], g[n][1] if 꼴수 == 2 else None, "ㄱ꼴"))
    if not 후보:
        return None
    후보.sort(key=lambda c: 0 if c[4] == "ㄴ꼴" else 1)
    for c in 후보:
        if sum(c[0].values()) == c[2]:
            return c + (0,)
    c = 후보[0]
    return c + (sum(c[0].values()) - c[2],)


def 분기매출(보고, 표이름들, 읽기, 필요분기):
    """{분기: {"값": {품목: 값}, "합계", "접수", "만든법", "합계차"}} · 검산 줄 목록."""
    읽은, 검 = {}, []

    def 표(k):
        if k in 읽은:
            return 읽은[k]
        r = 보고.get(k)
        v = None
        if r:
            글 = 읽기(r["rcept_no"])
            if 글 is not None:
                v = 품목표(글, 표이름들, 2 if k[1] in ("H", "3Q") else 1)
                if v is None:
                    검.append("%d %s %s 품목 표 못 찾음" % (k[0], k[1], r["rcept_no"]))
                else:
                    검.append("%d %s %s %s 합계차 %d" % (k[0], k[1], r["rcept_no"], v[4], v[5]))
            else:
                검.append("%d %s %s 원문 없음" % (k[0], k[1], r["rcept_no"]))
        읽은[k] = v
        return v

    낸 = {}
    for q in sorted(필요분기):
        y, n = int(q[:4]), int(q[-1])
        if n == 1:
            v = 표((y, "1Q"))
            if v:
                낸[q] = dict(값=v[0], 합계=v[2], 접수=보고[(y, "1Q")]["rcept_no"], 만든법="1분기보고서 당분기", 합계차=v[5])
        elif n in (2, 3):
            k = (y, "H" if n == 2 else "3Q")
            v = 표(k)
            if v:
                낸[q] = dict(값=v[0], 합계=v[2], 접수=보고[k]["rcept_no"],
                            만든법="반기보고서 3개월" if n == 2 else "3분기보고서 3개월", 합계차=v[5])
        else:
            f, s = 표((y, "FY")), 표((y, "3Q"))
            if f and s and s[1]:
                값 = {p: f[0][p] - s[1][p] for p in 표이름들}
                낸[q] = dict(값=값, 합계=f[2] - (s[3] or 0), 접수="%s − %s" % (보고[(y, "FY")]["rcept_no"], 보고[(y, "3Q")]["rcept_no"]),
                            만든법="사업보고서 연간 − 3분기 누적", 합계차=f[5] + s[5])
    return 낸, 검


# ═════════════════════════════════════ 환율

def 환율읽기(경로):
    if not os.path.exists(경로):
        return {}
    d = {}
    for r in csv.DictReader(io.open(경로, encoding="utf-8")):
        try:
            d[r["일자"]] = float(r["종가"])
        except (KeyError, ValueError):
            continue
    return d


def 환율받기(경로, 시작):
    """네이버 환율 창구(하나은행 고시) — pageSize 20 이 상한(100 은 400). 시작일까지 거슬러 받아 캐시에 합친다."""
    H = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    있 = 환율읽기(경로)
    page = 1
    while True:
        u = "https://api.stock.naver.com/marketindex/exchange/FX_USDKRW/prices?page=%d&pageSize=20" % page
        j = None
        for i in range(4):
            try:
                j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=30).read().decode("utf-8"))
                break
            except Exception:                                # noqa: BLE001
                time.sleep(1.5 * (i + 1))
        if not j:
            break
        for x in j:
            있[x["localTradedAt"]] = float(str(x["closePrice"]).replace(",", ""))
        if j[-1]["localTradedAt"] < 시작:
            break
        page += 1
        time.sleep(0.2)
    with io.open(경로, "w", encoding="utf-8") as f:
        f.write("일자,종가\n" + "".join("%s,%s\n" % (k, v) for k, v in sorted(있.items())))
    return 있


def 분기평균(일별, 분기, 결산월=12):
    달 = {"%04d-%02d" % ym for ym in 분기달(분기, 결산월)}
    v = [x for d, x in 일별.items() if d[:7] in 달]
    return (sum(v) / len(v), len(v)) if v else (None, 0)


# ═════════════════════════════════════ 셈

def 역산(u, 다른):
    """(1+u) = (1+x)(1+o) → x 구간(%). 다른 = (lo, hi) %(INF 허용)."""
    lo, hi = 다른
    a = -INF if hi == INF else ((1 + u) / (1 + hi / 100) - 1) * 100
    b = INF if lo <= -100 else ((1 + u) / (1 + lo / 100) - 1) * 100
    return (a, b)


def 판정(구간, 사전, 경계폭=1.0):
    a, b = 구간
    c, d = 사전
    lo, hi = max(a, c), min(b, d)
    if lo <= hi:
        return "겹침", 0.0
    gap = lo - hi
    return ("경계" if gap <= 경계폭 else "밖"), gap


def _반올림(x):
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return None
    return round(x, 3)


def _구간(t):
    return None if t is None else [_반올림(t[0]), _반올림(t[1])]


def fmt(x):
    if x is None:
        return ""
    if x in (INF, -INF):
        return "∞" if x > 0 else "−∞"
    return "%.1f" % x


def _글구간(t):
    return "" if not t else "%s ~ %s" % (fmt(t[0]), fmt(t[1]))


# ═════════════════════════════════════ 본체

def 행정리(r):
    r = dict(r)
    r["지표"] = 지표이름.get(str(r.get("지표", "")).strip().lower(), 지표이름.get(str(r.get("지표", "")).strip(), r.get("지표")))
    r["채널"] = 채널이름.get(str(r.get("채널", "")).strip().lower(), r.get("채널"))
    r["방향"] = int(r.get("방향", 0) or 0)
    r.setdefault("범위", "연결")
    return r


def 품목읽기(추출, 인자=None):
    """[(이름, 표 이름)] — 인자 「A,B:표 이름,기타」 가 있으면 그것을, 없으면 추출 파일의 「품목」."""
    if 인자:
        낸 = []
        for x in 인자.split(","):
            if not x.strip():
                continue
            a, _, b = x.partition(":")
            낸.append((a.strip(), (b or a).strip()))
        return 낸
    낸 = []
    for x in 추출.get("품목") or []:
        if isinstance(x, dict):
            낸.append((x.get("이름"), x.get("표") or x.get("이름")))
        else:
            낸.append((x, x))
    return 낸


def 실행(뿌리, 추출경로=None, 절=None, 품목인자=None, 단가통화="둘다", 받기=False, 환율받기_=False, 시작=None, 사전=None):
    raw = os.path.join(뿌리, "_raw")
    추출경로 = 추출경로 or os.path.join(raw, "표현추출.json")
    if not os.path.exists(추출경로):
        raise FileNotFoundError("표현추출.json 이 없습니다: %s" % 추출경로)
    추출 = json.load(io.open(추출경로, encoding="utf-8"))
    if not isinstance(추출.get("행"), list):
        raise ValueError("표현추출.json 에 「행」 목록이 없습니다")
    사전 = 사전 or 사전읽기()
    경계폭 = float((사전.get("판정") or {}).get("경계폭", 1.0))
    신설 = 사전.get("신호") or {}
    절 = 절 or 추출.get("절") or "가격변동추이"
    단가통화 = (추출.get("단가통화") if 단가통화 in (None, "둘다") and 추출.get("단가통화") else 단가통화) or "둘다"
    개황 = {}
    try:
        개황 = json.load(io.open(os.path.join(raw, "dart_기업개황.json"), encoding="utf-8"))
    except (IOError, OSError, ValueError):
        pass
    결산월 = int(추출.get("결산월") or 개황.get("acc_mt") or 12)
    품목 = 품목읽기(추출, 품목인자)
    표이름 = {a: b for a, b in 품목}
    뿌리들 = [raw]
    try:
        import dart_fetch                                    # noqa: PLC0415
        뿌리들.append(dart_fetch.RAW)
    except Exception:                                        # noqa: BLE001
        pass
    신호 = []

    def 알림(종류, 대상, 값, 문턱, 글, 등급="경보"):
        신호.append({"출처": "표현실현", "종류": 종류, "대상": 대상, "값": 값, "문턱": 문턱, "글": 글, "등급": 등급})

    글캐시 = {}

    def 읽기(접수):
        if 접수 in 글캐시:
            return 글캐시[접수]
        p = 원문경로(접수, 뿌리들)
        if p is None and 받기:
            try:
                원문받기(접수)
                p = 원문경로(접수, 뿌리들)
            except SystemExit:
                raise
            except Exception as e:                           # noqa: BLE001
                sys.stderr.write("원문 %s 받기 실패 — %s\n" % (접수, e))
        글캐시[접수] = None if p is None else io.open(p, encoding="utf-8", errors="replace").read()
        return 글캐시[접수]

    # ① 원문 대조
    행, 버림, 누락 = [], [], []
    절캐시 = {}
    for r0 in 추출["행"]:
        r = 행정리(r0)
        if r["채널"] == "공시":
            글 = 읽기(str(r.get("접수")))
            if 글 is None:
                버림.append(dict(분기=r.get("분기"), 제품=r.get("제품"), 지표=r.get("지표"), 까닭="원문 없음", 인용=r.get("인용")))
                알림("원문 없음", "%s %s %s" % (r.get("분기"), r.get("제품"), r.get("지표")), r.get("접수"), "원문 텍스트",
                   "접수번호 %s 의 원문이 없어 인용을 대조하지 못했다 — --받기 로 받거나 접수번호를 고친다" % r.get("접수"))
                continue
            조각 = 절캐시.setdefault(r["접수"], 절조각들(글, 절))
            if not any(정규(r.get("인용")) in c for c in 조각):
                까닭 = "인용이 원문에 없음" if 조각 else "절 「%s」 을 원문에서 못 찾음" % 절
                버림.append(dict(분기=r.get("분기"), 제품=r.get("제품"), 지표=r.get("지표"), 까닭=까닭, 인용=r.get("인용")))
                알림("인용 불일치", "%s %s %s" % (r.get("분기"), r.get("제품"), r.get("지표")), r.get("인용"), "원문 글자 그대로",
                   "%s — 이 행을 버렸다. LLM 추출이 원문을 고쳐 적었거나 엉뚱한 보고서를 가리킨다. 원문을 보고 인용을 다시 적는다" % 까닭)
                continue
        행.append(r)
    pat = re.compile(r"(한 ?자릿 ?수 ?(?:초중반|중후반|초반|중반|후반)|약 ?\d+% ?(?:초반|중반|후반|중후반|수준|가량)?|"
                     r"\d+% ?(?:초반|중반|후반|중후반|이상|미만|수준|가량)|소폭|유사한 수준|동일한 수준)")
    for 접수, 조각 in 절캐시.items():
        인용들 = [정규(r["인용"]) for r in 행 if r.get("접수") == 접수 and r["채널"] == "공시"]
        본 = max(조각, key=len) if 조각 else ""
        for m in pat.finditer(본):
            s, e = m.span()
            덮 = False
            for q in 인용들:
                i = 본.find(q)
                while i >= 0:
                    if i <= s and e <= i + len(q):
                        덮 = True
                        break
                    i = 본.find(q, i + 1)
                if 덮:
                    break
            if not 덮:
                누락.append(dict(접수=접수, 표현=m.group(0), 앞뒤=본[max(0, s - 40):e + 30]))
    for x in 누락[:20]:
        알림("인용 밖 크기 표현", x["접수"], x["표현"], "인용 안", "절 안의 「%s」 가 어느 인용에도 안 들어갔다 — 변동률 표현이면 행을 더하고, "
           "구성비 · 다른 뜻이면 그대로 둔다(…%s…)" % (x["표현"], x["앞뒤"]), "참고")

    # 사전
    사전없음 = sorted({(r["채널"], r["표현"]) for r in 행 if 밴드(r["표현"], 사전) == _없음})
    for 채, e in 사전없음:
        알림("사전에 없는 표현", 채, e, "밴드사전.json", "표현 「%s」 이 밴드사전에 없다 — 사전에 칸을 더하고 개정이력에 적거나, 사전 꼴로 다시 적는다" % e)

    # 제외
    제외 = {(x.get("분기"), x.get("제품")): x.get("까닭", "") for x in (추출.get("대조제외") or [])}

    # ④ 실현 — 보고서 목록
    목록 = []
    제출 = os.path.join(raw, "dart_제출이력.json")
    try:
        j = json.load(io.open(제출, encoding="utf-8"))
        목록 = j.get("list") if isinstance(j, dict) else j
    except (IOError, OSError, ValueError):
        목록 = []
    분기들 = sorted({r["분기"] for r in 행 if re.fullmatch(r"\d{4}Q[1-4]", str(r.get("분기", "")))})
    필요 = set(분기들) | {앞분기(q) for q in 분기들}
    for g in 추출.get("가이던스") or []:
        q = str(g.get("대상분기", ""))
        if re.fullmatch(r"\d{4}Q[1-4]", q):
            필요 |= {q, 앞분기(q)}
    보고 = 보고서고르기(목록, 결산월)
    if 받기 and 필요:
        첫해 = int(min(필요)[:4]) - 1
        if not any(k[0] <= 첫해 + 1 for k in 보고):
            목록 = (목록 or []) + _목록받기(개황.get("corp_code") or 추출.get("고유번호"), 시작 or "%d0101" % 첫해)
            보고 = 보고서고르기(목록, 결산월)
    실매출, 검산 = 분기매출(보고, [b for _, b in 품목], 읽기, 필요) if 품목 else ({}, ["품목이 없다 — 표현추출.json 의 「품목」 을 적는다"])
    # 품목 이름(행의 제품)으로 다시 단다
    역 = {b: a for a, b in 품목}
    for q, v in 실매출.items():
        v["값"] = {역.get(k, k): x for k, x in v["값"].items()}

    # 환율
    fx경로 = os.path.join(raw, "fx_USDKRW_일별.csv")
    일별 = 환율읽기(fx경로)
    if 환율받기_ and 필요 and 단가통화 in ("USD", "둘다"):
        y0, m0 = 분기달(min(필요), 결산월)[0]
        일별 = 환율받기(fx경로, "%04d-%02d-01" % (y0, m0))

    def 변동(q, p):
        if q not in 실매출 or 앞분기(q) not in 실매출:
            return None
        a, b = 실매출[q]["값"].get(p), 실매출[앞분기(q)]["값"].get(p)
        if not a or not b:
            return None
        r = a / b - 1
        f0, f1 = 분기평균(일별, q, 결산월)[0], 분기평균(일별, 앞분기(q), 결산월)[0]
        f = (f0 / f1 - 1) if (f0 and f1) else None
        return r, f

    기준들 = ["원", "USD"] if 단가통화 == "둘다" else [단가통화]

    def 유효(o):
        b = 부호밴드(o["표현"], o["방향"], 사전)
        return b not in (None, _없음)

    def 다른항(r):
        반대 = "단가" if r["지표"] == "물량" else "물량"
        차례 = [r["채널"]] + (["영문"] if r["채널"] != "영문" else [])
        for 채 in 차례:
            for o in 행:
                if (o["분기"], o["제품"], o["지표"], o["채널"]) != (r["분기"], r["제품"], 반대, 채):
                    continue
                if o.get("범위") != "연결" or not 유효(o):
                    continue
                if 채 == "공시" and r["채널"] == "공시" and o.get("접수") != r.get("접수"):
                    continue
                return o
        return None

    대장 = []
    for r in 행:
        사밴 = 부호밴드(r["표현"], r["방향"], 사전)
        q, p = r["분기"], r["제품"]
        rec = dict(분기=q, 제품=p, 지표=r["지표"], 채널=r["채널"], 표현=r["표현"], 방향=r["방향"],
                   사전밴드=None if 사밴 in (None, _없음) else _구간(사밴), 인용=r.get("인용"), 출처=r.get("접수"),
                   범위=r.get("범위"), 비고=r.get("비고", ""), 계열=계열(r["표현"]))
        if 사밴 == _없음:
            rec.update(판정="사전에 없음")
            대장.append(rec)
            continue
        if r.get("범위") != "연결" or (q, p) in 제외:
            rec.update(판정="대조 제외", 사유=제외.get((q, p)) or "범위가 연결 매출과 다름(%s)" % r.get("범위"))
            대장.append(rec)
            continue
        v = 변동(q, p)
        if v is None:
            rec.update(판정="대조 불가", 사유="실현 매출 없음(%s · %s)" % (앞분기(q), q))
            대장.append(rec)
            continue
        r_krw, f = v
        rec.update(매출변동_원=_반올림(r_krw * 100), 환율변동=_반올림(None if f is None else f * 100),
                   매출변동_USD=_반올림(None if f is None else ((1 + r_krw) / (1 + f) - 1) * 100))
        o = 다른항(r)
        if not o:
            rec.update(판정="짝 없음", 사유="같은 분기 다른 항의 크기 표현이 없음")
            대장.append(rec)
            continue
        ob = 부호밴드(o["표현"], o["방향"], 사전)
        rec["짝"] = "%s %s 「%s」" % (o["채널"], o["지표"], o["표현"])
        판들 = {}
        for 기 in 기준들:
            if 기 == "USD" and f is None:
                rec["판정_USD"] = "환율 없음"
                continue
            u = r_krw if 기 == "원" else (1 + r_krw) / (1 + f) - 1
            g = 역산(u, ob)
            rec["실현구간_" + 기] = _구간(g)
            if 사밴 is None:
                ok = (g[0] > 0) if r["방향"] > 0 else ((g[1] < 0) if r["방향"] < 0 else (g[0] <= 1 and g[1] >= -1))
                반 = (g[1] < 0) if r["방향"] > 0 else ((g[0] > 0) if r["방향"] < 0 else False)
                rec["판정_" + 기] = "방향 일치" if ok else ("방향 불일치" if 반 else "방향 판정 불가")
            else:
                j, gap = 판정(g, 사밴, 경계폭)
                rec["판정_" + 기] = j
                rec["거리_" + 기] = _반올림(gap)
            판들[기] = rec["판정_" + 기]
        대장.append(rec)

    # ⑥ 짝 검사
    짝 = []
    for 채 in ("공시", "영문", "구두"):
        for q in 분기들:
            for p, _ in 품목:
                if (q, p) in 제외:
                    continue
                b = [r for r in 행 if (r["분기"], r["제품"], r["채널"], r["지표"]) == (q, p, 채, "물량") and r.get("범위") == "연결" and 유효(r)]
                a = [r for r in 행 if (r["분기"], r["제품"], r["채널"], r["지표"]) == (q, p, 채, "단가") and r.get("범위") == "연결" and 유효(r)]
                if not (b and a):
                    continue
                v = 변동(q, p)
                if v is None:
                    continue
                r_krw, f = v
                bb, ab = 부호밴드(b[0]["표현"], b[0]["방향"], 사전), 부호밴드(a[0]["표현"], a[0]["방향"], 사전)
                x = r_krw * 100
                rec = dict(분기=q, 제품=p, 채널=채, 물량=b[0]["표현"], 단가=a[0]["표현"], 방향="%+d/%+d" % (b[0]["방향"], a[0]["방향"]),
                           실현_원화매출변동=_반올림(x), 환율변동=_반올림(None if f is None else f * 100))
                for 기 in 기준들:
                    k = 1.0 if 기 == "원" else (None if f is None else 1 + f)
                    if k is None:
                        rec["판정_USD"] = "환율 없음"
                        continue
                    lo = ((1 + bb[0] / 100) * (1 + ab[0] / 100) * k - 1) * 100
                    hi = INF if INF in (bb[1], ab[1]) else ((1 + bb[1] / 100) * (1 + ab[1] / 100) * k - 1) * 100
                    j, gap = 판정((x, x), (lo, hi), 경계폭)
                    rec["함의_" + 기] = _구간((lo, hi))
                    rec["판정_" + 기] = j
                    rec["벗어난거리_" + 기] = _반올림(0.0 if j == "겹침" else (x - hi if x > hi else x - lo))
                짝.append(rec)

    # 주 기준 — 하나를 선언했으면 그것, 둘다면 짝 검사 겹침 수가 많은 쪽(같으면 원)
    셈 = {기: dict(짝=sum(1 for z in 짝 if z.get("판정_" + 기) in ("겹침", "경계", "밖")),
                  겹침=sum(1 for z in 짝 if z.get("판정_" + 기) == "겹침"),
                  경계=sum(1 for z in 짝 if z.get("판정_" + 기) == "경계"),
                  밖=sum(1 for z in 짝 if z.get("판정_" + 기) == "밖")) for 기 in 기준들}
    if len(기준들) == 1:
        주 = 기준들[0]
        주까닭 = "선언된 단가 통화(%s)" % 주
    else:
        주 = "USD" if 셈.get("USD", {}).get("겹침", 0) > 셈.get("원", {}).get("겹침", 0) else "원"
        주까닭 = "단가 통화를 선언하지 않아 짝 검사 겹침이 많은 쪽(원 %d · USD %d)" % (셈["원"]["겹침"], 셈["USD"]["겹침"])
    for rec in 대장:
        if "판정_" + 주 in rec:
            rec["판정"] = rec["판정_" + 주]
            if "거리_" + 주 in rec:
                rec["거리"] = rec["거리_" + 주]
            rec["실현구간"] = rec.get("실현구간_" + 주)
    for z in 짝:
        z["판정"] = z.get("판정_" + 주)

    # 채널 대조 — 공시 행마다 같은 분기 · 제품 · 지표의 영문 · 구두
    대조 = []
    for r in 행:
        if r["채널"] != "공시" or r.get("범위") != "연결":
            continue
        for 채 in ("영문", "구두"):
            e = [o for o in 행 if o["채널"] == 채 and (o["분기"], o["제품"], o["지표"]) == (r["분기"], r["제품"], r["지표"])]
            if not e:
                continue
            e = e[0]
            kb, eb = 부호밴드(r["표현"], r["방향"], 사전), 부호밴드(e["표현"], e["방향"], 사전)
            if _없음 in (kb, eb):
                같 = "사전에 없음"
            elif kb is None or eb is None:
                같 = "방향만" + (" 같음" if (r["방향"] == e["방향"]) else " 다름")
            else:
                같 = "겹침" if 판정(kb, eb, 0.0)[0] == "겹침" else "다름"
            대조.append(dict(분기=r["분기"], 제품=r["제품"], 지표=r["지표"], 상대=채, 공시=r["표현"], 공시방향=r["방향"],
                            상대표현=e["표현"], 상대방향=e["방향"], 공시밴드=_구간(kb) if kb not in (None, _없음) else None,
                            상대밴드=_구간(eb) if eb not in (None, _없음) else None, 판정=같))

    # 표현별 · 계열별(주 기준)
    묶음, 계묶 = {}, {}
    for rec in 대장:
        if rec.get("판정") in ("겹침", "경계", "밖"):
            묶음.setdefault((rec["채널"], rec["표현"]), []).append(rec)
            계묶.setdefault(rec["계열"], []).append(rec)
    표현별 = []
    for (채, e), v in sorted(묶음.items()):
        mids = []
        for x in v:
            g = x.get("실현구간") or [None, None]
            if g[0] is not None and g[1] is not None:
                mids.append(abs((g[0] + g[1]) / 2))
        b = 밴드(e, 사전)
        표현별.append(dict(채널=채, 표현=e, 사전밴드=_구간(b) if b not in (None, _없음) else None, 관측=len(v),
                         겹침=sum(1 for x in v if x["판정"] == "겹침"), 경계=sum(1 for x in v if x["판정"] == "경계"),
                         밖=sum(1 for x in v if x["판정"] == "밖"),
                         중점_중앙값=None if not mids else round(statistics.median(mids), 1),
                         사례=["%s %s %s %s" % (x["분기"], x["제품"], x["지표"], x["판정"]) for x in v]))
    계열별 = [dict(계열=k, 관측=len(v), 겹침=sum(1 for x in v if x["판정"] == "겹침"),
                 경계=sum(1 for x in v if x["판정"] == "경계"), 밖=sum(1 for x in v if x["판정"] == "밖"))
           for k, v in sorted(계묶.items())]

    # 가이던스
    가이 = []
    오늘 = datetime.date.today()
    for g in 추출.get("가이던스") or []:
        q = str(g.get("대상분기", ""))
        p = g.get("제품")
        지 = 지표이름.get(str(g.get("지표", "")).strip().lower(), 지표이름.get(str(g.get("지표", "")).strip(), g.get("지표")))
        rec = dict(대상분기=q, 제품=p, 지표=지, 채널=채널이름.get(str(g.get("채널", "")).lower(), g.get("채널")),
                   표현=g.get("표현"), 방향=int(g.get("방향", 0) or 0), 출처=g.get("출처"))
        if not re.fullmatch(r"\d{4}Q[1-4]", q):
            rec["상태"] = "대상분기 꼴이 아니다"
        elif 변동(q, p) is None:
            기한 = 제출기한(q, 결산월)
            rec["제출기한"] = 기한.isoformat()
            rec["상태"] = "보고 시점 미도래" if 오늘 <= 기한 else "실현 매출 없음 — 원문을 받는다(--받기)"
            알림("가이던스 미도래" if 오늘 <= 기한 else "가이던스 실현 없음", "%s %s %s" % (q, p, 지), g.get("표현"), 기한.isoformat(),
               "가이던스 「%s」(%s)의 실현은 %s 분기 보고서(제출기한 %s) 뒤에 짝지어진다 — 그때 이 도구를 다시 돌린다"
               % (g.get("표현"), g.get("출처") or "", q, 기한.isoformat()), "참고")
        else:
            gb = 부호밴드(g.get("표현"), rec["방향"], 사전)
            r_krw, f = 변동(q, p)
            반대 = "단가" if 지 == "물량" else "물량"
            o = next((o for o in 행 if (o["분기"], o["제품"], o["지표"]) == (q, p, 반대) and 유효(o)), None)
            if gb in (None, _없음) or not o:
                rec["상태"] = "실현은 있으나 짝이 없다(같은 분기 다른 항의 표현)"
            else:
                u = r_krw if 주 == "원" or f is None else (1 + r_krw) / (1 + f) - 1
                구 = 역산(u, 부호밴드(o["표현"], o["방향"], 사전))
                j, gap = 판정(구, gb, 경계폭)
                rec.update(상태="짝지음", 실현구간=_구간(구), 짝="%s %s 「%s」" % (o["채널"], o["지표"], o["표현"]), 판정=j, 거리=_반올림(gap))
                if j == "밖":
                    알림("가이던스 밖", "%s %s %s" % (q, p, 지), g.get("표현"), _글구간(gb),
                       "가이던스 「%s」 의 실현 기반 구간이 %s 로 밴드 밖이다 — 이 회사 가이던스를 시나리오 근거로 쓸 때 이 이력을 적는다" % (g.get("표현"), _글구간(구)), "참고")
        가이.append(rec)

    # 신호 — 넓은 표현 · 짝 어긋남 · 채널 갈림 · 「약」 계열
    넓 = float(신설.get("넓은폭", 8))
    넓은 = {}
    for r in 행:
        b = 밴드(r["표현"], 사전)
        if b not in (None, _없음) and b[1] != INF and (b[1] - b[0]) >= 넓 and r["채널"] in ("공시", "구두"):
            넓은.setdefault((r["채널"], r["표현"]), []).append(r)
    for (채, e), v in sorted(넓은.items()):
        영 = []
        for r in v:
            x = next((o for o in 행 if o["채널"] == "영문" and (o["분기"], o["제품"], o["지표"]) == (r["분기"], r["제품"], r["지표"])), None)
            if x:
                영.append("%s %s %s → %s" % (r["분기"], r["제품"], r["지표"], x["표현"]))
        b = 밴드(e, 사전)
        알림("넓은 표현", "%s 「%s」" % (채, e), len(v), "폭 %.0f%%p 이상" % 넓,
           "「%s」 가 %d번 쓰였다(밴드 %s) — 말만으로는 좁힐 수 없다. 같은 분기 영문판이 있으면 그 칸을 근거로 쓰고(%s), 없으면 폭을 시나리오 폭으로 둔다"
           % (e, len(v), _글구간(b), " · ".join(영[:6]) if 영 else "영문판 없음"), "참고")
    최소 = int(신설.get("최소짝", 4))
    for p, _ in 품목:
        for 채 in ("공시", "영문", "구두"):
            v = [z for z in 짝 if z["제품"] == p and z["채널"] == 채 and z.get("판정") in ("겹침", "경계", "밖")]
            if len(v) < 최소:
                continue
            밖 = sum(1 for z in v if z["판정"] == "밖")
            비 = 밖 / len(v)
            if 비 >= float(신설.get("짝밖비율", 0.3)):
                알림("짝 어긋남", "%s %s" % (p, 채), round(비, 3), 신설.get("짝밖비율", 0.3),
                   "%s 의 %s 표현 두 개의 곱이 실현 매출을 %d짝 중 %d짝 비켜 갔다(%s 기준) — 이 품목의 지수 밴드는 말보다 넓게 두고, 그 사실을 근거 칸에 적는다"
                   % (p, 채, len(v), 밖, 주))
    for q in 분기들:
        for p, _ in 품목:
            z = {x["채널"]: x for x in 짝 if (x["분기"], x["제품"]) == (q, p)}
            if "공시" in z:
                for 채 in ("구두", "영문"):
                    if 채 in z and z["공시"].get("판정") and z[채].get("판정") and (z["공시"]["판정"] == "겹침") != (z[채]["판정"] == "겹침"):
                        맞 = "공시" if z["공시"]["판정"] == "겹침" else 채
                        알림("채널 갈림", "%s %s" % (q, p), "공시 %s · %s %s" % (z["공시"]["판정"], 채, z[채]["판정"]), "한쪽만 겹침",
                           "%s %s — 공시 조합(%s · %s)과 %s 조합(%s · %s) 가운데 %s 쪽만 실현 매출과 맞는다(%s 기준). 「공시와 컨콜이 어긋나면 공시를 쓴다」 의 근거로 적되 환율 근사 오차를 함께 적는다"
                           % (q, p, z["공시"]["물량"], z["공시"]["단가"], 채, z[채]["물량"], z[채]["단가"], 맞, 주))
    약 = [rec for rec in 대장 if rec.get("계열") == "약 N% · Around" and rec.get("판정") in ("겹침", "경계", "밖")]
    if len(약) >= 최소:
        밖 = sum(1 for x in 약 if x["판정"] == "밖")
        if 밖 / len(약) >= float(신설.get("약밖비율", 0.3)):
            알림("「약」 계열 밖", "약 N% · Around", round(밖 / len(약), 3), 신설.get("약밖비율", 0.3),
               "「약 N%%」 계열 %d번 중 %d번이 실현 구간 밖 — 사전의 ±%s%%p 는 이 회사에서 좁다. 근거 칸에 적고 밴드를 넓힐지 사람이 정한다"
               % (len(약), 밖, 사전.get("약폭", 1)), "참고")

    결과 = {"형식": "표현실현 1", "만든날": datetime.date.today().isoformat(),
          "설정": {"밴드사전": os.path.relpath(사전경로, 여기) if os.path.exists(사전경로) else None, "사전개정": (사전.get("개정이력") or [{}])[-1].get("날"),
                 "절": 절, "단가통화": 단가통화, "주기준": 주, "주기준_까닭": 주까닭, "결산월": 결산월, "경계폭": 경계폭, "신호문턱": 신설},
          "입력": {"추출": 추출경로, "품목": [{"이름": a, "표": b} for a, b in 품목],
                 "보고서": [{"기간": "%d %s" % k, "접수": v.get("rcept_no"), "보고서": v.get("report_nm")} for k, v in sorted(보고.items()) if (k[0], k[1]) and any(int(q[:4]) == k[0] for q in 필요)],
                 "환율": fx경로 if 일별 else None},
          "원문대조": {"행": len(추출["행"]), "통과": len(행), "버림": 버림, "누락후보": 누락},
          "실현매출": [dict(분기=q, **v) for q, v in sorted(실매출.items())], "실현매출_검산": 검산,
          "대장": 대장, "짝검사": 짝, "채널대조": 대조, "표현별": 표현별, "계열별": 계열별, "가이던스": 가이,
          "기준비교": dict(셈, 주=주, 까닭=주까닭), "신호": 신호}
    return 결과, (1 if (버림 or 사전없음) else 0)


def _목록받기(고유, 시작):
    """list.json(정기공시) — 인증키는 환경변수에서만. 받은 목록(list 의 행들)."""
    key = os.environ.get("OPENDART_API_KEY")
    if not key or not 고유:
        return []
    낸, page = [], 1
    while True:
        u = "https://opendart.fss.or.kr/api/list.json?" + urllib.parse.urlencode(
            {"crtfc_key": key, "corp_code": 고유, "bgn_de": 시작, "end_de": datetime.date.today().strftime("%Y%m%d"),
             "pblntf_ty": "A", "page_no": page, "page_count": 100})
        try:
            j = json.loads(urllib.request.urlopen(u, timeout=60).read().decode("utf-8"))
        except Exception:                                    # noqa: BLE001
            break
        time.sleep(0.6)
        if j.get("status") != "000":
            break
        낸 += j.get("list", [])
        if page >= int(j.get("total_page", 1)):
            break
        page += 1
    return 낸


def 쓰기(결과, 뿌리):
    raw = os.path.join(뿌리, "_raw")
    os.makedirs(raw, exist_ok=True)
    p = os.path.join(raw, "표현실현.json")
    io.open(p, "w", encoding="utf-8").write(json.dumps(결과, ensure_ascii=False, indent=1))
    열 = ["분기", "제품", "지표", "채널", "표현", "방향", "사전밴드", "짝", "매출변동_원", "환율변동", "매출변동_USD",
         "실현구간_원", "판정_원", "실현구간_USD", "판정_USD", "판정", "거리", "사유", "인용", "출처", "범위", "비고"]
    with io.open(os.path.join(raw, "표현실현_대장.csv"), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=열, extrasaction="ignore")
        w.writeheader()
        for rec in sorted(결과["대장"], key=lambda x: (str(x["분기"]), str(x["제품"]), str(x["지표"]), str(x["채널"]))):
            row = dict(rec)
            for k in ("사전밴드", "실현구간_원", "실현구간_USD"):
                if isinstance(row.get(k), list):
                    a, b = row[k]
                    row[k] = "%s ~ %s" % ("−∞" if a is None else "%.1f" % a, "∞" if b is None else "%.1f" % b)
            w.writerow(row)
    return p


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="표현-실현 대장 — 말로 준 변동률과 실현 매출")
    ap.add_argument("가정", nargs="?")
    ap.add_argument("--뿌리", help="회차 폴더(가정 없이 돌릴 때)")
    ap.add_argument("--추출")
    ap.add_argument("--절")
    ap.add_argument("--품목")
    ap.add_argument("--단가통화", choices=["원", "USD", "둘다"], default="둘다")
    ap.add_argument("--받기", action="store_true", help="없는 원문 · 제출이력을 받는다(본체에서는 멈춘다)")
    ap.add_argument("--환율받기", action="store_true")
    ap.add_argument("--시작", help="--받기 로 list.json 을 받을 때 시작일 YYYYMMDD")
    a = ap.parse_args()
    if a.가정:
        if not os.path.exists(a.가정):
            print("가정 파일이 없습니다: %s" % a.가정)
            return 입력오류
        뿌리 = os.path.dirname(os.path.abspath(a.가정))
    elif a.뿌리:
        뿌리 = os.path.abspath(a.뿌리)
    else:
        ap.print_help()
        return 입력오류
    try:
        결과, rc = 실행(뿌리, a.추출, a.절, a.품목, a.단가통화, a.받기, a.환율받기, a.시작)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        print("입력 오류 — %s" % e)
        return 입력오류
    p = 쓰기(결과, 뿌리)
    c = 결과["원문대조"]
    print("행 %d · 원문 대조 통과 %d · 버림 %d · 인용 밖 크기 표현 %d" % (c["행"], c["통과"], len(c["버림"]), len(c["누락후보"])))
    print("실현 매출 %d개 분기 · 짝 %d · 주 기준 %s(%s)" % (len(결과["실현매출"]), len(결과["짝검사"]), 결과["설정"]["주기준"], 결과["설정"]["주기준_까닭"]))
    for 기, v in 결과["기준비교"].items():
        if isinstance(v, dict):
            print("  %s 기준 — 짝 %d · 겹침 %d · 경계 %d · 밖 %d" % (기, v["짝"], v["겹침"], v["경계"], v["밖"]))
    print("신호 %d (경보 %d)" % (len(결과["신호"]), sum(1 for s in 결과["신호"] if s["등급"] == "경보")))
    print("→ %s" % p)
    return rc


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""레터인터랙티브 — 둘째 독자용 선택 판: 레터의 장부 · 민감도 격자 · 결합 민감도로 움직이는 HTML 한 장(2026-10-23 · 연구/레터_인터랙티브판_제안검토_20261023.md 4절).

    python -X utf8 스크립트/레터인터랙티브.py --장부 레터_초안.장부.json [--격자 _raw/민감도격자.json] [--결합 _raw/결합민감도.json]
                                           [--레터 레터_회사.md] [--주가 주가.csv] -o 레터_회사_interactive.html
    python -X utf8 스크립트/레터인터랙티브.py 검사 레터_회사_interactive.html --장부 레터_초안.장부.json [--격자 …] [--결합 …]
    python -X utf8 스크립트/레터인터랙티브.py --가정 가정.json -o 시험.html      # 장부 없이(실험 — 게이트로 대조하지 않은 판이라고 화면에 적는다)

원칙(2026-10-23 결정 ㄱ~ㄹ)
  · **브라우저는 계산하지 않는다.** 모든 숫자는 파이썬이 미리 낸 장부 · 격자 · 결합 민감도 파일의 값이다. 슬라이더 · 히트맵은 격자의 칸을 고를 뿐(칸 사이 보간 없음).
    데이터 객체(`<script type="application/json" id="레터데이터">`)는 그 파일들 그대로이고 해시가 붙는다 — `검사` 가 같은 파일인지 맞춘다(게이트 ⑦ 의 연장).
  · 몬테카를로 대신 결합 민감도 분포 — σ 를 정하지 않고, 확률로 읽지 않는다(「종가가 분포의 어느 자리에 서나」).
  · 「적정가치 · 목표주가 · 저평가 · 고평가 · 매수 · 매도 · 상승 확률 · upside · 경고등」 을 쓰지 않는다. 결과 이름은 「이 가정들에서 계산한 주당가치」.
  · 외부 CDN 스크립트 없음 — Anime.js 는 키트 자산(로컬)을 인라인(글꼴만 레터와 같은 Google Fonts 링크 · 없으면 시스템 글꼴).
  · 회사 · 업종 이름은 이 도구에 없다. 모듈은 재료가 있을 때만 선다(결합 민감도 · 주가 파일이 없으면 그 모듈 · 띠가 빠지고 알림).
  · **서사 없이 짓지 않는다**(2026-10-25 R6 · 레터재구성 계약 0절 6). 데이터 객체 `서사` 는 본편에서
    자른 글이다(`서사읽기` — 결론 다섯 줄 · Narrative 절 · 시나리오 세계 서술 · 관측 근거 · 시나리오별 표 · Reverse DCF 판정 · 모니터링 · 이해관계 ·
    손잡이마다 본편 가정 이름과 Narrative 문장). `--장부` 판은 `서사검사` 가 걸리면(빈 자리 · 장부와 다른 결론 · 화면 글의 내부 번호 · 내부어 ·
    비유어 · 권유어) 파일을 쓰지 않고 종료 1. `--가정` 실험 판은 머리에 「서사 없는 실험 판」 띠를 크게 두고 짓는다(게이트 ⑦-2 는 걸린다).
화면 차례 — 결론(첫 화면) · Narrative · 세 시나리오(단추마다 이름 · 세계 서술 · 관측 근거 · 표의 그 열) · 모델 설계(접힘) · 주요 가정 슬라이더(가정마다
  Narrative 문장) · 매출에서 주당가치까지(구분별 매출 → FCFF → 현재가치 → 영구가치 → 가치 다리 · 순차입금 드릴다운) · WACC × 영구성장률 · 영구기간
  영업이익률 히트맵 + 슬라이더 · 역산 곡선과 판정 문단 · 결합 민감도 쌓기 · 풋볼필드 · 틀릴 길 · 다음 점검 · 이해관계 · 이 판을 읽는 방법.
종료 코드 — 0 통과 · 1 발견(검사 걸림 · 서사가 비어 짓지 않음) · 2 입력 오류.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass
여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류  # noqa: E402
import 용어  # noqa: E402

형식 = "레터인터랙티브 1"
틀파일 = os.path.join(여기, "자산", "레터인터랙티브.틀.html")
애니메 = os.path.join(여기, "자산", "anime-4.5.0.umd.min.js")
금지어 = ("적정가치", "적정 가치", "목표주가", "목표 주가", "저평가", "고평가", "매수", "매도", "상승 확률", "상승확률", "상승 여력", "상승여력",
       "upside", "Upside", "UPSIDE", "Overvalued", "Undervalued", "경고등", "과열")
시나리오들 = ("비관", "기준", "낙관")


def _해시파일(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _읽기(p):
    with io.open(p, encoding="utf-8") as f:
        return json.load(f)


def _n(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def 분위(값, q):
    if not 값:
        return None
    v = sorted(값)
    i = q * (len(v) - 1)
    lo, hi = int(i), min(int(i) + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (i - lo)


def 결합요약(결, 종가, 칸수=30):
    """결합 민감도 파일 → 화면 재료(구간 수 · 판마다의 구간 차례 · 분위 · 종가 자리). 판마다의 값이 없으면(옛 판) 분위만."""
    if not isinstance(결, dict) or not 결.get("분포"):
        return None
    값 = [v for v in (결.get("표본주당") or []) if _n(v) is not None]
    분 = 결["분포"]
    낸 = {"판": 결.get("판"), "성공": 결.get("성공"), "실패": 결.get("실패"), "기준주당": 결.get("기준주당"),
         "분포": {k: 분.get(k) for k in ("P5", "P25", "P50", "P75", "P95", "최소", "최대", "기준위치")},
         "손잡이": [{"이름": h.get("이름"), "하": h.get("하"), "상": h.get("상"), "근거": h.get("근거") or h.get("출처")} for h in 결.get("손잡이") or []],
         "구간": None, "차례": None, "종가자리": None, "포함": _결합포함(결)}
    if 값:
        lo, hi = min(값), max(값)
        폭 = (hi - lo) / 칸수 if hi > lo else 1.0
        차례 = [min(칸수 - 1, int((v - lo) / 폭)) if hi > lo else 0 for v in 값]
        낸["구간"] = {"시작": lo, "폭": 폭, "수": 칸수, "개수": [차례.count(i) for i in range(칸수)]}
        낸["차례"] = 차례
        if _n(종가) is not None:
            낸["종가자리"] = sum(1 for v in 값 if v <= 종가) / len(값)
    return 낸


def _날짜(t):
    """YYYYMMDD · YYYY-MM-DD · YYYY.MM.DD → date. 못 읽으면 None."""
    t = ("%s" % t).strip()
    m = re.match(r"^(\d{4})(\d{2})(\d{2})$", t) or re.match(r"^(\d{4})[-./](\d{1,2})[-./](\d{1,2})", t)
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None
    except ValueError:
        return None


def 주가띠(csv경로, 기준일):
    """주가 파일 → 평가기준일까지 52주(364일)의 최저 · 최고 · 개수. 못 읽으면 None.
    레터와 같은 파일 꼴(`레터궤적.읽기` — 「#」 머리 주석 · date · close · YYYYMMDD)을 먼저 읽고, 못 읽으면 한글 머리(날짜 · 종가)로 읽는다
    (2026-10-23 — 레터의 주가 파일을 이 판만 못 읽어 주가 띠가 빠졌다)."""
    try:
        기 = datetime.date.fromisoformat(기준일)
        시작 = 기 - datetime.timedelta(days=364)
        줄 = []
        try:
            import 레터궤적                                         # noqa: PLC0415
            줄 = [(_날짜(d), v) for d, v in ((레터궤적.읽기(csv경로) or {}).get("줄") or [])]
        except Exception:                                        # noqa: BLE001
            줄 = []
        if not 줄:
            with io.open(csv경로, encoding="utf-8-sig") as f:
                행들 = [x for x in f if x.strip() and not x.lstrip().startswith("#")]
            for r in csv.DictReader(행들):
                v = r.get("종가") or r.get("close") or r.get("Close")
                if v in (None, ""):
                    continue
                줄.append((_날짜(r.get("날짜") or r.get("date") or r.get("Date") or ""), float(("%s" % v).replace(",", ""))))
        값 = [v for d, v in 줄 if d and 시작 <= d <= 기]
        return [min(값), max(값), len(값)] if 값 else None
    except Exception:                                # noqa: BLE001
        return None


def 풋볼(헤드, 격, 결요, 주띠):
    """방법마다의 주당가치 띠 — 있는 재료만(값을 정하지 않는다 · 띠마다 출처)."""
    띠 = []
    v = [헤드[s] for s in 시나리오들 if _n(헤드.get(s)) is not None]
    if len(v) >= 2:
        띠.append({"이름": "세 시나리오", "낮음": min(v), "높음": max(v), "가운데": 헤드.get("기준"), "출처": "평가 모델의 비관 · 기준 · 낙관 시나리오"})
    손값 = []
    for h in (격.get("손잡이") or {}).values():
        범 = h.get("근거범위")
        for x, r in zip(h.get("눈금") or [], h.get("결과") or []):
            if "막힘" in r or not 범:
                continue
            if 범[0] - 1e-12 <= x <= 범[1] + 1e-12:
                손값.append(r["주"])
    if len(손값) >= 2:
        띠.append({"이름": "주요 가정 하나씩(근거 범위 안)", "낮음": min(손값), "높음": max(손값), "가운데": 격["기준"]["주"],
                  "출처": "동인 표의 가정을 하나씩 근거 범위 안에서 옮긴 값(다른 가정은 기준)"})
    표 = [x for 줄 in ((격.get("표1") or {}).get("값") or []) for x in 줄 if _n(x) is not None]
    if 표:
        띠.append({"이름": "WACC × 영구성장률 표", "낮음": min(표), "높음": max(표), "가운데": 격["기준"]["주"],
                  "출처": "WACC · 영구성장률을 기준에서 위아래로 함께 옮긴 표의 가장 낮은 칸 · 높은 칸"})
    if 결요 and 결요["분포"].get("P5") is not None:
        띠.append({"이름": "결합 민감도(분포의 가운데 구십 퍼센트)", "낮음": 결요["분포"]["P5"], "높음": 결요["분포"]["P95"], "가운데": 결요["분포"]["P50"],
                  "출처": "근거 범위 안에서 가정 여럿을 함께 옮긴 조합들의 분포(확률이 아닙니다)"})
    if 주띠:
        띠.append({"이름": "평가기준일까지 오십이 주 주가", "낮음": 주띠[0], "높음": 주띠[1], "가운데": None, "출처": "주가 파일(평가기준일까지 1년)"})
    return 띠


# ────────────────────────────────────────────────── 모델 설계(본편 추정 구조 ~ 가치 브리지 — 2026-10-23 · 05_최적설계 W5)
# 인터랙티브 판이 본편 없이 혼자 놓이면 「모델 설계가 레터의 몸통」(2026-10-16 결정)이 통째로 빠진다.
# 그래서 게이트를 지난 본편에서 추정 구조부터 가치 브리지까지의 절을 그대로 잘라 데이터 객체에 싣는다(글은 본편 그대로 — 이 판이 쓰지 않는다).
# 절은 번호가 아니라 제목 앞쪽(「 : 」 앞)으로 고른다 — 인건비 절이 없는 회사는 번호가 하나씩 당겨진다.
설계절머리 = {"구조": "추정 구조", "매출": "매출 추정", "비용": "영업비용 추정", "인건비": "인건비 추정", "재투자": "설비투자와 감가상각",
          "운전자본": "운전자본 추정", "세금": "법인세와 FCFF", "할인율": "할인율", "영구": "Terminal Value", "주주가치": "가치 브리지"}
_절머리꼴 = re.compile(r"^## (\d+)\. (.+?)\s*$")
_그림표식 = re.compile(r"^<!--\s*그림:")
_그림캡션 = re.compile(r"^\*\*그림 ?\d*\.")


def _설계키(제목):
    앞 = 제목.split(" : ", 1)[0].strip()
    return next((k for k, v in 설계절머리.items() if 앞 == v), None)


def _표읽기(줄들):
    """마크다운 표 줄들 → {"머리", "정렬", "줄"}. 둘째 줄이 구분 줄이 아니면 머리 없이 전부 줄."""
    칸 = [[c.strip() for c in x.strip().strip("|").split("|")] for x in 줄들]
    if len(칸) >= 2 and all(re.match(r"^:?-{2,}:?$", c or "--") for c in 칸[1]):
        정렬 = ["r" if c.endswith(":") and not c.startswith(":") else "c" if c.startswith(":") and c.endswith(":") else "l" for c in 칸[1]]
        return {"꼴": "표", "머리": 칸[0], "정렬": 정렬, "줄": 칸[2:]}
    return {"꼴": "표", "머리": [], "정렬": [], "줄": 칸}


def 블록들(줄들):
    """절 본문 줄 → 블록 목록. 글 · 표 · 목록 · 인용 · 그림(캡션만 — 그림은 본편) · 소제목(###). HTML 주석은 건너뛴다."""
    낸, 글, i = [], [], 0

    def 글닫기():
        if 글:
            낸.append({"꼴": "글", "글": " ".join(글).strip()})
            글.clear()
    while i < len(줄들):
        s = 줄들[i].strip()
        if not s:
            글닫기()
            i += 1
            continue
        if _그림표식.match(s):
            글닫기()
            i += 1
            continue
        if s.startswith("<!--"):
            글닫기()
            while i < len(줄들) and "-->" not in 줄들[i]:
                i += 1
            i += 1
            continue
        if s.startswith("### "):
            글닫기()
            낸.append({"꼴": "소제목", "글": s[4:].strip()})
            i += 1
            continue
        if _그림캡션.match(s):
            글닫기()
            낸.append({"꼴": "그림", "글": re.sub(r"\*\*", "", s)})
            i += 1
            continue
        if s.startswith("|"):
            글닫기()
            j = i
            while j < len(줄들) and 줄들[j].strip().startswith("|"):
                j += 1
            낸.append(_표읽기(줄들[i:j]))
            i = j
            continue
        if re.match(r"^(?:[-*]|\d+\.)\s+", s):
            글닫기()
            항 = []
            while i < len(줄들) and 줄들[i].strip():
                t = 줄들[i].strip()
                m = re.match(r"^(?:[-*]|\d+\.)\s+(.*)$", t)
                if m:
                    항.append(m.group(1))
                elif 항:
                    항[-1] += " " + t
                i += 1
            낸.append({"꼴": "목록", "항목": 항})
            continue
        if s.startswith(">"):
            글닫기()
            인 = []
            while i < len(줄들) and 줄들[i].strip().startswith(">"):
                인.append(줄들[i].strip().lstrip(">").strip())
                i += 1
            낸.append({"꼴": "인용", "글": " ".join(인)})
            continue
        글.append(s)
        i += 1
    글닫기()
    return 낸


def _요약(글):
    """절 머리의 한 줄 — 첫 문단의 첫 문장(그 문장이 짧으면 둘째 문장까지). 글은 본편 그대로(고치지 않고 자른다)."""
    문 = [s for s in re.split(r"(?<=[.!?])\s+", (글 or "").strip()) if s]
    if not 문:
        return ""
    return 문[0] if len(문[0]) >= 30 or len(문) == 1 else 문[0] + " " + 문[1]


def 설계읽기(레터경로):
    """게이트를 지난 본편 md → {"파일", "html", "해시", "절": [{"번호", "키", "제목", "요약", "블록"}]}. 설계 절이 없으면 None."""
    if not 레터경로 or not os.path.exists(레터경로):
        return None
    원문 = open(레터경로, "rb").read()
    글 = 원문.decode("utf-8").replace("\r\n", "\n")
    i = 글.find("\n# 부록")
    줄 = (글 if i < 0 else 글[:i]).split("\n")
    머리 = [(k, _절머리꼴.match(x)) for k, x in enumerate(줄) if x.startswith("## ")]
    절 = []
    for n, (k, m) in enumerate(머리):
        키 = _설계키(m.group(2)) if m else None
        if not 키:
            continue
        끝 = 머리[n + 1][0] if n + 1 < len(머리) else len(줄)
        bl = 블록들(줄[k + 1:끝])
        요약 = _요약(next((b["글"] for b in bl if b["꼴"] == "글"), ""))
        절.append({"번호": int(m.group(1)), "키": 키, "제목": m.group(2), "요약": 요약, "블록": bl})
    if not 절:
        return None
    이름 = os.path.basename(레터경로)
    return {"파일": 이름, "html": os.path.splitext(이름)[0] + ".html", "해시": hashlib.sha256(원문).hexdigest(), "절": 절}


def _설계글(설):
    """설계 데이터의 글 전부(금지어 검사용)."""
    낸 = []
    for 절 in (설 or {}).get("절") or []:
        낸.append(절.get("제목") or "")
        for b in 절.get("블록") or []:
            if b["꼴"] == "표":
                낸 += [" ".join(r) for r in [b.get("머리") or []] + (b.get("줄") or [])]
            elif b["꼴"] == "목록":
                낸 += b.get("항목") or []
            else:
                낸.append(b.get("글") or "")
    return "\n".join(낸)


# ────────────────────────────────────────────────── 서사(2026-10-25 · 레터재구성 R6 · 계약 0절 6)
# 판의 글은 본편에서 자른다(브라우저는 계산하지 않는다 · 이 판은 글을 쓰지 않는다). 절은 번호가 아니라 제목 앞쪽(「 : 」 앞)으로 고른다.
#   결론     1절의 결론 다섯 줄 — `레터이야기.결론머리` 로 줄을 찾는다(게이트 ⑯ 과 같은 찾기 · 본편 1절 · 3분 레터와 같은 글)
#   이야기   Narrative 절 전부 — 정체성 · 우위 · 그러나 · 값의 원천 · 「→ 이 판단은」 줄 · 위험 표 · Narrative 표
#   시나리오 시나리오 절의 「**○○ 시나리오 「이름」** — 세계 서술」 문단과 뒤따르는 문단(관측 근거 · 크게 움직인 가정 · 값) · 시나리오 열이 있는 표
#   역산     Reverse DCF 절의 첫 문단(판정) · 「평가기준일 분석」 소절
#   끝       모니터링 절의 첫 문단 · 평가자의 이해관계 절의 소절 앞 문단
#   손잡이   격자 손잡이마다 본편 가정 이름(부록 「가정 일람」 의 번호 → 이름) · 그 가정이 온 Narrative 문장(부록 「Narrative와 입력값 전체」 ·
#            없으면 그 가정이 든 항목 절의 「이 절이 담은 Narrative」 줄) · 근거 글(격자의 글에 내부 번호 · 내부어 · 비유어가 없을 때만)
서사형식 = "레터서사 1"
서사절머리 = {"결론": "결론", "Narrative": "Narrative", "시나리오": "시나리오 분석", "역산": "Reverse DCF", "신호": "모니터링",
          "자리": "평가자의 이해관계와 평가의 한계"}
부록제목 = {"가정": "가정 일람", "입력값": "Narrative와 입력값 전체"}
_부록절꼴 = re.compile(r"^## 부록 ([A-Z])\. (.+?)\s*$")
_시머리꼴 = re.compile(r"^\*\*(비관|기준|낙관) 시나리오(?: 「(.+?)」)?\*\*(?:\s*—\s*(.*))?$")
관측머리 = ("이 세계로 가고 있다는 신호는", "3P 기준으로는", "이 길은 ")         # `레터이야기.시나리오3P` 가 세계 서술 뒤에 붙이는 문장의 머리
# 본편은 첫 「3P 기준」 에 용어 병기(「3P 기준(산술적 가능성 · …)으로는」 — 2026-10-27 옛 「3P test」)를 붙이므로 「기준」 뒤 괄호를 건너뛴다 · 문장 머리에서만 찾는다
_관측꼴 = [re.compile(r"(?:^|(?<=\. ))" + re.escape(m).replace("기준", r"기준(?:\([^)]*\))?")) for m in 관측머리]
부록A절키 = {"매출": "매출", "원가": "비용", "인건비": "인건비", "설비투자와 상각": "재투자", "운전자본과 미지급 항목": "운전자본", "운전자본": "운전자본",
          "법인세": "세금", "Terminal Value와 주주가치": "영구"}              # `레터._부록A절` 의 소제목 → 설계 절 키
엔진손잡이절 = {"매출성장": "매출", "목표마진": "비용", "영구ROIC": "영구", "영구이익률가감": "영구", "영구성장률": "영구", "비영업할인": "주주가치"}
_번호꼴 = re.compile(r"(?<![A-Za-z0-9])A-\d+")
_기호괄호끝 = re.compile(r"\s*\((?:[A-Za-z][A-Za-z/ .-]*|βu|βL)\)\s*$")
_절줄꼴 = re.compile(r"^(?:이 절이 담은 Narrative는 .*?「(.+?)」 줄이다|가정에 반영한 Narrative는 「(.+?)」입니다)")     # v27 — 본편 항목 절의 합쇼체 문장(옛 꼴도 읽는다)


def _앞말(제목):
    return ("%s" % 제목).split(" : ", 1)[0].strip()


def 절들(글):
    """본편 md → [{"번호", "제목", "부록", "줄"}] — 「## N. 제목」(본편) · 「# 부록」 아래 「## 부록 X. 제목」. 다른 「#」 · 「##」 줄은 절을 닫는다."""
    줄들 = 글.replace("\r\n", "\n").split("\n")
    머리, 부록 = [], False
    for k, x in enumerate(줄들):
        if x.startswith("# "):
            if x[2:].strip() == "부록":
                부록 = True
            머리.append((k, None, 부록))
        elif x.startswith("## "):
            머리.append((k, (_부록절꼴 if 부록 else _절머리꼴).match(x), 부록))
    낸 = []
    for n, (k, m, 부) in enumerate(머리):
        if not m:
            continue
        끝 = 머리[n + 1][0] if n + 1 < len(머리) else len(줄들)
        낸.append({"번호": ("부록 " + m.group(1)) if 부 else int(m.group(1)), "제목": m.group(2), "부록": 부, "줄": 줄들[k + 1:끝]})
    return 낸


def _머(b):
    return [("%s" % c).strip() for c in (b.get("머리") or [])]


def _시열(머):
    """표 머리 → {"공통", "기준", "비관", "낙관": [열 번호]} — 시나리오 이름이 든 열(「비관 − 기준」 은 비관 열 · 「기준 대비」 는 기준 열)."""
    열 = {"공통": [], "기준": [], "비관": [], "낙관": []}
    for i, c in enumerate(머):
        열["비관" if "비관" in c else "낙관" if "낙관" in c else "기준" if c.startswith("기준") else "공통"].append(i)
    return 열


def _결론자르기(블):
    """1절 블록 → [{"자리", "글"}] — 결론 다섯 줄(`레터이야기.결론자리` 차례 · 머리말을 담은 첫 문단 · 게이트 ⑯ 과 같은 찾기)."""
    import 레터이야기 as N                                   # noqa: PLC0415
    글들 = [b["글"] for b in 블 if b["꼴"] == "글"]
    낸 = []
    for 자리 in N.결론자리:
        머 = N.결론머리[자리]
        머 = (머,) if isinstance(머, str) else 머
        g = next((s for s in 글들 if any(m in s for m in 머)), None)
        if g:
            낸.append({"자리": 자리, "글": g})
    return 낸


def _관측자리(몸):
    """세계 서술 문단에서 관측 근거(이 세계로 가고 있다는 신호 · 3P test)가 시작하는 자리 — 없으면 끝."""
    자리 = [len(몸)]
    for 꼴 in _관측꼴:
        m = 꼴.search(몸)
        if m:
            자리.append(m.start())
    return min(자리)


def _시나리오자르기(블):
    """시나리오 절 블록 → {"머리": [글], "세계": {시: {"이름", "세계", "관측", "글": []}}, "표": [{"소제목", "설명", "표", "열", "전파"}]}."""
    머리, 세계, 표 = [], {}, []
    시, 닫힘, 앞글, 앞소 = None, False, None, None
    for b in 블:
        꼴 = b["꼴"]
        if 꼴 == "글":
            m = None if 닫힘 else _시머리꼴.match(b["글"])
            if m:
                시 = m.group(1)
                몸 = (m.group(3) or "").strip()
                k = _관측자리(몸)
                세계[시] = {"이름": m.group(2), "세계": 몸[:k].strip(), "관측": 몸[k:].strip(), "글": []}
            elif 시:
                세계[시]["글"].append(b["글"])
            elif not 세계 and not 닫힘:
                머리.append(b["글"])
            앞글 = b["글"]
        elif 꼴 == "소제목":
            닫힘, 시, 앞소, 앞글 = True, None, b["글"], None
        elif 꼴 == "표":
            열 = _시열(_머(b))
            if 열["비관"] or 열["낙관"]:
                표.append({"소제목": 앞소, "설명": 앞글, "표": b, "열": 열, "전파": ("변동 원인" in _머(b) or "무엇이 밀었나" in _머(b))})
            시, 앞글 = None, None
    return {"머리": 머리, "세계": 세계, "표": 표}


def _역산자르기(블):
    """Reverse DCF 절 블록 → {"판정": [첫 문단], "분석": [「평가기준일 분석」 소절의 블록]}."""
    판정 = []
    for b in 블:
        if b["꼴"] == "소제목":
            break
        if b["꼴"] == "글":
            판정 = [b["글"]]
            break
    분석, 안 = [], False
    for b in 블:
        if b["꼴"] == "소제목":
            안 = b["글"].strip().startswith("평가기준일 분석")
            continue
        if 안:
            분석.append(b)
    return {"판정": 판정, "분석": 분석}


def _앞문단(블, 하나=False):
    낸 = []
    for b in 블:
        if b["꼴"] == "소제목":
            break
        if b["꼴"] == "글":
            낸.append(b["글"])
            if 하나:
                break
    return 낸


def _가정이름표(블):
    """부록 「가정 일람」 블록 → {번호: {"이름", "절"}} — 첫 칸이 「A-030」 꼴인 줄(앞 0 을 걷는다) · 절은 그 표 위 소제목(`레터._부록A절`)."""
    낸, 소 = {}, None
    for b in 블:
        if b["꼴"] == "소제목":
            소 = b["글"].strip()
            continue
        if b["꼴"] != "표":
            continue
        for r in b.get("줄") or []:
            m = re.match(r"^A-0*(\d+)$", (r[0] if r else "").strip())
            if m and len(r) > 1 and r[1].strip():
                낸.setdefault(m.group(1), {"이름": r[1].strip(), "절": 부록A절키.get(소)})
    return 낸


def _입력값줄(묶음):
    """[(곳, 블록들)] → [{"Narrative", "입력값", "곳"}] — 머리가 「Narrative | 입력값 | …」 인 표의 줄(같은 줄은 한 번)."""
    낸, 본 = [], set()
    for 곳, 블 in 묶음:
        for b in 블:
            머 = _머(b) if b["꼴"] == "표" else []
            if len(머) < 2 or 머[0] != "Narrative" or 머[1] != "입력값":
                continue
            for r in b.get("줄") or []:
                if len(r) < 2 or not r[0].strip() or not r[1].strip():
                    continue
                키 = (r[0].strip(), r[1].strip())
                if 키 not in 본:
                    본.add(키)
                    낸.append({"Narrative": 키[0], "입력값": 키[1], "곳": 곳})
    return 낸


def _이름꼴(s):
    s = re.sub(r"\s+", " ", ("%s" % s).strip())
    while True:
        t = _기호괄호끝.sub("", s).strip()
        if t == s:
            return s
        s = t


def _이름펴기(이름, 구분들):
    """가정 이름 → 견줄 이름 모음. 「NAND · 범용 DRAM 정상 수준 …」 처럼 매출 구분 이름만 다른 가정을 묶은 이름(`레터이야기.이름묶기`)은
    구분마다의 이름으로 풀고, 「, 」 로 이은 이름은 나눈다. 끝의 기호 괄호(「(RONIC)」 · 「(g)」)는 걷고 견준다."""
    낸 = set()
    for 조각 in [이름] + ("%s" % 이름).split(", "):
        조각 = (조각 or "").strip()
        if not 조각:
            continue
        낸.add(_이름꼴(조각))
        앞, 남 = [], 조각
        while True:
            g = next((g for g in 구분들 if 남.startswith(g + " ")), None)
            if not g:
                break
            앞.append(g)
            남 = 남[len(g):]
            if 남.startswith(" · "):
                남 = 남[3:]
                continue
            남 = 남[1:]
            break
        if 앞 and 남:
            낸 |= {_이름꼴("%s %s" % (g, 남)) for g in 앞}
    return 낸


def _문체걸림(글):
    """화면 글 하나 → 걸린 말(내부 번호 「A-182」 · 번호식 이름 · 내부어 · 비유어). 목록은 레터 원고 검수와 같다(`레터.번호식이름` · `내부어` · `비유어`)."""
    import 레터 as L                                         # noqa: PLC0415
    글 = "%s" % (글 or "")
    낸 = []
    m = _번호꼴.search(글)
    if m:
        낸.append("내부 번호 「%s」" % m.group(0))
    for 패, 이름 in L.번호식이름:
        m = re.search(패, 글)
        if m:
            낸.append("%s 「%s」" % (이름, m.group(0)))
    for 말 in L.내부어:
        m = re.search(말, 글)
        if m:
            낸.append("내부어 「%s」" % m.group(0))
    for 말 in L.비유어:
        if 말 in 글:
            낸.append("비유어 「%s」" % 말)
    for 패, 이름 in L.옛말:
        if re.search(패, 글):
            낸.append("옛말 「%s」" % 이름)
    return 낸


def _근거글(h):
    """격자 손잡이의 근거 출처 글 — 화면에 낼 수 있을 때만(내부 번호 · 내부어 · 비유어 · 파일 이름 · 코드 표지가 없을 때). 아니면 None(화면은 근거 범위만 적는다)."""
    g = ("%s" % (h.get("근거출처") or "")).strip()
    if not g or not h.get("근거범위") or _문체걸림(g) or re.search(r"`|\.py\b|\.json\b|_raw", g) or any(w in 용어.권유어밖(g) for w in 금지어):
        return None
    return g


def _손잡이서사(격, 가정표, 입력, 절줄, 시가정, 지렛대들):
    """격자 손잡이 → {키: {"이름", "서사": [{"글", "입력값", "곳"}], "근거", "대상말", "지렛대", "시나리오"}}."""
    구분들 = sorted({("%s" % g).strip() for g in (격.get("잎") or []) if ("%s" % g).strip()}, key=len, reverse=True)
    낸 = {}
    for k, h in (격.get("손잡이") or {}).items():
        대상 = ["%s" % t for t in h.get("대상") or []]
        번 = [t.replace("A-", "") for t in 대상 if t.replace("A-", "").isdigit()]
        개별 = [가정표[b]["이름"] for b in 번 if b in 가정표]
        wacc = bool(대상) and all(t.startswith("WACC") for t in 대상)
        if wacc:
            개별 = ["WACC"]
        이름 = ("%s" % (h.get("이름") or "")).strip()
        if not 이름 or _번호꼴.search(이름):
            이름 = " · ".join(dict.fromkeys(개별)) or _번호꼴.sub("", 이름).strip(" ·")
        견줄 = set()
        for n in 개별 + [이름]:
            견줄 |= _이름펴기(n, 구분들)
        서 = [{"글": r["Narrative"], "입력값": r["입력값"], "곳": r["곳"]} for r in 입력 if _이름펴기(r["입력값"], 구분들) & 견줄]
        if not 서:
            절키 = "할인율" if wacc else next((가정표[b]["절"] for b in 번 if b in 가정표 and 가정표[b].get("절")), None) \
                or (엔진손잡이절.get(대상[0]) if 대상 else None)
            if 절키 and 절줄.get(절키):
                서 = [dict(절줄[절키])]
            elif 절키:                                         # 1.1.15 — 추정 블록(레터 v27 6단계)에는 「가정에 반영한 Narrative는」 줄이 없다 —
                절말 = set()                                   # 그 절의 가정으로 간 Narrative 문장(부록 「Narrative와 입력값 전체」 · Narrative 절 표)
                for v in 가정표.values():
                    if v.get("절") == 절키:
                        절말 |= _이름펴기(v.get("이름") or "", 구분들)
                서 = [{"글": r["Narrative"], "입력값": r["입력값"], "곳": r["곳"]} for r in 입력 if _이름펴기(r["입력값"], 구분들) & 절말][:2]
        말 = {}
        for t in 대상:
            v = ("%s" % ((h.get("대상이름") or {}).get(t) or "")).strip()
            b = t.replace("A-", "")
            말[t] = v if (v and not _번호꼴.search(v)) else ((가정표.get(b) or {}).get("이름") or "")
        낸[k] = {"이름": 이름, "서사": 서, "근거": _근거글(h), "대상말": 말, "지렛대": k in 지렛대들,
                "시나리오": h.get("꼴") in ("시나리오축", "시나리오보간") or bool(견줄 & 시가정)}
    return 낸


def _지렛대손잡이(격, 장부):
    """장부 「지렛대」(값을 가르는 가정 — `레터이야기.지렛대`)를 덮는 격자 손잡이 키들. 장부가 없으면 격자의 「지렛대」 손잡이."""
    지 = (장부 or {}).get("지렛대") or {}
    번 = {"%s" % b for b in 지.get("번호들") or 지.get("대상") or []}
    W = any(b.startswith("WACC") for b in 번)
    번 = {b for b in 번 if b.isdigit()}
    낸 = []
    for k, h in (격.get("손잡이") or {}).items():
        hd = {"%s" % x for x in h.get("대상") or []}
        if k == "지렛대" or (번 and 번 <= hd) or (W and any(x.startswith("WACC") for x in hd)):
            낸.append(k)
    return 낸


def _결합지렛대(결, 장부):
    """결합 민감도 손잡이에 값을 가르는 가정이 들었나 → {"이름", "포함": True · "일부" · False} · 재료가 없으면 None."""
    지 = (장부 or {}).get("지렛대") or {}
    if not 지 or not isinstance(결, dict) or not 결.get("손잡이"):
        return None
    목 = {"%s" % b for b in 지.get("번호들") or 지.get("대상") or []}
    목 = {("WACC" if b.startswith("WACC") else b) for b in 목 if b.isdigit() or b.startswith("WACC")}
    덮 = set()
    for h in 결["손잡이"]:
        hd = {"%s" % x for x in ((h.get("대상") or []) if isinstance(h, dict) else [])}
        덮 |= 목 & hd
        if "WACC" in 목 and any(x.startswith("WACC") for x in hd):
            덮.add("WACC")
    if not 목:
        이름들 = set(지.get("이름들") or [지.get("이름")])
        포함 = any(isinstance(h, dict) and h.get("이름") in 이름들 for h in 결["손잡이"])
    else:
        포함 = True if 덮 >= 목 else ("일부" if 덮 else False)
    return {"이름": 지.get("이름"), "포함": 포함}


def 서사읽기(레터경로, 격=None, 장부=None, 결=None):
    """게이트를 지난 본편 md → 서사 데이터(글은 본편 그대로 — 이 판은 자르기만 한다). 본편이 없으면 None. 빈 자리는 `서사검사` 가 센다."""
    if not 레터경로 or not os.path.exists(레터경로):
        return None
    원문 = open(레터경로, "rb").read()
    목 = 절들(원문.decode("utf-8"))
    본, 부 = {}, {}
    for x in 목:
        표 = 부 if x["부록"] else 본
        for k, v in (부록제목 if x["부록"] else 서사절머리).items():
            if k not in 표 and ((x["제목"].strip() == v) if x["부록"] else (_앞말(x["제목"]) == v)):
                표[k] = x
    블 = {k: 블록들(x["줄"]) for k, x in 본.items()}

    def 머(k):
        return {"번호": 본[k]["번호"], "제목": 본[k]["제목"]}
    이름 = os.path.basename(레터경로)
    낸 = {"형식": 서사형식, "파일": 이름, "html": os.path.splitext(이름)[0] + ".html", "해시": hashlib.sha256(원문).hexdigest()}
    낸["결론"] = dict(머("결론"), 줄=_결론자르기(블["결론"])) if "결론" in 본 else None
    낸["이야기"] = dict(머("Narrative"), 블록=블["Narrative"]) if "Narrative" in 본 else None
    낸["시나리오"] = dict(머("시나리오"), **_시나리오자르기(블["시나리오"])) if "시나리오" in 본 else None
    낸["역산"] = dict(머("역산"), **_역산자르기(블["역산"])) if "역산" in 본 else None
    낸["끝"] = {k: dict(머(k), 글=_앞문단(블[k], 하나=(k == "신호"))) for k in ("신호", "자리") if k in 본}
    가정표 = _가정이름표(블록들(부["가정"]["줄"])) if "가정" in 부 else {}
    묶음 = ([(부["입력값"]["번호"], 블록들(부["입력값"]["줄"]))] if "입력값" in 부 else []) + \
        ([("%d절" % 본["Narrative"]["번호"], 블["Narrative"])] if "Narrative" in 본 else [])
    입력 = _입력값줄(묶음)
    절줄 = {}
    for x in 목:
        키 = None if x["부록"] else _설계키(x["제목"])
        if 키 and 키 not in 절줄:
            g = next((b["글"] for b in 블록들(x["줄"]) if b["꼴"] == "글" and _절줄꼴.match(b["글"])), None)
            if g:
                절줄[키] = {"글": next(x for x in _절줄꼴.match(g).groups() if x), "입력값": None, "곳": "%d절" % x["번호"]}
    구분들 = sorted({("%s" % g).strip() for g in ((격 or {}).get("잎") or []) if ("%s" % g).strip()}, key=len, reverse=True)
    시가정 = set()
    for t in ((낸["시나리오"] or {}).get("표") or []):
        if _머(t["표"])[:1] == ["가정"]:
            for r in t["표"].get("줄") or []:
                if r and r[0].strip():
                    시가정 |= _이름펴기(r[0], 구분들)
    지들 = _지렛대손잡이(격 or {}, 장부)
    낸["손잡이"] = _손잡이서사(격 or {}, 가정표, 입력, 절줄, 시가정, 지들)
    for 손키, x in 낸["손잡이"].items():                       # 2026-10-26 합본 — 손잡이 카드가 설 본편 절(대상 가정의 절)
        x["절"] = 손잡이절((((격 or {}).get("손잡이") or {}).get(손키) or {}).get("대상") or [])
    지 = (장부 or {}).get("지렛대") or {}
    낸["지렛대"] = {"이름": 지.get("이름") or next((낸["손잡이"][k]["이름"] for k in 지들), None), "손잡이": 지들} if (지 or 지들) else None
    낸["결합지렛대"] = _결합지렛대(결, 장부)
    return 낸


def _블록말들(블):
    낸 = []
    for b in 블 or []:
        if b.get("꼴") == "표":
            낸 += [c for r in [b.get("머리") or []] + (b.get("줄") or []) for c in r]
        elif b.get("꼴") == "목록":
            낸 += b.get("항목") or []
        else:
            낸.append(b.get("글") or "")
    return 낸


def 서사글들(서):
    """서사 데이터에서 화면에 나가는 글 → [(곳, 글)]."""
    if not isinstance(서, dict):
        return []
    낸 = [("결론", z.get("글")) for z in ((서.get("결론") or {}).get("줄") or [])]
    이 = 서.get("이야기") or {}
    낸 += [("Narrative", g) for g in [이.get("제목")] + _블록말들(이.get("블록"))]
    시 = 서.get("시나리오") or {}
    낸 += [("시나리오", g) for g in 시.get("머리") or []]
    for s, w in (시.get("세계") or {}).items():
        낸 += [("%s 시나리오" % s, g) for g in [w.get("이름"), w.get("세계"), w.get("관측")] + (w.get("글") or [])]
    for t in 시.get("표") or []:
        낸 += [("시나리오 표", g) for g in [t.get("설명"), t.get("소제목")] + _블록말들([t.get("표") or {}])]
    역 = 서.get("역산") or {}
    낸 += [("Reverse DCF", g) for g in (역.get("판정") or []) + _블록말들(역.get("분석"))]
    for k, x in (서.get("끝") or {}).items():
        낸 += [(k, g) for g in [x.get("제목")] + (x.get("글") or [])]
    for k, x in (서.get("손잡이") or {}).items():
        곳 = "손잡이 %s" % (x.get("이름") or k)
        낸 += [(곳, g) for g in [x.get("이름"), x.get("근거")] + list((x.get("대상말") or {}).values())]
        낸 += [(곳, g) for z in x.get("서사") or [] for g in (z.get("글"), z.get("입력값"))]
    return [(곳, g) for 곳, g in 낸 if g]


def _수들(글):
    return re.findall(r"\d[\d,.]*", "%s" % (글 or ""))


def 서사검사(데, 장부=None):
    """서사가 실렸나 → 걸림 목록(빈 자리 · 장부와 다른 결론 · 화면 글의 내부 번호 · 내부어 · 비유어 · 금지어). 짓기 전과 게이트 ⑦-2 가 같은 함수를 쓴다."""
    서 = 데.get("서사")
    if not isinstance(서, dict) or 서.get("형식") != 서사형식:
        return ["서사가 없다 — 게이트를 지난 본편(--레터 레터_회사.md)으로 판을 다시 낸다(결론 · Narrative · 시나리오 서술 · Reverse DCF 판정이 빠진다)"]
    걸 = []
    G = 데.get("격자") or {}
    종가 = _n(G.get("종가")) is not None
    줄 = {z["자리"]: z["글"] for z in ((서.get("결론") or {}).get("줄") or [])}
    if not 서.get("결론"):
        걸.append("본편에 결론 절이 없다")
    for 자리 in ("값", "갈림") + (("가격",) if 종가 else ()):
        if 자리 not in 줄:
            걸.append("결론의 「%s」 줄이 본편 1절에 없다(결론 다섯 줄 — `레터이야기.결론줄들`)" % 자리)
    for z in ((장부 or {}).get("결론") or {}).get("줄") or []:
        자리 = z.get("자리")
        if 자리 not in 줄:
            if 자리 not in ("값", "갈림", "가격"):
                걸.append("장부의 결론 「%s」 줄을 본편 1절에서 찾지 못했다" % 자리)
        elif _수들(z.get("글")) != _수들(줄[자리]):
            걸.append("결론 「%s」 줄의 숫자가 장부와 다르다" % 자리)
    if not any(b.get("꼴") == "글" for b in ((서.get("이야기") or {}).get("블록") or [])):
        걸.append("본편에 Narrative 절(정체성 · 우위 · 그러나 · 값의 원천)이 없다")
    시 = 서.get("시나리오") or {}
    for s in 시나리오들:
        if ((데.get("헤드") or {}).get("주당") or {}).get(s) is None:
            continue
        w = (시.get("세계") or {}).get(s)
        if not w or not (w.get("세계") or "").strip():
            걸.append("시나리오 단추 「%s」 에 세계 서술이 없다(본편 시나리오 절의 「**%s 시나리오 「이름」** — …」 문단)" % (s, s))
    if (장부 or {}).get("전파표") and not any(t.get("전파") for t in 시.get("표") or []):
        걸.append("본편 시나리오 절에 「시나리오별 줄 변화와 그 까닭」 표가 없다(장부에는 전파 표가 있다)")
    for k, x in (서.get("손잡이") or {}).items():
        if (x.get("지렛대") or x.get("시나리오")) and not x.get("서사"):
            걸.append("손잡이 「%s」 는 %s인데 이어진 Narrative 문장이 본편에 없다(부록 「Narrative와 입력값 전체」 · 항목 절의 「이 절이 담은 Narrative」)"
                     % (x.get("이름") or k, "값을 가르는 가정" if x.get("지렛대") else "시나리오가 가른 가정"))
    if 종가 and G.get("역산곡선") and not ((서.get("역산") or {}).get("판정")):
        걸.append("종가가 있는데 Reverse DCF 판정 문단이 없다(본편 Reverse DCF 절의 첫 문단)")
    for 곳, g in 서사글들(서):
        for w in _문체걸림(g):
            걸.append("%s — %s" % (w, 곳))
        for w in 금지어:
            if w in 용어.권유어밖(g):                         # 1.1.9 — 회계 용어 안의 매수 · 매도는 뺀다
                걸.append("금지어 「%s」 — %s" % (w, 곳))
    return list(dict.fromkeys(걸))


def 설계내부번호(데):
    """모델 설계(본편의 추정 구조 ~ 가치 브리지를 그대로 옮긴 글)에 남은 내부 번호 「A-30」 의 수 — 걸림이 아니라 알림(본편 글을 이 판이 고치지 않는다)."""
    return len(_번호꼴.findall(_설계글(데.get("설계"))))


# 틀 글(판이 쓰는 고정 문구)의 문체 — 화면에 나가는 글은 HTML 의 태그 밖 글과 스크립트의 문자열 조각이다(식별자 · 주석 · 정규식은 글이 아니다).
def _js글조각(코드):
    """JS 코드 → 문자열 조각 목록(따옴표 · 템플릿 글 — `${}` 안은 코드로 다시 읽는다). 주석 · 정규식 글은 건너뛴다."""
    낸, 틀 = [], []
    st = [["코드", 0]]
    i, n, 앞, 낱 = 0, len(코드), "(", ""
    while i < n:
        c = 코드[i]
        if st[-1][0] == "틀":
            if c == "\\":
                틀.append(코드[i:i + 2])
                i += 2
            elif c == "`":
                낸.append("".join(틀))
                틀 = []
                st.pop()
                i += 1
                앞 = "x"
            elif c == "$" and 코드[i + 1:i + 2] == "{":
                낸.append("".join(틀))
                틀 = []
                st.append(["코드", 0, "틀"])
                i += 2
                앞 = "("
            else:
                틀.append(c)
                i += 1
            continue
        if c in "\"'":
            j, s = i + 1, []
            while j < n and 코드[j] != c and 코드[j] != "\n":
                if 코드[j] == "\\":
                    s.append(코드[j:j + 2])
                    j += 2
                    continue
                s.append(코드[j])
                j += 1
            낸.append("".join(s))
            i, 앞, 낱 = j + 1, "x", ""
            continue
        if c == "`":
            st.append(["틀"])
            틀 = []
            i += 1
            continue
        if 코드.startswith("//", i):
            j = 코드.find("\n", i)
            i = n if j < 0 else j
            continue
        if 코드.startswith("/*", i):
            j = 코드.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        if c == "/" and (앞 in "(,=:[!&|?{};+-*%<>~^" or 낱 in ("return", "typeof", "case", "of", "in")):
            j, 칸 = i + 1, False
            while j < n and 코드[j] != "\n":
                if 코드[j] == "\\":
                    j += 2
                    continue
                if 코드[j] == "[":
                    칸 = True
                elif 코드[j] == "]":
                    칸 = False
                elif 코드[j] == "/" and not 칸:
                    break
                j += 1
            i, 앞, 낱 = j + 1, "x", ""
            continue
        if c == "{":
            st[-1][1] += 1
        elif c == "}":
            if st[-1][1] == 0 and len(st) > 1 and len(st[-1]) > 2:
                st.pop()
                i += 1
                앞, 낱 = "x", ""
                continue
            st[-1][1] -= 1
        if c.isalnum() or c == "_" or c == "$" or ord(c) > 0x3000:
            낱 = (낱 + c) if 앞 == "x" and 낱 else c
            앞 = "x"
        elif not c.isspace():
            앞, 낱 = c, ""
        i += 1
    return 낸


def 틀화면글(html글):
    """틀이 쓰는 화면 글 — 태그 밖 글 + 스크립트 문자열 조각(데이터 객체 · 라이브러리 · 스타일은 뺀다)."""
    s = 틀글(html글)
    낸 = [보이는글(s)]
    for m in re.finditer(r"<script(?![^>]*application/json)[^>]*>(.*?)</script>", s, flags=re.S | re.I):
        낸 += _js글조각(m.group(1))
    return [x for x in 낸 if x and x.strip()]


def 틀문체(html글):
    """틀의 화면 글에 내부 번호 · 번호식 이름 · 내부어 · 비유어 · 평서체 끝(v27 — 화면 글도 레터와 같은 합쇼체)이 있나 → 걸림 목록."""
    import 어투                                             # noqa: PLC0415
    걸 = []
    for g in 틀화면글(html글):
        for w in _문체걸림(g):
            걸.append("%s — 판의 고정 글(%s)" % (w, re.sub(r"\s+", " ", g).strip()[:40]))
        for _a, _b, w, _n in 어투.끝찾기(g, 코드=True):
            걸.append("평서체 끝 「%s」 — 판의 고정 글(%s)" % (w, re.sub(r"\s+", " ", g).strip()[:40]))
    return list(dict.fromkeys(걸))


def _결합포함(결):
    """결합 민감도의 손잡이에 할인율(WACC) · 영구성장률이 들어 있나 — 캡션이 「포함」 · 「고정」 을 데이터에서 읽는다."""
    def 글(h):
        return " ".join(["%s" % (h.get("이름") or "")] + ["%s" % t for t in (h.get("대상") or [])] + ["%s" % (h.get("키") or "")])
    손 = [글(h) for h in (결.get("손잡이") or []) if isinstance(h, dict)]
    할 = bool(결.get("할인율포함")) or any(("WACC" in t or "할인율" in t) for t in 손)
    g = bool(결.get("영구성장률포함")) or any(("영구성장률" in t or re.search(r"(^|\s)g($|\s)", t)) for t in 손)
    return {"할인율": 할, "영구성장률": g}


def 데이터(장부경로=None, 격자경로=None, 결합경로=None, 레터경로=None, 주가경로=None, 가정경로=None):
    """화면이 읽는 데이터 객체 — 장부 · 격자 · 결합 민감도 그대로(해시와 함께). 장부가 없으면 가정으로 세 시나리오를 엔진에서 받는다(실험 판)."""
    알림 = []
    장부 = _읽기(장부경로) if 장부경로 else None
    if not 격자경로:
        후보 = []
        for 기준 in (장부경로, 가정경로):
            if 기준:
                d = os.path.dirname(os.path.abspath(기준))
                후보 += [os.path.join(d, "_raw", "민감도격자.json"), os.path.join(os.path.dirname(d), "_raw", "민감도격자.json")]
        if 장부 and (장부.get("재료파일") or {}).get("민감도격자"):
            후보.insert(0, os.path.join(os.path.dirname(os.path.abspath(장부경로)), 장부["재료파일"]["민감도격자"]["파일"]))
        격자경로 = next((p for p in 후보 if os.path.exists(p)), None)
    if not 격자경로 or not os.path.exists(격자경로):
        raise FileNotFoundError("민감도격자.json 이 없다 — `python 스크립트/민감도격자.py 가정.json` 을 먼저(레터보다 먼저 — 장부가 재료로 적는다)")
    격 = _읽기(격자경로)
    if not 결합경로:
        p = os.path.join(os.path.dirname(os.path.abspath(격자경로)), "결합민감도.json")
        결합경로 = p if os.path.exists(p) else None
    결 = _읽기(결합경로) if 결합경로 else None
    if 결 is None:
        알림.append("결합 민감도 파일이 없어 분포 모듈을 뺐다(`결합민감도.py 가정.json`)")
    elif not 결.get("표본주당"):
        알림.append("결합 민감도 파일에 판마다의 값이 없다(옛 판) — 분위만 보인다. `결합민감도.py` 를 다시 돌리면 쌓기가 선다")
    헤드 = {}
    if 장부:
        헤드 = {s: _n((장부.get("주당가치") or {}).get(s)) for s in 시나리오들}
        주주 = {s: _n((장부.get("주주가치") or {}).get(s)) for s in 시나리오들}
        영업 = {s: _n((장부.get("영업가치") or {}).get(s)) for s in 시나리오들}
        if 장부.get("가정해시") and 격.get("가정해시") and 장부["가정해시"] != 격["가정해시"]:
            알림.append("장부와 격자가 다른 가정 파일에서 났다(가정 해시가 다르다)")
    else:
        if not 가정경로:
            raise FileNotFoundError("장부도 가정도 없다 — --장부(게이트를 지난 레터의 장부) 또는 실험이면 --가정")
        import importlib                             # noqa: PLC0415
        if 여기 not in sys.path:
            sys.path.insert(0, 여기)
        importlib.import_module("엔진")
        from 엔진 import 계산                         # noqa: PLC0415
        가 = _읽기(가정경로)
        헤드, 주주, 영업 = {}, {}, {}
        for s in 시나리오들:
            R = 계산(가, s)
            헤드[s], 주주[s], 영업[s] = R["요약"]["주당가치"], R["요약"]["주주가치"], R["요약"]["영업가치"]
        알림.append("장부 없이 낸 실험 판 — 레터 게이트로 대조하지 않았다")
    k = 1.0 / ((격.get("단위") or {}).get("나눔") or 1.0)
    결요 = 결합요약(결, 격.get("종가"))
    주띠 = 주가띠(주가경로, 격.get("평가기준일") or "") if 주가경로 else None
    if 주가경로 and not 주띠:
        알림.append("주가 파일을 읽지 못해 주가 띠를 뺐다")
    제목 = None
    if 레터경로 and os.path.exists(레터경로):
        for 줄 in io.open(레터경로, encoding="utf-8"):
            if 줄.startswith("# "):
                제목 = 줄[2:].strip()
                break
    설 = 설계읽기(레터경로)
    서 = 서사읽기(레터경로, 격, 장부, 결)                   # 2026-10-25 R6 — 결론 · Narrative · 시나리오 세계 · 손잡이의 Narrative · 역산 판정(본편에서 자른다)
    if not 레터경로:
        알림.append("본편 레터 없이 낸 판이라 서사(결론 · Narrative · 시나리오 서술)와 모델 설계가 빠졌다 — --레터 레터_회사.md 로 다시 낸다")
    elif 설 is None:
        알림.append("본편 레터에서 모델 설계 절(추정 구조 ~ 가치 브리지)을 찾지 못했다 — 게이트를 지난 본편(레터_회사.md)을 준다")
    for 손키, x in ((서 or {}).get("손잡이") or {}).items():
        if not x.get("서사"):
            알림.append("손잡이 「%s」 에 이어진 Narrative 문장을 본편에서 찾지 못했다(부록 「Narrative와 입력값 전체」 · 항목 절의 「이 절이 담은 Narrative」)" % (x.get("이름") or 손키))
    # 2026-10-25 — DCF 적합성 경보(`DCF적합성.py`)면 머리 아래에 고지 문장(파일의 「고지글」 — 레터 결론 · 3분 레터와 같은 사실)
    적합, 적합경로 = None, None
    재적 = ((장부 or {}).get("재료파일") or {}).get("DCF적합성")
    for 곳 in ([os.path.join(os.path.dirname(os.path.abspath(장부경로)), 재적["파일"])] if (재적 and 장부경로) else []) + [os.path.join(os.path.dirname(os.path.abspath(격자경로)), "DCF적합성.json")]:
        if os.path.exists(곳):
            적합경로 = 곳
            break
    if 적합경로:
        j = _읽기(적합경로) or {}
        if j.get("판정") == "경보" and j.get("고지글"):
            적합 = {"판정": "경보", "글": list(j["고지글"]), "해시": _해시파일(적합경로)}
    해시 = {"장부": _해시파일(장부경로) if 장부경로 else None, "격자": _해시파일(격자경로), "결합": _해시파일(결합경로) if 결합경로 else None,
          "레터": _해시파일(레터경로) if 레터경로 and os.path.exists(레터경로) else None, "주가": _해시파일(주가경로) if 주가경로 and os.path.exists(주가경로) else None}
    return {
        "형식": 형식, "만든날": datetime.date.today().isoformat(), "제목": 제목 or 격.get("회사"),
        "회사": (장부 or {}).get("회사") or 격.get("회사"), "장부있음": bool(장부),
        "헤드": {"주당": 헤드, "주주": {s: (v * k if v is not None else None) for s, v in 주주.items()},
               "영업": {s: (v * k if v is not None else None) for s, v in 영업.items()}},
        "격자": 격, "결합": 결요, "풋볼": 풋볼(헤드, 격, 결요, 주띠), "주가띠": 주띠, "알림": 알림, "해시": 해시, "설계": 설, "서사": 서,
        "실험": not bool(장부),
        "장부재료": (장부 or {}).get("재료파일") or {},
        "적합성": 적합,
        "파일": {"장부": os.path.basename(장부경로) if 장부경로 else None, "격자": os.path.basename(격자경로),
               "결합": os.path.basename(결합경로) if 결합경로 else None},
    }


def 짓기(데, 틀=None):
    틀글 = io.open(틀 or 틀파일, encoding="utf-8").read()
    try:
        라 = io.open(애니메, encoding="utf-8").read()
        if "</script" in 라.lower():
            raise SystemExit("라이브러리 글에 </script 가 있어 인라인으로 실을 수 없다")
    except OSError:
        라 = ""
    j = json.dumps(데, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return 틀글.replace("/*__애니메__*/", 라).replace("/*__데이터__*/null", j)


# ────────────────────────────────────────────────── 합본(2026-10-26 결정 — 레터 세 판을 HTML 한 장으로)
# 바탕은 게이트를 지난 편집본 전체(3분 레터 + 본편 + 부록)를 `레터HTML.문서` 가 지은 한 장이다(그림 · 글은 본편 그대로).
# 이 판은 움직이는 모듈만 틀에서 떼어 그 숫자가 나온 본편 절 끝에 끼운다. 결론 · Narrative · 모델 설계 · 끝 모듈은 본편과 같은 글이라 숨긴다
# (스크립트가 그 칸에 쓰므로 지우지 않고 숨긴 칸에 둔다). 틀의 CSS 는 `.ix` 안으로 가두어 본편 스타일과 부딪히지 않게 한다.
합본표지 = '<meta name="레터합본" content="1">'
_ix꼴 = re.compile(r"<!--ix:([^>]+?)-->\n?(.*?)\n?<!--/ix:\1-->", re.S)
모듈절 = (("격자", "영구"), ("모션", "주주가치"), ("시나리오", "시나리오"), ("손잡이", "민감도"), ("분포", "민감도"), ("풋볼", "민감도"), ("역산", "역산"))
숨길모듈 = ("결론", "이야기", "설계", "끝")
절앞말 = {"매출": "매출 추정", "비용": "영업비용 추정", "인건비": "인건비 추정", "재투자": "설비투자와 감가상각", "운전자본": "운전자본 추정",
       "세금": "법인세와 FCFF", "할인율": "할인율", "영구": "Terminal Value", "주주가치": "가치 브리지", "시나리오": "시나리오 분석",
       "민감도": "민감도 분석", "역산": "Reverse DCF", "신호": "모니터링"}
합본css덧 = (".ix.ix-mod{margin:1.8rem 0 1.4rem;padding:1rem 1.15rem 1.1rem;border:1px solid var(--rule-2);border-radius:10px;background:var(--paper)}"
          ".ix.ix-mod > h3:first-child,.ix.ix-mod > .ix-kick{margin-top:0}"
          ".ix .ix-kick{font-size:.78rem;letter-spacing:.06em;color:var(--muted);margin:0 0 .4rem}"
          ".ix #시나리오머리,.ix #시나리오글,.ix #역판정{display:none}"
          ".ix.ix-about summary{cursor:pointer;font-weight:600}"
          "@media print{.ix,.ix-hidden{display:none!important}}")
_합본같음꼴 = re.compile(r"<!--\s*합본:3분과같음\s*-->.*?<!--\s*/합본:3분과같음\s*-->\n?", re.S)


def 손잡이절(대상):
    """손잡이 대상(가정 번호 · WACC.구간) → 그 가정의 본편 절 키(레터이야기.절가정) — 여럿이면 처음 것. 모르면 None."""
    import importlib                                     # noqa: PLC0415
    이 = importlib.import_module("레터이야기")
    for t in 대상 or []:
        t = "%s" % t
        if t.startswith("WACC"):
            return "할인율"
        if t.isdigit():
            try:
                k = 이.절가정(t)
            except Exception:                            # noqa: BLE001
                k = None
            if k:
                return k
    return None


def _범위css(css, 범=".ix"):
    """CSS 규칙마다 선택자를 범 안으로 가둔다(:root · html · body → 범 · :root[…] → :root[…] 범 · .wrap 은 뺀다). @media · @supports 안도 같게."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)

    def 선택자(sel):
        낸 = []
        for x in sel.split(","):
            x = x.strip()
            if not x or x == ".wrap":
                continue
            if x in ("html", "body", ":root"):
                낸.append(범)
            elif x.startswith(":root"):
                낸.append("%s %s" % (x, 범))
            elif x == "*":
                낸 += [범, 범 + " *"]
            else:
                낸.append("%s %s" % (범, x))
        return ",".join(dict.fromkeys(낸))

    def 덩이(t):
        o, k = [], 0
        while k < len(t):
            a = t.find("{", k)
            if a < 0:
                break
            머 = t[k:a].strip()
            깊, b = 1, a + 1
            while b < len(t) and 깊:
                깊 += 1 if t[b] == "{" else (-1 if t[b] == "}" else 0)
                b += 1
            몸 = t[a + 1:b - 1]
            if 머.startswith(("@media", "@supports")):
                o.append("%s{%s}" % (머, 덩이(몸)))
            elif 머.startswith("@"):
                o.append("%s{%s}" % (머, 몸))
            else:
                선 = 선택자(머)
                if 선:
                    o.append("%s{%s}" % (선, 몸))
            k = b
        return "".join(o)
    return 덩이(css)


def _틀나누기(단독):
    """단독 판 HTML → (css, {모듈: 조각}, 스크립트들). 조각은 틀의 `<!--ix:이름-->` 표지 사이."""
    m = re.search(r"<style>(.*?)</style>", 단독, re.S)
    css = m.group(1) if m else ""
    조각 = {k: v for k, v in _ix꼴.findall(단독)}
    i = 단독.find('<script type="application/json" id="레터데이터">')
    j = 단독.rfind("</body>")
    스 = 단독[i:j] if (i >= 0 and j > i) else ""
    return css, 조각, 스


def _머리3(t):
    return re.sub(r"<(/?)h2\b", r"<\1h3", t)


def _절끝자리(html, 키):
    """본편 HTML 에서 그 절(「## N. 앞말 …」 의 h2 id="sN")이 끝나는 자리(다음 h2 · 단 · 부록 앞). 없으면 None."""
    앞 = 절앞말.get(키)
    if not 앞:
        return None
    m = re.search(r'<h2 id="s\d+">\d+\. %s\b' % re.escape(앞), html)
    if not m:
        return None
    n = re.search(r'\n<h2 id="s\d+">|\n<div class="part"|\n</div><div class="wrap" id="appendix">', html[m.end():])
    return m.end() + n.start() if n else None


def 바탕글(본편html):
    """합본의 바탕 — 1절의 결론 머리(띠 · 결론 다섯 줄 — 3분 레터와 같은 글)를 걷어 낸 한 장(레터본문.결론절 의 표지 사이)."""
    return _합본같음꼴.sub("", 본편html, count=1)


def 합치기(본편html, 데, 틀=None):
    """게이트를 지난 한 장(3분 레터 + 본편 + 부록)에 움직이는 모듈을 끼운 HTML → (글, 놓인 자리 {모듈: 절 키}). 표지 `합본표지` 를 단다."""
    css, 조각, 스 = _틀나누기(짓기(데, 틀))
    글 = 바탕글(본편html)
    놓인, 끼울 = {}, {}
    손절 = []
    for x in (((데.get("서사") or {}).get("손잡이")) or {}).values():
        k = (x or {}).get("절")
        if k and k not in 손절 and _절끝자리(글, k) is not None:
            손절.append(k)
    for 키 in 손절:                                       # 손잡이 카드 자리 — 그 가정의 절 끝
        끼울.setdefault(키, []).append('<div class="ix ix-mod ix-knobslot"><p class="ix-kick">이 절의 가정을 움직여 보기</p>'
                                      '<p class="cap">슬라이더는 평가 모델이 미리 계산한 칸만 고릅니다. 결과는 카드 아래 줄과 민감도 분석 절의 큰 숫자에 함께 나옵니다.</p>'
                                      '<section class="knobs" id="ix-knobs-%s" aria-label="가정 슬라이더"></section></div>' % 키)
        놓인["손잡이:" + 키] = 키
    for 모, 키 in 모듈절:
        if 조각.get(모) and _절끝자리(글, 키) is not None:
            끼울.setdefault(키, []).append('<div class="ix ix-mod" data-ix="%s">%s</div>' % (모, _머리3(조각[모])))
            놓인[모] = 키
    for 키, 덩이들 in 끼울.items():
        자리 = _절끝자리(글, 키)
        글 = 글[:자리] + "\n" + "\n".join(덩이들) + 글[자리:]
    머 = 조각.get("머리", "")
    알 = "".join(re.findall(r'<div class="(?:band|notice)" id="(?:실험띠|알림|적합성)"[^>]*>\s*</div>', 머))
    숨 = (re.sub(r'<div class="(?:band|notice)" id="(?:실험띠|알림|적합성)"[^>]*>\s*</div>', "", 머)
         + "".join(조각.get(k, "") for k in 숨길모듈) + "".join(조각.get(모, "") for 모, _k in 모듈절 if 모 not in 놓인))
    읽 = 조각.get("읽기", "")
    k = 글.find('<div class="part" id="본편">')
    if 읽 and k >= 0:                                     # 3분 레터 뒤 · 본편 앞 — 움직이는 그림을 읽는 법(접힘)
        글 = 글[:k] + '<details class="ix ix-mod ix-about"><summary>움직이는 그림을 읽는 법</summary>%s</details>\n' % _머리3(읽) + 글[k:]
        놓인["읽기"] = "본편앞"
    elif 읽:
        숨 += 읽
    if 알:                                                # 알림 · 적합성 고지 칸은 첫 제목 뒤(스크립트가 채운다 — 비면 숨은 채로 둔다)
        h = 글.find("</h1>")
        글 = 글[:h + 5] + '\n<div class="ix ix-notes">%s</div>' % 알 + 글[h + 5:]
    j = 글.rfind("</body>")
    글 = 글[:j] + '<div class="ix ix-hidden" hidden aria-hidden="true">%s</div>\n%s' % (숨, 스) + 글[j:]
    글 = 글.replace("</head>", "%s\n<style class=\"ix-css\">%s%s</style>\n</head>" % (합본표지, _범위css(css), 합본css덧), 1)
    return 글, 놓인


def 합본뺀글(html글):
    """합본 HTML 에서 끼운 것(.ix 조각 · 스타일 · 스크립트 · 표지)을 걷어 낸 글 — 바탕(바탕글)과 맞대는 데 쓴다."""
    s = html글.replace(합본표지 + "\n", "", 1)
    s = re.sub(r'<style class="ix-css">.*?</style>\n', "", s, count=1, flags=re.S)
    i = s.find('<div class="ix ix-hidden" hidden aria-hidden="true">')
    j = s.rfind("</body>")
    if 0 <= i < j:
        s = s[:i] + s[j:]
    s = re.sub(r'<details class="ix ix-mod ix-about">.*?</details>\n', "", s, count=1, flags=re.S)
    s = re.sub(r'\n<div class="ix ix-notes">.*?</div>(?=\n)', "", s, count=1, flags=re.S)
    while True:                                           # 절 끝에 끼운 모듈 — 짝 맞는 </div> 까지
        m = re.search(r'\n<div class="ix ix-mod[^"]*"[^>]*>', s)
        if not m:
            break
        깊, b = 1, m.end()
        while 깊:
            a1, a2 = s.find("<div", b), s.find("</div>", b)
            if a2 < 0:
                break
            if 0 <= a1 < a2:
                깊, b = 깊 + 1, a1 + 4
            else:
                깊, b = 깊 - 1, a2 + 6
        s = s[:m.start()] + s[b:]
    return s


def 합본검사(html글, 데, 본편html):
    """합본 HTML → 걸림 목록: 표지 · 데이터 객체 = 데 · 끼운 것을 걷으면 바탕(1절 결론 머리를 갈음한 한 장)과 같다 · 모듈 글의 금지어 · id 겹침."""
    걸 = []
    if 합본표지 not in html글:
        걸.append("합본 표지가 없다")
    d = 데이터읽기(html글)
    if d is None:
        걸.append("데이터 객체가 없다")
    elif json.dumps(d, sort_keys=True, ensure_ascii=False) != json.dumps(데, sort_keys=True, ensure_ascii=False):
        걸.append("데이터 객체가 장부 · 재료에서 지은 것과 다르다")
    if 합본뺀글(html글) != 바탕글(본편html):
        걸.append("끼운 모듈을 걷어 낸 글이 본편(게이트를 지난 한 장)과 다르다")
    모 = []
    for m in re.finditer(r'<div class="ix ix-mod[^"]*"[^>]*>', html글):
        모.append(html글[m.start():m.start() + 6000])
    보 = 보이는글("\n".join(모))
    for w in 금지어:
        if w in 용어.권유어밖(보):
            걸.append("모듈 글에 금지어 「%s」" % w)
    아 = re.findall(r'\sid="([^"$`{]+)"', re.sub(r"<script\b.*?</script>", " ", html글, flags=re.S))
    겹 = sorted({x for x in 아 if 아.count(x) > 1})
    if 겹:
        걸.append("id 가 겹친다: %s" % " · ".join(겹[:8]))
    return 걸


# ────────────────────────────────────────────────── 검사(게이트 ⑦ 의 연장)

_데이터꼴 = re.compile(r'<script type="application/json" id="레터데이터">(.*?)</script>', re.S)


def 데이터읽기(html글):
    m = _데이터꼴.search(html글)
    if not m:
        return None
    return json.loads(m.group(1))


def 보이는글(html글):
    """화면에 고정으로 박힌 글(스크립트 · 스타일 · 데이터 객체를 뺀 태그 밖 글)."""
    s = re.sub(r"<script\b.*?</script>", " ", html글, flags=re.S | re.I)
    s = re.sub(r"<style\b.*?</style>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return s


def 틀글(html글):
    """데이터 객체와 라이브러리를 뺀 틀(화면 글 + 스크립트) — 금지어는 여기서 본다."""
    s = _데이터꼴.sub(" ", html글)
    i = s.find("/*__애니메끝__*/")
    j = s.find("/*__애니메시작__*/")
    if j >= 0 and i > j:
        s = s[:j] + s[i:]
    return s


def 설계검사(데, d, 레터경로=None):
    """모델 설계가 실렸나 · 본편과 같은가(해시 · 절 번호 · 제목 · 블록) · 항목 절이 빠지지 않았나 → 걸림 목록."""
    걸 = []
    설 = 데.get("설계")
    if not isinstance(설, dict) or not 설.get("절"):
        return ["모델 설계가 없다 — 본편 레터(--레터 레터_회사.md)를 주고 판을 다시 낸다(항목마다 무엇을 근거로 어떻게 추정했나가 이 판에 빠진다)"]
    레터경로 = 레터경로 or os.path.join(d, 설.get("파일") or "")
    if not os.path.exists(레터경로):
        return ["본편 레터 파일이 없다(%s) — 판과 같은 폴더에 둔다" % os.path.basename(레터경로)]
    if _해시파일(레터경로) != 설.get("해시"):
        걸.append("본편 해시가 다르다(판을 낸 뒤 본편이 바뀌었다)")
    새 = 설계읽기(레터경로) or {"절": []}
    옛표 = [(x["번호"], x["제목"]) for x in 설["절"]]
    새표 = [(x["번호"], x["제목"]) for x in 새["절"]]
    빠진 = [t for t in 새표 if t not in 옛표]
    if 빠진:
        걸.append("본편의 모델 설계 절이 판에 빠졌다 — %s" % " · ".join("%d절 %s" % t for t in 빠진))
    if 새표 == 옛표 and json.dumps(새["절"], sort_keys=True, ensure_ascii=False) != json.dumps(설["절"], sort_keys=True, ensure_ascii=False):
        걸.append("판에 실린 모델 설계 글 · 표가 본편과 다르다")
    if not any(x["키"] == "매출" for x in 설["절"]):
        걸.append("모델 설계에 매출 추정 절이 없다")
    return 걸


def 서사대조(데, d, 레터경로=None, 장부=None, 결합경로=None):
    """판에 실린 서사 = 본편에서 다시 자른 서사(본편 해시 · 글 · 손잡이의 Narrative)인가 → 걸림 목록."""
    서 = 데.get("서사")
    if not isinstance(서, dict) or not 서.get("파일"):
        return []
    경로 = 레터경로 or os.path.join(d, 서["파일"])
    if not os.path.exists(경로):
        return ["본편 레터 파일이 없다(%s) — 판과 같은 폴더에 둔다" % os.path.basename(경로)]
    if _해시파일(경로) != 서.get("해시"):
        return ["본편 해시가 다르다(판을 낸 뒤 본편이 바뀌었다)"]
    결 = _읽기(결합경로) if 결합경로 and os.path.exists(결합경로) else None
    새 = 서사읽기(경로, 데.get("격자"), 장부, 결)
    if json.dumps(새, sort_keys=True, ensure_ascii=False) != json.dumps(서, sort_keys=True, ensure_ascii=False):
        return ["판에 실린 서사가 본편과 다르다(결론 · Narrative · 시나리오 서술 · 손잡이의 Narrative 가운데)"]
    return []


def 검사(html경로, 장부경로=None, 격자경로=None, 결합경로=None, 레터경로=None):
    """인터랙티브 판의 데이터 객체 = 장부 · 재료 파일(해시 · 내용) · 모델 설계 = 본편 · 서사(결론 · Narrative · 시나리오 세계 · 손잡이의
    Narrative · 역산 판정)가 실렸고 본편과 같다 · 고정 글에 숫자 없음 · 금지어 없음 · 화면 글에 내부 번호 · 내부어 · 비유어 없음 → 걸림 목록."""
    걸 = []
    try:
        글 = io.open(html경로, encoding="utf-8").read()
    except OSError as e:
        return ["인터랙티브 판을 읽지 못했다(%s)" % type(e).__name__]
    try:
        데 = 데이터읽기(글)
    except ValueError:
        데 = None
    if not isinstance(데, dict) or 데.get("형식") != 형식:
        return ["데이터 객체가 없거나 형식이 다르다"]
    d = os.path.dirname(os.path.abspath(html경로))
    장부경로 = 장부경로 or (os.path.join(d, 데["파일"]["장부"]) if (데.get("파일") or {}).get("장부") else None)
    격자경로 = 격자경로 or os.path.join(d, "_raw", 데["파일"]["격자"])
    결합경로 = 결합경로 or ((os.path.join(d, "_raw", 데["파일"]["결합"])) if 데["파일"].get("결합") else None)
    if not 데.get("장부있음"):
        걸.append("장부 없이 낸 실험 판이다 — 레터 장부로 다시 낸다(`--장부`)")
    if 장부경로:
        if not os.path.exists(장부경로):
            걸.append("장부 파일이 없다(%s)" % os.path.basename(장부경로))
        else:
            장부 = _읽기(장부경로)
            if _해시파일(장부경로) != 데["해시"]["장부"]:
                걸.append("장부 해시가 다르다(인터랙티브 판을 낸 뒤 장부가 바뀌었다)")
            for s in 시나리오들:
                a, b = _n((장부.get("주당가치") or {}).get(s)), _n(데["헤드"]["주당"].get(s))
                if (a is None) != (b is None) or (a is not None and abs(a - b) > 1e-9 * max(1.0, abs(a))):
                    걸.append("헤드라인 %s 주당가치가 장부와 다르다" % s)
            재 = (장부.get("재료파일") or {}).get("민감도격자")
            if not 재:
                걸.append("장부가 민감도격자를 재료로 적지 않았다 — 격자를 낸 뒤 레터를 다시 낸다(재료 해시가 장부에 남게)")
            elif 재.get("해시") != 데["해시"]["격자"]:
                걸.append("장부에 적힌 민감도격자 해시와 판에 박힌 격자 해시가 다르다")
            재 = (장부.get("재료파일") or {}).get("결합민감도")
            if 데["해시"].get("결합") and 재 and 재.get("해시") != 데["해시"]["결합"]:
                걸.append("장부에 적힌 결합민감도 해시와 판에 박힌 해시가 다르다")
    if not os.path.exists(격자경로):
        걸.append("격자 파일이 없다(%s)" % os.path.basename(격자경로))
    else:
        if _해시파일(격자경로) != 데["해시"]["격자"]:
            걸.append("격자 파일 해시가 다르다(판을 낸 뒤 격자가 바뀌었다)")
        if json.dumps(_읽기(격자경로), sort_keys=True, ensure_ascii=False) != json.dumps(데["격자"], sort_keys=True, ensure_ascii=False):
            걸.append("판에 박힌 격자가 격자 파일과 다르다")
    if 결합경로 and 데["해시"].get("결합"):
        if not os.path.exists(결합경로):
            걸.append("결합 민감도 파일이 없다")
        elif _해시파일(결합경로) != 데["해시"]["결합"]:
            걸.append("결합 민감도 파일 해시가 다르다")
    적 = 데.get("적합성")
    if isinstance(적, dict) and 장부경로 and os.path.exists(장부경로):
        재 = (_읽기(장부경로).get("재료파일") or {}).get("DCF적합성")
        if 재 and 재.get("해시") and 적.get("해시") != 재["해시"]:
            걸.append("판에 박힌 DCF 적합성 고지와 장부에 적힌 재료 해시가 다르다(레터 · 판 가운데 하나를 다시 낸다)")
    걸 += 설계검사(데, d, 레터경로)
    장부값 = _읽기(장부경로) if 장부경로 and os.path.exists(장부경로) else None
    걸 += 서사검사(데, 장부값)                                # 2026-10-25 R6 — 서사가 실렸나 · 화면 글의 문체
    걸 += 서사대조(데, d, 레터경로, 장부값, 결합경로)          # 본편과 같은 글인가(해시 · 다시 자른 글)
    걸 += 틀문체(글)                                         # 판의 고정 글 — 내부 번호 · 내부어 · 비유어
    고정 = 보이는글(글)
    숫 = re.findall(r"\d", 고정)
    if 숫:
        걸.append("고정 글에 숫자가 있다(숫자는 데이터 객체에서만 — %s)" % "".join(sorted(set(숫)))[:20])
    틀 = 틀글(글)
    설글 = _설계글(데.get("설계"))
    for w in 금지어:
        if w in 용어.권유어밖(틀):
            걸.append("금지어 「%s」" % w)
        elif w in 용어.권유어밖(설글):
            걸.append("금지어 「%s」 — 모델 설계(본편에서 옮긴 글)에" % w)
    return list(dict.fromkeys(걸))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "검사":
        ap = argparse.ArgumentParser(allow_abbrev=False, description="인터랙티브 판 검사")
        ap.add_argument("html")
        ap.add_argument("--장부")
        ap.add_argument("--격자")
        ap.add_argument("--결합")
        ap.add_argument("--레터", help="본편 레터 md(없으면 판에 적힌 이름으로 판과 같은 폴더에서)")
        a = ap.parse_args(argv[1:])
        걸 = 검사(a.html, a.장부, a.격자, a.결합, a.레터)
        for x in 걸:
            print("  걸림 — %s" % x)
        try:
            n = 설계내부번호(데이터읽기(io.open(a.html, encoding="utf-8").read()) or {})
            if n:
                print("  알림 — 모델 설계(본편 그대로 옮긴 글)에 내부 번호 「A-」 %d곳 — 본편 글이라 이 판은 고치지 않는다" % n)
        except (OSError, ValueError):
            pass
        print("인터랙티브 판 검사 — %s" % ("걸림 %d" % len(걸) if 걸 else "통과"))
        return 발견 if 걸 else 통과
    ap = argparse.ArgumentParser(allow_abbrev=False, description="둘째 독자용 인터랙티브 레터(계산하지 않는 판)")
    ap.add_argument("--장부")
    ap.add_argument("--가정", help="장부 없이(실험) — 세 시나리오를 엔진에서 받는다")
    ap.add_argument("--격자")
    ap.add_argument("--결합")
    ap.add_argument("--레터")
    ap.add_argument("--주가", help="주가 CSV(날짜 · 종가) — 있으면 52주 띠")
    ap.add_argument("-o", "--출력", required=True)
    a = ap.parse_args(argv)
    try:
        데 = 데이터(a.장부, a.격자, a.결합, a.레터, a.주가, a.가정)
    except (FileNotFoundError, ValueError) as e:
        print("입력 오류 — %s" % e)
        return 입력오류
    if not 데.get("실험"):                                   # 2026-10-25 R6 — 서사 없이 짓지 않는다(실험 판은 머리에 띠를 크게 두고 짓는다)
        빈 = 서사검사(데, _읽기(a.장부)) + ([] if 데.get("설계") else ["모델 설계가 없다 — 본편에서 추정 구조 ~ 가치 브리지 절을 찾지 못했다"])
        빈 += [x for x in 틀문체(짓기(데)) if x not in 빈]
        if 빈:
            for x in 데["알림"]:
                print("  알림 — %s" % x)
            for x in 빈:
                print("  걸림 — %s" % x)
            print("레터인터랙티브 — 판을 짓지 않았다: 서사가 비었거나 화면 글이 걸렸다(%d곳). 게이트를 지난 본편(--레터 레터_회사.md)과 장부로 다시 낸다" % len(빈))
            return 발견
    with io.open(a.출력, "w", encoding="utf-8") as f:
        f.write(짓기(데))
    for x in 데["알림"]:
        print("  알림 — %s" % x)
    if 데.get("실험"):
        print("  알림 — 장부 없이 낸 실험 판이다%s(화면 머리에 띠 · 게이트 ⑦-2 는 걸린다)" % ("" if 데.get("서사") else " · 서사 없음"))
    n = 설계내부번호(데)
    if n:
        print("  알림 — 모델 설계(본편 그대로 옮긴 글)에 내부 번호 「A-」 %d곳 — 본편 글이라 이 판은 고치지 않는다" % n)
    서 = 데.get("서사") or {}
    print("레터인터랙티브 — %s · 손잡이 %d(Narrative 문장 %d) · 풋볼 띠 %d · 모델 설계 %d절 · 서사 결론 %d줄 · 시나리오 세계 %d · %s(%d바이트)" % (
        데["회사"], len(데["격자"].get("손잡이") or {}), sum(1 for x in (서.get("손잡이") or {}).values() if x.get("서사")), len(데["풋볼"]),
        len((데.get("설계") or {}).get("절") or []), len((서.get("결론") or {}).get("줄") or []), len((서.get("시나리오") or {}).get("세계") or {}),
        a.출력, os.path.getsize(a.출력)))
    return 통과


if __name__ == "__main__":
    sys.exit(main())

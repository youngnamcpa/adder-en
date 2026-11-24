# -*- coding: utf-8 -*-
"""dart_직원패널 — OpenDART 정기보고서 주요정보 「직원 현황」(empSttus)으로 국내 상장사 인원 · 급여 패널을 짓는다 (2026-10-24 PK · B 단계).

무엇을 부르나 — `https://opendart.fss.or.kr/api/empSttus.json?corp_code=…&bsns_year=…&reprt_code=11011`(사업보고서).
누구를 부르나 — 기저율 패널과 같은 분모(주요계정 회사 · 연도 · 제외 산업 · 기업인수목적 · 매출 하한 — `상세변수공통.분모`). 최근 해부터 거꾸로.
이어받기 — 받은 응답을 `{상세변수}/_원천/직원현황/<연도>.jsonl` 에 줄마다 쌓는다(고유번호 · 해 · status · list). 다음 실행은 이미 있는 (회사, 해)를
          부르지 않는다. 하루 호출 상한(`--상한`, 기본 10,000)에 닿거나 OpenDART 가 사용 한도(020)를 알리면 멈추고 진행을 목록에 적는다.

줄 고르기(P2 실측)
  ① 사업부문(fo_bbm)이 「회사계 · 합계 · 총계 · 계 · 전체」 인 줄이 있으면 그 줄만 ② 그 안에서 성별(sexdstn)이 「합계 · 계」 인 줄이 있으면 그 줄만 ③ 아니면 모두 더한다
  인원 = Σ sm · 급여총액 = Σ fyer_salary_totamt · 1인평균급여 = 급여총액 ÷ 인원(공시 1인 평균 급여와 차 중앙 0.1% — P2)

    변수(모델 칸)                 정의                                                딱지
    직원수(501 바탕)              인원 합계(회사 단독 · 기말)                              같음(모델 인원범위 = 본사) · 연결 인원이면 [유추]
    급여총액(503 · 520 바탕)       연간 급여 총액(회사 단독 · 급여만)                        [유추] 퇴직급여 · 복리후생 제외
    1인평균급여(503)              급여총액 ÷ 인원                                       [유추] 별도 · 급여만 — 모델은 연결 급여 ÷ 본사 인원(범위 환산 배수)
    인원증가율(501)               직원수(t) ÷ 직원수(t−1) − 1                            같음(본사 기준)
    1인평균급여증가율(504)          1인평균급여(t) ÷ (t−1) − 1                            같음(성과급을 품은 급여 — 성과급을 따로 세우는 회사는 [유추])
    급여총액증가율(대조)            급여총액(t) ÷ (t−1) − 1                               [유추] 인건비 증가 대조

    python 스크립트/dart_직원패널.py [--상한 10000] [--부터 2015] [--까지 2025] [--짓기만]
키 — 환경변수 OPENDART_API_KEY(값을 찍지 않는다). 종료 코드 — 0 · 2(키 없음 · 분모 없음). 회사 · 업종 이름은 이 도구에 없다(범용).
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass
여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
import 상세변수공통 as 공  # noqa: E402

주소 = "https://opendart.fss.or.kr/api/empSttus.json"
간격 = 0.12
멈춤코드 = {"020": "사용 한도 초과", "010": "등록되지 않은 키", "011": "사용할 수 없는 키", "012": "접근할 수 없는 IP", "800": "시스템 점검", "901": "키 만료"}
_계 = re.compile(r"^(회사계|합계|총계|계|전체|전체계|전사계)$")


def 원천자리(뿌리=None):
    p = os.path.join(공.자리(뿌리), "_원천", "직원현황")
    os.makedirs(p, exist_ok=True)
    return p


def 받은것(뿌리=None):
    """{(고유번호, 해): 응답 dict} — 쌓인 jsonl 전부."""
    낸 = {}
    곳 = 원천자리(뿌리)
    for f in sorted(os.listdir(곳)):
        if not f.endswith(".jsonl"):
            continue
        with io.open(os.path.join(곳, f), encoding="utf-8") as h:
            for l in h:
                l = l.strip()
                if not l:
                    continue
                try:
                    d = json.loads(l)
                except ValueError:
                    continue
                if d.get("status") in 멈춤코드 or d.get("status") == "ERR":
                    continue                               # 받지 못한 것 — 다음에 다시
                낸[(d["고유번호"], int(d["해"]))] = d
    return 낸


def 부르기(고, 해, 키, 열기=None):
    q = urllib.parse.urlencode({"crtfc_key": 키, "corp_code": 고, "bsns_year": str(해), "reprt_code": "11011"})
    열기 = 열기 or (lambda u: urllib.request.urlopen(u, timeout=30).read())
    for i in range(3):
        try:
            j = json.loads(열기(주소 + "?" + q).decode("utf-8"))
            return {"status": j.get("status"), "message": j.get("message"), "list": j.get("list") or []}
        except Exception as e:                           # noqa: BLE001
            err = type(e).__name__
            time.sleep(1.5 * (i + 1))
    return {"status": "ERR", "message": err, "list": []}


def 받기(뿌리=None, 부터=2015, 까지=2025, 상한=10000, 키=None, 열기=None, 조용=False):
    키 = 키 or os.environ.get("OPENDART_API_KEY")
    if not 키:
        return {"멈춘까닭": "키 없음(OPENDART_API_KEY)", "부른수": 0}
    분 = 공.분모(뿌리, range(부터, 까지 + 1))
    있 = 받은것(뿌리)
    할 = [(고, y) for y in sorted(분, reverse=True) for 고 in sorted(분[y]) if (고, y) not in 있]
    부른, 까닭 = 0, "다 받음"
    곳 = 원천자리(뿌리)
    시 = time.time()
    for 고, y in 할:
        if 부른 >= 상한:
            까닭 = "하루 상한 %d 에 닿음" % 상한
            break
        d = 부르기(고, y, 키, 열기)
        부른 += 1
        if d["status"] in 멈춤코드:
            까닭 = "OpenDART %s(%s) — 멈춤" % (d["status"], 멈춤코드[d["status"]])
            break
        줄 = {"고유번호": 고, "해": y, "status": d["status"], "받은때": 공.지금(), "list": d["list"]}
        with io.open(os.path.join(곳, "%d.jsonl" % y), "a", encoding="utf-8") as h:
            h.write(json.dumps(줄, ensure_ascii=False) + "\n")
        if not 조용 and 부른 % 500 == 0:
            print("  직원현황 %d/%d 부름 · %.0f초" % (부른, len(할), time.time() - 시), flush=True)
        time.sleep(간격)
    남 = len(할) - 부른 if 까닭 != "다 받음" else 0
    상태 = {"마지막실행": 공.지금(), "부른수": 부른, "할일": len(할), "남은수": max(0, 남), "상한": 상한, "멈춘까닭": 까닭,
          "해": "%d~%d" % (부터, 까지), "걸린초": round(time.time() - 시, 1), "원천": "OpenDART empSttus(reprt_code 11011)"}
    공.목록고치기(뿌리, 이어=("직원현황", 상태))
    return 상태


def 합치기(목록):
    """응답 줄들 → (인원, 급여총액, 쓴 줄 수, 고른 규칙) — 회사계 · 성별 합계 줄 규칙."""
    rows = [x for x in 목록 if isinstance(x, dict)]
    if not rows:
        return None, None, 0, ""
    def 정(s):
        return re.sub(r"\s+", "", (s or "").strip())
    회 = [x for x in rows if _계.match(정(x.get("fo_bbm")))]
    고른 = 회 if 회 else rows
    규 = "회사계 줄" if 회 else "부문 합"
    성 = [x for x in 고른 if _계.match(정(x.get("sexdstn")))]
    if 성:
        고른, 규 = 성, 규 + " · 성별 합계 줄"
    인 = [공.수(x.get("sm")) for x in 고른]
    급 = [공.수(x.get("fyer_salary_totamt")) for x in 고른]
    인원 = sum(v for v in 인 if v) if any(인) else None
    급여 = sum(v for v in 급 if v) if any(급) else None
    return 인원, 급여, len(고른), 규


def 짓기(뿌리=None, 조용=False):
    있 = 받은것(뿌리)
    분모해 = 공.분모(뿌리)
    값들 = {}
    for (고, y), d in 있.items():
        if d.get("status") != "000":
            continue
        인원, 급여, n, 규 = 합치기(d.get("list") or [])
        if not 인원 or 인원 <= 0:
            continue
        첫 = (d.get("list") or [{}])[0]
        값들[(고, y)] = {"인원": 인원, "급여": 급여 if (급여 and 급여 > 0) else None, "rcept": 첫.get("rcept_no", ""), "끝": 첫.get("stlm_dt", ""), "규": 규, "줄": n}
    줄 = {k: [] for k in ("직원수", "급여총액", "1인평균급여", "인원증가율", "1인평균급여증가율", "급여총액증가율")}
    뺌 = {k: 0 for k in 줄}

    def 넣(변, 고, y, v, 분자, 분모, 단위, 딱지, 비고, 범위=None):
        if v is None:
            return
        if 범위 and not (범위[0] <= v <= 범위[1]):
            뺌[변] += 1
            return
        a = 값들[(고, y)]
        줄[변].append({"고유번호": 고, "회계연도": y, "값": v, "분자": 분자, "분모": 분모, "단위": 단위, "기준": "별도",
                     "원천": "OpenDART empSttus 접수 %s · %s" % (a["rcept"], a["규"]), "기간끝": a["끝"], "딱지": 딱지, "비고": 비고})

    for (고, y), a in 값들.items():
        넣("직원수", 고, y, a["인원"], a["인원"], None, "명", "같음", "회사 단독(별도) 기말 인원 — 모델 인원범위가 연결이면 [유추]", (1, 1e6))
        if a["급여"]:
            넣("급여총액", 고, y, a["급여"], a["급여"], None, "원", "[유추]", "회사 단독 · 급여만(퇴직급여 · 복리후생 제외)", (1e6, 1e14))
            넣("1인평균급여", 고, y, a["급여"] / a["인원"], a["급여"], a["인원"], "원", "[유추]",
               "별도 · 급여만 — 모델 503 은 연결 급여 ÷ 본사 인원(범위 환산 배수를 곱해 견준다)", (1e6, 1e9))
        b = 값들.get((고, y - 1))
        if b:
            넣("인원증가율", 고, y, a["인원"] / b["인원"] - 1.0, a["인원"], b["인원"], "비율", "같음", "본사(별도) 인원 기준", (-0.9, 5.0))
            if a["급여"] and b["급여"]:
                넣("1인평균급여증가율", 고, y, (a["급여"] / a["인원"]) / (b["급여"] / b["인원"]) - 1.0, a["급여"] / a["인원"], b["급여"] / b["인원"], "비율",
                   "같음", "성과급을 품은 급여 기준 — 모델이 성과급을 따로 세우면 [유추]", (-0.9, 3.0))
                넣("급여총액증가율", 고, y, a["급여"] / b["급여"] - 1.0, a["급여"], b["급여"], "비율", "[유추]", "인건비 증가 대조(급여만)", (-0.95, 10.0))
    뜻 = {"직원수": ("인원 합계(회사 단독 · 기말)", ["501 바탕", "7k8(인원 지표)"], "명", "같음"),
         "급여총액": ("연간 급여 총액(회사 단독 · 급여만)", ["503 · 520 바탕"], "원", "[유추]"),
         "1인평균급여": ("급여총액 ÷ 인원(회사 단독)", ["503"], "원", "[유추]"),
         "인원증가율": ("직원수(t) ÷ 직원수(t−1) − 1", ["501"], "비율", "같음"),
         "1인평균급여증가율": ("1인평균급여(t) ÷ (t−1) − 1", ["504"], "비율", "같음"),
         "급여총액증가율": ("급여총액(t) ÷ (t−1) − 1", ["520(대조)"], "비율", "[유추]")}
    낸 = {}
    목 = 공.목록읽기(뿌리)
    이 = (목.get("이어받기") or {}).get("직원현황") or {}
    for 변, 줄들 in 줄.items():
        정, 칸, 단, 딱 = 뜻[변]
        낸[변] = 공.쓰기(변, 줄들, {"정의": 정, "칸": 칸, "단위": 단, "딱지": 딱, "원천": "OpenDART 직원 현황(empSttus)", "도구": "dart_직원패널.py",
                               "원천asof": max((a["rcept"] for a in 값들.values()), default=""), "뺀_정의역밖": 뺌[변],
                               "이어받기_남은수": 이.get("남은수")}, 뿌리, 분모해)
        if not 조용:
            print("  %-12s 줄 %6d · 커버리지 %s(%s) · 정의역 밖 %d" % (변, len(줄들), 낸[변]["커버리지_전체"], 낸[변]["커버리지_창"], 뺌[변]), flush=True)
    return 낸


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="국내 직원 현황 패널(B — OpenDART empSttus · 이어받기)")
    ap.add_argument("--상한", type=int, default=10000)
    ap.add_argument("--부터", type=int, default=2015)
    ap.add_argument("--까지", type=int, default=2025)
    ap.add_argument("--짓기만", action="store_true")
    a = ap.parse_args(argv)
    if not a.짓기만:
        if not os.environ.get("OPENDART_API_KEY"):
            print("입력 오류 — 환경변수 OPENDART_API_KEY 가 없다")
            return 2
        상 = 받기(None, a.부터, a.까지, a.상한)
        print("직원현황 받기 — 부름 %d · 할 일 %d · 남음 %d · %s · %.0f초" % (상["부른수"], 상.get("할일", 0), 상.get("남은수", 0), 상["멈춘까닭"], 상.get("걸린초", 0)))
    짓기(None)
    print("→ %s" % 공.자리())
    return 0


if __name__ == "__main__":
    sys.exit(main())

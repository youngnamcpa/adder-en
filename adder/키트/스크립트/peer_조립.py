# -*- coding: utf-8 -*-
"""유사기업 재료 조립 — 베타·잔차상관·시가총액·βU·성장성을 한 표로.

왜 따로 있는가
    유사기업-선정 스킬의 `scripts/잔차상관.py` 는 **가격표 CSV 를 만들어 넘기라**고만 하고
    그 CSV 를 만드는 도구가 없었다. 그래서 회차마다 회귀·상관을 다시 구현하게 됐다.
    **회차마다 똑같이 필요한 물건이라 여기로 올린다.**

읽는 것 (전부 앞 단계 도구가 남긴 것)
    _raw/peers/sise_{종목코드}_week_*.json  회귀 창 주봉  naver_price.py --부터/--까지 · dart_peer_사슬.py
    _raw/peers/종가_{기준일}.json           평가기준일 종가  naver_price.py --일봉
    주식수.csv                              발행·자기·유통  dart_shares.py
    전체재무_추출.csv                        차입금·자본     dart_fs_all.py
    상장사_주요계정_{연도}_후보.csv           매출·이익      dart_peer_screen.py

내는 것
    유사기업_재료_{표본}.csv — 잔차상관 내림차순. **대상회사도 참고행으로 한 줄 넣는다.**
    _raw/peers/βU_{표본}.json — βU·**현금보정**·세 방식(핵심·전체, 보정 전·후). 미국 `peer_βU_us.py` 와 같은 모양

**산출 이름은 표본마다 갈린다(2026-09-13 · L4a 세14 와 같은 처방).** 옛 판은 명단이 무엇이든
`유사기업_재료.csv` 에 써서 CP3(넓은 표본) 조립이 CP2(핵심+예비)를 덮을 수 있었다. `--표본`(기본: 명단
파일 이름)을 붙이고, 같은 표본 이름에 다른 명단·기준일의 βU 산출이 있으면 **덮지 않고 멈춘다.**
옛 이름이 필요하면 `--out 유사기업_재료.csv`.

**현금보정·세 방식.** 옛 판은 현금 칸만 있고 보정·세 방식이 없어 3단계가 손으로 해야 했다 —
미국 회차에서 그 자리가 통째로 빠져 주당가치가 3% 움직였다(세일즈포스). 식은 `현금보정.보정`·
`peer_βU_us.세방식` 을 **그대로 불러 쓴다**(두 조립기의 규약이 갈리지 않게). 현금 = 현금및현금성자산
+ 단기투자(`dart_fs_all.py` 의 단기투자 칸), 기업가치 = 시가총액 + D.

**잡음 문턱을 같이 낸다.** 표본 n 주에서 상관의 표준오차는 대략 1/√n 이고 그 두 배를
밑도는 잔차상관은 0과 구별되지 않는다. 「상위 N곳」으로 수를 맞추기 전에 **문턱을 넘는
후보가 몇 곳인지** 보아야 한다 — 작은 회사에서는 그 수가 자르려는 수보다 적어서,
그대로 자르면 잡음으로 순위를 매기게 된다.

무차입화 세율은 **이 표의 참고값**이다. 3단계가 확정한 세율로 다시 계산한다.

**시장지수 — 본값은 그 나라 넓은 시장 지수다(2026-10-17, S7-05 — 기본 `--지수 넓은` = KOSPI).** 베타는 ERP 를 곱하는
「시장 포트폴리오」 대비여야 하는데 KOSDAQ 은 성장 · 기술주에 쏠린 좁은 지수라 눈금이 다르다(실측 펄어비스 핵심 여섯:
KOSDAQ 회귀 βU 0.846 · KOSPI 회귀 0.645). 그래서 전원을 KOSPI 로 회귀해 본값을 내고, **상장시장 지수(KOSDAQ)로 잰 값은 대안 사양으로
병기한다**(칸 `베타_상장지수` · 요약 `대안_상장지수`). 아래 「자동」 은 종전 기본(회사별 상장시장)이다 — 대안 사양을 본값으로 쓰려면 사람이 지시한다.
**옛 기본(펄29, `--지수 자동`) — 회사마다 상장시장을 따른다.** 옛 판은 지수를 하나만
받아 KOSPI·KOSDAQ 가 섞인 표본을 **두 번 돌려 손으로 이었다**(펄어비스 회차: 유사기업_재료.csv
·유사기업_재료_KOSPI회귀.csv 두 벌). 한 번 돌리면 한쪽 시장 회사가 **틀린 지수로 회귀된 채**
표에 섞인다 — 실측 더블유게임즈(유가) βL: KOSPI 0.196 · KOSDAQ 0.345.
    시장 확인 순서  명단의 「시장」 칸 → _raw/peers/company/{고유번호}.json corp_cls(Y 유가·K 코스닥)
                    → 산업분류.csv·산업분류_전수.csv 상장구분 → _dartcache/상장명부_KIND.csv 시장
    못 찾으면       회귀하지 않고 「시장 확인 불가」로 비운다 — KOSPI 를 자동으로 붙이지 않는다
    잔차상관        짝마다 **후보의 지수 위에서** 후보 잔차 × 대상 잔차(회차 선례). 시장이 섞이면 표 아래에 적는다
    `--지수 KOSPI|KOSDAQ` 를 주면 옛 동작(전원 한 지수)이고, 시장이 다른 회사를 경보로 센다.
수익률은 **날짜로 짝짓는다** — 주봉 파일 길이·라벨이 달라도 위치로 어긋나지 않는다.

**회귀 창 = 기준일 − `--창년`(기본 5년 · 주간) ~ 기준일 (2026-10-16 결정).** 주봉 파일은 가장 긴 것을
고르므로, 더 긴 캐시(다른 회차의 10년 창 등)가 있으면 창이 조용히 늘어난다 — 창 시작 앞의 주를 자르고 회사마다
실제 주 수(`표본주`)를 적는다. `--부터 YYYYMMDD` 를 주면 그 날이 창 시작이다(사슬과 같은 값).

**`목적`(2026-10-16 · 결정 5).** 명단(`--후보`)이 C1 `핵심표본.json` 꼴이어도 읽는다(핵심 · 예비 · 운영 동종 전용).
`목적` 을 선언했는데 「위험동종」이 없는 회사(운영 동종 전용)는 βU 표본이 아니므로 회귀 · 표에서 빼고 화면에 적는다.
`핵심표본.json` 의 `B1도착` · `보강[]` 은 βU 산출 머리의 `표본판` 에 옮겨 적는다(어느 판의 표본인지).

**전체재무_추출.csv 가 병합판(연도·보고서 칸)이면** 회사마다 가장 최근 (연도, 보고서) 행을
쓴다(`--재무연도`·`--재무보고서` 로 고정). 쓴 행을 `재무기준` 칸에 적는다.

**본값 규칙(2026-10-17, S7-03 · 06 · 07 · 17 — `βU본값.py` 가 정본, 미국 · 병합 조립기와 같다).**
    · 본값에서 빼는 회사 — 차입금 확인필요(★) · 차입 미포착(D ÷ 부채총계 < 5% · 부채 ÷ 자산 > 50%) · 시가총액 없음 · 현금비중 ≥ 50% ·
      결정계수 < 0.10 · 표본 < 156주. 빼도 표에서 지우지 않고 「포함 시 값」을 나란히 낸다
    · **회사별 세율** — 국내 회사는 직전 사업연도 영업이익을 과세표준 근사로 법령 세율표(`한계세율.py`)의 구간 세율(지방소득세 포함).
      영업이익이 0 이하이거나 표가 없으면 `--세율`. `--세율고정` 이면 전원 `--세율`(옛 동작)
    · **D/E · 현금은 회귀 창 기말 점 평균이 1차** — `전체재무_추출.csv` 에 창 안 연도(사업보고서 11011)가 있으면 그 기말마다
      D ÷ (시가총액 × 주봉 종가비)로 낸다(주식수는 기준일 고정 근사 — 적는다). `dart_peer_사슬.py` 가 창 안 사업보고서를 함께 받는다(기본)
    · D/E ≥ 2 면 부채베타 βD = 스프레드 ÷ ERP(시장데이터 캐시 KR). **스프레드는 회사마다 합성등급이 기본**(2026-10-25 FX3-b —
      영업이익 ÷ 이자비용 → 다모다란 등급표 · 이자비용은 `전체재무_추출.csv` 의 `이자비용` 칸, 없으면 `_raw/peers/fs/` 캐시 원문).
      못 세우면 `--부채스프레드`, 그것도 없으면 하마다로 두고 적는다(βU본값 ⑧ — 본값에서 빠진다)
    · **국내 차입금 주석 확정**(2026-10-25 FX3-b) — `C2_차입금_확정.json`(별칭 `C2_차입금_확정_국내.json` · `차입금_확정.json` · `--차입확정`)
      을 `전체재무_추출.csv` 위에 덮어 읽는다. 키 = 고유번호(8자리) → 「연도 보고서」 → {"D", "근거"} — 손으로 CSV 를 고치지 않는다
    · **거래 정지 구간**(2026-10-25 FX3-b) — 1년 일봉 연속 무거래 ≥ 3일 · 연속 무수익 주 ≥ 2주를 정지로 보고 유동성 비율과 회귀 창에서
      뺀다(재개 첫 주 — 분할 기준가 불연속 — 도 뺀다). 원래 비율은 `…_원`
    · **세 겹 제한**(2026-10-25 FX3-b) — 대상 자체 βU 를 점검값에서 빼는 경우(지주형 · 연결 지주 · 캡티브 금융 · 본값 제외 사유)와
      부문 가중을 기본값으로 쓰지 않는 경우(비중 큰 약한 슬롯) — `βU본값.대상자체판정` · `부문가중` · `세겹`. 신호는 대상 재무 캐시 ·
      A3 `_raw/동인원천.json` · 핵심표본 · `--대상신호` 에서
    · `--대상` 을 종목코드 한 칸만 주면 고유번호 · 이름을 캐시(주식수 · C1 공용 · corpCode)로 푼다
    · βL 표준오차 · 중앙값 부트스트랩 95% 구간 · 3년 창 대안(`베타_3년`) · 상장시장 지수 대안 · 다모다란 산업 βU 대조(대상 매핑 줄 —
      ±30% 밖이면 ★) · 사이클 회사면 회귀 창이 저점 국면 해를 품는지(`--국면`, 기본 `_raw/동인원천.json`)

사용
    python 스크립트/peer_조립.py --기준일 20260630 --대상 011230,00129280,삼화전자공업 --세율 0.264
    python 스크립트/peer_조립.py --기준일 20260630 --대상 ... --지수 자동 --세율 0.209    # 회사별 상장시장 지수(옛 기본)
    python 스크립트/peer_조립.py --기준일 20260630 --대상 ... --지수 KOSDAQ --세율 0.209   # 전원 고정(옛 동작)
"""
from __future__ import annotations

import argparse
import csv
import glob
import io
import json
import math
import os
import re
import sys
from datetime import datetime as _dt, timedelta as _td

# 2026-10-25 FX4-P — 본체 경로로 돌려도 회차에 쓰게 `--폴더`(또는 환경변수 DCF_RUN_ROOT — 사슬이 하위 도구에 넘긴다). 없으면 스크립트의 부모
ROOT = os.environ.get("DCF_RUN_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEER = os.path.join(ROOT, "_raw", "peers")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── 현금보정·세 방식은 미국 조립기와 **같은 규약**을 쓴다(2026-09-13 · L4a 요청) ──────────
# `현금보정.보정` · `peer_βU_us.세방식` 을 그대로 불러 쓴다 — 식을 여기서 다시 짜면 두 판이 갈린다.
# 두 파일은 L4a 소유라 여기서 고치지 않는다. 못 읽으면(시험용 복사 폴더 등) 같은 식의 사본으로
# 돌고 그 사실을 산출 머리에 적는다.
try:
    from 현금보정 import 보정                                    # noqa: E402
    _보정출처 = "현금보정.보정"
except Exception:                                               # noqa: BLE001
    def 보정(βU, 비중):
        if βU is None or 비중 is None or 비중 >= 1:
            return None
        return βU / (1 - 비중)
    _보정출처 = "사본(현금보정.py 를 못 읽음 — 같은 식)"
try:
    from peer_βU_us import 세방식                                # noqa: E402
    _세방식출처 = "peer_βU_us.세방식"
except Exception:                                               # noqa: BLE001
    import statistics as _st

    def 세방식(행들, 세율, 키="βU", 비중키=None):
        ok = [z for z in 행들 if z.get(키) is not None]
        if not ok:
            return {"표본수": 0}
        v = [z[키] for z in ok]
        a = _st.mean(z["βL"] for z in ok) / (1 + (1 - 세율) * _st.mean(z["DE"] for z in ok))
        if 비중키:
            a = a / (1 - _st.mean(z[비중키] for z in ok))
        b, c = _st.median(v), _st.mean(v)
        순 = sorted(ok, key=lambda z: z[키])
        out = {"표본수": len(v), "(a)평균합산": a, "(b)개별중앙값_기본": b, "(c)개별평균": c,
               "최소": min(v), "최대": max(v), "티커": [z["티커"] for z in ok],
               "아래둘": [(z["티커"], round(z[키], 4)) for z in 순[:2]],
               "위둘": [(z["티커"], round(z[키], 4)) for z in 순[-2:]],
               "세값폭": max(a, b, c) - min(a, b, c)}
        out["세값_0.01안"] = out["세값폭"] <= 0.01
        return out
    _세방식출처 = "사본(peer_βU_us.py 를 못 읽음 — 같은 식)"


def 읽자(p, enc="utf-8"):
    return json.load(io.open(p, encoding=enc))


창시작 = ""          # main() 이 기준일 − 창년(또는 --부터)으로 채운다 — 이 날 앞의 주는 쓰지 않는다


def 주봉(code, 기준일):
    """창 시작 ~ 평가기준일 안의 주가 가장 많은 주봉 파일을 골라 그 창으로 자른다. 1.1.2(P10) — 종전에는 파일 전체 길이로 골라 길이가 같으면
    이름순 첫 파일(옛 창)이 골라져 기준일을 옮겨도 창 끝이 옛 기준일에 머물렀다. 창 안 주 수가 같으면 기준일에 가장 가까운 마지막 주의 파일."""
    후보 = sorted(glob.glob(os.path.join(PEER, "sise_%s_week_*.json" % code)))
    if not 후보:
        return None
    best, 열쇠 = None, None
    for p in 후보:
        rows = 읽자(p) or []
        안 = [(d, v) for d, v in rows if 창시작 <= d <= 기준일]
        k = (len(안), max((d for d, _v in 안), default=""))
        if 열쇠 is None or k > 열쇠:
            best, 열쇠 = 안, k
    return best


def _정지문턱():
    try:
        import βU본값 as _b
        return _b.문턱.get("정지연속일", 3), _b.문턱.get("정지연속주", 3)
    except Exception:                                           # noqa: BLE001
        return 3, 3


def 정지구간(rows, 연속):
    """1년 일봉 [날짜, 종가, 거래량] → 연속 무거래가 `연속` 일 이상인 구간 [(시작, 끝, 일수)] — 거래 정지(인적분할 · 합병 등)로 본다
    (2026-10-25 FX3-b · 셀트리온 표본의 대형 동종이 인적분할 정지로 「얇은 거래」 가 되어 본값에서 빠졌다)."""
    out, 시작, 끝, n = [], None, None, 0
    for r in rows:
        if not r[2]:
            시작 = 시작 or str(r[0])
            끝, n = str(r[0]), n + 1
        else:
            if n >= 연속:
                out.append((시작, 끝, n))
            시작, 끝, n = None, None, 0
    if n >= 연속:
        out.append((시작, 끝, n))
    return out


def _날(d):
    return _dt.strptime(str(d).replace("-", "")[:8], "%Y%m%d")


def 정지주(수익, 일구간, 연속주):
    """주간 수익 {날짜: 수익} → (회귀에서 뺄 주 set, 일봉으로 확인한 정지 주 set, 주간 정지 의심 구간 [(시작, 끝, 주수)]).
    연속 무수익 주가 `연속주` 이상이면 그 주들과 다음 주(재개 첫 주 — 분할 기준가 불연속)를, 일봉 정지 구간에 걸친 주(끝 + 7일까지)와
    그다음 주를 회귀에서 뺀다. **무거래 비율에서는 일봉으로 확인한 정지 주만 뺀다** — 주간 무수익 연속만으로 빼면 얇은 거래 회사가
    유동성 잣대를 빠져나간다."""
    날들 = sorted(수익)
    뺄, 일뺄, 주구간 = set(), set(), []
    i = 0
    while i < len(날들):
        if 수익[날들[i]] == 0.0:
            j = i
            while j < len(날들) and 수익[날들[j]] == 0.0:
                j += 1
            if j - i >= 연속주:
                뺄.update(날들[i:j])
                주구간.append((날들[i], 날들[j - 1], j - i))
                if j < len(날들):
                    뺄.add(날들[j])
            i = j
        else:
            i += 1
    for 시작, 끝, _n in 일구간 or []:
        s, e = _날(시작), _날(끝) + _td(days=7)
        걸린 = [d for d in 날들 if s <= _날(d) <= e]
        뺄.update(걸린)
        일뺄.update(걸린)
        뒤 = [d for d in 날들 if _날(d) > e]
        if 걸린 and 뒤:
            뺄.add(뒤[0])
            일뺄.add(뒤[0])
    return 뺄, 일뺄, 주구간


def 일봉유동성(code, 기준일):
    """1년 일봉(거래 두께 — 사슬이 받는 `vol_{코드}_day_*.json` · [날짜, 종가, 거래량])의 기준일까지 → 거래량 0 인 날 비율 · 일평균 거래대금(억).
    가장 긴 판을 쓴다. 파일이 없으면 빈 dict — 그러면 βU본값 ⑦ 의 일봉 문턱이 서지 않는다(2026-10-25 C1 규모).
    2026-10-25 FX3-b — 연속 무거래 구간(거래 정지)은 비율의 분자 · 분모에서 빼고 `정지구간` 에 적는다(원래 비율은 `무거래일비율_원`)."""
    best = None
    for p in sorted(glob.glob(os.path.join(PEER, "vol_%s_day_*.json" % code))):
        try:
            rows = 읽자(p)
        except (ValueError, OSError):
            continue
        if isinstance(rows, list) and (best is None or len(rows) > len(best)):
            best = rows
    rows = [r for r in (best or []) if isinstance(r, (list, tuple)) and len(r) >= 3 and str(r[0]) <= 기준일]
    if not rows:
        return {}
    연속일, _ = _정지문턱()
    구 = 정지구간(rows, 연속일)
    정지날 = {str(r[0]) for r in rows for s, e, _n in 구 if s <= str(r[0]) <= e}
    남 = [r for r in rows if str(r[0]) not in 정지날]
    영원 = sum(1 for r in rows if not r[2])
    영 = sum(1 for r in 남 if not r[2])
    대금 = sum(float(r[1]) * float(r[2]) for r in 남 if r[1] and r[2])
    return {"무거래일비율": (영 / len(남)) if 남 else None, "무거래일비율_원": 영원 / len(rows), "정지구간": 구,
            "일평균거래대금_억": (대금 / len(남) / 1e8) if 남 else None, "일봉일수": len(rows)}


_전용키 = ("운영동종전용", "운영동종_전용", "운영 동종 전용", "운영전용")


def 목적목록(x):
    v = x.get("목적") if isinstance(x, dict) else None
    if v is None:
        return None
    if isinstance(v, str):
        import re as _re
        v = _re.split(r"[,·/|]", v)
    return [str(t).replace(" ", "") for t in v]


def 운영전용(x):
    """목적을 선언했는데 「위험동종」이 없다 — βU 표본이 아니다."""
    v = 목적목록(x)
    return v is not None and "위험동종" not in v


def 후보펼치기(j):
    """목록 · {"행"} · C1 핵심표본(핵심 · 예비 · 운영 동종 전용) → 목록. 모르는 칸은 버리지 않고 쓰지 않을 뿐이다."""
    if isinstance(j, list):
        return j
    if any(k in j for k in ("핵심", "예비") + _전용키):
        out, 본 = [], set()
        묶음 = ([("핵심", j.get("핵심") or [])] + [("운영동종전용", j.get(k) or []) for k in _전용키]
              + [("예비", j.get("예비") or [])])
        for 이름, 목록 in 묶음:
            for x in 목록:
                c = str(x.get("종목코드") or "")
                if c and c not in 본:
                    본.add(c)
                    x = dict(x)
                    x.setdefault("왜", 이름)
                    out.append(x)
        return out
    return j.get("행") or []


def 로그수익(vals):
    return [math.log(b / a) if (a and b and a > 0 and b > 0) else None
            for a, b in zip(vals, vals[1:])]


def 회귀(y, x):
    쌍 = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
    n = len(쌍)
    if n < 3:
        return None, None, None, n
    ax = sum(a for a, _ in 쌍) / n
    ay = sum(b for _, b in 쌍) / n
    sxx = sum((a - ax) ** 2 for a, _ in 쌍)
    sxy = sum((a - ax) * (b - ay) for a, b in 쌍)
    syy = sum((b - ay) ** 2 for _, b in 쌍)
    if sxx == 0:
        return None, None, None, n
    beta = sxy / sxx
    alpha = ay - beta * ax
    r2 = (sxy ** 2) / (sxx * syy) if syy else None
    잔차 = [None if (a is None or b is None) else b - (alpha + beta * a)
          for a, b in zip(x, y)]
    return beta, r2, 잔차, n


def 상관(a, b):
    쌍 = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    n = len(쌍)
    if n < 3:
        return None, n
    ax = sum(x for x, _ in 쌍) / n
    ay = sum(y for _, y in 쌍) / n
    좌 = math.sqrt(sum((x - ax) ** 2 for x, _ in 쌍))
    우 = math.sqrt(sum((y - ay) ** 2 for _, y in 쌍))
    if 좌 == 0 or 우 == 0:
        return None, n
    return sum((x - ax) * (y - ay) for x, y in 쌍) / (좌 * 우), n


def 표읽기(name, key="고유번호"):
    p = os.path.join(ROOT, name)
    if not os.path.exists(p):
        return {}
    return {r[key]: r for r in csv.DictReader(io.open(p, encoding="utf-8-sig"))}


# ── 날짜로 짝짓는 수익률·회귀 (시장이 섞여도 위치로 어긋나지 않게) ─────────────
def 수익표(rows):
    """[(날짜, 종가)] → {끝날짜: 로그수익}."""
    out = {}
    for (d0, a), (d1, b) in zip(rows, rows[1:]):
        if a and b and a > 0 and b > 0:
            out[d1] = math.log(b / a)
    return out


def 회귀표(y, x):
    """y·x 는 {날짜: 수익}. (β, R², 잔차표, n)."""
    공통 = sorted(set(y) & set(x))
    if len(공통) < 3:
        return None, None, None, len(공통)
    b, r2, 잔차, n = 회귀([y[d] for d in 공통], [x[d] for d in 공통])
    if 잔차 is None:
        return None, None, None, n
    return b, r2, dict(zip(공통, 잔차)), n


def 상관표(a, b):
    공통 = sorted(set(a) & set(b))
    return 상관([a[d] for d in 공통], [b[d] for d in 공통])


_시장이름 = {"Y": "KOSPI", "K": "KOSDAQ", "N": "KONEX", "유가": "KOSPI", "유가증권": "KOSPI",
          "유가증권시장": "KOSPI", "코스피": "KOSPI", "KOSPI": "KOSPI", "코스닥": "KOSDAQ",
          "KOSDAQ": "KOSDAQ", "코넥스": "KONEX", "KONEX": "KONEX"}


def 시장지도(root=None):
    """(고유번호→(시장, 근거), 종목코드→(시장, 근거)) — 캐시만 읽는다."""
    root = root or ROOT
    고, 종 = {}, {}
    for p in sorted(glob.glob(os.path.join(root, "_raw", "peers", "company", "*.json"))):
        try:
            j = 읽자(p)
        except (ValueError, OSError):
            continue
        m = _시장이름.get(str(j.get("corp_cls") or "").strip())
        if m:
            근거 = "기업개황 corp_cls=%s" % j.get("corp_cls")
            if j.get("corp_code"):
                고.setdefault(str(j["corp_code"]).zfill(8), (m, 근거))
            if j.get("stock_code"):
                종.setdefault(str(j["stock_code"]).zfill(6), (m, 근거))
    for 이름 in ("산업분류.csv", "산업분류_전수.csv"):
        p = os.path.join(root, 이름)
        if os.path.exists(p):
            for r in csv.DictReader(io.open(p, encoding="utf-8-sig")):
                m = _시장이름.get(str(r.get("상장구분") or "").strip())
                if m:
                    if r.get("고유번호"):
                        고.setdefault(r["고유번호"].zfill(8), (m, "%s 상장구분" % 이름))
                    if r.get("종목코드"):
                        종.setdefault(r["종목코드"].zfill(6), (m, "%s 상장구분" % 이름))
    p = os.path.join(root, "_dartcache", "상장명부_KIND.csv")
    if os.path.exists(p):
        for r in csv.DictReader(io.open(p, encoding="utf-8-sig")):
            m = _시장이름.get(str(r.get("시장") or "").strip())
            if m and r.get("종목코드"):
                종.setdefault(r["종목코드"].zfill(6), (m, "KIND 상장명부"))
    return 고, 종


def 시장해석(행, 고, 종):
    """명단 칸 → 기업개황 → 산업분류 → KIND. 못 찾으면 (None, 사유)."""
    m = _시장이름.get(str(행.get("시장") or "").strip())
    if m:
        return m, "명단 시장=%s" % 행.get("시장")
    corp = str(행.get("고유번호") or "").zfill(8)
    if corp in 고:
        return 고[corp]
    code = str(행.get("종목코드") or "").zfill(6)
    if code in 종:
        return 종[code]
    return None, "시장 확인 불가 — 명단·기업개황·산업분류·KIND 캐시에 없음"


_보고서순 = {"11013": 1, "11012": 2, "11014": 3, "11011": 4}


def 재무읽기(연도=None, 보고서=None):
    """전체재무_추출.csv → {고유번호: 행}. 병합판이면 회사마다 가장 최근 (연도, 보고서)."""
    p = os.path.join(ROOT, "전체재무_추출.csv")
    if not os.path.exists(p):
        return {}
    고른 = {}
    for r in csv.DictReader(io.open(p, encoding="utf-8-sig")):
        c = str(r.get("고유번호") or "").zfill(8)
        y, rp = str(r.get("연도") or ""), str(r.get("보고서") or "")
        if 연도 and y and y != str(연도):
            continue
        if 보고서 and rp and rp != str(보고서):
            continue
        키 = (y, _보고서순.get(rp, 0))
        if c not in 고른 or 키 >= 고른[c][0]:
            고른[c] = (키, r)
    out = {}
    for c, (_, r) in 고른.items():
        r = dict(r)
        r["재무기준"] = ("%s %s" % (r.get("연도"), r.get("보고서"))) if r.get("연도") else "연도 미기재(옛 판)"
        out[c] = r
        out[r.get("고유번호", c)] = r
    return out


def _n(v):
    try:
        return float(str(v).replace(",", ""))
    except (ValueError, TypeError):
        return None


_보고서끝월 = {"11011": "1231", "11012": "0630", "11013": "0331", "11014": "0930"}


def _보고서끝(fr):
    """전체재무_추출.csv 행의 재무상태표 날짜(YYYYMMDD) — 12월 결산 가정(연도 + 보고서 코드). 모르면 None."""
    y, rp = str(fr.get("연도") or ""), str(fr.get("보고서") or "")
    return (y + _보고서끝월[rp]) if (len(y) == 4 and rp in _보고서끝월) else None


def 재무전부읽기():
    """전체재무_추출.csv → {고유번호: [행 …]} — 회귀 창 기말 점(S7-06)의 재료. 병합판(연도 · 보고서)만 쓸모 있다."""
    p = os.path.join(ROOT, "전체재무_추출.csv")
    out = {}
    if not os.path.exists(p):
        return out
    for r in csv.DictReader(io.open(p, encoding="utf-8-sig")):
        out.setdefault(str(r.get("고유번호") or "").zfill(8), []).append(r)
    return out


# ── 2026-10-25 FX3-b — 국내 차입금 주석 확정(덮어쓰기) · 합성등급 부채 스프레드 · 대상 신호 ─────────────────────────
_차입확정이름 = ("C2_차입금_확정.json", "C2_차입금_확정_국내.json", "차입금_확정.json")
_고유8 = re.compile(r"(?<!\d)(\d{8})(?!\d)")
_연보 = re.compile(r"(20\d\d)\D{0,3}(1101[1-4])")


def _확정값(v):
    if not isinstance(v, dict):
        return None, ""
    for k in ("D", "차입금", "차입금_확정", "확정D"):
        x = v.get(k)
        if isinstance(x, (int, float)) and not isinstance(x, bool):
            return float(x), str(v.get("근거") or v.get("판정") or "")
    return None, ""


def 차입확정읽기(경로들):
    """국내 차입금 주석 확정 파일 → {고유번호: {(연도, 보고서) 또는 None: {"D", "근거", "파일"}}}.

    정본 꼴은 {"고유번호": {"연도 보고서": {"D", "근거"}}}. 회차마다 손으로 쓴 꼴이 달라(C1 다시 돌리기 실측) 넷을 받는다 —
    ① 정본 ② {"고유번호 연도 보고서": {...}} ③ {"회사(… · 고유번호)": {"연도 보고서": {...}}} ④ {"회사": "…(… · 고유번호)", "근거",
    "확정": [{"연도", "보고서", "차입금_확정"}]}. 키에 고유번호(8자리)가 없는 항목(미국 꼴 — 티커)은 건너뛴다."""
    out = {}

    def 넣(고, 연보, D, 근, 파일):
        if 고 and D is not None:
            out.setdefault(고, {})[연보] = {"D": D, "근거": 근, "파일": 파일}
    for p in 경로들:
        try:
            j = 읽자(p)
        except (OSError, ValueError):
            continue
        if not isinstance(j, dict):
            continue
        파일 = os.path.basename(p)
        if isinstance(j.get("확정"), list):
            m = _고유8.search(str(j.get("회사") or ""))
            for x in j["확정"]:
                D, _근 = _확정값(x)
                연보 = (str(x.get("연도")), str(x.get("보고서"))) if (x.get("연도") and x.get("보고서")) else None
                넣(m.group(1) if m else None, 연보, D, str(x.get("근거") or j.get("근거") or ""), 파일)
            continue
        for k, v in j.items():
            m = _고유8.search(str(k))
            if not m or not isinstance(v, dict):
                continue
            ky = _연보.search(str(k))
            D, 근 = _확정값(v)
            if D is not None:
                넣(m.group(1), (ky.group(1), ky.group(2)) if ky else None, D, 근, 파일)
                continue
            for k2, v2 in v.items():
                D2, 근2 = _확정값(v2)
                ky2 = _연보.search(str(k2))
                if D2 is not None:
                    넣(m.group(1), (ky2.group(1), ky2.group(2)) if ky2 else None, D2, 근2, 파일)
    return out


def 확정덮기(재무, 재무전부, 확정):
    """확정 D 를 재무(회사마다 쓰는 행) · 재무전부(창 안 행)에 덮는다 — D판정 · D근거를 남기고 차입금_확인필요를 지운다. → 덮은 행 수."""
    n = 0

    def 덮(행, x):
        행["차입금합계"], 행["차입금_확인필요"] = x["D"], ""
        행["D판정"], 행["D근거"] = "확정(%s)" % x["파일"], x["근거"]
    for 고, 판 in 확정.items():
        for 행 in 재무전부.get(고, []):
            x = 판.get((str(행.get("연도") or ""), str(행.get("보고서") or "")))
            if x is not None:
                덮(행, x)
                n += 1
        행 = 재무.get(고)
        if 행 is not None:
            x = 판.get((str(행.get("연도") or ""), str(행.get("보고서") or ""))) or 판.get(None)
            if x is None:
                # 2026-10-25 FX4-P — 쓰는 행(기준일 반기 · 분기)에 맞는 확정이 없고 같은 회사의 사업보고서 확정만 있으면(주석은 사업보고서에 있다),
                # 가장 늦은 사업보고서 확정값을 「대용(직전 사업보고서)」 표지와 함께 쓴다 — 종전에는 덮지 못해 「차입금 미확정(주석 큐)」 이 그대로 남았고
                # 회차마다 손으로 「대용(현재 행)」 키를 더했다(C2 다시 셈 3-2 · 4-7). 확정의 해가 쓰는 행보다 앞서면 경보에 이름을 남긴다
                사업 = sorted(k for k in 판 if isinstance(k, tuple) and k[1] == "11011")
                if 사업:
                    x0 = 판[사업[-1]]
                    x = dict(x0, 근거="대용(직전 사업보고서 %s 확정 — 쓰는 행 %s %s) · %s" % (
                        사업[-1][0], 행.get("연도"), 행.get("보고서"), x0.get("근거") or ""), 파일=x0["파일"] + " · 대용")
                    _대용경보.append("%s — 확정은 %s 사업보고서 · 쓰는 행은 %s %s(대용으로 덮음 — 반기 주석으로 확정하면 바뀐다)" % (
                        고, 사업[-1][0], 행.get("연도"), 행.get("보고서")))
            if x is not None:
                덮(행, x)
                n += 1
    return n


_대용경보 = []                                                # 확정덮기가 대용으로 덮은 회사(화면 · 산출 머리)


def _명단정규(n):
    """산출 머리의 명단 이름 비교 — 사슬이 만든 `_사슬명단_X.json` 과 그 원본 `X.json` 은 같은 명단이다(2026-10-25 FX4-P · C2 다시 셈 3-10)."""
    n = os.path.splitext(os.path.basename(str(n or "")))[0]
    return n[len("_사슬명단_"):] if n.startswith("_사슬명단_") else n


def 대상차입확정(t고유, 연도=None, 보고서=None):
    """대상의 이자부부채 D → (D, 근거, 재무행) · 못 세우면 (None, 까닭, None) (2026-10-25 FX4-P — C2 다시 셈 3-3).

    유사기업 차입 큐 잣대(전체재무_추출 · 주석 큐)로 대상 자체 βU 를 빼던 결함 — 대상의 D 는 대상 공시로 세운다. 차례:
    ① A3 `_raw/동인원천.json` 재무시계열의 기준일 기간 「차입금」 · 「이자부부채」 칸(있으면 — A3 가 정본)
    ② 회차 원천의 대상 공시 재무제표 `_raw/dart_재무_{연결|별도}_{연도}_{보고서}.json` 을 `dart_fs_all.뽑기` 로 — 확인 필요가 서지 않을 때만.
    확인 필요가 서면(금융부채 뭉침 · 리스만) 세우지 않고 까닭을 돌려준다 — 대상 반기 주석으로 `C2_차입금_확정.json` 에 대상 고유번호로 적는다."""
    p = os.path.join(ROOT, "_raw", "동인원천.json")
    if os.path.exists(p):
        try:
            A3 = 읽자(p)
            시 = A3.get("재무시계열") or {}
            기 = sorted(k for k in 시 if isinstance(시.get(k), dict))
            for k in reversed(기):
                for 칸 in ("이자부부채", "차입금"):
                    v = 시[k].get(칸)
                    if isinstance(v, (int, float)) and not isinstance(v, bool):
                        배 = float(A3.get("단위배수") or 1.0) if isinstance(A3.get("단위배수"), (int, float)) else 1.0
                        return v * 배, "A3 동인원천 재무시계열 %s 「%s」" % (k, 칸), None
        except (OSError, ValueError):
            pass
    try:
        import dart_fs_all as _fsa
    except ImportError:                                     # 도구만 옮겨 쓴 자리(시험) — 대상 공시로 세우지 못한다
        return None, "dart_fs_all.py 없음 — 대상 공시로 세우지 못함", None
    후보 = []
    for 구 in ("연결", "별도"):
        if 연도 and 보고서:
            후보.append(os.path.join(ROOT, "_raw", "dart_재무_%s_%s_%s.json" % (구, 연도, 보고서)))
        후보 += sorted(glob.glob(os.path.join(ROOT, "_raw", "dart_재무_%s_*_*.json" % 구)), reverse=True)
    for q in dict.fromkeys(후보):
        if not os.path.exists(q):
            continue
        try:
            j = 읽자(q)
        except (OSError, ValueError):
            continue
        if (j or {}).get("status") not in (None, "000"):
            continue
        m = re.search(r"dart_재무_(연결|별도)_(\d{4})_(\d{5})\.json$", q)
        rp = m.group(3) if m else (보고서 or "11011")
        v = _fsa.뽑기(j, "CFS" if (m and m.group(1) == "연결") else "OFS", rp)
        if v.get("차입금_확인필요"):
            return None, "대상 공시 %s — %s" % (os.path.basename(q), v["차입금_확인필요"] if isinstance(v["차입금_확인필요"], str) else "차입금 0(이름을 못 찾았을 수 있다)"), None
        행 = {"고유번호": str(t고유).zfill(8), "연도": m.group(2) if m else 연도, "보고서": rp, "쓴구분": "CFS" if (m and m.group(1) == "연결") else "OFS",
             "자산총계": v.get("자산총계"), "부채총계": v.get("부채총계"), "자본총계": v.get("자본총계"),
             "현금및현금성자산": v.get("현금및현금성자산"), "단기투자": v.get("단기투자"), "영업이익": v.get("영업이익"),
             "매출액": v.get("매출액"), "계약부채선수금": v.get("계약부채선수금"), "예수정산부채": v.get("예수정산부채"),
             "이자비용": v.get("이자비용") if v.get("이자비용") is not None else "", "이자비용근거": v.get("이자비용근거") or "",
             "차입금합계": v["차입금합계"], "차입금_확인필요": "", "차입금항목": "; ".join("%s=%s" % (x["계정"], x["금액"]) for x in v["차입금항목"])}
        행["재무기준"] = "%s %s" % (행["연도"], rp)
        return v["차입금합계"], "대상 공시 재무상태표 %s(%s)" % (os.path.basename(q), 행["차입금항목"][:120] or "차입 계정 없음"), 행
    return None, "대상 공시 재무제표 원천(`_raw/dart_재무_*`)이 없다", None


def 공용C1뿌리():
    return os.path.join(os.environ.get("DCF_공용캐시") or os.environ.get("DCF_SHARED_CACHE")
                        or os.path.join(os.path.expanduser("~"), ".dcf캐시"), "C1")


def 대상풀기(종목, 고유="", 이름=""):
    """`--대상` 이 종목코드 한 칸이면 고유번호 · 이름을 캐시에서 푼다(2026-10-25 FX3-b — 한 칸이면 대상 자체 βU 가 「시가총액 없음」 으로
    빠지던 결함). 주식수.csv 는 종목코드가 없어 C1 공용 캐시(상장사 주요계정 · 상장명부) → `_dartcache/corpCode.xml` 차례. → (고유, 이름, 근거)"""
    종목 = str(종목).zfill(6)
    for p in sorted(glob.glob(os.path.join(공용C1뿌리(), "상장사_주요계정_*.csv")), reverse=True):
        try:
            for r in csv.DictReader(io.open(p, encoding="utf-8-sig")):
                if str(r.get("종목코드") or "").zfill(6) == 종목:
                    return (고유 or str(r.get("고유번호") or "").zfill(8)), (이름 or r.get("회사명") or 종목), "C1 공용 캐시 %s" % os.path.basename(p)
        except OSError:
            continue
    p = os.path.join(ROOT, "_dartcache", "corpCode.xml")
    if os.path.exists(p):
        try:
            import xml.etree.ElementTree as ET
            for e in ET.parse(p).getroot().iter("list"):
                if (e.findtext("stock_code") or "").strip() == 종목:
                    return (고유 or (e.findtext("corp_code") or "").strip()), (이름 or (e.findtext("corp_name") or "").strip()), "corpCode.xml"
        except Exception:                                   # noqa: BLE001
            pass
    return 고유, 이름, "못 풂 — `--대상 종목,고유번호,이름` 셋을 주십시오(대상 자체 βU 를 세울 수 없다)"


def _fs캐시(고유, 연도, 보고서, 쓴구분=None):
    for 구 in ([쓴구분] if 쓴구분 else []) + ["CFS", "OFS"]:
        p = os.path.join(PEER, "fs", "%s_%s_%s_%s.json" % (str(고유).zfill(8), 연도, 보고서, 구))
        if os.path.exists(p):
            try:
                return 읽자(p)
            except (OSError, ValueError):
                return None
    return None


def 이자비용(fr, 고유):
    """재무 행 → (이자비용, 근거). `전체재무_추출.csv` 의 `이자비용` 칸이 먼저, 없으면 `_raw/peers/fs/` 캐시 원문을 `dart_fs_all.이자비용뽑기` 로."""
    v = _n(fr.get("이자비용"))
    if v is not None and fr.get("이자비용") not in ("", None):
        return v, fr.get("이자비용근거") or "전체재무_추출.csv 이자비용"
    j = _fs캐시(고유, fr.get("연도"), fr.get("보고서"), fr.get("쓴구분"))
    if not j:
        return None, "이자비용 칸 · fs 캐시 원문 없음"
    try:
        import dart_fs_all as _fsa
        return _fsa.이자비용뽑기(j, str(fr.get("보고서") or "11011"))
    except Exception as e:                                   # noqa: BLE001
        return None, "이자비용 읽기 실패(%s)" % type(e).__name__


_지분계정 = re.compile(r"(관계기업|공동기업|관계회사|지분법적용|기타포괄손익.{0,8}공정가치)")


def 지분장부(고유, fr):
    """대상 재무상태표의 지분 투자 장부(관계 · 공동기업 · 지분법 · 기타포괄 공정가치 금융자산) 합 → (합, 근거). 지주형 신호의 재료 —
    상장 여부를 가르지 못하는 장부 근사라 근거에 적는다."""
    j = _fs캐시(고유, (fr or {}).get("연도"), (fr or {}).get("보고서"), (fr or {}).get("쓴구분")) if fr else None
    if not j:
        return None, "대상 재무 캐시 원문 없음"
    합, 본, 줄 = 0.0, set(), []
    for it in j.get("list") or []:
        nm = (it.get("account_nm") or "").replace(" ", "")
        if (it.get("sj_div") or "") != "BS" or not _지분계정.search(nm) or "부채" in nm or "손익" in nm and "기타포괄" not in nm:
            continue
        v = _n(it.get("thstrm_amount"))
        if v and (nm, v) not in 본:
            본.add((nm, v))
            합 += v
            줄.append("%s %.0f억" % (it.get("account_nm"), v / 1e8))
    return 합, "대상 %s %s 재무상태표 — %s(장부 · 상장 여부 미구분)" % (fr.get("연도"), fr.get("보고서"), " · ".join(줄[:4]) or "해당 계정 없음")


def _이름정규(s):
    return re.sub(r"\s|\(주\)|㈜|주식회사", "", str(s or ""))


def 종속같은사업(부문이름들, 핵심표본):
    """상장 종속회사 이름의 연결 부문 가운데 그 회사의 KIND 주요제품이 C1 슬롯 낱말과 맞는 것(대상과 같은 사업) — 이름 목록.
    KIND 상장명부(회차 `_dartcache` → 공용 C1 캐시)와 핵심표본 `슬롯들` 의 경로② 낱말을 쓴다. 재료가 없으면 빈 목록(종전 판정 그대로)."""
    슬낱 = []
    for x in ((핵심표본 or {}).get("슬롯들") or []):
        kw = x.get("경로2키워드") or ""
        슬낱 += [w.strip() for w in (kw if isinstance(kw, list) else str(kw).split(",")) if w.strip()]
    if not 슬낱:
        return []
    kind = {}
    for q in (os.path.join(ROOT, "_dartcache", "상장명부_KIND.csv"), os.path.join(공용C1뿌리(), "상장명부_KIND.csv")):
        if os.path.exists(q):
            try:
                for r in csv.DictReader(io.open(q, encoding="utf-8-sig")):
                    kind[_이름정규(r.get("회사명"))] = r.get("주요제품") or ""
            except OSError:
                continue
            break
    if not kind:
        return []
    try:
        import peer_후보조립_국내 as _c1
    except Exception:                                       # noqa: BLE001
        return []
    return [k for k in 부문이름들 if kind.get(_이름정규(k)) and _c1.맞은키워드(kind[_이름정규(k)], 슬낱)]


def 대상신호(a, 대상자체, 대상시총, 대상고유, 대상재무, 핵심표본):
    """대상 자체 βU 를 점검값에서 뺄 신호(2026-10-25 FX3-b) — {"상장지분비중", "상장지분근거", "연결지주", "캡티브"}.
    `--대상신호 없음` 이면 신호를 끈다(사람 판단). 문턱은 `βU본값.문턱`."""
    import βU본값 as _b
    신호 = {}
    for 조각 in (getattr(a, "대상신호", None) or "").split(","):
        k, _s, v = 조각.partition("=")
        k, v = k.strip(), v.strip()
        if k == "없음":
            return {"없음": "--대상신호 없음(사람 판단)"}
        if k in ("지주", "연결지주"):
            신호["연결지주"] = v or "--대상신호"
        elif k == "캡티브":
            신호["캡티브"] = v or "--대상신호"
        elif k in ("지분", "상장지분"):
            try:
                신호["상장지분비중"], 신호["상장지분근거"] = float(v), "--대상신호"
            except ValueError:
                pass
    if 핵심표본 and 핵심표본.get("지주대상") and "연결지주" not in 신호:
        신호["연결지주"] = "C1 핵심표본 지주대상"
    if "상장지분비중" not in 신호 and 대상시총:
        합, 근 = 지분장부(대상고유, 대상재무)
        if 합:
            # 2026-10-25 FX4-P — 판정 근거에 장부 · 시가총액 값을 함께 적는다(사람이 문턱 판정을 바로 볼 수 있게 — 장부 근사 · 상장 여부 미구분)
            신호["상장지분비중"], 신호["상장지분근거"] = 합 / 대상시총, "%s · 지분 장부 %.0f억 ÷ 시가총액 %.0f억 = %.0f%%" % (
                근, 합 / 1e8, 대상시총 / 1e8, 합 / 대상시총 * 100)
            신호["지분장부"], 신호["대상시총"] = 합, 대상시총
    A3 = {}
    p = os.path.join(ROOT, "_raw", "동인원천.json")
    if os.path.exists(p):
        try:
            A3 = 읽자(p)
        except (OSError, ValueError):
            A3 = {}
    유형 = A3.get("유형") or {}
    s = 유형.get("신호") or {}
    if s.get("지주문장"):                         # 지주 문장만으로는 빼지 않는다 — 연결 사업 전체가 슬롯이면 자체 βU 가 맞는 점검값이다
        신호["지주문장참고"] = "A3 지주 문장 %d건(참고 — 판정에 쓰지 않음)" % len(s["지주문장"])
    부문 = 유형.get("구분별상세") or {}
    DE = (대상자체 or {}).get("DE_본")
    금융 = [k for k in 부문 if re.search(r"금융|캐피탈|카드|파이낸|리스|할부", str(k))] or (["유형 판정 「금융」"] if "금융" in (유형.get("판정") or []) else [])
    if "캡티브" not in 신호 and 금융 and isinstance(DE, (int, float)) and DE >= _b.문턱["캡티브DE"]:
        신호["캡티브"] = "연결 D/E %.2f ≥ %.1f · 금융 부문(%s)" % (DE, _b.문턱["캡티브DE"], ", ".join(금융[:3]))
    # 연결 지주(SOTP 꼴) — 연결 영업부문 가운데 **다른 상장사 이름의 부문**이 있고 그 부문이 C1 슬롯(위험 동종을 고른 사업)에 없으면,
    # 평가는 그 자회사를 지분가치로 따로 두고 자체 사업만 슬롯으로 잰다 — 대상 자체 βU(연결 그룹)는 점검값이 될 수 없다.
    # 부문 매출 몫은 공시 표의 단위가 들쭉날쭉해(실측) 판정에 쓰지 않고 적기만 한다
    if "연결지주" not in 신호 and len(부문) >= 2:
        상장 = set()
        for q in sorted(glob.glob(os.path.join(공용C1뿌리(), "상장사_주요계정_*.csv")), reverse=True)[:1]:
            try:
                상장 = {_이름정규(r.get("회사명")) for r in csv.DictReader(io.open(q, encoding="utf-8-sig"))}
            except OSError:
                상장 = set()
        이름 = _이름정규((대상자체 or {}).get("티커") or "").replace("(대상)", "")
        슬이름 = [_이름정규(x.get("이름")) for x in ((핵심표본 or {}).get("슬롯들") or []) if x.get("이름")]
        맞 = [k for k in 부문 if _이름정규(k) in 상장 and _이름정규(k) != 이름
             and not any(_이름정규(k) in 슬 or 슬 in _이름정규(k) for 슬 in 슬이름 if 슬)]
        # 2026-10-25 FX4-P — 부문 이름이 아니라 **그 상장 종속회사의 사업(KIND 주요제품)** 이 슬롯 밖일 때만 연결 지주다. 대상과 같은 사업의
        # 상장 종속회사(같은 제품을 만드는 종속)는 연결 지주 신호가 아니다(C2 다시 셈 4-8 — 점안제 대상의 점안제 종속회사)
        if 맞:
            같은사업 = 종속같은사업(맞, 핵심표본)
            if 같은사업:
                신호["연결지주_참고"] = "상장사 이름의 연결 부문 %s 는 사업(주요제품)이 슬롯 안 — 대상과 같은 사업의 종속회사(신호 아님)" % ", ".join(같은사업)
                맞 = [k for k in 맞 if k not in 같은사업]
        if 맞:
            신호["연결지주"] = "상장사 이름의 연결 부문 %d개(%s)가 슬롯 밖 — 자회사를 지분가치로 두는 꼴" % (len(맞), ", ".join(맞[:3]))
    return 신호


try:
    import 한계세율 as _세율표                                      # 국내 법령 세율표 — 회사별 세율(S7-06)
except Exception:                                               # noqa: BLE001
    _세율표 = None


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--기준일", "--평가기준일", dest="기준일", required=True, help="평가기준일 T(분석일 · 시장 쪽 — 종가 · 시가총액 · 주식수 · 베타 창 끝 · 환율 · 법령 시행일) YYYYMMDD")
    ap.add_argument("--대상", required=True,
                    help="종목코드,고유번호,회사명 — 참고행으로 표에 한 줄 넣는다")
    ap.add_argument("--지수", default="넓은",
                    help="넓은(기본 — 전원 KOSPI, 상장시장 지수 회귀는 대안 사양으로 병기 · S7-05) · 자동(회사별 상장시장 — 옛 기본) · "
                         "KOSPI/KOSDAQ(전원 고정)")
    ap.add_argument("--세율고정", action="store_true", help="회사별 세율(영업이익 구간)을 쓰지 않고 전원 --세율(옛 동작)")
    ap.add_argument("--부채스프레드", type=float, default=None, help="D/E ≥ 2 회사의 부채베타 스프레드(없으면 부채베타 미반영)")
    ap.add_argument("--ERP", type=float, default=None, help="부채베타의 ERP — 없으면 시장데이터 캐시 KR 의 성숙 + 국가")
    ap.add_argument("--국면", default=None, help="대상 A3 동인원천(국면) — 기본 _raw/동인원천.json")
    ap.add_argument("--대상시장", default=None, help="대상 상장시장(KOSPI/KOSDAQ) — 캐시로 못 정할 때")
    ap.add_argument("--재무연도", default=None, help="전체재무_추출.csv 병합판에서 쓸 연도")
    ap.add_argument("--재무보고서", default=None, help="전체재무_추출.csv 병합판에서 쓸 보고서 코드")
    # **세율 숫자 기본값을 두지 않는다(HWO-26).** 1차 회차의 20.9% 로 계산된 βU 를 3차(26.4%)가
    # 그대로 인용했다가 감수에서 잡혔다 — 전제는 회차가 명시한다. 2026-10-24 W18: 빼면 숫자가 아니라
    # **출처 규칙**(무차입세율.py — 국내는 법령 세율표)에서 읽고 그 출처를 머리에 남긴다. 주면 대조해 다르면 경보.
    ap.add_argument("--세율", type=float, default=None,
                    help="무차입화 공통 세율(회사별 세율을 못 낸 줄 · 요약). 빼면 무차입세율.py 단일 출처(국내 법령 세율표)")
    ap.add_argument("--연도", default=None,
                    help="성장성 세 해 (쉼표). 기본은 기준일 연도 기준 최근 3개 사업연도")
    ap.add_argument("--후보", default="3차통과.json", help="_raw/peers/ 안의 후보 명단")
    ap.add_argument("--표본", default=None, help="산출 이름 꼬리 — 기본은 후보 명단 파일 이름(확장자 뗌)")
    ap.add_argument("--out", default=None, help="기본: 유사기업_재료_{표본}.csv")
    ap.add_argument("--핵심표본", default="핵심표본.json",
                    help="핵심/예비 구분·미래사업 슬롯을 읽을 C1 산출(없으면 명단의 「왜」 칸)")
    ap.add_argument("--창년", type=int, default=5, help="회귀 창 해 수(기본 5 — 주간). 창 시작 앞의 주는 자른다")
    ap.add_argument("--부터", default=None, help="창 시작 YYYYMMDD — 주면 --창년 보다 앞선다(사슬과 같은 값)")
    ap.add_argument("--기본값규칙", default="축소", choices=["축소", "본값", "세겹"],
                    help="3단계 βU 기본값 규칙 — 축소(기본 · 1.1.3 — 회귀 βU(동종 중앙값 · 대상 자체의 역분산 가중)를 업종 βU 쪽으로 정밀도 가중 축소 · "
                         "`βU본값.축소규칙`) / 본값(옛 순서 — βU본값.py 본값 (b)) / 세겹(① 부문 가중이 ③ 대상 자체와 ±0.20 안이면 ①, 밖이면 가운데 + ★ · 2026-10-25)")
    ap.add_argument("--산업줄", default=None, help="산업 βU 대조 줄(다모다란 Industry Group)을 사람이 정한다 — 대상 매핑 줄이 사업과 다를 때(분류경보)")
    ap.add_argument("--차입확정", default=None,
                    help="국내 차입금 주석 확정 json(기본: C2_차입금_확정.json · C2_차입금_확정_국내.json · 차입금_확정.json 을 _raw/peers · 작업 폴더에서) — 2026-10-25")
    ap.add_argument("--폴더", default=None, help="회차 키트 폴더 — 본체 경로로 돌려도 이 폴더의 _raw · 전체재무_추출.csv 를 읽고 쓴다(2026-10-25 FX4-P)")
    ap.add_argument("--대상신호", default=None,
                    help="대상 자체 βU 를 점검값에서 뺄 신호를 사람이 준다 — 「지주=까닭」 · 「캡티브=까닭」 · 「지분=0.45」 · 「없음」(자동 신호 끔) — 2026-10-25")
    ap.add_argument("--부채베타", default="합성등급", choices=["합성등급", "인자만"],
                    help="D/E ≥ 2 회사의 부채 스프레드 — 합성등급(기본 · 회사마다 이자보상배율) / 인자만(--부채스프레드 만 · 옛 동작)")
    a = ap.parse_args()
    if a.폴더:                                            # 2026-10-25 FX4-P — 회차 뿌리(본체 경로 실행 · C2 다시 셈 2조)
        global ROOT, PEER
        ROOT = os.path.abspath(a.폴더)
        PEER = os.path.join(ROOT, "_raw", "peers")
        os.environ["DCF_RUN_ROOT"] = ROOT
    try:
        import 무차입세율 as _무세
        a.세율, _세경보, _세출처 = _무세.대조(a.세율, "KR", a.기준일)
    except ImportError:                                  # 도구만 따로 옮겨 쓴 자리 — 사람이 준 세율로(단일 출처 대조 없음)
        _세경보, _세출처 = None, "--세율(사람 · 무차입세율.py 없음 — 단일 출처 대조 못 함)" if a.세율 is not None else "무차입세율.py 없음"
    if a.세율 is None:
        sys.exit("무차입 세율을 정하지 못했습니다(%s) — --세율 을 주십시오." % _세출처)
    if _세경보:
        print("[세율 경보] " + _세경보)
    global 창시작
    창시작 = a.부터 or "%04d%s" % (int(a.기준일[:4]) - a.창년, a.기준일[4:])
    표본 = a.표본 or os.path.splitext(os.path.basename(a.후보))[0]
    산출csv = os.path.join(ROOT, a.out or ("유사기업_재료_%s.csv" % 표본))
    산출βU = os.path.join(PEER, "βU_%s.json" % 표본)
    import 피어경로 as _pp0
    후보p = _pp0.명단경로(a.후보, PEER, ROOT)        # 2026-10-24 W16 — 작업 폴더 기준 상대 경로를 PEER 에 겹쳐 붙이지 않는다
    if 후보p in (os.path.abspath(산출csv), os.path.abspath(산출βU)):
        sys.exit("산출이 입력 명단과 같은 파일입니다 — 덮지 않습니다. --표본 을 바꾸십시오.")
    머리 = {"표본": 표본, "명단": os.path.basename(a.후보), "기준일": a.기준일, "세율": a.세율,
          "세율출처": _세출처, "세율경보": _세경보,
          "창": {"시작": 창시작, "끝": a.기준일, "창년": None if a.부터 else a.창년, "주기": "주간"}}
    if os.path.exists(산출βU):
        try:
            옛머리 = 읽자(산출βU).get("머리") or {}
        except (ValueError, OSError):
            옛머리 = {}
        if 옛머리 and (_명단정규(옛머리.get("명단")) != _명단정규(머리["명단"]) or 옛머리.get("기준일") != a.기준일):
            sys.exit("%s 는 다른 명단(%s)·기준일(%s)의 산출입니다 — 덮지 않습니다. --표본 을 바꾸십시오."
                     % (os.path.basename(산출βU), 옛머리.get("명단"), 옛머리.get("기준일")))

    기준일 = a.기준일
    if a.연도:
        연도들 = [int(x) for x in a.연도.split(",")]
    else:
        기준연 = int(기준일[:4])
        연도들 = [기준연 - 3, 기준연 - 2, 기준연 - 1]
    옛, 새 = 연도들[0], 연도들[-1]
    간격 = 새 - 옛

    _대 = [x.strip() for x in a.대상.split(",")] + ["", ""]
    t종목, t고유, t이름 = _대[0], _대[1], _대[2]
    if not t고유 or not t이름:                     # 2026-10-25 FX3-b — 한 칸이면 대상 자체 βU 가 「시가총액 없음」 으로 빠졌다
        t고유, t이름, _대근 = 대상풀기(t종목, t고유, t이름)
        print("[대상] --대상 한 칸 → 고유번호 %s · 이름 %s (%s)" % (t고유 or "?", t이름 or "?", _대근))
        t이름 = t이름 or t종목

    후보 = 후보펼치기(읽자(후보p))
    해외 = [c for c in 후보 if not str(c.get("종목코드") or "").strip()]
    if 해외:                                           # 2026-10-24 W16 — 해외 줄(종목코드 없음)은 미국 사슬의 몫(유니버스 조사 물결 실측)
        print("해외 줄 %d곳 — 국내 조립의 몫이 아니라 건너뜀(미국 사슬 `sec_peer_사슬` 이 같은 명단으로 돈다): %s"
              % (len(해외), ", ".join(str(c.get("회사명") or c.get("티커") or "?") for c in 해외)))
    후보 = [c for c in 후보 if str(c.get("종목코드") or "").strip()]
    전용 = [c for c in 후보 if 운영전용(c)]
    if 전용:
        print("운영 동종 전용 %d곳 — βU 표본이 아니라 회귀하지 않음: %s"
              % (len(전용), ", ".join(str(c.get("회사명") or c.get("종목코드")) for c in 전용)))
    후보 = [c for c in 후보 if not 운영전용(c)]
    후보 = 후보 + [{"종목코드": t종목, "고유번호": t고유,
                 "회사명": "%s(대상)" % t이름, "경로": "-", "왜": "대상회사 참고행"}]
    주식 = 표읽기("주식수.csv")
    재무 = 재무읽기(a.재무연도, a.재무보고서)
    재무전부 = 재무전부읽기()
    # 2026-10-25 FX3-b — 국내 차입금 주석 확정을 CSV 위에 덮는다(종전에는 회차가 전체재무_추출.csv 를 손으로 고쳤다)
    _확정경로 = []
    for _이 in ([a.차입확정] if a.차입확정 else list(_차입확정이름)):
        for _뿌 in ((_이,) if os.path.isabs(_이) else (os.path.join(PEER, _이), os.path.join(ROOT, _이))):
            if os.path.exists(_뿌) and _뿌 not in _확정경로:
                _확정경로.append(_뿌)
    _확정 = 차입확정읽기(_확정경로)
    if _확정:
        _덮은 = 확정덮기(재무, 재무전부, _확정)
        print("[차입금 확정] %s — %d곳 · 덮은 행 %d" % (" · ".join(os.path.basename(p) for p in _확정경로), len(_확정), _덮은))
        for _g in _대용경보:
            print("  ※ 차입금 확정 대용 — " + _g)
        머리["차입확정대용"] = list(_대용경보)
    # 2026-10-25 FX4-P — 대상의 D 는 대상 공시로 세운다(유사기업 주석 큐 잣대로 대상 자체 βU 를 빼지 않는다 — C2 다시 셈 3-3)
    _t8 = str(t고유).zfill(8)
    _tr = 재무.get(_t8)
    if t고유 and (_tr is None or (_tr.get("차입금_확인필요") not in (None, "", "False")) or "주석 큐" in str(_tr.get("D판정") or ""))             and "확정" not in str((_tr or {}).get("D판정") or ""):
        _tD, _t근, _t행 = 대상차입확정(t고유, a.재무연도, a.재무보고서)
        if _tD is not None:
            if _tr is None and _t행 is not None:
                _tr = 재무[_t8] = _t행
            _tr["차입금합계"], _tr["차입금_확인필요"] = _tD, ""
            _tr["D판정"], _tr["D근거"] = "확정(대상 공시)", _t근
            print("[대상 차입금] 대상 공시로 확정 — %.0f억 (%s)" % (_tD / 1e8, _t근))
        else:
            print("[대상 차입금] 대상 공시로 세우지 못함 — %s · 대상 반기 주석으로 C2_차입금_확정.json 에 대상 고유번호 %s 를 적으면 점검값에 든다" % (_t근, _t8))
        머리["대상차입"] = {"D": _tD, "근거": _t근}
    # 2026-10-25 FX3-b — 합성등급 부채 스프레드 재료(시장데이터 캐시 KR 등급표 · 기준일 원달러)
    _등급표, _원달러 = None, None
    if a.부채베타 == "합성등급":
        try:
            import market_data as _md0
            _d0, _ = _md0.캐시읽기("KR", "%s-%s-%s" % (a.기준일[:4], a.기준일[4:6], a.기준일[6:8]))
            _등급표 = ((_d0 or {}).get("합성등급 스프레드 표") or {}).get("값")
        except Exception:                                   # noqa: BLE001
            _등급표 = None
        _환p = os.path.join(PEER, "환율_%s.json" % a.기준일)
        if os.path.exists(_환p):
            try:
                _원달러 = ((읽자(_환p).get("원화고시") or {}).get("FX_USDKRW") or {}).get("원화당")
            except (OSError, ValueError):
                _원달러 = None
    종가경로 = os.path.join(PEER, "종가_%s.json" % 기준일)
    if not os.path.exists(종가경로):
        sys.exit("평가기준일 종가 파일이 없습니다: %s\n"
                 "naver_price.py --일봉 으로 먼저 받으십시오." % 종가경로)
    종가 = 읽자(종가경로)
    # 싼 층 — 후보 판(_후보) 이 없으면 전수 판(dart_peer_screen.py 기본 산출)을 읽는다(S7-06 회사별 세율의 영업이익 · 성장성 칸)
    주요 = {y: (표읽기("상장사_주요계정_%d_후보.csv" % y) or 표읽기("상장사_주요계정_%d.csv" % y)) for y in 연도들}

    # ── 시장지수: 회사마다 상장시장 (펄29) ────────────────────────────────
    고시장, 종시장 = 시장지도()
    넓은 = a.지수 in ("넓은", "broad")
    고정 = None if a.지수 in ("자동", "auto") else ("KOSPI" if 넓은 else a.지수.upper())
    지수캐시 = {}

    def 지수수익(지수):
        if 지수 not in 지수캐시:
            s = 주봉(지수, 기준일)
            지수캐시[지수] = 수익표(s) if s else None
        return 지수캐시[지수]

    대상행 = 후보[-1]
    if a.대상시장:
        대상행["시장"] = a.대상시장
    대상시장, 대상근거 = 시장해석(대상행, 고시장, 종시장)
    대상지수 = 고정 or 대상시장
    if 대상지수 not in ("KOSPI", "KOSDAQ"):
        sys.exit("대상회사 상장시장을 못 정했습니다(%s) — 명단에 대상 「시장」 칸을 주거나 "
                 "--지수 로 고정하십시오. KOSPI 를 자동으로 붙이지 않습니다" % 대상근거)
    if 지수수익(대상지수) is None:
        sys.exit("시장지수 주봉이 없습니다: %s — naver_price.py 로 sise_%s_week_*.json 을 받으십시오"
                 % (대상지수, 대상지수))
    대상주봉 = 주봉(t종목, 기준일)
    if not 대상주봉:
        sys.exit("대상회사 주봉이 없습니다: %s" % t종목)
    대상수익 = 수익표(대상주봉)
    대상잔차들 = {}

    def 대상잔차(지수):
        """대상 잔차를 **그 후보의 회귀 지수로** 다시 낸다 — 짝마다 같은 지수 위의 잔차끼리 잰다.
        펄어비스 회차 선례(KOSPI 후보는 대상의 KOSPI 잔차와 쟀다)와 같다. 대상 시장 지수로
        고정하면 KOSDAQ−KOSPI 괴리가 잔차에 섞여 KOSPI 후보의 잔차상관이 낮게 나온다
        (실측 넷마블 0.204 → 0.154)."""
        if 지수 not in 대상잔차들:
            대상잔차들[지수] = 회귀표(대상수익, 지수수익(지수))[2]
        return 대상잔차들[지수]

    out, 빠진지수, 어긋남 = [], set(), []
    for c in 후보:
        code, corp, nm = c["종목코드"], c.get("고유번호", ""), c.get("회사명") or c.get("이름") or c["종목코드"]
        row = {"회사명": nm, "종목코드": code, "고유번호": corp,
               "경로": c.get("경로", ""), "비고": c.get("왜", "")}
        시장, 근거 = 시장해석(c, 고시장, 종시장)
        지수 = 고정 or 시장
        row.update({"상장시장": 시장 or "확인 불가", "회귀지수": 지수 or "", "시장근거": 근거})
        if 고정 and 시장 and 시장 != 고정 and not 넓은:
            어긋남.append("%s(%s)" % (nm, 시장))
            row["비고"] = (row["비고"] + " · " if row["비고"] else "") + \
                "※ 상장 %s 인데 --지수 %s 로 고정 회귀" % (시장, 고정)
        w = 주봉(code, 기준일)
        row["창끝"] = ("%s" % w[-1][0]) if w else None             # 1.1.2(P10 · CT11) — 실제로 쓴 주봉 창의 끝 날짜(화면 · 산출에 찍는다)
        m수익 = 지수수익(지수) if 지수 in ("KOSPI", "KOSDAQ") else None
        if 지수 in ("KOSPI", "KOSDAQ") and m수익 is None:
            빠진지수.add(지수)
        유동 = 일봉유동성(code, 기준일)                     # 2026-10-25 C1 규모 — 1년 일봉 거래량 0 인 날 · 일평균 거래대금(βU본값 ⑦)
        if w and len(w) > 30 and m수익:
            수익 = 수익표(w)
            # 2026-10-25 FX3-b — 거래 정지 주(연속 무수익 · 일봉 정지 구간 · 재개 첫 주)는 회귀 창과 무거래 비율에서 뺀다
            row["무거래주비율_원"] = (sum(1 for v in 수익.values() if v == 0.0) / len(수익)) if 수익 else None
            뺄, 일뺄, 주구간 = 정지주(수익, 유동.get("정지구간"), _정지문턱()[1])
            # 2026-10-25 FX4-P — 분모에서 주간 정지 주(뺄)도 뺀다 — 1년 일봉 밖의 긴 정지(회생 · 장기 거래정지)가 비율에 남아 정지 뒤 정상 거래 회사가
            # 얇은 거래로 빠졌다(C2 다시 셈 1조 — 37% → 정지 뺀 뒤 약 2%)
            _무거래기준 = {k: v for k, v in 수익.items() if k not in 일뺄 and k not in 뺄}
            if 뺄:
                수익 = {k: v for k, v in 수익.items() if k not in 뺄}
                row["정지주수"] = len(뺄)
                유동["정지구간"] = list(유동.get("정지구간") or []) + [(s, e, "%d주(주간)" % n) for s, e, n in 주구간]
            b, r2, 잔차, cnt = 회귀표(수익, m수익)
            s, _ = 상관표(수익, 대상수익)
            대잔 = 대상잔차(지수)
            j, jn = 상관표(잔차, 대잔) if (잔차 and 대잔) else (None, 0)
            row.update({"베타": b, "결정계수": r2, "표본주": cnt,
                        "단순상관": s, "잔차상관": j, "상관표본": jn})
            # 2026-10-25 C1 규모 — 주간 수익률이 정확히 0 인 주의 비율(얇은 거래 · βU본값 ⑦)
            row["무거래주비율"] = (sum(1 for v in _무거래기준.values() if v == 0.0) / len(_무거래기준)) if _무거래기준 else None
            # 3년 창 대안(S7-06) — 같은 주봉의 뒤 3년만
            삼시작 = "%04d%s" % (int(기준일[:4]) - 3, 기준일[4:])
            b3, r23, _, n3 = 회귀표({k: v for k, v in 수익.items() if k >= 삼시작}, m수익)
            row.update({"베타_3년": b3, "결정계수_3년": r23, "표본주_3년": n3})
            # 상장시장 지수 대안(S7-05) — 넓은 지수로 본값을 낸 회사가 KOSDAQ 상장이면 그 지수로도 잰다
            if 넓은 and 시장 in ("KOSPI", "KOSDAQ") and 시장 != 지수 and 지수수익(시장):
                bl2, r2l, _, nl = 회귀표(수익, 지수수익(시장))
                row.update({"베타_상장지수": bl2, "결정계수_상장지수": r2l, "상장지수": 시장})
            else:
                row.update({"베타_상장지수": b, "결정계수_상장지수": r2, "상장지수": 지수})
        else:
            사유 = ("시장 확인 불가 — 회귀 안 함" if not 지수 else
                    ("%s 지수 주봉 없음" % 지수 if (지수 in ("KOSPI", "KOSDAQ") and not m수익) else
                     ("%s 는 KOSPI/KOSDAQ 가 아니라 회귀 안 함" % 지수 if 지수 not in ("KOSPI", "KOSDAQ") else "주봉 30개 이하")))
            row.update({"베타": None, "잔차상관": None, "표본주": len(w) if w else 0})
            row["비고"] = (row["비고"] + " · " if row["비고"] else "") + 사유

        row.update(유동)
        p = 종가.get(code)
        sh = 주식.get(corp, {})
        유통, 발행 = _n(sh.get("유통주식수")), _n(sh.get("발행주식총수"))
        분모, 종류 = ((유통, "유통(자기주식 차감)") if 유통
                    else (발행, "발행(유통 확인 불가)"))
        row.update({"종가": p, "주식수분모": 분모, "분모종류": 종류,
                    "시가총액": p * 분모 if (p and 분모) else None})

        f = 재무.get(str(corp).zfill(8), 재무.get(corp, {}))
        D, E = _n(f.get("차입금합계")), row["시가총액"]
        row["부채총계"], row["자산총계"] = _n(f.get("부채총계")), _n(f.get("자산총계"))
        row["계약부채"] = _n(f.get("계약부채선수금"))          # 2026-10-24 W16 — 수주 산업의 캡티브 오탐을 막는 재료(βU본값)
        row["예수정산부채"] = _n(f.get("예수정산부채"))        # 2026-10-25 FX4-P — 결제 회사 예수금 · 정산금(캡티브 오탐을 막는 재료)
        # 회귀 창 기말 점(S7-06) — 전체재무_추출.csv 의 창 안 행마다 D ÷ (시가총액 × 주봉 종가비). 주식수는 기준일 고정(근사)
        점들 = []
        if E and w:
            p0 = w[-1][1] if w else None
            for fr in 재무전부.get(str(corp).zfill(8), []):
                d8 = _보고서끝(fr)
                if not d8 or not (창시작 <= d8 <= 기준일) or not p0:
                    continue
                pt = [v for dd, v in w if dd <= d8]
                Dt = _n(fr.get("차입금합계"))
                if not pt or Dt is None:
                    continue
                Et = E * pt[-1] / p0
                현t = _n(fr.get("현금및현금성자산"))
                점들.append({"날짜": d8, "D": Dt, "E": Et, "DE": Dt / Et if Et else None,
                           "현금비중": ((현t + (_n(fr.get("단기투자")) or 0)) / (Et + Dt)) if (현t is not None and Et + Dt) else None,
                           "재무기준": "%s %s" % (fr.get("연도"), fr.get("보고서"))})
        row["창점"] = 점들
        # 회사별 세율(S7-06) — 직전 사업연도 영업이익을 과세표준 근사로 법령 세율표 구간 세율
        row["세율"], row["세율근거"] = a.세율, "--세율(공통)"
        if not a.세율고정:
            영익 = _n((주요.get(새) or {}).get(corp, {}).get("영업이익")) if 주요.get(새) else None
            if 영익 is not None and 영익 > 0 and _세율표:
                try:
                    r세 = _세율표.한계세율("%s-%s-%s" % (기준일[:4], 기준일[4:6], 기준일[6:8]), 영익)
                    if r세.get("한계세율") is not None:
                        row["세율"], row["세율근거"] = r세["한계세율"], "법령 세율표 — %d 영업이익 %.0f억 구간(과세표준 근사)" % (새, 영익 / 1e8)
                except Exception:                           # noqa: BLE001
                    pass
            elif 영익 is not None and 영익 <= 0:
                row["세율근거"] = "--세율(공통) — 영업이익 %.0f억 ≤ 0 이라 구간을 안 고름" % (영익 / 1e8)
        # 2026-10-25 FX3-b — 회사마다 합성등급 부채 스프레드(D/E ≥ 2 일 때 βU본값이 쓴다) — 이자보상배율 = 영업이익 ÷ 이자비용(같은 기간 누계)
        if _등급표 and f:
            _이자, _이근 = 이자비용(f, corp)
            _영익 = _n(f.get("영업이익"))
            # 2026-10-25 FX4-P — 이자비용이 없으면 스프레드를 세우지 않는다(종전에는 0 으로 넣어 이자보상배율 무한 → AAA 스프레드가 섰다).
            # 금융원가 · 금융비용은 이자비용 대용이 아니다 — D/E ≥ 2 동종은 βU본값 ⑧ 로 본값 밖(사유 기록)
            if _이자 is None:
                row["부채스프레드_근거"] = "스프레드 못 세움 — %s" % _이근
            if _이자 is not None:
                try:
                    import 합성등급 as _hg
                    _r합 = _hg.판정(_영익, _이자, (row["시가총액"] / _원달러) if (row["시가총액"] and _원달러) else None, _등급표)
                    if _r합.get("스프레드") is not None:
                        row["부채스프레드"] = _r합["스프레드"]
                        row["이자보상배율"] = _r합.get("이자보상배율")
                        row["부채스프레드_근거"] = "합성등급 %s(%s · 이자 %s · %s · %s%s)" % (
                            _r합.get("등급"), _r합.get("판정사유"), _이근, _r합.get("표"), f.get("재무기준", ""),
                            "" if _원달러 else " · 환율 파일 없음 — 시가총액 미상 표")
                except Exception:                           # noqa: BLE001
                    pass
        row.update({"차입금": D, "차입금_확인필요": f.get("차입금_확인필요", ""),
                    "D판정": f.get("D판정", ""), "D근거": f.get("D근거", ""),
                    "재무기준": f.get("재무기준", ""),
                    "차입금항목": f.get("차입금항목", ""),
                    "현금": _n(f.get("현금및현금성자산")),
                    "자본총계_장부": _n(f.get("자본총계")),
                    "DE": (D / E) if (D is not None and E) else None})
        row["βU"] = (row["베타"] / (1 + (1 - row["세율"]) * row["DE"])
                     if (row.get("베타") is not None and row["DE"] is not None) else None)
        # ── 현금보정 (현금보정.py 규약): βU ÷ (1 − (현금+단기투자) ÷ (시가총액 + D)) ──
        현금경보 = []
        단기 = _n(f.get("단기투자")) if "단기투자" in f else None
        if f and "단기투자" not in f:
            현금경보.append("전체재무_추출.csv 에 단기투자 칸 없음(옛 판) — 현금및현금성자산만")
        if (f.get("단기투자_제외후보") or "").strip():
            현금경보.append("단기투자 제외후보(합산 안 함): %s" % f["단기투자_제외후보"][:120])
        if row["현금"] is None:
            합계, 비중, 불가 = None, None, "현금및현금성자산 없음"
        elif not E:
            합계, 비중, 불가 = None, None, "시가총액 없음"
        elif D is None:
            합계, 비중, 불가 = None, None, "차입금 확인 불가 — 기업가치를 세우지 않음"
        else:
            합계 = row["현금"] + (단기 or 0)
            비중, 불가 = 합계 / (E + D), None
            if 비중 >= 0.5:                 # S7-03 — 종전 90%. 50% 이상이면 보정이 두 배 넘게 부풀린다 — 본값에서 빼고 포함 값 병기
                현금경보.append("현금비중 %.0f%% — 보정이 두 배 넘게 부풀린다(50%% 이상 — 본값 제외 · 보정 전 · 후 병기)" % (비중 * 100))
        row.update({"단기투자": 단기, "현금·단기투자": 합계, "기업가치": (E + D) if (E and D is not None) else None,
                    "현금비중": 비중, "βU_현금보정": 보정(row["βU"], 비중),
                    "현금보정_경보": " · ".join(현금경보), "현금보정_확인불가": 불가})

        for y in 연도들:
            r = 주요[y].get(corp, {})
            row["매출_%d" % y] = _n(r.get("매출액"))
            row["영업이익_%d" % y] = _n(r.get("영업이익"))
            row["순이익_%d" % y] = _n(r.get("당기순이익"))
        for 라벨, 키 in (("매출CAGR", "매출_%d"), ("순이익CAGR", "순이익_%d")):
            x, z = row.get(키 % 옛), row.get(키 % 새)
            row["%s%dy" % (라벨, 간격)] = (((z / x) ** (1.0 / 간격) - 1)
                                        if (x and z and x > 0 and z > 0) else None)
        rev, op, ni = (row.get("매출_%d" % 새), row.get("영업이익_%d" % 새),
                       row.get("순이익_%d" % 새))
        row["영업이익률_%d" % 새] = (op / rev) if (rev and op is not None) else None
        row["PER"] = (E / ni) if (E and ni and ni > 0) else None
        bk = row.get("자본총계_장부")
        row["PBR"] = (E / bk) if (E and bk and bk > 0) else None
        out.append(row)

    앞칸 = ["회사명", "종목코드", "고유번호", "경로", "종가", "주식수분모", "분모종류",
           "시가총액", "베타", "결정계수", "표본주", "단순상관", "잔차상관", "상관표본",
           "차입금", "차입금_확인필요", "DE", "βU", "현금", "자본총계_장부"]
    해별 = ([("매출_%d" % y) for y in 연도들] + [("영업이익_%d" % y) for y in 연도들]
           + [("순이익_%d" % y) for y in 연도들])
    cols = (앞칸 + 해별 + ["매출CAGR%dy" % 간격, "순이익CAGR%dy" % 간격,
                         "영업이익률_%d" % 새, "PER", "PBR", "차입금항목",
                         "단기투자", "현금·단기투자", "기업가치", "현금비중", "βU_현금보정",
                         "현금보정_경보", "현금보정_확인불가",
                         "상장시장", "회귀지수", "시장근거", "재무기준", "비고"])
    p = 산출csv
    줄순 = sorted(out, key=lambda r: -(r.get("잔차상관") or -9))
    with io.open(p, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in 줄순:
            w.writerow(r)
    print("→ %s (%d행)" % (p, len(out)))

    print("%-16s %8s %8s %8s %8s %8s %8s %s"
          % ("회사", "시총(억)", "베타", "잔차상관", "D/E", "βU", "영익률", "지수"))
    for r in 줄순:
        def g(v, s="%8.3f"):
            return "     n/a" if v is None else s % v
        print("%-16s %8s %8s %8s %8s %8s %8s %s"
              % (r["회사명"][:16],
                 g(r["시가총액"] / 1e8 if r["시가총액"] else None, "%8.0f"),
                 g(r.get("베타")), g(r.get("잔차상관")), g(r.get("DE")),
                 g(r.get("βU")), g(r.get("영업이익률_%d" % 새)), r.get("회귀지수") or "-"))

    # ── 회귀 창 — 실제 주 수(창 시작 앞은 잘랐다) ───────────────────────────
    주수 = [r.get("표본주") for r in out if r.get("표본주")]
    if 주수:
        print("\n── 회귀 창 ── %s ~ %s (%s) · 실제 주 수 최소 %d · 최대 %d (사양 %s주)"
              % (창시작, 기준일, "--부터 지정" if a.부터 else "%d년 주간" % a.창년, min(주수), max(주수),
                 "-" if a.부터 else 52 * a.창년))

    # ── 지수 표시 — 섞였으면 표에 적는다 ─────────────────────────
    쓴지수 = sorted({r["회귀지수"] for r in out if r.get("베타") is not None and r.get("회귀지수")})
    print("\n── 시장지수 ── %s · 대상 %s(%s)" % ((("넓은 시장 지수 %s(본값 — 상장시장 지수 회귀는 대안 사양)" % 고정) if 넓은 else ("고정 --지수 %s" % 고정 if 고정 else "자동(회사별 상장시장)")),
                                          대상지수, 대상근거))
    if len(쓴지수) > 1:
        print("  ※ **지수가 섞였습니다** (%s) — βL 을 모아 중앙값을 낼 때 그 사실을 표에 적으십시오. "
              "잔차상관은 짝마다 후보의 지수 위에서 잰 잔차끼리입니다(대상 참고행은 %s)" % ("·".join(쓴지수), 대상지수))
    if 어긋남:
        print("  ※ **상장시장과 다른 지수로 고정 회귀한 곳 %d** — %s. `--지수 자동` 으로 다시 돌리십시오"
              % (len(어긋남), ", ".join(어긋남)))
    if 빠진지수:
        print("  ※ **지수 주봉이 없어 회귀하지 못한 지수: %s** — naver_price.py 로 받은 뒤 다시 돌리십시오"
              % ", ".join(sorted(빠진지수)))
    불가 = [r["회사명"] for r in out if r.get("상장시장") == "확인 불가"]
    if 불가:
        print("  ※ 상장시장 확인 불가 %d곳 — 회귀하지 않았습니다: %s" % (len(불가), ", ".join(불가)))
    기준들 = sorted({r.get("재무기준") for r in out if r.get("재무기준")})
    if len(기준들) > 1:
        print("  ※ 재무 기준이 섞였습니다: %s — --재무연도/--재무보고서 로 고정할 수 있습니다" % " · ".join(기준들))

    # ── 잡음 문턱 — 「상위 N곳」으로 자르기 전에 반드시 본다 ──────────────
    표본들 = [r.get("상관표본") for r in out if r.get("상관표본")]
    if 표본들:
        n중앙 = sorted(표본들)[len(표본들) // 2]
        문턱 = 2.0 / math.sqrt(n중앙)
        넘음 = [r for r in out if (r.get("잔차상관") or 0) > 문턱
                and r["고유번호"] != t고유]
        낮은R2 = [r for r in out if r.get("결정계수") is not None
                 and r["결정계수"] < 0.16 and r["고유번호"] != t고유]
        전체 = [r for r in out if r["고유번호"] != t고유]
        print("\n── 잡음 문턱 ──")
        print("  표본 %d주 → 상관 표준오차 %.3f · **문턱(2배) %.3f**"
              % (n중앙, 1.0 / math.sqrt(n중앙), 문턱))
        print("  문턱을 넘는 후보 **%d곳** / 재료 있는 후보 %d곳"
              % (len(넘음), len(전체)))
        print("  결정계수 0.16 미만 %d곳 / %d곳" % (len(낮은R2), len(전체)))
        문턱값 = 문턱
        if len(넘음) < 8:
            print("  ※ **문턱을 넘는 곳이 8곳에 못 미칩니다.** 「잔차상관 상위 8곳」으로")
            print("     수를 맞추면 그 아래는 **0과 구별되지 않는 값으로 뽑는 것**입니다.")
            print("     문턱까지만 상관으로 자르고, 남는 자리는 사업 접점처럼 값과 무관한")
            print("     기준으로 채우고 그렇게 했다고 적으십시오.")
    βU요약(out, a, 머리, 산출βU, t고유, 문턱값 if 표본들 else None)
    return 0


def βU요약(out, a, 머리, 산출βU, t고유, 문턱):
    """βU·현금보정 세 방식 표 — 미국 `peer_βU_us.py` 의 산출 모양(`βU_{표본}.json`)과 맞춘다."""
    구분, 슬롯, 비위험 = {}, {}, set()
    슬롯비중 = None                                    # 2026-10-25 C1 규모 — C1 `슬롯들`(이름 · 비중) → 부문 가중 βU
    # 2026-10-24 W16 — 「_raw/peers/핵심표본.json」 같은 작업 폴더 기준 상대 경로를 PEER 에 한 번 더 붙여 파일을 못 찾고, 구분 없이 핵심 · 예비를
    # 한 묶음으로 본값을 내던 결함(유니버스 조사 물결 실측)을 피어경로 · 핵심표본읽기로 고친다
    import 피어경로 as _pp
    import 핵심표본읽기 as _hr
    hp = _pp.명단경로(a.핵심표본, PEER, ROOT) if a.핵심표본 else None
    h = None
    if hp and os.path.exists(hp):
        try:
            h = 읽자(hp)
            슬롯비중 = h.get("슬롯들") if isinstance(h, dict) else None
            for k, v in _hr.구분표(h).items():
                if v["시장"] == "US" or not k.isdigit():      # 해외 줄(종목코드 없음)은 미국 사슬의 몫 — 종전에는 KeyError 로 멈췄다(유니버스 조사 물결 실측)
                    continue
                g = v["구분"] if v["구분"] in ("핵심", "예비", "운영동종전용") else "넓은표본"
                구분[k] = g
                슬롯[k] = v["슬롯"]
                if g == "운영동종전용" or 운영전용(v["행"]):
                    비위험.add(k)
            머리["표본판"] = {k: v for k, v in (("B1도착", h.get("B1도착")),
                                                ("보강수", len(h["보강"]) if isinstance(h.get("보강"), list) else None))
                           if v is not None}
        except (ValueError, OSError, KeyError, TypeError, AttributeError):
            구분 = {}
    def 행꼴(r, g):
        return {"티커": r["회사명"], "종목코드": r["종목코드"], "구분": g, "핵심": g == "핵심",
                  "미래사업슬롯": "미래" in (슬롯.get(r["종목코드"]) or ""),
                  "βL": r.get("베타"), "R2": r.get("결정계수"), "회귀지수": r.get("회귀지수"),
                  "잔차상관": r.get("잔차상관"), "시가총액": r.get("시가총액"), "D": r.get("차입금"),
                  "DE": r.get("DE"), "βU": r.get("βU"), "현금·단기투자": r.get("현금·단기투자"),
                  "현금비중": r.get("현금비중"), "βU_현금보정": r.get("βU_현금보정"),
                  "현금보정_경보": r.get("현금보정_경보"), "현금보정_확인불가": r.get("현금보정_확인불가"),
                  "재무기준": r.get("재무기준"),
                  # 본값 재료(S7-03 · 06 · 17)
                  "표본주": r.get("표본주"), "세율": r.get("세율"), "세율근거": r.get("세율근거"),
                  "차입금_확인필요": r.get("차입금_확인필요"), "부채총계": r.get("부채총계"), "자산총계": r.get("자산총계"),
                  "계약부채": r.get("계약부채"), "예수정산부채": r.get("예수정산부채"),
                  "DE_점들": [p["DE"] for p in r.get("창점") or [] if p.get("DE") is not None],
                  "현금비중_점들": [p["현금비중"] for p in r.get("창점") or [] if p.get("현금비중") is not None],
                  "창점": r.get("창점") or [], "βL_3년": r.get("베타_3년"), "R2_3년": r.get("결정계수_3년"),
                  "βL_상장지수": r.get("베타_상장지수"), "R2_상장지수": r.get("결정계수_상장지수"), "상장지수": r.get("상장지수"),
                  # 2026-10-25 FX3-b — 회사마다 합성등급 스프레드가 먼저, 없으면 --부채스프레드
                  "부채스프레드": r.get("부채스프레드") if r.get("부채스프레드") is not None else a.부채스프레드,
                  "부채스프레드_근거": r.get("부채스프레드_근거") or ("--부채스프레드" if a.부채스프레드 is not None else ""),
                  "D판정": r.get("D판정") or "", "D근거": r.get("D근거") or "", "이자보상배율": r.get("이자보상배율"),
                  # 2026-10-25 C1 규모 — 유동성(βU본값 ⑦) · 슬롯(부문 가중)
                  "무거래주비율": r.get("무거래주비율"), "무거래일비율": r.get("무거래일비율"),
                  "무거래주비율_원": r.get("무거래주비율_원"), "무거래일비율_원": r.get("무거래일비율_원"),
                  "정지구간": r.get("정지구간") or [], "정지주수": r.get("정지주수"),
                  "일평균거래대금_억": r.get("일평균거래대금_억"), "슬롯": 슬롯.get(r["종목코드"]) or "",
                  "창끝": r.get("창끝")}                     # 1.1.8 — 종전에는 옮기지 않아 창 끝 점검(창실제 · P10)이 늘 비었다

    행 = []
    for r in out:
        if r["고유번호"] == t고유 or r["종목코드"] in 비위험:     # 운영 동종 전용은 βU 표본이 아니다
            continue
        g = 구분.get(r["종목코드"]) or (str(r.get("비고") or "").split(" ")[0] or "").split("·")[0].strip()
        g = g if g in ("핵심", "예비", "넓은표본") else None
        행.append(행꼴(r, g))
    핵 = [z for z in 행 if z["핵심"]] if any(z["구분"] for z in 행) else 행
    요약 = {}
    import statistics as _st2
    for 이름, 묶음 in (("핵심", 핵), ("전체", 행)):
        요약[이름] = {"보정전": 세방식([z for z in 묶음 if z["βU"] is not None], a.세율),
                    "현금보정": 세방식([z for z in 묶음 if z["βU_현금보정"] is not None], a.세율,
                                   키="βU_현금보정", 비중키="현금비중")}
        ok = [z for z in 묶음 if z["βU_현금보정"] is not None]
        if ok:
            요약[이름]["참고_중앙값βU÷(1−중앙값현금비중)"] = (
                _st2.median(z["βU"] for z in ok) / (1 - _st2.median(z["현금비중"] for z in ok)))
        요약[이름]["현금보정_제외"] = [(z["티커"], z["현금보정_확인불가"]) for z in 묶음
                                  if z["βU"] is not None and z["βU_현금보정"] is None]
        지수들 = sorted({z["회귀지수"] for z in 묶음 if z["βL"] is not None and z["회귀지수"]})
        if len(지수들) > 1:
            요약[이름]["지수혼합"] = "βL 이 %s 로 섞였다(표에 적는다)" % "·".join(지수들)
    if any(z["미래사업슬롯"] for z in 핵):
        포함 = 세방식([z for z in 핵 if z["βU_현금보정"] is not None], a.세율, "βU_현금보정", "현금비중")
        제외 = 세방식([z for z in 핵 if z["βU_현금보정"] is not None and not z["미래사업슬롯"]],
                   a.세율, "βU_현금보정", "현금비중")
        요약["미래사업슬롯"] = {"포함": 포함, "제외": 제외}
        if 포함.get("표본수") and 제외.get("표본수"):
            차 = abs(포함["(b)개별중앙값_기본"] - 제외["(b)개별중앙값_기본"])
            요약["미래사업슬롯"].update({"중앙값차": 차, "경보": 차 > 0.15})
    # ── 본값(S7-03 · 06 · 07) — βU본값.py 규칙. 본값 · 포함 · 3년 창 · 상장시장 지수 대안 · 95% 구간 · 산업 βU 대조 · 국면 창 ──
    import βU본값 as 본
    ERP, ERP근거 = a.ERP, "--ERP" if a.ERP else ""
    if ERP is None:
        try:
            import market_data as _md
            _d, _곳 = _md.캐시읽기("KR", "%s-%s-%s" % (a.기준일[:4], a.기준일[4:6], a.기준일[6:8]))
            if _d:
                _성, _국 = (_d.get("성숙시장 위험프리미엄") or {}).get("값"), (_d.get("국가위험프리미엄 (CRP)") or {}).get("값")
                ERP = (_성 + _국) if (_성 is not None and _국 is not None) else (_d.get("시장위험프리미엄 (ERP)") or {}).get("값")
                ERP근거 = "시장데이터 캐시 KR(%s)" % _곳
        except Exception:                                   # noqa: BLE001
            pass
    for z in 행:
        본.본값행(z, ERP)
    for 이름, 묶음 in (("핵심", 핵), ("전체", 행)):
        요약[이름]["본값규칙"] = 본.요약(묶음, a.세율, ERP)
        상장 = [dict(z, βL=z["βL_상장지수"]) for z in 묶음 if not z.get("본값제외") and z.get("βL_상장지수") is not None]
        for z in 상장:
            bu = 본.무차입(z["βL"], z.get("DE_본"), z.get("세율"), z.get("부채베타"))
            z["βU_상장"] = (bu / (1 - z["현금비중_본"])) if (bu is not None and z.get("현금비중_본") is not None and z["현금비중_본"] < 1) else None
        요약[이름]["본값규칙"]["대안_상장지수"] = 본.세방식([z for z in 상장 if z.get("βU_상장") is not None], a.세율, "βU_상장", "현금비중_본")
    # ── 세 겹 βU(2026-10-25 C1 규모) — ① 부문 가중(C1 슬롯 비중) ② 전체 중앙값(핵심 본값 (b)) ③ 대상 자체(상장 대상의 회귀 βU — **점검값**,
    #    본값 중앙값에 넣지 않는다). 대상 자체는 늘 적는다. 기본값을 세 겹 규칙으로 고르는 것은 `--기본값규칙 세겹` 일 때만(기본은 본값 규칙 그대로)
    대상자체 = None
    for r in out:
        if r["고유번호"] == t고유 and r.get("베타") is not None:
            zt = 본.본값행(행꼴(r, "대상"), ERP)
            대상자체 = {k: zt.get(k) for k in ("티커", "βL", "R2", "표본주", "DE_본", "DE_근거", "현금비중_본", "현금비중_근거", "세율", "세율근거",
                                            "βU_본전", "βU_본", "βL_상장지수", "R2_상장지수", "무거래주비율", "무거래일비율", "일평균거래대금_억",
                                            "시가총액", "부채베타", "부채베타_근거", "정지구간")}
            대상자체["본값규칙이면_제외사유"] = zt.get("본값제외") or []
            대상자체["쓰임"] = "점검값 — 유사기업 본값 중앙값에 넣지 않는다(대형 · 고유동 상장 대상의 자기 회귀는 동종 표본이 얇을 때 견줌 값)"
    # 2026-10-25 FX3-b — 대상 자체 βU 판정(지주형 · 연결 지주 · 캡티브 · 본값 제외 사유) · 부문 가중의 큰 슬롯 약함
    대상시총 = next((r.get("시가총액") for r in out if r["고유번호"] == t고유), None)
    try:
        _대재 = 재무읽기(a.재무연도, a.재무보고서).get(str(t고유).zfill(8))
    except Exception:                                       # noqa: BLE001
        _대재 = None
    신호 = 대상신호(a, 대상자체, 대상시총, t고유, _대재, h if isinstance(h, dict) else None) if 대상자체 else {}
    판정 = 본.대상자체판정(대상자체, 신호) if 대상자체 else None
    if 대상자체 is not None:
        대상자체["판정"], 대상자체["신호"] = 판정, 신호
    부문 = 본.부문가중(핵, 슬롯비중, 대상시총=대상시총)
    _본b = 요약["핵심"]["본값규칙"].get("본값") or {}
    # 2026-10-25 FX3-b — ② 도 본값 규칙의 최소 표본(셋)을 따른다 — 한두 회사 중앙값을 세 겹 기본값으로 넘기지 않는다(현대차 회차 실측 n=1)
    전체중앙 = _본b.get("(b)개별중앙값_기본") if _본b.get("표본수", 0) >= 본.기본값최소표본 else None
    겹 = 본.세겹(부문["값"] if 부문 else None, 전체중앙, (대상자체 or {}).get("βU_본"),
                대상까닭=(("βL %.3f 는 섰으나 대상 재무 · 시가총액이 없어 무차입화 못 함(%s) — 사슬 `--대상 종목,고유번호,이름` 이면 함께 받는다"
                         % (대상자체["βL"], ", ".join(대상자체.get("본값규칙이면_제외사유") or [])))
                        if (대상자체 and 대상자체.get("βL") is not None and 대상자체.get("βU_본") is None) else None),
                부문정보=부문, 대상판정=판정)
    if getattr(a, "기본값규칙", "본값") == "세겹" and 겹.get("제안") is not None:
        옛 = 요약["핵심"]["본값규칙"].get("기본값")
        요약["핵심"]["본값규칙"]["기본값_본값규칙"] = 옛
        요약["핵심"]["본값규칙"]["기본값"] = {"값": 겹["제안"], "출처": "세겹(%s)" % 겹["까닭"],
                                       "표본수": (옛 or {}).get("표본수"), "★": bool(겹.get("★") or (부문 or {}).get("★") or (옛 or {}).get("★")),
                                       "★★": bool(겹.get("★★"))}
    elif getattr(a, "기본값규칙", "본값") == "세겹" and 겹.get("제안") is None:
        # 2026-10-25 FX3-b — ① 을 못 쓰고 ② 도 없으면 산업 βU 선택지(값 없음 · ★★) — 옛 본값 규칙 값을 그대로 넘기지 않는다
        옛 = 요약["핵심"]["본값규칙"].get("기본값")
        요약["핵심"]["본값규칙"]["기본값_본값규칙"] = 옛
        요약["핵심"]["본값규칙"]["기본값"] = {"값": None, "출처": "세겹 — %s" % 겹["까닭"], "표본수": (옛 or {}).get("표본수"),
                                       "★": True, "★★": True}
    산업 = None
    try:
        import 산업베타 as _ib
        대시장 = None
        for r in out:
            if r["고유번호"] == t고유:
                대시장 = r.get("상장시장")
        b = 요약["핵심"]["본값규칙"]["본값"]
        # 2026-10-24 W18 — 핵심 동종의 매핑 줄로도 견준다(분류경보 · 대안줄) · `--산업줄` 이면 사람이 정한 줄
        _동 = [_ib.국내티커(z["종목코드"]) for z in 행 if z.get("핵심") and z.get("종목코드")]
        산업 = _ib.대조값(_ib.국내티커(r대상종목(out, t고유), 대시장), b.get("(b)개별중앙값_기본"),
                         "%s-%s-%s" % (a.기준일[:4], a.기준일[4:6], a.기준일[6:8]), a.산업줄, None, None if a.산업줄 else _동)
    except SystemExit as e:
        산업 = {"문장": "산업 βU 대조 불가 — %s" % e, "★": False}
    except Exception as e:                                  # noqa: BLE001
        산업 = {"문장": "산업 βU 대조 불가 — %s" % type(e).__name__, "★": False}
    # 2026-10-25 FX5-P — 잡음 βU 규칙(총괄 결정 ①): 본값 결정계수 중앙값 < 0.10 이고 동종 중앙값 · 대상 자체 · 산업 βU 가 0.30 넘게 갈리면
    # 세 값의 가운데(대상 자체가 빠지면 둘의 가운데). 세 겹 다음 차례 — `--기본값규칙 세겹` 이면 기본값을 덮고, 아니면 참고로 싣는다
    잡음 = 본.잡음규칙(핵, 겹, 산업)
    겹["잡음규칙"] = 잡음
    if getattr(a, "기본값규칙", "본값") == "세겹" and 잡음.get("적용"):
        요약["핵심"]["본값규칙"]["기본값"] = 본.잡음기본값(요약["핵심"]["본값규칙"].get("기본값"), 잡음)
    # 1.1.3(B1) — 정밀도 가중 축소: 회귀 βU(동종 중앙값 · 대상 자체 — 역분산 가중)와 업종 βU 를 회귀의 정밀도로 가중한다(이진 전환 · 문턱 절벽을 걷는다).
    #   기본값 규칙의 기본 — `--기본값규칙 본값 | 세겹` 이면 참고로만 싣는다
    축 = 본.축소규칙(핵, 겹, 산업, 대상자체, 판정, (요약["핵심"]["본값규칙"] or {}).get("구간95"))
    겹["축소규칙"] = 축
    if getattr(a, "기본값규칙", "본값") == "축소" and 축.get("적용"):
        요약["핵심"]["본값규칙"]["기본값_옛규칙"] = 요약["핵심"]["본값규칙"].get("기본값")
        요약["핵심"]["본값규칙"]["기본값"] = 본.축소기본값(요약["핵심"]["본값규칙"].get("기본값"), 축)
    국면 = 본.국면창점검(a.국면 or os.path.join(ROOT, "_raw", "동인원천.json"), 머리["창"]["시작"], a.기준일)
    결과 = {"머리": dict(머리, 보정식=_보정출처, 세방식=_세방식출처),
          "세율": a.세율, "기준일": a.기준일,
          "식": "βU = βL/(1+(1−t)D/E) · βU(보정) = βU ÷ (1 − (현금+단기투자)/(시가총액+D)) — 개별 보정 뒤 중앙값",
          "단기투자정의": "dart_fs_all.py 단기투자 칸(단기금융상품·단기예금·단기투자자산·단기투자증권·단기금융자산 합) — "
                     "당기손익-공정가치·기타유동금융자산은 합산 안 함(제외후보로 표시)",
          "표": 행, "요약": 요약,
          "잡음문턱": {"문턱": 문턱, "넘는수": sum(1 for z in 행 if 문턱 and (z["잔차상관"] or 0) > 문턱),
                   "전체": len(행)},
          "본값": {"핵심": 요약["핵심"]["본값규칙"], "판정": 요약["핵심"]["본값규칙"].get("판정"), "기본값": 요약["핵심"]["본값규칙"].get("기본값"), "ERP": ERP, "ERP근거": ERP근거, "산업대조": 산업, "국면창": 국면,
                 "대상자체": 대상자체, "부문가중": 부문, "세겹": 겹, "축소": 축, "기본값규칙": getattr(a, "기본값규칙", "본값"),
                 "대상자체판정": 판정, "대상신호": 신호,
                 "지수": "넓은(KOSPI) — 상장시장 지수 회귀는 `대안_상장지수`" if a.지수 in ("넓은", "broad") else a.지수,
                 "쓰는법": "3단계 WACC 의 무차입 베타 기본값은 `본값.핵심.기본값.값`(출처 칸 — 본값 셋 이상이면 본값 (b), 아니면 포함 (b), 그것도 셋 미만이면 산업 βU 선택지 ★ · S7R1-N1) — 「포함」 · 「대안_3년창」 · "
                         "「대안_상장지수」 · 「구간95」 · 산업 βU 를 근거 칸과 민감도 WACC 폭에 함께 싣는다"}}
    _끝들 = sorted({("%s" % z.get("창끝")) for z in 행 if z.get("창끝")})
    _T8 = ("%s" % a.기준일).replace("-", "")[:8]
    _늦음 = [z.get("회사명") or z.get("종목") or "?" for z in 행 if z.get("창끝") and ("%s" % z["창끝"]).replace("-", "")[:8] < (
        _dt.strptime(_T8, "%Y%m%d") - _td(days=14)).strftime("%Y%m%d")]
    결과.setdefault("창실제", {"끝": _끝들, "평가기준일보다14일넘게이른": _늦음})
    json.dump(결과, io.open(산출βU, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print()
    print("실제 주봉 창 끝: %s%s" % (" · ".join(_끝들) or "없음", ("  **경보 — 창 끝이 평가기준일보다 14일 넘게 이른 회사: %s(옛 창 시세 파일 — 다시 받는다)**"
                                                          % " · ".join(map(str, _늦음))) if _늦음 else ""))
    print("── βU 세 방식 (세율 %.4f · %s · %s) ──" % (a.세율, _보정출처, _세방식출처))
    for 이름, s2 in 요약.items():
        for k, v in s2.items():
            if isinstance(v, dict) and v.get("표본수"):
                print("  %s·%s: n=%d (a) %.4f · (b) %.4f[기본] · (c) %.4f · 폭 %.4f%s · 아래 %s · 위 %s" % (
                    이름, k, v["표본수"], v["(a)평균합산"], v["(b)개별중앙값_기본"], v["(c)개별평균"],
                    v["세값폭"], " (0.01 안)" if v["세값_0.01안"] else "", v["아래둘"], v["위둘"]))
            elif k.startswith("참고") and isinstance(v, float):
                print("  %s·%s: %.4f" % (이름, k, v))
            elif k in ("현금보정_제외", "지수혼합") and v:
                print("  %s·%s: %s" % (이름, k, v))
    print("── 본값(βU본값.py) ── " + 본.문장(요약["핵심"]["본값규칙"], 산업))
    상 = 요약["핵심"]["본값규칙"].get("대안_상장지수") or {}
    if 상.get("표본수"):
        print("  대안 — 상장시장 지수 회귀 (b) %.4f (n=%d)" % (상["(b)개별중앙값_기본"], 상["표본수"]))
    if 요약["핵심"]["본값규칙"].get("경보"):
        print("  ※ " + 요약["핵심"]["본값규칙"]["경보"])
    if 산업 and 산업.get("★"):
        print("  ★ 산업 βU 대조 — 핵심 본값 중앙값이 산업 βU 의 ±30% 밖이다. 확정 신뢰도 ★(문항) — 유사기업 βU 규칙")
    if 국면:
        print("  국면 창 — " + 국면["문장"])
    if 대상자체:
        print("  대상 자체 βU(점검값) %s · βL %s · R² %s · %s주" % (
            ("%.4f" % 대상자체["βU_본"]) if 대상자체.get("βU_본") is not None else "-", ("%.3f" % 대상자체["βL"]) if 대상자체.get("βL") is not None else "-",
            ("%.3f" % 대상자체["R2"]) if 대상자체.get("R2") is not None else "-", 대상자체.get("표본주")))
    if 부문:
        print("  부문 가중 βU %s — %s%s" % (("%.4f" % 부문["값"]) if 부문.get("값") is not None else "-",
              " · ".join("%s %.0f%% n=%d %s" % (c["이름"], c["비중"] * 100, c["표본수"], ("%.3f" % c["중앙값"]) if c["중앙값"] is not None else "-") for c in 부문["슬롯"]),
              (" ★(%s)" % 부문["까닭"]) if 부문.get("★") else ""))
    if 판정 and not 판정.get("쓴다") and 대상자체 and 대상자체.get("βU_본") is not None:
        print("  대상 자체 βU 는 점검값에서 뺌 — %s" % " · ".join(판정.get("사유") or []))
    print("  세 겹 제안 %s — %s%s" % (("%.4f" % 겹["제안"]) if 겹.get("제안") is not None else "-", 겹.get("까닭"),
                                  " [기본값으로 씀 — --기본값규칙 세겹]" if getattr(a, "기본값규칙", "본값") == "세겹" else " [참고 — 기본값은 본값 규칙]"))
    if 잡음.get("적용"):
        print("  잡음 βU 규칙 %.4f(폭 %.3f ~ %.3f) — %s%s" % (잡음["제안"], 잡음["민감도폭"][0], 잡음["민감도폭"][1], 잡음["까닭"],
                                                    " [기본값으로 씀]" if getattr(a, "기본값규칙", "본값") == "세겹" else " [참고]"))
    elif 잡음.get("까닭"):
        print("  잡음 βU 규칙 — %s" % 잡음["까닭"])
    print("→ %s" % 산출βU)


def r대상종목(out, t고유):
    for r in out:
        if r["고유번호"] == t고유:
            return r["종목코드"]
    return ""


if __name__ == "__main__":
    sys.exit(main())

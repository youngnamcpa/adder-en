# -*- coding: utf-8 -*-
"""연장 — 예측기간을 6~10년으로 늘린 사본을 둔화 층으로 채우고, 연수마다 안정성장 네 기준 · 영구가치 비중 · 주당가치 ·
연장 전후 차를 한 표로 낸다(「길이 결정」 · 「연장 구간 세우기」 — S8-01, 2026-10-17).

  python 스크립트/연장.py 가정.json                          # 6~10년 후보 전부 — 대조표만(사본은 --낼 을 줄 때)
  python 스크립트/연장.py 가정.json --연수 7,8 --사유 T2 --낼 _raw/연장
  python 스크립트/연장.py 가정.json --되돌리기 5 --낼 _raw/연장   # 늘린 회차의 「연장 전 값」 — 5년으로 되돌린 사본을 같은 엔진으로
  python 스크립트/연장.py 가정.json --수렴채움 --낼 가정_수렴.json # 구조.원가줄[].수렴 선언대로 비운 예측 열을 채운 사본

**사람이 연수를 고른다.** 도구는 후보마다 사본 · 표를 낼 뿐 회차 가정 파일을 고치지 않는다(「모델이 연수를 스스로 확정하지 않는다」).
고른 사본을 회차 가정으로 옮긴 뒤 근거 칸에 트리거와 자료를 적는다. 사본에는 시점가정 249(연장 전 주당가치) · 250(연장 후)을 채운다.

둔화 층 채우는 규칙 — 늘린 열 j(1 … k)의 값 = 마지막 예측 열 값 L 에서 종착 T 까지 직선 걸음(L + (T − L) × j ÷ k). 마지막 연장 열이 곧 T 라
영구기간 열과 절벽 없이 잇는다. 줄마다 종착은
  · 판매량 증가율(30 꼴 · 기타 70)            TV 칸에 값이 있으면 그 값, 비었으면 영구성장률 g(엔진의 TV 규약과 같다)
  · 판매단가 변동률(34 꼴)                    TV 칸 값, 비었으면 0. 단가경로 = 수렴(증가율 경로)이면 비워 둔다 — 엔진이 정상 수준으로 채운다
  · 임금상승률(504) · 원가 줄 수준 변동률(7k2)   TV 칸 값, 비었으면 g(스키마의 영구기간 규약과 같다)
  · Sales-to-Capital(859)                    g ÷ RONIC 에 맞는 값 = 1 ÷ (세후 영업이익률 ÷ RONIC − 운전자본 ÷ 매출)(밑 판 마지막 해)
  · 원가 줄 비율 · 계수 · 회전일수 · 인건비 · 유지 투자율 · 가동률 · 무형 취득 비율 · 세율 등 그 밖의 율   TV 칸 값, 비었으면 L(유지)
  · **종착 맞춤** — 위로 채운 뒤 마지막 연장 열의 영업이익률이 종착에서 0.05%p 밖이면, 원가 줄의 비율 줄(매출액비율 · 설비 계수 · 지표 계수)을
    늘린 열에서 j ÷ k 걸음으로, TV 칸은 끝 배율로 비례 조정한다(`--종착맞춤 끔` 으로 끈다). 종착은 기본이 밑 판의 영구기간 영업이익률이다
    (연장은 기간만 바꾸고 영구 마진은 바꾸지 않는다 — 전후 차가 기간의 효과가 되게). `--종착 기준마진` 이면 213 → 운영 동종 → 사이클 평균
    (안정성장 ② 와 같은 자)으로 걷고, 없으면 맞추지 않고 「종착 없음」 을 적는다. 어느 쪽이든 글에 종착 마진과의 거리를 적는다
  · 자본비용 — 영구 WACC 를 따로 두는 판은 사본에 구조.할인.연도별WACC = 사용(늘린 열에서 영구 WACC 로 걷는다 · `--WACC고정` 으로 끈다)
  · 판매량 수준(6s0 · 저량 유입 57s)          마지막 해 증가율에서 g 까지 걷는 증가율로 굴린다
  · 생산능력(668+2j · 669+2j) · 라인 배분율    L 유지 — 새 프로젝트는 비운다(T2 회수는 사람이 라인 · 프로젝트로 넣는다)
  · 되풀이 금액 줄(등록 `반복금액` — 유지 CAPEX 직접 148 · 처분 152 · 무형 취득 160 · 자산군 폐기액 82g)   L × (1 + g)^j(정상 상태).
    폐기액을 비우면 늘린 열에서 기준 자산군 취득원가가 유지 CAPEX 만큼 복리로 쌓여 유지 CAPEX(850 × 취득원가) · 상각이 함께 뛴다
    (S8-01 재리뷰 2 실측: 설비형 10년 −25.7% 의 대부분이 이 몫이었다)
  · 그 밖의 금액 줄(프로젝트 · 건설중 대체 · 한시적 · 지급 일정)   비운다(빈칸 = 0 — 일회성)
  · 대조 줄(시장 규모 · 점유율 — 값에 안 쓴다)   비운다
  줄의 종류(금액 · 규칙 · 대조 · 율)는 번호 범위가 아니라 시트 함수 파일 머리의 등록(`엔진.스키마.빈칸뜻`)으로 가른다
  · 판매단가 변동률(수준 경로 6s3)            비운다 — 엔진이 유지 · 수렴 · 연동 규칙으로 채운다
**성장은 공짜가 아니다**(S5-12) — 구조.투자.성장규칙 = 매출자본비율(859)이 아니면 표에 「성장 CAPEX 규칙 없음」을 적는다(연장 구간의 성장이
공짜가 된다 — 표의 늘린 판은 투자를 붙이지 않은 값이다).
수명(T1 — `구조.매출구분[].수명`) — 만료 연도 뒤의 해는 그 구분의 판매량 증가율(또는 판매량)을 잔존 비율까지 침식 연수에 걸쳐 내리고,
창이 침식을 다 담지 못하면 영구기간 열의 판매량 증가율에 남은 침식을 싣는다.

표 — 후보 연수 × 세 시나리오: 주당가치 · 연장 전후 차(%) · 영구가치 비중 · 안정성장 네 기준(엔진 `부수.안정성장4기준`) · 마지막 해 FCFF 부호.
판정 — 밑 판이 이미 네 기준을 채우면 「연장 불필요」, 늘린 판이 처음 채우는 연수가 있으면 그 연수, 10년까지 늘려도 안 차면 「서사 문제 — 시나리오로
가른다」. T1 · T2 연장인데 전후 차가 ±5% 안이면 「연장 무효 신호」. ④ 는 예측 끝 증분 ROIC 가 음수(이익 감소 — 마진 정상화)면 해당 없음으로 읽는다.
지분경로가 있으면 단서에 「늘린 사본은 워크북과 갈린다」 를 싣는다(재리뷰 S8R1-N4).
종료 코드: 0 낸 · 2 입력오류. 회사 · 업종 이름은 이 도구에 한 글자도 없다.
"""
import argparse
import copy
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 기간축 import 기간축, 기간축오류  # noqa: E402
from 종료코드 import 통과, 입력오류  # noqa: E402
import dcf엔진 as 엔진  # noqa: E402
from 엔진.스키마 import 빈칸뜻  # noqa: E402
from 엔진.부수 import 종착기준읽기  # noqa: E402
from 엔진.등록 import 반복금액전부  # noqa: E402

시나리오들 = ("비관", "기준", "낙관")
후보연수 = (6, 7, 8, 9, 10)
연장무효폭 = 0.05            # T1 · T2 연장의 전후 차가 이 안이면 무효 신호
원가비율번호 = {1: 80, 2: 84, 3: 88, 4: 92, 5: 112, 6: 116, 7: 120}      # 원가 줄 k 의 매출액비율 줄
상승률번호 = {504} | {700 + 10 * k + 2 for k in range(1, 8)}          # 임금상승률 · 원가 줄 수준 변동률 — 영구기간 규약이 g(스키마)
종착맞춤폭 = 0.0005           # 마지막 연장 열 영업이익률이 종착에서 이 안이면 맞춘 것으로 본다(0.05%p)
종착배율폭 = (0.5, 2.0)        # 비율 줄 배율의 한계 — 밖이면 맞추지 못한 것으로 적는다(비율 밖의 동인이 마진을 움직인다 — 사람이 본다)
영구절벽폭 = 0.005            # S8-01 재리뷰 2 — 마지막 연장 열과 영구기간(TV) 열의 영업이익률 차가 이보다 크면 「영구 절벽 — 늘린 사본」(㉝ 과 같은 자)


def _수(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _축(g):
    return 기간축(g)


def _행종류(r, 구):
    """늘린 열을 채우는 갈래 — 볼륨증가 · 단가변동 · 수렴단가 · 수준 · 유지 · 금액성장 · 비움 · 상승률 · 매출자본 · 율.

    빈칸의 뜻은 시트 함수 파일 머리의 등록이 정한다(`엔진.스키마.빈칸뜻` — 금액 · 규칙 · 대조 · 율). 번호 범위로 가르지 않는다(재리뷰 S8-01 —
    범위로 가르자 구분 2 의 가동률 298 과 무형 취득 ÷ 매출 867 이 「비움」 이 되어 늘린 열의 매출 · 무형 취득이 0 이 됐다)."""
    n = int(r)
    구분들 = {x.get("번호"): x for x in (구.get("매출구분") or []) if isinstance(x, dict)}
    if 30 <= n <= 70 and (n - 30) % 8 == 0:
        return "볼륨증가"
    if 34 <= n <= 66 and (n - 34) % 8 == 0:
        s = (n - 34) // 8 + 1
        x = 구분들.get(s) or {}
        return "수렴단가" if (x.get("경로", "증가율") == "증가율" and x.get("단가경로") == "수렴") else "단가변동"
    if 600 < n < 660 and n % 10 == 0:
        return "수준"
    if 571 <= n <= 575:
        return "수준"
    if 668 <= n <= 699 or 1000 <= n < 1700:
        return "유지"
    종 = 빈칸뜻(r)
    if 종 == "규칙":
        return "수준" if (600 < n < 660 and n % 10 == 1) else "비움"      # 6s1 기말 판매량은 굴리고 6s3 판매단가 변동률은 엔진이 채운다
    if 종 == "금액":
        return "금액성장" if n in 반복금액전부() else "비움"      # S8-01 남은 몫 — 되풀이 금액(폐기 82g · 처분 152 …)은 정상 상태로 채운다
    if 종 in ("대조", "모름"):
        return "비움"
    if n in 상승률번호:
        return "상승률"
    if n == 859:
        return "매출자본"
    return "율"


def _읽기(v, c):
    x = (v or {}).get(c)
    return x if _수(x) else None


def _채우기(벌, 종류, 옛예측, 새열, g, 침식=None, 종착=None):
    """한 시나리오의 {기간 ID: 값} 에 새 예측 열을 채운다(제자리). 침식 = {열: 배율} — 수명의 침식(볼륨증가 · 수준 줄에만).
    종착 = 매출자본(859)의 종착 Sales-to-Capital(영구 재투자율 g ÷ RONIC 에 맞는 값 — `_매출자본종착`)."""
    if not isinstance(벌, dict):
        return
    L = _읽기(벌, 옛예측[-1])
    k = len(새열)
    if 종류 == "비움" or k == 0:
        return
    if 종류 == "수렴단가":
        return
    if L is None:
        return
    tv = _읽기(벌, "TV")
    if 종류 in ("볼륨증가", "상승률"):
        T = tv if tv is not None else g
    elif 종류 == "단가변동":
        T = tv if tv is not None else 0.0
    elif 종류 == "매출자본":
        T = 종착 if 종착 is not None else L
    elif 종류 == "율":
        T = tv if tv is not None else L
    for j, c in enumerate(새열, start=1):
        if 종류 in ("볼륨증가", "단가변동", "율", "상승률", "매출자본"):
            v = L + (T - L) * j / k
            if 침식 and c in 침식 and 종류 == "볼륨증가":
                v = (1 + v) * 침식[c] - 1
            벌[c] = v
        elif 종류 == "유지":
            벌[c] = L
        elif 종류 == "금액성장":
            벌[c] = L * (1 + g) ** j
        elif 종류 == "수준":
            앞 = _읽기(벌, 옛예측[-2]) if len(옛예측) >= 2 else None
            γ0 = (L / 앞 - 1) if (앞 not in (None, 0)) else g
            γ = γ0 + (g - γ0) * j / k
            전 = 벌[새열[j - 2]] if j >= 2 else L
            v = 전 * (1 + γ)
            if 침식 and c in 침식:
                v = v * 침식[c]
            벌[c] = v


def _침식표(구분, 새열, 회계, 끝연도새):
    """수명(만료 연도 M · 잔존 비율 ρ · 침식 연수 n) → {열: 그 해의 침식 배율}, TV 배율. 만료 뒤 n 해에 걸쳐 ρ 까지 기하로 내린다."""
    수명 = 구분.get("수명") if isinstance(구분.get("수명"), dict) else None
    if not 수명 or not _수(수명.get("만료연도")):
        return {}, None
    M = int(수명["만료연도"])
    ρ = float(수명.get("잔존비율") or 0.0)
    n = max(1, int(수명.get("침식연수") or 1))
    한해 = (max(ρ, 1e-9)) ** (1.0 / n)
    표 = {}
    for c in 새열:
        y = 회계.get(c)
        if y is not None and M < y <= M + n:
            표[c] = 한해
    남은 = max(0, min(n, M + n - 끝연도새)) if 끝연도새 >= M else n
    tv배 = 한해 ** 남은 if 남은 > 0 else None
    return 표, tv배


def _g(가정, 시):
    gv = ((가정.get("시점가정") or {}).get("212"))
    gg = gv.get(시, gv.get("공통")) if isinstance(gv, dict) else gv
    return float(gg) if _수(gg) else 0.0


def _매출자본종착(가정, 시):
    """859(Sales-to-Capital)의 종착 — 영구 재투자율 g ÷ RONIC 에 맞는 값(「성장 CAPEX 는 g ÷ ROIC 에 맞는 859」).
    성장 투자 = ΔRev ÷ STC, 순운전자본 증가 = ΔRev × (운전자본 ÷ 매출), 둘의 합 = (g ÷ RONIC) × NOPLAT 이고 ΔRev = g × 매출이라
    STC = 1 ÷ (세후 영업이익률 ÷ RONIC − 운전자본 ÷ 매출). 유지 투자 ≈ 상각으로 본다. 분모가 0 이하면 None(L 유지)."""
    try:
        R = _조용히(엔진.계산, copy.deepcopy(가정), 시)
    except Exception:                                         # noqa: BLE001
        return None
    S, d = R["요약"], R["2.DCF"]
    끝 = S["마지막예측열"]
    매 = _수(d["11"].get(끝)) and d["11"][끝]
    ronic = S.get("영구ROIC")
    if not 매 or not _수(ronic) or ronic <= 0:
        return None
    분모 = (d["19"][끝] / 매) / ronic - (R["9.WC"]["14"][끝] or 0.0) / 매
    return 1.0 / 분모 if 분모 > 1e-9 else None


def _비율줄(가정):
    """영업이익률을 종착으로 걷을 때 비례로 맞추는 원가 줄 — 매출액비율(80 꼴) · 설비 계수(7k1) · 지표 계수(7k8). 물가연동 · 물량단위원가 줄은
    금액 수준이라 비율 손잡이가 없다(그 줄은 상승률 g 로 걷는다)."""
    낸 = []
    for x in ((가정.get("구조") or {}).get("원가줄") or []):
        if not isinstance(x, dict):
            continue
        k, 산식 = x.get("번호"), x.get("산식", "매출액비율")
        번 = {"매출액비율": 원가비율번호.get(k), "설비계수": 700 + 10 * k + 1 if k else None,
             "지표계수": 700 + 10 * k + 8 if k else None}.get(산식)
        if 번 and str(번) in (가정.get("가정") or {}):
            낸.append(str(번))
    return 낸


def _마지막마진(가정, 시, 열):
    R = _조용히(엔진.계산, copy.deepcopy(가정), 시)
    매 = R["4.Sales"]["54"][열]
    return (R["6.SG&A"]["22"][열] / 매) if 매 else None


def _종착맞춤(g0, 새열, 밑마진=None):
    """S8-01 · 재리뷰 S8R1-N1 — 마지막 연장 열의 영업이익률이 종착에 닿도록 비율 줄을 늘린 열에서 걸음으로(j ÷ k) 비례 조정한다.
    TV 칸도 같은 배율 — 마지막 연장 열과 영구기간 열이 절벽 없이 잇게. → {시나리오: 글}.

    종착은 둘 가운데 하나다.
      밑마진 = {시나리오: 값}   밑 판(늘리기 전)의 영구기간 영업이익률 — **기본**. 「종착은 그 줄의 영구기간(TV) 칸」 이고, 연장은 기간만
                               바꾸고 영구의 마진은 바꾸지 않는다(그래야 전후 차가 기간의 효과다). 종착 마진(213 · 운영 동종 · 사이클 평균)과의
                               거리는 글에 같이 적는다 — 그 거리는 ⑥ · 안정성장 ② 가 본다
      밑마진 = None             종착 마진(213 → 운영 동종 → 사이클 평균 — 엔진 `종착기준읽기`)으로 걷는다(`--종착 기준마진`).
                               시나리오의 영구 마진이 213 과 다르면(비관 · 낙관이 일부러 다르게 둔 판) 그 차이를 지운다는 점을 알고 쓴다"""
    글 = {}
    줄들 = _비율줄(g0)
    if not 새열:
        return 글
    A = g0.get("가정") or {}
    for r in 줄들:                                               # 시나리오마다 다르게 맞추므로 「공통」 은 세 벌로 편다
        if "공통" in (A.get(r) or {}):
            A[r] = {시: copy.deepcopy(A[r]["공통"]) for 시 in 시나리오들}
    k = len(새열)
    for 시 in 시나리오들:
        기, 기출처 = 종착기준읽기(g0, 시)
        if 밑마진 is not None:
            T = 밑마진.get(시)
            출처 = "밑 판 영구기간 열" + ((" · 종착 마진 %.2f%%(%s) 대비 %+.2f%%p" % (기 * 100, 기출처, ((T or 0) - 기) * 100)) if 기 is not None else " · 종착 마진 재료 없음")
        else:
            T, 출처 = 기, 기출처
        if T is None:
            글[시] = "종착 없음(213 · 운영 동종 · 사이클 평균) — 원가 줄은 TV 칸 · 유지로 걷는다"
            continue
        if not 줄들:
            글[시] = "종착 %.2f%%(%s) — 비율 줄이 없어(원가 줄이 물가연동 · 물량단위원가) 맞추지 않았다" % (T * 100, 출처)
            continue
        원본 = {r: copy.deepcopy(A[r].get(시)) for r in 줄들 if isinstance(A[r].get(시), dict)}

        def 놓기(f):
            for r, v0 in 원본.items():
                v = copy.deepcopy(v0)
                for j, c in enumerate(새열, start=1):
                    if _수(v.get(c)):
                        v[c] = v[c] * (1 + (f - 1) * j / k)
                if _수(v.get("TV")):
                    v["TV"] = v["TV"] * f
                A[r][시] = v

        try:
            m0 = _마지막마진(g0, 시, 새열[-1])
        except Exception as e:                                # noqa: BLE001
            글[시] = "맞추지 못함 — %s" % ("%s" % e)[:80]
            continue
        if m0 is None or abs(m0 - T) <= 종착맞춤폭:
            글[시] = "종착 %.2f%%(%s) — 이미 닿음(마지막 연장 열 %.2f%%)" % (T * 100, 출처, (m0 or 0) * 100)
            continue
        x0, y0 = 1.0, m0 - T
        x1 = 1.0 + y0 / max(1.0 - m0, 0.05)
        m1 = None
        for _i in range(6):
            x1 = min(종착배율폭[1], max(종착배율폭[0], x1))
            놓기(x1)
            m1 = _마지막마진(g0, 시, 새열[-1])
            y1 = (m1 - T) if m1 is not None else None
            if y1 is None or abs(y1) <= 종착맞춤폭 or abs(y1 - y0) < 1e-12:
                break
            x0, y0, x1 = x1, y1, x1 - y1 * (x1 - x0) / (y1 - y0)
        닿음 = m1 is not None and abs(m1 - T) <= 종착맞춤폭
        글[시] = "종착 %.2f%%(%s) — 비율 줄(%s) × %.3f 로 걸어 마지막 연장 열 %.2f%% → %.2f%%%s" % (
            T * 100, 출처, " · ".join(줄들), x1, m0 * 100, (m1 or 0) * 100, "" if 닿음 else (" — 닿지 못함(배율 %.1f~%.1f 밖 — 비율 줄 밖의 동인이 마진을 움직인다: 설비 취득원가 · 물가연동 금액이 "
                         "매출보다 빨리 는다든가 생산능력을 유지해 매출이 멈춘다. 늘린 열의 그 줄을 사람이 본다)" % 종착배율폭))
    return 글


def 늘리기(가정, 연수, 사유=None, 종착맞춤=True, 연도별WACC=True, 종착="영구열"):
    """예측 연간 열을 `연수` 로 늘린 사본(둔화 층으로 채운다). 수렴연수만 늘린다(상세는 그대로 — 늘린 열은 수렴 구간).

    둔화 층은 종착까지 걷는다 — 증가율 줄은 TV 칸(비면 g), 상승률 줄(임금 504 · 원가 수준 변동률 7k2)은 TV 칸(비면 g), 859 는
    g ÷ RONIC 에 맞는 값(`_매출자본종착`), 비율 줄은 마지막 연장 열의 영업이익률이 종착 마진에 닿게(`_종착맞춤` — 끄려면 종착맞춤=False).
    영구 WACC 를 따로 두는 판은 늘린 사본에 `구조.할인.연도별WACC = 사용` 을 켠다(「연장하면 자본비용도 같이 걷는다」).
    사본의 `_연장` 에 채움 글(종착 맞춤 · WACC)을 남긴다."""
    g0 = copy.deepcopy(가정)
    옛축 = _축(g0)
    P = g0["기간"]
    상세, 수렴 = int(P["상세추정연수"]), int(P.get("수렴연수") or 0)
    if 연수 <= 상세 + 수렴:
        raise ValueError("이미 %d년입니다 — 늘릴 연수(%d)가 더 커야 합니다" % (상세 + 수렴, 연수))
    매출자본종착 = {시: _매출자본종착(가정, 시) for 시 in 시나리오들} if "859" in (가정.get("가정") or {}) else {}
    밑마진 = None
    if 종착맞춤 and 종착 == "영구열":
        밑마진 = {}
        for 시 in 시나리오들:
            try:
                밑마진[시] = _조용히(엔진.계산, copy.deepcopy(가정), 시)["요약"]["영구기간영업이익률"]
            except Exception:                                 # noqa: BLE001
                밑마진[시] = None
    P["수렴연수"] = 연수 - 상세
    if 사유:
        P["연장사유"] = 사유
    elif not P.get("연장사유"):
        P["연장사유"] = "(후보 — T1~T4 가운데 사람이 고른다)"
    새축 = _축(g0)
    옛예측 = [옛축.ID[i] for i in 옛축.예측]
    새예측 = [새축.ID[i] for i in 새축.예측]
    새열 = [c for c in 새예측 if c not in 옛예측]
    회계 = {새축.ID[i]: 새축.열[i].회계연도 for i in 새축.예측}
    끝연도새 = 새축.열[새축.끝예측].회계연도
    구 = g0.get("구조") or {}
    구분들 = {x.get("번호"): x for x in (구.get("매출구분") or []) if isinstance(x, dict)}
    for r, 벌들 in (g0.get("가정") or {}).items():
        if not str(r).isdigit():
            continue
        종류 = _행종류(r, 구)
        n = int(r)
        s = None
        if 종류 == "볼륨증가" and n != 70:
            s = (n - 30) // 8 + 1
        elif 종류 == "수준" and 600 < n < 660:
            s = (n - 600) // 10
        침식, tv배 = _침식표(구분들.get(s) or {}, 새열, 회계, 끝연도새) if s else ({}, None)
        for 시, 벌 in (벌들 or {}).items():
            gg = _g(g0, 시 if 시 in 시나리오들 else "기준")
            _채우기(벌, 종류, 옛예측, 새열, gg, 침식, 매출자본종착.get(시 if 시 in 시나리오들 else "기준"))
            if tv배 is not None and isinstance(벌, dict) and 종류 == "볼륨증가":
                tv = _읽기(벌, "TV")
                벌["TV"] = (1 + (tv if tv is not None else gg)) * tv배 - 1
    채움 = {}
    할 = 구.get("할인") if isinstance(구.get("할인"), dict) else None
    if 연도별WACC and 할 is not None and 할.get("영구WACC") == "따로" and 할.get("연도별WACC") != "사용":
        할["연도별WACC"] = "사용"
        채움["WACC"] = "연도별WACC = 사용 — 늘린 열에서 예측기간 WACC 를 영구기간 WACC 로 걷는다"
    if 종착맞춤:
        채움["종착맞춤"] = _종착맞춤(g0, 새열, 밑마진)
    if 매출자본종착:
        채움["859종착"] = {시: v for 시, v in 매출자본종착.items()}
    배 = 지분배율맞추기(g0)
    if 배:
        채움["지분배율"] = 배
    g0["_연장"] = 채움
    return g0


def 지분배율맞추기(가정):
    """S8R1-N4 — 지분경로(경로 DCF)가 있으면 엔진이 그 축으로 센 배율을 시점가정 배율 칸(970 + 10(k − 1) + 배율)에 시나리오마다 적는다.
    워크북 11번 111 은 그 칸(입력)을 읽고 엔진은 경로를 다시 세므로, 축을 바꾼 사본(연장 · 되돌리기)에서 둘이 한 값이 되게 한다. → {지분: {시나리오: 배율}}"""
    if not 가정.get("지분경로"):
        return {}
    from 엔진.noa import 지분번호                                  # noqa: PLC0415
    낸 = {}
    for 시 in 시나리오들:
        try:
            R = _조용히(엔진.계산, copy.deepcopy(가정), 시)
        except Exception:                                         # noqa: BLE001
            continue
        for k, d in ((R.get("NOA") or {}).get("지분경로") or {}).items():
            번 = "%d" % 지분번호(int(k), "배율")
            벌 = 가정.setdefault("시점가정", {}).get(번)
            if not isinstance(벌, dict) or not any(x in 벌 for x in 시나리오들):
                옛 = 벌.get("공통") if isinstance(벌, dict) else 벌
                벌 = {x: 옛 for x in 시나리오들}
                가정["시점가정"][번] = 벌
            벌[시] = d["배율"]
            낸.setdefault("%s" % k, {})[시] = d["배율"]
    return 낸


def 되돌리기(가정, 연수=5):
    """늘린 회차를 `연수` 의 연간 예측 열로 줄인 사본 — 「연장 전 값」. 수렴연수를 먼저 줄이고 모자라면 상세를 줄인다.
    지금 가정의 짧은 판이다 — 늘릴 때 종착 맞춤이 TV 칸의 비율 줄을 옮겼으면 그 TV 는 그대로 남는다(늘리기 전 원본의 주당은 사본의 249 에 있다).
    축에서 빠진 열의 값은 가정 · 보조시나리오에서 지운다(그 밖의 글 — 서사연결 따위의 열 ID 는 남긴다)."""
    g0 = copy.deepcopy(가정)
    P = g0["기간"]
    상세, 수렴 = int(P["상세추정연수"]), int(P.get("수렴연수") or 0)
    if 연수 >= 상세 + 수렴:
        raise ValueError("이미 %d년입니다 — 줄일 연수(%d)가 더 작아야 합니다" % (상세 + 수렴, 연수))
    빼기 = 상세 + 수렴 - 연수
    줄수렴 = min(수렴, 빼기)
    P["수렴연수"] = 수렴 - 줄수렴
    P["상세추정연수"] = 상세 - (빼기 - 줄수렴)
    if 연수 <= 5:
        P.pop("연장사유", None)
    새 = set(_축(g0).ID)
    for 벌들 in (g0.get("가정") or {}).values():
        for 벌 in (벌들 or {}).values():
            if isinstance(벌, dict):
                for c in [c for c in 벌 if c not in 새]:
                    del 벌[c]
    for x in (g0.get("보조시나리오") or []):
        for 벌 in (((x or {}).get("덧") or {}).get("가정") or {}).values():
            if isinstance(벌, dict):
                for c in [c for c in 벌 if c not in 새]:
                    del 벌[c]
    지분배율맞추기(g0)                                  # S8R1-N4 — 줄인 축으로도 엔진 = 워크북(배율 칸)
    return g0


def 수렴채움(가정):
    """구조.원가줄[].수렴(목표 · 도달연도 · 걸음)대로 그 줄의 비율(매출액비율 — 80 꼴) · 설비 계수(7k1) · 지표 계수(7k8)의 **비운** 예측 열을 채운
    사본과 채운 칸 목록. 적은 칸은 그대로 둔다. 걸음 — 직선(기본) · 기하. 도달 연도 뒤 열과 비운 TV 칸 = 목표."""
    g0 = copy.deepcopy(가정)
    축 = _축(g0)
    예측 = [축.ID[i] for i in 축.예측]
    회계 = {축.ID[i]: 축.열[i].회계연도 for i in 축.예측}
    채운 = []
    for x in ((g0.get("구조") or {}).get("원가줄") or []):
        수렴 = x.get("수렴") if isinstance(x, dict) else None
        if not isinstance(수렴, dict) or not _수(수렴.get("목표")) or not _수(수렴.get("도달연도")):
            continue
        k = x.get("번호")
        산식 = x.get("산식", "매출액비율")
        번 = {"매출액비율": 원가비율번호.get(k), "설비계수": 700 + 10 * k + 1, "지표계수": 700 + 10 * k + 8}.get(산식)
        if 번 is None:
            채운.append("원가 줄 %s(산식 %s) — 수렴 키는 매출액비율 · 설비계수 · 지표계수 줄만 받습니다" % (k, 산식))
            continue
        목표, 도달 = float(수렴["목표"]), int(수렴["도달연도"])
        기하 = 수렴.get("걸음") == "기하"
        for 시, 벌 in ((g0.get("가정") or {}).get(str(번)) or {}).items():
            if not isinstance(벌, dict):
                continue
            적은 = [c for c in 예측 if _수(벌.get(c))]
            if not 적은:
                continue
            기점 = 적은[-1] if not any(not _수(벌.get(c)) for c in 예측[:예측.index(적은[-1])]) else 적은[0]
            L, y0 = float(벌[기점]), 회계[기점]
            for c in 예측[예측.index(기점) + 1:]:
                if _수(벌.get(c)):
                    L, y0 = float(벌[c]), 회계[c]
                    continue
                y = 회계[c]
                if y >= 도달:
                    v = 목표
                elif 기하 and L > 0 and 목표 > 0:
                    v = L * (목표 / L) ** ((y - y0) / float(도달 - y0))
                else:
                    v = L + (목표 - L) * (y - y0) / float(도달 - y0)
                벌[c] = v
                채운.append("가정.%d.%s.%s = %.6g" % (번, 시, c, v))
            if not _수(벌.get("TV")):
                벌["TV"] = 목표
                채운.append("가정.%d.%s.TV = %.6g" % (번, 시, 목표))
    return g0, 채운


def _조용히(f, *a, **k):
    원 = sys.stderr
    sys.stderr = io.StringIO()
    try:
        return f(*a, **k)
    finally:
        sys.stderr = 원


def 판읽기(가정):
    """세 시나리오 — 주당 · 영구 비중 · 네 기준 판정 · 마지막 해 FCFF."""
    낸 = {}
    for 시 in 시나리오들:
        try:
            R = _조용히(엔진.계산, copy.deepcopy(가정), 시)
        except Exception as e:                                # noqa: BLE001
            낸[시] = {"오류": ("%s" % e)[:300]}
            continue
        S = R["요약"]
        끝 = S["마지막예측열"]
        기준표 = R["부수"]["안정성장4기준"]
        판정들 = [x["판정"] for x in 기준표]
        # 재리뷰 S8R1-N2 — ④(증분 ROIC)는 예측 끝 이익이 줄어드는 판에서 엔진이 「해당 없음 — 마진 정상화 구간」 으로 낸다(S9 이월 — 엔진 판정과
        # 도구 판정이 같은 글이다). T3 단서 · 판정은 그 글을 그대로 읽는다
        끝마진 = (R["6.SG&A"]["22"][끝] / R["4.Sales"]["54"][끝]) if R["4.Sales"]["54"][끝] else None
        TV마진 = S.get("영구기간영업이익률")
        낸[시] = {"주당가치": S["주당가치"], "영구가치비중": S["영구가치비중"],
                 "마지막해FCFF": R["2.DCF"]["23"][끝], "마지막예측열": 끝,
                 "마지막해영업이익률": 끝마진, "영구기간영업이익률": TV마진,
                 # S8-01 재리뷰 2 — 종착 맞춤은 마지막 연장 열만 맞춘다. TV 열은 비율 밖 동인(설비 취득원가 · 상각)으로 따로 흐를 수 있어 다시 잰다
                 "영구절벽": (TV마진 - 끝마진) if (_수(TV마진) and _수(끝마진)) else None,
                 "네기준": 판정들,
                 "네기준충족": all(("OK" in ("%s" % x) or "해당 없음" in ("%s" % x)) for x in 판정들)}
    return 낸


def 트리거단서(가정, 밑판):
    """T1 ~ T4 의 단서(사람이 판정한다) — 수명 만료 · 마지막 해 FCFF · 네 기준."""
    줄 = []
    try:
        축 = _축(가정)
        끝연도 = 축.열[축.끝예측].회계연도
    except 기간축오류:
        return 줄
    for x in ((가정.get("구조") or {}).get("매출구분") or []):
        수명 = (x or {}).get("수명") if isinstance(x, dict) else None
        if isinstance(수명, dict) and _수(수명.get("만료연도")) and 수명["만료연도"] > 끝연도:
            n = int(수명.get("침식연수") or 1)
            줄.append("T1 — 매출 구분 %s 의 수명 만료 %d 이 창(%d) 밖 — 후보 연수: 만료 + 침식 %d해 = %d 회계연도까지(상한 10년)"
                     % (x.get("번호"), 수명["만료연도"], 끝연도, n, 수명["만료연도"] + n))
    b = 밑판.get(_적용(가정)) or {}
    if _수(b.get("마지막해FCFF")) and b["마지막해FCFF"] <= 0:
        줄.append("T4 — 마지막 해 FCFF 가 음수(%s) — FCFF 흑자 전환 + 최소 2년이 후보 연수" % "{:,.0f}".format(b["마지막해FCFF"]))
    if b.get("네기준") and not b.get("네기준충족"):
        줄.append("T3 후보 — 마지막 해가 네 기준을 다 채우지 못한다(%s) — 마진 · 투하자본이익률이 종착에 닿는 해" % " · ".join("%s" % x for x in b["네기준"]))
    if (((가정.get("구조") or {}).get("투자") or {}).get("성장규칙") or "없음") != "매출자본비율":
        줄.append("성장 CAPEX 규칙 없음 — 연장 구간의 성장이 공짜가 된다(S5-12 — 구조.투자.성장규칙 = 매출자본비율 · 859). "
                 "표의 늘린 판은 그 성장에 투자를 붙이지 않은 값이다 — 회차에 옮길 때 성장규칙과 859(종착 = 1 ÷ (세후 영업이익률 ÷ RONIC − 운전자본 ÷ 매출))를 둔다")
    if 가정.get("지분경로"):
        줄.append("지분경로가 있다 — 늘린 사본은 엔진이 늘어난 축으로 센 지분 배율을 시점가정 배율 칸에 다시 적었다(워크북 11번 111 이 그 칸을 읽는다 — "
                 "엔진 = 워크북 · S8R1-N4). 자체검사 ⑳ 이 두 값이 갈리면 경보한다")
    return 줄


def _적용(가정):
    v = ((가정.get("스위치") or {}).get("적용시나리오")) or "기준"
    return v if v in 시나리오들 else "기준"


def _퍼(x):
    return "—" if not _수(x) else "%.1f%%" % (x * 100)


def _퍼2(x):
    return "—" if not _수(x) else "%.2f%%" % (x * 100)


def 대조표(가정, 연수들, 사유=None, 종착맞춤=True, 연도별WACC=True, 종착="영구열"):
    밑 = 판읽기(가정)
    P = 가정["기간"]
    N0 = int(P["상세추정연수"]) + int(P.get("수렴연수") or 0)
    판들 = []
    for N in 연수들:
        if N <= N0:
            continue
        try:
            g = 늘리기(가정, N, 사유, 종착맞춤=종착맞춤, 연도별WACC=연도별WACC, 종착=종착)
        except (ValueError, 기간축오류) as e:
            판들.append({"연수": N, "오류": "%s" % e})
            continue
        판 = 판읽기(g)
        for 시 in 시나리오들:
            a, b = (밑.get(시) or {}).get("주당가치"), (판.get(시) or {}).get("주당가치")
            if _수(a) and _수(b) and a:
                판[시]["전후차"] = b / a - 1
        판들.append({"연수": N, "판": 판, "가정": g})
    return {"밑연수": N0, "밑": 밑, "후보": 판들, "단서": 트리거단서(가정, 밑)}


def 표글(표, 사유=None):
    줄 = ["연장 대조표 — 밑 %d년 (S8-01). 연수는 사람이 고른다" % 표["밑연수"]]
    for x in 표["단서"]:
        줄.append("  단서 · " + x)
    줄.append("  %-5s %-4s %14s %8s %8s %15s  %s" % ("연수", "시나리오", "주당가치", "전후 차", "TV 비중", "TV OPM 밑→사본",
                                                "네 기준(① ② ③ ④) · 마지막 해 FCFF"))
    for 시 in 시나리오들:
        b = 표["밑"].get(시) or {}
        줄.append("  %-5s %-4s %14s %8s %8s %15s  %s · %s" % (
            표["밑연수"], 시, "{:,.2f}".format(b["주당가치"]) if _수(b.get("주당가치")) else b.get("오류", "—")[:40], "—",
            _퍼(b.get("영구가치비중")), _퍼2(b.get("영구기간영업이익률")), " / ".join(("%s" % v)[:14] for v in b.get("네기준") or []),
            "{:,.0f}".format(b["마지막해FCFF"]) if _수(b.get("마지막해FCFF")) else "—"))
    절벽 = []
    무효 = []
    for x in 표["후보"]:
        if "오류" in x:
            줄.append("  %-5s 오류 — %s" % (x["연수"], x["오류"]))
            continue
        for 시 in 시나리오들:
            b = x["판"].get(시) or {}
            밑b = 표["밑"].get(시) or {}
            줄.append("  %-5s %-4s %14s %8s %8s %15s  %s · %s" % (
                x["연수"], 시, "{:,.2f}".format(b["주당가치"]) if _수(b.get("주당가치")) else ("%s" % b.get("오류", "—"))[:40],
                ("%+.1f%%" % (b["전후차"] * 100)) if _수(b.get("전후차")) else "—", _퍼(b.get("영구가치비중")),
                "%s→%s" % (_퍼2(밑b.get("영구기간영업이익률")), _퍼2(b.get("영구기간영업이익률"))),
                " / ".join(("%s" % v)[:14] for v in b.get("네기준") or []),
                "{:,.0f}".format(b["마지막해FCFF"]) if _수(b.get("마지막해FCFF")) else "—"))
            if _수(b.get("영구절벽")) and abs(b["영구절벽"]) > 영구절벽폭:
                절벽.append("%d년 %s(마지막 연장 열 %s → TV %s, %+.2f%%p)" % (x["연수"], 시, _퍼2(b.get("마지막해영업이익률")),
                                                                        _퍼2(b.get("영구기간영업이익률")), b["영구절벽"] * 100))
        채움 = (x.get("가정") or {}).get("_연장") or {}
        맞 = (채움.get("종착맞춤") or {}).get("기준")
        if 맞:
            줄.append("        둔화 층 · 기준 · " + 맞)
        if 채움.get("WACC") and x is 표["후보"][0]:
            줄.append("        둔화 층 · " + 채움["WACC"])
        적 = x["판"].get("기준") or {}
        if 사유 and any(t in 사유 for t in ("T1", "T2")) and _수(적.get("전후차")) and abs(적["전후차"]) <= 연장무효폭:
            무효.append(x["연수"])
    밑충족 = (표["밑"].get("기준") or {}).get("네기준충족")
    마지막 = [x for x in 표["후보"] if x.get("연수") == 10 and "판" in x]
    처음 = [x["연수"] for x in 표["후보"] if "판" in x and (x["판"].get("기준") or {}).get("네기준충족")]
    if 밑충족:
        줄.append("  판정 · 밑 %d년이 이미 기준 시나리오의 네 기준을 채운다 — 연장 불필요(T1 · T2 의 사실 근거가 없으면 늘리지 않는다)" % 표["밑연수"])
    elif 처음:
        줄.append("  판정 · 기준 시나리오가 네 기준을 처음 채우는 연수 %d년 — T3 · T4 후보 연수(사람이 근거와 함께 고른다)" % min(처음))
    elif 마지막 and not (마지막[0]["판"].get("기준") or {}).get("네기준충족"):
        줄.append("  판정 · 10년까지 늘려도 기준 시나리오가 네 기준을 다 채우지 못한다 — 기간 문제가 아니라 서사 문제다. 연장을 멈추고 시나리오를 가른다")
    if 절벽:
        줄.append("  영구 절벽 — 늘린 사본(마지막 연장 열과 TV 열의 영업이익률 차 > %.1f%%p): %s. 전후 차에 영구 마진 변화가 섞였다 — "
                 "TV OPM 칸(밑 → 사본)으로 기간 효과와 가른다. 비율 밖 동인(설비 취득원가 · 상각 · 물가연동 금액)이 TV 를 움직인다"
                 % (영구절벽폭 * 100, " · ".join(절벽[:6]) + (" …" if len(절벽) > 6 else "")))
    if 무효:
        줄.append("  판정 · %s 연장(%s년)은 기준 전후 차가 ±%.0f%% 안 — 연장 무효 신호(값을 풀려던 연장이 값을 못 풀었다)"
                 % (사유, " · ".join("%d" % n for n in 무효), 연장무효폭 * 100))
    return "\n".join(줄)


def _쓰기(g, 경로):
    os.makedirs(os.path.dirname(os.path.abspath(경로)) or ".", exist_ok=True)
    with io.open(경로, "w", encoding="utf-8", newline="\n") as f:
        json.dump(g, f, ensure_ascii=False, indent=1)
        f.write("\n")


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(allow_abbrev=False, description="예측기간 연장 후보 — 둔화 층으로 채운 사본과 대조표")
    ap.add_argument("가정")
    ap.add_argument("--연수", default=",".join("%d" % n for n in 후보연수))
    ap.add_argument("--사유", default=None, help="T1 · T2 · T3 · T4 (사본의 기간.연장사유 — 무효 판정에도 쓴다)")
    ap.add_argument("--낼", default=None, help="사본 · 표를 낼 폴더(--수렴채움 이면 낼 파일)")
    ap.add_argument("--되돌리기", type=int, default=None)
    ap.add_argument("--수렴채움", action="store_true")
    ap.add_argument("--종착맞춤", default="켬", choices=("켬", "끔"), help="마지막 연장 열의 영업이익률을 종착 마진에 맞추나(기본 켬)")
    ap.add_argument("--WACC고정", action="store_true", help="늘린 사본에 연도별WACC 를 켜지 않는다")
    ap.add_argument("--종착", default="영구열", choices=("영구열", "기준마진"),
                    help="종착 맞춤의 과녁 — 영구열(밑 판 영구기간 영업이익률 · 기본) · 기준마진(213 → 운영 동종 → 사이클 평균)")
    a = ap.parse_args(argv)
    try:
        g = json.load(io.open(a.가정, encoding="utf-8"))
    except (OSError, ValueError) as e:
        print("입력오류 — %s" % e)
        return 입력오류
    줄기 = os.path.splitext(os.path.basename(a.가정))[0]
    if a.수렴채움:
        새, 채운 = 수렴채움(g)
        print("수렴 채움 — %d칸" % len([x for x in 채운 if x.startswith("가정.")]))
        for x in 채운[:60]:
            print("  " + x)
        if a.낼:
            _쓰기(새, a.낼)
            print("낸 파일: %s" % a.낼)
        return 통과
    if a.되돌리기 is not None:
        try:
            짧은 = 되돌리기(g, a.되돌리기)
        except (ValueError, 기간축오류) as e:
            print("입력오류 — %s" % e)
            return 입력오류
        긴판, 짧은판 = 판읽기(g), 판읽기(짧은)
        print("연장 전 값 — %d년으로 되돌린 사본(같은 엔진). 시점가정 249 에 적는다" % a.되돌리기)
        for 시 in 시나리오들:
            x, y = (짧은판.get(시) or {}).get("주당가치"), (긴판.get(시) or {}).get("주당가치")
            print("  %s  연장 전 %s · 연장 후 %s%s" % (시, "{:,.2f}".format(x) if _수(x) else "—", "{:,.2f}".format(y) if _수(y) else "—",
                                              (" (차 %+.1f%%)" % ((y / x - 1) * 100)) if _수(x) and _수(y) and x else ""))
        if a.낼:
            _쓰기(짧은, os.path.join(a.낼, "%s_되돌림%d.json" % (줄기, a.되돌리기)))
        return 통과
    연수들 = [int(x) for x in a.연수.split(",") if x.strip()]
    try:
        표 = 대조표(g, 연수들, a.사유, 종착맞춤=(a.종착맞춤 == "켬"), 연도별WACC=not a.WACC고정, 종착=a.종착)
    except 기간축오류 as e:
        print("입력오류 — %s" % e)
        return 입력오류
    글 = 표글(표, a.사유)
    print(글)
    if a.낼:
        os.makedirs(a.낼, exist_ok=True)
        밑주당 = {시: (표["밑"].get(시) or {}).get("주당가치") for 시 in 시나리오들}
        for x in 표["후보"]:
            if "가정" not in x:
                continue
            s = x["가정"]
            s.setdefault("시점가정", {})["249"] = dict(밑주당)
            s["시점가정"]["250"] = {시: (x["판"].get(시) or {}).get("주당가치") for 시 in 시나리오들}
            _쓰기(s, os.path.join(a.낼, "%s_연장%d.json" % (줄기, x["연수"])))
        with io.open(os.path.join(a.낼, "연장대조.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump({"밑연수": 표["밑연수"], "밑": 표["밑"], "단서": 표["단서"],
                       "후보": [dict({k: v for k, v in x.items() if k != "가정"}, 채움=(x.get("가정") or {}).get("_연장"))
                              for x in 표["후보"]]}, f, ensure_ascii=False, indent=1, default=str)
        with io.open(os.path.join(a.낼, "연장대조.txt"), "w", encoding="utf-8", newline="\n") as f:
            f.write(글 + "\n")
        print("낸 폴더: %s" % a.낼)
    return 통과


if __name__ == "__main__":
    sys.exit(main())

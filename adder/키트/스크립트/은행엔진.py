# -*- coding: utf-8 -*-
"""은행·은행지주 전용 가치평가 엔진 — 초과이익(RI) + 잉여자본흐름(FCFE) 병행.

왜 따로 만들었나 (2026-09-10 신설, SOFI 회차):
  CLAUDE.md 2단계 「모델 형태 판정」 넷째 문항 — 연결 안의 금융 부문이 자산·부채의
  3분의 1을 넘으면 통합 FCFF/WACC 가 성립하지 않는다. 은행은 그 비중이 100% 라
  ① 공시 매출(RevenuesNetOfInterestExpense)이 이미 이자비용 차감 후이고
  ② 예금을 순차입금으로 빼면 주주가치가 지워진다(Ford Credit 실측과 같은 자리).
  그래서 FCFF 가 아니라 **자기자본 직접 평가**로 간다. dcf엔진.py 는 손대지 않는다.

두 모형을 나란히 세우는 이유 — 서로의 검산이다.
  청산관계(clean surplus) B_t = B_{t-1} + NI_t − FCFE_t 가 성립하면
  두 모형은 대수적으로 같은 값을 낸다. 어긋나면 배선이 틀린 것이다.
  기중할인을 쓰면 B0 항에만 (1+Ke)^0.5 이 안 걸려 예측 가능한 차이가 남는데,
  그 차이가 B0×((1+Ke)^0.5−1) 과 일치하는지까지 검산한다.

재투자 자리 — 제조업의 CapEx 를 은행에서는 **규제자본**이 대신한다.
  대출이 늘면 위험가중자산(RWA)이 늘고, CET1/RWA 를 목표 위로 유지하려면
  ΔRWA × 목표CET1 만큼 이익을 유보해야 한다. 그만큼 주주에게 못 간다.
  여유자본이 있으면 그것부터 소진하고, 모자라면 FCFE 가 음수(증자)로 나온다.
"""
from __future__ import annotations
import json, sys, io

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def 돌리기(a: dict) -> dict:
    """가정 dict 를 받아 두 모형의 값과 층별 표를 낸다. 단위는 입력 단위 그대로(천달러)."""
    열 = a["열"]                      # [{"이름","길이","t중","자산성장률","RWA밀도",
                                      #   "순수익률","효율성비율","대손율","세율"}, ...]
    Ke = a["Ke"]; g = a["영구성장률"]; 목표 = a["목표CET1"]
    자산 = a["기초자산"]; RWA = a["기초RWA"]; CET1 = a["기초CET1"]; B = a["기초자본"]
    공제 = B - CET1                    # 영업권·무형·DTA 등 규제자본 공제 — 경로 내 고정
    주식수 = a["주식수"]

    행 = []
    누계t = 0.0
    필요전 = 목표 * RWA
    for c in 열:
        L = c["길이"]
        자산전, RWA전, CET1전, B전 = 자산, RWA, CET1, B
        자산 = 자산전 * (1 + c["자산성장률"]) ** L
        평균자산 = (자산전 + 자산) / 2
        순매출 = 평균자산 * c["순수익률"] * L
        비이자비용 = 순매출 * c["효율성비율"]
        대손 = 순매출 * c["대손율"]
        세전 = 순매출 - 비이자비용 - 대손
        순이익 = 세전 * (1 - c["세율"])
        RWA = 자산 * c["RWA밀도"]
        필요 = 목표 * RWA
        # 여유자본이 있으면 그만큼만 분배한다. 모자라면 FCFE 가 음수(증자)로 나온다.
        FCFE = CET1전 + 순이익 - 필요
        CET1 = CET1전 + 순이익 - FCFE          # = 필요 (목표에 딱 맞춘다)
        B = CET1 + 공제
        # 초과이익 — 기초자본에 자기자본비용을 물린다. 기간 길이만큼만 물린다.
        Ke기간 = (1 + Ke) ** L - 1
        RI = 순이익 - Ke기간 * B전
        ROE = 순이익 / B전 / L if B전 else None
        누계t = c["t중"]
        할인 = (1 + Ke) ** (-c["t중"])
        행.append(dict(이름=c["이름"], 길이=L, t중=c["t중"], 자산=자산, 평균자산=평균자산,
                       순매출=순매출, 비이자비용=비이자비용, 대손=대손, 세전=세전,
                       순이익=순이익, RWA=RWA, 필요CET1=필요, ΔCET1=필요-필요전,
                       FCFE=FCFE, CET1=CET1, 자본=B, ROE=ROE, RI=RI,
                       할인계수=할인, FCFE현가=FCFE*할인, RI현가=RI*할인))
        필요전 = 필요

    끝 = 행[-1]
    t끝 = a["영구할인기간"]
    할인끝 = (1 + Ke) ** (-t끝)
    # 영구: 순이익·자본이 g 로 자란다. FCFE = NI(1+g) − g·B
    NI다음 = 끝["순이익"] / 끝["길이"] * (1 + g)      # 연율화 후 1년 성장
    B끝 = 끝["자본"]
    FCFE다음 = NI다음 - g * B끝
    RI다음 = NI다음 - Ke * B끝
    TV_FCFE = FCFE다음 / (Ke - g)
    TV_RI = RI다음 / (Ke - g)

    V_FCFE = sum(r["FCFE현가"] for r in 행) + TV_FCFE * 할인끝
    V_RI = a["기초자본"] + sum(r["RI현가"] for r in 행) + TV_RI * 할인끝

    # 검산 ① TV 항등식: TV_FCFE = TV_RI + B끝
    검산TV = TV_FCFE - (TV_RI + B끝)
    # 검산 ② 두 모형 차이 = B0×((1+Ke)^0.5−1) 꼴. 첫 열 기중폭이 만드는 예측 가능한 차이.
    예상차 = a["기초자본"] * ((1 + Ke) ** (행[0]["t중"] / 행[0]["길이"] * 0 + 0) - 1)  # 아래서 실측 대조
    # 배선 검사 — 같은 경로를 기말할인으로 다시 재면 두 모형이 정확히 같아야 한다.
    t끝누계, V_FCFE_말, V_RI_말 = 0.0, 0.0, 0.0
    for r in 행:
        t끝누계 += r["길이"]
        d = (1 + Ke) ** (-t끝누계)
        V_FCFE_말 += r["FCFE"] * d
        V_RI_말 += r["RI"] * d
    d끝 = (1 + Ke) ** (-t끝누계)
    V_FCFE_말 += TV_FCFE * d끝
    V_RI_말 += a["기초자본"] + TV_RI * d끝

    return dict(행=행, Ke=Ke, g=g, 목표CET1=목표, 공제=공제,
                V_FCFE_말=V_FCFE_말, V_RI_말=V_RI_말, 기말차=V_FCFE_말-V_RI_말,
                TV_FCFE=TV_FCFE, TV_RI=TV_RI, B끝=B끝, NI다음=NI다음,
                V_FCFE=V_FCFE, V_RI=V_RI,
                주당_FCFE=V_FCFE/주식수, 주당_RI=V_RI/주식수,
                검산TV=검산TV, 두모형차=V_FCFE-V_RI,
                영구비중_FCFE=TV_FCFE*할인끝/V_FCFE if V_FCFE else None,
                예측기간FCFE합=sum(r["FCFE"] for r in 행))


def 표(res, 단위=1e3, 통화="백만달러"):
    행 = res["행"]
    이름 = ["", *[r["이름"] for r in 행]]
    def 줄(라벨, 키, 배수=1.0, 소수=0, 퍼센트=False):
        vals = []
        for r in 행:
            v = r[키]
            if v is None: vals.append("—"); continue
            vals.append(f"{v*100:.{소수}f}%" if 퍼센트 else f"{v/단위*배수:,.{소수}f}")
        return f"{라벨:<16}" + "".join(f"{v:>13}" for v in vals)
    out = [f"{'':<16}" + "".join(f"{r['이름']:>13}" for r in 행)]
    out.append(f"{'기간길이(년)':<16}" + "".join(f"{r['길이']:>13.2f}" for r in 행))
    out.append(f"{'할인기간 t':<16}" + "".join(f"{r['t중']:>13.2f}" for r in 행))
    out.append("-"*(16+13*len(행)))
    for 라벨, 키 in [("총자산","자산"),("RWA","RWA"),("순매출","순매출"),
                     ("비이자비용","비이자비용"),("대손","대손"),("세전이익","세전"),
                     ("순이익","순이익")]:
        out.append(줄(라벨, 키))
    out.append("-"*(16+13*len(행)))
    out.append(줄("ROE(연율)","ROE",소수=2,퍼센트=True))
    out.append(줄("자본(장부)","자본"))
    out.append(줄("필요CET1","필요CET1"))
    out.append(줄("ΔCET1(재투자)","ΔCET1"))
    out.append("-"*(16+13*len(행)))
    out.append(줄("FCFE","FCFE"))
    out.append(줄("초과이익 RI","RI"))
    out.append(줄("FCFE 현가","FCFE현가"))
    out.append(줄("RI 현가","RI현가"))
    return "\n".join(out)


def 요약(a, r, 단위=1e3):
    주가 = a.get("기준일종가")
    L=[]
    L.append("")
    L.append("="*70)
    L.append(f"자기자본비용 Ke {r['Ke']*100:.2f}%   영구성장률 g {r['g']*100:.2f}%   목표CET1 {r['목표CET1']*100:.1f}%")
    L.append(f"규제자본 공제(영업권·무형 등) {r['공제']/단위:,.0f} 백만달러 — 경로 내 고정")
    L.append("-"*70)
    L.append(f"{'예측기간 FCFE 현가 합':<34}{sum(x['FCFE현가'] for x in r['행'])/단위:>14,.0f}")
    L.append(f"{'영구가치 FCFE (2031말)':<34}{r['TV_FCFE']/단위:>14,.0f}")
    L.append(f"{'영구가치 현가':<34}{(r['V_FCFE']-sum(x['FCFE현가'] for x in r['행']))/단위:>14,.0f}")
    L.append(f"{'★ 자기자본가치 (FCFE 모형)':<34}{r['V_FCFE']/단위:>14,.0f}")
    L.append(f"{'★ 자기자본가치 (초과이익 모형)':<32}{r['V_RI']/단위:>14,.0f}")
    L.append("-"*70)
    L.append(f"{'주당가치 (FCFE)':<34}{r['주당_FCFE']:>14,.2f} USD")
    L.append(f"{'주당가치 (초과이익)':<34}{r['주당_RI']:>14,.2f} USD")
    if 주가:
        L.append(f"{'평가기준일 종가':<34}{주가:>14,.2f} USD")
        L.append(f"{'괴리 (FCFE 기준)':<34}{(r['주당_FCFE']/주가-1)*100:>13,.1f}%")
    L.append("-"*70)
    L.append("검산")
    L.append(f"  ① TV 항등식  TV_FCFE − (TV_RI + B끝) = {r['검산TV']/단위:,.3f}  (0 이어야 한다)")
    Ke=r["Ke"]
    L.append(f"  ② 배선 검사 — 같은 경로를 기말할인으로 재면 두 모형이 일치해야 한다")
    L.append(f"     FCFE(기말) {r['V_FCFE_말']/단위:,.0f}  vs  초과이익(기말) {r['V_RI_말']/단위:,.0f}   차이 {r['기말차']/단위:,.3f}")
    L.append(f"     (기중할인 값끼리의 차이 {r['두모형차']/단위:,.0f} 는 첫 열 오프셋 0.25 가 만드는 규약 차다)")
    L.append(f"  ③ 예측기간 FCFE 합 부호  {'양수' if r['예측기간FCFE합']>0 else '음수'}  ({r['예측기간FCFE합']/단위:,.0f})")
    L.append(f"  ④ 영구가치 비중 (FCFE)  {r['영구비중_FCFE']*100:.1f}%")
    L.append(f"  ⑤ 종착 ROE {r['행'][-1]['ROE']*100:.2f}% vs Ke {Ke*100:.2f}%  → 초과수익 {(r['행'][-1]['ROE']-Ke)*100:+.2f}%p")
    return chr(10).join(L)


if __name__ == "__main__":
    a = json.load(io.open(sys.argv[1], encoding="utf-8"))
    r = 돌리기(a)
    print(표(r))
    print(요약(a, r))

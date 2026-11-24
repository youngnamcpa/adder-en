# -*- coding: utf-8 -*-
"""**투자능력(F 의 도구 판)** — 능력(매출의 상한을 정하는 자산 · 자원)과 투자의 공시 재료를 `_raw/투자능력.json` 으로 낸다. 업종 중립.

    python 스크립트/투자능력.py --공시만                                  # _raw/동인원천.json → _raw/투자능력.json (CP1 — 약정 · 공시)
    python 스크립트/투자능력.py --공시만 --동인원천 _raw/동인원천.json --가정 가정.json -o _raw/투자능력.json

능력(키트 CLAUDE.md 「동인 지도 규칙」) — 생산설비 · 라인(제조) · 매장 · 면적(소매) · 서버 · 데이터센터(클라우드) · 좌석 · 객실(운송 · 숙박) ·
인원(서비스) · 연구개발 파이프라인. 이 판은 공시만 읽는다 — 동인원천(A3) · 곁에 있으면 `_raw/수시공시.json`(국내 주요사항 · 거래소 · 발행공시) ·
`_raw/미국원천.json`(미국 약정 · capex 가이던스 · RPO · 누계 · 본문 조각). 웹(CP2: 능력 · 단위 투자비 발화 · 리드타임 · 램프업)은 F 갈래(깊이 등급 1)의 몫이다.

내는 것 — `"형식": "투자능력/2"`(2026-10-25 FX-B · 가정_스키마.md 「갈래 산출물」의 `_raw/투자능력.json` 꼴 — 공통 머리 + 아래)
  능력매출상한   {전체, 구분별: {구분: {값, 상한종류, 근거}}, 상한종류, 판정순서[], 단위, 근거} — **판정 순서**(유형 하나가 정하지 않는다):
                ① 수주 구조 신호(수주잔고 ÷ 연환산 매출 ≥ 1 → 상한종류 「잔고소화」 후보) ② 공시 가동률(≥ 0.85 「예」 · 0.6~0.85 흔들림 · < 0.6 수요가 정함 ·
                < 0.3 명목 능력 · 기간마다 같은 값 = 실적 역산 · 금액 기준 = 명목 금액 — 뒤 셋은 상한 근거가 아니다 · 인시 기준이면 상한종류 「인시」)
                ③ 숫자 대조(유형자산 ÷ 매출 ≥ 0.4(토지 · 건설중 뺀 판이 있으면 그것) · 유형 CAPEX ÷ 매출 ≥ 0.1 · 유형 CAPEX ÷ 유형 상각 ≥ 2 — 둘 이상 「예」 ·
                하나도 없으면 「해당 없음」. CAPEX ÷ 상각 < 1(증설 없음) · 사업결합이 CAPEX 의 절반을 넘는 해는 유형자산 문턱을 세지 않는다 · CAPEX ÷ 매출 <
                0.03 이면 CAPEX ÷ 상각 문턱을 세지 않는다(작은 기반에서 튄 값)) ④ 문장 · 낱말(**강한 꼴만 · 문장이 숫자를 이기지 않는다** — 외주는
                숫자가 설비 집약이 아닐 때만 · 합작은 「합작 상대에게서 생산물을 받는다」 꼴만 · 자체 생산능력 증설 문장 · 데이터센터는 클라우드 · 수주 ·
                RPO 가 없고 능력 유형이 아니면 역할 투자동인 · 그래도 못 정하면 유형 낱말). 수주 구조가 있으면 가동률 중앙 ≥ 0.9(또는 최대 ≥ 0.9 + 증설
                투자 중)일 때만 「예」, 아니면 「해당 없음(수주 산업)」 상한종류 잔고소화(2026-10-25 FX2-B). 보류여도 멈추지 않는다. 「예」 · 「해당 없음」 은
                근거와 함께 내되 확정은 본선이다
  약정          약정마다 {이름, 금액, 통화, 기준일, 성격(설비취득 · 비용 · 재고공급 · 사용권 · 지분 · 보증 · 보조금조건 · 매출측능력배정 · 혼합 · 미분류),
                기간별, 연결범위, 기준일뒤} — A3 취득약정액 · A3 약정줄(새) · 미국원천 약정 · 수시공시 타법인주식취득(지분)
  능력단위      능력 지표 · A3 생산능력표(새)마다 {…, 역할(매출상한 · 투자동인 · 참고), 가동률기준, 명목성(물리 · 명목금액 · 명목시간 · 실적역산), 변동[], 외주처, 정의,
                시계열{기간: 값}} — (품목 · 단위)로 묶은 한 단위 · 합계 · 소계 · 금액 자산 줄은 빼고 · 상한 「해당 없음」 이어도 「투자동인 · 참고」 로 남긴다(FX4-F)
  단위능력당투자비 (그 해 현금 CAPEX − 사업결합 − 유지 추정(유형 몫 상각)) ÷ 능력 증분 — 같은 해와 앞 해 두 짝, 근거 「유추」 · 독립 「모름」(회사 전체로 잰
                값 — 라인 짝은 본선). 저량 능력 · 명목 금액 능력 · 증분 ≤ 0 은 내지 않는다(까닭을 적는다)
  CAPEX비율     **정본 = 리스 스위치와 짝(2026-10-25 총괄 J1)** — `스위치.리스부채포함` 이 포함(기본)이면 매출대비CAPEX = (유형 + 무형 취득 + 리스로 새로 생긴
                사용권자산) ÷ 매출 · CAPEX대비상각 = (유형 취득 + 사용권 신규) ÷ (유형 몫 상각 + 사용권 상각), 제외면 현금 기준. **기준일 누계 열(1H 등)도**.
                사용권 신규를 못 찾으면 그 열은 현금 기준 + 「사용권 신규 확인 불가 — 리스 짝 미완」 경보. 곁 칸: 현금기준(옛 정본 S5-15 — 비교용) · 리스포함 ·
                발생기준(미지급 설비대금 증감) · 매출대비CAPEX_유형만 · 재무활동설비포함 · 유형자산대매출 · 토지건설중제외_유형자산대매출 ·
                SalesToCapital(_인수자본포함) · 합작몫(J2 — 엔진에 넣지 않는다). 정본과 현금 기준 차이가 매출의 3%p 넘으면 경보(`리스큰회사`)
  프로젝트 · 기집행 공시 투자계획 표(열 조각 · 머리 · 합계 줄은 거른다) · 진행 중 투자(새) · 수시공시 신규시설투자 · 유형자산 취득 결정 → 프로젝트 후보([공시]) ·
                회사 발화 → [회사주장](수주 문장은 거른다 — 투자가 아니다). 칸: 투자범위 · 지분율 · 금액100% · 공동투자자 · 회사몫 · 정정이력 · 이사회승인 ·
                자금출처겹침 · 집행대계획 · 연결범위 · 기준일뒤 · 유니버스중복
  처분 · 미종결인수 · 고객자금(J3 — 적기만) · 공시없음(공시가 「해당사항 없음」이라 적은 것 — 확인불가와 가름) · 원문읽음(A3 요약)
  계약시한      **언제나 목록** — {이름, 끝나는날, 끝꼴(날짜 · 조건), 조건글, 시작일, …}
  값짝          가정이 있고 라인 짝이 이룰 때 — 이 판은 비운다(라인 단위 단위 투자비가 없다)
  열람 · 심화_큐_처리 · 기준일후 · 충돌 · 통지정정 — 웹 몫은 비운다(기준일 뒤 수시공시는 `기준일후` 에)

**값을 정하지 않는다.** 옛 꼴(투자능력/1) 파일은 `옛꼴읽기` 가 새 칸 기본값을 채워 읽는다. 종료 코드는 `종료코드.py` 규약(0 통과 · 2 입력오류).
"""
from __future__ import annotations

import argparse
import datetime
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
try:
    from 종료코드 import 통과, 입력오류                    # noqa: E402
except Exception:                                    # noqa: BLE001
    통과, 입력오류 = 0, 2
ROOT = os.path.dirname(여기)
해당없음 = "해당 없음"
형식 = "투자능력/2"
# 능력 지표(A3 사업지표 표준 이름 → 능력 종류) — 생산설비 · 매장 · 면적 · 좌석 · 객실 · 서버 · 데이터센터 용량 · 회선 · 편대 · 파이프라인(S5-14)
능력지표 = {"생산능력": "생산설비", "매장수": "매장", "면적": "면적", "좌석수": "좌석", "객실수": "객실", "서버수": "서버",
         "데이터센터용량": "용량", "회선수": "회선", "편대": "편대", "파이프라인": "파이프라인"}
# 회사 유형(A3 판정 이름)의 두 묶음 — 능력이 매출 상한인 유형 · 자산 경량 유형. 회사 · 업종 이름이 아니라 유형이다(키트 CLAUDE 「동인 지도 규칙」)
능력유형 = ("설비 집약 제조", "조립 · 경공업 제조", "유통 · 소매", "숙박 · 운송 · 통신", "에너지 · 유틸리티")
자산경량유형 = ("소프트웨어 · 구독", "플랫폼 · 중개", "게임 · 콘텐츠", "금융")
제조유형 = ("설비 집약 제조", "조립 · 경공업 제조")
위탁생산문턱 = 0.08          # 제조 유형인데 유형자산(순장부) ÷ 매출이 이 아래면 위탁 생산(공급사 능력) 의심 — 근거 글에 남긴다(S5-14)
지표묵음연수 = 3             # 능력 지표 · 가동률 · 수주잔고의 마지막 공시가 평가기준일보다 이 연수 넘게 앞서면 쓰지 않는다(S5-14)
# 숫자 대조 문턱(물결 F_지시 · 설계 4-5) — 둘 이상 넘으면 「예」 후보 · 하나도 못 넘고 회색 띠(아래 띠 ~ 문턱)에 든 것이 둘 미만이면 「해당 없음」 후보 ·
# 나머지(하나만 넘음 · 회색 둘 이상)는 혼재 → 문장 · 낱말로. 회색 띠는 유니버스 물결 손 판정(62곳)에서 문턱 바로 밑 설비 회사(완성차 · 조선 · 방산)를 「해당 없음」 으로
# 밀지 않으려고 둔다(2026-10-25 FX-B 실측 — 회색 띠 없이 67% → 띠를 두면 회사 단위 일치가 오른다)
문턱 = {"유형자산대매출": 0.4, "CAPEX대매출": 0.1, "CAPEX대비상각": 2.0}
회색띠 = {"유형자산대매출": 0.25, "CAPEX대매출": 0.05, "CAPEX대비상각": 1.2}
소규모투자 = 0.03           # 유형 CAPEX ÷ 매출이 이 아래면 CAPEX ÷ 상각 문턱을 세지 않는다(작은 기반에서 튄 값 — F13 · F26 · F60)
가동률문턱 = {"예": 0.85, "흔들림": 0.6, "명목": 0.3}
수주문턱 = 1.0              # 수주잔고 ÷ 연환산 매출 — 이 이상이면 잔고 소화 속도가 상한 후보
리스차이경보 = 0.03          # J1(2026-10-25) — 정본(리스 스위치 짝)과 현금 기준의 CAPEX ÷ 매출 차이가 매출의 이만큼을 넘으면 경보(데이터센터 · 리스 많은 회사)
저량능력 = ("매장", "좌석", "객실", "편대", "면적")          # 순증 ≠ 신규(폐점 · 퇴역 · 반납) — 신규 능력을 따로 모르면 단위 투자비를 내지 않는다
약정성격 = ("설비취득", "비용", "재고공급", "사용권", "지분", "보증", "보조금조건", "매출측능력배정", "혼합", "미분류")

# 문장 신호(회사 이름 없는 낱말 꼴) — A3 `유형.신호` 가 있으면 그것을 먼저, 미국원천 본문 조각 · A3 유형 근거 글을 다음으로 본다
외주꼴 = re.compile(r"fabless|팹리스|third[- ]party (?:foundr|manufactur|assembl|wafer)|contract manufactur|"
                 r"outsourc\w* (?:all|substantially all|our|the|most) (?:of (?:our|the) )?(?:manufactur|fabricat|assembl|production|wafer)|"
                 r"위탁\s*(?:생산|제조|가공)|외주\s*(?:생산|가공|제조|조립)|파운드리에\s*위탁", re.I)
합작꼴 = re.compile(r"joint venture\w*.{0,120}(?:wafer|manufactur|\bfab|production capacity)|(?:wafer|manufactur|\bfab\b).{0,120}joint venture|"
                 r"합작\s*(?:법인|투자|회사|공장)?.{0,60}(?:생산|공장|팹|라인)|지분법.{0,40}생산", re.I | re.S)
데이터센터꼴 = re.compile(r"data ?cent(?:er|re)s?.{0,80}(?:capacity|gigawatt|megawatt|\bGW\b|\bMW\b|power)|gigawatt|"
                    r"\b\d+(?:\.\d+)?\s*(?:GW|MW)\b|데이터\s*센터.{0,40}(?:용량|전력|MW|GW|증설)", re.I | re.S)
수주꼴 = re.compile(r"시공사|시공자|우선협상|단일판매|공급계약|수주|낙찰|도급계약\s*체결|EPC")
# 문장의 세기(2026-10-25 FX2-B · R1 · R2) — 외주 · 합작 문장은 「강한 꼴」 일 때만 판정에 쓴다. 고객 OEM · 수탁(남의 것을 만들어 주는 쪽) · 부품 조달 문장은
# 외주 생산이 아니다. 합작은 「지분법 · 합작 상대에게서 생산물을 받는다」 일 때만(합작 법인 이름이 나온다고 합작 생산이 아니다)
강외주꼴 = re.compile(r"fabless|팹리스|outsourc\w* (?:all|substantially all|most|the majority) (?:of )?(?:our |the )?(?:manufactur|fabricat|assembl|production|wafer)|"
                   r"(?:rely|relies|depend\w*) (?:entirely |solely |primarily |exclusively )?on (?:third[- ]party|outside|external) (?:foundr|manufactur|wafer|contract manufactur)|"
                   r"third[- ]party foundr|do not own (?:or operate )?(?:any )?(?:manufactur|fabricat|wafer)|"
                   r"(?:전량|모두|대부분|전부)\s*(?:외주|위탁)\s*(?:생산|가공|제조)?|자체\s*(?:생산|제조)\s*(?:시설|설비|공장)(?:이|은|을|가)?\s*(?:없|보유하지)|"
                   r"생산(?:을|은)?\s*(?:외부|협력사|파운드리)에\s*(?:위탁|맡기)", re.I)
수탁꼴 = re.compile(r"수탁|CMO|CDMO|위탁\s*생산을\s*위한|위탁생산\s*(?:서비스|사업)|contract manufacturing (?:services|organi[sz]ation)|"
                 r"(?:our|its) role as an? OEM|OEM\s*(?:사|업체|고객|매출|자동차|부품|장비|PART)|완성차\s*OEM|글로벌\s*(?:주요\s*)?OEM", re.I)
강합작꼴 = re.compile(r"(?:obtain|purchas|source|buy|bought|suppl|receiv)\w*.{0,80}(?:from|through) (?:our |the |its |these |those )?(?:joint venture|equity[- ]method|affiliat)|"
                   r"joint venture\w*.{0,120}(?:provide|supply|supplies|sell|sold)\w* (?:us|to us|the company|wafer|output)|"
                   r"(?:지분법|합작\s*(?:법인|회사|투자))[^.。]{0,60}(?:로부터|에서|통해)[^.。]{0,30}(?:공급|매입|구매|조달)", re.I | re.S)
클라우드꼴 = re.compile(r"cloud (?:services?|platform|infrastructure|computing|revenue)|\bIaaS\b|GPUaaS|클라우드|AI\s*(?:인프라|컴퓨팅)\s*(?:임대|서비스|매출)", re.I)
부문클라우드꼴 = re.compile(r"클라우드|엔터프라이즈|cloud|enterprise|\bIDC\b|데이터\s*센터|data ?cent", re.I)      # 부문 이름(B2B IT · 클라우드 부문)
증설문장꼴 = re.compile(r"(?:expand|increas|doubl|add|grow)\w*[^.]{0,60}?(?:our |its )?(?:annual )?(?:production|manufacturing) capacity|"
                    r"(?:production|manufacturing) capacity[^.]{0,40}(?:from|to) (?:approximately )?\d|"
                    r"생산\s*능력(?:을|의)?\s*(?:증설|확대|확충|두\s*배)|(?:증설|확충)[^.。]{0,30}생산\s*능력", re.I)
유동능력꼴 = re.compile(r"유동적으로\s*(?:변동|조절)|조절\s*(?:및|과|·)?\s*확대할\s*수|탄력적으로\s*(?:조정|조절)|"
                    r"flexibl\w* (?:adjust|scale|expand) (?:our |the )?(?:production|manufacturing) capacity", re.I)
수요연동꼴 = re.compile(r"(?:생산\s*대수|생산량|생산\s*계획|물량)에\s*연동|고객(?:사)?의?\s*(?:생산|발주|주문)\s*(?:계획|물량|일정)에\s*(?:따라|연동)|"
                    r"in line with (?:our )?customers?'? (?:production|build) (?:volumes|schedules)", re.I)
공시제목꼴 = re.compile(r"주요사항보고|주요경영사항|기타경영사항|자율공시|기재정정|정정신고|투자판단관련|자회사의\s*주요|^\s*\[|"
                    r"^\s*(?:신규시설투자등?|유형자산\s*(?:취득|양수)\s*결정)\s*$")
# 부문 이름 꼴(구분별 판정 — 부문 숫자가 없을 때) — 서비스 · 금융 · 유통 성격 부문은 설비 능력이 상한이 아니다 · 공통 · 조정 줄은 부문이 아니다
경량부문꼴 = re.compile(r"금융|캐피탈|카드|보험|리스|서비스|설치|용역|플랫폼|핀테크|커머스|광고|콘텐츠|소프트웨어|무역|상사|유통|리조트|급식|식음|식자재|외식|패션|임대|컨설팅|"
                    r"\bICT\b|\bIT\b|IT\s*서비스|디지털|software|services?\b|financ|consult|subscription|platform|advertis", re.I)
수주부문꼴 = re.compile(r"건설|토건|토목|건축|construction", re.I)       # 외주 시공 · 수주 소화(설비 능력이 상한이 아니다)
기타부문꼴 = re.compile(r"^\s*(?:기타|그\s*밖|other|all other)", re.I)  # 주력 능력이 아닌 묶음
비부문꼴 = re.compile(r"공통|조정|내부\s*거래|제거|corporate|elimination|reconcil|unallocated", re.I)
고객꼴 = re.compile(r"주요\s*고객|고객\s*\(|customer", re.I)   # 영업부문 주석의 고객 정보 표(부문이 아니다)
고객법인꼴 = re.compile(r"[와과]\s*그\s*종속기업", re.I)   # 「○○와 그 종속기업」 — 그것만 있으면 고객 표, 다른 부문과 함께면 자회사 부문
합계꼴 = re.compile(r"^\s*(?:합\s*계|소\s*계|총\s*계|계)\s*$|합\s*계")
_부문군말 = re.compile(r"사업\s*부문|사업부|부문|segment|사업|division", re.I)
_머리말 = {"구분", "합계", "합 계", "소계", "계", "총계", "금 액", "금액", "비고", "투자기간", "향후투자액", "기투자액", "총투자액", "계획명칭", "사업부문",
        "투자대상자산", "투자효과", "투자대상", "자산형태", "단위", "기타 합계"}
_자산말 = r"건물|구축물|기계장치|비품|토지|공구|기구|차량|운반구|금형|설비|유형자산|무형자산|외|등|및|기타"
_효과말 = re.compile(r"(?:증대|향상|개선|효율화?|확보|대응|강화)(?:\s*등)?$")
_기간꼴 = re.compile(r"(?:19|20)\d{2}|['’]\d{2}\s*년|\d{2,4}\s*년|제\s*\d+\s*기|~|상반기|하반기|분기")


def _수(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        m = re.fullmatch(r"\s*(-?[\d,]+(?:\.\d+)?)\s*", v)
        return float(m.group(1).replace(",", "")) if m else None
    return None


def _fy(d):
    return {c: v for c, v in sorted((d or {}).items()) if isinstance(c, str) and c.startswith("FY") and isinstance(v, (int, float))} \
        if isinstance(d, dict) else {}


def _열수(d):
    """{기간: 수} — FY 열과 중간(1H · 9M 등) 열 모두."""
    return {c: float(v) for c, v in sorted((d or {}).items()) if isinstance(c, str) and isinstance(v, (int, float)) and not isinstance(v, bool)} \
        if isinstance(d, dict) else {}


def 상각분모(원):
    """FX4-F D1 — CAPEX ÷ 상각의 분모를 기간마다 고른다 → ({기간: 값}, {기간: "유형몫" | "579−무형" | "579"}, [뺀 기간 글]).
    유형 몫 상각(A3 상각유형)은 같은 기간 총 상각(579 — 유형 + 사용권 + 무형)의 0.05 ~ 1.02 배일 때만 쓴다 — 밖이면 자산 종류별 표의 자릿수 · 열 · 출처가
    어긋난 것(자동차 회사 FY2025 유형 몫 41,380 ↔ 579 5,016,484 → CAPEX ÷ 상각 202). 유형 몫이 없거나 뺀 기간은 579 − 무형 상각(있으면) · 579 로 내린다
    (종전에는 유형 몫이 한 해라도 있으면 다른 해의 분모가 비었다)."""
    유 = 원.get("유형자산") if isinstance(원.get("유형자산"), dict) else {}
    실 = _열수(유.get("상각유형") if isinstance(유.get("상각유형"), dict) else {})
    총 = _열수((원.get("원천행") or {}).get("579"))
    무 = _열수(유.get("상각무형") if isinstance(유.get("상각무형"), dict) else {})
    값, 뜻, 뺀 = {}, {}, []
    for c, v in 실.items():
        t = 총.get(c)
        if t and not (0.05 <= v / t <= 1.02):
            뺀.append("%s(%.3f)" % (c, v / t))
            continue
        값[c], 뜻[c] = v, "유형몫"
    for c, t in 총.items():
        if c in 값 or not t:
            continue
        if 무.get(c) is not None and 0 < t - 무[c] < t:
            값[c], 뜻[c] = t - 무[c], "579−무형"
        else:
            값[c], 뜻[c] = t, "579"
    return 값, 뜻, 뺀


def _해(c):
    m = re.match(r"FY(\d{4})", c or "")
    if m:
        return int(m.group(1))
    m = re.match(r"(?:\d[HQM]|[HQ]\d)(\d{2})", c or "")
    return 2000 + int(m.group(1)) if m else None


def _앞(c):
    y = _해(c)
    return ("FY%d%s" % (y - 1, c[6:])) if (y and (c or "").startswith("FY")) else None


def _유형판정(원):
    유 = 원.get("유형")
    if isinstance(유, dict):
        return 유.get("판정") or []
    return 유 if isinstance(유, list) else []


# ── 금액 단위 ────────────────────────────────────────────────────────────────
_배말 = (("조", 1e12), ("십억", 1e9), ("억", 1e8), ("백만", 1e6), ("천", 1e3), ("billion", 1e9), ("million", 1e6), ("thousand", 1e3))


def _단위배(단위):
    u = ("%s" % (단위 or "")).strip().lower().replace(" ", "")
    if not u:
        return None, None
    통 = "KRW" if ("원" in u or "krw" in u) else ("USD" if ("달러" in u or "usd" in u or "$" in u) else
                                              ("TWD" if ("대만" in u or "twd" in u) else ("EUR" if ("유로" in u or "eur" in u) else None)))
    for 말, b in _배말:
        if 말 in u:
            return b, 통
    return 1.0, 통


def 환산(값, 단위, 기준단위):
    """값(단위) → 기준단위(동인원천 `단위` — 백만원 · 백만달러 …)의 수. 통화가 다르면 None(환산하지 않는다)."""
    v = _수(값)
    if v is None:
        return None
    if not 단위:
        return v
    b1, c1 = _단위배(단위)
    b0, c0 = _단위배(기준단위)
    if b1 is None or b0 is None or (c1 and c0 and c1 != c0):
        return None
    return v * b1 / b0


def 통화(기준단위):
    return _단위배(기준단위)[1] or ""


# ── 원천 읽기 ────────────────────────────────────────────────────────────────
def 원천읽기(동인원천경로):
    """동인원천 곁의 `수시공시.json` · `미국원천.json`(원천 수집 — 계약 4-1 · 4-2)을 읽는다. 없으면 빈 dict(옛 동작)."""
    낸 = {}
    폴더 = os.path.dirname(os.path.abspath(동인원천경로))
    for 키 in ("수시공시", "미국원천"):
        p = os.path.join(폴더, 키 + ".json")
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(d, dict):
            낸[키] = d
    return 낸


def _기준해(원):
    """재무 쪽 해 — 동인원천 머리의 재무기준일 F(없으면 옛 파일 · 평가기준일 = F)의 해(날짜 둘 2026-10-25)."""
    return _해("FY" + ("%s" % (원.get("재무기준일") or 원.get("평가기준일") or ""))[:4]) or datetime.date.today().year


def _연환산배(원, c):
    """중간 열의 연환산 배수(A3 `반기연환산` → 없으면 1H = 2 · 9M = 4/3 · Q = 4)."""
    배 = (원.get("반기연환산") or {}).get(c) if isinstance(원.get("반기연환산"), dict) else None
    if isinstance(배, (int, float)) and 배 > 0:
        return float(배)
    if (c or "").startswith("FY"):
        return 1.0
    m = re.match(r"(\d)([HQM])", c or "")
    if m:
        n, k = int(m.group(1)), m.group(2)
        return {"H": 12.0 / (6 * n), "Q": 12.0 / (3 * n), "M": 12.0 / n}[k] if n else None
    return None


def _최근FY(d):
    k = sorted(c for c in d if isinstance(c, str) and c.startswith("FY"))
    return k[-1] if k else None


# ── ③ 숫자 대조 ──────────────────────────────────────────────────────────────
def _종류별순장부(원, 꼴, c):
    """유형자산 종류별(이름에 꼴이 든 것)의 순장부(c) 합 — 없으면 None."""
    합, 있음 = 0.0, False
    for 이름, 측 in (((원.get("유형자산") or {}).get("종류별") or {}) if isinstance((원.get("유형자산") or {}).get("종류별"), dict) else {}).items():
        if re.search(꼴, 이름) and isinstance(측, dict):
            v = (측.get("순장부") or {}).get(c) if isinstance(측.get("순장부"), dict) else None
            if isinstance(v, (int, float)):
                합 += v
                있음 = True
    return 합 if 있음 else None


def 숫자대조(원, 열=None):
    """→ {열, 유형자산대매출, 토지건설중제외, CAPEX대매출, CAPEX유무형대매출, CAPEX대비상각, 상각분모, 넘음[], 뺀까닭[], 결과(예 · 해당 없음 · 혼재 · 모름), 근거}.
    최근 회계연도(매출 · 유형자산이 있는 해)로 잰다. 중간 열을 주면 매출을 연환산한다."""
    재 = 원.get("재무시계열") or {}
    유 = 원.get("유형자산") if isinstance(원.get("유형자산"), dict) else {}
    if 열 is None:
        후 = sorted(c for c, v in 재.items() if c.startswith("FY") and isinstance(v, dict) and v.get("매출") and
                   (v.get("유형자산") is not None or v.get("CAPEX") is not None))
        열 = 후[-1] if 후 else None
    낸 = {"열": 열, "유형자산대매출": None, "토지건설중제외": None, "CAPEX대매출": None, "CAPEX유무형대매출": None, "CAPEX대비상각": None,
         "상각분모": "", "넘음": [], "뺀까닭": [], "결과": "모름", "근거": ""}
    if not 열:
        낸["근거"] = "매출 · 유형자산이 있는 회계연도가 없다"
        return 낸
    v = 재.get(열) or {}
    매 = _수(v.get("매출"))
    배 = _연환산배(원, 열) or 1.0
    if not 매:
        낸["근거"] = "%s 매출이 없다" % 열
        return 낸
    연매 = 매 * 배
    유형 = _수(v.get("유형자산"))
    capex = _수(v.get("CAPEX"))
    if capex is None:
        capex = _자산군CAPEX(원, 열)
    무형 = _수(v.get("무형취득")) or 0.0
    결합 = _수(v.get("사업결합취득")) or 0.0
    _분, _뜻, _ = 상각분모(원)
    상 = _분.get(열)
    낸["상각분모"] = {"유형몫": "유형 몫 상각(A3 상각유형 — 사용권 · 무형 상각 제외 · 총 상각과 검산)",
                   "579−무형": "579 − 무형 상각(사용권 상각 포함 — 비율이 조금 낮게 나온다)",
                   "579": "579(사용권 · 무형 상각 포함 — 유형 몫을 못 갈랐다 · 비율이 낮게 나온다)"}.get(_뜻.get(열), "")
    if 유형 is not None:
        낸["유형자산대매출"] = 유형 / 연매
        토지 = _종류별순장부(원, r"^토지", 열)
        건설 = (_열수(유.get("건설중인자산")) if isinstance(유.get("건설중인자산"), dict) else {}).get(열)
        if 건설 is None:
            건설 = _종류별순장부(원, r"건설중", 열)
        if 토지 is not None or 건설 is not None:
            남 = 유형 - (토지 or 0.0) - (건설 or 0.0)
            if 남 < 0 or 남 > 유형 * 1.0001:
                낸["뺀까닭"].append("토지 · 건설중을 뺀 값이 음수거나 유형자산보다 크다(종류별 표와 단위 · 범위가 다름) — 뺀 판을 쓰지 않았다")
            else:
                낸["토지건설중제외"] = 남 / 연매
    if capex is not None:
        낸["CAPEX대매출"] = capex / 매
        낸["CAPEX유무형대매출"] = (capex + 무형) / 매
        if 상:
            낸["CAPEX대비상각"] = capex / 상
    재고 = 낸["토지건설중제외"] if 낸["토지건설중제외"] is not None else 낸["유형자산대매출"]
    잰수 = sum(1 for x in (재고, 낸["CAPEX대매출"], 낸["CAPEX대비상각"]) if x is not None)
    if 재고 is not None and 재고 >= 문턱["유형자산대매출"]:
        if 낸["CAPEX대비상각"] is not None and 낸["CAPEX대비상각"] < 1:
            낸["뺀까닭"].append("유형자산 ÷ 매출 %.2f 는 넘지만 CAPEX ÷ 상각 %.2f < 1 — 증설이 없는 묵은 자산" % (재고, 낸["CAPEX대비상각"]))
        elif capex is not None and 결합 > 0.5 * capex:
            낸["뺀까닭"].append("유형자산 ÷ 매출 %.2f 는 넘지만 사업결합 취득이 CAPEX 의 절반을 넘는다 — 인수로 늘어난 자산" % 재고)
        else:
            낸["넘음"].append("유형자산 ÷ 매출 %.2f%s ≥ %.1f" % (재고, "(토지 · 건설중 뺌)" if 낸["토지건설중제외"] is not None else "", 문턱["유형자산대매출"]))
    if 낸["CAPEX대매출"] is not None and 낸["CAPEX대매출"] >= 문턱["CAPEX대매출"]:
        낸["넘음"].append("유형 CAPEX ÷ 매출 %.3f ≥ %.1f" % (낸["CAPEX대매출"], 문턱["CAPEX대매출"]))
    if 낸["CAPEX대비상각"] is not None and 낸["CAPEX대비상각"] >= 문턱["CAPEX대비상각"]:
        if 낸["CAPEX대매출"] is not None and 낸["CAPEX대매출"] < 소규모투자:
            낸["뺀까닭"].append("CAPEX ÷ 상각 %.2f 는 넘지만 CAPEX ÷ 매출 %.3f < %.2f — 작은 기반에서 튄 값" % (낸["CAPEX대비상각"], 낸["CAPEX대매출"], 소규모투자))
        else:
            낸["넘음"].append("CAPEX ÷ 유형 상각 %.2f ≥ %.0f" % (낸["CAPEX대비상각"], 문턱["CAPEX대비상각"]))
    n = len(낸["넘음"])
    회색 = []
    for 키, 값 in (("유형자산대매출", 재고), ("CAPEX대매출", 낸["CAPEX대매출"]), ("CAPEX대비상각", 낸["CAPEX대비상각"])):
        if 값 is not None and 회색띠[키] <= 값 and not any(키[:4] in x.replace(" ", "")[:12] for x in 낸["넘음"]):
            if 키 == "CAPEX대비상각" and 낸["CAPEX대매출"] is not None and 낸["CAPEX대매출"] < 소규모투자:
                continue                                  # 작은 기반에서 튄 CAPEX ÷ 상각은 회색으로도 세지 않는다
            회색.append("%s %.3f" % (키, 값))
    낸["회색"] = 회색
    if n >= 2:
        낸["결과"] = "예"
    elif n == 0 and 잰수 >= 2 and len(회색) < 2:
        낸["결과"] = 해당없음
    elif 잰수 >= 2:
        낸["결과"] = "혼재"
    낸["근거"] = "%s — %s%s%s" % (열, " · ".join(낸["넘음"]) or "문턱 넘음 없음(잰 비율 %d)" % 잰수,
                                (" · 회색 띠: " + " · ".join(회색)) if 회색 else "",
                                (" · 뺌: " + " · ".join(낸["뺀까닭"])) if 낸["뺀까닭"] else "")
    return 낸


def _자산군CAPEX(원, c):
    """A3 `재무시계열[c].CAPEX구성` — 유형취득이 없으면 자산군별 현금 취득 줄의 합(F18)."""
    구 = ((원.get("재무시계열") or {}).get(c) or {}).get("CAPEX구성")
    if not isinstance(구, dict):
        return None
    if _수(구.get("유형취득")) is not None:
        return _수(구["유형취득"])
    군 = 구.get("자산군별")
    if isinstance(군, dict):
        vs = [_수(v) for v in 군.values() if _수(v) is not None]
        return sum(vs) if vs else None
    return None


# ── ② 공시 가동률 ────────────────────────────────────────────────────────────
def 가동률판정(원):
    """A3 `가동률공시[]`(공장 · 품목별) → {"줄": [{이름, 값, 기간, 기준, 판정, 상한종류, 근거}], "요약": 예 · 해당 없음 · 흔들림 · 모름, "종류"}.
    판정: ≥ 0.85 예(1 넘으면 정규시간 능력이라 단단하지 않음) · 0.6~0.85 흔들림 · 0.3~0.6 해당 없음(수요) · < 0.3 해당 없음(명목 능력) ·
    기간마다 같은 값 = 실적 역산(근거 아님) · 금액 기준 = 명목 금액(근거 아님)."""
    가 = 원.get("가동률공시")
    줄 = []
    if not isinstance(가, list):
        return {"줄": [], "요약": "모름", "종류": "", "공시없음": isinstance(가, str) and "확인했고 없었다" in 가,
                "중앙": None, "최대": None, "최소": None, "끝최소": None, "창": 0, "약함": False}
    기준해 = _기준해(원)
    # FX4-F D2 — 능력 표의 단위가 「설비 가동시간」(공장 총가동시간 · 가동시간 — 인시 · MH 가 아닌 시간)인 품목의 가동률은 설비가 돌면 차는
    # 시간이라 판매 상한 근거가 아니다(방산 사업장 꼴 94% → 「예」 오판). 그 품목과 이름이 짝인 가동률 줄은 판정에서 뺀다
    시간품목 = [("%s" % (t.get("품목") or "")) for t in (원.get("생산능력표") or []) if isinstance(원.get("생산능력표"), list) and isinstance(t, dict)
            and re.search(r"가동\s*시간|^\s*시간\s*$|hours?", "%s" % (t.get("단위") or ""), re.I)
            and not re.search(r"M\s*/?\s*H|인\s*·?\s*시|공수|man", "%s" % (t.get("단위") or ""), re.I)]
    for x in 가:
        if not isinstance(x, dict) or not isinstance(x.get("값"), dict):
            continue
        값 = {c: (v / 100.0 if v > 3 else v) for c, v in _열수(x["값"]).items()}
        if not 값:
            continue
        열 = sorted(값, key=lambda c: (_해(c) or 0, 0 if c.startswith("FY") else 1))
        끝 = 열[-1]
        v = 값[끝]
        기준 = ("%s" % (x.get("기준") or "")).strip() or "모름"
        이름 = x.get("공시이름") or x.get("이름") or ""
        y = {"이름": 이름, "값": round(v, 4), "기간": 끝, "기준": 기준, "판정": None, "상한종류": "인시" if 기준 == "인시" else "설비", "근거": ""}
        끝해 = _해(끝)
        if 끝해 and 기준해 - 끝해 > 지표묵음연수:
            y["근거"] = "가동률의 마지막 공시(%s)가 %d년 넘게 묵었다" % (끝, 지표묵음연수)
        elif 기준 == "금액":
            y["근거"] = "금액 기준 능력(명목 금액 — 판가로 부푼다) — 상한 근거 아님"
        elif 시간품목 and _같은이름(이름, 시간품목):
            y["근거"] = "설비 가동시간 기준 능력(「%s」 — 명목 시간: 설비가 돌면 차는 시간이라 판매 상한 근거 아님 · D2)" % _같은이름(이름, 시간품목)[:30]
        elif len(값) >= 2 and max(값.values()) - min(값.values()) < 0.0005:
            y["근거"] = "가동률이 기간마다 %.1f%% 로 같다 — 실적 ÷ 고정 가동률로 역산한 능력(상한 근거 아님)" % (v * 100)
        elif v < 가동률문턱["명목"]:
            y["판정"], y["근거"] = 해당없음, "가동률 %.1f%%(%s) < 30%% — 명목 능력(실적과 따로 논다)" % (v * 100, 끝)
        elif v >= 가동률문턱["예"]:
            y["판정"] = "예"
            y["근거"] = "가동률 %.1f%%(%s)%s" % (v * 100, 끝, " — 100%% 를 넘는다: 정규시간 능력이라 상한이 단단하지 않다(흔들림)" if v > 1.0 else "")
        elif v >= 가동률문턱["흔들림"]:
            y["판정"], y["근거"] = "흔들림", "가동률 %.1f%%(%s) — 60~85%%: 수요가 정할 공산(사람 확인)" % (v * 100, 끝)
        else:
            y["판정"], y["근거"] = 해당없음, "가동률 %.1f%%(%s) < 60%% — 수요가 판매량을 정한다" % (v * 100, 끝)
        줄.append(y)
    # 묶음 셈(2026-10-25 FX2-B · R13) — 판정이 난 줄 가운데 **가장 최근 두 기간**(직전 회계연도 · 기준일 누계)의 줄만 본다(묵은 해 줄이 섞여
    # 요약을 흔들지 않게). 사업의 내용 **문장에서 뽑은 줄**(표가 아님)만 있으면 약한 근거 — 요약은 흔들림(판정을 정하지 않는다)
    for y in 줄:
        y["문장줄"] = ("%s" % y["이름"]).startswith("문장")
    # 여러 법인의 줄이 섞여 있고(이름 첫 낱말이 법인 이름) 그 가운데 대상 회사 자체 줄이 있으면, 묶음 셈은 자체 줄로만 한다 — 종속 · 상장 자회사
    # 라인은 그 회사의 판정이다(지주 · 연결 회사가 남의 라인 가동률로 판정되지 않게 · 줄은 그대로 남긴다)
    회사명 = _법인말(원.get("회사"))
    주체들 = {_법인말(("%s" % y["이름"]).split()[0]) for y in 줄 if ("%s" % y["이름"]).split()}
    자기만 = bool(회사명) and len(주체들) >= 2 and 회사명 in 주체들
    for y in 줄:
        y["남의줄"] = bool(자기만 and _법인말(("%s" % y["이름"]).split()[0] if ("%s" % y["이름"]).split() else "") != 회사명)
    판줄 = [y for y in 줄 if y["판정"] and not y["남의줄"]]

    def _키(y):
        return (_해(y["기간"]) or 0, 0 if ("%s" % y["기간"]).startswith("FY") else 1)
    해순 = sorted({_키(y) for y in 판줄})
    최근 = set(해순[-2:])
    창 = [y for y in 판줄 if _키(y) in 최근]
    값들 = sorted(min(y["값"], 1.3) for y in 창)
    중앙 = (값들[len(값들) // 2] if len(값들) % 2 else (값들[len(값들) // 2 - 1] + 값들[len(값들) // 2]) / 2) if 값들 else None
    약함 = bool(창) and all(y["문장줄"] for y in 창)
    판들 = [y["판정"] for y in 창]
    if not 판들:
        요약 = "모름"
    elif 약함:
        요약 = "흔들림"
    elif "예" in 판들:
        요약 = "예"
    elif all(p == 해당없음 for p in 판들):
        요약 = 해당없음
    elif "흔들림" in 판들:
        요약 = "흔들림"
    else:
        요약 = "모름"
    예줄 = [y for y in 창 if y["판정"] == "예"]
    종류 = "인시" if 예줄 and all(y["상한종류"] == "인시" for y in 예줄) else ("설비" if 예줄 else "")
    끝값 = [min(y["값"], 1.3) for y in 창 if 해순 and _키(y) == 해순[-1]]
    return {"줄": 줄, "요약": 요약, "종류": 종류, "공시없음": False, "중앙": 중앙, "최대": (값들[-1] if 값들 else None),
            "최소": (값들[0] if 값들 else None), "끝최소": (min(끝값) if 끝값 else None), "창": len(창), "약함": 약함}


def _법인말(s):
    """법인 이름 맞추기 — ㈜ · (주) · 주식회사 · 괄호 속 종목코드 · 띄어쓰기를 뺀다."""
    t = re.sub(r"\(\d{6}\)|㈜|\(주\)|주식회사|\s+", "", "%s" % (s or ""))
    return t.lower()


# ── ① 수주 구조 신호 ─────────────────────────────────────────────────────────
def 수주신호(원, 원천들=None):
    """→ {있음, 비(잔고 ÷ 연환산 매출), 근거}. 수주잔고표(A3 새) · 유형.신호 · 사업지표 수주잔고(국내 · 미국 RPO) · 미국원천 RPO 를 본다."""
    원천들 = 원천들 or {}
    재 = 원.get("재무시계열") or {}
    기준단위 = 원.get("단위") or ""
    fy = _최근FY({c: v for c, v in 재.items() if isinstance(v, dict) and v.get("매출")})
    연매 = _수((재.get(fy) or {}).get("매출")) if fy else None
    중 = [c for c, v in 재.items() if not c.startswith("FY") and isinstance(v, dict) and v.get("매출")]
    if 중:
        c = sorted(중, key=lambda k: _해(k) or 0)[-1]
        배 = _연환산배(원, c)
        if 배 and (_해(c) or 0) >= (_해(fy) or 0):
            연매 = _수(재[c]["매출"]) * 배
    후 = []
    표 = 원.get("수주잔고표")
    if isinstance(표, list) and 표:
        합 = 0.0
        for x in 표:
            if isinstance(x, dict):
                v = 환산(x.get("잔고"), x.get("단위"), 기준단위)
                if v:
                    합 += v
        if 합 > 0:
            후.append((합, "A3 수주잔고표 %d줄" % len(표)))
    신 = ((원.get("유형") or {}).get("신호") or {}) if isinstance(원.get("유형"), dict) else {}
    if isinstance(신, dict) and _수(신.get("수주잔고÷매출")):
        return {"있음": _수(신["수주잔고÷매출"]) >= 수주문턱, "비": _수(신["수주잔고÷매출"]), "근거": "A3 유형.신호 수주잔고 ÷ 매출 %.2f" % _수(신["수주잔고÷매출"])}
    지 = ((원.get("사업지표") or {}).get("수주잔고")) if isinstance(원.get("사업지표"), dict) else None
    if isinstance(지, dict) and isinstance(지.get("값"), dict) and 지["값"]:
        c = sorted(지["값"], key=lambda k: _해(k) or 0)[-1]
        if (_기준해(원) - (_해(c) or 0)) <= 지표묵음연수:
            v = 환산(지["값"][c], 지.get("단위"), 기준단위)
            if v:
                후.append((v, "사업지표 수주잔고 %s(%s)" % (c, 지.get("공시이름") or "")))
    rpo = (원천들.get("미국원천") or {}).get("RPO") if isinstance(원천들.get("미국원천"), dict) else None
    if isinstance(rpo, dict) and _수(rpo.get("값")):
        v = 환산(rpo["값"], "USD", 기준단위)
        if v:
            후.append((v, "미국원천 RPO %s" % (rpo.get("기준일") or "")))
    if 후 and 연매:
        v, 출 = max(후, key=lambda t: t[0])
        비 = v / 연매
        return {"있음": 비 >= 수주문턱, "비": 비, "근거": "%s ÷ 연환산 매출 = %.2f년치" % (출, 비)}
    if "수주 산업" in _유형판정(원):
        return {"있음": True, "비": None, "근거": "A3 유형 판정에 수주 산업(잔고 금액 없음)"}
    return {"있음": False, "비": None, "근거": ""}


# ── ④ 문장 신호 ──────────────────────────────────────────────────────────────
def 문장신호(원, 원천들=None):
    """→ {"외주": [...], "합작": [...], "데이터센터": [...], "사업의내용찾음": bool|None} — 짧은 조각(80자)만 남긴다."""
    원천들 = 원천들 or {}
    낸 = {"외주": [], "합작": [], "데이터센터": [], "사업의내용찾음": None, "외주강함": False, "합작강함": False, "클라우드": False,
         "유동능력": [], "수요연동": [], "강한외주": [], "강한합작": [], "자체증설": []}
    신 = ((원.get("유형") or {}).get("신호") or {}) if isinstance(원.get("유형"), dict) else {}
    if isinstance(신, dict):
        for 키, 칸 in (("외주", "외주생산문장"), ("합작", "합작생산문장"), ("데이터센터", "데이터센터문장")):
            낸[키] += [("%s" % s)[:80] for s in (신.get(칸) or []) if s]
        if "사업의내용찾음" in 신:
            낸["사업의내용찾음"] = bool(신.get("사업의내용찾음"))
    글들 = []
    미 = 원천들.get("미국원천") if isinstance(원천들.get("미국원천"), dict) else {}
    본 = 미.get("본문") if isinstance(미.get("본문"), dict) else {}
    for k in ("Item1", "Item2", "MDA_capex"):
        if isinstance(본.get(k), str):
            글들.append(본[k])
    근 = ((원.get("유형") or {}).get("근거") or []) if isinstance(원.get("유형"), dict) else []
    글들 += ["%s" % x for x in 근] if isinstance(근, list) else ["%s" % 근]
    for 글 in 글들:
        for 키, 꼴 in (("외주", 외주꼴), ("합작", 합작꼴), ("데이터센터", 데이터센터꼴)):
            if len(낸[키]) >= 3:
                continue
            m = 꼴.search(글)
            if m:
                낸[키].append(글[max(0, m.start() - 20): m.end() + 20].replace("\n", " ")[:80])
    # 세기 — A3 가 「외주생산강함」 을 냈거나, 본문 · A3 외주 문장에 강한 꼴이 있고 그 앞뒤가 수탁 · 고객 OEM 문맥이 아닐 때만
    전외주 = [("%s" % s) for s in (신.get("외주생산문장") or [])] if isinstance(신, dict) else []
    for 글 in 글들 + 전외주:
        for m in 강외주꼴.finditer(글):
            곁 = 글[max(0, m.start() - 60): m.end() + 60]
            if 수탁꼴.search(곁):
                continue
            낸["강한외주"].append(곁.replace("\n", " ")[:100])
            break
        if len(낸["강한외주"]) >= 2:
            break
    낸["외주강함"] = bool(isinstance(신, dict) and 신.get("외주생산강함")) or bool(낸["강한외주"])
    전합작 = [("%s" % s) for s in (신.get("합작생산문장") or [])] if isinstance(신, dict) else []
    for 글 in 글들 + 전합작:
        m = 강합작꼴.search(글)
        if m:
            낸["강한합작"].append(글[max(0, m.start() - 20): m.end() + 20].replace("\n", " ")[:100])
            if len(낸["강한합작"]) >= 2:
                break
    if isinstance(신, dict) and (신.get("합작생산강함") or 신.get("합작주력")):        # A3(FX2-A) 강한 합작 신호
        낸["강한합작"] += [("%s" % x)[:100] for x in (신.get("합작생산강한문장") or [])][:2] or ["A3 유형.신호.합작생산강함"]
    낸["합작강함"] = bool(낸["강한합작"])
    낸["지분법투자비"] = _수(신.get("지분법투자÷매출")) if isinstance(신, dict) else None
    # 클라우드(용량을 빌려주어 버는 매출) — 미국 본문 · A3 데이터센터 문장 · 부문 이름
    부문들 = list((((원.get("유형") or {}).get("구분별상세") or {}) if isinstance(원.get("유형"), dict) else {}).keys())
    낸["클라우드"] = (any(클라우드꼴.search(x or "") for x in [본.get("Item1") or "", 본.get("MDA_capex") or ""] + 낸["데이터센터"])
                  or any(부문클라우드꼴.search("%s" % x) for x in 부문들)
                  or bool(isinstance(신, dict) and 신.get("용량임대문장")))                     # A3(FX2-A) 용량 임대 매출 문장
    # 유동 능력 — 생산능력표 주석이 「능력은 인원 · 면적에 따라 유동적으로 변동 · 조절 · 확대할 수 있다」 고 말한다(묶이지 않는 명목 능력)
    for x in (원.get("생산능력표") or []) if isinstance(원.get("생산능력표"), list) else []:
        if isinstance(x, dict):
            m = 유동능력꼴.search("%s" % (x.get("주석글") or ""))
            if m and len(낸["유동능력"]) < 2:
                t = x["주석글"]
                낸["유동능력"].append(t[max(0, m.start() - 30): m.end() + 10].replace("\n", " ")[:80])
    for 글 in 글들:
        m = 수요연동꼴.search(글)
        if m:
            낸["수요연동"].append(글[max(0, m.start() - 30): m.end() + 10].replace("\n", " ")[:80])
            break
    # 자체 생산능력 증설 문장 — 미국원천 능력문장(물리 단위) · 본문에서 「우리 생산능력을 늘린다」(남의 공장 · 고객 공급 계약 · 배치량은 아니다)
    능문 = [("%s" % (x.get("문장") or "")) for x in (미.get("능력문장") or []) if isinstance(x, dict)]
    for 글 in 능문 + 글들:
        m = 증설문장꼴.search(글)
        if m and not 수탁꼴.search(글[max(0, m.start() - 60): m.end() + 60]):
            낸["자체증설"].append(글[max(0, m.start() - 20): m.end() + 40].replace("\n", " ")[:100])
            break
    return 낸


# ── 판정 ─────────────────────────────────────────────────────────────────────
def _토막(s):
    return {t for t in re.findall(r"[가-힣]{2,}|[a-z]{2,}|[a-z]*\d+[a-z]*", ("%s" % (s or "")).lower()) if len(t) >= 2}


def _같은이름(이름, 후보들):
    """글자만 남겨 한쪽이 다른 쪽을 품는 짝만(토막 겹침으로 넓히지 않는다 — 「○○부문 생산본부」 ↔ 「○○부문 대전사업장」 은 짝이 아니다)."""
    a = re.sub(r"\W+", "", ("%s" % 이름).lower())
    for b in 후보들:
        nb = re.sub(r"\W+", "", ("%s" % b).lower())
        if nb and a and (nb in a or a in nb):
            return b
    return None


def _이름짝(이름, 후보들):
    a = re.sub(r"\W+", "", ("%s" % 이름).lower())
    for b in 후보들:
        nb = re.sub(r"\W+", "", ("%s" % b).lower())
        if nb and a and (nb in a or a in nb):
            return b
    ta, 좋, 점 = _토막(이름), None, 0
    for b in 후보들:
        s = len(ta & _토막(b))
        if s > 점:
            좋, 점 = b, s
    return 좋


증설목적꼴 = re.compile(r"생산\s*능력|능력\s*(증대|확대|확보)|[Cc]apacity|증\s*설|생산\s*(설비|라인|시설)|공장\s*(신축|증축|건설)|라인\s*(증설|신설|구축)")
증설아님꼴 = re.compile(r"사옥|연구\s*(소|시설|개발)|R\s*&\s*D|부동산|임대|사무|본사\s*건물|기숙사|복지")


def 증설공시(원, 원천들, 해수=3):
    """FX4-F D4 — 기준일 앞 `해수` 년 안(기준일 뒤 공시 빼고)의 **본사** 신규시설투자 · 유형자산 취득 결정 가운데 목적 · 이름이 생산능력 증설인 것
    → [{이름, 공시일, 금액}] (최근 먼저). 상장 종속회사 결정 · 연구소 · 사옥 · 투자 목적 부동산은 뺀다."""
    수 = (원천들 or {}).get("수시공시") if isinstance((원천들 or {}).get("수시공시"), dict) else {}
    # 공시 창은 정보 경계라 평가기준일 T 에 선다(날짜 둘 2026-10-25 — (F, T] 결정은 쓰고 T 뒤만 「기준일뒤」). 옛 파일은 T = F
    기준 = "%s" % (원.get("평가기준일") or 수.get("평가기준일") or "")
    try:
        끝 = datetime.date.fromisoformat(기준[:10])
    except ValueError:
        return []
    시작 = 끝.replace(year=끝.year - 해수)
    낸 = []
    for x in 수.get("결정") or []:
        if not isinstance(x, dict) or x.get("종류") not in ("신규시설투자", "유형자산취득") or x.get("기준일뒤"):
            continue
        if ("%s" % (x.get("주체") or "본사")) != "본사":
            continue
        try:
            d = datetime.date.fromisoformat(("%s" % x.get("공시일"))[:10])
        except ValueError:
            continue
        if not (시작 <= d <= 끝):
            continue
        글 = "%s %s %s" % (x.get("이름") or "", x.get("목적") or "", x.get("대상") or "")
        if 증설목적꼴.search(글) and not 증설아님꼴.search(글):
            낸.append({"이름": x.get("이름") or "", "공시일": d.isoformat(), "금액": (x.get("금액") or {}).get("값") if isinstance(x.get("금액"), dict) else x.get("금액")})
    return sorted(낸, key=lambda y: y["공시일"], reverse=True)


def 상한판정(원, 원천들=None):
    """능력이 매출 상한인가 — 판정 순서(2026-10-25 FX2-B 확정): ① 수주 구조 ② 공시 가동률 ③ 숫자 대조 ④ 문장(강한 꼴만) ⑤ 낱말 · 역할.
    **문장이 숫자를 이기지 않는다** — 외주 · 위탁 문장은 숫자가 설비 집약을 가리키지 않을 때만(문턱 넘음 0 · 회색 띠 1 이하) 「해당 없음(외주처)」.
    수주 구조가 있으면 가동률은 「중앙 ≥ 0.9 · 또는 최대 ≥ 0.9 이고 증설 투자 중(CAPEX ÷ 상각 ≥ 2)」 일 때만 「예」 — 아니면 「해당 없음(수주 산업)」:
    상한은 설비가 아니라 잔고 소화 속도(매출 노드). 공시 능력이 인원 · 면적에 따라 유동적이라고 적힌 수주 생산도 같다.
    데이터센터가 CAPEX 를 정해도 용량을 팔아 버는 매출(클라우드 · 수주 · RPO)이 없고 능력 유형이 아니면 역할 「투자동인」 · 상한 「해당 없음」.
    → {"전체", "구분별", "상한종류", "판정순서", "근거", "흔들림", "역할", "위탁", "합작", "숫자", "가동률", "수주"}."""
    원천들 = 원천들 or {}
    판 = _유형판정(원)
    순서 = []
    수 = 수주신호(원, 원천들)
    if 수["있음"]:
        순서.append({"단계": "수주", "결과": "잔고소화 후보", "근거": 수["근거"]})
    가 = 가동률판정(원)
    숫 = 숫자대조(원)
    문 = 문장신호(원, 원천들)
    결과, 종류, 흔 = None, "", False
    근거 = []
    상비 = 숫["CAPEX대비상각"]
    확장 = 상비 is not None and 상비 >= 문턱["CAPEX대비상각"] and not (숫["CAPEX대매출"] is not None and 숫["CAPEX대매출"] < 소규모투자)
    무증설 = 상비 is not None and 상비 < 1

    def _줄글(조건=None):
        return " · ".join("%s %s" % (y["이름"][:20], y["근거"]) for y in 가["줄"] if y["판정"] and (조건 is None or y["판정"] in 조건))[:300]
    # ② 공시 가동률(수주 구조와 함께 본다)
    if 수["있음"] and 문["유동능력"]:
        결과, 종류, 흔 = 해당없음, "잔고소화", True
        근거.append("수주 생산 · 공시 능력이 인원 · 면적에 따라 유동적이라고 적었다(「%s」) — 묶이지 않는 명목 능력: 상한은 잔고 소화 속도(매출 노드)"
                  % 문["유동능력"][0][:50])
        순서.append({"단계": "가동률", "결과": 해당없음, "근거": 근거[-1]})
    elif 수["있음"] and 가.get("창") and not 가.get("약함"):
        m, mx = 가.get("중앙"), 가.get("최대")
        증설 = 증설공시(원, 원천들)
        if (m is not None and m >= 0.9) or (mx is not None and mx >= 0.9 and 확장):
            결과, 종류 = "예", (가["종류"] or "설비")
            흔 = m is None or m < 0.9 or (mx is not None and mx > 1.0)
            근거.append("수주 구조 · 공시 가동률 중앙 %.0f%% · 최대 %.0f%%%s — 능력(%s)이 잔고 소화 속도를 정한다" % (
                (m or 0) * 100, (mx or 0) * 100, (" · 증설 투자 중(CAPEX ÷ 상각 %.2f)" % 상비) if (m is None or m < 0.9) else "", 종류))
        elif 증설 and mx is not None and mx >= 0.8:
            # FX4-F D4 — 기준일 앞 3년 안의 본사 신규시설투자(생산능력 증대) 공시 + 가동률 최대 ≥ 80% — 회사가 능력을 늘려야 잔고를 소화한다고 공시한 것.
            # CAPEX ÷ 상각 문턱(투자 집행 전이면 아직 낮다)과 따로 센다(흔들림 · 사람 확인)
            결과, 종류, 흔 = "예", (가["종류"] or "설비"), True
            근거.append("수주 구조 · 공시 가동률 중앙 %.0f%% · 최대 %.0f%% · 생산능력 증설 공시(「%s」 %s) — 능력을 늘려 잔고를 소화한다: 능력(%s)이 상한(흔들림)" % (
                (m or 0) * 100, mx * 100, 증설[0]["이름"][:40], 증설[0]["공시일"], 종류))
        else:
            결과, 종류, 흔 = 해당없음, "잔고소화", True
            근거.append("수주 구조 · 공시 가동률 중앙 %.0f%% · 최대 %.0f%% — 0.9 에 못 미치거나 증설 투자 없이 일부 라인만 높다: 상한은 설비가 아니라 "
                      "잔고 소화 속도(매출 노드)" % ((m or 0) * 100, (mx or 0) * 100))
        순서.append({"단계": "가동률", "결과": 결과, "근거": 근거[-1] + " — " + _줄글()[:160]})
    elif 가["요약"] == 해당없음 and 숫["결과"] == "예":
        # 가동률 표는 일부 품목 · 공장만 담을 수 있다(주력 라인 능력 미공시) — 숫자가 분명히 설비 집약이면 「예」(흔들림)
        결과, 종류, 흔 = "예", "설비", True
        근거.append("공시 가동률은 수요가 정한다고 말하지만(%s) 숫자 대조가 설비 집약이다(%s) — 가동률 표가 주력 능력을 다 담지 않았을 공산(사람 확인)" % (
            " · ".join("%s %.0f%%" % (y["이름"][:12], y["값"] * 100) for y in 가["줄"] if y["판정"])[:120], 숫["근거"][:120]))
        순서.append({"단계": "가동률", "결과": 해당없음, "근거": "가동률 표 — 숫자와 어긋남"})
        순서.append({"단계": "숫자", "결과": "예", "근거": 숫["근거"]})
    elif (가["요약"] == "예" and 가.get("끝최소") is not None and 가["끝최소"] < 가동률문턱["흔들림"] and 숫["결과"] == 해당없음 and 무증설):
        결과, 종류, 흔 = 해당없음, "", True
        근거.append("공시 가동률이 갈린다(최대 %.0f%% · 최소 %.0f%% — 능력 여유 라인이 있고 100%% 넘는 줄은 정규시간 능력) · 숫자 대조가 해당 없음이고 증설 "
                  "투자가 없다(CAPEX ÷ 상각 %.2f < 1) — 수요가 판매량을 정한다" % (가["최대"] * 100, 가["끝최소"] * 100, 상비))
        순서.append({"단계": "가동률", "결과": 해당없음, "근거": 근거[-1] + " — " + _줄글()[:160]})
    elif 가["요약"] in ("예", 해당없음):
        결과, 종류 = 가["요약"], (가["종류"] or ("" if 가["요약"] == 해당없음 else "설비"))
        예줄 = [y for y in 가["줄"] if y["판정"] == "예"]
        흔 = bool(예줄) and all(y["값"] > 1.0 for y in 예줄)
        근거.append("공시 가동률 — " + _줄글(("예", 해당없음)))
        순서.append({"단계": "가동률", "결과": 결과, "근거": 근거[-1]})
    elif 가["줄"]:
        순서.append({"단계": "가동률", "결과": 가["요약"],
                   "근거": ("사업의 내용 문장에서 뽑은 가동률뿐 — 약한 근거(판정을 정하지 않는다) · " if 가.get("약함") else "") + _줄글()})
    # ③ 숫자 대조
    if 결과 is None:
        if 숫["결과"] in ("예", 해당없음):
            결과 = 숫["결과"]
            종류 = "설비" if 결과 == "예" else ""
            흔 = 흔 or 가["요약"] == "흔들림"
            근거.append("숫자 대조 " + 숫["근거"])
        순서.append({"단계": "숫자", "결과": 숫["결과"], "근거": 숫["근거"]})
    # ③-2 숫자는 작지만 자체 생산능력을 늘린다는 문장(물리 단위) — 증설하는 능력은 판매의 상한 후보(흔들림 · 사람 확인)
    if (결과 == 해당없음 and not 종류 and not 수["있음"] and not 문["외주강함"] and 문["자체증설"] and 상비 is not None and 상비 >= 1
            and not any(x in 판 for x in 자산경량유형)):
        결과, 종류, 흔 = "예", "설비", True
        근거.append("숫자 대조는 해당 없음이지만 자체 생산능력을 늘린다는 문장(「%s」) · CAPEX ÷ 상각 %.2f ≥ 1 — 능력이 판매 상한 후보(흔들림 · 사람 확인)"
                  % (문["자체증설"][0][:60], 상비))
        순서.append({"단계": "문장", "결과": "자체 증설", "근거": 근거[-1]})
    # ④ 문장 — 강한 꼴만 · 숫자를 이기지 않는다(R1 · R2)
    합작 = bool(문["합작강함"])
    숫자설비 = bool(숫["넘음"]) or len(숫.get("회색") or []) >= 2
    재고 = 숫["토지건설중제외"] if 숫["토지건설중제외"] is not None else 숫["유형자산대매출"]
    위탁 = bool(문["외주강함"]) and not 숫자설비 and (
        (재고 is not None and 재고 < 0.2) or (숫["CAPEX대매출"] is not None and 숫["CAPEX대매출"] < 0.05) or (재고 is None and 숫["CAPEX대매출"] is None))
    # 문장 없이 숫자만(제조 낱말 + 유형자산 ÷ 매출 < 0.08)이면 「의심」 — 숫자가 이미 해당 없음을 냈으면 글만 덧붙이고 상한 종류는 바꾸지 않는다
    # (수주 산업 · 서비스도 유형자산이 작다 — 외주처로 못 박지 않는다)
    의심 = (not 위탁 and not 합작 and any(x in 판 for x in 제조유형) and 숫["유형자산대매출"] is not None and 숫["유형자산대매출"] < 위탁생산문턱
          and 결과 != "예")
    if 의심:
        근거.append("제조 유형이지만 유형자산 ÷ 매출 %.3f(%s) < %.2f — 위탁 생산 의심(공급사 능력 — 외주 · 수주 문장으로 확인)" % (
            숫["유형자산대매출"], 숫["열"], 위탁생산문턱))
        if 결과 is None:
            위탁 = True
    if 합작 and 결과 != "예":
        결과, 종류, 흔 = "예", "합작", True
        대용 = ""
        if 문.get("지분법투자비") is not None and 숫["유형자산대매출"] is not None:
            숫["합작몫대용_유형자산대매출"] = 숫["유형자산대매출"] + 문["지분법투자비"]
            대용 = " · 합작 몫 대용치(유형자산 + 지분법 투자) ÷ 매출 %.2f" % 숫["합작몫대용_유형자산대매출"]
        근거.append("합작 · 지분법 상대에게서 생산물을 받는다(「%s」) — 합작 몫 능력이 상한(자기 유형자산이 작아도 합작 공장이 능력이다 · "
                  "합작 몫 숫자는 공시 대조 필요 · CAPEX 곁 칸 J2)%s" % (문["강한합작"][0][:60], 대용))
        순서.append({"단계": "문장", "결과": "합작 생산", "근거": 근거[-1]})
    elif 위탁 and 결과 != "예":
        결과, 종류 = 해당없음, "외주처"
        if 문["강한외주"] or 문["외주"]:
            근거.append("외주 · 위탁 생산 문장(「%s」) — 숫자도 설비 집약이 아니다 · 공급사 능력은 외부 제약(D) · 매출 노드로" % (
                (문["강한외주"] or 문["외주"])[0][:50]))
        순서.append({"단계": "문장", "결과": "위탁 생산", "근거": 근거[-1]})
    elif 문["외주강함"] and 숫자설비:
        if 결과 == "예":
            흔 = True
        근거.append("외주 · 위탁 문장(「%s」)이 있으나 숫자가 설비 집약을 가리킨다 — 문장이 숫자를 이기지 않는다(흔들림)" % (
            (문["강한외주"] or 문["외주"] or [""])[0][:50]))
    elif 문["외주"] and not 문["외주강함"]:
        근거.append("외주 · OEM 낱말 문장은 약하다(고객 OEM · 수탁 · 부품 조달 문맥 — 「%s」) — 판정에 쓰지 않았다" % 문["외주"][0][:40])
    # ⑤ 낱말
    if 결과 is None:
        if 수["있음"] and not any(x in 판 for x in 능력유형):
            결과, 종류, 흔 = 해당없음, "잔고소화", True
            근거.append("수주 구조(%s) · 공시 가동률 없음 · 숫자 %s · 능력 유형 아님 — 상한은 잔고 소화 속도(매출 노드)" % (수["근거"][:60], 숫["결과"]))
        elif any(x in 판 for x in 능력유형):
            if 문["수요연동"] and 숫["결과"] != "예":
                결과, 흔 = 해당없음, True
                근거.append("고객 생산 물량에 연동한다는 문장(「%s」) — 수요가 판매량을 정한다(흔들림)" % 문["수요연동"][0][:50])
            else:
                결과, 종류, 흔 = "예", "설비", True
                근거.append("숫자가 갈리거나 모자라 유형 낱말(%s)로 — 흔들림(사람 확인)" % " · ".join(판))
        elif 판 and any(x in 판 for x in 자산경량유형):
            결과 = 해당없음
            근거.append("유형 %s — 자산 경량" % " · ".join(판))
        elif 가["요약"] == "흔들림":
            결과, 흔 = 해당없음, True
            근거.append("가동률 60~85% 뿐 · 숫자 · 낱말이 정하지 못한다 — 수요가 정할 공산(사람 확인)")
        else:
            결과 = "확인 불가"
            근거.append("유형 판정 보류 · 숫자 대조 %s — 능력이 매출 상한인지 정하지 못했다(본선)" % 숫["결과"])
        순서.append({"단계": "낱말", "결과": 결과, "근거": 근거[-1]})
    # 역할 — 데이터센터가 CAPEX 를 정해도 매출이 사용자 · 광고 수요로 정해지면 투자동인(R3)
    역할 = "매출상한"
    if 문["데이터센터"] and 결과 == "예" and 종류 not in ("합작", "인시"):
        if 수["있음"] or 문["클라우드"]:
            역할 = "매출상한"
        elif not any(x in 판 for x in 능력유형):
            결과, 종류, 흔 = 해당없음, "", True
            역할 = "투자동인"
            근거.append("데이터센터 · 서버가 CAPEX 를 정하지만 용량을 팔아 버는 매출(클라우드 · 수주 · RPO)이 보이지 않고 능력 유형도 아니다 — 매출은 "
                      "사용자 · 광고 수요가 정한다: 역할 투자동인 · 상한 해당 없음(흔들림)")
            순서.append({"단계": "역할", "결과": 해당없음, "근거": 근거[-1]})
        else:
            역할 = "투자동인 또는 매출상한(사람 확인 — 데이터센터가 CAPEX 를 정하지만 매출 상한인지는 수주 · RPO · 클라우드 매출로 본다)"
            흔 = True
    if 결과 == 해당없음 and 수["있음"] and 종류 not in ("외주처",):
        종류 = "잔고소화"
        if not any("잔고 소화" in x for x in 근거):
            근거.append("수주 구조 — %s · 상한은 설비가 아니라 잔고 소화 속도(매출 노드)" % 수["근거"])
    elif 결과 == "예" and 수["있음"] and not any("잔고 소화" in x for x in 근거):
        근거.append("수주 구조 — %s · 능력이 잔고 소화 속도를 정한다" % 수["근거"])
    구분별 = 구분별판정(원, 가, 수, 결과, 종류)
    return {"전체": 결과, "구분별": 구분별, "상한종류": 종류 or ("없음" if 결과 == 해당없음 else ""), "판정순서": 순서,
            "근거": " · ".join(근거), "흔들림": 흔, "역할": 역할, "위탁": 위탁, "합작": 합작, "숫자": 숫, "가동률": 가, "수주": 수}


def 구분별판정(원, 가, 수, 전체=None, 전체종류=""):
    """부문(A3 `유형.구분별상세`) 또는 공장 · 품목(가동률공시)마다 {값, 상한종류, 근거}. 차례: 부문 이름과 짝인 가동률 줄 → 부문 자산 ÷ 매출 → 부문 유형 →
    부문 매출 0 → 부문 이름이 서비스 · 금융 · 유통 성격 → (부문 숫자가 없으면) 회사 판정을 물려받음(흔들림 · `물려받음` 표지). 공통 · 조정 줄은 뺀다."""
    낸 = {}
    상세 = ((원.get("유형") or {}).get("구분별상세") or {}) if isinstance(원.get("유형"), dict) else {}
    if isinstance(상세, dict):
        상세 = {k: v for k, v in 상세.items() if not 고객꼴.search("%s" % k)}      # 고객 정보 표가 부문으로 들어온 줄은 버린다
        if 상세 and all(고객법인꼴.search("%s" % k) for k in 상세):
            상세 = {}                                                           # 「○○와 그 종속기업」 뿐 — 주요 고객 표
    가줄 = [y for y in 가.get("줄") or [] if y.get("판정") and not y.get("남의줄")]
    남줄 = [y for y in 가.get("줄") or [] if y.get("판정") and y.get("남의줄")]

    def _법인줄(부문):
        """FX4-F — 부문 이름이 종속 · 상장 자회사 이름이면(「○○밥캣」 부문) 그 법인 이름으로 시작하는 가동률 줄(회사 묶음 셈에서 뺀 「남의줄」)이 그 부문의
        근거다 — 최근 두 기간만. 종전에는 회사 판정을 물려받아 수요가 정하는 자회사 부문까지 「예」 가 됐다."""
        이 = _법인말(부문)
        줄 = [y for y in 남줄 if ("%s" % y["이름"]).split() and _법인말(("%s" % y["이름"]).split()[0]) == 이]
        if not 줄:
            return []
        키 = sorted({((_해(y["기간"]) or 0), 0 if ("%s" % y["기간"]).startswith("FY") else 1) for y in 줄})[-2:]
        return [y for y in 줄 if ((_해(y["기간"]) or 0), 0 if ("%s" % y["기간"]).startswith("FY") else 1) in 키]
    if isinstance(상세, dict) and 상세:
        for 부문, d in 상세.items():
            if not isinstance(d, dict) or 비부문꼴.search("%s" % 부문):
                continue
            이름판 = _부문이름판(부문, 전체, 전체종류)
            if 이름판:
                낸[부문] = 이름판
                continue
            짝줄 = _부문줄짝(부문, 가줄) or _법인줄(부문)
            if 짝줄:
                vs = sorted(min(y["값"], 1.3) for y in 짝줄)
                m = vs[len(vs) // 2] if len(vs) % 2 else (vs[len(vs) // 2 - 1] + vs[len(vs) // 2]) / 2
                값 = "예" if m >= 가동률문턱["예"] else 해당없음
                낸[부문] = {"값": 값, "상한종류": (짝줄[0]["상한종류"] if 값 == "예" else "없음"),
                          "근거": "가동률 %d줄 중앙 %.0f%% — %s" % (len(짝줄), m * 100, " · ".join("%s %.0f%%" % (y["이름"][:16], y["값"] * 100) for y in 짝줄)[:120])}
                continue
            자, 매 = _수(d.get("자산")), _수(d.get("매출"))
            유 = d.get("유형") or ""
            if 자 is not None and 매:
                r = 자 / 매
                if r >= 문턱["유형자산대매출"] and not any(x in 유 for x in 자산경량유형):
                    낸[부문] = {"값": "예", "상한종류": "설비", "근거": "부문 자산 ÷ 매출 %.2f ≥ %.1f" % (r, 문턱["유형자산대매출"])}
                elif r < 0.2:
                    낸[부문] = {"값": 해당없음, "상한종류": "없음", "근거": "부문 자산 ÷ 매출 %.2f < 0.2" % r}
                else:
                    낸[부문] = {"값": "예" if any(x in 유 for x in 능력유형) else 해당없음, "상한종류": "설비" if any(x in 유 for x in 능력유형) else "없음",
                              "근거": "부문 자산 ÷ 매출 %.2f(중간) · 부문 유형 %s — 흔들림" % (r, 유 or "모름")}
            elif 유:
                예 = any(x in 유 for x in 능력유형)
                낸[부문] = {"값": "예" if 예 else 해당없음, "상한종류": "설비" if 예 else "없음", "근거": "부문 유형 %s(숫자 없음 — 흔들림)" % 유}
            elif 매 is not None and 매 <= 0:
                낸[부문] = {"값": 해당없음, "상한종류": "없음", "근거": "부문 매출 0 — 능력이 매출을 묶지 않는다"}
            elif 전체 in ("예", 해당없음):
                낸[부문] = {"값": 전체, "상한종류": (전체종류 or "설비") if 전체 == "예" else "없음",
                          "근거": "부문 자산 · 유형 · 가동률이 없어 회사 판정을 물려받음(흔들림 — 부문 숫자로 확인)", "물려받음": True}
        return 낸
    for y in 가줄:
        값 = "예" if y["판정"] == "예" else 해당없음
        낸[y["이름"]] = {"값": 값, "상한종류": y["상한종류"] if 값 == "예" else "없음", "근거": "공장 · 품목 가동률 — " + y["근거"]}
    if not 낸 and 전체 in ("예", 해당없음) and isinstance(원.get("생산능력표"), list):
        for x in 원["생산능력표"]:
            품 = ("%s" % (x.get("품목") or "")).strip() if isinstance(x, dict) else ""
            if not 품 or 합계꼴.search(품) or re.fullmatch(r"(?:%s)(?:\s|$).*" % _자산말, 품) or 품 in 낸:
                continue
            이름판 = _부문이름판(품, 전체, 전체종류)
            낸[품] = 이름판 or {"값": 전체, "상한종류": (전체종류 or "설비") if 전체 == "예" else "없음",
                             "근거": "생산능력표 품목 — 부문 · 가동률이 없어 회사 판정을 물려받음(흔들림)", "물려받음": True}
    return 낸


def _부문이름판(부문, 전체, 전체종류):
    """부문 이름만으로 정하는 자리(숫자보다 먼저 — 금융 · 건설 부문은 자산이 커도 설비 능력이 상한이 아니다). 없으면 None."""
    t = "%s" % 부문
    if 전체 == "예" and 부문클라우드꼴.search(t):
        return {"값": "예", "상한종류": 전체종류 or "설비", "근거": "클라우드 · 데이터센터 부문 — 회사 판정(데이터센터 능력)을 이 부문에 둔다(흔들림)"}
    if 기타부문꼴.search(t):
        return {"값": 해당없음, "상한종류": "없음", "근거": "기타 부문 — 주력 능력이 아닌 묶음(흔들림)"}
    if 경량부문꼴.search(t):
        return {"값": 해당없음, "상한종류": "없음", "근거": "부문 이름이 서비스 · 금융 · 유통 · IT 성격 — 설비 능력이 상한이 아니다(흔들림)"}
    if 수주부문꼴.search(t):
        return {"값": 해당없음, "상한종류": "잔고소화", "근거": "건설 부문 — 외주 시공 · 수주 소화가 매출을 정한다(설비 능력 아님 · 흔들림)"}
    return None


def _부문줄짝(부문, 줄들):
    """부문 이름 ↔ 가동률 줄 — 군말(부문 · 사업 · segment)을 뺀 핵심 낱말이 줄 이름에 들어 있거나 줄 이름 첫 낱말이 핵심과 같으면 짝(여러 줄)."""
    핵 = re.sub(r"[\s\W_]+", "", _부문군말.sub("", "%s" % 부문)).lower()
    if len(핵) < 2:
        return []
    낸 = []
    for y in 줄들:
        이 = re.sub(r"[\s\W_]+", "", "%s" % y["이름"]).lower()
        첫 = re.sub(r"[\s\W_]+", "", _부문군말.sub("", ("%s" % y["이름"]).split()[0] if ("%s" % y["이름"]).split() else "")).lower()
        if 핵 in 이 or (len(첫) >= 2 and 첫 == 핵) or (len(첫) >= 3 and re.search(r"[가-힣]", 첫) and 첫 in 핵):
            낸.append(y)
    return 낸


def 위탁생산인가(원):
    """제조 유형(능력유형 가운데 제조)인데 유형자산 ÷ 매출이 문턱 아래면 → (참, 비율, 해). 재료가 없으면 (거짓, None, None). (옛 이름 — 그대로 둔다)"""
    판 = _유형판정(원)
    if not any(x in 판 for x in 제조유형):
        return False, None, None
    재 = 원.get("재무시계열") or {}
    fy = sorted(c for c, v in 재.items() if c.startswith("FY") and v.get("매출") and v.get("유형자산") is not None)
    if not fy:
        return False, None, None
    c = fy[-1]
    r = 재[c]["유형자산"] / 재[c]["매출"]
    return r < 위탁생산문턱, r, c


def 자산경량인가(원):
    """→ (참 · 거짓, 까닭) — 옛 반환 꼴(동인진단이 부른다). `상한판정` 이 「해당 없음」이고 상한 종류가 잔고 소화 · 인시가 아니면 참."""
    상 = 상한판정(원)
    if 상["전체"] == 해당없음 and 상["상한종류"] not in ("잔고소화", "인시"):
        return True, 상["근거"] or "능력이 매출 상한이 아니다"
    return False, ""


# ── 편입 · CAPEX 비율 ────────────────────────────────────────────────────────
def 편입합(원, 측정="편입"):
    """자산 종류별 측정(편입 = 취득 + 대체 · 사업결합)의 합 — 건설중인자산 · 합계 · 사용권 · 투자부동산 열은 뺀다(대체로 본계정에 넘어가 두 번 세지 않게)."""
    합 = {}
    for 종류, 측정들 in ((원.get("유형자산") or {}).get("종류별") or {}).items():
        if "건설중" in 종류 or "합계" in 종류 or "사용권" in 종류 or "투자부동산" in 종류 or 종류 in ("유형자산", "계"):
            continue
        if not isinstance(측정들, dict):
            continue
        for c, v in _fy(측정들.get(측정)).items():
            합[c] = 합.get(c, 0.0) + v
    return 합


def CAPEX비율짓기(원, 원천들, 상, 주의, 확인불가, 가정=None):
    원천들 = 원천들 or {}
    재 = 원.get("재무시계열") or {}
    유 = 원.get("유형자산") if isinstance(원.get("유형자산"), dict) else {}
    열들 = [c for c, v in sorted(재.items()) if isinstance(v, dict)]
    매출 = {c: _수(재[c].get("매출")) for c in 열들 if _수(재[c].get("매출"))}
    현금 = {}
    for c in 열들:
        v = _수(재[c].get("CAPEX"))
        if v is None:
            v = _자산군CAPEX(원, c)
        if v is not None:
            현금[c] = v
    무형 = {c: _수(재[c].get("무형취득")) for c in 열들 if _수(재[c].get("무형취득")) is not None}
    상유, 상뜻, 상뺀 = 상각분모(원)
    상579 = _열수((원.get("원천행") or {}).get("579"))
    상유실 = {c: v for c, v in 상유.items() if 상뜻.get(c) == "유형몫"}
    if 상뺀:
        주의.append("유형 몫 상각이 총 상각(579)과 어긋나 그 기간은 579 계열로 내렸다(%s — 유형 몫 ÷ 579) — FX4-F D1" % " · ".join(상뺀))
    _뜻수 = {k: sum(1 for x in 상뜻.values() if x == k) for k in ("유형몫", "579−무형", "579")}
    상출 = ("기간마다 — 유형 몫 상각(A3 상각유형 · 총 상각과 검산 · 사용권 · 무형 제외) %d열 · 579 − 무형 상각 %d열 · 579(사용권 · 무형 포함) %d열"
          % (_뜻수["유형몫"], _뜻수["579−무형"], _뜻수["579"]))
    사신 = _열수(유.get("사용권신규") if isinstance(유.get("사용권신규"), dict) else {})
    편입 = 편입합(원)
    순유 = {c: _수(재[c].get("유형자산")) for c in 열들 if c.startswith("FY") and _수(재[c].get("유형자산")) is not None}
    무자 = {c: (_수(재[c].get("무형자산")) or 0.0) + (_수(재[c].get("영업권")) or 0.0) for c in 열들
           if c.startswith("FY") and (_수(재[c].get("무형자산")) is not None or _수(재[c].get("영업권")) is not None)}
    s2c, s2ci = {}, {}
    for c in sorted(순유):
        y3 = "FY%d%s" % (_해(c) - 3, c[6:])
        if y3 in 순유 and c in 매출 and y3 in 매출 and 순유[c] > 순유[y3] and 매출[c] > 매출[y3]:
            s2c[c] = (매출[c] - 매출[y3]) / (순유[c] - 순유[y3])
        if y3 in 순유 and c in 무자 and y3 in 무자 and c in 매출 and y3 in 매출:
            d = (순유[c] + 무자[c]) - (순유[y3] + 무자[y3])
            if d > 0 and 매출[c] > 매출[y3]:
                s2ci[c] = (매출[c] - 매출[y3]) / d

    def 곁(키):
        """재무시계열[c].키 · CAPEX구성.키 → {c: 값}."""
        낸 = {}
        for c in 열들:
            v = _수(재[c].get(키))
            if v is None and isinstance(재[c].get("CAPEX구성"), dict):
                v = _수(재[c]["CAPEX구성"].get(키))
            if v is not None:
                낸[c] = v
        return 낸
    미지급, 재활, 합작몫 = 곁("미지급설비증감"), 곁("재무활동설비"), 곁("합작몫CAPEX")
    # 리스로 새로 생긴 사용권자산 — 금융 · 운용으로 갈린 칸이 있으면 그 합(미국 — 금융리스 · 운용리스 사용권 태그), 없으면 A3 사용권신규(국내 — 리스
    # 주석 · 비현금거래). 미국 A3 사용권신규는 태그 하나(운용 먼저)만 잡을 수 있다 — 갈린 칸이 오면 그것이 이긴다
    사금, 사운 = 곁("사용권신규_금융"), 곁("사용권신규_운용")
    미 = 원천들.get("미국원천") if isinstance(원천들.get("미국원천"), dict) else {}
    누 = 미.get("누계") if isinstance(미.get("누계"), dict) else {}
    기준단위 = 원.get("단위") or ""
    if 누 and isinstance(누.get("값"), dict) and 누.get("기간ID"):
        k = 누["기간ID"]
        nv = 누["값"]
        for 키, 담 in (("매출", None), ("CAPEX", None), ("무형취득", None), ("유형상각", None), ("미지급설비증감", 미지급),
                      ("금융리스신규", 사금), ("운용리스신규", 사운)):
            v = 환산(nv.get(키), "USD", 기준단위) if _수(nv.get(키)) is not None else None
            if v is None:
                continue
            if 키 == "매출" and k not in 매출:
                매출[k] = v
            elif 키 == "CAPEX" and k not in 현금:
                현금[k] = v
            elif 키 == "무형취득" and k not in 무형:
                무형[k] = v
            elif 키 == "유형상각" and k not in 상유:
                상유[k] = v
            elif 담 is not None and k not in 담:
                담[k] = v
    사신합 = dict(사신)
    for c in set(사금) | set(사운):
        사신합[c] = (사금.get(c) or 0.0) + (사운.get(c) or 0.0)
    if 사신합 and not (사금 or 사운) and (원천들.get("미국원천") or 통화(기준단위) == "USD"):
        주의.append("미국 사용권 신규가 태그 하나(A3 — 운용리스 먼저)일 수 있다 — 금융리스 사용권(RightOfUseAssetObtainedInExchangeForFinanceLeaseLiability)이 "
                  "빠졌으면 리스포함 CAPEX 가 낮다(미국원천 누계의 금융리스신규 · 운용리스신규로 바로잡는다)")
    # 사용권 상각 = 579(유형 + 사용권 + 무형) − 유형 몫 − 무형 — 셋이 다 있을 때만(리스포함 CAPEX ÷ 상각의 분모 짝)
    상579 = _열수((원.get("원천행") or {}).get("579"))
    상무 = _열수(유.get("상각무형") if isinstance(유.get("상각무형"), dict) else {})
    사상 = {c: 상579[c] - 상유실[c] - 상무[c] for c in 상579 if c in 상유실 and c in 상무 and 상579[c] - 상유실[c] - 상무[c] > 0}
    스위치 = ((((가정 or {}).get("스위치") or {}).get("리스부채포함")) or "포함")
    스위치 = "제외" if 스위치 == "제외" else "포함"
    중간 = sorted(c for c in 현금 if not c.startswith("FY") and c in 매출)
    현기 = {"매출대비CAPEX": {c: (현금[c] + (무형.get(c) or 0.0)) / 매출[c] for c in 현금 if 매출.get(c)} if 현금 else "확인 불가",
          "CAPEX대비상각": {c: 현금[c] / 상유[c] for c in 현금 if 상유.get(c)} if (현금 and 상유) else "확인 불가",
          # FX4-F — 참고: 유형 취득 ÷ 총 상각(579 — 유형 + 사용권 + 무형). 유형 몫을 못 가른 옛 판 · 다른 자료와 견줄 때의 짝(정의가 다르다)
          "CAPEX대비총상각": {c: 현금[c] / 상579[c] for c in 현금 if 상579.get(c)} if (현금 and 상579) else "확인 불가 — 579 가 없다"}
    리기 = {"매출대비CAPEX": {c: (현금[c] + 사신합[c] + (무형.get(c) or 0.0)) / 매출[c] for c in 현금 if c in 사신합 and 매출.get(c)},
          "CAPEX대비상각": {c: (현금[c] + 사신합[c]) / (상유실[c] + 사상[c]) for c in 현금 if c in 사신합 and c in 사상 and c in 상유실}}
    리기 = {k: (v or ("확인 불가 — 사용권 신규가 없다" if k == "매출대비CAPEX" else "확인 불가 — 사용권 상각(579 − 유형 − 무형)이 없다")) for k, v in 리기.items()}
    발기 = {"매출대비CAPEX": {c: (현금[c] + 미지급[c] + (무형.get(c) or 0.0)) / 매출[c] for c in 현금 if c in 미지급 and 매출.get(c)} or
            "확인 불가 — 미지급 설비대금 증감이 없다(A3 CAPEX구성 · 미국원천 누계)"}
    # 정본 = 리스 스위치와 짝(2026-10-25 총괄 J1) — 포함이면 리스포함(열마다 사용권 신규가 없으면 그 열만 현금 기준 · 경보), 제외면 현금 기준
    정본 = {"매출대비CAPEX": {}, "CAPEX대비상각": {}}
    열정의 = {}
    for 키 in ("매출대비CAPEX", "CAPEX대비상각"):
        현 = 현기[키] if isinstance(현기[키], dict) else {}
        리 = 리기[키] if isinstance(리기[키], dict) else {}
        for c, v in 현.items():
            if 스위치 == "포함" and c in 리:
                정본[키][c] = 리[c]
                if 키 == "매출대비CAPEX":
                    열정의[c] = "리스포함"
            else:
                정본[키][c] = v
                if 키 == "매출대비CAPEX":
                    열정의[c] = "현금기준" if 스위치 == "제외" else "현금기준(사용권 신규 확인 불가 — 리스 짝 미완)"
        if not 정본[키]:
            정본[키] = "확인 불가"
    if 스위치 == "포함" and 현금 and not isinstance(리기["매출대비CAPEX"], dict):
        주의.append("사용권 신규 확인 불가 — 리스 짝 미완: 리스부채포함 = 포함인데 리스로 새로 생긴 사용권자산을 못 찾아 정본 CAPEX 를 현금 기준으로 냈다"
                  "(국내 — 현금흐름표 주석 비현금거래 「리스부채로 인한 사용권자산 증가」 · 리스 주석 / 미국 — RightOfUseAssetObtainedInExchangeFor… 태그)")
    elif 스위치 == "포함" and 현금 and any("확인 불가" in v for v in 열정의.values()):
        주의.append("사용권 신규 확인 불가 — 리스 짝 미완(일부 열: %s) — 그 열만 현금 기준" % " · ".join(c for c, v in 열정의.items() if "확인 불가" in v))
    비율 = {"매출대비CAPEX": 정본["매출대비CAPEX"], "CAPEX대비상각": 정본["CAPEX대비상각"],
          "정본": "리스스위치짝", "리스부채포함": 스위치, "정본열정의": 열정의,
          "현금기준": 현기, "리스포함": 리기, "발생기준": 발기,
          "성장CAPEX비중": "확인 불가",
          "사용권신규대비매출": {c: 사신합[c] / 매출[c] for c in 사신합 if 매출.get(c)} if 사신합 else 해당없음,
          "SalesToCapital": s2c or "확인 불가",
          "SalesToCapital_인수자본포함": s2ci or "확인 불가 — 재무시계열에 무형자산 · 영업권 잔액이 없다",
          "참고_편입기준": {c: 편입[c] / 매출[c] for c in 편입 if 매출.get(c)} if 편입 else "확인 불가",
          "매출대비CAPEX_유형만": {c: 현금[c] / 매출[c] for c in 현금 if 매출.get(c)} if 현금 else "확인 불가",
          "재무활동설비포함": {c: (현금[c] + 재활[c] + (무형.get(c) or 0.0)) / 매출[c] for c in 현금 if c in 재활 and 매출.get(c)} or
                      "확인 불가 — 재무활동의 설비 대금 줄이 없다",
          "합작몫": {c: 합작몫[c] / 매출[c] for c in 합작몫 if 매출.get(c)} if 합작몫 else (
              "확인 불가 — 합작(지분법) 생산 신호가 있다 · 합작 몫 CAPEX 는 곁 칸만(J2 — 엔진에 넣지 않는다 · 합작 장비 상각이 원가에 있다)"
              if 상.get("합작") else 해당없음),
          "유형자산대매출": {}, "토지건설중제외_유형자산대매출": {}, "재평가제외": "확인 불가 — 재평가 잉여금 칸이 없다",
          "중간열": {c: {"연환산배": _연환산배(원, c)} for c in 중간},
          "상각분모정의": "%s · 리스포함 판의 분모 = 유형 몫 상각 + 사용권 상각(579 − 유형 − 무형)" % 상출,
          "상각분모열": 상뜻 or "확인 불가",
          "분모": "재무시계열.매출(한 키 — 원천행으로 갈아 끼우지 않는다)",
          "정의": "정본은 리스 스위치와 짝(2026-10-25 총괄 J1 — 엔진은 리스부채포함 = 포함이면 리스부채를 브리지에서 빼고 사용권자산을 상각 밑값(원천 19)에 "
                "더한다 · 신규 사용권 취득을 재투자에서 빼면 리스로 들일 설비가 FCFF 어디에서도 현금으로 안 빠진다). 포함 — 매출대비CAPEX = (현금흐름표 유형자산의 "
                "취득 + 무형자산의 취득 + 리스로 새로 생긴 사용권자산) ÷ 매출 · CAPEX대비상각 = (유형 취득 + 사용권 신규) ÷ (유형 몫 상각 + 사용권 상각). 제외 — "
                "현금 기준(유형 + 무형 취득 ÷ 매출 · 유형 취득 ÷ 유형 몫 상각 — 리스료는 영업비용으로 이미 빠진다). 곁 칸: 현금기준(옛 정본 · S5-15 — 비교용) · "
                "리스포함 · 발생기준(현금 + 미지급 설비대금 증감) · 유형만 · 재무활동설비포함 · 합작몫(J2). 사업결합은 언제나 뺀다 · 편입 기준(취득 + 대체 — 완공 "
                "기준 · 투자부동산 대체 뺌)은 참고 · 중간 열(1H 등)은 비율이라 연환산하지 않는다(유형자산대매출만 매출을 연환산). 엔진 · 가정 값은 이 정의로 바뀌지 "
                "않는다(근거 범위의 재료 — ㊹ 는 A3 현금 기준으로 잰다)",
          "근거": "현금 = 동인원천 재무시계열.CAPEX(+ 무형취득) · 사용권 신규 = %s · 상각 = %s · 성장 비중은 공시 투자계획이 있어야 한다" % (
              "금융 · 운용 갈린 칸의 합" if (사금 or 사운) else ("A3 유형자산.사용권신규" if 사신 else "없음"), 상출)}
    for c in sorted(c for c in 열들 if c in 매출):
        v = _수(재[c].get("유형자산"))
        if v is None:
            continue
        배 = _연환산배(원, c) or 1.0
        비율["유형자산대매출"][c] = v / (매출[c] * 배)
        숫 = 숫자대조(원, c)
        if 숫["토지건설중제외"] is not None:
            비율["토지건설중제외_유형자산대매출"][c] = 숫["토지건설중제외"]
    if isinstance(비율["SalesToCapital"], dict) and any(v > 20 for v in 비율["SalesToCapital"].values()):
        주의.append("SalesToCapital 이 20 을 넘는 열이 있다(%s) — Δ순유형자산이 작아(자산 경량 · 수주 산업) 이 비율은 재투자 근거로 쓰지 않는다"
                  % " · ".join("%s %.0f" % (c, v) for c, v in 비율["SalesToCapital"].items() if v > 20))
    if not 비율["유형자산대매출"]:
        비율["유형자산대매출"] = "확인 불가"
    if not 비율["토지건설중제외_유형자산대매출"]:
        비율["토지건설중제외_유형자산대매출"] = "확인 불가 — 토지 · 건설중인자산 잔액이 없다"
    if isinstance(비율["매출대비CAPEX"], dict) and isinstance(현기["매출대비CAPEX"], dict):
        큰 = [(c, v, 현기["매출대비CAPEX"][c]) for c, v in 비율["매출대비CAPEX"].items()
             if c in 현기["매출대비CAPEX"] and v - 현기["매출대비CAPEX"][c] > 리스차이경보]
        비율["리스큰회사"] = bool(큰)
        if 큰:
            c, v, 기 = 큰[-1]
            주의.append("J1 리스 — 정본(리스포함) CAPEX ÷ 매출이 현금 기준보다 매출의 %.0f%%p 넘게 크다(%s %.3f ↔ 현금 %.3f · %d열) — 데이터센터 · 매장 · "
                      "리스 많은 회사: 유지 · 성장 CAPEX 근거 범위가 현금 기준과 다르다" % (리스차이경보 * 100, c, v, 기, len(큰)))
    if not 현금:
        확인불가.append({"항목": "CAPEX비율", "원인": "동인원천에 현금흐름표 유형자산의 취득이 없다(국내 — DART 앵커 · 재무 API 의 CF · 미국 — companyfacts)"})
    elif not 중간:
        주의.append("기준일 누계 열(1H · 9M)이 없다 — A3 재무시계열에 중간 열이 없거나(미국 — 미국원천 누계) 그 열에 CAPEX 가 없다")
    결합 = {c: _수(재[c].get("사업결합취득")) for c in 열들 if _수(재[c].get("사업결합취득"))}
    큰결합 = [c for c, v in 결합.items() if 현금.get(c) and v > 0.5 * 현금[c]]
    if 큰결합:
        주의.append("사업결합 취득이 그 해 CAPEX 의 절반을 넘는다(%s) — 인수로 늘어난 유형자산 · 능력은 CAPEX 가 아니다(능력 변동 원인 「사업결합」)" % " · ".join(큰결합))
    단절 = (원.get("구조") or {}).get("구조단절") if isinstance(원.get("구조"), dict) else None
    if 단절:
        주의.append("구조 단절 후보(%s) — 그 시점 앞 CAPEX 열은 지금 사업과 다를 수 있다(매각 · 분할 전 역사)" % (단절 if isinstance(단절, str) else json.dumps(단절, ensure_ascii=False)[:80]))
    return 비율, 상유, 상출, 현금, 결합


# ── 약정 ─────────────────────────────────────────────────────────────────────
_성격규칙 = (("보조금조건", r"보조금|subsid|grant"), ("보증", r"보증|guarant"), ("매출측능력배정", r"capacity (?:access|reservation)|능력\s*배정|선구매권"),
          ("지분", r"지분|출자|equity|capital call|펀드|타법인"), ("사용권", r"리스|사용권|lease"),
          ("비용", r"비용|클라우드|cloud|서비스|service|라이선스|licen|전력|energy|power|take-or-pay"),
          ("재고공급", r"원재료|재고|공급|wafer|inventory|purchase obligation|구매\s*의무|manufacturing purchase|공급사|매입약정"),
          ("설비취득", r"설비|유형자산|건설|건축|공사|capex|capital expend|plant|property|장비|토지|construction|도급"))


def 성격분류(이름, 후보=None):
    """약정 이름(또는 원천의 성격후보) → 성격 낱말(약정성격). 혼합 꼴이 먼저 · 모르면 「미분류」."""
    if 후보 in 약정성격 and 후보 != "미분류":
        return 후보
    t = ("%s %s" % (후보 or "", 이름 or "")).lower()
    if re.search(r"혼합|mixed", t):
        return "혼합"
    for 이름_, 꼴 in _성격규칙:
        if re.search(꼴, t):
            return 이름_
    return "미분류"


def 약정짓기(원, 원천들, 공시없음, 확인불가):
    원천들 = 원천들 or {}
    기준단위 = 원.get("단위") or ""
    통 = 통화(기준단위)
    유 = 원.get("유형자산") if isinstance(원.get("유형자산"), dict) else {}
    낸 = []
    취 = 유.get("취득약정액")
    if isinstance(취, dict):
        for c, v in sorted(취.items()):
            if _수(v) is None:
                continue
            낸.append({"이름": "유형자산 취득 약정", "금액": _수(v), "통화": 통, "기준일": c, "성격": "설비취득", "기간별": {}, "연결범위": "모름",
                      "기준일뒤": False, "출처": "동인원천 568(약정사항 주석)", "태그": "[공시]"})
    elif isinstance(취, str) and 취.strip():
        (공시없음 if re.search(r"확인했고 없었다|해당사항\s*없음|기재\s*없음|없음$", 취) else 확인불가).append(
            {"항목": "약정.유형자산 취득 약정", "원인" if not re.search(r"확인했고 없었다|해당사항\s*없음", 취) else "까닭": 취[:160]})
    for x in (유.get("약정줄") or []) if isinstance(유.get("약정줄"), list) else []:
        if not isinstance(x, dict) or _수(x.get("금액")) is None:
            continue
        v = 환산(x["금액"], x.get("단위") or x.get("통화"), 기준단위) if (x.get("단위") or x.get("통화")) else _수(x["금액"])
        낸.append({"이름": x.get("이름") or "", "금액": v if v is not None else _수(x["금액"]), "통화": x.get("통화") or 통,
                  "기준일": x.get("기준일") or "", "성격": 성격분류(x.get("이름"), x.get("성격")), "기간별": x.get("기간별") or {},
                  "연결범위": x.get("연결범위") or "모름", "상대": x.get("상대"), "특수관계": x.get("특수관계"), "기준일뒤": bool(x.get("기준일뒤")),
                  "출처": x.get("출처") or "동인원천 약정줄", "태그": "[공시]"})
    미 = 원천들.get("미국원천") if isinstance(원천들.get("미국원천"), dict) else {}
    for x in 미.get("약정") or []:
        if not isinstance(x, dict) or _수(x.get("금액")) is None:
            continue
        v = 환산(x["금액"], x.get("통화") or "USD", 기준단위)
        낸.append({"이름": x.get("이름") or "", "금액": v if v is not None else _수(x["금액"]), "통화": x.get("통화") or "USD",
                  "기준일": x.get("기준일") or "", "성격": 성격분류(x.get("이름"), x.get("성격후보")),
                  "기간별": {k: 환산(w, x.get("통화") or "USD", 기준단위) for k, w in (x.get("기간별") or {}).items() if _수(w) is not None},
                  "연결범위": "연결", "기준일뒤": bool(x.get("기준일뒤")), "원천": x.get("원천") or "", "출처": x.get("출처") or "미국원천",
                  "태그": "[공시]"})
    수 = 원천들.get("수시공시") if isinstance(원천들.get("수시공시"), dict) else {}
    for x in 수.get("결정") or []:
        if not isinstance(x, dict) or x.get("종류") != "타법인주식취득":
            continue
        금 = x.get("금액") if isinstance(x.get("금액"), dict) else {}
        v = 환산(금.get("값"), (금.get("통화") or "KRW"), 기준단위) if 금 else None
        if v is None:
            continue
        낸.append({"이름": "%s — %s" % (x.get("제목") or "타법인주식 취득", x.get("대상") or ""), "금액": v, "통화": 금.get("통화") or 통,
                  "기준일": x.get("공시일") or "", "성격": "지분", "기간별": {}, "연결범위": x.get("주체") or "본사",
                  "기준일뒤": bool(x.get("기준일뒤")), "출처": x.get("출처") or "수시공시", "태그": "[공시]", "비고": "지분 — CAPEX 아님"})
    # 같은 금액 · 기준일 두 줄은 하나로(A3 와 미국원천이 같은 약정을 따로 낸 경우)
    본, 남 = set(), []
    for x in 낸:
        k = (round(x["금액"] or 0, 3), x.get("기준일"))
        if k in 본:
            continue
        본.add(k)
        남.append(x)
    return 남


# ── 프로젝트 ─────────────────────────────────────────────────────────────────
def 표조각인가(이름):
    """투자계획 표의 「구분」 칸이 프로젝트 이름이 아니라 열 밀림 · 머리 · 합계 · 기간 조각인가 → (참, 까닭)."""
    t = ("%s" % (이름 or "")).strip()
    if not t or not re.search(r"[가-힣A-Za-z]", t):
        return True, "수 · 기호 조각"
    if re.fullmatch(r"[\d\s,.\-~'’%()년월일분기반기제기]*", t):
        return True, "기간 · 수 조각"
    if t.replace(" ", "") in {m.replace(" ", "") for m in _머리말} or re.fullmatch(r"제\s*\d+\s*기.*", t) or re.fullmatch(r"\(?\s*(기준일|단위)\s*[:：].*", t):
        return True, "머리 · 합계 줄"
    if re.fullmatch(r"(?:%s|[\s,/·()])+" % _자산말, t):
        return True, "자산 이름 조각(열 밀림)"
    if _효과말.search(t) and not re.search(r"증설|신설|신축|공장|라인|팹|캠퍼스|센터|사업장", t):
        return True, "투자효과 조각(열 밀림)"
    return False, ""


def _열밀림인가(y):
    """구분은 이름인데 기간 칸이 기간이 아니고 대상 칸이 기간이면 한 칸 밀린 줄(금액 칸을 믿지 않는다)."""
    기 = "%s" % (y.get("기간") or "")
    대 = "%s" % (y.get("대상") or "")
    return bool(기) and not _기간꼴.search(기) and bool(_기간꼴.search(대))


def _새칸(x, 기본=None):
    d = {"투자범위": "모름", "지분율": 1.0, "금액100%": None, "공동투자자": [], "회사몫": None, "정정이력": [], "이사회승인": None,
         "자금출처겹침": [], "집행대계획": None, "연결범위": "본사", "기준일뒤": False, "유니버스중복": []}
    d.update(기본 or {})
    for k, v in d.items():
        x.setdefault(k, v)
    if x.get("금액100%") is None and _수(x.get("총액")) is not None:
        x["금액100%"] = _수(x["총액"]) / (x.get("지분율") or 1.0)
    return x


def 프로젝트짓기(원, 원천들, 주의, 기준일후, 처분):
    원천들 = 원천들 or {}
    기준단위 = 원.get("단위") or ""
    계 = 원.get("투자계획") if isinstance(원.get("투자계획"), dict) else {}
    프로젝트, 기집행, 거름 = [], [], []
    밀림 = 0
    for y in (계.get("표") or []):
        if not isinstance(y, dict):
            continue
        구분글 = ("%s" % (y.get("구분") or "")).strip()
        조, 까 = 표조각인가(구분글)
        if 조:
            거름.append("%s(%s)" % (구분글[:16] or "빈칸", 까))
            continue
        if re.search(r"합\s*계|소\s*계|총\s*계", "%s %s" % (y.get("대상") or "", y.get("효과") or "")):
            거름.append("%s(합계 줄)" % 구분글[:16])
            continue
        밀 = _열밀림인가(y)
        밀림 += int(밀)
        if re.search(r"보완|경상|유지|합리화|대체|보수", 구분글):
            성격 = "유지"
        else:
            성격 = "성장" if re.search(r"신규|증설|확장|생산능력증가|신설|신축", "%s %s" % (구분글, y.get("효과") or "")) else "유지"
        총 = 기투 = 향후 = None
        총출 = ""
        if not 밀:
            총, 기투, 향후 = _수(y.get("총투자")), _수(y.get("기투자")), _수(y.get("향후투자"))
            if 향후 is None and 총 is not None and 기투 is not None:
                향후 = 총 - 기투
            if 총 is None and 기투 is not None and 향후 is not None:
                총, 총출 = 기투 + 향후, "기투자 + 향후투자"
            elif 총 is None and 향후 is not None and 기투 is None:
                총, 총출 = 향후, "향후투자(남은 예산 — 총액 칸 없음)"
            if 총 is not None and 기투 is not None and 기투 > 총 * 1.001:
                주의.append("투자계획 표 「%s」 기투자 %s > 총투자 %s — 표 검산 어긋남(열 밀림 · 단위 의심)" % (구분글, "{:,.0f}".format(기투), "{:,.0f}".format(총)))
        x = {"이름": 구분글 or (y.get("대상") or ""), "이름출처": "표", "능력단위": "" if 밀 else (y.get("대상") or ""), "금액": {}, "총액": 총,
             "착공": "", "완공": "", "리드타임": None, "성격": 성격, "기간": "" if 밀 else (y.get("기간") or ""), "효과": y.get("효과") or "",
             "출처": y.get("출처") or "", "태그": "[공시]"}
        if 총출:
            x["총액출처"] = 총출
        if 밀:
            x["주의"] = "열 밀림 의심(기간 칸 「%s」 · 대상 칸 「%s」) — 금액 · 기간 칸을 쓰지 않았다(A3 XML 표로 다시)" % (
                ("%s" % y.get("기간"))[:12], ("%s" % y.get("대상"))[:12])
        프로젝트.append(_새칸(x))
        해들 = sorted(set(re.findall(r"(20\d{2})", "%s" % (y.get("기간") or "")))) if not 밀 else []
        if 기투 is not None and 향후 is not None and 향후 > 0 and len(해들) >= 2 and 성격 == "성장":
            기집행.append({"프로젝트": 구분글, "라인": None, "금액": 기투, "자산군별": {}, "근거딱지": "[공시]",
                        "식": "공시 투자계획 표 기투자액(%s · 향후투자 %s)" % (y.get("기간") or "기간 미상", "{:,.0f}".format(향후)), "출처": y.get("출처") or ""})
        elif 기투 is not None:
            주의.append("투자계획 표 「%s」(%s · 기투자 %s)는 %s — 기집행으로 적지 않았다(실적 CAPEX 에 이미 있다 · 기집행 규칙)" % (
                구분글, y.get("기간") or "기간 미상", "{:,.0f}".format(기투),
                "유지 · 보완 투자" if 성격 == "유지" else ("향후투자가 없다" if not (향후 and 향후 > 0) else "기간이 한 해 안이다")))
    if 거름:
        주의.append("투자계획 표에서 프로젝트가 아닌 조각 %d줄을 걸렀다(%s) — 열 밀림 · 머리 · 합계 · 기간 조각(A3 XML 표 읽기로 바로잡는다)" % (
            len(거름), " · ".join(거름[:6]) + (" 외" if len(거름) > 6 else "")))
    if 밀림:
        주의.append("투자계획 표 %d줄이 한 칸 밀린 꼴이다 — 금액 · 기간 칸을 쓰지 않았다" % 밀림)
    for y in (계.get("진행중") or []):
        if not isinstance(y, dict):
            continue
        이름 = ("%s %s" % (y.get("구분") or "", y.get("대상") or "")).strip()
        조, _까 = 표조각인가(이름)
        if 조:
            continue
        총, 기투 = _수(y.get("총투자")), _수(y.get("기투자"))
        향후 = _수(y.get("향후투자")) if _수(y.get("향후투자")) is not None else ((총 - 기투) if (총 is not None and 기투 is not None) else None)
        프로젝트.append(_새칸({"이름": 이름, "이름출처": "진행중 투자", "능력단위": "", "금액": {}, "총액": 총, "착공": "", "완공": "", "리드타임": None,
                            "성격": "성장" if re.search(r"신규|증설|확장|신설|신축", 이름) else "유지", "기간": y.get("기간") or "", "효과": "",
                            "출처": y.get("출처") or "", "태그": "[공시]"}))
        if 기투 is not None and 향후 and 향후 > 0:
            기집행.append({"프로젝트": 이름, "라인": None, "금액": 기투, "자산군별": {}, "근거딱지": "[공시]",
                        "식": "진행 중 투자 기투자(향후 %s)" % "{:,.0f}".format(향후), "출처": y.get("출처") or ""})
    수주건 = 0
    for y in (계.get("발화") or []):
        if not isinstance(y, dict):
            continue
        문 = y.get("문장") or ""
        if 수주꼴.search(문):
            수주건 += 1
            continue
        이름, 출 = 명사구이름(문)
        프로젝트.append(_새칸({"이름": 이름, "이름출처": 출, "능력단위": "", "금액": {}, "총액": _수(y.get("금액")), "착공": "", "완공": "",
                            "리드타임": None, "성격": "성장", "출처": "%s 「%s」" % (y.get("출처", ""), 문[:80]), "태그": "[회사주장]"}))
    if 수주건:
        주의.append("투자 발화 가운데 수주 문장 %d건(시공사 선정 · 우선협상 · 공급계약 · 수주)을 걸렀다 — 투자가 아니라 매출 쪽(수주잔고 · 매출 노드)" % 수주건)
    # 수시공시(국내 주요사항 · 거래소 · 발행공시 — 계약 4-1)
    수 = 원천들.get("수시공시") if isinstance(원천들.get("수시공시"), dict) else {}
    시설자금 = []
    for d in 수.get("자금사용") or []:
        if not isinstance(d, dict):
            continue
        for h in d.get("항목") or []:
            if isinstance(h, dict) and h.get("목적") == "시설자금" and _수(h.get("금액")) is not None:
                시설자금.append({"문서": d.get("문서") or "", "접수번호": d.get("접수번호") or "", "세부": h.get("세부") or "",
                             "금액": 환산(h["금액"], h.get("통화") or "KRW", 기준단위), "집행": _수(h.get("집행")), "전용": h.get("전용"),
                             "기준일뒤": bool(d.get("기준일뒤"))})
    수주수 = 0
    for x in 수.get("결정") or []:
        if not isinstance(x, dict):
            continue
        종 = x.get("종류") or ""
        금 = x.get("금액") if isinstance(x.get("금액"), dict) else {}
        v = 환산(금.get("값"), 금.get("통화") or "KRW", 기준단위) if 금 else None
        정정 = [{"공시일": z.get("공시일"), "접수번호": z.get("접수번호"), "바뀐칸": z.get("바뀐칸")} for z in (x.get("정정") or []) if isinstance(z, dict)]
        if 종 in ("수주", "공급계약"):
            수주수 += 1
            continue
        if 종 == "유형자산처분":
            처분.append({"이름": x.get("대상") or x.get("제목") or "", "금액": v, "공시일": x.get("공시일"), "기간": x.get("기간") or {},
                       "주체": x.get("주체") or "본사", "기준일뒤": bool(x.get("기준일뒤")), "출처": x.get("출처") or "", "태그": "[공시]",
                       "비고": "능력 감소 후보 — 처분 대상이 생산 시설이면 능력단위 변동(원인 처분)"})
            continue
        if 종 not in ("신규시설투자", "유형자산취득"):
            continue
        기 = x.get("기간") if isinstance(x.get("기간"), dict) else {}
        이름, 이름출처 = 수시공시이름(x, v, 기준단위)
        # 금액 없는 장래사업 · 경영계획 공정공시(투자 가이드라인)는 시설 투자 결정이 아니라 회사 발화 — [회사주장]
        가이드 = (v is None and not ("%s" % (x.get("대상") or "")).strip()
                and bool(re.search(r"장래사업|경영계획|공정공시|가이드라인|계획\s*제시", "%s %s" % (x.get("제목") or "", x.get("목적") or ""))))
        p = _새칸({"이름": 이름, "이름출처": 이름출처, "능력단위": "", "금액": {}, "총액": v,
                  "착공": 기.get("시작") or "", "완공": 기.get("끝") or "", "리드타임": None,
                  "성격": "성장" if 종 == "신규시설투자" or re.search(r"신규|증설|신설|신축|확장", "%s %s" % (x.get("목적") or "", x.get("대상") or "")) else "유지",
                  "기간": "%s ~ %s" % (기.get("시작") or "", 기.get("끝") or "") if 기 else "", "효과": x.get("목적") or "",
                  "출처": "%s · %s %s" % (x.get("출처") or "DART", x.get("접수번호") or "", x.get("공시일") or ""), "태그": "[회사주장]" if 가이드 else "[공시]"},
                 {"투자범위": x.get("투자범위") or "모름", "정정이력": 정정, "연결범위": x.get("주체") or "본사", "기준일뒤": bool(x.get("기준일뒤")),
                  "자기자본대비": x.get("자기자본대비")})
        if 정정:
            바뀐 = [z.get("바뀐칸") for z in 정정 if isinstance(z.get("바뀐칸"), dict)]
            if any("기간.끝" in b for b in 바뀐):
                주의.append("수시공시 「%s」 완료일 정정(%s) — 지연 신호(리드타임 · 램프업)" % (p["이름"][:20], " → ".join(
                    "%s" % b["기간.끝"] for b in 바뀐 if "기간.끝" in b)))
        if p["기준일뒤"]:
            기준일후.append({"날짜": x.get("공시일") or "", "사건": "%s %s" % (종, p["이름"]), "금액": v, "출처": p["출처"]})
            continue
        for s in 시설자금:
            if s["금액"] and v and (abs(s["금액"] - v) / v < 0.01 or (s.get("집행") and abs(s["집행"] - v) / v < 0.01)):
                p["자금출처겹침"].append({"문서": s["문서"], "접수번호": s["접수번호"], "금액": s["금액"]})
        프로젝트.append(p)
    if 수주수:
        주의.append("수시공시 수주 · 공급계약 %d건 — 투자가 아니다(매출 쪽)" % 수주수)
    남은자금 = [s for s in 시설자금 if not any(s["접수번호"] == z["접수번호"] for p in 프로젝트 for z in p.get("자금출처겹침") or [])]
    if 남은자금:
        주의.append("증자 · 사채 시설자금 %d건(합 %s) — 프로젝트와 겹치는지 본선이 본다(같은 돈을 두 번 세지 않는다%s)" % (
            len(남은자금), "{:,.0f}".format(sum(s["금액"] or 0 for s in 남은자금)),
            " · 전용 있음" if any(s.get("전용") for s in 남은자금) else ""))
    # 같은 총액 · 이름이 겹치는 두 줄은 하나로(수시공시 판이 정정 이력을 가진다)
    남 = []
    for x in 프로젝트:
        같은 = next((y for y in 남 if _수(y.get("총액")) and _수(x.get("총액")) and abs(_수(y["총액"]) - _수(x["총액"])) / _수(y["총액"]) < 0.01
                   and (_토막(y["이름"]) & _토막(x["이름"]) or y.get("이름출처") != x.get("이름출처"))), None)
        if 같은:
            if ("%s" % x.get("이름출처")).startswith("수시공시"):
                같은.update({k: x[k] for k in ("정정이력", "투자범위", "착공", "완공") if x.get(k)})
            continue
        남.append(x)
    return 남, 기집행


def 수시공시이름(x, 금액=None, 기준단위=""):
    """R15(2026-10-25 FX2-B) — 수시공시 프로젝트 이름은 공시 제목(「기타경영사항(자율공시)」 · 「[기재정정]…」)이 아니라 본문 칸에서:
    ① 투자 대상(시설명) ② 투자 목적 ③ 둘 다 없거나 제목 꼴이면 「제목(머리표 뺌) 공시일 금액」 으로 유일하게. 상장 종속회사 공시면 앞에 주체 이름.
    → (이름, 이름출처). 회사 사이 교차가 같은 공시 제목을 「같은 시설」 로 잡지 않게 한다."""
    주 = ("%s " % x.get("주체이름")) if (x.get("주체") not in (None, "", "본사") and x.get("주체이름")) else ""
    이 = re.sub(r"\s+", " ", "%s" % (x.get("이름") or "")).strip()          # 원천 수집(FX2-C)이 결정마다 단 이름 — 있으면 그것이 먼저
    if 이 and not 공시제목꼴.search(이) and re.search(r"[가-힣A-Za-z]", 이):
        return (이 if (not 주 or 이.startswith(주.strip())) else 주 + 이).strip(), "수시공시 이름"
    for 칸, 출 in (("대상", "수시공시 대상"), ("목적", "수시공시 목적")):
        t = re.sub(r"\s+", " ", "%s" % (x.get(칸) or "")).strip()
        if t and not 공시제목꼴.search(t) and re.search(r"[가-힣A-Za-z]", t):
            날 = (" (%s)" % x.get("공시일")) if (not isinstance(금액, (int, float)) or not 금액) and x.get("공시일") else ""   # 금액 없는 공시는 날짜로 가른다
            return (주 + (t if len(t) <= 40 else 명사구이름(t)[0]) + 날).strip(), 출       # 표 칸은 이미 명사구 — 길 때만 자른다
    제 = re.sub(r"^\s*(?:\[[^\]]*\]\s*)+", "", "%s" % (x.get("제목") or "")).strip() or ("%s" % (x.get("종류") or "수시공시"))
    금 = ""
    if isinstance(금액, (int, float)) and 금액:
        금 = " %s%s" % ("{:,.0f}".format(금액), (" " + 기준단위) if 기준단위 else "")
    return ("%s%s %s%s" % (주, 제, x.get("공시일") or "", 금)).strip(), "수시공시 제목"


def 명사구이름(문장):
    """S6-15 — 서술 문장에서 뽑은 프로젝트 이름을 30자 안의 명사구로 자른다 → (이름, 이름출처).
    ① 코드꼴 이름(영문 대문자 · 숫자 · & — 「M15X(eXtension)」 · 「P&T7」) ② 「… 팹 · 공장 · 라인 · 캠퍼스 · 클러스터 · 단지 · 센터 · 사업장」 앞의 고유 이름
    ③ 둘 다 없으면 앞 30자를 낱말 경계에서 자른다. 출처는 「서술」(표 칸이 아니다 — ㊷ 명시 대응 전에 본선이 라인 이름과 맞춘다)."""
    글 = re.sub(r"\s+", " ", 문장 or "").strip()
    글 = re.sub(r"^[^가-힣A-Za-z0-9]*(용\s*:\s*)?", "", 글)
    후보 = [x.group(1) for x in re.finditer(r"(?<![A-Za-z0-9&])([A-Z][A-Za-z0-9&]*\d[A-Za-z0-9&]*(?:\([A-Za-z]{2,20}\))?|[A-Z]{2,}&?[0-9A-Z]+)(?![A-Za-z0-9&])", 글)]
    후보 = [x for x in 후보 if not re.fullmatch(r"(AI|IR|SK|LG|US|EU|HBM|DRAM|NAND|CEO|CFO|ESG|IPO|M&A)", x)]
    if 후보:
        return max(후보, key=len)[:30], "서술"
    m = re.search(r"([가-힣A-Za-z0-9]{1,15}\s?(?:반도체\s)?(?:팹|공장|라인|캠퍼스|클러스터|산업단지|단지|센터|사업장))", 글)
    if m:
        return m.group(1).strip()[:30], "서술"
    앞 = 글[:30]
    if len(글) > 30 and " " in 앞:
        앞 = 앞[:앞.rfind(" ")]
    return 앞.strip(), "서술"


def 계약시한칸(원):
    """S6-13 — A3 `계약시한후보`(경영상의 주요계약 절의 끝나는 날이 적힌 계약 줄)를 F 산출 칸으로 옮긴다. **언제나 목록**(FX-B — 옛 판은 글을
    돌려주었다 · 소비처는 목록만 읽는다). 끝이 날짜가 아니라 조건(로열티 기간 · 출시 후 10년)이면 `끝꼴: 조건`. 금액 경로 · 상대는 본선이 원문에서 채운다."""
    후 = 원.get("계약시한후보")
    if not isinstance(후, list):
        return []
    낸 = []
    for x in 후:
        if not isinstance(x, dict):
            continue
        끝 = x.get("끝나는날")
        꼴 = x.get("끝꼴") or ("날짜" if re.search(r"(19|20)\d{2}", "%s" % (끝 or "")) else "조건")
        낸.append({"이름": x.get("이름") or "", "상대": None, "끝나는날": 끝 if 꼴 == "날짜" else None, "끝꼴": 꼴,
                  "조건글": x.get("조건글") or ("" if 꼴 == "날짜" else ("%s" % (끝 or x.get("글") or ""))[:120]),
                  "시작일": x.get("시작일"), "금액경로": "확인 불가 — 원문 계약 조건에서 본선이 옮긴다",
                  "출처": x.get("출처") or "", "글": x.get("글") or "", "태그": "[공시]"})
    return 낸


def _계약시한까닭(원):
    후 = 원.get("계약시한후보")
    if isinstance(후, list):
        return None
    if isinstance(후, str) and 후.strip():
        return 후[:160]
    return "확인 불가 — 동인원천에 계약시한후보가 없다(옛 A3)"


# ── 능력단위 ─────────────────────────────────────────────────────────────────
def 능력단위짓기(원, 상, 원천들, 주의, 확인불가):
    지 = 원.get("사업지표") or {}
    기준해 = _기준해(원)
    능력, 묵은 = [], []
    가줄 = (상.get("가동률") or {}).get("줄") or []
    for 이름, 종류 in 능력지표.items():
        v = 지.get(이름)
        if not isinstance(v, dict) or not isinstance(v.get("값"), dict) or not v["값"]:
            continue
        값 = _fy(v["값"]) or v["값"]
        열 = sorted(값)
        끝해 = _해(열[-1])
        if 끝해 and 기준해 - 끝해 > 지표묵음연수:
            묵은.append("%s(%s · 마지막 %s)" % (v.get("공시이름") or 이름, 종류, 열[-1]))
            continue
        능력.append(_능력줄(v.get("공시이름") or 이름, 종류, v.get("단위", ""), 값, v.get("출처", ""), "물리", "", 원))
    # FX4-F D2 · D3 — 생산능력표 줄을 (품목 · 단위)로 묶어 한 단위의 시계열로(해별 줄 · 보고서마다 다시 적힌 줄 — 앞에 온 최근 보고서 값이 이긴다).
    # 합계 · 소계 줄은 검산 줄이라 단위가 아니다 · 금액 단위의 자산 종류 줄(생산설비의 현황 — 토지 · 건물 장부금액)은 능력이 아니다.
    # 단위가 금액이면 명목금액, 설비 가동시간(인시 · MH 아님)이면 명목시간 — 물리 능력이 아니어서 단위 투자비 · 값짝 · 상한 근거에서 뺀다
    묶음 = {}
    for x in (원.get("생산능력표") or []) if isinstance(원.get("생산능력표"), list) else []:
        if not isinstance(x, dict) or not isinstance(x.get("값"), dict) or not x["값"]:
            continue
        품 = ("%s" % (x.get("품목") or "")).strip()
        단 = "%s" % (x.get("단위") or "")
        if 합계꼴.search(re.sub(r"\s+", " ", 품)) or re.search(r"(?:합|소|총)\s*계\s*$", 품):
            continue
        금액단위 = bool(re.search(r"원|달러|USD|KRW|\$|엔|위안|유로", 단)) and not re.search(r"원료|원단|원통", 단)
        if 금액단위 and re.fullmatch(r"(?:%s|건설중인자산|사용권자산|생산시설)[\w\-()*\s]*" % _자산말, 품):
            continue
        if 금액단위 and re.search(r"매출\s*액|영업\s*(손익|이익|손실)|순\s*이익|자\s*산\s*$|부\s*채|\d\.\s*자산", 품):
            continue                                     # 부문 재무 표(매출액 · 영업손익 · 자산)가 능력 표로 들어온 줄
        if not 단.strip():
            # 단위가 품목 이름 괄호에 박힌 꼴(「컴포넌트(억개) 수동소자 …」) — 괄호 안의 수량 단위를 단위로
            m단 = re.search(r"\(([^)]{0,12}?(?:개|個|㎡|m2|톤|대|매|장|L|리터|GWh|MWh|MW|GW|CGT|MH|배치|kg|Kg|톤/월|천|백만|억)[^)]{0,6})\)", 품)
            if m단:
                단 = m단.group(1).replace("億個", "억개").replace("百万個", "백만개").replace("千", "천")
        키 = (re.sub(r"\W+", "", re.sub(r"\([^)]*\)", "", 품).lower()), re.sub(r"\W+", "", 단.lower()))
        if 키 not in 묶음:
            묶음[키] = {"x": x, "값": {}, "금액": 금액단위, "단위": 단}
        for c, w in x["값"].items():
            if _수(w) is not None and c not in 묶음[키]["값"]:
                묶음[키]["값"][c] = _수(w)
    for 키, m in 묶음.items():
        x, 단 = m["x"], m["단위"]
        기준 = "%s" % (x.get("산출기준") or "모름")
        시간단위 = bool(re.search(r"가동\s*시간|^\s*시간\s*$|hours?", 단, re.I)) and not re.search(r"M\s*/?\s*H|인\s*·?\s*시|공수|man", 단, re.I)
        명목성 = ("명목금액" if (기준 == "금액" or m["금액"]) else "명목시간" if 시간단위 else "실적역산" if 기준 == "실적기준" else "물리")
        # 비율 단위(「톤/월」 · 「/일」 · 「/시간」 · 「/년」)는 흐름이 아니라 속도다 — 중간 열을 연환산하지 않는다(월 능력 20,300 이 40,600 이 되던 FX4-F D3)
        속도 = bool(re.search(r"/\s*(월|일|시간|년|연|month|day|hour|year|yr)|(per|p\.?a\.?)|월\s*$", 단, re.I))
        연간말 = bool(re.search(r"연간|년간|/\s*년|annual", "%s %s %s" % (단, x.get("품목") or "", x.get("주석글") or ""), re.I))
        값 = {}
        for c, w in m["값"].items():
            배 = _연환산배(원, c) or 1.0
            if c.startswith("FY") or 속도:
                배 = 1.0
            else:
                # 중간 열이 그 기간 능력(반기 = 연의 절반)인지 연간 능력(「현재 생산능력」)인지 — 직전 회계연도 값에 대 본다(FX4-F M4)
                앞 = m["값"].get("FY%dA" % ((_해(c) or 0) - 1)) if _해(c) else None
                r = (w / 앞) if 앞 else None
                if r is not None and 0.75 <= r <= 1.35:
                    배 = 1.0
                elif r is None and 연간말:
                    배 = 1.0
            값[c] = w * 배
        if not 값:
            continue
        끝해 = _해(sorted(값, key=lambda k: _해(k) or 0)[-1])
        if 끝해 and 기준해 - 끝해 > 지표묵음연수:
            묵은.append("%s(생산능력표 · 마지막 %s)" % (x.get("품목") or "", 끝해))
            continue
        줄 = _능력줄(x.get("품목") or "", "생산설비", 단 or x.get("단위") or "", 값, x.get("출처") or "", 명목성, 기준, 원)
        if 명목성 in ("명목금액", "명목시간"):
            줄["역할"] = "참고(명목 — 물리 능력 아님)"
        if x.get("주석글"):
            줄["산출식"] = ("%s" % x["주석글"])[:160]
        if any(not c.startswith("FY") for c in m["값"]):
            줄["비고"] = "중간 열(1H 등)은 연환산해 적었다(×%s)" % " · ".join(
                "%s %s" % (c, _연환산배(원, c)) for c in m["값"] if not c.startswith("FY"))
        능력.append(줄)
    미 = 원천들.get("미국원천") if isinstance((원천들 or {}).get("미국원천"), dict) else {}
    for x in 미.get("능력문장") or []:
        if isinstance(x, dict) and _수(x.get("값")) is not None:
            능력.append(_능력줄(("%s" % (x.get("문장") or ""))[:40], "용량" if re.search(r"W\b", "%s" % x.get("단위")) else "생산설비",
                             x.get("단위") or "", {"공시": _수(x["값"])}, x.get("출처") or "미국원천", "물리", "", 원))
    for y in 능력:
        짝 = _이름짝(y["이름"], [g["이름"] for g in 가줄])
        if 짝:
            g = next(g for g in 가줄 if g["이름"] == 짝)
            y["가동률발화"] = "공시 가동률 %.1f%%(%s · 기준 %s) — %s" % (g["값"] * 100, g["기간"], g["기준"], g["근거"])
            y["가동률기준"] = g["기준"] if g["기준"] != "모름" else y.get("가동률기준", "모름")
        if 상.get("위탁"):
            y["외주처"] = "위탁 생산 — 이 능력은 공급사 몫일 수 있다(외부 제약 D)"
        if re.search(r"데이터\s*센터|data ?cent|GW|MW", "%s %s" % (y["이름"], y["단위"]), re.I):
            y["정의"] = "확인 불가 — 계약 · 연결 · 가동 전력 가운데 무엇인지 원문에서 본선이 가린다"
            if "투자동인" in (상.get("역할") or ""):
                y["역할"] = "투자동인 또는 매출상한(사람 확인)"
    if 묵은:
        주의.append("능력 지표의 마지막 공시가 평가기준일보다 %d년 넘게 앞서 쓰지 않았다 — %s" % (지표묵음연수, " · ".join(묵은)))
    return 능력


def _능력줄(이름, 종류, 단위, 값, 출처, 명목성, 가동률기준, 원):
    열 = sorted(값, key=lambda c: (_해(c) or 0, 0 if c.startswith("FY") else 1))
    재 = 원.get("재무시계열") or {}
    변동 = []
    for i in range(1, len(열)):
        증 = 값[열[i]] - 값[열[i - 1]]
        v = 재.get(열[i]) or {}
        원인 = "투자"
        if _수(v.get("사업결합취득")) and _수(v.get("CAPEX")) and _수(v["사업결합취득"]) > 0.5 * _수(v["CAPEX"]):
            원인 = "사업결합"
        elif 증 <= 0:
            원인 = "처분 · 제품 구성 · 산출기준 변경 후보"
        변동.append({"시점": 열[i], "증분": 증, "원인": 원인})
    return {"이름": 이름, "해당없음까닭": "", "종류": 종류, "단위": 단위,
            "엔진자리": "구조.매출구분[s].라인[j] — 판매량산정 = 능력 으로 세우는 구분이면(합류에서 본선이 정한다)",
            "매출구분": None, "명목능력": {"값": 값[열[-1]], "기준시점": 열[-1]},
            "증분일정": [{"시점": 열[i], "증분": 값[열[i]] - 값[열[i - 1]], "출처": 출처} for i in range(1, len(열))],
            "가동률발화": "", "램프업": {}, "역할": "매출상한", "가동률기준": 가동률기준 or "모름", "명목성": 명목성, "변동": 변동,
            "외주처": None, "정의": None, "_시계열": 값}


# ── 단위 능력당 투자비 ──────────────────────────────────────────────────────
def 단위투자짓기(능력, 현금, 결합, 상유, 원, 상출, 확인불가, 주의):
    투자 = {c: v for c, v in 현금.items() if c.startswith("FY")} or 편입합(원)
    투출 = "현금흐름표 유형자산의 취득" if 현금 else "유형자산 편입(취득 + 대체)"
    결합편입 = 편입합(원, "사업결합")
    단위투자 = []
    for x in 능력:
        s = _fy(x["_시계열"])
        열 = sorted(s)
        if x["종류"] in 저량능력:
            확인불가.append({"항목": "단위능력당투자비.%s" % x["이름"],
                         "원인": "확인 불가 — 신규 · 폐쇄 분리 없음(%s 는 저량이라 순증이 신규 능력이 아니다 — 출점 · 퇴역 수가 공시되면 F 갈래가 신규로 잰다)" % x["종류"]})
            continue
        if x.get("명목성") in ("명목금액", "실적역산", "명목시간"):
            확인불가.append({"항목": "단위능력당투자비.%s" % x["이름"],
                         "원인": "명목성 %s — 판가 · 실적으로 움직이는 능력이라 단위 투자비 · 값짝에서 뺀다(J6)" % x["명목성"]})
            continue
        음 = []
        for i in range(1, len(열)):
            증 = s[열[i]] - s[열[i - 1]]
            if 증 <= 0:
                음.append("%s %+.0f" % (열[i], 증))
                continue
            for 시차, c in ((0, 열[i]), (1, _앞(열[i]))):
                if c not in 투자:
                    continue
                성장분 = 투자[c] - (결합.get(c) or 결합편입.get(c) or 0.0) - (상유.get(c) or 0.0)
                if 성장분 <= 0:
                    continue
                단위투자.append({"대상": x["이름"], "라인": None, "값": 성장분 / 증, "단위": "금액/%s" % (x["단위"] or "능력 단위"), "리드타임": 시차,
                              "산식": "(%s %s − 사업결합 − 유지 추정 %s) ÷ 능력 증분(%s)" % (투출, c, 상출, 열[i]), "근거": "유추",
                              "독립": "모름", "같은프로젝트": False, "범위차": "회사 전체 CAPEX ÷ 한 능력 지표 — 라인 · 프로젝트 범위가 다를 수 있다",
                              "제외까닭": "", "출처": "동인원천 — 재무시계열 · 유형자산 · 사업지표"})
        if 음:
            주의.append("능력 증분 ≤ 0(%s — %s) — 제품 구성 · 처분 · 산출기준 변경 후보. 그 해는 단위 투자비를 내지 않았다" % (x["이름"][:20], " · ".join(음)))
    if 능력 and not 단위투자 and not any(y["항목"].startswith("단위능력당투자비") for y in 확인불가):
        주의.append("능력이 늘어난 해에 성장 투자(투자 − 사업결합 − 유지 추정)가 양수인 짝이 없어 단위 능력당 투자비를 재지 못했다")
    return 단위투자


# ── 공시없음 ↔ 확인불가 ─────────────────────────────────────────────────────
_없음꼴 = re.compile(r"확인했고 없었다|해당사항\s*없음|기재\s*없음|공시\s*없음")


def 공시없음모으기(원, 공시없음):
    for 키 in ("가동률공시", "투자계획", "계약시한후보"):
        v = 원.get(키)
        if isinstance(v, str) and _없음꼴.search(v):
            공시없음.append({"항목": 키, "까닭": v[:160]})
    for x in (원.get("공시없음") or []) if isinstance(원.get("공시없음"), list) else []:
        if isinstance(x, dict):
            공시없음.append(x)


def _원문읽음요약(원):
    읽 = 원.get("원문읽음")
    if not isinstance(읽, list):
        return {"보고서수": None, "기준일보고서": None, "비고": "A3 에 원문읽음이 없다(옛 A3)"}
    역할 = {}
    for r in 읽:
        if isinstance(r, dict) and r.get("역할"):
            역할[r["역할"]] = 역할.get(r["역할"], 0) + 1
    return {"보고서수": len(읽), "기준일보고서": any(isinstance(r, dict) and (r.get("기준일보고서") or r.get("역할") == "기준일분기") for r in 읽),
            "정정": sum(1 for r in 읽 if isinstance(r, dict) and r.get("정정")), "경보": 원.get("원문읽음경보"),
            "역할": 역할, "출처시점": 원.get("출처시점") if isinstance(원.get("출처시점"), dict) else None}


def 가이던스짓기(원, 원천들, 기준일후):
    """② 미국원천 capex 가이던스(FX2-C — 금액 · 방향 · 비교기간 · 공표일) → (옛 꼴 목록, 프로젝트 가이던스 행).
    기간마다 한 행 — 기준일까지 공표된 것 가운데 가장 늦은 공표가 현재 값이고 앞선 공표는 `정정이력`. 금액이 없으면 방향만(총액 None).
    공표일이 기준일 뒤면 행을 만들지 않고 `기준일후` 에(값 칸에 넣지 않는다). 태그 [회사주장] · 성격 「가이던스」(성장 · 유지 프로젝트 합에 넣지 않는다)."""
    미 = 원천들.get("미국원천") if isinstance(원천들.get("미국원천"), dict) else {}
    기준단위 = 원.get("단위") or ""
    옛, 기간별 = [], {}
    for g in 미.get("capex가이던스") or []:
        if not isinstance(g, dict):
            continue
        통 = g.get("통화") or "USD"
        하, 상 = 환산(g.get("하한"), 통, 기준단위), 환산(g.get("상한"), 통, 기준단위)
        줄 = {"기간": g.get("기간"), "하한": g.get("하한"), "상한": g.get("상한"), "통화": g.get("통화"), "방향": g.get("방향"),
             "비교기간": g.get("비교기간"), "금융리스포함": g.get("금융리스포함"), "공표일": g.get("공표일"), "출처": g.get("출처"), "태그": "[회사주장]"}
        if g.get("기준일뒤"):
            기준일후.append(dict(줄, 날짜=g.get("공표일") or "", 사건="capex 가이던스 %s%s" % (
                g.get("기간") or "", (" " + g["방향"]) if g.get("방향") else ""), 금액=(하 + 상) / 2 if (하 is not None and 상 is not None) else (하 or 상)))
            continue
        옛.append(줄)
        기간별.setdefault("%s" % (g.get("기간") or ""), []).append((줄, 하, 상))
    행 = []
    for 기, 줄들 in sorted(기간별.items()):
        줄들.sort(key=lambda t: "%s" % (t[0].get("공표일") or ""))
        줄, 하, 상 = 줄들[-1]
        총 = (하 + 상) / 2 if (하 is not None and 상 is not None) else (하 if 하 is not None else 상)
        방 = 줄.get("방향")
        비 = 줄.get("비교기간")
        p = _새칸({"이름": "capex 가이던스 %s%s" % (기, (" (%s%s)" % (방, (" · %s 대비" % 비) if 비 else "")) if 방 else ""),
                  "이름출처": "미국원천 capex 가이던스", "능력단위": "", "금액": {}, "총액": 총, "착공": "", "완공": "", "리드타임": None,
                  "성격": "가이던스", "기간": 기, "효과": "", "출처": "%s · 공표 %s" % (줄.get("출처") or "", 줄.get("공표일") or ""), "태그": "[회사주장]"},
                 {"정정이력": [{"공표일": z.get("공표일"), "하한": z.get("하한"), "상한": z.get("상한"), "방향": z.get("방향")} for z, _a, _b in 줄들[:-1]]})
        p["가이던스"] = {"하한": 하, "상한": 상, "방향": 방, "비교기간": 비, "공표일": 줄.get("공표일"), "금융리스포함": 줄.get("금융리스포함"),
                      "금액없음": 총 is None, "단위": 기준단위}
        행.append(p)
    return 옛, 행


# ── 정리 ─────────────────────────────────────────────────────────────────────
def 정리(원, 가정=None, 원천들=None):
    원천들 = 원천들 or {}
    유형 = 원.get("유형") or {"판정": [], "근거": [], "구분별": {}}
    if isinstance(유형, list):
        유형 = {"판정": 유형, "근거": [], "구분별": {}}
    확인불가, 해당없음목록, 주의, 공시없음, 기준일후, 처분 = [], [], [], [], [], []
    상판 = 상한판정(원, 원천들)
    상 = {"전체": 상판["전체"], "구분별": 상판["구분별"], "상한종류": 상판["상한종류"], "판정순서": 상판["판정순서"],
         "흔들림": 상판["흔들림"], "역할": 상판["역할"], "단위": "", "근거": 상판["근거"]}
    능력 = 능력단위짓기(원, 상판, 원천들, 주의, 확인불가)
    상["단위"] = " · ".join(sorted({x["단위"] for x in 능력 if x["단위"]}))
    if 상["전체"] == "확인 불가":
        확인불가.append({"항목": "능력매출상한", "원인": 상["근거"]})
    elif 상["전체"] == 해당없음:
        해당없음목록.append({"항목": "능력매출상한", "까닭": "%s — 능력이 매출 상한이 아니다" % 상["근거"]})
        # FX4-F D4 — 상한이 아니어도 능력 단위 · 증설은 산출에 남긴다(역할 = 투자동인 · 참고). 종전에는 비워서 수주 산업의 능력 표 48줄이 사라졌다
        # (증설 → 감가상각 · 유지 CAPEX 의 재료이고, 잔고 소화 속도의 참고다). 능력으로 세우려면 본선이 그 구분을 따로 판정한다
        for x in 능력:
            if not ("%s" % x.get("역할", "")).startswith("참고"):
                x["역할"] = "투자동인 · 참고(상한 아님 — %s)" % (상["상한종류"] if 상["상한종류"] not in ("", "없음") else "능력 여유 · 수요가 판매량을 정한다")
        if 능력:
            주의.append("능력이 매출 상한이 아니라고 판정했지만 능력 지표 %d개를 「투자동인 · 참고」 로 남겼다(%s) — 능력으로 세우려면 본선이 그 구분을 따로 판정한다"
                      % (len(능력), " · ".join("%s %s" % (x["이름"][:20], x["명목능력"]["기준시점"]) for x in 능력[:4])))
    elif not 능력:
        확인불가.append({"항목": "능력단위", "원인": "능력이 매출을 묶는다고 판정했는데(%s) 공시에서 능력 지표를 찾지 못했다 — F 갈래 CP2(웹)" % (
            상["상한종류"] or "설비")})
    if 상판["흔들림"]:
        주의.append("능력매출상한 「%s」 은 흔들린다 — %s(사람 확인)" % (상["전체"], 상["근거"][:160]))
    비율, 상유, 상출, 현금, 결합 = CAPEX비율짓기(원, 원천들, 상판, 주의, 확인불가, 가정)
    단위투자 = 단위투자짓기(능력, 현금, 결합, 상유, 원, 상출, 확인불가, 주의)
    프로젝트, 기집행 = 프로젝트짓기(원, 원천들, 주의, 기준일후, 처분)
    if 프로젝트:
        주의.append("공시 투자계획 · 투자 결정 · 발화 %d건을 프로젝트 후보로 적었다 — 금액의 기간 배분 · 라인 대응 · 리드타임 · 기집행 어림(회사 발화 총액 − 예측기간 "
                  "투자 — 딱지 [판단 · 어림]과 식)은 본선이 정한다(기집행 규칙)" % len(프로젝트))
    공시없음모으기(원, 공시없음)
    약정 = 약정짓기(원, 원천들, 공시없음, 확인불가)
    계약시한 = 계약시한칸(원)
    시한까닭 = _계약시한까닭(원)
    if 시한까닭:
        (공시없음 if _없음꼴.search(시한까닭) else 확인불가).append({"항목": "계약시한", ("까닭" if _없음꼴.search(시한까닭) else "원인"): 시한까닭})
    값짝 = []
    if 가정 and 단위투자:
        주의.append("값짝 — 단위 능력당 투자비는 회사 전체 능력 지표로 잰 값이라 라인 단위 짝은 본선이 정한다(이 판은 비운다 · ㊷ 는 같은 회사 라인 사이 · 이 실측과 견준다)")
    for x in 능력:
        시 = x.pop("_시계열", None)
        if isinstance(시, dict) and 시 and "시계열" not in x:
            x["시계열"] = {c: round(v, 6) for c, v in sorted(시.items(), key=lambda kv: (_해(kv[0]) or 0, 0 if kv[0].startswith("FY") else 1))}
    계 = 원.get("투자계획")
    출처종류 = {"동인원천(A3)": "봤다",
             "공시 투자계획 표": ("봤다" if isinstance(계, dict) and 계.get("표") else ("봤고 없었다" if 계 else "못 봤다(동인원천에 없음)")),
             "수시공시(주요사항 · 거래소 · 발행공시)": "봤다" if 원천들.get("수시공시") else "못 봤다(_raw/수시공시.json 없음)",
             "미국 원천(약정 · 가이던스 · RPO · 누계)": "봤다" if 원천들.get("미국원천") else "해당 없음 또는 못 봤다(_raw/미국원천.json 없음)"}
    가이던스, 가행 = 가이던스짓기(원, 원천들, 기준일후)
    시설프로젝트 = bool(프로젝트)
    if 가행:
        프로젝트 = 프로젝트 + 가행
        주의.append("미국원천 capex 가이던스 %d행을 프로젝트(성격 가이던스 · [회사주장])로 옮겼다 — 금액 없는 행은 방향만(%s)" % (
            len(가행), " · ".join("%s %s" % (x["기간"], (x["가이던스"]["방향"] or "금액")) for x in 가행)))
    return {"형식": 형식, "회사": 원.get("회사", ""), "평가기준일": 원.get("평가기준일", ""),
            "재무기준일": 원.get("재무기준일") or 원.get("평가기준일", ""), "조회일": datetime.date.today().isoformat(),
            "유형": 유형, "status": "부분", "사유": "도구 판(--공시만) — CP1 만. CP2(웹 능력 · 단위 투자비 발화 · 리드타임 · 램프업)는 F 갈래",
            "도구판": "도구", "예산실측": {"분": 0, "문서": 0, "출처종류": 출처종류},
            "확인불가": 확인불가 + ([] if 시설프로젝트 else [{"항목": "프로젝트", "원인": "공시 투자계획 표 · 투자 결정 · 발화가 없다 — F 갈래 CP1 손(증권신고서 · IR) · CP2"}]),
            "해당없음": 해당없음목록, "공시없음": 공시없음, "주의": 주의, "체크포인트": "CP1", "능력매출상한": 상, "열람": [], "약정": 약정,
            "고객자금": [x for x in (원.get("고객자금") or []) if isinstance(x, dict)] if isinstance(원.get("고객자금"), list) else [],
            "능력단위": 능력, "프로젝트": 프로젝트, "기집행": 기집행, "처분": 처분, "미종결인수": [], "단위능력당투자비": 단위투자, "값짝": 값짝,
            "CAPEX비율": 비율, "capex가이던스": 가이던스,
            # S6-13 — 계약이 끝을 정한 돈(기술이전 마일스톤 · 장기공급 · 라이선스 · 보조금 협약)의 후보 — 본선이 금액 경로를 원문에서 옮겨 한시적 현금흐름으로 붓는다
            "계약시한": 계약시한, "원문읽음": _원문읽음요약(원),
            "기준일후": 기준일후, "심화_큐_처리": [], "충돌": [], "통지정정": []}


def 옛꼴읽기(산출):
    """투자능력/1(옛 판 · 손 보강판) 파일을 새 칸 기본값으로 채워 읽는다 — 값은 바꾸지 않는다(제자리 고침 · 같은 dict 를 돌려준다)."""
    if not isinstance(산출, dict):
        return 산출
    상 = 산출.get("능력매출상한")
    if isinstance(상, str):
        산출["능력매출상한"] = 상 = {"전체": 상, "구분별": {}, "단위": "", "근거": ""}
    if isinstance(상, dict):
        구 = 상.get("구분별")
        if isinstance(구, dict):
            상["구분별"] = {k: (v if isinstance(v, dict) else {"값": v, "상한종류": "", "근거": ""}) for k, v in 구.items()}
        상.setdefault("판정순서", [])
        상.setdefault("상한종류", "")
    if not isinstance(산출.get("계약시한"), list):
        글 = 산출.get("계약시한")
        산출["계약시한"] = []
        if 글:
            산출.setdefault("확인불가", []).append({"항목": "계약시한", "원인": ("%s" % 글)[:160]})
    for x in 산출.get("약정") or []:
        if isinstance(x, dict):
            x.setdefault("성격", "미분류")
            x.setdefault("기준일뒤", False)
    for x in 산출.get("프로젝트") or []:
        if isinstance(x, dict):
            _새칸(x)
    for x in 산출.get("능력단위") or []:
        if isinstance(x, dict):
            for k, v in (("역할", "매출상한"), ("가동률기준", "모름"), ("명목성", "물리"), ("변동", []), ("외주처", None), ("정의", None)):
                x.setdefault(k, v)
    for 칸 in ("값짝", "단위능력당투자비"):
        for x in 산출.get(칸) or []:
            if isinstance(x, dict):
                x.setdefault("독립", "모름")
    for 칸 in ("고객자금", "처분", "미종결인수", "공시없음"):
        산출.setdefault(칸, [])
    산출.setdefault("형식", "투자능력/1")
    return 산출


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="투자능력 — 능력 · 약정 · 단위 능력당 투자비 · CAPEX 비율(공시만, 업종 중립)")
    ap.add_argument("--공시만", action="store_true", help="CP1 만(약정 · 공시) — 2 · 3등급의 도구 판. 이 판은 공시만 읽는다(인자를 빼도 같다)")
    ap.add_argument("--동인원천", default=os.path.join(ROOT, "_raw", "동인원천.json"))
    ap.add_argument("--가정", default=None)
    ap.add_argument("-o", "--출력", default=None, help="기본 동인원천 곁 투자능력.json")
    a = ap.parse_args()
    try:
        원 = json.load(io.open(a.동인원천, encoding="utf-8"))
    except (OSError, ValueError) as e:
        sys.stderr.write("투자능력 입력 오류 — %s: %s\n" % (a.동인원천, e))
        sys.exit(입력오류)
    가정 = json.load(io.open(a.가정, encoding="utf-8")) if a.가정 else None
    원천들 = 원천읽기(a.동인원천)
    낸 = 정리(원, 가정, 원천들)
    밖 = a.출력 or os.path.join(os.path.dirname(os.path.abspath(a.동인원천)), "투자능력.json")
    with io.open(밖, "w", encoding="utf-8", newline="\n") as f:
        json.dump(낸, f, ensure_ascii=False, indent=1)
        f.write("\n")
    상 = 낸["능력매출상한"]
    print("투자능력(CP1 · %s) — %s · 능력매출상한 %s%s(%s)" % (형식, 밖, 상["전체"], " · 흔들림" if 상.get("흔들림") else "", 상["근거"][:80]))
    for y in 상.get("판정순서") or []:
        print("  판정 %s — %s(%s)" % (y["단계"], y["결과"], y["근거"][:70]))
    for k, v in (상.get("구분별") or {}).items():
        print("  구분 %s — %s(%s)" % (k[:24], v.get("값"), v.get("상한종류")))
    print("  능력단위 %d · 단위능력당투자비 %d · 약정 %d · 프로젝트 후보 %d · 기집행 %d · 처분 %d · 원천 %s" % (
        len(낸["능력단위"]), len(낸["단위능력당투자비"]), len(낸["약정"]), len(낸["프로젝트"]), len(낸["기집행"]), len(낸["처분"]),
        " · ".join(sorted(원천들)) or "동인원천만"))
    for k in ("매출대비CAPEX", "CAPEX대비상각", "SalesToCapital"):
        v = 낸["CAPEX비율"][k]
        print("  %s %s" % (k, " · ".join("%s %.3f" % kv for kv in v.items()) if isinstance(v, dict) else v))
    for x in 낸["확인불가"]:
        print("  확인 불가 %s — %s" % (x["항목"], x.get("원인", "")))
    for x in 낸["공시없음"]:
        print("  공시 없음 %s — %s" % (x.get("항목"), (x.get("까닭") or "")[:80]))
    for x in 낸["해당없음"]:
        print("  해당 없음 %s — %s" % (x["항목"], x["까닭"]))
    sys.exit(통과)


if __name__ == "__main__":
    main()

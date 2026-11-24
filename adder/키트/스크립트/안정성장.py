# -*- coding: utf-8 -*-
"""안정성장 — 영구기간(안정 성장 단계)의 가정이 예측기간 끝과 이어지는지 여섯 자리에서 재고 대안 판을 엔진으로 셈한다(1.1.5).

    python 스크립트/안정성장.py <가정.json> [--낼 _raw/안정성장.json] [--자리 <회차 폴더>]
    python 스크립트/안정성장.py <가정.json> --쓰기 업종성숙|βL1|수렴없음     # 영구기간 자본비용을 그 판으로 가정에 적는다(근거 10 · 14 머리 포함)

**기준 · 비관 · 낙관 시나리오의 값을 바꾸지 않는다**(`--쓰기` 를 주지 않으면). 엔진(엔진.계산)이 낸 값을 읽고, 대안 판은 가정 사본으로 엔진을 다시 돌려
곁에 적는다. 설정은 `스크립트/안정성장설정.json` 한 곳이다. 회사 · 업종 이름은 이 도구에 없다.

  ① 영구베타    영구기간 Levered Beta · D/E 를 업종 성숙 평균 쪽으로(기본) — 사전값과 같은 업종 줄(βU 재료의 축소 블록 「업종」 · 산업대조 줄)의
                현금보정 βU 와 D/E 로 다시 레버한다. 대안 「βL1」(영구 D/E = 업종 D/E · Levered Beta = 1.0 이 되게 βU 를 푼다) · 「수렴없음」
                (영구 = 예측)을 나란히 엔진으로 셈한다. **대칭이다** — 베타가 업종보다 낮은 회사는 영구 베타가 올라가 값이 내려간다.
                업종 줄이 없으면 원고 `관측.업종성숙{βU, DE, 출처}` → 없으면 기본판은 「βL1」(D/E 는 예측기간 값)
  ② 재투자방향  마지막 예측 해 매출 · NOPLAT 증가율 · 재투자율 · 함축 증분 ROIC(NOPLAT 증가율 ÷ 재투자율)를 영구 RONIC · g ÷ RONIC 과 나란히.
                차가 문턱 밖이면 셋 가운데 어느 쪽인지 — 「예측기간 끝의 투자」 · 「영구 RONIC」 · 「g 와 마지막 해 성장」 — 근거 지표를 붙인 후보를 낸다.
                고르지 않는다(판단대장 「재투자 방향」 줄 — 자체검사 55)
  ③ 적자부문    보고부문의 최근 회계연도 영업손실(`_raw/부문매출.json` 「부문매출/1」 · 원고 `관측.적자부문[]`)이 연결 마진 경로에 묶여 영구로
                굳는지. 포기 판(영구기간에 손실이 멈춘 판 — 엔진 손잡이 영구이익률가감) · 가격 표지 판(원고에 외부 거래 · 투자 유치 가격이 있으면)
  ④ 연장감사    마지막 해 성장 낙차(매출 증가율 − g)와 평균 ROIC ÷ WACC 가 문턱을 넘는데 예측기간이 기본 길이 그대로인가
  ⑤ 주식보상    주식보상비용 ÷ 매출(원천 546 · 미국 companyfacts)이 문턱 이상인데 비율 경로를 적지 않았나 · 매출 규모에 따라 줄어드는 판
                (예측 열은 엔진 할인계수로 선형 셈 · 영구기간은 엔진 손잡이로)
  ⑥ 연구개발    미국 회계 · 연구개발비 ÷ 매출 ≥ 문턱인 회사만 — 자본화한 조정 영업이익 · 조정 투하자본 · 조정 ROIC(마지막 실적 회계연도).
                측정 보조 표다 — 주당가치를 바꾸지 않는다(조정 NOPLAT 증가 = 조정 재투자 증가 · FCFF 그대로)
  ⑦ RONIC정합   (1.1.6) 영구 RONIC 이 예측기간과 같은 투하자본 정의를 쓰나 — 매출자본비율 × 영구기간 세후 영업이익률이 함축하는 증분 수익률 ·
                기존 자본 수익률(마지막 해 평균 ROIC)을 RONIC 과 견준다. 자산 경량 회사(매출자본비율 ≥ 문턱)는 ⑥ 의 조정 ROIC 를 RONIC 의 기준으로
                함께. RONIC 을 바꾸지 않는다 — 판단대장 「RONIC 기준」 줄(자체검사 60)이 요건이다

산출 가정 곁 `_raw/안정성장.json` — 「안정성장/1」: 형식 · 만든날 · 가정해시 · 기준주당 · 영구베타 · 재투자방향 · 적자부문 · 연장감사 · 주식보상 ·
연구개발 · RONIC정합 · 신호[] · 값을바꿈: false. 레터는 장부 키 「파일:안정성장:…」 로 숫자를 부른다(게이트가 해시로 같은 파일인지 본다).
종료 코드 — 0 통과 · 2 입력오류(가정 파일 없음 · JSON 깨짐 · 엔진 계산 실패).
"""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import io
import json
import os
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 입력오류  # noqa: E402

형식 = "안정성장/1"
산출이름 = "안정성장.json"
설정파일 = os.path.join(여기, "안정성장설정.json")
판이름 = {"업종성숙": "업종 성숙 평균", "βL1": "Levered Beta 1.0", "수렴없음": "수렴 없음", "그밖": "손으로 적은 값"}
판차례 = ("업종성숙", "βL1", "수렴없음")
방향말 = {"투자": "예측기간 끝의 투자", "RONIC": "영구 RONIC", "g": "영구성장률 g"}


def 설정():
    try:
        with io.open(설정파일, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _n(x):
    try:
        return None if x is None or isinstance(x, bool) else float(x)
    except (TypeError, ValueError):
        return None


def _계산(가정, 시나리오="기준"):
    from 엔진.계산 import 계산                               # noqa: PLC0415
    return 계산(가정, 시나리오)


def _주당(R):
    return _n((R.get("요약") or {}).get("주당가치"))


def _변화(a, b):
    a, b = _n(a), _n(b)
    return (a / b - 1) if (a is not None and b) else None


def 관할(가정):
    m = (가정.get("메타") or {}) if isinstance(가정, dict) else {}
    k = ("%s" % (m.get("관할") or "")).strip().upper()
    if k:
        return k
    return {"KRW": "KR", "USD": "US"}.get(("%s" % (m.get("표시통화") or "KRW")).strip().upper(), "기타")


def 미국회계(가정, 자리=None):
    """연구개발비를 전액 비용으로 두는 회계(US GAAP)인가 — 메타.회계기준이 있으면 그것, 없으면 관할 US 이고 companyfacts 가 있는가."""
    m = 가정.get("메타") or {}
    기 = ("%s" % (m.get("회계기준") or "")).upper().replace(" ", "")
    if 기:
        return 기 in ("USGAAP", "US-GAAP")
    if 관할(가정) != "US":
        return False
    return bool(자리 and os.path.exists(os.path.join(자리, "_raw", "companyfacts.json"))) or 관할(가정) == "US"


# ══════════════════════════════════════════════════════════════════ ① 영구 베타 · 부채비율 수렴
def 업종줄(자리, 가정):
    """사전값과 같은 업종 줄 → {줄, 지역, βU현금보정, βU, DE, βL, 세율, 현금비중, 출처, 파일} 또는 None.
    차례 — βU 재료(`피어경로.βU재료고르기`)의 축소 블록 「업종」(지역 · 줄)과 같은 산업대조 줄 → 산업대조 머리 줄 · 지역 → 원고 `관측.업종성숙`."""
    import 피어경로                                         # noqa: PLC0415
    고 = 피어경로.βU재료고르기(자리, 가정) if 자리 else None
    if 고:
        try:
            d = json.load(io.open(고["경로"], encoding="utf-8"))
        except (OSError, ValueError):
            d = {}
        b = (d.get("본값") or {}) if isinstance(d, dict) else {}
        축 = b.get("축소") if isinstance(b.get("축소"), dict) else ((b.get("세겹") or {}).get("축소규칙") if isinstance(b.get("세겹"), dict) else None)
        업 = (축 or {}).get("업종") or {}
        산 = b.get("산업대조") or {}
        줄들 = [x for x in (산.get("산업") or []) if isinstance(x, dict)]
        고른 = None
        for 지, 이름 in ((업.get("지역"), 업.get("줄")), (산.get("지역"), 산.get("줄"))):
            if not 이름:
                continue
            고른 = next((x for x in 줄들 if x.get("줄") == 이름 and (not 지 or x.get("지역") == 지)), None)
            if 고른:
                break
        if 고른 and _n(고른.get("βU현금보정")) is not None and _n(고른.get("DE")) is not None:
            return {"줄": 고른.get("줄"), "지역": 고른.get("지역"), "βU현금보정": _n(고른.get("βU현금보정")), "βU": _n(고른.get("βU")),
                    "DE": _n(고른.get("DE")), "βL": _n(고른.get("βL")), "세율": _n(고른.get("세율")), "현금비중": _n(고른.get("현금비중")),
                    "판": 고른.get("판"), "출처": "βU 재료 산업대조(사전값 업종 줄)", "파일": 고["상대"]}
    관 = ((가정.get("관측") or {}).get("업종성숙")) if isinstance(가정, dict) else None
    if isinstance(관, dict) and _n(관.get("βU")) is not None and _n(관.get("DE")) is not None:
        return {"줄": 관.get("줄"), "지역": 관.get("지역"), "βU현금보정": _n(관["βU"]), "βU": None, "DE": _n(관["DE"]), "βL": _n(관.get("βL")),
                "세율": None, "현금비중": None, "출처": "원고 관측.업종성숙 — %s" % (관.get("출처") or "출처 없음"), "파일": None}
    return None


def _βu풀기(βL, de, t, bd):
    """Levered Beta 가 βL 이 되는 (현금 조정) βU — 하마다 βL = βU(1 + (1 − t)D/E) · 일반형 βL = βU + (βU − βD)(1 − t)D/E."""
    k = (1 - t) * de
    return (βL + (bd or 0.0) * k) / (1 + k)


def _판가정(가정, 칸, 통째=False):
    """영구기간 칸을 바꾼 가정 사본 — 구조.할인.영구WACC = 따로(연도별 WACC 는 건드리지 않는다). 통째면 영구기간을 칸으로 갈아 끼운다
    (수렴없음 — 예측기간 사본. 예측기간에 없는 키(목표 D/E 따위)가 영구기간에 남지 않게). 값이 None 인 칸은 지운다(빈칸 = 기본 — 기준일 D/E · 하마다)."""
    g = copy.deepcopy(가정)
    할 = g.setdefault("구조", {}).setdefault("할인", {})
    할["영구WACC"] = "따로"
    W = g.setdefault("WACC", {})
    if 통째:
        W["영구기간"] = {}
    영 = W.setdefault("영구기간", {})
    for k, v in 칸.items():
        if v is None:
            영.pop(k, None)
        else:
            영[k] = v
    return g


def _WACC칸(R, 구간):
    w = ((R.get("WACC") or {}).get(구간)) or {}
    return {k: w.get(k) for k in ("베타u", "현금보정베타u", "DE", "베타l", "Ke", "Kd", "WACC", "한계세율", "부채베타")}


def _같다(a, b, 허):
    a, b = _n(a), _n(b)
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return abs(a - b) <= 허 * max(1.0, abs(b))


def 영구베타(가정, R, 자리, 설=None):
    s = ((설 or 설정()).get("영구베타") or {})
    허 = float(s.get("같음허용", 1e-6))
    예W = (가정.get("WACC") or {}).get("예측기간") or {}
    영W = (가정.get("WACC") or {}).get("영구기간") or {}
    예R, 영R = _WACC칸(R, "예측기간"), _WACC칸(R, "영구기간")
    t = _n(영R.get("한계세율")) or 0.0
    bd = _n(영W.get("부채베타"))
    업 = 업종줄(자리, 가정)
    낸 = {"업종": 업, "예측기간": 예R, "채택영구": 영R, "영구WACC선언": (((가정.get("구조") or {}).get("할인") or {}).get("영구WACC") or "예측과같음"),
         "기준주당": _주당(R), "판": [], "근거": s.get("_근거")}
    de예 = _n(예R.get("DE"))
    판칸 = {"수렴없음": {"베타u": _n(예R.get("베타u")), "현금비중": _n(예W.get("현금비중")) or 0.0, "DE": _n(예W.get("DE")),
                       "부채베타": _n(예W.get("부채베타"))}}
    if 업:
        판칸["업종성숙"] = {"베타u": 업["βU현금보정"], "현금비중": 0.0, "DE": 업["DE"], "부채베타": bd}
    목표 = float(s.get("βL목표", 1.0))
    de1 = 업["DE"] if 업 else de예
    if de1 is not None:
        판칸["βL1"] = {"베타u": _βu풀기(목표, de1, t, bd), "현금비중": 0.0, "DE": de1, "부채베타": bd}
    기본 = s.get("기본판", "업종성숙") if (s.get("기본판", "업종성숙") in 판칸) else ("βL1" if "βL1" in 판칸 else "수렴없음")
    낸["기본판"] = 기본
    if not 업:
        낸["업종까닭"] = "업종 줄이 없다(βU 재료의 산업대조 · 원고 관측.업종성숙) — 기본판을 「%s」로 둔다" % 판이름[기본]
    # 채택 — 지금 가정의 영구기간 칸이 어느 판과 같은가(같은 판이 없으면 「그밖」)
    if 낸["영구WACC선언"] != "따로":
        채 = "수렴없음"
    else:
        채 = "그밖"
        for 이름 in 판차례:
            칸 = 판칸.get(이름)
            if 칸 and _같다(영R.get("현금보정베타u"), (칸["베타u"] or 0) / max(1e-12, 1 - (칸["현금비중"] or 0)), 허) and _같다(영R.get("DE"), 칸["DE"] if 칸["DE"] is not None else de예, 허):
                채 = 이름
                break
    낸["채택"] = 채
    for 이름 in 판차례:
        칸 = 판칸.get(이름)
        if not 칸:
            continue
        줄 = {"판": 이름, "이름": 판이름[이름], "칸": 칸}
        try:
            if 이름 == 채:
                R2 = R
            else:
                R2 = _계산(_판가정(가정, 칸) if 이름 != "수렴없음" else _판가정(가정, dict(copy.deepcopy(예W), 베타u=_n(예R.get("베타u"))), 통째=True), "기준")
            줄.update({"영구": _WACC칸(R2, "영구기간"), "주당": _주당(R2)})
            줄["채택대비"] = _변화(줄["주당"], 낸["기준주당"])
        except Exception as e:                               # noqa: BLE001 — 가정오류(g ≥ 영구 WACC 따위)는 그 판만 비운다
            줄["까닭"] = "셈 실패 — %s" % e
        낸["판"].append(줄)
    b = next((x for x in 낸["판"] if x["판"] == 기본), None)
    n0 = next((x for x in 낸["판"] if x["판"] == "수렴없음"), None)
    if b and b.get("영구") and _n(예R.get("베타l")) is not None:
        d = (_n(b["영구"].get("베타l")) or 0) - _n(예R["베타l"])
        낸["방향"] = "올라감" if d > 1e-9 else ("내려감" if d < -1e-9 else "같음")
        낸["베타차"] = d
    낸["기본판주당"] = b.get("주당") if b else None
    낸["기본판변화"] = b.get("채택대비") if b else None
    낸["수렴없음대비"] = _변화(b.get("주당"), n0.get("주당")) if (b and n0) else None
    문 = float(s.get("값문턱", 0.02))
    낸["경보"] = bool(채 != 기본 and 낸["기본판변화"] is not None and abs(낸["기본판변화"]) >= 문)
    낸["값문턱"] = 문
    return 낸


def 쓰기판(가정, 영, 판):
    """`--쓰기` — 영구기간 자본비용을 그 판으로 가정에 적는다(구조.할인.영구WACC · WACC.영구기간 · WACC근거 10 · 14 머리). → (가정, 글)."""
    줄 = next((x for x in 영["판"] if x["판"] == 판), None)
    if not 줄:
        raise ValueError("판 「%s」 을 셈하지 못했다(업종 줄이 없거나 셈 실패) — 고를 수 있는 판: %s" % (판, " · ".join(x["판"] for x in 영["판"])))
    g = copy.deepcopy(가정)
    할 = g.setdefault("구조", {}).setdefault("할인", {})
    W = g.setdefault("WACC", {})
    if 판 == "수렴없음":
        할["영구WACC"] = "예측과같음"
        W["영구기간"] = copy.deepcopy(W.get("예측기간") or {})
        머리 = "[영구 수렴 없음] 영구기간 자본비용 = 예측기간"
    else:
        할["영구WACC"] = "따로"
        영W = W.setdefault("영구기간", copy.deepcopy(W.get("예측기간") or {}))
        for k, v in 줄["칸"].items():
            if v is None:
                영W.pop(k, None)
                continue
            영W[k] = v
        업 = 영.get("업종") or {}
        if 판 == "업종성숙":
            머리 = ("[영구 수렴] 영구기간 βU %.4f · D/E %.4f — 업종 성숙 평균(%s %s 현금보정 βU · 업종 D/E · %s) · 영구 βL %.3f"
                  % (줄["칸"]["베타u"], 줄["칸"]["DE"], 업.get("줄") or "업종", 업.get("지역") or "", 업.get("출처") or "",
                     _n((줄.get("영구") or {}).get("베타l")) or 0))
        else:
            머리 = ("[영구 수렴] 영구기간 βU %.4f — Levered Beta 1.0 이 되는 값(영구 D/E %.4f%s)"
                  % (줄["칸"]["베타u"], 줄["칸"]["DE"], " — 업종 D/E" if 업 else " — 예측기간 D/E"))
    근 = g.setdefault("WACC근거", {})
    자리 = []
    for 번 in ("10", "14"):
        옛 = 근.get(번)
        옛글 = (옛[0] if isinstance(옛, list) and 옛 else (옛 if isinstance(옛, str) else "")) or ""
        if "(출처 —" in 옛글 or "(기준일 —" in 옛글:                # 1.1.15 — 예측기간 근거가 템플릿 자리표시다(이 도구는 영구 머리만 적는다 — 알린다)
            자리.append(번)
        if "[영구 수렴" in 옛글 and " / 예측기간 — " in 옛글:
            옛글 = 옛글.split(" / 예측기간 — ", 1)[1]
        elif 옛글.startswith("[영구 수렴"):
            옛글 = ""
        새 = 머리 + (" / 예측기간 — " + 옛글 if 옛글 else "")
        if isinstance(옛, list) and 옛:
            근[번] = [새] + list(옛[1:])
        else:
            근[번] = [새, (가정.get("메타") or {}).get("평가기준일") or "", "확인완료", "안정성장.py --쓰기 %s" % 판]
    덧 = (" · 예측기간 근거(WACC근거 %s)가 템플릿 자리표시다 — 이 도구는 영구기간 머리만 적는다. 예측기간 근거를 사실로 채운다(자체검사 경보)"
          % " · ".join(자리)) if 자리 else ""
    return g, "%s → %s(주당 %s · 채택 대비 %s)%s" % (판이름.get(영["채택"]), 판이름[판], _수글(줄.get("주당")), _p(줄.get("채택대비")), 덧)


# ══════════════════════════════════════════════════════════════════ ② 재투자 방향
def _축(가정):
    from 엔진.읽개 import 축내기                              # noqa: PLC0415
    return 축내기(가정)


def 재투자방향(가정, R, 설=None):
    s = ((설 or 설정()).get("재투자방향") or {})
    문 = float(s.get("재투자율차문턱", 0.15))
    lo, hi = (s.get("ROIC배") or [0.5, 2.0])[:2]
    g차 = float(s.get("g차문턱", 0.005))
    축 = _축(가정)
    끝i = 축.끝예측
    앞i = 끝i - 1 if (끝i - 1) in 축.예측 else None
    끝, 앞 = 축.ID[끝i], (축.ID[앞i] if 앞i is not None else None)
    년끝 = 축.열[끝i].년 or 1.0
    d = R["2.DCF"]
    요 = R.get("요약") or {}
    넷 = {x["기준"][:1]: x for x in ((R.get("부수") or {}).get("안정성장4기준") or [])}
    참 = (넷.get("④") or {}).get("참고") or {}
    매출성장 = _n((R["4.Sales"].get("56") or {}).get(끝))
    nop끝 = _n((d.get("19") or {}).get(끝))
    nop앞 = _n((d.get("19") or {}).get(앞)) if 앞 else None
    년앞 = (축.열[앞i].년 or 1.0) if 앞i is not None else None
    nop성장 = ((nop끝 / 년끝) / (nop앞 / 년앞) - 1) if (nop끝 and nop앞 and nop앞 > 0) else None
    재투자 = None
    if all(_n((d.get(k) or {}).get(끝)) is not None for k in ("21", "20", "22")) and nop끝:
        재투자 = (_n(d["21"][끝]) - _n(d["20"][끝]) + _n(d["22"][끝])) / nop끝
    g, ronic, 영재 = _n(요.get("영구성장률")), _n(요.get("영구ROIC")), _n(요.get("재투자율"))
    함축 = (nop성장 / 재투자) if (nop성장 is not None and 재투자 and 재투자 > 0) else None
    낸 = {"끝열": 끝, "앞열": 앞, "매출성장": 매출성장, "NOPLAT성장": nop성장, "재투자율": 재투자, "함축증분ROIC": 함축,
         "증분ROIC": _n(참.get("증분ROIC")), "증분ROIC구간": 참.get("증분ROIC구간"), "평균ROIC": _n(참.get("평균ROIC(마지막해)")),
         "마지막해WACC": _n(참.get("마지막해WACC")), "g": g, "RONIC": ronic, "영구재투자율": 영재,
         "문턱": {"재투자율차": 문, "ROIC배": [lo, hi], "g차": g차}}
    낸["재투자율차"] = (재투자 - 영재) if (재투자 is not None and 영재 is not None) else None
    낸["ROIC배"] = (함축 / ronic) if (함축 is not None and ronic) else None
    if _n((R["8.CapEx"].get("31") or {}).get(끝)) == 0 and 재투자 is not None and 재투자 <= 0:
        낸["판정"] = "해당 없음 — 자본경량(마지막 해 순재투자 0 이하)"
        낸["요건"] = False
        return 낸
    if nop성장 is not None and nop성장 <= 0:
        낸["판정"] = "해당 없음 — 마지막 해 NOPLAT 이 줄어든다(마진 정상화 구간 — 증분 ROIC 가 성장과 재투자의 다리를 재지 않는다)"
        낸["요건"] = False
        return 낸
    밖차 = 낸["재투자율차"] is not None and abs(낸["재투자율차"]) > 문
    밖배 = 낸["ROIC배"] is not None and not (lo <= 낸["ROIC배"] <= hi)
    낸["요건"] = bool(밖차 or 밖배)
    if not 낸["요건"]:
        낸["판정"] = "정합 — 마지막 해 재투자율과 g ÷ RONIC 이 문턱 안"
        return 낸
    낮다 = (낸["재투자율차"] is not None and 낸["재투자율차"] < 0) or (낸["재투자율차"] is None and 낸["ROIC배"] is not None and 낸["ROIC배"] > hi)
    낸["쪽"] = "마지막 해 재투자가 영구보다 가볍다" if 낮다 else "마지막 해 재투자가 영구보다 무겁다"
    p = 낸["평균ROIC"]
    if 낮다:
        후 = [("투자", "예측기간 끝의 투자가 낮다", 함축 is not None and ronic is not None and 함축 > ronic * hi,
              "마지막 해 함축 증분 ROIC %s 가 RONIC %s 의 %.1f배" % (_p0(함축), _p0(ronic), (함축 / ronic) if (함축 and ronic) else 0)),
             ("RONIC", "영구 RONIC 이 낮다", p is not None and ronic is not None and p > ronic * hi,
              "마지막 해 기존 자본 수익률(평균 ROIC) %s · RONIC %s" % (_p0(p), _p0(ronic))),
             ("g", "g 가 마지막 해 성장보다 높다", g is not None and 매출성장 is not None and g > 매출성장 + g차,
              "g %s · 마지막 해 매출 증가율 %s" % (_p0(g), _p0(매출성장)))]
    else:
        후 = [("투자", "예측기간 끝의 투자가 높다", 함축 is not None and ronic is not None and 함축 < ronic * lo,
              "마지막 해 함축 증분 ROIC %s 가 RONIC %s 보다 낮다" % (_p0(함축), _p0(ronic))),
             ("RONIC", "영구 RONIC 이 높다", p is not None and ronic is not None and p < ronic * lo,
              "마지막 해 기존 자본 수익률(평균 ROIC) %s · RONIC %s" % (_p0(p), _p0(ronic))),
             ("g", "g 가 마지막 해 성장보다 낮다", g is not None and 매출성장 is not None and g < 매출성장 - g차,
              "g %s · 마지막 해 매출 증가율 %s" % (_p0(g), _p0(매출성장)))]
    낸["후보"] = [{"키": k, "말": 말, "지표가가리킴": bool(b), "근거": 글} for k, 말, b, 글 in 후]
    낸["판정"] = "방향 판정 요건 — %s(재투자율 %s · g ÷ RONIC %s · 함축 증분 ROIC ÷ RONIC %s)" % (
        낸["쪽"], _p0(재투자), _p0(영재), ("%.2f배" % 낸["ROIC배"]) if 낸["ROIC배"] is not None else "—")
    return 낸


def 판단대장줄(자리, 말="재투자 방향"):
    """회차 폴더의 `_기록/판단대장.md`(없으면 `판단대장.md`)에서 그 말이 든 줄 → [(파일, 줄 번호, 글)]."""
    낸 = []
    for p in (os.path.join(자리 or "", "_기록", "판단대장.md"), os.path.join(자리 or "", "판단대장.md")):
        if not 자리 or not os.path.exists(p):
            continue
        try:
            for i, x in enumerate(io.open(p, encoding="utf-8"), 1):
                if 말 in x:
                    낸.append((os.path.relpath(p, 자리).replace(os.sep, "/"), i, x.strip()[:300]))
        except OSError:
            continue
    return 낸


# ══════════════════════════════════════════════════════════════════ ③ 공시된 적자 부문
def _FY(id_):
    return isinstance(id_, str) and id_.startswith("FY") and id_.endswith("A")


def _손잡이판(가정, 가감):
    g = copy.deepcopy(가정)
    m = g.setdefault("_민감도", {})
    m["영구이익률가감"] = (_n(m.get("영구이익률가감")) or 0.0) + 가감
    return g


def 주당계수(가정, R):
    """재무기준일 주주가치 1(금액 단위)이 평가기준일 주당가치를 얼마나 움직이나 — 이월계수 × 환산배율 ÷ 적용주식수(갭해석과 같은 셈)."""
    요 = R.get("요약") or {}
    배 = float(((가정.get("메타") or {}).get("환산배율")) or 1)
    주 = _n(요.get("적용주식수"))
    이 = _n(요.get("이월계수")) if 요.get("이월적용", True) and _n(요.get("이월계수")) else 1.0
    return (이 * 배 / 주) if 주 else None


def 적자부문(가정, R, 자리, 설=None):
    s = ((설 or 설정()).get("적자부문") or {})
    문 = float(s.get("손실문턱", 0.01))
    배 = float(((가정.get("메타") or {}).get("환산배율")) or 1)
    매출 = ((가정.get("원천") or {}).get("62")) or {}
    FY들 = sorted(k for k in 매출 if _FY(k) and _n(매출[k]))
    끝FY = FY들[-1] if FY들 else None
    후 = []
    p = os.path.join(자리 or "", "_raw", "부문매출.json")
    if 자리 and os.path.exists(p):
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except (OSError, ValueError):
            d = {}
        멤 = {x.get("멤버"): x for x in (d.get("멤버") or []) if isinstance(x, dict)}
        손 = ((d.get("값표") or {}).get("손익")) or {}
        매 = ((d.get("값표") or {}).get("매출")) or {}
        for 이름, 칸 in 손.items():
            종 = (멤.get(이름) or {}).get("종류")
            if 종 not in ("보고부문", "기타"):
                continue
            해 = sorted(k for k, v in (칸 or {}).items() if _FY(k) and isinstance(v, dict) and _n(v.get("값")) is not None)
            if not 해:
                continue
            f = 끝FY if (끝FY in 해) else 해[-1]
            v = _n(칸[f]["값"])
            후.append({"이름": (멤.get(이름) or {}).get("이름") or 이름, "멤버": 이름, "해": f, "영업손익": v / 배,
                      "부문매출": (_n(((매.get(이름) or {}).get(f) or {}).get("값")) or 0) / 배 or None,
                      "앞해": [{"해": k, "영업손익": _n(칸[k]["값"]) / 배} for k in 해[-int(s.get("최근연수", 2)):]],
                      "출처": "_raw/부문매출.json(%s · %s)" % (칸[f].get("양식") or "공시", 칸[f].get("접수번호") or "접수번호 없음")})
    선언 = [x for x in (((가정.get("관측") or {}).get("적자부문")) or []) if isinstance(x, dict)]
    for x in 선언:                                           # 원고가 적은 부문(국내 주석 · 공시가 XBRL 로 주지 않는 부문) — 이름이 같으면 원고가 이긴다
        손익 = x.get("영업손익") if isinstance(x.get("영업손익"), dict) else {}
        해 = sorted(k for k in 손익 if _FY(k) and _n(손익[k]) is not None)
        이미 = next((h for h in 후 if h["이름"] == x.get("이름") or h["멤버"] == x.get("멤버")), None)
        if 이미:
            이미["선언"] = x
            continue
        if not 해:
            continue
        후.append({"이름": x.get("이름"), "멤버": x.get("멤버"), "해": 해[-1], "영업손익": _n(손익[해[-1]]),
                  "부문매출": _n((x.get("매출") or {}).get(해[-1])) if isinstance(x.get("매출"), dict) else None,
                  "앞해": [{"해": k, "영업손익": _n(손익[k])} for k in 해[-int(s.get("최근연수", 2)):]],
                  "출처": "원고 관측.적자부문 — %s" % (x.get("출처") or "출처 없음"), "선언": x})
    계수 = 주당계수(가정, R)
    기준 = _주당(R)
    d2 = R.get("2.DCF") or {}
    m영 = _n((R.get("요약") or {}).get("영구기간영업이익률"))
    부문 = []
    for h in 후:
        if h["영업손익"] is None or h["영업손익"] >= 0:
            continue
        연 = _n(매출.get(h["해"]))
        h["연결매출"] = 연
        h["손실비"] = (-h["영업손익"] / 연) if 연 else None
        if h["손실비"] is None or h["손실비"] < 문:
            continue
        # 묶인 몫 — 다른 부문 마진을 그 회계연도 그대로 두고 이 부문 손실만 걷은 연결 마진(m 뺌)과 영구기간 영업이익률(m 영구)의 차.
        #   m 영구 ≥ m 뺌 이면 모델의 영구 마진이 이미 그 손실을 걷은 만큼 높다(굳지 않음) · m 영구 ≤ 그 해 연결 마진이면 손실 비율이 통째로 남았다
        ebit = _n((d2.get("15") or {}).get(h["해"]))
        rev = _n((d2.get("11") or {}).get(h["해"])) or 연
        h["연결마진"] = (ebit / rev) if (ebit is not None and rev) else None
        h["뺀마진"] = (h["연결마진"] + h["손실비"]) if h["연결마진"] is not None else None
        h["영구마진"] = m영
        h["묶인몫"] = (max(0.0, min(h["손실비"], h["뺀마진"] - m영)) if (h["뺀마진"] is not None and m영 is not None) else h["손실비"])
        선 = h.get("선언") or {}
        h["처리"] = 선.get("처리")
        h["굳음"] = bool(h["묶인몫"] >= 문 and not (선.get("처리") and (선.get("근거") or 선.get("출처"))))
        if h["묶인몫"] <= 0:
            h["포기판주당"], h["포기판변화"] = 기준, 0.0
            부문.append(h)
            h.pop("선언", None)
            continue
        try:
            R2 = _계산(_손잡이판(가정, h["묶인몫"]), "기준")
            h["포기판주당"] = _주당(R2)
            h["포기판변화"] = _변화(h["포기판주당"], 기준)
        except Exception as e:                               # noqa: BLE001
            h["까닭"] = "포기 판 셈 실패 — %s" % e
        표 = 선.get("가격표지") if isinstance(선.get("가격표지"), dict) else None
        if 표 and _n(표.get("금액")) is not None and 계수:
            몫 = _n(표.get("회사몫")) if _n(표.get("회사몫")) is not None else 1.0
            h["가격표지"] = {k: 표.get(k) for k in ("금액", "회사몫", "날짜", "종류", "출처")}
            h["가격표지"]["주당"] = _n(표["금액"]) * 몫 * 계수
            if h.get("포기판주당") is not None:
                h["가격표지판주당"] = h["포기판주당"] + h["가격표지"]["주당"]
                h["가격표지판변화"] = _변화(h["가격표지판주당"], 기준)
        h.pop("선언", None)
        부문.append(h)
    return {"부문": 부문, "손실문턱": 문, "끝FY": 끝FY, "기준주당": 기준, "근거": s.get("_근거"),
            "셈": "묶인 몫 = min(손실 ÷ 연결 매출, max(0, (그 해 연결 마진 + 손실 ÷ 연결 매출) − 영구기간 영업이익률)) — 다른 부문 마진을 그 해 그대로 둔 근사 · "
                  "포기 판 = 영구기간 영업이익에 묶인 몫 × 영구기간 매출을 더한 판(엔진 손잡이 영구이익률가감)",
            "경보": [h["이름"] for h in 부문 if h.get("굳음")]}


# ══════════════════════════════════════════════════════════════════ ④ 연장 트리거 감사
def 연장감사(가정, R, 설=None):
    s = ((설 or 설정()).get("연장감사") or {})
    기 = 가정.get("기간") or {}
    넷 = {x["기준"][:1]: x for x in ((R.get("부수") or {}).get("안정성장4기준") or [])}
    성장 = _n((넷.get("①") or {}).get("값"))
    g = _n((넷.get("①") or {}).get("종착"))
    참 = (넷.get("④") or {}).get("참고") or {}
    roic, w = _n(참.get("평균ROIC(마지막해)")), _n(참.get("마지막해WACC"))
    낙차 = (성장 - g) if (성장 is not None and g is not None) else None
    배 = (roic / w) if (roic is not None and w) else None
    상세, 수렴 = int(_n(기.get("상세추정연수")) or 0), int(_n(기.get("수렴연수")) or 0)
    늘림 = 수렴 > 0 or 상세 > int(s.get("기본상세연수", 5))
    a = 낙차 is not None and 낙차 > float(s.get("성장낙차문턱", 0.02)) + 1e-9      # 문턱과 같은 값(입력이 g + 문턱)은 넘지 않은 것으로
    b = 배 is not None and 배 > float(s.get("ROIC배문턱", 1.5)) + 1e-9
    return {"마지막해매출성장": 성장, "g": g, "성장낙차": 낙차, "평균ROIC": roic, "마지막해WACC": w, "ROIC배": 배,
            "ROIC폭": (roic - w) if (roic is not None and w is not None) else None,
            "상세추정연수": 상세, "수렴연수": 수렴, "늘림": 늘림, "성장트리거": a, "수익트리거": b,
            "트리거": bool(a and b), "경보": bool(a and b and not 늘림),
            "문턱": {"성장낙차": float(s.get("성장낙차문턱", 0.02)), "ROIC배": float(s.get("ROIC배문턱", 1.5)), "기본상세연수": int(s.get("기본상세연수", 5))}}


# ══════════════════════════════════════════════════════════════════ ⑤ ⑥ 미국 companyfacts 연간 값
def _cf(자리):
    p = os.path.join(자리 or "", "_raw", "companyfacts.json")
    if not 자리 or not os.path.exists(p):
        return None
    try:
        return json.load(io.open(p, encoding="utf-8"))
    except (OSError, ValueError):
        return None


def cf연간(cf, 태그들):
    """companyfacts 의 연간(10-K · 20-F · 40-F · 기간 350일 넘는) 값 → ({FY 기간 ID: 값(원 단위)}, 쓴 태그). 같은 기간은 늦게 낸 값."""
    if not isinstance(cf, dict):
        return {}, None
    f = (cf.get("facts") or {}).get("us-gaap") or {}
    for 태그 in 태그들:
        u = ((f.get(태그) or {}).get("units") or {})
        줄 = u.get("USD") or next((v for k, v in u.items() if len(k) == 3), None) or []
        낸, 때 = {}, {}
        for x in 줄:
            try:
                a = datetime.date.fromisoformat(x["start"])
                b = datetime.date.fromisoformat(x["end"])
            except (KeyError, ValueError, TypeError):
                continue
            if (b - a).days < 350 or (x.get("form") or "") not in ("10-K", "10-K/A", "20-F", "40-F"):
                continue
            id_ = "FY%dA" % (b - datetime.timedelta(days=7)).year
            if id_ not in 때 or (x.get("filed") or "") >= 때[id_]:
                낸[id_], 때[id_] = _n(x.get("val")), x.get("filed") or ""
        if 낸:
            return 낸, 태그
    return {}, None


def 주식보상(가정, R, 자리, 설=None):
    s = ((설 or 설정()).get("주식보상") or {})
    문 = float(s.get("비율문턱", 0.02))
    e = float(s.get("규모탄력", 0.5))
    배 = float(((가정.get("메타") or {}).get("환산배율")) or 1)
    원 = 가정.get("원천") or {}
    매출 = 원.get("62") or {}
    보상 = {k: _n(v) for k, v in (원.get("546") or {}).items() if _FY(k) and _n(v) is not None}
    출처 = "원천 546(주식보상비용)"
    if not 보상:
        cfv, 태그 = cf연간(_cf(자리), ("ShareBasedCompensation", "AllocatedShareBasedCompensationExpense"))
        보상 = {k: v / 배 for k, v in cfv.items() if v is not None}
        출처 = "companyfacts us-gaap:%s" % 태그 if 태그 else None
    해 = sorted(k for k in 보상 if _n(매출.get(k)))
    if not 해:
        return {"해당": False, "까닭": "주식보상비용 실적이 없다(원천 546 · companyfacts)", "비율문턱": 문}
    끝 = 해[-1]
    s0 = 보상[끝] / _n(매출[끝])
    관 = ((가정.get("관측") or {}).get("주식보상")) if isinstance((가정.get("관측") or {}).get("주식보상"), dict) else None
    낸 = {"해당": s0 >= 문, "해": 끝, "비율": s0, "비율들": [{"해": k, "비율": 보상[k] / _n(매출[k])} for k in 해[-3:]],
         "출처": 출처, "비율문턱": 문, "규모탄력": e, "두배비": 2 ** (e - 1), "선언": 관, "근거": s.get("_근거")}
    낸["경보"] = bool(s0 >= 문 and not (관 and (관.get("영구비율") is not None or 관.get("경로")) and (관.get("근거") or 관.get("출처"))))
    if s0 < 문:
        return 낸
    # 대안 판 — 비율 = s0 × (연환산 매출 ÷ 마지막 실적 매출)^(e − 1)
    축 = _축(가정)
    d = R["2.DCF"]
    M0 = _n(매출[끝])
    계수 = 주당계수(가정, R)
    Δ현가, 열줄 = 0.0, []
    for i in 축.예측:
        c = 축.ID[i]
        년 = 축.열[i].년 or 1.0
        rev = _n((d.get("11") or {}).get(c))
        if not rev:
            continue
        st = s0 * ((rev / 년) / M0) ** (e - 1) if M0 else s0
        ebit, nop = _n((d.get("15") or {}).get(c)), _n((d.get("19") or {}).get(c))
        세후 = (nop / ebit) if (ebit and nop is not None and ebit > 0) else (1 - (_n(((R.get("WACC") or {}).get("예측기간") or {}).get("한계세율")) or 0))
        f23, f36 = _n((d.get("23") or {}).get(c)), _n((d.get("36") or {}).get(c))
        할 = (f36 / f23) if (f23 and f36 is not None) else _n((d.get("35") or {}).get(c))
        Δ = (s0 - st) * rev * 세후 * (할 or 0)
        Δ현가 += Δ
        열줄.append({"열": c, "비율": st})
    TV = 축.ID[축.영구]
    revT = _n((d.get("11") or {}).get(TV)) or _n(d.get("41"))
    sT = s0 * (revT / M0) ** (e - 1) if (revT and M0) else s0
    낸["영구비율"] = sT
    낸["열비율"] = 열줄
    try:
        R2 = _계산(_손잡이판(가정, s0 - sT), "기준")
        Δ영 = (_주당(R2) or 0) - (_주당(R) or 0)
    except Exception as ex:                                   # noqa: BLE001
        낸["까닭"] = "영구 판 셈 실패 — %s" % ex
        return 낸
    Δ예 = Δ현가 * 계수 if 계수 else None
    낸["예측기간몫"] = Δ예
    낸["영구몫"] = Δ영
    낸["판주당"] = (_주당(R) or 0) + (Δ예 or 0) + Δ영 if Δ예 is not None else None
    낸["판변화"] = _변화(낸["판주당"], _주당(R))
    낸["셈"] = "예측 열은 엔진 할인계수로 선형 셈(NOPLAT ÷ 영업이익 비율 · FCFF 현가 ÷ FCFF) · 영구기간은 엔진 손잡이(영구이익률가감 = 마지막 실적 비율 − 영구 비율)"
    return 낸


def 연구개발(가정, R, 자리, 설=None):
    s = ((설 or 설정()).get("연구개발") or {})
    문 = float(s.get("비율문턱", 0.05))
    if not 미국회계(가정, 자리):
        return {"해당": False, "까닭": "연구개발비를 이미 일부 자산화하는 회계(국내 K-IFRS 따위)이거나 미국 회계가 아니다 — 다시 자본화하면 이중이다"}
    if (((가정.get("구조") or {}).get("투자") or {}).get("연구개발자본화")) == "예":
        요 = (R.get("요약") or {}).get("연구개발자본화") or {}
        return {"해당": True, "엔진켬": True, "엔진": 요, "RONIC": _n((R.get("요약") or {}).get("영구ROIC")),
                "기준": "자본화 기준(엔진이 조정 값을 쓴다 — RONIC 도 조정 투하자본에 대해 정한다)"}
    배 = float(((가정.get("메타") or {}).get("환산배율")) or 1)
    원 = 가정.get("원천") or {}
    매출 = 원.get("62") or {}
    연 = {k: _n(v) for k, v in (원.get("536") or {}).items() if _FY(k) and _n(v) is not None}
    출처 = "원천 536(연구개발비)"
    cfv, 태그 = cf연간(_cf(자리), ("ResearchAndDevelopmentExpense", "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost"))
    for k, v in cfv.items():                                  # 원천에 없는 옛 해는 companyfacts 로 채운다
        if k not in 연 and v is not None:
            연[k] = v / 배
            출처 = "원천 536 · companyfacts us-gaap:%s" % 태그 if 원.get("536") else "companyfacts us-gaap:%s" % 태그
    해 = sorted(k for k in 연 if _n(매출.get(k)))
    if not 해:
        return {"해당": False, "까닭": "연구개발비 실적이 없다(원천 536 · companyfacts)"}
    끝 = 해[-1]
    비 = 연[끝] / _n(매출[끝])
    if 비 < 문:
        return {"해당": False, "까닭": "연구개발비 ÷ 매출 %.1f%% 가 문턱 %.0f%% 아래" % (비 * 100, 문 * 100), "비율": 비}
    v805 = (가정.get("시점가정") or {}).get("805")
    if isinstance(v805, dict):
        v805 = v805.get("공통", v805.get("기준"))
    L = int(_n(v805) or s.get("상각연수", 5))
    끝해 = int(끝[2:6])
    줄 = [연.get("FY%dA" % (끝해 - k)) for k in range(0, L + 1)]
    if any(v is None for v in 줄[:L]):
        return {"해당": True, "까닭": "상각연수 %d해의 연구개발비가 다 있지 않다(있는 해: %s) — 재지 않는다" % (L, " · ".join(sorted(연))),
                "비율": 비, "상각연수": L}
    자산 = sum(줄[k] * (L - k) / L for k in range(L))
    상각 = sum((줄[k] or 0) / L for k in range(1, L + 1))
    d = R["2.DCF"]
    ebit = _n((d.get("15") or {}).get(끝))
    WC, 유, 무 = (_n((R["9.WC"].get("14") or {}).get(끝)), _n((R["8.CapEx"].get("21") or {}).get(끝)), _n((R["8.CapEx"].get("28") or {}).get(끝)))
    IC = (WC or 0) + (유 or 0) + (무 or 0)
    t = _n(((R.get("WACC") or {}).get("예측기간") or {}).get("한계세율")) or 0.0
    nop = ebit * (1 - t) if ebit is not None else None
    조nop = (nop + 연[끝] - 상각) if nop is not None else None
    조IC = IC + 자산
    return {"해당": True, "해": 끝, "비율": 비, "상각연수": L, "출처": 출처, "연구개발비": 연[끝], "연구자산": 자산, "상각": 상각,
            "보고영업이익": ebit, "조정영업이익": (ebit + 연[끝] - 상각) if ebit is not None else None,
            "보고투하자본": IC, "조정투하자본": 조IC, "보고ROIC": (nop / IC) if (nop is not None and IC > 0) else None,
            "조정ROIC": (조nop / 조IC) if (조nop is not None and 조IC > 0) else None,
            "조정NOPLAT증가": 연[끝] - 상각, "조정재투자증가": 연[끝] - 상각, "FCFF변화": 0.0,
            "RONIC": _n((R.get("요약") or {}).get("영구ROIC")), "기준": "보고 기준(연구개발비 비용 처리 — 투하자본에 연구자산이 없다)",
            "세": "보고 기준 세금 그대로(비용 처리의 세효과를 남긴다) · NOPLAT = 영업이익 × (1 − 한계세율)", "근거": s.get("_근거")}


# ══════════════════════════════════════════════════════════════════ ⑦ 영구 RONIC 과 투하자본 정의의 정합(1.1.6 — 값 불변)
def _열값(가정, 번, 열, 시나리오="기준"):
    벌 = ((가정.get("가정") or {}).get(번)) or {}
    한 = 벌.get(시나리오) if isinstance(벌.get(시나리오), dict) else (벌.get("공통") if isinstance(벌.get("공통"), dict) else {})
    return _n((한 or {}).get(열))


def RONIC정합(가정, R, 설=None, 연구=None):
    """영구 RONIC 이 예측기간의 매출자본비율 · 기존 자본 수익률과 같은 투하자본 정의를 쓰는가(1.1.6). **RONIC 을 바꾸지 않는다** — 대조 표 · 경보 ·
    판단대장 「RONIC 기준」 줄 요건만. 함축 증분 수익률 = 매출자본비율 × 영구기간 세후 영업이익률(ΔNOPLAT ÷ Δ투하자본 = 세후 마진 × Δ매출 ÷ (Δ매출 ÷ S2C))."""
    s = ((설 or 설정()).get("RONIC정합") or {})
    차문, 배문, 경문 = float(s.get("차문턱", 0.25)), float(s.get("배문턱", 3.0)), float(s.get("경량문턱", 5.0))
    축 = _축(가정)
    끝, TV = 축.ID[축.끝예측], 축.ID[축.영구]
    d = R["2.DCF"]
    요 = R.get("요약") or {}
    ronic = _n(요.get("영구ROIC"))
    매T, nopT = _n((d.get("11") or {}).get(TV)), _n((d.get("19") or {}).get(TV))
    세후 = (nopT / 매T) if (매T and nopT is not None) else None
    성장규칙 = ((((가정.get("구조") or {}).get("투자")) or {}).get("성장규칙"))
    s2c, s2c출처 = None, None
    if 성장규칙 == "매출자본비율":
        s2c = _열값(가정, "859", 끝)
        s2c출처 = "가정 859(Sales-to-Capital · 마지막 예측 열)" if s2c is not None else None
    if s2c is None:
        앞i = 축.끝예측 - 1 if (축.끝예측 - 1) in 축.예측 else None
        매끝 = _n((d.get("11") or {}).get(끝))
        매앞 = _n((d.get("11") or {}).get(축.ID[앞i])) if 앞i is not None else None
        년끝 = 축.열[축.끝예측].년 or 1.0
        년앞 = (축.열[앞i].년 or 1.0) if 앞i is not None else None
        재 = None
        if all(_n((d.get(k) or {}).get(끝)) is not None for k in ("21", "20", "22")):
            재 = _n(d["21"][끝]) - _n(d["20"][끝]) + _n(d["22"][끝])
        if 매끝 and 매앞 and 재 and 재 > 0 and (매끝 / 년끝 - 매앞 / 년앞) > 0:
            s2c, s2c출처 = (매끝 / 년끝 - 매앞 / 년앞) / (재 / 년끝), "마지막 예측 해 매출 증가 ÷ 재투자"
        else:
            참 = ((({x["기준"][:1]: x for x in ((R.get("부수") or {}).get("안정성장4기준") or [])}).get("④") or {}).get("참고")) or {}
            ic = _n(참.get("마지막해투하자본"))
            if 매끝 and ic and ic > 0:
                s2c, s2c출처 = (매끝 / 년끝) / ic, "마지막 예측 해 매출 ÷ 투하자본(평균 회전율)"
    함축 = (s2c * 세후) if (s2c is not None and 세후 is not None) else None
    n45, ic86 = _n(d.get("45")), _n(d.get("86"))                # 기존 자본의 수익률 — 영구기간 NOPLAT ÷ 최종 예측 연도 말 투하자본(레터 Terminal Value 절과 같은 정의)
    기존 = (n45 / ic86) if (n45 is not None and ic86 and ic86 > 0) else None
    낸 = {"RONIC": ronic, "매출자본비율": s2c, "매출자본비율출처": s2c출처, "세후영업이익률": 세후, "함축증분수익률": 함축,
         "기존자본수익률": 기존, "끝열": 끝, "문턱": {"차": 차문, "배": 배문, "경량": 경문}, "근거": s.get("_근거")}
    낸["차"] = (함축 - ronic) if (함축 is not None and ronic is not None) else None
    낸["기존배"] = (기존 / ronic) if (기존 is not None and ronic) else None
    낸["함축배"] = (함축 / ronic) if (함축 is not None and ronic) else None
    낸["자산경량"] = bool(s2c is not None and s2c >= 경문)
    r = 연구 or {}
    if 낸["자산경량"]:
        if _n(r.get("조정ROIC")) is not None:
            낸["조정ROIC"] = _n(r["조정ROIC"])
            낸["조정ROIC해"] = r.get("해")
            낸["조정ROIC배"] = (낸["조정ROIC"] / ronic) if ronic else None
        else:
            낸["조정ROIC까닭"] = r.get("까닭") or "연구개발 자본화 측정 표가 서지 않았다(미국 회계 · 연구개발비 ÷ 매출 문턱 이상 회사만)"
    밖차 = 낸["차"] is not None and abs(낸["차"]) > 차문
    밖배 = 낸["기존배"] is not None and 낸["기존배"] > 배문
    낸["경보"] = bool(밖차 or 밖배)
    까 = []
    if 밖차:
        까.append("매출자본비율 × 세후 영업이익률이 함축하는 증분 수익률 %s 가 RONIC %s 와 %s 갈린다(문턱 ±%.0f%%p)"
                 % (_p0(함축), _p0(ronic), _pp(낸["차"]), 100 * 차문))
    if 밖배:
        까.append("기존 자본 수익률 %s 가 RONIC 의 %.1f배(문턱 %.1f배)" % (_p0(기존), 낸["기존배"], 배문))
    낸["판정"] = ("정의 대조 요건 — " + " · ".join(까)) if 까 else "정합 — 함축 증분 수익률 · 기존 자본 수익률이 RONIC 과 문턱 안"
    return 낸


# ══════════════════════════════════════════════════════════════════ 한데 모아
def 셈(가정, 자리, R=None, 설=None):
    설 = 설 or 설정()
    R = R or _계산(가정, "기준")
    낸 = {"형식": 형식, "만든날": datetime.date.today().isoformat(), "평가기준일": (가정.get("메타") or {}).get("평가기준일"),
         "값을바꿈": False, "기준주당": _주당(R), "신호": []}
    for 이름, f in (("영구베타", lambda: 영구베타(가정, R, 자리, 설)), ("재투자방향", lambda: 재투자방향(가정, R, 설)),
                   ("적자부문", lambda: 적자부문(가정, R, 자리, 설)), ("연장감사", lambda: 연장감사(가정, R, 설)),
                   ("주식보상", lambda: 주식보상(가정, R, 자리, 설)), ("연구개발", lambda: 연구개발(가정, R, 자리, 설)),
                   ("RONIC정합", lambda: RONIC정합(가정, R, 설, 낸.get("연구개발")))):
        try:
            낸[이름] = f()
        except Exception as e:                               # noqa: BLE001 — 한 자리의 셈 실패가 나머지를 막지 않는다
            낸[이름] = {"까닭": "셈 실패 — %s: %s" % (type(e).__name__, e)}
    방 = 낸["재투자방향"]
    if 방.get("요건"):
        낸["재투자방향"]["판단대장"] = [{"파일": a, "줄": b, "글": c} for a, b, c in 판단대장줄(자리)]
    if (낸.get("RONIC정합") or {}).get("경보"):
        낸["RONIC정합"]["판단대장"] = [{"파일": a, "줄": b, "글": c} for a, b, c in 판단대장줄(자리, "RONIC 기준")]
        낸["신호"].append({"출처": "안정성장", "종류": "RONIC 정의 정합", "대상": "기준", "값": 낸["RONIC정합"].get("차"), "등급": "참고",
                         "글": 낸["RONIC정합"].get("판정")})
    v = 낸["영구베타"]
    if v.get("경보"):
        낸["신호"].append({"출처": "안정성장", "종류": "영구 자본비용 수렴", "대상": "기준", "값": v.get("기본판변화"), "등급": "참고",     # 경보는 자체검사 54 가 낸다
                         "글": "영구기간 자본비용이 기본 규칙(%s)과 다르다 — 그 판의 주당가치는 채택 대비 %s" % (판이름[v["기본판"]], _p(v.get("기본판변화")))})
    if 방.get("요건"):
        낸["신호"].append({"출처": "안정성장", "종류": "재투자 방향", "대상": "기준", "값": 방.get("재투자율차"), "등급": "참고", "글": 방.get("판정")})
    for h in 낸["적자부문"].get("부문") or []:
        if h.get("굳음"):
            낸["신호"].append({"출처": "안정성장", "종류": "적자 부문 영구화", "대상": "기준", "값": h.get("손실비"), "등급": "참고",
                             "글": "보고부문 %s 의 영업손실(연결 매출의 %s) 가운데 %s 가 연결 마진 경로에 묶여 영구기간까지 간다 — 손실이 멈춘 판의 주당가치는 %s"
                                   % (h.get("이름"), _p0(h.get("손실비")), _p0(h.get("묶인몫")), _p(h.get("포기판변화")))})
    if 낸["연장감사"].get("경보"):
        x = 낸["연장감사"]
        낸["신호"].append({"출처": "안정성장", "종류": "연장 트리거", "대상": "기준", "값": x.get("성장낙차"), "등급": "참고",
                         "글": "마지막 예측 해 성장 낙차 %s · 평균 ROIC ÷ WACC %.2f배인데 예측기간이 기본 길이다" % (_pp(x.get("성장낙차")), x.get("ROIC배") or 0)})
    if 낸["주식보상"].get("경보"):
        x = 낸["주식보상"]
        낸["신호"].append({"출처": "안정성장", "종류": "주식보상 비율 고정", "대상": "기준", "값": x.get("비율"), "등급": "참고",
                         "글": "주식보상이 매출의 %s 이고 비율 경로가 선언되지 않았다 — 규모에 따라 줄어드는 판의 주당가치는 %s" % (_p0(x.get("비율")), _p(x.get("판변화")))})
    return 낸


def _p(x):
    return ("%+.1f%%" % (100 * x)) if _n(x) is not None else "—"


def _p0(x):
    return ("%.1f%%" % (100 * x)) if _n(x) is not None else "—"


def _pp(x):
    return ("%+.2f%%p" % (100 * x)) if _n(x) is not None else "—"


def _수글(x):
    return ("%.6g" % x) if _n(x) is not None else "—"


def _가정해시(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def 쓰기(낸, 가정경로, 낼=None):
    p = 낼 or os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw", 산출이름)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(낸, f, ensure_ascii=False, indent=1)
    return p


def 화면(낸):
    줄 = ["안정성장 점검 — 기준 주당가치 %s" % _수글(낸.get("기준주당"))]
    v = 낸.get("영구베타") or {}
    if v.get("판"):
        업 = v.get("업종") or {}
        줄.append("  ① 영구 베타 — 업종 %s %s(βU %s · D/E %s) · 채택 「%s」 · 기본판 「%s」 · 방향 %s%s" % (
            업.get("줄") or "없음", 업.get("지역") or "", _수글(업.get("βU현금보정")), _수글(업.get("DE")), 판이름.get(v.get("채택"), v.get("채택")),
            판이름.get(v.get("기본판")), v.get("방향") or "—", " · ! 경보" if v.get("경보") else ""))
        for x in v["판"]:
            영 = x.get("영구") or {}
            줄.append("      %-22s βU %s · D/E %s · βL %s · 영구 WACC %s → 주당 %s(채택 대비 %s)%s" % (
                x["이름"], _수글((x.get("칸") or {}).get("베타u")), _수글(영.get("DE")), _수글(영.get("베타l")), _p0(영.get("WACC")),
                _수글(x.get("주당")), _p(x.get("채택대비")), (" — " + x["까닭"]) if x.get("까닭") else ""))
    elif v.get("까닭"):
        줄.append("  ① 영구 베타 — %s" % v["까닭"])
    방 = 낸.get("재투자방향") or {}
    줄.append("  ② 재투자 방향 — %s · 매출 %s · NOPLAT %s · 재투자율 %s · 함축 증분 ROIC %s · RONIC %s · g ÷ RONIC %s" % (
        방.get("판정") or 방.get("까닭"), _p0(방.get("매출성장")), _p0(방.get("NOPLAT성장")), _p0(방.get("재투자율")), _p0(방.get("함축증분ROIC")),
        _p0(방.get("RONIC")), _p0(방.get("영구재투자율"))))
    for h in 방.get("후보") or []:
        줄.append("      %s %s — %s" % ("●" if h["지표가가리킴"] else "○", h["말"], h["근거"]))
    for h in (낸.get("적자부문") or {}).get("부문") or []:
        줄.append("  ③ 적자 부문 — %s %s 영업손익 %s(연결 매출의 %s) · 그 해 연결 마진 %s · 걷은 마진 %s · 영구 마진 %s · 묶인 몫 %s · 포기 판 %s(%s)%s" % (
            h["이름"], h["해"], _수글(h["영업손익"]), _p0(h.get("손실비")), _p0(h.get("연결마진")), _p0(h.get("뺀마진")), _p0(h.get("영구마진")),
            _p0(h.get("묶인몫")), _수글(h.get("포기판주당")), _p(h.get("포기판변화")), " · 굳음" if h.get("굳음") else ""))
    x = 낸.get("연장감사") or {}
    줄.append("  ④ 연장 감사 — 성장 낙차 %s · 평균 ROIC ÷ WACC %s · 상세 %s년 · 수렴 %s년%s" % (
        _pp(x.get("성장낙차")), ("%.2f배" % x["ROIC배"]) if _n(x.get("ROIC배")) is not None else "—", x.get("상세추정연수"), x.get("수렴연수"),
        " · ! 트리거가 서는데 늘리지 않았다" if x.get("경보") else (" · 트리거" if x.get("트리거") else "")))
    x = 낸.get("주식보상") or {}
    if x.get("비율") is not None:
        줄.append("  ⑤ 주식보상 — %s 매출의 %s(%s)%s" % (x.get("해"), _p0(x.get("비율")), x.get("출처"),
                                              (" · 줄어드는 판 %s(%s) · 영구 비율 %s" % (_수글(x.get("판주당")), _p(x.get("판변화")), _p0(x.get("영구비율"))))
                                              if x.get("판주당") is not None else ""))
    else:
        줄.append("  ⑤ 주식보상 — %s" % (x.get("까닭") or "—"))
    x = 낸.get("연구개발") or {}
    if x.get("조정ROIC") is not None:
        줄.append("  ⑥ 연구개발 자본화(측정) — %s 매출의 %s · 연구자산 %s · ROIC 보고 %s → 조정 %s · RONIC %s(%s)" % (
            x["해"], _p0(x["비율"]), _수글(x["연구자산"]), _p0(x.get("보고ROIC")), _p0(x.get("조정ROIC")), _p0(x.get("RONIC")), x.get("기준")))
    else:
        줄.append("  ⑥ 연구개발 — %s" % (x.get("까닭") or x.get("기준") or "—"))
    x = 낸.get("RONIC정합") or {}
    if x.get("판정"):
        줄.append("  ⑦ RONIC 정합 — %s · 매출자본비율 %s(%s) × 세후 영업이익률 %s = 함축 증분 수익률 %s · 기존 자본 수익률 %s · RONIC %s%s" % (
            x["판정"], _수글(x.get("매출자본비율")), x.get("매출자본비율출처") or "—", _p0(x.get("세후영업이익률")), _p0(x.get("함축증분수익률")),
            _p0(x.get("기존자본수익률")), _p0(x.get("RONIC")),
            (" · 자산 경량 — 조정 ROIC %s" % _p0(x.get("조정ROIC"))) if x.get("조정ROIC") is not None
            else ((" · 자산 경량 — %s" % x["조정ROIC까닭"]) if x.get("조정ROIC까닭") else "")))
    elif x.get("까닭"):
        줄.append("  ⑦ RONIC 정합 — %s" % x["까닭"])
    return "\n".join(줄)


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                        # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description="안정 성장 점검 — 영구 베타 수렴 · 재투자 방향 · 적자 부문 · 연장 트리거 · 주식보상 · 연구개발(값을 바꾸지 않는다)")
    ap.add_argument("가정")
    ap.add_argument("--낼")
    ap.add_argument("--자리", help="회차 폴더(기본: 가정 곁)")
    ap.add_argument("--쓰기", choices=판차례, help="영구기간 자본비용을 그 판으로 가정에 적는다")
    a = ap.parse_args(argv)
    자리 = a.자리 or os.path.dirname(os.path.abspath(a.가정))
    try:
        가정 = json.load(io.open(a.가정, encoding="utf-8"))
        if a.쓰기:
            R = _계산(가정, "기준")
            영 = 영구베타(가정, R, 자리)
            새, 글 = 쓰기판(가정, 영, a.쓰기)
            _계산(새, "기준")                                   # 엔진이 받는 꼴인지 먼저 본다
            with io.open(a.가정, "w", encoding="utf-8", newline="\n") as f:
                json.dump(새, f, ensure_ascii=False, indent=1)
            print("영구기간 자본비용 — %s → %s" % (글, a.가정))
        낸 = 셈(json.load(io.open(a.가정, encoding="utf-8")), 자리)
    except (OSError, ValueError, KeyError) as e:
        print("입력오류 — %s" % e)
        return 입력오류
    낸["가정해시"] = _가정해시(a.가정)
    p = 쓰기(낸, a.가정, a.낼)
    print(화면(낸))
    print("→ %s" % p)
    return 통과


if __name__ == "__main__":
    sys.exit(main())

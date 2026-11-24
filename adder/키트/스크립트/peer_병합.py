# -*- coding: utf-8 -*-
"""두 시장 유사기업 βU 병합 — 국내 조립(`peer_조립.py`)과 해외 조립(`peer_βU_us.py`)의 βU 산출을 한 표로 (2026-10-17 S7-02).

왜 있는가
    국내 대상회사의 위험 동종이 국내 상장사로만 모였다. 반도체 · 플랫폼 · 게임 · 바이오 · 자동차처럼 국내 동종이 적거나 규모가 안 맞는
    업종에서 키트 기본 경로가 산업 βU 의 4분의 1~3분의 2 를 냈다(실측 NAVER 0.29 · 펄어비스 0.85 · BGF리테일 0.32 — 다모다란
    같은 매핑 줄 1.2~1.5 · 0.7~0.9). 참조 모형(하이닉스 βU 1.4869)은 키트 밖 수작업 스크립트로 해외 동종을 섞어 냈다 —
    **그 방법을 키트 경로로 재현할 수 없었다.** 이 도구가 그 자리다.

하는 일
    · 산출 둘(이상)을 읽어 회사 행을 합친다 — 회사마다 **그 시장의 사양**(회귀 지수 · 통화 · 소재국 세율 · 창 평균 D/E · 현금 ·
      부채베타 · 본값 제외 사유)을 조립기가 낸 그대로 싣는다. 여기서 다시 벗기지 않는다(βU 는 무차입 · 통화 무관 비율이다)
    · 같은 회사가 두 산출에 다 있으면(국내 상장사의 미국 ADR 등) 앞 산출(국내)을 쓰고 뒤를 적는다
    · `βU본값.py` 규칙으로 본값 · 포함 · 3년 창 대안 · 95% 구간을 내고, 대상회사 매핑 줄의 산업 βU 와 대조한다(±30% 밖 ★)
    · 산출 `_raw/peers/βU_병합_{표본}.json` — 꼴은 조립기 산출과 같다(`본값.핵심.본값.(b)개별중앙값_기본` 이 3단계 기본값)

핵심 표본 구분
    각 산출의 행에 `핵심`(C1 의 구분)이 있으면 그것을 쓴다. 해외 경로 ⑤ 로 연 산출은 C1 이 같은 슬롯 순서로 핵심 · 예비를 정한
    `핵심표본.json` 을 그 사슬에 넘겼다면 그대로 오고, 아니면 `--입력 경로:전부` 로 그 산출의 회사 전부를 핵심으로 둔다(사람이 지시한 것 —
    근거에 적는다). 시장마다 지수가 다르다는 사실(국내 KOSPI · 미국 S&P 500)은 표에 적는다.

세 겹 · 핵심 다시 가르기 (2026-10-25 FX3-b — C1 다시 돌리기 2 · 3 · 4조 실측)
    · `--핵심표본` 을 주면 입력 행마다 **새 핵심표본으로 핵심 · 예비 · 슬롯을 다시 가른다** — 해외 산출이 옛 핵심표본으로 지어져
      핵심 0곳이거나(`:전부` 로 돌리면 C1 예비까지 핵심이 됐다) 슬롯이 비던 결함. 핵심표본에 없는 행은 넓은 표본(`:전부` 면 그대로 핵심)
    · `--기본값규칙 세겹` — 국내 조립기와 같은 세 겹(① 병합 표본의 부문 가중 · ② 병합 본값 중앙값 · ③ 대상 자체 — 국내 입력의
      `본값.대상자체` 와 그 판정)을 병합 표본으로 낸다. 제한 둘(대상 자체 제외 · 비중 큰 약한 슬롯)은 `βU본값` 이 정본
    · 시장이 섞인 표본이면 부문 가중의 「소형」 잣대(대상 시가총액 대비)는 쓰지 않는다 — 통화가 다르다

사용
    python 스크립트/peer_병합.py --입력 _raw/peers/βU_핵심예비.json --입력 _raw/peers/βU_해외.json:전부 \\
           --대상 KOSE:A000660 --기준일 2026-06-30 --표본 병합
    python 스크립트/peer_병합.py --입력 βU_핵심예비.json --입력 βU_해외.json --핵심표본 핵심표본.json --기본값규칙 세겹 ...
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import βU본값 as 본  # noqa: E402

# 2026-10-25 FX4-P — DCF_RUN_ROOT(사슬 `--폴더` 가 넘긴다)면 그 회차에 쓴다 — 본체 경로로 돌려도 본체 _raw 에 쌓지 않게
ROOT = os.environ.get("DCF_RUN_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEER = os.path.join(ROOT, "_raw", "peers")


def 읽(p):
    return json.load(io.open(p, encoding="utf-8"))


def 시장추정(산출, 경로):
    """산출의 시장 · 지수 표시 — 국내 조립 산출은 머리에 창 · 표본이 있고 행에 회귀지수가 있다."""
    행 = (산출.get("표") or [{}])[0] if 산출.get("표") else {}
    if 행.get("회귀지수") in ("KOSPI", "KOSDAQ") or "종목코드" in 행:
        return "국내", "KOSPI(넓은)" if (산출.get("본값") or {}).get("지수", "").startswith("넓은") else (행.get("회귀지수") or "KOSPI/KOSDAQ")
    return "미국", "S&P 500"


def ERP캐시(시장, 기준일):
    """부채베타 ERP — 시장데이터 캐시(국내 = 성숙시장 위험프리미엄 + CRP · 미국 = 성숙시장 위험프리미엄). 없으면 (None, 까닭)."""
    if not 기준일:
        return None, "기준일 없음"
    try:
        import market_data as _md
        d, 곳 = _md.캐시읽기("KR" if 시장 == "국내" else "US", 기준일)
    except Exception as e:                                  # noqa: BLE001
        return None, "시장데이터 캐시 읽기 실패(%s)" % type(e).__name__
    if not d:
        return None, "시장데이터 캐시 없음"
    성 = (d.get("성숙시장 위험프리미엄") or {}).get("값")
    국 = (d.get("국가위험프리미엄 (CRP)") or {}).get("값") or 0.0
    v = (성 + 국) if 성 is not None else (d.get("시장위험프리미엄 (ERP)") or {}).get("값")
    return v, "시장데이터 캐시 %s(%s)" % ("KR" if 시장 == "국내" else "US", 곳)


def 병합(입력들, 대상티커=None, 기준일=None, ERP=None, 산업줄=None, 핵심표본=None, 기본값규칙="축소"):
    """[(경로, 전부핵심)] → 결과 dict. 핵심표본 = C1 `핵심표본.json` 경로(주면 핵심 · 슬롯을 다시 가른다) · 기본값규칙 = 축소(1.1.3 기본) / 본값 / 세겹."""
    구분, 슬롯비중, 재구분 = {}, None, 0
    if 핵심표본:
        import 핵심표본읽기 as _hr
        _h = 읽(핵심표본)
        구분 = _hr.구분표(_h)
        슬롯비중 = _h.get("슬롯들") if isinstance(_h, dict) else None
    행들, 본것, 출처, 대상자체, 대상판정 = [], {}, [], None, None
    for 경로, 전부 in 입력들:
        d = 읽(경로)
        시장, 지수 = 시장추정(d, 경로)
        출처.append({"파일": os.path.basename(경로), "시장": 시장, "지수": 지수, "세율": d.get("세율") or (d.get("머리") or {}).get("세율"),
                   "전부핵심": 전부, "회사수": len(d.get("표") or [])})
        _본 = d.get("본값") or {}
        if 대상자체 is None and _본.get("대상자체"):          # 국내 조립기가 낸 대상 자체 βU(점검값)와 판정
            대상자체, 대상판정 = _본["대상자체"], _본.get("대상자체판정")
        for z in d.get("표") or []:
            키 = (z.get("종목코드") or z.get("티커") or "").upper()
            if 키 in 본것:
                본것[키]["중복"] = "%s 에도 있음 — 앞 산출을 씀" % os.path.basename(경로)
                continue
            z = dict(z)
            z.update({"시장": 시장, "지수": 지수, "산출": os.path.basename(경로)})
            if 구분:                                       # 2026-10-25 FX3-b — 새 핵심표본으로 다시 가른다
                k6 = 키.zfill(6) if 키.isdigit() else 키
                v = 구분.get(k6) or 구분.get(키)
                옛 = (z.get("구분"), z.get("핵심"))
                if v:
                    z["구분"], z["핵심"] = v["구분"], v["구분"] == "핵심"
                    z["슬롯"] = v.get("슬롯") or z.get("슬롯") or ""
                else:
                    z["구분"], z["핵심"] = "넓은표본", False
                재구분 += int(옛 != (z.get("구분"), z.get("핵심")))
            if 전부:
                z["핵심"] = True
            if "βU_본" not in z:
                본.본값행(z, ERP if ERP is not None else ERP캐시(시장, 기준일)[0])   # 옛 산출(본값 칸이 없는 판) — 이 자리에서 같은 규칙으로 붙인다
            else:
                # 2026-10-25 FX4-P — 부채베타 규칙(FX3-b) 전에 지은 산출의 D/E ≥ 2 행은 하마다로 벗겨져 있다(C2 다시 셈 4-10 — 미국 동종 D/E 2.39).
                # 병합에서 같은 규칙으로 다시 판정한다 — 스프레드가 없으면 βU본값 ⑧ 로 본값 밖(포함 값에만)
                _de = z.get("DE_본") if z.get("DE_본") is not None else z.get("DE")
                if isinstance(_de, (int, float)) and _de >= 본.문턱["부채베타DE"] and z.get("부채베타") is None:
                    _e, _e근 = (ERP, "--ERP") if ERP is not None else ERP캐시(시장, 기준일)
                    본.본값행(z, _e)
                    z["병합다시판정"] = "옛 산출 — D/E %.2f ≥ %.1f 부채베타 없이 벗겨진 행을 병합에서 다시 판정(ERP %s · %s)" % (
                        _de, 본.문턱["부채베타DE"], ("%.4f" % _e) if _e is not None else "없음", _e근)
            본것[키] = z
            행들.append(z)
    핵 = [z for z in 행들 if z.get("핵심")] or 행들
    # 2026-10-24 W16 — 한 입력의 행이 하나도 핵심으로 안 들어오면(그 시장 조립기가 C1 구분을 못 읽음) 병합 본값이 다른 시장만으로 서던 결함(유니버스 조사 물결 실측 —
    # 해외 본값 n=4 인데 병합은 국내 n=1). 입력마다 핵심 수를 적고 0 이면 경보 — `--입력 파일:전부` 로 그 파일을 전부 핵심으로 넣을 수 있다
    빈입력 = [o["파일"] for o in 출처 if o["회사수"] and not any(z.get("핵심") and z["산출"] == o["파일"] for z in 행들)]
    for o in 출처:
        o["핵심수"] = sum(1 for z in 핵 if z["산출"] == o["파일"])
    요 = 본.요약(핵, None, ERP)
    if 빈입력 and len(출처) > 1:
        요["병합경보"] = ("입력 %s 에서 핵심으로 들어온 회사가 0곳 — 병합 본값이 다른 시장만으로 섰다. 그 조립기의 핵심표본 구분을 확인하거나 "
                     "`--입력 <파일>:전부` 로 다시 병합한다" % ", ".join(빈입력))
        print("  ※ " + 요["병합경보"])
    요["시장별"] = {}
    for 시장 in sorted({z["시장"] for z in 핵}):
        한 = [z for z in 핵 if z["시장"] == 시장 and not z.get("본값제외")]
        요["시장별"][시장] = 본.세방식([z for z in 한 if z.get("βU_본") is not None], None, "βU_본", "현금비중_본")
    산업 = None
    if not 대상티커:                                         # 1.1.4(R11) — 대상 없이 병합하면 산업 βU 대조가 없어 축소가 회귀 그대로(w = 1)로 선다
        print("  ※ --대상 이 없다 — 산업 βU 대조 없이 병합한다. 정밀도 가중 축소가 업종 βU 없이(w = 1) 선다 — --대상 <종목코드 · 티커> 를 준다")
    if 대상티커:
        try:
            import 산업베타 as _ib
            티커들 = _ib.국내티커(대상티커) if str(대상티커).isdigit() else _ib.티커정규(대상티커)   # 2026-10-24 W16 — A 접두 · KRX: 표기 정규화
            # 2026-10-24 W18 — 핵심 동종의 매핑 줄로도 견준다(분류경보 · 대안줄) · `--산업줄` 이면 사람이 정한 줄
            _동 = [(_ib.국내티커(z["종목코드"]) if z.get("종목코드") else _ib.거래소티커후보(z.get("티커"))) for z in 핵
                  if z.get("종목코드") or z.get("티커")]
            산업 = _ib.대조값(티커들, (요.get("본값") or {}).get("(b)개별중앙값_기본"), 기준일, 산업줄, None, None if 산업줄 else _동)
        except SystemExit as e:
            산업 = {"문장": "산업 βU 대조 불가 — %s" % e, "★": False}
        except Exception as e:                              # noqa: BLE001
            산업 = {"문장": "산업 βU 대조 불가 — %s" % type(e).__name__, "★": False}
    지수들 = sorted({z["지수"] for z in 핵})
    # 2026-10-25 FX3-b — 세 겹(국내 조립기와 같은 규칙 · 병합 표본) — 시장이 섞이면 「소형」 잣대(통화가 다른 시가총액 비교)는 쓰지 않는다
    한시장 = len({z["시장"] for z in 핵}) == 1
    부문 = 본.부문가중(핵, 슬롯비중, 대상시총=(대상자체 or {}).get("시가총액") if 한시장 else None) if 슬롯비중 else None
    if 대상자체 and 대상판정 is None:
        대상판정 = 본.대상자체판정(대상자체, 대상자체.get("신호"))
    _본b = 요.get("본값") or {}
    겹 = 본.세겹(부문["값"] if 부문 else None,
                _본b.get("(b)개별중앙값_기본") if _본b.get("표본수", 0) >= 본.기본값최소표본 else None,   # 최소 표본(셋) — 국내 조립기와 같다
                (대상자체 or {}).get("βU_본"), 부문정보=부문, 대상판정=대상판정)
    if 기본값규칙 == "세겹":
        옛 = 요.get("기본값")
        요["기본값_본값규칙"] = 옛
        요["기본값"] = {"값": 겹.get("제안"), "출처": "세겹(병합 표본 — %s)" % 겹.get("까닭"), "표본수": (옛 or {}).get("표본수"),
                     "★": bool(겹.get("★") or (부문 or {}).get("★") or (옛 or {}).get("★")) or 겹.get("제안") is None,
                     "★★": bool(겹.get("★★"))}
    # 2026-10-25 FX5-P — 잡음 βU 규칙(국내 조립기와 같은 규칙 · 병합 표본의 결정계수 · 병합 ② · 대상 자체 · 산업 βU)
    잡음 = 본.잡음규칙(핵, 겹, 산업)
    겹["잡음규칙"] = 잡음
    if 기본값규칙 == "세겹" and 잡음.get("적용"):
        요["기본값"] = 본.잡음기본값(요.get("기본값"), 잡음)
    축 = 본.축소규칙(핵, 겹, 산업, 대상자체, 대상판정, 요.get("구간95"))        # 1.1.3(B1) — 정밀도 가중 축소(국내 조립기와 같은 규칙)
    겹["축소규칙"] = 축
    if 기본값규칙 == "축소" and 축.get("적용"):
        요["기본값_옛규칙"] = 요.get("기본값")
        요["기본값"] = 본.축소기본값(요.get("기본값"), 축)
    return {"머리": {"입력": 출처, "기준일": 기준일, "지수혼합": len(지수들) > 1, "지수": 지수들,
                   "핵심표본": os.path.basename(핵심표본) if 핵심표본 else None, "다시가른행": 재구분,
                   "규칙": "회사마다 그 시장 조립기의 사양(지수 · 통화 · 소재국 세율 · 창 평균 D/E · 부채베타)을 그대로 쓴다 — βU 는 무차입 비율"},
            "표": 행들,
            "본값": {"핵심": 요, "산업대조": 산업, "부문가중": 부문, "세겹": 겹, "축소": 축, "대상자체": 대상자체, "대상자체판정": 대상판정,
                   "기본값규칙": 기본값규칙,
                   "쓰는법": "3단계 WACC 의 무차입 베타 기본값은 `본값.핵심.기본값.값`(출처 칸 — 본값 셋 이상이면 본값 (b), 아니면 포함 (b), 그것도 셋 미만이면 산업 βU 선택지 ★ · S7R1-N1) — 시장별 · 포함 · 3년 창 · 95% 구간 · "
                           "산업 βU 를 근거 칸과 민감도 WACC 폭에 함께 싣는다. 지수가 섞였다는 사실을 근거에 적는다"}}


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="두 시장 유사기업 βU 병합 (S7-02)")
    ap.add_argument("--입력", action="append", required=True,
                    help="βU 산출 json(경로[:전부]) — 여럿. 「:전부」 면 그 산출의 회사 전부를 핵심으로 둔다(해외 경로 ⑤ 를 사람이 지시했을 때)")
    ap.add_argument("--대상", default=None, help="대상 거래소 티커(KOSE:A000660) 또는 국내 종목코드 — 산업 βU 대조")
    ap.add_argument("--기준일", "--평가기준일", dest="기준일", default=None, help="평가기준일 T(분석일 · 시장 쪽 — 종가 · 시가총액 · 주식수 · 베타 창 끝 · 환율 · 법령 시행일) YYYY-MM-DD")
    ap.add_argument("--ERP", type=float, default=None, help="옛 산출(본값 칸 없음)을 다시 벗길 때의 부채베타 ERP")
    ap.add_argument("--표본", default="병합", help="산출 이름 꼬리 — _raw/peers/βU_병합_{표본}.json")
    ap.add_argument("--산업줄", default=None, help="산업 βU 대조 줄(다모다란 Industry Group)을 사람이 정한다 — 대상 매핑 줄이 사업과 다를 때(분류경보)")
    ap.add_argument("--핵심표본", default=None, help="C1 핵심표본.json — 주면 입력 행의 핵심 · 예비 · 슬롯을 새 표본으로 다시 가른다(2026-10-25)")
    ap.add_argument("--기본값규칙", default="축소", choices=["축소", "본값", "세겹"],
                    help="3단계 βU 기본값 — 축소(기본 · 1.1.3 정밀도 가중 축소) / 본값(옛 순서) / 세겹(① 부문 가중 · ② 병합 중앙값 · ③ 대상 자체 — 2026-10-25)")
    a = ap.parse_args()
    입력들 = []
    for x in a.입력:
        경로, _, 꼬리 = x.partition(":전부") if x.endswith(":전부") else (x, "", "")
        경로 = 경로 if os.path.isabs(경로) or os.path.exists(경로) else os.path.join(PEER, 경로)
        if not os.path.exists(경로):
            sys.exit("입력이 없습니다: %s" % 경로)
        입력들.append((경로, x.endswith(":전부")))
    hp = None
    if a.핵심표본:
        hp = a.핵심표본 if (os.path.isabs(a.핵심표본) or os.path.exists(a.핵심표본)) else os.path.join(PEER, a.핵심표본)
        if not os.path.exists(hp):
            sys.exit("핵심표본이 없습니다: %s" % hp)
    r = 병합(입력들, a.대상, a.기준일, a.ERP, a.산업줄, hp, a.기본값규칙)
    os.makedirs(PEER, exist_ok=True)
    op = os.path.join(PEER, "βU_병합_%s.json" % a.표본)
    json.dump(r, io.open(op, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    print("%-14s %-4s %-12s %7s %6s %6s %7s %7s  %s" % ("회사", "시장", "지수", "βL", "세율", "D/E", "현금", "βU본", "본값 제외"))
    for z in r["표"]:
        f = lambda v, fm="%7.3f": ("    n/a" if v is None else fm % v)
        print("%-14s %-4s %-12s %s %s %s %s %s  %s" % (
            str(z.get("티커") or z.get("회사명"))[:14], z["시장"], z["지수"][:12], f(z.get("βL")), f(z.get("세율"), "%6.3f"),
            f(z.get("DE_본"), "%6.2f"), f((z.get("현금비중_본") * 100) if z.get("현금비중_본") is not None else None, "%6.1f%%"), f(z.get("βU_본")), "; ".join(z.get("본값제외") or []) or "-"))
    print("── 병합 본값 ── " + 본.문장(r["본값"]["핵심"], r["본값"]["산업대조"]))
    for 시장, s in r["본값"]["핵심"]["시장별"].items():
        if s.get("표본수"):
            print("  %s 만: (b) %.4f (n=%d)" % (시장, s["(b)개별중앙값_기본"], s["표본수"]))
    if r["머리"]["지수혼합"]:
        print("  ※ 지수가 섞였다(%s) — 근거 칸에 적는다" % " · ".join(r["머리"]["지수"]))
    if r["본값"]["핵심"].get("경보"):
        print("  ※ " + r["본값"]["핵심"]["경보"])
    if r["머리"].get("핵심표본"):
        print("  핵심표본 %s 로 다시 가른 행 %d" % (r["머리"]["핵심표본"], r["머리"]["다시가른행"]))
    겹 = r["본값"].get("세겹") or {}
    print("  세 겹 제안 %s — %s%s" % (("%.4f" % 겹["제안"]) if 겹.get("제안") is not None else "-", 겹.get("까닭"),
                                  " [기본값으로 씀 — --기본값규칙 세겹]" if a.기본값규칙 == "세겹" else " [참고]"))
    잡 = 겹.get("잡음규칙") or {}
    if 잡.get("적용"):
        print("  잡음 βU 규칙 %.4f(폭 %.3f ~ %.3f) — %s%s" % (잡["제안"], 잡["민감도폭"][0], 잡["민감도폭"][1], 잡["까닭"],
                                                    " [기본값으로 씀]" if a.기본값규칙 == "세겹" else " [참고]"))
    elif 잡.get("까닭"):
        print("  잡음 βU 규칙 — %s" % 잡["까닭"])
    print("→ %s" % op)


if __name__ == "__main__":
    main()

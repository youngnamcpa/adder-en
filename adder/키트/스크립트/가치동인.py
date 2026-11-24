# -*- coding: utf-8 -*-
"""**가치동인 매트릭스** — 매출 동인 × 영구기간 영업이익률, 칸마다 주당가치 (다모다란 월그린 방식).

왜 만들었나 — 기준 시나리오가 음수인 회사(이차전지 4사)에서 「기준 −6.7만원」이라는
값 하나는 검증 불가능한 선언이다. 다모다란은 월그린·인텔에서 값 하나 대신 이 매트릭스를
내놓고 음수 칸을 괄호로 그대로 실었다 — 「어느 조합에서 음수이고, 현재 주가는 어느
조합을 가정하는가」로 서술을 바꾼다. 14번 민감도(WACC × g — 내 값이 얼마나 흔들리나)와
생김새가 같고 읽는 법이 정반대(시장이 무엇을 믿나)다.

무엇을 움직이나 — **적용시나리오의 가정 위에서 두 손잡이만**(엔진 `엔진/민감도.py` 의 손잡이 — 흔드는 것도 엔진이 한다):
  · 행(성장): 매출 동인 손잡이 하나를 그 값으로 둔다(방식 「값」 — 그 시나리오의 예측 열 전부. 영구기간 열은 그대로 둔다).
    기본은 증가율 경로인 첫 매출 구분의 판매량 증가율(A-030 · 038 … · 기타 A-070). 수준 경로만 있는 회사는
    `--성장축` 으로 준다 — 가정 번호(`616+626` 처럼 + 로 묶음) 또는 `민감도.손잡이` 의 이름. 그때 `--성장` 은 그 손잡이의 값이다.
  · 열(마진): 영구기간 영업이익률을 그 값으로 둔다. 영구이익기준 = 입력(이전본)이면 A-213 을 그 값으로,
    영구열이면 칸마다 그 판의 영구기간 영업이익률(결과)과의 차를 엔진 전용 가감(영구이익률가감)으로 더한다
    — 어느 쪽이든 칸의 머리 = 그 칸에서 엔진이 쓴 영구기간 영업이익률이다.
  예측기간의 원가 · 투자 경로는 손대지 않는다 — 매출 동인과 영구기간 마진만 움직이는 표다.

눈금은 감이 아니라 그 회사·산업의 과거 기간대에서 가져와 호출자가 --성장/--마진으로 준다.
종가는 13번 평가기준일 종가(H-099 — 엔진 `민감도.종가`)다. `--종가` 로 덮을 수 있다.

사용:
    python 스크립트/가치동인.py 가정_회사.json --성장 0.02,0.05,0.08 --마진 0.02,0.05,0.08,0.12
    python 스크립트/가치동인.py 가정_회사.json --성장축 616+626 --성장 0.85,0.95,1.05 --마진 0.25,0.35,0.45
"""
from __future__ import annotations

import argparse
import importlib
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dcf엔진 as E  # noqa: E402

민 = importlib.import_module("엔진.민감도")             # 손잡이 — 움직이기 · 손잡이풀기 · 종가
계 = importlib.import_module("엔진.계산")


def _수(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def 성장손잡이(가정, 축=None):
    """행 손잡이(방식 「값」). 축 = 가정 번호(+ 로 묶음) · `민감도.손잡이` 의 이름 · None(첫 증가율 경로 구분의 판매량 증가율)."""
    if 축:
        선언 = {h.get("이름"): h for h in ((가정.get("민감도") or {}).get("손잡이") or []) if isinstance(h, dict)}
        if 축 in 선언:
            h = dict(선언[축])
        else:
            번호들 = [x.strip() for x in str(축).split("+") if x.strip()]
            if not 번호들 or not all(x.isdigit() for x in 번호들):
                raise ValueError("--성장축 「%s」 — 가정 번호(616+626) 또는 민감도.손잡이 의 이름입니다" % 축)
            대상 = ["%d" % int(x) for x in 번호들]
            같은 = [n for n, d in 선언.items() if ["%s" % x for x in (d.get("대상") or [])] == 대상]   # 선언한 손잡이면 그 이름으로
            h = {"이름": "%s (A-%s)" % (같은[0], " + A-".join("%03d" % int(x) for x in 번호들)) if 같은
                 else "A-" + " + A-".join("%03d" % int(x) for x in 번호들), "대상": 대상}
    else:
        구분 = [x for x in ((가정.get("구조") or {}).get("매출구분") or [])
              if isinstance(x, dict) and (x.get("경로") or "증가율") == "증가율"]
        if not 구분:
            선언 = [h.get("이름") for h in ((가정.get("민감도") or {}).get("손잡이") or []) if isinstance(h, dict)]
            raise ValueError("증가율 경로인 매출 구분이 없습니다 — --성장축 으로 행 손잡이를 주십시오"
                             "(가정 번호 616+626 꼴 또는 민감도.손잡이 의 이름%s)" % (": " + " · ".join(선언) if 선언 else ""))
        s = 구분[0]["번호"]
        번호 = "70" if s == 6 else "%d" % (30 + 8 * (s - 1))
        이름 = 구분[0].get("이름") or ("기타" if s == 6 else "매출 구분 %d" % s)
        h = {"이름": "%s %s (A-%03d)" % (이름, "매출액 증가율" if s == 6 else "판매량 증가율", int(번호)), "대상": [번호]}
    없는 = [x for x in h["대상"] if "%s" % x not in (가정.get("가정") or {}) and "%s" % x not in (가정.get("시점가정") or {})]
    if 없는:
        raise ValueError("행 손잡이 「%s」 의 번호가 가정 파일에 없습니다: %s" % (h.get("이름"), " · ".join("%s" % x for x in 없는)))
    h["방식"] = "값"
    return h


def _예측만(원본, a, 손잡이, 시):
    """행 손잡이가 움직인 열별 가정의 영구기간 열(TV)을 원본 값으로 되돌린다 — 행은 예측기간만 움직인다(영구 쪽은 열 손잡이)."""
    for 대상 in 손잡이["대상"]:
        원벌 = (원본.get("가정") or {}).get("%s" % 대상)
        새벌 = (a.get("가정") or {}).get("%s" % 대상)
        if not (isinstance(원벌, dict) and isinstance(새벌, dict) and isinstance(새벌.get(시), dict)):
            continue
        원한 = 원벌.get(시, 원벌.get("공통"))
        if isinstance(원한, dict) and "TV" in 새벌[시]:
            새벌[시]["TV"] = 원한.get("TV")
    return a


def 한칸(원본, 시, 행손잡이, 성장, 마진, 마진손잡이=None):
    """한 칸의 주당가치 — 행 손잡이를 성장으로 두고(예측 열), 영구기간 영업이익률을 마진으로 둔다."""
    a = _예측만(원본, 민.움직이기(원본, 행손잡이, 성장, 시), 행손잡이, 시)
    hm = 마진손잡이 or 민.손잡이풀기("영구이익률", a)
    if "%s" % hm["대상"][0] == "213":                     # 입력 — A-213 을 그 값으로
        a = 민.움직이기(a, dict(hm, 방식="값"), 마진, 시)
    else:                                                   # 영구열 — 그 판의 영구기간 영업이익률(결과)과의 차를 가감으로
        지금 = 계.계산(a, 시)["요약"]["영구기간영업이익률"]
        a = 민.움직이기(a, dict(hm, 방식="가산"), 마진 - 지금, 시)
    R = 계.계산(a, 시)
    return _수((R.get("요약") or {}).get("주당가치"))


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("가정")
    ap.add_argument("--성장", required=True, help="행 손잡이의 값 눈금(쉼표) — 기본 손잡이면 예측기간 판매량 증가율")
    ap.add_argument("--마진", required=True, help="영구기간 영업이익률 눈금(쉼표)")
    ap.add_argument("--성장축", default=None, help="행 손잡이 — 가정 번호(616+626) · 민감도.손잡이 의 이름(기본: 첫 증가율 경로 구분)")
    ap.add_argument("--시나리오", default=None, help="기본: 스위치.적용시나리오")
    ap.add_argument("--종가", type=float, default=None, help="기본: 13번 평가기준일 종가(H-099)")
    a = ap.parse_args()

    try:
        원본 = json.load(io.open(a.가정, encoding="utf-8"))
        오류, _경보 = E.검증(원본)
        if 오류:
            raise E.가정오류("가정이 스키마를 어깁니다 — " + " / ".join(오류[:5]))
        시 = a.시나리오 or (원본.get("스위치") or {}).get("적용시나리오", "기준")
        행손잡이 = 성장손잡이(원본, a.성장축)
        성장들 = [float(x) for x in a.성장.split(",")]
        마진들 = [float(x) for x in a.마진.split(",")]
        종가 = a.종가 if a.종가 is not None else _수(민.종가(원본))
    except (E.가정오류, ValueError, IOError, OSError) as e:
        sys.stderr.write("가치동인 입력 오류 — %s\n" % e)
        sys.exit(2)
    if 종가 is not None and 종가 <= 0:
        종가 = None
    입력 = ((원본.get("구조") or {}).get("영구가치") or {}).get("영구이익기준", "입력") == "입력"

    회사 = ((원본.get("메타") or {}).get("회사명")) or a.가정
    print("── 가치동인 매트릭스 — %s · %s 시나리오 · 종가 %s ──"
          % (회사, 시, "{:,.0f}".format(종가) if 종가 else "미기재"))
    print("   행 = %s(값으로 둠) · 열 = 영구기간 영업이익률(%s)"
          % (행손잡이["이름"], "A-213 입력" if 입력 else "결과 — 칸마다 영구기간 열에 가감"))
    print("   괄호 = 음수 · ★ = 종가 이상 칸\n")

    표값 = {}
    for gr in 성장들:
        for m in 마진들:
            try:
                표값[(gr, m)] = 한칸(원본, 시, 행손잡이, gr, m)
            except Exception:                                   # noqa: BLE001 — 그 칸만 「-」
                표값[(gr, m)] = None
    너비 = "%.1f%%" if all(abs(x) < 1 for x in 성장들) else "%.3g"
    머리 = "%-10s " % "행\\마진" + "".join("%12s" % ("%.1f%%" % (m * 100)) for m in 마진들)
    print(머리)
    등가치 = []
    for gr in 성장들:
        줄 = "%10s " % ((너비 % (gr * 100)) if 너비.endswith("%%") else (너비 % gr))
        for m in 마진들:
            v = 표값[(gr, m)]
            if v is None:
                칸 = "-"
            else:
                칸 = "(%s)" % "{:,.0f}".format(-v) if v < 0 else "{:,.0f}".format(v)
                if 종가 and v >= 종가:
                    칸 += "★"
            줄 += "%12s" % 칸
        print(줄)
        if 종가:
            for j in range(1, len(마진들)):
                lo, hi = 표값[(gr, 마진들[j - 1])], 표값[(gr, 마진들[j])]
                if lo is not None and hi is not None and lo < 종가 <= hi:
                    보간 = 마진들[j - 1] + (마진들[j] - 마진들[j - 1]) * (종가 - lo) / (hi - lo)
                    등가치.append((gr, 보간))
    if not 등가치 and 종가:
        print("\n어느 칸도 현재 종가를 넘지 못합니다(또는 전부 넘습니다) — 시장이 가정하는"
              " 조합이 이 눈금 밖에 있습니다.")
        print("→ 판정 문장 재료: 「관측 기간대의 어떤 매출 동인 × 영구기간 영업이익률 조합으로도 현재 주가에 닿지"
              " 않는다 — 주가는 눈금 밖(더 높은 마진·성장, 또는 더 낮은 할인율)을 가정한다」")
    if 등가치:
        print("\n등가치 조합(현재 종가를 성립시키는 눈금):")
        for gr, m in 등가치:
            print("  %s %s 이면 영구기간 영업이익률 약 %.1f%%"
                  % (행손잡이["이름"], ((너비 % (gr * 100)) if 너비.endswith("%%") else (너비 % gr)), m * 100))
        print("→ 판정 문장 재료: 「현재 주가는 위 조합들을 가정하고 있다 — 내 기준 조합이"
              " 이 선의 어느 쪽인가」")


if __name__ == "__main__":
    main()

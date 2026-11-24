# -*- coding: utf-8 -*-
"""역산 — 독자가 고른 주가가 뜻하는 가정을 엔진으로 푼다(R1a K7 · 결정 9 · S9-03 · 04 · 05 · 06).

  python 스크립트/역산.py <가정.json> --주가 1322000 [--날짜 2026-07-30] [--배당 2026-08-14:375 …]
                         [--시나리오 기준] [--축 정상수준 매출성장 목표마진 영구이익률 WACC RONIC 616,626 …] [--등가 RONIC]
                         [--근거 "매수 단가"] [--답 "사람의 답 원문"] [--낼 _raw/역산_독자.json] [--json 낼.json]

  주가      그 날의 주가(주당 금액 단위 — 13번 99 와 같은 단위). --날짜 를 안 주면 평가기준일의 가격으로 본다. 여러 개를 주려면 여러 번 돌린다
  날짜      기준일 밖 가격이면 그 날. 엔진의 주당가치를 그날로 굴려(× (1 + Ke)^(일수 ÷ 365) − 그사이 배당을 그날까지 Ke 로 키운 값)
            가격과 견주고, 역산은 가격을 기준일로 되굴린 목표로 한다(같은 날짜끼리 견준다). Ke = 그 시나리오의 예측기간 자기자본비용.
            **다른 가정은 평가기준일의 것 그대로다 — 그날의 정보로 다시 세운 평가가 아니다**(고정 목록에 적는다)
  배당      날짜:주당(배당락일) — 안 주면 가정의 `역산.배당`
  축        풀 손잡이 — 이름 손잡이(정상수준 · 유지종료연도 · 고점구간 · 도달연도 · RONIC · 가동률 · 유지율 · 매출성장 · 목표마진 · 영구성장률 ·
            영구이익률 · WACC) 또는 가정 번호를 쉼표로(묶음 손잡이). 번호 손잡이의 방식은 칸의 척도로 정한다 — 비율 · 증가율 · 비중이면 가산(경로 모양을
            남긴다), 지수 · 금액 · 연도 밖의 수준이면 배율(묶음의 구분 사이 차를 남긴다), 연도면 가산. 안 주면 엔진의 `역산축목록`
            (선언 · 유형 기본 · 세 방향의 나머지 — 표 Ⅳ 와 같은 차례)
  등가      함께 움직일 손잡이(RONIC 따위) — 첫 축을 그 값마다 다시 푼다(등가 곡선). 값은 영구기간 WACC + 0 · 2.5 · 5 · 10 · 20%p
  근거      그 가격이 무엇인지(매수 단가 · 오늘 종가 · 증권사 목표주가 …) — 결과 파일 · 레터가 그대로 싣는다
  답 · 낼   7단계 끝의 물음(「역산해 볼 가격이 있으십니까」 — 집대성 7단계)에 사람이 답한 원문을 `_raw/멈춤기록.json` 의 답[] 에 남기고(--답),
            결과를 `_raw/역산_독자.json` 에 쌓는다(--낼 · 같은 날짜 · 주가면 갈아 끼운다). 레터 14절이 그 파일을 읽는다
화면: 축마다 시장 내재 값 · 지금 값 대비 · 그 값이 뜻하는 영구기간 영업이익률 · 영구 ROIC · 뜻 범위 밖이면 그 까닭(비고) · 풀이가 없으면 까닭
(값 중립 · 막힘 — 닿는 최댓값 · 범위 밖 — 양 끝 주당 · 계산 실패) · 무엇을 고정했는지.
**이 역산은 그 가격이 무엇을 전제하는지 보이는 것이지 그 가격이 싸다 · 비싸다는 판정이 아니다(「평단은 판정의 근거가 아니다」).**
종료 코드는 `종료코드.py` 규약(0 통과 / 2 입력오류 — 스키마 오류 · 없는 번호 · 모르는 축 · 가격 0 이하).
"""
import argparse
import datetime
import importlib
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
민 = importlib.import_module("엔진.민감도")
from 엔진.계산 import 계산  # noqa: E402
import dcf엔진 as E  # noqa: E402
try:
    from 종료코드 import 통과, 입력오류  # noqa: E402
except Exception:                                     # noqa: BLE001
    통과, 입력오류 = 0, 2

경고문 = "이 역산은 그 가격이 무엇을 전제하는지 보이는 것이지 그 가격이 싸다 · 비싸다는 판정이 아니다(평단은 판정의 근거가 아니다)"


class 역산입력오류(ValueError):
    pass


def _번호방식(번호):
    """S9-05 — 번호 손잡이의 방식을 칸의 척도로(번호 범위로 가르지 않는다): 비율 · 증가율 · 비중 · 탄력성 · 연수 · 시점 → 가산, 그 밖(지수 · 금액 · 계수 · 배수) → 배율."""
    import 거친바퀴 as B                                  # noqa: PLC0415 — 가정칸척도(가정_스키마 12번 표)
    척 = B.가정칸척도(번호)
    n = int(번호)
    if 척 in ("비율", "증가율", "비중", "탄력성", "연수", "시점", "일수"):
        return "가산"
    if 600 < n < 660 and n % 10 in (8, 9):                # 유지 종료 · 도달 연도
        return "가산"
    return "배율"


def _손잡이(이름, 가정):
    if "," in 이름 or "+" in 이름 or 이름.isdigit():
        대상 = ["%d" % int(x) for x in 이름.replace("+", ",").split(",") if x.strip()]
        없는 = [x for x in 대상 if x not in (가정.get("가정") or {}) and x not in (가정.get("시점가정") or {})]
        if 없는:
            raise 역산입력오류("축 %s — 가정 파일에 없는 번호입니다(가정 · 시점가정): %s" % (이름, " · ".join(없는)))
        방식 = _번호방식(대상[0])
        return {"이름": "가정 %s" % " · ".join(대상), "대상": 대상, "방식": 방식, "폭": 0.05}
    try:
        h = 민.손잡이풀기(이름, 가정)
    except ValueError as e:
        raise 역산입력오류("축 「%s」 를 모릅니다 — %s" % (이름, e))
    if not h.get("대상"):
        raise 역산입력오류("축 %s — 이 가정의 구조에는 그 이름 손잡이의 대상이 없습니다" % 이름)
    if 이름 == "정상수준":
        h = dict(h, 방식="배율")                          # S9-05 — 묶음 정상 수준의 기본은 배율(값이면 구분 사이의 차가 지워진다)
    return h


def 풀기(가정, 주가, 날짜=None, 배당=None, 시나리오="기준", 축들=None, 등가=None, 근거=None):
    오류, _경보 = E.검증(가정)
    if 오류:
        raise 역산입력오류("가정이 스키마를 어깁니다 — " + " / ".join(오류[:5]))
    if not isinstance(주가, (int, float)) or 주가 <= 0:
        raise 역산입력오류("주가가 0 이하입니다: %s" % 주가)
    R0 = 계산(가정, 시나리오)
    낸 = {"시나리오": 시나리오, "주가": 주가, "날짜": 날짜 or (가정.get("메타") or {}).get("평가기준일"), "근거": 근거,
         "기준일주당가치": R0["요약"]["주당가치"], "경고": 경고문, "조회": datetime.datetime.now().isoformat(timespec="seconds")}
    목표 = 주가
    if 날짜:
        목표, g = 민.되굴림(가정, 날짜, 주가, 시나리오, R0, 배당)
        굴 = 민.굴림(가정, 날짜, None, 시나리오, R0, 배당)
        낸.update({"굴림": 굴, "가격÷굴린주당가치": 주가 / 굴["굴린주당"] if 굴["굴린주당"] else None, "되굴린목표": 목표})
    if not 축들:
        축들 = 민.역산축목록(가정)
    else:
        축들 = [_손잡이(x, 가정) if isinstance(x, str) else x for x in 축들]
    낸["축"] = []
    for h in 축들:
        r = 민.역산(가정, 목표, 시나리오, h)
        한 = {"이름": h["이름"], "대상": h["대상"], "방식": h.get("방식", "가산"), "유형기본": bool(h.get("유형기본")),
             "지금": r.get("적용값") if (isinstance(r, dict) and r.get("적용값") is not None) else 민.적용값(가정, h, 시나리오, R0)}
        if isinstance(r, dict) and r.get("값") is not None:
            한.update({k: r[k] for k in ("값", "가감", "내재영구이익률", "내재영구ROIC", "내재영구매출액", "내재영구영업이익",
                                       "내재마지막해영업이익률", "내재매출CAGR", "손잡이값") if k in r})
            비고 = 민.역산비고(h, r["값"], R0)
            if 비고:
                한["비고"] = 비고
        else:
            한["결과"] = (r or {}).get("결과") or "해당 없음"
            한["까닭"] = (r or {}).get("까닭")
            for k in ("닿는끝", "양끝"):
                if (r or {}).get(k):
                    한[k] = r[k]
        한["고정"] = 민.고정목록(가정, h, 시나리오, R0, 날짜=날짜)
        낸["축"].append(한)
    if 등가:
        낸["등가"] = 민.등가곡선(가정, 목표, 시나리오, 축=축들[0], 함께=등가)
    return 낸


def _수(v, 꼴="%.4f"):
    return "—" if not isinstance(v, (int, float)) else 꼴 % v


def 화면(낸):
    L = ["시나리오 %s · 주가 %s (%s%s) · 기준일 주당가치 %s" % (낸["시나리오"], "{:,.0f}".format(낸["주가"]), 낸["날짜"],
                                                       (" · " + 낸["근거"]) if 낸.get("근거") else "", "{:,.0f}".format(낸["기준일주당가치"]))]
    if "굴림" in 낸:
        g = 낸["굴림"]
        L.append("  그날로 굴린 주당가치 %s (Ke %.2f%% · %d일 · 배당 차감 %s) · 가격 ÷ 굴린 값 %s · 역산 목표(기준일로 되굴림) %s"
                 % ("{:,.0f}".format(g["굴린주당"]), g["Ke"] * 100, g["일수"], "{:,.0f}".format(g["배당차감"]),
                    _수(낸["가격÷굴린주당가치"], "%.3f"), "{:,.0f}".format(낸["되굴린목표"])))
    for 한 in 낸["축"]:
        머 = "%s%-28s" % ("*" if 한.get("유형기본") else " ", 한["이름"])
        if "값" in 한:
            L.append("  %s 시장 내재 %s (지금 %s · 차 %s) · 뜻하는 영구기간 영업이익률 %s · 영구 ROIC %s%s"
                     % (머, _수(한["값"]), _수(한["지금"]), _수(한.get("가감"), "%+.4f"),
                        _수(한.get("내재영구이익률")), _수(한.get("내재영구ROIC")),
                        (" · 비고 " + 한["비고"]) if 한.get("비고") else ""))
        else:
            L.append("  %s %s" % (머, 한.get("결과")))
    if 낸["축"]:
        L.append("  고정(한 번에 하나만 풀고 나머지는 이 값 그대로): %s" % " · ".join(낸["축"][0].get("고정") or []))
    if 낸.get("등가"):
        e = 낸["등가"]
        L.append("  등가 곡선 — %s 를 두고 %s 를 푼다" % (e["함께"], e["축"]))
        for 한 in e["줄"]:
            L.append("    %s %s → %s %s · 영구기간 영업이익률 %s%s" % (e["함께"], _수(한["함께값"]), e["축"], _수(한.get("값")) if "값" in 한 else 한.get("결과"),
                                                         _수(한.get("내재영구이익률")), (" · " + 한["비고"]) if 한.get("비고") else ""))
    L.append("  * = 유형 기본 축(S9-03) · " + 경고문)
    return "\n".join(L)


def 쌓기(곳, 낸):
    """`_raw/역산_독자.json` 에 결과를 쌓는다 — {"목록": [ … ]}. 같은 (날짜 · 주가 · 시나리오)면 갈아 끼운다."""
    j = {}
    if os.path.exists(곳):
        try:
            j = json.load(io.open(곳, encoding="utf-8"))
        except (OSError, ValueError):
            j = {}
    목록 = [x for x in (j.get("목록") or []) if isinstance(x, dict)
          and not (x.get("날짜") == 낸["날짜"] and x.get("주가") == 낸["주가"] and x.get("시나리오") == 낸["시나리오"])]
    목록.append(낸)
    j = {"소유": "본선 — 7단계 끝 「역산해 볼 가격」(결정 9 · S9-06). 판정이 아니라 그 가격의 전제다", "목록": 목록}
    os.makedirs(os.path.dirname(os.path.abspath(곳)) or ".", exist_ok=True)
    with io.open(곳, "w", encoding="utf-8", newline="\n") as f:
        json.dump(j, f, ensure_ascii=False, indent=1, default=str)
        f.write("\n")


def 답적기(곳, 답, 주가, 날짜):
    """`_raw/멈춤기록.json` 의 답[] 에 사람의 답 원문을 남긴다(S9-06 — 「역산해 볼 가격」 물음)."""
    j = {}
    if os.path.exists(곳):
        try:
            j = json.load(io.open(곳, encoding="utf-8"))
        except (OSError, ValueError):
            j = {}
    j.setdefault("답", []).append({"시각": datetime.datetime.now().isoformat(timespec="minutes"), "노드": "역산 가격",
                                  "물음": "역산해 볼 가격이 있으십니까 — 매수 단가 · 오늘 종가 · 증권사 목표주가(집대성 7단계)",
                                  "답": 답, "누가": "사람", "주가": 주가, "날짜": 날짜})
    os.makedirs(os.path.dirname(os.path.abspath(곳)) or ".", exist_ok=True)
    with io.open(곳, "w", encoding="utf-8", newline="\n") as f:
        json.dump(j, f, ensure_ascii=False, indent=1)
        f.write("\n")


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="독자 지정 주가 역산")
    ap.add_argument("가정")
    ap.add_argument("--주가", type=float, required=True)
    ap.add_argument("--날짜")
    ap.add_argument("--배당", nargs="*", default=None, help="날짜:주당 …")
    ap.add_argument("--시나리오", default="기준", choices=("비관", "기준", "낙관"))
    ap.add_argument("--축", nargs="*", default=None)
    ap.add_argument("--등가")
    ap.add_argument("--근거", default=None, help="그 가격이 무엇인지(매수 단가 · 오늘 종가 · 증권사 목표주가 …)")
    ap.add_argument("--답", default=None, help="7단계 물음에 사람이 답한 원문 — _raw/멈춤기록.json 의 답[] 에 남긴다")
    ap.add_argument("--낼", default=None, help="결과를 쌓을 파일(기본: 가정 곁 _raw/역산_독자.json — --낼 끔 이면 쓰지 않는다)")
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    try:
        with io.open(a.가정, encoding="utf-8") as f:
            가정 = json.load(f)
        배당 = None if a.배당 is None else [{"날짜": x.split(":")[0], "주당": float(x.split(":")[1])} for x in a.배당]
        if a.날짜:
            datetime.date.fromisoformat(a.날짜[:10])
        낸 = 풀기(가정, a.주가, a.날짜, 배당, a.시나리오, a.축, a.등가, a.근거)
    except (역산입력오류, E.가정오류, ValueError, IndexError, OSError) as e:
        sys.stderr.write("역산 입력 오류 — %s\n" % e)
        return 입력오류
    print(화면(낸))
    곁 = os.path.join(os.path.dirname(os.path.abspath(a.가정)), "_raw")
    if a.낼 != "끔" and (a.낼 or a.근거 or a.답):           # S9R1-N7 — 진단용 실행(근거 · 답 없음)은 레터 14절 「독자가 고른 가격」에 섞지 않는다
        곳 = a.낼 or os.path.join(곁, "역산_독자.json")
        쌓기(곳, 낸)
        print("쌓은 곳: %s" % 곳)
    if a.답:
        답적기(os.path.join(곁, "멈춤기록.json"), a.답, a.주가, a.날짜)
        print("답을 멈춤 기록에 남겼다: %s" % os.path.join(곁, "멈춤기록.json"))
    if a.json:
        with io.open(a.json, "w", encoding="utf-8", newline="\n") as f:
            json.dump(낸, f, ensure_ascii=False, indent=1, default=str)
    return 통과


if __name__ == "__main__":
    sys.exit(main())

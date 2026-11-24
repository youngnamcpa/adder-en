# -*- coding: utf-8 -*-
"""기준일 — 가정 파일의 두 날짜(평가기준일 · 재무기준일)를 한 곳에서 푼다(2026-10-25 결정 · 설계/0_결정.md).

  평가기준일 T  정보 마감일 = 분석하는 날. 값 · 시장 자료(무위험이자율 · ERP · 베타 창 끝 · 신용스프레드 · 종가 · 주식수) ·
                정보 경계(T 뒤에 처음 생긴 사건만 「뒤」) · 레터가 이 날을 쓴다.
  재무기준일 F  T 전에 제출된 마지막 정기보고서(감사 · 검토를 거친 재무상태표)의 기간 끝 = 회사의 분기말.
                기간축(실적 열 · 첫 예측 열) · 원천 받기 · 운전자본 · 유무형자산 기초가 이 날을 쓴다.

  "메타": {"평가기준일": "2026-10-23", "재무기준일": "2026-06-30"}

**재무기준일이 없으면 F = 평가기준일로 읽는다** — 옛 가정 파일은 두 날짜가 같은 판(이월 연수 0)이라 값이 그대로다.
날짜를 도구마다 따로 읽지 않는다. 모든 도구가 이 모듈의 `기준일들` · `재무기준일` · `평가기준일` 을 부른다.

이월 연수 τ = (T − F) 일수 ÷ 365(기간축의 「일수 ÷ 365 × 12」 와 같은 밑). 주주가치 이월은 엔진이 한다
(주주가치_T = 주주가치_F × (1 + 자기자본비용)^τ + (F, T] 자본거래).

  python 스크립트/기준일.py 가정.json          # 두 날짜 · 이월 연수 · 점검(경보)
  python 스크립트/기준일.py 가정.json --json   # 같은 것을 JSON 으로

점검 — 오류(종료 2): 날짜 꼴이 아님 · F > T.
       경보(종료 1): T − F 가 문턱(`간격경보일`)을 넘음 — 더 늦은 분기 보고가 이미 제출됐을 수 있다.
                     F 가 회사 분기말(결산월 기준 · 말일 ± 10일)에 맞지 않음.
표준 라이브러리만 쓴다. 회사 · 업종 이름은 없다.
"""
import argparse
import calendar
import io
import json
import sys
from datetime import date, datetime

형식 = "기준일/1"
간격경보일 = 200          # 분기 길이 92일 + 연차보고서 제출기한 90일 + 여유 — 이보다 멀면 더 늦은 보고가 있을 수 있다
분기말허용일 = 10         # 52 · 53주 결산 등 말일과 며칠 어긋나는 회사


class 기준일오류(Exception):
    """날짜가 없거나 꼴이 아니거나 앞뒤가 뒤집혔다."""


def 날짜(v):
    """'YYYY-MM-DD' · date · datetime → date."""
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        try:
            return datetime.strptime(v.strip()[:10], "%Y-%m-%d").date()
        except ValueError:
            pass
    raise 기준일오류("날짜 꼴이 아닙니다 — %r (YYYY-MM-DD)" % (v,))


def _메타(가정):
    m = (가정 or {}).get("메타") if isinstance(가정, dict) else None
    return m if isinstance(m, dict) else {}


def 평가기준일(가정):
    """T — 메타.평가기준일(없으면 오류)."""
    v = _메타(가정).get("평가기준일")
    if v in (None, ""):
        raise 기준일오류("메타.평가기준일 이 없습니다")
    return 날짜(v)


def 재무기준일(가정):
    """F — 메타.재무기준일, 없으면 평가기준일(옛 꼴 · 두 날짜가 같은 판)."""
    v = _메타(가정).get("재무기준일")
    if v in (None, ""):
        return 평가기준일(가정)
    return 날짜(v)


def 이월연수(가정):
    """τ = (T − F) 일수 ÷ 365."""
    return (평가기준일(가정) - 재무기준일(가정)).days / 365.0


def 자료경계(가정):
    """레터가 「재무 자료 기준일 뒤에 공표돼 값에 닿은 자료」(레터부록 `기준일뒤자료`)를 부르는 말과 검증 경계(2026-10-26).
    옛 판(F = T): 「평가기준일 뒤」 — 공표일 > T. 이월 판(F < T): 「재무 자료 기준일과 평가기준일 사이」 — F < 공표일 ≤ T(평가기준일 뒤 자료는 값에 쓰지 않는다)."""
    try:
        F, T = 재무기준일(가정), 평가기준일(가정)
    except 기준일오류:
        return {"이월": False, "F": None, "T": None, "말": "평가기준일 뒤", "제목": "평가기준일 뒤에 공표된 자료를 참고한 가정"}
    if F < T:
        return {"이월": True, "F": F.isoformat(), "T": T.isoformat(), "말": "재무 자료 기준일과 평가기준일 사이",
                "제목": "재무 자료 기준일 뒤 · 평가기준일까지 공표된 자료를 참고한 가정"}
    return {"이월": False, "F": F.isoformat(), "T": T.isoformat(), "말": "평가기준일 뒤", "제목": "평가기준일 뒤에 공표된 자료를 참고한 가정"}


def _월말(y, m):
    return date(y, m, calendar.monthrange(y, m)[1])


def 분기말인가(d, 결산월=12, 허용=분기말허용일):
    """d 가 결산월 기준 회사 분기말(말일 ± 허용일)에 맞는가 → (맞음, 가장 가까운 분기말)."""
    달들 = sorted({((int(결산월) - 1 + 3 * k) % 12) + 1 for k in range(4)})
    후보 = []
    for y in (d.year - 1, d.year, d.year + 1):
        for m in 달들:
            후보.append(_월말(y, m))
    가까 = min(후보, key=lambda x: abs((x - d).days))
    return abs((가까 - d).days) <= 허용, 가까


def 기준일들(가정):
    """→ {형식, 평가기준일, 재무기준일, 이월연수, 같음, 재무기준일출처, 경보[], 오류[]} (날짜는 ISO 글)."""
    오류, 경보 = [], []
    try:
        T = 평가기준일(가정)
    except 기준일오류 as e:
        return {"형식": 형식, "오류": [str(e)], "경보": []}
    try:
        F = 재무기준일(가정)
    except 기준일오류 as e:
        return {"형식": 형식, "평가기준일": T.isoformat(), "오류": [str(e)], "경보": []}
    출처 = "메타.재무기준일" if _메타(가정).get("재무기준일") not in (None, "") else "평가기준일과 같음(메타.재무기준일 없음 — 옛 꼴)"
    if F > T:
        오류.append("재무기준일 %s 이 평가기준일 %s 보다 늦습니다 — 재무기준일은 평가기준일 전에 제출된 마지막 분기말입니다"
                  % (F.isoformat(), T.isoformat()))
    간격 = (T - F).days
    if 간격 > 간격경보일:
        경보.append("평가기준일과 재무기준일이 %d일 떨어져 있습니다(문턱 %d일) — 그 사이에 더 늦은 분기 보고가 제출됐는지 확인합니다"
                  % (간격, 간격경보일))
    결산월 = ((가정 or {}).get("기간") or {}).get("결산월") or 12
    맞음, 가까 = 분기말인가(F, 결산월)
    if not 맞음:
        경보.append("재무기준일 %s 이 회사 분기말(결산월 %s · 가장 가까운 %s)과 %d일 어긋납니다"
                  % (F.isoformat(), 결산월, 가까.isoformat(), abs((가까 - F).days)))
    return {"형식": 형식, "평가기준일": T.isoformat(), "재무기준일": F.isoformat(), "이월연수": 간격 / 365.0,
            "간격일": 간격, "같음": 간격 == 0, "재무기준일출처": 출처, "경보": 경보, "오류": 오류}


def main(argv=None):
    ap = argparse.ArgumentParser(description="가정 파일의 평가기준일 · 재무기준일 · 이월 연수")
    ap.add_argument("가정")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                   # noqa: BLE001
        pass
    g = json.load(io.open(a.가정, encoding="utf-8"))
    r = 기준일들(g)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        if r.get("오류"):
            for x in r["오류"]:
                print("오류 — " + x)
        else:
            print("평가기준일 %s · 재무기준일 %s(%s) · 이월 %.4f년(%d일)"
                  % (r["평가기준일"], r["재무기준일"], r["재무기준일출처"], r["이월연수"], r["간격일"]))
        for x in r.get("경보") or []:
            print("경보 — " + x)
    return 2 if r.get("오류") else (1 if r.get("경보") else 0)


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""대안평가 — 현금흐름할인법이 서지 않거나 기준 시나리오의 주주가치가 음수일 때 대안 평가(생애주기 단계에 따른 배수)의 값을 낸다(S8-09).

  python 스크립트/대안평가.py 가정.json                       # → 가정 곁 _raw/대안평가.json · 표를 찍는다
  python 스크립트/대안평가.py 가정.json --표본 핵심 --해 FY2025

재료 — 네트워크 없이 이미 받은 C2 파일만 읽는다
  · 유사기업 시가 · 차입 · 현금: `_raw/peers/βU_{표본}.json` 의 「표」(시가총액 · D · 현금·단기투자 · 부채총계 · 자산총계 — C2 조립기)
  · 유사기업 손익: `_raw/peers/운영지표_{표본}.json` 의 「회사[].재료.{회계연도}」(매출액 · 영업이익 · 감가상각비 · 법인세차감전이익 · 법인세비용)
  · 대상 지표: 원천 13번의 마지막 회계연도 실적 열(62 매출액 · 66 영업이익 · 77 + 78 상각 · 74 지배 순이익(없으면 73) · 56 지배 자본(없으면 58))
  · 브리지: 엔진 기준 시나리오의 2번 59 · 60 · 61 · 62 · 63 · 64 · 65 · 152 · 메타.환산배율(DCF 와 같은 브리지)
배수 넷 — EV/매출 · EV/EBITDA · PER · PBR(EV = 시가총액 + D − 현금 · 단기투자). 회사마다 같은 원천(같은 단위)의 분자 · 분모로 내므로
단위가 맞는다. 음수 · 0 분모의 배수는 뺀다(적자 회사의 PER 따위 — 뺀 수를 적는다). 대상 지표가 0 이하면 그 배수는 쓰지 않는다.
값은 배수의 중앙값 · 사분위(25 · 75%) · 범위로 내고 주당가치로 옮긴다. **단계와 배수는 사람이 고른다** — `메타.생애주기.단계` 로 둘을 제안만 한다
(도입 · 성장 · 젊은 회사 → EV/매출 · EV/EBITDA, 성숙 → EV/EBITDA · PER, 쇠퇴 · 자산 중심 → EV/EBITDA · PBR).
DCF 를 대신하지 않는다 — 레터에는 DCF 값과 나란히 싣고 어느 쪽을 결론으로 둘지는 사람이 정한다. 회사 · 업종 이름은 한 글자도 없다.
"""
import argparse
import copy
import io
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

배수들 = ("EV/매출", "EV/EBITDA", "PER", "PBR")


def _수(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _읽기(경로):
    try:
        return json.load(io.open(경로, encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _대상지표(가정, 해=None):
    원 = 가정.get("원천") or {}
    열들 = sorted({c for v in 원.values() if isinstance(v, dict) for c in v if ("%s" % c).startswith("FY")})
    열 = 해 if 해 in 열들 else (열들[-1] if 열들 else None)

    def v(번):
        x = (원.get("%d" % 번) or {}).get(열)
        return x if _수(x) else None
    상각 = (v(77) or 0.0) + (v(78) or 0.0)
    영 = v(66)
    return 열, {"매출": v(62), "EBITDA": (영 + 상각) if 영 is not None else None,
               "순이익": v(74) if v(74) is not None else v(73), "자본": v(56) if v(56) is not None else v(58)}


def _동종배수(βU, 운영, 해=None):
    """회사마다 배수 — [{이름, EV/매출, EV/EBITDA, PER, PBR}] 와 뺀 까닭."""
    재료 = {}
    for c in (운영 or {}).get("회사") or []:
        if not isinstance(c, dict):
            continue
        r = c.get("재료") or {}
        키 = sorted(r)
        if not 키:
            continue
        k = 해 if 해 in r else 키[-1]
        재료[("%s" % (c.get("코드") or "")).strip() or c.get("이름")] = (c.get("이름"), r[k], k)
        재료[c.get("이름")] = (c.get("이름"), r[k], k)
    낸, 뺀 = [], []
    for row in (βU or {}).get("표") or []:
        이름 = row.get("티커") or row.get("회사명")
        짝 = 재료.get(("%s" % (row.get("종목코드") or "")).strip()) or 재료.get(이름)
        시총 = row.get("시가총액")
        if not _수(시총) or not 시총:
            뺀.append("%s(시가총액 없음)" % 이름)
            continue
        ev = 시총 + (row.get("D") or 0.0) - (row.get("현금·단기투자") or 0.0)
        x = {"이름": 이름, "시가총액": 시총, "EV": ev, "해": 짝[2] if 짝 else None}
        if 짝:
            r = 짝[1]
            매, 영, 상 = r.get("매출액"), r.get("영업이익"), r.get("감가상각비")
            세전, 세 = r.get("법인세차감전이익"), r.get("법인세비용")
            ebitda = (영 + (상 or 0.0)) if _수(영) else None
            순 = (세전 - (세 or 0.0)) if _수(세전) else None
            x["EV/매출"] = ev / 매 if _수(매) and 매 > 0 else None
            x["EV/EBITDA"] = ev / ebitda if _수(ebitda) and ebitda > 0 else None
            x["PER"] = 시총 / 순 if _수(순) and 순 > 0 else None
        자 = (row.get("자산총계") - row.get("부채총계")) if _수(row.get("자산총계")) and _수(row.get("부채총계")) else None
        x["PBR"] = 시총 / 자 if _수(자) and 자 > 0 else None
        if not 짝:
            뺀.append("%s(손익 재료 없음 — EV/매출 · EV/EBITDA · PER 빠짐)" % 이름)
        낸.append(x)
    return 낸, 뺀


def _사분(v):
    v = sorted(v)
    if not v:
        return None
    q = statistics.quantiles(v, n=4) if len(v) >= 2 else [v[0], v[0], v[0]]
    return {"수": len(v), "중앙값": statistics.median(v), "25%": q[0], "75%": q[2], "최소": v[0], "최대": v[-1]}


def 제안배수(단계):
    t = "%s" % (단계 or "")
    if any(x in t for x in ("도입", "초기", "젊", "성장", "적자")):
        return ("EV/매출", "EV/EBITDA")
    if any(x in t for x in ("쇠퇴", "청산", "자산")):
        return ("EV/EBITDA", "PBR")
    if "성숙" in t:
        return ("EV/EBITDA", "PER")
    return None


def 대안표(가정, 가정경로=None, 표본="핵심", 해=None):
    d = os.path.dirname(os.path.abspath(가정경로)) if 가정경로 else os.getcwd()
    peers = os.path.join(d, "_raw", "peers")
    βU = _읽기(os.path.join(peers, "βU_%s.json" % 표본)) or _읽기(os.path.join(peers, "βU_병합_%s.json" % 표본))
    운영 = _읽기(os.path.join(peers, "운영지표_%s.json" % 표본))
    열, 대상 = _대상지표(가정, 해)
    import dcf엔진 as E                                       # noqa: PLC0415
    R = E.계산(copy.deepcopy(가정), "기준")
    D = R["2.DCF"]
    브리지 = sum((D.get(k) or 0.0) for k in ("59", "60", "65")) - sum((D.get(k) or 0.0) for k in ("61", "62", "63", "64"))
    브리지 += (D.get("165") or 0.0)                          # 날짜 둘 — F 장부 브리지에 (F, T] 자본거래 현금을 더해 T 주식수(152)와 같은 날로
    주식, 배율 = D.get("152") or 0.0, float((가정.get("메타") or {}).get("환산배율") or 1)
    동, 뺀 = _동종배수(βU, 운영, 해) if βU else ([], ["βU_%s.json 없음 — C2 조립기를 먼저 돌린다" % 표본])
    표 = {}
    for m in 배수들:
        통 = _사분([x[m] for x in 동 if _수(x.get(m))])
        지표 = {"EV/매출": 대상["매출"], "EV/EBITDA": 대상["EBITDA"], "PER": 대상["순이익"], "PBR": 대상["자본"]}[m]
        if 통 is None or not _수(지표) or 지표 <= 0:
            표[m] = {"동종": 통, "대상지표": 지표, "주당": None,
                    "까닭": "동종 배수 없음" if 통 is None else "대상 지표가 없거나 0 이하"}
            continue
        주당 = {}
        for k in ("25%", "중앙값", "75%"):
            값 = 통[k] * 지표 + (브리지 if m.startswith("EV") else 0.0)
            주당[k] = (값 * 배율 / 주식) if 주식 else None
        표[m] = {"동종": 통, "대상지표": 지표, "주당": 주당}
    단계 = (((가정.get("메타") or {}).get("생애주기") or {}).get("단계")) if isinstance((가정.get("메타") or {}).get("생애주기"), dict) else None
    return {"표본": 표본, "대상열": 열, "대상지표": 대상, "브리지": 브리지, "적용주식수": 주식, "환산배율": 배율,
            "DCF주당(기준)": R["요약"]["주당가치"], "배수": 표, "동종": 동, "뺀": 뺀,
            "생애주기단계": 단계, "제안": 제안배수(단계),
            "주의": "단계 판정과 배수 선택은 사람이 한다. DCF 값과 나란히 싣고 결론은 사람이 정한다"}


def _금(x):
    return "—" if not _수(x) else "{:,.0f}".format(x)


def 표글(t):
    줄 = ["대안 평가 — 배수 평가(표본 %s · 대상 %s · DCF 기준 주당 %s)" % (t["표본"], t["대상열"], _금(t["DCF주당(기준)"]))]
    for m in 배수들:
        x = t["배수"][m]
        통 = x.get("동종")
        if x.get("주당") is None:
            줄.append("  %-10s 재료 없음 — %s" % (m, x.get("까닭")))
            continue
        줄.append("  %-10s 동종 %d곳 중앙값 %.2f배(25~75%% %.2f~%.2f) × 대상 %s → 주당 %s (%s ~ %s)" % (
            m, 통["수"], 통["중앙값"], 통["25%"], 통["75%"], _금(x["대상지표"]), _금(x["주당"]["중앙값"]), _금(x["주당"]["25%"]), _금(x["주당"]["75%"])))
    if t["제안"]:
        줄.append("  제안(사람이 고른다) — 생애주기 「%s」: %s" % (t["생애주기단계"], " · ".join(t["제안"])))
    if t["뺀"]:
        줄.append("  뺀 회사 — " + " · ".join(t["뺀"][:8]))
    줄.append("  " + t["주의"])
    return "\n".join(줄)


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(allow_abbrev=False, description="대안 평가 — 유사기업 배수 평가(EV/매출 · EV/EBITDA · PER · PBR)")
    ap.add_argument("가정")
    ap.add_argument("--표본", default="핵심")
    ap.add_argument("--해", default=None, help="대상 · 동종 손익의 회계연도(기본 마지막)")
    ap.add_argument("--낼", default=None)
    a = ap.parse_args(argv)
    g = _읽기(a.가정)
    if not isinstance(g, dict):
        print("입력오류 — 가정 파일을 못 읽었다")
        return 2
    t = 대안표(g, a.가정, a.표본, a.해)
    print(표글(t))
    낼 = a.낼 or os.path.join(os.path.dirname(os.path.abspath(a.가정)), "_raw", "대안평가.json")
    os.makedirs(os.path.dirname(낼), exist_ok=True)
    with io.open(낼, "w", encoding="utf-8", newline="\n") as f:
        json.dump(t, f, ensure_ascii=False, indent=1, default=str)
    print("낸 파일: %s" % 낼)
    return 0


if __name__ == "__main__":
    sys.exit(main())

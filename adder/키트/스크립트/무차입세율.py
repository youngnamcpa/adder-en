# -*- coding: utf-8 -*-
"""무차입세율 — 유사기업 βU 를 벗길 때 쓰는 세율의 **단일 출처**(2026-10-24 W18 · 유니버스 조사 물결 실측).

왜 있는가
    국내 · 미국 조립기(`peer_조립.py` · `peer_βU_us.py`)가 `--세율` 을 사람이 적어 넣게 해서, 같은 유니버스 안에서
    공통 세율이 0.264(시장데이터 캐시의 다모다란 국가 한계세율 · 2025년 법) · 0.275(법령 세율표 · 2026년 법)로 갈렸다
    (유니버스 국내 조사 가운데 0.264 를 준 곳과 0.275 를 준 곳 · 미국 조사 0.21 과 0.25 가 섞였다). 회사끼리 βU 를 나란히 놓을 수 없었다.

출처 차례(값을 보기 전에 정한 규칙)
    · 국내(KR) — **법령 세율표**(`한계세율.py` — 법인세법 제55조 · 지방세법 제103조의20, 평가기준일까지 공포된 판). 법인세 규칙
      「한계세율은 법령 원문에서」. 회사별 세율은 직전 사업연도 영업이익을 과세표준 근사로 그 구간, 영업이익이 없거나 0 이하면 최고 구간
    · 그 밖의 나라 — **시장데이터 캐시**(`~/.dcf캐시/시장데이터_<국가>_<평가기준일>.json` 「국가 한계세율(다모다란)」)
    · 둘 다 없으면 None — 지어내지 않는다(조립기는 `--세율` 을 받아야 돈다)
대조
    · 사람이 `--세율` 을 주었는데 이 출처와 0.5%p 넘게 다르면 경보 문장을 낸다(값은 사람이 준 것을 쓰되 산출 머리에 남긴다)
    · 국내는 다모다란 캐시 값과 법령 값이 다르면 참고 문장(다모다란 표가 개정을 늦게 반영한다 — 2026년 26.4% 대 27.5%)
"""
from __future__ import annotations

import io
import json
import os
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)

허용차 = 0.005
최고구간과세표준 = 1e15


def _날짜(기준일):
    s = ("%s" % 기준일).replace("-", "")
    return "%s-%s-%s" % (s[:4], s[4:6], s[6:8]) if len(s) == 8 else ("%s" % 기준일)


def _공용뿌리():
    return (os.environ.get("DCF_공용캐시") or os.environ.get("DCF_SHARED_CACHE")
            or os.path.join(os.path.expanduser("~"), ".dcf캐시"))


def 캐시세율(국가, 기준일):
    """시장데이터 캐시의 국가 한계세율(다모다란) → (값, 출처 글) 또는 (None, 까닭)."""
    p = os.path.join(_공용뿌리(), "시장데이터_%s_%s.json" % (("%s" % 국가).upper(), _날짜(기준일)))
    if not os.path.exists(p):
        return None, "시장데이터 캐시 없음(%s)" % os.path.basename(p)
    try:
        d = json.load(io.open(p, encoding="utf-8"))
    except (OSError, ValueError) as e:
        return None, "시장데이터 캐시를 읽지 못함(%s)" % type(e).__name__
    v = (d.get("국가 한계세율(다모다란)") or {}).get("값")
    if not isinstance(v, (int, float)):
        return None, "시장데이터 캐시에 국가 한계세율이 없음"
    return float(v), "시장데이터 캐시 「국가 한계세율(다모다란)」 %s" % os.path.basename(p)


def 법령세율(기준일, 영업이익=None):
    """국내 법령 세율표 → (값, 출처 글) 또는 (None, 까닭). 영업이익이 양수면 그 구간, 아니면 최고 구간."""
    try:
        import 한계세율 as _h                       # noqa: PLC0415
    except Exception as e:                           # noqa: BLE001
        return None, "법령 세율표 도구를 못 읽음(%s)" % type(e).__name__
    과표 = 영업이익 if (isinstance(영업이익, (int, float)) and 영업이익 > 0) else 최고구간과세표준
    try:
        r = _h.한계세율(_날짜(기준일), 과표)
    except Exception as e:                           # noqa: BLE001
        return None, "법령 세율표 조회 실패(%s)" % type(e).__name__
    v = (r or {}).get("한계세율")
    if not isinstance(v, (int, float)):
        return None, "법령 세율표에 그 해 판이 없음(미확인)"
    구 = ("영업이익 %.0f억 구간(과세표준 근사)" % (영업이익 / 1e8)) if 과표 is not 최고구간과세표준 else "최고 구간"
    return float(v), "법령 세율표 — %s %s(법인세 %.3f + 지방소득세 %.4f)" % (_날짜(기준일)[:4], 구, r.get("법인세율") or 0, r.get("지방소득세율") or 0)


def 공통세율(국가, 기준일):
    """그 나라의 무차입 공통 세율 → {"값", "출처", "참고"}. 값이 None 이면 출처에 까닭."""
    국 = ("%s" % 국가).upper()
    참고 = []
    if 국 == "KR":
        v, 출 = 법령세율(기준일)
        cv, _ = 캐시세율(국, 기준일)
        if v is not None and cv is not None and abs(v - cv) > 허용차:
            참고.append("다모다란 국가 한계세율 %.3f 와 법령 세율표 %.3f 가 다르다 — 법령을 쓴다(다모다란 표가 개정을 늦게 반영)" % (cv, v))
        if v is None and cv is not None:
            참고.append("법령 세율표가 없어 다모다란 캐시 값으로 물러섰다")
            v, 출 = cv, _
        return {"값": v, "출처": 출, "참고": 참고}
    v, 출 = 캐시세율(국, 기준일)
    return {"값": v, "출처": 출, "참고": 참고}


def 회사세율(국가, 기준일, 영업이익=None):
    """회사 한 곳의 무차입 세율 → {"값", "출처"}. 국내는 영업이익 구간, 그 밖은 공통."""
    if ("%s" % 국가).upper() == "KR":
        v, 출 = 법령세율(기준일, 영업이익)
        if v is not None:
            return {"값": v, "출처": 출}
    r = 공통세율(국가, 기준일)
    return {"값": r["값"], "출처": r["출처"]}


def 대조(준값, 국가, 기준일):
    """사람이 준 세율과 단일 출처를 맞댄다 → (쓸 값, 경보 글 또는 None, 출처 글)."""
    r = 공통세율(국가, 기준일)
    if 준값 is None:
        return r["값"], None, r["출처"] + "".join(" · 참고: " + x for x in r["참고"])
    if r["값"] is not None and abs(float(준값) - r["값"]) > 허용차:
        return (float(준값), "`--세율` %.4f 이 단일 출처(%s) %.4f 와 %.1f%%p 다르다 — 유니버스 βU 를 나란히 놓으려면 단일 출처 값을 쓴다"
                % (float(준값), r["출처"], r["값"], abs(float(준값) - r["값"]) * 100), "--세율(사람)")
    return float(준값), None, "--세율(사람 · 단일 출처와 같음)"


def main(argv=None):
    import argparse                                  # noqa: PLC0415
    ap = argparse.ArgumentParser(description="무차입 세율 단일 출처 조회", allow_abbrev=False)
    ap.add_argument("--국가", required=True)
    ap.add_argument("--기준일", "--평가기준일", dest="기준일", required=True, help="평가기준일 T(분석일 · 시장 쪽 — 종가 · 시가총액 · 주식수 · 베타 창 끝 · 환율 · 법령 시행일) YYYY-MM-DD")
    ap.add_argument("--영업이익", type=float, default=None)
    a = ap.parse_args(argv)
    r = 회사세율(a.국가, a.기준일, a.영업이익) if a.영업이익 is not None else 공통세율(a.국가, a.기준일)
    print(json.dumps(r, ensure_ascii=False))
    return 0 if r.get("값") is not None else 2


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                # noqa: BLE001
        pass
    sys.exit(main())

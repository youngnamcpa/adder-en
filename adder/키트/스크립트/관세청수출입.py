# -*- coding: utf-8 -*-
"""관세청 수출입 — 품목(HS)별 월 수출 금액 · 중량으로 단가(P) · 물량(Q) 지수를 세우고 상태공간 복원과 대 본다 (제안 D-한국 · 2026-10-23 신설).

무엇을 하나
  관세청 수출입무역통계(tradedata.go.kr)의 「수출입 실적(품목별)」 화면이 쓰는 내부 요청(`/cts/hmpg/retrieveTrade.do` — 폼 인코딩 · 머리글 isAjax)은
  **회원가입 · 로그인 · 인증키 · 세션 없이** 받힌다(2026-10-23 실측 — 연도별 · 월별 · 품목 여럿 · 톤/kg). 공공데이터포털 키가 필요한 API 가 아니다.
  품목(HS 2 · 4 · 6 · 10단위)마다 월별 수출 **금액(천 달러) · 중량(톤)** 을 받아
      단가 지수 P = (금액 ÷ 중량) ÷ 첫 기간 값 × 100,   물량 지수 Q = 중량 ÷ 첫 기간 값 × 100
  을 월 · 연 단위로 낸다. 매출이 한 줄인 구분의 P · Q 를 재무제표 밖 제3자 집계로 세우는 **둘째 자**다(첫째 자는 상태공간 복원 — 기법 6).
  회사 밖 통계라 회사 매출을 대신하지 않는다 — 확인상태 「참고(공개 통계 — 관세청 수출입무역통계)」 · 매출 분해 규칙 「시장 규모는 출처별로 나란히」와 같은 자리.

한계(반드시 적는다)
  · 중량 단가는 **믹스**(같은 HS 안의 고가 · 저가 품목 비중)와 환율이 섞인 달러 단가다 — 회사의 판매단가가 아니다. 방향 · 변동의 자로 쓴다
  · HS 6단위는 국제 공통, 10단위는 한국 세번이다. HS 와 회사 매출 구분의 대응은 회차가 정하고 근거에 적는다(도구는 안 정한다 — 회사 이름이 없다)
  · 수출만 센다(국내 판매는 없다). 수출 비중이 작은 구분에는 자가 아니다

사용
  python 스크립트/관세청수출입.py 가정.json --hs 854232 [--hs 870323 …] [--부터 2015-01] [--구분 1] [--통계기준 acptDd|tkofDd] [--낼 _raw/수출입지수.json]
  python 스크립트/관세청수출입.py --hs 854232 --기준일 2026-06-30 [--작업 .]     # 조사 모드(가정 없음 — B1 공시 밖 관측치 · 상태공간 대조 없음)
  --까지 는 가정 메타.평가기준일의 달(기준일 뒤 통계는 쓰지 않는다). 받은 응답은 가정 곁 `_raw/수출입/{hs}_{부터}_{까지}.json` 에 캐시
내는 것 — {형식 · 만든날 · 입력 · 출처 · 확인상태 · 품목[{hs · 품목명 · 월[{연월 · 금액_천달러 · 중량_톤 · 단가_달러kg}] · 연[{연도 · 금액 · 중량 · 단가 · P지수 · Q지수 · 금액지수}] · 지수기준}] ·
          대조[{구분 · 연도 · 수출P변화 · 상태공간P변화 · 같은방향}] · 제안[] · 신호[]}
          신호: 「수출 P · Q 지수」(참고 · 품목마다) · 「수출 단가와 복원 단가의 방향이 갈림」(경보 — 상태공간.json 이 있을 때) · 「평가기준일 뒤 달은 뺐다」(참고)
종료 코드 — 0 통과(경보가 있어도) · 2 입력오류(HS 없음 · 응답 깨짐 · 품목이 하나도 안 옴).
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import re
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass
여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 입력오류  # noqa: E402

주소 = "https://tradedata.go.kr/cts/hmpg/retrieveTrade.do"
머리H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128", "Referer": "https://tradedata.go.kr/cts/index.do",
       "X-Requested-With": "XMLHttpRequest", "isAjax": "true", "Accept": "application/json, text/javascript, */*; q=0.01"}



def _평가기준일(가정):
    """메타 날짜를 `기준일.py` 로 푼다(날짜 둘 — 2026-10-25). 못 풀면 None."""
    try:
        import 기준일 as _B                                   # noqa: PLC0415
        return _B.평가기준일(가정).isoformat()
    except Exception:                                         # noqa: BLE001
        return None

def _수(s):
    s = ("%s" % (s or "")).strip().replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def hs단위(hs):
    n = len(hs)
    return {2: "HS2_SGN", 4: "HS4_SGN", 6: "HS6_SGN", 10: "HS10_SGN"}.get(n)


def _한번(hs목록, 부터, 까지, 통계기준, 단위):
    import requests                                      # noqa: PLC0415
    p = {"tradeKind": "ETS_MNK_1020000A", "priodKind": "MON", "priodFr": 부터.replace("-", ""), "priodTo": 까지.replace("-", ""), "statsBase": 통계기준,
         "ttwgTpcd": "1000", "showPagingLine": "100", "sortColumn": "", "sortOrder": "", "hsSgnGrpCol": 단위, "hsSgnWhrCol": 단위, "hsSgn": ",".join(hs목록)}
    for i in range(3):
        try:
            r = requests.post(주소, headers=머리H, data=p, timeout=120)
            if r.status_code == 200:
                j = r.json()
                if isinstance(j.get("items"), list) and not j.get("error"):
                    return j["items"]
        except Exception:                                # noqa: BLE001
            pass
        time.sleep(2.0 * (i + 1))
    return None


def 받기(hs목록, 부터, 까지, 통계기준="acptDd"):
    """월별 · 톤 · 품목 여럿 → 응답 items(총계 줄 포함). 세션 · 키 없음. **한 해씩 받는다** — 화면 응답이 목록 개수(최대 100줄)에 잘린다
    (2026-10-23 실측: 2015~2025 를 한 번에 청하니 99달에서 끊겼다). 해마다 품목 수 × 12 ≤ 100 이면 안전하다(품목 8개까지)."""
    단위 = {hs단위(h) for h in hs목록}
    if None in 단위 or len(단위) != 1:
        raise ValueError("HS 는 2 · 4 · 6 · 10자리이고 한 번에 같은 자릿수만 — %s" % hs목록)
    단 = 단위.pop()
    y0, y1 = int(부터[:4]), int(까지[:4])
    items = []
    for y in range(y0, y1 + 1):
        a = "%d%s" % (y, 부터[5:7] if y == y0 else "01")
        b = "%d%s" % (y, 까지[5:7] if y == y1 else "12")
        r = _한번(hs목록, a, b, 통계기준, 단)
        if r is None:
            return None
        items += [x for x in r if ("%s" % (x.get("priodTitle") or "")).strip() != "총계"]
        time.sleep(0.4)
    return items


def 품목묶기(items):
    """응답 items → {hs: {품목명, 월: [{연월 · 금액 · 중량 · 단가}]}} (총계 줄 제외 · 금액 천 달러 · 중량 톤 · 단가 달러/kg = 천달러 ÷ 톤)."""
    낸 = {}
    for x in items:
        hs = ("%s" % (x.get("hsSgn") or "")).strip()
        t = ("%s" % (x.get("priodTitle") or "")).strip()
        if not hs or not re.match(r"^\d{4}(\.\d{2})?$", t):
            continue
        금, 중 = _수(x.get("expUsdAmt")), _수(x.get("expTtwg"))
        d = 낸.setdefault(hs, {"hs": hs, "품목명": (x.get("korePrlstNm") or "").strip(), "월": []})
        d["월"].append({"연월": t, "금액_천달러": 금, "중량_톤": 중, "단가_달러kg": (금 / 중) if (금 is not None and 중) else None})
    for d in 낸.values():
        d["월"].sort(key=lambda m: m["연월"])
    return 낸


def 연집계(월들):
    해 = {}
    for m in 월들:
        y = m["연월"][:4]
        h = 해.setdefault(y, {"연도": int(y), "금액_천달러": 0.0, "중량_톤": 0.0, "달수": 0})
        if m["금액_천달러"] is not None:
            h["금액_천달러"] += m["금액_천달러"]
        if m["중량_톤"] is not None:
            h["중량_톤"] += m["중량_톤"]
        h["달수"] += 1
    낸 = []
    기준 = None
    for y in sorted(해):
        h = 해[y]
        h["단가_달러kg"] = (h["금액_천달러"] / h["중량_톤"]) if h["중량_톤"] else None
        if 기준 is None and h["달수"] == 12 and h["단가_달러kg"]:
            기준 = h
        낸.append(h)
    for h in 낸:
        h["P지수"] = round(h["단가_달러kg"] / 기준["단가_달러kg"] * 100, 2) if (기준 and h["단가_달러kg"]) else None
        h["Q지수"] = round(h["중량_톤"] / 기준["중량_톤"] * 100, 2) if (기준 and 기준["중량_톤"]) else None
        h["금액지수"] = round(h["금액_천달러"] / 기준["금액_천달러"] * 100, 2) if (기준 and 기준["금액_천달러"]) else None
        h["온전한해"] = h["달수"] == 12
    return 낸, (기준["연도"] if 기준 else None)


def 상태공간대조(가정경로, 구분, 연들):
    """`_raw/상태공간.json`(기법 6)의 그 구분 잠재단가지수(연간)와 연 변화 방향을 견준다. 없으면 []."""
    import 정상화                                         # noqa: PLC0415
    d, _p = 정상화.파일찾기("상태공간.json", 가정경로)
    if not isinstance(d, dict):
        return []
    목 = next((g for g in (d.get("구분") or []) if "%s" % g.get("번호") == "%s" % 구분 or g.get("매출구분") == 구분), None)
    if not 목:
        return []
    잠 = 목.get("잠재단가지수") or {}
    연값 = {}
    for k, v in 잠.items():
        m = re.match(r"(?:FY)?(\d{4})", "%s" % k)
        if m and isinstance(v, (int, float)):
            연값.setdefault(int(m.group(1)), []).append(v)
    연평 = {y: sum(v) / len(v) for y, v in 연값.items()}
    낸 = []
    온 = [h for h in 연들 if h.get("온전한해")]            # 기준일까지의 몇 달뿐인 해는 연 단가가 아니다 — 대조에서 뺀다
    for i in range(1, len(온)):
        a, b = 온[i - 1], 온[i]
        if not (a.get("P지수") and b.get("P지수") and a["연도"] in 연평 and b["연도"] in 연평):
            continue
        수 = b["P지수"] / a["P지수"] - 1
        복 = 연평[b["연도"]] / 연평[a["연도"]] - 1 if 연평[a["연도"]] else None
        if 복 is None:
            continue
        낸.append({"구분": 구분, "연도": b["연도"], "수출P변화": round(수, 4), "상태공간P변화": round(복, 4), "같은방향": (수 >= 0) == (복 >= 0)})
    return 낸


def 분석(가정, 가정경로, hs목록, 부터, 구분=None, 통계기준="acptDd", items=None):
    메타 = 가정.get("메타") or {}
    기준일 = _평가기준일(가정) or datetime.date.today().isoformat()       # 통계 경계 — 평가기준일(T · 2026-10-25 날짜 둘)
    까지 = 기준일[:7]
    신호, 제안 = [], []

    def 신(종류, 대상, 값, 문턱, 글, 등급="참고"):
        신호.append({"출처": "관세청수출입", "종류": 종류, "대상": 대상, "값": 값, "문턱": 문턱, "글": 글, "등급": 등급})

    곁 = os.path.dirname(os.path.abspath(가정경로))
    캐시 = os.path.join(곁, "_raw", "수출입", "%s_%s_%s.json" % ("_".join(hs목록), 부터.replace("-", ""), 까지.replace("-", "")))
    받음 = "인자"
    if items is None:
        if os.path.exists(캐시):
            items = json.load(io.open(캐시, encoding="utf-8"))
            받음 = "캐시"
        else:
            items = 받기(hs목록, 부터, 까지, 통계기준)
            if items is None:
                return None, "관세청 응답을 받지 못했다(%s)" % 주소
            os.makedirs(os.path.dirname(캐시), exist_ok=True)
            io.open(캐시, "w", encoding="utf-8").write(json.dumps(items, ensure_ascii=False))
            받음 = "받음"
    품목 = 품목묶기(items)
    if not 품목:
        return None, "품목 줄이 하나도 없다 — HS %s 가 맞는지 본다" % hs목록
    낸품 = []
    for hs in hs목록:
        d = 품목.get(hs)
        if not d:
            신("품목 없음", hs, None, None, "HS %s 의 줄이 응답에 없다(코드가 없거나 수출 실적 0)" % hs)
            continue
        연들, 기준연도 = 연집계(d["월"])
        d["연"] = 연들
        d["지수기준"] = "%s년 = 100(온전한 첫 해)" % 기준연도 if 기준연도 else "기준 해 없음(12달 온전한 해가 없다)"
        마지막 = [h for h in 연들 if h["온전한해"]]
        if len(마지막) >= 2:
            a, b = 마지막[-2], 마지막[-1]
            신("수출 P · Q 지수", "HS %s %s" % (hs, d["품목명"]), {"P": b["P지수"], "Q": b["Q지수"]}, None,
              "HS %s(%s) %d년 단가 지수 %s · 물량 지수 %s(%s). 전년 대비 단가 %+.1f%% · 중량 %+.1f%% — 재무제표 밖 제3자 집계라 회사 매출을 대신하지 않는다. "
              "중량 단가는 믹스 · 환율이 섞인 달러 단가다(방향 · 변동의 자)"
              % (hs, d["품목명"], b["연도"], b["P지수"], b["Q지수"], d["지수기준"], (b["단가_달러kg"] / a["단가_달러kg"] - 1) * 100 if a["단가_달러kg"] else 0.0,
                 (b["중량_톤"] / a["중량_톤"] - 1) * 100 if a["중량_톤"] else 0.0))
        if 구분 is not None:
            대 = 상태공간대조(가정경로, 구분, 연들)
            d["대조"] = 대
            갈 = [x for x in 대 if not x["같은방향"]]
            if 갈:
                신("수출 단가와 복원 단가의 방향이 갈림", "구분 %s · HS %s" % (구분, hs), len(갈), None,
                  "연 단가 변화의 부호가 %s 에서 갈린다(수출 %s · 복원 %s) — 어느 쪽이 맞는지 고르지 않는다. 믹스(HS 안 품목 구성) · 환율 · 회사 몫의 차이를 근거 칸에 적고 모순 장부에 올린다"
                  % (" · ".join(str(x["연도"]) for x in 갈), " · ".join("%+.1f%%" % (x["수출P변화"] * 100) for x in 갈), " · ".join("%+.1f%%" % (x["상태공간P변화"] * 100) for x in 갈)), "경보")
            if 연들 and 연들[-1].get("P지수"):
                제안.append({"자리": "매출 구분 %s 판매단가 · 판매량 지수(수출 통계 P · Q — 근사)" % 구분, "값": None, "근거범위": None,
                            "딱지": "[관측 — 관세청 수출입무역통계 HS %s · %s]" % (hs, d["지수기준"]), "확신": "약",
                            "글": "연도별 P 지수 %s · Q 지수 %s — 구분 %s 의 단가 · 물량 경로를 대 보는 둘째 자(상태공간이 첫째)" % (
                                [h["P지수"] for h in 연들 if h["온전한해"]], [h["Q지수"] for h in 연들 if h["온전한해"]], 구분)})
        낸품.append(d)
    if any(not h["온전한해"] for d in 낸품 for h in d["연"][-1:]):
        신("평가기준일까지만 셌다", 까지, None, None, "마지막 해는 기준일 %s 까지의 달만 모았다(온전한 해 아님) — 연 지수는 그 앞 해까지 읽는다" % 기준일)
    낸 = {"형식": "수출입지수 1", "만든날": datetime.date.today().isoformat(), "입력": {"가정": os.path.abspath(가정경로), "hs": hs목록, "구분": 구분, "기간": [부터, 까지], "통계기준": 통계기준, "받기": 받음, "캐시": 캐시},
         "출처": 주소 + " (관세청 수출입무역통계 「수출입 실적(품목별)」 — 세션 · 키 없음 · 월별 · 톤 · 천 달러)",
         "확인상태": "참고(공개 통계 — 관세청 수출입무역통계. 회사 값이 아니다 · 중량 단가는 믹스 · 환율 포함)", "품목": 낸품, "제안": 제안, "신호": 신호}
    return 낸, ""


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="관세청 품목별 월 수출 금액 · 중량 → P · Q 지수(상태공간과 대조)")
    ap.add_argument("가정", nargs="?", help="가정 파일(없으면 조사 모드 — `--기준일` · `--작업` 으로 · 2026-10-24 W16)")
    ap.add_argument("--hs", action="append", required=True, help="HS 코드(2 · 4 · 6 · 10자리 — 여러 번)")
    ap.add_argument("--기준일", default=None, help="조사 모드(가정 없음)의 평가기준일 YYYY-MM-DD — 그 달까지만 쓴다")
    ap.add_argument("--작업", default=None, help="조사 모드의 작업 폴더(캐시 `_raw/수출입/` · 산출 `_raw/수출입지수.json` 자리 — 기본 지금 폴더)")
    ap.add_argument("--부터", default="2015-01", help="YYYY-MM")
    ap.add_argument("--구분", help="대 볼 매출 구분 번호(상태공간.json 대조)")
    ap.add_argument("--통계기준", default="acptDd", help="acptDd 수리일 · tkofDd 출항일")
    ap.add_argument("--낼")
    a = ap.parse_args()
    if not a.가정:
        # 2026-10-24 W16 — 조사 단계(가정 전 · B1 공시 밖 관측치)에서도 돈다(유니버스 조사 물결 실측).
        # 상태공간 대조(--구분)는 가정이 있을 때만이다
        if not a.기준일:
            print("입력오류 — 가정 없이 돌리려면 --기준일 YYYY-MM-DD 를 준다")
            return 입력오류
        if a.구분:
            print("  알림 — 가정 없이는 상태공간 대조(--구분)를 하지 않는다")
            a.구분 = None
        가정 = {"메타": {"평가기준일": a.기준일}}
        a.가정 = os.path.join(os.path.abspath(a.작업 or os.getcwd()), "_조사모드_가정없음.json")
    else:
        try:
            가정 = json.load(io.open(a.가정, encoding="utf-8"))
        except (OSError, ValueError) as e:
            print("가정 파일을 못 읽었다 — %s" % e)
            return 입력오류
    try:
        낸, 까 = 분석(가정, a.가정, [h.strip() for h in a.hs], a.부터, a.구분, a.통계기준)
    except ValueError as e:
        print("입력오류 — %s" % e)
        return 입력오류
    if 낸 is None:
        print("입력오류 — %s" % 까)
        return 입력오류
    p = a.낼 or os.path.join(os.path.dirname(os.path.abspath(a.가정)), "_raw", "수출입지수.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, "w", encoding="utf-8").write(json.dumps(낸, ensure_ascii=False, indent=1, default=str))
    for d in 낸["품목"]:
        print("HS %s %s — 월 %d · %s" % (d["hs"], d["품목명"], len(d["월"]), d["지수기준"]))
        for h in d["연"]:
            print("   %d%s 금액 %12s 천달러 · 중량 %10s 톤 · 단가 %7s $/kg · P %6s · Q %6s" % (h["연도"], "" if h["온전한해"] else "(%d달)" % h["달수"], "{:,.0f}".format(h["금액_천달러"]),
                                                                                       "{:,.1f}".format(h["중량_톤"]), ("%.2f" % h["단가_달러kg"]) if h["단가_달러kg"] else "-", h["P지수"], h["Q지수"]))
    for s in 낸["신호"]:
        print("   · [%s] %s — %s: %s" % (s["등급"], s["종류"], s["대상"], s["글"][:150]))
    print("→ %s" % p)
    return 통과


if __name__ == "__main__":
    sys.exit(main())

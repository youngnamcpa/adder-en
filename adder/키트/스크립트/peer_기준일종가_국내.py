# -*- coding: utf-8 -*-
"""평가기준일 국내 종가 — peer_기준일종가.py 가 해외 창구(chart/foreign)만 쓰는 탓에
국내 6자리 코드가 전부 'reutersCode 확인 불가'로 떨어진다(실측 21/21).
국내는 api.finance.naver.com/siseJson.naver 기간 지정 창구를 쓴다.

산출: _raw/peers/종가_{기준일}.json  = {종목코드: 종가(float)}
      _raw/peers/종가상세_{기준일}.json = {종목코드: {종가·일자·일치}}
peer_조립.py 가 종가를 float 로 곱하므로 평평한 쪽을 본파일로 낸다.
"""
from __future__ import annotations
import argparse, io, json, os, sys, time, ast
import requests

sys.stdout.reconfigure(encoding="utf-8")
# 2026-10-25 FX4-P — DCF_RUN_ROOT(사슬 `--폴더` 가 넘긴다)면 그 회차에 쓴다 — 본체 경로로 돌려도 본체 _raw 에 쌓지 않게
ROOT = os.environ.get("DCF_RUN_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEER = os.path.join(ROOT, "_raw", "peers")
H = {"User-Agent": "Mozilla/5.0"}
URL = ("https://api.finance.naver.com/siseJson.naver?symbol=%s&requestType=1"
       "&startTime=%s&endTime=%s&timeframe=day")


def 일봉(code, 부터, 까지):
    # **캐시 폴더가 없으면 저장이 죽고, except 가 그것을 「조회 실패」로 위장한다.**
    # 실측(두산에너빌리티): 응답은 정상인데 세 번 다 FileNotFoundError 로 실패했다.
    os.makedirs(PEER, exist_ok=True)
    p = os.path.join(PEER, "day_%s_%s_%s.json" % (code, 부터, 까지))
    if os.path.exists(p):
        return json.load(io.open(p, encoding="utf-8")), "캐시"
    for i in range(3):
        try:
            t = requests.get(URL % (code, 부터, 까지), headers=H, timeout=40).text.strip()
            arr = ast.literal_eval(t.replace("\n", " "))
            rows = [(str(r[0]), float(r[4])) for r in arr[1:]]
            if rows:
                json.dump(rows, io.open(p, "w", encoding="utf-8"))
                time.sleep(0.25)
                return rows, "신규"
        except Exception:
            pass
        time.sleep(1.2 * (i + 1))
    return None, "조회 실패"


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--기준일", "--평가기준일", dest="기준일", default="20260630", help="평가기준일 T(분석일 · 시장 쪽 — 종가 · 시가총액 · 주식수 · 베타 창 끝 · 환율 · 법령 시행일) YYYY-MM-DD")
    ap.add_argument("--명단", default="1차통과.json")
    ap.add_argument("--추가", default="", help="명단 밖 종목코드(쉼표 구분)")
    a = ap.parse_args()
    # 기준일을 「20260630」 꼴로 정규화한다 — 대시 형식이 그대로 네이버 API 의
    # 종료일 파라미터에 들어가면 조용히 무시되어 창구가 전년 말에서 끊긴다
    # (실측: 3곳 모두 2025-12-30 「직전 거래일」로 위장 — 6개월 낡은 종가).
    a.기준일 = a.기준일.replace("-", "")
    # **명단이 없어도 돈다.** 대상회사 종가(원천 99행)는 유사기업 갈래와 무관하게
    # 늘 필요하다 — peer_기준일종가.py(미국판)와 같은 결함이 여기에도 있었다.
    import 피어경로 as _pp                              # 2026-10-24 W16 — 「_raw/peers/x.json」 을 PEER 에 겹쳐 붙여 동종 종가를 안 받던 결함(유니버스 조사 물결 실측)
    명단길 = _pp.명단경로(a.명단, PEER, ROOT) if a.명단 else ""
    티커 = []
    if 명단길 and os.path.exists(명단길):
        명 = json.load(io.open(명단길, encoding="utf-8"))
        if isinstance(명, dict):                         # C1 핵심표본 꼴도 받는다(국내 줄만)
            import 핵심표본읽기 as _hr
            명 = _hr.명단(명, ("핵심", "예비", "운영동종전용", "컷통과"), "KR")
        티커 = [d.get("종목코드") or d.get("티커") for d in 명 if isinstance(d, dict)]
        티커 = [t for t in 티커 if t]
    else:
        print("명단 %s 이 없습니다 — `--추가` 로 준 종목만 받습니다" % a.명단)
    티커 += [x.strip() for x in a.추가.split(",") if x.strip()]
    if not 티커:
        raise SystemExit("받을 종목이 없습니다 — `--추가 011200` 처럼 지정하십시오")
    부터 = "%s0101" % (int(a.기준일[:4]) - 1)
    평, 상세, 실패, 캐, 신 = {}, {}, [], 0, 0
    for t in 티커:
        rows, how = 일봉(t, 부터, a.기준일)
        if rows is None:
            실패.append((t, how)); print("%-7s *** 실패: %s — 조용히 빼지 않는다" % (t, how)); continue
        캐, 신 = (캐 + 1, 신) if how == "캐시" else (캐, 신 + 1)
        정 = [x for x in rows if x[0] == a.기준일]
        앞 = [x for x in rows if x[0] <= a.기준일]
        if 정:   v, d, ok = 정[0][1], a.기준일, True
        elif 앞: v, d, ok = 앞[-1][1], 앞[-1][0], False
        else:
            실패.append((t, "일봉이 평가기준일에 못 닿음")); continue
        평[t] = v
        상세[t] = {"종가": v, "일자": d, "일치": ok}
        print("%-7s %10.1f (%s%s) [%s]" % (t, v, d, "" if ok else " ← 직전 거래일", how))
    os.makedirs(PEER, exist_ok=True)   # 실측(알테오젠): 폴더가 없어 조회 뒤 저장에서 죽었다
    # 2026-10-24 W18 — 기존 파일에 **병합**한다(미국 사슬 `peer_기준일종가.py` 와 같은 규칙). 국내 사슬이 새로 써 미국 사슬이 받아 둔 티커 종가를
    # 지우던 결함(유니버스 조사 — 국내 · 미국 두 사슬을 한 회차에서 돌리면 서로 덮었다)
    def _합쳐(이름, 새것):
        p = os.path.join(PEER, 이름)
        옛 = {}
        if os.path.exists(p):
            try:
                옛 = json.load(io.open(p, encoding="utf-8")) or {}
            except (OSError, ValueError):
                옛 = {}
        옛.update(새것)
        json.dump(옛, io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    _합쳐("종가_%s.json" % a.기준일, 평)
    _합쳐("종가상세_%s.json" % a.기준일, 상세)
    print("\n캐시 %d · 신규 %d · 실패 %d" % (캐, 신, len(실패)))
    for t, w in 실패:
        print("  실패 %s: %s" % (t, w))


if __name__ == "__main__":
    main()

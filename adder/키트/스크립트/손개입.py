# -*- coding: utf-8 -*-
"""손개입 — 회차 산출에서 「사람 손이 간 자리」를 한 자로 센다(손개입 개선 1 · S10R2-N6-g · 2026-10-18).

왜 있나 — S10 리뷰가 회사마다 손 개입을 「NAVER 넷 · BGF 일곱 · 펄어비스 둘」로 적었는데 셈의 자가 달랐다(재리뷰 2 4절 8). 보고서 숫자가 아니라
가정 파일과 갈래 산출물(`_raw/`)에서 **기계가 같은 자로 재는 측정값**이어야 전후를 견줄 수 있다. 회사 · 업종 이름은 없다.

    python 스크립트/손개입.py 가정.json              # 한 회차 — 표와 수 · _raw/손개입.json
    python 스크립트/손개입.py 가정.json --json        # JSON 만
    python 스크립트/손개입.py --여럿 가정1.json 가정2.json …   # 여러 회차를 한 표로(전후 비교)

자(셋)
  ① 도구 틈 — 13번 원천 칸 가운데 값이 있는데 도구 산출에서 오지 않은 **번호**의 수. 번호마다 실적 열 값을 A2(`_raw/원천_조립*.json` — 기준일이 같은 파일 ·
     ÷ 환산배율) · A3(`동인원천.json` 원천행) · A1 주식수(`주식수.csv`) · 공시채움(`공시채움.json` 기록 · 원천근거의 「공시채움.py」) 과 맞춘다. 어느 도구 값과도
     같지 않은 열이 하나라도 있으면 그 번호는 「손」이다. 근거 첫 칸이 `[기본값]` 이면 손이 아니라 ③ 판단 자리(기본값)로 센다. 종가 99 · 표 구획(581~596 기준기간)
     · 값이 0 · null 뿐인 번호는 세지 않는다(0 뿐이면 「빈칸 0」 목록에만)
  ② 공시에 없음 — 원천근거 · 근거 셋째 칸에 「공시에 없 · 미공시 · 확인 불가 · 반기 … 없」가 적힌 번호(도구 틈에서 뺀다 — 도구가 못 채우는 것이 아니라 공시가 없는 것)
  ③ 판단 자리 — 넘긴 몫 장부(`넘긴몫.모으기` — 자체검사 빼고)의 미결 가운데 「기본값 확인 대기 · 기본값 의심 · 멈춤 문항 · 성격 확정 대기」를 **묶음**으로 센다.
     묶음은 가정 번호의 블록(매출 30~75 · 원가율 80~130 · 보조 7xx · 인건비 13x · 50x · 투자 14x~17x · 85x~86x · 운전자본 17x~19x · 법인세 19x~20x ·
     시점가정 212~220 · 저량 55x~61x · WACC · 원천 번호별)이고, 멈춤 문항은 문항마다 하나다. 칸 수도 함께 낸다
손 개입 수 = ① 도구 틈(번호) + ③ 판단 자리(묶음). ② 는 따로 적는다(도구의 몫이 아니다).
종료 코드 — 0(쟀다) · 2(입력 오류)
"""
import argparse
import csv
import glob
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
from 종료코드 import 통과, 입력오류                      # noqa: E402

안세는원천 = {"99", "100"}                                  # 종가 · 시가총액(관측 · 수식)
표구획 = set("%d" % n for n in range(581, 597))
없음말 = re.compile(r"공시에\s*없|미공시|확인\s*불가|보고서에\s*없|주석\s*미확인|없음")
기본값딱지 = re.compile(r"^\s*\[기본값\]|\[판단\]\s*기본값")
판단딱지 = re.compile(r"^\s*\[판단\]")                               # 원천 칸에 사람이 [판단] 으로 적은 값(설정 덮기 · 반기 미공시 저량) — 도구 틈이 아니라 판단 자리


def _수(x):
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def _읽기(p):
    try:
        return json.load(io.open(p, encoding="utf-8"))
    except (OSError, ValueError):
        return None


def 묶음(키):
    k = "%s" % 키
    if not k.isdigit():
        return "WACC" if k in ("국채수익률", "부도스프레드", "성숙시장프리미엄", "국가위험프리미엄", "베타u", "현금비중", "한계세율", "스프레드", "규모프리미엄") else k.split(".")[0]
    n = int(k)
    for lo, hi, 이름 in ((30, 75, "매출"), (80, 130, "원가율"), (134, 142, "인건비 배분"), (148, 172, "투자"), (178, 190, "운전자본"), (196, 208, "법인세"),
                       (212, 220, "시점가정"), (249, 250, "연장"), (395, 420, "한시"), (501, 512, "인건비"), (550, 620, "저량 · 판매량"), (700, 799, "원가 줄 보조"),
                       (800, 869, "투자"), (900, 960, "그 밖")):
        if lo <= n <= hi:
            return 이름
    return "그 밖"


def 도구값들(가정, 가정경로):
    """번호 → {열: {도구 값들}} — A2(기준일 같은 파일) · A3 원천행 · 주식수.csv · 공시채움 기록."""
    폴더 = os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw")
    배 = _수((가정.get("메타") or {}).get("환산배율")) or 1.0
    import 공시채움 as 채                                      # noqa: PLC0415
    낸, 출처 = {}, {}

    def 넣기(번호, 열, 값, 누구):
        낸.setdefault("%s" % 번호, {}).setdefault(열, set()).add(round(값, 6))
        출처.setdefault("%s" % 번호, set()).add(누구)
    try:
        실, 누, 열들 = 채.실적열들(가정)
        a2, 대응, _건 = 채.A2읽기(가정, 가정경로, 폴더)
    except Exception:                                       # noqa: BLE001
        실, 누, a2, 대응 = [], None, None, {}
    if a2:
        for 번호, v in (a2.get("원천") or {}).items():
            for 열, i in 대응.items():
                if isinstance(v, list) and i < len(v) and _수(v[i]) is not None:
                    넣기(번호, 열, _수(v[i]) / 배, "A2")
        for 번호, v in (a2.get("검산행") or {}).items():
            for 열, i in 대응.items():
                if isinstance(v, list) and i < len(v) and _수(v[i]) is not None:
                    넣기(번호, 열, _수(v[i]) / 배, "A2")
    a3 = _읽기(os.path.join(폴더, "동인원천.json"))
    for 번호, d in (((a3 or {}).get("원천행") or {}) if isinstance(a3, dict) else {}).items():
        for 열, x in (d or {}).items():
            if _수(x) is not None:
                넣기(번호, 열, _수(x), "A3")
    주 = os.path.join(폴더, "주식수.csv")
    if os.path.exists(주):
        try:
            for r in csv.DictReader(io.open(주, encoding="utf-8-sig")):
                for 번호, 칸 in (("95", "발행주식총수"), ("96", "자기주식수"), ("97", "유통주식수")):
                    if _수(float(r.get(칸) or "nan")) is not None:
                        for 열 in 실:
                            넣기(번호, 열, float(r[칸]), "A1 주식수")
        except Exception:                                   # noqa: BLE001
            pass
    기록 = _읽기(os.path.join(폴더, "공시채움.json"))
    for x in (((기록 or {}).get("채움") or []) if isinstance(기록, dict) else []):
        if x.get("칸", "").startswith("원천") and _수(x.get("값")) is not None:
            넣기(x["번호"], x["열"], _수(x["값"]), "공시채움")
    return 낸, 출처, 실


def 같다(a, b):
    return abs(a - b) <= max(1e-6, abs(b) * 1e-6)


def 재기(가정, 가정경로):
    원 = 가정.get("원천") or {}
    근 = 가정.get("원천근거") or {}
    도구, 누구, 실 = 도구값들(가정, 가정경로)
    손, 도구줄, 기본값줄, 없음줄, 빈칸0 = [], [], [], [], []
    for 번호 in sorted(원, key=lambda k: int(k) if k.isdigit() else 9999):
        if 번호 in 안세는원천 or 번호 in 표구획:
            continue
        d = 원.get(번호)
        if not isinstance(d, dict):
            continue
        값들 = {c: _수(v) for c, v in d.items() if c != "기준기간" and _수(v) is not None}
        if not 값들:
            continue
        if all(v == 0.0 for v in 값들.values()):
            빈칸0.append(번호)
            continue
        근거 = 근.get(번호) if isinstance(근.get(번호), list) else []
        첫 = "%s" % (근거[0] if 근거 else "")
        셋째 = "%s" % (근거[2] if len(근거) > 2 else "")
        if 기본값딱지.search(첫) or 판단딱지.search(첫):
            기본값줄.append(번호)
            continue
        if "공시채움.py" in 첫:
            도구줄.append((번호, "공시채움"))
            continue
        안맞음 = []
        for c, v in 값들.items():
            if v == 0.0:
                continue
            후보 = (도구.get(번호) or {}).get(c) or set()
            if not any(같다(v, x) for x in 후보):
                안맞음.append(c)
        if not 안맞음:
            도구줄.append((번호, " · ".join(sorted(누구.get(번호) or {"도구"}))))
        elif 없음말.search(셋째) or 없음말.search(첫):
            없음줄.append((번호, 안맞음, 첫[:60]))
        else:
            손.append((번호, 안맞음, 첫[:60]))
    # ③ 판단 자리 — 넘긴 몫 장부
    import 넘긴몫 as 넘                                     # noqa: PLC0415
    try:
        줄 = 넘.모으기(가정, 가정경로, 자체검사포함=False)
    except Exception as e:                                   # noqa: BLE001
        줄 = []
        장부오류 = "%s: %s" % (type(e).__name__, e)
    else:
        장부오류 = None
    판단칸, 판단묶음, 문항 = [], {}, []
    for r in 줄:
        if r.get("상태") != "미결":
            continue
        종 = r.get("종류") or ""
        if 종 in ("기본값 확인 대기", "기본값 의심"):
            번 = "%s" % (r.get("번호") or "")
            판단칸.append((번, 종))
            m = 묶음(번) if 번 else "그 밖"
            if 번.isdigit() and int(번) < 100 and "원천" in ("%s" % r.get("출처")):
                m = "원천 %s" % 번
            판단묶음.setdefault(m, []).append(번)
        elif 종 in ("멈춤 문항", "성격 확정 대기", "지도 없음"):
            문항.append((종, "%s" % (r.get("글") or "")[:70]))
    for 번호 in 기본값줄:
        판단묶음.setdefault("원천 %s" % 번호, []).append(번호)
    낸 = {"가정": os.path.basename(가정경로), "회사": (가정.get("메타") or {}).get("회사명"),
         "도구틈": [{"번호": n, "열": c, "근거": g} for n, c, g in 손],
         "공시에없음": [{"번호": n, "열": c, "근거": g} for n, c, g in 없음줄],
         "도구": [{"번호": n, "누구": w} for n, w in 도구줄], "기본값원천": 기본값줄, "빈칸0": 빈칸0,
         "판단묶음": {k: sorted(set(v)) for k, v in 판단묶음.items()}, "판단칸수": len(판단칸) + len(기본값줄),
         "문항": [{"종류": s, "글": g} for s, g in 문항], "장부오류": 장부오류,
         "수": {"도구틈": len(손), "공시에없음": len(없음줄), "판단묶음": len(판단묶음) + len(문항), "판단칸": len(판단칸) + len(기본값줄),
              "손개입": len(손) + len(판단묶음) + len(문항)}}
    return 낸


def 글(낸):
    s = 낸["수"]
    줄 = ["%s(%s) — 손 개입 %d = 도구 틈 %d + 판단 자리 %d묶음(%d칸) · 공시에 없음 %d" % (
        낸["가정"], 낸.get("회사") or "-", s["손개입"], s["도구틈"], s["판단묶음"], s["판단칸"], s["공시에없음"])]
    for x in 낸["도구틈"]:
        줄.append("  도구 틈  원천 %s(%s) — %s" % (x["번호"], " · ".join(x["열"]), x["근거"]))
    for x in 낸["공시에없음"]:
        줄.append("  공시에 없음  원천 %s(%s) — %s" % (x["번호"], " · ".join(x["열"]), x["근거"]))
    for k, v in sorted(낸["판단묶음"].items()):
        줄.append("  판단 자리  %s — %s" % (k, " · ".join(v[:12]) + (" …" if len(v) > 12 else "")))
    for x in 낸["문항"]:
        줄.append("  판단 자리  %s — %s" % (x["종류"], x["글"]))
    if 낸["빈칸0"]:
        줄.append("  빈칸 0(세지 않음) — %s" % " · ".join(낸["빈칸0"]))
    줄.append("  도구가 채운 원천 %d개 — %s" % (len(낸["도구"]), " · ".join("%s(%s)" % (x["번호"], x["누구"]) for x in 낸["도구"][:40]) + (" …" if len(낸["도구"]) > 40 else "")))
    if 낸.get("장부오류"):
        줄.append("  넘긴 몫 장부를 못 읽었다 — %s" % 낸["장부오류"])
    return "\n".join(줄)


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="손 개입의 자(손개입 개선 1)")
    ap.add_argument("가정", nargs="?")
    ap.add_argument("--여럿", nargs="*", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    목록 = a.여럿 or ([a.가정] if a.가정 else [])
    if not 목록:
        sys.stderr.write("가정 파일을 주십시오\n")
        return 입력오류
    낸들 = []
    for p in 목록:
        g = _읽기(p)
        if not isinstance(g, dict):
            sys.stderr.write("못 읽음 — %s\n" % p)
            return 입력오류
        낸 = 재기(g, p)
        낸들.append(낸)
        if a.json:
            print(json.dumps(낸, ensure_ascii=False, indent=1))
        else:
            print(글(낸))
        if not a.여럿:
            폴더 = os.path.join(os.path.dirname(os.path.abspath(p)), "_raw")
            if os.path.isdir(폴더):
                io.open(os.path.join(폴더, "손개입.json"), "w", encoding="utf-8").write(json.dumps(낸, ensure_ascii=False, indent=1))
    if a.여럿 and not a.json:
        print()
        print("| 가정 | 손 개입 | 도구 틈 | 판단 자리(묶음) | 판단 칸 | 공시에 없음 |")
        print("|---|---|---|---|---|---|")
        for 낸 in 낸들:
            s = 낸["수"]
            print("| %s | %d | %d | %d | %d | %d |" % (낸["가정"], s["손개입"], s["도구틈"], s["판단묶음"], s["판단칸"], s["공시에없음"]))
    return 통과


if __name__ == "__main__":
    sys.exit(main())

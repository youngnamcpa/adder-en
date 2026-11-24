# -*- coding: utf-8 -*-
"""구분가르기 — 수준 경로의 매출 구분 하나를 「합계 경로(상위) + 하위 구분」으로 가른다 — 중립 분할(값 그대로). (R1a K1 · K2 — 이전 도구)

  python 스크립트/구분가르기.py <가정.json> --상위 1 --하위 "범용 DRAM:3" "HBM:4" --몫 0.18 --배분 0.25 --낼 <새.json>

  상위    가를 구분(수준 경로 · 1~5). 그 구분이 합계 경로가 되고 실적(13번 86~90 · 58s 기준 기간)은 그대로 상위에 남는다
  하위    「이름:번호」 둘 이상 — 첫째가 나머지 몫(라인을 가진다), 둘째부터 몫 · 배분을 받는다. 번호는 상위보다 크고 비어 있어야 한다
  몫      둘째부터의 기준 배분(기준 기간 매출 중 몫 — A-53s)
  배분    둘째부터의 웨이퍼 배분(판매량산정 = 능력이면 모든 라인 · 모든 열에 같은 배분율 A-(1000 + 100s + j) · 직접이면 판매량의 몫)
중립 분할 = 배분이 일률이고 하위 구분의 판매단가 지수 · 정상 수준이 상위의 것에 비례(몫 ÷ 배분)하고 변동률 · 유지 · 도달 · 조정 계수 ·
단위 산출량 · 가동률 · 수율이 같다 — 세 시나리오 주당가치가 가르기 전과 1e-9 안에서 같다(모델링/S1_매출스트림_설계.md S1-1). 원가 ·
인원 가중은 웨이퍼 몫으로 나눈다(원가는 웨이퍼를 따른다). 가른 뒤 하위 구분의 단가 경로(연동 · 배율 · 시차)와 배분율의 시간 경로를
고쳐 쓴다. 민감도 · 역산의 대상에 적힌 상위의 번호(6p6 따위)는 하위 구분의 번호로 바꾼다. 다 하면 세 시나리오 값을 맞대어 보이고,
1e-9 를 넘으면 쓰지 않는다(rc 1).
"""
import argparse
import copy
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 엔진.계산 import 계산  # noqa: E402

시나 = ("비관", "기준", "낙관")


def _곱(벌, f):
    벌 = copy.deepcopy(벌)
    if isinstance(벌, dict):
        for k, v in 벌.items():
            if isinstance(v, dict):
                for c in v:
                    if isinstance(v[c], (int, float)) and not isinstance(v[c], bool):
                        v[c] = v[c] * f
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                벌[k] = v * f
    elif isinstance(벌, (int, float)) and not isinstance(벌, bool):
        벌 = 벌 * f
    return 벌


def 가르기(g0, p, 하위, 몫들, 배분들):
    """하위 = [(이름, 번호) …](첫째 = 나머지 몫), 몫들 · 배분들 = 둘째부터. → 새 가정."""
    g = copy.deepcopy(g0)
    A, S, T, H = g["가정"], g.setdefault("시점가정", {}), g.setdefault("표", {}), g.setdefault("원천", {})
    근 = g.setdefault("근거", {})
    구분들 = g["구조"]["매출구분"]
    위 = next(x for x in 구분들 if x["번호"] == p)
    if 위.get("경로") != "수준" or p >= 6:
        raise SystemExit("상위 %d 이 수준 경로(1~5)가 아니다" % p)
    번호들 = [c for _, c in 하위]
    if any(c <= p or c >= 6 or any(x["번호"] == c for x in 구분들) for c in 번호들):
        raise SystemExit("하위 번호 %s — 상위보다 크고(1~5) 비어 있어야 한다" % 번호들)
    if len(몫들) != len(하위) - 1 or len(배분들) != len(하위) - 1:
        raise SystemExit("몫 · 배분은 둘째 하위부터 하나씩(%d개) 적는다" % (len(하위) - 1))
    몫 = [1.0 - sum(몫들)] + list(몫들)
    배 = [1.0 - sum(배분들)] + list(배분들)
    표 = T.get(str(600 + 10 * p + 7)) or {}
    능력 = 위.get("판매량산정") == "능력"
    공시 = 위.get("판매량공시") == "예"                     # 하위 구분은 실적 열이 없다 — 판매량공시 = 아니오(기준 기간 판매량을 표 T1 에)
    if 공시:
        from 기간축 import 기간축
        축 = 기간축(g)
        기준일 = 축.ID[축.기준일]
        개월 = ((H.get("594") or {}).get("기준기간")) or 12
        기준판매량 = ((H.get(str(586 + p)) or {}).get("기준기간") or 0.0) * 12.0 / 개월
        기말판매량 = (H.get(str(555 + p)) or {}).get(기준일)
    # 구조 — 상위는 합계, 첫 하위가 라인을 가진다, 둘째부터 배분라인
    새 = []
    for k, (이름, c) in enumerate(하위):
        x = copy.deepcopy(위)
        x.update({"번호": c, "이름": 이름, "상위": p})
        if 공시:
            x["판매량공시"] = "아니오"
        if k > 0:
            x["라인"] = []
            if 능력:
                x["배분라인"] = [{"번호": j["번호"]} for j in 위.get("라인") or []]
        새.append(x)
    g["구조"]["매출구분"] = sorted([x for x in 구분들 if x["번호"] != p]
                             + [{"번호": p, "이름": 위.get("이름"), "경로": "합계", "기준기간": 위.get("기준기간")}] + 새, key=lambda x: x["번호"])
    b, bs = 600 + 10 * p, {c: 600 + 10 * c for c in 번호들}
    # 판매단가 지수 · 정상 수준은 몫 ÷ 배분에 비례 — 나머지는 그대로
    for k, c in enumerate(번호들):
        r = 몫[k] / 배[k]
        t = dict(copy.deepcopy(표))
        if 공시:
            t["판매량"] = 기준판매량
        if "판매량" in t:
            t["판매량"] = t["판매량"] * 배[k]
        if "판매단가지수" in t:
            t["판매단가지수"] = t["판매단가지수"] * r
        for 가중 in ("원가가중", "인원가중"):
            if 가중 in t:
                t[가중] = t[가중] * 배[k]
        T[str(bs[c] + 7)] = t
        for d in (0, 1):                                  # 직접 — 판매량(기간 평균 · 기말)의 몫
            if str(b + d) in A:
                A[str(bs[c] + d)] = _곱(A[str(b + d)], 배[k])
        if 공시 and not 능력 and 기말판매량 is not None:      # 공시 판매량이던 구분 — 평가기준일 열의 기말 판매량(실적)의 몫
            벌 = A.setdefault(str(bs[c] + 1), {})
            for 시, v in list(벌.items()) or [("공통", {})]:
                벌.setdefault(시, {})
                벌[시][기준일] = 기말판매량 * 배[k]
        for d in (3, 4):
            if str(b + d) in A:
                A[str(bs[c] + d)] = copy.deepcopy(A[str(b + d)])
        for d in (2, 8, 9):
            if str(b + d) in S:
                S[str(bs[c] + d)] = copy.deepcopy(S[str(b + d)])
        if str(b + 6) in S:
            S[str(bs[c] + 6)] = _곱(S[str(b + 6)], r)
        for 옛 in (273, 277, 281, 285):                 # 가동률 · 수율 · (시장 규모 · 점유율 — 점유율대조)
            if str(옛 + 25 * (p - 1)) in A:
                A[str(옛 + 25 * (c - 1))] = copy.deepcopy(A[str(옛 + 25 * (p - 1))])
        if k > 0:
            S[str(530 + c)] = 몫[k]
            if 능력:
                for j in 위.get("라인") or []:
                    기준일 = next((cc for v in (A.get(str(669 + 2 * j["번호"])) or {}).values() if isinstance(v, dict) for cc in v if cc.endswith("A")), None)
                    열 = sorted({cc for v in (A.get(str(668 + 2 * j["번호"])) or {}).values() if isinstance(v, dict) for cc in v})
                    벌 = {cc: 배[k] for cc in 열}
                    if 기준일:
                        벌[기준일] = 배[k]
                    A[str(1000 + 100 * c + j["번호"])] = {"공통": 벌}
        for 키 in list(근):
            if 키.isdigit() and len(키) == 3 and 키.startswith("6%d" % p):
                근.setdefault("6%d%s" % (c, 키[2]), 근[키])
    # 상위의 수준 경로 값은 걷는다(합계 경로는 그 줄이 없다)
    for d in (0, 1, 3, 4):
        A.pop(str(b + d), None)
    for d in (2, 6, 8, 9):
        S.pop(str(b + d), None)
    T.pop(str(b + 7), None)
    for 옛 in (273, 277, 281, 285):
        A.pop(str(옛 + 25 * (p - 1)), None)
    for 키 in [k for k in 근 if k.isdigit() and len(k) == 3 and k.startswith("6%d" % p)]:
        근.pop(키)
    # 민감도 · 역산의 대상 — 상위의 번호를 하위의 번호로
    def 옮김(대상):
        낸 = []
        for x in 대상:
            x = "%s" % x
            if len(x) == 3 and x.startswith("6%d" % p) and x[2] in "0123456789":
                낸 += ["6%d%s" % (c, x[2]) for c in 번호들]
            else:
                낸.append(x)
        return 낸
    for h in ((g.get("민감도") or {}).get("손잡이") or []):
        if "대상" in h:
            h["대상"] = 옮김(h["대상"])
    for 축 in ("세로", "가로"):
        d = ((g.get("민감도") or {}).get("표2") or {}).get(축)
        if isinstance(d, dict) and "대상" in d:
            d["대상"] = 옮김(d["대상"])
    축 = (g.get("역산") or {}).get("축")
    if isinstance(축, dict) and "대상" in 축:
        축["대상"] = 옮김(축["대상"])
    return g


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="매출 구분 가르기 — 중립 분할")
    ap.add_argument("가정")
    ap.add_argument("--상위", type=int, required=True)
    ap.add_argument("--하위", nargs="+", required=True, help="이름:번호 …(첫째 = 나머지 몫)")
    ap.add_argument("--몫", nargs="*", type=float, default=[])
    ap.add_argument("--배분", nargs="*", type=float, default=[])
    ap.add_argument("--낼", required=True)
    a = ap.parse_args(argv)
    with io.open(a.가정, encoding="utf-8") as f:
        g0 = json.load(f)
    하위 = [(x.rsplit(":", 1)[0], int(x.rsplit(":", 1)[1])) for x in a.하위]
    g = 가르기(g0, a.상위, 하위, a.몫, a.배분)
    나쁨 = 0
    for s in 시나:
        v0, v1 = 계산(g0, s)["요약"]["주당가치"], 계산(g, s)["요약"]["주당가치"]
        d = abs(v1 - v0) / max(1.0, abs(v0))
        나쁨 += d > 1e-9
        print("%s 가르기 전 %.6f · 뒤 %.6f · 상대차 %.1e" % (s, v0, v1, d))
    if 나쁨:
        print("중립 분할이 값을 바꿨다 — 쓰지 않는다(가정의 꼴을 본다: 상위의 가정 가운데 이 도구가 옮기지 않은 것)")
        return 1
    with io.open(a.낼, "w", encoding="utf-8", newline="\n") as f:
        json.dump(g, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("냈다 —", a.낼)
    return 0


if __name__ == "__main__":
    sys.exit(main())

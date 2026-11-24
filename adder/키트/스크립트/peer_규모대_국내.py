# -*- coding: utf-8 -*-
"""C2 · CP1 국내 시가총액 규모대 재판정 — 캐시만 읽는다(네트워크 0회).

왜 있는가 (펄어비스 회차 펄29)
    C1 은 매출·자산으로 규모대를 걸고 시가총액을 안 세운다. CP1 이 시가총액으로 다시 재야
    하는데 국내용 도구가 없어(미국은 `sec_peer_screen.py`) 회차가 캐시를 잇는 스크립트를 짰다.
    실측: 데브시스터즈가 매출로는 0.81배(안)였는데 시총으로는 0.081배 — 밴드 1/10 밖으로
    뒤집혔다. **손 조립은 틀리고 느리다** — 이 자리가 미국 회차의 최장 멈춤(약 7분)이었다.

읽는 것
    --명단            C1 산출(`peer_후보조립_국내.py` 의 핵심표본 JSON — 핵심·예비·컷통과_전체)
                      또는 목록 JSON [{종목코드, 고유번호, 회사명, 왜: "핵심|예비|넓은표본"}]
    주식수.csv        dart_shares.py — 유통(자기주식 차감) 우선, 없으면 발행
    _raw/peers/종가_{기준일}.json   peer_기준일종가_국내.py
    대상 주식수       --대상주식수(출처는 --대상주식수출처 로 적는다) 또는 주식수.csv 의 대상 고유번호 행

판정
    배 = 후보 시총 ÷ 대상 시총. `--배수`(C1 선언 규모대, 기본 10) 밖이면 밴드 밖.
    **사업 접점 「유」(C1 원문 확인)는 밴드 밖이어도 뒤집지 않는다**(2026-10-25 — 「밴드 밖 · 같은 사업 남김」 · 규모 차이만 적는다).
    위험 동종은 사업이 같은가가 첫째이고, 얇은 거래로 쏠린 베타는 βU본값 ⑦ 유동성 잣대가 본값에서 뺀다.
    `--참고배수`(기본 5) 판정을 나란히 싣는다 — 선언을 바꾸지 않고 「다른 기준이면」을 보인다.
    시총을 못 세운 곳(종가·주식수 없음)은 **판정하지 않는다** — 밖으로 읽지 않고 「확인 불가」.

뒤집히면 (워밍 창 불변식)
    **표를 고치지 않는다.** 교체안만 낸다 — 핵심에서 밴드 밖을 빼고 예비 순서대로 밴드 안인
    곳을 올리고, 예비 빈자리는 컷통과 순위에서 다음으로 밴드 안인 곳을 채운다(골라서 올리지 않는다).
    통지 정정 문안을 함께 쓴다. 되돌리는 결정은 사람의 것이다.

사용
    python 스크립트/peer_규모대_국내.py --명단 _raw/peers/핵심표본.json --기준일 20260630 \\
        --대상 263750 --대상주식수 60983910 --대상주식수출처 "_raw/A2b_주석.json 반기 유통주식수"
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")


def _f(v):
    try:
        s = str(v).replace(",", "").strip()
        return float(s) if s not in ("", "None", "-") else None
    except (TypeError, ValueError):
        return None


def 명단읽기(p):
    d = json.load(io.open(p, encoding="utf-8"))
    if isinstance(d, dict) and "컷통과_전체" in d:
        핵 = {x["종목코드"] for x in d.get("핵심", [])}
        예 = {x["종목코드"] for x in d.get("예비", [])}
        # 2026-10-25 C1 규모 — 핵심 · 예비 줄의 사업 접점을 함께 읽는다(접점 「유」 는 시총 띠 밖이어도 뒤집지 않는다). 슬롯을 합친 C1 산출은
        # 컷통과_전체가 첫 슬롯 것이라 핵심 · 예비가 거기 없을 수 있다 — 핵심 · 예비를 먼저 펴고 컷통과_전체로 나머지를 채운다
        본 = {}
        접 = {x["종목코드"]: x.get("사업접점", "") for x in d.get("핵심", []) + d.get("예비", [])}
        for x in d["컷통과_전체"] + d.get("핵심", []) + d.get("예비", []):      # 컷통과 순위가 먼저(교체안의 「컷통과순위」) · 빠진 핵심 · 예비는 뒤에
            c = x["종목코드"]
            if c in 본:
                continue
            본[c] = {"종목코드": c, "고유번호": x.get("고유번호", ""), "회사명": x.get("회사명", ""),
                    "시장": x.get("시장", ""), "사업접점": 접.get(c) or x.get("사업접점", ""),
                    "구분": "핵심" if c in 핵 else ("예비" if c in 예 else "넓은표본")}
        return list(본.values())
    out = []
    for x in d:
        왜 = (x.get("구분") or x.get("왜") or "넓은표본").split(" ")[0]
        out.append({"종목코드": str(x["종목코드"]).zfill(6), "고유번호": x.get("고유번호", ""),
                    "회사명": x.get("회사명", ""), "시장": x.get("시장", ""),
                    "구분": 왜 if 왜 in ("핵심", "예비") else "넓은표본"})
    return out


def 시총(row, 주식, 종가):
    s = 주식.get(row["고유번호"], {})
    유통, 발행 = _f(s.get("유통주식수")), _f(s.get("발행주식총수"))
    if 유통:
        분모, 종류 = 유통, "유통(자기주식 차감)"
    elif 발행:
        분모, 종류 = 발행, "발행(유통 확인 불가)"
    else:
        분모, 종류 = None, "확인 불가 — 주식수.csv 에 행 없음"
    p = 종가.get(row["종목코드"])
    return p, 분모, 종류, s.get("구분이름"), (p * 분모 if (p and 분모) else None)


def 판정(명단, 주식, 종가, 대상시총, 배수, 참고배수, 경계폭):
    행들 = []
    for x in 명단:
        p, 분모, 종류, 구분이름, cap = 시총(x, 주식, 종가)
        배 = cap / 대상시총 if cap else None
        밖 = None if 배 is None else not (1.0 / 배수 <= 배 <= 배수)
        참고밖 = None if 배 is None else not (1.0 / 참고배수 <= 배 <= 참고배수)
        비고 = []
        if p is None:
            비고.append("종가 없음 — 종가_{기준일}.json 에 코드 없음")
        if 배 is not None and not 밖 and (배 < 경계폭 / 배수 or 배 > 배수 / 경계폭):
            비고.append("경계 근접")
        # 2026-10-25 C1 규모 — 위험 동종은 사업이 같은가가 첫째다. 원문으로 접점 「유」 를 확인한 회사는 시총 띠 밖이어도 뒤집지 않고 규모 차이만 적는다
        # (대상이 국내 1위 대형사면 같은 사업 국내 상장사가 전부 띠 밑이다 — 얇은 거래는 βU본값 ⑦ 유동성 잣대가 막는다)
        같은 = bool(밖) and (x.get("사업접점") == "유")
        if 같은:
            비고.append("밴드 밖 · 같은 사업(접점 유) — 남김(규모 차이 %.3g배)" % 배)
        행들.append(dict(x, **{"종가": p, "주식수분모": 분모, "분모종류": 종류, "주식수_구분이름": 구분이름,
                             "시가총액_억": round(cap / 1e8, 1) if cap else None,
                             "대상대비배": round(배, 4) if 배 is not None else None,
                             "밴드밖": 밖, "참고밴드밖": 참고밖, "같은사업남김": 같은,
                             "판정": ("확인 불가 — 시총 못 세움" if 배 is None else
                                    ("밴드 밖 · 같은 사업 남김" if 같은 else ("밴드 밖" if 밖 else "밴드 안"))),
                             "비고": " · ".join(비고)}))
    return 행들


def _뒤집(r):
    """교체안에서 빼는 줄 — 시총 띠 밖이고 같은 사업으로 남긴 줄이 아니다."""
    return r["밴드밖"] is True and not r.get("같은사업남김")


def 교체안(행들):
    """핵심에서 밴드 밖을 빼고, 예비 순서대로 밴드 안을 올리고, 예비 빈자리는 넓은표본 순서로 채운다."""
    핵 = [r for r in 행들 if r["구분"] == "핵심"]
    예 = [r for r in 행들 if r["구분"] == "예비"]
    넓 = [r for r in 행들 if r["구분"] == "넓은표본"]
    뒤집힘 = [r for r in 핵 + 예 if _뒤집(r)]
    if not 뒤집힘:
        return 뒤집힘, None
    새핵 = [r for r in 핵 if not _뒤집(r)]
    남은예 = [r for r in 예 if not _뒤집(r)]
    올림 = []
    while len(새핵) < len(핵) and 남은예:
        r = 남은예.pop(0)
        새핵.append(r)
        올림.append(r)
    채움 = []
    후보 = [r for r in 넓 if r["밴드밖"] is False]
    while len(남은예) < len(예) and 후보:
        r = 후보.pop(0)
        남은예.append(r)
        채움.append(r)
    끝 = 넓.index(채움[-1]) if 채움 else len(넓)
    return 뒤집힘, {"새핵심": [r["회사명"] for r in 새핵], "새예비": [r["회사명"] for r in 남은예],
                   "예비에서_올림": [r["회사명"] for r in 올림], "넓은표본에서_채움": [
                       {"회사명": r["회사명"], "종목코드": r["종목코드"], "컷통과순위": 행들.index(r) + 1,
                        "대상대비배": r["대상대비배"]} for r in 채움],
                   "건너뛴_넓은표본(밴드 밖·확인 불가)": [r["회사명"] for r in 넓[:끝] if r["밴드밖"] is not False],
                   "줄어듦": max(0, len(핵) - len(새핵)) + max(0, len(예) - len(남은예))}


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="C2·CP1 국내 시가총액 규모대 재판정 — 네트워크 0회")
    ap.add_argument("--폴더", default=os.getcwd())
    ap.add_argument("--명단", required=True, help="C1 핵심표본 JSON 또는 목록 JSON")
    ap.add_argument("--기준일", "--평가기준일", dest="기준일", required=True, help="평가기준일 T(분석일 · 시장 쪽 — 종가 · 시가총액 · 주식수 · 베타 창 끝 · 환율 · 법령 시행일) YYYYMMDD — 종가_{기준일}.json")
    ap.add_argument("--대상", required=True, help="대상 종목코드")
    ap.add_argument("--대상고유번호", default=None, help="주식수.csv 에서 대상 주식수를 읽을 때")
    ap.add_argument("--대상주식수", type=float, default=None, help="대상 유통주식수(자기주식 차감)")
    ap.add_argument("--대상주식수출처", default="", help="대상 주식수의 출처 — 비우면 경보")
    ap.add_argument("--배수", type=float, default=10.0, help="C1 선언 규모대 배수")
    ap.add_argument("--참고배수", type=float, default=5.0)
    ap.add_argument("--경계폭", type=float, default=1.6, help="밴드 경계의 이 배 안쪽이면 경계 근접 표시")
    ap.add_argument("--주식수기준", default="", help="주식수.csv 의 기준(예: 2026 반기보고서 11012)")
    ap.add_argument("--출력", default=None, help="기본 {폴더}/_raw/peers/C2_CP1_규모대.json")
    a = ap.parse_args()
    폴더 = os.path.abspath(a.폴더)
    peer = os.path.join(폴더, "_raw", "peers")
    명단p = a.명단 if os.path.isabs(a.명단) else (os.path.join(peer, a.명단)
                                             if os.path.exists(os.path.join(peer, a.명단)) else os.path.join(폴더, a.명단))
    명단 = 명단읽기(명단p)
    # 고유번호가 빈 명단(회차 손 JSON 실측)은 KIND 명부·싼 층 캐시로 채운다 — 비면 주식수를 못 찾아 전원이 확인 불가로 떨어진다
    빈 = [x for x in 명단 if not x["고유번호"]]
    if 빈:
        import glob
        지도 = {}
        for p in ([os.path.join(폴더, "_dartcache", "상장명부_KIND.csv")]
                  + sorted(glob.glob(os.path.join(peer, "싼층_*.csv")))
                  + sorted(glob.glob(os.path.join(폴더, "상장사_주요계정_*.csv")))):
            if os.path.exists(p):
                for r in csv.DictReader(io.open(p, encoding="utf-8-sig")):
                    if r.get("고유번호") and r.get("종목코드"):
                        지도.setdefault(r["종목코드"].zfill(6), r["고유번호"].zfill(8))
        for x in 빈:
            x["고유번호"] = 지도.get(x["종목코드"], "")
    주식p = os.path.join(폴더, "주식수.csv")
    종가p = os.path.join(peer, "종가_%s.json" % a.기준일)
    for p in (주식p, 종가p):
        if not os.path.exists(p):
            sys.exit("캐시가 없습니다: %s — dart_peer_사슬.py --단계 중간 을 먼저 돌리십시오" % p)
    주식 = {r["고유번호"]: r for r in csv.DictReader(io.open(주식p, encoding="utf-8-sig"))}
    종가 = json.load(io.open(종가p, encoding="utf-8"))
    T = a.대상.zfill(6)
    if T not in 종가:
        sys.exit("대상 %s 종가가 %s 에 없습니다" % (T, 종가p))
    출처 = a.대상주식수출처
    if a.대상주식수:
        대상주식 = a.대상주식수
        if not 출처:
            출처 = "출처 미기재 — 경보: --대상주식수출처 를 적으십시오"
    elif a.대상고유번호 and (주식.get(a.대상고유번호) or {}).get("유통주식수"):
        대상주식 = _f(주식[a.대상고유번호]["유통주식수"])
        출처 = 출처 or "주식수.csv 대상 행 유통주식수(dart_shares.py)"
    else:
        sys.exit("대상 주식수가 없습니다 — --대상주식수(+출처) 또는 주식수.csv 에 대상 행이 필요합니다. "
                 "대상 주식수는 본선(원본 확보) 소유라 여기서 받지 않습니다")
    대상시총 = 종가[T] * 대상주식
    행들 = 판정(명단, 주식, 종가, 대상시총, a.배수, a.참고배수, a.경계폭)
    뒤집힘, 안 = 교체안(행들)
    확인불가 = [r["회사명"] for r in 행들 if r["대상대비배"] is None]
    통지 = None
    if 뒤집힘:
        통지 = ("[C1 통지 정정] 시가총액 기준 규모대(1/%g~%g배)를 다시 재니 핵심·예비 중 %d곳이 밴드 밖입니다. %s. "
               "배분표 다음 순위로 교체하면 핵심은 %s, 예비는 %s 가 됩니다(예비에서 올림: %s · 넓은표본에서 채움: %s). "
               "핵심표본.json 은 고치지 않았습니다 — 어느 쪽으로 갈까요?"
               % (a.배수, a.배수, len(뒤집힘),
                  " · ".join("%s(%s, %s) — 시총 %s억 · %.3f배" % (r["회사명"], r["구분"], r["종목코드"], r["시가총액_억"], r["대상대비배"])
                             for r in 뒤집힘),
                  "·".join(안["새핵심"]), "·".join(안["새예비"]), "·".join(안["예비에서_올림"]) or "없음",
                  "·".join("%s(순위 %d)" % (x["회사명"], x["컷통과순위"]) for x in 안["넓은표본에서_채움"]) or "없음"))
    out = {"status": "완료", "도구": "peer_규모대_국내.py", "끝난시각": time.strftime("%Y-%m-%d %H:%M:%S"), "네트워크": 0,
           "명단": os.path.relpath(명단p, 폴더), "기준일": a.기준일,
           "대상": {"종목코드": T, "종가": 종가[T], "주식수": 대상주식, "주식수_출처": 출처,
                  "시가총액_억": round(대상시총 / 1e8, 1)},
           "주식수기준": a.주식수기준 or "미기재",
           "밴드": "C1 선언 규모대 1/%g~%g배를 시가총액에 적용 → %.1f억~%.1f억 (참고 1/%g~%g배 병기)"
                 % (a.배수, a.배수, 대상시총 / a.배수 / 1e8, 대상시총 * a.배수 / 1e8, a.참고배수, a.참고배수),
           "뒤집힘_핵심예비": [r["회사명"] for r in 뒤집힘], "교체안": 안, "통지정정": 통지,
           "확인불가": 확인불가,
           "경계근접": [("%s %.3f배" % (r["회사명"], r["대상대비배"])) for r in 행들 if "경계 근접" in r["비고"]],
           "참고밴드_밖_핵심예비": [r["회사명"] for r in 행들 if r["구분"] in ("핵심", "예비") and r["참고밴드밖"]],
           "같은사업_밴드밖_남김": [{"회사명": r["회사명"], "구분": r["구분"], "대상대비배": r["대상대비배"]} for r in 행들 if r.get("같은사업남김")],
           "표불변": "핵심표본.json 은 고치지 않는다(워밍 창 불변식) — 교체는 사람의 답 뒤에",
           "행": 행들}
    p = a.출력 or os.path.join(peer, "C2_CP1_규모대.json")
    if not os.path.isabs(p):
        p = os.path.join(폴더, p)
    json.dump(out, io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("→ %s" % p)
    print("대상 시총 %.1f억 (%s) · %s" % (대상시총 / 1e8, 출처, out["밴드"]))
    for r in 행들:
        print("  %-8s %-12s %s %10s %8s %s %s" % (r["구분"], r["회사명"][:12], r["종목코드"], r["시가총액_억"],
                                              r["대상대비배"], r["판정"], r["비고"]))
    print("뒤집힘:", out["뒤집힘_핵심예비"] or "0곳")
    if 통지:
        print(통지)
    if 확인불가:
        print("확인 불가(판정 안 함):", 확인불가)
    return 0


if __name__ == "__main__":
    sys.exit(main())

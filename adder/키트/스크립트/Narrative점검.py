# -*- coding: utf-8 -*-
"""Narrative점검 — 분기마다 Narrative 의 신호를 보고 판정을 적는 기록 (L2 · 제안 5절 M9).

레터 15절(Narrative 점검)의 신호(가정 파일 「신호」 — M3)를 분기 실적이 나올 때마다 보고, 관측값과 판정을 회차 폴더의
`Narrative점검.json` 에 쌓는다. 판정이 shift 이상이면 회차를 다시 돌리라고 알린다(종료 코드 1).

    python 스크립트/Narrative점검.py <가정.json> --새분기 2026Q3 [--기준일 2026-09-30]   빈 기록(신호마다 한 줄)을 더한다
    python 스크립트/Narrative점검.py <가정.json> [--기록 <Narrative점검.json>]           기록을 검사하고 분기 × 신호 표 · 마지막 판정을 찍는다
    python 스크립트/Narrative점검.py <가정.json> --새분기 2026Q3 --원문 새.txt --직전 옛.txt   빈 기록에 「바뀐 문장 초안」을 붙인다(2026-10-21)

**바뀐 문장 초안(2026-10-21)** — `--원문`(새 분기 보고서 텍스트)과 `--직전`(그 앞 보고서)을 주면 `문장비교.비교()` 로 「사업의 내용」의
새 · 바뀐 · 빠진 문장을 뽑고, 신호마다 낱말이 겹치는 문장(설정 없이 — 신호 글의 두 글자 이상 낱말 둘 이상, 한 낱말 신호면 그 낱말이 겹치는 문장)을 그 관측의
`메모` 에 「초안 — …」 으로 적는다. **값 · 판정은 비워 둔다** — 판정은 사람이 한다. 기록에 `초안` 칸(앞 · 뒤 · 요약)이 붙는다.

기록 파일(회차 폴더 — 가정 파일 곁의 `Narrative점검.json`)
  {"형식": "Narrative 점검 1", "회사": "…", "레터": {"평가기준일": "2026-06-30", "가정해시": "…"},
   "기록": [{"분기": "2026Q3", "기준일": "2026-09-30", "작성일": "2026-10-28",
             "관측": [{"신호": "<가정 파일 신호[i].신호 와 같은 글>", "값": "…", "판정": "유지 | shift | change | break", "메모": "…"}],
             "판정": "유지 | shift | change | break(비우면 관측 판정의 가장 무거운 것)", "까닭": "…"}]}
판정의 무게: 유지 < shift < change < break. shift — 해당 가정만 고친다 · change — 매출 구분과 구조까지 · break — 모델을 다시 세운다.
종료 코드: 0 유지(또는 기록 없음) · 1 shift 이상 — 회차를 다시 돌린다 · 2 입력 오류(모르는 신호 · 판정 · 꼴).
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import io
import json
import os
import re
import sys

판정무게 = {"유지": 0, "shift": 1, "change": 2, "break": 3}
기록파일 = "Narrative점검.json"


def _해시(가정):
    깨끗 = {k: v for k, v in 가정.items() if not ("%s" % k).startswith("_경로")}
    return hashlib.sha256(json.dumps(깨끗, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def 신호목록(가정):
    return [("%s" % x.get("신호")).strip() for x in (가정.get("신호") or []) if isinstance(x, dict) and ("%s" % (x.get("신호") or "")).strip()]


def 검사(기록, 가정):
    """→ 걸린 목록(입력 오류)."""
    걸린 = []
    if not isinstance(기록, dict) or not isinstance(기록.get("기록"), list):
        return ["기록 파일의 꼴이 아니다 — {\"형식\", \"기록\": [...]}"]
    알 = set(신호목록(가정))
    for i, x in enumerate(기록["기록"]):
        if not isinstance(x, dict) or not re.match(r"^\d{4}Q[1-4]$", "%s" % x.get("분기")):
            걸린.append("기록[%d].분기 는 2026Q3 꼴이다" % i)
            continue
        if x.get("판정") not in (None, "") and x.get("판정") not in 판정무게:
            걸린.append("기록[%d].판정 은 유지 · shift · change · break 가운데 하나다" % i)
        for j, o in enumerate(x.get("관측") or []):
            if not isinstance(o, dict):
                걸린.append("기록[%d].관측[%d] 이 객체가 아니다" % (i, j))
                continue
            if ("%s" % o.get("신호")).strip() not in 알:
                걸린.append("기록[%d].관측[%d] 의 신호 「%s」 가 가정 파일의 신호에 없다" % (i, j, o.get("신호")))
            if o.get("판정") not in (None, "") and o.get("판정") not in 판정무게:
                걸린.append("기록[%d].관측[%d].판정 은 유지 · shift · change · break 가운데 하나다" % (i, j))
    return 걸린


def 분기판정(x):
    """한 분기의 판정 — 적은 판정, 없으면 관측 판정 가운데 가장 무거운 것(관측이 비었으면 None)."""
    if x.get("판정") in 판정무게:
        return x["판정"]
    판 = [o.get("판정") for o in x.get("관측") or [] if o.get("판정") in 판정무게]
    return max(판, key=lambda p: 판정무게[p]) if 판 else None


def 새분기(기록, 가정, 분기, 기준일=None):
    if any(x.get("분기") == 분기 for x in 기록["기록"]):
        raise ValueError("%s 의 기록이 이미 있다" % 분기)
    기록["기록"].append({"분기": 분기, "기준일": 기준일 or "", "작성일": datetime.date.today().isoformat(),
                      "관측": [{"신호": s, "값": "", "판정": "", "메모": ""} for s in 신호목록(가정)], "판정": "", "까닭": ""})
    return 기록


def _낱말(글):
    return {w for w in re.findall(r"[가-힣A-Za-z0-9]{2,}", "%s" % 글)}


def 초안붙이기(기록, 분기, 새글, 옛글, 앞이름="직전", 뒤이름="새 분기", 최대=3):
    """2026-10-21 — 그 분기 기록의 관측 메모에 바뀐 문장 초안을 단다(값 · 판정은 비운 채). → 붙인 관측 수."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import 문장비교                                          # noqa: PLC0415
    r = 문장비교.비교(옛글, 새글, 앞이름=앞이름, 뒤이름=뒤이름)
    줄 = []                                                  # (종류, 절, 문장, 번호)
    for 절 in r.get("절") or []:
        이름 = 절.get("절") or ""
        for x in 절.get("새") or []:
            줄.append(("새", 이름, x.get("문장") or "", x.get("번호")))
        for x in 절.get("바뀜") or []:
            줄.append(("바뀜", 이름, x.get("뒤") or "", x.get("뒤번호")))
        for x in 절.get("빠짐") or []:
            줄.append(("빠짐", 이름, x.get("문장") or "", x.get("번호")))
    x = next(y for y in 기록["기록"] if y.get("분기") == 분기)
    붙 = 0
    for o in x.get("관측") or []:
        신 = _낱말(o.get("신호"))
        문턱 = 1 if len(신) <= 1 else 2                       # 한 낱말 신호(「장기공급계약」)는 그 낱말 하나로
        맞 = [(len(신 & _낱말(문)), 종, 절, 문, 번) for 종, 절, 문, 번 in 줄]
        맞 = sorted([m for m in 맞 if m[0] >= 문턱], key=lambda m: -m[0])[:최대]
        if 맞:
            o["메모"] = "초안 — " + " / ".join("%s 문장(%s · %s번): 「%s」" % (종, 절, 번, 문[:120]) for _n, 종, 절, 문, 번 in 맞)
            붙 += 1
    x["초안"] = {"앞": 앞이름, "뒤": 뒤이름, "요약": r.get("요약"), "주의": "값 · 판정은 사람이 적는다 — 이 메모는 문장 비교의 후보다"}
    return 붙


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(allow_abbrev=False, description="분기 Narrative 점검 기록(M9)")
    ap.add_argument("가정")
    ap.add_argument("--기록", default=None, help="기록 파일(비우면 가정 파일 곁의 Narrative점검.json)")
    ap.add_argument("--새분기", default=None, help="빈 기록을 더할 분기(2026Q3 꼴)")
    ap.add_argument("--기준일", default=None)
    ap.add_argument("--원문", default=None, help="새 분기 보고서 텍스트 — --새분기 와 함께(바뀐 문장 초안)")
    ap.add_argument("--직전", default=None, help="그 앞 보고서 텍스트 — --원문 과 함께")
    a = ap.parse_args()
    try:
        가정 = json.load(io.open(a.가정, encoding="utf-8"))
    except Exception as e:                                   # noqa: BLE001
        print("Narrative 점검 — 가정 파일을 못 읽었다: %s" % e)
        return 2
    p = a.기록 or os.path.join(os.path.dirname(os.path.abspath(a.가정)), 기록파일)
    if os.path.isfile(p):
        기록 = json.load(io.open(p, encoding="utf-8"))
    else:
        기록 = {"형식": "Narrative 점검 1", "회사": (가정.get("메타") or {}).get("회사명"),
              "레터": {"평가기준일": (가정.get("메타") or {}).get("평가기준일"), "가정해시": _해시(가정)}, "기록": []}
    if not 신호목록(가정):
        print("Narrative 점검 — 가정 파일에 「신호」 가 없다(레터 15절의 신호 표 — M3)")
        return 2
    if a.새분기:
        if not re.match(r"^\d{4}Q[1-4]$", a.새분기):
            print("Narrative 점검 — 분기는 2026Q3 꼴로 준다")
            return 2
        try:
            새분기(기록, 가정, a.새분기, a.기준일)
        except ValueError as e:
            print("Narrative 점검 — %s" % e)
            return 2
        붙 = None
        if a.원문 or a.직전:
            if not (a.원문 and a.직전 and os.path.isfile(a.원문) and os.path.isfile(a.직전)):
                print("Narrative 점검 — 초안은 --원문 과 --직전 두 텍스트 파일이 다 있어야 한다")
                return 2
            붙 = 초안붙이기(기록, a.새분기, io.open(a.원문, encoding="utf-8").read(), io.open(a.직전, encoding="utf-8").read(),
                       os.path.basename(a.직전), os.path.basename(a.원문))
        io.open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(기록, ensure_ascii=False, indent=1) + "\n")
        print("Narrative 점검 — %s 의 빈 기록(신호 %d줄)을 더했다%s → %s"
              % (a.새분기, len(신호목록(가정)), "" if 붙 is None else " · 바뀐 문장 초안을 관측 %d줄에 붙였다(값 · 판정은 비움)" % 붙, p))
        return 0
    걸린 = 검사(기록, 가정)
    for x in 걸린:
        print("  · %s" % x)
    if 걸린:
        print("Narrative 점검 — 입력 오류 %d건" % len(걸린))
        return 2
    if 기록.get("레터", {}).get("가정해시") not in (None, _해시(가정)):
        print("알림 — 기록을 만든 뒤 가정 파일이 바뀌었다(새 회차면 새 기록 파일로 시작한다)")
    분기들 = [x for x in 기록["기록"] if isinstance(x, dict)]
    print("Narrative 점검 — %s · 분기 %d개" % (기록.get("회사") or "", len(분기들)))
    for s in 신호목록(가정):
        칸 = []
        for x in 분기들:
            o = next((y for y in x.get("관측") or [] if ("%s" % y.get("신호")).strip() == s), {})
            칸.append("%s %s%s" % (x["분기"], o.get("값") or "—", (" [%s]" % o["판정"]) if o.get("판정") else ""))
        print("  %s — %s" % (s[:40], " · ".join(칸) or "기록 없음"))
    if not 분기들:
        print("마지막 판정 — 기록 없음")
        return 0
    마 = 분기들[-1]
    판 = 분기판정(마)
    print("마지막 판정 — %s %s%s" % (마["분기"], 판 or "판정 없음", (" — %s" % 마["까닭"]) if 마.get("까닭") else ""))
    if 판 and 판정무게[판] >= 1:
        print("판정이 %s 다 — 회차를 다시 돌린다(%s)" % (판, {"shift": "해당 가정만 고친다", "change": "매출 구분과 구조까지 손본다",
                                                    "break": "모델을 다시 세운다"}[판]))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

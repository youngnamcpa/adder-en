# -*- coding: utf-8 -*-
"""**도구 상태 점검** — 키트 문서에 적힌 「도구 상태 문장」이 코드와 맞는가(2026-10-16, S1 리뷰 S1-15).

    python 스크립트/도구상태점검.py            # 걸린 곳 목록 · rc 1(걸림) / 0
    python 스크립트/도구상태점검.py --전부      # 걸린 곳과 함께 본 문서 수

왜 있나 — 문서가 코드보다 늦으면 갈래가 **있는 도구를 두고 손으로 조립한다.** 실측(S1 리뷰): 「운영 지표 집계 도구가 아직 없다」
(`peer_운영지표.py` 가 있었다) · 「`sec_주봉.py` 기본 창이 3년 고정」(코드는 5년) · 「국내 `peer_조립.py` 에는 아직 현금보정이 없다」(있었다) ·
「검증기가 아직 원가 범주를 모른다」(알았다) · 「`sec_fetch.py` 의 앵커 루프」(없다 — `sec_앵커.py`). `키이름점검.py` 와 같은 자리의 점검이다.

재는 것 둘(문장 꼴로 — 회사 · 업종 이름과 무관하다)
  ① **「아직 없다 · 모른다 · 코드 작업 몫」 문장에 이름이 나온 도구가 실제로 있는가** — 같은 줄에 `X.py` 와 「아직 (없 · 모르 · 안 됐)」
     「코드 작업 몫」 「코드가 고쳐질 때까지」가 함께 있으면 후보다. X.py 가 있으면 걸린다(문장을 코드에 맞추거나, 정말 없는 칸이면 칸 이름까지 적는다).
     문장에 도구 이름 없이 「집계 도구가 아직 없다」처럼 쓰면 잡히지 않는다 — 도구 상태를 말할 때는 이름을 적는다
  ② **「X.py … 기본(창) N년」 문장이 그 도구의 인자 기본값과 같은가** — X.py 의 argparse 인자 가운데 이름에 「창」이 든 것(`--창년` · `--창` · `--운영창`)의
     기본값이 N 과 다르면 걸린다
걸린 줄은 모두 사람이 고친다 — 이 도구는 문서를 고치지 않는다.
"""
from __future__ import annotations

import argparse
import glob
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass
여기 = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(여기)

_아직 = re.compile(r"아직[^.。]{0,30}?(없|모르|모른|안\s*(됐|되|된|한))|코드\s*작업\s*몫|코드가\s*고쳐질\s*때까지")
_도구 = re.compile(r"`?([A-Za-z0-9_가-힣]+\.py)`?")
_기본창 = re.compile(r"`?([A-Za-z0-9_가-힣]+\.py)`?[^\n]{0,80}?기본\s*(?:창|관측창)?\s*(?:이|은|값|=)?\s*(\d+)\s*(?:년|해)")


def 문서들(뿌리=ROOT):
    낸 = [os.path.join(뿌리, x) for x in ("CLAUDE.md", "모델링_프롬프트_집대성.md", "가정_스키마.md", "스캐폴드_구조.md")]
    낸 += sorted(glob.glob(os.path.join(뿌리, ".claude", "갈래", "*.md")))
    낸 += sorted(glob.glob(os.path.join(뿌리, ".claude", "skills", "*", "SKILL.md")))
    return [p for p in 낸 if os.path.exists(p)]


def 창기본값(경로):
    """도구의 argparse 인자 가운데 이름에 「창」이 든 것의 기본값들(정수)."""
    try:
        글 = io.open(경로, encoding="utf-8").read()
    except OSError:
        return []
    낸 = []
    for m in re.finditer(r"add_argument\(\s*\"--([^\"]*창[^\"]*)\"[^)]*?default\s*=\s*\"?(\d+)\"?", 글, re.S):
        낸.append(int(m.group(2)))
    return 낸


def 점검(뿌리=ROOT):
    스크립트 = os.path.join(뿌리, "스크립트")
    걸린, 본 = [], 0
    for p in 문서들(뿌리):
        본 += 1
        for i, 줄 in enumerate(io.open(p, encoding="utf-8").read().split("\n"), start=1):
            if _아직.search(줄):
                for 이름 in dict.fromkeys(_도구.findall(줄)):
                    if os.path.exists(os.path.join(스크립트, 이름)):
                        걸린.append({"파일": os.path.relpath(p, 뿌리), "줄": i, "도구": 이름, "종류": "①",
                                   "말": "「아직 없다 · 모른다 · 코드 작업 몫」 문장인데 %s 가 있다 — 코드에 맞춰 고치거나 정말 없는 칸 이름을 적는다" % 이름,
                                   "글": 줄.strip()[:160]})
            for m in _기본창.finditer(줄):
                이름, n = m.group(1), int(m.group(2))
                기본 = 창기본값(os.path.join(스크립트, 이름))
                if 기본 and n not in 기본:
                    걸린.append({"파일": os.path.relpath(p, 뿌리), "줄": i, "도구": 이름, "종류": "②",
                               "말": "문서는 기본 %d 이라는데 %s 의 창 인자 기본값은 %s" % (n, 이름, " · ".join(map(str, 기본))),
                               "글": 줄.strip()[:160]})
    걸린 += 버전맞물림(뿌리)
    return 걸린, 본


def 버전맞물림(뿌리=ROOT):
    """③ 플러그인 매니페스트의 version 이 `버전.json` 의 ADDER 와 같은가(2026-10-23 — 준비점검 설계 2-3).
    둘 다 없으면 묻지 않는다(플러그인으로 묶기 전 판). 하나만 있거나 다르면 걸린다."""
    import json                                      # noqa: PLC0415
    pv, vv = os.path.join(뿌리, ".claude-plugin", "plugin.json"), os.path.join(뿌리, "버전.json")
    if not os.path.exists(pv) and not os.path.exists(vv):
        return []
    try:
        p = json.load(io.open(pv, encoding="utf-8")).get("version") if os.path.exists(pv) else None
        v = json.load(io.open(vv, encoding="utf-8")).get("ADDER") if os.path.exists(vv) else None
    except (OSError, ValueError) as e:
        return [{"파일": "버전.json", "줄": 0, "도구": "-", "종류": "③", "말": "매니페스트 · 버전 파일을 읽지 못했다(%s)" % type(e).__name__, "글": ""}]
    if p != v:
        return [{"파일": ".claude-plugin/plugin.json", "줄": 0, "도구": "-", "종류": "③",
                 "말": "플러그인 version %s ≠ 버전.json ADDER %s — 둘을 같은 값으로 올린다" % (p, v), "글": ""}]
    return []


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="문서의 도구 상태 문장 ↔ 코드")
    ap.add_argument("--뿌리", default=ROOT)
    ap.add_argument("--전부", action="store_true")
    a = ap.parse_args(argv)
    걸린, 본 = 점검(a.뿌리)
    for x in 걸린:
        print("%s %s:%d — %s\n      %s" % (x["종류"], x["파일"], x["줄"], x["말"], x["글"]))
    print("도구 상태 점검 — 문서 %d개 · 걸린 곳 %d" % (본, len(걸린)))
    return 1 if 걸린 else 0


if __name__ == "__main__":
    sys.exit(main())

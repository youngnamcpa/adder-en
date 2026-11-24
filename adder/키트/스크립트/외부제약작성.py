# -*- coding: utf-8 -*-
"""**외부 제약 작성** — D 갈래가 `_raw/외부제약.json` 을 손으로 쓰지 않고 블록마다 넣는 작은 도구.

    python 스크립트/외부제약작성.py --새로 --회사 "…" --평가기준일 2026-06-30
    python 스크립트/외부제약작성.py --법령 '{"이름": "…", "조문": "…", "규칙": "…", "경로": {"2030": 0.0}, "적용행": "200", "영구화금지": true, …}'
    python 스크립트/외부제약작성.py --원가 '{"이름": "…", "닿는_원가줄": "인건비", "경로": {"2027": 0.05}, "영구화금지": false, …}'
    python 스크립트/외부제약작성.py --해당없음 산업상한 "그 유형에 물리 상한이 없다"
    python 스크립트/외부제약작성.py --보기

왜 있나 — 자유 JSON 은 형식이 계속 깨졌다(2026-10-16 S1 리뷰: 옛 D 산출 넷 — 하이닉스 · 펄어비스 · 세일즈포스 · LG에너지솔루션 — 이
전부 `외부제약검증.py` rc 1 이었다. 경로에 「영구」 · 「주석」 키, 문자열 영구화금지, 「MACR≥60%」 같은 문자열 잔존비율).
형식이 틀린 제약은 받는 쪽(㉟ · M-07 · M-08 · 동인진단 · 레터)에서 조용히 죽는다.

이 도구는 **항목 하나를 더할 때마다 파일 전체를 `외부제약검증.검사()` 로 재고, 위반이 있으면 쓰지 않는다**(rc 1 · 위반 문장).
블록 다섯(`법령` · `산업상한` · `규제가격` · `재무약정` · `원가`)과 꼴은 `가정_스키마.md` 「갈래 산출물」 · D 갈래 「산출물」 절이 정본이다.
값(잔존비율 · 금액)을 정하지 않는다 — 받은 항목을 꼴대로 넣을 뿐이다.
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
여기 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, 여기)
import 외부제약검증 as 검                                      # noqa: E402

블록 = 검.블록


def 읽기(p):
    if os.path.exists(p):
        return json.load(io.open(p, encoding="utf-8-sig"))
    return None


def 빈틀(회사="", 기준일=""):
    return {"회사": 회사, "평가기준일": 기준일, "조회일": datetime.date.today().isoformat(), "status": "부분", "사유": "",
            "제약": {b: [] for b in 블록}, "해당없음": [], "확인불가": []}


def 쓰기(p, j):
    위, 경 = 검.검사(j.get("제약"))
    for 사슬, 말 in 경:
        print("  경고 %s — %s" % (사슬, 말))
    if 위:
        for 사슬, 말 in 위:
            print("  위반 %s — %s" % (사슬, 말))
        print("**형식 위반 — 쓰지 않았습니다.** 항목을 고쳐 다시 넣으십시오(규약: .claude/갈래/D_외부제약.md 「산출물」)")
        return 1
    os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(j, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("→ %s (위반 0 · 경고 %d)" % (p, len(경)))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="D 외부 제약 — 블록마다 넣고 검증을 통과해야 쓴다")
    ap.add_argument("-o", "--출력", default=os.path.join(os.path.dirname(여기), "_raw", "외부제약.json"))
    ap.add_argument("--새로", action="store_true", help="빈 틀로 시작한다(있으면 덮는다)")
    ap.add_argument("--회사", default="")
    ap.add_argument("--평가기준일", default="", help="평가기준일 T(정보 경계)")
    ap.add_argument("--재무기준일", default="", help="재무기준일 F(2026-10-25 날짜 둘 — 평가기준일과 다를 때만 적힌다 · 스트림병합이 회차 F 로 읽는다)")
    ap.add_argument("--가정", default="", help="두 날짜를 가정 파일에서 읽는다(`기준일.py` — 메타.평가기준일 · 메타.재무기준일)")
    for b in 블록:
        ap.add_argument("--" + b, action="append", default=[], metavar="JSON", help="%s 블록에 항목 하나(JSON 객체)" % b)
    ap.add_argument("--해당없음", nargs=2, action="append", default=[], metavar=("블록", "까닭"),
                    help="그 회사 유형에 닿지 않는 블록 — `해당없음[]` 에 한 줄(블록은 [] 그대로)")
    ap.add_argument("--확인불가", nargs=2, action="append", default=[], metavar=("무엇", "원인"))
    ap.add_argument("--상태", choices=["완료", "부분", "실패"], default=None, help="status 칸")
    ap.add_argument("--보기", action="store_true")
    a = ap.parse_args(argv)
    if a.가정:                                              # 2026-10-25 날짜 둘 — 날짜는 기준일.py 한 곳에서 푼다
        import 기준일 as _기                                  # noqa: PLC0415
        r = _기.기준일들(json.load(io.open(a.가정, encoding="utf-8-sig")))
        if r.get("오류"):
            print("  가정의 날짜를 읽지 못했습니다 — %s" % " · ".join(r["오류"]))
            return 2
        a.평가기준일 = a.평가기준일 or r["평가기준일"]
        if not r["같음"]:
            a.재무기준일 = a.재무기준일 or r["재무기준일"]
    j = None if a.새로 else 읽기(a.출력)
    if j is None:
        j = 빈틀(a.회사, a.평가기준일)
    j.setdefault("제약", {})
    for b in 블록:
        j["제약"].setdefault(b, [])
    if a.회사:
        j["회사"] = a.회사
    if a.평가기준일:
        j["평가기준일"] = a.평가기준일
    if a.재무기준일 and a.재무기준일[:10] != (j.get("평가기준일") or "")[:10]:
        j["재무기준일"] = a.재무기준일[:10]
    if a.보기:
        print(json.dumps(j, ensure_ascii=False, indent=1))
        위, 경 = 검.검사(j.get("제약"))
        print("위반 %d · 경고 %d" % (len(위), len(경)))
        return 1 if 위 else 0
    for b in 블록:
        for 글 in getattr(a, b):
            try:
                x = json.loads(글)
            except ValueError as e:
                print("  %s 항목 JSON 을 읽지 못했습니다: %s" % (b, e))
                return 2
            if not isinstance(x, dict):
                print("  %s 항목은 JSON 객체여야 합니다" % b)
                return 2
            j["제약"][b].append(x)
    for b, 까닭 in a.해당없음:
        if b not in 블록:
            print("  모르는 블록 「%s」 — %s 가운데 하나" % (b, " · ".join(블록)))
            return 2
        j.setdefault("해당없음", []).append({"항목": b, "까닭": 까닭})
    for 무엇, 원인 in a.확인불가:
        j.setdefault("확인불가", []).append({"항목": 무엇, "원인": 원인})
    if a.상태:
        j["status"] = a.상태
    return 쓰기(a.출력, j)


if __name__ == "__main__":
    sys.exit(main())

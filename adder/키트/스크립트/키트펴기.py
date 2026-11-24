# -*- coding: utf-8 -*-
"""키트펴기 — 플러그인으로 설치한 ADDER 키트를 독자의 작업 폴더에 편다(2026-10-27 · 플러그인 배포).

    python -X utf8 <키트>/스크립트/키트펴기.py --낼 <작업 폴더> [--갱신] [--보기]

왜 — 키트 도구는 「키트 폴더 안에서 돌고 그 안에 산출(_raw · 짓기 · 레터)을 쓴다」는 전제로 지어졌고, 규칙(`CLAUDE.md`)도 작업 폴더에서 읽힌다.
  플러그인 설치 폴더는 판마다 바뀌는 캐시라 거기서 돌리면 산출이 판과 함께 사라진다. 그래서 플러그인은 키트를 싣고, 이 도구가 작업 폴더에 편다
  (회차를 만들 때 키트를 통째로 복사하던 것과 같은 꼴).

  처음      작업 폴더에 키트가 없을 때만 편다(`버전.json` 이 있으면 이미 펴진 것 — 종료 2 · `--갱신` 을 안내). 같은 이름의 독자 파일이 있으면
            덮지 않고 건너뛴 목록을 낸다(종료 1).
  --갱신    키트가 싣는 파일만 새 판으로 바꾼다. 내용이 다른 옛 파일은 `_raw/_키트갱신전_<옛 판>_<날짜>/` 에 같은 자리로 옮겨 둔다.
            독자 산출(가정_<회사>.json · 레터_* · 짓기/ · _raw/ · 모션/ · 회차 csv)은 키트가 싣지 않는 이름이라 건드리지 않는다.
  --보기    쓰지 않고 할 일만 찍는다.

펴고 나면 작업 폴더에 `키트펴기.json`(판 · 날짜 · 원본 · 쓴 수 · 건너뛴 수)을 남긴다. 원본은 이 파일이 든 키트(스크립트/ 의 부모)다.
뺄 것(`뺄것`)은 배포짓기와 같다 — 캐시 · 보관 · 작업 산출 · 잠금 파일. 종료: 0 · 1(건너뛴 파일 있음) · 2(입력 오류 · 이미 펴짐).
"""
from __future__ import annotations

import argparse
import datetime
import filecmp
import io
import json
import os
import shutil
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
키트 = os.path.dirname(여기)

# 배포짓기 · 키트펴기가 함께 쓰는 「싣지 않는 것」 — 폴더 이름 · 파일 이름 · 끝말
뺄폴더 = {"__pycache__", ".git", "_raw", "보관", "_dartcache", ".claude-plugin", "배포틀", "회귀기준선", "시험자료"}
뺄파일 = {"scheduled_tasks.lock", "키트펴기.json", ".env", ".env.local",
        # 개발 전용 — 시험 묶음 · 회귀 · 본체 대조 · 조문 지문 · 개발 기록 · 배포 짓기(독자 작업 폴더에는 필요 없다)
        "시험모두.py", "회귀.py", "F회귀자료짓기.py", "줄별대응.py", "도구대조.py", "조문점검.py", "_조문지문.json", "배포짓기.py",
        "CHANGELOG.md"}
뺄끝 = (".pyc", ".pyo", ".tmp", ".log", ".err")


def 뺄것(상대):
    """키트 안의 상대 경로 하나가 싣지 않는 것인가."""
    쪽 = 상대.replace("\\", "/").split("/")
    if any(x in 뺄폴더 for x in 쪽[:-1]) or 쪽[0] in 뺄폴더:
        return True
    이름 = 쪽[-1]
    if 이름.startswith("_") and "시험" in 이름 and 이름.endswith(".py"):       # 개발 전용 시험(_레터시험.py · _시험원고.py …)
        return True
    if 이름.startswith("재검증_") and 이름.endswith(".md"):                     # 개발 기록
        return True
    return 이름 in 뺄파일 or 이름.startswith((".env", "$", "~$")) or 이름.endswith(뺄끝)   # $ · ~$ — 셸이 남긴 떠돌이 로그 · 오피스 잠금 파일


def 실을것(원본=키트):
    """원본 키트에서 싣는 파일 → [상대 경로] (정렬)."""
    낸 = []
    for 뿌리, 폴더들, 파일들 in os.walk(원본):
        상뿌리 = os.path.relpath(뿌리, 원본)
        폴더들[:] = [d for d in 폴더들 if not 뺄것(os.path.normpath(os.path.join(상뿌리, d, "x")))]
        for f in 파일들:
            상 = os.path.normpath(os.path.join(상뿌리, f)) if 상뿌리 != "." else f
            if not 뺄것(상):
                낸.append(상)
    return sorted(낸)


def _판(폴더):
    p = os.path.join(폴더, "버전.json")
    try:
        with io.open(p, encoding="utf-8") as f:
            return (json.load(f) or {}).get("ADDER")
    except (OSError, ValueError):
        return None


def 펴기(낼, 갱신=False, 보기=False, 원본=키트, 오늘=None):
    """→ (종료 코드, 보고 dict)."""
    낼 = os.path.abspath(낼)
    if os.path.normcase(낼) == os.path.normcase(os.path.abspath(원본)):
        return 2, {"까닭": "작업 폴더가 키트 원본과 같다 — 다른 폴더를 준다"}
    새판, 옛판 = _판(원본), _판(낼)
    if 옛판 and not 갱신:
        return 2, {"까닭": "이 폴더에는 이미 키트(판 %s)가 펴져 있다 — 새 판으로 바꾸려면 --갱신" % 옛판, "옛판": 옛판, "새판": 새판}
    if not 옛판 and 갱신:
        return 2, {"까닭": "이 폴더에는 펴진 키트가 없다 — 처음이면 --갱신 없이 편다"}
    오늘 = 오늘 or datetime.date.today().isoformat()
    백 = os.path.join(낼, "_raw", "_키트갱신전_%s_%s" % (옛판 or "없음", 오늘))
    쓴, 같음, 건너뜀, 옮김 = [], [], [], []
    for 상 in 실을것(원본):
        a, b = os.path.join(원본, 상), os.path.join(낼, 상)
        if os.path.exists(b):
            if filecmp.cmp(a, b, shallow=False):
                같음.append(상)
                continue
            if not 갱신:
                건너뜀.append(상)
                continue
            옮김.append(상)
            if not 보기:
                d = os.path.join(백, 상)
                os.makedirs(os.path.dirname(d), exist_ok=True)
                shutil.copy2(b, d)
        쓴.append(상)
        if not 보기:
            os.makedirs(os.path.dirname(b), exist_ok=True)
            shutil.copy2(a, b)
    보고 = {"형식": "키트펴기 1", "판": 새판, "옛판": 옛판, "날짜": 오늘, "원본": os.path.abspath(원본), "작업폴더": 낼, "갱신": bool(갱신),
          "쓴수": len(쓴), "같은수": len(같음), "건너뛴": 건너뜀, "옮긴옛판": len(옮김), "백업": 백 if 옮김 else None, "보기": bool(보기)}
    if not 보기:
        with io.open(os.path.join(낼, "키트펴기.json"), "w", encoding="utf-8") as f:
            json.dump(보고, f, ensure_ascii=False, indent=1)
    return (1 if 건너뜀 else 0), 보고


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                    # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description="ADDER 키트를 작업 폴더에 편다(플러그인 배포)")
    ap.add_argument("--낼", required=True, help="작업 폴더(없으면 만든다)")
    ap.add_argument("--갱신", action="store_true", help="펴진 키트를 이 판으로 바꾼다(옛 판은 _raw/_키트갱신전_… 에)")
    ap.add_argument("--보기", action="store_true", help="쓰지 않고 할 일만 찍는다")
    a = ap.parse_args(argv)
    os.makedirs(a.낼, exist_ok=True)
    rc, 보고 = 펴기(a.낼, 갱신=a.갱신, 보기=a.보기)
    if "까닭" in 보고:
        print("키트펴기 — 멈춤: %s" % 보고["까닭"])
        return rc
    머 = "할 일(보기)" if a.보기 else ("새 판으로 바꿈" if a.갱신 else "폈음")
    print("키트펴기 — %s · 판 %s%s · 작업 폴더 %s" % (머, 보고["판"], (" (옛 판 %s)" % 보고["옛판"]) if 보고["옛판"] else "", 보고["작업폴더"]))
    print("  쓴 파일 %d · 이미 같은 파일 %d · 건너뛴 파일 %d%s" % (보고["쓴수"], 보고["같은수"], len(보고["건너뛴"]),
                                                    (" · 옛 판 %d개는 %s 에" % (보고["옮긴옛판"], 보고["백업"])) if 보고["백업"] else ""))
    for 상 in 보고["건너뛴"][:20]:
        print("  건너뜀(같은 이름의 다른 파일이 있다) — %s" % 상)
    if not a.보기 and not a.갱신:
        print("다음 — 이 폴더에서 클로드코드를 새로 연다(규칙 CLAUDE.md 가 읽힌다) → /준비점검")
    return rc


if __name__ == "__main__":
    sys.exit(main())

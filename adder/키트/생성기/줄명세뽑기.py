# -*- coding: utf-8 -*-
"""줄명세뽑기 — 정본(줄명세/)을 스캐폴드 xlsx 에서 새로 뽑는다. 시험은 이 일을 하지 않는다 — 이 명령으로만 한다.

정본을 손으로 고치기 시작한 뒤에는 쓸 일이 없다(고친 것이 모두 사라진다). 2단계(값 불변 대조)까지의 정본을
스캐폴드에서 다시 세울 때만 쓴다.

**산식 개편 W1(2026-10-02) 뒤로는 정본이 명세다.** 줄을 지운 정본에서 지은 스캐폴드는 행 번호가 행 ID 의 숫자(= 가정 번호)와
다르다 — 거기서 다시 뽑으면 행 ID 가 자리 순서로 새로 매겨져 가정 번호가 틀어진다. 그래서 정본의 `책.json` 에 「메모」가
있으면(손으로 고친 정본이라는 표시) `--덮어쓰기` 만으로는 덮어쓰지 않는다. 읽을 xlsx 의 기본값도 걷기 전 스캐폴드(키트 보관/)다.

쓰기:  python 줄명세뽑기.py                          줄명세/ 가 없을 때만 뽑는다
       python 줄명세뽑기.py --덮어쓰기               있는 줄명세/ 를 지우고 새로 뽑는다. 커밋하지 않은 고침이 있으면 멈춘다
       python 줄명세뽑기.py --덮어쓰기 --버려도됨    커밋하지 않은 고침이 있어도 덮어쓴다
       python 줄명세뽑기.py --덮어쓰기 --고친정본버림  책.json 에 「메모」가 있는 정본(손으로 고친 정본)도 덮어쓴다 — 고친 것이 모두 사라진다
       python 줄명세뽑기.py [위의 것] <읽을 xlsx>     스캐폴드 대신 다른 xlsx 에서

범위 지문(줄명세/범위지문.json)도 새로 낸다. 새 시트(새시트/)의 지문은 따로 승인한다:
       python 범위지문.py 승인 줄명세 --덧명세 새시트/S14.jsonl 새시트/S15.jsonl --위치범위
"""
import sys
import os
import json
import shutil
import subprocess

import 명세추출
import 열표
import 줄무늬
import 짓기 as 짓기모듈

여기 = os.path.dirname(os.path.abspath(__file__))
정본 = os.path.join(여기, "줄명세")
# 걷기 전(v12 배치)의 스캐폴드 — 키트 사본의 스캐폴드는 정본으로 지은 것이라 거기서 뽑지 않는다
스캐폴드 = os.path.normpath(os.path.join(여기, "..", "키트", "보관", "스캐폴드_20261002_걷기전", "DCF_워크북_스캐폴드.xlsx"))


def 안커밋한고침():
    """정본 폴더에 커밋하지 않은 고침이 있는가(git 이 없거나 저장소가 아니면 None)."""
    try:
        r = subprocess.run(["git", "status", "--porcelain", "--", "줄명세"], cwd=여기, capture_output=True, text=True, encoding="utf-8")
    except OSError:
        return None
    if r.returncode != 0:
        return None
    return [x for x in r.stdout.splitlines() if x.strip()]


def 정본메모():
    """정본의 `책.json` 에 적힌 「메모」(손으로 고친 정본이라는 표시). 없으면 빈 글."""
    try:
        with open(os.path.join(정본, "책.json"), encoding="utf-8") as f:
            return (json.load(f).get("메모") or "").strip()
    except (OSError, ValueError):
        return ""


def 뽑기(xlsx=스캐폴드, 덮어쓰기=False, 버려도됨=False, 고친정본버림=False):
    있음 = os.path.exists(os.path.join(정본, "책.json"))
    if 있음 and not 덮어쓰기:
        raise SystemExit("줄명세/ 가 이미 있다 — 덮어쓰지 않았다. 새로 뽑으려면 --덮어쓰기 (손으로 고친 것이 모두 사라진다)")
    if 있음:
        메모 = 정본메모()
        if 메모 and not 고친정본버림:
            raise SystemExit("줄명세/ 는 손으로 고친 정본이다 — 덮어쓰지 않았다. 책.json 의 메모: 「%s」\n"
                             "그래도 스캐폴드에서 새로 뽑으려면 --고친정본버림 (고친 것이 모두 사라지고 행 ID 가 읽은 xlsx 의 자리 순서로 매겨진다)" % 메모)
        고침 = 안커밋한고침()
        if 고침 is None and not 버려도됨:
            raise SystemExit("git 으로 줄명세/ 의 상태를 볼 수 없다 — 덮어쓰지 않았다. 그래도 덮어쓰려면 --버려도됨")
        if 고침 and not 버려도됨:
            raise SystemExit("줄명세/ 에 커밋하지 않은 고침이 있다 — 덮어쓰지 않았다(먼저 커밋하거나 --버려도됨):\n  " + "\n  ".join(고침[:20]))
    칸폴더 = os.path.join(여기, "산출", "명세_정본뽑기")
    요약 = 명세추출.추출(xlsx, 칸폴더)
    칸 = 열표.적용(짓기모듈.칸명세읽기(칸폴더))
    if os.path.isdir(정본):
        shutil.rmtree(정본)
    줄요약 = 줄무늬.쓰기(칸, 정본)
    return 요약, 줄요약


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    인자 = sys.argv[1:]
    깃발 = {a for a in 인자 if a.startswith("--")}
    남은 = [a for a in 인자 if not a.startswith("--")]
    if 깃발 - {"--덮어쓰기", "--버려도됨", "--고친정본버림"} or len(남은) > 1:
        raise SystemExit(__doc__)
    요약, 줄요약 = 뽑기(남은[0] if 남은 else 스캐폴드, "--덮어쓰기" in 깃발, "--버려도됨" in 깃발, "--고친정본버림" in 깃발)
    print("정본을 새로 뽑았다: %s ← %s" % (정본, 요약["원본"]))
    print(json.dumps(줄요약, ensure_ascii=False))
    print("새 시트의 범위 지문은 따로 승인한다: python 범위지문.py 승인 줄명세 --덧명세 새시트/S14.jsonl 새시트/S15.jsonl --위치범위")

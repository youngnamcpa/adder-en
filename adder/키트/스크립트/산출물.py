# -*- coding: utf-8 -*-
"""산출물 회차 규약 — 같은 폴더에서 두 세션이 돌아도 산출물이 조용히 안 덮이게 한다.

**규약 두 겹이다.**

1. **폴더를 가른다.** 회차별 산출물은 `_raw/{회차}/` 아래로 간다.
   회차는 환경변수 `DCF_회차` 로 정한다. 안 정하면 작업 폴더 이름을 쓴다
   (같은 폴더에서 두 세션이 돌면 둘 다 같은 이름이 되므로, 그때는 2번이 막는다).

2. **표식을 남기고 덮기 직전에 확인한다.** 파일을 쓸 때마다 옆에 `{파일}.표식.json`
   을 남긴다 — 회차·PID·프로세스 시작시각·쓴시각·사용자. 덮어쓰려는 파일의 표식이
   내 것이 아니면 **경고하고 새 이름으로 피한다.** 조용히 지나가지 않는다.

   「내 것이 아니다」의 판정
     - 회차가 다르다                                   → 남의 것
     - 회차는 같은데 PID 가 다르고, 그 표식이 **내 프로세스가 시작한 뒤에** 쓰였다
       → 지금 같이 돌고 있는 남의 프로세스              → 남의 것
     - 표식이 아예 없다 (규약 이전에 생긴 파일)        → 덮되 알린다

쓰는 법
    import 산출물
    경로, 말 = 산출물.안전쓰기(산출물.산출물경로(뿌리, "대조.txt"), 글)
    #                          ↑ **이것을 빼면 1번 규약이 조용히 무력화된다.**
    #  `안전쓰기` 는 받은 경로에 그대로 쓴다 — 회차 폴더로 되돌려 주지 않는다.
    #  `os.path.join(RAW, "대조.txt")` 를 그냥 넘기면 `_raw/` 직속에 쓰이고
    #  `_raw/{회차}/` 가 사라진다. 실측: 갈래 에이전트가 이 예시를 그대로 따라 썼다.
    경로, 말 = 산출물.안전확보(출력xlsx)   # 직접 저장하는 파일(xlsx 등)은 자리만 잡아 준다
    산출물.표식남기기(경로)                # 안전확보로 자리만 잡았으면 저장 뒤에 표식을 남긴다
"""
from __future__ import annotations

import getpass
import io
import json
import os
import time

_시작시각 = time.time()          # 이 프로세스가 시작한 때 (모듈 최초 import 시점)
_PID = os.getpid()
표식꼬리 = ".표식.json"


def 회차():
    """이번 회차의 이름. `DCF_회차`(= `DCF_ROUND`) 가 있으면 그것, 없으면 작업 폴더 이름.

    두 이름을 다 보는 이유: 윈도우의 bash 는 한글 환경변수 **이름**을 못 내보낸다.
    셸에서는 `DCF_ROUND` 를, 파워셸·파이썬에서는 어느 쪽이든 쓰면 된다."""
    v = (os.environ.get("DCF_회차") or os.environ.get("DCF_ROUND") or "").strip()
    if v:
        return _안전한이름(v)
    return _안전한이름(os.path.basename(os.path.abspath(os.getcwd())) or "기본")


def _안전한이름(s):
    for ch in '\/:*?"<>|':
        s = s.replace(ch, "_")
    return s.strip() or "기본"


def 나의표식():
    try:
        사용자 = getpass.getuser()
    except Exception:                                        # noqa: BLE001
        사용자 = "?"
    return {"회차": 회차(), "PID": _PID, "시작시각": _시작시각,
            "쓴시각": time.time(), "사용자": 사용자,
            "폴더": os.path.abspath(os.getcwd())}


def 회차폴더(뿌리, 하위="_raw"):
    """`{뿌리}/{하위}/{회차}/` 를 만들고 돌려준다."""
    p = os.path.join(뿌리, 하위, 회차())
    if not os.path.isdir(p):
        os.makedirs(p)
    return p


def 산출물경로(뿌리, 이름, 하위="_raw"):
    return os.path.join(회차폴더(뿌리, 하위), 이름)


def _표식읽기(경로):
    p = 경로 + 표식꼬리
    if not os.path.exists(p):
        return None
    try:
        return json.load(io.open(p, "r", encoding="utf-8"))
    except (ValueError, IOError, OSError):
        return None


def 표식남기기(경로):
    try:
        io.open(경로 + 표식꼬리, "w", encoding="utf-8").write(
            json.dumps(나의표식(), ensure_ascii=False))
    except (IOError, OSError):
        pass


def _새이름(경로, 꼬리표):
    뿌리, 확장 = os.path.splitext(경로)
    후보 = "%s__%s%s" % (뿌리, 꼬리표, 확장)
    n = 2
    while os.path.exists(후보):
        m = _표식읽기(후보)
        if m is not None and _내것인가(m):
            return 후보
        후보 = "%s__%s-%d%s" % (뿌리, 꼬리표, n, 확장)
        n += 1
    return 후보


def _내것인가(m):
    if m.get("회차") != 회차():
        return False
    if m.get("PID") != _PID and float(m.get("쓴시각") or 0) >= _시작시각:
        return False
    return True


def 안전확보(경로):
    """덮어쓸 자리가 안전한지 보고, 안 되면 새 경로를 돌려준다.

    돌려주는 것: (실제로 쓸 경로, 보고 문장 목록). 보고는 조용히 삼키지 않는다."""
    말 = []
    폴더 = os.path.dirname(os.path.abspath(경로))
    if 폴더 and not os.path.isdir(폴더):
        os.makedirs(폴더)
    if not os.path.exists(경로):
        return 경로, 말
    m = _표식읽기(경로)
    if m is None:
        말.append("회차 — 표식 없는 기존 파일을 덮었습니다: %s (이번 회차 「%s」)"
                  % (os.path.basename(경로), 회차()))
        return 경로, 말
    if _내것인가(m):
        return 경로, 말
    꼬리표 = 회차() if m.get("회차") != 회차() else "%s-%s" % (회차(), _PID)
    새 = _새이름(경로, 꼬리표)
    말.append("회차 경고 — %s 는 다른 회차/프로세스의 산출물입니다 "
              "(그쪽 회차 「%s」 · PID %s · 쓴시각 %s / 이쪽 회차 「%s」 · PID %s). "
              "덮지 않고 %s 에 씁니다"
              % (os.path.basename(경로), m.get("회차"), m.get("PID"),
                 time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(m.get("쓴시각") or 0))),
                 회차(), _PID, os.path.basename(새)))
    return 새, 말


def 안전쓰기(경로, 글, 인코딩="utf-8"):
    """텍스트 산출물을 안전하게 쓴다. (실제 경로, 보고 문장 목록)."""
    실제, 말 = 안전확보(경로)
    io.open(실제, "w", encoding=인코딩).write(글)
    표식남기기(실제)
    return 실제, 말

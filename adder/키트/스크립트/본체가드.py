# -*- coding: utf-8 -*-
"""**본체 보호** — 원본을 받는 도구(`dart_fetch` · `sec_fetch` · `dart_peer_사슬` …)가 본체(정본 키트)에 회차 원본을 쌓지 않게 한다.

이 도구들은 `_raw/` 를 **스크립트의 부모 폴더** 기준으로 잡는다. 회차 폴더는 본체를 통째로 복사해 쓰므로 제자리에
떨어지지만, 본체의 스크립트를 그대로 돌리면 정본에 떨어진다(실측: SEC 연결 시험이 `companyfacts.json` · 10-K 를 정본에 쌓았다).

본체를 가르는 표식(2026-10-16, S1 리뷰 — 종전에는 폴더 이름 「시작키트」 하나만 봤다)
  ① 폴더 이름이 `시작키트` 다 — 납품본 · 배포본의 본체(0단계가 「복사해 이름을 종목으로 바꾼다」로 시작한다)
  ② `회귀기준선/` 을 가진 폴더이고 그 위 어딘가에 `.git` 이 있다 — 개발 저장소의 본체(예: `구현/키트`).
     폴더째 복사한 회차에도 `회귀기준선/` 은 따라가지만 저장소 밖으로 복사하면 `.git` 은 따라가지 않는다
**폴더를 만드는 일은 이 판정 뒤에 한다** — 종전에는 import 때 `_raw/peers` · `_dartcache` 를 만들어, 멈추기도 전에 본체에 빈 폴더가 생겼다.
본체에서 정말 받아야 하면 환경변수 `YN_본체쓰기허용=1` 을 켠다.
"""
from __future__ import annotations

import os
import sys


def 본체인가(뿌리):
    뿌리 = os.path.abspath(뿌리)
    if os.path.basename(os.path.normpath(뿌리)) == "시작키트":
        return "폴더 이름이 「시작키트」"
    if os.path.isdir(os.path.join(뿌리, "회귀기준선")):
        d = os.path.dirname(뿌리)
        while True:
            if os.path.exists(os.path.join(d, ".git")):
                return "회귀기준선을 가진 저장소 안의 본체(%s)" % d
            위 = os.path.dirname(d)
            if 위 == d:
                break
            d = 위
    return None


def 본체면멈춘다(뿌리):
    까닭 = 본체인가(뿌리)
    if not 까닭:
        return
    sys.stderr.write(
        "\n[멈춤] **본체에서 원본을 받으려 했습니다** — %s.\n"
        "  이 스크립트는 `_raw/` 를 스크립트의 부모 폴더에 잡습니다 —\n"
        "  본체에서 돌리면 **정본에 회차 원본이 쌓입니다.**\n"
        "  이 폴더를 통째로 (저장소 밖으로) 복사해 **이름을 종목으로 바꾸고**(예: `삼성전자_DCF`)\n"
        "  그 폴더의 `스크립트/` 를 돌리십시오 — 0단계가 시키는 그대로입니다.\n"
        "  (본체에서 정말 받아야 하면 환경변수 `YN_본체쓰기허용=1` 을 켜십시오)\n" % 까닭)
    if os.environ.get("YN_본체쓰기허용") != "1":
        raise SystemExit(2)

# -*- coding: utf-8 -*-
"""숫자 서식 헬퍼 — 출력을 예쁘게 만들다 다섯 번 넘어진 자리의 처방 (집계 D1).

권고: %가 든 한글 문장은 % 포맷 대신 f-string이나 문자열 연결을 쓴다.
  나쁨:  "±5% 안" % ...        ← %가 포맷 지시자로 읽혀 터진다
  나쁨:  "%,.0f" % x           ← 파이썬에 없는 형식
  좋음:  f"매출 {콤마(x)} 백만달러 ({퍼센트(r)})"
"""


def 콤마(x, nd=0):
    return "-" if x is None else format(round(x, nd), ",")


def 퍼센트(x, nd=2):
    return "-" if x is None else ("%%.%df%%%%" % nd) % (x * 100)

# -*- coding: utf-8 -*-
"""고리검사 — 지은 워크북의 수식을 칸 단위로 따라가 고리(순환 참조)가 있는지 본다 (엑셀 안 씀. 설계/6_산식_설계.md 9-3 의 첫 겹).

  python 고리검사.py <xlsx> [<xlsx> …]          고리가 있는 워크북이 하나라도 있으면 종료 코드 1

짓기는 파일을 내기 전에 `검사wb(wb)` 를 돌린다 — 고리가 하나라도 있으면 「고리」 오류로 멈추고 파일을 내지 않는다.

수식마다 읽는 칸(범위는 칸마다 편다 — 열 전체 · 행 전체는 그 시트의 쓰인 범위까지)을 모아 「수식 칸 → 읽는 수식 칸」 그림을 그리고
강하게 이어진 덩어리(둘 이상의 칸이 서로를 읽거나 제 칸을 읽는 것)를 찾는다. INDEX(범위, n) 처럼 범위의 한 칸만 읽는 식도 범위 전체를
읽는 것으로 본다(넉넉하게 — 고리가 없다고 나오면 없다). 줄 단위가 아니라 칸 단위라, 직전 열을 읽는 굴림 식(기말 = 기초 + 증감)은 고리가 아니다.
W2 가 따로 지은 `W2/명세/고리검사.py` 를 생성기 안으로 옮긴 것이다(수식 글은 정규식으로 읽는다 — openpyxl 의 낱말 가르기보다 빠르다.
두 길이 같은 그림을 내는지는 시험 12 가 본다).
"""
import re
import sys

from openpyxl.utils import get_column_letter, column_index_from_string

_re글상수 = re.compile(r'"(?:[^"]|"")*"')
_칸 = r"\$?([A-Za-z]{1,3})\$?([0-9]{1,7})"
_re참조 = re.compile(
    r"(?<![A-Za-z0-9_.가-힣$!'])"
    r"(?:(?:'((?:[^']|'')+)'|([A-Za-z_가-힣][A-Za-z0-9_.가-힣]*))!)?"
    r"(?:" + _칸 + r"(?::" + _칸 + r")?"
    r"|\$?([A-Za-z]{1,3}):\$?([A-Za-z]{1,3})"
    r"|\$?([0-9]{1,7}):\$?([0-9]{1,7}))"
    r"(?![A-Za-z0-9_(.!])")


def 읽는칸(시트이름, 글, 크기):
    """수식 글 → 읽는 칸 [(시트, 열 번호, 행 번호)]. 크기 = {시트 이름: (끝 행, 끝 열)} — 그 밖의 시트를 가리키는 참조는 버린다."""
    칸 = []
    for m in _re참조.finditer(_re글상수.sub('""', 글)):
        시트 = (m.group(1) or "").replace("''", "'") or m.group(2) or 시트이름
        if 시트 not in 크기:
            continue
        끝행, 끝열 = 크기[시트]
        try:
            if m.group(3):
                c1, r1 = column_index_from_string(m.group(3).upper()), int(m.group(4))
                c2, r2 = (column_index_from_string(m.group(5).upper()), int(m.group(6))) if m.group(5) else (c1, r1)
            elif m.group(7):
                c1, c2, r1, r2 = column_index_from_string(m.group(7).upper()), column_index_from_string(m.group(8).upper()), 1, 끝행
            else:
                r1, r2, c1, c2 = int(m.group(9)), int(m.group(10)), 1, 끝열
        except ValueError:
            continue
        if c1 > c2:
            c1, c2 = c2, c1
        if r1 > r2:
            r1, r2 = r2, r1
        if r1 == r2 and c1 == c2:
            칸.append((시트, c1, r1))
            continue
        for r in range(r1, min(r2, 끝행) + 1):
            for c in range(c1, min(c2, 끝열) + 1):
                칸.append((시트, c, r))
    return 칸


def 덩어리(그림):
    """{칸: [읽는 칸 …]} → 강하게 이어진 덩어리 가운데 고리인 것(칸 둘 이상이거나 제 칸을 읽는 칸). 타잔 — 되부름 없이."""
    번호, 낮은, 쌓임, 위에, 낸, 셈 = {}, {}, [], set(), [], 0
    for 뿌리 in 그림:
        if 뿌리 in 번호:
            continue
        일 = [(뿌리, iter(그림[뿌리]))]
        번호[뿌리] = 낮은[뿌리] = 셈
        셈 += 1
        쌓임.append(뿌리)
        위에.add(뿌리)
        while 일:
            v, it = 일[-1]
            for w in it:
                if w not in 번호:
                    번호[w] = 낮은[w] = 셈
                    셈 += 1
                    쌓임.append(w)
                    위에.add(w)
                    일.append((w, iter(그림[w])))
                    break
                if w in 위에:
                    낮은[v] = min(낮은[v], 번호[w])
            else:
                일.pop()
                if 일:
                    낮은[일[-1][0]] = min(낮은[일[-1][0]], 낮은[v])
                if 낮은[v] == 번호[v]:
                    한 = []
                    while True:
                        w = 쌓임.pop()
                        위에.discard(w)
                        한.append(w)
                        if w == v:
                            break
                    if len(한) > 1 or v in 그림[v]:
                        낸.append(sorted(한))
    return 낸


def 수식칸들(wb):
    """워크북(openpyxl) → {(시트 이름, 열 번호, 행 번호): 수식 글}, {시트 이름: (끝 행, 끝 열)}"""
    수식, 크기 = {}, {}
    for ws in wb:
        크기[ws.title] = (ws.max_row, ws.max_column)
        for (r, c), 칸 in ws._cells.items():
            v = getattr(칸.value, "text", 칸.value)
            if isinstance(v, str) and v.startswith("="):
                수식[(ws.title, c, r)] = v
    return 수식, 크기


def 검사wb(wb):
    """→ (수식 칸 수, 읽는 줄 수, 고리 덩어리 목록 [[(시트, 열 번호, 행 번호) …] …])"""
    수식, 크기 = 수식칸들(wb)
    그림 = {k: [x for x in 읽는칸(k[0], v, 크기) if x in 수식] for k, v in 수식.items()}
    return len(수식), sum(len(x) for x in 그림.values()), 덩어리(그림)


def 검사(경로):
    import openpyxl
    return 검사wb(openpyxl.load_workbook(경로))


def 칸글(칸):
    return "%s!%s%d" % (칸[0], get_column_letter(칸[1]), 칸[2])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    나쁨 = 0
    for 경로 in sys.argv[1:]:
        n, 줄, 덩 = 검사(경로)
        나쁨 += bool(덩)
        print("%s — 수식 칸 %d · 읽는 줄 %d · 고리 %d개%s" % (
            경로[-60:], n, 줄, len(덩), "" if not 덩 else " ← " + "; ".join(" · ".join(칸글(x) for x in 한[:6]) for 한 in 덩[:3])))
    print("고리 검사 — 워크북 %d개 가운데 고리 있는 것 %d개" % (len(sys.argv) - 1, 나쁨))
    sys.exit(1 if 나쁨 else 0)

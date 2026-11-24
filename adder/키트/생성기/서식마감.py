# -*- coding: utf-8 -*-
"""서식마감 — 값을 부은 워크북의 서식을 마무리한다 (붓기 뒤 · 엑셀 재계산 앞).

쓰기:  python 서식마감.py <부은 xlsx> <좌표지도 json> <낼 xlsx> [--안쓰는줄 <행 ID 목록.json>] [--주당줄 <행 ID 목록.json>]

짓기(표준 서식 길)는 값이 없는 스캐폴드를 짓는다. 값을 보아야 정해지는 서식은 부은 뒤에 여기서 세운다.
수식과 값은 건드리지 않는다(서식 · 숨김 · 묶음 · 바닥글만 고친다). 엑셀을 쓰지 않는다.

  1. 붓기가 값을 쓴 서식 없는 칸 — 가정 파일이 명세의 입력 칸 밖에 값을 적은 칸(합계 줄의 출처 따위)이다. 열 종류로 가려 입력 스타일을 입힌다
     (긴 글 열 = 값_입력긴글 · 그 밖의 글 열과 글 값 = 값_입력글 · 숫자 = 값_입력 + 같은 줄의 숫자 서식).
     붓기가 칸에 직접 준 날짜 서식(평가기준일의 yyyy-mm-dd)은 표준 날짜 서식으로 맞춘다.
  2. 안 쓰는 예측 열 — 12번 기간 종료일 줄이 빈 예측 열을 시간축 시트 전부에서 묶어 접는다(열 묶음 수준 1 · 숨김).
     W2 뒤로 기간 열은 가정 파일의 기간에서 짓고 종료일은 생성기가 적는다 — 빈 예측 열이 없어 접을 것이 없다(옛 15열 스캐폴드를 받을 때만 일한다).
  3. 12번 시나리오 세 줄 — 세 줄의 값이 같은 가정은 세 줄을 접고(머리 줄에 접힘 표시), 다른 가정은 펴 둔다.
     세 줄이 모두 빈 가정(안 쓰는 가정)도 세 줄을 접는다.
  4. 바닥글 왼쪽 — 「대상회사 | 평가기준일 yyyy-mm-dd」(수식을 쓸 수 없는 자리라 글로 적는다).
  5. 안 쓰는 줄 — 부르는 쪽이 행 ID 목록을 주면(안쓰는줄=) 그 줄을 묶어 접는다(줄 묶음 수준 1 · 숨김. 그 안의 시나리오 세 줄은 수준 2).
     어느 줄이 안 쓰는 줄인지는 여기서 정하지 않는다 — 값이 비었다고 접으면 채워야 할 가정이 가려진다. 사용 표지(점검 설계 4절)나
     가정 파일의 선언을 읽는 쪽(붓기 · 워크북 마감)이 목록을 준다.
  6. 2번의 연도별 WACC 산정 줄 — 납품 배치가 묶어 접어 둔다(배치_납품.py 「접는줄」). 12번 「연도별 WACC 적용 여부」가 「사용」인 회차에만 편다.
  7. 구획 번호 — 안 쓰는 줄을 접어 구획이 통째로 숨으면, 로마 숫자는 보이는 구획에만 차례로 다시 매긴다(숨은 구획머리는 번호를 뗀다).
     접힌 구획 바로 위의 빈 줄(배치가 구획 사이에 넣은 줄)도 함께 접는다 — 빈 줄이 겹쳐 보이지 않게. (W6b)
  8. 주당 금액의 소수 자리 — 12번 「주당 금액 단위」가 원 · 엔이 아니면(달러 · 유로 등) 주당 금액 줄(단위 칸이 그 칸을 읽는 줄)의
     숫자 서식을 소수 둘째 자리로 바꾼다(0_결정 「L1 뒤」 1). 단위 칸이 없는 시트(15번)의 주당 금액 줄은 부르는 쪽이 준다(주당줄=). (W6b)

쪽 나눔(구획이 쪽 사이에서 갈리지 않게)은 여기서 하지 않는다 — 한 쪽에 드는 줄 수는 엑셀이 정하는 줄 높이에 달려 있어 파일만 보고는 셈할 수 없다.
엑셀로 재계산해 저장하는 단계가 쪽나눔.py 를 부른다(엑셀이 나눈 자리를 읽어 구획머리 앞으로 당긴다).

긴 글 칸의 줄 높이는 정하지 않는다 — 높이를 안 정한 줄은 엑셀이 열 때 줄바꿈된 글에 맞춘다(설계/2_배치_서식.md 4-1).
"""
import os
import re
import sys
import json
import datetime
from collections import OrderedDict

import openpyxl
from openpyxl.utils import get_column_letter as 열글자, column_index_from_string as 열번호
from openpyxl.worksheet.dimensions import ColumnDimension

import 서식훅
import 좌표지도

대상회사칸 = ("S12", 5, "값")        # 가정 번호 5 · 6 의 값 칸(붓기가 메타.회사명 · 메타.평가기준일을 적는 칸). 열은 그 줄 쓰임의 별칭으로 부른다
평가기준일칸 = ("S12", 6, "값")      # (열 ID 는 회차의 기간 축에 따라 달라진다 — FY2023A · H1 …)
기간종료일줄 = ("S12", 22)           # 기간 정의의 기간 종료일 줄 — 빈 예측 열은 안 쓰는 열이다
연도별WACC칸 = ("S12", 248, "값")    # 가정 번호 248 「연도별 WACC 적용 여부」의 값 칸 — 2번의 수렴 진행률 수식이 「사용」과 견준다
주당단위칸 = ("S12", 7, "값2")       # 12번 「주당 금액 단위」 — 원 · 엔이면 정수, 그 밖(달러 · 유로 …)은 소수 둘째 자리
정수통화 = ("원", "엔", "KRW", "JPY", "円")
_re구획번호 = re.compile(r"^([IVXLC]+)\.\s+(.*)$", re.S)
연도별WACC쓰는값 = ("사용",)
WACC산정줄 = ("S02R026", "S02R032")  # 2번의 연도별 WACC 산정 줄(첫 줄 · 끝 줄) — 배치_납품.py 의 「접는줄」과 같은 줄
값열종류 = ("실적", "예측", "영구", "값", "기타")
긴글열종류 = ("근거", "비고", "풀이")
글열종류 = 긴글열종류 + ("소비처", "방향", "방향점검", "역산", "보조", "점검칸")
숫자입는 = ("값_입력", "값_계산", "값_연결", "값_산출")


def 열펴기(ws):
    """여러 열을 한 항목으로 묶어 적은 열 속성(min~max)을 열마다 하나씩으로 편다 — 열 하나만 고칠 수 있게."""
    for 키, d in list(ws.column_dimensions.items()):
        lo, hi = d.min or 열번호(키), d.max or d.min or 열번호(키)
        if hi <= lo:
            continue
        del ws.column_dimensions[키]
        for k in range(lo, hi + 1):
            새 = ColumnDimension(ws, index=열글자(k), width=d.width, hidden=d.hidden, outlineLevel=d.outlineLevel,
                                collapsed=d.collapsed, bestFit=d.bestFit, customWidth=d.customWidth)
            새.min = 새.max = k
            ws.column_dimensions[열글자(k)] = 새


def _로마(n):
    낸 = ""
    for 값, 자 in ((100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= 값:
            낸 += 자
            n -= 값
    return 낸


def 구획번호다시(ws):
    """보이는 구획머리(「글_구획」 · 로마 숫자로 시작하는 이름)에만 차례로 번호를 다시 매긴다 → 바꾼 칸 수. 숨은 구획머리는 번호를 뗀다."""
    바꾼, 차례 = 0, 0
    for 줄 in ws.iter_rows():
        for 칸 in 줄[:4]:
            if 칸.style != "글_구획" or not isinstance(칸.value, str):
                continue
            m = _re구획번호.match(칸.value)
            if not m:
                continue
            if ws.row_dimensions[칸.row].hidden:
                새 = m.group(2)
            else:
                차례 += 1
                새 = "%s. %s" % (_로마(차례), m.group(2))
            if 새 != 칸.value:
                칸.value = 새
                바꾼 += 1
            break
    return 바꾼


def 마감(부은, 지도곳, 낼곳, 안쓰는줄=(), 주당줄=()):
    """부은 워크북 → 서식을 마무리한 워크북. → {"서식 없는 칸", "접은 열", "접은 묶음", "편 묶음", "바닥글", "접은 줄"}

    안쓰는줄 : 접어 숨길 줄의 행 ID 들(사용 표지 · 가정 파일의 선언을 읽는 쪽이 준다). 좌표 지도에 없는 ID 는 건너뛴다.
    주당줄   : 단위 칸이 없는 시트(15번)에서 주당 금액 서식을 입은 줄의 행 ID 들 — 표시 통화가 원 · 엔이 아니면 소수 둘째 자리로."""
    표준 = 서식훅._표준읽기(서식훅.표준경로)
    if 표준 is None:
        raise SystemExit("서식표준.py 가 없다: %s" % 서식훅.표준경로)
    지 = 좌표지도.읽기(지도곳)
    wb = openpyxl.load_workbook(부은)
    기본 = next((s.name for s in wb._named_styles if s.builtinId == 0), "Normal")
    if "값_입력" not in wb.named_styles:
        raise SystemExit("표준 서식 길로 지은 워크북이 아니다(명명 스타일 「값_입력」이 없다): %s" % 부은)
    시트of = {s["새이름"]: sid for sid, s in 지.시트.items() if s.get("새이름")}
    결 = OrderedDict([("서식 없는 칸", []), ("접은 열", OrderedDict()), ("접은 묶음", 0), ("편 묶음", 0), ("바닥글", None),
                     ("접은 줄", 0), ("날짜 서식을 맞춘 칸", []), ("연도별 WACC 줄", None), ("구획 번호", 0), ("주당 소수", None)])

    # 1. 붓기가 값을 쓴 서식 없는 칸
    for ws in wb.worksheets:
        sid = 시트of.get(ws.title)
        if sid is None:
            continue
        종 = {열번호(글): 지.시트[sid]["열종류"].get(cid) for cid, 글 in 지.시트[sid]["열ID"].items()}
        for 줄 in ws.iter_rows():
            for 칸 in 줄:
                if isinstance(칸, openpyxl.cell.cell.MergedCell):
                    continue
                if 칸.style != 기본 and 칸.number_format not in 표준.표준숫자서식 and (
                        isinstance(칸.value, (datetime.date, datetime.datetime)) or "yy" in str(칸.number_format).lower()):
                    칸.number_format = 표준.서식표["날짜"]      # 붓기가 직접 준 날짜 서식 → 표준 날짜 서식
                    결["날짜 서식을 맞춘 칸"].append("%s!%s" % (ws.title, 칸.coordinate))
                if 칸.value is None or 칸.style != 기본:
                    continue
                k = 종.get(칸.column)
                v = 칸.value
                if k == "이름":
                    칸.style = "글_행이름"
                elif k == "단위":
                    칸.style = "글_단위"
                elif k == "번호":
                    칸.style = "글_번호"
                elif k in 긴글열종류:
                    칸.style = "값_입력긴글"
                elif isinstance(v, str) and not v.startswith("="):
                    칸.style = "값_입력글"
                elif isinstance(v, str):
                    칸.style = "값_글"
                else:
                    서식 = next((c.number_format for c in 줄 if c.style in 숫자입는), None)
                    칸.style = "값_입력"
                    if isinstance(v, (datetime.date, datetime.datetime)):
                        칸.number_format = 표준.서식표["날짜"]
                    elif 서식:
                        칸.number_format = 서식
                결["서식 없는 칸"].append("%s!%s" % (ws.title, 칸.coordinate))

    # 2. 안 쓰는 예측 열
    안쓰는 = []
    s12 = 지.시트.get(기간종료일줄[0])
    if s12 and 지.행자리.get("%sR%03d" % 기간종료일줄) is not None:
        for cid, k in s12["열종류"].items():
            if k != "예측":
                continue
            이름, 자리 = 지.주소(기간종료일줄[0], 기간종료일줄[1], cid)
            if wb[이름][자리].value in (None, ""):
                안쓰는.append(cid)
    if 안쓰는:
        for ws in wb.worksheets:
            sid = 시트of.get(ws.title)
            if sid is None:
                continue
            한 = 지.시트[sid]
            열들 = sorted(열번호(한["열ID"][cid]) for cid in 안쓰는 if 한["열종류"].get(cid) == "예측" and cid in 한["열ID"])
            if not 열들:
                continue
            열펴기(ws)
            for k in 열들:
                d = ws.column_dimensions[열글자(k)]
                d.outlineLevel = max(d.outlineLevel or 0, 1)
                d.hidden = True
            for k in 열들:                      # 접힌 묶음의 요약 열(왼쪽 열)에 접힘 표시
                if k - 1 not in 열들 and k > 1:
                    ws.column_dimensions[열글자(k - 1)].collapsed = True
            ws.sheet_properties.outlinePr.summaryRight = False
            결["접은 열"][ws.title] = "%s:%s" % (열글자(열들[0]), 열글자(열들[-1])) if 열들[-1] - 열들[0] + 1 == len(열들) \
                else " ".join(열글자(k) for k in 열들)

    # 3. 12번 시나리오 세 줄 — 세 값이 같으면(또는 모두 비었으면) 접는다
    for sid, 묶음들 in (지.자료.get("가정묶음") or {}).items():
        한 = 지.시트.get(sid)
        if not 한 or not 한.get("새이름") or 한["새이름"] not in wb.sheetnames:
            continue
        ws = wb[한["새이름"]]
        값열 = [열번호(글) for cid, 글 in 한["열ID"].items() if 한["열종류"].get(cid) in ("실적", "예측", "영구")]
        for 머리, 세 in 묶음들:
            try:
                줄 = [지.가정행(sid, 번호)[1] for 번호 in 세]
                머리줄 = 지.가정행(sid, 머리)[1]
            except (KeyError, TypeError):
                continue
            if None in 줄 or 머리줄 is None or 줄 != list(range(머리줄 + 1, 머리줄 + 1 + len(줄))):
                continue                         # 머리 줄 바로 아래에 나란히 놓인 묶음만 접는다
            값 = [tuple(ws.cell(n, k).value for k in 값열) for n in 줄]
            같다 = all(v == 값[0] for v in 값[1:])
            for n in 줄:
                d = ws.row_dimensions[n]
                d.outlineLevel = max(d.outlineLevel or 0, 1)
                d.hidden = bool(같다)
            ws.row_dimensions[머리줄].collapsed = bool(같다)
            결["접은 묶음" if 같다 else "편 묶음"] += 1
        ws.sheet_properties.outlinePr.summaryBelow = False

    # 5. 안 쓰는 줄 — 받은 행 ID 를 묶어 접는다. 이미 묶인 줄(시나리오 세 줄)은 한 수준 안으로 들인다
    줄별 = OrderedDict()
    for rid in 안쓰는줄:
        n = 지.행자리.get(rid)
        한 = 지.시트.get(지.놓인시트(rid)) if n is not None else None
        if 한 and 한.get("새이름") in wb.sheetnames:
            줄별.setdefault(한["새이름"], set()).add(n)
    for 이름, 줄 in 줄별.items():
        ws = wb[이름]
        for n in sorted(줄):                    # 접는 구획머리 바로 위의 빈 줄(배치가 구획 사이에 넣은 줄) — 빈 줄이 겹쳐 보이지 않게 함께 접는다
            if n - 1 not in 줄 and n > 1 and any(c.style == "글_구획" for c in ws[n][:4]) and \
                    all(c.value in (None, "") for c in ws[n - 1]):
                줄.add(n - 1)
        for n in sorted(줄):
            d = ws.row_dimensions[n]
            d.outlineLevel = min(7, (d.outlineLevel or 0) + 1)
            d.hidden = True
            if n - 1 not in 줄 and n > 1:      # 접힌 묶음의 요약 줄(바로 위 줄)에 접힘 표시
                ws.row_dimensions[n - 1].collapsed = True
        ws.sheet_properties.outlinePr.summaryBelow = False
        결["접은 줄"] += len(줄)

    # 6. 2번의 연도별 WACC 산정 줄 — 배치가 묶어 둔 줄만 다룬다(묶이지 않았으면 그대로 둔다). 스위치 칸을 못 찾으면 접힌 채로 둔다
    n1, n2 = 지.행자리.get(WACC산정줄[0]), 지.행자리.get(WACC산정줄[1])
    한 = 지.시트.get(지.놓인시트(WACC산정줄[0])) if n1 is not None and n2 is not None else None
    if 한 and 한.get("새이름") in wb.sheetnames and 1 < n1 <= n2 and 지.놓인시트(WACC산정줄[1]) == 지.놓인시트(WACC산정줄[0]):
        ws = wb[한["새이름"]]
        if all(ws.row_dimensions[n].outlineLevel for n in range(n1, n2 + 1)):
            try:
                이름, 자리 = 지.주소(*연도별WACC칸)
                쓴다 = bool(자리) and wb[이름][자리].value in 연도별WACC쓰는값
            except (KeyError, TypeError, ValueError):
                쓴다 = False
            요약 = n2 + 1 if ws.sheet_properties.outlinePr.summaryBelow else n1 - 1
            for n in range(n1, n2 + 1):
                ws.row_dimensions[n].hidden = not 쓴다
            ws.row_dimensions[요약].collapsed = not 쓴다
            결["연도별 WACC 줄"] = "폈다" if 쓴다 else "접어 두었다"

    # 7. 구획 번호 — 접힌 구획이 있는 시트만 다시 매긴다
    for 이름 in 줄별:
        결["구획 번호"] += 구획번호다시(wb[이름])

    # 8. 주당 금액의 소수 자리 — 표시 통화가 원 · 엔이 아니면
    try:
        이름, 자리 = 지.주소(*주당단위칸)
        단위 = wb[이름][자리].value if 자리 else None
        단위칸 = "%s!%s" % (이름, 자리) if 자리 else None
    except (KeyError, TypeError, ValueError):
        단위, 단위칸 = None, None
    if isinstance(단위, str) and 단위.strip() and 단위.strip() not in 정수통화 and 단위칸:
        이름, 자리 = 단위칸.split("!")
        참조 = ("='%s'!$%s$%s" % (이름, re.match(r"[A-Z]+", 자리).group(0), re.search(r"\d+", 자리).group(0)),
              "=$%s$%s" % (re.match(r"[A-Z]+", 자리).group(0), re.search(r"\d+", 자리).group(0)))
        정수, 소수 = 표준.서식표["주당"], 표준.서식표["주당소수"]
        n칸 = 0
        for ws in wb.worksheets:
            sid = 시트of.get(ws.title)
            if sid is None:
                continue
            단위열 = [열번호(글) for cid, 글 in 지.시트[sid]["열ID"].items() if 지.시트[sid]["열종류"].get(cid) == "단위"]
            줄들 = set()
            if 단위열:
                for r in range(1, ws.max_row + 1):
                    v = ws.cell(r, 단위열[0]).value
                    if isinstance(v, str) and v.strip() in 참조[:1] + ((참조[1],) if ws.title == 이름 else ()):
                        줄들.add(r)
            for rid in 주당줄:
                if 지.놓인시트(rid) == sid and 지.행자리.get(rid) is not None:
                    줄들.add(지.행자리[rid])
            for r in 줄들:
                for c in ws[r]:
                    if c.number_format == 정수 and c.style in 숫자입는:
                        c.number_format = 소수
                        n칸 += 1
        결["주당 소수"] = "%s — %d칸" % (단위.strip(), n칸)

    # 4. 바닥글 왼쪽
    try:
        이름, 자리 = 지.주소(*대상회사칸)
        회사 = wb[이름][자리].value
        이름, 자리 = 지.주소(*평가기준일칸)
        기준일 = wb[이름][자리].value
    except (KeyError, TypeError):
        회사 = 기준일 = None
    if isinstance(기준일, (datetime.date, datetime.datetime)):
        기준일 = 기준일.strftime("%Y-%m-%d")
    if isinstance(회사, str) and 회사 and not 회사.startswith("="):
        글 = 회사.replace("&", "&&") + (" | 평가기준일 %s" % 기준일 if isinstance(기준일, str) and 기준일 else "")
        for ws in wb.worksheets:
            ws.oddFooter.left.text = 글
            ws.oddFooter.left.size, ws.oddFooter.left.font = 8, 표준.글꼴이름 + ",보통"
        결["바닥글"] = 글
    wb.save(낼곳)
    return 결


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    인자 = sys.argv[1:]
    안쓰는, 주당 = (), ()
    if "--안쓰는줄" in 인자:
        i = 인자.index("--안쓰는줄")
        with open(인자[i + 1], encoding="utf-8") as f:
            안쓰는 = json.load(f)
        del 인자[i:i + 2]
    if "--주당줄" in 인자:
        i = 인자.index("--주당줄")
        with open(인자[i + 1], encoding="utf-8") as f:
            주당 = json.load(f)
        del 인자[i:i + 2]
    if len(인자) != 3:
        raise SystemExit(__doc__)
    for p in 인자[:2]:
        if not os.path.exists(p):
            print("파일이 없다: %s" % p)
            sys.exit(2)
    결 = 마감(*인자, 안쓰는줄=안쓰는, 주당줄=주당)
    print("서식을 마무리했다: %s" % 인자[2])
    print("  서식 없는 칸에 입력 스타일 %d칸%s" % (len(결["서식 없는 칸"]), " (%s …)" % ", ".join(결["서식 없는 칸"][:4]) if 결["서식 없는 칸"] else ""))
    print("  날짜 서식을 표준으로 맞춘 칸 %d%s" % (len(결["날짜 서식을 맞춘 칸"]), " (%s)" % ", ".join(결["날짜 서식을 맞춘 칸"][:4]) if 결["날짜 서식을 맞춘 칸"] else ""))
    print("  접은 예측 열: %s" % (" · ".join("%s %s" % kv for kv in 결["접은 열"].items()) or "없음"))
    print("  시나리오 세 줄: 접은 가정 %d · 편 가정 %d" % (결["접은 묶음"], 결["편 묶음"]))
    print("  안 쓰는 줄: %s" % ("접은 줄 %d" % 결["접은 줄"] if 안쓰는 else "받은 목록 없음"))
    print("  2번의 연도별 WACC 산정 줄: %s" % (결["연도별 WACC 줄"] or "묶음이 없다(납품 배치로 지은 것이 아니다)"))
    print("  구획 번호를 다시 매긴 칸: %d" % 결["구획 번호"])
    print("  주당 금액 소수 둘째 자리: %s" % (결["주당 소수"] or "아니다(원 · 엔 — 정수)"))
    print("  바닥글 왼쪽: %s" % (결["바닥글"] or "적지 않았다(대상회사 칸이 비었다)"))

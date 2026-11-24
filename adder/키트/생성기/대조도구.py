# -*- coding: utf-8 -*-
"""대조도구 — 옛 파일과 새 파일을 좌표 지도를 거쳐 칸 단위로 견준다.

  글대조   : 수식 글·상수·글 (시험 가). 옮겨 지은 파일이면 옛 수식을 새 좌표로 옮긴 뒤 견준다.
  서식대조 : 글꼴·채움·테두리·맞춤·숫자 서식, 병합, 유효성, 틀 고정, 열 폭, 행 높이 (참고)
             값이 있는 칸은 서식이 없어도 견준다(서식 없는 칸은 통합문서의 기본 글꼴로 보인다).
  값대조   : 엑셀로 재계산한 값 (시험 나). 글을 내는 수식 칸도 판정에 든다(글이 다르면 「다른 칸」).
  시나리오바꾸기 : 시나리오 선택 칸을 바꾼 사본을 만든다(값 대조를 스위치 세 값에서 돌릴 때).

줄이 다른 시트로 옮겨진 배치에서는 칸마다 「그 칸이 놓인 시트」를 좌표 지도에 물어 견준다.
"""
import re
import math
import datetime
from collections import Counter

import openpyxl
from openpyxl.cell.cell import MergedCell
from openpyxl.worksheet.formula import ArrayFormula

import 좌표지도
from 공통 import 서식글, 열글자


def _정규(수식):
    """수식 글의 공백을 지우고 대문자로 — 견주기만을 위한 것."""
    return re.sub(r"\s+", "", 수식).upper()


def 글대조(옛경로, 새경로, 지도경로, 수식옮겨견주기=False):
    지 = 좌표지도.읽기(지도경로)
    옛, 새 = openpyxl.load_workbook(옛경로), openpyxl.load_workbook(새경로)
    결 = Counter()
    다른칸 = []
    닿은 = set()
    for ws in 옛.worksheets:
        for (r, c), 칸 in ws._cells.items():
            if 칸.value is None or isinstance(칸, MergedCell):
                continue
            새이름, 주소 = 지.새주소(ws.title, "%s%d" % (열글자(c), r))
            if 주소 is None:
                결["뺀칸"] += 1
                continue
            결["견준칸"] += 1
            닿은.add((새이름, 주소))
            a, b = 칸.value, 새[새이름][주소].value
            종류 = "수식" if 칸.data_type == "f" else ("글" if isinstance(a, str) else "숫자")
            결[종류] += 1
            if isinstance(a, ArrayFormula):          # 배열 수식은 (범위, 수식) 글로 견준다
                a = "%s|%s" % (a.ref, a.text)
                b = "%s|%s" % (b.ref, b.text) if isinstance(b, ArrayFormula) else b
            elif 종류 == "수식" and 수식옮겨견주기:
                a = 지.수식옮기기(a, ws.title, "%s%d" % (열글자(c), r))
            if a == b and type(a) is type(b):
                결["그대로같음"] += 1
            elif isinstance(a, str) and isinstance(b, str) and _정규(a) == _정규(b):
                결["정규화뒤같음"] += 1
            else:
                결["다름"] += 1
                결["다름·" + 종류] += 1
                if len(다른칸) < 50:
                    다른칸.append({"시트": ws.title, "옛칸": "%s%d" % (열글자(c), r), "새칸": 주소,
                                 "옛": repr(a)[:120], "새": repr(b)[:120]})
    # 새 파일에만 있는 값(배치가 끼운 새 줄·새 열은 뺀다)
    새줄 = {(지.시트[sid]["새이름"], n) for rid, (sid, n) in 지.자료.get("새줄", {}).items()}
    for wn in 새.worksheets:
        for (r, c), 칸 in wn._cells.items():
            if 칸.value is None or isinstance(칸, MergedCell):
                continue
            if (wn.title, "%s%d" % (열글자(c), r)) not in 닿은 and (wn.title, r) not in 새줄:
                결["새파일에만"] += 1
    return {"견준칸": 결["견준칸"], "수식": 결["수식"], "글": 결["글"], "숫자": 결["숫자"],
            "그대로같음": 결["그대로같음"], "정규화뒤같음": 결["정규화뒤같음"], "다름": 결["다름"],
            "다름·수식": 결["다름·수식"], "다름·글": 결["다름·글"], "다름·숫자": 결["다름·숫자"],
            "뺀칸": 결["뺀칸"], "새파일에만": 결["새파일에만"], "다른칸": 다른칸}


def 서식대조(옛경로, 새경로, 지도경로):
    지 = 좌표지도.읽기(지도경로)
    옛, 새 = openpyxl.load_workbook(옛경로), openpyxl.load_workbook(새경로)
    수, 보기 = Counter(), []

    def 다름(종류, 글):
        수[종류 + " 다름"] += 1
        if len(보기) < 40:
            보기.append("%s: %s" % (종류, 글))

    def 유효표(w, 옛시트):
        표 = {}
        for dv in w.data_validations.dataValidation:
            for g in dv.sqref.ranges:
                for r in range(g.min_row, g.max_row + 1):
                    for c in range(g.min_col, g.max_col + 1):
                        주 = "%s%d" % (열글자(c), r)
                        if 옛시트:
                            새시트, 주 = 지.새주소(옛시트, 주)
                            if 새시트 != 지.새시트(옛시트):      # 다른 시트로 옮긴 줄의 칸
                                continue
                        표[주] = (dv.type, dv.formula1, dv.allow_blank)
        return 표

    for ws in 옛.worksheets:
        wn = 새[지.새시트(ws.title)]
        기억 = {}
        for (r, c), 칸 in ws._cells.items():
            # 서식이 없어도 값이 있는 칸은 견준다 — 통합문서의 기본 글꼴로 보이는 칸이다
            if isinstance(칸, MergedCell) or not (칸.has_style or 칸.value is not None):
                continue
            새시트, 주소 = 지.새주소(ws.title, "%s%d" % (열글자(c), r))
            if 주소 is None:
                continue
            수["서식 견준 칸"] += 1
            if not 칸.has_style:
                수["서식 없이 값만 있는 칸(견준 칸에 든다)"] += 1
            새칸 = 새[새시트][주소]
            키 = (tuple(칸._style or ()), tuple(새칸._style or ()))      # 서식이 전혀 없는 칸은 _style 이 None 이다(새 파일에서 서식을 뗀 칸)
            if 키 not in 기억:
                a, b = 서식글(칸), 서식글(새칸)
                기억[키] = [k for k in a if a[k] != b[k]]
            if 기억[키]:
                다름("칸 서식", "%s!%s%d → %s (%s)" % (ws.title, 열글자(c), r, 주소, ",".join(기억[키])))
        # 병합
        옛병합 = set()
        for m in ws.merged_cells.ranges:
            시a, a = 지.새주소(ws.title, "%s%d" % (열글자(m.min_col), m.min_row))
            시b, b = 지.새주소(ws.title, "%s%d" % (열글자(m.max_col), m.max_row))
            if 시a == wn.title and 시b == wn.title and a and b:      # 다른 시트로 옮긴 줄 · 뺀 줄의 병합은 여기서 견주지 않는다
                옛병합.add("%s:%s" % (a, b))
        새병합 = {str(m) for m in wn.merged_cells.ranges}
        수["병합 견준 수"] += len(옛병합)
        for x in 옛병합 ^ 새병합:
            다름("병합", "%s %s" % (ws.title, x))
        # 유효성: 칸마다 (종류, 목록, 빈칸 허용)
        a, b = 유효표(ws, ws.title), 유효표(wn, None)
        수["유효성 견준 칸"] += len(a)
        for k in set(a) | set(b):
            if a.get(k) != b.get(k):
                다름("유효성", "%s %s %s / %s" % (ws.title, k, a.get(k), b.get(k)))
        # 틀 고정
        if ws.freeze_panes:
            수["틀 고정 견준 수"] += 1
            if 지.새주소(ws.title, ws.freeze_panes) != (wn.title, wn.freeze_panes):
                다름("틀 고정", "%s %s → %s" % (ws.title, ws.freeze_panes, wn.freeze_panes))
        elif wn.freeze_panes:
            다름("틀 고정", "%s 없음 → %s" % (ws.title, wn.freeze_panes))
        # 열 폭
        for 키, d in ws.column_dimensions.items():
            for n in range(d.min, d.max + 1):
                새열 = 지.열(ws.title, 열글자(n))
                수["열 폭 견준 수"] += 1
                if 새열 and (wn.column_dimensions[새열].width if 새열 in wn.column_dimensions else None) != d.width:
                    다름("열 폭", "%s %s" % (ws.title, 열글자(n)))
        # 행 높이
        sid = 지.sid(ws.title)
        for r, d in ws.row_dimensions.items():
            if d.height is None:
                continue
            n = 지.행("%sR%03d" % (sid, r))
            수["행 높이 견준 수"] += 1
            wr = 새[지.시트[지.놓인시트("%sR%03d" % (sid, r))]["새이름"]] if n else wn      # 줄이 놓인 시트
            if n and (wr.row_dimensions[n].height if n in wr.row_dimensions else None) != d.height:
                다름("행 높이", "%s %d" % (ws.title, r))
        # 탭 색·눈금선
        if (ws.sheet_properties.tabColor.rgb if ws.sheet_properties.tabColor else None) != \
                (wn.sheet_properties.tabColor.rgb if wn.sheet_properties.tabColor else None):
            다름("탭 색", ws.title)
        if ws.sheet_view.showGridLines != wn.sheet_view.showGridLines:
            다름("눈금선", ws.title)
    return {"수": dict(수), "보기": 보기}


def _같은값(a, b, 허용):
    """→ (같은가, 종류)"""
    if a is None and b is None:
        return True, "빈칸"
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b, "참거짓"
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if a == b:
            return True, "숫자"
        if math.isnan(a) and math.isnan(b):
            return True, "숫자"
        return abs(a - b) <= 허용 * max(abs(a), abs(b)), "숫자"
    날 = (datetime.datetime, datetime.date, datetime.time)   # 값 0 에 날짜 서식이면 time(0,0) 으로 읽힌다
    if isinstance(a, 날) or isinstance(b, 날):
        return type(a) is type(b) and a == b, "날짜"
    if isinstance(a, str) and isinstance(b, str):
        return a == b, ("오류값" if a.startswith("#") else "글")
    return False, "종류 다름"


def 값대조(옛값경로, 새값경로, 옛수식경로, 지도경로, 허용=1e-9, 제외=()):
    """엑셀로 재계산해 저장한 두 파일의 값을 대응 칸끼리 견준다.

    옛값경로·새값경로 : 재계산해 저장한 파일(값 캐시를 읽는다)
    옛수식경로         : 옛 파일(어느 칸이 수식인지 본다)
    글을 내는 수식 칸도 판정에 든다 — 글이 다르면 「다른 칸」에 더한다(판정 글 · 시점 머리 따위가 여기 든다).
    수는 따로도 센다: 「견준 칸」 = 숫자·날짜·빈 결과·상수 칸, 「글을 내는 수식 칸」 = 글 칸, 「판정에 든 칸」 = 둘의 합.
    제외 : 일부러 바꾼 칸 {(옛 시트 이름, 옛 주소)} — 견주지 않고 수만 센다.
    """
    지 = 좌표지도.읽기(지도경로)
    옛값 = openpyxl.load_workbook(옛값경로, data_only=True)
    새값 = openpyxl.load_workbook(새값경로, data_only=True)
    옛식 = openpyxl.load_workbook(옛수식경로)
    수 = Counter()
    다른칸, 글다른칸 = [], []
    for ws in 옛값.worksheets:
        wf = 옛식[ws.title]
        자리 = set(ws._cells) | {k for k, v in wf._cells.items() if v.data_type == "f"}
        for (r, c) in sorted(자리):
            칸 = ws._cells.get((r, c))
            if isinstance(칸, MergedCell):
                continue
            식칸 = wf._cells.get((r, c))
            수식인가 = 식칸 is not None and 식칸.data_type == "f"
            a = 칸.value if 칸 is not None else None
            if a is None and not 수식인가:
                continue
            옛주소 = "%s%d" % (열글자(c), r)
            새시트, 주소 = 지.새주소(ws.title, 옛주소)
            if 주소 is None:
                수["뺀 줄·열의 칸"] += 1
                continue
            if (ws.title, 옛주소) in 제외:
                수["일부러 바꾼 칸(견주지 않음)"] += 1
                continue
            b = 새값[새시트][주소].value
            같, 종류 = _같은값(a, b, 허용)
            갈래 = ("수식" if 수식인가 else "상수") + "·" + 종류
            수["판정에 든 칸"] += 1
            if 수식인가 and 종류 == "글":
                수["글을 내는 수식 칸"] += 1
                수["글을 내는 수식 칸 — 글이 " + ("같음" if 같 else "다름")] += 1
                if not 같:
                    수["다른 칸"] += 1
                    수["다름 — " + 갈래] += 1
                    if len(글다른칸) < 30:
                        글다른칸.append({"시트": ws.title, "옛칸": 옛주소, "새칸": 주소, "옛": str(a)[:100], "새": str(b)[:100]})
                continue
            수["견준 칸"] += 1
            수[갈래] += 1
            if not 같:
                수["다른 칸"] += 1
                수["다름 — " + 갈래] += 1
                if len(다른칸) < 60:
                    다른칸.append({"시트": ws.title, "옛칸": 옛주소, "새칸": 주소, "옛": repr(a)[:60], "새": repr(b)[:60]})
    수.setdefault("다른 칸", 0)
    return {"수": dict(수), "다른칸": 다른칸, "글다른칸": 글다른칸, "허용": 허용}


시나리오들 = ("비관", "기준", "낙관")
시나리오칸 = ("S12", 12, "값")            # 시나리오 선택 칸 — 12번 시트 12번 줄(설정)의 값 칸. 옛 주소는 12!D12


def 시나리오바꾸기(읽을, 낼, 시나리오, 지도경로=None):
    """워크북의 시나리오 선택 칸을 바꾼 사본을 낸다(수식은 그대로 — 엑셀로 재계산해야 값이 바뀐다).

    지도경로 를 주면 새 배치의 워크북(선택 칸의 자리를 지도에 묻는다), 안 주면 옛 배치의 워크북(12!D12).
    """
    wb = openpyxl.load_workbook(읽을)
    if 지도경로:
        시트, 주소 = 좌표지도.읽기(지도경로).주소(*시나리오칸)
    else:
        시트, 주소 = "12. 가정_시나리오", "D12"
    if wb[시트][주소].value not in 시나리오들:
        raise ValueError("시나리오 선택 칸이 아니다: %s!%s = %r" % (시트, 주소, wb[시트][주소].value))
    wb[시트][주소].value = 시나리오
    wb.save(낼)
    return 낼

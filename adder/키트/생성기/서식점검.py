# -*- coding: utf-8 -*-
"""서식점검 — 지은 워크북의 서식이 표준(서식표준.py)을 벗어난 곳을 세어 낸다.

쓰기:  python 서식점검.py <xlsx> [--자세히] [--보기 N] [--json <낼 json>]
       종료 코드: 0 = 벗어난 곳 0 · 1 = 하나라도 있다 · 2 = 파일을 못 읽었다

워크북만 읽는다(명세 · 배치 · 좌표 지도를 읽지 않는다 — 짓기와 다른 눈으로 본다). 표준 서식 길로 지은 워크북에서 전부 0 이 목표다.
엑셀로 재계산해 캐시 값이 든 파일이면 수식 칸의 값(숫자 · 글)까지 잰다. 캐시 값이 없는 수식 칸은 폭 · 글 서식을 잴 수 없어 건너뛰고 그 수를 알린다.

세는 것
  직접 서식            값이나 서식이 있는데 명명 스타일이 없는 칸 · 명명 스타일 위에 허용된 덧씌움 밖의 서식을 준 칸.
                       허용된 덧씌움은 넷: 숫자 서식(값 스타일에 서식표의 것) · 소계선/합계선(위 가는 실선 · 아래 이중선) · 들여쓰기 · 굵기.
                       날짜 값의 날짜 서식도 받는다.
  표준 밖 숫자 서식    서식표에 없는 숫자 서식
  표준 밖 글꼴         본문 글꼴(한 가지 · 한 크기)과 제목 크기 밖의 글꼴
  표준 밖 색           글자 · 바탕 · 선 · 탭 색이 표준(입력 파랑 + 연노랑 · 계산 검정 · 다른 시트 참조 초록 · 무채색) 밖.
                       조건부 서식은 판정 칸(점검_표시)에만, 판정 색(Error 빨강 · Review 주황)만.
  폭을 넘는 글         줄바꿈하지 않는 칸의 글이 흘러갈 빈 칸까지 합친 폭을 넘는다 · 행 이름이 이름 열을 넘는다 · 숫자가 열 폭을 넘는다(####)
  인쇄 설정 없는 시트  방향 · 폭 1쪽 맞춤 · 인쇄 영역 · 제목 행 반복 · 바닥글(시트 이름 · 쪽) 가운데 빠진 것이 있는 시트
  유효성 없는 선택 칸  선택 칸(값_선택)에 목록 유효성이 없다 · 목록 유효성이 걸렸는데 선택 칸이 아니다 ·
                       수식이 글 상수와 견주는 입력 칸에 목록 유효성이 없다
  숫자인데 글 서식     숫자 값에 글 서식(@) · 값 칸에 글로 넣은 숫자(「5.72x」 같은 것)
  서식 없는 숫자       값 칸(글 값 칸 포함)의 숫자가 일반(General) 서식이다(줄에 「서식」이 빠졌다)
  시트 공통            틀 고정이 없다 · 눈금선이 켜졌다 · 확대 비율이 사양과 다르다 · 탭 색이 없다 · 제목 줄 밖의 병합 ·
                       폭을 안 정한 열 · 탭 이름이 시트표에 없다 · 시트 순서가 시트표와 다르다
"""
import os
import re
import sys
import json
import datetime
from collections import OrderedDict

import openpyxl
from openpyxl.utils import get_column_letter as 열글자, column_index_from_string as 열번호
from openpyxl.utils.cell import range_boundaries

import 서식훅

갈래들 = ("직접 서식", "표준 밖 숫자 서식", "표준 밖 글꼴", "표준 밖 색", "폭을 넘는 글", "인쇄 설정 없는 시트",
        "유효성 없는 선택 칸", "숫자인데 글 서식", "서식 없는 숫자", "시트 공통")
입력스타일 = ("값_입력", "값_입력글", "값_입력긴글")
값스타일 = ("값_입력", "값_계산", "값_연결", "값_산출")
여유 = 1.0             # 칸 안쪽 여백으로 치는 폭(열 폭 단위)
이름여유 = 2.0         # 행 이름은 이름 열 폭에서 이만큼 뺀 것이 한도다(폭 38 → 한도 36 — 설계/2_배치_서식.md 4-2)
들여폭 = 1.5           # 들여쓰기 한 단이 먹는 폭
_re숫자글 = re.compile(r"^[+\-−(]?\d[\d,]*(\.\d+)?\)?\s*(%|%p|x|배|원|백만원|억원|천원)?$")
# 수식 속에서 글 상수와 견주는 칸 참조 — 「'시트'!$D$5="기중"」 「D5<>"미사용"」 「"기중"=D5」 「($J$7:$J$15="명시적 제외")」(범위째)
_칸 = r"\$?([A-Z]{1,3})\$?(\d+)"
_re참조 = r"(?:'((?:[^']|'')+)'!|([A-Za-z0-9_가-힣.]+)!)?" + _칸 + r"(?::" + _칸 + r")?"
_re뒤견줌 = re.compile(r"(?<![A-Za-z0-9_$:!'.])" + _re참조 + r'\s*(?:=|<>)\s*"((?:[^"]|"")*)"')
_re앞견줌 = re.compile(r'"((?:[^"]|"")*)"\s*(?:=|<>)\s*' + _re참조 + r"(?![\d:(A-Za-z])")


def _rgb(색):
    """openpyxl 의 Color → 여섯 자리 RGB(대문자). 없으면 None, 테마 · 색 번호면 "테마" · "번호"."""
    if 색 is None:
        return None
    if 색.type == "rgb":
        v = 색.rgb
        return v[-6:].upper() if isinstance(v, str) else None
    if 색.type == "theme":
        return "테마%s" % 색.theme
    if 색.type == "indexed":
        return None if 색.indexed in (64, 65) else "번호%s" % 색.indexed      # 64 · 65 = 시스템 기본(자동)
    return None


def _서식글(nf):
    """숫자 서식 글 — 엑셀이 저장하면서 괄호 · 붙임표 앞에 붙인 역빗금을 떼어 견준다."""
    return (nf or "General").replace(chr(92), "")


def _바탕색(fill):
    if fill is None or fill.fill_type in (None, "none"):
        return None
    return _rgb(fill.fgColor) or _rgb(fill.bgColor)


def _선(side):
    return (side.style if side is not None else None) or None


def _숫자글(v, 서식):
    """숫자 값이 그 서식으로 보이는 글의 길이(환산 폭). 표준 서식만 가늠한다."""
    if isinstance(v, bool):
        return 5
    if isinstance(v, (datetime.date, datetime.datetime)):
        return 10
    if not isinstance(v, (int, float)):
        return 0
    음 = v < 0
    a = abs(v)
    if 서식 in ("@", "General"):
        글 = repr(round(a, 10)).rstrip("0").rstrip(".") if isinstance(v, float) else str(a)
        return min(len(글), 11) + (1 if 음 else 0)      # 일반 서식은 엑셀이 폭에 맞춰 줄인다(11자리까지)
    if "yy" in 서식:
        return 10
    첫 = 서식.split(";")[0]
    소수 = len(re.sub(r"[^0#]", "", 첫.split(".")[1])) if "." in 첫 else 0
    if "%" in 첫:
        a *= 100
    글 = ("{:,.%df}" % 소수).format(a) if "," in 첫 else ("{:.%df}" % 소수).format(a)
    if "%" in 첫:
        글 += "%"
    if '"p"' in 첫:
        글 += "p"
    if 음:
        글 = "(" + 글 + ")" if ";" in 서식 else "-" + 글
    return len(글) - 0.5 * sum(글.count(c) for c in ",.()")      # 쉼표 · 마침표 · 괄호는 숫자 폭의 절반쯤이다


class 점검기:
    def __init__(self, 경로, 표준=None):
        self.경로 = 경로
        self.표준 = 표준 or 서식훅._표준읽기(서식훅.표준경로)
        if self.표준 is None:
            raise SystemExit("서식표준.py 가 없다: %s" % 서식훅.표준경로)
        self.찾은 = OrderedDict((갈, []) for 갈 in 갈래들)
        self.수 = OrderedDict([("시트", 0), ("칸", 0), ("수식 칸", 0), ("캐시 값 있는 수식 칸", 0)])
        self._판 = {}

    def 적기(self, 갈래, 시트, 자리, 설명):
        self.찾은[갈래].append("%s!%s — %s" % (시트, 자리, 설명) if 자리 else "%s — %s" % (시트, 설명))

    # ── 칸의 서식 ──
    def _칸판정(self, wb, 칸):
        """칸의 서식 번호 묶음 → [(갈래, 설명) …]. 같은 묶음은 한 번만 따진다."""
        키 = (tuple(칸._style), 칸.style)
        if 키 in self._판:
            return self._판[키]
        표 = self.표준
        낱 = []
        이름 = 칸.style
        f, 채, 선, 맞, nf = 칸.font, 칸.fill, 칸.border, 칸.alignment, _서식글(칸.number_format)
        # 표준 밖 숫자 서식 · 글꼴 · 색 — 스타일이 무엇이든 본다
        if nf not in 표.표준숫자서식:
            낱.append(("표준 밖 숫자 서식", "숫자 서식 %s" % nf))
        if (f.name, f.sz) not in 표.표준글꼴:
            낱.append(("표준 밖 글꼴", "글꼴 %s %s" % (f.name, f.sz)))
        글색 = _rgb(f.color)
        if 글색 is not None and 글색 not in 표.표준글자색:
            낱.append(("표준 밖 색", "글자색 %s" % 글색))
        바 = _바탕색(채)
        if 바 is not None and 바 not in 표.표준바탕:
            낱.append(("표준 밖 색", "바탕색 %s" % 바))
        for 쪽 in ("left", "right", "top", "bottom"):
            s = getattr(선, 쪽)
            c = _rgb(s.color) if s is not None and s.style else None
            if c is not None and c not in 표.표준선색:
                낱.append(("표준 밖 색", "선 색 %s" % c))
                break
        # 직접 서식
        if 이름 not in 표.스타일이름:
            기본 = self.기본스타일
            다름 = []
            if 이름 != 기본.name:
                다름.append("표준에 없는 스타일 「%s」" % 이름)
            if f != 기본.font:
                다름.append("글꼴")
            if 바 is not None:
                다름.append("바탕")
            if any(_선(getattr(선, 쪽)) for 쪽 in ("left", "right", "top", "bottom")):
                다름.append("선")
            if nf != "General":
                다름.append("숫자 서식")
            if 맞.horizontal or 맞.wrap_text or 맞.indent or (맞.vertical not in (None, "bottom", "center")):
                다름.append("맞춤")
            낱.append(("직접 서식?" if not 다름 else "직접 서식", "명명 스타일 없음" + (" (%s)" % " · ".join(다름) if 다름 else "")))
        else:
            본 = wb._named_styles[이름]
            다름 = []
            bf = 본.font
            if (f.name, f.sz, _rgb(f.color), bool(f.i), f.u, bool(f.strike)) != (
                    bf.name, bf.sz, _rgb(bf.color), bool(bf.i), bf.u, bool(bf.strike)):
                다름.append("글꼴")
            elif bool(f.b) != bool(bf.b) and bool(bf.b):
                다름.append("굵기를 뗌")
            if _바탕색(채) != _바탕색(본.fill):
                다름.append("바탕")
            b0 = 본.border
            if (_선(선.left), _선(선.right)) != (_선(b0.left), _선(b0.right)):
                다름.append("옆선")
            if _선(선.top) not in (_선(b0.top), "thin"):
                다름.append("윗선")
            if _선(선.bottom) not in (_선(b0.bottom), "double"):
                다름.append("아랫선")
            a0 = 본.alignment
            if (맞.horizontal or None, 맞.vertical, bool(맞.wrap_text)) != (a0.horizontal or None, a0.vertical, bool(a0.wrap_text)):
                if not (맞.indent and (맞.horizontal or "left") == "left" and (a0.horizontal or "left") == "left"
                        and 맞.vertical == a0.vertical and bool(맞.wrap_text) == bool(a0.wrap_text)):
                    다름.append("맞춤")
            if nf != _서식글(본.number_format):
                if nf == 표.서식표["날짜"]:
                    pass                                    # 날짜 값 · 날짜 입력 칸
                elif 이름 not in 표.숫자스타일:
                    다름.append("숫자 서식(%s)" % nf)
            if 다름:
                낱.append(("직접 서식", "「%s」 위에 허용 밖 덧씌움: %s" % (이름, " · ".join(다름))))
        self._판[키] = 낱
        return 낱

    # ── 시트 ──
    def 시트점검(self, wb, ws, 값ws, 사양):
        표 = self.표준
        이름 = ws.title
        폭 = {}

        def 열폭(k):
            if k not in 폭:
                폭[k] = 표.열폭(ws, k)
            return 폭[k]

        병합첫 = {}
        for g in ws.merged_cells.ranges:
            for r in range(g.min_row, g.max_row + 1):
                for k in range(g.min_col, g.max_col + 1):
                    병합첫[(r, k)] = g
        # 글이 흘러갈 수 있는 끝 열 — 값이 놓인 마지막 열과 인쇄 영역의 끝 열 가운데 먼 쪽(값이 적은 시트의 제목 · 부제는 빈 열로 흘러 보인다)
        영역 = ws.print_area
        영역 = (영역 if isinstance(영역, str) else ",".join(영역 or [])) or ""
        m = re.search(r":[$]?([A-Z]+)[$]?[0-9]+$", 영역.split("!")[-1])
        끝열 = max(ws.max_column, 열번호(m.group(1)) if m else 0)
        # 목록 유효성이 걸린 칸
        목록칸 = set()
        for dv in ws.data_validations.dataValidation:
            if dv.type != "list":
                continue
            for g in dv.sqref.ranges:
                for r in range(g.min_row, g.max_row + 1):
                    for k in range(g.min_col, g.max_col + 1):
                        목록칸.add((r, k))
        # 조건부 서식이 걸린 칸과 그 색
        조건칸 = set()
        for cf in ws.conditional_formatting:
            for 규칙 in cf.rules:
                색들 = set()
                if 규칙.dxf is not None:
                    if 규칙.dxf.font is not None and 규칙.dxf.font.color is not None:
                        색들.add(_rgb(규칙.dxf.font.color))
                    if 규칙.dxf.fill is not None:
                        색들.add(_rgb(규칙.dxf.fill.bgColor) or _rgb(규칙.dxf.fill.fgColor))
                for c in 색들 - {None}:
                    if c not in 표.조건부색:
                        self.적기("표준 밖 색", 이름, str(cf.sqref), "조건부 서식의 색 %s" % c)
            for g in cf.sqref.ranges:
                for r in range(g.min_row, g.max_row + 1):
                    for k in range(g.min_col, g.max_col + 1):
                        조건칸.add((r, k))

        숨긴줄 = {r for r, d in ws.row_dimensions.items() if d.hidden}
        칸들 = {}
        제목줄 = set()
        선택칸 = set()
        쓰는열 = set()
        for 줄 in ws.iter_rows():
            for 칸 in 줄:
                if 칸.value is None and not 칸.has_style:
                    continue
                if isinstance(칸, openpyxl.cell.cell.MergedCell):
                    continue
                칸들[(칸.row, 칸.column)] = 칸
        for (r, k), 칸 in 칸들.items():
            self.수["칸"] += 1
            스 = 칸.style
            if 칸.value is not None:
                쓰는열.add(k)
            if 스 == "글_제목":
                제목줄.add(r)
            if 스 == "값_선택":
                선택칸.add((r, k))
            for 갈, 설 in self._칸판정(wb, 칸):
                if 갈 == "직접 서식?":
                    if 칸.value is None:
                        continue                            # 값도 서식도 없는 칸
                    갈 = "직접 서식"
                self.적기(갈, 이름, 칸.coordinate, 설)
            if (r, k) in 조건칸 and 스 != "점검_표시":
                self.적기("표준 밖 색", 이름, 칸.coordinate, "판정 칸이 아닌 칸(%s)에 조건부 서식" % 스)

        # 값(캐시)을 곁들여 폭 · 글 서식 · 숫자 서식을 잰다
        for (r, k), 칸 in 칸들.items():
            v = 칸.value
            if v is None:
                continue
            수식 = 칸.data_type == "f" or (isinstance(v, str) and v.startswith("="))
            if 수식:
                self.수["수식 칸"] += 1
                v = 값ws.cell(r, k).value if 값ws is not None else None
                if v is None:
                    continue
                self.수["캐시 값 있는 수식 칸"] += 1
            스 = 칸.style
            nf = _서식글(칸.number_format)
            맞 = 칸.alignment
            숫자 = isinstance(v, (int, float)) and not isinstance(v, bool)
            if 숫자 and nf == "@":
                self.적기("숫자인데 글 서식", 이름, 칸.coordinate, "숫자 %r 에 글 서식(@) — 「%s」" % (v, 스))
            if isinstance(v, str) and not 수식 and 스 in 값스타일 + ("점검_결과",) and _re숫자글.match(v.strip()):
                self.적기("숫자인데 글 서식", 이름, 칸.coordinate, "글로 넣은 숫자 「%s」 — 「%s」" % (v, 스))
            if 숫자 and nf == "General" and 스 in 값스타일 + ("값_글", "값_연결글"):
                self.적기("서식 없는 숫자", 이름, 칸.coordinate, "숫자 %r 이 일반 서식 — 「%s」" % (v, 스))
            if 열폭(k) == 0 or r in 숨긴줄:
                continue                                    # 숨긴 줄 · 열은 폭을 재지 않는다
            if 맞.wrap_text:
                continue
            배 = (칸.font.sz or 표.글꼴크기) / float(표.글꼴크기) * (1.08 if 칸.font.b else 1.0)
            if 숫자 or isinstance(v, (datetime.date, datetime.datetime)):
                필요 = _숫자글(v, nf) * 배 + 0.5
                if 필요 > 열폭(k) and nf != "General":
                    self.적기("폭을 넘는 글", 이름, 칸.coordinate, "숫자가 열 폭 %.0f 을 넘는다(약 %.0f) — %s" % (열폭(k), 필요, nf))
                continue
            if not isinstance(v, str) or not v:
                continue
            필요 = max(표.환산폭(조각) for 조각 in v.split("\n")) * 배 + (맞.indent or 0) * 들여폭
            g = 병합첫.get((r, k))
            쓸 = sum(열폭(j) for j in range(g.min_col, g.max_col + 1)) if g is not None else 열폭(k)
            if 스 == "글_행이름":
                if 필요 > 쓸 - 이름여유:
                    self.적기("폭을 넘는 글", 이름, 칸.coordinate, "행 이름이 이름 열을 넘는다(폭 %.0f · 글 %.0f): %s" % (쓸, 필요, v[:30]))
                continue
            가로 = 맞.horizontal or "left"
            오른끝 = g.max_col if g is not None else k
            왼끝 = g.min_col if g is not None else k
            if 가로 in ("left", "general", "center", "centerContinuous", "fill"):
                j = 오른끝 + 1
                while 필요 > 쓸 - 여유 and j <= 끝열 and not self._찼나(ws, 값ws, 칸들, r, j):
                    쓸 += 열폭(j)
                    j += 1
            if 가로 in ("right", "center", "centerContinuous"):
                j = 왼끝 - 1
                while 필요 > 쓸 - 여유 and j >= 1 and not self._찼나(ws, 값ws, 칸들, r, j):
                    쓸 += 열폭(j)
                    j -= 1
            if 필요 > 쓸 - 여유:
                self.적기("폭을 넘는 글", 이름, 칸.coordinate, "글이 흘러갈 빈 칸까지 합친 폭을 넘는다(폭 %.0f · 글 %.0f · %s): %s"
                        % (쓸, 필요, 스, v[:30].replace("\n", " ")))

        # 유효성 없는 선택 칸
        for (r, k) in sorted(선택칸 - 목록칸):
            self.적기("유효성 없는 선택 칸", 이름, "%s%d" % (열글자(k), r), "선택 칸(값_선택)에 목록 유효성이 없다")
        for (r, k) in sorted(목록칸 - 선택칸):      # 값도 서식도 없는 빈 칸에 걸린 목록도 센다(계산 줄에 걸친 범위)
            칸 = 칸들.get((r, k))
            self.적기("유효성 없는 선택 칸", 이름, "%s%d" % (열글자(k), r),
                    "목록 유효성이 걸렸는데 선택 칸이 아니다(%s)" % (칸.style if 칸 is not None else "빈 칸"))

        # 시트 공통
        if ws.freeze_panes is None:
            self.적기("시트 공통", 이름, None, "틀 고정이 없다")
        if ws.sheet_view.showGridLines:
            self.적기("시트 공통", 이름, None, "눈금선이 켜졌다")
        확대 = ws.sheet_view.zoomScale or 100
        if 사양 is not None and 확대 != 사양.get("확대"):
            self.적기("시트 공통", 이름, None, "확대 비율 %s — 사양은 %s" % (확대, 사양.get("확대")))
        탭 = _rgb(ws.sheet_properties.tabColor)
        if 탭 is None:
            self.적기("시트 공통", 이름, None, "탭 색이 없다")
        elif 탭 not in set(표.탭색.values()):
            self.적기("표준 밖 색", 이름, None, "탭 색 %s" % 탭)
        for g in ws.merged_cells.ranges:
            if not (g.min_row == g.max_row and g.min_row in 제목줄):
                self.적기("시트 공통", 이름, str(g), "제목 줄 밖의 병합")
        정한열 = set()
        for d in ws.column_dimensions.values():
            if d.width or d.hidden:
                정한열.update(range(d.min or 0, (d.max or d.min or 0) + 1))
        for k in sorted(쓰는열 - 정한열):
            self.적기("시트 공통", 이름, 열글자(k), "폭을 안 정한 열")

        # 인쇄
        빠진 = []
        ps = ws.page_setup
        if not ps.orientation:
            빠진.append("방향")
        elif 사양 is not None and ps.orientation != 사양.get("방향"):
            빠진.append("방향(%s — 사양은 %s)" % (ps.orientation, 사양.get("방향")))
        맞춤 = ws.sheet_properties.pageSetUpPr
        if not (맞춤 is not None and 맞춤.fitToPage and ps.fitToWidth in (1, None) and ps.fitToHeight == 0):      # 폭 1 은 기본값이라 엑셀이 안 적는다
            빠진.append("폭 1쪽 맞춤")
        if not ws.print_area:
            빠진.append("인쇄 영역")
        틀 = ws.freeze_panes
        틀행 = int(re.sub(r"[A-Z]", "", 틀)) if 틀 else 1
        if 틀행 > 1 and not ws.print_title_rows:
            빠진.append("제목 행 반복")
        if "&A" not in (ws.oddFooter.center.text or ""):
            빠진.append("바닥글의 시트 이름")
        if "&P" not in (ws.oddFooter.right.text or ""):
            빠진.append("바닥글의 쪽")
        if 빠진:
            self.적기("인쇄 설정 없는 시트", 이름, None, " · ".join(빠진))
        return 칸들, 목록칸

    @staticmethod
    def _찼나(ws, 값ws, 칸들, r, k):
        칸 = 칸들.get((r, k))
        if 칸 is None or 칸.value is None:
            return False
        if 칸.data_type == "f" and 값ws is not None:
            v = 값ws.cell(r, k).value
            return v is not None and v != ""
        return True

    def 돌리기(self):
        표 = self.표준
        wb = openpyxl.load_workbook(self.경로)
        # 기본 스타일 — 지은 파일은 「Normal」, 한글 엑셀이 저장한 파일은 「표준」이다(내장 번호 0)
        self.기본스타일 = next((s for s in wb._named_styles if s.builtinId == 0), None) or wb._named_styles[0]
        try:
            값wb = openpyxl.load_workbook(self.경로, data_only=True)
        except Exception:                                   # noqa: BLE001
            값wb = None
        탭 = {s["탭"]: s for s in 표.시트표}
        시트칸, 시트목록 = {}, {}
        순 = []
        for ws in wb.worksheets:
            self.수["시트"] += 1
            사양 = 탭.get(ws.title)
            if 사양 is None:
                self.적기("시트 공통", ws.title, None, "탭 이름이 시트표에 없다")
            else:
                순.append(사양["id"])
            값ws = 값wb[ws.title] if 값wb is not None else None
            시트칸[ws.title], 시트목록[ws.title] = self.시트점검(wb, ws, 값ws, 사양)
        if 순 != [s["id"] for s in 표.시트표 if s["id"] in 순]:
            self.적기("시트 공통", "(통합 문서)", None, "시트 순서가 시트표와 다르다: %s" % " ".join(순))
        빠진 = [s["탭"] for s in 표.시트표 if s["id"] not in 순]
        if 빠진:
            self.적기("시트 공통", "(통합 문서)", None, "시트표의 시트가 없다: %s" % " · ".join(빠진))
        # 수식이 글 상수와 견주는 입력 칸 — 목록 유효성이 있어야 한다
        본 = set()
        for 이름, 칸들 in 시트칸.items():
            for (r, k), 칸 in 칸들.items():
                v = 칸.value
                if not (isinstance(v, str) and v.startswith("=") and '"' in v):
                    continue
                for m in list(_re뒤견줌.finditer(v)) + list(_re앞견줌.finditer(v)):
                    if m.re is _re뒤견줌:
                        따, 맨, 열, 행, 열2, 행2, 글 = m.groups()
                    else:
                        글, 따, 맨, 열, 행, 열2, 행2 = m.groups()
                    if 글 in ("", "n/a", "-", "미사용"):       # 「미사용」은 출처 칸의 표지다(배치_납품 표지글 — W6b) — 선택지가 아니다
                        continue
                    시트 = (따.replace("''", "'") if 따 else 맨) or 이름
                    if 시트 not in 시트칸:
                        continue
                    r1, r2 = sorted((int(행), int(행2 or 행)))
                    k1, k2 = sorted((열번호(열), 열번호(열2 or 열)))
                    for r0 in range(r1, r2 + 1):
                        for k0 in range(k1, k2 + 1):
                            자리 = (시트, r0, k0)
                            if 자리 in 본:
                                continue
                            본.add(자리)
                            과녁 = 시트칸[시트].get((r0, k0))
                            if 과녁 is None or 과녁.style not in 입력스타일:
                                continue
                            if (r0, k0) not in 시트목록[시트]:
                                self.적기("유효성 없는 선택 칸", 시트, "%s%d" % (열글자(k0), r0),
                                        "수식(%s!%s)이 글 「%s」 과 견주는 입력 칸인데 목록 유효성이 없다" % (이름, 칸.coordinate, 글))
        return self.결과()

    def 결과(self):
        return OrderedDict([("파일", self.경로), ("수", self.수),
                            ("갈래", OrderedDict((갈, OrderedDict([("수", len(낱)), ("목록", 낱)])) for 갈, 낱 in self.찾은.items())),
                            ("합계", sum(len(낱) for 낱 in self.찾은.values()))])


def 점검(경로, 표준=None):
    """워크북 하나를 점검한다 → {"파일", "수", "갈래": {갈래: {"수", "목록"}}, "합계"}."""
    return 점검기(경로, 표준).돌리기()


def 찍기(결, 자세히=False, 보기=5, 낼=print):
    수 = 결["수"]
    낼("서식 점검 — %s" % 결["파일"])
    낼("  시트 %d장 · 값이나 서식이 있는 칸 %d · 수식 칸 %d(캐시 값 있는 것 %d — 없는 칸은 폭 · 글 서식을 재지 않았다)"
      % (수["시트"], 수["칸"], 수["수식 칸"], 수["캐시 값 있는 수식 칸"]))
    for 갈, 한 in 결["갈래"].items():
        낼("  %-20s %d" % (갈, 한["수"]))
        if 한["수"] and (자세히 or 보기):
            for 글 in 한["목록"][:None if 자세히 else 보기]:
                낼("      " + 글)
            if not 자세히 and 한["수"] > 보기:
                낼("      … 그 밖 %d곳" % (한["수"] - 보기))
    낼("합계 %d → %s" % (결["합계"], "벗어난 곳 없음" if 결["합계"] == 0 else "벗어난 곳이 있다"))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    인자 = sys.argv[1:]
    자세히 = "--자세히" in 인자
    보기, 낼json = 5, None
    자리 = []
    i = 0
    while i < len(인자):
        if 인자[i] == "--보기":
            보기 = int(인자[i + 1])
            i += 2
        elif 인자[i] == "--json":
            낼json = 인자[i + 1]
            i += 2
        elif 인자[i] == "--자세히":
            i += 1
        else:
            자리.append(인자[i])
            i += 1
    if len(자리) != 1:
        raise SystemExit(__doc__)
    if not os.path.exists(자리[0]):
        print("파일이 없다: %s" % 자리[0])
        sys.exit(2)
    결 = 점검(자리[0])
    찍기(결, 자세히, 보기)
    if 낼json:
        with open(낼json, "w", encoding="utf-8", newline="\n") as f:
            json.dump(결, f, ensure_ascii=False, indent=1)
            f.write("\n")
    sys.exit(0 if 결["합계"] == 0 else 1)

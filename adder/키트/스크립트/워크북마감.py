# -*- coding: utf-8 -*-
"""워크북마감 — 부은 워크북을 마감한다 (W6b · 설계 3_점검_마감 5절 · 6_산식_설계 10-4).

  python 스크립트/워크북마감.py <부은 워크북.xlsx> <가정.json> [--낼 <마감본.xlsx>] [--출력 <워크북마감.txt>]
                                [--지도 <좌표지도.json>] [--재계산 자동|엑셀|formulas]

  ① 판      좌표 지도 · 구조 선언과 워크북의 일치(I-151 — 구조 지문) · 굳힌 일정의 일치(I-152 — `일정전개.py --검산` 의 종료 코드)
  ② 엔진    세 시나리오의 주당가치 · 영업가치 · 주주가치
  ③ 기입    1번 「시나리오별 결과」 아홉 칸을 엔진 값으로 채운다(도구 기입 칸 — 사람이 옮겨 적지 않는다)
  ④ 서식    서식마감(생성기) — 안 쓰는 줄(미사용 선언 · 구조가 쓰지 않는 매출 구분 3~5 …)과 이 회차에 해당하지 않는 점검 줄을 접고,
            보이는 구획에만 로마 숫자를 다시 매기고, 주당 금액의 소수 자리를 표시 통화에 맞춘다
  ⑤ 재계산  따로 띄운 엑셀로 비관 · 기준 · 낙관을 다시 계산해 15번 검증 시트 · 순환 참조(I-153) · 오류 값 칸(I-51) ·
            엔진 = 워크북(I-53)을 읽는다. 납품 시나리오로 되돌려 다시 계산하고 쪽을 나눈 뒤(쪽나눔) 저장한다(캐시 값이 남는다)
  ⑥ 판정    15번의 Error 0 · 검토사항(Review)마다 요건을 채운 검토 의견 · 도구 점검 통과 · 「확인 필요」류의 옛 판정 글 0 이면 「마감」
  ⑦ 개인 정보  납품 워크북은 독자에게 나간다 — 저장 전에 문서 속성의 작성자 · 마지막으로 수정한 사람 · 회사 · 관리자 · 설명 · 키워드 ·
            주제 · 범주를 비우고(작성자는 「DCF 시작키트」) 사용자 지정 속성은 키트의 것(배치 지문 · 부음 표식)만 남기며 엑셀이 저장할 때
            개인 정보를 지우게 한다(RemovePersonalInformation). 저장한 마감본의 문서 속성에 이 PC 의 사용자 이름이 남으면 I-154 Error(W6d)
종료 코드: 0 마감 · 1 미완(미완 목록을 낸다) · 2 입력오류(파일 · JSON · 좌표 지도 · 엔진 · 엑셀과 formulas 모두 실패)

엑셀은 `DispatchEx` 로 따로 띄운 것만 쓰고 그것만 끝낸다(사용자의 엑셀에 닿지 않는다). 원본 워크북을 직접 열지 않는다 — 임시 사본에서
계산하고 마감본(--낼, 기본: 원본 곁의 「<이름>_마감.xlsx」)으로 저장한다. 엑셀을 띄우지 못하면 formulas 로 판정하고 그 사실을 적는다
(그때 마감본에는 계산값이 없다). 가정 점검(자체검사)은 이 판의 판정에 넣지 않는다 — W7a 가 잇는다.
"""
import argparse
import collections
import datetime
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
import openpyxl  # noqa: E402

import 좌표  # noqa: E402
import 미사용  # noqa: E402
from 종료코드 import 통과, 발견, 입력오류  # noqa: E402

시나리오목록 = ("비관", "기준", "낙관")
적용시나리오칸 = ("12", "D12")         # 대조.py 와 같은 칸 — 재계산 전에 시나리오 이름을 쓴다
결과줄 = {"주당가치": 61, "영업가치": 62, "주주가치": 63}       # 1번 「시나리오별 결과」 줄
결과열 = {"비관": "값1", "기준": "값2", "낙관": "값3"}
계산줄 = {"주당가치": 68, "영업가치": 58, "주주가치": 66}       # 2번의 계산값 줄(단일 쓰임 — 값 칸 = 첫 시간축 열)
점검목록곳 = os.path.join(여기, "점검목록.json")
표시들 = ("OK", "Error", "Review", "N/A")
# 마감되지 않게 하는 옛 판정 글의 머리 — 「확인 필요 — …」 꼴의 글이 남은 워크북은 점검을 다 옮기지 못한 것이다
옛판정글 = re.compile(r"^\s*(확인 필요|확인 불가|검사 아님|신호 —|해당 없음 —|구조상 자동 성립)")
의견최소 = 15
의견한마디 = {"해당 없음", "확인함", "이상 없음", "상동", "-", "확인", "OK", "검토함", "문제 없음"}
호출거부 = -2147418111


중립작성자 = "DCF 시작키트"
키트속성 = (좌표.지문이름, 좌표.부음표식)           # 키트가 쓰는 사용자 지정 속성(배치 지문 · 부음 표식) — 개인 정보가 없다
걷을속성 = ("Author", "Last Author", "Manager", "Company", "Comments", "Keywords", "Subject", "Category", "Hyperlink base")
개인속성 = ("creator", "lastModifiedBy", "Company", "Manager", "description", "keywords", "subject", "category", "HyperlinkBase")


class 마감오류(Exception):
    """입력오류 — 종료 코드 2."""


def _속성비우기_엑셀(통합문서):
    """엑셀로 연 마감본의 문서 속성에서 개인 정보를 걷는다(저장 전 — W6d)."""
    try:
        통합문서.RemovePersonalInformation = True              # 저장할 때 작성자 · 마지막으로 수정한 사람 따위를 엑셀이 지운다
    except Exception:                                    # noqa: BLE001
        pass
    for 이름 in 걷을속성:
        try:
            통합문서.BuiltinDocumentProperties(이름).Value = 중립작성자 if 이름 == "Author" else ""
        except Exception:                                # noqa: BLE001 — 그 속성이 없는 판
            pass
    try:
        속 = 통합문서.CustomDocumentProperties
        for k in range(속.Count, 0, -1):
            if 속(k).Name not in 키트속성:
                속(k).Delete()
    except Exception:                                    # noqa: BLE001
        pass


def _속성비우기_openpyxl(wb):
    """openpyxl 로 저장하는 마감본(formulas 길)의 문서 속성에서 개인 정보를 걷는다(W6d)."""
    p = wb.properties
    p.creator = 중립작성자
    p.lastModifiedBy = None
    for 열쇠 in ("description", "keywords", "subject", "category"):
        setattr(p, 열쇠, None)
    try:
        for 이름 in list(wb.custom_doc_props.names):
            if 이름 not in 키트속성:
                del wb.custom_doc_props[이름]
    except Exception:                                    # noqa: BLE001
        pass


def 속성점검(경로, 이름들):
    """I-154 — 저장한 마감본의 문서 속성(docProps 의 core · app · custom)에 개인 정보가 남았는가 → (판정 0/1, 글).
    작성자 · 마지막으로 수정한 사람은 빈칸이거나 「DCF 시작키트」, 회사 · 관리자 · 설명 · 키워드 · 주제 · 범주는 빈칸,
    어느 속성에도 이 PC 의 사용자 이름(이름들)이 없어야 한다. 글에는 속성 이름만 적고 값(이름)은 적지 않는다."""
    import zipfile                                       # noqa: PLC0415
    걸린 = []
    with zipfile.ZipFile(경로) as z:
        for 부분 in ("docProps/core.xml", "docProps/app.xml", "docProps/custom.xml"):
            if 부분 not in z.namelist():
                continue
            글 = z.read(부분).decode("utf-8", "replace")
            if 부분.endswith("custom.xml"):
                for 이름, 값 in re.findall(r'<property[^>]*name="([^"]*)"[^>]*>.*?<vt:[a-z0-9]+[^>]*>([^<]*)</vt:', 글, re.S):
                    if 이름 not in 키트속성 or any(n and n.lower() in 값.lower() for n in 이름들):
                        걸린.append("사용자 지정 속성 %s" % ("(키트 밖)" if 이름 not in 키트속성 else 이름))
                continue
            for m in re.finditer(r"<(?:[A-Za-z]+:)?([A-Za-z]+)(?:\s[^>]*)?>([^<]*)</(?:[A-Za-z]+:)?\1>", 글):
                태그, 값 = m.group(1), m.group(2).strip()
                if not 값:
                    continue
                if 태그 in ("creator", "lastModifiedBy") and 값 != 중립작성자:
                    걸린.append(태그)
                elif 태그 in 개인속성 and 태그 not in ("creator", "lastModifiedBy"):
                    걸린.append(태그)
                elif any(n and len(n) >= 2 and n.lower() in 값.lower() for n in 이름들):
                    걸린.append(태그)
    if 걸린:
        return 1, "문서 속성에 개인 정보가 남았다 — %s(값은 적지 않는다)" % " · ".join(sorted(set(걸린)))
    return 0, "문서 속성에 개인 정보 없음(작성자 「%s」 · 사용자 지정 속성은 키트의 것만)" % 중립작성자


def _해시(바이트):
    return hashlib.sha256(바이트).hexdigest()


def _가정해시(가정):
    return _해시(json.dumps(가정, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def _거듭(부름, 번=8, 쉼=2.0):
    for k in range(번):
        try:
            return 부름()
        except Exception as e:                                 # noqa: BLE001
            if getattr(e, "hresult", None) != 호출거부 or k == 번 - 1:
                raise
            time.sleep(쉼)


def 점검목록읽기():
    with io.open(점검목록곳, encoding="utf-8") as f:
        return json.load(f)


def 의견요건(글):
    """검토 의견이 요건(15자 이상 · 한마디가 아님)을 채우는가 → 모자란 까닭 글(채우면 None)."""
    글 = ("%s" % (글 or "")).strip()
    if not 글:
        return "검토 의견 없음"
    if 글 in 의견한마디:
        return "검토 의견이 한마디(「%s」)다" % 글
    if len(글) < 의견최소:
        return "검토 의견이 %d자다(%d자 이상)" % (len(글), 의견최소)
    return None


def _수(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _금액글(v):
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        return "%s" % (v if v not in (None, "") else "—")
    return "{:,.0f}".format(v) if abs(v) >= 100 else ("%.4g" % v)


# ───────────────────────────── ③ · ④ openpyxl 단계 ─────────────────────────────
def _자리(지, 시트, 열, 번호):
    try:
        return 지.자리(시트, 열, 번호)
    except 좌표.좌표오류:
        return None, None


def 기입(wb, 지, 엔진값):
    """1번 시나리오별 결과 아홉 칸 → 쓴 칸 수."""
    n = 0
    for 키, 번 in 결과줄.items():
        for 시, 열 in 결과열.items():
            이름, 칸 = _자리(지, "1", 열, 번)
            if 칸 and 이름 in wb.sheetnames:
                wb[이름][칸].value = 엔진값[시][키]
                n += 1
    return n


def 점검줄들(wb, 지, 목록):
    """15번의 점검 줄 → [(점검, 행 번호, {열 ID: 칸 주소})]. 워크북에 없는 줄은 행 번호 None."""
    낸 = []
    for p in 목록["세운"]:
        번 = int(p["행"][4:])
        try:
            r = 지.행("15", 번)
        except 좌표.좌표오류:
            r = None
        칸 = {}
        if r is not None:
            for 열 in ("번호", "구분", "이름", "값A", "값B", "차이", "허용", "결과", "표시", "의견", "미결", "적용"):
                _이름, a = _자리(지, "15", 열, 번)
                칸[열] = a
        낸.append((p, r, 칸))
    return 낸


def 표지찾기(wb, 지):
    """워크북에 적힌 「미사용」 표지 — {(시트 번호, 번호)}(12번 근거 1 · 13번 · 3번 출처)."""
    낸 = set()
    for 시, 열 in (("12", "근거1"), ("13", "출처"), ("3", "출처")):
        try:
            장 = 지.장(wb, 시)
        except 좌표.좌표오류:
            continue
        for 번, _r in 장.줄들():
            try:
                if 장.값(열, 번) == 미사용.표지:
                    낸.add((시, 번))
            except 좌표.좌표오류:
                continue
    return 낸


원천구간 = [(7, 15), (17, 31), (34, 43), (45, 53), (56, 57), (62, 63), (65, 65), (67, 72), (74, 74), (77, 83), (86, 91), (95, 96), (98, 99)]
W입력줄 = (7, 101, 102, 103, 104, 10, 11, 13, 14, 21, 108)


def 빈칸자리(wb, 지, 가정=None):
    """완결성 미비의 자리 — {점검 번호: [「13번 현금및현금성자산(출처)」 …]}. 15번의 수식이 센 것을 도구가 다시 짚는다(13번 · 3번 · 12번 [기본값] · 17번 연동 빈칸)."""
    낸 = collections.defaultdict(list)
    기준일 = (지.기간().get("자리") or {}).get("기준일") or [c for c, 구 in zip(지.기간열(), 지.기간구분()) if 구 == "실적"][-1]
    try:
        장 = 지.장(wb, "13")
    except 좌표.좌표오류:
        장 = None
    for a, z in 원천구간 if 장 is not None else ():
        for 번 in range(a, z + 1):
            try:
                이름 = 장.값("이름", 번)
                값, 출처, 일 = 장.값(기준일, 번), 장.값("출처", 번), 장.값("기준일", 번)
            except 좌표.좌표오류:
                continue
            if 출처 == 미사용.표지:
                continue
            if 값 in (None, ""):
                낸["C-06"].append("13번 %s" % 이름)
            if 출처 in (None, ""):
                낸["C-07"].append("13번 %s(출처)" % 이름)
            if 일 in (None, ""):
                낸["C-07"].append("13번 %s(기준일)" % 이름)
    try:
        장 = 지.장(wb, "3")
    except 좌표.좌표오류:
        장 = None
    for 번 in W입력줄 if 장 is not None else ():
        try:
            이름, 값 = 장.값("이름", 번), 장.값("예측값", 번)
            if isinstance(값, str) and 값.startswith("="):
                continue
            for 열 in ("출처", "기준일"):
                if 장.값(열, 번) in (None, ""):
                    낸["C-05"].append("3번 %s(%s)" % (이름, 열))
        except 좌표.좌표오류:
            continue
    # C-109 · C-110(2026-10-24 결정 W11) — [기본값] 딱지가 남은 12번 가정 줄 · 17번에서 「무엇에 연동」 이 빈 노드
    try:
        접 = set(미사용.접을줄(가정)) if isinstance(가정, dict) else set()     # 구조가 쓰지 않는 줄은 세지 않는다(붓기 17번 196 과 같은 셈)
    except Exception:                                                  # noqa: BLE001
        접 = set()
    try:
        장 = 지.장(wb, "12")
        for 번, _줄 in 장.지.가정묶음(장.번호, 장):
            if "S12R%03d" % 번 in 접:
                continue
            v = 장.값("근거1", 번)
            if isinstance(v, str) and v.strip().startswith("[기본값]"):
                낸["C-109"].append("12번 %s %s" % (번, 장.값("이름", 번) or ""))
    except (좌표.좌표오류, KeyError, ValueError, TypeError):
        pass
    try:
        장 = 지.장(wb, "17")
        for 번 in range(101, 181):
            노 = 장.값("노드", 번)
            if 노 not in (None, "") and 장.값("연동", 번) in (None, ""):
                낸["C-110"].append("17번 %s" % 노)
    except (좌표.좌표오류, KeyError, ValueError, TypeError):
        pass
    return 낸


# ───────────────────────────── ⑤ 재계산 ─────────────────────────────
def _읽을칸(지, 줄들, 첫열):
    """재계산 뒤에 읽을 칸 → {열쇠: (시트 이름, 칸)}."""
    칸 = {}
    for p, r, 자리 in 줄들:
        if r is None:
            continue
        이름 = 지.시트("15")
        for 열 in ("값A", "값B", "결과", "표시", "의견", "미결", "적용"):
            if 자리.get(열):
                칸[(p["id"], 열)] = (이름, 자리[열])
    이름, a = _자리(지, "15", "결과", 8)
    if a:
        칸[("총괄", "결과")] = (이름, a)
    for 키, 번 in 계산줄.items():
        이름, a = _자리(지, "2", 첫열, 번)
        if a:
            칸[("계산", 키)] = (이름, a)
    return 칸


def _한번에읽기(통합문서, 읽을칸):
    """읽을 칸을 시트마다 한 번의 범위 읽기로 — 칸마다 부르면 COM 호출이 수천 번이다."""
    from openpyxl.utils.cell import coordinate_from_string, column_index_from_string     # noqa: PLC0415
    시트별 = collections.defaultdict(list)
    for 키, (이름, a) in 읽을칸.items():
        글자, r = coordinate_from_string(a.replace("$", ""))
        시트별[이름].append((키, r, column_index_from_string(글자)))
    값 = {}
    for 이름, 칸들 in 시트별.items():
        r1, r2 = min(x[1] for x in 칸들), max(x[1] for x in 칸들)
        c1, c2 = min(x[2] for x in 칸들), max(x[2] for x in 칸들)
        ws = 통합문서.Worksheets(이름)
        표 = _거듭(lambda: ws.Range(ws.Cells(r1, c1), ws.Cells(r2, c2)).Value)
        if not isinstance(표, tuple):
            표 = ((표,),)
        for 키, r, c in 칸들:
            값[키] = 표[r - r1][c - c1]
    return 값


def 엑셀재계산(사본, 낼곳, 지, 읽을칸, 납품시나리오, 쪽나누기=True):
    """→ {"시나리오": {시: {"값": {열쇠: 값}, "순환": [...], "오류칸": n, "오류보기": [...]}}, "쪽": {...}, "초": t}."""
    import pythoncom                    # noqa: PLC0415
    import win32com.client              # noqa: PLC0415
    시작 = time.time()
    시트명, 칸 = 지.자리(*적용시나리오칸)
    결과 = {"시나리오": collections.OrderedDict(), "쪽": {}}
    pythoncom.CoInitialize()
    엑셀 = win32com.client.DispatchEx("Excel.Application")      # 따로 띄운 엑셀 — 사용자의 엑셀에는 닿지 않는다
    통합문서 = None
    try:
        엑셀.Visible = False
        엑셀.DisplayAlerts = False
        엑셀.AskToUpdateLinks = False
        엑셀.EnableEvents = False
        엑셀.ScreenUpdating = False
        통합문서 = _거듭(lambda: 엑셀.Workbooks.Open(os.path.abspath(사본), UpdateLinks=0))
        결과["열기초"] = round(time.time() - 시작, 1)
        _거듭(lambda: setattr(엑셀, "Calculation", -4135))     # 수동 계산 — 시나리오 칸을 바꿀 때 저절로 다시 셈하지 않는다(W6d)
        for n, 시 in enumerate(시나리오목록):
            _거듭(lambda: setattr(통합문서.Worksheets(시트명).Range(칸), "Value", 시))
            t = time.time()
            _거듭(엑셀.CalculateFullRebuild if n == 0 else 엑셀.CalculateFull)   # 의존 관계는 처음 한 번만 다시 짓는다
            결과.setdefault("계산초", []).append(round(time.time() - t, 1))
            값 = _한번에읽기(통합문서, 읽을칸)
            순환, 오류칸, 보기 = [], 0, []
            for ws in 통합문서.Worksheets:
                try:
                    c = ws.CircularReference
                    if c is not None:
                        순환.append("%s!%s" % (ws.Name, str(c.Address).replace("$", "")))
                except Exception:                              # noqa: BLE001 — 순환이 없으면 예외가 난다
                    pass
                try:
                    오 = ws.UsedRange.SpecialCells(-4123, 16)    # xlCellTypeFormulas, xlErrors
                    오류칸 += 오.Count
                    if len(보기) < 6:
                        보기.append("%s!%s" % (ws.Name, str(오.Address).replace("$", "")[:60]))
                except Exception:                              # noqa: BLE001 — 오류 칸이 없으면 예외가 난다
                    pass
            결과["시나리오"][시] = {"값": 값, "순환": 순환, "오류칸": 오류칸, "오류보기": 보기}
        _거듭(lambda: setattr(통합문서.Worksheets(시트명).Range(칸), "Value", 납품시나리오))
        _거듭(엑셀.CalculateFull)
        _거듭(lambda: setattr(엑셀, "Calculation", -4105))     # 자동 계산으로 되돌려 저장한다(마감본을 여는 사람의 엑셀)
        결과["재계산초"] = round(time.time() - 시작, 1)
        t = time.time()
        if 쪽나누기:
            생 = _생성기()
            if 생 not in sys.path:
                sys.path.insert(0, 생)
            import 쪽나눔                    # noqa: PLC0415
            try:
                머리줄 = 쪽나눔.구획머리줄(사본) if hasattr(쪽나눔, "구획머리줄") else None     # 구획머리를 파일에서 한 번에(W6d)
                결과["쪽"] = 쪽나눔.맞추기(엑셀, 통합문서, 머리줄) if 머리줄 is not None else 쪽나눔.맞추기(엑셀, 통합문서)
            except Exception as e:                             # noqa: BLE001 — 쪽 나눔은 판정에 들지 않는다
                결과["쪽"] = {"오류": "%s" % e}
        결과["쪽초"] = round(time.time() - t, 1)
        if os.path.exists(낼곳):
            os.remove(낼곳)
        try:
            결과["사용자이름"] = "%s" % (엑셀.UserName or "")       # I-154 가 마감본에서 찾는 이름 — 화면 · 파일에 적지 않는다
        except Exception:                                  # noqa: BLE001
            결과["사용자이름"] = ""
        _속성비우기_엑셀(통합문서)
        _거듭(lambda: 통합문서.SaveAs(os.path.abspath(낼곳), FileFormat=51))
    finally:
        if 통합문서 is not None:
            try:
                통합문서.Close(SaveChanges=False)                     # 내가 연 것만 닫는다
            except Exception:                                  # noqa: BLE001
                pass
        try:
            엑셀.Quit()                                         # 내가 띄운 엑셀만 끝낸다
        except Exception:                                      # noqa: BLE001
            결과["끝내기"] = "띄운 엑셀을 끝내지 못했다 — 작업 관리자에서 확인한다"
        del 엑셀
        pythoncom.CoUninitialize()
    결과["초"] = round(time.time() - 시작, 1)
    return 결과


def formulas재계산(사본, 낼곳, 지, 읽을칸, 납품시나리오):
    """엑셀이 없을 때 — formulas 로 세 시나리오를 계산해 읽는다. 마감본에는 계산값이 남지 않는다."""
    import formulas                     # noqa: PLC0415
    try:
        from schedula import EMPTY as _빈칸표       # noqa: PLC0415
    except Exception:                                # noqa: BLE001
        _빈칸표 = None
    시작 = time.time()
    시트명, 칸 = 지.자리(*적용시나리오칸)
    결과 = {"시나리오": collections.OrderedDict(), "쪽": {}}
    임시 = tempfile.mkdtemp(prefix="워크북마감_")
    try:
        for 시 in 시나리오목록:
            wb = openpyxl.load_workbook(사본)
            wb[시트명][칸].value = 시
            p = os.path.join(임시, "계산_%s.xlsx" % 시)
            wb.save(p)
            해 = formulas.ExcelModel().loads(p).finish().calculate()
            이름 = os.path.basename(p).upper()
            표 = {}
            for k, v in 해.items():
                m = re.match(r"^'\[(.+?)\](.+?)'!([A-Z]+\d+)$", str(k))
                if m:
                    vv = getattr(v, "value", v)
                    try:
                        vv = vv[0][0]
                    except Exception:                          # noqa: BLE001
                        pass
                    if _빈칸표 is not None and vv is _빈칸표:     # W8a — 빈 칸은 formulas 의 EMPTY(글로 「empty」)다. 빈칸으로 읽는다
                        vv = None
                    표[(m.group(2), m.group(3))] = vv
            값, 오류칸 = {}, 0
            for 키, (시트, a) in 읽을칸.items():
                v = 표.get((시트.upper(), a.replace("$", "")))
                값[키] = None if v is None or "XlError" in type(v).__name__ else v
            for v in 표.values():
                if "XlError" in type(v).__name__ or (isinstance(v, str) and v.startswith("#")):
                    오류칸 += 1
            결과["시나리오"][시] = {"값": 값, "순환": [], "오류칸": 오류칸, "오류보기": []}
        wb = openpyxl.load_workbook(사본)
        wb[시트명][칸].value = 납품시나리오
        _속성비우기_openpyxl(wb)
        wb.save(낼곳)
    finally:
        shutil.rmtree(임시, ignore_errors=True)
    결과["초"] = round(time.time() - 시작, 1)
    return 결과


def _생성기():
    import 스캐폴드짓기                 # noqa: PLC0415
    return 스캐폴드짓기.생성기곳()


# ───────────────────────────── 마감 ─────────────────────────────
def 곁지도쓰기(지, 낼곳):
    """마감본 곁의 「<마감본>.좌표지도.json」을 이 마감이 읽은 좌표 지도로 새로 쓴다 → 쓴 꼴의 글(같으면 「그대로」) · 못 쓰면 None.

    대조 · 자체검사는 워크북 곁의 짝 지도를 먼저 읽는다 — 구조를 바꿔 다시 지은 회차에서 옛 짝 지도가 남으면 「스캐폴드 지문이 다르다」(rc 2)로
    멈춘다(N5). 마감은 늘 지금 지도로 덮는다(마감본과 그 지도가 한 짝이다)."""
    원 = getattr(지, "경로", None)
    if not 원 or not os.path.isfile(원):
        return None
    짝 = os.path.abspath(낼곳) + 좌표.짝지도꼬리
    if os.path.abspath(원) == 짝:
        return "그대로(마감본의 짝 지도를 읽었다)"
    with open(원, "rb") as f:
        새 = f.read()
    옛 = None
    if os.path.isfile(짝):
        with open(짝, "rb") as f:
            옛 = f.read()
    if 옛 == 새:
        return "그대로"
    with open(짝, "wb") as f:
        f.write(새)
    return "새로 썼다(옛 짝 지도와 달랐다)" if 옛 is not None else "새로 썼다"


def 마감(워크북, 가정경로, 낼곳=None, 지도곳=None, 재계산="자동"):
    """→ (판정 사전, 화면 글 줄들, 종료 코드)."""
    시작 = time.time()
    if not os.path.exists(워크북):
        raise 마감오류("워크북이 없다: %s" % 워크북)
    try:
        with io.open(가정경로, encoding="utf-8") as f:
            가정 = json.load(f)
    except (OSError, ValueError) as e:
        raise 마감오류("가정 JSON 을 읽지 못했다: %s" % e)
    import 옛꼴다리                     # noqa: PLC0415
    새가정 = 옛꼴다리.새꼴가정(가정) if 옛꼴다리.옛판인가(가정) else 가정
    try:
        지 = 좌표.읽기(지도곳) if 지도곳 else 좌표.지도찾기(워크북)
    except 좌표.좌표오류 as e:
        raise 마감오류("%s" % e)
    목록 = 점검목록읽기()
    낼곳 = 낼곳 or os.path.splitext(워크북)[0] + "_마감.xlsx"
    도구 = collections.OrderedDict()        # 도구 점검 번호 → (판정 0/1/None, 글)

    # ① 판 — I-151 구조 선언 · I-152 굳힌 일정
    try:
        경 = 지.구조지문확인(새가정, 필수=True)
        도구["I-151"] = (0, "구조 지문 %s 일치" % (지.구조지문() or "?") + (" — %s" % 경 if 경 else ""))
    except 좌표.좌표오류 as e:
        도구["I-151"] = (1, "%s" % e)
    if isinstance(가정.get("일정"), dict):
        r = subprocess.run([sys.executable, os.path.join(여기, "일정전개.py"), 가정경로, "--검산"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        if r.returncode == 2:
            raise 마감오류("일정전개 --검산 이 입력 오류로 끝났다:\n%s" % ((r.stdout or "") + (r.stderr or ""))[-1500:])
        도구["I-152"] = (0 if r.returncode == 0 else 1, "일정전개 --검산 — %s(종료 코드 %d)"
                        % ("굳힌 값 = 일정" if r.returncode == 0 else "가정 파일의 굳힌 값 · 지문이 일정 구획과 어긋난다", r.returncode))
    else:
        도구["I-152"] = (None, "일정 구획 없음")

    # ② 엔진
    import dcf엔진                     # noqa: PLC0415
    엔진값 = collections.OrderedDict()
    엔진결과 = []                        # W4 — 세 시나리오의 엔진 결과(0 인 선택 기능 줄 · 안 쓰는 시트 몸통을 접는 데 쓴다)
    for 시 in 시나리오목록:
        try:
            결 = dcf엔진.계산(새가정, 시)
            요 = 결["요약"]
        except Exception as e:                                 # noqa: BLE001 — 엔진이 못 읽는 가정은 마감할 수 없다
            raise 마감오류("엔진이 %s 시나리오를 계산하지 못했다 — %s" % (시, e))
        엔진결과.append(결)
        엔진값[시] = collections.OrderedDict((k, 요[k]) for k in ("주당가치", "영업가치", "주주가치"))

    # ③ · ④ openpyxl — 기입 · 표지 · 접을 줄
    wb = openpyxl.load_workbook(워크북)
    try:
        지.워크북구조지문확인(wb, "워크북")
    except 좌표.좌표오류 as e:
        도구["I-151"] = (1, "%s" % e)
    줄들 = 점검줄들(wb, 지, 목록)
    n기입 = 기입(wb, 지, 엔진값)
    빈자리 = 빈칸자리(wb, 지, 새가정)
    # I-54 검증 시트 판 — 번호 · 점검 항목이 점검목록과 같은가
    판다른 = []
    for p, r, 자리 in 줄들:
        if r is None:
            판다른.append("%s 줄이 없다" % p["id"])
            continue
        이름 = 지.시트("15")
        번호값, 이름값 = wb[이름][자리["번호"]].value, wb[이름][자리["이름"]].value
        if 번호값 != p["id"] or 이름값 != p["이름"]:
            판다른.append("%s (워크북 %s · %s)" % (p["id"], 번호값, 이름값))
    # I-52 미사용 표지 — 워크북의 표지가 가정의 선언(구조가 쓰지 않는 매출 구분 포함)에서 나온 자리인가
    기대표지 = {(시, 번) for 시, 번, _열, _까닭, _글 in 미사용.표지자리(새가정)}
    적힌표지 = 표지찾기(wb, 지)
    손표지 = sorted(적힌표지 - 기대표지)
    도구["I-52"] = (1 if 손표지 else 0, ("가정 파일의 선언에 없는 「미사용」 표지 %d곳(%s)" % (len(손표지), " · ".join("%s번 %d" % x for x in 손표지[:6])))
                   if 손표지 else "표지 %d곳 = 선언" % len(적힌표지))
    # 접을 줄 — 표지가 적힌 매출 구분 · 미사용 줄, 이 회차에 해당하지 않는 점검 줄(구조 갈래로 적용 칸이 「=0」)
    접을 = []
    자리들, _오 = 미사용.풀기(새가정)
    for 갈래, 시, 번, _까닭 in 자리들:
        if 갈래 == "구분":
            if ("13", 85 + 번) in 적힌표지 or any(("12", h) in 적힌표지 for h in 미사용.매출구분머리(번)):
                접을 += 미사용.구분줄(번)
        elif (시, 번) in 적힌표지:
            접을 += (["S12R%03d" % n for n in range(번, 번 + 4)] if 시 == "12" else ["S%02dR%03d" % (int(시), 번)])
    구조접을 = [i for i, _까 in 미사용.구조접을줄(새가정, 엔진결과)]       # W4 — 엔진 값으로 접는 줄(매출명칭 구분의 0 인 단가 · 매출원가 없는 5번 몸통 · 0 인 선택 기능)
    접을 += [i for i in 구조접을 if i not in 접을]
    try:                                        # W4 — 17번 동인 지도와 근거의 빈 노드 줄(동인 지도가 채우지 않은 자리)
        s17 = 지.장(wb, "17")
        접을 += ["S17R%03d" % n for n in range(101, 181) if s17.값("노드", n) in (None, "")]
    except (좌표.좌표오류, KeyError, ValueError):
        pass
    해당없음 = []
    for p, r, 자리 in 줄들:
        if r is not None and 자리.get("적용") and wb[지.시트("15")][자리["적용"]].value == "=0":
            해당없음.append(p["행"])
    주당줄 = [p["행"] for p in 목록["세운"] if p.get("단위") == "주당"]
    납품시나리오 = ((가정.get("스위치") or {}).get("적용시나리오") or "기준") if isinstance(가정.get("스위치"), dict) else "기준"
    임시 = tempfile.mkdtemp(prefix="워크북마감_")
    try:
        사본1 = os.path.join(임시, "기입.xlsx")
        wb.save(사본1)
        생 = _생성기()
        if 생 not in sys.path:
            sys.path.insert(0, 생)
        import 서식마감                  # noqa: PLC0415
        사본2 = os.path.join(임시, "서식.xlsx")
        서식 = 서식마감.마감(사본1, 지.경로, 사본2, 안쓰는줄=접을 + 해당없음, 주당줄=주당줄)
        # ⑤ 재계산
        첫열 = 지.기간열()[0]
        읽을 = _읽을칸(지, 줄들, 첫열)
        방식, 계 = None, None
        if 재계산 in ("자동", "엑셀"):
            try:
                계 = 엑셀재계산(사본2, 낼곳, 지, 읽을, 납품시나리오)
                방식 = "엑셀"
            except Exception as e:                             # noqa: BLE001
                if 재계산 == "엑셀":
                    raise 마감오류("엑셀로 다시 계산하지 못했다 — %s" % e)
                방식 = "formulas (엑셀 실패: %s)" % ("%s" % e)[:80]
        if 계 is None:
            try:
                계 = formulas재계산(사본2, 낼곳, 지, 읽을, 납품시나리오)
                방식 = 방식 or "formulas"
            except Exception as e:                             # noqa: BLE001
                raise 마감오류("엑셀과 formulas 모두 다시 계산하지 못했다 — %s" % e)
    finally:
        shutil.rmtree(임시, ignore_errors=True)

    # ⑥ 판정
    미완 = []
    점검결과 = []
    셈 = collections.Counter()
    for p, r, 자리 in 줄들:
        if r is None:
            continue
        판 = {}
        표 = {}
        for 시 in 시나리오목록:
            값 = 계["시나리오"][시]["값"]
            판[시] = 값.get((p["id"], "결과"))
            표[시] = 값.get((p["id"], "표시"))
        의견 = 계["시나리오"]["기준"]["값"].get((p["id"], "의견"))
        울린 = [시 for 시 in 시나리오목록 if 판[시] in (1, 1.0)]
        한 = collections.OrderedDict([("id", p["id"]), ("구분", p["구분"]), ("이름", p["이름"]),
                                     ("판정", {시: 판[시] for 시 in 시나리오목록}), ("표시", {시: 표[시] for 시 in 시나리오목록}),
                                     ("값A", 계["시나리오"]["기준"]["값"].get((p["id"], "값A"))),
                                     ("값B", 계["시나리오"]["기준"]["값"].get((p["id"], "값B"))), ("의견", 의견)])
        점검결과.append(한)
        틀린표시 = [시 for 시 in 시나리오목록 if 표[시] not in 표시들]
        틀린판정 = [시 for 시 in 시나리오목록 if 판[시] not in (0, 1, 0.0, 1.0)]
        if 틀린표시 or 틀린판정:
            미완.append(("정합성", p["id"], p["이름"], "판정 %s · 표시 %s — 판정은 0 또는 1, 표시는 OK · Error · Review · N/A 다"
                       % (판.get(시나리오목록[0]), 표.get(시나리오목록[0]))))
            셈["표시"] += 1
            continue
        if not 울린:
            continue
        if p["구분"] in ("정합성", "완결성"):
            셈[p["구분"]] += 1
            자리글 = ""
            if 빈자리.get(p["id"]):
                x = 빈자리[p["id"]]
                자리글 = " — 빈 칸: %s%s" % (" · ".join(x[:8]), " 외 %d" % (len(x) - 8) if len(x) > 8 else "")
            미완.append((p["구분"], p["id"], p["이름"], "%s — 값 A %s · 값 B %s%s" % (" · ".join(울린), _금액글(한["값A"]), _금액글(한["값B"]), 자리글)))
        else:
            셈["검토 신호"] += 1
            모자람 = 의견요건(의견)
            if 모자람:
                셈["검토사항"] += 1
                미완.append(("검토사항", p["id"], p["이름"], "%s — %s. 가정 파일 「검토의견」의 %s 에 적는다" % (" · ".join(울린), 모자람, p["id"])))
            else:
                셈["의견 기재"] += 1
    # 도구 점검 — I-153 순환 · I-51 오류 값 칸 · I-53 엔진 = 워크북 · I-54 판 · C-51 의견 · 총괄 칸
    순환 = {시: 계["시나리오"][시]["순환"] for 시 in 시나리오목록 if 계["시나리오"][시]["순환"]}
    도구["I-153"] = (1 if 순환 else 0, ("순환 참조 — " + " · ".join("%s %s" % (시, ", ".join(x)) for 시, x in 순환.items())) if 순환
                    else ("순환 참조 없음" if 방식 == "엑셀" else "formulas — 값 없는 수식 칸으로 본다"))
    오류칸 = {시: 계["시나리오"][시]["오류칸"] for 시 in 시나리오목록}
    도구["I-51"] = (1 if any(오류칸.values()) else 0, "오류 값 칸 " + " · ".join("%s %d" % kv for kv in 오류칸.items())
                   + ("" if not any(오류칸.values()) else " (%s)" % " · ".join(계["시나리오"][시]["오류보기"][0] for 시 in 시나리오목록 if 계["시나리오"][시]["오류보기"])))
    다른값 = []
    for 시 in 시나리오목록:
        for 키 in 계산줄:
            w = 계["시나리오"][시]["값"].get(("계산", 키))
            e = 엔진값[시][키]
            문턱 = 1e-6 if 키 == "주당가치" else 1.0
            if not isinstance(w, (int, float)) or abs(w - e) > max(문턱, abs(e) * 1e-9):
                다른값.append("%s %s 엔진 %s · 워크북 %s" % (시, 키, _금액글(e), _금액글(w)))
    도구["I-53"] = (1 if 다른값 else 0, " · ".join(다른값[:4]) if 다른값 else "세 시나리오 × 주당가치 · 영업가치 · 주주가치 일치")
    도구["I-54"] = (1 if 판다른 else 0, ("15번 점검 줄이 점검목록과 다르다 — " + " · ".join(판다른[:5])) if 판다른 else "15번 점검 %d줄 = 점검목록" % len(목록["세운"]))
    # C-51 — 워크북의 의견 = 가정 파일의 의견(붓기가 옮긴 것). 워크북에 손으로 적은 의견은 다음 붓기 때 지워진다
    의견다른 = []
    가정의견 = {k: (v.get("의견") if isinstance(v, dict) else v) for k, v in (가정.get("검토의견") or {}).items()}
    for 한 in 점검결과:
        w = ("%s" % (한["의견"] or "")).strip()
        g = ("%s" % (가정의견.get(한["id"]) or "")).strip()
        if w and g and w != g:
            의견다른.append(한["id"])
        elif w and not g and 한["id"] not in _사유옮긴것(가정):
            의견다른.append(한["id"])
    도구["C-51"] = (1 if 의견다른 else 0, ("워크북의 검토 의견이 가정 파일과 다르다 — %s" % " · ".join(의견다른[:6])) if 의견다른
                   else "검토 의견 = 가정 파일(요건은 점검마다 본다)")
    # I-154 개인 정보 — 저장한 마감본의 문서 속성에 이 PC 의 사용자 이름(윈도 사용자 · 엑셀 사용자 이름)이 남았는가(W6d)
    이름들 = [x for x in {("%s" % (계.get("사용자이름") or "")).strip(), (os.environ.get("USERNAME") or "").strip()} if x]
    도구["I-154"] = 속성점검(낼곳, 이름들)
    총괄다른 = []
    for 시 in 시나리오목록:
        도구셈 = sum(1 for 한 in 점검결과 if 한["판정"][시] in (1, 1.0) and (한["구분"] != "검토사항" or not (한["의견"] or "").strip()))
        w = 계["시나리오"][시]["값"].get(("총괄", "결과"))
        if w is None or int(w) != 도구셈:
            총괄다른.append("%s 워크북 %s · 도구 %d" % (시, w, 도구셈))
    if 총괄다른:
        도구["총괄"] = (1, "15번 총괄 칸의 미결 수가 점검 줄과 다르다 — " + " · ".join(총괄다른))
    for 번호, (판, 글) in 도구.items():
        if 판:
            셈["도구"] += 1
            미완.append(("도구", 번호, _도구이름(번호, 목록), 글))
    # 옛 판정 글 — 마감본(납품 시나리오의 계산값)에 「확인 필요 — …」 꼴의 글이 남았는가
    옛글 = []
    if 방식 == "엑셀":                     # 수식이 낸 글만 본다 — 근거 칸에 사람이 적은 「해당 없음 — …」 은 판정 글이 아니다
        wf = openpyxl.load_workbook(낼곳)
        wv = openpyxl.load_workbook(낼곳, data_only=True)
        for ws in wv.worksheets:
            식 = wf[ws.title]
            for 줄 in ws.iter_rows():
                for c in 줄:
                    수식 = 식[c.coordinate].value
                    if isinstance(c.value, str) and 옛판정글.match(c.value) and isinstance(수식, str) and 수식.startswith("="):
                        옛글.append("%s!%s 「%s」" % (ws.title, c.coordinate, c.value[:30]))
    if 옛글:
        셈["옛 판정 글"] += 1
        미완.append(("도구", "글", "옛 판정 글", "%d칸 — %s" % (len(옛글), " · ".join(옛글[:4]))))

    판정 = "마감" if not 미완 else "미완"
    걸린 = [k for k in ("정합성", "완결성", "검토사항", "도구") if any(x[0] == k for x in 미완)]
    머리 = "워크북 마감 — 마감" if 판정 == "마감" else "워크북 마감 — 미완 %d건 (%s)" % (
        len(미완), " · ".join("%s %d" % (k, sum(1 for x in 미완 if x[0] == k)) for k in 걸린))
    L = [머리,
         "  대상        %s · %s" % (os.path.basename(워크북), os.path.basename(가정경로)),
         "  재계산      %s (비관 · 기준 · 낙관, %.0f초)%s" % (방식, 계.get("초", 0),
                                                     " — 계산값을 마감본에 저장했다" if 방식 == "엑셀" else " — 마감본에 계산값이 없다"),
         "  모델 점검    정합성 오류 %d건 · 완결성 미비 %d건 · 검토사항 %d건 (의견 기재 %d건 · 미결 %d건)"
         % (셈["정합성"], 셈["완결성"], 셈["검토 신호"], 셈["의견 기재"], 셈["검토사항"]),
         "  도구 점검    " + " · ".join("%s %s" % (k, "N/A" if v[0] is None else ("OK" if v[0] == 0 else "Error")) for k, v in 도구.items()),
         "  주당가치     " + " · ".join("%s %s" % (시, "{:,.2f}".format(엔진값[시]["주당가치"])) for 시 in 시나리오목록)
         + " — 1번 시나리오별 결과 %d칸에 실었다" % n기입,
         "  접은 줄      %d줄 (미사용 · 쓰지 않는 매출 구분 %d · 해당 없는 점검 %d) · 구획 번호 %d칸 · 주당 소수 %s"
         % (서식.get("접은 줄", 0), len(접을), len(해당없음), 서식.get("구획 번호", 0), 서식.get("주당 소수") or "아님(원 · 엔)"),
         "  가정 점검    판정에 넣지 않음(자체검사 — W7a)"]
    for 갈래, 번호, 이름, 글 in 미완:
        L.append("  [%s] %s %s — %s" % (갈래, 번호, 이름, 글))
    L.append("  → %s" % 낼곳)
    짝 = 곁지도쓰기(지, 낼곳)
    if 짝:
        L.append("  곁 좌표 지도 %s" % 짝)
    # ADDER English Edition: preserve internal coordinate-verified copy under 짓기/_internal_ko.xlsx
    # and automatically convert the deliverable workbook (`낼곳`) into 100% American English.
    if os.environ.get("ADDER_SKIP_EN_EXPORT") != "1":
        try:
            내부곳 = os.path.join(os.path.dirname(os.path.abspath(낼곳)), "짓기")
            if not os.path.isdir(내부곳):
                내부곳 = os.path.dirname(os.path.abspath(낼곳))
            내부파일 = os.path.join(내부곳, "_internal_ko.xlsx")
            if os.path.abspath(내부파일) != os.path.abspath(낼곳):
                shutil.copy2(낼곳, 내부파일)
                if 짝 and os.path.isfile(짝):
                    shutil.copy2(짝, 내부파일 + ".좌표지도.json")
            en_scripts = os.path.join(os.path.dirname(여기), "scripts")
            if en_scripts not in sys.path:
                sys.path.insert(0, en_scripts)
            import export_en_workbook as _en_wb  # noqa: PLC0415
            _en_info = _en_wb.convert_workbook(낼곳, 낼곳, recalc=(방식 == "엑셀"))
            L.append("  영문 변환    완료 (%d칸 · 수식 %d칸 · 남은 한글 %d칸)" % (
                _en_info["translated_cells"], _en_info["translated_formulas"], _en_info["remaining_korean_cells"]))
        except Exception as _en_exc:  # noqa: BLE001
            L.append("  영문 변환    경고 (%s)" % _en_exc)
    with open(낼곳, "rb") as f:
        책해시 = _해시(f.read())
    결 = collections.OrderedDict([
        ("판정", 판정), ("일시", datetime.datetime.now().isoformat(timespec="seconds")),
        ("가정", {"경로": os.path.abspath(가정경로), "해시": _가정해시(가정), "값해시": __import__("가정해시").값(가정)}),   # 값해시 — 글 블록을 뺀 해시(게이트 ⑥ · 2026-10-24 W10)
        ("워크북", {"원본": os.path.abspath(워크북), "마감본": os.path.abspath(낼곳), "파일해시": 책해시}),
        ("재계산", {"방식": 방식, "초": 계.get("초"), "열기초": 계.get("열기초"), "계산초": 계.get("계산초"), "재계산초": 계.get("재계산초"),
                  "쪽초": 계.get("쪽초"), "쪽나눔": 계.get("쪽")}),
        ("엔진", 엔진값), ("도구점검", {k: {"판정": v[0], "글": v[1]} for k, v in 도구.items()}),
        ("모델점검", 점검결과), ("접은줄", {"미사용": 접을, "해당없음": 해당없음}),
        ("미완목록", [{"갈래": a, "번호": b, "이름": c, "글": d} for a, b, c, d in 미완]),
        ("초", round(time.time() - 시작, 1))])
    return 결, L, (통과 if 판정 == "마감" else 발견)


def _사유옮긴것(가정):
    """붓기가 옛 사유 칸에서 옮긴 의견의 점검 번호들 — 가정의 「검토의견」에 없어도 워크북에 의견이 있는 것이 맞다."""
    try:
        import 붓기                     # noqa: PLC0415
    except Exception:                                          # noqa: BLE001
        return set()
    return {붓기.사유점검.get(k) for k, v in (가정.get("사유") or {}).items() if v and ("%s" % v).strip() and 붓기.사유점검.get(k)}


def _도구이름(번호, 목록):
    for x in 목록.get("도구") or ():
        if x["id"] == 번호:
            return x["이름"]
    return {"총괄": "15번 총괄 칸"}.get(번호, 번호)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(allow_abbrev=False, description="부은 워크북을 마감한다(재계산 · 판정 · 도구 기입 · 서식 · 쪽 나눔)")
    ap.add_argument("워크북")
    ap.add_argument("가정")
    ap.add_argument("--낼", default=None)
    ap.add_argument("--출력", default=None)
    ap.add_argument("--지도", default=None)
    ap.add_argument("--재계산", default="자동", choices=("자동", "엑셀", "formulas"))
    a = ap.parse_args()
    try:
        결, L, rc = 마감(a.워크북, a.가정, 낼곳=a.낼, 지도곳=a.지도, 재계산=a.재계산)
    except 마감오류 as e:
        print("워크북 마감 — 입력오류\n  %s" % e)
        sys.exit(입력오류)
    글 = "\n".join(L)
    print(글)
    if a.출력:
        with io.open(a.출력, "w", encoding="utf-8") as f:
            f.write(글 + "\n")
        with io.open(os.path.splitext(a.출력)[0] + ".json", "w", encoding="utf-8") as f:
            json.dump(결, f, ensure_ascii=False, indent=1, default=str)
    sys.exit(rc)


if __name__ == "__main__":
    main()

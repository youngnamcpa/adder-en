# -*- coding: utf-8 -*-
"""짓기 — 명세 + 배치 → xlsx + 좌표 지도.

쓰기:  python 짓기.py <명세 폴더> <배치 json | 같은배치> <낼 xlsx> [<낼 좌표지도 json>] [--서식 옛|표준|없음] [--기간 <가정.json>]
       --기간 : 가정 파일(또는 {평가기준일, 결산월, 실적연도수, 상세추정연수, 수렴연수} json)의 기간으로 시간축 열을 짓는다 — 열 ID 는 기간 ID 다.
                배치의 「열」은 그 축의 열 ID 로 적혀 있어야 한다(같은배치 · 납품 배치는 읽은 명세에서 낸다). 안 주면 명세의 틀(15열)로 짓는다.
       --서식 을 안 주면 배치의 「서식길」을 따르고, 배치에도 없으면 「옛」이다. 납품 배치(배치_납품.py)는 「표준」을 적어 둔다 —
       납품은 표준 서식 길이 기본이고, 옛 서식 길은 시험(옛 워크북과 칸 단위로 견주기)에 쓴다.
                      [--이름경고허용] [--합계범위승인] [--못박은열허용] [--경고허용] [--덧명세 파일.jsonl …] [--추적]
       종료 코드: 0 지었다 · 1 오류(파일을 내지 않았다) · 2 지었으나 위험한 경고가 있다(--경고허용 이면 0)
       깃발은 어느 차례로 적어도 된다(--덧명세 뒤의 글은 다음 깃발 앞까지 덧명세 파일이다).
       오류로 멈추면 파일을 내지 않는다. 낼 자리에 앞서 지은 파일이 남아 있으면 그렇다고 알린다(이번에 지은 것이 아니다).
       --추적 : 예상하지 못한 오류의 트레이스백을 보인다(고칠 때만).

명세 폴더는 줄 무늬 명세(책.json 에 "형식")거나 칸 단위 명세(명세추출이 낸 것)다. 칸 단위 명세는 열표를 입혀 읽는다.

배치(dict / JSON)의 모양 — 열은 모두 열 ID 로 부른다
  {"시트": [
     {"id": "S04", "이름": "4. Sales_working",
      "행": ["S04R001",                          # 명세의 행 — 적힌 순서대로 1행부터 놓는다
             "S06R012",                          # 다른 시트의 행도 실을 수 있다 — 행 ID 는 이름일 뿐이고 놓이는 시트는 배치가 정한다
             {"id": "S04R002", "행": 5},          # 행 번호를 못 박을 수도 있다(앞보다 커야 한다)
             {"빈줄": 1},                         # 합계 범위 안에 빈 줄을 두려면 {"빈줄": 1, "틈허용": true}
             {"새줄": "S04R501", "이름": "매출총이익", "단위": "백만원", "종류": "계산", "서식": "금액",
              "무늬": {"예측": "=[S04R054 매출액]@.-[S05R017 매출원가 합계]@."},   # 줄 무늬 명세의 행 한 줄과 같은 꼴
              "글": {…}, "값": {…}, "입력": […], "병합": […], "높이": 18,
              "칸": {"E1": {"v": 1}, "E2": {"손수식": "=…"}},                     # 칸마다 직접 줄 수도 있다(v · t · 손수식 · 메모 · 링크 만)
              "범위허용": true,      # 합계 범위 안에 끼워도 된다(범위가 넓어진다). 위치로 읽는 범위 안이면 오류
              "범위에넣기": true}],  # 바로 위(아래) 줄이 끝인 합계 범위를 이 줄까지 넓힌다
      "열": ["여백", "이름", {"새열": "번호", "폭": 7, "종류": "번호"}, "단위", …],   # 새 열 순서
             # 새 열의 "종류" 가 그 시트의 묶음에 드는 종류면 묶음으로 적은 무늬·범위가 그 열까지 는다
      "열맞춤": {"S06": {"H1": "판정", "H2": "사유"}},   # 다른 시트(S06)에서 옮겨 온 줄의 열 → 이 시트의 열. 안 적은 열은 같은 ID 의 열에 놓인다
      "뺄줄": […], "뺄열": […], "숨길줄": […], "숨길열": […], "범위허용": [행 ID …],
      "묶음": [{"줄": ["S04R023", "S04R040"], "수준": 1, "숨김": true}],      # 줄 묶음(그룹 접기) — 첫 줄·끝 줄
      "열묶음": [{"열": ["E7", "E11"], "수준": 1, "숨김": true}],
      "새이름": {"S04R054": "매출액 합계"},         # 이름 열의 글을 바꾼다
      "덧칸": {"S12R030": {"번호": {"v": "A-030"}}},  # 옛 줄의 빈 칸·새 열에 값(또는 {"손수식": …})을 더한다(이 시트의 열 ID)
      "줄서식": {"S04R054": {"굵게": true, "채움": "E2EFDA", "숫자서식": "#,##0", "높이": 20}},
      "틀고정": {"행": "S04R009", "열": "H1"},
      "인쇄": {"방향": "landscape", "용지": 9, "폭맞춤": 1, "높이맞춤": 0, "제목행": ["S04R001", "S04R008"],
               "제목열": ["여백", "단위"], "영역": "전부", "바닥글": {"가운데": "&A", "오른쪽": "&P / &N"},
               "여백": {"left": 0.4, "right": 0.4}, "가로가운데": true, "쪽나눔": ["S04R046"]},
      "조건부서식": [{"범위": ["[S15R010]@판정:[S15R030]@판정"], "값": "\"OK\"", "연산": "equal",
                     "글자색": "006100", "채움": "C6EFCE", "굵게": true},
                    {"범위": […], "수식": "=[S15R010]@$미결=1", "채움": "FFEB9C"}],
      "유효성": [{"범위": ["[S12R009]@값"], "목록": ["기말", "기중"]}],       # "경고": true 면 목록 밖 값을 막지 않고 경고만 한다
      # 아래 넷은 표준 서식 길에서만 쓴다
      "보기": {"확대": 85, "눈금선": false, "탭색": "808080"},              # 안 주면 서식표준의 시트 사양
      "열폭": {"근거3": 60},                                               # 열 ID → 폭. 안 주면 표준 폭(열 종류 · 글 열의 머리 글)
      # 「줄서식」의 표준 서식 열쇠: 종류(줄 종류를 덮는다 — 머리보조 · 산출 · 부제 도 쓸 수 있다) · 서식 · 선 · 들여 · 굵게 · 높이 ·
      #   칸꼴({열 ID: 칸 종류} — 그 칸의 종류를 못 박는다). 표준 서식 길에서 글자색 · 채움 · 숫자서식(직접 서식)은 입히지 않는다
      }],
   "서식길": "표준",                                # 이 배치를 지을 때의 기본 서식 길(명령줄 --서식 · 짓기(서식길=)이 앞선다)
   "별칭": {"매출합계": "S04R054"},
   "뺄시트": ["S07"]}                               # 통째로 뺄 시트. 그 시트의 줄 가운데 다른 시트에 실은 것은 남는다
  새 시트(14. 민감도 · 15. 검증)는 배치가 아니라 줄 무늬 명세 파일로 준다 — 명세읽기(폴더, 덧파일=[…S14.jsonl, …S15.jsonl]).
  줄의 덧 속성 「선」(소계/합계) · 「들여」(0·1·2) · 「굵게」는 줄 무늬 명세의 행 줄(또는 새 줄)에 적는다(표준 서식 길에서 쓴다).
  명세의 「종류」「서식」이 모자란 줄은 명세를 고치지 않고 배치의 「줄서식」으로 덮는다.

표준 서식 길이 세우는 것 (서식훅.py · 서식표준.py)
  · 칸마다 명명 스타일 — 줄 종류 · 열 종류 · 칸의 내용 · 수식이 다른 시트를 읽는지(새 배치에서 판정)로 정한다.
    목록 유효성이 걸린 칸은 선택 칸, 점검 줄의 판정 칸에는 조건부 서식(Error 빨강 · Review 주황)을 건다.
  · 열 폭 표준 · 제목/구획/머리 줄의 높이 · 구획머리와 머리 줄의 띠 · 소계선과 합계선 · 눈금선 · 확대 · 탭 색.
  · 병합은 제목 줄에만 남긴다(다른 줄의 병합은 풀고 한 번 알린다).
  · 인쇄 — 배치가 안 준 것은 시트 사양으로 채운다(방향 · 용지 · 폭 1쪽 맞춤 · 제목 행/열 반복 · 인쇄 영역 · 바닥글 · 여백).

줄을 다른 시트로 옮기기
  · 옮길 줄의 ID 를 놓을 시트의 「행」에 적는다(본 시트의 「행」에서는 뺀다 — 「뺄줄」에는 안 적는다).
  · 참조의 시트 머리는 그 줄이 지금 놓인 시트로 쓴다. 옮긴 줄이 「같은 시트의 다른 줄」을 읽던 수식은 다른 시트 참조가 되고,
    두 줄이 같은 시트에 모이면 시트 머리가 빠진다.
  · 범위는 양 끝이 같은 시트에 놓였을 때만 선다(한쪽만 옮기면 오류). 범위 안의 줄은 통째로 함께 옮긴다.
  · 옮긴 줄의 칸은 「열맞춤」을 거쳐 놓인 시트의 열에 놓인다. 값이 있는 칸의 열이 놓인 시트에 없으면 오류다.
  · 좌표 지도의 「행시트」(옮긴 줄 → 놓인 시트)·「열맞춤」이 그 자리를 싣는다. 구조 대조·값 대조가 그것을 따라간다.

지키는 것
  · 명세의 줄은 어느 시트의 「행」이나 본 시트의 「뺄줄」 가운데 꼭 한 곳에 있어야 한다(빠뜨림 방지). 열·시트도 같다(「뺄열」·「뺄시트」).
  · 배치의 열쇠와 ID 는 등록부와 맞댄다. 모르는 열쇠, 놓이지 않은 행·열 ID 를 적은 「새이름」·「줄서식」·「숨길줄」·
    「덧칸」·「뺄줄」, 이름 칸이 빈 줄의 「새이름」은 오류다(오타가 말없이 무시되지 않게).
  · 탭 이름은 서로 달라야 하고(대소문자 안 가림) 31자 안이어야 하며 [ ] : * ? / \\ 를 못 쓴다.
  · 범위 참조는 양 끝 ID 로 다시 세운다. 범위 안에 낯선 줄·열이 끼거나, 순서가 바뀌거나, 범위에 있던 줄이
    밖으로 나가면 오류다. 뺀 줄을 가리키는 참조가 남아도 오류다.
  · 범위에 줄을 더하는 규칙: 「범위허용」 표시가 있는 줄만 범위 안에 낄 수 있다. 합계 따위면 범위가 넓어지고,
    INDEX·MATCH 처럼 위치로 읽는 범위나 SUMPRODUCT·COUNTIFS 처럼 짝지어 읽는 범위면 오류다.
    「범위허용」·「범위에넣기」를 단 줄이 어느 범위에도 안 들면 오류다(합계에 안 더해진다).
  · 범위 가운데 줄만 뺀 경우: 위치로 읽는 범위면 오류, 합계 따위면 경고.
  · 범위 안에 빈 줄이 생긴 경우(「빈줄」· 행 번호 못 박기): 오류. 합계 범위(SUM·MAX·MIN·COUNT·AVERAGE 따위)는
    그 빈 줄에 「틈허용」을 달았을 때만 경고로 낮춘다. 위치로 읽는 범위와 빈 칸을 세는 함수(COUNTBLANK 따위)는 늘 오류다.
  · 서로 짝인 범위(MATCH 가 낸 위치를 INDEX 가 쓰는 두 범위, 한 함수가 자리끼리 짝지어 읽는 범위들)는
    새 배치에서도 크기와 열 차례가 같아야 한다.
  · 묶음으로 적은 범위는 새 배치의 묶음(그 종류의 열 전부)으로 다시 세운다. 묶음의 열 사이에 다른 열이 끼면 오류다.
    묶음에서 열을 빼면 한 번 알린다(그 묶음을 읽는 범위가 그만큼 준다).
  · 시간축 묶음에 열을 더하는 배치는, 그 묶음의 열 ID 를 못 박은 참조(@H3 · @E11 …)가 남아 있으면 오류다(목록을 낸다).
    무늬·글·값의 열 구간 열쇠가 그 묶음의 끝 열(첫 열)에 못 박혀 있어도(「E11」·「E2~E11」) 같은 목록에 싣는다 — 새 열에 놓이지 않는다.
    기간 열을 가정 파일이 정하는 구현이 끝나기 전까지 막아 둔다(0_결정.md). 시연할 때만 못박은열허용=True.
  · 줄 무늬 명세면 범위 지문(범위지문.py)과 견준다 — 명세를 손으로 고쳐 범위의 구성이 바뀌었으면 오류다.
  · 수식에 덧붙인 이름이 지금 줄 이름과 다르면 멈춘다(「다시쓰기」로 맞춘다). 일부러 안 맞추고 지을 때만 이름불일치허용=True.
  · 「=」로 시작하는 글을 칸에 그대로 넣지 않는다({"v": …, "t": "s"} 또는 손 수식으로). 「칸」·「덧칸」에 수식의 틀(f · 배열)이나
    모르는 열쇠를 주면 오류다(수식은 손 수식으로만 — 문법을 거친다).
  · 병합이 서로 겹치면 오류다(엑셀이 파일을 못 연다). 다른 시트로 옮긴 줄의 병합이 풀리면 한 번 알린다(「병합」 경고).
  · 2007년 표준 뒤에 나온 함수(IFNA · IFS · XLOOKUP · TEXTJOIN …)는 수식 글을 낼 때 「_xlfn.」 접두를 붙인다(접두 없이는 #NAME?).
  · 새 열의 「종류」는 열 종류 등록부나 그 시트의 묶음·축에 있는 이름이어야 한다.
  · 글 칸과 수식 속 문자열의 좌표(「E28」「12번 30행」)는 옮기지 않는다. 자리가 바뀐 배치면 몇 칸인지 경고로 알린다.
  · 지은 워크북에는 배치의 지문(좌표 지도의 「지문」과 같은 글자)을 사용자 지정 속성으로 남긴다.
  · 오류가 하나라도 있으면 파일을 내지 않는다(엄격=False 로 풀 수 있다).
"""
import sys
import os
import re
import json
import datetime
from copy import copy
from collections import OrderedDict, Counter

import openpyxl
from openpyxl.styles import Font, PatternFill
from openpyxl.utils.indexed_list import IndexedList
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.cell_range import MultiCellRange
from openpyxl.worksheet.formula import ArrayFormula
from openpyxl.worksheet.page import PageMargins
from openpyxl.worksheet.pagebreak import Break
from openpyxl.worksheet.properties import PageSetupProperties
from openpyxl.formatting.rule import Rule, CellIsRule, FormulaRule
from openpyxl.styles.differential import DifferentialStyle
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.comments import Comment
from openpyxl.xml.functions import fromstring

from 공통 import (열글자, 열번호, 행ID풀기, 시트이름쓰기, 손수식틀, 서식객체, 배치오류, 위치로읽나, 짝범위함수,
                못바꾸는함수, 호출구조, 글속좌표, 합계함수, 남은자리표시, 새함수접두, 펼침함수, 자리풀기, 자리열)
import 열표
import 줄무늬
import 서식훅
import 좌표지도
import 범위지문
import 고리검사

가정시트 = "S12"      # 기간 열(엔진 배열 순서)을 정하는 시트 — 좌표 지도의 「기간열」을 여기서 읽는다

# 위험한 경고 — 지어지기는 했으나 사람이 꼭 봐야 하는 것. 명령줄 짓기는 이런 경고가 있으면 종료 코드 2 를 낸다
위험경고 = ("덧붙인 이름", "등록부 밖의 줄", "범위 가운데 뺀 줄", "범위 가운데 뺀 열", "범위 안의 빈 줄", "범위에넣기",
        "묶음에서 빠진 열", "못 박은 열", "범위 지문 (합계 범위)", "범위 끝의 새 줄", "못 바꾼 참조", "병합")
서식길들 = ("옛", "표준", "없음")


def 칸명세읽기(폴더):
    """명세추출이 낸 칸 단위 명세(열 = 옛 열 글자)를 읽는다."""
    with open(os.path.join(폴더, "책.json"), encoding="utf-8") as f:
        책 = json.load(f)
    시트 = OrderedDict()
    for sid in 책["시트순서"]:
        with open(os.path.join(폴더, sid + ".json"), encoding="utf-8") as f:
            시트[sid] = json.load(f)
    테마 = None
    if os.path.exists(os.path.join(폴더, "테마.xml")):
        with open(os.path.join(폴더, "테마.xml"), "rb") as f:
            테마 = f.read()
    return {"책": 책, "시트": 시트, "테마": 테마, "폴더": os.path.abspath(폴더)}


def 명세읽기(폴더, 옛서식=True, 덧파일=(), 기간=None, 구조=None):
    """명세 폴더 → 열 ID 명세. 줄 무늬 명세면 펴서, 칸 단위 명세면 열표를 입혀서 돌려준다.

    줄 무늬 명세를 읽다 틀린 곳을 만나면 배치오류를 던진다(오류마다 파일 이름과 줄 번호가 붙는다).
    기간 : 가정 사전 · 가정 파일 경로 따위(줄무늬.읽기) — 주면 시간축 열을 그 회차의 열로 편다(열 ID = 기간 ID).
    구조 : 가정 사전 · 가정 파일 경로 · 구조 사전 — 그 「구조」 선언대로 줄을 편다(구조펴기.py). 안 주면 기간으로 준 가정의 「구조」.
    """
    try:
        with open(os.path.join(폴더, "책.json"), encoding="utf-8") as f:
            책 = json.load(f)
    except (OSError, ValueError) as e:
        raise 배치오류([{"종류": "명세 읽기", "시트": None, "자리": None, "파일": "책.json",
                     "설명": "%s 의 책.json 을 읽을 수 없다: %s" % (폴더, e)}])
    if str(책.get("형식", "")).startswith("줄무늬"):
        return 줄무늬.읽기(폴더, 옛서식, 덧파일, 기간=기간, 구조=구조)
    if 기간 is not None:
        raise 배치오류([{"종류": "기간", "시트": None, "자리": None, "파일": "책.json",
                     "설명": "칸 단위 명세(옛 스캐폴드에서 뽑은 것)는 열이 못 박혀 있어 기간으로 열을 지을 수 없다"}])
    return 열표.적용(칸명세읽기(폴더))


def 같은배치(명세):
    """옛 배치 그대로. 다른 배치를 만들 때의 출발점이기도 하다."""
    return {"시트": [{"id": sid, "이름": s.get("옛이름") or s.get("이름"),
                    "행": [r["id"] for r in s["행"]],
                    "열": [c["id"] for c in s["열"]]} for sid, s in 명세["시트"].items()]}


# 배치가 쓸 수 있는 열쇠 — 여기에 없는 열쇠는 오타로 보고 오류로 올린다(말없이 무시되지 않게)
_배치열쇠 = {"시트", "별칭", "설명", "뺄시트", "서식길"}
_시트열쇠 = {"id", "이름", "행", "열", "열맞춤", "뺄줄", "뺄열", "숨길줄", "숨길열", "범위허용", "묶음", "묶음요약아래", "열묶음",
          "새이름", "덧칸", "줄서식", "틀고정", "인쇄", "조건부서식", "유효성", "이름열", "설명", "보기", "열폭"}
_새줄열쇠 = {"새줄", "행", "이름", "단위", "종류", "서식", "쓰임", "무늬", "글", "값", "입력", "병합", "높이", "칸", "덧",
          "범위허용", "범위에넣기", "숨김", "선", "들여", "굵게", "틈허용", "메모", "칸꼴"}
_옛줄열쇠 = {"id", "행", "틈허용"}
_빈줄열쇠 = {"빈줄", "틈허용"}
_새열열쇠 = {"새열", "폭", "종류", "숨김", "범위허용"}
_줄서식열쇠 = {"굵게", "글자색", "채움", "숫자서식", "높이", "종류", "서식", "선", "들여", "칸꼴"}
_직접서식열쇠 = ("글자색", "채움", "숫자서식")      # 표준 서식 길에서는 입히지 않는다(명명 스타일 밖의 서식이 된다)
_re탭못쓰는 = re.compile(r"[\[\]:*?/\\]")


def 탭이름문제(이름):
    """엑셀 탭 이름으로 못 쓰는 까닭. 괜찮으면 None."""
    if not isinstance(이름, str) or not 이름.strip():
        return "탭 이름이 비었다"
    if len(이름) > 31:
        return "탭 이름이 31자를 넘는다(%d자): %s" % (len(이름), 이름)
    if _re탭못쓰는.search(이름):
        return "탭 이름에 못 쓰는 글자([ ] : * ? / \\)가 있다: %s" % 이름
    if 이름.startswith("'") or 이름.endswith("'"):
        return "탭 이름은 작은따옴표로 시작하거나 끝날 수 없다: %s" % 이름
    return None


def 배치꼴점검(배치):
    """배치의 뼈대 — 꼴이 틀리면 더 읽을 수 없으므로 배치오류로 멈춘다(트레이스백 대신 무엇이 틀렸는지 알린다)."""
    틀린 = []
    if not isinstance(배치, dict) or not isinstance(배치.get("시트"), list):
        raise 배치오류([{"종류": "배치", "시트": None, "자리": None, "설명": "배치는 {\"시트\": [ … ]} 꼴이어야 한다"}])
    for i, b in enumerate(배치["시트"], 1):
        if not isinstance(b, dict) or not isinstance(b.get("id"), str) or not b.get("id"):
            틀린.append("배치의 %d번째 시트에 「id」 가 없다: %s" % (i, json.dumps(b, ensure_ascii=False)[:80]))
            continue
        sid = b["id"]
        for 키, 꼴 in (("행", list), ("열", list), ("뺄줄", list), ("뺄열", list), ("숨길줄", list), ("숨길열", list), ("범위허용", list),
                     ("열맞춤", dict), ("새이름", dict), ("덧칸", dict), ("줄서식", dict), ("묶음", list), ("열묶음", list),
                     ("유효성", list), ("조건부서식", list)):
            if b.get(키) is not None and not isinstance(b[키], 꼴):
                틀린.append("%s 의 「%s」 는 %s 로 적는다" % (sid, 키, "목록([ ])" if 꼴 is list else "{ }"))
        for 항 in b.get("행") if isinstance(b.get("행"), list) else ():
            if not (isinstance(항, str) or (isinstance(항, dict) and (
                    isinstance(항.get("id"), str) or isinstance(항.get("새줄"), str) or "빈줄" in 항))):
                틀린.append("%s 의 「행」 에 읽을 수 없는 것이 있다(행 ID 글 · {\"id\"} · {\"새줄\"} · {\"빈줄\"}): %s" % (
                    sid, json.dumps(항, ensure_ascii=False)[:80]))
            elif isinstance(항, dict) and "빈줄" in 항 and not (isinstance(항["빈줄"], int) and not isinstance(항["빈줄"], bool) and 항["빈줄"] >= 1):
                틀린.append("%s 의 「빈줄」 은 1 이상의 줄 수로 적는다: %r" % (sid, 항["빈줄"]))
            elif isinstance(항, dict) and "행" in 항 and not (isinstance(항["행"], int) and not isinstance(항["행"], bool)):
                틀린.append("%s 의 줄 %s 의 「행」(행 번호)은 숫자로 적는다: %r" % (sid, 항.get("id") or 항.get("새줄"), 항["행"]))
        for 항 in b.get("열") if isinstance(b.get("열"), list) else ():
            if not (isinstance(항, str) or (isinstance(항, dict) and isinstance(항.get("새열"), str) and 항.get("새열"))):
                틀린.append("%s 의 「열」 에 읽을 수 없는 것이 있다(열 ID 글 · {\"새열\": …}): %s" % (sid, json.dumps(항, ensure_ascii=False)[:80]))
    for 키 in ("별칭",):
        if 배치.get(키) is not None and not isinstance(배치[키], dict):
            틀린.append("배치의 「%s」 은 { } 로 적는다" % 키)
    if 배치.get("뺄시트") is not None and not isinstance(배치["뺄시트"], list):
        틀린.append("배치의 「뺄시트」 는 목록으로 적는다")
    if 틀린:
        raise 배치오류([{"종류": "배치", "시트": None, "자리": None, "설명": x} for x in 틀린])


class _지은이:
    def __init__(self, 명세, 배치):
        배치꼴점검(배치)
        self.명세, self.배치 = 명세, 배치
        self.오류, self.경고 = [], []
        self.행자리 = {}     # 행 ID → 새 행 번호(놓인 시트에서)
        self.행소속 = {}     # 행 ID → 본 시트 ID(명세에서 그 줄이 적힌 시트. 새 줄은 배치가 놓은 시트)
        self.놓인 = {}       # 행 ID → 놓인 시트 ID(배치가 정한다)
        self.뺀줄 = set()
        self.뺀열 = {}       # sid → set(열 ID)
        self.열자리 = {}     # sid → {열 ID: 새 열 글자}
        self.새열순서 = {}   # sid → [열 ID …] 새 배치의 순서
        self.새이름 = {}     # sid → 새 시트 이름
        self.새순서 = {}     # sid → [(새 행 번호, 행 ID)] — 그 시트에 놓인 줄(다른 시트에서 옮겨 온 줄 포함)
        self.옛순서 = {}     # sid → {행 ID: 옛 순번}(명세의 순서)
        self.옛열순서 = {}   # sid → {열 ID: 옛 순번}
        self.옛끝번호 = {}   # sid → 명세에서 가장 큰 행 번호
        self.새줄 = OrderedDict()   # 배치가 끼운 줄: 행 ID → 배치 항목
        self.새열 = {}       # sid → {열 ID: 배치 항목}
        self.열맞춤 = {}     # 놓인 sid → {본 sid: {본 시트의 열 ID: 놓인 시트의 열 ID}}
        self.틈허용 = {}     # sid → 「틈허용」을 단 빈 줄의 행 번호들
        self.늘종류 = set()  # (sid, 열 종류) — 배치가 시간축 묶음에 열을 더한 곳
        self.못박은 = []     # 늘어난 묶음의 열 ID 를 못 박아 읽는 참조: (수식의 시트, 자리, 가리키는 줄, 열 ID)
        self.못박은열쇠 = []  # 늘어난 묶음의 끝(첫) 열에 못 박힌 열 구간 열쇠: (시트, 행 ID, 무늬|글|값, 열쇠, 열 ID)
        self.펼침 = {}       # 펼쳐지는 함수 이름 → [(시트, 자리) …]
        self.범위허용, self.범위에넣기 = set(), set()
        self.범위에든 = set()       # 「범위허용」·「범위에넣기」 줄 가운데 실제로 어느 범위에 든 것
        self.본시트들 = set()
        self.열범위허용 = {}
        self.칸틀 = {}       # (행 ID, 열 ID) → 틀 (짝 범위 점검이 위치 칸의 수식을 따라갈 때 쓴다)
        self._짝후보 = []
        self._행범위기억, self._열범위기억, self._알린묶음 = {}, {}, set()
        self.문 = 줄무늬.문맥만들기(명세)
        self.문.별칭 = dict(배치.get("별칭") or {})
        self._배치읽기()

    # ── 배치를 읽어 자리표를 만든다 ──
    def _배치읽기(self):
        시트들 = self.명세["시트"]
        for 키 in self.배치:
            if 키 not in _배치열쇠:
                self._오류("배치", None, None, "모르는 배치 열쇠: 「%s」" % 키)
        줄주인 = {r["id"]: sid for sid, s in 시트들.items() for r in s["행"]}
        뺄시트 = set(self.배치.get("뺄시트") or ())
        # 명세의 것 — 배치에 안 실린 시트(뺄시트)의 줄도 다른 시트로 옮겨 실을 수 있으므로 모든 시트를 먼저 읽는다
        for sid, 명 in 시트들.items():
            옛줄 = [r["id"] for r in 명["행"]]
            self.옛순서[sid] = {rid: i for i, rid in enumerate(옛줄)}
            self.옛열순서[sid] = {c["id"]: i for i, c in enumerate(명["열"])}
            self.옛끝번호[sid] = max([행ID풀기(rid)[1] or 0 for rid in 옛줄] or [0])
            for 줄 in 명["행"]:
                self.행소속[줄["id"]] = sid
                for cid, 한 in 줄["칸"].items():
                    if "f" in 한:
                        self.칸틀[(줄["id"], cid)] = 한["f"]
        이름본 = {}
        for b in self.배치["시트"]:
            sid = b["id"]
            if sid in self.본시트들:
                self._오류("배치", sid, None, "같은 시트가 배치에 두 번 적혔다(한 시트를 둘로 가를 수 없다): %s" % sid)
                continue
            self.본시트들.add(sid)
            for 키 in b:
                if 키 not in _시트열쇠:
                    self._오류("배치", sid, None, "모르는 배치 열쇠: 「%s」" % 키)
            # 탭 이름 — 겹치면 openpyxl 이 뒤 시트에 1 을 붙이고 수식은 앞 시트를 읽는다
            명 = 시트들.get(sid)
            이름 = b.get("이름") or ((명.get("옛이름") or 명.get("이름")) if 명 else sid)
            문제 = 탭이름문제(이름)
            if 문제:
                self._오류("탭 이름", sid, None, 문제)
            elif 이름.lower() in 이름본:
                self._오류("탭 이름", sid, None, "탭 이름이 다른 시트(%s)와 겹친다: %s" % (이름본[이름.lower()], 이름))
            else:
                이름본[이름.lower()] = sid
            if 명 is None:
                실은 = [키 for 키 in b if 키 not in ("id", "이름") and b[키]]
                if 실은:
                    self._오류("배치", sid, None, "명세에 없는 시트에 %s 을(를) 실었다 — 버려진다. 새 시트는 줄 무늬 명세 파일로 준다(명세읽기의 덧파일)"
                             % " · ".join("「%s」" % 키 for 키 in 실은))
                else:
                    self._경고("배치", sid, None, "명세에 없는 시트 — 빈 시트로 짓는다")
                continue
            self.새이름[sid] = 이름
            옛줄 = [r["id"] for r in 명["행"]]
            for rid, 새이름 in (b.get("새이름") or {}).items():
                self.문.행이름.setdefault(rid, []).append(새이름)
            뺄 = set(b.get("뺄줄", []))
            self.뺀줄 |= 뺄 & set(옛줄)
            self.범위허용 |= set(b.get("범위허용", []))
            self.틈허용[sid] = set()
            n, 순서, 본 = 0, [], set()
            for 항 in b.get("행", 옛줄):
                if isinstance(항, str):
                    항 = {"id": 항}
                if "빈줄" in 항:
                    for 키 in 항:
                        if 키 not in _빈줄열쇠:
                            self._오류("배치", sid, None, "모르는 열쇠: 빈줄의 「%s」" % 키)
                    k = int(항["빈줄"])
                    if 항.get("틈허용"):
                        self.틈허용[sid].update(range(n + 1, n + k + 1))
                    n += k
                    continue
                rid = 항.get("id") or 항.get("새줄")
                for 키 in 항:
                    if 키 not in (_새줄열쇠 if "새줄" in 항 else _옛줄열쇠):
                        self._오류("배치", sid, None, "모르는 열쇠: %s 의 「%s」" % (rid, 키))
                if "새줄" in 항:
                    if rid in self.행소속 or rid in 줄주인:
                        self._오류("배치", sid, None, "새 줄 ID 가 겹친다: %s" % rid)
                        continue
                    머리 = 행ID풀기(rid)[0]
                    if 머리 is not None and 머리 != sid:      # 번호 꼴 ID 의 시트 머리 = 그 줄이 태어난 시트
                        self._오류("배치", sid, None, "새 줄 ID 의 시트 머리(%s)가 놓인 시트(%s)와 다르다: %s" % (머리, sid, rid))
                        continue
                    self.행소속[rid] = sid
                    self.문.행소속[rid] = sid
                    self.새줄[rid] = 항
                    if 항.get("이름") and not str(항["이름"]).startswith("="):
                        self.문.행이름[rid] = [항["이름"]]
                    if 항.get("쓰임"):
                        if 항["쓰임"] not in self.문.쓰임.get(sid, {}):
                            self._오류("배치", sid, None, "새 줄 %s 의 쓰임 「%s」 가 이 시트의 쓰임 표에 없다" % (rid, 항["쓰임"]))
                        self.문.행쓰임[rid] = 항["쓰임"]
                    for 키, 표 in (("종류", 줄무늬.줄종류들), ("서식", 줄무늬.서식이름들())):
                        if 항.get(키) is not None and 항[키] not in 표:
                            self._오류("배치", sid, None, "새 줄 %s 의 %s 「%s」 를 모른다" % (rid, 키, 항[키]))
                    if 항.get("칸") is not None and not isinstance(항["칸"], dict):
                        self._오류("배치", sid, [rid, None], "새 줄 %s 의 「칸」 은 {열 ID: {…}} 로 적는다" % rid)
                        항 = dict(항, 칸={})
                        self.새줄[rid] = 항
                    for cid, 한 in (항.get("칸") or {}).items():      # 칸의 안쪽 열쇠 — 수식의 틀(f)은 문법을 안 거친다
                        문제 = 줄무늬.덧문제(한, 줄무늬.칸열쇠)
                        if 문제:
                            self._오류("배치", sid, [rid, cid], "새 줄 %s 의 칸 「%s」 — %s" % (rid, cid, 문제))
                    if 항.get("범위허용"):
                        self.범위허용.add(rid)
                    if 항.get("범위에넣기"):
                        self.범위에넣기.add(rid)
                elif rid not in 줄주인:
                    self._오류("배치", sid, None, "명세에 없는 행 ID: %s" % rid)
                    continue
                if rid in self.놓인:
                    self._오류("배치", sid, None, "같은 줄이 두 번 놓였다: %s (%s 에 이미 놓였다)" % (rid, self.놓인[rid]))
                    continue
                self.놓인[rid] = sid
                본.add(rid)
                if "행" in 항:
                    if 항["행"] <= n:
                        self._오류("배치", sid, None, "행 번호가 앞줄보다 크지 않다: %s → %d" % (rid, 항["행"]))
                    elif 항.get("틈허용"):
                        self.틈허용[sid].update(range(n + 1, 항["행"]))
                    n = 항["행"]
                else:
                    n += 1
                self.행자리[rid] = n
                순서.append((n, rid))
            self.새순서[sid] = 순서
            # 열
            self.뺀열[sid] = set(b.get("뺄열", []))
            self.새열[sid], self.열범위허용[sid] = {}, set()
            자리, 순, k = {}, [], 0
            for 항 in b.get("열", [c["id"] for c in 명["열"]]):
                k += 1
                cid = 항 if isinstance(항, str) else 항["새열"]
                if cid in 자리:
                    self._오류("배치", sid, None, "같은 열이 두 번 놓였다: %s" % cid)
                    continue
                if not isinstance(항, str):
                    for 키 in 항:
                        if 키 not in _새열열쇠:
                            self._오류("배치", sid, None, "모르는 열쇠: 새 열 %s 의 「%s」" % (cid, 키))
                    if cid in self.옛열순서[sid] or cid in self.문.묶음.get(sid, {}):
                        self._오류("배치", sid, None, "새 열 ID 가 있는 열·묶음 이름과 겹친다: %s" % cid)
                    if cid in {c.get("옛") for c in 명["열"]}:
                        self._오류("배치", sid, None, "새 열 ID 가 옛 열 글자와 겹친다(좌표 지도의 「열」 표에서 헷갈린다): %s" % cid)
                    if 항.get("종류", "기타") not in 줄무늬.아는열종류(명):
                        self._오류("배치", sid, None, "새 열 %s 의 종류 「%s」 를 모른다 (등록된 종류: %s · 이 시트의 묶음·축의 종류)" % (
                            cid, 항.get("종류"), " · ".join(줄무늬.열종류들)))
                    self.새열[sid][cid] = 항
                    self.문.열종류[sid][cid] = 항.get("종류", "기타")
                    if 항.get("범위허용"):
                        self.열범위허용[sid].add(cid)
                    if 항.get("종류") in set(명.get("축", ())):
                        self.늘종류.add((sid, 항["종류"]))
                elif cid not in self.옛열순서[sid]:
                    self._오류("배치", sid, None, "명세에 없는 열 ID: %s" % cid)
                    continue
                자리[cid] = 열글자(k)
                순.append(cid)
            for c in 명["열"]:
                if c["id"] not in 자리 and c["id"] not in self.뺀열[sid]:
                    self._오류("배치", sid, None, "열이 배치에서 빠졌다: %s" % c["id"])
            self.열자리[sid], self.새열순서[sid] = 자리, 순
            self.문.새순서[sid] = 순
            # 시간축 열은 서로의 차례를 지켜야 한다(직전 열·다음 열의 뜻이 바뀐다)
            축종류 = set(명.get("축", ()))
            옛축 = [c["id"] for c in 명["열"] if c.get("종류") in 축종류 and c["id"] in 자리]
            if 옛축 != [c for c in 순 if c in set(옛축)]:
                self._오류("배치", sid, None, "시간축 열의 차례가 바뀌었다")
            # 다른 시트에서 옮겨 온 줄의 열 맞춤
            self.열맞춤[sid] = {}
            for 본sid, 표 in (b.get("열맞춤") or {}).items():
                if 본sid not in 시트들 or 본sid == sid:
                    self._오류("배치", sid, None, "「열맞춤」의 시트를 모른다(옮겨 온 줄의 본 시트 ID 를 적는다): %s" % 본sid)
                    continue
                for 본열, 새열 in 표.items():
                    if 본열 not in self.옛열순서[본sid]:
                        self._오류("배치", sid, None, "「열맞춤」에 %s 시트에 없는 열 ID: %s" % (본sid, 본열))
                    if 새열 not in 자리:
                        self._오류("배치", sid, None, "「열맞춤」이 이 시트에 놓이지 않은 열을 가리킨다: %s → %s" % (본열, 새열))
                if len(set(표.values())) != len(표):
                    self._오류("배치", sid, None, "「열맞춤」에서 %s 시트의 두 열이 같은 열로 맞춰졌다" % 본sid)
                self.열맞춤[sid][본sid] = dict(표)
            # 배치의 오타 — 등록부에 없는 ID 를 적은 설정은 말없이 넘기지 않는다
            for rid in sorted(뺄 - set(옛줄)):
                self._오류("배치", sid, None, "「뺄줄」에 이 시트의 명세에 없는 행 ID: %s (다른 시트에서 옮겨 온 줄은 본 시트의 「뺄줄」에 적는다)" % rid
                         if rid in 줄주인 else "「뺄줄」에 명세에 없는 행 ID: %s" % rid)
            for 키 in ("새이름", "줄서식", "덧칸"):
                for rid in (b.get(키) or {}):
                    if rid not in 본:
                        self._오류("배치", sid, None, "「%s」에 이 시트에 놓이지 않은 행 ID: %s" % (키, rid))
            for 키 in ("숨길줄", "범위허용"):
                for rid in (b.get(키) or []):
                    if rid not in 본:
                        self._오류("배치", sid, None, "「%s」에 이 시트에 놓이지 않은 행 ID: %s" % (키, rid))
            for rid, 칸들 in (b.get("덧칸") or {}).items():
                if not isinstance(칸들, dict):
                    self._오류("배치", sid, [rid, None], "「덧칸」의 %s 는 {열 ID: {…}} 로 적는다" % rid)
                    b["덧칸"] = dict(b["덧칸"], **{rid: {}})
                    continue
                for cid, 한 in 칸들.items():
                    if cid not in 자리:
                        self._오류("배치", sid, None, "「덧칸」에 이 시트에 놓이지 않은 열 ID: %s 의 %s" % (rid, cid))
                    문제 = 줄무늬.덧문제(한, 줄무늬.칸열쇠)
                    if 문제:
                        self._오류("배치", sid, [rid, cid], "「덧칸」 %s 의 「%s」 — %s" % (rid, cid, 문제))
            for cid in sorted(self.뺀열[sid] - set(self.옛열순서[sid])):
                self._오류("배치", sid, None, "「뺄열」에 명세에 없는 열 ID: %s" % cid)
            for cid in (b.get("숨길열") or []):
                if cid not in 자리:
                    self._오류("배치", sid, None, "「숨길열」에 이 시트에 놓이지 않은 열 ID: %s" % cid)
            for cid in self.뺀열[sid] & set(자리):
                self._오류("배치", sid, None, "「열」과 「뺄열」에 함께 있다: %s" % cid)
        # 명세의 줄은 어느 시트엔가 놓이거나 뺄줄에 있어야 한다
        for sid, 명 in 시트들.items():
            if sid not in self.본시트들 and sid not in 뺄시트:
                self._오류("배치", sid, None, "시트가 배치에서 빠졌다(「시트」에도 「뺄시트」에도 없다): %s" % sid)
                continue
            for 줄 in 명["행"]:
                rid = 줄["id"]
                if rid in self.놓인 and rid in self.뺀줄:
                    self._오류("배치", sid, None, "「행」과 「뺄줄」에 함께 있다: %s" % rid)
                elif rid not in self.놓인 and rid not in self.뺀줄:
                    if sid in 뺄시트:
                        self.뺀줄.add(rid)          # 통째로 뺀 시트의 줄 — 다른 시트에 실은 것만 남는다
                    else:
                        self._오류("배치", sid, None, "배치에서 빠졌다(어느 시트의 「행」에도 「뺄줄」에도 없다): %s" % rid)
        for sid in 뺄시트:
            if sid not in 시트들:
                self._오류("배치", sid, None, "「뺄시트」에 명세에 없는 시트: %s" % sid)
            elif sid in self.본시트들:
                self._오류("배치", sid, None, "「시트」와 「뺄시트」에 함께 있다: %s" % sid)

    def _오류(self, 종류, sid, 자리, 설명, **덧):
        self.오류.append(dict({"종류": 종류, "시트": sid, "자리": 자리, "설명": 설명}, **덧))

    def _경고(self, 종류, sid, 자리, 설명, **덧):
        self.경고.append(dict({"종류": 종류, "시트": sid, "자리": 자리, "설명": 설명}, **덧))

    # ── ID → 새 좌표 ──
    def 본시트(self, rid):
        """행 ID → 본 시트 ID(명세에서 그 줄이 적힌 시트). 등록부 밖의 줄은 ID 의 시트 머리."""
        return self.행소속.get(rid) or 행ID풀기(rid)[0]

    def 놓인시트(self, rid):
        """행 ID → 지금 놓인 시트 ID. 놓이지 않은 줄(뺀 줄 · 등록부 밖의 줄)은 본 시트."""
        return self.놓인.get(rid) or self.본시트(rid)

    def 새행(self, rid):
        """행 ID → 새 행 번호. 뺀 줄이면 None. 등록부 끝을 넘는 번호는 끝에서 떨어진 만큼 민다."""
        if rid in self.행자리:
            return self.행자리[rid]
        if rid in self.뺀줄:
            return None
        sid, 옛 = 행ID풀기(rid)
        if sid in self.새순서 and rid not in self.옛순서[sid]:
            옛끝 = self.옛끝번호[sid]
            새끝 = self.새순서[sid][-1][0] if self.새순서[sid] else 0
            if 옛 > 옛끝:
                return 새끝 + (옛 - 옛끝)
        raise KeyError(rid)

    def 놓인행(self, rid, sid=None):
        """배치가 놓은 줄의 새 행 번호. 놓이지 않은 줄(뺀 줄 · 모르는 ID)이나 다른 시트에 놓인 줄이면 KeyError."""
        if rid in self.행자리 and (sid is None or self.놓인.get(rid) == sid):
            return self.행자리[rid]
        raise KeyError(rid)

    def 묶음새열(self, sid, 이름):
        """묶음 이름 → 새 배치에서 그 묶음의 열 ID 목록(새 순서). 묶음이 아니면 None."""
        종류들 = self.문.묶음.get(sid, {}).get(이름)
        if 종류들 is None or sid not in self.새열순서:
            return None
        return [c for c in self.새열순서[sid] if self.문.든다(sid, c, 종류들)]

    def _자리열(self, sid, cid, 자, m):
        c = 자리열(m, 자[1])
        if c is None:
            raise KeyError("%s 의 자리 「%s」 — 묶음 「%s」 에 그 자리가 없다(이 배치에서 그 묶음의 열은 %d개)" % (sid, cid, 자[0], len(m)))
        return c

    def 열풀기(self, sid, cid):
        """자리 이름(「묶음.첫」「묶음.끝」「묶음.k」「묶음.끝k」) → 새 배치에서의 열 ID. 그 밖은 그대로."""
        자 = 자리풀기(cid)
        if 자:
            m = self.묶음새열(sid, 자[0])
            if m is not None and (m or sid in self.문.기간틀):
                return self._자리열(sid, cid, 자, m)
        return cid

    def 새열글자(self, sid, cid):
        """(시트의) 열 ID → 새 열 글자. 뺀 열이면 None. 모르는 열이면 KeyError."""
        cid = self.열풀기(sid, cid)
        자리 = self.열자리[sid]
        if cid in 자리:
            return 자리[cid]
        if cid in self.뺀열.get(sid, ()):
            return None
        raise KeyError("%s!%s" % (sid, cid))

    def 옮긴열(self, rid, cid):
        """행 rid 의 열(본 시트의 열 ID) → (놓인 시트 ID, 그 시트의 열 ID). 옮긴 줄은 「열맞춤」을 거친다."""
        본, 놓 = self.본시트(rid), self.놓인시트(rid)
        자 = 자리풀기(cid) if cid not in self.열자리.get(놓, ()) else None
        if 자:
            m = self.묶음새열(놓, 자[0])
            if m is not None and (m or 놓 in self.문.기간틀):
                return 놓, self._자리열(놓, cid, 자, m)
            if 놓 != 본:
                raise KeyError("%s 에는 묶음 「%s」 가 없다(%s 에서 옮겨 온 줄 %s)" % (놓, 자[0], 본, rid))
            return 놓, cid
        if 놓 != 본:
            cid = self.열맞춤.get(놓, {}).get(본, {}).get(cid, cid)
        return 놓, cid

    def 칸글자(self, rid, cid):
        """행 ID + (본 시트의) 열 ID → (놓인 시트 ID, 새 열 글자). 뺀 열이면 글자가 None. 모르는 열이면 KeyError."""
        놓, c = self.옮긴열(rid, cid)
        자리 = self.열자리.get(놓)
        if 자리 is None:
            raise KeyError("%s 시트가 배치에 없다" % 놓)
        if c in 자리:
            return 놓, 자리[c]
        if 놓 == self.본시트(rid) and c in self.뺀열.get(놓, ()):
            return 놓, None
        raise KeyError("%s!%s" % (놓, c) + ("" if 놓 == self.본시트(rid) else " (%s 에서 옮겨 온 줄 %s 의 열 %s — 「열맞춤」에 적는다)" % (self.본시트(rid), rid, cid)))

    def 못박은열쇠찾기(self, sid, rid, 낸):
        """는 묶음의 끝(첫) 열에 못 박힌 열 구간 열쇠를 찾아 적어 둔다 — 그 줄의 무늬·글·값이 새 열에 놓이지 않는다.

        묶음의 끝 쪽에 열이 늘었으면 끝 자리가 옛 끝 열 ID 인 열쇠(「E11」·「E2~E11」), 첫 쪽에 늘었으면 첫 자리가 옛 첫 열 ID 인 열쇠.
        「E2~예측」·「예측.끝」처럼 묶음으로 적은 것과, 그 줄 쓰임의 별칭으로 적은 것(시간축이 아닌 칸)은 걸리지 않는다.
        """
        종 = self.문.열종류[sid]
        명열 = [c["id"] for c in self.명세["시트"][sid]["열"]]
        for sid2, 종류 in self.늘종류:
            if sid2 != sid:
                continue
            옛 = [c for c in 명열 if 종.get(c) == 종류 and c in self.열자리[sid]]
            새 = [c for c in self.새열순서[sid] if 종.get(c) == 종류]
            if not 옛:
                continue
            끝늘, 첫늘 = 새.index(옛[-1]) < len(새) - 1, 새.index(옛[0]) > 0
            for 갈래 in ("무늬", "글", "값"):
                for 키 in (낸.get(갈래) or {}):
                    낱 = str(키).split("~")
                    if 끝늘 and 낱[-1] == 옛[-1]:
                        self.못박은열쇠.append((sid, rid, 갈래, 키, 옛[-1]))
                    elif 첫늘 and 낱[0] == 옛[0]:
                        self.못박은열쇠.append((sid, rid, 갈래, 키, 옛[0]))

    def _역맞춤(self, 놓, 본):
        return {v: k for k, v in self.열맞춤.get(놓, {}).get(본, {}).items()}

    def _행범위(self, r1, r2, 의존):
        """범위의 양 끝 행 ID 를 새 배치에서 점검한다. → (문제, 가운데서 빠진 줄, 새 첫 행, 새 끝 행, 알림, 틈, 허용 안 된 틈)

        틈 = 범위 안에 생긴 빈 줄 수(배치의 「빈줄」이나 행 번호 못 박기로 줄 사이가 벌어진 것).
        범위는 양 끝이 같은 시트에 놓였을 때만 선다. 줄의 옛 순서는 본 시트(명세)의 것, 새 순서는 놓인 시트의 것이다.
        """
        키 = (r1, r2, bool(의존))
        if 키 in self._행범위기억:
            return self._행범위기억[키]
        본 = self.본시트(r1)
        문제, 가운데뺀, 알림, 틈, 막힌틈 = [], [], [], 0, 0
        n1, n2 = self.행자리.get(r1), self.행자리.get(r2)
        옛 = self.옛순서.get(본, {})
        if r1 != r2 and n1 is not None and n2 is not None:
            놓 = self.놓인[r1]
            if self.놓인[r2] != 놓:
                문제.append("범위의 두 끝이 다른 시트에 놓였다(%s 는 %s, %s 는 %s) — 범위는 양 끝이 같은 시트일 때만 선다. 범위의 줄을 통째로 옮긴다"
                          % (r1, 놓, r2, self.놓인[r2]))
                결 = (문제, 가운데뺀, n1, n2, 알림, 틈, 막힌틈)
                self._행범위기억[키] = 결
                return 결
            a, b = sorted((n1, n2))
            새줄 = [rid for n, rid in self.새순서[놓] if a <= n <= b]
            찬 = {n for n, _ in self.새순서[놓] if a <= n <= b}
            빈 = set(range(a, b + 1)) - 찬
            틈, 막힌틈 = len(빈), len(빈 - self.틈허용.get(놓, set()))
            if r1 in 옛 and r2 in 옛:
                lo, hi = sorted((옛[r1], 옛[r2]))
                옛줄 = [r["id"] for r in self.명세["시트"][본]["행"][lo:hi + 1]]
                옛집 = set(옛줄)
                if (n1 - n2) * (옛[r1] - 옛[r2]) < 0:
                    문제.append("범위의 양 끝 순서가 뒤집혔다")
                낯선 = [x for x in 새줄 if x not in 옛집]
                막힌 = [x for x in 낯선 if x not in self.범위허용]
                if 막힌:
                    문제.append("범위 안에 낯선 줄이 끼었다: %s" % ", ".join(막힌[:5]))
                허용 = [x for x in 낯선 if x in self.범위허용]
                if 허용 and 의존:
                    문제.append("위치로 읽는 범위(INDEX·MATCH·SUMPRODUCT 따위) 안에는 줄을 더할 수 없다: %s" % ", ".join(허용[:5]))
                self.범위에든.update(허용)
                남은 = [x for x in 옛줄 if x not in self.뺀줄]
                나간 = [x for x in 남은 if x not in set(새줄)]
                if 나간:
                    문제.append("범위에 있던 줄이 범위 밖으로 나갔다: %s" % ", ".join(나간[:5]))
                if [x for x in 새줄 if x in 옛집] != [x for x in 남은 if x in set(새줄)]:
                    문제.append("범위 안 줄의 순서가 바뀌었다")
                가운데뺀 = [x for x in 옛줄 if x in self.뺀줄]
            # 「범위에넣기」 — 범위 끝에 바로 붙은 새 줄까지 넓힌다(위치로 읽는 범위는 안 넓힌다)
            차례 = self.새순서[놓]
            번호 = {n: i for i, (n, _) in enumerate(차례)}
            for 방향 in (1, -1):
                끝 = b if 방향 == 1 else a
                while True:
                    i = 번호[끝] + 방향
                    if not (0 <= i < len(차례)) or 차례[i][0] != 끝 + 방향 or 차례[i][1] not in self.범위에넣기:
                        break
                    if 의존:
                        알림.append("범위 끝에 「범위에넣기」 줄(%s)이 붙어 있으나 위치로 읽는 범위라 넓히지 않았다" % 차례[i][1])
                        break
                    self.범위에든.add(차례[i][1])
                    끝 += 방향
                if 방향 == 1:
                    b = 끝
                else:
                    a = 끝
            n1, n2 = (a, b) if n1 <= n2 else (b, a)
        결 = (문제, 가운데뺀, n1, n2, 알림, 틈, 막힌틈)
        self._행범위기억[키] = 결
        return 결

    def _열범위(self, sid, c1, c2, 의존):
        """→ (문제, 가운데서 빠진 열)"""
        키 = (sid, c1, c2, bool(의존))
        if 키 in self._열범위기억:
            return self._열범위기억[키]
        문제, 가운데뺀 = [], []
        옛 = self.옛열순서.get(sid, {})
        자리 = self.열자리[sid]
        if c1 in 옛 and c2 in 옛 and c1 != c2 and c1 in 자리 and c2 in 자리:
            lo, hi = sorted((옛[c1], 옛[c2]))
            옛열 = [c["id"] for c in self.명세["시트"][sid]["열"][lo:hi + 1]]
            옛집 = set(옛열)
            순 = self.새열순서[sid]
            i1, i2 = 순.index(c1), 순.index(c2)
            if (i1 - i2) * (옛[c1] - 옛[c2]) < 0:
                문제.append("범위의 양 끝 열 순서가 뒤집혔다")
            a, b = sorted((i1, i2))
            새열 = 순[a:b + 1]
            낯선 = [x for x in 새열 if x not in 옛집]
            막힌 = [x for x in 낯선 if x not in self.열범위허용[sid]]
            if 막힌:
                문제.append("범위 안에 낯선 열이 끼었다: %s" % ", ".join(막힌[:5]))
            허용 = [x for x in 낯선 if x in self.열범위허용[sid]]
            if 허용 and 의존:
                문제.append("위치로 읽는 범위 안에는 열을 더할 수 없다: %s" % ", ".join(허용[:5]))
            남은 = [x for x in 옛열 if x not in self.뺀열.get(sid, ())]
            나간 = [x for x in 남은 if x not in set(새열)]
            if 나간:
                문제.append("범위에 있던 열이 범위 밖으로 나갔다: %s" % ", ".join(나간[:5]))
            if [x for x in 새열 if x in 옛집] != [x for x in 남은 if x in set(새열)]:
                문제.append("범위 안 열의 순서가 바뀌었다")
            가운데뺀 = [x for x in 옛열 if x in self.뺀열.get(sid, ())]
        self._열범위기억[키] = (문제, 가운데뺀)
        return 문제, 가운데뺀

    def _옮긴열범위(self, 본, 놓, c1, c2):
        """다른 시트로 옮긴 줄의 열 범위 — 본 시트에서 범위에 들던 열들이 놓인 시트에서도 같은 차례로 붙어 있어야 한다. → 문제 목록"""
        옛 = self.옛열순서.get(본, {})
        if c1 not in 옛 or c2 not in 옛:
            return []
        lo, hi = sorted((옛[c1], 옛[c2]))
        맞 = self.열맞춤.get(놓, {}).get(본, {})
        새 = [맞.get(c["id"], c["id"]) for c in self.명세["시트"][본]["열"][lo:hi + 1]]
        순 = self.새열순서[놓]
        없는 = [c for c in 새 if c not in 순]
        if 없는:
            return ["옮긴 줄의 열 범위(%s:%s)에 놓인 시트(%s)에 없는 열이 있다: %s — 「열맞춤」에 적는다" % (c1, c2, 놓, ", ".join(없는[:5]))]
        i = 순.index(새[0])
        if 순[i:i + len(새)] != 새:
            return ["옮긴 줄의 열 범위(%s:%s)가 놓인 시트(%s)에서 같은 차례로 붙어 있지 않다" % (c1, c2, 놓)]
        return []

    def _묶음끝(self, sid, 이름, 현재sid, 자리):
        """묶음으로 적은 범위의 새 두 끝 열 ID. 묶음의 열이 새 배치에서 한데 붙어 있어야 한다."""
        m = self.묶음새열(sid, 이름)
        if not m:
            self._오류("묶음", 현재sid, 자리, "묶음 「%s」 의 열이 %s 에 하나도 없다" % (이름, sid))
            return None, None
        순 = self.새열순서[sid]
        i, j = 순.index(m[0]), 순.index(m[-1])
        if 순[i:j + 1] != m:
            self._오류("묶음", 현재sid, 자리, "묶음 「%s」 의 열 사이에 다른 열이 끼었다: %s" % (
                이름, ", ".join(c for c in 순[i:j + 1] if c not in m)))
        return m[0], m[-1]

    def 범위끝(self, p, 현재sid=None, 자리=None, 점검=False, 감싼=None):
        """범위 참조 → 새 배치에서의 (놓인 시트 ID, 첫 행, 끝 행, 첫 열 ID, 끝 열 ID). 점검=True 면 범위 점검도 한다.

        열 ID 는 놓인 시트의 것이다. 감싼 : 이 범위를 바로 감싼 함수 이름을 돌려주는 함수(범위 안에 빈 줄이 생겼을 때만 부른다).
        """
        본, 놓 = self.본시트(p["r"]), self.놓인시트(p["r"])
        의존 = 위치로읽나(p)
        문제, 뺀, n1, n2, 알림, 틈, 막힌틈 = self._행범위(p["r"], p["r2"], 의존)
        if 점검:
            for m in 문제:
                self._오류("범위 깨짐", 현재sid, 자리, "%s:%s — %s" % (p["r"], p["r2"], m))
            for m in 알림:
                self._경고("범위에넣기", 현재sid, 자리, "%s:%s — %s" % (p["r"], p["r2"], m))
            if 틈:
                # 범위 안의 빈 줄 — INDEX 는 자리가 밀리고 COUNTBLANK 는 수가 는다. 합계 범위만, 「틈허용」을 단 빈 줄일 때만 경고로 둔다
                fn = 감싼() if 감싼 else None
                글 = "%s:%s — 범위 안에 빈 줄이 %d줄 생겼다(배치의 「빈줄」 또는 행 번호 못 박기)" % (p["r"], p["r2"], 틈)
                if 의존:
                    self._오류("범위 안의 빈 줄 (위치로 읽는 범위)", 현재sid, 자리, 글)
                elif fn not in 합계함수:
                    self._오류("범위 안의 빈 줄", 현재sid, 자리, 글 + " — %s 빈 칸에 값이 달라질 수 있다" % (
                        (fn + " 는") if fn else "함수 밖에서 읽는 범위는"))
                elif 막힌틈:
                    self._오류("범위 안의 빈 줄", 현재sid, 자리, 글 + " — %s 라 값은 그대로지만, 일부러 띄웠으면 그 빈 줄에 「틈허용」을 단다" % fn)
                else:
                    self._경고("범위 안의 빈 줄", 현재sid, 자리, 글 + " — %s 라 값은 그대로다(틈허용)" % fn)
            if 뺀:
                글 = "%s:%s — 범위 가운데 줄을 뺐다: %s" % (p["r"], p["r2"], ", ".join(뺀[:5]))
                (self._오류 if 의존 else self._경고)("범위 가운데 뺀 줄" + (" (위치로 읽는 범위)" if 의존 else ""), 현재sid, 자리, 글)
        if p.get("g"):
            if 놓 != 본 and p["g"] not in self.문.묶음.get(놓, {}):
                if 점검:
                    self._오류("묶음", 현재sid, 자리, "옮긴 줄(%s)을 묶음 「%s」 으로 읽는데 놓인 시트(%s)에 그 묶음이 없다" % (p["r"], p["g"], 놓))
                return 놓, n1, n2, None, None
            if 점검:
                c1, c2 = self._묶음끝(놓, p["g"], 현재sid, 자리)
                빠진 = [c for c in (self.문.묶음열(본, p["g"]) or ()) if c in self.뺀열.get(본, ())] if 놓 == 본 else []
                if 빠진 and (본, p["g"]) not in self._알린묶음:      # 묶음에서 열이 빠졌다 — 묶음마다 한 번 알린다
                    self._알린묶음.add((본, p["g"]))
                    self._경고("묶음에서 빠진 열", 현재sid, 자리,
                             "%s 의 묶음 「%s」 에서 열을 뺐다: %s — 이 묶음을 읽는 범위가 모두 그만큼 준다(COUNTBLANK·SUM 따위의 값이 달라질 수 있고, "
                             "숫자로 적어 둔 자리는 따라가지 않는다)" % (본, p["g"], ", ".join(빠진)))
            else:
                m = self.묶음새열(놓, p["g"]) or [None]
                c1, c2 = m[0], m[-1]
        else:
            _, c1 = self.옮긴열(p["r"], p["c"])
            _, c2 = self.옮긴열(p["r2"], p["c2"])
            if 점검 and 놓 != 본:
                for m in self._옮긴열범위(본, 놓, p["c"], p["c2"]):
                    self._오류("범위 깨짐", 현재sid, 자리, "%s:%s — %s" % (p["r"], p["r2"], m))
            elif 점검 and c1 == p["c"] and c2 == p["c2"]:
                문제, 뺀 = self._열범위(놓, c1, c2, 의존)
                for m in 문제:
                    self._오류("범위 깨짐", 현재sid, 자리, "%s!%s:%s — %s" % (놓, c1, c2, m))
                if 뺀:
                    글 = "%s!%s:%s — 범위 가운데 열을 뺐다: %s" % (놓, c1, c2, ", ".join(뺀[:5]))
                    (self._오류 if 의존 else self._경고)("범위 가운데 뺀 열" + (" (위치로 읽는 범위)" if 의존 else ""), 현재sid, 자리, 글)
        return 놓, n1, n2, c1, c2

    # ── 틀 → 수식 ──
    def 수식(self, 조각, 현재sid, 자리, 엄한=False, 본sid=None):
        """틀 → 새 좌표의 수식 글. 엄한=True(배치가 준 수식)면 명세에 없는 행 ID 를 오류로 올린다.

        현재sid : 이 수식이 놓이는 시트(놓인 시트).  본sid : 이 수식의 줄이 본디 있던 시트(옮긴 줄이면 현재sid 와 다르다).
        참조의 시트 머리는 가리키는 줄이 지금 놓인 시트가 수식이 놓인 시트와 다를 때 쓴다(같은 시트인데 일부러 붙인 @! 는 살린다).
        옛 xlsx 에서 뽑은 명세의 수식은 등록부 밖의 줄(옛 파일이 빈 줄을 가리키던 것)을 끝 줄에서 떨어진 만큼 밀어 준다.
        """
        글 = []
        짝볼것 = False
        참번, 구조 = -1, []
        본sid = 본sid or 현재sid

        def 감싼(i):
            """참조 i(조각 가운데 참조만 센 순번)를 바로 감싼 함수 이름. 함수 밖이면 None."""
            if not 구조:
                구조.append(호출구조(조각))
            호출, 길 = 구조[0]
            return 호출[길[i][-1][0]]["fn"] if 길.get(i) else None

        for p in 조각:
            if isinstance(p, str):
                글.append(p)
                continue
            참번 += 1
            k = p["k"]
            if k in ("c", "r", "R"):
                모름 = sorted({rid for rid in (p["r"], p.get("r2", p["r"])) if rid not in self.행소속})
                if 모름 and (엄한 or self.문.엄한행):
                    self._오류("모르는 행·열", 현재sid, 자리, "명세에 없는 행 ID 를 가리킨다: %s" % ", ".join(모름))
                    글.append("#REF!")
                    continue
                if 모름:
                    self._경고("등록부 밖의 줄", 현재sid, 자리, "명세에 없는 줄을 가리킨다(끝 줄에서 떨어진 만큼 민다): %s" % ", ".join(모름))
            if k == "x":
                self._경고("못 바꾼 참조", 현재sid, 자리, "원문 그대로 둔다: %s (%s)" % (p["t"], p["why"]))
                글.append(p["t"])
                continue
            if k == "n":
                글.append((시트이름쓰기(self.새이름[p["s"]]) + "!" if p.get("s") else "") + p["name"])
                continue
            if p.get("fn") in 못바꾸는함수:
                self._경고("못 바꾸는 함수", 현재sid, 자리, "%s 안의 참조 — 값이 배치에 따라 달라질 수 있다" % p["fn"])
            if p.get("fn") in ("INDEX", "MATCH", "LOOKUP", "XLOOKUP") or p.get("fn") in 짝범위함수:
                짝볼것 = True
            if k == "C":
                본, 놓 = p["s"], p["s"]
            else:
                본, 놓 = self.본시트(p["r"]), self.놓인시트(p["r"])
            if 놓 not in self.새이름:
                self._오류("없는 시트", 현재sid, 자리, "참조가 가리키는 시트가 배치에 없다: %s" % 놓)
                글.append("#REF!")
                continue
            머리 = 시트이름쓰기(self.새이름[놓]) + "!" if ((p.get("x") and 본 == 본sid) or 놓 != 현재sid) else ""
            의존 = 위치로읽나(p)
            # 늘어난 시간축 묶음의 열 ID 를 못 박아 읽는 참조 — 새 열을 따라가지 않는다
            if self.늘종류 and k in ("c", "r"):
                종 = self.문.열종류.get(본, {})
                for 법, cid in ((p.get("w"), p["c"]), (p.get("w2"), p.get("c2"))):
                    if 법 == "i" and (본, 종.get(cid)) in self.늘종류:
                        self.못박은.append((현재sid, 자리, p["r"], cid))
            try:
                if k == "c":
                    n = self.새행(p["r"])
                    _, g = self.칸글자(p["r"], p["c"])
                    if n is None:
                        self._오류("뺀 줄 참조", 현재sid, 자리, "뺀 줄을 가리킨다: %s" % p["r"])
                        n = "#REF!"
                    if g is None:
                        self._오류("뺀 열 참조", 현재sid, 자리, "뺀 열을 가리킨다: %s!%s" % (놓, p["c"]))
                        g = "#REF!"
                    글.append("%s%s%s%s%s" % (머리, "$" if p["a"][0] == "$" else "", g, "$" if p["a"][1] == "$" else "", n))
                elif k == "r":
                    for rid in (p["r"], p["r2"]):
                        if self.새행(rid) is None:
                            self._오류("뺀 줄 참조", 현재sid, 자리, "뺀 줄을 가리킨다: %s" % rid)
                    _, n1, n2, c1, c2 = self.범위끝(p, 현재sid, 자리, 점검=True, 감싼=lambda i=참번: 감싼(i))
                    if n1 is None:           # 등록부 밖의 줄
                        n1 = self.새행(p["r"])
                    if n2 is None:
                        n2 = self.새행(p["r2"])
                    낱 = []
                    for n, cid, a in ((n1, c1, p["a"]), (n2, c2, p["a2"])):
                        if cid is None:
                            g = "#REF!"
                        elif cid in self.열자리[놓]:
                            g = self.열자리[놓][cid]
                        elif cid in self.뺀열.get(놓, ()):
                            self._오류("뺀 열 참조", 현재sid, 자리, "뺀 열을 가리킨다: %s!%s" % (놓, cid))
                            g = "#REF!"
                        else:
                            raise KeyError("%s!%s" % (놓, cid))
                        낱.append("%s%s%s%s" % ("$" if a[0] == "$" else "", g, "$" if a[1] == "$" else "",
                                                n if n is not None else "#REF!"))
                    글.append(머리 + ":".join(낱))
                elif k == "C":
                    g1, g2 = self.새열글자(놓, p["c"]), self.새열글자(놓, p["c2"])
                    if g1 is None or g2 is None:
                        self._오류("뺀 열 참조", 현재sid, 자리, "뺀 열을 가리킨다: %s!%s:%s" % (놓, p["c"], p["c2"]))
                    문제, 뺀 = self._열범위(놓, p["c"], p["c2"], 의존)
                    for m in 문제:
                        self._오류("범위 깨짐", 현재sid, 자리, "%s!%s:%s — %s" % (놓, p["c"], p["c2"], m))
                    글.append("%s%s%s:%s%s" % (머리, "$" if p["a"] == "$" else "", g1, "$" if p["a2"] == "$" else "", g2))
                elif k == "R":
                    문제, 뺀, n1, n2, _, 틈, _ = self._행범위(p["r"], p["r2"], 의존)
                    if 틈:
                        self._경고("범위 안의 빈 줄", 현재sid, 자리, "%s:%s — 행 전체 참조 안에 빈 줄이 %d줄 생겼다" % (p["r"], p["r2"], 틈))
                    n1 = n1 if n1 is not None else self.새행(p["r"])
                    n2 = n2 if n2 is not None else self.새행(p["r2"])
                    if n1 is None or n2 is None:
                        self._오류("뺀 줄 참조", 현재sid, 자리, "뺀 줄을 가리킨다: %s:%s" % (p["r"], p["r2"]))
                    for m in 문제:
                        self._오류("범위 깨짐", 현재sid, 자리, "%s:%s — %s" % (p["r"], p["r2"], m))
                    글.append("%s%s%s:%s%s" % (머리, "$" if p["a"] == "$" else "", n1, "$" if p["a2"] == "$" else "", n2))
            except KeyError as e:
                self._오류("모르는 행·열", 현재sid, 자리, "ID 를 새 배치에서 찾지 못했다: %s" % (e.args[0] if e.args else e))
                글.append("#REF!")
        글, 붙인 = 새함수접두("".join(글))      # 2007년 표준 뒤에 나온 함수에 「_xlfn.」 — 접두 없이 적히면 엑셀에서 #NAME? 이 된다
        for 이름 in 붙인:
            if 이름 in 펼침함수:
                self.펼침.setdefault(이름, []).append((현재sid, 자리))
        if len(글) > 8192:      # 엑셀은 한 칸 수식이 8,192자를 넘으면 파일을 못 연다
            self._오류("수식 길이", 현재sid, 자리, "수식이 8,192자를 넘는다(%d자)" % len(글))
        if 남은자리표시(글):      # 안에서 쓰는 자리표시 글자가 수식에 남았다 — 엑셀이 #NAME? 으로 읽는다
            self._오류("수식 꼴", 현재sid, 자리, "낸 수식 글에 자리표시 글자가 남았다: %s" % 글[:80])
        if 짝볼것:
            self._짝후보.append((조각, 현재sid, 자리))
        return 글

    def 손수식(self, 글, sid, rid, cid):
        """배치가 준 손 수식 → 수식 글. 틀은 짝 범위 점검을 위해 적어 둔다."""
        try:
            틀 = 손수식틀(글, cid, sid, self.문)
        except 배치오류 as e:
            for o in e.오류목록:
                self._오류(o["종류"], sid, [rid, cid], o["설명"])
            return "#REF!"
        self.칸틀[(rid, cid)] = 틀
        return self.수식(틀, sid, [rid, cid], 엄한=True)

    # ── 서로 짝인 범위 ──
    def _크기(self, p):
        """범위 참조 → (옛 (줄 수, 열 수), 새 (줄 수, 열 수), 새 열 차례 — 본 시트의 열 ID 로)."""
        본 = self.본시트(p["r"])
        옛행, 옛열 = self.옛순서.get(본, {}), self.옛열순서.get(본, {})
        옛 = None

        def 푼(c):      # 자리 이름으로 적은 열 — 명세의 열 등록부에서 푼다
            자 = 자리풀기(c) if c not in 옛열 else None
            return (자리열(self.문.묶음열(본, 자[0]) or [], 자[1]) or c) if 자 else c

        pc, pc2 = 푼(p["c"]), 푼(p["c2"])
        if p["r"] in 옛행 and p["r2"] in 옛행 and pc in 옛열 and pc2 in 옛열:
            옛 = (abs(옛행[p["r"]] - 옛행[p["r2"]]) + 1, abs(옛열[pc] - 옛열[pc2]) + 1)
        try:
            놓, n1, n2, c1, c2 = self.범위끝(p)
        except KeyError:
            return 옛, None, None
        순 = self.새열순서.get(놓, [])
        if None in (n1, n2) or c1 not in 순 or c2 not in 순:
            return 옛, None, None
        i, j = sorted((순.index(c1), 순.index(c2)))
        열들 = 순[i:j + 1]
        if 놓 != 본:
            역 = self._역맞춤(놓, 본)
            열들 = [역.get(c, c) for c in 열들]
        return 옛, (abs(n1 - n2) + 1, j - i + 1), 열들

    def 짝점검(self):
        """서로 짝인 범위가 새 배치에서도 크기·열 차례가 같은지 본다.

        ① 한 함수가 자리끼리 짝지어 읽는 범위들(SUMPRODUCT·COUNTIFS·SUMIF·LOOKUP …)
        ② INDEX 의 범위 ↔ 그 위치를 낸 MATCH 의 범위. 위치 인자가 다른 칸을 가리키면 그 칸의 수식(MATCH)을 따라간다.
        명세 안에서 이미 크기가 다른 짝은 범위지문.점검 이 오류로 올린다(줄 무늬 명세).
        """
        본, 수 = set(), {"한 함수 안의 짝": 0, "INDEX↔MATCH 짝": 0}

        def 견주기(가, 나, 갈래, 현재sid, 자리, 긴쪽만=False):
            키 = (범위지문.범위이름(가), 범위지문.범위이름(나), 갈래)
            if 키 in 본:
                return
            본.add(키)
            옛가, 새가, 열가 = self._크기(가)
            옛나, 새나, 열나 = self._크기(나)
            if 옛가 is None or 옛나 is None or 새가 is None or 새나 is None:
                return
            if 긴쪽만:      # INDEX 범위와 MATCH 범위 — 한 줄(또는 한 열)짜리끼리 길이를 견준다
                if 1 not in 옛가 or 1 not in 옛나 or max(옛가) != max(옛나):
                    return
                옛가, 옛나, 새가2, 새나2 = max(옛가), max(옛나), max(새가), max(새나)
                if 1 not in 새가 or 1 not in 새나:
                    새가2, 새나2 = 새가, 새나
            else:
                if 옛가 != 옛나:
                    return
                새가2, 새나2 = 새가, 새나
            수[갈래] += 1
            if 새가2 != 새나2:
                self._오류("짝 범위", 현재sid, 자리, "서로 짝인 범위의 크기가 달라졌다(%s): %s (%s칸) ↔ %s (%s칸)" % (
                    갈래, 범위지문.범위이름(가), 새가2, 범위지문.범위이름(나), 새나2))
            elif 새가[0] == 1 and 새나[0] == 1 and 열가 != 열나:
                sa, sb = self.본시트(가["r"]), self.본시트(나["r"])
                옛가열 = [c["id"] for c in self.명세["시트"][sa]["열"]]
                옛나열 = [c["id"] for c in self.명세["시트"][sb]["열"]]
                if not all(c in 옛가열 for c in (가["c"], 가["c2"])) or not all(c in 옛나열 for c in (나["c"], 나["c2"])):
                    return                                   # 자리 이름으로 적은 범위 — 열 차례는 묶음에서 정해진다
                i, j = sorted((옛가열.index(가["c"]), 옛가열.index(가["c2"])))
                k, l = sorted((옛나열.index(나["c"]), 옛나열.index(나["c2"])))
                if 옛가열[i:j + 1] == 옛나열[k:l + 1]:      # 옛 배치에서는 같은 열들이었다
                    self._오류("짝 범위", 현재sid, 자리, "서로 짝인 범위의 열 차례가 달라졌다(%s): %s ↔ %s" % (
                        갈래, 범위지문.범위이름(가), 범위지문.범위이름(나)))

        for 틀, 현재sid, 자리 in self._짝후보:
            for 가, 나, 갈래, 긴쪽만 in 범위지문.짝찾기(틀, self.칸틀):
                견주기(가, 나, 갈래, 현재sid, 자리, 긴쪽만)
        return 수

    # ── 서식용 범위(병합·유효성·조건부 서식) ──
    def 칸집합(self, 범위들, 알림시트=None):
        """범위 목록 → {놓인 시트 ID: 새 좌표 칸 집합}. 뺀 줄·열의 칸은 버린다. 옛 배치에서 범위에 들던 칸을 하나씩 옮긴다.

        줄이 다른 시트로 옮겨졌으면 그 칸은 놓인 시트의 집합에 든다(유효성·조건부 서식이 줄을 따라간다).
        """
        집 = {}
        for g in 범위들:
            본 = self.본시트(g["r"])
            옛행 = [r["id"] for r in self.명세["시트"][본]["행"]] if 본 in self.명세["시트"] else []
            옛열 = [c["id"] for c in self.명세["시트"][본]["열"]] if 본 in self.명세["시트"] else []
            옛순, 옛열순 = self.옛순서.get(본, {}), self.옛열순서.get(본, {})
            if g["r"] in 옛순 and g["r2"] in 옛순:
                i, j = sorted((옛순[g["r"]], 옛순[g["r2"]]))
                줄들 = 옛행[i:j + 1]
            else:                                   # 배치가 끼운 줄·등록부 밖의 줄 — 새 배치의 두 끝 사이
                try:
                    n1, n2 = sorted((self.새행(g["r"]), self.새행(g["r2"])))
                    놓 = self.놓인시트(g["r"])
                    if self.놓인시트(g["r2"]) != 놓:
                        raise KeyError(g["r2"])
                except (KeyError, TypeError):
                    self._오류("서식 범위", 알림시트 or 본, [g["r"], g["c"]],
                             "서식 범위(병합·유효성·조건부 서식)의 끝 줄을 새 배치에서 찾지 못했다: %s:%s" % (g["r"], g["r2"]))
                    continue
                줄들 = [rid for n, rid in self.새순서.get(놓, ()) if n1 <= n <= n2]
            if g["c"] in 옛열순 and g["c2"] in 옛열순:
                k, l = sorted((옛열순[g["c"]], 옛열순[g["c2"]]))
                열들 = 옛열[k:l + 1]
            else:
                순 = self.새열순서.get(본, [])
                if g["c"] not in 순 or g["c2"] not in 순:
                    self._오류("서식 범위", 알림시트 or 본, [g["r"], g["c"]], "서식 범위의 끝 열을 새 배치에서 찾지 못했다: %s~%s" % (g["c"], g["c2"]))
                    continue
                k, l = sorted((순.index(g["c"]), 순.index(g["c2"])))
                열들 = 순[k:l + 1]
            for rid in 줄들:
                n = self.행자리.get(rid)      # 뺀 줄 · 배치에서 빠뜨린 줄(이미 알렸다)은 건너뛴다
                if n is None:
                    continue
                for cid in 열들:
                    try:
                        놓, 새 = self.칸글자(rid, cid)
                    except KeyError:    # 배치에서 빠뜨린 열(이미 알렸다) · 옮긴 줄의 자리 없는 열
                        continue
                    if 새 is not None:
                        집.setdefault(놓, set()).add((n, 열번호(새)))
        return 집

    @staticmethod
    def 범위글(집):
        """칸 집합 → 'A1:A5 C3' 꼴. 열마다 이어진 줄을 묶고, 이웃 열의 같은 묶음을 합친다."""
        열별 = {}
        for n, k in 집:
            열별.setdefault(k, []).append(n)
        묶음 = {}
        for k, 줄 in 열별.items():
            줄.sort()
            시작 = 앞 = 줄[0]
            for n in 줄[1:] + [None]:
                if n is not None and n == 앞 + 1:
                    앞 = n
                    continue
                묶음.setdefault((시작, 앞), []).append(k)
                if n is not None:
                    시작 = 앞 = n
        글 = []
        for (a, b), 열들 in sorted(묶음.items()):
            열들.sort()
            시작 = 앞 = 열들[0]
            for k in 열들[1:] + [None]:
                if k is not None and k == 앞 + 1:
                    앞 = k
                    continue
                한 = "%s%d" % (열글자(시작), a)
                if (시작, a) != (앞, b):
                    한 += ":%s%d" % (열글자(앞), b)
                글.append((a, 시작, 한))
                if k is not None:
                    시작 = 앞 = k
        return " ".join(t[2] for t in sorted(글))


def _값(한):
    t = 한.get("t")
    v = 한.get("v")
    if t == "dt":
        return datetime.datetime.fromisoformat(v)
    if t == "d":
        return datetime.date.fromisoformat(v)
    if t == "tm":
        return datetime.time.fromisoformat(v)
    return v


_re수식속글 = re.compile(r'"(?:[^"]|"")*"')


def _글속좌표칸(명세, 지):
    """글 칸과 수식 속 문자열 상수에 좌표처럼 보이는 말(「E28」「12번 30행」「G열」)이 든 칸 — 놓인 줄만. → [(행 ID, 열 ID)]"""
    찾음 = []
    for sid in 명세["시트"]:
        for 줄 in 명세["시트"][sid]["행"]:
            if 줄["id"] not in 지.행자리:
                continue
            for cid, 한 in 줄.get("칸", {}).items():
                if isinstance(한.get("v"), str):
                    글 = [한["v"]]
                else:
                    글 = [m for p in 한.get("f", ()) if isinstance(p, str) for m in _re수식속글.findall(p)]
                if any(글속좌표(x) for x in 글):
                    찾음.append((줄["id"], cid))
    return 찾음


def _가정묶음(명):
    """세 시나리오 줄을 가진 가정 머리 줄: [[머리 번호, [비관 번호, 기준 번호, 낙관 번호]], …] (범위지문.가정묶음 을 번호로)"""
    묶음 = []
    for 머리, 세 in 범위지문.가정묶음(명):
        번호 = [행ID풀기(x)[1] for x in [머리] + list(세)]
        if None not in 번호:
            묶음.append([번호[0], 번호[1:]])
    return 묶음


def _단위표(명, 문):
    """줄의 단위: {"번호": 단위 글}. 단위 칸이 「설정」 줄의 단위 라벨 칸(금액 단위 · 주당 단위)을 읽는 수식이면 「금액」."""
    단위열 = next((c["id"] for c in 명["열"] if c.get("종류") == "단위"), None)
    표 = OrderedDict()
    for r in 명["행"]:
        번 = 행ID풀기(r["id"])[1]
        한 = r.get("칸", {}).get(단위열) if 단위열 else None
        if 번 is None or not 한:
            continue
        if "f" in 한:
            참 = [p for p in 한["f"] if isinstance(p, dict)]
            표["%d" % 번] = "금액" if any(p["k"] == "c" and 문.행쓰임.get(p["r"]) == "설정" for p in 참) else "(수식)"
        elif 한.get("v") is not None:
            표["%d" % 번] = ("%s" % 한["v"]).strip()
    return 표


# ───────────────────────── 표준 서식 길의 도우미 ─────────────────────────
_표밖열 = ("보조", "방향점검", "역산")       # 표의 끝 열을 정할 때 빼는 열 종류(점검 보조 열 — 접어 두고 인쇄 영역에서 뺀다)
_선택없는줄 = ("제목", "구획머리", "머리", "머리보조", "부제", "글", "빈줄", None)      # 이런 줄의 칸은 목록 유효성 범위에 들어 있어도 선택 칸이 아니다
_값열종류 = ("실적", "예측", "영구", "값")
_re틀칸 = re.compile(r"([A-Z]+)([0-9]+)")


def _표끝열(지, 문, sid, 값만=False):
    """그 시트의 표가 끝나는 열 번호. 값만=True 면 마지막 값 열(시간축의 끝 · 한 값 열), 아니면 점검 보조 열을 뺀 마지막 열."""
    종 = 문.열종류[sid]
    순 = 지.새열순서[sid]
    if 값만:
        안 = [c for c in 순 if 종.get(c) in _값열종류]
    else:
        안 = [c for c in 순 if 종.get(c) not in _표밖열 and 종.get(c) != "여백"]
    return 열번호(지.열자리[sid][안[-1]]) if 안 else None


def _줄찾기(명세, sid, rid):
    표 = 명세.setdefault("_줄표", {})
    if sid not in 표:
        표[sid] = {r["id"]: r for r in 명세["시트"][sid]["행"]} if sid in 명세["시트"] else {}
    return 표[sid].get(rid)


def _머리글(지, 명세, sid):
    """열 ID → 그 열의 머리 글(이 시트에 놓인 머리 줄에서 처음 나오는 글). 글 열의 표준 폭을 가리는 데 쓴다."""
    글 = {}
    for _, rid in 지.새순서[sid]:
        줄 = 지.새줄.get(rid)
        if 줄 is not None:
            if 줄.get("종류") == "머리":
                for 키, v in (줄.get("글") or {}).items():
                    if isinstance(v, str):
                        글.setdefault(키, v)
            continue
        본 = 지.본시트(rid)
        줄 = _줄찾기(명세, 본, rid)
        if not 줄 or 줄.get("종류") != "머리":
            continue
        맞 = 지.열맞춤.get(sid, {}).get(본, {}) if 본 != sid else {}
        for cid, 한 in (줄.get("칸") or {}).items():
            if isinstance(한.get("v"), str):
                글.setdefault(맞.get(cid, cid), 한["v"])
    return 글


def _선택칸(지, 명세, 배치):
    """목록 유효성이 걸린 칸 — {놓인 시트 ID: {(행 번호, 열 번호)}}. 명세의 유효성과 배치의 유효성을 함께 본다.

    칸 종류(선택)를 정하려고 줄을 놓기 전에 한 번 훑는다. 여기서 난 오류 · 경고는 버린다(유효성을 세울 때 다시 알린다)."""
    오, 경 = len(지.오류), len(지.경고)
    집 = {}
    for 본, 명 in 명세["시트"].items():
        for v in 명.get("유효성", []):
            if v.get("type") != "list":
                continue
            for 놓, 칸들 in 지.칸집합(v["범위"]).items():
                집.setdefault(놓, set()).update(칸들)
    for b in 배치["시트"]:
        if not isinstance(b, dict) or b.get("id") not in 명세["시트"]:
            continue
        for v in b.get("유효성") or ():
            try:
                범위 = [줄무늬.범위읽기(g, 지.문, 엄한=True) for g in v["범위"]]
                for 놓, 칸들 in 지.칸집합(범위, 알림시트=b["id"]).items():
                    집.setdefault(놓, set()).update(칸들)
            except (배치오류, KeyError, TypeError):
                continue
    del 지.오류[오:], 지.경고[경:]
    return 집


def _표준인쇄(지, 문, 훅, sid, 인b, 틀):
    """표준 서식 길의 인쇄 설정 — 배치의 「인쇄」가 안 준 것을 시트 사양으로 채운다.

    방향 · 용지 · 폭 1쪽 맞춤(높이는 자동) · 가로 가운데 · 여백 · 바닥글(가운데 시트 이름 · 오른쪽 쪽 번호) ·
    제목 행(틀 고정 위의 줄) · 인쇄 영역(첫 칸 ~ 사양의 끝 열 × 마지막 줄).
    제목 열(틀 고정 왼쪽의 열)은 폭을 1쪽에 맞추지 않는 시트에만 준다 — 폭 1쪽 맞춤이면 가로로 쪽이 안 나뉘어 쓸 일이 없고,
    엑셀이 맞춤 배율을 셈할 때 제목 열의 폭을 한 번 더 넣는다(L1 묶기에서 잰 것: 인쇄 영역의 폭으로는 94% 인 2번 시트가 70% 로 찍혔다)."""
    사 = 훅.사양(sid)
    표 = 훅.표준
    새 = {"방향": 사.get("방향"), "용지": 사.get("용지"), "폭맞춤": 1, "높이맞춤": 0, "가로가운데": True,
         "여백": dict(표.인쇄여백), "바닥글": dict(표.바닥글)}
    새.update(인b)
    if isinstance(인b.get("바닥글"), dict):
        새["바닥글"] = dict(표.바닥글, **인b["바닥글"])
    순서 = 지.새순서[sid]
    행id = {n: rid for n, rid in 순서}
    열id = {열번호(g): c for c, g in 지.열자리[sid].items()}
    m = _re틀칸.fullmatch(틀 or "")
    if m and "제목행" not in 인b and int(m.group(2)) > 1 and 순서:
        위 = [n for n in 행id if n < int(m.group(2))]
        if 위:
            새["제목행"] = [행id[min(위)], 행id[max(위)]]
    if m and "제목열" not in 인b and 열번호(m.group(1)) > 1 and 새.get("폭맞춤") != 1:
        왼 = [k for k in 열id if k < 열번호(m.group(1))]
        if 왼:
            새["제목열"] = [열id[min(왼)], 열id[max(왼)]]
    if "영역" not in 인b and 순서:
        끝 = _표끝열(지, 문, sid, 값만=사.get("인쇄끝") == "값") or _표끝열(지, 문, sid)
        if 끝:
            새["영역"] = {"끝열": 열id[끝]}
    return 새


def 짓기(명세, 배치, 낼곳, 지도곳=None, 엄격=True, 서식길=None, 지문남기기=True,
       이름불일치허용=False, 합계범위승인=False, 못박은열허용=False):
    """xlsx 를 짓고 좌표 지도를 돌려준다. 오류가 있으면 배치오류를 던진다(엄격).

    서식길 : "옛"   = 옛 서식을 있는 그대로 옮긴다(명세의 칸별 서식 번호 · 통합문서의 기본 글꼴) — 시험용
             "표준" = 칸 종류 → 명명 스타일 + 시트 공통 서식(서식훅.py · 서식표준.py) — 납품의 기본
             "없음" = 서식 없이
             안 주면 배치의 「서식길」, 배치에도 없으면 "옛" 이다(납품 배치는 "표준" 을 적어 둔다).
    이름불일치허용 : 수식에 덧붙인 이름이 지금 줄 이름과 달라도 경고만 하고 짓는다(기본은 멈춘다)
    합계범위승인   : 범위 지문과 다른 합계 범위를 승인한 것으로 보고 경고만 한다(위치로 읽는 범위는 늘 오류)
    못박은열허용   : 시간축 묶음에 열을 더할 때 그 묶음의 열 ID 를 못 박은 참조가 남아 있어도 경고만 한다(시연용)
    """
    if 서식길 is None:
        서식길 = (배치.get("서식길") if isinstance(배치, dict) else None) or "옛"
    if 서식길 not in 서식길들:
        raise 배치오류([{"종류": "배치", "시트": None, "자리": None,
                     "설명": "서식길 「%s」 을 모른다(%s)" % (서식길, " · ".join(서식길들))}])
    if isinstance(명세, str):
        명세 = 명세읽기(명세)
    지 = _지은이(명세, 배치)
    문 = 지.문
    책 = 명세["책"]
    if 책.get("줄무늬"):      # 명세를 손으로 고친 것에 대한 점검 — 범위의 구성이 지문과 같은가
        볼명세 = 명세
        if 명세.get("기간"):      # 회차의 기간으로 편 명세 — 지문은 틀(열 등록부 그대로)의 것이다. 틀로 한 번 더 읽어 견준다
            볼명세 = 줄무늬.읽기(명세["폴더"], 옛서식=False, 덧파일=명세.get("덧파일") or ())
        오, 경 = 범위지문.점검(볼명세, 합계승인=합계범위승인)
        지.오류 += 오
        지.경고 += 경
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    if 명세.get("테마"):
        wb.loaded_theme = 명세["테마"]
    if 서식길 == "옛" and not 책.get("서식조합"):
        서식길 = "없음"
    if 서식길 == "옛" and 책.get("기본글꼴"):
        # 통합문서의 기본 글꼴 — 서식 없는 칸(값만 있는 칸)이 옛 파일과 같은 글꼴로 보이게 한다
        기본 = Font.from_tree(fromstring(책["기본글꼴"]))
        wb._fonts = IndexedList([기본])
        wb._named_styles["Normal"].font = 기본
        wb._named_styles["Normal"].bind(wb)
    훅 = None
    if 서식길 != "없음":
        # "표준" 은 모든 시트에, "옛" 은 옛 서식이 없는 시트(명세로 새로 지은 14·15번 따위)에만 명명 스타일을 입힌다
        훅 = 서식훅.훅()
        훅.책준비(wb, 기본글꼴=(서식길 == "표준"))
        if not 훅.쓸수있나 and 서식길 == "표준":
            지._경고("서식", None, None, "서식표준.py 를 찾지 못해 명명 스타일을 입히지 못했다(칸 종류만 가렸다)")
    표준길 = 서식길 == "표준"
    선택칸 = _선택칸(지, 명세, 배치) if 표준길 else {}      # 놓인 시트 ID → {(행, 열 번호)} — 목록 유효성이 걸린 칸
    판정칸, 푼병합, 직접서식 = {}, [], []

    # 옛 서식 — 조합마다 한 번만 만들고, 같은 조합의 칸은 내부 서식 번호를 베낀다
    표 = 책.get("서식표")
    서식기억 = {}

    def 서식입히기(칸, 번호):
        if 번호 in 서식기억:
            칸._style = copy(서식기억[번호])
            return
        f, p, b, a, pr, nf, qp = 책["서식조합"][번호]
        o = 서식객체({"글꼴": 표["글꼴"][f], "채움": 표["채움"][p], "테두리": 표["테두리"][b],
                    "맞춤": 표["맞춤"][a], "보호": 표["보호"][pr], "숫자서식": 표["숫자서식"][nf]})
        칸.font, 칸.fill, 칸.border = o["font"], o["fill"], o["border"]
        칸.alignment, 칸.protection, 칸.number_format = o["alignment"], o["protection"], o["number_format"]
        if qp:
            칸.quotePrefix = True
        서식기억[번호] = copy(칸._style)

    # 시트를 먼저 다 만든다(줄이 다른 시트로 옮겨 갈 수 있으므로 병합·유효성은 뒤에 한꺼번에 세운다)
    시트ws, 지은시트 = {}, []
    for b in 배치["시트"]:
        sid = b["id"]
        if sid in 시트ws:               # 같은 시트가 두 번 적힌 배치 — 오류로 이미 올렸다
            continue
        이름 = 지.새이름.get(sid) or b.get("이름") or sid
        if 탭이름문제(이름) or 이름.lower() in {x.title.lower() for x in 시트ws.values()}:
            ws = wb.create_sheet("_%d" % (len(시트ws) + 1))     # 못 쓰는·겹친 탭 이름 — 오류로 이미 올렸다. 나머지 오류를 마저 모으려고 임시 이름으로 짓는다
        else:
            ws = wb.create_sheet(이름)
            if ws.title != 이름:
                지._오류("탭 이름", sid, None, "지은 시트의 이름이 배치와 다르다: %s → %s" % (이름, ws.title))
        시트ws[sid] = ws
        if sid in 명세["시트"]:
            지은시트.append((sid, b))

    옛줄all = {r["id"]: r for s in 명세["시트"].values() for r in s["행"]}
    배치시트 = {b["id"]: b for b in 배치["시트"] if isinstance(b, dict) and b.get("id")}

    def 줄종류of(rid):
        """그 줄의 종류 — 놓인 시트의 「줄서식」이 덮은 것이 앞선다."""
        꾸 = ((배치시트.get(지.놓인.get(rid)) or {}).get("줄서식") or {}).get(rid)
        return (꾸.get("종류") if isinstance(꾸, dict) else None) or (지.새줄.get(rid) or 옛줄all.get(rid) or {}).get("종류")
    뺀유효성 = []
    if 표준길:      # 선택 칸은 값이 놓이는 줄에만 — 제목 · 구획머리 · 머리 · 글 · 빈 줄에 걸친 유효성 범위(옛 파일의 범위 밀림)는 뺀다
        for 놓, 집 in 선택칸.items():
            줄of = dict(지.새순서.get(놓, ()))
            뺄 = {자 for 자 in 집 if 줄종류of(줄of.get(자[0])) in _선택없는줄}
            뺀유효성 += ["%s!%s%d" % (지.새이름.get(놓, 놓), 열글자(k), n) for n, k in sorted(뺄)]
            집 -= 뺄
    옮긴줄수 = 0
    지도칸 = {}
    병합된 = {}      # 시트 ID → [(첫 행, 첫 열 번호, 끝 행, 끝 열 번호, 글)] — 겹친 병합이 든 파일은 엑셀이 못 연다

    def 병합하기(sid, k1, n1, k2, n2, 자리):
        a, b = 열번호(k1), 열번호(k2)
        글 = "%s%d:%s%d" % (k1, n1, k2, n2)
        for r1, c1, r2, c2, 옛글 in 병합된.setdefault(sid, []):
            if n1 <= r2 and r1 <= n2 and a <= c2 and c1 <= b:
                지._오류("병합", sid, 자리, "병합이 서로 겹친다: %s ↔ %s (엑셀이 파일을 열지 못한다)" % (옛글, 글))
                return
        병합된[sid].append((n1, a, n2, b, 글))
        시트ws[sid].merge_cells(글)
    for sid, b in 지은시트:
        명 = 명세["시트"][sid]
        ws = 시트ws[sid]
        속 = 명.get("속성", {})
        if 표준길 and 훅.쓸수있나:      # 눈금선 · 확대 · 탭 색은 시트 사양(서식표준)이 정한다. 배치의 「보기」가 덮는다
            훅.보기(ws, sid, b.get("보기"))
        else:
            if 속.get("탭색"):
                ws.sheet_properties.tabColor = 속["탭색"]
            if 속.get("눈금선") is not None:
                ws.sheet_view.showGridLines = 속.get("눈금선")
            if 속.get("확대"):
                ws.sheet_view.zoomScale = 속["확대"]
            if 속.get("기본행높이"):
                ws.sheet_format.defaultRowHeight = 속["기본행높이"]
            if 속.get("기본열폭"):
                ws.sheet_format.defaultColWidth = 속["기본열폭"]
            if 속.get("기본글자폭"):
                ws.sheet_format.baseColWidth = 속["기본글자폭"]
        if 속.get("상태") and 속["상태"] != "visible":
            ws.sheet_state = 속["상태"]
        종 = 문.열종류[sid]
        순 = 지.새열순서[sid]
        이름열 = b.get("이름열") or next((c for c in 순 if 종.get(c) == "이름"), None)
        새이름표 = b.get("새이름", {})
        줄서식 = b.get("줄서식", {})
        숨길 = set(b.get("숨길줄", []))
        숨길열 = set(b.get("숨길열", []))
        덧칸 = b.get("덧칸", {})     # {행 ID: {열 ID: 칸}} — 옛 줄의 빈 칸·새 열에 값을 더한다
        옛이름 = 명.get("옛이름")
        옛열 = {c["id"]: c for c in 명["열"]}
        시트훅 = 훅 if (서식길 == "표준" or not 옛이름) else None
        표준시트 = 표준길 and 훅.쓸수있나
        for rid, 꾸밈 in 줄서식.items():
            for 키 in (꾸밈 if isinstance(꾸밈, dict) else ()):
                if 키 not in _줄서식열쇠:
                    지._오류("배치", sid, [rid, None], "모르는 열쇠: 「줄서식」 %s 의 「%s」" % (rid, 키))
                elif 표준시트 and 키 in _직접서식열쇠:
                    직접서식.append("%s 의 %s" % (rid, 키))
        # 틀 고정 줄 — 그 위가 머리 구역이다(표준 서식 길이 머리 구역의 글 줄을 부제로 입힌다)
        틀줄 = (b.get("틀고정") or 속.get("틀고정") or {}).get("행")
        머리끝 = 지.행자리.get(틀줄, 0) if 지.놓인.get(틀줄) == sid else 0
        열폭표 = b.get("열폭") or {}
        for cid in 열폭표:
            if cid not in 지.열자리[sid]:
                지._오류("배치", sid, None, "「열폭」에 이 시트에 놓이지 않은 열 ID: %s" % cid)
        머리글 = _머리글(지, 명세, sid) if 표준시트 else {}

        # 열 폭 · 숨김
        for cid in 순:
            새 = 지.열자리[sid][cid]
            항 = 지.새열[sid].get(cid)
            d = 옛열.get(cid, {}) if 항 is None else {"width": 항.get("폭"), "hidden": 항.get("숨김")}
            if 표준시트:      # 표준 폭 — 배치의 「열폭」 > 배치가 더한 새 열 · 새 시트 명세가 적은 폭 > 표준(열 종류 · 글 열의 머리 글)
                d = dict(d, width=열폭표.get(cid) or ((d.get("width") if (항 is not None or not 옛이름) else None)
                                                    or 훅.열폭(sid, 종.get(cid), 머리글.get(cid))))
            if d.get("width"):
                ws.column_dimensions[새].width = d["width"]
            if d.get("hidden") or cid in 숨길열:
                ws.column_dimensions[새].hidden = True
            if d.get("outlineLevel"):
                ws.column_dimensions[새].outlineLevel = d["outlineLevel"]

        # 배치가 더한 새 열 가운데 종류가 묶음에 드는 열 — 줄 무늬(묶음으로 적은 무늬)가 그 열까지 는다
        늘열 = {cid for cid, 항 in 지.새열[sid].items()
              if any(항.get("종류") in 종류들 for 종류들 in 문.묶음.get(sid, {}).values())}

        # 줄 — 이 시트에 놓인 줄(다른 시트에서 옮겨 온 줄 포함)
        for n, rid in 지.새순서[sid]:
            새줄 = rid in 지.새줄
            줄 = 지.새줄[rid] if 새줄 else 옛줄all[rid]
            본 = 지.본시트(rid)
            옮긴 = 본 != sid
            본열 = {}                    # 놓인 시트의 열 ID → 본 시트의 열 ID(옮긴 줄만)
            높이 = 줄.get("높이") or (None if (새줄 or 표준시트) else 줄.get("height"))
            꾸밈 = 줄서식.get(rid, {})
            if not isinstance(꾸밈, dict):
                지._오류("배치", sid, [rid, None], "「줄서식」의 %s 는 { } 로 적는다" % rid)
                꾸밈 = {}
            # 줄의 서식 속성 — 배치의 「줄서식」이 명세의 종류 · 서식 · 선 · 들여 · 굵게를 덮는다(명세는 안 고친다)
            줄속 = dict(줄)
            for 키 in ("종류", "서식", "선", "들여", "굵게"):
                if 키 in 꾸밈:
                    줄속[키] = 꾸밈[키]
            if 꾸밈.get("종류") is not None and 꾸밈["종류"] not in 줄무늬.줄종류들 + 서식훅.덧줄종류:
                지._오류("배치", sid, [rid, None], "「줄서식」 %s 의 종류 「%s」 를 모른다" % (rid, 꾸밈["종류"]))
            if 꾸밈.get("서식") is not None and 꾸밈["서식"] not in 줄무늬.서식이름들():
                지._오류("배치", sid, [rid, None], "「줄서식」 %s 의 서식 「%s」 를 모른다" % (rid, 꾸밈["서식"]))
            if 꾸밈.get("높이"):
                높이 = 꾸밈["높이"]
            if not 높이 and 표준시트:
                높이 = 훅.줄높이(줄속.get("종류"))
            if 높이:
                ws.row_dimensions[n].height = 높이
            if (줄.get("hidden") and not 표준시트) or 줄.get("숨김") or rid in 숨길:
                ws.row_dimensions[n].hidden = True
            if 줄.get("outlineLevel") and not 표준시트:
                ws.row_dimensions[n].outlineLevel = 줄["outlineLevel"]
            입력칸 = set(줄.get("입력") or ()) if not 새줄 else set()
            try:
                if 새줄:
                    낸 = dict(줄, id=rid)
                    칸들 = 줄무늬.줄펴기(sid, 낸, 문, 순) if any(k in 줄 for k in ("무늬", "글", "값", "이름", "단위", "덧")) else OrderedDict()
                    for cid, 한 in (줄.get("칸") or {}).items():
                        if isinstance(한, dict) and not 줄무늬.덧문제(한, 줄무늬.칸열쇠):      # 틀린 칸은 배치 읽기에서 이미 알렸다
                            칸들[cid] = dict(한)
                    입력칸 = {c for 키 in 줄.get("입력", []) for c in 줄무늬.구간풀기(문, sid, rid, 키, 순)}
                else:
                    칸들 = OrderedDict(줄.get("칸", {}))
                    if 늘열 and 줄.get("무늬원") and not 옮긴:
                        지.못박은열쇠찾기(sid, rid, 줄["무늬원"])
                        for cid, 한 in list(칸들.items()):      # 「예측.끝」처럼 묶음의 첫·끝 열로 적은 칸 — 새 배치의 그 열로 옮겨 간다
                            if 한.get("열쇠") and cid not in 줄무늬.구간풀기(문, sid, rid, 한["열쇠"], 순):
                                del 칸들[cid]
                        for cid, 한 in 줄무늬.줄펴기(sid, 줄["무늬원"], 문, 순, 열만=늘열).items():
                            if cid not in 칸들:
                                왼 = next((칸들[c] for c in reversed(순[:순.index(cid)])
                                          if c in 칸들 and 종.get(c) == 종.get(cid)), {})
                                if "s" in 왼:
                                    한["s"] = 왼["s"]
                                칸들[cid] = 한
            except 배치오류 as e:
                for o in e.오류목록:
                    지._오류(o["종류"], sid, [rid, None], o["설명"])
                continue
            if 옮긴:      # 다른 시트에서 옮겨 온 줄 — 칸을 「열맞춤」으로 이 시트의 열에 놓는다
                옮긴줄수 += 1
                맞 = 지.열맞춤.get(sid, {}).get(본, {})
                새칸 = OrderedDict()
                for c, 한 in 칸들.items():
                    c2 = 맞.get(c, c)
                    if c2 not in 지.열자리[sid]:
                        if any(k in 한 for k in ("f", "v", "메모", "링크")):
                            지._오류("옮긴 줄", sid, [rid, c], "%s 에서 옮겨 온 줄 %s 의 열 %s 가 이 시트에 자리가 없다 — 배치의 「열맞춤」에 적는다(값이 있는 칸이다)"
                                   % (본, rid, c))
                        continue
                    if c2 in 새칸:
                        지._오류("옮긴 줄", sid, [rid, c], "옮겨 온 줄 %s 의 두 열이 이 시트의 같은 열(%s)에 놓인다" % (rid, c2))
                        continue
                    새칸[c2] = 한
                    본열[c2] = c
                칸들 = 새칸
                입력칸 = {맞.get(c, c) for c in 입력칸}
            for cid, 한 in 덧칸.get(rid, {}).items():
                if cid in 칸들 and ("f" in 칸들[cid] or "v" in 칸들[cid]):
                    지._오류("배치", sid, [rid, cid], "덧칸이 이미 값이 있는 칸을 덮으려 한다")
                칸들[cid] = dict(칸들.get(cid, {}), **한)
            줄종류 = 줄속.get("종류")
            칸꼴 = {}
            for 키, 꼴 in dict(줄.get("칸꼴") or {}, **(꾸밈.get("칸꼴") or {})).items():
                if 꼴 not in 서식훅.칸종류들:
                    지._오류("배치", sid, [rid, 키], "「칸꼴」의 칸 종류 「%s」 를 모른다(%s)" % (꼴, " · ".join(서식훅.칸종류들)))
                    continue
                try:
                    for cid in 줄무늬.구간풀기(문, sid, rid, 키, 순):
                        칸꼴[cid] = 꼴
                except 배치오류 as e:
                    for o in e.오류목록:
                        지._오류(o["종류"], sid, [rid, 키], o["설명"])
            if 시트훅 is not None:           # 빈 입력 칸에도 입력 서식을 입힌다
                for cid in 입력칸 | set(칸꼴):
                    if cid in 지.열자리[sid]:
                        칸들.setdefault(cid, {})
            본명 = 명세["시트"].get(본, 명) if not 새줄 else 명
            본옛이름 = 본명.get("옛이름")
            본옛열 = {c["id"]: c for c in 본명["열"]} if 옮긴 else 옛열
            for cid, 한 in 칸들.items():
                if cid not in 지.열자리[sid]:
                    if cid not in 지.뺀열[sid]:
                        지._오류("모르는 행·열", sid, [rid, cid], "칸의 열 ID 를 새 배치에서 찾지 못했다: %s" % cid)
                    continue
                새열 = 지.열자리[sid][cid]
                자리 = [rid, cid]
                if 한.get("병합속"):
                    continue  # 병합 안쪽 칸의 테두리는 병합할 때 머리 칸에서 다시 세운다
                칸 = ws[새열 + str(n)]
                틀 = None
                if "손수식" in 한:
                    칸.value = 지.손수식(한["손수식"], sid, rid, cid)
                    틀 = 지.칸틀.get((rid, cid))
                elif "f" in 한:
                    틀 = 한["f"]
                    if 새줄 or cid in 늘열:
                        지.칸틀[(rid, cid)] = 틀
                    글 = 지.수식(틀, sid, 자리, 엄한=새줄, 본sid=본)
                    if "배열" in 한:
                        칸.value = ArrayFormula(지.수식(한["배열"], sid, 자리, 본sid=본)[1:], 글)
                    else:
                        칸.value = 글
                elif "v" in 한:
                    v = _값(한)
                    if cid == 이름열 and rid in 새이름표:
                        v = 새이름표[rid]
                    if isinstance(v, str) and v.startswith("=") and 한.get("t") != "s":
                        # 그대로 넣으면 문법을 거치지 않은 수식이 된다
                        지._오류("「=」 글", sid, 자리, '「=」로 시작하는 글이다: %s — 글이면 {"v": …, "t": "s"}, 수식이면 「손수식」·「무늬」로 적는다' % v[:40])
                        continue
                    칸.value = v
                    if 한.get("t") == "s":
                        칸.data_type = "s"      # 「=」로 시작하는 글 — 수식으로 읽히지 않게
                    elif 한.get("t") == "e":
                        칸.data_type = "e"
                if 서식길 == "옛" and "s" in 한:
                    서식입히기(칸, 한["s"])
                elif 시트훅 is not None:
                    별칭 = 문.별칭쓰기(본, rid, 본열.get(cid, cid)) if 옮긴 else 문.별칭쓰기(sid, rid, cid)
                    자리수 = (n, 열번호(새열))
                    # 수식이 다른 시트를 읽는가 — 틀의 참조가 가리키는 줄이 지금 놓인 시트로 판정한다
                    다른 = 서식훅.다른시트읽나(틀, sid, 지.놓인시트) if 틀 is not None else False
                    꼴 = 칸꼴.get(cid) or 훅.칸종류(줄종류, 종.get(cid), 한, cid in 입력칸, 틀, sid, 별칭, 다른시트=다른,
                                               선택=자리수 in 선택칸.get(sid, ()), 서식이름=줄속.get("서식"),
                                               머리구역=n < 머리끝)
                    훅.입히기(칸, 꼴, (줄.get("칸서식") or {}).get(본열.get(cid, cid)) or 서식훅.열서식.get(종.get(cid)) or 줄속.get("서식"))
                    훅.줄덧(칸, 종.get(cid), 줄속)
                    if 꼴 == "판정":
                        판정칸.setdefault(sid, set()).add(자리수)
                if 꾸밈:
                    _꾸미기(칸, 꾸밈, 직접=not 표준시트)
                if 한.get("메모"):
                    칸.comment = Comment(한["메모"]["글"], 한["메모"].get("쓴이") or "")
                if 한.get("링크"):
                    칸.hyperlink = 한["링크"].get("target") or ("#" + (한["링크"].get("location") or ""))
                    지._경고("링크", sid, 자리, "링크의 대상 주소는 옮기지 않는다")
                본cid = 본열.get(cid, cid)
                if not 새줄 and 본옛이름 and 본옛열.get(본cid, {}).get("옛") and 본cid in 줄.get("칸", {}) and "옛행" in 줄:
                    지도칸["%s!%s%d" % (본옛이름, 본옛열[본cid]["옛"], 줄["옛행"])] = "%s!%s%d" % (지.새이름[sid], 새열, n)
            선 = 줄속.get("선") or (줄종류 if 줄종류 in ("소계", "합계") else None)      # 줄의 「선」이 줄 종류보다 앞선다
            if 시트훅 is not None and 훅.쓸수있나 and 선 in ("소계", "합계"):
                # 줄선은 이름 열부터 마지막 값 열까지 — 근거 · 비고 같은 글 열에는 긋지 않는다
                자료 = [열번호(지.열자리[sid][c]) for c in 칸들 if c in 지.열자리[sid] and
                      (not 표준시트 or 종.get(c) not in 서식훅._글열)]
                if 자료:
                    if 표준시트:      # 줄선이 지나가는 빈 칸도 계산 칸으로 입힌다(스타일 없는 칸에 선만 남지 않게)
                        훅.띠(ws, n, min(자료), max(자료), "계산")
                    훅.줄선(ws, n, min(자료), max(자료), 선)
            if 표준시트 and 줄종류 in ("구획머리", "머리", "소구획"):
                # 띠 — 구획머리 · 소구획은 이름 열부터 표의 끝 열까지, 머리 줄은 글이 있는 마지막 열까지(병합 대신 같은 스타일)
                채운 = [열번호(지.열자리[sid][c]) for c, 한 in 칸들.items() if c in 지.열자리[sid] and 종.get(c) != "여백"
                      and ("v" in 한 or "f" in 한 or "손수식" in 한)]
                첫 = next((열번호(지.열자리[sid][c]) for c in 순 if 종.get(c) != "여백"), None)
                끝 = _표끝열(지, 문, sid) if 줄종류 in ("구획머리", "소구획") else (max(채운) if 채운 else None)
                if 첫 and 끝 and 끝 >= 첫:
                    훅.띠(ws, n, 첫, 끝, 줄종류)
            if rid in 새이름표 and "f" in 칸들.get(이름열, {}):
                지._경고("새 이름", sid, [rid, 이름열], "이름 칸이 수식이라 새 이름을 쓰지 않았다")
            elif rid in 새이름표 and "v" not in 칸들.get(이름열, {}):
                지._오류("배치", sid, [rid, 이름열], "이름 칸이 빈 줄에 「새이름」을 줬다 — 쓰이지 않는다(빈 칸에 글을 넣으려면 「덧칸」)")
            # 새 줄 안의 병합
            for 키 in (줄.get("병합") or []) if 새줄 else []:
                if 표준시트 and 줄종류 != "제목":      # 병합은 제목 줄에만
                    푼병합.append("%s(%s)" % (rid, 키))
                    continue
                try:
                    열들 = 줄무늬.구간풀기(문, sid, rid, 키, 순)
                    병합하기(sid, 지.열자리[sid][열들[0]], n, 지.열자리[sid][열들[-1]], n, [rid, None])
                except 배치오류 as e:
                    for o in e.오류목록:
                        지._오류(o["종류"], sid, [rid, None], o["설명"])

    # 병합 — 양 끝 ID 로 다시 세운다(서식 범위라 가운데 줄이 달라져도 막지 않고 알리기만 한다). 줄이 옮겨 갔으면 놓인 시트에 세운다
    풀린병합 = []      # 다른 시트로 옮긴 줄의 병합 가운데 놓인 시트에서 설 수 없어 버린 것: (놓인 시트, 행 ID, 열 구간)
    for 본, 명 in 명세["시트"].items():
        for g in 명.get("병합", []):
            놓1, 놓2 = 지.놓인.get(g["r"]), 지.놓인.get(g["r2"])
            if 놓1 is None and 놓2 is None:
                continue                          # 통째로 뺀 줄의 병합은 말없이 버린다
            if 표준길 and 훅.쓸수있나 and not (g["r"] == g["r2"] and 줄종류of(g["r"]) == "제목"):
                푼병합.append("%s(%s)" % (g["r"], g.get("키") or "%s~%s" % (g["c"], g["c2"])))
                continue                          # 표준 서식 길 — 병합은 제목 줄에만 남긴다
            if 놓1 != 놓2 or 놓1 not in 시트ws:
                지._경고("병합", 본, [g["r"], g["c"]], "병합의 한쪽 끝만 빠졌거나 두 끝이 다른 시트에 놓였다 — 병합을 버렸다")
                continue
            ws = 시트ws[놓1]
            n1, n2 = 지.행자리[g["r"]], 지.행자리[g["r2"]]
            try:
                if "키" in g and 놓1 == 본:      # 줄 안의 병합을 열 구간으로 적은 것 — 새 배치의 열 순서로 다시 편다
                    열들 = 줄무늬.구간풀기(문, 본, g["r"], g["키"], 지.새열순서[본]) if not (지.뺀열[본] & {g["c"], g["c2"]}) else []
                    k1, k2 = (지.열자리[본][열들[0]], 지.열자리[본][열들[-1]]) if 열들 else (None, None)
                elif "키" in g:                   # 옮긴 줄의 병합 — 본 시트의 열들 가운데 놓인 시트에 자리가 있는 것만(붙어 있어야 한다)
                    맞 = 지.열맞춤.get(놓1, {}).get(본, {})
                    열들 = [맞.get(c, c) for c in 줄무늬.구간풀기(문, 본, g["r"], g["키"])]
                    열들 = [c for c in 열들 if c in 지.열자리[놓1]]
                    순 = 지.새열순서[놓1]
                    if len(열들) >= 2 and 순[순.index(열들[0]):순.index(열들[0]) + len(열들)] == 열들:
                        k1, k2 = 지.열자리[놓1][열들[0]], 지.열자리[놓1][열들[-1]]
                    else:
                        풀린병합.append((놓1, g["r"], g["키"]))      # 한 칸만 남거나 흩어졌다 — 병합할 것이 없다(아래에서 한 번 알린다)
                        continue
                else:
                    k1, k2 = 지.칸글자(g["r"], g["c"])[1], 지.칸글자(g["r2"], g["c2"])[1]
            except (KeyError, 배치오류):
                지._경고("병합", 놓1, [g["r"], g["c"]], "병합의 끝을 새 배치에서 찾지 못해 병합을 버렸다")
                continue
            if None in (k1, k2):
                if not (k1 is None and k2 is None):
                    지._경고("병합", 놓1, [g["r"], g["c"]], "병합의 한쪽 끝만 빠졌다 — 병합을 버렸다")
                continue   # 통째로 뺀 열의 병합은 말없이 버린다
            if n1 > n2 or 열번호(k1) > 열번호(k2):
                지._오류("병합", 놓1, [g["r"], g["c"]], "병합의 양 끝 순서가 뒤집혔다")
                continue
            if g["r"] != g["r2"]:
                문제 = 지._행범위(g["r"], g["r2"], False)[0]
                for m in 문제:
                    지._경고("병합", 놓1, [g["r"], g["c"]], "여러 줄 병합 — " + m)
            병합하기(놓1, k1, n1, k2, n2, [g["r"], g["c"]])

        # 목록 유효성 — 칸 집합으로 옮긴다(줄 순서가 바뀌어도, 줄이 다른 시트로 가도 따라간다)
        for v in 명.get("유효성", []):
            집들 = 지.칸집합(v["범위"])
            if not 집들:
                if 본 in 지.새이름:
                    지._경고("유효성", 본, None, "대상 칸이 모두 빠져 유효성을 버렸다")
                continue
            for 놓, 집 in 집들.items():
                if 표준길 and v.get("type") == "list":      # 선택 칸에만 건다(값이 놓이지 않는 줄의 칸은 뺀다)
                    집 = 집 & 선택칸.get(놓, set())
                    if not 집:
                        continue
                dv = DataValidation(type=v.get("type"), operator=v.get("operator"),
                                    allow_blank=v.get("allow_blank", False),
                                    showErrorMessage=v.get("showErrorMessage", False),
                                    showInputMessage=v.get("showInputMessage", False),
                                    showDropDown=v.get("showDropDown", False),
                                    error=v.get("error"), errorTitle=v.get("errorTitle"), errorStyle=v.get("errorStyle"),
                                    prompt=v.get("prompt"), promptTitle=v.get("promptTitle"))
                for k in ("formula1", "formula2"):
                    if k in v:
                        setattr(dv, k, 지.수식(v[k], 놓, [v["범위"][0]["r"], v["범위"][0]["c"]], 본sid=본)[1:])
                dv.sqref = MultiCellRange(지.범위글(집))
                시트ws[놓].add_data_validation(dv)

        # 조건부 서식 — 칸 집합으로 옮기고, 수식은 범위 첫 칸을 기준으로 다시 세운다
        for c in 명.get("조건부서식", []):
            for 놓, 집 in 지.칸집합(c["범위"]).items():
                규칙 = Rule.from_tree(fromstring(c["규칙"]))
                규칙.formula = [지.수식(f, 놓, [c["범위"][0]["r"], c["범위"][0]["c"]], 본sid=본)[1:] for f in c["수식"]]
                if c.get("서식"):
                    규칙.dxf = DifferentialStyle.from_tree(fromstring(c["서식"]))
                시트ws[놓].conditional_formatting.add(지.범위글(집), 규칙)

    if 풀린병합:      # 옮긴 줄의 병합이 풀렸다 — 한 번 알린다(줄마다 알리면 묻힌다)
        지._경고("병합", 풀린병합[0][0], [풀린병합[0][1], None],
               "다른 시트로 옮긴 줄의 병합 %d곳이 풀렸다 — 병합에 들던 열들이 놓인 시트에서 붙어 있지 않다(「열맞춤」으로 한 칸만 남았거나 흩어졌다). "
               "병합이 있어야 하면 놓인 시트의 열을 그 차례로 두거나 그 줄을 새 줄로 다시 적는다. 보기: %s" % (
                   len(풀린병합), ", ".join("%s(%s)" % (rid, 키) for _, rid, 키 in 풀린병합[:5])),
               목록=["%s 에 놓인 %s 의 병합 「%s」" % x for x in 풀린병합])

    for sid, b in 지은시트:
        명 = 명세["시트"][sid]
        ws = 시트ws[sid]
        속 = 명.get("속성", {})
        순 = 지.새열순서[sid]

        def 이시트칸(범위글들, 종류):
            """배치가 준 범위 글 → 이 시트의 칸 집합(다른 시트에 놓인 줄이 끼면 오류)."""
            범위 = [줄무늬.범위읽기(g, 문, 엄한=True) for g in 범위글들]
            집들 = 지.칸집합(범위, 알림시트=sid)
            for 놓 in 집들:
                if 놓 != sid:
                    지._오류(종류, sid, None, "이 시트에 놓이지 않은 줄을 가리킨다(%s 에 놓였다): %s" % (놓, " ".join(범위글들)[:80]))
            return 범위, 집들.get(sid, set())

        for v in b.get("유효성", []):       # 배치가 준 목록 유효성
            try:
                _, 집 = 이시트칸(v["범위"], "유효성")
            except 배치오류 as e:
                for o in e.오류목록:
                    지._오류("유효성", sid, None, o["설명"])
                continue
            if 표준길:
                집 = 집 & 선택칸.get(sid, set())
            if 집:
                dv = DataValidation(type="list", formula1='"' + ",".join(v["목록"]) + '"',
                                    allow_blank=bool(v.get("빈칸허용")), showErrorMessage=True,
                                    errorStyle="warning" if v.get("경고") else None,
                                    errorTitle="입력 오류", error="목록에서 고르십시오: " + ", ".join(v["목록"]))
                dv.sqref = MultiCellRange(지.범위글(집))
                ws.add_data_validation(dv)

        for c in b.get("조건부서식", []):   # 배치가 준 조건부 서식
            try:
                범위, 집 = 이시트칸(c["범위"], "조건부 서식")
            except 배치오류 as e:
                for o in e.오류목록:
                    지._오류("조건부 서식", sid, None, o["설명"])
                continue
            if not 집:
                continue
            글꼴 = Font(color=c.get("글자색"), b=c.get("굵게")) if (c.get("글자색") or c.get("굵게")) else None
            채움 = PatternFill("solid", start_color=c["채움"], end_color=c["채움"]) if c.get("채움") else None
            if "수식" in c:
                # 조건부 서식의 수식은 범위 첫 칸의 줄·열 자리에서 읽는다(그 줄의 본 시트의 열 ID)
                식 = 지.손수식(c["수식"], sid, 범위[0]["r"], 범위[0]["c"])[1:] if 지.본시트(범위[0]["r"]) == sid else \
                    지.수식(_손틀(지, c["수식"], 범위[0], sid), sid, [범위[0]["r"], 범위[0]["c"]], 엄한=True,
                         본sid=지.본시트(범위[0]["r"]))[1:]
                규칙 = FormulaRule(formula=[식], font=글꼴, fill=채움)
            else:
                규칙 = CellIsRule(operator=c.get("연산", "equal"), formula=[str(c["값"])], font=글꼴, fill=채움)
            ws.conditional_formatting.add(지.범위글(집), 규칙)

        if 표준길 and 판정칸.get(sid):      # 판정 칸 — Error 빨강 · Review 주황(색 셋 규칙의 예외는 여기뿐이다)
            훅.판정서식(ws, 지.범위글(판정칸[sid]).split())

        # 줄 묶음 · 열 묶음(그룹 접기)
        if b.get("묶음"):
            ws.sheet_properties.outlinePr.summaryBelow = bool(b.get("묶음요약아래", False))   # 요약 줄은 묶음 바로 위
        for 묶 in b.get("묶음", []):
            try:
                n1, n2 = 지.놓인행(묶["줄"][0], sid), 지.놓인행(묶["줄"][-1], sid)
            except KeyError as e:
                지._오류("묶음", sid, None, "줄 묶음의 행 ID 를 모른다(이 시트에 놓인 줄이 아니다): %s" % e)
                continue
            if n1 is None or n2 is None or n1 > n2:
                지._오류("묶음", sid, None, "줄 묶음의 두 끝이 빠졌거나 뒤집혔다: %s" % 묶["줄"])
                continue
            for n in range(n1, n2 + 1):
                d = ws.row_dimensions[n]
                d.outlineLevel = max(d.outlineLevel or 0, 묶.get("수준", 1))
                if 묶.get("숨김"):
                    d.hidden = True
            if 묶.get("숨김"):
                ws.row_dimensions[n1 - 1 if not b.get("묶음요약아래") else n2 + 1].collapsed = True
        for 묶 in b.get("열묶음", []):
            try:
                k1, k2 = 열번호(지.열자리[sid][묶["열"][0]]), 열번호(지.열자리[sid][묶["열"][-1]])
            except KeyError as e:
                지._오류("묶음", sid, None, "열 묶음의 열 ID 를 모른다: %s" % e)
                continue
            if k1 > k2:
                지._오류("묶음", sid, None, "열 묶음의 두 끝이 뒤집혔다: %s" % 묶["열"])
                continue
            for k in range(k1, k2 + 1):
                d = ws.column_dimensions[열글자(k)]
                d.outlineLevel = max(d.outlineLevel or 0, 묶.get("수준", 1))
                if 묶.get("숨김"):
                    d.hidden = True
            if 표준길 and 묶.get("숨김") and k1 > 1:      # 접힌 묶음의 요약 열(왼쪽 열)에 접힘 표시
                ws.column_dimensions[열글자(k1 - 1)].collapsed = True

        # 틀 고정 — 배치가 주면 그것, 아니면 명세의 것
        틀 = b.get("틀고정") or 속.get("틀고정")
        if 틀:
            try:
                def 여기행(rid):
                    return 지.행자리.get(rid) if 지.놓인.get(rid) == sid else None
                if 틀["행"] not in 지.행소속:
                    raise KeyError(틀["행"])
                n = 여기행(틀["행"])
                옛번 = 지.옛순서[sid].get(틀["행"])
                while n is None and 옛번 is not None and 옛번 + 1 < len(명["행"]):   # 고정 줄을 뺐거나 옮겼으면 그 아래 첫 남은 줄
                    옛번 += 1
                    n = 여기행(명["행"][옛번]["id"])
                g = 지.새열글자(sid, 틀["열"]) or "A"
                ws.freeze_panes = "%s%d" % (g, n or 1)
            except KeyError as e:
                지._오류("틀 고정", sid, None, "틀 고정의 행·열 ID 를 모른다: %s" % e)

        # 인쇄 — 명세의 것 위에 배치의 것을 덮는다
        인 = dict(속.get("인쇄") or {})
        인b = b.get("인쇄") or {}
        if 표준길 and 훅.쓸수있나:
            인 = {}                                   # 옛 파일의 인쇄 설정은 쓰지 않는다
            인b = _표준인쇄(지, 문, 훅, sid, 인b, ws.freeze_panes)
        인.update({k: v for k, v in 인b.items() if k not in ("제목행", "제목열", "영역")})
        if 인.get("방향"):
            ws.page_setup.orientation = 인["방향"]
        if 인.get("용지"):
            ws.page_setup.paperSize = 인["용지"]
        if 인.get("쪽맞춤") or "폭맞춤" in 인b or "높이맞춤" in 인b:
            ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
            ws.page_setup.fitToWidth = 인.get("폭맞춤")
            ws.page_setup.fitToHeight = 인.get("높이맞춤")
        바 = 인.get("바닥글")
        if isinstance(바, str):
            ws.oddFooter.center.text = 바
        elif isinstance(바, dict):
            for 자리이름, 곳 in (("왼쪽", ws.oddFooter.left), ("가운데", ws.oddFooter.center), ("오른쪽", ws.oddFooter.right)):
                if 바.get(자리이름):
                    곳.text = 바[자리이름]
        if 인.get("여백"):
            ws.page_margins = PageMargins(**인["여백"])
        if 인.get("가로가운데"):
            ws.print_options.horizontalCentered = True
        if 표준길 and 훅.쓸수있나:
            ws.print_options.gridLines = False
            for 곳 in (ws.oddFooter.left, ws.oddFooter.center, ws.oddFooter.right):
                if 곳.text:
                    곳.size, 곳.font = 8, 훅.표준.글꼴이름 + ",보통"
        try:
            if 인b.get("제목행"):
                ws.print_title_rows = "%d:%d" % (지.놓인행(인b["제목행"][0], sid), 지.놓인행(인b["제목행"][-1], sid))
            if 인b.get("제목열"):
                ws.print_title_cols = "%s:%s" % (지.새열글자(sid, 인b["제목열"][0]), 지.새열글자(sid, 인b["제목열"][-1]))
            영역 = 인b.get("영역")
            if 영역 and 지.새순서[sid]:
                # 영역 = "전부" 또는 {"끝행": 행 ID(안 주면 마지막 줄), "끝열": 열 ID(안 주면 마지막 열)}
                끝행 = 지.새순서[sid][-1][0] if (영역 == "전부" or not 영역.get("끝행")) else 지.놓인행(영역["끝행"], sid)
                끝열 = 열글자(len(순)) if (영역 == "전부" or not 영역.get("끝열")) else 지.새열글자(sid, 영역["끝열"])
                ws.print_area = "A1:%s%d" % (끝열, 끝행)
            for rid in 인b.get("쪽나눔", []):
                ws.row_breaks.append(Break(id=지.놓인행(rid, sid) - 1))
        except (KeyError, TypeError) as e:
            지._오류("인쇄", sid, None, "인쇄 설정의 행·열 ID 를 이 시트의 새 배치에서 찾지 못했다: %s" % e)
        if (속.get("인쇄") or {}).get("제목행") or (속.get("인쇄") or {}).get("제목열") or (속.get("인쇄") or {}).get("영역"):
            지._경고("인쇄", sid, None, "옛 파일의 인쇄 제목 행·영역(좌표 글)은 옮기지 않는다 — 배치의 「인쇄」로 준다")

        # 시트 안 정의된 이름
        for d in 명.get("정의된이름", []):
            ws.defined_names[d["이름"]] = DefinedName(d["이름"], attr_text=지.수식(d["틀"], sid, None)[1:])

    for d in 책.get("정의된이름", []):
        wb.defined_names[d["이름"]] = DefinedName(d["이름"], attr_text=지.수식(d["틀"], None, None)[1:])
    wb.calculation.fullCalcOnLoad = True
    안선유효성 = []
    if 표준길 and 훅.쓸수있나:      # 목록 유효성은 선택 칸으로 선 칸에만 남긴다 — 계산 줄에 걸친 범위(옛 파일의 범위 밀림)의 빈 칸에 목록이 남지 않게
        선택스타일 = 서식훅.훅표["선택"]
        for sid, ws in 시트ws.items():
            남길 = []
            for dv in ws.data_validations.dataValidation:
                if dv.type != "list":
                    남길.append(dv)
                    continue
                집 = {(n, k) for g in dv.sqref.ranges for n in range(g.min_row, g.max_row + 1) for k in range(g.min_col, g.max_col + 1)}
                선 = {자 for 자 in 집 if 자 in ws._cells and ws._cells[자].style == 선택스타일}
                안선유효성 += ["%s!%s%d" % (ws.title, 열글자(k), n) for n, k in sorted(집 - 선)]
                if 선:
                    dv.sqref = MultiCellRange(지.범위글(선))
                    남길.append(dv)
            ws.data_validations.dataValidation = 남길
    if 푼병합:      # 표준 서식 길 — 병합은 제목 줄에만(0_결정 5절). 띠와 흘려 쓰기로 대신한다
        지._경고("표준 서식", None, None, "제목 줄이 아닌 병합 %d곳을 풀었다(병합은 제목 줄에만 남긴다). 보기: %s"
               % (len(푼병합), ", ".join(푼병합[:5])), 푼병합=푼병합)
    if 뺀유효성:
        지._경고("표준 서식", None, None, "목록 유효성 범위에 든 칸 %d곳을 뺐다 — 값이 놓이지 않는 줄(제목 · 구획머리 · 머리 · 글 · 빈 줄)이다. 보기: %s"
               % (len(뺀유효성), ", ".join(뺀유효성[:5])), 목록=뺀유효성)
    if 안선유효성:
        지._경고("표준 서식", None, None, "목록 유효성 범위에 든 칸 %d곳을 뺐다 — 선택 칸으로 서지 않은 칸(입력 칸이 아닌 계산 줄의 칸 따위)이다. 보기: %s"
               % (len(안선유효성), ", ".join(안선유효성[:5])), 목록=안선유효성)
    if 직접서식:
        지._경고("표준 서식", None, None, "「줄서식」의 직접 서식(글자색 · 채움 · 숫자서식) %d곳을 입히지 않았다 — 표준 서식 길에서는 "
               "종류 · 서식 · 선 · 들여 · 굵게 · 칸꼴로 적는다. 보기: %s" % (len(직접서식), ", ".join(직접서식[:5])), 목록=직접서식)

    짝수 = 지.짝점검()

    # 「범위허용」·「범위에넣기」 표시를 단 줄이 어느 범위에도 들지 않았다 — 합계에 안 더해진다. 표시를 떼거나 범위 안에 놓는다
    for rid in sorted((지.범위허용 | 지.범위에넣기) - 지.범위에든):
        if rid in 지.행자리:
            지._오류("범위허용", 지.놓인.get(rid), [rid, None],
                   "「범위허용」·「범위에넣기」 표시가 있으나 어느 범위에도 들지 않았다 — 합계 따위에 더해지지 않는다(범위 안에 놓거나 표시를 뗀다)")

    # 시간축 묶음에 열을 더했는데 그 묶음의 열 ID 를 못 박은 참조가 남았다 — 그 수식은 옛 열을 그대로 읽는다
    if 지.못박은 or 지.못박은열쇠:
        열별 = Counter(cid for _, _, _, cid in 지.못박은)
        목록 = ["%s %s → [%s]@%s" % (현재, 자리, rid, cid) for 현재, 자리, rid, cid in 지.못박은]
        열쇠목록 = ["%s %s 의 %s 열쇠 「%s」 — 열 %s 에 못 박혔다(새 열에는 놓이지 않는다)" % x for x in 지.못박은열쇠]
        글 = ("시간축 묶음에 열을 더했는데(%s) 그 묶음의 열 ID 를 못 박은 참조가 %d곳 남았다 — %s. 새 열을 따라가지 않는다. "
             "「.끝」·「.첫」·묶음으로 고쳐 적은 뒤에 열을 더한다. 보기: %s" % (
                 ", ".join("%s 의 %s" % x for x in sorted(지.늘종류)), len(목록),
                 " · ".join("@%s %d곳" % (c, n) for c, n in 열별.most_common()) or "없음", " / ".join(목록[:5]) or "없음"))
        if 열쇠목록:
            글 += (" · 묶음의 끝(첫) 열에 못 박힌 열 구간 열쇠(무늬·글·값)가 %d곳 있다 — 그 줄의 수식·값이 새 열에 놓이지 않는다. "
                  "「E2~예측」·「예측.끝」·「예측.첫」으로 고쳐 적는다. 보기: %s" % (len(열쇠목록), " / ".join(열쇠목록[:3])))
        (지._경고 if 못박은열허용 else 지._오류)("못 박은 열", None, None, 글, 목록=목록 + 열쇠목록,
                                       참조수=len(목록), 열쇠수=len(열쇠목록))

    # 펼쳐지는 함수 — 생성기는 수식을 칸마다 적는다. 그 칸에는 첫 값만 나오고 옆 칸으로 펼쳐지지 않는다(SUM 따위로 감싼 값은 맞다)
    for 이름, 곳 in sorted(지.펼침.items()):
        지._경고("펼쳐지는 함수", 곳[0][0], 곳[0][1], "%s 가 %d칸에 쓰였다 — 값이 옆 칸으로 펼쳐지지 않는다(그 칸에는 첫 값만 나온다. "
               "SUM · INDEX 따위로 감싸 값 하나를 받는 것이면 맞다)" % (이름, len(곳)))

    # 글 속 좌표 — 글 칸과 수식 속 문자열 상수의 「E28」「12번 30행」 따위는 옮기지 않는다.
    # 줄·열의 자리나 시트 이름이 바뀐 배치면 낡은 말이 됐을 수 있으므로 한 번 알린다(같은 배치면 조용하다)
    옮김 = bool(지.뺀줄) or bool(지.새줄) or bool(옮긴줄수) or any(
        지.새이름[sid] != (명세["시트"][sid].get("옛이름") or 명세["시트"][sid].get("이름")) or
        [c["id"] for c in 명세["시트"][sid]["열"]] != 지.새열순서[sid] or
        [r["id"] for r in 명세["시트"][sid]["행"]] != [rid for _, rid in 지.새순서[sid]] or
        any(n != i + 1 for i, (n, _) in enumerate(지.새순서[sid])) or
        # 행 ID 의 번호 ≠ 놓인 행 — 명세에서 줄을 지운 뒤로는 같은 배치로 지어도 글 속의 「30행」이 그 줄이 아니다(W1 검증의 작은 결함 1)
        # (옛 xlsx 의 행 번호를 ID 로 물려받은 줄 — 「옛행」 — 만 본다. 명세로 새로 지은 시트의 줄 ID 는 자리와 무관하다)
        any(옛줄all[rid].get("옛행") not in (None, n) for n, rid in 지.새순서[sid] if rid in 옛줄all)
        for sid in 지.새이름)
    if 옮김:
        글칸 = _글속좌표칸(명세, 지)
        if 글칸:
            지._경고("글 속 좌표", None, None,
                   "글 칸·수식 속 문자열 %d칸에 좌표처럼 보이는 말이 있다 — 옮기지 않는다(자리가 바뀐 배치라 낡았을 수 있다). 보기: %s"
                   % (len(글칸), ", ".join("%s %s" % x for x in 글칸[:3])))

    # 덧붙인 이름이 지금 이름과 다른 곳 — 문법이 내세운 안전장치다. 다르면 멈춘다(한 줄·한 이름에 한 번만 알린다)
    이름알림 = 지._경고 if 이름불일치허용 else 지._오류
    풀이 = "" if 이름불일치허용 else " — 행 ID 가 틀렸는지 본다. 줄 이름을 고친 것이면 「python 줄무늬.py --다시쓰기 <명세 폴더>」 로 맞춘다"
    for 한 in 명세.get("이름경고", []):      # 줄 이름을 고친 것인지 · 행 ID 를 틀리게 적었을 수 있는지를 갈라 알린다(줄이름.json)
        이름알림("덧붙인 이름", 지.본시트(한["행"]), [한["행"], None], 줄무늬.이름알림글(한), 갈래=한.get("갈래"))
    for (rid, 덧), n in 문.이름경고.items():
        이름알림("덧붙인 이름", 지.놓인시트(rid), [rid, None],
             "%s 를 가리키는 수식에 덧붙인 이름 「%s」 이 지금 이름 「%s」 과 다르다(%d곳)%s" % (
                 rid, 덧, " / ".join(문.행이름.get(rid) or ["(없음)"]), n, 풀이))

    # 틀로 못 바꾸는 함수가 명세에 있으면 한 번 알린다(INDIRECT 처럼 참조 없이 글만 받는 것도 여기서 걸린다)
    목록곳 = os.path.join(명세.get("폴더") or "", "목록_좌표의존함수.json")
    if os.path.exists(목록곳):
        with open(목록곳, encoding="utf-8") as f:
            for 함수, 한 in json.load(f)["함수별"].items():
                if 한["틀로못바꿈"]:
                    지._경고("못 바꾸는 함수", None, None, "%s 가 %d곳에 쓰였다 — %s" % (함수, 한["수"], 한["설명"]))

    지도 = OrderedDict()
    지도["형식"] = 2
    지도["명세"] = os.path.basename(명세.get("폴더") or "") or None       # 절대 경로는 싣지 않는다(폴더가 바뀌어도 지도가 같게)
    지도["원본"] = os.path.basename(책.get("원본") or "") or None
    지도["시트"] = OrderedDict()
    for sid in 지.새이름:
        명 = 명세["시트"][sid]
        옛글 = {c["id"]: c.get("옛") for c in 명["열"]}
        자리 = 지.열자리[sid]
        열 = OrderedDict()
        for cid in 지.새열순서[sid]:           # 옛 열 글자 → 새 열 글자(배치가 더한 새 열은 열 ID 로 싣는다 — 원형과 같다)
            열[옛글.get(cid) or cid] = 자리[cid]
        # 회차의 기간으로 지은 시트 — 틀의 시간축 열(옛 D~R)은 이 배치에 없다. 「뺀 열」로 실어 옛 열 글자로 부르면 자리가 없다고 답하게 한다
        # (기간 열은 기간 ID 로, 값 칸은 그 줄 쓰임의 별칭으로 부른다 — 틀의 옛 열 글자 · 별칭 표는 「틀」에 싣는다)
        틀머리 = 명.get("머리원") if 명세.get("기간") else None
        틀열 = [c for c in (틀머리 or {}).get("열", ()) if c.get("갈래")]
        지도["시트"][sid] = {
            "옛이름": 명.get("옛이름"), "새이름": 지.새이름[sid], "열": 열,
            "뺀열": sorted(옛글.get(c) or c for c in 지.뺀열[sid]) + [c["옛"] for c in 틀열 if c.get("옛")],
            "옛끝행": 지.옛끝번호[sid],
            "새끝행": 지.새순서[sid][-1][0] if 지.새순서[sid] else 0,
            "옛끝열": len(틀머리["열"]) if 틀머리 else len(명["열"]),
            # 넓힌 것 — 열 ID 로 부르는 조회
            "열ID": OrderedDict((cid, 자리[cid]) for cid in 지.새열순서[sid]),
            "옛열ID": OrderedDict((옛글[c["id"]], c["id"]) for c in 명["열"] if 옛글.get(c["id"])),
            "뺀열ID": sorted(지.뺀열[sid]),
            "열종류": {cid: 문.열종류[sid].get(cid) for cid in 지.새열순서[sid]},
            "묶음": {이름: 지.묶음새열(sid, 이름) for 이름 in 문.묶음.get(sid, {})},
            "쓰임": 문.쓰임.get(sid, {}),
        }
        if 틀열:
            지도["시트"][sid]["틀"] = {"옛열ID": OrderedDict((c["옛"], c["id"]) for c in 틀열 if c.get("옛")),
                                    "쓰임": 명.get("틀쓰임") or {}}
    for sid in 명세["시트"]:                   # 통째로 뺀 시트 — 그 시트의 줄이 다른 시트에 실렸으면 옛 주소 조회에 옛 이름·옛 열이 있어야 한다
        if sid not in 지도["시트"] and any(지.본시트(rid) == sid for rid in 지.놓인):
            명 = 명세["시트"][sid]
            지도["시트"][sid] = {"옛이름": 명.get("옛이름"), "새이름": None, "열": {}, "뺀열": [], "옛끝행": 지.옛끝번호[sid],
                             "새끝행": 0, "옛끝열": len(명["열"]), "열ID": {}, "뺀열ID": [], "열종류": {}, "묶음": {},
                             "옛열ID": OrderedDict((c["옛"], c["id"]) for c in 명["열"] if c.get("옛")),
                             "쓰임": 문.쓰임.get(sid, {}), "뺀시트": True}
    지도["옛이름"] = {명세["시트"][sid]["옛이름"]: sid for sid in 지도["시트"] if 명세["시트"][sid].get("옛이름")}
    지도["행"] = {rid: n for rid, n in 지.행자리.items()}
    지도["뺀줄"] = sorted(지.뺀줄)
    지도["새줄"] = {rid: [지.놓인[rid], 지.행자리[rid]] for rid in 지.새줄 if rid in 지.행자리}
    지도["행쓰임"] = dict(문.행쓰임)
    지도["칸"] = 지도칸
    # 줄의 시트 이동 — 다른 시트에 놓인 줄과 그 줄의 열 맞춤(없으면 싣지 않는다 — 옛 형식의 지도와 같게)
    행시트 = {rid: 놓 for rid, 놓 in 지.놓인.items() if rid not in 지.새줄 and 놓 != 지.본시트(rid)}
    if 행시트:
        지도["행시트"] = 행시트
        지도["열맞춤"] = {놓: {본: 표 for 본, 표 in 한.items() if 표} for 놓, 한 in 지.열맞춤.items() if any(한.values())}
    # 키트 스크립트(좌표.py)가 읽는 표 — 명세의 수식 구조와 단위에서 낸다(워크북의 글을 읽지 않는다)
    지도["가정묶음"] = {sid: m for sid, m in ((sid, _가정묶음(명세["시트"][sid])) for sid in 지.새이름) if m}
    지도["단위"] = {sid: u for sid, u in ((sid, _단위표(명세["시트"][sid], 문)) for sid in 지.새이름) if u}
    if 가정시트 in 지.새이름:
        축종류 = set(명세["시트"][가정시트].get("축", ()))
        옛글 = {c["id"]: c.get("옛") for c in 명세["시트"][가정시트]["열"]}
        if 명세.get("기간"):      # 회차의 기간으로 지었다 — 열 ID 가 기간 ID 다. 축 전체(기간축.사전())를 함께 싣는다
            import 기간열
            # id = 기간 ID(= 열 ID) · 열 = 그 열의 글자(시간축 시트는 모두 같은 글자에 놓는다 — 12번의 것을 싣는다)
            지도["기간열"] = [{"id": c, "구분": 문.열종류[가정시트].get(c), "열": 지.열자리[가정시트].get(c)}
                          for c in 지.새열순서[가정시트] if 문.열종류[가정시트].get(c) in 축종류]
            지도["기간"] = 기간열.간추림(명세["기간"])
        else:
            지도["기간열"] = [옛글.get(c) or c for c in 지.새열순서[가정시트] if 문.열종류[가정시트].get(c) in 축종류]
    지도["지문"] = 좌표지도.지문(지도)
    _지도덧(지도, 명세, 지, 시트ws, wb)
    # 칸 단위 고리 검사 — 지은 수식의 참조를 칸마다 따라가 고리가 있으면 파일을 내지 않는다(9-3. 엑셀의 순환 참조 읽기 · 대조의 값 없음 오류 앞의 첫 겹)
    _, _, 고리들 = 고리검사.검사wb(wb)
    if 고리들:
        줄of = {(ws.title, n): rid for sid, ws in 시트ws.items() for n, rid in 지.새순서.get(sid, ())}
        for 한 in 고리들[:20]:
            지._오류("고리", None, None, "수식이 서로를 읽는 고리(순환 참조) — 칸 %d개: %s%s" % (
                len(한), " → ".join("%s(%s)" % (고리검사.칸글(x), 줄of.get((x[0], x[2]), "?")) for x in 한[:8]), " …" if len(한) > 8 else ""),
                목록=[고리검사.칸글(x) for x in 한])
        if len(고리들) > 20:
            지._오류("고리", None, None, "고리가 %d개 더 있다" % (len(고리들) - 20))
    if 지문남기기:      # 워크북에 배치의 지문을 남긴다 — 키트의 좌표.확인 이 다른 배치의 지도와 짝지은 것을 가려낸다
        from openpyxl.packaging.custom import StringProperty
        wb.custom_doc_props.append(StringProperty(name=좌표지도.지문이름, value=지도["지문"]))
    결과 = {"지도": 지도, "오류": 지.오류, "경고": 지.경고, "짝": 짝수, "옮긴 줄": 옮긴줄수}
    if 지.오류 and 엄격:
        raise 배치오류(지.오류)
    os.makedirs(os.path.dirname(os.path.abspath(낼곳)), exist_ok=True)
    wb.save(낼곳)
    if 지도곳:
        with open(지도곳, "w", encoding="utf-8") as f:
            json.dump(지도, f, ensure_ascii=False, separators=(",", ":"))
    return 결과


def _줄이름해시(v):
    """줄 이름 칸의 값 → 지문 글자(키트 좌표.py 의 `_줄이름해시` 와 같은 셈) — 빈칸이면 None, 수식이면 「=」, 글이면 다듬은 글의 sha1 앞 8자."""
    import hashlib
    if v is None:
        return None
    글 = ("%s" % (v,)).strip()
    if not 글:
        return None
    if isinstance(v, str) and 글.startswith("="):
        return "="
    return hashlib.sha1(글.encode("utf-8")).hexdigest()[:8]


_re번호행 = re.compile(r"^([SX]\d+)R(\d+)$")


대조종류 = ("계산", "소계", "합계", "비율")       # 엔진 = 워크북 대조의 대상 줄(설계서 9-2)
# 「대조열」로 적는 열의 묶음 → 열 종류. 적지 않으면 「전부」 — 수식이 선 값 열 전부(시간축의 실적 · 예측 · 영구, 시간축이 없는 시트의 값 열)
대조열묶음 = {"전부": ("실적", "예측", "영구", "값"), "예측영구": ("예측", "영구"), "예측": ("예측",), "영구": ("영구",), "실적": ("실적",)}


def _지도덧(지도, 명세, 지, 시트ws, wb):
    """좌표 지도에 싣는 덧 표 (W3a) — 명세 지문 · 구조 지문 · 줄 속성 · 표 구획 · 짓지 않은 줄 · 줄 이름 지문 · 이름 칸 · 단위 종류.

    명세지문     축 · 구조와 무관한 명세의 지문(줄무늬._명세지문) — 축이 다른 회차끼리도 같은 명세로 지었는지 가린다
    구조지문     기간 · 구조 · 명세지문에서 낸 글자(좌표지도.구조지문). 기간으로 지은 워크북에만. 12번 시트의 숨은 이름 `_구조지문` 에도 남긴다
    구조지문재료 되풀이 정의가 가정 파일에서 읽은 값의 경로들(있을 때만) — 키트가 지문을 다시 낼 때 그 값도 넣는다
    구조         {"안지은줄": {행 ID | 틀의 id: 까닭}, "틀": [{id, 되풀이, 시트, 지은: [행 ID …]}]} — 구조가 요구한 줄 집합의 기록(I-151)
    줄속성       {행 ID: {시나리오 · 빈칸허용 · 표}} — 그 속성을 적은 줄만(줄의 등록부 — 엔진 · 대조 · 자체검사가 읽는다)
    대조줄       {시트 ID: {"번호": {종류 · 서식 · 열(수식이 선 시간축 열) 또는 쓰임 · 칸}}} — 종류가 계산 · 소계 · 합계 · 비율인 지은 줄 전부(W3c).
                 키트의 대조가 이 표로 엔진 = 워크북을 견준다(대조표를 손으로 적지 않는다)
    견주지않는줄 {행 ID: 까닭} — 명세에 「대조」: false 를 단 줄
    표구획       {시트 ID: {표 이름: {"칸": [칸 이름 …], "열": [열 ID …], "줄": [행 ID …]}}} — 가정 파일의 「표.<번호>.<칸>」이 들어갈 자리
    줄이름지문   {시트 ID: {"번호": 지문}} — 지은 워크북의 줄 이름 칸에서(키트의 좌표지도보강.py 가 스캐폴드에서 읽던 것과 같은 표)
    이름칸 · 단위종류 · 이름입히기  이름표/ 가 있는 명세(정본)면 이름입히기가 명세에서 낸다(「이름입히기.py --지도」 와 같은 표)
    """
    if 명세.get("명세지문"):
        지도["명세지문"] = 명세["명세지문"]
    구 = 명세.get("구조")
    if 구 is not None:
        if 구.get("안지은") or 구.get("틀"):
            지도["구조"] = OrderedDict([("안지은줄", 구.get("안지은") or {}), ("틀", 구.get("틀") or [])])
        if 명세.get("기간"):
            지도["구조지문"] = 좌표지도.구조지문(명세["기간"], 구.get("준것") if not 구.get("틀읽기") else {}, 명세.get("명세지문"), 구.get("쓴경로"))
            if 구.get("쓴경로"):
                지도["구조지문재료"] = list(구["쓴경로"])
            if 가정시트 in 시트ws:
                이름 = DefinedName(좌표지도.구조이름, attr_text='"%s"' % 지도["구조지문"], hidden=True)
                시트ws[가정시트].defined_names[좌표지도.구조이름] = 이름
    속성 = OrderedDict()
    표구획 = OrderedDict()
    for sid, 명 in 명세["시트"].items():
        for 줄 in 명["행"]:
            한 = OrderedDict((k, 줄[k]) for k in ("시나리오", "빈칸허용", "표", "표머리") if 줄.get(k))
            if 한 and 줄["id"] in 지.행자리:
                속성[줄["id"]] = 한
        for 표이름, 한 in (명.get("표") or {}).items():
            쓰 = 지.문.쓰임.get(sid, {}).get(표이름) or {}
            표구획.setdefault(sid, OrderedDict())[표이름] = {"칸": list(한["칸"]), "열": [쓰.get(칸) for 칸 in 한["칸"]],
                                                         "줄": [rid for rid in 한["줄"] if rid in 지.행자리]}
    if 속성:
        지도["줄속성"] = 속성
    if 표구획:
        지도["표구획"] = 표구획
    # 대조 줄 — 엔진 = 워크북 대조의 등록부(설계서 9-2 · W3c). 종류가 계산 · 소계 · 합계 · 비율인 지은 줄 전부를 싣는다.
    #   {시트 ID: {"번호": {"종류", "서식", "쓰임"(있을 때), "열": [수식이 선 값 열 ID …], "칸": {별칭: 열 ID}(쓰임이 있는 줄 — 수식이 선 값 칸)}}}
    # 명세에 `"대조": false` 를 단 줄(글 · 날짜를 내는 줄 · 도구 기입 칸)은 「견주지않는줄」({행 ID: 까닭})에 싣는다 — 조용히 빠지지 않는다.
    # `"대조열": "예측영구"` 를 적은 줄은 그 묶음의 열만 대조한다(실적 열이 원천을 그대로 읽는 연결인 줄)
    # 종류가 계산 줄이 아닌 수식 줄은 「대조밖수식줄」({시트 ID: {종류: [번호 …]}})에 싣는다 — 키트의 대조가 그 수를 화면에 내고,
    # 머리 · 점검 · 입력 밖의 종류면 멈춘다(산식 줄을 다른 종류로 적어 대조를 비켜 가지 못한다)
    대조줄, 안견줌, 종류밖 = OrderedDict(), OrderedDict(), OrderedDict()
    for sid, 명 in 명세["시트"].items():
        종류of = OrderedDict((c["id"], c.get("종류")) for c in 명["열"])
        for 줄 in 명["행"]:
            rid = 줄["id"]
            m = _re번호행.match(rid)
            if not m or rid not in 지.행자리 or rid in 지.새줄:
                continue
            n = 지.행자리[rid]

            def 수식인가(cid, rid=rid, n=n):
                try:
                    놓, 글자 = 지.칸글자(rid, cid)
                except KeyError:
                    return False
                if 글자 is None or 놓 not in 시트ws:
                    return False
                칸 = 시트ws[놓]._cells.get((n, 열번호(글자)))
                v = getattr(칸.value, "text", 칸.value) if 칸 is not None else None
                return isinstance(v, str) and v.startswith("=")
            if 줄.get("종류") not in 대조종류:
                # 종류가 계산 줄이 아닌데 값 열에 수식이 선 줄(머리 · 점검 · 제안값 수식을 둔 입력) — 대조 대상은 아니지만 수를 세어 알린다
                if any(종 in 대조열묶음["전부"] and 수식인가(cid) for cid, 종 in 종류of.items()):
                    종류밖.setdefault(m.group(1), OrderedDict()).setdefault(줄.get("종류") or "?", []).append(int(m.group(2)))
                continue
            if 줄.get("대조") is False:
                안견줌[rid] = 줄.get("메모") or "명세가 대조에서 뺐다(「대조」: false)"
                continue
            한 = OrderedDict([("종류", 줄["종류"])])
            if 줄.get("서식"):
                한["서식"] = 줄["서식"]
            쓰임 = 줄.get("쓰임")
            if 쓰임:
                한["쓰임"] = 쓰임
                별칭 = 지.문.쓰임.get(sid, {}).get(쓰임) or {}
                한["칸"] = OrderedDict((이름, cid) for 이름, cid in 별칭.items() if cid and 수식인가(cid))
            else:
                볼종류 = 대조열묶음.get(줄.get("대조열") or "전부", 대조열묶음["전부"])
                한["열"] = [cid for cid, 종 in 종류of.items() if 종 in 볼종류 and 수식인가(cid)]
                if 줄.get("대조열"):
                    한["대조열"] = 줄["대조열"]
            대조줄.setdefault(m.group(1), OrderedDict())["%d" % int(m.group(2))] = 한
    if 대조줄:
        지도["대조줄"] = 대조줄
    if 안견줌:
        지도["견주지않는줄"] = 안견줌
    if 종류밖:
        지도["대조밖수식줄"] = 종류밖
    # 줄 이름 지문 — 놓인 자리의 이름 칸에서 읽는다(옮긴 줄은 놓인 시트의 이름 열)
    이름표 = OrderedDict()
    이름열of = {sid: next((c["id"] for c in 명["열"] if c.get("종류") == "이름"), None) for sid, 명 in 명세["시트"].items()}
    for rid, n in 지.행자리.items():
        m = _re번호행.match(rid)
        if not m or not 이름열of.get(지.본시트(rid)):      # 배치가 끼운 새 줄(번호 꼴의 ID — 1번 「모델 점검 총괄」)도 싣는다 — 키트의 줄이름표가 읽는다
            continue
        try:
            놓, 글자 = 지.칸글자(rid, 이름열of[지.본시트(rid)])
        except KeyError:
            continue
        if 글자 is None or 놓 not in 시트ws:
            continue
        칸 = 시트ws[놓]._cells.get((n, 열번호(글자)))
        h = _줄이름해시(getattr(칸.value, "text", 칸.value)) if 칸 is not None else None
        if h:
            이름표.setdefault(m.group(1), OrderedDict())["%d" % int(m.group(2))] = h
    if 이름표:
        지도["줄이름지문"] = 이름표
    # 이름 칸 · 단위 종류 — 정본(이름표/ 를 읽는 명세)이면 이름입히기가 낸다. 다른 명세(합성 · 옛 판)는 싣지 않는다
    if 명세["책"].get("줄무늬") and 명세.get("폴더"):
        import 이름입히기
        if os.path.abspath(명세["폴더"]) == os.path.abspath(이름입히기.정본):
            이름입히기.명세에싣기(지도, 명세)


def _손틀(지, 글, 범위첫, sid):
    """옮겨 온 줄을 범위 첫 칸으로 하는 조건부 서식의 손 수식 → 틀(그 줄의 본 시트 자리에서 읽는다)."""
    try:
        return 손수식틀(글, 범위첫["c"], 지.본시트(범위첫["r"]), 지.문)
    except 배치오류 as e:
        for o in e.오류목록:
            지._오류(o["종류"], sid, [범위첫["r"], 범위첫["c"]], o["설명"])
        return ["=#REF!"]


def _꾸미기(칸, 꾸밈, 직접=True):
    """배치의 「줄서식」 — 굵게·글자색·채움·숫자 서식. 직접=False(표준 서식 길)면 아무것도 입히지 않는다
    (굵게는 줄의 덧 속성으로 이미 입혔고, 글자색 · 채움 · 숫자서식은 명명 스타일 밖의 서식이라 버린다)."""
    if not 직접:
        return
    if "굵게" in 꾸밈 or "글자색" in 꾸밈:
        f = copy(칸.font)
        칸.font = Font(name=f.name, sz=f.sz, b=꾸밈.get("굵게", f.b), i=f.i,
                      color=꾸밈.get("글자색", f.color), u=f.u, strike=f.strike, vertAlign=f.vertAlign)
    if "채움" in 꾸밈:
        칸.fill = PatternFill("solid", start_color=꾸밈["채움"], end_color=꾸밈["채움"])
    if "숫자서식" in 꾸밈 and isinstance(칸.value, (int, float, str)) and 칸.column > 3:
        칸.number_format = 꾸밈["숫자서식"]


def 알림찍기(목록, 머리, 보기=3, 낼=print):
    """오류·경고 목록을 종류별 건수와 내용으로 찍는다(종류마다 처음 몇 건은 전문)."""
    종류별 = OrderedDict()
    for o in 목록:
        종류별.setdefault(o["종류"], []).append(o)
    낼("%s %d건 — %s" % (머리, len(목록), " · ".join("%s %d" % (k, len(v)) for k, v in 종류별.items())))
    for 종류, 낱 in 종류별.items():
        낼("  [%s] %d건%s" % (종류, len(낱), " ※ 위험" if 머리 == "경고" and 종류 in 위험경고 else ""))
        for o in 낱[:보기]:
            곳 = " ".join(str(x) for x in (o.get("시트"), o.get("자리")) if x)
            낼("     %s%s" % ((곳 + " — ") if 곳 else "", o["설명"]))
            for 줄 in (o.get("목록") or [])[:20]:
                낼("        · %s" % 줄)
            if len(o.get("목록") or ()) > 20:
                낼("        … 그 밖 %d곳" % (len(o["목록"]) - 20))
        if len(낱) > 보기:
            낼("     … 그 밖 %d건" % (len(낱) - 보기))


def 명령줄(인자들, 낼=print):
    """명령줄 짓기 — 종료 코드를 돌려준다(0 지었다 · 1 오류 · 2 위험한 경고). 어떤 오류든 트레이스백 없이 무엇이 틀렸는지 알린다."""
    깃발 = {"--이름경고허용": False, "--합계범위승인": False, "--못박은열허용": False, "--경고허용": False, "--추적": False}
    서식길, 덧, 자리, 기간 = None, [], [], None
    i = 0
    while i < len(인자들):
        a = 인자들[i]
        if a == "--기간":       # 가정 파일(또는 기간 json) — 그 기간으로 시간축 열을 짓는다
            if i + 1 >= len(인자들) or 인자들[i + 1].startswith("--"):
                낼("--기간 뒤에 가정 파일(또는 기간 json)이 없다")
                return 1
            기간 = 인자들[i + 1]
            i += 2
        elif a == "--서식":     # 값을 받는 깃발 — 어느 자리에 적어도 바로 뒤의 글이 값이다
            if i + 1 >= len(인자들) or 인자들[i + 1].startswith("--"):
                낼("--서식 뒤에 값이 없다(%s)" % " · ".join(서식길들))
                return 1
            서식길 = 인자들[i + 1]
            i += 2
        elif a == "--덧명세":   # 다음 깃발 앞까지가 덧명세 파일이다
            i += 1
            while i < len(인자들) and not 인자들[i].startswith("--"):
                덧.append(인자들[i])
                i += 1
        elif a in 깃발:
            깃발[a] = True
            i += 1
        elif a.startswith("--"):
            낼("모르는 깃발: %s (쓸 수 있는 깃발: --서식 · --기간 · --덧명세 · %s)" % (a, " · ".join(깃발)))
            return 1
        else:
            자리.append(a)
            i += 1
    if 서식길 is not None and 서식길 not in 서식길들:
        낼("--서식 의 값 「%s」 을 모른다(%s)" % (서식길, " · ".join(서식길들)))
        return 1
    if not 3 <= len(자리) <= 4:
        낼(__doc__)
        return 1
    낼곳, 지도곳 = 자리[2], (자리[3] if len(자리) > 3 else None)
    앞것 = {p: os.path.getmtime(p) for p in (낼곳, 지도곳) if p and os.path.exists(p)}

    def 멈춤(오류목록, 머리="오류"):
        알림찍기(오류목록, 머리, 보기=8, 낼=낼)
        낼("파일을 내지 않았다")
        남은 = [p for p, t in 앞것.items() if os.path.exists(p) and os.path.getmtime(p) == t]
        if 남은:      # 앞서 지은 파일이 그 자리에 남아 있다 — 이번에 지은 것으로 잘못 알지 않게 알린다
            낼("낼 자리에 앞서 지은 파일이 남아 있다(이번에 지은 것이 아니다): %s" % " · ".join(
                "%s (%s)" % (p, datetime.datetime.fromtimestamp(앞것[p]).strftime("%Y-%m-%d %H:%M:%S")) for p in 남은))
        return 1

    def 한건(종류, 설명):
        return [{"종류": 종류, "시트": None, "자리": None, "설명": 설명}]

    try:
        배 = None
        if 자리[1] != "같은배치":
            try:
                with open(자리[1], encoding="utf-8") as f:
                    배 = json.load(f)
            except OSError as e:
                return 멈춤(한건("배치 읽기", "배치 파일을 읽을 수 없다: %s — %s" % (자리[1], e.strerror or e)))
            except ValueError as e:
                return 멈춤(한건("배치 읽기", "배치 파일의 JSON 문법 오류: %s — %s" % (os.path.basename(자리[1]), e)))
        if 서식길 is None:      # 안 주면 배치의 「서식길」(납품 배치는 표준), 배치에도 없으면 옛
            서식길 = (배.get("서식길") if isinstance(배, dict) else None) or "옛"
            if 서식길 not in 서식길들:
                return 멈춤(한건("배치", "배치의 서식길 「%s」 을 모른다(%s)" % (서식길, " · ".join(서식길들))))
        명 = 명세읽기(자리[0], 옛서식=(서식길 == "옛"), 덧파일=덧, 기간=기간)
        if 배 is None:
            배 = 같은배치(명)
        결 = 짓기(명, 배, 낼곳, 지도곳, 서식길=서식길, 이름불일치허용=깃발["--이름경고허용"],
                합계범위승인=깃발["--합계범위승인"], 못박은열허용=깃발["--못박은열허용"])
    except 배치오류 as e:
        return 멈춤(e.오류목록)
    except Exception as e:      # 예상하지 못한 오류 — 트레이스백 대신 한 줄로 알린다(--추적 이면 트레이스백도)
        if 깃발["--추적"]:
            import traceback
            traceback.print_exc()
        return 멈춤(한건("안에서 난 오류", "%s: %s — 명세나 배치의 꼴이 틀렸을 수 있다(자리를 찾으려면 --추적)" % (type(e).__name__, str(e)[:300])))
    위험 = [w for w in 결["경고"] if w["종류"] in 위험경고]
    낼("지었다: %s · 경고 %d건(위험 %d건) · 짝 범위 %s%s" % (
        낼곳, len(결["경고"]), len(위험), json.dumps(결["짝"], ensure_ascii=False),
        " · 다른 시트로 옮긴 줄 %d" % 결["옮긴 줄"] if 결["옮긴 줄"] else ""))
    if 결["경고"]:
        알림찍기(결["경고"], "경고", 낼=낼)
    if 위험 and not 깃발["--경고허용"]:
        낼("위험한 경고가 있다 — 내용을 확인한다(확인했으면 --경고허용). 종료 코드 2")
        return 2
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(명령줄(sys.argv[1:]))

# -*- coding: utf-8 -*-
"""합성통합문서 — 스캐폴드에 없는 참조 유형(열 전체·행 전체·정의된 이름·배열 수식·조건부 서식·INDIRECT …)을 담은 작은 통합문서.

시험 4(문법 왕복)와 시험 6(합성 통합문서 옮겨 짓기)이 쓴다. 원형의 시험 마에서 가져왔다.
"""
import datetime

import openpyxl
from openpyxl.styles import PatternFill, Font
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.formula import ArrayFormula
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.comments import Comment

자료, 계산, 민 = "1. 자료", "2. 계산's", "Plain"

# 계산 시트 B열에 넣을 수식(A열에는 무엇을 보는지 적는다)
수식들 = [
    ("칸 하나", "='1. 자료'!B5"),
    ("절대·혼합", "='1. 자료'!$B5+'1. 자료'!B$5+'1. 자료'!$B$5"),
    ("범위(여러 행)", "=SUM('1. 자료'!B2:B11)"),
    ("범위(여러 행·열)", "=SUM('1. 자료'!B2:C4)"),
    ("범위(같은 행)", "=SUM('1. 자료'!B3:C3)"),
    ("열 전체", "=SUM('1. 자료'!B:B)"),
    ("열 전체(절대·여러 열)", "=SUM('1. 자료'!$B:$C)"),
    ("행 전체", "=SUM('1. 자료'!3:5)"),
    ("행 전체(절대)", "=SUM('1. 자료'!$3:$3)"),
    ("정의된 이름(칸)", "=세율*100"),
    ("정의된 이름(범위)", "=SUM(자료범위)"),
    ("INDEX", "=INDEX('1. 자료'!B2:B11,3)"),
    ("MATCH", "=MATCH(7,'1. 자료'!B2:B11,0)"),
    ("INDEX+MATCH", "=INDEX('1. 자료'!C2:C11,MATCH(\"다\",'1. 자료'!A2:A11,0))"),
    ("CHOOSE", "=CHOOSE(2,'1. 자료'!B2,'1. 자료'!B3,'1. 자료'!B4)"),
    ("VLOOKUP", "=VLOOKUP(\"다\",'1. 자료'!A2:C11,2,FALSE)"),
    ("OFFSET", "=OFFSET('1. 자료'!B2,3,0)"),
    ("INDIRECT", "=INDIRECT(\"'1. 자료'!B5\")"),
    ("ROW", "=ROW('1. 자료'!B5)"),
    ("COLUMN", "=COLUMN('1. 자료'!B5)"),
    ("ADDRESS", "=ADDRESS(ROW('1. 자료'!B5),2)"),
    ("문자열 속 좌표", "=\"B5 는 \"&'1. 자료'!B5&\" (자료!B5, 12번 30행)\""),
    ("따옴표 없는 시트", "=Plain!A1*2"),
    ("같은 시트", "=SUM(B2:B3)+B$2"),
    ("소문자·공백", "= sum( b2:b3 ) + 1"),
    ("배열 상수", "=SUM({1,2,3})"),
    ("오류 상수", "=IFERROR(#N/A,1)"),
    ("등록부 밖의 줄", "=N('1. 자료'!B20)"),
    ("여러 시트 참조(못 바꿈)", "=SUM('1. 자료:Plain'!E3)"),
    ("시트 이름 속 작은따옴표", "='2. 계산''s'!B2+1"),
]
# 옮기면 값이 달라지는 것이 맞는 줄 — 틀로 못 바꾸는 것들(명세추출이 목록으로 알린다)
못바꾸는줄 = {"INDIRECT", "ROW", "COLUMN", "ADDRESS", "여러 시트 참조(못 바꿈)"}


def 합성(경로):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 자료
    ws.append(["이름", "수량", "단가", None, "세율"])
    for i, 글 in enumerate("가나다라마바사아자차", 1):
        ws.append([글, i, i * 10])
    ws["E2"] = 0.22
    ws["E3"] = 5
    ws["A12"] = "=이것은 글"
    ws["A12"].data_type = "s"                     # 「=」로 시작하지만 수식이 아닌 글
    ws["D2"] = datetime.datetime(2026, 6, 30)
    ws["D3"] = True
    ws["A1"].font = Font(bold=True, color="FFFFFF")
    ws["A1"].fill = PatternFill("solid", start_color="2E75B6", end_color="2E75B6")
    ws["B2"].comment = Comment("메모 한 줄", "시험")
    ws.merge_cells("F2:G4")                       # 여러 줄 병합
    ws["F2"] = "병합"
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["C"].hidden = True
    ws.row_dimensions[6].hidden = True
    ws.row_dimensions[8].height = 30
    ws.freeze_panes = "B2"
    ws.conditional_formatting.add("B2:B11", CellIsRule(operator="greaterThan", formula=["$E$3"],
                                                       fill=PatternFill("solid", start_color="FFC7CE", end_color="FFC7CE")))
    ws.conditional_formatting.add("C2:C11", FormulaRule(formula=["$B2>AVERAGE($B$2:$B$11)"],
                                                        font=Font(bold=True, color="C00000")))
    dv = DataValidation(type="list", formula1="$A$2:$A$4", allow_blank=True)
    dv.add("H2:H5")
    ws.add_data_validation(dv)
    dv2 = DataValidation(type="list", formula1='"기말,기중"', allow_blank=True)
    dv2.add("I2")
    dv2.add("I4:I5")
    ws.add_data_validation(dv2)
    ws.page_setup.orientation = "landscape"

    wc = wb.create_sheet(계산)
    wc["A1"], wc["B1"] = "무엇을", "수식"
    for i, (이름, 식) in enumerate(수식들, 2):
        wc.cell(i, 1, 이름)
        wc.cell(i, 2, 식)
    wc["D2"] = ArrayFormula("D2:D4", "='1. 자료'!B2:B4*2")   # 배열 수식

    wp = wb.create_sheet(민)
    wp["A1"] = 21
    wp["B1"] = "='2. 계산''s'!B2"
    wp["E3"] = 1
    wb.defined_names["세율"] = DefinedName("세율", attr_text="'1. 자료'!$E$2")
    wb.defined_names["자료범위"] = DefinedName("자료범위", attr_text="'1. 자료'!$B$2:$B$11")
    wb.save(경로)

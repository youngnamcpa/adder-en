# -*- coding: utf-8 -*-
"""함수표확인 — 공통.새함수(2007년 표준 뒤에 나온 함수 표)가 이 컴퓨터의 엑셀과 맞는지 엑셀에게 물어본다.

뒤에 나온 함수는 xlsx 에 「_xlfn.」 접두와 함께 적혀야 엑셀이 안다(접두 없이 적히면 #NAME?). 짓기는 수식 글을 낼 때
이 표에 든 이름 앞에 접두를 붙인다(공통.새함수접두). 표가 틀리면 — 표에 없는 새 함수는 「모르는 함수」로 막히고,
표에 잘못 든 옛 함수에는 쓸데없는 접두가 붙는다. 그래서 표를 엑셀에 견준다:

  함수 이름마다 엑셀에 수식을 적어(=이름(A1,…)) 저장한 뒤, 파일에 적힌 글(엑셀이 붙인 접두)을 읽는다.
    · 표의 이름: 엑셀이 「_xlfn.」(SORT · FILTER 는 「_xlfn._xlws.」)을 붙여 저장해야 한다 = 새함수접두 가 내는 글과 같아야 한다
    · 2007년 표준의 이름(openpyxl 의 FORMULAE) 몇 개: 접두 없이 저장돼야 한다
    · 표에 없는 이름(오타): 엑셀도 모른다(#NAME?)

엑셀은 win32com 의 DispatchEx 로 따로 띄운 것만 쓰고, 자기가 띄운 것만 끝낸다. 시험 6 이 함께 돌린다.

쓰기:  python 함수표확인.py [<낼 xlsx>]
"""
import sys
import os

import openpyxl

from 공통 import 새함수, 새함수접두, 못쓰는함수, _엑셀함수

옛함수보기 = ("IFERROR", "SUMIFS", "MEDIAN", "NETWORKDAYS.INTL", "WORKDAY.INTL", "ISO.CEILING", "COUNTIFS", "AVERAGEIF")
없는함수보기 = ("SUMM", "IFNAA")


def 확인(낼곳):
    """→ {"엑셀 판", "본 함수 수", "틀린 것": […], "엑셀이 수식을 받지 않은 것": […]}"""
    import win32com.client
    낼곳 = os.path.abspath(낼곳)
    이름들 = sorted(새함수) + list(옛함수보기) + list(없는함수보기)
    적은 = {}
    엑셀 = win32com.client.DispatchEx("Excel.Application")      # 따로 띄운 엑셀
    try:
        엑셀.Visible = False
        엑셀.DisplayAlerts = False
        판 = "%s (빌드 %s)" % (엑셀.Version, 엑셀.Build)
        책 = 엑셀.Workbooks.Add()
        try:
            ws = 책.Worksheets(1)
            ws.Range("A1").Value = 1
            for 줄, 이름 in enumerate(이름들, 3):
                ws.Cells(줄, 1).Value = 이름
                for n in range(0, 8):       # 인자 수를 늘려 가며 엑셀이 받는 꼴을 찾는다(인자는 A1 칸 · 숫자 · 글)
                    for 인자 in ((["$A$1"] * n, ["1"] * n, ['"a"'] * n) if n else ([],)):
                        식 = "=%s(%s)" % (이름, ",".join(인자))
                        try:
                            ws.Cells(줄, 2).Formula = 식
                            적은[이름] = (줄, 식)
                            break
                        except Exception:
                            pass
                    if 이름 in 적은:
                        break
            if os.path.exists(낼곳):
                os.remove(낼곳)
            os.makedirs(os.path.dirname(낼곳), exist_ok=True)
            책.SaveAs(낼곳, FileFormat=51)
        finally:
            책.Close(SaveChanges=False)       # 내가 연 것만 닫는다
    finally:
        엑셀.Quit()                           # 내가 띄운 엑셀만 끝낸다
        del 엑셀
    wf = openpyxl.load_workbook(낼곳).active
    wv = openpyxl.load_workbook(낼곳, data_only=True).active
    틀린, 못적은 = [], []
    for 이름 in 이름들:
        if 이름 not in 적은:
            못적은.append(이름)
            continue
        줄, 식 = 적은[이름]
        저장 = wf.cell(줄, 2).value
        저장 = getattr(저장, "text", 저장)
        값 = wv.cell(줄, 2).value
        if 이름 in 새함수:
            기대 = 새함수접두(식)[0]
            if 저장 != 기대:
                틀린.append({"함수": 이름, "까닭": "엑셀이 저장한 글이 짓기가 내는 글과 다르다", "엑셀": 저장, "짓기": 기대})
            elif 값 == "#NAME?":
                틀린.append({"함수": 이름, "까닭": "엑셀이 모르는 함수다(#NAME?)", "엑셀": 저장})
        elif 이름 in 옛함수보기:
            if 저장 != 식 or 새함수접두(식)[0] != 식 or 이름 not in _엑셀함수:
                틀린.append({"함수": 이름, "까닭": "2007년 표준의 함수인데 접두가 붙는다", "엑셀": 저장, "짓기": 새함수접두(식)[0]})
        elif 값 != "#NAME?":
            틀린.append({"함수": 이름, "까닭": "없는 함수인데 엑셀이 안다", "엑셀": 저장, "값": 값})
    return {"엑셀 판": 판, "본 함수 수": len(이름들), "표의 함수 수": len(새함수), "손 수식으로 못 적는 함수": sorted(못쓰는함수),
            "틀린 것": 틀린, "엑셀이 수식을 받지 않은 것": 못적은, "통과": not 틀린 and not 못적은}


if __name__ == "__main__":
    import json
    sys.stdout.reconfigure(encoding="utf-8")
    결 = 확인(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "산출", "함수표확인.xlsx"))
    print(json.dumps(결, ensure_ascii=False, indent=1))
    sys.exit(0 if 결["통과"] else 1)

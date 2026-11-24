# -*- coding: utf-8 -*-
"""명세추출 — xlsx 를 읽어 「명세」(행 등록부 + 칸 내용 + 수식 틀)를 낸다.

쓰기:  python 명세추출.py <읽을 xlsx> <명세 폴더>

내는 파일
  책.json                시트 순서·이름, 정의된 이름, 서식 표(글꼴·채움·테두리·맞춤·보호·숫자 서식), 기본 글꼴, 테마
  S01.json … S13.json    시트마다: 속성, 열 등록부, 행 등록부(행 ID·옛 행·높이·이름·칸), 병합, 목록 유효성, 조건부 서식
  목록_좌표의존함수.json  INDIRECT·OFFSET·INDEX·MATCH·CHOOSE … 가 쓰인 곳 전부
  목록_못바꾼참조.json    틀로 못 바꾼 참조(원문 그대로 둔 것)
  목록_글속좌표.json      글·수식 속 문자열에 든 좌표처럼 보이는 낱말(틀은 안 바꾼다)
  행등록부.tsv            사람이 읽는 행 등록부(행 ID · 시트 · 옛 행 · 이름 · 수식 칸 수 · 상수 칸 수)
  요약.json              수

읽기만 한다. 읽은 xlsx 는 고치지 않는다.
"""
import sys
import os
import json
import datetime
from collections import Counter, OrderedDict

import openpyxl
from openpyxl.formula import Tokenizer
from openpyxl.worksheet.formula import ArrayFormula, DataTableFormula
from openpyxl.cell.cell import MergedCell
from openpyxl.xml.functions import tostring

from 공통 import (시트ID, 행ID, 열글자, 수식틀, 글속좌표, 서식글, 좌표의존함수, 못바꾸는함수)


def _속성(객체, 이름들):
    return {k: getattr(객체, k) for k in 이름들 if getattr(객체, k, None) not in (None, "", False)}


def 추출(xlsx, 폴더):
    os.makedirs(폴더, exist_ok=True)
    wb = openpyxl.load_workbook(xlsx)  # 수식은 글로, 값 캐시는 안 읽는다
    이름sid, 순서 = {}, []
    for i, ws in enumerate(wb.worksheets, 1):
        sid = 시트ID(ws.title, i)
        if sid in 이름sid.values():
            raise SystemExit("시트 ID 가 겹친다: %s (%s)" % (sid, ws.title))
        이름sid[ws.title] = sid
        순서.append(sid)
    정의된이름 = set(wb.defined_names.keys())
    for ws in wb.worksheets:
        정의된이름 |= set(ws.defined_names.keys())

    # 서식 표 — 같은 서식은 한 번만 싣는다
    부품 = {k: OrderedDict() for k in ("글꼴", "채움", "테두리", "맞춤", "보호", "숫자서식")}
    조합, 조합키 = [], {}

    def 서식번호(칸):
        키 = tuple(칸._style)
        if 키 in 조합키:
            return 조합키[키]
        글 = 서식글(칸)
        줄 = [부품[k].setdefault(글[k], len(부품[k])) for k in ("글꼴", "채움", "테두리", "맞춤", "보호", "숫자서식")]
        줄.append(1 if 글["따옴표머리"] else 0)
        조합키[키] = len(조합)
        조합.append(줄)
        return 조합키[키]

    쓰임, 못바꿈, 글좌표 = [], [], []
    등록부 = ["행ID\t시트\t옛행\t이름(B열)\t수식 칸 수\t상수 칸 수"]
    수 = Counter()
    참조종류 = Counter()

    def 틀만들기(수식, sid, rid, 열):
        조각 = 수식틀(수식, sid, 이름sid, 정의된이름, 쓰임, [sid, rid, 열])
        for p in 조각:
            if isinstance(p, dict):
                참조종류[p["k"] + ("!" if p.get("x") else "")] += 1
                if p["k"] == "x":
                    못바꿈.append({"자리": [sid, rid, 열], "원문": p["t"], "사유": p["why"]})
        # 수식 속 문자열 상수에 든 좌표 글
        for t in Tokenizer(수식).items:
            if t.type == "OPERAND" and t.subtype == "TEXT":
                좌 = 글속좌표(t.value)
                if 좌:
                    글좌표.append({"자리": [sid, rid, 열], "곳": "수식 속 문자열", "낱말": 좌[:8], "글": t.value[:80]})
        return 조각

    for ws in wb.worksheets:
        sid = 이름sid[ws.title]
        명 = OrderedDict()
        명["id"] = sid
        명["옛이름"] = ws.title
        뷰 = ws.sheet_view
        틀 = None
        if ws.freeze_panes:
            from openpyxl.utils.cell import coordinate_from_string
            열, 행 = coordinate_from_string(ws.freeze_panes)
            틀 = {"행": 행ID(sid, 행), "열": 열}
        명["속성"] = {
            "탭색": ws.sheet_properties.tabColor.rgb if ws.sheet_properties.tabColor is not None else None,
            "눈금선": 뷰.showGridLines, "확대": 뷰.zoomScale, "틀고정": 틀,
            "기본행높이": ws.sheet_format.defaultRowHeight, "기본열폭": ws.sheet_format.defaultColWidth,
            "기본글자폭": ws.sheet_format.baseColWidth,
            "상태": ws.sheet_state,
            "인쇄": {"방향": ws.page_setup.orientation, "용지": ws.page_setup.paperSize,
                   "폭맞춤": ws.page_setup.fitToWidth, "높이맞춤": ws.page_setup.fitToHeight,
                   "쪽맞춤": bool(ws.sheet_properties.pageSetUpPr and ws.sheet_properties.pageSetUpPr.fitToPage),
                   "제목행": ws.print_title_rows, "제목열": ws.print_title_cols,
                   "영역": ws.print_area if ws.print_area else None,
                   "바닥글": ws.oddFooter.center.text if ws.oddFooter and ws.oddFooter.center else None},
        }
        최대행, 최대열 = ws.max_row, ws.max_column

        # 열 등록부 — 열 ID 는 옛 열 글자. 묶여 적힌 폭(min~max)은 풀어 적는다.
        열폭 = {}
        for 키, d in ws.column_dimensions.items():
            for n in range(d.min or 열번호_(키), (d.max or 열번호_(키)) + 1):
                열폭[열글자(n)] = _속성(d, ("width", "hidden", "outlineLevel", "collapsed"))
                최대열 = max(최대열, n) if d.width or d.hidden else 최대열
        명["열"] = [dict(id=열글자(n), **열폭.get(열글자(n), {})) for n in range(1, 최대열 + 1)]

        # 행 등록부
        칸들 = {}
        for (r, c), 칸 in ws._cells.items():
            칸들.setdefault(r, {})[c] = 칸
        행들 = []
        for r in range(1, 최대행 + 1):
            rid = 행ID(sid, r)
            줄 = OrderedDict(id=rid, 옛행=r)
            if r in ws.row_dimensions:
                d = ws.row_dimensions[r]
                줄.update(_속성(d, ("height", "hidden", "outlineLevel", "collapsed")))
            b = 칸들.get(r, {}).get(2)
            if b is not None and isinstance(b.value, str):
                줄["이름"] = "(수식)" if b.data_type == "f" else b.value
            칸명세 = OrderedDict()
            for c in sorted(칸들.get(r, {})):
                칸 = 칸들[r][c]
                열 = 열글자(c)
                한 = OrderedDict()
                v = 칸.value
                if isinstance(칸, MergedCell):
                    if 칸.has_style:
                        한["s"] = 서식번호(칸)
                        한["병합속"] = 1
                        칸명세[열] = 한
                    continue
                if isinstance(v, ArrayFormula):
                    한["f"] = 틀만들기(v.text if v.text.startswith("=") else "=" + v.text, sid, rid, 열)
                    한["배열"] = 틀만들기("=" + v.ref, sid, rid, 열)
                    수["배열 수식"] += 1
                    수["수식"] += 1
                elif isinstance(v, DataTableFormula):
                    한["x"] = "데이터 표 — 원형은 안 옮긴다"
                    못바꿈.append({"자리": [sid, rid, 열], "원문": "데이터 표(%s)" % v.ref, "사유": "데이터 표 수식"})
                    수["데이터 표"] += 1
                elif 칸.data_type == "f":
                    한["f"] = 틀만들기(v, sid, rid, 열)
                    수["수식"] += 1
                    # 왕복 확인: 토큰을 이어 붙이면 원문과 같아야 한다
                    if "=" + "".join(t.value for t in Tokenizer(v).items) != v:
                        수["토큰 왕복 불일치"] += 1
                elif v is None:
                    pass
                elif isinstance(v, bool):
                    한["v"] = v
                    수["상수(참거짓)"] += 1
                elif isinstance(v, (int, float)):
                    한["v"] = v
                    수["상수(숫자)"] += 1
                elif isinstance(v, datetime.datetime):
                    한["v"], 한["t"] = v.isoformat(), "dt"
                    수["상수(날짜)"] += 1
                elif isinstance(v, datetime.date):
                    한["v"], 한["t"] = v.isoformat(), "d"
                    수["상수(날짜)"] += 1
                elif isinstance(v, datetime.time):
                    한["v"], 한["t"] = v.isoformat(), "tm"
                    수["상수(날짜)"] += 1
                elif isinstance(v, str):
                    한["v"] = v
                    if 칸.data_type == "e":
                        한["t"] = "e"
                    elif v.startswith("="):
                        한["t"] = "s"  # 「=」로 시작하는 글(수식 아님)
                    수["글"] += 1
                    좌 = 글속좌표(v)
                    if 좌:
                        글좌표.append({"자리": [sid, rid, 열], "곳": "글 칸", "낱말": 좌[:8], "글": v[:80]})
                else:
                    한["v"], 한["t"] = str(v), "?"
                    수["모르는 값 종류"] += 1
                if 칸.has_style:
                    한["s"] = 서식번호(칸)
                if 칸.comment is not None:
                    한["메모"] = {"글": 칸.comment.text, "쓴이": 칸.comment.author}
                    수["메모"] += 1
                if 칸.hyperlink is not None:
                    한["링크"] = {"target": 칸.hyperlink.target, "location": 칸.hyperlink.location}
                    수["링크"] += 1
                if 한:
                    칸명세[열] = 한
            줄["칸"] = 칸명세
            행들.append(줄)
        명["행"] = 행들

        # 병합
        명["병합"] = [{"r": 행ID(sid, m.min_row), "c": 열글자(m.min_col),
                     "r2": 행ID(sid, m.max_row), "c2": 열글자(m.max_col)} for m in ws.merged_cells.ranges]
        수["병합"] += len(명["병합"])

        # 목록 유효성
        유효 = []
        for dv in ws.data_validations.dataValidation:
            한 = _속성(dv, ("type", "operator", "allow_blank", "showErrorMessage", "showInputMessage",
                          "showDropDown", "error", "errorTitle", "errorStyle", "prompt", "promptTitle"))
            한["범위"] = [{"r": 행ID(sid, g.min_row), "c": 열글자(g.min_col),
                         "r2": 행ID(sid, g.max_row), "c2": 열글자(g.max_col)} for g in dv.sqref.ranges]
            for k in ("formula1", "formula2"):
                f = getattr(dv, k)
                if f is not None:
                    # "a,b,c" 꼴 목록은 글이라 그대로 남는다. 칸을 가리키면 틀이 된다.
                    한[k] = 틀만들기("=" + f, sid, 한["범위"][0]["r"], 한["범위"][0]["c"])
            유효.append(한)
        명["유효성"] = 유효
        수["목록 유효성"] += len(유효)

        # 조건부 서식 — 규칙은 XML 글로, 수식은 틀로
        조건 = []
        for cf in ws.conditional_formatting:
            범위 = [{"r": 행ID(sid, g.min_row), "c": 열글자(g.min_col),
                    "r2": 행ID(sid, g.max_row), "c2": 열글자(g.max_col)} for g in cf.sqref.ranges]
            for 규칙 in cf.rules:
                한 = {"범위": 범위,
                     "규칙": tostring(규칙.to_tree("cfRule")).decode("utf-8"),
                     "수식": [틀만들기("=" + f, sid, 범위[0]["r"], 범위[0]["c"]) for f in (규칙.formula or [])],
                     "서식": tostring(규칙.dxf.to_tree("dxf")).decode("utf-8") if 규칙.dxf is not None else None}
                조건.append(한)
        명["조건부서식"] = 조건
        수["조건부 서식"] += len(조건)

        # 시트 안에서만 쓰는 정의된 이름
        명["정의된이름"] = [{"이름": k, "틀": 틀만들기("=" + d.attr_text, sid, None, None)}
                       for k, d in ws.defined_names.items()]

        with open(os.path.join(폴더, sid + ".json"), "w", encoding="utf-8") as f:
            json.dump(명, f, ensure_ascii=False, separators=(",", ":"))
        for 줄 in 행들:   # 사람이 읽는 행 등록부 한 줄
            이름 = " ".join((줄.get("이름") or "").split())
            등록부.append("\t".join([줄["id"], ws.title, str(줄["옛행"]), 이름,
                                    str(sum(1 for 한 in 줄["칸"].values() if "f" in 한)),
                                    str(sum(1 for 한 in 줄["칸"].values() if "v" in 한))]))
        수["시트"] += 1
        수["행"] += len(행들)

    with open(os.path.join(폴더, "행등록부.tsv"), "w", encoding="utf-8-sig") as f:
        f.write("\n".join(등록부) + "\n")

    책 = OrderedDict()
    책["원본"] = os.path.basename(xlsx)        # 파일 이름만 싣는다(절대 경로를 실으면 폴더가 바뀔 때마다 명세가 달라진다)
    책["시트순서"] = 순서
    책["시트이름"] = {v: k for k, v in 이름sid.items()}
    책["정의된이름"] = [{"이름": k, "틀": 수식틀("=" + d.attr_text, None, 이름sid, 정의된이름)}
                   for k, d in wb.defined_names.items() if d.attr_text]
    책["서식표"] = {k: list(v.keys()) for k, v in 부품.items()}
    책["서식조합"] = 조합
    # 통합문서의 기본 글꼴 — 서식 없는 칸(값만 있는 칸)이 보이는 글꼴이다. 옛 서식 길로 지을 때 그대로 옮긴다
    책["기본글꼴"] = tostring(wb._fonts[0].to_tree("font")).decode("utf-8") if len(wb._fonts) else None
    책["계산"] = {"fullCalcOnLoad": True}
    with open(os.path.join(폴더, "책.json"), "w", encoding="utf-8") as f:
        json.dump(책, f, ensure_ascii=False, separators=(",", ":"))
    if wb.loaded_theme:
        with open(os.path.join(폴더, "테마.xml"), "wb") as f:
            f.write(wb.loaded_theme)

    # 좌표 의존 함수 — 함수별 수와 쓰인 곳
    함수수 = Counter(u["함수"] for u in 쓰임)
    with open(os.path.join(폴더, "목록_좌표의존함수.json"), "w", encoding="utf-8") as f:
        json.dump({"함수별": {k: {"수": n, "설명": 좌표의존함수[k], "틀로못바꿈": k in 못바꾸는함수}
                           for k, n in 함수수.most_common()},
                   "쓰인곳": 쓰임}, f, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(폴더, "목록_못바꾼참조.json"), "w", encoding="utf-8") as f:
        json.dump(못바꿈, f, ensure_ascii=False, indent=1)
    with open(os.path.join(폴더, "목록_글속좌표.json"), "w", encoding="utf-8") as f:
        json.dump(글좌표, f, ensure_ascii=False, separators=(",", ":"))
    요약 = {"원본": os.path.basename(xlsx), "수": dict(수), "참조": dict(참조종류),
          "서식 조합 수": len(조합), "좌표 의존 함수": dict(함수수),
          "틀로 못 바꾸는 함수가 쓰인 수": sum(n for k, n in 함수수.items() if k in 못바꾸는함수),
          "못 바꾼 참조": len(못바꿈), "글 속 좌표(칸 수)": len(글좌표),
          "정의된 이름": sorted(정의된이름)}
    with open(os.path.join(폴더, "요약.json"), "w", encoding="utf-8") as f:
        json.dump(요약, f, ensure_ascii=False, indent=1)
    return 요약


def 열번호_(글자):
    from openpyxl.utils import column_index_from_string
    return column_index_from_string(글자)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    요약 = 추출(sys.argv[1], sys.argv[2])
    print(json.dumps(요약, ensure_ascii=False, indent=1))

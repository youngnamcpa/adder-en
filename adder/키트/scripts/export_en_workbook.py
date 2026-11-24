# -*- coding: utf-8 -*-
"""Convert an ADDER DCF workbook (.xlsx) into a 100% American English 17-sheet workbook.

Translates:
  - All 17 sheet tab names (`1. Value_per_share` .. `17. Driver_map_and_evidence`)
  - Cross-sheet formula references, string literals, `LEFT(...)` character counts, and wildcards
  - Conditional formatting formulas and data-validation dropdown lists (`Bear,Base,Bull`, etc.)
  - All scaffold labels, check descriptions, compositional cost/segment labels, and dynamic SEC source tags
  - Per-share USD formatting (`#,##0.00;[Red](#,##0.00);-`)
  - Optional background Excel COM recalculation + personal document property scrubbing
"""
from __future__ import annotations
import argparse
import io
import json
import os
import re
import shutil
import sys
import tempfile

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLE_PATH = os.path.join(HERE, "en_workbook_bundle.json")

KO_RE = re.compile(r"[가-힣「」『』]")
ROMAN_RE = re.compile(r"^([IVXLCDM]+)\.\s+(.+)$")
LEFT_RE = re.compile(r'LEFT\(([^()]*(?:\([^()]*\)[^()]*)*),(\d+)\)(\s*(?:<>|=)\s*)"([^"]*)"')

# Dynamic phrase replacements for auto-generated SEC/market source notes
DYNAMIC_SUBS = [
    ("[공시]", "[Filing]"),
    ("[관측]", "[Observed]"),
    ("[계산]", "[Calculated]"),
    ("[판단]", "[Judgment]"),
    ("[회사 주장]", "[Company claim]"),
    ("[외부 추정]", "[External estimate]"),
    ("[법령]", "[Statute]"),
    ("[기본값]", "[Default]"),
    ("접수)", "filed)"),
    (" 접수", " filed"),
    ("(유동)", "(current)"),
    ("(비유동)", "(non-current)"),
    ("유동 · 선순위 무담보채", "current; senior unsecured notes"),
    ("비유동 · 선순위 무담보채", "non-current; senior unsecured notes"),
    ("(감가상각 포함형)", "(incl. depreciation)"),
    ("(감가상각 제외형)", "(ex-depreciation)"),
    ("(비지배지분 없음)", "(no non-controlling interest)"),
    ("재무상태표", "Balance Sheet"),
    ("연결재무상태표", "Consolidated Balance Sheets"),
    ("연결손익계산서", "Consolidated Statements of Income"),
    ("손익계산서", "Income Statement"),
    ("연결현금흐름표", "Consolidated Statements of Cash Flows"),
    ("현금흐름표", "Cash Flow Statement"),
    ("발행 · 유통 주식수", "issued & outstanding shares"),
    ("유통주식수", "shares outstanding"),
    ("발행주식총수", "total shares issued"),
    ("자기주식수", "treasury shares"),
    ("천 주 → 주", "thousand shares to shares"),
    ("백만 주 → 주", "million shares to shares"),
    ("천 주", " thousand shares"),
    ("백만 주", " million shares"),
    ("백만달러", "USD mn"),
    ("억 달러", "00M USD"),
    ("미국 재무부", "US Treasury"),
    ("일별 수익률", "daily par yield curve"),
    ("전년 동기 대비", "YoY"),
    ("전년 대비", "YoY"),
    ("유형 감가상각", "PP&E depreciation"),
    ("무형 상각", "intangible amortization"),
    ("이자부부채 없음", "no other interest-bearing debt"),
    ("기업어음", "commercial paper"),
    ("선순위 무담보채", "senior unsecured notes"),
    ("미지급 법인세", "income taxes payable"),
    ("리스부채", "lease liabilities"),
    ("선수수익", "deferred revenue"),
    ("무형자산", "intangible assets"),
    ("유형자산", "PP&E"),
    ("비유동", "non-current"),
    ("유동", "current"),
    ("포함", "incl."),
    ("제외", "excl."),
    ("약 ", "approx. "),
    ("없음", "none"),
    ("같음", "matched"),
    ("표시와", "reported"),
]


def load_bundle():
    with io.open(BUNDLE_PATH, encoding="utf-8") as f:
        return json.load(f)


def clean_punctuation(s: str) -> str:
    s = s.replace("「", '"').replace("」", '"').replace("『", '"').replace("』", '"')
    s = s.replace(" · ", "; ")
    s = re.sub(r"([0-9,]+)\s*명\b", r"\1 employees", s)
    s = re.sub(r"([0-9,]+)\s*주\b", r"\1 shares", s)
    return s


def translate_text(s: str, B: dict) -> str:
    if s in B["values"]:
        return B["values"][s]
    if s in B["units"]:
        return B["units"][s]
    if s in B["cells"]:
        return B["cells"][s]

    m = ROMAN_RE.match(s)
    if m and m.group(2) in B["section_titles"]:
        return f"{m.group(1)}. {B['section_titles'][m.group(2)]}"

    for ko_suf, en_suf in B["suffix_rules"]:
        if s.endswith(ko_suf):
            stem = s[: -len(ko_suf)]
            return translate_text(stem, B) + en_suf

    for ko_pre, en_pre in B["prefix_rules"]:
        if s.startswith(ko_pre):
            rest = s[len(ko_pre) :]
            return en_pre + translate_text(rest, B)

    if KO_RE.search(s):
        out = s
        for ko_tok, en_tok in DYNAMIC_SUBS:
            if ko_tok in out:
                out = out.replace(ko_tok, en_tok)
        out = clean_punctuation(out)
        return out
    return s


def replace_sheet_refs(formula: str, sheets_map: dict) -> str:
    for ko, en in sorted(sheets_map.items(), key=lambda kv: -len(kv[0])):
        if ko != en:
            formula = formula.replace(f"'{ko}'!", f"'{en}'!")
    return formula


def translate_formula(f: str, where: str | None, B: dict, lit_map: dict) -> str:
    if where and where in B["fx_cells"]:
        patch = B["fx_cells"][where]
        if patch["찾기"] in f:
            f = f.replace(patch["찾기"], patch["바꾸기"])
    f = replace_sheet_refs(f, B["sheets"])

    def left_fix(m):
        expr, _n, op, lit = m.group(1), m.group(2), m.group(3), m.group(4)
        if KO_RE.search(lit) and lit in lit_map:
            en = lit_map[lit]
            return f'LEFT({expr},{len(en)}){op}"{en}"'
        return m.group(0)

    f = LEFT_RE.sub(left_fix, f)

    def lit_sub(m):
        s = m.group(1)
        if not KO_RE.search(s):
            return m.group(0)
        if s in lit_map:
            en = lit_map[s].replace('"', '""')
            return f'"{en}"'
        en_dyn = translate_text(s, B).replace('"', '""')
        return f'"{en_dyn}"'

    return re.sub(r'"((?:[^"]|"")*)"', lit_sub, f)


def scrub_openpyxl_props(wb):
    wb.properties.creator = "ADDER Valuation Kit"
    wb.properties.lastModifiedBy = ""
    wb.properties.company = ""
    wb.properties.manager = ""
    wb.properties.description = ""
    wb.properties.keywords = ""
    wb.properties.subject = ""
    wb.properties.category = ""


def recalc_with_excel(xlsx_path: str) -> bool:
    if os.name != "nt":
        return False
    try:
        import pythoncom
        import win32com.client
    except ImportError:
        return False

    abs_p = os.path.abspath(xlsx_path)
    pythoncom.CoInitialize()
    app = None
    try:
        app = win32com.client.DispatchEx("Excel.Application")
        app.Visible = False
        app.DisplayAlerts = False
        wb = app.Workbooks.Open(abs_p)
        try:
            wb.RemovePersonalInformation = True
        except Exception:
            pass
        for prop in ("Author", "Last Author", "Manager", "Company", "Comments", "Keywords", "Subject", "Category"):
            try:
                wb.BuiltinDocumentProperties(prop).Value = "ADDER Valuation Kit" if prop == "Author" else ""
            except Exception:
                pass
        app.CalculateFullRebuild()
        wb.Save()
        wb.Close(SaveChanges=False)
        return True
    except Exception:
        return False
    finally:
        if app is not None:
            try:
                app.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()


def convert_workbook(src_path: str, dst_path: str, recalc: bool = True) -> dict:
    B = load_bundle()
    lit_map = dict(B["values"])
    lit_map.update(B["wildcards"])
    lit_map.update(B["fx_literals"])

    wb = openpyxl.load_workbook(src_path)
    n_cells = 0
    n_formulas = 0

    for ws in wb.worksheets:
        orig_sheet = ws.title
        for row in ws.iter_rows():
            for c in row:
                v = c.value
                if not isinstance(v, str):
                    continue
                coord_key = f"{orig_sheet}!{c.coordinate}"
                if v.startswith("="):
                    nv = translate_formula(v, coord_key, B, lit_map)
                    if nv != v:
                        c.value = nv
                        n_formulas += 1
                elif coord_key in B["universal_cell_labels"]:
                    c.value = B["universal_cell_labels"][coord_key]
                    n_cells += 1
                elif KO_RE.search(v):
                    nv = translate_text(v, B)
                    if nv != v:
                        c.value = nv
                        n_cells += 1

        # Conditional formatting formulas
        for cf in ws.conditional_formatting:
            for rule in cf.rules:
                if rule.formula:
                    rule.formula = [
                        translate_formula("=" + x, None, B, lit_map)[1:] if (KO_RE.search(x) or "'" in x) else x
                        for x in rule.formula
                    ]

        # Data validation lists & formulas
        if ws.data_validations and ws.data_validations.dataValidation:
            for dv in ws.data_validations.dataValidation:
                for attr in ("formula1", "formula2"):
                    fval = getattr(dv, attr, None)
                    if not isinstance(fval, str):
                        continue
                    if fval.startswith('"') and fval.endswith('"'):
                        items = fval[1:-1].split(",")
                        new_items = [B["values"].get(it.strip(), translate_text(it.strip(), B)) for it in items]
                        setattr(dv, attr, '"' + ",".join(new_items) + '"')
                    elif KO_RE.search(fval) or "'" in fval:
                        prefix = "=" if fval.startswith("=") else ""
                        body = fval[1:] if prefix else fval
                        setattr(dv, attr, prefix + translate_formula("=" + body, None, B, lit_map)[1:])

    # Apply USD cents formatting on per-share summary cells when currency is USD
    s12 = wb["12. 가정_시나리오"] if "12. 가정_시나리오" in wb.sheetnames else None
    curr = str(s12["D5"].value or "").upper() if s12 is not None else "USD"
    if curr in ("USD", "달러", "$", ""):
        fmt = B["cents_format"]["형식"]
        for spec in B["cents_format"]["범위"]:
            sh_ko, rng = spec.split("!")
            if sh_ko in wb.sheetnames:
                ws_t = wb[sh_ko]
                cells_rng = ws_t[rng]
                if isinstance(cells_rng, tuple):
                    for r_tup in cells_rng:
                        for cell in (r_tup if isinstance(r_tup, tuple) else (r_tup,)):
                            cell.number_format = fmt
                else:
                    cells_rng.number_format = fmt

    # Rename all 17 worksheet tabs to English
    for ws in wb.worksheets:
        if ws.title in B["sheets"]:
            ws.title = B["sheets"][ws.title]

    # Update defined names / print areas if they reference old Korean sheet names
    if wb.defined_names:
        for dn in wb.defined_names.values():
            if isinstance(dn.attr_text, str):
                dn.attr_text = replace_sheet_refs(dn.attr_text, B["sheets"])

    scrub_openpyxl_props(wb)
    os.makedirs(os.path.dirname(os.path.abspath(dst_path)), exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".xlsx", prefix="en_wb_")
    os.close(tmp_fd)
    try:
        wb.save(tmp_path)
        recalced = recalc_with_excel(tmp_path) if recalc else False
        shutil.move(tmp_path, dst_path)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    # Count any remaining Korean characters
    wb_check = openpyxl.load_workbook(dst_path)
    rem_ko = 0
    for ws in wb_check.worksheets:
        if KO_RE.search(ws.title):
            rem_ko += 1
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and KO_RE.search(c.value):
                    rem_ko += 1

    return {
        "translated_cells": n_cells,
        "translated_formulas": n_formulas,
        "excel_recalculated": recalced,
        "remaining_korean_cells": rem_ko,
        "output": os.path.abspath(dst_path),
    }


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Convert an ADDER DCF workbook into 100% American English.")
    ap.add_argument("src", help="Input .xlsx workbook")
    ap.add_argument("dst", nargs="?", default=None, help="Output .xlsx workbook (defaults to overwriting src)")
    ap.add_argument("--no-recalc", action="store_true", help="Skip Excel COM recalculation")
    args = ap.parse_args(argv)

    dst = args.dst or args.src
    info = convert_workbook(args.src, dst, recalc=not args.no_recalc)
    print(
        f"English workbook ready: {info['output']} "
        f"(cells: {info['translated_cells']}, formulas: {info['translated_formulas']}, "
        f"recalc: {info['excel_recalculated']}, remaining Korean cells: {info['remaining_korean_cells']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

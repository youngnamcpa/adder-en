# -*- coding: utf-8 -*-
"""Generate a 100% American English Valuation Memorandum (.md & .html) from verified ADDER outputs.

Replaces the Korean-only `레터.py` / `레터게이트.py` pipeline in ADDER (English Edition) so
every valuation produces both:
  1) A 17-sheet English Excel workbook (`<Company>_DCF.xlsx`), and
  2) A clean, non-advisory English Valuation Memorandum (`Letter_<TICKER>.md` & `.html`)
     tied directly to the engine's exact Bear / Base / Bull calculations.
"""
from __future__ import annotations
import argparse
import datetime
import html
import importlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
KO_SCRIPTS = os.path.join(KIT, "스크립트")
if KO_SCRIPTS not in sys.path:
    sys.path.insert(0, KO_SCRIPTS)


def _fmt_num(x, decimals=2, prefix=""):
    if x is None or isinstance(x, bool):
        return "—"
    try:
        v = float(x)
        return f"{prefix}{v:,.{decimals}f}"
    except (TypeError, ValueError):
        return str(x)


def _fmt_pct(x, decimals=1):
    if x is None or isinstance(x, bool):
        return "—"
    try:
        return f"{float(x) * 100.0:.{decimals}f}%"
    except (TypeError, ValueError):
        return str(x)


def build_english_memo(assump_path: str, workbook_path: str | None = None, out_md: str | None = None) -> tuple[str, str]:
    with io.open(assump_path, encoding="utf-8") as f:
        A = json.load(f)

    calc = importlib.import_module("엔진.계산")
    scen_map = [("비관", "Bear"), ("기준", "Base"), ("낙관", "Bull")]
    R = {ko: calc.계산(A, ko) for ko, _ in scen_map}

    meta = A.get("메타") or {}
    company = meta.get("회사명") or meta.get("종목명") or "Target Company"
    ticker = meta.get("종목코드") or meta.get("티커") or ""
    val_date = meta.get("평가기준일") or datetime.date.today().isoformat()
    fin_date = meta.get("재무기준일") or val_date
    currency = meta.get("통화") or "USD"
    unit_raw = meta.get("단위") or "USD mn"
    unit_map = {"백만달러": "USD mn", "달러": "USD", "원": "KRW", "백만원": "KRW mn"}
    unit_en = unit_map.get(unit_raw, unit_raw)
    sym = "$" if currency in ("USD", "달러", "$") else f"{currency} "

    active_ko = (A.get("스위치") or {}).get("적용시나리오") or "기준"
    active_en = dict(scen_map).get(active_ko, "Base")
    Ra = R[active_ko]
    P = Ra["기간"]
    fy_last = P["자리"].get("FY실적.끝") or ""
    fc_end = P["자리"].get("예측.끝") or ""

    # Close price at valuation date if present in 관측 / 원천
    close_px = None
    obs = A.get("관측") or {}
    for k_cand in ("종가", "평가기준일종가", "주가"):
        if isinstance(obs.get(k_cand), (int, float)):
            close_px = float(obs[k_cand])
            break
    if close_px is None:
        s13 = (Ra.get("1.요약") or {})
        if isinstance(s13.get("현재주가"), (int, float)):
            close_px = float(s13["현재주가"])

    # Narrative block (if written by Claude in English)
    narr = A.get("Narrative") if isinstance(A.get("Narrative"), dict) else {}
    wb_name = os.path.basename(workbook_path) if workbook_path else f"{company.replace(' ', '_')}_DCF.xlsx"

    lines = []
    title_ticker = f" ({ticker})" if ticker else ""
    lines.append(f"# DCF Valuation Memorandum — {company}{title_ticker}")
    lines.append("")
    lines.append(f"- **Valuation Date**: {val_date}  |  **Financial Data Date**: {fin_date}")
    lines.append(f"- **Active Scenario**: {active_en}  |  **Reporting Unit**: {unit_en} (per-share figures in {currency})")
    lines.append(f"- **Companion 17-Sheet Model**: `{wb_name}`")
    lines.append("")

    # 1. Executive Summary Table
    lines.append("## 1. Scenario Valuation Summary")
    lines.append("")
    lines.append("| Metric | Bear Case | Base Case | Bull Case |")
    lines.append("|---|---:|---:|---:|")
    vps_row = [f"**{_fmt_num(R[ko]['요약'].get('주당가치'), 2, sym)}**" for ko, _ in scen_map]
    opv_row = [_fmt_num(R[ko]['요약'].get('영업가치'), 1) for ko, _ in scen_map]
    eqv_row = [_fmt_num(R[ko]['요약'].get('주주가치'), 1) for ko, _ in scen_map]
    wacc_row = [_fmt_pct(R[ko]['요약'].get('영구기간WACC'), 2) for ko, _ in scen_map]
    tg_row = [_fmt_pct(R[ko]['요약'].get('영구성장률'), 2) for ko, _ in scen_map]
    opm_row = [_fmt_pct(R[ko]['요약'].get('영구기간영업이익률'), 1) for ko, _ in scen_map]
    roic_row = [_fmt_pct(R[ko]['요약'].get('영구ROIC'), 1) for ko, _ in scen_map]

    lines.append(f"| **Fair Value per Share ({currency})** | {vps_row[0]} | {vps_row[1]} | {vps_row[2]} |")
    if close_px is not None:
        lines.append(f"| Market Close ({val_date}) | {_fmt_num(close_px, 2, sym)} | {_fmt_num(close_px, 2, sym)} | {_fmt_num(close_px, 2, sym)} |")
    lines.append(f"| Operating Value ({unit_en}) | {opv_row[0]} | {opv_row[1]} | {opv_row[2]} |")
    lines.append(f"| Equity Value ({unit_en}) | {eqv_row[0]} | {eqv_row[1]} | {eqv_row[2]} |")
    lines.append(f"| Terminal WACC | {wacc_row[0]} | {wacc_row[1]} | {wacc_row[2]} |")
    lines.append(f"| Terminal Growth Rate (*g*) | {tg_row[0]} | {tg_row[1]} | {tg_row[2]} |")
    lines.append(f"| Terminal Operating Margin | {opm_row[0]} | {opm_row[1]} | {opm_row[2]} |")
    lines.append(f"| Terminal ROIC | {roic_row[0]} | {roic_row[1]} | {roic_row[2]} |")
    lines.append("")

    # 2. Core Thesis & Narrative
    if any(isinstance(v, str) and v.strip() for v in narr.values()):
        lines.append("## 2. Business Narrative & Key Drivers")
        lines.append("")
        for key in ("정체성", "한줄", "우위", "그러나", "가격"):
            txt = (narr.get(key) or "").strip()
            if txt and "{" not in txt:
                lines.append(f"- {txt}")
        lines.append("")

    # 3. Value Bridge (Base / Active Case)
    lines.append(f"## 3. Enterprise-to-Equity Value Bridge ({active_en} Case)")
    lines.append("")
    s_sum = Ra.get("요약") or {}
    lines.append(f"- **Forecast Horizon**: `{fy_last}` reported anchor through `{fc_end}`, followed by steady-state terminal period.")
    lines.append(f"- **Operating Value**: {_fmt_num(s_sum.get('영업가치'), 1)} ({unit_en})")
    lines.append(f"- **Equity Value at Valuation Date**: {_fmt_num(s_sum.get('주주가치'), 1)} ({unit_en})")
    lines.append(f"- **Implied Fair Value per Share**: **{_fmt_num(s_sum.get('주당가치'), 2, sym)}**")
    lines.append("")

    # 4. How to Inspect & Stress-Test the Workbook
    lines.append("## 4. Auditing & Updating Assumptions in Excel")
    lines.append("")
    lines.append(f"Open `{wb_name}` in Microsoft Excel:")
    lines.append("1. **`1. Value_per_share`**: Review the scenario bridge, implied multiples, and key driver summary.")
    lines.append("2. **`12. Assumptions_scenarios`**: Every editable forecast input sits on this single sheet alongside its `[Filing]` / `[Calculated]` / `[Observed]` / `[Judgment]` basis. Switch cell `D12` between `Bear`, `Base`, and `Bull` to watch the entire model recalculate.")
    lines.append("3. **`14. Sensitivity` & `15. Checks`**: Inspect two-way WACC/growth/margin grids, Reverse DCF market-implied expectations, and automated integrity/completeness checks.")
    lines.append("")
    lines.append("---")
    lines.append("*Disclaimer: Generated with ADDER (English Edition). This memorandum records how public SEC filings and explicit user assumptions map into discounted cash flows. It does not recommend buying, selling, or holding any security.*")
    lines.append("")

    md_content = "\n".join(lines)
    out_md_path = out_md or os.path.join(os.path.dirname(os.path.abspath(assump_path)), f"Letter_{ticker or company.replace(' ', '_')}.md")
    with io.open(out_md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(md_content)

    # Simple clean HTML companion
    out_html_path = os.path.splitext(out_md_path)[0] + ".html"
    html_body = (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        f"<title>DCF Valuation Memorandum — {html.escape(company)}</title>"
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Georgia,serif;"
        "max-width:860px;margin:40px auto;padding:0 24px;line-height:1.6;color:#1a1e29}"
        "h1,h2{color:#091e5a}table{border-collapse:collapse;width:100%;margin:16px 0}"
        "th{background:#091e5a;color:#fff;padding:8px 12px;text-align:right}"
        "th:first-child,td:first-child{text-align:left}"
        "td{border-bottom:1px solid #cbd5e8;padding:8px 12px;text-align:right}"
        "code{background:#f3f5f9;padding:2px 5px;border-radius:3px}</style></head><body><pre style='white-space:pre-wrap;font-family:inherit'>"
        + html.escape(md_content)
        + "</pre></body></html>\n"
    )
    with io.open(out_html_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(html_body)

    return out_md_path, out_html_path


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Build a 100% English Valuation Memorandum (.md and .html).")
    ap.add_argument("assumptions", help="Path to 가정_<TICKER>.json")
    ap.add_argument("--workbook", default=None, help="Path to finished English .xlsx workbook")
    ap.add_argument("-o", "--out", default=None, help="Output markdown path (default: Letter_<TICKER>.md)")
    args = ap.parse_args(argv)

    md_p, html_p = build_english_memo(args.assumptions, args.workbook, args.out)
    print(f"English valuation memorandum ready: {md_p} (HTML: {html_p})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

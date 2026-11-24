# ADDER (English Edition) — DCF Stock Valuation Kit for Claude Code

 Companion valuation kit for ***Value Your Own Stocks: Calculate Any Stock's Fair Value Yourself with an AI-Powered DCF Model* (Second Edition)** by **Youngnam Kim**.

ADDER runs inside **Claude Code** on your computer. It gathers primary **SEC EDGAR** filings (`10-K`, `10-Q`, `8-K` earnings releases, XBRL `companyfacts`), **US Treasury** par yield curves, **Bureau of Labor Statistics** wage data, and **Damodaran** risk-premium datasets to build an auditable **17-sheet English Excel DCF workbook** (`1. Value_per_share` through `17. Driver_map_and_evidence`).

ADDER never picks a target price on its own: every reported figure carries its SEC accession number and filing date, every forecast input sits on a single sheet (`12. Assumptions_scenarios`) with its basis and historical/peer range, and every economic judgment stays in your hands.

Version `1.2.0` · `2026-11-24`

---

## Requirements

- **Claude Code** installed on your computer (terminal CLI, desktop app Code tab, or VS Code extension; browser-only cloud sessions cannot load local plugins)
- **Python 3.11 or later** ([python.org](https://www.python.org/) — on Windows, check **"Add python.exe to PATH"** during installation)
- **Git** ([Git for Windows](https://git-scm.com/download/win) on Windows; preinstalled or via Xcode Command Line Tools on macOS)
- **Microsoft Excel** (recommended for live formula editing and automatic COM recalculation; without Excel, `formulas` / `openpyxl` still builds the complete linked `.xlsx` workbook)

---

## Installation (Two Commands in Claude Code)

Open Claude Code and enter these two commands in order:

```text
/plugin marketplace add youngnamcpa/adder-en
/plugin install adder@adder-en
```

---

## Quick Start: From Empty Folder to Your First Valuation

1. **Create an empty folder** for the company you want to value (for example, `Documents/ADDER/NVIDIA`) and open Claude Code in that folder.
2. **Unpack the kit**:
   ```text
   /adder:init
   ```
   Confirm when asked to install the Python packages (`requests`, `openpyxl`, `xlrd`).
3. **Reopen Claude Code in the same folder** (so `CLAUDE.md` loads at session start) and run the environment check:
   ```text
   /preflight
   ```
4. **Store your SEC EDGAR contact email** (one-time setup — no registration or API key required; SEC fair-access rules simply ask for a contact email in request headers):
   ```bash
   python -X utf8 scripts/preflight.py --save SEC_CONTACT_EMAIL
   ```
   Reopen your terminal and Claude Code, then run `/preflight` once more to confirm `⑥ SEC EDGAR connection` reads `ok`.
5. **Run a valuation**:
   ```text
   Value NVIDIA for me
   ```
   ADDER launches its parallel research lines, stops once with the key economic assumption choices that require human judgment, and produces the finished **17-sheet English `.xlsx` workbook** (`<Company>_DCF.xlsx`) with built-in integrity, completeness, and review checks on `15. Checks`.

---

## Reference Workbook Included

- [`examples/NVIDIA_DCF_T1118_EN.xlsx`](examples/NVIDIA_DCF_T1118_EN.xlsx) — Complete 17-sheet English DCF valuation workbook from *Value Your Own Stocks (Second Edition)* (valuation date November 18, 2026; financial data date July 26, 2026).

### The 17 Sheets Produced by ADDER

| Tab | Sheet Name | Role |
|---:|---|---|
| 1 | `1. Value_per_share` | Executive summary, Bear/Base/Bull value bridge, and key drivers |
| 2 | `2. DCF` | FCFF projection, mid-year discounting, terminal value, and equity roll-forward |
| 3 | `3. WACC_working` | Unlevered peer beta, synthetic credit spread, cost of equity, and WACC |
| 4 | `4. Sales_working` | Segment revenue builds (volume x price, capacity, or market-arrival paths) |
| 5 | `5. COGS_working` | Cost of revenue drivers and depreciation allocation |
| 6 | `6. SG&A_working` | R&D, SG&A, and operating expense schedules |
| 7 | `7. Payroll_working` | Headcount, compensation, and functional payroll allocation |
| 8 | `8. CAPEX_working` | Maintenance CAPEX, growth CAPEX, PP&E, and intangibles roll-forward |
| 9 | `9. NWC_working` | Working capital days (DSO, DIO, DPO), deferred revenue, and NWC investment |
| 10 | `10. Tax_working` | Effective vs. marginal tax rate convergence, R&D amortization, and NOLs |
| 11 | `11. NOA_working` | Non-operating assets, debt, leases, and equity bridge classifications |
| 12 | `12. Assumptions_scenarios` | **Single input sheet** — Bear/Base/Bull assumptions, basis, and sources |
| 13 | `13. Source_financials` | Reported 10-K/10-Q statements with SEC accession numbers |
| 14 | `14. Sensitivity` | Two-way WACC/growth/margin grids, Reverse DCF, and scenario waterfall |
| 15 | `15. Checks` | Automated Integrity, Completeness, and Review checks |
| 16 | `16. Narrative_and_numbers` | Damodaran-style story-to-numbers bridge and 3P plausibility checks |
| 17 | `17. Driver_map_and_evidence` | Cost/revenue driver map, empirical base-rate ranges, and sensitivity weights |

---

## Updating & Uninstalling

- **Update plugin & working folder**:
  1. `/plugin marketplace update adder-en`
  2. Inside each company working folder: `/adder:update` (updates kit scripts while preserving your assumptions, SEC filings, and `.xlsx` workbooks)
- **Optional US Empirical Base-Rate Panel** (SEC Financial Statement Data Sets):
  ```bash
  python -X utf8 scripts/base_rates.py --download --country US
  ```
- **Uninstall plugin**:
  ```text
  /plugin uninstall adder@adder-en
  ```

---

## License

Created by **Youngnam Kim** and licensed under the **[PolyForm Noncommercial License 1.0.0](LICENSE.md)**. Required attribution and commercial licensing information are in **[NOTICE.md](NOTICE.md)**.

- **Permitted noncommercial use**: Personal learning, academic research, and **analyzing investments for your own personal account**.
- **Separate commercial license required**: Paid advisory services, paid investment research/newsletters, paid courses, or institutional/corporate work (inquire via GitHub Issues).

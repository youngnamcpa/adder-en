---
name: letter
description: Build the English DCF Valuation Memorandum (Letter_<TICKER>.md and .html) after the 17-sheet English Excel workbook has closed cleanly.
---

# English Valuation Memorandum (`scripts/build_en_letter.py`)

> **IMPORTANT (ADDER English Edition)**: Do **NOT** run `스크립트/레터.py`, `레터원고.py`, `레터교열.py`, or `레터게이트.py` — those scripts enforce Korean prose endings (`~습니다`) for the Korean edition.

Instead, once `워크북마감.py`, `자체검사.py`, and `대조.py` have verified the model and exported `<Company>_DCF.xlsx`:

1. Run the English memorandum builder:
   ```bash
   python -X utf8 scripts/build_en_letter.py 가정_<TICKER>.json --workbook <Company>_DCF.xlsx -o Letter_<TICKER>.md
   ```
2. If the user asks for deeper qualitative commentary on business drivers, peer selection, or scenario signposts, expand `Letter_<TICKER>.md` directly in clear, non-advisory **American English** while citing exact figures from `<Company>_DCF.xlsx` and never recommending buy, sell, or hold.

---
name: init
description: Unpack the ADDER (English Edition) DCF valuation kit into the current working folder — run once in a new empty folder after installing the plugin. Use for "init ADDER", "start ADDER", "unpack ADDER kit", or "set up DCF folder".
---

# /adder:init — Unpack the ADDER Kit into Your Working Folder

ADDER runs inside a dedicated working folder for each company you value. Your rules file (`CLAUDE.md`), downloaded SEC filings (`_raw/`), assumptions JSON, and the 17-sheet English Excel workbook all live inside that folder so plugin cache updates never overwrite your work.

1. **Check the current directory.** An empty folder created for one company is ideal (for example, `Documents/ADDER/NVIDIA`). If the current directory already contains unrelated project files, recommend creating a dedicated empty folder before proceeding.
2. **Unpack the kit.** Run the command below and display its output **verbatim**:

   ```bash
   python -X utf8 "${CLAUDE_PLUGIN_ROOT}/키트/scripts/init_kit.py" --target .
   ```

   - If it reports that a kit is already unpacked in this folder, ask whether the user wants to update it and use `/adder:update` instead.
   - If Python is not found, stop and ask the user to install **Python 3.11 or later** from `python.org` (on Windows, check **"Add python.exe to PATH"** during installation).
3. **Offer to install Python packages.** Ask the user before running:

   ```bash
   python -m pip install -r requirements.txt
   ```

   Never install packages without asking first.
4. **Prompt to reopen Claude Code.** Tell the user:
   > "Reopen Claude Code in this folder so `CLAUDE.md` is loaded at session startup, then type `/preflight`."

Do not ask for the SEC contact email during `/adder:init`; `/preflight` checks it and guides the user safely.

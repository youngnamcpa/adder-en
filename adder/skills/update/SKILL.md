---
name: update
description: Update an unpacked ADDER working folder to the newly installed plugin version while keeping your assumptions, SEC filings, and Excel workbooks intact. Use for "update ADDER kit" or "/adder:update".
---

# /adder:update — Update an Unpacked ADDER Working Folder

Updating the plugin cache does not automatically overwrite files inside existing company folders. Run `/adder:update` inside a working folder to refresh only ADDER's kit files while preserving all of your valuation data.

1. **Preview changes first** and display the output **verbatim**:

   ```bash
   python -X utf8 "${CLAUDE_PLUGIN_ROOT}/키트/scripts/init_kit.py" --target . --update --dry-run
   ```

2. **Apply the update** once the user confirms:

   ```bash
   python -X utf8 "${CLAUDE_PLUGIN_ROOT}/키트/scripts/init_kit.py" --target . --update
   ```

   - Modified kit files from the prior version are backed up under `_raw/_before_update_<old_version>_<date>/`.
   - Your own deliverables (assumptions JSON, `.xlsx` workbooks, valuation letters, and `_raw/` filings) are never touched.
3. **Prompt to reopen Claude Code.** Tell the user:
   > "Reopen Claude Code in this folder to load the updated `CLAUDE.md` rules, then run `/preflight` once."

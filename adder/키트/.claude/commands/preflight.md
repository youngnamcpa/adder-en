---
description: Run the ADDER (English Edition) preflight check — Python, packages, Excel/formula engine, SEC EDGAR contact email, SEC connection, US base-rate panel, write access, and subagent permissions (10 US checks).
argument-hint: "[--offline]"
---

# /preflight — Check Your Environment Before the First Valuation

1. Run `python -X utf8 scripts/preflight.py $ARGUMENTS` in the current working folder and display the output table **verbatim**.
2. Walk through any items listed under **"Next"** one at a time:
   - **⑤ SEC contact (`SEC_CONTACT_EMAIL`)**: Ask the user to run `python -X utf8 scripts/preflight.py --save SEC_CONTACT_EMAIL` **in their own terminal** (input is hidden and stored in their OS environment variables, never echoed in chat history).
   - If the user already pasted their email address in chat, pipe it through standard input (`stdin`) to `python -X utf8 scripts/preflight.py --save SEC_CONTACT_EMAIL` and **never repeat the address** — confirm only that it was saved.
3. After storing `SEC_CONTACT_EMAIL`, ask the user to reopen their terminal and Claude Code so the updated environment variable is picked up, then run `/preflight` once more to confirm `⑥ SEC EDGAR connection` reads `ok`.
4. Do not start a valuation while any required item (`① Python`, `② requests, openpyxl`, `⑤ SEC contact`, `⑨ Write access`) is missing.

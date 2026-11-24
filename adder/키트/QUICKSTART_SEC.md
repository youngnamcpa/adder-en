# Setting Up Your SEC EDGAR Contact Email (`QUICKSTART_SEC.md`)

To value US-listed companies, ADDER fetches original `10-K`, `10-Q`, `8-K`, and XBRL `companyfacts` filings directly from the U.S. Securities and Exchange Commission's **EDGAR** system (`data.sec.gov` and `www.sec.gov`).

## 1. No API Key or Registration Needed
- The SEC does **not** issue API keys or require account registration.
- Under SEC EDGAR fair-access guidelines, automated scripts must declare a `User-Agent` header containing a contact email address (for example, `ADDER/1.2.0 (your.name@example.com)`), rate-limited well below 10 requests per second.

## 2. How to Store `SEC_CONTACT_EMAIL` Privately
Open your own terminal inside your working folder and run:

```bash
python -X utf8 scripts/preflight.py --save SEC_CONTACT_EMAIL
```

- Type or paste your email address and press **Enter** (characters are hidden as you type).
- On **Windows**, ADDER saves `SEC_CONTACT_EMAIL` in your **User Environment Variables**.
- On **macOS / Linux**, ADDER appends `export SEC_CONTACT_EMAIL=...` to `~/.zshrc` or `~/.bashrc` (with `0600` permissions).
- Close and reopen your terminal and Claude Code, then run `/preflight` to verify that both **⑤ SEC contact** and **⑥ SEC EDGAR connection** read `ok`.

## 3. Recommended Claude Code Subagent Permissions
ADDER launches five parallel research subagents (Chapter 4 of *Value Your Own Stocks*) to cross-check SEC filings, revenue drivers, peer betas, external constraints, and cost behavior. Because background subagents cannot display interactive approval pop-ups, allowing `python`, `WebSearch`, and `WebFetch` in your Claude Code settings (`~/.claude/settings.json` under `permissions.allow`) prevents subagents from stalling on permission prompts.

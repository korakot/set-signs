# set-signs
Daily scraper for SET / mai stock warning signs (SP, CB, CS, NC, NP, ...).

`scrape.py` opens each sector index page on set.or.th
(`https://www.set.or.th/th/market/index/{set,mai}/{sector}`) in headless
Chromium via [Playwright](https://playwright.dev/python/), scrolls until every
symbol is rendered, and reads each `a.text-symbol` (`data-symbol`) and its
`div.item-sign` badges. Output is `set_signs.json`: a JSON array with one
`{"symbol": ..., "signs": [...]}` object per line, so diffs stay readable.

If any page fails after retries or returns 0 symbols, the script exits
non-zero and leaves `set_signs.json` untouched.

## Run locally

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium   # add --with-deps on a fresh Linux box
python scrape.py
```

Uses the full Chromium build (`channel="chromium"`); no API key needed
(previously used the paid Zyte API).

GitHub Actions (`.github/workflows/scrape.yml`) runs daily at 11:00 UTC
(18:00 Bangkok) and commits changes to `set_signs.json`.

Last updated: 2026-10-09

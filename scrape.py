"""Scrape SET / mai stock warning signs (SP, CB, CS, NC, ...) from set.or.th.

Loads each sector index page in headless Playwright Chromium, scrolls until
all symbols are rendered, and writes set_signs.json (one object per line).
Exits non-zero, without touching set_signs.json, if any page fails or is empty.
"""
import json
import sys
import time

from playwright.sync_api import sync_playwright

MARKETS = ["set", "mai"]
SECTORS = "agro consump fincial indus propcon resourc service tech".split()
URL = "https://www.set.or.th/th/market/index/{market}/{sector}"
OUT = "set_signs.json"
RETRIES = 3          # 1 try + 2 retries
DELAY = 2.0          # polite pause between pages (s)

EXTRACT_JS = """els => els.map(a => ({
    symbol: a.getAttribute('data-symbol'),
    signs: Array.from(a.querySelectorAll('div.item-sign')).map(d => d.textContent.trim()),
}))"""


def scroll_to_bottom(page, max_rounds=30):
    """Scroll until the number of a.text-symbol stops growing."""
    prev = -1
    stable = 0
    for _ in range(max_rounds):
        count = page.locator("a.text-symbol").count()
        if count == prev:
            stable += 1
            if stable >= 2:
                break
        else:
            stable = 0
        prev = count
        page.mouse.wheel(0, 20000)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(700)


def get_all_signs(page, market, sector):
    url = URL.format(market=market, sector=sector)
    last_err = None
    for attempt in range(1, RETRIES + 1):
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=90_000)
            if resp is not None and resp.status >= 400:
                raise RuntimeError(f"HTTP {resp.status} ({page.title()!r})")
            page.wait_for_selector("a.text-symbol", state="attached", timeout=45_000)
            scroll_to_bottom(page)
            rows = page.eval_on_selector_all("a.text-symbol", EXTRACT_JS)
            if not rows:
                raise RuntimeError("0 symbols")
            return [{"symbol": r["symbol"], "signs": r["signs"]} for r in rows]
        except Exception as e:  # noqa: BLE001
            last_err = e
            print(f"  {market}/{sector} attempt {attempt} failed: {e}", flush=True)
            time.sleep(DELAY * attempt)
    raise RuntimeError(f"{market}/{sector}: giving up after {RETRIES} attempts: {last_err}")


def write_json(items, path=OUT):
    with open(path, "w", encoding="utf-8") as f:
        f.write("[\n")
        for i, item in enumerate(items):
            comma = "," if i < len(items) - 1 else ""
            f.write(f"{json.dumps(item, ensure_ascii=False)}{comma}\n")
        f.write("]\n")


def main():
    all_signs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True, channel="chromium",
            args=["--disable-blink-features=AutomationControlled"])
        try:
            ctx = browser.new_context(locale="th-TH", viewport={"width": 1366, "height": 900})
            page = ctx.new_page()
            for market in MARKETS:
                for sector in SECTORS:
                    rows = get_all_signs(page, market, sector)
                    all_signs.extend(rows)
                    print(f"{market}/{sector}: {len(rows)}", flush=True)
                    time.sleep(DELAY)
        finally:
            browser.close()

    print(f"Total: {len(all_signs)}")
    write_json(all_signs)
    print(f"Saved to {OUT}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

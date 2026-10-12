"""Read back the filled title/desc from the Douyin detail page."""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = None
    for pg in ctx.pages:
        if "creator.douyin.com" in pg.url:
            page = pg
            break
    print("URL:", page.url)
    print("TITLE_INPUT:", repr(page.eval_on_selector(
        "input[placeholder*='标题'], textarea[placeholder*='标题']", "e => e.value")))
    print("DESC_TEXT:", repr(page.eval_on_selector(
        "div[contenteditable='true']", "e => e.innerText").strip()))
    print("PUBLISH_BTN:", [b.strip() for b in page.eval_on_selector_all(
        "button", "els => els.map(e => e.innerText).filter(t => t.includes('发布'))")])

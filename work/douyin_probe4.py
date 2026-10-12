"""Find the exact '放弃' clickable in the resume modal."""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from playwright.sync_api import sync_playwright

URL = "https://creator.douyin.com/creator-micro/content/upload"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = None
    for pg in ctx.pages:
        if "creator.douyin.com" in pg.url:
            page = pg
            break
    if page is None:
        page = ctx.new_page()
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(6000)

    for sel in ["text=继续编辑", "text=放弃", "button:has-text('放弃')",
                "[class*='modal'] button", "[class*='dialog'] button"]:
        try:
            loc = page.locator(sel)
            n = loc.count()
            print(f"{sel}: count={n}")
            for i in range(min(n, 3)):
                el = loc.nth(i)
                try:
                    print("   text=", repr(el.inner_text(timeout=1000)),
                          "visible=", el.is_visible())
                except Exception as e:
                    print("   err", e)
        except Exception as e:
            print(f"{sel}: ERR {e}")

"""Dump candidate modal buttons/dropzone on the Douyin upload page."""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
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

    res = page.evaluate("""() => {
      const btns = [];
      document.querySelectorAll("button, [role='button'], a").forEach(el => {
        const t = (el.innerText || '').trim();
        if (t && t.length < 20) {
          const r = el.getBoundingClientRect();
          btns.push({tag: el.tagName, cls: (el.className||'').toString().slice(0,60),
            text: t, rect: [r.x|0, r.y|0, r.width|0, r.height|0]});
        }
      });
      return btns;
    }""")
    for b in res:
        print(b)

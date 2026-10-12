"""Inspect the Douyin upload page file input + page state via CDP."""
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
    print("URL:", page.url)
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(6000)
    print("AFTER GOTO URL:", page.url)

    info = page.evaluate("""() => {
      const out = [];
      document.querySelectorAll("input[type='file']").forEach((el, i) => {
        const r = el.getBoundingClientRect();
        const cs = getComputedStyle(el);
        out.push({i, accept: el.accept, disabled: el.disabled,
          display: cs.display, visibility: cs.visibility, opacity: cs.opacity,
          rect: [r.x|0, r.y|0, r.width|0, r.height|0],
          parentDisplay: el.parentElement ? getComputedStyle(el.parentElement).display : null});
      });
      return out;
    }""")
    for it in info:
        print(it)
    body = page.inner_text("body")[:800]
    print("--- BODY ---")
    print(body)
    page.screenshot(path=str(REPO / "work" / "douyin_upload_probe.png"))
    print("SHOT:", REPO / "work" / "douyin_upload_probe.png")

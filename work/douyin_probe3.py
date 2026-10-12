"""Locate the '继续编辑?' modal and its clickable '放弃' element."""
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
      const out = [];
      const walk = (el) => {
        for (const c of el.children) {
          const t = (c.innerText || '').replace(/\\s+/g,'');
          if (t === '继续编辑放弃' || t === '放弃' || (t.includes('继续编辑') && t.includes('放弃'))) {
            out.push({tag:c.tagName, cls:(c.className||'').toString().slice(0,80),
              text:(c.innerText||'').slice(0,40),
              html: c.outerHTML.slice(0,500)});
          }
          walk(c);
        }
      };
      walk(document.body);
      return out;
    }""")
    for r in res[:10]:
        print(r)
        print("----")

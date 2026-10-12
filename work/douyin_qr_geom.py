"""Report QR element geometry + risk-control text on the Douyin login screen."""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
USER_DATA_DIR = REPO / "browser-data" / "douyin"
URL = "https://creator.douyin.com/creator-micro/content/upload"

RISK = ["异常登录", "异常", "风险", "请完成验证", "安全验证", "操作频繁", "请稍后再试", "验证码"]

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=str(USER_DATA_DIR), channel="chrome", headless=False,
        viewport={"width": 1920, "height": 1080},
        args=["--disable-blink-features=AutomationControlled"],
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(8000)

    print("VIEWPORT:", page.viewport_size)
    info = page.evaluate("""() => {
      const out = [];
      for (const c of document.querySelectorAll('canvas')) {
        const r = c.getBoundingClientRect();
        out.push({tag:'canvas', w:c.width, h:c.height, rect:[r.x|0,r.y|0,r.width|0,r.height|0]});
      }
      for (const i of document.querySelectorAll("img[src^='data:image']")) {
        const r = i.getBoundingClientRect();
        out.push({tag:'img', w:i.naturalWidth, h:i.naturalHeight, rect:[r.x|0,r.y|0,r.width|0,r.height|0]});
      }
      return out;
    }""")
    for it in info:
        print(it)

    body = page.inner_text("body")
    print("--- RISK SCAN ---")
    for h in RISK:
        print(f"{h}: {'YES' if h in body else 'no'}")

    ctx.close()

"""One-off diagnostic for the Douyin login/QR screen. Read-only: never logs in."""
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
USER_DATA_DIR = REPO / "browser-data" / "douyin"
SHOT = REPO / "work" / "douyin_login_debug.png"
URL = "https://creator.douyin.com/creator-micro/content/upload"

USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=str(USER_DATA_DIR),
        channel="chrome",
        headless=False,
        viewport={"width": 1920, "height": 1080},
        args=["--disable-blink-features=AutomationControlled", "--start-maximized"],
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.set_viewport_size({"width": 1920, "height": 1080})
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(8000)

    print("URL:", page.url)
    print("TITLE:", page.title())

    # QR candidates
    for sel in ["canvas", "img[src^='data:image']", "img[class*='qrcode']",
                "div[class*='qrcode']", "div[class*='qr']"]:
        try:
            n = page.locator(sel).count()
        except Exception:
            n = -1
        print(f"count[{sel}] = {n}")

    try:
        body = page.inner_text("body", timeout=5000)
    except Exception:
        body = ""
    print("--- BODY (first 1500) ---")
    print(body[:1500])
    print("--- /BODY ---")

    page.screenshot(path=str(SHOT), full_page=False)
    print("SHOT:", SHOT, SHOT.stat().st_size, "bytes")

    # keep window open briefly
    page.wait_for_timeout(3000)
    ctx.close()

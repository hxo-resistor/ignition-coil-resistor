"""Open Douyin creator login in a visible window and wait for the user to scan
the QR code. Polls for login state (upload input present / login panel gone).

Usage: python work/douyin_login.py
"""
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


def has_login_panel(page):
    try:
        if page.locator("text=扫码登录").count() > 0:
            return True
        if page.locator("input[type='file']").count() == 0 and \
           page.locator("div[class*='login']").count() > 0:
            return True
    except Exception:
        pass
    return False


def has_upload_ready(page):
    try:
        return page.locator("input[type='file']").count() > 0
    except Exception:
        return False


with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=str(USER_DATA_DIR), channel="chrome", headless=False,
        viewport={"width": 1920, "height": 1080},
        args=["--disable-blink-features=AutomationControlled", "--start-maximized"],
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.set_viewport_size({"width": 1920, "height": 1080})
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(6000)

    if "login" not in page.url and not has_login_panel(page) and has_upload_ready(page):
        print("[login] 已是登录态，会话已保存。")
        page.screenshot(path=str(SHOT))
        page.wait_for_timeout(2000)
        ctx.close()
        sys.exit(0)

    print("[login] 请用抖音APP扫描窗口中的二维码登录（最长等待 10 分钟）...")
    deadline = time.time() + 600
    while time.time() < deadline:
        try:
            if not has_login_panel(page) and has_upload_ready(page):
                print("[login] 登录成功！会话已保存到 browser-data/douyin")
                page.screenshot(path=str(SHOT))
                page.wait_for_timeout(3000)
                ctx.close()
                sys.exit(0)
        except Exception:
            pass
        page.wait_for_timeout(2000)

    print("[login] 超时，未检测到登录态。")
    page.screenshot(path=str(SHOT))
    ctx.close()
    sys.exit(1)

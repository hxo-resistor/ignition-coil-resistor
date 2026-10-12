"""Launch the user's real Chrome with a CDP debug port so Playwright can attach.

Why: Douyin's login (QR + face verification) is risk-controlled under Playwright,
so the user logs in manually in a normal Chrome, and tools/publish_douyin_cdp.py
attaches to that already-logged-in browser over CDP.

Uses a DEDICATED user-data-dir (browser-data/chrome-debug) so it never conflicts
with the user's everyday Chrome profile. First run: log in once, the profile keeps
the session.

Usage:
    python tools/launch_chrome_debug.py
"""
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent.parent
USER_DATA_DIR = REPO / "browser-data" / "chrome-debug"
PORT = 9222
START_URL = "https://creator.douyin.com/creator-micro/content/upload"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    str(Path.home() / "AppData/Local/Google/Chrome/Application/chrome.exe"),
]


def find_chrome():
    for c in CHROME_CANDIDATES:
        if Path(c).exists():
            return c
    return None


def main():
    chrome = find_chrome()
    if not chrome:
        print("[error] 未找到 Chrome，请确认已安装 Google Chrome。")
        return 1

    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        chrome,
        f"--remote-debugging-port={PORT}",
        f"--user-data-dir={USER_DATA_DIR}",
        "--no-first-run",
        "--no-default-browser-check",
        START_URL,
    ]
    print("[launch] Chrome:", chrome)
    print("[launch] 调试端口:", PORT)
    print("[launch] 用户数据目录:", USER_DATA_DIR)
    print("[launch] 打开:", START_URL)
    print()
    print("下一步：")
    print("  1) 在这个 Chrome 窗口里手动登录抖音创作者中心（扫码/人脸）")
    print("  2) 登录成功后保持窗口打开")
    print("  3) 另开终端运行: python tools/publish_douyin_cdp.py --dry-run ...")
    print()

    subprocess.Popen(cmd)
    print("[ok] Chrome 已启动（后台）。验证端口: 打开 http://localhost:%d/json/version" % PORT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

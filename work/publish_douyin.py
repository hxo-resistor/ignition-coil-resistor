"""Douyin (抖音创作者中心) video publisher via Playwright + persistent userDataDir.

Login state is kept in browser-data/douyin (relative to repo root).

Usage:
    python work/publish_douyin.py --video work/videos/xxx.mp4 \
        --title "标题" --desc "#标签1 #标签2" --no-headless
    python work/publish_douyin.py --video work/videos/xxx.mp4 \
        --title "标题" --desc "#标签1 #标签2" --dry-run
    python work/publish_douyin.py --list

Published URLs are appended to work/douyin_published.log.

Red lines:
  - dry-run only fills the form; it never clicks 发布.
  - Stop immediately on captcha / risk-control prompts.
"""
import argparse
import datetime as dt
import re
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

REPO = Path(__file__).resolve().parent.parent
USER_DATA_DIR = REPO / "browser-data" / "douyin"
VIDEOS_DIR = REPO / "work" / "videos"
LOG_FILE = REPO / "work" / "douyin_published.log"

UPLOAD_URL = "https://creator.douyin.com/creator-micro/content/upload"
MANAGE_URL = "https://creator.douyin.com/creator-micro/content/manage"

RISK_HINTS = [
    "验证码", "请完成验证", "安全验证", "操作频繁", "请稍后再试",
    "异常", "风险", "verify", "captcha",
]


def log_publish(video, title, url):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(f"{ts}\t{video}\t{title}\t{url}\n")
    print(f"[log] appended to {LOG_FILE}")


def first_visible(page, selectors, timeout=15000):
    deadline = time.time() + timeout / 1000
    while time.time() < deadline:
        for sel in selectors:
            try:
                loc = page.locator(sel).first
                if loc.count() and loc.is_visible():
                    return loc
            except Exception:
                continue
        time.sleep(0.4)
    return None


def check_risk(page):
    """Raise if a captcha / risk-control prompt is on screen."""
    try:
        body = page.inner_text("body", timeout=3000)
    except Exception:
        return
    low = body.lower()
    for hint in RISK_HINTS:
        if hint.lower() in low:
            raise RuntimeError(
                f"检测到风控/验证码提示（'{hint}'），立即停下，请手动处理后再运行。"
            )


def newest_video():
    if not VIDEOS_DIR.exists():
        return None
    vids = sorted(VIDEOS_DIR.glob("*.mp4"), key=lambda p: p.stat().st_mtime)
    return vids[-1] if vids else None


def _has_login_panel(page):
    """Douyin renders the login panel inline on the same upload URL (no redirect),
    so we must detect it by DOM, not by URL."""
    try:
        if page.locator("text=扫码登录").count() > 0:
            return True
        if page.locator("text=验证码登录").count() > 0:
            return True
        if page.locator("div[class*='login']").count() > 0 and \
           page.locator("input[type='file']").count() == 0:
            return True
    except Exception:
        pass
    return False


def _has_upload_ready(page):
    """Logged-in state: the upload input is present on the upload page."""
    try:
        return page.locator("input[type='file']").count() > 0
    except Exception:
        return False


def is_logged_in(page):
    """Load the upload page and check for the login panel vs the upload input."""
    try:
        page.goto(UPLOAD_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)
        if "login" in page.url or "passport" in page.url:
            return False
        if _has_login_panel(page):
            return False
        return _has_upload_ready(page)
    except Exception:
        return False


def wait_for_login(page, timeout_s=600):
    print("[login] 未检测到登录态，请在打开的浏览器中扫码登录（最长等待 10 分钟）...")
    page.goto(UPLOAD_URL, wait_until="domcontentloaded", timeout=60000)
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            if not _has_login_panel(page) and _has_upload_ready(page):
                print("[login] 登录成功，会话已保存到 browser-data/douyin")
                page.wait_for_timeout(2000)
                return True
        except Exception:
            pass
        page.wait_for_timeout(2000)
    return False


def upload_video(page, video_path):
    print(f"[upload] 上传视频: {video_path.name}")
    inp = first_visible(page, ["input[type='file']"], timeout=30000)
    if not inp:
        raise RuntimeError("找不到文件上传 input")
    inp.set_input_files(str(video_path))
    # Wait for the editor page (upload progress -> detail form).
    print("[upload] 等待视频上传/转码进入详情页 ...")
    deadline = time.time() + 600
    while time.time() < deadline:
        check_risk(page)
        if page.locator("input[placeholder*='标题'], textarea[placeholder*='标题']").count() > 0:
            print("[upload] 已进入详情页")
            return True
        page.wait_for_timeout(2000)
    raise RuntimeError("等待上传/转码超时")


def fill_title(page, title):
    loc = first_visible(page, [
        "input[placeholder*='作品标题']",
        "input[placeholder*='标题']",
        "textarea[placeholder*='标题']",
        ".title-input input",
    ], timeout=20000)
    if not loc:
        raise RuntimeError("找不到标题输入框")
    loc.click()
    loc.fill(title)
    print(f"[fill] 标题已填: {title}")


def fill_desc(page, desc):
    if not desc:
        return
    loc = first_visible(page, [
        "div[contenteditable='true']",
        "textarea[placeholder*='作品描述']",
        "textarea[placeholder*='添加作品描述']",
        ".editor-kit-container div[contenteditable='true']",
    ], timeout=20000)
    if not loc:
        raise RuntimeError("找不到描述编辑区")
    loc.click()
    page.wait_for_timeout(300)
    # Topic tags are typed as plain '#' text; Douyin turns them into chips.
    for token in desc.split():
        loc.type(token, delay=30)
        page.wait_for_timeout(400)
        page.keyboard.press("Space")
        page.wait_for_timeout(300)
    print(f"[fill] 描述已填: {desc}")


def click_publish(page, dry_run=False):
    if dry_run:
        print("[dry-run] 已填写但未点击发布")
        return None
    btn = first_visible(page, [
        "button:has-text('发布')",
        "button.primary:has-text('发布')",
        "button[class*='primary']:has-text('发布')",
    ], timeout=30000)
    if not btn:
        raise RuntimeError("找不到发布按钮")
    deadline = time.time() + 30
    while time.time() < deadline and not btn.is_enabled():
        time.sleep(0.5)
    if not btn.is_enabled():
        raise RuntimeError("发布按钮不可用（标题/视频可能未完成）")
    btn.click()
    print("[publish] 已点击发布，等待跳转内容管理页 ...")
    try:
        page.wait_for_url("**/content/manage**", timeout=45000)
    except PWTimeout:
        pass
    page.wait_for_timeout(4000)
    print(f"[publish] 当前URL: {page.url}")
    return page.url


def find_video_url(page):
    """Grab the newest published video link from the manage page."""
    try:
        page.goto(MANAGE_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)
        check_risk(page)
        hrefs = page.eval_on_selector_all(
            "a[href*='douyin.com/video/'], a[href*='/video/']",
            "els => els.map(e => e.href)",
        )
        if hrefs:
            return hrefs[0].split("?")[0]
        # Fallback: derive from item ids on the page.
        txt = page.content()
        m = re.search(r"douyin\.com/video/(\d+)", txt)
        if m:
            return f"https://www.douyin.com/video/{m.group(1)}"
    except Exception as e:
        print(f"[warn] 抓取视频URL失败: {e}")
    return None


def publish_video(video_path, title, desc, headless=False, dry_run=False):
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            channel="chrome",
            headless=headless,
            viewport={"width": 1440, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        if not is_logged_in(page):
            if headless:
                print("[login] 未检测到登录态；首次登录请加 --no-headless 扫码")
                ctx.close()
                return None
            if not wait_for_login(page):
                print("[login] 登录超时，退出")
                ctx.close()
                return None

        page.goto(UPLOAD_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4000)
        check_risk(page)

        upload_video(page, video_path)
        fill_title(page, title)
        fill_desc(page, desc)
        url = click_publish(page, dry_run=dry_run)

        if dry_run:
            print("[dry-run] 浏览器保持打开 60 秒供检查 ...")
            page.wait_for_timeout(60000)
        else:
            video_url = find_video_url(page)
            if video_url:
                url = video_url

        ctx.close()
        return url


def main():
    ap = argparse.ArgumentParser(description="Douyin video publisher")
    ap.add_argument("--video", help="视频路径，默认取 work/videos 下最新的 .mp4")
    ap.add_argument("--title", required=False)
    ap.add_argument("--desc", default="")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-headless", action="store_true")
    args = ap.parse_args()

    if args.list:
        if VIDEOS_DIR.exists():
            for p in sorted(VIDEOS_DIR.glob("*.mp4")):
                print(p)
        return

    video = Path(args.video) if args.video else newest_video()
    if not video or not video.exists():
        raise SystemExit("未找到视频，请用 --video 指定或用 --list 查看")
    if not args.title:
        raise SystemExit("请用 --title 指定标题")

    headless = not args.no_headless
    url = publish_video(
        video, args.title, args.desc, headless=headless, dry_run=args.dry_run
    )
    if url and not args.dry_run:
        log_publish(video.name, args.title, url)
        print(f"[done] 视频URL: {url}")
    elif args.dry_run:
        print("[done] dry-run 完成")
    else:
        print("[fail] 未发布")


if __name__ == "__main__":
    main()

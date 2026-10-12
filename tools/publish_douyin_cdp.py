"""Publish a video to Douyin by attaching to the user's already-logged-in Chrome
via CDP (http://localhost:9222).

The user logs in manually in tools/launch_chrome_debug.py's Chrome (real browser,
so face verification / QR is not risk-controlled); this script reuses that session.

Usage:
    python tools/launch_chrome_debug.py            # once, then log in manually
    python tools/publish_douyin_cdp.py --video work/videos/x.mp4 \
        --title "标题" --desc "#标签1 #标签2" --dry-run
    python tools/publish_douyin_cdp.py --video ... --title ... --desc ...   # real
    python tools/publish_douyin_cdp.py --check     # just verify CDP + login state

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
VIDEOS_DIR = REPO / "work" / "videos"
LOG_FILE = REPO / "work" / "douyin_published.log"

CDP_URL = "http://localhost:9222"
UPLOAD_URL = "https://creator.douyin.com/creator-micro/content/upload"
MANAGE_URL = "https://creator.douyin.com/creator-micro/content/manage"

RISK_HINTS = [
    "验证码", "请完成验证", "安全验证", "操作频繁", "请稍后再试",
    "异常", "风险", "verify", "captcha", "人脸",
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


def has_login_panel(page):
    try:
        if page.locator("text=扫码登录").count() > 0:
            return True
        if page.locator("div[class*='login']").count() > 0 and \
           page.locator("input[type='file']").count() == 0:
            return True
    except Exception:
        pass
    return False


def has_upload_ready(page):
    try:
        return page.locator("input[type='file']").count() > 0
    except Exception:
        return False


def check_risk(page):
    try:
        body = page.inner_text("body", timeout=3000)
    except Exception:
        return
    low = body.lower()
    for hint in RISK_HINTS:
        if hint.lower() in low:
            raise RuntimeError(
                f"检测到风控/验证提示（'{hint}'），立即停下，请手动处理后再运行。"
            )


def pick_page(ctx):
    """Reuse an existing creator.douyin.com tab, else open a new one."""
    for pg in ctx.pages:
        try:
            if "creator.douyin.com" in pg.url:
                return pg
        except Exception:
            continue
    return ctx.new_page()


def newest_video():
    if not VIDEOS_DIR.exists():
        return None
    vids = sorted(VIDEOS_DIR.glob("*.mp4"), key=lambda p: p.stat().st_mtime)
    return vids[-1] if vids else None


def connect(p):
    try:
        browser = p.chromium.connect_over_cdp(CDP_URL)
    except Exception as e:
        raise SystemExit(
            f"无法连接 {CDP_URL}。请先运行 tools/launch_chrome_debug.py 启动带调试端口的 Chrome。\n{e}"
        )
    return browser


def do_check(p):
    browser = connect(p)
    ctx = browser.contexts[0]
    page = pick_page(ctx)
    page.goto(UPLOAD_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)
    print("[check] URL:", page.url)
    print("[check] TITLE:", page.title())
    logged = (not has_login_panel(page)) and has_upload_ready(page)
    print("[check] 登录态:", "已登录 ✅" if logged else "未登录（请在 Chrome 里手动登录）❌")
    return 0 if logged else 1


def dismiss_resume_modal(page):
    """Douyin may show '你还有上次未发布的视频，是否继续编辑？' on the upload page.
    We always start fresh, so click 放弃."""
    try:
        discard = page.locator("text=放弃").first
        if discard.count() and discard.is_visible():
            discard.click()
            print("[modal] 关闭'继续编辑?'弹窗（点击 放弃）")
            page.wait_for_timeout(1500)
            return True
    except Exception:
        pass
    return False


def upload_video(page, video_path):
    print(f"[upload] 上传视频: {video_path.name}")
    dismiss_resume_modal(page)

    # The real file input is a 1x1 hidden element; set files directly (no actionability).
    inp = page.locator("input[type='file']").first
    try:
        inp.wait_for(state="attached", timeout=30000)
    except Exception:
        raise RuntimeError("找不到文件上传 input")
    inp.set_input_files(str(video_path), timeout=60000)

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
        txt = page.content()
        m = re.search(r"douyin\.com/video/(\d+)", txt)
        if m:
            return f"https://www.douyin.com/video/{m.group(1)}"
    except Exception as e:
        print(f"[warn] 抓取视频URL失败: {e}")
    return None


def main():
    ap = argparse.ArgumentParser(description="Douyin publisher via CDP attach")
    ap.add_argument("--video", help="视频路径，默认取 work/videos 下最新的 .mp4")
    ap.add_argument("--title")
    ap.add_argument("--desc", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true", help="只检查 CDP 连接和登录态")
    ap.add_argument("--screenshot", help="dry-run 完成后截图保存路径")
    args = ap.parse_args()

    with sync_playwright() as p:
        if args.check:
            return do_check(p)

        video = Path(args.video) if args.video else newest_video()
        if not video or not video.exists():
            raise SystemExit("未找到视频，请用 --video 指定")
        if not args.title:
            raise SystemExit("请用 --title 指定标题")

        browser = connect(p)
        ctx = browser.contexts[0]
        page = pick_page(ctx)

        page.goto(UPLOAD_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)

        if has_login_panel(page) or not has_upload_ready(page):
            raise SystemExit("未登录：请在 Chrome（端口 9222）里手动登录抖音创作者中心后重试。")

        check_risk(page)
        upload_video(page, video)
        fill_title(page, args.title)
        fill_desc(page, args.desc)
        url = click_publish(page, dry_run=args.dry_run)

        if args.dry_run:
            if args.screenshot:
                shot = Path(args.screenshot)
                shot.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(shot))
                print(f"[dry-run] 截图: {shot} ({shot.stat().st_size} bytes)")
            print("[dry-run] 完成，浏览器保持打开供检查。")
        else:
            video_url = find_video_url(page)
            if video_url:
                url = video_url
            if url:
                log_publish(video.name, args.title, url)
                print(f"[done] 视频URL: {url}")
            else:
                print("[warn] 已发布但未抓到URL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

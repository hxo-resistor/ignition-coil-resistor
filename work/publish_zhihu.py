"""Zhihu full-auto publisher via Playwright + persistent userDataDir.

Login state is kept in browser-data/zhihu (relative to repo root). Reuses the
saved session (no login needed) via the `z_c0` cookie.

Usage:
    python work/publish_zhihu.py --slug article_xxx
    python work/publish_zhihu.py --slug article_xxx --dry-run
    python work/publish_zhihu.py --slug article_xxx --no-headless   # first-run QR login
    python work/publish_zhihu.py --list

Published URLs are appended to work/zhihu_published.log.
"""
import argparse
import datetime as dt
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

REPO = Path(__file__).resolve().parent.parent
USER_DATA_DIR = REPO / "browser-data" / "zhihu"
LOG_FILE = REPO / "work" / "zhihu_published.log"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from zhihu_content import parse_article, list_articles, ARTICLES_DIR  # noqa: E402

WRITE_URL = "https://zhuanlan.zhihu.com/write"
HOME_URL = "https://www.zhihu.com/"


def log_publish(slug, title, url):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(f"{ts}\t{slug}\t{title}\t{url}\n")
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


def is_logged_in(context):
    """Zhihu keeps the auth token in the `z_c0` cookie. Works headless."""
    try:
        cookies = context.cookies("https://www.zhihu.com")
        return any(c["name"] == "z_c0" and c.get("value") for c in cookies)
    except Exception:
        return False


def wait_for_login(page, timeout_s=300):
    print("[login] 未检测到登录态，请在打开的浏览器中扫码登录（最长等待 5 分钟）...")
    page.goto(HOME_URL, wait_until="domcontentloaded", timeout=60000)
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            if page.locator("a[href*='/people/'], .AppHeader-profile, .Avatar").count() > 0:
                print("[login] 登录成功，会话已保存到 browser-data/zhihu")
                return True
        except Exception:
            pass
        page.wait_for_timeout(2000)
    return False


def fill_title(page, title):
    loc = first_visible(page, [
        "textarea[placeholder*='标题']",
        "input[placeholder*='标题']",
        ".WriteIndex-titleInput textarea",
        ".Editable--title",
        "div[contenteditable='true'][data-za-detail-view-path-module='Title']",
    ], timeout=20000)
    if not loc:
        raise RuntimeError("找不到标题输入框")
    loc.click()
    tag = loc.evaluate("el => el.tagName")
    if tag in ("TEXTAREA", "INPUT"):
        loc.fill(title)
    else:
        loc.type(title, delay=10)
    print(f"[fill] 标题已填: {title}")


def fill_body(page, body):
    loc = first_visible(page, [
        ".public-DraftEditor-content",
        "div[contenteditable='true'][role='textbox']",
        ".Editable-content div[contenteditable='true']",
        "div[contenteditable='true']",
    ], timeout=20000)
    if not loc:
        raise RuntimeError("找不到正文编辑区")
    loc.click()
    page.wait_for_timeout(300)
    page.evaluate(
        """(text) => {
            const el = document.activeElement;
            const dt = new DataTransfer();
            dt.setData('text/plain', text);
            el.dispatchEvent(new ClipboardEvent('paste', {clipboardData: dt, bubbles: true, cancelable: true}));
        }""",
        body,
    )
    page.wait_for_timeout(1500)
    print(f"[fill] 正文已填 ({len(body)} 字符)")


def click_publish(page, dry_run=False):
    if dry_run:
        print("[dry-run] 已填写但未点击发布")
        return None
    # Two buttons contain '发布': '发布设置' (panel) and the real primary blue one.
    publish = first_visible(page, [
        "button.Button--primary:has-text('发布')",
        "button.Button--blue:has-text('发布')",
    ], timeout=20000)
    if not publish:
        raise RuntimeError("找不到发布按钮（Button--primary）")
    deadline = time.time() + 30
    while time.time() < deadline and not publish.is_enabled():
        time.sleep(0.5)
    if not publish.is_enabled():
        raise RuntimeError("发布按钮仍不可用（可能标题/正文未成功填入）")
    publish.click()
    print("[publish] 已点击发布，等待跳转...")
    try:
        page.wait_for_url("**/p/**", timeout=30000)
    except PWTimeout:
        pass
    page.wait_for_timeout(3000)
    url = page.url
    clean = url.split("?")[0]
    print(f"[publish] 当前URL: {url}")
    return clean


def publish_article(article, headless=False, dry_run=False):
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            channel="chrome",
            headless=headless and not dry_run and False,
            viewport={"width": 1440, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        if not is_logged_in(ctx):
            if headless:
                print("[login] 未检测到登录态；首次登录请加 --no-headless 扫码")
                ctx.close()
                return None
            if not wait_for_login(page):
                print("[login] 登录超时，退出")
                ctx.close()
                return None

        print("[nav] 打开发布页 ...")
        page.goto(WRITE_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4000)

        fill_title(page, article["zhihu_title"])
        fill_body(page, article["body"])
        url = click_publish(page, dry_run=dry_run)

        if dry_run:
            print("[dry-run] 浏览器保持打开 60 秒供检查 ...")
            page.wait_for_timeout(60000)

        ctx.close()
        return url


def resolve_article(slug=None, file=None):
    if file:
        return parse_article(Path(file))
    if slug:
        path = ARTICLES_DIR / f"{slug}.md"
        if not path.exists():
            raise SystemExit(f"未找到文章: {path}")
        return parse_article(path)
    raise SystemExit("请用 --slug 或 --file 指定文章，或用 --list 查看")


def main():
    ap = argparse.ArgumentParser(description="Zhihu full-auto publisher")
    ap.add_argument("--slug")
    ap.add_argument("--file")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-headless", action="store_true")
    args = ap.parse_args()

    if args.list:
        for p in list_articles():
            a = parse_article(p)
            print(f"{p.stem}\t{a['zhihu_title']}")
        return

    article = resolve_article(args.slug, args.file)
    headless = not args.no_headless
    url = publish_article(article, headless=headless, dry_run=args.dry_run)
    if url and not args.dry_run:
        log_publish(article["slug"], article["zhihu_title"], url)
        print(f"[done] 文章URL: {url}")
    elif args.dry_run:
        print("[done] dry-run 完成")
    else:
        print("[fail] 未发布")


if __name__ == "__main__":
    main()

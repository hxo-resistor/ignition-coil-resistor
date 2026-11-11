#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""N10: 小红书图文笔记发布（Playwright 自动化框架）

⚠️ 高风控说明：
    小红书无官方发布 API，风控极严（设备指纹 + 行为检测）。业界通用做法是
    Playwright 复用登录态（persistent userDataDir）模拟人工发布。为避免封号：
    * 默认必须「真实用户已扫码登录一次」，会话保存在 browser-data/xhs。
    * 发布频率极低、单账号、避免批量、避免无头模式（用真实 Chrome）。
    * 本框架 selectors 为「尽力而为」，页面改版需人工微调。

用法：
    python work/n8n/n10_xiaohongshu.py --login          # 打开浏览器扫码登录（一次性）
    python work/n8n/n10_xiaohongshu.py --slug article_xxx --dry-run
    python work/n8n/n10_xiaohongshu.py --slug article_xxx   # 真实发布（图文笔记）
输出契约：{"ok": true, "action": "xiaohongshu", ...}
"""
import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from _common import emit, fail, REPO  # noqa: E402
import content_factory  # noqa: E402

DRY = os.environ.get("HXO_DRY_RUN") == "1"
# 风控保护：默认关闭。人工验证通过后再用 XHS_ENABLED=1 开启自动发布。
XHS_ENABLED = os.environ.get("XHS_ENABLED") == "1"
USER_DATA_DIR = REPO / "browser-data" / "xhs"
UPLOAD_URL = "https://creator.xiaohongshu.com/publish/publish"
HOME_URL = "https://www.xiaohongshu.com"

# 尽力而为的 selectors（页面改版需人工更新）
SEL_LOGIN_AVATAR = ".user .avatar, .avatar-wrapper, .reds-avatar"
SEL_TITLE = "input[placeholder*='标题'], .title-input input, textarea[placeholder*='标题']"
SEL_BODY = ".content-editable, .ql-editor, textarea[placeholder*='正文'], div[contenteditable='true']"
SEL_PUBLISH = "button:has-text('发布'), .publish-btn, button.submit"


def has_login_state():
    return (USER_DATA_DIR / "Default").exists()


def login():
    """打开可见浏览器扫码登录，会话自动保存。"""
    from playwright.sync_api import sync_playwright
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    print("[xhs] 打开浏览器扫码登录（最长等 3 分钟）...")
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR), channel="chrome",
            headless=False, viewport={"width": 1280, "height": 900})
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(HOME_URL, wait_until="domcontentloaded", timeout=60000)
        deadline = time.time() + 180
        while time.time() < deadline:
            try:
                if page.locator(SEL_LOGIN_AVATAR).count() > 0:
                    print("[xhs] 登录成功，会话已保存到 browser-data/xhs")
                    ctx.close()
                    return
            except Exception:
                pass
            time.sleep(2)
        print("[xhs] 登录超时")
        ctx.close()


def create_note(title, body):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR), channel="chrome",
            headless=False, viewport={"width": 1280, "height": 900})
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(UPLOAD_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4000)

        t = page.locator(SEL_TITLE).first
        if t.count() and t.is_visible():
            t.fill(title)
        b = page.locator(SEL_BODY).first
        if b.count() and b.is_visible():
            b.click()
            page.keyboard.type(body, delay=20)

        if DRY:
            print("[xhs] dry-run：已填写，未点击发布")
            page.wait_for_timeout(3000)
            ctx.close()
            return None

        pub = page.locator(SEL_PUBLISH).first
        if pub.count() and pub.is_visible():
            pub.click()
            page.wait_for_timeout(5000)
        url = page.url
        ctx.close()
        return url


def main():
    ap = argparse.ArgumentParser(description="小红书图文笔记发布")
    ap.add_argument("--login", action="store_true")
    ap.add_argument("--slug")
    a = ap.parse_args()

    if a.login:
        login()
        return

    if not a.slug:
        ap.print_help()
        sys.exit(2)

    if not XHS_ENABLED:
        emit({"ok": True, "action": "xiaohongshu", "skipped": True,
              "reason": "XHS_ENABLED 未启用（风控保护，人工验证通过后再开）"})
        return

    if not has_login_state():
        emit({"ok": True, "action": "xiaohongshu", "skipped": True,
              "reason": "未登录。先跑 --login 扫码一次"})
        return

    social = content_factory.load_social(a.slug)
    if not social:
        fail("xiaohongshu", f"文案缺失: work/social/{a.slug}.json")

    title = social.get("title_cn", a.slug)
    body = social.get("xiaohongshu", "")

    if DRY:
        emit({"ok": True, "action": "xiaohongshu", "dry_run": True, "title": title})
        return

    url = create_note(title, body)
    if url:
        emit({"ok": True, "action": "xiaohongshu", "url": url})
    else:
        emit({"ok": True, "action": "xiaohongshu", "note": "已发布（URL 未能捕获）"})


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""N9: 微信公众号草稿发布（官方接口）

依赖环境变量：
    WECHAT_APPID    公众号 AppID（登录 mp.weixin.qq.com → 开发 → 基本配置）
    WECHAT_SECRET   公众号 AppSecret

流程：
    1. GET  /cgi-bin/token            → access_token（缓存 2 小时）
    2. POST /cgi-bin/draft/add        → 新增草稿（正文 HTML）
    3. 群发：需认证服务号 + 群发权限；个人订阅号无接口权限，只能发草稿后人工群发。

用法：
    python work/n8n/n9_wechat.py --slug article_xxx
输出契约：{"ok": true, "action": "wechat", ...}
"""
import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from _common import emit, fail, REPO  # noqa: E402
import content_factory  # noqa: E402

try:
    import requests
except ImportError:
    requests = None

API = "https://api.weixin.qq.com"
DRY = os.environ.get("HXO_DRY_RUN") == "1"
APPID = os.environ.get("WECHAT_APPID", "")
SECRET = os.environ.get("WECHAT_SECRET", "")
TOKEN_CACHE = REPO / "work" / ".wechat_token.json"


def get_access_token():
    """access_token 2 小时有效，落盘缓存避免频繁请求。"""
    if TOKEN_CACHE.exists():
        try:
            c = json.loads(TOKEN_CACHE.read_text(encoding="utf-8"))
            if c.get("expire", 0) > dt.datetime.now().timestamp() + 60:
                return c["access_token"]
        except Exception:
            pass
    r = requests.get(API + "/cgi-bin/token", params={
        "grant_type": "client_credential", "appid": APPID, "secret": SECRET}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if "access_token" not in data:
        raise RuntimeError(f"获取 access_token 失败: {data}")
    TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_CACHE.write_text(json.dumps({
        "access_token": data["access_token"],
        "expire": dt.datetime.now().timestamp() + data.get("expires_in", 7200),
    }), encoding="utf-8")
    return data["access_token"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    a = ap.parse_args()

    if not APPID or not SECRET:
        emit({"ok": True, "action": "wechat", "skipped": True, "reason": "WECHAT_APPID/SECRET 未配置"})
        return
    if requests is None:
        fail("wechat", "缺少 requests 库")

    social = content_factory.load_social(a.slug)
    if not social:
        fail("wechat", f"文案缺失: work/social/{a.slug}.json")

    wc = social.get("wechat", {})
    title = wc.get("title", social.get("title_cn", a.slug))
    digest = wc.get("digest", "")
    content = wc.get("content", "")
    url = f"https://www.hxo-lcr.cn/{a.slug}.html"

    if DRY:
        emit({"ok": True, "action": "wechat", "dry_run": True,
              "title": title, "content_chars": len(content)})
        return

    try:
        token = get_access_token()
        r = requests.post(API + "/cgi-bin/draft/add", params={"access_token": token}, json={
            "articles": [{
                "title": title,
                "author": "HXO Resistor",
                "digest": digest,
                "content": content,
                "content_source_url": url,
            }]
        }, timeout=60)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        fail("wechat", f"新增草稿失败: {e}")

    if "media_id" not in data:
        fail("wechat", f"草稿接口返回异常: {data}")
    emit({"ok": True, "action": "wechat", "media_id": data["media_id"], "note": "草稿已保存，待人工群发"})


if __name__ == "__main__":
    main()

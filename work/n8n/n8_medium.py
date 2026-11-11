#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""N8: 发布到 Medium（REST API 全自动）

依赖：
    MEDIUM_TOKEN  自签发令牌。获取：https://medium.com/me/settings → Security and apps
                  → Integration tokens（或 "Self-issued access token"）。

流程：
    1. GET  https://api.medium.com/v1/me         → 取 userId
    2. POST https://api.medium.com/v1/users/{id}/posts   → 发布（markdown 格式）
    3. HXO_DRY_RUN=1 时只校验 token，不真正发布

用法：
    python work/n8n/n8_medium.py --slug article_xxx [--publish-status draft|public]
输出契约：{"ok": true, "action": "medium", ...}
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from _common import emit, fail  # noqa: E402
import content_factory  # noqa: E402

try:
    import requests
except ImportError:
    requests = None

API = "https://api.medium.com"
DRY = os.environ.get("HXO_DRY_RUN") == "1"
TOKEN = os.environ.get("MEDIUM_TOKEN", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--publish-status", default="draft", choices=["draft", "public", "unlisted"])
    a = ap.parse_args()

    if not TOKEN:
        emit({"ok": True, "action": "medium", "skipped": True, "reason": "MEDIUM_TOKEN 未配置"})
        return
    if requests is None:
        fail("medium", "缺少 requests 库")

    social = content_factory.load_social(a.slug)
    if not social:
        fail("medium", f"海外文案缺失: work/social/{a.slug}.json（先跑 --region cn 生成）")

    title = social.get("title_en", a.slug)
    content = social.get("medium", "")
    tags = [t.lstrip("#") for t in social.get("hashtags_en", [])][:5]

    headers = {"Authorization": f"Bearer {TOKEN}"}

    if DRY:
        emit({"ok": True, "action": "medium", "dry_run": True,
              "title": title, "tags": tags, "content_chars": len(content)})
        return

    try:
        r = requests.get(API + "/v1/me", headers=headers, timeout=30)
        r.raise_for_status()
        uid = r.json()["data"]["id"]
    except Exception as e:
        fail("medium", f"获取 userId 失败: {e}")

    payload = {
        "title": title,
        "contentFormat": "markdown",
        "content": content,
        "tags": tags,
        "publishStatus": a.publish_status,
    }
    try:
        r = requests.post(f"{API}/v1/users/{uid}/posts", headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()["data"]
    except Exception as e:
        fail("medium", f"发布失败: {e}")

    emit({"ok": True, "action": "medium", "id": data.get("id"),
          "url": data.get("url"), "status": a.publish_status})


if __name__ == "__main__":
    main()

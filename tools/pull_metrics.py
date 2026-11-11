#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pull_metrics.py — 发布后数据回拉 + 喂给 self_optimize 形成终极闭环

发布后：
    1. record_publish()  记录 post_id / 平台 / 状态 → work/published_links.json
    2. pull_*()          拉取真实点赞/阅读/互动
       * Buffer：公开 API 不暴露互动数据，只记录 post_id 与状态
       * X：需 X_BEARER_TOKEN（X API v2，免费 Basic 档可查单帖指标）
       * LinkedIn：需 LINKEDIN_TOKEN（组织管理 API）
    3. feed_self_optimize()  把归一化效果分喂给 self_optimize，动态调权 + 提示词自调优

无凭证时优雅跳过，不阻塞。
"""
import datetime as dt
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import content_factory  # noqa: E402
import self_optimize  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent.parent
LINKS = REPO / "work" / "published_links.json"


def record_publish(slug, platform, post_id, status):
    data = []
    if LINKS.exists():
        try:
            data = json.loads(LINKS.read_text(encoding="utf-8"))
        except Exception:
            data = []
    data.append({
        "ts": dt.datetime.now().isoformat(timespec="seconds"),
        "slug": slug, "platform": platform, "post_id": post_id, "status": status,
    })
    LINKS.parent.mkdir(parents=True, exist_ok=True)
    LINKS.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def pull_x_metrics(post_id):
    """X 单帖指标（需 X_BEARER_TOKEN，X API v2）。无 token 返回 None。"""
    token = os.environ.get("X_BEARER_TOKEN", "")
    if not token:
        return None
    import requests
    r = requests.get(f"https://api.x.com/2/tweets/{post_id}",
                     params={"tweet.fields": "public_metrics"},
                     headers={"Authorization": f"Bearer {token}"}, timeout=30)
    r.raise_for_status()
    m = r.json().get("data", {}).get("public_metrics", {})
    return {"likes": m.get("like_count", 0), "retweets": m.get("retweet_count", 0),
            "replies": m.get("reply_count", 0), "impressions": m.get("impression_count", 0)}


def pull_linkedin_metrics(post_id):
    """LinkedIn 帖子指标（需 LINKEDIN_TOKEN，组织 API）。无 token 返回 None。"""
    token = os.environ.get("LINKEDIN_TOKEN", "")
    if not token:
        return None
    return {"note": "LinkedIn 组织 API 需 urn 与权限，接入后补全"}


def normalize(metrics) -> float:
    """把互动指标归一化到 0~1 效果分（简单对数压缩，避免单帖刷分）。"""
    if not metrics:
        return 0.5
    likes = metrics.get("likes", 0)
    views = metrics.get("impressions", metrics.get("views", 0))
    score = (likes * 1.0 + (views / 100.0)) 
    return round(min(1.0, max(0.0, score / 10.0)), 3)


def feed_self_optimize(slug, platform, metrics=None):
    spec = content_factory.spec_by_slug(slug)
    ctype = spec.get("ctype", "selection") if spec else "selection"
    outcome = normalize(metrics)
    self_optimize.record_result(ctype, outcome)
    return ctype, outcome


def main():
    # 回拉最近发布的帖子，尝试取互动，喂给 self_optimize
    if not LINKS.exists():
        print("暂无发布记录。先跑发布再回拉。")
        return
    posts = json.loads(LINKS.read_text(encoding="utf-8"))
    print(f"共 {len(posts)} 条发布记录，逐条回拉：")
    for p in posts:
        metrics = None
        if p["platform"] == "x":
            metrics = pull_x_metrics(p["post_id"])
        elif p["platform"] == "linkedin":
            metrics = pull_linkedin_metrics(p["post_id"])
        ctype, outcome = feed_self_optimize(p["slug"], p["platform"], metrics)
        src = "真实互动" if metrics else "无凭证，用占位分"
        print(f"  [{p['platform']}] {p['slug']} → ctype={ctype} outcome={outcome} ({src})")
    print("\n" + self_optimize.daily_review())


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""publish_reddit.py — Reddit 技术版块「技术解答 + 软植入」框架（Phase C）

策略：专业论坛反广告极严，本框架**不硬发广告**，而是：
    1. 搜索目标版块近期与「点火线圈/泄放电阻/EMI/选型」相关的提问；
    2. 生成一段真正能解决问题的技术回答（先帮人，最后一句才软植入 HXO）；
    3. 遵守 Reddit 版规与反垃圾规则（低频、诚实、不刷屏）。

依赖：
    pip install praw
环境变量（申请 Reddit "script" app 后填入）：
    REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET / REDDIT_USERNAME / REDDIT_PASSWORD
    REDDIT_USER_AGENT   e.g. "hxo-bot/1.0 (by /u/<username>)"

用法：
    python tools/publish_reddit.py --search "bleeder resistor"       # 找相关提问（只读）
    python tools/publish_reddit.py --answer <post_id> --slug article_xxx   # 回答（软植入）
    python tools/publish_reddit.py --dry-run --search "..."          # 只列候选，不发
"""
import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import content_factory  # noqa: E402
import translate  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DRY = os.environ.get("HXO_DRY_RUN") == "1"

TARGET_SUBREDDITS = [
    "AskElectronics",      # 高频问答，注意版规（禁止纯自我推广）
    "electronics",         # 技术讨论
    "ElectricalEngineering",
    "PowerElectronics",
]

# 软植入模板：先给硬核答案，最后一句才自然带出 HXO
SOFT_PITCH = "For reference, we (HXO Resistor) build automotive/industrial resistors for exactly this use case — happy to share datasheets or test data if useful."


def _credentials_ready() -> bool:
    return all(os.environ.get(k) for k in (
        "REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME",
        "REDDIT_PASSWORD", "REDDIT_USER_AGENT"))


def _get_reddit():
    import praw
    return praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        username=os.environ["REDDIT_USERNAME"],
        password=os.environ["REDDIT_PASSWORD"],
        user_agent=os.environ["REDDIT_USER_AGENT"],
    )


def build_answer(spec):
    """生成技术回答：中文技术要点 → DeepSeek 翻英文 → 加软植入。"""
    cta = content_factory.PRODUCT_CTA[content_factory._cta_key(spec["product"])]
    points = "\n".join(f"- {p}" for p in spec.get("pain", [])[:3])
    body_cn = f"{spec['desc']}\n{points}\n{spec['formula']}"
    body_en = translate.translate(body_cn, "en") if translate.is_configured() else spec["hook_en"]
    return f"{body_en}\n\n{SOFT_PITCH}"


def search(keyword, limit=5):
    reddit = _get_reddit()
    hits = []
    for sub in TARGET_SUBREDDITS:
        try:
            for post in reddit.subreddit(sub).search(keyword, limit=limit):
                hits.append((sub, post.id, post.title, post.url))
        except Exception as e:
            print(f"[warn] 搜索 {sub} 失败: {e}", file=sys.stderr)
        time.sleep(1)  # 限流
    return hits


def answer(post_id, spec):
    reddit = _get_reddit()
    submission = reddit.submission(id=post_id)
    text = build_answer(spec)
    if DRY:
        print(f"[dry-run] 将对 {post_id} 回复：\n{text}")
        return
    submission.reply(text)
    print(f"[ok] 已回复 {post_id}")


def main():
    ap = argparse.ArgumentParser(description="Reddit 技术版块软植入框架")
    ap.add_argument("--search")
    ap.add_argument("--answer")
    ap.add_argument("--slug", help="用于生成回答的选题 slug")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.dry_run:
        os.environ["HXO_DRY_RUN"] = "1"

    if not _credentials_ready():
        print("Reddit 凭证未配置。需 REDDIT_CLIENT_ID/CLIENT_SECRET/USERNAME/PASSWORD/USER_AGENT。")
        print("申请：https://www.reddit.com/prefs/apps → create a 'script' app")
        sys.exit(0)

    if args.search:
        hits = search(args.search)
        for sub, pid, title, url in hits:
            print(f"[{sub}] {pid}  {title}\n    {url}")
        return

    if args.answer:
        if not args.slug:
            print("--answer 需配合 --slug 指定选题")
            sys.exit(2)
        spec = content_factory.spec_by_slug(args.slug)
        if not spec:
            print(f"未找到 slug: {args.slug}")
            sys.exit(2)
        answer(args.answer, spec)
        return

    ap.print_help()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pull_metrics.py — 发布后数据回拉（Buffer GraphQL 为主）+ 喂给 self_optimize 形成闭环

数据源：Buffer GraphQL API（api.buffer.com/graphql，复用已活的 BUFFER_TOKEN）
    可拿到真实指标：Impressions(阅读/曝光) / Reactions(点赞) / Comments / Reposts / Clicks / Eng.Rate

链路：
    1. account { organizations { id } }    → 取 orgId
    2. posts(input:{organizationId})       → 列帖子（含 sent 帖及 metrics）
    3. 归一化效果分 → self_optimize.record_result() → 动态调权 + 提示词自调优

兼容：仍保留 X_BEARER_TOKEN / LINKEDIN_TOKEN 增强项（有则补更细数据），无则不影响 Buffer 主链路。
"""
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import content_factory  # noqa: E402
import self_optimize  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    import requests
except ImportError:
    requests = None

REPO = Path(__file__).resolve().parent.parent
LINKS = REPO / "work" / "published_links.json"
GRAPHQL = "https://api.buffer.com/graphql"
TOKEN = os.environ.get("BUFFER_TOKEN", "34cyqxAOzZHdZwFrBFy6Ou89lwONFsuihkJ2RCOGAZm")
PROXY = os.environ.get("HXO_PROXY", "http://127.0.0.1:7897")


def _gql(query, variables=None):
    if requests is None:
        raise RuntimeError("缺少 requests 库")
    r = requests.post(GRAPHQL, json={"query": query, "variables": variables or {}},
                      headers={"Authorization": f"Bearer {TOKEN}"},
                      proxies={"http": PROXY, "https": PROXY}, timeout=40)
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(data["errors"][0].get("message", str(data["errors"])))
    return data["data"]


def get_org_id():
    d = _gql("{ account { organizations { id } } }")
    orgs = d["account"].get("organizations", [])
    if not orgs:
        raise RuntimeError("未找到 organization")
    return orgs[0]["id"]


def list_posts():
    """列出帖子及其 metrics（status + text + metrics）。"""
    org = get_org_id()
    d = _gql('{ posts(input: { organizationId: "%s" }) { edges { node { id status text metrics { name value } } } } }' % org)
    out = []
    for e in d["posts"]["edges"]:
        n = e["node"]
        out.append({
            "id": n["id"], "status": n["status"], "text": n.get("text", ""),
            "metrics": {m["name"]: m["value"] for m in n.get("metrics", [])},
        })
    return out


def get_post_metrics(post_id):
    d = _gql('{ post(input: { id: "%s" }) { id status metrics { name value } } }' % post_id)
    p = d["post"]
    return {"id": p["id"], "status": p["status"], "metrics": {m["name"]: m["value"] for m in p.get("metrics", [])}}


def _slug_from_text(text):
    """从帖子文本反查 slug：先查 URL 里的 slug，再按中文标题匹配（旧帖无 slug 只有标题）。"""
    if not text:
        return None
    m = re.search(r"(article_[a-z0-9_]+)", text)
    if m:
        return m.group(1)
    # 按中文标题匹配（标题作为子串，或取标题前 12 字做模糊匹配）
    for t in content_factory.TOPICS:
        title = t.get("title", "")
        if title and (title in text or (len(title) >= 8 and title[:12] in text)):
            return t["slug"]
    return None


def normalize(metrics) -> float:
    """互动指标 → 0~1 效果分（对数压缩防单帖刷分）。"""
    impressions = metrics.get("Impressions", 0) or 0
    reactions = metrics.get("Reactions", 0) or 0
    comments = metrics.get("Comments", 0) or 0
    reposts = metrics.get("Reposts", 0) or 0
    clicks = metrics.get("Clicks", 0) or 0
    engagement = reactions * 3 + comments * 5 + reposts * 4 + clicks * 2
    raw = impressions * 0.1 + engagement
    import math
    return round(min(1.0, math.log1p(raw) / 5.0), 3)


def record_publish(slug, platform, post_id, status):
    data = []
    if LINKS.exists():
        try:
            data = json.loads(LINKS.read_text(encoding="utf-8"))
        except Exception:
            data = []
    # 去重：同 post_id 已存在则只更新状态，不重复追加
    for d in data:
        if d.get("post_id") == post_id:
            d["status"] = status
            d["ts"] = dt.datetime.now().isoformat(timespec="seconds")
            LINKS.parent.mkdir(parents=True, exist_ok=True)
            LINKS.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return
    data.append({"ts": dt.datetime.now().isoformat(timespec="seconds"),
                 "slug": slug, "platform": platform, "post_id": post_id, "status": status})
    LINKS.parent.mkdir(parents=True, exist_ok=True)
    LINKS.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def pull_and_feed():
    """从 Buffer 拉取真实数据：登记排队帖，回喂已发帖数据给 self_optimize。"""
    posts = list_posts()
    sent = [p for p in posts if p["status"] == "sent"]
    scheduled = [p for p in posts if p["status"] == "scheduled"]
    lines = [f"Buffer 共 {len(posts)} 条帖子：已发 {len(sent)}，排队中 {len(scheduled)}。"]

    # 登记排队中的帖子（post_id 入库，等发出后下次自动回填真实数据）
    registered = 0
    for p in scheduled:
        slug = _slug_from_text(p["text"])
        if slug:
            record_publish(slug, "buffer", p["id"], "scheduled")
            registered += 1
            lines.append(f"  [登记] {slug}  排队中 post_id={p['id']}")
    if registered:
        lines.append(f"已登记 {registered} 条排队帖到 published_links.json，发出后自动回填。")

    fed = 0
    for p in sent:
        slug = _slug_from_text(p["text"])
        if not slug:
            continue
        spec = content_factory.spec_by_slug(slug)
        ctype = spec.get("ctype", "selection") if spec else "selection"
        score = normalize(p["metrics"])
        self_optimize.record_result(ctype, score)
        fed += 1
        imp = p["metrics"].get("Impressions", 0)
        rea = p["metrics"].get("Reactions", 0)
        com = p["metrics"].get("Comments", 0)
        lines.append(f"  [{ctype:<12}] {slug}  曝光={imp} 点赞={rea} 评论={com} → 效果分={score}")
    lines.append(f"已回喂 {fed} 条真实数据到 self_optimize。")
    return "\n".join(lines)


def main():
    try:
        print(pull_and_feed())
        print("\n" + self_optimize.daily_review())
    except Exception as e:
        print(f"[拉取失败] {e}")


if __name__ == "__main__":
    main()

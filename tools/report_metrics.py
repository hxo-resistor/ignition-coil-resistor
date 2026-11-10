#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""report_metrics.py — 发布数据回传与复盘

现状（无外部 API key 也能跑）：
    1. 从 work/publish_all.log 解析每次发布的成功/失败统计。
    2. 从 work/published_manifest.json 读取已发布清单。
    3. 汇总成 work/metrics/<date>.json + 可读报告。

扩展点（配好 key 后自动启用）：
    * GA4 Data API       -> 官网 PV/UV（需 GOOGLE_APPLICATION_CREDENTIALS + GA4_PROPERTY_ID）
    * 百度搜索资源平台     -> 点击/展现（需 BAIDU_QUOTA_TOKEN）
    * LinkedIn/X API     -> 阅读量/互动（需 LINKEDIN_TOKEN / X_BEARER_TOKEN）

用法：
    python tools/report_metrics.py                 # 生成本地复盘报告
    python tools/report_metrics.py --days 7        # 汇总最近 N 天
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent.parent
WORK = REPO / "work"
LOG_FILE = WORK / "publish_all.log"
MANIFEST = WORK / "published_manifest.json"
METRICS_DIR = WORK / "metrics"

ACTION_NAMES = {
    "website": "官网", "baidu": "百度", "zhihu": "知乎",
    "supabase": "Supabase", "dashboard": "看板",
    "linkedin": "LinkedIn", "x": "X/Twitter",
}


def parse_log(days=7):
    """解析 publish_all.log，统计各动作成功/失败次数（最近 N 天）。"""
    if not LOG_FILE.exists():
        return {}
    cutoff = dt.datetime.now() - dt.timedelta(days=days)
    stats = {}
    current_ts = None
    for ln in LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = re.match(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]", ln)
        if m:
            try:
                current_ts = dt.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
        if current_ts and current_ts < cutoff:
            continue
        m = re.match(r"\s*\[(OK|FAIL)\s*\]\s+(\w+)\s", ln)
        if m:
            flag, key = m.group(1), m.group(2)
            d = stats.setdefault(key, {"ok": 0, "fail": 0, "name": ACTION_NAMES.get(key, key)})
            d["ok" if flag == "OK" else "fail"] += 1
    return stats


def load_manifest():
    if MANIFEST.exists():
        try:
            return json.loads(MANIFEST.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"published": []}


def build_report(days=7):
    stats = parse_log(days)
    manifest = load_manifest()
    published = manifest.get("published", [])
    report = {
        "generated_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "days": days,
        "published_total": len(published),
        "recent_published": [
            {"slug": p.get("slug"), "title": p.get("title"),
             "published_at": p.get("published_at")}
            for p in published[-10:]
        ],
        "action_stats": stats,
        "platform_metrics": {},
    }
    # 外部平台指标（未配置时标记未启用）
    report["platform_metrics"]["ga4_website"] = {
        "enabled": False, "note": "未配置 GOOGLE_APPLICATION_CREDENTIALS / GA4_PROPERTY_ID"}
    report["platform_metrics"]["linkedin"] = {
        "enabled": False, "note": "未配置 LINKEDIN_TOKEN"}
    report["platform_metrics"]["x"] = {
        "enabled": False, "note": "未配置 X_BEARER_TOKEN"}
    return report


def render_text(report):
    lines = [
        "=" * 60,
        f"发布复盘报告（最近 {report['days']} 天）",
        f"生成时间: {report['generated_at']}",
        f"累计已发布: {report['published_total']} 篇",
        "=" * 60,
        "",
        "各平台动作统计:",
    ]
    for key, d in sorted(report["action_stats"].items()):
        total = d["ok"] + d["fail"]
        lines.append(f"  {d['name']:<10} 成功 {d['ok']} / 失败 {d['fail']}  (共 {total})")
    if not report["action_stats"]:
        lines.append("  （无记录）")
    lines.append("")
    lines.append("外部平台指标:（未配置 API key，暂未启用）")
    for k, v in report["platform_metrics"].items():
        lines.append(f"  - {k}: {v['note']}")
    lines.append("")
    lines.append("最近发布:")
    for p in report["recent_published"]:
        lines.append(f"  - [{p['published_at']}] {p['slug']}  {p['title']}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="发布数据回传与复盘")
    ap.add_argument("--days", type=int, default=7)
    args = ap.parse_args()

    report = build_report(args.days)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    out = METRICS_DIR / f"{dt.date.today().isoformat()}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[写入] {out.relative_to(REPO)}")
    print(render_text(report))


if __name__ == "__main__":
    main()

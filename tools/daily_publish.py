#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""daily_publish.py — 每日自动发文（区域感知版）

流程（国内 CN）：
    1. 读 work/topic_pool.md，取第一个「待写」主题
    2. content_factory 生成差异化中文长文 + 海外文案（work/social/*.json）
    3. 构建 HTML（tools/build_from_content.py）并复制到仓库根
    4. publish_all.py --region cn 发布国内（官网/百度/知乎/Supabase/看板）
    5. 成功后选题标记「已完成」，并记录 last_published_slug

流程（海外 INTL）：
    1. 读 work/last_published_slug.txt
    2. publish_all.py --region intl 发布海外（LinkedIn/X），文案取 work/social/

用法：
    python tools/daily_publish.py --region cn      # 国内（默认）
    python tools/daily_publish.py --region intl    # 海外
    python tools/daily_publish.py --region all     # 一次性国内外
    python tools/daily_publish.py --dry-run --list
红线：只发 1 篇；遇错停下，不重试。
"""
import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import content_factory  # noqa: E402
import tz  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent.parent
WORK = REPO / "work"
POOL = WORK / "topic_pool.md"
ARTICLES = REPO / "content" / "articles"
LAST_SLUG = WORK / "last_published_slug.txt"
PY = sys.executable


def log(msg):
    print(f"[{dt.datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# 选题池
# ---------------------------------------------------------------------------
def parse_pool():
    lines = POOL.read_text(encoding="utf-8").splitlines()
    rows = []
    for idx, ln in enumerate(lines):
        if not ln.strip().startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        if cells[0] in ("#", "---") or set(cells[0]) <= set("-"):
            continue
        if cells[0].isdigit():
            rows.append({
                "line": idx, "num": cells[0], "topic": cells[1],
                "priority": cells[2], "product": cells[3],
                "platforms": cells[4], "status": cells[5],
            })
    return lines, rows


def next_topic(rows):
    for r in rows:
        if r["status"] == "待写":
            return r
    return None


def mark_done(topic):
    lines = POOL.read_text(encoding="utf-8").splitlines()
    for i, ln in enumerate(lines):
        if ln.strip().startswith("|") and topic["topic"] in ln and "待写" in ln:
            lines[i] = ln.replace("待写", "已完成")
            POOL.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return True
    return False


def run(cmd, timeout=900):
    r = subprocess.run(cmd, shell=True, cwd=str(REPO), capture_output=True,
                       text=True, encoding="utf-8", errors="ignore", timeout=timeout)
    return r.returncode, r.stdout or "", r.stderr or ""


# ---------------------------------------------------------------------------
# 海外发布
# ---------------------------------------------------------------------------
def publish_intl(dry_run):
    if not dry_run and not tz.intl_golden():
        log("[海外] 当前不在美东/美西黄金窗口，跳过。")
        print(tz.status_report())
        sys.exit(0)
    if not LAST_SLUG.exists():
        log(f"[错误] 未找到 {LAST_SLUG.name}（国内发布尚未成功过），无法海外发布")
        sys.exit(2)
    slug = LAST_SLUG.read_text(encoding="utf-8").strip()
    if not slug:
        log("[错误] last_published_slug 为空")
        sys.exit(2)
    social = content_factory.load_social(slug)
    if not social:
        log(f"[错误] 未找到海外文案 work/social/{slug}.json，请先跑 --region cn 生成")
        sys.exit(2)
    log(f"[海外] 发布 slug={slug}  ({social.get('title_en', '')})")
    cmd = f'"{PY}" tools/publish_all.py --slug {slug} --region intl'
    if dry_run:
        cmd += " --dry-run"
    rc, out, err = run(cmd)
    print(out)
    if err.strip():
        print(err, file=sys.stderr)
    ok = (rc == 0) and ("全部动作成功" in out)
    log("[海外] 完成" if ok else f"[错误] 海外发布未全部成功（rc={rc}）")
    sys.exit(0 if ok or dry_run else 1)


# ---------------------------------------------------------------------------
# 国内发布（含生成 + 构建）
# ---------------------------------------------------------------------------
def publish_cn(dry_run, also_intl=False):
    if not POOL.exists():
        log(f"[错误] 选题池不存在: {POOL}")
        sys.exit(2)
    _, rows = parse_pool()
    topic = next_topic(rows)
    if not topic:
        log("选题池已无「待写」主题，收工。")
        return 0

    log(f"下一个主题: #{topic['num']} [{topic['priority']}] {topic['topic']}  (产品: {topic['product']})")
    spec = content_factory.spec_by_num(topic["num"])
    if not spec:
        log(f"[错误] content_factory 缺少 #{topic['num']} 的规格")
        sys.exit(2)

    # 1) 生成差异化中文长文 + 海外文案
    md_text, slug = content_factory.build_article_md(spec)
    md_path = ARTICLES / f"{slug}.md"
    md_path.write_text(md_text, encoding="utf-8")
    log(f"[生成] {md_path.relative_to(REPO)}")
    social_path = content_factory.write_social(spec)
    log(f"[海外文案] {social_path.relative_to(REPO)}")
    LAST_SLUG.write_text(slug + "\n", encoding="utf-8")

    # 2) 构建 HTML 并复制到根目录
    rc, out, err = run(f'"{PY}" tools/build_from_content.py --content content/articles --out build')
    if rc != 0:
        log(f"[错误] 构建失败：{err[:200]}")
        sys.exit(1)
    built = REPO / "build" / f"{slug}.html"
    if not built.exists():
        log(f"[错误] 构建产物缺失: {built}")
        sys.exit(1)
    (REPO / f"{slug}.html").write_text(built.read_text(encoding="utf-8"), encoding="utf-8")
    log(f"[构建] {slug}.html 生成并复制到根目录")

    # 3) 发布国内
    cmd = f'"{PY}" tools/publish_all.py --slug {slug} --region cn'
    if dry_run:
        cmd += " --dry-run"
    log(f"[发布] {cmd}")
    rc, out, err = run(cmd, timeout=900)
    print(out)
    if err.strip():
        print(err, file=sys.stderr)
    ok = (rc == 0) and ("全部动作成功" in out)

    if dry_run:
        log("[dry-run] 完成，未标记选题。")
        return 0
    if not ok:
        log(f"[错误] 国内发布未全部成功（rc={rc}），未标记选题（保留待写，可修复后重跑）。")
        sys.exit(1)
    if not mark_done(topic):
        log(f"[错误] 发布成功但选题 #{topic['num']} 标记「已完成」失败。")
        sys.exit(1)
    log(f"[标记] 选题 #{topic['num']} 已改为「已完成」")
    log(f"[完成] 文章URL: https://www.hxo-lcr.cn/{slug}.html")

    # 4) 可选：接着发海外
    if also_intl:
        publish_intl(dry_run)
    return 0


def main():
    ap = argparse.ArgumentParser(description="HXO 每日自动发文（区域感知）")
    ap.add_argument("--region", default="cn", choices=["cn", "intl", "all"],
                    help="发布区域（默认 cn）")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if args.region == "intl":
        publish_intl(args.dry_run)
        return
    if args.region == "all":
        publish_cn(args.dry_run, also_intl=True)
        return

    if not POOL.exists():
        log(f"[错误] 选题池不存在: {POOL}")
        sys.exit(2)
    _, rows = parse_pool()
    topic = next_topic(rows)
    if not topic:
        log("选题池已无「待写」主题，收工。")
        return
    log(f"下一个主题: #{topic['num']} [{topic['priority']}] {topic['topic']}")
    if args.list:
        return
    publish_cn(args.dry_run)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"[致命错误] {e}", file=sys.stderr, flush=True)
        sys.exit(1)

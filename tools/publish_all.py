#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""publish_all.py — HXO 一键发布编排器（纯 Python，替代 n8n）

输入一篇文章的 slug，按顺序执行 6 个动作：
    1. 官网发布      work/n8n/n1_website.py      (git push → Actions 自动构建)
    2. 百度推送      work/n8n/n2_baidu.py
    3. 知乎发布      work/n8n/n3_zhihu.py        (含间隔控制，避免 40362 限流)
    4. Buffer 发布   work/n8n/n4_buffer.py       (LinkedIn + X)
    5. Supabase 同步 work/n8n/n5_supabase.py
    6. 看板刷新      work/n8n/n6_dashboard.py    (本 checkout 可能缺目录，失败不阻塞)

设计：
    - 每个动作独立执行，失败不阻塞后续
    - 所有 stdout/stderr 写入 work/publish_all.log
    - 最后打印汇总报告（每个动作的 状态/耗时/关键结果）
    - 全部动作成功后写 work/published_manifest.json（幂等标记）

用法：
    python tools/publish_all.py --slug article_xxx
    python tools/publish_all.py --slug article_xxx --dry-run
    python tools/publish_all.py --slug article_xxx --no-zhihu-interval
    python tools/publish_all.py --slug article_xxx --only website,baidu
    python tools/publish_all.py --slug article_xxx --skip supabase,dashboard
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent.parent
WORK = REPO / "work"
N8N = WORK / "n8n"
LOG_FILE = WORK / "publish_all.log"
MANIFEST = WORK / "published_manifest.json"
PY = sys.executable

# 动作定义：(key, 显示名, 脚本, 额外参数函数(slug, title) -> list)
ACTIONS = [
    ("website", "官网发布 (git push)", "n1_website.py", lambda s, t: []),
    ("baidu", "百度推送", "n2_baidu.py", lambda s, t: ["--slugs", s]),
    ("zhihu", "知乎发布", "n3_zhihu.py", lambda s, t: ["--slug", s]),
    ("buffer", "Buffer 发布 (LinkedIn+X)", "n4_buffer.py", lambda s, t: ["--title", t]),
    ("supabase", "Supabase 同步", "n5_supabase.py", lambda s, t: ["--slug", s]),
    ("dashboard", "看板刷新", "n6_dashboard.py", lambda s, t: []),
]

# 默认：动作之间的间隔（秒），主要防止知乎/接口限流
DEFAULT_INTERVAL = 3
ZHIHU_PRE_INTERVAL = 10  # 知乎前额外等待（避免 40362）


def log(msg):
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def read_title(slug):
    """从 content/articles/<slug>.md 读 frontmatter title（失败则用 slug）。"""
    import re
    md = REPO / "content" / "articles" / f"{slug}.md"
    if md.exists():
        m = re.search(r"^title:\s*(.+)$", md.read_text(encoding="utf-8"), re.MULTILINE)
        if m:
            return m.group(1).strip().strip('"').strip("'")
    return slug


def run_action(key, name, script, args, dry_run):
    """执行单个 wrapper，返回 (ok, detail, parsed_json)。"""
    cmd = [PY, str(N8N / script)] + args
    env = dict(os.environ)
    if dry_run:
        env["HXO_DRY_RUN"] = "1"

    log(f"--- 动作 [{key}] {name} 开始 ---")
    log(f"    cmd: {' '.join(cmd)}" + ("  (HXO_DRY_RUN=1)" if dry_run else ""))
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True,
                           encoding="utf-8", errors="ignore", timeout=900, env=env)
        out, err, rc = r.stdout or "", r.stderr or "", r.returncode
    except subprocess.TimeoutExpired:
        out, err, rc = "", "timeout after 900s", 1
    dur = time.time() - t0

    if out.strip():
        for ln in out.rstrip().splitlines():
            log(f"    | {ln}")
    if err.strip():
        for ln in err.rstrip().splitlines():
            log(f"    ! {ln}")

    # 解析最后一行 JSON 契约
    parsed = {}
    for ln in reversed((out or "").splitlines()):
        ln = ln.strip()
        if ln.startswith("{"):
            try:
                parsed = json.loads(ln)
                break
            except Exception:
                continue

    ok = rc == 0 and parsed.get("ok", True)
    detail = summarize(key, parsed, rc)
    log(f"--- 动作 [{key}] {name} 结束: {'成功' if ok else '失败'} ({dur:.1f}s) {detail} ---")
    return ok, detail, parsed, dur


def summarize(key, parsed, rc):
    if not parsed:
        return f"exit={rc}"
    p = dict(parsed)
    p.pop("ok", None)
    # 精简：只保留关键字段
    for k in ("new", "raw", "results"):
        if k in p and k == "results":
            p[k] = [{"channel": x.get("channel", "")[:8], "ok": x.get("ok")} for x in p[k]]
        elif k in p:
            p.pop(k)
    return json.dumps(p, ensure_ascii=False)


def load_manifest():
    if MANIFEST.exists():
        try:
            return json.loads(MANIFEST.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"published": []}


def save_manifest(data):
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def mark_published(slug, title, results):
    m = load_manifest()
    have = {p.get("slug"): p for p in m.get("published", [])}
    zhihu_url = ""
    for item in results:
        key, ok, _detail, _dur = item[0], item[1], item[2], item[3]
        parsed = item[4] if len(item) > 4 else {}
        if key == "zhihu" and ok:
            zhihu_url = parsed.get("url", "") if isinstance(parsed, dict) else ""
    have[slug] = {
        "slug": slug, "title": title, "note": "publish_all",
        "zhihu_url": zhihu_url,
        "published_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    m["published"] = list(have.values())
    save_manifest(m)


# 默认跳过 dashboard：本 checkout 缺 dashboard_data/ 目录，运行必报错
DEFAULT_SKIP = {"dashboard"}


def main():
    ap = argparse.ArgumentParser(description="HXO 一键发布编排器")
    ap.add_argument("--slug", required=True, help="文章 slug，如 article_xxx")
    ap.add_argument("--dry-run", action="store_true", help="只验证编排，不实际发布")
    ap.add_argument("--only", default="", help="只跑指定动作（逗号分隔）")
    ap.add_argument("--skip", default="", help="跳过指定动作（逗号分隔；dashboard 默认已跳过）")
    ap.add_argument("--include-dashboard", action="store_true",
                    help="显式启用 dashboard 动作（默认跳过，因本 checkout 缺 dashboard_data/）")
    ap.add_argument("--interval", type=int, default=DEFAULT_INTERVAL,
                    help=f"动作间隔秒数（默认 {DEFAULT_INTERVAL}）")
    ap.add_argument("--no-zhihu-interval", action="store_true",
                    help="知乎前不做额外等待")
    args = ap.parse_args()

    slug = args.slug
    if not (REPO / "content" / "articles" / f"{slug}.md").exists():
        log(f"[错误] 找不到文章: content/articles/{slug}.md")
        sys.exit(2)

    title = read_title(slug)
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    skip = {x.strip() for x in args.skip.split(",") if x.strip()}
    # dashboard 默认跳过（可 --include-dashboard 启用）
    if not args.include_dashboard:
        skip |= DEFAULT_SKIP

    log("=" * 70)
    log(f"publish_all.py  文章={slug}  标题={title}")
    log(f"模式={'DRY-RUN（不实际发布）' if args.dry_run else 'REAL'}"
        f"  only={sorted(only) or '全部'}  skip={sorted(skip) or '无'}")
    log("=" * 70)

    results = []
    order = [a for a in ACTIONS
             if (not only or a[0] in only) and a[0] not in skip]

    for idx, (key, name, script, argfn) in enumerate(order):
        if idx > 0:
            time.sleep(args.interval)
        if key == "zhihu" and not args.no_zhihu_interval and not args.dry_run:
            log(f"    [限流控制] 知乎前等待 {ZHIHU_PRE_INTERVAL}s ...")
            time.sleep(ZHIHU_PRE_INTERVAL)

        script_path = N8N / script
        if not script_path.exists():
            log(f"--- 动作 [{key}] {name}: 脚本缺失 {script}，跳过 ---")
            results.append((key, False, "script missing", 0.0, {}))
            continue

        ok, detail, parsed, dur = run_action(
            key, name, script, argfn(slug, title), args.dry_run)
        results.append((key, ok, detail, dur, parsed))

    # ---- 汇总报告 ----
    log("")
    log("=" * 70)
    log("汇总报告")
    log("=" * 70)
    n_ok = sum(1 for item in results if item[1])
    for item in results:
        key, ok, detail, dur = item[0], item[1], item[2], item[3]
        flag = "OK  " if ok else "FAIL"
        log(f"  [{flag}] {key:<10} {dur:>6.1f}s  {detail}")
    log(f"  合计: {n_ok}/{len(results)} 成功")
    log("=" * 70)

    # 幂等标记：仅当非 dry-run 且所有动作成功
    all_ok = results and all(item[1] for item in results)
    if args.dry_run:
        log("DRY-RUN 完成，未实际发布，未写 manifest。")
    elif all_ok:
        mark_published(slug, title, results)
        log(f"已写入 {MANIFEST.relative_to(REPO)}")
        log("全部动作成功。")
    else:
        log("存在失败动作，未写 manifest（可修复后重跑，幂等）。")

    sys.exit(0 if all_ok or args.dry_run else 1)


if __name__ == "__main__":
    main()

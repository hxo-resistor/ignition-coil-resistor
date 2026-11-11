#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""publish_all.py — 一键发布编排器（国内外分组版）

按 slug 依次执行各平台发布动作，现拆分为国内组（CN）与海外组（INTL）：
    CN   官网(git push) / 百度 / 知乎 / Supabase / 看板
    INTL LinkedIn / X (Twitter)   —— 内容来自 content_factory 生成的 social JSON

用法：
    python tools/publish_all.py --slug article_xxx --dry-run
    python tools/publish_all.py --slug article_xxx --region cn
    python tools/publish_all.py --slug article_xxx --region intl
    python tools/publish_all.py --slug article_xxx --region all
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import content_factory  # noqa: E402

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

# Buffer channel ID（查询于 2026-10-08）
LINKEDIN_CHANNEL = "6a9ecd14cd8b9c702c228760"
X_CHANNEL = "6ac640c66a5c39ccb63fed31"

# 默认：动作之间间隔（秒），防知乎/接口限流
DEFAULT_INTERVAL = 3
ZHIHU_PRE_INTERVAL = 10

# 知乎开关：false 时整条流水线跳过知乎（被禁言，待解封后人工评估）
ZHIHU_ENABLED = False


def log(msg):
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception as e:
        print(f"[warn] 写发布日志失败 {LOG_FILE}: {e}", file=sys.stderr, flush=True)


def _intl_args(slug, key):
    """海外动作参数：从 content_factory 生成的 social JSON 取英文文案。"""
    social = content_factory.load_social(slug)
    if not social:
        return None
    title_en = social.get("title_en", slug)
    if key == "linkedin":
        return ["--title", title_en, "--text", social["linkedin"], "--channels", LINKEDIN_CHANNEL]
    if key == "x":
        return ["--title", title_en, "--text", social["x"], "--channels", X_CHANNEL]
    return None


# 动作定义：(key, 显示名, 脚本, 额外参数函数(slug, title) -> list|None)
CN_ACTIONS = [
    ("website", "官网发布 (git push)", "n1_website.py", lambda s, t: []),
    ("baidu", "百度推送", "n2_baidu.py", lambda s, t: ["--slugs", s]),
    ("zhihu", "知乎发布", "n3_zhihu.py", lambda s, t: ["--slug", s]),
    ("wechat", "微信公众号草稿", "n9_wechat.py", lambda s, t: ["--slug", s]),
    ("xiaohongshu", "小红书笔记", "n10_xiaohongshu.py", lambda s, t: ["--slug", s]),
    ("supabase", "Supabase 同步", "n5_supabase.py", lambda s, t: ["--slug", s]),
    ("dashboard", "看板刷新", "n6_dashboard.py", lambda s, t: []),
]

INTL_ACTIONS = [
    ("linkedin", "LinkedIn 发布", "n4_buffer.py", lambda s, t: _intl_args(s, "linkedin")),
    ("x", "X (Twitter) 发布", "n4_buffer.py", lambda s, t: _intl_args(s, "x")),
    ("medium", "Medium 发布", "n8_medium.py", lambda s, t: ["--slug", s]),
]


def read_title(slug):
    """从 content/articles/<slug>.md 读 frontmatter title（失败则用 slug）。"""
    md = REPO / "content" / "articles" / f"{slug}.md"
    if md.exists():
        m = re.search(r"^title:\s*(.+)$", md.read_text(encoding="utf-8"), re.MULTILINE)
        if m:
            return m.group(1).strip().strip('"').strip("'")
    return slug


def read_meta(slug):
    """从 content/articles/<slug>.md 读 (title, description, date)。"""
    md = REPO / "content" / "articles" / f"{slug}.md"
    title, desc, date = slug, "", ""
    if md.exists():
        text = md.read_text(encoding="utf-8")
        m = re.search(r"^title:\s*(.+)$", text, re.MULTILINE)
        if m:
            title = m.group(1).strip().strip('"').strip("'")
        m = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
        if m:
            desc = m.group(1).strip().strip('"').strip("'")
        m = re.search(r"^date:\s*(.+)$", text, re.MULTILINE)
        if m:
            date = m.group(1).strip().strip('"').strip("'")
    return title, desc, date


_TAG_RULES = [
    (("aec", "iso", "certification", "compliance", "rohs", "appliance"), "认证标准"),
    (("burn", "melt", "troubleshoot", "diagnos", "failure", "fault"), "故障排查"),
    (("select", "selection", "rating", "derating", "sizing", "calculation"), "选型指南"),
    (("comparison", "vs", "substitution"), "国产替代"),
    (("test", "measure", "multimeter", "oscilloscope", "verify"), "测试方法"),
    (("install", "assembly", "guide"), "安装指南"),
]


def derive_tag(slug):
    low = slug.lower()
    for keys, tag in _TAG_RULES:
        if any(k in low for k in keys):
            return tag
    return "技术解析"


def update_articles_index(slug):
    import re
    idx_path = REPO / "articles.html"
    if not idx_path.exists():
        return False, "articles.html 不存在，跳过索引更新"
    raw = idx_path.read_bytes()
    newline = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8")
    link = f'./{slug}.html'
    if link in text or f"hxo-lcr.cn/{slug}.html" in text:
        return False, "索引已存在该文章，无需更新"
    title, desc, date = read_meta(slug)
    if not date:
        date = dt.date.today().isoformat()
    tag = derive_tag(slug)
    desc = desc.replace("<", "&lt;").replace(">", "&gt;")
    title = title.replace("<", "&lt;").replace(">", "&gt;")
    anchor = re.search(r'(<h2 class="section-title">\s*技术文章\s*</h2>\s*<div class="article-list">)', text)
    if not anchor:
        return False, "未找到技术文章列表锚点，跳过索引更新"
    block = (
        f'{newline}        <div class="article-item">{newline}'
        f'            <span class="tag">{tag}</span>{newline}'
        f'            <h3><a href="{link}">{title}</a></h3>{newline}'
        f'            <p>{desc}</p>{newline}'
        f'            <div class="meta">{date}</div>{newline}'
        f'        </div>{newline}'
    )
    insert_at = anchor.end()
    text = text[:insert_at] + block + text[insert_at:]
    idx_path.write_bytes(text.encode("utf-8"))
    return True, f"已插入 articles.html 索引 ({tag} · {date})"


def update_sitemap(slug):
    sm_path = REPO / "sitemap.xml"
    if not sm_path.exists():
        return False, "sitemap.xml 不存在，跳过"
    raw = sm_path.read_bytes()
    newline = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8")
    loc = f"https://www.hxo-lcr.cn/{slug}.html"
    if loc in text or f"<loc>./{slug}.html</loc>" in text:
        return False, "sitemap 已存在该文章，无需更新"
    if "</urlset>" not in text:
        return False, "sitemap.xml 缺少 </urlset> 结尾，跳过"
    _, _, date = read_meta(slug)
    if not date:
        date = dt.date.today().isoformat()
    block = (
        f'{newline}  <url>{newline}'
        f'    <loc>{loc}</loc>{newline}'
        f'    <lastmod>{date}</lastmod>{newline}'
        f'    <changefreq>weekly</changefreq>{newline}'
        f'    <priority>0.7</priority>{newline}'
        f'  </url>{newline}'
    )
    text = text.replace("</urlset>", block + "</urlset>")
    sm_path.write_bytes(text.encode("utf-8"))
    return True, f"已追加 sitemap.xml ({loc} · {date})"


def run_action(key, name, script, args, dry_run):
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
    for k in ("new", "raw"):
        if k in p:
            p.pop(k)
    if "results" in p:
        p["results"] = [{"channel": x.get("channel", "")[:8], "ok": x.get("ok")} for x in p["results"]]
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
        parsed = item[4] if len(item) > 4 else {}
        if item[0] == "zhihu" and item[1]:
            zhihu_url = parsed.get("url", "") if isinstance(parsed, dict) else ""
    have[slug] = {
        "slug": slug, "title": title, "note": "publish_all",
        "zhihu_url": zhihu_url,
        "published_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    m["published"] = list(have.values())
    save_manifest(m)


def main():
    ap = argparse.ArgumentParser(description="HXO 一键发布编排器（国内外分组）")
    ap.add_argument("--slug", required=True, help="文章 slug，如 article_xxx")
    ap.add_argument("--dry-run", action="store_true", help="只验证编排，不实际发布")
    ap.add_argument("--region", default="all", choices=["cn", "intl", "all"],
                    help="发布区域：cn 国内 / intl 海外 / all 全部（默认 all）")
    ap.add_argument("--only", default="", help="只跑指定动作（逗号分隔）")
    ap.add_argument("--skip", default="", help="跳过指定动作（逗号分隔）")
    ap.add_argument("--include-dashboard", action="store_true", help="显式启用 dashboard 动作")
    ap.add_argument("--interval", type=int, default=DEFAULT_INTERVAL)
    ap.add_argument("--no-zhihu-interval", action="store_true")
    args = ap.parse_args()

    slug = args.slug
    if not (REPO / "content" / "articles" / f"{slug}.md").exists():
        log(f"[错误] 找不到文章: content/articles/{slug}.md")
        sys.exit(2)

    title = read_title(slug)
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    skip = {x.strip() for x in args.skip.split(",") if x.strip()}

    # 区域 → 动作集合
    if args.region == "cn":
        actions = CN_ACTIONS
    elif args.region == "intl":
        actions = INTL_ACTIONS
    else:
        actions = CN_ACTIONS + INTL_ACTIONS

    # dashboard 默认跳过（可 --include-dashboard 启用）
    if not args.include_dashboard:
        skip |= {"dashboard"}
    # 知乎开关关闭时，强制跳过知乎
    zhihu_on = ZHIHU_ENABLED or os.environ.get("HXO_ZHIHU_ENABLED") == "1"
    if not zhihu_on:
        skip |= {"zhihu"}
        if "zhihu" in only:
            only.discard("zhihu")
            if not only:
                skip |= {a[0] for a in actions}

    log("=" * 70)
    log(f"publish_all.py  文章={slug}  标题={title}  区域={args.region}")
    log(f"模式={'DRY-RUN（不实际发布）' if args.dry_run else 'REAL'}"
        f"  only={sorted(only) or '全部'}  skip={sorted(skip) or '无'}")
    log("=" * 70)

    # 索引/sitemap 同步：仅 CN 的 website 动作前执行
    do_index = (args.region in ("cn", "all")) and (not only or "website" in only) and "website" not in skip
    if do_index and not args.dry_run:
        changed, note = update_articles_index(slug)
        log(f"[索引] {note}" + (" → 由 website 动作一并提交" if changed else ""))
        changed, note = update_sitemap(slug)
        log(f"[sitemap] {note}" + (" → 由 website 动作一并提交" if changed else ""))
    elif do_index and args.dry_run:
        log("[索引] dry-run：将同步 articles.html 索引（未执行）")
        log("[sitemap] dry-run：将追加 sitemap.xml（未执行）")

    # 海外动作前置校验：social JSON 必须存在
    if args.region in ("intl", "all"):
        social = content_factory.load_social(slug)
        if not social:
            log(f"[警告] 未找到海外文案 work/social/{slug}.json，跳过海外动作")
            skip |= {a[0] for a in INTL_ACTIONS}

    results = []
    order = [a for a in actions
             if (not only or a[0] in only) and a[0] not in skip]

    for idx, (key, name, script, argfn) in enumerate(order):
        if idx > 0:
            time.sleep(args.interval)
        if key == "zhihu" and not args.no_zhihu_interval and not args.dry_run:
            log(f"    [限流控制] 知乎前等待 {ZHIHU_PRE_INTERVAL}s ...")
            time.sleep(ZHIHU_PRE_INTERVAL)

        argvals = argfn(slug, title)
        if argvals is None:
            log(f"--- 动作 [{key}] {name}: 参数缺失，跳过 ---")
            results.append((key, False, "missing content", 0.0, {}))
            continue

        script_path = N8N / script
        if not script_path.exists():
            log(f"--- 动作 [{key}] {name}: 脚本缺失 {script}，跳过 ---")
            results.append((key, False, "script missing", 0.0, {}))
            continue

        ok, detail, parsed, dur = run_action(key, name, script, argvals, args.dry_run)
        results.append((key, ok, detail, dur, parsed))

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

    all_ok = results and all(item[1] for item in results)
    if args.dry_run:
        log("DRY-RUN 完成，未实际发布，未写 manifest。")
    elif all_ok:
        if args.region in ("cn", "all"):
            mark_published(slug, title, results)
            log(f"已写入 {MANIFEST.relative_to(REPO)}")
        log("全部动作成功。")
    else:
        log("存在失败动作，未写 manifest（可修复后重跑，幂等）。")

    sys.exit(0 if all_ok or args.dry_run else 1)


if __name__ == "__main__":
    main()

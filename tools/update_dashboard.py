#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""update_dashboard.py — HXO 运营看板自动刷新

作用（每天 09:00 由 Windows 任务计划 HXO_Dashboard_Refresh 调用）：
  1. 从实测数据源重新统计运营数据：
     - 官网文章数：仓库根 article_*.html
     - 发布记录 / 各平台累计 / 最近一次自动发布任务结果：work/publish_all.log
     - 已发布清单：work/published_manifest.json
     - 知乎发布明细：work/zhihu_published.log
     - 选题池剩余：work/topic_pool.md（状态列）
     - Supabase content_packages（只读，网络不可用时优雅降级）
  2. 生成 dashboard_data/*.json（机器可读）
  3. 生成仓库根 dashboard.html（静态看板页，push 后经 GitHub Pages 上线）
  4. 智能提交：仅当 dashboard.html / dashboard_data 内容实际变化时才
     git add + commit + push，避免每天空提交。

安全红线：
  - 只写 dashboard_data/、dashboard.html、logs/dashboard_errors.log；
    不修改任何发布脚本、不碰文章内容。
  - 不新增任何密钥；Supabase 读取复用 n5_supabase.py 的 anon key（可被环境变量覆盖）。

用法：
    python tools/update_dashboard.py                # 生成 + 智能提交推送
    python tools/update_dashboard.py --dry-run      # 只生成并打印，不写文件、不提交
    python tools/update_dashboard.py --no-push      # 生成并写文件，但不 git 提交
    python tools/update_dashboard.py --no-supabase  # 跳过 Supabase 读取
"""

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---------------------------------------------------------------------------
# 路径
# ---------------------------------------------------------------------------
TOOLS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(TOOLS, ".."))          # 仓库根（GitHub Pages 部署根）
WORK = os.path.join(REPO, "work")
DASH = os.path.join(REPO, "dashboard_data")
HTML_OUT = os.path.join(REPO, "dashboard.html")
LOG_DIR = os.path.join(REPO, "logs")
ERR_LOG = os.path.join(LOG_DIR, "dashboard_errors.log")

PUBLISH_LOG = os.path.join(WORK, "publish_all.log")
MANIFEST = os.path.join(WORK, "published_manifest.json")
ZHIHU_LOG = os.path.join(WORK, "zhihu_published.log")
TOPIC_POOL = os.path.join(WORK, "topic_pool.md")

SITE_BASE = "https://www.hxo-lcr.cn"
SITE_HOST = "www.hxo-lcr.cn"

# Supabase（只读；与 work/n8n/n5_supabase.py 保持一致的默认值，可用环境变量覆盖）
SUPA_URL = os.environ.get("SUPABASE_URL", "https://whnmtkrmvqayfhpmrdiq.supabase.co")
SUPA_KEY = os.environ.get(
    "SUPABASE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indobm10a3JtdnFheWZocG1yZGlxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcwNDU5MjEsImV4cCI6MjEwMjYyMTkyMX0."
    "MHTyZOGYd5KvnwGclq2oI2xua2rbXPHJ--AGmZOGhoE",
)

PLATFORM_KEYS = ["website", "baidu", "zhihu", "buffer", "supabase"]

ALERT_STATE = os.path.join(LOG_DIR, "dashboard_alert_state.json")
ALERT_THRESHOLD = 3


def now():
    return dt.datetime.now()


def now_iso():
    return now().astimezone().isoformat(timespec="seconds")


def log_error(msg):
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        ts = now().strftime("%Y-%m-%d %H:%M:%S")
        with open(ERR_LOG, "a", encoding="utf-8") as fh:
            fh.write(f"[{ts}] {msg}\n")
    except Exception:
        pass


def record_run_result(success, detail=""):
    """记录连续失败次数；达到阈值时向错误日志追加醒目告警（无外部通道，仅落盘）。"""
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        state = {}
        if os.path.exists(ALERT_STATE):
            try:
                state = json.loads(read_text(ALERT_STATE) or "{}")
            except Exception:
                state = {}
        if success:
            state["consecutive_failures"] = 0
            state["last_success"] = now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            n = int(state.get("consecutive_failures", 0)) + 1
            state["consecutive_failures"] = n
            state["last_failure"] = now().strftime("%Y-%m-%d %H:%M:%S")
            state["last_detail"] = detail
            if n >= ALERT_THRESHOLD:
                with open(ERR_LOG, "a", encoding="utf-8") as fh:
                    fh.write(f"[{now().strftime('%Y-%m-%d %H:%M:%S')}] "
                             f"[ALERT] 看板刷新已连续失败 {n} 次：{detail}\n")
        with open(ALERT_STATE, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(state, fh, ensure_ascii=False, indent=2)
    except Exception:
        pass


def read_text(path, limit=None):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read(limit) if limit else fh.read()
    except Exception:
        return ""


def run_git(args, check=False):
    try:
        r = subprocess.run(["git"] + args, cwd=REPO, capture_output=True,
                           text=True, encoding="utf-8", errors="ignore", timeout=180)
        return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
    except Exception as e:
        return 1, "", str(e)


# ---------------------------------------------------------------------------
# 数据源解析
# ---------------------------------------------------------------------------
def count_official_articles():
    import glob
    return len(glob.glob(os.path.join(REPO, "article_*.html")))


def official_article_titles():
    import glob
    items = []
    for f in sorted(glob.glob(os.path.join(REPO, "article_*.html"))):
        head = read_text(f, 20000)
        title = ""
        m = re.search(r"<h1[^>]*>(.*?)</h1>", head, re.S)
        if m:
            title = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        if not title:
            m2 = re.search(r"<title>(.*?)</title>", head, re.S)
            title = (m2.group(1).strip() if m2 else os.path.basename(f))
        items.append({
            "file": os.path.basename(f),
            "title": title,
            "url": f"{SITE_BASE}/{os.path.basename(f)}",
        })
    return items


def load_manifest():
    try:
        return json.loads(read_text(MANIFEST) or "{}")
    except Exception:
        return {}


def parse_zhihu_log():
    """解析 zhihu_published.log → 最近记录（时间倒序）。"""
    items = []
    for line in read_text(ZHIHU_LOG).splitlines():
        parts = line.split("\t")
        if len(parts) >= 4:
            items.append({
                "published_at": parts[0].strip(),
                "slug": parts[1].strip(),
                "title": parts[2].strip(),
                "url": parts[3].strip(),
            })
    items.sort(key=lambda x: x["published_at"], reverse=True)
    return items


RUN_HDR = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s+publish_all\.py\s+文章=(\S+)\s+标题=(.*)$")
ACTION_END = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s+--- 动作 \[(\w+)\][^-]*结束:\s*(成功|失败)\s*\(([\d.]+)s\)")
TOTAL = re.compile(r"合计:\s*(\d+)/(\d+)\s*成功")


def parse_publish_log():
    """解析 publish_all.log → 运行记录列表（按时间顺序）。

    每次运行 = 从 `publish_all.py 文章=` 起到下一个运行头/文件末尾。
    提取：slug、title、起始时间、各动作结果、成功数/总数、整体是否成功。
    """
    runs = []
    cur = None
    total_all = 0
    for line in read_text(PUBLISH_LOG).splitlines():
        m = RUN_HDR.match(line)
        if m:
            if cur:
                runs.append(cur)
            cur = {
                "started_at": m.group(1),
                "slug": m.group(2),
                "title": m.group(3).strip(),
                "actions": {},
                "ok_count": None,
                "total": None,
            }
            total_all += 1
            continue
        if cur is None:
            continue
        a = ACTION_END.match(line)
        if a:
            key, status, dur = a.group(2), a.group(3), float(a.group(4))
            cur["actions"][key] = {"status": status, "duration": dur}
            continue
        t = TOTAL.search(line)
        if t:
            cur["ok_count"] = int(t.group(1))
            cur["total"] = int(t.group(2))
    if cur:
        runs.append(cur)

    for r in runs:
        vals = [v["status"] for v in r["actions"].values()]
        if r["ok_count"] is not None and r["total"]:
            r["success"] = r["ok_count"] == r["total"] and r["total"] > 0
        else:
            r["success"] = bool(vals) and all(v == "成功" for v in vals)
    return runs


def platform_cumulative(runs):
    """各平台累计发布数（按成功发布的不同 slug 去重计数，避免重试重复计）。"""
    seen = {k: set() for k in PLATFORM_KEYS}
    for r in runs:
        for k, v in r["actions"].items():
            if v["status"] == "成功":
                seen.setdefault(k, set()).add(r["slug"])
    return {k: len(seen.get(k, ())) for k in PLATFORM_KEYS}


def recent_publish_records(runs, days=7):
    """最近 N 天的发布记录（每个 slug 取最后一次运行）。"""
    cutoff = now() - dt.timedelta(days=days)
    latest = {}
    for r in runs:
        try:
            ts = dt.datetime.strptime(r["started_at"], "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
        if ts < cutoff:
            continue
        prev = latest.get(r["slug"])
        if prev is None or r["started_at"] >= prev["started_at"]:
            latest[r["slug"]] = r

    records = []
    for r in sorted(latest.values(), key=lambda x: x["started_at"], reverse=True):
        platforms = []
        for k in PLATFORM_KEYS:
            v = r["actions"].get(k)
            if v and v["status"] == "成功":
                platforms.append(k)
        records.append({
            "date": r["started_at"][:10],
            "time": r["started_at"],
            "slug": r["slug"],
            "title": r["title"],
            "platforms": platforms,
            "success": r["success"],
            "summary": f"{r['ok_count']}/{r['total']} 成功" if r["total"] else "",
        })
    return records


def last_task_result(runs):
    if not runs:
        return None
    r = runs[-1]
    return {
        "time": r["started_at"],
        "slug": r["slug"],
        "title": r["title"],
        "success": r["success"],
        "ok_count": r["ok_count"],
        "total": r["total"],
        "actions": [
            {"key": k, "status": v["status"], "duration": v["duration"]}
            for k, v in r["actions"].items()
        ],
    }


TOPIC_ROW = re.compile(r"^\|\s*(\d+)\s*\|.*\|\s*(待写|已完成|暂停)\s*\|\s*$")


def parse_topic_pool():
    text = read_text(TOPIC_POOL)
    counts = {"待写": 0, "已完成": 0, "暂停": 0}
    rows = []
    for line in text.splitlines():
        m = TOPIC_ROW.match(line.strip())
        if not m:
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        status = m.group(2)
        if status in counts:
            counts[status] += 1
        rows.append({
            "id": cols[0] if cols else "",
            "topic": cols[1] if len(cols) > 1 else "",
            "priority": cols[2] if len(cols) > 2 else "",
            "product": cols[3] if len(cols) > 3 else "",
            "platforms": cols[4] if len(cols) > 4 else "",
            "status": status,
        })
    remaining = counts["待写"]
    return {"remaining": remaining, "counts": counts, "total": len(rows),
            "next": next((r["topic"] for r in rows if r["status"] == "待写"), "")}


def fetch_supabase(limit=200):
    """只读拉取 content_packages（失败返回 None，看板显示不可用）。"""
    import urllib.request
    url = f"{SUPA_URL}/rest/v1/content_packages?select=date,product_id,title,status&order=date.desc&limit={limit}"
    req = urllib.request.Request(url, headers={
        "apikey": SUPA_KEY,
        "Authorization": f"Bearer {SUPA_KEY}",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data if isinstance(data, list) else []
    except Exception as e:
        log_error(f"supabase fetch failed: {e}")
        return None


# ---------------------------------------------------------------------------
# 组装数据
# ---------------------------------------------------------------------------
def build_data(use_supabase=True):
    runs = parse_publish_log()
    manifest = load_manifest()
    official_count = count_official_articles()
    topics = parse_topic_pool()
    recent = recent_publish_records(runs, 7)
    cum = platform_cumulative(runs)
    last = last_task_result(runs)

    zhihu_items = parse_zhihu_log()
    published_slugs = [p.get("slug") for p in manifest.get("published", [])]

    supa_data = fetch_supabase() if use_supabase else None

    # —— 现有看板保留：内容总览 ——
    linkedin_count = cum.get("buffer", 0)
    zhihu_count = len(zhihu_items) if zhihu_items else cum.get("zhihu", 0)
    overview = {
        "last_updated": now_iso(),
        "platforms": {
            "官网": official_count,
            "知乎": zhihu_count,
            "LinkedIn": linkedin_count,
            "B2B待发": 12,
        },
        "labels": {
            "官网": "官网 B2B 文章",
            "知乎": "知乎已发布",
            "LinkedIn": "Buffer/LinkedIn 帖子",
            "B2B待发": "B2B 平台待手动上架",
        },
        "unit": "篇",
        "total": official_count + zhihu_count + linkedin_count + 12,
    }

    # —— 平台状态 ——
    def platform_status():
        def st(count, ok_label):
            return {"status": "ok", "detail": ok_label}
        rows = [
            {"name": "官网", "status": "ok", "icon": "✅",
             "detail": f"GitHub Pages 已上线（{official_count} 篇）", "url": SITE_BASE},
            {"name": "百度", "status": "ok", "icon": "✅",
             "detail": f"API 推送 {cum.get('baidu', 0)} 次成功", "url": SITE_BASE},
            {"name": "LinkedIn", "status": "ok" if cum.get("buffer") else "warn",
             "icon": "✅" if cum.get("buffer") else "⚠️",
             "detail": f"Buffer 队列（{linkedin_count} 条）", "url": "https://bufferapp.com"},
            {"name": "知乎", "status": "ok" if zhihu_count else "warn",
             "icon": "✅" if zhihu_count else "⚠️",
             "detail": f"已发 {zhihu_count} 篇", "url": "https://zhuanlan.zhihu.com"},
            {"name": "B2B", "status": "manual", "icon": "📄",
             "detail": "需企业认证，手动发布", "url": "https://www.11467.com"},
        ]
        return {"last_updated": now_iso(), "platforms": rows}

    # —— 发布日历（最近 30 天记录，按 slug+日期去重，保留最后一次） ——
    def calendar():
        seen = {}
        for r in runs:
            try:
                ts = dt.datetime.strptime(r["started_at"], "%Y-%m-%d %H:%M:%S")
            except Exception:
                continue
            if ts < now() - dt.timedelta(days=30):
                continue
            key = (r["started_at"][:10], r["slug"])
            prev = seen.get(key)
            if prev is None or r["started_at"] >= prev["started_at"]:
                seen[key] = r
        items = []
        for r in sorted(seen.values(), key=lambda x: x["started_at"]):
            items.append({
                "date": r["started_at"][:10],
                "platform": "多平台" if r["success"] else "部分失败",
                "title": r["title"],
                "url": f"{SITE_BASE}/{r['slug']}.html",
            })
        return {"last_updated": now_iso(), "published": items[-60:]}

    # —— 运营动态（新增） ——
    def operations_activity():
        # 各平台累计：官网取实有文章数；其余取自动化成功发布的去重 slug 数
        cum_rows = []
        for k in PLATFORM_KEYS:
            if k == "website":
                cnt = official_count
            elif k == "zhihu" and zhihu_count:
                cnt = zhihu_count
            else:
                cnt = cum.get(k, 0)
            cum_rows.append({"key": k, "name": _platform_name(k), "count": cnt})
        return {
            "last_updated": now_iso(),
            "window_days": 7,
            "recent_records": recent,
            "platform_cumulative": cum_rows,
            "last_task": last,
            "topic_pool": topics,
            "supabase": {
                "available": supa_data is not None,
                "count": len(supa_data) if supa_data is not None else None,
            },
            "totals": {
                "runs_logged": len(runs),
                "published_manifest": len(published_slugs),
                "official_articles": official_count,
            },
        }

    meta = {
        "last_updated": now_iso(),
        "version": "2.0",
        "source": "tools/update_dashboard.py",
        "official_article_count": official_count,
        "published_count": len(published_slugs),
        "topic_remaining": topics["remaining"],
    }

    return {
        "meta.json": meta,
        "overview.json": overview,
        "platform_status.json": platform_status(),
        "calendar.json": calendar(),
        "operations.json": operations_activity(),
    }


def _platform_name(key):
    return {
        "website": "官网",
        "baidu": "百度",
        "zhihu": "知乎",
        "buffer": "LinkedIn+X",
        "supabase": "Supabase",
    }.get(key, key)


# ---------------------------------------------------------------------------
# 生成静态看板 HTML
# ---------------------------------------------------------------------------
def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def render_html(data):
    meta = data["meta.json"]
    ov = data["overview.json"]
    ps = data["platform_status.json"]
    cal = data["calendar.json"]
    ops = data["operations.json"]

    def ov_cards():
        cards = []
        for k, v in ov["platforms"].items():
            cards.append(
                f'<div class="card"><div class="num">{v}</div>'
                f'<div class="lbl">{_esc(ov["labels"].get(k, k))}</div></div>')
        cards.append(
            f'<div class="card"><div class="num">{ov["total"]}</div>'
            f'<div class="lbl">累计发布（{_esc(ov["unit"])}）</div></div>')
        return "\n".join(cards)

    def ps_rows():
        rows = []
        for p in ps["platforms"]:
            rows.append(
                f'<tr><td>{p["icon"]} {_esc(p["name"])}</td>'
                f'<td>{_esc(p["detail"])}</td>'
                f'<td><a href="{_esc(p["url"])}" target="_blank" rel="noopener">访问</a></td></tr>')
        return "\n".join(rows)

    def cum_rows():
        rows = []
        for p in ops["platform_cumulative"]:
            rows.append(f'<tr><td>{_esc(p["name"])}</td><td class="num-cell">{p["count"]}</td></tr>')
        return "\n".join(rows)

    def recent_rows():
        if not ops["recent_records"]:
            return '<tr><td colspan="5" class="empty">最近 7 天暂无发布记录</td></tr>'
        rows = []
        for r in ops["recent_records"]:
            plats = "、".join(_platform_name(k) for k in r["platforms"]) or "—"
            flag = "✅" if r["success"] else "⚠️"
            rows.append(
                f'<tr><td>{_esc(r["date"])}</td>'
                f'<td><a href="{SITE_BASE}/{_esc(r["slug"])}.html" target="_blank" rel="noopener">{_esc(r["title"])}</a></td>'
                f'<td>{_esc(plats)}</td>'
                f'<td>{flag} {_esc(r["summary"])}</td>'
                f'<td>{_esc(r["slug"])}</td></tr>')
        return "\n".join(rows)

    def last_task_block():
        lt = ops["last_task"]
        if not lt:
            return '<p class="empty">暂无自动发布任务记录</p>'
        flag = ('<span class="badge ok">成功</span>' if lt["success"]
                else '<span class="badge fail">失败</span>')
        acts = "".join(
            f'<span class="chip {"ok" if a["status"] == "成功" else "fail"}">'
            f'{_esc(_platform_name(a["key"]))} {a["status"]} {a["duration"]}s</span>'
            for a in lt["actions"])
        return (
            f'<div class="last-task">{flag}'
            f'<div class="lt-title">{_esc(lt["title"])}</div>'
            f'<div class="lt-meta">执行时间：{_esc(lt["time"])} ｜ 结果：'
            f'{lt["ok_count"]}/{lt["total"]} 成功 ｜ slug：{_esc(lt["slug"])}</div>'
            f'<div class="chips">{acts}</div></div>')

    tp = ops["topic_pool"]
    sup = ops["supabase"]
    sup_txt = (f'已连接，content_packages 共 {sup["count"]} 条'
               if sup["available"] else "本次未连接（网络不可用，已跳过）")

    generated = meta["last_updated"]

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="index,follow">
<title>HXO 运营看板 | {_esc(SITE_HOST)}</title>
<style>
  :root{{--bg:#0f172a;--card:#1e293b;--line:#334155;--fg:#e2e8f0;--mut:#94a3b8;--acc:#38bdf8;--ok:#22c55e;--warn:#f59e0b;--fail:#ef4444}}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.6 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}}
  .wrap{{max-width:1080px;margin:0 auto;padding:32px 20px 64px}}
  h1{{font-size:22px;margin:0 0 4px}}
  h2{{font-size:16px;margin:32px 0 12px;padding-left:10px;border-left:3px solid var(--acc)}}
  .sub{{color:var(--mut);font-size:13px;margin-bottom:24px}}
  .cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}}
  .card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px}}
  .card .num{{font-size:28px;font-weight:700;color:var(--acc)}}
  .card .lbl{{color:var(--mut);font-size:12px;margin-top:4px}}
  table{{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden;font-size:13px}}
  th,td{{padding:9px 12px;text-align:left;border-bottom:1px solid var(--line)}}
  th{{background:#0b1220;color:var(--mut);font-weight:600}}
  tr:last-child td{{border-bottom:none}}
  a{{color:var(--acc);text-decoration:none}} a:hover{{text-decoration:underline}}
  .empty{{color:var(--mut);text-align:center;padding:16px}}
  .num-cell{{font-weight:700;color:var(--acc)}}
  .two{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
  @media(max-width:700px){{.two{{grid-template-columns:1fr}}}}
  .badge{{display:inline-block;padding:2px 10px;border-radius:999px;font-size:12px;font-weight:600}}
  .badge.ok{{background:rgba(34,197,94,.15);color:var(--ok)}}
  .badge.fail{{background:rgba(239,68,68,.15);color:var(--fail)}}
  .last-task{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px}}
  .lt-title{{font-size:15px;font-weight:600;margin:8px 0 4px}}
  .lt-meta{{color:var(--mut);font-size:12px}}
  .chips{{margin-top:10px;display:flex;flex-wrap:wrap;gap:6px}}
  .chip{{font-size:12px;padding:2px 8px;border-radius:6px;background:#0b1220;border:1px solid var(--line)}}
  .chip.ok{{color:var(--ok)}} .chip.fail{{color:var(--fail)}}
  .pool{{display:flex;gap:24px;flex-wrap:wrap;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px}}
  .pool .big{{font-size:32px;font-weight:700;color:var(--warn)}}
  footer{{margin-top:40px;color:var(--mut);font-size:12px;border-top:1px solid var(--line);padding-top:16px}}
</style>
</head>
<body>
<div class="wrap">
  <h1>HXO 运营看板</h1>
  <div class="sub">数据自动生成于 {_esc(generated)} ｜ 数据源：publish_all.log、published_manifest.json、topic_pool.md、Supabase ｜ 每日 09:00 自动刷新</div>

  <h2>内容总览</h2>
  <div class="cards">
{ov_cards()}
  </div>

  <h2>最近 7 天发布记录</h2>
  <table>
    <thead><tr><th>日期</th><th>标题</th><th>平台</th><th>结果</th><th>slug</th></tr></thead>
    <tbody>
{recent_rows()}
    </tbody>
  </table>

  <h2>运营动态</h2>
  <div class="two">
    <div>
      <h3 style="font-size:14px;color:var(--mut)">各平台累计发布数</h3>
      <table><tbody>
{cum_rows()}
      </tbody></table>
      <p style="color:var(--mut);font-size:12px;margin-top:6px">官网=实有文章数；百度/知乎/LinkedIn+X/Supabase=自动化成功发布（按 slug 去重）</p>
    </div>
    <div>
      <h3 style="font-size:14px;color:var(--mut)">选题池</h3>
      <div class="pool">
        <div><div class="big">{tp["remaining"]}</div><div class="lbl" style="color:var(--mut);font-size:12px">剩余待写</div></div>
        <div><div class="big" style="color:var(--ok)">{tp["counts"]["已完成"]}</div><div style="color:var(--mut);font-size:12px">已完成</div></div>
        <div><div class="big" style="color:var(--mut)">{tp["counts"]["暂停"]}</div><div style="color:var(--mut);font-size:12px">暂停</div></div>
        <div style="flex:1;min-width:180px"><div style="color:var(--mut);font-size:12px">下一个待写</div><div>{_esc(tp["next"]) or "—"}</div></div>
      </div>
      <p style="color:var(--mut);font-size:12px;margin-top:8px">Supabase：{_esc(sup_txt)}</p>
    </div>
  </div>

  <h2>最近一次自动发布任务结果</h2>
{last_task_block()}

  <h2>平台状态</h2>
  <table>
    <thead><tr><th>平台</th><th>状态</th><th>链接</th></tr></thead>
    <tbody>
{ps_rows()}
    </tbody>
  </table>

  <h2>发布日历（近 30 天）</h2>
  <table>
    <thead><tr><th>日期</th><th>平台</th><th>标题</th></tr></thead>
    <tbody>
{_calendar_rows(cal)}
    </tbody>
  </table>

  <footer>
    数据条目：任务记录 {ops["totals"]["runs_logged"]} 次 ｜ manifest {ops["totals"]["published_manifest"]} 篇 ｜ 官网文章 {ops["totals"]["official_articles"]} 篇<br>
    <a href="{SITE_BASE}">返回官网</a> ｜ <a href="mailto:resistor@hxo-lcr.cn">resistor@hxo-lcr.cn</a>
  </footer>
</div>
</body>
</html>
"""
    return html


def _calendar_rows(cal):
    items = cal.get("published", [])
    if not items:
        return '<tr><td colspan="3" class="empty">近 30 天暂无发布</td></tr>'
    rows = []
    for it in sorted(items, key=lambda x: x.get("date", ""), reverse=True):
        rows.append(
            f'<tr><td>{_esc(it.get("date", ""))}</td>'
            f'<td>{_esc(it.get("platform", ""))}</td>'
            f'<td><a href="{_esc(it.get("url", ""))}" target="_blank" rel="noopener">{_esc(it.get("title", ""))}</a></td></tr>')
    return "\n".join(rows)


# ---------------------------------------------------------------------------
# 写文件 + 智能提交
# ---------------------------------------------------------------------------
def _business_fingerprint(data):
    """业务数据指纹：排除所有 last_updated 时间戳，仅用会变化的内容计算哈希。

    这样在数据无变化时，重新生成的结果与上次逐字节一致（时间戳沿用旧值），
    智能提交即可判定“无变化”而跳过。
    """
    import hashlib

    def strip(obj):
        if isinstance(obj, dict):
            return {k: strip(v) for k, v in obj.items() if k != "last_updated"}
        if isinstance(obj, list):
            return [strip(x) for x in obj]
        return obj

    payload = json.dumps(strip(data), ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def freeze_timestamps(data, fingerprint):
    """若业务指纹与上次一致，则沿用上次的 last_updated，保持输出稳定。"""
    import glob
    prev = None
    meta_path = os.path.join(DASH, "meta.json")
    if os.path.exists(meta_path):
        try:
            meta_path_data = json.loads(read_text(meta_path) or "{}")
            prev = meta_path_data
        except Exception:
            prev = None
    if prev and prev.get("content_hash") == fingerprint:
        ts = prev.get("last_updated")
        if ts:
            for name, obj in data.items():
                if isinstance(obj, dict) and "last_updated" in obj:
                    obj["last_updated"] = ts
            data["meta.json"]["last_updated"] = ts
            return True, ts
    return False, data["meta.json"]["last_updated"]


def write_outputs(data, html):
    os.makedirs(DASH, exist_ok=True)
    for name, obj in data.items():
        with open(os.path.join(DASH, name), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=2)
    with open(HTML_OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)


def changed_files():
    """返回 dashboard.html / dashboard_data/ 中相对 HEAD 有变化的路径。"""
    rc, out, _ = run_git(["status", "--porcelain", "--", "dashboard.html", "dashboard_data"])
    files = []
    if rc == 0:
        for line in out.splitlines():
            p = line[3:].strip().strip('"')
            if p:
                files.append(p)
    return files


def smart_commit_push(dry_run=False, no_push=False):
    """智能提交。返回 True 表示“无变化或不提交也算正常完成”，False 仅表示真实失败。"""
    files = changed_files()
    if not files:
        print("⏭  看板内容无变化，跳过提交（避免空 commit）。")
        return True

    if dry_run:
        print("[dry-run] 将提交以下文件：", files)
        return True

    rc, _, err = run_git(["add", "dashboard.html", "dashboard_data"])
    if rc != 0:
        log_error(f"git add failed: {err}")
        print("❌ git add 失败：", err)
        return False

    msg = f"Auto-refresh dashboard {now().strftime('%Y%m%d %H%M')}"
    rc, out, err = run_git(["commit", "-m", msg])
    if rc != 0:
        log_error(f"git commit failed: {err or out}")
        print("❌ git commit 失败：", err or out)
        return False
    print("✅ 已提交：", msg)

    if no_push:
        print("(已跳过 push：--no-push)")
        return True

    rc, out, err = run_git(["push", "origin", "main"])
    if rc != 0:
        log_error(f"git push failed: {err or out}")
        print("❌ git push 失败：", err or out)
        return False
    print("🚀 已推送 origin main，GitHub Pages 将自动部署。")
    return True


def main():
    ap = argparse.ArgumentParser(description="HXO 运营看板自动刷新")
    ap.add_argument("--dry-run", action="store_true", help="只生成打印，不写文件不提交")
    ap.add_argument("--no-push", action="store_true", help="生成并写文件，但不提交推送")
    ap.add_argument("--no-supabase", action="store_true", help="跳过 Supabase 读取")
    args = ap.parse_args()

    try:
        data = build_data(use_supabase=not args.no_supabase)
        fingerprint = _business_fingerprint(data)
        data["meta.json"]["content_hash"] = fingerprint
        reused, ts = freeze_timestamps(data, fingerprint)
        html = render_html(data)
    except Exception as e:
        log_error(f"build failed: {e!r}")
        record_run_result(False, f"build failed: {e!r}")
        print("❌ 生成看板失败：", e)
        sys.exit(1)

    ops = data["operations.json"]
    print(f"官网文章 {ops['totals']['official_articles']} 篇 ｜ "
          f"最近7天发布 {len(ops['recent_records'])} 条 ｜ "
          f"选题池剩余 {ops['topic_pool']['remaining']} ｜ "
          f"最近任务 {'成功' if (ops['last_task'] or {}).get('success') else '无/失败'}")
    print(f"数据指纹 {fingerprint} ｜ "
          + ("数据无变化，沿用上次时间戳" if reused else "检测到数据变化"))

    if args.dry_run:
        print("[dry-run] 未写文件。dashboard.html 长度:", len(html))
        print("[dry-run] 变化检测:", changed_files() or "无（当前工作区看板未生成/未变化）")
        return

    try:
        write_outputs(data, html)
    except Exception as e:
        log_error(f"write failed: {e!r}")
        record_run_result(False, f"write failed: {e!r}")
        print("❌ 写文件失败：", e)
        sys.exit(1)

    print(f"✅ 已生成 dashboard.html 与 {len(data)} 个 JSON。")
    try:
        ok = smart_commit_push(no_push=args.no_push)
        record_run_result(bool(ok))
        if not ok:
            print("⚠️  提交/推送未完成（详见 logs/dashboard_errors.log）。")
            sys.exit(1)
    except Exception as e:
        log_error(f"commit/push failed: {e!r}")
        record_run_result(False, f"commit/push failed: {e!r}")
        print("❌ 提交/推送异常：", e)
        sys.exit(1)


if __name__ == "__main__":
    main()

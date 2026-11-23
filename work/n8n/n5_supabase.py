"""N5: Sync one article into Supabase table content_packages.

Mirrors publish_b2b_package_v2.py: same URL/key/proxy, same payload shape
(content_md stores the full HTML). Idempotent on (slug): one row per article.

Args:
    --slug <article_slug>
    --product-id <product_id>   (optional; default derived from slug + title)
    --date YYYY-MM-DD           (optional; default today)
Env:
    SUPABASE_URL / SUPABASE_KEY override defaults
    HXO_PROXY (default http://127.0.0.1:7897)
Output: {"ok": true, "action": "supabase", "http": 201}
"""
import argparse
import datetime as dt
import os
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from _common import REPO, emit, fail, request_with_fallback  # noqa: E402

SUPA_URL = os.environ.get("SUPABASE_URL", "https://whnmtkrmvqayfhpmrdiq.supabase.co")
SUPA_KEY = os.environ.get("SUPABASE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indobm10"
    "a3JtdnFheWZocG1yZGlxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcwNDU5MjEsImV4cCI6MjEw"
    "MjYyMTkyMX0.MHTyZOGYd5KvnwGclq2oI2xua2rbXPHJ--AGmZOGhoE")
PROXY = os.environ.get("HXO_PROXY", "http://127.0.0.1:7897")
ENDPOINT = SUPA_URL + "/rest/v1/content_packages"
HEADERS = {"apikey": SUPA_KEY, "Authorization": "Bearer " + SUPA_KEY,
           "Content-Type": "application/json"}

# 产品线映射：按优先级匹配 slug + title 的规范化文本；未命中返回 "unknown"（不猜）
#
# 顺序即优先级（命中即返回第一个）：
#   1) 明确型号系列（ig-c/ig-f/ig-s、rxf）——必须排在泛化关键词前，
#      否则 "ignition" 会把 IG-F/IG-S 误判成 ig-c。
#   2) HVW 高压/绕线/泄放/医疗高压脉冲线——含 AED/除颤/影像设备关键词。
#   3) 泛化关键词（"点火"/"ignition"）兜底到 ig-c。
#
# 关键词分两类：
#   - 普通子串（CJK 词、长英文词）：直接做 `in` 匹配。
#   - 短英文缩写（ct/dr/mri/xray…）：必须词边界匹配。裸子串会误伤，
#     例如 "ct" 命中 "product"，"dr" 命中 "drain"/"drive"。见 WORD_BOUNDED。
PRODUCT_MAP = [
    # --- 明确型号系列（最具体，优先匹配）---
    (("ig-c", "ig_c", "igc", "陶瓷芯", "ceramic"), "ig-c-ceramic"),
    (("ig-f", "ig_f", "igf", "玻纤", "glassfiber", "glass-fiber"), "ig-f-glassfiber"),
    (("ig-s", "ig_s", "igs", "实心"), "ig-s-ceramic"),
    # --- 温度保险/OTP ---
    (("rxf", "otp", "fuse", "温度保险", "thermal-fuse", "thermal fuse"), "rxf-otp-1w"),
    # --- HVW 高压/绕线/泄放/医疗高压脉冲/影像设备 ---
    (("hvw", "wirewound", "wire-wound", "bleeder", "ev-pile", "bleed",
      "braking", "brake", "泄放", "制动",
      "除颤", "aed", "defibrillator", "医疗",
      "x光", "x射线", "影像", "核磁"), "hv-wirewound"),
    # --- 泛化关键词兜底 ---
    (("点火", "ignition"), "ig-c-ceramic"),
]

# 需要词边界匹配的短英文缩写 → 所属 product_id。
# 用 (?<![a-z0-9])...(?![a-z0-9]) 保证 "ct" 不会命中 "product"、"dr" 不会命中 "drain"。
WORD_BOUNDED_MAP = [
    ((r"x-?ray",), "hv-wirewound"),
    (("ct",), "hv-wirewound"),        # CT 设备
    (("dr",), "hv-wirewound"),        # DR 数字摄影
    (("mri",), "hv-wirewound"),       # MRI/核磁
]


def guess_product_id(*texts):
    """按 slug + title 识别产品线；命中不了返回 unknown（绝不臆测成 av）。"""
    blob = " ".join(t for t in texts if t).lower().replace("_", "-")
    for kws, pid in PRODUCT_MAP:
        if any(k in blob for k in kws):
            return pid
    for kws, pid in WORD_BOUNDED_MAP:
        for k in kws:
            if re.search(rf"(?<![a-z0-9]){k}(?![a-z0-9])", blob):
                return pid
    return "unknown"


def find_html(slug):
    for name in (f"{slug}.html",):
        p = REPO / name
        if p.exists():
            return p
    return None


PENDING_LOG = REPO / "work" / "supabase_pending.log"


def _record_pending(slug, error):
    """把同步失败的 slug 记入待补发清单，待网络恢复后可重跑补发。"""
    try:
        PENDING_LOG.parent.mkdir(parents=True, exist_ok=True)
        ts = dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        with PENDING_LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"{ts} {slug} {error}\n")
    except Exception:
        pass


def _request(method, url, **kwargs):
    """代理池轮换 + 直连兜底（代理自愈），全部失败抛出最后的网络异常。"""
    return request_with_fallback(method, url, **kwargs)


def _skip_unreachable(a, product_id, stage, exc):
    """Supabase 网络不可达时软跳过：不阻断流水线，slug 进待补发清单。"""
    print(f"[warn] Supabase 网络不可达（{stage}）：{exc}", file=sys.stderr)
    _record_pending(a.slug, f"unreachable:{type(exc).__name__}")
    emit({"ok": True, "action": "supabase", "skipped": True,
          "reason": "supabase_unreachable", "slug": a.slug,
          "product_id": product_id, "error": str(exc)})


def _pending_slugs():
    """从待补发清单读取去重后的 slug（保持首次出现顺序）。"""
    if not PENDING_LOG.exists():
        return []
    slugs, seen = [], set()
    for ln in PENDING_LOG.read_text(encoding="utf-8").splitlines():
        parts = ln.split()
        if len(parts) >= 2 and parts[1] not in seen:
            seen.add(parts[1])
            slugs.append(parts[1])
    return slugs


def _clear_pending(slugs):
    """把已成功补发的 slug 从待补发清单移除。"""
    if not PENDING_LOG.exists():
        return
    done = set(slugs)
    remaining = []
    for ln in PENDING_LOG.read_text(encoding="utf-8").splitlines():
        parts = ln.split()
        if len(parts) >= 2 and parts[1] in done:
            continue
        remaining.append(ln)
    PENDING_LOG.write_text("\n".join(remaining) + ("\n" if remaining else ""),
                           encoding="utf-8")


def _sync_one(slug):
    """同步单篇（补发用）。返回 (ok, reason)。网络异常向上抛出。"""
    html_path = find_html(slug)
    if not html_path:
        return False, "html not found"
    content = html_path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"<title>(.*?)</title>", content, re.S)
    title = m.group(1).strip() if m else slug
    product_id = guess_product_id(slug, title)
    payload = {"date": dt.date.today().isoformat(), "product_id": product_id,
               "title": title, "slug": slug, "content_md": content,
               "source": "n8n_workflow", "status": "published",
               "sync_status": "synced"}
    q = _request("get", ENDPOINT, params={"slug": "eq." + slug, "select": "id"},
                 headers=HEADERS, timeout=30)
    if q.status_code == 200 and q.json():
        return True, "row exists"
    r = _request("post", ENDPOINT, json=payload,
                 headers=dict(HEADERS, Prefer="return=minimal"), timeout=60)
    if r.status_code in (200, 201, 204):
        return True, "synced"
    return False, f"http {r.status_code}"


def backfill():
    """补发待补发清单：逐条同步，网络恢复即逐步清空；网络异常则停止保留剩余。"""
    slugs = _pending_slugs()
    if not slugs:
        emit({"ok": True, "action": "supabase_backfill", "pending": 0,
              "note": "no pending"})
        return
    done, failed = [], []
    for s in slugs:
        try:
            ok, reason = _sync_one(s)
        except requests.exceptions.RequestException as e:
            print(f"[backfill] 网络仍不可达，停止补发：{e}", file=sys.stderr)
            break
        if ok:
            done.append(s)
            print(f"[backfill] {s}: {reason}")
        else:
            failed.append({"slug": s, "reason": reason})
    if done:
        _clear_pending(done)
    emit({"ok": True, "action": "supabase_backfill", "done": done,
          "failed": failed, "remaining": len(_pending_slugs())})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default="")
    ap.add_argument("--product-id", default="")
    ap.add_argument("--date", default="")
    ap.add_argument("--backfill", action="store_true", help="补发待补发清单中的 slug")
    a = ap.parse_args()

    if a.backfill:
        backfill()
        return

    if not a.slug:
        fail("supabase", "--slug required (或使用 --backfill)")

    html_path = find_html(a.slug)
    if not html_path:
        fail("supabase", f"html not found: {a.slug}.html (run website publish first)")

    content = html_path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"<title>(.*?)</title>", content, re.S)
    title = m.group(1).strip() if m else a.slug
    date = a.date or dt.date.today().isoformat()
    product_id = a.product_id or guess_product_id(a.slug, title)

    payload = {"date": date, "product_id": product_id, "title": title,
               "slug": a.slug, "content_md": content, "source": "n8n_workflow",
               "status": "published", "sync_status": "synced"}

    if os.environ.get("HXO_DRY_RUN") == "1":
        emit({"ok": True, "action": "supabase", "dry_run": True,
              "date": date, "product_id": product_id, "slug": a.slug,
              "title": title, "content_chars": len(content)})
        return

    # idempotency: skip if this slug already exists (one row per article)
    try:
        q = _request("get", ENDPOINT, params={"slug": "eq." + a.slug, "select": "id"},
                     headers=HEADERS, timeout=30)
        if q.status_code == 200 and q.json():
            emit({"ok": True, "action": "supabase", "skipped": True,
                  "reason": "row exists", "slug": a.slug, "product_id": product_id})
            return
    except requests.exceptions.RequestException as e:
        _skip_unreachable(a, product_id, "existence check", e)
        return
    except Exception as e:
        print(f"[warn] existence check failed: {e}", file=sys.stderr)

    try:
        r = _request("post", ENDPOINT, json=payload,
                     headers=dict(HEADERS, Prefer="return=minimal"), timeout=60)
    except requests.exceptions.RequestException as e:
        _skip_unreachable(a, product_id, "post", e)
        return
    except Exception as e:
        fail("supabase", f"request failed: {e}")

    emit({"ok": r.status_code in (200, 201, 204), "action": "supabase",
          "http": r.status_code, "slug": a.slug, "title": title,
          "product_id": product_id})
    if r.status_code not in (200, 201, 204):
        sys.exit(1)


if __name__ == "__main__":
    main()

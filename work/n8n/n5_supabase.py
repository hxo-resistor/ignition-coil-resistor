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
from pathlib import Path

import requests

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from _common import REPO, emit, fail  # noqa: E402

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
PRODUCT_MAP = [
    (("rxf", "otp", "fuse"), "rxf-otp-1w"),
    (("ig_c", "ig-c", "igc"), "ig-c-ceramic"),
    (("ig_f", "ig-f", "igf"), "ig-f-glassfiber"),
    (("ig_s", "ig-s", "igs"), "ig-s-ceramic"),
    (("hvw", "wirewound", "bleeder", "ev_pile", "bleed"), "hv-wirewound"),
]


def guess_product_id(*texts):
    """按 slug + title 识别产品线；命中不了返回 unknown（绝不臆测成 av）。"""
    blob = " ".join(t for t in texts if t).lower().replace("_", "-")
    for kws, pid in PRODUCT_MAP:
        if any(k in blob for k in kws):
            return pid
    return "unknown"


def find_html(slug):
    for name in (f"{slug}.html",):
        p = REPO / name
        if p.exists():
            return p
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--product-id", default="")
    ap.add_argument("--date", default="")
    a = ap.parse_args()

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
        q = requests.get(ENDPOINT, params={"slug": "eq." + a.slug, "select": "id"},
                         headers=HEADERS, proxies={"http": PROXY, "https": PROXY}, timeout=30)
        if q.status_code == 200 and q.json():
            emit({"ok": True, "action": "supabase", "skipped": True,
                  "reason": "row exists", "slug": a.slug, "product_id": product_id})
            return
    except Exception as e:
        print(f"[warn] existence check failed: {e}", file=sys.stderr)

    try:
        r = requests.post(ENDPOINT, json=payload,
                          headers=dict(HEADERS, Prefer="return=minimal"),
                          proxies={"http": PROXY, "https": PROXY}, timeout=60)
    except Exception as e:
        fail("supabase", f"request failed: {e}")

    emit({"ok": r.status_code in (200, 201, 204), "action": "supabase",
          "http": r.status_code, "slug": a.slug, "title": title,
          "product_id": product_id})
    if r.status_code not in (200, 201, 204):
        sys.exit(1)


if __name__ == "__main__":
    main()

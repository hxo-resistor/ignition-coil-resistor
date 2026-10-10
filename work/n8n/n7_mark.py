"""N7: Mark an article as published in work/published_manifest.json (idempotency).

Call once per article after all publish actions succeed, so the next discovery
run skips it.

Args:
    --slug <article_slug>  (repeatable)
    --url  <url>           (optional; matched to slug position)
    --note TEXT
Output: {"ok": true, "action": "mark", "total": N}
"""
import argparse
import datetime as dt
import os
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from _common import emit, load_manifest, save_manifest  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", nargs="+", required=True)
    ap.add_argument("--url", nargs="*", default=[])
    ap.add_argument("--note", default="n8n")
    a = ap.parse_args()

    if os.environ.get("HXO_DRY_RUN") == "1":
        emit({"ok": True, "action": "mark", "dry_run": True, "slugs": a.slug})
        return

    m = load_manifest()
    have = {p.get("slug"): p for p in m.get("published", [])}
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for i, slug in enumerate(a.slug):
        url = a.url[i] if i < len(a.url) else have.get(slug, {}).get("url", "")
        have[slug] = {"slug": slug, "url": url, "note": a.note, "published_at": ts}
    m["published"] = list(have.values())
    save_manifest(m)
    emit({"ok": True, "action": "mark", "total": len(m["published"])})


if __name__ == "__main__":
    main()

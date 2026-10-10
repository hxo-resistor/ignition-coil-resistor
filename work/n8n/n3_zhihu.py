"""N3: Publish one article to Zhihu via the existing full-auto script.

Delegates to work/publish_zhihu.py (sub-task 1.1). Reuses browser-data/zhihu
session (no QR after first login).

Args:
    --slug <article_slug>
Env:
    HXO_DRY_RUN=1  -> fill but do not click publish
Output: {"ok": ..., "action": "zhihu", "slug": ..., "url": "..."}
"""
import argparse
import os
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from _common import emit, fail, run, PY  # noqa: E402

DRY = os.environ.get("HXO_DRY_RUN") == "1"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    a = ap.parse_args()

    cmd = f'"{PY}" work/publish_zhihu.py --slug {a.slug}'
    if DRY:
        cmd += " --dry-run"
    rc, out, err = run(cmd, timeout=600)
    print(out)
    if err:
        print(err, file=sys.stderr)

    url = ""
    for line in out.splitlines():
        if "文章URL:" in line:
            url = line.split("文章URL:")[-1].strip()
    ok = rc == 0 and (url or DRY)
    emit({"ok": ok, "action": "zhihu", "slug": a.slug, "url": url,
          "exit_code": rc})
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()

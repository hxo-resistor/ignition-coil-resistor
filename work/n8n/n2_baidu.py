"""N2: Push article URLs to Baidu (主动推送).

Reuses the exact API the legacy pipeline used. Reads token/proxy from env with
the same defaults as publish_b2b_package_v2.py so behavior is unchanged.

Env:
    BAIDU_API_TOKEN  (default: the value already in the repo)
    HXO_PROXY        (default: http://127.0.0.1:7897)
Args:
    --urls URL [URL ...]   explicit URLs, OR
    --slugs slug [slug ...]  build URLs as https://www.hxo-lcr.cn/<slug>.html
Output: {"ok": true, "action": "baidu", "success": N, "remain": M}
"""
import argparse
import os
import sys

import requests

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from _common import emit, fail  # noqa: E402

TOKEN = os.environ.get("BAIDU_API_TOKEN", "StZI77pKI1nwhzFp")
PROXY = os.environ.get("HXO_PROXY", "http://127.0.0.1:7897")
SITE = "www.hxo-lcr.cn"
BASE = "https://www.hxo-lcr.cn"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--urls", nargs="*", default=[])
    ap.add_argument("--slugs", nargs="*", default=[])
    a = ap.parse_args()

    urls = list(a.urls)
    urls += [f"{BASE}/{s}.html" for s in a.slugs]
    urls.append(f"{BASE}/articles.html")
    if not urls:
        fail("baidu", "no urls")

    api = f"http://data.zz.baidu.com/urls?site={SITE}&token={TOKEN}"
    headers = {"User-Agent": "hxobot", "Content-Type": "text/plain; charset=utf-8"}

    if os.environ.get("HXO_DRY_RUN") == "1":
        emit({"ok": True, "action": "baidu", "dry_run": True, "urls": urls})
        return

    try:
        r = requests.post(api, data="\n".join(urls), headers=headers,
                          proxies={"http": PROXY, "https": PROXY}, timeout=30)
        res = r.json()
    except Exception as e:
        fail("baidu", f"request failed: {e}")

    emit({"ok": res.get("success", 0) > 0, "action": "baidu",
          "success": res.get("success", 0), "remain": res.get("remain", 0),
          "not_same_site": res.get("not_same_site", []),
          "raw": res, "http": r.status_code})


if __name__ == "__main__":
    main()

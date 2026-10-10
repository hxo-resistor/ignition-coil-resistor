"""N4: Push a post to Buffer (LinkedIn + X).

Delegates to the existing buffer_auto_linkedin_fixed.py logic but as an
importable call so we can target multiple channels. Falls back to invoking the
legacy script for LinkedIn if import fails.

Args:
    --title TEXT
    --text  TEXT            (optional; default builds a short template)
    --channels id [id ...] (optional; default: env BUFFER_CHANNEL_IDS or LinkedIn)
Env:
    BUFFER_TOKEN        (default: value already in repo)
    BUFFER_CHANNEL_IDS  comma-separated channel ids
Output: {"ok": true, "action": "buffer", "results": [{channel, post_id}]}
"""
import argparse
import os
import sys

import requests

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from _common import emit, fail  # noqa: E402

TOKEN = os.environ.get("BUFFER_TOKEN", "34cyqxAOzZHdZwFrBFy6Ou89lwONFsuihkJ2RCOGAZm")
# LinkedIn + X (Twitter). 查询于 2026-10-08 via Buffer API:
#   linkedin  余良-...a219419   6a9ecd14cd8b9c702c228760
#   twitter   HXOResistofiy     6ac640c66a5c39ccb63fed31
DEFAULT_CHANNELS = os.environ.get(
    "BUFFER_CHANNEL_IDS",
    "6a9ecd14cd8b9c702c228760,6ac640c66a5c39ccb63fed31",
)

QUERY = """
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on PostActionSuccess { post { id status } }
    ... on MutationError { message }
  }
}
"""


# X (Twitter) channel id — needs a <=280 char version
TWITTER_CHANNEL_ID = "6ac640c66a5c39ccb63fed31"


def build_texts(title):
    """Return {channel_id: text}. LinkedIn gets the long post; X gets a 280-char cut."""
    long_text = (
        f"{title}\n\n"
        "HXO Resistor — AEC-Q200 automotive-grade ignition-coil suppression "
        "resistors. 7-15 day delivery, 30-50% lower cost vs Japanese brands.\n"
        "Contact: resistor@hxo-lcr.cn | www.hxo-lcr.cn\n"
        "#Resistor #AutomotiveElectronics #OEM #ChinaSupplier"
    )
    short_text = (
        f"{title}\n\n"
        "AEC-Q200 ignition-coil suppression resistors. 7-15 day delivery.\n"
        "resistor@hxo-lcr.cn | www.hxo-lcr.cn\n"
        "#Resistor #AutomotiveElectronics"
    )
    if len(short_text) > 280:
        short_text = short_text[:277] + "..."
    return long_text, short_text


def create_post(channel_id, text):
    variables = {"input": {
        "channelId": channel_id,
        "text": text,
        "schedulingType": "automatic",
        "mode": "addToQueue",
    }}
    r = requests.post("https://api.buffer.com/graphql",
                      headers={"Authorization": f"Bearer {TOKEN}",
                               "Content-Type": "application/json"},
                      json={"query": QUERY, "variables": variables}, timeout=30)
    data = r.json()
    if "errors" in data:
        return {"channel": channel_id, "ok": False, "error": data["errors"]}
    d = data.get("data", {}).get("createPost", {})
    if "post" in d:
        return {"channel": channel_id, "ok": True, "post_id": d["post"]["id"],
                "status": d["post"]["status"]}
    return {"channel": channel_id, "ok": False, "error": d.get("message", d)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--text", default="")
    ap.add_argument("--channels", nargs="*", default=[])
    a = ap.parse_args()

    title = a.title
    long_text, short_text = build_texts(title)
    channels = a.channels or [c.strip() for c in DEFAULT_CHANNELS.split(",") if c.strip()]

    def text_for(ch):
        if a.text:
            return a.text
        return short_text if ch == TWITTER_CHANNEL_ID else long_text

    if os.environ.get("HXO_DRY_RUN") == "1":
        emit({"ok": True, "action": "buffer", "dry_run": True,
              "channels": channels,
              "text_preview": {c: text_for(c)[:80] for c in channels}})
        return

    results = [create_post(c, text_for(c)) for c in channels]
    ok = any(r["ok"] for r in results)
    emit({"ok": ok, "action": "buffer", "results": results})
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()

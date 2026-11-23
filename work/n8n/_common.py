"""Shared helpers for n8n Execute-Command wrapper scripts.

Contract: every wrapper prints a single JSON object on the last line:
    {"ok": true, "action": "...", ...}
so n8n can parse the result with a Code node (or just pass through).
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WORK = REPO / "work"
ARTICLES = REPO / "content" / "articles"
MANIFEST = WORK / "published_manifest.json"

PY = sys.executable


# ---------------------------------------------------------------------------
# 代理自愈：HXO_PROXY_POOL（逗号分隔）轮换 + 直连兜底 + 粘性记住可用代理。
# 网络失败（TLS 重置/超时）时自动切备用代理重试，直到成功，而不是默默放弃。
# ---------------------------------------------------------------------------
def _proxy_pool():
    env = os.environ.get("HXO_PROXY_POOL", "").strip()
    pool = [p.strip() for p in env.split(",") if p.strip()] if env else []
    if not pool:
        pool = ["http://127.0.0.1:7897", "http://127.0.0.1:7891"]
    return pool


_LAST_GOOD_PROXY = None


def request_with_fallback(method, url, retries=2, **kwargs):
    """按「最近可用代理 → 代理池 → 直连」顺序轮换请求，直到成功。

    返回 requests.Response；全部失败抛最后一个网络异常。
    kwargs（timeout/headers/json/params 等）原样透传给 requests.request。
    """
    global _LAST_GOOD_PROXY
    import requests

    order = []
    if _LAST_GOOD_PROXY:
        order.append(_LAST_GOOD_PROXY)
    for p in _proxy_pool():
        if p not in order:
            order.append(p)
    order.append(None)  # 直连兜底

    last = None
    for proxy in order:
        proxies = {"http": proxy, "https": proxy} if proxy else None
        for _ in range(retries):
            try:
                r = requests.request(method, url, proxies=proxies, **kwargs)
                if proxy:
                    _LAST_GOOD_PROXY = proxy
                return r
            except requests.exceptions.RequestException as e:
                last = e
                time.sleep(1)
    _LAST_GOOD_PROXY = None
    raise last


def emit(payload):
    """Print a single JSON line and exit."""
    payload.setdefault("ok", True)
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def fail(action, error):
    emit({"ok": False, "action": action, "error": str(error)})
    sys.exit(1)


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


def run(cmd, timeout=600, cwd=None):
    """Run a command, return (rc, stdout, stderr)."""
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            encoding="utf-8", errors="ignore",
            cwd=str(cwd or REPO), timeout=timeout,
        )
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        return 1, "", f"timeout after {timeout}s"
    except Exception as e:
        return 1, "", str(e)


def article_title(md_path):
    """Pull the frontmatter title from an article markdown file."""
    import re
    text = Path(md_path).read_text(encoding="utf-8")
    m = re.search(r"^title:\s*(.+)$", text, re.MULTILINE)
    if not m:
        return Path(md_path).stem
    return m.group(1).strip().strip('"').strip("'")


def wait_for_index_lock(max_tries=3, wait=5.0):
    """Wait for a stale/concurrent git index.lock to clear.

    Returns (ok, message). If .git/index.lock exists, wait `wait` seconds and
    retry up to `max_tries` times. ok=False means the lock never cleared.
    """
    lock = REPO / ".git" / "index.lock"
    for attempt in range(1, max_tries + 1):
        if not lock.exists():
            return True, f"index.lock free (attempt {attempt})"
        if attempt == max_tries:
            return False, f"index.lock 仍存在（重试 {max_tries} 次后放弃）"
        print(f"[lock] 检测到 {lock}，等待 {wait:g}s 后重试 ({attempt}/{max_tries}) ...",
              flush=True)
        time.sleep(wait)
    return False, "index.lock 未清除"

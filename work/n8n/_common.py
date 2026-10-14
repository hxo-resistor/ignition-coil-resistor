"""Shared helpers for n8n Execute-Command wrapper scripts.

Contract: every wrapper prints a single JSON object on the last line:
    {"ok": true, "action": "...", ...}
so n8n can parse the result with a Code node (or just pass through).
"""
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WORK = REPO / "work"
ARTICLES = REPO / "content" / "articles"
MANIFEST = WORK / "published_manifest.json"

PY = sys.executable


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

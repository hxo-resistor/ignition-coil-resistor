"""Shared helpers for n8n Execute-Command wrapper scripts.

Contract: every wrapper prints a single JSON object on the last line:
    {"ok": true, "action": "...", ...}
so n8n can parse the result with a Code node (or just pass through).
"""
import json
import subprocess
import sys
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

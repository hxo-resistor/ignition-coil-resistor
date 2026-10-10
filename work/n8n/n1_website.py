"""N1: Publish website = git add content/articles + commit + push origin main.

GitHub Actions (build-and-deploy.yml) then builds Markdown->HTML and deploys
Pages. This script ONLY stages content/articles to avoid sweeping unrelated
files into the auto-commit.

Env:
    HXO_DRY_RUN=1   -> 只报告"计划执行"，不 git add / commit / push（不污染工作区）。
Output: {"ok": true, "action": "website", "commit": "<hash-or-empty>"}
"""
import os
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from _common import REPO, emit, fail, run  # noqa: E402

DRY = os.environ.get("HXO_DRY_RUN") == "1"


def main():
    rc, out, err = run("git status --porcelain content/articles")
    if rc != 0:
        fail("website", f"git status failed: {err}")

    if DRY:
        changed = [ln for ln in out.splitlines() if ln.strip()]
        emit({"ok": True, "action": "website", "dry_run": True, "intended": True,
              "pending_changes": len(changed),
              "note": "计划执行：git add content/articles + commit + push（dry-run 未执行）"})
        return

    if not out.strip():
        emit({"ok": True, "action": "website", "note": "no content changes", "commit": ""})
        return

    rc, _, err = run("git add content/articles")
    if rc != 0:
        fail("website", f"git add failed: {err}")

    rc, _, err = run('git commit -m "Auto-publish content YYYYMMDD"')
    # A commit may legitimately find nothing to commit if only unstaged meta changed
    if rc != 0 and "nothing to commit" not in err:
        fail("website", f"git commit failed: {err}")

    rc, out, _ = run("git log -1 --format=%H")
    commit = out.strip() if rc == 0 else ""

    rc, _, err = run("git push origin main", timeout=300)
    if rc != 0:
        fail("website", f"git push failed: {err}")
    emit({"ok": True, "action": "website", "commit": commit, "pushed": True})


if __name__ == "__main__":
    main()

"""N6: Refresh the TrendFlow dashboard JSON.

Delegates to tools/update_dashboard.py.
Output: {"ok": true, "action": "dashboard"}
"""
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from _common import emit, fail, run, PY  # noqa: E402
import os  # noqa: E402


def main():
    if os.environ.get("HXO_DRY_RUN") == "1":
        emit({"ok": True, "action": "dashboard", "dry_run": True})
        return
    rc, out, err = run(f'"{PY}" tools/update_dashboard.py', timeout=300)
    print(out)
    if rc != 0:
        fail("dashboard", err)
    emit({"ok": True, "action": "dashboard"})


if __name__ == "__main__":
    main()

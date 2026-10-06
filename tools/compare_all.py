#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/compare_all.py — 对 build/ 下所有由 content/articles/*.md 生成的页面逐篇对比，
汇总输出 build/compare_report.md。"""
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent

PILOT = [p.stem for p in sorted((ROOT / "content" / "articles").glob("*.md"))]


def main():
    results = []
    detail = []
    for slug in PILOT:
        r = subprocess.run(
            [sys.executable, "tools/compare_build.py", "--slug", slug,
             "--report", f"build/_cmp_{slug}.md"],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
        )
        out = r.stdout
        ok = r.returncode == 0
        first_line = next((l for l in out.splitlines() if "结果:" in l), "")
        results.append((slug, ok, first_line.strip()))
        detail.append(f"\n\n---\n\n# {slug}\n\n" + out)

    lines = [f"# 阶段2/3 · 对比汇总（共 {len(results)} 篇）\n"]
    passed = sum(1 for _, ok, _ in results if ok)
    lines.append(f"**通过：{passed}/{len(results)} 篇**\n")
    lines.append("| 文章 | 结果 |")
    lines.append("| --- | --- |")
    for slug, ok, res in results:
        mark = "✅" if ok else "❌"
        lines.append(f"| `{slug}` | {mark} {res} |")
    lines.append("".join(detail))

    Path(ROOT / "build" / "compare_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:12]))
    print(f"\n汇总报告：build/compare_report.md")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

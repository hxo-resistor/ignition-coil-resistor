#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""backup_website.py — HXO 官网仓库备份

作用（每周日 22:00 由 Windows 任务计划 "HXO Website Backup" 调用）：
  1. 把 website-repo 的已跟踪文件打包成 zip，存到 backups/。
  2. 文件名带时间戳（backup_YYYYmmdd_HHMMSS.zip），保留最近 N 份，旧的自动清理。
  3. 输出日志追加到 logs/website_backup.log。

安全红线：
  - 只读仓库文件、只写 backups/ 与 logs/。
  - 排除 .git、browser-data（含登录 cookie）、logs、backups 自身、__pycache__。
  - 不新增任何密钥，不联网。

用法：
    python tools/backup_website.py                # 打包 + 清理旧备份
    python tools/backup_website.py --keep 5       # 只保留最近 5 份
    python tools/backup_website.py --dry-run      # 只打印将要打包的内容，不写文件
"""
import argparse
import datetime as dt
import subprocess
import sys
import zipfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent.parent
BACKUPS_DIR = REPO / "backups"
LOG_FILE = REPO / "logs" / "website_backup.log"

EXCLUDE_DIRS = {".git", "browser-data", "logs", "backups", "__pycache__", ".pytest_cache"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}
DEFAULT_KEEP = 10


def log(msg):
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def iter_files():
    """Yield tracked-ish files under REPO, skipping noise dirs."""
    for p in REPO.rglob("*"):
        if not p.is_file():
            continue
        rel_parts = p.relative_to(REPO).parts
        if any(part in EXCLUDE_DIRS for part in rel_parts):
            continue
        if p.suffix in EXCLUDE_SUFFIXES:
            continue
        yield p


def git_head():
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(REPO), capture_output=True, text=True, timeout=15,
        )
        return out.stdout.strip() if out.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def prune(keep):
    if not BACKUPS_DIR.exists():
        return 0
    zips = sorted(BACKUPS_DIR.glob("backup_*.zip"), key=lambda p: p.stat().st_mtime)
    removed = 0
    for old in zips[:-keep] if keep > 0 else zips:
        try:
            old.unlink()
            removed += 1
        except Exception as e:
            log(f"[warn] 删除旧备份失败 {old.name}: {e}")
    return removed


def main():
    ap = argparse.ArgumentParser(description="HXO website repo backup")
    ap.add_argument("--keep", type=int, default=DEFAULT_KEEP, help="保留最近 N 份备份")
    ap.add_argument("--dry-run", action="store_true", help="只打印，不写文件")
    args = ap.parse_args()

    files = list(iter_files())
    if args.dry_run:
        log(f"[dry-run] 将打包 {len(files)} 个文件（排除 {sorted(EXCLUDE_DIRS)}）")
        for p in files[:20]:
            print("  ", p.relative_to(REPO))
        if len(files) > 20:
            print(f"   ... 其余 {len(files) - 20} 个")
        return 0

    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = BACKUPS_DIR / f"backup_{ts}.zip"

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in files:
            try:
                zf.write(p, arcname=str(p.relative_to(REPO)))
            except Exception as e:
                log(f"[warn] 跳过 {p}: {e}")

    size_mb = out.stat().st_size / 1024 / 1024
    log(f"[ok] 备份完成: {out.name}（{len(files)} 文件, {size_mb:.1f} MB, git {git_head()}）")

    removed = prune(args.keep)
    if removed:
        log(f"[clean] 清理旧备份 {removed} 份，保留最近 {args.keep} 份")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_tasks_health.py — HXO 计划任务健康监控

作用（每天 08:00 由 Windows 任务计划 HXO_TaskHealthCheck 调用）：
  1. 读取所有 HXO* 计划任务的 LastTaskResult / NextRunTime / State。
  2. 判定：
       LastTaskResult == 0        → 正常
       LastTaskResult != 0        → 异常（记录错误码 + 人类可读含义）
       NextRunTime 为空/无效      → 异常（任务没有下一触发时间，等于没挂上）
       State == Disabled          → 异常（任务被禁用）
  3. 检查看板数据新鲜度：dashboard_data/meta.json 的 last_updated 距今 >2 天 → 异常。
  4. DNS 巡检：比对 hxo-lcr.cn / www.hxo-lcr.cn 与标准配置（见 docs/DNS配置锁定.md），不符标红。
  4. 有异常时生成报告文本，写入 logs/task_health_report.txt 并打印到命令行。
     不发邮件；需要时手动运行或双击桌面「检查系统健康.bat」查看。

只读设计：不修改任何计划任务、不碰文章内容。仅写 logs/ 下的报告文件。

用法：
    python tools/check_tasks_health.py              # 检查 + 生成报告 + 命令行输出
    python tools/check_tasks_health.py --json       # 额外输出机器可读 JSON
    python tools/check_tasks_health.py --dashboard-max-age 2   # 看板新鲜度阈值（天）
"""
import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent.parent
LOGS_DIR = REPO / "logs"
REPORT_FILE = LOGS_DIR / "task_health_report.txt"
DASHBOARD_META = REPO / "dashboard_data" / "meta.json"

TASK_PREFIX = "HXO"
DEFAULT_DASHBOARD_MAX_AGE_DAYS = 2

# 常见 Windows 计划任务结果码（0x8007xxxx = Win32 错误，其余为任务计划器自定义）
RESULT_HINTS = {
    0: "正常",
    267008: "0x00041300 任务已就绪（尚未运行）",
    267009: "0x00041301 任务正在运行",
    267010: "0x00041302 任务已被禁用",
    267011: "0x00041303 任务尚未运行过",
    267012: "0x00041304 没有更多运行实例",
    267014: "0x00041306 任务被终止",
    267015: "0x00041307 任务没有有效触发器",
    267016: "0x00041308 任务的一个或多个属性无效",
    -2147020576: "0x800710E0 操作员或管理员拒绝了请求（常见：电池限制/权限）",
    -2147020577: "0x800710DF 服务未运行",
    -2147024891: "0x80070005 访问被拒绝",
    -2147024894: "0x80070002 系统找不到指定的文件（脚本路径错误）",
    -2147024893: "0x80070003 系统找不到指定的路径",
    -2147024770: "0x8007007E 找不到指定的模块",
    -2147024362: "0x80070522 客户端没有所需特权",
    -2147024890: "0x80070006 无效的句柄",
    -2147024223: "0x800705D1 任务不能运行，因为上一个实例仍在运行",
}


def run_ps(cmd):
    """Run a PowerShell command, return stdout as text."""
    out = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
    )
    return out.stdout.strip(), out.returncode


def read_tasks():
    """Return list of dicts for all HXO* scheduled tasks."""
    ps = (
        "Get-ScheduledTask | Where-Object { $_.TaskName -like '%s*' } | "
        "ForEach-Object { $t = $_; $i = Get-ScheduledTaskInfo -TaskName $t.TaskName -TaskPath $t.TaskPath; "
        "[PSCustomObject]@{ Name=$t.TaskName; State=$t.State.ToString(); "
        "LastResult=$i.LastTaskResult; LastRun=$i.LastRunTime.ToString('o'); NextRun=$i.NextRunTime.ToString('o') } } | "
        "ConvertTo-Json -Compress" % TASK_PREFIX
    )
    out, rc = run_ps(ps)
    if not out:
        return []
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        data = [data]
    return data


def parse_ps_date(s):
    if not s or s == "null":
        return None
    s = s.strip()
    # PowerShell '.ToString("o")' yields e.g. 2026-10-11T22:00:00.0000000+08:00
    # (7 fractional digits). Trim fractional part to <=6 digits for %f.
    import re
    s_norm = re.sub(r"\.(\d{6})\d+", r".\1", s)
    for candidate in (s_norm, s):
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z",
                    "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S",
                    "%Y/%m/%d %H:%M:%S"):
            try:
                return dt.datetime.strptime(candidate, fmt)
            except Exception:
                continue
    return None


def eval_task(task):
    """Return (ok: bool, reason: str) for a task dict."""
    name = task.get("Name", "?")
    state = task.get("State", "")
    try:
        result = int(task.get("LastResult", 0))
    except Exception:
        result = None
    next_run = parse_ps_date(task.get("NextRun"))

    if state == "Disabled":
        return False, "任务被禁用"
    if next_run is None:
        return False, "NextRunTime 为空 —— 没有有效触发时间（任务可能没挂上）"
    if result is None:
        return False, "无法读取 LastTaskResult"
    if result != 0:
        hint = RESULT_HINTS.get(result, "未知错误码")
        # 267009 = 0x41301 任务正在运行：此刻正在执行（含健康检查自身），属正常瞬时态，不算故障
        if result == 267009:
            return True, f"正在运行中（{hint}）"
        return False, f"LastTaskResult={result}（{hint}）"
    return True, "正常"


def check_dashboard(max_age_days):
    """Return (ok, reason, age_days)."""
    if not DASHBOARD_META.exists():
        return False, f"找不到 {DASHBOARD_META.relative_to(REPO)}", None
    try:
        meta = json.loads(DASHBOARD_META.read_text(encoding="utf-8"))
        ts = meta.get("last_updated")
        updated = dt.datetime.fromisoformat(ts)
    except Exception as e:
        return False, f"无法解析看板更新时间: {e}", None

    now = dt.datetime.now(updated.tzinfo) if updated.tzinfo else dt.datetime.now()
    age = (now - updated).total_seconds() / 86400
    if age > max_age_days:
        return False, f"看板数据距今 {age:.1f} 天未更新（阈值 {max_age_days} 天），最后更新 {ts}", age
    return True, f"看板数据距今 {age:.1f} 天（最后更新 {ts}）", age


# DNS 标准配置 —— 唯一权威见 docs/DNS配置锁定.md，改动前必读
DNS_EXPECT = {
    "hxo-lcr.cn": {"want": "216.198.79.1", "owner": "Vercel（裸域/看板项目）"},
    "www.hxo-lcr.cn": {"want": "hxo-resistor.github.io", "owner": "GitHub Pages（官网）"},
}
DNS_SERVER = "8.8.8.8"


def _resolve(name):
    """Return (a_ips, cname_target) via Resolve-DnsName (structured, locale-independent)."""
    ps = (
        f"Resolve-DnsName '{name}' -Type A -Server {DNS_SERVER} "
        "-ErrorAction SilentlyContinue | ConvertTo-Json -Compress"
    )
    out = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=40,
    ).stdout.strip()
    a_ips, cname = [], None
    if not out:
        return a_ips, cname
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return a_ips, cname
    if isinstance(data, dict):
        data = [data]
    for rec in data:
        if rec.get("Type") == 5 or rec.get("NameHost"):  # CNAME
            host = rec.get("NameHost")
            if host:
                cname = host.rstrip(".")
        if rec.get("IP4Address"):
            a_ips.append(rec["IP4Address"])
    return a_ips, cname


def check_dns():
    """Return (ok, reason, details dict). Compares live DNS to DNS_EXPECT."""
    details = {}
    problems = []
    for domain, exp in DNS_EXPECT.items():
        a_ips, cname = _resolve(domain)
        details[domain] = {"a": a_ips, "cname": cname, "want": exp["want"]}
        want = exp["want"]
        if want in a_ips or (cname and cname == want):
            continue
        got = cname or (", ".join(a_ips) if a_ips else "无解析")
        problems.append(f"{domain} 期望 {want}（{exp['owner']}），实际 {got}")

    if problems:
        return False, "DNS 与标准不符：" + "；".join(problems), details
    return True, "hxo-lcr.cn→Vercel、www→GitHub Pages，与标准一致", details


def build_report(task_rows, dash_ok, dash_reason, dns_ok, dns_reason):
    lines = []
    lines.append("=" * 64)
    lines.append("HXO 任务健康报告")
    lines.append(f"生成时间: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 64)

    bad = [r for r in task_rows if not r["ok"]]

    lines.append("")
    lines.append("【计划任务】")
    for r in task_rows:
        mark = "✅ 正常" if r["ok"] else "❌ 异常"
        lines.append(f"  {mark}  {r['name']}")
        lines.append(f"       LastResult={r['result']}  LastRun={r['last_run']}  NextRun={r['next_run']}")
        if not r["ok"]:
            lines.append(f"       原因: {r['reason']}")

    lines.append("")
    lines.append("【看板数据新鲜度】")
    lines.append(f"  {'✅ 正常' if dash_ok else '❌ 异常'}  {dash_reason}")

    lines.append("")
    lines.append("【DNS 配置巡检】")
    lines.append(f"  {'✅ 正常' if dns_ok else '❌ 异常'}  {dns_reason}")

    lines.append("")
    has_issue = bool(bad) or (not dash_ok) or (not dns_ok)
    if has_issue:
        parts = []
        if bad:
            parts.append(f"{len(bad)} 个任务异常")
        if not dash_ok:
            parts.append("看板数据陈旧")
        if not dns_ok:
            parts.append("DNS 不符标准")
        lines.append("结论: " + " + ".join(parts))
        lines.append("")
        lines.append("【修复建议】")
        for r in bad:
            lines.append(f"  - {r['name']}: {suggest(r)}")
        if not dash_ok:
            lines.append("  - 看板: 手动运行 python tools/update_dashboard.py，检查 HXO_Dashboard_Refresh 任务")
        if not dns_ok:
            lines.append("  - DNS: 先读 docs/DNS配置锁定.md，再按标准改回（勿凭记忆操作）")
    else:
        lines.append("结论: 全部正常 ✅")

    lines.append("=" * 64)
    return "\n".join(lines), has_issue


def suggest(row):
    reason = row["reason"]
    if "NextRunTime 为空" in reason:
        return "重建触发器（schtasks /Create ... /XML），确认任务未丢失触发计划"
    if "被禁用" in reason:
        return "启用任务：schtasks /Change /TN <名> /ENABLE"
    if "操作员或管理员拒绝" in reason or "0x800710E0" in reason:
        return "检查任务的电源限制（DisallowStartIfOnBatteries）与权限，改为 false + RunLevel=HighestAvailable"
    if "找不到指定的文件" in reason or "0x80070002" in reason:
        return "任务引用的脚本/程序路径错误，核对 Action 的 Command 与 WorkingDirectory"
    if "正在运行" in reason:
        return "任务正在运行；若长时间不结束，检查是否有卡死进程"
    if row["result"] == 267011:
        return "任务从未运行过 —— 检查触发器是否在未来时间点、Action 路径是否存在"
    return "查看 logs/ 与事件查看器（Microsoft-Windows-TaskScheduler/Operational）定位原因"


def main():
    ap = argparse.ArgumentParser(description="HXO scheduled-task health check")
    ap.add_argument("--json", action="store_true", help="额外打印机器可读 JSON")
    ap.add_argument("--dashboard-max-age", type=int, default=DEFAULT_DASHBOARD_MAX_AGE_DAYS,
                    help="看板数据最大允许天数（默认 2）")
    ap.add_argument("--fail-on-issue", action="store_true",
                    help="发现异常时以退出码 1 结束（默认退出码 0，避免任务自查误报）")
    args = ap.parse_args()

    raw = read_tasks()
    if not raw:
        print("[error] 未读取到任何 HXO* 计划任务（PowerShell 查询失败或任务不存在）")
        return 2

    task_rows = []
    for t in raw:
        ok, reason = eval_task(t)
        next_run = parse_ps_date(t.get("NextRun"))
        last_run = parse_ps_date(t.get("LastRun"))
        try:
            result = int(t.get("LastResult", 0))
        except Exception:
            result = None
        task_rows.append({
            "name": t.get("Name", "?"),
            "ok": ok,
            "reason": reason,
            "result": result,
            "last_run": last_run.strftime("%Y-%m-%d %H:%M:%S") if last_run else "-",
            "next_run": next_run.strftime("%Y-%m-%d %H:%M:%S") if next_run else "-",
        })

    dash_ok, dash_reason, _ = check_dashboard(args.dashboard_max_age)
    try:
        dns_ok, dns_reason, dns_details = check_dns()
    except Exception as e:
        dns_ok, dns_reason, dns_details = False, f"DNS 巡检失败: {e}", {}
    report, has_issue = build_report(task_rows, dash_ok, dash_reason, dns_ok, dns_reason)

    print(report)

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(report + "\n", encoding="utf-8")
    print(f"\n[report] 已写入 {REPORT_FILE}")

    if args.json:
        print("\n[JSON]")
        print(json.dumps({
            "generated": dt.datetime.now().isoformat(),
            "tasks": task_rows,
            "dashboard": {"ok": dash_ok, "reason": dash_reason},
            "dns": {"ok": dns_ok, "reason": dns_reason, "details": dns_details},
            "has_issue": has_issue,
        }, ensure_ascii=False, indent=2))

    return 1 if (has_issue and args.fail_on_issue) else 0


if __name__ == "__main__":
    raise SystemExit(main())

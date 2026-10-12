# DNS 配置锁定（唯一权威）

> ⚠️ **此文件是 DNS 配置的唯一权威。任何 AI（或人）在改动 DNS 之前，必须先读本文件。**
> 若本文件与任何其他聊天记录、注释、推测冲突，以本文件为准。
> 最后核实：2026-10-12（公共解析 8.8.8.8 / 1.1.1.1 + HTTPS 响应头双向确认）

## 一、标准配置

| 域名 | 记录类型 | 目标 | 归属 | 状态 |
|---|---|---|---|---|
| `hxo-lcr.cn`（裸域 / @） | A | `216.198.79.1` | Vercel（TrendFlow / 看板项目） | ✅ |
| `www.hxo-lcr.cn` | CNAME | `hxo-resistor.github.io` | GitHub Pages（官网静态站） | ✅ |

指向 GitHub Pages 的 CNAME 会级联解析到 GitHub 的 A 记录：
`185.199.108.153 / 185.199.109.153 / 185.199.110.153 / 185.199.111.153`
（这四个 IPv4 是 GitHub Pages 的标准地址，属正常，不是错配。）

## 二、看板正确入口

- **运营看板唯一入口：https://www.hxo-lcr.cn/dashboard.html**
- 裸域 `hxo-lcr.cn` 是另一个 Vercel/Next.js 项目（TrendFlow），**不代表官网，也不是看板**。
- 官网（营销站）走 `www.hxo-lcr.cn`（GitHub Pages）。

## 三、验证方法

```powershell
nslookup hxo-lcr.cn 8.8.8.8        # 应返回 216.198.79.1
nslookup www.hxo-lcr.cn 8.8.8.8    # 应 CNAME 到 hxo-resistor.github.io
```

判据（HTTPS 响应头）：
- `https://hxo-lcr.cn` → `Server: Vercel`
- `https://www.hxo-lcr.cn` → `Server: GitHub.com`

`tools/check_tasks_health.py` 已内置本巡检，每天 08:00 随任务健康检查一并执行。

## 四、红线

1. **不改 DNS。** 只输出「用户需要点哪几下」的精确操作，由人来点。
2. 任何改动前先读本文件；改动后更新本文件的「最后核实」日期。
3. 不要把 `www` 的 CNAME 改成 Vercel，也不要把裸域 A 改成 GitHub IP —— 会同时打断看板与官网。
4. 裸域与 www **分工不同**，不是主从/跳转关系；不要设置「裸域重定向到 www」或反之。

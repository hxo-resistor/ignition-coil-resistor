# 第2步 · n8n 工作流串联 — 设计方案

> 状态：**设计阶段（未安装任何软件）**。本文件 + `work/n8n/hxo_pipeline.workflow.json` 为交付物。
> 约束：n8n 用 `npx` 试用（不装）；**所有动作走 Execute Command 调脚本**；不碰 HTML、不提交 git。

---

## 一、n8n 本地部署调研（Windows）

### 1.1 结论速览

| 项目 | 结论 |
|---|---|
| 免费吗 | ✅ 自托管 **Community 版永久免费**，功能几乎完整（SSO/项目/环境/Git 版本控制等为企业版）。fair-code 许可 |
| Node 要求 | **20.19 ≤ Node ≤ 24.x**。⚠️ 本机 **Node v26.5.0 超出范围** |
| 资源占用 | 空闲约 **300–500 MB 内存**，执行时 0.5–1 GB，单核。本机 **7.7 GB / 4 核，够用** |
| 数据库 | 默认 **SQLite**（零配置），本场景足够；生产可换 Postgres |
| 数据目录 | `%USERPROFILE%\.n8n\`（SQLite + 加密凭证） |
| 默认端口 | `5678`（`http://localhost:5678`） |

### 1.2 本机环境实测

```
Node   v26.5.0     ← 超标（n8n 要 20.19–24.x）
npm    11.17.0
Docker 未安装       ← 无 Docker Desktop
CPU    4 逻辑核
RAM    7.7 GB
```

### 1.3 部署方式对比（本机适配）

| 方式 | 命令 | 适配本机 | 说明 |
|---|---|---|---|
| **npx 试用**（已选） | `npx n8n` | ⚠️ 可能因 Node26 报错 | 免安装，首次下载约几百 MB。若 Node26 不兼容，需临时用 nvm 切 Node22 |
| npm 全局 | `npm i -g n8n` | ⚠️ 同上 | n8n 3.0 起 npm 安装标记 deprecated |
| Docker | `docker run ... n8nio/n8n` | ❌ 无 Docker | 最稳，但需先装 Docker Desktop |
| 一键脚本 | 官方 install script | ❌ | 依赖 Docker |

**建议（鉴于已选 npx）**：若 `npx n8n` 因 Node26 失败，用 **nvm-windows 临时切到 Node 22 LTS**（不改变全局默认），再 `npx n8n`。这是不改系统的最佳止损。

### 1.4 常驻运行

`npx`/npm 启动是前台进程。要常驻需：
- Windows 计划任务（开机启动 `npx n8n`），或
- NSSM 包装成 Windows 服务（推荐）
- 本阶段先用**手动启动**验证，稳定后再谈常驻。

---

## 二、现有资产盘点（工作流要串的动作）

| 动作 | 现成脚本/机制 | 状态 |
|---|---|---|
| **发现新文章** | `content/articles/*.md`（git 唯一内容入口） | ✅ |
| **发布官网** | `git push main` → GitHub Actions `build-and-deploy.yml` 自动 Markdown→HTML→Pages | ✅ 已自动化 |
| **百度推送** | `publish_b2b_package_v2.py::baidu_push_urls()`，token `StZI77pKI1nwhzFp` | ⚠️ 硬编码 token |
| **知乎发布** | `work/publish_zhihu.py`（子任务1.1，全自动，session 在 `browser-data/zhihu`） | ✅ |
| **Buffer(LinkedIn+X)** | `buffer_auto_linkedin_fixed.py`，token 硬编码，**仅 LinkedIn channel** | ⚠️ 需补 X channel |
| **同步 Supabase** | 表 `content_packages`，需本地代理 `127.0.0.1:7897` | ⚠️ 硬编码 key + 依赖代理 |
| **刷新看板** | `tools/update_dashboard.py` | ❌ **本 checkout 中看板数据目录不存在，脚本会报错**（见 §五） |

---

## 三、Workflow 设计

### 3.1 流程图

```
┌──────────────────────────────────────────────────────────┐
│  Trigger: Schedule (每天 09:00) 或 手动 Execute            │
└───────────────────────────┬──────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────┐
│  N0 · Discover   Execute Command                          │
│  python work/n8n/n0_discover.py                           │
│  → JSON {new:[{slug,title}]}  （对比 published_manifest）  │
└───────────────────────────┬──────────────────────────────┘
                            ▼
              ┌─────────────────────────────┐
              │  IF new.count == 0 ?         │──yes──▶ No-Op (停止)
              └──────────────┬──────────────┘
                            │ no
                            ▼
              ┌─────────────────────────────┐
              │  Split In Batches (1 篇/次)  │
              └──────────────┬──────────────┘
                            ▼
   ┌────────┬────────┬──────┴─────┬────────┬────────┐   （顺序 Execute Command）
   ▼        ▼        ▼            ▼        ▼        ▼
┌──────┐┌──────┐┌────────┐  ┌────────┐┌────────┐┌────────┐
│N1 官网││N2 百度││N3 知乎  │  │N4 Buffer││N5 Supa ││N6 看板 │
│git   ││POST  ││publish │  │POST    ││POST    ││update_ │
│push  ││baidu ││_zhihu  │  │buffer  ││content ││dashbrd │
└──┬───┘└──┬───┘└───┬────┘  └───┬────┘└───┬────┘└───┬────┘
   └───────┴────────┴───────────┴─────────┴─────────┘
                            ▼
              ┌─────────────────────────────┐
              │  N7 · Mark   Execute Command │
              │  python work/n8n/n7_mark.py  │
              │  --slug ... --url ...        │
              │  （写 published_manifest）    │
              └──────────────┬──────────────┘
                             ▼
              ┌─────────────────────────────┐
              │  Loop back to Split Batches  │
              └─────────────────────────────┘
```

### 3.2 节点说明

| 节点 | n8n 类型 | 命令 / 参数 | 输出契约 |
|---|---|---|---|
| **Trigger** | Schedule Trigger | 每天 09:00（可停用） | — |
| **N0 Discover** | Execute Command | `python work/n8n/n0_discover.py` | `{"ok":true,"new":[...]}` |
| **IF no new** | IF | `{{ $json.new.length === 0 }}` | — |
| **Split In Batches** | Split In Batches | batchSize=1，以 `new` 数组 | 每轮 1 篇 |
| **N1 Website** | Execute Command | `python work/n8n/n1_website.py` | `{"ok":true,"commit":"..."}` |
| **N2 Baidu** | Execute Command | `python work/n8n/n2_baidu.py --slugs {{slug}}` | `{"ok":true,"success":N}` |
| **N3 Zhihu** | Execute Command | `python work/n8n/n3_zhihu.py --slug {{slug}}` | `{"ok":true,"url":"..."}` |
| **N4 Buffer** | Execute Command | `python work/n8n/n4_buffer.py --title "{{title}}"` | `{"ok":true,"results":[...]}` |
| **N5 Supabase** | Execute Command | `python work/n8n/n5_supabase.py --slug {{slug}}` | `{"ok":true,"http":201}` |
| **N6 Dashboard** | Execute Command | `python work/n8n/n6_dashboard.py` | `{"ok":true}` ⚠️ 见 §五 |
| **N7 Mark** | Execute Command | `python work/n8n/n7_mark.py --slug {{slug}} --url "{{zhihuUrl}}"` | `{"ok":true,"total":N}` |

### 3.3 Wrapper 脚本（已建，`work/n8n/`）

| 脚本 | 作用 | 复用来源 |
|---|---|---|
| `_common.py` | 共用：REPO 路径、JSON 输出、manifest 读写、run() | 新 |
| `n0_discover.py` | 扫描未发布文章 | 新 |
| `n1_website.py` | `git add content/articles` + commit + push（仅 stage 内容） | 新（借鉴 `publish_*`） |
| `n2_baidu.py` | 百度主动推送 | 复用 `baidu_push_urls()` 逻辑 |
| `n3_zhihu.py` | 调 `publish_zhihu.py` | 复用子任务1.1 |
| `n4_buffer.py` | Buffer GraphQL，支持多 channel | 复用 `buffer_auto_linkedin_fixed.py` |
| `n5_supabase.py` | 写 `content_packages`（幂等） | 复用 `publish_b2b_package_v2.py` |
| `n6_dashboard.py` | 调 `tools/update_dashboard.py` | 复用（但有布局问题，§五） |
| `n7_mark.py` | 写 `published_manifest.json` | 新 |

**统一契约**：每个 wrapper 都在最后一行打印一个 JSON 对象（`{"ok":...,"action":...}`），n8n 用 Code 节点 `JSON.parse` 即可拿到结构化结果。

---

## 四、关键设计决策

1. **幂等/防重**（最重要）：`work/published_manifest.json` 记录已发 slug；N0 据此过滤，N7 写回。否则每天 Schedule 会重复发布。
2. **顺序 vs 并行**：N1（官网 push）是前提（URL 要生效），且 CI 需 ~120s 构建；建议流程串行，N1 后可加 Wait 节点。
3. **凭证安全**：现有 token 全硬编码。wrapper 已改为**优先读环境变量**（`BAIDU_API_TOKEN`/`BUFFER_TOKEN`/`SUPABASE_KEY`/`HXO_PROXY`），默认值兼容旧行为。**建议后续把 token 挪出脚本。**
4. **代理**：N5 Supabase 依赖 Clash `127.0.0.1:7897`，n8n 进程环境需能访问。
5. **git 防循环**：N1 **只 stage `content/articles`**，避免把 manifest/日志一起提交触发无谓 CI。

---

## 五、已知缺口 / 风险（需你知晓）

| # | 缺口 | 影响 | 建议 |
|---|---|---|---|
| 1 | **N6 看板脚本布局不匹配** | `tools/update_dashboard.py` 期望 `tools/../../dashboard_data`，但本 checkout 无该目录，运行会 `FileNotFoundError` | 本 checkout 中 TrendFlow 看板不存在；N6 暂标 **disabled**，等看板目录就位再启 |
| 2 | **Node 26 超标** | `npx n8n` 可能启动失败 | 失败则用 nvm-windows 临时切 Node 22 |
| 3 | **Buffer 仅 LinkedIn** | 未含 X channel | 需提供 X 的 Buffer channel ID 才能覆盖 |
| 4 | **Supabase 表结构** | code 假设 `content_packages(date,product_id,title,content_md,source,status,sync_status)` | 需你确认字段 |
| 5 | **知乎限流** | 连续跑多篇会触发 40362 | workflow 加间隔/错误重试 |
| 6 | **首次登录** | 知乎需扫码一次 | 已登录（`browser-data/zhihu`）；抖音暂停 |

---

## 六、下一步（待确认后）

1. 你确认本设计 → 我补全 `hxo_pipeline.workflow.json`（可导入 n8n）
2. 用 `npx n8n` 起服务 → 导入 workflow → **全部禁用发布，只跑 N0/N6 dry-run** 验证编排
3. 逐节点启用，先跑一篇测试文章
4. 稳定后加 Schedule + 常驻服务

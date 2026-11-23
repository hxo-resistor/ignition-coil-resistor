# AGENTS.md

Static GitHub Pages marketing site for HXO Resistor (ignition-coil suppression resistors). Plain HTML, no framework, no build step, no `package.json`, no tests/lint, no CI.

## Deploy
- Live at `https://www.hxo-lcr.cn` (see `CNAME`). Push to `main` → GitHub Pages auto-deploys.
- `.nojekyll` is required so paths/files are served as-is (do not remove).
- `robots.txt` references the `www.hxo-lcr.cn` domain, not the `*.github.io` URL.

## Editing pages
- Edit `.html` files directly. Each page is self-contained: nav, footer, analytics, and schema are duplicated inline in every file (no shared templates/includes).
- Primary language is Chinese at repo root; English mirror lives under `en/`.
- Product pages: `ig-c.html`, `ig-f.html`, `ig-s.html` (+ `en/` copies). Datasheets are checked-in PDFs (`IG-C_Datasheet.pdf`, `IG-F_Datasheet.pdf`, `IG-S_Datasheet.pdf`, `Product_Catalog.pdf`, `Application_Notes.pdf`, `Certifications.pdf`).

## Cross-file updates (easy to miss)
When adding/renaming a page, also update:
- `sitemap.xml` (and `en/sitemap.xml` for English pages)
- the duplicated in-page nav links, plus the article index (`articles.html`, `en/article_guides.html`)
Every page carries Google Analytics `gtag`, Microsoft Clarity, Baidu `push.js`, and JSON-LD structured data — mirror these on any new page.

### Article publish → index (mandatory)
**发布文章后必须同步 `articles.html` 索引**，否则文章页能上线（CI 由 md 自动构建），但索引页不会出现新文章，看板的「N/5 成功」会误导（官网动作即使成功，索引仍是旧的）。
- `tools/publish_all.py` 已在 website 动作前自动调用 `update_articles_index(slug)`（幂等，按 `./<slug>.html` 或绝对 URL 去重），并由 `work/n8n/n1_website.py` 的 `git add content/articles articles.html` 一并提交——正常链路无需手动改索引。
- 手动补发/重建索引时：同步插入 `articles.html`（如需英文再补 `en/article_guides.html`），保持 `<div class="article-item">` 结构（tag/h3/p/meta），与既有条目风格一致。
- 同理，任何"只改 md、不碰索引"的操作都可能漏掉索引，提交前务必确认 `articles.html` 已包含新文章链接。

## Python scripts (legacy one-offs — do not run blindly)
Scripts in repo root are automation leftovers, not part of any pipeline. They contain hardcoded Linux paths (`/app/data/所有对话/...`) that don't exist here, plus hardcoded/placeholder secrets:
- `push_all.py`, `upload_to_github.py`, `publish_articles.py` — GitHub Contents API uploads; `GITHUB_TOKEN = "YOUR_TOKEN_HERE"`.
- `publish_b2b_package.py` / `publish_b2b_package_v1.1.py` / `publish_b2b_package_v1.2.py` — deploy pipeline with hardcoded Supabase key, Clash proxy, Baidu token.
- `buffer_auto_linkedin.py` / `buffer_auto_linkedin_fixed.py` — Buffer/LinkedIn posting with hardcoded token.
- `generate_all_pdfs.py`, `generate_series_pages.py` — PDF/HTML generators (Linux font paths, write to `/app/data/...`).
Treat these as reference only. Never commit new secrets; the repo already leaks several.

## Operations dashboard (automated)
- **运营看板唯一入口 = `https://www.hxo-lcr.cn/dashboard.html`**（GitHub Pages）。裸域 `hxo-lcr.cn` 是另一个 Vercel/Next.js 项目（TrendFlow），本看板**不涉及**，勿动其 DNS 或项目。
- `tools/update_dashboard.py` regenerates `dashboard.html` (live at `/dashboard.html`) and `dashboard_data/*.json` from real sources: `work/publish_all.log`, `work/published_manifest.json`, `work/zhihu_published.log`, `work/topic_pool.md`, repo-root `article_*.html`, and read-only Supabase `content_packages`.
- `dashboard.html` is listed in `sitemap.xml` (`changefreq=daily`).
- Smart commit: it fingerprints business data (excluding `last_updated`). If unchanged, output is byte-identical and **no commit is made** (avoids daily empty commits). Only real data changes are `git add dashboard.html dashboard_data` + commit + push `origin main`.
- `tools/run_dashboard_task.bat` is the scheduled runner (sets cwd, logs to `logs/dashboard_run.log`).
- Windows Task Scheduler task `HXO_Dashboard_Refresh` runs it daily at **09:00**. Verify: `schtasks /Query /TN HXO_Dashboard_Refresh /V /FO LIST`.
- Errors append to `logs/dashboard_errors.log`; `logs/dashboard_alert_state.json` tracks consecutive failures (alert at 3).

## Windows 计划任务（Task Scheduler）

四个自动化任务（当前用户 fwen8；Python = `C:\Users\fwen8\AppData\Local\Programs\Python\Python315\python.exe`）：

| 任务 | 触发 | 命令 |
|------|------|------|
| `HXO_Dashboard_Refresh` | 每天 09:00 | `tools\run_dashboard_task.bat` → `tools\update_dashboard.py` |
| `HXO_Auto_Publish` | 周一/三/五 10:00 | `tools\daily_publish.py --region cn`（国内全链路：官网→百度→微信→Supabase→看板） |
| `HXO_Auto_Publish_INTL` | 周一~五 20:00（每 30min 重试，最多 3h） | `tools\daily_publish.py --region intl`（海外 LinkedIn/X，走 Buffer） |
| `HXO_Website_Backup` | 周日 22:00 | `tools\backup_website.py`（打包到 `backups/`，已 gitignore） |

- **登录模式 = InteractiveToken**（仅用户登录时运行）。机器注销/锁屏时任务会被拒（上次结果 `0x800710E0`）。已为所有任务加 `StartWhenAvailable`（错过时间后登录即补跑）+ `RestartOnFailure`（失败按间隔重试）缓解；要彻底「无论是否登录都运行」需**管理员权限 + 账号密码**（S4U/Password 注册均被拒）。
- **已删除**：`HXO_UpdateWebsite`、`HXO_Buffer_AutoPublish`（2026-10-14 起与 `HXO_Auto_Publish` 抢 `.git/index.lock` 导致发布中断，先禁用后删除）。
- 相关加固（2026-10-14）：`tools/publish_all.py` 的 `log()` 写日志失败会打印到 stderr（不再静默）；`work/n8n/n1_website.py` 在 git 操作前等 `.git/index.lock` 释放（最多 3×5s，仍失败则报错）；`tools/daily_publish.py` 失败/标记失败均返回非 0 退出码，避免「失败却显示成功」。
- 查验：`Get-ScheduledTask | Where-Object TaskName -like "HXO*" | Select TaskName,State`。

## 知乎发布暂停（2026-10-16 起）
- **知乎账号因「AI 批量生成」被禁言，至 2026-10-19 结束。** 期间**暂停知乎发布**，10-19 后**人工评估**是否恢复（复评前不要自动重开）。
- 开关：`tools/publish_all.py` 顶部 `ZHIHU_ENABLED = False`。为 false 时整条流水线**强制跳过** `zhihu` 动作，其他平台（官网/百度/Buffer/Supabase）不受影响；`--only zhihu` 也不会发布（会 log 提示并跳过）。
- 临时调试可用环境变量 `HXO_ZHIHU_ENABLED=1` 覆盖开关（仅调试，勿长期开启）。
- 恢复步骤：把 `ZHIHU_ENABLED` 改回 `True`（或评估后确认账号恢复），再跑发布；**不删除、不回滚任何知乎历史内容**（`work/zhihu_published.log`、已发布文章均保留）。


## Conventions
- Commit style: `Auto-deploy YYYYMMDD` or a short description.
- `logs/` is runtime output and is gitignored. `work/` (logs, manifests, topic pool, runtime scripts) is untracked — commit only explicit paths, never `git add -A`. One exception: `work/n8n/n5_supabase.py` is force-added (`git add -f`) because it carries the slug/product_id logic; prefer keeping core scripts tracked.

## Supabase sync (content_packages)
- `work/n8n/n5_supabase.py` syncs one article per row; idempotent on **`slug`** (UNIQUE), not `(date, product_id)`.
- `product_id` is derived from slug+title via `PRODUCT_MAP` (`rxf-otp-1w` / `ig-c-ceramic` / `ig-f-glassfiber` / `ig-s-ceramic` / `hv-wirewound`); unmatched → `unknown` (never guesses `av`).
- Legacy rows (pre-slug) carry non-semantic `legacy-<id>` slugs; normalizing them is a separate future task.
- **网络自愈（2026-11-23）**：`supabase.co` 在当前代理节点上常被 TLS 重置（`SSLError UNEXPECTED_EOF`，直连同样失败）。`n5_supabase.py` 先走代理再直连、各重试 2 次；仍失败则**软跳过**（`ok:true, skipped:supabase_unreachable`）不阻断流水线，slug 写入 `work/supabase_pending.log`（gitignored）。`tools/daily_publish.py` 每次发布成功后自动调用 `n5_supabase.py --backfill` 补发待补发清单——网络恢复即自动回填，无需人工干预。

## TODO (not yet done, by design)
- Move core automation scripts (`n5_supabase.py`, `publish_all.py`, `daily_publish.py`) out of untracked `work/` into tracked `tools/`. Deferred to keep changes minimal.

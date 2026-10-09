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

## Conventions
- Commit style: `Auto-deploy YYYYMMDD` or a short description.
- `logs/` is runtime output and is gitignored. `work/` (logs, manifests, topic pool, runtime scripts) is untracked — commit only explicit paths, never `git add -A`. One exception: `work/n8n/n5_supabase.py` is force-added (`git add -f`) because it carries the slug/product_id logic; prefer keeping core scripts tracked.

## Supabase sync (content_packages)
- `work/n8n/n5_supabase.py` syncs one article per row; idempotent on **`slug`** (UNIQUE), not `(date, product_id)`.
- `product_id` is derived from slug+title via `PRODUCT_MAP` (`rxf-otp-1w` / `ig-c-ceramic` / `ig-f-glassfiber` / `ig-s-ceramic` / `hv-wirewound`); unmatched → `unknown` (never guesses `av`).
- Legacy rows (pre-slug) carry non-semantic `legacy-<id>` slugs; normalizing them is a separate future task.

## TODO (not yet done, by design)
- Move core automation scripts (`n5_supabase.py`, `publish_all.py`, `daily_publish.py`) out of untracked `work/` into tracked `tools/`. Deferred to keep changes minimal.

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

## Conventions
- Commit style: `Auto-deploy YYYYMMDD` or a short description.
- No `.gitignore`; `logs/` is runtime output and untracked.

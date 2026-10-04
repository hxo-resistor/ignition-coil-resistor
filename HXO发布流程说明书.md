# HXO 发布流程说明书

> 分析范围：`AGENTS.md` 与仓库根目录下的发布脚本。只做分析与文档输出，未执行任何发布。
> 生成日期：2026-10-04

## 0. 与请求的两处差异（重要）

请求中提到的两个脚本在当前仓库中**不存在**，实际对应关系如下：

| 请求的脚本 | 实际情况 |
|---|---|
| `publish_b2b_package_v2.py` | 不存在。最新版本是 `publish_b2b_package_v1.2.py`（另有 `publish_b2b_package.py` v1.0 与 `publish_b2b_package_v1.1.py`） |
| `add_baidu_push.py` | 不存在。百度主动推送是 `publish_b2b_package_v1.2.py` 内的 `baidu_push_urls()` 函数，且因引用未定义的全局变量而**无法运行**（详见 5.1） |

仓库中实际存在的发布相关脚本（均为一次性自动化遗留，非流水线组件）：

- `generate_series_pages.py` / `generate_all_pdfs.py` —— 生成 HTML / PDF
- `publish_articles.py` —— 从 Markdown 生成文章 HTML 并上传
- `upload_to_github.py` / `push_all.py` —— 经 GitHub Contents API 直接上传文件
- `publish_b2b_package.py` / `_v1.1.py` / `_v1.2.py` —— git 提交推送 + Supabase 同步 + 验证（+百度推送 + Buffer）
- `buffer_auto_linkedin.py` / `buffer_auto_linkedin_fixed.py` —— Buffer/LinkedIn 社媒发布（两文件内容完全相同）

---

## 1. 流程概览

一篇文章从生成到上线存在两套并行的路径：

```
A. 本地生成 → GitHub Contents API 直接上传（旧脚本，token 为占位符，已不可用）
B. 本地 git 提交推送 → GitHub Pages 构建 → Supabase/Baidu/Buffer 联动（publish_b2b_package_v1.2 主路径）
```

实际「上线」由 **GitHub Pages** 完成：仓库 push 到 `main` 分支即自动构建发布到 `https://www.hxo-lcr.cn`（见 `CNAME`），无 CI 文件、无 build 步骤，`.nojekyll` 需保留。

---

## 2. 一篇文章的完整步骤

### 第 0 步：准备原始内容（可选，离线生成）

将技术资料/文案转换为站点资源：

- **产品系列页**：`generate_series_pages.py`
  - 内置 `SERIES` 字典（IG-C/IG-F/IG-S），生成 `ig-c.html` / `ig-f.html` / `ig-s.html`
  - 输出到硬编码 Linux 路径 `/app/data/所有对话/主对话/github_pages/`（本地不存在，仅参考模板）
- **PDF 资料**：`generate_all_pdfs.py`（依赖 `fpdf`）
  - 生成 `IG-F_Datasheet.pdf`、`IG-S_Datasheet.pdf`、`Product_Catalog.pdf`、`Application_Notes.pdf`
  - 依赖 Linux 字体 `/usr/share/fonts/opentype/noto/NotoSansCJK-*.ttc`，同样仅 Linux 环境可用
- **文章 HTML**：`publish_articles.py`
  - 内置 `create_article_page(title, content, filename)`，把 Markdown 逐行转成独立自包含 HTML（含内联 CSS、返回首页/文章列表导航、CTA）
  - `articles` 列表定义了三篇示例文章（标题 + 本地 Markdown 路径 + 目标文件名）

### 第 1 步：把文章 HTML 放进仓库

文章 HTML 需与站内其他页面保持一致：自带导航、页脚、Google Analytics `gtag`、Microsoft Clarity、百度 `push.js`、JSON-LD 结构化数据（见 `AGENTS.md`）。旧脚本 `publish_articles.py` 生成的 HTML 只含基础样式，**不含** gtag/Clarity/schema，需人工补齐。

### 第 2 步：跨文件同步（易遗漏，见 `AGENTS.md`）

新增/改名页面时同步更新：

- `sitemap.xml`（英文页还需 `en/sitemap.xml`）
- 每页内联导航链接 + 文章索引 `articles.html`（英文 `en/article_guides.html`）
- `robots.txt` 的 Sitemap 地址保持 `https://www.hxo-lcr.cn/sitemap.xml`

### 第 3 步：部署（两条路径二选一）

**路径 A —— Contents API 上传（已失效）**
- `upload_to_github.py`：`files_to_upload` 列表硬编码 7 个文件
- `push_all.py`：上传 `FILES_DIR` 下全部文件（含 `en/`）
- 均需 `GITHUB_TOKEN`（当前为占位符 `YOUR_TOKEN_HERE`）

**路径 B —— git 流水线（主路径，`publish_b2b_package_v1.2.py`）**

```bash
python publish_b2b_package_v1.2.py <html_file> <product_id> [title]
# 示例：python publish_b2b_package_v1.2.py article_ig_c.html ig-c "IG-C 陶瓷芯"
```

- `html_file`：待发布的 HTML 文件名（须存在于 `repo_path` 下）
- `product_id`：Supabase `content_packages.product_id` 字段值
- `title`：可选，缺省时由文件名推导（`article_ig_c` → `article ig c`）

流水线内部 7 步（见脚本 `main()`）：
1. 代理自检（Clash `http://127.0.0.1:7897`）
2. 检查当前为 `main` 分支
3. 参数与文件存在性校验
4. `git add .` → `git commit` → `git push origin main`（失败重试 3 次，间隔 60s）
5. 百度 API 主动推送 4 个 URL（`baidu_push_urls`，v1.2 新增）
6. Supabase 同步（`POST /rest/v1/content_packages`）
7. 等待 120s → `verify_deployment()` 验证（重试 3 次，间隔 60s）+ Buffer LinkedIn 联动

### 第 4 步：社媒联动

- `publish_b2b_package_v1.2.py` 通过 `publish_to_buffer()` 以子进程调用：
  `python buffer_auto_linkedin.py <html_file> <title>`
- `buffer_auto_linkedin.py` / `buffer_auto_linkedin_fixed.py` 用法相同，调用 Buffer GraphQL `createPost` 把固定模板文案加入 LinkedIn 队列

---

## 3. 脚本与参数汇总

| 脚本 | 调用方式 | 关键参数 | 作用 |
|---|---|---|---|
| `generate_series_pages.py` | `python generate_series_pages.py` | 无（内置 `SERIES`） | 生成产品系列页 HTML |
| `generate_all_pdfs.py` | `python generate_all_pdfs.py` | 无 | 生成 4 份 PDF |
| `publish_articles.py` | `python publish_articles.py` | 无（内置 `articles` 列表） | 生成并上传文章 HTML |
| `upload_to_github.py` | `python upload_to_github.py` | 无（内置 `files_to_upload`） | Contents API 上传 7 文件 |
| `push_all.py` | `python push_all.py` | 无 | Contents API 上传全部文件 |
| `publish_b2b_package.py`（v1.0） | `python publish_b2b_package.py <html_file> <product_id> <title>` | 3 个位置参数 | git 推送 + Supabase + 验证 |
| `publish_b2b_package_v1.1.py` | 同上 | 同上（title 可选） | 增加导航更新 + 验证重试 |
| `publish_b2b_package_v1.2.py` | `python publish_b2b_package_v1.2.py <html_file> <product_id> [title]` | 同上 | 增加百度推送 + Buffer 联动 |
| `buffer_auto_linkedin.py` / `_fixed.py` | `python buffer_auto_linkedin.py <html_file> <title>` | 2 个位置参数 | Buffer/LinkedIn 发帖 |

---

## 4. 密钥 / 凭证依赖

> 注意：以下密钥均**硬编码在脚本中**，仓库已泄露多处，切勿再提交新密钥。

| 步骤 | 依赖项 | 位置 | 现状 |
|---|---|---|---|
| Contents API 上传 | GitHub Token | `push_all.py`/`upload_to_github.py`/`publish_articles.py` 的 `GITHUB_TOKEN` | 占位符 `YOUR_TOKEN_HERE`（不可用） |
| git 推送 | Git 远程凭证 | 本地 git 配置 | 依赖本机已配置的 GitHub 凭据 |
| 代理 | Clash | `publish_b2b_package*.py` 的 `CONFIG['proxy'] = 'http://127.0.0.1:7897'` | 需本地 Clash 运行 |
| Supabase 同步 | Supabase URL + anon key | `publish_b2b_package*.py` 的 `supabase_url` / `supabase_key` | URL `whnmtkrmvqayfhpmrdiq.supabase.co`；key 为 anon JWT |
| 百度推送 | 百度 token | `publish_b2b_package_v1.2.py` 引用 `BAIDU_API_TOKEN` | **未定义**，导致脚本无法运行（见 5.1） |
| Buffer/LinkedIn | Buffer Token + Channel ID | `buffer_auto_linkedin*.py` 的 `BUFFER_TOKEN` / `CHANNEL_IDS` | 硬编码已泄露 |

`content_packages` 表现在有 **24** 条记录（2026-10-04 实测）。

---

## 5. 常见错误与处理

### 5.1 `publish_b2b_package_v1.2.py` 无法运行（NameError）

- 现象：脚本导入即报错 `NameError: name 'BAIDU_API_TOKEN' is not defined`（`CONFIG` 第 39–40 行直接引用 `BAIDU_API_TOKEN` / `BASE_URL`，全文件无定义）。
- 处理：若需使用百度推送，在脚本顶部补 `BAIDU_API_TOKEN = "<真实token>"`、`BASE_URL = "https://www.hxo-lcr.cn"`。git 历史曾提交过 token `StZI77pKI1nwhzFp`（`baidu_push_urls` 里把它当作「未配置」哨兵值）。
- 建议：优先用 `publish_b2b_package_v1.1.py`（无百度推送、无此 bug），或仅参考逻辑。

### 5.2 脚本内的仓库名 / 域名拼写错误

- `publish_b2b_package*.py` 里 `github_repo` / `remote` 写成 `hxo-resitor/ignition-coil-resitor`（`resitor` 拼写错误），而真实仓库是 `hxo-resistor/ignition-coil-resistor`（见 `git remote -v`）。
- `update_articles_nav()` 生成的文章链接用了错误的 `https://hxo-resitor.github.io/ignition-coil-resitor/...`，插入 `articles.html` 后会指向错误域名。
- 处理：新增导航链接应以 `https://www.hxo-lcr.cn/<file>` 或相对路径为准，不要沿用脚本里的旧域名模板。

### 5.3 Linux 硬编码路径不存在

- `push_all.py` / `upload_to_github.py` / `publish_articles.py` / `generate_*` 中 `FILES_DIR`/`OUTPUT_DIR` 指向 `/app/data/所有对话/...`，本机（Windows）不存在。
- 处理：这些是生成端脚本的遗留路径，仅作参考；实际站点文件已在仓库内，直接编辑 `.html` 即可。

### 5.4 代理自检失败（`无法连接到代理服务器 127.0.0.1:7897`）

- 现象：`check_proxy()` 通过代理访问 GitHub 失败，`main()` 直接 `sys.exit(1)` 终止。
- 处理：启动本地 Clash 并确认监听 7897 端口；或改 `CONFIG['proxy']`。

### 5.5 git 推送失败 / 不在 main 分支

- 现象：`check_git_branch()` 校验失败终止；`git_add_commit_push()` 重试 3 次后仍失败写入 `logs/publish_errors.log`。
- 处理：确保在 `main` 分支、远端为正确仓库；无变更时脚本会视为成功继续（`git status --porcelain` 为空则返回成功）。

### 5.6 GitHub Pages 构建未就绪导致验证失败

- 现象：`verify_deployment()` 检查首页含 `HXO`、`articles.html` HTTP 200，构建未完成时失败。
- 处理：脚本已内置 120s 等待 + 3 次重试（每次 60s）；若仍失败，确认 CNAME/DNS 正确、`.nojekyll` 存在。

### 5.7 Supabase 同步失败

- 现象：`sync_to_supabase()` 返回非 200/201（RLS 拒绝、字段不匹配等）。
- 处理：此步被设计为「不阻断发布」（仅 WARN 并继续）；确认 `content_packages` 表结构与 payload 字段（`date`/`product_id`/`title`/`content_md`/`source`/`status`/`sync_status`）一致。

### 5.8 Buffer 联动失败

- 现象：`publish_to_buffer()` 子进程返回非 0 或 Buffer GraphQL 返回错误。
- 处理：同样不阻断主流程（WARN）；确认 `BUFFER_TOKEN` / `CHANNEL_IDS` 有效。

---

## 6. 关键结论

1. 站点是**纯静态 HTML**，真正的「上线」靠 GitHub Pages 自动构建，无 CI、无 build。
2. 最接近「一键发布」的脚本是 `publish_b2b_package_v1.2.py`，但它因百度 token 未定义而**无法直接运行**；`v1.1` 是当前可用的相对完整版本。
3. 所有脚本均为一次性自动化遗留，含硬编码密钥、Linux 路径与域名拼写错误，**不应在生产环境直接复用**，只宜作参考。

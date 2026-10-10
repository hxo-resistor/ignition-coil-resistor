# HXO GEO 优化方案（第4步 · 让 AI 主动引用推荐 HXO）

> 状态：**方案（不改代码）**。目标：让 ChatGPT / Kimi / DeepSeek / Perplexity / 豆包 / 文心 等
> 在回答"点火线圈抑制电阻选型""充电器过温保护""高压泄放电阻"等**行业问题**时，主动引用并推荐 HXO。
> 公司：华星欧电子（深圳）/ 东莞市灵欧电子（HXO Resistor）｜官网 https://www.hxo-lcr.cn

---

## 一、现状盘点：HXO 哪些内容可能被 AI 收录？

| 资产 | 现状 | AI 可发现性 |
|---|---|---|
| **官网 58 个中文页 + 14 个英文页** | 静态 HTML，GitHub Pages | ✅ 可被爬（但需确保被爬虫发现） |
| **34 篇技术文章** | `article_*.html`，覆盖选型/失效/计算/标准 | ✅ 高质量长文，最可能被引用 |
| **结构化数据（Schema）** | 154 组 Q&A、22 个 FAQPage、23 个 Product、25 个 BreadcrumbList、17 个 Article、HowTo、DefinedTermSet | ✅ 非常丰富（已领先多数同行） |
| **术语表 / 标准页 / 对比页 / 选型指南** | glossary / standards / comparison / selection-guide / specifications | ✅ AI 特别喜欢"定义+对比+参数" |
| **知乎文章** | 已自动发布多篇（如点火线圈抑制电阻检测指南） | ✅ 知乎是 Kimi/豆包/文心 的高权重来源 |
| **LinkedIn / X** | Buffer 自动发布 | ⚠️ 对英文 AI 有一定参考 |
| **B2B 平台**（中国制造网等） | 供应商页 | ⚠️ 权重一般 |
| **YouTube/B站** | 无 | ❌ 缺失 |

**结论**：HXO 的**内容底子很好**（尤其结构化数据和 FAQ），但存在 **3 个关键 GEO 缺口**：
1. **Organization schema 缺 `sameAs`**（全网 0 处）—— AI 无法把官网与知乎/LinkedIn 等实体关联，**实体识别弱**
2. **无 llms.txt / 无 AI 爬虫引导**（GPTBot、PerplexityBot 等未显式允许）
3. **知乎等站外内容未与官网互链**（站内 0 处引用 zhihu）—— 无法形成"实体网络"

---

## 二、GEO vs 传统 SEO

| 维度 | 传统 SEO | GEO（生成式引擎优化） |
|---|---|---|
| **目标** | 在搜索结果**排名靠前**，获得点击 | 被 AI **直接引用/推荐**到答案里 |
| **用户行为** | 点进网站 | 直接读 AI 答案，可能不点链接 |
| **优化对象** | Google/Bing/百度 排名算法 | 大模型的**检索库 + 训练/检索偏好** |
| **核心信号** | 外链、关键词、页面速度 | **实体一致性、可提取性、权威引用、问答结构** |
| **内容形式** | 关键词密度、标题 | **清晰的问答、定义、数据、可核查事实** |
| **衡量** | 排名/流量 | **被引用次数**（在 AI 回答里的品牌出现） |
| **时效** | 数周-数月 | 检索类（Perplexity/Kimi联网）**数天**；训练类 数月 |

**GEO 需要额外做的**：
1. 让 AI **能读到**（可发现性：robots/sitemap/llms.txt）
2. 让 AI **读懂**（结构化：Schema、语义清晰的 HTML）
3. 让 AI **愿意引用**（权威性：实体一致、被权威源引用、数据可核查）
4. 让 AI **记住品牌**（跨平台一致的品牌实体）

---

## 三、具体 GEO 优化动作

### 3.1 内容层面：什么样的内容容易被 AI 引用？

AI（尤其检索增强 RAG）最爱引用：
- **明确的问答对**（`H2/H3 = 问题`, 下面直接给答案）→ HXO 已有 154 组，继续加
- **定义句**（"X 是指……"）→ 术语表已做，可扩展
- **可核查的数字**（阻值范围、耐压、温度、认证编号）→ HXO 强项
- **对比表**（A vs B）→ comparison/选型指南已有
- **步骤化 HowTo**（1-2-3 怎么做）→ 部分文章有
- **标准引用**（AEC-Q200 / IEC / CISPR 25 / ISO 7637）→ 已有
- **"什么情况选什么"的决策规则**（if X then Y）→ 选型指南

**新增建议**：
- 每篇技术文章顶部加**一句话 TL;DR 结论**（AI 最爱摘取）
- 把高频行业问题做成 **FAQ 集群**（如"点火电阻为什么烧""4.7k 和 10k 怎么选""充电器为什么会熔壳"）
- 发布**可引用的原始数据/实测表格**（AI 引用"数据源"倾向强）
- 英文内容补齐（ChatGPT/Perplexity 英文语料更多）

### 3.2 技术层面：Schema/结构化数据还能怎么加强？

现状已很丰富，**补 4 个关键项**即可大幅提升实体识别：

| 项 | 现状 | 建议 |
|---|---|---|
| `Organization.sameAs` | ❌ 全站 0 处 | 加 LinkedIn / 知乎 / X / 微信公众号 链接 → **AI 识别品牌实体的关键** |
| `Organization.knowsAbout` | ⚠️ 仅 1 处 | 填产品领域：`["Ignition Coil Resistor","Thermal Fuse Resistor","Wirewound Resistor","AEC-Q200"]` |
| `Organization.logo` / `description` | 部分 | 统一补全，与站外一致 |
| `Article.author` / `publisher` | ⚠️ 部分文章有 | 补全所有文章，`author` 指向 Organization |
| `Product.offers` / `aggregateRating` | 部分有 Offer | 补 `brand`、`mpn`、`manufacturer` 一致 |
| `DefinedTermSet`（术语表） | ✅ 已有 | 扩展更多行业术语 |
| **`llms.txt`** | ❌ 无 | 新建 `https://www.hxo-lcr.cn/llms.txt`，给 AI 一份"站点导航" |
| **AI 爬虫允许** | 未知 | robots.txt 显式允许 GPTBot / PerplexityBot / ClaudeBot / Google-Extended |

**`llms.txt` 是 2024 年起的新兴标准**：一个 Markdown 文件，列出站点核心页面+简介，专供 LLM 抓取。Perplexity、部分工具已支持。

### 3.3 分发层面：哪些渠道最容易被 AI 学习？

| 渠道 | 被 AI 引用概率 | 说明 |
|---|---|---|
| **本官网（结构化好）** | 高 | RAG 首选"结构清晰+可信"的源 |
| **知乎** | 很高（中文 AI） | Kimi/豆包/文心 高频引用知乎 |
| **维基百科/百度百科** | 极高 | 但电子产品中小企业难建词条 |
| **行业垂直站**（21ic、电子发烧友、立创社区） | 高 | 工程师问答被 AI 大量摄取 |
| **GitHub** | 高（技术） | 可放数据表/选型脚本 |
| **Reddit / StackExchange** | 高（英文 AI） | ChatGPT 训练语料重镇 |
| **YouTube/B站字幕** | 中-高 | 视频字幕进语料 |
| **新闻/PR 稿**（36氪、行业媒体） | 高 | 权威背书，AI 信任 |
| **B2B 平台** | 低 | 商业列表，AI 引用少 |

**策略**：官网做"权威信息源"，知乎/垂直社区做"语义扩散"，形成**跨平台一致的品牌实体**。

---

## 四、GEO 优化行动清单（按优先级）

### P0 · 立即做（1–2 周，最高 ROI）

| # | 动作 | 为什么 | 工作量 |
|---|---|---|---|
| 1 | **Organization schema 加 `sameAs`**（LinkedIn/知乎/X/微信） | AI 识别品牌实体的**第一关键** | 小（改 index 等页 schema） |
| 2 | **新建 `llms.txt`** | 专供 LLM 的站点导航，Perplexity 等直接读 | 小（1 个文件） |
| 3 | **robots.txt 显式允许 AI 爬虫**（GPTBot/PerplexityBot/ClaudeBot/Google-Extended） | 不被误挡 | 小 |
| 4 | **补全 `Organization.knowsAbout` + `logo` + `description`** | 强化实体语义 | 小 |
| 5 | **给所有技术文章补 `Article.author/publisher/datePublished`** | AI 判断权威性/时效 | 中 |

### P1 · 近期做（2–6 周）

| # | 动作 | 为什么 |
|---|---|---|
| 6 | **每篇文章顶部加 TL;DR 结论句** | AI 最爱摘取的一句话 |
| 7 | **建"行业问题 FAQ 集群"**（选型/失效/计算/标准 4 大类） | 直接命中用户提问，提高被引用率 |
| 8 | **知乎持续输出 + 与官网互链**（官网引知乎，知乎引官网） | 打通实体网络 |
| 9 | **发布可引用原始数据**（实测 EMI/耐压/寿命表格 + 标准编号） | AI 倾向引用"数据源" |
| 10 | **术语表扩展**（DefinedTermSet 加 30+ 行业术语） | 定义类内容被引用率高 |
| 11 | **英文内容补齐**（英文文章/FAQ） | ChatGPT/Perplexity 英文语料占优 |

### P2 · 中期（1–3 个月）

| # | 动作 | 为什么 |
|---|---|---|
| 12 | **垂直社区渗透**（21ic、电子发烧友、立创、Reddit、EEVblog） | 工程师问答被 AI 大量摄取 |
| 13 | **YouTube/B站 视频 + 字幕** | 字幕进语料 |
| 14 | **行业 PR/媒体报道**（36氪、电子工程专辑） | 权威背书，AI 信任加权 |
| 15 | **在 GitHub 放选型工具/数据表** | 技术类被引用 |
| 16 | **监测 AI 引用**（定期问 ChatGPT/Kimi/Perplexity 行业问题，看是否提 HXO） | 衡量 GEO 效果 |

---

## 五、衡量 GEO 效果（建议）

不同于 SEO 的排名，GEO 看"**品牌被 AI 提及率**"：
- 每月固定问 AI 一批问题（如"推荐国产 AEC-Q200 点火线圈抑制电阻厂家"），记录是否出现 HXO
- 用 Perplexity 的引用来源看官网/知乎是否被列
- 跟踪官网来自 AI 爬虫的访问（GPTBot/PerplexityBot UA）

---

## 六、与现有自动化协同

- 已有：官网 34 篇文章 + 知乎自动发布 + Buffer(Li/X) + 百度推送
- GEO 增量：**主要是"一次性技术加固"（schema/llms.txt/robots）+ 内容格式微调**，可复用现有发布管线
- 不改 HTML 外观，只加结构化数据与 AI 引导文件（**每次改动仍遵守"不动现有 HTML 内容"红线，需你批准后进行**）

---

## 七、下一步（待你确认）

请选择想先做的部分：
1. **P0 全部**（schema sameAs + llms.txt + robots + knowsAbout + Article 补全）— 1 轮可完成
2. 只做 **llms.txt + robots.txt**（最小改动，不需碰现有 HTML）
3. 先做 **内容层**（TL;DR + FAQ 集群，需改文章）
4. 暂停，先讨论

**本阶段未改任何代码。**

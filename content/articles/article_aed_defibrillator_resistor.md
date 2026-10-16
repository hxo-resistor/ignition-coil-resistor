---
filename_slug: article_aed_defibrillator_resistor
title: "AED除颤器里的『隐形守护者』：无感绕线电阻为何如此关键"
description: AED除颤器放电瞬间会产生数千伏双相高压脉冲，高阻值无感绕线电阻同时承担高压电容安全泄放与放电回路限流两项任务。本文从双相波形切换、寄生电感尖峰击穿IGBT的现象出发，给出无感绕线电阻的选型原理、HXO HVW系列（0.1Ω~651kΩ、1W~50W、耐压10kV+、寄生电感<0.1μH）参数表与典型应用场景，适用于医疗除颤及高压脉冲设备。
keywords: "AED除颤器,无感绕线电阻,HVW,高压脉冲电阻,双相波形,IGBT击穿,电容泄放电阻,医疗设备电阻,高压脉冲"
canonical: https://www.hxo-lcr.cn/article_aed_defibrillator_resistor.html
layout: nav
shell_head: |
  <!DOCTYPE html>
  <html lang="zh-CN">
  <head>
  <!-- Clarity tracking code -->
  <script>
  (function(c,l,a,r,i,t,y){ c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)}; t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i; y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y); })(window, document, "clarity", "script", "xrcejtxzio");
  </script>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <meta name="description" content="AED除颤器放电瞬间产生数千伏双相高压脉冲，高阻值无感绕线电阻同时承担高压电容安全泄放与放电回路限流两项任务。本文解析双相波形切换下寄生电感尖峰击穿IGBT的原理，给出HXO HVW系列（0.1Ω~651kΩ、1W~50W、耐压10kV+、寄生电感<0.1μH）选型参数与应用场景。">
      <meta name="keywords" content="AED除颤器,无感绕线电阻,HVW,高压脉冲电阻,双相波形,IGBT击穿,电容泄放电阻,医疗设备电阻,高压脉冲">
      <title>AED除颤器里的『隐形守护者』：无感绕线电阻为何如此关键 | HXO Resistor</title>
      <link rel="canonical" href="https://www.hxo-lcr.cn/article_aed_defibrillator_resistor.html">
  <style>
          * { margin: 0; padding: 0; box-sizing: border-box; }
          body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; color: #1a1a2e; line-height: 1.7; background: #fff; }
          .nav { background: rgba(26, 26, 46, 0.98); position: fixed; top: 0; left: 0; right: 0; z-index: 1000; height: 64px; }
          .nav-inner { max-width: 1200px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; padding: 0 24px; height: 100%; }
          .nav-logo { font-size: 1.3em; font-weight: 800; color: #fff; text-decoration: none; }
          .nav-logo span { color: #e94560; }
          .nav-links { display: flex; gap: 6px; list-style: none; }
          .nav-links a { color: #ccc; text-decoration: none; font-size: 0.85em; padding: 8px 14px; border-radius: 6px; }
          .nav-links a:hover { color: #fff; background: rgba(233,69,96,0.15); }
          .nav-links a.active { color: #e94560; background: rgba(233,69,96,0.12); }
          .nav-toggle { display: none; background: none; border: none; color: #fff; font-size: 1.5em; cursor: pointer; }
          @media (max-width: 768px) {
              .nav-links { display: none; position: absolute; top: 64px; left: 0; right: 0; background: #1a1a2e; flex-direction: column; padding: 12px; }
              .nav-links.open { display: flex; }
              .nav-toggle { display: block; }
          }
          .article-header { background: linear-gradient(135deg, #1a1a2e, #0f3460); color: #fff; padding: 100px 24px 50px; text-align: center; }
          .article-header h1 { font-size: 1.8em; font-weight: 800; max-width: 820px; margin: 0 auto 10px; }
          .article-header .meta { color: #8899b4; font-size: 0.85em; }
          .article-header .breadcrumb { color: #7a8aa5; font-size: 0.8em; margin-bottom: 12px; }
          .article-header .breadcrumb a { color: #e94560; text-decoration: none; }
          .container { max-width: 820px; margin: 0 auto; padding: 50px 24px; }
          .toc { background: #f5f7fa; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px 24px; margin: 0 0 30px; }
          .toc h3 { margin-bottom: 12px; font-size: 1em; }
          .toc ol { padding-left: 20px; }
          .toc li { margin: 6px 0; }
          .toc a { color: #0f3460; text-decoration: none; }
          h2 { color: #1a1a2e; font-size: 1.4em; margin: 34px 0 14px; border-left: 4px solid #e94560; padding-left: 14px; line-height: 1.4; }
          h3 { color: #0f3460; font-size: 1.1em; margin: 22px 0 10px; }
          p { margin-bottom: 14px; text-align: justify; }
          ul { margin: 0 0 16px 22px; }
          li { margin-bottom: 8px; }
          a { color: #e94560; }
          .table-wrap { overflow-x: auto; margin: 20px 0; }
          table { width: 100%; border-collapse: collapse; font-size: 0.92em; }
          th, td { padding: 10px 12px; border-bottom: 1px solid #e2e8f0; text-align: left; }
          th { background: #1a1a2e; color: #fff; }
          tr:hover td { background: #f7f9fc; }
          .highlight-box { background: #fff5f5; border-left: 4px solid #e94560; padding: 16px 18px; margin: 20px 0; border-radius: 0 8px 8px 0; }
          .info-box { background: #e8f5e9; border-left: 4px solid #27ae60; padding: 16px 18px; margin: 20px 0; border-radius: 0 8px 8px 0; }
          .warn-box { background: #fff8e1; border-left: 4px solid #f39c12; padding: 16px 18px; margin: 20px 0; border-radius: 0 8px 8px 0; }
          .cta { background: linear-gradient(135deg, #1a1a2e, #0f3460); color: #fff; padding: 30px 24px; border-radius: 10px; margin: 36px 0; text-align: center; }
          .cta h2 { color: #fff; border: none; padding: 0; margin-top: 0; }
          .cta .btn { display: inline-block; background: #e94560; color: #fff; padding: 12px 26px; border-radius: 6px; text-decoration: none; font-weight: 700; margin: 8px 6px; }
          .cta .btn-secondary { background: transparent; border: 1px solid #e94560; }
          .related-links { background: #f5f7fa; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px 24px; margin: 20px 0; }
          .back-link { display: inline-block; margin: 10px 0; color: #0f3460; text-decoration: none; }
          .footer { background: #1a1a2e; color: #8899b4; padding: 30px 24px; text-align: center; font-size: 0.85em; margin-top: 40px; }
          .footer a { color: #ccc; text-decoration: none; margin: 0 6px; }
  </style>
  <script type="application/ld+json">
  {
   "@context": "https://schema.org",
   "@type": "BreadcrumbList",
   "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "首页", "item": "https://www.hxo-lcr.cn/"},
    {"@type": "ListItem", "position": 2, "name": "技术文章", "item": "https://www.hxo-lcr.cn/articles.html"},
    {"@type": "ListItem", "position": 3, "name": "AED除颤器里的『隐形守护者』：无感绕线电阻为何如此关键", "item": "https://www.hxo-lcr.cn/article_aed_defibrillator_resistor.html"}
   ]
  }
  </script>
  <script type="application/ld+json">
  {
   "@context": "https://schema.org",
   "@type": "Article",
   "headline": "AED除颤器里的『隐形守护者』：无感绕线电阻为何如此关键",
   "description": "AED除颤器放电瞬间产生数千伏双相高压脉冲，高阻值无感绕线电阻同时承担高压电容安全泄放与放电回路限流。本文解析双相波形切换下寄生电感尖峰击穿IGBT的原理，给出HXO HVW系列（0.1Ω~651kΩ、1W~50W、耐压10kV+、寄生电感<0.1μH）选型参数。",
   "image": [
    "https://www.hxo-lcr.cn/product_overview.jpg"
   ],
   "datePublished": "2026-10-16",
   "dateModified": "2026-10-16",
   "author": {"@type": "Organization", "name": "HXO Resistor", "url": "https://www.hxo-lcr.cn/"},
   "publisher": {
    "@type": "Organization",
    "name": "HXO Resistor",
    "logo": {"@type": "ImageObject", "url": "https://www.hxo-lcr.cn/product_overview.jpg"}
   },
   "mainEntityOfPage": {"@type": "WebPage", "@id": "https://www.hxo-lcr.cn/article_aed_defibrillator_resistor.html"},
   "mentions": [
    {"@type": "Thing", "name": "HVW 高阻值无感绕线电阻"},
    {"@type": "Thing", "name": "AED 自动体外除颤器放电回路"},
    {"@type": "Thing", "name": "双相高压脉冲波形"}
   ]
  }
  </script>
  <script type="application/ld+json">
  {
   "@context": "https://schema.org",
   "@type": "FAQPage",
   "mainEntity": [
    {
     "@type": "Question",
     "name": "AED为什么要用无感电阻？",
     "acceptedAnswer": {"@type": "Answer", "text": "AED放电采用双相（Biphasic）波形：几千伏脉冲先按一个方向输出几十毫秒，再在极短时间内反向输出。回路中的电阻如果带有寄生电感，电流换向瞬间会产生 L·di/dt 电压尖峰，叠加在数千伏母线之上，直接加到放电开关（IGBT/H桥）两端。若尖峰超过开关管的耐压余量，就会雪崩击穿。无感绕线电阻采用 Ayrton-Perry 或同向双绕组等结构把寄生电感压到 0.1μH 以下，从源头消除这一尖峰。"}
    },
    {
     "@type": "Question",
     "name": "高阻值和低阻值在AED里怎么选？",
     "acceptedAnswer": {"@type": "Answer", "text": "按功能区分：串在电网/人体放电回路里做限流的电阻用低阻值（几Ω~几百Ω），它决定放电电流峰值和除颤能量输出；并联在高压储能电容两端做安全泄放的电阻用高阻值（几十kΩ~651kΩ），它只在断电后把电容电压降到安全范围，正常工作时几乎不耗电。同一台AED往往同时需要这两种，不能用一个阻值兼顾。"}
    },
    {
     "@type": "Question",
     "name": "AED里的无感绕线电阻需要多高耐压？",
     "acceptedAnswer": {"@type": "Answer", "text": "AED储能电容电压通常在1kV~3kV量级，部分除颤/高压脉冲设备更高。选型时耐压必须覆盖母线电压+换向尖峰+绝缘裕量，工程上建议耐压等级≥10kV（AC rms, 1min），并配合≥1000MΩ绝缘电阻和低漏电流设计，避免高压端沿面爬电与漏电干扰。"}
    },
    {
     "@type": "Question",
     "name": "寄生电感多大才算『无感』？",
     "acceptedAnswer": {"@type": "Answer", "text": "没有绝对为零的电感，只要求在工作频段内产生的尖峰可忽略。AED双相换向在微秒级完成，行业经验判据是单只电阻寄生电感<0.1μH（HXO HVW系列实测值），此时 L·di/dt 尖峰通常只有几十伏量级，远低于IGBT的耐压余量，可以认为对该应用是『无感』的。"}
    },
    {
     "@type": "Question",
     "name": "无感绕线电阻的功率怎么定？",
     "acceptedAnswer": {"@type": "Answer", "text": "AED是脉冲工作制，不是连续加载。放电脉冲宽度只有几到几十毫秒，两次放电间隔通常数分钟以上，所以功率按脉冲能量与占空比折算平均功耗，再留2倍以上余量。HXO HVW系列覆盖1W~50W，多数AED泄放/限流位选用5W~10W即可，若设备放电频率高或含连续高压测试模式，请提供占空比由我们重新核算。"}
    }
   ]
  }
  </script>
  <script type="application/ld+json">
  {
   "@context": "https://schema.org",
   "@type": "WebSite",
   "name": "HXO Resistor - 点火线圈电阻与放电电阻",
   "url": "https://www.hxo-lcr.cn/",
   "description": "HXO 提供 HVW 无感绕线电阻、IG 系列点火电阻与 RXF 温度保险电阻，交期 7-15 天。",
   "inLanguage": ["zh-CN", "en"]
  }
  </script>
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-X6WNVWY7LC"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-X6WNVWY7LC');
  </script>
  </head>
  <body>
  <nav class="nav">
      <div class="nav-inner">
          <a href="./" class="nav-logo">HXO<span>.</span></a>
          <button class="nav-toggle" onclick="document.querySelector('.nav-links').classList.toggle('open')">菜单</button>
          <ul class="nav-links">
              <li><a href="./">首页</a></li><li><a href="./products/ignition-coil.html">点火线圈抑制电阻</a></li>
  <li><a href="./products/otp-fuse.html">OTP 2合1保险丝电阻</a></li>
  <li><a href="./products/wirewound.html">高阻值绕线电阻</a></li>
              
              
              
              <li><a href="./comparison.html">产品对比</a></li>
              <li><a href="./specifications.html">规格参数</a></li>
              <li><a href="./selection-guide.html">选型指南</a></li>
              <li><a href="./case-studies.html">客户案例</a></li>
              <li><a href="./standards.html">标准认证</a></li>
              <li><a href="./articles.html" class="active">技术文章</a></li>
              <li><a href="./faq.html">FAQ</a></li>
              <li><a href="./#inquiry">询盘/联系</a></li>
          </ul>
      </div>
  </nav>
  <div class="article-header">
      <div class="breadcrumb"><a href="./">首页</a> › <a href="./articles.html">技术文章</a> › AED除颤器无感绕线电阻</div>
      <h1>AED除颤器里的"隐形守护者"：无感绕线电阻为何如此关键</h1>
      <div class="meta">HXO Resistor 技术部 · 高压脉冲 / 医疗设备 · 2026-10-16 · 约 1800 字</div>
  </div>
  <div class="container">
meta_info: ""
shell_tail: |
  </div>
  <div class="footer">
      <div class="footer-links">
          <a href="./">首页</a> <a href="./ig-c.html">IG-C</a> <a href="./ig-f.html">IG-F</a> <a href="./ig-s.html">IG-S</a>
          <a href="./comparison.html">产品对比</a> <a href="./specifications.html">规格参数</a> <a href="./articles.html">技术文章</a> <a href="./faq.html">FAQ</a>
          <a href="mailto:resistor@hxo-lcr.cn">resistor@hxo-lcr.cn</a>
      </div>
      <p>© 2026 HXO Resistor / AED除颤器无感绕线电阻选型</p>
  </div>
  <script>
  (function(){
      var bp = document.createElement('script');
      var curProtocol = window.location.protocol.split(':')[0];
      if (curProtocol === 'https') {
          bp.src = 'https://zz.bdstatic.com/linksubmit/push.js';
      } else {
          bp.src = 'http://push.zhanzhang.baidu.com/push.js';
      }
      var s = document.getElementsByTagName('script')[0];
      s.parentNode.insertBefore(bp, s);
  })();
  </script>
  </body>
  </html>

---

:::raw
<div class="toc">
    <h3>本文目录</h3>
    <ol>
        <li><a href="#problem">现象：AED放电一瞬间发生了什么</a></li>
        <li><a href="#roles">高阻值无感电阻的两个作用</a></li>
        <li><a href="#why-noninductive">为什么必须"无感"</a></li>
        <li><a href="#solution">HXO HVW 系列方案与参数</a></li>
        <li><a href="#scenario">典型应用场景</a></li>
        <li><a href="#faq">常见问题</a></li>
    </ol>
</div>
:::

:::raw
<h2 id="problem">现象：AED放电一瞬间发生了什么</h2>
:::

AED（自动体外除颤器）的工作节奏可以用"**长时间待机 + 一瞬间爆发**"来概括。待机时它安静地监测心电，一旦判定需要除颤，内部高压电路会在数秒内把储能电容充到 **1kV~3kV**，随后在一次几毫秒到几十毫秒的放电窗口里，把能量通过电极板经人体释放出去。

以典型的双相（Biphasic）除颤为例：电流先沿一个方向输出一段时间，再迅速反向输出一段——两个方向的脉冲共同构成一次除颤波形。整个过程里，放电回路承受的是**数千伏的高压脉冲 + 极快的电流换向**，而回路上几乎每个位置都装着电阻：

- 储能电容两端：**泄放电阻**，负责断电后把电容电压降到安全值；
- 放电回路中：**限流电阻**，决定放电电流峰值与能量输出形状；
- 高压采样/分压支路：**分压电阻**，把高压按比例降到ADC可测范围。

这些电阻平时"看不见"，但只要其中一颗在关键瞬间失效，整台设备要么报错自检失败，要么在最需要它工作的那一刻掉链子。这就是我们称它为"隐形守护者"的原因。

:::raw
<div class="highlight-box"><p><strong>工况要点</strong>：AED放电回路的特征是「高压 + 脉冲 + 快速换向」。这与普通电源里"低压 + 连续 + 单方向"的电阻工况完全不同，选型思路也不能照搬。</p></div>
:::

:::raw
<h2 id="roles">高阻值无感电阻的两个作用</h2>
:::

### 作用一：高压电容安全泄放

设备关机、故障或自检时，储能电容不会自动变空——它仍然带着数千伏电荷。如果没有泄放通路，电压会维持相当长时间，维修人员或使用者一旦接触高压端就有触电风险。

泄放电阻**永久并联**在高压电容两端，断电后作为放电通路，让电容电压按 τ=RC 指数衰减，把电压降到安全阈值以下。选型核心是**阻值上限**与**耐压等级**：

`R ≤ 1 / (C · ln(V₀/V_safe))`

阻值取得过小会在正常工作时常耗发热，取得过大则泄放太慢，必须按电容值和目标泄放时间核算。

### 作用二：放电回路限流保护

放电瞬间，储能电容相当于一个内阻极低的数千伏电源。如果直接短接，电流会冲到极高值，既损伤电极与人体接触面，也会烧毁 IGBT、MOSFET 或继电器等放电开关。

在放电回路中串入合适的**限流电阻**，可以：

- 把放电电流峰值钳制在设计与安规允许的范围内；
- 塑造脉冲波形，让输出能量符合除颤波形要求；
- 限制开关管在开通瞬间承受的电流应力，提高可靠性。

:::raw
<div class="info-box"><p><strong>一个容易混淆的点</strong>：泄放电阻是<b>高阻值</b>（数十kΩ级，几乎不透电流），限流电阻是<b>低阻值</b>（几Ω~几百Ω级，要通大电流）。它们虽然都叫"高压脉冲电阻"，但阻值区间、功率算法、安装位置完全不同，不能互相替代。</p></div>
:::

:::raw
<h2 id="why-noninductive">为什么必须"无感"</h2>
:::

普通绕线电阻是把电阻丝绕在骨架上，线圈天然是一颗电感。对直流或低频回路这没什么问题，但在 AED 的双相切换里，它会直接带来两个后果。

**其一，换向尖峰。** 电感电压遵循 `V = L · di/dt`。双相波形的电流在**微秒级**完成反向，di/dt 极大。哪怕只有几微亨的寄生电感，也能在换向瞬间产生几百伏到上千伏的反向尖峰，叠加在原本就数千伏的母线上。

**其二，尖峰击穿开关管。** 这个尖峰首当其冲加载在放电开关（IGBT / H桥）两端。开关管的耐压是按母线电压加固定裕量设计的，一旦尖峰把总电压推过耐压极限，器件会进入雪崩击穿——轻则一次放电后损坏，重则短路失效。而且这类失效往往是**偶发、难以复现**的，排查成本极高。

此外，寄生电感还会让脉冲波形产生振荡与过冲，影响放电能量的准确输出，对除颤效果的一致性不利。

:::raw
<div class="warn-box"><p><strong>结论</strong>：在AED这类双相高压脉冲回路里，"无感"不是加分项而是<b>入门项</b>。判断标准不是"标称是绕线电阻"，而是实测寄生电感是否足够低。</p></div>
:::

:::raw
<h2 id="solution">HXO HVW 系列方案与参数</h2>
:::

针对医疗除颤与高压脉冲设备，HXO **HVW 系列无感绕线电阻**通过 Ayrton-Perry / 同向双绕组等绕制结构，把寄生电感压到 **0.1μH 以下**，在双相换向时几乎不产生附加尖峰；同时提供从低阻限流到高阻泄放的完整阻值覆盖。

:::raw
<div class="table-wrap">
<table>
    <tr><th>参数项</th><th>HXO HVW 系列规格</th><th>对AED/高压脉冲设备的意义</th></tr>
    <tr><td>阻值范围</td><td><strong>0.1Ω ~ 651kΩ</strong></td><td>低阻端做放电回路限流，高阻端做高压电容泄放</td></tr>
    <tr><td>额定功率</td><td><strong>1W ~ 50W</strong></td><td>按脉冲占空比折算平均功耗后留余量</td></tr>
    <tr><td>耐压等级</td><td><strong>10kV+</strong>（AC rms, 1min）</td><td>覆盖数千伏母线 + 换向尖峰 + 绝缘裕量</td></tr>
    <tr><td>寄生电感</td><td><strong>&lt;0.1 μH</strong></td><td>双相快速换向不产生击穿级尖峰</td></tr>
    <tr><td>绝缘电阻</td><td>≥1000 MΩ @500V DC</td><td>高压端安全与低漏电基础</td></tr>
    <tr><td>阻值精度</td><td>±1% / ±5% / ±10%（可选）</td><td>保证放电能量输出一致性</td></tr>
    <tr><td>温度系数</td><td>低TCR 绕线结构</td><td>温升后阻值漂移小，波形稳定</td></tr>
    <tr><td>安装形式</td><td>轴向/立式、接线端子、面板安装</td><td>适配高压端安全爬电距离要求</td></tr>
</table>
</div>
:::

:::raw
<div class="table-wrap">
<table>
    <tr><th>回路位置</th><th>推荐阻值区间</th><th>推荐功率</th><th>关注重点</th></tr>
    <tr><td>放电回路限流</td><td>0.1Ω ~ 数百Ω</td><td>10W ~ 50W</td><td>峰值电流、脉冲能量、寄生电感</td></tr>
    <tr><td>高压电容泄放</td><td>数十kΩ ~ 651kΩ</td><td>1W ~ 5W</td><td>泄放时间常数、耐压、低漏电</td></tr>
    <tr><td>高压分压采样</td><td>高阻端 kΩ ~ MΩ级（按分压比）</td><td>1W ~ 5W</td><td>精度、TCR、长期稳定性</td></tr>
</table>
</div>
:::

:::raw
<div class="warn-box"><p><strong>合规说明</strong>：本文所述应用为<b>医疗除颤设备 / 高压脉冲设备</b>的电路器件选型，HXO HVW 系列是通用高压脉冲无感绕线电阻，不构成对任何整机医疗设备的认证或对特定治疗用途的宣称。整机合规请以设备厂家的医疗器械注册与安规测试结论为准。</p></div>
:::

:::raw
<h2 id="scenario">典型应用场景</h2>
:::

- **AED / 除颤仪放电回路**：串入限流电阻塑造双相波形，抑制换向尖峰对 IGBT 的冲击。
- **储能电容泄放回路**：断电后把高压母线降到安全阈值，保障维修与使用安全。
- **高压脉冲发生设备**：如脉冲电源、高压测试台的脉冲限流与阻尼。
- **IGBT 保护 / 吸收网络**：配合 RC 吸收，抑制换向过冲，降低器件应力。
- **高压分压与采样**：为控制板提供可测的低压采样信号。

如果你的设备同时包含放电限流与安全泄放两个位置，通常需要**分别选用低阻与高阻两种规格**，而不是用一颗电阻折中。

:::raw
<h2 id="faq">常见问题</h2>
:::

### AED为什么要用无感电阻？

AED放电采用双相波形，电流在微秒级反向。回路电阻的寄生电感会产生 `L·di/dt` 尖峰，叠加数千伏母线后可能击穿放电开关。无感绕线结构把寄生电感压到 0.1μH 以下，从源头消除该尖峰。

### 高阻值和低阻值在AED里怎么选？

按功能选：放电回路限流用低阻值（几Ω~几百Ω），它决定放电电流峰值；高压电容泄放用高阻值（数十kΩ~651kΩ），只在断电后工作、正常工作几乎不耗电。两者不能互相替代。

### AED里的无感绕线电阻需要多高耐压？

AED母线通常 1kV~3kV，部分高压脉冲设备更高。耐压应覆盖母线电压+换向尖峰+绝缘裕量，建议 ≥10kV（AC rms, 1min），并配合 ≥1000MΩ 绝缘电阻与低漏电设计。

### 寄生电感多大才算"无感"？

没有绝对为零的电感。行业经验判据是单只电阻寄生电感 <0.1μH，此时微秒级换向产生的尖峰仅几十伏量级，远低于开关管耐压余量，可视为"无感"。

### 无感绕线电阻的功率怎么定？

AED是脉冲工作制。按脉冲能量与占空比折算平均功耗、留2倍以上余量；HVW 系列覆盖 1W~50W，多数位选 5W~10W 即可。放电频率高或含连续高压模式时，请提供占空比重新核算。

:::raw
<div class="cta">
    <h2>需要 AED / 高压脉冲回路的电阻方案</h2>
    <p>把母线电压、储能电容值、放电电流峰值与脉冲占空比发给我们，HXO 出无感绕线电阻选型 + 定制方案（低阻限流 / 高阻泄放分开核算）。</p>
    <a href="./#inquiry" class="btn">索取选型方案</a>
    <a href="./order.html" class="btn btn-secondary">查看订单入口</a>
</div>
:::

:::raw
<div class="related-links">
    <h3>延伸阅读</h3>
    <ul>
        <li><a href="./article_hvw_resistor.html">HVW 高阻值绕线电阻：参数、结构与选型要点</a></li>
        <li><a href="./article_xray_bleeder_resistor.html">高压电阻在X光机中的应用：如何选择合适的泄放电阻</a></li>
        <li><a href="./article_discharge_calculation.html">泄放电阻计算指南：变频器制动系统完整选型方法</a></li>
        <li><a href="./article_ev_pile_bleeder.html">新能源充电桩电容泄放电阻选型</a></li>
    </ul>
</div>
:::

:::raw
<a href="./articles.html" class="back-link">‹ 返回技术文章列表</a>
:::

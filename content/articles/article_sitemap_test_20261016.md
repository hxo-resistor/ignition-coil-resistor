---
title: "sitemap 自动化测试文章（临时）"
description: 用于验证 publish_all.py 的 sitemap.xml 自动追加与 articles.html 索引同步功能，验证完成后可删除。
keywords: "sitemap,自动化测试,临时文章"
---

这是一篇用于验证发布流水线 sitemap 自动追加功能的临时测试文章。

## 验证目标

- publish_all.py 在 website 动作前把新 URL 追加进 sitemap.xml（幂等、仅追加）
- 同步把条目插入 articles.html 索引
- 二者由 website 动作的 git add/commit/push 一并提交

验证完成后本文件与对应索引/sitemap 条目将被移除。

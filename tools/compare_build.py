#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/compare_build.py — 阶段1 对比验证

把 build/<slug>.html 与原仓库页面逐项比对：标题、description、keywords、
canonical、Schema、埋点（Clarity/GA4/Baidu）、<style>、正文文本、正文结构、
链接、footer。输出 Markdown 对比报告到 build/compare_report.md。
"""

import argparse
import difflib
import html as html_mod
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent


def strip_tags(s: str) -> str:
    s = re.sub(r"<(script|style)\b.*?</\1>", "", s, flags=re.S | re.I)
    # 仅移除形如 <tag ...> / </tag> 的标签，避免误删正文里的孤立的 "<"
    s = re.sub(r"</?[A-Za-z][A-Za-z0-9]*(\s[^<>]*)?/?>", "", s)
    s = html_mod.unescape(s)
    s = re.sub(r"[ \t\u00a0]+", " ", s)
    lines = [ln.strip() for ln in s.splitlines()]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)


def get_meta(text: str, name: str):
    m = re.search(rf'<meta\s+name="{re.escape(name)}"\s+content="(.*?)">', text, re.S)
    return m.group(1) if m else None


def get_title(text: str):
    m = re.search(r"<title>(.*?)</title>", text, re.S)
    return m.group(1) if m else None


def get_schema(text: str):
    m = re.search(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return m.group(1).strip()


def get_all_schemas_raw(text: str):
    """返回所有 JSON-LD 块的原始文本列表（不做 JSON 解析，保真对比）。"""
    return [m.strip() for m in re.findall(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>', text, re.S)]


def schema_parse_errors(text: str):
    """返回每个 JSON-LD 块的解析结果：[(index, ok, error_text)]。"""
    out = []
    for i, block in enumerate(get_all_schemas_raw(text), 1):
        try:
            json.loads(block)
            out.append((i, True, None))
        except json.JSONDecodeError as e:
            out.append((i, False, f"{e.msg} (line {e.lineno}, col {getattr(e, 'colno', '?')})"))
    return out


def get_article_inner(text: str):
    """正文区域：PILOT=?<article>；NAV=<div class="container">；LEGACY=header 之后到 .cta 之前。"""
    m = re.search(r"<article>(.*)</article>", text, re.S)
    if m:
        return m.group(1)
    if '<div class="container">' in text:
        return get_container_inner(text)
    hm = re.search(r'<div class="header">', text)
    if hm:
        head_end = _match_div_close(text, hm.start())
        cta = re.search(r'<div class="cta"', text[head_end:])
        ftr = re.search(r'<div class="footer"', text[head_end:])
        cands = []
        if cta:
            cands.append(head_end + cta.start())
        if ftr:
            cands.append(head_end + ftr.start())
        tail_start = min(cands) if cands else len(text)
        return text[head_end:tail_start]
    return ""


def _match_div_close(text, open_start):
    tag_re = re.compile(r"<(/?)div\b[^>]*>", re.I)
    depth = 0
    for m in tag_re.finditer(text, open_start):
        if m.group(1) == "/":
            depth -= 1
            if depth == 0:
                return m.end()
        else:
            depth += 1
    return -1


def get_container_inner(text: str):
    m = re.search(r'<div class="container">', text)
    if not m:
        return ""
    end = _match_div_close(text, m.start())
    close = text.rfind("</div>", m.start(), end)
    return text[m.end():close]


def extract_div_by_class(text: str, cls: str):
    """按 class 提取一个 div 的完整 HTML（深度感知）。"""
    m = re.search(rf'<div class="{re.escape(cls)}">', text)
    if not m:
        return None
    end = _match_div_close(text, m.start())
    return text[m.start():end] if end != -1 else None


def re_group(pattern, text):
    m = re.search(pattern, text, re.S)
    return m.group(0) if m else None


def detect_layout(text: str) -> str:
    if '<div class="container">' in text and '<article>' not in text:
        return "nav"
    if '<article>' in text:
        return "pilot"
    if '<div class="header">' in text:
        return "legacy"
    return "pilot"


def collect_links(text: str):
    return re.findall(r'href="([^"]+)"', text)


def collect_classes(text: str):
    return re.findall(r'class="([^"]+)"', text)


def normalized_html(s: str) -> str:
    s = re.sub(r">\s+<", "><", s.strip())
    s = re.sub(r"\s+", " ", s)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default="article_hvw_braking")
    ap.add_argument("--build", default=str(ROOT / "build"))
    ap.add_argument("--original", default=None)
    ap.add_argument("--report", default=str(ROOT / "build" / "compare_report.md"))
    args = ap.parse_args()

    built_path = Path(args.build) / f"{args.slug}.html"
    orig_path = Path(args.original) if args.original else ROOT / f"{args.slug}.html"

    built = built_path.read_text(encoding="utf-8")
    orig = orig_path.read_text(encoding="utf-8")

    checks = []
    diffs = []

    def check(name, a, b):
        ok = a == b
        checks.append((name, ok, a, b))
        return ok

    check("`<title>`", get_title(orig), get_title(built))
    check("meta description", get_meta(orig, "description"), get_meta(built, "description"))
    check("meta keywords", get_meta(orig, "keywords"), get_meta(built, "keywords"))
    check("canonical", re_group(r'rel="canonical" href="([^"]+)"', orig),
          re_group(r'rel="canonical" href="([^"]+)"', built))

    # Schema：对比所有 JSON-LD 块的原始文本（保真，不因 JSON 语法错误而跳过）
    check("JSON-LD Schema（全部块，原样）", get_all_schemas_raw(orig), get_all_schemas_raw(built))

    # 埋点
    check("Clarity ID", "xrcejtxzio" in orig, "xrcejtxzio" in built)
    check("GA4 ID (G-X6WNVWY7LC)", "G-X6WNVWY7LC" in orig, "G-X6WNVWY7LC" in built)
    check("Baidu push.js", "linksubmit/push.js" in orig, "linksubmit/push.js" in built)

    # <style>
    so = re.search(r"<style>(.*?)</style>", orig, re.S).group(1).strip()
    sb = re.search(r"<style>(.*?)</style>", built, re.S).group(1).strip()
    check("内联 <style> CSS", so, sb)

    # 正文文本（去空白比较，避免缩进/换行/表格单元格换行造成的假差异）
    ao, ab = strip_tags(get_article_inner(orig)), strip_tags(get_article_inner(built))
    text_ok = re.sub(r"\s+", "", ao) == re.sub(r"\s+", "", ab)
    checks.append(("正文文本（忽略空白）", text_ok, ao, ab))
    if not text_ok:
        diffs.append(("正文文本差异", "\n".join(
            difflib.unified_diff(ao.splitlines(), ab.splitlines(), "original", "build", lineterm=""))))

    # 正文结构（标签序列）：忽略 Markdown 自动补的 thead/tbody 包裹标签
    TAG_RE = r"<(h2|h3|h4|p|ul|ol|li|table|tr|th|td|pre|div|a)\b"
    to = re.findall(TAG_RE, get_article_inner(orig))
    tb = re.findall(TAG_RE, get_article_inner(built))
    check("正文标签结构序列", to, tb)

    # 链接
    check("全站链接集合", sorted(set(collect_links(orig))), sorted(set(collect_links(built))))

    # class 集合
    check("CSS class 集合", sorted(set(collect_classes(orig))), sorted(set(collect_classes(built))))

    # 外壳区块（按版式选择对应选择器）
    layout = detect_layout(orig)
    if layout == "nav":
        shell_specs = [
            ("nav 导航栏", lambda t: re_group(r'<nav class="nav">.*?</nav>', t)),
            ("article-header（标题/面包屑/meta）", lambda t: extract_div_by_class(t, "article-header")),
            ("toc 目录", lambda t: extract_div_by_class(t, "toc")),
            ("related-links 相关阅读", lambda t: extract_div_by_class(t, "related-links")),
            ("footer", lambda t: extract_div_by_class(t, "footer")),
        ]
    elif layout == "legacy":
        shell_specs = [
            ("nav 导航栏", lambda t: extract_div_by_class(t, "nav")),
            ("header", lambda t: extract_div_by_class(t, "header")),
            ("cta", lambda t: extract_div_by_class(t, "cta")),
            ("footer", lambda t: extract_div_by_class(t, "footer")),
        ]
    else:
        shell_specs = [
            ("header", lambda t: re_group(r"<header>.*?</header>", t)),
            ("breadcrumb", lambda t: extract_div_by_class(t, "breadcrumb")),
            ("meta-info（标签+日期）", lambda t: extract_div_by_class(t, "meta-info")),
            ("footer", lambda t: re_group(r"<footer>.*?</footer>", t)),
        ]
    for name, getter in shell_specs:
        a = getter(orig)
        b = getter(built)
        check(name, normalized_html(a) if a else None, normalized_html(b) if b else None)

    passed = sum(1 for _, ok, *_ in checks if ok)
    total = len(checks)

    lines = []
    lines.append(f"# 阶段1 对比报告 — {args.slug}\n")
    lines.append(f"- 原文件: `{orig_path.relative_to(ROOT).as_posix()}`")
    lines.append(f"- 生成文件: `{built_path.relative_to(ROOT).as_posix()}`")
    lines.append(f"- 结果: **{passed}/{total} 项一致**\n")
    lines.append("| # | 检查项 | 结果 |")
    lines.append("|---|--------|------|")
    for i, (name, ok, *_ ) in enumerate(checks, 1):
        lines.append(f"| {i} | {name} | {'✅ 一致' if ok else '❌ 不一致'} |")

    failed = [(n, a, b) for n, ok, a, b in checks if not ok]
    if failed:
        lines.append("\n## 不一致明细\n")
        for name, a, b in failed:
            lines.append(f"### {name}\n")
            lines.append("```diff")
            sa = json.dumps(a, ensure_ascii=False, indent=2) if not isinstance(a, str) else a
            sb = json.dumps(b, ensure_ascii=False, indent=2) if not isinstance(b, str) else b
            for d in difflib.unified_diff(str(sa).splitlines(), str(sb).splitlines(),
                                          "original", "build", lineterm=""):
                lines.append(d)
            lines.append("```\n")
    else:
        lines.append("\n## 结论\n")
        lines.append("所有检查项一致。build/ 产物可 1:1 替代原文件（本阶段未替换）。\n")

    report = "\n".join(lines)
    Path(args.report).write_text(report, encoding="utf-8")
    print(report)
    print(f"\n报告已写入: {args.report}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())

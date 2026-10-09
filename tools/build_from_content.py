#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/build_from_content.py  —  Markdown 内容管线（阶段1 试点）

用途：
    读取 content/articles/*.md（YAML front matter + Markdown 正文），
    使用 HTML 模板渲染成与原站完全一致的整页 HTML，
    输出到 build/ 临时目录（绝不覆盖仓库根目录的现有 .html）。

设计原则（红线）：
    * 不写入、不替换任何现有 HTML 文件。
    * 幂等：重复运行输出结果一致。
    * 无第三方 YAML 依赖（仅标准库 + markdown）。

模板来源：
    站点每个页面都把 nav/footer/analytics/schema 内联复制，没有共享模板。
    因此本脚本把现有页面作为「模板来源」——从模板文件里提取
    <head> 固定部分（analytics 埋点 + <style>）、header/breadcrumb/
    article 外壳、footer、百度推送脚本。正文（<article> 内的动态部分）
    完全由 Markdown + front matter 生成。

用法：
    python tools/build_from_content.py
    python tools/build_from_content.py --content content/articles --out build
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

try:
    import markdown
except ImportError:  # pragma: no cover
    sys.stderr.write("缺少依赖：markdown。请先 `pip install markdown`。\n")
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# 1. 极简 front matter 解析（仅支持本管线用到的 YAML 子集，零依赖）
# ---------------------------------------------------------------------------
def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def _parse_scalar(value: str):
    v = value.strip()
    if v == "":
        return None
    low = v.lower()
    if low in ("true", "false"):
        return low == "true"
    if low in ("null", "~"):
        return None
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return _strip_quotes(v)


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _dedent_block(raw):
    """去掉块标量的公共缩进。空行（含仅空白行）按同量裁剪以保真。"""
    indents = [_indent(ln) for ln in raw if ln.strip()]
    cut = min(indents) if indents else 0
    out = []
    for ln in raw:
        if len(ln) >= cut:
            out.append(ln[cut:])
        else:
            out.append("")
    return "\n".join(out)


def parse_front_matter(text: str):
    """返回 (meta: dict, body: str)。仅支持映射 / 列表 / 列表内映射。"""
    if not text.startswith("---"):
        raise ValueError("缺少 front matter（文件需以 --- 开头）")
    end = text.find("\n---", 3)
    if end == -1:
        raise ValueError("front matter 未闭合（缺少结尾 ---）")
    fm = text[3:end].strip("\n")
    body = text[end + 4:].lstrip("\n")

    # 先去掉注释行
    lines = [ln for ln in fm.splitlines() if not ln.lstrip().startswith("#")]

    def parse_block(block, base_indent):
        """解析同缩进层级的块，返回 dict 或 list。"""
        # 判断是列表还是映射
        first = next((ln for ln in block if ln.strip()), "")
        is_list = first.strip().startswith("- ")

        if is_list:
            items = []
            i = 0
            while i < len(block):
                ln = block[i]
                if not ln.strip():
                    i += 1
                    continue
                if ln.strip().startswith("- "):
                    rest = ln.strip()[2:]
                    if ":" in rest and not rest.startswith("\"") and not rest.startswith("'"):
                        # 列表内映射起始
                        key, _, val = rest.partition(":")
                        key = key.strip().strip("\"'")
                        item = {}
                        parsed = _parse_scalar(val)
                        if parsed is not None:
                            item[key.strip()] = parsed
                        else:
                            # 值在后续更深缩进行
                            j = i + 1
                            sub = []
                            while j < len(block) and (not block[j].strip() or _indent(block[j]) > base_indent + 1):
                                sub.append(block[j])
                                j += 1
                            item[key.strip()] = parse_block(sub, base_indent + 2) if sub else None
                            i = j
                            items.append(item)
                            continue
                        # 收集同一 item 的后续键
                        j = i + 1
                        while j < len(block) and (not block[j].strip() or _indent(block[j]) > base_indent + 1) and not block[j].strip().startswith("- "):
                            subkey, _, subval = block[j].strip().partition(":")
                            item[subkey.strip().strip("\"'")] = _parse_scalar(subval)
                            j += 1
                        items.append(item)
                        i = j
                    else:
                        items.append(_parse_scalar(rest))
                        i += 1
                else:
                    i += 1
            return items

        # 映射
        result = {}
        i = 0
        while i < len(block):
            ln = block[i]
            if not ln.strip():
                i += 1
                continue
            key, sep, val = ln.strip().partition(":")
            if not sep:
                i += 1
                continue
            key = key.strip().strip("\"'")
            val_stripped = val.strip()
            # YAML 块标量：| 或 |-（保留换行）；> 折叠标量（段落间保留空行，段内换行折叠为空格）
            if val_stripped in ("|", "|-", "|+", ">", ">-", ">+"):
                j = i + 1
                raw = []
                while j < len(block):
                    ln = block[j]
                    if ln == "":
                        raw.append("")
                        j += 1
                        continue
                    if _indent(ln) > base_indent:
                        raw.append(ln)
                        j += 1
                    else:
                        break
                content = _dedent_block(raw)
                if val_stripped in (">", ">-", ">+"):
                    # 折叠标量：连续非空行用空格连接，空行保留为换行
                    folded = []
                    para = []
                    for ln in content.splitlines():
                        if ln.strip() == "":
                            if para:
                                folded.append(" ".join(para))
                                para = []
                            folded.append("")
                        else:
                            para.append(ln.strip())
                    if para:
                        folded.append(" ".join(para))
                    content = "\n".join(folded)
                    # 去掉尾部多余空行，保留单个换行
                    content = content.rstrip("\n") + "\n"
                else:
                    if val_stripped in ("|", "|+"):
                        content += "\n"
                result[key] = content
                i = j
            elif val_stripped == "":
                j = i + 1
                sub = []
                while j < len(block) and (not block[j].strip() or _indent(block[j]) > base_indent):
                    sub.append(block[j])
                    j += 1
                result[key] = parse_block(sub, base_indent + 2) if sub else None
                i = j
            else:
                result[key] = _parse_scalar(val)
                i += 1
        return result

    return parse_block(lines, 0), body


# ---------------------------------------------------------------------------
# 2. 模板提取：从现有 HTML 页面抽取可复用的固定骨架
# ---------------------------------------------------------------------------
def extract_template(html_text: str):
    """从现有页面抽取固定骨架片段。缺失项返回 None。"""
    tpl = {}

    m = re.search(r"(<!-- Clarity tracking code -->.*?</script>)\s*", html_text, re.S)
    if m:
        tpl["clarity"] = m.group(1)

    m = re.search(r'(<script async src="https://www\.googletagmanager\.com/gtag/js[^>]*></script>.*?</script>)', html_text, re.S)
    if m:
        tpl["ga4"] = m.group(1)

    m = re.search(r"<style>(.*?)</style>", html_text, re.S)
    if m:
        tpl["style"] = "<style>" + m.group(1) + "</style>"

    m = re.search(r"<footer>.*?</footer>", html_text, re.S)
    if m:
        tpl["footer"] = m.group(0)

    m = re.search(r"<script>\s*\(function\(\)\{\s*var bp = document\.createElement.*?</script>", html_text, re.S)
    if m:
        tpl["baidu"] = m.group(0)

    return tpl


# ---------------------------------------------------------------------------
# 3. Markdown 渲染（支持 ::highlight / ::formula / ::cta 自定义块）
# ---------------------------------------------------------------------------
_BLOCK_RE = re.compile(r"^:::(highlight|info|warn|formula|cta|raw)(?:[ \t]+(.*?))?[ \t]*$", re.M)


def render_markdown(body: str) -> str:
    md = markdown.Markdown(extensions=["extra", "tables", "sane_lists", "md_in_html"])

    def convert_plain(chunk: str) -> str:
        md.reset()
        return md.convert(chunk.strip("\n"))

    out = []
    pos = 0
    for m in _BLOCK_RE.finditer(body):
        out.append(convert_plain(body[pos:m.start()]))
        kind = m.group(1)
        head = m.group(2) or ""
        # 找到对应的结束 :::
        end = body.find("\n:::", m.end())
        if end == -1:
            raise ValueError(f"自定义块 :::{kind} 未闭合")
        inner = body[m.end():end].strip("\n")
        out.append(render_block(kind, head, inner))
        pos = end + 4
    out.append(convert_plain(body[pos:]))
    return "\n".join(s for s in out if s.strip())


def render_block(kind: str, head: str, inner: str) -> str:
    md = markdown.Markdown(extensions=["extra", "tables", "sane_lists", "md_in_html"])

    if kind == "raw":
        # 内容为原样 HTML（不做 Markdown 处理）
        return inner

    if kind == "cta":
        title, _, desc = head.partition("|")
        return (
            '<div class="cta-section">\n'
            f"<h3>{html.escape(title.strip())}</h3>\n"
            f"{_render_inner(inner, md)}\n"
            "</div>"
        )

    box_cls = {"highlight": "highlight-box", "info": "info-box",
               "warn": "warn-box", "formula": "formula-box"}[kind]
    h4 = html.escape(head)
    return (
        f'<div class="{box_cls}">\n'
        f"<h4>{h4}</h4>\n"
        f"{_render_inner(inner, md)}\n"
        "</div>"
    )


def _render_inner(inner: str, md) -> str:
    """渲染 box 内部：``` 代码块 → <pre>，其余走 Markdown。"""
    parts = []
    pos = 0
    for m in re.finditer(r"```[^\n]*\n(.*?)```", inner, re.S):
        pre_md = inner[pos:m.start()]
        if pre_md.strip():
            md.reset()
            parts.append(md.convert(pre_md.strip("\n")).strip())
        code = m.group(1)
        # 去掉代码块常见的前导缩进
        parts.append("<pre>" + html.escape(code.rstrip("\n")) + "</pre>")
        pos = m.end()
    tail = inner[pos:]
    if tail.strip():
        md.reset()
        parts.append(md.convert(tail.strip("\n")).strip())
    return "\n".join(p for p in parts if p.strip())


# ---------------------------------------------------------------------------
# 4. 整页组装
# ---------------------------------------------------------------------------
def build_page(meta: dict, body: str, tpl: dict) -> str:
    title = meta["title"] + (meta.get("title_suffix") or "")
    schema = json.dumps(meta.get("schema", {}), ensure_ascii=False, indent=2)
    ts = meta.get("tags") or []
    tags_html = "\n                ".join(
        f'<span class="tag">{html.escape(t)}</span>' for t in ts
    )
    bc = meta.get("breadcrumb") or []
    crumb_parts = []
    for i, c in enumerate(bc):
        if c.get("href") and i < len(bc) - 1:
            crumb_parts.append(f'<a href="{c["href"]}">{html.escape(c["label"])}</a>')
        else:
            crumb_parts.append(html.escape(c["label"]))
    crumb_html = " > ".join(crumb_parts)
    footer_inner = "\n        ".join(
        f"<p>{html.escape(line)}</p>" for line in (meta.get("footer_lines") or [])
    )
    content = render_markdown(body)

    return f"""<!DOCTYPE html>
<html lang="{meta.get('lang', 'zh-CN')}">
<head>
{tpl.get('clarity', '')}
{tpl.get('ga4', '')}
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <meta name="description" content="{html.escape(meta.get('description', ''))}">
    <meta name="keywords" content="{html.escape(meta.get('keywords', ''))}">
    <link rel="canonical" href="{meta.get('canonical', '')}">
    {tpl.get('style', '')}
<script type="application/ld+json">
{schema}
</script>
</head>
<body>
    <header>
        <h1>{html.escape(meta.get('header_title', ''))}</h1>
        <p>{html.escape(meta.get('header_subtitle', ''))}</p>
    </header>

    <div class="container">
        <div class="breadcrumb">
            {crumb_html}
        </div>

        <article>
            <div class="meta-info">
                {tags_html}
                <span style="color: #a0aec0;">发布时间：{meta.get('date', '')}</span>
            </div>

{content}
        </article>
    </div>

    <footer>
        {footer_inner}
    </footer>
{tpl.get('baidu', '')}
</body>
</html>
"""


# ---------------------------------------------------------------------------
# 5. 入口
# ---------------------------------------------------------------------------
def build_page_shell(meta: dict, body: str) -> str:
    """外壳模式：shell_head / meta_info / shell_tail 原样取自原页面，
    仅正文 body 经过 Markdown 渲染。用于 PILOT 家族逐篇迁移。"""
    for k in ("shell_head", "meta_info", "shell_tail"):
        if k not in meta or meta[k] is None:
            raise ValueError(f"外壳模式缺少 front matter 字段：{k}")
    content = render_markdown(body)
    return meta["shell_head"] + meta["meta_info"] + content + meta["shell_tail"]


def main():
    ap = argparse.ArgumentParser(description="Build HTML pages from Markdown content")
    ap.add_argument("--content", default=str(ROOT / "content" / "articles"))
    ap.add_argument("--out", default=str(ROOT / "build"))
    ap.add_argument("--template", default=str(ROOT / "article_hvw_braking.html"),
                    help="模板模式下用于提取固定骨架的现有页面")
    args = ap.parse_args()

    content_dir = Path(args.content)
    out_dir = Path(args.out)
    tpl_path = Path(args.template)

    # 模板模式仍保留（兼容试点），但外壳模式不依赖它
    tpl = {}
    if tpl_path.exists():
        tpl = extract_template(tpl_path.read_text(encoding="utf-8"))

    out_dir.mkdir(parents=True, exist_ok=True)
    md_files = sorted(content_dir.glob("*.md"))
    if not md_files:
        raise SystemExit(f"未找到 Markdown 源文件：{content_dir}")

    for md_path in md_files:
        text = md_path.read_text(encoding="utf-8")
        meta, body = parse_front_matter(text)
        slug = meta.get("filename_slug") or md_path.stem
        out_name = slug if slug.endswith(".html") else f"{slug}.html"

        if "shell_head" in meta:
            page = build_page_shell(meta, body)
            mode = "shell"
        else:
            missing = [k for k in ("clarity", "ga4", "style", "footer", "baidu") if k not in tpl]
            if missing:
                raise SystemExit(f"{md_path.name}: 模板模式缺少模板片段 {missing}")
            page = build_page(meta, body, tpl)
            mode = "template"

        target = out_dir / out_name
        target.write_text(page, encoding="utf-8", newline="")
        print(f"[build:{mode}] {md_path.name} -> {target}  ({len(page)} bytes)")

    print(f"\n完成：输出目录 {out_dir}（未改动任何现有 HTML）")


if __name__ == "__main__":
    main()

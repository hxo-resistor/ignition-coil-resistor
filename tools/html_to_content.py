#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/html_to_content.py — 阶段2 迁移工具

把 PILOT 家族页面（<header>/<breadcrumb>/<article>/<footer> 结构）
转换为 content/articles/<slug>.md：

  * shell_head : <!DOCTYPE> ... 直到 <article> 结束（含 <article>）—— 原样保留
  * meta_info  : <article> 内的 <div class="meta-info">...</div> —— 原样保留
  * shell_tail : </article> ... 直到 </html> —— 原样保留
  * body       : <article> 内、meta-info 之后的正文 → Markdown

正文用 stdlib html.parser 解析成轻量树，再序列化为 Markdown：
  h2/h3/h4 -> ##/###/#### ; p -> 段落 ; ul/ol/li -> 列表 ;
  table -> GitHub 表格 ; pre -> ``` 代码块 ;
  div.highlight-box/info-box/warn-box/formula-box/cta-section -> :::xxx 块 ;
  其余无法安全转换的内联 HTML 原样保留。

用法：
  python tools/html_to_content.py article_discharge_calculation
  python tools/html_to_content.py --all-pilot
"""

import argparse
import html as html_mod
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent

VOID = {"br", "img", "hr", "input", "meta", "link", "source"}


# ---------------------------------------------------------------------------
# 轻量 DOM
# ---------------------------------------------------------------------------
class Node:
    __slots__ = ("tag", "attrs", "children", "text", "is_text")

    def __init__(self, tag=None, attrs=None, text=None):
        self.tag = tag
        self.attrs = attrs or {}
        self.children = []
        self.text = text
        self.is_text = text is not None

    def get(self, key, default=None):
        return self.attrs.get(key, default)


class TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.root = Node("root")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, dict(attrs)))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(Node(text=data))

    def handle_entityref(self, name):
        self.stack[-1].children.append(Node(text=html_mod.unescape("&" + name + ";")))

    def handle_charref(self, name):
        self.stack[-1].children.append(Node(text=html_mod.unescape("&#" + name + ";")))


def parse_fragment(fragment: str) -> Node:
    tb = TreeBuilder()
    tb.feed(fragment)
    tb.close()
    return tb.root


def text_of(node: Node) -> str:
    if node.is_text:
        return node.text
    return "".join(text_of(c) for c in node.children)


def collapse(s: str) -> str:
    return re.sub(r"[ \t\r\n]+", " ", s).strip()


# ---------------------------------------------------------------------------
# 行内序列化
# ---------------------------------------------------------------------------
def inline(node: Node) -> str:
    if node.is_text:
        return node.text
    tag = node.tag
    inner = "".join(inline(c) for c in node.children)
    if tag in ("strong", "b"):
        return f"**{inner.strip()}**"
    if tag in ("em", "i"):
        return f"*{inner.strip()}*"
    if tag == "br":
        return "<br>"
    if tag == "a":
        href = node.get("href", "")
        cls = node.get("class")
        if cls:
            return f'<a href="{href}" class="{cls}">{inner}</a>'
        return f"[{inner}]({href})"
    if tag == "code":
        return f"`{inner}`"
    if tag == "span":
        style = node.get("style")
        if style:
            return f'<span style="{style}">{inner}</span>'
        return inner
    # 其它内联标签原样保留
    return f"<{tag}>{inner}</{tag}>"


def inline_children(node: Node) -> str:
    return "".join(inline(c) for c in node.children)


# ---------------------------------------------------------------------------
# 块级序列化
# ---------------------------------------------------------------------------
BOX_CLASSES = {
    "highlight-box": "highlight",
    "info-box": "info",
    "warn-box": "warn",
    "formula-box": "formula",
    "cta-section": "cta",
}


def block(node: Node) -> str:
    if node.is_text:
        t = node.text.strip()
        return t
    tag = node.tag
    # 带属性的块级元素（含子孙属性）：原样保留以保证 1:1
    if has_attrs(node):
        return _raw_block(node)
    if tag in ("h2", "h3", "h4"):
        level = {"h2": "##", "h3": "###", "h4": "####"}[tag]
        return f"{level} {inline_children(node).strip()}"
    if tag == "p":
        return inline_children(node).strip()
    if tag == "ul":
        return render_list(node, ordered=False)
    if tag == "ol":
        return render_list(node, ordered=True)
    if tag == "table":
        return render_table(node)
    if tag == "pre":
        if node.attrs:
            # 带属性（如 style）的 pre：原样保留，避免丢失属性
            return ":::raw\n" + raw_html(node) + "\n:::"
        code = text_of(node)
        return "```\n" + code.strip("\n") + "\n```"
    if tag == "blockquote":
        inner = "\n".join(block(c) for c in node.children if block(c).strip())
        return "\n".join("> " + l for l in inner.splitlines())
    if tag == "div":
        cls = node.get("class", "").split()
        for c in cls:
            if c in BOX_CLASSES:
                return render_box(BOX_CLASSES[c], node)
        # 未知 div：原样保留
        return ":::raw\n" + raw_html(node) + "\n:::"
    if tag == "header":
        return ":::raw\n" + raw_html(node) + "\n:::"
    return ":::raw\n" + raw_html(node) + "\n:::"


def render_list(node: Node, ordered: bool) -> str:
    lines = []
    n = 0
    for li in node.children:
        if li.is_text or li.tag != "li":
            continue
        n += 1
        marker = f"{n}. " if ordered else "- "
        # 分离嵌套列表
        top, nested = [], []
        for c in li.children:
            if not c.is_text and c.tag in ("ul", "ol"):
                nested.append(c)
            else:
                top.append(c)
        text = "".join(inline(c) for c in top).strip()
        lines.append(marker + text)
        for sub in nested:
            sub_md = render_list(sub, ordered=(sub.tag == "ol"))
            for l in sub_md.splitlines():
                lines.append("    " + l)
    return "\n".join(lines)


def _iter_rows(node: Node):
    """递归收集 tr（兼容 thead/tbody 包裹）。"""
    for c in node.children:
        if c.is_text:
            continue
        if c.tag == "tr":
            yield c
        elif c.tag in ("thead", "tbody", "tfoot"):
            yield from _iter_rows(c)


def render_table(node: Node) -> str:
    rows = []
    for tr in _iter_rows(node):
        cells, is_header = [], False
        for cell in tr.children:
            if cell.is_text or cell.tag not in ("th", "td"):
                continue
            if cell.tag == "th":
                is_header = True
            cells.append(collapse(inline_children(cell)).replace("|", "\\|"))
        rows.append((cells, is_header))
    if not rows:
        return _raw_block(node)
    # 没有表头的表格无法用 Markdown 精确表达（会被补空表头），原样保留
    if not any(h for _, h in rows):
        return _raw_block(node)
    out = []
    header_done = False
    for cells, is_header in rows:
        out.append("| " + " | ".join(cells) + " |")
        if is_header and not header_done:
            out.append("| " + " | ".join("---" for _ in cells) + " |")
            header_done = True
    return "\n".join(out)


INLINE_SAFE = {"strong", "b", "em", "i", "a", "code", "br", "span"}


def has_attrs(node: Node) -> bool:
    """节点或其子孙是否带需要保真的结构属性。
    行内标签（strong/a/br 等）默认可安全转换，不算属性冲突；
    但带 class/style 的 span/a 仍视为需要保真。"""
    if node.is_text:
        return False
    if node.tag in INLINE_SAFE:
        # a 只有 href 时可转换；span 只有 style 时才需保留
        if node.tag in ("a",) and set(node.attrs) <= {"href"}:
            return any(has_attrs(c) for c in node.children)
        if node.tag in ("span",) and not node.attrs:
            return any(has_attrs(c) for c in node.children)
        return bool(node.attrs)
    if node.attrs:
        return True
    return any(has_attrs(c) for c in node.children)


def _raw_block(node: Node) -> str:
    return ":::raw\n" + raw_html(node) + "\n:::"


def render_box(kind: str, node: Node) -> str:
    # 含属性（style/class 等）的 box：整块原样保留，避免嵌套自定义块与属性丢失
    if has_attrs(node):
        return _raw_block(node)
    # h3/h4 作为标题
    head = ""
    rest = []
    for c in node.children:
        if not c.is_text and c.tag in ("h3", "h4") and not head:
            head = collapse(inline_children(c))
        else:
            rest.append(c)
    inner_md = "\n\n".join(block(c) for c in rest if block(c).strip())
    return f":::{kind} {head}\n{inner_md.strip()}\n:::"


def raw_html(node: Node) -> str:
    if node.is_text:
        return html_mod.escape(node.text, quote=False)
    attrs = ""
    for k, v in node.attrs.items():
        if v is None:
            attrs += f" {k}"
        else:
            attrs += f' {k}="{v}"'
    if node.tag in VOID:
        return f"<{node.tag}{attrs}>"
    inner = "".join(raw_html(c) for c in node.children)
    return f"<{node.tag}{attrs}>{inner}</{node.tag}>"


# ---------------------------------------------------------------------------
# 页面切分 + 元数据
# ---------------------------------------------------------------------------
def split_page_legacy(text: str):
    """LEGACY-header 版式：外壳头 = 至 <div class="header"> 结束；
    正文 = header 之后到第一个 <div class="cta">（或 footer）之前；
    外壳尾 = 从 .cta/.footer 起到文件结束。"""
    hm = re.search(r'<div class="header">', text)
    if not hm:
        raise ValueError('未找到 <div class="header">')
    head_end = _match_div_close(text, hm.start())
    cta = re.search(r'<div class="cta"', text[head_end:])
    ftr = re.search(r'<div class="footer"', text[head_end:])
    cands = []
    if cta:
        cands.append(head_end + cta.start())
    if ftr:
        cands.append(head_end + ftr.start())
    tail_start = min(cands) if cands else len(text)
    return text[:head_end], "", text[head_end:tail_start], text[tail_start:]


def split_page(text: str):
    a_open = text.index("<article>") + len("<article>")
    a_close = text.rindex("</article>")
    mi_open = text.index('<div class="meta-info">', a_open)
    mi_close = text.index("</div>", mi_open) + len("</div>")
    return text[:a_open], text[mi_open:mi_close], text[mi_close:a_close], text[a_close:]


def _match_div_close(text: str, open_start: int) -> int:
    """给定 <div ...> 的起始位置，返回其匹配的 </div> 结束位置（不含空格）。"""
    tag_re = re.compile(r"<(/?)div\b[^>]*>", re.I)
    depth = 0
    for m in tag_re.finditer(text, open_start):
        if m.group(1) == "/":
            depth -= 1
            if depth == 0:
                return m.end()
        else:
            depth += 1
    raise ValueError("未能匹配 container 的 </div>")


def split_page_nav(text: str):
    """NAV 版式：外壳 = 至 <div class="container"> 结束；
    正文 = container 内部（含 TOC）；外壳尾 = container 的 </div> 之后。"""
    m = re.search(r'<div class="container">', text)
    if not m:
        raise ValueError("未找到 <div class=\"container\">")
    head_end = m.end()
    close_end = _match_div_close(text, m.start())
    # close_end 指向 </div> 之后；找 </div> 起始
    close_start = text.rfind("</div>", m.start(), close_end)
    return text[:head_end], "", text[head_end:close_start], text[close_start:]


def body_to_markdown(body_html: str) -> str:
    root = parse_fragment(body_html)
    parts = [block(c) for c in root.children]
    return "\n\n".join(p.strip("\n") for p in parts if p and p.strip())


def yaml_scalar(v: str) -> str:
    if v == "":
        return '""'
    if re.search(r'[:#\[\]{}"\'&*!|>%@`,]', v) or v != v.strip():
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return v


def block_scalar(v: str) -> str:
    if v == "":
        return ""
    lines = v.split("\n")
    out = []
    for i, ln in enumerate(lines):
        if ln == "":
            out.append("")
        else:
            out.append("  " + ln)
    return "\n".join(out)


def convert(slug: str, src_path: Path, out_dir: Path, layout: str = "auto"):
    text = src_path.read_text(encoding="utf-8")
    if layout == "auto":
        if 'class="nav-inner"' in text and '<article>' not in text:
            layout = "nav"
        elif '<div class="content">' in text or '<div class="header">' in text and '<article>' not in text:
            layout = "legacy"
        else:
            layout = "pilot"
    if layout == "nav":
        shell_head, meta_info, body_html, shell_tail = split_page_nav(text)
    elif layout == "legacy":
        shell_head, meta_info, body_html, shell_tail = split_page_legacy(text)
    else:
        shell_head, meta_info, body_html, shell_tail = split_page(text)

    title = re.search(r"<title>(.*?)</title>", text, re.S)
    desc = re.search(r'<meta name="description" content="(.*?)">', text, re.S)
    kw = re.search(r'<meta name="keywords" content="(.*?)">', text, re.S)
    canon = re.search(r'rel="canonical" href="(.*?)"', text, re.S)
    tags = re.findall(r'<span class="tag">(.*?)</span>', meta_info, re.S)
    date_m = re.search(r"发布时间：([\d-]+)", meta_info)
    if not date_m:
        date_m = re.search(r"(\d{4}-\d{2}-\d{2})", meta_info)

    body_md = body_to_markdown(body_html)

    fm = ["---", f"filename_slug: {slug}"]
    if title:
        fm.append(f"title: {yaml_scalar(html_mod.unescape(title.group(1)))}")
    if date_m:
        fm.append(f"date: {date_m.group(1)}")
    if desc:
        fm.append(f"description: {yaml_scalar(html_mod.unescape(desc.group(1)))}")
    if kw:
        fm.append(f"keywords: {yaml_scalar(html_mod.unescape(kw.group(1)))}")
    if canon:
        fm.append(f"canonical: {canon.group(1)}")
    if tags:
        fm.append("tags:")
        for t in tags:
            fm.append(f"  - {yaml_scalar(collapse(t))}")
    fm.append("# 外壳：原页面固定结构，逐字保留（阶段2：不改变外观/埋点/Schema）")
    fm.append(f"layout: {layout}")
    fm.append("shell_head: |")
    fm.append(block_scalar(shell_head))
    if meta_info:
        fm.append("meta_info: |")
        fm.append(block_scalar(meta_info))
    else:
        fm.append('meta_info: ""')
    fm.append("shell_tail: |")
    fm.append(block_scalar(shell_tail))
    fm.append("---")
    fm.append("")

    out = "\n".join(fm) + "\n" + body_md.strip("\n") + "\n"
    out_path = out_dir / f"{slug}.md"
    out_path.write_text(out, encoding="utf-8", newline="")
    print(f"[convert:{layout}] {src_path.name} -> {out_path}")
    return out_path


PILOT = [
    "article_hvw_braking",
    "article_discharge_calculation",
    "article_ev_pile_bleeder",
    "article_ig_c_vs_ig_f",
    "article_ig_f_engineering",
    "article_ig_s_patent",
    "article_otp_vs_fuse",
    "article_rxf_charger",
    "article_tcr_wirewound",
]

NAV = [
    "article_4k7_vs_10k",
    "article_burn_causes",
    "article_charger_melt",
    "article_emi_suppression",
    "article_import_substitution_qa",
    "article_installation_guide",
    "article_moto_ignition",
    "article_multimeter_test",
    "article_price_difference",
    "article_vishay_vs_hxo",
    "article_wirewound_vs_thickfilm",
    "article_xray_bleeder_resistor",
]


LEGACY = [
    "article_aeq200_certification",
    "article_bleeder_resistor",
    "article_custom_resistor",
    "article_hvw_resistor",
    "article_ig_c_ceramic",
    "article_ig_f",
    "article_ig_s",
    "article_ignition_history",
    "article_iso7637_transient",
    "article_otp_fuse_resistor",
    "article_otp_selection_derating",
    "article_rxf_charger_protection",
    "article_rxf_fuse",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--all-pilot", action="store_true")
    ap.add_argument("--all-nav", action="store_true")
    ap.add_argument("--all-legacy", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "content" / "articles"))
    args = ap.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.all_pilot:
        slugs, layout = PILOT, "pilot"
    elif args.all_nav:
        slugs, layout = NAV, "nav"
    elif args.all_legacy:
        slugs, layout = LEGACY, "legacy"
    else:
        slugs, layout = args.slugs, "auto"
    if not slugs:
        raise SystemExit("请指定 slug 或使用 --all-pilot / --all-nav")
    for slug in slugs:
        src = ROOT / f"{slug}.html"
        if not src.exists():
            raise SystemExit(f"源文件不存在：{src}")
        convert(slug, src, out_dir, layout=layout)


if __name__ == "__main__":
    main()

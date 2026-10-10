"""Parse HXO content/articles/*.md into (title, plain_text_body) for Zhihu.

The .md files are YAML frontmatter whose `shell_head` key holds the full HTML
page shell, followed by the real article body. The body mixes markdown with
`:::raw ... :::` blocks that hold raw HTML (tables, callout boxes, headings).

This module extracts a Zhihu-friendly plain-text rendering.
"""
import re
from pathlib import Path

ARTICLES_DIR = Path(__file__).resolve().parent.parent / "content" / "articles"


def _split_frontmatter(text):
    """Return (frontmatter, body). Frontmatter is between the first two lines
    equal to '---'."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1:])
    return "", text


def _frontmatter_value(fm, key):
    m = re.search(rf"^{re.escape(key)}:\s*(.+)$", fm, re.MULTILINE)
    if not m:
        return ""
    return m.group(1).strip().strip('"').strip("'")


def _html_to_text(html):
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
    html = re.sub(r"</(p|div|li|tr|h[1-6]|ul|ol|table)>", "\n", html, flags=re.I)
    html = re.sub(r"<li[^>]*>", "- ", html, flags=re.I)
    html = re.sub(r"<h([1-6])[^>]*>", lambda m: "\n" + "#" * int(m.group(1)) + " ", html, flags=re.I)
    html = re.sub(r"</t[dh]>", " | ", html, flags=re.I)
    html = re.sub(r"<[^>]+>", "", html)
    html = (html.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"'))
    html = html.replace("✅", "[有]").replace("—", "-")
    return html


def _md_to_text(md):
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", md)
    md = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", md)
    md = re.sub(r"\*\*([^*]+)\*\*", r"\1", md)
    md = re.sub(r"`([^`]+)`", r"\1", md)
    return md


def _clean_body(body):
    out = []

    def repl(m):
        return "\n" + _html_to_text(m.group(1)) + "\n"

    body = re.sub(r":::\s*raw\s*\n(.*?)\n:::", repl, body, flags=re.DOTALL)
    body = _md_to_text(body)
    for line in body.splitlines():
        line = line.strip()
        if not line or line == "---":
            continue
        out.append(line)
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


_BRAND_SUFFIX = re.compile(
    r"\s*[|—\-]\s*HXO[\w\u4e00-\u9fff ]*(Resistor|华星欧电子|点火线圈|技术博客)?\s*$"
)


def strip_brand(title):
    """Remove the website SEO brand suffix from a title for Zhihu display."""
    cleaned = _BRAND_SUFFIX.sub("", title).strip()
    return cleaned or title


def parse_article(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    fm, body = _split_frontmatter(text)
    title = _frontmatter_value(fm, "title")
    if not title:
        title = path.stem
    return {
        "slug": path.stem,
        "title": title,
        "zhihu_title": strip_brand(title),
        "body": _clean_body(body),
    }


def list_articles():
    return sorted(ARTICLES_DIR.glob("article_*.md"))


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    arts = list_articles()
    print(f"found {len(arts)} articles")
    for p in arts[:1]:
        a = parse_article(p)
        print("TITLE:", a["title"])
        print("BODY (first 400):")
        print(a["body"][:400])

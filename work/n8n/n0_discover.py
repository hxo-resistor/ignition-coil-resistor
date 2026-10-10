"""N0: Discover new (unpublished) articles under content/articles/.

Compares *.md files against work/published_manifest.json. Emits the list of
articles not yet recorded as published.

Output: {"ok": true, "action": "discover", "new": [{slug, md, title}]}
"""
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from _common import ARTICLES, emit, load_manifest, article_title  # noqa: E402


def main():
    manifest = load_manifest()
    published = {p.get("slug") for p in manifest.get("published", [])}
    new = []
    for md in sorted(ARTICLES.glob("article_*.md")):
        slug = md.stem
        if slug in published:
            continue
        new.append({"slug": slug, "md": md.name, "title": article_title(md)})
    emit({"ok": True, "action": "discover", "count": len(new), "new": new})


if __name__ == "__main__":
    main()

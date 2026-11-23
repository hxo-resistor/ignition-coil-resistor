#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""brainstorm.py — 内容自进化：LLM 挖掘热点痛点，自动生成新选题入库。

流程：
    1. 收集已有选题标题（去重参照）。
    2. 让 DeepSeek 生成 N 个新选题的完整规格（JSON）。
    3. 校验字段、分配新编号（21+），写入 work/generated_topics.json（content_factory 自动加载）。
    4. 同步追加到 work/topic_pool.md（状态「待写」）。

可选联网搜索：设置 HXO_TAVILY_API_KEY 后把实时热点注入提示词；未配置则用 LLM 知识模拟「近期热点」。
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import content_factory  # noqa: E402
import translate  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent.parent
WORK = REPO / "work"
GEN = WORK / "generated_topics.json"
POOL = WORK / "topic_pool.md"

CTYPES = ("selection", "compare", "certification", "pain")
CERT_POOL = ("AEC-Q200", "CQC", "UL", "RoHS/REACH", "CISPR 25", "IEC 62477", "MIL-STD")

SYSTEM = (
    "You are a senior B2B power-resistor marketing strategist at HXO Resistor (华星欧电子), "
    "a manufacturer of ignition-coil suppression resistors and power resistors. "
    "Products: IG-C (ceramic-core wirewound ignition suppression resistor), IG-F (glass-fiber anti-vibration), "
    "IG-S (solid-ceramic non-inductive), RXF (thermal-fuse resistor), HVW (high-voltage wirewound). "
    "You mine real hot pain points that design engineers / buyers / OEM decision-makers search for recently. "
    "Output ONLY a JSON array, no markdown fences, no explanation."
)


def _load_gen():
    if not GEN.exists():
        return []
    try:
        data = json.loads(GEN.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _existing_titles():
    titles = [t.get("title", "") for t in content_factory.TOPICS if t.get("title")]
    titles += [t.get("title", "") for t in _load_gen() if t.get("title")]
    return titles


def _existing_slugs():
    slugs = {t["slug"] for t in content_factory.TOPICS if t.get("slug")}
    slugs |= {t["slug"] for t in _load_gen() if t.get("slug")}
    return slugs


def _next_num():
    nums = [int(t["num"]) for t in content_factory.TOPICS if str(t.get("num", "")).isdigit()]
    nums += [int(t["num"]) for t in _load_gen() if str(t.get("num", "")).isdigit()]
    return max(nums) + 1 if nums else 21


def _search_hot(seed):
    """可选联网搜索（Tavily）。未配置 key 则返回空串，交给 LLM 知识模拟热点。"""
    key = os.environ.get("HXO_TAVILY_API_KEY", "").strip()
    if not key:
        return ""
    try:
        import requests
        r = requests.post("https://api.tavily.com/search",
                          json={"api_key": key, "query": seed, "max_results": 5},
                          timeout=30)
        r.raise_for_status()
        results = r.json().get("results", [])
        return "\n".join(f"- {x.get('title', '')}: {x.get('content', '')[:200]}"
                         for x in results[:5])
    except Exception as e:
        print(f"[brainstorm] 联网搜索失败（回退到 LLM 知识模拟）：{e}", file=sys.stderr)
        return ""


def _prompt(seed, existing, n, hot):
    p = (
        f"Generate {n} NEW content topic specs (选题) about recently hot pain points, seeded by: 「{seed}」.\n"
        "Topics must be DIFFERENT from each other and from the existing list, and cover diverse product lines and angles.\n\n"
        "For each topic output a JSON object with EXACTLY these keys:\n"
        '- slug: "article_" + lowercase english snake_case (unique)\n'
        '- product: one of "IG-C / IG-F / IG-S", "IG-C", "IG-F", "IG-S", "RXF", "HVW"\n'
        "- title: Chinese question-style title (specific + hook)\n"
        "- desc: Chinese 1-2 sentence description\n"
        "- kw: Chinese keywords comma-separated\n"
        '- ctype: one of "selection", "compare", "certification", "pain"\n'
        "- pain: array of 3 Chinese pain points\n"
        "- params: array of [参数, 值, 说明] (3-5 items)\n"
        "- formula: a short Chinese formula or rule of thumb\n"
        "- scenarios: array of [场景, 痛点, 方案] (2-3 items)\n"
        "- myths: array of 3 Chinese misconceptions\n"
        "- hook: Chinese one-line hook\n"
        "- title_en: English title\n"
        "- hook_en: English one-line hook\n"
        "- points_en: array of 3 English bullet points\n"
        "- data_points: array of [指标, 数据] (3-5 items)\n"
        f"- certifications: array from {list(CERT_POOL)}\n"
        "- case: a short Chinese application case (generic scenario, no fabricated company names)\n"
        "- manufacturing: short Chinese manufacturing/QC note\n\n"
        f"Existing topics (avoid duplicating):\n" + "\n".join(f"- {t}" for t in existing) + "\n"
    )
    if hot:
        p += f"\nRecent real web results about this topic (use as grounding):\n{hot}\n"
    p += "\nOutput the JSON array only."
    return p


def _list(x):
    if isinstance(x, list):
        return [str(s).strip() for s in x if str(s).strip()]
    if isinstance(x, str) and x.strip():
        return [s.strip() for s in x.replace("\n", ",").split(",") if s.strip()]
    return []


def _table(x):
    out = []
    if isinstance(x, list):
        for row in x:
            if isinstance(row, list):
                out.append([str(c) for c in row])
    return out


def _fill(spec, num, slugs):
    title = (spec.get("title") or "").strip()
    if not title:
        return None
    slug = (spec.get("slug") or "").strip()
    if not slug.startswith("article_"):
        slug = "article_" + re.sub(r"[^a-z0-9_]+", "_", slug.lower()).strip("_")
    if not slug or slug == "article_":
        return None
    base = slug
    i = 2
    while slug in slugs:
        slug = f"{base}_{i}"
        i += 1
    ctype = spec.get("ctype") if spec.get("ctype") in CTYPES else "selection"
    pain = _list(spec.get("pain"))
    if len(pain) < 3:
        pain = (pain + ["选型依据不足", "缺乏实测数据", "工况差异被忽略"])[:3]
    params = _table(spec.get("params")) or [["关键参数", "典型值", "说明"]]
    scenarios = _table(spec.get("scenarios")) or [["典型场景", "核心痛点", "推荐方案"]]
    myths = _list(spec.get("myths")) or ["盲目按经验选型", "忽略工况差异", "只看价格不看寿命"]
    certs = [c for c in _list(spec.get("certifications")) if c in CERT_POOL]
    return {
        "num": str(num), "slug": slug, "product": spec.get("product") or "IG-C / IG-F / IG-S",
        "title": title, "desc": spec.get("desc") or "", "kw": spec.get("kw") or "",
        "ctype": ctype,
        "title_en": spec.get("title_en") or "", "hook": spec.get("hook") or "",
        "hook_en": spec.get("hook_en") or "",
        "pain": pain, "params": params, "formula": spec.get("formula") or "",
        "scenarios": scenarios, "myths": myths,
        "tags_cn": _list(spec.get("tags_cn")) or ["点火电阻", "选型"],
        "tags_en": _list(spec.get("tags_en")) or ["#Resistor", "#PowerElectronics"],
        "points_en": _list(spec.get("points_en")),
        "data_points": _table(spec.get("data_points")),
        "certifications": certs, "case": spec.get("case") or "",
        "manufacturing": spec.get("manufacturing") or "", "source": "llm",
    }


def _parse_json(out):
    out = out.strip()
    m = re.search(r"\[.*\]", out, re.S)
    if m:
        out = m.group(0)
    return json.loads(out)


def generate(seed, n=5):
    if not translate.is_configured():
        print("未配置 DEEPSEEK_API_KEY，无法自进化选题。", file=sys.stderr)
        return []
    existing = _existing_titles()
    hot = _search_hot(seed)
    prompt = _prompt(seed, existing, n, hot)
    try:
        out = translate.chat(SYSTEM, prompt, temperature=0.7)
        data = _parse_json(out)
    except Exception as e:
        print(f"[brainstorm] LLM 生成失败：{e}", file=sys.stderr)
        return []
    if not isinstance(data, list):
        print("[brainstorm] 返回格式异常（期望 JSON 数组）。", file=sys.stderr)
        return []
    slugs = _existing_slugs()
    specs, num = [], _next_num()
    for spec in data:
        if not isinstance(spec, dict):
            continue
        filled = _fill(spec, num, slugs)
        if filled:
            specs.append(filled)
            slugs.add(filled["slug"])
            num += 1
    return specs


def _append_pool(specs):
    if not POOL.exists():
        return
    lines = POOL.read_text(encoding="utf-8").splitlines()
    for s in specs:
        platforms = "官网+知乎+Buffer" if s.get("ctype") in ("compare", "pain", "selection") else "官网+知乎"
        lines.append(f"| {s['num']} | {s['title']} | P1 | {s['product']} | {platforms} | 待写 |")
    POOL.write_text("\n".join(lines) + "\n", encoding="utf-8")


def save(specs):
    if not specs:
        return specs
    all_gen = _load_gen()
    all_gen.extend(specs)
    GEN.parent.mkdir(parents=True, exist_ok=True)
    GEN.write_text(json.dumps(all_gen, ensure_ascii=False, indent=2), encoding="utf-8")
    _append_pool(specs)
    return specs


def _last_published_title():
    slug_file = WORK / "last_published_slug.txt"
    if slug_file.exists():
        slug = slug_file.read_text(encoding="utf-8").strip()
        spec = content_factory.spec_by_slug(slug)
        if spec and spec.get("title"):
            return spec["title"]
    return "航空/军工级点火电阻（IG-S 无感陶瓷实心方案）"


def main():
    ap = argparse.ArgumentParser(description="内容自进化：LLM 挖掘热点生成新选题")
    ap.add_argument("--seed", default="", help="种子主题（默认用最近已发布主题）")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    seed = args.seed or _last_published_title()
    print(f"[brainstorm] 种子主题：{seed}")
    specs = generate(seed, args.n)
    if not specs:
        print("未生成任何新选题。")
        return 1
    if args.dry_run:
        for s in specs:
            print(f"  #{s['num']} [{s['ctype']}] {s['title']}")
        return 0
    save(specs)
    for s in specs:
        print(f"  + 新选题 #{s['num']} [{s['ctype']}] {s['title']}")
    print(f"已入库 {len(specs)} 个新选题。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

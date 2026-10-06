import sys, re, json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent

LEGACY = ["article_aeq200_certification","article_bleeder_resistor","article_custom_resistor",
 "article_hvw_resistor","article_ig_c_ceramic","article_ig_f","article_ig_s",
 "article_ignition_history","article_iso7637_transient","article_otp_fuse_resistor",
 "article_otp_selection_derating","article_rxf_charger_protection","article_rxf_fuse"]

lines = []
lines.append("# LEGACY 版式遗留问题清单（迁移前已存在，迁移时原样保留、未修复）\n")
lines.append("> 说明：以下问题均为**原文件既有问题**。本次迁移遵循「原样搬家」原则，未新增、未修复任何一项。\n")

def src_line_of_block(text, block_index):
    """返回第 N 个 ld+json 块的起始行号（指向 <script> 行）。"""
    pat = re.compile(r'<script type="application/ld\+json">')
    matches = list(pat.finditer(text))
    if block_index - 1 < len(matches):
        return text[:matches[block_index - 1].start()].count("\n") + 1
    return None


def block_content_start_line(text, block_index):
    """返回块内第一行（`{`）在源文件中的行号。"""
    m = re.search(r'<script type="application/ld\+json">', text)
    matches = list(re.finditer(r'<script type="application/ld\+json">', text))
    if block_index - 1 >= len(matches):
        return None
    seg = text[matches[block_index - 1].end():]
    # 找到该块结束
    end = seg.find("</script>")
    seg = seg[:end]
    # 块的“逻辑行0”= { 所在行
    brace = seg.find("{")
    return text[:matches[block_index - 1].end()].count("\n") + 1 + seg[:brace].count("\n")

for s in LEGACY:
    p = ROOT / (s + ".html")
    t = p.read_text(encoding="utf-8")
    issues = []
    if 'name="keywords"' not in t:
        issues.append("缺少 `<meta name=\"keywords\">`")
    if 'rel="canonical"' not in t:
        issues.append("缺少 `<link rel=\"canonical\">`")
    if 'name="description"' not in t:
        issues.append("缺少 `<meta name=\"description\">`")
    blocks = re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', t, re.S)
    for i, blk in enumerate(blocks, 1):
        try:
            json.loads(blk)
        except json.JSONDecodeError as e:
            content_start = block_content_start_line(t, i)  # blk 第 1 行对应的源文件行号
            blk_lines = blk.splitlines()
            def src_of(ln):  # blk 内第 ln 行(1-based) -> 源文件行号
                return content_start + (ln - 1) if content_start else "?"
            if e.msg.startswith("Expecting ','"):
                a = blk_lines[e.lineno - 1] if 0 < e.lineno <= len(blk_lines) else "?"
                b = blk_lines[e.lineno - 2] if e.lineno >= 2 else "?"
                issues.append(
                    f"JSON-LD 第 {i} 块语法错误：相邻对象之间缺逗号"
                    f"（源文件第 {src_of(e.lineno - 1)} 行 `{b.strip()}` 后应加逗号，"
                    f"其下第 {src_of(e.lineno)} 行是 `{a.strip()}`）")
            else:
                bad = blk_lines[e.lineno - 1] if 0 < e.lineno <= len(blk_lines) else ""
                issues.append(
                    f"JSON-LD 第 {i} 块语法错误：{e.msg}"
                    f"（源文件第 {src_of(e.lineno)} 行）：`{bad.strip()}`")
    # detect broken FAQ block (missing comma between } {)
    if re.search(r'\}\s*\n\s*\{', "\n".join(blocks)) and not issues:
        issues.append("JSON-LD 疑似相邻对象之间缺逗号（需人工确认）")
    if issues:
        lines.append(f"\n## `{s}.html`\n")
        for it in issues:
            lines.append(f"- {it}")
    else:
        lines.append(f"\n## `{s}.html`\n")
        lines.append("- 未发现 SEO / JSON-LD 结构问题")

(ROOT / "build" / "legacy_issues_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))

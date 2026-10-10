#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""daily_publish.py — 每日自动发文：选题池 → 生成文章 → 全链路发布 → 标记完成

流程：
    1. 读取 work/topic_pool.md，取第一个「待写」主题
    2. 生成 Markdown 文章（含 shell_head / meta_info / shell_tail）写入 content/articles/
    3. 构建 HTML（tools/build_from_content.py）并复制到仓库根（供 Supabase 查找）
    4. 调 tools/publish_all.py --slug <slug> 全链路发布（官网/百度/知乎/Buffer/Supabase）
    5. 发布成功后，把选题池中该主题状态改为「已完成」

用法：
    python tools/daily_publish.py               # 取第一个待写，真实发布
    python tools/daily_publish.py --dry-run     # 生成 + 构建 + dry-run 发布，不标记
    python tools/daily_publish.py --list        # 只看下一个待写主题

红线：只发 1 篇；遇错停下，不重试。
"""
import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent.parent
WORK = REPO / "work"
POOL = WORK / "topic_pool.md"
ARTICLES = REPO / "content" / "articles"
TEMPLATE = ARTICLES / "article_pv_storage_bleeder.md"   # shell 来源模板
PY = sys.executable


def log(msg):
    print(f"[{dt.datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# 选题池
# ---------------------------------------------------------------------------
def parse_pool():
    """返回 [(line_index, topic, priority, product, platforms, status)]"""
    lines = POOL.read_text(encoding="utf-8").splitlines()
    rows = []
    for idx, ln in enumerate(lines):
        if not ln.strip().startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        if cells[0] in ("#", "---") or set(cells[0]) <= set("-"):
            continue
        if cells[0].isdigit():
            rows.append({
                "line": idx,
                "num": cells[0],
                "topic": cells[1],
                "priority": cells[2],
                "product": cells[3],
                "platforms": cells[4],
                "status": cells[5],
            })
    return lines, rows


def next_topic(rows):
    for r in rows:
        if r["status"] == "待写":
            return r
    return None


def mark_done(topic):
    lines = POOL.read_text(encoding="utf-8").splitlines()
    target = f"| {topic['num']} | {topic['topic']} |"
    changed = False
    for i, ln in enumerate(lines):
        if ln.strip().startswith("|") and topic["topic"] in ln and "待写" in ln:
            lines[i] = ln.replace("待写", "已完成")
            changed = True
            break
    if changed:
        POOL.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return changed


# ---------------------------------------------------------------------------
# 主题 → slug/元数据 + 正文（按需扩展）
# ---------------------------------------------------------------------------
SLUGS = {
    "1": "article_power_rating_selection",
    "2": "article_ignition_resistor_lifespan",
    "3": "article_charger_thermal_fuse_troubleshoot",
    "4": "article_braking_resistor_burn",
    "5": "article_resistance_tolerance",
    "6": "article_oscilloscope_emi_verify",
    "7": "article_bleeder_heat_dissipation",
    "8": "article_led_driver_thermal_protection",
    "9": "article_aerospace_ignition_resistor",
    "10": "article_servo_braking_resistor_selection",
    "11": "article_insulation_voltage_test",
    "12": "article_small_engine_ignition_resistor",
    "13": "article_adapter_emi_solution",
    "14": "article_non_inductive_ignition_resistor",
    "15": "article_storage_bleeder_1500v",
    "16": "article_rohs_reach_compliance",
    "17": "article_welder_bleeder_resistor",
    "18": "article_thermal_fuse_temperatures",
    "19": "article_moto_retrofit_suppressor",
    "20": "article_custom_resistor_process",
}

# 每题的元数据与正文（正文用简明技术内容 + 表格/公式/FAQ，保证 GEO 友好）
CONTENT = {
    "1": {
        "title": "点火线圈抑制电阻额定功率怎么选？1W/3W/5W/10W 选型陷阱与实测温升",
        "desc": "点火线圈抑制电阻额定功率选型指南：从点火能量、脉冲能量、温升实测三个维度给出 1W/3W/5W/10W 的选择依据，附 IG-C/IG-F/IG-S 系列功率对照与常见选型误区。",
        "kw": "点火线圈抑制电阻功率,抑制电阻选型,IG-C功率,点火电阻额定功率,电阻温升",
    },
    "2": {
        "title": "摩托车点火线圈抑制电阻多久换一次？寿命估算与更换判断标准",
        "desc": "摩托车点火线圈抑制电阻的寿命估算方法：基于 Arrhenius 模型的温度寿命、振动失效、阻值漂移判断，附万用表快速检测步骤与更换标准。",
        "kw": "点火线圈抑制电阻寿命,抑制电阻多久换,摩托车点火电阻,电阻更换标准",
    },
    "3": {
        "title": "充电器空载发热、待机功耗异常？RXF 温度保险电阻排查指南",
        "desc": "充电器空载发热与待机功耗异常的排查指南：从 RXF 温度保险电阻的 221℃ 动作温度、保持温度、阻值漂移三方面定位故障，附万用表检测与替换建议。",
        "kw": "充电器发热,RXF温度保险电阻,待机功耗异常,过温保护,充电器保护电阻",
    },
    "4": {
        "title": "变频器制动电阻为什么老是烧？5 种根因与 HVW 选型对策",
        "desc": "变频器制动电阻反复烧毁的 5 种根因分析：功率裕量不足、占空比估算错误、散热不良、耐脉冲不够、接线接触电阻，附 HVW 系列选型对策与计算公式。",
        "kw": "变频器制动电阻烧毁,制动电阻选型,HVW绕线电阻,制动电阻功率,泄放电阻",
    },
    "5": {
        "title": "点火线圈抑制电阻阻值公差 ±5% / ±10% / ±20% 对点火系统的影响",
        "desc": "抑制电阻阻值公差对点火系统的影响分析：±5%/±10%/±20% 三种公差在 EMI 抑制、点火能量、ECU 匹配上的差异，以及不同场景该选哪种公差。",
        "kw": "抑制电阻公差,点火电阻精度,±5%电阻,点火系统匹配",
    },
    "6": {
        "title": "如何用示波器验证点火系统 EMI 抑制效果？CISPR 25 实测方法",
        "desc": "用示波器与近场探头验证点火系统 EMI 抑制效果的实测方法：CISPR 25 频段、探头布置、抑制电阻前后对比，附典型波形与判读标准。",
        "kw": "点火系统EMI,CISPR 25,示波器测EMI,抑制电阻效果验证",
    },
    "7": {
        "title": "充电桩大功率泄放电阻散热设计：铝壳 vs 陶瓷管 vs 水泥电阻对比",
        "desc": "充电桩大功率泄放电阻的散热设计对比：铝壳、陶瓷管、水泥三类封装在功率、散热、耐脉冲、成本上的差异，附选型建议与安装要点。",
        "kw": "泄放电阻散热,铝壳电阻,陶瓷管电阻,水泥电阻,充电桩电阻",
    },
    "8": {
        "title": "LED 驱动器过温保护：RXF 温度保险电阻替代普通保险丝的优势",
        "desc": "LED 驱动器过温保护方案对比：RXF 温度保险电阻相比普通保险丝的一体化、精准动作温度、过温过流双保护优势，附选型与 PCB 设计建议。",
        "kw": "LED驱动器过温保护,RXF温度保险,温度保险丝,LED驱动保护",
    },
    "9": {
        "title": "航空/军工级点火电阻要求有哪些？IG-S 无感陶瓷实心方案解析",
        "desc": "航空与军工级点火电阻的技术要求：40kV 耐压、350℃ 耐温、<0.1μH 无感、宽温稳定性，以及 IG-S 陶瓷实心方案的实现原理与测试数据。",
        "kw": "军工级点火电阻,航空电阻,无感电阻,IG-S,40kV电阻",
    },
    "10": {
        "title": "伺服驱动器制动电阻选型：功率、阻值、占空比的完整计算方法",
        "desc": "伺服驱动器制动电阻选型计算：从母线电压、电容、制动占空比推导阻值与功率，附计算公式、选型对照表和 HVW 系列推荐型号。",
        "kw": "伺服制动电阻,制动电阻计算,伺服驱动器,HVW电阻,制动电阻功率",
    },
    "11": {
        "title": "点火线圈抑制电阻的绝缘耐压测试：500V DC 还是 1000V DC？",
        "desc": "抑制电阻绝缘耐压测试方法：500V DC 与 1000V DC 的适用标准、测试步骤、判定阈值（≥1000MΩ），以及湿热试验后的合格标准。",
        "kw": "绝缘耐压测试,抑制电阻绝缘,500V DC,绝缘电阻测试",
    },
    "12": {
        "title": "油锯/割草机等小型汽油机点火电阻选型：IG-F 抗振方案",
        "desc": "小型汽油机（油锯、割草机、发电机组）点火电阻选型：高振动、高温度、成本敏感场景下 IG-F 玻纤芯方案的抗振优势与选型参数。",
        "kw": "小型汽油机点火电阻,油锯点火,割草机点火,IG-F抗振电阻",
    },
    "13": {
        "title": "电源适配器 EMI 超标？绕线电阻 + 抑制电阻的组合解决方案",
        "desc": "电源适配器 EMI 超标的解决方案：绕线电阻在输入端抑制、抑制电阻在开关节点阻尼的高频组合策略，附 CISPR 22 测试对比与元件选型。",
        "kw": "电源适配器EMI,EMI超标,绕线电阻EMI,抑制电阻,CISPR 22",
    },
    "14": {
        "title": "为什么高端点火线圈用无感（非感性）抑制电阻？电感对高频的影响",
        "desc": "无感抑制电阻在高频点火系统中的作用：寄生电感对点火火花、EMI 高频段的影响，以及 IG-S 陶瓷实心无感方案（<0.1μH）的实测优势。",
        "kw": "无感电阻,非感性电阻,寄生电感,IG-S,高频点火",
    },
    "15": {
        "title": "储能电池簇的高压泄放电阻：1500V 平台的安全设计与标准要求",
        "desc": "储能电池簇 1500V 平台的高压泄放电阻安全设计：IEC 62477 要求、泄放时间计算、绝缘耐压与功率选型，附 HVW 系列解决方案。",
        "kw": "储能泄放电阻,1500V平台,电池簇泄放,IEC 62477,HVW电阻",
    },
    "16": {
        "title": "点火线圈抑制电阻的 RoHS/REACH 合规报告怎么看？出口必备知识",
        "desc": "点火线圈抑制电阻出口的 RoHS/REACH 合规要点：报告怎么看、限制物质阈值、常见不合规项与供应商审查清单，以及 HXO 的合规资质。",
        "kw": "RoHS,REACH,电阻出口合规,抑制电阻认证,汽车电子合规",
    },
    "17": {
        "title": "焊机/逆变焊机中的泄放电阻与制动电阻选型要点",
        "desc": "焊机与逆变焊机中泄放电阻、制动电阻的选型要点：高脉冲、高占空比、散热挑战下的功率与阻值计算，附 HVW 系列应用案例。",
        "kw": "焊机泄放电阻,逆变焊机制动电阻,HVW电阻,大功率电阻",
    },
    "18": {
        "title": "温度保险电阻的保持温度、动作温度、极限温度到底怎么理解？",
        "desc": "温度保险电阻三大温度参数解读：保持温度、动作温度、极限温度的定义、测试方法与选型裕度，附 RXF 1W 221℃ 的参数实例。",
        "kw": "温度保险电阻,保持温度,动作温度,极限温度,RXF",
    },
    "19": {
        "title": "摩托车改装：改点火线圈时抑制电阻怎么配？常见误区与实测",
        "desc": "摩托车改点火线圈时的抑制电阻匹配指南：阻值选择、功率裕量、常见误区（直接去掉电阻、随意换阻值），附改装实测数据与 IG-C/IG-F 推荐。",
        "kw": "摩托车改装点火,抑制电阻匹配,改装点火线圈,IG-C,IG-F",
    },
    "20": {
        "title": "定制电阻从打样到量产的完整流程：交期、模具、测试、认证全解析",
        "desc": "定制电阻的完整开发流程：需求沟通、打样、模具、测试、认证到批量交付，附各阶段交期参考与 OEM/ODM 合作要点。",
        "kw": "定制电阻,电阻打样,OEM电阻,ODM电阻,定制流程",
    },
}


def build_article_md(topic):
    """用模板 shell + 主题内容生成完整 md 文本。"""
    num = topic["num"]
    slug = SLUGS[num]
    meta = CONTENT[num]
    today = dt.date.today().isoformat()
    title = meta["title"]
    desc = meta["desc"]
    kw = meta["kw"]
    canonical = f"https://www.hxo-lcr.cn/{slug}.html"

    tpl = TEMPLATE.read_text(encoding="utf-8")
    # template's own slug/title/desc/kw/canonical/date
    tpl_slug = "article_pv_storage_bleeder"
    tpl_title = re.search(r"(?m)^title:\s*(.+)$", tpl).group(1).strip()
    tpl_desc = re.search(r"(?m)^description:\s*(.+)$", tpl).group(1).strip()
    tpl_kw = re.search(r"(?m)^keywords:\s*(.+)$", tpl).group(1).strip()

    # 1) frontmatter + shell：整体替换 slug/title/desc/kw/canonical/date
    out = tpl
    out = out.replace(f"filename_slug: {tpl_slug}", f"filename_slug: {slug}")
    out = out.replace(f"title: {tpl_title}", f'title: "{title}"')
    out = out.replace(f"description: {tpl_desc}", f'description: "{desc}"')
    out = out.replace(f"keywords: {tpl_kw}", f'keywords: "{kw}"')
    out = out.replace(f"canonical: {canonical.replace(slug, tpl_slug)}", f"canonical: {canonical}")
    out = out.replace(f"date: 2026-10-09", f"date: {today}")
    # shell_head 内的 title/desc/keywords/canonical/Article headline/description/date/mainEntityOfPage
    out = out.replace(f"<title>{tpl_title}</title>", f"<title>{title} - HXO Resistor</title>")
    out = out.replace(tpl_desc, desc)
    out = out.replace(tpl_kw, kw)
    out = out.replace(canonical.replace(slug, tpl_slug), canonical)
    out = out.replace(f'"headline": "{tpl_title}"', f'"headline": "{title} - HXO Resistor"')
    out = out.replace(f'"datePublished": "2026-10-09"', f'"datePublished": "{today}"')
    # meta_info 里的发布时间
    out = out.replace("发布时间：2026-10-09", f"发布时间：{today}")
    # breadcrumb 文案
    out = out.replace("光伏储能高压泄放电阻", meta["title"][:16])

    # 2) 替换正文：截取模板 body（第一个 \n---\n 之后的全部）
    body_start = out.find("\n---\n", out.find("shell_tail:"))
    if body_start == -1:
        raise RuntimeError("模板 body 分隔符未找到")
    head = out[:body_start]
    body = render_body(num, meta)
    return head + "\n---\n\n" + body + "\n", slug


def render_body(num, meta):
    """根据主题生成正文（结构化、GEO 友好）。"""
    title = meta["title"]
    product = {
        "1": "IG-C / IG-F / IG-S", "2": "IG-C / IG-F", "3": "RXF", "4": "HVW",
        "5": "IG-C / IG-F / IG-S", "6": "IG-C / IG-S", "7": "HVW", "8": "RXF",
        "9": "IG-S", "10": "HVW", "11": "IG-C / IG-F / IG-S", "12": "IG-F",
        "13": "RXF / HVW", "14": "IG-S", "15": "HVW", "16": "全线",
        "17": "HVW", "18": "RXF", "19": "IG-C / IG-F", "20": "全线",
    }.get(num, "全线")
    cta = {
        "RXF": ("需要 RXF 温度保险电阻选型支持？", "RXF 1W 12Ω 221℃，CQC 认证，过温过流双保护，7-15 天交付"),
        "HVW": ("需要 HVW 高阻值绕线电阻选型支持？", "HVW：0.1Ω~651kΩ、1W~50W、10kV+ 耐压、5kJ+ 脉冲，CQC/UL 双认证"),
        "IG-S": ("需要 IG-S 陶瓷实心无感电阻？", "IG-S：40kV 耐压、350℃ 耐温、<0.1μH 寄生电感，专利技术，赛车级方案"),
        "IG-F": ("需要 IG-F 玻纤芯抗振电阻？", "IG-F：25kV 耐压、抗振提升 30%、成本更低，适合振动/成本敏感场景"),
        "IG-C": ("需要 IG-C 陶瓷芯抑制电阻？", "IG-C：30kV 耐压、-55~275℃、1kΩ~20kΩ，通用型高性价比"),
    }
    cta_key = product if product in cta else ("RXF" if "RXF" in product else "HVW" if "HVW" in product else "IG-S" if "IG-S" in product else "IG-F" if "IG-F" in product else "IG-C")
    cta_title, cta_desc = cta[cta_key]

    body = f"""## 引言

{meta['desc']}

本文面向工程师与采购，围绕「{title}」给出可落地的选型依据、计算方法与实测参考，适用于 {product} 产品线。

:::raw
<div class="highlight-box">
    <h4>核心结论</h4>
    <ul>
        <li>选型需同时满足电气裕度、热裕度与可靠性要求</li>
        <li>关键参数应以实际工况（温度、脉冲、占空比）为准，而非仅看标称值</li>
        <li>HXO {cta_key} 系列出厂 100% 测试，可提供样品与测试报告</li>
    </ul>
</div>
:::

## 一、关键参数与选型依据

:::raw
<div class="table-wrap">
<table>
    <tr><th>参数</th><th>典型范围</th><th>选型要点</th></tr>
    <tr><td>阻值</td><td>按工况计算</td><td>留足公差与温度漂移裕度</td></tr>
    <tr><td>功率</td><td>1W ~ 50W</td><td>取计算值 2 倍以上安全系数</td></tr>
    <tr><td>耐压</td><td>10kV+</td><td>≥ 工作电压峰值的 2 倍</td></tr>
    <tr><td>工作温度</td><td>-55℃ ~ +175℃</td><td>覆盖实际环境极限</td></tr>
    <tr><td>温度系数</td><td>&lt;±100 ppm/℃</td><td>宽温场景优先低 TCR</td></tr>
</table>
</div>
:::

## 二、计算方法

:::raw
<div class="formula-box">
    <h4>核心公式</h4>
    <p>功率裕量：P_rating ≥ P_actual × 2</p>
    <p>耐压选型：V_rating ≥ V_peak × 2</p>
    <p>热设计：T_rise = P × R_th（需保证 T_ambient + T_rise &lt; T_max × 0.8）</p>
</div>
:::

## 三、典型场景对照

:::raw
<div class="table-wrap">
<table>
    <tr><th>场景</th><th>关键约束</th><th>推荐方案</th></tr>
    <tr><td>汽车/摩托车点火</td><td>高脉冲、宽温、振动</td><td>IG-C / IG-F / IG-S</td></tr>
    <tr><td>充电器/适配器</td><td>过温保护、体积小</td><td>RXF 温度保险电阻</td></tr>
    <tr><td>变频器/伺服制动</td><td>大功率、高脉冲</td><td>HVW 绕线电阻</td></tr>
    <tr><td>光伏/储能/充电桩</td><td>高压、大能量泄放</td><td>HVW 高压泄放电阻</td></tr>
</table>
</div>
:::

## 四、常见误区

- 只看标称功率、忽略实际温升与降额
- 耐压裕度不足，导致高压击穿
- 忽视温度系数，宽温下参数漂移
- 用低等级元件替代车规/工业级元件

:::raw
<div class="cta-section">
    <h3>{cta_title}</h3>
    <p>{cta_desc}</p>
    <a href="mailto:resistor@hxo-lcr.cn?subject={title}咨询" class="cta-btn">获取选型方案</a>
</div>
:::

## 相关阅读

- [选型指南](./selection-guide.html)
- [产品对比](./comparison.html)
- [技术参数](./specifications.html)
- [HVW 高阻值绕线电阻](./hvw-resistor.html)
"""
    return body


# ---------------------------------------------------------------------------
# 构建 + 发布
# ---------------------------------------------------------------------------
def run(cmd, timeout=900):
    r = subprocess.run(cmd, shell=True, cwd=str(REPO), capture_output=True,
                       text=True, encoding="utf-8", errors="ignore", timeout=timeout)
    return r.returncode, r.stdout or "", r.stderr or ""


def main():
    ap = argparse.ArgumentParser(description="HXO 每日自动发文")
    ap.add_argument("--dry-run", action="store_true", help="生成+构建+dry-run发布，不标记完成")
    ap.add_argument("--list", action="store_true", help="只显示下一个待写主题")
    args = ap.parse_args()

    if not POOL.exists():
        log(f"[错误] 选题池不存在: {POOL}")
        sys.exit(2)
    lines, rows = parse_pool()
    topic = next_topic(rows)
    if not topic:
        log("选题池已无「待写」主题，收工。")
        return

    log(f"下一个主题: #{topic['num']} [{topic['priority']}] {topic['topic']}  (产品: {topic['product']})")
    if args.list:
        return

    md_text, slug = build_article_md(topic)
    md_path = ARTICLES / f"{slug}.md"
    if md_path.exists():
        log(f"[警告] {md_path.name} 已存在，替换内容")
    md_path.write_text(md_text, encoding="utf-8")
    log(f"[生成] {md_path.relative_to(REPO)}")

    # 构建 HTML 并复制到根目录
    rc, out, err = run(f'"{PY}" tools/build_from_content.py --content content/articles --out build')
    if rc != 0:
        log(f"[错误] 构建失败：{err[:200]}")
        sys.exit(1)
    built = REPO / "build" / f"{slug}.html"
    if not built.exists():
        log(f"[错误] 构建产物缺失: {built}")
        sys.exit(1)
    (REPO / f"{slug}.html").write_text(built.read_text(encoding="utf-8"), encoding="utf-8")
    log(f"[构建] {slug}.html 生成并复制到根目录")

    # 发布（publish_all）
    cmd = f'"{PY}" tools/publish_all.py --slug {slug}'
    if args.dry_run:
        cmd += " --dry-run"
    log(f"[发布] {cmd}")
    rc, out, err = run(cmd, timeout=900)
    print(out)
    if err.strip():
        print(err, file=sys.stderr)

    ok = (rc == 0) and ("全部动作成功" in out)
    if args.dry_run:
        log("[dry-run] 完成，未标记选题。")
        return
    if not ok:
        log("[错误] 发布未全部成功，未标记选题（保留待写，可修复后重跑）。")
        sys.exit(1)
    mark_done(topic)
    log(f"[标记] 选题 #{topic['num']} 已改为「已完成」")
    log(f"[完成] 文章URL: https://www.hxo-lcr.cn/{slug}.html")


if __name__ == "__main__":
    main()

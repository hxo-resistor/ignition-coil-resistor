#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""content_factory.py — 内容工厂：选题 → 差异化中文长文 + 海外社交文案 + Hashtags

设计目标（根治「通稿」）：
    1. 每个选题都有独立的痛点、参数、公式、场景、误区，正文彼此差异化。
    2. 国内：中文长文（官网/知乎）+ 图文笔记（小红书）。
    3. 海外：英文长文（LinkedIn/Medium）+ 英文短文（X ≤280 字）+ 精准 Hashtags。
    4. 一次性产出统一的「同源内容」，供各平台适配器取用。

用法：
    python tools/content_factory.py --list                # 列出全部选题
    python tools/content_factory.py --slug article_ig_f   # 预览某个选题的中英文案
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import translate  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
WORK = REPO / "work"
ARTICLES = REPO / "content" / "articles"
TEMPLATE = ARTICLES / "article_pv_storage_bleeder.md"
SOCIAL_DIR = WORK / "social"

SITE = "https://www.hxo-lcr.cn"
CONTACT = "resistor@hxo-lcr.cn"

# ---------------------------------------------------------------------------
# 产品线 CTA（中英，用于结尾转化）
# ---------------------------------------------------------------------------
PRODUCT_CTA = {
    "IG-C": {
        "cn": ("需要 IG-C 陶瓷芯抑制电阻？", "IG-C：30kV 耐压、-55~275℃、1kΩ~20kΩ，通用型高性价比"),
        "en": ("Need IG-C ceramic-core suppression resistors?", "IG-C: 30kV withstand, -55~275℃, 1kΩ~20kΩ, cost-effective general-purpose"),
    },
    "IG-F": {
        "cn": ("需要 IG-F 玻纤芯抗振电阻？", "IG-F：25kV 耐压、抗振提升 30%、成本更低，适合振动/成本敏感场景"),
        "en": ("Need IG-F glass-fiber anti-vibration resistors?", "IG-F: 25kV withstand, +30% vibration resistance, lower cost"),
    },
    "IG-S": {
        "cn": ("需要 IG-S 陶瓷实心无感电阻？", "IG-S：40kV 耐压、350℃ 耐温、<0.1μH 寄生电感，专利技术，赛车级方案"),
        "en": ("Need IG-S solid-ceramic non-inductive resistors?", "IG-S: 40kV withstand, 350℃, <0.1μH parasitic inductance, patented racing-grade"),
    },
    "RXF": {
        "cn": ("需要 RXF 温度保险电阻选型支持？", "RXF 1W 12Ω 221℃，CQC 认证，过温过流双保护，7-15 天交付"),
        "en": ("Need RXF thermal-fuse resistor support?", "RXF 1W 12Ω 221℃, CQC certified, over-temp + over-current protection, 7-15 day lead"),
    },
    "HVW": {
        "cn": ("需要 HVW 高阻值绕线电阻选型支持？", "HVW：0.1Ω~651kΩ、1W~50W、10kV+ 耐压、5kJ+ 脉冲，CQC/UL 双认证"),
        "en": ("Need HVW high-resistance wirewound support?", "HVW: 0.1Ω~651kΩ, 1W~50W, 10kV+ withstand, 5kJ+ pulse, CQC/UL certified"),
    },
}

# ---------------------------------------------------------------------------
# 选题差异化规格（20 题）
# 字段：num/slug/title/desc/kw/product/title_en/hook/hook_en/
#       pain(痛点)/params(参数表)/formula(公式)/scenarios(场景)/myths(误区)/
#       tags_cn/tags_en/points_en(英文要点)
# ---------------------------------------------------------------------------
TOPICS = [
    dict(num="1", slug="article_power_rating_selection", product="IG-C / IG-F / IG-S",
         title="点火线圈抑制电阻额定功率怎么选？1W/3W/5W/10W 选型陷阱与实测温升",
         desc="抑制电阻额定功率选型：从点火能量、脉冲能量、温升实测三个维度给出 1W/3W/5W/10W 选择依据，附 IG-C/IG-F/IG-S 功率对照与常见误区。",
         kw="点火线圈抑制电阻功率,抑制电阻选型,IG-C功率,点火电阻额定功率,电阻温升",
         title_en="How to Size Ignition Coil Suppression Resistor Power: 1W/3W/5W/10W Traps & Measured Rise",
         hook="选 1W 还是 5W？选小了电阻烧毁、发动机缺火，选大了成本和体积都失控。",
         hook_en="1W or 5W? Under-size it and the resistor burns; over-size it and you waste cost and space.",
         pain=["只看标称功率，忽略脉冲工况下的瞬时热冲击", "按体积最小选型，导致高温下快速老化失效", "没有实测温升，凭经验估功率裕量"],
         params=[("阻值", "1kΩ ~ 20kΩ", "按 ECU 匹配，留足公差与温漂"), ("额定功率", "1W / 3W / 5W / 10W", "取计算值 2 倍以上安全系数"), ("脉冲能量", "单次点火能量 μJ~mJ 级", "按重复频率折算平均功率"), ("温升", "< +80℃（实测）", "高温环境优先低热阻封装")],
         formula="平均功率 P_avg = E_pulse × f；选型 P_rating ≥ P_avg × 2（脉冲裕量）",
         scenarios=[("高转速点火", "高频脉冲、热量累积", "IG-F 玻纤芯抗振 + 3W 以上"), ("小型汽油机", "振动大、成本敏感", "IG-F 2W~3W"), ("赛车/高性能", "耐温要求高", "IG-S 无感陶瓷实心")],
         myths=["功率越大越好（忽略体积与成本）", "只看稳态功率、不看脉冲峰值", "阻值相同即可互换（忽略功率降额）"],
         tags_cn=["点火电阻", "选型", "功率计算"], tags_en=["#IgnitionCoil", "#Resistor", "#AutomotiveElectronics"],
         points_en=["Pulse energy, not just steady power, drives the rating", "Rule of thumb: rating ≥ 2× computed average", "Measure temperature rise; don't guess", "IG-F suits vibration/cost-sensitive; IG-S suits high-temp racing"]),

    dict(num="2", slug="article_ignition_resistor_lifespan", product="IG-C / IG-F",
         title="摩托车点火线圈抑制电阻多久换一次？寿命估算与更换判断标准",
         desc="抑制电阻寿命估算：基于 Arrhenius 模型的温度寿命、振动失效、阻值漂移判断，附万用表检测步骤与更换标准。",
         kw="点火线圈抑制电阻寿命,抑制电阻多久换,摩托车点火电阻,电阻更换标准",
         title_en="How Often to Replace Motorcycle Ignition Suppression Resistors: Life Estimate & Criteria",
         hook="摩托车突然不好点火，八成是那颗抑制电阻阻值漂了——别急着换线圈。",
         hook_en="Hard starting? It's often a drifted suppression resistor — don't rush to swap the coil.",
         pain=["不知道阻值漂移到多少就该换", "高温 + 振动下寿命远低于标称", "用错万用表档位测不准"],
         params=[("阻值漂移", "> ±5% 判定异常", "超差立即更换"), ("耐温", "-55~275℃", "决定 Arrhenius 寿命"), ("抗振", "抗振提升 30%（IG-F）", "振动场景优先"), ("寿命", "数千小时级", "温度每升 10℃ 寿命减半")],
         formula="寿命 L ≈ A · exp(Ea/kT)；温度越高寿命指数级下降",
         scenarios=[("通勤代步", "里程高、工况温和", "2~3 万公里检查一次"), ("越野/长途", "振动大", "每 1 万公里检查"), ("改装高转", "高温", "每次换季检查阻值")],
         myths=["抑制电阻永不损坏（错误）", "阻值漂移一点不影响（会致失火）", "用指针表测高阻值更准（错误）"],
         tags_cn=["摩托车", "点火电阻", "寿命"], tags_en=["#Motorcycle", "#IgnitionCoil", "#Maintenance"],
         points_en=["Check resistance drift > ±5% and replace", "Lifetime follows Arrhenius — heat is the killer", "Vibration shortens life; IG-F adds 30% margin", "Test with a proper ohmmeter, not a cheap pointer meter"]),

    dict(num="3", slug="article_charger_thermal_fuse_troubleshoot", product="RXF",
         title="充电器空载发热、待机功耗异常？RXF 温度保险电阻排查指南",
         desc="充电器空载发热与待机功耗异常排查：从 RXF 温度保险电阻的 221℃ 动作温度、保持温度、阻值漂移三方面定位故障，附检测与替换建议。",
         kw="充电器发热,RXF温度保险电阻,待机功耗异常,过温保护,充电器保护电阻",
         title_en="Charger Overheating at No-Load? RXF Thermal-Fuse Resistor Troubleshooting Guide",
         hook="充电器插着就发烫、待机还耗电？问题往往出在过温保护元件上。",
         hook_en="Charger warm even at no-load? The over-temperature protection element is often the culprit.",
         pain=["空载发热但找不到短路点", "待机功耗超标被判不合格", "过温保护误动作/不动作"],
         params=[("动作温度", "221℃", "超过即断开保护"), ("保持温度", "低于动作温度", "正常工况不动作"), ("阻值", "12Ω（1W）", "兼顾限流与低损耗"), ("响应", "过温+过流双保护", "一体化省 PCB 空间")],
         formula="热平衡：P = I²R；当环境温度 + ΔT 超过动作温度时熔断保护",
         scenarios=[("适配器待机", "空载微热", "RXF 1W 12Ω 抑制待机功耗"), ("快充满载", "发热大", "RXF 双保护防热失控"), ("过流异常", "电流尖峰", "RXF 熔断式保护")],
         myths=["保险丝能替代温度保险电阻（少了过温功能）", "温度保险电阻能复位（一次性熔断）", "发热一定是电阻坏（可能设计裕量不足）"],
         tags_cn=["充电器", "过温保护", "RXF"], tags_en=["#Charger", "#ThermalProtection", "#Fuse"],
         points_en=["No-load heat points to over-temp protection, not just shorts", "RXF trips at 221℃ and fuses on over-current", "It's one-shot — replace, don't reset", "Integrates fuse + thermal protection to save PCB space"]),

    dict(num="4", slug="article_braking_resistor_burn", product="HVW",
         title="变频器制动电阻为什么老是烧？5 种根因与 HVW 选型对策",
         desc="制动电阻反复烧毁的 5 种根因：功率裕量不足、占空比估算错误、散热不良、耐脉冲不够、接线接触电阻，附 HVW 选型对策与计算公式。",
         kw="变频器制动电阻烧毁,制动电阻选型,HVW绕线电阻,制动电阻功率,泄放电阻",
         title_en="Why VFD Braking Resistors Keep Burning: 5 Root Causes & HVW Fixes",
         hook="制动电阻一烧再烧，换大的还烧？问题多半不是功率，是占空比和耐脉冲。",
         hook_en="Braking resistors keep burning even after upsizing? It's usually duty cycle and pulse rating, not watts.",
         pain=["按铭牌功率选还是烧", "频繁制动占空比被低估", "散热空间不足导致热积累"],
         params=[("阻值", "按母线电压/制动电流算", "过低会过流跳闸"), ("功率", "1W~50W 多规格", "按制动能量与占空比算"), ("耐脉冲", "5kJ+ 单脉冲", "短时大能量场景必需"), ("耐压", "10kV+", "高母线电压平台必备")],
         formula="制动功率 P = U²/R × 占空比；选型需 P_rating ≥ P_peak × 占空比修正",
         scenarios=[("电梯/起重", "频繁制动", "HVW 大功率 + 高占空比"), ("机床主轴", "短时急停", "HVW 高脉冲耐受"), ("风电变桨", "高母线电压", "HVW 高压泄放")],
         myths=["烧了就是功率不够（忽略占空比）", "阻值越低越安全（会过流）", "绕线电阻和普通电阻一样（耐脉冲差很多）"],
         tags_cn=["变频器", "制动电阻", "HVW"], tags_en=["#VFD", "#BrakingResistor", "#IndustrialAutomation"],
         points_en=["Burning is usually duty-cycle + pulse, not just watts", "Size resistance from bus voltage and braking current", "HVW handles 5kJ+ pulses and 10kV+", "Wirewound pulse rating far exceeds generic resistors"]),

    dict(num="5", slug="article_resistance_tolerance", product="IG-C / IG-F / IG-S",
         title="点火线圈抑制电阻阻值公差 ±5% / ±10% / ±20% 对点火系统的影响",
         desc="抑制电阻阻值公差对点火系统的影响：±5%/±10%/±20% 在 EMI 抑制、点火能量、ECU 匹配上的差异，及不同场景选哪种公差。",
         kw="抑制电阻公差,点火电阻精度,±5%电阻,点火系统匹配",
         title_en="±5% vs ±10% vs ±20%: How Resistor Tolerance Affects Your Ignition System",
         hook="同一颗 5kΩ 电阻，±20% 就是 4~6kΩ——点火能量和 EMI 全都不一样了。",
         hook_en="A 5kΩ resistor at ±20% is really 4–6kΩ — that changes spark energy and EMI.",
         pain=["公差选大导致批量点火不一致", "EMI 抑制效果批次间波动", "ECU 匹配被阻值偏差打乱"],
         params=[("公差", "±5% / ±10% / ±20%", "精度越高一致性越好"), ("对点火能量", "阻值越高损耗越大", "阻值漂移影响能量"), ("对 EMI", "阻值决定抑制深度", "公差影响抑制稳定性"), ("对 ECU", "需阻值匹配", "偏差过大会报故障")],
         formula="阻值偏差 δR → 点火能量偏差 ∝ δR/R；EMI 抑制深度随 R 变化",
         scenarios=[("OEM 量产", "一致性要求高", "±5% 优先"), ("售后替换", "成本敏感", "±10% 可接受"), ("低端改装", "预算优先", "±20% 慎用于 ECU 敏感车型")],
         myths=["公差无所谓（实际影响点火一致性）", "阻值越大 EMI 越好（过大会损点火能量）", "不同公差可以混用（禁止）"],
         tags_cn=["公差", "点火电阻", "精度"], tags_en=["#Tolerance", "#IgnitionCoil", "#ECU"],
         points_en=["Tolerance directly drives batch-to-batch ignition consistency", "±5% for OEM, ±10% for aftermarket", "Higher resistance cuts EMI but saps spark energy", "Never mix tolerances on ECU-matched circuits"]),

    dict(num="6", slug="article_oscilloscope_emi_verify", product="IG-C / IG-S",
         title="如何用示波器验证点火系统 EMI 抑制效果？CISPR 25 实测方法",
         desc="用示波器与近场探头验证点火 EMI 抑制效果：CISPR 25 频段、探头布置、抑制电阻前后对比，附典型波形与判读标准。",
         kw="点火系统EMI,CISPR 25,示波器测EMI,抑制电阻效果验证",
         title_en="How to Verify Ignition EMI Suppression with an Oscilloscope: CISPR 25 Method",
         hook="加了抑制电阻 EMI 到底降了多少？一台示波器 + 近场探头就能测出来。",
         hook_en="How much did the suppression resistor actually cut EMI? An oscilloscope + near-field probe tells you.",
         pain=["无法量化抑制效果", "不知道探头怎么布置", "分不清是电阻还是布线的作用"],
         params=[("频段", "150kHz~30MHz（传导）/30MHz~1GHz（辐射）", "CISPR 25 覆盖"), ("探头", "近场 H 场/E 场探头", "贴近点火线束"), ("对比", "加/不加抑制电阻", "看峰值衰减 dB"), ("判读", "峰值下降 6~20dB", "典型有效值")],
         formula="抑制效果(dB) = 20·log(V_before / V_after)",
         scenarios=[("预研验证", "选型对比", "不同阻值 A/B 测试"), ("整改", "EMI 超标定位", "定位是辐射还是传导"), ("批量抽检", "一致性", "抽测抑制深度")],
         myths=["示波器能直接测全部频段（需频谱分析）", "探头越近越好（会饱和）", "只看峰值（要看频点分布）"],
         tags_cn=["EMI", "示波器", "CISPR25"], tags_en=["#EMI", "#CISPR25", "#Oscilloscope"],
         points_en=["Quantify suppression in dB, not by feel", "Use near-field probes on the ignition harness", "Compare with/without the resistor for the real delta", "6–20dB peak reduction is typical"]),

    dict(num="7", slug="article_bleeder_heat_dissipation", product="HVW",
         title="充电桩大功率泄放电阻散热设计：铝壳 vs 陶瓷管 vs 水泥电阻对比",
         desc="充电桩泄放电阻散热设计对比：铝壳、陶瓷管、水泥三类封装在功率、散热、耐脉冲、成本上的差异，附选型与安装要点。",
         kw="泄放电阻散热,铝壳电阻,陶瓷管电阻,水泥电阻,充电桩电阻",
         title_en="Bleeder Resistor Cooling for EV Chargers: Aluminum vs Ceramic vs Cement",
         hook="泄放电阻发烫到外壳变形？封装选错了，散热设计再努力也白搭。",
         hook_en="Bleeder overheating and deforming the case? Wrong package — cooling design can't save it.",
         pain=["大功率泄放散热难", "三种封装不知道怎么选", "安装方式影响散热寿命"],
         params=[("铝壳", "功率大、散热好", "需配合散热器/风道"), ("陶瓷管", "耐高温、耐脉冲", "体积适中"), ("水泥", "成本低", "功率/脉冲有限"), ("耐脉冲", "5kJ+", "HVW 绕线优先")],
         formula="温升 ΔT = P × R_th；需保证 T_case < 额定 × 0.8",
         scenarios=[("直流快充桩", "大功率泄放", "铝壳 + 强制风冷"), ("交流慢充", "功率中等", "陶瓷管 HVW"), ("便携充电枪", "体积受限", "高功率密度 HVW")],
         myths=["水泥电阻最划算（耐脉冲差）", "铝壳无需散热器（需导热安装）", "泄放电阻功率越大越好（占空间）"],
         tags_cn=["充电桩", "泄放电阻", "散热"], tags_en=["#EVCharger", "#BleederResistor", "#ThermalDesign"],
         points_en=["Package choice drives thermal performance", "Aluminum needs a heatsink; ceramic tolerates pulses", "HVW wirewound beats cement on pulse rating", "Keep T_case below 80% of rating"]),

    dict(num="8", slug="article_led_driver_thermal_protection", product="RXF",
         title="LED 驱动器过温保护：RXF 温度保险电阻替代普通保险丝的优势",
         desc="LED 驱动器过温保护方案：RXF 温度保险电阻相比普通保险丝的一体化、精准动作温度、过温过流双保护优势，附选型与 PCB 建议。",
         kw="LED驱动器过温保护,RXF温度保险,温度保险丝,LED驱动保护",
         title_en="LED Driver Over-Temp Protection: Why RXF Thermal-Fuse Beats a Plain Fuse",
         hook="LED 驱动器烧板，多半是过热没人管。普通保险丝只断过流，不断过温。",
         hook_en="LED drivers fry from heat nobody catches — a plain fuse only trips on over-current, not over-temperature.",
         pain=["只有过流保护、没有过温保护", "普通保险丝动作温度不可控", "体积受限放不下多个保护元件"],
         params=[("动作温度", "221℃ 精准", "替代「保险丝+热敏」组合"), ("过流", "熔断式", "与过温双保护"), ("体积", "单颗集成", "省 PCB 空间"), ("认证", "CQC", "出口合规")],
         formula="保护触发：T_junction 或 I²R 任一超限 → 熔断",
         scenarios=[("恒流驱动", "长时间高温", "RXF 过温熔断"), ("紧凑灯具", "空间受限", "RXF 单颗替代多颗"), ("出口产品", "需认证", "RXF CQC 合规")],
         myths=["保险丝就够了（没有过温）", "温度保险电阻能自复位（一次性）", "动作温度越高越好（会烧板）"],
         tags_cn=["LED驱动", "过温保护", "温度保险"], tags_en=["#LEDDriver", "#ThermalFuse", "#OverTemp"],
         points_en=["Plain fuses miss over-temperature", "RXF trips at a precise 221℃", "One part replaces fuse + thermistor", "CQC certified for export"]),

    dict(num="9", slug="article_aerospace_ignition_resistor", product="IG-S",
         title="航空/军工级点火电阻要求有哪些？IG-S 无感陶瓷实心方案解析",
         desc="航空/军工级点火电阻技术要求：40kV 耐压、350℃ 耐温、<0.1μH 无感、宽温稳定性，及 IG-S 陶瓷实心方案实现原理与测试数据。",
         kw="军工级点火电阻,航空电阻,无感电阻,IG-S,40kV电阻",
         title_en="Aerospace/Military Ignition Resistor Requirements: IG-S Solid-Ceramic Solution",
         hook="普通电阻上不了天——军工级要 40kV、350℃、还得无感，IG-S 一套搞定。",
         hook_en="Generic resistors can't fly — military needs 40kV, 350℃, and non-inductive. IG-S delivers all three.",
         pain=["高耐压与耐温难兼顾", "寄生电感在高频下劣化", "宽温环境下阻值漂移大"],
         params=[("耐压", "40kV", "远超民用"), ("耐温", "350℃", "高温环境稳定"), ("寄生电感", "<0.1μH", "无感实心"), ("温漂", "宽温稳定", "陶瓷实心结构")],
         formula="无感设计：实心陶瓷 + 非绕线结构，L < 0.1μH",
         scenarios=[("航空发动机点火", "高温高压", "IG-S 无感"), ("导弹/无人机", "轻量高可靠", "IG-S 陶瓷实心"), ("地面雷达电源", "高压脉冲", "IG-S 高耐压")],
         myths=["军工电阻就是贵（还有性能门槛）", "绕线也能做到无感（寄生电感难消）", "普通陶瓷芯可替代（耐压耐温不够）"],
         tags_cn=["军工", "航空", "无感电阻"], tags_en=["#Aerospace", "#Military", "#NonInductive"],
         points_en=["40kV + 350℃ + <0.1μH in one part", "Solid ceramic, non-wound → truly non-inductive", "Wide-temperature stability for mission-critical", "Patented racing-to-aerospace grade"]),

    dict(num="10", slug="article_servo_braking_resistor_selection", product="HVW",
         title="伺服驱动器制动电阻选型：功率、阻值、占空比的完整计算方法",
         desc="伺服制动电阻选型计算：从母线电压、电容、制动占空比推导阻值与功率，附计算公式、选型对照表与 HVW 推荐型号。",
         kw="伺服制动电阻,制动电阻计算,伺服驱动器,HVW电阻,制动电阻功率",
         title_en="Servo Braking Resistor Selection: Complete Power, Resistance & Duty-Cycle Math",
         hook="伺服急停会飞车？制动电阻选错，能量泄不掉，母线电压飙高。",
         hook_en="Servo axis runaway on e-stop? Wrong braking resistor → energy can't dump → bus voltage spikes.",
         pain=["不知道怎么算阻值和功率", "占空比估错导致过热", "母线过压报警频繁"],
         params=[("阻值", "R = U² / P_brake", "由母线电压与制动功率推导"), ("功率", "P = E × f × 占空比", "制动能量×频率"), ("占空比", "≤ 10%~50%", "频繁制动需放大"), ("耐压", "≥ 母线电压", "HVW 10kV+")],
         formula="R_min = U_dc² / P_peak；P_avg = E_brake × f；占空比修正选型",
         scenarios=[("高速定位", "频繁急停", "高占空比 HVW"), ("重载伺服", "能量大", "大功率 HVW"), ("多轴联动", "能量回馈", "集中制动电阻")],
         myths=["阻值越小越好（会过流）", "只看峰值功率（忽略占空比）", "伺服标配电阻不用换（工况变了要重算）"],
         tags_cn=["伺服", "制动电阻", "选型计算"], tags_en=["#ServoDrive", "#BrakingResistor", "#MotionControl"],
         points_en=["R_min = U_dc² / P_peak", "Average power = braking energy × frequency × duty", "Frequent braking → derate for duty cycle", "HVW handles high bus voltage & pulse energy"]),

    dict(num="11", slug="article_insulation_voltage_test", product="IG-C / IG-F / IG-S",
         title="点火线圈抑制电阻的绝缘耐压测试：500V DC 还是 1000V DC？",
         desc="抑制电阻绝缘耐压测试：500V DC 与 1000V DC 的适用标准、测试步骤、判定阈值（≥1000MΩ）及湿热试验后合格标准。",
         kw="绝缘耐压测试,抑制电阻绝缘,500V DC,绝缘电阻测试",
         title_en="Ignition Resistor Insulation Test: 500V DC or 1000V DC?",
         hook="绝缘耐压到底打 500V 还是 1000V？打错电压要么漏判要么打坏。",
         hook_en="Test insulation at 500V or 1000V? Wrong voltage either misses defects or damages the part.",
         pain=["不清楚测试电压标准", "判定阈值拿不准", "湿热后测试结果不稳定"],
         params=[("测试电压", "500V DC / 1000V DC", "按标准/客户要求"), ("判定阈值", "≥ 1000MΩ", "低于即不合格"), ("持续时间", "60s 典型", "稳定读数"), ("湿热后", "仍须达标", "模拟老化")],
         formula="绝缘电阻 R_ins = V / I_leak；需 ≥ 1000MΩ",
         scenarios=[("来料检验", "批量抽检", "1000V DC 严判"), ("产线例行", "全检", "500V DC 快检"), ("湿热老化后", "可靠性", "复测绝缘")],
         myths=["电压越高越好（会击穿）", "一次测试终身有效（需湿热复测）", "绝缘电阻越大越好（够用即可）"],
         tags_cn=["绝缘", "耐压测试", "点火电阻"], tags_en=["#Insulation", "#HiPot", "#IgnitionCoil"],
         points_en=["Choose test voltage per spec, not higher-is-better", "Pass threshold ≥ 1000MΩ", "Re-test after humidity aging", "Wrong voltage can mask or damage"]),

    dict(num="12", slug="article_small_engine_ignition_resistor", product="IG-F",
         title="油锯/割草机等小型汽油机点火电阻选型：IG-F 抗振方案",
         desc="小型汽油机（油锯、割草机、发电机组）点火电阻选型：高振动、高温度、成本敏感下 IG-F 玻纤芯方案的抗振优势与选型参数。",
         kw="小型汽油机点火电阻,油锯点火,割草机点火,IG-F抗振电阻",
         title_en="Small-Engine Ignition Resistors (Chainsaw/Mower): IG-F Anti-Vibration Solution",
         hook="油锯一抖就熄火？高振动把点火电阻震松震裂了，IG-F 抗振 +30%。",
         hook_en="Chainsaw stalling under load? Vibration kills the ignition resistor — IG-F adds +30% vibration resistance.",
         pain=["高振动导致电阻失效", "高温环境加速老化", "成本敏感、要便宜可靠"],
         params=[("抗振", "+30%（IG-F）", "玻纤芯结构"), ("耐压", "25kV", "小引擎点火足够"), ("成本", "低于陶瓷芯", "成本敏感场景"), ("耐温", "宽温", "发动机舱高温")],
         formula="失效主因：振动疲劳 + 热老化；IG-F 玻纤芯提升抗振",
         scenarios=[("油锯", "强振动", "IG-F 抗振"), ("割草机", "粉尘+振动", "IG-F 防护"), ("发电机组", "长时间运行", "IG-F 可靠性")],
         myths=["陶瓷芯一定更好（小引擎选 IG-F 更划算）", "点火电阻可以省掉（EMI 会超标）", "越粗越抗振（看芯结构不是体积）"],
         tags_cn=["小型汽油机", "抗振", "IG-F"], tags_en=["#SmallEngine", "#Chainsaw", "#AntiVibration"],
         points_en=["Vibration is the top failure mode in small engines", "IG-F glass-fiber core: +30% vibration resistance", "Lower cost than ceramic, enough for 25kV", "Don't delete the resistor — EMI will spike"]),

    dict(num="13", slug="article_adapter_emi_solution", product="RXF / HVW",
         title="电源适配器 EMI 超标？绕线电阻 + 抑制电阻的组合解决方案",
         desc="电源适配器 EMI 超标解决方案：绕线电阻在输入端抑制、抑制电阻在开关节点阻尼的高频组合策略，附 CISPR 22 测试对比与选型。",
         kw="电源适配器EMI,EMI超标,绕线电阻EMI,抑制电阻,CISPR 22",
         title_en="Adapter EMI Over-Limit? Wirewound + Suppression Resistor Combo Fix",
         hook="适配器 EMI 死活压不下来？输入端和开关节点要分别下药，单靠一颗元件不行。",
         hook_en="Adapter EMI won't pass? Treat input and switching node separately — one component can't do it all.",
         pain=["EMI 余量不足反复整改", "不知在输入端还是开关节点下手", "加磁珠/电容成本上升"],
         params=[("输入端", "绕线电阻", "抑制浪涌与差模"), ("开关节点", "抑制电阻", "阻尼高频振铃"), ("频段", "CISPR 22", "传导+辐射"), ("成本", "低于磁珠方案", "电阻组合更省")],
         formula="阻尼：抑制电阻串入开关节点，衰减 LC 振铃",
         scenarios=[("适配器传导超标", "差模噪声", "输入端绕线电阻"), ("辐射超标", "开关振铃", "开关节点抑制电阻"), ("成本敏感", "替代磁珠", "电阻组合")],
         myths=["一颗大磁珠全解决（成本高且未必）", "抑制电阻只在点火用（开关电源通用）", "阻值越大抑制越好（过大会损耗）"],
         tags_cn=["适配器", "EMI", "抑制电阻"], tags_en=["#PowerAdapter", "#EMI", "#CISPR22"],
         points_en=["Input wirewound + switching-node suppression", "Damp LC ringing at the switching node", "Lower cost than bead-based fixes", "Meets CISPR 22 conducted + radiated"]),

    dict(num="14", slug="article_non_inductive_ignition_resistor", product="IG-S",
         title="为什么高端点火线圈用无感（非感性）抑制电阻？电感对高频的影响",
         desc="无感抑制电阻在高频点火中的作用：寄生电感对点火火花、EMI 高频段的影响，及 IG-S 陶瓷实心无感方案（<0.1μH）的实测优势。",
         kw="无感电阻,非感性电阻,寄生电感,IG-S,高频点火",
         title_en="Why High-End Ignition Coils Use Non-Inductive Resistors: Inductance at High Frequency",
         hook="普通电阻在高频下其实是个小电感——高端点火线圈要的是「纯阻」。",
         hook_en="At high frequency, a normal resistor is really a small inductor — high-end coils need pure resistance.",
         pain=["高频下寄生电感劣化性能", "火花能量被电感吃掉", "EMI 高频段更难压"],
         params=[("寄生电感", "<0.1μH", "IG-S 实心无感"), ("耐压", "40kV", "高压点火"), ("耐温", "350℃", "高温稳定"), ("结构", "陶瓷实心非绕线", "无感原理")],
         formula="阻抗 Z = R + jωL；高频下 ωL 项不可忽略",
         scenarios=[("赛车点火", "高频高能", "IG-S 无感"), ("高端 OEM", "EMI 严苛", "IG-S 实心"), ("高频电源", "阻尼振铃", "IG-S 无感")],
         myths=["绕线电阻没有电感（有寄生电感）", "无感电阻没用（高频差异明显）", "电感对点火没影响（影响火花波形）"],
         tags_cn=["无感", "高频", "IG-S"], tags_en=["#NonInductive", "#HighFrequency", "#IgnitionCoil"],
         points_en=["Z = R + jωL — inductance matters at HF", "IG-S solid ceramic: <0.1μH parasitic", "Non-wound construction eliminates inductance", "Cleaner spark waveform + lower HF EMI"]),

    dict(num="15", slug="article_storage_bleeder_1500v", product="HVW",
         title="储能电池簇的高压泄放电阻：1500V 平台的安全设计与标准要求",
         desc="储能电池簇 1500V 平台高压泄放电阻安全设计：IEC 62477 要求、泄放时间计算、绝缘耐压与功率选型，附 HVW 方案。",
         kw="储能泄放电阻,1500V平台,电池簇泄放,IEC 62477,HVW电阻",
         title_en="Energy Storage Bleeder Resistors: 1500V Platform Safety Design & Standards",
         hook="1500V 储能系统检修前要放电，泄放电阻选不好，要么放得慢要么烧掉。",
         hook_en="Before servicing a 1500V ESS, you must bleed the bus — a bad bleeder is either too slow or burns out.",
         pain=["泄放时间不达标", "1500V 高压耐压不足", "安全标准不熟"],
         params=[("平台电压", "1500V DC", "高压储能"), ("泄放时间", "<5 分钟", "安全标准要求"), ("耐压", "10kV+", "HVW 满足"), ("标准", "IEC 62477", "安全合规")],
         formula="泄放时间 t = RC · ln(V0/Vt)；需 < 5 分钟",
         scenarios=[("电池簇", "1500V 平台", "HVW 高压泄放"), ("PCS 母线", "大电容", "HVW 大功率"), ("检修放电", "安全放电", "HVW 快速泄放")],
         myths=["泄放越快越好（会过热）", "普通电阻可耐 1500V（需专用高压）", "泄放电阻功率不用大（放电能量大）"],
         tags_cn=["储能", "泄放电阻", "1500V"], tags_en=["#EnergyStorage", "#BleederResistor", "#1500V"],
         points_en=["Bleed < 5 min per IEC 62477", "10kV+ withstand for 1500V platforms", "t = RC·ln(V0/Vt) sets the bleeder", "HVW handles high pulse energy safely"]),

    dict(num="16", slug="article_rohs_reach_compliance", product="全线",
         title="点火线圈抑制电阻的 RoHS/REACH 合规报告怎么看？出口必备知识",
         desc="抑制电阻出口 RoHS/REACH 合规要点：报告怎么看、限制物质阈值、常见不合规项与供应商审查清单，及 HXO 合规资质。",
         kw="RoHS,REACH,电阻出口合规,抑制电阻认证,汽车电子合规",
         title_en="How to Read RoHS/REACH Reports for Ignition Resistors: Export Essentials",
         hook="货到海关被扣？RoHS/REACH 报告看不懂，出口就是裸奔。",
         hook_en="Shipment held at customs? Can't read a RoHS/REACH report and you're flying blind on export.",
         pain=["看不懂合规报告", "不清楚限制物质阈值", "供应商资质难审查"],
         params=[("RoHS", "Pb/Cd/Hg/Cr6+/PBB/PBDE", "10 项限制物质"), ("REACH", "SVHC 高关注物质", "需声明"), ("阈值", "Cd 0.01% 其余 0.1%", "均质材料"), ("报告", "第三方检测 + 声明", "供应商审查")],
         formula="合规：均质材料中限制物质 ≤ 阈值；SVHC 需披露",
         scenarios=[("出口欧盟", "RoHS/REACH", "HXO 全项合规"), ("汽车电子", "ELV 指令", "无铅焊端"), ("供应链审查", "资质审核", "第三方报告")],
         myths=["有报告就一定合规（要看检测范围）", "RoHS 和 REACH 是一回事（不同）", "样品过就行（要均质材料）"],
         tags_cn=["RoHS", "REACH", "出口合规"], tags_en=["#RoHS", "#REACH", "#Compliance"],
         points_en=["RoHS 10 substances; REACH SVHC disclosure", "Cd 0.01% / others 0.1% at homogeneous material", "Third-party test + declaration required", "HXO ships full-compliance, lead-free terminations"]),

    dict(num="17", slug="article_welder_bleeder_resistor", product="HVW",
         title="焊机/逆变焊机中的泄放电阻与制动电阻选型要点",
         desc="焊机与逆变焊机中泄放电阻、制动电阻选型：高脉冲、高占空比、散热挑战下的功率与阻值计算，附 HVW 应用案例。",
         kw="焊机泄放电阻,逆变焊机制动电阻,HVW电阻,大功率电阻",
         title_en="Bleeder & Braking Resistor Selection for Welding Machines",
         hook="逆变焊机电容大、脉冲狠，泄放和制动电阻选不对，分分钟过热烧毁。",
         hook_en="Inverter welders have big caps and harsh pulses — wrong bleeder/braking resistor overheats fast.",
         pain=["高脉冲下电阻易烧", "占空比高、散热难", "大功率选型没头绪"],
         params=[("阻值", "按母线电压/泄放时间", "过小电流大"), ("功率", "1W~50W", "HVW 大功率"), ("耐脉冲", "5kJ+", "焊接脉冲"), ("散热", "铝壳/风冷", "高占空比必备")],
         formula="P = U²/R；脉冲工况按占空比折算平均功率",
         scenarios=[("逆变焊机", "高频脉冲", "HVW 耐脉冲"), ("储能焊", "大能量", "HVW 大功率"), ("等离子切割", "高压", "HVW 高压")],
         myths=["用普通电阻凑合（耐脉冲不够）", "只看功率不看耐压", "泄放电阻随便放（散热要设计）"],
         tags_cn=["焊机", "泄放电阻", "HVW"], tags_en=["#Welding", "#BleederResistor", "#Inverter"],
         points_en=["Inverter welders demand pulse-rated resistors", "Size for duty cycle, not just peak", "HVW: 5kJ+ pulse, 10kV+ withstand", "Thermal design is non-negotiable"]),

    dict(num="18", slug="article_thermal_fuse_temperatures", product="RXF",
         title="温度保险电阻的保持温度、动作温度、极限温度到底怎么理解？",
         desc="温度保险电阻三大温度参数解读：保持温度、动作温度、极限温度的定义、测试方法与选型裕度，附 RXF 1W 221℃ 实例。",
         kw="温度保险电阻,保持温度,动作温度,极限温度,RXF",
         title_en="Holding vs Acting vs Limit Temperature: Making Sense of Thermal-Fuse Specs",
         hook="保持温度、动作温度、极限温度傻傻分不清？选错一个，保护就是摆设。",
         hook_en="Holding vs acting vs limit temperature — get one wrong and your protection is decorative.",
         pain=["三个温度概念混淆", "选型裕度拿不准", "动作温度与实际不符"],
         params=[("保持温度", "正常工作不动作", "须高于工作温"), ("动作温度", "221℃（RXF）", "超此熔断"), ("极限温度", "不损坏的上限", "短时耐受"), ("选型裕度", "留 20~30%", "防止误动作")],
         formula="选型：动作温度 ≥ 最高工作温 + 裕度；保持温度 > 额定工作温",
         scenarios=[("充电器", "工作温 100℃级", "动作 221℃ 留裕度"), ("LED 驱动", "高温密闭", "RXF 精准动作"), ("小家电", "异常过热", "RXF 熔断保护")],
         myths=["动作温度=工作温度（错，要留裕度）", "保持温度越低越好（会误动作）", "极限温度随便超（会永久损坏）"],
         tags_cn=["温度保险", "RXF", "参数解读"], tags_en=["#ThermalFuse", "#RXF", "#Specs"],
         points_en=["Holding: won't trip below this", "Acting: trips at this (RXF 221℃)", "Limit: short-term survival ceiling", "Leave 20–30% margin to avoid nuisance trips"]),

    dict(num="19", slug="article_moto_retrofit_suppressor", product="IG-C / IG-F",
         title="摩托车改装：改点火线圈时抑制电阻怎么配？常见误区与实测",
         desc="摩托车改点火线圈时的抑制电阻匹配：阻值选择、功率裕量、常见误区（直接去掉电阻、随意换阻值），附改装实测与 IG-C/IG-F 推荐。",
         kw="摩托车改装点火,抑制电阻匹配,改装点火线圈,IG-C,IG-F",
         title_en="Motorcycle Ignition Retrofit: Matching Suppression Resistors (Myths & Tests)",
         hook="改点火线圈直接把抑制电阻拆了？EMI 和 ECU 分分钟教你做人。",
         hook_en="Removing the suppression resistor when retrofitting? EMI and the ECU will punish you.",
         pain=["改装后失火/干扰", "不知阻值怎么配", "拆掉电阻图省事"],
         params=[("阻值", "按原厂线圈匹配", "不可随意换"), ("功率", "留足裕量", "改装高转发热"), ("产品", "IG-C / IG-F", "按振动/成本选"), ("效果", "EMI 抑制+点火稳定", "实测对比")],
         formula="阻值匹配：按线圈特性与 ECU 输入阻抗；功率 ≥ 2× 计算值",
         scenarios=[("换高压线", "阻值要匹配", "IG-C 通用"), ("高振动改装", "抗振需求", "IG-F 玻纤芯"), ("赛道改装", "高转高温", "IG-S 无感")],
         myths=["拆掉电阻动力更强（EMI 乱窜）", "随便换个阻值无所谓（会失火）", "改装件越贵越好（匹配才是关键）"],
         tags_cn=["摩托车改装", "抑制电阻", "匹配"], tags_en=["#Motorcycle", "#Retrofit", "#IgnitionCoil"],
         points_en=["Never delete the suppressor — EMI + ECU issues", "Match resistance to coil & ECU", "IG-F for vibration, IG-S for track heat", "Keep 2× power margin on modified coils"]),

    dict(num="20", slug="article_custom_resistor_process", product="全线",
         title="定制电阻从打样到量产的完整流程：交期、模具、测试、认证全解析",
         desc="定制电阻完整开发流程：需求沟通、打样、模具、测试、认证到批量交付，附各阶段交期参考与 OEM/ODM 合作要点。",
         kw="定制电阻,电阻打样,OEM电阻,ODM电阻,定制流程",
         title_en="Custom Resistor from Prototype to Mass Production: Lead Time, Tooling, Test, Certification",
         hook="定制电阻要多久？从需求到量产，每个阶段的坑和时间点一次讲清。",
         hook_en="How long does a custom resistor take? Every stage from spec to mass production, with lead times.",
         pain=["交期心里没数", "模具/测试流程不熟", "OEM/ODM 合作怕踩坑"],
         params=[("打样", "7~15 天", "快速样件"), ("模具", "视结构", "专用模周期"), ("测试", "100% 全检", "耐压/温漂/寿命"), ("认证", "CQC/UL", "出口合规")],
         formula="交付 = 需求确认 → 打样 → 模具 → 小批 → 认证 → 量产",
         scenarios=[("新项目打样", "快速验证", "7~15 天样件"), ("OEM 代工", "按图定制", "全流程托管"), ("ODM 设计", "方案定制", "选型+设计")],
         myths=["定制一定很慢（打样可 7~15 天）", "小批量不值得定制（灵活起订）", "认证是客户的事（供应商可代办）"],
         tags_cn=["定制", "OEM", "ODM"], tags_en=["#CustomResistor", "#OEM", "#ODM"],
         points_en=["Prototype in 7–15 days", "100% testing: withstand, TCR, life", "CQC/UL for export compliance", "Flexible MOQ for small batches"]),
]

_TOPIC_BY_NUM = {t["num"]: t for t in TOPICS}
_TOPIC_BY_SLUG = {t["slug"]: t for t in TOPICS}


def spec_by_num(num: str):
    return _TOPIC_BY_NUM.get(str(num))


def spec_by_slug(slug: str):
    return _TOPIC_BY_SLUG.get(slug)


def _cta_key(product: str) -> str:
    for k in ("IG-C", "IG-F", "IG-S", "RXF", "HVW"):
        if k in product:
            return k
    return "IG-C"


# ---------------------------------------------------------------------------
# Hashtag 生成
# ---------------------------------------------------------------------------
def gen_hashtags(spec, lang="en", count=None):
    tags = spec.get("tags_en") if lang == "en" else spec.get("tags_cn")
    tags = tags or []
    if count:
        tags = tags[:count]
    return tags


# ---------------------------------------------------------------------------
# 中文长文正文（差异化）
# ---------------------------------------------------------------------------
def build_cn_body(spec):
    cta = PRODUCT_CTA[_cta_key(spec["product"])]
    pain_items = "\n".join(f"- {p}" for p in spec["pain"])
    rows = "\n".join(
        f'    <tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>'
        for a, b, c in spec["params"]
    )
    scen_rows = "\n".join(
        f'    <tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>'
        for a, b, c in spec["scenarios"]
    )
    myths = "\n".join(f"- {m}" for m in spec["myths"])

    return f"""## 引言

{spec['hook']}

{spec['desc']}

本文面向工程师与采购，围绕「{spec['title']}」给出可落地的依据、计算方法与实测参考，适用于 {spec['product']} 产品线。

:::raw
<div class="highlight-box">
    <h4>核心结论</h4>
    <ul>
{pain_items}
        <li>关键参数以实际工况为准，而非仅看标称值</li>
        <li>HXO {_cta_key(spec['product'])} 系列出厂 100% 测试，可提供样品与测试报告</li>
    </ul>
</div>
:::

## 一、关键参数与选型依据

:::raw
<div class="table-wrap">
<table>
    <tr><th>参数</th><th>典型值/范围</th><th>选型要点</th></tr>
{rows}
</table>
</div>
:::

## 二、计算方法

:::raw
<div class="formula-box">
    <h4>核心公式</h4>
    <p>{spec['formula']}</p>
</div>
:::

## 三、典型场景对照

:::raw
<div class="table-wrap">
<table>
    <tr><th>场景</th><th>关键约束</th><th>推荐方案</th></tr>
{scen_rows}
</table>
</div>
:::

## 四、常见误区

{myths}

:::raw
<div class="cta-section">
    <h3>{cta['cn'][0]}</h3>
    <p>{cta['cn'][1]}</p>
    <a href="mailto:{CONTACT}?subject={spec['title']}咨询" class="cta-btn">获取选型方案</a>
</div>
:::

## 相关阅读

- [选型指南](./selection-guide.html)
- [产品对比](./comparison.html)
- [技术参数](./specifications.html)
"""
    + (f"- [HVW 高阻值绕线电阻](./hvw-resistor.html)\n" if _cta_key(spec["product"]) == "HVW" else "")


# ---------------------------------------------------------------------------
# 海外英文文案
# ---------------------------------------------------------------------------
def build_en_linkedin(spec):
    cta = PRODUCT_CTA[_cta_key(spec["product"])]
    points = "\n".join(f"• {p}" for p in spec["points_en"])
    tags = " ".join(gen_hashtags(spec, "en", 5))
    return f"""{spec['hook_en']}

{spec['title_en']}

{points}

{cta['en'][1]}.

Contact: {CONTACT} | {SITE}
{tags}"""


def build_en_x(spec):
    tags = " ".join(gen_hashtags(spec, "en", 3))
    body = f"{spec['hook_en']} {SITE}/{spec['slug']}.html {tags}"
    if len(body) > 280:
        body = f"{spec['hook_en'][:220]}... {SITE}/{spec['slug']}.html {tags}"
    return body


def build_zhihu(spec):
    """国内知乎：长文、工程师视角、去硬广、保留技术结论。"""
    pain_items = "\n".join(f"- {p}" for p in spec["pain"])
    myths = "\n".join(f"- {m}" for m in spec["myths"])
    return f"""{spec['hook']}

{spec['desc']}

## 先说结论

{pain_items}

## 关键参数

{chr(10).join(f"- {a}：{b}（{c}）" for a, b, c in spec["params"])}

## 计算方法

{spec['formula']}

## 常见误区

{myths}

（本文基于 HXO 电阻产品线的工程实测整理，欢迎交流。）"""


def build_wechat(spec):
    """国内微信公众号：草稿用 HTML 长文（标题 + 摘要 + 正文）。"""
    cta = PRODUCT_CTA[_cta_key(spec["product"])]
    pain = "".join(f"<li>{p}</li>" for p in spec["pain"])
    params = "".join(f"<li><b>{a}</b>：{b}（{c}）</li>" for a, b, c in spec["params"])
    myths = "".join(f"<li>{m}</li>" for m in spec["myths"])
    content = (
        f"<h2>{spec['hook']}</h2>"
        f"<p>{spec['desc']}</p>"
        f"<h3>核心结论</h3><ul>{pain}</ul>"
        f"<h3>关键参数</h3><ul>{params}</ul>"
        f"<h3>计算方法</h3><p>{spec['formula']}</p>"
        f"<h3>常见误区</h3><ul>{myths}</ul>"
        f"<p>{cta['cn'][1]}｜官网：{SITE}/{spec['slug']}.html</p>"
    )
    return {
        "title": spec["title"],
        "digest": spec["desc"][:120],
        "content": content,
    }


# ---------------------------------------------------------------------------
# 统一社交内容导出
# ---------------------------------------------------------------------------
def _en_bundle(spec):
    """英文文案来源：配好 DeepSeek key 时走翻译，否则回退手写英文字段。"""
    if translate.is_configured():
        t = lambda x: translate.translate(x, "en")
        return {
            "title_en": t(spec["title"]),
            "hook_en": t(spec["hook"]),
            "desc_en": t(spec["desc"]),
            "points_en": [t(p) for p in spec["pain"]],
        }
    return {
        "title_en": spec.get("title_en", spec["title"]),
        "hook_en": spec.get("hook_en", spec["hook"]),
        "desc_en": spec.get("desc_en", spec.get("desc", "")),
        "points_en": spec.get("points_en", [p for p in spec["pain"]]),
    }


def build_social(spec):
    s = dict(spec)
    s.update(_en_bundle(spec))
    return {
        "slug": s["slug"],
        "title_cn": spec["title"],
        "title_en": s["title_en"],
        "zhihu": build_zhihu(spec),
        "wechat": build_wechat(spec),
        "linkedin": build_en_linkedin(s),
        "x": build_en_x(s),
        "hashtags_en": gen_hashtags(s, "en", 5),
        "hashtags_cn": spec.get("tags_cn", []),
    }


def write_social(spec):
    SOCIAL_DIR.mkdir(parents=True, exist_ok=True)
    data = build_social(spec)
    path = SOCIAL_DIR / f"{spec['slug']}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_social(slug):
    path = SOCIAL_DIR / f"{slug}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# 生成完整中文文章 md（复用原 shell 模板）
# ---------------------------------------------------------------------------
def build_article_md(spec):
    slug = spec["slug"]
    title = spec["title"]
    desc = spec["desc"]
    kw = spec["kw"]
    today = dt.date.today().isoformat()
    canonical = f"{SITE}/{slug}.html"

    tpl = TEMPLATE.read_text(encoding="utf-8")
    tpl_slug = "article_pv_storage_bleeder"
    tpl_title = re.search(r"(?m)^title:\s*(.+)$", tpl).group(1).strip()
    tpl_desc = re.search(r"(?m)^description:\s*(.+)$", tpl).group(1).strip()
    tpl_kw = re.search(r"(?m)^keywords:\s*(.+)$", tpl).group(1).strip()

    out = tpl
    out = out.replace(f"filename_slug: {tpl_slug}", f"filename_slug: {slug}")
    out = out.replace(f"title: {tpl_title}", f'title: "{title}"')
    out = out.replace(f"description: {tpl_desc}", f'description: "{desc}"')
    out = out.replace(f"keywords: {tpl_kw}", f'keywords: "{kw}"')
    out = out.replace(f"canonical: {canonical.replace(slug, tpl_slug)}", f"canonical: {canonical}")
    out = out.replace(f"date: 2026-10-09", f"date: {today}")
    out = out.replace(f"<title>{tpl_title}</title>", f"<title>{title} - HXO Resistor</title>")
    out = out.replace(tpl_desc, desc)
    out = out.replace(tpl_kw, kw)
    out = out.replace(canonical.replace(slug, tpl_slug), canonical)
    out = out.replace(f'"headline": "{tpl_title}"', f'"headline": "{title} - HXO Resistor"')
    out = out.replace(f'"datePublished": "2026-10-09"', f'"datePublished": "{today}"')
    out = out.replace("发布时间：2026-10-09", f"发布时间：{today}")

    body_start = out.find("\n---\n", out.find("shell_tail:"))
    if body_start == -1:
        raise RuntimeError("模板 body 分隔符未找到")
    head = out[:body_start]
    body = build_cn_body(spec)
    return head + "\n---\n\n" + body + "\n", slug


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="内容工厂：预览/导出差异化中英内容")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--slug")
    args = ap.parse_args()

    if args.list:
        for t in TOPICS:
            print(f"#{t['num']}  {t['slug']}  [{t['product']}]  {t['title']}")
        return

    if args.slug:
        spec = spec_by_slug(args.slug)
        if not spec:
            raise SystemExit(f"未找到 slug: {args.slug}")
        s = build_social(spec)
        print("=" * 70)
        print(f"[中文标题] {spec['title']}")
        print(f"[英文标题] {spec['title_en']}")
        print("=" * 70)
        print("[LinkedIn EN]")
        print(s["linkedin"])
        print("\n[X EN]")
        print(s["x"])
        print("\n[知乎 CN]")
        print(s["zhihu"])
        print("\n[小红书 CN]")
        print(s["xiaohongshu"])
        return

    ap.print_help()


if __name__ == "__main__":
    main()

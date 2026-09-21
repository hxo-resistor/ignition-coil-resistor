import os

BASE_HEAD = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{meta_desc}">
    <title>{title}</title>
    <link rel="sitemap" type="application/xml" href="https://hxo-resistor.github.io/ignition-coil-resistor/sitemap.xml">
    {schema_html}
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; color: #1a1a2e; line-height: 1.6; background: #fff; }}
        .container {{ max-width: 1100px; margin: 0 auto; padding: 0 20px; }}
        nav {{ background: #1a1a2e; position: sticky; top: 0; z-index: 100; padding: 12px 0; }}
        .nav-inner {{ max-width: 1100px; margin: 0 auto; padding: 0 20px; display: flex; justify-content: space-between; align-items: center; }}
        .nav-logo {{ color: #fff; font-size: 1.5em; font-weight: 800; text-decoration: none; letter-spacing: 1px; }}
        .nav-logo span {{ color: #e94560; }}
        .nav-links {{ display: flex; gap: 6px; list-style: none; }}
        .nav-links a {{ color: #ccc; text-decoration: none; font-size: 0.85em; padding: 8px 14px; border-radius: 6px; transition: 0.2s; white-space: nowrap; }}
        .nav-links a:hover {{ color: #fff; background: rgba(233, 69, 96, 0.15); }}
        .nav-links a.active {{ color: #e94560; background: rgba(233, 69, 96, 0.12); }}
        @media (max-width: 768px) {{ .nav-links {{ display: none; position: absolute; top: 64px; left: 0; right: 0; background: #1a1a2e; flex-direction: column; padding: 12px; gap: 2px; }} .nav-links.open {{ display: flex; }} .nav-toggle {{ display: block; }} }}
        .nav-toggle {{ display: none; background: none; border: none; color: #fff; font-size: 1.5em; cursor: pointer; }}
        .page-hero {{ background: linear-gradient(135deg, #1a1a2e 0%, {hero_color} 100%); padding: 60px 0 50px; text-align: center; }}
        .page-hero h1 {{ font-size: 2.2em; color: #fff; margin-bottom: 12px; }}
        .page-hero .subtitle {{ color: rgba(255,255,255,0.85); font-size: 1.1em; max-width: 700px; margin: 0 auto; }}
        .page-hero .badge {{ display: inline-block; background: {badge_color}; color: #fff; padding: 4px 16px; border-radius: 20px; font-size: 0.85em; font-weight: 600; margin-top: 16px; }}
        .section {{ padding: 50px 0; }}
        .section-title {{ font-size: 1.5em; margin-bottom: 24px; color: #0f3460; }}
        .section-label {{ color: #e94560; font-size: 0.75em; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; }}
        .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
        @media (max-width: 768px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}
        .grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }}
        @media (max-width: 768px) {{ .grid-3 {{ grid-template-columns: 1fr; }} }}
        .feature-card {{ background: #f8f9fa; border-radius: 12px; padding: 24px; border: 1px solid #eee; }}
        .feature-card .icon {{ font-size: 2em; margin-bottom: 8px; }}
        .feature-card h3 {{ font-size: 1.1em; margin-bottom: 8px; color: #0f3460; }}
        .feature-card ul {{ padding-left: 18px; }}
        .feature-card li {{ margin-bottom: 4px; font-size: 0.95em; color: #444; }}
        .param-table {{ width: 100%; border-collapse: collapse; margin: 16px 0 24px; font-size: 0.9em; }}
        .param-table th {{ background: #0f3460; color: #fff; padding: 10px 14px; text-align: left; }}
        .param-table td {{ padding: 10px 14px; border-bottom: 1px solid #eee; }}
        .param-table tr:hover {{ background: #f5f5f5; }}
        .btn {{ display: inline-block; padding: 10px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 0.9em; transition: 0.2s; }}
        .btn-primary {{ background: #e94560; color: #fff; }}
        .btn-outline {{ border: 2px solid #e94560; color: #e94560; }}
        .btn-sm {{ padding: 8px 16px; font-size: 0.83em; }}
        .cta {{ background: linear-gradient(135deg, #1a1a2e, #16213e); color: #fff; text-align: center; padding: 50px 20px; }}
        .cta h2 {{ font-size: 1.5em; margin-bottom: 12px; }}
        .cta p {{ color: rgba(255,255,255,0.7); margin-bottom: 20px; }}
        .footer {{ background: #1a1a2e; color: #888; text-align: center; padding: 30px 20px; font-size: 0.85em; }}
        .footer a {{ color: #aaa; text-decoration: none; margin: 0 12px; }}
        .footer a:hover {{ color: #e94560; }}
        .back-link {{ text-align: center; margin: 30px 0; }}
        .back-link a {{ color: #e94560; text-decoration: none; }}
        .cert-badges {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }}
        .cert-badge {{ background: #0f3460; color: #fff; padding: 4px 12px; border-radius: 4px; font-size: 0.8em; }}
        .faq-section {{ margin-top: 30px; }}
        .faq-item {{ background: #f8f9fa; border-radius: 10px; padding: 20px; margin-bottom: 12px; border: 1px solid #eee; }}
        .faq-item h3 {{ font-size: 1em; color: #0f3460; margin-bottom: 8px; }}
        .faq-item p {{ font-size: 0.93em; color: #555; }}
    </style>
</head>
<body>
<nav>
    <div class="nav-inner">
        <a href="index.html" class="nav-logo">HXO<span>.</span></a>
        <button class="nav-toggle" onclick="document.querySelector('.nav-links').classList.toggle('open')">☰</button>
        <ul class="nav-links">
            <li><a href="index.html">首页</a></li>
            <li><a href="ig-c.html" class="active">{nav_igc}</a></li>
            <li><a href="ig-f.html">{nav_igf}</a></li>
            <li><a href="ig-s.html">{nav_igs}</a></li>
            <li><a href="articles.html">技术文章</a></li>
            <li><a href="faq.html">常见问题</a></li>
            <li><a href="index.html#docs">技术文档</a></li>
            <li><a href="index.html#inquiry">询价/联系</a></li>
        </ul>
    </div>
</nav>
'''

FOOTER = '''
<div class="cta">
    <h2>立即获取专业报价</h2>
    <p>告诉我们您的需求，我们将在 24 小时内提供专业的技术方案和报价</p>
    <div class="btn-group" style="text-align:center;">
        <a href="mailto:resistor@hxo-lcr.cn?subject=HXO%20Resistor%20询价" class="btn btn-primary" style="margin:0 6px;">📧 发送邮件询价</a>
        <a href="tel:+8613510200650" class="btn btn-outline" style="margin:0 6px;">📞 拨打电话</a>
    </div>
</div>
<div class="footer">
    <div class="footer-links" style="text-align:center;margin-bottom:12px;">
        <a href="https://www.hxo-lcr.cn" target="_blank">官网</a>
        <a href="mailto:resistor@hxo-lcr.cn">resistor@hxo-lcr.cn</a>
    </div>
    <p>© 2026 HXO Resistor / 华星欧电子（深圳）有限公司 — 专注点火线圈抑制电阻</p>
</div>
<script>
document.querySelectorAll('.nav-links a').forEach(link => {
    link.addEventListener('click', () => { document.querySelector('.nav-links')?.classList.remove('open'); });
});
</script>
</body>
</html>'''

SERIES = [
    {
        "name": "IG-C",
        "full_name": "IG-C 陶瓷芯绕线型",
        "tag": "🌟 性价比之选 · 标准应用",
        "hero_color": "#16213e",
        "badge_color": "#e94560",
        "nav_igc": "IG-C",
        "nav_igf": "IG-F",
        "nav_igs": "IG-S",
        "meta_desc": "HXO IG-C陶瓷芯绕线型点火线圈抑制电阻，脉冲耐压30kV，工作温度-55°C~+275°C，阻值1kΩ~20kΩ，AEC-Q200认证，7-15天交付。",
        "title": "IG-C 陶瓷芯绕线型点火线圈抑制电阻 | HXO Resistor",
        "schema": '''
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "Product",
      "name": "IG-C 陶瓷芯绕线型点火线圈抑制电阻",
      "brand": {"@type": "Brand", "name": "HXO Resistor"},
      "description": "IG-C陶瓷芯绕线型抑制电阻，通用型性价比之选，脉冲耐压30kV，工作温度-55°C~+275°C，AEC-Q200标准级认证",
      "category": "Automotive Ignition Resistor",
      "mpn": "IG-C Series",
      "material": "高纯氧化铝陶瓷芯骨架（Al₂O₃≥96%）",
      "application": "通用摩托车点火线圈、汽车点火线圈维修替换、售后市场",
      "additionalProperty": [
        {"@type": "PropertyValue", "name": "阻值范围", "value": "1kΩ~20kΩ"},
        {"@type": "PropertyValue", "name": "额定功率", "value": "1W~15W"},
        {"@type": "PropertyValue", "name": "脉冲耐压", "value": "30kV"},
        {"@type": "PropertyValue", "name": "工作温度", "value": "-55°C~+275°C"},
        {"@type": "PropertyValue", "name": "TCR", "value": "±100~±300 ppm/°C"},
        {"@type": "PropertyValue", "name": "绝缘电阻", "value": "≥1,000 MΩ"}
      ],
      "hasCertification": [
        {"@type": "EducationalOccupationalCredential", "name": "AEC-Q200 Standard Grade"},
        {"@type": "EducationalOccupationalCredential", "name": "RoHS"},
        {"@type": "EducationalOccupationalCredential", "name": "REACH"}
      ]
    }
    </script>
''',
        "intro_title": "标准主力 · 性价比之选",
        "intro_text": "IG-C 系列采用高纯氧化铝陶瓷芯骨架（Al₂O₃≥96%）绕线工艺，在性能、可靠性和成本之间取得最佳平衡，是摩托车和汽车点火线圈应用中最通用的系列。脉冲耐压 30kV，工作温度 -55°C~+275°C，覆盖绝大多数民用点火系统需求。",
        "params_list": ["阻值范围：1kΩ ~ 20kΩ（最常用 4.7kΩ/5.1kΩ/10kΩ）","额定功率：1W / 3W / 5W / 7W / 10W / 15W","脉冲耐压：30kV（峰值，1.2/50μs 标准雷电冲击波）","温度系数：±100 ~ ±300 ppm/°C","高温负载寿命：275°C / 1000h / 阻值变化 ≤ ±2%"],
        "table_rows": [
            ("标称阻值范围","1kΩ ~ 20kΩ","E系列标准值，非标可定制"),
            ("最常用阻值","4.7kΩ / 5.1kΩ / 10kΩ","摩托车/日系车/电喷车"),
            ("额定功率","1W / 3W / 5W / 7W / 10W / 15W","25°C 环境温度下"),
            ("最高脉冲耐压","30kV（峰值）","1.2/50μs 标准雷电冲击波"),
            ("连续工作电压","最高 28kV","AC/DC"),
            ("工作温度范围","-55°C ~ +275°C","存储：-55°C ~ +300°C"),
            ("温度系数 (TCR)","±100 ~ ±300 ppm/°C","中阻值段最稳定"),
            ("公差等级","J(±5%) / K(±10%) / M(±20%)","推荐 K 级"),
            ("绝缘电阻","≥1,000 MΩ (500V DC)","湿热后 ≥100 MΩ"),
            ("寄生电感","1~5 μH","绕线结构固有"),
        ],
        "apps": [
            ("🏍️ 摩托车应用","<li>3W / 4.7kΩ~10kΩ / ±10%</li><li>城市通勤·越野·赛车</li><li>最常用组合，性价比最优</li>"),
            ("🚗 汽车应用","<li>5W / 5kΩ~10kΩ / ±10%</li><li>发动机舱高温环境稳定运行</li><li>30kV 脉冲耐压满足严苛工况</li>"),
            ("⚡ 工业应用","<li>10W / 5kΩ~15kΩ / ±10%</li><li>15,000~25,000 小时连续工作寿命</li><li>高抗振，极端环境适应</li>"),
        ],
        "faqs": [
            ("IG-C系列适用哪些车型？","IG-C是通用型陶瓷芯绕线抑制电阻，覆盖主流摩托车（本田、雅马哈、铃木、川崎、宗申、隆鑫、力帆等）和汽车点火线圈维修替换市场。次级阻值4.7kΩ~10kΩ，初级阻值0.5Ω~1.5Ω。"),
            ("IG-C的AEC-Q200认证等级是什么？","IG-C系列通过AEC-Q200标准级认证，经过高温寿命测试（125°C，1000h）、温度循环（-55°C~+155°C，1000次）、湿度偏压、振动冲击等20+项应力测试。可提供第三方检测报告。"),
            ("IG-C的最小起订量是多少？","样品订单无MOQ，1颗起发。批量订单常规型号1000颗起订，定制型号需协商。免费提供5颗样品，运费到付，附完整测试报告。"),
        ]
    },
    {
        "name": "IG-F",
        "full_name": "IG-F 玻纤芯绕线型",
        "tag": "💪 经济型 · 高抗振",
        "hero_color": "#1a1a2e",
        "badge_color": "#e67e22",
        "nav_igc": "IG-C",
        "nav_igf": "IG-F",
        "nav_igs": "IG-S",
        "meta_desc": "HXO IG-F玻纤芯绕线型点火线圈抑制电阻，经济型高抗振方案，脉冲耐压25kV，抗振性比陶瓷芯高30%，AEC-Q200认证，7-15天交付。",
        "title": "IG-F 玻纤芯绕线型点火线圈抑制电阻 | HXO Resistor",
        "schema": '''
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "Product",
      "name": "IG-F 玻纤芯绕线型点火线圈抑制电阻",
      "brand": {"@type": "Brand", "name": "HXO Resistor"},
      "description": "IG-F玻纤芯绕线型抑制电阻，经济型高抗振方案，脉冲耐压25kV，抗振性比陶瓷芯高30%，AEC-Q200标准级认证",
      "category": "Automotive Ignition Resistor",
      "mpn": "IG-F Series",
      "material": "玻纤芯（GFRP）骨架绕线",
      "application": "越野摩托车、单缸高振动机型、售后替换市场、通用汽油机",
      "additionalProperty": [
        {"@type": "PropertyValue", "name": "阻值范围", "value": "1kΩ~15kΩ"},
        {"@type": "PropertyValue", "name": "额定功率", "value": "1W~10W"},
        {"@type": "PropertyValue", "name": "脉冲耐压", "value": "25kV"},
        {"@type": "PropertyValue", "name": "工作温度", "value": "-55°C~+155°C"},
        {"@type": "PropertyValue", "name": "TCR", "value": "±200~±500 ppm/°C"},
        {"@type": "PropertyValue", "name": "抗振性", "value": "比陶瓷芯高30%"}
      ],
      "hasCertification": [
        {"@type": "EducationalOccupationalCredential", "name": "AEC-Q200 Standard Grade"},
        {"@type": "EducationalOccupationalCredential", "name": "RoHS"},
        {"@type": "EducationalOccupationalCredential", "name": "REACH"}
      ]
    }
    </script>
''',
        "intro_title": "经济型 · 高抗振",
        "intro_text": "IG-F 系列采用玻纤芯（GFRP）骨架绕线工艺，以低于陶瓷芯系列约 30% 的价格提供良好的基本性能。玻纤芯的低弹性模量和高断裂伸长率使其在振动环境下具有天然优势，是售后替换市场和经济型整车配套的首选方案。",
        "params_list": ["阻值范围：1kΩ ~ 15kΩ（最常用 3.3kΩ/4.7kΩ/10kΩ）","额定功率：1W / 3W / 5W / 8W / 10W","脉冲耐压：25kV（峰值，1.2/50μs 标准雷电冲击波）","温度系数：±200 ~ ±500 ppm/°C","振动测试：2.0g，3小时/轴（比 IC-C 更严苛）"],
        "table_rows": [
            ("标称阻值范围","1kΩ ~ 15kΩ","E系列标准值，非标可定制"),
            ("最常用阻值","3.3kΩ / 4.7kΩ / 10kΩ","小排量/通用/电喷经济型"),
            ("额定功率","1W / 3W / 5W / 8W / 10W","25°C 环境温度下"),
            ("最高脉冲耐压","25kV（峰值）","1.2/50μs 标准雷电冲击波"),
            ("连续工作电压","最高 20kV","AC/DC"),
            ("工作温度范围","-55°C ~ +155°C","存储：-55°C ~ +185°C"),
            ("温度系数 (TCR)","±200 ~ ±500 ppm/°C","中阻值段最稳定"),
            ("公差等级","K(±10%) / M(±20%)","不提供 J 级 ±5%"),
            ("绝缘电阻","≥500 MΩ (500V DC)","湿热后 ≥50 MΩ"),
            ("抗弯强度","≥200 MPa","玻纤芯韧性优异"),
        ],
        "apps": [
            ("🏍️ 经济型摩托车","<li>3W / 4.7kΩ / ±20% 最低成本</li><li>小排量踏板车优选</li><li>抗振性能优于陶瓷芯</li>"),
            ("🔧 售后替换市场","<li>3W / 4.7kΩ~10kΩ / ±20%</li><li>通用替换，兼容性强</li><li>比原厂性价比更高</li>"),
            ("🌿 通用汽油机","<li>3W~5W / 4.7kΩ~10kΩ</li><li>割草机、油锯等</li><li>轻便、高抗振、成本低</li>"),
        ],
        "faqs": [
            ("IG-F系列相比IG-C的主要优势是什么？","IG-F最大优势是抗振性——玻纤芯的弹性模量低、断裂伸长率高，比陶瓷芯抗振性高30%。价格比IG-C低约30%，适合振动大的越野摩托车、单缸发动机和售后替换市场。"),
            ("IG-F的交期和MOQ是怎样的？","IG-F与IG-C共享产线，标准交期7-15天。样品1颗起发，免费5颗样品。批量常规型号1000颗起订，定制型号可协商。"),
            ("IG-F的AEC-Q200认证和IG-C一样吗？","是的，IG-F同样通过AEC-Q200标准级认证，经过高温寿命、温度循环、湿度偏压、振动冲击等20+项应力测试。可提供第三方检测报告原件。"),
        ]
    },
    {
        "name": "IG-S",
        "full_name": "IG-S 陶瓷实心型",
        "tag": "🏆 旗舰性能 · 极端环境",
        "hero_color": "#0a0a1a",
        "badge_color": "#e94560",
        "nav_igc": "IG-C",
        "nav_igf": "IG-F",
        "nav_igs": "IG-S",
        "meta_desc": "HXO IG-S陶瓷实心型点火线圈抑制电阻，旗舰性能，脉冲耐压40kV，工作温度-55°C~+350°C，寄生电感<0.1μH，AEC-Q200完整级认证。",
        "title": "IG-S 陶瓷实心型点火线圈抑制电阻 | HXO Resistor",
        "schema": '''
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "Product",
      "name": "IG-S 陶瓷实心型点火线圈抑制电阻",
      "brand": {"@type": "Brand", "name": "HXO Resistor"},
      "description": "IG-S陶瓷实心型抑制电阻，旗舰性能，脉冲耐压40kV，工作温度-55°C~+350°C，寄生电感<0.1μH，AEC-Q200完整级认证",
      "category": "Automotive Ignition Resistor",
      "mpn": "IG-S Series",
      "material": "实心陶瓷基体+薄膜/厚膜工艺，专利陶瓷区域导通技术（CN 113016042 A）",
      "application": "赛车、极端高温环境、涡轮增压发动机、军用/航空级需求",
      "additionalProperty": [
        {"@type": "PropertyValue", "name": "阻值范围", "value": "1kΩ~20kΩ"},
        {"@type": "PropertyValue", "name": "额定功率", "value": "2W~10W"},
        {"@type": "PropertyValue", "name": "脉冲耐压", "value": "40kV"},
        {"@type": "PropertyValue", "name": "工作温度", "value": "-55°C~+350°C"},
        {"@type": "PropertyValue", "name": "TCR", "value": "-900±300 ppm/°C (NTC)"},
        {"@type": "PropertyValue", "name": "寄生电感", "value": "<0.1 μH"},
        {"@type": "PropertyValue", "name": "绝缘电阻", "value": "≥1,000 MΩ"}
      ],
      "hasCertification": [
        {"@type": "EducationalOccupationalCredential", "name": "AEC-Q200 Full Grade"},
        {"@type": "EducationalOccupationalCredential", "name": "RoHS"},
        {"@type": "EducationalOccupationalCredential", "name": "REACH"},
        {"@type": "EducationalOccupationalCredential", "name": "中国发明专利 CN 113016042 A"}
      ]
    }
    </script>
''',
        "intro_title": "旗舰性能 · 极端环境",
        "intro_text": "IG-S 系列采用陶瓷实心非感性工艺，搭载 HXO 专利陶瓷区域导通技术（Peeling Area Conduction Technology，CN 113016042 A），实现行业领先的 40kV 脉冲耐压、350°C 极限工作温度和 <0.1μH 的寄生电感。面向高性能赛车、涡轮增压汽车、军用/航空和工业极端环境。",
        "params_list": ["阻值范围：1kΩ ~ 20kΩ（最常用 5kΩ~10kΩ）","额定功率：2W / 3W / 5W / 7W / 10W","脉冲耐压：40kV（峰值）— 行业最高","温度系数：-900±300 ppm/°C（NTC 负温度系数）","寄生电感：<0.1 μH（无感，适用 DC~100MHz）"],
        "table_rows": [
            ("标称阻值范围","1kΩ ~ 20kΩ","E系列标准值，非标可定制"),
            ("最常用阻值","5kΩ~10kΩ / 10kΩ~15kΩ","高性能/工业应用"),
            ("额定功率","2W / 3W / 5W / 7W / 10W","25°C 环境温度下"),
            ("最高脉冲耐压","40kV（峰值）","专利陶瓷区域导通技术"),
            ("连续工作电压","最高 28kV","AC/DC"),
            ("工作温度范围","-55°C ~ +350°C","存储：-55°C ~ +400°C"),
            ("温度系数 (TCR)","-900 ± 300 ppm/°C (NTC)","负温度系数，冷启动优势"),
            ("公差等级","K(±10%) / M(±20%)","可筛选 ±5%"),
            ("绝缘电阻","≥1,000 MΩ (500V DC)","高温后 ≥500 MΩ"),
            ("寄生电感","<0.1 μH","无感，宽频纯阻性"),
        ],
        "apps": [
            ("🏎️ 赛车/高性能","<li>7W~10W / 5kΩ~10kΩ</li><li>无感设计提升高转速响应</li><li>40kV 耐压应对极端工况</li>"),
            ("🔥 极端高温","<li>5W~7W / 5kΩ~10kΩ</li><li>350°C 上限，NTC 补偿</li><li>涡轮增压、工业燃烧器</li>"),
            ("⚙️ 高频多点点火","<li>5W~7W / 5kΩ~10kΩ</li><li><0.1μH 无感，无谐振</li><li>军用/航空级可靠性</li>"),
        ],
        "faqs": [
            ("IG-S的AEC-Q200认证等级和IG-C/IG-F有什么不同？","IG-S通过AEC-Q200完整级认证（Full Grade），覆盖全部测试项目，而IG-C/IG-F为标准级认证。IG-S还额外通过350°C极限高温测试和40kV脉冲测试，这是标准级测试不覆盖的严苛条件。"),
            ("IG-S的NTC负温度系数特性有什么好处？","NTC意味着温度升高时阻值降低，正好补偿点火线圈高温下铜线电阻增大的趋势，使整体点火能量更稳定。冷启动时阻值较高，帮助快速建立初始点火能量。"),
            ("IG-S专利技术（CN 113016042 A）是什么？","HXO专利陶瓷区域导通技术（Peeling Area Conduction Technology），通过精密控制陶瓷基体表面导通区域的形状和分布，实现40kV超高脉冲耐压和<0.1μH的超低寄生电感。这是HXO独有的核心技术，使IG-S在性能上对标甚至超越进口旗舰品牌。"),
        ]
    }
]

for s in SERIES:
    # Build page
    html = BASE_HEAD.format(
        meta_desc=s["meta_desc"],
        title=s["title"],
        schema_html=s["schema"],
        hero_color=s["hero_color"],
        badge_color=s["badge_color"],
        nav_igc=s["nav_igc"],
        nav_igf=s["nav_igf"],
        nav_igs=s["nav_igs"]
    )

    # Hero
    html += f'''
<div class="page-hero">
    <div class="container">
        <div class="badge">{s["tag"]}</div>
        <h1>{s["full_name"]}</h1>
        <p class="subtitle">{s["intro_text"][:100]}…</p>
        <div class="cert-badges" style="justify-content:center;">
            <span class="cert-badge">AEC-Q200</span>
            <span class="cert-badge">RoHS</span>
            <span class="cert-badge">REACH</span>
            <span class="cert-badge">ISO 9001</span>
        </div>
        <div style="margin-top:20px;">
            <a href="index.html#inquiry" class="btn btn-primary" style="margin:0 6px;">📧 获取报价</a>
            <a href="./{s['name']}_Datasheet.pdf" class="btn btn-outline" style="margin:0 6px;border-color:#fff;color:#fff;">📄 下载PDF规格书</a>
        </div>
    </div>
</div>
'''

    # Overview
    html += f'''
<div class="section">
    <div class="container">
        <span class="section-label">OVERVIEW</span>
        <h2 class="section-title">产品概述</h2>
        <div class="grid-2">
            <div class="feature-card">
                <div class="icon">🎯</div>
                <h3>{s["intro_title"]}</h3>
                <p>{s["intro_text"]}</p>
            </div>
            <div class="feature-card">
                <div class="icon">⚡</div>
                <h3>核心参数一览</h3>
                <ul>
'''
    for p in s["params_list"]:
        html += f'                    <li>{p}</li>\n'
    html += '''                </ul>
            </div>
        </div>
    </div>
</div>
'''

    # Param table
    html += f'''
<div class="section" style="background:#f8f9fa;">
    <div class="container">
        <span class="section-label">SPECIFICATIONS</span>
        <h2 class="section-title">详细技术参数</h2>
        <table class="param-table">
            <thead><tr><th>参数项</th><th>规格</th><th>备注</th></tr></thead>
            <tbody>
'''
    for row in s["table_rows"]:
        html += f'                <tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td></tr>\n'
    html += '''            </tbody>
        </table>
    </div>
</div>
'''

    # Application scenarios
    html += f'''
<div class="section">
    <div class="container">
        <span class="section-label">APPLICATIONS</span>
        <h2 class="section-title">适用场景</h2>
        <div class="grid-3">
'''
    for app in s["apps"]:
        html += f'            <div class="feature-card"><h3>{app[0]}</h3><ul>{app[1]}</ul></div>\n'
    html += '''        </div>
    </div>
</div>
'''

    # PDF download
    pdf_name = s["name"]
    html += f'''
<div class="section" style="background:#f8f9fa;">
    <div class="container">
        <span class="section-label">DOCUMENTS</span>
        <h2 class="section-title">相关文档</h2>
        <div style="display:flex;flex-wrap:wrap;gap:16px;">
            <div class="feature-card" style="flex:1;min-width:200px;">
                <div class="icon">📊</div>
                <h3>{s["full_name"]} Datasheet</h3>
                <p>完整技术参数，含电气特性、尺寸、降额曲线、寿命数据。</p>
                <a href="./{pdf_name}_Datasheet.pdf" class="btn btn-sm btn-primary" style="margin-top:12px;display:inline-block;" target="_blank">下载 PDF</a>
            </div>
            <div class="feature-card" style="flex:1;min-width:200px;">
                <div class="icon">📋</div>
                <h3>产品目录 / 选型手册</h3>
                <p>全系列产品规格、对比表、选型指南。</p>
                <a href="./Product_Catalog.pdf" class="btn btn-sm btn-primary" style="margin-top:12px;display:inline-block;" target="_blank">下载 PDF</a>
            </div>
            <div class="feature-card" style="flex:1;min-width:200px;">
                <div class="icon">📜</div>
                <h3>认证文件</h3>
                <p>RoHS、REACH 合规声明、专利证书。</p>
                <a href="./Certifications.pdf" class="btn btn-sm btn-primary" style="margin-top:12px;display:inline-block;" target="_blank">查看认证</a>
            </div>
        </div>
    </div>
</div>
'''

    # FAQ
    html += f'''
<div class="section">
    <div class="container">
        <span class="section-label">FAQ</span>
        <h2 class="section-title">{s["full_name"]} 常见问题</h2>
        <div class="faq-section">
'''
    for faq in s["faqs"]:
        html += f'            <div class="faq-item"><h3>❓ {faq[0]}</h3><p>{faq[1]}</p></div>\n'
    html += '''
        </div>
        <div class="back-link">
            <a href="faq.html">查看全部18个FAQ →</a>
        </div>
    </div>
</div>
'''

    # Back link
    html += '''
<div class="back-link">
    <a href="index.html">← 返回首页</a>&nbsp;&nbsp;<a href="articles.html">查看技术文章 →</a>
</div>
'''

    html += FOOTER

    fname = f"ig-{s['name'].lower().split('-')[0]}.html"
    # Actually let me just use the simple name
    fname = f"ig-{s['name'].lower().split('-')[0]}.html"
    if s['name'] == 'IG-C':
        fname = 'ig-c.html'
    elif s['name'] == 'IG-F':
        fname = 'ig-f.html'
    elif s['name'] == 'IG-S':
        fname = 'ig-s.html'
    
    with open(f'/app/data/所有对话/主对话/github_pages/{fname}', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ Created {fname}")

print("\nAll pages generated!")

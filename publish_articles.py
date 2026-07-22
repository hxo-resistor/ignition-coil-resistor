#!/usr/bin/env python3
import requests, base64, os

headers = {'Authorization': 'token YOUR_TOKEN_HERE'}
repo = 'https://api.github.com/repos/hxo-resistor/ignition-coil-resistor'

def create_article_page(title, content, filename):
    html_lines = []
    in_code = False
    for line in content.split('\n'):
        stripped = line.strip()
        if stripped.startswith('```'):
            if in_code:
                html_lines.append('</code></pre>')
                in_code = False
            else:
                html_lines.append('<pre><code>')
                in_code = True
            continue
        if in_code:
            html_lines.append(line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
            continue
        if stripped.startswith('## '):
            html_lines.append(f'<h2>{stripped[3:]}</h2>')
        elif stripped.startswith('### '):
            html_lines.append(f'<h3>{stripped[4:]}</h3>')
        elif stripped.startswith('- '):
            html_lines.append(f'<li>{stripped[2:]}</li>')
        elif stripped == '':
            html_lines.append('<br>')
        else:
            html_lines.append(f'<p>{stripped}</p>')
    
    body = '\n'.join(html_lines)
    
    # Escape for HTML
    title_escaped = title.replace('"', '&quot;')
    
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title_escaped} | HXO Resistor</title>
    <meta name="description" content="{title_escaped} - 点火线圈抑制电阻技术文章">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.8; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; background: #f9f9f9; }}
        .article {{ background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        h1 {{ font-size: 1.8em; color: #1a1a1a; margin-bottom: 20px; border-bottom: 3px solid #e63946; padding-bottom: 10px; }}
        h2 {{ font-size: 1.3em; color: #e63946; margin: 30px 0 15px; }}
        h3 {{ font-size: 1.1em; color: #457b9d; margin: 20px 0 10px; }}
        p {{ margin: 10px 0; }}
        li {{ margin: 5px 0 5px 20px; }}
        pre {{ background: #f1f1f1; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 0.9em; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background: #e63946; color: white; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        .cta {{ background: #1d3557; color: white; padding: 20px; border-radius: 8px; text-align: center; margin: 30px 0; }}
        .cta a {{ color: #a8dadc; font-weight: bold; }}
        .back {{ margin: 20px 0; }}
        .back a {{ color: #e63946; text-decoration: none; }}
        .back a:hover {{ text-decoration: underline; }}
        @media (max-width: 600px) {{ body {{ padding: 10px; }} .article {{ padding: 20px; }} }}
    </style>
</head>
<body>
    <div class="back"><a href="./index.html">返回首页</a> | <a href="./articles.html">所有文章</a></div>
    <div class="article">
        <h1>{title_escaped}</h1>
        {body}
        <div class="cta">
            <p><strong>需要采购点火线圈抑制电阻？</strong></p>
            <p>提供免费样品 + 完整测试报告，交期7-15天</p>
            <p>邮箱: resistor@hxo-lcr.cn | 电话: 13510200650</p>
            <p><a href="./index.html">访问官网查看更多产品信息</a></p>
        </div>
    </div>
</body>
</html>'''

def upload_file(filename, content, commit_msg):
    check = requests.get(f'{repo}/contents/{filename}', headers=headers)
    data = {'message': commit_msg, 'content': base64.b64encode(content.encode('utf-8')).decode('utf-8')}
    if check.status_code == 200:
        data['sha'] = check.json()['sha']
    r = requests.put(f'{repo}/contents/{filename}', headers=headers, json=data)
    return r.status_code in [200, 201]

# 读取文章
base_dir = '/app/data/所有对话/主对话/系统资料库/04_内容营销'
articles = [
    ('点火线圈抑制电阻选型指南：阻值、功率、温度系数怎么选', 
     os.path.join(base_dir, '技术文章_点火线圈抑制电阻选型指南.md'),
     'article_selection_guide.html'),
    ('AEC-Q200认证对汽车电阻意味着什么？',
     os.path.join(base_dir, '技术文章_AEC-Q200认证对汽车电阻意味着什么.md'),
     'article_aeq200_certification.html'),
    ('点火线圈故障排查：电阻值异常的原因分析',
     os.path.join(base_dir, '技术文章_点火线圈故障排查电阻值异常原因分析.md'),
     'article_fault_diagnosis.html'),
]

for title, filepath, filename in articles:
    with open(filepath, 'r') as f:
        content = f.read()
    page_html = create_article_page(title, content, filename)
    if upload_file(filename, page_html, f'发布技术文章: {title[:20]}'):
        print(f'OK: {filename}')
    else:
        print(f'FAIL: {filename}')

# 创建文章列表页
articles_html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>技术文章 | HXO Resistor 点火线圈抑制电阻</title>
    <meta name="description" content="点火线圈抑制电阻技术文章合集 - 选型指南、AEC-Q200认证、故障排查等实用内容">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; background: #f9f9f9; }
        h1 { color: #1a1a1a; border-bottom: 3px solid #e63946; padding-bottom: 10px; margin-bottom: 30px; }
        .back { margin-bottom: 20px; }
        .back a { color: #e63946; text-decoration: none; }
        .back a:hover { text-decoration: underline; }
        .article-card { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .article-card h2 { font-size: 1.2em; margin-bottom: 10px; }
        .article-card h2 a { color: #1d3557; text-decoration: none; }
        .article-card h2 a:hover { color: #e63946; }
        .article-card p { color: #666; font-size: 0.9em; }
        .article-card .tag { display: inline-block; background: #e63946; color: white; padding: 2px 10px; border-radius: 3px; font-size: 0.8em; margin-top: 10px; }
        @media (max-width: 600px) { body { padding: 10px; } .article-card { padding: 15px; } }
    </style>
</head>
<body>
    <div class="back"><a href="./index.html">返回首页</a></div>
    <h1>技术文章</h1>
    
    <div class="article-card">
        <h2><a href="./article_selection_guide.html">点火线圈抑制电阻选型指南：阻值、功率、温度系数怎么选</a></h2>
        <p>详解抑制电阻的选型方法，阻值1Ω和5kΩ的区别、功率3W/5W/10W的适用场景、不同工艺的温度表现对比，附快速选型三步法。</p>
        <span class="tag">选型指南</span>
    </div>
    
    <div class="article-card">
        <h2><a href="./article_aeq200_certification.html">AEC-Q200认证对汽车电阻意味着什么？</a></h2>
        <p>AEC-Q200的20+项应力测试详解，没有认证的电阻在车载环境中的真实风险，不同认证等级的含金量差异，以及如何验证认证真伪。</p>
        <span class="tag">认证标准</span>
    </div>
    
    <div class="article-card">
        <h2><a href="./article_fault_diagnosis.html">点火线圈故障排查：电阻值异常的原因分析</a></h2>
        <p>阻值偏大/偏小/开路/不稳定四种异常现象的原因分析和解决方案，维修师傅的实用诊断流程，不同场景的选型推荐。</p>
        <span class="tag">故障排查</span>
    </div>
</body>
</html>'''

if upload_file('articles.html', articles_html, '创建技术文章列表页'):
    print('OK: articles.html')
else:
    print('FAIL: articles.html')
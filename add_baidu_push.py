# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

REPO_DIR = r"C:\Users\Administrator\.agnes\temporary\2026-08-17\20260817_1\website-repo"
BASE_URL = "https://www.hxo-lcr.cn"

def log(msg):
    print(f"[Baidu Push] {msg}")

# 百度自动推送JS代码（官方标准）
BAIDU_PUSH_JS = '''    <!-- Baidu Auto Push JS -->
    <script>
    (function(){
        var bp = document.createElement('script');
        var curProtocol = window.location.protocol.split(':')[0];
        if (curProtocol === 'https') {
            bp.src = 'https://zz.bdstatic.com/linksubmit/push.js';
        } else {
            bp.src = 'http://push.zhanzhang.baidu.com/push.js';
        }
        var s = document.getElementsByTagName("script")[0];
        s.parentNode.insertBefore(bp, s);
    })();
    </script>
'''

# 百度API推送Token（待填写）
BAIDU_API_TOKEN = "YOUR_BAIDU_API_TOKEN_HERE"

# Step 1: Add Baidu push JS to all HTML files
log("\nStep 1: Adding Baidu auto-push JS to all HTML files...")

html_files = list(Path(REPO_DIR).glob("*.html"))
modified_count = 0

for html_file in html_files:
    if html_file.name.startswith('.'):
        continue
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already has baidu push
    if 'linksubmit/push.js' in content or 'push.zhanzhang.baidu.com' in content:
        log(f"  SKIP {html_file.name}: Already has Baidu push JS")
        continue
    
    # Add before </body>
    if '</body>' in content:
        new_content = content.replace('</body>', BAIDU_PUSH_JS + '    </body>')
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        log(f"  OK {html_file.name}")
        modified_count += 1
    else:
        log(f"  WARN {html_file.name}: No </body> found")

log(f"\nTotal modified: {modified_count} files")

# Step 2: Update publish script with Baidu API push function
log("\nStep 2: Updating publish_b2b_package_v1.2.py...")

publish_script = Path(REPO_DIR) / "publish_b2b_package_v1.2.py"
with open(publish_script, 'r', encoding='utf-8') as f:
    script_content = f.read()

# Check if baidu push already exists
if 'baidu_push_urls' in script_content:
    log("  SKIP: Baidu API push already exists in script")
else:
    # Add baidu_push_urls function after check_proxy function
    baidu_push_func = '''

def baidu_push_urls(urls):
    """百度API主动推送URL（加速收录）"""
    log("百度API主动推送...")
    
    if BAIDU_API_TOKEN == "YOUR_BAIDU_API_TOKEN_HERE":
        log("  Token未配置，跳过百度API推送", 'WARN')
        return False
    
    try:
        # 构造API URL
        site = CONFIG['primary_domain']
        api_url = f"http://data.zz.baidu.com/urls?site={site}&token={BAIDU_API_TOKEN}"
        
        # 发送请求
        proxies = {'http': CONFIG['proxy'], 'https': CONFIG['proxy']}
        headers = {'User-Agent': 'hxobot', 'Content-Type': 'text/plain; charset=utf-8'}
        
        response = requests.post(
            api_url,
            data='\\n'.join(urls),
            headers=headers,
            proxies=proxies,
            timeout=CONFIG['timeout']
        )
        
        result = response.json()
        
        if response.status_code == 200 and result.get('success', 0) > 0:
            log(f"  百度API推送成功: 成功{result['success']}条, 剩余{result.get('remain', 0)}条配额", 'SUCCESS')
            return True
        else:
            log(f"  百度API推送异常: {result}", 'WARN')
            return False
            
    except Exception as e:
        log(f"  百度API推送失败: {e}", 'ERROR')
        return False
'''
    
    # Insert after check_proxy function
    if 'def check_proxy():' in script_content:
        # Find the end of check_proxy function
        import re
        match = re.search(r'(def check_proxy\(\).*?)(\ndef )', script_content, re.DOTALL)
        if match:
            insert_pos = match.start(2)
            script_content = script_content[:insert_pos] + baidu_push_func + script_content[insert_pos:]
            log("  Added baidu_push_urls function")
        else:
            log("  WARN: Could not find insertion point", 'WARN')
    else:
        log("  WARN: check_proxy function not found", 'WARN')
    
    # Add config for Baidu API
    baidu_config = '''
    # 百度搜索配置
    'baidu_api_token': BAIDU_API_TOKEN,
    'baidu_site': BASE_URL,
'''
    
    # Insert after 'github_repo' line
    if "'github_repo'" in script_content:
        script_content = script_content.replace(
            "    'github_repo': 'hxo-resitor/ignition-coil-resitor',",
            "    'github_repo': 'hxo-resitor/ignition-coil-resitor',\n" + baidu_config
        )
        log("  Added Baidu config to CONFIG")
    
    # Add baidu push call after git push success
    # Find the git push section and add baidu push after
    if 'commit_hash = git_add_commit_push' in script_content:
        # Find where to insert - after git push success
        insert_text = '''
    # 步骤4.5: 百度API推送
    log("步骤 4.5/7: 百度API推送")
    site_urls = [
        '{}/{}'.format(CONFIG['primary_domain'], html_file),
        '{}/articles.html'.format(CONFIG['primary_domain']),
        '{}/faq.html'.format(CONFIG['primary_domain']),
        '{}/comparison.html'.format(CONFIG['primary_domain']),
    ]
    baidu_success = baidu_push_urls(site_urls)
    if baidu_success:
        log("百度API推送完成", 'SUCCESS')
    print("")
'''
        script_content = script_content.replace(
            '    log("Commit Hash: {}".format(commit_hash[:8]))\n    print("")',
            '    log("Commit Hash: {}".format(commit_hash[:8]))\n' + insert_text
        )
        log("  Added baidu push call in main()")
    
    # Write updated script
    with open(publish_script, 'w', encoding='utf-8') as f:
        f.write(script_content)
    log("  Saved updated publish script")

# Step 3: Git commit and push
log("\nStep 3: Git operations...")

result = subprocess.run(
    f'cd "{REPO_DIR}" && git add . && git commit -m "Add Baidu auto-push JS and API push support" && git push origin main',
    shell=True, capture_output=True, text=True
)
log(f"Result: rc={result.returncode}")
if result.returncode != 0:
    log(f"Error: {result.stderr}")
else:
    commit_hash = subprocess.run('git rev-parse HEAD', shell=True, capture_output=True, text=True, cwd=REPO_DIR).stdout.strip()
    log(f"Commit: {commit_hash}")

# Step 4: Wait and verify
log("\nStep 4: Waiting 120 seconds for deployment...")
time.sleep(120)

# Verify homepage
log("\nStep 5: Verifying deployment...")
try:
    req = urllib.request.Request(f"{BASE_URL}/", headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(req, timeout=15)
    html_content = response.read().decode('utf-8')
    status = response.getcode()
    
    has_push_js = 'linksubmit/push.js' in html_content or 'push.zhanzhang.baidu.com' in html_content
    
    log(f"  Homepage HTTP Status: {status}")
    log(f"  Baidu Push JS: {'Found ✅' if has_push_js else 'NOT Found ❌'}")
    
    if has_push_js:
        # Extract and show a snippet
        import re
        match = re.search(r'<script[^>]*>[\s\S]*?linksubmit/push\.js[\s\S]*?</script>', html_content, re.IGNORECASE)
        if match:
            snippet = match.group()[:200].replace('\n', ' ')
            log(f"  JS Snippet: {snippet}...")
            
except Exception as e:
    log(f"  ERROR: {e}")

log("\n" + "="*60)
log("Task completed!")
log("="*60)
log(f"\n注意: 请前往 https://ziyuan.baidu.com/ 获取百度API Token，")
log(f"      然后编辑 publish_b2b_package_v1.2.py 替换 BAIDU_API_TOKEN")

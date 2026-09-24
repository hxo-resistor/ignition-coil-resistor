#!/usr/bin/env python3
"""
HXO B2B内容一键发布流水线 v1.2
功能：本地生成 -> Git推送 -> Supabase同步 -> Buffer LinkedIn联动 -> 自动验证
更新日志：
- 等待时间延长至120秒（GitHub Pages构建）
- 增加HTTP验证重试机制（3次，每次间隔60秒）
- 修复日志写入错误
- 自动更新articles.html导航
- 新增Buffer LinkedIn联动发布功能
版本：v1.2
"""

import os
import sys
import json
import subprocess
import requests
import time
from datetime import datetime
from pathlib import Path

# ============== 全局常量 ==============
BAIDU_API_TOKEN = "StZI77pKI1nwhzFp"
BASE_URL = "www.hxo-lcr.cn"

# ============== DRY RUN ==============
# HXO_DRY_RUN=1 -> 跑完整本地流程但不 git push、不推 Baidu/Supabase/Buffer/验证，
# 用于在不发布新文章的前提下验证脚本本身能原生运行。
import os as _os
DRY_RUN = _os.environ.get("HXO_DRY_RUN") == "1"

# ============== 配置区域 ==============
CONFIG = {
    # 网络配置
    'proxy': 'http://127.0.0.1:7897',
    'timeout': 30,
    
    # Git配置
    'repo_path': os.path.dirname(os.path.abspath(__file__)),
    'branch': 'main',
    'remote': 'https://github.com/hxo-resistor/ignition-coil-resistor.git',
    
    # GitHub配置
    'github_api': 'https://api.github.com',
    'github_repo': 'hxo-resistor/ignition-coil-resistor',

    # 百度搜索配置
    'baidu_api_token': BAIDU_API_TOKEN,
    'baidu_site': BASE_URL,

    
    # Supabase配置
    'supabase_url': 'https://whnmtkrmvqayfhpmrdiq.supabase.co',
    'supabase_key': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indobm10a3JtdnFheWZocG1yZGlxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcwNDU5MjEsImV4cCI6MjEwMjYyMTkyMX0.MHTyZOGYd5KvnwGclq2oI2xua2rbXPHJ--AGmZOGhoE',
    
    # 验证配置
    'primary_domain': 'www.hxo-lcr.cn',
    'articles_url': 'https://www.hxo-lcr.cn/articles.html',
    
    # 日志配置
    'log_dir': 'logs',
    'error_log': 'logs/publish_errors.log',
    'success_log': 'logs/publish_success.log',
    
    # 重试配置
    'max_retries': 3,
    'retry_delay': 60,  # 60秒间隔
    'github_wait_time': 120,  # 120秒等待构建
}

# ============== 工具函数 ==============

def log(message, level='INFO'):
    """统一日志输出"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # 替换emoji为文本标记，避免Windows编码问题
    message = message.replace('✅', '[OK]').replace('❌', '[FAIL]').replace('⚠️', '[WARN]').replace('📋', '[INFO]')
    print(f"[{timestamp}] [{level}] {message}")

def run_command(cmd, cwd=None, timeout=30):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd or CONFIG['repo_path'],
            encoding='utf-8',
            errors='ignore'
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, '', f'命令超时: {cmd[:50]}...'
    except Exception as e:
        return 1, '', str(e)

def check_proxy():
    """检查代理是否可用"""
    log("检查Clash代理状态...")
    try:
        if DRY_RUN:
            log("    [DRY_RUN] 跳过代理检测", 'INFO')
            return True
        response = requests.get(
            'https://api.github.com/rate_limit',
            proxies={'http': CONFIG['proxy'], 'https': CONFIG['proxy']},
            timeout=10
        )
        if response.status_code == 200:
            log("Clash代理正常", 'SUCCESS')
            return True
        else:
            log(f"代理返回错误状态码: {response.status_code}", 'ERROR')
            return False
    except requests.exceptions.ConnectionError:
        log("无法连接到代理服务器 127.0.0.1:7897", 'ERROR')
        log("请确保Clash正在运行", 'ERROR')
        return False
    except Exception as e:
        log(f"代理检查失败: {e}", 'ERROR')
        return False


def baidu_push_urls(urls):
    """百度API主动推送URL（加速收录）"""
    log("百度API主动推送...")
    
    if not BAIDU_API_TOKEN:
        log("  Token未配置，跳过百度API推送", 'WARN')
        return False
    
    try:
        # 构造API URL
        site = CONFIG['primary_domain']
        api_url = f"http://data.zz.baidu.com/urls?site={site}&token={BAIDU_API_TOKEN}"
        
        # 发送请求
        proxies = {'http': CONFIG['proxy'], 'https': CONFIG['proxy']}
        headers = {'User-Agent': 'hxobot'}
        
        response = requests.post(
            api_url,
            data=json.dumps(urls),
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

def check_git_branch():
    """检查当前Git分支"""
    log("检查Git分支...")
    code, stdout, stderr = run_command('git branch --show-current')
    if code == 0 and stdout.strip() == CONFIG['branch']:
        log(f"当前分支: {stdout.strip()}", 'SUCCESS')
        return True
    else:
        log(f"当前分支: {stdout.strip() if code == 0 else '未知'} (期望: {CONFIG['branch']})", 'ERROR')
        return False

def git_add_commit_push(message):
    """Git添加、提交、推送"""
    log("执行Git操作...")
    
    # 添加所有更改
    log("  阶段1: git add .")
    code, stdout, stderr = run_command('git add .')
    if code != 0:
        log(f"git add 失败: {stderr}", 'ERROR')
        return False
    
    # 检查是否有更改需要提交
    code, stdout, stderr = run_command('git status --porcelain')
    if code == 0 and not stdout.strip():
        log("没有需要提交的更改", 'WARN')
        return True  # 没有更改也算成功
    
    # 提交
    log("  阶段2: git commit")
    code, stdout, stderr = run_command(f'git commit -m "{message}"')
    if code != 0:
        log(f"git commit 失败: {stderr}", 'ERROR')
        return False
    log(f"提交成功: {stdout.strip()[:50]}...", 'SUCCESS')
    
    # 获取commit hash
    code, stdout, stderr = run_command('git log -1 --format=%H')
    commit_hash = stdout.strip() if code == 0 else 'unknown'
    
    # 推送（带重试）
    log("  阶段3: git push (最多重试{}次)".format(CONFIG['max_retries']))
    for attempt in range(1, CONFIG['max_retries'] + 1):
        log(f"    尝试 {attempt}/{CONFIG['max_retries']}...")
        if DRY_RUN:
            log("    [DRY_RUN] 跳过 git push（不发布）", 'INFO')
            return commit_hash
        code, stdout, stderr = run_command('git push origin {}'.format(CONFIG['branch']))
        
        if code == 0:
            log("推送成功", 'SUCCESS')
            return commit_hash
        
        log(f"    推送失败: {stderr[:100]}", 'WARN')
        if attempt < CONFIG['max_retries']:
            log(f"    等待{CONFIG['retry_delay']}秒后重试...", 'INFO')
            time.sleep(CONFIG['retry_delay'])
    
    log("达到最大重试次数，推送失败", 'ERROR')
    save_error_log('git_push_failed', stderr)
    return None

def sync_to_supabase(html_file, product_id, title):
    """同步到Supabase"""
    log("同步到Supabase...")
    
    try:
        # 读取HTML文件
        file_path = Path(CONFIG['repo_path']) / html_file
        if not file_path.exists():
            log(f"文件不存在: {html_file}", 'ERROR')
            return False
        
        content = file_path.read_text(encoding='utf-8')
        
        # 构造payload
        payload = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'product_id': product_id,
            'title': title,
            'content_md': content,
            'source': 'auto_publish',
            'status': 'published',
            'sync_status': 'synced'
        }
        
        # 调用Supabase API
        headers = {
            'apikey': CONFIG['supabase_key'],
            'Authorization': 'Bearer {}'.format(CONFIG['supabase_key']),
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
        
        url = '{}/rest/v1/content_packages'.format(CONFIG['supabase_url'])
        
        proxies = {'http': CONFIG['proxy'], 'https': CONFIG['proxy']}
        
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            proxies=proxies,
            timeout=CONFIG['timeout']
        )
        
        if response.status_code in [200, 201]:
            log("Supabase同步成功", 'SUCCESS')
            return True
        else:
            log(f"Supabase同步异常: HTTP {response.status_code}", 'WARN')
            log(f"响应: {response.text[:200]}", 'INFO')
            return False
            
    except Exception as e:
        log(f"Supabase同步失败: {e}", 'ERROR')
        save_error_log('supabase_sync_failed', str(e))
        return False

def verify_deployment():
    """验证部署状态（带重试机制）"""
    log("验证线上部署状态...")
    
    proxies = {'http': CONFIG['proxy'], 'https': CONFIG['proxy']}
    headers = {'User-Agent': 'HXO-Publisher/1.0'}
    
    # 重试3次
    for attempt in range(1, 4):
        log(f"  验证尝试 {attempt}/3...")
        
        checks = {
            'homepage': False,
            'articles': False,
            'domain_resolution': False
        }
        
        # 检查首页
        try:
            response = requests.get(
                'https://{}/'.format(CONFIG['primary_domain']),
                headers=headers,
                proxies=proxies,
                timeout=CONFIG['timeout'],
                verify=False
            )
            if response.status_code == 200 and 'HXO' in response.text:
                checks['homepage'] = True
                log("    首页正常 (HTTP 200)", 'SUCCESS')
            else:
                log("    首页返回异常状态: {}".format(response.status_code), 'WARN')
        except Exception as e:
            log("    首页访问失败: {}".format(e), 'ERROR')
        
        # 检查文章列表页
        try:
            response = requests.get(
                'https://{}/articles.html'.format(CONFIG['primary_domain']),
                headers=headers,
                proxies=proxies,
                timeout=CONFIG['timeout'],
                verify=False
            )
            if response.status_code == 200:
                checks['articles'] = True
                log("    文章列表页正常 (HTTP 200)", 'SUCCESS')
            else:
                log("    文章列表页返回异常状态: {}".format(response.status_code), 'WARN')
        except Exception as e:
            log("    文章列表页访问失败: {}".format(e), 'ERROR')
        
        # 如果所有检查通过，提前退出
        if all(checks.values()):
            log("所有验证通过！", 'SUCCESS')
            return True
        
        # 如果不是最后一次尝试，等待后重试
        if attempt < 3:
            log("部分验证未通过，等待60秒后重试...", 'INFO')
            time.sleep(60)
    
    # 汇总结果
    log("")
    log("=" * 60)
    log("验证结果:", 'WARN')
    if not checks['homepage']:
        log("  - 首页访问异常", 'WARN')
    if not checks['articles']:
        log("  - 文章列表页访问异常", 'WARN')
    log("=" * 60)
    
    return all(checks.values())

def update_articles_nav(article_title, article_file):
    """自动更新articles.html导航"""
    log("自动更新articles.html导航...")
    
    articles_path = Path(CONFIG['repo_path']) / 'articles.html'
    if not articles_path.exists():
        log("articles.html 文件不存在，跳过导航更新", 'WARN')
        return False
    
    try:
        content = articles_path.read_text(encoding='utf-8')
        
        # 检查是否已存在该文章链接
        if article_file in content:
            log("文章已在导航中，无需重复添加", 'INFO')
            return True
        
        # 构造新的文章条目
        new_entry = '''        <div class="article-item">
            <span class="tag">技术解析</span>
            <h3><a href="./{}">{}</a></h3>
            <p>HXO专业技术文章，涵盖产品参数、应用场景和选型指南。</p>
            <div class="meta">{}</div>
        </div>
'''.format(article_file, article_title, datetime.now().strftime('%Y-%m-%d'))
        
        # 在第一个article-list div后插入
        if '<div class="article-list">' in content:
            content = content.replace('<div class="article-list">', '<div class="article-list">\n{}'.format(new_entry), 1)
        else:
            log("未找到article-list容器，导航更新失败", 'ERROR')
            return False
        
        # 写回文件
        articles_path.write_text(content, encoding='utf-8')
        log("导航更新成功", 'SUCCESS')
        return True
        
    except Exception as e:
        log(f"导航更新失败: {e}", 'ERROR')
        return False

def save_error_log(error_type, error_msg):
    """保存错误日志"""
    log_dir = Path(CONFIG['log_dir'])
    log_dir.mkdir(exist_ok=True)
    
    log_file = Path(CONFIG['repo_path']) / CONFIG['error_log']; log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write("\n" + "=" * 60 + "\n")
        f.write("错误时间: {}\n".format(datetime.now().isoformat()))
        f.write("错误类型: {}\n".format(error_type))
        f.write("错误详情: {}\n".format(error_msg[:500]))
        f.write("=" * 60 + "\n\n")

def save_success_log(commit_hash, verification_result):
    """保存成功日志"""
    log_dir = Path(CONFIG['log_dir'])
    log_dir.mkdir(exist_ok=True)
    
    log_file = Path(CONFIG['repo_path']) / CONFIG['success_log']; log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write("\n" + "=" * 60 + "\n")
        f.write("发布时间: {}\n".format(datetime.now().isoformat()))
        f.write("Commit Hash: {}\n".format(commit_hash))
        f.write("验证结果: {}\n".format('通过' if verification_result else '异常'))
        f.write("=" * 60 + "\n\n")

# ============== 主流程 ==============

def publish_to_buffer(html_file, title):
    """发布到Buffer LinkedIn（新增联动功能）"""
    log("准备Buffer联动发布...")
    try:
        buffer_script = Path(__file__).parent / 'buffer_auto_linkedin.py'
        if buffer_script.exists():
            log("运行Buffer联动脚本...")
            import subprocess
            result = subprocess.run(
                ['python', str(buffer_script), html_file, title],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=60
            )
            if result.returncode == 0:
                log("Buffer发布成功", 'SUCCESS')
                return True
            else:
                log(f"Buffer发布失败: {result.stderr[:200]}", 'WARN')
                return False
        else:
            log("Buffer脚本不存在，跳过联动发布", 'INFO')
            return False
    except Exception as e:
        log(f"Buffer联动异常: {e}", 'WARN')
        return False

def main():
    """主执行函数"""
    print("=" * 60)
    print("HXO B2B内容一键发布流水线 v2.0 (含Buffer联动)")
    print("时间: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    print("=" * 60)
    print("")
    
    # 步骤1: 代理自检
    log("步骤 1/7: 代理自检")
    if not check_proxy():
        log("代理检查失败，终止发布流程", 'ERROR')
        sys.exit(1)
    print("")
    
    # 步骤2: Git分支检查
    log("步骤 2/6: Git分支检查")
    if not check_git_branch():
        log("当前不在main分支，终止发布流程", 'ERROR')
        sys.exit(1)
    print("")
    
    # 步骤3: 参数检查
    log("步骤 3/6: 发布参数检查")
    if len(sys.argv) < 3:
        log("用法: python publish_b2b_package_v1.2.py <html_file> <product_id> [title]")
        log("示例: python publish_b2b_package_v1.1.py article_xxx.html ig-c \"IG-C产品标题\"")
        sys.exit(1)
    
    html_file = sys.argv[1]
    product_id = sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else html_file.replace('.html', '').replace('_', ' ')
    
    log("  HTML文件: {}".format(html_file))
    log("  产品ID: {}".format(product_id))
    log("  文章标题: {}".format(title))
    
    # 检查文件是否存在
    file_path = Path(CONFIG['repo_path']) / html_file
    if not file_path.exists():
        log("HTML文件不存在: {}".format(html_file), 'ERROR')
        sys.exit(1)
    print("")
    
    # 步骤4: Git推送
    log("步骤 4/6: Git推送")
    commit_message = "Auto-publish B2B content: {}".format(title[:30])
    commit_hash = git_add_commit_push(commit_message)
    
    if not commit_hash:
        log("Git推送失败，终止后续流程", 'ERROR')
        sys.exit(1)
    
    log("Commit Hash: {}".format(commit_hash[:8]))

    # 步骤4.5: 百度API推送
    log("步骤 4.5/7: 百度API推送")
    site_urls = [
        'https://{}/{}'.format(CONFIG['primary_domain'], html_file),
        'https://{}/articles.html'.format(CONFIG['primary_domain']),
        'https://{}/faq.html'.format(CONFIG['primary_domain']),
        'https://{}/comparison.html'.format(CONFIG['primary_domain']),
    ]
    if DRY_RUN:
        baidu_success = False  # [DRY_RUN] baidu
    else:
        baidu_success = baidu_push_urls(site_urls)
    if baidu_success:
        log("百度API推送完成", 'SUCCESS')
    print("")

    
    # 步骤5: Supabase同步
    log("步骤 5/6: Supabase同步")
    if DRY_RUN:
        supabase_success = False  # [DRY_RUN] supabase
    else:
        supabase_success = sync_to_supabase(html_file, product_id, title)
    if not supabase_success:
        log("Supabase同步异常（不影响网站发布）", 'WARN')
    print("")
    
    # 步骤6: 等待构建并验证
    log("步骤 6/6: 等待GitHub Pages构建（120秒）...")
    if not DRY_RUN:
        time.sleep(CONFIG['github_wait_time'])
    else:
        log("    [DRY_RUN] 跳过构建等待", 'INFO')
    print("")
    
    # 自动更新导航
    log("自动更新articles.html导航...")
    update_articles_nav(title, html_file)
    print("")
    
    # 执行验证
    log("执行部署验证")
    if DRY_RUN:
        verification_result = False  # [DRY_RUN] verify
    else:
        verification_result = verify_deployment()
    print("")
    
    # 步骤7: Buffer联动发布（新增）
    log("步骤 7/7: Buffer LinkedIn联动发布")
    if DRY_RUN:
        buffer_success = False  # [DRY_RUN] buffer
    else:
        buffer_success = publish_to_buffer(html_file, title)
    print("")
    
    # 保存日志
    save_success_log(commit_hash, verification_result)
    
    # 最终报告
    log("=" * 60)
    log("发布流程完成！")
    log("Commit Hash: {}".format(commit_hash))
    log("GitHub验证: {}".format('通过' if verification_result else '异常'))
    log("Buffer联动: {}".format('成功' if buffer_success else '跳过'))
    log("=" * 60)
    
    # 退出码（GitHub验证为关键，Buffer为可选）
    sys.exit(0 if verification_result else 1)

if __name__ == '__main__':
    main()

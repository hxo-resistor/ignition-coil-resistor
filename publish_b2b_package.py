#!/usr/bin/env python3
"""
HXO B2B内容一键发布流水线
功能：本地生成 -> Git推送 -> Supabase同步 -> 自动验证
版本：v1.0
"""

import os
import sys
import json
import subprocess
import requests
import time
from datetime import datetime
from pathlib import Path

# ============== 配置区域 ==============
CONFIG = {
    # 网络配置
    'proxy': 'http://127.0.0.1:7897',
    'timeout': 30,
    
    # Git配置
    'repo_path': r'C:\Users\Administrator\.agnes\temporary\2026-08-17\20260817_1\website-repo',
    'branch': 'main',
    'remote': 'https://github.com/hxo-resitor/ignition-coil-resistor.git',
    
    # GitHub配置
    'github_api': 'https://api.github.com',
    'github_repo': 'hxo-resitor/ignition-coil-resitor',
    
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
    'retry_delay': 5,
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
        response = requests.get(
            'https://api.github.com/rate_limit',
            proxies={'http': CONFIG['proxy'], 'https': CONFIG['proxy']},
            timeout=10
        )
        if response.status_code == 200:
            log("✅ Clash代理正常", 'SUCCESS')
            return True
        else:
            log(f"❌ 代理返回错误状态码: {response.status_code}", 'ERROR')
            return False
    except requests.exceptions.ConnectionError:
        log("❌ 无法连接到代理服务器 127.0.0.1:7897", 'ERROR')
        log("请确保Clash正在运行", 'ERROR')
        return False
    except Exception as e:
        log(f"❌ 代理检查失败: {e}", 'ERROR')
        return False

def check_git_branch():
    """检查当前Git分支"""
    log("检查Git分支...")
    code, stdout, stderr = run_command('git branch --show-current')
    if code == 0 and stdout.strip() == CONFIG['branch']:
        log(f"✅ 当前分支: {stdout.strip()}", 'SUCCESS')
        return True
    else:
        log(f"❌ 当前分支: {stdout.strip() if code == 0 else '未知'} (期望: {CONFIG['branch']})", 'ERROR')
        return False

def git_add_commit_push(message):
    """Git添加、提交、推送"""
    log("执行Git操作...")
    
    # 添加所有更改
    log("  阶段1: git add .")
    code, stdout, stderr = run_command('git add .')
    if code != 0:
        log(f"❌ git add 失败: {stderr}", 'ERROR')
        return False
    
    # 检查是否有更改需要提交
    code, stdout, stderr = run_command('git status --porcelain')
    if code == 0 and not stdout.strip():
        log("⚠️ 没有需要提交的更改", 'WARN')
        return True  # 没有更改也算成功
    
    # 提交
    log("  阶段2: git commit")
    code, stdout, stderr = run_command(f'git commit -m "{message}"')
    if code != 0:
        log(f"❌ git commit 失败: {stderr}", 'ERROR')
        return False
    log(f"✅ 提交成功: {stdout.strip()[:50]}...", 'SUCCESS')
    
    # 推送（带重试）
    log("  阶段3: git push (最多重试{}次)".format(CONFIG['max_retries']))
    for attempt in range(1, CONFIG['max_retries'] + 1):
        log(f"    尝试 {attempt}/{CONFIG['max_retries']}...")
        code, stdout, stderr = run_command('git push origin {}'.format(CONFIG['branch']))
        
        if code == 0:
            log("✅ 推送成功", 'SUCCESS')
            return True
        
        log(f"    推送失败: {stderr[:100]}", 'WARN')
        if attempt < CONFIG['max_retries']:
            log(f"    等待{CONFIG['retry_delay']}秒后重试...", 'INFO')
            time.sleep(CONFIG['retry_delay'])
    
    log("❌ 达到最大重试次数，推送失败", 'ERROR')
    save_error_log('git_push_failed', stderr)
    return False

def sync_to_supabase(html_file, product_id, title):
    """同步到Supabase"""
    log("同步到Supabase...")
    
    try:
        # 读取HTML文件
        file_path = Path(CONFIG['repo_path']) / html_file
        if not file_path.exists():
            log(f"❌ 文件不存在: {html_file}", 'ERROR')
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
            'sync_status': 'pending'
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
            log("✅ Supabase同步成功", 'SUCCESS')
            return True
        else:
            log(f"⚠️ Supabase同步异常: HTTP {response.status_code}", 'WARN')
            log(f"   响应: {response.text[:200]}", 'INFO')
            return False  # 不阻断流程
            
    except Exception as e:
        log(f"❌ Supabase同步失败: {e}", 'ERROR')
        save_error_log('supabase_sync_failed', str(e))
        return False

def verify_deployment():
    """验证部署状态"""
    log("验证线上部署状态...")
    
    checks = {
        'homepage': False,
        'articles': False,
        'domain_resolution': False
    }
    
    proxies = {'http': CONFIG['proxy'], 'https': CONFIG['proxy']}
    headers = {'User-Agent': 'HXO-Publisher/1.0'}
    
    # 检查首页
    log("  检查首页可访问性...")
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
            log("    ✅ 首页正常 (HTTP 200)", 'SUCCESS')
        else:
            log("    ⚠️ 首页返回异常状态: {}".format(response.status_code), 'WARN')
    except Exception as e:
        log("    ❌ 首页访问失败: {}".format(e), 'ERROR')
    
    # 检查文章列表页
    log("  检查文章列表页...")
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
            log("    ✅ 文章列表页正常 (HTTP 200)", 'SUCCESS')
        else:
            log("    ⚠️ 文章列表页返回异常状态: {}".format(response.status_code), 'WARN')
    except Exception as e:
        log("    ❌ 文章列表页访问失败: {}".format(e), 'ERROR')
    
    # 检查DNS解析
    log("  检查域名解析...")
    try:
        import socket
        result = socket.getaddrinfo(CONFIG['primary_domain'], None)
        if result:
            ip = result[0][4][0]
            # GitHub Pages的IP范围
            if ip.startswith('185.199.108') or ip.startswith('185.199.111'):
                checks['domain_resolution'] = True
                log("    ✅ DNS解析正常 (IP: {})".format(ip), 'SUCCESS')
            else:
                log("    ⚠️ DNS指向非GitHub IP: {}".format(ip), 'WARN')
        else:
            log("    ❌ DNS解析失败", 'ERROR')
    except Exception as e:
        log("    ❌ DNS检查异常: {}".format(e), 'ERROR')
    
    # 汇总结果
    all_passed = all(checks.values())
    
    log("")
    log("=" * 60)
    if all_passed:
        log("✅ 部署验证通过！所有检查项正常。", 'SUCCESS')
    else:
        log("⚠️ 部署验证发现异常，请检查以下项目:", 'WARN')
        if not checks['homepage']:
            log("  - 首页访问异常", 'WARN')
        if not checks['articles']:
            log("  - 文章列表页访问异常", 'WARN')
        if not checks['domain_resolution']:
            log("  - DNS解析异常", 'WARN')
        log("")
        log("建议操作:")
        log("  1. 等待GitHub Pages构建完成（通常2-5分钟）")
        log("  2. 检查 https://github.com/{}/settings/pages".format(CONFIG['github_repo']))
        log("  3. 确认CNAME配置正确")
    log("=" * 60)
    
    return all_passed

def save_error_log(error_type, error_msg):
    """保存错误日志"""
    log_dir = Path(CONFIG['log_dir'])
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / CONFIG['error_log']
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
    
    log_file = log_dir / CONFIG['success_log']
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write("\n" + "=" * 60 + "\n")
        f.write("发布时间: {}\n".format(datetime.now().isoformat()))
        f.write("Commit Hash: {}\n".format(commit_hash))
        f.write("验证结果: {}\n".format('通过' if verification_result else '异常'))
        f.write("=" * 60 + "\n\n")

# ============== 主流程 ==============

def main():
    """主执行函数"""
    print("=" * 60)
    print("HXO B2B内容一键发布流水线")
    print("版本: v1.0")
    print("时间: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    print("=" * 60)
    print("")
    
    # 步骤1: 代理自检
    log("步骤 1/5: 代理自检")
    if not check_proxy():
        log("❌ 代理检查失败，终止发布流程", 'ERROR')
        sys.exit(1)
    print("")
    
    # 步骤2: Git分支检查
    log("步骤 2/5: Git分支检查")
    if not check_git_branch():
        log("❌ 当前不在main分支，终止发布流程", 'ERROR')
        sys.exit(1)
    print("")
    
    # 步骤3: 参数检查
    log("步骤 3/5: 发布参数检查")
    if len(sys.argv) < 3:
        log("用法: python publish_b2b_package.py <html_file> <product_id> <title>")
        log("示例: python publish_b2b_package.py article_ig_c.html ig-c IG-C陶瓷芯")
        sys.exit(1)
    
    html_file = sys.argv[1]
    product_id = sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else 'B2B Technical Article'
    
    log("  HTML文件: {}".format(html_file))
    log("  产品ID: {}".format(product_id))
    log("  文章标题: {}".format(title))
    
    # 检查文件是否存在
    file_path = Path(CONFIG['repo_path']) / html_file
    if not file_path.exists():
        log("❌ HTML文件不存在: {}".format(html_file), 'ERROR')
        sys.exit(1)
    print("")
    
    # 步骤4: Git推送
    log("步骤 4/5: Git推送")
    commit_message = "Auto-publish B2B content: {}".format(title[:30])
    push_success = git_add_commit_push(commit_message)
    
    if not push_success:
        log("❌ Git推送失败，终止后续流程", 'ERROR')
        sys.exit(1)
    
    # 获取commit hash
    code, stdout, stderr = run_command('git log -1 --format=%H')
    commit_hash = stdout.strip() if code == 0 else 'unknown'
    log("  Commit Hash: {}".format(commit_hash[:8]))
    print("")
    
    # 步骤5: Supabase同步
    log("步骤 5/5: Supabase同步")
    supabase_success = sync_to_supabase(html_file, product_id, title)
    if not supabase_success:
        log("⚠️ Supabase同步异常（不影响网站发布）", 'WARN')
    print("")
    
    # 等待GitHub Pages构建
    log("等待GitHub Pages构建（30秒）...")
    time.sleep(30)
    print("")
    
    # 步骤6: 自动验证
    log("执行部署验证")
    verification_result = verify_deployment()
    print("")
    
    # 保存日志
    save_success_log(commit_hash, verification_result)
    
    # 最终报告
    log("=" * 60)
    log("发布流程完成！")
    log("Commit Hash: {}".format(commit_hash))
    log("验证结果: {}".format('通过' if verification_result else '异常'))
    log("=" * 60)
    
    # 退出码
    sys.exit(0 if verification_result else 1)

if __name__ == '__main__':
    main()

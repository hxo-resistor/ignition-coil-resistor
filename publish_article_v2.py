#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HXO 文章发布流水线 v2.1 - 修复Git仓库路径问题
功能：生成文章 -> Git推送 -> Supabase同步 -> 百度API推送
版本：v2.1
"""

import os
import sys
import json
import subprocess
import requests
import time
from datetime import datetime
from pathlib import Path

# ============== 配置 ==============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG = {
    'proxy': 'http://127.0.0.1:7897',
    'timeout': 30,
    'repo_path': BASE_DIR,
    'branch': 'main',
    'remote': 'https://github.com/hxo-resistor/ignition-coil-resistor.git',
    'supabase_url': 'https://whnmtkrmvqayfhpmrdiq.supabase.co',
    'supabase_key': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indobm10a3JtdnFheWZocG1yZGlxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcwNDU5MjEsImV4cCI6MjEwMjYyMTkyMX0.MHTyZOGYd5KvnwGclq2oI2xua2rbXPHJ--AGmZOGhoE',
    'primary_domain': 'www.hxo-lcr.cn',
    'baidu_token': 'StZI77pKI1nwhzFp',
    'log_dir': BASE_DIR + '/logs',
}

def log(message, level='INFO'):
    """统一日志输出"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [{level}] {message}")

def run_command(cmd, cwd=None, timeout=30):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=cwd or CONFIG['repo_path'],
            encoding='utf-8', errors='ignore'
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
            log("Clash代理正常", 'SUCCESS')
            return True
        else:
            log(f"代理返回错误状态码: {response.status_code}", 'ERROR')
            return False
    except requests.exceptions.ConnectionError:
        log("无法连接到代理服务器 127.0.0.1:7897", 'ERROR')
        return False
    except Exception as e:
        log(f"代理检查失败: {e}", 'ERROR')
        return False

def git_add_commit_push(message):
    """Git添加、提交、推送"""
    log("执行Git操作...")
    
    # 添加所有更改
    log("  阶段1: git add .")
    code, stdout, stderr = run_command('git add .')
    if code != 0:
        log(f"git add 失败: {stderr}", 'ERROR')
        return None
    
    # 检查是否有更改需要提交
    code, stdout, stderr = run_command('git status --porcelain')
    if code == 0 and not stdout.strip():
        log("没有需要提交的更改", 'WARN')
        return None
    
    # 提交
    log("  阶段2: git commit")
    code, stdout, stderr = run_command(f'git commit -m "{message}"')
    if code != 0:
        log(f"git commit 失败: {stderr}", 'ERROR')
        return None
    log(f"提交成功: {stdout.strip()[:50]}...", 'SUCCESS')
    
    # 获取commit hash
    code, stdout, stderr = run_command('git log -1 --format=%H')
    commit_hash = stdout.strip() if code == 0 else 'unknown'
    
    # 推送（带重试）
    log(f"  阶段3: git push (最多重试3次)")
    for attempt in range(1, 4):
        log(f"    尝试 {attempt}/3...")
        code, stdout, stderr = run_command('git push origin {}'.format(CONFIG['branch']))
        
        if code == 0:
            log("推送成功", 'SUCCESS')
            return commit_hash
        
        log(f"    推送失败: {stderr[:100]}", 'WARN')
        if attempt < 3:
            log(f"    等待60秒后重试...", 'INFO')
            time.sleep(60)
    
    log("达到最大重试次数，推送失败", 'ERROR')
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
        
        # 构建payload
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
            url, json=payload, headers=headers,
            proxies=proxies, timeout=CONFIG['timeout']
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
        return False

def push_to_baidu(urls):
    """推送到百度API"""
    log("推送到百度API...")
    
    try:
        site = 'https://{}'.format(CONFIG['primary_domain'])
        token = CONFIG['baidu_token']
        api_url = 'http://data.zz.baidu.com/urls?site={}&token={}'.format(site, token)
        
        proxies = {'http': CONFIG['proxy'], 'https': CONFIG['proxy']}
        
        data = '\n'.join(urls)
        response = requests.post(
            api_url, data=data.encode('utf-8'),
            headers={'User-Agent': 'hxobot'},
            proxies=proxies, timeout=10
        )
        
        result = json.loads(response.text)
        log(f"百度推送响应: {json.dumps(result, ensure_ascii=False)}", 'INFO')
        
        if result.get('success', 0) > 0:
            log(f"成功推送 {result.get('success')} 个URL", 'SUCCESS')
            log(f"剩余配额: {result.get('remain')} 条/天", 'INFO')
            return True
        else:
            log(f"推送失败: {result.get('message', '未知错误')}", 'ERROR')
            return False
            
    except Exception as e:
        log(f"百度API推送失败: {e}", 'ERROR')
        return False

def verify_deployment(article_url):
    """验证部署状态"""
    log("验证部署状态...")
    
    proxies = {'http': CONFIG['proxy'], 'https': CONFIG['proxy']}
    headers = {'User-Agent': 'HXO-Publisher/1.0'}
    
    try:
        response = requests.get(
            article_url, headers=headers, proxies=proxies,
            timeout=CONFIG['timeout'], verify=False
        )
        if response.status_code == 200:
            log(f"文章验证成功: {article_url}", 'SUCCESS')
            return True
        else:
            log(f"文章访问失败: HTTP {response.status_code}", 'WARN')
            return False
    except Exception as e:
        log(f"文章访问异常: {e}", 'ERROR')
        return False

def main():
    """主执行函数"""
    print("=" * 70)
    print("HXO 文章发布流水线 v2.1")
    print("时间: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    print("=" * 70)
    print("")
    
    # 参数检查
    if len(sys.argv) < 3:
        log("用法: python publish_article_v2.py <html_file> <product_id> [title]")
        log("示例: python publish_article_v2.py article_ig_f_engineering.html ig-f \"IG-F工程车辆应用\"")
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
    
    # 步骤1: Git推送
    log("步骤 1/5: Git推送")
    commit_message = "Auto-publish: {}".format(title[:40])
    commit_hash = git_add_commit_push(commit_message)
    
    if not commit_hash:
        log("Git推送失败或无更改，终止流程", 'ERROR')
        sys.exit(1)
    
    log("Commit Hash: {}".format(commit_hash[:8]))
    print("")
    
    # 步骤2: 等待GitHub Pages构建
    log("步骤 2/5: 等待GitHub Pages构建（60秒）...")
    time.sleep(60)
    print("")
    
    # 步骤3: Supabase同步
    log("步骤 3/5: Supabase同步")
    supabase_success = sync_to_supabase(html_file, product_id, title)
    if not supabase_success:
        log("Supabase同步异常（不影响网站发布）", 'WARN')
    print("")
    
    # 步骤4: 验证部署
    log("步骤 4/5: 验证部署")
    article_url = 'https://www.hxo-lcr.cn/{}'.format(html_file)
    verification_result = verify_deployment(article_url)
    print("")
    
    # 步骤5: 百度推送
    log("步骤 5/5: 百度API推送")
    baidu_success = push_to_baidu([article_url])
    print("")
    
    # 最终报告
    log("=" * 70)
    log("发布流程完成！")
    log("Commit Hash: {}".format(commit_hash))
    log("文章URL: {}".format(article_url))
    log("GitHub验证: {}".format('通过' if verification_result else '异常'))
    log("百度推送: {}".format('成功' if baidu_success else '失败'))
    log("=" * 70)
    
    sys.exit(0 if verification_result else 1)

if __name__ == '__main__':
    main()

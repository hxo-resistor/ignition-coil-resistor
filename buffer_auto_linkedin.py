#!/usr/bin/env python3
"""
HXO Buffer LinkedIn 联动发布脚本 - 修复版
用法: python buffer_auto_linkedin.py <html_file> <title>
"""

import sys
import os
import requests
import hashlib
from datetime import datetime
from pathlib import Path

# 配置
BUFFER_TOKEN = "34cyqxAOzZHdZwFrBFy6Ou89lwONFsuihkJ2RCOGAZm"
CHANNEL_IDS = ["6a9ecd14cd8b9c702c228760"]  # LinkedIn

def safe_log(msg, to_err=False):
    """安全日志输出，避免编码错误"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 清理非ASCII字符
    clean_msg = ''.join(c for c in msg if ord(c) < 128)
    if to_err:
        print(f"[{timestamp}] {clean_msg}", file=sys.stderr)
    else:
        print(f"[{timestamp}] {clean_msg}")

def get_content_from_html(html_file, title):
    """从HTML文章提取核心卖点"""
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取标题和产品关键信息
        linkedin_post = f"""{title}

Technical highlights:
• Professional automotive electronics resistor manufacturer
• AEC-Q200 certified products
• Monthly capacity: 500,000 pieces
• Standard delivery: 7-15 days
• 30-50% cost reduction vs Japanese brands

Contact: resistor@hxo-lcr.cn
Website: www.hxo-lcr.cn

#Resistor #AutomotiveElectronics #OEM #ODM #ChinaSupplier"""
        
        return linkedin_post
    except Exception as e:
        safe_log(f"读取HTML失败: {e}", to_err=True)
        return None

def publish_to_buffer(text):
    """发布到Buffer"""
    url = "https://api.buffer.com/graphql"
    headers = {
        "Authorization": f"Bearer {BUFFER_TOKEN}",
        "Content-Type": "application/json"
    }
    query = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess {
          post { id status }
        }
        ... on MutationError {
          message
        }
      }
    }
    """
    variables = {
        "input": {
            "channelId": CHANNEL_IDS[0],
            "text": text,
            "schedulingType": "automatic",
            "mode": "addToQueue"
        }
    }
    
    try:
        resp = requests.post(url, headers=headers, json={"query": query, "variables": variables}, timeout=30)
        result = resp.json()
        
        if "errors" in result:
            safe_log(f"GraphQL错误: {result['errors']}", to_err=True)
            return False
        
        data = result.get("data", {}).get("createPost", {})
        
        if "post" in data:
            post_id = data['post']['id']
            status = data['post']['status']
            safe_log(f"发布成功 | ID: {post_id} | 状态: {status}")
            return post_id
        elif "message" in data:
            safe_log(f"发布失败: {data['message']}", to_err=True)
            return None
        else:
            safe_log(f"未知响应: {data}", to_err=True)
            return None
    except Exception as e:
        safe_log(f"异常: {e}", to_err=True)
        return None

def main():
    if len(sys.argv) < 3:
        print("用法: python buffer_auto_linkedin.py <html_file> <title>", file=sys.stderr)
        sys.exit(1)
    
    html_file = sys.argv[1]
    title = sys.argv[2]
    
    safe_log("=" * 60)
    safe_log("Buffer LinkedIn 联动发布 (修复版)")
    safe_log("=" * 60)
    
    # 获取内容
    text = get_content_from_html(html_file, title)
    if not text:
        safe_log("无法提取内容，终止发布", to_err=True)
        sys.exit(1)
    
    safe_log(f"内容预览: {text[:80]}...")
    
    # 发布
    post_id = publish_to_buffer(text)
    
    safe_log("=" * 60)
    if post_id:
        safe_log(f"任务完成 | Post ID: {post_id}")
        sys.exit(0)
    else:
        safe_log("任务失败", to_err=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
HXO Buffer LinkedIn 联动发布脚本
由 publish_b2b_package_v1.1.py 调用
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

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

def get_content_from_html(html_file, title):
    """从HTML文章提取核心卖点"""
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取标题和产品关键信息（简化版）
        # 实际应用中可以根据HTML结构解析更多内容
        
        # 构造LinkedIn文案
        linkedin_post = f"""{title}

Technical highlights:
• Professional automotive electronics resistor manufacturer
• AEC-Q200 certified products
• Monthly capacity: 500,000 pieces
• Standard delivery: 7-15 days
• 30-50% cost reduction vs Japanese brands

📧 Contact: resistor@hxo-lcr.cn
🌐 Website: www.hxo-lcr.cn

#Resistor #AutomotiveElectronics #OEM #ODM #ChinaSupplier"""
        
        return linkedin_post
    except Exception as e:
        log(f"读取HTML失败: {e}")
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
            log(f"GraphQL错误: {result['errors']}")
            return False
        
        data = result.get("data", {}).get("createPost", {})
        
        if "post" in data:
            log(f"发布成功 | ID: {data['post']['id']} | 状态: {data['post']['status']}")
            return True
        elif "message" in data:
            log(f"发布失败: {data['message']}")
            return False
        else:
            log(f"未知响应: {data}")
            return False
    except Exception as e:
        log(f"异常: {e}")
        return False

def main():
    if len(sys.argv) < 3:
        print("用法: python buffer_auto_linkedin.py <html_file> <title>")
        sys.exit(1)
    
    html_file = sys.argv[1]
    title = sys.argv[2]
    
    log("=" * 60)
    log("Buffer LinkedIn 联动发布")
    log("=" * 60)
    
    # 获取内容
    text = get_content_from_html(html_file, title)
    if not text:
        log("无法提取内容，终止发布")
        sys.exit(1)
    
    log(f"内容预览: {text[:80]}...")
    
    # 发布
    success = publish_to_buffer(text)
    
    log("=" * 60)
    log(f"任务完成: {'成功' if success else '失败'}")
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Upload all files to GitHub Pages repository - comprehensive version"""

import requests
import base64
import os
import json

GITHUB_TOKEN = "YOUR_TOKEN_HERE"
REPO = "hxo-resistor/ignition-coil-resistor"
BASE_URL = f"https://api.github.com/repos/{REPO}/contents"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

FILES_DIR = "/app/data/所有对话/主对话/github_pages"

BINARY_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.ico', '.zip', '.py'}

def get_existing_sha(filename):
    url = f"{BASE_URL}/{filename}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        return resp.json().get("sha")
    return None

def upload_file(filename):
    filepath = os.path.join(FILES_DIR, filename)
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False
    
    ext = os.path.splitext(filename)[1].lower()
    is_binary = ext in BINARY_EXTENSIONS
    
    with open(filepath, "rb") as f:
        content = f.read()
    
    content_b64 = base64.b64encode(content).decode("utf-8")
    
    data = {
        "message": f"Update {filename}",
        "content": content_b64,
    }
    
    sha = get_existing_sha(filename)
    if sha:
        data["sha"] = sha
    
    url = f"{BASE_URL}/{filename}"
    resp = requests.put(url, headers=HEADERS, json=data)
    
    if resp.status_code in (200, 201):
        print(f"✅ {filename}")
        return True
    else:
        print(f"❌ {filename}: {resp.status_code} - {resp.text[:150]}")
        return False

# All files to upload
all_files = sorted([
    f for f in os.listdir(FILES_DIR)
    if os.path.isfile(os.path.join(FILES_DIR, f))
    and not f.endswith('.py')  # exclude scripts
])

print(f"Uploading {len(all_files)} files to {REPO}...")
print()

success_count = 0
fail_count = 0
for filename in all_files:
    if upload_file(filename):
        success_count += 1
    else:
        fail_count += 1

print()
print(f"✅ Success: {success_count}, ❌ Failed: {fail_count}")
print(f"🌐 https://hxo-resistor.github.io/ignition-coil-resistor/")
#!/usr/bin/env python3
"""Upload all files to GitHub Pages repository"""

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

def get_existing_sha(filename):
    """Get SHA of existing file if it exists"""
    url = f"{BASE_URL}/{filename}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        return resp.json().get("sha")
    return None

def upload_file(filename, is_binary=False):
    """Upload a file to GitHub"""
    filepath = os.path.join(FILES_DIR, filename)
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False
    
    with open(filepath, "rb") as f:
        content = f.read()
    
    if is_binary:
        content_b64 = base64.b64encode(content).decode("utf-8")
        data = {
            "message": f"Update {filename}",
            "content": content_b64,
        }
    else:
        content_str = content.decode("utf-8")
        content_b64 = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
        data = {
            "message": f"Update {filename}",
            "content": content_b64,
        }
    
    # Check if file exists
    sha = get_existing_sha(filename)
    if sha:
        data["sha"] = sha
    
    url = f"{BASE_URL}/{filename}"
    resp = requests.put(url, headers=HEADERS, json=data)
    
    if resp.status_code in (200, 201):
        print(f"✅ Uploaded: {filename} (Status: {resp.status_code})")
        return True
    else:
        print(f"❌ Failed to upload {filename}: {resp.status_code} - {resp.text[:200]}")
        return False

# Files to upload: (filename, is_binary)
files_to_upload = [
    ("index.html", False),
    ("IG-C_Datasheet.pdf", True),
    ("IG-F_Datasheet.pdf", True),
    ("IG-S_Datasheet.pdf", True),
    ("Product_Catalog.pdf", True),
    ("Application_Notes.pdf", True),
    ("Certifications.pdf", True),
]

print("Starting upload to GitHub...")
print(f"Repository: {REPO}")
print()

success = True
for filename, is_binary in files_to_upload:
    if not upload_file(filename, is_binary):
        success = False

print()
if success:
    print("✅ All files uploaded successfully!")
    print(f"🌐 GitHub Pages: https://hxo-resistor.github.io/ignition-coil-resistor/")
else:
    print("⚠️ Some files failed to upload. Check errors above.")

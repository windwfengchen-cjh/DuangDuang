#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""尝试通过群消息或文件信息API获取PDF"""

import sys
import os
import json
import requests

sys.path.insert(0, '/home/admin/openclaw/workspace')
from feishu_config import get_feishu_credentials

FILE_KEY = "file_v3_00103_3ef15c26-a68b-42ac-ac84-2ac099a9852g"
CHAT_ID = "oc_59539a59e696491bd93241ecd9b8c80d"
TEMP_PDF_PATH = "/home/admin/openclaw/workspace/converted/利宝对接文档V1.0.9.pdf"

def get_access_token(app_id, app_secret):
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    response = requests.post(url, json={"app_id": app_id, "app_secret": app_secret})
    return response.json().get("tenant_access_token")

def try_file_operations(access_token):
    """尝试文件相关操作"""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 尝试1: 使用file_v3前缀的文件接口
    print("[尝试1] 使用file_v3文件接口...")
    # file_v3_00103_3ef15c26-a68b-42ac-ac84-2ac099a9852g
    # 尝试去除前缀
    if FILE_KEY.startswith("file_v3_"):
        file_token = FILE_KEY[8:]  # 去掉 "file_v3_" 前缀
        print(f"  提取的token: {file_token}")
        
        url = f"https://open.feishu.cn/open-apis/drive/v1/files/{file_token}/download"
        response = requests.get(url, headers=headers, allow_redirects=True)
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'json' not in content_type:
                with open(TEMP_PDF_PATH, 'wb') as f:
                    f.write(response.content)
                print(f"  ✓ 下载成功 ({len(response.content)} bytes)")
                return True
            else:
                try:
                    result = response.json()
                    print(f"  JSON响应: {json.dumps(result, indent=2, ensure_ascii=False)[:800]}")
                except:
                    print(f"  响应: {response.text[:500]}")
    
    # 尝试2: 使用完整的file_key
    print("\n[尝试2] 使用完整file_key...")
    url = f"https://open.feishu.cn/open-apis/drive/v1/files/{FILE_KEY}/download"
    response = requests.get(url, headers=headers, allow_redirects=True)
    print(f"  状态码: {response.status_code}")
    
    # 尝试3: 检查是否为资源类型文件
    print("\n[尝试3] 检查文件资源信息...")
    url = "https://open.feishu.cn/open-apis/drive/v1/files"
    params = {"page_size": 50}
    response = requests.get(url, headers=headers, params=params)
    print(f"  状态码: {response.status_code}")
    if response.status_code == 200:
        try:
            result = response.json()
            if result.get("code") == 0:
                files = result.get("data", {}).get("files", [])
                print(f"  找到 {len(files)} 个文件")
                for f in files[:10]:
                    print(f"    - {f.get('name')} ({f.get('token')})")
        except Exception as e:
            print(f"  错误: {e}")
    
    # 尝试4: 尝试使用消息资源下载
    print("\n[尝试4] 尝试作为消息资源下载...")
    # 如果是消息中的文件，可能需要使用不同接口
    url = f"https://open.feishu.cn/open-apis/im/v1/files/{FILE_KEY}"
    response = requests.get(url, headers=headers)
    print(f"  状态码: {response.status_code}")
    if response.status_code == 200:
        try:
            result = response.json()
            print(f"  响应: {json.dumps(result, indent=2, ensure_ascii=False)[:800]}")
        except:
            print(f"  响应: {response.text[:500]}")
    
    return False

def main():
    print("=" * 60)
    print("尝试多种方式获取PDF文件")
    print(f"文件Key: {FILE_KEY}")
    print("=" * 60)
    
    app_id, app_secret = get_feishu_credentials()
    access_token = get_access_token(app_id, app_secret)
    print(f"✓ 已获取访问令牌\n")
    
    success = try_file_operations(access_token)
    
    if success:
        print(f"\n✓ 成功!")
        return True
    else:
        print(f"\n✗ 未能下载文件，可能需要其他权限或接口")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

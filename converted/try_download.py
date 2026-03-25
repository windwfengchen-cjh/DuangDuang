#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""尝试多种方式下载PDF文件"""

import sys
import os
import json
import requests

sys.path.insert(0, '/home/admin/openclaw/workspace')
from feishu_config import get_feishu_credentials

FILE_KEY = "file_v3_00103_3ef15c26-a68b-42ac-ac84-2ac099a9852g"
TEMP_PDF_PATH = "/home/admin/openclaw/workspace/converted/利宝对接文档V1.0.9.pdf"

def get_access_token(app_id, app_secret):
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    response = requests.post(url, json={"app_id": app_id, "app_secret": app_secret})
    return response.json().get("tenant_access_token")

def try_download_methods(access_token):
    """尝试多种下载方式"""
    
    # 方法1: 使用files/download接口
    print("[方法1] 尝试 files/download 接口...")
    url = f"https://open.feishu.cn/open-apis/drive/v1/files/{FILE_KEY}/download"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers, allow_redirects=True)
    print(f"  状态码: {response.status_code}")
    print(f"  Content-Type: {response.headers.get('Content-Type')}")
    
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
                print(f"  响应: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
            except:
                print(f"  响应: {response.text[:500]}")
    
    # 方法2: 使用medias/download接口
    print("\n[方法2] 尝试 medias/download 接口...")
    url = f"https://open.feishu.cn/open-apis/drive/v1/medias/{FILE_KEY}/download"
    response = requests.get(url, headers=headers, allow_redirects=True)
    print(f"  状态码: {response.status_code}")
    print(f"  Content-Type: {response.headers.get('Content-Type')}")
    
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
                print(f"  响应: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
            except:
                print(f"  响应: {response.text[:500]}")
    
    # 方法3: 先获取文件元信息
    print("\n[方法3] 尝试获取文件元信息...")
    url = f"https://open.feishu.cn/open-apis/drive/v1/files/{FILE_KEY}/meta"
    response = requests.get(url, headers=headers)
    print(f"  状态码: {response.status_code}")
    try:
        result = response.json()
        print(f"  响应: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}")
        
        if result.get("code") == 0:
            data = result.get("data", {})
            print(f"\n  文件信息:")
            print(f"    名称: {data.get('name')}")
            print(f"    类型: {data.get('type')}")
            print(f"    Token: {data.get('token')}")
    except Exception as e:
        print(f"  错误: {e}")
    
    return False

def main():
    print("=" * 60)
    print("尝试多种方式下载PDF")
    print("=" * 60)
    
    app_id, app_secret = get_feishu_credentials()
    access_token = get_access_token(app_id, app_secret)
    
    success = try_download_methods(access_token)
    
    if success and os.path.exists(TEMP_PDF_PATH):
        file_size = os.path.getsize(TEMP_PDF_PATH)
        print(f"\n✓ 文件已保存: {TEMP_PDF_PATH} ({file_size} bytes)")
        return True
    else:
        print("\n✗ 所有下载方法均失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

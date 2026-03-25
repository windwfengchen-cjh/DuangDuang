#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""尝试多种file_v3资源下载方式"""

import sys
import os
import json
import requests
import re

sys.path.insert(0, '/home/admin/openclaw/workspace')
from feishu_config import get_feishu_credentials

FILE_KEY = "file_v3_00103_3ef15c26-a68b-42ac-ac84-2ac099a9852g"
TEMP_PDF_PATH = "/home/admin/openclaw/workspace/converted/利宝对接文档V1.0.9.pdf"

def get_access_token(app_id, app_secret):
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    response = requests.post(url, json={"app_id": app_id, "app_secret": app_secret})
    return response.json().get("tenant_access_token")

def download_with_retry(access_token, url, headers, method='GET', data=None):
    """带重试的下载"""
    try:
        if method == 'POST':
            response = requests.post(url, headers=headers, json=data, allow_redirects=True, timeout=30)
        else:
            response = requests.get(url, headers=headers, allow_redirects=True, timeout=30)
        return response
    except Exception as e:
        print(f"  请求错误: {e}")
        return None

def try_all_download_methods(access_token):
    """尝试所有可能的下载方式"""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 解析file_v3: file_v3_<biz_id>_<uuid>
    parts = FILE_KEY.split('_')
    print(f"文件key解析: {parts}")
    
    # 方法1: 使用 /im/v1/resources/{resource_id}
    print("\n[方法1] /im/v1/resources/{resource_id}")
    url = f"https://open.feishu.cn/open-apis/im/v1/resources/{FILE_KEY}"
    response = download_with_retry(access_token, url, headers)
    if response and response.status_code == 200:
        content_type = response.headers.get('Content-Type', '')
        content_len = len(response.content)
        print(f"  状态: 200, 类型: {content_type}, 大小: {content_len}")
        if content_len > 1000 and 'json' not in content_type:
            with open(TEMP_PDF_PATH, 'wb') as f:
                f.write(response.content)
            print(f"  ✓ 下载成功!")
            return True
    elif response:
        print(f"  状态: {response.status_code}")
    
    # 方法2: 使用 /im/v1/files/{file_key}
    print("\n[方法2] /im/v1/files/{file_key}")
    url = f"https://open.feishu.cn/open-apis/im/v1/files/{FILE_KEY}"
    response = download_with_retry(access_token, url, headers)
    if response and response.status_code == 200:
        content_type = response.headers.get('Content-Type', '')
        content_len = len(response.content)
        print(f"  状态: 200, 类型: {content_type}, 大小: {content_len}")
        if content_len > 1000 and 'json' not in content_type:
            with open(TEMP_PDF_PATH, 'wb') as f:
                f.write(response.content)
            print(f"  ✓ 下载成功!")
            return True
    elif response:
        print(f"  状态: {response.status_code}")
    
    # 方法3: 使用 /drive/v1/medias/batch_get_download_url
    print("\n[方法3] /drive/v1/medias/batch_get_download_url")
    url = "https://open.feishu.cn/open-apis/drive/v1/medias/batch_get_download_url"
    data = {
        "file_tokens": [FILE_KEY],
        "extra": json.dumps({})
    }
    response = download_with_retry(access_token, url, {**headers, "Content-Type": "application/json"}, 'POST', data)
    if response and response.status_code == 200:
        try:
            result = response.json()
            print(f"  响应: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}")
            if result.get("code") == 0:
                items = result.get("data", {}).get("items", [])
                if items:
                    download_url = items[0].get("download_url")
                    if download_url:
                        print(f"  获取到下载URL: {download_url[:100]}...")
                        # 下载文件
                        file_response = requests.get(download_url, allow_redirects=True, timeout=60)
                        if file_response.status_code == 200:
                            with open(TEMP_PDF_PATH, 'wb') as f:
                                f.write(file_response.content)
                            print(f"  ✓ 下载成功! ({len(file_response.content)} bytes)")
                            return True
        except Exception as e:
            print(f"  错误: {e}")
    elif response:
        print(f"  状态: {response.status_code}")
        try:
            print(f"  响应: {response.json()}")
        except:
            pass
    
    # 方法4: 使用 /drive/v1/files/{file_token}/download (带类型参数)
    print("\n[方法4] /drive/v1/files/{file_token}/download?type=file")
    url = f"https://open.feishu.cn/open-apis/drive/v1/files/{FILE_KEY}/download?type=file"
    response = download_with_retry(access_token, url, headers)
    if response and response.status_code == 200:
        content_type = response.headers.get('Content-Type', '')
        content_len = len(response.content)
        print(f"  状态: 200, 类型: {content_type}, 大小: {content_len}")
        if content_len > 1000 and 'json' not in content_type:
            with open(TEMP_PDF_PATH, 'wb') as f:
                f.write(response.content)
            print(f"  ✓ 下载成功!")
            return True
        elif 'json' in content_type:
            try:
                print(f"  JSON: {response.json()}")
            except:
                pass
    elif response:
        print(f"  状态: {response.status_code}")
    
    # 方法5: 尝试使用 /open-apis/drive/v1/attachments/{token}
    print("\n[方法5] /drive/v1/attachments/{token}")
    url = f"https://open.feishu.cn/open-apis/drive/v1/attachments/{FILE_KEY}"
    response = download_with_retry(access_token, url, headers)
    if response and response.status_code == 200:
        content_type = response.headers.get('Content-Type', '')
        content_len = len(response.content)
        print(f"  状态: 200, 类型: {content_type}, 大小: {content_len}")
        if content_len > 1000 and 'json' not in content_type:
            with open(TEMP_PDF_PATH, 'wb') as f:
                f.write(response.content)
            print(f"  ✓ 下载成功!")
            return True
    elif response:
        print(f"  状态: {response.status_code}")
    
    return False

def main():
    print("=" * 60)
    print("尝试所有file_v3下载方式")
    print("=" * 60)
    
    app_id, app_secret = get_feishu_credentials()
    access_token = get_access_token(app_id, app_secret)
    print(f"✓ 已获取访问令牌\n")
    
    success = try_all_download_methods(access_token)
    
    if success:
        print(f"\n✓ 下载成功: {TEMP_PDF_PATH}")
        # 显示文件信息
        file_size = os.path.getsize(TEMP_PDF_PATH)
        print(f"  文件大小: {file_size} bytes ({file_size/1024:.1f} KB)")
        # 检查文件头
        with open(TEMP_PDF_PATH, 'rb') as f:
            header = f.read(10)
            print(f"  文件头: {header[:10]}")
            if header.startswith(b'%PDF'):
                print(f"  文件类型: PDF")
        return True
    else:
        print(f"\n✗ 所有下载方式均失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

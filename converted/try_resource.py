#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""尝试通过消息资源接口下载文件"""

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

def try_resource_download(access_token):
    """尝试资源下载接口"""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # file_v3 格式: file_v3_<biz_id>_<uuid>
    # 尝试不同的资源下载方式
    
    # 方法1: 使用附件下载接口
    print("[方法1] 尝试附件下载接口...")
    url = f"https://open.feishu.cn/open-apis/im/v1/attachments/{FILE_KEY}"
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
                print(f"  响应: {json.dumps(result, indent=2, ensure_ascii=False)[:800]}")
            except:
                print(f"  响应: {response.text[:500]}")
    
    # 方法2: 尝试使用资源下载API (针对消息中的文件)
    print("\n[方法2] 尝试资源下载API...")
    # 解析file_v3格式
    parts = FILE_KEY.split('_')
    if len(parts) >= 3:
        # file_v3_00103_uuid -> 提取相关信息
        url = f"https://open.feishu.cn/open-apis/drive/v1/metas/batch_query"
        data = {
            "request_list": [
                {
                    "token": FILE_KEY,
                    "type": "file"
                }
            ]
        }
        response = requests.post(url, headers={**headers, "Content-Type": "application/json"}, json=data)
        print(f"  状态码: {response.status_code}")
        try:
            result = response.json()
            print(f"  响应: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}")
            
            if result.get("code") == 0:
                meta_list = result.get("data", {}).get("metas", [])
                if meta_list:
                    meta = meta_list[0]
                    print(f"\n  文件元信息:")
                    print(f"    名称: {meta.get('name')}")
                    print(f"    类型: {meta.get('type')}")
                    print(f"    Token: {meta.get('token')}")
                    print(f"    Parent Token: {meta.get('parent_token')}")
        except Exception as e:
            print(f"  错误: {e}")
    
    # 方法3: 尝试使用第三方插件下载接口
    print("\n[方法3] 尝试使用通用资源下载...")
    # 有些文件可以通过直接构造URL下载
    # 尝试使用内联下载
    url = f"https://open.feishu.cn/open-apis/drive/v1/files/download?file_token={FILE_KEY}"
    response = requests.get(url, headers=headers, allow_redirects=True)
    print(f"  状态码: {response.status_code}")
    
    if response.status_code == 200:
        content_type = response.headers.get('Content-Type', '')
        print(f"  Content-Type: {content_type}")
        if 'json' not in content_type:
            with open(TEMP_PDF_PATH, 'wb') as f:
                f.write(response.content)
            print(f"  ✓ 下载成功 ({len(response.content)} bytes)")
            return True
        else:
            try:
                result = response.json()
                print(f"  JSON: {json.dumps(result, indent=2, ensure_ascii=False)[:800]}")
            except:
                pass
    
    return False

def main():
    print("=" * 60)
    print("尝试资源下载接口")
    print("=" * 60)
    
    app_id, app_secret = get_feishu_credentials()
    access_token = get_access_token(app_id, app_secret)
    print(f"✓ 已获取访问令牌\n")
    
    success = try_resource_download(access_token)
    
    if success:
        print(f"\n✓ 下载成功: {TEMP_PDF_PATH}")
        return True
    else:
        print(f"\n✗ 所有方法均失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

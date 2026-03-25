#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""尝试通过群消息获取文件"""

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

def try_chat_messages(access_token):
    """尝试通过群消息获取文件"""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 获取群消息历史
    print("[尝试] 获取群消息历史...")
    url = f"https://open.feishu.cn/open-apis/im/v1/messages"
    params = {
        "container_id_type": "chat",
        "container_id": CHAT_ID,
        "page_size": 50
    }
    response = requests.get(url, headers=headers, params=params)
    print(f"  状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        if result.get("code") == 0:
            messages = result.get("data", {}).get("items", [])
            print(f"  找到 {len(messages)} 条消息")
            
            for msg in messages:
                msg_type = msg.get("msg_type", "")
                content = msg.get("body", {}).get("content", "")
                
                # 检查是否包含文件
                if "file" in msg_type or "file_v3" in content or "附件" in content:
                    print(f"\n  找到文件消息:")
                    print(f"    类型: {msg_type}")
                    print(f"    内容: {content[:500] if content else 'N/A'}")
                    print(f"    消息ID: {msg.get('message_id')}")
                    
                    # 尝试解析内容中的文件信息
                    try:
                        content_json = json.loads(content)
                        file_key = content_json.get("file_key") or content_json.get("file_token")
                        if file_key:
                            print(f"    文件Key: {file_key}")
                            if FILE_KEY in file_key or file_key in FILE_KEY:
                                print(f"    ✓ 匹配到目标文件!")
                                return download_file_from_msg(access_token, file_key)
                    except:
                        pass
        else:
            print(f"  错误: {result.get('msg')}")
    else:
        print(f"  错误: {response.text[:500]}")
    
    return False

def download_file_from_msg(access_token, file_key):
    """从消息中下载文件"""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print(f"\n[下载] 尝试下载文件: {file_key}")
    
    # 尝试使用资源下载接口
    url = f"https://open.feishu.cn/open-apis/im/v1/resources/{file_key}"
    response = requests.get(url, headers=headers, allow_redirects=True)
    print(f"  状态码: {response.status_code}")
    
    if response.status_code == 200:
        content_type = response.headers.get('Content-Type', '')
        if 'json' not in content_type and len(response.content) > 1000:
            with open(TEMP_PDF_PATH, 'wb') as f:
                f.write(response.content)
            print(f"  ✓ 下载成功 ({len(response.content)} bytes)")
            return True
    
    # 尝试附件接口
    url = f"https://open.feishu.cn/open-apis/im/v1/attachments/{file_key}"
    response = requests.get(url, headers=headers, allow_redirects=True)
    print(f"  附件接口状态码: {response.status_code}")
    
    if response.status_code == 200:
        content_type = response.headers.get('Content-Type', '')
        if 'json' not in content_type and len(response.content) > 1000:
            with open(TEMP_PDF_PATH, 'wb') as f:
                f.write(response.content)
            print(f"  ✓ 下载成功 ({len(response.content)} bytes)")
            return True
    
    return False

def main():
    print("=" * 60)
    print("尝试通过群消息获取文件")
    print(f"群ID: {CHAT_ID}")
    print("=" * 60)
    
    app_id, app_secret = get_feishu_credentials()
    access_token = get_access_token(app_id, app_secret)
    print(f"✓ 已获取访问令牌\n")
    
    success = try_chat_messages(access_token)
    
    if success:
        print(f"\n✓ 下载成功: {TEMP_PDF_PATH}")
        return True
    else:
        print(f"\n✗ 未能获取文件")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

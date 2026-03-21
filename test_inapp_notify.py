#!/usr/bin/env python3
"""
探索应用内通知API
"""

import json
import os
import ssl
import urllib.request
from typing import Dict, Tuple

OPENCLAW_CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")
TARGET_USER_ID = "ou_d03303783b5538c608b540dc8ad9ac87"

def load_feishu_creds() -> Tuple[str, str]:
    with open(OPENCLAW_CONFIG, 'r') as f:
        config = json.load(f)
        feishu_config = config.get('channels', {}).get('feishu', {})
        return feishu_config.get('appId'), feishu_config.get('appSecret')

def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
        result = json.loads(response.read().decode('utf-8'))
        if result.get('code') != 0:
            raise Exception(f"获取token失败: {result}")
        return result.get('tenant_access_token')

def main():
    print("=" * 80)
    print("应用内通知API探索")
    print("=" * 80)
    
    app_id, app_secret = load_feishu_creds()
    token = get_tenant_access_token(app_id, app_secret)
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # 尝试应用内通知V1 API
    print("\n尝试应用内通知V1 API...")
    url = "https://open.feishu.cn/open-apis/notify/v1/send"
    data = json.dumps({
        "user_id": TARGET_USER_ID,
        "user_id_type": "open_id",
        "content": {
            "tag": "text",
            "text": "测试通知"
        }
    }).encode('utf-8')
    
    req = urllib.request.Request(
        url, data=data,
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"  结果: {result}")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"  HTTP错误 {e.code}: {error_body}")
    
    # 尝试V2 API
    print("\n尝试批量发送API (send_multi_users)...")
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
    data = json.dumps({
        "user_ids": [TARGET_USER_ID],
        "msg_type": "text",
        "content": json.dumps({"text": "测试批量消息"})
    }).encode('utf-8')
    
    req = urllib.request.Request(
        url, data=data,
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"  结果: {result}")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        try:
            error_data = json.loads(error_body)
            print(f"  错误: {error_data.get('code')} - {error_data.get('msg')}")
        except:
            print(f"  HTTP错误 {e.code}: {error_body}")

if __name__ == '__main__':
    main()

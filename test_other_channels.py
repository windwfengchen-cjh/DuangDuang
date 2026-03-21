#!/usr/bin/env python3
"""
探索飞书其他可能的消息渠道
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

def api_request(token: str, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    base_url = "https://open.feishu.cn/open-apis"
    url = f"{base_url}{endpoint}"
    
    if params:
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{url}?{query}"
    
    headers = {'Authorization': f'Bearer {token}'}
    req_data = None
    if data:
        headers['Content-Type'] = 'application/json'
        req_data = json.dumps(data).encode('utf-8')
    
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        try:
            return json.loads(error_body)
        except:
            return {'code': e.code, 'msg': error_body}

def main():
    print("=" * 80)
    print("探索飞书其他可能的消息渠道")
    print("=" * 80)
    
    app_id, app_secret = load_feishu_creds()
    token = get_tenant_access_token(app_id, app_secret)
    print(f"✅ Token获取成功\n")
    
    # 检查是否有群机器人列表
    print("检查群机器人API...")
    result = api_request(token, 'GET', '/im/v1/bots')
    print(f"  结果: {result.get('code')} - {result.get('msg', 'Success')}")
    if result.get('code') == 0:
        bots = result.get('data', {}).get('bots', [])
        print(f"  找到 {len(bots)} 个机器人")
        for bot in bots[:3]:
            print(f"    - {bot.get('bot_name')}")
    print()
    
    # 检查用户是否有手机或邮箱
    print("尝试获取用户联系方式...")
    # 先检查使用user_id能否绕过可用性限制
    # 尝试获取用户的user_id
    result = api_request(token, 'POST', '/contact/v3/users/batch_get_id', {
        "user_ids": [TARGET_USER_ID]
    }, {"user_id_type": "open_id"})
    print(f"  结果: {result.get('code')} - {result.get('msg', 'Success')}")
    print()
    
    # 尝试使用union_id发送消息
    print("尝试获取union_id...")
    if result.get('code') == 0:
        user_list = result.get('data', {}).get('user_list', [])
        if user_list:
            union_id = user_list[0].get('union_id')
            print(f"  Union ID: {union_id}")
            if union_id:
                print(f"  尝试用union_id发送消息...")
                result2 = api_request(token, 'POST', '/im/v1/messages?receive_id_type=union_id', {
                    "receive_id": union_id,
                    "msg_type": "text",
                    "content": json.dumps({"text": "测试"})
                })
                print(f"  结果: {result2.get('code')} - {result2.get('msg', 'Success')}")
    print()
    
    # 尝试email作为receive_id
    print("尝试email作为receive_id...")
    result = api_request(token, 'POST', '/im/v1/messages?receive_id_type=email', {
        "receive_id": "test@example.com",  # 测试email
        "msg_type": "text",
        "content": json.dumps({"text": "测试"})
    })
    print(f"  结果: {result.get('code')} - {result.get('msg', 'Success')}")
    print()
    
    # 检查是否有用户状态API
    print("检查用户状态...")
    result = api_request(token, 'GET', f'/contact/v3/users/{TARGET_USER_ID}', {}, {"user_id_type": "open_id"})
    print(f"  结果: {result.get('code')} - {result.get('msg', 'Success')}")
    
    print("\n" + "=" * 80)
    print("探索完成")
    print("=" * 80)

if __name__ == '__main__':
    main()

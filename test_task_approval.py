#!/usr/bin/env python3
"""
探索飞书待办任务API
检查是否可以创建待办来通知用户
"""

import json
import os
import ssl
import urllib.request
from typing import Dict, Tuple
import time

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

def api_request(token: str, method: str, endpoint: str, data: Dict = None) -> Dict:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = f"https://open.feishu.cn/open-apis{endpoint}"
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
    print("飞书任务/待办API探索")
    print("=" * 80)
    
    app_id, app_secret = load_feishu_creds()
    token = get_tenant_access_token(app_id, app_secret)
    print(f"✅ Token获取成功\n")
    
    # 尝试创建任务
    print("尝试创建任务API...")
    result = api_request(token, 'POST', '/task/v1/tasks', {
        "summary": "【系统通知】有新问题需要处理",
        "description": "这是一条通过任务发送的通知",
        "due": {
            "timestamp": str(int(time.time()) + 86400)  # 明天
        },
        "collaborators": [
            {"id": TARGET_USER_ID, "type": "user"}
        ],
        "follower_ids": [TARGET_USER_ID]
    })
    print(f"  结果: {result.get('code')} - {result.get('msg', 'Success')}")
    if result.get('code') == 0:
        print(f"  ✅ 任务创建成功！这是一个可行的替代方案")
    print()
    
    # 尝试获取审批ID列表
    print("尝试获取审批列表...")
    result = api_request(token, 'GET', '/approval/v1/approvals')
    print(f"  结果: {result.get('code')} - {result.get('msg', 'Success')}")
    print()
    
    # 尝试创建审批实例
    print("尝试创建审批实例...")
    result = api_request(token, 'POST', '/approval/v1/instances', {
        "approval_code": "TEST",
        "user_id": TARGET_USER_ID,
        "user_id_type": "open_id",
        "form": [
            {"name": "问题内容", "value": "测试审批通知"}
        ]
    })
    print(f"  结果: {result.get('code')} - {result.get('msg', 'Success')}")
    print()
    
    # 检查是否有user_access_token方式
    print("检查user_access_token方式...")
    print("  注意：需要使用用户的OAuth授权获取user_access_token")
    print("  这需要用户主动授权，不适合自动化场景")

if __name__ == '__main__':
    main()

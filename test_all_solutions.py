#!/usr/bin/env python3
"""
终极方案探索：尝试所有可能的飞书消息渠道
"""

import json
import os
import ssl
import urllib.request
import urllib.error
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
    """通用API请求"""
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
    print("终极方案探索 - 测试所有可能的飞书消息渠道")
    print("=" * 80)
    
    app_id, app_secret = load_feishu_creds()
    token = get_tenant_access_token(app_id, app_secret)
    print(f"✅ Token获取成功\n")
    
    # 方案1: 直接私聊消息
    print("方案1: 直接私聊消息")
    print("-" * 40)
    result = api_request(token, 'POST', '/im/v1/messages?receive_id_type=open_id', {
        "receive_id": TARGET_USER_ID,
        "msg_type": "text",
        "content": json.dumps({"text": "测试"})
    })
    print(f"  结果: {result.get('code')} - {result.get('msg', 'Success')}")
    if result.get('code') == 230013:
        print(f"  ❌ 用户不在可用性范围内")
    print()
    
    # 方案2: 检查是否有消息卡片相关API
    print("方案2: 通过消息卡片发送")
    print("-" * 40)
    card_content = {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": "系统通知"}},
        "elements": [{"tag": "div", "text": {"tag": "plain_text", "content": "测试消息"}}]
    }
    result = api_request(token, 'POST', '/im/v1/messages?receive_id_type=open_id', {
        "receive_id": TARGET_USER_ID,
        "msg_type": "interactive",
        "content": json.dumps(card_content)
    })
    print(f"  结果: {result.get('code')} - {result.get('msg', 'Success')}")
    print()
    
    # 方案3: 检查应用Feed卡片
    print("方案3: 应用Feed卡片")
    print("-" * 40)
    result = api_request(token, 'POST', '/im/v1/app_feed_cards', {
        "user_id": TARGET_USER_ID,
        "user_id_type": "open_id",
        "content": {
            "tag": "plain_text",
            "content": "测试Feed卡片"
        }
    })
    print(f"  结果: {result.get('code')} - {result.get('msg', 'Success')}")
    if result.get('code') == 0:
        print(f"  ✅ Feed卡片发送成功！这可能是一个可行的替代方案")
    print()
    
    # 方案4: 检查日程创建能力
    print("方案4: 创建日程（是否可以作为通知）")
    print("-" * 40)
    # 需要calendar_id，通常是 primary
    result = api_request(token, 'POST', '/calendar/v4/calendars/primary/events', {
        "summary": "系统通知",
        "description": "这是一条通过日程发送的通知",
        "start_time": {"timestamp": str(int(__import__('time').time()) + 3600)},
        "end_time": {"timestamp": str(int(__import__('time').time()) + 7200)},
        "attendees": [{"type": "user", "user_id": TARGET_USER_ID}]
    })
    print(f"  结果: {result.get('code')} - {result.get('msg', 'Success')}")
    if result.get('code') == 0:
        print(f"  ✅ 日程创建成功！这可能是一个可行的替代方案")
    elif result.get('code') == 222303:
        print(f"  ❌ 被邀请人不存在或不可用")
    print()
    
    # 方案5: 检查是否能创建包含用户的群聊
    print("方案5: 创建群聊并邀请用户")
    print("-" * 40)
    result = api_request(token, 'POST', '/im/v1/chats', {
        "name": "临时通知群",
        "description": "自动创建的通知群",
        "chat_mode": "group",
        "chat_type": "public",
        "user_id_list": [TARGET_USER_ID]
    })
    print(f"  结果: {result.get('code')} - {result.get('msg', 'Success')}")
    if result.get('code') == 0:
        print(f"  ✅ 群聊创建成功！可以在群内发送消息")
    elif result.get('code') == 222303:
        print(f"  ❌ 无法邀请用户 - 用户不在可用性范围内")
    print()
    
    # 方案6: 检查系统消息接口
    print("方案6: 系统消息接口")
    print("-" * 40)
    # im:message:send_sys_msg 权限
    result = api_request(token, 'POST', '/im/v1/messages?receive_id_type=open_id', {
        "receive_id": TARGET_USER_ID,
        "msg_type": "text",
        "content": json.dumps({"text": "测试"}),
        "msg_option": {
            "notification": {
                "notify": True,
                "notify_type": "default"
            }
        }
    })
    print(f"  结果: {result.get('code')} - {result.get('msg', 'Success')}")
    print()
    
    print("=" * 80)
    print("探索完成")
    print("=" * 80)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
测试飞书加急消息功能
检查是否可以在用户不在可用性范围的情况下发送加急通知
"""

import json
import os
import ssl
import urllib.request
import urllib.error
from typing import Dict, Tuple

OPENCLAW_CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")

# 目标用户 (梁思洁)
TARGET_USER_ID = "ou_d03303783b5538c608b540dc8ad9ac87"

def load_feishu_creds() -> Tuple[str, str]:
    """加载飞书凭证"""
    with open(OPENCLAW_CONFIG, 'r') as f:
        config = json.load(f)
        feishu_config = config.get('channels', {}).get('feishu', {})
        return feishu_config.get('appId'), feishu_config.get('appSecret')

def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    """获取 tenant_access_token"""
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

def send_p2p_message(token: str, user_id: str, message: str) -> Dict:
    """发送私聊消息"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
    data = {
        "receive_id": user_id,
        "msg_type": "text",
        "content": json.dumps({"text": message})
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            return {'success': True, 'code': result.get('code'), 'data': result.get('data'), 'raw': result}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        error_data = json.loads(error_body)
        return {'success': False, 'code': error_data.get('code'), 'msg': error_data.get('msg'), 'raw': error_data}

def send_urgent_app(token: str, message_id: str, user_id: str) -> Dict:
    """
    发送应用内加急消息
    注意：需要先发送一条消息，然后对这条消息发起加急
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/urgent_app"
    data = {
        "user_id_list": [user_id]
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        method='PATCH'
    )
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            return {'success': True, 'code': result.get('code'), 'data': result.get('data'), 'raw': result}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        try:
            error_data = json.loads(error_body)
            return {'success': False, 'code': error_data.get('code'), 'msg': error_data.get('msg'), 'raw': error_data}
        except:
            return {'success': False, 'code': e.code, 'msg': error_body}

def send_urgent_sms(token: str, message_id: str, user_id: str) -> Dict:
    """
    发送短信加急消息
    注意：需要先发送一条消息，然后对这条消息发起加急
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/urgent_sms"
    data = {
        "user_id_list": [user_id]
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        method='PATCH'
    )
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            return {'success': True, 'code': result.get('code'), 'data': result.get('data'), 'raw': result}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        try:
            error_data = json.loads(error_body)
            return {'success': False, 'code': error_data.get('code'), 'msg': error_data.get('msg'), 'raw': error_data}
        except:
            return {'success': False, 'code': e.code, 'msg': error_body}

def test_urgent_message():
    """测试加急消息功能"""
    print("=" * 70)
    print("飞书加急消息功能测试")
    print("=" * 70)
    
    # 加载凭证
    app_id, app_secret = load_feishu_creds()
    token = get_tenant_access_token(app_id, app_secret)
    print(f"✅ Token获取成功\n")
    
    # 第1步：先尝试发送普通消息
    print("步骤1: 尝试发送普通私聊消息...")
    message = "【测试】这是一条测试加急功能的基准消息"
    result = send_p2p_message(token, TARGET_USER_ID, message)
    
    if result['success']:
        print(f"✅ 普通消息发送成功！")
        message_id = result['data'].get('message_id')
        print(f"   Message ID: {message_id}\n")
        
        # 第2步：尝试应用内加急
        print("步骤2: 尝试应用内加急...")
        urgent_result = send_urgent_app(token, message_id, TARGET_USER_ID)
        if urgent_result['success']:
            print(f"✅ 应用内加急成功！")
        else:
            print(f"❌ 应用内加急失败")
            print(f"   错误码: {urgent_result.get('code')}")
            print(f"   错误信息: {urgent_result.get('msg')}")
        
        print()
        
        # 第3步：尝试短信加急
        print("步骤3: 尝试短信加急...")
        sms_result = send_urgent_sms(token, message_id, TARGET_USER_ID)
        if sms_result['success']:
            print(f"✅ 短信加急成功！")
        else:
            print(f"❌ 短信加急失败")
            print(f"   错误码: {sms_result.get('code')}")
            print(f"   错误信息: {sms_result.get('msg')}")
    
    else:
        print(f"❌ 普通消息发送失败")
        print(f"   错误码: {result.get('code')}")
        print(f"   错误信息: {result.get('msg')}")
        print(f"\n⚠️ 由于普通消息发送失败，无法进行加急测试")
        print(f"   加急消息的前提是先成功发送一条消息")

if __name__ == '__main__':
    test_urgent_message()

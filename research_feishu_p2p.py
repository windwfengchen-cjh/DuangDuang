#!/usr/bin/env python3
"""
飞书私聊功能深度研究脚本
测试各种API端点和可能的解决方案
"""

import json
import os
import ssl
import urllib.request
from typing import Dict, List, Optional, Tuple

OPENCLAW_CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")

def load_feishu_creds() -> Tuple[Optional[str], Optional[str]]:
    """从 OpenClaw 配置加载飞书凭证"""
    try:
        with open(OPENCLAW_CONFIG, 'r') as f:
            config = json.load(f)
            feishu_config = config.get('channels', {}).get('feishu', {})
            return feishu_config.get('appId'), feishu_config.get('appSecret')
    except Exception as e:
        print(f"Error loading config: {e}")
        return None, None

def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    """获取飞书 tenant_access_token"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({
        "app_id": app_id,
        "app_secret": app_secret
    }).encode('utf-8')
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
        result = json.loads(response.read().decode('utf-8'))
        if result.get('code') != 0:
            raise Exception(f"Failed to get token: {result}")
        return result.get('tenant_access_token')

def api_call(token: str, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
    """通用API调用函数"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    base_url = "https://open.feishu.cn/open-apis"
    url = f"{base_url}{endpoint}"
    
    if params:
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{url}?{query}"
    
    headers = {'Authorization': f'Bearer {token}'}
    
    if data:
        headers['Content-Type'] = 'application/json'
        req_data = json.dumps(data).encode('utf-8')
    else:
        req_data = None
    
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = e.read()
        try:
            error_json = json.loads(error_body.decode('utf-8')) if error_body else {}
        except:
            error_json = {'raw': error_body.decode('utf-8') if error_body else 'empty'}
        return {
            'error': True,
            'status_code': e.code,
            'response': error_json
        }
    except Exception as e:
        return {'error': True, 'message': str(e)}

def test_get_chat_list(token: str) -> None:
    """测试获取聊天列表API"""
    print("\n" + "="*60)
    print("测试1: 获取机器人所在的所有会话列表")
    print("="*60)
    
    # 尝试获取群列表
    result = api_call(token, 'GET', '/im/v1/chats', params={'page_size': '100'})
    
    if result.get('code') == 0:
        items = result.get('data', {}).get('items', [])
        print(f"✅ 成功获取会话列表，共 {len(items)} 个会话")
        for item in items[:5]:  # 只显示前5个
            print(f"  - {item.get('name', 'N/A')} ({item.get('chat_id', 'N/A')})")
            print(f"    类型: {item.get('chat_mode', 'unknown')}")
    else:
        print(f"❌ 获取会话列表失败: {result}")

def test_get_user_chat_id(token: str, user_id: str) -> Optional[str]:
    """
    测试获取用户与机器人的1对1会话ID
    尝试使用 contact 相关接口
    """
    print(f"\n" + "="*60)
    print(f"测试2: 尝试获取用户 {user_id} 与机器人的会话信息")
    print("="*60)
    
    # 方案A: 尝试通过用户ID获取私聊会话
    # 飞书没有直接的API来获取p2p chat_id，但我们可以尝试获取聊天记录
    
    # 尝试获取会话信息
    result = api_call(token, 'GET', f'/im/v1/chats', params={
        'user_id_type': 'open_id',
        'page_size': '100'
    })
    
    print(f"API结果: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
    
    return None

def test_send_p2p_message(token: str, user_id: str) -> Dict:
    """测试发送私聊消息"""
    print(f"\n" + "="*60)
    print(f"测试3: 尝试给用户 {user_id} 发送私聊消息")
    print("="*60)
    
    endpoint = '/im/v1/messages?receive_id_type=open_id'
    data = {
        "receive_id": user_id,
        "msg_type": "text",
        "content": json.dumps({"text": "这是一条测试消息"})
    }
    
    result = api_call(token, 'POST', endpoint, data)
    
    if result.get('code') == 0:
        print(f"✅ 消息发送成功!")
        print(f"   Message ID: {result.get('data', {}).get('message_id')}")
    else:
        print(f"❌ 消息发送失败")
        print(f"   错误码: {result.get('code')}")
        print(f"   错误信息: {result.get('msg', 'Unknown')}")
        print(f"   完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    return result

def test_check_bot_info(token: str) -> None:
    """测试获取机器人自身信息"""
    print(f"\n" + "="*60)
    print("测试4: 获取机器人自身信息")
    print("="*60)
    
    result = api_call(token, 'GET', '/im/v1/bots')
    
    if result.get('code') == 0:
        bot = result.get('data', {}).get('bots', [{}])[0]
        print(f"✅ 获取成功")
        print(f"   Bot名称: {bot.get('bot_name', 'N/A')}")
        print(f"   Bot open_id: {bot.get('open_id', 'N/A')}")
    else:
        print(f"❌ 获取失败: {result}")

def test_search_chats(token: str, query: str = "") -> None:
    """测试搜索群聊"""
    print(f"\n" + "="*60)
    print(f"测试5: 搜索群聊 (query={query or 'all'})")
    print("="*60)
    
    result = api_call(token, 'GET', '/im/v1/chats/search', params={
        'query': query,
        'page_size': '20'
    })
    
    if result.get('code') == 0:
        items = result.get('data', {}).get('items', [])
        print(f"✅ 搜索成功，找到 {len(items)} 个结果")
        for item in items[:5]:
            print(f"  - {item.get('name', 'N/A')} ({item.get('chat_id', 'N/A')})")
    else:
        print(f"❌ 搜索失败: {result}")

def test_create_p2p_chat(token: str, user_id: str) -> None:
    """
    测试创建1对1会话
    飞书API实际上不允许直接创建1对1会话，只能创建群聊
    """
    print(f"\n" + "="*60)
    print(f"测试6: 尝试创建与用户 {user_id} 的1对1会话")
    print("="*60)
    print("注意: 飞书API不直接支持创建1对1会话，只能创建群聊")
    
    # 飞书的chat/create接口只能创建群聊，不能创建1对1会话
    # 1对1会话是在用户首次与机器人互动时自动创建的
    
    endpoint = '/im/v1/chats'
    data = {
        "name": f"P2P_{user_id[:8]}",
        "description": "Test P2P chat",
        "chat_mode": "p2p",  # 尝试设置p2p模式
        "owner_id": user_id
    }
    
    result = api_call(token, 'POST', endpoint, data)
    
    print(f"创建结果: {json.dumps(result, indent=2, ensure_ascii=False)}")

def test_get_message_history(token: str, user_id: str) -> None:
    """测试获取消息历史"""
    print(f"\n" + "="*60)
    print(f"测试7: 尝试获取与用户 {user_id} 的消息历史")
    print("="*60)
    
    # 这个接口需要container_id，对于私聊来说，这个ID很难获取
    endpoint = '/im/v1/messages'
    result = api_call(token, 'GET', endpoint, params={
        'container_id_type': 'open_id',
        'container_id': user_id,
        'page_size': '10'
    })
    
    print(f"结果: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}")

def test_get_user_info(token: str, user_id: str) -> None:
    """测试获取用户信息"""
    print(f"\n" + "="*60)
    print(f"测试8: 获取用户 {user_id} 的详细信息")
    print("="*60)
    
    endpoint = f'/contact/v3/users/{user_id}'
    result = api_call(token, 'GET', endpoint, params={'user_id_type': 'open_id'})
    
    if result.get('code') == 0:
        user = result.get('data', {}).get('user', {})
        print(f"✅ 获取成功")
        print(f"   姓名: {user.get('name', 'N/A')}")
        print(f"   部门: {user.get('department_ids', [])}")
        print(f"   状态: {user.get('status', {}).get('is_activated', 'N/A')}")
    else:
        print(f"❌ 获取失败: {result.get('msg')}")

def main():
    """主函数 - 运行所有测试"""
    print("="*60)
    print("飞书私聊功能深度研究")
    print("="*60)
    
    # 加载凭证
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        print("❌ 无法获取飞书凭证")
        return
    
    print(f"✅ 凭证加载成功")
    
    # 获取token
    token = get_tenant_access_token(app_id, app_secret)
    print(f"✅ Token获取成功: {token[:20]}...")
    
    # 目标用户ID (梁思洁)
    target_user_id = "ou_d03303783b5538c608b540dc8ad9ac87"
    
    # 运行测试
    test_get_chat_list(token)
    test_get_user_chat_id(token, target_user_id)
    result = test_send_p2p_message(token, target_user_id)
    test_check_bot_info(token)
    test_search_chats(token)
    test_create_p2p_chat(token, target_user_id)
    test_get_message_history(token, target_user_id)
    test_get_user_info(token, target_user_id)
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    if result.get('code') == 0:
        print("✅ 可以直接发送私聊消息!")
    else:
        print(f"❌ 无法发送私聊消息")
        print(f"   错误: {result.get('msg', 'Unknown error')}")
        print(f"\n可能的原因:")
        print(f"1. 用户不在应用可用性范围内")
        print(f"2. 缺少 im:message.p2p_msg 权限")
        print(f"3. 用户从未与机器人建立过会话")
        
if __name__ == '__main__':
    main()

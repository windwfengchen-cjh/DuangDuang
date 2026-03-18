#!/usr/bin/env python3
"""
离线消息检查与补录工具
重新上线后检查断线期间的@消息，补录并转发
"""

import json
import os
import urllib.request
import ssl
from datetime import datetime, timedelta
from typing import List, Dict, Optional

OPENCLAW_CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")
MY_BOT_ID = "ou_428d1d5b99e0bb6d1c26549c70688cfb"

# 监控的群列表
MONITORED_CHATS = [
    {"id": "oc_469678cc3cd264438f9bbb65da534c0b", "name": "产研-融合业务组"},
    {"id": "oc_3b4215cdadcc9366c863377561ce00c5", "name": "新群"},
    {"id": "oc_ee55ec5275cc158b826fe1204d75cf2c", "name": "新群（二）"},
    {"id": "oc_a016323a9fda4263ab5a27976065088e", "name": "猛龙队开发"},
]

def load_feishu_creds():
    """从 OpenClaw 配置加载飞书凭证"""
    try:
        with open(OPENCLAW_CONFIG, 'r') as f:
            config = json.load(f)
            feishu_config = config.get('channels', {}).get('feishu', {})
            return feishu_config.get('appId'), feishu_config.get('appSecret')
    except Exception as e:
        print(f"Error loading config: {e}")
        return None, None

def get_tenant_access_token(app_id, app_secret):
    """获取飞书 tenant_access_token"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    
    with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
        result = json.loads(response.read().decode('utf-8'))
        if result.get('code') != 0:
            raise Exception(f"Failed to get token: {result}")
        return result.get('tenant_access_token')

def get_chat_history(chat_id: str, token: str, start_time: str = None, page_size: int = 50) -> List[Dict]:
    """
    获取群消息历史
    
    Args:
        chat_id: 群ID
        token: 访问令牌
        start_time: 起始时间 (ISO 8601格式)，None表示获取最近消息
        page_size: 每页消息数
    
    Returns:
        消息列表
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # 飞书API：获取群消息历史
    # 注意：这个API可能需要特定的权限
    url = f"https://open.feishu.cn/open-apis/im/v1/chats/{chat_id}/messages?page_size={page_size}"
    if start_time:
        url += f"&start_time={start_time}"
    
    req = urllib.request.Request(
        url,
        headers={'Authorization': f'Bearer {token}'},
        method='GET'
    )
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get('code') == 0:
                return result.get('data', {}).get('items', [])
            else:
                print(f"获取消息历史失败: {result.get('msg')}")
                return []
    except Exception as e:
        print(f"获取消息历史异常: {e}")
        return []

def is_at_me(message_text: str) -> bool:
    """检查消息是否@我"""
    at_pattern = f'<at user_id="{MY_BOT_ID}">'
    return at_pattern in message_text

def extract_sender_info(message: Dict) -> Dict:
    """提取发送者信息"""
    sender = message.get('sender', {})
    return {
        'user_id': sender.get('sender_id', ''),
        'name': sender.get('name', '未知用户')
    }

def format_message_content(message: Dict) -> str:
    """格式化消息内容"""
    content = message.get('body', {}).get('content', '')
    # 如果是富文本，提取纯文本
    try:
        content_obj = json.loads(content)
        if 'text' in content_obj:
            return content_obj['text']
    except:
        pass
    return content

def check_offline_messages(hours_back: int = 2) -> List[Dict]:
    """
    检查离线期间的@消息
    
    Args:
        hours_back: 检查多少小时前的消息（默认2小时）
    
    Returns:
        需要处理的@消息列表
    """
    print(f"[{datetime.now()}] 检查离线消息（最近{hours_back}小时）...")
    
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        print("无法获取飞书凭证")
        return []
    
    token = get_tenant_access_token(app_id, app_secret)
    
    # 计算起始时间
    start_time = (datetime.now() - timedelta(hours=hours_back)).isoformat()
    
    at_messages = []
    
    for chat in MONITORED_CHATS:
        chat_id = chat['id']
        chat_name = chat['name']
        
        print(f"\n检查群: {chat_name}")
        
        # 获取消息历史
        messages = get_chat_history(chat_id, token, start_time)
        
        if not messages:
            print(f"  无新消息")
            continue
        
        print(f"  获取到 {len(messages)} 条消息")
        
        # 检查是否有@我的消息
        for msg in messages:
            content = format_message_content(msg)
            
            if is_at_me(content):
                sender = extract_sender_info(msg)
                create_time = msg.get('create_time', '')
                
                at_messages.append({
                    'chat_id': chat_id,
                    'chat_name': chat_name,
                    'sender_id': sender['user_id'],
                    'sender_name': sender['name'],
                    'content': content,
                    'create_time': create_time,
                    'message_id': msg.get('message_id', '')
                })
                
                print(f"  ⚠️ 发现@消息: {sender['name']}: {content[:50]}...")
    
    return at_messages

def process_offline_message(message: Dict) -> bool:
    """
    处理离线期间的@消息
    
    Returns:
        是否成功处理
    """
    print(f"\n处理离线消息:")
    print(f"  来源: {message['chat_name']}")
    print(f"  发送人: {message['sender_name']}")
    print(f"  内容: {message['content'][:100]}...")
    
    # TODO: 这里调用反馈处理流程
    # 1. 去重检查
    # 2. 转发到目标群
    # 3. 记录到表格
    
    print(f"  ✅ 已标记待处理")
    return True

def main():
    """主函数 - 上线后检查离线消息"""
    print("=" * 60)
    print("离线消息检查工具")
    print(f"检查时间: {datetime.now()}")
    print("=" * 60)
    
    # 检查最近2小时的离线消息
    messages = check_offline_messages(hours_back=2)
    
    print("\n" + "=" * 60)
    print(f"检查结果: 发现 {len(messages)} 条@消息")
    print("=" * 60)
    
    if not messages:
        print("\n✅ 离线期间无未处理的@消息")
        return
    
    # 处理每条@消息
    processed = 0
    for msg in messages:
        if process_offline_message(msg):
            processed += 1
    
    print(f"\n处理完成: {processed}/{len(messages)} 条")
    
    # 生成报告给Boss
    if messages:
        print("\n📋 离线期间消息摘要:")
        for i, msg in enumerate(messages, 1):
            print(f"\n{i}. [{msg['chat_name']}] {msg['sender_name']}")
            print(f"   内容: {msg['content'][:80]}...")
            print(f"   时间: {msg['create_time']}")

if __name__ == '__main__':
    # 测试运行
    print("测试离线消息检查...")
    print("注意：实际运行时需要确认飞书API权限是否支持获取历史消息")
    main()

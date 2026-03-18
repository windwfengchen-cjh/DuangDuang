#!/usr/bin/env python3
"""
自动收集联系人信息
从消息事件中提取发送者信息，更新到映射表
"""

import json
import os
from datetime import datetime

CONTACTS_FILE = os.path.expanduser("~/openclaw/workspace/feishu_contacts.json")

def load_contacts():
    """加载联系人映射表"""
    if os.path.exists(CONTACTS_FILE):
        try:
            with open(CONTACTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载联系人失败: {e}")
            return {}
    return {}

def save_contacts(contacts):
    """保存联系人映射表"""
    try:
        with open(CONTACTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(contacts, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存联系人失败: {e}")
        return False

def extract_sender_from_event(event_data: dict) -> dict:
    """
    从消息事件中提取发送者信息
    
    Args:
        event_data: OpenClaw消息事件数据
    
    Returns:
        {"user_id": "xxx", "name": "xxx", "chat_id": "xxx"}
    """
    # 从 inbound 元数据中提取
    sender_id = event_data.get('sender_id', '')
    chat_id = event_data.get('chat_id', '')
    
    # 尝试从事件中获取名称
    # 飞书消息事件中 sender 字段
    sender_info = event_data.get('sender', {})
    
    # 优先从事件中获取名称
    name = None
    
    # 尝试从 event.payload 中获取
    if 'event' in event_data:
        event_payload = event_data.get('event', {})
        sender = event_payload.get('sender', {})
        if isinstance(sender, dict):
            name = sender.get('name') or sender.get('en_name')
    
    # 尝试从 message 中获取
    if not name and 'message' in event_data:
        msg = event_data.get('message', {})
        sender = msg.get('sender', {})
        if isinstance(sender, dict):
            name = sender.get('name') or sender.get('en_name')
    
    # 最后尝试 sender_info
    if not name and isinstance(sender_info, dict):
        name = sender_info.get('name')
    
    return {
        "user_id": sender_id,
        "name": name or sender_id[:8] + "...",  # 如果拿不到名称，用ID缩写
        "chat_id": chat_id
    }

def update_contact_from_message(message_data: dict) -> bool:
    """
    从消息中自动提取并更新联系人
    
    Args:
        message_data: 消息数据，包含各种可能的字段
    
    Returns:
        是否成功更新
    """
    contacts = load_contacts()
    
    # 尝试多种方式提取用户信息
    user_id = None
    user_name = None
    
    # 方式1: 直接从 sender_id 获取
    if 'sender_id' in message_data:
        user_id = message_data['sender_id']
    
    # 方式2: 从 sender.id 获取
    if not user_id and 'sender' in message_data:
        sender = message_data['sender']
        if isinstance(sender, dict):
            user_id = sender.get('id') or sender.get('sender_id')
            user_name = sender.get('name')
    
    # 方式3: 从 event 中获取
    if not user_id and 'event' in message_data:
        event = message_data['event']
        if isinstance(event, dict):
            sender = event.get('sender', {})
            if isinstance(sender, dict):
                user_id = sender.get('sender_id', {}).get('open_id')
                user_name = sender.get('name')
    
    if not user_id:
        return False
    
    # 如果已经有这个用户且已有名称，不覆盖（保留已有的）
    if user_id in contacts and contacts[user_id].get('name') and user_name:
        if contacts[user_id]['name'] != user_id[:8] + "...":
            return False
    
    # 更新或添加联系人
    if user_id not in contacts:
        contacts[user_id] = {}
    
    # 如果有新名称，更新
    if user_name and user_name != user_id:
        contacts[user_id]['name'] = user_name
        contacts[user_id]['role'] = '反馈人'
        contacts[user_id]['source'] = message_data.get('chat_name', '未知来源')
        contacts[user_id]['updated_at'] = datetime.now().isoformat()
        
        if save_contacts(contacts):
            print(f"[Contacts] 新增联系人: {user_name} ({user_id[:20]}...)")
            return True
    
    return False

def get_user_name(user_id: str) -> str:
    """
    根据用户ID获取姓名
    
    Args:
        user_id: 用户Open ID
    
    Returns:
        用户姓名，找不到返回ID缩写
    """
    contacts = load_contacts()
    
    if user_id in contacts:
        name = contacts[user_id].get('name')
        if name and name != user_id:
            return name
    
    return user_id[:8] + "..."

def auto_collect_from_inbound(inbound_meta: dict, inbound_context: dict = None):
    """
    从入站消息中自动收集联系人
    
    Args:
        inbound_meta: 入站元数据（可信）
        inbound_context: 入站上下文（可能包含更多用户信息）
    """
    contacts = load_contacts()
    
    # 提取用户ID
    user_id = inbound_meta.get('sender_id', '')
    if not user_id:
        return
    
    # 如果已存在且不是默认名称，跳过
    if user_id in contacts:
        existing_name = contacts[user_id].get('name', '')
        if existing_name and existing_name != user_id[:8] + "...":
            return
    
    # 尝试从 context 中提取名称
    user_name = None
    if inbound_context:
        # 尝试各种路径
        if 'sender' in inbound_context:
            sender = inbound_context['sender']
            if isinstance(sender, dict):
                user_name = sender.get('name')
        
        if not user_name and 'event' in inbound_context:
            event = inbound_context['event']
            if isinstance(event, dict):
                sender = event.get('sender', {})
                if isinstance(sender, dict):
                    user_name = sender.get('name')
    
    # 如果能获取到名称，更新映射表
    if user_name and user_name != user_id:
        contacts[user_id] = {
            'name': user_name,
            'role': '反馈人',
            'updated_at': datetime.now().isoformat()
        }
        save_contacts(contacts)
        print(f"[Contacts] 自动收集: {user_name} ({user_id[:20]}...)")

if __name__ == '__main__':
    # 测试
    print("测试自动收集联系人...")
    
    # 模拟入站消息
    test_inbound = {
        "sender_id": "ou_test123456789",
        "chat_id": "oc_test987654321",
        "sender": {
            "id": "ou_test123456789",
            "name": "测试用户"
        }
    }
    
    update_contact_from_message(test_inbound)
    
    # 查询名称
    name = get_user_name("ou_test123456789")
    print(f"查询结果: {name}")

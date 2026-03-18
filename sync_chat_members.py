#!/usr/bin/env python3
"""
飞书群成员自动同步工具
被拉入新群后，自动获取群成员信息并更新联系人映射表
"""

import json
import os
import urllib.request
import ssl
from typing import Dict, List

OPENCLAW_CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")
CONTACTS_FILE = "/home/admin/openclaw/workspace/feishu_contacts.json"

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

def get_chat_members(chat_id: str, token: str) -> List[Dict]:
    """获取群成员列表"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    members = []
    page_token = None
    
    while True:
        url = f"https://open.feishu.cn/open-apis/im/v1/chats/{chat_id}/members?page_size=100&member_id_type=open_id"
        if page_token:
            url += f"&page_token={page_token}"
        
        req = urllib.request.Request(
            url,
            headers={'Authorization': f'Bearer {token}'},
            method='GET'
        )
        
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if result.get('code') != 0:
                    print(f"获取群成员失败: {result.get('msg')}")
                    break
                
                data = result.get('data', {})
                items = data.get('items', [])
                
                for item in items:
                    member_id = item.get('member_id')
                    if member_id:
                        members.append({
                            'user_id': member_id,
                            'member_type': item.get('member_type', 'user')
                        })
                
                page_token = data.get('page_token')
                has_more = data.get('has_more', False)
                
                if not has_more or not page_token:
                    break
        except Exception as e:
            print(f"获取群成员异常: {e}")
            break
    
    return members

def get_user_info(user_id: str, token: str) -> Dict:
    """获取用户详细信息"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = f"https://open.feishu.cn/open-apis/contact/v3/users/{user_id}?user_id_type=open_id"
    req = urllib.request.Request(
        url,
        headers={'Authorization': f'Bearer {token}'},
        method='GET'
    )
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get('code') == 0:
                return result.get('data', {}).get('user', {})
            else:
                return {}
    except Exception as e:
        print(f"获取用户信息失败 {user_id}: {e}")
        return {}

def load_contacts() -> Dict:
    """加载现有联系人映射表"""
    if not os.path.exists(CONTACTS_FILE):
        return {}
    
    with open(CONTACTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_contacts(contacts: Dict):
    """保存联系人映射表"""
    with open(CONTACTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(contacts, f, ensure_ascii=False, indent=2)

def sync_chat_members(chat_id: str, chat_name: str = ""):
    """
    同步指定群的成员到联系人映射表
    
    Args:
        chat_id: 群聊ID (oc_xxx)
        chat_name: 群名称（可选，用于日志）
    """
    print(f"开始同步群成员: {chat_name or chat_id}")
    
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        print("❌ 无法获取飞书凭证")
        return False
    
    token = get_tenant_access_token(app_id, app_secret)
    print("✅ 获取访问令牌成功")
    
    # 获取群成员
    members = get_chat_members(chat_id, token)
    print(f"✅ 获取到 {len(members)} 位群成员")
    
    # 加载现有联系人
    contacts = load_contacts()
    existing_count = len(contacts)
    
    # 获取每个成员的详细信息
    new_count = 0
    update_count = 0
    
    for member in members:
        user_id = member.get('user_id')
        if not user_id:
            continue
        
        # 如果已存在且已有姓名，跳过
        if user_id in contacts and contacts[user_id].get('name'):
            continue
        
        # 获取用户详细信息
        user_info = get_user_info(user_id, token)
        
        if user_info:
            name = user_info.get('name', '')
            en_name = user_info.get('en_name', '')
            
            if name:
                if user_id in contacts:
                    update_count += 1
                else:
                    new_count += 1
                
                contacts[user_id] = {
                    'name': name,
                    'en_name': en_name,
                    'role': contacts.get(user_id, {}).get('role', ''),  # 保留现有角色
                    'source': chat_name or chat_id  # 记录来源群
                }
    
    # 保存更新后的映射表
    save_contacts(contacts)
    
    print(f"✅ 同步完成!")
    print(f"   原有: {existing_count} 人")
    print(f"   新增: {new_count} 人")
    print(f"   更新: {update_count} 人")
    print(f"   现有: {len(contacts)} 人")
    
    return True

def sync_all_known_chats():
    """同步所有已知群的成员"""
    # 已知的群列表
    chats = [
        {"id": "oc_469678cc3cd264438f9bbb65da534c0b", "name": "产研-融合业务组"},
        {"id": "oc_a016323a9fda4263ab5a27976065088e", "name": "猛龙队开发"},
    ]
    
    print("开始同步所有已知群的成员...\n")
    
    for chat in chats:
        print(f"\n{'='*50}")
        sync_chat_members(chat['id'], chat['name'])
    
    print(f"\n{'='*50}")
    print("所有群同步完成!")
    
    # 显示当前映射表
    print("\n当前联系人映射表:")
    contacts = load_contacts()
    for user_id, info in sorted(contacts.items(), key=lambda x: x[1].get('name', '')):
        name = info.get('name', '')
        role = info.get('role', '')
        source = info.get('source', '')
        print(f"  {name:<10} {user_id:<50} {role:<10} {source}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        # 同步指定群
        chat_id = sys.argv[1]
        chat_name = sys.argv[2] if len(sys.argv) > 2 else ""
        sync_chat_members(chat_id, chat_name)
    else:
        # 同步所有已知群
        sync_all_known_chats()

#!/usr/bin/env python3
"""
飞书通讯录同步工具
获取所有联系人的ID和姓名，建立映射表
"""

import json
import os
import urllib.request
import ssl
from typing import Dict, List

OPENCLAW_CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")
OUTPUT_FILE = "/home/admin/openclaw/workspace/feishu_contacts.json"

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

def get_all_users(token: str) -> List[Dict]:
    """获取所有用户列表"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    all_users = []
    page_token = None
    
    while True:
        url = "https://open.feishu.cn/open-apis/contact/v3/users?department_id_type=open_department_id&user_id_type=open_id&page_size=50"
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
                    print(f"API 错误: {result}")
                    break
                
                data = result.get('data', {})
                users = data.get('items', [])
                all_users.extend(users)
                
                page_token = data.get('page_token')
                has_more = data.get('has_more', False)
                
                print(f"已获取 {len(users)} 条，总计 {len(all_users)} 条")
                
                if not has_more or not page_token:
                    break
        except Exception as e:
            print(f"获取用户失败: {e}")
            break
    
    return all_users

def build_contacts_map(users: List[Dict]) -> Dict:
    """构建联系人映射表"""
    contacts = {}
    
    for user in users:
        user_id = user.get('open_id') or user.get('user_id')
        name = user.get('name', '')
        en_name = user.get('en_name', '')
        email = user.get('email', '')
        
        if user_id and name:
            contacts[user_id] = {
                'name': name,
                'en_name': en_name,
                'email': email,
                'user_id': user_id
            }
    
    return contacts

def save_contacts(contacts: Dict, filepath: str):
    """保存联系人到JSON文件"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(contacts, f, ensure_ascii=False, indent=2)
    print(f"✅ 联系人已保存到: {filepath}")

def load_contacts(filepath: str) -> Dict:
    """从JSON文件加载联系人"""
    if not os.path.exists(filepath):
        return {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_user_name(user_id: str, contacts: Dict = None) -> str:
    """
    根据user_id获取用户姓名
    
    Args:
        user_id: 用户open_id
        contacts: 联系人映射表（可选，不传则自动加载）
    
    Returns:
        用户姓名，找不到则返回空字符串
    """
    if contacts is None:
        contacts = load_contacts(OUTPUT_FILE)
    
    user = contacts.get(user_id, {})
    return user.get('name', '')

def sync_contacts():
    """同步通讯录主函数"""
    print("开始同步飞书通讯录...")
    
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        print("❌ 无法获取飞书凭证")
        return False
    
    token = get_tenant_access_token(app_id, app_secret)
    print("✅ 获取访问令牌成功")
    
    users = get_all_users(token)
    print(f"✅ 共获取 {len(users)} 位用户")
    
    contacts = build_contacts_map(users)
    print(f"✅ 构建映射表完成，共 {len(contacts)} 条记录")
    
    save_contacts(contacts, OUTPUT_FILE)
    
    # 显示部分示例
    print("\n部分联系人示例:")
    for i, (uid, info) in enumerate(list(contacts.items())[:5]):
        print(f"  {uid}: {info['name']}")
    
    return True

def add_contact(user_id: str, name: str, role: str = "", description: str = ""):
    """
    手动添加联系人到映射表
    
    Args:
        user_id: 用户open_id
        name: 用户姓名
        role: 角色（如"处理人"、"Boss"）
        description: 描述
    """
    contacts = load_contacts(OUTPUT_FILE)
    
    contacts[user_id] = {
        'name': name,
        'role': role,
        'description': description
    }
    
    save_contacts(contacts, OUTPUT_FILE)
    print(f"✅ 已添加联系人: {name} ({user_id})")

def list_contacts():
    """列出所有联系人"""
    contacts = load_contacts(OUTPUT_FILE)
    
    print(f"\n共有 {len(contacts)} 位联系人:\n")
    print(f"{'Open ID':<50} {'姓名':<10} {'角色':<10}")
    print("-" * 70)
    
    for user_id, info in contacts.items():
        name = info.get('name', '')
        role = info.get('role', '')
        print(f"{user_id:<50} {name:<10} {role:<10}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'list':
            list_contacts()
        elif command == 'add' and len(sys.argv) >= 4:
            user_id = sys.argv[2]
            name = sys.argv[3]
            role = sys.argv[4] if len(sys.argv) > 4 else ""
            desc = sys.argv[5] if len(sys.argv) > 5 else ""
            add_contact(user_id, name, role, desc)
        else:
            print("用法:")
            print("  python3 sync_feishu_contacts.py           # 同步通讯录")
            print("  python3 sync_feishu_contacts.py list      # 列出联系人")
            print("  python3 sync_feishu_contacts.py add <user_id> <name> [role] [desc]")
    else:
        # 默认执行同步
        sync_contacts()

#!/usr/bin/env python3
"""
重复反馈检测工具
检查表格中是否已存在相同用户的相似问题
"""

import json
import os
import urllib.request
import ssl
from typing import Dict, Optional, List
from difflib import SequenceMatcher

OPENCLAW_CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")
CONTACTS_FILE = os.path.expanduser("~/openclaw/workspace/feishu_contacts.json")
APP_TOKEN = "KNiibDP6KaRwopsPbRucr752ntg"
TABLE_ID = "tblyDHrGGTQTaex6"

def load_contacts() -> dict:
    """加载联系人映射表"""
    if os.path.exists(CONTACTS_FILE):
        try:
            with open(CONTACTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载联系人失败: {e}")
            return {}
    return {}

def get_user_name(user_id: str) -> str:
    """根据user_id获取姓名"""
    contacts = load_contacts()
    return contacts.get(user_id, {}).get('name', '')

def get_user_id_by_name(name: str) -> str:
    """根据姓名查找user_id（反向查找）"""
    contacts = load_contacts()
    for uid, info in contacts.items():
        if info.get('name') == name:
            return uid
    return ''

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

def get_all_records(token: str) -> List[Dict]:
    """获取表格中所有记录"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    all_records = []
    page_token = None
    
    while True:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records?page_size=500"
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
                records = data.get('items', [])
                all_records.extend(records)
                
                page_token = data.get('page_token')
                has_more = data.get('has_more', False)
                
                if not has_more or not page_token:
                    break
        except Exception as e:
            print(f"获取记录失败: {e}")
            break
    
    return all_records

def extract_user_id(record: Dict) -> str:
    """从记录中提取反馈人ID"""
    fields = record.get('fields', {})
    
    # 尝试从处理人字段提取（如果有）
    feedback_user = fields.get('反馈人', '')
    
    # 如果是对象，提取id
    if isinstance(feedback_user, dict):
        return feedback_user.get('id', '')
    elif isinstance(feedback_user, list) and len(feedback_user) > 0:
        if isinstance(feedback_user[0], dict):
            return feedback_user[0].get('id', '')
    
    return str(feedback_user)

def extract_content(record: Dict) -> str:
    """从记录中提取问题内容"""
    fields = record.get('fields', {})
    return fields.get('问题内容', '') or fields.get('业务反馈问题记录表', '')

def extract_status(record: Dict) -> str:
    """从记录中提取处理状态"""
    fields = record.get('fields', {})
    status = fields.get('处理状态', '')
    if isinstance(status, list) and len(status) > 0:
        return status[0].get('text', '') if isinstance(status[0], dict) else str(status[0])
    return str(status)

def calculate_similarity(text1: str, text2: str) -> float:
    """计算两个文本的相似度（0-1）"""
    if not text1 or not text2:
        return 0.0
    
    # 使用SequenceMatcher计算相似度
    return SequenceMatcher(None, text1, text2).ratio()

def check_duplicate(user_id: str, content: str, similarity_threshold: float = 0.8) -> Optional[Dict]:
    """
    检查是否存在重复反馈
    
    Args:
        user_id: 反馈人ID (ou_xxx)
        content: 问题内容
        similarity_threshold: 相似度阈值（默认0.8）
    
    Returns:
        如果存在重复，返回重复的记录信息；否则返回None
    """
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        print("❌ 无法获取飞书凭证")
        return None
    
    token = get_tenant_access_token(app_id, app_secret)
    records = get_all_records(token)
    
    # 将传入的user_id转换为姓名（用于和表格中的姓名比较）
    user_name = get_user_name(user_id)
    
    # 遍历所有记录，检查是否重复
    for record in records:
        record_id = record.get('record_id', '')
        fields = record.get('fields', {})
        
        # 提取记录中的反馈人（可能是姓名或ID）
        record_user = extract_user_id(record)
        
        # 尝试将记录中的反馈人转换为ID（如果是姓名）
        record_user_id = get_user_id_by_name(record_user) if record_user and not record_user.startswith('ou_') else record_user
        
        # 匹配逻辑：ID相同 或 姓名相同
        is_same_user = False
        if record_user_id == user_id:  # ID匹配
            is_same_user = True
        elif user_name and record_user == user_name:  # 姓名匹配
            is_same_user = True
        
        # 如果反馈人不同，跳过
        if not is_same_user:
            continue
        
        # 提取处理状态
        status = extract_status(record)
        
        # 如果状态是已解决/已关闭，视为新问题
        if status in ['已解决', '已关闭']:
            continue
        
        # 提取问题内容
        record_content = extract_content(record)
        
        # 计算相似度
        similarity = calculate_similarity(content, record_content)
        
        if similarity >= similarity_threshold:
            return {
                'record_id': record_id,
                'content': record_content,
                'status': status,
                'similarity': similarity,
                'fields': fields
            }
    
    return None

def should_record_feedback(user_id: str, content: str) -> bool:
    """
    判断是否应该记录该反馈
    
    Returns:
        True - 应该记录（非重复问题）
        False - 不应记录（重复问题）
    """
    duplicate = check_duplicate(user_id, content)
    
    if duplicate:
        print(f"⚠️ 发现重复反馈（相似度: {duplicate['similarity']:.1%}）")
        print(f"   现有记录: {duplicate['content'][:50]}...")
        print(f"   处理状态: {duplicate['status']}")
        return False
    
    return True

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) >= 3:
        user_id = sys.argv[1]
        content = sys.argv[2]
        
        print(f"检查重复反馈...")
        print(f"用户: {user_id}")
        print(f"内容: {content[:50]}...")
        print()
        
        duplicate = check_duplicate(user_id, content)
        
        if duplicate:
            print(f"❌ 重复反馈，无需记录")
            print(f"   相似度: {duplicate['similarity']:.1%}")
            print(f"   现有记录状态: {duplicate['status']}")
        else:
            print(f"✅ 非重复问题，可以记录")
    else:
        print("用法: python3 check_duplicate.py <user_id> <content>")
        print("\n测试示例:")
        print('  python3 check_duplicate.py "ou_xxx" "登录页面报错"')

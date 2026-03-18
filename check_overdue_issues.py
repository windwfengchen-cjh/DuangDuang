#!/usr/bin/env python3
"""
问题超时催促检查器
- 每小时检查一次表格
- 发现超过1小时未处理的问题，在目标群催促
"""

import json
import os
import sys
import urllib.request
import ssl
from datetime import datetime, timedelta

# 配置
OPENCLAW_CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")
BITABLE_APP_TOKEN = "KNiibDP6KaRwopsPbRucr752ntg"
BITABLE_TABLE_ID = "tblyDHrGGTQTaex6"

# 目标群 - 猛龙队开发
TARGET_CHAT_ID = "oc_a016323a9fda4263ab5a27976065088e"

# 处理人
HANDLERS = [
    {"user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "施嘉科"},
    {"user_id": "ou_cbcd1090961b620a4500ce68e3c81952", "user_name": "宋广智"}
]

# 需求关键词（用于识别需求类，超时提醒会跳过）
NEED_KEYWORDS = ['需求', '建议', '优化', '改进', '新增', '增加', '功能', '想要', '希望', '能否']

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

def get_pending_records():
    """获取所有待处理的记录"""
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        return []
    
    token = get_tenant_access_token(app_id, app_secret)
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    all_records = []
    page_token = None
    
    while True:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/records?page_size=500"
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
                if not page_token or not data.get('has_more'):
                    break
        except Exception as e:
            print(f"获取记录失败: {e}")
            break
    
    return all_records

def parse_datetime(value):
    """解析日期时间"""
    if isinstance(value, int):
        # 毫秒时间戳
        return datetime.fromtimestamp(value / 1000)
    elif isinstance(value, str):
        # 尝试多种格式
        formats = ['%Y/%m/%d %H:%M', '%Y/%m/%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except:
                continue
    return None

def is_need_type(content):
    """判断是否是需求/建议类"""
    if not content:
        return False
    content_lower = content.lower()
    return any(kw in content_lower for kw in NEED_KEYWORDS)

def find_overdue_issues(records, hours=1):
    """找出超过指定小时数未处理的问题（只检查Bug/问题类，需求类不提醒）"""
    now = datetime.now()
    threshold = timedelta(hours=hours)
    
    overdue = []
    
    for record in records:
        fields = record.get('fields', {})
        
        # 只检查待处理的问题
        status = fields.get('处理状态', '')
        if status not in ['待处理']:
            continue
        
        # 获取反馈时间
        feedback_time = fields.get('反馈时间', '')
        dt = parse_datetime(feedback_time)
        
        if not dt:
            continue
        
        # 检查是否超过阈值
        elapsed = now - dt
        if elapsed >= threshold:
            content = fields.get('问题内容', '')
            
            # 跳过需求类（需求不需要超时提醒）
            if is_need_type(content):
                continue
            
            overdue.append({
                'record_id': record.get('record_id'),
                '问题简述': fields.get('业务反馈问题记录表', '无标题'),
                '反馈人': fields.get('反馈人', '未知'),
                '反馈来源': fields.get('反馈来源', '未知'),
                '问题内容': content,
                '反馈时间': dt.strftime('%Y-%m-%d %H:%M'),
                '已超时': f"{elapsed.total_seconds() // 3600:.0f}小时{(elapsed.total_seconds() % 3600) // 60:.0f}分钟"
            })
    
    return overdue

def send_reminder_chat(issues):
    """在目标群发送催促消息（只针对Bug/问题类）"""
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        print("无法获取飞书凭证")
        return False
    
    token = get_tenant_access_token(app_id, app_secret)
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # 构造消息内容
    lines = [
        f"⏰ **问题超时提醒**",
        f"",
        f"以下问题已超过1小时未处理，请尽快响应：",
        f"",
    ]
    
    for i, issue in enumerate(issues, 1):
        lines.append(f"{i}. **{issue['问题简述']}**")
        lines.append(f"   反馈人：{issue['反馈人']} | 来源：{issue['反馈来源']}")
        lines.append(f"   时间：{issue['反馈时间']}（已超时 {issue['已超时']}）")
        lines.append(f"")
    
    content_text = "\n".join(lines)
    
    # 构造 post 消息
    content_blocks = [[{"tag": "text", "text": content_text}]]
    
    # 添加 @ 处理人
    at_paragraph = [{"tag": "text", "text": "请处理："}]
    for handler in HANDLERS:
        at_paragraph.append({
            "tag": "at",
            "user_id": handler["user_id"],
            "user_name": handler["user_name"]
        })
        at_paragraph.append({"tag": "text", "text": " "})
    content_blocks.append(at_paragraph)
    
    message_content = {
        "zh_cn": {
            "title": "⏰ 问题超时提醒",
            "content": content_blocks
        }
    }
    
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    payload = {
        "receive_id": TARGET_CHAT_ID,
        "msg_type": "post",
        "content": json.dumps(message_content, ensure_ascii=False)
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get('code') == 0:
                return True
            else:
                print(f"发送失败: {result}")
                return False
    except Exception as e:
        print(f"发送异常: {e}")
        return False

def main():
    print(f"[{datetime.now()}] 开始检查超时问题...")
    
    # 获取所有记录
    records = get_pending_records()
    print(f"共获取 {len(records)} 条记录")
    
    # 找出超时问题
    overdue_issues = find_overdue_issues(records, hours=1)
    print(f"发现 {len(overdue_issues)} 条超时问题")
    
    if overdue_issues:
        # 发送催促消息
        success = send_reminder_chat(overdue_issues)
        if success:
            print(f"[{datetime.now()}] 催促消息发送成功")
        else:
            print(f"[{datetime.now()}] 催促消息发送失败")
    else:
        print(f"[{datetime.now()}] 无超时问题，无需催促")

if __name__ == '__main__':
    main()

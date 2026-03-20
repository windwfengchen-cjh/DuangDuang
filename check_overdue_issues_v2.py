#!/usr/bin/env python3
"""
问题超时催促检查器 (增强版)
- 每小时检查一次表格
- 超过1小时未处理的Bug/问题：在目标群催促
- 超过3天未处理的反馈：私聊提醒主人
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

# 主人ID (Boss - 陈俊洪)
MASTER_USER_ID = "ou_3e48baef1bd71cc89fb5a364be55cafc"

# 处理人
HANDLERS = [
    {"user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "施嘉科"},
    {"user_id": "ou_cbcd1090961b620a4500ce68e3c81952", "user_name": "宋广智"}
]

# 需求关键词（用于识别需求类，1小时超时提醒会跳过）
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
        return datetime.fromtimestamp(value / 1000)
    elif isinstance(value, str):
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

def find_overdue_issues_1h(records):
    """找出超过1小时未处理的Bug/问题（需求类不提醒）"""
    now = datetime.now()
    overdue = []
    
    for record in records:
        fields = record.get('fields', {})
        status = fields.get('处理状态', '')
        if status not in ['待处理']:
            continue
        
        feedback_time = fields.get('反馈时间', '')
        dt = parse_datetime(feedback_time)
        if not dt:
            continue
        
        elapsed = now - dt
        if timedelta(hours=1) <= elapsed < timedelta(days=3):
            content = fields.get('问题内容', '')
            if is_need_type(content):
                continue
            
            overdue.append({
                'record_id': record.get('record_id'),
                '问题简述': fields.get('业务反馈问题记录表', '无标题'),
                '反馈人': fields.get('反馈人', '未知'),
                '反馈来源': fields.get('反馈来源', '未知'),
                '问题内容': content,
                '反馈时间': dt.strftime('%Y-%m-%d %H:%M'),
                '已超时': f"{elapsed.total_seconds() // 3600:.0f}小时{(elapsed.total_seconds() % 3600) // 60:.0f}分钟",
            })
    return overdue

def find_overdue_issues_3d(records):
    """找出超过3天未处理的反馈（包括问题和需求，私聊提醒主人）"""
    now = datetime.now()
    threshold = timedelta(days=3)
    overdue = []
    
    for record in records:
        fields = record.get('fields', {})
        status = fields.get('处理状态', '')
        if status not in ['待处理', '处理中']:
            continue
        
        feedback_time = fields.get('反馈时间', '')
        dt = parse_datetime(feedback_time)
        if not dt:
            continue
        
        elapsed = now - dt
        if elapsed >= threshold:
            record_type = fields.get('类型', '问题')
            overdue.append({
                'record_id': record.get('record_id'),
                '问题简述': fields.get('业务反馈问题记录表', '无标题'),
                '类型': record_type,
                '反馈人': fields.get('反馈人', '未知'),
                '处理人': fields.get('处理人', []),
                '处理状态': status,
                '问题内容': fields.get('问题内容', '')[:100] + '...' if len(fields.get('问题内容', '')) > 100 else fields.get('问题内容', ''),
                '反馈时间': dt.strftime('%Y-%m-%d %H:%M'),
                '已超时': f"{elapsed.days}天 {elapsed.seconds // 3600}小时",
                'elapsed_days': elapsed.days
            })
    
    overdue.sort(key=lambda x: x['elapsed_days'], reverse=True)
    return overdue

def send_reminder_chat(issues):
    """在目标群发送1小时催促消息"""
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        return False
    
    token = get_tenant_access_token(app_id, app_secret)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    lines = [f"⏰ **问题超时提醒**", "", f"以下问题已超过1小时未处理，请尽快响应：", ""]
    for i, issue in enumerate(issues, 1):
        lines.append(f"{i}. **{issue['问题简述']}**")
        lines.append(f"   反馈人：{issue['反馈人']} | 来源：{issue['反馈来源']}")
        lines.append(f"   时间：{issue['反馈时间']}（已超时 {issue['已超时']}）")
        lines.append("")
    
    content_blocks = [[{"tag": "text", "text": "\n".join(lines)}]]
    at_paragraph = [{"tag": "text", "text": "请处理："}]
    for handler in HANDLERS:
        at_paragraph.append({"tag": "at", "user_id": handler["user_id"], "user_name": handler["user_name"]})
        at_paragraph.append({"tag": "text", "text": " "})
    content_blocks.append(at_paragraph)
    
    message_content = {"zh_cn": {"title": "⏰ 问题超时提醒", "content": content_blocks}}
    
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    payload = {
        "receive_id": TARGET_CHAT_ID,
        "msg_type": "post",
        "content": json.dumps(message_content, ensure_ascii=False)
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}, method='POST')
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('code') == 0
    except Exception as e:
        print(f"发送异常: {e}")
        return False

def get_handler_names(handler_list):
    """获取处理人姓名列表"""
    if not handler_list:
        return '未分配'
    handler_map = {
        'ou_82e152d737ab5aedee7110066828b5a1': '施嘉科',
        'ou_cbcd1090961b620a4500ce68e3c81952': '宋广智',
        'ou_3e48baef1bd71cc89fb5a364be55cafc': '陈俊洪',
    }
    names = []
    for h in handler_list:
        if isinstance(h, dict):
            uid = h.get('id', '')
            name = h.get('name', '') or handler_map.get(uid, uid[:8] if uid else '未知')
            names.append(name)
        elif isinstance(h, str):
            names.append(handler_map.get(h, h[:8]))
    return '、'.join(names) if names else '未分配'

def send_private_reminder_to_master(issues):
    """私聊提醒主人超过3天未处理的反馈"""
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        return False
    
    token = get_tenant_access_token(app_id, app_secret)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    lines = [f"🚨 **严重超时提醒**", "", f"以下 {len(issues)} 条反馈已超过3天未处理完毕，需要您关注和督办：", ""]
    for i, issue in enumerate(issues, 1):
        lines.append(f"{i}. 【{issue['类型']}】{issue['问题简述']}")
        lines.append(f"   状态：{issue['处理状态']} | 反馈人：{issue['反馈人']}")
        lines.append(f"   处理人：{get_handler_names(issue['处理人'])}")
        lines.append(f"   反馈时间：{issue['反馈时间']}（已超时 **{issue['已超时']}**）")
        if issue['问题内容']:
            lines.append(f"   内容：{issue['问题内容']}")
        lines.append("")
    lines.append("-" * 40)
    lines.append("📎 查看完整表格：https://gz-junbo.feishu.cn/base/KNiibDP6KaRwopsPbRucr752ntg")
    
    content_text = "\n".join(lines)
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
    payload = {
        "receive_id": MASTER_USER_ID,
        "msg_type": "text",
        "content": json.dumps({"text": content_text}, ensure_ascii=False)
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}, method='POST')
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('code') == 0
    except Exception as e:
        print(f"发送异常: {e}")
        return False

def main():
    print(f"[{datetime.now()}] 开始检查超时问题...")
    
    records = get_pending_records()
    print(f"共获取 {len(records)} 条记录")
    
    # 1. 检查1小时超时（群提醒）
    overdue_1h = find_overdue_issues_1h(records)
    print(f"发现 {len(overdue_1h)} 条超过1小时未处理的Bug/问题")
    if overdue_1h:
        success = send_reminder_chat(overdue_1h)
        print(f"[{datetime.now()}] 1小时群提醒发送{'成功' if success else '失败'}")
    
    # 2. 检查3天超时（私聊提醒主人）
    overdue_3d = find_overdue_issues_3d(records)
    print(f"发现 {len(overdue_3d)} 条超过3天未处理的反馈")
    if overdue_3d:
        success = send_private_reminder_to_master(overdue_3d)
        print(f"[{datetime.now()}] 3天私聊提醒发送{'成功' if success else '失败'}")
    
    print(f"[{datetime.now()}] 检查完成")

if __name__ == '__main__':
    main()

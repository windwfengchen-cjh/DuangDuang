#!/usr/bin/env python3
"""
状态更新处理器
处理开发群@我的消息，更新表格状态
只处理被@的消息，不主动监听所有消息
"""

import json
import os
import urllib.request
import ssl
import re
from typing import Optional, Dict, Tuple
from datetime import datetime

OPENCLAW_CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")
APP_TOKEN = "KNiibDP6KaRwopsPbRucr752ntg"
TABLE_ID = "tblyDHrGGTQTaex6"

# 我的Bot ID
MY_BOT_ID = "ou_428d1d5b99e0bb6d1c26549c70688cfb"

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

def is_at_me(message_text: str) -> bool:
    """检查消息是否@我"""
    at_pattern = f'<at user_id="{MY_BOT_ID}">'
    return at_pattern in message_text

def remove_at_tags(message_text: str) -> str:
    """移除消息中的@标签"""
    cleaned = re.sub(r'<at[^>]*>[^<]*</at>', '', message_text)
    cleaned = ' '.join(cleaned.split())
    return cleaned.strip()

def extract_status_and_result(message_text: str) -> Tuple[Optional[str], str]:
    """
    从消息中提取处理状态
    
    Returns:
        (status, result_text) 状态可能为None
    """
    status_keywords = {
        "已解决": "已解决",
        "已完成": "已解决",
        "搞定": "已解决",
        "已修复": "已解决",
        "ok": "已解决",
        "OK": "已解决",
        "已处理": "已解决",
        "解决了": "已解决",
        "完成了": "已解决",
        "处理好了": "已解决",
        "同步好了": "已解决",
        "已上线": "已解决",
        "上线": "已解决",
        "已关闭": "已关闭",
        "无需处理": "已关闭",
        "重复问题": "已关闭",
        "处理中": "处理中",
        "正在处理": "处理中",
        "跟进中": "处理中",
        "待处理": "待处理"
    }
    
    for keyword, status in status_keywords.items():
        if keyword in message_text:
            # 提取完整句子
            sentences = re.split(r'[。！？\n]', message_text)
            for sent in sentences:
                if keyword in sent:
                    return status, sent.strip()
            return status, message_text[:100]  # 取前100字符
    
    # 没有明确状态词，返回整个消息作为处理结果
    return None, message_text[:100]

def extract_issue_keywords(message_text: str) -> list:
    """提取问题关键词用于匹配"""
    keywords = [
        "同步", "数据", "订单", "导入", "CSV", "派卡", "公众号",
        "通知", "抢单", "交付", "系统", "接口", "历史订单",
        "重新同步", "统计", "配置", "关闭", "统计"
    ]
    found = []
    for kw in keywords:
        if kw in message_text:
            found.append(kw)
    return found

def search_records_by_keywords(keywords: list, token: str) -> Optional[Dict]:
    """根据关键词搜索表格记录"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records?page_size=100"
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'}, method='GET')
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get('code') != 0:
                return None
            
            records = result.get('data', {}).get('items', [])
            
            # 按关键词匹配
            for keyword in keywords:
                for record in records:
                    fields = record.get('fields', {})
                    status = fields.get('处理状态', '')
                    
                    # 跳过已解决/已关闭的
                    if isinstance(status, list):
                        status = status[0] if status else ''
                    if status in ['已解决', '已关闭']:
                        continue
                    
                    # 匹配标题和内容
                    title = fields.get('业务反馈问题记录表', '')
                    content = fields.get('问题内容', '')
                    
                    if keyword in title or keyword in content:
                        return {
                            'record_id': record.get('record_id'),
                            'title': title,
                            'content': content,
                            'status': status,
                            '来源群': fields.get('来源群', ''),
                            '反馈人': fields.get('反馈人', ''),
                            '原始消息ID': fields.get('原始消息ID', '')
                        }
            
            return None
    except Exception as e:
        print(f"搜索记录失败: {e}")
        return None

def update_record_status(record_id: str, status: str, result: str, token: str) -> bool:
    """更新记录状态"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/{record_id}"
    payload = {
        "fields": {
            "处理状态": status,
            "处理结果": result
        }
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        method='PUT'
    )
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('code') == 0
    except Exception as e:
        print(f"更新记录失败: {e}")
        return False

def forward_reply_to_source(matched: dict, status: str, result: str, sender_name: str, token: str) -> bool:
    """
    转发处理结果到来源群
    
    Args:
        matched: 匹配的记录信息
        status: 处理状态
        result: 处理结果
        sender_name: 处理人姓名
        token: 飞书token
    
    Returns:
        是否发送成功
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # 从记录中获取来源群和反馈人
    source_chat_id = matched.get('来源群', '')
    feedback_user = matched.get('反馈人', '')
    original_message_id = matched.get('原始消息ID', '')
    
    if not source_chat_id:
        print(f"  ⚠️ 未找到来源群信息，跳过转发")
        return False
    
    # 构造回复消息
    title = matched.get('title', '未知问题')
    
    # 构建post消息内容
    content_blocks = []
    
    # 标题
    content_blocks.append([{"tag": "text", "text": f"【问题处理结果】", "style": {"bold": True}}])
    content_blocks.append([{"tag": "text", "text": ""}])
    
    # 问题信息
    content_blocks.append([{"tag": "text", "text": f"问题：{title}"}])
    content_blocks.append([{"tag": "text", "text": f"处理人：{sender_name}"}])
    content_blocks.append([{"tag": "text", "text": f"状态：{status}"}])
    content_blocks.append([{"tag": "text", "text": f"结果：{result}"}])
    content_blocks.append([{"tag": "text", "text": ""}])
    
    # @反馈人
    if feedback_user:
        content_blocks.append([{"tag": "text", "text": f"@{feedback_user} 问题已处理，请查看~"}])
    
    post_content = {
        "zh_cn": {
            "title": "【问题处理结果】",
            "content": content_blocks
        }
    }
    
    # 发送消息
    url = "https://open.feishu.cn/open-apis/im/v1/messages"
    
    # 如果知道原始消息ID，使用reply方式
    if original_message_id:
        url = f"https://open.feishu.cn/open-apis/im/v1/messages/{original_message_id}/reply"
    
    payload = {
        "receive_id": source_chat_id,
        "msg_type": "post",
        "content": json.dumps(post_content)
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
            result_data = json.loads(response.read().decode('utf-8'))
            if result_data.get('code') == 0:
                print(f"  ✅ 已转发回复到来源群")
                return True
            else:
                print(f"  ⚠️ 转发失败: {result_data}")
                return False
    except Exception as e:
        print(f"  ⚠️ 转发异常: {e}")
        return False


def handle_at_message(message_data: dict) -> Optional[str]:
    """
    处理@我的消息，更新表格状态
    
    Args:
        message_data: 飞书消息数据，包含 text, sender_name 等
    
    Returns:
        处理结果描述，失败返回None
    """
    message_text = message_data.get('text', '')
    sender_name = message_data.get('sender_name', '处理人')
    
    # 检查是否@我
    if not is_at_me(message_text):
        return None
    
    print(f"[{datetime.now()}] 收到@消息 from {sender_name}")
    
    # 清理@标签
    clean_text = remove_at_tags(message_text)
    print(f"  内容: {clean_text}")
    
    # 提取状态和处理结果
    status, result = extract_status_and_result(clean_text)
    if not status:
        print(f"  ⚠️ 未识别到处理状态，使用默认'已解决'")
        status = "已解决"
    
    print(f"  状态: {status}")
    print(f"  结果: {result[:50]}...")
    
    # 加载凭证
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        return "无法获取飞书凭证"
    
    token = get_tenant_access_token(app_id, app_secret)
    
    # 提取关键词匹配问题
    keywords = extract_issue_keywords(clean_text)
    print(f"  关键词: {keywords}")
    
    if not keywords:
        return "未提取到问题关键词，无法匹配"
    
    # 搜索匹配的问题
    matched = search_records_by_keywords(keywords, token)
    if not matched:
        return "未找到匹配的待处理问题"
    
    print(f"  匹配到: {matched['title']}")
    
    # 更新状态
    success = update_record_status(matched['record_id'], status, result, token)
    
    if success:
        # 转发回复到来源群
        forward_result = forward_reply_to_source(matched, status, result, sender_name, token)
        if forward_result:
            return f"✅ 已更新「{matched['title']}」为{status}，并已通知来源群"
        else:
            return f"✅ 已更新「{matched['title']}」为{status}，但通知来源群失败"
    else:
        return f"❌ 更新失败"

if __name__ == '__main__':
    # 测试
    test_cases = [
        {
            "text": f'<at user_id="{MY_BOT_ID}">DuangDuang</at> 历史订单同步已完成，数据已导入交付系统',
            "sender_name": "施嘉科"
        },
        {
            "text": f'<at user_id="{MY_BOT_ID}">DuangDuang</at> 抢单功能配置已关闭',
            "sender_name": "宋广智"
        },
        {
            "text": f'<at user_id="{MY_BOT_ID}">DuangDuang</at> 派卡统计需求处理中，稍后给出结果',
            "sender_name": "施嘉科"
        }
    ]
    
    print("测试@消息处理...\n")
    for msg in test_cases:
        print(f"输入: {msg['text'][:60]}...")
        result = handle_at_message(msg)
        print(f"输出: {result}\n")

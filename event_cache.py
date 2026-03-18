#!/usr/bin/env python3
"""
OpenClaw事件缓存系统
记录所有收到的@消息，用于断线重连后的遗漏检查
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# 事件日志文件
EVENT_LOG_FILE = os.path.expanduser("~/openclaw/workspace/.event_cache.json")
MAX_LOG_DAYS = 7  # 保留7天的事件记录

def load_event_cache() -> Dict:
    """加载事件缓存"""
    if os.path.exists(EVENT_LOG_FILE):
        try:
            with open(EVENT_LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载事件缓存失败: {e}")
            return {"events": [], "last_check": None}
    return {"events": [], "last_check": None}

def save_event_cache(cache: Dict):
    """保存事件缓存"""
    try:
        with open(EVENT_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存事件缓存失败: {e}")

def log_at_message(
    message_id: str,
    chat_id: str,
    chat_name: str,
    sender_id: str,
    sender_name: str,
    content: str,
    processed: bool = False
):
    """
    记录收到的@消息
    
    Args:
        message_id: 消息唯一ID
        chat_id: 群ID
        chat_name: 群名称
        sender_id: 发送者ID
        sender_name: 发送者姓名
        content: 消息内容
        processed: 是否已处理
    """
    cache = load_event_cache()
    
    # 检查是否已存在（去重）
    for event in cache["events"]:
        if event["message_id"] == message_id:
            return  # 已记录，跳过
    
    # 添加新事件
    event = {
        "message_id": message_id,
        "chat_id": chat_id,
        "chat_name": chat_name,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "content": content[:200],  # 只保存前200字符
        "timestamp": datetime.now().isoformat(),
        "processed": processed,
        "logged_at": datetime.now().isoformat()
    }
    
    cache["events"].append(event)
    
    # 清理过期事件
    cutoff_date = datetime.now() - timedelta(days=MAX_LOG_DAYS)
    cache["events"] = [
        e for e in cache["events"]
        if datetime.fromisoformat(e["timestamp"]) > cutoff_date
    ]
    
    save_event_cache(cache)
    print(f"[EventCache] 已记录@消息: {sender_name} @ {chat_name}")

def mark_as_processed(message_id: str):
    """标记消息为已处理"""
    cache = load_event_cache()
    
    for event in cache["events"]:
        if event["message_id"] == message_id:
            event["processed"] = True
            event["processed_at"] = datetime.now().isoformat()
            save_event_cache(cache)
            print(f"[EventCache] 标记为已处理: {message_id}")
            return True
    
    return False

def get_unprocessed_events(hours: int = 24) -> List[Dict]:
    """
    获取未处理的事件
    
    Args:
        hours: 最近多少小时内
    
    Returns:
        未处理的事件列表
    """
    cache = load_event_cache()
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    unprocessed = []
    for event in cache["events"]:
        if not event.get("processed", False):
            event_time = datetime.fromisoformat(event["timestamp"])
            if event_time > cutoff_time:
                unprocessed.append(event)
    
    return unprocessed

def check_missed_messages() -> List[Dict]:
    """
    检查可能遗漏的消息
    上线后调用，返回未处理的@消息
    """
    print(f"[{datetime.now()}] 检查遗漏的@消息...")
    
    # 获取最近24小时未处理的@消息
    unprocessed = get_unprocessed_events(hours=24)
    
    if not unprocessed:
        print("✅ 无遗漏的@消息")
        return []
    
    print(f"⚠️ 发现 {len(unprocessed)} 条未处理的@消息：")
    for event in unprocessed:
        print(f"  - [{event['chat_name']}] {event['sender_name']}: {event['content'][:50]}...")
    
    return unprocessed

def generate_offline_report() -> str:
    """生成离线期间的消息报告"""
    unprocessed = get_unprocessed_events(hours=24)
    
    if not unprocessed:
        return "离线期间无未处理的@消息"
    
    report = f"📋 离线期间未处理的消息（{len(unprocessed)}条）：\n\n"
    
    for i, event in enumerate(unprocessed, 1):
        report += f"{i}. [{event['chat_name']}] {event['sender_name']}\n"
        report += f"   内容：{event['content'][:80]}...\n"
        report += f"   时间：{event['timestamp'][:19]}\n\n"
    
    return report

# 便捷函数：在消息处理流程中调用
def on_at_message_received(message_data: dict) -> bool:
    """
    收到@消息时调用，记录到缓存
    
    Args:
        message_data: 消息数据，包含 message_id, chat_id, sender, text 等
    
    Returns:
        是否是重复消息（已存在缓存中）
    """
    message_id = message_data.get('message_id', '')
    chat_id = message_data.get('chat_id', '')
    chat_name = message_data.get('chat_name', '未知群')
    sender_id = message_data.get('sender_id', '')
    sender_name = message_data.get('sender_name', '未知用户')
    content = message_data.get('text', '')
    
    cache = load_event_cache()
    
    # 检查是否已存在
    for event in cache["events"]:
        if event["message_id"] == message_id:
            return True  # 重复消息
    
    # 记录新消息
    log_at_message(
        message_id=message_id,
        chat_id=chat_id,
        chat_name=chat_name,
        sender_id=sender_id,
        sender_name=sender_name,
        content=content,
        processed=False
    )
    
    return False  # 新消息

def on_message_processed(message_id: str):
    """消息处理完成后调用"""
    mark_as_processed(message_id)

if __name__ == '__main__':
    # 测试
    print("测试事件缓存系统...\n")
    
    # 模拟收到消息
    test_msg = {
        "message_id": "test_001",
        "chat_id": "oc_469678cc3cd264438f9bbb65da534c0b",
        "chat_name": "产研-融合业务组",
        "sender_id": "ou_test123",
        "sender_name": "测试用户",
        "text": "@DuangDuang 这是一个测试问题"
    }
    
    print("1. 记录消息...")
    is_duplicate = on_at_message_received(test_msg)
    print(f"   是否重复: {is_duplicate}\n")
    
    print("2. 再次记录同一消息...")
    is_duplicate = on_at_message_received(test_msg)
    print(f"   是否重复: {is_duplicate}\n")
    
    print("3. 标记为已处理...")
    on_message_processed("test_001")
    
    print("\n4. 检查未处理消息...")
    unprocessed = check_missed_messages()
    
    print("\n5. 生成离线报告...")
    report = generate_offline_report()
    print(report)

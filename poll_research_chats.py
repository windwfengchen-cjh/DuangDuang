#!/usr/bin/env python3
"""
调研群消息轮询收集器
不依赖 OpenClaw 事件订阅，直接使用飞书 API 轮询
"""

import json
import time
import os
import sys
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# 配置
RESEARCH_STATE_DIR = os.path.expanduser("~/.openclaw/feishu/research")
RESEARCH_MESSAGES_DIR = os.path.expanduser("~/.openclaw/feishu/research_messages")

# 问答模式问题列表
RESEARCH_QUESTIONS = [
    {
        "key": "background",
        "question": "👋 大家好！需求调研现在开始。\n\n📋 **需求标题**: {title}\n👤 **需求人**: @{requester}\n\n🤖 我将通过 **7个关键问题** 引导调研，同时 **自动收集** 群内所有讨论内容。\n\n---\n\n**问题 1/7：业务背景**\n请描述一下这个需求的【业务背景】是什么？是在什么场景下产生的？\n\n💡 提示：为什么需要这个功能？要解决什么业务问题？"
    },
    {
        "key": "target_users",
        "question": "**问题 2/7：目标用户**\n这个需求的【目标用户】是谁？\n\n💡 例如：内部同事（哪个部门/角色？）、外部客户、特定群体等"
    },
    {
        "key": "current_situation",
        "question": "**问题 3/7：现状描述**\n请描述一下【当前的系统/流程现状】是什么样？\n\n💡 提示：用户现在是如何完成这个任务的？"
    },
    {
        "key": "pain_points",
        "question": "**问题 4/7：核心痛点**\n当前的【核心痛点】是什么？\n\n💡 提示：哪个步骤最耗时/容易出错？造成了什么影响？"
    },
    {
        "key": "expected_solution",
        "question": "**问题 5/7：期望解决方案**\n针对这个痛点，您【期望的解决方案】是什么？\n\n💡 提示：希望系统如何帮助用户？"
    },
    {
        "key": "priority",
        "question": "**问题 6/7：优先级和时间**\n请问这个需求的【优先级和时间要求】是怎样的？\n\n💡 例如：高/中/低，期望上线时间"
    },
    {
        "key": "attachments",
        "question": "**问题 7/7：相关资料**\n是否有相关的【数据、截图、文档】需要补充？如有请直接发送，没有请回复\"无\"。"
    }
]

def load_feishu_creds():
    """加载飞书凭证"""
    config_path = os.path.expanduser("~/.openclaw/openclaw.json")
    with open(config_path) as f:
        config = json.load(f)
    return config['channels']['feishu']['appId'], config['channels']['feishu']['appSecret']

def get_tenant_token(app_id: str, app_secret: str) -> str:
    """获取 tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": app_id, "app_secret": app_secret})
    return resp.json()['tenant_access_token']

def load_research_sessions() -> List[Dict]:
    """加载所有活跃的调研会话"""
    sessions = []
    if not os.path.exists(RESEARCH_STATE_DIR):
        return sessions
    
    for filename in os.listdir(RESEARCH_STATE_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(RESEARCH_STATE_DIR, filename)
            with open(filepath) as f:
                session = json.load(f)
                if session.get('status') == 'collecting':
                    sessions.append(session)
    return sessions

def load_chat_messages(chat_id: str) -> List[Dict]:
    """加载已保存的消息"""
    filepath = os.path.join(RESEARCH_MESSAGES_DIR, f"{chat_id}.json")
    if os.path.exists(filepath):
        with open(filepath) as f:
            return json.load(f)
    return []

def save_chat_messages(chat_id: str, messages: List[Dict]):
    """保存消息"""
    os.makedirs(RESEARCH_MESSAGES_DIR, exist_ok=True)
    filepath = os.path.join(RESEARCH_MESSAGES_DIR, f"{chat_id}.json")
    with open(filepath, 'w') as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)

def update_session(chat_id: str, updates: Dict):
    """更新会话状态"""
    filepath = os.path.join(RESEARCH_STATE_DIR, f"{chat_id}.json")
    with open(filepath) as f:
        session = json.load(f)
    session.update(updates)
    session['updated_at'] = datetime.now().isoformat()
    with open(filepath, 'w') as f:
        json.dump(session, f, indent=2, ensure_ascii=False)

def save_session(chat_id: str, session: Dict):
    """保存完整会话状态"""
    filepath = os.path.join(RESEARCH_STATE_DIR, f"{chat_id}.json")
    session['updated_at'] = datetime.now().isoformat()
    with open(filepath, 'w') as f:
        json.dump(session, f, indent=2, ensure_ascii=False)
    session['updated_at'] = datetime.now().isoformat()
    with open(filepath, 'w') as f:
        json.dump(session, f, indent=2, ensure_ascii=False)

def fetch_chat_messages(chat_id: str, token: str, after_time: str = None) -> List[Dict]:
    """获取群消息历史
    
    注意：飞书 API /im/v1/messages 返回的 sender 结构：
    {
        "id": "ou_xxx",        # 发送者 ID (open_id)
        "id_type": "open_id",  # ID 类型
        "sender_type": "user", # 发送者类型: user/app/anonymous/unknown
        "tenant_key": "xxx"    # 租户 key
    }
    这与 Webhook 事件推送的结构不同！
    """
    url = f"https://open.feishu.cn/open-apis/im/v1/messages"
    headers = {"Authorization": f"Bearer {token}"}
    
    params = {
        "container_id_type": "chat",
        "container_id": chat_id,
        "page_size": 50,
        "sort_type": "ByCreateTimeAsc"
    }
    
    if after_time:
        params["start_time"] = after_time
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        data = resp.json()
        if data.get('code') == 0:
            items = data.get('data', {}).get('items', [])
            messages = []
            for item in items:
                sender = item.get('sender', {})
                # API 返回结构: sender.id 直接是 open_id (当 id_type == 'open_id')
                # 修复：更宽松地获取 sender_id
                # API 返回结构: sender.id 就是 open_id
                sender_id = sender.get('id') or sender.get('open_id') or None
                sender_type = sender.get('sender_type') or sender.get('type') or 'unknown'
                
                msg = {
                    "message_id": item.get('message_id'),
                    "sender_id": sender_id,
                    "sender_type": sender_type,
                    "sender_name": sender.get('name', 'Unknown'),  # API 可能不返回 name
                    "content": extract_text_content(item.get('body', {}).get('content', '')),
                    "message_type": item.get('msg_type'),
                    "create_time": item.get('create_time')
                }
                messages.append(msg)
            return messages
        else:
            print(f"⚠️ API 错误: code={data.get('code')}, msg={data.get('msg')}")
    except Exception as e:
        print(f"❌ 获取消息失败: {e}")
    return []

def extract_text_content(content: str) -> str:
    """从消息内容中提取文本"""
    try:
        data = json.loads(content)
        if 'text' in data:
            return data['text']
        elif 'post' in data:
            post = data['post'].get('zh_cn', data['post'])
            text = post.get('title', '') + '\n'
            for block in post.get('content', []):
                if isinstance(block, list):
                    for elem in block:
                        if elem.get('tag') == 'text':
                            text += elem.get('text', '')
                        elif elem.get('tag') == 'at':
                            text += f"@{elem.get('user_name', '')}"
                    text += '\n'
            return text.strip()
    except:
        pass
    return content

def send_message(chat_id: str, content: str, token: str):
    """发送消息到群"""
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    post_content = {
        "zh_cn": {
            "title": "",
            "content": [[{"tag": "text", "text": content}]]
        }
    }
    
    payload = {
        "receive_id": chat_id,
        "msg_type": "post",
        "content": json.dumps(post_content, ensure_ascii=False)
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        return resp.json().get('code') == 0
    except Exception as e:
        print(f"❌ 发送消息失败: {e}")
        return False

def check_triggers(text: str, session: Dict) -> Optional[str]:
    """检查是否触发指令"""
    text_lower = text.lower()
    
    # 完成指令
    if any(kw in text for kw in ['完成调研', '生成prd', 'prd', '结束', '完成']):
        return 'complete'
    
    # 取消指令
    if any(kw in text for kw in ['取消', '不做了', '停止']):
        return 'cancel'
    
    return None

def process_session(session: Dict, token: str):
    """处理一个调研会话 - 支持问答+自动收集混合模式"""
    chat_id = session['chat_id']
    requirement_person_id = session['requirement_person_id']
    boss_id = session['boss_id']
    qa_mode = session.get('qa_mode', False)
    current_idx = session.get('current_question_idx', 0)
    
    # 获取已保存的消息
    saved_messages = load_chat_messages(chat_id)
    saved_ids = {m['message_id'] for m in saved_messages}
    
    # 获取最新消息
    new_messages = fetch_chat_messages(chat_id, token)
    
    added_count = 0
    need_next_question = False
    
    for msg in new_messages:
        if msg['message_id'] not in saved_ids:
            sender_id = msg.get('sender_id')
            sender_type = msg.get('sender_type', 'unknown')
            
            # 标记是否是需求人（通过比较 sender_id）
            is_req_person = sender_id == requirement_person_id if sender_id else False
            msg['is_requirement_person'] = is_req_person
            saved_messages.append(msg)
            saved_ids.add(msg['message_id'])
            added_count += 1
            
            content = msg['content']
            
            # 调试日志：显示发送者信息
            debug_info = f"sender_id={sender_id[-8:] if sender_id else 'None'}, type={sender_type}"
            if is_req_person:
                debug_info += " [需求人]"
            print(f"  📩 新消息: {debug_info}", flush=True)
            
            # 跳过机器人自己发的消息（通过内容特征判断）
            if '👋 大家好！需求调研' in content or '**问题' in content or '🤖 我将通过' in content:
                print(f"  🤖 跳过机器人消息", flush=True)
                continue
            
            # 检查触发词 - 仅在 sender_id 匹配需求人或 Boss 时才触发
            # 注意：由于 API 权限限制，sender_id 可能为 None，此时不触发指令
            trigger = check_triggers(content, session)
            sender_id = msg.get('sender_id')
            is_authorized = sender_id and (sender_id == requirement_person_id or sender_id == boss_id)
            
            if trigger == 'complete' and is_authorized:
                print(f"✅ 收到完成指令 from authorized user")
                return 'complete'
            elif trigger == 'cancel' and is_authorized:
                print(f"❌ 收到取消指令 from authorized user")
                return 'cancel'
            
            # 问答模式：收到任何非机器人消息都视为有效回答
            if qa_mode and current_idx < len(RESEARCH_QUESTIONS):
                # 保存答案
                question_key = RESEARCH_QUESTIONS[current_idx]['key']
                collected_data = session.get('collected_data', {})
                collected_data[question_key] = content
                session['collected_data'] = collected_data
                save_session(chat_id, session)
                print(f"  💾 保存答案 [{question_key}]: {content[:30]}...", flush=True)
                need_next_question = True
    
    # 保存消息
    if added_count > 0:
        save_chat_messages(chat_id, saved_messages)
        update_session(chat_id, {'message_count': len(saved_messages)})
        print(f"✅ {chat_id[-8:]}: 新增 {added_count} 条消息 (总计: {len(saved_messages)})", flush=True)
        
        # 问答模式：发送下一个问题
        if need_next_question and qa_mode:
            current_idx = session.get('current_question_idx', 0)
            next_idx = current_idx + 1
            if next_idx < len(RESEARCH_QUESTIONS):
                question = RESEARCH_QUESTIONS[next_idx]['question']
                send_message(chat_id, question, token)
                update_session(chat_id, {'current_question_idx': next_idx})
                print(f"  📤 发送问题 {next_idx + 1}/{len(RESEARCH_QUESTIONS)}", flush=True)
            else:
                # 所有问题完成
                print(f"  ✅ 所有问题已回答完毕")
                return 'complete'
    else:
        print(f"  {chat_id[-8:]}: 没有新消息", flush=True)
    
    return 'continue'

def test_fetch_messages(chat_id: str, token: str):
    """测试获取消息 API，打印原始响应以便调试"""
    url = f"https://open.feishu.cn/open-apis/im/v1/messages"
    headers = {"Authorization": f"Bearer {token}"}
    
    params = {
        "container_id_type": "chat",
        "container_id": chat_id,
        "page_size": 5,
        "sort_type": "ByCreateTimeDesc"  # 最新的在前
    }
    
    print(f"\n🔍 测试获取消息 API")
    print(f"   Chat ID: {chat_id}")
    print(f"   URL: {url}")
    print(f"   Params: {params}")
    print("-" * 60)
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        data = resp.json()
        
        print(f"响应状态: {resp.status_code}")
        print(f"响应 code: {data.get('code')}")
        print(f"响应 msg: {data.get('msg')}")
        
        if data.get('code') == 0:
            items = data.get('data', {}).get('items', [])
            print(f"\n获取到 {len(items)} 条消息:\n")
            
            for i, item in enumerate(items[:3]):  # 只显示前3条
                sender = item.get('sender', {})
                body = item.get('body', {})
                
                print(f"消息 {i+1}:")
                print(f"  message_id: {item.get('message_id')}")
                print(f"  sender 结构:")
                print(f"    - id: {sender.get('id')}")
                print(f"    - id_type: {sender.get('id_type')}")
                print(f"    - sender_type: {sender.get('sender_type')}")
                print(f"    - tenant_key: {sender.get('tenant_key')}")
                print(f"    - name: {sender.get('name', '未返回')}")
                print(f"  msg_type: {item.get('msg_type')}")
                print(f"  create_time: {item.get('create_time')}")
                print(f"  content: {body.get('content', '')[:100]}...")
                print()
        else:
            print(f"❌ API 错误: {data}")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")


def main():
    import sys
    
    # 检查是否有测试参数
    test_mode = '--test' in sys.argv
    test_chat_id = None
    
    for i, arg in enumerate(sys.argv):
        if arg == '--test' and i + 1 < len(sys.argv):
            test_chat_id = sys.argv[i + 1]
    
    # 加载凭证
    app_id, app_secret = load_feishu_creds()
    token = get_tenant_token(app_id, app_secret)
    
    # 测试模式
    if test_mode and test_chat_id:
        test_fetch_messages(test_chat_id, token)
        return
    
    print("=" * 60, flush=True)
    print("🚀 启动调研群消息轮询收集器", flush=True)
    print("=" * 60, flush=True)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("轮询间隔: 10 秒", flush=True)
    print("测试命令: python3 poll_research_chats.py --test <chat_id>", flush=True)
    print("=" * 60, flush=True)
    
    # 加载凭证
    app_id, app_secret = load_feishu_creds()
    token = get_tenant_token(app_id, app_secret)
    token_expiry = datetime.now() + timedelta(hours=1.5)
    
    try:
        while True:
            # 检查 token 是否过期
            if datetime.now() > token_expiry:
                token = get_tenant_token(app_id, app_secret)
                token_expiry = datetime.now() + timedelta(hours=1.5)
                print("🔄 Token 已刷新")
            
            # 加载所有活跃会话
            sessions = load_research_sessions()
            
            if not sessions:
                print(f"⏳ {datetime.now().strftime('%H:%M:%S')} 没有活跃的调研群", flush=True)
            else:
                print(f"\n⏳ {datetime.now().strftime('%H:%M:%S')} 检查 {len(sessions)} 个调研群:", flush=True)
                
                for session in sessions:
                    chat_id = session['chat_id']
                    title = session.get('requirement_title', 'Unknown')
                    print(f"  检查群: {chat_id[-8:]} ({title})", flush=True)
                    
                    result = process_session(session, token)
                    
                    if result == 'complete':
                        # 生成 PRD
                        print(f"📝 正在生成 PRD for {title}...")
                        update_session(chat_id, {'status': 'completed'})
                        send_message(chat_id, f"✅ 调研完成！已收集 {session.get('message_count', 0)} 条消息，正在生成 PRD...", token)
                        # TODO: 调用 PRD 生成逻辑
                        
                    elif result == 'cancel':
                        update_session(chat_id, {'status': 'cancelled'})
                        send_message(chat_id, "❌ 调研已取消", token)
            
            # 等待 10 秒（可修改为 30 秒以降低消耗）
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n👋 已停止")
        sys.exit(0)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
飞书反馈自动转发脚本
整合功能：转发消息 + 记录表格 + 消息链接（图片无法下载时）

此脚本由 feishu-feedback-handler skill 调用
"""

import json
import os
import sys
import tempfile
import time
import requests

# 默认配置路径
DEFAULT_CONFIG_PATH = os.path.expanduser("~/.openclaw/skills/feishu-feedback-handler/config.json")
OPENCLAW_CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")
CONTACTS_PATH = os.path.expanduser("~/.openclaw/skills/feishu-feedback-handler/references/contacts.json")

def load_skill_config(config_path=None):
    """加载 Skill 配置"""
    path = config_path or DEFAULT_CONFIG_PATH
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ 加载 skill 配置失败: {e}")
    return None

def load_feishu_creds():
    """加载飞书凭证"""
    try:
        with open(OPENCLAW_CONFIG, 'r') as f:
            config = json.load(f)
            feishu_config = config.get('channels', {}).get('feishu', {})
            return feishu_config.get('appId'), feishu_config.get('appSecret')
    except Exception as e:
        print(f"❌ 加载配置失败: {e}")
        return None, None

def get_tenant_access_token(app_id, app_secret):
    """获取 tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": app_id, "app_secret": app_secret})
    data = resp.json()
    if data.get('code') != 0:
        raise Exception(f"获取 token 失败: {data}")
    return data.get('tenant_access_token')

def download_image(image_key, token):
    """下载图片"""
    url = f"https://open.feishu.cn/open-apis/im/v1/images/{image_key}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, stream=True)
    
    if resp.status_code != 200:
        raise Exception(f"下载失败: {resp.status_code}")
    
    suffix = ".png"
    content_type = resp.headers.get('content-type', '')
    if 'jpeg' in content_type or 'jpg' in content_type:
        suffix = ".jpg"
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    for chunk in resp.iter_content(chunk_size=8192):
        if chunk:
            temp_file.write(chunk)
    temp_file.close()
    return temp_file.name

def upload_image(image_path, token):
    """上传图片到飞书"""
    url = "https://open.feishu.cn/open-apis/im/v1/images"
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(image_path, 'rb') as f:
        files = {'image': f}
        data = {'image_type': 'message'}
        resp = requests.post(url, headers=headers, files=files, data=data)
    
    result = resp.json()
    if result.get('code') != 0:
        raise Exception(f"上传失败: {result}")
    return result['data']['image_key']

def send_forward_message(token, chat_id, title, content, image_key=None, message_link=None, at_list=None):
    """发送转发消息"""
    # 构造内容块
    content_blocks = []
    
    # 正文
    content_blocks.append([{"tag": "text", "text": content}])
    
    # 图片
    if image_key:
        content_blocks.append([{"tag": "img", "image_key": image_key}])
    
    # 消息链接（图片无法下载时）
    if message_link and not image_key:
        content_blocks.append([{"tag": "text", "text": ""}])
        content_blocks.append([{"tag": "text", "text": "📎 原消息包含图片，点击查看："}])
        content_blocks.append([{
            "tag": "a",
            "text": "点击查看原消息和图片",
            "href": message_link
        }])
    
    # @人员
    if at_list:
        content_blocks.append([{"tag": "text", "text": ""}])
        at_para = []
        for i, at in enumerate(at_list):
            if i > 0:
                at_para.append({"tag": "text", "text": " "})
            at_para.append({
                "tag": "at",
                "user_id": at["user_id"],
                "user_name": at.get("user_name", "")
            })
        at_para.append({"tag": "text", "text": " 请查看~"})
        content_blocks.append(at_para)
    
    # 发送
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    message_content = {
        "zh_cn": {
            "title": title,
            "content": content_blocks
        }
    }
    
    payload = {
        "receive_id": chat_id,
        "msg_type": "post",
        "content": json.dumps(message_content, ensure_ascii=False)
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    resp = requests.post(url, json=payload, headers=headers)
    return resp.json()

def record_to_bitable(token, app_token, table_id, fields):
    """记录到多维表格"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"fields": fields}
    
    resp = requests.post(url, json=payload, headers=headers)
    return resp.json()

def get_forward_config(source_chat_id, skill_config):
    """
    根据来源群ID获取转发配置
    
    Args:
        source_chat_id: 来源群 chat_id
        skill_config: skill 配置
    
    Returns:
        dict: 配置信息
    """
    if skill_config and 'forward_configs' in skill_config:
        config = skill_config['forward_configs'].get(source_chat_id)
        if config:
            # 过滤掉没有 user_id 的处理人
            handlers = [h for h in config.get("handlers", []) if h.get("user_id")]
            return {
                "target_chat_id": config.get("target_chat_id"),
                "handlers": handlers,
                "source_name": config.get("source_name", "未知来源"),
                "record_bitable": config.get("record_bitable", True),
                "notify_boss_for_requirement": config.get("notify_boss_for_requirement", True)
            }
    return None

def classify_message(content):
    """
    判断消息类型
    
    Returns:
        dict: {type: '问题'|'需求'|'咨询', should_record: bool, notify_boss: bool}
    """
    content = content.lower()
    
    # 问题类关键词
    bug_keywords = ['bug', '报错', '故障', '异常', '错误', '失败', 'crash', '卡死', '无法', '不能', '问题']
    # 需求类关键词  
    requirement_keywords = ['需求', '新功能', '改进', '优化', '建议', '统计', '报表', '导出', '增加', '添加']
    # 咨询类关键词
    consult_keywords = ['如何使用', '怎么操作', '在哪里', '怎么用', '请教', '咨询']
    
    for kw in consult_keywords:
        if kw in content:
            return {"type": "咨询", "should_record": False, "notify_boss": False}
    
    for kw in bug_keywords:
        if kw in content:
            return {"type": "问题", "should_record": True, "notify_boss": False}
    
    for kw in requirement_keywords:
        if kw in content:
            return {"type": "需求", "should_record": True, "notify_boss": True}
    
    # 默认按问题处理
    return {"type": "问题", "should_record": True, "notify_boss": False}

def forward_feedback(source_chat, reporter, content, image_key=None, message_id=None,
                     message_type=None, source_chat_id=None, skill_config=None, message_time=None):
    """
    转发反馈到目标群并记录到表格

    Args:
        source_chat: 来源群名称
        reporter: 反馈人
        content: 问题内容
        image_key: 图片 key（可选）
        message_id: 消息 ID（用于生成链接）
        message_type: 类型（问题/需求），为None时自动判断
        source_chat_id: 来源群 chat_id（用于匹配配置）
        skill_config: skill 配置
        message_time: 消息时间戳（秒级，可选。不传则使用当前时间）

    Returns:
        dict: 转发结果
    """
    # 加载凭证
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        return {"success": False, "error": "无法加载飞书凭证"}
    
    token = get_tenant_access_token(app_id, app_secret)
    
    # 获取配置
    config = None
    if source_chat_id and skill_config:
        config = get_forward_config(source_chat_id, skill_config)
    
    if not config:
        return {"success": False, "error": f"未找到来源群 {source_chat_id} 的配置"}
    
    target_chat_id = config["target_chat_id"]
    handlers = config["handlers"]
    source_name = config["source_name"]
    record_bitable = config.get("record_bitable", True)
    
    # 自动判断消息类型
    if message_type is None:
        classification = classify_message(content)
        message_type = classification["type"]
        should_record = classification["should_record"]
        notify_boss = classification["notify_boss"]
    else:
        should_record = True
        notify_boss = (message_type == "需求")
    
    print(f"📋 使用配置: {source_name} → 目标群: {target_chat_id}")
    print(f"👥 处理人: {[h['user_name'] for h in handlers]}")
    print(f"🏷️ 类型: {message_type}")
    
    # 如果需要@Boss
    if notify_boss and config.get("notify_boss_for_requirement"):
        boss = skill_config.get("boss", {})
        if boss.get("user_id"):
            handlers = handlers + [boss]
            print(f"👔 额外@Boss: {boss['user_name']}")
    
    # 1. 处理图片
    new_image_key = None
    message_link = None
    temp_file = None
    
    if image_key:
        try:
            print(f"📥 尝试下载图片: {image_key}")
            temp_file = download_image(image_key, token)
            print(f"📤 上传图片到目标群...")
            new_image_key = upload_image(temp_file, token)
            print(f"✅ 图片转发成功")
        except Exception as e:
            print(f"⚠️ 图片下载失败: {e}")
            print(f"💡 将使用消息链接")
            if message_id:
                message_link = f"https://applink.feishu.cn/client/message/open?message_id={message_id}"
        finally:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
    
    # 2. 发送到目标群
    title = f"【产研反馈-{message_type}】"
    if image_key and not new_image_key:
        title += "（含消息链接）"
    
    try:
        result = send_forward_message(
            token=token,
            chat_id=target_chat_id,
            title=title,
            content=f"反馈人：{reporter} | 来源：{source_name}\n\n问题描述：\n{content}",
            image_key=new_image_key,
            message_link=message_link,
            at_list=handlers
        )
        
        if result.get('code') != 0:
            return {"success": False, "error": f"发送消息失败: {result}"}
        
        print(f"✅ 已转发到目标群")
    except Exception as e:
        return {"success": False, "error": f"转发失败: {e}"}
    
    # 3. 记录到表格
    record_id = None
    if should_record and record_bitable:
        try:
            bitable_config = skill_config.get("bitable", {})
            app_token = bitable_config.get("app_token")
            table_id = bitable_config.get("table_id")
            
            if app_token and table_id:
                # 构造时间戳：优先使用消息时间，其次使用当前时间
                if message_time and message_time > 0:
                    # 使用消息的实际时间（飞书消息时间戳是秒级，需要转为毫秒）
                    feedback_timestamp = int(message_time * 1000) if message_time < 10000000000 else int(message_time)
                    print(f"📝 使用消息时间戳: {feedback_timestamp}")
                else:
                    # 使用当前时间
                    feedback_timestamp = int(time.time() * 1000)
                    print(f"📝 使用当前时间戳: {feedback_timestamp}")

                # 构造字段
                fields = {
                    "业务反馈问题记录表": content[:100] + ("..." if len(content) > 100 else ""),
                    "反馈时间": feedback_timestamp,
                    "反馈人": reporter,
                    "反馈来源": source_chat,
                    "问题内容": content,
                    "处理状态": "待处理",
                    "类型": message_type,
                    "来源群": source_chat
                }
                
                if message_id:
                    fields["原始消息ID"] = message_id
                
                record_result = record_to_bitable(
                    token=token,
                    app_token=app_token,
                    table_id=table_id,
                    fields=fields
                )
                
                if record_result.get('code') == 0:
                    print(f"✅ 已记录到问题记录表")
                    record_id = record_result.get('data', {}).get('record', {}).get('record_id')
                else:
                    print(f"⚠️ 记录表格失败: {record_result}")
            else:
                print(f"⚠️ 未配置表格信息，跳过记录")
        except Exception as e:
            print(f"⚠️ 记录表格异常: {e}")
    elif not should_record:
        print(f"💬 咨询类消息，不记录表格")
    
    return {
        "success": True,
        "image_forwarded": new_image_key is not None,
        "message_link": message_link,
        "record_id": record_id,
        "message_type": message_type
    }

def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='飞书反馈转发脚本')
    parser.add_argument('--source-chat', required=True, help='来源群名称')
    parser.add_argument('--reporter', required=True, help='反馈人')
    parser.add_argument('--content', required=True, help='消息内容')
    parser.add_argument('--source-chat-id', help='来源群chat_id')
    parser.add_argument('--image-key', help='图片key')
    parser.add_argument('--message-id', help='消息ID')
    parser.add_argument('--message-type', help='消息类型（问题/需求）')
    parser.add_argument('--message-time', type=int, help='消息时间戳（秒级）')
    parser.add_argument('--config', help='配置文件路径')

    args = parser.parse_args()

    # 加载配置
    skill_config = load_skill_config(args.config)

    result = forward_feedback(
        source_chat=args.source_chat,
        reporter=args.reporter,
        content=args.content,
        image_key=args.image_key,
        message_id=args.message_id,
        message_type=args.message_type,
        source_chat_id=args.source_chat_id,
        skill_config=skill_config,
        message_time=args.message_time
    )
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("success") else 1

# 导出函数
__all__ = ['forward_feedback', 'load_skill_config']

if __name__ == "__main__":
    sys.exit(main())

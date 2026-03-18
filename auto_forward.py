#!/usr/bin/env python3
"""
飞书反馈自动转发脚本
整合功能：转发消息 + 记录表格 + 消息链接（图片无法下载时）
"""

import json
import os
import sys
import tempfile
import time
import requests

# 配置
OPENCLAW_CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")
BITABLE_CONFIG = "/home/admin/openclaw/workspace/.feishu_bitable_config.json"

# 多配置映射表：根据 source_chat_id 决定 target_chat_id 和 handlers
# 配置1: 产研-融合业务组 → 猛龙队开发
# 配置2: 号卡&宽带 → 猛龙队开发
# 配置3: 线下号卡 → 猛龙队开发
# 配置4: 号卡能力中心信息同频群 → oc_cf3c4adafb332df5988b20204c272dbb
FORWARD_CONFIGS = {
    # 配置1: 产研-融合业务组
    "oc_469678cc3cd264438f9bbb65da534c0b": {
        "target_chat_id": "oc_a016323a9fda4263ab5a27976065088e",
        "handlers": [
            {"user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "施嘉科"},
            {"user_id": "ou_cbcd1090961b620a4500ce68e3c81952", "user_name": "宋广智"}
        ],
        "source_name": "产研-融合业务组"
    },
    # 配置2: 号卡&宽带需求和酬金系统体系搭建
    "oc_3b4215cdadcc9366c863377561ce00c5": {
        "target_chat_id": "oc_a016323a9fda4263ab5a27976065088e",
        "handlers": [
            {"user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "施嘉科"},
            {"user_id": "ou_cbcd1090961b620a4500ce68e3c81952", "user_name": "宋广智"}
        ],
        "source_name": "号卡&宽带需求和酬金系统体系搭建"
    },
    # 配置3: 线下号卡-信息流投放上报沟通
    "oc_ee55ec5275cc158b826fe1204d75cf2c": {
        "target_chat_id": "oc_a016323a9fda4263ab5a27976065088e",
        "handlers": [
            {"user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "施嘉科"}
        ],
        "source_name": "线下号卡-信息流投放上报沟通"
    },
    # 配置4: 号卡能力中心信息同频群
    "oc_5bf7336955740fb41ba59e4e929c5239": {
        "target_chat_id": "oc_cf3c4adafb332df5988b20204c272dbb",
        "handlers": [
            {"user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "施嘉科"},
            {"user_id": "", "user_name": "郑武友"},  # 待获取，后续自动收集
            {"user_id": "ou_3e48baef1bd71cc89fb5a364be55cafc", "user_name": "陈俊洪"}
        ],
        "source_name": "号卡能力中心信息同频群"
    }
}

# 兼容旧代码：默认配置（配置1）
TARGET_CHAT_ID = "oc_a016323a9fda4263ab5a27976065088e"
HANDLER_USERS = [
    {"user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "施嘉科"},
    {"user_id": "ou_cbcd1090961b620a4500ce68e3c81952", "user_name": "宋广智"}
]

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

def get_forward_config(source_chat_id):
    """
    根据来源群ID获取转发配置
    
    Args:
        source_chat_id: 来源群 chat_id
    
    Returns:
        dict: 配置信息，包含 target_chat_id, handlers, source_name
    """
    config = FORWARD_CONFIGS.get(source_chat_id)
    if config:
        # 过滤掉没有 user_id 的处理人（如郑武友待获取）
        handlers = [h for h in config["handlers"] if h.get("user_id")]
        return {
            "target_chat_id": config["target_chat_id"],
            "handlers": handlers,
            "source_name": config["source_name"]
        }
    # 默认返回配置1
    return {
        "target_chat_id": TARGET_CHAT_ID,
        "handlers": HANDLER_USERS,
        "source_name": "产研-融合业务组"
    }

def forward_feedback(source_chat, reporter, content, image_key=None, message_id=None, message_type="问题", source_chat_id=None):
    """
    转发反馈到目标群并记录到表格
    
    Args:
        source_chat: 来源群名称
        reporter: 反馈人
        content: 问题内容
        image_key: 图片 key（可选）
        message_id: 消息 ID（用于生成链接）
        message_type: 类型（问题/需求）
        source_chat_id: 来源群 chat_id（用于匹配配置）
    
    Returns:
        dict: 转发结果
    """
    # 加载凭证
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        return {"success": False, "error": "无法加载飞书凭证"}
    
    token = get_tenant_access_token(app_id, app_secret)
    
    # 获取配置（根据 source_chat_id）
    config = get_forward_config(source_chat_id) if source_chat_id else {
        "target_chat_id": TARGET_CHAT_ID,
        "handlers": HANDLER_USERS,
        "source_name": source_chat
    }
    
    target_chat_id = config["target_chat_id"]
    handlers = config["handlers"]
    source_name = config["source_name"]
    
    print(f"📋 使用配置: {source_name} → 目标群: {target_chat_id}")
    print(f"👥 处理人: {[h['user_name'] for h in handlers]}")
    
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
    try:
        if os.path.exists(BITABLE_CONFIG):
            with open(BITABLE_CONFIG, 'r') as f:
                bitable_config = json.load(f)
            
            # 构造字段
            fields = {
                "业务反馈问题记录表": content[:100] + ("..." if len(content) > 100 else ""),
                "反馈时间": int(time.time() * 1000),
                "反馈人": reporter,
                "反馈来源": source_chat,
                "问题内容": content,
                "处理状态": "待处理",
                "类型": message_type,
                "来源群": source_chat
            }
            
            record_result = record_to_bitable(
                token=token,
                app_token=bitable_config["app_token"],
                table_id=bitable_config["table_id"],
                fields=fields
            )
            
            if record_result.get('code') == 0:
                print(f"✅ 已记录到问题记录表")
                record_id = record_result.get('data', {}).get('record', {}).get('record_id')
            else:
                print(f"⚠️ 记录表格失败: {record_result}")
                record_id = None
        else:
            print(f"⚠️ 未找到表格配置，跳过记录")
            record_id = None
    except Exception as e:
        print(f"⚠️ 记录表格异常: {e}")
        record_id = None
    
    return {
        "success": True,
        "image_forwarded": new_image_key is not None,
        "message_link": message_link,
        "record_id": record_id
    }

# 导出函数
__all__ = ['forward_feedback']

if __name__ == "__main__":
    # 测试用法
    import time
    
    result = forward_feedback(
        source_chat="产研-融合业务组",
        reporter="苏键伟",
        content="这种恶意刷单的可以定期加进我们的黑名单排除吗？减少接口拥堵的问题",
        image_key="img_v3_02vs_c6fac74c-cb8d-44d9-8566-3d91ccdf52cg",
        message_id="om_x100b54bb70d1dcb4b3dacfb1122326b",
        message_type="问题"
    )
    
    print(f"\\n结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
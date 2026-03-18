#!/usr/bin/env python3
"""
飞书 Post 消息发送工具
支持富文本、@高亮、图片、链接等元素

用法:
    python3 send_feishu_post.py --chat-id oc_xxx --title "标题" --content "内容"
    python3 send_feishu_post.py --chat-id oc_xxx --title "标题" --content "内容" --at "ou_xxx:姓名"
    python3 send_feishu_post.py --chat-id oc_xxx --title "标题" --content "内容" --image-key "img_xxx"
"""

import json
import argparse
import os
import sys
import tempfile
import requests

# 从 OpenClaw 配置读取飞书凭证
OPENCLAW_CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")

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
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={
        "app_id": app_id,
        "app_secret": app_secret
    })
    data = resp.json()
    if data.get('code') != 0:
        raise Exception(f"Failed to get token: {data}")
    return data.get('tenant_access_token')

def download_image(image_key, token):
    """下载飞书图片到本地临时文件"""
    url = f"https://open.feishu.cn/open-apis/im/v1/images/{image_key}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, stream=True)
    
    if resp.status_code != 200:
        raise Exception(f"Failed to download image: {resp.status_code}, {resp.text}")
    
    # 保存到临时文件
    suffix = ".png"  # 默认后缀
    content_type = resp.headers.get('content-type', '')
    if 'jpeg' in content_type or 'jpg' in content_type:
        suffix = ".jpg"
    elif 'gif' in content_type:
        suffix = ".gif"
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    for chunk in resp.iter_content(chunk_size=8192):
        if chunk:
            temp_file.write(chunk)
    temp_file.close()
    
    return temp_file.name

def upload_image(image_path, token):
    """上传图片到飞书，返回新的 image_key"""
    url = "https://open.feishu.cn/open-apis/im/v1/images"
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(image_path, 'rb') as f:
        files = {'image': f}
        data = {'image_type': 'message'}
        resp = requests.post(url, headers=headers, files=files, data=data)
    
    result = resp.json()
    if result.get('code') != 0:
        raise Exception(f"Failed to upload image: {result}")
    
    return result['data']['image_key']

def send_post_message(chat_id, title, content_blocks, app_id=None, app_secret=None, reply_to=None):
    """
    发送飞书 post 消息
    
    Args:
        chat_id: 群聊 ID
        title: 消息标题
        content_blocks: 内容块列表，每个块是一个段落（列表）
        app_id: 飞书 App ID（可选，默认从配置读取）
        app_secret: 飞书 App Secret（可选，默认从配置读取）
        reply_to: 引用的原消息 ID（可选）
    
    Returns:
        API 响应 JSON
    """
    import requests
    
    # 加载凭证
    if not app_id or not app_secret:
        app_id, app_secret = load_feishu_creds()
        if not app_id or not app_secret:
            raise Exception("Feishu credentials not found in config")
    
    token = get_tenant_access_token(app_id, app_secret)
    url = f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    
    # 构造消息体
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
    
    # 添加引用回复（如果需要）
    if reply_to:
        payload["reply_to"] = reply_to
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    resp = requests.post(url, json=payload, headers=headers)
    return resp.json()

def parse_at_list(at_strings):
    """
    解析 @ 列表
    
    格式: "open_id:姓名" 或 "open_id"（姓名默认为空）
    
    Returns:
        列表，每个元素是 {"user_id": "xxx", "user_name": "xxx"}
    """
    at_list = []
    for at_str in at_strings:
        if ':' in at_str:
            user_id, user_name = at_str.split(':', 1)
        else:
            user_id, user_name = at_str, ""
        at_list.append({"user_id": user_id.strip(), "user_name": user_name.strip()})
    return at_list

def build_content_paragraphs(content, at_list=None, image_key=None, message_link=None):
    """
    构造内容段落
    
    Args:
        content: 正文内容（纯文本）
        at_list: @ 用户列表
        image_key: 图片的 image_key（可选）
        message_link: 消息链接（当图片无法下载时使用）
    
    Returns:
        段落列表
    """
    paragraphs = []
    
    # 第一行：正文内容
    paragraphs.append([{"tag": "text", "text": content}])
    
    # 如果有图片，添加图片段落
    if image_key:
        paragraphs.append([{"tag": "img", "image_key": image_key}])
    
    # 如果有消息链接（图片无法下载时）
    if message_link:
        paragraphs.append([{"tag": "text", "text": ""}])
        paragraphs.append([{"tag": "text", "text": "📎 原消息包含图片，点击查看："}])
        paragraphs.append([{
            "tag": "a",
            "text": "点击查看原消息和图片",
            "href": message_link
        }])
    
    # 如果有 @ 列表，添加一行 @ 信息
    if at_list:
        paragraphs.append([{"tag": "text", "text": ""}])
        at_paragraph = []
        for i, at in enumerate(at_list):
            if i > 0:
                at_paragraph.append({"tag": "text", "text": " "})
            at_paragraph.append({
                "tag": "at", 
                "user_id": at["user_id"], 
                "user_name": at["user_name"]
            })
        at_paragraph.append({"tag": "text", "text": " 请查看~"})
        paragraphs.append(at_paragraph)
    
    return paragraphs

def main():
    parser = argparse.ArgumentParser(description='发送飞书 Post 消息')
    parser.add_argument('--chat-id', required=True, help='群聊 ID (oc_xxx)')
    parser.add_argument('--title', required=True, help='消息标题')
    parser.add_argument('--content', required=True, help='消息正文')
    parser.add_argument('--at', action='append', help='@ 用户，格式: "open_id:姓名"，可多次使用')
    parser.add_argument('--image-key', help='要转发的图片 image_key')
    parser.add_argument('--message-link', help='消息链接（当图片无法下载时使用）')
    parser.add_argument('--reply-to', help='引用的原消息 ID（用于回复特定消息）')
    parser.add_argument('--app-id', help='飞书 App ID（可选，默认从配置读取）')
    parser.add_argument('--app-secret', help='飞书 App Secret（可选，默认从配置读取）')
    
    args = parser.parse_args()
    
    # 加载凭证
    app_id = args.app_id
    app_secret = args.app_secret
    if not app_id or not app_secret:
        app_id, app_secret = load_feishu_creds()
        if not app_id or not app_secret:
            raise Exception("Feishu credentials not found in config")
    
    token = get_tenant_access_token(app_id, app_secret)
    
    # 解析 @ 列表
    at_list = parse_at_list(args.at) if args.at else None
    
    # 处理图片转发（下载 + 重新上传）
    new_image_key = None
    temp_file = None
    message_link = args.message_link
    
    if args.image_key:
        try:
            print(f"📥 正在下载图片: {args.image_key}...")
            temp_file = download_image(args.image_key, token)
            print(f"📤 正在上传图片到目标群...")
            new_image_key = upload_image(temp_file, token)
            print(f"✅ 图片上传成功: {new_image_key}")
        except Exception as e:
            print(f"⚠️ 图片处理失败: {e}")
            print(f"💡 将使用消息链接替代")
            new_image_key = None
            # 如果没有提供消息链接，尝试构造一个
            if not message_link:
                print(f"⚠️ 请提供 --message-link 参数以便查看原图")
        finally:
            # 清理临时文件
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
    
    # 构造内容段落
    content_blocks = build_content_paragraphs(args.content, at_list, new_image_key, message_link)
    
    # 发送消息
    try:
        result = send_post_message(
            chat_id=args.chat_id,
            title=args.title,
            content_blocks=content_blocks,
            app_id=app_id,
            app_secret=app_secret,
            reply_to=args.reply_to
        )
        
        if result.get('code') == 0:
            print(f"✅ 消息发送成功！")
            print(f"   Message ID: {result['data']['message_id']}")
            print(f"   Chat ID: {result['data']['chat_id']}")
        else:
            print(f"❌ 发送失败: {result.get('msg')}")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

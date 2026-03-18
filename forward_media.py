#!/usr/bin/env python3
"""
飞书富媒体消息转发工具
支持：文字、图片、文件的跨群转发
转发完成后自动清理临时文件
"""

import json
import os
import sys
import urllib.request
import ssl
import tempfile
import shutil
from typing import List, Dict, Optional

# 配置
OPENCLAW_CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")
CONTACTS_FILE = "/home/admin/openclaw/workspace/feishu_contacts.json"
TEMP_DIR = tempfile.gettempdir()  # 使用系统临时目录

def load_contacts() -> Dict:
    """加载联系人映射表"""
    if not os.path.exists(CONTACTS_FILE):
        return {}
    
    with open(CONTACTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_user_name(user_id: str) -> str:
    """根据user_id获取用户姓名"""
    contacts = load_contacts()
    return contacts.get(user_id, {}).get('name', '')

def build_at_list(user_ids: List[str]) -> List[Dict]:
    """
    根据user_id列表构建@列表（自动查询姓名）
    
    Args:
        user_ids: open_id列表
    
    Returns:
        @列表，每个元素包含user_id和user_name
    """
    at_list = []
    for uid in user_ids:
        name = get_user_name(uid)
        at_list.append({
            "user_id": uid,
            "user_name": name
        })
    return at_list

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

def download_file(file_key: str, file_name: str, token: str) -> str:
    """下载普通文件，返回本地路径"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # 获取下载链接
    url = f"https://open.feishu.cn/open-apis/im/v1/files/{file_key}"
    req = urllib.request.Request(
        url,
        headers={'Authorization': f'Bearer {token}'},
        method='GET'
    )
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get('code') != 0:
                print(f"获取下载链接失败: {result}")
                return None
            
            download_url = result.get('data', {}).get('file_url')
            if not download_url:
                return None
    except Exception as e:
        print(f"获取下载链接异常: {e}")
        return None
    
    # 下载文件到临时目录
    local_path = os.path.join(TEMP_DIR, f"feishu_forward_file_{file_key}_{file_name}")
    
    try:
        req = urllib.request.Request(download_url, method='GET')
        with urllib.request.urlopen(req, context=ctx, timeout=60) as response:
            with open(local_path, 'wb') as f:
                f.write(response.read())
        return local_path
    except Exception as e:
        print(f"下载文件异常: {e}")
        return None

def download_image(image_key: str, token: str) -> str:
    """下载图片，返回本地路径"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # 图片使用 images API
    url = f"https://open.feishu.cn/open-apis/im/v1/images/{image_key}"
    req = urllib.request.Request(
        url,
        headers={'Authorization': f'Bearer {token}'},
        method='GET'
    )
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get('code') != 0:
                print(f"获取图片下载链接失败: {result}")
                return None
            
            download_url = result.get('data', {}).get('image_url')
            if not download_url:
                return None
    except Exception as e:
        print(f"获取图片下载链接异常: {e}")
        return None
    
    # 下载图片到临时目录
    local_path = os.path.join(TEMP_DIR, f"feishu_forward_img_{image_key}.png")
    
    try:
        req = urllib.request.Request(download_url, method='GET')
        with urllib.request.urlopen(req, context=ctx, timeout=60) as response:
            with open(local_path, 'wb') as f:
                f.write(response.read())
        print(f"图片下载成功: {local_path}")
        return local_path
    except Exception as e:
        print(f"下载图片异常: {e}")
        return None

def download_media(file_key: str, file_name: str, token: str, media_type: str = 'file') -> str:
    """
    下载媒体文件（兼容旧代码）
    
    Args:
        file_key: 文件或图片的key
        file_name: 文件名
        token: 访问令牌
        media_type: 'file' 或 'image'
    """
    if media_type == 'image':
        return download_image(file_key, token)
    else:
        return download_file(file_key, file_name, token)

def upload_image(file_path: str, token: str) -> Optional[str]:
    """上传图片到飞书，返回 image_key"""
    import urllib.request
    import ssl
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    
    # 构造 multipart/form-data
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    body = []
    body.append(f'--{boundary}'.encode())
    body.append(b'Content-Disposition: form-data; name="image_type"')
    body.append(b'')
    body.append(b'message')
    body.append(f'--{boundary}'.encode())
    body.append(f'Content-Disposition: form-data; name="image"; filename="{os.path.basename(file_path)}"'.encode())
    body.append(b'Content-Type: image/png')
    body.append(b'')
    body.append(file_data)
    body.append(f'--{boundary}--'.encode())
    
    body = b'\r\n'.join(body)
    
    url = "https://open.feishu.cn/open-apis/im/v1/images"
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': f'multipart/form-data; boundary={boundary}'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get('code') == 0:
                return result.get('data', {}).get('image_key')
            else:
                print(f"上传图片失败: {result}")
                return None
    except Exception as e:
        print(f"上传图片异常: {e}")
        return None

def send_rich_message(chat_id: str, title: str, text_content: str, 
                      image_keys: List[str] = None, at_list: List[Dict] = None,
                      reply_to: str = None):
    """发送富文本消息（支持图片和@，支持引用回复）"""
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        print("无法获取飞书凭证")
        return False
    
    token = get_tenant_access_token(app_id, app_secret)
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # 构造内容块
    content_blocks = []
    
    # 添加文字内容
    content_blocks.append([{"tag": "text", "text": text_content}])
    
    # 添加图片
    if image_keys:
        for img_key in image_keys:
            content_blocks.append([{
                "tag": "img",
                "image_key": img_key
            }])
    
    # 添加 @ 人员
    if at_list:
        at_paragraph = [{"tag": "text", "text": "请处理："}]
        for at in at_list:
            at_paragraph.append({
                "tag": "at",
                "user_id": at["user_id"],
                "user_name": at.get("user_name", "")
            })
            at_paragraph.append({"tag": "text", "text": " "})
        content_blocks.append(at_paragraph)
    
    message_content = {
        "zh_cn": {
            "title": title,
            "content": content_blocks
        }
    }
    
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    payload = {
        "receive_id": chat_id,
        "msg_type": "post",
        "content": json.dumps(message_content, ensure_ascii=False)
    }
    
    # 添加引用回复（如果需要）
    if reply_to:
        payload["reply_to"] = reply_to
    
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
                print(f"发送消息失败: {result}")
                return False
    except Exception as e:
        print(f"发送消息异常: {e}")
        return False

def forward_with_media(source_message: dict, target_chat_id: str, 
                       title: str, at_list: List[Dict] = None,
                       reply_to: str = None) -> bool:
    """
    转发消息（含富媒体）到目标群
    
    Args:
        source_message: 源消息对象（包含文本、图片等信息）
        target_chat_id: 目标群ID
        title: 消息标题
        at_list: @人员列表
        reply_to: 引用的原消息ID（用于回复特定消息）
    
    Returns:
        bool: 是否成功
    """
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        return False
    
    token = get_tenant_access_token(app_id, app_secret)
    downloaded_files = []  # 记录下载的文件，用于后续清理
    uploaded_images = []   # 记录上传的图片key
    
    try:
        # 提取文字内容
        text_content = source_message.get('text', '')
        
        # 处理图片
        images = source_message.get('images', [])
        for img in images:
            file_key = img.get('file_key')
            file_name = img.get('file_name', 'image.png')
            
            if file_key:
                # 下载图片（使用 image 类型）
                local_path = download_media(file_key, file_name, token, media_type='image')
                if local_path:
                    downloaded_files.append(local_path)
                    
                    # 上传图片获取 image_key
                    image_key = upload_image(local_path, token)
                    if image_key:
                        uploaded_images.append(image_key)
        
        # 发送消息
        success = send_rich_message(
            chat_id=target_chat_id,
            title=title,
            text_content=text_content,
            image_keys=uploaded_images,
            at_list=at_list,
            reply_to=reply_to
        )
        
        return success
        
    finally:
        # 清理下载的临时文件
        for file_path in downloaded_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"已清理临时文件: {file_path}")
            except Exception as e:
                print(f"清理文件失败 {file_path}: {e}")

def main():
    """测试用法"""
    # 示例：转发一条带图片的消息
    test_message = {
        'text': '这是一个测试反馈，带图片说明',
        'images': [
            {'file_key': 'test_key', 'file_name': 'test.png'}
        ]
    }
    
    at_list = [
        {"user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "施嘉科"},
        {"user_id": "ou_cbcd1090961b620a4500ce68e3c81952", "user_name": "宋广智"}
    ]
    
    # 注意：需要提供真实的 file_key 才能测试
    print("富媒体转发工具已就绪")
    print("使用方式：from forward_media import forward_with_media")

if __name__ == '__main__':
    main()

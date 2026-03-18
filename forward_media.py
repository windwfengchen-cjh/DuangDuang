#!/usr/bin/env python3
"""
飞书图片转发工具 - 简化版
核心功能：下载图片 → 上传获取新 image_key

核心限制：机器人只能下载自己发送的图片
其他用户发送的图片返回错误："The app is not the resource sender"
"""

import json
import os
import urllib.request
import ssl
import tempfile
from typing import Optional, Tuple

# 配置
OPENCLAW_CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")
TEMP_DIR = tempfile.gettempdir()


def load_feishu_creds() -> Tuple[Optional[str], Optional[str]]:
    """从 OpenClaw 配置加载飞书凭证"""
    try:
        with open(OPENCLAW_CONFIG, 'r') as f:
            config = json.load(f)
            feishu_config = config.get('channels', {}).get('feishu', {})
            return feishu_config.get('appId'), feishu_config.get('appSecret')
    except Exception as e:
        return None, None


def get_tenant_access_token(app_id: str, app_secret: str) -> Optional[str]:
    """获取飞书 tenant_access_token"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode('utf-8')
    
    req = urllib.request.Request(
        url, data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get('code') == 0:
                return result.get('tenant_access_token')
    except Exception:
        pass
    return None


def download_image_by_resource(message_id: str, file_key: str, token: str) -> Tuple[bool, str]:
    """
    使用 Resource API 下载图片（支持下载任何人发的图片）
    
    Args:
        message_id: 消息 ID
        file_key: 文件/图片 key
        token: tenant_access_token
    
    Returns:
        (success: bool, result: str)
        - success=True: result 是本地文件路径
        - success=False: result 是错误信息
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # 使用 Resource API 直接下载图片
    url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/resources/{file_key}?type=image"
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'}, method='GET')
    
    local_path = os.path.join(TEMP_DIR, f"feishu_img_{file_key}.jpg")
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60) as response:
            # 直接获取图片二进制数据
            image_data = response.read()
            
            with open(local_path, 'wb') as f:
                f.write(image_data)
            
            print(f"✅ 通过 Resource API 下载图片成功：{len(image_data)} bytes")
            return True, local_path
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        try:
            error_data = json.loads(error_body)
            error_msg = error_data.get('msg', str(e))
        except:
            error_msg = str(e)
        return False, f"Resource API 下载失败：{error_msg}"
    except Exception as e:
        return False, f"Resource API 下载异常：{str(e)}"


def download_image(image_key: str, token: str) -> Tuple[bool, str]:
    """
    使用 Images API 下载图片（只能下载自己发送的图片）
    
    Args:
        image_key: 飞书图片 key
        token: tenant_access_token
    
    Returns:
        (success: bool, result: str)
        - success=True: result 是本地文件路径
        - success=False: result 是错误信息
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # 1. 获取下载链接
    url = f"https://open.feishu.cn/open-apis/im/v1/images/{image_key}"
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'}, method='GET')
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            if result.get('code') != 0:
                error_msg = result.get('msg', 'Unknown error')
                # 检测权限错误
                if 'not the resource sender' in error_msg or 'not the resource owner' in error_msg:
                    return False, f"权限错误：{error_msg}\n说明：机器人只能下载自己发送的图片，无法下载其他用户发送的图片"
                return False, f"获取下载链接失败：{error_msg}"
            
            download_url = result.get('data', {}).get('image_url')
            if not download_url:
                return False, "获取下载链接成功，但没有返回 URL"
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        try:
            error_data = json.loads(error_body)
            error_msg = error_data.get('msg', str(e))
        except:
            error_msg = str(e)
        
        # 检测权限错误
        if 'not the resource sender' in error_msg or 'not the resource owner' in error_msg:
            return False, f"权限错误：机器人只能下载自己发送的图片，无法下载其他用户发送的图片\n({error_msg})"
        return False, f"HTTP 错误：{error_msg}"
    except Exception as e:
        return False, f"获取下载链接异常：{str(e)}"
    
    # 2. 下载图片
    local_path = os.path.join(TEMP_DIR, f"feishu_img_{image_key}.png")
    
    try:
        req = urllib.request.Request(download_url, method='GET')
        with urllib.request.urlopen(req, context=ctx, timeout=60) as response:
            with open(local_path, 'wb') as f:
                f.write(response.read())
        return True, local_path
    except Exception as e:
        return False, f"下载图片异常：{str(e)}"


def upload_image(file_path: str, token: str) -> Tuple[bool, str]:
    """
    上传图片到飞书
    
    Args:
        file_path: 本地图片路径
        token: tenant_access_token
    
    Returns:
        (success: bool, result: str)
        - success=True: result 是新的 image_key
        - success=False: result 是错误信息
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    
    # 构造 multipart/form-data
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
    except Exception as e:
        return False, f"读取文件失败：{str(e)}"
    
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
        url, data=body,
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
                image_key = result.get('data', {}).get('image_key')
                return True, image_key
            else:
                return False, f"上传失败：{result.get('msg', 'Unknown error')}"
    except Exception as e:
        return False, f"上传异常：{str(e)}"


def cleanup_temp_file(file_path: str) -> None:
    """
    清理临时文件，失败不抛出异常
    
    Args:
        file_path: 要删除的文件路径
    """
    if not file_path or not os.path.exists(file_path):
        return
    
    try:
        os.remove(file_path)
        print(f"✅ 本地图片已删除：{file_path}")
    except Exception as e:
        print(f"⚠️ 删除本地图片失败：{file_path}，错误：{e}")


def forward_image(image_key: str, message_id: str = None) -> Tuple[bool, str]:
    """
    转发图片：下载原图 → 上传获取新 image_key
    
    注意：无论成功或失败，都会自动清理本地临时文件
    
    Args:
        image_key: 原图片的 image_key
        message_id: 消息 ID（可选，提供后可使用 Resource API 下载任何人发的图片）
    
    Returns:
        (success: bool, result: str)
        - success=True: result 是新的 image_key
        - success=False: result 是错误信息
    """
    local_path = None
    
    try:
        # 1. 获取凭证
        app_id, app_secret = load_feishu_creds()
        if not app_id or not app_secret:
            return False, "无法加载飞书凭证"
        
        token = get_tenant_access_token(app_id, app_secret)
        if not token:
            return False, "无法获取 access_token"
        
        # 2. 下载图片
        # 优先使用 Resource API（如果提供了 message_id）
        if message_id:
            print(f"📥 使用 Resource API 下载图片（支持任何人发的图片）...")
            success, result = download_image_by_resource(message_id, image_key, token)
            if not success:
                print(f"⚠️ Resource API 失败，回退到 Images API...")
                success, result = download_image(image_key, token)
        else:
            print(f"📥 使用 Images API 下载图片...")
            success, result = download_image(image_key, token)
        
        if not success:
            return False, f"下载失败：{result}"
        
        local_path = result
        print(f"✅ 图片下载成功：{local_path}")
        
        # 3. 上传图片
        success, new_image_key = upload_image(local_path, token)
        
        if success:
            return True, new_image_key
        else:
            return False, f"上传失败：{new_image_key}"
    
    finally:
        # 4. 确保清理临时文件（无论成功或失败都会执行）
        cleanup_temp_file(local_path)


def main():
    """
    使用示例：尝试转发一张图片
    
    用法：
        python forward_media.py <image_key> [message_id]
    
    示例：
        python forward_media.py img_v3_02vt_xxx
        python forward_media.py img_v3_02vt_xxx om_xxx
    """
    import sys
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        image_key = sys.argv[1]
    else:
        # 示例 image_key（需要替换为真实的）
        image_key = "your_image_key_here"
        print("用法：python forward_media.py <image_key> [message_id]")
        print("       python forward_media.py img_v3_02vt_xxx")
        print("       python forward_media.py img_v3_02vt_xxx om_xxx")
        print()
        print(f"将使用示例 key：{image_key}")
        print()
    
    # 可选的 message_id（用于 Resource API）
    message_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"开始转发图片：{image_key}")
    if message_id:
        print(f"使用消息 ID：{message_id}（可通过 Resource API 下载任何人发的图片）")
    print("-" * 40)
    
    success, result = forward_image(image_key, message_id)
    
    print("-" * 40)
    if success:
        print(f"✅ 转发成功！")
        print(f"新 image_key：{result}")
    else:
        print(f"❌ 转发失败")
        print(f"错误信息：{result}")


if __name__ == '__main__':
    main()

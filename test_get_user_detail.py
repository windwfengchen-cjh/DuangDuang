#!/usr/bin/env python3
"""
测试获取用户详细信息（包括邮箱、手机号）
检查是否有其他联系方式可以绕过飞书限制
"""

import json
import os
import ssl
import urllib.request
from typing import Dict, Tuple

OPENCLAW_CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")

# 目标用户 (梁思洁)
TARGET_USER_ID = "ou_d03303783b5538c608b540dc8ad9ac87"

def load_feishu_creds() -> Tuple[str, str]:
    """加载飞书凭证"""
    with open(OPENCLAW_CONFIG, 'r') as f:
        config = json.load(f)
        feishu_config = config.get('channels', {}).get('feishu', {})
        return feishu_config.get('appId'), feishu_config.get('appSecret')

def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    """获取 tenant_access_token"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    
    with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
        result = json.loads(response.read().decode('utf-8'))
        if result.get('code') != 0:
            raise Exception(f"获取token失败: {result}")
        return result.get('tenant_access_token')

def get_user_detail(token: str, user_id: str) -> Dict:
    """获取用户详细信息"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = f"https://open.feishu.cn/open-apis/contact/v3/users/{user_id}?user_id_type=open_id"
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'}, method='GET')
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        try:
            error_data = json.loads(error_body)
            return error_data
        except:
            return {'code': e.code, 'msg': error_body}

def get_user_emails_batch(token: str, user_ids: list) -> Dict:
    """批量获取用户邮箱"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = "https://open.feishu.cn/open-apis/contact/v3/users/batch_get_id?user_id_type=open_id"
    data = json.dumps({"user_ids": user_ids}).encode('utf-8')
    req = urllib.request.Request(
        url, 
        data=data,
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        try:
            error_data = json.loads(error_body)
            return error_data
        except:
            return {'code': e.code, 'msg': error_body}

def main():
    print("=" * 70)
    print("获取用户详细信息测试")
    print("=" * 70)
    
    # 加载凭证
    app_id, app_secret = load_feishu_creds()
    token = get_tenant_access_token(app_id, app_secret)
    print(f"✅ Token获取成功\n")
    
    # 获取用户详细信息
    print(f"正在获取用户 {TARGET_USER_ID} 的详细信息...")
    result = get_user_detail(token, TARGET_USER_ID)
    
    if result.get('code') == 0:
        user = result.get('data', {}).get('user', {})
        print(f"✅ 获取成功！")
        print(f"\n用户信息:")
        print(f"  - Open ID: {user.get('open_id')}")
        print(f"  - Union ID: {user.get('union_id')}")
        print(f"  - User ID: {user.get('user_id')}")
        print(f"  - 姓名: {user.get('name')}")
        print(f"  - 英文名: {user.get('en_name')}")
        print(f"  - 邮箱: {user.get('email', 'N/A')}")
        print(f"  - 手机号: {user.get('mobile', 'N/A')}")
        print(f"  - 部门: {user.get('department_ids', [])}")
        print(f"  - 状态: {'已激活' if user.get('status', {}).get('is_activated') else '未激活'}")
        
        email = user.get('email')
        mobile = user.get('mobile')
        
        if email:
            print(f"\n💡 发现邮箱: {email}")
            print(f"   可以探索通过邮件发送通知的方案")
        if mobile:
            print(f"\n💡 发现手机号: {mobile}")
            print(f"   可以探索通过短信发送通知的方案")
        
        if not email and not mobile:
            print(f"\n⚠️ 未获取到邮箱或手机号")
            print(f"   无法使用邮件/短信方案")
    else:
        print(f"❌ 获取失败")
        print(f"   错误码: {result.get('code')}")
        print(f"   错误信息: {result.get('msg')}")
        
        # 检查是否是权限问题
        if result.get('code') == 41050 or 'authority' in result.get('msg', '').lower():
            print(f"\n⚠️ 权限不足，无法获取用户详细信息")
            print(f"   需要申请 contact:user.base:readonly 或更高级别权限")

if __name__ == '__main__':
    main()

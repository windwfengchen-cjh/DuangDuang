#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import time
import requests
from datetime import datetime

DEBUG = True
FEISHU_API_BASE = "https://open.feishu.cn/open-apis"

def log_debug(title, content):
    if DEBUG:
        print(f"\n{'='*70}")
        print(f"【{title}】")
        print(f"{'='*70}")
        if isinstance(content, (dict, list)):
            print(json.dumps(content, indent=2, ensure_ascii=False))
        else:
            print(content)
        print(f"{'='*70}\n")

def load_feishu_creds():
    try:
        config_path = os.path.expanduser("~/.openclaw/openclaw.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
            feishu_config = config.get('channels', {}).get('feishu', {})
            return feishu_config.get('appId'), feishu_config.get('appSecret')
    except Exception as e:
        print(f"❌ 加载配置失败: {e}")
        return None, None

def get_tenant_access_token(app_id, app_secret):
    url = f"{FEISHU_API_BASE}/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {"app_id": app_id, "app_secret": app_secret}
    
    log_debug("获取 Token - 请求", {"url": url, "body": {**data, "app_secret": "***"}})
    
    resp = requests.post(url, headers=headers, json=data)
    result = resp.json()
    
    log_debug("获取 Token - 响应", {"status": resp.status_code, "body": result})
    
    if result.get("code") != 0:
        raise Exception(f"获取 token 失败: {result}")
    
    return result.get("tenant_access_token")

def create_research_chat_debug(token, requirement_id, requirement_content, requester_name):
    print(f"\n{'='*70}")
    print(f"【步骤 1: 创建需求调研群】")
    print(f"{'='*70}")
    
    today = datetime.now().strftime("%m%d")
    chat_name = f"需求调研-{requester_name}-{today}"
    summary = requirement_content[:30] + "..." if len(requirement_content) > 30 else requirement_content
    description = f"需求调研群\n需求记录: {requirement_id}\n摘要: {summary}"
    
    print(f"群名称: {chat_name}")
    print(f"群描述: {description}")
    
    url = f"{FEISHU_API_BASE}/im/v1/chats"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"name": chat_name, "description": description, "chat_mode": "group", "chat_type": "private"}
    
    log_debug("创建群聊 - 请求", {"url": url, "headers": {**headers, "Authorization": "Bearer ***"}, "body": body})
    
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=15)
        result = resp.json()
        
        log_debug("创建群聊 - 响应", {"status": resp.status_code, "body": result})
        
        if result.get("code") == 0:
            chat_id = result.get("data", {}).get("chat_id")
            print(f"✅ 群聊创建成功! Chat ID: {chat_id}")
            time.sleep(3)
            return {"chat_id": chat_id, "chat_name": chat_name}
        else:
            print(f"❌ 群聊创建失败: {result.get('msg')}")
            return None
    except Exception as e:
        print(f"❌ 创建群聊异常: {e}")
        return None

def verify_chat_exists(token, chat_id):
    print(f"\n{'='*70}")
    print(f"【步骤 2: 验证群聊是否存在】")
    print(f"{'='*70}")
    
    url = f"{FEISHU_API_BASE}/im/v1/chats/{chat_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    log_debug("验证群聊 - 请求", {"url": url})
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        result = resp.json()
        
        log_debug("验证群聊 - 响应", {"status": resp.status_code, "body": result})
        
        if result.get("code") == 0:
            chat_info = result.get("data", {})
            print(f"✅ 群聊验证成功!")
            print(f"   名称: {chat_info.get('name')}")
            print(f"   类型: {chat_info.get('chat_type')}")
            print(f"   成员数: {chat_info.get('member_count', 'N/A')}")
            return chat_info
        else:
            print(f"❌ 群聊验证失败: {result.get('msg')}")
            return None
    except Exception as e:
        print(f"❌ 验证异常: {e}")
        return None

def main():
    print("\n" + "="*70)
    print("【需求跟进 - 创建群调试工具】")
    print("="*70)
    
    requirement_content = "杭州甄选的号卡接口帮忙对接一下（调试测试）"
    requester_id = "ou_a41f4c2c7b005523668988a9bfd2d778"
    boss_id = "ou_3e48baef1bd71cc89fb5a364be55cafc"
    
    print(f"\n需求内容: {requirement_content}")
    print(f"需求方: {requester_id}")
    print(f"Boss: {boss_id}")
    
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        print("❌ 加载凭证失败")
        return
    
    try:
        token = get_tenant_access_token(app_id, app_secret)
        print(f"✅ Token 获取成功: {token[:20]}...")
    except Exception as e:
        print(f"❌ 获取 Token 失败: {e}")
        return
    
    requirement_id = f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # 创建群聊
    chat_info = create_research_chat_debug(token, requirement_id, requirement_content, "杨政航")
    
    if not chat_info:
        print("\n❌ 群聊创建失败，调试结束")
        return
    
    # 验证群聊
    chat_verify = verify_chat_exists(token, chat_info["chat_id"])
    
    print("\n" + "="*70)
    print("【调试结果】")
    print("="*70)
    print(f"群聊创建: {'✅ 成功' if chat_info else '❌ 失败'}")
    print(f"群聊验证: {'✅ 成功' if chat_verify else '⚠️ 失败'}")
    if chat_info:
        print(f"Chat ID: {chat_info['chat_id']}")

if __name__ == "__main__":
    main()

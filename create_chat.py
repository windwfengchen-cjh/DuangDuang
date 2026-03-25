#!/usr/bin/env python3
"""创建需求调研群并添加成员"""
import sys
sys.path.insert(0, '/home/admin/openclaw/workspace')

import requests
from feishu_config import get_app_id, get_app_secret

# 获取 tenant_access_token
app_id, app_secret = get_app_id(), get_app_secret()
auth_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
resp = requests.post(auth_url, json={"app_id": app_id, "app_secret": app_secret})
token = resp.json().get("tenant_access_token")
print(f"Got token: {token[:20]}...")

# 创建群聊
create_url = "https://open.feishu.cn/open-apis/im/v1/chats"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
payload = {
    "name": "需求调研-杨政航-0325",
    "description": "保险系统对接需求调研群",
    "owner_id": "ou_3e48baef1bd71cc89fb5a364be55cafc",
    "chat_mode": "group"
}
resp = requests.post(create_url, headers=headers, json=payload)
result = resp.json()
print(f"Create chat response: {result}")

if result.get("code") == 0:
    chat_id = result["data"]["chat_id"]
    print(f"Chat created: {chat_id}")
    
    # 添加成员
    member_url = f"https://open.feishu.cn/open-apis/im/v1/chats/{chat_id}/members"
    member_payload = {
        "member_ids": ["ou_a41f4c2c7b005523668988a9bfd2d778", "ou_3e48baef1bd71cc89fb5a364be55cafc"],
        "member_type": "user"
    }
    resp2 = requests.post(member_url, headers=headers, json=member_payload)
    print(f"Add members response: {resp2.json()}")
    
    # 输出 chat_id 供后续使用
    print(f"CHAT_ID:{chat_id}")
else:
    print(f"Failed to create chat: {result.get('msg')}")
    sys.exit(1)

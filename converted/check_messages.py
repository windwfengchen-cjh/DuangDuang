#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查群消息详细内容"""

import sys
import os
import json
import requests

sys.path.insert(0, '/home/admin/openclaw/workspace')
from feishu_config import get_feishu_credentials

FILE_KEY = "file_v3_00103_3ef15c26-a68b-42ac-ac84-2ac099a9852g"
CHAT_ID = "oc_59539a59e696491bd93241ecd9b8c80d"

def get_access_token(app_id, app_secret):
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    response = requests.post(url, json={"app_id": app_id, "app_secret": app_secret})
    return response.json().get("tenant_access_token")

def check_messages(access_token):
    """检查群消息"""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    url = f"https://open.feishu.cn/open-apis/im/v1/messages"
    params = {
        "container_id_type": "chat",
        "container_id": CHAT_ID,
        "page_size": 50
    }
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("code") == 0:
            messages = result.get("data", {}).get("items", [])
            
            print("群消息列表:\n")
            for i, msg in enumerate(messages):
                msg_type = msg.get("msg_type", "")
                content = msg.get("body", {}).get("content", "")
                sender = msg.get("sender", {}).get("sender_id", {}).get("open_id", "unknown")[:20]
                create_time = msg.get("create_time", "")[:19]
                
                print(f"[{i+1}] {create_time} | {msg_type} | from {sender}")
                
                # 检查文件类型消息
                if "file" in msg_type.lower():
                    print(f"    文件类型消息!")
                    print(f"    内容: {content}")
                    try:
                        c = json.loads(content)
                        print(f"    解析: {json.dumps(c, indent=2, ensure_ascii=False)}")
                    except:
                        pass
                    print()
                
                # 检查目标文件key是否匹配
                if FILE_KEY in content:
                    print(f"    ✓✓✓ 匹配到目标文件!")
                    print(f"    内容: {content}")
                
                # 显示部分文本消息
                if msg_type == "text" and i < 5:
                    try:
                        c = json.loads(content)
                        text = c.get("text", "")[:100]
                        print(f"    文本: {text}...")
                    except:
                        pass

def main():
    print("=" * 60)
    print("检查群消息详细内容")
    print("=" * 60)
    
    app_id, app_secret = get_feishu_credentials()
    access_token = get_access_token(app_id, app_secret)
    
    check_messages(access_token)

if __name__ == "__main__":
    main()

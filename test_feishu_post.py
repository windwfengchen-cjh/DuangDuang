#!/usr/bin/env python3
"""测试发送飞书 post 消息"""

import json
import requests
import os

# 从环境变量或配置文件获取
APP_ID = os.getenv("FEISHU_APP_ID", "cli_a9390dce99f9dbc9")
APP_SECRET = os.getenv("FEISHU_APP_SECRET", "npTtb8fp0ZwefHldLzFLZf8o4GrdWhP5")

# 获取 tenant_access_token
def get_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={
        "app_id": APP_ID,
        "app_secret": APP_SECRET
    })
    return resp.json().get("tenant_access_token")

# 发送 post 消息
def send_post_message(chat_id, title, content_list):
    token = get_token()
    url = f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    
    # 构造消息体 - 飞书 post 消息格式
    message_content = {
        "zh_cn": {
            "title": title,
            "content": content_list
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

if __name__ == "__main__":
    # 构造测试消息内容 - 需要加上 user_name 才能正确显示
    content = [
        [{"tag": "text", "text": "原消息：这是一条测试反馈消息"}],
        [{"tag": "text", "text": "反馈人："}, {"tag": "at", "user_id": "ou_3e48baef1bd71cc89fb5a364be55cafc", "user_name": "陈俊洪"}],
        [
            {"tag": "at", "user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "施嘉科"},
            {"tag": "text", "text": " "},
            {"tag": "at", "user_id": "ou_cbcd1090961b620a4500ce68e3c81952", "user_name": "宋广智"},
            {"tag": "text", "text": " 请查看~"}
        ]
    ]
    
    result = send_post_message(
        chat_id="oc_a016323a9fda4263ab5a27976065088e",
        title="【产研反馈-测试4-带名字】",
        content_list=content
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))

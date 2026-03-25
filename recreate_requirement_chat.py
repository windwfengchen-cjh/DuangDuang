#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重新创建需求调研群（第二次）"""

import requests
import json
import sys

# 导入飞书凭证
from feishu_config import get_feishu_credentials

# 飞书API基础URL
BASE_URL = "https://open.feishu.cn/open-apis"

# 记录ID
RECORD_ID = "recveKgB6l8jLP"

# 用户ID
USER_CHEN = "ou_3e48baef1bd71cc89fb5a364be55cafc"  # 陈俊洪
USER_YANG = "ou_a41f4c2c7b005523668988a9bfd2d778"  # 杨政航

# 新群信息
CHAT_NAME = "需求调研-陈俊洪-0324"
CHAT_DESC = "抖音小程序客服工单对接飞书需求调研"

# Bitable信息（从其他脚本推断）
APP_TOKEN = "YMRYbwynTaNLI2sd0EccGVT1nwb"  # 需求调研跟进表
TABLE_ID = "tblF60wF4S5PE1Ju"  # 需求调研表


def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    """获取 tenant_access_token"""
    url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": app_id, "app_secret": app_secret})
    result = resp.json()
    if result.get("code") == 0:
        return result["tenant_access_token"]
    raise Exception(f"获取token失败: {result}")


def create_chat(token: str) -> str:
    """创建群聊，返回chat_id"""
    url = f"{BASE_URL}/im/v1/chats"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": CHAT_NAME,
        "description": CHAT_DESC,
        "owner_id": USER_CHEN,
        "chat_mode": "group",
        "chat_type": "private"
    }
    resp = requests.post(url, headers=headers, json=data)
    result = resp.json()
    print(f"创建群响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get("code") == 0:
        chat_id = result["data"]["chat_id"]
        print(f"✅ 群创建成功: {chat_id}")
        return chat_id
    raise Exception(f"创建群失败: {result}")


def add_chat_members(token: str, chat_id: str):
    """添加群成员"""
    url = f"{BASE_URL}/im/v1/chats/{chat_id}/members"
    headers = {"Authorization": f"Bearer {token}"}
    
    members = [USER_CHEN, USER_YANG]
    data = {
        "id_list": members,
        "member_id_type": "open_id"
    }
    resp = requests.post(url, headers=headers, json=data)
    result = resp.json()
    print(f"添加成员响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get("code") == 0:
        print(f"✅ 成员添加成功")
        return True
    raise Exception(f"添加成员失败: {result}")


def get_chat_members(token: str, chat_id: str) -> list:
    """获取群成员列表"""
    url = f"{BASE_URL}/im/v1/chats/{chat_id}/members"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"member_id_type": "open_id"}
    
    resp = requests.get(url, headers=headers, params=params)
    result = resp.json()
    
    if result.get("code") == 0:
        items = result.get("data", {}).get("items", [])
        print(f"✅ 群成员数量: {len(items)}")
        for item in items:
            print(f"   - {item.get('member_id')} ({item.get('name', '未知')})")
        return items
    raise Exception(f"获取成员失败: {result}")


def send_welcome_message(token: str, chat_id: str):
    """发送欢迎消息"""
    url = f"{BASE_URL}/im/v1/messages"
    headers = {"Authorization": f"Bearer {token}"}
    
    message = """📋 需求调研群已创建

本群用于沟通【抖音小程序客服工单对接飞书】需求

请陈总补充以下信息：
1. 项目背景：为什么要做这个项目？
2. 目标用户：主要服务哪些用户？
3. 核心痛点：当前面临的主要问题？
4. 预期方案：希望达到什么效果？

收到信息后我会整理需求文档，感谢配合！"""
    
    data = {
        "receive_id": chat_id,
        "msg_type": "text",
        "content": json.dumps({"text": message})
    }
    params = {"receive_id_type": "chat_id"}
    
    resp = requests.post(url, headers=headers, params=params, json=data)
    result = resp.json()
    print(f"发送消息响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get("code") == 0:
        print(f"✅ 引导消息发送成功")
        return True
    raise Exception(f"发送消息失败: {result}")


def update_bitable_record(token: str, record_id: str, chat_id: str):
    """更新Bitable记录"""
    url = f"{BASE_URL}/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/{record_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    # 记录新群号到备注字段
    remark = f"新群号（第二次创建）: {chat_id}"
    data = {
        "fields": {
            "备注": remark
        }
    }
    
    resp = requests.put(url, headers=headers, json=data)
    result = resp.json()
    print(f"更新记录响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get("code") == 0:
        print(f"✅ Bitable记录更新成功")
        return True
    raise Exception(f"更新记录失败: {result}")


def main():
    print("=" * 60)
    print("重新创建需求调研群（第二次）")
    print("=" * 60)
    
    # 1. 获取凭证
    print("\n[1/6] 读取飞书凭证...")
    app_id, app_secret = get_feishu_credentials()
    token = get_tenant_access_token(app_id, app_secret)
    print(f"✅ Token获取成功: {token[:20]}...")
    
    # 2. 创建群
    print("\n[2/6] 创建群聊...")
    chat_id = create_chat(token)
    
    # 3. 添加成员
    print("\n[3/6] 添加群成员...")
    add_chat_members(token, chat_id)
    
    # 4. 验证成员
    print("\n[4/6] 验证群成员...")
    members = get_chat_members(token, chat_id)
    
    # 检查两个成员是否都在
    member_ids = [m.get("member_id") for m in members]
    if USER_CHEN not in member_ids:
        print(f"⚠️ 陈俊洪未在群中")
    if USER_YANG not in member_ids:
        print(f"⚠️ 杨政航未在群中")
    
    if USER_CHEN in member_ids and USER_YANG in member_ids:
        print("✅ 所有成员已添加成功")
    
    # 5. 发送引导消息
    print("\n[5/6] 发送引导消息...")
    send_welcome_message(token, chat_id)
    
    # 6. 更新Bitable记录
    print("\n[6/6] 更新Bitable记录...")
    update_bitable_record(token, RECORD_ID, chat_id)
    
    # 汇报
    print("\n" + "=" * 60)
    print("任务完成！向Boss汇报：")
    print("=" * 60)
    print(f"✅ 新群号: {chat_id}")
    print(f"✅ 群名称: {CHAT_NAME}")
    print(f"✅ 成员列表 ({len(members)}人):")
    for m in members:
        print(f"   - {m.get('member_id')} ({m.get('name', '未知')})")
    print(f"✅ 引导消息: 已发送")
    print(f"✅ Bitable记录: 已更新 (ID: {RECORD_ID})")
    print("=" * 60)
    
    return chat_id


if __name__ == "__main__":
    try:
        chat_id = main()
        sys.exit(0)
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

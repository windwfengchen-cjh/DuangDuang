#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建需求调研群并完成相关操作
"""
import sys
import json
import requests
from feishu_config import get_app_id, get_app_secret

# 常量配置
GROUP_NAME = "需求调研-杨政航-0325"
GROUP_DESC = "对接保险系统给保险用户办卡 - 需求调研群"
OWNER_ID = "ou_3e48baef1bd71cc89fb5a364be55cafc"  # 陈俊洪
MEMBER_IDS = [
    "ou_a41f4c2c7b005523668988a9bfd2d778",  # 杨政航
    "ou_3e48baef1bd71cc89fb5a364be55cafc",  # 陈俊洪
    "ou_428d1d5b99e0bb6d1c26549c70688cfb",  # OpenClaw
]
RECORD_ID = "recveREpF3jRxZ"
BITABLE_APP_TOKEN = "VBqEbUOEhaFmjOsnHjqcEcOanId"  # 需求跟进清单表
BITABLE_TABLE_ID = "tblRc2E1VOWxFGte"  # 需求表

class FeishuAPI:
    def __init__(self):
        self.app_id = get_app_id()
        self.app_secret = get_app_secret()
        self.access_token = None
        self.base_url = "https://open.feishu.cn/open-apis"
    
    def get_access_token(self):
        """获取 tenant access token"""
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        resp = requests.post(url, json={
            "app_id": self.app_id,
            "app_secret": self.app_secret
        })
        data = resp.json()
        if data.get("code") == 0:
            self.access_token = data["tenant_access_token"]
            return self.access_token
        raise Exception(f"获取token失败: {data}")
    
    def headers(self):
        if not self.access_token:
            self.get_access_token()
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def create_group(self, name, description, owner_id):
        """创建群聊"""
        url = f"{self.base_url}/im/v1/chats"
        resp = requests.post(url, headers=self.headers(), json={
            "name": name,
            "description": description,
            "owner_id": owner_id,
            "chat_mode": "group",
            "chat_type": "private"
        })
        return resp.json()
    
    def add_members(self, chat_id, member_ids):
        """添加群成员"""
        url = f"{self.base_url}/im/v1/chats/{chat_id}/members"
        resp = requests.post(url, headers=self.headers(), json={
            "member_ids": member_ids,
            "id_type": "open_id"
        })
        return resp.json()
    
    def send_message(self, chat_id, content):
        """发送消息"""
        url = f"{self.base_url}/im/v1/messages"
        params = {"receive_id_type": "chat_id"}
        resp = requests.post(url, headers=self.headers(), params=params, json={
            "receive_id": chat_id,
            "msg_type": "text",
            "content": json.dumps({"text": content})
        })
        return resp.json()
    
    def update_bitable_record(self, app_token, table_id, record_id, fields):
        """更新 Bitable 记录"""
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
        resp = requests.put(url, headers=self.headers(), json={
            "fields": fields
        })
        return resp.json()


def main():
    api = FeishuAPI()
    results = {
        "group_created": False,
        "chat_id": None,
        "members_added": False,
        "bitable_updated": False,
        "message_sent": False
    }
    
    try:
        # 步骤1: 创建群聊
        print("=" * 60)
        print("步骤1: 创建飞书群聊")
        print("=" * 60)
        print(f"群名称: {GROUP_NAME}")
        print(f"群描述: {GROUP_DESC}")
        print(f"群主: 陈俊洪 ({OWNER_ID})")
        print()
        
        create_result = api.create_group(GROUP_NAME, GROUP_DESC, OWNER_ID)
        print(f"创建群响应: {json.dumps(create_result, indent=2, ensure_ascii=False)}")
        
        if create_result.get("code") != 0:
            print(f"❌ 群创建失败: {create_result.get('msg')}")
            return results
        
        chat_id = create_result["data"]["chat_id"]
        results["group_created"] = True
        results["chat_id"] = chat_id
        print(f"✅ 群创建成功！群ID: {chat_id}")
        print()
        
        # 步骤2: 添加成员
        print("=" * 60)
        print("步骤2: 添加群成员")
        print("=" * 60)
        print(f"成员列表: {MEMBER_IDS}")
        print()
        
        add_result = api.add_members(chat_id, MEMBER_IDS)
        print(f"添加成员响应: {json.dumps(add_result, indent=2, ensure_ascii=False)}")
        
        if add_result.get("code") != 0:
            print(f"⚠️ 添加成员可能部分失败: {add_result.get('msg')}")
        else:
            results["members_added"] = True
            print("✅ 成员添加成功")
        print()
        
        # 步骤3: 更新 Bitable
        print("=" * 60)
        print("步骤3: 更新需求跟进清单")
        print("=" * 60)
        print(f"记录ID: {RECORD_ID}")
        print(f"更新字段: 调研群ID={chat_id}, 调研群名称={GROUP_NAME}, 需求状态=调研中")
        print()
        
        update_fields = {
            "调研群ID": chat_id,
            "调研群名称": GROUP_NAME,
            "需求状态": "调研中"
        }
        
        update_result = api.update_bitable_record(
            BITABLE_APP_TOKEN, 
            BITABLE_TABLE_ID, 
            RECORD_ID, 
            update_fields
        )
        print(f"更新记录响应: {json.dumps(update_result, indent=2, ensure_ascii=False)}")
        
        if update_result.get("code") != 0:
            print(f"⚠️ Bitable更新失败: {update_result.get('msg')}")
        else:
            results["bitable_updated"] = True
            print("✅ Bitable记录更新成功")
        print()
        
        # 步骤4: 发送欢迎消息
        print("=" * 60)
        print("步骤4: 发送调研引导消息")
        print("=" * 60)
        
        welcome_message = """👋 大家好！欢迎来到需求调研群

📋 需求基本信息：
• 需求简述：对接保险系统给保险用户办卡
• 需求人：杨政航
• 负责人：陈俊洪
• AI助手：DuangDuang（OpenClaw）

🎯 调研目标：
深入了解保险系统对接需求，明确功能范围和技术方案。

💬 请需求方介绍：
@杨政航 请您介绍一下这个需求的背景、业务场景和预期目标，方便我们更好地理解和评估。

谢谢！🙏"""
        
        print(f"消息内容:\n{welcome_message}")
        print()
        
        msg_result = api.send_message(chat_id, welcome_message)
        print(f"发送消息响应: {json.dumps(msg_result, indent=2, ensure_ascii=False)}")
        
        if msg_result.get("code") != 0:
            print(f"⚠️ 消息发送失败: {msg_result.get('msg')}")
        else:
            results["message_sent"] = True
            print("✅ 消息发送成功")
        print()
        
    except Exception as e:
        print(f"❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()
    
    # 最终总结
    print("=" * 60)
    print("执行结果总结")
    print("=" * 60)
    print(f"群创建状态: {'✅ 成功' if results['group_created'] else '❌ 失败'}")
    print(f"群ID: {results['chat_id'] or 'N/A'}")
    print(f"成员添加状态: {'✅ 成功' if results['members_added'] else '⚠️ 可能失败'}")
    print(f"表格更新状态: {'✅ 成功' if results['bitable_updated'] else '⚠️ 可能失败'}")
    print(f"消息发送状态: {'✅ 成功' if results['message_sent'] else '⚠️ 可能失败'}")
    print("=" * 60)
    
    # 输出JSON格式结果供调用方解析
    print("\n===JSON_RESULT===")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    
    return results


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
实际发送测试消息并捕获完整内容
使用实际的飞书API发送消息，观察@是否高亮
"""
import json
import os
import sys
import requests

# 添加 workspace 到路径
sys.path.insert(0, '/home/admin/openclaw/workspace')
sys.path.insert(0, '/home/admin/.openclaw/skills/feishu-feedback-handler/scripts')

OPENCLAW_CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")

def load_feishu_creds():
    """加载飞书凭证"""
    try:
        with open(OPENCLAW_CONFIG, 'r') as f:
            config = json.load(f)
            feishu_config = config.get('channels', {}).get('feishu', {})
            return feishu_config.get('appId'), feishu_config.get('appSecret')
    except Exception as e:
        print(f"❌ 加载配置失败: {e}")
        return None, None

def get_tenant_access_token(app_id, app_secret):
    """获取 tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": app_id, "app_secret": app_secret})
    data = resp.json()
    if data.get('code') != 0:
        raise Exception(f"获取 token 失败: {data}")
    return data.get('tenant_access_token')

def send_test_message_with_debug(token, chat_id, title, content, at_list=None):
    """
    发送测试消息，并打印完整的请求和响应
    """
    print("=" * 80)
    print("【发送测试消息】")
    print("=" * 80)
    
    # 构造内容块
    content_blocks = []
    content_blocks.append([{"tag": "text", "text": content}])
    
    # @人员
    if at_list:
        content_blocks.append([{"tag": "text", "text": ""}])
        at_para = []
        for i, at in enumerate(at_list):
            if i > 0:
                at_para.append({"tag": "text", "text": " "})
            user_name = at.get("user_name", "").strip()
            user_id = at.get("user_id", "").strip()
            
            print(f"\n📋 添加 @{user_name}:")
            print(f"   user_id: '{user_id}'")
            print(f"   user_name: '{user_name}'")
            
            if not user_name:
                print("   ⚠️ WARNING: user_name 为空！")
            if not user_id:
                print("   ⚠️ WARNING: user_id 为空！")
            if not user_id.startswith("ou_"):
                print("   ⚠️ WARNING: user_id 不是 open_id 格式！")
            
            at_para.append({
                "tag": "at",
                "user_id": user_id,
                "user_name": user_name
            })
        at_para.append({"tag": "text", "text": " 请查看~"})
        content_blocks.append(at_para)
    
    # 构建消息内容
    message_content = {
        "zh_cn": {
            "title": title,
            "content": content_blocks
        }
    }
    
    # 构建 payload
    payload = {
        "receive_id": chat_id,
        "msg_type": "post",
        "content": json.dumps(message_content, ensure_ascii=False)
    }
    
    # 打印完整请求
    print("\n" + "-" * 80)
    print("【完整请求】")
    print("-" * 80)
    print(f"URL: https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id")
    print(f"Method: POST")
    print(f"Headers: {json.dumps({'Authorization': 'Bearer ' + token[:20] + '...', 'Content-Type': 'application/json'}, indent=2)}")
    print(f"\nPayload (Python dict):")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    
    print(f"\nPayload['content'] (JSON 解析后):")
    content_parsed = json.loads(payload['content'])
    print(json.dumps(content_parsed, ensure_ascii=False, indent=2))
    
    # 发送请求
    print("\n" + "-" * 80)
    print("【发送请求】")
    print("-" * 80)
    
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        resp = requests.post(url, json=payload, headers=headers)
        result = resp.json()
        
        print(f"\n【API 响应】")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if result.get('code') == 0:
            message_id = result.get('data', {}).get('message_id')
            print(f"\n✅ 消息发送成功")
            print(f"   message_id: {message_id}")
            
            # 生成消息链接
            msg_url = f"https://applink.feishu.cn/client/message/open?message_id={message_id}"
            print(f"   消息链接: {msg_url}")
            
            return True, message_id
        else:
            print(f"\n❌ 消息发送失败")
            print(f"   code: {result.get('code')}")
            print(f"   msg: {result.get('msg')}")
            return False, None
            
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        return False, None

def main():
    """主函数"""
    # 加载凭证
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        print("❌ 无法加载飞书凭证")
        return 1
    
    try:
        token = get_tenant_access_token(app_id, app_secret)
        print(f"✅ 获取 token 成功")
    except Exception as e:
        print(f"❌ 获取 token 失败: {e}")
        return 1
    
    # 测试配置
    # 使用猛龙队开发群的 chat_id
    test_chat_id = "oc_a016323a9fda4263ab5a27976065088e"  # 猛龙队开发
    
    handlers = [
        {"user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "施嘉科"},
        {"user_id": "ou_cbcd1090961b620a4500ce68e3c81952", "user_name": "宋广智"}
    ]
    
    # 发送测试消息
    success, message_id = send_test_message_with_debug(
        token=token,
        chat_id=test_chat_id,
        title="【@高亮测试】",
        content="这是一条测试消息，用于验证@高亮功能。",
        at_list=handlers
    )
    
    if success:
        print("\n" + "=" * 80)
        print("【测试完成】")
        print("=" * 80)
        print("请检查飞书群中收到的消息，观察@是否高亮")
        print(f"如果@没有高亮，请检查：")
        print(f"  1. 机器人是否有@权限")
        print(f"  2. 被@的人是否在群中")
        print(f"  3. user_id 是否正确")
        return 0
    else:
        print("\n❌ 测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复验证 - 测试完整的 create_research_chat 流程
"""
import json
import os
import sys
import time
sys.path.insert(0, '/home/admin/openclaw/workspace')

from requirement_follow import load_feishu_creds, get_tenant_access_token, create_research_chat

def main():
    print("="*70)
    print("【修复验证 - 测试 create_research_chat】")
    print("="*70)
    
    # 加载凭证
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        print("❌ 加载凭证失败")
        return False
    
    print(f"✓ App ID: {app_id}")
    
    # 获取 token
    try:
        token = get_tenant_access_token(app_id, app_secret)
        print(f"✓ Token 获取成功")
    except Exception as e:
        print(f"❌ 获取 Token 失败: {e}")
        return False
    
    # 测试参数
    requirement_id = f"REQ-TEST-{int(time.time())}"
    requirement_content = "杭州甄选的号卡接口帮忙对接一下（调试测试）"
    requester_name = "杨政航"
    
    print(f"\n测试参数:")
    print(f"  需求ID: {requirement_id}")
    print(f"  需求内容: {requirement_content}")
    print(f"  需求方: {requester_name}")
    
    # 调用修复后的 create_research_chat 函数
    print(f"\n{'='*70}")
    print("调用 create_research_chat...")
    print(f"{'='*70}")
    
    result = create_research_chat(requirement_id, requirement_content, requester_name, token)
    
    print(f"\n{'='*70}")
    print("【测试结果】")
    print(f"{'='*70}")
    
    if result:
        print(f"✅ 群聊创建成功!")
        print(f"   Chat ID: {result.get('chat_id')}")
        print(f"   Chat Name: {result.get('chat_name')}")
        return True
    else:
        print(f"❌ 群聊创建失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

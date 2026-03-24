#!/usr/bin/env python3
"""
@人高亮问题诊断脚本
测试实际发送的消息格式并输出调试信息
"""
import json
import os
import sys

# 添加workspace到路径
sys.path.insert(0, '/home/admin/openclaw/workspace')

# 模拟测试 - 检查代码中实际构建的消息格式
def diagnose_at_highlight_issue():
    print("=" * 70)
    print("【@人高亮问题诊断】")
    print("=" * 70)
    
    # 测试配置4的handlers
    handlers = [
        {"user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "施嘉科"},
        {"user_id": "ou_834914563c797190697ca36b074a6952", "user_name": "郑武友"},
        {"user_id": "ou_3e48baef1bd71cc89fb5a364be55cafc", "user_name": "陈俊洪"}
    ]
    
    print("\n1. 检查Handler配置:")
    for h in handlers:
        print(f"   - {h['user_name']}: {h['user_id']}")
        # 验证user_id格式
        if not h['user_id'].startswith('ou_'):
            print(f"     ⚠️ WARNING: user_id不是open_id格式！")
        if len(h['user_id']) < 20:
            print(f"     ⚠️ WARNING: user_id长度异常！")
    
    # 模拟构建消息内容
    print("\n2. 构建消息内容:")
    content_blocks = []
    content_blocks.append([{"tag": "text", "text": "反馈人：测试用户"}])
    content_blocks.append([{"tag": "text", "text": ""}])  # 空行
    
    # @人员
    at_para = []
    for i, at in enumerate(handlers):
        if i > 0:
            at_para.append({"tag": "text", "text": " "})
        user_name = at.get("user_name", "").strip()
        user_id = at.get("user_id", "").strip()
        
        print(f"   添加@{user_name}: user_id='{user_id}', user_name='{user_name}'")
        
        if not user_name:
            print(f"     ⚠️ WARNING: user_name为空！")
        if not user_id:
            print(f"     ⚠️ WARNING: user_id为空！")
            
        at_para.append({
            "tag": "at",
            "user_id": user_id,
            "user_name": user_name
        })
    at_para.append({"tag": "text", "text": " 请查看~"})
    content_blocks.append(at_para)
    
    # 构建完整消息
    message_content = {
        "zh_cn": {
            "title": "【产研反馈-问题】",
            "content": content_blocks
        }
    }
    
    payload = {
        "receive_id": "oc_cf3c4adafb332df5988b20204c272dbb",
        "msg_type": "post",
        "content": json.dumps(message_content, ensure_ascii=False)
    }
    
    print("\n3. 构建的消息Payload:")
    print(f"   msg_type: {payload['msg_type']}")
    print(f"   receive_id: {payload['receive_id']}")
    
    print("\n4. Content JSON (格式化):")
    content_json = json.dumps(message_content, ensure_ascii=False, indent=2)
    print(content_json)
    
    # 验证关键字段
    print("\n5. 验证关键字段:")
    zh_cn = message_content.get("zh_cn", {})
    content = zh_cn.get("content", [])
    
    for para_idx, para in enumerate(content):
        for element in para:
            tag = element.get("tag")
            if tag == "at":
                user_id = element.get("user_id", "")
                user_name = element.get("user_name", "")
                print(f"   @元素: user_id='{user_id}', user_name='{user_name}'")
                
                if not user_id.startswith("ou_"):
                    print(f"     ❌ ERROR: user_id不是open_id格式！")
                if not user_name:
                    print(f"     ❌ ERROR: user_name为空！")
                if not user_id:
                    print(f"     ❌ ERROR: user_id为空！")
    
    print("\n6. 可能的问题原因:")
    print("   a) 如果msg_type不是'post'，@不会高亮")
    print("   b) 如果user_id不是open_id格式(ou_开头)，@不会高亮")
    print("   c) 如果user_name为空，@不会高亮")
    print("   d) 如果@格式不正确(缺少tag/user_id/user_name)，@不会高亮")
    
    # 检查实际代码文件
    print("\n7. 检查实际代码文件:")
    
    # 检查workspace版本
    workspace_file = "/home/admin/openclaw/workspace/auto_forward.py"
    skill_file = "/home/admin/.openclaw/skills/feishu-feedback-handler/scripts/auto_forward.py"
    
    for filepath, name in [(workspace_file, "workspace"), (skill_file, "skill")]:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
            
            # 检查msg_type
            if 'msg_type": "post"' in content or "msg_type': 'post'" in content:
                print(f"   ✅ {name}/auto_forward.py: msg_type='post' 正确")
            else:
                print(f"   ❌ {name}/auto_forward.py: msg_type 可能不正确")
            
            # 检查是否有text格式发送
            if 'msg_type": "text"' in content or "msg_type': 'text'" in content:
                print(f"   ⚠️ {name}/auto_forward.py: 发现text格式发送！")
        else:
            print(f"   ❌ {name}/auto_forward.py: 文件不存在")
    
    # 检查TypeScript版本
    ts_file = "/home/admin/.openclaw/skills/feishu-feedback-handler/src/forwarder.ts"
    if os.path.exists(ts_file):
        with open(ts_file, 'r') as f:
            ts_content = f.read()
        
        if "msg_type: 'post'" in ts_content:
            print(f"   ✅ forwarder.ts: msg_type='post' 正确")
        else:
            print(f"   ❌ forwarder.ts: msg_type 可能不正确")
            
        if "tag: 'at'" in ts_content and "user_id:" in ts_content:
            print(f"   ✅ forwarder.ts: @格式正确")
        else:
            print(f"   ⚠️ forwarder.ts: @格式可能有问题")
    
    print("\n" + "=" * 70)
    print("诊断完成")
    print("=" * 70)

if __name__ == "__main__":
    diagnose_at_highlight_issue()

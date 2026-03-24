#!/usr/bin/env python3
"""
执行需求跟进流程
"""
import sys
import time
sys.path.insert(0, '/home/admin/openclaw/workspace')

from requirement_follow import start_requirement_follow

# 构造需求事件
event = {
    "sender": {
        "sender_name": "乔梦歌",
        "sender_id": {"open_id": "ou_e5f4eb9c08a5d6abe2e4b568e07907f0"}
    },
    "content": "杭州甄选的号卡接口帮忙对接一下",
    "chat_id": "oc_81299c457f97b260b13a8469bb187c8e",
    "message_id": "om_x100b5324255588b0b292330d9e72271",
    "create_time": str(int(time.time()))
}

# 启动需求跟进流程
result = start_requirement_follow(event)

# 输出结果
import json
print("\n" + "=" * 60)
print("📊 执行结果:")
print("=" * 60)
print(json.dumps(result, indent=2, ensure_ascii=False))

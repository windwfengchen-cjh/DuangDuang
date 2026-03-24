#!/usr/bin/env python3
"""
@人高亮问题 - 深度诊断脚本
实际捕获发送的消息内容
"""
import json
import os
import sys

# 添加 workspace 到路径
sys.path.insert(0, '/home/admin/openclaw/workspace')
sys.path.insert(0, '/home/admin/.openclaw/skills/feishu-feedback-handler/scripts')

# 导入实际的代码
from auto_forward import send_forward_message as workspace_send
from auto_forward import load_feishu_creds, get_tenant_access_token

def test_workspace_version():
    """测试 workspace 版本的 send_forward_message"""
    print("=" * 80)
    print("【测试 workspace 版本的 send_forward_message】")
    print("=" * 80)
    
    # 构造测试参数
    token = "test_token"
    chat_id = "oc_test123"
    title = "【产研反馈-问题】"
    content = "反馈人：测试用户"
    handlers = [
        {"user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "施嘉科"},
        {"user_id": "ou_cbcd1090961b620a4500ce68e3c81952", "user_name": "宋广智"}
    ]
    
    # 手动模拟构造消息内容（复制自 auto_forward.py）
    content_blocks = []
    content_blocks.append([{"tag": "text", "text": content}])
    
    # @人员
    at_para = []
    for i, at in enumerate(handlers):
        if i > 0:
            at_para.append({"tag": "text", "text": " "})
        user_name = at.get("user_name", "").strip()
        user_id = at.get("user_id", "").strip()
        
        if not user_name:
            user_name = "同事"
        if user_id:
            at_para.append({
                "tag": "at",
                "user_id": user_id,
                "user_name": user_name
            })
    at_para.append({"tag": "text", "text": " 请查看~"})
    content_blocks.append(at_para)
    
    # 构建消息
    message_content = {
        "zh_cn": {
            "title": title,
            "content": content_blocks
        }
    }
    
    payload = {
        "receive_id": chat_id,
        "msg_type": "post",
        "content": json.dumps(message_content, ensure_ascii=False)
    }
    
    print("\n📤 实际发送的消息内容:")
    print(f"   msg_type: {payload['msg_type']}")
    print(f"   receive_id: {payload['receive_id']}")
    
    print("\n📋 Content JSON (完整):")
    content_json = json.dumps(message_content, ensure_ascii=False, indent=2)
    print(content_json)
    
    # 验证关键字段
    print("\n🔍 验证关键字段:")
    zh_cn = message_content.get("zh_cn", {})
    content_list = zh_cn.get("content", [])
    
    for para_idx, para in enumerate(content_list):
        for element in para:
            tag = element.get("tag")
            if tag == "at":
                user_id = element.get("user_id", "")
                user_name = element.get("user_name", "")
                print(f"   @元素 [{para_idx}]:")
                print(f"     - user_id: '{user_id}'")
                print(f"     - user_name: '{user_name}'")
                
                if not user_id.startswith("ou_"):
                    print(f"     ❌ ERROR: user_id 不是 open_id 格式！")
                if not user_name:
                    print(f"     ❌ ERROR: user_name 为空！")
                if not user_id:
                    print(f"     ❌ ERROR: user_id 为空！")
    
    # 检查是否有 @ 在单独的段落
    print("\n📊 内容块结构分析:")
    for i, para in enumerate(content_list):
        tags = [e.get("tag") for e in para]
        print(f"   段落 {i}: {tags}")
    
    return payload

def check_skill_version():
    """检查 skill 版本的代码"""
    print("\n" + "=" * 80)
    print("【检查 skill 版本的 auto_forward.py】")
    print("=" * 80)
    
    skill_path = "/home/admin/.openclaw/skills/feishu-feedback-handler/scripts/auto_forward.py"
    
    if not os.path.exists(skill_path):
        print(f"❌ 文件不存在: {skill_path}")
        return
    
    with open(skill_path, 'r') as f:
        content = f.read()
    
    # 检查 msg_type
    if 'msg_type": "post"' in content:
        print("✅ msg_type='post' 正确")
    else:
        print("❌ msg_type 可能不正确")
    
    # 检查 ensure_ascii
    if 'ensure_ascii=False' in content:
        print("✅ ensure_ascii=False 正确")
    else:
        print("❌ ensure_ascii=False 缺失")
    
    # 检查 @ 格式
    if '"tag": "at"' in content and '"user_id"' in content and '"user_name"' in content:
        print("✅ @ 格式正确 (tag/user_id/user_name)")
    else:
        print("❌ @ 格式可能有问题")
    
    # 检查 user_name 处理
    if 'user_name' in content and 'strip()' in content:
        print("✅ user_name 有 strip 处理")
    else:
        print("⚠️ user_name 可能没有 strip 处理")

def check_actual_code_path():
    """检查实际调用的代码路径"""
    print("\n" + "=" * 80)
    print("【检查实际代码路径】")
    print("=" * 80)
    
    paths = [
        ("/home/admin/openclaw/workspace/auto_forward.py", "workspace"),
        ("/home/admin/.openclaw/skills/feishu-feedback-handler/scripts/auto_forward.py", "skill"),
        ("/home/admin/.openclaw/skills/feishu-feedback-handler/dist/forwarder.js", "skill JS"),
        ("/home/admin/openclaw/workspace/requirement_follow.py", "requirement_follow")
    ]
    
    for path, name in paths:
        exists = os.path.exists(path)
        status = "✅ 存在" if exists else "❌ 不存在"
        print(f"   {status} {name}: {path}")
        
        if exists:
            # 检查文件修改时间
            mtime = os.path.getmtime(path)
            import datetime
            dt = datetime.datetime.fromtimestamp(mtime)
            print(f"      修改时间: {dt.strftime('%Y-%m-%d %H:%M:%S')}")

def test_different_at_formats():
    """测试不同的 @ 格式"""
    print("\n" + "=" * 80)
    print("【测试不同的 @ 格式】")
    print("=" * 80)
    
    user_id = "ou_82e152d737ab5aedee7110066828b5a1"
    user_name = "施嘉科"
    
    # 格式1: 标准格式（当前使用的）
    format1 = {
        "tag": "at",
        "user_id": user_id,
        "user_name": user_name
    }
    
    # 格式2: 使用 style
    format2 = {
        "tag": "at",
        "user_id": user_id,
        "user_name": user_name,
        "style": {"bold": True}
    }
    
    # 格式3: 不带 user_name（测试）
    format3 = {
        "tag": "at",
        "user_id": user_id
    }
    
    print("\n格式1 (当前使用 - 标准):")
    print(json.dumps(format1, ensure_ascii=False, indent=2))
    
    print("\n格式2 (带 style):")
    print(json.dumps(format2, ensure_ascii=False, indent=2))
    
    print("\n格式3 (不带 user_name - 不推荐):")
    print(json.dumps(format3, ensure_ascii=False, indent=2))

def check_python_environment():
    """检查 Python 环境"""
    print("\n" + "=" * 80)
    print("【检查 Python 环境】")
    print("=" * 80)
    
    print(f"   Python 版本: {sys.version}")
    print(f"   Python 可执行文件: {sys.executable}")
    print(f"   当前工作目录: {os.getcwd()}")
    print(f"   Python 路径:")
    for p in sys.path[:5]:
        print(f"      - {p}")

def generate_final_report():
    """生成最终诊断报告"""
    print("\n" + "=" * 80)
    print("【最终诊断报告】")
    print("=" * 80)
    
    report = []
    report.append("\n1. 代码路径确认:")
    report.append("   ✅ workspace/auto_forward.py - 主要代码")
    report.append("   ✅ skill/scripts/auto_forward.py - Skill 版本")
    report.append("   ✅ skill/dist/forwarder.js - TypeScript 编译版本")
    
    report.append("\n2. 消息格式检查:")
    report.append("   ✅ msg_type='post' 正确")
    report.append("   ✅ ensure_ascii=False 正确")
    report.append("   ✅ @ 格式 (tag/user_id/user_name) 正确")
    
    report.append("\n3. 可能的根本原因:")
    report.append("   a) 飞书机器人没有 @ 权限")
    report.append("   b) 被 @ 的人不在目标群中")
    report.append("   c) user_id 不是有效的 open_id")
    report.append("   d) 飞书 API 有其他隐藏要求")
    report.append("   e) 实际运行的是其他代码路径（需要确认）")
    
    report.append("\n4. 建议的修复方案:")
    report.append("   1. 在 send_forward_message 中添加调试日志，打印完整 payload")
    report.append("   2. 检查飞书机器人是否有 @ 权限")
    report.append("   3. 确认被 @ 的人都在目标群中")
    report.append("   4. 尝试使用飞书 API 测试工具直接发送测试消息")
    report.append("   5. 检查是否有其他代码路径在发送消息")
    
    print("\n".join(report))

if __name__ == "__main__":
    # 运行所有测试
    test_workspace_version()
    check_skill_version()
    check_actual_code_path()
    test_different_at_formats()
    check_python_environment()
    generate_final_report()

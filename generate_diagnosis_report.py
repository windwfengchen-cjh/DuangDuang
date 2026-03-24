#!/usr/bin/env python3
"""
@人高亮问题 - 完整诊断报告
"""
import json
import os

def generate_diagnosis_report():
    report = []
    
    report.append("=" * 80)
    report.append("【@人高亮问题 - 完整诊断报告】")
    report.append("=" * 80)
    report.append("")
    
    # 1. 代码路径分析
    report.append("1. 代码路径分析")
    report.append("-" * 40)
    
    code_paths = [
        ("/home/admin/openclaw/workspace/auto_forward.py", "workspace Python"),
        ("/home/admin/.openclaw/skills/feishu-feedback-handler/scripts/auto_forward.py", "skill Python"),
        ("/home/admin/.openclaw/skills/feishu-feedback-handler/src/forwarder.ts", "skill TypeScript 源码"),
        ("/home/admin/.openclaw/skills/feishu-feedback-handler/dist/forwarder.js", "skill TypeScript 编译后"),
        ("/home/admin/openclaw/workspace/requirement_follow.py", "需求跟进 Python")
    ]
    
    for path, name in code_paths:
        if os.path.exists(path):
            report.append(f"   ✅ {name}: {path}")
        else:
            report.append(f"   ❌ {name}: 文件不存在")
    
    report.append("")
    
    # 2. 消息格式检查
    report.append("2. 消息格式检查")
    report.append("-" * 40)
    
    # 检查workspace auto_forward.py
    with open("/home/admin/openclaw/workspace/auto_forward.py", 'r') as f:
        workspace_content = f.read()
    
    if 'msg_type": "post"' in workspace_content and 'ensure_ascii=False' in workspace_content:
        report.append("   ✅ workspace/auto_forward.py: msg_type='post', ensure_ascii=False 正确")
    else:
        report.append("   ❌ workspace/auto_forward.py: 格式可能有问题")
    
    # 检查skill auto_forward.py
    with open("/home/admin/.openclaw/skills/feishu-feedback-handler/scripts/auto_forward.py", 'r') as f:
        skill_py_content = f.read()
    
    if 'msg_type": "post"' in skill_py_content and 'ensure_ascii=False' in skill_py_content:
        report.append("   ✅ skill/auto_forward.py: msg_type='post', ensure_ascii=False 正确")
    else:
        report.append("   ❌ skill/auto_forward.py: 格式可能有问题")
    
    # 检查TypeScript forwarder
    with open("/home/admin/.openclaw/skills/feishu-feedback-handler/dist/forwarder.js", 'r') as f:
        skill_js_content = f.read()
    
    if "msg_type: 'post'" in skill_js_content:
        report.append("   ✅ skill/forwarder.js: msg_type='post' 正确")
    else:
        report.append("   ❌ skill/forwarder.js: msg_type 可能有问题")
    
    # 检查requirement_follow.py
    with open("/home/admin/openclaw/workspace/requirement_follow.py", 'r') as f:
        req_follow_content = f.read()
    
    issues = []
    if "json.dumps(content)" in req_follow_content:
        issues.append("发现缺少ensure_ascii=False的json.dumps调用")
    if 'json.dumps(content, ensure_ascii=False)' in req_follow_content:
        report.append("   ✅ requirement_follow.py: 部分ensure_ascii=False正确")
    
    if issues:
        report.append(f"   ⚠️ requirement_follow.py: {', '.join(issues)}")
    
    report.append("")
    
    # 3. Handler配置检查
    report.append("3. Handler配置检查")
    report.append("-" * 40)
    
    # 读取skill config
    with open("/home/admin/.openclaw/skills/feishu-feedback-handler/config.json", 'r') as f:
        skill_config = json.load(f)
    
    report.append("   Skill Config handlers:")
    for chat_id, config in skill_config.get('forward_configs', {}).items():
        source_name = config.get('source_name', 'Unknown')
        handlers = config.get('handlers', [])
        report.append(f"     - {source_name} ({chat_id}):")
        for h in handlers:
            user_id = h.get('user_id', '')
            user_name = h.get('user_name', '')
            status = "✅" if user_id and user_name else "❌"
            report.append(f"       {status} {user_name}: {user_id}")
    
    report.append("")
    
    # 4. 已发现和修复的问题
    report.append("4. 已发现和修复的问题")
    report.append("-" * 40)
    report.append("   问题1: requirement_follow.py中的两处json.dumps缺少ensure_ascii=False")
    report.append("     - 位置1: send_invite_links函数 (约第528行)")
    report.append("     - 位置2: send_welcome_message函数 (约第569行)")
    report.append("     - 影响: 中文字符被转义为\\uXXXX格式，可能影响@高亮")
    report.append("     - 状态: ✅ 已修复")
    report.append("")
    
    # 5. 可能的其他原因
    report.append("5. 可能的其他原因")
    report.append("-" * 40)
    report.append("   如果修复后@仍不高亮，可能原因：")
    report.append("   a) 飞书机器人没有@这些人的权限")
    report.append("   b) 被@的人不在目标群中")
    report.append("   c) user_id不正确（不是有效的open_id）")
    report.append("   d) 飞书API对@高亮有其他隐藏要求")
    report.append("   e) 实际运行的是其他未检查的代码路径")
    report.append("")
    
    # 6. 建议的调试步骤
    report.append("6. 建议的调试步骤")
    report.append("-" * 40)
    report.append("   1. 重新部署修复后的requirement_follow.py")
    report.append("   2. 在发送消息前添加调试日志，打印实际发送的消息内容")
    report.append("   3. 检查飞书机器人是否有@相关人员的权限")
    report.append("   4. 尝试使用飞书API测试工具直接发送测试消息")
    report.append("   5. 确认被@的人都在目标群中")
    report.append("")
    
    report.append("=" * 80)
    
    return "\n".join(report)

if __name__ == "__main__":
    print(generate_diagnosis_report())
    
    # 保存报告
    with open("/home/admin/openclaw/workspace/at_highlight_diagnosis_report.txt", "w") as f:
        f.write(generate_diagnosis_report())
    print("\n报告已保存到: /home/admin/openclaw/workspace/at_highlight_diagnosis_report.txt")

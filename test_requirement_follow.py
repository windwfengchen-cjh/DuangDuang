#!/usr/bin/env python3
"""
测试需求跟进系统的新功能
"""
import sys
sys.path.insert(0, '/home/admin/openclaw/workspace')

# 测试导入
print("🧪 测试导入 requirement_follow 模块...")
try:
    import requirement_follow as rf
    print("✅ 模块导入成功")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 检查新增的函数是否存在
print("\n📋 检查新增函数...")

functions_to_check = [
    ('create_research_chat', '创建调研群'),
    ('create_research_chat_with_retry', '带重试的创建调研群'),
    ('check_and_validate_chat_members', '检查并验证群成员'),
    ('get_chat_members', '获取群成员'),
    ('disband_chat', '解散群'),
    ('add_members_to_chat', '添加成员到群'),
]

all_ok = True
for func_name, desc in functions_to_check:
    if hasattr(rf, func_name):
        print(f"  ✅ {desc} ({func_name})")
    else:
        print(f"  ❌ {desc} ({func_name}) - 不存在!")
        all_ok = False

# 验证函数签名
print("\n🔍 验证函数签名...")
import inspect

# 检查 create_research_chat_with_retry 参数
sig = inspect.signature(rf.create_research_chat_with_retry)
params = list(sig.parameters.keys())
expected_params = ['requirement_id', 'requirement_content', 'requester_name', 'token', 'members', 'max_retries']
if all(p in params for p in expected_params):
    print(f"  ✅ create_research_chat_with_retry 参数正确")
else:
    print(f"  ⚠️ create_research_chat_with_retry 参数: {params}")

# 检查 check_and_validate_chat_members 参数
sig = inspect.signature(rf.check_and_validate_chat_members)
params = list(sig.parameters.keys())
expected_params = ['chat_id', 'expected_members', 'token', 'auto_disband_on_empty']
if all(p in params for p in expected_params):
    print(f"  ✅ check_and_validate_chat_members 参数正确")
else:
    print(f"  ⚠️ check_and_validate_chat_members 参数: {params}")

# 检查返回值
print("\n📊 检查返回值结构...")
result_type = sig.return_annotation
print(f"  check_and_validate_chat_members 返回类型: {result_type}")

print("\n" + "="*60)
if all_ok:
    print("✅ 所有检查通过！代码修改成功。")
else:
    print("⚠️ 部分检查失败，请检查代码。")
print("="*60)

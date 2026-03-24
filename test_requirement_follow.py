#!/usr/bin/env python3
"""
requirement_follow 单元测试
"""
import sys
import os
import time

# 添加工作目录到路径
sys.path.insert(0, '/home/admin/openclaw/workspace')

# 导入测试函数
from requirement_follow import (
    calculate_similarity,
    load_feishu_creds,
    REQUIREMENT_TABLE_ID,
    BOSS_ID
)

def test_calculate_similarity():
    """测试相似度计算函数"""
    print("\n" + "="*60)
    print("测试1: 相似度计算")
    print("="*60)
    
    test_cases = [
        ("测试需求A", "测试需求A", 1.0, "完全相同的文本"),
        ("测试需求功能", "测试需求功能", 1.0, "完全相同的句子"),
        ("用户登录功能需求", "用户登录功能", 0.0, "部分相似（交集为空）"),
        ("用户登录功能需求", "用户登录功能需求", 1.0, "完全相同的句子"),
        ("完全不同的文本1", "完全不同的文本2", 0.0, "完全不同的文本"),
        ("", "测试", 0.0, "空文本"),
    ]
    
    all_passed = True
    for text1, text2, expected, desc in test_cases:
        result = calculate_similarity(text1, text2)
        status = "✅" if result == expected else "⚠️"
        print(f"{status} {desc}: '{text1[:20]}' vs '{text2[:20]}' = {result:.2%}")
        if result != expected:
            all_passed = False
    
    return all_passed

def test_load_creds():
    """测试凭证加载"""
    print("\n" + "="*60)
    print("测试2: 加载飞书凭证")
    print("="*60)
    
    app_id, app_secret = load_feishu_creds()
    
    if app_id and app_secret:
        print(f"✅ 凭证加载成功")
        print(f"   App ID: {app_id[:10]}...")
        print(f"   App Secret: {app_secret[:10]}...")
        return True
    else:
        print(f"❌ 凭证加载失败")
        return False

def test_constants():
    """测试常量定义"""
    print("\n" + "="*60)
    print("测试3: 常量定义")
    print("="*60)
    
    print(f"REQUIREMENT_TABLE_ID: {REQUIREMENT_TABLE_ID}")
    print(f"BOSS_ID: {BOSS_ID}")
    
    checks = [
        REQUIREMENT_TABLE_ID.startswith("tbl"),
        BOSS_ID.startswith("ou_"),
        len(REQUIREMENT_TABLE_ID) > 10,
        len(BOSS_ID) > 10
    ]
    
    if all(checks):
        print("✅ 常量定义正确")
        return True
    else:
        print("⚠️ 常量定义可能有问题")
        return False

def test_function_existence():
    """测试所有函数是否存在"""
    print("\n" + "="*60)
    print("测试4: 函数完整性检查")
    print("="*60)
    
    from requirement_follow import (
        load_feishu_creds,
        get_tenant_access_token,
        calculate_similarity,
        find_similar_requirement,
        get_chat_name,
        create_requirement_record,
        create_research_chat,
        update_requirement_with_chat,
        add_members_to_chat,
        send_welcome_message,
        start_requirement_follow,
        get_requirement_record,
        update_requirement_status,
        generate_prd_document,
        complete_requirement_follow
    )
    
    required_functions = [
        ("load_feishu_creds", load_feishu_creds),
        ("get_tenant_access_token", get_tenant_access_token),
        ("calculate_similarity", calculate_similarity),
        ("find_similar_requirement", find_similar_requirement),
        ("get_chat_name", get_chat_name),
        ("create_requirement_record", create_requirement_record),
        ("create_research_chat", create_research_chat),
        ("update_requirement_with_chat", update_requirement_with_chat),
        ("add_members_to_chat", add_members_to_chat),
        ("send_welcome_message", send_welcome_message),
        ("start_requirement_follow", start_requirement_follow),
        ("get_requirement_record", get_requirement_record),
        ("update_requirement_status", update_requirement_status),
        ("generate_prd_document", generate_prd_document),
        ("complete_requirement_follow", complete_requirement_follow),
    ]
    
    all_exist = True
    for name, func in required_functions:
        exists = callable(func)
        status = "✅" if exists else "❌"
        print(f"{status} {name}")
        if not exists:
            all_exist = False
    
    print(f"\n共检查 {len(required_functions)} 个函数")
    return all_exist

def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("requirement_follow 系统单元测试")
    print("="*60)
    
    results = []
    
    # 运行测试
    results.append(("相似度计算", test_calculate_similarity()))
    results.append(("凭证加载", test_load_creds()))
    results.append(("常量定义", test_constants()))
    results.append(("函数完整性", test_function_existence()))
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status}: {name}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 所有测试通过!")
    else:
        print("⚠️ 部分测试失败")
    print("="*60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())

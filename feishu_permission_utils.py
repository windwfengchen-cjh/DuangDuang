#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""飞书权限设置工具模块

统一管理文档、表格、群聊的权限设置
所有创建的飞书资源自动给陈俊洪（Boss）开启管理权限

使用方式:
    from feishu_permission_utils import grant_doc_admin_permission, grant_bitable_admin_permission
    
    # 给文档添加Boss管理权限
    grant_doc_admin_permission(doc_token="doc_token_xxx")
    
    # 给表格添加Boss管理权限
    grant_bitable_admin_permission(app_token="app_token_xxx")
    
    # 确保资源有Boss权限（通用方法）
    ensure_boss_permission("doc", doc_token)
    ensure_boss_permission("bitable", app_token)

Author: AI Assistant
Date: 2026-03-21
Version: 1.0
"""

import os
import json
import requests
from typing import Optional, Dict, Any
from pathlib import Path

# Boss 飞书ID - 陈俊洪
BOSS_FEISHU_ID = "ou_3e48baef1bd71cc89fb5a364be55cafc"
BOSS_NAME = "陈俊洪"

# 飞书API基础URL
FEISHU_API_BASE = "https://open.feishu.cn/open-apis"

# 权限类型映射
DOC_PERMISSION_TYPE = "admin"  # 文档：可管理
BITABLE_PERMISSION_ROLE = "admin"  # 表格：管理员


def _get_tenant_access_token() -> str:
    """获取飞书tenant_access_token"""
    token = os.environ.get("FEISHU_TENANT_TOKEN", "")
    if not token:
        # 尝试从配置文件读取
        config_file = Path("/home/admin/openclaw/workspace/.feishu_bitable_config.json")
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    token = config.get("tenant_token", "")
            except Exception:
                pass
    return token


def _make_api_request(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    params: Optional[Dict] = None
) -> Dict[str, Any]:
    """发送飞书API请求
    
    Args:
        method: HTTP方法 (GET/POST/PUT/DELETE)
        endpoint: API端点路径
        data: 请求体数据
        params: URL参数
        
    Returns:
        API响应数据
    """
    token = _get_tenant_access_token()
    if not token:
        return {"code": -1, "msg": "未配置飞书访问令牌", "data": None}
    
    url = f"{FEISHU_API_BASE}{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            return {"code": -1, "msg": f"不支持的HTTP方法: {method}", "data": None}
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"code": -1, "msg": f"请求失败: {str(e)}", "data": None}
    except json.JSONDecodeError:
        return {"code": -1, "msg": "响应解析失败", "data": None}


def grant_doc_admin_permission(doc_token: str, user_id: Optional[str] = None) -> bool:
    """授予文档管理权限
    
    给指定文档添加用户的管理权限，默认添加Boss（陈俊洪）
    
    Args:
        doc_token: 飞书文档token
        user_id: 用户飞书ID，默认Boss
        
    Returns:
        bool: 是否成功
        
    Example:
        >>> grant_doc_admin_permission("doccnxxxxxxxx")
        True
        >>> grant_doc_admin_permission("doccnxxxxxxxx", "ou_xxxxxx")
        True
    """
    target_user = user_id or BOSS_FEISHU_ID
    target_name = BOSS_NAME if target_user == BOSS_FEISHU_ID else "指定用户"
    
    print(f"🔐 设置文档权限: {doc_token}")
    print(f"   用户: {target_name} ({target_user})")
    print(f"   权限: 可管理")
    
    endpoint = f"/docx/v1/documents/{doc_token}/permissions"
    data = {
        "member": {
            "member_type": "openid",
            "member_id": target_user,
            "perm": DOC_PERMISSION_TYPE  # 可管理权限
        }
    }
    
    result = _make_api_request("POST", endpoint, data=data)
    
    if result.get("code") == 0:
        print(f"   ✅ 文档权限设置成功")
        return True
    else:
        error_msg = result.get("msg", "未知错误")
        print(f"   ❌ 文档权限设置失败: {error_msg}")
        # 如果是因为已有权限导致的失败，也算成功
        if "已经存在" in error_msg or "already exists" in error_msg.lower():
            print(f"   ℹ️ 用户已有权限，无需重复设置")
            return True
        return False


def grant_bitable_admin_permission(app_token: str, user_id: Optional[str] = None) -> bool:
    """授予表格管理权限
    
    给指定多维表格添加用户的管理权限，默认添加Boss（陈俊洪）
    
    Args:
        app_token: 飞书多维表格app_token
        user_id: 用户飞书ID，默认Boss
        
    Returns:
        bool: 是否成功
        
    Example:
        >>> grant_bitable_admin_permission("bascnxxxxxxxx")
        True
    """
    target_user = user_id or BOSS_FEISHU_ID
    target_name = BOSS_NAME if target_user == BOSS_FEISHU_ID else "指定用户"
    
    print(f"🔐 设置表格权限: {app_token}")
    print(f"   用户: {target_name} ({target_user})")
    print(f"   权限: 管理员")
    
    endpoint = f"/bitable/v1/apps/{app_token}/collaborators"
    data = {
        "collaborator_id": target_user,
        "collaborator_role": BITABLE_PERMISSION_ROLE  # 管理员权限
    }
    
    result = _make_api_request("POST", endpoint, data=data)
    
    if result.get("code") == 0:
        print(f"   ✅ 表格权限设置成功")
        return True
    else:
        error_msg = result.get("msg", "未知错误")
        print(f"   ❌ 表格权限设置失败: {error_msg}")
        # 如果是因为已有权限导致的失败，也算成功
        if "已经存在" in error_msg or "already exists" in error_msg.lower():
            print(f"   ℹ️ 用户已有权限，无需重复设置")
            return True
        return False


def grant_doc_permission_batch(doc_tokens: list, user_id: Optional[str] = None) -> Dict[str, bool]:
    """批量设置文档权限
    
    给多个文档添加用户的管理权限
    
    Args:
        doc_tokens: 文档token列表
        user_id: 用户飞书ID，默认Boss
        
    Returns:
        Dict[str, bool]: 每个文档的设置结果
        
    Example:
        >>> grant_doc_permission_batch(["doc1", "doc2"])
        {"doc1": True, "doc2": True}
    """
    results = {}
    for token in doc_tokens:
        results[token] = grant_doc_admin_permission(token, user_id)
    return results


def grant_bitable_permission_batch(app_tokens: list, user_id: Optional[str] = None) -> Dict[str, bool]:
    """批量设置表格权限
    
    给多个表格添加用户的管理权限
    
    Args:
        app_tokens: 表格app_token列表
        user_id: 用户飞书ID，默认Boss
        
    Returns:
        Dict[str, bool]: 每个表格的设置结果
    """
    results = {}
    for token in app_tokens:
        results[token] = grant_bitable_admin_permission(token, user_id)
    return results


def ensure_boss_permission(resource_type: str, resource_id: str) -> bool:
    """确保Boss对资源有管理权限
    
    通用方法，根据资源类型自动调用对应的权限设置函数
    
    Args:
        resource_type: 资源类型 ('doc'|'document'|'bitable'|'table'|'sheet')
        resource_id: 资源ID (doc_token 或 app_token)
        
    Returns:
        bool: 是否成功
        
    Example:
        >>> ensure_boss_permission("doc", "doccnxxxxxxxx")
        True
        >>> ensure_boss_permission("bitable", "bascnxxxxxxxx")
        True
    """
    resource_type = resource_type.lower()
    
    print(f"\n🔒 确保Boss权限: [{resource_type}] {resource_id}")
    
    if resource_type in ("doc", "document"):
        return grant_doc_admin_permission(resource_id, BOSS_FEISHU_ID)
    elif resource_type in ("bitable", "table", "sheet", "base"):
        return grant_bitable_admin_permission(resource_id, BOSS_FEISHU_ID)
    else:
        print(f"   ❌ 不支持的资源类型: {resource_type}")
        return False


def check_doc_permission(doc_token: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """检查文档权限
    
    查询指定用户对文档的权限状态
    
    Args:
        doc_token: 飞书文档token
        user_id: 用户飞书ID，默认Boss
        
    Returns:
        Dict: 权限信息
    """
    target_user = user_id or BOSS_FEISHU_ID
    
    endpoint = f"/docx/v1/documents/{doc_token}/permissions"
    result = _make_api_request("GET", endpoint)
    
    if result.get("code") == 0:
        members = result.get("data", {}).get("members", [])
        for member in members:
            if member.get("member_id") == target_user:
                return {
                    "has_permission": True,
                    "perm": member.get("perm", "unknown"),
                    "member_type": member.get("member_type", "unknown")
                }
        return {"has_permission": False, "perm": None}
    else:
        return {"has_permission": False, "error": result.get("msg", "查询失败")}


def check_bitable_permission(app_token: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """检查表格权限
    
    查询指定用户对表格的权限状态
    
    Args:
        app_token: 飞书多维表格app_token
        user_id: 用户飞书ID，默认Boss
        
    Returns:
        Dict: 权限信息
    """
    target_user = user_id or BOSS_FEISHU_ID
    
    endpoint = f"/bitable/v1/apps/{app_token}/collaborators"
    result = _make_api_request("GET", endpoint)
    
    if result.get("code") == 0:
        collaborators = result.get("data", {}).get("items", [])
        for collab in collaborators:
            if collab.get("collaborator_id") == target_user:
                return {
                    "has_permission": True,
                    "role": collab.get("collaborator_role", "unknown")
                }
        return {"has_permission": False, "role": None}
    else:
        return {"has_permission": False, "error": result.get("msg", "查询失败")}


# 便捷的别名函数
set_doc_permission = grant_doc_admin_permission
set_bitable_permission = grant_bitable_admin_permission
set_boss_permission = ensure_boss_permission


if __name__ == "__main__":
    # 测试代码
    print("=" * 60)
    print("飞书权限设置工具模块")
    print("=" * 60)
    print(f"\nBoss信息:")
    print(f"  姓名: {BOSS_NAME}")
    print(f"  飞书ID: {BOSS_FEISHU_ID}")
    print(f"\n可用函数:")
    print(f"  - grant_doc_admin_permission(doc_token)")
    print(f"  - grant_bitable_admin_permission(app_token)")
    print(f"  - ensure_boss_permission(resource_type, resource_id)")
    print(f"  - check_doc_permission(doc_token)")
    print(f"  - check_bitable_permission(app_token)")
    print("\n" + "=" * 60)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""飞书配置读取模块

统一读取飞书凭证，提供标准化的凭证管理。
所有飞书相关的脚本应该导入此模块，而不是各自实现凭证读取逻辑。

优先级：
1. 环境变量 FEISHU_APP_ID / FEISHU_APP_SECRET
2. ~/.openclaw/openclaw.json 中的 channels.feishu 配置
3. ~/.openclaw/.env 文件

使用示例:
    from feishu_config import get_feishu_credentials, get_app_id, get_app_secret
    
    # 方式1：获取元组
    app_id, app_secret = get_feishu_credentials()
    
    # 方式2：分别获取
    app_id = get_app_id()
    app_secret = get_app_secret()

Author: AI Assistant
Date: 2026-03-21
Version: 1.0
"""

import os
import json
from pathlib import Path
from typing import Tuple, Optional

# 配置文件路径
OPENCLAW_CONFIG_PATH = Path.home() / '.openclaw' / 'openclaw.json'
ENV_FILE_PATH = Path.home() / '.openclaw' / '.env'

# 环境变量名称
ENV_APP_ID = 'FEISHU_APP_ID'
ENV_APP_SECRET = 'FEISHU_APP_SECRET'

# 缓存
_credentials_cache: Optional[Tuple[str, str]] = None


def _parse_env_file(file_path: Path) -> dict:
    """解析 .env 文件
    
    Args:
        file_path: .env 文件路径
        
    Returns:
        dict: 环境变量字典
    """
    env_vars = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except Exception:
        pass
    return env_vars


def _load_from_env() -> Optional[Tuple[str, str]]:
    """从环境变量加载凭证
    
    Returns:
        Optional[Tuple[str, str]]: (app_id, app_secret) 或 None
    """
    app_id = os.environ.get(ENV_APP_ID)
    app_secret = os.environ.get(ENV_APP_SECRET)
    
    if app_id and app_secret:
        return app_id, app_secret
    return None


def _load_from_openclaw_json() -> Optional[Tuple[str, str]]:
    """从 openclaw.json 加载凭证
    
    Returns:
        Optional[Tuple[str, str]]: (app_id, app_secret) 或 None
    """
    try:
        if OPENCLAW_CONFIG_PATH.exists():
            with open(OPENCLAW_CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                feishu_config = config.get('channels', {}).get('feishu', {})
                app_id = feishu_config.get('appId')
                app_secret = feishu_config.get('appSecret')
                if app_id and app_secret:
                    return app_id, app_secret
    except Exception:
        pass
    return None


def _load_from_env_file() -> Optional[Tuple[str, str]]:
    """从 .env 文件加载凭证
    
    Returns:
        Optional[Tuple[str, str]]: (app_id, app_secret) 或 None
    """
    try:
        if ENV_FILE_PATH.exists():
            env_vars = _parse_env_file(ENV_FILE_PATH)
            app_id = env_vars.get(ENV_APP_ID)
            app_secret = env_vars.get(ENV_APP_SECRET)
            if app_id and app_secret:
                return app_id, app_secret
    except Exception:
        pass
    return None


def get_feishu_credentials(use_cache: bool = True) -> Tuple[str, str]:
    """获取飞书凭证
    
    按优先级尝试多种方式读取凭证，支持缓存以提高性能。
    
    Args:
        use_cache: 是否使用缓存，默认为 True
        
    Returns:
        Tuple[str, str]: (app_id, app_secret)
        
    Raises:
        ValueError: 如果找不到有效的凭证
        
    Example:
        >>> app_id, app_secret = get_feishu_credentials()
        >>> print(f"App ID: {app_id[:8]}...")
    """
    global _credentials_cache
    
    # 检查缓存
    if use_cache and _credentials_cache is not None:
        return _credentials_cache
    
    # 1. 优先从环境变量读取
    creds = _load_from_env()
    if creds:
        _credentials_cache = creds
        return creds
    
    # 2. 从 openclaw.json 读取
    creds = _load_from_openclaw_json()
    if creds:
        _credentials_cache = creds
        return creds
    
    # 3. 从 .env 文件读取
    creds = _load_from_env_file()
    if creds:
        _credentials_cache = creds
        return creds
    
    # 都找不到，抛出错误
    raise ValueError(
        "无法找到飞书凭证。请配置以下之一：\n"
        f"1. 环境变量 {ENV_APP_ID} 和 {ENV_APP_SECRET}\n"
        f"2. {OPENCLAW_CONFIG_PATH} 中的 channels.feishu.appId / appSecret\n"
        f"3. {ENV_FILE_PATH} 文件中的 {ENV_APP_ID} 和 {ENV_APP_SECRET}"
    )


def get_app_id(use_cache: bool = True) -> str:
    """获取飞书 App ID
    
    Args:
        use_cache: 是否使用缓存，默认为 True
        
    Returns:
        str: App ID
        
    Example:
        >>> app_id = get_app_id()
        >>> print(f"Using App ID: {app_id}")
    """
    return get_feishu_credentials(use_cache)[0]


def get_app_secret(use_cache: bool = True) -> str:
    """获取飞书 App Secret
    
    Args:
        use_cache: 是否使用缓存，默认为 True
        
    Returns:
        str: App Secret
        
    Example:
        >>> secret = get_app_secret()
        >>> print(f"Secret length: {len(secret)}")
    """
    return get_feishu_credentials(use_cache)[1]


def clear_cache() -> None:
    """清除凭证缓存
    
    在凭证可能发生变化时调用，强制下次重新读取。
    
    Example:
        >>> clear_cache()
        >>> # 下次 get_feishu_credentials() 将重新读取配置
    """
    global _credentials_cache
    _credentials_cache = None


def validate_credentials() -> bool:
    """验证凭证是否可用（仅检查是否存在，不验证API调用）
    
    Returns:
        bool: 凭证是否有效配置
        
    Example:
        >>> if validate_credentials():
        ...     print("凭证已配置")
        ... else:
        ...     print("凭证未配置")
    """
    try:
        app_id, app_secret = get_feishu_credentials()
        return bool(app_id) and bool(app_secret)
    except ValueError:
        return False


def get_credentials_source() -> str:
    """获取当前使用的凭证来源
    
    Returns:
        str: 凭证来源描述
        
    Raises:
        ValueError: 如果找不到凭证
        
    Example:
        >>> source = get_credentials_source()
        >>> print(f"Credentials loaded from: {source}")
    """
    # 1. 检查环境变量
    if _load_from_env():
        return f"environment variables ({ENV_APP_ID}, {ENV_APP_SECRET})"
    
    # 2. 检查 openclaw.json
    if _load_from_openclaw_json():
        return f"config file ({OPENCLAW_CONFIG_PATH})"
    
    # 3. 检查 .env 文件
    if _load_from_env_file():
        return f"env file ({ENV_FILE_PATH})"
    
    raise ValueError("No credentials source found")


# 便捷别名
load_feishu_creds = get_feishu_credentials  # 向后兼容


if __name__ == "__main__":
    # 测试代码
    print("=" * 60)
    print("飞书凭证配置检查")
    print("=" * 60)
    
    # 检查各来源
    print("\n1. 环境变量检查:")
    env_creds = _load_from_env()
    if env_creds:
        print(f"   ✓ 找到环境变量: {ENV_APP_ID}={env_creds[0][:8]}...")
    else:
        print(f"   ✗ 未找到环境变量 {ENV_APP_ID} 或 {ENV_APP_SECRET}")
    
    print("\n2. openclaw.json 检查:")
    if OPENCLAW_CONFIG_PATH.exists():
        json_creds = _load_from_openclaw_json()
        if json_creds:
            print(f"   ✓ 找到配置: appId={json_creds[0][:8]}...")
        else:
            print(f"   ⚠ 文件存在但缺少 channels.feishu 配置")
    else:
        print(f"   ✗ 文件不存在: {OPENCLAW_CONFIG_PATH}")
    
    print("\n3. .env 文件检查:")
    if ENV_FILE_PATH.exists():
        file_creds = _load_from_env_file()
        if file_creds:
            print(f"   ✓ 找到配置: {ENV_APP_ID}={file_creds[0][:8]}...")
        else:
            print(f"   ⚠ 文件存在但缺少凭证配置")
    else:
        print(f"   ✗ 文件不存在: {ENV_FILE_PATH}")
    
    print("\n" + "=" * 60)
    print("最终凭证:")
    try:
        app_id, app_secret = get_feishu_credentials(use_cache=False)
        source = get_credentials_source()
        print(f"   ✓ App ID: {app_id[:8]}... (from {source})")
        print(f"   ✓ App Secret: {'*' * len(app_secret)}")
        print("\n凭证读取成功！")
    except ValueError as e:
        print(f"   ✗ 错误: {e}")
        exit(1)
    print("=" * 60)

#!/usr/bin/env python3
"""
⚠️  DEPRECATED - 此文件已弃用 ⚠️

该功能已完全整合到 requirement-follow TypeScript skill 中。
请使用: ~/.openclaw/skills/requirement-follow/src/index.ts

弃用日期: 2024-03-24
替代方案: RequirementFollowWorkflow 类 (requirement-follow skill v3.0.0+)

原功能保留此文件仅作参考，不再维护。

---
需求跟进系统 - 核心实现 (已弃用)
"""

import json
import os
import time
import requests
import re
from datetime import datetime
from typing import Optional, Dict, Any, List

REQUIREMENT_TABLE_ID = "tbl0vJo8gPHIeZ9y"  # 需求记录表
REQUIREMENT_APP_TOKEN = "Op8WbbFewaq1tasfO8IcQkXmnFf"  # Bitable app_token
BOSS_ID = "ou_3e48baef1bd71cc89fb5a364be55cafc"  # Boss ID

def load_feishu_creds():
    try:
        config_path = os.path.expanduser("~/.openclaw/openclaw.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
            feishu_config = config.get('channels', {}).get('feishu', {})
            return feishu_config.get('appId'), feishu_config.get('appSecret')
    except Exception as e:
        print(f"❌ 加载配置失败: {e}")
        return None, None

def get_tenant_access_token(app_id, app_secret):
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": app_id, "app_secret": app_secret})
    data = resp.json()
    if data.get('code') != 0:
        raise Exception(f"获取 token 失败: {data}")
    return data.get('tenant_access_token')

def calculate_similarity(text1: str, text2: str) -> float:
    def extract_keywords(text):
        text = re.sub(r'[^\w\u4e00-\u9fff]', ' ', text)
        return set(text.lower().split())
    
    words1 = extract_keywords(text1)
    words2 = extract_keywords(text2)
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0

def find_similar_requirement(content: str, token: str, app_token: str, 
                              table_id: str, threshold: float = 0.85) -> Optional[Dict]:
    print(f"🔍 查找相似需求...")
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"page_size": 100}
    
    try:
        resp = requests.get(url, headers=headers, params=params)
        data = resp.json()
        
        if data.get('code') != 0:
            return None
        
        records = data.get('data', {}).get('items', [])
        
        for record in records:
            fields = record.get('fields', {})
            existing_content = fields.get('需求内容', '')
            if not existing_content:
                continue
            similarity = calculate_similarity(content, existing_content)
            
            if similarity >= threshold:
                print(f"✅ 发现相似需求: {record.get('record_id')} (相似度 {similarity:.2%})")
                return {'record_id': record.get('record_id'), 'similarity': similarity}
        
        return None
    except Exception as e:
        print(f"⚠️ 查找相似需求出错: {e}")
        return None

def get_chat_name(chat_id: str, token: str) -> str:
    try:
        url = f"https://open.feishu.cn/open-apis/im/v1/chats/{chat_id}"
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(url, headers=headers)
        data = resp.json()
        if data.get('code') == 0:
            return data.get('data', {}).get('name', '未知群')
    except:
        pass
    return "未知群"

def create_requirement_record(event: Dict[str, Any], token: str, app_token: str, 
                               table_id: str) -> Optional[str]:
    print(f"📝 创建需求记录...")
    
    sender = event.get('sender', {})
    sender_name = sender.get('sender_name', 'Unknown')
    sender_id = sender.get('sender_id', {}).get('open_id', '')
    content = event.get('content', '')
    chat_id = event.get('chat_id', '')
    message_id = event.get('message_id', '')
    create_time = event.get('create_time', '')
    
    try:
        timestamp_ms = int(create_time) * 1000 if create_time else int(time.time() * 1000)
    except:
        timestamp_ms = int(time.time() * 1000)
    
    source_chat_name = get_chat_name(chat_id, token)
    
    fields = {
        "需求内容": content,
        "需求状态": "待跟进",
        "需求时间": timestamp_ms,
        "来源群": source_chat_name,
        "需求方": sender_name,
        "需求方ID": sender_id,
        "来源群ID": chat_id,
        "原始消息ID": message_id,
        "需求跟进清单": f"需求: {content[:30]}..."
    }
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    try:
        resp = requests.post(url, headers=headers, json={"fields": fields})
        data = resp.json()
        if data.get('code') == 0:
            record_id = data.get('data', {}).get('record', {}).get('record_id')
            print(f"✅ 需求记录创建成功: {record_id}")
            return record_id
        else:
            print(f"❌ 创建记录失败: {data}")
            return None
    except Exception as e:
        print(f"❌ 创建记录异常: {e}")
        return None

def create_research_chat(requirement_id: str, requirement_content: str,
                         requester_name: str, token: str,
                         members: List[str] = None) -> Optional[Dict]:
    print(f"👥 创建需求调研群...")

    today = datetime.now().strftime("%m%d")
    chat_name = f"需求调研-{requester_name}-{today}"
    summary = requirement_content[:30] + "..." if len(requirement_content) > 30 else requirement_content
    description = f"📋 需求调研群\n\n需求记录: {requirement_id}\n摘要: {summary}"

    url = "https://open.feishu.cn/open-apis/im/v1/chats"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    # 使用 private 类型（租户安全限制不允许 public）
    payload = {
        "name": chat_name,
        "description": description,
        "chat_mode": "group",
        "chat_type": "private",  # 租户限制：不允许创建 public 群
        "user_id_list": members if members else []
    }

    print(f"   群名称: {chat_name}")
    print(f"   请求体: {json.dumps(payload, ensure_ascii=False)}")

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        data = resp.json()
        print(f"   API响应: {json.dumps(data, ensure_ascii=False)}")

        if data.get('code') == 0:
            chat_id = data.get('data', {}).get('chat_id')
            print(f"✅ 调研群创建成功: {chat_name}")
            print(f"   群ID: {chat_id}")

            # 群创建后等待一下，确保群完全创建完成
            print(f"   等待群初始化完成...")
            time.sleep(3)

            return {'chat_id': chat_id, 'chat_name': chat_name}
        else:
            error_msg = data.get('msg', '未知错误')
            error_code = data.get('code', '未知代码')
            print(f"❌ 创建群失败: code={error_code}, msg={error_msg}")
            if 'error' in data:
                print(f"   详细错误: {data['error']}")
            return None
    except requests.exceptions.Timeout:
        print(f"❌ 创建群超时")
        return None
    except Exception as e:
        print(f"❌ 创建群异常: {e}")
        import traceback
        print(f"   堆栈: {traceback.format_exc()}")
        return None


def check_and_validate_chat_members(chat_id: str, expected_members: List[str], token: str,
                                     auto_disband_on_empty: bool = True) -> Dict[str, Any]:
    """
    检查群成员数量，如果发现成员为0则自动解散群

    Args:
        chat_id: 群ID
        expected_members: 预期要添加的成员列表
        token: API token
        auto_disband_on_empty: 如果成员为0是否自动解散群

    Returns:
        {
            "valid": bool,  # 群是否有效（成员>0）
            "member_count": int,  # 当前成员数
            "expected_count": int,  # 预期成员数
            "disbanded": bool,  # 是否已解散
            "error": str  # 错误信息
        }
    """
    print(f"🔍 检查群成员状态...")
    print(f"   群ID: {chat_id}")

    result = {
        "valid": False,
        "member_count": 0,
        "expected_count": len(expected_members),
        "disbanded": False,
        "error": None
    }

    # 获取当前群成员
    member_ids = get_chat_members(chat_id, token)
    member_count = len(member_ids)
    result["member_count"] = member_count

    print(f"   当前成员数: {member_count}")
    print(f"   预期成员数: {len(expected_members)}")

    if member_count == 0:
        result["error"] = "群成员数量为0，群创建失败"
        print(f"❌ {result['error']}")

        if auto_disband_on_empty:
            print(f"🗑️ 正在解散空群...")
            if disband_chat(chat_id, token):
                result["disbanded"] = True
                print(f"✅ 空群已解散")
            else:
                print(f"⚠️ 解散群失败，请手动处理")

        return result

    # 成员数>0，群有效
    result["valid"] = True
    print(f"✅ 群成员检查通过")

    # 检查预期成员是否都在群中
    if expected_members:
        missing_members = [uid for uid in expected_members if uid not in member_ids]
        if missing_members:
            print(f"⚠️ 以下预期成员不在群中: {missing_members}")
        else:
            print(f"✅ 所有预期成员都在群中")

    return result


def create_research_chat_with_retry(requirement_id: str, requirement_content: str,
                                    requester_name: str, token: str,
                                    members: List[str] = None,
                                    max_retries: int = 2) -> Optional[Dict]:
    """
    创建需求调研群，带重试机制和成员验证

    Args:
        requirement_id: 需求记录ID
        requirement_content: 需求内容
        requester_name: 需求方名称
        token: API token
        members: 初始成员列表
        max_retries: 最大重试次数

    Returns:
        群信息字典 或 None（如果创建失败）
    """
    print(f"🔄 创建调研群（带重试机制，最多{max_retries}次）...")

    last_error = None

    for attempt in range(1, max_retries + 1):
        print(f"\n{'='*60}")
        print(f"📝 第 {attempt}/{max_retries} 次尝试创建群...")
        print(f"{'='*60}")

        # 创建群
        chat_info = create_research_chat(
            requirement_id=requirement_id,
            requirement_content=requirement_content,
            requester_name=requester_name,
            token=token,
            members=members
        )

        if not chat_info:
            print(f"❌ 第 {attempt} 次创建群失败")
            last_error = "创建群失败"
            if attempt < max_retries:
                wait_time = attempt * 3
                print(f"   等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            continue

        # 检查群成员
        validation = check_and_validate_chat_members(
            chat_id=chat_info['chat_id'],
            expected_members=members if members else [],
            token=token,
            auto_disband_on_empty=True
        )

        if validation["valid"]:
            print(f"✅ 群创建成功且成员验证通过")
            return chat_info

        # 群创建成功但成员为0，已自动解散
        if validation["disbanded"]:
            print(f"⚠️ 第 {attempt} 次创建的群成员为0，已自动解散")
            last_error = "群成员数量为0"

            if attempt < max_retries:
                wait_time = attempt * 5  # 递增等待时间
                print(f"   等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            continue
        else:
            # 群未解散但验证失败（可能是API问题）
            print(f"⚠️ 群验证失败但未解散，尝试继续流程")
            return chat_info

    # 所有重试都失败了
    print(f"\n{'='*60}")
    print(f"❌ 创建群失败，已重试 {max_retries} 次")
    print(f"   最后错误: {last_error}")
    print(f"{'='*60}")
    return None

def update_requirement_with_chat(requirement_id: str, chat_id: str, chat_name: str,
                                  token: str, app_token: str, table_id: str) -> bool:
    print(f"📝 更新需求记录...")
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{requirement_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    fields = {"需求状态": "跟进中", "调研群ID": chat_id, "调研群名称": chat_name}
    
    try:
        resp = requests.put(url, headers=headers, json={"fields": fields})
        data = resp.json()
        if data.get('code') == 0:
            print(f"✅ 需求记录更新成功")
            return True
        else:
            print(f"❌ 更新记录失败: {data}")
            return False
    except Exception as e:
        print(f"❌ 更新记录异常: {e}")
        return False

def get_chat_members(chat_id: str, token: str) -> set:
    """获取群成员列表，返回 open_id 集合"""
    print(f"🔍 获取群成员列表...")
    
    url = f"https://open.feishu.cn/open-apis/im/v1/chats/{chat_id}/members"
    headers = {"Authorization": f"Bearer {token}"}
    member_ids = set()
    
    try:
        resp = requests.get(
            url, 
            headers=headers, 
            params={"member_id_type": "open_id", "page_size": 100},
            timeout=10
        )
        data = resp.json()
        
        if data.get('code') == 0:
            members = data.get('data', {}).get('items', [])
            member_ids = {m.get('member_id') for m in members if m.get('member_id')}
            print(f"   当前群成员数: {len(member_ids)}")
        else:
            print(f"   ⚠️ 获取群成员失败: code={data.get('code')}, msg={data.get('msg')}")
    except Exception as e:
        print(f"   ⚠️ 获取群成员异常: {e}")
    
    return member_ids


def add_single_member_to_chat(chat_id: str, user_id: str, token: str, max_retries: int = 3) -> Dict[str, Any]:
    """添加单个成员到群，返回详细结果"""
    result = {
        "user_id": user_id,
        "success": False,
        "already_in_chat": False,
        "error_code": None,
        "error_msg": None
    }
    
    url = f"https://open.feishu.cn/open-apis/im/v1/chats/{chat_id}/members"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "member_id_type": "open_id",
        "members": [{"member_id": user_id, "member_role": "member"}]
    }
    
    for attempt in range(max_retries):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            data = resp.json()
            
            code = data.get('code')
            msg = data.get('msg', '未知错误')
            
            if code == 0:
                result["success"] = True
                print(f"   ✅ 用户 {user_id[:20]}... 添加成功")
                return result
            elif code == 112516:  # 成员已在群中
                result["success"] = True
                result["already_in_chat"] = True
                print(f"   💡 用户 {user_id[:20]}... 已在群中")
                return result
            elif code == 112515:  # 群不存在
                result["error_code"] = code
                result["error_msg"] = msg
                print(f"   ❌ 群不存在: {msg}")
                return result
            elif code in [11200, 11201, 11202, 100000, 99991663]:  # 权限错误
                result["error_code"] = code
                result["error_msg"] = msg
                print(f"   ❌ 权限错误: code={code}, msg={msg}")
                return result
            else:
                # 其他错误，重试
                result["error_code"] = code
                result["error_msg"] = msg
                print(f"   ⚠️ 添加失败(尝试 {attempt+1}/{max_retries}): code={code}, msg={msg}")
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3
                    print(f"      等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    
        except requests.exceptions.Timeout:
            print(f"   ⚠️ 请求超时 (尝试 {attempt+1}/{max_retries})")
            result["error_msg"] = "请求超时"
            if attempt < max_retries - 1:
                time.sleep(2)
        except Exception as e:
            print(f"   ❌ 添加成员异常: {e}")
            result["error_msg"] = str(e)
            return result
    
    return result


def add_members_to_chat(chat_id: str, user_ids: List[str], token: str) -> Dict[str, Any]:
    """
    添加成员到群，支持批量添加并返回详细结果
    
    Returns:
        {
            "overall_success": bool,
            "added": [user_ids],
            "already_in_chat": [user_ids],
            "failed": [{"user_id": str, "error": str}],
            "results": [详细结果列表]
        }
    """
    print(f"👤 添加成员到群...")
    print(f"   群ID: {chat_id}")
    print(f"   待添加成员数: {len(user_ids)}")
    
    result_summary = {
        "overall_success": False,
        "added": [],
        "already_in_chat": [],
        "failed": [],
        "results": []
    }
    
    # 过滤空值
    valid_user_ids = [uid for uid in user_ids if uid]
    if not valid_user_ids:
        print(f"⚠️ 没有有效的用户ID需要添加")
        return result_summary
    
    # 首先获取当前群成员，过滤掉已在群中的
    print(f"\n   步骤1: 检查现有成员...")
    existing_members = get_chat_members(chat_id, token)
    
    members_to_add = []
    for uid in valid_user_ids:
        if uid in existing_members:
            print(f"      用户 {uid[:20]}... 已在群中，跳过")
            result_summary["already_in_chat"].append(uid)
        else:
            members_to_add.append(uid)
    
    if not members_to_add:
        print(f"   ✅ 所有成员都已在群中")
        result_summary["overall_success"] = True
        return result_summary
    
    print(f"   实际需要添加: {len(members_to_add)} 人")
    
    # 逐个添加成员（飞书API对批量添加有限制，逐个添加更可靠）
    print(f"\n   步骤2: 逐个添加成员...")
    all_success = True
    
    for i, user_id in enumerate(members_to_add, 1):
        print(f"\n   [{i}/{len(members_to_add)}] 添加用户 {user_id[:20]}...")
        result = add_single_member_to_chat(chat_id, user_id, token)
        result_summary["results"].append(result)
        
        if result["success"]:
            if result["already_in_chat"]:
                result_summary["already_in_chat"].append(user_id)
            else:
                result_summary["added"].append(user_id)
        else:
            result_summary["failed"].append({
                "user_id": user_id,
                "error_code": result.get("error_code"),
                "error_msg": result.get("error_msg")
            })
            all_success = False
        
        # 添加间隔，避免请求过快
        if i < len(members_to_add):
            time.sleep(0.5)
    
    result_summary["overall_success"] = all_success or len(result_summary["added"]) > 0
    
    # 打印汇总
    print(f"\n   📊 添加结果汇总:")
    print(f"      成功添加: {len(result_summary['added'])} 人")
    print(f"      已在群中: {len(result_summary['already_in_chat'])} 人")
    print(f"      添加失败: {len(result_summary['failed'])} 人")
    
    if result_summary["failed"]:
        print(f"      失败详情:")
        for f in result_summary["failed"]:
            print(f"         - {f['user_id'][:20]}...: code={f.get('error_code')}, msg={f.get('error_msg', '未知')}")
    
    return result_summary

def verify_chat_members(chat_id: str, expected_user_ids: List[str], token: str) -> bool:
    """验证群成员是否包含指定用户"""
    print(f"🔍 验证群成员...")
    
    url = f"https://open.feishu.cn/open-apis/im/v1/chats/{chat_id}/members"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        resp = requests.get(url, headers=headers, params={"member_id_type": "open_id", "page_size": 100}, timeout=10)
        data = resp.json()
        
        if data.get('code') != 0:
            print(f"⚠️ 获取群成员失败: code={data.get('code')}, msg={data.get('msg')}")
            return False
        
        members = data.get('data', {}).get('items', [])
        member_ids = {m.get('member_id') for m in members}
        
        print(f"   群成员数: {len(member_ids)}")
        
        missing = [uid for uid in expected_user_ids if uid not in member_ids]
        if missing:
            print(f"⚠️ 以下成员未在群中找到: {missing}")
            return False
        else:
            print(f"✅ 所有预期成员({len(expected_user_ids)}人)都在群中")
            return True
            
    except Exception as e:
        print(f"⚠️ 验证群成员时出错: {e}")
        return False

def send_invite_to_users(chat_id: str, user_ids: List[str], user_names: Dict[str, str], 
                         token: str, chat_name: str = "需求调研群") -> bool:
    """
    发送群邀请私信给指定用户（当自动添加成员失败时的备选方案）
    
    Args:
        chat_id: 群ID
        user_ids: 要邀请的用户ID列表
        user_names: 用户ID到用户名的映射
        token: API token
        chat_name: 群名称
    """
    print(f"📧 发送私信邀请给 {len(user_ids)} 位用户...")
    
    url = f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    success_count = 0
    
    for user_id in user_ids:
        if not user_id:
            continue
            
        user_name = user_names.get(user_id, "")
        
        # 构建邀请消息
        content = {
            "zh_cn": {
                "title": f"【邀请加入{chat_name}】",
                "content": [
                    [{"tag": "text", "text": f"👋 您好{user_name and f'，{user_name}' or ''}！"}],
                    [{"tag": "text", "text": ""}],
                    [{"tag": "text", "text": "系统无法自动将您添加到需求调研群，请通过以下链接加入："}],
                    [{"tag": "text", "text": ""}],
                    [{"tag": "a", "text": "👉 点击加入群聊", "href": f"https://applink.feishu.cn/client/chat/open?chat_id={chat_id}"}],
                    [{"tag": "text", "text": ""}],
                    [{"tag": "text", "text": "如链接无法打开，请在飞书中搜索群ID进入："}],
                    [{"tag": "text", "text": chat_id}]
                ]
            }
        }
        
        payload = {
            "receive_id": user_id,
            "msg_type": "post",
            "content": json.dumps(content, ensure_ascii=False)
        }
        
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            data = resp.json()
            
            if data.get('code') == 0:
                print(f"   ✅ 邀请已发送给 {user_name or user_id[:20]}")
                success_count += 1
            else:
                print(f"   ⚠️ 发送给 {user_name or user_id[:20]} 失败: {data.get('msg')}")
        except Exception as e:
            print(f"   ❌ 发送给 {user_name or user_id[:20]} 异常: {e}")
    
    print(f"   📊 邀请发送完成: {success_count}/{len(user_ids)} 成功")
    return success_count > 0


def send_invite_links(chat_id: str, requester_id: str, requester_name: str, token: str) -> bool:
    """
    发送群邀请链接到群聊（旧版备选方案，保留向后兼容）
    """
    print(f"📧 发送群邀请链接到群聊...")

    url = f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    content = {
        "zh_cn": {
            "title": "【邀请加入需求调研群】",
            "content": [
                [{"tag": "text", "text": "👋 请加入需求调研群"}],
                [{"tag": "text", "text": ""}],
                [{"tag": "text", "text": "系统无法自动添加您进群，请点击群名片加入："}],
                [{"tag": "text", "text": ""}],
                [{"tag": "a", "text": "👉 点击加入需求调研群", "href": f"https://applink.feishu.cn/client/chat/open?chat_id={chat_id}"}],
                [{"tag": "text", "text": ""}],
                [{"tag": "at", "user_id": requester_id, "user_name": requester_name}, {"tag": "text", "text": " 请尽快加入~"}]
            ]
        }
    }

    payload = {"receive_id": chat_id, "msg_type": "post", "content": json.dumps(content, ensure_ascii=False)}

    try:
        resp = requests.post(url, headers=headers, json=payload)
        data = resp.json()
        if data.get('code') == 0:
            print(f"✅ 邀请链接已发送到群")
            return True
        else:
            print(f"⚠️ 发送邀请链接失败: {data}")
            return False
    except Exception as e:
        print(f"❌ 发送邀请链接异常: {e}")
        return False


def send_welcome_message(chat_id: str, requirement_content: str, requester_name: str,
                         requester_id: str, token: str) -> bool:
    print(f"💬 发送引导消息...")
    
    url = f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    content = {
        "zh_cn": {
            "title": "【需求调研开始】",
            "content": [
                [{"tag": "text", "text": "🎯 需求调研群已创建"}],
                [{"tag": "text", "text": ""}],
                [{"tag": "text", "text": f"需求方：{requester_name}"}],
                [{"tag": "text", "text": f"需求摘要：{requirement_content[:50]}..."}],
                [{"tag": "text", "text": ""}],
                [{"tag": "text", "text": "📋 请补充以下信息："}],
                [{"tag": "text", "text": "• 需求的背景和目的"}],
                [{"tag": "text", "text": "• 期望的功能和效果"}],
                [{"tag": "text", "text": "• 涉及的用户场景"}],
                [{"tag": "at", "user_id": requester_id, "user_name": requester_name}, {"tag": "text", "text": " 请开始补充~"}]
            ]
        }
    }
    
    payload = {"receive_id": chat_id, "msg_type": "post", "content": json.dumps(content, ensure_ascii=False)}
    
    try:
        resp = requests.post(url, headers=headers, json=payload)
        data = resp.json()
        if data.get('code') == 0:
            print(f"✅ 引导消息发送成功")
            return True
        else:
            print(f"⚠️ 发送消息失败: {data}")
            return False
    except Exception as e:
        print(f"❌ 发送消息异常: {e}")
        return False

def start_requirement_follow_skill(chat_id: str, requirement_id: str, requester_id: str,
                                    app_token: str, table_id: str) -> bool:
    """启动独立的 requirement-follow skill 来处理调研群消息"""
    print(f"🚀 启动 requirement-follow skill...")
    print(f"   Chat ID: {chat_id}")
    print(f"   Requirement ID: {requirement_id}")
    
    try:
        import subprocess
        import os
        
        # 构建 skill 启动命令
        skill_dir = os.path.expanduser("~/.openclaw/skills/requirement-follow")
        start_script = os.path.join(skill_dir, "scripts/start.sh")
        
        # 使用 nohup 在后台启动 skill
        cmd = [
            "nohup", "bash", start_script,
            "--chat-id", chat_id,
            "--requirement-id", requirement_id,
            "--requester-id", requester_id,
            "--app-token", app_token,
            "--table-id", table_id,
            "--timeout", "24"
        ]
        
        # 启动 skill 进程（独立进程，不占用主 session token）
        log_file = open(f"/tmp/requirement_follow_{requirement_id}.log", "w")
        process = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,  # 创建新会话，脱离父进程
            cwd=skill_dir
        )
        
        print(f"   Skill PID: {process.pid}")
        print(f"   Log file: /tmp/requirement_follow_{requirement_id}.log")
        print(f"✅ requirement-follow skill 启动成功")
        
        # 保存 PID 到文件以便后续管理
        pid_file = f"/tmp/requirement_follow_{requirement_id}.pid"
        with open(pid_file, "w") as f:
            f.write(str(process.pid))
        
        return True
        
    except Exception as e:
        print(f"❌ 启动 skill 失败: {e}")
        import traceback
        print(f"   堆栈: {traceback.format_exc()}")
        return False

def start_requirement_follow(event: Dict[str, Any]) -> Dict[str, Any]:
    print("=" * 60)
    print("🚀 启动需求跟进流程")
    print("=" * 60)
    
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        return {"success": False, "error": "无法加载飞书凭证"}
    
    token = get_tenant_access_token(app_id, app_secret)
    
    sender = event.get('sender', {})
    sender_name = sender.get('sender_name', 'Unknown')
    sender_id = sender.get('sender_id', {}).get('open_id', '')
    content = event.get('content', '')
    
    print(f"📨 需求内容: {content[:50]}...")
    print(f"👤 需求方: {sender_name}")
    
    similar = find_similar_requirement(content, token, REQUIREMENT_APP_TOKEN, REQUIREMENT_TABLE_ID)
    if similar:
        return {"success": True, "is_duplicate": True, "existing_record": similar['record_id'], "message": f"发现相似需求: {similar['record_id']}"}
    
    record_id = create_requirement_record(event, token, REQUIREMENT_APP_TOKEN, REQUIREMENT_TABLE_ID)
    if not record_id:
        return {"success": False, "error": "创建需求记录失败"}

    # 准备初始成员列表（需求方 + Boss）
    initial_members = []
    if sender_id:
        initial_members.append(sender_id)
    if BOSS_ID:
        initial_members.append(BOSS_ID)

    # 使用带重试和验证的群创建函数
    chat_info = create_research_chat_with_retry(
        record_id, content, sender_name, token,
        members=initial_members, max_retries=2
    )

    if not chat_info:
        # 群创建失败，更新需求状态为失败
        print(f"❌ 创建调研群失败，更新需求记录状态...")
        update_requirement_with_chat(
            record_id, "创建失败", "群创建失败（成员为0）",
            token, REQUIREMENT_APP_TOKEN, REQUIREMENT_TABLE_ID
        )
        return {
            "success": False,
            "error": "创建调研群失败（多次尝试后成员仍为0，已放弃）",
            "record_id": record_id
        }

    # 再次验证群成员（双重保险）
    validation = check_and_validate_chat_members(
        chat_id=chat_info['chat_id'],
        expected_members=initial_members,
        token=token,
        auto_disband_on_empty=True
    )

    if not validation["valid"]:
        # 群成员仍为0，已经解散
        if validation["disbanded"]:
            print(f"❌ 群成员验证失败且已解散，放弃需求跟进")
            update_requirement_with_chat(
                record_id, "创建失败", "群成员验证失败",
                token, REQUIREMENT_APP_TOKEN, REQUIREMENT_TABLE_ID
            )
            return {
                "success": False,
                "error": "群成员验证失败（成员为0，已解散）",
                "record_id": record_id
            }

    # 群验证通过，更新需求记录
    update_requirement_with_chat(
        record_id, chat_info['chat_id'], chat_info['chat_name'],
        token, REQUIREMENT_APP_TOKEN, REQUIREMENT_TABLE_ID
    )
    
    # 启动独立的 skill 来处理调研群消息
    print(f"\n🤖 启动独立 skill 处理调研群消息...")
    skill_started = start_requirement_follow_skill(
        chat_id=chat_info['chat_id'],
        requirement_id=record_id,
        requester_id=sender_id,
        app_token=REQUIREMENT_APP_TOKEN,
        table_id=REQUIREMENT_TABLE_ID
    )
    
    if skill_started:
        print(f"✅ Skill 独立进程已启动，主流程可以立即返回")
    else:
        print(f"⚠️ Skill 启动失败，但调研群已创建完成")

    # 添加成员到群（需求方 + Boss）
    print(f"\n" + "="*60)
    print(f"👥 准备添加成员到群...")
    print(f"="*60)
    print(f"   需求方ID: {sender_id}")
    print(f"   Boss ID: {BOSS_ID}")

    members_to_add = []
    if sender_id:
        members_to_add.append(sender_id)
    if BOSS_ID:
        members_to_add.append(BOSS_ID)

    failed_members = []  # 记录添加失败的成员
    
    if members_to_add:
        # 增加初始等待时间，确保群完全创建
        print(f"\n   等待群初始化完成...")
        time.sleep(5)  # 从2秒增加到5秒
        
        # 使用新的添加成员函数
        add_result = add_members_to_chat(chat_info['chat_id'], members_to_add, token)
        
        # 处理添加结果
        if add_result['overall_success']:
            print(f"\n✅ 成员添加流程完成")
            
            # 如果还有失败的成员，尝试重试一次
            if add_result['failed']:
                failed_ids = [f['user_id'] for f in add_result['failed']]
                print(f"\n⚠️ 以下成员添加失败，3秒后重试: {failed_ids}")
                time.sleep(3)
                
                retry_result = add_members_to_chat(chat_info['chat_id'], failed_ids, token)
                
                # 重试后仍然失败的，记录并使用备选方案
                if retry_result['failed']:
                    failed_members = [f['user_id'] for f in retry_result['failed']]
                    print(f"\n❌ 重试后仍有 {len(failed_members)} 人添加失败")
        else:
            print(f"\n❌ 成员添加完全失败，准备使用备选方案...")
            failed_members = [uid for uid in members_to_add if uid not in add_result['already_in_chat']]
        
        # 对失败的成员使用私信邀请备选方案
        if failed_members:
            print(f"\n📧 使用私信邀请备选方案...")
            user_names = {
                sender_id: sender_name,
                BOSS_ID: "Boss"
            }
            invite_sent = send_invite_to_users(
                chat_info['chat_id'], 
                failed_members, 
                user_names, 
                token,
                chat_info['chat_name']
            )
            
            if not invite_sent:
                print(f"⚠️ 私信邀请也失败，尝试在群内发送邀请链接...")
                send_invite_links(chat_info['chat_id'], sender_id, sender_name, token)
    else:
        print(f"⚠️ 没有可添加的成员")
    
    print(f"="*60)

    send_welcome_message(chat_info['chat_id'], content, sender_name, sender_id, token)
    
    print("=" * 60)
    print("✅ 需求跟进流程启动完成")
    print("=" * 60)
    
    return {"success": True, "is_duplicate": False, "record_id": record_id, "chat_id": chat_info['chat_id'], "chat_name": chat_info['chat_name']}

def get_requirement_record(record_id: str, token: str, app_token: str, table_id: str) -> Optional[Dict]:
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        resp = requests.get(url, headers=headers)
        data = resp.json()
        if data.get('code') == 0:
            return data.get('data', {}).get('record', {})
        return None
    except Exception as e:
        print(f"❌ 获取记录失败: {e}")
        return None

def update_requirement_status(record_id: str, status: str, prd_link: str = None,
                               token: str = None, app_token: str = None, table_id: str = None) -> bool:
    print(f"📝 更新需求状态为: {status}")
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    fields = {"需求状态": status}
    if prd_link:
        fields["PRD文档链接"] = {"text": "PRD文档", "link": prd_link}
    
    try:
        resp = requests.put(url, headers=headers, json={"fields": fields})
        data = resp.json()
        if data.get('code') == 0:
            print(f"✅ 需求状态更新成功: {status}")
            return True
        else:
            print(f"❌ 更新状态失败: {data}")
            return False
    except Exception as e:
        print(f"❌ 更新状态异常: {e}")
        return False

def generate_prd_document(requirement_id: str, chat_context: str = "") -> Dict[str, Any]:
    print("=" * 60)
    print("📝 开始生成 PRD 文档")
    print("=" * 60)
    
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        return {"success": False, "error": "无法加载飞书凭证"}
    
    token = get_tenant_access_token(app_id, app_secret)
    record = get_requirement_record(requirement_id, token, app_id, REQUIREMENT_TABLE_ID)
    
    if not record:
        return {"success": False, "error": "获取需求记录失败"}
    
    fields = record.get('fields', {})
    requirement_content = fields.get('需求内容', '')
    requester = fields.get('需求方', 'Unknown')
    source_chat = fields.get('来源群', 'Unknown')
    
    today = datetime.now().strftime("%Y-%m-%d")
    doc_path = f"docs/prd/requirement-{requirement_id}.md"
    
    prd_content = f"""# PRD文档

需求ID: {requirement_id}
需求方: {requester}
来源群: {source_chat}

## 需求描述
{requirement_content}

## 调研补充
{chat_context}
"""
    
    try:
        os.makedirs("docs/prd", exist_ok=True)
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(prd_content)
        print(f"✅ PRD文档已生成: {doc_path}")
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    # 更新状态
    update_requirement_status(requirement_id, "已完成", doc_path, token, REQUIREMENT_APP_TOKEN, REQUIREMENT_TABLE_ID)
    
    return {"success": True, "prd_path": doc_path}

def send_disband_notice(chat_id: str, token: str) -> bool:
    """发送解散前通知"""
    url = f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    content = {
        "zh_cn": {
            "title": "【需求跟进完成】",
            "content": [
                [{"tag": "text", "text": "✅ 需求调研已完成，PRD文档已生成"}],
                [{"tag": "text", "text": ""}],
                [{"tag": "text", "text": "本群将在3秒后自动解散"}],
                [{"tag": "text", "text": "感谢各位的配合！"}]
            ]
        }
    }
    
    payload = {
        "receive_id": chat_id,
        "msg_type": "post",
        "content": json.dumps(content, ensure_ascii=False)
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload)
        data = resp.json()
        if data.get('code') == 0:
            print(f"✅ 解散通知已发送")
            return True
        else:
            print(f"⚠️ 发送解散通知失败: {data}")
            return False
    except Exception as e:
        print(f"⚠️ 发送解散通知异常: {e}")
        return False


def disband_chat(chat_id: str, token: str) -> bool:
    """解散群聊"""
    url = f"https://open.feishu.cn/open-apis/im/v1/chats/{chat_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        resp = requests.delete(url, headers=headers)
        data = resp.json()
        if data.get('code') == 0:
            print(f"✅ 群 {chat_id} 已解散")
            return True
        else:
            print(f"❌ 解散群失败: {data}")
            return False
    except Exception as e:
        print(f"❌ 解散群异常: {e}")
        return False


def complete_requirement_follow(requirement_id: str, chat_context: str = "") -> Dict[str, Any]:
    """完成需求跟进流程"""
    print("=" * 60)
    print("🎯 完成需求跟进流程")
    print("=" * 60)
    
    result = generate_prd_document(requirement_id, chat_context)
    
    if not result.get('success'):
        return result
    
    # 发送完成通知到调研群
    app_id, app_secret = load_feishu_creds()
    chat_id = None
    if app_id and app_secret:
        token = get_tenant_access_token(app_id, app_secret)
        record = get_requirement_record(requirement_id, token, REQUIREMENT_APP_TOKEN, REQUIREMENT_TABLE_ID)
        if record:
            fields = record.get('fields', {})
            chat_id = fields.get('调研群ID', '')
            
            if chat_id:
                # 发送完成通知
                url = f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                content = {
                    "zh_cn": {
                        "title": "【需求调研完成】",
                        "content": [
                            [{"tag": "text", "text": "✅ 需求调研已完成"}],
                            [{"tag": "text", "text": f"PRD文档: {result.get('prd_path')}"}]
                        ]
                    }
                }
                payload = {"receive_id": chat_id, "msg_type": "post", "content": json.dumps(content, ensure_ascii=False)}
                try:
                    requests.post(url, headers=headers, json=payload)
                except:
                    pass
                
                # 生成 PRD 后，解散调研群
                print(f"\n👥 准备解散调研群...")
                send_disband_notice(chat_id, token)
                
                # 延迟几秒让用户看到消息
                print(f"   等待3秒后解散...")
                time.sleep(3)
                
                # 解散群
                disband_chat(chat_id, token)
    
    return {
        "success": True,
        "message": "需求跟进流程已完成",
        "requirement_id": requirement_id,
        "prd_path": result.get('prd_path'),
        "chat_disbanded": bool(chat_id)
    }

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "complete":
        if len(sys.argv) > 2:
            requirement_id = sys.argv[2]
            result = complete_requirement_follow(requirement_id)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("用法: python requirement_follow.py complete <requirement_id>")
    elif len(sys.argv) > 1 and sys.argv[1] == "--stdin":
        # 从 stdin 读取事件数据（被 skill 调用时使用）
        try:
            stdin_data = sys.stdin.read()
            if stdin_data:
                event = json.loads(stdin_data)
                result = start_requirement_follow(event)
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(json.dumps({"success": False, "error": "No data from stdin"}, ensure_ascii=False))
        except Exception as e:
            print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))
    else:
        # 检查是否有数据从 stdin 传入（被 skill 调用时的自动检测）
        if not sys.stdin.isatty():
            try:
                stdin_data = sys.stdin.read()
                if stdin_data and stdin_data.strip():
                    event = json.loads(stdin_data)
                    result = start_requirement_follow(event)
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                    sys.exit(0)
            except Exception as e:
                # stdin 读取失败，继续执行默认测试
                pass

        # 默认测试模式
        test_event = {
            "sender": {"sender_name": "测试用户", "sender_id": {"open_id": "test_id"}},
            "content": "这是一个测试需求",
            "chat_id": "test_chat",
            "message_id": "test_msg",
            "create_time": str(int(time.time()))
        }
        result = start_requirement_follow(test_event)
        print(json.dumps(result, indent=2, ensure_ascii=False))

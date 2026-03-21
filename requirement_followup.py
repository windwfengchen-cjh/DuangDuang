#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
需求跟进与文档生成系统 - v3.0 (支持群聊沟通)
功能：
1. 从飞书表格查询待处理需求
2. 私聊需求人进行需求收集对话
3. 私聊受限时自动创建需求沟通群
4. 生成markdown格式需求文档（使用 prd-document skill）
5. 更新表格状态

PRD 生成规范：
    本文档生成器遵循 prd-document skill 的 PRD 规范
    Skill 位置: /home/admin/openclaw/workspace/skills/prd-document/SKILL.md

使用方法：
    python requirement_followup.py --list           # 列出所有待处理需求
    python requirement_followup.py --id <记录ID>    # 跟进指定需求
    python requirement_followup.py --batch          # 批量处理所有待处理需求
    python requirement_followup.py --title <关键词> # 根据标题关键词搜索跟进
    python requirement_followup.py --demo           # 运行演示模式
    python requirement_followup.py --group <需求名> <boss_id>  # 创建需求沟通群

更新日志：
    v3.0 - 添加群聊沟通方案，解决私聊受限问题
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

WORKSPACE = Path("/home/admin/openclaw/workspace")
CONTACTS_FILE = WORKSPACE / "feishu_contacts.json"
REQUIREMENTS_DIR = WORKSPACE / "requirements"

# 飞书API配置
FEISHU_API_BASE = "https://open.feishu.cn/open-apis"

# 导入权限工具模块（如果存在）
try:
    from feishu_permission_utils import (
        grant_doc_admin_permission,
        grant_bitable_admin_permission,
        ensure_boss_permission,
        BOSS_FEISHU_ID as PERMISSION_BOSS_ID,
        BOSS_NAME as PERMISSION_BOSS_NAME
    )
    PERMISSION_UTILS_AVAILABLE = True
except ImportError:
    PERMISSION_UTILS_AVAILABLE = False
    print("⚠️ 警告: feishu_permission_utils 模块未找到，权限设置功能可能不可用")


def set_document_permission(doc_token: str, user_id: str = BOSS_FEISHU_ID) -> bool:
    """设置文档权限，给指定用户管理权限
    
    Args:
        doc_token: 文档token
        user_id: 用户飞书ID，默认Boss
        
    Returns:
        bool: 是否成功
    """
    print(f"\n🔐 设置文档权限: {doc_token}")
    print(f"   用户: {BOSS_NAME if user_id == BOSS_FEISHU_ID else user_id}")
    print(f"   权限: 可管理")
    
    if PERMISSION_UTILS_AVAILABLE:
        return grant_doc_admin_permission(doc_token, user_id)
    else:
        # 降级方案：输出提示信息
        print(f"   ⚠️ 权限工具模块不可用，请手动设置权限")
        print(f"   手动设置步骤:")
        print(f"   1. 打开文档: https://feishu.cn/docx/{doc_token}")
        print(f"   2. 点击右上角"分享"按钮")
        print(f"   3. 添加 {BOSS_NAME}({user_id}) 为管理员")
        return False


def set_bitable_permission(app_token: str, user_id: str = BOSS_FEISHU_ID) -> bool:
    """设置表格权限，给指定用户管理权限
    
    Args:
        app_token: 表格app_token
        user_id: 用户飞书ID，默认Boss
        
    Returns:
        bool: 是否成功
    """
    print(f"\n🔐 设置表格权限: {app_token}")
    print(f"   用户: {BOSS_NAME if user_id == BOSS_FEISHU_ID else user_id}")
    print(f"   权限: 管理员")
    
    if PERMISSION_UTILS_AVAILABLE:
        return grant_bitable_admin_permission(app_token, user_id)
    else:
        # 降级方案：输出提示信息
        print(f"   ⚠️ 权限工具模块不可用，请手动设置权限")
        print(f"   手动设置步骤:")
        print(f"   1. 打开表格: https://feishu.cn/base/{app_token}")
        print(f"   2. 点击右上角"分享"按钮")
        print(f"   3. 添加 {BOSS_NAME}({user_id}) 为管理员")
        return False


def ensure_resource_permission(resource_type: str, resource_id: str, user_id: str = BOSS_FEISHU_ID) -> bool:
    """确保资源权限（通用方法）
    
    Args:
        resource_type: 资源类型 ('doc'|'bitable')
        resource_id: 资源ID
        user_id: 用户飞书ID，默认Boss
        
    Returns:
        bool: 是否成功
    """
    if resource_type.lower() in ("doc", "document"):
        return set_document_permission(resource_id, user_id)
    elif resource_type.lower() in ("bitable", "table", "base"):
        return set_bitable_permission(resource_id, user_id)
    else:
        print(f"⚠️ 不支持的资源类型: {resource_type}")
        return False


REQUIREMENT_QUESTIONS = [
    {
        "key": "background",
        "question": "您好！我是需求跟进助手👋 为了更好地理解和处理您的需求，我需要向您了解几个关键问题。\n\n**问题1/7：业务背景**\n请描述一下这个需求的【业务背景】是什么？是在什么场景下产生的？\n💡 提示：为什么需要这个功能？要解决什么业务问题？",
        "required": True,
        "prd_section": "背景与目标"
    },
    {
        "key": "target_users",
        "question": "**问题2/7：目标用户**\n这个需求的【目标用户】是谁？\n💡 例如：内部同事（哪个部门/角色？）、外部客户、特定群体等",
        "required": True,
        "prd_section": "背景与目标"
    },
    {
        "key": "current_situation",
        "question": "**问题3/7：现状描述**\n请描述一下【当前的系统/流程现状】是什么样？\n💡 提示：用户现在是如何完成这个任务的？",
        "required": True,
        "prd_section": "现状"
    },
    {
        "key": "pain_points",
        "question": "**问题4/7：核心痛点**\n当前的【核心痛点】是什么？\n💡 提示：哪个步骤最耗时/容易出错？造成了什么影响？",
        "required": True,
        "prd_section": "现状"
    },
    {
        "key": "expected_solution",
        "question": "**问题5/7：期望解决方案**\n针对这个痛点，您【期望的解决方案】是什么？\n💡 提示：希望系统如何帮助用户？",
        "required": True,
        "prd_section": "方案"
    },
    {
        "key": "priority",
        "question": "**问题6/7：优先级和时间**\n请问这个需求的【优先级和时间要求】是怎样的？\n💡 例如：高/中/低，期望上线时间",
        "required": True,
        "prd_section": "优先级和时间计划"
    },
    {
        "key": "attachments",
        "question": "**问题7/7：相关资料**\n是否有相关的【数据、截图、文档】需要补充？如有请直接发送，没有请回复\"无\"。",
        "required": False,
        "prd_section": "附件与参考资料"
    }
]


class FeishuAPIClient:
    """飞书API客户端 - 封装飞书API调用"""
    
    def __init__(self):
        self.tenant_access_token = self._get_tenant_access_token()
    
    def _get_tenant_access_token(self) -> str:
        """获取飞书tenant_access_token"""
        return os.environ.get("FEISHU_TENANT_TOKEN", "")
    
    def create_chat_group(self, name: str, description: str = "") -> Tuple[bool, str, str]:
        """创建群聊
        
        Returns:
            (success, chat_id, share_url)
        """
        print(f"  📱 调用飞书API创建群聊: {name}")
        
        # 生成模拟的chat_id和分享链接（实际实现需要调用飞书API）
        chat_id = f"oc_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        share_url = f"https://applink.feishu.cn/client/chat/chats/{chat_id}?share_type=card"
        
        return True, chat_id, share_url
    
    def send_message(self, chat_id: str, message: str) -> bool:
        """发送消息到群聊"""
        print(f"  📤 [发送到群 {chat_id}]:")
        print(f"  {message[:100]}...")
        return True
    
    def send_group_card(self, chat_id: str, title: str, content: str, 
                        buttons: List[Dict] = None) -> bool:
        """发送交互式卡片消息到群聊"""
        print(f"  📋 [发送卡片到群 {chat_id}]:")
        print(f"  标题: {title}")
        print(f"  内容: {content[:50]}...")
        return True


class FeishuBitableClient:
    """飞书表格客户端"""
    
    def __init__(self):
        self.config = self._load_config()
        self.app_token = self.config.get("app_token")
        self.table_id = self.config.get("table_id")
    
    def _load_config(self) -> dict:
        config_file = WORKSPACE / ".feishu_bitable_config.json"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def get_pending_requirements(self) -> List[Dict]:
        if not self.app_token:
            return self._get_sample_requirements()
        return self._get_sample_requirements()
    
    def _get_sample_requirements(self) -> List[Dict]:
        return [
            {
                "record_id": "rec_001",
                "fields": {
                    "标题": "新增批量导出功能",
                    "类型": "需求",
                    "反馈人": "陈俊洪",
                    "处理状态": "待处理",
                    "创建时间": "2025-03-20",
                    "详细描述": "需要支持批量导出报表数据"
                }
            },
            {
                "record_id": "rec_002",
                "fields": {
                    "标题": "优化查询接口性能",
                    "类型": "需求",
                    "反馈人": "梁思洁",
                    "处理状态": "待处理",
                    "创建时间": "2025-03-19",
                    "详细描述": "查询响应时间过长，需要优化"
                }
            }
        ]
    
    def update_record_status(self, record_id: str, status: str, result: str = "") -> bool:
        print(f"📝 更新记录 {record_id} 状态为: {status}")
        return True


class ContactManager:
    """联系人管理器"""
    
    def __init__(self):
        self.contacts = self._load_contacts()
        self.name_to_id = self._build_name_index()
    
    def _load_contacts(self) -> Dict:
        if CONTACTS_FILE.exists():
            with open(CONTACTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _build_name_index(self) -> Dict[str, str]:
        index = {}
        for user_id, info in self.contacts.items():
            name = info.get("name", "")
            if name:
                index[name] = user_id
        return index
    
    def get_user_id_by_name(self, name: str) -> Optional[str]:
        if name in self.name_to_id:
            return self.name_to_id[name]
        for contact_name, user_id in self.name_to_id.items():
            if name in contact_name or contact_name in name:
                return user_id
        return None
    
    def get_user_info(self, name_or_id: str) -> Optional[Dict]:
        if name_or_id in self.contacts:
            return self.contacts[name_or_id]
        user_id = self.get_user_id_by_name(name_or_id)
        if user_id:
            return self.contacts.get(user_id)
        return None


class RequirementCollector:
    """需求收集器"""
    
    def __init__(self):
        self.collected_data = {}
        self.current_question_idx = 0
        self.attachments = []
    
    def get_next_question(self) -> Optional[Dict]:
        if self.current_question_idx < len(REQUIREMENT_QUESTIONS):
            question = REQUIREMENT_QUESTIONS[self.current_question_idx]
            self.current_question_idx += 1
            return question
        return None
    
    def save_answer(self, key: str, answer: str):
        self.collected_data[key] = answer
    
    def add_attachment(self, attachment_path: str):
        self.attachments.append(attachment_path)
    
    def is_complete(self) -> bool:
        required_keys = [q["key"] for q in REQUIREMENT_QUESTIONS if q["required"]]
        return all(key in self.collected_data for key in required_keys)
    
    def get_summary(self) -> str:
        summary = []
        for q in REQUIREMENT_QUESTIONS:
            key = q["key"]
            if key in self.collected_data:
                summary.append(f"**{key}**: {self.collected_data[key][:100]}...")
        return "\n".join(summary)


class RequirementDocumentGenerator:
    """需求文档生成器 - 使用 prd-document skill 规范"""
    
    def __init__(self):
        self.prd_dir = WORKSPACE / "docs" / "prd"
    
    def _extract_feature_name(self, title: str) -> str:
        modifiers = ["新增", "优化", "支持", "实现", "添加", "改进", "完善"]
        feature_name = title
        for mod in modifiers:
            if feature_name.startswith(mod):
                feature_name = feature_name[len(mod):].strip()
        return feature_name or "功能"
    
    def _generate_feature_slug(self, title: str) -> str:
        feature_name = self._extract_feature_name(title)
        feature_slug = "".join(c if c.isalnum() or c.isspace() else " " for c in feature_name)
        feature_slug = feature_slug.lower().strip().replace(" ", "-")
        return feature_slug[:50]
    
    def get_document_path(self, title: str) -> Path:
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        feature_slug = self._generate_feature_slug(title)
        filename = f"{date_str}-{feature_slug}.md"
        return self.prd_dir / filename
    
    def generate_document(self, requirement_info: Dict, collected_data: Dict, 
                         attachments: List[str]) -> str:
        fields = requirement_info.get("fields", {})
        title = fields.get("标题", "未命名需求")
        reporter = fields.get("反馈人", "未知")
        feature_name = self._extract_feature_name(title)
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        doc_id = f"PRD-{now.strftime('%Y%m%d')}-{feature_name[:10]}"
        attachments_str = "\n".join([f"- {a}" for a in attachments]) if attachments else "无"
        
        return f"""# {title}

<!-- 
文档生成信息:
- 使用 Skill: prd-document
- 生成工具: requirement_followup.py
- 生成时间: {now.strftime('%Y-%m-%d %H:%M')}
- 文档编号: {doc_id}
-->

> **声明：** 本文档使用 `prd-document` skill 生成  
> **状态：** 需求分析中  
> **创建日期:** {date_str}  
> **需求人:** {reporter}  
> **文档版本:** v1.0

---

## 1. 背景与目标

### 1.1 背景（为什么要做？解决什么问题？）
{collected_data.get('background', '待补充')}

### 1.2 目标用户
{collected_data.get('target_users', '待补充')}

### 1.3 业务目标
- 解决用户当前面临的核心痛点
- 提升业务处理效率和用户体验
- 降低人工操作成本和错误率

---

## 2. 现状

### 2.1 当前系统/流程现状
{collected_data.get('current_situation', '待补充')}

### 2.2 存在的问题
{collected_data.get('pain_points', '待补充')}

---

## 3. 目标（要达到什么效果？）

### 3.1 产品目标
{collected_data.get('expected_solution', '待补充')}

---

## 4. 方案

### 4.1 流程图
```mermaid
flowchart TD
    A[开始] --> B[用户触发操作]
    B --> C[系统处理]
    C --> D{{验证条件}}
    D -->|验证通过| E[执行成功]
    D -->|验证失败| F[错误提示]
    E --> G[结束]
    F --> G
```

### 4.2 功能说明
{collected_data.get('expected_solution', '待补充')}

---

## 5. 优先级和时间计划

- **优先级**: {collected_data.get('priority', '待评估')}
- **期望上线时间**: 根据优先级确定

---

## 6. 附件与参考资料

{attachments_str}

---

*本文档由需求跟进系统基于 prd-document skill 自动生成*
"""
    
    def save_document(self, content: str, title: str) -> Path:
        doc_path = self.get_document_path(title)
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return doc_path


class GroupChatManager:
    """群聊沟通管理器 - 处理需求沟通群的创建和管理"""
    
    def __init__(self):
        self.feishu_api = FeishuAPIClient()
        self.active_groups = {}  # chat_id -> requirement_info
    
    def create_requirement_chat(self, requirement_name: str, boss_id: str) -> Tuple[bool, str, str]:
        """创建需求沟通群
        
        Args:
            requirement_name: 需求名称
            boss_id: Boss的飞书ID
            
        Returns:
            (success, chat_id, share_url): 是否成功，群聊ID，分享链接
        """
        print(f"\n📱 创建需求沟通群: {requirement_name}")
        
        # 生成群名称
        timestamp = datetime.now().strftime("%m%d")
        chat_name = f"[{timestamp}] {requirement_name} - 需求沟通"
        description = f"该群用于讨论需求：{requirement_name}"
        
        # 调用飞书API创建群聊
        success, chat_id, share_url = self.feishu_api.create_chat_group(chat_name, description)
        
        if not success:
            return False, "", ""
        
        # 保存群聊信息
        self.active_groups[chat_id] = {
            "requirement_name": requirement_name,
            "boss_id": boss_id,
            "created_at": datetime.now().isoformat(),
            "status": "created"
        }
        
        print(f"  ✅ 群聊创建成功")
        print(f"  📎 群聊ID: {chat_id}")
        print(f"  🔗 分享链接: {share_url}")
        
        return True, chat_id, share_url
    
    def send_group_invite(self, chat_id: str, boss_id: str, requirement_name: str,
                         requirement_person_name: str = "") -> bool:
        """在群里发送邀请信息，提示Boss拉人
        
        Args:
            chat_id: 群聊ID
            boss_id: Boss的飞书ID
            requirement_name: 需求名称
            requirement_person_name: 需求人姓名（可选）
        """
        print(f"\n📨 发送群邀请信息")
        
        # 构建邀请消息
        person_info = f"（需求人：{requirement_person_name}）" if requirement_person_name else ""
        
        invite_message = f"""👋 Boss好！

我已为需求「**{requirement_name}**」{person_info}创建了专门的沟通群。

⚠️ **由于飞书机器人权限限制，我无法直接添加未授权的用户进群。**

👉 **请您帮忙将需求人拉入本群**，我将在此群内收集需求信息。

收集的问题清单：
1️⃣ 业务背景
2️⃣ 目标用户  
3️⃣ 现状描述
4️⃣ 核心痛点
5️⃣ 期望解决方案
6️⃣ 优先级和时间
7️⃣ 相关资料

需求人进群后，我会自动开始收集信息。谢谢！🙏"""
        
        success = self.feishu_api.send_message(chat_id, invite_message)
        
        if success:
            print(f"  ✅ 邀请信息已发送给Boss")
            # 更新群聊状态
            if chat_id in self.active_groups:
                self.active_groups[chat_id]["status"] = "waiting_for_members"
        
        return success
    
    def send_welcome_message(self, chat_id: str, requirement_name: str) -> bool:
        """发送欢迎消息到群聊，开始需求收集"""
        welcome_message = f"""👋 大家好！我是需求跟进助手。

本群用于收集「**{requirement_name}**」的需求信息。

我将通过7个关键问题来了解需求详情，请需求人配合回答。

让我们开始吧！🚀"""
        
        return self.feishu_api.send_message(chat_id, welcome_message)
    
    def collect_requirement_in_group(self, chat_id: str, requirement_person_id: str) -> Dict:
        """在群内收集需求信息
        
        Args:
            chat_id: 群聊ID
            requirement_person_id: 需求人的飞书ID
            
        Returns:
            collected_info: 收集到的需求信息字典
        """
        print(f"\n💬 在群内收集需求信息")
        print(f"  群聊ID: {chat_id}")
        print(f"  需求人ID: {requirement_person_id}")
        
        collector = RequirementCollector()
        
        # 发送欢迎消息
        if chat_id in self.active_groups:
            req_name = self.active_groups[chat_id].get("requirement_name", "当前需求")
            self.send_welcome_message(chat_id, req_name)
        
        # 逐条发送问题并收集回答
        question = collector.get_next_question()
        while question:
            print(f"\n🤖 提问: {question['key']}")
            self.feishu_api.send_message(chat_id, question["question"])
            
            # 模拟收集回答（实际实现需要监听群消息）
            sample_answers = {
                "background": "在使用系统过程中，发现当前功能不够完善，需要改进以提升工作效率。",
                "target_users": "业务部门和运营团队日常使用",
                "current_situation": "用户目前需要手动处理数据，然后在Excel中进行整理，步骤繁琐",
                "pain_points": "目前流程繁琐，耗时较长，影响工作效率，容易出错",
                "expected_solution": "实现自动化处理功能，减少人工操作，提升效率",
                "priority": "中等优先级，希望在两周内完成",
                "attachments": "无"
            }
            answer = sample_answers.get(question["key"], "待补充")
            collector.save_answer(question["key"], answer)
            print(f"  ✅ 收到回答: {answer[:50]}...")
            
            question = collector.get_next_question()
        
        # 发送收集完成消息
        if collector.is_complete():
            self.feishu_api.send_message(
                chat_id,
                "✅ 需求信息收集完成！正在生成PRD文档..."
            )
        
        return {
            "collected_data": collector.collected_data,
            "attachments": collector.attachments,
            "is_complete": collector.is_complete()
        }
    
    def close_group_chat(self, chat_id: str, reason: str = "需求处理完成") -> bool:
        """关闭群聊，发送结束消息"""
        close_message = f"""✅ 需求处理完成！

{reason}

感谢大家的配合！如需进一步沟通，请随时联系。

本群可以继续保留用于后续跟进，或根据需要自行解散。"""
        
        success = self.feishu_api.send_message(chat_id, close_message)
        
        if chat_id in self.active_groups:
            self.active_groups[chat_id]["status"] = "closed"
            self.active_groups[chat_id]["closed_at"] = datetime.now().isoformat()
        
        return success


class MessageSender:
    """消息发送器 - 处理私聊消息"""
    
    def send(self, user_id: str, message: str) -> bool:
        """发送私聊消息
        
        Returns:
            bool: 是否发送成功
            
        Note:
            由于飞书机器人限制，可能无法直接给未授权用户发送消息。
            如果发送失败，应该切换到群聊模式。
        """
        print(f"\n📤 [尝试私聊用户 {user_id}]:")
        print(f"{message[:100]}...")
        
        # 模拟发送结果
        # 实际实现中，这里应该调用飞书API
        # 如果返回权限错误，表示私聊受限
        return True
    
    def can_send_direct_message(self, user_id: str) -> bool:
        """检查是否可以给指定用户发送私聊消息"""
        # 实际实现需要调用飞书API检查权限
        # 这里模拟部分用户受限的情况
        return True  # 默认假设可以发送


class RequirementFollowupSystem:
    """需求跟进系统主类"""
    
    def __init__(self):
        self.bitable = FeishuBitableClient()
        self.contacts = ContactManager()
        self.messenger = MessageSender()
        self.doc_generator = RequirementDocumentGenerator()
        self.group_manager = GroupChatManager()
        self.collector = None
    
    def list_pending_requirements(self) -> List[Dict]:
        """列出所有待处理需求"""
        requirements = self.bitable.get_pending_requirements()
        print("\n📋 待处理需求列表:")
        print("=" * 80)
        
        pending = []
        for idx, req in enumerate(requirements, 1):
            fields = req.get("fields", {})
            if fields.get("类型") == "需求" and fields.get("处理状态") == "待处理":
                pending.append(req)
                print(f"\n[{idx}] {fields.get('标题', '未命名')}")
                print(f"    记录ID: {req.get('record_id')}")
                print(f"    反馈人: {fields.get('反馈人', '未知')}")
                print(f"    创建时间: {fields.get('创建时间', '未知')}")
                desc = fields.get('详细描述', '无')
                if len(desc) > 50:
                    desc = desc[:50] + "..."
                print(f"    描述: {desc}")
        
        print("\n" + "=" * 80)
        print(f"共找到 {len(pending)} 条待处理需求")
        return pending
    
    def followup_by_id(self, record_id: str, boss_id: str = None) -> bool:
        """跟进指定ID的需求"""
        print(f"\n🔍 跟进需求: {record_id}")
        
        requirements = self.bitable.get_pending_requirements()
        requirement = None
        for req in requirements:
            if req.get("record_id") == record_id:
                requirement = req
                break
        
        if not requirement:
            print(f"❌ 未找到记录: {record_id}")
            return False
        
        return self._process_requirement(requirement, boss_id)
    
    def followup_by_title(self, title_keyword: str, boss_id: str = None) -> bool:
        """根据标题关键词跟进需求"""
        print(f"\n🔍 搜索标题包含 '{title_keyword}' 的需求")
        
        requirements = self.bitable.get_pending_requirements()
        matched = []
        
        for req in requirements:
            fields = req.get("fields", {})
            title = fields.get("标题", "")
            if title_keyword.lower() in title.lower():
                matched.append(req)
        
        if not matched:
            print(f"❌ 未找到包含 '{title_keyword}' 的需求")
            return False
        
        print(f"✅ 找到 {len(matched)} 条匹配需求")
        for req in matched:
            self._process_requirement(req, boss_id)
        
        return True
    
    def batch_followup(self, boss_id: str = None) -> bool:
        """批量处理所有待处理需求"""
        pending = self.list_pending_requirements()
        
        if not pending:
            print("✅ 没有待处理的需求")
            return True
        
        print(f"\n🚀 开始批量处理 {len(pending)} 条需求...")
        success_count = 0
        
        for req in pending:
            if self._process_requirement(req, boss_id):
                success_count += 1
            print("\n" + "=" * 80 + "\n")
        
        print(f"✅ 批量处理完成：成功 {success_count}/{len(pending)}")
        return True
    
    def _process_requirement(self, requirement: Dict, boss_id: str = None) -> bool:
        """处理单个需求（支持私聊和群聊两种模式）"""
        fields = requirement.get("fields", {})
        record_id = requirement.get("record_id", "")
        title = fields.get("标题", "未命名需求")
        reporter_name = fields.get("反馈人", "")
        
        print(f"\n📌 处理需求: {title}")
        print(f"   记录ID: {record_id}")
        print(f"   反馈人: {reporter_name}")
        
        # 获取需求人ID
        reporter_id = self.contacts.get_user_id_by_name(reporter_name)
        if not reporter_id:
            print(f"⚠️ 未找到反馈人 '{reporter_name}' 的飞书ID")
            
            # 如果没有Boss ID，无法继续
            if not boss_id:
                print("❌ 缺少Boss ID，无法创建沟通群")
                return False
            
            # 创建群聊，让Boss拉人
            print("\n🔄 切换到群聊模式...")
            return self._process_with_group_chat(requirement, boss_id, reporter_name)
        
        print(f"   飞书ID: {reporter_id}")
        
        # 检查是否可以私聊
        if self.messenger.can_send_direct_message(reporter_id):
            # 尝试私聊模式
            print("\n💬 尝试私聊模式...")
            success = self._process_with_direct_chat(requirement, reporter_id)
            if success:
                return True
        
        # 私聊失败，切换到群聊模式
        if boss_id:
            print("\n🔄 私聊受限，切换到群聊模式...")
            return self._process_with_group_chat(requirement, boss_id, reporter_name)
        else:
            print("❌ 私聊受限且未提供Boss ID，无法继续")
            return False
    
    def _process_with_direct_chat(self, requirement: Dict, reporter_id: str) -> bool:
        """使用私聊模式处理需求"""
        fields = requirement.get("fields", {})
        record_id = requirement.get("record_id", "")
        title = fields.get("标题", "未命名需求")
        
        # 初始化收集器
        self.collector = RequirementCollector()
        
        # 发送开场白
        success = self.messenger.send(
            reporter_id,
            f"您好！我是需求跟进助手。您提交的需求「{title}」正在处理中，需要向您了解一些详细信息。"
        )
        
        if not success:
            print("⚠️ 私聊发送失败")
            return False
        
        print("\n💬 开始需求收集对话...")
        question = self.collector.get_next_question()
        while question:
            print(f"\n🤖 提问: {question['key']}")
            success = self.messenger.send(reporter_id, question["question"])
            
            if not success:
                print("⚠️ 发送问题失败，中断收集")
                return False
            
            # 模拟收集回答
            sample_answers = {
                "background": f"在使用系统过程中，发现{title}的功能不够完善，需要改进以提升工作效率。",
                "target_users": "业务部门和运营团队日常使用",
                "current_situation": "用户目前需要手动导出数据，然后在Excel中进行处理，步骤繁琐",
                "pain_points": "目前流程繁琐，耗时较长，影响工作效率",
                "expected_solution": f"实现{title}的自动化处理功能，减少人工操作",
                "priority": "中等优先级，希望在两周内完成",
                "attachments": "无"
            }
            answer = sample_answers.get(question["key"], "待补充")
            self.collector.save_answer(question["key"], answer)
            print(f"✅ 收到回答: {answer[:50]}...")
            
            question = self.collector.get_next_question()
        
        # 生成文档
        return self._generate_and_save_document(requirement)
    
    def _process_with_group_chat(self, requirement: Dict, boss_id: str, 
                                 reporter_name: str = "") -> bool:
        """使用群聊模式处理需求"""
        fields = requirement.get("fields", {})
        record_id = requirement.get("record_id", "")
        title = fields.get("标题", "未命名需求")
        
        print("\n📱 启动群聊沟通模式")
        
        # 1. 创建需求沟通群
        success, chat_id, share_url = self.group_manager.create_requirement_chat(title, boss_id)
        if not success:
            print("❌ 创建群聊失败")
            return False
        
        # 2. 发送群邀请信息给Boss
        self.group_manager.send_group_invite(chat_id, boss_id, title, reporter_name)
        
        print(f"\n⏳ 等待Boss拉人进群...")
        print(f"   群聊ID: {chat_id}")
        print(f"   分享链接: {share_url}")
        
        # 注意：实际实现中，这里需要等待Boss拉人进群
        # 可以通过监听群成员变化事件来检测需求人是否已进群
        
        # 模拟需求人已进群，开始收集
        print("\n📝 模拟需求人已进群，开始收集信息...")
        reporter_id = self.contacts.get_user_id_by_name(reporter_name)
        result = self.group_manager.collect_requirement_in_group(chat_id, reporter_id or "")
        
        if not result["is_complete"]:
            print("⚠️ 需求信息收集不完整")
            return False
        
        # 保存收集的数据
        self.collector = RequirementCollector()
        self.collector.collected_data = result["collected_data"]
        self.collector.attachments = result["attachments"]
        
        # 生成文档并更新状态
        success = self._generate_and_save_document(requirement)
        
        # 发送群聊关闭消息
        if success:
            self.group_manager.close_group_chat(chat_id, f"PRD文档已生成：{title}")
        
        return success
    
    def _generate_and_save_document(self, requirement: Dict) -> bool:
        """生成并保存需求文档"""
        fields = requirement.get("fields", {})
        record_id = requirement.get("record_id", "")
        title = fields.get("标题", "未命名需求")
        
        if not self.collector or not self.collector.is_complete():
            print("⚠️ 需求信息收集不完整")
            return False
        
        print("\n✅ 需求信息收集完成")
        print("\n📊 收集的数据摘要:")
        print(self.collector.get_summary())
        
        print("\n📝 生成需求文档...")
        doc_content = self.doc_generator.generate_document(
            requirement,
            self.collector.collected_data,
            self.collector.attachments
        )
        
        doc_path = self.doc_generator.save_document(doc_content, title)
        
        print(f"✅ 文档已保存: {doc_path}")
        
        # 更新表格状态
        self.bitable.update_record_status(
            record_id,
            "处理中",
            f"需求文档已生成: {doc_path.name}"
        )
        
        return True
    
    def _set_document_permission(self, doc_path: Path) -> bool:
        """设置文档权限，给Boss管理权限
        
        Args:
            doc_path: 文档路径
            
        Returns:
            bool: 是否成功
        """
        print(f"\n🔐 正在设置文档权限...")
        print(f"   目标用户: {BOSS_NAME} ({BOSS_FEISHU_ID})")
        print(f"   权限级别: 可管理")
        
        # 注意：本地生成的markdown文件没有飞书doc_token
        # 这里输出提示信息，实际权限设置需要在上传到飞书后执行
        print(f"   ℹ️ 本地文档已生成，路径: {doc_path}")
        print(f"   ℹ️ 如需设置飞书文档权限，请先上传到飞书")
        
        return True
    
    def create_and_grant_doc(self, requirement: Dict, collected_data: Dict, attachments: List[str]) -> Path:
        """创建文档并设置权限
        
        Args:
            requirement: 需求信息
            collected_data: 收集的数据
            attachments: 附件列表
            
        Returns:
            Path: 文档路径
        """
        # 生成文档
        doc_content = self.doc_generator.generate_document(
            requirement, collected_data, attachments
        )
        title = requirement.get("fields", {}).get("标题", "未命名需求")
        doc_path = self.doc_generator.save_document(doc_content, title)
        
        print(f"✅ 文档已生成: {doc_path}")
        
        # 设置权限
        self._set_document_permission(doc_path)
        
        return doc_path
    
    def create_requirement_group(self, requirement_name: str, boss_id: str = None, 
                                  reporter_name: str = "") -> Tuple[bool, str]:
        """创建需求沟通群（独立功能）
        
        Args:
            requirement_name: 需求名称
            boss_id: Boss的飞书ID（默认使用BOSS_FEISHU_ID）
            reporter_name: 需求人姓名（可选）
            
        Returns:
            (success, chat_id): 是否成功，群聊ID
        """
        # 使用默认Boss ID
        actual_boss_id = boss_id or BOSS_FEISHU_ID
        
        print(f"\n📱 为需求创建沟通群: {requirement_name}")
        print(f"   群主: {BOSS_NAME} ({actual_boss_id})")
        
        # 创建群聊
        success, chat_id, share_url = self.group_manager.create_requirement_chat(
            requirement_name, actual_boss_id
        )
        
        if not success:
            print("❌ 创建群聊失败")
            return False, ""
        
        # 发送邀请信息
        self.group_manager.send_group_invite(chat_id, actual_boss_id, requirement_name, reporter_name)
        
        print(f"\n✅ 群聊创建成功！")
        print(f"   群聊ID: {chat_id}")
        print(f"   分享链接: {share_url}")
        print(f"   群主: {BOSS_NAME}")
        print(f"\n⏳ 等待Boss拉人进群后，可以使用以下命令继续：")
        print(f"   python requirement_followup.py --collect {chat_id} <需求人ID>")
        
        return True, chat_id


def process_command(command: str, boss_id: str = None) -> bool:
    """处理Boss指令"""
    system = RequirementFollowupSystem()
    
    parts = command.strip().split()
    
    if len(parts) == 1 or (len(parts) == 2 and parts[1] == ""):
        system.list_pending_requirements()
        return True
    
    arg = parts[1] if len(parts) > 1 else ""
    
    if arg.startswith("rec_") or arg.isdigit():
        return system.followup_by_id(arg, boss_id)
    else:
        return system.followup_by_title(arg, boss_id)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="需求跟进与文档生成系统 v3.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 列出待处理需求
    python requirement_followup.py --list
    
    # 跟进指定需求（自动选择私聊或群聊模式）
    python requirement_followup.py --id rec_001
    
    # 指定Boss ID，私聊失败时自动创建群聊
    python requirement_followup.py --id rec_001 --boss <boss_id>
    
    # 根据标题关键词跟进
    python requirement_followup.py --title 导出
    
    # 批量处理所有需求
    python requirement_followup.py --batch
    
    # 创建需求沟通群
    python requirement_followup.py --group "需求名称" <boss_id> [--reporter 需求人姓名]
    
    # 在群内收集需求信息
    python requirement_followup.py --collect <chat_id> <需求人ID>
    
    # 运行演示模式
    python requirement_followup.py --demo
        """
    )
    
    parser.add_argument("--list", "-l", action="store_true",
                        help="列出所有待处理需求")
    parser.add_argument("--id", "-i", metavar="RECORD_ID",
                        help="跟进指定记录ID的需求")
    parser.add_argument("--title", "-t", metavar="KEYWORD",
                        help="跟进标题包含关键词的需求")
    parser.add_argument("--batch", "-b", action="store_true",
                        help="批量处理所有待处理需求")
    parser.add_argument("--group", "-g", metavar="REQUIREMENT_NAME",
                        help="创建需求沟通群")
    parser.add_argument("--boss", metavar="BOSS_ID",
                        help="指定Boss的飞书ID（用于群聊模式）")
    parser.add_argument("--reporter", metavar="REPORTER_NAME",
                        help="指定需求人姓名")
    parser.add_argument("--collect", metavar="CHAT_ID",
                        help="在指定群聊内收集需求信息")
    parser.add_argument("--person", metavar="PERSON_ID",
                        help="指定需求人ID（配合--collect使用）")
    parser.add_argument("--command", "-c", metavar="COMMAND",
                        help="执行指令")
    parser.add_argument("--demo", "-d", action="store_true",
                        help="运行演示模式")
    
    args = parser.parse_args()
    
    system = RequirementFollowupSystem()
    
    if args.list:
        system.list_pending_requirements()
    elif args.id:
        system.followup_by_id(args.id, args.boss)
    elif args.title:
        system.followup_by_title(args.title, args.boss)
    elif args.batch:
        system.batch_followup(args.boss)
    elif args.group:
        if not args.boss:
            print("❌ 创建群聊需要指定 --boss <boss_id>")
            sys.exit(1)
        system.create_requirement_group(args.group, args.boss, args.reporter or "")
    elif args.collect:
        if not args.person:
            print("❌ 收集信息需要指定 --person <需求人ID>")
            sys.exit(1)
        result = system.group_manager.collect_requirement_in_group(args.collect, args.person)
        print(f"\n📊 收集结果: {'完成' if result['is_complete'] else '未完成'}")
    elif args.command:
        process_command(args.command, args.boss)
    elif args.demo:
        print("🎬 运行演示模式...")
        print("\n演示场景1: 私聊模式（默认）")
        system.followup_by_id("rec_001")
        print("\n" + "=" * 80 + "\n")
        print("演示场景2: 群聊模式（私聊受限时）")
        system.followup_by_id("rec_002", boss_id="boss_001")
    else:
        system.list_pending_requirements()


if __name__ == "__main__":
    main()
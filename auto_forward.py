#!/usr/bin/env python3
"""
飞书反馈自动转发脚本
整合功能：转发消息 + 记录表格 + 消息链接（图片无法下载时）
"""

import json
import os
import sys
import tempfile
import time
import requests
import re
from typing import Optional
from datetime import datetime, timedelta

# 配置
OPENCLAW_CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")
BITABLE_CONFIG = "/home/admin/openclaw/workspace/.feishu_bitable_config.json"

# 多配置映射表：根据 source_chat_id 决定 target_chat_id 和 handlers
# 配置1: 产研-融合业务组 → 猛龙队开发
# 配置2: 号卡&宽带 → 猛龙队开发
# 配置3: 线下号卡 → 猛龙队开发
# 配置4: 号卡能力中心信息同频群 → oc_cf3c4adafb332df5988b20204c272dbb
# 配置5: 待补充 → 猛龙队开发
FORWARD_CONFIGS = {
    # 配置1: 产研-融合业务组
    "oc_469678cc3cd264438f9bbb65da534c0b": {
        "target_chat_id": "oc_a016323a9fda4263ab5a27976065088e",
        "handlers": [
            {"user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "施嘉科"},
            {"user_id": "ou_cbcd1090961b620a4500ce68e3c81952", "user_name": "宋广智"}
        ],
        "source_name": "产研-融合业务组"
    },
    # 配置2: 号卡&宽带需求和酬金系统体系搭建
    "oc_3b4215cdadcc9366c863377561ce00c5": {
        "target_chat_id": "oc_a016323a9fda4263ab5a27976065088e",
        "handlers": [
            {"user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "施嘉科"},
            {"user_id": "ou_cbcd1090961b620a4500ce68e3c81952", "user_name": "宋广智"}
        ],
        "source_name": "号卡&宽带需求和酬金系统体系搭建"
    },
    # 配置3: 线下号卡-信息流投放上报沟通
    "oc_ee55ec5275cc158b826fe1204d75cf2c": {
        "target_chat_id": "oc_a016323a9fda4263ab5a27976065088e",
        "handlers": [
            {"user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "施嘉科"}
        ],
        "source_name": "线下号卡-信息流投放上报沟通"
    },
    # 配置4: 号卡能力中心信息同频群
    "oc_5bf7336955740fb41ba59e4e929c5239": {
        "target_chat_id": "oc_cf3c4adafb332df5988b20204c272dbb",
        "handlers": [
            {"user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "施嘉科"},
            {"user_id": "ou_834914563c797190697ca36b074a6952", "user_name": "郑武友"},
            {"user_id": "ou_3e48baef1bd71cc89fb5a364be55cafc", "user_name": "陈俊洪"}
        ],
        "source_name": "号卡能力中心信息同频群"
    },
    # 配置5: 待补充（新来源群）
    "oc_81299c457f97b260b13a8469bb187c8e": {
        "target_chat_id": "oc_a016323a9fda4263ab5a27976065088e",
        "handlers": [
            {"user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "施嘉科"},
            {"user_id": "ou_e0b3221ff687bea25dd88257dbbb30d4", "user_name": "李川平"},
            {"user_id": "ou_d68b02946c960929136849be2c8be50f", "user_name": "王凯明"}
        ],
        "source_name": "待补充"
    }
}

# 兼容旧代码：默认配置（配置1）
TARGET_CHAT_ID = "oc_a016323a9fda4263ab5a27976065088e"
HANDLER_USERS = [
    {"user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "施嘉科"},
    {"user_id": "ou_cbcd1090961b620a4500ce68e3c81952", "user_name": "宋广智"}
]

def load_feishu_creds():
    """加载飞书凭证"""
    try:
        with open(OPENCLAW_CONFIG, 'r') as f:
            config = json.load(f)
            feishu_config = config.get('channels', {}).get('feishu', {})
            return feishu_config.get('appId'), feishu_config.get('appSecret')
    except Exception as e:
        print(f"❌ 加载配置失败: {e}")
        return None, None

def get_tenant_access_token(app_id, app_secret):
    """获取 tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": app_id, "app_secret": app_secret})
    data = resp.json()
    if data.get('code') != 0:
        raise Exception(f"获取 token 失败: {data}")
    return data.get('tenant_access_token')

def download_image(image_key, token):
    """下载图片"""
    url = f"https://open.feishu.cn/open-apis/im/v1/images/{image_key}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, stream=True)
    
    if resp.status_code != 200:
        raise Exception(f"下载失败: {resp.status_code}")
    
    suffix = ".png"
    content_type = resp.headers.get('content-type', '')
    if 'jpeg' in content_type or 'jpg' in content_type:
        suffix = ".jpg"
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    for chunk in resp.iter_content(chunk_size=8192):
        if chunk:
            temp_file.write(chunk)
    temp_file.close()
    return temp_file.name

def upload_image(image_path, token):
    """上传图片到飞书"""
    url = "https://open.feishu.cn/open-apis/im/v1/images"
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(image_path, 'rb') as f:
        files = {'image': f}
        data = {'image_type': 'message'}
        resp = requests.post(url, headers=headers, files=files, data=data)
    
    result = resp.json()
    if result.get('code') != 0:
        raise Exception(f"上传失败: {result}")
    return result['data']['image_key']

def send_forward_message(token, chat_id, title, content, image_key=None, message_link=None, at_list=None, source_name=None, message_type=None, problem_content=None, original_message_id=None):
    """发送转发消息"""
    # 构造内容块
    content_blocks = []

    # 正文（反馈人信息）- 按行拆分，确保换行生效
    if content:
        lines = content.split('\n')
        for line in lines:
            content_blocks.append([{"tag": "text", "text": line}])

    # 📌 问题类型
    if message_type:
        content_blocks.append([{"tag": "text", "text": ""}])  # 空行
        content_blocks.append([
            {"tag": "text", "text": "📌 问题类型：", "style": {"bold": True}},
            {"tag": "text", "text": message_type}
        ])

    # 📍 来源群
    if source_name:
        content_blocks.append([
            {"tag": "text", "text": "📍 来源群：", "style": {"bold": True}},
            {"tag": "text", "text": source_name}
        ])

    # 🔗 原始消息（添加消息ID和链接）
    if original_message_id:
        content_blocks.append([{"tag": "text", "text": ""}])  # 空行
        content_blocks.append([
            {"tag": "text", "text": "🔗 原始消息：", "style": {"bold": True}}
        ])
        # 添加可点击的消息链接
        msg_url = f"https://applink.feishu.cn/client/message/open?message_id={original_message_id}"
        content_blocks.append([{
            "tag": "a",
            "text": f"点击查看原消息 ({original_message_id[:15]}...)",
            "href": msg_url
        }])
    
    # 问题描述
    if problem_content:
        content_blocks.append([{"tag": "text", "text": ""}])  # 空行
        content_blocks.append([{"tag": "text", "text": "问题描述："}])
        # 按行拆分，确保换行生效
        prob_lines = problem_content.split('\n')
        for line in prob_lines:
            content_blocks.append([{"tag": "text", "text": line}])
    
    # 图片
    if image_key:
        content_blocks.append([{"tag": "img", "image_key": image_key}])
    
    # 消息链接（图片无法下载时）
    if message_link and not image_key:
        content_blocks.append([{"tag": "text", "text": ""}])
        content_blocks.append([{"tag": "text", "text": "📎 原消息包含图片，点击查看："}])
        content_blocks.append([{
            "tag": "a",
            "text": "点击查看原消息和图片",
            "href": message_link
        }])
    
    # @人员
    if at_list:
        content_blocks.append([{"tag": "text", "text": ""}])
        at_para = []
        for i, at in enumerate(at_list):
            if i > 0:
                at_para.append({"tag": "text", "text": " "})
            # 确保 user_name 不为空，否则@不会高亮
            user_name = at.get("user_name", "").strip()
            user_id = at.get("user_id", "").strip()
            if not user_name:
                # 如果user_name为空，尝试从contacts查找
                user_name = "同事"  # 默认名称
            if user_id:  # 只添加有user_id的@
                at_para.append({
                    "tag": "at",
                    "user_id": user_id,
                    "user_name": user_name
                })
        at_para.append({"tag": "text", "text": " 请查看~"})
        content_blocks.append(at_para)
    
    # 发送
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
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
    
    # 调试日志：打印实际发送的消息内容
    print(f"📤 [DEBUG] 实际发送的消息内容:")
    print(f"   msg_type: {payload['msg_type']}")
    print(f"   receive_id: {chat_id}")
    print(f"   content JSON: {payload['content'][:500]}...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    resp = requests.post(url, json=payload, headers=headers)
    
    # 调试日志：打印API响应
    print(f"📥 [DEBUG] API响应: {resp.json()}")
    
    return resp.json()

def record_to_bitable(token, app_token, table_id, fields):
    """记录到多维表格"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 🛡️ 防御性检查：确保反馈时间有效
    feedback_time = fields.get("反馈时间")
    if feedback_time is None or feedback_time == 0 or feedback_time == "":
        import time
        fallback_timestamp = int(time.time() * 1000)
        print(f"⚠️ [Bitable] 反馈时间为空或无效({feedback_time})，使用当前时间戳: {fallback_timestamp}")
        fields["反馈时间"] = fallback_timestamp

    # 🛡️ 防御性检查：确保反馈来源不为 null
    if not fields.get("反馈来源"):
        fields["反馈来源"] = fields.get("来源群", "其他")
        print(f"⚠️ [Bitable] 反馈来源为空，使用默认值: {fields['反馈来源']}")

    payload = {"fields": fields}

    # 调试：打印请求数据（隐藏敏感信息）
    debug_fields = {k: v for k, v in fields.items() if k != "问题内容"}
    print(f"📝 [Bitable] 创建记录字段: {debug_fields}")

    resp = requests.post(url, json=payload, headers=headers)
    result = resp.json()

    # 调试：打印响应
    if result.get('code') != 0:
        print(f"❌ [Bitable] API 错误: code={result.get('code')}, msg={result.get('msg')}")
        print(f"❌ [Bitable] 错误详情: {result}")
    else:
        record_id = result.get('data', {}).get('record', {}).get('record_id')
        print(f"✅ [Bitable] 记录创建成功: {record_id}")

    return result

def is_requirement_request(content: str) -> bool:
    """判断是否是需求跟进请求"""
    keywords = ["跟进这个需求", "跟进需求", "记录这个需求", 
                "需求调研", "产品需求", "功能需求", "新需求"]
    content_lower = content.lower()
    return any(kw in content for kw in keywords)

def extract_keywords(content: str) -> dict:
    """
    从问题内容中提取关键词
    
    Args:
        content: 问题内容
    
    Returns:
        dict: 包含提取的关键词，如订单号、产品名、地名等
    """
    keywords = {
        "order_ids": [],
        "product_names": [],
        "locations": [],
        "phone_numbers": [],
        "other_keywords": []
    }
    
    # 1. 提取订单号 (CC2026 开头 或 类似格式)
    order_patterns = [
        r'CC2026\w+',
        r'订单[号码]?[\s:：]*([A-Za-z0-9]+)',
        r'订单[\s:：]*([A-Za-z0-9]+)',
    ]
    for pattern in order_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        keywords["order_ids"].extend(matches)
    
    # 2. 提取产品/业务关键词
    product_keywords = [
        "俊子云", "广州电信", "杭州电信", "电信", "联通", "移动",
        "号卡", "宽带", "酬金", "融合", "黑名单", "接口", "投放",
        "信息流", "钉钉", "企微", "企业微信"
    ]
    for keyword in product_keywords:
        if keyword in content:
            keywords["product_names"].append(keyword)
    
    # 3. 提取地点关键词
    location_patterns = [
        r'(广州|杭州|深圳|北京|上海|成都|武汉|西安)[电信联通移动]*',
    ]
    for pattern in location_patterns:
        matches = re.findall(pattern, content)
        keywords["locations"].extend(matches)
    
    # 4. 提取手机号 (可选)
    phone_pattern = r'1[3-9]\d{9}'
    phone_matches = re.findall(phone_pattern, content)
    keywords["phone_numbers"] = phone_matches
    
    return keywords


def calculate_similarity(content1: str, content2: str, keywords1: dict = None, keywords2: dict = None) -> float:
    """
    计算两个问题内容的相似度
    
    Args:
        content1: 第一个问题内容
        content2: 第二个问题内容
        keywords1: 第一个内容的关键词（可选）
        keywords2: 第二个内容的关键词（可选）
    
    Returns:
        float: 相似度分数 (0-1)
    """
    # 如果没有提供关键词，则提取
    if keywords1 is None:
        keywords1 = extract_keywords(content1)
    if keywords2 is None:
        keywords2 = extract_keywords(content2)
    
    # 1. 订单号匹配 - 100% 相似度
    if keywords1["order_ids"] and keywords2["order_ids"]:
        set1 = set(k.upper() for k in keywords1["order_ids"])
        set2 = set(k.upper() for k in keywords2["order_ids"])
        if set1 & set2:  # 有共同订单号
            return 1.0
    
    # 2. 手机号匹配 - 100% 相似度
    if keywords1["phone_numbers"] and keywords2["phone_numbers"]:
        set1 = set(keywords1["phone_numbers"])
        set2 = set(keywords2["phone_numbers"])
        if set1 & set2:
            return 1.0
    
    # 3. 关键词匹配评分
    score = 0.0
    total_weight = 0.0
    
    # 产品关键词权重最高
    product_weight = 0.5
    if keywords1["product_names"] or keywords2["product_names"]:
        set1 = set(keywords1["product_names"])
        set2 = set(keywords2["product_names"])
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        if union > 0:
            score += (intersection / union) * product_weight
        total_weight += product_weight
    
    # 地点关键词
    location_weight = 0.3
    if keywords1["locations"] or keywords2["locations"]:
        set1 = set(keywords1["locations"])
        set2 = set(keywords2["locations"])
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        if union > 0:
            score += (intersection / union) * location_weight
        total_weight += location_weight
    
    # 文本相似度（简单实现：共同子串比例）
    text_weight = 0.2
    content1_clean = re.sub(r'\s+', '', content1)
    content2_clean = re.sub(r'\s+', '', content2)
    
    # 计算最长公共子串长度
    if len(content1_clean) > 0 and len(content2_clean) > 0:
        # 简化：计算共同字符比例
        set1_chars = set(content1_clean)
        set2_chars = set(content2_clean)
        char_intersection = len(set1_chars & set2_chars)
        char_union = len(set1_chars | set2_chars)
        if char_union > 0:
            char_similarity = char_intersection / char_union
            score += char_similarity * text_weight
        total_weight += text_weight
    
    # 归一化
    if total_weight > 0:
        final_score = score / total_weight
    else:
        final_score = 0.0
    
    return final_score


def find_similar_record(content: str, table_id: str, token: str, app_token: str, days: int = 7, similarity_threshold: float = 0.6) -> Optional[str]:
    """
    搜索相似记录
    
    Args:
        content: 新问题内容
        table_id: Bitable表ID
        token: 飞书token
        app_token: Bitable app token
        days: 搜索最近几天的记录（默认7天）
        similarity_threshold: 相似度阈值（默认0.6）
    
    Returns:
        相似记录的ID，如果没有则返回None
    """
    try:
        # 计算时间范围
        end_time = int(time.time() * 1000)
        start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        
        # 构建查询条件：最近N天且状态为"待处理"或"处理中"
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 提取新内容的关键词
        new_keywords = extract_keywords(content)
        
        # 分页查询记录
        page_token = None
        all_records = []
        
        while True:
            params = {
                "page_size": 500,
                "filter": f'AND(CurrentValue.[反馈时间] >= {start_time}, CurrentValue.[反馈时间] <= {end_time}, OR(CurrentValue.[处理状态] = "待处理", CurrentValue.[处理状态] = "处理中"))'
            }
            if page_token:
                params["page_token"] = page_token
            
            resp = requests.get(url, headers=headers, params=params)
            data = resp.json()
            
            if data.get('code') != 0:
                print(f"⚠️ 查询记录失败: {data}")
                return None
            
            records = data.get('data', {}).get('items', [])
            all_records.extend(records)
            
            has_more = data.get('data', {}).get('has_more', False)
            page_token = data.get('data', {}).get('page_token')
            
            if not has_more or not page_token:
                break
        
        # 遍历记录，计算相似度
        best_match = None
        best_score = 0.0
        
        for record in records:
            record_id = record.get('record_id')
            fields = record.get('fields', {})
            
            # 获取问题内容字段
            record_content = fields.get('问题内容', '')
            if not record_content:
                record_content = fields.get('业务反馈问题记录表', '')
            
            if not record_content:
                continue
            
            # 计算相似度
            similarity = calculate_similarity(content, record_content, new_keywords)
            
            if similarity > best_score:
                best_score = similarity
                best_match = record_id
        
        # 如果最佳匹配超过阈值，返回记录ID
        if best_score >= similarity_threshold:
            print(f"🔍 找到相似记录: {best_match}, 相似度: {best_score:.2%}")
            return best_match
        
        return None
        
    except Exception as e:
        print(f"⚠️ 搜索相似记录时出错: {e}")
        return None


def update_record_with_supplement(record_id: str, new_content: str, new_reporter: str, token: str, app_token: str, table_id: str, source_chat: str = None):
    """
    更新原记录，追加补充信息
    关键：保留原始反馈时间；但如果原时间为 null，则设置当前时间

    Args:
        record_id: 原记录ID
        new_content: 新的问题内容
        new_reporter: 新的反馈人
        token: 飞书token
        app_token: Bitable app token
        table_id: Bitable表ID
        source_chat: 来源群（可选）
    """
    try:
        # 1. 获取原记录
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        resp = requests.get(url, headers=headers)
        data = resp.json()
        
        if data.get('code') != 0:
            print(f"⚠️ 获取原记录失败: {data}")
            return False
        
        fields = data.get('data', {}).get('record', {}).get('fields', {})

        # 2. 构建更新字段
        # ⚠️ 重要：通常保留原始反馈时间，但如果原时间为 null，则设置当前时间
        update_fields = {}

        # 🛡️ 防御性检查：如果原记录反馈时间为 null，设置当前时间
        original_feedback_time = fields.get('反馈时间')
        if original_feedback_time is None or original_feedback_time == 0:
            feedback_timestamp = int(time.time() * 1000)
            print(f"⚠️ 原记录反馈时间为空，设置当前时间戳: {feedback_timestamp}")
            update_fields['反馈时间'] = feedback_timestamp
        
        # 获取原问题内容
        original_content = fields.get('问题内容', '')
        if not original_content:
            original_content = fields.get('业务反馈问题记录表', '')
        
        # 更新问题内容：追加新内容
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        supplement_text = f"\n\n--- 补充 ({current_time}) ---\n{new_content}"
        updated_content = original_content + supplement_text
        update_fields['问题内容'] = updated_content
        
        # 更新业务反馈问题记录表字段（简要描述）
        update_fields['业务反馈问题记录表'] = updated_content[:100] + ("..." if len(updated_content) > 100 else "")
        
        # 更新反馈人：添加新反馈人
        original_reporter = fields.get('反馈人', '')
        if isinstance(original_reporter, str):
            if new_reporter not in original_reporter:
                updated_reporter = f"{original_reporter}, {new_reporter}"
                update_fields['反馈人'] = updated_reporter
        
        # 更新备注字段：记录补充时间和内容
        original_remark = fields.get('备注', '')
        # 格式：XX于2026-03-23 11:50补充：内容（截断显示）
        content_preview = new_content[:100] + "..." if len(new_content) > 100 else new_content
        supplement_remark = f"{new_reporter}于{current_time}补充：{content_preview}"
        if original_remark:
            updated_remark = f"{original_remark}\n---\n{supplement_remark}"
        else:
            updated_remark = supplement_remark
        update_fields['备注'] = updated_remark
        
        # 如果来源不同，也更新来源群
        if source_chat:
            original_source = fields.get('来源群', '')
            if isinstance(original_source, str) and source_chat not in original_source:
                updated_source = f"{original_source}, {source_chat}"
                update_fields['来源群'] = updated_source
            update_fields['反馈来源'] = source_chat
        else:
            # 🛡️ 防御性检查：确保反馈来源不为 null
            if not fields.get('反馈来源'):
                fallback_source = fields.get('来源群', '其他')
                update_fields['反馈来源'] = fallback_source
                print(f"⚠️ 原记录反馈来源为空，设置默认值: {fallback_source}")
        
        # 3. 发送更新请求
        update_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
        payload = {"fields": update_fields}
        
        update_resp = requests.put(update_url, headers=headers, json=payload)
        update_data = update_resp.json()
        
        if update_data.get('code') == 0:
            print(f"✅ 记录 {record_id} 更新成功")
            return True
        else:
            print(f"⚠️ 更新记录失败: {update_data}")
            return False
            
    except Exception as e:
        print(f"⚠️ 更新记录时出错: {e}")
        return False


def get_forward_config(source_chat_id):
    """
    根据来源群ID获取转发配置
    
    Args:
        source_chat_id: 来源群 chat_id
    
    Returns:
        dict: 配置信息，包含 target_chat_id, handlers, source_name
    """
    config = FORWARD_CONFIGS.get(source_chat_id)
    if config:
        # 过滤掉没有 user_id 的处理人（如郑武友待获取）
        handlers = [h for h in config["handlers"] if h.get("user_id")]
        return {
            "target_chat_id": config["target_chat_id"],
            "handlers": handlers,
            "source_name": config["source_name"]
        }
    # 默认返回配置1
    return {
        "target_chat_id": TARGET_CHAT_ID,
        "handlers": HANDLER_USERS,
        "source_name": "产研-融合业务组"
    }

def forward_feedback(source_chat, reporter, content, image_key=None, message_id=None, message_type="问题", source_chat_id=None, message_time=None):
    """
    转发反馈到目标群并记录到表格
    
    Args:
        source_chat: 来源群名称
        reporter: 反馈人
        content: 问题内容
        image_key: 图片 key（可选）
        message_id: 消息 ID（用于生成链接）
        message_type: 类型（问题/需求）
        source_chat_id: 来源群 chat_id（用于匹配配置）
        message_time: 消息时间戳（毫秒，可选。不传则使用当前时间）
    
    Returns:
        dict: 转发结果
    """
    # 检查是否是需求跟进请求，如果是则跳过让需求跟进流程处理
    if content and is_requirement_request(content):
        print(f"📝 检测到需求跟进请求，跳过问题转发: {content[:50]}...")
        return {"success": True, "skipped": True, "reason": "需求跟进请求"}
    
    # 加载凭证
    app_id, app_secret = load_feishu_creds()
    if not app_id or not app_secret:
        return {"success": False, "error": "无法加载飞书凭证"}
    
    token = get_tenant_access_token(app_id, app_secret)
    
    # 获取配置（根据 source_chat_id）
    config = get_forward_config(source_chat_id) if source_chat_id else {
        "target_chat_id": TARGET_CHAT_ID,
        "handlers": HANDLER_USERS,
        "source_name": source_chat
    }
    
    target_chat_id = config["target_chat_id"]
    handlers = config["handlers"]
    source_name = config["source_name"]
    
    print(f"📋 使用配置: {source_name} → 目标群: {target_chat_id}")
    print(f"👥 处理人: {[h['user_name'] for h in handlers]}")
    
    # 1. 处理图片
    new_image_key = None
    message_link = None
    temp_file = None
    
    if image_key:
        try:
            print(f"📥 尝试下载图片: {image_key}")
            temp_file = download_image(image_key, token)
            print(f"📤 上传图片到目标群...")
            new_image_key = upload_image(temp_file, token)
            print(f"✅ 图片转发成功")
        except Exception as e:
            print(f"⚠️ 图片下载失败: {e}")
            print(f"💡 将使用消息链接")
            if message_id:
                message_link = f"https://applink.feishu.cn/client/message/open?message_id={message_id}"
        finally:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
    
    # 2. 发送到目标群
    title = f"【产研反馈-{message_type}】"
    if image_key and not new_image_key:
        title += "（含消息链接）"
    
    try:
        result = send_forward_message(
            token=token,
            chat_id=target_chat_id,
            title=title,
            content=f"反馈人：{reporter}",
            image_key=new_image_key,
            message_link=message_link,
            at_list=handlers,
            source_name=source_name,
            message_type=message_type,
            problem_content=content,
            original_message_id=message_id
        )
        
        if result.get('code') != 0:
            return {"success": False, "error": f"发送消息失败: {result}"}
        
        print(f"✅ 已转发到目标群")
    except Exception as e:
        return {"success": False, "error": f"转发失败: {e}"}
    
    # 3. 记录到表格
    record_id = None
    try:
        if os.path.exists(BITABLE_CONFIG):
            with open(BITABLE_CONFIG, 'r') as f:
                bitable_config = json.load(f)
            
            app_token = bitable_config["app_token"]
            table_id = bitable_config["table_id"]
            
            # 3.1 先检查是否存在相似记录
            print(f"🔍 检查是否存在相似记录...")
            similar_record_id = find_similar_record(
                content=content,
                table_id=table_id,
                token=token,
                app_token=app_token,
                days=7,
                similarity_threshold=0.6
            )
            
            if similar_record_id:
                # 存在相似记录，更新原记录
                print(f"📝 发现相似记录 {similar_record_id}，将更新原记录追加补充信息")
                update_success = update_record_with_supplement(
                    record_id=similar_record_id,
                    new_content=content,
                    new_reporter=reporter,
                    token=token,
                    app_token=app_token,
                    table_id=table_id,
                    source_chat=source_name
                )
                if update_success:
                    print(f"✅ 已更新原记录 {similar_record_id}，追加补充信息")
                    record_id = similar_record_id
                else:
                    print(f"⚠️ 更新记录失败，尝试创建新记录...")
            
            if not record_id:
                # 不存在相似记录或更新失败，创建新记录
                # 构造时间戳：优先使用消息时间，其次使用当前时间
                if message_time and message_time > 0:
                    # 🛡️ 修复：正确识别时间戳单位（秒 vs 毫秒）
                    # 秒级时间戳约10位（如 1711536000）
                    # 毫秒级时间戳约13位（如 1711536000000）
                    if message_time < 10000000000:  # 10位以下是秒级
                        feedback_timestamp = int(message_time * 1000)
                        print(f"📝 传入秒级时间戳，转换为毫秒: {feedback_timestamp}")
                    else:
                        feedback_timestamp = int(message_time)  # 已经是毫秒级
                        print(f"📝 传入毫秒级时间戳，直接使用: {feedback_timestamp}")
                else:
                    # 使用当前时间
                    feedback_timestamp = int(time.time() * 1000)
                    print(f"📝 使用当前时间戳: {feedback_timestamp}")

                # 🛡️ 验证时间戳合理性（2023-2030年范围）
                current_timestamp = int(time.time() * 1000)
                min_valid_timestamp = 1672531200000  # 2023-01-01 00:00:00
                max_valid_timestamp = 1893456000000  # 2030-01-01 00:00:00

                if feedback_timestamp < min_valid_timestamp or feedback_timestamp > max_valid_timestamp:
                    print(f"❌ 时间戳异常: {feedback_timestamp}，使用当前时间")
                    feedback_timestamp = current_timestamp

                # 🛡️ 防御性检查：确保 source_name 不为空
                if not source_name:
                    source_name = source_chat if source_chat else "其他"
                    print(f"⚠️ source_name 为空，使用默认值: {source_name}")

                # 构造字段
                fields = {
                    "业务反馈问题记录表": content[:100] + ("..." if len(content) > 100 else ""),
                    "反馈时间": feedback_timestamp,
                    "反馈人": reporter,
                    "反馈来源": source_name,  # 使用 source_name 而不是 source_chat，保持一致性
                    "问题内容": content,
                    "处理状态": "待处理",
                    "类型": message_type,
                    "来源群": source_name  # 使用 source_name 而不是 source_chat，保持一致性
                }

                # 🛡️ 额外验证：确保关键字段不为空
                if not fields.get("反馈时间"):
                    fields["反馈时间"] = int(time.time() * 1000)
                    print(f"⚠️ 反馈时间为空，重新设置: {fields['反馈时间']}")
                if not fields.get("反馈来源"):
                    fields["反馈来源"] = source_name if source_name else "其他"
                    print(f"⚠️ 反馈来源为空，重新设置: {fields['反馈来源']}")

                record_result = record_to_bitable(
                    token=token,
                    app_token=app_token,
                    table_id=table_id,
                    fields=fields
                )

                if record_result.get('code') == 0:
                    record_id = record_result.get('data', {}).get('record', {}).get('record_id')

                    # 🛡️ 验证：检查创建的记录中反馈时间是否正确
                    created_fields = record_result.get('data', {}).get('record', {}).get('fields', {})
                    created_feedback_time = created_fields.get('反馈时间')
                    if not created_feedback_time:
                        print(f"⚠️ [验证失败] 创建的记录反馈时间为空！尝试更新...")
                        print(f"⚠️ [验证失败] 请求的时间戳: {feedback_timestamp}")
                        # 强制更新反馈时间
                        update_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
                        update_payload = {"fields": {"反馈时间": feedback_timestamp}}
                        try:
                            update_resp = requests.put(update_url, headers=headers, json=update_payload)
                            update_result = update_resp.json()
                            if update_result.get('code') == 0:
                                print(f"✅ [修复成功] 已强制更新反馈时间: {feedback_timestamp}")
                            else:
                                print(f"❌ [修复失败] 强制更新失败: {update_result}")
                        except Exception as e:
                            print(f"❌ [修复失败] 强制更新异常: {e}")
                    else:
                        print(f"✅ [验证通过] 反馈时间已设置: {created_feedback_time}")
                        # 转换时间戳为人类可读格式
                        try:
                            dt = datetime.fromtimestamp(created_feedback_time / 1000)
                            print(f"✅ [验证通过] 反馈时间: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                        except Exception as e:
                            print(f"⚠️ 时间戳转换错误: {e}")
                else:
                    print(f"⚠️ 记录表格失败: code={record_result.get('code')}, msg={record_result.get('msg')}")
        else:
            print(f"⚠️ 未找到表格配置，跳过记录")
    except Exception as e:
        print(f"⚠️ 记录表格异常: {e}")
    
    return {
        "success": True,
        "image_forwarded": new_image_key is not None,
        "message_link": message_link,
        "record_id": record_id
    }

# 导出函数
__all__ = ['forward_feedback']

if __name__ == "__main__":
    # 测试用法
    import time

    # 示例：使用消息的实际时间戳（秒级）
    message_create_time = 1711536000  # 示例：2024-03-27 12:00:00 UTC

    result = forward_feedback(
        source_chat="产研-融合业务组",
        reporter="苏键伟",
        content="这种恶意刷单的可以定期加进我们的黑名单排除吗？减少接口拥堵的问题",
        image_key="img_v3_02vs_c6fac74c-cb8d-44d9-8566-3d91ccdf52cg",
        message_id="om_x100b54bb70d1dcb4b3dacfb1122326b",
        message_type="问题",
        message_time=message_create_time  # 传入消息的实际时间戳
    )

    print(f"\\n结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
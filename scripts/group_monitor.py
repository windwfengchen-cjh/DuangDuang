# 群消息轮询监控脚本
# 用于在没有公网回调的情况下，主动拉取群消息并检测@事件

import time
import json
from datetime import datetime

# 配置
SOURCE_CHAT_ID = "oc_469678cc3cd264438f9bbb65da534c0b"  # 产研-融合业务组
TARGET_CHAT_ID = "oc_a016323a9fda4263ab5a27976065088e"  # 猛龙队开发
BOSS_ID = "ou_3e48baef1bd71cc89fb5a364be55cafc"  # 陈俊洪

# 需要@的人
AT_USERS = {
    "施嘉科": "ou_82e152d737ab5aedee7110066828b5a1",
    "宋广智": "ou_cbcd1090961b620a4500ce68e3c81952"
}

# 表格配置
BITABLE_APP_TOKEN = "KNiibDP6KaRwopsPbRucr752ntg"
BITABLE_TABLE_ID = "tblyDHrGGTQTaex6"

# 检测关键词
FEEDBACK_KEYWORDS = [
    "bug", "问题", "报错", "故障", "异常", "反馈", "issue", "错误",
    "需求", "优化", "改进", "建议", "无法", "不能", "失败", "崩溃"
]

def check_if_feedback(content):
    """判断是否是问题反馈"""
    content_lower = content.lower()
    for keyword in FEEDBACK_KEYWORDS:
        if keyword in content_lower:
            return True, f"匹配关键词: {keyword}"
    return False, "无匹配关键词"

def format_forward_message(source_group, original_msg, sender):
    """格式化转发消息"""
    return f"""【来自{source_group}】

原消息：{original_msg}

反馈人：@{sender}

施嘉科 宋广智 请查看~"""

# 记录上次检查的消息ID，避免重复处理
LAST_PROCESSED_MSG = {
    "timestamp": None,
    "msg_id": None
}

print(f"[{datetime.now()}] 群消息轮询监控已启动")
print(f"监控群: 产研-融合业务组")
print(f"转发群: 猛龙队开发")

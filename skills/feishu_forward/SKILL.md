---
skill_id: feishu_forward
version: 1.1.0
description: 飞书群消息转发与@高亮规范（严格版）
---

# 飞书群消息转发与@高亮规范（严格版）

## ⚠️ 重要警告

**绝对禁止：使用纯文本格式发送带@的消息！**

纯文本格式 `<at id="ou_xxx"></at>` **永远不会高亮**，必须使用 Post 消息格式。

## 群内响应规则（强制）

### 被@时的行为准则

| 场景 | 正确做法 | 禁止行为 |
|------|---------|---------|
| **被@反馈问题** | ✅ 默默记录到问题反馈表，**不回复任何消息** | ❌ 发送"正在记录..."、"已记录到表格"等过程消息 |
| **问题已记录** | ✅ 静默处理，通过转发目标群通知处理人 | ❌ 在源群回复确认消息 |
| **需要澄清** | ✅ 转发到目标群@处理人，由处理人跟进 | ❌ 在源群与反馈人讨论 |

**核心原则**：
- 在源群（业务群）中**只监听、不发言**
- 所有响应和通知都通过**转发到目标群**完成
- **绝不**在业务群发送任何解释性、确认性消息

## 核心规则

### 1. 消息格式选择（强制）

| 格式 | 是否支持@高亮 | 使用场景 |
|------|--------------|---------|
| **Post** | ✅ 支持 | 所有需要@人的消息 |
| **Text** | ❌ 不支持 | 仅用于无@的纯文本通知 |

**正确示例（Post格式）**：
```python
{
    "msg_type": "post",
    "content": {
        "zh_cn": {
            "title": "【产研反馈-问题】",
            "content": [
                [{"tag": "text", "text": "问题描述..."}],
                [
                    {"tag": "at", "user_id": "ou_xxx", "user_name": "姓名"},
                    {"tag": "text", "text": " 请查看~"}
                ]
            ]
        }
    }
}
```

**错误示例（Text格式 - 禁止用于@消息）**：
```python
{
    "msg_type": "text",
    "content": {"text": "【产研反馈-问题】... <at id='ou_xxx'></at> 请查看"}
}
# ❌ 这种格式@永远不会高亮！
```

### 2. @高亮关键字段（强制）

**必须同时包含 `user_id` 和 `user_name`**

```python
# ✅ 正确 - 会高亮
{"tag": "at", "user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "施嘉科"}

# ❌ 错误 - 缺少user_name，不会高亮
{"tag": "at", "user_id": "ou_82e152d737ab5aedee7110066828b5a1"}
```

### 3. 转发配置映射

| 来源群 | 来源群ID | 目标群 | 目标群ID | @处理人 |
|--------|----------|--------|----------|---------|
| 产研-融合业务组 | `oc_469678cc3cd264438f9bbb65da534c0b` | 猛龙队开发 | `oc_a016323a9fda4263ab5a27976065088e` | 施嘉科、宋广智 |
| 号卡&宽带需求和酬金系统体系搭建 | `oc_3b4215cdadcc9366c863377561ce00c5` | 猛龙队开发 | `oc_a016323a9fda4263ab5a27976065088e` | 施嘉科、宋广智 |
| 线下号卡-信息流投放上报沟通 | `oc_ee55ec5275cc158b826fe1204d75cf2c` | 猛龙队开发 | `oc_a016323a9fda4263ab5a27976065088e` | 施嘉科 |
| 号卡能力中心信息同频群 | `oc_5bf7336955740fb41ba59e4e929c5239` | 配置4目标群 | `oc_cf3c4adafb332df5988b20204c272dbb` | 施嘉科、郑武友、陈俊洪 |

### 4. 处理人ID映射

```json
{
    "ou_82e152d737ab5aedee7110066828b5a1": "施嘉科",
    "ou_cbcd1090961b620a4500ce68e3c81952": "宋广智",
    "ou_834914563c797190697ca36b074a6952": "郑武友",
    "ou_3e48baef1bd71cc89fb5a364be55cafc": "陈俊洪"
}
```

## 完整转发示例

```python
import json

# 构造Post消息内容
content_blocks = [
    [{"tag": "text", "text": "📍 问题来源：号卡能力中心信息同频群"}],
    [{"tag": "text", "text": "👤 反馈人：严欣欣"}],
    [{"tag": "text", "text": "📌 问题类型：问题/Bug"}],
    [{"tag": "text", "text": "问题描述：重庆移动 - 下单失败，也上报"}],
    [{"tag": "text", "text": ""}],
    [
        {"tag": "at", "user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "施嘉科"},
        {"tag": "text", "text": " "},
        {"tag": "at", "user_id": "ou_cbcd1090961b620a4500ce68e3c81952", "user_name": "宋广智"},
        {"tag": "text", "text": " 请查看~"}
    ]
]

message_content = {
    "zh_cn": {
        "title": "【产研反馈-问题】",
        "content": content_blocks
    }
}

payload = {
    "receive_id": "oc_a016323a9fda4263ab5a27976065088e",
    "msg_type": "post",
    "content": json.dumps(message_content, ensure_ascii=False)
}
```

## 检查清单（发送前必须逐项确认）

- [ ] **使用 `msg_type: "post"` 格式**（禁止text格式用于@消息）
- [ ] **@标签包含 `user_id` 和 `user_name`**（两个字段都必须有）
- [ ] **根据来源群选择正确的目标群**
- [ ] **@的处理人符合配置映射表**
- [ ] **已验证API返回中包含 `mentions` 字段**（这是高亮成功的标志）

## 常见错误案例

### 错误1：使用纯文本格式
```python
# ❌ 错误 - @不会高亮
message = "【产研反馈-问题】... <at id='ou_xxx'></at> 请查看"
send_message(msg_type="text", content={"text": message})
```

### 错误2：缺少user_name
```python
# ❌ 错误 - @不会高亮
{"tag": "at", "user_id": "ou_xxx"}  # 缺少user_name
```

### 错误3：user_id为空
```python
# ❌ 错误 - 配置4郑武友曾出现此问题（已修复）
{"user_id": "", "user_name": "郑武友"}
```

## 相关文件

- `/home/admin/openclaw/workspace/auto_forward.py` - 转发逻辑主文件
- `/home/admin/openclaw/workspace/feishu_contacts.json` - 联系人映射
- `/home/admin/openclaw/workspace/.feishu_bitable_config.json` - 表格配置
- `/home/admin/openclaw/workspace/AT_HIGHLIGHT_FIX.md` - 问题排查记录
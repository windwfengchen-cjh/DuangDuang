# 飞书@高亮问题排查清单

## 问题描述
发现消息中@人没有高亮显示，原因是使用了纯文本格式的`<at id="..."></at>`，而非Post消息的`{"tag": "at", ...}`格式。

## 根本原因
飞书消息有两种格式：
1. **text格式** - 纯文本，`<at id="..."></at>` 不会高亮 ❌
2. **post格式** - 富文本，`{"tag": "at", "user_id": "...", "user_name": "..."}` 会高亮 ✅

## 已检查的发送渠道

### ✅ 已修复/正确的脚本

| 脚本 | 格式 | 状态 |
|------|------|------|
| `auto_forward.py` | Post + user_name | ✅ 已修复 |
| `check_overdue_issues.py` | Post + user_name | ✅ 正确 |
| `auto_update_status.py` | Post + user_name | ✅ 正确 |
| `send_feishu_post.py` | Post + user_name | ✅ 正确 |
| `test_feishu_post.py` | Post + user_name | ✅ 正确 |
| `send_daily_reminder.py` | Text（无@） | ✅ 无需@ |

### ❌ 已发现的问题

1. **配置4中郑武友user_id为空** - 已修复为 `ou_834914563c797190697ca36b074a6952`
2. **message工具直接发送** - 使用纯文本格式，@不会高亮

## 使用规范

### 正确示例（Python Post消息）
```python
message_content = {
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

payload = {
    "receive_id": chat_id,
    "msg_type": "post",
    "content": json.dumps(message_content, ensure_ascii=False)
}
```

### 错误示例（message工具纯文本）
```python
# 这种格式@不会高亮！
message = "【产研反馈-问题】... <at id='ou_xxx'></at> 请查看"
```

## 处理人ID映射

```json
{
    "ou_82e152d737ab5aedee7110066828b5a1": "施嘉科",
    "ou_cbcd1090961b620a4500ce68e3c81952": "宋广智",
    "ou_834914563c797190697ca36b074a6952": "郑武友",
    "ou_3e48baef1bd71cc89fb5a364be55cafc": "陈俊洪"
}
```

## 转发配置

| 来源群ID | 目标群ID | @处理人 |
|----------|----------|---------|
| oc_469678cc3cd264438f9bbb65da534c0b | oc_a016323a9fda4263ab5a27976065088e | 施嘉科、宋广智 |
| oc_3b4215cdadcc9366c863377561ce00c5 | oc_a016323a9fda4263ab5a27976065088e | 施嘉科、宋广智 |
| oc_ee55ec5275cc158b826fe1204d75cf2c | oc_a016323a9fda4263ab5a27976065088e | 施嘉科 |
| oc_5bf7336955740fb41ba59e4e929c5239 | oc_cf3c4adafb332df5988b20204c272dbb | 施嘉科、郑武友、陈俊洪 |

## 注意

**以后需要使用@高亮时，必须通过Python脚本发送Post格式消息，不能直接使用message工具发送纯文本消息。**
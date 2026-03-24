# @人高亮问题 - 深度诊断报告

## 诊断时间
2026-03-23 20:10 GMT+8

## 1. 实际调用的代码路径

### 主要代码路径
```
飞书事件 → skill/src/index.ts → forwarder.forwardMessage() → forwarder.sendPostMessage() → 飞书API
```

### 具体文件位置
| 路径 | 用途 | 状态 |
|------|------|------|
| `/home/admin/openclaw/workspace/auto_forward.py` | 主要转发逻辑 | ✅ 存在 |
| `/home/admin/.openclaw/skills/feishu-feedback-handler/scripts/auto_forward.py` | Skill Python版本 | ✅ 存在 |
| `/home/admin/.openclaw/skills/feishu-feedback-handler/src/forwarder.ts` | Skill TypeScript源码 | ✅ 存在 |
| `/home/admin/.openclaw/skills/feishu-feedback-handler/dist/forwarder.js` | Skill TypeScript编译后 | ✅ 存在 |
| `/home/admin/openclaw/workspace/requirement_follow.py` | 需求跟进逻辑 | ✅ 存在 |

### 调用关系
1. **飞书事件触发** → `skill/src/index.ts` 中的 `handleFeedback()` 或 `handleConsultation()`
2. **调用转发器** → `this.forwarder.forwardMessage()`
3. **构建消息** → `forwarder.ts` 中的 `sendPostMessage()`
4. **发送请求** → 飞书 API `POST /im/v1/messages`

## 2. 实际发送的消息内容

### 测试发送的消息（已验证）
```json
{
  "receive_id": "oc_a016323a9fda4263ab5a27976065088e",
  "msg_type": "post",
  "content": {
    "zh_cn": {
      "title": "【@高亮测试】",
      "content": [
        [{"tag": "text", "text": "这是一条测试消息，用于验证@高亮功能。"}],
        [{"tag": "text", "text": ""}],
        [
          {"tag": "at", "user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "施嘉科"},
          {"tag": "text", "text": " "},
          {"tag": "at", "user_id": "ou_cbcd1090961b620a4500ce68e3c81952", "user_name": "宋广智"},
          {"tag": "text", "text": " 请查看~"}
        ]
      ]
    }
  }
}
```

### API响应（关键发现）
```json
{
  "code": 0,
  "data": {
    "msg_type": "post",
    "mentions": [
      {
        "id": "ou_82e152d737ab5aedee7110066828b5a1",
        "id_type": "open_id",
        "key": "@_user_1",
        "name": "施嘉科"
      },
      {
        "id": "ou_cbcd1090961b620a4500ce68e3c81952",
        "id_type": "open_id",
        "key": "@_user_2",
        "name": "宋广智"
      }
    ],
    "body": {
      "content": "...user_id被替换为@_user_1和@_user_2..."
    }
  }
}
```

### 关键发现
✅ **消息格式完全正确**  
✅ **API正确识别了@**（响应中有mentions数组）  
✅ **user_id被正确替换**（返回的content中@_user_1和@_user_2是飞书内部表示）  

## 3. 问题根因分析

### 已确认的事实
1. 代码中使用的是 `msg_type: "post"` ✅
2. JSON序列化使用了 `ensure_ascii=False` ✅
3. @格式正确（tag/user_id/user_name）✅
4. user_id是有效的open_id格式（ou_开头）✅
5. 飞书API正确识别了@（mentions数组存在）✅

### 可能的问题原因
如果@在飞书客户端中仍然不高亮，可能原因：

1. **飞书机器人权限问题**
   - 机器人没有@成员的权限
   - 需要检查机器人的权限设置

2. **成员不在目标群中**
   - 被@的人必须同时在消息所在群中才能高亮
   - 施嘉科、宋广智是否都在"猛龙队开发"群中？

3. **飞书API限制**
   - 虽然API识别了@，但可能有其他限制
   - 需要检查飞书后台的应用权限

4. **飞书客户端显示问题**
   - 可能是飞书客户端的bug
   - 尝试在不同的飞书客户端查看

5. **代码路径问题**
   - 实际运行的是TypeScript版本（dist/forwarder.js）
   - 需要确保skill已重新编译

## 4. 发现的问题

### 问题1: requirement_follow.py 缺少 ensure_ascii=False（已修复）
- **位置**: 第936行
- **原代码**: `json.dumps(content)`
- **修复后**: `json.dumps(content, ensure_ascii=False)`
- **影响**: 可能导致中文字符被转义为\uXXXX格式

### 问题2: TypeScript版本需要重新编译
- skill/src/forwarder.ts 修改后需要重新编译为 dist/forwarder.js
- 编译命令: `cd /home/admin/.openclaw/skills/feishu-feedback-handler && npm run build`

## 5. 具体修复方案

### 立即执行
1. ✅ **修复requirement_follow.py** - 已添加ensure_ascii=False
2. **重新编译skill**
   ```bash
   cd /home/admin/.openclaw/skills/feishu-feedback-handler
   npm run build
   ```
3. **重启OpenClaw** 使修改生效

### 验证步骤
1. **发送测试消息**
   ```bash
   cd /home/admin/openclaw/workspace
   python3 test_at_highlight_live.py
   ```

2. **检查飞书群中消息**
   - 打开"猛龙队开发"群
   - 查看测试消息中的@是否高亮
   - 点击消息链接验证

3. **如果仍不高亮，检查权限**
   - 登录飞书开放平台
   - 检查机器人应用的权限设置
   - 确认有"发送消息"和"@用户"权限
   - 确认施嘉科、宋广智都在目标群中

### 长期方案
1. 在send_forward_message中添加调试日志（已添加）
2. 定期检查skill是否需要重新编译
3. 建立消息发送监控机制

## 6. 测试消息记录

### 发送的测试消息
- **消息ID**: `om_x100b532696b3c8b8b3278eedd5bd522`
- **目标群**: 猛龙队开发 (oc_a016323a9fda4263ab5a27976065088e)
- **@人员**: 施嘉科、宋广智
- **消息链接**: https://applink.feishu.cn/client/message/open?message_id=om_x100b532696b3c8b8b3278eedd5bd522

请检查该消息在飞书客户端中的显示效果。

## 7. 结论

**消息格式完全正确，API也正确识别了@。如果@仍不高亮，问题很可能在于：**
1. 飞书机器人的权限设置
2. 被@的人不在目标群中
3. 飞书后台的应用配置

请优先检查飞书开放平台的权限设置和成员是否在群中。

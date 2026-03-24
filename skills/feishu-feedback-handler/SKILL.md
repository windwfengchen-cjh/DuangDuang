# 飞书跨群问题反馈处理 Skill

飞书跨群问题反馈自动处理系统，支持多群配置、消息自动转发、表格自动记录、状态自动更新等功能。

## 功能特性

1. **多配置支持** - 支持多个来源群到目标群的转发配置
2. **消息自动转发** - 来源群消息自动转发到目标群并@处理人
3. **表格自动记录** - 问题/需求自动记录到飞书多维表格
4. **状态自动更新** - 处理人回复自动更新表格状态
5. **回复转发** - 处理结果自动转发回来源群
6. **@人高亮显示** - 支持@处理人和反馈人高亮显示
7. **跟进指令处理** - 支持"跟进XX问题"指令自动处理
8. **新群选项自动补充** - 自动添加新来源群到表格选项
9. **图片自动转发** - 使用 Resource API 转发任何人发的图片

## 安装方法

### 1. 安装 Skill

```bash
# 从本地安装
openclaw skills install ~/.openclaw/skills/feishu-feedback-handler

# 从 GitHub 安装（如果已发布）
openclaw skills install github:your-org/feishu-feedback-handler
```

### 2. 配置 Skill

安装后需要创建配置文件：

```bash
cd ~/.openclaw/skills/feishu-feedback-handler
cp config.json.example config.json
```

编辑 `config.json`，填写你的配置：

```json
{
  "bitable": {
    "app_token": "YOUR_BITABLE_APP_TOKEN",
    "table_id": "YOUR_TABLE_ID"
  },
  "bot": {
    "bot_id": "YOUR_BOT_ID"
  },
  "boss": {
    "user_id": "YOUR_BOSS_USER_ID",
    "user_name": "Boss姓名"
  },
  "forward_configs": {
    "oc_source_chat_id": {
      "target_chat_id": "oc_target_chat_id",
      "handlers": [
        { "user_id": "ou_handler1", "user_name": "处理人1" },
        { "user_id": "ou_handler2", "user_name": "处理人2" }
      ],
      "source_name": "来源群名称",
      "record_bitable": true,
      "notify_boss_for_requirement": true
    }
  }
}
```

### 3. 配置说明

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `bitable.app_token` | 飞书多维表格 App Token | `KNiibxxx...` |
| `bitable.table_id` | 表格 ID | `tblyDxxx...` |
| `bot.bot_id` | 机器人 ID | `ou_42xxx...` |
| `boss.user_id` | Boss 的 Open ID | `ou_3exxx...` |
| `boss.user_name` | Boss 的姓名 | `陈俊洪` |
| `forward_configs` | 转发配置映射表，key 为来源群 chat_id | 见上方示例 |

### 转发配置字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `target_chat_id` | string | 目标群 chat_id |
| `handlers` | array | 处理人列表，包含 user_id 和 user_name |
| `source_name` | string | 来源群显示名称 |
| `record_bitable` | boolean | 是否记录到表格 |
| `notify_boss_for_requirement` | boolean | 需求类是否额外@Boss |

### 4. 权限要求

飞书应用需开启以下权限：
- 获取群组信息
- 发送消息
- 读取多维表格
- 写入多维表格
- 读取用户信息
- 读取消息资源（用于图片转发）

## 图片转发

### 工作原理

Skill 使用飞书 **Resource API** 下载图片，支持转发**任何人**发送的图片：

```
GET /open-apis/im/v1/messages/{message_id}/resources/{file_key}?type=image
```

### 转发流程

1. **接收消息** - 从来源群收到带图片的消息
2. **提取信息** - 获取 message_id 和 image_key
3. **下载图片** - 使用 Resource API 下载原图
4. **上传图片** - 上传获取新的 image_key
5. **发送消息** - 在目标群发送带图片的消息
6. **清理文件** - 自动删除本地临时文件

### 图片处理规则

**重要：直接转发原图，不做任何解析/识别/OCR**

- ✅ 收到带图片的消息 → 直接转发原图
- ❌ 不进行 OCR 文字识别
- ❌ 不进行图片内容分析
- ❌ 不生成图片描述
- ✅ 保持图片原始质量和内容

### 失败处理

如果图片下载失败：
- 直接报错，不再使用消息链接方案
- 请检查 message_id 和 image_key 是否正确

## 工作流程

### 正常反馈流程

```
来源群@我反馈问题
    ↓
解析消息内容
    ↓
转发到目标群并@处理人
    ↓
记录到飞书多维表格
    ↓
等待处理人回复
```

### 处理人回复流程

```
处理人在目标群回复
    ↓
转发回复到来源群@反馈人
    ↓
更新表格处理状态
```

### 跟进指令流程

```
收到"跟进XX问题"
    ↓
查询表格找到原记录
    ↓
按当前群配置转发
    ↓
更新表格状态为"处理中"
```

## 注意事项

1. **必须先被拉入来源群**才能接收消息
2. 转发和记录是**同步执行**的
3. 配置文件 `config.json` **不要提交到 Git**（已添加到 .gitignore）
4. 不确定的消息**宁可问 Boss，不要擅自决定**
5. **被动响应原则**：群里没有人@我时，不主动回复或发消息

## @高亮规范

### 正确格式

@高亮功能需要同时提供 `user_id` 和 `user_name` 才能正常工作：

```json
{
  "handlers": [
    {
      "user_id": "ou_82e152d737ab5aedee7110066828b5a1",
      "user_name": "施嘉科"
    }
  ]
}
```

### 字段说明

| 字段 | 说明 | 是否必填 |
|------|------|----------|
| `user_id` | 用户的 Open ID，以 `ou_` 开头 | ✅ 必填 |
| `user_name` | 用户显示名称 | ✅ 必填 |

### 常见错误

#### ❌ 错误示例 1：缺少 user_id
```json
{
  "handlers": [
    { "user_name": "施嘉科" }
  ]
}
```
**后果**：@高亮不生效，降级为纯文本 `@施嘉科`

#### ❌ 错误示例 2：user_id 为空
```json
{
  "handlers": [
    { "user_id": "", "user_name": "施嘉科" }
  ]
}
```
**后果**：被过滤掉，降级为纯文本 `@施嘉科`

#### ❌ 错误示例 3：user_name 为空
```json
{
  "handlers": [
    { "user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "" }
  ]
}
```
**后果**：被过滤掉，降级为纯文本 `@未知用户`

### 防护机制

Skill 已内置@高亮防护机制：

1. **格式验证**：发送前检查每个@配置的 `user_id` 和 `user_name`
2. **无效过滤**：无效的@配置会被过滤，不会导致消息发送失败
3. **降级显示**：无效的@以纯文本形式显示，确保消息仍可送达
4. **调试日志**：发送前打印完整 payload，便于排查问题

### 如何获取 user_id

1. **通过飞书开放平台** - 在"用户与部门"中查看用户的 Open ID
2. **通过机器人日志** - 当用户在群里发消息时，机器人会收到包含 user_id 的消息
3. **通过通讯录 API** - 调用飞书 API 查询用户信息

## 版本历史

### v1.2.1
- 新增@高亮防护机制
- 添加@格式验证，确保 `user_id` 和 `user_name` 都不为空
- 无效的@配置自动降级为纯文本显示
- 添加调试日志，打印完整 payload 便于排查

### v1.2.0
- 将配置从代码抽离到外部配置文件
- 支持通过 `config.json` 自定义配置
- 移除硬编码的默认配置

### v1.1.0
- 新增图片自动转发功能
- 使用 Resource API 下载图片，支持转发任何人发的图片
- 移除消息链接备选方案
- 转发后自动清理本地临时文件

### v1.0.0
- 初始版本
- 支持多群配置
- 消息自动转发
- 表格自动记录
- 状态自动更新

## 作者

- **Author**: DuangDuang
- **Maintainer**: 陈俊洪

## License

MIT

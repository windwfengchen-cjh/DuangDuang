# 飞书跨群问题反馈处理 Skill

飞书跨群问题反馈自动处理系统，支持多群配置、消息自动转发、表格自动记录、状态自动更新等功能。

## 🚀 快速开始

### 1. 安装依赖

```bash
cd ~/.openclaw/skills/feishu-feedback-handler
npm install
```

### 2. 配置 Skill

```bash
cp config.json.example config.json
# 编辑 config.json，填写你的飞书配置
```

### 3. 配置飞书凭证

确保 `~/.openclaw/openclaw.json` 包含飞书凭证：

```json
{
  "channels": {
    "feishu": {
      "appId": "cli_xxxxxxxxxxxxxxxx",
      "appSecret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    }
  }
}
```

### 4. 编译

```bash
npm run build
```

### 5. 启动

```bash
# 使用 openclaw 启动
openclaw skills run feishu-feedback-handler
```

---

## 📖 使用指南

### 基础配置

编辑 `config.json`：

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

### 功能说明

#### 1. 消息自动转发

当用户在来源群@机器人时：
- 消息自动转发到目标群
- @相关处理人
- 记录到多维表格

#### 2. 处理人回复

处理人在目标群回复时：
- 自动转发回来源群
- @原反馈人
- 更新表格状态为"已处理"

#### 3. 需求跟进（与 requirement-follow 集成）

当用户发送"跟进这个需求"时：
- 自动创建需求记录
- 创建调研群
- 拉入 Boss 和需求方
- 启动调研流程

---

## 📁 文件结构

```
~/.openclaw/skills/feishu-feedback-handler/
├── README.md                     # 本文件
├── SKILL.md                      # 完整文档
├── config.json                   # 配置文件（本地创建）
├── config.json.example           # 配置示例
├── package.json                  # Node.js 依赖
├── tsconfig.json                 # TypeScript 配置
├── openclaw.plugin.json          # OpenClaw 插件配置
├── src/
│   └── index.ts                  # 主处理逻辑
├── dist/                         # 编译输出
└── scripts/                      # 辅助脚本
```

---

## 🔗 依赖说明

### requirement-follow Skill

本 skill 依赖 requirement-follow skill 来处理需求跟进功能：

```
feishu-feedback-handler (v1.3.0+)
    ↓ 调用
requirement-follow (v3.0.0+)
```

确保 requirement-follow 已安装并编译：

```bash
cd ~/.openclaw/skills/requirement-follow
npm install
npm run build
```

---

## 📝 命令说明

### 普通反馈

直接在来源群@机器人：
```
@机器人 系统出现问题，无法登录
```

### 跟进指令

查询并跟进历史问题：
```
@机器人 跟进订单问题
```

### 需求跟进（触发 requirement-follow）

```
@机器人 跟进这个需求：需要开发新功能
```

---

## ⚙️ 配置字段说明

### bitable

| 字段 | 说明 | 必填 |
|------|------|------|
| `app_token` | 多维表格 App Token | ✓ |
| `table_id` | 表格 ID | ✓ |

### bot

| 字段 | 说明 | 必填 |
|------|------|------|
| `bot_id` | 机器人 Open ID | ✓ |

### boss

| 字段 | 说明 | 必填 |
|------|------|------|
| `user_id` | Boss 的 Open ID | ✓ |
| `user_name` | Boss 的显示名称 | ✓ |

### forward_configs

键为来源群 chat_id，值为配置对象：

| 字段 | 说明 | 类型 |
|------|------|------|
| `target_chat_id` | 目标群 chat_id | string |
| `handlers` | 处理人列表 | array |
| `source_name` | 来源群显示名称 | string |
| `record_bitable` | 是否记录到表格 | boolean |
| `notify_boss_for_requirement` | 需求类是否@Boss | boolean |

---

## 🔍 调试

### 查看日志

```bash
# 查看实时日志
tail -f ~/.openclaw/logs/feishu-feedback-handler.log

# 或使用 openclaw
openclaw skills logs feishu-feedback-handler
```

### 测试集成

```bash
# 测试与 requirement-follow 的集成
cd ~/.openclaw/skills/feishu-feedback-handler
node test-integration.js
```

---

## 📚 更多信息

- [SKILL.md](./SKILL.md) - 完整的功能文档和 API 说明
- [config.json.example](./config.json.example) - 配置示例
- [INTEGRATION_DIRECT_CALL.md](./INTEGRATION_DIRECT_CALL.md) - 与 requirement-follow 集成详情

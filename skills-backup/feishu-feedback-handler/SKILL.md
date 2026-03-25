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
10. **需求跟进集成** - 与 requirement-follow skill 深度集成

---

## 与 requirement-follow 集成说明

### 集成方式

采用 **直接函数调用** 方案，从 feishu-feedback-handler 直接导入并调用 requirement-follow 的核心类。

```typescript
import { RequirementFollowWorkflow, getDefaultConfig } from '../requirement-follow/dist/index.js';
```

### 触发机制

当用户发送包含以下关键词的消息时触发需求跟进流程：

| 触发词 | 示例 |
|--------|------|
| `跟进这个需求` | "@机器人 跟进这个需求：需要开发新功能" |
| `跟进需求` | "@机器人 跟进需求：优化订单流程" |
| `需求跟进` | "@机器人 需求跟进：增加导出功能" |

### 参数传递格式

从 feishu-feedback-handler 传递到 requirement-follow 的参数：

```typescript
interface RequirementFollowParams {
  requirementContent: string;      // 需求标题/内容
  requesterName: string;           // 需求方姓名
  requesterId: string;             // 需求方 OpenID (ou_xxx)
  sourceChatId: string;            // 来源群ID (oc_xxx)
  sourceChatName: string;          // 来源群名称
  originalMessageId?: string;      // 原始消息ID (可选)
}
```

### handleRequirementFollow 流程

```
收到需求跟进指令
    ↓
提取需求标题（从消息内容）
    ↓
获取发送者信息（姓名、ID）
    ↓
加载配置: getDefaultConfig()
    ↓
创建工作流: new RequirementFollowWorkflow(config)
    ↓
启动工作流: workflow.startWorkflow(params)
    ↓
检查返回结果
    ↓
┌─────────────────┐
│ 成功？          │
└─────────────────┘
    ↓ 是              ↓ 否
发送成功通知      发送错误通知
（含群链接）      （含错误原因）
    ↓
结束
```

### 处理结果返回

```typescript
interface StartWorkflowResult {
  success: boolean;               // 是否成功
  isDuplicate?: boolean;          // 是否为重复需求
  recordId?: string;              // 需求记录ID
  chatId?: string;                // 调研群ID
  chatName?: string;              // 调研群名称
  error?: string;                 // 错误信息
  existingRecordId?: string;      // 相似需求记录ID
}
```

### 成功响应示例

用户收到消息：
```
✅ 需求跟进已启动
📋 需要开发订单同步功能
🆔 rec_xxxxxxxx
💬 需求调研-订单同步功能-张三
👥 调研群已创建，请查看群聊
```

### 重复需求检测

如果检测到相似需求（相似度≥85%）：
```
⚠️ 发现相似需求
该需求与已有需求相似度：92%

📋 已有需求：需要开发订单同步功能
🆔 记录ID：rec_xxxxxx
📅 创建时间：2024-03-20 10:30
💬 状态：跟进中

如需继续创建，请使用不同的描述方式。
```

---

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
  "_comment": "飞书跨群反馈处理配置 - 请根据实际情况修改",
  
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
    "oc_xxxxxxxxxxxxxxxx": {
      "target_chat_id": "oc_yyyyyyyyyyyyyyyy",
      "handlers": [
        { "user_id": "ou_zzzzzzzzzzzzzzzz", "user_name": "处理人1" },
        { "user_id": "ou_wwwwwwwwwwwwwwww", "user_name": "处理人2" }
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

---

## 消息分类逻辑

Skill 自动识别消息类型，根据内容关键词将消息分为三类：

### 分类规则

| 类型 | 关键词 | 处理逻辑 |
|------|--------|----------|
| **需求** | `需求`, `建议`, `优化`, `改进`, `建议增加`, `希望有`, `能否` | 转发到目标群，记录到表格，类型标记为"需求" |
| **咨询** | `如何使用`, `怎么操作`, `在哪里`, `咨询`, `问一下` | 仅转发到目标群，不记录到表格 |
| **问题** | 其他所有内容 | 转发到目标群，记录到表格，类型标记为"问题" |

### 分类代码示例

```typescript
function classifyMessage(text: string): MessageType {
  const lower = text.toLowerCase();
  
  // 需求类关键词
  const demandKeywords = ['需求', '建议', '优化', '改进', '建议增加', '希望有', '能否'];
  if (demandKeywords.some(k => lower.includes(k))) return '需求';
  
  // 咨询类关键词
  const consultKeywords = ['如何使用', '怎么操作', '在哪里', '咨询', '问一下'];
  if (consultKeywords.some(k => lower.includes(k))) return '咨询';
  
  // 默认为问题
  return '问题';
}
```

### 分类处理差异

| 特性 | 需求 | 问题 | 咨询 |
|------|------|------|------|
| 转发到目标群 | ✅ | ✅ | ✅ |
| 记录到 Bitable | ✅ | ✅ | ❌ |
| @Boss（如配置） | ✅ | ❌ | ❌ |
| 触发 requirement-follow | ✅ 通过指令 | ❌ | ❌ |

### 需求跟进触发指令

除自动分类外，以下指令会触发需求跟进流程（调用 requirement-follow）：

| 触发指令 | 示例 |
|----------|------|
| `跟进这个需求` | @机器人 跟进这个需求：需要开发新功能 |
| `跟进需求` | @机器人 跟进需求：优化订单流程 |
| `记录这个需求` | @机器人 记录这个需求：增加导出功能 |
| `跟进一下这个需求` | @机器人 跟进一下这个需求 |
| `记录一下这个需求` | @机器人 记录一下这个需求 |

---

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

---

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
读取 config.json 确认来源群ID（强制）
    ↓
转发回复到来源群@反馈人
    ↓
更新表格处理状态
```

### 转发回复强制规范（2026-03-25 新增）

**⚠️ 转发回复到来源群时，必须从 `config.json` 查询来源群ID，禁止依赖表格字段或其他推断。**

#### 执行步骤

1. **读取配置**
   ```typescript
   const config = JSON.parse(fs.readFileSync('config.json', 'utf8'));
   const forwardConfigs = config.forward_configs;
   ```

2. **匹配来源群**
   - 通过 `source_name` 匹配配置
   - 或通过问题记录中的来源群名称反向查找

3. **获取正确的来源群ID**
   ```typescript
   // forward_configs 的 key 就是来源群 chat_id
   const sourceChatId = Object.keys(forwardConfigs).find(key => {
     return forwardConfigs[key].source_name === '产研-融合业务组';
   });
   ```

4. **转发消息**
   - 使用配置中的 `sourceChatId` 作为目标
   - @反馈人

#### 错误案例（2026-03-25）

**问题：** 子智能体使用了错误的群ID `oc_59539a59e696491bd93241ecd9b8c80d`（配置名称为"待补充"），而非正确的 `oc_469678cc3cd264438f9bbb65da534c0b`（"产研-融合业务组"）。

**原因：** 没有先查 `config.json`，依赖了可能不准确的来源信息。

**教训：** 转发前必须读取配置文件，通过 `source_name` 确认正确的来源群ID。

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

### 需求跟进流程（与 requirement-follow 集成）

```
收到"跟进这个需求"
    ↓
提取需求信息
    ↓
调用 requirement-follow.startWorkflow()
    ↓
检查重复需求
    ↓
创建需求记录
    ↓
创建调研群
    ↓
添加成员（Boss + 需求方）
    ↓
发送确认消息
    ↓
启动调研群监听
```

---

## 注意事项

1. **必须先被拉入来源群**才能接收消息
2. 转发和记录是**同步执行**的
3. 配置文件 `config.json` **不要提交到 Git**（已添加到 .gitignore）
4. 不确定的消息**宁可问 Boss，不要擅自决定**
5. **被动响应原则**：群里没有人@我时，不主动回复或发消息
6. **requirement-follow 依赖**：确保 requirement-follow skill 已安装并编译

---

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

---

## 版本历史

### v1.3.1 (2026-03-25)
- 🔒 新增转发回复强制规范
- 转发回复前必须从 `config.json` 查询来源群ID
- 禁止依赖表格字段或其他推断的来源群信息
- 添加错误案例和教训总结

### v1.3.0 (2024-03-24)
- ✨ 新增与 requirement-follow skill 深度集成
- ✨ 新增需求跟进自动触发机制
- ✨ 新增调研群自动创建和管理
- ✨ 新增需求重复检测
- ♻️ 重构为直接函数调用方式（替代 spawn）
- 📦 依赖 requirement-follow v3.0.0+

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

---

## 作者

- **Author**: DuangDuang
- **Maintainer**: 陈俊洪

## License

MIT

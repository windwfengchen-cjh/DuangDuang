# Requirement Follow Skill v3.0

完整独立的需求跟进解决方案 - 整合自 `requirement_follow.py`

## 📋 目录

1. [功能概述](#功能概述)
2. [工作流程图](#工作流程图)
3. [配置文件说明](#配置文件说明)
4. [API 接口文档](#api-接口文档)
5. [启动方式](#启动方式)
6. [文件存储位置](#文件存储位置)
7. [版本历史](#版本历史)

---

## 功能概述

requirement-follow 是一个完整的需求跟进自动化解决方案，提供以下核心功能：

### 1. 需求记录管理（Bitable 表格）
- 自动创建需求记录到飞书多维表格
- 记录需求内容、来源、时间、需求方信息
- 支持重复需求检测（基于关键词相似度，默认85%阈值）
- 自动更新需求处理状态：待跟进 → 跟进中 → 已完成

### 2. 调研群管理（飞书群聊）
- **创建群聊**：带重试机制，自动验证群聊可用性
- **添加成员**：批量添加需求方和 Boss 到调研群
- **验证成员**：自动检测群成员数量，成员为0时自动解散重建
- **解散群聊**：调研完成后自动解散，释放资源

### 3. 群消息问答（调研流程）
- **等待开始**：创建群后发送欢迎消息，等待"开始调研"指令
- **问答模式**：7个标准问题引导需求方详细描述需求
- **自动收集**：记录群内所有消息作为调研上下文
- **混合模式**：问答与自动收集同时进行
- **智能触发**：检测 "生成PRD"/"完成调研" 等关键词自动完成
- **指令支持**：支持"开始调研"、"完成调研"/"生成PRD"、"取消"等群内指令

### 4. 消息监听处理
- 独立监听调研群消息，避免消耗主 session token
- 支持命令：生成PRD、状态查询、结束调研
- 超时机制：默认24小时自动退出

### 5. PRD 文档生成
- 基于调研上下文自动生成产品需求文档
- 更新表格记录，添加 PRD 文档链接
- 发送完成通知并解散调研群


---

## 工作流程图

### 整体工作流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    需求跟进完整流程                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  用户@机器人: "跟进这个需求"                                     │
│       ↓                                                         │
│  feishu-feedback-handler                                        │
│       ↓ 调用 API                                                │
│  requirement-follow.startWorkflow()                             │
│       ↓                                                         │
│   ┌──────────────────────────────────────┐                     │
│   │ 1. 检查重复需求（相似度检测）           │                     │
│   │ 2. 创建需求记录（Bitable）              │                     │
│   │ 3. 创建调研群（带重试）                 │                     │
│   │ 4. 添加成员（Boss + 需求方）            │                     │
│   │ 5. 发送欢迎消息（状态: waiting_start）  │                     │
│   │ 6. 等待"开始调研"指令                   │                     │
│   └──────────────────────────────────────┘                     │
│       ↓ 用户发送"开始调研"                                       │
│   ┌──────────────────────────────────────┐                     │
│   │ 启动消息监听 + 开始问答                 │                     │
│   │ 状态: researching                       │                     │
│   └──────────────────────────────────────┘                     │
│       ↓                                                         │
│  调研群消息处理（research.ts）                                    │
│   ├─ 问答模式：7个问题引导需求方回答                              │
│   ├─ 自动收集：记录群内所有消息                                  │
│   └─ 混合模式：问答 + 自动收集同时进行                             │
│       ↓                                                         │
│  用户发送 "完成调研"/"生成PRD" 或 超时自动完成                     │
│       ↓                                                         │
│   ┌──────────────────────────────────────┐                     │
│   │ 1. 生成 PRD 文档                       │                     │
│   │ 2. 更新表格状态为 "已完成"              │                     │
│   │ 3. 发送完成通知                         │                     │
│   │ 4. 解散群聊                             │                     │
│   └──────────────────────────────────────┘                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 群创建流程（含重试机制）

```
开始创建群聊
    ↓
调用飞书API创建群
    ↓
┌─────────────┐
│ 创建成功？   │
└─────────────┘
    ↓ 是              ↓ 否
验证群成员数      重试（最多3次）
    ↓                    ↓
┌─────────────┐    重试成功？
│ 成员 > 0？   │    ↓ 是    ↓ 否（3次后）
└─────────────┘  继续验证   报错退出
    ↓ 是    ↓ 否
返回成功   解散重建
```


---

## 配置文件说明

### 配置文件位置

- **主配置**: `~/.openclaw/skills/requirement-follow/config.json`
- **示例配置**: `~/.openclaw/skills/requirement-follow/config.json.example`
- **飞书凭证**: `~/.openclaw/openclaw.json`

### config.json 结构

```json
{
  "name": "requirement-follow",
  "version": "1.0.0",
  "description": "Standalone skill for handling requirement research group messages",
  "entry": "src/index.ts",
  "config": {
    "chat_id": {
      "type": "string",
      "required": true,
      "description": "Research chat group ID"
    },
    "requirement_id": {
      "type": "string",
      "required": true,
      "description": "Requirement record ID in Bitable"
    },
    "requester_id": {
      "type": "string",
      "required": true,
      "description": "Original requester ID"
    },
    "trigger_words": {
      "type": "array",
      "default": ["生成PRD", "完成调研", "generate_prd", "prd", "完成"],
      "description": "Trigger words for generating PRD"
    },
    "timeout_hours": {
      "type": "number",
      "default": 24,
      "description": "Auto-exit timeout in hours"
    },
    "app_token": {
      "type": "string",
      "required": true,
      "description": "Bitable app token"
    },
    "table_id": {
      "type": "string",
      "required": true,
      "description": "Bitable table ID"
    }
  },
  "permissions": [
    "message:read",
    "message:send",
    "feishu:read",
    "feishu:write"
  ]
}
```

### 配置字段说明

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `name` | string | ✓ | - | Skill 名称 |
| `version` | string | ✓ | - | 版本号 |
| `entry` | string | ✓ | - | 入口文件路径 |
| `config.chat_id` | string | ✓ | - | 调研群 ID |
| `config.requirement_id` | string | ✓ | - | Bitable 需求记录 ID |
| `config.requester_id` | string | ✓ | - | 需求方用户 ID |
| `config.trigger_words` | array | ✗ | [见上] | PRD生成触发词 |
| `config.timeout_hours` | number | ✗ | 24 | 自动超时时间（小时） |
| `config.app_token` | string | ✓ | - | Bitable App Token |
| `config.table_id` | string | ✓ | - | Bitable 表格 ID |
| `permissions` | array | ✓ | - | 所需权限列表 |

### 飞书凭证配置 (~/.openclaw/openclaw.json)

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


---

## API 接口文档

### RequirementFollowWorkflow 类

主工作流类，封装完整的需求跟进流程。

#### 构造函数

```typescript
constructor(config: RequirementFollowConfig)
```

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| config | RequirementFollowConfig | 包含 appId, appSecret, appToken, tableId 等 |

#### startWorkflow(params)

启动完整的需求跟进流程。

```typescript
async startWorkflow(params: {
  requirementContent: string;      // 需求内容描述
  requesterName: string;           // 需求方姓名
  requesterId: string;             // 需求方 OpenID
  sourceChatId: string;            // 来源群ID
  sourceChatName: string;          // 来源群名称
  originalMessageId?: string;      // 原始消息ID（可选）
  additionalMembers?: string[];    // 额外成员ID列表（可选）
}): Promise<StartWorkflowResult>
```

**返回值：**
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

**示例：**
```typescript
const workflow = new RequirementFollowWorkflow(config);
const result = await workflow.startWorkflow({
  requirementContent: '需要开发订单同步功能',
  requesterName: '张三',
  requesterId: 'ou_xxx',
  sourceChatId: 'oc_xxx',
  sourceChatName: '业务反馈群'
});

if (result.success) {
  console.log(`✅ 需求跟进已启动`);
  console.log(`   记录ID: ${result.recordId}`);
  console.log(`   群ID: ${result.chatId}`);
}
```

#### completeWorkflow(requirementId, chatContext)

完成需求跟进，生成 PRD 并解散群。

```typescript
async completeWorkflow(
  requirementId: string,
  chatContext?: string
): Promise<CompleteWorkflowResult>
```

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| requirementId | string | 需求记录ID |
| chatContext | string | 调研上下文内容（可选） |

**返回值：**
```typescript
interface CompleteWorkflowResult {
  success: boolean;
  requirementId?: string;
  prdPath?: string;               // PRD 文件路径
  chatDisbanded?: boolean;        // 群是否已解散
  error?: string;
}
```

### 工作流状态说明

| 状态 | 说明 | 触发条件 |
|------|------|----------|
| `waiting_start` | 等待开始调研 | 群创建完成，发送欢迎消息后 |
| `researching` | 调研进行中 | 用户发送"开始调研"指令后 |
| `completed` | 调研完成 | 用户发送"完成调研"/"生成PRD"或超时 |
| `cancelled` | 调研取消 | 用户发送"取消"指令 |

### 群内指令

创建调研群后，支持以下群内指令：

| 指令 | 动作 | 状态要求 |
|------|------|----------|
| `开始调研` / `start` | 启动问答流程，开始收集需求信息 | waiting_start |
| `完成调研` / `生成PRD` / `prd` | 生成 PRD 文档并结束调研 | researching |
| `取消` / `cancel` | 终止调研，解散群聊 | any |
| `状态` / `status` | 查看当前调研状态 | any |

**工作流程：**
1. 群创建后发送欢迎消息，状态为 `waiting_start`
2. 需求方或 Boss 发送"开始调研"指令后，启动问答
3. 问答过程中自动收集所有群消息作为调研上下文
4. 发送"完成调研"或"生成PRD"生成 PRD 并结束


### 便捷函数

#### startRequirementFollow(params)

一行代码启动需求跟进。

```typescript
import { startRequirementFollow } from './index';

const result = await startRequirementFollow({
  requirementContent: '需求描述...',
  requesterName: '张三',
  requesterId: 'ou_xxx',
  sourceChatId: 'oc_xxx',
  sourceChatName: '反馈群'
});
```

#### completeRequirementFollow(requirementId, chatContext)

一行代码完成需求跟进。

```typescript
import { completeRequirementFollow } from './index';

const result = await completeRequirementFollow(
  'record_id_xxx',
  '调研上下文...'
);
```

#### getDefaultConfig()

从 `~/.openclaw/openclaw.json` 加载默认配置。

```typescript
import { getDefaultConfig } from './index';

const config = getDefaultConfig();
// 返回 null 如果配置加载失败
```

### FeishuAPI 类

群管理和消息发送 API。

```typescript
import { FeishuAPI } from './api';

const api = new FeishuAPI({ appId: 'xxx', appSecret: 'xxx' });

// 创建群聊
const chat = await api.createChat({
  name: '需求调研群',
  description: '...',
  user_id_list: ['ou_xxx', 'ou_yyy']
});

// 添加成员
const result = await api.addMembersToChat(chatId, ['ou_xxx']);

// 发送消息
await api.sendTextMessage(chatId, '欢迎消息');
await api.sendPostMessage(chatId, { title: '...', content: [...] });

// 解散群
await api.disbandChat(chatId);
```

### BitableClient 类

需求跟进清单表操作。

```typescript
import { BitableClient } from './bitable';

const client = new BitableClient({
  appToken: 'xxx',
  tableId: 'xxx',
  feishuApi: api
});

// 创建记录
const recordId = await client.createRecord({
  requirementContent: '...',
  requesterName: '...',
  requesterId: '...',
  sourceChatId: '...',
  sourceChatName: '...'
});

// 更新状态
await client.updateStatus(recordId, '已完成', '/path/to/prd.md');

// 查找相似需求
const similar = await client.findSimilarRequirement('需求描述', 0.85);
```


---

## 启动方式

### 方式一：独立启动（直接运行）

适用于直接启动调研监听：

```bash
# 使用启动脚本
~/.openclaw/skills/requirement-follow/scripts/start.sh \
  --chat-id "oc_xxx" \
  --requirement-id "rec_xxx" \
  --requester-id "ou_xxx" \
  --app-token "Op8WbbFewaq1tasfO8IcQkXmnFf" \
  --table-id "tbl0vJo8gPHIeZ9y"

# 或使用 node 直接运行
cd ~/.openclaw/skills/requirement-follow
node dist/index.js \
  --chat-id "oc_xxx" \
  --requirement-id "rec_xxx" \
  --requester-id "ou_xxx"
```

### 方式二：被调用启动（API调用）

其他 skill 或程序通过 API 调用启动：

```typescript
// feishu-feedback-handler 中调用
import { RequirementFollowWorkflow, getDefaultConfig } from '../requirement-follow/dist/index.js';

async function handleRequirementFollow(event, text, config) {
  const rfConfig = getDefaultConfig();
  const workflow = new RequirementFollowWorkflow(rfConfig);
  
  const result = await workflow.startWorkflow({
    requirementContent: '需求描述',
    requesterName: '张三',
    requesterId: 'ou_xxx',
    sourceChatId: 'oc_xxx',
    sourceChatName: '反馈群'
  });
  
  return result;
}
```

### 方式三：通过 openclaw CLI 启动

```bash
openclaw skill run requirement-follow \
  --chat-id "oc_xxx" \
  --requirement-id "rec_xxx" \
  --requester-id "ou_xxx"
```

---

## 文件存储位置

| 类型 | 路径 | 说明 |
|------|------|------|
| **源代码** | `~/.openclaw/skills/requirement-follow/src/` | TypeScript 源码 |
| **编译输出** | `~/.openclaw/skills/requirement-follow/dist/` | JavaScript 编译结果 |
| **配置** | `~/.openclaw/skills/requirement-follow/config.json` | Skill 配置 |
| **示例配置** | `~/.openclaw/skills/requirement-follow/config.json.example` | 配置示例 |
| **飞书凭证** | `~/.openclaw/openclaw.json` | 飞书应用凭证 |
| **脚本** | `~/.openclaw/skills/requirement-follow/scripts/` | 启动脚本 |
| **日志** | `/tmp/requirement_follow_<record_id>.log` | 运行日志 |
| **上下文** | `/tmp/requirement_follow/<record_id>.json` | 调研上下文缓存 |
| **PID文件** | `/tmp/requirement_follow_<record_id>.pid` | 进程ID文件 |

---

## 版本历史

### v3.1.0 (2026-03-25)
- ✨ 新增 `waiting_start` 等待开始状态
- ✨ 支持群内"开始调研"指令控制调研启动
- ✨ 支持"取消"指令终止调研
- ✨ 更新工作流：创建群 → 等待指令 → 开始调研
- ♻️ 优化用户体验：不再自动开始问答，等待用户准备就绪

### v3.0.0 (2024-03-24)
- ✨ 完整整合自 `requirement_follow.py`
- ✨ 新增 `RequirementFollowWorkflow` 完整工作流类
- ✨ 新增 `FeishuAPI` 群管理模块
- ✨ 新增 `BitableClient` 表格操作模块
- ✨ 新增群创建重试机制
- ✨ 新增成员验证机制
- ♻️ 重构为模块化架构
- 📦 简化 `feishu-feedback-handler` 集成
- ⛔ 废弃 `workspace/requirement_follow.py`

### v2.0.0 (2024-03-20)
- 从 `feishu-feedback-handler` 迁移调研逻辑
- 统一调研消息处理
- 新增独立 session 监听

### v1.0.0 (2024-03-18)
- 初始版本
- 基础调研消息处理

---

## 集成说明

### 与 feishu-feedback-handler 集成

```typescript
// feishu-feedback-handler/src/index.ts
import { RequirementFollowWorkflow, getDefaultConfig } from '../requirement-follow/dist/index.js';

private async handleRequirementFollow(event: FeishuMessageEvent, text: string, config: ForwardConfig): Promise<any> {
  const rfConfig = getDefaultConfig();
  if (!rfConfig) {
    return { success: false, error: '配置加载失败' };
  }
  
  const workflow = new RequirementFollowWorkflow(rfConfig);
  
  const result = await workflow.startWorkflow({
    requirementContent: extractTitle(event.content),
    requesterName: event.sender.sender_name || 'Unknown',
    requesterId: event.sender.sender_id.open_id,
    sourceChatId: event.chat_id,
    sourceChatName: config.source_name,
    originalMessageId: event.message_id
  });
  
  return result;
}
```

### 调用流程

```
用户消息 → FeedbackHandler.handleMessage()
              ↓
         检测需求跟进指令
              ↓
         FeedbackHandler.handleRequirementFollow()
              ↓
         获取配置: getDefaultConfig()
              ↓
         创建工作流: new RequirementFollowWorkflow(config)
              ↓
         启动工作流: workflow.startWorkflow(params)
              ↓
         返回结果 → 发送确认消息
```


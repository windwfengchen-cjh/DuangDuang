# feishu-feedback-handler 直接调用 requirement-follow 集成方案

## 解决方案概述

采用 **直接函数调用** 方案，从 feishu-feedback-handler 直接导入并调用 requirement-follow 的核心类。

## 实现方式

### 1. 导入方式

```typescript
import { RequirementFollowWorkflow, getDefaultConfig } from '../../requirement-follow/dist/index.js';
```

使用相对路径从 requirement-follow 的 dist 目录导入编译后的 JavaScript 模块。

### 2. 调用流程

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

### 3. 核心代码

```typescript
private async handleRequirementFollow(event: FeishuMessageEvent, text: string, config: ForwardConfig): Promise<any> {
  // 1. 提取需求信息
  const senderName = event.sender.sender_name || 'Unknown';
  const senderId = event.sender.sender_id.open_id;
  const requirementTitle = extractTitle(event.content);

  // 2. 直接调用 requirement-follow
  const rfConfig = getDefaultConfig();
  const workflow = new RequirementFollowWorkflow(rfConfig);
  const result = await workflow.startWorkflow({
    requirementContent: requirementTitle,
    requesterName: senderName,
    requesterId: senderId,
    sourceChatId: event.chat_id,
    sourceChatName: config.source_name,
    originalMessageId: event.message_id
  });

  // 3. 处理结果
  if (result.success) {
    await sendFeishuMessage(event.chat_id, 
      `✅ 需求已记录\n📋 ${requirementTitle}\n🆔 ${result.recordId}\n💬 ${result.chatName}`, 
      token);
  }

  return result;
}
```

## 项目结构

```
~/.openclaw/skills/
├── feishu-feedback-handler/
│   ├── src/
│   │   └── index.ts          # 修改: 直接调用 requirement-follow
│   ├── dist/
│   │   └── index.js          # 编译输出
│   └── package.json          # 版本: 1.3.0
│
└── requirement-follow/
    ├── dist/
    │   └── index.js          # 导出: RequirementFollowWorkflow 类
    └── src/
        └── index.ts          # 源码
```

## 导出内容 (requirement-follow)

```typescript
// 核心类
export class RequirementFollowWorkflow {
  constructor(config: RequirementFollowConfig);
  startWorkflow(params: {...}): Promise<StartWorkflowResult>;
  completeWorkflow(requirementId: string, chatContext?: string): Promise<CompleteWorkflowResult>;
}

// 便捷函数
export function getDefaultConfig(): RequirementFollowConfig | null;
export function startRequirementFollow(params: {...}): Promise<StartWorkflowResult>;
export function completeRequirementFollow(...): Promise<CompleteWorkflowResult>;
```

## 编译状态

✅ **编译成功**

```bash
$ cd ~/.openclaw/skills/feishu-feedback-handler
$ npm run build

> feishu-feedback-handler@1.3.0 build
> tsc

# 无错误，编译成功
```

## 新的调用流程对比

| 特性 | 旧方式 (spawn) | 新方式 (直接调用) |
|------|---------------|------------------|
| 调用方式 | 子进程 spawn | 函数调用 |
| 依赖 | OpenClaw CLI | 无额外依赖 |
| 性能 | 慢 (进程启动) | 快 (函数调用) |
| 错误处理 | 困难 (stderr) | 容易 (try-catch) |
| 类型安全 | 无 | TypeScript 类型 |
| 调试 | 困难 | 容易 |

## 部署说明

1. 确保 requirement-follow 已编译:
   ```bash
   cd ~/.openclaw/skills/requirement-follow
   npm run build
   ```

2. 编译 feishu-feedback-handler:
   ```bash
   cd ~/.openclaw/skills/feishu-feedback-handler
   npm run build
   ```

3. 重启 skill 服务即可生效

## 注意事项

1. **路径依赖**: 两个 skill 必须在 `~/.openclaw/skills/` 目录下
2. **编译顺序**: 先编译 requirement-follow，再编译 feishu-feedback-handler
3. **配置共享**: 两个 skill 共享相同的飞书配置 (`~/.openclaw/openclaw.json`)

## 故障排除

### 问题: 找不到模块
**解决**: 确保 requirement-follow 已编译 (`dist/index.js` 存在)

### 问题: 类型错误
**解决**: 检查 TypeScript 版本兼容性和类型定义

### 问题: 运行时错误
**解决**: 检查 `~/.openclaw/openclaw.json` 配置是否正确

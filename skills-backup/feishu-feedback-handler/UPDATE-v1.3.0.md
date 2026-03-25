# feishu-feedback-handler v1.3.0 更新说明

## 主要变更

### 需求跟进调用方式变更

**之前的方式** (v1.2.x):
- 使用 `spawn('openclaw', ['sessions_spawn', '--skill', 'requirement-follow', ...])` 启动子进程
- 通过命令行参数传递数据
- 依赖 OpenClaw CLI 工具

**新的方式** (v1.3.0):
- 直接导入 `RequirementFollowWorkflow` 类
- 调用 `workflow.startWorkflow()` 方法
- 纯 JavaScript/TypeScript 函数调用，无外部依赖

## 实现细节

### 代码变更

```typescript
// 导入 requirement-follow 的核心类
import { RequirementFollowWorkflow, getDefaultConfig as getRFConfig } from '../../requirement-follow/dist/index.js';

// 在 handleRequirementFollow 方法中直接调用
const rfConfig = getRFConfig();
const workflow = new RequirementFollowWorkflow(rfConfig);
const result = await workflow.startWorkflow({
  requirementContent: requirementTitle,
  requesterName: senderName,
  requesterId: senderId,
  sourceChatId: event.chat_id,
  sourceChatName: config.source_name,
  originalMessageId: event.message_id
});
```

### 流程图

```
用户发送: "@机器人 跟进这个需求 xxx"
         ↓
feishu-feedback-handler 接收消息
         ↓
handleMessage() 检测到需求跟进指令
         ↓
handleRequirementFollow() 被调用
         ↓
直接实例化 RequirementFollowWorkflow
         ↓
调用 workflow.startWorkflow()
         ↓
requirement-follow 内部执行:
  - 检查重复需求
  - 创建需求记录
  - 创建调研群
  - 添加成员
  - 发送欢迎消息
         ↓
返回结果给 feishu-feedback-handler
         ↓
发送确认消息给用户
```

## 优点

1. **可靠性提升**: 不再依赖 spawn 子进程，避免了进程管理问题
2. **性能优化**: 函数调用比进程启动快得多
3. **错误处理**: 可以捕获和传递详细的错误信息
4. **类型安全**: TypeScript 类型检查和自动补全
5. **调试方便**: 可以在同一进程内调试

## 文件变更

### 修改的文件
- `src/index.ts` - 主要逻辑变更
- `package.json` - 版本号更新

### 删除的方法
- `spawnRequirementFollowSkill()` - 移除 spawn 调用
- `handleRequirementFollowRecord()` - 合并到主方法
- `handleRequirementFollowFallback()` - 不再需要

## 兼容性

- 与现有配置完全兼容
- 与现有需求跟进流程完全兼容
- requirement-follow skill 本身无需修改

## 测试建议

1. 在测试群发送 "@机器人 跟进这个需求 xxx"
2. 验证需求记录是否创建
3. 验证调研群是否创建
4. 验证成员是否正确添加
5. 验证重复需求检测是否正常

## 回滚方案

如需回滚到 v1.2.x，只需恢复之前的代码版本即可。

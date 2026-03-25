# Requirement Follow Skill

独立的需求调研群消息处理 Skill，避免消耗主 session token。

## 🚀 快速开始

### 1. 安装依赖

```bash
cd ~/.openclaw/skills/requirement-follow
npm install
```

### 2. 配置飞书凭证

创建或编辑 `~/.openclaw/openclaw.json`：

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

### 3. 配置 Skill

```bash
cp config.json.example config.json
# 根据需要编辑 config.json
```

### 4. 编译

```bash
npm run build
```

### 5. 启动 Skill

```bash
# 方法1: 使用启动脚本
./scripts/start.sh \
  --chat-id "oc_xxx" \
  --requirement-id "rec_xxx" \
  --requester-id "ou_xxx" \
  --app-token "YOUR_APP_TOKEN" \
  --table-id "YOUR_TABLE_ID"

# 方法2: 通过 openclaw 启动
openclaw skill run requirement-follow \
  --chat-id "oc_xxx" \
  --requirement-id "rec_xxx" \
  --requester-id "ou_xxx"
```

### 6. 群内指令示例

启动后，在调研群内使用以下指令：

```
# 1. 群创建后，先发送欢迎消息，等待"开始调研"指令
[系统] 欢迎消息：需求调研群已创建，请发送"开始调研"启动问答

# 2. 需求方或 Boss 发送开始指令
开始调研

# 3. 机器人开始问答流程
[机器人] 问题1/7：请描述一下这个需求的背景和业务场景？
...

# 4. 调研完成后，发送完成指令
完成调研
# 或
generate_prd
```

---

## 📖 使用指南

### 作为独立服务启动

适用于直接监听调研群消息：

```bash
# 基础用法
~/.openclaw/skills/requirement-follow/scripts/start.sh \
  --chat-id "oc_xxx" \
  --requirement-id "rec_xxx" \
  --requester-id "ou_xxx"

# 完整参数
~/.openclaw/skills/requirement-follow/scripts/start.sh \
  --chat-id "oc_xxx" \
  --requirement-id "rec_xxx" \
  --requester-id "ou_xxx" \
  --app-token "Op8WbbFewaq1tasfO8IcQkXmnFf" \
  --table-id "tbl0vJo8gPHIeZ9y" \
  --timeout 48
```

### 调研工作流程

新的工作流程支持"等待开始"模式：

```
创建调研群
    ↓
发送欢迎消息（状态: waiting_start）
    ↓
等待用户发送"开始调研"指令
    ↓
启动问答流程（状态: researching）
    ↓
7个问题引导 + 自动收集消息
    ↓
用户发送"完成调研"或"生成PRD"
    ↓
生成PRD → 更新表格 → 解散群聊
```

### 群内指令

| 指令 | 说明 |
|------|------|
| `开始调研` | 启动问答流程（群创建后需先发送此指令） |
| `完成调研` / `生成PRD` | 结束调研，生成PRD文档 |
| `取消` | 终止调研，解散群聊 |
| `状态` | 查看当前调研状态 |

### 作为模块被调用

在其他 skill 中调用：

```typescript
import { RequirementFollowWorkflow, getDefaultConfig } from '../requirement-follow/dist/index.js';

async function handleRequirement() {
  const config = getDefaultConfig();
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
}
```

---

## ⌨️ 命令触发词

| 命令 | 动作 | 使用时机 |
|------|------|----------|
| `开始调研` / `start` | 启动问答流程，开始收集需求信息 | 群创建后，准备开始调研时 |
| `生成PRD` / `完成调研` / `prd` | 生成 PRD 文档并结束调研 | 调研完成后 |
| `取消` / `cancel` | 终止调研，解散群聊 | 任何阶段 |
| `状态` / `status` | 查看当前调研状态 | 任何阶段 |
| `结束` / `退出` | 退出 skill | 任何阶段 |

---

## 📁 文件结构

```
~/.openclaw/skills/requirement-follow/
├── SKILL.md                      # Skill 定义文档
├── README.md                     # 本文件
├── config.json                   # Skill 配置
├── config.json.example           # 配置示例
├── package.json                  # Node.js 依赖
├── tsconfig.json                 # TypeScript 配置
├── src/
│   ├── index.ts                  # 主入口，导出工作流
│   ├── api.ts                    # Feishu API 封装
│   ├── bitable.ts                # Bitable 表格操作
│   └── research.ts               # 调研消息处理
├── dist/                         # 编译输出
└── scripts/
    ├── start.sh                  # 启动脚本
    └── monitor_research_chat.py  # Python 辅助脚本
```

---

## ⚙️ 进程管理

```bash
# 查看运行中的 skill 进程
ps aux | grep requirement-follow

# 查看特定需求的 skill 日志
tail -f /tmp/requirement_follow_<record_id>.log

# 停止特定需求的 skill
kill $(cat /tmp/requirement_follow_<record_id>.pid)

# 停止所有 requirement-follow skill
pkill -f "requirement-follow"
```

---

## ⏱️ 超时机制

- 默认超时时间：24 小时
- 超时后自动发送退出通知并清理资源
- 可以通过 `--timeout` 参数调整

---

## 💾 消息上下文

- 自动保存最近 100 条消息
- 上下文存储在 `/tmp/requirement_follow/<record_id>.json`
- 用于生成 PRD 时提供完整调研信息

---

## 📝 日志

日志文件位置：`/tmp/requirement_follow_<record_id>.log`

包含：
- 启动/退出时间
- 接收到的消息记录
- 命令执行结果
- 错误信息

---

## 🐛 调试

```bash
# 前台运行查看详细日志
bash ~/.openclaw/skills/requirement-follow/scripts/start.sh \
  --chat-id "oc_xxx" \
  --requirement-id "rec_xxx" \
  --requester-id "ou_xxx" 2>&1 | tee /tmp/skill_debug.log
```

---

## 📚 更多信息

- [SKILL.md](./SKILL.md) - 完整的 API 文档和架构说明
- [config.json.example](./config.json.example) - 配置示例

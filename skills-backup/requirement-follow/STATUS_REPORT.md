# 需求跟进工作流系统 - 启动报告

## 📊 系统状态概览

| 项目 | 状态 | 详情 |
|------|------|------|
| Skill 安装 | ✅ 已就绪 | requirement-follow v3.0.0 |
| 代码编译 | ✅ 已完成 | dist/ 目录存在 |
| Bitable 连接 | ✅ 已配置 | App: Op8WbbFewaq1tasfO8IcQkXmnFf |
| 飞书凭证 | ✅ 已配置 | AppID: cli_a9390dce99f9dbc9 |
| 消息监听 | ✅ 已就绪 | feishu-feedback-handler 已集成 |

---

## 📋 当前待处理需求

**总数: 1 条**

| 记录ID | 需求内容 | 需求方 | 状态 | 时间 |
|--------|----------|--------|------|------|
| recveMa92m9xxH | 抖音小程序客服工单对接飞书 | 陈俊洪 | 待跟进 | 2025-03-24 |

---

## ⚙️ 配置详情

### Bitable 需求跟进清单表
- **App Token**: `Op8WbbFewaq1tasfO8IcQkXmnFf`
- **Table ID**: `tbl0vJo8gPHIeZ9y`
- **Boss ID**: `ou_3e48baef1bd71cc89fb5a364be55cafc`

### 飞书应用
- **App ID**: `cli_a9390dce99f9dbc9`
- **App Secret**: `npTtb8fp0ZwefHldLzFLZf8o4GrdWhP5`

### 触发词配置
```
跟进这个需求, 跟进需求, 记录这个需求, 
跟进一下这个需求, 记录一下这个需求
```

---

## 🚀 工作流程

```
用户@机器人: "跟进这个需求"
    ↓
feishu-feedback-handler 识别指令
    ↓
记录到业务反馈表
    ↓
调用 requirement-follow skill
    ↓
检查重复需求 (相似度>85%)
    ↓
创建需求记录 (状态: 待跟进)
    ↓
创建调研群 (带重试机制)
    ↓
添加成员 (需求方 + Boss)
    ↓
发送欢迎消息
    ↓
启动消息监听 (问答+自动收集)
    ↓
用户发送 "完成调研" → 生成PRD → 解散群聊
```

---

## 📝 使用说明

### 启动需求跟进
在配置的群内 @机器人 并发送：
```
@机器人 跟进这个需求
需求内容：xxxxxx
```

### 完成调研
在调研群内发送触发词：
```
生成PRD / 完成调研 / prd / 完成
```

---

## ⚠️ 注意事项

1. **调研群名称格式**: `需求调研-{需求方}-{MM-DD}`
2. **超时处理**: 24小时自动提醒
3. **重复检测**: 基于关键词相似度 (阈值: 85%)
4. **成员添加失败**: 自动发送私信邀请

---

## 🔧 技术细节

### 文件结构
```
~/.openclaw/skills/requirement-follow/
├── src/
│   ├── index.ts      # 主工作流 API
│   ├── api.ts        # 飞书群管理 API
│   ├── bitable.ts    # 多维表格操作
│   └── research.ts   # 调研消息处理
├── dist/             # 编译输出
├── config.json       # Skill 配置
└── start.sh          # 启动脚本
```

### 核心 API
- `RequirementFollowWorkflow.startWorkflow()` - 启动完整流程
- `RequirementFollowWorkflow.completeWorkflow()` - 完成调研
- `BitableClient.createRecord()` - 创建需求记录
- `BitableClient.findSimilarRequirement()` - 重复检测

---

## ✅ 系统已就绪

需求跟进监听流程已成功启动！
等待用户发送 "跟进XX需求" 指令...

生成时间: 2026-03-24 17:37 GMT+8

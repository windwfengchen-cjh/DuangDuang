# Requirement Follow Skill - v1.1.0 Update

## 更新内容

### 新增：问答+自动收集混合模式 (QA + Auto-Collect Hybrid Mode)

这个版本新增了**问答+自动收集混合模式**，在需求调研过程中自动发送7个预设问题引导需求人回答，同时收集群内所有讨论内容。

#### 7个研究问题

1. **业务背景** - Business background and context
2. **目标用户** - Target users and personas  
3. **现状描述** - Current situation/process
4. **核心痛点** - Core pain points
5. **期望解决方案** - Expected solution
6. **优先级和时间** - Priority and timeline
7. **相关资料** - Supporting materials

#### 混合模式工作流程

1. 启动时发送欢迎消息并 @需求人
2. 自动发送第1个问题
3. 检测需求人回答后自动发送下一个问题
4. 同时收集群内所有消息（不只是答案）
5. 7个问题回答完毕后自动生成PRD

### 更新文件

- `SKILL.md` - 更新文档，添加混合模式说明
- `scripts/monitor_research_chat.py` - 添加QA模式支持
- `src/index.ts` - 类型定义参考（需要进一步更新）

### 使用方法

#### 启用QA模式

```bash
python3 scripts/monitor_research_chat.py \
  --chat-id "oc_xxx" \
  --requirement-id "rec_xxx" \
  --requester-id "ou_xxx" \
  --requester-name "杨政航" \
  --qa-mode
```

#### 仅自动收集模式

```bash
python3 scripts/monitor_research_chat.py \
  --chat-id "oc_xxx" \
  --requirement-id "rec_xxx" \
  --requester-id "ou_xxx"
```

### Python 参考实现

完整的轮询实现参考：
`/home/admin/openclaw/workspace/poll_research_chats.py`

该脚本展示了：
- 直接飞书API轮询（无需事件订阅）
- QA模式状态管理
- 消息收集和存储
- 触发词检测

### 数据结构

会话状态保存在：
`~/.openclaw/feishu/research/{chat_id}.json`

```json
{
  "status": "collecting",
  "qa_mode": true,
  "current_question_idx": 2,
  "collected_answers": {
    "background": "...",
    "target_users": "..."
  },
  "questions_sent": [0, 1]
}
```

### Changelog

#### v1.1.0 (2026-03-24)
- 新增问答+自动收集混合模式
- 添加7个预定义研究问题
- 添加自动问题推进功能
- 添加需求人回答检测
- 更新配置支持QA模式

#### v1.0.0
- 初始版本
- 仅自动收集模式
- Boss命令支持
- PRD生成

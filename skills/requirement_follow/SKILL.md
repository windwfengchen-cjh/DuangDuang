# Requirement Follow Skill v1.1.0

## 需求跟进流程系统

### 系统概述

本 Skill 用于管理从飞书消息中捕获的需求，并建立完整的跟进流程，包括：需求记录、重复检测、调研群创建、需求调研、PRD生成等。

### 依赖

- Bitable: 需求跟进清单 (app_token: Op8WbbFewaq1tasfO8IcQkXmnFf, table_id: tbl0vJo8gPHIeZ9y)
- 飞书群组管理 API
- superpowers skill (调研能力)
- prd-document skill (PRD生成)

### 表格字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 需求内容 | Text | 需求描述 |
| 需求状态 | SingleSelect | 待跟进、跟进中、已完成 |
| 需求时间 | DateTime | 需求提出时间 |
| 来源群 | Text | 原消息所在群名称 |
| 来源群ID | Text | 原消息所在群 chat_id |
| 需求方 | Text | 需求提出人 |
| 需求方ID | Text | 需求提出人 open_id |
| 调研群名称 | Text | 新建调研群名称 |
| 调研群ID | Text | 新建调研群 chat_id |
| 原始消息ID | Text | 引用的消息ID |
| PRD文档链接 | URL | 生成的需求文档链接 |

---

## 流程说明

### 触发条件

| 阶段 | 触发指令 | 说明 |
|------|----------|------|
| 启动需求跟进 | "跟进这个需求" / "跟进需求" / "记录这个需求" | Boss 引用需求方消息后触发 |
| 执行调研 | "开始调研" / "开始分析" / "调研一下" / "分析一下" | 在调研群触发调研流程 |
| 生成 PRD | "生成PRD" / "完成调研" / "写需求文档" / "写PRD" | 在调研群触发 PRD 生成 |
| 取消需求 | "取消" / "不做了" / "暂停" | 取消当前需求跟进 |

### 完整流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                     需求跟进流程                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. 消息捕获                                                      │
│    - 监听 Boss 指令 "跟进这个需求"                                  │
│    - 提取原消息：发送人、内容、时间、群信息                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. 重复需求检测                                                   │
│    - 基于需求内容相似度匹配                                        │
│    - 相似度 > 85% 视为重复需求                                     │
│    - 如发现重复，提示已有跟进记录                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │ 重复                          │ 不重复
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────────────────┐
│ 返回已有记录链接          │     │ 3. 创建需求记录                      │
│ 提示关注现有跟进          │     │    - 状态: 待跟进                    │
└─────────────────────────┘     │    - 记录所有来源信息                 │
                                └─────────────────────────────────────┘
                                                  │
                                                  ▼
                                ┌─────────────────────────────────────┐
                                │ 4. 创建调研群                        │
                                │    - 群名: "需求调研-[需求方]-[日期]"  │
                                │    - 自动拉取需求方和Boss              │
                                └─────────────────────────────────────┘
                                                  │
                                                  ▼
                                ┌─────────────────────────────────────┐
                                │ 5. 更新需求记录                      │
                                │    - 状态: 跟进中                    │
                                │    - 记录调研群信息                   │
                                └─────────────────────────────────────┘
                                                  │
                                                  ▼
                                ┌─────────────────────────────────────┐
                                │ 6. 发送引导消息                      │
                                │    - 说明调研目的                     │
                                │    - @需求方 请补充详细信息            │
                                └─────────────────────────────────────┘
                                                  │
                                                  ▼
                                ┌─────────────────────────────────────┐
                                │ 7. 监控调研群 (持续监听)              │
                                │    - 收集需求方的补充信息              │
                                │    - Boss 说"开始调研"时触发           │
                                └─────────────────────────────────────┘
                                                  │
                                                  ▼
                                ┌─────────────────────────────────────┐
                                │ 8. 执行调研 (superpowers skill)      │
                                │    - 分析完整需求背景                  │
                                │    - 竞品分析、用户场景分析             │
                                └─────────────────────────────────────┘
                                                  │
                                                  ▼
                                ┌─────────────────────────────────────┐
                                │ 9. 生成PRD (prd-document skill)      │
                                │    - 基于调研结果生成需求文档           │
                                │    - 输出到飞书文档                    │
                                └─────────────────────────────────────┘
                                                  │
                                                  ▼
                                ┌─────────────────────────────────────┐
                                │ 10. 完成跟进                         │
                                │    - 状态: 已完成                    │
                                │    - 记录PRD链接                     │
                                │    - 发送完成通知                     │
                                └─────────────────────────────────────┘
```

---

## 重复需求检测逻辑

### 算法

```python
def check_duplicate_requirement(content: str, threshold: float = 0.85) -> Optional[Dict]:
    """
    检测重复需求
    
    1. 从 Bitable 查询所有"待跟进"或"跟进中"的需求
    2. 使用文本相似度算法（Jaccard 或余弦相似度）计算相似度
    3. 返回相似度最高的记录（如果超过阈值）
    
    相似度计算：
    - 分词：使用 jieba 中文分词
    - 向量化：TF-IDF
    - 相似度：余弦相似度
    """
    # 实现见 requirement_follow.py
```

### 判定标准

- **完全重复** (相似度 > 95%): 直接返回已有记录
- **高度相似** (相似度 85%-95%): 提示可能重复，询问是否创建新记录
- **新需求** (相似度 < 85%): 正常创建新记录

---

## 创建调研群步骤

### 群名称规则

```
需求调研-{需求方姓名}-{YYYYMMDD}
```

示例：`需求调研-张三-20260323`

### 群成员

1. **需求方** (自动拉取)
2. **Boss** (创建者，自动拉取)
3. **机器人** (自动加入)

### 群描述

```
📋 需求调研群

需求内容：{需求内容摘要}
来源群：{来源群名称}

本群用于深入沟通需求细节，请需求方补充：
1. 需求的背景和痛点
2. 期望的解决方案
3. 优先级和时间要求

Boss 可在确认信息充分后说"开始调研"触发调研流程。
```

---

## 监控调研群消息规则

### 监听规则

```python
# 持续监听调研群消息
# 触发条件：
TRIGGER_WORDS = {
    "follow_requirement": ["跟进这个需求", "跟进需求", "记录这个需求"],
    "start_research": ["开始调研", "开始分析", "调研一下", "分析一下"],
    "generate_prd": ["生成PRD", "生成prd", "完成调研", "写需求文档", "开始写PRD", "写PRD"],
    "add_context": ["补充一下", "详细说明", "背景是"],
    "urgent": ["紧急", "加急", "尽快"],
    "cancel": ["取消", "不做了", "暂停"]
}
```

### PRD 生成触发

当 Boss 在调研群说以下任一指令时触发 PRD 生成：
- "生成PRD" / "生成prd"
- "完成调研"
- "写需求文档"
- "开始写PRD" / "写PRD"

执行流程：

```python
elif is_trigger_word(message, "generate_prd"):
    # 1. 收集调研群所有历史消息
    chat_history = get_chat_history(chat_id)

    # 2. 整理上下文
    context = format_chat_context(chat_history)

    # 3. 调用 PRD 生成
    result = complete_requirement_follow(
        requirement_id=requirement_id,
        chat_context=context
    )

    # 4. 发送完成通知到调研群
    notify_group(f"✅ 需求调研已完成\nPRD文档: {result['prd_path']}")
```

### 消息处理

```python
async def handle_research_chat_message(event):
    """
    处理调研群消息

    1. 记录所有消息到上下文（用于后续调研分析）
    2. 检测触发词
    3. 执行对应操作
    """
    message = event.message

    if is_trigger_word(message, "start_research"):
        # Boss 触发调研
        await conduct_research(requirement_id)

    elif is_trigger_word(message, "generate_prd"):
        # 生成 PRD 文档
        result = await complete_requirement_follow(requirement_id)
        await notify_group(f"✅ PRD已生成: {result['prd_path']}")

    elif is_trigger_word(message, "cancel"):
        # 取消需求
        await update_requirement_status(requirement_id, "已取消")
        await notify_group("❌ 需求已取消")
```

---

## 使用 superpowers 调研

### 调研触发

当 Boss 在调研群说"开始调研"时，系统：

1. 收集调研群所有历史消息作为上下文
2. 调用 superpowers skill 进行深度调研
3. 调研维度：
   - 需求背景分析
   - 用户痛点挖掘
   - 竞品分析
   - 可行性评估
   - 实现建议

### 调研输出

```json
{
  "research_summary": "调研总结",
  "user_pain_points": ["痛点1", "痛点2"],
  "competitor_analysis": "竞品分析结果",
  "feasibility": "可行性评估",
  "recommendations": ["建议1", "建议2"],
  "key_questions": ["待确认问题1"]
}
```

---

## 生成 PRD 文档流程（2026-03-23 更新）

### 触发条件

当 Boss 在调研群说以下任一指令时触发 PRD 生成流程：

| 触发词 | 示例 |
|--------|------|
| 生成PRD | "生成PRD" / "生成prd" |
| 完成调研 | "完成调研" |
| 写需求文档 | "写需求文档" |
| 写PRD | "开始写PRD" / "写PRD" |

**完整触发词列表**：
```python
"generate_prd": ["生成PRD", "生成prd", "完成调研", "写需求文档", "开始写PRD", "写PRD"]
```

### PRD 生成流程

```
Boss: "生成PRD" / "完成调研"
  │
  ▼
系统: 调用 complete_requirement_follow(requirement_id, chat_context)
  │
  ├── 1. 调用 generate_prd_document()
  │       ├── 获取飞书凭证和 tenant_access_token
  │       ├── 从 Bitable 获取需求记录详情
  │       ├── 提取需求内容、需求方、来源群等信息
  │       ├── 构建 PRD Markdown 内容
  │       │       ├── 需求信息表格 (ID、需求方、来源群、创建日期)
  │       │       ├── 需求描述
  │       │       ├── 调研补充信息 (chat_context)
  │       │       └── 占位章节 (背景、目标、方案、验收标准)
  │       ├── 确保 docs/prd 目录存在
  │       └── 保存到 docs/prd/requirement-{id}.md
  │
  ├── 2. 更新需求状态
  │       └── 调用 update_requirement_status()
  │           ├── 状态更新为 "已完成"
  │           └── PRD 文档链接写入 "PRD文档链接" 字段
  │
  └── 3. 发送完成通知到调研群
          └── 消息内容包含 PRD 路径和状态更新信息
  │
  ▼
返回: {"success": True, "prd_path": "...", "requirement_id": "..."}
```

### PRD 文档内容

生成的 PRD 文档为 Markdown 格式，包含以下章节：

| 章节 | 内容 | 来源 |
|------|------|------|
| 需求信息 | 需求ID、需求方、来源群、创建日期 | Bitable 需求记录表 |
| 需求描述 | 原始需求内容 | Bitable 需求记录表 |
| 调研补充信息 | 调研群聊天记录整理 | 调研群消息上下文 |
| 背景 | 业务背景、用户痛点 | （模板占位，待人工补充） |
| 目标 | 期望达成的业务目标 | （模板占位，待人工补充） |
| 方案 | 产品方案、功能设计 | （模板占位，待人工补充） |
| 验收标准 | 可验证的验收条件 | （模板占位，待人工补充） |

### 文档保存路径

```
docs/prd/requirement-{requirement_id}.md
```

示例：`docs/prd/requirement-recvexxxxx.md`

### API 使用

**生成 PRD**:
```python
from requirement_follow import complete_requirement_follow, generate_prd_document

# 方式1: 直接生成 PRD
result = generate_prd_document(
    requirement_id="recvexxxxx",
    chat_context="调研群聊天记录整理..."
)

# 方式2: 完成整个跟进流程（生成 PRD + 发送通知）
result = complete_requirement_follow(
    requirement_id="recvexxxxx",
    chat_context="调研群聊天记录整理..."
)

# 返回结果
{
    "success": True,
    "prd_path": "docs/prd/requirement-recvexxxxx.md",
    "requirement_id": "recvexxxxx"
}
```

**命令行**:
```bash
# 完成需求跟进（生成 PRD）
python requirement_follow.py complete <requirement_id>

# 启动新的需求跟进（测试模式）
python requirement_follow.py
```

---

## 状态流转规则

```
待跟进 ──(创建调研群)──> 跟进中 ──(生成PRD)──> 已完成
   │                        │
   └──(发现重复)──> 已合并   └──(取消)──> 已取消
```

| 状态 | 说明 | 可流转到 |
|------|------|----------|
| 待跟进 | 刚创建，未开始调研 | 跟进中、已合并、已取消 |
| 跟进中 | 已创建调研群，正在沟通 | 已完成、已取消 |
| 已完成 | PRD 已生成 | - |
| 已合并 | 与已有需求合并 | - |
| 已取消 | 需求取消 | - |

---

## 使用示例

### 触发需求跟进

**Boss 在群聊中：**
> 跟进这个需求
> [引用某条消息]

**系统自动：**
1. 创建需求记录
2. 创建调研群 `需求调研-张三-20260323`
3. 拉取需求方和 Boss
4. 发送引导消息

### 执行调研

**Boss 在调研群：**
> 开始调研

**系统自动：**
1. 收集群聊上下文
2. 调用 superpowers 进行深度调研
3. 生成调研报告（包含背景分析、痛点挖掘、竞品分析等）

### 生成 PRD 文档

**Boss 在调研群（调研信息充分后）：**
> 生成PRD

或

> 完成调研

**系统自动：**
1. 收集调研群所有聊天记录作为上下文
2. 调用 `complete_requirement_follow(requirement_id, chat_context)`
3. 内部调用 `generate_prd_document()`:
   - 从 Bitable 获取需求记录
   - 生成 Markdown 格式 PRD（包含需求信息、需求描述、调研补充、背景、目标、方案、验收标准等章节）
   - 保存到 `docs/prd/requirement-{id}.md`
4. 更新需求状态为"已完成"
5. 记录 PRD 文档链接到需求表的"PRD文档链接"字段
6. 发送完成通知到调研群：
   > ✅ 需求调研已完成
   > PRD文档已生成: docs/prd/requirement-recvexxxxx.md
   > 需求状态已更新为: 已完成

---

## 长时监听模式（2026-03-26 新增）

### 方案A：独立子智能体 + 父进程监控（推荐）

**解决什么问题：**
- 原有方案：子智能体启动后立即退出，群内消息无人监听
- 新方案：子智能体保持运行（最长24小时），持续监听群内消息

**实现方式：**

```typescript
// 派子智能体时设置24小时超时
sessions_spawn({
  task: "使用 requirement-follow skill 启动长时监听...",
  timeoutSeconds: 86400,  // 24小时
  ...
});
```

**Skill 内部实现：**

1. **启动工作流**（创建群、发送欢迎消息）
2. **进入长时监听模式** `runLongRunningListener(chatId)`
   - 每5秒轮询一次消息
   - 每5分钟发送心跳（输出到日志）
   - 处理问答流程
   - 24小时自动超时或收到结束指令后退出

**使用方式：**

```bash
# 启动工作流并进入长时监听模式
node dist/index.js \
  -c "需求内容" \
  -r "张三" \
  -rid "ou_xxx" \
  -cid "oc_xxx" \
  -cn "测试群" \
  -l  # --long-running 参数
```

**子智能体任务描述示例：**

```markdown
你现在是"豆浆"，需求跟进专员。

**任务**：使用 requirement-follow skill 跟进需求并启动长时监听

**执行要求**：
- 必须使用 requirement-follow skill
- 调用 startWorkflow() 启动工作流
- 工作流成功后，调用 runLongRunningListener() 进入长时监听模式
- 保持运行直到调研完成（最长24小时）

**超时设置**：
- 子智能体超时：24小时（86400秒）
- 监听心跳间隔：5分钟
- 消息轮询间隔：5秒

**返回格式**：
```
✅ 需求跟进已启动（长时监听模式）
📋 记录ID: {record_id}
💬 调研群: {chat_name} ({chat_id})
⏰ 监听时长: 24小时或直到调研完成
```

### 多调研群并发

每个调研群由独立的子智能体监听，完全隔离：

```
调研群A (oc_xxx)  →  子智能体A  →  完全独立，24小时监听
调研群B (oc_yyy)  →  子智能体B  →  完全独立，24小时监听
调研群C (oc_zzz)  →  子智能体C  →  完全独立，24小时监听
```

**优势：**
- ✅ 一个群崩溃/超时不影响其他群
- ✅ 可以单独查看每个子智能体的日志
- ✅ 便于问题定位

---

## 文件清单

| 文件 | 说明 |
|------|------|
| `/home/admin/openclaw/workspace/skills/requirement_follow/SKILL.md` | 本文件，流程文档 (v1.1.0) |
| `/home/admin/openclaw/workspace/requirement_follow.py` | 核心实现代码 |

## 核心函数说明

| 函数 | 功能 | 说明 |
|------|------|------|
| `start_requirement_follow(event)` | 启动需求跟进 | 重复检测、创建记录、创建调研群、添加成员、发送引导消息 |
| `generate_prd_document(requirement_id, chat_context)` | 生成 PRD 文档 | 获取需求、生成 Markdown、保存文件、更新状态 |
| `complete_requirement_follow(requirement_id, chat_context)` | 完成需求跟进 | 调用 generate_prd + 发送完成通知 |
| `find_similar_requirement(content, token, app_token, table_id, threshold=0.85)` | 重复需求检测 | 基于关键词 Jaccard 相似度 |
| `create_research_chat(requirement_id, content, requester_name, token)` | 创建调研群 | 群名格式: 需求调研-{姓名}-{日期} |
| `update_requirement_status(record_id, status, prd_link, token, app_token, table_id)` | 更新需求状态 | 更新状态和 PRD 链接 |

## 配置参数

```python
# Bitable 配置
REQUIREMENT_TABLE_ID = "tbl0vJo8gPHIeZ9y"
BITABLE_APP_TOKEN = "Op8WbbFewaq1tasfO8IcQkXmnFf"
BITABLE_TABLE_ID = "tbl0vJo8gPHIeZ9y"
BOSS_ID = "ou_3e48baef1bd71cc89fb5a364be55cafc"

# 重复检测阈值
SIMILARITY_THRESHOLD = 0.85

# 触发词配置
TRIGGER_WORDS = {
    "follow_requirement": ["跟进这个需求", "跟进需求", "记录这个需求"],
    "start_research": ["开始调研", "开始分析", "调研一下", "分析一下"],
    "generate_prd": ["生成PRD", "生成prd", "完成调研", "写需求文档", "开始写PRD", "写PRD"],
    "add_context": ["补充一下", "详细说明", "背景是"],
    "urgent": ["紧急", "加急", "尽快"],
    "cancel": ["取消", "不做了", "暂停"]
}
```

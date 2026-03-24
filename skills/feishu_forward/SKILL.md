---
skill_id: feishu_forward
version: 1.3.0
description: 飞书群消息转发与@高亮规范（严格版）
---

# 飞书群消息转发与@高亮规范（严格版）

## 🔴 核心工作模式（2026-03-23 强制执行）

### 所有任务必须派子智能体（防呆机制 #1）

**绝对禁止：在主会话中直接执行任务！**

无论任务大小、简单或复杂，**一律通过 `sessions_spawn` 派发子智能体处理**。

> **防呆原理**：通过强制派生子智能体，避免主会话上下文膨胀、任务边界模糊、错误难以追溯等问题。子智能体失败不影响主会话，且每个任务有独立执行记录。

| 场景 | 错误做法 | 正确做法 |
|------|----------|----------|
| 数据查询 | ❌ 直接查询Bitable | ✅ 派子智能体查询 |
| 数据修复 | ❌ 直接update_record | ✅ 派子智能体修复 |
| 发送消息 | ❌ 直接send_message | ✅ 派子智能体发送 |
| 文件操作 | ❌ 直接read/write | ✅ 派子智能体处理 |
| 脚本执行 | ❌ 直接exec执行 | ✅ 派子智能体执行 |

**为什么要派子智能体：**
1. **隔离性**：子任务失败不影响主会话
2. **专注性**：子智能体专注处理单一任务
3. **效率性**：避免主会话上下文膨胀
4. **可追溯性**：每个子任务有独立的执行记录

**违规后果**：在主会话直接执行任务会导致上下文膨胀、任务边界模糊、错误难以追溯。

---

## ⚠️ 重要警告

**绝对禁止：使用纯文本格式发送带@的消息！**

纯文本格式 `<at id="ou_xxx"></at>` **永远不会高亮**，必须使用 Post 消息格式。

### 消息格式深度解析（2026-03-23 更新）

#### Text vs Post 格式的本质区别

| 维度 | Text 格式 | Post 格式 |
|------|-----------|-----------|
| **@高亮** | ❌ 完全不支持 | ✅ 原生支持 |
| **富文本** | ❌ 纯文本 | ✅ 支持多种元素 |
| **语法** | 纯字符串 | JSON结构化数据 |
| **使用场景** | 简单通知、机器人日志 | 需要@人或格式化展示 |

#### 为什么 `<at id="...">` 在Text消息中不会高亮

**误区**：很多人认为 `<at id="ou_xxx"></at>` 是飞书的"@语法"

**真相**：
1. 这是飞书客户端**内部使用的HTML标记**，不是API的公开语法
2. 通过API发送时，这种HTML被当做**纯文本**显示
3. 只有Post消息的 `{"tag": "at", ...}` 格式才能触发真正的@功能

**对比示例**：

```python
# ❌ 错误 - Text消息中的HTML@标签
{
    "msg_type": "text",
    "content": {
        "text": "请查看 <at id='ou_82e152d737ab5aedee7110066828b5a1'></at>"
    }
}
# 实际显示: "请查看 <at id='ou_82e152d737ab5aedee7110066828b5a1'></at>"
# @不会高亮，显示为原始HTML字符串

# ✅ 正确 - Post消息中的@标签
{
    "msg_type": "post",
    "content": {
        "zh_cn": {
            "title": "提醒",
            "content": [
                [{"tag": "text", "text": "请查看 "}],
                [{"tag": "at", "user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "施嘉科"}]
            ]
        }
    }
}
# @会高亮，显示为蓝色可点击的@施嘉科
```

#### 客户端 vs API 的差异

**飞书客户端**（用户手动输入）：
- 输入 `@施嘉科` → 客户端自动转换为内部格式 → 显示为高亮

**飞书API**（程序发送）：
- 必须使用 Post 消息的 `{"tag": "at", ...}` 格式
- 不能使用 HTML 格式
- 不能依赖客户端的自动转换

## 群内响应规则（强制）

### 被@时的行为准则

| 场景 | 正确做法 | 禁止行为 |
|------|---------|---------|
| **被@反馈问题** | ✅ 默默记录到问题反馈表，**不回复任何消息** | ❌ 发送"正在记录..."、"已记录到表格"等过程消息 |
| **问题已记录** | ✅ 静默处理，通过转发目标群通知处理人 | ❌ 在源群回复确认消息 |
| **需要澄清** | ✅ 转发到目标群@处理人，由处理人跟进 | ❌ 在源群与反馈人讨论 |

**核心原则**：
- 在源群（业务群）中**只监听、不发言**
- 所有响应和通知都通过**转发到目标群**完成
- **绝不**在业务群发送任何解释性、确认性消息

## 核心规则

### 1. 消息格式选择（强制）

| 格式 | 是否支持@高亮 | 使用场景 |
|------|--------------|---------|
| **Post** | ✅ 支持 | 所有需要@人的消息 |
| **Text** | ❌ 不支持 | 仅用于无@的纯文本通知 |

**正确示例（Post格式）**：
```python
{
    "msg_type": "post",
    "content": {
        "zh_cn": {
            "title": "【产研反馈-问题】",
            "content": [
                [{"tag": "text", "text": "问题描述..."}],
                [
                    {"tag": "at", "user_id": "ou_xxx", "user_name": "姓名"},
                    {"tag": "text", "text": " 请查看~"}
                ]
            ]
        }
    }
}
```

**错误示例（Text格式 - 禁止用于@消息）**：
```python
{
    "msg_type": "text",
    "content": {"text": "【产研反馈-问题】... <at id='ou_xxx'></at> 请查看"}
}
# ❌ 这种格式@永远不会高亮！
```

### 2. @高亮关键字段（强制）

**必须同时包含 `user_id` 和 `user_name`**

```python
# ✅ 正确 - 会高亮
{"tag": "at", "user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "施嘉科"}

# ❌ 错误 - 缺少user_name，不会高亮
{"tag": "at", "user_id": "ou_82e152d737ab5aedee7110066828b5a1"}
```

### 3. 转发配置映射

| 来源群 | 来源群ID | 目标群 | 目标群ID | @处理人 |
|--------|----------|--------|----------|---------|
| 产研-融合业务组 | `oc_469678cc3cd264438f9bbb65da534c0b` | 猛龙队开发 | `oc_a016323a9fda4263ab5a27976065088e` | 施嘉科、宋广智 |
| 号卡&宽带需求和酬金系统体系搭建 | `oc_3b4215cdadcc9366c863377561ce00c5` | 猛龙队开发 | `oc_a016323a9fda4263ab5a27976065088e` | 施嘉科、宋广智 |
| 线下号卡-信息流投放上报沟通 | `oc_ee55ec5275cc158b826fe1204d75cf2c` | 猛龙队开发 | `oc_a016323a9fda4263ab5a27976065088e` | 施嘉科 |
| 号卡能力中心信息同频群 | `oc_5bf7336955740fb41ba59e4e929c5239` | 配置4目标群 | `oc_cf3c4adafb332df5988b20204c272dbb` | 施嘉科、郑武友、陈俊洪 |

### 4. 处理人ID映射

```json
{
    "ou_82e152d737ab5aedee7110066828b5a1": "施嘉科",
    "ou_cbcd1090961b620a4500ce68e3c81952": "宋广智",
    "ou_834914563c797190697ca36b074a6952": "郑武友",
    "ou_3e48baef1bd71cc89fb5a364be55cafc": "陈俊洪"
}
```

## 完整转发示例

```python
import json

# 构造Post消息内容
content_blocks = [
    [{"tag": "text", "text": "📍 问题来源：号卡能力中心信息同频群"}],
    [{"tag": "text", "text": "👤 反馈人：严欣欣"}],
    [{"tag": "text", "text": "📌 问题类型：问题/Bug"}],
    [{"tag": "text", "text": "问题描述：重庆移动 - 下单失败，也上报"}],
    [{"tag": "text", "text": ""}],
    [
        {"tag": "at", "user_id": "ou_82e152d737ab5aedee7110066828b5a1", "user_name": "施嘉科"},
        {"tag": "text", "text": " "},
        {"tag": "at", "user_id": "ou_cbcd1090961b620a4500ce68e3c81952", "user_name": "宋广智"},
        {"tag": "text", "text": " 请查看~"}
    ]
]

message_content = {
    "zh_cn": {
        "title": "【产研反馈-问题】",
        "content": content_blocks
    }
}

payload = {
    "receive_id": "oc_a016323a9fda4263ab5a27976065088e",
    "msg_type": "post",
    "content": json.dumps(message_content, ensure_ascii=False)
}
```

## 检查清单（发送前必须逐项确认）

- [ ] **使用 `msg_type: "post"` 格式**（禁止text格式用于@消息）
- [ ] **@标签包含 `user_id` 和 `user_name`**（两个字段都必须有）
- [ ] **根据来源群选择正确的目标群**
- [ ] **@的处理人符合配置映射表**
- [ ] **已验证API返回中包含 `mentions` 字段**（这是高亮成功的标志）

## 常见错误案例

### 错误1：使用纯文本格式
```python
# ❌ 错误 - @不会高亮
message = "【产研反馈-问题】... <at id='ou_xxx'></at> 请查看"
send_message(msg_type="text", content={"text": message})
```

### 错误2：缺少user_name
```python
# ❌ 错误 - @不会高亮
{"tag": "at", "user_id": "ou_xxx"}  # 缺少user_name
```

### 错误3：user_id为空
```python
# ❌ 错误 - 配置4郑武友曾出现此问题（已修复）
{"user_id": "", "user_name": "郑武友"}
```

### 错误4：换行符不生效（2026-03-23 新增）
```python
# ❌ 错误 - 把带\n的字符串直接放入text，换行不会生效
content = "第一行\n第二行\n第三行"
content_blocks.append([{"tag": "text", "text": content}])
# 结果：所有内容显示在一行，\n被当做普通字符

# ✅ 正确 - 按行拆分，每行一个text元素
lines = content.split('\n')
for line in lines:
    content_blocks.append([{"tag": "text", "text": line}])
# 结果：每行独立显示，换行正常
```
**教训**：2026-03-23 `auto_forward.py` 因未拆分换行符导致消息内容挤在一行显示。

### 错误5：使用Markdown语法（2026-03-23 新增）

### 错误4：使用Markdown语法（2026-03-23 新增）
```python
# ❌ 错误 - Post消息不支持Markdown，**不会被解析为粗体
lines = ["**严重超时提醒**", "**问题标题**"]
content_blocks = [[{"tag": "text", "text": "\n".join(lines)}]]
# 结果：**显示为纯文本**，且可能影响@高亮

# ✅ 正确 - 使用纯文本（飞书API的style属性有问题，不建议使用）
content_blocks = [
    [{"tag": "text", "text": "🚨 严重超时提醒"}],
    [{"tag": "text", "text": "1. 问题标题"}]
]
```
**教训**：2026-03-23 `check_overdue_issues.py` 因使用 `**粗体**` Markdown语法导致@不高亮。

### 错误5：使用style属性（2026-03-23 新增）
```python
# ❌ 错误 - style属性会导致HTTP 400错误
{"tag": "text", "text": "粗体文字", "style": {"bold": True}}
# 结果：HTTP Error 400: invalid message content

# ❌ 错误 - 即使auto_forward.py里有style，实际API返回也是style: []
# 说明服务器会清空或拒绝style属性

# ✅ 正确 - 不使用style，用符号代替高亮
{"tag": "text", "text": "【重要】普通文字"}  # 用【】代替加粗
{"tag": "text", "text": "🚨 提醒文字"}       # 用emoji代替样式
```
**教训**：2026-03-23 测试发现飞书API对text标签的`style`属性支持有问题，应避免使用。  
**注意**：`auto_forward.py` 代码中虽有 `style: {"bold": True}`，但实际API返回的是 `style: []`，说明服务器会忽略或清空该属性。

## 数据录入规范（强制）

### 时间戳校验规则

**写入Bitable「反馈时间」字段前必须执行以下校验：**

```python
from datetime import datetime, timedelta

def validate_feedback_timestamp(timestamp_ms: int) -> tuple[bool, str]:
    """
    校验反馈时间戳是否合理
    返回: (是否通过, 错误信息)
    """
    now = datetime.now()
    feedback_time = datetime.fromtimestamp(timestamp_ms / 1000)
    
    # 规则1: 不能是未来时间
    if feedback_time > now + timedelta(minutes=5):
        return False, f"反馈时间不能是未来: {feedback_time}"
    
    # 规则2: 不能超过30天（可能是历史数据复制错误）
    if feedback_time < now - timedelta(days=30):
        return False, f"反馈时间超过30天前: {feedback_time}，可能是复制了旧记录"
    
    return True, "通过"
```

**校验失败时的处理：**
- ❌ **禁止直接写入**错误的时间戳
- ✅ **立即提醒Boss**："发现异常时间戳，请确认是否为复制旧记录导致"
- ✅ **使用当前时间**：如果确认是误操作，使用 `int(time.time() * 1000)` 生成正确的时间戳

### 典型案例

**错误案例：复制旧记录导致时间错误**
```python
# ❌ 错误 - 直接复制旧记录的时间戳
old_record = get_record("rec_old_id")
new_fields = {
    "反馈时间": old_record["反馈时间"],  # 错误！复制了2025年的时间
    "问题内容": "新的问题描述"
}
create_record(new_fields)  # 结果：新问题被标记为2025年的记录
```

**正确做法**
```python
# ✅ 正确 - 使用当前时间
import time
new_fields = {
    "反馈时间": int(time.time() * 1000),  # 正确！使用当前时间戳
    "问题内容": "新的问题描述"
}
create_record(new_fields)
```

## 写入后验证（必须）

**创建/更新记录后，必须读取验证关键字段：**

```python
def create_and_verify_record(fields: dict) -> dict:
    """创建记录并验证写入结果"""
    record_id = create_record(fields)
    
    # 必须验证：读取刚创建的记录
    verify_record = get_record(record_id)
    
    # 验证反馈时间
    written_time = verify_record["fields"].get("反馈时间")
    expected_time = fields["反馈时间"]
    
    written_dt = datetime.fromtimestamp(written_time / 1000)
    now = datetime.now()
    
    # 如果写入的时间超过7天前，立即警告
    if (now - written_dt).days > 7:
        raise Warning(f"写入的时间异常: {written_dt}，可能是数据错误")
    
    return verify_record
```

## 补充反馈处理规则（2026-03-23 新增）

### ⚠️ 重要：补充信息应该更新而非新建

**规则**：收到关于同一问题的补充反馈时，**必须更新原记录**，禁止创建新记录。

#### 什么是补充反馈

| 特征 | 说明 |
|------|------|
| **同一问题** | 与已记录问题属于同一现象/根因 |
| **新增信息** | 提供额外的订单号、截图、描述等 |
| **不同反馈人** | 可能由其他人补充信息 |
| **时间接近** | 通常在短时间内（几天内）补充 |

#### 处理流程

```
收到反馈
    ↓
搜索Bitable是否存在相似/相关问题
    ↓
存在相关记录？
    ├─ 是 → 更新原记录（追加信息）
    │         - 更新"问题内容"追加新信息
    │         - 更新"反馈人"添加新反馈人
    │         - 更新"备注"添加补充说明
    │         - 记录"原始消息ID"如果有新消息
    └─ 否 → 创建新记录
```

#### 典型案例（2026-03-23）

**错误做法**：
```
第21条：何镇浩反馈"俊子云状态更新延迟"
第24条：曹敏补充"俊子云订单状态未回调" + 两个订单号

❌ 错误：为同一问题的补充创建了第24条新记录
```

**正确做法**：
```
第21条：合并何镇浩和曹敏的反馈
- 反馈人：何镇浩、曹敏
- 问题内容：包含原问题 + 曹敏补充的订单号
- 备注：记录所有相关信息

✅ 正确：曹敏的补充更新到第21条，不创建新记录
```

#### 如何判断是否应该更新

检查以下字段是否匹配：
- [ ] **问题关键词**（如"俊子云"、"状态更新"）
- [ ] **涉及系统/产品**（如"广州电信"、"特定PD编号"）
- [ ] **时间范围**（几天内的反馈通常相关）
- [ ] **反馈来源**（同一渠道的相关性更高）

**不确定时**：先询问Boss "这条反馈是否应该更新到记录XXX？

### ⚠️ 重要：处理状态字段受控管理

**绝对禁止**：私自新增或修改「处理状态」字段的选项值。

#### 当前允许的处理状态

| 状态值 | 含义 | 超时提醒规则 |
|--------|------|-------------|
| **待处理** | 新反馈，尚未开始处理 | ✅ 1小时群提醒 + 3天严重超时提醒 |
| **处理中** | 已开始处理 | ✅ 1小时群提醒 + 3天严重超时提醒 |
| **紧急处理中** | 紧急处理中（高优先级） | ✅ 1小时群提醒 + 3天严重超时提醒 |
| **已解决** | 问题已解决 | ❌ 不需要提醒 |
| **已关闭** | 反馈已关闭 | ❌ 不需要提醒 |

#### 新增处理状态的流程

如果需要新增状态（如"待验证"、"挂起"等）：

1. **先询问Boss**："需要新增处理状态'xxx'，请确认"
2. **确认超时规则**：该状态是否需要超时提醒？
3. **更新脚本**：修改 `check_overdue_issues.py` 中的状态过滤逻辑
4. **更新文档**：在skill中记录新状态的规则

**违规后果**：私自新增状态会导致超时提醒逻辑异常，可能漏提醒或误提醒。

### 时间戳错误修复记录（2026-03-23 新增）

**问题现象**：Bitable中出现时间戳错误的记录
- 第21条：时间戳为 `1742694840000`（2025-03-23），实际应为2026年
- 第22条：时间戳为 `null`，实际应为今天

**根本原因分析**：
1. `auto_forward.py` 使用 `int(time.time() * 1000)` 生成时间戳，理论上正确
2. 但第21条显示2025年时间，可能是：
   - 系统时间被临时设置为2025年
   - 或 `auto_forward.py` 在某些情况下使用了缓存/硬编码的时间
3. 第22条显示null，可能是字段映射错误或API返回异常

**修复方案**：
1. **发现时间错误时**：
   - ✅ **派子智能体处理**（推荐）：`sessions_spawn` 创建一个子任务来批量修复
   - ✅ **手动修复**：使用 `feishu_bitable_update_record` 更新单个记录
   
2. **修复后验证**：
   ```python
   # 修复后必须读取验证
   updated_record = get_record(record_id)
   new_time = updated_record['fields']['反馈时间']
   new_dt = datetime.fromtimestamp(new_time / 1000)
   print(f"修复后时间: {new_dt}")  # 确认是今天
   ```

3. **预防措施**：
   - `auto_forward.py` 创建记录后，立即读取验证反馈时间
   - 如果检测到异常时间（如超过1年前），立即告警

**为什么应该派子智能体**：
- 批量修复涉及多条记录，适合独立任务
- 避免主会话上下文膨胀
- 子任务可以专注处理数据修复，不影响主流程

### 时间记录修复（2026-03-23 新增）

**问题现象**：
1. 更新补充记录时，原始"反馈时间"可能被修改
2. 新创建记录时，"反馈时间"字段未正确写入

**根本原因**：
- `update_record_with_supplement()` 函数中可能意外修改了"反馈时间"
- 字段映射错误或时间戳生成问题

**修复方案**（已在 `auto_forward.py` 中实现）：

1. **更新记录时不修改反馈时间**：
   ```python
   def update_record_with_supplement(record_id, new_content, new_reporter, ...):
       # ⚠️ 重要：不要包含"反馈时间"字段，必须保留原始时间！
       update_fields = {}
       
       # 只更新这些字段，不包含"反馈时间"
       update_fields['问题内容'] = updated_content
       update_fields['反馈人'] = updated_reporter
       update_fields['备注'] = updated_remark
       # ... 其他字段，但不包括"反馈时间"
   ```

2. **新记录使用正确时间戳**：
   ```python
   fields = {
       "反馈时间": int(time.time() * 1000),  # 毫秒级时间戳
       # ... 其他字段
   }
   ```

3. **补充时间记录在备注中**：
   ```
   原始备注内容
   ---
   张三于2026-03-23 11:50补充：内容预览...
   ```

**验证方法**：
- 更新记录后，读取验证"反馈时间"未被修改
- 创建记录后，读取验证"反馈时间"为当前时间

### 使用消息实际时间（2026-03-23 新增）

**问题现象**：
- 新记录的"反馈时间"显示为处理时间（当前时间），而非消息实际发送时间
- 例如：3月17号发送的消息，3月23号处理时记录为3月23号

**根本原因**：
- 代码使用 `Date.now()` 或 `time.time()` 生成当前时间戳
- 没有使用飞书消息的 `create_time` 字段

**修复方案**：

1. **Python 版本** (`auto_forward.py`):
   ```python
   def forward_feedback(..., message_time=None):
       # 优先使用消息时间，其次使用当前时间
       if message_time and message_time > 0:
           # message_time 是秒级，转换为毫秒
           feedback_timestamp = int(message_time * 1000)
       else:
           feedback_timestamp = int(time.time() * 1000)

       fields = {
           "反馈时间": feedback_timestamp,
           # ... 其他字段
       }
   ```

2. **TypeScript 版本** (`index.ts`):
   ```typescript
   // 使用消息的实际时间（create_time 是秒级字符串）
   const messageTimeMs = parseInt(event.create_time) * 1000;

   await this.bitable.createRecord({
       feedbackTime: messageTimeMs,  // 不是 Date.now()
       // ... 其他字段
   });
   ```

3. **命令行参数支持**:
   ```python
   parser.add_argument('--message-time', type=int, help='消息时间戳（秒级）')

   result = forward_feedback(
       ...,
       message_time=args.message_time
   )
   ```

**使用示例**：
```python
# 从飞书消息事件中获取时间戳（秒级）
message_time = event.get('create_time')  # 例如: 1711536000

# 调用时传入 message_time
result = forward_feedback(
    source_chat="产研-融合业务组",
    reporter="用户姓名",
    content="问题内容",
    message_time=message_time  # 秒级时间戳，会自动转为毫秒
)
```

## 超时提醒规则（2026-03-23 更新）

### 提醒触发条件

| 提醒类型 | 触发条件 | 目标人群 | 需求类型是否提醒 | 提醒频率 |
|----------|----------|----------|-----------------|----------|
| **1小时提醒** | 问题/待处理/处理中状态，超过1小时但不到3天 | 目标群@处理人 | ❌ 需求不提醒 | 每小时检查 |
| **3天严重超时** | 问题/待处理/处理中状态，超过3天 | 目标群@处理人 + 私聊Boss | ❌ 需求不提醒 | **每3小时提醒1次** |

### 严重超时3小时间隔控制机制

**实现方式**：通过Bitable「上次提醒时间」字段控制

```python
def should_send_severe_reminder(fields):
    """判断是否应该发送严重超时提醒（每3小时提醒1次）"""
    last_reminder_time = fields.get('上次提醒时间', None)
    
    if not last_reminder_time:
        # 从未提醒过，应该提醒
        return True
    
    last_dt = parse_datetime(last_reminder_time)
    if not last_dt:
        return True
    
    now = datetime.now()
    elapsed = now - last_dt
    
    # 3小时 = 3 * 60 * 60 秒
    return elapsed.total_seconds() >= 3 * 60 * 60
```

**流程**：
1. 每小时检查一次所有超过3天未处理的记录
2. 检查每条记录的「上次提醒时间」字段
3. 如果从未提醒过，或距上次提醒已超过3小时，则发送提醒
4. 发送成功后，更新「上次提醒时间」为当前时间

**目的**：避免对同一问题频繁提醒，减少干扰，同时确保严重问题得到持续跟进

### 类型判断优先级

**优先使用「类型」字段（单选：问题/需求）**：

```python
def is_need_type(fields):
    """判断是否是需求/建议类 - 优先使用「类型」字段"""
    record_type = fields.get('类型', '')
    if record_type == '需求':
        return True
    if record_type == '问题':
        return False
    
    # 类型字段为空时，通过关键词辅助判断
    content = fields.get('问题内容', '')
    need_keywords = ['需求', '建议', '优化', '改进', '新增', '增加', '功能', '想要', '希望', '能否']
    return any(kw in content.lower() for kw in need_keywords)
```

### 过滤逻辑代码示例

```python
# 1小时超时提醒过滤
for record in records:
    fields = record.get('fields', {})
    status = fields.get('处理状态', '')
    
    # 只处理"待处理"和"处理中"
    if status not in ['待处理', '处理中']:
        continue
    
    # 需求不需要超时提醒
    if is_need_type(fields):
        continue
    
    # 检查是否超过1小时但不到3天...

# 3天严重超时提醒过滤（相同逻辑）
for record in records:
    fields = record.get('fields', {})
    status = fields.get('处理状态', '')
    
    # 只处理"待处理"和"处理中"
    if status not in ['待处理', '处理中']:
        continue
    
    # 需求不需要严重超时提醒
    if is_need_type(fields):
        continue
    
    # 检查是否超过3天...
```

## 防呆机制汇总（防错设计）

### #1 所有任务派子智能体（最高优先级）

**规则**：无论任务大小，一律通过 `sessions_spawn` 派子智能体处理。

**防呆设计**：
- 主会话只负责接收指令和派子任务
- 子智能体专注执行单一任务
- 子任务失败不污染主会话上下文

**违规案例**：
```
❌ 错误 - 主会话直接执行
  me: 检查表格记录
  → 直接执行 feishu_bitable_list_records
  → 结果占用主会话上下文

✅ 正确 - 派子智能体
  me: 派子智能体检查表格
  → sessions_spawn(task="检查表格记录...")
  → 子智能体返回结果
  → 主会话保持干净
```

### #2 Bitable时间戳校验

**规则**：写入「反馈时间」前必须校验时间戳合理性。

**防呆设计**：
```python
def validate_feedback_timestamp(timestamp_ms: int) -> tuple[bool, str]:
    now = datetime.now()
    feedback_time = datetime.fromtimestamp(timestamp_ms / 1000)
    
    # 不能是未来时间
    if feedback_time > now + timedelta(minutes=5):
        return False, "反馈时间不能是未来"
    
    # 不能超过30天（防止复制旧记录）
    if feedback_time < now - timedelta(days=30):
        return False, "反馈时间超过30天前，可能是复制了旧记录"
    
    return True, "通过"
```

### #3 写入后验证

**规则**：创建/更新记录后，必须读取验证关键字段。

**防呆设计**：
```python
def create_and_verify_record(fields: dict) -> dict:
    record_id = create_record(fields)
    verify_record = get_record(record_id)
    
    # 验证反馈时间
    written_time = verify_record["fields"].get("反馈时间")
    written_dt = datetime.fromtimestamp(written_time / 1000)
    now = datetime.now()
    
    if (now - written_dt).days > 7:
        raise Warning(f"写入的时间异常: {written_dt}")
    
    return verify_record
```

### #4 处理状态受控管理

**规则**：禁止私自新增「处理状态」选项值。

**防呆设计**：
- 只允许使用：待处理、处理中、已解决、已关闭
- 新增状态必须经Boss确认
- 脚本中硬编码状态白名单，拒绝未知状态

### #5 消息格式强制检查

**规则**：发送带@的消息必须使用 Post 格式。

**防呆设计**：
```python
# 检查清单（发送前必须逐项确认）
checklist = [
    "使用 msg_type: post 格式",
    "@标签包含 user_id 和 user_name",
    "不使用 Markdown 语法（如 **粗体**）",
    "不使用 style 属性（API不稳定）"
]
```

### #6 副作用操作确认

**规则**：测试有副作用的脚本时，先询问是否使用 `--dry-run`。

**防呆设计**：
```
Boss: 测试一下脚本
  me: 该脚本会发送真实消息到群里，是否使用 --dry-run 模式测试？
  Boss: 用 dry-run
  me: 执行 dry-run 测试，只打印日志不发送消息
```

### #7 更新记录时不修改反馈时间（2026-03-23 新增）

**规则**：更新记录追加补充信息时，**绝对不能修改"反馈时间"字段**。

**防呆设计**：
```python
def update_record_with_supplement(record_id, new_content, new_reporter, ...):
    # ⚠️ 关键：update_fields 中不能包含"反馈时间"
    update_fields = {}
    
    # 只更新允许修改的字段
    update_fields['问题内容'] = updated_content
    update_fields['反馈人'] = updated_reporter
    update_fields['备注'] = updated_remark
    # ❌ 不要这样做：update_fields['反馈时间'] = xxx
    
    # 发送更新请求
    update_record(record_id, update_fields)
```

**违规后果**：
- 原始反馈时间丢失，无法追溯问题首次反馈时间
- 超时提醒逻辑异常（基于反馈时间计算）

**教训**：2026-03-23 发现 `update_record_with_supplement` 函数可能意外修改反馈时间，已修复。

### 防呆机制优先级

| 优先级 | 机制 | 违反后果 |
|--------|------|----------|
| P0 | 所有任务派子智能体 | 主会话上下文污染 |
| P1 | Bitable时间戳校验 | 数据时间错误 |
| P1 | 写入后验证 | 脏数据流入系统 |
| P1 | 更新不修改反馈时间 | 原始时间丢失，超时逻辑异常 |
| P2 | 处理状态受控管理 | 提醒逻辑异常 |
| P2 | 消息格式强制检查 | @不高亮 |
| P2 | 副作用操作确认 | 误发消息 |

## 相关文件

- `/home/admin/openclaw/workspace/auto_forward.py` - 转发逻辑主文件
- `/home/admin/openclaw/workspace/feishu_contacts.json` - 联系人映射
- `/home/admin/openclaw/workspace/.feishu_bitable_config.json` - 表格配置
- `/home/admin/openclaw/workspace/AT_HIGHLIGHT_FIX.md` - 问题排查记录
- `/home/admin/openclaw/workspace/logs/feedback_date_fix_2026-03-19.md` - 时间戳错误修复记录
- `/home/admin/openclaw/workspace/logs/feedback_date_fix_2026-03-23.md` - 时间戳错误修复记录（含子智能体规则）
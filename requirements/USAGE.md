# 需求跟进与文档生成系统 - 使用说明 v3.0

## 📋 系统概述

本系统用于自动化处理需求跟进流程，包括：
- 从飞书表格查询待处理需求
- **私聊/群聊**多渠道沟通收集信息
- 自动生成标准化的需求文档（PRD）
- 更新表格处理状态

**v3.0 新特性**：支持群聊沟通方案，解决私聊受限问题

## 🚀 快速开始

### 1. 列出所有待处理需求
```bash
python requirement_followup.py --list
# 或简写
python requirement_followup.py -l
```

### 2. 跟进指定需求
```bash
# 按记录ID跟进（自动选择沟通模式）
python requirement_followup.py --id rec_001
python requirement_followup.py -i rec_001

# 指定Boss ID，私聊失败时自动创建群聊
python requirement_followup.py --id rec_001 --boss <boss_id>

# 按标题关键词跟进
python requirement_followup.py --title 导出
python requirement_followup.py -t 性能
```

### 3. 批量处理所有需求
```bash
python requirement_followup.py --batch
python requirement_followup.py -b

# 批量处理时指定Boss ID（用于群聊模式）
python requirement_followup.py --batch --boss <boss_id>
```

### 4. 创建需求沟通群（独立功能）
```bash
# 创建群聊并通知Boss拉人
python requirement_followup.py --group "需求名称" <boss_id>

# 指定需求人姓名
python requirement_followup.py --group "需求名称" <boss_id> --reporter "张三"
```

### 5. 在群内收集需求信息
```bash
python requirement_followup.py --collect <chat_id> <需求人ID>
```

### 6. 运行演示模式
```bash
python requirement_followup.py --demo
python requirement_followup.py -d
```

## 📝 Boss指令支持

Boss可以通过以下方式触发需求跟进：

```
跟进需求                    # 列出所有待处理需求
跟进需求 rec_001           # 跟进指定记录ID的需求
跟进需求 导出              # 跟进标题包含"导出"的需求
```

## 📱 私聊限制与群聊方案

### 飞书机器人权限限制

经过测试，飞书机器人存在以下限制：

| 功能 | 支持状态 | 说明 |
|------|---------|------|
| 创建群聊 | ✅ 支持 | 机器人可以创建群聊 |
| 直接私聊 | ❌ 受限 | 不能直接给未授权用户发送消息 |
| 生成群链接 | ✅ 支持 | 可以生成群二维码/分享链接 |

### 智能沟通模式

系统会根据权限自动选择最佳沟通方式：

```
用户指令跟进需求
    ↓
查询飞书表格获取需求详情
    ↓
获取需求人联系方式
    ↓
尝试私聊（可能被限制）
    ↓
如果私聊失败:
    创建临时需求沟通群
    邀请Boss加入
    提示Boss拉需求人进群
    ↓
Boss拉人进群后
    ↓
在群内收集需求信息（多轮对话）
    ↓
使用prd-document skill分析整理
    ↓
生成PRD文档
    ↓
向Boss汇报结果
```

### 群聊沟通流程

#### 1. 创建需求沟通群
```bash
python requirement_followup.py --group "新增批量导出功能" ou_boss_id --reporter "张三"
```

系统会：
- 创建以需求名称命名的群聊
- 邀请Boss加入群聊
- 发送邀请信息，提示Boss拉需求人进群

#### 2. 群内消息示例

**Bot发送给Boss的消息：**
```
👋 Boss好！

我已为需求「新增批量导出功能」（需求人：张三）创建了专门的沟通群。

⚠️ 由于飞书机器人权限限制，我无法直接添加未授权的用户进群。

👉 请您帮忙将需求人拉入本群，我将在此群内收集需求信息。

收集的问题清单：
1️⃣ 业务背景
2️⃣ 目标用户
3️⃣ 现状描述
4️⃣ 核心痛点
5️⃣ 期望解决方案
6️⃣ 优先级和时间
7️⃣ 相关资料

需求人进群后，我会自动开始收集信息。谢谢！🙏
```

#### 3. 群内收集信息

需求人进群后，Bot会：
- 发送欢迎消息
- 逐一询问7个关键问题
- 收集需求人回答
- 生成PRD文档

#### 4. 处理完成

文档生成后，Bot会在群内通知：
```
✅ 需求处理完成！

PRD文档已生成：新增批量导出功能

感谢大家的配合！如需进一步沟通，请随时联系。
```

## 📊 需求收集的问题清单

系统会通过以下多轮对话收集需求信息（基于 prd-document skill）：

1. **业务背景** - 需求产生的场景和原因
2. **目标用户** - 需求的使用对象
3. **现状描述** - 当前系统/流程现状
4. **核心痛点** - 当前遇到的问题
5. **期望解决方案** - 希望实现的功能
6. **优先级和时间** - 期望的完成时间
7. **相关资料** - 数据、截图、文档等

## 📁 生成的文档

需求文档保存在 `workspace/docs/prd/` 目录下，文件名格式：
```
docs/prd/YYYY-MM-DD-<feature-name>.md
```

示例：
```
docs/prd/2026-03-21-pi-liang-dao-chu-gong-neng.md
```

## 📄 需求文档模板

生成的需求文档包含以下章节：

1. **背景与目标**
   - 需求背景
   - 目标用户
   - 业务目标

2. **现状**
   - 当前系统/流程现状
   - 存在的问题

3. **目标**
   - 产品目标

4. **方案**
   - 流程图
   - 功能说明

5. **优先级和时间计划**
   - 优先级
   - 期望完成时间

6. **附件与参考资料**
   - 文档列表

## ⚙️ 配置说明

### 飞书表格配置

编辑 `.feishu_bitable_config.json` 文件配置表格信息：

```json
{
    "app_token": "你的应用token",
    "table_id": "你的表格ID"
}
```

### 联系人配置

系统会自动读取 `workspace/feishu_contacts.json` 文件获取联系人信息。

### 环境变量配置

```bash
# 设置飞书tenant_access_token（用于创建群聊等操作）
export FEISHU_TENANT_TOKEN="your_token_here"
```

## 🔧 系统架构

主要组件：

- `FeishuBitableClient` - 飞书表格客户端
- `FeishuAPIClient` - 飞书API客户端（创建群聊等）
- `ContactManager` - 联系人管理器
- `RequirementCollector` - 需求信息收集器
- `RequirementDocumentGenerator` - 需求文档生成器
- `GroupChatManager` - 群聊沟通管理器
- `MessageSender` - 消息发送器
- `RequirementFollowupSystem` - 主系统类

## 📌 注意事项

1. **首次使用**请确保已配置飞书表格的 app_token 和 table_id
2. **联系人信息**需要从 feishu_contacts.json 加载
3. **Boss ID**用于群聊模式，私聊受限时需要提供
4. **生成的文档**保存在 docs/prd/ 目录下
5. **系统会自动更新**表格中的处理状态
6. **私聊受限**是预期行为，系统会自动切换到群聊模式

## 🐛 故障排查

### 问题：找不到联系人
**解决**：确保 feishu_contacts.json 文件存在且包含反馈人信息。

### 问题：无法查询表格
**解决**：检查 .feishu_bitable_config.json 中的配置是否正确。

### 问题：私聊发送失败
**解决**：这是预期行为，系统会自动切换到群聊模式。需要提供Boss ID：
```bash
python requirement_followup.py --id rec_001 --boss ou_xxxxxxxx
```

### 问题：无法创建群聊
**解决**：检查飞书API权限，确保机器人有创建群聊的权限。确认环境变量已设置：
```bash
export FEISHU_TENANT_TOKEN="your_token"
```

### 问题：文档生成失败
**解决**：检查 docs/prd/ 目录是否有写权限。

### 问题：Boss不知道如何拉人进群
**解决**：系统会自动发送详细的邀请信息给Boss，包含：
- 需求名称和背景
- 权限限制的说明
- 明确的操作指引
- 需要收集的问题清单

## 🔐 权限管理

### 自动权限设置
系统会自动为陈俊洪（Boss）开启所有创建资源的管理权限：

| 资源类型 | Boss权限 | 设置方式 |
|---------|---------|---------|
| PRD文档 | 可编辑、可管理 | 自动生成后调用权限API |
| 需求沟通群 | 群主权限 | 创建群时设置 |
| 飞书表格 | 协作者权限 | 操作时自动添加 |

**Boss信息：**
- 姓名：陈俊洪
- 飞书ID：`ou_3e48baef1bd71cc89fb5a364be55cafc`

### 权限设置实现

系统通过 `feishu_permission_utils.py` 模块实现自动权限设置：

```python
# 设置文档权限
from feishu_permission_utils import grant_doc_admin_permission
grant_doc_admin_permission(doc_token="doccnxxx")

# 设置表格权限
from feishu_permission_utils import grant_bitable_admin_permission
grant_bitable_admin_permission(app_token="bascnxxx")

# 通用方法
from feishu_permission_utils import ensure_boss_permission
ensure_boss_permission("doc", doc_token)
ensure_boss_permission("bitable", app_token)
```

### 手动设置权限（备用）

如果自动设置失败，可按以下步骤手动设置：

**文档权限：**
1. 打开飞书文档
2. 点击右上角"分享"按钮
3. 搜索"陈俊洪"并添加
4. 权限选择"可管理"

**表格权限：**
1. 打开飞书多维表格
2. 点击右上角"分享"按钮
3. 搜索"陈俊洪"并添加
4. 权限选择"管理员"

**群聊权限：**
1. 进入群聊设置
2. 点击"群管理"
3. 设置陈俊洪为群主

## 🔄 版本历史

- **v3.1** (2026-03-21) - 集成权限管理，自动给Boss添加管理权限
- **v3.0** (2026-03-21) - 添加群聊沟通方案，解决私聊受限问题
- **v2.0** (2026-03-20) - 集成 prd-document skill，规范化PRD生成
- **v1.0** (2026-03-19) - 基础版本，支持私聊收集

---

*文档版本: 3.0*  
*最后更新: 2026-03-21*
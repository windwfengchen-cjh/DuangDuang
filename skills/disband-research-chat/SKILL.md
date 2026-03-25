# Disband Research Chat Skill

飞书调研群解散工具 - 支持多种调用方式的安全群管理 skill

## 功能

- 🔐 安全解散飞书群组（需要确认）
- 📝 支持多种调用方式（命令行、环境变量、交互式）
- 🧪 模拟运行模式（dry-run）
- 📊 详细的操作日志
- ✅ 群ID格式验证

## 安装

```bash
cd /home/admin/.openclaw/skills/disband-research-chat
npm install
npm run build
```

## 配置

工具会从 `~/.openclaw/openclaw.json` 读取飞书凭证：

```json
{
  "channels": {
    "feishu": {
      "app_id": "cli_xxxxxxxxxxxxxxxx",
      "app_secret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    }
  }
}
```

需要确保应用有以下权限：
- `chat:manage` - 管理群组
- `im:chat:read` - 读取群信息

## 使用方法

### 1. 命令行参数

```bash
# 指定群ID
node dist/index.js --chat-id oc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 简写形式
node dist/index.js -c oc_xxx

# 详细模式
node dist/index.js -c oc_xxx -v

# 模拟运行（不实际解散）
node dist/index.js -c oc_xxx --dry-run

# 显示帮助
node dist/index.js --help
```

### 2. 环境变量

```bash
export DISBAND_CHAT_ID=oc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
node dist/index.js
```

### 3. 位置参数

```bash
node dist/index.js oc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 4. 交互式

```bash
node dist/index.js
# 会提示输入群ID
```

### 5. 全局安装后使用

```bash
# 创建软链接到全局路径
ln -s /home/admin/.openclaw/skills/disband-research-chat/dist/index.js /usr/local/bin/disband-research-chat
chmod +x /usr/local/bin/disband-research-chat

# 直接使用
disband-research-chat --chat-id oc_xxx
disband-research-chat -c oc_xxx --dry-run
```

## 操作流程

1. 加载配置并验证凭证
2. 验证群ID格式
3. 获取访问令牌
4. （可选）模拟运行验证
5. 要求用户确认（输入 `DISBAND {chat_id}`）
6. 执行解散操作
7. 输出结果

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 1 | 配置文件未找到 | 检查 `~/.openclaw/openclaw.json` 是否存在 |
| 2 | 凭证无效 | 检查 app_id 和 app_secret 是否正确 |
| 3 | 群ID缺失 | 提供 `--chat-id` 参数或设置环境变量 |
| 4 | 群ID格式无效 | 确保群ID格式为 `oc_` + 32位十六进制字符 |
| 5 | 令牌错误 | 检查网络连接和凭证有效性 |
| 6 | 权限不足 | 确保应用有 `chat:manage` 权限 |
| 7 | API错误 | 查看具体错误信息 |
| 8 | 网络错误 | 检查网络连接 |
| 100 | 未知错误 | 查看日志获取详细信息 |

## 飞书API错误码

| 错误码 | 说明 |
|--------|------|
| 9499 | 权限不足，无法解散该群组 |
| 230004 | 群组不存在或已被解散 |
| 230001 | 无效的群ID |

## 示例输出

### 成功解散

```
📋 正在加载配置...
🔍 验证群ID: oc_1234567890abcdef1234567890abcdef
🔗 连接飞书API...
✓ 认证成功

⚠️  警告: 此操作将永久解散群组，不可恢复！
请输入 "DISBAND oc_1234567890abcdef1234567890abcdef" 以确认解散: DISBAND oc_1234567890abcdef1234567890abcdef

🗑️  正在解散群组...

✅ 群组解散成功！
   chatId: oc_1234567890abcdef1234567890abcdef
   duration: 523ms
   code: 0
```

### 模拟运行

```
📋 正在加载配置...
🔍 验证群ID: oc_xxx
🔗 连接飞书API...
✓ 认证成功

🧪 [模拟运行模式] 不会实际解散群组

✅ 模拟解散成功
   chatId: oc_xxx
   status: 群组存在，可以解散
```

### 取消操作

```
⚠️  警告: 此操作将永久解散群组，不可恢复！
请输入 "DISBAND oc_1234567890abcdef1234567890abcdef" 以确认解散: cancel

❌ 操作已取消
```

### 配置错误示例

```
❌ 未找到配置文件 ~/.openclaw/openclaw.json

💡 提示: 请确保 ~/.openclaw/openclaw.json 文件存在且包含有效的飞书凭证
   格式: { "app_id": "cli_xxx", "app_secret": "xxx" }
```

## 日志

日志文件保存在 `~/.openclaw/logs/disband-research-chat/` 目录下，按日期命名。

## 注意事项

### 1. 权限要求

确保飞书应用具有以下权限：
- `chat:manage` - 管理群组（必需）
- `im:chat:read` - 读取群信息（可选，用于验证）

### 2. 群ID获取方式

```bash
# 通过飞书客户端
1. 打开目标群组
2. 点击右上角「···」→「设置」
3. 在「群信息」中查看「群ID」

# 通过API获取
GET /open-apis/im/v1/chats
```

### 3. 安全建议

- 使用 `--dry-run` 先验证群ID有效性
- 定期轮换 app_secret
- 不要在日志中记录敏感信息
- 建议配置日志轮转策略

### 4. 常见问题

**Q: 如何获取群ID？**
A: 飞书群ID格式为 `oc_` + 32位十六进制字符，可在群设置中查看。

**Q: 提示权限不足怎么办？**
A: 检查应用是否有 `chat:manage` 权限，并确认应用是该群的管理员。

**Q: 群已解散但API返回成功？**
A: 这是正常行为，飞书API对已解散的群返回成功状态码。

## 集成示例

### 在脚本中使用

```bash
#!/bin/bash
CHAT_ID=$1

# 检查参数
if [ -z "$CHAT_ID" ]; then
  echo "用法: $0 <chat_id>"
  exit 1
fi

# 先模拟运行
node dist/index.js -c "$CHAT_ID" --dry-run
if [ $? -ne 0 ]; then
  echo "模拟运行失败，终止操作"
  exit 1
fi

# 确认后执行（需要手动输入确认）
echo "DISBAND $CHAT_ID" | node dist/index.js -c "$CHAT_ID"
```

### 批量解散（谨慎使用）

```bash
#!/bin/bash
# chat_ids.txt 每行一个群ID
while read -r chat_id; do
  echo "正在解散: $chat_id"
  echo "DISBAND $chat_id" | node dist/index.js -c "$chat_id" --verbose
  sleep 1
done < chat_ids.txt
```

## 版本

v1.0.0

## 作者

OpenClaw

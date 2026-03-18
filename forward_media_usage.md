# 飞书图片转发工具 - 使用说明

## 核心功能

简化版工具只包含3个核心功能：

1. **下载图片** - 带权限错误检测
2. **上传图片** - 获取新的 image_key
3. **转发图片** - 下载+上传的完整流程

## 核心限制

⚠️ **飞书安全策略限制**：机器人只能下载自己发送的图片

- ✅ 自己发送的图片 → 可以下载 → 可以转发
- ❌ 其他用户发送的图片 → 下载失败 → 错误："The app is not the resource sender"

## 快速使用

### 命令行方式

```bash
# 方式1：直接运行（使用默认示例 key）
python3 /home/admin/openclaw/workspace/forward_media.py

# 方式2：传入 image_key（使用 Images API，只能下载自己发的图片）
python3 /home/admin/openclaw/workspace/forward_media.py img_v2_12345678

# 方式3：传入 image_key + message_id（使用 Resource API，可下载任何人发的图片）⭐推荐
python3 /home/admin/openclaw/workspace/forward_media.py img_v2_12345678 om_xxxxxxxx
```

**🧹 自动清理说明：**
- 转发完成后，本地临时图片会被**自动删除**
- 无论成功或失败，都不会占用存储资源

### Python API 方式

```python
from forward_media import forward_image, download_image, upload_image

# ========== 方式1：完整转发流程（推荐）==========
# 提供 message_id，使用 Resource API 下载任何人发的图片
success, result = forward_image("img_v2_12345678", message_id="om_xxxxxxxx")
if success:
    print(f"新 image_key: {result}")
else:
    print(f"错误: {result}")

# ========== 方式2：不指定 message_id ==========
# 使用 Images API，只能下载自己发的图片
success, result = forward_image("img_v2_12345678")

# ========== 方式3：分步操作 ==========
from forward_media import load_feishu_creds, get_tenant_access_token, download_image_by_resource

# 获取 token
app_id, app_secret = load_feishu_creds()
token = get_tenant_access_token(app_id, app_secret)

# 使用 Resource API 下载（推荐）
success, result = download_image_by_resource("om_xxxx", "img_v2_12345678", token)
if success:
    local_path = result  # 本地文件路径
    # 上传图片
    success2, result2 = upload_image(local_path, token)
    if success2:
        new_image_key = result2
```

## API 说明

### `forward_image(image_key, message_id=None)`

完整转发流程：下载原图 → 上传获取新 image_key → **自动清理本地文件**

**参数：**
- `image_key`: 原图片的 image_key
- `message_id`: 消息 ID（可选）
  - 提供后使用 **Resource API**，可下载**任何人**发的图片 ⭐推荐
  - 不提供则使用 Images API，只能下载自己发的图片

**返回：** `(success, result)`
- `success=True`: `result` 是新的 image_key
- `success=False`: `result` 是错误信息

**⚠️ 重要说明：**
- 无论转发成功或失败，本地临时文件都会被**自动删除**
- 这是为了避免占用存储资源
- 如需保留原图，请在调用前自行保存

### `download_image_by_resource(message_id, file_key, token)` ⭐推荐

使用 **Resource API** 下载图片（支持下载**任何人**发的图片）

**参数：**
- `message_id`: 消息 ID
- `file_key`: 文件/图片 key
- `token`: tenant_access_token

**返回：** `(success, result)`
- `success=True`: `result` 是本地文件路径
- `success=False`: `result` 是错误信息

### `download_image(image_key, token)`

使用 **Images API** 下载图片（只能下载自己发送的图片）

**参数：**
- `image_key`: 图片 key
- `token`: tenant_access_token

**返回：** `(success, result)`
- `success=True`: `result` 是本地文件路径
- `success=False`: `result` 是错误信息（包含权限错误检测）

### `upload_image(file_path, token)`

上传本地图片到飞书

**参数：**
- `file_path`: 本地图片路径
- `token`: tenant_access_token

**返回：** `(success, result)`
- `success=True`: `result` 是新的 image_key
- `success=False`: `result` 是错误信息

## API 选择指南

### Images API vs Resource API

| 特性 | Images API | Resource API ⭐推荐 |
|------|------------|---------------------|
| 适用场景 | 下载自己发的图片 | 下载**任何人**发的图片 |
| 所需参数 | image_key | message_id + file_key |
| 权限限制 | 只能下载自己的 | 无限制（只要有消息ID） |
| 推荐使用 | ❌ 不推荐 | ✅ **推荐** |

### 如何选择？

**情况1：从飞书消息事件中获取图片**
- 消息事件包含 `message_id` 和 `image_key`
- ✅ 使用 Resource API：`forward_image(image_key, message_id)`

**情况2：只有 image_key，没有 message_id**
- 尝试使用 Images API：`forward_image(image_key)`
- 如果是别人发的图片，会报错

## 常见错误处理

### 权限错误（使用 Images API 时）

```
错误信息：权限错误：The app is not the resource sender
说明：机器人只能下载自己发送的图片，无法下载其他用户发送的图片
```

**解决方案：**
- 提供 `message_id` 使用 Resource API
- 例如：`forward_image(image_key, message_id)`

### 凭证错误

```
错误信息：无法加载飞书凭证 / 无法获取 access_token
```

**解决方案：**
- 检查 `~/.openclaw/openclaw.json` 是否存在
- 检查配置中的 `appId` 和 `appSecret` 是否正确

### 图片不存在

```
错误信息：获取下载链接失败：resource not found
```

**解决方案：**
- 检查 image_key 是否正确
- 检查图片是否已被删除

## 与其他用户图片的兼容方案

由于机器人无法下载其他用户发送的图片，建议采用以下方案：

```python
# 方案：消息链接转发
def forward_with_link(original_message_url: str, text_content: str):
    """
    对于无法下载的图片，发送消息链接让用户点击查看原图
    """
    message = f"{text_content}\n\n📎 原消息包含图片，点击查看：\n{original_message_url}"
    # 发送文字消息...
```

## 文件位置

- 代码：`/home/admin/openclaw/workspace/forward_media.py`
- 临时文件：`/tmp/feishu_img_*.png`（自动清理）

## 下一步扩展

如需扩展功能，可考虑：

1. **批量转发** - 一次处理多张图片
2. **消息构造** - 构造包含文字+图片的完整消息
3. **群消息发送** - 将转发后的图片发送到指定群
4. **自动清理** - 更完善的临时文件管理

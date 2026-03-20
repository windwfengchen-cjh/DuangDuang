# GLM-V-Model 技能使用指南

## 一、技能概述

**名称**: glm-v-model  
**功能**: 智谱 GLM-4V/4.6V 视觉模型调用技能  
**用途**: 图像/视频理解、多模态对话、图表分析等任务  

## 二、支持的模型

| 模型 | 说明 | 特点 |
|------|------|------|
| glm-4v | GLM-4 视觉模型 | 基础视觉理解 |
| glm-4.6v | GLM-4.6V 视觉模型 | 更强的视觉理解能力，支持更长上下文 |

## 三、配置需求

### 必需配置

1. **API Key** (必需)
   - 获取方式: 访问 https://open.bigmodel.cn 获取智谱 AI API Key
   - 在使用代码中替换 `YOUR_API_KEY`

2. **Python 依赖**
   ```bash
   pip install zhipuai
   ```

3. **环境变量** (可选，建议)
   ```bash
   export ZHIPU_API_KEY="your_api_key_here"
   ```

## 四、使用方法

### 方式一：直接使用 Python API

```python
from zhipuai import ZhipuAI
import base64

# 初始化客户端
client = ZhipuAI(api_key="YOUR_API_KEY")

# 读取本地图片并转为 base64
with open("image.jpg", "rb") as f:
    img_base = base64.b64encode(f.read()).decode("utf-8")

# 调用模型
response = client.chat.completions.create(
    model="glm-4.6v",
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base}"}},
            {"type": "text", "text": "描述这张图片"}
        ]
    }],
    thinking={"type": "enabled"}
)
print(response.choices[0].message.content)
```

### 方式二：使用图片URL

```python
response = client.chat.completions.create(
    model="glm-4.6v",
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}},
            {"type": "text", "text": "这张图片里有什么？"}
        ]
    }]
)
```

### 方式三：多图理解

```python
response = client.chat.completions.create(
    model="glm-4.6v",
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": "图片1 base64 或 URL"}},
            {"type": "image_url", "image_url": {"url": "图片2 base64 或 URL"}},
            {"type": "text", "text": "比较这两张图片的异同"}
        ]
    }]
)
```

### 方式四：视频理解 (GLM-4.6V)

```python
response = client.chat.completions.create(
    model="glm-4.6v",
    messages=[{
        "role": "user",
        "content": [
            {"type": "video_url", "video_url": {"url": "视频URL"}},
            {"type": "text", "text": "描述这个视频的内容"}
        ]
    }]
)
```

### 方式五：使用技能脚本

```python
import sys
sys.path.append('/home/admin/openclaw/workspace/skills/glm-v-model/script')
from infer_glmv import glm_v

# 调用方式
result = glm_v(['image.jpg'], '描述图片', 'glm-4.6v')
print(result)
```

## 五、常用场景及 Prompt 示例

| 场景 | Prompt 示例 |
|------|-------------|
| 图片描述 | "详细描述这张图片的内容" |
| 图表分析 | "分析这张图表数据" |
| 文字识别(OCR) | "提取图片中的文字" |
| 物体识别 | "图片中有哪些物体" |
| 场景理解 | "这是什么地方" |
| 多图对比 | "比较这两张图片的异同" |
| 视频理解 | "总结这个视频的内容" |

## 六、参数说明

### 主要参数

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| model | string | 模型名称 | "glm-4.6v" |
| messages | array | 对话消息列表 | 必需 |
| thinking | object | 深度思考模式 | {"type": "enabled"} |
| temperature | float | 采样温度 | 0.7 |
| top_p | float | 核采样参数 | 0.9 |
| max_tokens | int | 最大生成token数 | 4096 |

### 消息格式

```python
{
    "role": "user",  # 角色: user/assistant/system
    "content": [
        {"type": "image_url", "image_url": {"url": "图片URL或base64"}},
        {"type": "text", "text": "文本内容"}
    ]
}
```

## 七、注意事项

1. **API Key 安全**: 不要将 API Key 硬编码在代码中，建议使用环境变量
2. **图片格式**: 支持 JPEG、PNG、WebP 等常见格式
3. **图片大小**: 单张图片建议不超过 10MB
4. **计费方式**: 按 token 计费，图片会转换为 token 消耗
5. **网络要求**: 需要访问智谱 AI 服务，确保网络畅通
6. **错误处理**: 建议添加 try-except 处理 API 调用异常

## 八、触发场景

当用户提到以下内容时，使用此技能：
- 图片理解
- 图像识别
- 视觉模型
- GLM-4V / GLM-4.6V
- 多模态分析
- 看图说话
- 图表分析
- 视频理解

---
*报告生成时间: 2026-03-19*  
*技能路径: /home/admin/openclaw/workspace/skills/glm-v-model*

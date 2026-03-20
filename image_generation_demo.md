# 图片生成技能演示指南

本指南演示三种不同的图片生成方法，从本地AI绘图到在线API再到图表生成工具。

---

## 1. Stable Diffusion（本地免费）

### 简介
Stable Diffusion 是开源的文本到图像生成模型，可以在本地运行，完全免费。

### 硬件要求
- **最低**: 4GB VRAM (NVIDIA GPU)
- **推荐**: 8GB+ VRAM
- **CPU模式**: 可用但速度极慢

### 安装步骤

```bash
# 1. 克隆 Stable Diffusion WebUI
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
cd stable-diffusion-webui

# 2. 运行安装脚本
# Windows:
./webui-user.bat

# Linux/Mac:
./webui.sh
```

### 完整Python代码示例

```python
"""
Stable Diffusion 本地生成图片示例
需要安装: pip install diffusers transformers accelerate torch
"""

import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
from PIL import Image
import os

def generate_image_sd(
    prompt: str,
    negative_prompt: str = "",
    width: int = 512,
    height: int = 512,
    steps: int = 25,
    guidance_scale: float = 7.5,
    seed: int = None,
    output_path: str = "output.png"
) -> str:
    """
    使用 Stable Diffusion 生成图片
    
    Args:
        prompt: 正向提示词（想要的内容）
        negative_prompt: 负向提示词（不想要的内容）
        width: 图片宽度
        height: 图片高度
        steps: 推理步数（越多越精细）
        guidance_scale: 引导强度（7-12之间）
        seed: 随机种子（可复现）
        output_path: 输出路径
    """
    
    # 设置设备
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"使用设备: {device}")
    
    # 加载模型（首次会下载约4GB）
    model_id = "runwayml/stable-diffusion-v1-5"
    
    print("正在加载模型...")
    pipe = StableDiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        safety_checker=None,  # 关闭安全检查器（可选）
    )
    
    # 使用更快的调度器
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to(device)
    
    # 启用内存优化（低显存模式）
    if device == "cuda":
        pipe.enable_attention_slicing()
        # pipe.enable_vae_slicing()  # 如果使用 SDXL
    
    # 设置随机种子
    generator = None
    if seed is not None:
        generator = torch.Generator(device=device).manual_seed(seed)
    
    print(f"开始生成: '{prompt}'")
    
    # 生成图片
    with torch.autocast(device):
        image = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            generator=generator,
        ).images[0]
    
    # 保存图片
    image.save(output_path)
    print(f"图片已保存至: {os.path.abspath(output_path)}")
    
    return output_path


# ============ 使用示例 ============

if __name__ == "__main__":
    # 示例1: 生成一只宇航员猫
    generate_image_sd(
        prompt="a cat wearing astronaut suit, floating in space, earth in background, "
               "highly detailed, 8k, photorealistic, cinematic lighting",
        negative_prompt="blurry, low quality, distorted, ugly, deformed",
        width=512,
        height=512,
        steps=25,
        seed=42,
        output_path="astronaut_cat.png"
    )
    
    # 示例2: 生成风景图
    generate_image_sd(
        prompt="a serene lake in the mountains at sunset, reflection in water, "
               "golden hour, peaceful atmosphere, landscape photography",
        negative_prompt="people, buildings, text, watermark",
        width=768,
        height=512,
        steps=30,
        output_path="mountain_lake.png"
    )
```

### 高级用法：ControlNet

```python
"""
使用 ControlNet 控制图片生成
需要: pip install controlnet-aux
"""

import torch
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
from PIL import Image
import numpy as np
import cv2

def generate_with_controlnet(
    base_image_path: str,
    prompt: str,
    output_path: str = "controlnet_output.png"
):
    """使用 ControlNet 基于线稿生成图片"""
    
    # 加载 ControlNet 模型（Canny边缘检测）
    controlnet = ControlNetModel.from_pretrained(
        "lllyasviel/sd-controlnet-canny",
        torch_dtype=torch.float16
    )
    
    pipe = StableDiffusionControlNetPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        controlnet=controlnet,
        torch_dtype=torch.float16
    )
    pipe.to("cuda")
    
    # 读取并处理输入图片
    image = Image.open(base_image_path)
    image = np.array(image)
    
    # Canny 边缘检测
    low_threshold = 100
    high_threshold = 200
    canny_image = cv2.Canny(image, low_threshold, high_threshold)
    canny_image = canny_image[:, :, None]
    canny_image = np.concatenate([canny_image, canny_image, canny_image], axis=2)
    canny_image = Image.fromarray(canny_image)
    
    # 生成
    result = pipe(
        prompt=prompt,
        image=canny_image,
        num_inference_steps=20,
    ).images[0]
    
    result.save(output_path)
    return output_path
```

### 预期输出
```
使用设备: cuda
正在加载模型...
开始生成: 'a cat wearing astronaut suit...'
图片已保存至: /path/to/astronaut_cat.png
```

### 注意事项
1. **首次运行**会下载约4GB模型文件
2. **低显存**（<6GB）：启用 `enable_attention_slicing()`
3. **模型选择**：
   - `v1-5`: 通用性好，速度快
   - `SDXL`: 更高质量，需要更多显存
   - `DreamShaper`: 艺术风格更好

---

## 2. Z-Image Generation（ModelScope免费）

### 简介
ModelScope 是阿里达摩院推出的模型平台，提供免费的图片生成API。

### API Key 获取方式

1. 访问 https://www.modelscope.cn/
2. 注册/登录账号
3. 进入「个人中心」→「访问令牌」
4. 创建新令牌（Token）

### 完整Python代码示例

```python
"""
ModelScope Z-Image 图片生成API示例
需要: pip install requests
"""

import requests
import json
import base64
from PIL import Image
import io
import os

class ModelScopeImageGenerator:
    """ModelScope 图片生成器"""
    
    API_URL = "https://modelscope.cn/api/v1/studio/damo/z-image-generation/gradio/run"
    
    def __init__(self, api_token: str = None):
        """
        初始化
        
        Args:
            api_token: ModelScope API令牌（可选，公开API可能不需要）
        """
        self.api_token = api_token
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        if api_token:
            self.headers["Authorization"] = f"Bearer {api_token}"
    
    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 30,
        cfg_scale: float = 7.5,
        seed: int = -1
    ) -> Image.Image:
        """
        生成图片
        
        Args:
            prompt: 提示词（支持中英文）
            negative_prompt: 负向提示词
            width: 宽度（512-2048）
            height: 高度（512-2048）
            steps: 步数（10-50）
            cfg_scale: 引导系数（1-20）
            seed: 随机种子（-1为随机）
        
        Returns:
            PIL Image 对象
        """
        
        # 构建请求数据
        payload = {
            "fn_index": 0,  # 函数索引，可能需要根据实际API调整
            "data": [
                prompt,           # 提示词
                negative_prompt,  # 负向提示词
                width,            # 宽度
                height,           # 高度
                steps,            # 步数
                cfg_scale,        # CFG Scale
                seed,             # 种子
            ]
        }
        
        print(f"正在生成: {prompt}")
        
        try:
            response = requests.post(
                self.API_URL,
                headers=self.headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            
            # 解析返回的图片数据（通常是base64格式）
            if "data" in result:
                image_data = result["data"][0] if isinstance(result["data"], list) else result["data"]
                
                # 处理base64图片
                if isinstance(image_data, str) and image_data.startswith("data:image"):
                    base64_str = image_data.split(",")[1]
                    image_bytes = base64.b64decode(base64_str)
                    image = Image.open(io.BytesIO(image_bytes))
                    return image
                
                # 处理URL格式
                elif isinstance(image_data, str) and image_data.startswith("http"):
                    img_response = requests.get(image_data)
                    image = Image.open(io.BytesIO(img_response.content))
                    return image
            
            raise ValueError(f"无法解析响应: {result}")
            
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")
            raise
    
    def save_image(self, image: Image.Image, path: str):
        """保存图片"""
        image.save(path)
        print(f"图片已保存: {os.path.abspath(path)}")


# ============ 使用示例 ============

def demo_modelscope_api():
    """演示ModelScope图片生成"""
    
    # 初始化（如果需要API Token）
    # generator = ModelScopeImageGenerator(api_token="your-token-here")
    generator = ModelScopeImageGenerator()
    
    # 示例1: 生成中国风山水画
    try:
        image1 = generator.generate(
            prompt="中国传统山水画，云雾缭绕的山峰，松树，瀑布，水墨风格，高清",
            negative_prompt="人物，现代建筑，模糊，低质量",
            width=1024,
            height=1024,
            steps=30,
            cfg_scale=7.5
        )
        generator.save_image(image1, "chinese_landscape.png")
    except Exception as e:
        print(f"生成失败: {e}")
    
    # 示例2: 生成赛博朋克风格
    try:
        image2 = generator.generate(
            prompt="cyberpunk city at night, neon lights, flying cars, futuristic buildings, "
                   "highly detailed, 8k, cinematic",
            negative_prompt="blur, low quality, ugly",
            width=1024,
            height=768,
            steps=35
        )
        generator.save_image(image2, "cyberpunk_city.png")
    except Exception as e:
        print(f"生成失败: {e}")


if __name__ == "__main__":
    demo_modelscope_api()
```

### 命令行使用示例

```bash
# 方式1: 使用curl直接调用（简化版）
curl -X POST "https://modelscope.cn/api/v1/studio/damo/z-image-generation/gradio/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "fn_index": 0,
    "data": [
      "一只可爱的猫咪在樱花树下",  # 提示词
      "丑陋, 模糊",                  # 负向提示词
      1024,                          # 宽度
      1024,                          # 高度
      30,                            # 步数
      7.5,                           # CFG Scale
      -1                             # 种子
    ]
  }'

# 方式2: 使用Python脚本命令行
python modelscope_generator.py --prompt "星空下的城堡" --output castle.png
```

### 备选API：其他免费模型

```python
"""
备选方案：使用Hugging Face Inference API（免费额度）
"""

import requests
from PIL import Image
import io

def generate_with_hf_api(prompt: str, api_token: str = None):
    """
    使用 Hugging Face Inference API 生成图片
    免费版有速率限制
    """
    API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
    
    headers = {}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "num_inference_steps": 25,
            "guidance_scale": 7.5
        }
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    
    if response.status_code == 200:
        image = Image.open(io.BytesIO(response.content))
        return image
    else:
        raise Exception(f"API错误: {response.text}")


# 使用示例
if __name__ == "__main__":
    image = generate_with_hf_api("a beautiful sunset over the ocean")
    image.save("sunset.png")
```

### 预期输出
```
正在生成: 中国传统山水画，云雾缭绕的山峰...
图片已保存: /path/to/chinese_landscape.png
```

### 注意事项
1. **免费额度**：ModelScope对免费用户有调用频率限制
2. **API变动**：Gradio API可能随版本更新而调整
3. **备选方案**：
   - Hugging Face Inference API（需注册）
   - Replicate API（有免费额度）
   - DeepAI API（有限免费）

---

## 3. Excalidraw（图表生成）

### 简介
Excalidraw 是开源的手绘风格图表工具，支持通过JSON数据程序化生成图表。

### 完整Python代码示例

```python
"""
Excalidraw 图表程序化生成
生成手绘风格的流程图、架构图等
"""

import json
import base64
import webbrowser
import os
from datetime import datetime

class ExcalidrawGenerator:
    """Excalidraw 图表生成器"""
    
    # 元素类型
    ELEMENT_TYPES = {
        "rectangle": "rectangle",
        "ellipse": "ellipse",
        "diamond": "diamond",
        "arrow": "arrow",
        "text": "text",
        "image": "image"
    }
    
    # 默认颜色
    COLORS = {
        "black": "#000000",
        "red": "#e03131",
        "green": "#2f9e44",
        "blue": "#1971c2",
        "yellow": "#f08c00",
        "purple": "#9c36b5",
        "gray": "#868e96"
    }
    
    def __init__(self):
        self.elements = []
        self.app_state = {
            "viewBackgroundColor": "#ffffff",
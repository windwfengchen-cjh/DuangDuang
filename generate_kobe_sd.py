import os
import torch
from diffusers import StableDiffusionPipeline
from PIL import Image

# 设置 HF 镜像
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
print(f"HF_ENDPOINT: {os.environ.get('HF_ENDPOINT')}")

# 创建输出目录
output_dir = "/home/admin/openclaw/workspace/generated_images"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "kobe_ice_cream_sd.png")

# 检查设备
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# 检查缓存
from pathlib import Path
cache_dir = Path.home() / ".cache/huggingface/hub"
if cache_dir.exists():
    sd_cache = list(cache_dir.glob("models--runwayml--stable-diffusion-v1-5"))
    if sd_cache:
        size = sum(f.stat().st_size for f in sd_cache[0].rglob('*') if f.is_file())
        print(f"本地缓存大小: {size / 1024**3:.2f} GB")

# 加载模型 - 尝试使用本地缓存或继续下载
print("正在从 HF Mirror 加载 Stable Diffusion v1.5 模型...")
model_id = "runwayml/stable-diffusion-v1-5"

try:
    # 先尝试本地缓存
    pipe = StableDiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float32,
        safety_checker=None,
        requires_safety_checker=False,
        local_files_only=True
    )
    print("使用本地缓存加载成功!")
except Exception as e:
    print(f"本地缓存不完整，尝试下载... ({e})")
    pipe = StableDiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float32,
        safety_checker=None,
        requires_safety_checker=False
    )

pipe = pipe.to(device)

# 生成图片
prompt = "Kobe Bryant eating ice cream, cartoon style, colorful, cheerful, 3D cartoon render, vibrant colors, fun atmosphere, high quality"
print(f"\n生成图片...")
print(f"提示词: {prompt}")

image = pipe(
    prompt,
    num_inference_steps=20,
    guidance_scale=7.5,
    height=512,
    width=512
).images[0]

# 保存图片
image.save(output_path)
print(f"\n✅ 图片已保存到: {output_path}")

# 显示图片信息
print(f"图片尺寸: {image.size}")

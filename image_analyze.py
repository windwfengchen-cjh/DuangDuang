#!/usr/bin/env python3
"""
图片识别工具 - 使用多模态大模型
支持：Kimi、Gemini、OpenAI GPT-4V 等
"""
import sys
import os
import base64
import json
import requests
from pathlib import Path

# 加载 .env 文件（如果存在）
from pathlib import Path
dotenv_path = Path(__file__).parent / ".env"
if dotenv_path.exists():
    with open(dotenv_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key, value)

# API 配置（从环境变量读取，避免硬编码）
API_CONFIG = {
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1/chat/completions",
        "api_key": os.getenv("KIMI_API_KEY", ""),
        "model": "moonshot-v1-8k-vision-preview"
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
        "api_key": os.getenv("GEMINI_API_KEY", ""),
    },
    "openai": {
        "base_url": "https://api.openai.com/v1/chat/completions",
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "model": "gpt-4o"
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "api_key": os.getenv("ZHIPU_API_KEY", ""),
        "model": "glm-4v"
    }
}

def encode_image(image_path):
    """将图片转为 base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def analyze_with_kimi(image_path, prompt="描述这张图片的内容"):
    """使用 Kimi 分析图片"""
    config = API_CONFIG["kimi"]
    if not config["api_key"]:
        return "错误：未设置 KIMI_API_KEY 环境变量"
    
    base64_image = encode_image(image_path)
    
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": config["model"],
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(config["base_url"], headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"API 调用失败: {str(e)}"

def analyze_with_gemini(image_path, prompt="描述这张图片的内容"):
    """使用 Gemini 分析图片"""
    config = API_CONFIG["gemini"]
    if not config["api_key"]:
        return "错误：未设置 GEMINI_API_KEY 环境变量"
    
    # 读取图片并转为 base64
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    url = f"{config['base_url']}?key={config['api_key']}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_data
                        }
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        # 提取 Gemini 的回复
        if "candidates" in result and len(result["candidates"]) > 0:
            parts = result["candidates"][0]["content"]["parts"]
            return "".join([p.get("text", "") for p in parts])
        return "无法解析 Gemini 响应"
    except Exception as e:
        return f"API 调用失败: {str(e)}"

def analyze_with_zhipu(image_path, prompt="描述这张图片的内容"):
    """使用智谱 AI GLM-V 分析图片"""
    config = API_CONFIG["zhipu"]
    if not config["api_key"]:
        return "错误：未设置 ZHIPU_API_KEY 环境变量"
    
    base64_image = encode_image(image_path)
    
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": config["model"],
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(config["base_url"], headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"API 调用失败: {str(e)}"

def analyze_image(image_path, provider="gemini", prompt="描述这张图片的内容"):
    """
    分析图片
    provider: kimi | gemini | openai | zhipu
    """
    if not os.path.exists(image_path):
        return f"错误：图片文件不存在: {image_path}"
    
    if provider == "kimi":
        return analyze_with_kimi(image_path, prompt)
    elif provider == "gemini":
        return analyze_with_gemini(image_path, prompt)
    elif provider == "zhipu":
        return analyze_with_zhipu(image_path, prompt)
    else:
        return f"错误：不支持的提供商: {provider}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 image_analyze.py <图片路径> [提供商] [提示词]")
        print("提供商: kimi | gemini | zhipu (默认: gemini)")
        print("\n示例:")
        print("  python3 image_analyze.py /path/to/image.png")
        print("  python3 image_analyze.py /path/to/image.png zhipu '提取图片中的文字'")
        print("\n环境变量:")
        print("  GEMINI_API_KEY - Gemini API 密钥")
        print("  KIMI_API_KEY - Kimi API 密钥")
        print("  ZHIPU_API_KEY - 智谱 AI API 密钥")
        sys.exit(1)
    
    image_path = sys.argv[1]
    provider = sys.argv[2] if len(sys.argv) > 2 else "gemini"
    prompt = sys.argv[3] if len(sys.argv) > 3 else "描述这张图片的内容"
    
    result = analyze_image(image_path, provider, prompt)
    print(result)

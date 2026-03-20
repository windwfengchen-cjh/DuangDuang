#!/usr/bin/env python3
"""
ModelScope 图像生成脚本
使用 API Token: ms-343b98a1-5bf0-4247-8478-4c6db0883e0d
"""

import requests
import json
import os
import base64
from datetime import datetime

# API Token
API_TOKEN = "ms-343b98a1-5bf0-4247-8478-4c6db0883e0d"

# 基础配置
BASE_URL = "https://api.modelscope.cn"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# 提示词和参数
PROMPT = "科比吃冰激凌，卡通风格，可爱，色彩丰富"
IMAGE_SIZE = "1024x1024"
STEPS = 30

def list_available_models():
    """列出可用的图像生成模型"""
    print("=" * 60)
    print("正在查找可用的图像生成模型...")
    
    # 尝试几个已知的图像生成模型
    models_to_try = [
        "damo/cv_diffusion_text-to-image-synthesis",
        "damo/z-image-generation",
        "AI-ModelScope/stable-diffusion-v1-5",
        "AI-ModelScope/stable-diffusion-xl-base-1.0"
    ]
    
    available_models = []
    
    for model_id in models_to_try:
        try:
            url = f"{BASE_URL}/api/v1/models/{model_id}"
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✓ 模型可用: {model_id}")
                available_models.append(model_id)
            else:
                print(f"✗ 模型不可用 ({response.status_code}): {model_id}")
        except Exception as e:
            print(f"✗ 检查失败: {model_id} - {e}")
    
    return available_models

def try_generate_image(model_id, prompt, width=1024, height=1024, steps=30):
    """尝试生成图片"""
    print(f"\n{'=' * 60}")
    print(f"尝试使用模型: {model_id}")
    print(f"API 端点: {BASE_URL}/api/v1/models/{model_id}/inference")
    print(f"{'=' * 60}")
    
    url = f"{BASE_URL}/api/v1/models/{model_id}/inference"
    
    payload = {
        "input": {
            "prompt": prompt,
            "width": width,
            "height": height,
            "num_inference_steps": steps
        },
        "parameters": {
            "width": width,
            "height": height,
            "num_inference_steps": steps
        }
    }
    
    print(f"请求参数:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=120)
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应内容:")
            print(json.dumps(result, indent=2, ensure_ascii=False)[:1000])
            return result
        else:
            print(f"请求失败: {response.status_code}")
            print(f"响应内容: {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"请求异常: {e}")
        return None

def save_image(result, filename):
    """保存生成的图片"""
    try:
        # 尝试不同的响应格式
        image_data = None
        
        if isinstance(result, dict):
            # 检查 output 字段
            if 'output' in result:
                output = result['output']
                if isinstance(output, dict):
                    # 可能的图片字段
                    for key in ['image', 'images', 'image_url', 'url', 'base64']:
                        if key in output:
                            image_data = output[key]
                            print(f"找到图片数据字段: {key}")
                            break
                elif isinstance(output, str):
                    image_data = output
            
            # 检查 data 字段
            if not image_data and 'data' in result:
                data = result['data']
                if isinstance(data, dict):
                    for key in ['image', 'images', 'image_url', 'url', 'base64']:
                        if key in data:
                            image_data = data[key]
                            print(f"找到图片数据字段: data.{key}")
                            break
        
        if not image_data:
            print("未能在响应中找到图片数据")
            print(f"完整响应: {json.dumps(result, indent=2, ensure_ascii=False)[:2000]}")
            return None
        
        # 处理 base64 编码的图片
        if isinstance(image_data, str):
            if image_data.startswith('data:image'):
                # data:image/png;base64,xxxxx 格式
                image_data = image_data.split(',')[1]
            
            # 解码并保存
            image_bytes = base64.b64decode(image_data)
            
            # 确保目录存在
            os.makedirs('generated_images', exist_ok=True)
            
            filepath = os.path.join('generated_images', filename)
            with open(filepath, 'wb') as f:
                f.write(image_bytes)
            
            print(f"✓ 图片已保存: {filepath}")
            return filepath
        
        elif isinstance(image_data, list) and len(image_data) > 0:
            # 处理图片列表
            first_image = image_data[0]
            if isinstance(first_image, str):
                if first_image.startswith('data:image'):
                    first_image = first_image.split(',')[1]
                image_bytes = base64.b64decode(first_image)
                
                os.makedirs('generated_images', exist_ok=True)
                filepath = os.path.join('generated_images', filename)
                with open(filepath, 'wb') as f:
                    f.write(image_bytes)
                
                print(f"✓ 图片已保存: {filepath}")
                return filepath
        
        print(f"未知的图片数据格式: {type(image_data)}")
        return None
        
    except Exception as e:
        print(f"保存图片失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("=" * 60)
    print("ModelScope 图像生成任务")
    print("=" * 60)
    print(f"提示词: {PROMPT}")
    print(f"图片尺寸: {IMAGE_SIZE}")
    print(f"推理步数: {STEPS}")
    print(f"API Token: {API_TOKEN[:20]}...")
    
    # 测试 API 连接
    print(f"\n{'=' * 60}")
    print("测试 API 连接...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/user", headers=HEADERS, timeout=10)
        print(f"API 连接状态: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"用户信息: {json.dumps(user_data, indent=2, ensure_ascii=False)[:500]}")
    except Exception as e:
        print(f"API 连接测试失败: {e}")
    
    # 查找可用模型
    available_models = list_available_models()
    
    if not available_models:
        print("\n未找到可用的图像生成模型，尝试使用默认模型...")
        available_models = ["damo/cv_diffusion_text-to-image-synthesis"]
    
    # 尝试生成图片
    success = False
    for model_id in available_models:
        result = try_generate_image(model_id, PROMPT, 1024, 1024, STEPS)
        
        if result:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"kobe_icecream_{timestamp}.png"
            
            saved_path = save_image(result, filename)
            
            if saved_path:
                print(f"\n{'=' * 60}")
                print("生成成功！")
                print(f"使用的模型: {model_id}")
                print(f"API 端点: {BASE_URL}/api/v1/models/{model_id}/inference")
                print(f"图片保存路径: {saved_path}")
                print(f"{'=' * 60}")
                success = True
                break
    
    if not success:
        print(f"\n{'=' * 60}")
        print("生成失败 - 所有模型尝试均失败")
        print(f"{'=' * 60}")
        
        # 尝试其他方法 - 直接使用模型推理
        print("\n尝试使用 ModelScope 模型推理 API...")
        try_alternative_api()

def try_alternative_api():
    """尝试替代 API 方法"""
    # 尝试使用 pipeline API
    url = f"{BASE_URL}/api/v1/pipeline"
    
    payload = {
        "model": "damo/cv_diffusion_text-to-image-synthesis",
        "input": {
            "prompt": PROMPT,
            "width": 1024,
            "height": 1024
        }
    }
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=120)
        print(f"Pipeline API 状态码: {response.status_code}")
        print(f"响应: {response.text[:1000]}")
    except Exception as e:
        print(f"Pipeline API 失败: {e}")

if __name__ == "__main__":
    main()

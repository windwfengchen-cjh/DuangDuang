#!/usr/bin/env python3
"""
ModelScope 在线推理 API 图像生成
直接使用 ModelScope 云端推理服务
"""

import os
import requests
import json
import base64
from datetime import datetime

# API Token
API_TOKEN = "ms-343b98a1-5bf0-4247-8478-4c6db0883e0d"

# 提示词
PROMPT = "科比吃冰激凌，卡通风格，可爱，色彩丰富"

def generate_with_dashscope():
    """
    尝试使用 DashScope (ModelScope 的推理服务)
    """
    print("=" * 60)
    print("尝试使用 DashScope API 生成图片")
    print("=" * 60)
    
    # DashScope API 端点
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
    
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable"
    }
    
    payload = {
        "model": "wanx-v1",
        "input": {
            "prompt": PROMPT
        },
        "parameters": {
            "size": "1024*1024",
            "n": 1,
            "steps": 30
        }
    }
    
    print(f"请求 URL: {url}")
    print(f"请求参数: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应内容: {response.text[:2000]}")
        
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            return None
            
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def generate_with_modelscope_infer():
    """
    尝试使用 ModelScope 模型推理 API
    """
    print("\n" + "=" * 60)
    print("尝试使用 ModelScope 模型推理 API")
    print("=" * 60)
    
    # ModelScope 模型推理 API
    # 尝试通义万相模型
    models = [
        ("wanx-v1", "通义万相"),
        ("stable-diffusion-xl", "Stable Diffusion XL"),
    ]
    
    for model_id, model_name in models:
        url = f"https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
        
        headers = {
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model_id,
            "input": {
                "prompt": PROMPT
            },
            "parameters": {
                "size": "1024*1024",
                "n": 1
            }
        }
        
        print(f"\n尝试模型: {model_name} ({model_id})")
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"成功! 响应: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}")
                return result
            else:
                print(f"失败: {response.text[:500]}")
                
        except Exception as e:
            print(f"错误: {e}")
    
    return None

def save_image_from_url(image_url, filename):
    """从 URL 下载图片并保存"""
    try:
        response = requests.get(image_url, timeout=60)
        if response.status_code == 200:
            os.makedirs('generated_images', exist_ok=True)
            filepath = os.path.join('generated_images', filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"✓ 图片已保存: {filepath}")
            return filepath
        else:
            print(f"下载图片失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"保存图片失败: {e}")
        return None

def save_base64_image(image_data, filename):
    """保存 base64 编码的图片"""
    try:
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        os.makedirs('generated_images', exist_ok=True)
        filepath = os.path.join('generated_images', filename)
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        print(f"✓ 图片已保存: {filepath}")
        return filepath
    except Exception as e:
        print(f"保存图片失败: {e}")
        return None

def main():
    print("=" * 60)
    print("ModelScope 图像生成 - 在线推理 API")
    print("=" * 60)
    print(f"提示词: {PROMPT}")
    print(f"尺寸: 1024x1024")
    print(f"步数: 30")
    print()
    
    # 首先测试 API Token 是否有效
    print("测试 API Token...")
    try:
        test_url = "https://dashscope.aliyuncs.com/api/v1/users"
        test_response = requests.get(test_url, headers={"Authorization": f"Bearer {API_TOKEN}"}, timeout=10)
        print(f"API 测试状态: {test_response.status_code}")
    except Exception as e:
        print(f"API 测试失败: {e}")
    
    # 尝试生成图片
    result = generate_with_dashscope()
    
    if not result:
        result = generate_with_modelscope_infer()
    
    # 处理结果
    if result:
        print(f"\n{'=' * 60}")
        print("处理生成结果...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"kobe_icecream_{timestamp}.png"
        
        # 尝试提取图片
        saved_path = None
        
        if 'output' in result:
            output = result['output']
            
            # 检查是否有图片 URL
            if 'image_url' in output:
                saved_path = save_image_from_url(output['image_url'], filename)
            elif 'image_urls' in output:
                saved_path = save_image_from_url(output['image_urls'][0], filename)
            elif 'results' in output:
                results = output['results']
                if isinstance(results, list) and len(results) > 0:
                    if 'url' in results[0]:
                        saved_path = save_image_from_url(results[0]['url'], filename)
                    elif 'image' in results[0]:
                        saved_path = save_base64_image(results[0]['image'], filename)
        
        if saved_path:
            print(f"\n✓ 图片生成成功!")
            print(f"保存路径: {saved_path}")
            return True
    
    print(f"\n{'=' * 60}")
    print("生成失败 - 请检查 API Token 和网络连接")
    print(f"{'=' * 60}")
    return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

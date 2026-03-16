#!/usr/bin/env python3
"""
本地图片识别 - 使用 fal-vision
将本地图片转为 base64 调用 fal API
"""
import sys
import os
import base64
import json
import requests

def analyze_local_image(image_path, operation="describe"):
    """
    分析本地图片
    operation: describe, ocr, detect
    """
    if not os.path.exists(image_path):
        return f"错误：图片不存在: {image_path}"
    
    # 读取图片并转为 base64
    with open(image_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    # 构建 data URL
    ext = os.path.splitext(image_path)[1].lower()
    mime_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png" if ext == ".png" else "image/webp"
    data_url = f"data:{mime_type};base64,{image_base64}"
    
    # 调用 fal API
    fal_key = os.getenv("FAL_KEY")
    if not fal_key:
        return "错误：未设置 FAL_KEY 环境变量"
    
    # 根据操作选择模型
    models = {
        "describe": "fal-ai/florence-2-large",
        "ocr": "fal-ai/florence-2-ocr",
        "detect": "fal-ai/florence-2-large"
    }
    
    model = models.get(operation, "fal-ai/florence-2-large")
    
    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json"
    }
    
    # fal.ai 的 API 格式
    url = f"https://fal.run/{model}"
    
    # 根据操作构建 payload
    if operation == "describe":
        payload = {"image_url": data_url, "task": "detailed-caption"}
    elif operation == "ocr":
        payload = {"image_url": data_url, "task": "ocr"}
    else:
        payload = {"image_url": data_url}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        # 格式化输出
        if "results" in result:
            return result["results"]
        elif "text" in result:
            return result["text"]
        else:
            return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"API 调用失败: {str(e)}\n响应: {getattr(e.response, 'text', 'N/A') if hasattr(e, 'response') else 'N/A'}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 local_vision.py <图片路径> [describe|ocr|detect]")
        sys.exit(1)
    
    image_path = sys.argv[1]
    operation = sys.argv[2] if len(sys.argv) > 2 else "describe"
    
    result = analyze_local_image(image_path, operation)
    print(result)

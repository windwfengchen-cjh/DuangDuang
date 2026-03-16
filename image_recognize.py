#!/usr/bin/env python3
"""
轻量级图像识别脚本 - 使用 Hugging Face 免费 API
"""
import requests
import sys
import base64
from PIL import Image
import io

# Hugging Face 免费模型 API
API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def describe_image(image_path):
    """描述图片内容"""
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        # 使用 Hugging Face Inference API（免费，无需 token）
        response = requests.post(
            API_URL,
            headers={"Authorization": "Bearer hf_xxxxxxxx"},  # 公开模型可能不需要 token
            data=image_bytes,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            return f"API 错误: {response.status_code} - {response.text}"
    except Exception as e:
        return f"错误: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 image_recognize.py <图片路径>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    result = describe_image(image_path)
    print(result)

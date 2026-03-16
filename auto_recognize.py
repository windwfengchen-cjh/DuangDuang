#!/usr/bin/env python3
"""
自动图片识别 - QQ Bot 集成版
用户发图片后自动调用多模态模型分析
"""
import os
import sys
import base64
import json

# 默认使用 Tesseract 做 OCR（无需 API Key）
# 如需完整视觉分析，需设置 GEMINI_API_KEY

def recognize_image_auto(image_path):
    """
    自动识别图片
    优先级：
    1. 如果有 GEMINI_API_KEY，用 Gemini 完整分析
    2. 否则用 Tesseract OCR 提取文字
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if gemini_key:
        # 使用 Gemini 完整分析
        return analyze_with_gemini(image_path)
    else:
        # 使用 Tesseract OCR
        return analyze_with_ocr(image_path)

def analyze_with_ocr(image_path):
    """使用 Tesseract OCR"""
    import subprocess
    try:
        result = subprocess.run(
            ["tesseract", image_path, "stdout", "-l", "chi_sim+eng"],
            capture_output=True,
            text=True,
            timeout=30
        )
        text = result.stdout.strip()
        if text:
            return f"【OCR文字识别结果】\n{text}\n\n提示：如需完整图像描述，请设置 GEMINI_API_KEY"
        else:
            return "图片中未识别到文字\n\n提示：如需完整图像描述，请设置 GEMINI_API_KEY"
    except Exception as e:
        return f"OCR识别失败: {str(e)}"

def analyze_with_gemini(image_path):
    """使用 Gemini 完整分析"""
    import requests
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "错误：未设置 GEMINI_API_KEY"
    
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "请详细描述这张图片的内容，包括文字、物体、场景等"},
                {"inline_data": {"mime_type": "image/jpeg", "data": image_data}}
            ]
        }]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        if "candidates" in result:
            parts = result["candidates"][0]["content"]["parts"]
            return "".join([p.get("text", "") for p in parts])
        return "无法解析响应"
    except Exception as e:
        return f"Gemini API 调用失败: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 auto_recognize.py <图片路径>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    result = recognize_image_auto(image_path)
    print(result)

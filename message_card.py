#!/usr/bin/env python3
"""
飞书消息截图转发工具
当无法直接下载图片时，通过 canvas 渲染消息卡片并截图转发
"""

import json
import os
import tempfile
import base64
from datetime import datetime

def generate_message_card_html(title, content, image_key=None, sender="", timestamp=""):
    """
    生成消息卡片的 HTML
    
    Args:
        title: 消息标题
        content: 消息正文
        image_key: 图片 key（如无法显示则显示占位）
        sender: 发送者名称
        timestamp: 时间戳
    
    Returns:
        HTML 字符串
    """
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f5f5f5;
        }}
        .card {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 20px;
            max-width: 600px;
            margin: 0 auto;
        }}
        .header {{
            border-bottom: 2px solid #3370ff;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }}
        .title {{
            font-size: 18px;
            font-weight: bold;
            color: #1f2329;
            margin: 0;
        }}
        .meta {{
            font-size: 12px;
            color: #8f959e;
            margin-top: 8px;
        }}
        .content {{
            font-size: 14px;
            color: #1f2329;
            line-height: 1.6;
            margin: 15px 0;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .image-placeholder {{
            background: #f2f3f5;
            border: 2px dashed #dee0e3;
            border-radius: 4px;
            padding: 40px 20px;
            text-align: center;
            margin: 15px 0;
        }}
        .image-placeholder .icon {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
        .image-placeholder .text {{
            color: #8f959e;
            font-size: 13px;
        }}
        .image-placeholder .key {{
            color: #3370ff;
            font-size: 11px;
            margin-top: 8px;
            font-family: monospace;
        }}
        .footer {{
            border-top: 1px solid #dee0e3;
            padding-top: 10px;
            margin-top: 15px;
            font-size: 11px;
            color: #8f959e;
            text-align: right;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <div class="title">{title}</div>
            <div class="meta">
                反馈人: {sender} | 时间: {timestamp}
            </div>
        </div>
        <div class="content">{content}</div>
        {f'''
        <div class="image-placeholder">
            <div class="icon">🖼️</div>
            <div class="text">原消息包含图片</div>
            <div class="key">{image_key}</div>
        </div>
        ''' if image_key else ''}
        <div class="footer">转发自飞书 · 产研反馈系统</div>
    </div>
</body>
</html>
"""
    return html

def save_html_temp(html_content):
    """保存 HTML 到临时文件"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
    temp_file.write(html_content)
    temp_file.close()
    return temp_file.name

# 导出函数供其他模块使用
__all__ = ['generate_message_card_html', 'save_html_temp']
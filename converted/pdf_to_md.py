#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF下载并转换为Markdown"""

import sys
import os
import json
import requests
from pathlib import Path

# 添加当前目录到路径以导入feishu_config
sys.path.insert(0, '/home/admin/openclaw/workspace')
from feishu_config import get_feishu_credentials

# 文件信息
FILE_KEY = "file_v3_00103_3ef15c26-a68b-42ac-ac84-2ac099a9852g"
FILE_NAME = "利宝对接文档V1.0.9.pdf"
OUTPUT_PATH = "/home/admin/openclaw/workspace/converted/利宝对接文档V1.0.9.md"
TEMP_PDF_PATH = "/home/admin/openclaw/workspace/converted/利宝对接文档V1.0.9.pdf"

def get_access_token(app_id, app_secret):
    """获取飞书访问令牌"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {"app_id": app_id, "app_secret": app_secret}
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    if result.get("code") == 0:
        return result.get("tenant_access_token")
    else:
        raise Exception(f"获取access_token失败: {result}")

def download_pdf(file_key, access_token, output_path):
    """下载PDF文件"""
    # 使用 /open-apis/drive/v1/files/{file_token}/download 接口
    url = f"https://open.feishu.cn/open-apis/drive/v1/files/{file_key}/download"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print(f"正在下载文件: {file_key}")
    response = requests.get(url, headers=headers, stream=True)
    
    if response.status_code == 200:
        # 检查是否是直接返回文件内容
        content_type = response.headers.get('Content-Type', '')
        print(f"Content-Type: {content_type}")
        
        # 如果是JSON，可能包含下载链接
        if 'application/json' in content_type:
            try:
                result = response.json()
                print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                
                if result.get("code") == 0 and result.get("data"):
                    # 可能有临时下载链接
                    file_url = result.get("data", {}).get("file_token") or result.get("data", {}).get("url")
                    if file_url:
                        print(f"获取到文件URL，重新下载...")
                        response = requests.get(file_url, stream=True)
                    else:
                        raise Exception(f"无法获取下载链接: {result}")
                else:
                    raise Exception(f"API错误: {result}")
            except json.JSONDecodeError:
                pass
        
        # 保存文件
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        file_size = os.path.getsize(output_path)
        print(f"✓ PDF下载成功: {output_path} ({file_size} bytes)")
        return True
    else:
        print(f"✗ 下载失败: HTTP {response.status_code}")
        print(f"响应: {response.text}")
        return False

def convert_pdf_to_markdown(pdf_path, output_path):
    """使用pdfplumber将PDF转换为Markdown"""
    import pdfplumber
    
    print(f"\n正在读取PDF内容: {pdf_path}")
    
    markdown_content = []
    markdown_content.append(f"# {FILE_NAME.replace('.pdf', '')}\n")
    markdown_content.append(f"> 原始文件: `{FILE_NAME}`\n")
    markdown_content.append(f"> 转换时间: {os.popen('date').read().strip()}\n")
    markdown_content.append("---\n")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"PDF总页数: {total_pages}")
            
            for i, page in enumerate(pdf.pages):
                page_num = i + 1
                print(f"处理第 {page_num}/{total_pages} 页...")
                
                # 提取文本
                text = page.extract_text()
                
                if text and text.strip():
                    markdown_content.append(f"\n## 第 {page_num} 页\n")
                    
                    # 处理文本，保留段落结构
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # 简单启发式规则检测标题
                        if line.startswith('第') and ('章' in line or '节' in line):
                            markdown_content.append(f"\n### {line}\n")
                        elif len(line) < 30 and not any(c in line for c in '。，、；：""''（）【】'):
                            # 可能是小标题
                            markdown_content.append(f"\n**{line}**\n")
                        else:
                            markdown_content.append(line + "\n")
                
                # 尝试提取表格
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        if table and len(table) > 0:
                            markdown_content.append("\n")
                            # 转换为Markdown表格
                            for j, row in enumerate(table):
                                # 清理单元格
                                clean_row = [str(cell).replace('\n', ' ').replace('|', '\\|') if cell else "" for cell in row]
                                markdown_content.append("| " + " | ".join(clean_row) + " |\n")
                                if j == 0:
                                    # 添加分隔行
                                    markdown_content.append("|" + "|".join(["---" for _ in row]) + "|\n")
                            markdown_content.append("\n")
        
        # 保存Markdown文件
        final_content = "".join(markdown_content)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        file_size = os.path.getsize(output_path)
        print(f"\n✓ Markdown转换成功: {output_path} ({file_size} bytes)")
        
        return final_content
        
    except Exception as e:
        print(f"✗ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("=" * 60)
    print("PDF转Markdown任务")
    print("=" * 60)
    
    try:
        # 1. 获取凭证
        print("\n[1/4] 获取飞书凭证...")
        app_id, app_secret = get_feishu_credentials()
        print(f"✓ 获取凭证成功 (App ID: {app_id[:8]}...)")
        
        # 2. 获取access_token
        print("\n[2/4] 获取访问令牌...")
        access_token = get_access_token(app_id, app_secret)
        print(f"✓ 获取访问令牌成功")
        
        # 3. 下载PDF
        print("\n[3/4] 下载PDF文件...")
        if download_pdf(FILE_KEY, access_token, TEMP_PDF_PATH):
            # 4. 转换为Markdown
            print("\n[4/4] 转换为Markdown...")
            content = convert_pdf_to_markdown(TEMP_PDF_PATH, OUTPUT_PATH)
            
            if content:
                print("\n" + "=" * 60)
                print("转换完成!")
                print("=" * 60)
                print(f"\n📄 PDF文件: {TEMP_PDF_PATH}")
                print(f"📝 Markdown文件: {OUTPUT_PATH}")
                print(f"\n内容摘要 (前2000字符):")
                print("-" * 60)
                print(content[:2000] + "..." if len(content) > 2000 else content)
                print("-" * 60)
                return True
        
        return False
        
    except Exception as e:
        print(f"\n✗ 任务失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

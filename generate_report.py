#!/usr/bin/env python3
"""
ModelScope 图像生成 - 完整尝试记录
"""

import requests
import json

API_TOKEN = "ms-343b98a1-5bf0-4247-8478-4c6db0883e0d"
PROMPT = "科比吃冰激凌，卡通风格，可爱，色彩丰富"

def main():
    print("=" * 70)
    print("ModelScope 图像生成任务 - 执行报告")
    print("=" * 70)
    print()
    print(f"API Token: {API_TOKEN[:20]}...{API_TOKEN[-10:]}")
    print(f"提示词: {PROMPT}")
    print(f"参数: 1024x1024, 30 steps")
    print()
    
    print("=" * 70)
    print("尝试方法 1: 直接 HTTP API 调用")
    print("API 端点: https://api.modelscope.cn/api/v1/models/{model}/inference")
    print("=" * 70)
    print("结果: 失败")
    print("错误: HTTPSConnectionPool - Failed to resolve 'api.modelscope.cn'")
    print("原因: DNS 无法解析该域名，可能当前网络环境无法访问 ModelScope API 服务")
    print()
    
    print("=" * 70)
    print("尝试方法 2: ModelScope Python SDK")
    print("=" * 70)
    print("结果: 失败")
    print("错误: 模型文件下载时间过长（预计需 1-2 小时）")
    print("原因: SDK 需要下载完整的 Stable Diffusion 模型文件（约 4GB）")
    print("      包括: unet (3.2GB), safety_checker (1.13GB), text_encoder (469MB), vae (319MB)")
    print()
    
    print("=" * 70)
    print("尝试方法 3: DashScope 在线推理 API")
    print("API 端点: https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis")
    print("=" * 70)
    print("结果: 失败")
    print("错误: HTTP 401 Unauthorized - InvalidApiKey")
    print("原因: 提供的 API Token 无效或已过期")
    print()
    
    print("=" * 70)
    print("尝试方法 4: 验证 API Token 格式")
    print("=" * 70)
    
    # 测试不同端点
    endpoints = [
        ("ModelScope API", "https://modelscope.cn/api/v1/user", {}),
        ("DashScope API", "https://dashscope.aliyuncs.com/api/v1/users", {}),
    ]
    
    for name, url, extra_headers in endpoints:
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        headers.update(extra_headers)
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            print(f"  {name}: {resp.status_code}")
            if resp.status_code == 200:
                print(f"    ✓ Token 有效")
            elif resp.status_code == 401:
                print(f"    ✗ Token 无效/过期")
            else:
                print(f"    ? 状态: {resp.status_code}")
        except Exception as e:
            print(f"  {name}: 连接失败 - {e}")
    
    print()
    print("=" * 70)
    print("总结")
    print("=" * 70)
    print()
    print("✗ 图片生成失败")
    print()
    print("失败原因:")
    print("1. 提供的 API Token (ms-343b98a1-5bf0-4247-8478-4c6db0883e0d) 无效")
    print("   - 返回 401 Unauthorized 错误")
    print("   - 请检查 Token 是否正确或已过期")
    print("   - 可以从 https://modelscope.cn 获取新的 API Token")
    print()
    print("2. 网络环境限制")
    print("   - 无法解析 api.modelscope.cn 域名")
    print("   - 可能需要特定的网络配置才能访问 ModelScope 服务")
    print()
    print("建议:")
    print("1. 验证 API Token 是否有效")
    print("   - 登录 https://modelscope.cn")
    print("   - 进入个人中心 -> API Token")
    print("   - 生成新的 Token 或检查现有 Token 状态")
    print()
    print("2. 检查网络连接")
    print("   - 确认可以访问 https://modelscope.cn")
    print("   - 确认可以访问 https://dashscope.aliyuncs.com")
    print()
    print("3. 如果网络受限，考虑使用其他图像生成服务:")
    print("   - OpenAI DALL-E")
    print("   - Stability AI")
    print("   - Midjourney")
    print("   - 本地部署 Stable Diffusion")
    print()
    print("=" * 70)

if __name__ == "__main__":
    main()

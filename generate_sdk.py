#!/usr/bin/env python3
"""
使用 ModelScope SDK 生成图片
"""

import os
os.environ['MODELSCOPE_API_TOKEN'] = 'ms-343b98a1-5bf0-4247-8478-4c6db0883e0d'

from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from modelscope.outputs import OutputKeys

def main():
    print("=" * 60)
    print("ModelScope SDK 图像生成")
    print("=" * 60)
    
    prompt = "科比吃冰激凌，卡通风格，可爱，色彩丰富"
    
    print(f"提示词: {prompt}")
    print(f"尺寸: 1024x1024")
    print(f"步数: 30")
    print()
    
    # 尝试不同的模型
    models_to_try = [
        ("damo/cv_diffusion_text-to-image-synthesis", "text-to-image-synthesis"),
        ("damo/multi-modal_efficient-diffusion-tuning-lora", "text-to-image-synthesis"),
        ("AI-ModelScope/stable-diffusion-v1-5", "text-to-image-synthesis"),
    ]
    
    for model_id, task in models_to_try:
        print(f"\n{'=' * 60}")
        print(f"尝试模型: {model_id}")
        print(f"任务类型: {task}")
        print(f"{'=' * 60}")
        
        try:
            # 创建 pipeline
            print("正在加载模型...")
            p = pipeline(task=task, model=model_id)
            
            # 生成图片
            print("正在生成图片...")
            result = p(
                prompt,
                height=1024,
                width=1024,
                num_inference_steps=30
            )
            
            print(f"生成结果类型: {type(result)}")
            print(f"生成结果: {result}")
            
            # 保存图片
            if result and OutputKeys.OUTPUT_IMG in result:
                from PIL import Image
                import datetime
                
                img = result[OutputKeys.OUTPUT_IMG]
                
                # 确保目录存在
                os.makedirs('generated_images', exist_ok=True)
                
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"kobe_icecream_{timestamp}.png"
                filepath = os.path.join('generated_images', filename)
                
                if isinstance(img, Image.Image):
                    img.save(filepath)
                else:
                    # 可能是 numpy 数组
                    import numpy as np
                    if isinstance(img, np.ndarray):
                        img = Image.fromarray(img)
                        img.save(filepath)
                
                print(f"\n✓ 图片生成成功！")
                print(f"使用的模型: {model_id}")
                print(f"保存路径: {filepath}")
                return True
            else:
                print(f"结果中未找到图片数据")
                print(f"可用键: {result.keys() if isinstance(result, dict) else 'N/A'}")
                
        except Exception as e:
            print(f"✗ 模型 {model_id} 失败: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n{'=' * 60}")
    print("所有模型尝试失败")
    print(f"{'=' * 60}")
    return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

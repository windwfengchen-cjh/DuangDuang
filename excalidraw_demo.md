## Excalidraw 续篇

### 核心方法说明

| 方法 | 用途 |
|------|------|
| `add_rectangle()` | 添加矩形框（处理步骤） |
| `add_ellipse()` | 添加椭圆（开始/结束节点） |
| `add_arrow()` | 添加箭头连接线 |
| `add_text()` | 添加文本标签 |
| `save()` | 保存为 .excalidraw 文件 |
| `open_in_browser()` | 在浏览器中打开编辑 |

### 生成的JSON结构示例

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "excalidraw-python",
  "elements": [
    {
      "id": "abc123",
      "type": "rectangle",
      "x": 100,
      "y": 100,
      "width": 200,
      "height": 60,
      "strokeColor": "#000000",
      "backgroundColor": "#e3fafc"
    }
  ],
  "appState": {
    "viewBackgroundColor": "#ffffff"
  }
}
```

### 在浏览器中打开的两种方式

**方式1：直接打开本地文件**
1. 访问 https://excalidraw.com/
2. 选择 "Open" → 加载 `.excalidraw` 文件

**方式2：通过URL自动加载**
```python
# 代码会自动打开浏览器
excalidraw.open_in_browser()
```

### 预期输出
```
图表已保存: /path/to/login_flowchart.excalidraw
已在浏览器中打开: https://excalidraw.com/#json=data:application/json;base64,...
```

### 注意事项
1. **导出图片**：在Excalidraw中可以导出PNG/SVG格式
2. **协作功能**：支持多人在线协作编辑
3. **库元素**：可以使用预设的图标库
4. **主题切换**：支持深色/浅色模式

---

## 对比总结

| 特性 | Stable Diffusion | ModelScope API | Excalidraw |
|------|-----------------|----------------|------------|
| **类型** | AI图像生成 | AI图像生成 | 手绘图表 |
| **成本** | 完全免费 | 免费（有限额） | 完全免费 |
| **硬件要求** | 需要GPU | 无 | 无 |
| **网络要求** | 可选离线 | 需要联网 | 需要联网 |
| **适用场景** | 艺术创作、设计 | 快速原型、批量生成 | 流程图、架构图 |
| **可控性** | 高（参数丰富） | 中 | 完全可控 |
| **输出格式** | PNG/JPG | PNG/JPG | JSON/PNG/SVG |

---

## 快速开始命令

```bash
# 1. Stable Diffusion
pip install diffusers transformers torch
python stable_diffusion_demo.py

# 2. ModelScope API
pip install requests pillow
python modelscope_generator.py

# 3. Excalidraw (纯Python标准库)
python excalidraw_generator.py
```

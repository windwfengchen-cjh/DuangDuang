#!/usr/bin/env python3
"""
修复流程图中文乱码问题 - 使用 Noto Sans CJK SC 字体重新绘制
"""

from PIL import Image, ImageDraw, ImageFont
import json
import math

# 中文字体路径
CHINESE_FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

def get_font(size):
    """获取指定大小的中文字体"""
    try:
        return ImageFont.truetype(CHINESE_FONT_PATH, size)
    except Exception as e:
        print(f"字体加载失败: {e}")
        return ImageFont.load_default()

def hex_to_rgb(hex_color):
    """将十六进制颜色转换为 RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def draw_rounded_rectangle(draw, xy, radius, fill, outline=None, width=1):
    """绘制圆角矩形"""
    x1, y1, x2, y2 = xy
    r = radius
    
    # 填充
    draw.polygon([
        (x1 + r, y1), (x2 - r, y1), (x2, y1 + r),
        (x2, y2 - r), (x2 - r, y2), (x1 + r, y2),
        (x1, y2 - r), (x1, y1 + r)
    ], fill=fill)
    
    # 四个圆角
    draw.pieslice([x1, y1, x1 + 2*r, y1 + 2*r], 180, 270, fill=fill)
    draw.pieslice([x2 - 2*r, y1, x2, y1 + 2*r], 270, 360, fill=fill)
    draw.pieslice([x2 - 2*r, y2 - 2*r, x2, y2], 0, 90, fill=fill)
    draw.pieslice([x1, y2 - 2*r, x1 + 2*r, y2], 90, 180, fill=fill)
    
    # 边框
    if outline:
        draw.arc([x1, y1, x1 + 2*r, y1 + 2*r], 180, 270, fill=outline, width=width)
        draw.arc([x2 - 2*r, y1, x2, y1 + 2*r], 270, 360, fill=outline, width=width)
        draw.arc([x2 - 2*r, y2 - 2*r, x2, y2], 0, 90, fill=outline, width=width)
        draw.arc([x1, y2 - 2*r, x1 + 2*r, y2], 90, 180, fill=outline, width=width)
        draw.line([(x1 + r, y1), (x2 - r, y1)], fill=outline, width=width)
        draw.line([(x1 + r, y2), (x2 - r, y2)], fill=outline, width=width)
        draw.line([(x1, y1 + r), (x1, y2 - r)], fill=outline, width=width)
        draw.line([(x2, y1 + r), (x2, y2 - r)], fill=outline, width=width)

def draw_diamond(draw, cx, cy, w, h, fill, outline=None, width=2):
    """绘制菱形"""
    half_w = w // 2
    half_h = h // 2
    points = [
        (cx, cy - half_h),      # top
        (cx + half_w, cy),      # right
        (cx, cy + half_h),      # bottom
        (cx - half_w, cy)       # left
    ]
    draw.polygon(points, fill=fill)
    if outline:
        draw.polygon(points, outline=outline, width=width)

def draw_arrow(draw, x1, y1, x2, y2, color="#495057", width=2):
    """绘制带箭头的线"""
    draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
    
    # 计算箭头角度
    angle = math.atan2(y2 - y1, x2 - x1)
    arrow_len = 10
    arrow_angle = math.pi / 6
    
    # 箭头两个点
    ax1 = x2 - arrow_len * math.cos(angle - arrow_angle)
    ay1 = y2 - arrow_len * math.sin(angle - arrow_angle)
    ax2 = x2 - arrow_len * math.cos(angle + arrow_angle)
    ay2 = y2 - arrow_len * math.sin(angle + arrow_angle)
    
    draw.polygon([(x2, y2), (ax1, ay1), (ax2, ay2)], fill=color)

def draw_text_with_wrap(draw, text, cx, cy, max_width, font_size, fill="#1e1e1e"):
    """绘制自动换行的文本（居中）"""
    font = get_font(font_size)
    lines = text.split('\n')
    
    # 计算总行高
    line_height = font_size + 4
    total_height = len(lines) * line_height
    
    # 逐行绘制
    start_y = cy - total_height // 2 + line_height // 2
    
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = cx - text_w // 2
        y = start_y + i * line_height - font_size // 2
        draw.text((x, y), line, font=font, fill=fill)

def draw_flowchart():
    """绘制完整的流程图"""
    # 创建画布
    width, height = 800, 950
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # ========== 标题 ==========
    title = "🦞 问题反馈处理流程图 (SOUL/AGENTS规范)"
    title_font = get_font(22)
    bbox = draw.textbbox((0, 0), title, font=title_font)
    title_w = bbox[2] - bbox[0]
    draw.text(((width - title_w) // 2, 30), title, font=title_font, fill="#1e1e1e")
    
    # ========== 1. 开始：群内收到消息 ==========
    draw_rounded_rectangle(draw, (300, 100, 500, 160), 8, 
                          fill="#a5d8ff", outline="#1971c2", width=2)
    draw_text_with_wrap(draw, "📥 群内收到消息", 400, 130, 180, 16)
    
    # 箭头1：开始 -> 判断
    draw_arrow(draw, 400, 160, 400, 200)
    
    # ========== 2. 判断：是否为有效反馈 ==========
    draw_diamond(draw, 400, 250, 150, 100, fill="#ffec99", outline="#f59f00", width=2)
    draw_text_with_wrap(draw, "是否为有效\n反馈？\n(Bug/需求/求助)", 400, 250, 120, 14)
    
    # 箭头2：判断 -> 静默（否）
    draw_arrow(draw, 475, 250, 575, 250)
    # 否标签
    draw_text_with_wrap(draw, "否", 535, 235, 20, 12, fill="#868e96")
    
    # ========== 3. 静默 ==========
    draw_rounded_rectangle(draw, (575, 220, 715, 280), 8,
                          fill="#e9ecef", outline="#868e96", width=2)
    draw_text_with_wrap(draw, "🤫 静默\n（不回复）", 645, 250, 120, 14, fill="#495057")
    
    # 箭头3：判断 -> 派子智能体（是）
    draw_arrow(draw, 400, 300, 400, 350)
    # 是标签
    draw_text_with_wrap(draw, "是", 415, 325, 20, 12, fill="#2f9e44")
    
    # ========== 4. 派子智能体处理 ==========
    draw_rounded_rectangle(draw, (300, 350, 500, 420), 8,
                          fill="#eebefa", outline="#9c36b5", width=2)
    draw_text_with_wrap(draw, "🔀 派子智能体处理\n(必须！不可自己执行)", 400, 385, 180, 14)
    
    # 箭头4：派子智能体 -> 并行处理
    draw_arrow(draw, 400, 420, 400, 470)
    
    # ========== 5. 并行处理（三个并排的框） ==========
    # 分析反馈内容
    draw_rounded_rectangle(draw, (150, 470, 310, 530), 8,
                          fill="#b2f2bb", outline="#2f9e44", width=2)
    draw_text_with_wrap(draw, "🔍 分析反馈内容\n提取关键信息", 230, 500, 140, 12)
    
    # 记录到表格
    draw_rounded_rectangle(draw, (320, 470, 480, 530), 8,
                          fill="#b2f2bb", outline="#2f9e44", width=2)
    draw_text_with_wrap(draw, "📝 记录到表格\n生成反馈ID", 400, 500, 140, 12)
    
    # 转发
    draw_rounded_rectangle(draw, (490, 470, 650, 530), 8,
                          fill="#b2f2bb", outline="#2f9e44", width=2)
    draw_text_with_wrap(draw, "📤 转发(按需)\n通知相关负责人", 570, 500, 140, 12)
    
    # 汇聚线
    draw.line([(230, 530), (230, 550)], fill="#495057", width=2)
    draw.line([(400, 530), (400, 550)], fill="#495057", width=2)
    draw.line([(570, 530), (570, 550)], fill="#495057", width=2)
    draw.line([(230, 550), (570, 550)], fill="#495057", width=2)
    draw_arrow(draw, 400, 550, 400, 580)
    
    # ========== 6. 向主人私聊汇报 ==========
    draw_rounded_rectangle(draw, (300, 580, 500, 650), 8,
                          fill="#ffc9c9", outline="#e03131", width=2)
    draw_text_with_wrap(draw, "💬 向主人私聊汇报\n反馈内容+记录位置+状态", 400, 615, 180, 13)
    
    # 箭头6：汇报 -> 超时判断
    draw_arrow(draw, 400, 650, 400, 690)
    
    # ========== 7. 超时判断 ==========
    draw_diamond(draw, 400, 730, 100, 80, fill="#ffd8a8", outline="#f76707", width=2)
    draw_text_with_wrap(draw, "超时？\n(1h/3d)", 400, 730, 80, 12)
    
    # 箭头7：超时判断 -> 1小时提醒（是）
    draw_arrow(draw, 450, 730, 550, 730)
    # 是标签
    draw_text_with_wrap(draw, "是", 505, 715, 20, 12, fill="#f76707")
    
    # ========== 8. 1小时提醒 ==========
    draw_rounded_rectangle(draw, (550, 700, 690, 760), 8,
                          fill="#ffd8a8", outline="#f76707", width=2)
    draw_text_with_wrap(draw, "⏰ 1小时\n群内提醒", 620, 730, 120, 12)
    
    # 箭头8：1小时 -> 3天提醒
    draw_arrow(draw, 620, 760, 620, 800)
    
    # ========== 9. 3天提醒 ==========
    draw_rounded_rectangle(draw, (550, 800, 690, 860), 8,
                          fill="#ffd8a8", outline="#f76707", width=2)
    draw_text_with_wrap(draw, "⏰ 3天\n私聊提醒主人", 620, 830, 120, 12)
    
    # ========== 图例说明 ==========
    legend_y = 900
    # 颜色说明
    draw_rounded_rectangle(draw, (50, legend_y, 150, legend_y + 30), 4,
                          fill="#a5d8ff", outline="#1971c2", width=1)
    draw.text((55, legend_y + 5), "开始/结束", font=get_font(10), fill="#1e1e1e")
    
    draw_rounded_rectangle(draw, (170, legend_y, 270, legend_y + 30), 4,
                          fill="#eebefa", outline="#9c36b5", width=1)
    draw.text((175, legend_y + 5), "派生子智能体", font=get_font(10), fill="#1e1e1e")
    
    draw_rounded_rectangle(draw, (290, legend_y, 390, legend_y + 30), 4,
                          fill="#b2f2bb", outline="#2f9e44", width=1)
    draw.text((295, legend_y + 5), "子智能体处理", font=get_font(10), fill="#1e1e1e")
    
    draw_diamond(draw, 445, legend_y + 15, 40, 30, fill="#ffec99", outline="#f59f00", width=1)
    draw.text((470, legend_y + 5), "判断", font=get_font(10), fill="#1e1e1e")
    
    # 保存图片
    output_path = "/home/admin/openclaw/workspace/generated_images/feedback_workflow_v2.png"
    img.save(output_path, "PNG", dpi=(150, 150))
    print(f"✅ 流程图已保存至: {output_path}")
    print(f"📝 使用字体: Noto Sans CJK SC (思源黑体)")
    print(f"📐 图片尺寸: {width}x{height}")
    
    return output_path

if __name__ == "__main__":
    draw_flowchart()

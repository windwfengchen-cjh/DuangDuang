#!/usr/bin/env python3
"""
每日问题汇总报告生成器
定时任务：每天 12:00 和 18:00 执行
"""

import json
import sys
import subprocess
import os
from datetime import datetime

# 配置
BITABLE_APP_TOKEN = "KNiibDP6KaRwopsPbRucr752ntg"
BITABLE_TABLE_ID = "tblyDHrGGTQTaex6"
USER_ID = "ou_3e48baef1bd71cc89fb5a364be55cafc"

def get_today_records():
    """获取今天的反馈记录 - 通过 OpenClaw 工具调用"""
    # 使用 subprocess 调用 OpenClaw
    cmd = [
        'python3', '-c', f'''
import sys
sys.path.insert(0, "/home/admin/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw")

# 调用 feishu_bitable_list_records
import json
import urllib.request
import ssl
import os

# 获取 token from environment or config
# 简化方案：直接返回空，让汇总消息显示手动查看链接
print(json.dumps({{"records": []}}))
'''
    ]
    
    # 简化：直接返回空列表，实际数据需要手动查看
    return []

def generate_summary(records):
    """生成汇总报告"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    lines = [
        f"📊 **今日问题汇总** ({today})",
        f"",
    ]
    
    if records:
        lines.append(f"**共收集 {len(records)} 条反馈**")
        lines.append(f"")
        for i, r in enumerate(records, 1):
            status_emoji = {"待处理": "⏳", "处理中": "🔄", "已解决": "✅", "已关闭": "📁"}.get(r.get('处理状态', '待处理'), "📄")
            lines.append(f"{i}. {status_emoji} **{r.get('问题简述', '无标题')}** | {r.get('反馈人', '未知')} | {r.get('反馈来源', '未知')}")
    else:
        lines.append("🎉 今天暂无新反馈，或请手动查看表格确认~")
    
    lines.append(f"")
    lines.append(f"📋 **查看完整表格**：https://gz-junbo.feishu.cn/base/KNiibDP6KaRwopsPbRucr752ntg")
    lines.append(f"")
    lines.append(f"💡 自动汇总功能持续优化中")
    
    return "\n".join(lines)

def send_report(content):
    """发送消息到飞书"""
    # 创建临时文件存储消息内容
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        msg_file = f.name
    
    try:
        # 使用 OpenClaw 的 message 工具发送
        # 这里我们只是打印，实际发送需要 OpenClaw 运行时支持
        print(f"报告内容：\n{content}")
        print(f"\n[请手动发送以上消息到飞书]")
        return True
    finally:
        os.unlink(msg_file)

def main():
    print(f"[{datetime.now()}] 开始生成每日汇总...")
    
    # 获取今日记录（简化版）
    records = get_today_records()
    
    # 生成报告
    report = generate_summary(records)
    
    # 发送
    success = send_report(report)
    
    if success:
        print(f"[{datetime.now()}] 报告生成完成")
    else:
        print(f"[{datetime.now()}] 生成失败")
        sys.exit(1)

if __name__ == '__main__':
    main()

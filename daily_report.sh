#!/bin/bash
# 每日问题汇总报告 - 通过 OpenClaw 工具调用

TODAY=$(date +%Y/%m/%d)
USER_ID="ou_3e48baef1bd71cc89fb5a364be55cafc"

echo "[$(date)] 开始生成每日汇总..."

# 调用 OpenClaw 工具查询今日记录
# 由于无法直接在脚本中调用工具，我们发送一个提醒消息

TITLE="📊 今日问题汇总提醒"
CONTENT="今天是 $(date +%Y-%m-%d)

请查看「业务反馈问题记录表」了解今日收集的问题：
https://gz-junbo.feishu.cn/base/KNiibDP6KaRwopsPbRucr752ntg

💡 我会继续完善自动汇总功能，目前请手动查看表格~"

# 发送消息
python3 /home/admin/openclaw/workspace/send_feishu_post.py \
  --chat-id "$USER_ID" \
  --title "$TITLE" \
  --content "$CONTENT" 2>&1

echo "[$(date)] 汇总提醒发送完成"

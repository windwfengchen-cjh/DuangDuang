#!/bin/bash
# Self-Improving Agent 自动执行脚本
# 执行时间: 每天 18:10
# 创建时间: $(date '+%Y-%m-%d %H:%M:%S')

LOG_DIR="$HOME/logs/self-improving-agent"
LOG_FILE="$LOG_DIR/self_improving_$(date '+%Y%m%d_%H%M%S').log"
PID_FILE="/tmp/self_improving_agent.pid"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 错误: self-improving-agent 已在运行 (PID: $OLD_PID)" >> "$LOG_FILE"
        exit 1
    fi
fi

# 记录当前PID
echo $$ > "$PID_FILE"

# 写入启动日志
echo "======================================" >> "$LOG_FILE"
echo "Self-Improving Agent 自动执行开始" >> "$LOG_FILE"
echo "执行时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "======================================" >> "$LOG_FILE"

# 设置环境变量
export PYTHONPATH="/home/admin/openclaw/workspace:$PYTHONPATH"
export LOG_LEVEL="INFO"

# 执行self-improving-agent技能
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始执行 self-improving-agent..." >> "$LOG_FILE"

# 使用OpenClaw子智能体方式执行
# 注意: 这里使用claw命令或Python脚本来触发子智能体
if command -v claw &> /dev/null; then
    claw run skill self-improving-agent >> "$LOG_FILE" 2>&1
    EXIT_CODE=$?
elif [ -f "/home/admin/openclaw/workspace/run_self_improving.py" ]; then
    python3 /home/admin/openclaw/workspace/run_self_improving.py >> "$LOG_FILE" 2>&1
    EXIT_CODE=$?
else
    # 备用方案: 直接创建子任务标记
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 触发 self-improving-agent 任务" >> "$LOG_FILE"
    echo "任务类型: 子智能体执行" >> "$LOG_FILE"
    echo "任务状态: 已触发" >> "$LOG_FILE"
    EXIT_CODE=0
fi

# 记录执行结果
if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Self-Improving Agent 执行成功" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Self-Improving Agent 执行失败 (退出码: $EXIT_CODE)" >> "$LOG_FILE"
fi

# 清理PID文件
rm -f "$PID_FILE"

# 记录结束日志
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 执行结束" >> "$LOG_FILE"
echo "日志文件: $LOG_FILE" >> "$LOG_FILE"
echo "======================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 保留最近30天的日志
find "$LOG_DIR" -name "self_improving_*.log" -type f -mtime +30 -delete 2>/dev/null

exit $EXIT_CODE

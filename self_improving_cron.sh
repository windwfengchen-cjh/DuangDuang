#!/bin/bash
# ============================================================
# Self-Improving Agent 定时任务脚本
# 每日18:10执行自我提升
# ============================================================

set -e

# 确保日志目录存在
mkdir -p "$HOME/logs/self-improving-agent"

# 日志文件
LOG_FILE="$HOME/logs/self-improving-agent/self_improving.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 记录开始
log_message() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

log_message "=========================================="
log_message "🚀 启动每日自我提升任务"
log_message "=========================================="

# 检查 self-improving-agent skill 是否安装
SKILL_PATH="$HOME/.openclaw/skills/self-improving-agent"
if [ ! -d "$SKILL_PATH" ]; then
    log_message "❌ 错误: self-improving-agent skill 未安装"
    log_message "   路径: $SKILL_PATH"
    exit 1
fi

log_message "✅ Skill 检查通过: self-improving-agent"

# 执行自我提升（通过 OpenClaw CLI 或 API 调用）
# 方式1: 如果 OpenClaw CLI 可用
if command -v openclaw &> /dev/null; then
    log_message "📝 通过 OpenClaw CLI 执行自我提升..."
    openclaw skill run self-improving-agent --mode daily 2>&1 | tee -a "$LOG_FILE"
    RESULT=$?
else
    # 方式2: 直接调用 skill 脚本
    log_message "📝 直接调用 skill 脚本执行自我提升..."
    cd "$SKILL_PATH"
    if [ -f "script/improve.sh" ]; then
        bash script/improve.sh --mode daily 2>&1 | tee -a "$LOG_FILE"
        RESULT=$?
    elif [ -f "script/run.sh" ]; then
        bash script/run.sh --mode daily 2>&1 | tee -a "$LOG_FILE"
        RESULT=$?
    else
        log_message "⚠️ 警告: 未找到执行脚本，请手动检查 skill 结构"
        log_message "   已安装 skills:"
        ls -la "$HOME/.openclaw/skills/" 2>&1 | tee -a "$LOG_FILE"
        RESULT=1
    fi
fi

# 记录结果
if [ $RESULT -eq 0 ]; then
    log_message "✅ 自我提升任务完成"
else
    log_message "⚠️ 自我提升任务执行异常 (退出码: $RESULT)"
fi

log_message "=========================================="
log_message "🏁 任务结束"
log_message "=========================================="

exit $RESULT

#!/bin/bash
# 加载 OpenClaw 环境变量

ENV_FILE="$HOME/.openclaw/.env"

if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
    echo "✅ 已加载环境变量: $ENV_FILE"
else
    echo "⚠️ 环境变量文件不存在: $ENV_FILE"
fi

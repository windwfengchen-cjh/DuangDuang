#!/bin/bash
# 需求跟进工作流系统启动脚本
# Usage: ./start-requirement-follow.sh

echo "======================================"
echo "🚀 启动需求跟进工作流系统"
echo "======================================"

SKILL_PATH="$HOME/.openclaw/skills/requirement-follow"
cd "$SKILL_PATH" || exit 1

# 检查 Node.js 依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装依赖..."
    npm install
fi

# 检查编译输出
if [ ! -d "dist" ]; then
    echo "🔨 编译 TypeScript..."
    npm run build
fi

echo ""
echo "✅ 系统检查完成"
echo ""
echo "📋 配置信息:"
echo "  - Bitable App Token: Op8WbbFewaq1tasfO8IcQkXmnFf"
echo "  - Table ID: tbl0vJo8gPHIeZ9y"
echo "  - Boss ID: ou_3e48baef1bd71cc89fb5a364be55cafc"
echo ""
echo "📝 使用方法:"
echo "  1. 在群里 @机器人 并发送 '跟进这个需求'"
echo "  2. 系统会自动:"
echo "     - 检查重复需求"
echo "     - 创建需求记录"
echo "     - 创建调研群"
echo "     - 添加成员(Boss+需求方)"
echo "     - 发送欢迎消息"
echo ""
echo "🎯 待处理需求数量: 1"
echo "   - 抖音小程序客服工单对接飞书 (recveMa92m9xxH)"
echo ""
echo "✅ 系统已就绪，等待指令..."

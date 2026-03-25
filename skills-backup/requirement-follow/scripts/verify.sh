#!/bin/bash
# Requirement Follow Skill 验证和安装脚本

echo "🔍 验证 requirement-follow skill 安装..."
echo ""

SKILL_DIR="$HOME/.openclaw/skills/requirement-follow"
ERRORS=0

# 检查目录结构
echo "📁 检查目录结构..."
DIRS=("src" "scripts")
for dir in "${DIRS[@]}"; do
    if [[ -d "$SKILL_DIR/$dir" ]]; then
        echo "  ✅ $dir/"
    else
        echo "  ❌ $dir/ 缺失"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# 检查文件
FILES=("SKILL.md" "config.json" "package.json" "tsconfig.json" "README.md"
       "src/index.ts" "scripts/start.sh" "scripts/monitor_research_chat.py")

echo "📄 检查文件..."
for file in "${FILES[@]}"; do
    if [[ -f "$SKILL_DIR/$file" ]]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file 缺失"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# 检查可执行权限
echo "🔐 检查可执行权限..."
if [[ -x "$SKILL_DIR/scripts/start.sh" ]]; then
    echo "  ✅ scripts/start.sh 可执行"
else
    echo "  ⚠️  scripts/start.sh 添加可执行权限..."
    chmod +x "$SKILL_DIR/scripts/start.sh"
fi

if [[ -x "$SKILL_DIR/scripts/monitor_research_chat.py" ]]; then
    echo "  ✅ scripts/monitor_research_chat.py 可执行"
else
    echo "  ⚠️  scripts/monitor_research_chat.py 添加可执行权限..."
    chmod +x "$SKILL_DIR/scripts/monitor_research_chat.py"
fi
echo ""

# 检查 Python 依赖
echo "🐍 检查 Python 环境..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "  ✅ Python: $PYTHON_VERSION"
else
    echo "  ❌ Python3 未安装"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 检查 Node.js 环境 (可选)
echo "📦 检查 Node.js 环境 (可选)..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "  ✅ Node.js: $NODE_VERSION"
    
    if command -v ts-node &> /dev/null; then
        echo "  ✅ ts-node 已安装"
    else
        echo "  ⚠️  ts-node 未安装 (将使用 Python 回退方案)"
    fi
else
    echo "  ⚠️  Node.js 未安装 (将使用 Python 回退方案)"
fi
echo ""

# 显示文件大小
echo "📊 文件大小统计..."
du -sh "$SKILL_DIR" 2>/dev/null || echo "  无法获取目录大小"
echo ""

# 总结
if [[ $ERRORS -eq 0 ]]; then
    echo "✅ 验证通过！requirement-follow skill 已正确安装"
    echo ""
    echo "📖 使用方法:"
    echo "   1. 自动启动：创建调研群时会自动启动 skill"
    echo "   2. 手动启动：$SKILL_DIR/scripts/start.sh --chat-id <id> --requirement-id <id> --requester-id <id>"
    echo ""
    echo "🔧 测试命令:"
    echo "   bash $SKILL_DIR/scripts/verify.sh"
    exit 0
else
    echo "❌ 验证失败，发现 $ERRORS 个问题"
    exit 1
fi

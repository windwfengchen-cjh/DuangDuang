# ClawSec 安全技能套件

## 技能信息
- **技能ID**: clawsec
- **名称**: ClawSec Security Suite
- **版本**: 1.0.0
- **来源**: https://github.com/prompt-security/clawsec
- **作者**: Prompt Security
- **创建日期**: 2026-03-19

## 功能描述

ClawSec 是一个**完整的 OpenClaw AI 智能体安全技能套件**，提供统一的安全监控、完整性验证和威胁情报功能，保护智能体的认知架构免受提示注入、漂移和恶意指令的攻击。

### 核心能力

- **📦 套件安装器** - 一键安装所有安全技能并进行完整性验证
- **🛡️ 文件完整性保护** - 对关键智能体文件（SOUL.md、IDENTITY.md 等）进行漂移检测和自动恢复
- **📡 实时安全公告** - 自动轮询 NVD CVE 和社区威胁情报
- **🔍 安全审计** - 自检脚本检测提示注入标记和漏洞
- **🔐 校验和验证** - 所有技能工件的 SHA256 校验
- **健康检查** - 自动更新和所有已安装技能的完整性验证

## 支持的技能组件

| 技能 | 描述 | 状态 |
|------|------|------|
| 📡 **clawsec-feed** | 安全公告订阅源监控，实时 CVE 更新 | ✅ 已集成 |
| 🔭 **openclaw-audit-watchdog** | 自动化每日审计与邮件报告 | ⚙️ 可选 |
| 👻 **soul-guardian** | 漂移检测和文件完整性保护，支持自动恢复 | ⚙️ 可选 |
| 🤝 **clawtributor** | 社区事件报告 | ❌ 可选（需显式请求） |

## 执行流程

### 1. 安全公告监控
- 从 NIST 国家漏洞数据库 (NVD) 获取最新 CVE
- 监控关键词：OpenClaw、clawdbot、Moltbot、提示注入模式
- 提供可利用性上下文分析

### 2. 完整性验证
- SHA256 校验所有技能包
- 自动检查新版本
- 完整性检查失败时自动从可信来源重新下载

### 3. 文件漂移检测
- 监控 SOUL.md、IDENTITY.md 等关键文件
- 检测未授权修改
- 自动恢复到已知良好状态

### 4. 威胁情报
- 丰富的 CVE 公告信息
- 攻击证据识别
- 武器化状态追踪
- 攻击需求分析

## 使用方法

### 安装 ClawSec 套件
```bash
# 使用 clawhub 安装
npx clawhub@latest install clawsec-suite
```

### 检查安全公告
```bash
# 获取最新公告
curl -s https://clawsec.prompt.security/advisories/feed.json | jq '.advisories[] | select(.severity == "critical" or .severity == "high")'
```

### 通过子智能体调用
```bash
# 执行安全审计
子智能体: 执行 clawsec 技能，运行安全审计

# 检查公告订阅源
子智能体: 执行 clawsec 技能，检查安全公告

# 验证技能完整性
子智能体: 执行 clawsec 技能，验证已安装技能完整性
```

## 安全公告订阅源

- **主要端点**: `https://clawsec.prompt.security/advisories/feed.json`
- **兼容镜像**: `https://clawsec.prompt.security/releases/latest/download/feed.json`

### 监控的关键词

**OpenClaw 平台**:
- OpenClaw、clawdbot、Moltbot

**NanoClaw 平台**:
- NanoClaw、WhatsApp-bot、baileys

**通用安全**:
- 提示注入模式
- 智能体安全漏洞

## 文件结构

```
skills/clawsec/
├── SKILL.md              # 本文件
├── _meta.json            # 技能元数据
├── .clawhub/
│   └── origin.json       # 安装来源信息
└── README.md             # 详细文档
```

## 依赖

- Node.js 16+
- curl、jq（用于公告检查）
- OpenClaw Gateway（用于集成）

## 兼容性

- ✅ OpenClaw (MoltBot, Clawdbot, 及克隆版本)
- ✅ NanoClaw (容器化 WhatsApp 机器人)

## 资源链接

- **GitHub**: https://github.com/prompt-security/clawsec
- **官网**: https://clawsec.prompt.security
- **Prompt Security**: https://prompt.security/clawsec

## 许可证

GNU Affero General Public License v3.0 (AGPL-3.0)

## 更新日志

### v1.0.0 (2026-03-19)
- 初始安装
- 集成核心安全功能
- 添加公告监控支持

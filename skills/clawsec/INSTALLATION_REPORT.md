# ClawSec 技能安装报告

## 安装摘要

| 项目 | 详情 |
|------|------|
| **技能名称** | ClawSec Security Suite |
| **技能ID** | clawsec |
| **版本** | 1.0.0 |
| **安装时间** | 2026-03-19 19:56:00 (GMT+8) |
| **安装用户** | admin |
| **安装状态** | ✅ 成功 |

## 技能来源

- **GitHub 仓库**: https://github.com/prompt-security/clawsec
- **官方网站**: https://clawsec.prompt.security
- **作者**: Prompt Security
- **许可证**: AGPL-3.0

## 远程搜索结果

### 1. GitHub 搜索 ✅
```json
{
  "found": true,
  "repository": "prompt-security/clawsec",
  "description": "A complete security skill suite for OpenClaw's and NanoClaw agents",
  "stars": 798,
  "forks": 82,
  "language": "JavaScript",
  "updated_at": "2026-03-19T09:57:51Z"
}
```

### 2. Claw123.ai 社区索引
- **状态**: 已搜索，未在索引中找到
- **社区技能总数**: 5473
- **过滤恶意技能**: 2748

### 3. Sanwan.ai 技能商店
- **状态**: 已搜索，未找到
- **可用技能数**: 30+ 官方技能

## 安装过程

### 步骤 1: 本地检查 ✅
- 检查本地 skills 目录: 未找到现有 clawsec 技能
- 检查 lock.json: 未找到现有记录
- **结论**: 需要新安装

### 步骤 2: 远程获取 ✅
- 搜索 GitHub API: 找到 prompt-security/clawsec 仓库
- 获取 SKILL.md: 成功
- 获取 _meta.json 模板: 成功

### 步骤 3: 创建目录结构 ✅
```
/home/admin/openclaw/workspace/skills/clawsec/
├── SKILL.md              (3877 bytes)
├── _meta.json            (771 bytes)
└── .clawhub/
    └── origin.json       (439 bytes)
```

### 步骤 4: 创建技能文件 ✅

#### SKILL.md
- 技能信息定义
- 功能描述（安全监控、完整性验证、威胁情报）
- 支持的技能组件列表
- 执行流程说明
- 使用方法（命令行和子智能体）
- 依赖和兼容性信息

#### _meta.json
- 技能ID: clawsec
- 名称: ClawSec Security Suite
- 版本: 1.0.0
- 分类: security
- 标签: security, monitoring, threat-intelligence, integrity, cve, audit
- 状态: active
- 兼容: openclaw-agent, nanoclaw, moltbot, clawdbot

#### .clawhub/origin.json
- 来源: https://github.com/prompt-security/clawsec
- 来源类型: github
- 安装方法: manual
- 安装时间: 2026-03-19T19:56:00+08:00

### 步骤 5: 更新 lock.json ✅
- 添加 clawsec 到 installed 数组
- 版本: 1.0.0
- 来源: https://github.com/prompt-security/clawsec
- 状态: active
- 更新 generated_at 时间戳
- 添加安装报告到 previous_installations

## 技能功能概览

ClawSec 是一个**完整的 OpenClaw AI 智能体安全技能套件**：

### 核心能力
1. **📦 套件安装器** - 一键安装所有安全技能并进行完整性验证
2. **🛡️ 文件完整性保护** - 对关键文件（SOUL.md、IDENTITY.md）进行漂移检测和自动恢复
3. **📡 实时安全公告** - 自动轮询 NVD CVE 和社区威胁情报
4. **🔍 安全审计** - 自检脚本检测提示注入标记和漏洞
5. **🔐 校验和验证** - 所有技能工件的 SHA256 校验
6. **健康检查** - 自动更新和完整性验证

### 支持的组件
| 组件 | 描述 | 状态 |
|------|------|------|
| clawsec-feed | 安全公告订阅源监控 | ✅ 集成 |
| openclaw-audit-watchdog | 自动化每日审计 | ⚙️ 可选 |
| soul-guardian | 漂移检测和文件完整性保护 | ⚙️ 可选 |
| clawtributor | 社区事件报告 | ❌ 需显式请求 |

### 监控关键词
- **OpenClaw 平台**: OpenClaw, clawdbot, Moltbot
- **NanoClaw 平台**: NanoClaw, WhatsApp-bot, baileys
- **通用安全**: 提示注入模式, 智能体安全漏洞

## 使用方法

### 通过子智能体调用
```bash
# 执行安全审计
子智能体: 执行 clawsec 技能，运行安全审计

# 检查安全公告
子智能体: 执行 clawsec 技能，检查安全公告

# 验证技能完整性
子智能体: 执行 clawsec 技能，验证已安装技能完整性
```

### 命令行
```bash
# 使用 clawhub 安装完整套件
npx clawhub@latest install clawsec-suite

# 获取最新安全公告
curl -s https://clawsec.prompt.security/advisories/feed.json | jq '.advisories[] | select(.severity == "critical" or .severity == "high")'
```

## 验证结果

| 检查项 | 状态 | 详情 |
|--------|------|------|
| 目录创建 | ✅ | `/home/admin/openclaw/workspace/skills/clawsec/` |
| SKILL.md | ✅ | 3877 bytes，内容完整 |
| _meta.json | ✅ | 771 bytes，元数据正确 |
| .clawhub/origin.json | ✅ | 439 bytes，来源信息完整 |
| lock.json 更新 | ✅ | 已添加 clawsec 条目 |
| 状态设置 | ✅ | active |

## 安装后总技能数

**已安装技能总数**: 28

新安装的技能列表：
1. Self-Improving Agent
2. 网页搜索
3. 浏览器控制
4. 股票监控
5. 视频总结
6. AI文本人性化
7. 天气查询
8. AI图片生成
9. 语音合成
10. PDF生成
11. 飞书文档
12. GitHub操作
13. 火车票查询
14. 机票查询
15. 多Agent团队配置
16. 深度研究
17. SEO内容写作
18. 反爬网页访问
19. 今日热榜
20. 飞书互动卡片
21. 工作汇报生成
22. 自动化工作流
23. 小红书运营
24. 代码助手
25. Ontology 本体管理
26. Proactive Agent 主动式智能体
27. Tavily Web Search 智能搜索
28. **ClawSec Security Suite** (新)

## 后续建议

1. **配置安全公告监控**: 设置定时任务检查 https://clawsec.prompt.security/advisories/feed.json
2. **启用文件完整性保护**: 配置 soul-guardian 监控 SOUL.md 和 IDENTITY.md
3. **定期审计**: 使用 openclaw-audit-watchdog 运行定期安全审计
4. **查看完整文档**: 访问 https://clawsec.prompt.security 获取详细使用指南

## 资源链接

- **GitHub 仓库**: https://github.com/prompt-security/clawsec
- **官方网站**: https://clawsec.prompt.security
- **Prompt Security**: https://prompt.security/clawsec
- **安全公告订阅源**: https://clawsec.prompt.security/advisories/feed.json

---
**报告生成时间**: 2026-03-19 19:58:00 (GMT+8)
**安装批次ID**: batch_20250319_1956

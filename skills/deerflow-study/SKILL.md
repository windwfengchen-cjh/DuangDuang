# DeerFlow 深度研究

## 项目概述

**DeerFlow**（Deep Exploration and Efficient Research Flow）是字节跳动开源的 Super Agent Harness 框架，定位为 AI 超级智能体的基础架构。项目在 2026 年 2 月发布后迅速登上 GitHub Trending #1。

### 核心定位
- **类型**：开源 Super Agent Harness / AI Agent 框架
- **版本**：2.0（彻底重写，与 v1 无共享代码）
- **技术栈**：Python + LangGraph + LangChain
- **架构**：全栈架构（Backend + Frontend + Nginx 网关）

### 核心特性
1. **Skills & Tools**：可扩展的技能系统
2. **Sub-Agents**：子智能体编排与任务委托
3. **Sandbox & File System**：Docker/本地/K8s 沙箱执行环境
4. **Context Engineering**：上下文工程
5. **Long-Term Memory**：长期记忆系统
6. **Claude Code Integration**：与 Claude Code 等 Coding Agent 集成
7. **IM Channels**：支持 Telegram、Slack、Feishu/Lark
8. **MCP Server**：可配置的 MCP Server 扩展能力

---

## 核心架构

### 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        DeerFlow System                           │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (Next.js)                                             │
│  └── Port 3000                                                  │
├─────────────────────────────────────────────────────────────────┤
│  Nginx Gateway                                                   │
│  └── Port 2026 (统一入口)                                        │
├─────────────────────────────────────────────────────────────────┤
│  Gateway API (FastAPI)                                           │
│  └── Port 8001 - REST API 层                                     │
├─────────────────────────────────────────────────────────────────┤
│  LangGraph Server                                                │
│  └── Port 2024 - Agent Runtime                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 关键设计原则

**Harness / App 分层**:
- **Harness** (`packages/harness/deerflow/`): 可发布的 Agent 框架包
- **App** (`app/`): 未发布的应用代码

**依赖规则**：App 可以导入 deerflow，但 deerflow 绝不可导入 app

---

## 关键设计模式

### 1. 技能系统 (Skills System)

技能是结构化的提示词模板，存储在 `skills/{category}/{skill-name}/SKILL.md`：

```markdown
---
name: deep-research
description: Use this skill for ANY question requiring web research.
trigger: what is X, explain X
---

# 技能内容（提示词模板）
```

### 2. 子智能体编排 (Sub-Agent Orchestration)

内置子智能体类型：
- **General Purpose Agent**: 通用任务
- **Bash Agent**: 命令执行
- **Research Agent**: 深度研究

### 3. 沙箱执行机制 (Sandbox System)

三种执行模式：
- **Local**: 本地文件系统
- **Docker**: 容器隔离
- **K8s**: Kubernetes Pod

虚拟路径映射：
| Agent 看到的虚拟路径 | 实际物理路径 |
|---------------------|-------------|
| `/mnt/user-data/workspace` | 线程隔离目录 |
| `/mnt/skills/public` | 公共技能目录 |

### 4. 记忆系统 (Memory System)

```
MemoryQueue → MemoryExtractor → MemoryUpdater → MemoryStorage
```

- 异步提取（不阻塞主流程）
- LLM 驱动的关键信息提取
- 重要性评分和分类

### 5. 中间件链 (Middleware Chain)

12 个中间件按严格顺序执行：

| 顺序 | 中间件 | 功能 |
|-----|--------|------|
| 1 | ThreadDataMiddleware | 创建线程目录结构 |
| 2 | UploadsMiddleware | 跟踪并注入上传文件 |
| 3 | SandboxMiddleware | 获取沙箱 |
| 4 | DanglingToolCallMiddleware | 处理中断的工具调用 |
| 5 | GuardrailMiddleware | 工具调用授权检查 |
| 6 | SummarizationMiddleware | 上下文压缩 |
| 7 | TodoListMiddleware | 任务跟踪 |
| 8 | TitleMiddleware | 自动生成线程标题 |
| 9 | MemoryMiddleware | 记忆队列处理 |
| 10 | ViewImageMiddleware | 注入图片 base64 数据 |
| 11 | SubagentLimitMiddleware | 限制并发子智能体 |
| 12 | ClarificationMiddleware | 澄清请求拦截 |

---

## 与 OpenClaw 对比

### 架构对比

| 特性 | DeerFlow | OpenClaw |
|-----|----------|----------|
| **定位** | Super Agent Harness | Agent 运行平台 |
| **技术栈** | Python + LangGraph | TypeScript/JavaScript |
| **沙箱** | Docker/K8s/本地多级 | 依赖宿主环境 |
| **子智能体** | 内置多种类型 Agent | sessions_spawn 统一接口 |
| **技能系统** | Markdown 模板 + Frontmatter | TypeScript 技能目录 |
| **记忆系统** | 异步提取 + 队列 | 自动注入相关记忆 |
| **IM 集成** | Telegram/Slack/Feishu | Feishu 为主 |
| **前端** | Next.js 完整界面 | 无内置前端 |

### 各自优势

**DeerFlow 优势**:
- ✅ 完整的沙箱执行环境（安全隔离）
- ✅ 丰富的技能模板生态
- ✅ Claude Code 等 Coding Agent 深度集成
- ✅ 可视化线程管理

**OpenClaw 优势**:
- ✅ 更轻量，部署简单
- ✅ 与现有技能生态深度集成（feishu-bitable 等）
- ✅ 无需额外基础设施（Docker/K8s）
- ✅ 更灵活的工具调用机制

---

## 可借鉴的最佳实践

### 1. 技能模板化

DeerFlow 将技能定义为 Markdown + Frontmatter：
- **可读性**：技能定义即文档
- **版本控制**：Git 友好
- **社区共享**：易于分发

### 2. 虚拟路径系统

Agent 使用统一虚拟路径，映射到实际物理路径：
- 路径抽象，Agent 无需关心实际位置
- 线程隔离（每个线程独立目录）

### 3. 中间件链设计

12 个中间件按顺序执行，单一职责：
- 可插拔（可选中间件）
- 可中断（提前结束流程）
- 状态共享

### 4. 子智能体类型化

为不同场景定义专用子智能体：
- `general_purpose`: 通用任务
- `bash_agent`: 命令执行
- `research_agent`: 深度研究

### 5. 记忆异步提取

异步队列 + LLM 提取：
- 不阻塞主流程
- 重要性评分
- 分类存储

### 6. 沙箱安全执行

多级沙箱保障代码执行安全：
- Docker 隔离
- 资源限制
- 文件系统隔离

---

## 参考资源

- **GitHub**: https://github.com/bytedance/deer-flow
- **官网**: https://deerflow.tech
- **中文 README**: https://github.com/bytedance/deer-flow/blob/main/README_zh.md

---

## 学习总结

DeerFlow 2.0 代表了字节跳动在 AI Agent 领域的最新探索，其核心贡献在于：

1. **全栈架构**：从前端到沙箱的完整解决方案
2. **技能生态**：Markdown 化的技能定义降低了门槛
3. **安全执行**：多级沙箱保障代码执行安全
4. **企业集成**：Claude Code、Feishu 等深度集成

对于 OpenClaw 技能开发者，最值得借鉴的是：
- 技能模板化思路
- 子智能体场景化设计
- 中间件链的解耦模式

---

*文档生成时间: 2026-03-27*
*技能路径: `/home/admin/openclaw/workspace/skills/deerflow-study/`*
# OpenClaw 调教学习笔记

> 来源：《从安装完"智障"到战车：我把 OpenClaw 调教了两周后的终极精华帖》
> 作者：Collin | 整理于 2026年3月
> 学习时间：2026-03-16

---

## 一、安装踩坑（已踩过）

### 坑1：GitHub SSH 拉取失败
- **问题**：国内网络 npm install 卡死，GitHub SSH 子模块拉取失败
- **解决**：`git config --global url."https://github.com/".insteadOf "ssh://git@github.com/"`
- **状态**：✅ 已解决（Boss 的环境已配置好）

### 坑2：BOOTSTRAP.md 隐形炸弹
- **问题**：装完后没删 BOOTSTRAP.md，Agent 每次启动都重新执行初始化
- **解决**：装完第一件事删掉它！
- **状态**：✅ 已删除

---

## 二、核心技能清单（已安装状态）

| 技能 | 用途 | 安装状态 |
|------|------|----------|
| Summarize | 长文摘要机 | ❌ 未安装 |
| Coding Agent | 代码包工头（Codex/Claude Code） | ❌ 未安装 |
| Agent Browser | 无头浏览器（Playwright） | ✅ **已安装** |
| 飞书全家桶 | 飞书文档/云盘/权限/Wiki | ✅ **已安装** |
| Cron Scheduling | 定时任务 | ❌ 未安装 |
| Tavily Search | 干净的AI搜索 | ✅ **已安装** (Search/Research) |
| Healthcheck | 内网体检器 | ❌ 未安装 |
| PDF Toolkit | PDF结构化拆解 | ✅ **已安装** (PDF技能) |

### 技能安全审计原则
- 🔴 DANGEROUS：坚决不装（如 claw-shell）
- 🟡 CAUTION：谨慎使用（如 canvas）
- 🟢 SAFE：放心使用

---

## 三、4层保命配置（核心精华）

### 第1层：锁死网关（防渗透）
```json
"gateway": { "bind": "loopback" }
```
- 只允许 127.0.0.1 访问，局域网其他机器全部挡在门外
- 禁用 camera.snap、screen.record 等危险操作
- 检查无 ngrok/cpolar 等内网穿透隧道

### 第2层：模型分层路由
**关键教训**：
- 千问系列 → `openai-completions`
- GPT 系列 → `openai-responses`
- **事故**：API类型配错导致静默 fallback 到 GPT-5.2，Token费暴涨

**最佳实践**：
- 日常对话用 qwen3.5-plus（便宜）
- 硬核推理拉 gpt-5.2
- Heartbeat/Cron 用最廉价模型

### 第3层：上下文"减肥"
- AGENTS.md / USER.md 精简到条件约束，别写小作文
- 养成用 `/compact` 或 `/new` 重置对话的习惯
- 保持 `compaction.mode = "safeguard"`
- 活跃群聊隔几天检查 Session 大小，超10万字符果断截断

### 第4层：搭建长期记忆
四个记忆文件体系：
1. **SOUL.md**（灵魂文件）：核心价值观、行为边界、回复格式
2. **IDENTITY.md**（身份卡）：名字、Emoji、头像
3. **MEMORY.md**（长期记忆库）：核心业务脉络、常用路径、技术栈、踩坑记录
4. **memory/YYYY-MM-DD.md**（每日日记）：当天新信息

**自动化建议**：每晚11点扫描今日对话，提炼关键信息反写到 MEMORY.md

---

## 四、安全加固清单

1. ✅ 网关绝对隔离（bind: loopback）
2. ✅ 危险命令黑名单（改用白名单更佳）
3. ✅ 技能安全审计（57个技能已扫描）
4. ⚠️ 输出约束（可添加模型名称和Session ID）
5. ✅ 反代理信任（trustedProxies为空）

---

## 五、巡检优化 SOP

定期执行：`openclaw status --deep`

检查项：
- Session 大小（超10万字符需截断）
- 配置漂移（对比预期 vs 实际）
- 内存文件质量
- 心跳状态追踪

---

## 六、对我的启发

1. **记忆系统需要更主动**：目前我是被动记录，可以加入自动提炼机制
2. **定期巡检**：可以每周做一次"全身体检"，检查 session 大小、配置状态
3. **技能扩展**：可以考虑安装 Summarize 和 Healthcheck
4. **上下文管理**：长对话时主动提醒 Boss 用 /compact

---

## 行动项

- [ ] 建议 Boss 安装 Summarize 技能（长文摘要需求多）
- [ ] 建议 Boss 安装 Healthcheck 技能（安全体检）
- [ ] 每周主动做一次 session 巡检
- [ ] 优化 MEMORY.md 结构（参考 4层记忆体系）

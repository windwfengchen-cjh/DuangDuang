# PRD Document 影子模式验证系统

## 概述

影子模式验证系统用于在不影响现有业务逻辑的情况下，验证元数据触发规则的准确性。通过对比旧逻辑和元数据匹配结果，收集数据以优化触发机制。

## 文件说明

| 文件 | 说明 |
|------|------|
| `shadow-validator.ts` | 影子验证器核心模块 |
| `analyze-shadow-logs.ts` | 日志分析脚本 |
| `feishu-handler-integration.ts` | Feishu Handler 集成示例 |
| `README.md` | 本文件 |

## 快速开始

### 1. 安装依赖

确保系统已安装 Node.js 和 TypeScript：

```bash
npm install -g ts-node typescript
```

### 2. 启动影子验证

在 feishu-feedback-handler 中集成影子验证：

```typescript
import { ShadowValidator } from '../skills/prd-document/shadow-validator';

const shadowValidator = new ShadowValidator();

async function handleMessage(text: string) {
  // 旧逻辑（保持不变）
  const result = oldLogic(text);
  
  // 影子验证（异步，不阻塞）
  shadowValidator.quickValidate(text, result).catch(console.error);
  
  return result;
}
```

### 3. 查看日志

日志文件位置：`~/logs/shadow-validation/prd-document.jsonl`

每条日志格式：
```json
{
  "timestamp": "2026-03-28T00:00:00.000Z",
  "message": "写PRD文档",
  "oldLogicResult": "prd-document",
  "metadataMatch": true,
  "triggerWord": "写PRD",
  "match": true
}
```

### 4. 运行分析报告

```bash
# 查看文本报告
cd ~/openclaw/workspace/skills/prd-document
npx ts-node analyze-shadow-logs.ts

# 输出 JSON 格式
npx ts-node analyze-shadow-logs.ts --output json

# 分析最近7天的数据
npx ts-node analyze-shadow-logs.ts --days 7

# 保存报告到文件
npx ts-node analyze-shadow-logs.ts --save-report
```

## 分析报告说明

### 匹配率统计

- **整体匹配率**: 新旧逻辑一致的比例
- **真阳性 (TP)**: 两者都识别为 PRD
- **假阳性 (FP)**: 元数据识别为 PRD 但旧逻辑未识别
- **假阴性 (FN)**: 旧逻辑识别为 PRD 但元数据未识别
- **真阴性 (TN)**: 两者都未识别为 PRD

### 触发词统计

显示各个触发词的匹配次数，帮助识别最常用的触发词。

### 建议

根据分析结果自动生成优化建议：
- 假阳性过多 → 元数据触发词过于宽泛
- 假阴性过多 → 需要补充元数据触发词
- 匹配率高 → 可以考虑正式投入使用

## 配置文件

### SKILL.md 元数据格式

```yaml
---
name: prd-document
trigger:
  - 写PRD
  - 创建PRD
  - 产品需求文档
---
```

## 部署后检查清单

- [ ] 影子验证器模块已部署
- [ ] Feishu Handler 已集成
- [ ] 日志目录已创建 (`~/logs/shadow-validation/`)
- [ ] 验证日志开始记录
- [ ] 分析脚本可正常运行

## 运行计划

| 时间 | 操作 |
|------|------|
| Day 1 | 部署影子模式验证 |
| Day 7 | 首次运行分析报告 |
| Day 14 | 二次运行分析报告，对比数据 |
| Day 30 | 评估是否正式切换为元数据匹配 |

## 注意事项

1. **不影响主流程**: 影子验证完全异步，不影响现有业务逻辑
2. **日志轮转**: 建议定期清理旧日志文件
3. **隐私保护**: 日志中存储用户消息，注意数据安全
4. **性能监控**: 观察影子验证对系统性能的影响

## 故障排查

### 日志文件未创建

检查目录权限：
```bash
ls -la ~/logs/shadow-validation/
```

### TypeScript 编译错误

确保安装了类型定义：
```bash
npm install --save-dev @types/node
```

### 分析脚本报错

检查日志文件格式：
```bash
head -5 ~/logs/shadow-validation/prd-document.jsonl
```

## 联系

如有问题，请联系开发团队。

# ERRORS.md - 错误记录

## [ERR-20260314-001] 问卷星问卷修改失败

**Logged**: 2026-03-14T12:16:00+08:00
**Priority**: medium
**Status**: pending
**Area**: config

### Summary
尝试修改问卷星问卷时，浏览器操作多次失败，未能成功将纯文字说明改为填空题。

### Error
- 点击元素 ref 经常失效（页面刷新后 ref 变化）
- 问卷星编辑页面动态更新，导致元素引用不稳定
- 最终任务被 Boss 中断

### Context
- 任务：将企业名称、联系人、联系方式从纯文字改为填空题
- 环境：问卷星编辑页面
- 工具：browser 工具

### Suggested Fix
1. 使用更稳定的定位方式（如 aria-label、text content 等）
2. 或者使用问卷星的批量编辑功能
3. 或者重新创建问卷而不是修改

### Metadata
- Reproducible: yes
- Related Files: memory/2026-03-14.md
- Tags: wjx, browser, automation

---

## [ERR-20260314-002] Ollama 安装失败

**Logged**: 2026-03-14T12:16:00+08:00
**Priority**: low
**Status**: pending
**Area**: infra

### Summary
尝试安装 Ollama 本地模型以支持图像识别，但因网络问题多次失败。

### Error
- 下载速度极慢（0.1%-0.2%），多次超时
- 使用 curl 安装脚本、git clone 源码等方式均失败

### Context
- 目的：获取图像识别能力
- 方案：本地部署 LLaVA 等多模态模型
- 问题：网络带宽不足，模型文件太大

### Suggested Fix
1. 使用 Gemini API（需要申请 API Key）
2. 或使用其他云端视觉 API
3. 或等待网络条件改善后再尝试本地部署

### Metadata
- Reproducible: yes (网络环境相关)
- Related Files: memory/2026-03-14.md
- Tags: ollama, vision, local-model

---
